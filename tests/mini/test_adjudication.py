"""An attack relation, and a status computed from it.

CREATIVITY-ARMS-1 measured every loop arm flat because mini had no way for a criticism to land: it
produced prose the next stage was shown. These tests pin the smallest machinery that changes that --
a criticism naming a target and a ground, a target resolved against the record, and a status that is
recomputed rather than marked.
"""

from __future__ import annotations

import unittest

from creib.forge.mini.adjudication import (
    ACCEPTED,
    GROUNDS,
    NO_ATTACK,
    REFUTED,
    status_from,
)
from creib.forge.mini.common import MiniError


def _edge(attacker: str, target: str, landed: bool = True) -> dict:
    return {"attacker": attacker, "target": target, "ground": "rule-and-code-diverge", "landed": landed}


class StatusTests(unittest.TestCase):
    def test_an_unattacked_attacker_refutes_its_target(self) -> None:
        self.assertEqual(status_from([_edge("c1", "x1")], ["x1", "c1"]),
                         {"x1": REFUTED, "c1": ACCEPTED})

    def test_refuting_the_attacker_reinstates_the_target(self) -> None:
        """The property the first version of this function did not have: refutation is not absorbing."""

        edges = [_edge("c1", "x1"), _edge("c2", "c1")]
        self.assertEqual(status_from(edges, ["x1", "c1", "c2"]),
                         {"x1": ACCEPTED, "c1": REFUTED, "c2": ACCEPTED})

    def test_the_alternation_continues_down_a_chain(self) -> None:
        edges = [_edge("c1", "x1"), _edge("c2", "c1"), _edge("c3", "c2")]
        self.assertEqual(status_from(edges, ["x1", "c1", "c2", "c3"]),
                         {"x1": REFUTED, "c1": ACCEPTED, "c2": REFUTED, "c3": ACCEPTED})

    def test_an_edge_that_did_not_land_changes_nothing(self) -> None:
        self.assertEqual(status_from([_edge("c1", "x1", landed=False)], ["x1", "c1"]),
                         {"x1": ACCEPTED, "c1": ACCEPTED})

    def test_two_attackers_and_one_refuted_still_leaves_the_target_refuted(self) -> None:
        edges = [_edge("c1", "x1"), _edge("c2", "x1"), _edge("c3", "c1")]
        self.assertEqual(status_from(edges, ["x1", "c1", "c2", "c3"])["x1"], REFUTED)

    def test_a_relation_that_does_not_settle_is_refused_rather_than_reported(self) -> None:
        """Attacks are expected to point backwards in time; a cycle is a defect, not a verdict."""

        with self.assertRaises(MiniError) as caught:
            status_from([_edge("a", "b"), _edge("b", "a")], ["a", "b"])
        self.assertIn("MINI_ADJUDICATION_UNSETTLED", str(caught.exception))


class GroundTests(unittest.TestCase):
    def test_the_escape_road_exists_and_mints_no_attack(self) -> None:
        """DeepReason measures a required closed field with no escape fabricating at 100%."""

        self.assertIn("cannot-tell", GROUNDS)
        self.assertEqual(NO_ATTACK, frozenset({"cannot-tell"}))
        self.assertTrue(NO_ATTACK.issubset(set(GROUNDS)))
