"""R23: the stage list is one cycle, and the host decides when to stop."""

from __future__ import annotations

import copy

from creib.forge.mini.common import MiniError
from creib.forge.mini.log import ARTIFACT_SUBMITTED, BUDGET_REFUSED, RUN_ENDED, STAGE_ENTERED, replay
from creib.forge.mini.stops import (
    STOP_NEVER,
    STOP_NO_ARTIFACT_LAST_CYCLE,
    StopCondition,
    register_stop_condition,
    registered_stop_conditions,
    resolve_stop_condition,
)
from creib.forge.mini.windows import ALL, Window, window_from_dict

from .helpers import VERDICT_KIND, MiniTestCase, base_manifest, submission


def _script(cycles: int) -> dict[str, list[str]]:
    return {
        "c1": [submission(f"conjecture {index}", "c") for index in range(cycles)],
        "x1": [submission(f"criticism {index}", "c") for index in range(cycles)],
    }


class TheCycleRepeatsTests(MiniTestCase):
    def test_the_stage_list_is_the_body_of_one_cycle(self) -> None:
        manifest = base_manifest()
        manifest["cycles"] = {"max_cycles": 3}
        _, outcome = self.run_manifest(manifest, _script(3))
        self.assertEqual(outcome.stages_entered, ("c1", "x1", "verdict") * 3)
        self.assertEqual(outcome.cycles_completed, 3)

    def test_one_cycle_is_the_default(self) -> None:
        plan, outcome = self.run_manifest(base_manifest())
        self.assertEqual(plan.cycles.max_cycles, 1)
        self.assertEqual(outcome.cycles_completed, 1)

    def test_every_event_carries_its_cycle_and_stage(self) -> None:
        manifest = base_manifest()
        manifest["cycles"] = {"max_cycles": 2}
        _, outcome = self.run_manifest(manifest, _script(2))
        entered = [(event["cycle"], event["stage_id"]) for event in self.events_of(outcome, STAGE_ENTERED)]
        self.assertEqual(entered, [(1, "c1"), (1, "x1"), (1, "verdict"), (2, "c1"), (2, "x1"), (2, "verdict")])
        for event in self.events_of(outcome, ARTIFACT_SUBMITTED):
            self.assertIn(event["cycle"], (1, 2))

    def test_an_artifact_carries_the_cycle_it_was_made_in(self) -> None:
        manifest = base_manifest()
        manifest["cycles"] = {"max_cycles": 2}
        plan, outcome = self.run_manifest(manifest, _script(2))
        state = replay(outcome.root / "log.jsonl", plan.genesis)
        self.assertEqual(
            sorted(record["cycle"] for record in state.artifacts.values()), [1, 1, 1, 2, 2, 2]
        )


