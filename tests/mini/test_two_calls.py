"""R35: two calls per artifact, and one verdict node per cycle."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from creib.forge.mini.log import ARTIFACT_SUBMITTED, FORMAT_FAILURE, BlobStore, replay
from creib.forge.mini.manifest import COMMITMENT_CALL_SINGLE, COMMITMENT_CALL_TWO, VERDICT_KIND_ID

from .helpers import VERDICT_KIND, VERDICT_STAGE, MiniTestCase, base_manifest, submission

ROOT = Path(__file__).resolve().parents[2]


class _Recorder:
    """A responder that keeps every request it was handed."""

    def __init__(self, inner) -> None:
        self._inner = inner
        self.seen: list[tuple[str, str, str]] = []

    def reply(self, request):
        self.seen.append((request.stage_id, request.phase, request.brief))
        return self._inner.reply(request)


class TwoCallsTests(MiniTestCase):
    def _run(self, manifest, script, name="run"):
        from creib.forge.mini.executor import ScriptedResponder
        from creib.forge.mini.runner import run_mini

        plan = self.compile(manifest)
        recorder = _Recorder(ScriptedResponder(script))
        return plan, run_mini(plan, self.tmp / name, recorder), recorder

    def test_an_artifact_is_produced_by_two_calls_by_default(self) -> None:
        plan, outcome, recorder = self._run(
            base_manifest(), {"c1": [submission("a body", "a commitment")], "x1": [submission("b", "c")]}
        )
        phases = [(stage, phase) for stage, phase, _ in recorder.seen]
        self.assertEqual(phases[:2], [("c1", "body"), ("c1", "commitments")])
        self.assertEqual(plan.kinds["k.conjecture"].commitment_call, COMMITMENT_CALL_TWO)

    def test_by_default_the_second_call_sees_the_body_and_nothing_else(self) -> None:
        """C7: asserted as absence in the dispatched bytes, not trusted.

        This is the DEFAULT, not a law: see the tests below for a kind that
        declares what else its commitments call sees (R37).
        """

        manifest = base_manifest()
        manifest["problem"] = "AN UNMISTAKABLE PROBLEM STATEMENT"
        _, outcome, recorder = self._run(
            manifest,
            {
                "c1": [submission("THE BODY OF THE FIRST ARTIFACT", "c")],
                "x1": [submission("THE BODY OF THE SECOND ARTIFACT", "c")],
            },
        )
        second = [brief for stage, phase, brief in recorder.seen if stage == "x1" and phase == "commitments"]
        self.assertEqual(len(second), 1)
        brief = second[0]
        self.assertIn("THE BODY OF THE SECOND ARTIFACT", brief)
        self.assertNotIn("AN UNMISTAKABLE PROBLEM STATEMENT", brief)
        self.assertNotIn("THE BODY OF THE FIRST ARTIFACT", brief)
        self.assertNotIn("first paragraph", brief)
        for block in self._block_ids(outcome):
            self.assertNotIn(block[:16], brief)

    def _block_ids(self, outcome) -> list[str]:
        return [
            block["block_id"]
            for event in self.events_of(outcome, "EVIDENCE_BATCHED")
            for block in event["payload"]["blocks"]
        ]

    def test_the_record_carries_both_requests_and_both_replies(self) -> None:
        _, outcome, _ = self._run(
            base_manifest(), {"c1": [submission("a body", "a commitment")], "x1": [submission("b", "c")]}
        )
        submitted = self.events_of(outcome, ARTIFACT_SUBMITTED)[0]
        calls = submitted["payload"]["calls"]
        self.assertEqual([call["phase"] for call in calls], ["body", "commitments"])
        store = BlobStore(outcome.root / "blobs")
        for call in calls:
            self.assertTrue(store.get(call["request_ref"]))
            self.assertTrue(store.get(call["reply_ref"]))
        # Anyone can read the second request and see what it did not contain.
        second = store.get(calls[1]["request_ref"]).decode("utf-8")
        self.assertIn("a body", second)
        self.assertNotIn("first paragraph", second)

    def test_a_kind_set_to_single_dispatches_once(self) -> None:
        manifest = base_manifest()
        manifest["kinds"][0]["commitment_call"] = "single"
        plan, outcome, recorder = self._run(
            manifest, {"c1": [submission("a body", "a commitment")], "x1": [submission("b", "c")]}
        )
        self.assertEqual([phase for stage, phase, _ in recorder.seen if stage == "c1"], ["both"])
        self.assertEqual(plan.kinds["k.conjecture"].commitment_call, COMMITMENT_CALL_SINGLE)

    def test_the_record_says_which_shape_produced_each_artifact(self) -> None:
        manifest = base_manifest()
        manifest["kinds"][0]["commitment_call"] = "single"
        _, outcome, _ = self._run(
            manifest, {"c1": [submission("a body", "a commitment")], "x1": [submission("b", "c")]}
        )
        shapes = {
            event["kind_id"]: event["payload"]["commitment_call"]
            for event in self.events_of(outcome, ARTIFACT_SUBMITTED)
        }
        self.assertEqual(shapes["k.conjecture"], "single")
        self.assertEqual(shapes["k.criticism"], "two")

    def test_a_machine_seat_makes_one_call_and_says_so(self) -> None:
        """C10: there is no second call to make blind, and the record says it."""

        _, outcome, _ = self._run(
            base_manifest(), {"c1": [submission("a body", "c")], "x1": [submission("b", "c")]}
        )
        shapes = {
            event["kind_id"]: event["payload"]["commitment_call"]
            for event in self.events_of(outcome, ARTIFACT_SUBMITTED)
        }
        self.assertEqual(shapes[VERDICT_KIND_ID], "machine_single")

    def test_a_commitments_call_that_misses_its_format_drops_the_artifact(self) -> None:
        """C8: the format splits, and the failure names the phase."""

        manifest = base_manifest()
        manifest["kinds"][0]["format"] = {
            "commitments": {"all_of": [{"check": "keywords", "keywords": ["I COMMIT"]}]}
        }
        manifest["kinds"][0]["failure_policy"] = {"retries": 0}
        _, outcome, _ = self._run(
            manifest,
            {
                "c1": [submission("a body", "no such words")],
                "c1@commitments": [json.dumps({"commitments": "no such words"})],
                "x1": [submission("b", "c")],
            },
        )
        failures = self.events_of(outcome, FORMAT_FAILURE)
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0]["payload"]["phase"], "commitments")
        self.assertEqual([e["kind_id"] for e in self.events_of(outcome, ARTIFACT_SUBMITTED)][0], "k.criticism")

    def test_a_body_call_that_misses_its_format_never_reaches_the_second_call(self) -> None:
        manifest = base_manifest()
        manifest["kinds"][0]["format"] = {"body": {"all_of": [{"check": "keywords", "keywords": ["BECAUSE"]}]}}
        manifest["kinds"][0]["failure_policy"] = {"retries": 0}
        _, outcome, recorder = self._run(
            manifest, {"c1": [submission("nothing", "c")], "x1": [submission("b", "c")]}
        )
        self.assertEqual([phase for stage, phase, _ in recorder.seen if stage == "c1"], ["body"])


class VerdictNodeTests(MiniTestCase):
    def test_a_manifest_with_no_verdict_stage_is_refused(self) -> None:
        self.assertRefuses("MINI_VERDICT_MISSING", self.compile, base_manifest(), None, False)

    def test_two_verdict_stages_are_refused(self) -> None:
        manifest = base_manifest()
        manifest["kinds"].append(copy.deepcopy(VERDICT_KIND))
        manifest["stages"] = manifest["stages"][:-1] + [
            {**copy.deepcopy(VERDICT_STAGE), "stage_id": "v1"},
            {**copy.deepcopy(VERDICT_STAGE), "stage_id": "v2"},
            {"stage_id": "end", "end": True},
        ]
        self.assertRefuses("MINI_VERDICT_DUPLICATE", self.compile, manifest, None, False)

    def test_a_verdict_stage_that_is_not_last_is_refused(self) -> None:
        manifest = base_manifest()
        manifest["kinds"].append(copy.deepcopy(VERDICT_KIND))
        manifest["stages"] = [
            {"stage_id": "c1", "kind_id": "k.conjecture", "ports": ["problem"]},
            copy.deepcopy(VERDICT_STAGE),
            {"stage_id": "x1", "kind_id": "k.criticism", "ports": ["problem", "conjectures"]},
            {"stage_id": "end", "end": True},
        ]
        self.assertRefuses("MINI_VERDICT_NOT_LAST", self.compile, manifest, None, False)

    def test_exactly_one_verdict_per_cycle(self) -> None:
        manifest = base_manifest()
        manifest["cycles"] = {"max_cycles": 3}
        script = {
            "c1": {str(index + 1): [submission(f"body {index}", "c")] for index in range(3)},
            "x1": {str(index + 1): [submission(f"criticism {index}", "c")] for index in range(3)},
        }
        _, outcome = self.run_manifest(manifest, script)
        verdicts = [event for event in self.events_of(outcome, ARTIFACT_SUBMITTED) if event["kind_id"] == VERDICT_KIND_ID]
        self.assertEqual([event["cycle"] for event in verdicts], [1, 2, 3])
        self.assertEqual(outcome.stages_entered, ("c1", "x1", "verdict") * 3)

    def test_attention_cannot_reach_the_verdict_early(self) -> None:
        """C12: 'ends with' survives a re-ordering policy."""

        from creib.forge.mini.attention import ATTENTION_MOST_UNANSWERED

        manifest = base_manifest()
        manifest["attention"] = {"policy": ATTENTION_MOST_UNANSWERED}
        manifest["stages"][0]["max_repeats"] = 1
        _, outcome = self.run_manifest(
            manifest, {"c1": [submission("a", "c")] * 3, "x1": [submission("b", "c")] * 3}
        )
        self.assertEqual(outcome.stages_entered[-1], "verdict")
        self.assertEqual(outcome.stages_entered.count("verdict"), 1)

    def test_the_shipped_manifests_all_carry_a_verdict_stage(self) -> None:
        """C11: a structural rule the repository's own examples break is not a rule."""

        from creib.forge.mini.manifest import compile_manifest

        manifests = sorted((ROOT / "forge" / "mini" / "manifests").glob("*/manifest.json"))
        self.assertTrue(manifests)
        for path in manifests:
            with self.subTest(manifest=path.parent.name):
                plan = compile_manifest(path)
                self.assertEqual(plan.stages[-2].kind_id, VERDICT_KIND_ID)


