"""Shared fail-closed helpers for the task-conformance pilot.

Everything in this package is content-addressed, float-free, and published
without overwriting.  These helpers exist so that no module in the package
needs to reach into other forge modules for utilities.  Nothing here assigns
truth, confirmation, or a score to any model output.
"""

from __future__ import annotations

from functools import lru_cache
import hashlib
import os
from pathlib import Path
import re
from typing import Any, Mapping

from jsonschema import Draft202012Validator

from creib.canonical import bytes_digest, canonical_bytes
from creib.errors import RecordError
from creib.forge.schema_validation import LocalSchemaCatalog, load_local_schema_catalog


REPO_ROOT = Path(__file__).resolve().parents[4]
CONFORMANCE_SCHEMA_DIR = REPO_ROOT / "forge" / "conformance" / "schema"

CONFIG_SCHEMA_NAME = "conformance-pilot-config.schema.json"
CORPUS_SCHEMA_NAME = "conformance-corpus.schema.json"
OBSERVATION_SCHEMA_NAME = "conformance-observation.schema.json"
RUN_SCHEMA_NAME = "conformance-run.schema.json"

CONFIG_SCHEMA_VERSION = "creib.conformance-pilot.config.v1"
CORPUS_SCHEMA_VERSION = "creib.conformance-pilot.corpus.v1"
OBSERVATION_SCHEMA_VERSION = "creib.conformance-pilot.observation.v1"
RUN_SCHEMA_VERSION = "creib.conformance-pilot.run.v1"

OBSERVATION_SCHEMA_ID = "https://ahepi.example/smf/0.5/conformance-observation.schema.json"

# Ordered so that every serialised locus list is deterministic.  The set is
# the vocabulary already used by creib.forge.generic_inquiry.
LOCUS_VALUES: tuple[str, ...] = ("CANDIDATE", "AUXILIARY", "TEST", "SCOPE")
ROUTE_AWAITING_HUMAN_TRIAGE = "AWAITING_HUMAN_TRIAGE"
OVERALL_STATUS_UNRESOLVED = "UNRESOLVED"
SCOPE_REFUTED = "REFUTED_CASES_PRESENT"
SCOPE_UNREFUTED = "UNREFUTED_FOR_DECLARED_SCOPE"
SCOPE_INCONCLUSIVE = "INCONCLUSIVE_NO_SCORED_OUTPUT"

_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9._:-]{0,127}$")
_FIELD_NAME = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_SENTENCE_ID = re.compile(r"^S[1-9][0-9]{0,3}$")
_MODEL_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
_HEX_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_RFC3339 = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(Z|[+-][0-9]{2}:[0-9]{2})$"
)


