"""Conjectures about language-model form filling, tested against records.

A claim is a universal statement over the observations in a declared scope.
A ``never`` claim is refuted by one observation where its condition holds; an
``always`` claim by one where it does not. A claim that no supplied record
refutes is ``UNREFUTED_FOR_DECLARED_SCOPE``. That is not a proof and not a
confirmation: the scope is exactly the records supplied, and the next record
may refute it. Nothing here counts survivals as evidence for anything.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from creib.canonical import canonical_bytes
from creib.errors import RecordError
from creib.strict_json import loads_strict

from .common import (
    LOCUS_VALUES,
    NON_INDUCTIVE_LIMIT,
    array_value,
    boolean,
    decode_utf8,
    identifier,
    object_value,
    optional_boolean,
    optional_text,
    text,
    validate_instance,
)
from .families import Family
from .spec import CYCLE_CRITICISMS, THINK_LEVELS
from .units import UNIT_RELATIONS
from .oracle import FIELD_VERDICTS, GROUNDING_VERDICTS, RESPONSE_VERDICTS
from .appraisal import Appraisal
from .records import ObservationRecord, RunRecord
from .routing import TRIGGERS

CLAIMS_SCHEMA_NAME = "conformance-claims.schema.json"
CLAIMS_SCHEMA_VERSION = "creib.conformance-pilot.claims.v1"
CLAIM_KINDS: tuple[str, ...] = ("never", "always")
CLAIM_STATUSES: tuple[str, ...] = ("REFUTED", "REFUTED_ON_CONTESTED_READING", "UNREFUTED_FOR_DECLARED_SCOPE", "NOT_TESTED")
_MAX_EXAMPLES = 5


@dataclass(frozen=True)
class Scope:
    families: tuple[str, ...] | None
    cases: tuple[str, ...] | None
    models: tuple[str, ...] | None
    model_call: bool | None

    def admits(self, observation: ObservationRecord) -> bool:
        variant = observation.variant
        if self.families is not None and variant.family.value not in self.families:
            return False
        if self.cases is not None and variant.base_case_id not in self.cases:
            return False
        if self.models is not None and observation.model not in self.models:
            return False
        if self.model_call is not None and variant.model_call is not self.model_call:
            return False
        return True

    def to_dict(self) -> dict[str, object]:
        return {
            "families": None if self.families is None else list(self.families),
            "cases": None if self.cases is None else list(self.cases),
            "models": None if self.models is None else list(self.models),
            "model_call": self.model_call,
        }


@dataclass(frozen=True)
class Claim:
    claim_id: str
    statement: str
    kind: str
    scope: Scope
    condition: Mapping[str, Any]
    note: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_id": self.claim_id,
            "statement": self.statement,
            "kind": self.kind,
            "scope": self.scope.to_dict(),
            "condition": _plain(self.condition),
            "note": self.note,
        }


def _grounding_set(raw: Any, where: str) -> frozenset[str]:
    items = [raw] if isinstance(raw, str) else list(array_value(raw, where))
    if not items:
        raise RecordError(f"{where} must name at least one grounding verdict")
    verdicts = []
    for index, item in enumerate(items):
        verdict = text(item, f"{where}[{index}]")
        if verdict not in GROUNDING_VERDICTS:
            raise RecordError(f"{where}[{index}] {verdict!r} is not a known grounding verdict")
        verdicts.append(verdict)
    return frozenset(verdicts)


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    return value


# --------------------------------------------------------------------------
# conditions
# --------------------------------------------------------------------------

class Context:
    """The other records a predicate may refer to: the baseline of the same run and case, the step an observation follows, and the run it belongs to."""

    def __init__(self, observations: list[ObservationRecord], runs: Iterable[RunRecord] = ()) -> None:
        self._baselines: dict[tuple[str, str], ObservationRecord] = {}
        self._by_id: dict[str, ObservationRecord] = {}
        self._runs: dict[str, RunRecord] = {run.run_id: run for run in runs}
        for observation in observations:
            self._by_id[observation.observation_id] = observation
            if observation.variant.family is Family.BASELINE:
                self._baselines[(observation.run_id, observation.variant.base_case_id)] = observation

    def run_of(self, observation: ObservationRecord) -> RunRecord | None:
        """The run record an observation belongs to, when the run records were supplied."""

        return self._runs.get(observation.run_id)

    def baseline_of(self, observation: ObservationRecord) -> ObservationRecord | None:
        return self._baselines.get((observation.run_id, observation.variant.base_case_id))

    def previous_of(self, observation: ObservationRecord) -> ObservationRecord | None:
        """The observation this one was compared with: the record it names, else the baseline of its run and case."""

        if observation.baseline_observation_id is not None:
            named = self._by_id.get(observation.baseline_observation_id)
            if named is not None:
                return named
        return self.baseline_of(observation)


Predicate = Callable[[ObservationRecord, Context], bool]


def _output(observation: ObservationRecord) -> Mapping[str, Any]:
    return observation.scoring.parsed_output or {}


_MISS_VERDICTS: tuple[str, ...] = tuple(v for v in FIELD_VERDICTS if v not in ("MATCH", "NOT_SCORED"))


def _verdict_set(raw: Any, where: str) -> frozenset[str]:
    """A field verdict, a list of them, or the shorthand ``miss`` for every criticising verdict."""

    if raw == "miss":
        return frozenset(_MISS_VERDICTS)
    items = [raw] if isinstance(raw, str) else list(array_value(raw, where))
    if not items:
        raise RecordError(f"{where} must name at least one verdict")
    verdicts = []
    for index, item in enumerate(items):
        verdict = text(item, f"{where}[{index}]")
        if verdict not in FIELD_VERDICTS:
            raise RecordError(f"{where}[{index}] {verdict!r} is not a known field verdict")
        verdicts.append(verdict)
    return frozenset(verdicts)


def _field_verdicts_by_name(observation: ObservationRecord) -> dict[str, str]:
    return {item.field: item.verdict for item in observation.scoring.field_verdicts}


def _value_changed(field: str, observation: ObservationRecord, previous: ObservationRecord) -> bool:
    """Whether a key's value or presence differs between an observation and the step it follows.

    A field's companion span key, where grounding is active, counts as part of the field: a
    criticism of a span is repaired by changing the span.
    """

    keys = [field]
    variant = observation.variant
    if variant.grounding is not None and variant.grounding.active and field in variant.active_span_fields:
        keys.append(variant.span_key(field))
    now = _output(observation)
    before = _output(previous)
    return any((key in now) != (key in before) or now.get(key) != before.get(key) for key in keys)


def compile_condition(raw: Any, where: str = "condition") -> Predicate:
    """Turn one condition object into a predicate; fail closed on anything unknown."""

    record = object_value(raw, where)
    if len(record) != 1:
        raise RecordError(f"{where} must have exactly one key, got {sorted(record)}")
    (key, value), = record.items()
    if key == "all_of":
        parts = [compile_condition(item, f"{where}.all_of[{i}]") for i, item in enumerate(array_value(value, f"{where}.all_of"))]
        if not parts:
            raise RecordError(f"{where}.all_of must not be empty")
        return lambda o, c: all(p(o, c) for p in parts)
    if key == "any_of":
        parts = [compile_condition(item, f"{where}.any_of[{i}]") for i, item in enumerate(array_value(value, f"{where}.any_of"))]
        if not parts:
            raise RecordError(f"{where}.any_of must not be empty")
        return lambda o, c: any(p(o, c) for p in parts)
    if key == "not":
        inner = compile_condition(value, f"{where}.not")
        return lambda o, c: not inner(o, c)
    if key == "baseline":
        # The nested condition is evaluated on the baseline observation of the same run and case;
        # false when no baseline was supplied, so a claim about "where the baseline matched" is
        # not refuted by an observation whose baseline is missing.
        inner = compile_condition(value, f"{where}.baseline")

        def on_baseline(o: ObservationRecord, c: Context) -> bool:
            base = c.baseline_of(o)
            return base is not None and inner(base, c)

        return on_baseline
    if key == "previous":
        # The nested condition is evaluated on the step this observation follows (for a cycle, the
        # previous cycle or the baseline; for any other comparison family, the baseline); false
        # when that record was not supplied.
        inner = compile_condition(value, f"{where}.previous")

        def on_previous(o: ObservationRecord, c: Context) -> bool:
            before = c.previous_of(o)
            return before is not None and inner(before, c)

        return on_previous
    if key == "cycle":
        spec = object_value(value, f"{where}.cycle")
        index = spec.get("index")
        if index is not None and (type(index) is not int or index < 1):
            raise RecordError(f"{where}.cycle.index must be a positive integer or null")
        criticism = optional_text(spec.get("criticism"), f"{where}.cycle.criticism")
        if criticism is not None and criticism not in CYCLE_CRITICISMS:
            raise RecordError(f"{where}.cycle.criticism {criticism!r} is not a known criticism source")
        criticised = optional_boolean(spec.get("criticised"), f"{where}.cycle.criticised")

        def is_cycle(o: ObservationRecord, c: Context) -> bool:
            v = o.variant
            if v.family is not Family.CYCLE or v.cycle_index is None:
                return False
            if index is not None and v.cycle_index != index:
                return False
            if criticism is not None and v.cycle_criticism != criticism:
                return False
            if criticised is not None and bool(v.criticised_fields) is not criticised:
                return False
            return True

        return is_cycle
    if key == "verdict_move":
        spec = object_value(value, f"{where}.verdict_move")
        field = optional_text(spec.get("field"), f"{where}.verdict_move.field")
        source = _verdict_set(spec["from"], f"{where}.verdict_move.from")
        target = _verdict_set(spec["to"], f"{where}.verdict_move.to")
        criticised = optional_boolean(spec.get("criticised"), f"{where}.verdict_move.criticised")

        def verdict_move(o: ObservationRecord, c: Context) -> bool:
            before = c.previous_of(o)
            if before is None or before.scoring.parsed_output is None or o.scoring.parsed_output is None:
                return False
            earlier = _field_verdicts_by_name(before)
            later = _field_verdicts_by_name(o)
            named = set(o.variant.criticised_fields)
            for name in sorted(set(earlier) | set(later)):
                if field is not None and name != field:
                    continue
                if criticised is not None and (name in named) is not criticised:
                    continue
                if earlier.get(name, "NOT_SCORED") in source and later.get(name, "NOT_SCORED") in target:
                    return True
            return False

        return verdict_move
    if key == "criticised_field":
        spec = object_value(value, f"{where}.criticised_field")
        changed = optional_boolean(spec.get("changed"), f"{where}.criticised_field.changed")
        verdicts = None if spec.get("verdict") is None else _verdict_set(spec["verdict"], f"{where}.criticised_field.verdict")
        grounding = None if spec.get("grounding_verdict") is None else _grounding_set(spec["grounding_verdict"], f"{where}.criticised_field.grounding_verdict")
        if changed is None and verdicts is None and grounding is None:
            raise RecordError(f"{where}.criticised_field needs changed, verdict, or grounding_verdict")

        def criticised_field(o: ObservationRecord, c: Context) -> bool:
            names = o.variant.criticised_fields
            if not names or o.scoring.parsed_output is None:
                return False
            before = c.previous_of(o)
            later = _field_verdicts_by_name(o)
            grounded = {item.field: item.verdict for item in o.scoring.grounding_verdicts}
            for name in names:
                if changed is not None:
                    if before is None or before.scoring.parsed_output is None:
                        continue
                    if _value_changed(name, o, before) is not changed:
                        continue
                if verdicts is not None and later.get(name, "NOT_SCORED") not in verdicts:
                    continue
                if grounding is not None and grounded.get(name) not in grounding:
                    continue
                return True
            return False

        return criticised_field
    if key == "endpoint":
        # A setting of the run the observation belongs to, read from its run record: the reasoning
        # setting actually sent (a run-time override is recorded there, not in the pilot) or the
        # call timeout. False when the run record was not supplied.
        spec = object_value(value, f"{where}.endpoint")
        if not spec:
            raise RecordError(f"{where}.endpoint needs think or timeout_seconds")
        want_think = spec.get("think", "unset")
        if want_think != "unset" and want_think is not None and type(want_think) is not bool and want_think not in THINK_LEVELS:
            raise RecordError(f"{where}.endpoint.think must be null, a boolean, or one of {list(THINK_LEVELS)}")
        want_timeout = spec.get("timeout_seconds")
        if want_timeout is not None and (type(want_timeout) is not int or want_timeout < 1):
            raise RecordError(f"{where}.endpoint.timeout_seconds must be a positive integer")

        def endpoint(o: ObservationRecord, c: Context) -> bool:
            run = c.run_of(o)
            if run is None:
                return False
            if want_think != "unset" and run.endpoint.think != want_think:
                return False
            if want_timeout is not None and run.endpoint.timeout_seconds != want_timeout:
                return False
            return True

        return endpoint
    if key == "internal_count":
        # A relation inside one reply, never a comparison with the key: the integer in ``field``
        # equals the number of ``of`` fields whose value is ``value``. False, not a counterexample
        # by default, when any named field is absent or the count is not an integer; a claim that
        # wants those cases counted says so with key_present and field_verdict guards of its own.
        spec = object_value(value, f"{where}.internal_count")
        field = text(spec["field"], f"{where}.internal_count.field")
        of = tuple(text(item, f"{where}.internal_count.of[{i}]") for i, item in enumerate(array_value(spec["of"], f"{where}.internal_count.of")))
        if not of:
            raise RecordError(f"{where}.internal_count.of must name at least one field")
        if field in of or len(set(of)) != len(of):
            raise RecordError(f"{where}.internal_count.of must not repeat a field or name the count field")
        counted = spec["value"]
        if type(counted) not in (str, int, bool) or counted is None:
            raise RecordError(f"{where}.internal_count.value must be a string, integer, or boolean")

        def internal_count(o: ObservationRecord, c: Context) -> bool:
            output = _output(o)
            if field not in output or any(name not in output for name in of):
                return False
            count = output[field]
            if type(count) is not int:
                return False
            return count == sum(1 for name in of if type(output[name]) is type(counted) and output[name] == counted)

        return internal_count
    if key == "unit":
        # UNIT_DEPENDENCE only: which unit of the document was removed, by id or by its relation
        # to the claim (self, declared, other) as the plan computed it from the document.
        spec = object_value(value, f"{where}.unit")
        relations = None
        if spec.get("relation") is not None:
            relations = frozenset(text(item, f"{where}.unit.relation[{i}]") for i, item in enumerate(array_value(spec["relation"], f"{where}.unit.relation")))
            unknown = sorted(relations - set(UNIT_RELATIONS))
            if unknown:
                raise RecordError(f"{where}.unit.relation names unknown relations {unknown}; known: {list(UNIT_RELATIONS)}")
        removed = None
        if spec.get("removed") is not None:
            removed = frozenset(text(item, f"{where}.unit.removed[{i}]") for i, item in enumerate(array_value(spec["removed"], f"{where}.unit.removed")))
        if relations is None and removed is None:
            raise RecordError(f"{where}.unit must name a relation or a removed unit")

        def unit(o: ObservationRecord, c: Context) -> bool:
            variant = o.variant
            if variant.removed_unit_id is None:
                return False
            if relations is not None and variant.removed_unit_relation not in relations:
                return False
            if removed is not None and variant.removed_unit_id not in removed:
                return False
            return True

        return unit
    if key == "field_value":
        # The value the model returned for a field is one of the listed values, compared as
        # canonical JSON so that lists and objects can be named as well as scalars. False, not a
        # counterexample by default, when the field is absent or the reply did not parse.
        spec = object_value(value, f"{where}.field_value")
        field = text(spec["field"], f"{where}.field_value.field")
        listed = array_value(spec["values"], f"{where}.field_value.values")
        if not listed:
            raise RecordError(f"{where}.field_value.values must list at least one value")
        wanted = frozenset(canonical_bytes(_plain(item)) for item in listed)

        def field_value(o: ObservationRecord, c: Context) -> bool:
            output = _output(o)
            return field in output and canonical_bytes(_plain(output[field])) in wanted

        return field_value
    if key == "value_changed":
        # The field's value or presence differs from the observation this one is compared with
        # (the baseline, or for a cycle the step it follows). False, not a counterexample by
        # default, when either reply did not parse or there is nothing to compare with.
        field = text(object_value(value, f"{where}.value_changed")["field"], f"{where}.value_changed.field")

        def value_changed(o: ObservationRecord, c: Context) -> bool:
            previous = c.previous_of(o)
            if previous is None or o.scoring.parsed_output is None or previous.scoring.parsed_output is None:
                return False
            return _value_changed(field, o, previous)

        return value_changed
    if key == "trigger":
        trigger = text(value, f"{where}.trigger")
        if trigger not in TRIGGERS:
            raise RecordError(f"{where}.trigger {trigger!r} is not a known trigger")
        return lambda o, c: trigger in o.routing.triggers
    if key == "locus":
        locus = text(value, f"{where}.locus")
        if locus not in LOCUS_VALUES:
            raise RecordError(f"{where}.locus {locus!r} is not a known locus")
        return lambda o, c: locus in o.routing.loci
    if key == "response_verdict":
        verdict = text(value, f"{where}.response_verdict")
        if verdict not in RESPONSE_VERDICTS:
            raise RecordError(f"{where}.response_verdict {verdict!r} is not a known response verdict")
        return lambda o, c: o.scoring.response_verdict == verdict
    if key == "field_verdict":
        spec = object_value(value, f"{where}.field_verdict")
        verdict = text(spec["verdict"], f"{where}.field_verdict.verdict")
        if verdict not in FIELD_VERDICTS:
            raise RecordError(f"{where}.field_verdict.verdict {verdict!r} is not a known field verdict")
        field = optional_text(spec.get("field"), f"{where}.field_verdict.field")
        value_null = optional_boolean(spec.get("value_null"), f"{where}.field_verdict.value_null")

        def field_verdict(o: ObservationRecord, c: Context) -> bool:
            output = _output(o)
            for item in o.scoring.field_verdicts:
                if item.verdict != verdict or (field is not None and item.field != field):
                    continue
                if value_null is not None and ((item.field in output and output[item.field] is None) is not value_null):
                    continue
                return True
            return False

        return field_verdict
    if key == "grounding_verdict":
        spec = object_value(value, f"{where}.grounding_verdict")
        verdict = text(spec["verdict"], f"{where}.grounding_verdict.verdict")
        if verdict not in GROUNDING_VERDICTS:
            raise RecordError(f"{where}.grounding_verdict.verdict {verdict!r} is not a known grounding verdict")
        field = optional_text(spec.get("field"), f"{where}.grounding_verdict.field")
        relaxed = optional_boolean(spec.get("relaxed"), f"{where}.grounding_verdict.relaxed")

        def grounding(o: ObservationRecord, c: Context) -> bool:
            for item in o.scoring.grounding_verdicts:
                if item.verdict != verdict or (field is not None and item.field != field):
                    continue
                if relaxed is not None and (bool(item.detail and "relaxation" in item.detail) is not relaxed):
                    continue
                return True
            return False

        return grounding
    if key == "changed_vs_baseline":
        expected = optional_boolean(value, f"{where}.changed_vs_baseline")
        return lambda o, c: o.scoring.changed_vs_baseline is expected
    if key == "value_null":
        field = text(object_value(value, f"{where}.value_null")["field"], f"{where}.value_null.field")
        return lambda o, c: field in _output(o) and _output(o)[field] is None
    if key == "key_present":
        name = text(object_value(value, f"{where}.key_present")["key"], f"{where}.key_present.key")
        return lambda o, c: name in _output(o)
    if key == "thinking_present":
        expected_thinking = boolean(value, f"{where}.thinking_present")
        return lambda o, c: o.response is not None and o.response.thinking_present is expected_thinking
    if key == "output_tokens":
        spec = object_value(value, f"{where}.output_tokens")
        low = spec.get("min"); high = spec.get("max")
        if low is None and high is None:
            raise RecordError(f"{where}.output_tokens needs min or max")
        for bound, name in ((low, "min"), (high, "max")):
            if bound is not None and (type(bound) is not int or bound < 0):
                raise RecordError(f"{where}.output_tokens.{name} must be a non-negative integer")

        def output_tokens(o: ObservationRecord, c: Context) -> bool:
            if o.response is None or o.response.eval_count is None:
                return False
            n = o.response.eval_count
            return (low is None or n >= low) and (high is None or n <= high)

        return output_tokens
    if key == "recovered":
        how = text(value, f"{where}.recovered")
        if how not in ("any", "prose", "duplicate_keys"):
            raise RecordError(f"{where}.recovered must be any, prose, or duplicate_keys")

        def recovered(o: ObservationRecord, c: Context) -> bool:
            if not o.scoring.recovered_from_prose:
                return False
            duplicates = bool(o.scoring.response_detail and "duplicate keys" in o.scoring.response_detail)
            return how == "any" or (how == "duplicate_keys") is duplicates

        return recovered
    raise RecordError(f"{where} has unknown predicate {key!r}")


def condition_footprint(raw: Any) -> tuple[frozenset[str] | None, frozenset[str] | None]:
    """The fields and triggers a condition looks at: (fields, triggers), each None for "any".

    Predicates that look at no field verdict and no trigger (a token count, the thinking
    channel, recovery, the change flag) contribute nothing, so a refutation through them
    rests on no reading and is usable whatever the appraisal says.
    """

    fields: set[str] = set(); triggers: set[str] = set(); any_field = False
    def walk(node: Any) -> None:
        nonlocal any_field
        record = object_value(node, "condition")
        (key, value), = record.items()
        if key in ("all_of", "any_of"):
            for item in value:
                walk(item)
        elif key in ("not", "baseline", "previous"):
            walk(value)
        elif key == "verdict_move":
            field = object_value(value, "verdict_move").get("field")
            if field is None:
                any_field = True
            else:
                fields.add(str(field))
        elif key == "criticised_field":
            any_field = True
        elif key == "internal_count":
            spec = object_value(value, "internal_count")
            fields.add(str(spec["field"]))
            fields.update(str(item) for item in spec["of"])
        elif key == "trigger":
            triggers.add(str(value))
        elif key == "field_verdict":
            field = object_value(value, "field_verdict").get("field")
            if field is None:
                any_field = True
            else:
                fields.add(str(field))
        elif key == "grounding_verdict":
            verdict = str(object_value(value, "grounding_verdict")["verdict"])
            if verdict in TRIGGERS:
                triggers.add(verdict)
        elif key == "value_null":
            fields.add(str(object_value(value, "value_null")["field"]))
        elif key in ("field_value", "value_changed"):
            fields.add(str(object_value(value, key)["field"]))
    walk(raw)
    return (None if any_field else frozenset(fields)), frozenset(triggers)


# --------------------------------------------------------------------------
# loading
# --------------------------------------------------------------------------


def _scope_from_dict(raw: Any, where: str) -> Scope:
    if raw is None:
        return Scope(families=None, cases=None, models=None, model_call=None)
    record = object_value(raw, where)
    families = None
    if record.get("families") is not None:
        families = tuple(text(item, f"{where}.families[{i}]") for i, item in enumerate(array_value(record["families"], f"{where}.families")))
        for item in families:
            try:
                Family(item)
            except ValueError as exc:
                raise RecordError(f"{where}.families names unknown family {item!r}") from exc
    cases = None if record.get("cases") is None else tuple(identifier(item, f"{where}.cases[{i}]") for i, item in enumerate(array_value(record["cases"], f"{where}.cases")))
    models = None if record.get("models") is None else tuple(text(item, f"{where}.models[{i}]") for i, item in enumerate(array_value(record["models"], f"{where}.models")))
    return Scope(families=families, cases=cases, models=models, model_call=optional_boolean(record.get("model_call"), f"{where}.model_call"))


def claims_from_dict(raw: Any) -> tuple[Claim, ...]:
    validate_instance(raw, CLAIMS_SCHEMA_NAME)
    record = object_value(raw, "claims file")
    if record.get("schema_version") != CLAIMS_SCHEMA_VERSION:
        raise RecordError("claims schema_version mismatch")
    claims: list[Claim] = []
    seen: set[str] = set()
    for index, item in enumerate(array_value(record["claims"], "claims")):
        where = f"claims[{index}]"
        entry = object_value(item, where)
        claim_id = identifier(entry["claim_id"], f"{where}.claim_id")
        if claim_id in seen:
            raise RecordError(f"{where}.claim_id {claim_id!r} repeats")
        seen.add(claim_id)
        kind = text(entry["kind"], f"{where}.kind")
        if kind not in CLAIM_KINDS:
            raise RecordError(f"{where}.kind must be one of {list(CLAIM_KINDS)}")
        condition = object_value(entry["condition"], f"{where}.condition")
        compile_condition(condition, f"{where}.condition")
        claims.append(
            Claim(
                claim_id=claim_id,
                statement=text(entry["statement"], f"{where}.statement"),
                kind=kind,
                scope=_scope_from_dict(entry.get("scope"), f"{where}.scope"),
                condition=condition,
                note=optional_text(entry.get("note"), f"{where}.note"),
            )
        )
    return tuple(claims)


def load_claims(path: Path) -> tuple[Claim, ...]:
    if not isinstance(path, Path):
        raise TypeError("path must be pathlib.Path")
    # Read the bytes here rather than through load_strict, which turns an OSError into a
    # RecordError of its own; a handler for OSError around it never ran (H27).
    try:
        raw_bytes = path.read_bytes()
    except OSError as exc:
        raise RecordError(f"cannot read claims {path}: {exc}") from exc
    raw = loads_strict(decode_utf8(raw_bytes, str(path)))
    return claims_from_dict(raw)


# --------------------------------------------------------------------------
# evaluation
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ClaimResult:
    claim: Claim
    status: str
    tested: int
    models_tested: tuple[str, ...]
    refuting: int
    refuting_models: tuple[str, ...]
    per_model: tuple[tuple[str, int, int], ...]
    examples: tuple[tuple[str, str, str, str], ...]
    # Standing of the refuting observations under the appraisal: usable (every reading they
    # rest on stands, or none is argued about), contested (a reading is undecided), defeated
    # (a reading is out). Without an appraisal every refutation is usable.
    refuting_usable: int = 0
    refuting_contested: int = 0
    refuting_defeated: int = 0
    readings: tuple[str, ...] = ()
    # Liveness of the check: how many supplied observations outside the declared scope
    # satisfy the refuting predicate. A survival whose predicate held nowhere, in or out of
    # scope, has not been shown to be a survival of anything the records could have said.
    witnesses_outside_scope: int = 0

    @property
    def shown_able_to_fail(self) -> bool:
        return self.refuting > 0 or self.witnesses_outside_scope > 0

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_id": self.claim.claim_id,
            "statement": self.claim.statement,
            "kind": self.claim.kind,
            "status": self.status,
            "tested": self.tested,
            "models_tested": list(self.models_tested),
            "refuting": self.refuting,
            "refuting_models": list(self.refuting_models),
            "refuting_usable": self.refuting_usable,
            "refuting_contested": self.refuting_contested,
            "refuting_defeated": self.refuting_defeated,
            "readings": list(self.readings),
            "witnesses_outside_scope": self.witnesses_outside_scope,
            "shown_able_to_fail": self.shown_able_to_fail,
            "per_model": [{"model": m, "tested": t, "refuting": r} for m, t, r in self.per_model],
            "examples": [{"observation_id": i, "model": m, "case_id": c, "family": f} for i, m, c, f in self.examples],
            "note": self.claim.note,
            "epistemic_limit": NON_INDUCTIVE_LIMIT,
        }


def evaluate_claim(claim: Claim, observations: list[ObservationRecord], context: Context | None = None, appraisal: Appraisal | None = None, runs: Iterable[RunRecord] = ()) -> ClaimResult:
    predicate = compile_condition(claim.condition)
    if context is None:
        context = Context(observations, runs)
    fields, triggers = condition_footprint(claim.condition)
    tested: dict[str, int] = {}
    refuting: dict[str, int] = {}
    standing = {"usable": 0, "contested": 0, "defeated": 0}
    readings: set[str] = set()
    examples: list[tuple[str, str, str, str]] = []
    witnesses = 0
    for observation in observations:
        holds = predicate(observation, context)
        refutes = holds if claim.kind == "never" else not holds
        if not claim.scope.admits(observation):
            if refutes:
                witnesses += 1
            continue
        tested[observation.model] = tested.get(observation.model, 0) + 1
        if refutes:
            refuting[observation.model] = refuting.get(observation.model, 0) + 1
            if appraisal is None:
                standing["usable"] += 1
            else:
                standing[appraisal.standing_of(observation, fields, triggers)] += 1
                readings.update(appraisal.readings_of(observation, fields, triggers))
            if len(examples) < _MAX_EXAMPLES:
                examples.append((observation.observation_id, observation.model, observation.variant.base_case_id, observation.variant.family.value))
    total = sum(tested.values())
    if total == 0:
        status = "NOT_TESTED"
    elif standing["usable"]:
        status = "REFUTED"
    elif standing["contested"]:
        status = "REFUTED_ON_CONTESTED_READING"
    else:
        # No refutation, or every refutation rests on a defeated reading; the raw count stays visible.
        status = "UNREFUTED_FOR_DECLARED_SCOPE"
    return ClaimResult(
        claim=claim,
        status=status,
        tested=total,
        models_tested=tuple(sorted(tested)),
        refuting=sum(refuting.values()),
        refuting_models=tuple(sorted(refuting)),
        per_model=tuple((model, tested[model], refuting.get(model, 0)) for model in sorted(tested)),
        examples=tuple(examples),
        refuting_usable=standing["usable"],
        refuting_contested=standing["contested"],
        refuting_defeated=standing["defeated"],
        readings=tuple(sorted(readings)),
        witnesses_outside_scope=witnesses,
    )


def evaluate_claims(claims: tuple[Claim, ...], observations: list[ObservationRecord], appraisal: Appraisal | None = None, runs: Iterable[RunRecord] = ()) -> tuple[ClaimResult, ...]:
    context = Context(observations, runs)
    return tuple(evaluate_claim(claim, observations, context, appraisal) for claim in claims)


def _plural(count: int, noun: str) -> str:
    return f"{count} {noun}" + ("" if count == 1 else "s")


def render_claims_markdown(results: tuple[ClaimResult, ...]) -> str:
    parts = ["# Conjectures tested against the records", ""]
    parts.append("A `never` claim is refuted by one observation where its condition holds; an `always` claim by one where it does not. `UNREFUTED_FOR_DECLARED_SCOPE` means no supplied record refuted the claim, or every refutation rests on a reading of the key that the appraisal labels out; it is not a proof. `REFUTED_ON_CONTESTED_READING` means every refutation rests on a reading that is under criticism and undecided. An unrefuted claim also says whether its refuting condition held on any supplied record outside the declared scope: a condition that never held anywhere has not been shown able to fail. Counts are of observations, not of quality, and imply no ranking.")
    parts.append("")
    for result in results:
        parts.append(f"## {result.claim.claim_id}: {result.status}")
        parts.append("")
        parts.append(f"*{result.claim.statement}* (`{result.claim.kind}`)")
        parts.append("")
        parts.append(f"- tested on {result.tested} observations from {_plural(len(result.models_tested), 'model')}")
        if result.refuting:
            parts.append(f"- refuting observations: {result.refuting} from {_plural(len(result.refuting_models), 'model')}: {', '.join(result.refuting_models)}")
            parts.append("- not refuted by: " + (", ".join(m for m in result.models_tested if m not in result.refuting_models) or "-"))
            if result.readings:
                parts.append(f"- standing under the appraisal: {result.refuting_usable} usable, {result.refuting_contested} on a contested reading, {result.refuting_defeated} on a defeated reading; readings involved: {', '.join(result.readings)}")
            parts.append("- examples: " + "; ".join(f"`{i[:16]}` ({m}, {c}, {f})" for i, m, c, f in result.examples))
        elif result.status != "NOT_TESTED":
            if result.shown_able_to_fail:
                parts.append(f"- the refuting condition held on {_plural(result.witnesses_outside_scope, 'supplied observation')} outside the declared scope, so the check has been shown able to fail")
            else:
                parts.append("- the refuting condition held on no supplied observation, in or out of scope; this check has not been shown able to fail, and the survival should be read accordingly")
        if result.claim.note:
            parts.append(f"- note: {result.claim.note}")
        parts.append("")
    parts.append(NON_INDUCTIVE_LIMIT)
    parts.append("")
    return "\n".join(parts)


__all__ = [
    "CLAIMS_SCHEMA_NAME",
    "CLAIMS_SCHEMA_VERSION",
    "CLAIM_KINDS",
    "CLAIM_STATUSES",
    "Claim",
    "ClaimResult",
    "Context",
    "Scope",
    "claims_from_dict",
    "compile_condition",
    "evaluate_claim",
    "evaluate_claims",
    "load_claims",
    "render_claims_markdown",
]