class BlindSpotOnTheNewShapeTests(MiniTestCase):
    def test_the_committed_blind_spot_run_is_built_on_two_calls(self) -> None:
        from creib.forge.mini.common import RUN_HEADER_DOMAIN, content_id
        from creib.strict_json import load_strict

        root = ROOT / "forge" / "mini" / "runs" / "blind-spot-stub"
        genesis = content_id(RUN_HEADER_DOMAIN, load_strict(root / "run-header.json"))
        state = replay(root / "log.jsonl", genesis)
        self.assertEqual(state.cycles_completed, 3)
        proposals = [record for record in state.artifacts.values() if record["kind_id"] == "mini.proposal.v1"]
        self.assertEqual(len(proposals), 9)
        verdicts = [record for record in state.artifacts.values() if record["kind_id"] == VERDICT_KIND_ID]
        self.assertEqual(len(verdicts), 3)


class WhatTheCommitmentsCallSeesTests(MiniTestCase):
    """R37: the blind second call is the default, and the default is declared."""

    def _run(self, manifest, script, name="run"):
        from creib.forge.mini.executor import ScriptedResponder
        from creib.forge.mini.runner import run_mini

        plan = self.compile(manifest)
        recorder = _Recorder(ScriptedResponder(script))
        return plan, run_mini(plan, self.tmp / name, recorder), recorder

    def _script(self):
        return {"c1": [submission("THE BODY", "c")], "x1": [submission("b", "c")]}

    def test_the_default_is_no_ports_at_all(self) -> None:
        plan = self.compile(base_manifest())
        self.assertEqual(plan.kinds["k.conjecture"].commitment_ports, ())

    def test_a_kind_may_declare_what_else_its_commitments_call_sees(self) -> None:
        manifest = base_manifest()
        manifest["problem"] = "AN UNMISTAKABLE PROBLEM STATEMENT"
        manifest["kinds"][0]["commitment_ports"] = ["problem"]
        _, _, recorder = self._run(manifest, self._script())
        second = [brief for stage, phase, brief in recorder.seen if stage == "c1" and phase == "commitments"][0]
        self.assertIn("THE BODY", second)
        self.assertIn("AN UNMISTAKABLE PROBLEM STATEMENT", second)

    def test_a_kind_that_declares_nothing_still_sees_nothing(self) -> None:
        manifest = base_manifest()
        manifest["problem"] = "AN UNMISTAKABLE PROBLEM STATEMENT"
        _, _, recorder = self._run(manifest, self._script())
        second = [brief for stage, phase, brief in recorder.seen if stage == "c1" and phase == "commitments"][0]
        self.assertNotIn("AN UNMISTAKABLE PROBLEM STATEMENT", second)
        self.assertIn("You are shown nothing else", second)

    def test_the_evidence_legend_can_be_sent_to_the_commitments_call(self) -> None:
        manifest = base_manifest()
        manifest["kinds"][0]["commitment_ports"] = ["evidence"]
        _, outcome, recorder = self._run(manifest, self._script())
        second = [brief for stage, phase, brief in recorder.seen if stage == "c1" and phase == "commitments"][0]
        self.assertIn("first paragraph", second)

    def test_the_record_says_what_the_second_call_saw(self) -> None:
        """C14: written blind is read off the record, not assumed from a default."""

        manifest = base_manifest()
        manifest["kinds"][0]["commitment_ports"] = ["problem"]
        _, outcome, _ = self._run(manifest, self._script())
        seen = {
            event["kind_id"]: event["payload"]["commitment_ports"]
            for event in self.events_of(outcome, ARTIFACT_SUBMITTED)
        }
        self.assertEqual(seen["k.conjecture"], ["problem"])
        self.assertEqual(seen["k.criticism"], [])

    def test_a_commitment_port_the_kind_does_not_declare_is_refused(self) -> None:
        manifest = base_manifest()
        manifest["kinds"][0]["commitment_ports"] = ["nowhere"]
        self.assertRefuses("MINI_PORT_UNKNOWN", self.compile, manifest)

    def test_the_declared_ports_are_on_the_run_header(self) -> None:
        manifest = base_manifest()
        manifest["kinds"][0]["commitment_ports"] = ["problem"]
        plan = self.compile(manifest)
        self.assertEqual(plan.kinds["k.conjecture"].to_dict()["commitment_ports"], ["problem"])
