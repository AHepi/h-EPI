"""R26: the blind-spot template, and R27: comparison that ranks nothing."""

from __future__ import annotations

import json
from pathlib import Path

from creib.forge.mini.blindspot import (
    STANDING_CANDIDATE,
    STANDING_DEFECT,
    STANDING_REJECTED,
    VERDICT_KIND,
    registered_kernels,
    registered_transforms,
    resolve_kernel,
    resolve_transform,
    standing_for,
)
from creib.forge.mini.compare import compare_roots, read_root
from creib.forge.mini.log import replay
from creib.strict_json import load_strict

from .helpers import MiniTestCase

ROOT = Path(__file__).resolve().parents[2]
BLIND_SPOT = ROOT / "forge" / "mini" / "manifests" / "blind-spot" / "manifest.json"
CATALOGUE = BLIND_SPOT.parent / "catalogue.json"
SCRIPT = ROOT / "forge" / "mini" / "scripts" / "blind-spot.json"
COMMITTED_RUN = ROOT / "forge" / "mini" / "runs" / "blind-spot-stub"


def _manifest() -> dict:
    manifest = dict(load_strict(BLIND_SPOT))
    manifest["sources"] = [{"source_id": "catalogue", "text": CATALOGUE.read_text(encoding="utf-8")}]
    return manifest


def _script() -> dict:
    """A fresh copy of the committed script, which is addressed by coordinate."""

    return json.loads(json.dumps(load_strict(SCRIPT)))


class TheStandingRuleTests(MiniTestCase):
    def test_an_uncatalogued_movement_is_a_candidate_point(self) -> None:
        self.assertEqual(standing_for("moved", False), STANDING_CANDIDATE)

    def test_a_catalogue_claiming_a_movement_that_did_not_happen_is_a_defect(self) -> None:
        self.assertEqual(standing_for("unchanged", True, catalogue_moves=True), STANDING_DEFECT)

    def test_a_catalogue_denying_a_movement_that_did_happen_is_a_defect(self) -> None:
        self.assertEqual(standing_for("moved", True, catalogue_moves=False), STANDING_DEFECT)

    def test_a_catalogued_pair_that_agrees_is_neither(self) -> None:
        self.assertEqual(standing_for("moved", True, catalogue_moves=True), STANDING_REJECTED)
        self.assertEqual(standing_for("unchanged", True, catalogue_moves=False), STANDING_REJECTED)

    def test_an_uncatalogued_invariance_is_not_a_standing(self) -> None:
        """It belongs in the ledger compare prints, not in a verdict's standing."""

        self.assertEqual(standing_for("unchanged", False), STANDING_REJECTED)


class KernelAndTransformTests(MiniTestCase):
    def test_the_kernels_are_this_prototypes_own_checks(self) -> None:
        ids = {kernel.kernel_id for kernel in registered_kernels()}
        self.assertLessEqual({"mini.kernel.cut-count", "mini.kernel.folded", "mini.kernel.json-readable"}, ids)

    def test_a_kernel_is_deterministic(self) -> None:
        kernel = resolve_kernel("mini.kernel.cut-count")
        self.assertEqual(kernel.verdict("a\n\nb"), kernel.verdict("a\n\nb"))
        self.assertEqual(kernel.verdict("a\n\nb"), "2")

    def test_a_transform_is_deterministic(self) -> None:
        transform = resolve_transform("mini.transform.wrap-in-code-fence")
        self.assertEqual(transform.rewrite("x"), transform.rewrite("x"))
        self.assertIn("```", transform.rewrite("x"))

    def test_an_unknown_kernel_is_refused(self) -> None:
        self.assertRefuses("MINI_KERNEL_UNKNOWN", resolve_kernel, "mini.kernel.telepathy")

    def test_an_unknown_transform_is_refused(self) -> None:
        self.assertRefuses("MINI_TRANSFORM_UNKNOWN", resolve_transform, "mini.transform.telepathy")

    def test_registering_a_kernel_twice_is_refused(self) -> None:
        from creib.forge.mini.blindspot import Kernel, register_kernel

        self.assertRefuses(
            "MINI_KERNEL_DUPLICATE", register_kernel, Kernel("mini.kernel.folded", "again", lambda text: text)
        )

    def test_registering_a_transform_twice_is_refused(self) -> None:
        from creib.forge.mini.blindspot import Transform, register_transform

        self.assertRefuses(
            "MINI_TRANSFORM_DUPLICATE",
            register_transform,
            Transform("mini.transform.upper-case", "again", lambda text: text),
        )


