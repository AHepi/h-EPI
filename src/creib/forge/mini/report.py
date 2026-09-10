"""Read a mini run root and say what it holds, deterministically and without a model.

Every round of the experiments needed the same reading: how many proposals a run got
through, how many the executor could run, which expectations the machine contradicted, which
cells of a grid were covered, and what the verdict seat committed. That reading was written by
hand each time, which put a person in the middle of a loop that has no other reason to stop.

Nothing here judges anything. It counts what the record says and lays the disagreements out
beside the texts that produced them; whether a disagreement is a blind spot is a reading a
person makes (``docs/mini/AUTONOMY.md``), and this module neither makes it nor pretends to.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from creib.errors import RecordError
from creib.strict_json import load_strict

from .blindspot import (
    EXECUTION_KIND,
    GRID_SOURCE,
    PAIR_EXECUTION_KIND,
    PAIR_PROPOSAL_PREFIX,
    PROPOSAL_KIND,
    VERDICT_KIND,
    grid_cells,
    proposal_fields,
)
from .common import RUN_HEADER_DOMAIN, content_id
from .log import BlobStore, replay

#: Every artifact kind this module reads as a proposal: the transform proposal of the first
#: template, and any pair proposal, whatever a manifest names it.
PROPOSAL_KINDS: tuple[str, ...] = (PROPOSAL_KIND,)


@dataclass(frozen=True)
class ExecutionRow:
    """One execution as the executor recorded it, with the proposal's own texts beside it."""

    cycle: int
    proposal: str
    kernel: str
    transform: str
    executed: str
    before: str
    after: str
    expect: str
    as_expected: bool | None
    detail: str
    cell: str
    source: str
    rewritten: str

    @property
    def parts_changed(self) -> int:
        """How many lines differ between the two texts, counted as a multiset.

        A pair is a probe only if exactly one thing differs (register M14), and a seat asked
        for a realistic reply will change four. Lines are what the notations of these grids
        call parts, so this counts parts where it can and over-counts where a part spans lines;
        it is a measure to sort by, never a refusal.
        """

        from collections import Counter

        before, after = Counter(self.source.split("\n")), Counter(self.rewritten.split("\n"))
        return sum(((before - after) + (after - before)).values())

    @property
    def disagreed(self) -> bool:
        """The machine's answer differs from what the proposal expected of it."""

        return self.as_expected is False


@dataclass(frozen=True)
class VerdictRow:
    """One entry of a verdict artifact's commitments."""

    cycle: int
    proposal: str
    kernel: str
    executed: str
    expected: str
    predicted: str | None
    reading: str
    catalogued: bool
    standing: str
    column: str | None


@dataclass(frozen=True)
class RunReading:
    """What one run root holds. Counts and rows only; no judgement of any kind."""

    root: str
    run_id: str
    manifest_id: str
    responder_id: str
    ended: bool
    cycles_completed: int
    stop_reason: str
    proposals: int
    calls_refused: int
    drops: int
    format_failures: int
    executed: Mapping[str, int]
    standings: Mapping[str, int]
    columns: Mapping[str, int]
    readings: Mapping[str, int]
    executions: tuple[ExecutionRow, ...]
    verdicts: tuple[VerdictRow, ...]
    cells_in_grid: tuple[str, ...]
    cells_named: tuple[str, ...]

    @property
    def disagreements(self) -> tuple[ExecutionRow, ...]:
        return tuple(row for row in self.executions if row.disagreed)

    @property
    def ran(self) -> int:
        """Executions the kernel actually ran: not a duplicate, unrunnable or unreadable."""

        return sum(count for name, count in self.executed.items() if name in ("moved", "unchanged"))

    @property
    def multi_part_pairs(self) -> int:
        """Pairs whose two texts differ by more than one line, which probe nothing in particular."""

        return sum(1 for row in self.executions if row.executed in ("moved", "unchanged") and row.parts_changed > 2)

    @property
    def cells_uncovered(self) -> tuple[str, ...]:
        named = set(self.cells_named)
        return tuple(cell for cell in self.cells_in_grid if cell not in named)

    @property
    def cells_off_grid(self) -> tuple[str, ...]:
        """Cells a seat named that the grid does not hold: it wrote its own instead of the one given."""

        listed = set(self.cells_in_grid)
        return tuple(cell for cell in self.cells_named if cell not in listed) if self.cells_in_grid else ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "root": self.root,
            "run_id": self.run_id,
            "manifest_id": self.manifest_id,
            "responder_id": self.responder_id,
            "ended": self.ended,
            "cycles_completed": self.cycles_completed,
            "stop_reason": self.stop_reason,
            "proposals": self.proposals,
            "ran": self.ran,
            "drops": self.drops,
            "format_failures": self.format_failures,
            "executed": dict(sorted(self.executed.items())),
            "standings": dict(sorted(self.standings.items())),
            "columns": dict(sorted(self.columns.items())),
            "readings": dict(sorted(self.readings.items())),
            "cells_in_grid": list(self.cells_in_grid),
            "cells_named": list(self.cells_named),
            "cells_uncovered": list(self.cells_uncovered),
            "cells_off_grid": list(self.cells_off_grid),
            "disagreements": [
                {
                    "cycle": row.cycle,
                    "proposal": row.proposal,
                    "kernel": row.kernel,
                    "cell": row.cell,
                    "executed": row.executed,
                    "expect": row.expect,
                    "before": row.before,
                    "after": row.after,
                    "input": row.source,
                    "rewritten": row.rewritten,
                    "parts_changed": row.parts_changed,
                }
                for row in self.disagreements
            ],
        }


