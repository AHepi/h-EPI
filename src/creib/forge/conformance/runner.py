"""Execute a plan for one model and publish observation and run records.

The runner orders baseline variants first, materialises ROUND_TRIP variants
from the model's own baseline output, materialises each CYCLE variant from the
observation of the step it follows, compares NEGATION and IMPORT_DEPENDENCY
outputs with the baseline, and never calls a model for NON_VACUITY controls.
It tallies verdicts and loci for human reading.  It does not compute a
score, rank a model, or declare a run passed: the run status is always
``UNRESOLVED`` and a non-empty live-locus set means unresolved criticism.
"""

from __future__ import annotations

from collections import Counter
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from creib.errors import RecordError

from .common import RUN_ORDERS, RUN_SCHEMA_VERSION, SCOPE_INCONCLUSIVE, SCOPE_REFUTED, SCOPE_UNREFUTED, canonical_text, rfc3339
from .corpus import Corpus
from .executor import ChatRequest, ChatResponse, ModelExecutor, executor_failure_response
from .families import ExpectationKind, Family, Plan, Variant, materialize_cycle, materialize_round_trip
from .oracle import GROUNDING_VERDICTS, RESPONSE_VERDICTS, FIELD_VERDICTS, external_criticisms, prerequisite_unavailable, score
from .prompt import build_chat_request
from .records import EXECUTOR_KINDS, ObservationRecord, RunRecord, build_observation, build_run_record, compute_run_id, publish_record
from .routing import route
from .spec import TaskSpec


_BASELINE_DEPENDENT = frozenset({Family.NEGATION, Family.IMPORT_DEPENDENCY, Family.ROUND_TRIP, Family.REPEAT, Family.CYCLE, Family.UNIT_DEPENDENCE})


@dataclass(frozen=True)
class RunResult:
    run_record: RunRecord
    run_path: Path
    observations: tuple[ObservationRecord, ...]
    observation_paths: tuple[Path, ...]

    @property
    def unresolved(self) -> bool:
        return any(observation.routing.live_loci for observation in self.observations)


ORDERS: tuple[str, ...] = RUN_ORDERS


def select_variants(plan: Plan, *, families: Iterable[Family] | None = None, limit: int | None = None, order: str = "family", seed: int | None = None) -> tuple[Variant, ...]:
    """Choose variants; baselines needed by comparison families are always added.

    ``order`` is the sending order. ``family`` sends every baseline first and then the other
    families in plan order, so a drift in the endpoint during the run lands on whole families.
    ``interleaved`` sends each case's baseline followed at once by that case's other variants,
    so the requests a comparison pairs are close in time. ``shuffled`` is interleaved with the
    cases in an order drawn from ``seed``, so that a drift in the endpoint does not land on the
    cases in the order the corpus lists them; the seed is written to the run record. The records
    are the same in every order, and the run record lists its observations in the order they
    were made.
    """

    if order not in ORDERS:
        raise RecordError(f"order must be one of {list(ORDERS)}")
    if (order == "shuffled") != (seed is not None):
        raise RecordError("a seed is given exactly when the order is shuffled")
    if seed is not None and (type(seed) is not int or seed < 0):
        raise RecordError("seed must be a non-negative integer")
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
    if order in ("interleaved", "shuffled"):
        cases: list[str] = []
        for variant in ordered:
            if variant.base_case_id not in cases:
                cases.append(variant.base_case_id)
        if order == "shuffled":
            random.Random(seed).shuffle(cases)
        by_case = {case_id: [variant for variant in ordered if variant.base_case_id == case_id] for case_id in cases}
        ordered = [variant for case_id in cases for variant in by_case[case_id]]
    return tuple(ordered)


