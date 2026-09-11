"""The architecture space, pinned by enumeration so a change to it cannot pass unnoticed."""

from __future__ import annotations

from creib.forge.mini.configspace import BLIND_SPOT

from .helpers import MiniTestCase


class ConfigSpaceTests(MiniTestCase):
    def test_the_compiler_admits_every_ordering_but_the_verdict_must_be_last(self) -> None:
        orderings = list(BLIND_SPOT.orderings())
        self.assertEqual(len(orderings), 720, "six stages in any order, the verdict pinned last")
        self.assertTrue(all(order[-1] == "verdict" for order in orderings))

    def test_the_orderings_collapse_to_twenty_four_architectures(self) -> None:
        architectures = BLIND_SPOT.architectures()
        self.assertEqual(len(architectures), 24, "distinct dataflow signatures, not 720 shapes")
        self.assertLess(len(architectures), 2 ** len(BLIND_SPOT.edges), "far below the ceiling")

    def test_exactly_one_architecture_is_fully_synchronous_and_twelve_orderings_realise_it(self) -> None:
        architectures = BLIND_SPOT.architectures()
        synchronous = [s for s in architectures if BLIND_SPOT.lag_of(s) == 0]
        self.assertEqual(len(synchronous), 1)
        example, count = architectures[synchronous[0]]
        self.assertEqual(count, 12)
        self.assertEqual(example, ("rules", "source", "cell", "propose", "execute", "criticise", "verdict"))

    def test_every_other_architecture_lags_at_least_one_edge(self) -> None:
        lags = sorted(BLIND_SPOT.lag_of(s) for s in BLIND_SPOT.architectures())
        self.assertEqual(lags[0], 0)
        self.assertEqual(lags[-1], 5, "the most lagged architecture defers five of seven edges")
        self.assertEqual(sum(1 for lag in lags if lag > 0), 23)
