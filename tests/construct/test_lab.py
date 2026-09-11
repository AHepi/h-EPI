"""CONSTRUCT-TEST-1: the conditions, the controls, and the one thing the measure is about.

The measure is not whether a good artifact was produced. It is how many contract violations the
controller commits afterwards, counted against a reference relation the proposer never sees.
"""

from __future__ import annotations

import unittest

from creib.errors import RecordError
from creib.forge.construct.candidates import VIEW_TWO
from creib.forge.construct.controller import contract_check, starting_controller
from creib.forge.construct.lab import (
    THE_GUARD,
    corrupted_evaluator_control,
    identity_aliasing_control,
    no_return_control,
    read_tree,
    run_enumeration,
    run_supplied,
)


class OperativeStateTests(unittest.TestCase):
    def test_what_is_deployed_before_an_episode_breaks_the_contract(self) -> None:
        before = contract_check(starting_controller(False), 4)
        self.assertEqual(before["violations"], 34)
        self.assertGreater(before["accepted_obsolete_result"], 0, "it accepts results it must reject")

    def test_installing_the_guard_changes_what_the_controller_answers(self) -> None:
        controller = starting_controller(False)
        controller.install(THE_GUARD, VIEW_TWO, "verified")
        self.assertTrue(contract_check(controller, 4)["clean"])

    def test_a_sealed_controller_keeps_the_artifact_and_changes_nothing(self) -> None:
        """The no-return control, and the shape a system that mints no standing is fixed in."""

        sealed = starting_controller(True)
        before = contract_check(sealed, 4)["violations"]
        sealed.install(THE_GUARD, VIEW_TWO, "verified, and not applied")
        self.assertEqual(sealed.installs[0]["program"], "active and current == incoming")
        self.assertFalse(sealed.installs[0]["applied"])
        self.assertEqual(contract_check(sealed, 4)["violations"], before)


class BaselineTests(unittest.TestCase):
    def test_enumeration_reaches_the_guard_and_the_cost_is_the_baseline(self) -> None:
        record = run_enumeration(budget=0)
        self.assertEqual(record["installed_program"], "active and current == incoming")
        self.assertEqual(record["after"]["violations"], 0)
        self.assertEqual(len(record["proposals"]), 8, "eight proposals is what a model must beat")

    def test_a_budget_below_the_baseline_cost_installs_nothing(self) -> None:
        record = run_enumeration(budget=6)
        self.assertEqual(record["installed_program"], "active")
        self.assertEqual(record["after"]["violations"], 34)

    def test_the_supplied_solution_control_shows_what_no_construction_looks_like(self) -> None:
        record = run_supplied()
        self.assertEqual(record["after"]["violations"], 0)
        self.assertTrue(record["proposals"][0]["supplied"])


class ControlTests(unittest.TestCase):
    def test_the_no_return_control_separates_the_artifact_from_the_use_path(self) -> None:
        control = no_return_control(4)
        self.assertTrue(control["held"])
        self.assertEqual(control["sealed_before"], control["sealed_after"])
        self.assertEqual(control["installed_after"], 0)

    def test_an_accepting_evaluator_is_not_correctness(self) -> None:
        control = corrupted_evaluator_control(4)
        self.assertTrue(control["held"])
        self.assertGreater(control["independent_contract_check"]["missed_current_result"], 0)

    def test_reusing_identities_defeats_the_verified_guard(self) -> None:
        for modulus in (1, 2, 3):
            with self.subTest(modulus=modulus):
                control = identity_aliasing_control(modulus + 1, modulus)
                self.assertTrue(control["held"])
                self.assertGreater(control["collisions"], 0)

    def test_a_control_that_corrupts_nothing_is_refused_when_it_is_built(self) -> None:
        with self.assertRaises(RecordError) as caught:
            identity_aliasing_control(4, 4)
        self.assertIn("vacuous", str(caught.exception))


class ReadingTests(unittest.TestCase):
    def test_a_reply_without_a_tree_is_not_repaired_into_one(self) -> None:
        for reply in ("not json", "{}", '{"why": "no tree"}', '{"tree": "active"}'):
            with self.subTest(reply=reply):
                self.assertIsNone(read_tree(reply)[0])

    def test_a_fenced_reply_is_read(self) -> None:
        tree, why = read_tree('```json\n{"tree": {"op": "true"}, "why": "because"}\n```')
        self.assertEqual(tree, {"op": "true"})
        self.assertEqual(why, "because")
