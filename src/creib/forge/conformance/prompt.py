"""Deterministic prompt construction for one variant.

The system prompt is deliberately minimal so that the numbered instructions
are the only place output-format requirements are stated; removing one of
them in IMPORT_DEPENDENCY is then not confounded by harness text.  The form
schema is rendered with its properties in the variant's declared field order
so that SEMANTIC_ROLE_TWIN position swaps are visible to the model.
"""

from __future__ import annotations

import json
from typing import Any

from creib.errors import RecordError

from creib.strict_json import loads_strict

from .executor import ChatRequest
from .families import Variant
from .spec import Endpoint


SYSTEM_PROMPT = (
    "You are completing a form from a case document. The numbered instructions, "
    "the form schema, and the case document follow."
)


_TOP_LEVEL_ORDER: tuple[str, ...] = ("$schema", "title", "description", "type", "additionalProperties", "required", "properties")


def _sorted_schema(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _sorted_schema(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_sorted_schema(item) for item in value]
    return value


def ordered_form_schema(form_schema: dict[str, Any], field_order: tuple[str, ...]) -> dict[str, Any]:
    """Deterministic key order: fixed top-level order, properties by field_order.

    The variant's schema may arrive in file order or in canonical (sorted)
    order after a record reload; both must render to the same prompt text so
    that request digests replay.
    """

    properties = form_schema["properties"]
    if set(properties) != set(field_order):
        raise RecordError("field_order does not cover the form schema properties")
    ordered: dict[str, Any] = {}
    remaining = sorted(key for key in form_schema if key not in _TOP_LEVEL_ORDER)
    for key in (*_TOP_LEVEL_ORDER, *remaining):
        if key not in form_schema:
            continue
        if key == "properties":
            ordered[key] = {field: _sorted_schema(properties[field]) for field in field_order}
        else:
            ordered[key] = _sorted_schema(form_schema[key])
    return ordered


def render_schema_for_prompt(form_schema: dict[str, Any], field_order: tuple[str, ...]) -> str:
    return json.dumps(ordered_form_schema(form_schema, field_order), ensure_ascii=False, indent=2, allow_nan=False)


CYCLE_REVISION_SENTENCE = (
    "Check the previous answer against the instructions, the form schema, and the case document. "
    "Correct any error and return the complete form again as a single JSON object and no other text; "
    "return the same value for any field that needs no change."
)


def render_previous_answer(variant: Variant) -> str:
    """The previous answer as shown in a cycle: declared fields in prompt order, then any other key sorted."""

    if variant.cycle_previous_output is None:
        raise RecordError(f"variant {variant.variant_id} is a cycle with no previous answer; materialise it first")
    previous = loads_strict(variant.cycle_previous_output)
    if not isinstance(previous, dict):
        raise RecordError("a cycle's previous answer must be a JSON object")
    order = [key for key in variant.prompt_field_order if key in previous]
    order += sorted(key for key in previous if key not in order)
    return json.dumps({key: previous[key] for key in order}, ensure_ascii=False, indent=2, allow_nan=False)


def render_cycle_section(variant: Variant) -> str:
    """The text a CYCLE variant appends after the document; deterministic from the variant alone."""

    parts = ["\n## Previous answer\n\nYour previous answer to this task was:\n\n```json\n" + render_previous_answer(variant) + "\n```\n"]
    if variant.cycle_criticism == "external":
        criticisms = variant.cycle_criticisms or ()
        if criticisms:
            lines = ["\n## Checks on the previous answer\n\nThe following automatic checks failed on the previous answer:\n"]
            for item in criticisms:
                lines.append(f"- `{item.field}`: {item.verdict}" + (f" ({item.detail})" if item.detail else ""))
            parts.append("\n".join(lines) + "\n")
        else:
            parts.append("\n## Checks on the previous answer\n\nNo automatic check failed on the previous answer.\n")
    parts.append("\n## Revision\n\n" + CYCLE_REVISION_SENTENCE + "\n")
    return "".join(parts)


def build_user_prompt(variant: Variant) -> str:
    if variant.input_document is None:
        raise RecordError(f"variant {variant.variant_id} has no document; materialise it first")
    prompt = (
        "## Instructions\n\n"
        + variant.prompt_instructions()
        + "\n## Form schema (JSON Schema draft 2020-12)\n\n"
        + render_schema_for_prompt(variant.prompt_form_schema(), variant.prompt_field_order)
        + "\n\n## Case document\n\n<<<DOCUMENT\n"
        + variant.input_document
        + ("\n" if not variant.input_document.endswith("\n") else "")
        + "DOCUMENT>>>\n"
    )
    if variant.cycle_index is not None:
        prompt += render_cycle_section(variant)
    return prompt


def build_chat_request(variant: Variant, *, model: str, endpoint: Endpoint) -> ChatRequest:
    return ChatRequest(
        model=model,
        system=SYSTEM_PROMPT,
        user=build_user_prompt(variant),
        format_schema=ordered_form_schema(variant.prompt_form_schema(), variant.prompt_field_order),
        options={"temperature": endpoint.temperature, "seed": endpoint.seed},
        think=endpoint.think,
        repeat_index=variant.repeat_index,
        variant_id=variant.variant_id,
    )
