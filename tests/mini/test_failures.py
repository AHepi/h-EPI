"""R11: the tolerance for format failures, per artifact kind, at submission."""

from __future__ import annotations

import copy

from creib.forge.mini.failures import DEFAULT_FAILURE_POLICY, FailurePolicy, failure_policy_from_dict
from creib.forge.mini.log import ARTIFACT_SUBMITTED, FORMAT_FAILURE, PORT_EMPTY, RUN_ENDED, SUBMISSION_DROPPED

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
        self.assertEqual(self.events_of(outcome, RUN_ENDED)[0]["payload"]["stop_reason"], "cycle_cap")

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
        self.assertEqual(self.events_of(outcome, RUN_ENDED)[0]["payload"]["stop_reason"], "cycle_cap")


class StopTests(MiniTestCase):
    def test_exceeding_the_tolerance_stops_the_run_typed(self) -> None:
        manifest = _manifest({"retries": 0, "tolerance": 1, "action": "stop"}, stages=3)
        _, outcome = self.run_manifest(manifest, {"c1": [BAD], "c2": [BAD], "c3": [BAD]})
        self.assertEqual(self.events_of(outcome, RUN_ENDED)[0]["payload"]["stop_reason"], "format_failures_exceeded")

    def test_the_boundary_the_tolerance_permits_does_not_stop_the_run(self) -> None:
        manifest = _manifest({"retries": 0, "tolerance": 1, "action": "stop"}, stages=2)
        _, outcome = self.run_manifest(manifest, {"c1": [BAD], "c2": [GOOD]})
        self.assertEqual(len(self.events_of(outcome, SUBMISSION_DROPPED)), 1)
        self.assertEqual(self.events_of(outcome, RUN_ENDED)[0]["payload"]["stop_reason"], "cycle_cap")

    def test_action_drop_goes_on_dropping_past_the_tolerance(self) -> None:
        manifest = _manifest({"retries": 0, "tolerance": 0, "action": "drop"}, stages=2)
        _, outcome = self.run_manifest(manifest, {"c1": [BAD], "c2": [BAD]})
        self.assertEqual(len(self.events_of(outcome, SUBMISSION_DROPPED)), 2)
        self.assertEqual(self.events_of(outcome, RUN_ENDED)[0]["payload"]["stop_reason"], "cycle_cap")

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
            {"retries": 2, "tolerance": 3, "action": "drop", "skip_on_empty_port": False},
        )


class RefusedRepliesAreKeptTests(MiniTestCase):
    """FAILURE_MODES H1: a reply refused for its format is kept, not only its reason.

    Found by a live run whose conjecture stage returned something unreadable
    twice: the record said it was unreadable and could not say what it was.
    """

    def test_a_reply_refused_for_its_format_is_stored_and_named_on_the_event(self) -> None:
        _, outcome = self.run_manifest(_manifest({"retries": 1}), {"c1": [BAD, GOOD]})
        from creib.forge.mini.log import BlobStore

        failure = self.events_of(outcome, FORMAT_FAILURE)[0]
        self.assertIsNotNone(failure["body_ref"])
        kept = BlobStore(outcome.root / "blobs").get(failure["body_ref"]).decode("utf-8")
        self.assertEqual(kept, BAD)

    def test_an_unreadable_reply_is_kept_verbatim(self) -> None:
        """The live case: not JSON at all, so nothing could be parsed out of it."""

        _, outcome = self.run_manifest(_manifest({"retries": 0}), {"c1": ["Here is my answer, in prose."]})
        from creib.forge.mini.log import BlobStore

        failure = self.events_of(outcome, FORMAT_FAILURE)[0]
        self.assertEqual(failure["payload"]["code"], "MINI_SUBMISSION_NOT_JSON")
        self.assertEqual(
            BlobStore(outcome.root / "blobs").get(failure["body_ref"]).decode("utf-8"),
            "Here is my answer, in prose.",
        )

    def test_a_dropped_submission_names_every_reply_that_was_refused(self) -> None:
        _, outcome = self.run_manifest(_manifest({"retries": 1}), {"c1": [BAD, "not json either"]})
        from creib.forge.mini.log import BlobStore

        dropped = self.events_of(outcome, SUBMISSION_DROPPED)[0]
        refs = dropped["payload"]["refused_refs"]
        self.assertEqual(len(refs), 2)
        store = BlobStore(outcome.root / "blobs")
        self.assertEqual(
            [store.get(ref).decode("utf-8") for ref in refs],
            [BAD, "not json either"],
        )

    def test_an_accepted_reply_leaves_no_refusal_blob_behind(self) -> None:
        _, outcome = self.run_manifest(_manifest({"retries": 1}), {"c1": [GOOD]})
        self.assertEqual(self.events_of(outcome, FORMAT_FAILURE), [])
        self.assertEqual(self.events_of(outcome, SUBMISSION_DROPPED), [])


