"""The adversarial test families of the conformance pilot.

Each family is a pure function ``(spec, case) -> list[Variant]``.  A variant
is a content-addressed, fully materialised task instance: the exact form
schema, instruction text, document, and per-field oracles a model will face.
``BASELINE`` is not a test family; it is the reference observation the
NEGATION, IMPORT_DEPENDENCY, and ROUND_TRIP families compare against.

Case selection per family:

* BASELINE, DELETION, NEGATION, SEMANTIC_ROLE_TWIN, SUBSTRATE_SWAP,
  IMPORT_DEPENDENCY, ROUND_TRIP act on ordinary (non-boundary) cases;
* BOUNDARY_SHIFT selects boundary cases unchanged (it is their baseline);
* RIVAL_SUBSTITUTION acts on any case that declares ``rival_expected``;
* NON_VACUITY acts on any case that supplies a ``reference_output`` and makes
  no model call.

A variant records what was held fixed and what was changed.  It does not
record what the "right" answer is beyond the case's non-final oracles, and a
family never asserts that a model passes or fails.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Any, Callable, Mapping

from creib.errors import RecordError
from creib.forge.models import OracleStatus

from .common import (
    array_value,
    boolean,
    content_id,
    field_name,
    frozen_mapping_to_dict,
    hex_digest,
    identifier,
    object_value,
    optional_text,
    scalar,
    text,
)
from .corpus import Case, Corpus, Oracle, Scalar, parse_oracle
from .spec import TaskSpec, render_instructions, validate_form_schema


VARIANT_DOMAIN = "creib.conformance-pilot.variant.v1"
PLAN_DOMAIN = "creib.conformance-pilot.plan.v1"


class Family(str, Enum):
    BASELINE = "BASELINE"
    DELETION = "DELETION"
    NEGATION = "NEGATION"
    RIVAL_SUBSTITUTION = "RIVAL_SUBSTITUTION"
    SEMANTIC_ROLE_TWIN = "SEMANTIC_ROLE_TWIN"
    SUBSTRATE_SWAP = "SUBSTRATE_SWAP"
    BOUNDARY_SHIFT = "BOUNDARY_SHIFT"
    IMPORT_DEPENDENCY = "IMPORT_DEPENDENCY"
    NON_VACUITY = "NON_VACUITY"
    ROUND_TRIP = "ROUND_TRIP"


TEST_FAMILIES: tuple[Family, ...] = tuple(family for family in Family if family is not Family.BASELINE)


class ExpectationKind(str, Enum):
    ORACLE = "ORACLE"
    RECORD_DEPENDENCE = "RECORD_DEPENDENCE"
    ROUND_TRIP = "ROUND_TRIP"
    CONTROL_REJECT = "CONTROL_REJECT"
    CONTROL_ACCEPT = "CONTROL_ACCEPT"


@dataclass(frozen=True)
class Variant:
    variant_id: str
    family: Family
    base_case_id: str
    form_schema: dict[str, Any]
    field_order: tuple[str, ...]
    instructions: str
    input_document: str | None
    expected: tuple[Oracle, ...]
    held_fixed: str
    controlled_difference: str
    expectation_kind: ExpectationKind
    substrate: str | None
    control_id: str | None
    control_output: tuple[tuple[str, Scalar], ...] | None
    model_call: bool
    round_trip_of: str | None
    rival_label: str | None
    removed_sentence_id: str | None

    @property
    def required_fields(self) -> tuple[str, ...]:
        return tuple(self.form_schema.get("required", ()))

    def oracle(self, field: str) -> Oracle | None:
        for oracle in self.expected:
            if oracle.field == field:
                return oracle
        return None

    def body(self) -> dict[str, object]:
        return {
            "family": self.family.value,
            "base_case_id": self.base_case_id,
            "form_schema": frozen_mapping_to_dict(self.form_schema),
            "field_order": list(self.field_order),
            "instructions": self.instructions,
            "input_document": self.input_document,
            "expected": [oracle.to_dict() for oracle in self.expected],
            "held_fixed": self.held_fixed,
            "controlled_difference": self.controlled_difference,
            "expectation_kind": self.expectation_kind.value,
            "substrate": self.substrate,
            "control_id": self.control_id,
            "control_output": (
                None
                if self.control_output is None
                else [{"field": field, "value": value} for field, value in self.control_output]
            ),
            "model_call": self.model_call,
            "round_trip_of": self.round_trip_of,
            "rival_label": self.rival_label,
            "removed_sentence_id": self.removed_sentence_id,
        }

    def to_dict(self) -> dict[str, object]:
        record = self.body()
        record["variant_id"] = self.variant_id
        return record


def make_variant(**fields: Any) -> Variant:
    """Build a variant and assign its content-addressed identifier."""

    draft = Variant(variant_id="0" * 64, **fields)
    return Variant(variant_id=content_id(VARIANT_DOMAIN, draft.body()), **fields)


def variant_from_dict(raw: Any) -> Variant:
    """Rebuild a variant from a record and fail closed if its id does not replay."""

    record = object_value(raw, "variant")
    try:
        family = Family(text(record["family"], "variant.family"))
        expectation = ExpectationKind(text(record["expectation_kind"], "variant.expectation_kind"))
    except ValueError as exc:
        raise RecordError(f"variant carries an unknown family or expectation kind: {exc}") from exc
    form_schema, schema_fields = validate_form_schema(record["form_schema"], "variant.form_schema")
    field_order = tuple(field_name(item, "variant.field_order") for item in array_value(record["field_order"], "variant.field_order"))
    if set(field_order) != set(schema_fields) or len(field_order) != len(schema_fields):
        raise RecordError("variant.field_order does not match its form schema")
    control_raw = record["control_output"]
    control_output: tuple[tuple[str, Scalar], ...] | None = None
    if control_raw is not None:
        control_output = tuple(
            (
                text(object_value(item, "variant.control_output")["field"], "variant.control_output.field"),
                scalar(object_value(item, "variant.control_output")["value"], "variant.control_output.value"),
            )
            for item in array_value(control_raw, "variant.control_output")
        )
    expected = tuple(
        parse_oracle(item, f"variant.expected[{index}]", form_schema["properties"], allow_foreign_absent=True)
        for index, item in enumerate(array_value(record["expected"], "variant.expected"))
    )
    rebuilt = make_variant(
        family=family,
        base_case_id=identifier(record["base_case_id"], "variant.base_case_id"),
        form_schema=form_schema,
        field_order=field_order,
        instructions=text(record["instructions"], "variant.instructions"),
        input_document=None if record["input_document"] is None else text(record["input_document"], "variant.input_document"),
        expected=expected,
        held_fixed=text(record["held_fixed"], "variant.held_fixed"),
        controlled_difference=text(record["controlled_difference"], "variant.controlled_difference"),
        expectation_kind=expectation,
        substrate=optional_text(record["substrate"], "variant.substrate"),
        control_id=optional_text(record["control_id"], "variant.control_id"),
        control_output=control_output,
        model_call=boolean(record["model_call"], "variant.model_call"),
        round_trip_of=None if record["round_trip_of"] is None else hex_digest(record["round_trip_of"], "variant.round_trip_of"),
        rival_label=optional_text(record["rival_label"], "variant.rival_label"),
        removed_sentence_id=optional_text(record["removed_sentence_id"], "variant.removed_sentence_id"),
    )
    if rebuilt.variant_id != hex_digest(record["variant_id"], "variant.variant_id"):
        raise RecordError("variant_id does not replay from the variant content")
    return rebuilt


# --------------------------------------------------------------------------
# value transforms for NEGATION
# --------------------------------------------------------------------------


def iso_date_to_dmy(value: str) -> str:
    match = re.fullmatch(r"([0-9]{4})-([0-9]{2})-([0-9]{2})", value)
    if match is None:
        raise RecordError(f"negation transform iso_date_to_dmy needs an ISO date, got {value!r}")
    return f"{match.group(3)}/{match.group(2)}/{match.group(1)}"


def e164_au_to_national_spaced(value: str) -> str:
    """+61XXXXXXXXX -> 04XX XXX XXX for mobiles, 0X XXXX XXXX otherwise."""

    match = re.fullmatch(r"\+61([0-9]{9})", value)
    if match is None:
        raise RecordError(f"negation transform e164_au_to_national_spaced needs +61 E.164, got {value!r}")
    national = "0" + match.group(1)
    if national.startswith("04"):
        return f"{national[:4]} {national[4:7]} {national[7:]}"
    return f"{national[:2]} {national[2:6]} {national[6:]}"


VALUE_TRANSFORMS: Mapping[str, Callable[[str], str]] = {
    "iso_date_to_dmy": iso_date_to_dmy,
    "e164_au_to_national_spaced": e164_au_to_national_spaced,
}


def _transform_oracle(oracle: Oracle, transform_name: str) -> Oracle:
    transform = VALUE_TRANSFORMS[transform_name]
    if oracle.kind == "absent":
        return oracle
    if oracle.kind == "exact":
        if type(oracle.value) is not str:
            raise RecordError(f"negation of {oracle.field} needs a string oracle")
        return Oracle(
            field=oracle.field,
            kind="exact",
            value=transform(oracle.value),
            values=None,
            pattern=None,
            oracle_status=oracle.oracle_status,
            rationale=oracle.rationale + f" (re-expressed by {transform_name} for the negated instruction)",
        )
    if oracle.kind == "any_of":
        values = tuple(transform(item) if type(item) is str else item for item in oracle.values or ())
        return Oracle(
            field=oracle.field,
            kind="any_of",
            value=None,
            values=values,
            pattern=None,
            oracle_status=oracle.oracle_status,
            rationale=oracle.rationale + f" (re-expressed by {transform_name} for the negated instruction)",
        )
    raise RecordError(
        f"negation of {oracle.field} cannot re-express a {oracle.kind} oracle; use exact or any_of"
    )


# --------------------------------------------------------------------------
# shared construction helpers
# --------------------------------------------------------------------------


def _schema_for(spec: TaskSpec, field_order: tuple[str, ...], pattern_overrides: Mapping[str, str] | None = None) -> dict[str, Any]:
    base = spec.form_schema
    properties: dict[str, Any] = {}
    for field in field_order:
        property_schema = frozen_mapping_to_dict(base["properties"][field])
        if pattern_overrides and field in pattern_overrides:
            property_schema["pattern"] = pattern_overrides[field]
        properties[field] = property_schema
    schema: dict[str, Any] = {}
    for key, value in base.items():
        if key == "properties":
            schema[key] = properties
        elif key == "required":
            schema[key] = [field for field in field_order if field in value]
        else:
            schema[key] = frozen_mapping_to_dict(value) if isinstance(value, Mapping) else value
    return schema


def _sentence_texts(spec: TaskSpec) -> list[str]:
    return [sentence.text for sentence in spec.sentences]


def _instructions(spec: TaskSpec, sentences: list[str]) -> str:
    return render_instructions(spec.preamble, tuple(sentences))


def _base_fields(spec: TaskSpec, case: Case, document: str | None = None) -> dict[str, Any]:
    return {
        "base_case_id": case.case_id,
        "form_schema": _schema_for(spec, spec.field_order),
        "field_order": spec.field_order,
        "instructions": spec.instructions,
        "input_document": case.input_document if document is None else document,
        "expected": case.expected,
        "expectation_kind": ExpectationKind.ORACLE,
        "substrate": case.rendering,
        "control_id": None,
        "control_output": None,
        "model_call": True,
        "round_trip_of": None,
        "rival_label": None,
        "removed_sentence_id": None,
    }


# --------------------------------------------------------------------------
# families
# --------------------------------------------------------------------------


def baseline(spec: TaskSpec, case: Case) -> list[Variant]:
    if case.boundary:
        return []
    fields = _base_fields(spec, case)
    fields.update(
        family=Family.BASELINE,
        held_fixed="form schema, instructions, and document exactly as bound",
        controlled_difference="none; reference observation for comparison families",
    )
    return [make_variant(**fields)]


def deletion(spec: TaskSpec, case: Case) -> list[Variant]:
    """Remove each optional field from schema and instructions; it must not appear."""

    if case.boundary:
        return []
    variants: list[Variant] = []
    for obligation in spec.obligations:
        if obligation.required:
            continue
        field = obligation.field
        remaining = tuple(item for item in spec.field_order if item != field)
        removed = [sentence.sentence_id for sentence in spec.sentences if sentence.primary_field == field]
        sentences = [sentence.text for sentence in spec.sentences if sentence.primary_field != field]
        expected = tuple(oracle for oracle in case.expected if oracle.field != field) + (
            Oracle(
                field=field,
                kind="absent",
                value=None,
                values=None,
                pattern=None,
                oracle_status=OracleStatus.SOURCE_SCOPED.value,
                rationale=f"{field} was removed from the form schema; emitting it ignores the schema",
            ),
        )
        fields = _base_fields(spec, case)
        fields.update(
            family=Family.DELETION,
            form_schema=_schema_for(spec, remaining),
            field_order=remaining,
            instructions=_instructions(spec, sentences),
            expected=expected,
            held_fixed="document and every other field's schema, instruction, and oracle",
            controlled_difference=(
                f"field {field} removed from the schema and its sentence(s) "
                f"{', '.join(removed) or 'none'} removed from the instructions"
            ),
        )
        variants.append(make_variant(**fields))
    return variants


def negation(spec: TaskSpec, case: Case) -> list[Variant]:
    """Invert a formatting instruction and its pattern; the expected value follows."""

    if case.boundary:
        return []
    variants: list[Variant] = []
    for item in spec.negations:
        oracle = case.oracle(item.field)
        if oracle is None:
            continue
        sentences = _sentence_texts(spec)
        index = int(item.sentence_id[1:]) - 1
        sentences[index] = item.replacement_sentence
        expected = tuple(
            _transform_oracle(oracle, item.value_transform) if oracle.field == item.field else oracle
            for oracle in case.expected
        )
        fields = _base_fields(spec, case)
        fields.update(
            family=Family.NEGATION,
            form_schema=_schema_for(spec, spec.field_order, {item.field: item.replacement_pattern}),
            instructions=_instructions(spec, sentences),
            expected=expected,
            held_fixed="document, every other field, and the field's position and type",
            controlled_difference=(
                f"sentence {item.sentence_id} replaced by {item.replacement_sentence!r} and the "
                f"{item.field} pattern replaced by {item.replacement_pattern!r}; oracle re-expressed "
                f"by {item.value_transform}"
            ),
        )
        variants.append(make_variant(**fields))
    return variants


def rival_substitution(spec: TaskSpec, case: Case) -> list[Variant]:
    """Append one rival disambiguation rule at a time; the oracle follows the rule."""

    variants: list[Variant] = []
    ambiguity_by_field = {ambiguity.field: ambiguity for ambiguity in spec.ambiguities}
    for rival in case.rival_expected:
        ambiguity = ambiguity_by_field[rival.field]
        rule = next(item for item in ambiguity.rivals if item.label == rival.label)
        sentences = _sentence_texts(spec) + [rule.instruction]
        expected = tuple(rival.oracle if oracle.field == rival.field else oracle for oracle in case.expected)
        if rival.field not in {oracle.field for oracle in case.expected}:
            expected = expected + (rival.oracle,)
        fields = _base_fields(spec, case)
        fields.update(
            family=Family.RIVAL_SUBSTITUTION,
            instructions=_instructions(spec, sentences),
            expected=expected,
            rival_label=rival.label,
            held_fixed="document, schema, and every original instruction sentence",
            controlled_difference=(
                f"rival reading {rival.label!r} of {rival.field} appended as sentence "
                f"S{len(sentences)}: {rule.instruction!r}; question: {ambiguity.question}"
            ),
        )
        variants.append(make_variant(**fields))
    return variants


def semantic_role_twin(spec: TaskSpec, case: Case) -> list[Variant]:
    """Exchange the positions of two role-bearing labels; values must follow labels."""

    if case.boundary:
        return []
    variants: list[Variant] = []
    for first, second in spec.twins:
        order = list(spec.field_order)
        i, j = order.index(first), order.index(second)
        order[i], order[j] = order[j], order[i]
        sentences = _sentence_texts(spec)
        first_index = next(k for k, sentence in enumerate(spec.sentences) if sentence.primary_field == first)
        second_index = next(k for k, sentence in enumerate(spec.sentences) if sentence.primary_field == second)
        sentences[first_index], sentences[second_index] = sentences[second_index], sentences[first_index]
        fields = _base_fields(spec, case)
        fields.update(
            family=Family.SEMANTIC_ROLE_TWIN,
            form_schema=_schema_for(spec, tuple(order)),
            field_order=tuple(order),
            instructions=_instructions(spec, sentences),
            held_fixed="labels, descriptions, document, and oracles; only positions move",
            controlled_difference=(
                f"labels {first} and {second} exchange positions in the schema property order "
                f"and their sentences exchange positions in the instructions"
            ),
        )
        variants.append(make_variant(**fields))
    return variants


def substrate_swap(spec: TaskSpec, case: Case) -> list[Variant]:
    """Re-render the same facts on another substrate; the oracle is unchanged."""

    if case.boundary:
        return []
    variants: list[Variant] = []
    for rendering in ("prose", "table", "email"):
        if rendering == case.rendering or rendering not in case.renderings:
            continue
        fields = _base_fields(spec, case, document=case.renderings[rendering])
        fields.update(
            family=Family.SUBSTRATE_SWAP,
            substrate=rendering,
            held_fixed="facts, schema, instructions, and oracles",
            controlled_difference=f"document re-rendered as {rendering} instead of {case.rendering}",
        )
        variants.append(make_variant(**fields))
    return variants


def boundary_shift(spec: TaskSpec, case: Case) -> list[Variant]:
    """Select boundary cases unchanged; the case's own oracle applies."""

    if not case.boundary:
        return []
    fields = _base_fields(spec, case)
    fields.update(
        family=Family.BOUNDARY_SHIFT,
        held_fixed=case.held_fixed,
        controlled_difference=case.notes or "boundary condition declared by the corpus",
    )
    return [make_variant(**fields)]