def _genesis(root: Path) -> str:
    try:
        header = load_strict(root / "run-header.json")
    except RecordError as error:
        raise RecordError(f"{root} carries no readable run header: {error}") from error
    return content_id(RUN_HEADER_DOMAIN, header)


def _is_proposal(kind_id: str) -> bool:
    return kind_id in PROPOSAL_KINDS or kind_id.startswith(PAIR_PROPOSAL_PREFIX)


def _text(value: Any) -> str:
    return value if type(value) is str else ""


def read_run(root: Path) -> RunReading:
    """Read one run root: replay its log, and lay out what its seats committed."""

    state = replay(root / "log.jsonl", _genesis(root))
    blobs = BlobStore(root / "blobs")
    fields: dict[str, dict[str, Any]] = {}
    cells: list[str] = []
    proposals = 0
    for key in state.artifact_order:
        record = state.artifacts[key]
        kind_id = str(record["kind_id"])
        parsed = proposal_fields(blobs.get(str(record["commitments_ref"])).decode("utf-8"), record.get("extra"))
        if parsed is None:
            parsed = {}
        fields[str(record["artifact_id"])[:16]] = parsed
        if _is_proposal(kind_id):
            proposals += 1
        cell = parsed.get("cell")
        if type(cell) is str and cell.strip():
            cells.append(" ".join(cell.split()))

    executions: list[ExecutionRow] = []
    verdicts: list[VerdictRow] = []
    for key in state.artifact_order:
        record = state.artifacts[key]
        kind_id = str(record["kind_id"])
        if kind_id not in (EXECUTION_KIND, PAIR_EXECUTION_KIND, VERDICT_KIND):
            continue
        try:
            body = json.loads(blobs.get(str(record["commitments_ref"])).decode("utf-8"))
        except ValueError:
            continue
        cycle = int(record.get("cycle", 0))
        if kind_id in (EXECUTION_KIND, PAIR_EXECUTION_KIND):
            for entry in body.get("executions", []):
                proposal = _text(entry.get("proposal"))
                own = fields.get(proposal[:16], {})
                executions.append(
                    ExecutionRow(
                        cycle=cycle,
                        proposal=proposal,
                        kernel=_text(entry.get("kernel")),
                        transform=_text(entry.get("transform")) or _text(entry.get("rewrite")),
                        executed=_text(entry.get("executed")),
                        before=_text(entry.get("before")),
                        after=_text(entry.get("after")),
                        expect=_text(entry.get("expect")),
                        as_expected=entry.get("as_expected") if type(entry.get("as_expected")) is bool else None,
                        detail=_text(entry.get("detail")),
                        cell=_text(own.get("cell")),
                        source=_text(entry.get("input")) or _text(own.get("input")),
                        rewritten=_text(entry.get("rewritten")) or _text(own.get("rewritten")),
                    )
                )
            continue
        for entry in body.get("verdicts", []):
            predicted = entry.get("predicted")
            verdicts.append(
                VerdictRow(
                    cycle=cycle,
                    proposal=_text(entry.get("proposal")),
                    kernel=_text(entry.get("kernel")),
                    executed=_text(entry.get("executed")),
                    expected=_text(entry.get("expected")),
                    predicted=predicted if type(predicted) is str else None,
                    reading=_text(entry.get("reading")),
                    catalogued=bool(entry.get("catalogued")),
                    standing=_text(entry.get("standing")),
                    column=entry.get("column") if type(entry.get("column")) is str else None,
                )
            )

    return RunReading(
        root=root.name,
        run_id=state.run_id,
        manifest_id=state.manifest_id,
        responder_id=state.responder_id,
        ended=state.ended,
        cycles_completed=state.cycles_completed,
        stop_reason=state.stop_reason,
        proposals=proposals,
        calls_refused=sum(state.format_failures_by_kind.values()),
        drops=sum(state.drops_by_kind.values()),
        format_failures=sum(state.format_failures_by_kind.values()),
        executed=Counter(row.executed for row in executions),
        standings=Counter(row.standing for row in verdicts),
        columns=Counter(row.column for row in verdicts if row.column),
        readings=Counter(row.reading for row in verdicts if row.reading),
        executions=tuple(executions),
        verdicts=tuple(verdicts),
        cells_in_grid=grid_cells(state, blobs),
        cells_named=tuple(dict.fromkeys(cells)),
    )


