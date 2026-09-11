"""The serialized asynchronous-callback task, and its reference model.

From *The Creativity Machine* and its *Evidence and Experimental Report* (11 September 2026). The
task is chosen because it is exactly decidable on a finite domain, so a reference relation can be
implemented separately from any candidate and exhaustive checking settles correctness within that
domain — the Blueprint's condition for a closed task.

A START introduces a request and supersedes the former live one. CANCEL invalidates the live
request but does not erase callbacks still awaiting delivery. A pending callback arrives once, in
any order. The required decision on arrival is to accept precisely the callback belonging to the
currently live request; accepting the current result and rejecting obsolete results are both
protected obligations.

**Where this departs from the Evidence Report, and why.** That report states two things which are
not jointly satisfiable: that the four-start reference model holds 46 reachable states and 81
decision cases, and that the constructed guard is ``active and current == incoming``. Deduping
states on ``(live, pending)`` reproduces 46 and 81 exactly — but then ``current`` is the live
ticket, ``None`` whenever nothing is live, and a bare ``current == incoming`` already answers every
case, so the conjunction is redundant. Making ``current`` a register that retains its value
through CANCEL is what makes the conjunction necessary (fifteen cases separate them) — and that
gives 61 states and 98 cases. Holding both at once requires a state set deduped on a key that
omits ``current``, under which eight merged groups contain members exposing *different* values of
``current`` to the candidate, so whether a candidate is accepted depends on which member the fixed
point happened to keep. A verifier's verdict must be a function of the state set. This module
therefore keeps the register in the state's identity and reports 61 and 98.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from creib.errors import RecordError

#: Request identities, in the order a START consumes them.
TICKETS: tuple[str, ...] = ("A", "B", "C", "D", "E", "F")

START, CANCEL, COMPLETE = "START", "CANCEL", "COMPLETE"


@dataclass(frozen=True)
class State:
    """The reference model's whole state, every field of which is part of its identity.

    ``register`` is the last request started and retains its value through CANCEL, as a hardware
    register would; ``active`` says whether that request is still live. The live request is the
    register when active and nothing otherwise. ``started`` bounds which tickets remain and is part
    of the identity too: two states that expose the same view but admit different continuations are
    not the same state.
    """

    active: bool
    register: str | None
    pending: frozenset[str]
    started: int

    @property
    def live(self) -> str | None:
        return self.register if self.active else None

    def to_dict(self) -> dict[str, Any]:
        return {
            "active": self.active,
            "register": self.register,
            "pending": sorted(self.pending),
            "started": self.started,
        }


INITIAL = State(active=False, register=None, pending=frozenset(), started=0)


def start(state: State, max_starts: int) -> State | None:
    """A new request supersedes the live one; the superseded request's callback is still owed."""

    if state.started >= max_starts:
        return None
    ticket = TICKETS[state.started]
    return State(True, ticket, state.pending | {ticket}, state.started + 1)


def cancel(state: State) -> State | None:
    """The live request is invalidated. The register keeps its value and nothing owed is erased."""

    if not state.active:
        return None
    return State(False, state.register, state.pending, state.started)


def complete(state: State, ticket: str) -> State | None:
    """One owed callback arrives. It arrives once."""

    if ticket not in state.pending:
        return None
    return State(state.active, state.register, state.pending - {ticket}, state.started)


def required(state: State, ticket: str) -> bool:
    """The reference decision: accept precisely the callback of the currently live request."""

    return state.active and ticket == state.register


def reachable(max_starts: int) -> tuple[State, ...]:
    """Every state reachable from the initial one, to a fixed point rather than by sampling."""

    if type(max_starts) is not int or not 1 <= max_starts <= len(TICKETS):
        raise RecordError(f"max_starts must be a whole number from 1 to {len(TICKETS)}")
    seen: dict[State, None] = {INITIAL: None}
    frontier = [INITIAL]
    while frontier:
        state = frontier.pop()
        successors = [start(state, max_starts), cancel(state)]
        successors.extend(complete(state, ticket) for ticket in sorted(state.pending))
        for nxt in successors:
            if nxt is not None and nxt not in seen:
                seen[nxt] = None
                frontier.append(nxt)
    return tuple(sorted(seen, key=lambda s: (s.started, s.active, s.register or "", sorted(s.pending))))


@dataclass(frozen=True)
class Case:
    """One decision the reference model requires: a state, an arriving callback, the answer."""

    state: State
    ticket: str

    @property
    def answer(self) -> bool:
        return required(self.state, self.ticket)

    def view(self, fields: tuple[str, ...]) -> dict[str, Any]:
        """What a candidate is shown. Which fields those are is the experiment's variable."""

        whole: dict[str, Any] = {
            "active": self.state.active,
            "current": self.state.register,
            "incoming": self.ticket,
        }
        missing = [name for name in fields if name not in whole]
        if missing:
            raise RecordError(f"no such exposed field: {', '.join(missing)}")
        return {name: whole[name] for name in fields}

    def to_dict(self) -> dict[str, Any]:
        return {"state": self.state.to_dict(), "ticket": self.ticket, "answer": self.answer}


def cases(max_starts: int) -> tuple[Case, ...]:
    """Every callback decision the reference model can be asked for, in the reachable set."""

    return tuple(Case(s, t) for s in reachable(max_starts) for t in sorted(s.pending))