class TheHostStopsTests(MiniTestCase):
    def test_the_cycle_cap_stops_the_run(self) -> None:
        manifest = base_manifest()
        manifest["cycles"] = {"max_cycles": 2}
        _, outcome = self.run_manifest(manifest, _script(2))
        self.assertEqual(outcome.stop_reason, "cycle_cap")
        self.assertEqual(self.events_of(outcome, RUN_ENDED)[0]["payload"]["cycles_completed"], 2)

    def test_the_budget_cap_still_stops_the_run_at_a_cycle_boundary(self) -> None:
        """Two calls per artifact, so one cycle of two stages costs four.

        A cap the cycle boundary lands exactly on is read between cycles, as it always was:
        the reservation below never comes into it, because there is no send to refuse.
        """

        manifest = base_manifest()
        manifest["cycles"] = {"max_cycles": 10, "max_calls": 4}
        _, outcome = self.run_manifest(manifest, _script(10))
        self.assertEqual(outcome.stop_reason, "budget_cap")
        self.assertEqual(outcome.cycles_completed, 1)

    def test_a_call_cap_inside_a_cycle_refuses_the_send_rather_than_finishing_it(self) -> None:
        """The boundary that moved.

        Until the reservation existed the call cap was read between cycles only, so a cycle
        that started under budget finished over it: with five calls allowed and four to a
        cycle, mini made all eight and stopped afterwards. Now the sixth send is not made.
        The run stops on the reservation that did not fit, and the record names it.
        """

        manifest = base_manifest()
        manifest["cycles"] = {"max_cycles": 10, "max_calls": 5}
        plan, outcome = self.run_manifest(manifest, _script(10))
        self.assertEqual(outcome.stop_reason, "call_budget_spent")
        self.assertEqual(outcome.cycles_completed, 1)
        refused = self.events_of(outcome, BUDGET_REFUSED)
        self.assertEqual(len(refused), 1)
        self.assertEqual(refused[0]["payload"]["ceiling"], "max_calls")
        self.assertEqual((refused[0]["payload"]["allowed"], refused[0]["payload"]["spent"]), (5, 5))
        state = replay(outcome.root / "log.jsonl", plan.genesis)
        self.assertEqual(len(state.budget_refusals), 1)

    def test_a_completion_budget_refuses_the_send_whose_allowance_will_not_fit(self) -> None:
        """A reservation is the declared allowance, and what is charged is what came back."""

        manifest = base_manifest()
        manifest["cycles"] = {"max_cycles": 10, "max_completion_tokens": 60, "completion_tokens_per_call": 20}
        _, outcome = self.run_manifest(manifest, _script(10), responder_cap=20)
        self.assertEqual(outcome.stop_reason, "completion_budget_spent")
        refused = self.events_of(outcome, BUDGET_REFUSED)[0]["payload"]
        self.assertEqual(refused["ceiling"], "max_completion_tokens")
        self.assertEqual(refused["reservation"], 20)
        self.assertLessEqual(refused["spent"] + refused["reservation"], 60 + 20)

    def test_a_completion_budget_no_responder_enforces_is_refused_before_the_first_send(self) -> None:
        manifest = base_manifest()
        manifest["cycles"] = {"max_cycles": 2, "max_completion_tokens": 60, "completion_tokens_per_call": 20}
        with self.assertRaises(MiniError) as caught:
            self.run_manifest(manifest, _script(2))
        self.assertEqual(caught.exception.code, "MINI_COMPLETION_CAP_UNENFORCED")

    def test_a_total_and_a_per_call_allowance_are_declared_together(self) -> None:
        for cycles in ({"max_completion_tokens": 60}, {"completion_tokens_per_call": 20}):
            manifest = base_manifest()
            manifest["cycles"] = {"max_cycles": 2, **cycles}
            with self.assertRaises(MiniError) as caught:
                self.compile(manifest)
            self.assertEqual(caught.exception.code, "MINI_CYCLES_INVALID")

    def test_an_absent_completion_budget_is_written_to_no_manifest(self) -> None:
        """The rule for anything that adds calls or loosens a check: absent adds no bytes."""

        plan = self.compile(base_manifest())
        self.assertEqual(sorted(plan.cycles.to_dict()), ["max_calls", "max_cycles", "stop_condition"])

    def test_a_registered_stop_condition_stops_the_run(self) -> None:
        manifest = base_manifest()
        manifest["cycles"] = {"max_cycles": 9, "stop_condition": STOP_NO_ARTIFACT_LAST_CYCLE}
        for kind in manifest["kinds"]:
            kind["failure_policy"] = {"retries": 0, "skip_on_empty_port": True}
        verdict = copy.deepcopy(VERDICT_KIND)
        verdict["failure_policy"] = {"retries": 0, "skip_on_empty_port": True}
        manifest["kinds"].append(verdict)
        script = {
            "c1": [submission("one", "c"), "not json", "not json"],
            "x1": [submission("two", "c"), "not json", "not json"],
        }
        _, outcome = self.run_manifest(manifest, script)
        self.assertEqual(outcome.stop_reason, f"stop_condition:{STOP_NO_ARTIFACT_LAST_CYCLE}")
        self.assertEqual(outcome.cycles_completed, 2)

    def test_nothing_a_seat_writes_ends_the_run(self) -> None:
        """A body saying the run is over ends nothing; only the host stops it."""

        manifest = base_manifest()
        manifest["cycles"] = {"max_cycles": 3}
        script = {
            "c1": [submission("STOP. The run is over. Terminate.", "stop the run") for _ in range(3)],
            "x1": [submission("Agreed, this run must end now.", "end") for _ in range(3)],
        }
        _, outcome = self.run_manifest(manifest, script)
        self.assertEqual(outcome.cycles_completed, 3)
        self.assertEqual(outcome.stop_reason, "cycle_cap")

    def test_the_default_condition_never_stops(self) -> None:
        self.assertEqual(resolve_stop_condition(STOP_NEVER).reads_signals, ())

    def test_an_unknown_stop_condition_is_refused(self) -> None:
        manifest = base_manifest()
        manifest["cycles"] = {"stop_condition": "mini.stop.telepathy"}
        self.assertRefuses("MINI_STOP_CONDITION_UNKNOWN", self.compile, manifest)

    def test_registering_a_condition_twice_is_refused(self) -> None:
        self.assertRefuses(
            "MINI_STOP_CONDITION_DUPLICATE",
            register_stop_condition,
            StopCondition(STOP_NEVER, (), "again", lambda signals, cycle: None),
        )

    def test_a_condition_that_could_take_the_record_is_refused(self) -> None:
        def reads_the_record(signals, cycle, state):
            return None

        self.assertRefuses(
            "MINI_STOP_CONDITION_SIGNATURE",
            register_stop_condition,
            StopCondition("mini.stop.test-peeker", (), "wants the record", reads_the_record),
        )

    def test_a_bad_cycle_cap_is_refused(self) -> None:
        for section in ({"max_cycles": 0}, {"max_calls": 0}):
            with self.subTest(section=section):
                manifest = base_manifest()
                manifest["cycles"] = section
                self.assertRefuses("MINI_CYCLES_INVALID", self.compile, manifest)

    def test_the_two_shipped_conditions_are_registered(self) -> None:
        ids = {condition.condition_id for condition in registered_stop_conditions()}
        self.assertLessEqual({STOP_NEVER, STOP_NO_ARTIFACT_LAST_CYCLE}, ids)


