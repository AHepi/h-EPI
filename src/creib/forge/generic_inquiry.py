"""Stage-neutral adaptive-inquiry v3 foundation.

This module is intentionally isolated from :mod:`creib.forge.inquiry`.  The
existing v1/v2 records and publishers remain unchanged.  V3 normalizes one
exact observation from an explicitly selected adapter, binds every subject
that gives the observation its meaning, and previews a human-selected work
route.  It is not publication authority and it never infers a failure locus or
research need from an observation's origin.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from functools import lru_cache
from pathlib import Path
import re
from typing import Any, Iterable, Mapping, Protocol

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError
from referencing import Registry, Resource
from referencing.exceptions import NoSuchResource

from creib.canonical import bytes_digest, canonical_bytes, domain_digest
from creib.errors import PolicyViolation, RecordError
from creib.strict_json import loads_strict

from .engine import generate_research_warrant
from .models import (
    ISSUE_SCHEMA,
    NON_INDUCTIVE_LIMIT,
    WARRANT_SCHEMA,
    Issue,
    ResearchWarrant,
    parse_issue,
    parse_research_warrant,
)


INQUIRY_INPUT_SCHEMA = "creib.semantic-forge.inquiry-input.v1"
INPUT_OBSERVATION_SCHEMA = "creib.semantic-forge.input-observation.v1"
CASE_BINDING_SCHEMA = "creib.semantic-forge.case-binding.v1"
GENERIC_PLAN_SCHEMA = "creib.semantic-forge.adaptive-inquiry-plan.v3"
LOCUS_ASSESSMENT_SCHEMA = "creib.semantic-forge.locus-assessment.v1"
NEXT_ACTION_SCHEMA = "creib.semantic-forge.next-action.v2"
ATTACK_TARGET_DOMAIN = "creib.semantic-forge.attack-target.v1"

INQUIRY_INPUT_SCHEMA_REF = "../schema/inquiry-input-v1.schema.json"
GENERIC_PLAN_SCHEMA_REF = "../schema/adaptive-inquiry-v3.schema.json"

OBSERVATION_KIND = "CRITICISM_CANDIDATE_NOT_SEMANTIC_VERDICT"
OBSERVATION_EFFECT = "CRITICISM_CANDIDATE_ONLY"
ROUTING_EFFECT = "WORKFLOW_ROUTING_ONLY"

LEGACY_CALIBRATION_ADAPTER_ID = "SMF-ADAPTER-CALIBRATION-RUN-V1"
GENERIC_RECORD_ADAPTER_ID = "SMF-ADAPTER-INQUIRY-INPUT-V1"
LEGACY_OBSERVATION_POINTER = "/fixture_evaluations/weak_typed_role_projection"
GENERIC_OBSERVATION_POINTER = "/observation/selected_value"
LEGACY_SELECTION_DOMAIN = (
    "creib.semantic-forge.criticism-candidate-observation.v1"
)
GENERIC_SELECTION_DOMAIN = (
    "creib.semantic-forge.generic-input-observation-selection.v1"
)

DEFAULT_SCHEMA_DIR = Path(__file__).resolve().parents[3] / "forge" / "schema"

_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9._:-]{0,127}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_DOMAIN_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
_LOCUS_VALUES = frozenset({"CANDIDATE", "AUXILIARY", "TEST", "SCOPE"})
_SELECTION_BASES = frozenset(
    {
        "UPSTREAM_DEPENDENCY",
        "INDEPENDENT_HUMAN_PRIORITY",
        "SHARED_ACTION_FOR_MULTIPLE_LOCI",
    }
)
_LOCATION_ROUTE_INTENT = {
    "INTERNAL_HARNESS_SPECIFICATION": "INTERNAL_HARNESS_WORK",
    "INTERNAL_DEDUCTION_OR_MODEL_FINDING": "INTERNAL_MODEL_WORK",
    "CR_AUTHORITY_INTERPRETATION": "AUTHORITY_REVIEW",
    "EXTERNAL_CRITICAL_INSTRUMENT": "EXTERNAL_RESEARCH_REQUIRED",
    "APPLICATION_EMPIRICAL": "EXTERNAL_RESEARCH_REQUIRED",
}


class ObservationDomain(str, Enum):
    """Where an observation was produced, never where its defect is located."""

    HARNESS_TEST = "HARNESS_TEST"
    LEGACY_CALIBRATION = "LEGACY_CALIBRATION"
    MATHEMATICAL_EXTRACTION = "MATHEMATICAL_EXTRACTION"
    ROUND_TRIP = "ROUND_TRIP"
    SEMANTIC_MODEL = "SEMANTIC_MODEL"
    SOURCE_TRANSLATION = "SOURCE_TRANSLATION"


class BindingKind(str, Enum):
    CANONICAL_RECORD = "CANONICAL_RECORD"
    CONTRACT = "CONTRACT"
    FILE_BYTES = "FILE_BYTES"
    VALUE = "VALUE"


class GenericInquiryRoute(str, Enum):
    AWAITING_HUMAN_TRIAGE = "AWAITING_HUMAN_TRIAGE"
    AWAITING_HUMAN_ACTION_SELECTION = "AWAITING_HUMAN_ACTION_SELECTION"
    INTERNAL_HARNESS_WORK = "INTERNAL_HARNESS_WORK"
    INTERNAL_MODEL_WORK = "INTERNAL_MODEL_WORK"
    AUTHORITY_REVIEW = "AUTHORITY_REVIEW"
    EXTERNAL_RESEARCH_REQUIRED = "EXTERNAL_RESEARCH_REQUIRED"


def _object(value: Any, where: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise RecordError(f"{where} must be an object")
    return value


def _array(value: Any, where: str) -> list[Any]:
    if type(value) is not list:
        raise RecordError(f"{where} must be an array")
    return value


def _text(value: Any, where: str) -> str:
    if type(value) is not str or not value.strip():
        raise RecordError(f"{where} must be a non-empty string")
    if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
        raise RecordError(f"{where} contains a Unicode surrogate")
    return value


def _identifier(value: Any, where: str) -> str:
    checked = _text(value, where)
    if not _IDENTIFIER.fullmatch(checked):
        raise RecordError(f"{where} must be a stable identifier")
    return checked


def _sha256(value: Any, where: str) -> str:
    checked = _text(value, where)
    if not _SHA256.fullmatch(checked):
        raise RecordError(f"{where} must be a lowercase SHA-256 digest")
    return checked


def _domain_sha256(value: Any, where: str) -> str:
    checked = _text(value, where)
    if not _DOMAIN_SHA256.fullmatch(checked):
        raise RecordError(f"{where} must be a domain-separated SHA-256 digest")
    return checked


def _exact_keys(record: dict[str, Any], expected: set[str], where: str) -> None:
    actual = set(record)
    if actual != expected:
        raise RecordError(
            f"{where} keys differ; missing={sorted(expected - actual)}, "
            f"extra={sorted(actual - expected)}"
        )


def _without(record: Mapping[str, Any], key: str) -> dict[str, object]:
    return {name: value for name, value in record.items() if name != key}


def _record_id(prefix: str, domain: str, body: Mapping[str, object]) -> str:
    return f"{prefix}:{domain_digest(domain, dict(body)).removeprefix('sha256:')}"


def _plain_domain_digest(domain: str, value: Any) -> str:
    return domain_digest(domain, value).removeprefix("sha256:")


def _json_pointer(value: Any, pointer: Any, where: str) -> Any:
    if type(pointer) is not str:
        raise RecordError(f"{where} must be a JSON pointer string")
    if pointer == "":
        return value
    if not pointer.startswith("/"):
        raise RecordError(f"{where} must be empty or start with '/'")
    current = value
    for encoded in pointer[1:].split("/"):
        token = ""
        index = 0
        while index < len(encoded):
            character = encoded[index]
            if character != "~":
                token += character
                index += 1
                continue
            if index + 1 >= len(encoded) or encoded[index + 1] not in "01":
                raise RecordError(f"{where} contains an invalid JSON pointer escape")
            token += "~" if encoded[index + 1] == "0" else "/"
            index += 2
        if type(current) is dict:
            if token not in current:
                raise RecordError(f"{where} does not resolve in its record")
            current = current[token]
        elif type(current) is list:
            if not token.isdigit() or (len(token) > 1 and token.startswith("0")):
                raise RecordError(f"{where} contains an invalid array index")
            offset = int(token)
            if offset >= len(current):
                raise RecordError(f"{where} array index is out of range")
            current = current[offset]
        else:
            raise RecordError(f"{where} traverses a scalar value")
    return current


def _canonical_tuple(
    values: Iterable[Any],
    where: str,
    *,
    nonempty: bool = False,
) -> tuple[Any, ...]:
    checked = tuple(values)
    if nonempty and not checked:
        raise RecordError(f"{where} must not be empty")
    encoded = tuple(canonical_bytes(item.to_dict()) for item in checked)
    if len(encoded) != len(set(encoded)):
        raise RecordError(f"{where} must contain unique bindings")
    if encoded != tuple(sorted(encoded)):
        raise RecordError(f"{where} must use canonical order")
    return checked


def _canonical_strings(
    value: Any,
    where: str,
    *,
    nonempty: bool = False,
) -> tuple[str, ...]:
    items = _array(value, where)
    checked = tuple(_text(item, f"{where} item") for item in items)
    if nonempty and not checked:
        raise RecordError(f"{where} must not be empty")
    if len(checked) != len(set(checked)):
        raise RecordError(f"{where} must contain unique values")
    if checked != tuple(sorted(checked)):
        raise RecordError(f"{where} must use canonical lexical order")
    return checked


def _date(value: Any, where: str) -> str:
    checked = _text(value, where)
    try:
        parsed = date.fromisoformat(checked)
    except ValueError as exc:
        raise RecordError(f"{where} must be an ISO 8601 date") from exc
    if parsed.isoformat() != checked:
        raise RecordError(f"{where} must use canonical YYYY-MM-DD form")
    return checked


def _deny_schema_retrieval(uri: str) -> Resource[Any]:
    raise NoSuchResource(ref=uri)


@lru_cache(maxsize=1)
def _schema_registry() -> tuple[dict[str, dict[str, Any]], Registry[Any]]:
    schemas: dict[str, dict[str, Any]] = {}
    registry: Registry[Any] = Registry(retrieve=_deny_schema_retrieval)
    for filename in (
        "challenge.schema.json",
        "research-issue.schema.json",
        "calibration-run.schema.json",
        "inquiry-input-v1.schema.json",
        "adaptive-inquiry-v3.schema.json",
    ):
        path = DEFAULT_SCHEMA_DIR / filename
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise RecordError(f"cannot read generic inquiry schema {path}: {exc}") from exc
        schema = _object(loads_strict(raw), f"schema {filename}")
        try:
            Draft202012Validator.check_schema(schema)
            resource = Resource.from_contents(schema)
        except (SchemaError, ValueError) as exc:
            raise RecordError(f"invalid generic inquiry schema {filename}: {exc}") from exc
        schemas[filename] = schema
        registry = registry.with_resource(_text(schema.get("$id"), "$id"), resource)
    return schemas, registry.crawl()


def _validate_schema(record: dict[str, object], filename: str) -> None:
    schemas, registry = _schema_registry()
    try:
        schema = schemas[filename]
    except KeyError as exc:
        raise RecordError(f"unknown generic inquiry schema {filename}") from exc
    validator = Draft202012Validator(schema, registry=registry)
    errors = sorted(validator.iter_errors(record), key=lambda item: list(item.path))
    if errors:
        failure = errors[0]
        location = "/" + "/".join(str(part) for part in failure.path)
        raise RecordError(f"{filename} validation failed at {location}: {failure.message}")


@dataclass(frozen=True)
class AuthorityBinding:
    role: str
    authority_id: str
    file_sha256: str

    def __post_init__(self) -> None:
        _identifier(self.role, "authority_binding.role")
        _identifier(self.authority_id, "authority_binding.authority_id")
        _sha256(self.file_sha256, "authority_binding.file_sha256")

    def to_dict(self) -> dict[str, object]:
        return {
            "role": self.role,
            "authority_id": self.authority_id,
            "file_sha256": self.file_sha256,
        }


@dataclass(frozen=True)
class ComponentBinding:
    role: str
    subject_id: str | None
    binding_kind: BindingKind
    sha256: str

    def __post_init__(self) -> None:
        _identifier(self.role, "component_binding.role")
        if self.subject_id is not None:
            _identifier(self.subject_id, "component_binding.subject_id")
        if type(self.binding_kind) is not BindingKind:
            raise RecordError("component_binding.binding_kind must be BindingKind")
        _sha256(self.sha256, "component_binding.sha256")

    def to_dict(self) -> dict[str, object]:
        return {
            "role": self.role,
            "subject_id": self.subject_id,
            "binding_kind": self.binding_kind.value,
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class ResearchLedgerBinding:
    ledger_id: str
    created_on: str
    as_of_date: str
    file_sha256: str
    record_sha256: str

    def __post_init__(self) -> None:
        _identifier(self.ledger_id, "research_ledger.ledger_id")
        created = _date(self.created_on, "research_ledger.created_on")
        as_of = _date(self.as_of_date, "research_ledger.as_of_date")
        if as_of > created:
            raise RecordError("research_ledger.as_of_date cannot follow created_on")
        _sha256(self.file_sha256, "research_ledger.file_sha256")
        _domain_sha256(self.record_sha256, "research_ledger.record_sha256")

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> "ResearchLedgerBinding":
        record = _object(dict(value), "research_ledger")
        _exact_keys(
            record,
            {
                "ledger_id",
                "created_on",
                "as_of_date",
                "file_sha256",
                "record_sha256",
            },
            "research_ledger",
        )
        return cls(
            ledger_id=record["ledger_id"],
            created_on=record["created_on"],
            as_of_date=record["as_of_date"],
            file_sha256=record["file_sha256"],
            record_sha256=record["record_sha256"],
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "ledger_id": self.ledger_id,
            "created_on": self.created_on,
            "as_of_date": self.as_of_date,
            "file_sha256": self.file_sha256,
            "record_sha256": self.record_sha256,
        }


@dataclass(frozen=True)
class ResearchBasis:
    issue: Issue
    warrant: ResearchWarrant

    def __post_init__(self) -> None:
        if type(self.issue) is not Issue:
            raise TypeError("research_basis.issue must be Issue")
        if type(self.warrant) is not ResearchWarrant:
            raise TypeError("research_basis.warrant must be ResearchWarrant")
        expected = generate_research_warrant(
            self.issue,
            discovery_channels=self.warrant.discovery_channels,
        )
        if expected is None or expected != self.warrant:
            raise PolicyViolation(
                "research basis warrant is not the exact deterministic projection "
                "of its external issue"
            )

    @property
    def issue_sha256(self) -> str:
        return domain_digest(ISSUE_SCHEMA, self.issue.to_dict())

    @property
    def warrant_sha256(self) -> str:
        return domain_digest(WARRANT_SCHEMA, self.warrant.to_dict())

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> "ResearchBasis":
        record = _object(dict(value), "research_basis")
        _exact_keys(record, {"issue", "warrant"}, "research_basis")
        return cls(
            issue=parse_issue(record["issue"]),
            warrant=parse_research_warrant(record["warrant"]),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "issue": self.issue.to_dict(),
            "warrant": self.warrant.to_dict(),
        }


@dataclass(frozen=True)
class InputObservation:
    """One exact trigger observation plus the adapter that selected it."""

    observation_domain: ObservationDomain
    adapter_id: str
    adapter_contract_sha256: str
    source_record_id: str
    source_schema_version: str
    source_record_id_pointer: str
    source_file_sha256: str
    source_contract_sha256: str
    selected_value_pointer: str
    selected_value_digest_domain: str
    selected_value_sha256: str
    source_bytes: bytes | None = field(default=None, repr=False, compare=False)
    observation_id: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self.observation_domain) is not ObservationDomain:
            raise RecordError("input_observation.observation_domain must be ObservationDomain")
        _identifier(self.adapter_id, "input_observation.adapter_id")
        _sha256(
            self.adapter_contract_sha256,
            "input_observation.adapter_contract_sha256",
        )
        _identifier(self.source_record_id, "input_observation.source_record_id")
        _text(self.source_schema_version, "input_observation.source_schema_version")
        _json_pointer({}, "", "input_observation.source_record_id_pointer")
        _text(
            self.source_record_id_pointer,
            "input_observation.source_record_id_pointer",
        )
        _sha256(self.source_file_sha256, "input_observation.source_file_sha256")
        _sha256(
            self.source_contract_sha256,
            "input_observation.source_contract_sha256",
        )
        _text(self.selected_value_pointer, "input_observation.selected_value_pointer")
        _text(
            self.selected_value_digest_domain,
            "input_observation.selected_value_digest_domain",
        )
        _domain_sha256(
            self.selected_value_sha256,
            "input_observation.selected_value_sha256",
        )
        if self.source_bytes is not None:
            if type(self.source_bytes) is not bytes:
                raise TypeError("input_observation.source_bytes must be bytes")
            try:
                snapshot = loads_strict(self.source_bytes.decode("utf-8"))
            except UnicodeDecodeError as exc:
                raise RecordError("input observation source is not UTF-8") from exc
            source_record = _object(snapshot, "input observation source")
            if self.source_bytes != canonical_bytes(source_record) + b"\n":
                raise RecordError(
                    "input observation source must be canonical JSON plus one newline"
                )
            if bytes_digest(self.source_bytes) != self.source_file_sha256:
                raise RecordError("input observation source-file digest mismatch")
            if _json_pointer(
                source_record,
                self.source_record_id_pointer,
                "input_observation.source_record_id_pointer",
            ) != self.source_record_id:
                raise PolicyViolation("input observation source-record ID pointer mismatch")
            selected = _json_pointer(
                source_record,
                self.selected_value_pointer,
                "input_observation.selected_value_pointer",
            )
            if domain_digest(self.selected_value_digest_domain, selected) != (
                self.selected_value_sha256
            ):
                raise RecordError("input observation selected-value digest mismatch")
        object.__setattr__(
            self,
            "observation_id",
            _record_id("IO", INPUT_OBSERVATION_SCHEMA, self._body()),
        )

    def _body(self) -> dict[str, object]:
        return {
            "schema_version": INPUT_OBSERVATION_SCHEMA,
            "observation_domain": self.observation_domain.value,
            "adapter_id": self.adapter_id,
            "adapter_contract_sha256": self.adapter_contract_sha256,
            "source_record_id": self.source_record_id,
            "source_schema_version": self.source_schema_version,
            "source_record_id_pointer": self.source_record_id_pointer,
            "source_file_sha256": self.source_file_sha256,
            "source_contract_sha256": self.source_contract_sha256,
            "selected_value_pointer": self.selected_value_pointer,
            "selected_value_digest_domain": self.selected_value_digest_domain,
            "selected_value_sha256": self.selected_value_sha256,
            "observation_kind": OBSERVATION_KIND,
            "epistemic_effect": OBSERVATION_EFFECT,
            "semantic_verdict": None,
        }

    @property
    def source_snapshot(self) -> dict[str, object]:
        if self.source_bytes is None:
            raise RecordError("input observation has no attached source snapshot")
        return _object(
            loads_strict(self.source_bytes.decode("utf-8")),
            "input observation source",
        )

    def to_dict(self) -> dict[str, object]:
        return {**self._body(), "observation_id": self.observation_id}


@dataclass(frozen=True)
class CaseBinding:
    """Exact subjects and one observation; no inferred criticism or route."""

    authority_bindings: tuple[AuthorityBinding, ...]
    component_bindings: tuple[ComponentBinding, ...]
    observation: InputObservation
    research_basis: ResearchBasis | None
    research_ledger: ResearchLedgerBinding
    case_binding_id: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self.authority_bindings) is not tuple:
            raise TypeError("case_binding.authority_bindings must be a tuple")
        if type(self.component_bindings) is not tuple:
            raise TypeError("case_binding.component_bindings must be a tuple")
        if any(type(item) is not AuthorityBinding for item in self.authority_bindings):
            raise TypeError("case_binding authority values must be AuthorityBinding")
        if any(type(item) is not ComponentBinding for item in self.component_bindings):
            raise TypeError("case_binding component values must be ComponentBinding")
        _canonical_tuple(
            self.authority_bindings,
            "case_binding.authority_bindings",
            nonempty=True,
        )
        _canonical_tuple(
            self.component_bindings,
            "case_binding.component_bindings",
            nonempty=True,
        )
        authority_roles = tuple(item.role for item in self.authority_bindings)
        if len(authority_roles) != len(set(authority_roles)):
            raise PolicyViolation(
                "case_binding repeats a singleton authority role with conflicting bytes"
            )
        component_roles = tuple(item.role for item in self.component_bindings)
        if len(component_roles) != len(set(component_roles)):
            raise PolicyViolation(
                "case_binding repeats a singleton component role with conflicting bytes"
            )
        if type(self.observation) is not InputObservation:
            raise TypeError("case_binding.observation must be InputObservation")
        if self.research_basis is not None and type(self.research_basis) is not ResearchBasis:
            raise TypeError("case_binding.research_basis must be ResearchBasis or None")
        if type(self.research_ledger) is not ResearchLedgerBinding:
            raise TypeError("case_binding.research_ledger must be ResearchLedgerBinding")
        object.__setattr__(
            self,
            "case_binding_id",
            _record_id("CB", CASE_BINDING_SCHEMA, self._body()),
        )

    def _body(self) -> dict[str, object]:
        return {
            "schema_version": CASE_BINDING_SCHEMA,
            "authority_bindings": [item.to_dict() for item in self.authority_bindings],
            "component_bindings": [item.to_dict() for item in self.component_bindings],
            "observation": self.observation.to_dict(),
            "research_basis": (
                None if self.research_basis is None else self.research_basis.to_dict()
            ),
            "research_ledger": self.research_ledger.to_dict(),
        }

    @property
    def subject_binding_sha256(self) -> str:
        return domain_digest(
            "creib.semantic-forge.inquiry-subject-binding.v1",
            {
                "authority_bindings": [
                    item.to_dict() for item in self.authority_bindings
                ],
                "component_bindings": [
                    item.to_dict() for item in self.component_bindings
                ],
            },
        )

    def to_dict(self) -> dict[str, object]:
        return {**self._body(), "case_binding_id": self.case_binding_id}


def _parse_authority_binding(value: Any) -> AuthorityBinding:
    record = _object(value, "authority_binding")
    _exact_keys(record, {"role", "authority_id", "file_sha256"}, "authority_binding")
    return AuthorityBinding(
        role=record["role"],
        authority_id=record["authority_id"],
        file_sha256=record["file_sha256"],
    )


def _parse_component_binding(value: Any) -> ComponentBinding:
    record = _object(value, "component_binding")
    _exact_keys(
        record,
        {"role", "subject_id", "binding_kind", "sha256"},
        "component_binding",
    )
    try:
        kind = BindingKind(record["binding_kind"])
    except (TypeError, ValueError) as exc:
        raise RecordError("component_binding.binding_kind is unsupported") from exc
    return ComponentBinding(
        role=record["role"],
        subject_id=record["subject_id"],
        binding_kind=kind,
        sha256=record["sha256"],
    )


def parse_input_observation(value: Any) -> InputObservation:
    record = _object(value, "input_observation")
    expected = {
        "schema_version",
        "observation_id",
        "observation_domain",
        "adapter_id",
        "adapter_contract_sha256",
        "source_record_id",
        "source_schema_version",
        "source_record_id_pointer",
        "source_file_sha256",
        "source_contract_sha256",
        "selected_value_pointer",
        "selected_value_digest_domain",
        "selected_value_sha256",
        "observation_kind",
        "epistemic_effect",
        "semantic_verdict",
    }
    _exact_keys(record, expected, "input_observation")
    if record["schema_version"] != INPUT_OBSERVATION_SCHEMA:
        raise RecordError("input observation has an unsupported schema version")
    if record["observation_kind"] != OBSERVATION_KIND:
        raise PolicyViolation("input observation changed its epistemic kind")
    if record["epistemic_effect"] != OBSERVATION_EFFECT:
        raise PolicyViolation("input observation changed its epistemic effect")
    if record["semantic_verdict"] is not None:
        raise PolicyViolation("input observation cannot contain a semantic verdict")
    try:
        origin = ObservationDomain(record["observation_domain"])
    except (TypeError, ValueError) as exc:
        raise RecordError("input observation has an unsupported domain") from exc
    parsed = InputObservation(
        observation_domain=origin,
        adapter_id=record["adapter_id"],
        adapter_contract_sha256=record["adapter_contract_sha256"],
        source_record_id=record["source_record_id"],
        source_schema_version=record["source_schema_version"],
        source_record_id_pointer=record["source_record_id_pointer"],
        source_file_sha256=record["source_file_sha256"],
        source_contract_sha256=record["source_contract_sha256"],
        selected_value_pointer=record["selected_value_pointer"],
        selected_value_digest_domain=record["selected_value_digest_domain"],
        selected_value_sha256=record["selected_value_sha256"],
    )
    if parsed.observation_id != record["observation_id"]:
        raise RecordError("input observation content-addressed ID mismatch")
    return parsed


def parse_case_binding(value: Any) -> CaseBinding:
    record = _object(value, "case_binding")
    _exact_keys(
        record,
        {
            "schema_version",
            "case_binding_id",
            "authority_bindings",
            "component_bindings",
            "observation",
            "research_basis",
            "research_ledger",
        },
        "case_binding",
    )
    if record["schema_version"] != CASE_BINDING_SCHEMA:
        raise RecordError("case binding has an unsupported schema version")
    authorities = tuple(
        _parse_authority_binding(item)
        for item in _array(record["authority_bindings"], "authority_bindings")
    )
    components = tuple(
        _parse_component_binding(item)
        for item in _array(record["component_bindings"], "component_bindings")
    )
    basis_value = record["research_basis"]
    parsed = CaseBinding(
        authority_bindings=authorities,
        component_bindings=components,
        observation=parse_input_observation(record["observation"]),
        research_basis=(
            None
            if basis_value is None
            else ResearchBasis.from_dict(_object(basis_value, "research_basis"))
        ),
        research_ledger=ResearchLedgerBinding.from_dict(
            _object(record["research_ledger"], "research_ledger")
        ),
    )
    if parsed.case_binding_id != record["case_binding_id"]:
        raise RecordError("case binding content-addressed ID mismatch")
    return parsed


def compute_inquiry_input_id(record: Mapping[str, object]) -> str:
    value = _object(dict(record), "inquiry input")
    if value.get("schema_version") != INQUIRY_INPUT_SCHEMA:
        raise RecordError("inquiry input has an unsupported schema version")
    return _record_id("II", INQUIRY_INPUT_SCHEMA, _without(value, "input_id"))


def build_inquiry_input_record(
    *,
    producer_contract_sha256: str,
    authority_bindings: tuple[AuthorityBinding, ...],
    component_bindings: tuple[ComponentBinding, ...],
    observation_domain: ObservationDomain,
    selected_value: Any,
    research_basis: ResearchBasis | None,
) -> dict[str, object]:
    """Build a canonical stage-neutral input; it remains only a criticism input."""

    _sha256(producer_contract_sha256, "producer_contract_sha256")
    _canonical_tuple(authority_bindings, "authority_bindings", nonempty=True)
    _canonical_tuple(component_bindings, "component_bindings", nonempty=True)
    authority_roles = tuple(item.role for item in authority_bindings)
    if len(authority_roles) != len(set(authority_roles)):
        raise PolicyViolation(
            "inquiry input repeats a singleton authority role with conflicting bytes"
        )
    component_roles = tuple(item.role for item in component_bindings)
    if len(component_roles) != len(set(component_roles)):
        raise PolicyViolation(
            "inquiry input repeats a singleton component role with conflicting bytes"
        )
    if type(observation_domain) is not ObservationDomain:
        raise TypeError("observation_domain must be ObservationDomain")
    canonical_bytes(selected_value)
    body: dict[str, object] = {
        "$schema": INQUIRY_INPUT_SCHEMA_REF,
        "schema_version": INQUIRY_INPUT_SCHEMA,
        "record_type": "inquiry_input",
        "producer_contract_sha256": producer_contract_sha256,
        "authority_bindings": [item.to_dict() for item in authority_bindings],
        "component_bindings": [item.to_dict() for item in component_bindings],
        "observation": {
            "observation_domain": observation_domain.value,
            "selected_value": selected_value,
            "observation_kind": OBSERVATION_KIND,
            "semantic_verdict": None,
        },
        "research_basis": None if research_basis is None else research_basis.to_dict(),
        "epistemic_effect": OBSERVATION_EFFECT,
        "semantic_verdict": None,
    }
    record = {**body, "input_id": _record_id("II", INQUIRY_INPUT_SCHEMA, body)}
    _validate_schema(record, "inquiry-input-v1.schema.json")
    return record


class InquiryInputAdapter(Protocol):
    adapter_id: str
    adapter_contract_sha256: str

    def adapt_record(
        self,
        record: dict[str, Any],
        raw: bytes,
        *,
        repo_root: Path,
        research_ledger: ResearchLedgerBinding,
    ) -> CaseBinding:
        ...


class AdapterRegistry:
    """Closed, explicit adapter selection; there is deliberately no auto-detect."""

    def __init__(self, adapters: Iterable[InquiryInputAdapter] = ()) -> None:
        self._adapters: dict[str, InquiryInputAdapter] = {}
        for adapter in adapters:
            self.register(adapter)

    def register(self, adapter: InquiryInputAdapter) -> None:
        adapter_id = _identifier(getattr(adapter, "adapter_id", None), "adapter_id")
        _sha256(
            getattr(adapter, "adapter_contract_sha256", None),
            "adapter_contract_sha256",
        )
        if not callable(getattr(adapter, "adapt_record", None)):
            raise TypeError("adapter must implement adapt_record")
        if adapter_id in self._adapters:
            raise RecordError(f"duplicate inquiry input adapter: {adapter_id}")
        self._adapters[adapter_id] = adapter

    @property
    def adapter_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._adapters))

    def adapt_path(
        self,
        adapter_id: str,
        path: Path,
        *,
        repo_root: Path,
        research_ledger_binding: Mapping[str, object],
    ) -> CaseBinding:
        selected_id = _identifier(adapter_id, "adapter_id")
        try:
            adapter = self._adapters[selected_id]
        except KeyError as exc:
            raise RecordError(f"unknown inquiry input adapter: {selected_id}") from exc
        if not isinstance(path, Path) or not isinstance(repo_root, Path):
            raise TypeError("path and repo_root must be pathlib.Path")
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise RecordError(f"cannot read inquiry input {path}: {exc}") from exc
        try:
            decoded = loads_strict(raw.decode("utf-8"))
        except UnicodeDecodeError as exc:
            raise RecordError(f"inquiry input is not UTF-8: {path}") from exc
        record = _object(decoded, "inquiry input")
        if raw != canonical_bytes(record) + b"\n":
            raise RecordError("inquiry input must be canonical JSON plus one newline")
        ledger = ResearchLedgerBinding.from_dict(research_ledger_binding)
        case = adapter.adapt_record(
            record,
            raw,
            repo_root=repo_root,
            research_ledger=ledger,
        )
        if case.observation.adapter_id != selected_id:
            raise PolicyViolation("adapter output changed the explicitly selected adapter ID")
        if case.observation.adapter_contract_sha256 != adapter.adapter_contract_sha256:
            raise PolicyViolation("adapter output changed its exact adapter contract")
        parse_case_binding(case.to_dict())
        return case


_LEGACY_ADAPTER_CONTRACT = {
    "adapter_id": LEGACY_CALIBRATION_ADAPTER_ID,
    "accepted_schema_version": "creib.semantic-forge.calibration-run.v1",
    "record_id_pointer": "/run_id",
    "observation_pointer": LEGACY_OBSERVATION_POINTER,
    "selection_digest_domain": LEGACY_SELECTION_DOMAIN,
    "semantic_verdict_pointers": [
        "/fixture_evaluations/weak_typed_role_projection/semantic_verdict",
        "/semantic_verdict",
    ],
}
_GENERIC_ADAPTER_CONTRACT = {
    "adapter_id": GENERIC_RECORD_ADAPTER_ID,
    "accepted_schema_version": INQUIRY_INPUT_SCHEMA,
    "record_id_pointer": "/input_id",
    "observation_pointer": GENERIC_OBSERVATION_POINTER,
    "selection_digest_domain": GENERIC_SELECTION_DOMAIN,
    "semantic_verdict_pointers": [
        "/observation/semantic_verdict",
        "/semantic_verdict",
    ],
}


class LegacyCalibrationAdapter:
    adapter_id = LEGACY_CALIBRATION_ADAPTER_ID
    adapter_contract_sha256 = _plain_domain_digest(
        "creib.semantic-forge.inquiry-input-adapter-contract.v1",
        _LEGACY_ADAPTER_CONTRACT,
    )

    def adapt_record(
        self,
        record: dict[str, Any],
        raw: bytes,
        *,
        repo_root: Path,
        research_ledger: ResearchLedgerBinding,
    ) -> CaseBinding:
        # This isolated foundation normalizes the pinned run intrinsically.  A
        # future v3 publisher must additionally require current-repository
        # replay before treating the case as transition authority.
        del repo_root
        _validate_schema(record, "calibration-run.schema.json")
        try:
            trace = _object(record["corpus_trace"], "calibration corpus_trace")
            issue = parse_issue(trace["selected_external_issue"])
            routing = _object(record["research_routing"], "calibration research_routing")
            warrant = parse_research_warrant(routing["external_role_warrant"])
            basis = ResearchBasis(issue, warrant)
            challenge = _object(trace["selected_challenge"], "selected challenge")
            execution = _object(record["execution_contract"], "execution contract")
            evaluation = _object(
                _object(record["fixture_evaluations"], "fixture evaluations")[
                    "weak_typed_role_projection"
                ],
                "weak typed-role observation",
            )
            contract = _object(evaluation["contract_binding"], "observation contract")
            evaluators = _object(
                execution["evaluator_contract_sha256"],
                "execution evaluator contracts",
            )
        except KeyError as exc:
            raise RecordError(f"calibration input is missing {exc}") from exc
        pairs = (
            (evaluation.get("challenge_id"), challenge.get("challenge_id"), "challenge ID"),
            (
                contract.get("challenge_contract_sha256"),
                execution.get("challenge_contract_sha256"),
                "challenge contract",
            ),
            (
                contract.get("candidate_contract_sha256"),
                execution.get("candidate_contract_sha256"),
                "candidate contract",
            ),
            (
                contract.get("fixture_contract_sha256"),
                execution.get("fixture_contract_sha256"),
                "fixture contract",
            ),
            (
                contract.get("evaluator_contract_sha256"),
                evaluators.get("weak_typed_role_projection"),
                "evaluator contract",
            ),
        )
        for actual, expected, label in pairs:
            if actual != expected:
                raise RecordError(f"calibration input has a mismatched {label}")
        if record.get("semantic_verdict") is not None or evaluation.get(
            "semantic_verdict"
        ) is not None:
            raise PolicyViolation("calibration input contains a semantic verdict")

        authorities = (
            AuthorityBinding(
                "SEMANTIC_AUTHORITY",
                "CR-1.0",
                _sha256(execution.get("authority_sha256"), "authority_sha256"),
            ),
        )
        components = tuple(
            sorted(
                (
                    ComponentBinding(
                        "CANDIDATE",
                        _identifier(evaluation.get("candidate_id"), "candidate_id"),
                        BindingKind.CONTRACT,
                        _sha256(
                            contract.get("candidate_contract_sha256"),
                            "candidate_contract_sha256",
                        ),
                    ),
                    ComponentBinding(
                        "CHALLENGE",
                        _identifier(challenge.get("challenge_id"), "challenge_id"),
                        BindingKind.CONTRACT,
                        _sha256(
                            contract.get("challenge_contract_sha256"),
                            "challenge_contract_sha256",
                        ),
                    ),
                    ComponentBinding(
                        "EVALUATOR",
                        _identifier(contract.get("evaluator_id"), "evaluator_id"),
                        BindingKind.CONTRACT,
                        _sha256(
                            contract.get("evaluator_contract_sha256"),
                            "evaluator_contract_sha256",
                        ),
                    ),
                    ComponentBinding(
                        "FIXTURE",
                        None,
                        BindingKind.CONTRACT,
                        _sha256(
                            contract.get("fixture_contract_sha256"),
                            "fixture_contract_sha256",
                        ),
                    ),
                ),
                key=lambda item: canonical_bytes(item.to_dict()),
            )
        )
        observation = InputObservation(
            observation_domain=ObservationDomain.LEGACY_CALIBRATION,
            adapter_id=self.adapter_id,
            adapter_contract_sha256=self.adapter_contract_sha256,
            source_record_id=_identifier(record.get("run_id"), "run_id"),
            source_schema_version=_text(record.get("schema_version"), "schema_version"),
            source_record_id_pointer="/run_id",
            source_file_sha256=bytes_digest(raw),
            source_contract_sha256=_sha256(
                execution.get("run_contract_sha256"),
                "run_contract_sha256",
            ),
            selected_value_pointer=LEGACY_OBSERVATION_POINTER,
            selected_value_digest_domain=LEGACY_SELECTION_DOMAIN,
            selected_value_sha256=domain_digest(LEGACY_SELECTION_DOMAIN, evaluation),
            source_bytes=raw,
        )
        return CaseBinding(
            authority_bindings=authorities,
            component_bindings=components,
            observation=observation,
            research_basis=basis,
            research_ledger=research_ledger,
        )


class GenericInquiryInputAdapter:
    adapter_id = GENERIC_RECORD_ADAPTER_ID
    adapter_contract_sha256 = _plain_domain_digest(
        "creib.semantic-forge.inquiry-input-adapter-contract.v1",
        _GENERIC_ADAPTER_CONTRACT,
    )

    def adapt_record(
        self,
        record: dict[str, Any],
        raw: bytes,
        *,
        repo_root: Path,
        research_ledger: ResearchLedgerBinding,
    ) -> CaseBinding:
        del repo_root
        _validate_schema(record, "inquiry-input-v1.schema.json")
        if record.get("input_id") != compute_inquiry_input_id(record):
            raise RecordError("inquiry input content-addressed ID mismatch")
        if record.get("semantic_verdict") is not None:
            raise PolicyViolation("inquiry input cannot contain a semantic verdict")
        observation_value = _object(record.get("observation"), "observation")
        if observation_value.get("semantic_verdict") is not None:
            raise PolicyViolation("inquiry input observation cannot contain a semantic verdict")
        try:
            origin = ObservationDomain(observation_value["observation_domain"])
        except (KeyError, TypeError, ValueError) as exc:
            raise RecordError("inquiry input observation domain is unsupported") from exc
        authorities = tuple(
            _parse_authority_binding(item)
            for item in _array(record.get("authority_bindings"), "authority_bindings")
        )
        components = tuple(
            _parse_component_binding(item)
            for item in _array(record.get("component_bindings"), "component_bindings")
        )
        _canonical_tuple(authorities, "authority_bindings", nonempty=True)
        _canonical_tuple(components, "component_bindings", nonempty=True)
        raw_basis = record.get("research_basis")
        basis = (
            None
            if raw_basis is None
            else ResearchBasis.from_dict(_object(raw_basis, "research_basis"))
        )
        selected_value = _json_pointer(
            record,
            GENERIC_OBSERVATION_POINTER,
            "generic inquiry observation pointer",
        )
        observation = InputObservation(
            observation_domain=origin,
            adapter_id=self.adapter_id,
            adapter_contract_sha256=self.adapter_contract_sha256,
            source_record_id=_identifier(record.get("input_id"), "input_id"),
            source_schema_version=_text(record.get("schema_version"), "schema_version"),
            source_record_id_pointer="/input_id",
            source_file_sha256=bytes_digest(raw),
            source_contract_sha256=_sha256(
                record.get("producer_contract_sha256"),
                "producer_contract_sha256",
            ),
            selected_value_pointer=GENERIC_OBSERVATION_POINTER,
            selected_value_digest_domain=GENERIC_SELECTION_DOMAIN,
            selected_value_sha256=domain_digest(
                GENERIC_SELECTION_DOMAIN,
                selected_value,
            ),
            source_bytes=raw,
        )
        return CaseBinding(
            authority_bindings=authorities,
            component_bindings=components,
            observation=observation,
            research_basis=basis,
            research_ledger=research_ledger,
        )


def default_adapter_registry() -> AdapterRegistry:
    return AdapterRegistry((LegacyCalibrationAdapter(), GenericInquiryInputAdapter()))


def legacy_calibration_binding_projection(case_binding: CaseBinding) -> dict[str, object]:
    """Project a legacy-adapted case back to the exact v2 flat binding shape."""

    if type(case_binding) is not CaseBinding:
        raise TypeError("case_binding must be CaseBinding")
    observation = case_binding.observation
    if observation.adapter_id != LEGACY_CALIBRATION_ADAPTER_ID:
        raise PolicyViolation("legacy projection requires the calibration adapter")
    if case_binding.research_basis is None:
        raise PolicyViolation("legacy calibration projection requires its research basis")
    authorities = {item.role: item for item in case_binding.authority_bindings}
    if set(authorities) != {"SEMANTIC_AUTHORITY"}:
        raise RecordError("legacy calibration authority binding changed")
    components = {item.role: item for item in case_binding.component_bindings}
    if set(components) != {"CANDIDATE", "CHALLENGE", "EVALUATOR", "FIXTURE"}:
        raise RecordError("legacy calibration component bindings changed")
    candidate = components["CANDIDATE"]
    challenge = components["CHALLENGE"]
    evaluator = components["EVALUATOR"]
    fixture = components["FIXTURE"]
    basis = case_binding.research_basis
    return {
        "run_record_file_sha256": observation.source_file_sha256,
        "run_id": observation.source_record_id,
        "run_contract_sha256": observation.source_contract_sha256,
        "authority_sha256": authorities["SEMANTIC_AUTHORITY"].file_sha256,
        "candidate_id": candidate.subject_id,
        "candidate_contract_sha256": candidate.sha256,
        "challenge_id": challenge.subject_id,
        "challenge_contract_sha256": challenge.sha256,
        "fixture_contract_sha256": fixture.sha256,
        "evaluator_id": evaluator.subject_id,
        "evaluator_contract_sha256": evaluator.sha256,
        "observation_pointer": observation.selected_value_pointer,
        "observation_sha256": observation.selected_value_sha256,
        "observation_kind": OBSERVATION_KIND,
        "issue_id": basis.issue.issue_id,
        "issue_sha256": basis.issue_sha256,
        "warrant_id": basis.warrant.warrant_id,
        "warrant_sha256": basis.warrant_sha256,
        "research_ledger": case_binding.research_ledger.to_dict(),
    }


def compute_locus_assessment_id(record: Mapping[str, object]) -> str:
    return _record_id("LA", LOCUS_ASSESSMENT_SCHEMA, _without(record, "assessment_id"))


def make_locus_assessment(
    *,
    loci: tuple[str, ...],
    mechanism: str,
    relevance: str,
    discriminator: str,
    scope: str,
    uncertainty_location: str,
    depends_on_assessment_ids: tuple[str, ...] = (),
) -> dict[str, object]:
    body: dict[str, object] = {
        "status": "LIVE",
        "loci": sorted(loci),
        "mechanism": mechanism,
        "relevance": relevance,
        "discriminator": discriminator,
        "scope": scope,
        "uncertainty_location": uncertainty_location,
        "depends_on_assessment_ids": sorted(depends_on_assessment_ids),
        "epistemic_effect": "CRITICISM_ONLY",
        "can_establish_unique_cause": False,
    }
    record = {**body, "assessment_id": _record_id("LA", LOCUS_ASSESSMENT_SCHEMA, body)}
    _validate_locus_assessment(record, "locus_assessment")
    return record


def _validate_locus_assessment(value: Any, where: str) -> dict[str, object]:
    record = _object(value, where)
    expected = {
        "assessment_id",
        "status",
        "loci",
        "mechanism",
        "relevance",
        "discriminator",
        "scope",
        "uncertainty_location",
        "depends_on_assessment_ids",
        "epistemic_effect",
        "can_establish_unique_cause",
    }
    _exact_keys(record, expected, where)
    if record.get("assessment_id") != compute_locus_assessment_id(record):
        raise RecordError(f"{where} content-addressed ID mismatch")
    if record.get("status") != "LIVE":
        raise PolicyViolation(f"{where} must remain LIVE")
    loci = _canonical_strings(record.get("loci"), f"{where}.loci", nonempty=True)
    if not set(loci).issubset(_LOCUS_VALUES):
        raise PolicyViolation(f"{where} contains an unsupported locus")
    for field_name in ("mechanism", "relevance", "discriminator", "scope"):
        _text(record.get(field_name), f"{where}.{field_name}")
    location = _text(record.get("uncertainty_location"), f"{where}.uncertainty_location")
    if location not in set(_LOCATION_ROUTE_INTENT).union({"UNLOCATED"}):
        raise PolicyViolation(f"{where} contains an unsupported uncertainty location")
    dependencies = _canonical_strings(
        record.get("depends_on_assessment_ids"),
        f"{where}.depends_on_assessment_ids",
    )
    if record["assessment_id"] in dependencies:
        raise PolicyViolation("a locus assessment cannot depend on itself")
    if record.get("epistemic_effect") != "CRITICISM_ONLY" or record.get(
        "can_establish_unique_cause"
    ) is not False:
        raise PolicyViolation("locus assessment changed a non-inductive boundary")
    return record


def _validate_locus_assessments(value: Iterable[Any]) -> tuple[dict[str, object], ...]:
    assessments = tuple(
        _validate_locus_assessment(item, f"locus_assessments[{index}]")
        for index, item in enumerate(value)
    )
    ids = tuple(str(item["assessment_id"]) for item in assessments)
    if len(ids) != len(set(ids)):
        raise RecordError("locus assessment IDs must be unique")
    if ids != tuple(sorted(ids)):
        raise RecordError("locus assessments must use canonical assessment-ID order")
    by_id = {str(item["assessment_id"]): item for item in assessments}
    for assessment in assessments:
        unknown = sorted(
            set(assessment["depends_on_assessment_ids"]).difference(by_id)  # type: ignore[arg-type]
        )
        if unknown:
            raise PolicyViolation(f"locus assessment dependencies are absent: {unknown}")
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(assessment_id: str) -> None:
        if assessment_id in visiting:
            raise PolicyViolation("locus assessment dependency graph contains a cycle")
        if assessment_id in visited:
            return
        visiting.add(assessment_id)
        for dependency in by_id[assessment_id]["depends_on_assessment_ids"]:  # type: ignore[index]
            visit(str(dependency))
        visiting.remove(assessment_id)
        visited.add(assessment_id)

    for assessment_id in ids:
        visit(assessment_id)
    return assessments


def available_attack_targets(case_binding: CaseBinding) -> tuple[dict[str, object], ...]:
    if type(case_binding) is not CaseBinding:
        raise TypeError("case_binding must be CaseBinding")
    basis = case_binding.research_basis
    if basis is None:
        return ()
    targets: list[dict[str, object]] = []
    for rival in basis.issue.rivals:
        for falsifier in rival.falsifier_conditions:
            body: dict[str, object] = {
                "issue_sha256": basis.issue_sha256,
                "warrant_sha256": basis.warrant_sha256,
                "rival_id": rival.rival_id,
                "rival_claim": rival.claim,
                "falsifier_condition": falsifier,
            }
            targets.append(
                {
                    **body,
                    "attack_target_id": _record_id("AT", ATTACK_TARGET_DOMAIN, body),
                }
            )
    targets.sort(key=lambda item: str(item["attack_target_id"]))
    return tuple(targets)


def compute_next_action_id(record: Mapping[str, object]) -> str:
    return _record_id("NA", NEXT_ACTION_SCHEMA, _without(record, "action_id"))


def make_next_action(
    case_binding: CaseBinding,
    *,
    selected_assessment_ids: tuple[str, ...],
    route_intent: str,
    action: str,
    selection_basis: str,
    reason: str,
    attack_target_ids: tuple[str, ...] = (),
) -> dict[str, object]:
    selected = tuple(sorted(selected_assessment_ids))
    target_ids = tuple(sorted(attack_target_ids))
    research_target: dict[str, object] | None = None
    if route_intent == GenericInquiryRoute.EXTERNAL_RESEARCH_REQUIRED.value:
        basis = case_binding.research_basis
        if basis is None:
            raise PolicyViolation("external action requires an exact research basis")
        if not target_ids:
            raise PolicyViolation("external action requires an exact attack-target subset")
        research_target = {
            "case_binding_id": case_binding.case_binding_id,
            "issue_id": basis.issue.issue_id,
            "issue_sha256": basis.issue_sha256,
            "warrant_id": basis.warrant.warrant_id,
            "warrant_sha256": basis.warrant_sha256,
            "attack_target_ids": list(target_ids),
        }
    elif target_ids:
        raise PolicyViolation("only an external action may select attack targets")
    body: dict[str, object] = {
        "selected_assessment_ids": list(selected),
        "route_intent": route_intent,
        "action": action,
        "selection_basis": selection_basis,
        "reason": reason,
        "research_target": research_target,
        "epistemic_effect": "SCHEDULING_ONLY",
        "can_rank_semantic_truth": False,
    }
    record = {**body, "action_id": _record_id("NA", NEXT_ACTION_SCHEMA, body)}
    return record


def _validate_next_action(
    value: Any,
    *,
    case_binding: CaseBinding,
    assessments: tuple[dict[str, object], ...],
    attack_targets: tuple[dict[str, object], ...],
) -> dict[str, object]:
    action = _object(value, "next_action")
    expected = {
        "action_id",
        "selected_assessment_ids",
        "route_intent",
        "action",
        "selection_basis",
        "reason",
        "research_target",
        "epistemic_effect",
        "can_rank_semantic_truth",
    }
    _exact_keys(action, expected, "next_action")
    if action.get("action_id") != compute_next_action_id(action):
        raise RecordError("next action content-addressed ID mismatch")
    selected = _canonical_strings(
        action.get("selected_assessment_ids"),
        "next_action.selected_assessment_ids",
        nonempty=True,
    )
    assessment_by_id = {str(item["assessment_id"]): item for item in assessments}
    unknown = sorted(set(selected).difference(assessment_by_id))
    if unknown:
        raise PolicyViolation(f"next action selects absent assessments: {unknown}")
    frontier = {
        assessment_id
        for assessment_id, assessment in assessment_by_id.items()
        if not assessment["depends_on_assessment_ids"]
    }
    blocked = sorted(set(selected).difference(frontier))
    if blocked:
        raise PolicyViolation(f"next action selects assessments behind dependencies: {blocked}")
    route_intent = _text(action.get("route_intent"), "next_action.route_intent")
    if route_intent not in {item.value for item in GenericInquiryRoute}:
        raise PolicyViolation("next action has an unsupported route intent")
    if route_intent.startswith("AWAITING_"):
        raise PolicyViolation("a next action cannot select a waiting route")
    for assessment_id in selected:
        location = str(assessment_by_id[assessment_id]["uncertainty_location"])
        expected_route = _LOCATION_ROUTE_INTENT.get(location)
        if expected_route is None:
            raise PolicyViolation("an UNLOCATED criticism cannot be scheduled")
        if expected_route != route_intent:
            raise PolicyViolation("next action conflicts with an assessment location")
    selection_basis = _text(action.get("selection_basis"), "next_action.selection_basis")
    if selection_basis not in _SELECTION_BASES:
        raise PolicyViolation("next action has an unsupported selection basis")
    if selection_basis == "SHARED_ACTION_FOR_MULTIPLE_LOCI" and len(selected) < 2:
        raise PolicyViolation("shared action selection requires multiple assessments")
    if len(selected) > 1 and selection_basis != "SHARED_ACTION_FOR_MULTIPLE_LOCI":
        raise PolicyViolation("multiple assessments require a declared shared action")
    _text(action.get("action"), "next_action.action")
    _text(action.get("reason"), "next_action.reason")
    if action.get("epistemic_effect") != "SCHEDULING_ONLY" or action.get(
        "can_rank_semantic_truth"
    ) is not False:
        raise PolicyViolation("next action changed its scheduling-only boundary")

    research_target = action.get("research_target")
    if route_intent == GenericInquiryRoute.EXTERNAL_RESEARCH_REQUIRED.value:
        basis = case_binding.research_basis
        if basis is None:
            raise PolicyViolation("external action requires an exact research basis")
        target = _object(research_target, "next_action.research_target")
        _exact_keys(
            target,
            {
                "case_binding_id",
                "issue_id",
                "issue_sha256",
                "warrant_id",
                "warrant_sha256",
                "attack_target_ids",
            },
            "next_action.research_target",
        )
        expected_binding = {
            "case_binding_id": case_binding.case_binding_id,
            "issue_id": basis.issue.issue_id,
            "issue_sha256": basis.issue_sha256,
            "warrant_id": basis.warrant.warrant_id,
            "warrant_sha256": basis.warrant_sha256,
        }
        if any(target.get(key) != value for key, value in expected_binding.items()):
            raise PolicyViolation("external action changed its exact research basis")
        selected_targets = _canonical_strings(
            target.get("attack_target_ids"),
            "next_action.research_target.attack_target_ids",
            nonempty=True,
        )
        available_ids = {str(item["attack_target_id"]) for item in attack_targets}
        unavailable = sorted(set(selected_targets).difference(available_ids))
        if unavailable:
            raise PolicyViolation(
                f"external action selects unavailable attack targets: {unavailable}"
            )
    elif research_target is not None:
        raise PolicyViolation("a non-external action cannot carry a research target")
    return action


def _generic_case_digest(
    case_binding: CaseBinding,
    assessments: tuple[dict[str, object], ...],
    next_action: dict[str, object] | None,
) -> str:
    return domain_digest(
        "creib.semantic-forge.adaptive-inquiry-case.v3",
        {
            "case_binding": case_binding.to_dict(),
            "locus_assessments": list(assessments),
            "next_action": next_action,
        },
    )


def _build_generic_inquiry_plan(
    case_binding: CaseBinding,
    locus_assessments: Iterable[dict[str, object]],
    next_action: dict[str, object] | None,
) -> dict[str, object]:
    if type(case_binding) is not CaseBinding:
        raise TypeError("case_binding must be CaseBinding")
    parse_case_binding(case_binding.to_dict())
    assessments = _validate_locus_assessments(locus_assessments)
    targets = available_attack_targets(case_binding)
    checked_action: dict[str, object] | None = None
    if not assessments:
        if next_action is not None:
            raise PolicyViolation("an action cannot precede human locus assessment")
        route = GenericInquiryRoute.AWAITING_HUMAN_TRIAGE
        reason = "An exact observation cannot locate its own failure locus."
    elif next_action is None:
        route = GenericInquiryRoute.AWAITING_HUMAN_ACTION_SELECTION
        reason = "Live human criticism assessments exist; no work action was selected."
    else:
        checked_action = _validate_next_action(
            next_action,
            case_binding=case_binding,
            assessments=assessments,
            attack_targets=targets,
        )
        route = GenericInquiryRoute(str(checked_action["route_intent"]))
        reason = "The human-selected action chooses a work queue without ranking truth."
    case_sha256 = _generic_case_digest(case_binding, assessments, checked_action)
    body: dict[str, object] = {
        "$schema": GENERIC_PLAN_SCHEMA_REF,
        "schema_version": GENERIC_PLAN_SCHEMA,
        "record_type": "adaptive_inquiry_plan",
        "case_sha256": case_sha256,
        "case_binding": case_binding.to_dict(),
        "locus_assessments": list(assessments),
        "live_locus_assessment_ids": [
            str(item["assessment_id"]) for item in assessments
        ],
        "next_action": checked_action,
        "selected_action_id": (
            None if checked_action is None else checked_action["action_id"]
        ),
        "available_attack_targets": list(targets),
        "route": route.value,
        "route_reason": reason,
        "origin_can_select_locus_or_route": False,
        "publication_authority": False,
        "epistemic_status": "UNRESOLVED",
        "epistemic_effect": ROUTING_EFFECT,
        "epistemic_limit": NON_INDUCTIVE_LIMIT,
        "semantic_verdict": None,
    }
    return {**body, "plan_id": _record_id("AIP", GENERIC_PLAN_SCHEMA, body)}


def build_generic_inquiry_plan(
    case_binding: CaseBinding,
    *,
    locus_assessments: Iterable[dict[str, object]] = (),
    next_action: dict[str, object] | None = None,
) -> dict[str, object]:
    """Build a non-publishing v3 route preview from explicit human inputs."""

    plan = _build_generic_inquiry_plan(case_binding, locus_assessments, next_action)
    _validate_schema(plan, "adaptive-inquiry-v3.schema.json")
    return plan


def validate_generic_inquiry_plan(plan: dict[str, object]) -> None:
    _validate_schema(plan, "adaptive-inquiry-v3.schema.json")
    if plan.get("schema_version") != GENERIC_PLAN_SCHEMA:
        raise RecordError("generic inquiry plan has an unsupported schema version")
    case_binding = parse_case_binding(plan.get("case_binding"))
    assessments = tuple(
        _object(item, "locus_assessment")
        for item in _array(plan.get("locus_assessments"), "locus_assessments")
    )
    action_value = plan.get("next_action")
    action = None if action_value is None else _object(action_value, "next_action")
    expected = _build_generic_inquiry_plan(case_binding, assessments, action)
    if plan != expected:
        raise PolicyViolation(
            "generic inquiry plan differs from exact deterministic regeneration"
        )


__all__ = [
    "AdapterRegistry",
    "AuthorityBinding",
    "BindingKind",
    "CaseBinding",
    "ComponentBinding",
    "GENERIC_RECORD_ADAPTER_ID",
    "GenericInquiryInputAdapter",
    "GenericInquiryRoute",
    "InputObservation",
    "LEGACY_CALIBRATION_ADAPTER_ID",
    "LegacyCalibrationAdapter",
    "ObservationDomain",
    "ResearchBasis",
    "ResearchLedgerBinding",
    "available_attack_targets",
    "build_generic_inquiry_plan",
    "build_inquiry_input_record",
    "compute_inquiry_input_id",
    "compute_locus_assessment_id",
    "compute_next_action_id",
    "default_adapter_registry",
    "legacy_calibration_binding_projection",
    "make_locus_assessment",
    "make_next_action",
    "parse_case_binding",
    "parse_input_observation",
    "validate_generic_inquiry_plan",
]
