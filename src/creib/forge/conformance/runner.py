"""Execute a plan for one model and publish observation and run records.

The runner orders baseline variants first, materialises ROUND_TRIP variants
from the model's own baseline output, compares NEGATION and IMPORT_DEPENDENCY
outputs with the baseline, and never calls a model for NON_VACUITY controls.
It tallies verdicts and loci for human reading.  It does not compute a
score, rank a model, or declare a run passed: the run status is always
``UNRESOLVED`` and a non-empty live-locus set means unresolved criticism.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from creib.errors import RecordError

from .common import SCOPE_REFUTED, SCOPE_UNREFUTED, rfc3339
from .corpus import Corpus
from .executor import ModelExecutor
from .families import ExpectationKind, Family, Plan, Variant, materialize_round_trip
from .oracle import RESPONSE_VERDICTS, FIELD_VERDICTS, prerequisite_unavailable, score
from .prompt import build_chat_request
from .records import EXECUTOR_KINDS, ObservationRecord, RunRecord, build_observation, build_run_record, compute_run_id, publish_record
from .routing import route
from .spec import TaskSpec


_BASELINE_DEPENDENT = frozenset({Family.NEGATION, Family.IMPORT_DEPENDENCY, Family.ROUND_TRIP})


@dataclass(frozen=True)
class RunResult:
    run_record: RunRecord
    run_path: Path
    observations: tuple[ObservationRecord, ...]
    observation_paths: tuple[Path, ...]

    @property
    def unresolved(self) -> bool:
        return any(observation.routing.live_loci for observation in self.observations)


def select_variants(plan: Plan, *, families: Iterable[Family] | None = None, limit: int | None = None) -> tuple[Variant, ...]:
    """Choose variants; baselines needed by comparison families are always added."""

    chosen_families = None if families is None else frozenset(families)
    selected = [variant for variant in plan.variants if chosen_families is None or variant.family in chosen_families]
    if limit is not None:
        if type(limit) is not int or limit < 1:
            raise RecordError("limit must be a positive integer")
        selected = selected[:limit]
    baselines = {variant.base_case_id: variant for variant in plan.variants if variant.family is Family.BASELINE}
    needed_ids = set()
    for variant in selected:
        if variant.family in _BASELINE_DEPENDENT:
            base = baselines.get(variant.base_case_id)
            if base is None:
                raise RecordError(f"variant {variant.variant_id} needs a baseline for case {variant.base_case_id}")
            needed_ids.add(base.variant_id)
    selected_ids = {variant.variant_id for variant in selected}
    ordered: list[Variant] = []
    for variant in plan.variants:
        if variant.family is Family.BASELINE and (variant.variant_id in selected_ids or variant.variant_id in needed_ids):
            ordered.append(variant)
    for variant in plan.variants:
        if variant.family is not Family.BASELINE and variant.variant_id in selected_ids:
            ordered.append(variant)
    return tuple(ordered)


def run_pilot(
    *,
    spec: TaskSpec,
    corpus: Corpus,
    plan: Plan,
    model: str,
    executor: ModelExecutor,
    executor_kind: str,
    output_dir: Path,
    created_on: str,
    families: Iterable[Family] | None = None,
    limit: int | None = None,
) -> RunResult:
    if model not in spec.models:
        raise RecordError(f"model {model!r} is not declared in the pilot configuration")
    if executor_kind not in EXECUTOR_KINDS:
        raise RecordError(f"unknown executor kind {executor_kind!r}")
    if plan.pilot_id != spec.pilot_id or plan.corpus_sha256 != corpus.sha256:
        raise RecordError("plan does not belong to this specification and corpus")
    rfc3339(created_on, "created_on")
    if not isinstance(output_dir, Path):
        raise TypeError("output_dir must be pathlib.Path")
    selected_families = tuple(sorted({variant.family.value for variant in plan.variants} if families is None else {family.value for family in families}))
    if not selected_families:
        raise RecordError("no families selected")
    variants = select_variants(plan, families=families, limit=limit)
    header = {
        "schema_version": "creib.conformance-pilot.run.v1",
        "pilot_id": spec.pilot_id,
        "plan_id": plan.plan_id,
        "model": model,
        "endpoint": spec.endpoint.to_dict(),
        "executor_kind": executor_kind,
        "spec_bindings": spec.bindings_dict(),
        "created_on": created_on,
        "selected_families": list(selected_families),
        "variant_limit": limit,
    }
    run_id = compute_run_id(header)

    observations: list[ObservationRecord] = []
    paths: list[Path] = []
    baseline_by_case: dict[str, ObservationRecord] = {}
    for planned in variants:
        baseline = baseline_by_case.get(planned.base_case_id)
        baseline_output = None if baseline is None else baseline.scoring.parsed_output
        variant = planned
        request_digest: str | None = None
        response = None
        if not planned.model_call:
            scoring = score(planned, None)
            routing = route(planned, scoring, format_sent=False)
        elif planned.expectation_kind is ExpectationKind.ROUND_TRIP:
            if baseline is None or baseline_output is None:
                detail = "baseline observation missing" if baseline is None else f"baseline response verdict {baseline.scoring.response_verdict}"
                scoring = prerequisite_unavailable(detail)
                routing = route(planned, scoring, format_sent=True)
            else:
                try:
                    variant = materialize_round_trip(planned, baseline_output)
                except RecordError as exc:
                    scoring = prerequisite_unavailable(f"baseline output cannot be rendered: {exc}")
                    routing = route(planned, scoring, format_sent=True)
                else:
                    request = build_chat_request(variant, model=model, endpoint=spec.endpoint)
                    request_digest = request.request_digest
                    response = executor.complete(request)
                    scoring = score(variant, response, refusal_phrases=spec.refusal_phrases, baseline_output=baseline_output)
                    routing = route(variant, scoring, format_sent=True)
        else:
            request = build_chat_request(planned, model=model, endpoint=spec.endpoint)
            request_digest = request.request_digest
            response = executor.complete(request)
            comparison = baseline_output if planned.family in _BASELINE_DEPENDENT else None
            scoring = score(planned, response, refusal_phrases=spec.refusal_phrases, baseline_output=comparison)
            routing = route(planned, scoring, format_sent=True)
        observation = build_observation(
            run_id=run_id,
            pilot_id=spec.pilot_id,
            plan_id=plan.plan_id,
            planned_variant_id=planned.variant_id,
            spec_bindings=spec.source_bindings,
            model=model,
            variant=variant,
            request_digest=request_digest,
            response=response,
            scoring=scoring,
            routing=routing,
            baseline_observation_id=None if baseline is None or planned.family not in _BASELINE_DEPENDENT else baseline.observation_id,
            created_on=created_on,
        )
        paths.append(publish_record(observation, output_dir))
        observations.append(observation)
        if planned.family is Family.BASELINE:
            baseline_by_case[planned.base_case_id] = observation

    family_counter = Counter(observation.variant.family.value for observation in observations)
    response_counter = Counter(observation.scoring.response_verdict for observation in observations)
    field_counter: Counter[str] = Counter()
    locus_counter: Counter[str] = Counter()
    for observation in observations:
        field_counter.update(verdict.verdict for verdict in observation.scoring.field_verdicts)
        locus_counter.update(observation.routing.loci)
    candidate_live = any("CANDIDATE" in observation.routing.loci for observation in observations)
    format_flags = [observation.routing.format_enforced_by_server for observation in observations]
    run_record = build_run_record(
        pilot_id=spec.pilot_id,
        plan_id=plan.plan_id,
        model=model,
        endpoint=spec.endpoint,
        executor_kind=executor_kind,
        spec_bindings=spec.source_bindings,
        created_on=created_on,
        selected_families=selected_families,
        variant_limit=limit,
        observation_ids=tuple(observation.observation_id for observation in observations),
        family_counts=tuple((family.value, family_counter.get(family.value, 0)) for family in Family if family.value in family_counter),
        response_verdict_counts=tuple((verdict, response_counter[verdict]) for verdict in RESPONSE_VERDICTS if verdict in response_counter),
        field_verdict_counts=tuple((verdict, field_counter[verdict]) for verdict in FIELD_VERDICTS if verdict in field_counter),
        live_locus_counts=tuple((locus, locus_counter[locus]) for locus in ("CANDIDATE", "AUXILIARY", "TEST", "SCOPE") if locus in locus_counter),
        observations_with_live_loci=sum(1 for observation in observations if observation.routing.live_loci),
        model_call_count=sum(1 for observation in observations if observation.response is not None),
        transport_error_count=response_counter.get("TRANSPORT_ERROR", 0),
        scope_label=SCOPE_REFUTED if candidate_live else SCOPE_UNREFUTED,
        format_enforced_by_server=False if any(flag is False for flag in format_flags) else None,
    )
    if run_record.run_id != run_id:
        raise RecordError("run header changed during execution")
    run_path = publish_record(run_record, output_dir)
    return RunResult(run_record=run_record, run_path=run_path, observations=tuple(observations), observation_paths=tuple(paths))