def import_dependency(spec: TaskSpec, case: Case) -> list[Variant]:
    """Remove one load-bearing sentence; record dependence rather than pass/fail."""

    if case.boundary:
        return []
    variants: list[Variant] = []
    for sentence_id in spec.load_bearing:
        index = int(sentence_id[1:]) - 1
        sentences = [sentence.text for k, sentence in enumerate(spec.sentences) if k != index]
        fields = _base_fields(spec, case)
        fields.update(
            family=Family.IMPORT_DEPENDENCY,
            instructions=_instructions(spec, sentences),
            expectation_kind=ExpectationKind.RECORD_DEPENDENCE,
            removed_sentence_id=sentence_id,
            held_fixed="document, schema, and every other instruction sentence",
            controlled_difference=(
                f"load-bearing sentence {sentence_id} removed: {spec.sentences[index].text!r}; "
                "dependence is evidence about the instruction, not the model"
            ),
        )
        variants.append(make_variant(**fields))
    return variants


def _corrupt(reference: tuple[tuple[str, Scalar], ...], control: Any, case_id: str) -> tuple[tuple[str, Scalar], ...]:
    values = dict(reference)
    if control.kind == "none":
        return reference
    if control.kind == "swap_fields":
        first, second = control.fields
        if first not in values or second not in values:
            raise RecordError(f"control {control.control_id} swaps fields absent from {case_id} reference output")
        values[first], values[second] = values[second], values[first]
        return tuple(values.items())
    if control.kind == "drop_required":
        if control.field not in values:
            raise RecordError(f"control {control.control_id} drops a field absent from {case_id} reference output")
        del values[control.field]
        return tuple(values.items())
    values[control.key] = control.value
    return tuple(values.items())


