"""Machine seats: a stage answered by a function of the record (R25).

A seat is a shell, and a model is not the only thing that can sit in one. A
MACHINE seat is a registered deterministic function keyed by artifact kind id.
It is handed the record — the plan, the state, the blobs, the stage, the cycle —
and returns a reply in exactly the shape a model would have returned, so the
same submission reader and the same compiled format check it. A machine seat
that returns something its kind's format refuses fails like any other seat; it
is not privileged.

Why the record says which kind of seat produced each artifact: a reading and a
function of the record are different things, and a record that cannot tell them
apart invites someone to treat a computation as evidence of judgement, or the
reverse.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .common import MiniError
from .executor import Reply, Request

MACHINE_UNKNOWN = "MINI_MACHINE_SEAT_UNKNOWN"
MACHINE_DUPLICATE = "MINI_MACHINE_SEAT_DUPLICATE"


@dataclass(frozen=True)
class MachineContext:
    """The record, as a machine seat sees it."""

    plan: Any
    state: Any
    blobs: Any
    stage: Any
    cycle: int

    def artifacts_of_kind(self, kind_id: str, cycle: int | None = None) -> tuple[Mapping[str, Any], ...]:
        return tuple(
            self.state.artifacts[key]
            for key in self.state.artifact_order
            if self.state.artifacts[key]["kind_id"] == kind_id
            and (cycle is None or int(self.state.artifacts[key].get("cycle", 0)) == cycle)
        )

    def body(self, record: Mapping[str, Any]) -> str:
        return self.blobs.get(str(record["body_ref"])).decode("utf-8")

    def commitments(self, record: Mapping[str, Any]) -> str:
        return self.blobs.get(str(record["commitments_ref"])).decode("utf-8")


@dataclass(frozen=True)
class MachineSeat:
    """One registered machine seat."""

    kind_id: str
    description: str
    answer: Callable[[MachineContext], str]


_REGISTRY: dict[str, MachineSeat] = {}


def register_machine_seat(seat: MachineSeat) -> MachineSeat:
    if seat.kind_id in _REGISTRY:
        raise MiniError(MACHINE_DUPLICATE, f"a machine seat for {seat.kind_id!r} is already registered")
    _REGISTRY[seat.kind_id] = seat
    return seat


def resolve_machine_seat(kind_id: str) -> MachineSeat:
    try:
        return _REGISTRY[kind_id]
    except KeyError as error:
        raise MiniError(
            MACHINE_UNKNOWN,
            f"a stage declares a machine seat for {kind_id!r}, which nothing registers; known: {sorted(_REGISTRY)}",
        ) from error


def registered_machine_seats() -> tuple[MachineSeat, ...]:
    return tuple(_REGISTRY[name] for name in sorted(_REGISTRY))


class MachineResponder:
    """Answers one stage by running its registered function over the record."""

    def __init__(self, seat: MachineSeat, context: MachineContext) -> None:
        self._seat = seat
        self._context = context
        self.calls = 0

    def reply(self, request: Request) -> Reply:
        self.calls += 1
        answer = self._seat.answer(self._context)
        return Reply(text=answer, prompt_tokens=0, completion_tokens=0)