class TheBlindSpotRunTests(MiniTestCase):
    def test_three_cycles_under_the_stub(self) -> None:
        plan, outcome = self.run_manifest(_manifest(), _script())
        self.assertEqual(outcome.cycles_completed, 3)
        self.assertEqual(
            outcome.stages_entered,
            ("propose-1", "propose-2", "propose-3", "execute", "criticise", "verdict") * 3,
        )
        self.assertEqual(outcome.stop_reason, "cycle_cap")

    def test_the_last_verdict_is_the_deliverable(self) -> None:
        plan, outcome = self.run_manifest(_manifest(), _script())
        state = replay(outcome.root / "log.jsonl", plan.genesis)
        verdicts = [state.artifacts[key] for key in state.artifact_order if state.artifacts[key]["kind_id"] == VERDICT_KIND]
        self.assertEqual(len(verdicts), 3)
        last = verdicts[-1]
        self.assertEqual(last["cycle"], 3)
        self.assertEqual(last["seat"], "machine")
        from creib.forge.mini.log import BlobStore

        payload = json.loads(BlobStore(outcome.root / "blobs").get(last["commitments_ref"]).decode("utf-8"))
        self.assertTrue(payload["verdicts"])
        for entry in payload["verdicts"]:
            self.assertIn(entry["standing"], (STANDING_CANDIDATE, STANDING_DEFECT, STANDING_REJECTED))

    def test_the_run_finds_a_candidate_point(self) -> None:
        """The record shows what these nine proposals did, and nothing wider."""

        plan, outcome = self.run_manifest(_manifest(), _script())
        state = replay(outcome.root / "log.jsonl", plan.genesis)
        from creib.forge.mini.log import BlobStore

        blobs = BlobStore(outcome.root / "blobs")
        standings: list[str] = []
        for key in state.artifact_order:
            record = state.artifacts[key]
            if record["kind_id"] != VERDICT_KIND:
                continue
            payload = json.loads(blobs.get(record["commitments_ref"]).decode("utf-8"))
            standings.extend(entry["standing"] for entry in payload["verdicts"])
        self.assertIn(STANDING_CANDIDATE, standings)

    def test_nothing_in_the_loop_promotes_anything(self) -> None:
        """A verdict is an artifact. No standing is minted anywhere else."""

        plan, outcome = self.run_manifest(_manifest(), _script())
        state = replay(outcome.root / "log.jsonl", plan.genesis)
        self.assertEqual(plan.policy.defaults.changes, "nothing")
        for record in state.artifacts.values():
            self.assertEqual(set(record) & {"standing", "status", "accepted"}, set())

    def test_the_committed_stub_run_replays(self) -> None:
        from creib.forge.mini.common import RUN_HEADER_DOMAIN, content_id

        genesis = content_id(RUN_HEADER_DOMAIN, load_strict(COMMITTED_RUN / "run-header.json"))
        state = replay(COMMITTED_RUN / "log.jsonl", genesis)
        self.assertEqual(state.cycles_completed, 3)


