"""Canonical hashing for the integer/string-only CR-EIB record profile."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .errors import RecordError


def _validate_profile(value: Any, location: str = "$") -> None:
    if value is None or isinstance(value, (str, bool)):
        return
    if type(value) is int:
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_profile(item, f"{location}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise RecordError(f"non-string object key at {location}")
            _validate_profile(item, f"{location}.{key}")
        return
    raise RecordError(f"value outside canonical profile at {location}: {type(value).__name__}")


def canonical_bytes(value: Any) -> bytes:
    """Return deterministic UTF-8 JSON for the CR-EIB no-float profile."""
    _validate_profile(value)
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def domain_digest(domain: str, value: Any) -> str:
    framed = domain.encode("ascii") + b"\0" + canonical_bytes(value)
    return "sha256:" + hashlib.sha256(framed).hexdigest()


def bytes_digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
