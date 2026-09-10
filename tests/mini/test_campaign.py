"""Reading a run without a person, and deciding the next round from what was read.

The reader is deterministic and calls no model. The rules are the rewrites the five rounds of
experiments made by hand, each stated once and fired by a measurement its own register entry
names; the assertions below are that each fires on the record that motivated it and stays
silent on the one that did not.
"""

from __future__ import annotations

import json
from pathlib import Path

from creib.forge.mini.campaign import (
    LONG_FIELDS,
    RULES,
    append_instruction,
    decide,
    render_decisions,
    set_cycles,
    to_fields_form,
)
from creib.forge.mini.report import read_run, render

from .helpers import MiniTestCase

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "forge" / "mini" / "runs" / "experiments"
MANIFESTS = ROOT / "forge" / "mini" / "manifests" / "experiments"


def _manifest(name: str) -> dict:
    return json.loads((MANIFESTS / name / "manifest.json").read_text(encoding="utf-8"))


class ReadingTests(MiniTestCase):
    def test_a_committed_record_reads_to_its_counts_and_its_disagreements(self) -> None:
        reading = read_run(RUNS / "round-5" / "r5-3-skeletons-fields-gemma")
        self.assertEqual((reading.responder_id, reading.ended, reading.cycles_completed), ("model:gemma4:31b", True, 7))
        self.assertEqual((reading.proposals, reading.ran, reading.drops, reading.format_failures), (21, 21, 0, 0))
        self.assertEqual(len(reading.cells_in_grid), 20)
        self.assertEqual(len(reading.cells_named), 20, "every cell of the grid was named")
        self.assertEqual(reading.cells_uncovered, ())
        cells = [row.cell for row in reading.disagreements]
        self.assertIn("fence[ S A ] B", cells, "the control's own cell is among the contradictions")
        rendered = render(reading)
        self.assertIn("Where the machine contradicted the proposal", rendered)
        self.assertIn("fence[ S A ] B", rendered)
        self.assertIn("Here is the result:", rendered, "the texts that produced it are laid out beside it")

    def test_a_run_that_contradicted_nothing_says_so(self) -> None:
        reading = read_run(RUNS / "round-1" / "s2-source-adversary")
        self.assertEqual(reading.disagreements, ())
        self.assertIn("every expectation the executor could run held", render(reading))

    def test_the_parts_measure_separates_the_run_that_changed_four_things_at_once(self) -> None:
        careful = read_run(RUNS / "round-5" / "r5-4-grounding-pairs-given")
        careless = read_run(RUNS / "round-2" / "e-replies-as-written")
        self.assertEqual(careful.multi_part_pairs, 0)
        self.assertGreater(careless.multi_part_pairs * 2, careless.ran, "M14: more than half of them")