def non_vacuity(spec: TaskSpec, case: Case) -> list[Variant]:
    """Model-free controls: the oracle must reject corrupted and accept correct output."""

    if case.reference_output is None:
        return []
    variants: list[Variant] = []
    for control in spec.controls:
        output = _corrupt(case.reference_output, control, case.case_id)
        fields = _base_fields(spec, case)
        fields.update(
            family=Family.NON_VACUITY,
            expectation_kind=ExpectationKind.CONTROL_ACCEPT if control.kind == "none" else ExpectationKind.CONTROL_REJECT,
            control_id=control.control_id,
            control_output=output,
            model_call=False,
            held_fixed="schema, instructions, document, and oracles; no model is called",
            controlled_difference=(
                f"reference output corrupted by {control.kind}"
                + (f" {control.to_dict()}" if control.kind != "none" else "; uncorrupted reference must be accepted")
            ),
        )
        variants.append(make_variant(**fields))
    return variants


def round_trip(spec: TaskSpec, case: Case) -> list[Variant]:
    """Plan a second pass over the model's own baseline output rendered as prose."""

    if case.boundary:
        return []
    base = baseline(spec, case)[0]
    fields = _base_fields(spec, case)
    fields.update(
        family=Family.ROUND_TRIP,
        input_document=None,
        expected=(),
        expectation_kind=ExpectationKind.ROUND_TRIP,
        substrate="prose",
        round_trip_of=base.variant_id,
        held_fixed="schema and instructions; the document is the model's baseline output re-rendered",
        controlled_difference="document replaced by a fixed prose rendering of the baseline output; output must be identical",
    )
    return [make_variant(**fields)]


