"""One regression per audit finding, each failing on the behaviour it fixes.

The audit ran copied fragments against doubles. These run the real package, and
each is written so that reverting the repair turns it red.
"""

from __future__ import annotations

import copy
import json

from creib.forge.mini.executor import (
    BODY_SCHEMA,
    COMMITMENTS_SCHEMA,
    LiveResponder,
    Request,
    contract_for,
)
from creib.forge.mini.kinds import kind_from_dict
from creib.forge.mini.log import ARTIFACT_SUBMITTED, REFUSED, RUN_ENDED, BlobStore
from creib.forge.mini.manifest import Stage, VERDICT_KIND_ID
from creib.forge.mini.runner import _offered

from pathlib import Path

from .helpers import CONJECTURE_KIND, MiniTestCase, base_manifest, submission

ROOT = Path(__file__).resolve().parents[2]

KEYWORD = {"body": {"all_of": [{"check": "keywords", "keywords": ["BECAUSE"]}]}}


def _kind(**extra):
    raw = copy.deepcopy(CONJECTURE_KIND)
    raw.update(extra)
    return kind_from_dict(raw, "kind")


class F1IdentityBindsTheFormatTests(MiniTestCase):
    """A kind's rules are part of what a run is, wherever the kind was loaded from."""

    def test_two_kinds_differing_only_in_format_serialise_differently(self) -> None:
        alpha = _kind(format={"body": {"all_of": [{"check": "keywords", "keywords": ["ALPHA"]}]}})
        beta = _kind(format={"body": {"all_of": [{"check": "keywords", "keywords": ["BETA"]}]}})
        self.assertNotEqual(alpha.to_dict(), beta.to_dict())

    def test_a_freeform_kind_adds_no_key(self) -> None:
        """An absent format changes no identity, so published records still replay."""

        self.assertNotIn("format", _kind().to_dict())

    def test_a_format_only_edit_to_an_external_kind_file_moves_the_run_identity(self) -> None:
        """The manifest is byte-identical; only the file it names changed."""

        manifest = base_manifest()
        manifest["kinds"] = ["kinds/conjecture.json", copy.deepcopy(manifest["kinds"][1])]

        def compile_with(keyword: str) -> str:
            raw = copy.deepcopy(CONJECTURE_KIND)
            raw["format"] = {"body": {"all_of": [{"check": "keywords", "keywords": [keyword]}]}}
            self.write_json("kinds/conjecture.json", {"schema_version": "creib.mini.kind.v1", "kind": raw})
            return self.compile(copy.deepcopy(manifest)).genesis

        first, second = compile_with("ALPHA"), compile_with("BETA")
        self.assertNotEqual(first, second)

    def test_an_unchanged_kind_file_keeps_its_identity(self) -> None:
        manifest = base_manifest()
        first = self.compile(copy.deepcopy(manifest)).genesis
        second = self.compile(copy.deepcopy(manifest)).genesis
        self.assertEqual(first, second)