class CompareTests(MiniTestCase):
    def _two_roots(self) -> tuple[Path, Path]:
        manifest = _manifest()
        machine = dict(manifest)
        model = json.loads(json.dumps(manifest))
        for stage in model["stages"]:
            if stage["stage_id"] == "verdict":
                stage["seat"] = "model"
        script = _script()
        model_script = _script()
        model_script["verdict"] = {
            str(index + 1): [
                json.dumps(
                    {
                        "body": f"My own reading of cycle {index + 1}.",
                        "commitments": json.dumps(
                            {"verdicts": [{"proposal": "aaaaaaaaaaaaaaaa", "executed": "moved", "catalogued": False, "standing": "candidate point"}]}
                        ),
                    }
                )
            ]
            for index in range(3)
        }
        _, first = self.run_manifest(machine, script, name="machine-root")
        plan = self.compile(model)
        from creib.forge.mini.executor import ScriptedResponder
        from creib.forge.mini.runner import run_mini

        second = run_mini(plan, self.tmp / "model-root", ScriptedResponder(model_script), "script:same")
        # The first root was written by run_manifest, which records no responder;
        # give both the same responder id so the comparison is of the runs.
        return first.root, second.root

    def test_compare_emits_both_ledgers(self) -> None:
        manifest = _manifest()
        plan = self.compile(manifest)
        from creib.forge.mini.executor import ScriptedResponder
        from creib.forge.mini.runner import run_mini

        first = run_mini(plan, self.tmp / "a", ScriptedResponder(_script()), "script:same")
        second = run_mini(self.compile(manifest), self.tmp / "b", ScriptedResponder(_script()), "script:same")
        rendered = compare_roots(first.root, second.root)
        self.assertEqual(rendered.count("### executed-invariance ledger"), 2)
        self.assertIn("is invariant under", rendered)
        self.assertEqual(rendered.count("### verdicts"), 2)

    def test_compare_names_no_winner_and_totals_nothing(self) -> None:
        from creib.forge.mini.executor import ScriptedResponder
        from creib.forge.mini.runner import run_mini

        manifest = _manifest()
        first = run_mini(self.compile(manifest), self.tmp / "a", ScriptedResponder(_script()), "script:same")
        second = run_mini(self.compile(manifest), self.tmp / "b", ScriptedResponder(_script()), "script:same")
        rendered = compare_roots(first.root, second.root).casefold()
        for forbidden in ("score", "best", "worst", "better", "wins", "rank", "accuracy", "total"):
            self.assertNotIn(forbidden, rendered, f"compare must not say {forbidden!r}")

    def test_compare_refuses_roots_that_were_asked_differently(self) -> None:
        from creib.forge.mini.executor import ScriptedResponder
        from creib.forge.mini.runner import run_mini

        manifest = _manifest()
        first = run_mini(self.compile(manifest), self.tmp / "a", ScriptedResponder(_script()), "script:one")
        second = run_mini(self.compile(manifest), self.tmp / "b", ScriptedResponder(_script()), "script:two")
        self.assertRefuses("MINI_COMPARE_MISMATCH", compare_roots, first.root, second.root)

    def test_compare_refuses_roots_given_different_sources(self) -> None:
        from creib.forge.mini.executor import ScriptedResponder
        from creib.forge.mini.runner import run_mini

        manifest = _manifest()
        other = _manifest()
        other["sources"] = [{"source_id": "catalogue", "text": '{"points": []}'}]
        first = run_mini(self.compile(manifest), self.tmp / "a", ScriptedResponder(_script()), "script:same")
        second = run_mini(self.compile(other), self.tmp / "b", ScriptedResponder(_script()), "script:same")
        self.assertRefuses("MINI_COMPARE_MISMATCH", compare_roots, first.root, second.root)

    def test_compare_refuses_a_score_flag_by_name(self) -> None:
        import subprocess
        import sys

        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools" / "run_mini.py"),
                "compare",
                "--root",
                str(COMMITTED_RUN),
                "--root",
                str(COMMITTED_RUN),
                "--score",
            ],
            cwd=ROOT,
            env={"PYTHONPATH": str(ROOT / "src"), "PATH": "/usr/bin:/bin"},
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("MINI_COMPARE_UNSUPPORTED", completed.stderr)
        self.assertIn("computes no score", completed.stderr)

    def test_a_root_that_is_not_a_root_is_refused(self) -> None:
        self.assertRefuses("MINI_COMPARE_MISMATCH", read_root, self.tmp / "nothing-here")