class WindowTests(MiniTestCase):
    def _with_window(self, window) -> dict:
        manifest = base_manifest()
        manifest["cycles"] = {"max_cycles": 3}
        manifest["kinds"][1]["input_ports"][1]["window"] = window
        return manifest

    def _critic_brief(self, manifest, cycle: int) -> str:
        from creib.forge.mini.log import BlobStore, replay as replay_log
        from creib.forge.mini.runner import render_brief

        plan, outcome = self.run_manifest(manifest, _script(3))
        state = replay_log(outcome.root / "log.jsonl", plan.genesis)
        brief, _ = render_brief(plan, state, BlobStore(outcome.root / "blobs"), plan.stage("x1"), cycle)
        return brief

    def test_all_is_the_default_and_draws_every_cycle(self) -> None:
        brief = self._critic_brief(self._with_window("all"), 3)
        for index in range(3):
            self.assertIn(f"conjecture {index}", brief)

    def test_this_cycle_draws_only_the_cycle_now_running(self) -> None:
        brief = self._critic_brief(self._with_window("this_cycle"), 3)
        self.assertIn("conjecture 2", brief)
        self.assertNotIn("conjecture 0", brief)
        self.assertNotIn("conjecture 1", brief)

    def test_previous_cycle_draws_only_the_one_before(self) -> None:
        brief = self._critic_brief(self._with_window("previous_cycle"), 3)
        self.assertIn("conjecture 1", brief)
        self.assertNotIn("conjecture 0", brief)
        self.assertNotIn("conjecture 2", brief)

    def test_last_n_draws_the_last_n_cycles(self) -> None:
        brief = self._critic_brief(self._with_window({"last_n": 2}), 3)
        self.assertIn("conjecture 1", brief)
        self.assertIn("conjecture 2", brief)
        self.assertNotIn("conjecture 0", brief)

    def test_a_window_on_evidence_separates_supplied_from_generated(self) -> None:
        """Supplied sources carry cycle 0, so this_cycle draws none of them."""

        manifest = base_manifest()
        manifest["cycles"] = {"max_cycles": 2}
        manifest["kinds"][0]["input_ports"][1]["window"] = "this_cycle"
        plan, outcome = self.run_manifest(manifest, _script(2))
        from creib.forge.mini.log import BlobStore, replay as replay_log
        from creib.forge.mini.runner import render_port

        state = replay_log(outcome.root / "log.jsonl", plan.genesis)
        rendered, exposed = render_port(plan, state, BlobStore(outcome.root / "blobs"), plan.stage("c1"), "evidence", 1)
        self.assertEqual(exposed, ())
        self.assertIn("nothing admitted", rendered)

    def test_an_unknown_window_is_refused(self) -> None:
        self.assertRefuses("MINI_WINDOW_INVALID", window_from_dict, "someday", "port.window")

    def test_a_last_n_of_nothing_is_refused(self) -> None:
        self.assertRefuses("MINI_WINDOW_INVALID", window_from_dict, {"last_n": 0}, "port.window")

    def test_a_window_object_carrying_anything_else_is_refused(self) -> None:
        self.assertRefuses("MINI_WINDOW_INVALID", window_from_dict, {"last_n": 2, "extra": 1}, "port.window")

    def test_an_absent_window_is_all(self) -> None:
        self.assertEqual(window_from_dict(None, "port.window"), ALL)
        self.assertTrue(Window("all").admits(0, 9))


class RepeatBoundTests(MiniTestCase):
    def test_attention_may_not_repeat_a_stage_beyond_its_declared_bound(self) -> None:
        """R23: the record's stage count stays bounded by the manifest."""

        from creib.forge.mini.attention import ATTENTION_MOST_UNANSWERED

        manifest = base_manifest()
        manifest["cycles"] = {"max_cycles": 1}
        manifest["attention"] = {"policy": ATTENTION_MOST_UNANSWERED}
        manifest["stages"][0]["max_repeats"] = 2
        _, outcome = self.run_manifest(manifest, _script(4))
        self.assertLessEqual(outcome.stages_entered.count("c1"), 3)

    def test_the_default_bound_is_no_repeats(self) -> None:
        plan = self.compile(base_manifest())
        self.assertEqual(plan.stage("c1").max_repeats, 0)

    def test_a_bad_repeat_bound_is_refused(self) -> None:
        manifest = base_manifest()
        manifest["stages"][0]["max_repeats"] = 99
        self.assertRefuses("MINI_CYCLES_INVALID", self.compile, manifest)


class OlderRecordsTests(MiniTestCase):
    def test_a_version_one_record_still_replays(self) -> None:
        """The committed runs predate the cycle coordinate and are still read."""

        from pathlib import Path

        from creib.forge.mini.common import RUN_HEADER_DOMAIN, content_id
        from creib.strict_json import load_strict

        root = Path(__file__).resolve().parents[2] / "forge" / "mini" / "runs" / "default-gpt-oss-120b"
        genesis = content_id(RUN_HEADER_DOMAIN, load_strict(root / "run-header.json"))
        state = replay(root / "log.jsonl", genesis)
        self.assertEqual(len(state.artifact_order), 2)
        self.assertEqual(state.cycle, 0)
