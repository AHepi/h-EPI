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


def build_user_prompt(variant: Variant) -> str:
    if variant.input_document is None:
        raise RecordError(f"variant {variant.variant_id} has no document; materialise it first")
    return (
        "## Instructions\n\n"
        + variant.instructions
        + "\n## Form schema (JSON Schema draft 2020-12)\n\n"
        + render_schema_for_prompt(variant.form_schema, variant.field_order)
        + "\n\n## Case document\n\n<<<DOCUMENT\n"
        + variant.input_document
        + ("\n" if not variant.input_document.endswith("\n") else "")
        + "DOCUMENT>>>\n"
    )


def build_chat_request(variant: Variant, *, model: str, endpoint: Endpoint) -> ChatRequest:
    return ChatRequest(
        model=model,
        system=SYSTEM_PROMPT,
        user=build_user_prompt(variant),
        format_schema=ordered_form_schema(variant.form_schema, variant.field_order),
        options={"temperature": endpoint.temperature, "seed": endpoint.seed},
        think=endpoint.think,
    )
