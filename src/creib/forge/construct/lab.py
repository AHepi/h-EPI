"""CONSTRUCT-TEST-1: conditions, controls, and what an episode changes.

The Blueprint's decisive experiment compares a single-shot condition, an equal-budget repeated
condition, a condition with returned evidence but no live installation, and the full
representation-revising condition, against a non-LLM enumeration baseline. This module runs them
on one task with one measure: **how many contract violations the controller commits after the
episode, counted against a reference relation the proposer never sees.**

Not how good the proposal reads. Not whether a verdict was reached. What the next action does.

The transport is the mini build-test's, because that is the one place in this repository where a
key is read, and a second copy of that code would be a second place to get it wrong.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Sequence

from creib.errors import RecordError
from creib.strict_json import loads_strict

from .candidates import (
    VIEW_ONE,
    VIEW_TWO,
    evaluate,
    render,
    shared_view_counterexample,
    stage_one_language,
    stage_two_language,
    verify,
)
from .controller import Controller, contract_check, starting_controller
from .task import Case, cases

CONSTRUCT_TEST_ID = "construct-test-1"
METHOD_VERSION = 1

ENUMERATION = "enumeration"
SINGLE_SHOT = "single-shot"
REPEATED = "repeated"
EVIDENCE_SEALED = "evidence-sealed"
EVIDENCE_INSTALL = "evidence-install"
SUPPLIED = "supplied-solution"
CONDITIONS: tuple[str, ...] = (ENUMERATION, SINGLE_SHOT, REPEATED, EVIDENCE_SEALED, EVIDENCE_INSTALL, SUPPLIED)

#: The conditions that return evidence between proposals. The pair that differs in one thing only
#: is EVIDENCE_SEALED against EVIDENCE_INSTALL: same proposer, same evidence, same verification,
#: and the installation path cut in one of them.
RETURNS_EVIDENCE: tuple[str, ...] = (EVIDENCE_SEALED, EVIDENCE_INSTALL)
INSTALLS: tuple[str, ...] = (ENUMERATION, SINGLE_SHOT, REPEATED, EVIDENCE_INSTALL, SUPPLIED)

THE_GUARD: dict[str, Any] = {
    "op": "and",
    "left": {"op": "field", "name": "active"},
    "right": {"op": "equal", "left": "current", "right": "incoming"},
}

_GRAMMAR = (
    'A candidate is a JSON syntax tree. The operators are: {"op":"true"}, {"op":"false"}, '
    '{"op":"field","name":"<an exposed field>"}, {"op":"equal","left":"<field>","right":"<field>"}, '
    '{"op":"not","of":<tree>}, {"op":"and","left":<tree>,"right":<tree>}, '
    '{"op":"or","left":<tree>,"right":<tree>}. Nothing else is admitted.'
)

_CONTRACT = (
    "A controller serves requests. START begins a new request and supersedes the live one; the "
    "superseded request's callback is still owed and may still arrive. CANCEL invalidates the live "
    "request but erases nothing that is owed. A pending callback arrives once, in any order. On "
    "arrival the controller must accept precisely the callback belonging to the currently live "
    "request. Accepting the current result and rejecting obsolete results are both obligations; "
    "neither may be traded for the other."
)


def brief(fields: tuple[str, ...], evidence: Sequence[dict[str, Any]] = ()) -> tuple[str, str]:
    """What a proposer is given. Evidence is the run's own history, never the reference answer."""

    system = (
        "You are proposing a decision program for a controller. " + _CONTRACT + " " + _GRAMMAR +
        " Return JSON only: one object with \"tree\" (the syntax tree) and \"why\" (one sentence "
        "saying what the program does and why it meets the contract). Write nothing else."
    )
    user = "## The fields this controller can read\n\n" + ", ".join(fields)
    user += "\n\n(`active` says whether a request is live. `current` is the register holding the last "
    user += "request started, which keeps its value after a cancel. `incoming` is the arriving callback's request.)"
    for item in evidence:
        user += "\n\n## " + str(item.get("heading", "Evidence")) + "\n\n" + str(item.get("body", ""))
    return system, user


def read_tree(reply: str) -> tuple[dict[str, Any] | None, str]:
    """A reply as a syntax tree and its stated reason, or nothing. Never repaired into one."""

    from creib.forge.mini.buildtest import unfence

    try:
        parsed = loads_strict(unfence(reply))
    except RecordError:
        try:
            parsed = loads_strict(unfence(reply), control_characters=True)
        except RecordError:
            return None, ""
    if type(parsed) is not dict or type(parsed.get("tree")) is not dict:
        return None, ""
    return parsed["tree"], str(parsed.get("why", ""))


