"""Candidate decision programs, their verification, and the representation extension.

A candidate is a syntax tree over the fields a declared interface exposes. It is evaluated, never
executed as source: a proposal is data, and a proposer that could run arbitrary code would be a
different experiment with a different permission argument.

The experiment's variable is which fields the interface exposes. Stage one exposes ``active``
alone, and *every* function of that one bit fails — not because the deployed program is poor but
because two situations with the same exposed view require opposite answers. That is the witness
Theorem T1 describes, and no larger proposer downstream of the same lost information can repair
it. Stage two admits a typed comparison of two ticket registers, and the failure becomes
repairable.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Any, Iterator, Mapping, Sequence

from creib.errors import RecordError

from .task import Case, cases

#: What stage one exposes, and what stage two adds.
VIEW_ONE: tuple[str, ...] = ("active",)
VIEW_TWO: tuple[str, ...] = ("active", "current", "incoming")

TRUE, FALSE, FIELD, EQUAL, NOT, AND, OR = "true", "false", "field", "equal", "not", "and", "or"


def evaluate(tree: Any, view: Mapping[str, Any]) -> bool:
    """A syntax tree against one exposed view. Anything unrecognised is refused, never guessed."""

    if type(tree) is not dict or "op" not in tree:
        raise RecordError(f"not a candidate tree: {tree!r}")
    op = tree["op"]
    if op == TRUE:
        return True
    if op == FALSE:
        return False
    if op == FIELD:
        name = tree.get("name")
        if name not in view:
            raise RecordError(f"the candidate reads {name!r}, which this interface does not expose")
        return bool(view[name])
    if op == EQUAL:
        left, right = tree.get("left"), tree.get("right")
        for name in (left, right):
            if name not in view:
                raise RecordError(f"the candidate reads {name!r}, which this interface does not expose")
        return view[left] == view[right]
    if op == NOT:
        return not evaluate(tree["of"], view)
    if op == AND:
        return evaluate(tree["left"], view) and evaluate(tree["right"], view)
    if op == OR:
        return evaluate(tree["left"], view) or evaluate(tree["right"], view)
    raise RecordError(f"no such operator: {op!r}")


def render(tree: Any) -> str:
    """The tree as the source a person reads. Rendering is for the record, never for execution."""

    op = tree["op"]
    if op in (TRUE, FALSE):
        return op.capitalize()
    if op == FIELD:
        return str(tree["name"])
    if op == EQUAL:
        return f"{tree['left']} == {tree['right']}"
    if op == NOT:
        return f"not ({render(tree['of'])})"
    if op in (AND, OR):
        return f"{render(tree['left'])} {op} {render(tree['right'])}"
    raise RecordError(f"no such operator: {op!r}")


def stage_one_language() -> tuple[dict[str, Any], ...]:
    """The four Boolean functions of one flag. All of them, so failure is of the class not a guess."""

    flag: dict[str, Any] = {"op": FIELD, "name": "active"}
    return ({"op": TRUE}, {"op": FALSE}, flag, {"op": NOT, "of": flag})


def stage_two_language() -> tuple[dict[str, Any], ...]:
    """The extension: the same flag, and a typed comparison of the two ticket registers.

    Enumerated smallest first, so the installed program is the simplest the language admits that
    survives every covered case, and not whichever the proposer happened to like.
    """

    flag: dict[str, Any] = {"op": FIELD, "name": "active"}
    same: dict[str, Any] = {"op": EQUAL, "left": "current", "right": "incoming"}
    atoms = (flag, same)
    out: list[dict[str, Any]] = [{"op": TRUE}, {"op": FALSE}]
    out.extend(atoms)
    out.extend({"op": NOT, "of": atom} for atom in atoms)
    for op in (AND, OR):
        for left, right in itertools.product(atoms, repeat=2):
            out.append({"op": op, "left": left, "right": right})
    return tuple(out)


@dataclass(frozen=True)
class Verdict:
    """What exhaustive checking found. A failure names the case, so it can be read and argued with."""

    accepted: bool
    checked: int
    first_failure: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"accepted": self.accepted, "checked": self.checked, "first_failure": self.first_failure}


def verify(tree: Any, fields: tuple[str, ...], max_starts: int, corpus: Sequence[Case] | None = None) -> Verdict:
    """Exhaustive checking against the reference relation on the covered finite domain.

    The verifier never sees a candidate's provenance and never sees the reference answer through
    anything but the reference model. Exhaustive on a decidable closed task settles exact
    correctness within that domain and says nothing about any larger one.
    """

    corpus = corpus if corpus is not None else cases(max_starts)
    for index, case in enumerate(corpus):
        try:
            answered = evaluate(tree, case.view(fields))
        except RecordError as error:
            return Verdict(False, index, {"case": case.to_dict(), "refused": str(error)})
        if answered != case.answer:
            return Verdict(False, index + 1, {"case": case.to_dict(), "answered": answered, "required": case.answer})
    return Verdict(True, len(corpus))


def shared_view_counterexample(fields: tuple[str, ...], max_starts: int) -> tuple[Case, Case] | None:
    """Two cases with the same exposed view and opposite required answers, if the interface has one.

    This is the witness that defeats *every* function of the view rather than one candidate, and it
    is what licenses asking for a changed representation instead of another guess.
    """

    by_view: dict[tuple[tuple[str, Any], ...], Case] = {}
    for case in cases(max_starts):
        key = tuple(sorted(case.view(fields).items()))
        seen = by_view.get(key)
        if seen is not None and seen.answer != case.answer:
            return (seen, case)
        by_view.setdefault(key, case)
    return None
