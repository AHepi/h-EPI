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
    READING_ABSENT,
    READING_AGREE,
    READING_CODE_MISREAD,
    READING_NEITHER,
    READING_RULE_DIVERGES,
    READING_UNREADABLE,
    STANDING_CANDIDATE,
    STANDING_REJECTED,
    VERDICT_KIND,
    reading_for,
    resolve_kernel,
    standing_for_pair,
)
from creib.forge.mini.log import BlobStore, replay

from .helpers import MiniTestCase, submission

OBJECT = '{"claimant_name": "amara okoro", "total_days": "five"}'


PREDICTION_KIND = "mini.pair-prediction.v1"


def _pair_manifest(cycles: int = 1, predict: bool = False, rules: bool = False,
                   window: str = "this_cycle", execute_first: bool = False) -> dict:
    shown = kernels.KERNEL_RULES_KIND if rules else kernels.KERNEL_SOURCE_KIND
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
    prediction = {
        "kind_id": PREDICTION_KIND,
        "title": "Prediction",
        "commitment_call": "single",
        "input_ports": [{"port_id": "proposals", "port_type": "pair_proposals", "window": "this_cycle"}],
        "output_port": {"port_id": "out", "produces_kind": PREDICTION_KIND},
    }
    manifest = {
        "schema_version": "creib.mini.manifest.v1",
        "manifest_id": "test.pairs",
        "problem": "Find a rewrite the recovery check cannot see.",
        "cycles": {"max_cycles": cycles},
        "port_types": [
            {"port_type": "kernel_source", "draws_from": {"artifact_kinds": [shown]}, "render": {"rule": "list_bodies", "header": "The source"}},
            {"port_type": "pair_proposals", "draws_from": {"artifact_kinds": ["mini.pair-proposal.recovery.v1"]}, "render": {"rule": "list_bodies_and_commitments", "header": "Proposals"}},
            {"port_type": "pair_executions", "draws_from": {"artifact_kinds": [PAIR_EXECUTION_KIND]}, "render": {"rule": "list_bodies_and_commitments", "header": "Executions"}},
        ],
        "kinds": [
            {"kind_id": shown, "title": "Source", "input_ports": [], "output_port": {"port_id": "out", "produces_kind": shown}},
            proposal,
            {"kind_id": PAIR_EXECUTION_KIND, "title": "Execution", "input_ports": [{"port_id": "proposals", "port_type": "pair_proposals", "window": window}], "output_port": {"port_id": "out", "produces_kind": PAIR_EXECUTION_KIND}},
            {"kind_id": VERDICT_KIND, "title": "Verdict", "input_ports": [{"port_id": "executions", "port_type": "pair_executions", "window": "this_cycle"}], "output_port": {"port_id": "out", "produces_kind": VERDICT_KIND}},
        ],
        "stages": [
            {"stage_id": "source", "kind_id": shown, "seat": "machine", "ports": []},
            {"stage_id": "propose", "kind_id": "mini.pair-proposal.recovery.v1", "ports": ["problem", "source"]},
            {"stage_id": "execute", "kind_id": PAIR_EXECUTION_KIND, "seat": "machine", "ports": ["proposals"]},
            {"stage_id": "verdict", "kind_id": VERDICT_KIND, "seat": "machine", "ports": ["executions"]},
            {"stage_id": "end", "end": True},
        ],
    }
    if predict:
        manifest["kinds"].insert(2, prediction)
        manifest["stages"].insert(2, {"stage_id": "predict", "kind_id": PREDICTION_KIND, "ports": ["proposals"]})
    if execute_first:
        stages = manifest["stages"]
        stages.insert(stages.index(next(s for s in stages if s["stage_id"] == "propose")), stages.pop(
            stages.index(next(s for s in stages if s["stage_id"] == "execute"))))
    return manifest


def _proposal(kernel: str, source: str, rewritten: str, expect: str) -> str:
    return submission("a body", json.dumps({"kernel": kernel, "input": source, "rewritten": rewritten, "expect": expect, "rewrite": "test"}))


