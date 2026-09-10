"""Mini pointed at the conformance harness: its checks as kernels, the kernel table as the catalogue.

The integration this tests is the seam between the two packages. A kernel here is
one of the conformance harness's own functions read over a reply; a transform is a
rewrite of the kind the kernel table describes; the catalogue is rows drawn from
that table with the input each was checked on. The blind-spot loop then runs by
machine over those, and the verdict it commits must agree with the table: a
catalogued row that executes against its own claim is a defect in one or the
other, and none is expected.
"""

from __future__ import annotations

import json
from pathlib import Path

from creib.forge.mini import conformance_kernels as kernels
from creib.forge.mini.blindspot import (
    STANDING_CANDIDATE,
    STANDING_DEFECT,
    STANDING_REJECTED,
    VERDICT_KIND,
    catalogue_from,
    resolve_kernel,
    resolve_transform,
)
from creib.forge.mini.compare import read_root
from creib.forge.mini.evidence import cut_source
from creib.forge.mini.log import BlobStore, replay
from creib.forge.mini.manifest import compile_manifest
from creib.forge.mini.runner import render_brief
from creib.strict_json import load_strict

from .helpers import MiniTestCase

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_DIR = ROOT / "forge" / "mini" / "manifests" / "conformance-blind-spot"
MANIFEST = MANIFEST_DIR / "manifest.json"
CATALOGUE = MANIFEST_DIR / "catalogue.json"
REGISTRY = MANIFEST_DIR / "registry.txt"
SCRIPT = ROOT / "forge" / "mini" / "scripts" / "conformance-blind-spot.json"


def _points() -> list[dict]:
    text = CATALOGUE.read_text(encoding="utf-8")
    return [point for block in text.split("\n\n") if block.strip() for point in json.loads(block)["points"]]


class TheCatalogueIsTheCodeTests(MiniTestCase):
    def test_every_catalogued_row_agrees_with_the_conformance_code(self) -> None:
        """Each row re-derived by executing the harness's own function on the row's input."""

        points = _points()
        self.assertGreaterEqual(len(points), 20)
        for point in points:
            with self.subTest(kernel=point["kernel"], transform=point["transform"]):
                kernel = resolve_kernel(point["kernel"])
                transform = resolve_transform(point["transform"])
                before = kernel.verdict(point["input"])
                after = kernel.verdict(transform.rewrite(point["input"]))
                self.assertEqual(before != after, point["moves"], f"{before!r} -> {after!r}")

    def test_the_kernels_are_the_harness_own_functions(self) -> None:
        from creib.forge.conformance.oracle import parse_content, recover_json_object, refusal_phrase_in

        text = 'draft {"a": 1} ```json\nnote {"a": 2}\n``` then {"a": 3}'
        value, _ = recover_json_object(text)
        self.assertEqual(json.loads(resolve_kernel(kernels.KERNEL_RECOVERY).verdict(text)), value)
        self.assertEqual(resolve_kernel(kernels.KERNEL_RESPONSE_VERDICT).verdict(text), parse_content(text, kernels.REFUSAL_PHRASES)[1])
        self.assertEqual(resolve_kernel(kernels.KERNEL_REFUSAL_PHRASE).verdict("I’m sorry."), refusal_phrase_in("I’m sorry.", kernels.REFUSAL_PHRASES))
        self.assertEqual(resolve_kernel(kernels.KERNEL_RECOVERY).verdict("nothing here"), kernels.NO_OBJECT)

    def test_the_registry_file_is_the_module(self) -> None:
        self.assertEqual(REGISTRY.read_text(encoding="utf-8"), kernels.registry_text())

    def test_each_row_is_its_own_block_so_the_legend_shows_it(self) -> None:
        """A JSON source with no blank lines is one block and invisible in the legend (mini register M6)."""

        raw = CATALOGUE.read_bytes()
        self.assertEqual(len(cut_source("catalogue", raw, "evidence")), len(_points()))


class TheProposerSeesTheRegistryTests(MiniTestCase):
    def test_every_kernel_and_transform_id_is_in_the_first_brief(self) -> None:
        """The blind-spot live run's first defect was a proposer shown no registry (mini register M5)."""

        plan = compile_manifest(MANIFEST)
        self.compile_only = plan
        from creib.forge.mini.log import MiniState
        from creib.forge.mini.runner import _batch_evidence, _Recorder, EventLog

        root = self.tmp / "brief"
        root.mkdir()
        blobs = BlobStore(root / "blobs")
        state = MiniState()
        recorder = _Recorder(EventLog(root / "log.jsonl", plan.genesis), state, plan.genesis)
        _batch_evidence(plan, blobs, recorder)
        brief, exposed = render_brief(plan, state, blobs, plan.stage("propose-1"), 1)
        for kernel in kernels.KERNELS:
            self.assertIn(kernel.kernel_id, brief)
        for transform in kernels.TRANSFORMS:
            self.assertIn(transform.transform_id, brief)
        self.assertGreaterEqual(len(exposed), len(_points()) + len(kernels.KERNELS) + len(kernels.TRANSFORMS))


