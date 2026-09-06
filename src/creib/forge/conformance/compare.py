"""Compare two runs of the same model request by request: drift, regressions, the noise floor.

The request digest is a function of the prompt, the schema, the options, and the model
name, so two runs of one model on one plan send byte-identical requests, and a repeat is
the same request sent again.  ``compare_runs`` pairs each request of the left run with the
same request of the right run, repeat by repeat, and says whether the two replies carried
the same form values, which fields differed, and how the oracle's verdicts moved.  A
difference is not a wrong answer: identity is decided without consulting the oracle, and
verdict changes are listed separately so a reader can tell drift in a total from drift in
a field nobody scored.  Each run's own repeat count is shown beside the comparison, because
a difference across runs means nothing until it is read against the difference within one.

Nothing here ranks, scores, or prefers either run.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from creib.canonical import canonical_bytes
from creib.errors import RecordError
from .common import NON_INDUCTIVE_LIMIT
from .families import Family
from .records import ObservationRecord, RunRecord


def _form_values(observation: ObservationRecord) -> dict[str, Any] | None:
    parsed = observation.scoring.parsed_output
    if parsed is None:
        return None
    return {field: parsed[field] for field in observation.variant.field_order if field in parsed}


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


def _keyed(observations: Iterable[ObservationRecord]) -> dict[tuple[str, int], ObservationRecord]:
    keyed: dict[tuple[str, int], ObservationRecord] = {}
    for observation in observations:
        if not observation.variant.model_call or observation.request_digest is None:
            continue
        key = (observation.request_digest, observation.variant.repeat_index or 0)
        if key in keyed:
            raise RecordError(f"run {observation.run_id} holds two observations for request {key[0]} repeat {key[1]}")
        keyed[key] = observation
    return keyed


def _repeat_floor(observations: Iterable[ObservationRecord]) -> dict[str, int]:
    repeats = [o for o in observations if o.variant.family is Family.REPEAT]
    return {
        "repeats": len(repeats),
        "identical_to_baseline": sum(1 for o in repeats if o.scoring.changed_vs_baseline is False),
        "differing_from_baseline": sum(1 for o in repeats if o.scoring.changed_vs_baseline is True),
        "not_comparable": sum(1 for o in repeats if o.scoring.changed_vs_baseline is None),
    }


def _run_summary(run: RunRecord, observations: list[ObservationRecord]) -> dict[str, Any]:
    return {
        "run_id": run.run_id,
        "model": run.model,
        "created_on": run.created_on,
        "plan_id": run.plan_id,
        "executor_kind": run.executor_kind,
        "scope_label": run.scope_label,
        "observations": len(observations),
        "repeat_floor": _repeat_floor(observations),
    }


def compare_runs(left: RunRecord, right: RunRecord, observations: Iterable[ObservationRecord]) -> dict[str, Any]:
    """Pair the requests two runs share and report identity, differing fields, and verdict moves."""

    if left.run_id == right.run_id:
        raise RecordError("compare needs two different runs")
    if left.model != right.model:
        raise RecordError(
            f"runs are for different models ({left.model!r} and {right.model!r}); the model name is part of every request digest, so no request can be shared"
        )
    by_id = {observation.observation_id: observation for observation in observations}
    left_observations = _run_observations(left, by_id)
    right_observations = _run_observations(right, by_id)
    left_keyed = _keyed(left_observations)
    right_keyed = _keyed(right_observations)
    shared = sorted(set(left_keyed) & set(right_keyed), key=lambda key: (left_keyed[key].variant.base_case_id, left_keyed[key].variant.family.value, key[1]))

    identical = 0
    differing = 0
    not_comparable = 0
    field_counts: dict[str, int] = {}
    verdict_moves: dict[tuple[str, str, str], int] = {}
    response_moves: dict[tuple[str, str], int] = {}
    by_family: dict[str, dict[str, int]] = {}
    examples: list[dict[str, Any]] = []
    for key in shared:
        a = left_keyed[key]
        b = right_keyed[key]
        family = a.variant.family.value
        row = by_family.setdefault(family, {"shared": 0, "identical": 0, "differing": 0, "not_comparable": 0})
        row["shared"] += 1
        if a.scoring.response_verdict != b.scoring.response_verdict:
            move = (a.scoring.response_verdict, b.scoring.response_verdict)
            response_moves[move] = response_moves.get(move, 0) + 1
        left_verdicts = {v.field: v.verdict for v in a.scoring.field_verdicts}
        right_verdicts = {v.field: v.verdict for v in b.scoring.field_verdicts}
        for field in a.variant.field_order:
            before = left_verdicts.get(field, "NOT_SCORED")
            after = right_verdicts.get(field, "NOT_SCORED")
            if before != after:
                move3 = (field, before, after)
                verdict_moves[move3] = verdict_moves.get(move3, 0) + 1
        x = _form_values(a)
        y = _form_values(b)
        if x is None or y is None:
            not_comparable += 1
            row["not_comparable"] += 1
            continue
        if canonical_bytes(x) == canonical_bytes(y):
            identical += 1
            row["identical"] += 1
            continue
        differing += 1
        row["differing"] += 1
        changed_fields = [field for field in a.variant.field_order if x.get(field) != y.get(field) or (field in x) != (field in y)]
        for field in changed_fields:
            field_counts[field] = field_counts.get(field, 0) + 1
        if len(examples) < 20:
            examples.append(
                {
                    "case_id": a.variant.base_case_id,
                    "family": family,
                    "repeat_index": key[1] or None,
                    "fields": changed_fields,
                    "left_observation_id": a.observation_id,
                    "right_observation_id": b.observation_id,
                }
            )

    return {
        "schema_version": "creib.conformance-pilot.compare.v1",
        "left": _run_summary(left, left_observations),
        "right": _run_summary(right, right_observations),
        "shared_requests": len(shared),
        "only_left": len(set(left_keyed) - set(right_keyed)),
        "only_right": len(set(right_keyed) - set(left_keyed)),
        "identical": identical,
        "differing": differing,
        "not_comparable": not_comparable,
        "differing_fields": [{"field": field, "count": count} for field, count in sorted(field_counts.items(), key=lambda item: (-item[1], item[0]))],
        "by_family": [{"family": family, **row} for family, row in sorted(by_family.items())],
        "field_verdict_moves": [
            {"field": field, "left": before, "right": after, "count": count}
            for (field, before, after), count in sorted(verdict_moves.items(), key=lambda item: (-item[1], item[0]))
        ],
        "response_verdict_moves": [{"left": before, "right": after, "count": count} for (before, after), count in sorted(response_moves.items(), key=lambda item: (-item[1], item[0]))],
        "examples": examples,
        "reading": (
            "Identity compares the declared form fields of the two replies to the same request and never consults the oracle; "
            "a difference is drift, not a wrong answer, and a verdict move says how the oracle read each side. "
            "Read the counts against each run's own repeat floor before attributing anything to time or to a version."
        ),
        "epistemic_limit": NON_INDUCTIVE_LIMIT,
    }


def _md_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(cell.replace("|", "\\|") for cell in row) + " |")
    return "\n".join(lines)


def render_compare_markdown(comparison: Mapping[str, Any]) -> str:
    left = comparison["left"]
    right = comparison["right"]
    parts: list[str] = [f"# Two runs of {left['model']}, request by request", ""]
    for label, run in (("Left", left), ("Right", right)):
        floor = run["repeat_floor"]
        parts.append(
            f"- {label}: run `{str(run['run_id'])[:16]}`, created {run['created_on']}, plan `{str(run['plan_id'])[:16]}`, executor `{run['executor_kind']}`, "
            f"scope label `{run['scope_label']}`, {run['observations']} observations; repeats {floor['repeats']}, identical to baseline {floor['identical_to_baseline']}, differing {floor['differing_from_baseline']}"
        )
    parts.append("")
    parts.append(
        f"Shared requests: {comparison['shared_requests']} (only in the left run: {comparison['only_left']}; only in the right: {comparison['only_right']}). "
        f"Identical form values: {comparison['identical']}. Differing: {comparison['differing']}. Not comparable, one side unparsed: {comparison['not_comparable']}."
    )
    parts.append("")
    parts.append("## By family")
    parts.append("")
    parts.append(_md_table(["family", "shared", "identical", "differing", "not comparable"], [[r["family"], str(r["shared"]), str(r["identical"]), str(r["differing"]), str(r["not_comparable"])] for r in comparison["by_family"]]))
    parts.append("")
    parts.append("## Fields that differed")
    parts.append("")
    if comparison["differing_fields"]:
        parts.append(_md_table(["field", "pairs"], [[r["field"], str(r["count"])] for r in comparison["differing_fields"]]))
    else:
        parts.append("No shared request returned different form values.")
    parts.append("")
    parts.append("## Verdict moves")
    parts.append("")
    if comparison["field_verdict_moves"]:
        parts.append(_md_table(["field", "left", "right", "pairs"], [[r["field"], r["left"], r["right"], str(r["count"])] for r in comparison["field_verdict_moves"]]))
    else:
        parts.append("No field verdict moved between the two runs.")
    if comparison["response_verdict_moves"]:
        parts.append("")
        parts.append(_md_table(["left response", "right response", "pairs"], [[r["left"], r["right"], str(r["count"])] for r in comparison["response_verdict_moves"]]))
    parts.append("")
    parts.append("## Examples")
    parts.append("")
    if comparison["examples"]:
        parts.append(
            _md_table(
                ["case", "family", "repeat", "fields", "left", "right"],
                [[e["case_id"], e["family"], "" if e["repeat_index"] is None else str(e["repeat_index"]), ", ".join(e["fields"]), f"`{e['left_observation_id'][:16]}`", f"`{e['right_observation_id'][:16]}`"] for e in comparison["examples"]],
            )
        )
    else:
        parts.append("None.")
    parts.append("")
    parts.append(str(comparison["reading"]))
    parts.append("")
    parts.append(str(comparison["epistemic_limit"]))
    parts.append("")
    return "\n".join(parts)


__all__ = ["compare_runs", "render_compare_markdown"]
