"""Scoring of one response against one variant: plural verdicts, no number.

A response is first classified at the response level (transport failure,
empty, truncated, unparseable, refusal suspected, not an object), then each
form field receives its own verdict.  Nothing here is summed or weighted.
A ``MATCH`` means the output met one non-final oracle; it is not evidence
that the model understands the form.

Recovering a JSON object embedded in prose or code fences is a project
import: it is applied only after strict parsing fails, and the scoring
records ``recovered_from_prose`` with a provisional status so a human can
decide whether recovered output should count at all.
"""

from __future__ import annotations

import json

from dataclasses import dataclass
import re
from typing import Any, Mapping

from jsonschema import Draft202012Validator

from creib.canonical import canonical_bytes
from creib.errors import RecordError
from .common import OracleStatus
from creib.strict_json import loads_strict

from .common import (
    any_string,
    array_value,
    boolean,
    canonical_text,
    object_value,
    optional_boolean,
    optional_text,
    text,
)
from .corpus import Oracle
from .executor import ChatResponse
from .families import ExpectationKind, Variant


RESPONSE_VERDICTS: tuple[str, ...] = (
    "JSON_OBJECT",
    "TRANSPORT_ERROR",
    "EMPTY_RESPONSE",
    "TRUNCATED",
    "INVALID_JSON",
    "NOT_AN_OBJECT",
    "REFUSAL_SUSPECTED",
    "NO_MODEL_CALL",
    "PREREQUISITE_UNAVAILABLE",
)
FIELD_VERDICTS: tuple[str, ...] = (
    "MATCH",
    "MISMATCH",
    "MISSING_REQUIRED",
    "EXTRA_FIELD",
    "TYPE_VIOLATION",
    "PATTERN_VIOLATION",
    "ENUM_VIOLATION",
    "LENGTH_VIOLATION",
    "UNEXPECTED_PRESENT",
    "NOT_SCORED",
)
_JSON_TYPES: Mapping[str, type] = {"string": str, "boolean": bool, "integer": int}
GROUNDING_VERDICTS: tuple[str, ...] = ("GROUNDED", "SPAN_MISSING", "SPAN_NOT_IN_DOCUMENT", "VALUE_NOT_IN_SPAN", "ABSTAINED")
GROUNDING_CRITICISMS: tuple[str, ...] = ("SPAN_MISSING", "SPAN_NOT_IN_DOCUMENT", "VALUE_NOT_IN_SPAN")
_FENCE = re.compile(r"```(?:json|JSON)?\s*(.*?)```", re.DOTALL)


@dataclass(frozen=True)
class FieldVerdict:
    field: str
    verdict: str
    observed_present: bool
    observed_canonical: str | None
    expected_summary: str | None
    oracle_status: str | None
    detail: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "field": self.field,
            "verdict": self.verdict,
            "observed_present": self.observed_present,
            "observed_canonical": self.observed_canonical,
            "expected_summary": self.expected_summary,
            "oracle_status": self.oracle_status,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class GroundingVerdict:
    """Provenance check for one field: is the cited span real, and does the value come from it?

    GROUNDED is a structural property of the reply (the cited text exists and
    contains the value); it is not a judgement that the value is correct.
    """

    field: str
    verdict: str
    span: str | None
    detail: str | None

    def to_dict(self) -> dict[str, object]:
        return {"field": self.field, "verdict": self.verdict, "span": self.span, "detail": self.detail}


@dataclass(frozen=True)
class Scoring:
    response_verdict: str
    response_detail: str | None
    recovered_from_prose: bool
    recovery_status: str | None
    parsed_output: dict[str, Any] | None
    schema_valid: bool | None
    field_verdicts: tuple[FieldVerdict, ...]
    changed_vs_baseline: bool | None
    grounding_verdicts: tuple[GroundingVerdict, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "response_verdict": self.response_verdict,
            "response_detail": self.response_detail,
            "recovered_from_prose": self.recovered_from_prose,
            "recovery_status": self.recovery_status,
            "parsed_output_canonical": None if self.parsed_output is None else canonical_text(self.parsed_output),
            "schema_valid": self.schema_valid,
            "field_verdicts": [verdict.to_dict() for verdict in self.field_verdicts],
            "changed_vs_baseline": self.changed_vs_baseline,
            "grounding_verdicts": [verdict.to_dict() for verdict in self.grounding_verdicts],
        }

    def grounding_kinds(self) -> tuple[str, ...]:
        """Distinct grounding criticisms (never GROUNDED or ABSTAINED), in field order."""

        seen: list[str] = []
        for verdict in self.grounding_verdicts:
            if verdict.verdict in GROUNDING_CRITICISMS and verdict.verdict not in seen:
                seen.append(verdict.verdict)
        return tuple(seen)

    def verdict_kinds(self) -> tuple[str, ...]:
        """Distinct field verdicts other than MATCH and NOT_SCORED, in field order."""

        seen: list[str] = []
        for verdict in self.field_verdicts:
            if verdict.verdict not in ("MATCH", "NOT_SCORED") and verdict.verdict not in seen:
                seen.append(verdict.verdict)
        return tuple(seen)

    @property
    def all_match(self) -> bool:
        return self.response_verdict in ("JSON_OBJECT", "NO_MODEL_CALL") and bool(self.schema_valid) and all(
            verdict.verdict in ("MATCH", "NOT_SCORED") for verdict in self.field_verdicts
        )


