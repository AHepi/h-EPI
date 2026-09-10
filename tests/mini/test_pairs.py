"""Pair proposals: the proposer writes the rewrite, the executor runs the kernel on both texts,
and the verdict reads the result against what the proposer expected.

No transform registry stands between a proposer and the check, so a rewrite nobody registered
can be proposed. Repeats are named, not re-run (mini register M10). The source-emitting seat
puts the checks' code in front of a proposer as an artifact, whole, where the legend would show
160 characters. The grounding kernels read a JSON object and answer as the harness does.
"""

from __future__ import annotations

import hashlib
import json

from creib.forge.mini import conformance_kernels as kernels
from creib.forge.mini.blindspot import (
    EXECUTION_KIND,
    PAIR_EXECUTION_KIND,
    STANDING_CANDIDATE,
    STANDING_REJECTED,
    VERDICT_KIND,
    resolve_kernel,
    standing_for_pair,
)
from creib.forge.mini.log import BlobStore, replay

from .helpers import MiniTestCase, submission

OBJECT = '{"claimant_name": "amara okoro", "total_days": "five"}'


def _pair_manifest(cycles: int = 1) -> dict:
    proposal = {
        "kind_id": "mini.pair-proposal.recovery.v1",
        "title": "Proposal",
        "commitment_call": "single",
        "input_ports": [
            {"port_id": "problem", "port_type": "problem"},
            {"port_id": "source", "port_type": "kernel_source", "window": "this_cycle"},
        ],
        "output_port": {"port_id": "out", "produces_kind": "mini.pair-proposal.recovery.v1"},
    }
    return {
        "schema_version": "creib.mini.manifest.v1",
        "manifest_id": "test.pairs",
        "problem": "Find a rewrite the recovery check cannot see.",
        "cycles": {"max_cycles": cycles},
        "port_types": [
            {"port_type": "kernel_source", "draws_from": {"artifact_kinds": [kernels.KERNEL_SOURCE_KIND]}, "render": {"rule": "list_bodies", "header": "The source"}},
            {"port_type": "pair_proposals", "draws_from": {"artifact_kinds": ["mini.pair-proposal.recovery.v1"]}, "render": {"rule": "list_bodies_and_commitments", "header": "Proposals"}},
            {"port_type": "pair_executions", "draws_from": {"artifact_kinds": [PAIR_EXECUTION_KIND]}, "render": {"rule": "list_bodies_and_commitments", "header": "Executions"}},
        ],
        "kinds": [
            {"kind_id": kernels.KERNEL_SOURCE_KIND, "title": "Source", "input_ports": [], "output_port": {"port_id": "out", "produces_kind": kernels.KERNEL_SOURCE_KIND}},
            proposal,
            {"kind_id": PAIR_EXECUTION_KIND, "title": "Execution", "input_ports": [{"port_id": "proposals", "port_type": "pair_proposals", "window": "this_cycle"}], "output_port": {"port_id": "out", "produces_kind": PAIR_EXECUTION_KIND}},
            {"kind_id": VERDICT_KIND, "title": "Verdict", "input_ports": [{"port_id": "executions", "port_type": "pair_executions", "window": "this_cycle"}], "output_port": {"port_id": "out", "produces_kind": VERDICT_KIND}},
        ],
        "stages": [
            {"stage_id": "source", "kind_id": kernels.KERNEL_SOURCE_KIND, "seat": "machine", "ports": []},
            {"stage_id": "propose", "kind_id": "mini.pair-proposal.recovery.v1", "ports": ["problem", "source"]},
            {"stage_id": "execute", "kind_id": PAIR_EXECUTION_KIND, "seat": "machine", "ports": ["proposals"]},
            {"stage_id": "verdict", "kind_id": VERDICT_KIND, "seat": "machine", "ports": ["executions"]},
            {"stage_id": "end", "end": True},
        ],
    }


def _proposal(kernel: str, source: str, rewritten: str, expect: str) -> str:
    return submission("a body", json.dumps({"kernel": kernel, "input": source, "rewritten": rewritten, "expect": expect, "rewrite": "test"}))


