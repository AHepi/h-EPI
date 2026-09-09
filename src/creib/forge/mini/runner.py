"""The loop: walk the declared stages, ask each seat, write the record.

Nothing here knows a conjecturer from a critic. It walks stages, renders each
stage's declared ports, asks the responder, reads the reply into a submission,
checks the compiled format, checks the citations, routes the output through the
permission layer, and writes every outcome — accepted, failed, dropped, refused
— to the append-only record.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from creib.canonical import canonical_bytes

from .attention import ATTENTION_OFF, PendingStage, choose_next
from .common import ARTIFACT_DOMAIN, MiniError, content_id, digest_bytes
from .evidence import Block, check_citations, cut_source, render_legend
from .executor import Request, Responder
from .kinds import ArtifactKind, Submission, read_submission
from .log import (
    ARTIFACT_SUBMITTED,
    ATTENTION_CHOSE,
    BLOBS_DIR,
    EVIDENCE_BATCHED,
    FORMAT_FAILURE,
    LOG_NAME,
    REFUSED,
    ROUTED,
    RUN_ENDED,
    RUN_STARTED,
    STAGE_ENTERED,
    SUBMISSION_DROPPED,
    BlobStore,
    EventLog,
    MiniState,
    apply_event,
    build_event,
)
from .manifest import RunPlan, Stage
from .ports import PortType, port_draws_kinds, port_draws_tiers
from .routing import Destination
from .signals import compute_signals

MAX_STEPS = 512


@dataclass(frozen=True)
class RunOutcome:
    """What the record says when the loop stops."""

    run_id: str
    root: Path
    genesis: str
    state_digest: str
    stop_reason: str
    stages_entered: tuple[str, ...]


class _Recorder:
    """Appends one event, applies it, and carries the chain forward."""

    def __init__(self, log: EventLog, state: MiniState, genesis: str) -> None:
        self._log = log
        self._state = state
        self._prev = genesis
        self._seq = 0

    @property
    def seq(self) -> int:
        return self._seq

    def emit(self, event_type: str, payload: Mapping[str, Any], **fields: Any) -> None:
        event = build_event(seq=self._seq, prev=self._prev, type=event_type, payload=payload, **fields)
        self._log.append(event)
        apply_event(self._state, event)
        self._prev = event.event_id
        self._seq += 1


def block_text(blobs: BlobStore, block: Mapping[str, Any]) -> str:
    """Recover one block's own words from the source it was cut from."""

    window = blobs.get(str(block["source_ref"]))[int(block["span_start"]) : int(block["span_end"])]
    if digest_bytes(window) != block["text_sha256"]:
        raise MiniError("MINI_BLOB_CORRUPT", f"block {str(block['block_id'])[:16]} does not match the bytes it names")
    return window.decode("utf-8")


def _as_block(blobs: BlobStore, entry: Mapping[str, Any]) -> Block:
    return Block(
        block_id=str(entry["block_id"]),
        source_id=str(entry["source_id"]),
        source_sha256=str(entry["source_sha256"]),
        tier=str(entry["tier"]),
        span_start=int(entry["span_start"]),
        span_end=int(entry["span_end"]),
        text_sha256=str(entry["text_sha256"]),
        text=block_text(blobs, entry),
    )


def _visible_through(
    plan: RunPlan,
    state: MiniState,
    port_type: PortType,
    params: Mapping[str, Any],
    port_type_name: str,
    entry: Mapping[str, Any],
) -> bool:
    tier = str(entry["tier"])
    route = plan.routing.for_evidence(tier)
    if route is None:
        return port_type.source == "evidence" and tier in port_draws_tiers(port_type, params)
    if route.target == "nowhere":
        return False
    if route.target == "port_type":
        return port_type_name == route.port_type and port_type.source == "evidence" and tier in port_draws_tiers(port_type, params)
    destination = str(route.destination)
    return port_type.source == "scratch" and str(params.get("destination")) == destination and str(entry["block_id"]) in state.scratch_blocks.get(destination, [])


def _artifact_lines(blobs: BlobStore, records: tuple[Mapping[str, Any], ...], rule: str) -> list[str]:
    lines: list[str] = []
    for record in records:
        body = blobs.get(str(record["body_ref"])).decode("utf-8")
        lines.append(f"[{str(record['artifact_id'])[:16]}] ({record['kind_id']})")
        lines.append(body)
        if rule == "list_bodies_and_commitments":
            lines.append("commitments: " + blobs.get(str(record["commitments_ref"])).decode("utf-8"))
    return lines


