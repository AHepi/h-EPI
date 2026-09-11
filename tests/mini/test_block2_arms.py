"""CREATIVITY-ARMS-2's arms differ in exactly what the block says they differ in.

Written because they did not, last time. Block 1's ``W`` and ``A`` declared a ``reads`` port on the
criticism KIND and never listed it on the criticise STAGE, so the readings were never rendered while
the instruction told the critic to attack one by name; two other settings moved at the same time and
the effect was named after the one that was not operating (ERRATA C12, CON-PORT-NOT-DECLARED).

A stage's ``ports`` is the operative list, so these assertions read that and nothing else. What they
pin is the contrast the block is for: ``F`` -> ``W`` is the readings port and the instruction that
uses it, ``W`` -> ``A`` is the warrant and the adjudication, and nothing else moves in either step.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROOT_PATH = Path
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))


def _module():
    spec = importlib.util.spec_from_file_location("creativity_block2", ROOT / "tools" / "creativity_block2.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


BLOCK = _module()


def _stage(manifest: dict, stage_id: str) -> dict | None:
    for stage in manifest["stages"]:
        if stage.get("stage_id") == stage_id:
            return stage
    return None


def _kind(manifest: dict, kind_id: str) -> dict:
    return next(k for k in manifest["kinds"] if k["kind_id"] == kind_id)


class ArmDifferenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.arm = {a: BLOCK.manifest(a, 0, 0, BLOCK.PROBLEM) for a in BLOCK.ARMS}

    def test_the_readings_port_is_on_the_criticise_STAGE_and_not_only_on_the_kind(self) -> None:
        """The assertion block 1 needed and did not have."""

        for name in ("W", "A"):
            stage = _stage(self.arm[name], "criticise")
            self.assertIsNotNone(stage)
            self.assertIn("reads", stage["ports"], f"{name}'s critic would never see a reading")

    def test_F_is_the_same_stage_without_that_one_port(self) -> None:
        self.assertEqual(_stage(self.arm["F"], "criticise")["ports"], ["source", "conj", "execs"])
        self.assertEqual(_stage(self.arm["W"], "criticise")["ports"], ["source", "conj", "reads", "execs"])

    def test_every_stage_lists_every_port_its_kind_declares(self) -> None:
        """A port on a kind that its stage does not list is silent, compiles, and renders nothing."""

        for name, manifest in self.arm.items():
            for stage in manifest["stages"]:
                if stage.get("end") or stage.get("kind_id") is None:
                    continue
                declared = {p["port_type"] for p in _kind(manifest, stage["kind_id"])["input_ports"]}
                listed = set(stage.get("ports", ()))
                self.assertEqual(declared - {"problem"}, listed - {"problem"},
                                 f"{name}.{stage['stage_id']} declares {declared} and lists {listed}")

    def test_the_conjecture_is_rendered_the_same_way_for_every_arm(self) -> None:
        """Block 1 varied this together with the wiring, which is how the effect lost its cause."""

        rules = {name: next(p["render"]["rule"] for p in manifest["port_types"] if p["port_type"] == "conj")
                 for name, manifest in self.arm.items()}
        self.assertEqual(set(rules.values()), {"list_bodies"}, rules)

    def test_one_failure_policy_on_every_kind_of_every_arm(self) -> None:
        """CON-FORMAT-KILLS-RUN: strictness and lifetime are one knob unless the policy is held."""

        for name, manifest in self.arm.items():
            for kind in manifest["kinds"]:
                self.assertEqual(kind["failure_policy"], BLOCK.FAILURE_POLICY, f"{name}.{kind['kind_id']}")
            self.assertIsNone(BLOCK.FAILURE_POLICY["tolerance"], "an arm could die younger for being asked more")

    def test_the_reading_declares_a_shape_for_its_own_three_texts_on_every_arm(self) -> None:
        """Nine of thirty-nine block 1 readings returned no texts and were counted as answers."""

        for name, manifest in self.arm.items():
            reading = _kind(manifest, BLOCK.READING)
            self.assertEqual(sorted(reading["format"]["fields"]), ["input", "rewrite", "rewritten"], name)
            self.assertEqual(sorted(reading["optional_fields"]), ["input", "rewrite", "rewritten"], name)

    def test_only_arm_A_declares_a_format_on_a_criticism_and_it_keeps_the_escape_road(self) -> None:
        for name, manifest in self.arm.items():
            formats = [k["kind_id"] for k in manifest["kinds"]
                       if k.get("format") and k["kind_id"] != BLOCK.READING]
            self.assertEqual(formats, [BLOCK.CRITICISM] if name == "A" else [], name)
        pattern = BLOCK.CRITICISM_SCHEMA["schema"]["properties"]["ground"]["pattern"]
        self.assertIn("cannot-tell", pattern)
        self.assertIn("test-is-unsound", pattern)

    def test_the_schema_admits_exactly_the_grounds_the_adjudicator_admits(self) -> None:
        """Two copies of a closed vocabulary drift; this is the test that says they have not."""

        from creib.forge.mini.adjudication import GROUNDS

        pattern = BLOCK.CRITICISM_SCHEMA["schema"]["properties"]["ground"]["pattern"]
        self.assertEqual(pattern, "^(" + "|".join(GROUNDS) + ")$")

    def test_the_adjudicate_stage_is_arm_A_alone(self) -> None:
        for name, manifest in self.arm.items():
            self.assertEqual(_stage(manifest, "adjudicate") is not None, name == "A", name)

    def test_repeats_differ_in_the_endpoint_seed_and_in_nothing_else(self) -> None:
        """A declared stochastic floor, and a declaration a reader can check (ERRATA C7)."""

        first = BLOCK.manifest("W", 0, 0, BLOCK.PROBLEM)
        for repeat in range(1, BLOCK.REPEATS):
            other = BLOCK.manifest("W", repeat, 0, BLOCK.PROBLEM)
            self.assertNotEqual(first["endpoint"]["options"]["seed"], other["endpoint"]["options"]["seed"])
            stripped_first = json.loads(json.dumps(first))
            stripped_other = json.loads(json.dumps(other))
            for blob in (stripped_first, stripped_other):
                blob["endpoint"]["options"]["seed"] = 0
                blob["manifest_id"] = ""
            self.assertEqual(stripped_first, stripped_other)

    def test_the_install_map_is_withheld_from_no_arm_that_is_supposed_to_have_it(self) -> None:
        self.assertEqual({a for a, s in BLOCK.ARMS.items() if s["install"]}, {"F", "W", "A"})
        self.assertFalse(BLOCK.ARMS["R"]["install"])


class BaselineTests(unittest.TestCase):
    def test_the_seed_pool_is_larger_than_block_one_s_and_holds_its_fourteen(self) -> None:
        """ERRATA A3: 458 of 460 collapses were on functions constant over the old pool."""

        from creativity_arms import SEEDS as OLD

        self.assertGreater(len(BLOCK.SEEDS_POOL), len(OLD))
        self.assertTrue(set(OLD).issubset(set(BLOCK.SEEDS_POOL)))

    def test_no_seed_appears_twice(self) -> None:
        self.assertEqual(len(set(BLOCK.SEEDS_POOL)), len(BLOCK.SEEDS_POOL))


if __name__ == "__main__":
    unittest.main()


class StarvationStreakTests(unittest.TestCase):
    """Whether an ARM is starved is a run of segments, and only the caller can see a run."""

    def test_the_streak_counts_up_and_resets(self) -> None:
        self.assertEqual(BLOCK.starved_streak(0, {"LOOP_STARVED"}), 1)
        self.assertEqual(BLOCK.starved_streak(1, {"NOTHING_EXECUTED"}), 2)
        self.assertEqual(BLOCK.starved_streak(2, {"FORMAT_FAILURES_RISING"}), 0)
        self.assertEqual(BLOCK.starved_streak(0, set()), 0)

    def test_the_stop_needs_more_than_one_segment(self) -> None:
        self.assertGreater(BLOCK.STARVED_RUN, 1)


class BriefCeilingTests(unittest.TestCase):
    """A brief the manifest schema refuses ends the arm; one paragraph shorter does not.

    Arm A reached 8310 characters at segment 14 of 16 and MINI_MANIFEST_INVALID stopped it three
    attempts running. The schema caps `problem` at 8192.
    """

    def test_a_short_brief_is_returned_unchanged(self) -> None:
        self.assertEqual(BLOCK._under_ceiling(["a", "b"], 0), "a\nb")

    def test_the_oldest_attempts_go_first_and_the_brief_says_how_many(self) -> None:
        parts = ["head", ""] + [f"- attempt {i} {'z' * 200}" for i in range(60)] + ["tail"]
        out = BLOCK._under_ceiling(list(parts), 60)
        self.assertLessEqual(len(out), BLOCK.BRIEF_CEILING)
        self.assertIn("earlier attempt(s) dropped", out)
        self.assertIn("tail", out, "the newest information is what the ceiling protects")

    def test_a_brief_with_nothing_droppable_is_cut_rather_than_left_over(self) -> None:
        out = BLOCK._under_ceiling(["head", "", "- one", "q" * 9000], 1)
        self.assertLessEqual(len(out), BLOCK.BRIEF_CEILING)
        self.assertIn("cut to fit", out)

    def test_the_ceiling_leaves_room_under_the_schema(self) -> None:
        import json as _json
        from pathlib import Path as _Path

        schema = _json.loads((ROOT / "forge/mini/schema/mini-manifest.schema.json").read_text())
        self.assertLess(BLOCK.BRIEF_CEILING, schema["properties"]["problem"]["maxLength"])
        _ = _Path


class FinishedSegmentsOnlyTests(unittest.TestCase):
    """A log file is not a finished segment, and the reader must not count one as if it were.

    A transport failure leaves a root holding a conjecture, a reading and no execution. `_segments`
    asked only whether a log existed, so it returned those beside the real ones: `R.r1` read as twenty
    segments where sixteen had finished, and the call count and the row count both carried the
    difference. Found by a completeness check run against the records, not by reading the code.
    """

    def test_a_root_with_a_log_but_no_end_is_not_a_segment(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as place:
            root = ROOT_PATH(place)
            cell = root / "W" / "r0"
            (cell / "s00").mkdir(parents=True)
            (cell / "s00" / "log.jsonl").write_text('{"type": "RUN_STARTED"}\n{"type": "RUN_ENDED"}\n')
            (cell / "s01").mkdir(parents=True)
            (cell / "s01" / "log.jsonl").write_text('{"type": "RUN_STARTED"}\n')
            (cell / "s02.dead1").mkdir(parents=True)
            (cell / "s02.dead1" / "log.jsonl").write_text('{"type": "RUN_STARTED"}\n{"type": "RUN_ENDED"}\n')
            found = [p.name for p in BLOCK._segments(root, "W", 0)]
            self.assertEqual(found, ["s00"], "an unfinished root and a set-aside root are not segments")

    def test_a_set_aside_root_leaves_the_block_entirely(self) -> None:
        """It goes to a directory of its own, because a records directory is read by enumeration."""

        self.assertEqual(BLOCK.DEAD_ROOTS, "creativity-2-aborted/dead")
        self.assertNotIn("creativity-2/", BLOCK.DEAD_ROOTS + "/")

    def test_the_block_tree_holds_no_set_aside_root(self) -> None:
        place = ROOT / "forge/mini/runs/creativity-2"
        if not place.is_dir():
            self.skipTest("the block's records are not in this checkout")
        stray = [str(p) for p in place.rglob("*.dead*")]
        self.assertEqual(stray, [], "a set-aside root inside the block is one the reader can count")