class F2CommitmentPortsArePreflightedTests(MiniTestCase):
    """A configurable second-call input is still an input the policy governs."""

    def _manifest(self) -> dict:
        manifest = base_manifest()
        manifest["kinds"][0]["commitment_ports"] = ["evidence"]
        manifest["stages"][0]["ports"] = ["problem"]
        manifest["policy"] = {
            "base": "mini.policy.default.v1",
            "grants": [{"kind_id": "k.conjecture", "may_read_port_types": ["problem"]}],
        }
        return manifest

    def test_a_denied_commitment_port_is_refused_before_anything_is_dispatched(self) -> None:
        _, outcome = self.run_manifest(self._manifest(), {"x1": [submission("b", "c")]})
        refusals = [event for event in self.events_of(outcome, REFUSED) if event["stage_id"] == "c1"]
        self.assertEqual(len(refusals), 1)
        self.assertEqual(refusals[0]["payload"]["code"], "MINI_POLICY_READ_REFUSED")
        self.assertEqual(refusals[0]["payload"]["port_id"], "evidence")

    def test_the_denied_content_reaches_neither_dispatch(self) -> None:
        seen: list[str] = []

        class Recording:
            def __init__(self, inner) -> None:
                self._inner = inner

            def reply(self, request):
                seen.append(request.brief)
                return self._inner.reply(request)

        from creib.forge.mini.executor import ScriptedResponder
        from creib.forge.mini.runner import run_mini

        plan = self.compile(self._manifest())
        run_mini(plan, self.tmp / "run", Recording(ScriptedResponder({"x1": [submission("b", "c")]})))
        for brief in seen:
            self.assertNotIn("first paragraph", brief)

    def test_an_authorised_commitment_port_still_works(self) -> None:
        manifest = self._manifest()
        manifest["policy"]["grants"][0]["may_read_port_types"] = ["problem", "evidence_legend"]
        _, outcome = self.run_manifest(manifest, {"c1": [submission("b", "c")], "x1": [submission("b", "c")]})
        self.assertEqual([e for e in self.events_of(outcome, REFUSED) if e["stage_id"] == "c1"], [])

    def test_an_unused_commitment_port_is_not_checked(self) -> None:
        """A single-call kind never reads them, and refusing it would refuse a legal run."""

        manifest = self._manifest()
        manifest["kinds"][0]["commitment_call"] = "single"
        _, outcome = self.run_manifest(manifest, {"c1": [submission("b", "c")], "x1": [submission("b", "c")]})
        self.assertEqual([e for e in self.events_of(outcome, REFUSED) if e["stage_id"] == "c1"], [])


class F3RetriesAreCountedTests(MiniTestCase):
    def _manifest(self, max_calls: int) -> dict:
        manifest = base_manifest()
        manifest["kinds"][0]["format"] = copy.deepcopy(KEYWORD)
        manifest["kinds"][0]["failure_policy"] = {"retries": 1}
        manifest["kinds"][0]["commitment_call"] = "single"
        manifest["kinds"][1]["commitment_call"] = "single"
        manifest["cycles"] = {"max_cycles": 5 if max_calls < 99 else 1, "max_calls": max_calls}
        return manifest

    def test_a_retry_that_succeeded_counts_as_two_invocations(self) -> None:
        script = {
            "c1": {str(cycle): [submission("nothing", "c"), submission("BECAUSE", "c")] for cycle in range(1, 6)},
            "x1": {str(cycle): [submission("b", "c")] for cycle in range(1, 6)},
        }
        _, outcome = self.run_manifest(self._manifest(3), script)
        # One cycle costs three invocations: two for the retried body, one for
        # the critic. A budget of three must therefore stop the second cycle.
        self.assertEqual(outcome.stop_reason, "budget_cap")
        self.assertEqual(outcome.cycles_completed, 1)

    def test_the_record_carries_the_invocation_count(self) -> None:
        script = {
            "c1": {"1": [submission("nothing", "c"), submission("BECAUSE", "c")]},
            "x1": {"1": [submission("b", "c")]},
        }
        _, outcome = self.run_manifest(self._manifest(99), script)
        submitted = [e for e in self.events_of(outcome, ARTIFACT_SUBMITTED) if e["kind_id"] == "k.conjecture"][0]
        self.assertEqual(submitted["payload"]["calls"][0]["invocations"], 2)