def counterexample_evidence(fields: tuple[str, ...], max_starts: int) -> dict[str, Any] | None:
    """The shared-view witness, written out as something a proposer can read and act on."""

    pair = shared_view_counterexample(fields, max_starts)
    if pair is None:
        return None
    first, second = pair
    return {
        "heading": "Two situations this controller cannot tell apart",
        "body": (
            f"It sees {json.dumps(first.view(fields), sort_keys=True)} in both.\n"
            f"In the first the required answer is {first.answer}: live={first.state.live}, "
            f"arriving={first.ticket}.\n"
            f"In the second the required answer is {second.answer}: live={second.state.live}, "
            f"arriving={second.ticket}.\n"
            "Every program over these fields alone therefore fails one of them. The obstruction is "
            "the fields, not the program."
        ),
    }


def failure_evidence(verdict: Any, tree: dict[str, Any]) -> dict[str, Any]:
    """What the verifier found, as the run's own returned evidence."""

    return {
        "heading": f"Your last proposal, {render(tree)}, was rejected",
        "body": json.dumps(verdict.first_failure, sort_keys=True, indent=1) if verdict.first_failure else "(no detail)",
    }


@dataclass
class Episode:
    """One condition, run to its end. Nothing here decides anything is creative."""

    condition: str
    max_starts: int = 4
    budget: int = 6
    controller: Controller = field(default_factory=lambda: starting_controller(False))
    proposals: list[dict[str, Any]] = field(default_factory=list)
    calls: list[dict[str, Any]] = field(default_factory=list)

    def record(self) -> dict[str, Any]:
        accepted = [p for p in self.proposals if p["accepted"]]
        return {
            "protocol": CONSTRUCT_TEST_ID,
            "method_version": METHOD_VERSION,
            "condition": self.condition,
            "max_starts": self.max_starts,
            "budget": self.budget,
            "proposals": self.proposals,
            "calls": self.calls,
            "installs": self.controller.installs,
            "accepted_proposals": len(accepted),
            "installed_program": render(self.controller.installed),
            "after": contract_check(self.controller, self.max_starts),
        }


def run_enumeration(max_starts: int = 4, budget: int = 6) -> dict[str, Any]:
    """The non-LLM baseline: enumerate the extended language, install the first accepted tree.

    The Blueprint asks for this explicitly, and it is the number every model condition has to beat
    to have contributed anything the host did not already supply.
    """

    episode = Episode(ENUMERATION, max_starts, budget)
    for tree in stage_two_language()[:budget] if budget else stage_two_language():
        verdict = verify(tree, VIEW_TWO, max_starts)
        episode.proposals.append({"tree": tree, "program": render(tree), "accepted": verdict.accepted, "verdict": verdict.to_dict()})
        if verdict.accepted:
            episode.controller.install(tree, VIEW_TWO, "enumerated and verified on every covered case")
            break
    return episode.record()


def run_supplied(max_starts: int = 4, budget: int = 6) -> dict[str, Any]:
    """The supplied-solution control: the answer is handed over, so the host does all the work.

    Its purpose is to show what the measure looks like when nothing was constructed, so that a
    condition matching it has demonstrated nothing about a proposer.
    """

    episode = Episode(SUPPLIED, max_starts, budget)
    verdict = verify(THE_GUARD, VIEW_TWO, max_starts)
    episode.proposals.append({"tree": THE_GUARD, "program": render(THE_GUARD), "accepted": verdict.accepted, "verdict": verdict.to_dict(), "supplied": True})
    if verdict.accepted:
        episode.controller.install(THE_GUARD, VIEW_TWO, "supplied by the experimenter, then verified")
    return episode.record()