class PairExecutionTests(MiniTestCase):
    def _run(self, replies: dict[str, list[str]], cycles: int = 1, name: str = "run", predict: bool = False):
        plan, outcome = self.run_manifest(_pair_manifest(cycles, predict=predict), replies, name=name)
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

    def test_an_execute_stage_before_the_proposer_runs_an_earlier_cycles_proposal_if_its_window_admits_it(self) -> None:
        """M22. The seat read this cycle whatever the stage declared, so half the sweep's lattice was dead.

        With ``execute`` ordered before ``propose`` the edge is lagged: nothing is there to run in
        the first cycle, and the second cycle's execute must reach the first cycle's proposal. It
        does so only because the port says ``all``; the companion test below is the same ordering
        with ``this_cycle`` declared, where nothing runs, ever.
        """

        reply = _proposal(kernels.KERNEL_RECOVERY, OBJECT, OBJECT.upper(), "moves")
        plan, outcome = self.run_manifest(
            _pair_manifest(cycles=2, window="all", execute_first=True), {"propose": [reply, reply]}, name="lagged-all")
        state = replay(outcome.root / "log.jsonl", plan.genesis)
        blobs = BlobStore(outcome.root / "blobs")
        rows = [e for r in state.artifacts.values() if r["kind_id"] == PAIR_EXECUTION_KIND
                for e in json.loads(blobs.get(r["commitments_ref"]).decode("utf-8"))["executions"]]
        self.assertEqual([e["executed"] for e in rows], ["moved"])

    def test_the_same_ordering_with_this_cycle_declared_runs_nothing_at_all(self) -> None:
        reply = _proposal(kernels.KERNEL_RECOVERY, OBJECT, OBJECT.upper(), "moves")
        plan, outcome = self.run_manifest(
            _pair_manifest(cycles=2, window="this_cycle", execute_first=True), {"propose": [reply, reply]}, name="lagged-this")
        state = replay(outcome.root / "log.jsonl", plan.genesis)
        blobs = BlobStore(outcome.root / "blobs")
        rows = [e for r in state.artifacts.values() if r["kind_id"] == PAIR_EXECUTION_KIND
                for e in json.loads(blobs.get(r["commitments_ref"]).decode("utf-8"))["executions"]]
        self.assertEqual(rows, [])

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


    def test_an_input_the_kernel_cannot_read_is_unrunnable_not_a_move(self) -> None:
        readable = json.dumps({"value": "five", "span": "five days", "document": "away for five days."})
        state, executions, verdicts = self._run({"propose": [_proposal(kernels.KERNEL_GROUNDING, "not json at all", readable, "moves")]})
        self.assertEqual(executions[0]["executed"], "unrunnable")
        self.assertEqual((executions[0]["before"], executions[0]["after"]), (kernels.UNREADABLE, "GROUNDED"))
        self.assertIn("could not read the input", executions[0]["detail"])
        self.assertEqual((verdicts[0]["standing"], verdicts[0]["column"]), (STANDING_REJECTED, None))
        state, executions, verdicts = self._run({"propose": [_proposal(kernels.KERNEL_RECOVERY, "not json at all", readable, "moves")]}, name="recovery")
        self.assertEqual(executions[0]["executed"], "moved", "a kernel that declares no unreadable verdict moves as before")

    def test_a_prediction_is_read_beside_the_expectation(self) -> None:
        from creib.forge.mini.runner import run_mini

        h44 = "```json\nthe form:\n" + OBJECT + "\n``` then {\"later\": 1}"
        proposal = _proposal(kernels.KERNEL_RECOVERY, OBJECT, h44, "unchanged")
        plan = self.compile(_pair_manifest(predict=True))
        for expect, shown, reading, name in ((" moves", "?", READING_UNREADABLE, "bad"), ("moves", "moves", READING_RULE_DIVERGES, "code"), ("unchanged", "unchanged", READING_NEITHER, "neither")):
            outcome = run_mini(plan, self.tmp / name, _PredictingResponder({"propose": [proposal]}, expect))
            state = replay(outcome.root / "log.jsonl", plan.genesis)
            blobs = BlobStore(outcome.root / "blobs")
            verdict = [json.loads(blobs.get(r["commitments_ref"]).decode("utf-8"))["verdicts"] for r in state.artifacts.values() if r["kind_id"] == VERDICT_KIND][0][0]
            self.assertEqual((verdict["executed"], verdict["expected"], verdict["predicted"], verdict["reading"]), ("moved", "unchanged", shown, reading), name)
            self.assertEqual(verdict["standing"], STANDING_CANDIDATE, "the standing is the proposer's expectation against the machine; a prediction names a reading, never a standing")

    def test_a_prediction_naming_no_proposal_of_this_cycle_leaves_the_reading_absent(self) -> None:
        state, executions, verdicts = self._run(
            {"propose": [_proposal(kernels.KERNEL_RECOVERY, OBJECT, OBJECT.upper(), "moves")], "predict": [submission("p", json.dumps({"proposal": "0000000000000000", "expect": "moves"}))]},
            predict=True,
        )
        self.assertEqual((verdicts[0]["predicted"], verdicts[0]["reading"]), (None, READING_ABSENT))

    def test_the_readings_name_every_pairing(self) -> None:
        self.assertEqual(reading_for("moved", "moves", None), READING_ABSENT)
        self.assertEqual(reading_for("moved", "moves", "moves"), READING_AGREE)
        self.assertEqual(reading_for("moved", "unchanged", "moves"), READING_RULE_DIVERGES)
        self.assertEqual(reading_for("moved", "moves", "unchanged"), READING_CODE_MISREAD)
        self.assertEqual(reading_for("unchanged", "moves", "moves"), READING_NEITHER)
        self.assertEqual(reading_for("unrunnable", "moves", "moves"), READING_UNREADABLE)
        self.assertEqual(reading_for("moved", "moves", "?"), READING_UNREADABLE)

    def test_the_rules_seat_shows_the_docstrings_and_not_the_code(self) -> None:
        from creib.forge.mini.runner import render_brief

        plan, outcome = self.run_manifest(_pair_manifest(rules=True), {"propose": [_proposal(kernels.KERNEL_RECOVERY, OBJECT, OBJECT.upper(), "moves")]})
        state = replay(outcome.root / "log.jsonl", plan.genesis)
        blobs = BlobStore(outcome.root / "blobs")
        rules = next(r for r in state.artifacts.values() if r["kind_id"] == kernels.KERNEL_RULES_KIND)
        body = blobs.get(rules["body_ref"]).decode("utf-8")
        self.assertEqual(body, kernels.kernel_rules_text())
        self.assertIn("def recover_json_object", body)
        self.assertIn("last one inside a code fence", body, "the rule the H44 case is read against")
        self.assertNotIn("_FENCE.finditer", body)
        self.assertNotIn("return ", body)
        brief, _ = render_brief(plan, state, blobs, plan.stage("propose"), 1)
        self.assertIn("last one inside a code fence", brief)
        self.assertNotIn("_FENCE.finditer", brief)