class F4ThePhaseDecidesTheContractTests(MiniTestCase):
    class _Stub:
        def __init__(self) -> None:
            self.seen = []

        def complete(self, request):
            from creib.forge.conformance.executor import ChatResponse

            self.seen.append(request)
            return ChatResponse(
                content='{"commitments": "c"}' if "COMMITMENTS" in request.system else '{"body": "b"}',
                thinking_present=False,
                done=True,
                done_reason="stop",
                prompt_eval_count=1,
                eval_count=1,
                total_duration_ns=None,
                http_status=200,
                transport_error=None,
                response_digest="0" * 64,
            )

    def test_a_commitments_call_asks_for_commitments_only(self) -> None:
        stub = self._Stub()
        LiveResponder("m", stub).reply(Request("s", "k", 0, "brief", cycle=1, phase="commitments"))
        request = stub.seen[0]
        self.assertEqual(request.format_schema["required"], ["commitments"])
        self.assertFalse(request.format_schema.get("properties", {}).get("body"))
        self.assertNotIn("citations", request.system)

    def test_a_body_call_asks_for_a_body(self) -> None:
        stub = self._Stub()
        LiveResponder("m", stub).reply(Request("s", "k", 0, "brief", cycle=1, phase="body"))
        self.assertEqual(stub.seen[0].format_schema["required"], ["body"])
        self.assertIn("citations", stub.seen[0].system)

    def test_the_whole_artifact_contract_is_unchanged(self) -> None:
        stub = self._Stub()
        LiveResponder("m", stub).reply(Request("s", "k", 0, "brief", cycle=1, phase="both"))
        self.assertEqual(stub.seen[0].format_schema["required"], ["body", "commitments"])

    def test_the_brief_and_the_schema_agree_about_the_second_call(self) -> None:
        """The contradiction the audit found: a brief asking for one field and a
        schema requiring two."""

        self.assertEqual(COMMITMENTS_SCHEMA["required"], ["commitments"])
        self.assertFalse(COMMITMENTS_SCHEMA["additionalProperties"])
        self.assertEqual(BODY_SCHEMA["required"], ["body"])

    def test_an_unknown_phase_is_refused_rather_than_silently_contracted(self) -> None:
        self.assertRefuses("MINI_LIVE_CALL_FAILED", contract_for, "sideways")


class F5NothingIsOfferedAfterTheVerdictTests(MiniTestCase):
    class _Plan:
        def __init__(self, stages) -> None:
            self._stages = {stage.stage_id: stage for stage in stages}

        def stage(self, stage_id):
            return self._stages[stage_id]

    def _plan(self):
        end = Stage("end", None, (), True)
        work = Stage("c1", "k.conjecture", ("p",), False, max_repeats=2)
        verdict = Stage("verdict", VERDICT_KIND_ID, ("p",), False, max_repeats=1)
        return self._Plan([work, verdict, end]), work, verdict, end

    def test_an_end_only_remainder_offers_nothing(self) -> None:
        plan, _, _, end = self._plan()
        self.assertEqual(_offered(plan, [end], {"c1": 0, "verdict": 0}), ())

    def test_the_verdict_is_never_offered_as_a_repeat(self) -> None:
        plan, work, verdict, end = self._plan()
        offered = _offered(plan, [work, verdict, end], {"verdict": 0})
        self.assertNotIn(VERDICT_KIND_ID, [item.kind_id for item in offered])

    def test_ordinary_repeats_are_still_offered_before_the_verdict(self) -> None:
        plan, work, verdict, end = self._plan()
        offered = _offered(plan, [work, verdict, end], {"c1": 0})
        self.assertEqual([item.stage_id for item in offered], ["c1", "c1"])

    def test_an_adversarial_policy_cannot_reopen_a_finished_cycle(self) -> None:
        """A policy that takes every opportunity offered, rather than a
        well-behaved one whose preferences may avoid the defect."""

        from creib.forge.mini.attention import AttentionPolicy, register_attention_policy

        register_attention_policy(
            AttentionPolicy(
                "mini.attention.test-greedy",
                (),
                "takes the last opportunity offered, always",
                lambda signals, stages: stages[-1].stage_id if stages else None,
            )
        )
        manifest = base_manifest()
        manifest["attention"] = {"policy": "mini.attention.test-greedy"}
        manifest["stages"][0]["max_repeats"] = 3
        manifest["stages"][1]["max_repeats"] = 3
        script = {
            "c1": {"1": [submission("a", "c")] * 8},
            "x1": {"1": [submission("b", "c")] * 8},
        }
        _, outcome = self.run_manifest(manifest, script)
        self.assertEqual(outcome.stages_entered[-1], "verdict")
        self.assertEqual(outcome.stages_entered.count("verdict"), 1)