class PairExecutionTests(MiniTestCase):
    def _run(self, replies: dict[str, list[str]], cycles: int = 1, name: str = "run"):
        plan, outcome = self.run_manifest(_pair_manifest(cycles), replies, name=name)
        state = replay(outcome.root / "log.jsonl", plan.genesis)
        blobs = BlobStore(outcome.root / "blobs")
        executions = [json.loads(blobs.get(r["commitments_ref"]).decode("utf-8"))["executions"] for r in state.artifacts.values() if r["kind_id"] == PAIR_EXECUTION_KIND]
        verdicts = [json.loads(blobs.get(r["commitments_ref"]).decode("utf-8"))["verdicts"] for r in state.artifacts.values() if r["kind_id"] == VERDICT_KIND]
        return state, [e for batch in executions for e in batch], [v for batch in verdicts for v in batch]

    def test_the_kernel_runs_on_both_texts_and_the_verdict_reads_the_expectation(self) -> None:
        h44 = "```json\nthe form:\n" + OBJECT + "\n``` then {\"later\": 1}"
        state, executions, verdicts = self._run({"propose": [_proposal(kernels.KERNEL_RECOVERY, OBJECT, h44, "unchanged")]})
        self.assertEqual(len(executions), 1)
        self.assertEqual((executions[0]["executed"], executions[0]["as_expected"]), ("moved", False))
        self.assertEqual((verdicts[0]["standing"], verdicts[0]["column"], verdicts[0]["expected"]), (STANDING_CANDIDATE, "moves", "unchanged"))
        self.assertFalse(verdicts[0]["catalogued"])

    def test_an_expected_movement_that_does_not_happen_is_a_candidate_for_the_unchanged_column(self) -> None:
        state, executions, verdicts = self._run({"propose": [_proposal(kernels.KERNEL_RECOVERY, OBJECT, OBJECT + "\nThat is all.", "moves")]})
        self.assertEqual(executions[0]["executed"], "unchanged")
        self.assertEqual((verdicts[0]["standing"], verdicts[0]["column"]), (STANDING_CANDIDATE, "unchanged"))

    def test_agreement_adds_no_row(self) -> None:
        state, executions, verdicts = self._run({"propose": [_proposal(kernels.KERNEL_RECOVERY, OBJECT, OBJECT.upper(), "moves")]})
        self.assertEqual((executions[0]["executed"], verdicts[0]["standing"], verdicts[0]["column"]), ("moved", STANDING_REJECTED, None))

    def test_a_repeat_across_cycles_is_named_and_not_re_run(self) -> None:
        reply = _proposal(kernels.KERNEL_RECOVERY, OBJECT, OBJECT.upper(), "moves")
        state, executions, verdicts = self._run({"propose": [reply, reply]}, cycles=2)
        self.assertEqual([e["executed"] for e in executions], ["moved", "duplicate"])
        self.assertEqual([v["standing"] for v in verdicts], [STANDING_REJECTED, STANDING_REJECTED])

    def test_an_unchanged_rewrite_an_unknown_kernel_and_a_bad_expectation_are_unrunnable(self) -> None:
        state, executions, verdicts = self._run({"propose": [_proposal(kernels.KERNEL_RECOVERY, OBJECT, OBJECT, "moves")]})
        self.assertEqual(executions[0]["executed"], "unrunnable")
        state, executions, verdicts = self._run({"propose": [_proposal("conformance.kernel.nothing", OBJECT, "x", "moves")]}, name="unknown")
        self.assertEqual(executions[0]["executed"], "unrunnable")
        state, executions, verdicts = self._run({"propose": [_proposal(kernels.KERNEL_RECOVERY, OBJECT, "x", "maybe")]}, name="expect")
        self.assertEqual(executions[0]["executed"], "unrunnable")
        self.assertEqual(standing_for_pair("unrunnable", "moves"), STANDING_REJECTED)

    def test_the_source_seat_puts_the_code_in_the_proposers_brief(self) -> None:
        from creib.forge.mini.runner import render_brief

        plan, outcome = self.run_manifest(_pair_manifest(), {"propose": [_proposal(kernels.KERNEL_RECOVERY, OBJECT, OBJECT.upper(), "moves")]})
        state = replay(outcome.root / "log.jsonl", plan.genesis)
        blobs = BlobStore(outcome.root / "blobs")
        source = next(r for r in state.artifacts.values() if r["kind_id"] == kernels.KERNEL_SOURCE_KIND)
        body = blobs.get(source["body_ref"]).decode("utf-8")
        self.assertEqual(body, kernels.kernel_source_text())
        self.assertIn("def recover_json_object", body)
        self.assertIn(hashlib.sha256(body.encode("utf-8")).hexdigest(), blobs.get(source["commitments_ref"]).decode("utf-8"))
        brief, _ = render_brief(plan, state, blobs, plan.stage("propose"), 1)
        self.assertIn("def refusal_phrase_in", brief)