class _PredictingResponder:
    """A scripted responder whose prediction names the proposal it was shown, read from the brief."""

    def __init__(self, script: dict, expect: str) -> None:
        from creib.forge.mini.executor import ScriptedResponder

        self._inner = ScriptedResponder(script)
        self._expect = expect

    def reply(self, request):
        import re

        from creib.forge.mini.executor import Reply

        if request.stage_id != "predict":
            return self._inner.reply(request)
        found = re.search(r"\b([0-9a-f]{16})\b", request.brief)
        text = submission("a prediction", json.dumps({"proposal": "" if found is None else found.group(1), "expect": self._expect}))
        return Reply(text=text, prompt_tokens=1, completion_tokens=1)


    def test_a_proposal_whose_json_carries_a_raw_line_break_is_run_not_called_unreadable(self) -> None:
        """M13: the executor reads the commitments the way the format layer read them."""

        with_break = json.dumps({"kernel": kernels.KERNEL_RECOVERY, "input": OBJECT, "rewritten": "```\n" + OBJECT + "\n```", "expect": "moves", "rewrite": "test"})
        raw = with_break.replace("\\n", "\n")
        self.assertIn("\n", json.loads(json.dumps(raw)), "the commitments string itself now carries the break")
        state, executions, verdicts = self._run({"propose": [submission("a body", raw)]})
        self.assertEqual(executions[0]["executed"], "unchanged", "the pair ran: a fence around the object does not move what is recovered")
        self.assertEqual(executions[0]["rewritten"], "```\n" + OBJECT + "\n```")


    def test_a_kind_may_carry_the_long_fields_beside_the_commitments(self) -> None:
        """M13: three levels of escaping become one when the kind declares the fields itself."""

        from creib.forge.mini.executor import contract_for
        from creib.forge.mini.runner import render_brief

        manifest = _pair_manifest()
        proposal = next(k for k in manifest["kinds"] if k["kind_id"] == "mini.pair-proposal.recovery.v1")
        proposal["optional_fields"] = ["input", "rewritten"]
        schema = proposal["format"]["commitments"]["all_of"][0]["schema"]
        schema["required"] = ["kernel", "expect", "rewrite"]
        for name in ("input", "rewritten"):
            schema["properties"].pop(name)
        reply = submission(
            "a body",
            json.dumps({"kernel": kernels.KERNEL_RECOVERY, "expect": "unchanged", "rewrite": "wrapped it in a fence"}),
            input=OBJECT,
            rewritten="```json\n" + OBJECT + "\n```",
        )
        plan, outcome = self.run_manifest(manifest, {"propose": [reply]})
        state = replay(outcome.root / "log.jsonl", plan.genesis)
        blobs = BlobStore(outcome.root / "blobs")
        executions = [e for r in state.artifacts.values() if r["kind_id"] == PAIR_EXECUTION_KIND for e in json.loads(blobs.get(r["commitments_ref"]).decode("utf-8"))["executions"]]
        self.assertEqual(executions[0]["executed"], "unchanged", "the pair ran from the artifact's own fields")
        self.assertEqual((executions[0]["input"], executions[0]["expect"]), (OBJECT, "unchanged"))

        brief, _ = render_brief(plan, state, blobs, plan.stage("propose"), 1)
        self.assertIn('This artifact also carries "input", "rewritten", each a string.', brief)
        _system, wire = contract_for("both", ("input", "rewritten"))
        self.assertEqual(wire["properties"]["input"], {"type": "string"})
        self.assertEqual(wire["required"], ["body", "commitments"], "an optional field is offered, never required")
        _blind_system, blind = contract_for("commitments", ("input",))
        self.assertNotIn("input", blind["properties"], "the blind commitments call is entitled to one field")