def render_port(plan: RunPlan, state: MiniState, blobs: BlobStore, stage: Stage, port_id: str) -> tuple[str, tuple[str, ...]]:
    """Render one port, and say which evidence blocks it exposed."""

    kind = plan.kinds[str(stage.kind_id)]
    port = kind.port(port_id)
    port_type = plan.port_types[port.port_type]
    header = f"## {port_type.header} ({port_id})"
    if port_type.source == "problem":
        return f"{header}\n{plan.problem}", ()
    if port_type.source == "artifacts":
        drawn = port_draws_kinds(port_type, port.params)
        records = tuple(state.artifacts[key] for key in state.artifact_order if state.artifacts[key]["kind_id"] in drawn)
        pushed = tuple(state.artifacts[key] for key in state.pushed.get(f"{stage.stage_id}::{port_id}", []) if key in state.artifacts)
        ordered = records + tuple(item for item in pushed if item not in records)
        lines = _artifact_lines(blobs, ordered, port_type.render_rule) or ["(nothing yet)"]
        return "\n".join([header, *lines]), ()
    if port_type.source == "evidence":
        entries = [item for item in state.blocks if _visible_through(plan, state, port_type, port.params, port.port_type, item)]
        blocks = [_as_block(blobs, item) for item in entries]
        return render_legend(blocks, header), tuple(block.block_id for block in blocks)
    destination = str(port.params["destination"])
    records = tuple(state.artifacts[key] for key in state.scratch.get(destination, []) if key in state.artifacts)
    lines = _artifact_lines(blobs, records, port_type.render_rule)
    entries = [item for item in state.blocks if _visible_through(plan, state, port_type, port.params, port.port_type, item)]
    blocks = [_as_block(blobs, item) for item in entries]
    if blocks:
        lines.append(render_legend(blocks, "admitted blocks"))
    return "\n".join([header, *(lines or ["(nothing yet)"])]), tuple(block.block_id for block in blocks)


def render_brief(plan: RunPlan, state: MiniState, blobs: BlobStore, stage: Stage) -> tuple[str, frozenset[str]]:
    """Render everything a stage is shown, and the blocks it may cite."""

    kind = plan.kinds[str(stage.kind_id)]
    sections = [f"# {kind.title}"]
    exposed: set[str] = set()
    for port_id in stage.ports:
        rendered, block_ids = render_port(plan, state, blobs, stage, port_id)
        sections.append(rendered)
        exposed.update(block_ids)
    compiled = plan.formats[kind.kind_id]
    sections.append(
        "## What to return\n"
        'A JSON object carrying "body" and "commitments". Both are strings and nothing else is required.'
    )
    if not compiled.freeform:
        sections.append("## Required shape\n" + "\n".join(compiled.describe()))
    return "\n\n".join(sections), frozenset(exposed)


def _batch_evidence(plan: RunPlan, blobs: BlobStore, recorder: _Recorder) -> None:
    for source in plan.sources:
        reference = blobs.put(source.raw)
        blocks = cut_source(source.source_id, source.raw, source.tier)
        route = plan.routing.for_evidence(source.tier)
        recorder.emit(
            EVIDENCE_BATCHED,
            {
                "source_id": source.source_id,
                "source_ref": reference,
                "tier": source.tier,
                "blocks": [block.to_dict() for block in blocks],
                "to": {} if route is None else route.to_dict(),
            },
        )


def _store_artifact(blobs: BlobStore, stage: Stage, submission: Submission, seq: int) -> tuple[str, str, str]:
    body_ref = blobs.put(submission.body.encode("utf-8"))
    commitments_ref = blobs.put(submission.commitments.encode("utf-8"))
    artifact_id = content_id(
        ARTIFACT_DOMAIN,
        {
            "stage_id": stage.stage_id,
            "kind_id": stage.kind_id,
            "seq": seq,
            "body_ref": body_ref,
            "commitments_ref": commitments_ref,
        },
    )
    return artifact_id, body_ref, commitments_ref


