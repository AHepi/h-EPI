"""What a further cycle did, cycle by cycle, beside the run's own repeat floor.

A cycle shows the model its previous answer and asks it to check and correct it. The table
this module builds says, for each run, criticism source, and cycle index, how many cycles
returned the same form as the step before, how many differed, and how the oracle's verdict
per field moved between the two: a match that became a miss, a miss that became a match. The
same counts for the REPEAT family, where the request was byte-identical and nothing was asked
to change, sit in the same table as the floor every cycle count has to be read against.

Nothing here is a score. A miss that became a match is a description of two records and the
oracle's reading of each; the table does not say the second answer is better, does not sum
the moves into a figure, and does not order models.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from creib.errors import RecordError

from .common import NON_INDUCTIVE_LIMIT
from .families import ORACLE_FREE_FIELD_VERDICTS, ORACLE_FREE_GROUNDING_VERDICTS, Family
from .records import ObservationRecord, RunRecord

_MISS = frozenset({"MISMATCH", "MISSING_REQUIRED", "EXTRA_FIELD", "TYPE_VIOLATION", "PATTERN_VIOLATION", "ENUM_VIOLATION", "LENGTH_VIOLATION", "UNEXPECTED_PRESENT"})


def _run_observations(run: RunRecord, by_id: Mapping[str, ObservationRecord]) -> list[ObservationRecord]:
    found: list[ObservationRecord] = []
    for observation_id in run.observation_ids:
        observation = by_id.get(observation_id)
        if observation is None:
            raise RecordError(f"run {run.run_id} references observation {observation_id} that was not supplied")
        if observation.run_id != run.run_id:
            raise RecordError(f"observation {observation_id} belongs to a different run")
        found.append(observation)
    return found


def _verdicts(observation: ObservationRecord) -> dict[str, str]:
    return {item.field: item.verdict for item in observation.scoring.field_verdicts}


def _value_changed(field: str, observation: ObservationRecord, previous: ObservationRecord) -> bool:
    keys = [field]
    variant = observation.variant
    if variant.grounding is not None and variant.grounding.active and field in variant.active_span_fields:
        keys.append(variant.span_key(field))
    now = observation.scoring.parsed_output or {}
    before = previous.scoring.parsed_output or {}
    return any((key in now) != (key in before) or now.get(key) != before.get(key) for key in keys)


def _empty_row(run: RunRecord, kind: str, criticism: str | None, index: int | None) -> dict[str, Any]:
    return {
        "model": run.model,
        "run_id": run.run_id,
        "kind": kind,
        "criticism": criticism,
        "cycle": index,
        "observations": 0,
        "prerequisite_unavailable": 0,
        "not_comparable": 0,
        "identical_to_previous": 0,
        "differing_from_previous": 0,
        "match_to_miss": 0,
        "miss_to_match": 0,
        "other_moves": 0,
        "with_criticism": 0,
        "criticised_fields": 0,
        "criticised_fields_changed": 0,
        "criticised_fields_still_failing": 0,
        "field_moves": {},
        "examples": [],
    }


def _count(row: dict[str, Any], observation: ObservationRecord, previous: ObservationRecord | None) -> None:
    row["observations"] += 1
    if observation.scoring.response_verdict == "PREREQUISITE_UNAVAILABLE":
        row["prerequisite_unavailable"] += 1
        return
    if previous is None or previous.scoring.parsed_output is None or observation.scoring.parsed_output is None:
        row["not_comparable"] += 1
        return
    if observation.scoring.changed_vs_baseline is False:
        row["identical_to_previous"] += 1
    elif observation.scoring.changed_vs_baseline is True:
        row["differing_from_previous"] += 1
    else:
        row["not_comparable"] += 1
        return
    earlier = _verdicts(previous)
    later = _verdicts(observation)
    moved: list[str] = []
    for field in sorted(set(earlier) | set(later)):
        before = earlier.get(field, "NOT_SCORED")
        after = later.get(field, "NOT_SCORED")
        if before == after:
            continue
        if before == "MATCH" and after in _MISS:
            row["match_to_miss"] += 1
        elif before in _MISS and after == "MATCH":
            row["miss_to_match"] += 1
        else:
            row["other_moves"] += 1
        key = f"{field}: {before} -> {after}"
        row["field_moves"][key] = row["field_moves"].get(key, 0) + 1
        moved.append(key)
    criticisms = observation.variant.cycle_criticisms or ()
    if criticisms:
        row["with_criticism"] += 1
        grounded = {item.field: item.verdict for item in observation.scoring.grounding_verdicts}
        for item in criticisms:
            row["criticised_fields"] += 1
            if _value_changed(item.field, observation, previous):
                row["criticised_fields_changed"] += 1
            still = later.get(item.field) == item.verdict if item.verdict in ORACLE_FREE_FIELD_VERDICTS else grounded.get(item.field) == item.verdict
            if item.verdict in ORACLE_FREE_GROUNDING_VERDICTS or item.verdict in ORACLE_FREE_FIELD_VERDICTS:
                if still:
                    row["criticised_fields_still_failing"] += 1
    if moved and len(row["examples"]) < 6:
        row["examples"].append({"case_id": observation.variant.base_case_id, "observation_id": observation.observation_id, "previous_observation_id": previous.observation_id, "moves": moved})


def summarise_cycles(runs: list[RunRecord], observations: Iterable[ObservationRecord]) -> dict[str, Any]:
    """One row per run, criticism source, and cycle index, and one REPEAT floor row per run."""

    by_id = {observation.observation_id: observation for observation in observations}
    rows: list[dict[str, Any]] = []
    for run in runs:
        run_observations = _run_observations(run, by_id)
        groups: dict[tuple[str, int], dict[str, Any]] = {}
        floor = _empty_row(run, "repeat", None, None)
        for observation in run_observations:
            variant = observation.variant
            previous = None if observation.baseline_observation_id is None else by_id.get(observation.baseline_observation_id)
            if variant.family is Family.CYCLE and variant.cycle_index is not None:
                key = (variant.cycle_criticism or "none", variant.cycle_index)
                row = groups.setdefault(key, _empty_row(run, "cycle", key[0], key[1]))
                _count(row, observation, previous)
            elif variant.family is Family.REPEAT:
                _count(floor, observation, previous)
        for key in sorted(groups):
            rows.append(groups[key])
        rows.append(floor)
    for row in rows:
        row["field_moves"] = [{"move": move, "count": count} for move, count in sorted(row["field_moves"].items(), key=lambda item: (-item[1], item[0]))]
    return {
        "schema_version": "creib.conformance-pilot.cycles.v1",
        "rows": rows,
        "reading": (
            "Each row counts the cycles (or repeats) of one run whose form was identical to, or differed from, the step before, "
            "and how the oracle's per-field verdict moved between the two records. The repeat row is the floor: what the same "
            "request produced with nothing asked to change. A move in either direction is a description of two records, not a "
            "score; the criticised-field columns say how many fields a cycle was told about, how many of those it changed, and "
            "how many still fail the same check afterwards."
        ),
        "epistemic_limit": NON_INDUCTIVE_LIMIT,
    }


def _md_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(cell.replace("|", "\\|") for cell in row) + " |")
    return "\n".join(lines)


def render_cycles_markdown(summary: Mapping[str, Any]) -> str:
    parts = ["# Cycles beside the repeat floor", ""]
    parts.append(str(summary["reading"]))
    parts.append("")
    headers = ["model", "row", "n", "unavailable", "not comparable", "identical", "differing", "match to miss", "miss to match", "other moves", "told of", "criticised fields", "changed", "still failing"]
    table: list[list[str]] = []
    for row in summary["rows"]:
        label = "repeat" if row["kind"] == "repeat" else f"cycle {row['cycle']}, criticism {row['criticism']}"
        table.append([
            str(row["model"]), label, str(row["observations"]), str(row["prerequisite_unavailable"]), str(row["not_comparable"]),
            str(row["identical_to_previous"]), str(row["differing_from_previous"]), str(row["match_to_miss"]), str(row["miss_to_match"]), str(row["other_moves"]),
            str(row["with_criticism"]), str(row["criticised_fields"]), str(row["criticised_fields_changed"]), str(row["criticised_fields_still_failing"]),
        ])
    parts.append(_md_table(headers, table))
    parts.append("")
    parts.append("## Field moves")
    parts.append("")
    moves: list[list[str]] = []
    for row in summary["rows"]:
        label = "repeat" if row["kind"] == "repeat" else f"cycle {row['cycle']}, criticism {row['criticism']}"
        for item in row["field_moves"]:
            moves.append([str(row["model"]), label, str(item["move"]), str(item["count"])])
    parts.append(_md_table(["model", "row", "move", "count"], moves) if moves else "No field verdict moved.")
    parts.append("")
    parts.append("## Examples")
    parts.append("")
    examples: list[list[str]] = []
    for row in summary["rows"]:
        label = "repeat" if row["kind"] == "repeat" else f"cycle {row['cycle']}, criticism {row['criticism']}"
        for example in row["examples"]:
            examples.append([str(row["model"]), label, str(example["case_id"]), f"`{example['previous_observation_id'][:16]}` to `{example['observation_id'][:16]}`", "; ".join(example["moves"])])
    parts.append(_md_table(["model", "row", "case", "records", "moves"], examples) if examples else "None.")
    parts.append("")
    parts.append(str(summary["epistemic_limit"]))
    parts.append("")
    return "\n".join(parts)


__all__ = ["render_cycles_markdown", "summarise_cycles"]