FAMILY_GENERATORS: Mapping[Family, Callable[[TaskSpec, Case], list[Variant]]] = {
    Family.BASELINE: baseline,
    Family.DELETION: deletion,
    Family.NEGATION: negation,
    Family.RIVAL_SUBSTITUTION: rival_substitution,
    Family.SEMANTIC_ROLE_TWIN: semantic_role_twin,
    Family.SUBSTRATE_SWAP: substrate_swap,
    Family.BOUNDARY_SHIFT: boundary_shift,
    Family.IMPORT_DEPENDENCY: import_dependency,
    Family.NON_VACUITY: non_vacuity,
    Family.ROUND_TRIP: round_trip,
}


ROUND_TRIP_HEADER = "The following details were transcribed from a completed form."


def render_round_trip_document(output: Mapping[str, Any], field_order: tuple[str, ...]) -> str:
    """Fixed prose template used by ROUND_TRIP; deterministic and label-preserving."""

    lines = [ROUND_TRIP_HEADER]
    for field in field_order:
        if field not in output:
            continue
        value = output[field]
        if type(value) is bool:
            rendered = "yes" if value else "no"
        elif type(value) is int or type(value) is str:
            rendered = str(value)
        else:
            raise RecordError(f"round trip cannot render non-scalar value for {field}")
        label = field.replace("_", " ").capitalize()
        lines.append(f"{label}: {rendered}")
    return "\n".join(lines) + "\n"