class TheLoopUnderTheStubTests(MiniTestCase):
    def _run(self):
        plan = compile_manifest(MANIFEST)
        from creib.forge.mini.executor import ScriptedResponder
        from creib.forge.mini.runner import run_mini

        outcome = run_mini(plan, self.tmp / "run", ScriptedResponder(json.loads(json.dumps(load_strict(SCRIPT)))), "script:test")
        state = replay(outcome.root / "log.jsonl", plan.genesis)
        return plan, outcome, state

    def _verdicts(self, outcome, state) -> list[dict]:
        blobs = BlobStore(outcome.root / "blobs")
        entries: list[dict] = []
        for key in state.artifact_order:
            record = state.artifacts[key]
            if record["kind_id"] == VERDICT_KIND:
                entries.extend(json.loads(blobs.get(record["commitments_ref"]).decode("utf-8"))["verdicts"])
        return entries

    def test_two_cycles_complete_and_every_proposal_was_run(self) -> None:
        plan, outcome, state = self._run()
        self.assertEqual((outcome.cycles_completed, outcome.stop_reason), (2, "cycle_cap"))
        entries = self._verdicts(outcome, state)
        self.assertEqual(len(entries), 6)
        self.assertEqual({entry["executed"] for entry in entries}, {"moved", "unchanged"}, "every proposal was runnable")

    def test_no_catalogued_row_is_contradicted_by_execution(self) -> None:
        """The integration claim: the conformance table and the conformance code agree, read by mini."""

        plan, outcome, state = self._run()
        entries = self._verdicts(outcome, state)
        self.assertEqual([entry for entry in entries if entry["standing"] == STANDING_DEFECT], [])
        catalogued = [entry for entry in entries if entry["catalogued"]]
        self.assertEqual(len(catalogued), 4)
        self.assertTrue(all(entry["standing"] == STANDING_REJECTED for entry in catalogued))

    def test_the_uncatalogued_pairs_land_where_the_rule_puts_them(self) -> None:
        plan, outcome, state = self._run()
        entries = {(entry["kernel"], entry["transform"]): entry for entry in self._verdicts(outcome, state)}
        moved = entries[(kernels.KERNEL_RECOVERED_FROM_PROSE, "conformance.transform.bare-after")]
        self.assertEqual((moved["executed"], moved["catalogued"], moved["standing"]), ("moved", False, STANDING_CANDIDATE))
        unchanged = entries[(kernels.KERNEL_RECOVERY, "conformance.transform.prose-after")]
        self.assertEqual((unchanged["executed"], unchanged["catalogued"], unchanged["standing"]), ("unchanged", False, STANDING_REJECTED))
        # The invariance the standing rule does not hold is in the ledger compare prints.
        reading = read_root(outcome.root)
        self.assertEqual([(item["kernel"], item["transform"]) for item in reading.ledger], [(kernels.KERNEL_RECOVERY, "conformance.transform.prose-after")])

    def test_the_catalogue_the_verdict_read_is_the_whole_file(self) -> None:
        plan, outcome, state = self._run()
        listed = catalogue_from(state, BlobStore(outcome.root / "blobs"))
        self.assertEqual(len(listed), len(_points()))

    def test_a_proposal_is_one_call_and_a_criticism_two(self) -> None:
        """The proposal's commitments carry the triple its body reasons about; a blind second call
        cannot write the instance the body chose (the second live run lost every first-cycle proposal
        to it), so the kind is declared single-call, and the record says so per artifact."""

        plan, outcome, state = self._run()
        shapes = {(record["kind_id"], record["seat"]) for record in state.artifacts.values()}
        self.assertIn(("mini.proposal.v1", "model"), shapes)
        events = [json.loads(line) for line in (outcome.root / "log.jsonl").read_text(encoding="utf-8").splitlines()]
        by_kind: dict[str, set[str]] = {}
        for event in events:
            if event["type"] == "ARTIFACT_SUBMITTED":
                by_kind.setdefault(event["kind_id"], set()).add(event["payload"]["commitment_call"])
        self.assertEqual(by_kind["mini.proposal.v1"], {"single"})
        self.assertEqual(by_kind["mini.criticism.v1"], {"two"})
        self.assertEqual(by_kind["mini.execution.v1"], {"machine_single"})


class TheCommittedLiveRootsTests(MiniTestCase):
    """Three live runs on gemma4:31b, one per revision of the manifest, each a record of what the
    template did on the day. They are read here for their shape only: that each replays, and what it
    holds. Nothing here is a claim about the model."""

    ROOTS = ROOT / "forge" / "mini" / "runs"

    def _replay(self, name: str):
        from creib.forge.mini.common import RUN_HEADER_DOMAIN, content_id

        root = self.ROOTS / name
        genesis = content_id(RUN_HEADER_DOMAIN, load_strict(root / "run-header.json"))
        return root, replay(root / "log.jsonl", genesis)

    def test_each_root_replays_to_its_end(self) -> None:
        for name in ("conformance-blind-spot-gemma4-31b-1", "conformance-blind-spot-gemma4-31b-2", "conformance-blind-spot-gemma4-31b-3"):
            with self.subTest(root=name):
                root, state = self._replay(name)
                self.assertTrue(state.ended)
                self.assertEqual(state.cycles_completed, 2)
                self.assertEqual(state.responder_id, "model:gemma4:31b")

    def test_the_second_run_lost_its_first_cycle_to_the_blind_call(self) -> None:
        root, state = self._replay("conformance-blind-spot-gemma4-31b-2")
        self.assertEqual(state.drops_by_kind.get("mini.proposal.v1"), 3)
        self.assertEqual(state.artifacts_of_kind("mini.proposal.v1")[0]["cycle"], 2)