def _route_output(
    plan: RunPlan,
    state: MiniState,
    blobs: BlobStore,
    recorder: _Recorder,
    stage: Stage,
    artifact_id: str,
    body_ref: str,
) -> None:
    kind_id = str(stage.kind_id)
    destination: Destination | None = plan.routing.for_artifact(kind_id)
    if destination is None:
        return
    if not plan.policy.may_write(kind_id, destination):
        recorder.emit(
            REFUSED,
            {"code": "MINI_POLICY_WRITE_REFUSED", "detail": f"policy {plan.policy.policy_id!r} does not let {kind_id!r} write there", "to": destination.to_dict()},
            stage_id=stage.stage_id,
            kind_id=kind_id,
            artifact_id=artifact_id,
        )
        return
    recorder.emit(
        ROUTED,
        {"to": destination.to_dict()},
        stage_id=stage.stage_id,
        kind_id=kind_id,
        artifact_id=artifact_id,
    )
    if destination.target == "evidence_store":
        raw = blobs.get(body_ref)
        blocks = cut_source(artifact_id[:16], raw, str(destination.tier))
        recorder.emit(
            EVIDENCE_BATCHED,
            {
                "source_id": artifact_id[:16],
                "source_ref": body_ref,
                "tier": str(destination.tier),
                "blocks": [block.to_dict() for block in blocks],
                "to": {},
            },
            stage_id=stage.stage_id,
            kind_id=kind_id,
            artifact_id=artifact_id,
        )


def _check_reads(plan: RunPlan, recorder: _Recorder, stage: Stage) -> bool:
    kind = plan.kinds[str(stage.kind_id)]
    for port_id in stage.ports:
        port = kind.port(port_id)
        if not plan.policy.may_read(kind.kind_id, port.port_type):
            recorder.emit(
                REFUSED,
                {
                    "code": "MINI_POLICY_READ_REFUSED",
                    "detail": f"policy {plan.policy.policy_id!r} does not let {kind.kind_id!r} read a port of type {port.port_type!r}",
                    "port_id": port_id,
                },
                stage_id=stage.stage_id,
                kind_id=kind.kind_id,
            )
            return False
    return True


def _attempt_submission(
    plan: RunPlan,
    recorder: _Recorder,
    responder: Responder,
    stage: Stage,
    kind: ArtifactKind,
    brief: str,
    blobs: BlobStore,
) -> tuple[Submission, int, int] | None:
    """Ask the seat, and keep every reply — the refused ones included.

    A refused reply is stored as a blob and named on its FORMAT_FAILURE event,
    so the record says what the model actually returned and not only why it was
    turned away (FAILURE_MODES H1). An accepted body is kept verbatim; a refused
    one is no different.
    """

    compiled = plan.formats[kind.kind_id]
    policy = kind.failure_policy
    reasons: tuple[str, ...] = ()
    refused_refs: list[str] = []
    for attempt in range(policy.retries + 1):
        shown = brief if attempt == 0 else brief + "\n\n## The last reply was refused\n" + "\n".join(reasons)
        reply = responder.reply(Request(stage_id=stage.stage_id, kind_id=kind.kind_id, attempt=attempt, brief=shown))
        reply_ref = blobs.put(reply.text.encode("utf-8"))
        try:
            submission = read_submission(reply.text, kind)
        except MiniError as error:
            reasons = (str(error),)
            refused_refs.append(reply_ref)
            recorder.emit(
                FORMAT_FAILURE,
                {"attempt": attempt, "reasons": list(reasons), "code": error.code},
                stage_id=stage.stage_id,
                kind_id=kind.kind_id,
                body_ref=reply_ref,
            )
            continue
        if not submission.body.strip() or not submission.commitments.strip():
            reasons = ("body and commitments must each carry something",)
            refused_refs.append(reply_ref)
            recorder.emit(
                FORMAT_FAILURE,
                {"attempt": attempt, "reasons": list(reasons), "code": "MINI_SUBMISSION_MISSING_FIELD"},
                stage_id=stage.stage_id,
                kind_id=kind.kind_id,
                body_ref=reply_ref,
            )
            continue
        reasons = compiled.failures(submission.as_fields())
        if not reasons:
            return submission, reply.prompt_tokens, reply.completion_tokens
        refused_refs.append(reply_ref)
        recorder.emit(
            FORMAT_FAILURE,
            {"attempt": attempt, "reasons": list(reasons), "code": "MINI_FORMAT_FAILURE"},
            stage_id=stage.stage_id,
            kind_id=kind.kind_id,
            body_ref=reply_ref,
        )
    recorder.emit(
        SUBMISSION_DROPPED,
        {"attempts": policy.retries + 1, "reasons": list(reasons), "refused_refs": refused_refs},
        stage_id=stage.stage_id,
        kind_id=kind.kind_id,
    )
    return None