def materialize_round_trip(variant: Variant, baseline_output: Mapping[str, Any]) -> Variant:
    """Fill a planned ROUND_TRIP variant with the baseline output it depends on."""

    if variant.expectation_kind is not ExpectationKind.ROUND_TRIP:
        raise RecordError("only ROUND_TRIP variants can be materialised")
    document = render_round_trip_document(baseline_output, variant.field_order)
    expected: list[Oracle] = []
    for field in variant.field_order:
        if field in baseline_output:
            expected.append(
                Oracle(
                    field=field,
                    kind="exact",
                    value=scalar(baseline_output[field], f"baseline output {field}"),
                    values=None,
                    pattern=None,
                    oracle_status=OracleStatus.PROJECT_IMPORT_PROVISIONAL.value,
                    rationale="derived from the model's own baseline output; tests stability under re-rendering, not correctness",
                )
            )
        else:
            expected.append(
                Oracle(
                    field=field,
                    kind="absent",
                    value=None,
                    values=None,
                    pattern=None,
                    oracle_status=OracleStatus.PROJECT_IMPORT_PROVISIONAL.value,
                    rationale="absent from the model's own baseline output; tests stability under re-rendering, not correctness",
                )
            )
    return make_variant(
        family=Family.ROUND_TRIP,
        base_case_id=variant.base_case_id,
        form_schema=variant.form_schema,
        field_order=variant.field_order,
        instructions=variant.instructions,
        input_document=document,
        expected=tuple(expected),
        held_fixed=variant.held_fixed,
        controlled_difference=variant.controlled_difference,
        expectation_kind=ExpectationKind.ROUND_TRIP,
        substrate=variant.substrate,
        control_id=None,
        control_output=None,
        model_call=True,
        round_trip_of=variant.round_trip_of,
        rival_label=None,
        removed_sentence_id=None,
    )


