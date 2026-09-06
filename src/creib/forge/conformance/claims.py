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
from typing import Any, Callable, Mapping

from creib.errors import RecordError
from creib.strict_json import load_strict

from .common import (
    LOCUS_VALUES,
    NON_INDUCTIVE_LIMIT,
    array_value,
    boolean,
    identifier,
    object_value,
    optional_boolean,
    optional_text,
    text,
    validate_instance,
)
from .families import Family
from .oracle import FIELD_VERDICTS, GROUNDING_VERDICTS, RESPONSE_VERDICTS
from .records import ObservationRecord
from .routing import TRIGGERS

CLAIMS_SCHEMA_NAME = "conformance-claims.schema.json"
CLAIMS_SCHEMA_VERSION = "creib.conformance-pilot.claims.v1"
CLAIM_KINDS: tuple[str, ...] = ("never", "always")
CLAIM_STATUSES: tuple[str, ...] = ("REFUTED", "UNREFUTED_FOR_DECLARED_SCOPE", "NOT_TESTED")
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
    """The other observations a predicate may refer to: here, the baseline of the same run and case."""

    def __init__(self, observations: list[ObservationRecord]) -> None:
        self._baselines: dict[tuple[str, str], ObservationRecord] = {}
        for observation in observations:
            if observation.variant.family is Family.BASELINE:
                self._baselines[(observation.run_id, observation.variant.base_case_id)] = observation

    def baseline_of(self, observation: ObservationRecord) -> ObservationRecord | None:
        return self._baselines.get((observation.run_id, observation.variant.base_case_id))


Predicate = Callable[[ObservationRecord, Context], bool]


def _output(observation: ObservationRecord) -> Mapping[str, Any]:
    return observation.scoring.parsed_output or {}


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
    try:
        raw = load_strict(path)
    except OSError as exc:
        raise RecordError(f"cannot read claims {path}: {exc}") from exc
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
            "per_model": [{"model": m, "tested": t, "refuting": r} for m, t, r in self.per_model],
            "examples": [{"observation_id": i, "model": m, "case_id": c, "family": f} for i, m, c, f in self.examples],
            "note": self.claim.note,
            "epistemic_limit": NON_INDUCTIVE_LIMIT,
        }


def evaluate_claim(claim: Claim, observations: list[ObservationRecord], context: Context | None = None) -> ClaimResult:
    predicate = compile_condition(claim.condition)
    if context is None:
        context = Context(observations)
    tested: dict[str, int] = {}
    refuting: dict[str, int] = {}
    examples: list[tuple[str, str, str, str]] = []
    for observation in observations:
        if not claim.scope.admits(observation):
            continue
        tested[observation.model] = tested.get(observation.model, 0) + 1
        holds = predicate(observation, context)
        refutes = holds if claim.kind == "never" else not holds
        if refutes:
            refuting[observation.model] = refuting.get(observation.model, 0) + 1
            if len(examples) < _MAX_EXAMPLES:
                examples.append((observation.observation_id, observation.model, observation.variant.base_case_id, observation.variant.family.value))
    total = sum(tested.values())
    if total == 0:
        status = "NOT_TESTED"
    elif refuting:
        status = "REFUTED"
    else:
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
    )


def evaluate_claims(claims: tuple[Claim, ...], observations: list[ObservationRecord]) -> tuple[ClaimResult, ...]:
    context = Context(observations)
    return tuple(evaluate_claim(claim, observations, context) for claim in claims)


def _plural(count: int, noun: str) -> str:
    return f"{count} {noun}" + ("" if count == 1 else "s")


def render_claims_markdown(results: tuple[ClaimResult, ...]) -> str:
    parts = ["# Conjectures tested against the records", ""]
    parts.append("A `never` claim is refuted by one observation where its condition holds; an `always` claim by one where it does not. `UNREFUTED_FOR_DECLARED_SCOPE` means no supplied record refuted the claim; it is not a proof. Counts are of observations, not of quality, and imply no ranking.")
    parts.append("")
    for result in results:
        parts.append(f"## {result.claim.claim_id}: {result.status}")
        parts.append("")
        parts.append(f"*{result.claim.statement}* (`{result.claim.kind}`)")
        parts.append("")
        parts.append(f"- tested on {result.tested} observations from {_plural(len(result.models_tested), 'model')}")
        if result.status == "REFUTED":
            parts.append(f"- refuted by {_plural(result.refuting, 'observation')} from {_plural(len(result.refuting_models), 'model')}: {', '.join(result.refuting_models)}")
            parts.append("- not refuted by: " + (", ".join(m for m in result.models_tested if m not in result.refuting_models) or "-"))
            parts.append("- examples: " + "; ".join(f"`{i[:16]}` ({m}, {c}, {f})" for i, m, c, f in result.examples))
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
