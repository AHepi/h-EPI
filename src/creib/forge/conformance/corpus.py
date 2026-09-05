"""Case corpus for one conformance pilot.

Each case is a document rendered on one or more substrates plus one proposed
oracle per form field.  Every oracle carries a non-final status and a
rationale.  Minimal pairs are cases that differ in one declared fact.

The corpus does not define correctness.  An oracle labelled
``interpretation_provisional`` or ``project_import_provisional`` records that
the expected value is itself contestable; the routing layer keeps the TEST
locus live for such fields.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Iterator, Mapping

from creib.canonical import bytes_digest
from creib.errors import RecordError
from creib.forge.models import OracleStatus
from creib.strict_json import loads_strict

from .common import (
    CORPUS_SCHEMA_NAME,
    CORPUS_SCHEMA_VERSION,
    array_value,
    boolean,
    decode_utf8,
    field_name,
    identifier,
    object_value,
    optional_text,
    scalar,
    text,
    validate_instance,
)
from .spec import TaskSpec


RENDERINGS: tuple[str, ...] = ("prose", "table", "email")
ORACLE_KINDS: tuple[str, ...] = ("exact", "regex", "enum", "absent", "any_of")
_JSON_TYPES: Mapping[str, type] = {"string": str, "boolean": bool, "integer": int}

Scalar = str | bool | int | None


@dataclass(frozen=True)
class Oracle:
    """One proposed expectation for one field; never a ground truth."""

    field: str
    kind: str
    value: Scalar
    values: tuple[Scalar, ...] | None
    pattern: str | None
    oracle_status: str
    rationale: str

    def to_dict(self) -> dict[str, object]:
        return {
            "field": self.field,
            "kind": self.kind,
            "value": self.value,
            "values": None if self.values is None else list(self.values),
            "pattern": self.pattern,
            "oracle_status": self.oracle_status,
            "rationale": self.rationale,
        }

    def summary(self) -> str:
        if self.kind == "exact":
            return f"exact {self.value!r}"
        if self.kind == "absent":
            return "absent"
        if self.kind == "regex":
            return f"regex {self.pattern!r}"
        return f"{self.kind} {list(self.values or ())!r}"


@dataclass(frozen=True)
class RivalExpectation:
    field: str
    label: str
    oracle: Oracle

    def to_dict(self) -> dict[str, object]:
        return {"field": self.field, "label": self.label, "oracle": self.oracle.to_dict()}


@dataclass(frozen=True)
class Case:
    case_id: str
    boundary: bool
    rendering: str
    renderings: Mapping[str, str]
    expected: tuple[Oracle, ...]
    held_fixed: str
    varied: str | None
    pair_of: str | None
    reference_output: tuple[tuple[str, Scalar], ...] | None
    rival_expected: tuple[RivalExpectation, ...]
    notes: str | None

    @property
    def input_document(self) -> str:
        return self.renderings[self.rendering]

    def oracle(self, field: str) -> Oracle | None:
        for oracle in self.expected:
            if oracle.field == field:
                return oracle
        return None

    def to_dict(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "boundary": self.boundary,
            "rendering": self.rendering,
            "renderings": dict(self.renderings),
            "expected": [oracle.to_dict() for oracle in self.expected],
            "held_fixed": self.held_fixed,
            "varied": self.varied,
            "pair_of": self.pair_of,
            "reference_output": (
                None
                if self.reference_output is None
                else [{"field": field, "value": value} for field, value in self.reference_output]
            ),
            "rival_expected": [rival.to_dict() for rival in self.rival_expected],
            "notes": self.notes,
        }


@dataclass(frozen=True)
class Corpus:
    corpus_id: str
    sha256: str
    cases: tuple[Case, ...]

    def case(self, case_id: str) -> Case:
        for case in self.cases:
            if case.case_id == case_id:
                return case
        raise RecordError(f"unknown case {case_id!r}")

    def pairs(self) -> Iterator[tuple[Case, Case]]:
        """Yield (a, b) where ``b.pair_of == a.case_id``."""

        for case in self.cases:
            if case.pair_of is not None:
                yield self.case(case.pair_of), case

    @property
    def ordinary_cases(self) -> tuple[Case, ...]:
        return tuple(case for case in self.cases if not case.boundary)

    @property
    def boundary_cases(self) -> tuple[Case, ...]:
        return tuple(case for case in self.cases if case.boundary)


def _check_value_type(value: Scalar, json_type: str, where: str) -> None:
    expected = _JSON_TYPES[json_type]
    if type(value) is not expected:
        raise RecordError(f"{where} value {value!r} is not of form type {json_type}")


def parse_oracle(
    raw: Any,
    where: str,
    properties: Mapping[str, Mapping[str, Any]],
    *,
    allow_foreign_absent: bool = False,
) -> Oracle:
    """Parse one oracle against the field schemas it will be scored with.

    ``allow_foreign_absent`` admits an ``absent`` oracle for a field that the
    (variant) schema no longer defines; DELETION variants rely on it.
    """

    entry = object_value(raw, where)
    field = field_name(entry["field"], f"{where}.field")
    kind_probe = entry.get("kind")
    if field not in properties and not (allow_foreign_absent and kind_probe == "absent"):
        raise RecordError(f"{where} expects unknown form field {field!r}")
    kind = text(entry["kind"], f"{where}.kind")
    if kind not in ORACLE_KINDS:
        raise RecordError(f"{where}.kind is not a known oracle kind")
    status_raw = text(entry["oracle_status"], f"{where}.oracle_status")
    try:
        OracleStatus(status_raw)
    except ValueError as exc:
        raise RecordError(f"{where}.oracle_status must be a non-final status") from exc
    value = scalar(entry["value"], f"{where}.value")
    values_raw = entry["values"]
    pattern = optional_text(entry["pattern"], f"{where}.pattern")
    values: tuple[Scalar, ...] | None = None
    if values_raw is not None:
        values = tuple(scalar(item, f"{where}.values[{index}]") for index, item in enumerate(array_value(values_raw, f"{where}.values")))
        if not values:
            raise RecordError(f"{where}.values must not be empty")
    json_type = str(properties[field]["type"]) if field in properties else "string"
    if kind == "exact":
        if value is None or values is not None or pattern is not None:
            raise RecordError(f"{where} exact oracle needs value only")
        _check_value_type(value, json_type, where)
    elif kind == "regex":
        if pattern is None or value is not None or values is not None:
            raise RecordError(f"{where} regex oracle needs pattern only")
        if json_type != "string":
            raise RecordError(f"{where} regex oracle applies only to string fields")
        try:
            re.compile(pattern)
        except re.error as exc:
            raise RecordError(f"{where}.pattern is not a valid regex: {exc}") from exc
    elif kind in ("enum", "any_of"):
        if values is None or value is not None or pattern is not None:
            raise RecordError(f"{where} {kind} oracle needs values only")
        for item in values:
            if item is not None:
                _check_value_type(item, json_type, where)
        if len(values) != len(set(values)):
            raise RecordError(f"{where}.values must be distinct")
        if kind == "enum":
            allowed = properties[field].get("enum") if field in properties else None
            if allowed is not None and any(item not in allowed for item in values):
                raise RecordError(f"{where} enum oracle lists values outside the form enum")
    else:
        if value is not None or values is not None or pattern is not None:
            raise RecordError(f"{where} absent oracle carries no value")
    return Oracle(
        field=field,
        kind=kind,
        value=value,
        values=values,
        pattern=pattern,
        oracle_status=status_raw,
        rationale=text(entry["rationale"], f"{where}.rationale"),
    )


def _parse_case(raw: Any, where: str, spec: TaskSpec) -> Case:
    entry = object_value(raw, where)
    case_id = identifier(entry["case_id"], f"{where}.case_id")
    rendering = text(entry["rendering"], f"{where}.rendering")
    if rendering not in RENDERINGS:
        raise RecordError(f"{where}.rendering is not a known substrate")
    renderings_raw = object_value(entry["renderings"], f"{where}.renderings")
    renderings: dict[str, str] = {}
    for key in RENDERINGS:
        if key in renderings_raw:
            renderings[key] = text(renderings_raw[key], f"{where}.renderings.{key}")
    if set(renderings_raw) - set(RENDERINGS):
        raise RecordError(f"{where}.renderings has an unknown substrate")
    if rendering not in renderings:
        raise RecordError(f"{where} base rendering {rendering!r} has no text")

    expected = tuple(
        parse_oracle(item, f"{where}.expected[{index}]", spec.form_schema["properties"])
        for index, item in enumerate(array_value(entry["expected"], f"{where}.expected"))
    )
    fields = [oracle.field for oracle in expected]
    if len(fields) != len(set(fields)):
        raise RecordError(f"{where}.expected lists a field twice")
    for field in spec.required_fields:
        if field not in fields:
            raise RecordError(f"{where} required field {field!r} has no oracle")

    pair_of = optional_text(entry["pair_of"], f"{where}.pair_of")
    varied = optional_text(entry["varied"], f"{where}.varied")
    if (pair_of is None) != (varied is None):
        raise RecordError(f"{where} must declare varied exactly when pair_of is set")
    if pair_of is not None:
        identifier(pair_of, f"{where}.pair_of")
        if pair_of == case_id:
            raise RecordError(f"{where} cannot be its own pair")

    reference_raw = entry["reference_output"]
    reference: tuple[tuple[str, Scalar], ...] | None = None
    if reference_raw is not None:
        items: list[tuple[str, Scalar]] = []
        for index, item in enumerate(array_value(reference_raw, f"{where}.reference_output")):
            pair = object_value(item, f"{where}.reference_output[{index}]")
            field = field_name(pair["field"], f"{where}.reference_output[{index}].field")
            if field not in spec.field_order:
                raise RecordError(f"{where}.reference_output names unknown field {field!r}")
            items.append((field, scalar(pair["value"], f"{where}.reference_output[{index}].value")))
        if len({field for field, _ in items}) != len(items):
            raise RecordError(f"{where}.reference_output repeats a field")
        reference = tuple(items)

    rivals: list[RivalExpectation] = []
    ambiguity_by_field = {ambiguity.field: ambiguity for ambiguity in spec.ambiguities}
    for index, item in enumerate(array_value(entry["rival_expected"], f"{where}.rival_expected")):
        rival_where = f"{where}.rival_expected[{index}]"
        rival = object_value(item, rival_where)
        field = field_name(rival["field"], f"{rival_where}.field")
        ambiguity = ambiguity_by_field.get(field)
        if ambiguity is None:
            raise RecordError(f"{rival_where} names field {field!r} without a declared ambiguity")
        label = identifier(rival["label"], f"{rival_where}.label")
        if label not in {rule.label for rule in ambiguity.rivals}:
            raise RecordError(f"{rival_where} label {label!r} is not a declared rival")
        oracle = parse_oracle(rival["oracle"], f"{rival_where}.oracle", spec.form_schema["properties"])
        if oracle.field != field:
            raise RecordError(f"{rival_where} oracle field must be {field!r}")
        rivals.append(RivalExpectation(field=field, label=label, oracle=oracle))
    if len({(rival.field, rival.label) for rival in rivals}) != len(rivals):
        raise RecordError(f"{where}.rival_expected repeats a (field, label) pair")

    return Case(
        case_id=case_id,
        boundary=boolean(entry["boundary"], f"{where}.boundary"),
        rendering=rendering,
        renderings=renderings,
        expected=expected,
        held_fixed=text(entry["held_fixed"], f"{where}.held_fixed"),
        varied=varied,
        pair_of=pair_of,
        reference_output=reference,
        rival_expected=tuple(rivals),
        notes=optional_text(entry["notes"], f"{where}.notes"),
    )


def parse_corpus(raw: Any, spec: TaskSpec, *, sha256: str) -> Corpus:
    record = object_value(raw, "corpus")
    validate_instance(record, CORPUS_SCHEMA_NAME)
    if record["schema_version"] != CORPUS_SCHEMA_VERSION:
        raise RecordError("corpus schema_version mismatch")
    cases = tuple(
        _parse_case(item, f"cases[{index}]", spec)
        for index, item in enumerate(array_value(record["cases"], "cases"))
    )
    ids = [case.case_id for case in cases]
    if len(ids) != len(set(ids)):
        raise RecordError("corpus case_id values must be unique")
    for case in cases:
        if case.pair_of is not None and case.pair_of not in ids:
            raise RecordError(f"case {case.case_id} pairs with unknown case {case.pair_of!r}")
    return Corpus(corpus_id=identifier(record["corpus_id"], "corpus_id"), sha256=sha256, cases=cases)


def load_corpus(path: Path, spec: TaskSpec) -> Corpus:
    """Strict-load a corpus file and check it against the task specification."""

    if not isinstance(path, Path):
        raise TypeError("path must be pathlib.Path")
    try:
        raw_bytes = path.read_bytes()
    except OSError as exc:
        raise RecordError(f"cannot read corpus {path}: {exc}") from exc
    raw = loads_strict(decode_utf8(raw_bytes, str(path)))
    return parse_corpus(raw, spec, sha256=bytes_digest(raw_bytes))