class F6TheRecordedRequestIsTheOneThatWasSentTests(MiniTestCase):
    def _manifest(self) -> dict:
        manifest = base_manifest()
        manifest["kinds"][0]["format"] = copy.deepcopy(KEYWORD)
        manifest["kinds"][0]["failure_policy"] = {"retries": 1}
        return manifest

    def _submitted(self, outcome):
        return [e for e in self.events_of(outcome, ARTIFACT_SUBMITTED) if e["kind_id"] == "k.conjecture"][0]

    def test_the_recorded_request_is_the_retry_that_was_accepted(self) -> None:
        script = {
            "c1": {"1": [submission("nothing", "c"), submission("BECAUSE", "c")]},
            "x1": {"1": [submission("b", "c")]},
        }
        _, outcome = self.run_manifest(self._manifest(), script)
        call = self._submitted(outcome)["payload"]["calls"][0]
        sent = BlobStore(outcome.root / "blobs").get(call["request_ref"]).decode("utf-8")
        self.assertIn("was refused, for these reasons", sent)

    def test_a_first_time_acceptance_records_the_plain_brief(self) -> None:
        script = {"c1": {"1": [submission("BECAUSE", "c")]}, "x1": {"1": [submission("b", "c")]}}
        _, outcome = self.run_manifest(self._manifest(), script)
        call = self._submitted(outcome)["payload"]["calls"][0]
        sent = BlobStore(outcome.root / "blobs").get(call["request_ref"]).decode("utf-8")
        self.assertNotIn("was refused, for these reasons", sent)

    def test_usage_covers_every_attempt_not_only_the_accepted_one(self) -> None:
        script = {
            "c1": {"1": [submission("nothing", "c"), submission("BECAUSE", "c")]},
            "x1": {"1": [submission("b", "c")]},
        }
        _, outcome = self.run_manifest(self._manifest(), script)
        call = self._submitted(outcome)["payload"]["calls"][0]
        self.assertEqual([item["attempt"] for item in call["usage"]], [0, 1])
        self.assertEqual(
            self._submitted(outcome)["payload"]["completion_tokens"],
            sum(item["completion_tokens"] for entry in self._submitted(outcome)["payload"]["calls"] for item in entry["usage"]),
        )

    def test_a_dropped_submission_keeps_every_attempt_usage_too(self) -> None:
        script = {"c1": {"1": [submission("nothing", "c")] * 2}, "x1": {"1": [submission("b", "c")]}}
        _, outcome = self.run_manifest(self._manifest(), script)
        dropped = [e for e in self.events_of(outcome, "SUBMISSION_DROPPED") if e["kind_id"] == "k.conjecture"][0]
        self.assertEqual([item["attempt"] for item in dropped["payload"]["usage"]], [0, 1])