def object_value(value: Any, where: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise RecordError(f"{where} must be an object")
    return value


def array_value(value: Any, where: str) -> list[Any]:
    if type(value) is not list:
        raise RecordError(f"{where} must be an array")
    return value


def text(value: Any, where: str) -> str:
    if type(value) is not str or not value.strip():
        raise RecordError(f"{where} must be a non-empty string")
    if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
        raise RecordError(f"{where} contains a Unicode surrogate")
    return value


def optional_text(value: Any, where: str) -> str | None:
    if value is None:
        return None
    return text(value, where)


def any_string(value: Any, where: str) -> str:
    if type(value) is not str:
        raise RecordError(f"{where} must be a string")
    if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
        raise RecordError(f"{where} contains a Unicode surrogate")
    return value


def identifier(value: Any, where: str) -> str:
    checked = text(value, where)
    if not _IDENTIFIER.fullmatch(checked):
        raise RecordError(f"{where} must be a stable identifier")
    return checked


def field_name(value: Any, where: str) -> str:
    checked = text(value, where)
    if not _FIELD_NAME.fullmatch(checked):
        raise RecordError(f"{where} must be a snake_case field name")
    return checked


def sentence_id(value: Any, where: str) -> str:
    checked = text(value, where)
    if not _SENTENCE_ID.fullmatch(checked):
        raise RecordError(f"{where} must be a sentence identifier such as S3")
    return checked


def model_id(value: Any, where: str) -> str:
    checked = text(value, where)
    if not _MODEL_ID.fullmatch(checked):
        raise RecordError(f"{where} must be a model identifier")
    return checked


def hex_digest(value: Any, where: str) -> str:
    checked = text(value, where)
    if not _HEX_DIGEST.fullmatch(checked):
        raise RecordError(f"{where} must be a lowercase SHA-256 hex digest")
    return checked


def rfc3339(value: Any, where: str) -> str:
    checked = text(value, where)
    if not _RFC3339.fullmatch(checked):
        raise RecordError(f"{where} must be an RFC 3339 timestamp with seconds")
    return checked


def boolean(value: Any, where: str) -> bool:
    if type(value) is not bool:
        raise RecordError(f"{where} must be a boolean")
    return value


def optional_boolean(value: Any, where: str) -> bool | None:
    if value is None:
        return None
    return boolean(value, where)


def integer(value: Any, where: str, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise RecordError(f"{where} must be an integer >= {minimum}")
    return value


def optional_integer(value: Any, where: str, *, minimum: int = 0) -> int | None:
    if value is None:
        return None
    return integer(value, where, minimum=minimum)


def scalar(value: Any, where: str) -> str | bool | int | None:
    """Accept only the JSON scalars the record profile allows (no floats)."""

    if value is None or type(value) is bool or type(value) is int:
        return value
    if type(value) is str:
        return any_string(value, where)
    raise RecordError(f"{where} must be a string, boolean, integer, or null")


def unique_texts(values: Any, where: str) -> tuple[str, ...]:
    items = array_value(values, where)
    checked = tuple(text(item, f"{where}[{index}]") for index, item in enumerate(items))
    if len(checked) != len(set(checked)):
        raise RecordError(f"{where} must not contain duplicates")
    return checked


def content_id(domain: str, value: Any) -> str:
    """Return a hex SHA-256 over domain-framed canonical bytes."""

    framed = domain.encode("ascii") + b"\0" + canonical_bytes(value)
    return hashlib.sha256(framed).hexdigest()


def canonical_text(value: Any) -> str:
    return canonical_bytes(value).decode("utf-8")


def file_binding(path: Path, root: Path) -> tuple[str, str, bytes]:
    """Return (posix path relative to root, sha256, raw bytes) for one file."""

    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise RecordError(f"cannot read {path}: {exc}") from exc
    try:
        relative = path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise RecordError(f"{path} is outside the pilot directory {root}") from exc
    return relative, bytes_digest(raw), raw


def decode_utf8(raw: bytes, where: str) -> str:
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RecordError(f"{where} is not UTF-8") from exc


def publish_no_clobber(path: Path, payload: bytes) -> Path:
    """Create ``path`` exclusively, write ``payload``, and fsync file and directory."""

    if not isinstance(path, Path):
        raise TypeError("path must be pathlib.Path")
    parent = path.parent
    try:
        parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise RecordError(f"cannot create record directory {parent}: {exc}") from exc
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError as exc:
        raise RecordError(f"record path exists: {path}") from exc
    except OSError as exc:
        raise RecordError(f"cannot create record {path}: {exc}") from exc
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except OSError as exc:
        raise RecordError(f"cannot durably write record {path}: {exc}") from exc
    try:
        directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        directory_descriptor = os.open(parent, directory_flags)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    except OSError as exc:
        raise RecordError(
            f"record was written without confirmed directory durability: {path}: {exc}"
        ) from exc
    return path


@lru_cache(maxsize=1)
def conformance_catalog() -> LocalSchemaCatalog:
    """Load the four pilot schemas through the repository's offline catalog."""

    return load_local_schema_catalog(CONFORMANCE_SCHEMA_DIR)


def validate_instance(instance: Any, schema_name: str) -> None:
    conformance_catalog().validate(instance, schema_name)


def form_schema_profile_validator() -> Draft202012Validator:
    """Validator for the restricted form-schema profile declared in the observation schema."""

    catalog = conformance_catalog()
    return Draft202012Validator(
        {"$ref": OBSERVATION_SCHEMA_ID + "#/$defs/form_schema"},
        registry=catalog.registry,
        format_checker=Draft202012Validator.FORMAT_CHECKER,
    )


def schema_errors(validator: Draft202012Validator, instance: Any) -> list[str]:
    """Return deterministic error descriptions for one instance."""

    errors = sorted(
        validator.iter_errors(instance),
        key=lambda error: (
            "/".join(str(part) for part in error.absolute_path),
            error.message,
        ),
    )
    return [
        "/" + "/".join(str(part) for part in error.absolute_path) + ": " + error.message
        for error in errors
    ]


def frozen_mapping_to_dict(value: Mapping[str, Any]) -> dict[str, Any]:
    """Deep-copy a JSON-like mapping into plain dicts and lists."""

    def copy(item: Any) -> Any:
        if isinstance(item, Mapping):
            return {str(key): copy(inner) for key, inner in item.items()}
        if isinstance(item, (list, tuple)):
            return [copy(inner) for inner in item]
        return item

    return copy(value)
