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
    MACHINE_GROUNDS,
    NO_ATTACK,
    REFUTED,
    TEST_UNSOUND,
    attacks_of,
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

    def test_a_test_may_be_attacked_and_the_machine_grounds_are_not_a_critic_s_to_claim(self) -> None:
        self.assertIn(TEST_UNSOUND, GROUNDS)
        self.assertEqual(set(GROUNDS) & set(MACHINE_GROUNDS), set())


class _State:
    def __init__(self, artifacts: dict) -> None:
        self.artifacts = artifacts
        self.artifact_order = list(artifacts)


class _Context:
    """The two things ``attacks_of`` reads: the record in order, and a commitment as text."""

    def __init__(self, artifacts: dict) -> None:
        self.state = _State(artifacts)

    def commitments(self, record) -> str:
        return str(record["commitments"])


def _execution(artifact_id: str, rows: list[dict]) -> dict:
    import json as _json

    return {"artifact_id": artifact_id, "kind_id": "mini.pair-execution.open.v1",
            "commitments": _json.dumps({"executions": rows})}


def _criticism(artifact_id: str, attacks: str, ground: str) -> dict:
    import json as _json

    return {"artifact_id": artifact_id, "kind_id": "mini.criticism.v1",
            "commitments": _json.dumps({"attacks": attacks, "ground": ground, "why": "because"})}


def _reading(artifact_id: str) -> dict:
    return {"artifact_id": artifact_id, "kind_id": "mini.pair-proposal.reading.v1", "commitments": "{}"}


class ValidityNodeTests(unittest.TestCase):
    """The execution attacks the reading it ran, and a criticism may attack the execution.

    Answers ERRATA C5. Before this, the one criticism CREATIVITY-ARMS-1 most deserved to hear --
    that the executor refused a true conjecture on an arity bound -- had nowhere to go: an
    unrunnable row simply sat in the record and no ground named it.
    """

    def _edges(self, artifacts: dict) -> list[dict]:
        return attacks_of(_Context(artifacts))

    def test_a_claim_the_check_bore_out_is_refuted_by_its_own_execution(self) -> None:
        edges = self._edges({
            "r000000000000000": _reading("r000000000000000"),
            "e000000000000000": _execution("e000000000000000", [
                {"proposal": "r000000000000000", "executed": "moved", "expect": "moves", "as_expected": True}]),
        })
        self.assertEqual([e["ground"] for e in edges], ["execution-contradicts-claim"])
        self.assertTrue(edges[0]["landed"])
        self.assertEqual(status_from(edges, ["r000000000000000", "e000000000000000"])["r000000000000000"], REFUTED)

    def test_a_T1_witness_mints_no_edge_at_all(self) -> None:
        """An absence of attack is not an endorsement, and it must not be an attack either."""

        edges = self._edges({
            "r000000000000000": _reading("r000000000000000"),
            "e000000000000000": _execution("e000000000000000", [
                {"proposal": "r000000000000000", "executed": "unchanged", "expect": "moves", "as_expected": False}]),
        })
        self.assertEqual(edges, [])

    def test_a_claim_the_machine_could_not_run_is_refuted_and_says_why(self) -> None:
        edges = self._edges({
            "r000000000000000": _reading("r000000000000000"),
            "e000000000000000": _execution("e000000000000000", [
                {"proposal": "r000000000000000", "executed": "unrunnable",
                 "detail": "takes 2 required arguments"}]),
        })
        self.assertEqual(edges[0]["ground"], "execution-could-not-run-the-claim")
        self.assertIn("2 required arguments", edges[0]["why"])

    def test_attacking_the_execution_as_unsound_reinstates_the_reading(self) -> None:
        """The point of the ground: an executor that refused a true claim can itself be refused."""

        artifacts = {
            "r000000000000000": _reading("r000000000000000"),
            "e000000000000000": _execution("e000000000000000", [
                {"proposal": "r000000000000000", "executed": "unrunnable", "detail": "arity"}]),
            "c000000000000000": _criticism("c000000000000000", "e000000000000000", "test-is-unsound"),
        }
        edges = self._edges(artifacts)
        label = status_from(edges, list(artifacts))
        self.assertEqual(label["e000000000000000"], REFUTED)
        self.assertEqual(label["r000000000000000"], ACCEPTED)

    def test_without_the_ground_the_same_criticism_leaves_the_reading_refuted(self) -> None:
        """The boundary point: it is the ground that does the work, not the criticism existing."""

        artifacts = {
            "r000000000000000": _reading("r000000000000000"),
            "e000000000000000": _execution("e000000000000000", [
                {"proposal": "r000000000000000", "executed": "unrunnable", "detail": "arity"}]),
            "c000000000000000": _criticism("c000000000000000", "e000000000000000", "cannot-tell"),
        }
        label = status_from(self._edges(artifacts), list(artifacts))
        self.assertEqual(label["r000000000000000"], REFUTED)

    def test_a_criticism_may_not_claim_a_ground_the_machine_mints(self) -> None:
        artifacts = {
            "r000000000000000": _reading("r000000000000000"),
            "c000000000000000": _criticism("c000000000000000", "r000000000000000",
                                            "execution-contradicts-claim"),
        }
        edges = self._edges(artifacts)
        self.assertFalse(edges[0]["landed"])
        self.assertIn("machine's own", edges[0]["why"])

    def test_a_row_naming_no_artifact_of_this_run_mints_nothing(self) -> None:
        edges = self._edges({
            "e000000000000000": _execution("e000000000000000", [
                {"proposal": "ffffffffffffffff", "executed": "moved", "expect": "moves", "as_expected": True}]),
        })
        self.assertEqual(edges, [])

    def test_the_machine_edges_come_before_the_criticisms(self) -> None:
        artifacts = {
            "r000000000000000": _reading("r000000000000000"),
            "e000000000000000": _execution("e000000000000000", [
                {"proposal": "r000000000000000", "executed": "moved", "expect": "moves", "as_expected": True}]),
            "c000000000000000": _criticism("c000000000000000", "r000000000000000", "rule-and-code-diverge"),
        }
        edges = self._edges(artifacts)
        self.assertEqual([e["attacker"] for e in edges], ["e000000000000000", "c000000000000000"])
