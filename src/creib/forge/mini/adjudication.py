"""An attack relation for mini, and a status computed from it rather than stored.

CREATIVITY-ARMS-1 measured every loop arm flat, and the reason is structural rather than
statistical. Mini has stages, ports and commitments, but no way for a criticism to *land*: it
produces prose that the next stage is shown. DeepReason's harness spec names the failure surface
exactly -- criticism ritualizes, "leaves commitments unevaluated, never reinstates, never attacks a
test" -- and the sentence that explains the nulls is its remark that grounded semantics is "exactly
as skeptical as its attack supply". Mini's attack supply was zero.

This is the smallest thing that changes that, and it is deliberately much less than the spec:

- a criticism's commitment names **a target** and **a ground**, so it carries a warrant rather than
  an opinion;
- a machine seat resolves the target against the record and refuses a name that resolves to nothing,
  which is the referential-integrity check that stops a criticism attacking a thing it invented;
- status is **computed** from the attack relation and never stored -- an artifact with at least one
  unattacked attacker is refuted, and an attacker that is itself attacked stops refuting, so
  reinstatement falls out rather than being a rule.

A criticism is not the only thing that can attack. The machine mints an edge of its own from an
execution to the reading it ran, whenever the run shows the reading's claim did not hold -- the
check behaved as the rule requires, or the claim could not be run at all. That edge is what makes
the next ground worth having: ``test-is-unsound`` attacks the EXECUTION, and an execution that is
itself refuted stops refuting the reading, so a reading the executor wrongly refused comes back.
That is the validity node in its smallest form, and it is the criticism this session most deserved
to hear and had nowhere to put: the executor refused a true conjecture on an arity bound and the
record said only that the conjecture was unrunnable.

What it is still not: artifacts here are typed and dispatch is by port, where the spec is untyped
and dispatches on interface; and a commitment carries no eval and no budget, so "attack surface"
stays a metaphor rather than a count. Both are named in ``docs/mini/PIPELINE_MATH.md`` and
``docs/mini/ERRATA.md`` rather than quietly omitted.
"""

from __future__ import annotations

import json
from typing import Any, Mapping

from .blindspot import CRITICISM_KIND_PREFIX, PAIR_EXECUTION_PREFIX
from .common import MiniError
from .machines import MachineContext, MachineSeat, register_machine_seat

ADJUDICATION_KIND = "mini.adjudication.v1"

#: The grounds a criticism may stand on. Closed, because an open one cannot be counted -- but with
#: an escape road, because DeepReason's structured-output note measures the same model fabricating
#: at 0-2% in prose and 100% under a required field with no way to say "I cannot tell".
GROUNDS: tuple[str, ...] = (
    "reading-misrenders-conjecture",
    "conjecture-misreads-rule",
    "rule-and-code-diverge",
    "test-is-unsound",
    "cannot-tell",
)

#: The ground whose target is an EXECUTION rather than a conjecture or a reading: the run itself is
#: being called unsound. It is admitted like any other ground and needs no rule of its own, because
#: the execution is already an attacker in the relation and refuting an attacker already reinstates
#: what it attacked.
TEST_UNSOUND = "test-is-unsound"

#: Grounds the MACHINE mints, from what an execution returned. They are not available to a critic:
#: a criticism carrying one of these names a ground it did not establish, and it does not land.
MACHINE_GROUNDS: tuple[str, ...] = (
    "execution-contradicts-claim",
    "execution-could-not-run-the-claim",
)

#: An execution outcome that says the claim was never put to the test. It refutes the reading that
#: made it -- a claim the machine could not run has not survived anything -- and it is exactly the
#: edge ``test-is-unsound`` exists to attack.
UNRUN: frozenset[str] = frozenset({"unreadable", "unrunnable"})

#: A ground that asserts nothing about the target mints no attack edge. Saying you cannot tell is
#: an honest answer, and an honest answer is not a refutation.
NO_ATTACK: frozenset[str] = frozenset({"cannot-tell"})

ACCEPTED, REFUTED = "accepted", "refuted"


def _claims(context: MachineContext) -> list[tuple[str, Mapping[str, Any]]]:
    """Every criticism in the record so far, with its commitment parsed, oldest first."""

    out: list[tuple[str, Mapping[str, Any]]] = []
    for key in context.state.artifact_order:
        record = context.state.artifacts[key]
        if not str(record["kind_id"]).startswith(CRITICISM_KIND_PREFIX):
            continue
        try:
            parsed = json.loads(context.commitments(record))
        except (ValueError, TypeError):
            parsed = {}
        if isinstance(parsed, dict):
            out.append((str(record["artifact_id"]), parsed))
    return out


def _resolve(context: MachineContext, named: str) -> str | None:
    """The one artifact whose id begins with ``named``, or None when that is not exactly one."""

    if not named:
        return None
    hits = [key for key in context.state.artifact_order if str(key).startswith(named)]
    return str(hits[0]) if len(hits) == 1 else None


def attacks_of(context: MachineContext) -> list[dict[str, Any]]:
    """The attack relation this run has accumulated, each edge saying whether it resolved."""

    edges: list[dict[str, Any]] = []
    for attacker, claim in _claims(context):
        named = str(claim.get("attacks", ""))
        ground = str(claim.get("ground", ""))
        entry: dict[str, Any] = {"attacker": attacker[:16], "names": named[:16], "ground": ground}
        if ground in MACHINE_GROUNDS:
            entry.update({"landed": False, "why": "that ground is the machine's own and a criticism may not claim it"})
        elif ground not in GROUNDS:
            entry.update({"landed": False, "why": f"ground must be one of {list(GROUNDS)}"})
        elif ground in NO_ATTACK:
            entry.update({"landed": False, "why": "the ground asserts nothing about the target"})
        else:
            target = _resolve(context, named)
            if target is None:
                entry.update({"landed": False, "why": "names no artifact of this run, or more than one"})
            else:
                entry.update({"landed": True, "target": target[:16], "why": claim.get("why", "")})
        edges.append(entry)
    return _evidence_edges(context) + edges