def scoring_from_dict(raw: Any, where: str = "scoring") -> Scoring:
    record = object_value(raw, where)
    verdict = text(record["response_verdict"], f"{where}.response_verdict")
    if verdict not in RESPONSE_VERDICTS:
        raise RecordError(f"{where}.response_verdict is unknown")
    parsed_raw = record["parsed_output_canonical"]
    parsed: dict[str, Any] | None = None
    if parsed_raw is not None:
        parsed = object_value(loads_strict(text(parsed_raw, f"{where}.parsed_output_canonical")), f"{where}.parsed_output_canonical")
        if canonical_text(parsed) != parsed_raw:
            raise RecordError(f"{where}.parsed_output_canonical is not canonical")
    grounding: list[GroundingVerdict] = []
    for index, item in enumerate(array_value(record["grounding_verdicts"], f"{where}.grounding_verdicts")):
        entry = object_value(item, f"{where}.grounding_verdicts[{index}]")
        kind = text(entry["verdict"], f"{where}.grounding_verdicts[{index}].verdict")
        if kind not in GROUNDING_VERDICTS:
            raise RecordError(f"{where}.grounding_verdicts[{index}].verdict is unknown")
        grounding.append(
            GroundingVerdict(
                field=any_string(entry["field"], f"{where}.grounding_verdicts[{index}].field"),
                verdict=kind,
                span=None if entry["span"] is None else any_string(entry["span"], f"{where}.grounding_verdicts[{index}].span"),
                detail=optional_text(entry["detail"], f"{where}.grounding_verdicts[{index}].detail"),
            )
        )
    verdicts: list[FieldVerdict] = []
    for index, item in enumerate(array_value(record["field_verdicts"], f"{where}.field_verdicts")):
        entry = object_value(item, f"{where}.field_verdicts[{index}]")
        kind = text(entry["verdict"], f"{where}.field_verdicts[{index}].verdict")
        if kind not in FIELD_VERDICTS:
            raise RecordError(f"{where}.field_verdicts[{index}].verdict is unknown")
        verdicts.append(
            FieldVerdict(
                field=any_string(entry["field"], f"{where}.field_verdicts[{index}].field"),
                verdict=kind,
                observed_present=boolean(entry["observed_present"], f"{where}.field_verdicts[{index}].observed_present"),
                observed_canonical=None if entry["observed_canonical"] is None else text(entry["observed_canonical"], f"{where}.field_verdicts[{index}].observed_canonical"),
                expected_summary=optional_text(entry["expected_summary"], f"{where}.field_verdicts[{index}].expected_summary"),
                oracle_status=optional_text(entry["oracle_status"], f"{where}.field_verdicts[{index}].oracle_status"),
                detail=optional_text(entry["detail"], f"{where}.field_verdicts[{index}].detail"),
            )
        )
    return Scoring(
        response_verdict=verdict,
        response_detail=optional_text(record["response_detail"], f"{where}.response_detail"),
        recovered_from_prose=boolean(record["recovered_from_prose"], f"{where}.recovered_from_prose"),
        recovery_status=optional_text(record["recovery_status"], f"{where}.recovery_status"),
        parsed_output=parsed,
        schema_valid=optional_boolean(record["schema_valid"], f"{where}.schema_valid"),
        field_verdicts=tuple(verdicts),
        changed_vs_baseline=optional_boolean(record["changed_vs_baseline"], f"{where}.changed_vs_baseline"),
        grounding_verdicts=tuple(grounding),
    )