def _counts(counter: Mapping[str, int]) -> str:
    return ", ".join(f"{name} {count}" for name, count in sorted(counter.items())) or "none"


def render(reading: RunReading) -> str:
    """The reading as a person reads it: what the run did, then every disagreement in full."""

    lines = [
        f"# {reading.root}",
        "",
        f"{reading.responder_id} on {reading.manifest_id}, run {reading.run_id}.",
        (
            f"Ended after {reading.cycles_completed} cycles ({reading.stop_reason})."
            if reading.ended
            else f"Did not end; {reading.cycles_completed} cycles are in the record."
        ),
        "",
        f"- proposals: {reading.proposals}, of which the executor ran {reading.ran}",
        f"- executions: {_counts(reading.executed)}",
        f"- standings: {_counts(reading.standings)}",
        f"- columns: {_counts(reading.columns)}",
        f"- readings: {_counts(reading.readings)}",
        f"- refused replies: {reading.format_failures}, submissions dropped: {reading.drops}",
        f"- pairs changing more than one part: {reading.multi_part_pairs} of {reading.ran} run (M14)",
    ]
    if reading.cells_in_grid:
        lines.append(
            f"- grid: {len(reading.cells_named)} of {len(reading.cells_in_grid)} cells named"
            + (f"; not named: {'; '.join(reading.cells_uncovered)}" if reading.cells_uncovered else "")
            + (f"; {len(reading.cells_off_grid)} named that the grid does not hold" if reading.cells_off_grid else "")
        )
    lines.extend(["", "## Where the machine contradicted the proposal", ""])
    if not reading.disagreements:
        lines.append("Nothing: every expectation the executor could run held.")
    for row in reading.disagreements:
        lines.extend(
            [
                f"### cycle {row.cycle}, proposal {row.proposal[:16]}"
                + (f", cell `{row.cell}`" if row.cell else ""),
                "",
                f"{row.kernel}: expected to {row.expect}, {row.executed}, {row.before!r} to {row.after!r}."
                + (f" The two texts differ in {row.parts_changed} lines." if row.parts_changed > 2 else ""),
                "",
                "```",
                row.source,
                "```",
                "",
                "```",
                row.rewritten,
                "```",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def read_roots(roots: tuple[Path, ...]) -> tuple[RunReading, ...]:
    return tuple(read_run(root) for root in roots)


__all__ = ["ExecutionRow", "RunReading", "VerdictRow", "read_run", "read_roots", "render"]