class RuleTests(MiniTestCase):
    def test_every_rule_names_a_register_entry_and_fires_once(self) -> None:
        self.assertEqual(len({rule.rule_id for rule in RULES}), len(RULES))
        for rule in RULES:
            self.assertTrue(rule.register.strip(), rule.rule_id)
            self.assertTrue(rule.why.strip(), rule.rule_id)

    def test_the_escaping_rule_fires_on_the_run_that_lost_its_calls(self) -> None:
        decision = decide("r4-1", read_run(RUNS / "round-4" / "r4-1-skeletons-mistral"), _manifest("round-4/r4-1-skeletons-mistral"))
        self.assertEqual(decision.rules_fired, ("fields-form",))
        proposer = next(k for k in decision.manifest["kinds"] if k["kind_id"] == "mini.pair-proposal.grid-1.v1")
        self.assertEqual(tuple(proposer["optional_fields"]), LONG_FIELDS)
        schema = proposer["format"]["commitments"]["all_of"][0]["schema"]
        self.assertEqual(sorted(schema["required"]), ["expect", "kernel"])
        self.assertNotIn("input", schema["properties"])

    def test_the_line_break_rule_fires_on_the_run_that_wrote_the_escape_out(self) -> None:
        decision = decide("r5-2", read_run(RUNS / "round-5" / "r5-2-skeletons-fields-qwen"), _manifest("round-5/r5-2-skeletons-fields-qwen"))
        self.assertEqual(decision.rules_fired, ("real-line-breaks",))
        self.assertIn("never the two characters backslash and n", json.dumps(decision.manifest))

    def test_the_one_change_rule_fires_on_the_run_that_changed_four_things(self) -> None:
        decision = decide("e", read_run(RUNS / "round-2" / "e-replies-as-written"), _manifest("round-2/e-replies-as-written"))
        self.assertEqual(decision.rules_fired, ("one-change-per-pair",))
        self.assertIn("differs from the input in exactly ONE part", json.dumps(decision.manifest))

    def test_no_rule_fires_on_the_run_that_did_what_was_asked(self) -> None:
        decision = decide("r5-3", read_run(RUNS / "round-5" / "r5-3-skeletons-fields-gemma"), _manifest("round-5/r5-3-skeletons-fields-gemma"))
        self.assertEqual((decision.rules_fired, decision.stop), ((), False))
        self.assertEqual(decision.manifest["kinds"], _manifest("round-5/r5-3-skeletons-fields-gemma")["kinds"], "run again unchanged")

    def test_a_grid_left_uncovered_raises_the_cycles_to_cover_it(self) -> None:
        """No committed record shows this: every enumerated grid was sized to be covered, and
        each was. The rule is for a grid enlarged without its cycles, so the reading is built."""

        import dataclasses

        covered = read_run(RUNS / "round-3" / "r3-7-grid-skeletons")
        self.assertEqual(covered.cells_uncovered, (), "the record it is built from covered its own grid")
        manifest = _manifest("round-3/r3-7-grid-skeletons")
        reading = dataclasses.replace(covered, cells_in_grid=covered.cells_in_grid + ("fence[ S A B ] C", "fence[ B ] A"), stop_reason="cycle_cap")
        self.assertEqual(len(reading.cells_uncovered), 2)
        decision = decide("r3-7", reading, manifest)
        self.assertIn("cover-the-grid", decision.rules_fired)
        self.assertGreater(decision.manifest["cycles"]["max_cycles"], manifest["cycles"]["max_cycles"])
        self.assertGreaterEqual(decision.manifest["cycles"]["max_cycles"] * 3, len(reading.cells_in_grid))

    def test_a_seat_that_named_its_own_cell_is_counted(self) -> None:
        reading = read_run(RUNS / "round-5" / "r5-4-grounding-pairs-given")
        self.assertTrue(reading.cells_off_grid, "this seat wrote its own cell names rather than the ones given")
        self.assertIn("named that the grid does not hold", render(reading))

    def test_the_helpers_change_only_what_they_name(self) -> None:
        manifest = _manifest("round-5/r5-3-skeletons-fields-gemma")
        self.assertEqual(set_cycles(manifest, 9)["cycles"]["max_cycles"], 9)
        self.assertEqual(manifest["cycles"]["max_cycles"], 7, "the original is untouched")
        once = append_instruction(manifest, " One more sentence.")
        twice = append_instruction(once, " One more sentence.")
        self.assertEqual(json.dumps(once), json.dumps(twice), "a sentence is added once")
        self.assertEqual(json.dumps(to_fields_form(manifest)), json.dumps(to_fields_form(to_fields_form(manifest))))

    def test_the_decision_note_says_what_changed_and_on_what_measurement(self) -> None:
        reading = read_run(RUNS / "round-4" / "r4-1-skeletons-mistral")
        decision = decide("r4-1", reading, _manifest("round-4/r4-1-skeletons-mistral"))
        note = render_decisions("campaign-round-2", [decision], {"r4-1": reading})
        self.assertIn("Decided from the previous round's records, before this round was run.", note)
        self.assertIn("fields-form (M13)", note)
        self.assertIn("1 proposals, 1 run", note)
