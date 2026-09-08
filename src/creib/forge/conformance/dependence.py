"""What removing one unit of the document did, unit by unit, beside the run's own repeat floor.

A UNIT_DEPENDENCE variant sends the case document with one of its headed units removed and
everything else as it was. The table this module builds says, for each run and each
relation a unit bears to the claim (``self``, the document's own argument for it;
``declared``, a unit defining a term that argument uses; ``other``), how many removals left
the form as the baseline had it, how many moved it, and which fields moved. The REPEAT
family, where nothing was removed, sits in the same table as the floor every count has to
be read against. Where the form carries an array field, the model's own list of what the
claim depends on is set beside what removal moved: a unit it named whose removal moved
nothing, and a unit it did not name whose removal moved the answer, are both visible.

Nothing here is a score. A moved field is a description of two records; the table does not
say which reply is right, sums nothing into a figure, and orders no models. Every relation
and every "defines" list was computed from the document by pattern at plan time and is
recorded on the variant, so the table can be checked against the document by hand.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from creib.errors import RecordError

from .common import NON_INDUCTIVE_LIMIT
from .families import Family
from .records import ObservationRecord, RunRecord
from .units import UNIT_RELATIONS


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


def _as_set_if_list(value: Any) -> Any:
    """A list compares as the sorted list of its items' texts: an array field of the form profile is a set of strings, and its order is not an answer."""

    if isinstance(value, list):
        return sorted(str(item) for item in value)
    return value


def _moved_fields(observation: ObservationRecord, baseline: ObservationRecord, fields: tuple[str, ...]) -> tuple[str, ...]:
    """Fields whose value or presence differs, with an array compared as a set."""

    now = observation.scoring.parsed_output or {}
    before = baseline.scoring.parsed_output or {}
    return tuple(field for field in fields if (field in now) != (field in before) or _as_set_if_list(now.get(field)) != _as_set_if_list(before.get(field)))


def _reordered_fields(observation: ObservationRecord, baseline: ObservationRecord, fields: tuple[str, ...]) -> tuple[str, ...]:
    """Array fields that hold the same items in a different order; counted apart, never as a move."""

    now = observation.scoring.parsed_output or {}
    before = baseline.scoring.parsed_output or {}
    return tuple(
        field for field in fields
        if isinstance(now.get(field), list) and isinstance(before.get(field), list)
        and now[field] != before[field] and _as_set_if_list(now[field]) == _as_set_if_list(before[field])
    )


def _array_fields(observation: ObservationRecord) -> tuple[str, ...]:
    properties = observation.variant.form_schema.get("properties", {})
    return tuple(field for field in observation.variant.field_order if isinstance(properties.get(field), Mapping) and properties[field].get("type") == "array")


def _asserted_terms(baseline: ObservationRecord) -> frozenset[str]:
    output = baseline.scoring.parsed_output or {}
    terms: set[str] = set()
    for field in _array_fields(baseline):
        value = output.get(field)
        if isinstance(value, list):
            terms.update(str(item) for item in value)
    return frozenset(terms)


def _empty_relation_row(run: RunRecord, relation: str, fields: tuple[str, ...]) -> dict[str, Any]:
    return {
        "model": run.model,
        "run_id": run.run_id,
        "relation": relation,
        "observations": 0,
        "unavailable": 0,
        "unmoved": 0,
        "moved": 0,
        "moved_by_field": {field: 0 for field in fields},
        "reordered_only": 0,
    }