class EmptyPortTests(MiniTestCase):
    """R32: a declared artifact port that draws nothing is a typed notice.

    The shape is the one the glm run produced (FAILURE_MODES M3): a conjecture
    stage drops, and the critic then runs with no conjectures to criticise.
    """

    def _manifest(self, skip: bool) -> dict:
        manifest = base_manifest()
        manifest["kinds"][0]["format"] = copy.deepcopy(KEYWORD_SPEC)
        manifest["kinds"][0]["failure_policy"] = {"retries": 0}
        manifest["kinds"][1]["failure_policy"] = {"skip_on_empty_port": skip}
        return manifest

    def test_by_default_the_stage_still_runs_and_the_notice_is_on_the_record(self) -> None:
        _, outcome = self.run_manifest(self._manifest(False), {"c1": [BAD], "x1": [submission("a", "b")]})
        notices = self.events_of(outcome, "PORT_EMPTY")
        self.assertEqual(len(notices), 1)
        self.assertEqual(notices[0]["payload"]["port_id"], "conjectures")
        self.assertEqual(notices[0]["stage_id"], "x1")
        self.assertEqual(len(self.events_of(outcome, ARTIFACT_SUBMITTED)), 1)

    def test_the_notice_comes_before_the_stage_is_asked(self) -> None:
        _, outcome = self.run_manifest(self._manifest(False), {"c1": [BAD], "x1": [submission("a", "b")]})
        types = [event["type"] for event in self.events(outcome)]
        self.assertLess(types.index("PORT_EMPTY"), len(types) - 1 - types[::-1].index(ARTIFACT_SUBMITTED))

    def test_set_to_skip_the_stage_produces_nothing(self) -> None:
        _, outcome = self.run_manifest(self._manifest(True), {"c1": [BAD]})
        self.assertEqual(len(self.events_of(outcome, "PORT_EMPTY")), 1)
        self.assertEqual(self.events_of(outcome, ARTIFACT_SUBMITTED), [])
        dropped = [event for event in self.events_of(outcome, SUBMISSION_DROPPED) if event["stage_id"] == "x1"]
        self.assertEqual(len(dropped), 1)
        self.assertIn("drew nothing", dropped[0]["payload"]["reasons"][0])

    def test_a_port_that_drew_something_writes_no_notice(self) -> None:
        _, outcome = self.run_manifest(self._manifest(False), {"c1": [GOOD], "x1": [submission("a", "b")]})
        self.assertEqual(self.events_of(outcome, "PORT_EMPTY"), [])

    def test_an_empty_evidence_port_is_not_a_notice(self) -> None:
        """C6: an empty evidence port is the ordinary state of a first cycle."""

        manifest = base_manifest()
        manifest["sources"] = []
        _, outcome = self.run_manifest(manifest)
        self.assertEqual(self.events_of(outcome, "PORT_EMPTY"), [])

    def test_the_default_is_not_to_skip(self) -> None:
        self.assertFalse(DEFAULT_FAILURE_POLICY.skip_on_empty_port)

    def test_a_bad_skip_setting_is_refused(self) -> None:
        self.assertRefuses(
            "MINI_FAILURE_POLICY_INVALID", failure_policy_from_dict, {"skip_on_empty_port": "yes"}, "p"
        )
