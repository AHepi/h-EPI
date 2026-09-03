"""Strict immutable records for the semantic-model forge.

These records describe criticism and comparison surfaces.  They do not assign
truth, probability, or confirmation to a conjecture.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Any

from creib.errors import PolicyViolation, RecordError


ISSUE_SCHEMA = "creib.semantic-forge.issue.v1"
WARRANT_SCHEMA = "creib.semantic-forge.research-warrant.v1"
CHALLENGE_SCHEMA = "creib.semantic-forge.minimal-pair.v1"
ASSESSMENT_SCHEMA = "creib.semantic-forge.hardening-assessment.v1"
READINESS_SCHEMA = "creib.semantic-forge.formalization-readiness.v1"

NON_INDUCTIVE_LIMIT = (
    "Survival of criticism leaves a claim unrefuted; pass counts, consensus, "
    "and confidence do not justify it."
)

_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9._:-]{0,127}$")
_DEFECT_KEY = re.compile(r"^[a-z][a-z0-9_]{0,127}$")


class UnknownKind(str, Enum):
    """Where the missing discriminator must be sought."""

    EXTERNAL = "external"
    INTERNAL = "internal"


class DefectType(str, Enum):
    """Seed templates for known defects, not an exhaustive defect ontology."""

    ROLE_RELABELING = "role_relabeling"
    PROBLEM_TRIGGER_COLLAPSE = "problem_trigger_collapse"
    CONJECTURE_CRITICISM_ORDER = "conjecture_criticism_order"
    ARBITRARY_REJECTION = "arbitrary_rejection"
    REPAIR_PROVENANCE = "repair_provenance"
    RECEIVED_CREATED_COLLAPSE = "received_created_collapse"
    PLAYBACK_ZOMBIE = "playback_zombie"
    INDUCTIVE_WARRANT = "inductive_warrant"
    PRIVILEGED_CRITIC = "privileged_critic"
    METRIC_TRUTH_COLLAPSE = "metric_truth_collapse"
    CONVERGENCE_SMUGGLING = "convergence_smuggling"
    PRIMITIVE_VACUITY = "primitive_vacuity"
    SCOPE_ESCAPE = "scope_escape"
    SUBSTRATE_OVERFIT = "substrate_overfit"


class OracleStatus(str, Enum):
    """Explicitly non-final status of a proposed challenge oracle."""

    SOURCE_SCOPED = "source_scoped"
    INTERPRETATION_PROVISIONAL = "interpretation_provisional"
    PROJECT_IMPORT_PROVISIONAL = "project_import_provisional"


class PreservationDimension(str, Enum):
    """Independent obligations; they are never combined into a score."""

    ADMITTED_CLASS_NOT_BROADENED = "admitted_class_not_broadened"
    INTENDED_REACH_PRESERVED = "intended_reach_preserved"
    CLAIMS_AND_MODALITY_PRESERVED = "claims_and_modality_preserved"
    DISTINCTIONS_PRESERVED = "distinctions_preserved"


REQUIRED_PRESERVATION_DIMENSIONS = frozenset(PreservationDimension)


class JustificationBasis(str, Enum):
    """Typed bases named in a hardening report.

    The first four can expose a defect or establish a relative formal fact.
    The final three are representable only so an attempted illicit promotion
    can be rejected explicitly.
    """

    SOURCE_TEXT = "source_text"
    DEDUCTIVE_CONSEQUENCE = "deductive_consequence"
    COUNTEREXAMPLE = "counterexample"
    CAUSAL_DISCRIMINATION = "causal_discrimination"
    PASS_COUNT = "pass_count"
    CONSENSUS = "consensus"
    CONFIDENCE = "confidence"


PROHIBITED_JUSTIFICATION_BASES = frozenset(
    {
        JustificationBasis.PASS_COUNT,
        JustificationBasis.CONSENSUS,
        JustificationBasis.CONFIDENCE,
    }
)


class HardeningStatus(str, Enum):
    HARDENING_UNREFUTED = "HARDENING_UNREFUTED"
    NO_HARDENING = "NO_HARDENING"
    UNRESOLVED = "UNRESOLVED"


class ReadinessStatus(str, Enum):
    PROVISIONALLY_READY = "PROVISIONALLY_READY"
    BLOCKED = "BLOCKED"


def _text(value: Any, where: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{where} must be a non-empty string")
    if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
        raise ValueError(f"{where} contains a Unicode surrogate")
    return value


def _optional_text(value: Any, where: str) -> str | None:
    if value is None:
        return None
    return _text(value, where)


def _identifier_text(value: Any, where: str) -> str:
    text = _text(value, where)
    if not _IDENTIFIER.fullmatch(text):
        raise ValueError(f"{where} must be a stable identifier")
    return text


def _text_tuple(value: Any, where: str, *, nonempty: bool = False) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{where} must be a tuple")
    if nonempty and not value:
        raise ValueError(f"{where} must not be empty")
    checked = tuple(_text(item, f"{where}[{index}]") for index, item in enumerate(value))
    if len(checked) != len(set(checked)):
        raise ValueError(f"{where} must not contain duplicates")
    return checked


def _typed_tuple(value: Any, expected: type, where: str) -> tuple[Any, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{where} must be a tuple")
    for index, item in enumerate(value):
        if type(item) is not expected:
            raise ValueError(f"{where}[{index}] must be {expected.__name__}")
    if len(value) != len(set(value)):
        raise ValueError(f"{where} must not contain duplicates")
    return value


def _oracle_status(value: Any, where: str) -> OracleStatus:
    oracle = _text(value, where)
    if "\n" in oracle or "\r" in oracle:
        raise ValueError(f"{where} must be a single-line status and rationale")
    prefix, separator, rationale = oracle.partition(";")
    if separator != ";" or not rationale.strip() or not prefix.startswith("status="):
        raise ValueError(
            f"{where} must declare status=<non-final-status>; followed by a rationale"
        )
    try:
        return OracleStatus(prefix.removeprefix("status="))
    except ValueError as exc:
        allowed = ", ".join(status.value for status in OracleStatus)
        raise ValueError(f"{where} status must be one of: {allowed}") from exc


@dataclass(frozen=True)
class Rival:
    """One live answer and conditions that could criticize it."""

    rival_id: str
    claim: str
    falsifier_conditions: tuple[str, ...]

    def __post_init__(self) -> None:
        _identifier_text(self.rival_id, "rival.rival_id")
        _text(self.claim, "rival.claim")
        _text_tuple(self.falsifier_conditions, "rival.falsifier_conditions")

    def to_dict(self) -> dict[str, object]:
        return {
            "rival_id": self.rival_id,
            "claim": self.claim,
            "falsifier_conditions": list(self.falsifier_conditions),
        }


@dataclass(frozen=True)
class Issue:
    """An explicit gap whose relation to a model decision is inspectable."""

    issue_id: str
    question: str
    unknown_kind: UnknownKind
    decision: str
    decision_relevance: str | None
    rivals: tuple[Rival, ...]
    expected_discriminator: str | None = None
    admissible_source_scope: tuple[str, ...] = ()
    stop_condition: str | None = None

    def __post_init__(self) -> None:
        _identifier_text(self.issue_id, "issue.issue_id")
        _text(self.question, "issue.question")
        if type(self.unknown_kind) is not UnknownKind:
            raise ValueError("issue.unknown_kind must be UnknownKind")
        _text(self.decision, "issue.decision")
        _optional_text(self.decision_relevance, "issue.decision_relevance")
        _typed_tuple(self.rivals, Rival, "issue.rivals")
        _optional_text(self.expected_discriminator, "issue.expected_discriminator")
        _text_tuple(self.admissible_source_scope, "issue.admissible_source_scope")
        _optional_text(self.stop_condition, "issue.stop_condition")
        rival_ids = [rival.rival_id for rival in self.rivals]
        if len(rival_ids) != len(set(rival_ids)):
            raise ValueError("issue.rivals must have unique rival_id values")
        claims = [rival.claim for rival in self.rivals]
        if len(claims) != len(set(claims)):
            raise ValueError("issue.rivals must state distinct claims")

    @property
    def is_decision_relevant(self) -> bool:
        return self.decision_relevance is not None

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": ISSUE_SCHEMA,
            "issue_id": self.issue_id,
            "question": self.question,
            "unknown_kind": self.unknown_kind.value,
            "decision": self.decision,
            "decision_relevance": self.decision_relevance,
            "rivals": [rival.to_dict() for rival in self.rivals],
            "expected_discriminator": self.expected_discriminator,
            "admissible_source_scope": list(self.admissible_source_scope),
            "stop_condition": self.stop_condition,
        }


@dataclass(frozen=True)
class ResearchWarrant:
    """Permission to seek a discriminator, never a confirmation request."""

    warrant_id: str
    issue_id: str
    question: str
    unknown_kind: UnknownKind
    decision: str
    decision_relevance: str
    rivals: tuple[Rival, ...]
    expected_discriminator: str
    admissible_source_scope: tuple[str, ...]
    stop_condition: str
    discovery_channels: tuple[str, ...]
    proposal_status: str = "PROPOSED"
    epistemic_limit: str = NON_INDUCTIVE_LIMIT

    def __post_init__(self) -> None:
        _identifier_text(self.warrant_id, "research_warrant.warrant_id")
        _identifier_text(self.issue_id, "research_warrant.issue_id")
        _text(self.question, "research_warrant.question")
        if self.unknown_kind is not UnknownKind.EXTERNAL:
            raise ValueError("a research warrant must concern an external unknown")
        _text(self.decision, "research_warrant.decision")
        _text(self.decision_relevance, "research_warrant.decision_relevance")
        _typed_tuple(self.rivals, Rival, "research_warrant.rivals")
        _text(self.expected_discriminator, "research_warrant.expected_discriminator")
        _text_tuple(
            self.admissible_source_scope,
            "research_warrant.admissible_source_scope",
            nonempty=True,
        )
        _text(self.stop_condition, "research_warrant.stop_condition")
        if len(self.rivals) < 2:
            raise ValueError("a research warrant requires at least two rivals")
        rival_ids = [rival.rival_id for rival in self.rivals]
        if len(rival_ids) != len(set(rival_ids)):
            raise ValueError("research_warrant.rivals must have unique rival_id values")
        claims = [rival.claim for rival in self.rivals]
        if len(claims) != len(set(claims)):
            raise ValueError("research_warrant.rivals must state distinct claims")
        if any(not rival.falsifier_conditions for rival in self.rivals):
            raise ValueError("every warranted rival requires a falsifier condition")
        _text_tuple(
            self.discovery_channels,
            "research_warrant.discovery_channels",
            nonempty=True,
        )
        if self.proposal_status != "PROPOSED":
            raise PolicyViolation("a generated research warrant must remain PROPOSED")
        if self.epistemic_limit != NON_INDUCTIVE_LIMIT:
            raise PolicyViolation("research warrant weakens the non-inductive limit")

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": WARRANT_SCHEMA,
            "warrant_id": self.warrant_id,
            "issue_id": self.issue_id,
            "question": self.question,
            "unknown_kind": self.unknown_kind.value,
            "decision": self.decision,
            "decision_relevance": self.decision_relevance,
            "rivals": [rival.to_dict() for rival in self.rivals],
            "expected_discriminator": self.expected_discriminator,
            "admissible_source_scope": list(self.admissible_source_scope),
            "stop_condition": self.stop_condition,
            "discovery_channels": list(self.discovery_channels),
            "proposal_status": self.proposal_status,
            "epistemic_limit": self.epistemic_limit,
        }


@dataclass(frozen=True)
class MinimalPairChallenge:
    """A one-difference contrast with an explicit semantic oracle."""

    challenge_id: str
    defect_type: str
    intended_case: str
    lookalike_case: str
    held_fixed: str
    controlled_difference: str
    oracle: str
    falsifies_if: str
    epistemic_limit: str = NON_INDUCTIVE_LIMIT

    def __post_init__(self) -> None:
        _identifier_text(self.challenge_id, "minimal_pair.challenge_id")
        if type(self.defect_type) is DefectType:
            object.__setattr__(self, "defect_type", self.defect_type.value)
        elif type(self.defect_type) is not str or not _DEFECT_KEY.fullmatch(
            self.defect_type
        ):
            raise ValueError("minimal_pair.defect_type must be a stable snake_case key")
        _text(self.intended_case, "minimal_pair.intended_case")
        _text(self.lookalike_case, "minimal_pair.lookalike_case")
        if self.intended_case == self.lookalike_case:
            raise ValueError("minimal-pair cases must differ")
        _text(self.held_fixed, "minimal_pair.held_fixed")
        _text(self.controlled_difference, "minimal_pair.controlled_difference")
        _oracle_status(self.oracle, "minimal_pair.oracle")
        _text(self.falsifies_if, "minimal_pair.falsifies_if")
        if self.epistemic_limit != NON_INDUCTIVE_LIMIT:
            raise PolicyViolation("minimal-pair challenge weakens the non-inductive limit")

    @property
    def oracle_status(self) -> OracleStatus:
        return _oracle_status(self.oracle, "minimal_pair.oracle")

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": CHALLENGE_SCHEMA,
            "challenge_id": self.challenge_id,
            "defect_type": self.defect_type,
            "intended_case": self.intended_case,
            "lookalike_case": self.lookalike_case,
            "held_fixed": self.held_fixed,
            "controlled_difference": self.controlled_difference,
            "oracle": self.oracle,
            "falsifies_if": self.falsifies_if,
            "epistemic_limit": self.epistemic_limit,
        }


def expected_hardening_status(
    *,
    excluded_countermodels: tuple[str, ...],
    resolved_ambiguities: tuple[str, ...],
    preserved_dimensions: tuple[PreservationDimension, ...],
    new_countermodels: tuple[str, ...],
    lost_intended_cases: tuple[str, ...],
    weakened_claims: tuple[str, ...],
    collapsed_distinctions: tuple[str, ...],
    unresolved_criticisms: tuple[str, ...],
    research_warrants: tuple[ResearchWarrant, ...],
    gain_witness_refs: tuple[str, ...],
    preservation_review_refs: tuple[str, ...],
    human_decision_refs: tuple[str, ...],
    justification_bases: tuple[JustificationBasis, ...],
) -> HardeningStatus:
    """Derive the fail-closed disposition without weighing dimensions.

    The v0.1 records carry human-readable references for traceability, but no
    typed resolver yet proves that those references exist, are digest-bound to
    the assessed artifacts, or contain the claimed decisions.  Consequently,
    reference strings cannot authorize ``HARDENING_UNREFUTED``.  That status
    remains in the vocabulary for a later ledger-backed protocol.
    """

    refuted = any(
        (
            new_countermodels,
            lost_intended_cases,
            weakened_claims,
            collapsed_distinctions,
        )
    )
    if refuted:
        return HardeningStatus.NO_HARDENING
    if research_warrants:
        # A generated warrant is only a structurally eligible route proposal.
        # It cannot establish that the criticism's failure locus is external;
        # the adaptive inquiry layer requires a separate human triage before
        # it can authorize research.  Keep the assessment unresolved here.
        return HardeningStatus.UNRESOLVED
    has_gain_claim = bool(excluded_countermodels or resolved_ambiguities)
    if not has_gain_claim:
        # Preservation obligations license a claimed gain; they need not be
        # asserted merely to record that this revision claims no gain.
        return HardeningStatus.NO_HARDENING
    if unresolved_criticisms or set(preserved_dimensions) != REQUIRED_PRESERVATION_DIMENSIONS:
        return HardeningStatus.UNRESOLVED
    if has_gain_claim:
        # These fields remain recorded as unresolved evidence claims.  Their
        # non-emptiness is deliberately not an authorization mechanism.
        _ = (
            gain_witness_refs,
            preservation_review_refs,
            human_decision_refs,
            justification_bases,
        )
        return HardeningStatus.UNRESOLVED
    raise AssertionError("unreachable hardening-status branch")


@dataclass(frozen=True)
class HardeningAssessment:
    """A non-scalar comparison of one proposed revision with its baseline."""

    assessment_id: str
    baseline_id: str
    revision_id: str
    status: HardeningStatus
    excluded_countermodels: tuple[str, ...]
    resolved_ambiguities: tuple[str, ...]
    preserved_dimensions: tuple[PreservationDimension, ...]
    new_countermodels: tuple[str, ...]
    lost_intended_cases: tuple[str, ...]
    weakened_claims: tuple[str, ...]
    collapsed_distinctions: tuple[str, ...]
    unresolved_criticisms: tuple[str, ...]
    research_warrants: tuple[ResearchWarrant, ...]
    justification_bases: tuple[JustificationBasis, ...]
    gain_witness_refs: tuple[str, ...]
    preservation_review_refs: tuple[str, ...]
    human_decision_refs: tuple[str, ...]
    epistemic_limit: str = NON_INDUCTIVE_LIMIT

    def __post_init__(self) -> None:
        _identifier_text(self.assessment_id, "hardening.assessment_id")
        _identifier_text(self.baseline_id, "hardening.baseline_id")
        _identifier_text(self.revision_id, "hardening.revision_id")
        if self.baseline_id == self.revision_id:
            raise ValueError("hardening baseline and revision must differ")
        if type(self.status) is not HardeningStatus:
            raise ValueError("hardening.status must be HardeningStatus")
        for field_name in (
            "excluded_countermodels",
            "resolved_ambiguities",
            "new_countermodels",
            "lost_intended_cases",
            "weakened_claims",
            "collapsed_distinctions",
            "unresolved_criticisms",
            "gain_witness_refs",
            "preservation_review_refs",
            "human_decision_refs",
        ):
            _text_tuple(getattr(self, field_name), f"hardening.{field_name}")
        _typed_tuple(
            self.preserved_dimensions,
            PreservationDimension,
            "hardening.preserved_dimensions",
        )
        _typed_tuple(
            self.research_warrants,
            ResearchWarrant,
            "hardening.research_warrants",
        )
        warrant_ids = [warrant.warrant_id for warrant in self.research_warrants]
        if len(warrant_ids) != len(set(warrant_ids)):
            raise ValueError("hardening.research_warrants must have unique warrant IDs")
        _typed_tuple(
            self.justification_bases,
            JustificationBasis,
            "hardening.justification_bases",
        )
        prohibited = set(self.justification_bases) & PROHIBITED_JUSTIFICATION_BASES
        if prohibited:
            names = sorted(item.value for item in prohibited)
            raise PolicyViolation(
                "pass counts, consensus, and confidence cannot justify a claim; "
                f"forbidden bases={names}"
            )
        if self.epistemic_limit != NON_INDUCTIVE_LIMIT:
            raise PolicyViolation("hardening assessment weakens the non-inductive limit")
        expected = expected_hardening_status(
            excluded_countermodels=self.excluded_countermodels,
            resolved_ambiguities=self.resolved_ambiguities,
            preserved_dimensions=self.preserved_dimensions,
            new_countermodels=self.new_countermodels,
            lost_intended_cases=self.lost_intended_cases,
            weakened_claims=self.weakened_claims,
            collapsed_distinctions=self.collapsed_distinctions,
            unresolved_criticisms=self.unresolved_criticisms,
            research_warrants=self.research_warrants,
            gain_witness_refs=self.gain_witness_refs,
            preservation_review_refs=self.preservation_review_refs,
            human_decision_refs=self.human_decision_refs,
            justification_bases=self.justification_bases,
        )
        if self.status is not expected:
            raise PolicyViolation(
                f"hardening status {self.status.value} is inconsistent with evidence; "
                f"expected {expected.value}"
            )

    def __bool__(self) -> bool:
        raise TypeError("hardening has no truth coercion; inspect .status explicitly")

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": ASSESSMENT_SCHEMA,
            "assessment_id": self.assessment_id,
            "baseline_id": self.baseline_id,
            "revision_id": self.revision_id,
            "status": self.status.value,
            "excluded_countermodels": list(self.excluded_countermodels),
            "resolved_ambiguities": list(self.resolved_ambiguities),
            "preserved_dimensions": [item.value for item in self.preserved_dimensions],
            "new_countermodels": list(self.new_countermodels),
            "lost_intended_cases": list(self.lost_intended_cases),
            "weakened_claims": list(self.weakened_claims),
            "collapsed_distinctions": list(self.collapsed_distinctions),
            "unresolved_criticisms": list(self.unresolved_criticisms),
            "research_warrants": [warrant.to_dict() for warrant in self.research_warrants],
            "justification_bases": [item.value for item in self.justification_bases],
            "gain_witness_refs": list(self.gain_witness_refs),
            "preservation_review_refs": list(self.preservation_review_refs),
            "human_decision_refs": list(self.human_decision_refs),
            "epistemic_limit": self.epistemic_limit,
        }


@dataclass(frozen=True)
class FormalizationReadiness:
    """A current advisory check, never a declaration of final adequacy."""

    report_id: str
    candidate_id: str
    status: ReadinessStatus
    unresolved_semantic_roles: tuple[str, ...]
    missing_positive_witnesses: tuple[str, ...]
    missing_negative_witnesses: tuple[str, ...]
    ungrounded_primitives: tuple[str, ...]
    undecided_source_forks: tuple[str, ...]
    review_record_refs: tuple[str, ...]
    advisory: bool = True
    final: bool = False
    epistemic_limit: str = NON_INDUCTIVE_LIMIT

    def __post_init__(self) -> None:
        _identifier_text(self.report_id, "readiness.report_id")
        _identifier_text(self.candidate_id, "readiness.candidate_id")
        if type(self.status) is not ReadinessStatus:
            raise ValueError("readiness.status must be ReadinessStatus")
        blocker_fields = (
            "unresolved_semantic_roles",
            "missing_positive_witnesses",
            "missing_negative_witnesses",
            "ungrounded_primitives",
            "undecided_source_forks",
        )
        for field_name in blocker_fields:
            _text_tuple(getattr(self, field_name), f"readiness.{field_name}")
        _text_tuple(self.review_record_refs, "readiness.review_record_refs")
        if self.advisory is not True or self.final is not False:
            raise PolicyViolation("formalization readiness must remain advisory and non-final")
        # v0.1 has no typed, digest-bound resolver for review records.  Plain
        # strings are useful trace pointers but cannot clear a semantic gate.
        # PROVISIONALLY_READY remains a future protocol status and is therefore
        # fail-closed here even when no blocker string has been supplied.
        expected = ReadinessStatus.BLOCKED
        if self.status is not expected:
            raise PolicyViolation(
                f"readiness status {self.status.value} is inconsistent; expected {expected.value}"
            )
        if self.epistemic_limit != NON_INDUCTIVE_LIMIT:
            raise PolicyViolation("readiness report weakens the non-inductive limit")

    def __bool__(self) -> bool:
        raise TypeError("formalization readiness is advisory; inspect .status explicitly")

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": READINESS_SCHEMA,
            "report_id": self.report_id,
            "candidate_id": self.candidate_id,
            "status": self.status.value,
            "unresolved_semantic_roles": list(self.unresolved_semantic_roles),
            "missing_positive_witnesses": list(self.missing_positive_witnesses),
            "missing_negative_witnesses": list(self.missing_negative_witnesses),
            "ungrounded_primitives": list(self.ungrounded_primitives),
            "undecided_source_forks": list(self.undecided_source_forks),
            "review_record_refs": list(self.review_record_refs),
            "advisory": self.advisory,
            "final": self.final,
            "epistemic_limit": self.epistemic_limit,
        }


def _object(value: Any, where: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise RecordError(f"{where} must be an object")
    return value


def _exact_keys(value: dict[str, Any], expected: set[str], where: str) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise RecordError(f"{where} keys differ; missing={missing}, extra={extra}")


def _array(value: Any, where: str) -> list[Any]:
    if type(value) is not list:
        raise RecordError(f"{where} must be an array")
    return value


def _parse_enum(value: Any, enum_type: type[Enum], where: str) -> Any:
    if type(value) is not str:
        raise RecordError(f"{where} must be a string")
    try:
        return enum_type(value)
    except ValueError as exc:
        allowed = sorted(item.value for item in enum_type)
        raise RecordError(f"{where} must be one of {allowed}") from exc


def _parse_text_array(value: Any, where: str) -> tuple[str, ...]:
    items = _array(value, where)
    try:
        return _text_tuple(tuple(items), where)
    except ValueError as exc:
        raise RecordError(str(exc)) from exc


def parse_rival(value: Any, *, where: str = "rival") -> Rival:
    record = _object(value, where)
    _exact_keys(record, {"rival_id", "claim", "falsifier_conditions"}, where)
    try:
        return Rival(
            rival_id=record["rival_id"],
            claim=record["claim"],
            falsifier_conditions=_parse_text_array(
                record["falsifier_conditions"],
                f"{where}.falsifier_conditions",
            ),
        )
    except ValueError as exc:
        raise RecordError(str(exc)) from exc


def parse_issue(value: Any) -> Issue:
    record = _object(value, "issue")
    _exact_keys(
        record,
        {
            "schema_version",
            "issue_id",
            "question",
            "unknown_kind",
            "decision",
            "decision_relevance",
            "rivals",
            "expected_discriminator",
            "admissible_source_scope",
            "stop_condition",
        },
        "issue",
    )
    if record["schema_version"] != ISSUE_SCHEMA:
        raise RecordError("unknown semantic-forge issue schema version")
    rival_values = _array(record["rivals"], "issue.rivals")
    try:
        return Issue(
            issue_id=record["issue_id"],
            question=record["question"],
            unknown_kind=_parse_enum(record["unknown_kind"], UnknownKind, "issue.unknown_kind"),
            decision=record["decision"],
            decision_relevance=_optional_text(
                record["decision_relevance"],
                "issue.decision_relevance",
            ),
            rivals=tuple(
                parse_rival(item, where=f"issue.rivals[{index}]")
                for index, item in enumerate(rival_values)
            ),
            expected_discriminator=_optional_text(
                record["expected_discriminator"],
                "issue.expected_discriminator",
            ),
            admissible_source_scope=_parse_text_array(
                record["admissible_source_scope"],
                "issue.admissible_source_scope",
            ),
            stop_condition=_optional_text(
                record["stop_condition"],
                "issue.stop_condition",
            ),
        )
    except ValueError as exc:
        raise RecordError(str(exc)) from exc


def parse_research_warrant(value: Any) -> ResearchWarrant:
    record = _object(value, "research_warrant")
    _exact_keys(
        record,
        {
            "schema_version",
            "warrant_id",
            "issue_id",
            "question",
            "unknown_kind",
            "decision",
            "decision_relevance",
            "rivals",
            "expected_discriminator",
            "admissible_source_scope",
            "stop_condition",
            "discovery_channels",
            "proposal_status",
            "epistemic_limit",
        },
        "research_warrant",
    )
    if record["schema_version"] != WARRANT_SCHEMA:
        raise RecordError("unknown semantic-forge research-warrant schema version")
    rival_values = _array(record["rivals"], "research_warrant.rivals")
    try:
        return ResearchWarrant(
            warrant_id=record["warrant_id"],
            issue_id=record["issue_id"],
            question=record["question"],
            unknown_kind=_parse_enum(
                record["unknown_kind"],
                UnknownKind,
                "research_warrant.unknown_kind",
            ),
            decision=record["decision"],
            decision_relevance=record["decision_relevance"],
            rivals=tuple(
                parse_rival(item, where=f"research_warrant.rivals[{index}]")
                for index, item in enumerate(rival_values)
            ),
            expected_discriminator=record["expected_discriminator"],
            admissible_source_scope=_parse_text_array(
                record["admissible_source_scope"],
                "research_warrant.admissible_source_scope",
            ),
            stop_condition=record["stop_condition"],
            discovery_channels=_parse_text_array(
                record["discovery_channels"],
                "research_warrant.discovery_channels",
            ),
            proposal_status=record["proposal_status"],
            epistemic_limit=record["epistemic_limit"],
        )
    except ValueError as exc:
        raise RecordError(str(exc)) from exc


def parse_minimal_pair_challenge(value: Any) -> MinimalPairChallenge:
    record = _object(value, "minimal_pair")
    _exact_keys(
        record,
        {
            "schema_version",
            "challenge_id",
            "defect_type",
            "intended_case",
            "lookalike_case",
            "held_fixed",
            "controlled_difference",
            "oracle",
            "falsifies_if",
            "epistemic_limit",
        },
        "minimal_pair",
    )
    if record["schema_version"] != CHALLENGE_SCHEMA:
        raise RecordError("unknown semantic-forge minimal-pair schema version")
    try:
        return MinimalPairChallenge(
            challenge_id=record["challenge_id"],
            defect_type=record["defect_type"],
            intended_case=record["intended_case"],
            lookalike_case=record["lookalike_case"],
            held_fixed=record["held_fixed"],
            controlled_difference=record["controlled_difference"],
            oracle=record["oracle"],
            falsifies_if=record["falsifies_if"],
            epistemic_limit=record["epistemic_limit"],
        )
    except ValueError as exc:
        raise RecordError(str(exc)) from exc


def parse_hardening_assessment(value: Any) -> HardeningAssessment:
    record = _object(value, "hardening")
    _exact_keys(
        record,
        {
            "schema_version",
            "assessment_id",
            "baseline_id",
            "revision_id",
            "status",
            "excluded_countermodels",
            "resolved_ambiguities",
            "preserved_dimensions",
            "new_countermodels",
            "lost_intended_cases",
            "weakened_claims",
            "collapsed_distinctions",
            "unresolved_criticisms",
            "research_warrants",
            "justification_bases",
            "gain_witness_refs",
            "preservation_review_refs",
            "human_decision_refs",
            "epistemic_limit",
        },
        "hardening",
    )
    if record["schema_version"] != ASSESSMENT_SCHEMA:
        raise RecordError("unknown semantic-forge hardening-assessment schema version")
    preservation_values = _array(record["preserved_dimensions"], "hardening.preserved_dimensions")
    warrant_values = _array(record["research_warrants"], "hardening.research_warrants")
    basis_values = _array(record["justification_bases"], "hardening.justification_bases")
    try:
        return HardeningAssessment(
            assessment_id=record["assessment_id"],
            baseline_id=record["baseline_id"],
            revision_id=record["revision_id"],
            status=_parse_enum(record["status"], HardeningStatus, "hardening.status"),
            excluded_countermodels=_parse_text_array(
                record["excluded_countermodels"],
                "hardening.excluded_countermodels",
            ),
            resolved_ambiguities=_parse_text_array(
                record["resolved_ambiguities"],
                "hardening.resolved_ambiguities",
            ),
            preserved_dimensions=tuple(
                _parse_enum(
                    item,
                    PreservationDimension,
                    f"hardening.preserved_dimensions[{index}]",
                )
                for index, item in enumerate(preservation_values)
            ),
            new_countermodels=_parse_text_array(
                record["new_countermodels"],
                "hardening.new_countermodels",
            ),
            lost_intended_cases=_parse_text_array(
                record["lost_intended_cases"],
                "hardening.lost_intended_cases",
            ),
            weakened_claims=_parse_text_array(
                record["weakened_claims"],
                "hardening.weakened_claims",
            ),
            collapsed_distinctions=_parse_text_array(
                record["collapsed_distinctions"],
                "hardening.collapsed_distinctions",
            ),
            unresolved_criticisms=_parse_text_array(
                record["unresolved_criticisms"],
                "hardening.unresolved_criticisms",
            ),
            research_warrants=tuple(
                parse_research_warrant(item) for item in warrant_values
            ),
            justification_bases=tuple(
                _parse_enum(
                    item,
                    JustificationBasis,
                    f"hardening.justification_bases[{index}]",
                )
                for index, item in enumerate(basis_values)
            ),
            gain_witness_refs=_parse_text_array(
                record["gain_witness_refs"],
                "hardening.gain_witness_refs",
            ),
            preservation_review_refs=_parse_text_array(
                record["preservation_review_refs"],
                "hardening.preservation_review_refs",
            ),
            human_decision_refs=_parse_text_array(
                record["human_decision_refs"],
                "hardening.human_decision_refs",
            ),
            epistemic_limit=record["epistemic_limit"],
        )
    except ValueError as exc:
        raise RecordError(str(exc)) from exc


def parse_formalization_readiness(value: Any) -> FormalizationReadiness:
    record = _object(value, "readiness")
    _exact_keys(
        record,
        {
            "schema_version",
            "report_id",
            "candidate_id",
            "status",
            "unresolved_semantic_roles",
            "missing_positive_witnesses",
            "missing_negative_witnesses",
            "ungrounded_primitives",
            "undecided_source_forks",
            "review_record_refs",
            "advisory",
            "final",
            "epistemic_limit",
        },
        "readiness",
    )
    if record["schema_version"] != READINESS_SCHEMA:
        raise RecordError("unknown semantic-forge formalization-readiness schema version")
    if type(record["advisory"]) is not bool or type(record["final"]) is not bool:
        raise RecordError("readiness advisory and final fields must be Booleans")
    try:
        return FormalizationReadiness(
            report_id=record["report_id"],
            candidate_id=record["candidate_id"],
            status=_parse_enum(record["status"], ReadinessStatus, "readiness.status"),
            unresolved_semantic_roles=_parse_text_array(
                record["unresolved_semantic_roles"],
                "readiness.unresolved_semantic_roles",
            ),
            missing_positive_witnesses=_parse_text_array(
                record["missing_positive_witnesses"],
                "readiness.missing_positive_witnesses",
            ),
            missing_negative_witnesses=_parse_text_array(
                record["missing_negative_witnesses"],
                "readiness.missing_negative_witnesses",
            ),
            ungrounded_primitives=_parse_text_array(
                record["ungrounded_primitives"],
                "readiness.ungrounded_primitives",
            ),
            undecided_source_forks=_parse_text_array(
                record["undecided_source_forks"],
                "readiness.undecided_source_forks",
            ),
            review_record_refs=_parse_text_array(
                record["review_record_refs"],
                "readiness.review_record_refs",
            ),
            advisory=record["advisory"],
            final=record["final"],
            epistemic_limit=record["epistemic_limit"],
        )
    except ValueError as exc:
        raise RecordError(str(exc)) from exc
