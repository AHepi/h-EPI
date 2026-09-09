"""The append-only record: a hash-chained event log, and state rebuilt from it.

One ``log.jsonl`` per run root. Each event is canonical JSON on one line,
carries its own content digest, and carries the previous event's digest; the
first event's ``prev`` is the digest of the run header, which is fixed before
anything is called. Flipping one byte anywhere breaks that event's own identity
and the next event's link to it.

Bodies and commitments are blob references, not inline text, and a new artifact
kind logs through the same ``ARTIFACT_SUBMITTED`` shape with its kind id in the
event. Adding a kind therefore adds no event type: the event vocabulary is
about the run, not about the kinds.

One function applies one event to state, and replay of the log alone rebuilds
the final state and its digest.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Iterator, Mapping

from creib.canonical import canonical_bytes
from creib.errors import RecordError
from creib.forge.conformance.common import publish_no_clobber
from creib.strict_json import load_strict, loads_strict

from .common import (
    EVENT_DOMAIN,
    EVENT_SCHEMA_NAME,
    EVENT_SCHEMA_VERSION,
    STATE_DOMAIN,
    MiniError,
    content_id,
    digest_bytes,
    validate_instance,
)

RUN_STARTED = "RUN_STARTED"
STAGE_ENTERED = "STAGE_ENTERED"
ARTIFACT_SUBMITTED = "ARTIFACT_SUBMITTED"
FORMAT_FAILURE = "FORMAT_FAILURE"
SUBMISSION_DROPPED = "SUBMISSION_DROPPED"
REFUSED = "REFUSED"
EVIDENCE_BATCHED = "EVIDENCE_BATCHED"
ROUTED = "ROUTED"
ATTENTION_CHOSE = "ATTENTION_CHOSE"
RUN_ENDED = "RUN_ENDED"

EVENT_TYPES: tuple[str, ...] = (
    RUN_STARTED,
    STAGE_ENTERED,
    ARTIFACT_SUBMITTED,
    FORMAT_FAILURE,
    SUBMISSION_DROPPED,
    REFUSED,
    EVIDENCE_BATCHED,
    ROUTED,
    ATTENTION_CHOSE,
    RUN_ENDED,
)

LOG_NAME = "log.jsonl"
BLOBS_DIR = "blobs"


@dataclass(frozen=True)
class Event:
    """One event of the append-only record."""

    seq: int
    prev: str
    type: str
    stage_id: str | None
    kind_id: str | None
    artifact_id: str | None
    body_ref: str | None
    commitments_ref: str | None
    payload: Mapping[str, Any]
    event_id: str

    def body(self) -> dict[str, Any]:
        return {
            "schema_version": EVENT_SCHEMA_VERSION,
            "seq": self.seq,
            "prev": self.prev,
            "type": self.type,
            "stage_id": self.stage_id,
            "kind_id": self.kind_id,
            "artifact_id": self.artifact_id,
            "body_ref": self.body_ref,
            "commitments_ref": self.commitments_ref,
            "payload": dict(self.payload),
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.body(), "event_id": self.event_id}


def build_event(
    *,
    seq: int,
    prev: str,
    type: str,
    payload: Mapping[str, Any],
    stage_id: str | None = None,
    kind_id: str | None = None,
    artifact_id: str | None = None,
    body_ref: str | None = None,
    commitments_ref: str | None = None,
) -> Event:
    if type not in EVENT_TYPES:
        raise MiniError("MINI_LOG_EVENT_TYPE_UNKNOWN", f"{type!r} is not one of the record's event types")
    partial = Event(
        seq=seq,
        prev=prev,
        type=type,
        stage_id=stage_id,
        kind_id=kind_id,
        artifact_id=artifact_id,
        body_ref=body_ref,
        commitments_ref=commitments_ref,
        payload=dict(payload),
        event_id="",
    )
    return replace(partial, event_id=content_id(EVENT_DOMAIN, partial.body()))


def event_from_dict(raw: Any, where: str) -> Event:
    validate_instance(raw, EVENT_SCHEMA_NAME, "MINI_LOG_UNREADABLE")
    entry = dict(raw)
    event = Event(
        seq=entry["seq"],
        prev=entry["prev"],
        type=entry["type"],
        stage_id=entry["stage_id"],
        kind_id=entry["kind_id"],
        artifact_id=entry["artifact_id"],
        body_ref=entry["body_ref"],
        commitments_ref=entry["commitments_ref"],
        payload=entry["payload"],
        event_id=entry["event_id"],
    )
    if event.type not in EVENT_TYPES:
        raise MiniError("MINI_LOG_EVENT_TYPE_UNKNOWN", f"{where} carries the unknown event type {event.type!r}")
    if content_id(EVENT_DOMAIN, event.body()) != event.event_id:
        raise MiniError("MINI_LOG_EVENT_ID_MISMATCH", f"{where} does not replay its own identity: the bytes have moved")
    return event


class BlobStore:
    """Content-addressed bytes, written once and never overwritten."""

    def __init__(self, directory: Path) -> None:
        if not isinstance(directory, Path):
            raise TypeError("directory must be pathlib.Path")
        self.directory = directory

    def put(self, data: bytes) -> str:
        reference = digest_bytes(data)
        path = self.directory / reference
        if path.exists():
            if path.read_bytes() != data:
                raise MiniError("MINI_BLOB_CORRUPT", f"blob {reference[:16]} on disk does not carry its own digest")
            return reference
        try:
            publish_no_clobber(path, data)
        except RecordError as error:
            raise MiniError("MINI_BLOB_CORRUPT", f"cannot store blob {reference[:16]}: {error}") from error
        return reference

    def get(self, reference: str) -> bytes:
        path = self.directory / reference
        try:
            data = path.read_bytes()
        except OSError as error:
            raise MiniError("MINI_BLOB_MISSING", f"blob {reference[:16]} is not in the store") from error
        if digest_bytes(data) != reference:
            raise MiniError("MINI_BLOB_CORRUPT", f"blob {reference[:16]} does not carry its own digest")
        return data


class EventLog:
    """Append-only, hash-chained. Reading verifies the chain from the genesis."""

    def __init__(self, path: Path, genesis: str) -> None:
        if not isinstance(path, Path):
            raise TypeError("path must be pathlib.Path")
        self.path = path
        self.genesis = genesis

    def append(self, event: Event) -> Event:
        record = event.to_dict()
        validate_instance(record, EVENT_SCHEMA_NAME, "MINI_LOG_UNREADABLE")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "ab") as handle:
            handle.write(canonical_bytes(record) + b"\n")
            handle.flush()
        return event

    def read(self) -> Iterator[Event]:
        if not self.path.exists():
            return
        try:
            raw = self.path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            raise MiniError("MINI_LOG_UNREADABLE", f"cannot read {self.path}: {error}") from error
        expected_prev = self.genesis
        for index, line in enumerate(raw.splitlines()):
            if not line.strip():
                continue
            where = f"{self.path.name}:{index + 1}"
            try:
                parsed = loads_strict(line)
            except RecordError as error:
                raise MiniError("MINI_LOG_UNREADABLE", f"{where} is not readable: {error}") from error
            event = event_from_dict(parsed, where)
            if event.seq != index:
                raise MiniError("MINI_LOG_SEQUENCE_BROKEN", f"{where} carries sequence {event.seq}, expected {index}")
            if event.prev != expected_prev:
                raise MiniError("MINI_LOG_CHAIN_BROKEN", f"{where} does not link to the event before it")
            expected_prev = event.event_id
            yield event


@dataclass
class MiniState:
    """What the record says, rebuilt from the log alone."""

    run_id: str = ""
    manifest_id: str = ""
    stages_entered: list[str] = field(default_factory=list)
    artifacts: dict[str, dict[str, Any]] = field(default_factory=dict)
    artifact_order: list[str] = field(default_factory=list)
    blocks: list[dict[str, Any]] = field(default_factory=list)
    scratch: dict[str, list[str]] = field(default_factory=dict)
    scratch_blocks: dict[str, list[str]] = field(default_factory=dict)
    pushed: dict[str, list[str]] = field(default_factory=dict)
    submissions_by_kind: dict[str, int] = field(default_factory=dict)
    format_failures_by_kind: dict[str, int] = field(default_factory=dict)
    drops_by_kind: dict[str, int] = field(default_factory=dict)
    tokens_by_kind: dict[str, int] = field(default_factory=dict)
    refusals: list[dict[str, Any]] = field(default_factory=list)
    attention_choices: list[dict[str, Any]] = field(default_factory=list)
    ended: bool = False
    stop_reason: str = ""

    def snapshot(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "manifest_id": self.manifest_id,
            "stages_entered": list(self.stages_entered),
            "artifacts": {key: self.artifacts[key] for key in sorted(self.artifacts)},
            "artifact_order": list(self.artifact_order),
            "blocks": list(self.blocks),
            "scratch": {key: self.scratch[key] for key in sorted(self.scratch)},
            "scratch_blocks": {key: self.scratch_blocks[key] for key in sorted(self.scratch_blocks)},
            "pushed": {key: self.pushed[key] for key in sorted(self.pushed)},
            "submissions_by_kind": {key: self.submissions_by_kind[key] for key in sorted(self.submissions_by_kind)},
            "format_failures_by_kind": {key: self.format_failures_by_kind[key] for key in sorted(self.format_failures_by_kind)},
            "drops_by_kind": {key: self.drops_by_kind[key] for key in sorted(self.drops_by_kind)},
            "tokens_by_kind": {key: self.tokens_by_kind[key] for key in sorted(self.tokens_by_kind)},
            "refusals": list(self.refusals),
            "attention_choices": list(self.attention_choices),
            "ended": self.ended,
            "stop_reason": self.stop_reason,
        }

    def digest(self) -> str:
        return content_id(STATE_DOMAIN, self.snapshot())

    def artifacts_of_kind(self, kind_id: str) -> tuple[dict[str, Any], ...]:
        return tuple(self.artifacts[key] for key in self.artifact_order if self.artifacts[key]["kind_id"] == kind_id)

    def blocks_of_tier(self, tiers: tuple[str, ...]) -> tuple[dict[str, Any], ...]:
        return tuple(block for block in self.blocks if block["tier"] in tiers)


def _bump(counter: dict[str, int], key: str, amount: int = 1) -> None:
    counter[key] = counter.get(key, 0) + amount


def apply_event(state: MiniState, event: Event) -> None:
    """Apply one event. This is the only function that changes state."""

    payload = dict(event.payload)
    if event.type == RUN_STARTED:
        state.run_id = str(payload.get("run_id", ""))
        state.manifest_id = str(payload.get("manifest_id", ""))
    elif event.type == STAGE_ENTERED:
        state.stages_entered.append(str(event.stage_id))
    elif event.type == ARTIFACT_SUBMITTED:
        artifact_id = str(event.artifact_id)
        state.artifacts[artifact_id] = {
            "artifact_id": artifact_id,
            "kind_id": event.kind_id,
            "stage_id": event.stage_id,
            "seq": event.seq,
            "body_ref": event.body_ref,
            "commitments_ref": event.commitments_ref,
            "about": list(payload.get("about", [])),
            "answers": list(payload.get("answers", [])),
            "citations": list(payload.get("citations", [])),
            "extra": dict(payload.get("extra", {})),
        }
        state.artifact_order.append(artifact_id)
        _bump(state.submissions_by_kind, str(event.kind_id))
        _bump(state.tokens_by_kind, str(event.kind_id), int(payload.get("completion_tokens", 0)))
    elif event.type == FORMAT_FAILURE:
        _bump(state.format_failures_by_kind, str(event.kind_id))
    elif event.type == SUBMISSION_DROPPED:
        _bump(state.drops_by_kind, str(event.kind_id))
    elif event.type == REFUSED:
        state.refusals.append({"stage_id": event.stage_id, "kind_id": event.kind_id, **payload})
    elif event.type == EVIDENCE_BATCHED:
        destination = dict(payload.get("to", {}))
        for block in payload.get("blocks", []):
            state.blocks.append({**block, "source_ref": payload.get("source_ref")})
            if destination.get("target") == "scratch":
                state.scratch_blocks.setdefault(str(destination.get("destination")), []).append(str(block["block_id"]))
    elif event.type == ROUTED:
        target = dict(payload.get("to", {}))
        artifact_id = str(event.artifact_id)
        if target.get("target") == "scratch":
            state.scratch.setdefault(str(target.get("destination")), []).append(artifact_id)
        elif target.get("target") == "port":
            key = f"{target.get('stage_id')}::{target.get('port_id')}"
            state.pushed.setdefault(key, []).append(artifact_id)
    elif event.type == ATTENTION_CHOSE:
        state.attention_choices.append({"policy": payload.get("policy"), "chosen": payload.get("chosen")})
    elif event.type == RUN_ENDED:
        state.ended = True
        state.stop_reason = str(payload.get("stop_reason", ""))
    else:
        raise MiniError("MINI_LOG_EVENT_TYPE_UNKNOWN", f"no rule applies the event type {event.type!r}")


def replay(path: Path, genesis: str) -> MiniState:
    """Rebuild state from the log alone."""

    state = MiniState()
    for event in EventLog(path, genesis).read():
        apply_event(state, event)
    return state


def read_run_header(root: Path) -> dict[str, Any]:
    header = root / "run-header.json"
    try:
        return dict(load_strict(header))
    except RecordError as error:
        raise MiniError("MINI_LOG_UNREADABLE", f"cannot read the run header at {header}: {error}") from error
