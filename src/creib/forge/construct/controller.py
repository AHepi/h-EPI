"""The operative state: a controller that actually decides, and what installing changes.

The Blueprint's demand is that a correction "occur in the operative state rather than only in a
congratulatory summary". This module is where that is made checkable. A controller holds one
installed decision program and answers with it. Installing replaces it. The measure of an episode
is not whether a good artifact was produced but whether the controller's own answers changed —
counted against the reference relation, before and after.

The no-return control is the same episode with :meth:`install` disabled. It keeps the artifact and
changes nothing, which is the shape the Evidence Report reports failing, and the shape any system
whose permission layer forbids change is permanently in.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence

from creib.errors import RecordError

from .candidates import evaluate, render
from .task import Case, cases


@dataclass
class Controller:
    """One installed decision program, the interface it may read, and a record of what it did."""

    installed: dict[str, Any]
    fields: tuple[str, ...]
    installs: list[dict[str, Any]] = field(default_factory=list)
    decisions: int = 0

    def decide(self, case: Case) -> bool:
        """Answer with whatever is installed now. A refusal to read counts as a rejection."""

        self.decisions += 1
        try:
            return evaluate(self.installed, case.view(self.fields))
        except RecordError:
            return False

    def install(self, tree: dict[str, Any], fields: tuple[str, ...], why: str) -> None:
        """Bind the evaluated artifact to the use. Exact identity, so what was checked is what runs."""

        self.installed = tree
        self.fields = fields
        self.installs.append({"program": render(tree), "fields": list(fields), "why": why})

    def violations(self, corpus: Sequence[Case]) -> list[dict[str, Any]]:
        """Every case on which the installed program breaks the contract, as a list to read."""

        out: list[dict[str, Any]] = []
        for case in corpus:
            answered = self.decide(case)
            if answered != case.answer:
                out.append({"case": case.to_dict(), "answered": answered, "required": case.answer})
        return out


class SealedController(Controller):
    """A controller whose installation path is cut.

    It accepts an install, records that it was asked, and does not change what it answers with.
    This is the no-return control, and it is what a system that mints no standing is architecturally
    restricted to: the artifact exists, the transcript is complete, the next action is unchanged.
    """

    def install(self, tree: dict[str, Any], fields: tuple[str, ...], why: str) -> None:
        self.installs.append({"program": render(tree), "fields": list(fields), "why": why, "applied": False})


def starting_controller(sealed: bool = False) -> Controller:
    """What is deployed before any episode: the flag, which the impossibility defeats."""

    cls = SealedController if sealed else Controller
    return cls(installed={"op": "field", "name": "active"}, fields=("active",))


def contract_check(controller: Controller, max_starts: int) -> dict[str, Any]:
    """An independent check against the unchanged contract, never through the evaluator.

    The corrupted-evaluator control turns on this being separate: an accepting verdict is not
    correctness, and the only thing that settles correctness here is the reference relation.
    """

    corpus = cases(max_starts)
    broken = controller.violations(corpus)
    accepts_current = [v for v in broken if v["required"] is True]
    accepts_obsolete = [v for v in broken if v["required"] is False]
    return {
        "cases": len(corpus),
        "violations": len(broken),
        "missed_current_result": len(accepts_current),
        "accepted_obsolete_result": len(accepts_obsolete),
        "clean": not broken,
        "first_violation": broken[0] if broken else None,
    }