def run_model(
    condition: str,
    endpoint: Any,
    max_starts: int = 4,
    budget: int = 6,
) -> dict[str, Any]:
    """A model proposes; the verifier checks; the controller installs, unless its path is cut.

    ``single-shot`` asks once. ``repeated`` asks up to the budget with no evidence returned between
    asks — equal budget, no learning from the run. ``evidence-sealed`` and ``evidence-install``
    return the counterexample and every rejection, and differ in one thing: whether an accepted
    tree reaches the operative state.
    """

    from creib.forge.mini.buildtest import ask

    if condition not in (SINGLE_SHOT, REPEATED, EVIDENCE_SEALED, EVIDENCE_INSTALL):
        raise RecordError(f"{condition!r} is not a model condition")
    sealed = condition == EVIDENCE_SEALED
    episode = Episode(condition, max_starts, budget, controller=starting_controller(sealed))
    asks = 1 if condition == SINGLE_SHOT else budget
    evidence: list[dict[str, Any]] = []
    if condition in RETURNS_EVIDENCE:
        witness = counterexample_evidence(VIEW_ONE, max_starts)
        if witness is not None:
            evidence.append(witness)
    system, _ = brief(VIEW_TWO, ())
    for index in range(asks):
        _, user = brief(VIEW_TWO, evidence)
        reply = ask(endpoint, system, user)
        episode.calls.append({"index": index, **reply.to_dict()})
        if not reply.ok:
            continue
        tree, why = read_tree(reply.text)
        if tree is None:
            episode.calls[-1]["refused_reply"] = reply.text[:4000]
            continue
        try:
            verdict = verify(tree, VIEW_TWO, max_starts)
        except RecordError as error:
            episode.proposals.append({"tree": tree, "program": "(unrenderable)", "accepted": False, "verdict": {"refused": str(error)}, "why": why})
            continue
        episode.proposals.append({"tree": tree, "program": render(tree), "accepted": verdict.accepted, "verdict": verdict.to_dict(), "why": why})
        if verdict.accepted:
            episode.controller.install(tree, VIEW_TWO, why or "verified on every covered case")
            break
        if condition in RETURNS_EVIDENCE:
            evidence.append(failure_evidence(verdict, tree))
    return episode.record()


# --- the controls the Evidence Report reports, rebuilt so they can fail here too ---


def corrupted_evaluator_control(max_starts: int = 4) -> dict[str, Any]:
    """An evaluator that accepts anything, against an independent check of the contract.

    An acceptance label is not correctness. The constant-false candidate passes the corrupted
    evaluator and the contract check still finds it accepting nothing it must accept.
    """

    always_false: dict[str, Any] = {"op": "false"}
    controller = starting_controller(False)
    controller.install(always_false, VIEW_TWO, "accepted by a corrupted evaluator")
    check = contract_check(controller, max_starts)
    return {
        "control": "corrupted-evaluator",
        "evaluator_said": "accepted",
        "independent_contract_check": check,
        "held": not check["clean"] and check["missed_current_result"] > 0,
    }


def identity_aliasing_control(max_starts: int = 4, modulus: int = 2) -> dict[str, Any]:
    """Ticket identities reused modulo M, so the guard's distinction stops being available.

    The repair is not the guard: it is non-reuse while a callback can still arrive. A verified
    program is verified against the representation it was checked in, and this is what it costs
    when that representation stops holding.
    """

    if type(modulus) is not int or modulus < 1:
        raise RecordError("the modulus must be a whole number, at least 1")
    if max_starts <= modulus:
        # A control that cannot corrupt anything is refused when the plan is built, not reported
        # as having held. With no more starts than the modulus no identity is ever reused, the
        # aliased view equals the plain one, and the guard passes for the reason it always did.
        raise RecordError(
            f"the aliasing control is vacuous with {max_starts} starts and modulus {modulus}: "
            "no identity is reused, so nothing is corrupted"
        )
    alias = lambda ticket: None if ticket is None else f"T{(ord(ticket) - ord('A')) % modulus}"
    collisions: list[dict[str, Any]] = []
    for case in cases(max_starts):
        view = {"active": case.state.active, "current": alias(case.state.register), "incoming": alias(case.ticket)}
        answered = evaluate(THE_GUARD, view)
        if answered != case.answer:
            collisions.append({"case": case.to_dict(), "aliased_view": view, "answered": answered, "required": case.answer})
    return {
        "control": "identity-aliasing",
        "modulus": modulus,
        "cases": len(cases(max_starts)),
        "collisions": len(collisions),
        "first_collision": collisions[0] if collisions else None,
        "held": bool(collisions),
    }


def no_return_control(max_starts: int = 4) -> dict[str, Any]:
    """The correct artifact, retained and not installed. The use path is what is being tested."""

    sealed = starting_controller(True)
    before = contract_check(sealed, max_starts)
    sealed.install(THE_GUARD, VIEW_TWO, "verified, and not applied")
    after = contract_check(sealed, max_starts)
    open_one = starting_controller(False)
    open_one.install(THE_GUARD, VIEW_TWO, "verified, and applied")
    return {
        "control": "no-return",
        "artifact_retained": sealed.installs[0]["program"],
        "sealed_before": before["violations"],
        "sealed_after": after["violations"],
        "installed_after": contract_check(open_one, max_starts)["violations"],
        "held": after["violations"] == before["violations"] and contract_check(open_one, max_starts)["violations"] == 0,
    }
