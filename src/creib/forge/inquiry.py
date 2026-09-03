"""Additive adaptive-inquiry protocol for the semantic-model forge.

The protocol routes work; it does not decide CR-1.0 semantics.  A mechanical
calibration observation remains only a criticism candidate until a separately
supplied human triage record preserves every live criticism assessment and selects at
most one operational action.  External reports may
sharpen a criticism, but their number, agreement, provider ranking, or absence
cannot promote a model or close a semantic question.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
import errno
from functools import lru_cache
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Iterable

from creib.canonical import bytes_digest, canonical_bytes, domain_digest
from creib.errors import PolicyViolation, RecordError
from creib.strict_json import loads_strict

from .calibration import dumps_calibration_report
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
from .research import ResearchLedger, parse_event_research_entry, parse_research_ledger
from .schema_validation import load_local_schema_catalog


LEGACY_TRIAGE_SCHEMA = "creib.semantic-forge.human-failure-triage.v1"
LEGACY_PLAN_SCHEMA = "creib.semantic-forge.adaptive-inquiry-plan.v1"
LEGACY_QUESTION_SCHEMA = "creib.semantic-forge.critical-question.v1"
LEGACY_EVENT_SCHEMA = "creib.semantic-forge.inquiry-event.v1"
LEGACY_ADAPTIVE_SCHEMA_REF = "../schema/adaptive-inquiry.schema.json"
LEGACY_EVENT_SCHEMA_REF = "../schema/inquiry-event.schema.json"

TRIAGE_SCHEMA = "creib.semantic-forge.human-failure-triage.v2"
PLAN_SCHEMA = "creib.semantic-forge.adaptive-inquiry-plan.v2"
QUESTION_SCHEMA = "creib.semantic-forge.critical-question.v2"
EVENT_SCHEMA = "creib.semantic-forge.inquiry-event.v2"
ADAPTIVE_SCHEMA_REF = "../schema/adaptive-inquiry-v2.schema.json"
EVENT_SCHEMA_REF = "../schema/inquiry-event-v2.schema.json"
INQUIRY_LEDGER_ID = "SMF-INQUIRY-CR-1-0"

OBSERVATION_POINTER = "/fixture_evaluations/weak_typed_role_projection"
OBSERVATION_KIND = "CRITICISM_CANDIDATE_NOT_SEMANTIC_VERDICT"
ROUTING_EFFECT = "WORKFLOW_ROUTING_ONLY"
EVENT_EFFECT = "MAY_CRITICIZE_OR_ROUTE_WORK_ONLY"
LEGACY_EVENT_RESEARCH_ENTRY_DOMAIN = (
    "creib.semantic-forge.inquiry-event-entry-binding.v1"
)
EVENT_RESEARCH_ENTRY_DOMAIN = "creib.semantic-forge.inquiry-event-entry-binding.v2"
EVENT_RESEARCH_ENTRY_SCHEMA = "creib.semantic-forge.event-research-entry.v2"
ATTACK_TARGET_DOMAIN = "creib.semantic-forge.attack-target.v1"

LOCUS_ASSESSMENT_SCHEMA = "creib.semantic-forge.locus-assessment.v1"
NEXT_ACTION_SCHEMA = "creib.semantic-forge.next-action.v1"
ASSESSMENT_DISPOSITION_SCHEMA = (
    "creib.semantic-forge.assessment-disposition.v1"
)
EVIDENCE_BINDING_SCHEMA = (
    "creib.semantic-forge.disposition-evidence-binding.v1"
)
EVIDENCE_RECORD_DOMAIN = "creib.semantic-forge.disposition-evidence-record.v1"
EVIDENCE_SELECTION_DOMAIN = (
    "creib.semantic-forge.disposition-evidence-selection.v1"
)

_LOCUS_VALUES = frozenset({"CANDIDATE", "AUXILIARY", "TEST", "SCOPE"})
_ROUTE_INTENTS = frozenset(
    {
        "INTERNAL_HARNESS_WORK",
        "INTERNAL_MODEL_WORK",
        "AUTHORITY_REVIEW",
        "EXTERNAL_RESEARCH_REQUIRED",
    }
)
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

_SHA256 = "sha256:"


class InquiryRoute(str, Enum):
    AWAITING_HUMAN_TRIAGE = "AWAITING_HUMAN_TRIAGE"
    AWAITING_HUMAN_ACTION_SELECTION = "AWAITING_HUMAN_ACTION_SELECTION"
    AWAITING_HUMAN_REASSESSMENT = "AWAITING_HUMAN_REASSESSMENT"
    INTERNAL_HARNESS_WORK = "INTERNAL_HARNESS_WORK"
    INTERNAL_MODEL_WORK = "INTERNAL_MODEL_WORK"
    AUTHORITY_REVIEW = "AUTHORITY_REVIEW"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    POLICY_BLOCKED = "POLICY_BLOCKED"
    EXTERNAL_RESEARCH_REQUIRED = "EXTERNAL_RESEARCH_REQUIRED"
    RESEARCH_IN_PROGRESS = "RESEARCH_IN_PROGRESS"
    AWAITING_HUMAN_REVIEW = "AWAITING_HUMAN_REVIEW"
    INTERNAL_INTEGRATION_REQUIRED = "INTERNAL_INTEGRATION_REQUIRED"
    NO_NEW_RESEARCH_UNDER_CURRENT_PROTOCOL = (
        "NO_NEW_RESEARCH_UNDER_CURRENT_PROTOCOL"
    )


class QuestionState(str, Enum):
    PROPOSED = "PROPOSED"
    ACTIVE = "ACTIVE"
    AWAITING_HUMAN_REVIEW = "AWAITING_HUMAN_REVIEW"
    RETIRED_WITH_CRITICISM_CANDIDATE = "RETIRED_WITH_CRITICISM_CANDIDATE"
    RETIRED_NONDISCRIMINATING = "RETIRED_NONDISCRIMINATING"
    RETIRED_MISFRAMED = "RETIRED_MISFRAMED"
    RETIRED_OUT_OF_SCOPE = "RETIRED_OUT_OF_SCOPE"
    STALE_BY_MODEL_CHANGE = "STALE_BY_MODEL_CHANGE"


class InquiryError(RecordError):
    """Stable, machine-classifiable adaptive-inquiry failure."""

    def __init__(self, error_code: str, message: str) -> None:
        super().__init__(message)
        self.error_code = error_code


@dataclass(frozen=True)
class InquiryState:
    """Verified state derived from one selected append-only event head."""

    head_event_id: str | None
    events: tuple[dict[str, object], ...]
    question_states: dict[str, QuestionState]
    questions: dict[str, dict[str, object]]


@dataclass(frozen=True)
class HumanTriageState:
    """Verified state derived from one selected append-only triage head."""

    head_triage_id: str | None
    triages: tuple[dict[str, object], ...]


def _object(value: Any, where: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise RecordError(f"{where} must be an object")
    return value


def _string(value: Any, where: str) -> str:
    if type(value) is not str or not value.strip():
        raise RecordError(f"{where} must be a non-empty string")
    return value


def _iso_date(value: Any, where: str) -> str:
    text = _string(value, where)
    try:
        parsed = date.fromisoformat(text)
    except ValueError as exc:
        raise RecordError(f"{where} must be an ISO 8601 calendar date") from exc
    if parsed.isoformat() != text:
        raise RecordError(f"{where} must use canonical YYYY-MM-DD form")
    return text


def _canonical_unique_strings(
    value: Any,
    where: str,
    *,
    nonempty: bool = False,
) -> tuple[str, ...]:
    if type(value) is not list:
        raise RecordError(f"{where} must be an array")
    checked = tuple(_string(item, f"{where} item") for item in value)
    if nonempty and not checked:
        raise RecordError(f"{where} must not be empty")
    if len(checked) != len(set(checked)):
        raise RecordError(f"{where} must contain unique values")
    if checked != tuple(sorted(checked)):
        raise RecordError(f"{where} must use canonical lexical order")
    return checked


def _research_ledger_binding_dates(
    value: Any,
    where: str,
) -> tuple[str, str]:
    binding = _object(value, where)
    created_on = _iso_date(
        binding.get("created_on"),
        f"{where}.created_on",
    )
    as_of_date = _iso_date(
        binding.get("as_of_date"),
        f"{where}.as_of_date",
    )
    if as_of_date > created_on:
        raise RecordError(
            f"{where}.as_of_date cannot be after {where}.created_on"
        )
    return created_on, as_of_date


def _validate_research_ledger_object_binding(
    research_ledger: ResearchLedger,
    value: Any,
    where: str,
) -> dict[str, Any]:
    if type(research_ledger) is not ResearchLedger:
        raise TypeError("research_ledger must be ResearchLedger")
    binding = _object(value, where)
    _research_ledger_binding_dates(binding, where)
    expected: dict[str, object] = {
        "ledger_id": research_ledger.ledger_id,
        "created_on": research_ledger.created_on,
        "as_of_date": research_ledger.as_of_date,
        "record_sha256": domain_digest(
            research_ledger.schema_version,
            research_ledger.to_dict(),
        ),
    }
    for field, required in expected.items():
        if binding.get(field) != required:
            raise PolicyViolation(
                f"{where}.{field} does not match the supplied ResearchLedger"
            )
    return binding


def _read_snapshot(path: Path, where: str) -> tuple[Any, bytes]:
    if not isinstance(path, Path):
        raise TypeError(f"{where} path must be pathlib.Path")
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise InquiryError("INQUIRY_INPUT_READ_FAILED", f"cannot read {where}: {exc}") from exc
    try:
        source = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InquiryError("INQUIRY_INPUT_NOT_UTF8", f"{where} is not UTF-8") from exc
    try:
        return loads_strict(source), raw
    except (RecordError, RecursionError) as exc:
        raise InquiryError("INQUIRY_INPUT_INVALID_JSON", f"invalid {where}: {exc}") from exc


def _hex_from_domain(value: str) -> str:
    if not value.startswith(_SHA256) or len(value) != 71:
        raise RecordError("internal domain digest has an unexpected shape")
    return value.removeprefix(_SHA256)


def _record_id(prefix: str, domain: str, body: dict[str, object]) -> str:
    return f"{prefix}:{_hex_from_domain(domain_digest(domain, body))}"


def _without(record: dict[str, Any], key: str) -> dict[str, object]:
    return {name: value for name, value in record.items() if name != key}


def compute_human_triage_id(record: dict[str, object]) -> str:
    """Compute an ID for a human-authored triage record without creating it."""

    if type(record) is not dict:
        raise TypeError("human triage must be a dictionary")
    version = record.get("schema_version")
    if version not in {LEGACY_TRIAGE_SCHEMA, TRIAGE_SCHEMA}:
        raise RecordError("human triage has an unsupported schema_version")
    body = _without(record, "triage_id")
    return _record_id("HT", str(version), body)


def compute_locus_assessment_id(record: dict[str, object]) -> str:
    """Content-address one live, fallible failure-locus assessment."""

    if type(record) is not dict:
        raise TypeError("locus assessment must be a dictionary")
    return _record_id(
        "LA",
        LOCUS_ASSESSMENT_SCHEMA,
        _without(record, "assessment_id"),
    )


def compute_evidence_binding_id(record: dict[str, object]) -> str:
    """Content-address one embedded disposition-evidence binding."""

    if type(record) is not dict:
        raise TypeError("evidence binding must be a dictionary")
    return _record_id(
        "EB",
        EVIDENCE_BINDING_SCHEMA,
        _without(record, "evidence_binding_id"),
    )


def compute_assessment_disposition_id(record: dict[str, object]) -> str:
    """Content-address one fallible human disposition of an exact criticism."""

    if type(record) is not dict:
        raise TypeError("assessment disposition must be a dictionary")
    return _record_id(
        "AD",
        ASSESSMENT_DISPOSITION_SCHEMA,
        _without(record, "disposition_id"),
    )


def compute_next_action_id(record: dict[str, object]) -> str:
    """Content-address one scheduling action without ranking semantic truth."""

    if type(record) is not dict:
        raise TypeError("next action must be a dictionary")
    return _record_id("NA", NEXT_ACTION_SCHEMA, _without(record, "action_id"))


def compute_question_id(record: dict[str, object]) -> str:
    if type(record) is not dict:
        raise TypeError("critical question must be a dictionary")
    version = record.get("schema_version")
    if version not in {LEGACY_QUESTION_SCHEMA, QUESTION_SCHEMA}:
        raise RecordError("critical question has an unsupported schema_version")
    return _record_id("IQ", str(version), _without(record, "question_id"))


def compute_adaptive_inquiry_plan_id(record: dict[str, object]) -> str:
    if type(record) is not dict:
        raise TypeError("adaptive inquiry plan must be a dictionary")
    version = record.get("schema_version")
    if version not in {LEGACY_PLAN_SCHEMA, PLAN_SCHEMA}:
        raise RecordError("adaptive inquiry plan has an unsupported schema_version")
    return _record_id("AIP", str(version), _without(record, "plan_id"))


def compute_event_id(record: dict[str, object]) -> str:
    if type(record) is not dict:
        raise TypeError("inquiry event must be a dictionary")
    version = record.get("schema_version")
    if version not in {LEGACY_EVENT_SCHEMA, EVENT_SCHEMA}:
        raise RecordError("inquiry event has an unsupported schema_version")
    return _record_id("IE", str(version), _without(record, "event_id"))


def _content_id(value: Any, prefix: str, where: str) -> str:
    checked = _string(value, where)
    if not checked.startswith(f"{prefix}:") or len(checked) != len(prefix) + 65:
        raise RecordError(f"{where} has an invalid shape")
    suffix = checked.removeprefix(f"{prefix}:")
    if any(character not in "0123456789abcdef" for character in suffix):
        raise RecordError(f"{where} has an invalid shape")
    return checked


def _compute_attack_target_id(record: dict[str, object]) -> str:
    return _record_id(
        "AT",
        ATTACK_TARGET_DOMAIN,
        _without(record, "attack_target_id"),
    )


@lru_cache(maxsize=1)
def _schema_catalog() -> Any:
    """Build the immutable local registry once for this process."""

    return load_local_schema_catalog()


def _validate_with_schema(record: dict[str, object], schema_name: str) -> None:
    _schema_catalog().validate(record, schema_name)


def verify_issue_warrant_binding(
    issue: Issue,
    warrant: ResearchWarrant,
) -> None:
    """Require the complete warrant to be the deterministic projection of Issue."""

    if type(issue) is not Issue:
        raise TypeError("issue must be Issue")
    if type(warrant) is not ResearchWarrant:
        raise TypeError("warrant must be ResearchWarrant")
    expected = generate_research_warrant(
        issue,
        discovery_channels=warrant.discovery_channels,
    )
    if expected is None:
        raise PolicyViolation("the bound issue is not eligible for external research")
    if warrant != expected:
        raise PolicyViolation(
            "research warrant is not the exact deterministic projection of the bound issue"
        )


def _load_verified_run(path: Path, repo_root: Path) -> tuple[dict[str, Any], bytes]:
    decoded, raw = _read_snapshot(path, "calibration run")
    report = _object(decoded, "calibration run")
    try:
        canonical = dumps_calibration_report(report, repo_root=repo_root).encode("utf-8") + b"\n"
    except (RecordError, ValueError, TypeError, RecursionError) as exc:
        raise InquiryError(
            "INQUIRY_RUN_NOT_CURRENT",
            f"calibration run failed its current exact contract: {exc}",
        ) from exc
    if raw != canonical:
        raise InquiryError(
            "INQUIRY_RUN_NONCANONICAL",
            "calibration run must be canonical UTF-8 JSON followed by one newline",
        )
    return report, raw


def _load_research_ledger_snapshot(
    path: Path,
) -> tuple[ResearchLedger, bytes, dict[str, object]]:
    decoded, raw = _read_snapshot(path, "research ledger")
    try:
        ledger = parse_research_ledger(decoded)
    except (RecordError, PolicyViolation, ValueError, TypeError) as exc:
        raise InquiryError(
            "INQUIRY_RESEARCH_LEDGER_INVALID",
            f"research ledger failed its strict runtime contract: {exc}",
        ) from exc
    binding: dict[str, object] = {
        "ledger_id": ledger.ledger_id,
        "created_on": ledger.created_on,
        "as_of_date": ledger.as_of_date,
        "file_sha256": bytes_digest(raw),
        "record_sha256": domain_digest(ledger.schema_version, ledger.to_dict()),
    }
    return ledger, raw, binding


def _extract_bindings(
    report: dict[str, Any],
    run_raw: bytes,
    research_binding: dict[str, object],
) -> tuple[dict[str, object], Issue, ResearchWarrant]:
    try:
        trace = _object(report["corpus_trace"], "calibration corpus_trace")
        issue = parse_issue(trace["selected_external_issue"])
        routing = _object(report["research_routing"], "calibration research_routing")
        warrant = parse_research_warrant(routing["external_role_warrant"])
        verify_issue_warrant_binding(issue, warrant)
        challenge = _object(trace["selected_challenge"], "selected challenge")
        execution = _object(report["execution_contract"], "execution contract")
        evaluations = _object(report["fixture_evaluations"], "fixture evaluations")
        observation = _object(
            evaluations["weak_typed_role_projection"],
            "weak typed-role observation",
        )
        contract = _object(observation["contract_binding"], "observation contract")
        evaluator_contracts = _object(
            execution["evaluator_contract_sha256"],
            "execution evaluator contracts",
        )
    except KeyError as exc:
        raise RecordError(f"calibration run is missing adaptive-inquiry input {exc}") from exc

    exact_pairs = (
        (observation["challenge_id"], challenge["challenge_id"], "challenge ID"),
        (
            contract["challenge_contract_sha256"],
            execution["challenge_contract_sha256"],
            "challenge contract",
        ),
        (
            contract["candidate_contract_sha256"],
            execution["candidate_contract_sha256"],
            "candidate contract",
        ),
        (
            contract["fixture_contract_sha256"],
            execution["fixture_contract_sha256"],
            "fixture contract",
        ),
        (
            contract["evaluator_contract_sha256"],
            evaluator_contracts["weak_typed_role_projection"],
            "evaluator contract",
        ),
        (
            issue.issue_id,
            warrant.issue_id,
            "issue/warrant ID",
        ),
    )
    for actual, expected, label in exact_pairs:
        if actual != expected:
            raise RecordError(f"calibration run has a mismatched {label}")
    if report.get("semantic_verdict") is not None or observation.get("semantic_verdict") is not None:
        raise PolicyViolation("adaptive inquiry requires the calibration semantic verdict to remain null")

    bindings: dict[str, object] = {
        "run_record_file_sha256": bytes_digest(run_raw),
        "run_id": _string(report.get("run_id"), "run_id"),
        "run_contract_sha256": _string(
            execution.get("run_contract_sha256"), "run_contract_sha256"
        ),
        "authority_sha256": _string(
            execution.get("authority_sha256"), "authority_sha256"
        ),
        "candidate_id": _string(observation.get("candidate_id"), "candidate_id"),
        "candidate_contract_sha256": _string(
            contract.get("candidate_contract_sha256"), "candidate_contract_sha256"
        ),
        "challenge_id": _string(challenge.get("challenge_id"), "challenge_id"),
        "challenge_contract_sha256": _string(
            contract.get("challenge_contract_sha256"), "challenge_contract_sha256"
        ),
        "fixture_contract_sha256": _string(
            contract.get("fixture_contract_sha256"), "fixture_contract_sha256"
        ),
        "evaluator_id": _string(contract.get("evaluator_id"), "evaluator_id"),
        "evaluator_contract_sha256": _string(
            contract.get("evaluator_contract_sha256"), "evaluator_contract_sha256"
        ),
        "observation_pointer": OBSERVATION_POINTER,
        "observation_sha256": domain_digest(
            "creib.semantic-forge.criticism-candidate-observation.v1",
            observation,
        ),
        "observation_kind": OBSERVATION_KIND,
        "issue_id": issue.issue_id,
        "issue_sha256": domain_digest(ISSUE_SCHEMA, issue.to_dict()),
        "warrant_id": warrant.warrant_id,
        "warrant_sha256": domain_digest(WARRANT_SCHEMA, warrant.to_dict()),
        "research_ledger": research_binding,
    }
    return bindings, issue, warrant


def _validate_legacy_human_triage(
    triage: dict[str, object],
    *,
    expected_bindings: dict[str, object],
) -> dict[str, object]:
    """Retain validation of immutable v1 history without creating new v1 data."""

    _validate_with_schema(triage, "adaptive-inquiry.schema.json")
    if triage.get("record_type") != "human_failure_triage":
        raise RecordError("triage input is not a human_failure_triage record")
    if triage.get("triage_id") != compute_human_triage_id(triage):
        raise RecordError("human triage content-addressed ID mismatch")
    if triage.get("bindings") != expected_bindings:
        raise PolicyViolation("human triage is not bound to the exact current inquiry inputs")
    ledger_created_on, _snapshot_date = _research_ledger_binding_dates(
        expected_bindings.get("research_ledger"),
        "triage.bindings.research_ledger",
    )
    created_on = _iso_date(triage.get("created_on"), "triage.created_on")
    if created_on < ledger_created_on:
        raise PolicyViolation(
            "human triage created_on precedes the bound research ledger artifact"
        )
    return triage


def _validate_locus_assessments(
    triage: dict[str, object],
    *,
    allow_external_dependencies: bool = False,
) -> tuple[dict[str, object], ...]:
    raw = triage.get("locus_assessments")
    if type(raw) is not list or not raw:
        raise RecordError("triage.locus_assessments must be a non-empty array")
    assessments: list[dict[str, object]] = []
    for index, item in enumerate(raw):
        assessment = _object(item, f"triage.locus_assessments[{index}]")
        assessment_id = _string(
            assessment.get("assessment_id"),
            f"triage.locus_assessments[{index}].assessment_id",
        )
        if assessment_id != compute_locus_assessment_id(assessment):
            raise RecordError("locus assessment content-addressed ID mismatch")
        if assessment.get("status") != "LIVE":
            raise PolicyViolation("every v2 locus assessment must remain LIVE")
        loci = _canonical_unique_strings(
            assessment.get("loci"),
            f"triage.locus_assessments[{index}].loci",
            nonempty=True,
        )
        if not set(loci).issubset(_LOCUS_VALUES):
            raise PolicyViolation("locus assessment contains an unknown locus")
        for field in ("mechanism", "relevance", "discriminator", "scope"):
            _string(
                assessment.get(field),
                f"triage.locus_assessments[{index}].{field}",
            )
        _string(
            assessment.get("uncertainty_location"),
            f"triage.locus_assessments[{index}].uncertainty_location",
        )
        _canonical_unique_strings(
            assessment.get("depends_on_assessment_ids"),
            f"triage.locus_assessments[{index}].depends_on_assessment_ids",
        )
        if assessment.get("epistemic_effect") != "CRITICISM_ONLY":
            raise PolicyViolation("locus assessment changed its epistemic effect")
        if assessment.get("can_establish_unique_cause") is not False:
            raise PolicyViolation("a locus assessment cannot establish a unique cause")
        assessments.append(assessment)

    assessment_ids = tuple(
        _string(item.get("assessment_id"), "locus assessment ID")
        for item in assessments
    )
    if len(assessment_ids) != len(set(assessment_ids)):
        raise RecordError("locus assessment IDs must be unique")
    if assessment_ids != tuple(sorted(assessment_ids)):
        raise RecordError("locus assessments must use canonical assessment_id order")

    by_id = dict(zip(assessment_ids, assessments, strict=True))
    for assessment_id, assessment in by_id.items():
        dependencies = _canonical_unique_strings(
            assessment.get("depends_on_assessment_ids"),
            f"assessment {assessment_id} dependencies",
        )
        for dependency in dependencies:
            _content_id(
                dependency,
                "LA",
                f"assessment {assessment_id} dependency",
            )
        if assessment_id in dependencies:
            raise PolicyViolation("a locus assessment cannot depend on itself")
        unknown = sorted(set(dependencies).difference(by_id))
        if unknown and not allow_external_dependencies:
            raise PolicyViolation(
                f"locus assessment dependencies are absent from this triage: {unknown}"
            )

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(assessment_id: str) -> None:
        if assessment_id in visiting:
            raise PolicyViolation("locus assessment dependency graph contains a cycle")
        if assessment_id in visited:
            return
        visiting.add(assessment_id)
        for dependency in by_id[assessment_id]["depends_on_assessment_ids"]:  # type: ignore[index]
            if dependency in by_id:
                visit(dependency)
        visiting.remove(assessment_id)
        visited.add(assessment_id)

    for assessment_id in assessment_ids:
        visit(assessment_id)
    return tuple(assessments)


_EVIDENCE_KINDS = frozenset(
    {
        "CALIBRATION_RUN",
        "INPUT_BINDING_DELTA",
    }
)
_ASSESSMENT_DISPOSITIONS = frozenset(
    {"RETAINED", "DEFEATED", "STALE_BY_BINDING_CHANGE"}
)
_TERMINAL_ASSESSMENT_DISPOSITIONS = frozenset(
    {"DEFEATED", "STALE_BY_BINDING_CHANGE"}
)


def _json_pointer(value: Any, pointer: Any, where: str) -> Any:
    checked = pointer if type(pointer) is str else None
    if checked is None:
        raise RecordError(f"{where} must be a JSON pointer string")
    if checked == "":
        return value
    if not checked.startswith("/"):
        raise RecordError(f"{where} must be empty or start with '/'")
    current = value
    for raw_token in checked[1:].split("/"):
        index = 0
        decoded: list[str] = []
        while index < len(raw_token):
            character = raw_token[index]
            if character != "~":
                decoded.append(character)
                index += 1
                continue
            if index + 1 >= len(raw_token) or raw_token[index + 1] not in "01":
                raise RecordError(f"{where} contains an invalid JSON pointer escape")
            decoded.append("~" if raw_token[index + 1] == "0" else "/")
            index += 2
        token = "".join(decoded)
        if type(current) is dict:
            if token not in current:
                raise RecordError(f"{where} does not resolve in its record snapshot")
            current = current[token]
        elif type(current) is list:
            if not token.isdigit() or (len(token) > 1 and token.startswith("0")):
                raise RecordError(f"{where} contains an invalid array index")
            array_index = int(token)
            if array_index >= len(current):
                raise RecordError(f"{where} array index is out of range")
            current = current[array_index]
        else:
            raise RecordError(f"{where} traverses a scalar value")
    return current


def _pointer_token(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _changed_binding_pointers(
    previous: Any,
    current: Any,
    pointer: str = "",
) -> tuple[str, ...]:
    if previous == current:
        return ()
    if type(previous) is dict and type(current) is dict:
        changed: list[str] = []
        for key in sorted(set(previous).union(current)):
            child = f"{pointer}/{_pointer_token(key)}"
            if key not in previous or key not in current:
                changed.append(child)
            else:
                changed.extend(
                    _changed_binding_pointers(previous[key], current[key], child)
                )
        return tuple(changed)
    if type(previous) is list and type(current) is list:
        return (pointer,)
    return (pointer,)


def _validate_evidence_binding(
    value: Any,
    where: str,
    *,
    bindings: dict[str, object],
) -> dict[str, object]:
    evidence = _object(value, where)
    expected_fields = {
        "evidence_binding_id",
        "evidence_kind",
        "record_id",
        "record_id_pointer",
        "record_snapshot",
        "record_sha256",
        "selected_value_pointer",
        "selected_value_sha256",
        "bearing",
    }
    if set(evidence) != expected_fields:
        raise RecordError(f"{where} has unexpected or missing fields")
    if evidence.get("evidence_binding_id") != compute_evidence_binding_id(evidence):
        raise RecordError("disposition evidence binding content-addressed ID mismatch")
    kind = _string(evidence.get("evidence_kind"), f"{where}.evidence_kind")
    if kind not in _EVIDENCE_KINDS:
        raise PolicyViolation("assessment disposition has an unsupported evidence kind")
    record_id = _string(evidence.get("record_id"), f"{where}.record_id")
    snapshot = _object(evidence.get("record_snapshot"), f"{where}.record_snapshot")
    if evidence.get("record_sha256") != domain_digest(EVIDENCE_RECORD_DOMAIN, snapshot):
        raise RecordError("disposition evidence record digest mismatch")
    resolved_id = _json_pointer(
        snapshot,
        evidence.get("record_id_pointer"),
        f"{where}.record_id_pointer",
    )
    if resolved_id != record_id:
        raise PolicyViolation("disposition evidence record ID pointer changed its target")
    selected = _json_pointer(
        snapshot,
        evidence.get("selected_value_pointer"),
        f"{where}.selected_value_pointer",
    )
    if evidence.get("selected_value_sha256") != domain_digest(
        EVIDENCE_SELECTION_DOMAIN,
        selected,
    ):
        raise RecordError("disposition evidence selected-value digest mismatch")
    _string(evidence.get("bearing"), f"{where}.bearing")

    if kind == "CALIBRATION_RUN":
        if evidence.get("record_id_pointer") != "/run_id":
            raise PolicyViolation(
                "calibration disposition evidence must identify /run_id"
            )
        expected_observation_pointer = _string(
            bindings.get("observation_pointer"),
            "disposition bindings observation_pointer",
        )
        if evidence.get("selected_value_pointer") != expected_observation_pointer:
            raise PolicyViolation(
                "calibration disposition evidence must select the exact bound observation"
            )
        _validate_with_schema(snapshot, "calibration-run.schema.json")
        embedded_bindings, _issue, _warrant = _extract_bindings(
            snapshot,
            canonical_bytes(snapshot) + b"\n",
            _object(
                bindings.get("research_ledger"),
                "disposition bindings research_ledger",
            ),
        )
        if embedded_bindings != bindings:
            raise PolicyViolation(
                "calibration disposition evidence is not the exact bound run record"
            )
    else:
        if (
            evidence.get("record_id_pointer") != "/record_id"
            or record_id != "TRIAGE-BINDING-DELTA"
        ):
            raise PolicyViolation(
                "input-change evidence must identify the canonical binding-delta record"
            )
    return evidence


def _validate_assessment_dispositions(
    triage: dict[str, object],
    assessments: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    raw = triage.get("assessment_dispositions")
    if type(raw) is not list:
        raise RecordError("triage.assessment_dispositions must be an array")
    assessment_by_id = {
        _string(item.get("assessment_id"), "assessment_id"): item
        for item in assessments
    }
    dispositions: list[dict[str, object]] = []
    for index, item in enumerate(raw):
        where = f"triage.assessment_dispositions[{index}]"
        disposition = _object(item, where)
        if disposition.get("disposition_id") != compute_assessment_disposition_id(
            disposition
        ):
            raise RecordError("assessment disposition content-addressed ID mismatch")
        if disposition.get("schema_version") != ASSESSMENT_DISPOSITION_SCHEMA:
            raise RecordError("assessment disposition changed schema_version")
        if disposition.get("record_type") != "assessment_disposition":
            raise RecordError("assessment disposition changed record_type")
        assessment_id = _content_id(
            disposition.get("assessment_id"),
            "LA",
            f"{where}.assessment_id",
        )
        assessment = assessment_by_id.get(assessment_id)
        if assessment is None:
            raise PolicyViolation("assessment disposition targets an absent assessment")
        _content_id(
            disposition.get("assessment_origin_triage_id"),
            "HT",
            f"{where}.assessment_origin_triage_id",
        )
        sequence = disposition.get("decision_sequence")
        if type(sequence) is not int or sequence < 1:
            raise RecordError("assessment disposition sequence must be positive")
        previous = disposition.get("previous_disposition_id")
        if previous is not None:
            _content_id(previous, "AD", f"{where}.previous_disposition_id")
        _iso_date(disposition.get("created_on"), f"{where}.created_on")
        _object(disposition.get("bindings"), f"{where}.bindings")
        decision = _string(disposition.get("disposition"), f"{where}.disposition")
        if decision not in _ASSESSMENT_DISPOSITIONS:
            raise PolicyViolation("assessment disposition has an unsupported decision")
        if disposition.get("declared_discriminator") != assessment.get("discriminator"):
            raise PolicyViolation(
                "assessment disposition changed the exact declared discriminator"
            )
        current_bindings = _object(
            disposition.get("bindings"),
            f"{where}.bindings",
        )
        evidence_values = disposition.get("evidence_bindings")
        if type(evidence_values) is not list or not evidence_values:
            raise RecordError("assessment disposition requires embedded evidence")
        evidence = tuple(
            _validate_evidence_binding(
                value,
                f"{where}.evidence_bindings[{offset}]",
                bindings=current_bindings,
            )
            for offset, value in enumerate(evidence_values)
        )
        evidence_ids = tuple(
            _string(value.get("evidence_binding_id"), "evidence_binding_id")
            for value in evidence
        )
        if len(evidence_ids) != len(set(evidence_ids)) or evidence_ids != tuple(
            sorted(evidence_ids)
        ):
            raise RecordError(
                "assessment disposition evidence bindings must be unique and canonical"
            )
        _string(disposition.get("reason"), f"{where}.reason")
        changed = _canonical_unique_strings(
            disposition.get("changed_binding_pointers"),
            f"{where}.changed_binding_pointers",
        )
        superseded = disposition.get("superseded_bindings")
        if decision == "STALE_BY_BINDING_CHANGE":
            previous_bindings = _object(
                superseded,
                f"{where}.superseded_bindings",
            )
            expected_changed = _changed_binding_pointers(
                previous_bindings,
                current_bindings,
            )
            if not expected_changed or changed != expected_changed:
                raise PolicyViolation(
                    "stale assessment disposition changed or omitted its exact binding delta"
                )
            expected_delta = {
                "record_id": "TRIAGE-BINDING-DELTA",
                "previous_bindings": previous_bindings,
                "current_bindings": current_bindings,
                "changed_binding_pointers": list(expected_changed),
            }
            if not any(
                item.get("evidence_kind") == "INPUT_BINDING_DELTA"
                and item.get("record_snapshot") == expected_delta
                for item in evidence
            ):
                raise PolicyViolation(
                    "stale assessment disposition lacks its exact embedded binding delta"
                )
        else:
            if superseded is not None or changed:
                raise PolicyViolation(
                    "only a stale assessment disposition may carry a binding delta"
                )
            if any(
                item.get("evidence_kind") == "INPUT_BINDING_DELTA"
                for item in evidence
            ):
                raise PolicyViolation(
                    "a retained or defeated criticism requires substantive run evidence"
                )
            if not any(
                item.get("evidence_kind") == "CALIBRATION_RUN"
                for item in evidence
            ):
                raise PolicyViolation(
                    "a retained or defeated criticism requires the exact bound calibration run"
                )
        fixed = {
            "reviewer_kind": "HUMAN",
            "machine_generated": False,
            "epistemic_effect": "ASSESSMENT_WORKFLOW_ONLY",
            "can_establish_unique_cause": False,
            "can_promote_model": False,
            "can_confirm_target_semantics": False,
            "not_found_can_dispose": False,
            "source_count_can_decide": False,
            "provider_agreement_can_decide": False,
            "semantic_verdict": None,
        }
        if any(disposition.get(field) != required for field, required in fixed.items()):
            raise PolicyViolation(
                "assessment disposition changed a fixed non-inductive boundary"
            )
        dispositions.append(disposition)

    disposition_ids = tuple(
        _string(item.get("disposition_id"), "assessment disposition ID")
        for item in dispositions
    )
    if len(disposition_ids) != len(set(disposition_ids)):
        raise RecordError("assessment disposition IDs must be unique")
    if disposition_ids != tuple(sorted(disposition_ids)):
        raise RecordError("assessment dispositions must use canonical ID order")

    by_assessment: dict[str, list[dict[str, object]]] = {}
    for disposition in dispositions:
        by_assessment.setdefault(str(disposition["assessment_id"]), []).append(
            disposition
        )
    for assessment_id, chain in by_assessment.items():
        ordered = sorted(chain, key=lambda item: int(item["decision_sequence"]))
        origins = {item["assessment_origin_triage_id"] for item in ordered}
        if len(origins) != 1:
            raise PolicyViolation(
                f"assessment disposition chain changed origin for {assessment_id}"
            )
        for sequence, disposition in enumerate(ordered, start=1):
            if disposition["decision_sequence"] != sequence:
                raise PolicyViolation(
                    "assessment disposition chain has a sequence gap or fork"
                )
            expected_previous = (
                None if sequence == 1 else ordered[sequence - 2]["disposition_id"]
            )
            if disposition["previous_disposition_id"] != expected_previous:
                raise PolicyViolation(
                    "assessment disposition chain has an inconsistent predecessor"
                )
            if sequence > 1 and disposition["created_on"] < ordered[sequence - 2]["created_on"]:
                raise PolicyViolation("assessment disposition chronology moves backwards")
    return tuple(dispositions)


def _disposition_heads(
    dispositions: tuple[dict[str, object], ...],
) -> dict[str, dict[str, object]]:
    heads: dict[str, dict[str, object]] = {}
    for disposition in dispositions:
        assessment_id = str(disposition["assessment_id"])
        current = heads.get(assessment_id)
        if current is None or disposition["decision_sequence"] > current["decision_sequence"]:
            heads[assessment_id] = disposition
    return heads


def _effective_assessment_state(
    assessment_id: str,
    heads: dict[str, dict[str, object]],
    bindings: dict[str, object],
) -> str:
    disposition = heads.get(assessment_id)
    if disposition is None or disposition.get("bindings") != bindings:
        return "LIVE"
    return _string(disposition.get("disposition"), "assessment disposition")


def _assessment_work_state(
    bindings: dict[str, object],
    assessments: tuple[dict[str, object], ...],
    dispositions: tuple[dict[str, object], ...],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    heads = _disposition_heads(dispositions)
    active_ids = tuple(
        str(assessment["assessment_id"])
        for assessment in assessments
        if _effective_assessment_state(str(assessment["assessment_id"]), heads, bindings)
        not in _TERMINAL_ASSESSMENT_DISPOSITIONS
    )
    terminal_ids = {
        str(assessment["assessment_id"])
        for assessment in assessments
        if _effective_assessment_state(str(assessment["assessment_id"]), heads, bindings)
        in _TERMINAL_ASSESSMENT_DISPOSITIONS
    }
    frontier_ids = tuple(
        str(assessment["assessment_id"])
        for assessment in assessments
        if str(assessment["assessment_id"]) in active_ids
        and set(assessment["depends_on_assessment_ids"]).issubset(terminal_ids)
    )
    return active_ids, frontier_ids


def _expected_research_target_base(bindings: dict[str, object]) -> dict[str, object]:
    return {
        "issue_id": bindings["issue_id"],
        "issue_sha256": bindings["issue_sha256"],
        "warrant_id": bindings["warrant_id"],
        "warrant_sha256": bindings["warrant_sha256"],
    }


def _validate_next_action(
    value: object,
    *,
    assessments: tuple[dict[str, object], ...],
    dispositions: tuple[dict[str, object], ...],
    bindings: dict[str, object],
) -> dict[str, object]:
    action = _object(value, "triage.next_action")
    if action.get("action_id") != compute_next_action_id(action):
        raise RecordError("next action content-addressed ID mismatch")
    selected_ids = _canonical_unique_strings(
        action.get("selected_assessment_ids"),
        "triage.next_action.selected_assessment_ids",
        nonempty=True,
    )
    assessment_by_id = {
        _string(item.get("assessment_id"), "assessment_id"): item
        for item in assessments
    }
    unknown = sorted(set(selected_ids).difference(assessment_by_id))
    if unknown:
        raise PolicyViolation(
            f"next action selects absent locus assessments: {unknown}"
        )
    active_ids, frontier_ids = _assessment_work_state(
        bindings,
        assessments,
        dispositions,
    )
    inactive = sorted(set(selected_ids).difference(active_ids))
    if inactive:
        raise PolicyViolation(
            f"next action selects dispositioned locus assessments: {inactive}"
        )
    blocked = sorted(set(selected_ids).difference(frontier_ids))
    if blocked:
        raise PolicyViolation(
            "next action selects assessments outside the dependency-frontier "
            f"because of unresolved dependencies: {blocked}"
        )

    route_intent = _string(action.get("route_intent"), "next_action.route_intent")
    if route_intent not in _ROUTE_INTENTS:
        raise PolicyViolation("next action has an unsupported route_intent")
    for assessment_id in selected_ids:
        location = _string(
            assessment_by_id[assessment_id].get("uncertainty_location"),
            f"assessment {assessment_id} uncertainty_location",
        )
        expected_route = _LOCATION_ROUTE_INTENT.get(location)
        if expected_route is None:
            raise PolicyViolation(
                "an UNLOCATED or unsupported assessment cannot be selected for action"
            )
        if expected_route != route_intent:
            raise PolicyViolation(
                "next action route_intent contradicts a selected assessment location"
            )

    for field in ("action", "reason"):
        _string(action.get(field), f"triage.next_action.{field}")
    selection_basis = _string(
        action.get("selection_basis"),
        "triage.next_action.selection_basis",
    )
    if selection_basis not in _SELECTION_BASES:
        raise PolicyViolation("next action has an unsupported selection_basis")
    if len(selected_ids) > 1 and selection_basis != "SHARED_ACTION_FOR_MULTIPLE_LOCI":
        raise PolicyViolation(
            "an action selecting multiple assessments must declare a shared action"
        )
    if len(selected_ids) == 1 and selection_basis == "SHARED_ACTION_FOR_MULTIPLE_LOCI":
        raise PolicyViolation(
            "a shared-action selection must address multiple locus assessments"
        )
    if selection_basis == "UPSTREAM_DEPENDENCY":
        selected_id = selected_ids[0]
        if not any(
            selected_id in assessment.get("depends_on_assessment_ids", [])
            for assessment_id, assessment in assessment_by_id.items()
            if assessment_id in active_ids and assessment_id != selected_id
        ):
            raise PolicyViolation(
                "UPSTREAM_DEPENDENCY does not select a prerequisite of another live assessment"
            )

    research_target = action.get("research_target")
    if route_intent == InquiryRoute.EXTERNAL_RESEARCH_REQUIRED.value:
        target = _object(research_target, "triage.next_action.research_target")
        expected_target_base = _expected_research_target_base(bindings)
        for field, expected in expected_target_base.items():
            if target.get(field) != expected:
                raise PolicyViolation(
                    "external next action is not bound to the exact issue and warrant"
                )
        attack_target_ids = _canonical_unique_strings(
            target.get("attack_target_ids"),
            "triage.next_action.research_target.attack_target_ids",
            nonempty=True,
        )
        for attack_target_id in attack_target_ids:
            _content_id(
                attack_target_id,
                "AT",
                "triage.next_action.research_target.attack_target_ids item",
            )
    elif research_target is not None:
        raise PolicyViolation("only an external next action may carry a research target")
    if action.get("epistemic_effect") != "SCHEDULING_ONLY":
        raise PolicyViolation("next action changed its epistemic effect")
    if action.get("can_rank_semantic_truth") is not False:
        raise PolicyViolation("next action cannot rank semantic truth")
    return action


def validate_human_triage(
    triage: dict[str, object],
    *,
    expected_bindings: dict[str, object],
) -> dict[str, object]:
    """Validate human-authored plural diagnoses and one optional work action."""

    if type(triage) is not dict:
        raise TypeError("human triage must be a dictionary")
    if triage.get("schema_version") == LEGACY_TRIAGE_SCHEMA:
        return _validate_legacy_human_triage(
            triage,
            expected_bindings=expected_bindings,
        )
    _validate_with_schema(triage, "adaptive-inquiry-v2.schema.json")
    if triage.get("schema_version") != TRIAGE_SCHEMA:
        raise RecordError("triage input has an unsupported schema version")
    if triage.get("record_type") != "human_failure_triage":
        raise RecordError("triage input is not a human_failure_triage record")
    if triage.get("triage_id") != compute_human_triage_id(triage):
        raise RecordError("human triage content-addressed ID mismatch")
    sequence = triage.get("sequence")
    if type(sequence) is not int or sequence < 1:
        raise RecordError("human triage sequence must be a positive integer")
    previous_triage_id = triage.get("previous_triage_id")
    if previous_triage_id is not None:
        _content_id(previous_triage_id, "HT", "triage.previous_triage_id")
    transition_kind = _string(
        triage.get("transition_kind"),
        "triage.transition_kind",
    )
    _string(triage.get("transition_reason"), "triage.transition_reason")
    if sequence == 1:
        if previous_triage_id is not None or transition_kind != "GENESIS":
            raise PolicyViolation(
                "genesis human triage must have sequence one, no predecessor, and transition_kind GENESIS"
            )
    elif previous_triage_id is None or transition_kind == "GENESIS":
        raise PolicyViolation(
            "non-genesis human triage must link a predecessor and use a transition kind other than GENESIS"
        )
    if transition_kind not in {
        "GENESIS",
        "SAME_BINDINGS",
        "INPUT_BINDING_CHANGED",
    }:
        raise PolicyViolation("human triage has an unsupported transition_kind")
    if triage.get("bindings") != expected_bindings:
        raise PolicyViolation("human triage is not bound to the exact current inquiry inputs")
    if triage.get("overall_status") != "UNRESOLVED":
        raise PolicyViolation("plural human triage must remain overall UNRESOLVED")
    if triage.get("reviewer_kind") != "HUMAN" or triage.get("machine_generated") is not False:
        raise PolicyViolation("plural failure triage must be declared human-authored")
    if triage.get("epistemic_effect") != ROUTING_EFFECT:
        raise PolicyViolation("human triage changed its workflow-only epistemic effect")
    if triage.get("can_promote_model") is not False or triage.get("semantic_verdict") is not None:
        raise PolicyViolation("human triage cannot promote or semantically decide a model")

    ledger_created_on, _snapshot_date = _research_ledger_binding_dates(
        expected_bindings.get("research_ledger"),
        "triage.bindings.research_ledger",
    )
    created_on = _iso_date(triage.get("created_on"), "triage.created_on")
    if created_on < ledger_created_on:
        raise PolicyViolation(
            "human triage created_on precedes the bound research ledger artifact"
        )
    assessments = _validate_locus_assessments(triage)
    dispositions = _validate_assessment_dispositions(triage, assessments)
    if sequence == 1 and dispositions:
        raise PolicyViolation(
            "genesis triage cannot immediately disposition a new assessment"
        )
    action = triage.get("next_action")
    if action is not None:
        _validate_next_action(
            action,
            assessments=assessments,
            dispositions=dispositions,
            bindings=expected_bindings,
        )
    return triage


def _triage_filename(triage_id: str) -> str:
    return _content_id(triage_id, "HT", "triage_id").replace(":", "-") + ".json"


def _triage_claim_filename(parent_triage_id: str | None) -> str:
    parent_token = (
        "GENESIS"
        if parent_triage_id is None
        else _content_id(
            parent_triage_id,
            "HT",
            "parent_triage_id",
        ).removeprefix("HT:")
    )
    return f"NEXT-{parent_token}.claim"


def _triage_inventory(triage_dir: Path) -> tuple[set[str], set[str]]:
    if not isinstance(triage_dir, Path):
        raise TypeError("triage_dir must be pathlib.Path")
    if not triage_dir.is_dir():
        raise InquiryError(
            "INQUIRY_TRIAGE_PARENT_MISSING",
            f"human triage directory does not exist: {triage_dir}",
        )
    record_names: set[str] = set()
    claim_names: set[str] = set()
    for entry in triage_dir.iterdir():
        if not entry.is_file():
            continue
        name = entry.name
        if name.startswith("HT-") and name.endswith(".json"):
            record_names.add(name)
        elif name.startswith("NEXT-") and name.endswith(".claim"):
            claim_names.add(name)
    return record_names, claim_names


def _fsync_directory(directory: Path) -> None:
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _load_triage_file(path: Path) -> dict[str, object]:
    decoded, raw = _read_snapshot(path, "human triage")
    triage = _object(decoded, "human triage")
    if triage.get("schema_version") != TRIAGE_SCHEMA:
        raise PolicyViolation(
            "published active triage lineage may contain only human triage v2"
        )
    bindings = _object(triage.get("bindings"), "triage.bindings")
    validate_human_triage(triage, expected_bindings=bindings)
    if raw != canonical_bytes(triage) + b"\n":
        raise RecordError("human triage file is not canonical JSON plus one newline")
    triage_id = _string(triage.get("triage_id"), "triage.triage_id")
    if path.name != _triage_filename(triage_id):
        raise RecordError("human triage filename does not match its triage ID")
    return triage


def _assessment_inventory(
    triage: dict[str, object],
) -> dict[str, dict[str, object]]:
    return {
        _string(item.get("assessment_id"), "locus assessment ID"): item
        for item in _validate_locus_assessments(triage)
    }


def _disposition_inventory(
    triage: dict[str, object],
) -> dict[str, dict[str, object]]:
    assessments = _validate_locus_assessments(triage)
    return {
        _string(item.get("disposition_id"), "assessment disposition ID"): item
        for item in _validate_assessment_dispositions(triage, assessments)
    }


def _assessment_origin_inventory(
    triages: tuple[dict[str, object], ...],
) -> dict[str, str]:
    origins: dict[str, str] = {}
    for triage in triages:
        triage_id = _string(triage.get("triage_id"), "triage.triage_id")
        for assessment_id in _assessment_inventory(triage):
            origins.setdefault(assessment_id, triage_id)
    return origins


def _validate_triage_successor(
    predecessor: dict[str, object],
    successor: dict[str, object],
    *,
    assessment_origins: dict[str, str],
) -> None:
    if successor.get("sequence") != predecessor.get("sequence", 0) + 1:
        raise InquiryError(
            "INQUIRY_TRIAGE_SEQUENCE_MISMATCH",
            "human triage sequence does not extend its selected predecessor",
        )
    if successor.get("previous_triage_id") != predecessor.get("triage_id"):
        raise InquiryError(
            "INQUIRY_TRIAGE_STALE_HEAD",
            "human triage previous link differs from its selected predecessor",
        )
    if successor.get("created_on") < predecessor.get("created_on"):
        raise InquiryError(
            "INQUIRY_TRIAGE_CHRONOLOGY_REGRESSION",
            "human triage date precedes its selected predecessor",
        )

    predecessor_assessments = _assessment_inventory(predecessor)
    successor_assessments = _assessment_inventory(successor)
    missing = sorted(set(predecessor_assessments).difference(successor_assessments))
    if missing:
        raise PolicyViolation(
            f"human triage successor dropped live locus assessments: {missing}"
        )
    changed = sorted(
        assessment_id
        for assessment_id, assessment in predecessor_assessments.items()
        if successor_assessments[assessment_id] != assessment
    )
    if changed:
        raise PolicyViolation(
            f"human triage successor changed live locus assessments: {changed}"
        )

    predecessor_dispositions = _disposition_inventory(predecessor)
    successor_dispositions = _disposition_inventory(successor)
    missing_dispositions = sorted(
        set(predecessor_dispositions).difference(successor_dispositions)
    )
    if missing_dispositions:
        raise PolicyViolation(
            "human triage successor dropped assessment dispositions: "
            f"{missing_dispositions}"
        )
    changed_dispositions = sorted(
        disposition_id
        for disposition_id, disposition in predecessor_dispositions.items()
        if successor_dispositions[disposition_id] != disposition
    )
    if changed_dispositions:
        raise PolicyViolation(
            "human triage successor changed assessment dispositions: "
            f"{changed_dispositions}"
        )
    new_dispositions = [
        disposition
        for disposition_id, disposition in successor_dispositions.items()
        if disposition_id not in predecessor_dispositions
    ]
    new_targets = [str(item["assessment_id"]) for item in new_dispositions]
    if len(new_targets) != len(set(new_targets)):
        raise PolicyViolation(
            "a triage successor may add at most one disposition per assessment"
        )
    predecessor_heads = _disposition_heads(
        tuple(predecessor_dispositions.values())
    )
    predecessor_bindings = _object(
        predecessor.get("bindings"),
        "predecessor.bindings",
    )
    successor_bindings = _object(
        successor.get("bindings"),
        "successor.bindings",
    )
    _predecessor_live, predecessor_frontier = _assessment_work_state(
        predecessor_bindings,
        tuple(predecessor_assessments.values()),
        tuple(predecessor_dispositions.values()),
    )
    predecessor_action = predecessor.get("next_action")
    selected_by_predecessor = (
        set()
        if type(predecessor_action) is not dict
        else set(predecessor_action["selected_assessment_ids"])
    )
    for disposition in new_dispositions:
        assessment_id = str(disposition["assessment_id"])
        if assessment_id not in predecessor_assessments:
            raise PolicyViolation(
                "a new assessment must survive one triage before disposition"
            )
        if disposition.get("assessment_origin_triage_id") != assessment_origins.get(
            assessment_id
        ):
            raise PolicyViolation(
                "assessment disposition changed its assessment origin triage"
            )
        previous_head = predecessor_heads.get(assessment_id)
        expected_previous = (
            None if previous_head is None else previous_head["disposition_id"]
        )
        expected_sequence = (
            1 if previous_head is None else int(previous_head["decision_sequence"]) + 1
        )
        if (
            disposition.get("previous_disposition_id") != expected_previous
            or disposition.get("decision_sequence") != expected_sequence
        ):
            raise PolicyViolation(
                "new assessment disposition does not extend its selected disposition head"
            )
        if disposition.get("created_on") != successor.get("created_on"):
            raise PolicyViolation(
                "new assessment disposition date must equal its containing triage date"
            )
        if disposition.get("bindings") != successor.get("bindings"):
            raise PolicyViolation(
                "new assessment disposition is not bound to its containing triage inputs"
            )
        decision = str(disposition["disposition"])
        prior_state = _effective_assessment_state(
            assessment_id,
            predecessor_heads,
            predecessor_bindings,
        )
        if successor_bindings == predecessor_bindings:
            if prior_state in _TERMINAL_ASSESSMENT_DISPOSITIONS:
                if decision != "RETAINED":
                    raise PolicyViolation(
                        "a terminal assessment can only be reopened by RETAINED"
                    )
            elif (
                assessment_id not in predecessor_frontier
                or assessment_id not in selected_by_predecessor
            ):
                raise PolicyViolation(
                    "assessment disposition bypassed the previously authorized dependency-frontier action"
                )
        elif decision != "STALE_BY_BINDING_CHANGE":
            raise PolicyViolation(
                "a binding-change successor may add only exact staleness dispositions"
            )

    if successor_bindings == predecessor_bindings:
        if successor.get("transition_kind") != "SAME_BINDINGS":
            raise PolicyViolation(
                "same-binding human triage successor must declare SAME_BINDINGS"
            )
        if any(
            item.get("disposition") == "STALE_BY_BINDING_CHANGE"
            for item in new_dispositions
        ):
            raise PolicyViolation(
                "same-binding triage cannot mark an assessment stale by binding change"
            )
        return
    if successor.get("transition_kind") != "INPUT_BINDING_CHANGED":
        raise PolicyViolation(
            "changed-binding human triage successor must declare INPUT_BINDING_CHANGED"
        )
    predecessor_ledger = _object(
        predecessor_bindings.get("research_ledger"),
        "predecessor.bindings.research_ledger",
    )
    successor_ledger = _object(
        successor_bindings.get("research_ledger"),
        "successor.bindings.research_ledger",
    )
    if (
        successor_bindings.get("authority_sha256")
        != predecessor_bindings.get("authority_sha256")
        or successor_ledger.get("ledger_id") != predecessor_ledger.get("ledger_id")
    ):
        raise PolicyViolation(
            "changed-binding triage must preserve authority and research-ledger identity"
        )
    if successor.get("next_action") is not None:
        raise PolicyViolation(
            "changed-binding triage must leave next_action null for human reselection"
        )
    for disposition in new_dispositions:
        if (
            disposition.get("disposition") == "STALE_BY_BINDING_CHANGE"
            and disposition.get("superseded_bindings") != predecessor_bindings
        ):
            raise PolicyViolation(
                "stale assessment disposition does not name the exact predecessor bindings"
            )


def verify_human_triage_chain(
    triage_dir: Path,
    head_triage_id: str | None,
    *,
    expected_bindings: dict[str, object] | None,
    _pending_successor_claim: tuple[str, bytes] | None = None,
) -> HumanTriageState:
    """Verify the complete no-clobber v2 triage lineage and selected terminal."""

    record_names, claim_names = _triage_inventory(triage_dir)
    pending_claim_name: str | None = None
    pending_claim_payload: bytes | None = None
    if _pending_successor_claim is not None:
        pending_claim_name, pending_claim_payload = _pending_successor_claim
        if (
            type(pending_claim_name) is not str
            or type(pending_claim_payload) is not bytes
            or pending_claim_name not in claim_names
            or pending_claim_name != _triage_claim_filename(head_triage_id)
        ):
            raise InquiryError(
                "INQUIRY_TRIAGE_PENDING_CLAIM_INVALID",
                "pending human-triage recovery did not identify an existing exact claim",
            )
        try:
            existing_pending = (triage_dir / pending_claim_name).read_bytes()
        except OSError as exc:
            raise InquiryError(
                "INQUIRY_TRIAGE_CLAIM_READ_FAILED",
                f"cannot read pending human triage successor claim: {exc}",
            ) from exc
        if existing_pending != pending_claim_payload:
            raise InquiryError(
                "INQUIRY_TRIAGE_PENDING_CLAIM_INVALID",
                "pending human-triage recovery claim changed content",
            )
        try:
            pending_source = pending_claim_payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise InquiryError(
                "INQUIRY_TRIAGE_PENDING_CLAIM_INVALID",
                "pending human-triage recovery content is not UTF-8",
            ) from exc
        pending_triage = _object(
            loads_strict(pending_source),
            "pending human-triage successor",
        )
        if canonical_bytes(pending_triage) + b"\n" != pending_claim_payload:
            raise RecordError("pending human-triage successor is not canonical")
        validate_human_triage(
            pending_triage,
            expected_bindings=_object(
                pending_triage.get("bindings"),
                "pending human-triage successor bindings",
            ),
        )
        if (
            pending_triage.get("schema_version") != TRIAGE_SCHEMA
            or pending_triage.get("previous_triage_id") != head_triage_id
        ):
            raise InquiryError(
                "INQUIRY_TRIAGE_PENDING_CLAIM_INVALID",
                "pending human-triage recovery does not extend the selected parent",
            )
    if head_triage_id is None:
        expected_claim_names = (
            set() if pending_claim_name is None else {pending_claim_name}
        )
        if record_names or claim_names != expected_claim_names:
            raise InquiryError(
                "INQUIRY_TRIAGE_HEAD_REQUIRED",
                "no-triage planning is allowed only when the triage lineage is empty",
            )
        return HumanTriageState(None, ())

    _content_id(head_triage_id, "HT", "head_triage_id")
    reverse: list[dict[str, object]] = []
    seen: set[str] = set()
    current: str | None = head_triage_id
    while current is not None:
        if current in seen:
            raise RecordError("human triage chain contains a cycle")
        seen.add(current)
        triage = _load_triage_file(triage_dir / _triage_filename(current))
        if triage.get("triage_id") != current:
            raise RecordError("human triage chain resolved the wrong record")
        reverse.append(triage)
        previous = triage.get("previous_triage_id")
        current = previous if type(previous) is str else None

    triages = tuple(reversed(reverse))
    assessment_origins: dict[str, str] = {}
    for index, triage in enumerate(triages, start=1):
        if triage.get("sequence") != index:
            raise RecordError("human triage sequence is not contiguous from one")
        expected_previous = None if index == 1 else triages[index - 2]["triage_id"]
        if triage.get("previous_triage_id") != expected_previous:
            raise RecordError("human triage previous link is inconsistent")
        if index > 1:
            _validate_triage_successor(
                triages[index - 2],
                triage,
                assessment_origins=assessment_origins,
            )
        triage_id = _string(triage.get("triage_id"), "triage.triage_id")
        for assessment_id in _assessment_inventory(triage):
            assessment_origins.setdefault(assessment_id, triage_id)

    expected_records = {
        _triage_filename(_string(triage.get("triage_id"), "triage_id"))
        for triage in triages
    }
    if record_names != expected_records:
        raise InquiryError(
            "INQUIRY_TRIAGE_ORPHAN_RECORD",
            "triage directory contains a record outside the selected complete lineage",
        )
    expected_claims: set[str] = set()
    for triage in triages:
        previous = triage.get("previous_triage_id")
        claim_name = _triage_claim_filename(
            previous if type(previous) is str else None
        )
        expected_claims.add(claim_name)
        try:
            claim_payload = (triage_dir / claim_name).read_bytes()
        except OSError as exc:
            raise InquiryError(
                "INQUIRY_TRIAGE_CLAIM_READ_FAILED",
                f"cannot read human triage successor claim: {exc}",
            ) from exc
        if claim_payload != canonical_bytes(triage) + b"\n":
            raise RecordError("human triage successor claim has changed content")
    if pending_claim_name is not None:
        expected_claims.add(pending_claim_name)
    if claim_names != expected_claims:
        raise InquiryError(
            "INQUIRY_TRIAGE_NONTERMINAL_HEAD",
            "triage claims do not identify the selected record as the unique terminal head",
        )
    terminal = triages[-1]
    if expected_bindings is not None and terminal.get("bindings") != expected_bindings:
        raise PolicyViolation(
            "selected human triage head is not bound to the exact current inquiry inputs"
        )
    return HumanTriageState(head_triage_id, triages)


def _validate_action_attack_target_selection(
    triage: dict[str, object],
    available_attack_targets: tuple[dict[str, object], ...],
) -> None:
    action = triage.get("next_action")
    if type(action) is not dict or action.get("route_intent") != InquiryRoute.EXTERNAL_RESEARCH_REQUIRED.value:
        return
    target = _object(action.get("research_target"), "triage.next_action.research_target")
    selected = set(
        _canonical_unique_strings(
            target.get("attack_target_ids"),
            "triage.next_action.research_target.attack_target_ids",
            nonempty=True,
        )
    )
    available = {
        _string(item.get("attack_target_id"), "attack_target_id")
        for item in available_attack_targets
    }
    unknown = sorted(selected.difference(available))
    if unknown:
        raise PolicyViolation(
            f"external next action selects unavailable attack targets: {unknown}"
        )


def _publish_human_triage(
    triage_dir: Path,
    triage: dict[str, object],
    *,
    expected_head_triage_id: str | None,
    expected_bindings: dict[str, object],
    available_attack_targets: tuple[dict[str, object], ...],
) -> Path:
    """Publish one v2 human triage without overwrite or criticism loss."""

    validate_human_triage(triage, expected_bindings=expected_bindings)
    if triage.get("schema_version") != TRIAGE_SCHEMA:
        raise PolicyViolation("only human triage v2 may be newly published")
    checked_targets = _validate_attack_target_menu(
        list(available_attack_targets),
        "available_attack_targets",
    )
    _validate_action_attack_target_selection(triage, checked_targets)
    if triage.get("previous_triage_id") != expected_head_triage_id:
        raise InquiryError(
            "INQUIRY_TRIAGE_STALE_HEAD",
            "human triage previous link differs from the caller's expected head",
        )

    payload = canonical_bytes(triage) + b"\n"
    triage_id = _string(triage.get("triage_id"), "triage.triage_id")
    output_path = triage_dir / _triage_filename(triage_id)
    claim_path = triage_dir / _triage_claim_filename(expected_head_triage_id)
    pending_claim: tuple[str, bytes] | None = None
    claim_exists = claim_path.exists()
    output_exists = output_path.exists()
    if output_exists and not claim_exists:
        raise InquiryError(
            "INQUIRY_TRIAGE_ORPHAN_RECORD",
            "human triage record exists without its immutable successor claim",
        )
    if claim_exists:
        try:
            existing_claim = claim_path.read_bytes()
        except OSError as exc:
            raise InquiryError(
                "INQUIRY_TRIAGE_CLAIM_READ_FAILED",
                f"cannot read human triage successor claim: {exc}",
            ) from exc
        if existing_claim != payload:
            raise InquiryError(
                "INQUIRY_TRIAGE_STALE_HEAD",
                "the selected triage head already has a different claimed successor",
            )
        if output_exists:
            try:
                existing_record = output_path.read_bytes()
            except OSError as exc:
                raise InquiryError(
                    "INQUIRY_TRIAGE_READ_FAILED",
                    f"cannot read existing human triage record: {exc}",
                ) from exc
            if existing_record != payload:
                raise RecordError(
                    "human triage record differs from its exact successor claim"
                )
            verify_human_triage_chain(
                triage_dir,
                triage_id,
                expected_bindings=expected_bindings,
            )
            try:
                _fsync_directory(triage_dir)
            except OSError as exc:
                raise InquiryError(
                    "INQUIRY_TRIAGE_WRITE_FAILED",
                    f"cannot durably acknowledge human triage: {exc}",
                ) from exc
            return output_path
        pending_claim = (claim_path.name, payload)

    state = verify_human_triage_chain(
        triage_dir,
        expected_head_triage_id,
        expected_bindings=None,
        _pending_successor_claim=pending_claim,
    )
    if triage.get("sequence") != len(state.triages) + 1:
        raise InquiryError(
            "INQUIRY_TRIAGE_SEQUENCE_MISMATCH",
            "human triage sequence does not extend the selected head",
        )
    if state.triages:
        _validate_triage_successor(
            state.triages[-1],
            triage,
            assessment_origins=_assessment_origin_inventory(state.triages),
        )
    elif triage.get("transition_kind") != "GENESIS":
        raise PolicyViolation("first published human triage must declare GENESIS")

    temporary_path: Path | None = None
    try:
        if pending_claim is None:
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=".human-triage-",
                suffix=".tmp",
                dir=triage_dir,
            )
            temporary_path = Path(temporary_name)
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            try:
                os.link(temporary_path, claim_path)
            except FileExistsError as exc:
                try:
                    existing_claim = claim_path.read_bytes()
                except OSError:
                    existing_claim = b""
                if existing_claim != payload:
                    raise InquiryError(
                        "INQUIRY_TRIAGE_STALE_HEAD",
                        "the selected triage head already has a different claimed successor",
                    ) from exc
            _fsync_directory(triage_dir)
        try:
            os.link(claim_path, output_path)
        except FileExistsError as exc:
            try:
                existing_record = output_path.read_bytes()
            except OSError:
                existing_record = b""
            if existing_record != payload:
                raise InquiryError(
                    "INQUIRY_TRIAGE_EXISTS",
                    f"different human triage content exists: {output_path}",
                ) from exc
        _fsync_directory(triage_dir)
    except OSError as exc:
        code = (
            "INQUIRY_TRIAGE_PARENT_MISSING"
            if exc.errno == errno.ENOENT
            else "INQUIRY_TRIAGE_WRITE_FAILED"
        )
        raise InquiryError(code, f"cannot publish human triage: {exc}") from exc
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass
    verify_human_triage_chain(
        triage_dir,
        triage_id,
        expected_bindings=expected_bindings,
    )
    return output_path


def publish_human_triage_against_inputs(
    triage_dir: Path,
    triage: dict[str, object],
    *,
    expected_head_triage_id: str | None,
    repo_root: Path,
    run_record_path: Path,
    research_ledger_path: Path,
) -> Path:
    """Publish only after deriving authorization from exact current inputs."""

    report, run_raw = _load_verified_run(run_record_path, repo_root)
    _ledger, _ledger_raw, research_binding = _load_research_ledger_snapshot(
        research_ledger_path
    )
    bindings, issue, warrant = _extract_bindings(report, run_raw, research_binding)
    available_attack_targets = _available_attack_targets(issue, warrant, bindings)
    return _publish_human_triage(
        triage_dir,
        triage,
        expected_head_triage_id=expected_head_triage_id,
        expected_bindings=bindings,
        available_attack_targets=available_attack_targets,
    )


def _case_digest(
    bindings: dict[str, object],
    triage: dict[str, object] | None,
    *,
    plan_schema: str = PLAN_SCHEMA,
) -> str:
    if plan_schema == LEGACY_PLAN_SCHEMA:
        domain = "creib.semantic-forge.adaptive-inquiry-case.v1"
    elif plan_schema == PLAN_SCHEMA:
        domain = "creib.semantic-forge.adaptive-inquiry-case.v2"
    else:
        raise RecordError("adaptive inquiry case has an unsupported plan schema")
    return domain_digest(
        domain,
        {
            "bindings": bindings,
            "triage_id": None if triage is None else triage["triage_id"],
        },
    )


def _model_binding_digest(bindings: dict[str, object]) -> str:
    model_binding = {
        key: bindings[key]
        for key in (
            "authority_sha256",
            "candidate_id",
            "candidate_contract_sha256",
            "challenge_id",
            "challenge_contract_sha256",
            "fixture_contract_sha256",
            "evaluator_id",
            "evaluator_contract_sha256",
        )
    }
    return domain_digest(
        "creib.semantic-forge.inquiry-model-binding.v1",
        model_binding,
    )


def _validate_attack_target(value: Any, where: str) -> dict[str, object]:
    target = _object(value, where)
    expected_fields = {
        "attack_target_id",
        "issue_sha256",
        "warrant_sha256",
        "rival_id",
        "rival_claim",
        "falsifier_condition",
    }
    if set(target) != expected_fields:
        raise RecordError(f"{where} has unexpected or missing fields")
    target_id = _content_id(
        target.get("attack_target_id"),
        "AT",
        f"{where}.attack_target_id",
    )
    for field in (
        "issue_sha256",
        "warrant_sha256",
        "rival_id",
        "rival_claim",
        "falsifier_condition",
    ):
        _string(target.get(field), f"{where}.{field}")
    if target_id != _compute_attack_target_id(target):
        raise RecordError(f"{where} content-addressed ID mismatch")
    return target


def _validate_attack_target_menu(
    value: Any,
    where: str,
) -> tuple[dict[str, object], ...]:
    if type(value) is not list:
        raise RecordError(f"{where} must be an array")
    targets = tuple(
        _validate_attack_target(item, f"{where}[{index}]")
        for index, item in enumerate(value)
    )
    target_ids = tuple(
        _string(target.get("attack_target_id"), f"{where} attack_target_id")
        for target in targets
    )
    if len(target_ids) != len(set(target_ids)):
        raise RecordError(f"{where} must contain unique attack targets")
    if target_ids != tuple(sorted(target_ids)):
        raise RecordError(f"{where} must use canonical attack_target_id order")
    return targets


def _available_attack_targets(
    issue: Issue,
    warrant: ResearchWarrant,
    bindings: dict[str, object],
) -> tuple[dict[str, object], ...]:
    """Derive the complete non-authorizing menu of exact rival attacks."""

    targets: list[dict[str, object]] = []
    for rival in issue.rivals:
        for falsifier in rival.falsifier_conditions:
            body: dict[str, object] = {
                "issue_sha256": bindings["issue_sha256"],
                "warrant_sha256": bindings["warrant_sha256"],
                "rival_id": rival.rival_id,
                "rival_claim": rival.claim,
                "falsifier_condition": falsifier,
            }
            targets.append(
                {
                    **body,
                    "attack_target_id": _record_id(
                        "AT",
                        ATTACK_TARGET_DOMAIN,
                        body,
                    ),
                }
            )
    targets.sort(key=lambda item: str(item["attack_target_id"]))
    checked = _validate_attack_target_menu(targets, "available_attack_targets")
    if not checked:
        raise PolicyViolation("bound issue has no exact rival attack targets")
    return checked


def _critical_questions(
    issue: Issue,
    warrant: ResearchWarrant,
    bindings: dict[str, object],
    case_sha256: str,
    default_contemporary_provider: str,
    triage: dict[str, object],
    available_attack_targets: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    if (
        not warrant.discovery_channels
        or warrant.discovery_channels[0] != default_contemporary_provider
    ):
        raise PolicyViolation(
            "bound run and research ledger disagree on the default discovery provider"
        )
    model_binding_sha256 = _model_binding_digest(bindings)
    action = _object(triage.get("next_action"), "triage.next_action")
    if action.get("route_intent") != InquiryRoute.EXTERNAL_RESEARCH_REQUIRED.value:
        raise PolicyViolation("critical questions require a selected external action")
    selected_assessment_ids = list(
        _canonical_unique_strings(
            action.get("selected_assessment_ids"),
            "triage.next_action.selected_assessment_ids",
            nonempty=True,
        )
    )
    assessment_by_id = {
        _string(item.get("assessment_id"), "assessment_id"): item
        for item in _validate_locus_assessments(triage)
    }
    selected_assessments = [
        assessment_by_id[assessment_id]
        for assessment_id in selected_assessment_ids
    ]
    action_text = _string(action.get("action"), "triage.next_action.action")
    selection_reason = _string(
        action.get("reason"),
        "triage.next_action.reason",
    )
    research_target = _object(
        action.get("research_target"),
        "triage.next_action.research_target",
    )
    selected_target_ids = _canonical_unique_strings(
        research_target.get("attack_target_ids"),
        "triage.next_action.research_target.attack_target_ids",
        nonempty=True,
    )
    target_by_id = {
        _string(target.get("attack_target_id"), "attack_target_id"): target
        for target in available_attack_targets
    }
    unknown_targets = sorted(set(selected_target_ids).difference(target_by_id))
    if unknown_targets:
        raise PolicyViolation(
            f"external next action selects unavailable attack targets: {unknown_targets}"
        )
    assessment_instructions = " ".join(
        (
            f"Assessment {assessment['assessment_id']}: mechanism={assessment['mechanism']} "
            f"discriminator={assessment['discriminator']} relevance={assessment['relevance']} "
            f"scope={assessment['scope']}."
        )
        for assessment in selected_assessments
    )
    questions: list[dict[str, object]] = []
    for attack_target_id in selected_target_ids:
        target = target_by_id[attack_target_id]
        body: dict[str, object] = {
            "schema_version": QUESTION_SCHEMA,
            "case_sha256": case_sha256,
            "issue_id": issue.issue_id,
            "issue_sha256": bindings["issue_sha256"],
            "warrant_id": warrant.warrant_id,
            "warrant_sha256": bindings["warrant_sha256"],
            "model_binding_sha256": model_binding_sha256,
            "trigger_observation_sha256": bindings["observation_sha256"],
            "triage_id": triage["triage_id"],
            "action_id": action["action_id"],
            "selected_assessment_ids": selected_assessment_ids,
            "selected_locus_assessments": selected_assessments,
            "selected_action": action_text,
            "selection_reason": selection_reason,
            "triage_created_on": _iso_date(
                triage.get("created_on"),
                "triage.created_on",
            ),
            "attack_target_id": attack_target_id,
            "attack_target": target,
            "rival_id": target["rival_id"],
            "rival_claim": target["rival_claim"],
            "falsifier_condition": target["falsifier_condition"],
            "purpose": "RIVAL_FALSIFIER",
            "query": (
                f"Scheduled action: {action_text} Selection reason: "
                f"{selection_reason} Apply these live criticism constraints: "
                f"{assessment_instructions} Seek a counterexample, boundary "
                "case, explicit denial, or discriminating instrument for "
                f"rival {target['rival_id']}: {target['rival_claim']} Exact "
                f"attack: {target['falsifier_condition']} Report a direct "
                "primary-source locator or reproducible construction and the "
                "premise it attacks. If none is found under the declared "
                "protocol, leave the question open; absence supplies no "
                "support and cannot retire the question under this protocol."
            ),
            "expected_discriminator": warrant.expected_discriminator,
            "decision_relevance": warrant.decision_relevance,
            "admissible_source_scope": list(warrant.admissible_source_scope),
            "search_protocol": {
                "discovery_channels": list(warrant.discovery_channels),
                "default_contemporary_discovery_channel": (
                    default_contemporary_provider
                ),
                "direct_primary_source_required": True,
                "provider_output_is_oracle": False,
                "stop_condition": warrant.stop_condition,
                "not_found_effect": "ABSENCE_SUPPLIES_NO_SUPPORT",
            },
            "epistemic_limit": NON_INDUCTIVE_LIMIT,
            "can_confirm_target_semantics": False,
            "source_count_can_promote": False,
            "provider_agreement_can_promote": False,
        }
        question = {**body, "question_id": _record_id("IQ", QUESTION_SCHEMA, body)}
        questions.append(question)
    question_ids = [item["question_id"] for item in questions]
    if len(question_ids) != len(set(question_ids)):
        raise RecordError("generated critical questions are not uniquely addressed")
    return tuple(questions)


_HUMAN_DISPOSITIONS = {
    "HUMAN_CRITICISM_RETAINED",
    "HUMAN_NONDISCRIMINATING",
    "HUMAN_MISFRAMED",
    "HUMAN_OUT_OF_SCOPE",
}

_EVENT_RULES: dict[str, tuple[str, tuple[str | None, ...], str]] = {
    "QUESTION_PROPOSED": ("MACHINE", (None,), QuestionState.PROPOSED.value),
    "QUESTION_ACTIVATED": (
        "HUMAN",
        (QuestionState.PROPOSED.value,),
        QuestionState.ACTIVE.value,
    ),
    "RESEARCH_CANDIDATE_RECORDED": (
        "OPERATOR",
        (QuestionState.ACTIVE.value,),
        QuestionState.AWAITING_HUMAN_REVIEW.value,
    ),
    "HUMAN_CRITICISM_RETAINED": (
        "HUMAN",
        (QuestionState.AWAITING_HUMAN_REVIEW.value,),
        QuestionState.RETIRED_WITH_CRITICISM_CANDIDATE.value,
    ),
    "HUMAN_NONDISCRIMINATING": (
        "HUMAN",
        (QuestionState.AWAITING_HUMAN_REVIEW.value,),
        QuestionState.RETIRED_NONDISCRIMINATING.value,
    ),
    "HUMAN_MISFRAMED": (
        "HUMAN",
        (
            QuestionState.PROPOSED.value,
            QuestionState.ACTIVE.value,
            QuestionState.AWAITING_HUMAN_REVIEW.value,
        ),
        QuestionState.RETIRED_MISFRAMED.value,
    ),
    "HUMAN_OUT_OF_SCOPE": (
        "HUMAN",
        (
            QuestionState.PROPOSED.value,
            QuestionState.ACTIVE.value,
            QuestionState.AWAITING_HUMAN_REVIEW.value,
        ),
        QuestionState.RETIRED_OUT_OF_SCOPE.value,
    ),
    "MODEL_CHANGED": (
        "MACHINE",
        (
            QuestionState.PROPOSED.value,
            QuestionState.ACTIVE.value,
            QuestionState.AWAITING_HUMAN_REVIEW.value,
        ),
        QuestionState.STALE_BY_MODEL_CHANGE.value,
    ),
}

_ACTIONABLE_ROUTE_EVENT_TYPES: dict[str, frozenset[str]] = {
    InquiryRoute.EXTERNAL_RESEARCH_REQUIRED.value: frozenset(
        {"QUESTION_PROPOSED"}
    ),
    InquiryRoute.RESEARCH_IN_PROGRESS.value: frozenset(
        {
            "QUESTION_ACTIVATED",
            "RESEARCH_CANDIDATE_RECORDED",
            "HUMAN_MISFRAMED",
            "HUMAN_OUT_OF_SCOPE",
            "MODEL_CHANGED",
        }
    ),
    InquiryRoute.AWAITING_HUMAN_REVIEW.value: frozenset(
        {
            "HUMAN_CRITICISM_RETAINED",
            "HUMAN_NONDISCRIMINATING",
            "HUMAN_MISFRAMED",
            "HUMAN_OUT_OF_SCOPE",
            "MODEL_CHANGED",
        }
    ),
}


def _validate_question(question: dict[str, object]) -> None:
    if type(question) is not dict:
        raise RecordError("critical question must be an object")
    version = question.get("schema_version")
    if version not in {LEGACY_QUESTION_SCHEMA, QUESTION_SCHEMA}:
        raise RecordError("critical question has an unsupported schema_version")
    if question.get("question_id") != compute_question_id(question):
        raise RecordError("critical question content-addressed ID mismatch")
    _iso_date(question.get("triage_created_on"), "question.triage_created_on")
    forbidden = {"confidence", "consensus", "citation_count", "source_count", "winner"}
    leaked = sorted(forbidden.intersection(question))
    if leaked:
        raise PolicyViolation(f"critical question contains promotive fields: {leaked}")
    fixed = {
        "schema_version": version,
        "purpose": "RIVAL_FALSIFIER",
        "epistemic_limit": NON_INDUCTIVE_LIMIT,
        "can_confirm_target_semantics": False,
        "source_count_can_promote": False,
        "provider_agreement_can_promote": False,
    }
    for field, required in fixed.items():
        if question.get(field) != required:
            raise PolicyViolation(
                f"critical question changed its fixed non-inductive field {field}"
            )
    if version == QUESTION_SCHEMA:
        _content_id(question.get("triage_id"), "HT", "question.triage_id")
        _content_id(question.get("action_id"), "NA", "question.action_id")
        selected_ids = _canonical_unique_strings(
            question.get("selected_assessment_ids"),
            "question.selected_assessment_ids",
            nonempty=True,
        )
        selected_assessments = _validate_locus_assessments(
            {
                "locus_assessments": question.get(
                    "selected_locus_assessments"
                )
            },
            allow_external_dependencies=True,
        )
        copied_ids = tuple(
            _string(item.get("assessment_id"), "selected assessment ID")
            for item in selected_assessments
        )
        if copied_ids != selected_ids:
            raise PolicyViolation(
                "critical question changed its selected assessment records"
            )
        selected_action = _string(
            question.get("selected_action"),
            "question.selected_action",
        )
        selection_reason = _string(
            question.get("selection_reason"),
            "question.selection_reason",
        )
        target = _validate_attack_target(
            question.get("attack_target"),
            "question.attack_target",
        )
        flattened = (
            (question.get("attack_target_id"), target["attack_target_id"]),
            (question.get("issue_sha256"), target["issue_sha256"]),
            (question.get("warrant_sha256"), target["warrant_sha256"]),
            (question.get("rival_id"), target["rival_id"]),
            (question.get("rival_claim"), target["rival_claim"]),
            (
                question.get("falsifier_condition"),
                target["falsifier_condition"],
            ),
        )
        if any(actual != expected for actual, expected in flattened):
            raise PolicyViolation(
                "critical question changed its full or flattened attack target"
            )
        query = _string(question.get("query"), "question.query")
        required_query_fragments = [selected_action, selection_reason]
        for assessment in selected_assessments:
            required_query_fragments.extend(
                _string(assessment.get(field), f"selected assessment {field}")
                for field in ("mechanism", "discriminator", "relevance", "scope")
            )
        required_query_fragments.extend(
            _string(target.get(field), f"attack target {field}")
            for field in ("rival_claim", "falsifier_condition")
        )
        if any(fragment not in query for fragment in required_query_fragments):
            raise PolicyViolation(
                "critical question query does not apply its selected action, criticisms, and target"
            )
    protocol = _object(question.get("search_protocol"), "question.search_protocol")
    channels = protocol.get("discovery_channels")
    if type(channels) is not list or not channels:
        raise RecordError("critical question must retain ordered discovery channels")
    if protocol.get("default_contemporary_discovery_channel") != channels[0]:
        raise PolicyViolation(
            "critical question default provider must be its first bound channel"
        )
    protocol_fixed = {
        "direct_primary_source_required": True,
        "provider_output_is_oracle": False,
        "not_found_effect": "ABSENCE_SUPPLIES_NO_SUPPORT",
    }
    for field, required in protocol_fixed.items():
        if protocol.get(field) != required:
            raise PolicyViolation(
                f"critical question changed its fixed search-policy field {field}"
            )


def _validate_standalone_entry(
    entry: dict[str, object],
    *,
    research_ledger: ResearchLedger,
    occurred_on: str,
) -> None:
    """Apply the strict v2 source-report contract to an event-time snapshot."""

    parsed = parse_event_research_entry(
        entry,
        policy_ledger=research_ledger,
        recorded_on=occurred_on,
    )
    if parsed.to_dict() != entry:
        raise RecordError("research entry does not round-trip exactly")


def _v2_question_binding(question: dict[str, object]) -> dict[str, object]:
    """Project the audit-visible identity of one exact v2 research question."""

    if question.get("schema_version") != QUESTION_SCHEMA:
        raise PolicyViolation(
            "a v2 event research-entry envelope requires an exact v2 question"
        )
    case_sha256 = _string(question.get("case_sha256"), "question.case_sha256")
    _hex_from_domain(case_sha256)
    return {
        "question_id": _content_id(
            question.get("question_id"),
            "IQ",
            "question.question_id",
        ),
        "case_sha256": case_sha256,
        "triage_id": _content_id(
            question.get("triage_id"),
            "HT",
            "question.triage_id",
        ),
        "action_id": _content_id(
            question.get("action_id"),
            "NA",
            "question.action_id",
        ),
        "attack_target_id": _content_id(
            question.get("attack_target_id"),
            "AT",
            "question.attack_target_id",
        ),
    }


def _validate_entry_targets_question(
    entry: dict[str, object],
    question: dict[str, object],
) -> None:
    if (
        entry.get("attacked_harness_question") != question.get("query")
        or entry.get("falsifier") != question.get("falsifier_condition")
    ):
        raise PolicyViolation(
            "research entry does not target the exact active question and falsifier"
        )


def _validate_v2_event_research_entry(
    envelope: dict[str, object],
    question: dict[str, object],
    *,
    research_ledger: ResearchLedger,
    occurred_on: str,
) -> dict[str, object]:
    """Validate an operator-supplied source report against exact question identity."""

    expected_fields = {"schema_version", "question_binding", "source_report"}
    if set(envelope) != expected_fields:
        raise RecordError(
            "v2 event research-entry envelope has unexpected or missing fields"
        )
    if envelope.get("schema_version") != EVENT_RESEARCH_ENTRY_SCHEMA:
        raise RecordError("v2 event research-entry envelope changed schema_version")
    binding = _object(
        envelope.get("question_binding"),
        "event.research_entry.question_binding",
    )
    if binding != _v2_question_binding(question):
        raise PolicyViolation(
            "research entry changed its exact v2 question binding"
        )
    source_report = _object(
        envelope.get("source_report"),
        "event.research_entry.source_report",
    )
    _validate_standalone_entry(
        source_report,
        research_ledger=research_ledger,
        occurred_on=occurred_on,
    )
    entry_id = _string(
        source_report.get("entry_id"),
        "event.research_entry.source_report.entry_id",
    )
    bound_entry = next(
        (
            item.to_dict()
            for item in research_ledger.entries
            if item.entry_id == entry_id
        ),
        None,
    )
    if bound_entry is not None and bound_entry != source_report:
        raise PolicyViolation(
            "event source report reuses a bound research-ledger entry ID for different content"
        )
    _validate_entry_targets_question(source_report, question)
    return source_report


def _validate_event_chronology(
    *,
    event_date: str,
    triage_date: str,
    research_ledger_binding: Any,
) -> None:
    ledger_created_on, _ledger_as_of_date = _research_ledger_binding_dates(
        research_ledger_binding,
        "event.research_ledger",
    )
    if event_date < triage_date:
        raise InquiryError(
            "INQUIRY_EVENT_PRECEDES_TRIAGE",
            "inquiry event occurred_on precedes the exact plan triage.created_on",
        )
    if event_date < ledger_created_on:
        raise InquiryError(
            "INQUIRY_EVENT_PRECEDES_RESEARCH_LEDGER",
            "inquiry event occurred_on precedes bound research_ledger.created_on",
        )
    if triage_date < ledger_created_on:
        raise InquiryError(
            "INQUIRY_TRIAGE_PRECEDES_RESEARCH_LEDGER",
            "question triage_created_on precedes bound research_ledger.created_on",
        )


def build_inquiry_event(
    *,
    sequence: int,
    previous_event_id: str | None,
    event_type: str,
    occurred_on: str,
    actor_kind: str,
    question: dict[str, object],
    from_state: str | None,
    reason_code: str,
    reason: str,
    research_ledger: ResearchLedger,
    research_ledger_binding: dict[str, object],
    research_entry: dict[str, object] | None = None,
) -> dict[str, object]:
    """Build one content-addressed transition; human events remain caller input."""

    if type(sequence) is not int or sequence < 1:
        raise ValueError("sequence must be a positive integer")
    if (sequence == 1) != (previous_event_id is None):
        raise PolicyViolation(
            "v2 inquiry event sequence one must have no parent and later events must name one"
        )
    try:
        required_actor, allowed_from, to_state = _EVENT_RULES[event_type]
    except KeyError as exc:
        raise ValueError(f"unknown inquiry event type: {event_type!r}") from exc
    if actor_kind != required_actor:
        raise PolicyViolation(f"{event_type} requires actor_kind {required_actor}")
    if from_state not in allowed_from:
        raise PolicyViolation(
            f"{event_type} cannot transition from {from_state!r}; allowed={allowed_from}"
        )
    checked_research_binding = _validate_research_ledger_object_binding(
        research_ledger,
        research_ledger_binding,
        "research_ledger_binding",
    )
    _validate_question(question)
    event_date = _iso_date(occurred_on, "event.occurred_on")
    triage_date = _iso_date(
        question.get("triage_created_on"),
        "question.triage_created_on",
    )
    _validate_event_chronology(
        event_date=event_date,
        triage_date=triage_date,
        research_ledger_binding=checked_research_binding,
    )
    if event_type == "RESEARCH_CANDIDATE_RECORDED":
        if type(research_entry) is not dict:
            raise PolicyViolation(
                "research-candidate event requires a v2 event research-entry envelope"
            )
        _validate_v2_event_research_entry(
            research_entry,
            question,
            research_ledger=research_ledger,
            occurred_on=occurred_on,
        )
        entry_digest: str | None = domain_digest(
            EVENT_RESEARCH_ENTRY_DOMAIN,
            research_entry,
        )
    else:
        if research_entry is not None:
            raise PolicyViolation("only a research-candidate event may carry a research entry")
        entry_digest = None
    body: dict[str, object] = {
        "$schema": EVENT_SCHEMA_REF,
        "schema_version": EVENT_SCHEMA,
        "ledger_id": INQUIRY_LEDGER_ID,
        "sequence": sequence,
        "previous_event_id": previous_event_id,
        "event_type": event_type,
        "occurred_on": occurred_on,
        "actor_kind": actor_kind,
        "question": question,
        "from_state": from_state,
        "to_state": to_state,
        "reason_code": reason_code,
        "reason": reason,
        "research_ledger": checked_research_binding,
        "research_entry": research_entry,
        "research_entry_sha256": entry_digest,
        "semantic_verdict": None,
        "epistemic_effect": EVENT_EFFECT,
    }
    event = {**body, "event_id": _record_id("IE", EVENT_SCHEMA, body)}
    _validate_with_schema(event, "inquiry-event-v2.schema.json")
    return event


def validate_inquiry_event(
    event: dict[str, object],
    *,
    research_ledger: ResearchLedger,
    expected_research_binding: dict[str, object],
) -> None:
    if type(event) is not dict:
        raise TypeError("inquiry event must be a dictionary")
    version = event.get("schema_version")
    if version == LEGACY_EVENT_SCHEMA:
        schema_name = "inquiry-event.schema.json"
    elif version == EVENT_SCHEMA:
        schema_name = "inquiry-event-v2.schema.json"
    else:
        raise RecordError("inquiry event has an unsupported schema_version")
    _validate_with_schema(event, schema_name)
    if version == EVENT_SCHEMA and (
        (event.get("sequence") == 1)
        != (event.get("previous_event_id") is None)
    ):
        raise PolicyViolation(
            "v2 inquiry event sequence and previous-event link are inconsistent"
        )
    if event.get("event_id") != compute_event_id(event):
        raise RecordError("inquiry event content-addressed ID mismatch")
    question = _object(event.get("question"), "event.question")
    _validate_question(question)
    event_date = _iso_date(event.get("occurred_on"), "event.occurred_on")
    triage_date = _iso_date(
        question.get("triage_created_on"),
        "event.question.triage_created_on",
    )
    event_research_binding = _object(
        event.get("research_ledger"),
        "event.research_ledger",
    )
    _validate_event_chronology(
        event_date=event_date,
        triage_date=triage_date,
        research_ledger_binding=event_research_binding,
    )
    if event_research_binding != expected_research_binding:
        raise PolicyViolation("inquiry event changed the bound research ledger")
    _validate_research_ledger_object_binding(
        research_ledger,
        event_research_binding,
        "event.research_ledger",
    )
    event_type = _string(event.get("event_type"), "event_type")
    required_actor, allowed_from, to_state = _EVENT_RULES[event_type]
    if event.get("actor_kind") != required_actor:
        raise PolicyViolation(f"{event_type} requires actor_kind {required_actor}")
    if event.get("from_state") not in allowed_from or event.get("to_state") != to_state:
        raise PolicyViolation(f"illegal state transition for {event_type}")
    entry = event.get("research_entry")
    entry_digest = event.get("research_entry_sha256")
    if event_type == "RESEARCH_CANDIDATE_RECORDED":
        checked = _object(entry, "event.research_entry")
        if version == EVENT_SCHEMA:
            _validate_v2_event_research_entry(
                checked,
                _object(event.get("question"), "event.question"),
                research_ledger=research_ledger,
                occurred_on=_string(event.get("occurred_on"), "event.occurred_on"),
            )
            entry_domain = EVENT_RESEARCH_ENTRY_DOMAIN
        else:
            _validate_standalone_entry(
                checked,
                research_ledger=research_ledger,
                occurred_on=_string(event.get("occurred_on"), "event.occurred_on"),
            )
            _validate_entry_targets_question(
                checked,
                _object(event.get("question"), "event.question"),
            )
            entry_domain = LEGACY_EVENT_RESEARCH_ENTRY_DOMAIN
        if entry_digest != domain_digest(entry_domain, checked):
            raise RecordError("research-entry digest mismatch")
    elif entry is not None or entry_digest is not None:
        raise PolicyViolation("non-research event cannot carry a research entry")


def _event_filename(event_id: str) -> str:
    return _content_id(event_id, "IE", "event_id").replace(":", "-") + ".json"


def _event_claim_filename(parent_event_id: str | None) -> str:
    parent_token = (
        "GENESIS"
        if parent_event_id is None
        else _content_id(
            parent_event_id,
            "IE",
            "parent_event_id",
        ).removeprefix("IE:")
    )
    return f"NEXT-{parent_token}.claim"


def _event_inventory(events_dir: Path) -> tuple[set[str], set[str]]:
    if not isinstance(events_dir, Path):
        raise TypeError("events_dir must be pathlib.Path")
    if not events_dir.is_dir():
        raise InquiryError(
            "INQUIRY_EVENT_PARENT_MISSING",
            f"inquiry event directory does not exist: {events_dir}",
        )
    record_names: set[str] = set()
    claim_names: set[str] = set()
    for entry in events_dir.iterdir():
        if not entry.is_file():
            continue
        name = entry.name
        if name.startswith("IE-") and name.endswith(".json"):
            record_names.add(name)
        elif name.startswith("NEXT-") and name.endswith(".claim"):
            claim_names.add(name)
    return record_names, claim_names


def _event_source_report(event: dict[str, object]) -> dict[str, object]:
    entry = _object(event.get("research_entry"), "event.research_entry")
    if event.get("schema_version") == EVENT_SCHEMA:
        return _object(
            entry.get("source_report"),
            "event.research_entry.source_report",
        )
    return entry


def _load_event_file(
    path: Path,
    *,
    research_ledger: ResearchLedger,
    research_binding: dict[str, object],
) -> dict[str, object]:
    decoded, raw = _read_snapshot(path, "inquiry event")
    event = _object(decoded, "inquiry event")
    validate_inquiry_event(
        event,
        research_ledger=research_ledger,
        expected_research_binding=research_binding,
    )
    canonical = canonical_bytes(event) + b"\n"
    if raw != canonical:
        raise RecordError("inquiry event file is not canonical JSON plus one newline")
    if path.name != _event_filename(_string(event.get("event_id"), "event_id")):
        raise RecordError("inquiry event filename does not match its event ID")
    return event


def verify_inquiry_chain(
    events_dir: Path,
    head_event_id: str | None,
    *,
    research_ledger: ResearchLedger,
    research_binding: dict[str, object],
    required_schema_version: str | None = None,
    _pending_successor_claim: tuple[str, bytes] | None = None,
    _committed_successor: tuple[str, bytes] | None = None,
) -> InquiryState:
    """Verify one complete, homogeneous, explicitly selected event lineage."""

    _validate_research_ledger_object_binding(
        research_ledger,
        research_binding,
        "research_binding",
    )
    if required_schema_version not in {None, LEGACY_EVENT_SCHEMA, EVENT_SCHEMA}:
        raise ValueError("required_schema_version is unsupported")
    record_names, claim_names = _event_inventory(events_dir)
    if (
        _pending_successor_claim is not None
        and _committed_successor is not None
    ):
        raise ValueError("event recovery may name only one successor state")

    def validate_recovery_payload(
        payload: bytes,
        *,
        error_code: str,
    ) -> dict[str, object]:
        try:
            source = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise InquiryError(
                error_code,
                "event recovery content is not UTF-8",
            ) from exc
        recovered = _object(loads_strict(source), "inquiry event recovery successor")
        if canonical_bytes(recovered) + b"\n" != payload:
            raise RecordError("inquiry event recovery successor is not canonical")
        validate_inquiry_event(
            recovered,
            research_ledger=research_ledger,
            expected_research_binding=research_binding,
        )
        if recovered.get("previous_event_id") != head_event_id:
            raise InquiryError(
                error_code,
                "event recovery successor does not extend the selected parent",
            )
        if (
            required_schema_version is not None
            and recovered.get("schema_version") != required_schema_version
        ):
            raise InquiryError(
                error_code,
                "event recovery successor has the wrong schema version",
            )
        return recovered

    pending_claim_name: str | None = None
    pending_claim_payload: bytes | None = None
    committed_record_name: str | None = None
    if _pending_successor_claim is not None:
        pending_claim_name, pending_claim_payload = _pending_successor_claim
        if (
            type(pending_claim_name) is not str
            or type(pending_claim_payload) is not bytes
            or pending_claim_name not in claim_names
            or pending_claim_name != _event_claim_filename(head_event_id)
        ):
            raise InquiryError(
                "INQUIRY_EVENT_PENDING_CLAIM_INVALID",
                "pending event recovery did not identify an existing exact claim",
            )
        try:
            existing_pending = (events_dir / pending_claim_name).read_bytes()
        except OSError as exc:
            raise InquiryError(
                "INQUIRY_EVENT_CLAIM_READ_FAILED",
                f"cannot read pending inquiry event successor claim: {exc}",
            ) from exc
        if existing_pending != pending_claim_payload:
            raise InquiryError(
                "INQUIRY_EVENT_PENDING_CLAIM_INVALID",
                "pending inquiry event recovery claim changed content",
            )
        validate_recovery_payload(
            pending_claim_payload,
            error_code="INQUIRY_EVENT_PENDING_CLAIM_INVALID",
        )
    elif _committed_successor is not None:
        committed_event_id, pending_claim_payload = _committed_successor
        if type(committed_event_id) is not str or type(pending_claim_payload) is not bytes:
            raise InquiryError(
                "INQUIRY_EVENT_COMMITTED_SUCCESSOR_INVALID",
                "committed event recovery did not identify an exact successor",
            )
        pending_claim_name = _event_claim_filename(head_event_id)
        committed_record_name = _event_filename(committed_event_id)
        if (
            pending_claim_name not in claim_names
            or committed_record_name not in record_names
        ):
            raise InquiryError(
                "INQUIRY_EVENT_COMMITTED_SUCCESSOR_INVALID",
                "committed event recovery paths are incomplete",
            )
        try:
            committed_claim = (events_dir / pending_claim_name).read_bytes()
            committed_record = (events_dir / committed_record_name).read_bytes()
        except OSError as exc:
            raise InquiryError(
                "INQUIRY_EVENT_READ_FAILED",
                f"cannot read committed inquiry event successor: {exc}",
            ) from exc
        if committed_claim != pending_claim_payload or committed_record != pending_claim_payload:
            raise InquiryError(
                "INQUIRY_EVENT_COMMITTED_SUCCESSOR_INVALID",
                "committed event recovery content differs from the exact successor",
            )
        committed_event = validate_recovery_payload(
            pending_claim_payload,
            error_code="INQUIRY_EVENT_COMMITTED_SUCCESSOR_INVALID",
        )
        if (
            committed_event.get("event_id") != committed_event_id
        ):
            raise InquiryError(
                "INQUIRY_EVENT_COMMITTED_SUCCESSOR_INVALID",
                "committed event recovery does not extend the selected parent",
            )
    if head_event_id is None:
        expected_claim_names = (
            set() if pending_claim_name is None else {pending_claim_name}
        )
        expected_record_names = (
            set() if committed_record_name is None else {committed_record_name}
        )
        if record_names != expected_record_names or claim_names != expected_claim_names:
            raise InquiryError(
                "INQUIRY_EVENT_HEAD_REQUIRED",
                "an empty event head is allowed only when the event lineage is empty",
            )
        return InquiryState(None, (), {}, {})
    _content_id(head_event_id, "IE", "head_event_id")
    reverse: list[dict[str, object]] = []
    seen: set[str] = set()
    current: str | None = head_event_id
    while current is not None:
        if current in seen:
            raise RecordError("inquiry event chain contains a cycle")
        seen.add(current)
        event = _load_event_file(
            events_dir / _event_filename(current),
            research_ledger=research_ledger,
            research_binding=research_binding,
        )
        if event["event_id"] != current:
            raise RecordError("inquiry event chain resolved the wrong event")
        reverse.append(event)
        previous = event["previous_event_id"]
        current = previous if type(previous) is str else None
    events = tuple(reversed(reverse))
    versions = {
        _string(event.get("schema_version"), "event.schema_version")
        for event in events
    }
    if len(versions) != 1:
        raise InquiryError(
            "INQUIRY_EVENT_MIXED_VERSION_LINEAGE",
            "an inquiry event lineage cannot mix v1 and v2 records",
        )
    lineage_version = next(iter(versions))
    if (
        required_schema_version is not None
        and lineage_version != required_schema_version
    ):
        raise InquiryError(
            "INQUIRY_EVENT_LINEAGE_VERSION_MISMATCH",
            "the selected event lineage has the wrong schema version for this operation",
        )
    for index, event in enumerate(events, start=1):
        if event["sequence"] != index:
            raise RecordError("inquiry event sequence is not contiguous from one")
        expected_previous = None if index == 1 else events[index - 2]["event_id"]
        if event["previous_event_id"] != expected_previous:
            raise RecordError("inquiry event previous link is inconsistent")
        if index > 1 and event["occurred_on"] < events[index - 2]["occurred_on"]:
            raise PolicyViolation("inquiry event chronology moves backwards")

    expected_records = {
        _event_filename(_string(event.get("event_id"), "event.event_id"))
        for event in events
    }
    if committed_record_name is not None:
        expected_records.add(committed_record_name)
    if record_names != expected_records:
        raise InquiryError(
            "INQUIRY_EVENT_ORPHAN_RECORD",
            "event directory contains a record outside the selected complete lineage",
        )
    expected_claims: set[str] = set()
    for event in events:
        previous = event.get("previous_event_id")
        claim_name = _event_claim_filename(
            previous if type(previous) is str else None
        )
        expected_claims.add(claim_name)
        try:
            claim_payload = (events_dir / claim_name).read_bytes()
        except OSError as exc:
            raise InquiryError(
                "INQUIRY_EVENT_CLAIM_READ_FAILED",
                f"cannot read inquiry event successor claim: {exc}",
            ) from exc
        if claim_payload != canonical_bytes(event) + b"\n":
            raise InquiryError(
                "INQUIRY_EVENT_CLAIM_MISMATCH",
                "inquiry event successor claim differs from its exact successor",
            )
    if pending_claim_name is not None:
        expected_claims.add(pending_claim_name)
    if claim_names != expected_claims:
        raise InquiryError(
            "INQUIRY_EVENT_NONTERMINAL_HEAD",
            "event claims do not identify the selected record as the unique terminal head",
        )

    states: dict[str, QuestionState] = {}
    questions: dict[str, dict[str, object]] = {}
    research_entries: dict[str, dict[str, object]] = {}
    for event in events:
        question = _object(event["question"], "event.question")
        question_id = _string(question["question_id"], "question.question_id")
        prior = states.get(question_id)
        prior_value = None if prior is None else prior.value
        if event["from_state"] != prior_value:
            raise PolicyViolation(
                f"question {question_id} transition does not match replayed state"
            )
        existing = questions.get(question_id)
        if existing is not None and existing != question:
            raise PolicyViolation("an inquiry event changed an existing question record")
        questions[question_id] = question
        states[question_id] = QuestionState(event["to_state"])
        if event["event_type"] == "RESEARCH_CANDIDATE_RECORDED":
            entry = _event_source_report(event)
            entry_id = _string(entry.get("entry_id"), "research_entry.entry_id")
            existing_entry = research_entries.get(entry_id)
            if existing_entry is not None and existing_entry != entry:
                raise PolicyViolation(
                    "inquiry chain reuses a research-entry ID with different content"
                )
            research_entries[entry_id] = entry
    return InquiryState(head_event_id, events, states, questions)


def _question_digest(question: dict[str, object]) -> str:
    version = question.get("schema_version")
    if version not in {LEGACY_QUESTION_SCHEMA, QUESTION_SCHEMA}:
        raise RecordError("critical question has an unsupported schema_version")
    return domain_digest(str(version), question)


def _event_output_path(events_dir: Path, event: dict[str, object]) -> Path:
    return events_dir / _event_filename(_string(event.get("event_id"), "event_id"))


def publish_inquiry_event(
    events_dir: Path,
    event: dict[str, object],
    *,
    expected_head_event_id: str | None,
    plan: dict[str, object],
    repo_root: Path,
    run_record_path: Path,
    research_ledger_path: Path,
    triage_dir: Path,
    research_ledger: ResearchLedger,
    research_binding: dict[str, object],
) -> Path:
    """Publish one plan-authorized v2 transition without overwrite."""

    if not isinstance(events_dir, Path):
        raise TypeError("events_dir must be pathlib.Path")
    if not events_dir.is_dir():
        raise InquiryError(
            "INQUIRY_EVENT_PARENT_MISSING",
            f"inquiry event directory does not exist: {events_dir}",
        )
    if type(event) is not dict or event.get("schema_version") != EVENT_SCHEMA:
        raise PolicyViolation(
            "legacy inquiry events are immutable history and cannot be newly published"
        )
    if type(plan) is not dict or plan.get("schema_version") != PLAN_SCHEMA:
        raise PolicyViolation(
            "new inquiry event publication requires an exact active v2 plan"
        )
    validate_inquiry_event(
        event,
        research_ledger=research_ledger,
        expected_research_binding=research_binding,
    )
    if event["previous_event_id"] != expected_head_event_id:
        raise InquiryError(
            "INQUIRY_EVENT_STALE_HEAD",
            "event previous link differs from the caller's expected head",
        )

    payload = canonical_bytes(event) + b"\n"
    event_id = _string(event.get("event_id"), "event.event_id")
    output_path = _event_output_path(events_dir, event)
    claim_path = events_dir / _event_claim_filename(expected_head_event_id)
    pending_claim: tuple[str, bytes] | None = None
    committed_event: tuple[str, bytes] | None = None
    claim_exists = claim_path.exists()
    output_exists = output_path.exists()
    if output_exists and not claim_exists:
        raise InquiryError(
            "INQUIRY_EVENT_ORPHAN_RECORD",
            "inquiry event record exists without its immutable successor claim",
        )
    if claim_exists:
        try:
            existing_claim = claim_path.read_bytes()
        except OSError as exc:
            raise InquiryError(
                "INQUIRY_EVENT_CLAIM_READ_FAILED",
                f"cannot read inquiry event successor claim: {exc}",
            ) from exc
        if existing_claim != payload:
            raise InquiryError(
                "INQUIRY_EVENT_STALE_HEAD",
                "the selected parent head already has a different claimed successor",
            )
        if output_exists:
            try:
                existing_record = output_path.read_bytes()
            except OSError as exc:
                raise InquiryError(
                    "INQUIRY_EVENT_READ_FAILED",
                    f"cannot read existing inquiry event record: {exc}",
                ) from exc
            if existing_record != payload:
                raise RecordError(
                    "inquiry event record differs from its exact successor claim"
                )
            committed_event = (event_id, payload)
        else:
            pending_claim = (claim_path.name, payload)

    validate_adaptive_inquiry_plan_against_inputs(
        plan,
        repo_root=repo_root,
        run_record_path=run_record_path,
        research_ledger_path=research_ledger_path,
        triage_dir=triage_dir,
        events_dir=events_dir,
        _pending_event_claim=pending_claim,
        _committed_event=committed_event,
    )
    if plan.get("state_head_event_id") != expected_head_event_id:
        raise InquiryError(
            "INQUIRY_PLAN_STALE_HEAD",
            "supplied plan was not regenerated at the caller's expected event head",
        )
    plan_bindings = _object(plan.get("bindings"), "plan.bindings")
    if plan_bindings.get("research_ledger") != research_binding:
        raise InquiryError(
            "INQUIRY_RESEARCH_LEDGER_MISMATCH",
            "plan is not bound to the supplied research ledger",
        )
    event_type = _string(event.get("event_type"), "event.event_type")
    validate_inquiry_transition_against_plan(event_type, plan)
    validate_inquiry_question_against_plan(
        _object(event.get("question"), "event.question"),
        plan,
    )
    state = verify_inquiry_chain(
        events_dir,
        expected_head_event_id,
        research_ledger=research_ledger,
        research_binding=research_binding,
        required_schema_version=EVENT_SCHEMA,
        _pending_successor_claim=pending_claim,
        _committed_successor=committed_event,
    )
    if event["sequence"] != len(state.events) + 1:
        raise InquiryError(
            "INQUIRY_EVENT_SEQUENCE_MISMATCH",
            "event sequence does not extend the selected head",
        )
    if state.events and event["occurred_on"] < state.events[-1]["occurred_on"]:
        raise InquiryError(
            "INQUIRY_EVENT_CHRONOLOGY_REGRESSION",
            "new inquiry event date precedes its selected parent",
        )
    question = _object(event.get("question"), "event.question")
    question_id = _string(question.get("question_id"), "event.question.question_id")
    prior_state = state.question_states.get(question_id)
    prior_state_value = None if prior_state is None else prior_state.value
    if event.get("from_state") != prior_state_value:
        raise InquiryError(
            "INQUIRY_EVENT_STATE_MISMATCH",
            "event transition does not start from the replayed state of its exact question",
        )
    if event["event_type"] == "RESEARCH_CANDIDATE_RECORDED":
        new_entry = _event_source_report(event)
        new_entry_id = _string(new_entry.get("entry_id"), "research_entry.entry_id")
        for prior_event in state.events:
            prior_entry = prior_event.get("research_entry")
            if type(prior_entry) is not dict:
                continue
            prior_source = _event_source_report(prior_event)
            if prior_source.get("entry_id") == new_entry_id and prior_source != new_entry:
                raise InquiryError(
                    "INQUIRY_RESEARCH_ENTRY_ID_REUSED",
                    "research-entry ID already names different content in this chain",
                )
    if committed_event is not None:
        try:
            _fsync_directory(events_dir)
        except OSError as exc:
            raise InquiryError(
                "INQUIRY_EVENT_WRITE_FAILED",
                f"cannot durably acknowledge inquiry event: {exc}",
            ) from exc
        verify_inquiry_chain(
            events_dir,
            event_id,
            research_ledger=research_ledger,
            research_binding=research_binding,
            required_schema_version=EVENT_SCHEMA,
        )
        return output_path
    temporary_path: Path | None = None
    try:
        if pending_claim is None:
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=".inquiry-event-",
                suffix=".tmp",
                dir=events_dir,
            )
            temporary_path = Path(temporary_name)
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            try:
                os.link(temporary_path, claim_path)
            except FileExistsError as exc:
                try:
                    existing_claim = claim_path.read_bytes()
                except OSError:
                    existing_claim = b""
                if existing_claim != payload:
                    raise InquiryError(
                        "INQUIRY_EVENT_STALE_HEAD",
                        "the selected parent head already has a different claimed successor",
                    ) from exc
            _fsync_directory(events_dir)
        try:
            os.link(claim_path, output_path)
        except FileExistsError as exc:
            try:
                existing_record = output_path.read_bytes()
            except OSError:
                existing_record = b""
            if existing_record != payload:
                raise InquiryError(
                    "INQUIRY_EVENT_EXISTS",
                    f"different inquiry event content exists: {output_path}",
                ) from exc
        _fsync_directory(events_dir)
    except OSError as exc:
        if exc.errno == errno.ENOENT:
            code = "INQUIRY_EVENT_PARENT_MISSING"
        else:
            code = "INQUIRY_EVENT_WRITE_FAILED"
        raise InquiryError(code, f"cannot publish inquiry event: {exc}") from exc
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass
    verify_inquiry_chain(
        events_dir,
        event_id,
        research_ledger=research_ledger,
        research_binding=research_binding,
        required_schema_version=EVENT_SCHEMA,
    )
    return output_path


def _route(
    triage: dict[str, object] | None,
    all_questions: tuple[dict[str, object], ...],
    state: InquiryState,
    current_case_sha256: str,
) -> tuple[InquiryRoute, str, tuple[dict[str, object], ...]]:
    question_by_id = {item["question_id"]: item for item in all_questions}
    for question_id, existing in state.questions.items():
        if existing.get("case_sha256") != current_case_sha256:
            continue
        expected = question_by_id.get(question_id)
        if expected is None or existing != expected:
            return (
                InquiryRoute.POLICY_BLOCKED,
                "Event history changed a bound question.",
                (),
            )
    if triage is None:
        return (
            InquiryRoute.AWAITING_HUMAN_TRIAGE,
            "A mechanical observation cannot locate its own failure locus.",
            (),
        )
    assessments = _validate_locus_assessments(triage)
    dispositions = _validate_assessment_dispositions(triage, assessments)
    live_ids, _frontier_ids = _assessment_work_state(
        _object(triage.get("bindings"), "triage.bindings"),
        assessments,
        dispositions,
    )
    if not live_ids:
        return (
            InquiryRoute.AWAITING_HUMAN_REASSESSMENT,
            "No assessment is effective-live for these inputs; semantics remain unresolved pending human reassessment.",
            (),
        )
    action_value = triage.get("next_action")
    if action_value is None:
        live_count = len(live_ids)
        noun = (
            "One live criticism assessment is"
            if live_count == 1
            else "Multiple live criticism assessments are"
        )
        return (
            InquiryRoute.AWAITING_HUMAN_ACTION_SELECTION,
            f"{noun} recorded; no operational next action was selected.",
            (),
        )
    action = _object(action_value, "triage.next_action")
    route_intent = _string(action.get("route_intent"), "triage.next_action.route_intent")
    if route_intent == InquiryRoute.INTERNAL_HARNESS_WORK.value:
        return (
            InquiryRoute.INTERNAL_HARNESS_WORK,
            "The selected human action schedules internal harness work without dismissing other live loci.",
            (),
        )
    if route_intent == InquiryRoute.INTERNAL_MODEL_WORK.value:
        return (
            InquiryRoute.INTERNAL_MODEL_WORK,
            "The selected human action schedules internal model work without dismissing other live loci.",
            (),
        )
    if route_intent == InquiryRoute.AUTHORITY_REVIEW.value:
        return (
            InquiryRoute.AUTHORITY_REVIEW,
            "The selected human action schedules CR-1.0 authority review without dismissing other live loci.",
            (),
        )
    if route_intent != InquiryRoute.EXTERNAL_RESEARCH_REQUIRED.value:
        return InquiryRoute.POLICY_BLOCKED, "The selected action has no authorized route.", ()

    current_states = {
        question_id: state.question_states[question_id]
        for question_id in question_by_id
        if question_id in state.question_states
    }
    values = set(current_states.values())
    if QuestionState.STALE_BY_MODEL_CHANGE in values:
        return (
            InquiryRoute.POLICY_BLOCKED,
            "The current case was marked stale; a new model snapshot and triage are required.",
            (),
        )
    if QuestionState.AWAITING_HUMAN_REVIEW in values:
        return (
            InquiryRoute.AWAITING_HUMAN_REVIEW,
            "A concrete research report awaits human discrimination review; additional agreement cannot promote it.",
            (),
        )
    if QuestionState.RETIRED_WITH_CRITICISM_CANDIDATE in values:
        return (
            InquiryRoute.INTERNAL_INTEGRATION_REQUIRED,
            "A human-retained criticism candidate must be integrated and retested before more search.",
            (),
        )
    if values.intersection({QuestionState.PROPOSED, QuestionState.ACTIVE}):
        return (
            InquiryRoute.RESEARCH_IN_PROGRESS,
            "At least one exact current attack question is already proposed or active.",
            (),
        )
    uncovered = tuple(
        question
        for question in all_questions
        if question["question_id"] not in current_states
    )
    if uncovered:
        return (
            InquiryRoute.EXTERNAL_RESEARCH_REQUIRED,
            "Human-selected external work has exact rival falsifiers that remain uncovered.",
            uncovered,
        )
    return (
        InquiryRoute.NO_NEW_RESEARCH_UNDER_CURRENT_PROTOCOL,
        "Every current question for the action's selected targets is in a non-criticizing terminal state; this records no support and leaves semantics unresolved.",
        (),
    )


def build_adaptive_inquiry_plan(
    *,
    repo_root: Path,
    run_record_path: Path,
    research_ledger_path: Path,
    triage_dir: Path,
    head_triage_id: str | None = None,
    triage: dict[str, object] | None = None,
    events_dir: Path | None = None,
    head_event_id: str | None = None,
    _pending_event_claim: tuple[str, bytes] | None = None,
    _committed_event: tuple[str, bytes] | None = None,
) -> dict[str, object]:
    """Build a deterministic work-routing plan from exact current evidence."""

    report, run_raw = _load_verified_run(run_record_path, repo_root)
    ledger, _ledger_raw, research_binding = _load_research_ledger_snapshot(
        research_ledger_path
    )
    bindings, issue, warrant = _extract_bindings(report, run_raw, research_binding)
    available_attack_targets = _available_attack_targets(issue, warrant, bindings)
    triage_state = verify_human_triage_chain(
        triage_dir,
        head_triage_id,
        expected_bindings=bindings,
    )
    selected_head_triage = (
        None if not triage_state.triages else triage_state.triages[-1]
    )
    if triage is not None and triage != selected_head_triage:
        raise PolicyViolation(
            "embedded human triage does not equal the verified selected triage head"
        )
    checked_triage = selected_head_triage
    if (
        checked_triage is not None
        and checked_triage.get("schema_version") != TRIAGE_SCHEMA
    ):
        raise PolicyViolation("active inquiry construction requires human triage v2")
    if checked_triage is not None:
        _validate_action_attack_target_selection(
            checked_triage,
            available_attack_targets,
        )
    if head_event_id is not None and events_dir is None:
        raise ValueError("events_dir is required when head_event_id is supplied")
    state = (
        InquiryState(None, (), {}, {})
        if events_dir is None
        else verify_inquiry_chain(
            events_dir,
            head_event_id,
            research_ledger=ledger,
            research_binding=research_binding,
            required_schema_version=EVENT_SCHEMA,
            _pending_successor_claim=_pending_event_claim,
            _committed_successor=_committed_event,
        )
    )
    case_sha256 = _case_digest(bindings, checked_triage)
    if checked_triage is not None:
        triage_created_on = _iso_date(
            checked_triage.get("created_on"),
            "triage.created_on",
        )
        if any(
            _object(event.get("question"), "event.question").get("case_sha256")
            == case_sha256
            and _iso_date(event.get("occurred_on"), "event.occurred_on")
            < triage_created_on
            for event in state.events
        ):
            raise PolicyViolation(
                "inquiry event chronology precedes the exact plan triage.created_on"
            )
    selected_action = (
        None if checked_triage is None else checked_triage.get("next_action")
    )
    all_questions = (
        _critical_questions(
            issue,
            warrant,
            bindings,
            case_sha256,
            ledger.provider_policy.default_contemporary_discovery_provider,
            checked_triage,
            available_attack_targets,
        )
        if checked_triage is not None
        and type(selected_action) is dict
        and selected_action.get("route_intent")
        == InquiryRoute.EXTERNAL_RESEARCH_REQUIRED.value
        else ()
    )
    route, reason, proposed = _route(
        checked_triage,
        all_questions,
        state,
        case_sha256,
    )
    current_ids = {item["question_id"] for item in all_questions}
    question_state = {
        question_id: state_value.value
        for question_id, state_value in sorted(state.question_states.items())
        if question_id in current_ids
    }
    if checked_triage is None:
        live_locus_assessment_ids: list[str] = []
    else:
        checked_assessments = _validate_locus_assessments(checked_triage)
        checked_dispositions = _validate_assessment_dispositions(
            checked_triage,
            checked_assessments,
        )
        live_locus_assessment_ids = list(
            _assessment_work_state(
                bindings,
                checked_assessments,
                checked_dispositions,
            )[0]
        )
    selected_action_id = (
        None
        if type(selected_action) is not dict
        else selected_action["action_id"]
    )
    body: dict[str, object] = {
        "$schema": ADAPTIVE_SCHEMA_REF,
        "schema_version": PLAN_SCHEMA,
        "record_type": "adaptive_inquiry_plan",
        "case_sha256": case_sha256,
        "route": route.value,
        "route_reason": reason,
        "bindings": bindings,
        "triage": checked_triage,
        "available_attack_targets": list(available_attack_targets),
        "live_locus_assessment_ids": live_locus_assessment_ids,
        "selected_action_id": selected_action_id,
        "state_head_triage_id": head_triage_id,
        "state_head_event_id": head_event_id,
        "proposed_questions": list(proposed),
        "question_state": question_state,
        "semantic_verdict": None,
        "epistemic_status": "UNRESOLVED",
        "epistemic_effect": ROUTING_EFFECT,
        "epistemic_limit": NON_INDUCTIVE_LIMIT,
    }
    plan = {**body, "plan_id": _record_id("AIP", PLAN_SCHEMA, body)}
    _validate_with_schema(plan, "adaptive-inquiry-v2.schema.json")
    return plan


_LEGACY_ROUTE_REASONS = {
    InquiryRoute.AWAITING_HUMAN_TRIAGE.value: (
        "A mechanical observation cannot locate its own failure locus.",
        "The supplied record leaves the uncertainty location unresolved.",
    ),
    InquiryRoute.INTERNAL_HARNESS_WORK.value: (
        "The supplied human triage locates work in the auxiliary, fixture, or oracle contract.",
    ),
    InquiryRoute.INTERNAL_MODEL_WORK.value: (
        "The supplied human triage identifies a discriminator available through internal deduction or model finding.",
    ),
    InquiryRoute.AUTHORITY_REVIEW.value: (
        "CR-1.0 interpretation must be reviewed against the bound authority, not settled by external reports.",
    ),
    InquiryRoute.OUT_OF_SCOPE.value: (
        "The supplied human triage marks the case out of scope.",
    ),
    InquiryRoute.POLICY_BLOCKED.value: (
        "The uncertainty location has no authorized route.",
        "The current case was marked stale; a new model snapshot and triage are required.",
        "Event history changed a bound question.",
    ),
    InquiryRoute.EXTERNAL_RESEARCH_REQUIRED.value: (
        "Human triage locates an external discriminator and exact rival falsifiers remain uncovered.",
    ),
    InquiryRoute.RESEARCH_IN_PROGRESS.value: (
        "At least one exact current attack question is already proposed or active.",
    ),
    InquiryRoute.AWAITING_HUMAN_REVIEW.value: (
        "A concrete research report awaits human discrimination review; additional agreement cannot promote it.",
    ),
    InquiryRoute.INTERNAL_INTEGRATION_REQUIRED.value: (
        "A human-retained criticism candidate must be integrated and retested before more search.",
    ),
    InquiryRoute.NO_NEW_RESEARCH_UNDER_CURRENT_PROTOCOL.value: (
        "Every exact target is terminal under this protocol; this records no support and leaves semantics unresolved.",
    ),
}

_ROUTE_REASONS = {
    InquiryRoute.AWAITING_HUMAN_TRIAGE.value: (
        "A mechanical observation cannot locate its own failure locus.",
    ),
    InquiryRoute.AWAITING_HUMAN_ACTION_SELECTION.value: (
        "One live criticism assessment is recorded; no operational next action was selected.",
        "Multiple live criticism assessments are recorded; no operational next action was selected.",
    ),
    InquiryRoute.AWAITING_HUMAN_REASSESSMENT.value: (
        "No assessment is effective-live for these inputs; semantics remain unresolved pending human reassessment.",
    ),
    InquiryRoute.INTERNAL_HARNESS_WORK.value: (
        "The selected human action schedules internal harness work without dismissing other live loci.",
    ),
    InquiryRoute.INTERNAL_MODEL_WORK.value: (
        "The selected human action schedules internal model work without dismissing other live loci.",
    ),
    InquiryRoute.AUTHORITY_REVIEW.value: (
        "The selected human action schedules CR-1.0 authority review without dismissing other live loci.",
    ),
    InquiryRoute.POLICY_BLOCKED.value: (
        "The selected action has no authorized route.",
        "The current case was marked stale; a new model snapshot and triage are required.",
        "Event history changed a bound question.",
    ),
    InquiryRoute.EXTERNAL_RESEARCH_REQUIRED.value: (
        "Human-selected external work has exact rival falsifiers that remain uncovered.",
    ),
    InquiryRoute.RESEARCH_IN_PROGRESS.value: (
        "At least one exact current attack question is already proposed or active.",
    ),
    InquiryRoute.AWAITING_HUMAN_REVIEW.value: (
        "A concrete research report awaits human discrimination review; additional agreement cannot promote it.",
    ),
    InquiryRoute.INTERNAL_INTEGRATION_REQUIRED.value: (
        "A human-retained criticism candidate must be integrated and retested before more search.",
    ),
    InquiryRoute.NO_NEW_RESEARCH_UNDER_CURRENT_PROTOCOL.value: (
        "Every current question for the action's selected targets is in a non-criticizing terminal state; this records no support and leaves semantics unresolved.",
    ),
}


def _validate_plan_question_binding(
    question: dict[str, object],
    *,
    bindings: dict[str, object],
    case_sha256: str,
    triage_created_on: str,
    triage: dict[str, object] | None = None,
    available_attack_targets: tuple[dict[str, object], ...] = (),
) -> None:
    _validate_question(question)
    expected = (
        (question.get("case_sha256"), case_sha256, "case"),
        (question.get("issue_id"), bindings.get("issue_id"), "issue ID"),
        (question.get("issue_sha256"), bindings.get("issue_sha256"), "issue digest"),
        (question.get("warrant_id"), bindings.get("warrant_id"), "warrant ID"),
        (
            question.get("warrant_sha256"),
            bindings.get("warrant_sha256"),
            "warrant digest",
        ),
        (
            question.get("trigger_observation_sha256"),
            bindings.get("observation_sha256"),
            "observation digest",
        ),
        (
            question.get("model_binding_sha256"),
            _model_binding_digest(bindings),
            "model binding digest",
        ),
        (
            question.get("triage_created_on"),
            triage_created_on,
            "triage creation date",
        ),
        (question.get("epistemic_limit"), NON_INDUCTIVE_LIMIT, "epistemic limit"),
    )
    for actual, required, label in expected:
        if actual != required:
            raise PolicyViolation(f"critical question changed its bound {label}")
    if question.get("schema_version") == QUESTION_SCHEMA:
        if triage is None or triage.get("schema_version") != TRIAGE_SCHEMA:
            raise PolicyViolation("v2 critical question lacks its exact v2 triage")
        action = _object(triage.get("next_action"), "triage.next_action")
        selected_ids = list(
            _canonical_unique_strings(
                action.get("selected_assessment_ids"),
                "triage.next_action.selected_assessment_ids",
                nonempty=True,
            )
        )
        assessment_by_id = _assessment_inventory(triage)
        selected_assessments = [
            assessment_by_id[assessment_id]
            for assessment_id in selected_ids
        ]
        target_by_id = {
            _string(target.get("attack_target_id"), "attack_target_id"): target
            for target in available_attack_targets
        }
        attack_target_id = _string(
            question.get("attack_target_id"),
            "question.attack_target_id",
        )
        expected_target = target_by_id.get(attack_target_id)
        if expected_target is None:
            raise PolicyViolation(
                "critical question selects an unavailable exact attack target"
            )
        v2_expected = (
            (question.get("triage_id"), triage.get("triage_id"), "triage ID"),
            (question.get("action_id"), action.get("action_id"), "action ID"),
            (
                question.get("selected_assessment_ids"),
                selected_ids,
                "selected locus assessments",
            ),
            (
                question.get("selected_locus_assessments"),
                selected_assessments,
                "selected locus assessment records",
            ),
            (
                question.get("selected_action"),
                action.get("action"),
                "selected action text",
            ),
            (
                question.get("selection_reason"),
                action.get("reason"),
                "selection reason",
            ),
            (
                question.get("attack_target"),
                expected_target,
                "exact attack target",
            ),
        )
        for actual, required, label in v2_expected:
            if actual != required:
                raise PolicyViolation(f"critical question changed its bound {label}")


def _validate_legacy_intrinsic_route(
    plan: dict[str, object],
    triage: dict[str, object] | None,
) -> None:
    route = _string(plan.get("route"), "plan.route")
    reason = _string(plan.get("route_reason"), "plan.route_reason")
    if (
        route not in _LEGACY_ROUTE_REASONS
        or reason not in _LEGACY_ROUTE_REASONS[route]
    ):
        raise PolicyViolation("adaptive inquiry route and reason are not a declared pair")
    proposed = plan.get("proposed_questions")
    state = plan.get("question_state")
    if type(proposed) is not list or type(state) is not dict:
        raise RecordError("adaptive inquiry plan has invalid question collections")

    history_blocked = (
        route == InquiryRoute.POLICY_BLOCKED.value
        and reason == "Event history changed a bound question."
        and not proposed
    )
    if history_blocked:
        return

    if triage is None:
        if (
            route != InquiryRoute.AWAITING_HUMAN_TRIAGE.value
            or reason != _LEGACY_ROUTE_REASONS[route][0]
            or proposed
            or state
        ):
            raise PolicyViolation(
                "an untriaged observation cannot authorize a route or questions"
            )
        return

    disposition = triage["disposition"]
    location = triage["uncertainty_location"]
    external_locations = {"EXTERNAL_CRITICAL_INSTRUMENT", "APPLICATION_EMPIRICAL"}
    if disposition == "OUT_OF_SCOPE":
        expected_route = InquiryRoute.OUT_OF_SCOPE.value
    elif disposition in {"AUXILIARY_DEFECT", "TEST_DEFECT"} or location == "INTERNAL_HARNESS_SPECIFICATION":
        expected_route = InquiryRoute.INTERNAL_HARNESS_WORK.value
    elif location == "INTERNAL_DEDUCTION_OR_MODEL_FINDING":
        expected_route = InquiryRoute.INTERNAL_MODEL_WORK.value
    elif location == "CR_AUTHORITY_INTERPRETATION":
        expected_route = InquiryRoute.AUTHORITY_REVIEW.value
    elif location == "UNLOCATED":
        expected_route = InquiryRoute.AWAITING_HUMAN_TRIAGE.value
    elif location not in external_locations:
        expected_route = InquiryRoute.POLICY_BLOCKED.value
    else:
        expected_route = None

    if expected_route is not None:
        if route != expected_route or proposed or state:
            raise PolicyViolation(
                "adaptive inquiry route contradicts the supplied human triage"
            )
        return

    values = set(state.values())
    if route == InquiryRoute.EXTERNAL_RESEARCH_REQUIRED.value:
        if not proposed or any(question["question_id"] in state for question in proposed):
            raise PolicyViolation("external-research route requires uncovered questions")
    elif route == InquiryRoute.AWAITING_HUMAN_REVIEW.value:
        if proposed or QuestionState.AWAITING_HUMAN_REVIEW.value not in values:
            raise PolicyViolation("human-review route lacks an awaiting report")
    elif route == InquiryRoute.INTERNAL_INTEGRATION_REQUIRED.value:
        if proposed or QuestionState.RETIRED_WITH_CRITICISM_CANDIDATE.value not in values:
            raise PolicyViolation("integration route lacks a retained criticism candidate")
    elif route == InquiryRoute.RESEARCH_IN_PROGRESS.value:
        if proposed or not values.intersection(
            {QuestionState.PROPOSED.value, QuestionState.ACTIVE.value}
        ):
            raise PolicyViolation("research-in-progress route lacks an active question")
    elif route == InquiryRoute.POLICY_BLOCKED.value:
        stale_reason = (
            "The current case was marked stale; a new model snapshot and triage are required."
        )
        if (
            proposed
            or reason != stale_reason
            or QuestionState.STALE_BY_MODEL_CHANGE.value not in values
        ):
            raise PolicyViolation(
                "policy-blocked external route lacks its declared integrity condition"
            )
    elif route == InquiryRoute.NO_NEW_RESEARCH_UNDER_CURRENT_PROTOCOL.value:
        allowed = {
            QuestionState.RETIRED_NONDISCRIMINATING.value,
            QuestionState.RETIRED_MISFRAMED.value,
            QuestionState.RETIRED_OUT_OF_SCOPE.value,
        }
        if proposed or not values or not values.issubset(allowed):
            raise PolicyViolation("protocol-exhausted route has nonterminal questions")
    else:
        raise PolicyViolation("external human triage selected an incompatible route")


def _validate_intrinsic_route(
    plan: dict[str, object],
    triage: dict[str, object] | None,
) -> None:
    """Validate v2 routing as a projection of one explicit scheduled action."""

    route = _string(plan.get("route"), "plan.route")
    reason = _string(plan.get("route_reason"), "plan.route_reason")
    if route not in _ROUTE_REASONS or reason not in _ROUTE_REASONS[route]:
        raise PolicyViolation("adaptive inquiry route and reason are not a declared pair")
    proposed = plan.get("proposed_questions")
    state = plan.get("question_state")
    if type(proposed) is not list or type(state) is not dict:
        raise RecordError("adaptive inquiry plan has invalid question collections")
    event_head = plan.get("state_head_event_id")
    if state and event_head is None:
        raise PolicyViolation(
            "an event-derived question state requires a named event head"
        )

    history_blocked = (
        route == InquiryRoute.POLICY_BLOCKED.value
        and reason == "Event history changed a bound question."
        and not proposed
    )
    if history_blocked:
        if event_head is None:
            raise PolicyViolation(
                "an event-history integrity block requires a named event head"
            )
        return

    if triage is None:
        if (
            route != InquiryRoute.AWAITING_HUMAN_TRIAGE.value
            or reason != _ROUTE_REASONS[route][0]
            or proposed
            or state
        ):
            raise PolicyViolation(
                "an untriaged observation cannot authorize a route or questions"
            )
        return

    assessments = _validate_locus_assessments(triage)
    dispositions = _validate_assessment_dispositions(triage, assessments)
    live_ids, _frontier_ids = _assessment_work_state(
        _object(triage.get("bindings"), "triage.bindings"),
        assessments,
        dispositions,
    )
    if not live_ids:
        expected_reason = _ROUTE_REASONS[
            InquiryRoute.AWAITING_HUMAN_REASSESSMENT.value
        ][0]
        if (
            route != InquiryRoute.AWAITING_HUMAN_REASSESSMENT.value
            or reason != expected_reason
            or proposed
            or state
            or triage.get("next_action") is not None
        ):
            raise PolicyViolation(
                "a criticism set with no effective-live assessment must await human reassessment"
            )
        return

    action_value = triage.get("next_action")
    if action_value is None:
        live_count = len(live_ids)
        expected_no_action_reason = _ROUTE_REASONS[
            InquiryRoute.AWAITING_HUMAN_ACTION_SELECTION.value
        ][0 if live_count == 1 else 1]
        if (
            route != InquiryRoute.AWAITING_HUMAN_ACTION_SELECTION.value
            or reason != expected_no_action_reason
            or proposed
            or state
        ):
            raise PolicyViolation(
                "plural triage without a next action cannot authorize work or questions"
            )
        return

    action = _object(action_value, "triage.next_action")
    route_intent = _string(action.get("route_intent"), "triage.next_action.route_intent")
    if route_intent != InquiryRoute.EXTERNAL_RESEARCH_REQUIRED.value:
        if route != route_intent or proposed or state:
            raise PolicyViolation(
                "adaptive inquiry route contradicts the selected human action"
            )
        return

    values = set(state.values())
    if route == InquiryRoute.EXTERNAL_RESEARCH_REQUIRED.value:
        if not proposed or any(question["question_id"] in state for question in proposed):
            raise PolicyViolation("external-research route requires uncovered questions")
    elif route == InquiryRoute.AWAITING_HUMAN_REVIEW.value:
        if proposed or QuestionState.AWAITING_HUMAN_REVIEW.value not in values:
            raise PolicyViolation("human-review route lacks an awaiting report")
    elif route == InquiryRoute.INTERNAL_INTEGRATION_REQUIRED.value:
        if proposed or QuestionState.RETIRED_WITH_CRITICISM_CANDIDATE.value not in values:
            raise PolicyViolation("integration route lacks a retained criticism candidate")
    elif route == InquiryRoute.RESEARCH_IN_PROGRESS.value:
        if proposed or not values.intersection(
            {QuestionState.PROPOSED.value, QuestionState.ACTIVE.value}
        ):
            raise PolicyViolation("research-in-progress route lacks an active question")
    elif route == InquiryRoute.POLICY_BLOCKED.value:
        stale_reason = (
            "The current case was marked stale; a new model snapshot and triage are required."
        )
        if (
            proposed
            or reason != stale_reason
            or QuestionState.STALE_BY_MODEL_CHANGE.value not in values
        ):
            raise PolicyViolation(
                "policy-blocked external route lacks its declared integrity condition"
            )
    elif route == InquiryRoute.NO_NEW_RESEARCH_UNDER_CURRENT_PROTOCOL.value:
        allowed = {
            QuestionState.RETIRED_NONDISCRIMINATING.value,
            QuestionState.RETIRED_MISFRAMED.value,
            QuestionState.RETIRED_OUT_OF_SCOPE.value,
        }
        if proposed or not values or not values.issubset(allowed):
            raise PolicyViolation("protocol-exhausted route has nonterminal questions")
    else:
        raise PolicyViolation("selected external action has an incompatible route")


def _validate_adaptive_inquiry_plan_v1(plan: dict[str, object]) -> None:
    _validate_with_schema(plan, "adaptive-inquiry.schema.json")
    if plan.get("record_type") != "adaptive_inquiry_plan":
        raise RecordError("record is not an adaptive inquiry plan")
    if plan.get("plan_id") != compute_adaptive_inquiry_plan_id(plan):
        raise RecordError("adaptive inquiry plan content-addressed ID mismatch")
    bindings = _object(plan.get("bindings"), "plan.bindings")
    raw_triage = plan.get("triage")
    triage = (
        None
        if raw_triage is None
        else validate_human_triage(
            _object(raw_triage, "plan.triage"),
            expected_bindings=bindings,
        )
    )
    expected_case_sha256 = _case_digest(
        bindings,
        triage,
        plan_schema=LEGACY_PLAN_SCHEMA,
    )
    if plan.get("case_sha256") != expected_case_sha256:
        raise PolicyViolation("adaptive inquiry plan changed its bound case digest")
    if plan.get("epistemic_limit") != NON_INDUCTIVE_LIMIT:
        raise PolicyViolation("adaptive inquiry plan changed its non-inductive limit")
    for question in plan.get("proposed_questions", []):
        if triage is None:
            raise PolicyViolation("an untriaged plan cannot contain a critical question")
        _validate_plan_question_binding(
            _object(question, "plan.proposed_questions item"),
            bindings=bindings,
            case_sha256=expected_case_sha256,
            triage_created_on=_iso_date(
                triage.get("created_on"),
                "plan.triage.created_on",
            ),
        )
    _validate_legacy_intrinsic_route(plan, triage)
    if plan.get("semantic_verdict") is not None or plan.get("epistemic_status") != "UNRESOLVED":
        raise PolicyViolation("adaptive inquiry cannot emit a positive semantic status")


def _validate_adaptive_inquiry_plan_v2(plan: dict[str, object]) -> None:
    _validate_with_schema(plan, "adaptive-inquiry-v2.schema.json")
    if plan.get("record_type") != "adaptive_inquiry_plan":
        raise RecordError("record is not an adaptive inquiry plan")
    if plan.get("plan_id") != compute_adaptive_inquiry_plan_id(plan):
        raise RecordError("adaptive inquiry plan content-addressed ID mismatch")
    bindings = _object(plan.get("bindings"), "plan.bindings")
    raw_triage = plan.get("triage")
    triage = (
        None
        if raw_triage is None
        else validate_human_triage(
            _object(raw_triage, "plan.triage"),
            expected_bindings=bindings,
        )
    )
    if triage is not None and triage.get("schema_version") != TRIAGE_SCHEMA:
        raise PolicyViolation("a v2 plan cannot embed legacy human triage")
    expected_head_triage_id = None if triage is None else triage.get("triage_id")
    if plan.get("state_head_triage_id") != expected_head_triage_id:
        raise PolicyViolation(
            "adaptive inquiry plan changed its selected human triage head"
        )
    expected_case_sha256 = _case_digest(bindings, triage, plan_schema=PLAN_SCHEMA)
    if plan.get("case_sha256") != expected_case_sha256:
        raise PolicyViolation("adaptive inquiry plan changed its bound case digest")
    if plan.get("epistemic_limit") != NON_INDUCTIVE_LIMIT:
        raise PolicyViolation("adaptive inquiry plan changed its non-inductive limit")

    available_attack_targets = _validate_attack_target_menu(
        plan.get("available_attack_targets"),
        "plan.available_attack_targets",
    )
    for target in available_attack_targets:
        if (
            target.get("issue_sha256") != bindings.get("issue_sha256")
            or target.get("warrant_sha256") != bindings.get("warrant_sha256")
        ):
            raise PolicyViolation(
                "available attack target changed its issue or warrant binding"
            )

    if triage is None:
        expected_live_ids: list[str] = []
    else:
        assessments = _validate_locus_assessments(triage)
        dispositions = _validate_assessment_dispositions(triage, assessments)
        expected_live_ids = list(
            _assessment_work_state(bindings, assessments, dispositions)[0]
        )
    if plan.get("live_locus_assessment_ids") != expected_live_ids:
        raise PolicyViolation("adaptive inquiry plan changed its live locus inventory")
    action = None if triage is None else triage.get("next_action")
    expected_action_id = None if type(action) is not dict else action["action_id"]
    if plan.get("selected_action_id") != expected_action_id:
        raise PolicyViolation("adaptive inquiry plan changed its selected action ID")
    if triage is not None:
        _validate_action_attack_target_selection(
            triage,
            available_attack_targets,
        )

    for question in plan.get("proposed_questions", []):
        if triage is None or type(action) is not dict:
            raise PolicyViolation(
                "a plan without a selected action cannot contain a critical question"
            )
        if action.get("route_intent") != InquiryRoute.EXTERNAL_RESEARCH_REQUIRED.value:
            raise PolicyViolation(
                "a non-external selected action cannot contain a critical question"
            )
        _validate_plan_question_binding(
            _object(question, "plan.proposed_questions item"),
            bindings=bindings,
            case_sha256=expected_case_sha256,
            triage_created_on=_iso_date(
                triage.get("created_on"),
                "plan.triage.created_on",
            ),
            triage=triage,
            available_attack_targets=available_attack_targets,
        )
    _validate_intrinsic_route(plan, triage)
    if plan.get("semantic_verdict") is not None or plan.get("epistemic_status") != "UNRESOLVED":
        raise PolicyViolation("adaptive inquiry cannot emit a positive semantic status")


def validate_adaptive_inquiry_plan(plan: dict[str, object]) -> None:
    if type(plan) is not dict:
        raise TypeError("adaptive inquiry plan must be a dictionary")
    version = plan.get("schema_version")
    if version == LEGACY_PLAN_SCHEMA:
        _validate_adaptive_inquiry_plan_v1(plan)
    elif version == PLAN_SCHEMA:
        _validate_adaptive_inquiry_plan_v2(plan)
    else:
        raise RecordError("adaptive inquiry plan has an unsupported schema_version")


def validate_adaptive_inquiry_plan_against_inputs(
    plan: dict[str, object],
    *,
    repo_root: Path,
    run_record_path: Path,
    research_ledger_path: Path,
    triage_dir: Path,
    events_dir: Path | None = None,
    _pending_event_claim: tuple[str, bytes] | None = None,
    _committed_event: tuple[str, bytes] | None = None,
) -> None:
    """Regenerate a plan from its declared origin head and exact external inputs."""

    validate_adaptive_inquiry_plan(plan)
    if plan.get("schema_version") != PLAN_SCHEMA:
        raise PolicyViolation(
            "legacy inquiry plans are immutable history, not active transition authority"
        )
    head = plan.get("state_head_event_id")
    if head is not None and events_dir is None:
        raise ValueError("events_dir is required for a plan with an event head")
    expected = build_adaptive_inquiry_plan(
        repo_root=repo_root,
        run_record_path=run_record_path,
        research_ledger_path=research_ledger_path,
        triage_dir=triage_dir,
        head_triage_id=plan.get("state_head_triage_id"),  # type: ignore[arg-type]
        triage=plan.get("triage"),  # type: ignore[arg-type]
        events_dir=events_dir,
        head_event_id=head,  # type: ignore[arg-type]
        _pending_event_claim=_pending_event_claim,
        _committed_event=_committed_event,
    )
    if plan != expected:
        raise PolicyViolation(
            "adaptive inquiry plan differs from exact deterministic regeneration"
        )


def validate_inquiry_question_against_plan(
    question: dict[str, object],
    plan: dict[str, object],
) -> None:
    """Check intrinsic question/plan compatibility, not event-lineage authority."""

    validate_adaptive_inquiry_plan(plan)
    triage = _object(plan.get("triage"), "plan.triage")
    _validate_plan_question_binding(
        question,
        bindings=_object(plan.get("bindings"), "plan.bindings"),
        case_sha256=_string(plan.get("case_sha256"), "plan.case_sha256"),
        triage_created_on=_iso_date(
            triage.get("created_on"),
            "plan.triage.created_on",
        ),
        triage=triage if plan.get("schema_version") == PLAN_SCHEMA else None,
        available_attack_targets=(
            _validate_attack_target_menu(
                plan.get("available_attack_targets"),
                "plan.available_attack_targets",
            )
            if plan.get("schema_version") == PLAN_SCHEMA
            else ()
        ),
    )
    question_id = _string(question.get("question_id"), "question.question_id")
    proposed = {
        _string(item.get("question_id"), "plan.proposed_question.question_id"): item
        for item in plan["proposed_questions"]  # type: ignore[index]
    }
    question_state = _object(plan.get("question_state"), "plan.question_state")
    if question_id not in proposed and question_id not in question_state:
        raise PolicyViolation(
            "critical question is absent from the exact plan inventory"
        )
    expected = proposed.get(question_id)
    if expected is not None and expected != question:
        raise PolicyViolation(
            "critical question differs from the exact proposed plan record"
        )


def validate_inquiry_transition_against_plan(
    event_type: str,
    plan: dict[str, object],
) -> None:
    """Check intrinsic route compatibility, not event-lineage authority."""

    validate_adaptive_inquiry_plan(plan)
    if plan.get("schema_version") != PLAN_SCHEMA:
        raise PolicyViolation(
            "legacy inquiry plans are immutable history, not active transition authority"
        )
    route = _string(plan.get("route"), "plan.route")
    allowed = _ACTIONABLE_ROUTE_EVENT_TYPES.get(route, frozenset())
    if event_type not in allowed:
        raise InquiryError(
            "INQUIRY_ROUTE_NOT_ACTIONABLE",
            f"{event_type} is not authorized while the exact plan route is {route}",
        )


def dumps_adaptive_inquiry_plan(plan: dict[str, object]) -> str:
    validate_adaptive_inquiry_plan(plan)
    return canonical_bytes(plan).decode("utf-8")


def loads_adaptive_inquiry_plan(source: str) -> dict[str, object]:
    plan = _object(loads_strict(source), "adaptive inquiry plan")
    validate_adaptive_inquiry_plan(plan)
    return plan


def load_human_triage(path: Path) -> dict[str, object]:
    decoded, _raw = _read_snapshot(path, "human triage")
    triage = _object(decoded, "human triage")
    version = triage.get("schema_version")
    if version == LEGACY_TRIAGE_SCHEMA:
        schema_name = "adaptive-inquiry.schema.json"
    elif version == TRIAGE_SCHEMA:
        schema_name = "adaptive-inquiry-v2.schema.json"
    else:
        raise RecordError("human triage file has an unsupported schema_version")
    _validate_with_schema(triage, schema_name)
    if triage.get("record_type") != "human_failure_triage":
        raise RecordError("file is not a human_failure_triage record")
    return triage


def load_research_ledger_binding(
    path: Path,
) -> tuple[ResearchLedger, dict[str, object]]:
    ledger, _raw, binding = _load_research_ledger_snapshot(path)
    return ledger, binding


def inquiry_question_digest(question: dict[str, object]) -> str:
    _validate_question(question)
    return _question_digest(question)


def terminal_question_states() -> frozenset[QuestionState]:
    return frozenset(
        {
            QuestionState.RETIRED_WITH_CRITICISM_CANDIDATE,
            QuestionState.RETIRED_NONDISCRIMINATING,
            QuestionState.RETIRED_MISFRAMED,
            QuestionState.RETIRED_OUT_OF_SCOPE,
            QuestionState.STALE_BY_MODEL_CHANGE,
        }
    )


def iter_question_ids(plan: dict[str, object]) -> Iterable[str]:
    validate_adaptive_inquiry_plan(plan)
    for question in plan["proposed_questions"]:  # type: ignore[index]
        yield question["question_id"]  # type: ignore[index]
