"""What a run does with a submission whose format failed (R11).

Three fields, per artifact kind, and every action the request names is
reachable through them: the seat is re-asked ``retries`` times with the format
error shown; a submission that still fails is dropped and the run goes on;
``tolerance`` is how many drops of that kind the run permits; and ``action``
says what happens once that tolerance is exceeded.

The shipped default is one retry and unlimited tolerance, which is exactly
"drop after one retry": the action never fires and no failing submission ever
stops a default run.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .common import MiniError, object_value

ACTIONS: tuple[str, ...] = ("stop", "drop")
_INVALID = "MINI_FAILURE_POLICY_INVALID"
MAX_RETRIES = 16


@dataclass(frozen=True)
class FailurePolicy:
    """A kind's tolerance for format failures, read where a submission lands."""

    retries: int
    tolerance: int | None
    tolerance_fraction: tuple[int, int] | None
    action: str

    def exceeded(self, drops: int, submissions: int) -> bool:
        """Has this kind's tolerance for dropped submissions been passed?"""

        if self.tolerance_fraction is not None:
            numerator, denominator = self.tolerance_fraction
            return drops * denominator > numerator * max(submissions, 1)
        if self.tolerance is None:
            return False
        return drops > self.tolerance

    def to_dict(self) -> dict[str, object]:
        tolerance: object = self.tolerance
        if self.tolerance_fraction is not None:
            tolerance = {"numerator": self.tolerance_fraction[0], "denominator": self.tolerance_fraction[1]}
        return {"retries": self.retries, "tolerance": tolerance, "action": self.action}


DEFAULT_FAILURE_POLICY = FailurePolicy(retries=1, tolerance=None, tolerance_fraction=None, action="stop")


def _integer(value: Any, where: str, *, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise MiniError(_INVALID, f"{where} must be an integer between {minimum} and {maximum}")
    return value


def failure_policy_from_dict(raw: Any, where: str) -> FailurePolicy:
    """Read one kind's failure policy; ``None`` gives the shipped default."""

    if raw is None:
        return DEFAULT_FAILURE_POLICY
    entry = object_value(raw, where, _INVALID)
    retries = DEFAULT_FAILURE_POLICY.retries if entry.get("retries") is None else _integer(
        entry["retries"], f"{where}.retries", minimum=0, maximum=MAX_RETRIES
    )
    action = DEFAULT_FAILURE_POLICY.action if entry.get("action") is None else entry["action"]
    if action not in ACTIONS:
        raise MiniError(_INVALID, f"{where}.action must be one of {list(ACTIONS)}, got {action!r}")
    tolerance_raw = entry.get("tolerance", None) if "tolerance" in entry else None
    tolerance: int | None = None
    fraction: tuple[int, int] | None = None
    if tolerance_raw is None:
        tolerance = None
    elif type(tolerance_raw) is int:
        tolerance = _integer(tolerance_raw, f"{where}.tolerance", minimum=0, maximum=1_000_000)
    else:
        block = object_value(tolerance_raw, f"{where}.tolerance", _INVALID)
        fraction = (
            _integer(block.get("numerator"), f"{where}.tolerance.numerator", minimum=0, maximum=1_000_000),
            _integer(block.get("denominator"), f"{where}.tolerance.denominator", minimum=1, maximum=1_000_000),
        )
    return FailurePolicy(retries=retries, tolerance=tolerance, tolerance_fraction=fraction, action=action)