@dataclass(frozen=True)
class Plan:
    plan_id: str
    pilot_id: str
    corpus_sha256: str
    variants: tuple[Variant, ...]
    counts: tuple[tuple[str, int], ...]

    def variant(self, variant_id: str) -> Variant:
        for variant in self.variants:
            if variant.variant_id == variant_id:
                return variant
        raise RecordError(f"unknown variant {variant_id!r}")

    def to_dict(self) -> dict[str, object]:
        return {
            "plan_id": self.plan_id,
            "pilot_id": self.pilot_id,
            "corpus_sha256": self.corpus_sha256,
            "counts": [{"family": family, "count": count} for family, count in self.counts],
            "variant_ids": [variant.variant_id for variant in self.variants],
        }


def plan(spec: TaskSpec, corpus: Corpus) -> Plan:
    """Enumerate every variant deterministically and content-address the plan."""

    variants: list[Variant] = []
    counts: list[tuple[str, int]] = []
    for family in Family:
        generator = FAMILY_GENERATORS[family]
        produced: list[Variant] = []
        for case in corpus.cases:
            produced.extend(generator(spec, case))
        counts.append((family.value, len(produced)))
        variants.extend(produced)
    ids = [variant.variant_id for variant in variants]
    if len(ids) != len(set(ids)):
        raise RecordError("plan produced duplicate variants; families must differ in content")
    plan_id = content_id(
        PLAN_DOMAIN,
        {
            "pilot_id": spec.pilot_id,
            "source_bindings": spec.bindings_dict(),
            "corpus_sha256": corpus.sha256,
            "variant_ids": ids,
        },
    )
    return Plan(plan_id=plan_id, pilot_id=spec.pilot_id, corpus_sha256=corpus.sha256, variants=tuple(variants), counts=tuple(counts))
