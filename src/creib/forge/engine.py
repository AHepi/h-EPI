"""Pure deterministic operations for research, challenge, and hardening."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, Protocol

from creib.errors import PolicyViolation
from creib.strict_json import loads_strict

from .models import (
    DefectType,
    FormalizationReadiness,
    HardeningAssessment,
    HardeningStatus,
    Issue,
    JustificationBasis,
    MinimalPairChallenge,
    NON_INDUCTIVE_LIMIT,
    PROHIBITED_JUSTIFICATION_BASES,
    PreservationDimension,
    ReadinessStatus,
    ResearchWarrant,
    UnknownKind,
    expected_hardening_status,
    parse_hardening_assessment,
    parse_formalization_readiness,
    parse_issue,
    parse_minimal_pair_challenge,
    parse_research_warrant,
)


class QuestionGenerator(Protocol):
    """Optional provider-neutral question generation boundary."""

    def generate(self, warrant: ResearchWarrant) -> tuple[str, ...]: ...


class ResearchRunner(Protocol):
    """Optional provider-neutral external research boundary."""

    def run(self, warrant: ResearchWarrant, questions: tuple[str, ...]) -> tuple[object, ...]: ...


@dataclass(frozen=True)
class _ChallengeSpec:
    intended_case: str
    lookalike_case: str
    held_fixed: str
    controlled_difference: str
    oracle: str
    falsifies_if: str


_CHALLENGE_SPECS: dict[DefectType, _ChallengeSpec] = {
    DefectType.ROLE_RELABELING: _ChallengeSpec(
        "A conjecture answers a recognized problem and a later criticism targets that conjecture.",
        "The same events are assigned conjecture and criticism roles in the opposite direction.",
        "Underlying events, contents, timing, and causal links.",
        "Only the epistemic role assignment is exchanged.",
        "The exchanged assignment must violate answer-to-problem or prior-target conditions.",
        "Both assignments satisfy the candidate model without a grounded difference.",
    ),
    DefectType.PROBLEM_TRIGGER_COLLAPSE: _ChallengeSpec(
        "A discrepancy becomes a problem through recognized conflict and value-mediated attention.",
        "The identical signal opens an episode through a content-insensitive interrupt.",
        "Signal, system, time, and downstream visible transcript.",
        "Recognized conflict and relevance are present only in the intended case.",
        "Removing recognition or relevance must change problem uptake while leaving the signal fixed.",
        "The model attributes the same problem role to the hard-coded trigger.",
    ),
    DefectType.CONJECTURE_CRITICISM_ORDER: _ChallengeSpec(
        "A criticism targets immutable conjectural content that was already available.",
        "An evaluator invents the alleged conjecture while emitting its supposed criticism.",
        "Final text, evaluator, and reported critical defect.",
        "Target content exists before criticism only in the intended case.",
        "Every criticism must resolve to an earlier conjectural target identity.",
        "Post-hoc target construction is admitted as criticism of a prior conjecture.",
    ),
    DefectType.ARBITRARY_REJECTION: _ChallengeSpec(
        "A conjecture is rejected because an articulated defect bears on its content.",
        "The same conjecture is discarded by timeout, reward, or arbitrary preference.",
        "Conjecture, rejection event, resources, and final disposition.",
        "A content-bearing defect causally explains rejection only in the intended case.",
        "Neutralizing the defect must remove defect-based credit without forcing acceptance.",
        "Arbitrary disposal receives the same criticism or error-correction attribution.",
    ),
    DefectType.REPAIR_PROVENANCE: _ChallengeSpec(
        "A successor responds to the defect exposed by criticism.",
        "The identical successor is injected independently after the criticism.",
        "Predecessor, successor content, chronology, and visible output.",
        "Only defect-relevant causal provenance differs.",
        "Varying the alleged defect must vary the credited repair or defeat its provenance claim.",
        "Independent overwrite is classified as correction through criticism.",
    ),
    DefectType.RECEIVED_CREATED_COLLAPSE: _ChallengeSpec(
        "A system receives a conjecture with external provenance and then criticizes it.",
        "The receiving system is credited with creating the same externally supplied conjecture.",
        "Conjecture content, recipient, subsequent criticism, and output.",
        "The incoming content channel and locus of creation.",
        "Severing the channel must remove local creation attribution, not local critical activity.",
        "Receipt and local creation remain indistinguishable.",
    ),
    DefectType.PLAYBACK_ZOMBIE: _ChallengeSpec(
        "The process counterfactually responds when conjecture or criticism content is changed.",
        "A fixed playback emits the identical observed transcript without responsiveness.",
        "Observed transcript and final output in the baseline run.",
        "Counterfactual causal responsiveness.",
        "Epistemic attribution must follow interventions, not transcript identity.",
        "Playback receives the same attribution as the responsive process.",
    ),
    DefectType.INDUCTIVE_WARRANT: _ChallengeSpec(
        "Repeated successful tests leave a conjecture presently unrefuted.",
        "The same successes increase truth warrant, confirmation, or probability by accumulation.",
        "Conjecture, tests, outcomes, criticisms, and content-specific relations.",
        "Only the claimed epistemic promotion from repetition differs.",
        "Duplicating accommodated successes must not promote truth status.",
        "Pass count, consensus, or confidence raises epistemic warrant.",
    ),
    DefectType.PRIVILEGED_CRITIC: _ChallengeSpec(
        "A criticism is itself fallible and may be criticized, ignored, rejected, or suspended.",
        "A critic seat or rule defeats its target solely by occupying the critic role.",
        "Target, critical utterance, and initial disposition.",
        "A premise of the criticism is false only in the lookalike.",
        "The model must permit criticism of the critic without automatically rejecting the target.",
        "Role occupancy makes criticism infallible.",
    ),
    DefectType.METRIC_TRUTH_COLLAPSE: _ChallengeSpec(
        "A metric is a fallible instrument directed at a specified defect.",
        "An equal or better metric value is definitionally treated as truth or knowledge.",
        "Metric, observed value, optimization procedure, and output.",
        "A reward-hacking case violates the problem while preserving or improving the value.",
        "The model must distinguish problem satisfaction from metric optimization.",
        "Metric value alone establishes epistemic merit.",
    ),
    DefectType.CONVERGENCE_SMUGGLING: _ChallengeSpec(
        "Inquiry may branch, stall, suspend, or fail to create an adequate conjecture.",
        "Finite repetition or asymptotic concentration is assumed to guarantee truth.",
        "Problem, available history, generator, and criticism rules.",
        "Only an admissible unresolved continuation is added.",
        "The model must admit the unresolved history unless a restricted completeness premise is explicit.",
        "Open inquiry is excluded merely because a process repeats or converges numerically.",
    ),
    DefectType.PRIMITIVE_VACUITY: _ChallengeSpec(
        "A primitive changes at least one causal, counterfactual, or inferential consequence.",
        "The primitive is empty, universal, or arbitrarily repartitioned with no consequence.",
        "All other vocabulary, realizations, and claimed results.",
        "Only the interpretation or presence of the primitive.",
        "Deletion or arbitrary substitution must break a consequence the primitive explains.",
        "The candidate survives every substitution, making the primitive ornamental.",
    ),
    DefectType.SCOPE_ESCAPE: _ChallengeSpec(
        "A counterexample falls within a scope fixed independently of the challenged claim.",
        "The counterexample is excluded by redefining genuine, relevant, or the domain after discovery.",
        "Counterexample, claim text, and all non-scope facts.",
        "Only post-hoc movement of the scope boundary.",
        "The pre-registered scope must continue to classify the counterexample.",
        "A challenged universal survives solely through scope redefinition.",
    ),
    DefectType.SUBSTRATE_OVERFIT: _ChallengeSpec(
        "Two substrate-distinct systems realize the same epistemically relevant organization.",
        "One is excluded solely because it lacks an incidental implementation detail.",
        "Epistemic roles, causal organization, histories, and content relations.",
        "Only substrate or implementation varies.",
        "Classification must be invariant under irrelevant substrate replacement.",
        "The proposed repair hardens by losing substrate-independent reach.",
    ),
}


def _unique_sorted_texts(values: Iterable[str], where: str) -> tuple[str, ...]:
    items = tuple(values)
    for index, item in enumerate(items):
        if type(item) is not str or not item.strip():
            raise ValueError(f"{where}[{index}] must be a non-empty string")
    if len(items) != len(set(items)):
        raise ValueError(f"{where} must not contain duplicates")
    return tuple(sorted(items))


def _unique_ordered_texts(values: Iterable[str], where: str) -> tuple[str, ...]:
    """Validate a priority-ordered text sequence without reordering it."""

    items = tuple(values)
    for index, item in enumerate(items):
        if type(item) is not str or not item.strip():
            raise ValueError(f"{where}[{index}] must be a non-empty string")
    if len(items) != len(set(items)):
        raise ValueError(f"{where} must not contain duplicates")
    return items


def _research_warrant_id(issue: Issue) -> str:
    """Return a bounded ID derived from the complete canonical issue record."""

    canonical = json.dumps(
        issue.to_dict(),
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"RW:{hashlib.sha256(canonical).hexdigest()}"


def _enum_tuple(
    values: Iterable[Any],
    enum_type: type,
    where: str,
) -> tuple[Any, ...]:
    parsed: list[Any] = []
    for index, value in enumerate(values):
        if type(value) is enum_type:
            item = value
        elif type(value) is str:
            try:
                item = enum_type(value)
            except ValueError as exc:
                raise ValueError(f"{where}[{index}] has an unknown value: {value!r}") from exc
        else:
            raise ValueError(f"{where}[{index}] must be {enum_type.__name__} or string")
        parsed.append(item)
    if len(parsed) != len(set(parsed)):
        raise ValueError(f"{where} must not contain duplicates")
    return tuple(sorted(parsed, key=lambda item: item.value))


def generate_research_warrant(
    issue: Issue,
    *,
    discovery_channels: Iterable[str] = ("AlphaXiv",),
) -> ResearchWarrant | None:
    """Return a warrant when the issue is structurally eligible for that route."""

    if type(issue) is not Issue:
        raise TypeError("issue must be Issue")
    if issue.unknown_kind is not UnknownKind.EXTERNAL:
        return None
    if not issue.is_decision_relevant:
        return None
    if len(issue.rivals) < 2:
        return None
    if any(not rival.falsifier_conditions for rival in issue.rivals):
        return None
    if (
        issue.expected_discriminator is None
        or not issue.admissible_source_scope
        or issue.stop_condition is None
    ):
        return None
    channels = _unique_ordered_texts(discovery_channels, "discovery_channels")
    if not channels:
        raise ValueError("discovery_channels must not be empty")
    return ResearchWarrant(
        warrant_id=_research_warrant_id(issue),
        issue_id=issue.issue_id,
        question=issue.question,
        unknown_kind=UnknownKind.EXTERNAL,
        decision=issue.decision,
        decision_relevance=issue.decision_relevance,
        rivals=issue.rivals,
        expected_discriminator=issue.expected_discriminator,
        admissible_source_scope=issue.admissible_source_scope,
        stop_condition=issue.stop_condition,
        discovery_channels=channels,
    )


def generate_challenge_template(
    defect_type: DefectType | str,
    *,
    challenge_id: str | None = None,
) -> MinimalPairChallenge:
    """Instantiate the fixed minimal-pair template for one defect family."""

    if type(defect_type) is str:
        try:
            parsed_type = DefectType(defect_type)
        except ValueError as exc:
            raise ValueError(f"unknown defect type: {defect_type!r}") from exc
    elif type(defect_type) is DefectType:
        parsed_type = defect_type
    else:
        raise TypeError("defect_type must be DefectType or string")
    spec = _CHALLENGE_SPECS[parsed_type]
    return MinimalPairChallenge(
        challenge_id=challenge_id or f"MP:{parsed_type.value}",
        defect_type=parsed_type.value,
        intended_case=spec.intended_case,
        lookalike_case=spec.lookalike_case,
        held_fixed=spec.held_fixed,
        controlled_difference=spec.controlled_difference,
        oracle=f"status=project_import_provisional; {spec.oracle}",
        falsifies_if=spec.falsifies_if,
    )


def generate_challenge_templates(
    defect_types: Iterable[DefectType | str] | None = None,
) -> tuple[MinimalPairChallenge, ...]:
    """Generate templates in canonical defect-type order."""

    values = tuple(DefectType) if defect_types is None else defect_types
    requested = _enum_tuple(
        values,
        DefectType,
        "defect_types",
    )
    return tuple(generate_challenge_template(item) for item in requested)


def assess_revision(
    *,
    assessment_id: str,
    baseline_id: str,
    revision_id: str,
    excluded_countermodels: Iterable[str] = (),
    resolved_ambiguities: Iterable[str] = (),
    preserved_dimensions: Iterable[PreservationDimension | str] = (),
    new_countermodels: Iterable[str] = (),
    lost_intended_cases: Iterable[str] = (),
    weakened_claims: Iterable[str] = (),
    collapsed_distinctions: Iterable[str] = (),
    unresolved_criticisms: Iterable[str] = (),
    research_issues: Iterable[Issue] = (),
    justification_bases: Iterable[JustificationBasis | str] = (),
    gain_witness_refs: Iterable[str] = (),
    preservation_review_refs: Iterable[str] = (),
    human_decision_refs: Iterable[str] = (),
    discovery_channels: Iterable[str] = ("AlphaXiv",),
) -> HardeningAssessment:
    """Compare revisions by independent obligations and strict witnesses.

    Passing trials are deliberately absent from this interface.  Named
    countermodels and preservation obligations matter; their frequency does
    not.
    """

    excluded = _unique_sorted_texts(excluded_countermodels, "excluded_countermodels")
    resolved = _unique_sorted_texts(resolved_ambiguities, "resolved_ambiguities")
    preserved = _enum_tuple(
        preserved_dimensions,
        PreservationDimension,
        "preserved_dimensions",
    )
    new = _unique_sorted_texts(new_countermodels, "new_countermodels")
    lost = _unique_sorted_texts(lost_intended_cases, "lost_intended_cases")
    weakened = _unique_sorted_texts(weakened_claims, "weakened_claims")
    collapsed = _unique_sorted_texts(collapsed_distinctions, "collapsed_distinctions")
    unresolved = list(_unique_sorted_texts(unresolved_criticisms, "unresolved_criticisms"))
    bases = _enum_tuple(justification_bases, JustificationBasis, "justification_bases")
    gain_refs = _unique_sorted_texts(gain_witness_refs, "gain_witness_refs")
    preservation_refs = _unique_sorted_texts(
        preservation_review_refs,
        "preservation_review_refs",
    )
    decision_refs = _unique_sorted_texts(human_decision_refs, "human_decision_refs")
    prohibited = set(bases) & PROHIBITED_JUSTIFICATION_BASES
    if prohibited:
        names = sorted(item.value for item in prohibited)
        raise PolicyViolation(
            "pass counts, consensus, and confidence cannot justify a claim; "
            f"forbidden bases={names}"
        )

    issues = tuple(research_issues)
    for index, issue in enumerate(issues):
        if type(issue) is not Issue:
            raise TypeError(f"research_issues[{index}] must be Issue")
    issue_ids = [issue.issue_id for issue in issues]
    if len(issue_ids) != len(set(issue_ids)):
        raise ValueError("research_issues must have unique issue IDs")

    channels = _unique_ordered_texts(discovery_channels, "discovery_channels")
    if not channels:
        raise ValueError("discovery_channels must not be empty")
    warrants: list[ResearchWarrant] = []
    for issue in sorted(issues, key=lambda item: item.issue_id):
        warrant = generate_research_warrant(issue, discovery_channels=channels)
        if warrant is None:
            unresolved.append(f"issue {issue.issue_id} is not eligible for external research")
        else:
            warrants.append(warrant)
    unresolved_tuple = _unique_sorted_texts(unresolved, "unresolved_criticisms")

    status = expected_hardening_status(
        excluded_countermodels=excluded,
        resolved_ambiguities=resolved,
        preserved_dimensions=preserved,
        new_countermodels=new,
        lost_intended_cases=lost,
        weakened_claims=weakened,
        collapsed_distinctions=collapsed,
        unresolved_criticisms=unresolved_tuple,
        research_warrants=tuple(warrants),
        gain_witness_refs=gain_refs,
        preservation_review_refs=preservation_refs,
        human_decision_refs=decision_refs,
        justification_bases=bases,
    )
    return HardeningAssessment(
        assessment_id=assessment_id,
        baseline_id=baseline_id,
        revision_id=revision_id,
        status=status,
        excluded_countermodels=excluded,
        resolved_ambiguities=resolved,
        preserved_dimensions=preserved,
        new_countermodels=new,
        lost_intended_cases=lost,
        weakened_claims=weakened,
        collapsed_distinctions=collapsed,
        unresolved_criticisms=unresolved_tuple,
        research_warrants=tuple(warrants),
        justification_bases=bases,
        gain_witness_refs=gain_refs,
        preservation_review_refs=preservation_refs,
        human_decision_refs=decision_refs,
    )


def assess_formalization_readiness(
    *,
    report_id: str,
    candidate_id: str,
    unresolved_semantic_roles: Iterable[str] = (),
    missing_positive_witnesses: Iterable[str] = (),
    missing_negative_witnesses: Iterable[str] = (),
    ungrounded_primitives: Iterable[str] = (),
    undecided_source_forks: Iterable[str] = (),
    review_record_refs: Iterable[str] = (),
) -> FormalizationReadiness:
    """Report current semantic blockers, failing closed pending ledger review."""

    unresolved_roles = _unique_sorted_texts(
        unresolved_semantic_roles,
        "unresolved_semantic_roles",
    )
    missing_positive = _unique_sorted_texts(
        missing_positive_witnesses,
        "missing_positive_witnesses",
    )
    missing_negative = _unique_sorted_texts(
        missing_negative_witnesses,
        "missing_negative_witnesses",
    )
    ungrounded = _unique_sorted_texts(ungrounded_primitives, "ungrounded_primitives")
    source_forks = _unique_sorted_texts(undecided_source_forks, "undecided_source_forks")
    review_refs = _unique_sorted_texts(review_record_refs, "review_record_refs")
    return FormalizationReadiness(
        report_id=report_id,
        candidate_id=candidate_id,
        status=ReadinessStatus.BLOCKED,
        unresolved_semantic_roles=unresolved_roles,
        missing_positive_witnesses=missing_positive,
        missing_negative_witnesses=missing_negative,
        ungrounded_primitives=ungrounded,
        undecided_source_forks=source_forks,
        review_record_refs=review_refs,
    )


def to_jsonable(
    record: Issue | ResearchWarrant | MinimalPairChallenge | HardeningAssessment | FormalizationReadiness,
) -> dict[str, object]:
    """Project one forge record to JSON-compatible primitive values."""

    if type(record) not in {
        Issue,
        ResearchWarrant,
        MinimalPairChallenge,
        HardeningAssessment,
        FormalizationReadiness,
    }:
        raise TypeError("record must be a semantic-forge record")
    return record.to_dict()


def dumps_record(
    record: Issue | ResearchWarrant | MinimalPairChallenge | HardeningAssessment | FormalizationReadiness,
) -> str:
    """Return a deterministic JSON representation."""

    return json.dumps(
        to_jsonable(record),
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def loads_issue(source: str) -> Issue:
    return parse_issue(loads_strict(source))


def loads_research_warrant(source: str) -> ResearchWarrant:
    return parse_research_warrant(loads_strict(source))


def loads_minimal_pair_challenge(source: str) -> MinimalPairChallenge:
    return parse_minimal_pair_challenge(loads_strict(source))


def loads_hardening_assessment(source: str) -> HardeningAssessment:
    return parse_hardening_assessment(loads_strict(source))


def loads_formalization_readiness(source: str) -> FormalizationReadiness:
    return parse_formalization_readiness(loads_strict(source))
