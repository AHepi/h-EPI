"""The callback task, the impossibility, the construction, and the reproduction discrepancy.

The Evidence Report of 11 September 2026 is the thing being reproduced. Its qualitative result
reproduces here in full; its state and case counts do not, and the reason is pinned by a test so
that it cannot drift silently.
"""

from __future__ import annotations

import unittest

from creib.errors import RecordError
from creib.forge.construct.candidates import (
    VIEW_ONE,
    VIEW_TWO,
    evaluate,
    render,
    shared_view_counterexample,
    stage_one_language,
    stage_two_language,
    verify,
)
from creib.forge.construct.task import TICKETS, Case, State, cases, reachable, required


class TaskTests(unittest.TestCase):
    def test_the_reachable_set_is_a_fixed_point_and_its_size_is_pinned(self) -> None:
        self.assertEqual((len(reachable(4)), len(cases(4))), (61, 98))
        for smaller, larger in zip((2, 3, 4, 5), (3, 4, 5, 6)):
            self.assertLess(len(reachable(smaller)), len(reachable(larger)))

    def test_cancel_keeps_what_is_owed_and_keeps_the_register(self) -> None:
        from creib.forge.construct.task import cancel, start, INITIAL

        after = start(INITIAL, 4)
        cancelled = cancel(after)
        self.assertEqual(cancelled.pending, after.pending, "a cancel erases nothing that is owed")
        self.assertEqual(cancelled.register, after.register, "a register keeps its value")
        self.assertIsNone(cancelled.live, "but nothing is live")

    def test_a_superseded_request_still_owes_its_callback(self) -> None:
        from creib.forge.construct.task import start, INITIAL

        second = start(start(INITIAL, 4), 4)
        self.assertEqual(sorted(second.pending), ["A", "B"])
        self.assertEqual(second.live, "B")
        self.assertFalse(required(second, "A"), "the superseded request's callback is obsolete")
        self.assertTrue(required(second, "B"))


class ImpossibilityTests(unittest.TestCase):
    def test_every_function_of_the_one_bit_view_fails(self) -> None:
        """Not a poor candidate: the whole class, which is what licenses changing the view."""

        for tree in stage_one_language():
            with self.subTest(tree=render(tree)):
                self.assertFalse(verify(tree, VIEW_ONE, 4).accepted)

    def test_the_counterexample_is_two_cases_sharing_a_view_and_needing_opposite_answers(self) -> None:
        pair = shared_view_counterexample(VIEW_ONE, 4)
        self.assertIsNotNone(pair)
        first, second = pair
        self.assertEqual(first.view(VIEW_ONE), second.view(VIEW_ONE))
        self.assertNotEqual(first.answer, second.answer)

    def test_the_richer_view_has_no_such_counterexample(self) -> None:
        self.assertIsNone(shared_view_counterexample(VIEW_TWO, 4), "the extension removes the obstruction")


class ConstructionTests(unittest.TestCase):
    def test_the_first_accepted_candidate_is_the_guard_the_report_installs(self) -> None:
        accepted = [tree for tree in stage_two_language() if verify(tree, VIEW_TWO, 4).accepted]
        self.assertTrue(accepted)
        self.assertEqual(render(accepted[0]), "active and current == incoming")

    def test_the_bare_comparison_is_not_enough_because_the_register_retains(self) -> None:
        bare = {"op": "equal", "left": "current", "right": "incoming"}
        outcome = verify(bare, VIEW_TWO, 4)
        self.assertFalse(outcome.accepted, "after a cancel the register still equals the arriving ticket")

    def test_a_candidate_reading_an_unexposed_field_is_refused_not_guessed(self) -> None:
        peeking = {"op": "field", "name": "current"}
        outcome = verify(peeking, VIEW_ONE, 4)
        self.assertFalse(outcome.accepted)
        self.assertIn("does not expose", str(outcome.first_failure))

    def test_a_malformed_equal_is_refused_and_does_not_end_the_run(self) -> None:
        """Three models proposed an equal over whole trees. That is not this grammar."""

        nested = {"op": "equal", "left": {"op": "field", "name": "current"}, "right": {"op": "field", "name": "incoming"}}
        outcome = verify(nested, VIEW_TWO, 4)
        self.assertFalse(outcome.accepted)
        self.assertIn("two field names", str(outcome.first_failure))

    def test_a_field_named_by_something_that_is_not_a_string_is_refused(self) -> None:
        outcome = verify({"op": "field", "name": {"op": "true"}}, VIEW_TWO, 4)
        self.assertFalse(outcome.accepted)
        self.assertIn("named by a string", str(outcome.first_failure))

    def test_an_unknown_operator_is_refused(self) -> None:
        with self.assertRaises(RecordError):
            evaluate({"op": "xor", "left": "a", "right": "b"}, {"a": True, "b": False})


class ReproductionTests(unittest.TestCase):
    """Why this module's counts differ from the Evidence Report's, pinned so it cannot drift."""

    def _deduped(self, max_starts: int) -> tuple[int, int]:
        """The report's counts come from a key that omits a field the candidate can see."""

        key = lambda s: ((s.register if s.active else None), s.pending)
        groups: dict[object, State] = {}
        for state in reachable(max_starts):
            groups.setdefault(key(state), state)
        return len(groups), sum(len(s.pending) for s in groups.values())

    def test_the_reports_counts_come_from_dropping_an_exposed_field_from_the_key(self) -> None:
        self.assertEqual(self._deduped(4), (46, 81), "the Evidence Report's 46 states and 81 cases")

    def test_that_key_merges_states_that_show_the_candidate_different_things(self) -> None:
        key = lambda s: ((s.register if s.active else None), s.pending)
        groups: dict[object, set[str | None]] = {}
        for state in reachable(4):
            groups.setdefault(key(state), set()).add(state.register if not state.active else None)
        colliding = [k for k, regs in groups.items() if len({r for r in regs if r is not None}) > 1]
        self.assertTrue(colliding, "so a verdict would depend on which member the fixed point kept")

    def test_under_that_key_the_installed_guard_would_be_redundant(self) -> None:
        """The two claims are not jointly satisfiable: the counts make the conjunction unnecessary."""

        bare_is_enough = all(
            ((case.state.live == case.ticket) == case.answer) for case in cases(4)
        )
        self.assertTrue(bare_is_enough, "with current as the live ticket, `current == incoming` suffices")