def recover_json_object(content: str) -> Any:
    """Project import: extract a JSON object from fences or surrounding prose."""

    candidates: list[str] = [match.group(1) for match in _FENCE.finditer(content)]
    # Every balanced object in the text is a candidate, not only the span from
    # the first "{" to the last "}": reasoning prose before or after the answer
    # frequently contains stray braces. Among the candidates that parse as
    # strict objects, the one with the most keys is taken; ties go to the last,
    # because models place their final answer last.
    decoder = json.JSONDecoder()
    for index, character in enumerate(content):
        if character != "{":
            continue
        try:
            _value, end = decoder.raw_decode(content, index)
        except (ValueError, RecursionError):
            continue
        candidates.append(content[index:end])
    best: dict[str, Any] | None = None
    best_duplicates: tuple[str, ...] = ()
    for candidate in candidates:
        duplicates: tuple[str, ...] = ()
        try:
            value = loads_strict(candidate.strip())
        except (RecordError, ValueError, RecursionError):
            # Strict JSON refuses duplicate keys. A reply that is otherwise one well-formed object with a
            # repeated key is still scoreable: take the last value for each key, and say which keys repeated.
            parsed = _loads_last_wins(candidate.strip())
            if parsed is None:
                continue
            value, duplicates = parsed
        if type(value) is dict and (best is None or len(value) >= len(best)):
            best, best_duplicates = value, duplicates
    if best is not None:
        return best, best_duplicates
    raise RecordError("no JSON object could be recovered from the response")


def _loads_last_wins(candidate: str) -> tuple[Any, tuple[str, ...]] | None:
    """Parse JSON that strict parsing refused only because of repeated keys; last value wins."""

    seen_duplicates: list[str] = []

    def pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        counts: dict[str, int] = {}
        for key, _ in pairs:
            counts[key] = counts.get(key, 0) + 1
        seen_duplicates.extend(key for key, n in counts.items() if n > 1)
        return dict(pairs)

    try:
        value = json.loads(candidate, object_pairs_hook=pairs_hook, parse_float=_refuse_float, parse_constant=_refuse_constant)
    except (ValueError, RecursionError):
        return None
    if not seen_duplicates:
        return None
    return value, tuple(sorted(set(seen_duplicates)))


def _refuse_float(_text: str) -> Any:
    raise ValueError("floats are not admitted")


def _refuse_constant(_text: str) -> Any:
    raise ValueError("NaN and Infinity are not admitted")


def parse_content(content: str, refusal_phrases: tuple[str, ...]) -> tuple[Any, str, str | None, bool]:
    """Return (parsed, response_verdict, detail, recovered_from_prose)."""

    try:
        return loads_strict(content), "JSON_OBJECT", None, False
    except (RecordError, ValueError, RecursionError) as strict_error:
        try:
            recovered, duplicates = recover_json_object(content)
        except RecordError:
            lowered = content.lower()
            for phrase in refusal_phrases:
                if phrase.lower() in lowered:
                    return None, "REFUSAL_SUSPECTED", f"matched refusal phrase {phrase!r}; heuristic", False
            return None, "INVALID_JSON", str(strict_error), False
        if duplicates:
            detail = (
                f"strict parse failed ({strict_error}); object recovered with duplicate keys "
                f"{list(duplicates)!r} resolved last-wins"
            )
        else:
            detail = f"strict parse failed ({strict_error}); object recovered from prose"
        return recovered, "JSON_OBJECT", detail, True


def _constraint_verdict(value: Any, property_schema: Mapping[str, Any]) -> tuple[str | None, str | None]:
    json_type = property_schema.get("type")
    expected_type = _JSON_TYPES.get(str(json_type))
    if expected_type is None or type(value) is not expected_type:
        return "TYPE_VIOLATION", f"expected JSON type {json_type}"
    if type(value) is str:
        pattern = property_schema.get("pattern")
        if pattern is not None and re.search(pattern, value) is None:
            return "PATTERN_VIOLATION", f"does not match {pattern!r}"
        allowed = property_schema.get("enum")
        if allowed is not None and value not in allowed:
            return "ENUM_VIOLATION", f"not one of {list(allowed)!r}"
        maximum = property_schema.get("maxLength")
        if maximum is not None and len(value) > maximum:
            return "LENGTH_VIOLATION", f"length {len(value)} exceeds maxLength {maximum}"
        minimum = property_schema.get("minLength")
        if minimum is not None and len(value) < minimum:
            return "LENGTH_VIOLATION", f"length {len(value)} below minLength {minimum}"
    return None, None