def run_mini(plan: RunPlan, root: Path, responder: Responder) -> RunOutcome:
    """Run one plan into one root, and return what the record says."""

    if not isinstance(root, Path):
        raise TypeError("root must be pathlib.Path")
    log_path = root / LOG_NAME
    if log_path.exists():
        raise MiniError("MINI_RUN_ROOT_OCCUPIED", f"{root} already holds a record; a record is never written over")
    root.mkdir(parents=True, exist_ok=True)
    (root / "run-header.json").write_bytes(canonical_bytes(dict(plan.header)) + b"\n")

    blobs = BlobStore(root / BLOBS_DIR)
    state = MiniState()
    recorder = _Recorder(EventLog(log_path, plan.genesis), state, plan.genesis)
    recorder.emit(
        RUN_STARTED,
        {
            "run_id": plan.run_id,
            "manifest_id": plan.manifest_id,
            "manifest_digest": plan.manifest_digest,
            "policy_id": plan.policy.policy_id,
            "policy_overrides": [dict(item) for item in plan.policy_overrides],
            "attention_policy": plan.attention.policy_id,
            "declared_order": [stage.stage_id for stage in plan.stages],
        },
    )
    _batch_evidence(plan, blobs, recorder)

    remaining = list(plan.stages)
    stop_reason = "stages_exhausted"
    steps = 0
    while remaining and steps < MAX_STEPS:
        steps += 1
        stage = remaining[0]
        if plan.attention.policy_id != ATTENTION_OFF:
            pending = tuple(PendingStage(item.stage_id, str(item.kind_id)) for item in remaining if not item.end)
            signals = compute_signals(state, plan.attention.reads_signals)
            chosen = choose_next(plan.attention, signals, pending)
            if chosen is not None:
                stage = next(item for item in remaining if item.stage_id == chosen)
                recorder.emit(
                    ATTENTION_CHOSE,
                    {"policy": plan.attention.policy_id, "chosen": chosen, "declared_next": remaining[0].stage_id},
                )
        remaining = [item for item in remaining if item.stage_id != stage.stage_id]
        if stage.end:
            stop_reason = "end_stage"
            break
        recorder.emit(STAGE_ENTERED, {"ports": list(stage.ports)}, stage_id=stage.stage_id, kind_id=stage.kind_id)
        if not _check_reads(plan, recorder, stage):
            continue
        kind = plan.kinds[str(stage.kind_id)]
        brief, exposed = render_brief(plan, state, blobs, stage)
        attempt = _attempt_submission(plan, recorder, responder, stage, kind, brief, blobs)
        if attempt is None:
            drops = state.drops_by_kind.get(kind.kind_id, 0)
            attempts = drops + state.submissions_by_kind.get(kind.kind_id, 0)
            if kind.failure_policy.exceeded(drops, attempts) and kind.failure_policy.action == "stop":
                stop_reason = "format_failures_exceeded"
                break
            continue
        submission, prompt_tokens, completion_tokens = attempt
        artifact_id, body_ref, commitments_ref = _store_artifact(blobs, stage, submission, recorder.seq)
        blocks = {str(item["block_id"]): _as_block(blobs, item) for item in state.blocks}
        measures = check_citations(submission.citations, blocks, exposed)
        recorder.emit(
            ARTIFACT_SUBMITTED,
            {
                "about": list(submission.about),
                "answers": list(submission.answers),
                "citations": [measure.to_dict() for measure in measures],
                "extra": dict(submission.extra),
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
            },
            stage_id=stage.stage_id,
            kind_id=kind.kind_id,
            artifact_id=artifact_id,
            body_ref=body_ref,
            commitments_ref=commitments_ref,
        )
        _route_output(plan, state, blobs, recorder, stage, artifact_id, body_ref)

    recorder.emit(RUN_ENDED, {"stop_reason": stop_reason})
    return RunOutcome(
        run_id=plan.run_id,
        root=root,
        genesis=plan.genesis,
        state_digest=state.digest(),
        stop_reason=stop_reason,
        stages_entered=tuple(state.stages_entered),
    )
