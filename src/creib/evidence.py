"""Four-valued evidence resolution: absence is never negative evidence."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class Availability(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


class ReviewStatus(str, Enum):
    ACCEPTED = "accepted"
    UNREVIEWED = "unreviewed"
    CONTESTED = "contested"


class Polarity(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    UNKNOWN = "unknown"


class Outcome(str, Enum):
    SUPPORTED = "supported"
    REFUTED = "refuted"
    BLOCKED = "blocked"
    ERROR = "error"


@dataclass(frozen=True)
class Evidence:
    availability: Availability
    review_status: ReviewStatus
    polarity: Polarity
    scope: str
    evidence_id: str

    def __post_init__(self) -> None:
        if not self.scope or not self.evidence_id:
            raise ValueError("scope and evidence_id must be non-empty")


@dataclass(frozen=True)
class Resolution:
    outcome: Outcome
    reason: str

    def __bool__(self) -> bool:
        raise TypeError("evidence resolutions are four-valued; inspect .outcome explicitly")


def resolve_atom(items: Iterable[Evidence], required_scope: str) -> Resolution:
    candidates = list(items)
    accepted: set[Polarity] = set()
    blocked_reasons: list[str] = []
    for item in candidates:
        if item.scope != required_scope:
            blocked_reasons.append(f"{item.evidence_id}: scope mismatch")
            continue
        if item.availability is not Availability.AVAILABLE:
            blocked_reasons.append(f"{item.evidence_id}: unavailable")
            continue
        if item.review_status is not ReviewStatus.ACCEPTED:
            blocked_reasons.append(f"{item.evidence_id}: {item.review_status.value}")
            continue
        if item.polarity is Polarity.UNKNOWN:
            blocked_reasons.append(f"{item.evidence_id}: unknown polarity")
            continue
        accepted.add(item.polarity)

    if accepted == {Polarity.POSITIVE, Polarity.NEGATIVE}:
        return Resolution(Outcome.ERROR, "contradictory accepted polarities")
    if accepted == {Polarity.POSITIVE}:
        return Resolution(Outcome.SUPPORTED, "accepted positive evidence")
    if accepted == {Polarity.NEGATIVE}:
        return Resolution(Outcome.REFUTED, "accepted explicit negative evidence")
    reason = "; ".join(blocked_reasons) if blocked_reasons else "no evidence"
    return Resolution(Outcome.BLOCKED, reason)


def resolve_th3b_witness(
    ccp_result: Iterable[Evidence],
    retained: Iterable[Evidence],
    k_e: Iterable[Evidence],
    required_scope: str,
) -> Resolution:
    """Resolve the pilot witness CCPResult ∧ Retained ∧ ¬K_E."""
    ccp = resolve_atom(ccp_result, required_scope)
    ret = resolve_atom(retained, required_scope)
    knowledge = resolve_atom(k_e, required_scope)

    for label, result in (("CCPResult", ccp), ("Retained", ret), ("K_E", knowledge)):
        if result.outcome is Outcome.ERROR:
            return Resolution(Outcome.ERROR, f"{label}: {result.reason}")

    if ccp.outcome is not Outcome.SUPPORTED:
        return Resolution(Outcome.BLOCKED, f"CCPResult not established: {ccp.reason}")
    if ret.outcome is not Outcome.SUPPORTED:
        return Resolution(Outcome.BLOCKED, f"Retained not established: {ret.reason}")
    if knowledge.outcome is Outcome.BLOCKED:
        return Resolution(Outcome.BLOCKED, f"K_E is unknown: {knowledge.reason}")
    if knowledge.outcome is Outcome.REFUTED:
        return Resolution(Outcome.SUPPORTED, "explicit accepted negative K_E supplies the witness")
    return Resolution(Outcome.REFUTED, "accepted positive K_E defeats the witness")
