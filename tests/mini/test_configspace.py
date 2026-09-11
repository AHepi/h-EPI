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


class TheoremTests(MiniTestCase):
    """The propositions of docs/mini/ARCHITECTURE_SPACE.md, each checked by enumeration."""

    def test_t1_every_realisable_signature_is_an_acyclic_orientation(self) -> None:
        from creib.forge.mini.configspace import is_acyclic, orientation_of

        vertices = sorted({v for edge in BLIND_SPOT.edges for v in edge})
        signatures = {BLIND_SPOT.signature(order) for order in BLIND_SPOT.orderings()}
        self.assertTrue(all(is_acyclic(orientation_of(BLIND_SPOT, s), vertices) for s in signatures))

    def test_t1_the_count_agrees_with_stanleys_theorem(self) -> None:
        """|chi_G(-1)| for two pendants on a triangle is |(-1)(-2)^3(-3)| = 24."""

        self.assertEqual(len(BLIND_SPOT.architectures()), abs(-1 * (-2) ** 3 * (-3)))

    def test_t2_every_delivered_set_is_a_suffix_interval_or_empty(self) -> None:
        from creib.forge.mini.configspace import NAMED_WINDOWS, delivered

        for cycle in range(1, 6):
            for lag in (0, 1):
                for window in NAMED_WINDOWS:
                    got = delivered(lag, window, cycle)
                    with self.subTest(cycle=cycle, lag=lag, window=window):
                        if got:
                            self.assertEqual(got, tuple(range(got[0], got[-1] + 1)), "an interval")
                            self.assertIn(got[-1], (cycle, cycle - 1), "ending at t or t-1")

    def test_t3_the_maximal_configuration_dominates_every_other_on_every_edge(self) -> None:
        from creib.forge.mini.configspace import MAXIMAL, NAMED_WINDOWS, delivered

        for cycle in range(1, 6):
            top = set(delivered(0, MAXIMAL[1], cycle))
            for lag in (0, 1):
                for window in NAMED_WINDOWS:
                    with self.subTest(cycle=cycle, lag=lag, window=window):
                        self.assertLessEqual(set(delivered(lag, window, cycle)), top)

    def test_t4_previous_cycle_makes_an_edges_lag_unobservable(self) -> None:
        from creib.forge.mini.configspace import delivered

        for cycle in range(1, 6):
            self.assertEqual(delivered(0, "previous_cycle", cycle), delivered(1, "previous_cycle", cycle))

    def test_t5_the_space_saturates_at_three_cycles(self) -> None:
        from creib.forge.mini.configspace import behaviours

        sizes = [behaviours(BLIND_SPOT, t) for t in (1, 2, 3, 4)]
        self.assertEqual(sizes, [128, 8352, 24525, 24525])
        self.assertLess(sizes[0], sizes[1], "one cycle cannot tell the architectures apart")
        self.assertEqual(sizes[2], sizes[3], "and a fourth cycle adds nothing")

    def test_t6_a_one_cycle_run_distinguishes_only_two_states_per_edge(self) -> None:
        from creib.forge.mini.configspace import NAMED_WINDOWS, delivered

        reachable = {delivered(lag, w, 1) for lag in (0, 1) for w in NAMED_WINDOWS}
        self.assertEqual(reachable, {(), (1,)}, "shown the producer's artifact, or shown nothing")
