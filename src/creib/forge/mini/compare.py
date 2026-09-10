"""Setting two runs beside each other, and ranking neither (R27).

`compare` takes two run roots given the same sources and answered by the same
responder, and prints their verdict artifacts side by side, with each root's
executed-unchanged ledger: the kernel and transform pairs the catalogue does not
list, that a MACHINE seat executed, and that came out unchanged, each with the
input it was run on. The gate checks the sources and the responder; it does not
check that the two were asked the same question, and the report says which
manifest each was compiled from and whether they were the same (audit F-E). A
row is a result on one input, never a property of the kernel. A
model's prose about an invariance never enters a ledger; only an executed result
does. Since 10 September the same pairs are also candidate points for the
unchanged column in the verdict; the ledger is the same fact read across a run.

It prints no score, no total, no ordering, and no count offered as merit. A
template's own verdict counts are not an objective and nothing here may be tuned
to raise one — this repository's rule that a report never ranks, scores, or says
best or worst, applied to a mini run's own output. The ``--score`` flag is
refused by name so that the refusal is a thing that happens rather than a thing
intended.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from creib.errors import RecordError
from creib.strict_json import load_strict, loads_strict

from .blindspot import EXECUTION_KIND, PAIR_EXECUTION_KIND, VERDICT_KIND, catalogue_from
from .common import RUN_HEADER_DOMAIN, MiniError, content_id
from .log import BLOBS_DIR, LOG_NAME, BlobStore, MiniState, replay

MISMATCH = "MINI_COMPARE_MISMATCH"
UNSUPPORTED = "MINI_COMPARE_UNSUPPORTED"
SEAT_MACHINE = "machine"


@dataclass(frozen=True)
class RootReading:
    """One run root, read for comparison."""

    root: Path
    manifest_id: str
    #: The digest of the manifest this run was compiled from. Two roots may be compared with
    #: different manifests — that is often the point — but the report says which it was, since
    #: the gate below checks the sources and the responder and nothing else (audit F-E).
    manifest_digest: str
    responder_id: str
    source_digests: tuple[str, ...]
    verdict_bodies: tuple[str, ...]
    ledger: tuple[Mapping[str, Any], ...]


def _payload_of(blobs: BlobStore, record: Mapping[str, Any]) -> dict[str, Any]:
    try:
        parsed = loads_strict(blobs.get(str(record["commitments_ref"])).decode("utf-8"))
    except (RecordError, UnicodeDecodeError):
        return {}
    return parsed if type(parsed) is dict else {}


def read_root(root: Path) -> RootReading:
    """Read one run root: its identity, its verdicts, and its ledger."""

    if not isinstance(root, Path):
        raise TypeError("compare root must be pathlib.Path")
    try:
        header = load_strict(root / "run-header.json")
    except RecordError as error:
        raise MiniError(MISMATCH, f"{root} is not a run root: {error}") from error
    state: MiniState = replay(root / LOG_NAME, content_id(RUN_HEADER_DOMAIN, header))
    blobs = BlobStore(root / BLOBS_DIR)
    catalogue = catalogue_from(state, blobs)

    verdicts = [
        state.artifacts[key] for key in state.artifact_order if state.artifacts[key]["kind_id"] == VERDICT_KIND
    ]
    ledger: list[dict[str, Any]] = []
    for key in state.artifact_order:
        record = state.artifacts[key]
        # Both executor kinds are read: a run whose proposals carry their own rewrites wrote
        # pair executions, and a ledger that knew only the transform kind was empty for every
        # experiment after the third round (audit F-E).
        if record["kind_id"] not in (EXECUTION_KIND, PAIR_EXECUTION_KIND) or record.get("seat") != SEAT_MACHINE:
            continue
        for entry in _payload_of(blobs, record).get("executions", []):
            transform = str(entry.get("transform") or entry.get("rewrite") or "")
            pair = (str(entry.get("kernel")), transform)
            if str(entry.get("executed")) == "unchanged" and pair not in catalogue:
                ledger.append(
                    {
                        "kernel": pair[0],
                        "transform": transform,
                        "cycle": record.get("cycle", 0),
                        # The witness: what was run and what came back. Without it a row reads
                        # as a property of the kernel rather than a result on one input.
                        "input": str(entry.get("input") or ""),
                        "verdict": str(entry.get("before") or ""),
                    }
                )
    return RootReading(
        root=root,
        manifest_id=str(dict(header).get("manifest_id", "")),
        manifest_digest=str(dict(header).get("manifest_digest", "")),
        responder_id=str(state.responder_id),
        source_digests=tuple(str(item.get("sha256")) for item in dict(header).get("sources", [])),
        verdict_bodies=tuple(blobs.get(str(record["body_ref"])).decode("utf-8") for record in verdicts),
        ledger=tuple(ledger),
    )


def _require_same(left: RootReading, right: RootReading) -> None:
    if left.source_digests != right.source_digests:
        raise MiniError(MISMATCH, "the two roots were not given the same sources; there is nothing to compare")
    if left.responder_id != right.responder_id:
        raise MiniError(
            MISMATCH,
            f"the two roots were not asked the same way: {left.responder_id!r} against {right.responder_id!r}",
        )


def _section(reading: RootReading) -> list[str]:
    lines = [f"## {reading.root}", f"manifest: {reading.manifest_id}", ""]
    if reading.verdict_bodies:
        lines.append("### verdicts")
        for index, body in enumerate(reading.verdict_bodies, start=1):
            lines.extend([f"verdict {index}:", body, ""])
    else:
        lines.extend(["### verdicts", "(this root committed none)", ""])
    lines.append("### executed-unchanged ledger")
    lines.append("Pairs the catalogue does not list, that a machine seat executed and found unchanged.")
    lines.append("Each row is one result on one input, not a property of the kernel.")
    if reading.ledger:
        lines.extend(
            f"  cycle {entry['cycle']}: {entry['kernel']} unchanged under {entry['transform']}"
            + (f" on {entry['input']!r}" if entry.get("input") else "")
            + (f", both {entry['verdict']!r}" if entry.get("verdict") else "")
            for entry in reading.ledger
        )
    else:
        lines.append("  (none)")
    lines.append("")
    return lines


def compare_roots(left: Path, right: Path) -> str:
    """Render two roots side by side. Nothing here is ordered or totalled."""

    first, second = read_root(left), read_root(right)
    _require_same(first, second)
    lines = [
        "# Two runs, side by side",
        "",
        "Neither root is preferred here, and nothing below is ordered or added up.",
        "A count of verdicts is not a measure of a run, and nothing in this",
        "prototype may be tuned to raise one.",
        f"Both were given the same sources and answered by the same responder ({first.responder_id}).",
        (
            "Both were compiled from the same manifest, so the problem, the instructions, the"
            " ports and the cycles were the same."
            if first.manifest_digest and first.manifest_digest == second.manifest_digest
            else (
                "Their manifests differ, so the problem, the instructions, the ports, the"
                " routing or the cycles may differ too: what is checked here is the sources and"
                " the responder, and nothing else."
            )
        ),
        "",
    ]
    lines.extend(_section(first))
    lines.extend(_section(second))
    return "\n".join(lines)