class FAudit20260910Tests(MiniTestCase):
    """The audit of 10 September 2026, one regression per finding it established.

    Each of these fails on the behaviour it repairs. The audit's own probes ran adapted
    fragments against doubles; these run the package.
    """

    def _two_call_manifest(self):
        manifest = base_manifest()
        manifest["kinds"][0]["commitment_call"] = "two"
        return manifest

    def test_f_g_a_successful_body_call_keeps_its_record_when_the_commitments_fail(self) -> None:
        """F-G: the drop path admitted no artifact, so the body call it had paid for vanished."""

        script = {
            "c1": [submission("a body", "unused")] * 2,
            "c1@commitments": ["not a submission at all"] * 2,
            "x1": [submission("b", "c")],
        }
        _, outcome = self.run_manifest(self._two_call_manifest(), script)
        dropped = [e for e in self.events_of(outcome, "SUBMISSION_DROPPED") if e["kind_id"] == "k.conjecture"]
        self.assertEqual(len(dropped), 1)
        calls = dropped[0]["payload"]["calls"]
        self.assertEqual([item["phase"] for item in calls], ["body"], "the body call that succeeded is on the record")
        self.assertTrue(calls[0]["reply_ref"], "with the reply it was answered with")
        self.assertEqual(calls[0]["invocations"], 1)
        self.assertEqual(dropped[0]["payload"]["phase"], "commitments", "and the phase that failed is named")

    def test_f_f_a_cycle_that_runs_out_of_steps_is_not_counted_as_completed(self) -> None:
        """F-F: the step limit ended a cycle silently and the outer counter called it done."""

        from unittest.mock import patch

        import creib.forge.mini.runner as runner

        manifest = base_manifest()
        manifest["cycles"] = {"max_cycles": 3}
        script = {"c1": {str(cycle): [submission("a body", "c")] for cycle in (1, 2, 3)}, "x1": {str(cycle): [submission("b", "c")] for cycle in (1, 2, 3)}}
        with patch.object(runner, "MAX_STEPS", 1):
            plan, outcome = self.run_manifest(manifest, script)
        ended = self.events_of(outcome, RUN_ENDED)[0]["payload"]
        self.assertEqual(ended["stop_reason"], "steps_exhausted")
        self.assertEqual(ended["cycles_completed"], 0, "the cycle that never reached its verdict is not one of them")
        self.assertEqual(outcome.stop_reason, "steps_exhausted")

    def test_f_c_two_artifacts_that_would_execute_differently_have_different_identities(self) -> None:
        """F-C: identity was body and commitments, so the executable fields could differ freely."""

        from creib.forge.mini.kinds import Submission
        from creib.forge.mini.log import BlobStore as Store
        from creib.forge.mini.runner import _store_artifact

        blobs = Store(self.tmp / "blobs")
        stage = Stage(stage_id="propose", kind_id="k.conjecture", ports=(), seat="model", end=False)

        def stored(rewritten: str) -> str:
            submitted = Submission(body="a body", commitments="a commitment", citations=(), about=(), answers=(), extra={"input": "x", "rewritten": rewritten})
            return _store_artifact(blobs, stage, submitted, 3)[0]

        self.assertNotEqual(stored('{"a": 1}'), stored('{"b": 2}'))
        self.assertEqual(stored('{"a": 1}'), stored('{"a": 1}'), "and the identity is still of the content")

    def test_f_c_a_seat_shown_an_artifact_is_shown_what_will_be_executed(self) -> None:
        """F-C: a port rendered body and commitments, never the fields a machine seat runs."""

        from creib.forge.mini.log import replay
        from creib.forge.mini.runner import render_brief

        manifest = base_manifest()
        manifest["kinds"][0]["optional_fields"] = ["input", "rewritten"]
        script = {"c1": [submission("a body", "a commitment", input='{"a": 1}', rewritten='```\n{"a": 1}\n```')], "x1": [submission("b", "c")]}
        plan, outcome = self.run_manifest(manifest, script)
        state = replay(outcome.root / "log.jsonl", plan.genesis)
        brief, _ = render_brief(plan, state, BlobStore(outcome.root / "blobs"), plan.stage("x1"), 1)
        self.assertIn('input: {"a": 1}', brief)
        self.assertIn("rewritten: ```", brief, "the critic sees the text that will be run, not only the prose about it")

    def test_f_e_the_comparison_says_only_what_its_gate_checked(self) -> None:
        """F-E: it announced that both roots were asked the same way, having checked neither."""

        from creib.forge.mini.compare import compare_roots

        manifest = base_manifest()
        script = {"c1": [submission("a body", "c")], "x1": [submission("b", "c")]}
        plan, first = self.run_manifest(manifest, script, name="left")
        asked_otherwise = copy.deepcopy(manifest)
        asked_otherwise["problem"] = "A different question entirely, put to the same model."
        _, second = self.run_manifest(asked_otherwise, script, name="right")
        rendered = compare_roots(first.root, second.root)
        self.assertIn("answered by the same responder", rendered)
        self.assertIn("Their manifests differ", rendered, "the report does not claim they were asked the same question")
        self.assertNotIn("asked the same way", rendered)

    def test_f_e_the_ledger_reads_both_executor_kinds_and_carries_its_witness(self) -> None:
        """F-E: it read only the transform executor, so every later experiment's ledger was empty."""

        from creib.forge.mini.compare import read_root
        from creib.forge.mini.report import read_run

        root = ROOT / "forge" / "mini" / "runs" / "experiments" / "round-5" / "r5-3-skeletons-fields-gemma"
        self.assertTrue(read_run(root).executions, "this run executed pairs, not transforms")
        reading = read_root(root)
        self.assertTrue(reading.ledger, "and its unchanged pairs now reach the ledger")
        self.assertTrue(all(entry["input"] for entry in reading.ledger), "each row carries the input it was run on")
        self.assertTrue(reading.manifest_digest)
