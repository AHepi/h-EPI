"""Shared vocabulary, digests, and small typed readers for the mini prototype.

Every refusal in the package is a ``MiniError`` carrying a code from the closed
vocabulary below, so a caller can branch on the code rather than on a message,
and an unknown code is itself refused.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from creib.canonical import canonical_bytes
from creib.errors import RecordError
from creib.forge.schema_validation import LocalSchemaCatalog, load_local_schema_catalog

REPO_ROOT = Path(__file__).resolve().parents[4]
MINI_SCHEMA_DIR = REPO_ROOT / "forge" / "mini" / "schema"
MINI_POLICY_DIR = REPO_ROOT / "forge" / "mini" / "policies"

MANIFEST_SCHEMA_NAME = "mini-manifest.schema.json"
KIND_SCHEMA_NAME = "mini-kind.schema.json"
POLICY_SCHEMA_NAME = "mini-policy.schema.json"
EVENT_SCHEMA_NAME = "mini-event.schema.json"

MANIFEST_SCHEMA_VERSION = "creib.mini.manifest.v1"
KIND_SCHEMA_VERSION = "creib.mini.kind.v1"
POLICY_SCHEMA_VERSION = "creib.mini.policy.v1"
EVENT_SCHEMA_VERSION = "creib.mini.event.v1"

EVENT_DOMAIN = "creib.mini.event.v1"
RUN_HEADER_DOMAIN = "creib.mini.run-header.v1"
BLOCK_DOMAIN = "creib.mini.evidence-block.v1"
ARTIFACT_DOMAIN = "creib.mini.artifact.v1"
STATE_DOMAIN = "creib.mini.state.v1"

#: The two fields every artifact must carry, whatever its kind (R7, R9).
REQUIRED_SUBMISSION_FIELDS: tuple[str, ...] = ("body", "commitments")
#: Fields of the template itself: always optional, always recognised (A13).
TEMPLATE_SUBMISSION_FIELDS: tuple[str, ...] = ("citations", "about", "answers")

MINI_CODES: frozenset[str] = frozenset(
    {
        "MINI_MANIFEST_INVALID",
        "MINI_KIND_UNKNOWN",
        "MINI_KIND_DUPLICATE",
        "MINI_KIND_OUTPUT_MISMATCH",
        "MINI_KIND_PORT_DUPLICATE",
        "MINI_KIND_FILE_UNREADABLE",
        "MINI_PORT_TYPE_UNKNOWN",
        "MINI_PORT_TYPE_DUPLICATE",
        "MINI_PORT_TYPE_DRAWS_FROM_INVALID",
        "MINI_PORT_PARAMS_INVALID",
        "MINI_RENDER_RULE_UNKNOWN",
        "MINI_PORT_UNKNOWN",
        "MINI_FORMAT_SPEC_INVALID",
        "MINI_FAILURE_POLICY_INVALID",
        "MINI_TIER_UNKNOWN",
        "MINI_TIER_DUPLICATE",
        "MINI_SOURCE_INVALID",
        "MINI_STAGE_DUPLICATE",
        "MINI_STAGE_UNKNOWN",
        "MINI_STAGE_NO_END",
        "MINI_STAGE_END_NOT_LAST",
        "MINI_ROUTE_TARGET_UNKNOWN",
        "MINI_ROUTE_INVALID",
        "MINI_POLICY_UNKNOWN",
        "MINI_POLICY_CHANGE_UNSUPPORTED",
        "MINI_POLICY_READ_REFUSED",
        "MINI_POLICY_WRITE_REFUSED",
        "MINI_POLICY_DEFAULT_UNKNOWN",
        "MINI_ATTENTION_POLICY_UNKNOWN",
        "MINI_ATTENTION_POLICY_DUPLICATE",
        "MINI_ATTENTION_SIGNATURE",
        "MINI_ATTENTION_UNDECLARED_SIGNAL",
        "MINI_ATTENTION_STAGE_UNKNOWN",
        "MINI_SIGNAL_UNKNOWN",
        "MINI_SIGNAL_DUPLICATE",
        "MINI_SUBMISSION_NOT_JSON",
        "MINI_SUBMISSION_MISSING_FIELD",
        "MINI_SUBMISSION_UNKNOWN_FIELD",
        "MINI_SUBMISSION_FIELD_TYPE",
        "MINI_SCRIPT_EXHAUSTED",
        "MINI_LIVE_CALL_FAILED",
        "MINI_LOG_SEQUENCE_BROKEN",
        "MINI_LOG_CHAIN_BROKEN",
        "MINI_LOG_EVENT_ID_MISMATCH",
        "MINI_LOG_EVENT_TYPE_UNKNOWN",
        "MINI_LOG_UNREADABLE",
        "MINI_BLOB_CORRUPT",
        "MINI_BLOB_MISSING",
        "MINI_RUN_ROOT_OCCUPIED",
    }
)


class MiniError(RecordError):
    """A typed refusal. ``code`` is from :data:`MINI_CODES`; the vocabulary
    fails closed, so a code nobody declared cannot be raised."""

    def __init__(self, code: str, message: str) -> None:
        if code not in MINI_CODES:
            raise RecordError(f"unknown mini refusal code: {code!r}")
        super().__init__(f"{code}: {message}")
        self.code = code


_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9._:-]{0,127}$")


def content_id(domain: str, value: Any) -> str:
    """Return a hex SHA-256 over domain-framed canonical bytes."""

    framed = domain.encode("ascii") + b"\0" + canonical_bytes(value)
    return hashlib.sha256(framed).hexdigest()


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def identifier(value: Any, where: str, code: str = "MINI_MANIFEST_INVALID") -> str:
    if type(value) is not str or not _IDENTIFIER.match(value):
        raise MiniError(code, f"{where} must be an identifier, got {value!r}")
    return value


def text(value: Any, where: str, code: str = "MINI_MANIFEST_INVALID") -> str:
    if type(value) is not str or not value:
        raise MiniError(code, f"{where} must be a non-empty string")
    return value


def object_value(value: Any, where: str, code: str = "MINI_MANIFEST_INVALID") -> dict[str, Any]:
    if type(value) is not dict:
        raise MiniError(code, f"{where} must be a JSON object")
    return value


def array_value(value: Any, where: str, code: str = "MINI_MANIFEST_INVALID") -> list[Any]:
    if type(value) is not list:
        raise MiniError(code, f"{where} must be a JSON array")
    return value


def mini_catalog() -> LocalSchemaCatalog:
    return load_local_schema_catalog(MINI_SCHEMA_DIR)


def validate_instance(instance: Any, schema_name: str, code: str) -> None:
    """Validate against a mini schema, re-raising as a typed mini refusal."""

    try:
        mini_catalog().validate(instance, schema_name)
    except RecordError as error:
        raise MiniError(code, str(error)) from error
