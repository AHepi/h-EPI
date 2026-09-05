"""Human-readable report over one or more runs: tables, failure modes, no ranking.

The report lists, per run, how many observations fell into each family and
verdict, which failure modes appeared with one example each, and the run's
scope label.  Across models it shows only presence or absence of each failure
mode.  It never orders models by merit, never sums verdicts into a score,
and closes with the non-inductive limit verbatim.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from creib.errors import RecordError
from creib.forge.models import NON_INDUCTIVE_LIMIT

from .families import Family
from .oracle import FIELD_VERDICTS, RESPONSE_VERDICTS
from .records import ObservationRecord, RunRecord


HUMAN_READINGS: Mapping[str, str] = {
    "TRANSPORT_ERROR": "The call did not complete; nothing about the model's filling behaviour was observed.",
    "EMPTY_RESPONSE": "The model returned nothing.",
    "TRUNCATED": "The model ran out of output budget before finishing.",
    "INVALID_JSON": "The reply was not parseable JSON even after prose recovery.",
    "NOT_AN_OBJECT": "The reply was JSON but not an object.",
    "REFUSAL_SUSPECTED": "The reply reads like a refusal; the phrase match is a heuristic.",
    "PREREQUISITE_UNAVAILABLE": "A chained variant could not be built because its baseline output was unusable.",
    "MISMATCH": "At least one field value differs from the proposed oracle.",
    "MISSING_REQUIRED": "A required key was omitted.",
    "EXTRA_FIELD": "A key outside the schema was emitted.",
    "TYPE_VIOLATION": "A field has the wrong JSON type.",
    "PATTERN_VIOLATION": "A field violates its declared pattern (for example date or phone format).",
    "ENUM_VIOLATION": "A field is outside its declared enumeration.",
    "LENGTH_VIOLATION": "A field exceeds its declared length bound.",
    "UNEXPECTED_PRESENT": "A field expected to be absent was emitted (schema-ignoring or optional-field over-filling).",
    "SCHEMA_INVALID": "The object fails the form schema for a reason not attributable to one field.",
    "IDENTICAL_TO_BASELINE": "Inverting the formatting instruction changed nothing; the instruction may be ignored or dominated by the schema pattern.",
    "CONTROL_ACCEPTED": "The oracle accepted a deliberately corrupted output; the check is vacuous for that corruption.",
    "CONTROL_REJECTED": "The oracle rejected the uncorrupted reference output; the oracle or the reference is wrong.",
    "DEPENDENCE_CHANGED": "Removing the declared load-bearing sentence changed the output; the dependence is recorded, not judged.",
    "DEPENDENCE_UNCHANGED": "Removing the declared load-bearing sentence changed nothing for this case.",
    "FORMAT_NOT_ENFORCED": "A structural violation occurred although a format schema was sent; server-side enforcement cannot be assumed.",
}


def _table(rows: Iterable[tuple[str, str]]) -> list[dict[str, object]]:
    counts: dict[tuple[str, str], int] = {}
    for key in rows:
        counts[key] = counts.get(key, 0) + 1
    return [{"family": family, "verdict": verdict, "count": count} for (family, verdict), count in sorted(counts.items())]


def build_report(run_records: list[RunRecord], observations: Iterable[ObservationRecord]) -> dict[str, Any]:
    """Aggregate runs and their observations into a plural, unranked report."""

    by_id = {observation.observation_id: observation for observation in observations}
    runs: list[dict[str, Any]] = []
    presence: dict[tuple[str, str], set[str]] = {}
    models: list[str] = []
    for run in run_records:
        if run.model not in models:
            models.append(run.model)
        run_observations: list[ObservationRecord] = []
        for observation_id in run.observation_ids:
            observation = by_id.get(observation_id)
            if observation is None:
                raise RecordError(f"run {run.run_id} references observation {observation_id} that was not supplied")
            if observation.run_id != run.run_id:
                raise RecordError(f"observation {observation_id} belongs to a different run")
            run_observations.append(observation)
        response_table = _table((observation.variant.family.value, observation.scoring.response_verdict) for observation in run_observations)
        field_table = _table(
            (observation.variant.family.value, verdict.verdict)
            for observation in run_observations
            for verdict in observation.scoring.field_verdicts
        )
        modes: dict[tuple[str, str], dict[str, Any]] = {}
        for observation in run_observations:
            for trigger in observation.routing.triggers:
                key = (observation.variant.family.value, trigger)
                presence.setdefault(key, set()).add(run.model)
                mode = modes.get(key)
                if mode is None:
                    modes[key] = {
                        "family": key[0],
                        "trigger": trigger,
                        "count": 1,
                        "example_case_id": observation.variant.base_case_id,
                        "example_observation_id": observation.observation_id,
                        "live_loci": list(observation.routing.loci),
                        "human_reading": HUMAN_READINGS.get(trigger, "No canned reading; inspect the observation."),
                    }
                else:
                    mode["count"] += 1
        runs.append(
            {
                "model": run.model,
                "run_id": run.run_id,
                "created_on": run.created_on,
                "executor_kind": run.executor_kind,
                "scope_label": run.scope_label,
                "overall_status": run.overall_status,
                "route": run.route,
                "observation_count": len(run_observations),
                "observations_with_live_loci": run.observations_with_live_loci,
                "response_verdicts_by_family": response_table,
                "field_verdicts_by_family": field_table,
                "failure_modes": [modes[key] for key in sorted(modes)],
                "format_enforced_by_server": run.format_enforced_by_server,
            }
        )
    cross_model = [
        {
            "family": family,
            "trigger": trigger,
            "present_in": sorted(present),
            "absent_in": sorted(set(models) - present),
        }
        for (family, trigger), present in sorted(presence.items())
    ]
    return {
        "schema_version": "creib.conformance-pilot.report.v1",
        "models": models,
        "ordering_note": "Runs are listed in the order supplied; no ordering by merit is implied and none can be derived from these counts.",
        "runs": runs,
        "cross_model_failure_modes": cross_model,
        "overall_status": "UNRESOLVED",
        "route": "AWAITING_HUMAN_TRIAGE",
        "epistemic_limit": NON_INDUCTIVE_LIMIT,
    }


def _md_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(cell.replace("|", "\\|") for cell in row) + " |")
    return "\n".join(lines)


def render_markdown(report: Mapping[str, Any]) -> str:
    """Render the report as Markdown; the closing sentence is the non-inductive limit."""

    parts: list[str] = ["# Task-conformance pilot report", "", str(report["ordering_note"]), ""]
    for run in report["runs"]:
        parts.append(f"## {run['model']} (run {str(run['run_id'])[:16]})")
        parts.append("")
        parts.append(f"- scope label: `{run['scope_label']}`")
        parts.append(f"- overall status: `{run['overall_status']}`; route: `{run['route']}`")
        parts.append(f"- observations: {run['observation_count']}; with live loci: {run['observations_with_live_loci']}")
        parts.append(f"- format enforced by server: `{run['format_enforced_by_server']}`")
        parts.append("")
        parts.append("### Response verdicts by family")
        parts.append("")
        parts.append(_md_table(["family", "verdict", "count"], [[str(r["family"]), str(r["verdict"]), str(r["count"])] for r in run["response_verdicts_by_family"]]))
        parts.append("")
        parts.append("### Field verdicts by family")
        parts.append("")
        parts.append(_md_table(["family", "verdict", "count"], [[str(r["family"]), str(r["verdict"]), str(r["count"])] for r in run["field_verdicts_by_family"]]))
        parts.append("")
        parts.append("### Failure modes")
        parts.append("")
        if run["failure_modes"]:
            parts.append(
                _md_table(
                    ["family", "trigger", "count", "example case", "live loci", "human reading"],
                    [
                        [str(m["family"]), str(m["trigger"]), str(m["count"]), str(m["example_case_id"]), ", ".join(m["live_loci"]), str(m["human_reading"])]
                        for m in run["failure_modes"]
                    ],
                )
            )
        else:
            parts.append("No triggers were raised for the executed variants; this is not confirmation.")
        parts.append("")
    parts.append("## Failure-mode presence across models")
    parts.append("")
    parts.append(
        _md_table(
            ["family", "trigger", "present in", "absent in"],
            [[str(m["family"]), str(m["trigger"]), ", ".join(m["present_in"]) or "-", ", ".join(m["absent_in"]) or "-"] for m in report["cross_model_failure_modes"]],
        )
    )
    parts.append("")
    parts.append(str(report["epistemic_limit"]))
    parts.append("")
    return "\n".join(parts)


__all__ = ["HUMAN_READINGS", "build_report", "render_markdown", "Family", "FIELD_VERDICTS", "RESPONSE_VERDICTS"]