class TransformDuplicateTests(MiniTestCase):
    def test_a_repeated_triple_is_named_and_not_re_run(self) -> None:
        from pathlib import Path
        from creib.strict_json import load_strict

        root = Path(__file__).resolve().parents[2]
        manifest = dict(load_strict(root / "forge" / "mini" / "manifests" / "conformance-blind-spot" / "manifest.json"))
        manifest["sources"] = [{"source_id": item["source_id"], "text": (root / "forge" / "mini" / "manifests" / "conformance-blind-spot" / item["path"]).read_text(encoding="utf-8")} for item in manifest["sources"]]
        manifest["cycles"] = {"max_cycles": 2}
        triple = json.dumps({"kernel": kernels.KERNEL_RECOVERY, "transform": "conformance.transform.upper-case", "input": OBJECT})
        reply = submission("the same again", triple)
        script = {stage: [reply] * 2 for stage in ("propose-1", "propose-2", "propose-3")}
        script["criticise"] = [submission("c", "c")] * 2
        script["criticise@commitments"] = [json.dumps({"commitments": "c"})] * 2
        plan, outcome = self.run_manifest(manifest, script)
        state = replay(outcome.root / "log.jsonl", plan.genesis)
        blobs = BlobStore(outcome.root / "blobs")
        executed = [e["executed"] for r in state.artifacts.values() if r["kind_id"] == EXECUTION_KIND for e in json.loads(blobs.get(r["commitments_ref"]).decode("utf-8"))["executions"]]
        self.assertEqual(executed, ["moved", "duplicate", "duplicate", "duplicate", "duplicate", "duplicate"])


class GroundingKernelTests(MiniTestCase):
    def test_the_grounding_kernels_answer_as_the_harness_does(self) -> None:
        grounding = resolve_kernel(kernels.KERNEL_GROUNDING).verdict
        occurs = resolve_kernel(kernels.KERNEL_SPAN_OCCURS).verdict
        document = "Claimant: amara okoro, away for five days."
        self.assertEqual(grounding(json.dumps({"value": "Amara Okoro", "span": "amara  okoro", "document": document})), "GROUNDED", "G-01: whitespace normalised, value case-insensitive")
        self.assertEqual(grounding(json.dumps({"value": "amara", "span": "Amara okoro", "document": document})), "SPAN_NOT_IN_DOCUMENT", "G-04: the span's occurrence is case-sensitive without a relaxation")
        self.assertEqual(grounding(json.dumps({"value": "five", "span": "amara okoro", "document": document})), "VALUE_NOT_IN_SPAN")
        self.assertEqual(grounding(json.dumps({"value": "five", "span": "  ", "document": document})), "SPAN_MISSING")
        self.assertEqual(occurs(json.dumps({"span": "five   days", "document": document})), "verbatim")
        self.assertEqual(occurs(json.dumps({"span": "six days", "document": document})), "NOT_IN_DOCUMENT")
        self.assertEqual(grounding("not json"), kernels.UNREADABLE)
        self.assertEqual(occurs(json.dumps({"span": 3, "document": document})), kernels.UNREADABLE)
