"""When a run stops, decided by the host and never by a seat (R23).

Three things can end a run, and a seat's prose is none of them: a cycle cap, a
budget cap, and a registered stop condition. A stop condition is a function of
SIGNALS, declared and handed a view of exactly what it declared, for the same
reason an attention policy is: nothing that decides whether the run continues
may read the record directly, and no artifact's content may end a run by saying
so.

A stop condition is not attention. It decides whether there is another cycle;
attention decides what runs inside one.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .attention import SignalView
from .common import MiniError

STOP_NEVER = "mini.stop.never"
STOP_NO_ARTIFACT_LAST_CYCLE = "mini.stop.no-artifact-last-cycle"
SIGNAL_ARTIFACTS_IN_LAST_CYCLE = "mini.signal.artifacts-in-last-cycle"
_SIGNATURE: tuple[str, ...] = ("signals", "cycle")


@dataclass(frozen=True)
class StopCondition:
    """One registered machine stop condition."""

    condition_id: str
    reads_signals: tuple[str, ...]
    description: str
    decide: Callable[[SignalView, int], str | None]


_REGISTRY: dict[str, StopCondition] = {}


def register_stop_condition(condition: StopCondition) -> StopCondition:
    """Register one condition, refusing a function that could take the record."""

    if condition.condition_id in _REGISTRY:
        raise MiniError(
            "MINI_STOP_CONDITION_DUPLICATE", f"stop condition {condition.condition_id!r} is already registered"
        )
    parameters = tuple(inspect.signature(condition.decide).parameters)
    if parameters != _SIGNATURE:
        raise MiniError(
            "MINI_STOP_CONDITION_SIGNATURE",
            f"stop condition {condition.condition_id!r} takes {list(parameters)}; it may take only {list(_SIGNATURE)}",
        )
    _REGISTRY[condition.condition_id] = condition
    return condition


def resolve_stop_condition(condition_id: str) -> StopCondition:
    try:
        return _REGISTRY[condition_id]
    except KeyError as error:
        raise MiniError(
            "MINI_STOP_CONDITION_UNKNOWN",
            f"no stop condition {condition_id!r} is registered; known: {sorted(_REGISTRY)}",
        ) from error


def registered_stop_conditions() -> tuple[StopCondition, ...]:
    return tuple(_REGISTRY[name] for name in sorted(_REGISTRY))


def should_stop(condition: StopCondition, signals: Mapping[str, Any], cycle: int) -> str | None:
    """Ask one condition whether the run stops before this cycle."""

    view = SignalView(signals, condition.reads_signals, condition.condition_id)
    return condition.decide(view, cycle)


def _never(signals: SignalView, cycle: int) -> str | None:
    return None


def _no_artifact_last_cycle(signals: SignalView, cycle: int) -> str | None:
    if cycle <= 1:
        return None
    produced = signals[SIGNAL_ARTIFACTS_IN_LAST_CYCLE]
    if int(produced.get(str(cycle - 1), 0) if isinstance(produced, dict) else produced) == 0:
        return "no artifact was produced in the cycle before this one"
    return None


NEVER = register_stop_condition(
    StopCondition(STOP_NEVER, (), "Never stop of its own accord. The default.", _never)
)

NO_ARTIFACT_LAST_CYCLE = register_stop_condition(
    StopCondition(
        STOP_NO_ARTIFACT_LAST_CYCLE,
        (SIGNAL_ARTIFACTS_IN_LAST_CYCLE,),
        "Stop when a whole cycle produced nothing.",
        _no_artifact_last_cycle,
    )
)
