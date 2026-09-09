"""The format grammar: written as data, compiled once before any call.

Five checks cover everything the request lists — keywords that must appear,
section markers, a regular expression, a line shape, a JSON Schema fragment —
and ``all_of`` combines them. A specification is compiled at run start into
callables; a specification that cannot be compiled refuses the run there, so no
model is ever called under a format nobody could have satisfied.

Absent a specification the format is freeform: a field is checked only for
being present and non-empty.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Callable

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from creib.errors import RecordError
from creib.strict_json import loads_strict

from .common import MiniError, array_value, object_value, text

CHECK_KINDS: tuple[str, ...] = ("keywords", "sections", "regex", "line_shape", "json_schema")
LINE_SHAPE_SCOPES: tuple[str, ...] = ("every_line", "any_line")
FORMAT_FIELDS: tuple[str, ...] = ("body", "commitments")

_INVALID = "MINI_FORMAT_SPEC_INVALID"


@dataclass(frozen=True)
class CompiledCheck:
    """One compiled check.

    ``rendered`` is the check written out in full — the keyword list, the
    markers, the expression, the schema as text — and it is what the seat is
    shown, on the first attempt and on every retry. A seat that is only told
    its answer was the wrong shape, without being told the shape, is being set
    up to fail twice.
    """

    check: str
    describe: str
    rendered: str
    run: Callable[[str], str | None]


@dataclass(frozen=True)
class CompiledFormat:
    """The compiled format of one artifact kind, per field."""

    checks: dict[str, tuple[CompiledCheck, ...]]

    @property
    def freeform(self) -> bool:
        return not any(self.checks.values())

    def describe(self) -> tuple[str, ...]:
        """The compiled format in full, one entry per field and check."""

        return tuple(
            f"`{field}` {item.rendered}" for field in FORMAT_FIELDS for item in self.checks.get(field, ())
        )

    def failures(self, submission: dict[str, Any]) -> tuple[str, ...]:
        """Return one reason per failing check; empty means the format held."""

        reasons: list[str] = []
        for field in FORMAT_FIELDS:
            value = submission.get(field)
            if type(value) is not str:
                continue
            for item in self.checks.get(field, ()):
                reason = item.run(value)
                if reason is not None:
                    reasons.append(f"{field}: {reason}")
        return tuple(reasons)


FREEFORM = CompiledFormat(checks={field: () for field in FORMAT_FIELDS})


def _boolean(value: Any, where: str, default: bool) -> bool:
    if value is None:
        return default
    if type(value) is not bool:
        raise MiniError(_INVALID, f"{where} must be true or false")
    return value


def _string_list(value: Any, where: str) -> tuple[str, ...]:
    items = array_value(value, where, _INVALID)
    if not items:
        raise MiniError(_INVALID, f"{where} must not be empty")
    return tuple(text(item, f"{where}[{index}]", _INVALID) for index, item in enumerate(items))


def _compile_pattern(raw: Any, where: str) -> re.Pattern[str]:
    pattern = text(raw, where, _INVALID)
    try:
        return re.compile(pattern)
    except re.error as error:
        raise MiniError(_INVALID, f"{where} is not a usable expression: {error}") from error


def _keywords(spec: dict[str, Any], where: str) -> CompiledCheck:
    keywords = _string_list(spec.get("keywords"), f"{where}.keywords")
    case_sensitive = _boolean(spec.get("case_sensitive"), f"{where}.case_sensitive", True)

    def run(value: str) -> str | None:
        haystack = value if case_sensitive else value.casefold()
        for keyword in keywords:
            needle = keyword if case_sensitive else keyword.casefold()
            if needle not in haystack:
                return f"the word {keyword!r} does not appear"
        return None

    listed = "\n".join(f"  - {word}" for word in keywords)
    sensitivity = "exactly as written" if case_sensitive else "in any case"
    return CompiledCheck(
        "keywords",
        f"must contain {', '.join(repr(word) for word in keywords)}",
        f"must contain every one of these words, {sensitivity}:\n{listed}",
        run,
    )


def _sections(spec: dict[str, Any], where: str) -> CompiledCheck:
    markers = _string_list(spec.get("markers"), f"{where}.markers")

    def run(value: str) -> str | None:
        remaining = list(markers)
        for line in value.splitlines():
            if remaining and line.startswith(remaining[0]):
                remaining.pop(0)
        if remaining:
            return f"the section marker {remaining[0]!r} does not begin a line, in order"
        return None

    listed = "\n".join(f"  {index + 1}. {marker}" for index, marker in enumerate(markers))
    return CompiledCheck(
        "sections",
        f"must carry the section markers {list(markers)} in order",
        f"must begin lines with these markers, in this order:\n{listed}",
        run,
    )


def _regex(spec: dict[str, Any], where: str) -> CompiledCheck:
    compiled = _compile_pattern(spec.get("pattern"), f"{where}.pattern")

    def run(value: str) -> str | None:
        if compiled.search(value) is None:
            return f"nothing in it matches {compiled.pattern!r}"
        return None

    return CompiledCheck(
        "regex",
        f"must match {compiled.pattern!r}",
        f"must contain something matching this expression:\n  {compiled.pattern}",
        run,
    )


def _line_shape(spec: dict[str, Any], where: str) -> CompiledCheck:
    compiled = _compile_pattern(spec.get("pattern"), f"{where}.pattern")
    scope = spec.get("applies_to", "every_line")
    if scope not in LINE_SHAPE_SCOPES:
        raise MiniError(_INVALID, f"{where}.applies_to must be one of {list(LINE_SHAPE_SCOPES)}, got {scope!r}")

    def run(value: str) -> str | None:
        lines = [line for line in value.splitlines() if line.strip()]
        if not lines:
            return "it carries no line to shape"
        matched = [line for line in lines if compiled.search(line) is not None]
        if scope == "every_line" and len(matched) != len(lines):
            return f"a line does not match {compiled.pattern!r}"
        if scope == "any_line" and not matched:
            return f"no line matches {compiled.pattern!r}"
        return None

    every = "every non-blank line" if scope == "every_line" else "at least one line"
    return CompiledCheck(
        "line_shape",
        f"{scope}: must match {compiled.pattern!r}",
        f"{every} must match this expression:\n  {compiled.pattern}",
        run,
    )


def _reject_references(node: Any, where: str) -> None:
    """Refuse ``$ref`` anywhere in a fragment: nothing may be fetched."""

    if type(node) is dict:
        if "$ref" in node:
            raise MiniError(_INVALID, f"{where} may not use $ref; a fragment must be self-contained")
        for key, value in node.items():
            _reject_references(value, f"{where}.{key}")
    elif type(node) is list:
        for index, value in enumerate(node):
            _reject_references(value, f"{where}[{index}]")


def _json_schema(spec: dict[str, Any], where: str) -> CompiledCheck:
    fragment = object_value(spec.get("schema"), f"{where}.schema", _INVALID)
    _reject_references(fragment, f"{where}.schema")
    try:
        Draft202012Validator.check_schema(fragment)
    except SchemaError as error:
        raise MiniError(_INVALID, f"{where}.schema is not a usable JSON Schema: {error.message}") from error
    validator = Draft202012Validator(fragment)

    def run(value: str) -> str | None:
        try:
            parsed = loads_strict(value)
        except RecordError as error:
            return f"it is not readable as JSON: {error}"
        errors = sorted(validator.iter_errors(parsed), key=lambda item: (list(item.absolute_path), item.message))
        if errors:
            return f"it does not fit the declared shape: {errors[0].message}"
        return None

    as_text = json.dumps(fragment, ensure_ascii=False, sort_keys=True, indent=2)
    return CompiledCheck(
        "json_schema",
        "must be JSON fitting the declared shape",
        f"must be JSON fitting exactly this schema:\n{as_text}",
        run,
    )


_COMPILERS: dict[str, Callable[[dict[str, Any], str], CompiledCheck]] = {
    "keywords": _keywords,
    "sections": _sections,
    "regex": _regex,
    "line_shape": _line_shape,
    "json_schema": _json_schema,
}


def compile_check(spec: Any, where: str) -> CompiledCheck:
    entry = object_value(spec, where, _INVALID)
    kind = text(entry.get("check"), f"{where}.check", _INVALID)
    if kind not in _COMPILERS:
        raise MiniError(_INVALID, f"{where}.check must be one of {list(CHECK_KINDS)}, got {kind!r}")
    return _COMPILERS[kind](entry, where)


def compile_format_spec(spec: Any, where: str) -> CompiledFormat:
    """Compile one kind's format specification; ``None`` compiles to freeform."""

    if spec is None:
        return FREEFORM
    entry = object_value(spec, where, _INVALID)
    checks: dict[str, tuple[CompiledCheck, ...]] = {}
    for field in FORMAT_FIELDS:
        raw = entry.get(field)
        if raw is None:
            checks[field] = ()
            continue
        block = object_value(raw, f"{where}.{field}", _INVALID)
        items = array_value(block.get("all_of"), f"{where}.{field}.all_of", _INVALID)
        checks[field] = tuple(
            compile_check(item, f"{where}.{field}.all_of[{index}]") for index, item in enumerate(items)
        )
    return CompiledFormat(checks=checks)
