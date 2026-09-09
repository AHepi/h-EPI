"""Signals: named quantities computed from the record, added by registration (R19).

A signal declares a name, a unit, and what it means; a function computes it from
state. Adding one is a registration, and nothing that consumes signals is
edited — an attention policy sees a new signal because it declares that it
reads it, never because a consumer learned about a subsystem.

Every shipped signal is keyed by an id the record already carries (a kind id, an
artifact id), so a kind nobody had invented when a signal was written still
appears in that signal's result.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .common import MiniError, identifier
from .evidence import CITATION_VERIFIED
from .log import MiniState

SIGNAL_ARTIFACTS_BY_KIND = "mini.signal.artifacts-by-kind"
SIGNAL_CITATIONS_VERIFIED = "mini.signal.citations-verified-by-artifact"
SIGNAL_UNANSWERED_BY_KIND = "mini.signal.unanswered-criticisms-by-kind"
SIGNAL_TOKENS_BY_KIND = "mini.signal.tokens-by-kind"
SIGNAL_CYCLE_COUNT = "mini.signal.cycle-count"


@dataclass(frozen=True)
class SignalDecl:
    """What a signal is: a name, a unit, and what it counts."""

    signal_id: str
    unit: str
    description: str


@dataclass(frozen=True)
class RegisteredSignal:
    declaration: SignalDecl
    compute: Callable[[MiniState], Any]


_REGISTRY: dict[str, RegisteredSignal] = {}


def register_signal(declaration: SignalDecl, compute: Callable[[MiniState], Any]) -> RegisteredSignal:
    identifier(declaration.signal_id, "signal_id", "MINI_SIGNAL_UNKNOWN")
    if declaration.signal_id in _REGISTRY:
        raise MiniError("MINI_SIGNAL_DUPLICATE", f"signal {declaration.signal_id!r} is already registered")
    registered = RegisteredSignal(declaration=declaration, compute=compute)
    _REGISTRY[declaration.signal_id] = registered
    return registered


def registered_signals() -> tuple[SignalDecl, ...]:
    return tuple(_REGISTRY[name].declaration for name in sorted(_REGISTRY))


def compute_signals(state: MiniState, signal_ids: tuple[str, ...]) -> dict[str, Any]:
    """Compute exactly the named signals."""

    values: dict[str, Any] = {}
    for name in signal_ids:
        try:
            registered = _REGISTRY[name]
        except KeyError as error:
            raise MiniError("MINI_SIGNAL_UNKNOWN", f"no signal {name!r} is registered; known: {sorted(_REGISTRY)}") from error
        values[name] = registered.compute(state)
    return values


def _artifacts_by_kind(state: MiniState) -> dict[str, int]:
    return dict(state.submissions_by_kind)


def _citations_verified(state: MiniState) -> dict[str, int]:
    return {
        artifact_id: sum(1 for item in record["citations"] if item.get("code") == CITATION_VERIFIED)
        for artifact_id, record in state.artifacts.items()
    }


def _unanswered_by_kind(state: MiniState) -> dict[str, int]:
    """Count, per kind, the artifacts about one of its artifacts that nothing answers.

    No kind is named here. An artifact that points at another through ``about``
    is a criticism of it for this purpose, and an artifact named in some other
    artifact's ``answers`` has been answered.
    """

    answered: set[str] = set()
    for record in state.artifacts.values():
        answered.update(record["answers"])
    counts: dict[str, int] = {}
    for artifact_id, record in state.artifacts.items():
        if artifact_id in answered:
            continue
        for target_id in record["about"]:
            target = state.artifacts.get(target_id)
            if target is None:
                continue
            key = str(target["kind_id"])
            counts[key] = counts.get(key, 0) + 1
    return counts


def _tokens_by_kind(state: MiniState) -> dict[str, int]:
    return dict(state.tokens_by_kind)


def _cycle_count(state: MiniState) -> int:
    """How many times the run has come back round to the stage it began with."""

    if not state.stages_entered:
        return 0
    first = state.stages_entered[0]
    return sum(1 for stage_id in state.stages_entered if stage_id == first)


SHIPPED_SIGNALS: Mapping[str, str] = {
    SIGNAL_ARTIFACTS_BY_KIND: "artifacts",
    SIGNAL_CITATIONS_VERIFIED: "citations",
    SIGNAL_UNANSWERED_BY_KIND: "criticisms",
    SIGNAL_TOKENS_BY_KIND: "tokens",
    SIGNAL_CYCLE_COUNT: "cycles",
}

register_signal(
    SignalDecl(SIGNAL_ARTIFACTS_BY_KIND, "artifacts", "How many artifacts of each kind the run has produced."),
    _artifacts_by_kind,
)
register_signal(
    SignalDecl(SIGNAL_CITATIONS_VERIFIED, "citations", "How many of each artifact's citations were verified."),
    _citations_verified,
)
register_signal(
    SignalDecl(SIGNAL_UNANSWERED_BY_KIND, "criticisms", "How many unanswered criticisms stand against each kind's artifacts."),
    _unanswered_by_kind,
)
register_signal(
    SignalDecl(SIGNAL_TOKENS_BY_KIND, "tokens", "How many reply tokens each kind has spent."),
    _tokens_by_kind,
)
register_signal(
    SignalDecl(SIGNAL_CYCLE_COUNT, "cycles", "How many times the run has returned to the stage it began with."),
    _cycle_count,
)