def _evidence_edges(context: MachineContext) -> list[dict[str, Any]]:
    """What the executions themselves attack: the reading whose claim the run did not bear out.

    A claim the check answered exactly as the rule requires is a claim of a divergence that is not
    there, and a claim the machine could not run at all was never put to the test. Either way the
    reading does not stand on that row, and saying so is the machine's business rather than a
    critic's. The rows that DO stand -- the collapse the rule forbids, and the separation the rule
    forbids -- mint nothing: an absence of attack is not an endorsement.

    These edges come FIRST in the relation, before any criticism, because the order a reader sees
    them in should be the order they were established in: what the machine found, then what anyone
    said about it.
    """

    edges: list[dict[str, Any]] = []
    for key in context.state.artifact_order:
        record = context.state.artifacts[key]
        if not str(record["kind_id"]).startswith(PAIR_EXECUTION_PREFIX):
            continue
        try:
            rows = json.loads(context.commitments(record)).get("executions", [])
        except (ValueError, TypeError, AttributeError):
            continue
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            target = _resolve(context, str(row.get("proposal", "")))
            if target is None:
                continue
            executed = str(row.get("executed", ""))
            if executed in UNRUN:
                ground, why = MACHINE_GROUNDS[1], str(row.get("detail", ""))[:200]
            elif row.get("as_expected") is True:
                ground = MACHINE_GROUNDS[0]
                why = (f"the check answered {executed} and the reading expected {row.get('expect')}: "
                       "the rule and the code do not part company on this pair")
            else:
                continue
            edges.append({"attacker": str(record["artifact_id"])[:16], "names": str(row.get("proposal", ""))[:16],
                          "ground": ground, "landed": True, "target": target[:16], "why": why})
    return edges


def status_from(edges: list[dict[str, Any]], everything: list[str]) -> dict[str, str]:
    """Status computed from the relation: refuted iff some attacker of it is not itself refuted.

    Recomputed simultaneously to a fixed point rather than marked incrementally. The difference is
    reinstatement: an attacker that a later criticism refutes stops refuting its own target, and the
    target must go back to accepted. Marking a target refuted and never unmarking it -- which is
    what the first version of this function did -- makes refutation absorbing, which is the one
    thing a fallibilist status computation may not be.

    Attacks here point from later artifacts to earlier ones, so the relation is acyclic and the
    iteration converges; the bound is kept anyway and a relation that does not settle within it is
    refused rather than reported.
    """

    landed = [e for e in edges if e.get("landed")]
    by_target: dict[str, list[str]] = {}
    for edge in landed:
        by_target.setdefault(str(edge["target"]), []).append(str(edge["attacker"]))
    label = {artifact: ACCEPTED for artifact in everything}
    for attacker in (a for edge in landed for a in (str(edge["attacker"]),)):
        label.setdefault(attacker, ACCEPTED)
    for target in by_target:
        label.setdefault(target, ACCEPTED)
    for _ in range(len(label) + 2):
        nxt = {
            artifact: (REFUTED if any(label.get(a, ACCEPTED) != REFUTED for a in by_target.get(artifact, ()))
                       else ACCEPTED)
            for artifact in label
        }
        if nxt == label:
            return label
        label = nxt
    raise MiniError("MINI_ADJUDICATION_UNSETTLED",
                    "the attack relation did not settle; it is expected to be acyclic")


def _adjudicate(context: MachineContext) -> str:
    """Resolve every criticism's target, compute status, and say what landed and what did not."""

    edges = attacks_of(context)
    everything = [str(key)[:16] for key in context.state.artifact_order]
    label = status_from(edges, everything)
    refuted = sorted(artifact for artifact, value in label.items() if value == REFUTED)
    lines = [
        f"{e['attacker']} -> {e.get('target', e['names']) or '(unnamed)'} on {e['ground'] or '(no ground)'}: "
        f"{'landed' if e.get('landed') else 'did not land, ' + str(e.get('why'))}"
        for e in edges
    ]
    # Counted apart, because they are different measurements: how much the machine established on
    # its own, and how much a critic added to it. Adding them would let a block's "attacks landed"
    # rise because more claims were unrunnable, which is the machinery working less, not more.
    criticism = [e for e in edges if str(e.get("ground")) not in MACHINE_GROUNDS]
    evidence = [e for e in edges if str(e.get("ground")) in MACHINE_GROUNDS]
    return json.dumps(
        {
            "body": "Attacks resolved against the record.\n" + ("\n".join(lines) or "(no criticism carried a target)"),
            "commitments": json.dumps(
                {"edges": edges, "refuted": refuted,
                 "attacks_landed": sum(1 for e in criticism if e.get("landed")),
                 "criticisms": len(criticism),
                 "evidence_edges": sum(1 for e in evidence if e.get("landed"))},
                sort_keys=True,
            ),
        },
        ensure_ascii=False,
    )


ADJUDICATION_SEAT = register_machine_seat(
    MachineSeat(ADJUDICATION_KIND, "Resolves each criticism's named target and computes status from the attack relation.", _adjudicate)
)