class NextCellTests(MiniTestCase):
    """The grid is enumerated by machine: each next-cell seat names the cell named least often."""

    def test_the_seat_walks_the_grid_and_starts_again_from_the_least_named(self) -> None:
        from creib.forge.mini.blindspot import NEXT_CELL_KINDS

        first, second = NEXT_CELL_KINDS[:2]
        manifest = _pair_manifest(cycles=2)
        manifest["sources"] = [{"source_id": "grid", "text": "object alone / nothing\n\nsentence then an object / a different bare object\n\nobject alone / a sentence\n"}]
        for kind_id in (first, second):
            manifest["port_types"].append({"port_type": "cell_" + kind_id, "draws_from": {"artifact_kinds": [kind_id]}, "render": {"rule": "list_bodies", "header": "Grid"}})
            manifest["kinds"].append({"kind_id": kind_id, "title": "Next cell", "input_ports": [], "output_port": {"port_id": "out", "produces_kind": kind_id}})
        proposal = next(k for k in manifest["kinds"] if k["kind_id"] == "mini.pair-proposal.recovery.v1")
        proposal["input_ports"].append({"port_id": "cell", "port_type": "cell_" + first, "window": "this_cycle"})
        second_proposal = json.loads(json.dumps(proposal))
        second_proposal["kind_id"] = second_proposal["output_port"]["produces_kind"] = "mini.pair-proposal.recovery-2.v1"
        second_proposal["input_ports"][-1] = {"port_id": "cell", "port_type": "cell_" + second, "window": "this_cycle"}
        manifest["kinds"].append(second_proposal)
        next(t for t in manifest["port_types"] if t["port_type"] == "pair_proposals")["draws_from"]["artifact_kinds"].append("mini.pair-proposal.recovery-2.v1")
        stages = manifest["stages"]
        propose = next(s for s in stages if s["stage_id"] == "propose")
        propose["ports"] = propose["ports"] + ["cell"]
        stages[1:2] = [{"stage_id": "cell-1", "kind_id": first, "seat": "machine", "ports": []}, dict(propose), {"stage_id": "cell-2", "kind_id": second, "seat": "machine", "ports": []}, dict(propose, stage_id="propose-2", kind_id="mini.pair-proposal.recovery-2.v1")]

        def naming(cell: str) -> str:
            return submission("a body", json.dumps({"kernel": kernels.KERNEL_RECOVERY, "input": OBJECT, "rewritten": OBJECT + cell, "expect": "moves", "rewrite": "test", "cell": cell}))

        script = {"propose": [naming("object alone / nothing"), naming("object alone / nothing")], "propose-2": [naming("sentence then an object / a different bare object"), naming("object alone / a sentence")]}
        plan, outcome = self.run_manifest(manifest, script)
        state = replay(outcome.root / "log.jsonl", plan.genesis)
        blobs = BlobStore(outcome.root / "blobs")
        named = [json.loads(blobs.get(r["commitments_ref"]).decode("utf-8"))["cell"] for r in state.artifacts.values() if r["kind_id"] in (first, second)]
        self.assertEqual(
            named,
            ["object alone / nothing", "sentence then an object / a different bare object", "object alone / a sentence", "object alone / a sentence"],
            "cycle 1 names the first two; cycle 2 names the third, never named, and then again the one named once (by the seat) over those named twice or thrice",
        )
        from creib.forge.mini.runner import render_brief

        brief, _ = render_brief(plan, state, blobs, plan.stage("propose-2"), 2)
        self.assertIn("The cell to cover: object alone / a sentence", brief)
        self.assertEqual(brief.count("The cell to cover:"), 1, "a proposer's port draws its own stage's cell kind, so it sees one cell")


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


