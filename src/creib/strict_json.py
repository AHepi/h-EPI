"""Fail-closed JSON loading for normative bridge records."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .errors import RecordError


def _pairs_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise RecordError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise RecordError(f"non-finite JSON number is forbidden: {value}")


def _reject_floats(value: Any, location: str = "$") -> None:
    if isinstance(value, str):
        if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
            raise RecordError(f"Unicode surrogate code point is forbidden at {location}")
        return
    if isinstance(value, float):
        raise RecordError(f"floating-point value is forbidden at {location}")
    if isinstance(value, list):
        for index, item in enumerate(value):
            _reject_floats(item, f"{location}[{index}]")
    elif isinstance(value, dict):
        for key, item in value.items():
            if any(0xD800 <= ord(character) <= 0xDFFF for character in key):
                raise RecordError(f"Unicode surrogate code point is forbidden in key at {location}")
            _reject_floats(item, f"{location}.{key}")


def loads_strict(source: str) -> Any:
    try:
        value = json.loads(
            source,
            object_pairs_hook=_pairs_no_duplicates,
            parse_constant=_reject_constant,
        )
        _reject_floats(value)
    except RecordError:
        raise
    except RecursionError as exc:
        raise RecordError("JSON nesting exceeds the supported depth") from exc
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise RecordError(f"invalid JSON: {exc}") from exc
    return value


def load_strict(path: Path) -> Any:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise RecordError(f"cannot read {path}: {exc}") from exc
    try:
        source = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RecordError(f"JSON is not UTF-8: {path}") from exc
    return loads_strict(source)
