"""Deterministic first-run calibration for the semantic-model forge.

The calibration deliberately evaluates a tiny finite fixture.  Its mechanics
expose exact equality and erasure-invariance criticism candidates; they do not
adjudicate that a definition is too weak, that a predicate is semantically
disconnected, or what CR-1.0 means.  Those judgments remain human tasks against
the digest-bound authority and declared test oracle.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import errno
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from creib.canonical import bytes_digest, canonical_bytes, domain_digest
from creib.errors import AuthorityMismatch, RecordError
from creib.strict_json import loads_strict
from creib.verify import verify_bundle, verify_pdf

from .engine import (
    assess_formalization_readiness,
    assess_revision,
    generate_research_warrant,
)
from .schema_validation import load_local_schema_catalog
from .models import (
    DefectType,
    Issue,
    JustificationBasis,
    MinimalPairChallenge,
    NON_INDUCTIVE_LIMIT,
    PreservationDimension,
    Rival,
    UnknownKind,
    parse_issue,
    parse_minimal_pair_challenge,
)


CALIBRATION_SCHEMA = "creib.semantic-forge.calibration-run.v1"
CALIBRATION_CONTRACT_SCHEMA = "creib.semantic-forge.calibration-contract.v1"
AUTHORITY_BINDING_STATUS = "MECHANICALLY_VALID"
AUTHORITY_SEMANTIC_SCOPE = "EXTERNAL_CR_1_0_PDF_ONLY"
AUTHORITY_VERIFICATION_SCOPE = (
    "PDF identity, byte length, page structure, and pinned source anchors; "
    "not a semantic verdict"
)
ROLE_CHALLENGE_ID = "SMF-CH-ROLE-RELABEL-TWIN-001"
ROLE_ISSUE_ID = "SMF-RI-ROLE-REALIZATION-001"
RUN_ID = "SMF-CALIBRATION-CR-1-0-001"
CANDIDATE_ID = "SMF-FIXTURE-TYPED-ROLE-PROJECTION"
NAIVE_REVISION_ID = "SMF-0.1-VACUOUS-GROUNDING"
SEED_CORPUS_ID = "SMF-CORPUS-CR-1-0-SEED"
ANNOTATION_PROSE_STATUS = "unreviewed_non_authoritative"
ANNOTATION_PROSE_SEMANTIC_EFFECT = "none"

# Updated only when the reviewed seed corpus bytes deliberately change.  The
# fixed first-run identity is unavailable to arbitrary custom corpora even if
# they reuse all visible record identifiers.
PINNED_SEED_CORPUS_SHA256 = (
    "4219efceb5502aa8b9209884ec1d22533d6eb049277c8ae3354d08e38f7c47a6"
)

WEAK_ROLE_EVALUATOR_ID = "SMF-EVAL-WEAK-ROLE-PROJECTION-001"
ERASURE_EVALUATOR_ID = "SMF-EVAL-NAIVE-EXISTENTIAL-ERASURE-001"

# The digest is over the canonical, typed challenge record rather than its ID
# or defect label.  It prevents contrary prose from selecting a hard-coded
# evaluator merely by retaining those two shallow fields.
PINNED_ROLE_CHALLENGE_CONTRACT_SHA256 = (
    "60eaccc0eff53936740ef063edd332e86dbac0b7bd098b720d6ca90628647b3d"
)

_IMPLEMENTATION_CODE_PATHS = (
    "src/creib/__init__.py",
    "src/creib/canonical.py",
    "src/creib/errors.py",
    "src/creib/evidence.py",
    "src/creib/models.py",
    "src/creib/strict_json.py",
    "src/creib/verify.py",
    "src/creib/forge/__init__.py",
    "src/creib/forge/models.py",
    "src/creib/forge/engine.py",
    "src/creib/forge/research.py",
    "src/creib/forge/inquiry.py",
    "src/creib/forge/schema_validation.py",
    "src/creib/forge/calibration.py",
    "tools/run_semantic_forge.py",
    "tools/run_semantic_inquiry.py",
    "tools/validate_semantic_forge.py",
)

_AUTHORITY_BINDING_KEYS = {
    "status",
    "document_id",
    "sha256",
    "byte_length",
    "physical_pdf_pages",
    "semantic_authority",
    "verification_scope",
}
_CORPUS_KEYS = {
    "$schema",
    "schema_version",
    "corpus_id",
    "title",
    "authority",
    "epistemic_policy",
    "research_policy",
    "challenges",
    "challenge_annotations",
    "research_issues",
    "research_issue_annotations",
}

_REPORT_KEYS = {
    "schema_version",
    "run_id",
    "run_status",
    "mechanical_status",
    "epistemic_status",
    "review_status",
    "result_scope",
    "semantic_verdict",
    "human_disposition",
    "epistemic_limit",
    "authority_binding",
    "corpus_trace",
    "execution_contract",
    "fixture_evaluations",
    "research_routing",
    "hardening_assessments",
    "formalization_readiness",
    "human_review",
}

_EXECUTION_CONTRACT_KEYS = {
    "schema_version",
    "run_id",
    "corpus_id",
    "corpus_sha256",
    "authority_sha256",
    "challenge_contract_sha256",
    "fixture_contract_sha256",
    "candidate_contract_sha256",
    "naive_revision_contract_sha256",
    "evaluator_contract_sha256",
    "implementation_file_sha256",
    "run_contract_sha256",
}


class CalibrationRunError(RecordError):
    """A stable, machine-classifiable calibration persistence failure."""

    def __init__(self, error_code: str, message: str) -> None:
        super().__init__(message)
        self.error_code = error_code


def _object(value: Any, where: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise RecordError(f"{where} must be an object")
    return value


def _exact_keys(value: dict[str, Any], expected: set[str], where: str) -> None:
    actual = set(value)
    if actual != expected:
        raise RecordError(
            f"{where} keys differ; missing={sorted(expected - actual)}, "
            f"extra={sorted(actual - expected)}"
        )


def _array(value: Any, where: str) -> list[Any]:
    if type(value) is not list:
        raise RecordError(f"{where} must be an array")
    return value


def _string(value: Any, where: str) -> str:
    if type(value) is not str or not value.strip():
        raise RecordError(f"{where} must be a non-empty string")
    return value


def _integer(value: Any, where: str) -> int:
    if type(value) is not int or value < 1:
        raise RecordError(f"{where} must be a positive integer")
    return value


def _boolean(value: Any, where: str) -> bool:
    if type(value) is not bool:
        raise RecordError(f"{where} must be a boolean")
    return value


def _read_bytes(path: Path, where: str) -> bytes:
    """Read one immutable input snapshot or raise a stable record failure."""

    try:
        return path.read_bytes()
    except OSError as exc:
        raise RecordError(f"cannot read {where} {path}: {exc}") from exc


def _strict_json_snapshot(path: Path, where: str) -> tuple[Any, bytes, str]:
    """Hash and parse exactly the same byte snapshot.

    Returning both the bytes and their digest makes it impossible for a
    second path read to silently bind the parsed value to different bytes.
    """

    raw_bytes = _read_bytes(path, where)
    digest = bytes_digest(raw_bytes)
    try:
        source = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RecordError(f"{where} is not UTF-8: {path}") from exc
    return loads_strict(source), raw_bytes, digest


def _contract_sha256(domain: str, value: Any) -> str:
    digest = domain_digest(domain, value)
    if not digest.startswith("sha256:"):
        raise RecordError("contract digest implementation returned an unknown algorithm")
    return digest.removeprefix("sha256:")


def _require_sha256(value: Any, where: str) -> str:
    digest = _string(value, where)
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise RecordError(f"{where} must be a lowercase SHA-256 digest")
    return digest


def _repo_root_from_module() -> Path:
    return Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class CorpusAuthority:
    """Authority identity copied from, but never substituted for, the PDF."""

    document_id: str
    sha256: str
    byte_length: int
    physical_pdf_pages: int
    semantic_and_formal_authority: bool
    supplied_externally: bool


@dataclass(frozen=True)
class CorpusAnnotation:
    """An immutable canonical snapshot of one schema-validated annotation."""

    record_id: str
    annotation_prose_status: str
    annotation_prose_semantic_effect: str
    canonical_json: str
    canonical_sha256: str


@dataclass(frozen=True)
class CalibrationCorpus:
    """Strictly parsed runtime records required by the calibration."""

    corpus_id: str
    corpus_sha256: str
    authority: CorpusAuthority
    discovery_channels: tuple[str, ...]
    provider_replaceable: bool
    provider_output_is_oracle: bool
    falsifier_first: bool
    challenges: tuple[MinimalPairChallenge, ...]
    issues: tuple[Issue, ...]
    challenge_annotations: tuple[CorpusAnnotation, ...]
    issue_annotations: tuple[CorpusAnnotation, ...]

    @property
    def challenge_annotation_ids(self) -> tuple[str, ...]:
        return tuple(item.record_id for item in self.challenge_annotations)

    @property
    def issue_annotation_ids(self) -> tuple[str, ...]:
        return tuple(item.record_id for item in self.issue_annotations)

    def challenge(self, challenge_id: str) -> MinimalPairChallenge:
        matches = tuple(
            challenge
            for challenge in self.challenges
            if challenge.challenge_id == challenge_id
        )
        if len(matches) != 1:
            raise RecordError(
                f"corpus must contain exactly one challenge {challenge_id!r}"
            )
        return matches[0]

    def issue(self, issue_id: str) -> Issue:
        matches = tuple(issue for issue in self.issues if issue.issue_id == issue_id)
        if len(matches) != 1:
            raise RecordError(f"corpus must contain exactly one issue {issue_id!r}")
        return matches[0]


@dataclass(frozen=True)
class RoleFixtureCase:
    """One finite mechanical case, not a semantic model of a real system."""

    case_id: str
    typed_events_present: bool
    typed_role_predicates_present: bool
    system_level_causal_use: bool
    matched_counterfactual_support: bool


def _corpus_annotation(value: Any, where: str) -> CorpusAnnotation:
    record = _object(value, where)
    record_id = _string(record.get("record_id"), f"{where}.record_id")
    prose_status = _string(
        record.get("annotation_prose_status"),
        f"{where}.annotation_prose_status",
    )
    prose_effect = _string(
        record.get("annotation_prose_semantic_effect"),
        f"{where}.annotation_prose_semantic_effect",
    )
    if prose_status != ANNOTATION_PROSE_STATUS:
        raise RecordError(
            f"{where} annotation prose must remain unreviewed and non-authoritative"
        )
    if prose_effect != ANNOTATION_PROSE_SEMANTIC_EFFECT:
        raise RecordError(f"{where} annotation prose must have no semantic effect")
    encoded = canonical_bytes(record)
    return CorpusAnnotation(
        record_id=record_id,
        annotation_prose_status=prose_status,
        annotation_prose_semantic_effect=prose_effect,
        canonical_json=encoded.decode("utf-8"),
        canonical_sha256=bytes_digest(encoded),
    )


def load_calibration_corpus(path: Path) -> CalibrationCorpus:
    """Strict-load the corpus and parse every runtime challenge and issue."""

    snapshot, _raw_bytes, corpus_sha256 = _strict_json_snapshot(path, "corpus")
    raw = _object(snapshot, "corpus")
    load_local_schema_catalog(
        _repo_root_from_module() / "forge" / "schema"
    ).validate(raw, "corpus.schema.json")
    _exact_keys(raw, _CORPUS_KEYS, "corpus")
    if raw.get("schema_version") != "smf-corpus-0.1":
        raise RecordError("unknown semantic-forge corpus schema version")
    corpus_id = _string(raw.get("corpus_id"), "corpus.corpus_id")

    raw_authority = _object(raw.get("authority"), "corpus.authority")
    _exact_keys(
        raw_authority,
        {
            "document_id",
            "sha256",
            "byte_length",
            "physical_pdf_pages",
            "semantic_and_formal_authority",
            "supplied_externally",
        },
        "corpus.authority",
    )
    authority = CorpusAuthority(
        document_id=_string(
            raw_authority.get("document_id"), "corpus.authority.document_id"
        ),
        sha256=_string(raw_authority.get("sha256"), "corpus.authority.sha256"),
        byte_length=_integer(
            raw_authority.get("byte_length"), "corpus.authority.byte_length"
        ),
        physical_pdf_pages=_integer(
            raw_authority.get("physical_pdf_pages"),
            "corpus.authority.physical_pdf_pages",
        ),
        semantic_and_formal_authority=_boolean(
            raw_authority.get("semantic_and_formal_authority"),
            "corpus.authority.semantic_and_formal_authority",
        ),
        supplied_externally=_boolean(
            raw_authority.get("supplied_externally"),
            "corpus.authority.supplied_externally",
        ),
    )
    if not authority.semantic_and_formal_authority or not authority.supplied_externally:
        raise RecordError("corpus must preserve the external PDF authority boundary")

    epistemic_policy = _object(
        raw.get("epistemic_policy"), "corpus.epistemic_policy"
    )
    _exact_keys(
        epistemic_policy,
        {
            "claim_kind_meanings",
            "research_role",
            "passing_tests_confirms",
            "failed_test_targets_whole_conjunction",
            "unresolved_is_not_false",
            "frequency_or_consensus_can_promote_authority",
        },
        "corpus.epistemic_policy",
    )
    if epistemic_policy["research_role"] != (
        "generate_and_sharpen_criticism_not_confirm_the_model"
    ):
        raise RecordError("corpus research role must remain criticism-only")
    epistemic_boolean_policy = {
        "passing_tests_confirms": False,
        "failed_test_targets_whole_conjunction": True,
        "unresolved_is_not_false": True,
        "frequency_or_consensus_can_promote_authority": False,
    }
    for field, required in epistemic_boolean_policy.items():
        if _boolean(
            epistemic_policy[field], f"corpus.epistemic_policy.{field}"
        ) is not required:
            raise RecordError(f"corpus epistemic policy is unsafe for {field}")

    raw_policy = _object(raw.get("research_policy"), "corpus.research_policy")
    _exact_keys(
        raw_policy,
        {
            "preferred_discovery_channels",
            "provider_replaceable",
            "falsifier_first",
            "provider_output_is_oracle",
        },
        "corpus.research_policy",
    )
    raw_channels = _array(
        raw_policy.get("preferred_discovery_channels"),
        "corpus.research_policy.preferred_discovery_channels",
    )
    channels = tuple(
        _string(value, f"corpus.research_policy.preferred_discovery_channels[{index}]")
        for index, value in enumerate(raw_channels)
    )
    if not channels or len(channels) != len(set(channels)):
        raise RecordError("preferred discovery channels must be non-empty and unique")
    provider_replaceable = _boolean(
        raw_policy.get("provider_replaceable"),
        "corpus.research_policy.provider_replaceable",
    )
    provider_output_is_oracle = _boolean(
        raw_policy.get("provider_output_is_oracle"),
        "corpus.research_policy.provider_output_is_oracle",
    )
    falsifier_first = _boolean(
        raw_policy.get("falsifier_first"),
        "corpus.research_policy.falsifier_first",
    )
    if not provider_replaceable or provider_output_is_oracle or not falsifier_first:
        raise RecordError(
            "research policy must remain replaceable, falsifier-first, and non-oracular"
        )

    challenges = tuple(
        parse_minimal_pair_challenge(value)
        for value in _array(raw.get("challenges"), "corpus.challenges")
    )
    issues = tuple(
        parse_issue(value)
        for value in _array(raw.get("research_issues"), "corpus.research_issues")
    )
    challenge_ids = tuple(challenge.challenge_id for challenge in challenges)
    issue_ids = tuple(issue.issue_id for issue in issues)
    if len(challenge_ids) != len(set(challenge_ids)):
        raise RecordError("corpus challenge identifiers must be unique")
    if len(issue_ids) != len(set(issue_ids)):
        raise RecordError("corpus issue identifiers must be unique")

    challenge_annotations = tuple(
        _corpus_annotation(value, f"corpus.challenge_annotations[{index}]")
        for index, value in enumerate(
            _array(raw.get("challenge_annotations"), "corpus.challenge_annotations")
        )
    )
    issue_annotations = tuple(
        _corpus_annotation(value, f"corpus.research_issue_annotations[{index}]")
        for index, value in enumerate(
            _array(
                raw.get("research_issue_annotations"),
                "corpus.research_issue_annotations",
            )
        )
    )
    challenge_annotation_ids = tuple(
        item.record_id for item in challenge_annotations
    )
    issue_annotation_ids = tuple(item.record_id for item in issue_annotations)
    if len(challenge_annotation_ids) != len(set(challenge_annotation_ids)):
        raise RecordError("corpus challenge annotation identifiers must be unique")
    if len(issue_annotation_ids) != len(set(issue_annotation_ids)):
        raise RecordError("corpus issue annotation identifiers must be unique")
    if set(challenge_annotation_ids) != set(challenge_ids):
        raise RecordError("corpus challenge annotation coverage must be one-to-one")
    if set(issue_annotation_ids) != set(issue_ids):
        raise RecordError("corpus issue annotation coverage must be one-to-one")

    return CalibrationCorpus(
        corpus_id=corpus_id,
        corpus_sha256=corpus_sha256,
        authority=authority,
        discovery_channels=channels,
        provider_replaceable=provider_replaceable,
        provider_output_is_oracle=provider_output_is_oracle,
        falsifier_first=falsifier_first,
        challenges=challenges,
        issues=issues,
        challenge_annotations=challenge_annotations,
        issue_annotations=issue_annotations,
    )


def verify_authority_binding(
    repo_root: Path,
    pdf_path: Path,
    corpus_authority: CorpusAuthority,
) -> dict[str, object]:
    """Verify the external PDF through the existing digest-bound tooling."""

    bundle = verify_bundle(repo_root, with_records=True)
    if type(bundle) is not tuple:
        raise RecordError("authority verifier did not return validated records")
    _bundle_report, manifest, anchors = bundle
    verify_pdf(pdf_path, manifest, anchors)

    comparisons = {
        "document_id": corpus_authority.document_id,
        "sha256": corpus_authority.sha256,
        "byte_length": corpus_authority.byte_length,
        "page_count": corpus_authority.physical_pdf_pages,
    }
    for field, expected in comparisons.items():
        if manifest[field] != expected:
            raise AuthorityMismatch(
                f"corpus authority disagrees with source manifest for {field}"
            )

    return {
        "status": AUTHORITY_BINDING_STATUS,
        "document_id": manifest["document_id"],
        "sha256": manifest["sha256"],
        "byte_length": manifest["byte_length"],
        "physical_pdf_pages": manifest["page_count"],
        "semantic_authority": AUTHORITY_SEMANTIC_SCOPE,
        "verification_scope": AUTHORITY_VERIFICATION_SCOPE,
    }


def role_fixture_cases() -> tuple[RoleFixtureCase, ...]:
    """Return the grounded case and the labels-only contrast case."""

    return (
        RoleFixtureCase(
            case_id="GROUNDED-ROLE-ASSIGNMENT",
            typed_events_present=True,
            typed_role_predicates_present=True,
            system_level_causal_use=True,
            matched_counterfactual_support=True,
        ),
        RoleFixtureCase(
            case_id="LABELS-ONLY-CONTRAST",
            typed_events_present=True,
            typed_role_predicates_present=True,
            system_level_causal_use=False,
            matched_counterfactual_support=False,
        ),
    )


def _challenge_contract_sha256(challenge: MinimalPairChallenge) -> str:
    return _contract_sha256(
        "creib.semantic-forge.challenge-contract.v1",
        challenge.to_dict(),
    )


def _fixture_contract() -> dict[str, object]:
    return {
        "schema_version": "creib.semantic-forge.role-fixture.v1",
        "cases": [asdict(case) for case in role_fixture_cases()],
        "pair_relation": (
            "typed events, typed predicates, and declared surface behavior are "
            "held fixed; causal use and matched counterfactual support vary together"
        ),
    }


def _candidate_contract() -> dict[str, object]:
    return {
        "schema_version": "creib.semantic-forge.candidate-contract.v1",
        "candidate_id": CANDIDATE_ID,
        "input_type": "RoleFixtureCase",
        "admission_operator": "logical_conjunction",
        "required_true_fields": [
            "typed_events_present",
            "typed_role_predicates_present",
        ],
        "ignored_fields": [
            "system_level_causal_use",
            "matched_counterfactual_support",
        ],
    }


def _naive_revision_contract() -> dict[str, object]:
    return {
        "schema_version": "creib.semantic-forge.revision-contract.v1",
        "revision_id": NAIVE_REVISION_ID,
        "baseline_id": CANDIDATE_ID,
        "new_predicate": "RoleGrounded",
        "new_predicate_domain": [False, True],
        "admission_dependency": [],
        "erasure_operator": "existential_disjunction_over_new_predicate",
    }


def _mechanical_contract_digests() -> dict[str, object]:
    fixture_sha256 = _contract_sha256(
        "creib.semantic-forge.fixture-contract.v1",
        _fixture_contract(),
    )
    candidate_sha256 = _contract_sha256(
        "creib.semantic-forge.candidate-contract.v1",
        _candidate_contract(),
    )
    revision_sha256 = _contract_sha256(
        "creib.semantic-forge.revision-contract.v1",
        _naive_revision_contract(),
    )
    erasure_evaluator_contract = {
        "schema_version": "creib.semantic-forge.evaluator-contract.v1",
        "evaluator_id": ERASURE_EVALUATOR_ID,
        "fixture_contract_sha256": fixture_sha256,
        "candidate_contract_sha256": candidate_sha256,
        "naive_revision_contract_sha256": revision_sha256,
        "mechanical_claim": (
            "enumerate both RoleGrounded values and existentially erase the "
            "new predicate before comparing old-language admissions"
        ),
    }
    return {
        "fixture_contract_sha256": fixture_sha256,
        "candidate_contract_sha256": candidate_sha256,
        "naive_revision_contract_sha256": revision_sha256,
        "naive_existential_erasure_evaluator_sha256": _contract_sha256(
            "creib.semantic-forge.evaluator-contract.v1",
            erasure_evaluator_contract,
        ),
    }


def _contract_digests(challenge: MinimalPairChallenge) -> dict[str, object]:
    challenge_sha256 = _challenge_contract_sha256(challenge)
    mechanical = _mechanical_contract_digests()
    fixture_sha256 = mechanical["fixture_contract_sha256"]
    candidate_sha256 = mechanical["candidate_contract_sha256"]
    revision_sha256 = mechanical["naive_revision_contract_sha256"]
    evaluator_contracts = {
        "weak_typed_role_projection": {
            "schema_version": "creib.semantic-forge.evaluator-contract.v1",
            "evaluator_id": WEAK_ROLE_EVALUATOR_ID,
            "challenge_contract_sha256": challenge_sha256,
            "fixture_contract_sha256": fixture_sha256,
            "candidate_contract_sha256": candidate_sha256,
            "mechanical_claim": (
                "evaluate candidate admission on both fixture cases and report "
                "whether both are admitted"
            ),
        },
    }
    return {
        "challenge_contract_sha256": challenge_sha256,
        "fixture_contract_sha256": fixture_sha256,
        "candidate_contract_sha256": candidate_sha256,
        "naive_revision_contract_sha256": revision_sha256,
        "evaluator_contract_sha256": {
            "weak_typed_role_projection": _contract_sha256(
                "creib.semantic-forge.evaluator-contract.v1",
                evaluator_contracts["weak_typed_role_projection"],
            ),
            "naive_existential_erasure": mechanical[
                "naive_existential_erasure_evaluator_sha256"
            ],
        },
    }


def implementation_file_digests(repo_root: Path) -> dict[str, str]:
    """Hash every code and schema file that participates in one CLI run.

    The offline schema catalog discovers all ``*.schema.json`` files.  The
    execution trace therefore discovers and binds that same complete set,
    rather than relying on a list that could silently become stale when a new
    record family is added.
    """

    if not isinstance(repo_root, Path):
        raise TypeError("repo_root must be a Path")
    root = repo_root.resolve()
    module_path = Path(__file__).resolve()
    expected_module_path = (root / "src/creib/forge/calibration.py").resolve()
    if module_path != expected_module_path:
        raise RecordError(
            "loaded calibration implementation is outside the selected repository"
        )
    schema_dir = root / "forge" / "schema"
    schema_paths = tuple(sorted(schema_dir.glob("*.schema.json")))
    if not schema_paths:
        raise RecordError("semantic-forge execution requires local schema files")
    relative_schema_paths: list[str] = []
    for schema_path in schema_paths:
        resolved = schema_path.resolve()
        try:
            relative = resolved.relative_to(root)
        except ValueError as exc:
            raise RecordError(
                f"semantic-forge schema resolves outside the repository: {schema_path}"
            ) from exc
        if resolved != schema_path.absolute() or not resolved.is_file():
            raise RecordError(
                f"semantic-forge schema must be a regular in-repository file: {schema_path}"
            )
        relative_schema_paths.append(relative.as_posix())
    implementation_paths = _IMPLEMENTATION_CODE_PATHS + tuple(relative_schema_paths)
    if len(implementation_paths) != len(set(implementation_paths)):
        raise RecordError("semantic-forge implementation trace contains duplicate paths")
    return {
        relative_path: bytes_digest(
            _read_bytes(root / relative_path, f"implementation file {relative_path}")
        )
        for relative_path in implementation_paths
    }


def _require_pinned_first_run_corpus(corpus: CalibrationCorpus) -> None:
    if corpus.corpus_id != SEED_CORPUS_ID:
        raise RecordError(
            f"fixed first-run ID {RUN_ID!r} requires corpus ID {SEED_CORPUS_ID!r}"
        )
    if corpus.corpus_sha256 != PINNED_SEED_CORPUS_SHA256:
        raise RecordError(
            f"fixed first-run ID {RUN_ID!r} requires pinned seed corpus SHA-256 "
            f"{PINNED_SEED_CORPUS_SHA256}; observed {corpus.corpus_sha256}"
        )


def _require_bound_role_challenge(challenge: MinimalPairChallenge) -> dict[str, object]:
    if challenge.challenge_id != ROLE_CHALLENGE_ID:
        raise RecordError("the first calibration requires the role-relabel challenge")
    if challenge.defect_type != DefectType.ROLE_RELABELING.value:
        raise RecordError("the selected challenge must target role relabelling")
    contracts = _contract_digests(challenge)
    if (
        contracts["challenge_contract_sha256"]
        != PINNED_ROLE_CHALLENGE_CONTRACT_SHA256
    ):
        raise RecordError(
            "the role evaluator is not registered for this challenge content; "
            "matching an ID and defect type is insufficient"
        )
    return contracts


def weak_typed_role_projection(case: RoleFixtureCase) -> bool:
    """The intentionally weak candidate ignores causal and counterfactual use."""

    if type(case) is not RoleFixtureCase:
        raise TypeError("case must be RoleFixtureCase")
    return case.typed_events_present and case.typed_role_predicates_present


def evaluate_weak_role_projection(
    challenge: MinimalPairChallenge,
) -> dict[str, object]:
    """Mechanically show that the weak candidate admits both fixture cases."""

    if type(challenge) is not MinimalPairChallenge:
        raise TypeError("challenge must be MinimalPairChallenge")
    contracts = _require_bound_role_challenge(challenge)

    cases = role_fixture_cases()
    case_results = [
        {
            "case_id": case.case_id,
            "typed_events_present": case.typed_events_present,
            "typed_role_predicates_present": case.typed_role_predicates_present,
            "system_level_causal_use": case.system_level_causal_use,
            "matched_counterfactual_support": case.matched_counterfactual_support,
            "admitted_by_weak_projection": weak_typed_role_projection(case),
        }
        for case in cases
    ]
    both_admitted = all(
        result["admitted_by_weak_projection"] is True for result in case_results
    )
    return {
        "result_scope": "NON_AUTHORITATIVE_MECHANICAL_FIXTURE",
        "mechanical_status": "MECHANICALLY_VALID",
        "semantic_verdict": None,
        "candidate_id": CANDIDATE_ID,
        "challenge_id": challenge.challenge_id,
        "contract_binding": {
            "evaluator_id": WEAK_ROLE_EVALUATOR_ID,
            "challenge_contract_sha256": contracts[
                "challenge_contract_sha256"
            ],
            "fixture_contract_sha256": contracts["fixture_contract_sha256"],
            "candidate_contract_sha256": contracts["candidate_contract_sha256"],
            "evaluator_contract_sha256": contracts[
                "evaluator_contract_sha256"
            ]["weak_typed_role_projection"],
        },
        "candidate_rule": (
            "admit exactly when typed events and typed role predicates are present"
        ),
        "omitted_authority_constraints": [
            "SC-2 system-level causal use and semantic invariance",
            "SC-3 content-sensitive causal and counterfactual role constraints",
        ],
        "case_results": case_results,
        "mechanical_observation": (
            "BOTH_GROUNDED_AND_LABELS_ONLY_CONTRASTS_ADMITTED"
            if both_admitted
            else "FIXTURE_DID_NOT_REPRODUCE_EXPECTED_WEAKNESS"
        ),
    }


def evaluate_naive_existential_erasure() -> dict[str, object]:
    """Forget an unconstrained RoleGrounded predicate over the finite fixture."""

    contracts = _mechanical_contract_digests()
    cases = role_fixture_cases()
    baseline = {
        case.case_id: weak_typed_role_projection(case)
        for case in cases
    }
    expansions: list[dict[str, object]] = []
    erased: dict[str, bool] = {}
    for case in cases:
        expanded_results: list[bool] = []
        for role_grounded in (False, True):
            # The defect is intentional: RoleGrounded occurs nowhere in the
            # revised admission rule, so the two expansions are identical.
            admitted = weak_typed_role_projection(case)
            expanded_results.append(admitted)
            expansions.append(
                {
                    "case_id": case.case_id,
                    "role_grounded": role_grounded,
                    "admitted_by_naive_revision": admitted,
                }
            )
        erased[case.case_id] = any(expanded_results)

    old_language_result_preserved = erased == baseline
    return {
        "result_scope": "NON_AUTHORITATIVE_MECHANICAL_FIXTURE",
        "mechanical_status": "MECHANICALLY_VALID",
        "semantic_verdict": None,
        "revision_id": NAIVE_REVISION_ID,
        "contract_binding": {
            "evaluator_id": ERASURE_EVALUATOR_ID,
            "fixture_contract_sha256": contracts["fixture_contract_sha256"],
            "candidate_contract_sha256": contracts["candidate_contract_sha256"],
            "naive_revision_contract_sha256": contracts[
                "naive_revision_contract_sha256"
            ],
            "evaluator_contract_sha256": contracts[
                "naive_existential_erasure_evaluator_sha256"
            ],
        },
        "new_predicate": "RoleGrounded",
        "new_predicate_connected_to_admission": False,
        "expanded_case_results": expansions,
        "baseline_old_language_admission": baseline,
        "existentially_erased_admission": erased,
        "old_language_result_preserved": old_language_result_preserved,
        "mechanical_observation": (
            "EXISTENTIAL_ERASURE_CHANGES_NOTHING_IN_FIXTURE"
            if old_language_result_preserved
            else "EXISTENTIAL_ERASURE_CHANGED_THE_FIXTURE"
        ),
    }


def internal_erasure_issue() -> Issue:
    """State the erasure question as an internal modelling issue."""

    return Issue(
        issue_id="SMF-INTERNAL-ERASURE-001",
        question=(
            "Does adding RoleGrounded change any old-language consequence after "
            "existential erasure?"
        ),
        unknown_kind=UnknownKind.INTERNAL,
        decision="Decide whether the naive RoleGrounded revision hardens the candidate.",
        decision_relevance=(
            "Erasure equivalence defeats old-language restriction; a separate, "
            "connected witness would still be required to show role-expansion narrowing."
        ),
        rivals=(
            Rival(
                rival_id="ERASURE-EQUIVALENT",
                claim="Existential erasure returns the original candidate theory.",
                falsifier_conditions=(
                    "An old-language fixture classification changes under every admissible expansion.",
                ),
            ),
            Rival(
                rival_id="ERASURE-STRENGTHENS",
                claim="Existential erasure excludes at least one old-language candidate model.",
                falsifier_conditions=(
                    "Every old-language model has an expansion satisfying the disconnected predicate addition.",
                ),
            ),
        ),
    )


def attack_search_targets(issue: Issue) -> list[dict[str, object]]:
    """Derive falsifier-first search targets without running a provider."""

    if type(issue) is not Issue:
        raise TypeError("issue must be Issue")
    targets: list[dict[str, object]] = []
    for rival in issue.rivals:
        for position, condition in enumerate(rival.falsifier_conditions, start=1):
            targets.append(
                {
                    "target_id": f"{issue.issue_id}:{rival.rival_id}:ATTACK-{position}",
                    "rival_id": rival.rival_id,
                    "falsifier_condition": condition,
                    "attack_query": (
                        "Find a primary or contemporary counterexample, boundary case, "
                        f"or explicit denial of this claim: {rival.claim} Attack target: "
                        f"{condition}"
                    ),
                }
            )
    return targets


def _validate_authority_binding(
    binding: dict[str, object],
    expected: CorpusAuthority,
) -> None:
    if type(binding) is not dict or set(binding) != _AUTHORITY_BINDING_KEYS:
        raise RecordError("authority binding has an unexpected shape")
    if binding["status"] != AUTHORITY_BINDING_STATUS:
        raise AuthorityMismatch("authority binding is not mechanically valid")
    comparisons = {
        "document_id": expected.document_id,
        "sha256": expected.sha256,
        "byte_length": expected.byte_length,
        "physical_pdf_pages": expected.physical_pdf_pages,
    }
    for field, value in comparisons.items():
        if binding[field] != value:
            raise AuthorityMismatch(f"verified authority binding differs for {field}")
    if binding["semantic_authority"] != AUTHORITY_SEMANTIC_SCOPE:
        raise AuthorityMismatch("authority binding changes the semantic authority")
    if binding["verification_scope"] != AUTHORITY_VERIFICATION_SCOPE:
        raise AuthorityMismatch(
            "authority binding changes the non-semantic verification scope"
        )


def _build_execution_contract(
    *,
    corpus: CalibrationCorpus,
    challenge: MinimalPairChallenge,
    repo_root: Path,
) -> dict[str, object]:
    contracts = _require_bound_role_challenge(challenge)
    implementation_sha256 = implementation_file_digests(repo_root)
    identity_material: dict[str, object] = {
        "schema_version": CALIBRATION_CONTRACT_SCHEMA,
        "run_id": RUN_ID,
        "corpus_id": corpus.corpus_id,
        "corpus_sha256": corpus.corpus_sha256,
        "authority_sha256": corpus.authority.sha256,
        "challenge_contract_sha256": contracts[
            "challenge_contract_sha256"
        ],
        "fixture_contract_sha256": contracts["fixture_contract_sha256"],
        "candidate_contract_sha256": contracts["candidate_contract_sha256"],
        "naive_revision_contract_sha256": contracts[
            "naive_revision_contract_sha256"
        ],
        "evaluator_contract_sha256": contracts["evaluator_contract_sha256"],
        "implementation_file_sha256": implementation_sha256,
    }
    return {
        **identity_material,
        "run_contract_sha256": _contract_sha256(
            "creib.semantic-forge.calibration-run-identity.v1",
            identity_material,
        ),
    }


def build_calibration_report(
    corpus: CalibrationCorpus,
    authority_binding: dict[str, object],
    *,
    repo_root: Path | None = None,
) -> dict[str, object]:
    """Build the first-run report from verified inputs and finite mechanics."""

    if type(corpus) is not CalibrationCorpus:
        raise TypeError("corpus must be CalibrationCorpus")
    _require_pinned_first_run_corpus(corpus)
    _validate_authority_binding(authority_binding, corpus.authority)

    challenge = corpus.challenge(ROLE_CHALLENGE_ID)
    execution_contract = _build_execution_contract(
        corpus=corpus,
        challenge=challenge,
        repo_root=_repo_root_from_module() if repo_root is None else repo_root,
    )
    role_issue = corpus.issue(ROLE_ISSUE_ID)
    if role_issue.unknown_kind is not UnknownKind.EXTERNAL:
        raise RecordError("the role-realization issue must remain external")

    weak_evaluation = evaluate_weak_role_projection(challenge)
    erasure_evaluation = evaluate_naive_existential_erasure()

    erasure_issue = internal_erasure_issue()
    erasure_warrant = generate_research_warrant(
        erasure_issue,
        discovery_channels=corpus.discovery_channels,
    )
    if erasure_warrant is not None:
        raise RecordError("an internal erasure issue cannot generate a research warrant")

    role_warrant = generate_research_warrant(
        role_issue,
        discovery_channels=corpus.discovery_channels,
    )
    if role_warrant is None:
        raise RecordError("the external role issue must generate a research warrant")

    naive_assessment = assess_revision(
        assessment_id="SMF-ASSESS-NAIVE-ROLEGROUNDED-001",
        baseline_id=CANDIDATE_ID,
        revision_id=NAIVE_REVISION_ID,
        preserved_dimensions=(),
        justification_bases=(
            JustificationBasis.COUNTEREXAMPLE,
            JustificationBasis.DEDUCTIVE_CONSEQUENCE,
        ),
    )
    substantive_assessment = assess_revision(
        assessment_id="SMF-ASSESS-CONNECTED-ROLEGROUNDED-PROPOSAL-001",
        baseline_id=CANDIDATE_ID,
        revision_id="SMF-PROPOSED-CONNECTED-ROLEGROUNDED-001",
        unresolved_criticisms=(
            "The proposed guard has not yet excluded the role-relabel twin under "
            "executable candidate semantics.",
            "Preservation of intended inexplicit and distributed cases requires "
            "human adjudication.",
        ),
        research_issues=(role_issue,),
        justification_bases=(
            JustificationBasis.CAUSAL_DISCRIMINATION,
            JustificationBasis.COUNTEREXAMPLE,
        ),
        discovery_channels=corpus.discovery_channels,
    )
    readiness = assess_formalization_readiness(
        report_id="SMF-READINESS-ROLE-GROUNDING-001",
        candidate_id="SMF-PROPOSED-CONNECTED-ROLEGROUNDED-001",
        unresolved_semantic_roles=(
            "minimum causal realization of inexplicit roles",
        ),
        missing_positive_witnesses=(
            "tacit distributed role without an explicit token",
        ),
        missing_negative_witnesses=(
            "executed exclusion of a role-relabel twin for the selected target theory",
        ),
        ungrounded_primitives=("RoleGrounded",),
        undecided_source_forks=(
            "operational-discrimination versus network-role",
        ),
    )

    return {
        "schema_version": CALIBRATION_SCHEMA,
        "run_id": RUN_ID,
        "run_status": "RUN_COMPLETE",
        "mechanical_status": "MECHANICALLY_VALID",
        "epistemic_status": "UNRESOLVED",
        "review_status": "AWAITING_HUMAN",
        "result_scope": "NON_AUTHORITATIVE_MECHANICAL_CALIBRATION",
        "semantic_verdict": None,
        "human_disposition": None,
        "epistemic_limit": NON_INDUCTIVE_LIMIT,
        "authority_binding": authority_binding,
        "corpus_trace": {
            "corpus_id": corpus.corpus_id,
            "corpus_sha256": corpus.corpus_sha256,
            "parsed_challenge_ids": [
                item.challenge_id for item in corpus.challenges
            ],
            "parsed_issue_ids": [item.issue_id for item in corpus.issues],
            "challenge_annotation_ids": list(corpus.challenge_annotation_ids),
            "issue_annotation_ids": list(corpus.issue_annotation_ids),
            "challenge_annotation_sha256": {
                item.record_id: item.canonical_sha256
                for item in corpus.challenge_annotations
            },
            "issue_annotation_sha256": {
                item.record_id: item.canonical_sha256
                for item in corpus.issue_annotations
            },
            "selected_challenge": challenge.to_dict(),
            "selected_external_issue": role_issue.to_dict(),
        },
        "execution_contract": execution_contract,
        "fixture_evaluations": {
            "weak_typed_role_projection": weak_evaluation,
            "naive_existential_erasure": erasure_evaluation,
        },
        "research_routing": {
            "execution_boundary": "OUTSIDE_DETERMINISTIC_CORE",
            "provider_replaceable": corpus.provider_replaceable,
            "provider_output_is_oracle": corpus.provider_output_is_oracle,
            "falsifier_first": corpus.falsifier_first,
            "default_discovery_channel": corpus.discovery_channels[0],
            "internal_erasure_issue": erasure_issue.to_dict(),
            "internal_erasure_warrant": None,
            "external_role_warrant": role_warrant.to_dict(),
            "attack_search_targets": attack_search_targets(role_issue),
        },
        "hardening_assessments": {
            "naive_disconnected_revision": naive_assessment.to_dict(),
            "substantive_connected_proposal": substantive_assessment.to_dict(),
        },
        "formalization_readiness": readiness.to_dict(),
        "human_review": {
            "status": "AWAITING_HUMAN",
            "question": (
                "Which candidate, auxiliary, test, or scope criticisms remain live "
                "for the paired fixture, and what operational action, if any, "
                "should be taken next?"
            ),
            "allowed_loci": [
                "CANDIDATE",
                "AUXILIARY",
                "TEST",
                "SCOPE",
            ],
            "multiple_loci_may_coexist": True,
            "overall_status": "UNRESOLVED",
            "human_triage_record": None,
            "semantic_verdict": None,
        },
    }


def run_first_calibration(
    *,
    repo_root: Path,
    pdf_path: Path,
    corpus_path: Path,
) -> dict[str, object]:
    """Verify authority, load the seed, and produce one deterministic report."""

    corpus = load_calibration_corpus(corpus_path)
    binding = verify_authority_binding(repo_root, pdf_path, corpus.authority)
    return build_calibration_report(corpus, binding, repo_root=repo_root)


def validate_calibration_report(
    report: dict[str, object],
    *,
    repo_root: Path | None = None,
) -> None:
    """Validate a run record against its schema and executable contracts.

    This is an operational integrity check only.  In particular, exact replay
    does not turn the null semantic verdict into a positive one.
    """

    if type(report) is not dict:
        raise TypeError("report must be a dictionary")
    root = _repo_root_from_module() if repo_root is None else repo_root
    _exact_keys(report, _REPORT_KEYS, "calibration report")
    fixed_values = {
        "schema_version": CALIBRATION_SCHEMA,
        "run_id": RUN_ID,
        "run_status": "RUN_COMPLETE",
        "mechanical_status": "MECHANICALLY_VALID",
        "epistemic_status": "UNRESOLVED",
        "review_status": "AWAITING_HUMAN",
        "result_scope": "NON_AUTHORITATIVE_MECHANICAL_CALIBRATION",
        "semantic_verdict": None,
        "human_disposition": None,
        "epistemic_limit": NON_INDUCTIVE_LIMIT,
    }
    for field, expected in fixed_values.items():
        if report[field] != expected:
            raise RecordError(
                f"calibration report field {field!r} differs from its fixed contract"
            )

    # Validate the complete nested shape with a retrieval-disabled local
    # registry before applying cross-field and executable checks.
    load_local_schema_catalog(root / "forge" / "schema").validate(
        report,
        "calibration-run.schema.json",
    )

    corpus_trace = _object(report["corpus_trace"], "report.corpus_trace")
    if corpus_trace.get("corpus_id") != SEED_CORPUS_ID:
        raise RecordError("calibration report is not bound to the seed corpus ID")
    if corpus_trace.get("corpus_sha256") != PINNED_SEED_CORPUS_SHA256:
        raise RecordError("calibration report is not bound to the pinned corpus bytes")
    for ids_field, digests_field in (
        ("challenge_annotation_ids", "challenge_annotation_sha256"),
        ("issue_annotation_ids", "issue_annotation_sha256"),
    ):
        raw_ids = _array(corpus_trace.get(ids_field), f"report.corpus_trace.{ids_field}")
        identifiers = tuple(
            _string(value, f"report.corpus_trace.{ids_field}[{index}]")
            for index, value in enumerate(raw_ids)
        )
        digest_map = _object(
            corpus_trace.get(digests_field),
            f"report.corpus_trace.{digests_field}",
        )
        if set(digest_map) != set(identifiers):
            raise RecordError(
                f"report.corpus_trace.{digests_field} must cover annotation IDs exactly"
            )
        for record_id, digest in digest_map.items():
            _require_sha256(
                digest,
                f"report.corpus_trace.{digests_field}.{record_id}",
            )
    try:
        challenge = parse_minimal_pair_challenge(
            _object(
                corpus_trace.get("selected_challenge"),
                "report.corpus_trace.selected_challenge",
            )
        )
    except (TypeError, ValueError) as exc:
        raise RecordError("calibration report contains an invalid selected challenge") from exc
    contracts = _require_bound_role_challenge(challenge)

    execution = _object(
        report["execution_contract"],
        "report.execution_contract",
    )
    _exact_keys(execution, _EXECUTION_CONTRACT_KEYS, "report.execution_contract")
    expected_execution_fields: dict[str, object] = {
        "schema_version": CALIBRATION_CONTRACT_SCHEMA,
        "run_id": RUN_ID,
        "corpus_id": SEED_CORPUS_ID,
        "corpus_sha256": PINNED_SEED_CORPUS_SHA256,
        "challenge_contract_sha256": contracts[
            "challenge_contract_sha256"
        ],
        "fixture_contract_sha256": contracts["fixture_contract_sha256"],
        "candidate_contract_sha256": contracts["candidate_contract_sha256"],
        "naive_revision_contract_sha256": contracts[
            "naive_revision_contract_sha256"
        ],
        "evaluator_contract_sha256": contracts["evaluator_contract_sha256"],
        "implementation_file_sha256": implementation_file_digests(root),
    }
    authority = _object(report["authority_binding"], "report.authority_binding")
    _exact_keys(authority, _AUTHORITY_BINDING_KEYS, "report.authority_binding")
    authority_sha256 = _require_sha256(
        authority.get("sha256"),
        "report.authority_binding.sha256",
    )
    expected_execution_fields["authority_sha256"] = authority_sha256
    for field, expected in expected_execution_fields.items():
        if execution[field] != expected:
            raise RecordError(
                f"execution contract field {field!r} differs from current bound inputs"
            )
    identity_material = {
        field: execution[field]
        for field in _EXECUTION_CONTRACT_KEYS
        if field != "run_contract_sha256"
    }
    expected_run_contract_sha256 = _contract_sha256(
        "creib.semantic-forge.calibration-run-identity.v1",
        identity_material,
    )
    if execution["run_contract_sha256"] != expected_run_contract_sha256:
        raise RecordError("calibration run-contract digest does not replay")

    evaluations = _object(
        report["fixture_evaluations"],
        "report.fixture_evaluations",
    )
    if set(evaluations) != {
        "weak_typed_role_projection",
        "naive_existential_erasure",
    }:
        raise RecordError("calibration fixture evaluations have an unexpected shape")
    if evaluations["weak_typed_role_projection"] != evaluate_weak_role_projection(
        challenge
    ):
        raise RecordError("weak-role fixture evaluation does not replay")
    if evaluations["naive_existential_erasure"] != evaluate_naive_existential_erasure():
        raise RecordError("existential-erasure fixture evaluation does not replay")

    current_corpus = load_calibration_corpus(
        root / "forge" / "corpus" / "cr-1.0-seed.json"
    )
    regenerated = build_calibration_report(
        current_corpus,
        authority,
        repo_root=root,
    )
    if report != regenerated:
        raise RecordError(
            "calibration report differs from exact deterministic regeneration"
        )


def dumps_calibration_report(
    report: dict[str, object],
    *,
    repo_root: Path | None = None,
) -> str:
    """Validate and serialize a calibration report with stable JSON ordering."""

    validate_calibration_report(report, repo_root=repo_root)
    return json.dumps(
        report,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def load_calibration_report(
    path: Path,
    *,
    repo_root: Path | None = None,
) -> dict[str, object]:
    """Load one canonical run record from a single byte snapshot."""

    try:
        snapshot, raw_bytes, _digest = _strict_json_snapshot(path, "calibration run")
    except RecordError as exc:
        raise CalibrationRunError("RUN_RECORD_READ_FAILED", str(exc)) from exc
    report = _object(snapshot, "calibration run")
    canonical = (
        dumps_calibration_report(report, repo_root=repo_root).encode("utf-8") + b"\n"
    )
    if raw_bytes != canonical:
        raise CalibrationRunError(
            "RUN_RECORD_NONCANONICAL",
            "calibration run record must be canonical UTF-8 JSON followed by one newline",
        )
    return report


def replay_calibration_report(
    run_path: Path,
    *,
    repo_root: Path,
    pdf_path: Path,
    corpus_path: Path,
) -> dict[str, object]:
    """Regenerate and compare every run field against one persisted record."""

    recorded = load_calibration_report(run_path, repo_root=repo_root)
    regenerated = run_first_calibration(
        repo_root=repo_root,
        pdf_path=pdf_path,
        corpus_path=corpus_path,
    )
    if recorded != regenerated:
        recorded_sha256 = _contract_sha256(
            "creib.semantic-forge.calibration-report.v1",
            recorded,
        )
        regenerated_sha256 = _contract_sha256(
            "creib.semantic-forge.calibration-report.v1",
            regenerated,
        )
        raise CalibrationRunError(
            "RUN_RECORD_REPLAY_MISMATCH",
            "persisted calibration run differs from exact regeneration; "
            f"recorded={recorded_sha256}, regenerated={regenerated_sha256}",
        )
    return regenerated


def publish_calibration_report(
    output_path: Path,
    report: dict[str, object],
    *,
    repo_root: Path | None = None,
) -> None:
    """Atomically publish a canonical run record without replacing any path."""

    if not isinstance(output_path, Path):
        raise TypeError("output_path must be a Path")
    payload = (
        dumps_calibration_report(report, repo_root=repo_root).encode("utf-8") + b"\n"
    )
    parent = output_path.parent
    if not parent.exists():
        raise CalibrationRunError(
            "RUN_RECORD_PARENT_MISSING",
            f"run-record parent directory does not exist: {parent}",
        )
    if not parent.is_dir():
        raise CalibrationRunError(
            "RUN_RECORD_PARENT_NOT_DIRECTORY",
            f"run-record parent path is not a directory: {parent}",
        )
    if os.path.lexists(output_path):
        raise CalibrationRunError(
            "RUN_RECORD_EXISTS",
            f"refusing to overwrite existing run record: {output_path}",
        )

    file_descriptor = -1
    temporary_path: Path | None = None
    published = False
    try:
        try:
            file_descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{output_path.name}.",
                suffix=".tmp",
                dir=parent,
            )
            temporary_path = Path(temporary_name)
        except OSError as exc:
            raise CalibrationRunError(
                "RUN_RECORD_TEMP_CREATE_FAILED",
                f"cannot create same-directory run-record temporary file: {exc}",
            ) from exc

        try:
            os.fchmod(file_descriptor, 0o644)
            with os.fdopen(file_descriptor, "wb") as handle:
                file_descriptor = -1
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
        except OSError as exc:
            raise CalibrationRunError(
                "RUN_RECORD_TEMP_WRITE_FAILED",
                f"cannot durably write run-record temporary file: {exc}",
            ) from exc

        try:
            # A same-filesystem hard link publishes the complete temporary file
            # atomically and, unlike replace/rename, fails if any target exists.
            os.link(temporary_path, output_path)
            published = True
        except FileExistsError as exc:
            raise CalibrationRunError(
                "RUN_RECORD_EXISTS",
                f"refusing to overwrite existing run record: {output_path}",
            ) from exc
        except OSError as exc:
            error_code = (
                "RUN_RECORD_EXISTS"
                if exc.errno in (errno.EEXIST, errno.EISDIR)
                else "RUN_RECORD_PUBLISH_FAILED"
            )
            raise CalibrationRunError(
                error_code,
                f"cannot atomically publish run record: {exc}",
            ) from exc

        try:
            temporary_path.unlink()
            temporary_path = None
        except OSError as exc:
            raise CalibrationRunError(
                "RUN_RECORD_TEMP_CLEANUP_FAILED",
                "run record was published but its temporary link could not be "
                f"removed: {temporary_path}: {exc}",
            ) from exc
        try:
            directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
            directory_descriptor = os.open(parent, directory_flags)
            try:
                os.fsync(directory_descriptor)
            finally:
                os.close(directory_descriptor)
        except OSError as exc:
            raise CalibrationRunError(
                "RUN_RECORD_DIRECTORY_SYNC_FAILED",
                "run record was published without confirmed directory durability: "
                f"{output_path}: {exc}",
            ) from exc
    finally:
        if file_descriptor >= 0:
            try:
                os.close(file_descriptor)
            except OSError:
                pass
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
        # `published` is intentionally not used to roll back the destination:
        # no-clobber publication succeeded, and deleting it after a later
        # durability error could destroy the only complete record.
        _ = published
