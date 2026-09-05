"""Task specification for one form-filling conformance pilot.

A pilot is configured, not coded: the form schema, the numbered instructions,
the corpus, the model list, and every family-specific setting come from
``pilot.json`` and the files it references.  Loading content-binds each file
by SHA-256 and derives one obligation per form field from the form schema and
the instruction sentence that mentions it.

This module does not claim that the instructions are complete, that the
obligations are the right reading of the form, or that any model meets them.
An obligation without a source sentence is flagged ``unsourced``: it is an
import from the form schema, not a requirement stated in the instructions.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from creib.errors import RecordError
from creib.forge.models import NON_INDUCTIVE_LIMIT
from creib.strict_json import loads_strict

from .common import (
    CONFIG_SCHEMA_NAME,
    CONFIG_SCHEMA_VERSION,
    array_value,
    decode_utf8,
    field_name,
    file_binding,
    form_schema_profile_validator,
    frozen_mapping_to_dict,
    identifier,
    integer,
    model_id,
    object_value,
    optional_boolean,
    scalar,
    schema_errors,
    sentence_id,
    text,
    unique_texts,
    validate_instance,
)


ENDPOINT_KIND = "ollama-chat"
VALUE_TRANSFORMS: tuple[str, ...] = ("iso_date_to_dmy", "e164_au_to_national_spaced")
CORRUPTION_KINDS: tuple[str, ...] = ("none", "swap_fields", "drop_required", "extra_key")
_CONSTRAINT_KEYS: tuple[str, ...] = ("pattern", "enum", "maxLength", "minLength", "format")
_NUMBERED_LINE = re.compile(r"^([1-9][0-9]{0,3})\. (\S.*)$")


@dataclass(frozen=True)
class Binding:
    """One content-bound source file."""

    path: str
    sha256: str

    def to_dict(self) -> dict[str, object]:
        return {"path": self.path, "sha256": self.sha256}


@dataclass(frozen=True)
class Endpoint:
    kind: str
    base_url: str
    timeout_seconds: int
    temperature: int
    seed: int
    think: bool | None

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "base_url": self.base_url,
            "timeout_seconds": self.timeout_seconds,
            "options": {"temperature": self.temperature, "seed": self.seed},
            "think": self.think,
        }


@dataclass(frozen=True)
class Charter:
    purpose: str
    output: str
    scope_in: tuple[str, ...]
    scope_out: tuple[str, ...]
    non_inductive_constitution: str = NON_INDUCTIVE_LIMIT

    def to_dict(self) -> dict[str, object]:
        return {
            "purpose": self.purpose,
            "output": self.output,
            "scope_in": list(self.scope_in),
            "scope_out": list(self.scope_out),
            "non_inductive_constitution": self.non_inductive_constitution,
        }


@dataclass(frozen=True)
class Sentence:
    """One numbered instruction sentence and the fields it mentions."""

    sentence_id: str
    text: str
    mentions: tuple[str, ...]
    primary_field: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "sentence_id": self.sentence_id,
            "text": self.text,
            "mentions": list(self.mentions),
            "primary_field": self.primary_field,
        }


@dataclass(frozen=True)
class RivalRule:
    label: str
    instruction: str

    def to_dict(self) -> dict[str, object]:
        return {"label": self.label, "instruction": self.instruction}


@dataclass(frozen=True)
class Ambiguity:
    """Declared rival readings of one field; none of them is endorsed."""

    field: str
    question: str
    rivals: tuple[RivalRule, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "field": self.field,
            "question": self.question,
            "rivals": [rival.to_dict() for rival in self.rivals],
        }


@dataclass(frozen=True)
class Obligation:
    field: str
    json_type: str
    required: bool
    constraint: dict[str, Any] | None
    source_claim: str | None
    source_sentence_ids: tuple[str, ...]
    unsourced: bool
    ambiguity: Ambiguity | None

    def to_dict(self) -> dict[str, object]:
        return {
            "field": self.field,
            "json_type": self.json_type,
            "required": self.required,
            "constraint": None if self.constraint is None else dict(self.constraint),
            "source_claim": self.source_claim,
            "source_sentence_ids": list(self.source_sentence_ids),
            "unsourced": self.unsourced,
            "ambiguity": None if self.ambiguity is None else self.ambiguity.to_dict(),
        }


@dataclass(frozen=True)
class Negation:
    field: str
    sentence_id: str
    replacement_sentence: str
    replacement_pattern: str
    value_transform: str


@dataclass(frozen=True)
class Control:
    """A model-free corruption template for the NON_VACUITY family."""

    control_id: str
    kind: str
    fields: tuple[str, ...]
    field: str | None
    key: str | None
    value: str | bool | int | None

    def to_dict(self) -> dict[str, object]:
        return {
            "control_id": self.control_id,
            "kind": self.kind,
            "fields": list(self.fields),
            "field": self.field,
            "key": self.key,
            "value": self.value,
        }


@dataclass(frozen=True)
class TaskSpec:
    """The content-bound task: form, instructions, obligations, models, endpoint."""

    pilot_id: str
    title: str
    form_schema: dict[str, Any]
    field_order: tuple[str, ...]
    instructions: str
    preamble: str
    sentences: tuple[Sentence, ...]
    obligations: tuple[Obligation, ...]
    models: tuple[str, ...]
    endpoint: Endpoint
    charter: Charter
    source_bindings: tuple[Binding, ...]
    load_bearing: tuple[str, ...]
    negations: tuple[Negation, ...]
    twins: tuple[tuple[str, str], ...]
    ambiguities: tuple[Ambiguity, ...]
    controls: tuple[Control, ...]
    refusal_phrases: tuple[str, ...]

    @property
    def required_fields(self) -> tuple[str, ...]:
        return tuple(obligation.field for obligation in self.obligations if obligation.required)

    def sentence(self, sentence_id_value: str) -> Sentence:
        for sentence in self.sentences:
            if sentence.sentence_id == sentence_id_value:
                return sentence
        raise RecordError(f"unknown instruction sentence {sentence_id_value!r}")

    def obligation(self, field: str) -> Obligation:
        for obligation in self.obligations:
            if obligation.field == field:
                return obligation
        raise RecordError(f"unknown form field {field!r}")

    def bindings_dict(self) -> list[dict[str, object]]:
        return [binding.to_dict() for binding in self.source_bindings]

    def to_dict(self) -> dict[str, object]:
        return {
            "pilot_id": self.pilot_id,
            "title": self.title,
            "form_schema": frozen_mapping_to_dict(self.form_schema),
            "field_order": list(self.field_order),
            "instructions": self.instructions,
            "sentences": [sentence.to_dict() for sentence in self.sentences],
            "obligations": [obligation.to_dict() for obligation in self.obligations],
            "models": list(self.models),
            "endpoint": self.endpoint.to_dict(),
            "charter": self.charter.to_dict(),
            "source_bindings": self.bindings_dict(),
            "load_bearing": list(self.load_bearing),
        }


@dataclass(frozen=True)
class PilotConfig:
    path: Path
    directory: Path
    spec: TaskSpec
    corpus_path: Path


def parse_instructions(source: str) -> tuple[str, tuple[str, ...]]:
    """Split instructions into a preamble and consecutively numbered sentences.

    The file must round-trip through :func:`render_instructions` so that the
    baseline variant's instruction text is byte-identical to the bound file.
    """

    lines = source.split("\n")
    preamble_lines: list[str] = []
    sentences: list[str] = []
    seen_numbered = False
    for line in lines:
        match = _NUMBERED_LINE.match(line)
        if match is None:
            if seen_numbered:
                if line == "":
                    continue
                raise RecordError(
                    "instructions must not contain unnumbered text after the first "
                    f"numbered sentence: {line!r}"
                )
            preamble_lines.append(line)
            continue
        seen_numbered = True
        number = int(match.group(1))
        if number != len(sentences) + 1:
            raise RecordError(
                f"instruction sentences must be numbered consecutively; found {number}"
            )
        sentences.append(match.group(2).rstrip())
    if not sentences:
        raise RecordError("instructions must contain at least one numbered sentence")
    preamble = "\n".join(preamble_lines).strip("\n")
    rendered = render_instructions(preamble, tuple(sentences))
    if rendered != source:
        raise RecordError(
            "instructions.md must be in canonical form: optional preamble, one blank "
            "line, consecutively numbered sentences, one trailing newline"
        )
    return preamble, tuple(sentences)


def render_instructions(preamble: str, sentences: tuple[str, ...]) -> str:
    body = "\n".join(f"{index}. {sentence}" for index, sentence in enumerate(sentences, start=1))
    if preamble:
        return preamble + "\n\n" + body + "\n"
    return body + "\n"


def mentioned_fields(sentence: str, fields: tuple[str, ...]) -> tuple[str, ...]:
    """Fields whose name appears in the sentence as a whole token, in text order."""

    positions: list[tuple[int, str]] = []
    for field in fields:
        match = re.search(r"(?<![A-Za-z0-9_])" + re.escape(field) + r"(?![A-Za-z0-9_])", sentence)
        if match is not None:
            positions.append((match.start(), field))
    return tuple(field for _, field in sorted(positions))


def validate_form_schema(raw: Any, where: str) -> tuple[dict[str, Any], tuple[str, ...]]:
    """Check the form schema is a valid, closed Draft 2020-12 object schema."""

    schema = object_value(raw, where)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise RecordError(f"{where} is not a valid JSON Schema: {exc.message}") from exc
    errors = schema_errors(form_schema_profile_validator(), schema)
    if errors:
        raise RecordError(f"{where} violates the pilot form profile: " + "; ".join(errors[:5]))
    properties = object_value(schema.get("properties"), f"{where}.properties")
    field_order = tuple(field_name(key, f"{where}.properties key") for key in properties)
    required = array_value(schema.get("required"), f"{where}.required")
    for item in required:
        if item not in properties:
            raise RecordError(f"{where}.required names unknown field {item!r}")
    return schema, field_order


def endpoint_from_dict(raw: dict[str, Any]) -> Endpoint:
    raw = object_value(raw, "endpoint")
    options = object_value(raw["options"], "endpoint.options")
    if raw["kind"] != ENDPOINT_KIND:
        raise RecordError("endpoint.kind must be ollama-chat")
    return Endpoint(
        kind=ENDPOINT_KIND,
        base_url=text(raw["base_url"], "endpoint.base_url").rstrip("/"),
        timeout_seconds=integer(raw["timeout_seconds"], "endpoint.timeout_seconds", minimum=1),
        temperature=integer(options["temperature"], "endpoint.options.temperature"),
        seed=integer(options["seed"], "endpoint.options.seed"),
        think=optional_boolean(raw["think"], "endpoint.think"),
    )


def _charter(raw: dict[str, Any]) -> Charter:
    return Charter(
        purpose=text(raw["purpose"], "charter.purpose"),
        output=text(raw["output"], "charter.output"),
        scope_in=unique_texts(raw["scope_in"], "charter.scope_in"),
        scope_out=unique_texts(raw["scope_out"], "charter.scope_out"),
    )


def _controls(raw: list[Any], field_order: tuple[str, ...], required: tuple[str, ...]) -> tuple[Control, ...]:
    controls: list[Control] = []
    for index, item in enumerate(raw):
        where = f"controls[{index}]"
        entry = object_value(item, where)
        corruption = object_value(entry["corruption"], f"{where}.corruption")
        kind = text(corruption["kind"], f"{where}.corruption.kind")
        if kind not in CORRUPTION_KINDS:
            raise RecordError(f"{where}.corruption.kind is not a known corruption")
        fields: tuple[str, ...] = ()
        field: str | None = None
        key: str | None = None
        value: str | bool | int | None = None
        if kind == "swap_fields":
            fields = tuple(field_name(f, f"{where}.corruption.fields") for f in corruption["fields"])
            for f in fields:
                if f not in field_order:
                    raise RecordError(f"{where} swaps unknown field {f!r}")
        elif kind == "drop_required":
            field = field_name(corruption["field"], f"{where}.corruption.field")
            if field not in required:
                raise RecordError(f"{where} drops {field!r}, which is not a required field")
        elif kind == "extra_key":
            key = field_name(corruption["key"], f"{where}.corruption.key")
            if key in field_order:
                raise RecordError(f"{where} extra key {key!r} is already a form field")
            value = scalar(corruption["value"], f"{where}.corruption.value")
        controls.append(
            Control(
                control_id=identifier(entry["control_id"], f"{where}.control_id"),
                kind=kind,
                fields=fields,
                field=field,
                key=key,
                value=value,
            )
        )
    ids = [control.control_id for control in controls]
    if len(ids) != len(set(ids)):
        raise RecordError("controls must have unique control_id values")
    if not any(control.kind == "none" for control in controls):
        raise RecordError("controls must include one uncorrupted reference (kind none)")
    if not any(control.kind != "none" for control in controls):
        raise RecordError("controls must include at least one corruption")
    return tuple(controls)


def build_task_spec(
    *,
    raw_config: dict[str, Any],
    form_schema_raw: Any,
    instructions_text: str,
    bindings: tuple[Binding, ...],
) -> TaskSpec:
    """Derive the task specification from already-loaded, already-bound inputs."""

    validate_instance(raw_config, CONFIG_SCHEMA_NAME)
    if raw_config["schema_version"] != CONFIG_SCHEMA_VERSION:
        raise RecordError("pilot config schema_version mismatch")
    form_schema, field_order = validate_form_schema(form_schema_raw, "form_schema")
    required = tuple(field for field in field_order if field in form_schema["required"])
    preamble, sentence_texts = parse_instructions(instructions_text)
    sentences: list[Sentence] = []
    for index, sentence_text in enumerate(sentence_texts, start=1):
        mentions = mentioned_fields(sentence_text, field_order)
        sentences.append(
            Sentence(
                sentence_id=f"S{index}",
                text=sentence_text,
                mentions=mentions,
                primary_field=mentions[0] if mentions else None,
            )
        )
    sentence_ids = {sentence.sentence_id for sentence in sentences}

    ambiguities: list[Ambiguity] = []
    for index, item in enumerate(array_value(raw_config["ambiguity"], "ambiguity")):
        where = f"ambiguity[{index}]"
        entry = object_value(item, where)
        field = field_name(entry["field"], f"{where}.field")
        if field not in field_order:
            raise RecordError(f"{where} names unknown field {field!r}")
        rivals = tuple(
            RivalRule(
                label=identifier(rival["label"], f"{where}.rivals[{rival_index}].label"),
                instruction=text(rival["instruction"], f"{where}.rivals[{rival_index}].instruction"),
            )
            for rival_index, rival in enumerate(array_value(entry["rivals"], f"{where}.rivals"))
        )
        labels = [rival.label for rival in rivals]
        if len(labels) != len(set(labels)):
            raise RecordError(f"{where} rival labels must be unique")
        if len({rival.instruction for rival in rivals}) != len(rivals):
            raise RecordError(f"{where} rival instructions must differ")
        ambiguities.append(Ambiguity(field=field, question=text(entry["question"], f"{where}.question"), rivals=rivals))
    ambiguity_fields = [ambiguity.field for ambiguity in ambiguities]
    if len(ambiguity_fields) != len(set(ambiguity_fields)):
        raise RecordError("ambiguity declares the same field twice")
    ambiguity_by_field = {ambiguity.field: ambiguity for ambiguity in ambiguities}

    obligations: list[Obligation] = []
    for field in field_order:
        property_schema = object_value(form_schema["properties"][field], f"form_schema.properties.{field}")
        constraint = {key: property_schema[key] for key in _CONSTRAINT_KEYS if key in property_schema}
        sources = tuple(sentence for sentence in sentences if field in sentence.mentions)
        obligations.append(
            Obligation(
                field=field,
                json_type=text(property_schema["type"], f"form_schema.properties.{field}.type"),
                required=field in required,
                constraint=constraint or None,
                source_claim=sources[0].text if sources else None,
                source_sentence_ids=tuple(sentence.sentence_id for sentence in sources),
                unsourced=not sources,
                ambiguity=ambiguity_by_field.get(field),
            )
        )

    load_bearing = tuple(
        sentence_id(item, f"load_bearing[{index}]")
        for index, item in enumerate(array_value(raw_config["load_bearing"], "load_bearing"))
    )
    for item in load_bearing:
        if item not in sentence_ids:
            raise RecordError(f"load_bearing names unknown sentence {item!r}")
    if len(load_bearing) != len(set(load_bearing)):
        raise RecordError("load_bearing must not repeat a sentence")

    negations: list[Negation] = []
    for index, item in enumerate(array_value(raw_config["negations"], "negations")):
        where = f"negations[{index}]"
        entry = object_value(item, where)
        field = field_name(entry["field"], f"{where}.field")
        if field not in field_order:
            raise RecordError(f"{where} names unknown field {field!r}")
        target = sentence_id(entry["sentence_id"], f"{where}.sentence_id")
        if target not in sentence_ids:
            raise RecordError(f"{where} names unknown sentence {target!r}")
        primary = next(sentence for sentence in sentences if sentence.sentence_id == target).primary_field
        if primary != field:
            raise RecordError(f"{where} sentence {target} is not primarily about {field!r}")
        transform = text(entry["value_transform"], f"{where}.value_transform")
        if transform not in VALUE_TRANSFORMS:
            raise RecordError(f"{where}.value_transform is not a known transform")
        replacement_pattern = text(entry["replacement_pattern"], f"{where}.replacement_pattern")
        try:
            re.compile(replacement_pattern)
        except re.error as exc:
            raise RecordError(f"{where}.replacement_pattern is not a valid regex: {exc}") from exc
        negations.append(
            Negation(
                field=field,
                sentence_id=target,
                replacement_sentence=text(entry["replacement_sentence"], f"{where}.replacement_sentence"),
                replacement_pattern=replacement_pattern,
                value_transform=transform,
            )
        )
    negation_fields = [negation.field for negation in negations]
    if len(negation_fields) != len(set(negation_fields)):
        raise RecordError("negations declare the same field twice")

    twins: list[tuple[str, str]] = []
    for index, item in enumerate(array_value(raw_config["twins"], "twins")):
        where = f"twins[{index}]"
        pair = array_value(item, where)
        if len(pair) != 2:
            raise RecordError(f"{where} must name exactly two fields")
        first = field_name(pair[0], f"{where}[0]")
        second = field_name(pair[1], f"{where}[1]")
        if first == second:
            raise RecordError(f"{where} must name two different fields")
        for field in (first, second):
            if field not in field_order:
                raise RecordError(f"{where} names unknown field {field!r}")
            if not any(sentence.primary_field == field for sentence in sentences):
                raise RecordError(f"{where} field {field!r} has no primary instruction sentence")
        twins.append((first, second))

    controls = _controls(array_value(raw_config["controls"], "controls"), field_order, required)
    refusal_phrases = unique_texts(raw_config["refusal_phrases"], "refusal_phrases")
    models = tuple(model_id(item, f"models[{index}]") for index, item in enumerate(raw_config["models"]))
    if len(models) != len(set(models)):
        raise RecordError("models must be unique")

    return TaskSpec(
        pilot_id=identifier(raw_config["pilot_id"], "pilot_id"),
        title=text(raw_config["title"], "title"),
        form_schema=form_schema,
        field_order=field_order,
        instructions=instructions_text,
        preamble=preamble,
        sentences=tuple(sentences),
        obligations=tuple(obligations),
        models=models,
        endpoint=endpoint_from_dict(object_value(raw_config["endpoint"], "endpoint")),
        charter=_charter(object_value(raw_config["charter"], "charter")),
        source_bindings=bindings,
        load_bearing=load_bearing,
        negations=tuple(negations),
        twins=tuple(twins),
        ambiguities=tuple(ambiguities),
        controls=controls,
        refusal_phrases=refusal_phrases,
    )


def load_pilot_config(path: Path) -> PilotConfig:
    """Strict-load ``pilot.json``, bind every referenced file, and build the spec."""

    if not isinstance(path, Path):
        raise TypeError("path must be pathlib.Path")
    directory = path.resolve().parent
    config_relative, config_sha256, config_raw = file_binding(path.resolve(), directory)
    raw_config = object_value(loads_strict(decode_utf8(config_raw, str(path))), "pilot config")
    validate_instance(raw_config, CONFIG_SCHEMA_NAME)
    bindings: list[Binding] = [Binding(config_relative, config_sha256)]

    def bound(key: str) -> tuple[Path, bytes]:
        relative = text(raw_config[key], key)
        target = (directory / relative).resolve()
        rel, sha256, raw = file_binding(target, directory)
        bindings.append(Binding(rel, sha256))
        return target, raw

    form_path, form_raw = bound("form_schema")
    form_schema_raw = loads_strict(decode_utf8(form_raw, str(form_path)))
    instructions_path, instructions_raw = bound("instructions")
    instructions_text = decode_utf8(instructions_raw, str(instructions_path))
    corpus_path, _ = bound("corpus")
    spec = build_task_spec(
        raw_config=raw_config,
        form_schema_raw=form_schema_raw,
        instructions_text=instructions_text,
        bindings=tuple(bindings),
    )
    return PilotConfig(path=path, directory=directory, spec=spec, corpus_path=corpus_path)