def _oracle_verdict(value: Any, oracle: Oracle) -> tuple[str, str | None]:
    if oracle.kind == "unknown":
        return "NOT_SCORED", "no expectation declared; value recorded, not judged"
    if oracle.kind == "exact":
        return ("MATCH", None) if value == oracle.value and type(value) is type(oracle.value) else ("MISMATCH", f"expected {oracle.value!r}")
    if oracle.kind in ("enum", "any_of"):
        return ("MATCH", None) if value in (oracle.values or ()) else ("MISMATCH", f"expected one of {list(oracle.values or ())!r}")
    if oracle.kind == "regex":
        if type(value) is str and re.search(oracle.pattern or "", value) is not None:
            return "MATCH", None
        return "MISMATCH", f"expected to match {oracle.pattern!r}"
    raise RecordError(f"oracle kind {oracle.kind} is not comparable to a present value")


def _field_verdict(field: str, verdict: str, output: Mapping[str, Any], oracle: Oracle | None, detail: str | None) -> FieldVerdict:
    present = field in output
    return FieldVerdict(
        field=field,
        verdict=verdict,
        observed_present=present,
        observed_canonical=canonical_text(output[field]) if present else None,
        expected_summary=None if oracle is None else oracle.summary(),
        oracle_status=None if oracle is None else oracle.oracle_status,
        detail=detail,
    )


def _normalise_whitespace(value: str) -> str:
    return " ".join(value.split())


def _grounding_verdict(variant: Variant, field: str, value: Any, output: Mapping[str, Any]) -> GroundingVerdict:
    key = variant.span_key(field)
    span = output.get(key)
    if type(span) is not str or not span.strip():
        return GroundingVerdict(field, "SPAN_MISSING", None, f"companion key {key!r} is absent, null, or empty")
    document = variant.input_document or ""
    if _normalise_whitespace(span) not in _normalise_whitespace(document):
        return GroundingVerdict(field, "SPAN_NOT_IN_DOCUMENT", span, "the cited text does not occur verbatim in the document (whitespace-normalised)")
    if field in variant.active_value_in_span_fields and str(value).casefold() not in span.casefold():
        return GroundingVerdict(field, "VALUE_NOT_IN_SPAN", span, "the value does not occur inside the cited span (case-insensitive)")
    return GroundingVerdict(field, "GROUNDED", span, None)


def score_output(variant: Variant, output: Mapping[str, Any]) -> tuple[bool, tuple[FieldVerdict, ...], tuple[GroundingVerdict, ...]]:
    """Schema validity, one verdict per schema field and per extra key, and grounding verdicts."""

    # A model reply is validated against the schema the model was sent (companion span keys and
    # nullable abstain fields included); a model-free control output is a reference output in the
    # bound form's own shape and is validated against the bound form schema.
    schema = variant.prompt_form_schema() if variant.model_call else variant.form_schema
    validator = Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)
    schema_valid = not any(True for _ in validator.iter_errors(dict(output)))
    verdicts: list[FieldVerdict] = []
    record_only = variant.expectation_kind is ExpectationKind.RECORD_DEPENDENCE
    required = set(variant.required_fields)
    properties = variant.form_schema["properties"]
    abstain = set(variant.active_abstain_fields)
    span_fields = set(variant.active_span_fields) if variant.model_call else set()
    companion_keys = {variant.span_key(field) for field in variant.active_span_fields} if variant.grounding is not None and variant.grounding.active else set()
    grounding: list[GroundingVerdict] = []
    for field in variant.field_order:
        oracle = variant.oracle(field)
        if record_only:
            verdicts.append(_field_verdict(field, "NOT_SCORED", output, oracle, "dependence is recorded, not scored"))
            continue
        if field not in output:
            if oracle is not None and oracle.kind == "absent":
                verdicts.append(_field_verdict(field, "MATCH", output, oracle, None))
            elif field in required:
                verdicts.append(_field_verdict(field, "MISSING_REQUIRED", output, oracle, "required key absent"))
            elif oracle is None or oracle.kind == "unknown":
                verdicts.append(_field_verdict(field, "NOT_SCORED", output, oracle, "optional key absent; no expectation"))
            else:
                verdicts.append(_field_verdict(field, "MISMATCH", output, oracle, "optional key absent but a value was expected"))
            continue
        value = output[field]
        if oracle is not None and oracle.kind == "absent":
            verdicts.append(_field_verdict(field, "UNEXPECTED_PRESENT", output, oracle, "key present although expected absent"))
            continue
        if value is None and field in abstain:
            # The model declined to state a value it was allowed to decline.
            grounding.append(GroundingVerdict(field, "ABSTAINED", None, "null returned for a field the configuration allows to be unstated"))
            if oracle is None or oracle.kind == "unknown":
                verdicts.append(_field_verdict(field, "NOT_SCORED", output, oracle, "abstained; no expectation declared"))
            elif oracle.kind in ("enum", "any_of") and None in (oracle.values or ()):
                # The answer key says the document does not state this value: abstaining is the expected answer.
                verdicts.append(_field_verdict(field, "MATCH", output, oracle, None))
            else:
                verdicts.append(_field_verdict(field, "MISMATCH", output, oracle, "abstained where the oracle expected a value"))
            continue
        constraint_verdict, constraint_detail = _constraint_verdict(value, properties[field])
        if constraint_verdict is not None:
            verdicts.append(_field_verdict(field, constraint_verdict, output, oracle, constraint_detail))
            continue
        if oracle is None:
            verdicts.append(_field_verdict(field, "NOT_SCORED", output, None, "no oracle for this field"))
            continue
        verdict, detail = _oracle_verdict(value, oracle)
        verdicts.append(_field_verdict(field, verdict, output, oracle, detail))
    for field in variant.field_order:
        if field in span_fields and field in output and output[field] is not None and not record_only:
            grounding.append(_grounding_verdict(variant, field, output[field], output))
    for key in sorted(k for k in output if k not in variant.field_order and k not in companion_keys):
        oracle = variant.oracle(key)
        if record_only:
            verdicts.append(_field_verdict(key, "NOT_SCORED", output, oracle, "dependence is recorded, not scored"))
        elif oracle is not None and oracle.kind == "absent":
            verdicts.append(_field_verdict(key, "UNEXPECTED_PRESENT", output, oracle, "key present although removed from the form"))
        else:
            verdicts.append(_field_verdict(key, "EXTRA_FIELD", output, oracle, "key is not defined by the form schema"))
    return schema_valid, tuple(verdicts), tuple(grounding)


