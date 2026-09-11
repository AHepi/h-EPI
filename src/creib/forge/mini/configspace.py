"""The space of mini architectures a stage list can express, enumerated rather than sampled.

A mini template is not one shape. The compiler admits any ordering of stages with one exception,
so what a sequence decides is not whether a run is legal but **which cycle each stage's inputs come
from**. A consumer placed before its producer does not starve: with ``window: all`` it reads the
previous cycle, and the ordering becomes a feedback architecture with a lag rather than a broken
one. That is the thing a config mutation study is varying, and it is the thing every block in this
repository held fixed.

Three facts this module establishes by enumeration, with no model called:

* Of the 5040 orderings of seven stages, **720 compile** — every arrangement of the six
  non-verdict stages, the verdict pinned last (``MINI_VERDICT_NOT_LAST``). The compiler checks no
  dataflow at all: a stage may read a port whose producer runs after it.
* Under ``window: this_cycle`` only **12 of 720** feed every port, and the other 708 starve in
  every cycle. Under ``window: all`` **all 720** are fed from the second cycle onward, every one
  producing the same artifact count.
* Those 720 orderings collapse to **24 distinct dataflow signatures** over the port edges — one
  fully synchronous, twenty-three lagged. The synchronous one is what twelve of the orderings
  realise, and is the only architecture this repository has ever run.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Iterator, Sequence

#: One stage list's port edges: each pair is (consumer, producer).
@dataclass(frozen=True)
class Wiring:
    """Which stages there are, and which of them reads which."""

    stages: tuple[str, ...]
    last: str
    edges: tuple[tuple[str, str], ...]

    def orderings(self) -> Iterator[tuple[str, ...]]:
        """Every ordering the compiler admits: any arrangement, with ``last`` pinned last."""

        for perm in itertools.permutations(self.stages):
            yield perm + (self.last,)

    def signature(self, ordering: Sequence[str]) -> tuple[str, ...]:
        """Which edges read this cycle and which read the one before, for this ordering."""

        position = {stage: index for index, stage in enumerate(ordering)}
        return tuple(
            "same" if position[producer] < position[consumer] else "lagged"
            for consumer, producer in self.edges
        )

    def architectures(self) -> dict[tuple[str, ...], tuple[tuple[str, ...], int]]:
        """Each distinct signature, one ordering that realises it, and how many do."""

        found: dict[tuple[str, ...], tuple[tuple[str, ...], int]] = {}
        for ordering in self.orderings():
            sig = self.signature(ordering)
            example, count = found.get(sig, (ordering, 0))
            found[sig] = (example, count + 1)
        return found

    def lag_of(self, signature: Sequence[str]) -> int:
        return sum(1 for edge in signature if edge == "lagged")


#: The blind-spot wiring this repository has run: rules and source and a grid cell feed a proposer,
#: a machine executes the pair, a critic reads both, a verdict reads the executions and criticisms.
BLIND_SPOT = Wiring(
    stages=("rules", "source", "cell", "propose", "execute", "criticise"),
    last="verdict",
    edges=(
        ("propose", "rules"),
        ("propose", "cell"),
        ("execute", "propose"),
        ("criticise", "propose"),
        ("criticise", "execute"),
        ("verdict", "execute"),
        ("verdict", "criticise"),
    ),
)


# --- the semantics a theorem can be stated about ---


def delivered(lag: int, window: str, cycle: int, last_n: int | None = None) -> tuple[int, ...]:
    """Which producing cycles reach a consumer on one edge, at one cycle.

    A producer placed before its consumer in the ordering has produced through the current cycle;
    one placed after has produced only through the cycle before. The window then filters by the
    cycle coordinate the record already carries. Everything below is a consequence of these two
    sentences and of :class:`~creib.forge.mini.windows.Window`.
    """

    from .windows import Window

    admits = Window(window, last_n) if last_n is not None else Window(window)
    return tuple(k for k in range(1, cycle - lag + 1) if admits.admits(k, cycle))


#: The windows a manifest may name without a parameter.
NAMED_WINDOWS: tuple[str, ...] = ("all", "this_cycle", "previous_cycle")

#: The configuration that withholds nothing: every edge same-cycle, every window ``all``.
MAXIMAL = ("same", "all")


def is_acyclic(arcs: Sequence[tuple[str, str]], vertices: Sequence[str]) -> bool:
    """Does this orientation admit a topological order? The realisability test of Theorem 1."""

    following: dict[str, list[str]] = {vertex: [] for vertex in vertices}
    for tail, head in arcs:
        following[tail].append(head)
    colour: dict[str, int] = {}

    def visit(vertex: str) -> bool:
        colour[vertex] = 1
        for nxt in following[vertex]:
            if colour.get(nxt) == 1:
                return False
            if colour.get(nxt) is None and not visit(nxt):
                return False
        colour[vertex] = 2
        return True

    return all(colour.get(v) is not None or visit(v) for v in vertices)


def orientation_of(wiring: "Wiring", signature: Sequence[str]) -> list[tuple[str, str]]:
    """A lag signature as an orientation: producer to consumer when same, the reverse when lagged."""

    return [
        (producer, consumer) if state == "same" else (consumer, producer)
        for (consumer, producer), state in zip(wiring.edges, signature)
    ]


def behaviours(wiring: "Wiring", cycles: int, windows: Sequence[str] = NAMED_WINDOWS) -> int:
    """How many configurations of this wiring are distinguishable by what they deliver.

    Two configurations are the same behaviour when every edge delivers the same producing cycles
    at every cycle of the run. Window ``previous_cycle`` makes an edge's lag unobservable, so the
    count is strictly below the naive product of orderings and window assignments.
    """

    signatures = {wiring.signature(order) for order in wiring.orderings()}
    seen: set[tuple[tuple[tuple[int, ...], ...], ...]] = set()
    for assignment in itertools.product(windows, repeat=len(wiring.edges)):
        for signature in signatures:
            seen.add(
                tuple(
                    tuple(
                        delivered(0 if signature[i] == "same" else 1, assignment[i], t)
                        for t in range(1, cycles + 1)
                    )
                    for i in range(len(wiring.edges))
                )
            )
    return len(seen)
