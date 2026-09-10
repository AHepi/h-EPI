"""Setting two runs beside each other, and ranking neither (R27).

`compare` takes two run roots that were asked the same way — the same sources,
the same responder — and prints their verdict artifacts side by side, with each
root's executed-invariance ledger: the kernel and transform pairs the catalogue
does not list, that a MACHINE seat executed, and that came out unchanged. A
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

from .blindspot import EXECUTION_KIND, VERDICT_KIND, catalogue_from
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
        if record["kind_id"] != EXECUTION_KIND or record.get("seat") != SEAT_MACHINE:
            continue
        for entry in _payload_of(blobs, record).get("executions", []):
            pair = (str(entry.get("kernel")), str(entry.get("transform")))
            if str(entry.get("executed")) == "unchanged" and pair not in catalogue:
                ledger.append({"kernel": pair[0], "transform": pair[1], "cycle": record.get("cycle", 0)})
    return RootReading(
        root=root,
        manifest_id=str(dict(header).get("manifest_id", "")),
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
    lines.append("### executed-invariance ledger")
    lines.append("Pairs the catalogue does not list, that a machine seat executed and found unchanged.")
    if reading.ledger:
        lines.extend(
            f"  cycle {entry['cycle']}: {entry['kernel']} is invariant under {entry['transform']}"
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
        f"Both were given the same sources and asked the same way ({first.responder_id}).",
        "",
    ]
    lines.extend(_section(first))
    lines.extend(_section(second))
    return "\n".join(lines)