def _complete(executor: ModelExecutor, request: ChatRequest) -> ChatResponse:
    """One model call; an executor that raises becomes a recorded transport error."""

    try:
        return executor.complete(request)
    except RecordError:
        # Configuration failures (for example a missing API key) are the
        # operator's to fix before any call is made; they abort deliberately.
        raise
    except Exception as exc:  # noqa: BLE001 - recorded, not swallowed
        return executor_failure_response(exc)


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
    order: str = "family",
    seed: int | None = None,
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
    variants = select_variants(plan, families=families, limit=limit, order=order, seed=seed)
    header = {
        "schema_version": RUN_SCHEMA_VERSION,
        "pilot_id": spec.pilot_id,
        "plan_id": plan.plan_id,
        "model": model,
        "endpoint": spec.endpoint.to_dict(),
        "executor_kind": executor_kind,
        "spec_bindings": spec.bindings_dict(),
        "created_on": created_on,
        "selected_families": list(selected_families),
        "variant_limit": limit,
        "order": order,
        "shuffle_seed": seed,
    }
    run_id = compute_run_id(header)

    observations: list[ObservationRecord] = []
    paths: list[Path] = []
    baseline_by_case: dict[str, ObservationRecord] = {}
    # CYCLE: the observation each cycle follows, by (case, criticism source, cycle index).
    cycle_by_step: dict[tuple[str, str, int], ObservationRecord] = {}
    for planned in variants:
        baseline = baseline_by_case.get(planned.base_case_id)
        baseline_output = None if baseline is None else baseline.scoring.parsed_output
        # The observation this one is compared with and chained to: the baseline, or for a cycle
        # the step it follows.
        previous = baseline
        variant = planned
        request_digest: str | None = None
        response = None
        if not planned.model_call:
            scoring = score(planned, None)
            routing = route(planned, scoring, format_sent=False)
        elif planned.family is Family.CYCLE:
            index = planned.cycle_index or 0
            source = planned.cycle_criticism or "none"
            previous = baseline if index == 1 else cycle_by_step.get((planned.base_case_id, source, index - 1))
            previous_output = None if previous is None else previous.scoring.parsed_output
            if previous is None or previous_output is None:
                detail = (
                    "previous step missing" if previous is None
                    else f"previous step response verdict {previous.scoring.response_verdict}"
                )
                scoring = prerequisite_unavailable(detail)
                routing = route(planned, scoring, format_sent=True)
            else:
                criticisms = external_criticisms(previous.scoring, previous.variant) if source == "external" else ()
                variant = materialize_cycle(planned, canonical_text(previous_output), criticisms)
                request = build_chat_request(variant, model=model, endpoint=spec.endpoint)
                try:
                    response = _complete(executor, request)
                except RecordError as exc:
                    if executor_kind != "replay":
                        raise
                    # A re-score reads a cycle chain as far as the recorded replies go. A cycle's request
                    # carries the previous step's output; when the re-score reads that output differently
                    # from the recorded run, the request the step now makes was never sent and has no
                    # recorded reply. The step, and every step after it, is PREREQUISITE_UNAVAILABLE, and
                    # the record says why (H40). Outside a replay a missing reply still aborts the run.
                    variant = planned
                    response = None
                    scoring = prerequisite_unavailable(f"no recorded reply for the request this step makes under the re-score; the previous step's re-scored output is not the output the recorded run showed the model: {exc}")
                    routing = route(planned, scoring, format_sent=True)
                else:
                    request_digest = request.request_digest
                    scoring = score(variant, response, refusal_phrases=spec.refusal_phrases, baseline_output=previous_output)
                    routing = route(variant, scoring, format_sent=True)
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
                    try:
                        response = _complete(executor, request)
                    except RecordError as exc:
                        if executor_kind != "replay":
                            raise
                        # The same reading as a cycle step's: the request carries the baseline's output, and
                        # when the re-score reads that output differently from the recorded run, the request
                        # was never sent and has no recorded reply. Outside a replay a missing reply still aborts.
                        variant = planned
                        response = None
                        scoring = prerequisite_unavailable(f"no recorded reply for the request this variant makes under the re-score; the baseline's re-scored output is not the output the recorded run rendered: {exc}")
                        routing = route(planned, scoring, format_sent=True)
                    else:
                        request_digest = request.request_digest
                        scoring = score(variant, response, refusal_phrases=spec.refusal_phrases, baseline_output=baseline_output)
                        routing = route(variant, scoring, format_sent=True)
        else:
            request = build_chat_request(planned, model=model, endpoint=spec.endpoint)
            request_digest = request.request_digest
            response = _complete(executor, request)
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
            baseline_observation_id=None if previous is None or planned.family not in _BASELINE_DEPENDENT else previous.observation_id,
            created_on=created_on,
            replayed_from=getattr(executor, "last_source_id", None) if executor_kind == "replay" and response is not None else None,
        )
        paths.append(publish_record(observation, output_dir))
        observations.append(observation)
        if planned.family is Family.BASELINE:
            baseline_by_case[planned.base_case_id] = observation
        if planned.family is Family.CYCLE and planned.cycle_index is not None:
            cycle_by_step[(planned.base_case_id, planned.cycle_criticism or "none", planned.cycle_index)] = observation

    family_counter = Counter(observation.variant.family.value for observation in observations)
    response_counter = Counter(observation.scoring.response_verdict for observation in observations)
    field_counter: Counter[str] = Counter()
    locus_counter: Counter[str] = Counter()
    grounding_counter: Counter[str] = Counter()
    for observation in observations:
        field_counter.update(verdict.verdict for verdict in observation.scoring.field_verdicts)
        locus_counter.update(observation.routing.loci)
        grounding_counter.update(verdict.verdict for verdict in observation.scoring.grounding_verdicts)
    candidate_live = any("CANDIDATE" in observation.routing.loci for observation in observations)
    scored_model_outputs = sum(
        1 for observation in observations
        if observation.response is not None and observation.scoring.response_verdict == "JSON_OBJECT"
    )
    # RP-1: "unrefuted" is claimable only when at least one model output was
    # actually scored and no model call went unobserved. A run made of
    # transport errors has refuted nothing and confirmed nothing.
    if candidate_live:
        scope_label = SCOPE_REFUTED
    elif (
        scored_model_outputs > 0
        and response_counter.get("TRANSPORT_ERROR", 0) == 0
        and all(o.routing.unrefuted_for_variant for o in observations if o.response is not None)
    ):
        scope_label = SCOPE_UNREFUTED
    else:
        scope_label = SCOPE_INCONCLUSIVE
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
        order=order,
        shuffle_seed=seed,
        observation_ids=tuple(observation.observation_id for observation in observations),
        family_counts=tuple((family.value, family_counter.get(family.value, 0)) for family in Family if family.value in family_counter),
        response_verdict_counts=tuple((verdict, response_counter[verdict]) for verdict in RESPONSE_VERDICTS if verdict in response_counter),
        field_verdict_counts=tuple((verdict, field_counter[verdict]) for verdict in FIELD_VERDICTS if verdict in field_counter),
        live_locus_counts=tuple((locus, locus_counter[locus]) for locus in ("CANDIDATE", "AUXILIARY", "TEST", "SCOPE") if locus in locus_counter),
        grounding_verdict_counts=tuple((verdict, grounding_counter[verdict]) for verdict in GROUNDING_VERDICTS if verdict in grounding_counter),
        observations_with_live_loci=sum(1 for observation in observations if observation.routing.live_loci),
        model_call_count=sum(1 for observation in observations if observation.response is not None),
        transport_error_count=response_counter.get("TRANSPORT_ERROR", 0),
        scope_label=scope_label,
        format_enforced_by_server=False if any(flag is False for flag in format_flags) else None,
    )
    if run_record.run_id != run_id:
        raise RecordError("run header changed during execution")
    run_path = publish_record(run_record, output_dir)
    return RunResult(run_record=run_record, run_path=run_path, observations=tuple(observations), observation_paths=tuple(paths))
