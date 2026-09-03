"""Strict external-research records for the semantic-model forge.

The ledger preserves bounded project reports about external sources.  It does
not import those reports into CR-1.0, adjudicate target semantics, or turn
provider output, repetition, agreement, or test survival into confirmation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
import hashlib
import json
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlsplit

from creib.canonical import domain_digest
from creib.errors import PolicyViolation, RecordError
from creib.strict_json import load_strict, loads_strict


LEDGER_SCHEMA_VERSION = "creib.semantic-forge.external-research-ledger.v2"
LEDGER_SCHEMA_REF = "../schema/research-ledger.schema.json"
TARGET_DOCUMENT_ID = "CR-1.0"
TARGET_SHA256 = "08ff81e848fea976b558345402d85723173be8f40f1041fb00d6267f1e026b8b"
EXTERNAL_REPORT_KIND = "external_source_report"
SOURCE_REPORT_SCOPE = "source_claims_only"
PROJECT_REPORT_AUTHOR = "SMF_PROJECT"
RESEARCH_ROLE = "generate_and_sharpen_criticism_not_confirm_the_model"
EPISTEMIC_EFFECT = "may_criticize_or_guide_engineering_only"
PROJECT_USE_EFFECT = "may_guide_harness_engineering_only"
PRIMARY_PRESERVATION_STATUS = "versioned_locator_and_bounded_report_only"

_LEDGER_ID = re.compile(r"^SMF-RESEARCH-[A-Z0-9][A-Z0-9-]*$")
_ENTRY_ID = re.compile(r"^SMF-RES-[A-Z0-9][A-Z0-9-]*$")
_PROPOSAL_ID = re.compile(r"^SMF-PROP-[A-Z0-9][A-Z0-9-]*$")
_DECISION_ID = re.compile(r"^SMF-DEC-[A-Z0-9][A-Z0-9-]*$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_DOI_ID = re.compile(r"^doi:(10\.[0-9]{4,9}/\S+)$")
_ARXIV_ID = re.compile(r"^arXiv:([0-9]{2}(?:0[1-9]|1[0-2])\.[0-9]{5})$")


class SourceKind(str, Enum):
    DOI = "doi"
    ARXIV = "arxiv"


class DiscoveryRouteKind(str, Enum):
    DEFAULT_CONTEMPORARY = "default_contemporary_discovery"
    DIRECT_PRIMARY_SOURCE = "direct_primary_source"


class ProposalStatus(str, Enum):
    PROPOSED = "PROPOSED"


class DecisionDisposition(str, Enum):
    ADOPT = "ADOPT"
    REJECT = "REJECT"
    DEFER = "DEFER"


class HumanAdjudicationStatus(str, Enum):
    UNREVIEWED = "UNREVIEWED"


def report_sha256(report: str) -> str:
    """Hash the exact UTF-8 report text without normalization."""

    _text(report, "bounded_source_report")
    return hashlib.sha256(report.encode("utf-8")).hexdigest()


def _record_sha256(domain: str, value: dict[str, object]) -> str:
    """Digest a complete unsigned record under a type-specific domain."""

    return domain_digest(domain, value).removeprefix("sha256:")


def _text(value: Any, where: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{where} must be a non-empty string")
    if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
        raise ValueError(f"{where} contains a Unicode surrogate")
    return value


def _identifier(value: Any, where: str, pattern: re.Pattern[str]) -> str:
    text = _text(value, where)
    if not pattern.fullmatch(text):
        raise ValueError(f"{where} is not a valid stable identifier")
    return text


def _iso_date(value: Any, where: str) -> str:
    text = _text(value, where)
    try:
        parsed = date.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{where} must be an ISO 8601 calendar date") from exc
    if parsed.isoformat() != text:
        raise ValueError(f"{where} must be a normalized ISO 8601 calendar date")
    return text


def _https_url(value: Any, where: str) -> str:
    text = _text(value, where)
    if not text.startswith("https://"):
        raise ValueError(f"{where} must start with lowercase https://")
    parsed = urlsplit(text)
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
    ):
        raise ValueError(f"{where} must be an HTTPS URL without credentials or fragment")
    return text


def _is_schema_valid_alphaxiv_locator(value: str) -> bool:
    return value.startswith(("https://alphaxiv.org/", "https://www.alphaxiv.org/"))


def _text_tuple(value: Any, where: str, *, nonempty: bool = False) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{where} must be a tuple")
    if nonempty and not value:
        raise ValueError(f"{where} must not be empty")
    checked = tuple(_text(item, f"{where}[{index}]") for index, item in enumerate(value))
    if len(checked) != len(set(checked)):
        raise ValueError(f"{where} must not contain duplicates")
    return checked


@dataclass(frozen=True, slots=True)
class AuthorityBoundary:
    target_document_id: str
    target_sha256: str
    external_research_semantic_authority: bool
    external_reports_are_target_semantics: bool

    def __post_init__(self) -> None:
        if self.target_document_id != TARGET_DOCUMENT_ID:
            raise PolicyViolation("the research ledger must remain bound to CR-1.0")
        if self.target_sha256 != TARGET_SHA256:
            raise PolicyViolation("the research ledger target authority digest changed")
        if self.external_research_semantic_authority is not False:
            raise PolicyViolation("external research cannot be semantic authority")
        if self.external_reports_are_target_semantics is not False:
            raise PolicyViolation("external source reports cannot become target semantics")

    def to_dict(self) -> dict[str, object]:
        return {
            "target_document_id": self.target_document_id,
            "target_sha256": self.target_sha256,
            "external_research_semantic_authority": self.external_research_semantic_authority,
            "external_reports_are_target_semantics": self.external_reports_are_target_semantics,
        }


@dataclass(frozen=True, slots=True)
class ProviderPolicy:
    default_contemporary_discovery_provider: str
    contemporary_from_year: int
    consensus_role: str
    providers_replaceable: bool
    direct_primary_source_required: bool
    provider_output_is_oracle: bool

    def __post_init__(self) -> None:
        _text(
            self.default_contemporary_discovery_provider,
            "provider_policy.default_contemporary_discovery_provider",
        )
        if (
            type(self.contemporary_from_year) is not int
            or not 1900 <= self.contemporary_from_year <= 9999
        ):
            raise ValueError(
                "provider_policy.contemporary_from_year must be a four-digit integer"
            )
        if self.consensus_role != "optional_independent_cross_check":
            raise PolicyViolation("Consensus must remain an optional independent cross-check")
        if self.providers_replaceable is not True:
            raise PolicyViolation("research providers must remain replaceable")
        if self.direct_primary_source_required is not True:
            raise PolicyViolation("retained reports require direct primary-source inspection")
        if self.provider_output_is_oracle is not False:
            raise PolicyViolation("provider output cannot be an oracle")

    def to_dict(self) -> dict[str, object]:
        return {
            "default_contemporary_discovery_provider": self.default_contemporary_discovery_provider,
            "contemporary_from_year": self.contemporary_from_year,
            "consensus_role": self.consensus_role,
            "providers_replaceable": self.providers_replaceable,
            "direct_primary_source_required": self.direct_primary_source_required,
            "provider_output_is_oracle": self.provider_output_is_oracle,
        }


@dataclass(frozen=True, slots=True)
class EpistemicPolicy:
    claim_kind: str
    research_role: str
    passing_reports_confirm_model: bool
    frequency_or_citation_count_can_promote: bool
    provider_agreement_can_promote: bool
    inductive_promotion_permitted: bool
    research_can_close_semantic_question: bool

    def __post_init__(self) -> None:
        if self.claim_kind != EXTERNAL_REPORT_KIND:
            raise PolicyViolation("research records must remain external source reports")
        if self.research_role != RESEARCH_ROLE:
            raise PolicyViolation("research must remain criticism-oriented")
        forbidden = {
            "passing_reports_confirm_model": self.passing_reports_confirm_model,
            "frequency_or_citation_count_can_promote": self.frequency_or_citation_count_can_promote,
            "provider_agreement_can_promote": self.provider_agreement_can_promote,
            "inductive_promotion_permitted": self.inductive_promotion_permitted,
            "research_can_close_semantic_question": self.research_can_close_semantic_question,
        }
        promoted = sorted(name for name, value in forbidden.items() if value is not False)
        if promoted:
            raise PolicyViolation(f"inductive promotion is forbidden: {promoted}")

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_kind": self.claim_kind,
            "research_role": self.research_role,
            "passing_reports_confirm_model": self.passing_reports_confirm_model,
            "frequency_or_citation_count_can_promote": self.frequency_or_citation_count_can_promote,
            "provider_agreement_can_promote": self.provider_agreement_can_promote,
            "inductive_promotion_permitted": self.inductive_promotion_permitted,
            "research_can_close_semantic_question": self.research_can_close_semantic_question,
        }


@dataclass(frozen=True, slots=True)
class CanonicalSource:
    source_kind: SourceKind
    canonical_identifier: str
    canonical_url: str
    version: str
    versioned_url: str
    publication_year: int
    as_of_date: str
    retrieved_on: str

    def __post_init__(self) -> None:
        if type(self.source_kind) is not SourceKind:
            raise ValueError("canonical_source.source_kind must be SourceKind")
        canonical_identifier = _text(
            self.canonical_identifier,
            "canonical_source.canonical_identifier",
        )
        version = _text(self.version, "canonical_source.version")
        if type(self.publication_year) is not int or not 1900 <= self.publication_year <= 9999:
            raise ValueError("canonical_source.publication_year must be a four-digit integer")
        _iso_date(self.as_of_date, "canonical_source.as_of_date")
        _iso_date(self.retrieved_on, "canonical_source.retrieved_on")
        if self.publication_year > date.fromisoformat(self.as_of_date).year:
            raise ValueError("canonical_source.publication_year cannot be after as_of_date")
        if self.retrieved_on > self.as_of_date:
            raise ValueError("canonical_source.retrieved_on cannot be after as_of_date")
        if date.fromisoformat(self.retrieved_on).year < self.publication_year:
            raise ValueError("canonical_source.retrieved_on cannot predate publication_year")
        canonical_url = _https_url(self.canonical_url, "canonical_source.canonical_url")
        versioned_url = _https_url(self.versioned_url, "canonical_source.versioned_url")
        if self.source_kind is SourceKind.DOI:
            match = _DOI_ID.fullmatch(canonical_identifier)
            if match is None:
                raise ValueError("DOI source must use a canonical doi: identifier")
            if canonical_url != f"https://doi.org/{match.group(1)}":
                raise ValueError("DOI identifier and canonical URL disagree")
            if versioned_url != canonical_url:
                raise ValueError("DOI versioned URL must equal its canonical URL")
        else:
            match = _ARXIV_ID.fullmatch(canonical_identifier)
            if match is None:
                raise ValueError("arXiv source must use a canonical arXiv: identifier")
            if canonical_url != f"https://arxiv.org/abs/{match.group(1)}":
                raise ValueError("arXiv identifier and canonical URL disagree")
            if not re.fullmatch(r"v[1-9][0-9]*", version):
                raise ValueError("arXiv source version must be an explicit vN")
            if versioned_url != f"https://arxiv.org/abs/{match.group(1)}{version}":
                raise ValueError("arXiv version and versioned URL disagree")
            identifier_year = 2000 + int(match.group(1)[:2])
            if self.publication_year != identifier_year:
                raise ValueError("arXiv identifier and publication year disagree")

    def to_dict(self) -> dict[str, object]:
        return {
            "source_kind": self.source_kind.value,
            "canonical_identifier": self.canonical_identifier,
            "canonical_url": self.canonical_url,
            "version": self.version,
            "versioned_url": self.versioned_url,
            "publication_year": self.publication_year,
            "as_of_date": self.as_of_date,
            "retrieved_on": self.retrieved_on,
        }


@dataclass(frozen=True, slots=True)
class PrimaryInspection:
    locator: str
    version: str
    retrieved_on: str
    inspected_scope: str
    primary_source_inspected: bool
    preservation_status: str
    source_artifact_sha256: None

    def __post_init__(self) -> None:
        _https_url(self.locator, "primary_inspection.locator")
        _text(self.version, "primary_inspection.version")
        _iso_date(self.retrieved_on, "primary_inspection.retrieved_on")
        _text(self.inspected_scope, "primary_inspection.inspected_scope")
        if self.primary_source_inspected is not True:
            raise PolicyViolation("a retained report requires primary-source inspection")
        if self.preservation_status != PRIMARY_PRESERVATION_STATUS:
            raise PolicyViolation(
                "primary inspection must state its locator-only preservation limit"
            )
        if self.source_artifact_sha256 is not None:
            raise PolicyViolation(
                "v2 cannot claim an archived source digest without a stored artifact"
            )

    def to_dict(self) -> dict[str, object]:
        return {
            "locator": self.locator,
            "version": self.version,
            "retrieved_on": self.retrieved_on,
            "inspected_scope": self.inspected_scope,
            "primary_source_inspected": self.primary_source_inspected,
            "preservation_status": self.preservation_status,
            "source_artifact_sha256": self.source_artifact_sha256,
        }


@dataclass(frozen=True, slots=True)
class DiscoveryRecord:
    provider: str
    route_kind: DiscoveryRouteKind
    query: str
    route_locator: str
    discovered_on: str
    contemporary: bool
    provider_output_is_oracle: bool

    def __post_init__(self) -> None:
        _text(self.provider, "discovery.provider")
        if type(self.route_kind) is not DiscoveryRouteKind:
            raise ValueError("discovery.route_kind must be DiscoveryRouteKind")
        _text(self.query, "discovery.query")
        _https_url(self.route_locator, "discovery.route_locator")
        _iso_date(self.discovered_on, "discovery.discovered_on")
        if type(self.contemporary) is not bool:
            raise ValueError("discovery.contemporary must be a Boolean")
        if self.provider_output_is_oracle is not False:
            raise PolicyViolation("discovery-provider output cannot be an oracle")

    def to_dict(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "route_kind": self.route_kind.value,
            "query": self.query,
            "route_locator": self.route_locator,
            "discovered_on": self.discovered_on,
            "contemporary": self.contemporary,
            "provider_output_is_oracle": self.provider_output_is_oracle,
        }


@dataclass(frozen=True, slots=True)
class ResearchEntry:
    entry_id: str
    title: str
    canonical_source: CanonicalSource
    primary_inspection: PrimaryInspection
    discovery: DiscoveryRecord
    attacked_harness_question: str
    falsifier: str
    claim_kind: str
    report_scope: str
    report_author: str
    bounded_source_report: str
    report_sha256: str
    entry_sha256: str
    limitations: tuple[str, ...]
    epistemic_effect: str
    semantic_authority: bool
    provider_output_is_oracle: bool
    can_confirm_target_semantics: bool
    human_adjudication_status: HumanAdjudicationStatus

    def __post_init__(self) -> None:
        _identifier(self.entry_id, "entry.entry_id", _ENTRY_ID)
        _text(self.title, "entry.title")
        if type(self.canonical_source) is not CanonicalSource:
            raise ValueError("entry.canonical_source must be CanonicalSource")
        if type(self.primary_inspection) is not PrimaryInspection:
            raise ValueError("entry.primary_inspection must be PrimaryInspection")
        if type(self.discovery) is not DiscoveryRecord:
            raise ValueError("entry.discovery must be DiscoveryRecord")
        if self.primary_inspection.locator != self.canonical_source.versioned_url:
            raise ValueError("primary inspection must resolve the exact source version")
        if self.primary_inspection.version != self.canonical_source.version:
            raise ValueError("primary inspection and source version disagree")
        if self.primary_inspection.retrieved_on != self.canonical_source.retrieved_on:
            raise ValueError("primary inspection and source retrieval date disagree")
        if self.discovery.discovered_on > self.canonical_source.retrieved_on:
            raise ValueError("source inspection cannot precede its discovery record")
        if (
            date.fromisoformat(self.discovery.discovered_on).year
            < self.canonical_source.publication_year
        ):
            raise ValueError("discovery.discovered_on cannot predate publication_year")
        if self.discovery.route_kind is DiscoveryRouteKind.DIRECT_PRIMARY_SOURCE and (
            self.discovery.route_locator != self.canonical_source.canonical_url
        ):
            raise ValueError("direct discovery must resolve the canonical source URL")
        _text(self.attacked_harness_question, "entry.attacked_harness_question")
        _text(self.falsifier, "entry.falsifier")
        if self.claim_kind != EXTERNAL_REPORT_KIND:
            raise PolicyViolation("entry claim kind must remain external_source_report")
        if self.report_scope != SOURCE_REPORT_SCOPE:
            raise PolicyViolation("bounded source reports must contain source claims only")
        if self.report_author != PROJECT_REPORT_AUTHOR:
            raise PolicyViolation("bounded source reports must be project-authored")
        _text(self.bounded_source_report, "entry.bounded_source_report")
        report_digest = _text(self.report_sha256, "entry.report_sha256")
        if not _SHA256.fullmatch(report_digest):
            raise ValueError("entry.report_sha256 must be a lowercase SHA-256 digest")
        expected = report_sha256(self.bounded_source_report)
        if self.report_sha256 != expected:
            raise ValueError(
                f"entry.report_sha256 mismatch for {self.entry_id}; expected {expected}"
            )
        entry_digest = _text(self.entry_sha256, "entry.entry_sha256")
        if not _SHA256.fullmatch(entry_digest):
            raise ValueError("entry.entry_sha256 must be a lowercase SHA-256 digest")
        _text_tuple(self.limitations, "entry.limitations", nonempty=True)
        if self.epistemic_effect != EPISTEMIC_EFFECT:
            raise PolicyViolation("external research cannot acquire a promotive epistemic effect")
        if self.semantic_authority is not False:
            raise PolicyViolation("external research entry cannot be semantic authority")
        if self.provider_output_is_oracle is not False:
            raise PolicyViolation("provider output cannot be an entry oracle")
        if self.can_confirm_target_semantics is not False:
            raise PolicyViolation("external research cannot confirm target semantics")
        if self.human_adjudication_status is not HumanAdjudicationStatus.UNREVIEWED:
            raise PolicyViolation("seed research entries must remain UNREVIEWED")
        expected_entry_digest = _record_sha256(
            "creib.semantic-forge.external-source-entry.v2",
            self._unsigned_dict(),
        )
        if self.entry_sha256 != expected_entry_digest:
            raise ValueError(
                f"entry.entry_sha256 mismatch for {self.entry_id}; "
                f"expected {expected_entry_digest}"
            )

    def _unsigned_dict(self) -> dict[str, object]:
        return {
            "entry_id": self.entry_id,
            "title": self.title,
            "canonical_source": self.canonical_source.to_dict(),
            "primary_inspection": self.primary_inspection.to_dict(),
            "discovery": self.discovery.to_dict(),
            "attacked_harness_question": self.attacked_harness_question,
            "falsifier": self.falsifier,
            "claim_kind": self.claim_kind,
            "report_scope": self.report_scope,
            "report_author": self.report_author,
            "bounded_source_report": self.bounded_source_report,
            "report_sha256": self.report_sha256,
            "limitations": list(self.limitations),
            "epistemic_effect": self.epistemic_effect,
            "semantic_authority": self.semantic_authority,
            "provider_output_is_oracle": self.provider_output_is_oracle,
            "can_confirm_target_semantics": self.can_confirm_target_semantics,
            "human_adjudication_status": self.human_adjudication_status.value,
        }

    def to_dict(self) -> dict[str, object]:
        record = self._unsigned_dict()
        record["entry_sha256"] = self.entry_sha256
        return record


@dataclass(frozen=True, slots=True)
class ProjectUseProposal:
    proposal_id: str
    source_entry_id: str
    source_entry_sha256: str
    proposed_use: str
    rationale: str
    proposal_status: ProposalStatus
    epistemic_effect: str
    semantic_authority: bool
    can_promote_hardening: bool
    proposal_sha256: str

    def __post_init__(self) -> None:
        _identifier(self.proposal_id, "project_use_proposal.proposal_id", _PROPOSAL_ID)
        _identifier(self.source_entry_id, "project_use_proposal.source_entry_id", _ENTRY_ID)
        if not _SHA256.fullmatch(
            _text(self.source_entry_sha256, "project_use_proposal.source_entry_sha256")
        ):
            raise ValueError("project_use_proposal.source_entry_sha256 must be SHA-256")
        _text(self.proposed_use, "project_use_proposal.proposed_use")
        _text(self.rationale, "project_use_proposal.rationale")
        if self.proposal_status is not ProposalStatus.PROPOSED:
            raise PolicyViolation("a source-linked project use must begin as PROPOSED")
        if self.epistemic_effect != PROJECT_USE_EFFECT:
            raise PolicyViolation("a project-use proposal cannot acquire semantic force")
        if self.semantic_authority is not False or self.can_promote_hardening is not False:
            raise PolicyViolation(
                "a project-use proposal cannot be semantic authority or promote hardening"
            )
        if not _SHA256.fullmatch(
            _text(self.proposal_sha256, "project_use_proposal.proposal_sha256")
        ):
            raise ValueError("project_use_proposal.proposal_sha256 must be SHA-256")
        expected = _record_sha256(
            "creib.semantic-forge.project-use-proposal.v1",
            self._unsigned_dict(),
        )
        if self.proposal_sha256 != expected:
            raise ValueError(
                f"project_use_proposal.proposal_sha256 mismatch for {self.proposal_id}; "
                f"expected {expected}"
            )

    def _unsigned_dict(self) -> dict[str, object]:
        return {
            "schema_version": "creib.semantic-forge.project-use-proposal.v1",
            "proposal_id": self.proposal_id,
            "source_entry_id": self.source_entry_id,
            "source_entry_sha256": self.source_entry_sha256,
            "proposed_use": self.proposed_use,
            "rationale": self.rationale,
            "proposal_status": self.proposal_status.value,
            "epistemic_effect": self.epistemic_effect,
            "semantic_authority": self.semantic_authority,
            "can_promote_hardening": self.can_promote_hardening,
        }

    def to_dict(self) -> dict[str, object]:
        record = self._unsigned_dict()
        record["proposal_sha256"] = self.proposal_sha256
        return record


@dataclass(frozen=True, slots=True)
class EngineeringDecision:
    decision_id: str
    proposal_id: str
    proposal_sha256: str
    disposition: DecisionDisposition
    rationale: str
    decided_on: str
    decision_maker_role: str
    decision_scope: str
    semantic_authority: bool
    can_promote_hardening: bool

    def __post_init__(self) -> None:
        _identifier(self.decision_id, "engineering_decision.decision_id", _DECISION_ID)
        _identifier(self.proposal_id, "engineering_decision.proposal_id", _PROPOSAL_ID)
        if not _SHA256.fullmatch(
            _text(self.proposal_sha256, "engineering_decision.proposal_sha256")
        ):
            raise ValueError("engineering_decision.proposal_sha256 must be SHA-256")
        if type(self.disposition) is not DecisionDisposition:
            raise ValueError("engineering_decision.disposition must be DecisionDisposition")
        _text(self.rationale, "engineering_decision.rationale")
        _iso_date(self.decided_on, "engineering_decision.decided_on")
        if self.decision_maker_role != "HUMAN_REVIEWER":
            raise PolicyViolation("engineering decisions require a human reviewer")
        if self.decision_scope != "HARNESS_ENGINEERING_ONLY":
            raise PolicyViolation("engineering decisions cannot exceed harness engineering")
        if self.semantic_authority is not False or self.can_promote_hardening is not False:
            raise PolicyViolation(
                "an engineering decision cannot be semantic authority or promote hardening"
            )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": "creib.semantic-forge.engineering-decision.v1",
            "decision_id": self.decision_id,
            "proposal_id": self.proposal_id,
            "proposal_sha256": self.proposal_sha256,
            "disposition": self.disposition.value,
            "rationale": self.rationale,
            "decided_on": self.decided_on,
            "decision_maker_role": self.decision_maker_role,
            "decision_scope": self.decision_scope,
            "semantic_authority": self.semantic_authority,
            "can_promote_hardening": self.can_promote_hardening,
        }


@dataclass(frozen=True, slots=True)
class ResearchLedger:
    schema_ref: str
    schema_version: str
    ledger_id: str
    title: str
    created_on: str
    as_of_date: str
    authority_boundary: AuthorityBoundary
    provider_policy: ProviderPolicy
    epistemic_policy: EpistemicPolicy
    entries: tuple[ResearchEntry, ...]
    project_use_proposals: tuple[ProjectUseProposal, ...]
    engineering_decisions: tuple[EngineeringDecision, ...]
    previous_ledger_sha256: str | None
    ledger_sha256: str

    def __post_init__(self) -> None:
        if self.schema_ref != LEDGER_SCHEMA_REF:
            raise ValueError("research ledger has an unexpected schema reference")
        if self.schema_version != LEDGER_SCHEMA_VERSION:
            raise ValueError("unknown external-research ledger schema version")
        _identifier(self.ledger_id, "ledger.ledger_id", _LEDGER_ID)
        _text(self.title, "ledger.title")
        _iso_date(self.created_on, "ledger.created_on")
        _iso_date(self.as_of_date, "ledger.as_of_date")
        if self.created_on < self.as_of_date:
            raise ValueError("ledger.created_on cannot precede as_of_date")
        if type(self.authority_boundary) is not AuthorityBoundary:
            raise ValueError("ledger.authority_boundary must be AuthorityBoundary")
        if type(self.provider_policy) is not ProviderPolicy:
            raise ValueError("ledger.provider_policy must be ProviderPolicy")
        if type(self.epistemic_policy) is not EpistemicPolicy:
            raise ValueError("ledger.epistemic_policy must be EpistemicPolicy")
        if type(self.entries) is not tuple or not self.entries:
            raise ValueError("ledger.entries must be a non-empty tuple")
        for index, entry in enumerate(self.entries):
            if type(entry) is not ResearchEntry:
                raise ValueError(f"ledger.entries[{index}] must be ResearchEntry")
            if entry.canonical_source.as_of_date != self.as_of_date:
                raise ValueError("every source as_of_date must match the ledger as_of_date")
            if entry.canonical_source.retrieved_on > self.created_on:
                raise ValueError("source retrieval cannot be after ledger creation")
            contemporary = (
                entry.canonical_source.publication_year
                >= self.provider_policy.contemporary_from_year
            )
            if entry.discovery.contemporary is not contemporary:
                raise PolicyViolation(
                    f"entry {entry.entry_id} has an inconsistent contemporary marker"
                )
            if (
                entry.discovery.route_kind is DiscoveryRouteKind.DEFAULT_CONTEMPORARY
                and entry.discovery.provider
                != self.provider_policy.default_contemporary_discovery_provider
            ):
                raise PolicyViolation(
                    f"entry {entry.entry_id} default route must use the configured provider"
                )
            if (
                entry.discovery.route_kind is DiscoveryRouteKind.DEFAULT_CONTEMPORARY
                and not contemporary
            ):
                raise PolicyViolation(
                    f"entry {entry.entry_id} default contemporary route requires "
                    "a contemporary source"
                )
            if (
                entry.discovery.provider == "AlphaXiv"
                and not _is_schema_valid_alphaxiv_locator(
                    entry.discovery.route_locator
                )
            ):
                raise PolicyViolation(
                    f"entry {entry.entry_id} AlphaXiv route has a non-AlphaXiv locator"
                )
        entry_ids = tuple(entry.entry_id for entry in self.entries)
        source_ids = tuple(
            entry.canonical_source.canonical_identifier.casefold()
            if entry.canonical_source.source_kind is SourceKind.DOI
            else entry.canonical_source.canonical_identifier
            for entry in self.entries
        )
        if len(entry_ids) != len(set(entry_ids)):
            raise ValueError("research ledger entry IDs must be unique")
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("research ledger canonical source identifiers must be unique")
        if type(self.project_use_proposals) is not tuple or not self.project_use_proposals:
            raise ValueError("ledger.project_use_proposals must be a non-empty tuple")
        if type(self.engineering_decisions) is not tuple:
            raise ValueError("ledger.engineering_decisions must be a tuple")
        if self.engineering_decisions:
            raise PolicyViolation(
                "research-ledger v2 cannot authenticate human engineering decisions; "
                "the collection must remain empty"
            )
        entry_by_id = {entry.entry_id: entry for entry in self.entries}
        proposal_by_id: dict[str, ProjectUseProposal] = {}
        for index, proposal in enumerate(self.project_use_proposals):
            if type(proposal) is not ProjectUseProposal:
                raise ValueError(
                    f"ledger.project_use_proposals[{index}] must be ProjectUseProposal"
                )
            if proposal.proposal_id in proposal_by_id:
                raise ValueError("project-use proposal IDs must be unique")
            try:
                entry = entry_by_id[proposal.source_entry_id]
            except KeyError as exc:
                raise ValueError(
                    f"proposal {proposal.proposal_id} references an unknown source entry"
                ) from exc
            if proposal.source_entry_sha256 != entry.entry_sha256:
                raise ValueError(
                    f"proposal {proposal.proposal_id} source-entry digest mismatch"
                )
            proposal_by_id[proposal.proposal_id] = proposal
        decisions_by_proposal: set[str] = set()
        decision_ids: set[str] = set()
        for index, decision in enumerate(self.engineering_decisions):
            if type(decision) is not EngineeringDecision:
                raise ValueError(
                    f"ledger.engineering_decisions[{index}] must be EngineeringDecision"
                )
            if decision.decision_id in decision_ids:
                raise ValueError("engineering decision IDs must be unique")
            if decision.proposal_id in decisions_by_proposal:
                raise ValueError("each project-use proposal may have at most one decision")
            try:
                proposal = proposal_by_id[decision.proposal_id]
            except KeyError as exc:
                raise ValueError(
                    f"decision {decision.decision_id} references an unknown proposal"
                ) from exc
            if decision.proposal_sha256 != proposal.proposal_sha256:
                raise ValueError(
                    f"decision {decision.decision_id} proposal digest mismatch"
                )
            if decision.decided_on > self.as_of_date:
                raise ValueError("engineering decision cannot be after ledger as_of_date")
            decision_ids.add(decision.decision_id)
            decisions_by_proposal.add(decision.proposal_id)
        if self.previous_ledger_sha256 is not None:
            if type(self.previous_ledger_sha256) is not str or not _SHA256.fullmatch(
                self.previous_ledger_sha256
            ):
                raise ValueError("ledger.previous_ledger_sha256 must be null or SHA-256")
        if not _SHA256.fullmatch(_text(self.ledger_sha256, "ledger.ledger_sha256")):
            raise ValueError("ledger.ledger_sha256 must be a lowercase SHA-256 digest")
        expected_ledger_digest = _record_sha256(
            "creib.semantic-forge.external-research-ledger.v2",
            self._unsigned_dict(),
        )
        if self.ledger_sha256 != expected_ledger_digest:
            raise ValueError(
                f"ledger.ledger_sha256 mismatch; expected {expected_ledger_digest}"
            )

    def _unsigned_dict(self) -> dict[str, object]:
        return {
            "$schema": self.schema_ref,
            "schema_version": self.schema_version,
            "ledger_id": self.ledger_id,
            "title": self.title,
            "created_on": self.created_on,
            "as_of_date": self.as_of_date,
            "authority_boundary": self.authority_boundary.to_dict(),
            "provider_policy": self.provider_policy.to_dict(),
            "epistemic_policy": self.epistemic_policy.to_dict(),
            "entries": [entry.to_dict() for entry in self.entries],
            "project_use_proposals": [
                proposal.to_dict() for proposal in self.project_use_proposals
            ],
            "engineering_decisions": [
                decision.to_dict() for decision in self.engineering_decisions
            ],
            "previous_ledger_sha256": self.previous_ledger_sha256,
        }

    def to_dict(self) -> dict[str, object]:
        record = self._unsigned_dict()
        record["ledger_sha256"] = self.ledger_sha256
        return record


def _object(value: Any, where: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise RecordError(f"{where} must be an object")
    return value


def _array(value: Any, where: str) -> list[Any]:
    if type(value) is not list:
        raise RecordError(f"{where} must be an array")
    return value


def _exact_keys(value: dict[str, Any], expected: set[str], where: str) -> None:
    actual = set(value)
    if actual != expected:
        raise RecordError(
            f"{where} keys differ; missing={sorted(expected - actual)}, "
            f"extra={sorted(actual - expected)}"
        )


def _enum(value: Any, enum_type: type[Enum], where: str) -> Any:
    if type(value) is not str:
        raise RecordError(f"{where} must be a string")
    try:
        return enum_type(value)
    except ValueError as exc:
        allowed = sorted(item.value for item in enum_type)
        raise RecordError(f"{where} must be one of {allowed}") from exc


def _boolean(value: Any, where: str) -> bool:
    if type(value) is not bool:
        raise RecordError(f"{where} must be a Boolean")
    return value


def _integer(value: Any, where: str) -> int:
    if type(value) is not int:
        raise RecordError(f"{where} must be an integer")
    return value


def _parse_source(value: Any, where: str) -> CanonicalSource:
    record = _object(value, where)
    _exact_keys(
        record,
        {
            "source_kind",
            "canonical_identifier",
            "canonical_url",
            "version",
            "versioned_url",
            "publication_year",
            "as_of_date",
            "retrieved_on",
        },
        where,
    )
    try:
        return CanonicalSource(
            source_kind=_enum(record["source_kind"], SourceKind, f"{where}.source_kind"),
            canonical_identifier=record["canonical_identifier"],
            canonical_url=record["canonical_url"],
            version=record["version"],
            versioned_url=record["versioned_url"],
            publication_year=_integer(
                record["publication_year"], f"{where}.publication_year"
            ),
            as_of_date=record["as_of_date"],
            retrieved_on=record["retrieved_on"],
        )
    except ValueError as exc:
        raise RecordError(str(exc)) from exc


def _parse_primary_inspection(value: Any, where: str) -> PrimaryInspection:
    record = _object(value, where)
    _exact_keys(
        record,
        {
            "locator",
            "version",
            "retrieved_on",
            "inspected_scope",
            "primary_source_inspected",
            "preservation_status",
            "source_artifact_sha256",
        },
        where,
    )
    if record["source_artifact_sha256"] is not None:
        raise RecordError(f"{where}.source_artifact_sha256 must be null in v2")
    try:
        return PrimaryInspection(
            locator=record["locator"],
            version=record["version"],
            retrieved_on=record["retrieved_on"],
            inspected_scope=record["inspected_scope"],
            primary_source_inspected=_boolean(
                record["primary_source_inspected"],
                f"{where}.primary_source_inspected",
            ),
            preservation_status=record["preservation_status"],
            source_artifact_sha256=None,
        )
    except ValueError as exc:
        raise RecordError(str(exc)) from exc


def _parse_discovery(value: Any, where: str) -> DiscoveryRecord:
    record = _object(value, where)
    _exact_keys(
        record,
        {
            "provider",
            "route_kind",
            "query",
            "route_locator",
            "discovered_on",
            "contemporary",
            "provider_output_is_oracle",
        },
        where,
    )
    try:
        return DiscoveryRecord(
            provider=record["provider"],
            route_kind=_enum(
                record["route_kind"],
                DiscoveryRouteKind,
                f"{where}.route_kind",
            ),
            query=record["query"],
            route_locator=record["route_locator"],
            discovered_on=record["discovered_on"],
            contemporary=_boolean(record["contemporary"], f"{where}.contemporary"),
            provider_output_is_oracle=_boolean(
                record["provider_output_is_oracle"],
                f"{where}.provider_output_is_oracle",
            ),
        )
    except ValueError as exc:
        raise RecordError(str(exc)) from exc


def _parse_entry(value: Any, where: str) -> ResearchEntry:
    record = _object(value, where)
    _exact_keys(
        record,
        {
            "entry_id",
            "title",
            "canonical_source",
            "primary_inspection",
            "discovery",
            "attacked_harness_question",
            "falsifier",
            "claim_kind",
            "report_scope",
            "report_author",
            "bounded_source_report",
            "report_sha256",
            "entry_sha256",
            "limitations",
            "epistemic_effect",
            "semantic_authority",
            "provider_output_is_oracle",
            "can_confirm_target_semantics",
            "human_adjudication_status",
        },
        where,
    )
    limitations = _array(record["limitations"], f"{where}.limitations")
    try:
        return ResearchEntry(
            entry_id=record["entry_id"],
            title=record["title"],
            canonical_source=_parse_source(
                record["canonical_source"], f"{where}.canonical_source"
            ),
            primary_inspection=_parse_primary_inspection(
                record["primary_inspection"], f"{where}.primary_inspection"
            ),
            discovery=_parse_discovery(record["discovery"], f"{where}.discovery"),
            attacked_harness_question=record["attacked_harness_question"],
            falsifier=record["falsifier"],
            claim_kind=record["claim_kind"],
            report_scope=record["report_scope"],
            report_author=record["report_author"],
            bounded_source_report=record["bounded_source_report"],
            report_sha256=record["report_sha256"],
            entry_sha256=record["entry_sha256"],
            limitations=tuple(limitations),
            epistemic_effect=record["epistemic_effect"],
            semantic_authority=_boolean(
                record["semantic_authority"], f"{where}.semantic_authority"
            ),
            provider_output_is_oracle=_boolean(
                record["provider_output_is_oracle"],
                f"{where}.provider_output_is_oracle",
            ),
            can_confirm_target_semantics=_boolean(
                record["can_confirm_target_semantics"],
                f"{where}.can_confirm_target_semantics",
            ),
            human_adjudication_status=_enum(
                record["human_adjudication_status"],
                HumanAdjudicationStatus,
                f"{where}.human_adjudication_status",
            ),
        )
    except ValueError as exc:
        raise RecordError(str(exc)) from exc


def parse_research_entry(value: Any) -> ResearchEntry:
    """Parse one standalone source report with the ledger's exact v2 rules.

    Inquiry events embed this immutable snapshot after the corresponding
    question exists.  The report therefore need not have been pre-seeded in
    the background research ledger, but it receives no additional epistemic
    force by being attached to an event.
    """

    return _parse_entry(value, "research_entry")


def parse_event_research_entry(
    value: Any,
    *,
    policy_ledger: ResearchLedger,
    recorded_on: str,
) -> ResearchEntry:
    """Parse an event-time source report under the bound ledger's policy.

    The ledger is a frozen background snapshot, so a later report is dated by
    its event rather than forced into the ledger's earlier data cut-off.  The
    provider, contemporaneity, primary-inspection, and anti-promotion rules are
    nevertheless inherited exactly from that bound policy.
    """

    if type(policy_ledger) is not ResearchLedger:
        raise TypeError("policy_ledger must be ResearchLedger")
    event_date = _iso_date(recorded_on, "inquiry_event.occurred_on")
    entry = parse_research_entry(value)
    if entry.canonical_source.as_of_date != event_date:
        raise PolicyViolation(
            "event research entry as_of_date must equal the recording event date"
        )
    if entry.canonical_source.retrieved_on > event_date:
        raise PolicyViolation("event research entry cannot be recorded before retrieval")
    contemporary = (
        entry.canonical_source.publication_year
        >= policy_ledger.provider_policy.contemporary_from_year
    )
    if entry.discovery.contemporary is not contemporary:
        raise PolicyViolation(
            f"entry {entry.entry_id} has an inconsistent contemporary marker"
        )
    if (
        entry.discovery.route_kind is DiscoveryRouteKind.DEFAULT_CONTEMPORARY
        and entry.discovery.provider
        != policy_ledger.provider_policy.default_contemporary_discovery_provider
    ):
        raise PolicyViolation(
            f"entry {entry.entry_id} default route must use the configured provider"
        )
    if (
        entry.discovery.route_kind is DiscoveryRouteKind.DEFAULT_CONTEMPORARY
        and not contemporary
    ):
        raise PolicyViolation(
            f"entry {entry.entry_id} default contemporary route requires a "
            "contemporary source"
        )
    if (
        entry.discovery.provider == "AlphaXiv"
        and not _is_schema_valid_alphaxiv_locator(entry.discovery.route_locator)
    ):
        raise PolicyViolation(
            f"entry {entry.entry_id} AlphaXiv route has a non-AlphaXiv locator"
        )
    return entry


def _parse_project_use_proposal(value: Any, where: str) -> ProjectUseProposal:
    record = _object(value, where)
    _exact_keys(
        record,
        {
            "schema_version",
            "proposal_id",
            "source_entry_id",
            "source_entry_sha256",
            "proposed_use",
            "rationale",
            "proposal_status",
            "epistemic_effect",
            "semantic_authority",
            "can_promote_hardening",
            "proposal_sha256",
        },
        where,
    )
    if record["schema_version"] != "creib.semantic-forge.project-use-proposal.v1":
        raise RecordError(f"{where}.schema_version is unknown")
    try:
        return ProjectUseProposal(
            proposal_id=record["proposal_id"],
            source_entry_id=record["source_entry_id"],
            source_entry_sha256=record["source_entry_sha256"],
            proposed_use=record["proposed_use"],
            rationale=record["rationale"],
            proposal_status=_enum(
                record["proposal_status"], ProposalStatus, f"{where}.proposal_status"
            ),
            epistemic_effect=record["epistemic_effect"],
            semantic_authority=_boolean(
                record["semantic_authority"], f"{where}.semantic_authority"
            ),
            can_promote_hardening=_boolean(
                record["can_promote_hardening"], f"{where}.can_promote_hardening"
            ),
            proposal_sha256=record["proposal_sha256"],
        )
    except ValueError as exc:
        raise RecordError(str(exc)) from exc


def _parse_engineering_decision(value: Any, where: str) -> EngineeringDecision:
    record = _object(value, where)
    _exact_keys(
        record,
        {
            "schema_version",
            "decision_id",
            "proposal_id",
            "proposal_sha256",
            "disposition",
            "rationale",
            "decided_on",
            "decision_maker_role",
            "decision_scope",
            "semantic_authority",
            "can_promote_hardening",
        },
        where,
    )
    if record["schema_version"] != "creib.semantic-forge.engineering-decision.v1":
        raise RecordError(f"{where}.schema_version is unknown")
    try:
        return EngineeringDecision(
            decision_id=record["decision_id"],
            proposal_id=record["proposal_id"],
            proposal_sha256=record["proposal_sha256"],
            disposition=_enum(
                record["disposition"], DecisionDisposition, f"{where}.disposition"
            ),
            rationale=record["rationale"],
            decided_on=record["decided_on"],
            decision_maker_role=record["decision_maker_role"],
            decision_scope=record["decision_scope"],
            semantic_authority=_boolean(
                record["semantic_authority"], f"{where}.semantic_authority"
            ),
            can_promote_hardening=_boolean(
                record["can_promote_hardening"], f"{where}.can_promote_hardening"
            ),
        )
    except ValueError as exc:
        raise RecordError(str(exc)) from exc


def parse_research_ledger(value: Any) -> ResearchLedger:
    """Parse one already-decoded ledger and reject every unknown field."""

    record = _object(value, "research_ledger")
    _exact_keys(
        record,
        {
            "$schema",
            "schema_version",
            "ledger_id",
            "title",
            "created_on",
            "as_of_date",
            "authority_boundary",
            "provider_policy",
            "epistemic_policy",
            "entries",
            "project_use_proposals",
            "engineering_decisions",
            "previous_ledger_sha256",
            "ledger_sha256",
        },
        "research_ledger",
    )

    authority_value = _object(record["authority_boundary"], "research_ledger.authority_boundary")
    _exact_keys(
        authority_value,
        {
            "target_document_id",
            "target_sha256",
            "external_research_semantic_authority",
            "external_reports_are_target_semantics",
        },
        "research_ledger.authority_boundary",
    )
    authority = AuthorityBoundary(
        target_document_id=authority_value["target_document_id"],
        target_sha256=authority_value["target_sha256"],
        external_research_semantic_authority=_boolean(
            authority_value["external_research_semantic_authority"],
            "research_ledger.authority_boundary.external_research_semantic_authority",
        ),
        external_reports_are_target_semantics=_boolean(
            authority_value["external_reports_are_target_semantics"],
            "research_ledger.authority_boundary.external_reports_are_target_semantics",
        ),
    )

    provider_value = _object(record["provider_policy"], "research_ledger.provider_policy")
    _exact_keys(
        provider_value,
        {
            "default_contemporary_discovery_provider",
            "contemporary_from_year",
            "consensus_role",
            "providers_replaceable",
            "direct_primary_source_required",
            "provider_output_is_oracle",
        },
        "research_ledger.provider_policy",
    )
    provider = ProviderPolicy(
        default_contemporary_discovery_provider=provider_value[
            "default_contemporary_discovery_provider"
        ],
        contemporary_from_year=_integer(
            provider_value["contemporary_from_year"],
            "research_ledger.provider_policy.contemporary_from_year",
        ),
        consensus_role=provider_value["consensus_role"],
        providers_replaceable=_boolean(
            provider_value["providers_replaceable"],
            "research_ledger.provider_policy.providers_replaceable",
        ),
        direct_primary_source_required=_boolean(
            provider_value["direct_primary_source_required"],
            "research_ledger.provider_policy.direct_primary_source_required",
        ),
        provider_output_is_oracle=_boolean(
            provider_value["provider_output_is_oracle"],
            "research_ledger.provider_policy.provider_output_is_oracle",
        ),
    )

    epistemic_value = _object(record["epistemic_policy"], "research_ledger.epistemic_policy")
    _exact_keys(
        epistemic_value,
        {
            "claim_kind",
            "research_role",
            "passing_reports_confirm_model",
            "frequency_or_citation_count_can_promote",
            "provider_agreement_can_promote",
            "inductive_promotion_permitted",
            "research_can_close_semantic_question",
        },
        "research_ledger.epistemic_policy",
    )
    epistemic = EpistemicPolicy(
        claim_kind=epistemic_value["claim_kind"],
        research_role=epistemic_value["research_role"],
        passing_reports_confirm_model=_boolean(
            epistemic_value["passing_reports_confirm_model"],
            "research_ledger.epistemic_policy.passing_reports_confirm_model",
        ),
        frequency_or_citation_count_can_promote=_boolean(
            epistemic_value["frequency_or_citation_count_can_promote"],
            "research_ledger.epistemic_policy.frequency_or_citation_count_can_promote",
        ),
        provider_agreement_can_promote=_boolean(
            epistemic_value["provider_agreement_can_promote"],
            "research_ledger.epistemic_policy.provider_agreement_can_promote",
        ),
        inductive_promotion_permitted=_boolean(
            epistemic_value["inductive_promotion_permitted"],
            "research_ledger.epistemic_policy.inductive_promotion_permitted",
        ),
        research_can_close_semantic_question=_boolean(
            epistemic_value["research_can_close_semantic_question"],
            "research_ledger.epistemic_policy.research_can_close_semantic_question",
        ),
    )

    entry_values = _array(record["entries"], "research_ledger.entries")
    proposal_values = _array(
        record["project_use_proposals"],
        "research_ledger.project_use_proposals",
    )
    decision_values = _array(
        record["engineering_decisions"],
        "research_ledger.engineering_decisions",
    )
    previous_digest = record["previous_ledger_sha256"]
    if previous_digest is not None and type(previous_digest) is not str:
        raise RecordError("research_ledger.previous_ledger_sha256 must be null or string")
    try:
        return ResearchLedger(
            schema_ref=record["$schema"],
            schema_version=record["schema_version"],
            ledger_id=record["ledger_id"],
            title=record["title"],
            created_on=record["created_on"],
            as_of_date=record["as_of_date"],
            authority_boundary=authority,
            provider_policy=provider,
            epistemic_policy=epistemic,
            entries=tuple(
                _parse_entry(item, f"research_ledger.entries[{index}]")
                for index, item in enumerate(entry_values)
            ),
            project_use_proposals=tuple(
                _parse_project_use_proposal(
                    item,
                    f"research_ledger.project_use_proposals[{index}]",
                )
                for index, item in enumerate(proposal_values)
            ),
            engineering_decisions=tuple(
                _parse_engineering_decision(
                    item,
                    f"research_ledger.engineering_decisions[{index}]",
                )
                for index, item in enumerate(decision_values)
            ),
            previous_ledger_sha256=previous_digest,
            ledger_sha256=record["ledger_sha256"],
        )
    except ValueError as exc:
        raise RecordError(str(exc)) from exc


def load_research_ledger(path: Path) -> ResearchLedger:
    """Load strict UTF-8 JSON and validate the external-research ledger."""

    return parse_research_ledger(load_strict(path))


def loads_research_ledger(source: str) -> ResearchLedger:
    """Load a strict JSON string and validate the external-research ledger."""

    return parse_research_ledger(loads_strict(source))


def dumps_research_ledger(ledger: ResearchLedger) -> str:
    """Serialize a validated ledger deterministically without changing its reports."""

    if type(ledger) is not ResearchLedger:
        raise TypeError("ledger must be ResearchLedger")
    return json.dumps(
        ledger.to_dict(),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
