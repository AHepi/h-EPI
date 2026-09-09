"""Attention: the plug, not the brain (R18, R20, R21).

An attention policy is a registered function that decides which stage runs
next. It is handed two things and nothing else: a view of the signals it
declared it reads, and the stages still to run. There is no parameter through
which the record could arrive, and registration refuses a function whose
signature would take one — that is what makes attention a decision of the
machine rather than of the operator, and what keeps a policy from reading round
the signal interface.

Two policies ship. ``mini.attention.off`` is the default and returns nothing at
all, so the declared order runs exactly as written. The other prefers, of the
stages still to run, the one whose kind has the most unanswered criticisms
about it; it reads a count keyed by kind id and knows no kind's name, so a kind
invented after it was written is visible to it.

This module imports nothing that touches the record. That is checked.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, Callable, Iterator, Mapping

from .common import MiniError

ATTENTION_OFF = "mini.attention.off"
ATTENTION_MOST_UNANSWERED = "mini.attention.most-unanswered-criticisms"
SIGNAL_UNANSWERED_BY_KIND = "mini.signal.unanswered-criticisms-by-kind"
_SIGNATURE: tuple[str, ...] = ("signals", "stages")


@dataclass(frozen=True)
class PendingStage:
    """One stage still to run, as an attention policy sees it."""

    stage_id: str
    kind_id: str


class SignalView(Mapping[str, Any]):
    """A read-only view of exactly the signals a policy declared.

    Asking for anything else is a typed refusal, not a missing key: a policy
    that reaches beyond what it declared stops the run rather than quietly
    reading nothing.
    """

    def __init__(self, values: Mapping[str, Any], declared: tuple[str, ...], policy_id: str) -> None:
        self._declared = tuple(declared)
        self._policy_id = policy_id
        self._values = {name: values[name] for name in self._declared if name in values}
        self.read: list[str] = []

    def __getitem__(self, key: str) -> Any:
        if key not in self._declared:
            raise MiniError(
                "MINI_ATTENTION_UNDECLARED_SIGNAL",
                f"attention policy {self._policy_id!r} asked for the signal {key!r}, which it does not declare",
            )
        self.read.append(key)
        return self._values.get(key, {})

    def __iter__(self) -> Iterator[str]:
        return iter(self._declared)

    def __len__(self) -> int:
        return len(self._declared)


@dataclass(frozen=True)
class AttentionPolicy:
    """One registered attention policy."""

    policy_id: str
    reads_signals: tuple[str, ...]
    description: str
    choose: Callable[[SignalView, tuple[PendingStage, ...]], str | None]


_REGISTRY: dict[str, AttentionPolicy] = {}


def register_attention_policy(policy: AttentionPolicy) -> AttentionPolicy:
    """Register one policy, refusing a function that could be handed a record."""

    if policy.policy_id in _REGISTRY:
        raise MiniError("MINI_ATTENTION_POLICY_DUPLICATE", f"attention policy {policy.policy_id!r} is already registered")
    parameters = tuple(inspect.signature(policy.choose).parameters)
    if parameters != _SIGNATURE:
        raise MiniError(
            "MINI_ATTENTION_SIGNATURE",
            f"attention policy {policy.policy_id!r} takes {list(parameters)}; it may take only {list(_SIGNATURE)}",
        )
    _REGISTRY[policy.policy_id] = policy
    return policy


def resolve_attention_policy(policy_id: str) -> AttentionPolicy:
    try:
        return _REGISTRY[policy_id]
    except KeyError as error:
        raise MiniError(
            "MINI_ATTENTION_POLICY_UNKNOWN",
            f"no attention policy {policy_id!r} is registered; known: {sorted(_REGISTRY)}",
        ) from error


def registered_attention_policies() -> tuple[AttentionPolicy, ...]:
    return tuple(_REGISTRY[name] for name in sorted(_REGISTRY))


def choose_next(
    policy: AttentionPolicy,
    signals: Mapping[str, Any],
    stages: tuple[PendingStage, ...],
) -> str | None:
    """Ask one policy for the next stage. ``None`` means follow the declared order."""

    view = SignalView(signals, policy.reads_signals, policy.policy_id)
    chosen = policy.choose(view, stages)
    if chosen is None:
        return None
    if chosen not in {stage.stage_id for stage in stages}:
        raise MiniError(
            "MINI_ATTENTION_STAGE_UNKNOWN",
            f"attention policy {policy.policy_id!r} chose {chosen!r}, which is not a stage still to run",
        )
    return chosen


def _off(signals: SignalView, stages: tuple[PendingStage, ...]) -> str | None:
    return None


def _most_unanswered(signals: SignalView, stages: tuple[PendingStage, ...]) -> str | None:
    counts = signals[SIGNAL_UNANSWERED_BY_KIND]
    best: str | None = None
    best_count = 0
    for stage in stages:
        count = int(counts.get(stage.kind_id, 0))
        if count > best_count:
            best, best_count = stage.stage_id, count
    return best


OFF_POLICY = register_attention_policy(
    AttentionPolicy(
        policy_id=ATTENTION_OFF,
        reads_signals=(),
        description="Follow the declared order exactly. The default.",
        choose=_off,
    )
)

MOST_UNANSWERED_POLICY = register_attention_policy(
    AttentionPolicy(
        policy_id=ATTENTION_MOST_UNANSWERED,
        reads_signals=(SIGNAL_UNANSWERED_BY_KIND,),
        description="Prefer the stage whose kind has the most unanswered criticisms about it.",
        choose=_most_unanswered,
    )
)
