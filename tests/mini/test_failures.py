"""R11: the tolerance for format failures, per artifact kind, at submission."""

from __future__ import annotations

import copy

from creib.forge.mini.failures import DEFAULT_FAILURE_POLICY, FailurePolicy, failure_policy_from_dict
from creib.forge.mini.log import ARTIFACT_SUBMITTED, FORMAT_FAILURE, RUN_ENDED, SUBMISSION_DROPPED

from .helpers import MiniTestCase, base_manifest, submission

BAD = submission("nothing to see", "c")
GOOD = submission("it holds BECAUSE the source says so", "c")
KEYWORD_SPEC = {"body": {"all_of": [{"check": "keywords", "keywords": ["BECAUSE"]}]}}


def _manifest(policy: dict, stages: int = 1) -> dict:
    manifest = base_manifest()
    manifest["kinds"][0]["format"] = copy.deepcopy(KEYWORD_SPEC)
    manifest["kinds"][0]["failure_policy"] = policy
    manifest["stages"] = [
        {"stage_id": f"c{index + 1}", "kind_id": "k.conjecture", "ports": ["problem"]} for index in range(stages)
    ] + [{"stage_id": "end", "end": True}]
    return manifest


class RetryTests(MiniTestCase):
    def test_the_seat_is_re_asked_and_a_good_second_reply_is_accepted(self) -> None:
        _, outcome = self.run_manifest(_manifest({"retries": 1}), {"c1": [BAD, GOOD]})
        self.assertEqual(len(self.events_of(outcome, FORMAT_FAILURE)), 1)
        self.assertEqual(len(self.events_of(outcome, ARTIFACT_SUBMITTED)), 1)
        self.assertEqual(self.events_of(outcome, SUBMISSION_DROPPED), [])

    def test_no_retries_means_one_attempt(self) -> None:
        _, outcome = self.run_manifest(_manifest({"retries": 0}), {"c1": [BAD]})
        self.assertEqual(len(self.events_of(outcome, FORMAT_FAILURE)), 1)
        self.assertEqual(len(self.events_of(outcome, SUBMISSION_DROPPED)), 1)


class DropTests(MiniTestCase):
    def test_a_submission_still_failing_after_its_retries_is_dropped_and_the_run_goes_on(self) -> None:
        manifest = _manifest({"retries": 1}, stages=2)
        _, outcome = self.run_manifest(manifest, {"c1": [BAD, BAD], "c2": [GOOD]})
        self.assertEqual(len(self.events_of(outcome, SUBMISSION_DROPPED)), 1)
        self.assertEqual(len(self.events_of(outcome, ARTIFACT_SUBMITTED)), 1)
        self.assertEqual(self.events_of(outcome, RUN_ENDED)[0]["payload"]["stop_reason"], "end_stage")

    def test_the_default_is_drop_after_one_retry_and_never_stops(self) -> None:
        self.assertEqual(DEFAULT_FAILURE_POLICY.retries, 1)
        self.assertIsNone(DEFAULT_FAILURE_POLICY.tolerance)
        manifest = base_manifest()
        manifest["kinds"][0]["format"] = copy.deepcopy(KEYWORD_SPEC)
        manifest["stages"] = [
            {"stage_id": "c1", "kind_id": "k.conjecture", "ports": ["problem"]},
            {"stage_id": "c2", "kind_id": "k.conjecture", "ports": ["problem"]},
            {"stage_id": "end", "end": True},
        ]
        _, outcome = self.run_manifest(manifest, {"c1": [BAD, BAD], "c2": [BAD, BAD]})
        self.assertEqual(len(self.events_of(outcome, SUBMISSION_DROPPED)), 2)
        self.assertEqual(self.events_of(outcome, RUN_ENDED)[0]["payload"]["stop_reason"], "end_stage")


class StopTests(MiniTestCase):
    def test_exceeding_the_tolerance_stops_the_run_typed(self) -> None:
        manifest = _manifest({"retries": 0, "tolerance": 1, "action": "stop"}, stages=3)
        _, outcome = self.run_manifest(manifest, {"c1": [BAD], "c2": [BAD], "c3": [BAD]})
        self.assertEqual(self.events_of(outcome, RUN_ENDED)[0]["payload"]["stop_reason"], "format_failures_exceeded")

    def test_the_boundary_the_tolerance_permits_does_not_stop_the_run(self) -> None:
        manifest = _manifest({"retries": 0, "tolerance": 1, "action": "stop"}, stages=2)
        _, outcome = self.run_manifest(manifest, {"c1": [BAD], "c2": [GOOD]})
        self.assertEqual(len(self.events_of(outcome, SUBMISSION_DROPPED)), 1)
        self.assertEqual(self.events_of(outcome, RUN_ENDED)[0]["payload"]["stop_reason"], "end_stage")

    def test_action_drop_goes_on_dropping_past_the_tolerance(self) -> None:
        manifest = _manifest({"retries": 0, "tolerance": 0, "action": "drop"}, stages=2)
        _, outcome = self.run_manifest(manifest, {"c1": [BAD], "c2": [BAD]})
        self.assertEqual(len(self.events_of(outcome, SUBMISSION_DROPPED)), 2)
        self.assertEqual(self.events_of(outcome, RUN_ENDED)[0]["payload"]["stop_reason"], "end_stage")

    def test_a_fraction_tolerance_is_read_against_that_kinds_submissions(self) -> None:
        policy = FailurePolicy(retries=0, tolerance=None, tolerance_fraction=(1, 2), action="stop")
        self.assertFalse(policy.exceeded(drops=1, submissions=2))
        self.assertTrue(policy.exceeded(drops=2, submissions=2))

    def test_a_fraction_tolerance_stops_a_run_that_passes_it(self) -> None:
        manifest = _manifest({"retries": 0, "tolerance": {"numerator": 1, "denominator": 2}, "action": "stop"}, stages=3)
        _, outcome = self.run_manifest(manifest, {"c1": [GOOD], "c2": [BAD], "c3": [BAD]})
        self.assertEqual(self.events_of(outcome, RUN_ENDED)[0]["payload"]["stop_reason"], "format_failures_exceeded")


class PolicyReadingTests(MiniTestCase):
    def test_an_absent_policy_is_the_shipped_default(self) -> None:
        self.assertEqual(failure_policy_from_dict(None, "p"), DEFAULT_FAILURE_POLICY)

    def test_an_unknown_action_is_refused(self) -> None:
        self.assertRefuses("MINI_FAILURE_POLICY_INVALID", failure_policy_from_dict, {"action": "shout"}, "p")

    def test_a_retry_count_outside_the_range_is_refused(self) -> None:
        self.assertRefuses("MINI_FAILURE_POLICY_INVALID", failure_policy_from_dict, {"retries": 999}, "p")

    def test_a_fraction_with_a_bad_denominator_is_refused(self) -> None:
        self.assertRefuses(
            "MINI_FAILURE_POLICY_INVALID",
            failure_policy_from_dict,
            {"tolerance": {"numerator": 1, "denominator": 0}},
            "p",
        )

    def test_a_tolerance_that_is_neither_a_number_nor_a_fraction_is_refused(self) -> None:
        self.assertRefuses("MINI_FAILURE_POLICY_INVALID", failure_policy_from_dict, {"tolerance": "some"}, "p")

    def test_a_policy_is_carried_on_the_run_header(self) -> None:
        plan = self.compile(_manifest({"retries": 2, "tolerance": 3, "action": "drop"}))
        self.assertEqual(
            plan.kinds["k.conjecture"].failure_policy.to_dict(),
            {"retries": 2, "tolerance": 3, "action": "drop"},
        )
