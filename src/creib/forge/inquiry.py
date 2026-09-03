"""Additive adaptive-inquiry protocol for the semantic-model forge.

The protocol routes work; it does not decide CR-1.0 semantics.  A mechanical
calibration observation remains only a criticism candidate until a separately
supplied human triage record locates the uncertainty.  External reports may
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


TRIAGE_SCHEMA = "creib.semantic-forge.human-failure-triage.v1"
PLAN_SCHEMA = "creib.semantic-forge.adaptive-inquiry-plan.v1"
QUESTION_SCHEMA = "creib.semantic-forge.critical-question.v1"
EVENT_SCHEMA = "creib.semantic-forge.inquiry-event.v1"
ADAPTIVE_SCHEMA_REF = "../schema/adaptive-inquiry.schema.json"
EVENT_SCHEMA_REF = "../schema/inquiry-event.schema.json"
INQUIRY_LEDGER_ID = "SMF-INQUIRY-CR-1-0"

OBSERVATION_POINTER = "/fixture_evaluations/weak_typed_role_projection"
OBSERVATION_KIND = "CRITICISM_CANDIDATE_NOT_SEMANTIC_VERDICT"
ROUTING_EFFECT = "WORKFLOW_ROUTING_ONLY"
EVENT_EFFECT = "MAY_CRITICIZE_OR_ROUTE_WORK_ONLY"
EVENT_RESEARCH_ENTRY_DOMAIN = "creib.semantic-forge.inquiry-event-entry-binding.v1"

_SHA256 = "sha256:"


class InquiryRoute(str, Enum):
    AWAITING_HUMAN_TRIAGE = "AWAITING_HUMAN_TRIAGE"
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
    body = _without(record, "triage_id")
    return _record_id("HT", TRIAGE_SCHEMA, body)


def compute_question_id(record: dict[str, object]) -> str:
    if type(record) is not dict:
        raise TypeError("critical question must be a dictionary")
    return _record_id("IQ", QUESTION_SCHEMA, _without(record, "question_id"))


def compute_adaptive_inquiry_plan_id(record: dict[str, object]) -> str:
    if type(record) is not dict:
        raise TypeError("adaptive inquiry plan must be a dictionary")
    return _record_id("AIP", PLAN_SCHEMA, _without(record, "plan_id"))


def compute_event_id(record: dict[str, object]) -> str:
    if type(record) is not dict:
        raise TypeError("inquiry event must be a dictionary")
    return _record_id("IE", EVENT_SCHEMA, _without(record, "event_id"))


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


def validate_human_triage(
    triage: dict[str, object],
    *,
    expected_bindings: dict[str, object],
) -> dict[str, object]:
    """Validate a supplied human record without inventing its disposition."""

    if type(triage) is not dict:
        raise TypeError("human triage must be a dictionary")
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


def _case_digest(
    bindings: dict[str, object],
    triage: dict[str, object] | None,
) -> str:
    return domain_digest(
        "creib.semantic-forge.adaptive-inquiry-case.v1",
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


def _critical_questions(
    issue: Issue,
    warrant: ResearchWarrant,
    bindings: dict[str, object],
    case_sha256: str,
    default_contemporary_provider: str,
    triage_created_on: str,
) -> tuple[dict[str, object], ...]:
    if (
        not warrant.discovery_channels
        or warrant.discovery_channels[0] != default_contemporary_provider
    ):
        raise PolicyViolation(
            "bound run and research ledger disagree on the default discovery provider"
        )
    model_binding_sha256 = _model_binding_digest(bindings)
    questions: list[dict[str, object]] = []
    for rival in issue.rivals:
        for falsifier in rival.falsifier_conditions:
            target_body: dict[str, object] = {
                "issue_sha256": bindings["issue_sha256"],
                "warrant_sha256": bindings["warrant_sha256"],
                "rival_id": rival.rival_id,
                "rival_claim": rival.claim,
                "falsifier_condition": falsifier,
            }
            attack_target_id = _record_id(
                "AT",
                "creib.semantic-forge.attack-target.v1",
                target_body,
            )
            body: dict[str, object] = {
                "schema_version": QUESTION_SCHEMA,
                "case_sha256": case_sha256,
                "issue_id": issue.issue_id,
                "issue_sha256": bindings["issue_sha256"],
                "warrant_id": warrant.warrant_id,
                "warrant_sha256": bindings["warrant_sha256"],
                "model_binding_sha256": model_binding_sha256,
                "trigger_observation_sha256": bindings["observation_sha256"],
                "triage_created_on": _iso_date(
                    triage_created_on,
                    "triage.created_on",
                ),
                "attack_target_id": attack_target_id,
                "rival_id": rival.rival_id,
                "rival_claim": rival.claim,
                "falsifier_condition": falsifier,
                "purpose": "RIVAL_FALSIFIER",
                "query": (
                    "Seek a counterexample, boundary case, explicit denial, or "
                    f"discriminating instrument for rival {rival.rival_id}: "
                    f"{rival.claim} Exact attack: {falsifier} Report a direct "
                    "primary-source locator or reproducible construction and the "
                    "premise it attacks. If none is found under the declared "
                    "protocol, leave the question open; absence supplies no "
                    "support and cannot retire the question in protocol v1."
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
    if question.get("question_id") != compute_question_id(question):
        raise RecordError("critical question content-addressed ID mismatch")
    _iso_date(question.get("triage_created_on"), "question.triage_created_on")
    forbidden = {"confidence", "consensus", "citation_count", "source_count", "winner"}
    leaked = sorted(forbidden.intersection(question))
    if leaked:
        raise PolicyViolation(f"critical question contains promotive fields: {leaked}")
    fixed = {
        "schema_version": QUESTION_SCHEMA,
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
                "research-candidate event requires a standalone research entry"
            )
        _validate_standalone_entry(
            research_entry,
            research_ledger=research_ledger,
            occurred_on=occurred_on,
        )
        _validate_entry_targets_question(research_entry, question)
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
    _validate_with_schema(event, "inquiry-event.schema.json")
    return event


def validate_inquiry_event(
    event: dict[str, object],
    *,
    research_ledger: ResearchLedger,
    expected_research_binding: dict[str, object],
) -> None:
    if type(event) is not dict:
        raise TypeError("inquiry event must be a dictionary")
    _validate_with_schema(event, "inquiry-event.schema.json")
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
        _validate_standalone_entry(
            checked,
            research_ledger=research_ledger,
            occurred_on=_string(event.get("occurred_on"), "event.occurred_on"),
        )
        _validate_entry_targets_question(
            checked,
            _object(event.get("question"), "event.question"),
        )
        if entry_digest != domain_digest(EVENT_RESEARCH_ENTRY_DOMAIN, checked):
            raise RecordError("research-entry digest mismatch")
    elif entry is not None or entry_digest is not None:
        raise PolicyViolation("non-research event cannot carry a research entry")


def _event_filename(event_id: str) -> str:
    value = _string(event_id, "event_id")
    if not value.startswith("IE:") or len(value) != 67:
        raise RecordError("event_id has an invalid shape")
    return value.replace(":", "-") + ".json"


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
) -> InquiryState:
    """Verify one explicitly selected chain; directory order never selects a head."""

    _validate_research_ledger_object_binding(
        research_ledger,
        research_binding,
        "research_binding",
    )
    if head_event_id is None:
        return InquiryState(None, (), {}, {})
    if not isinstance(events_dir, Path):
        raise TypeError("events_dir must be pathlib.Path")
    if not events_dir.is_dir():
        raise RecordError(f"inquiry event directory does not exist: {events_dir}")
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
    for index, event in enumerate(events, start=1):
        if event["sequence"] != index:
            raise RecordError("inquiry event sequence is not contiguous from one")
        expected_previous = None if index == 1 else events[index - 2]["event_id"]
        if event["previous_event_id"] != expected_previous:
            raise RecordError("inquiry event previous link is inconsistent")
        if index > 1 and event["occurred_on"] < events[index - 2]["occurred_on"]:
            raise PolicyViolation("inquiry event chronology moves backwards")

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
            entry = _object(event["research_entry"], "event.research_entry")
            entry_id = _string(entry.get("entry_id"), "research_entry.entry_id")
            existing_entry = research_entries.get(entry_id)
            if existing_entry is not None and existing_entry != entry:
                raise PolicyViolation(
                    "inquiry chain reuses a research-entry ID with different content"
                )
            research_entries[entry_id] = entry
    return InquiryState(head_event_id, events, states, questions)


def _question_digest(question: dict[str, object]) -> str:
    return domain_digest(QUESTION_SCHEMA, question)


def _event_output_path(events_dir: Path, event: dict[str, object]) -> Path:
    return events_dir / _event_filename(_string(event.get("event_id"), "event_id"))


def publish_inquiry_event(
    events_dir: Path,
    event: dict[str, object],
    *,
    expected_head_event_id: str | None,
    research_ledger: ResearchLedger,
    research_binding: dict[str, object],
) -> Path:
    """Publish without overwrite and atomically reserve the selected parent head."""

    if not isinstance(events_dir, Path):
        raise TypeError("events_dir must be pathlib.Path")
    if not events_dir.is_dir():
        raise InquiryError(
            "INQUIRY_EVENT_PARENT_MISSING",
            f"inquiry event directory does not exist: {events_dir}",
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
    state = verify_inquiry_chain(
        events_dir,
        expected_head_event_id,
        research_ledger=research_ledger,
        research_binding=research_binding,
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
    if event["event_type"] == "RESEARCH_CANDIDATE_RECORDED":
        new_entry = _object(event["research_entry"], "event.research_entry")
        new_entry_id = _string(new_entry.get("entry_id"), "research_entry.entry_id")
        for prior_event in state.events:
            prior_entry = prior_event.get("research_entry")
            if type(prior_entry) is not dict:
                continue
            if prior_entry.get("entry_id") == new_entry_id and prior_entry != new_entry:
                raise InquiryError(
                    "INQUIRY_RESEARCH_ENTRY_ID_REUSED",
                    "research-entry ID already names different content in this chain",
                )
    payload = canonical_bytes(event) + b"\n"
    output_path = _event_output_path(events_dir, event)
    parent_token = (
        "GENESIS" if expected_head_event_id is None else expected_head_event_id.removeprefix("IE:")
    )
    claim_path = events_dir / f"NEXT-{parent_token}.claim"
    temporary_path: Path | None = None
    try:
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
        try:
            os.link(claim_path, output_path)
        except FileExistsError as exc:
            raise InquiryError(
                "INQUIRY_EVENT_EXISTS",
                f"inquiry event already exists: {output_path}",
            ) from exc
        directory_fd = os.open(events_dir, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
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
    disposition = triage["disposition"]
    location = triage["uncertainty_location"]
    if disposition == "OUT_OF_SCOPE":
        return InquiryRoute.OUT_OF_SCOPE, "The supplied human triage marks the case out of scope.", ()
    if disposition in {"AUXILIARY_DEFECT", "TEST_DEFECT"} or location == "INTERNAL_HARNESS_SPECIFICATION":
        return (
            InquiryRoute.INTERNAL_HARNESS_WORK,
            "The supplied human triage locates work in the auxiliary, fixture, or oracle contract.",
            (),
        )
    if location == "INTERNAL_DEDUCTION_OR_MODEL_FINDING":
        return (
            InquiryRoute.INTERNAL_MODEL_WORK,
            "The supplied human triage identifies a discriminator available through internal deduction or model finding.",
            (),
        )
    if location == "CR_AUTHORITY_INTERPRETATION":
        return (
            InquiryRoute.AUTHORITY_REVIEW,
            "CR-1.0 interpretation must be reviewed against the bound authority, not settled by external reports.",
            (),
        )
    if location == "UNLOCATED":
        return (
            InquiryRoute.AWAITING_HUMAN_TRIAGE,
            "The supplied record leaves the uncertainty location unresolved.",
            (),
        )
    if location not in {"EXTERNAL_CRITICAL_INSTRUMENT", "APPLICATION_EMPIRICAL"}:
        return InquiryRoute.POLICY_BLOCKED, "The uncertainty location has no authorized route.", ()

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
            "Human triage locates an external discriminator and exact rival falsifiers remain uncovered.",
            uncovered,
        )
    return (
        InquiryRoute.NO_NEW_RESEARCH_UNDER_CURRENT_PROTOCOL,
        "Every exact target is terminal under this protocol; this records no support and leaves semantics unresolved.",
        (),
    )


def build_adaptive_inquiry_plan(
    *,
    repo_root: Path,
    run_record_path: Path,
    research_ledger_path: Path,
    triage: dict[str, object] | None = None,
    events_dir: Path | None = None,
    head_event_id: str | None = None,
) -> dict[str, object]:
    """Build a deterministic work-routing plan from exact current evidence."""

    report, run_raw = _load_verified_run(run_record_path, repo_root)
    ledger, _ledger_raw, research_binding = _load_research_ledger_snapshot(
        research_ledger_path
    )
    bindings, issue, warrant = _extract_bindings(report, run_raw, research_binding)
    checked_triage = (
        None
        if triage is None
        else validate_human_triage(triage, expected_bindings=bindings)
    )
    if head_event_id is not None and events_dir is None:
        raise ValueError("events_dir is required when head_event_id is supplied")
    state = verify_inquiry_chain(
        events_dir if events_dir is not None else Path("."),
        head_event_id,
        research_ledger=ledger,
        research_binding=research_binding,
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
    all_questions = (
        ()
        if checked_triage is None
        else _critical_questions(
            issue,
            warrant,
            bindings,
            case_sha256,
            ledger.provider_policy.default_contemporary_discovery_provider,
            _string(checked_triage.get("created_on"), "triage.created_on"),
        )
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
    body: dict[str, object] = {
        "$schema": ADAPTIVE_SCHEMA_REF,
        "schema_version": PLAN_SCHEMA,
        "record_type": "adaptive_inquiry_plan",
        "case_sha256": case_sha256,
        "route": route.value,
        "route_reason": reason,
        "bindings": bindings,
        "triage": checked_triage,
        "state_head_event_id": head_event_id,
        "proposed_questions": list(proposed),
        "question_state": question_state,
        "semantic_verdict": None,
        "epistemic_status": "UNRESOLVED",
        "epistemic_effect": ROUTING_EFFECT,
        "epistemic_limit": NON_INDUCTIVE_LIMIT,
    }
    plan = {**body, "plan_id": _record_id("AIP", PLAN_SCHEMA, body)}
    _validate_with_schema(plan, "adaptive-inquiry.schema.json")
    return plan


_ROUTE_REASONS = {
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


def _validate_plan_question_binding(
    question: dict[str, object],
    *,
    bindings: dict[str, object],
    case_sha256: str,
    triage_created_on: str,
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


def _validate_intrinsic_route(
    plan: dict[str, object],
    triage: dict[str, object] | None,
) -> None:
    route = _string(plan.get("route"), "plan.route")
    reason = _string(plan.get("route_reason"), "plan.route_reason")
    if route not in _ROUTE_REASONS or reason not in _ROUTE_REASONS[route]:
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
            or reason != _ROUTE_REASONS[route][0]
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


def validate_adaptive_inquiry_plan(plan: dict[str, object]) -> None:
    if type(plan) is not dict:
        raise TypeError("adaptive inquiry plan must be a dictionary")
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
    expected_case_sha256 = _case_digest(bindings, triage)
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
    _validate_intrinsic_route(plan, triage)
    if plan.get("semantic_verdict") is not None or plan.get("epistemic_status") != "UNRESOLVED":
        raise PolicyViolation("adaptive inquiry cannot emit a positive semantic status")


def validate_adaptive_inquiry_plan_against_inputs(
    plan: dict[str, object],
    *,
    repo_root: Path,
    run_record_path: Path,
    research_ledger_path: Path,
    events_dir: Path | None = None,
) -> None:
    """Regenerate a plan from its declared origin head and exact external inputs."""

    validate_adaptive_inquiry_plan(plan)
    head = plan.get("state_head_event_id")
    if head is not None and events_dir is None:
        raise ValueError("events_dir is required for a plan with an event head")
    expected = build_adaptive_inquiry_plan(
        repo_root=repo_root,
        run_record_path=run_record_path,
        research_ledger_path=research_ledger_path,
        triage=plan.get("triage"),  # type: ignore[arg-type]
        events_dir=events_dir,
        head_event_id=head,  # type: ignore[arg-type]
    )
    if plan != expected:
        raise PolicyViolation(
            "adaptive inquiry plan differs from exact deterministic regeneration"
        )


def validate_inquiry_question_against_plan(
    question: dict[str, object],
    plan: dict[str, object],
) -> None:
    """Check that a question belongs to the exact case bound by a valid plan."""

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
    """Require the exact route to authorize this class of lifecycle work."""

    validate_adaptive_inquiry_plan(plan)
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
    _validate_with_schema(triage, "adaptive-inquiry.schema.json")
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