def summarise_dependence(runs: list[RunRecord], observations: Iterable[ObservationRecord]) -> dict[str, Any]:
    """Per run: removals by relation, the repeat floor per case, the asserted-against-moved cross-check, and every probe."""

    by_id = {observation.observation_id: observation for observation in observations}
    relation_rows: list[dict[str, Any]] = []
    floor_rows: list[dict[str, Any]] = []
    assertion_rows: list[dict[str, Any]] = []
    probe_rows: list[dict[str, Any]] = []
    examples: list[dict[str, Any]] = []
    for run in runs:
        run_observations = _run_observations(run, by_id)
        fields: tuple[str, ...] = run_observations[0].variant.field_order if run_observations else ()
        baselines = {o.variant.base_case_id: o for o in run_observations if o.variant.family is Family.BASELINE}
        rows = {relation: _empty_relation_row(run, relation, fields) for relation in UNIT_RELATIONS}
        assertion = {
            "model": run.model,
            "run_id": run.run_id,
            "units_defining_a_term": 0,
            "asserted_and_moved": 0,
            "asserted_and_unmoved": 0,
            "not_asserted_and_moved": 0,
            "not_asserted_and_unmoved": 0,
            "unavailable": 0,
        }
        per_case: dict[str, dict[str, Any]] = {}
        for case_id, baseline in baselines.items():
            per_case[case_id] = {
                "model": run.model,
                "run_id": run.run_id,
                "case_id": case_id,
                "baseline_observation_id": baseline.observation_id,
                "baseline_available": baseline.scoring.parsed_output is not None,
                "baseline_values": {field: (baseline.scoring.parsed_output or {}).get(field) for field in fields},
                "asserted": sorted(_asserted_terms(baseline)),
                "repeats": 0,
                "repeats_moved": 0,
                "repeats_moved_by_field": {field: 0 for field in fields},
                "repeats_reordered_only": 0,
                "units": [],
                "moved_units_by_field": {field: [] for field in fields},
                "by_relation": {relation: {"units": 0, "moved": 0, "unavailable": 0} for relation in UNIT_RELATIONS},
            }
        for observation in run_observations:
            variant = observation.variant
            baseline = baselines.get(variant.base_case_id)
            if baseline is None or variant.base_case_id not in per_case:
                continue
            case_row = per_case[variant.base_case_id]
            comparable = baseline.scoring.parsed_output is not None and observation.scoring.parsed_output is not None
            if variant.family is Family.REPEAT:
                case_row["repeats"] += 1
                if comparable:
                    moved = _moved_fields(observation, baseline, fields)
                    if moved:
                        case_row["repeats_moved"] += 1
                    elif _reordered_fields(observation, baseline, fields):
                        case_row["repeats_reordered_only"] += 1
                    for field in moved:
                        case_row["repeats_moved_by_field"][field] += 1
                continue
            if variant.family is not Family.UNIT_DEPENDENCE or variant.removed_unit_id is None:
                continue
            relation = variant.removed_unit_relation or "other"
            row = rows[relation]
            row["observations"] += 1
            case_row["by_relation"][relation]["units"] += 1
            defines = tuple(variant.removed_unit_defines or ())
            asserted = bool(set(defines) & set(case_row["asserted"]))
            unit_row = {
                "unit_id": variant.removed_unit_id,
                "title": variant.removed_unit_title,
                "relation": relation,
                "defines": list(defines),
                "asserted": asserted,
                "observation_id": observation.observation_id,
                "status": "unavailable",
                "moved_fields": [],
            }
            if not comparable:
                row["unavailable"] += 1
                case_row["by_relation"][relation]["unavailable"] += 1
                if defines:
                    assertion["units_defining_a_term"] += 1
                    assertion["unavailable"] += 1
                case_row["units"].append(unit_row)
                continue
            moved = _moved_fields(observation, baseline, fields)
            unit_row["moved_fields"] = list(moved)
            if moved:
                row["moved"] += 1
                unit_row["status"] = "moved"
                case_row["by_relation"][relation]["moved"] += 1
                for field in moved:
                    row["moved_by_field"][field] += 1
                    case_row["moved_units_by_field"][field].append(variant.removed_unit_id)
                if len(examples) < 12:
                    examples.append({
                        "model": run.model,
                        "case_id": variant.base_case_id,
                        "unit_id": variant.removed_unit_id,
                        "title": variant.removed_unit_title,
                        "relation": relation,
                        "observation_id": observation.observation_id,
                        "baseline_observation_id": baseline.observation_id,
                        "moves": [f"{field}: {(baseline.scoring.parsed_output or {}).get(field)!r} -> {(observation.scoring.parsed_output or {}).get(field)!r}" for field in moved],
                    })
            else:
                row["unmoved"] += 1
                unit_row["status"] = "unmoved"
                if _reordered_fields(observation, baseline, fields):
                    row["reordered_only"] += 1
                    unit_row["status"] = "reordered"
            if defines:
                assertion["units_defining_a_term"] += 1
                key = ("asserted" if asserted else "not_asserted") + ("_and_moved" if moved else "_and_unmoved")
                assertion[key] += 1
            case_row["units"].append(unit_row)
        relation_rows.extend(rows[relation] for relation in UNIT_RELATIONS)
        assertion_rows.append(assertion)
        for case_id in sorted(per_case):
            case_row = per_case[case_id]
            floor_rows.append({
                "model": run.model,
                "run_id": run.run_id,
                "case_id": case_id,
                "repeats": case_row["repeats"],
                "moved": case_row["repeats_moved"],
                "moved_by_field": dict(case_row["repeats_moved_by_field"]),
                "reordered_only": case_row["repeats_reordered_only"],
            })
            probe_rows.append(case_row)
    return {
        "rows": relation_rows,
        "floor": floor_rows,
        "assertions": assertion_rows,
        "probes": probe_rows,
        "examples": examples,
        "reading": (
            "Each row counts UNIT_DEPENDENCE observations of one run whose removed unit bears the named "
            "relation to the claim: self is the document's own argument for the claim, declared is a "
            "unit defining a term that argument uses, other is neither; the relations and the terms were "
            "computed from the document by pattern at plan time and are recorded on each variant. "
            "'moved' means at least one form field differs from the run's own baseline reply for the "
            "same claim, an array field compared as a set of items; 'unmoved' means none does, and among "
            "the unmoved 'reordered only' counts replies whose array held the same items in another order; "
            "'unavailable' means one of the two replies did not "
            "parse, so nothing was compared. The repeat floor is the same comparison for byte-identical "
            "requests and is the noise every 'moved' count has to be read against. The assertions table "
            "sets the model's own list of what the claim depends on beside what removal moved, for the "
            "units that define at least one term. None of this scores a reply or a model."
        ),
        "epistemic_limit": NON_INDUCTIVE_LIMIT,
    }