class TransformUnreadableTests(MiniTestCase):
    def test_a_triple_whose_kernel_cannot_read_the_input_is_unrunnable(self) -> None:
        from pathlib import Path
        from creib.strict_json import load_strict

        root = Path(__file__).resolve().parents[2]
        manifest = dict(load_strict(root / "forge" / "mini" / "manifests" / "conformance-blind-spot" / "manifest.json"))
        manifest["sources"] = [{"source_id": item["source_id"], "text": (root / "forge" / "mini" / "manifests" / "conformance-blind-spot" / item["path"]).read_text(encoding="utf-8")} for item in manifest["sources"]]
        manifest["cycles"] = {"max_cycles": 1}
        triple = json.dumps({"kernel": kernels.KERNEL_GROUNDING, "transform": "conformance.transform.upper-case", "input": OBJECT})
        reply = submission("a reply that is not a grounding input", triple)
        script = {stage: [reply] for stage in ("propose-1", "propose-2", "propose-3")}
        script["criticise"] = [submission("c", "c")]
        script["criticise@commitments"] = [json.dumps({"commitments": "c"})]
        plan, outcome = self.run_manifest(manifest, script)
        state = replay(outcome.root / "log.jsonl", plan.genesis)
        blobs = BlobStore(outcome.root / "blobs")
        executions = [e for r in state.artifacts.values() if r["kind_id"] == EXECUTION_KIND for e in json.loads(blobs.get(r["commitments_ref"]).decode("utf-8"))["executions"]]
        self.assertEqual([e["executed"] for e in executions], ["unrunnable", "duplicate", "duplicate"])
        self.assertEqual((executions[0]["before"], executions[0]["after"]), (kernels.UNREADABLE, kernels.UNREADABLE))
        verdicts = [v for r in state.artifacts.values() if r["kind_id"] == VERDICT_KIND for v in json.loads(blobs.get(r["commitments_ref"]).decode("utf-8"))["verdicts"]]
        self.assertEqual([v["standing"] for v in verdicts], [STANDING_REJECTED] * 3)


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
        self.assertEqual(grounding('{"value": "five", "span": "five days", "document": "away for five\ndays."}'), "GROUNDED", "M11: a line break written into the string is the line break meant")
        self.assertEqual(grounding('{"value": "five", "span": "five days", "document": "away for five\ndays.", "span": "x"}'), kernels.UNREADABLE, "M11 admits a control character and nothing else: a duplicate key is still refused")
        self.assertEqual(occurs(json.dumps({"span": 3, "document": document})), kernels.UNREADABLE)