def _changed(parsed: Mapping[str, Any] | None, baseline_output: Mapping[str, Any] | None, fields: tuple[str, ...]) -> bool | None:
    """Whether the form's own field values changed against the baseline.

    Only the declared form fields are compared. Companion span keys are provenance, not answers,
    and keys outside the form are reported per observation as EXTRA_FIELD; neither makes a fill
    "unstable" or "dependent" on its own.
    """

    if parsed is None or baseline_output is None:
        return None
    left = {k: parsed[k] for k in fields if k in parsed}
    right = {k: baseline_output[k] for k in fields if k in baseline_output}
    return canonical_bytes(left) != canonical_bytes(right)


def score(
    variant: Variant,
    response: ChatResponse | None,
    *,
    refusal_phrases: tuple[str, ...] = (),
    baseline_output: Mapping[str, Any] | None = None,
) -> Scoring:
    """Score one response (or one model-free control when ``response`` is None)."""

    if response is None:
        if variant.control_output is None or variant.model_call:
            raise RecordError("a response is required unless the variant is a model-free control")
        output = dict(variant.control_output)
        schema_valid, verdicts, grounding = score_output(variant, output)
        return Scoring("NO_MODEL_CALL", None, False, None, output, schema_valid, verdicts, None, grounding)
    if not response.usable:
        detail = response.transport_error or f"HTTP status {response.http_status}"
        return Scoring("TRANSPORT_ERROR", detail, False, None, None, None, (), None)
    if not response.content.strip():
        return Scoring("EMPTY_RESPONSE", "response content is empty", False, None, None, None, (), None)
    if response.done_reason == "length":
        return Scoring("TRUNCATED", "done_reason is length", False, None, None, None, (), None)
    parsed, verdict, detail, recovered = parse_content(response.content, refusal_phrases)
    if verdict != "JSON_OBJECT":
        return Scoring(verdict, detail, False, None, None, None, (), None)
    if type(parsed) is not dict:
        return Scoring("NOT_AN_OBJECT", f"parsed JSON is {type(parsed).__name__}", recovered, None, None, None, (), None)
    schema_valid, verdicts, grounding = score_output(variant, parsed)
    return Scoring(
        response_verdict="JSON_OBJECT",
        response_detail=detail,
        recovered_from_prose=recovered,
        recovery_status=OracleStatus.PROJECT_IMPORT_PROVISIONAL.value if recovered else None,
        parsed_output=parsed,
        schema_valid=schema_valid,
        field_verdicts=verdicts,
        changed_vs_baseline=_changed(parsed, baseline_output, variant.field_order),
        grounding_verdicts=grounding,
    )


def prerequisite_unavailable(detail: str) -> Scoring:
    """Scoring for a chained variant whose prerequisite output was unusable."""

    return Scoring("PREREQUISITE_UNAVAILABLE", detail, False, None, None, None, (), None)