def _md_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(cell.replace("|", "\\|") for cell in row) + " |")
    return "\n".join(lines)


def render_dependence_markdown(summary: Mapping[str, Any]) -> str:
    parts = ["# Unit removal beside the repeat floor", "", str(summary["reading"]), ""]
    fields: list[str] = []
    for row in summary["rows"]:
        for field in row["moved_by_field"]:
            if field not in fields:
                fields.append(field)
    parts.append("## Removals by relation")
    parts.append("")
    headers = ["model", "relation", "n", "unavailable", "unmoved", "of which reordered only", "moved"] + [f"moved: {field}" for field in fields]
    table = [
        [str(row["model"]), str(row["relation"]), str(row["observations"]), str(row["unavailable"]), str(row["unmoved"]), str(row["reordered_only"]), str(row["moved"])]
        + [str(row["moved_by_field"].get(field, 0)) for field in fields]
        for row in summary["rows"]
    ]
    parts.append(_md_table(headers, table) if table else "No UNIT_DEPENDENCE observation was supplied.")
    parts.append("")
    parts.append("## Repeat floor")
    parts.append("")
    floor = [
        [str(row["model"]), str(row["case_id"]), str(row["repeats"]), str(row["moved"]), str(row["reordered_only"])] + [str(row["moved_by_field"].get(field, 0)) for field in fields]
        for row in summary["floor"]
    ]
    parts.append(_md_table(["model", "case", "repeats", "moved", "reordered only"] + [f"moved: {field}" for field in fields], floor) if floor else "No REPEAT observation was supplied.")
    parts.append("")
    parts.append("## The model's asserted dependencies against removal")
    parts.append("")
    assertions = [
        [str(row["model"]), str(row["units_defining_a_term"]), str(row["asserted_and_moved"]), str(row["asserted_and_unmoved"]), str(row["not_asserted_and_moved"]), str(row["not_asserted_and_unmoved"]), str(row["unavailable"])]
        for row in summary["assertions"]
    ]
    parts.append(_md_table(["model", "units defining a term", "named and moved", "named and unmoved", "not named and moved", "not named and unmoved", "unavailable"], assertions) if assertions else "None.")
    parts.append("")
    parts.append("## Probes")
    parts.append("")
    probes: list[list[str]] = []
    for row in summary["probes"]:
        by_relation = row["by_relation"]
        probes.append([
            str(row["model"]),
            str(row["case_id"]),
            "; ".join(f"{field}={value!r}" for field, value in row["baseline_values"].items() if field not in {f for f in row["baseline_values"] if isinstance(row["baseline_values"][f], list)}) or "-",
            ", ".join(row["asserted"]) or "-",
            f"{row['repeats_moved']} of {row['repeats']}",
            " / ".join(f"{relation} {by_relation[relation]['moved']} of {by_relation[relation]['units']}" for relation in UNIT_RELATIONS),
            "; ".join(f"{field}: {', '.join(units)}" for field, units in row["moved_units_by_field"].items() if units) or "-",
        ])
    parts.append(_md_table(["model", "case", "baseline", "named as essential", "repeats moved", "removals moved (self / declared / other)", "units that moved a field"], probes) if probes else "None.")
    parts.append("")
    parts.append("## Examples")
    parts.append("")
    examples = [
        [str(e["model"]), str(e["case_id"]), f"{e['unit_id']} {e['title']} ({e['relation']})", f"`{e['baseline_observation_id'][:16]}` to `{e['observation_id'][:16]}`", "; ".join(e["moves"])]
        for e in summary["examples"]
    ]
    parts.append(_md_table(["model", "case", "unit removed", "records", "moves"], examples) if examples else "None.")
    parts.append("")
    parts.append(str(summary["epistemic_limit"]))
    parts.append("")
    return "\n".join(parts)


__all__ = ["render_dependence_markdown", "summarise_dependence"]
