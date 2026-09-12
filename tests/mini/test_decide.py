"""DECIDE-TEST-1's states, briefs and scoring, and every refusal they can make.

`docs/mini/DECIDE_TEST_1.md` is the pre-registration. The assertions that matter most are the ones on
the briefs: the block's whole claim is that a decider must be insensitive to form and sensitive to
content, so `reordered` and `relabelled` have to carry the same content as `plain` and `contrast` and
`ablated` have to carry different content, and if any of that stops being true the measure means
nothing. Each is asserted here rather than described.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from creib.forge.mini.common import MiniError  # noqa: E402
from creib.forge.mini.decide import (  # noqa: E402
    ABLATED,
    BLOCKS,
    BRIEFS,
    CONTRAST,
    FORM_BRIEFS,
    ORDERS,
    PLAIN,
    RELABELLED,
    REORDERED,
    REORDERED_2,
    REORDERED_3,
    REPEAT,
    ADD_NOTHING,
    ADDITIONS,
    STAY,
    STOP,
    UNCHANGED,
    WORKING_SET,
    AddState,
    CampaignState,
    Grid,
    State,
    Tally,
    add_brief,
    add_contrast_of,
    add_options,
    add_relabelling,
    add_states,
    agreement,
    brief,
    campaign_brief,
    campaign_contrast_of,
    campaign_options,
    campaign_states,
    check_of_option,
    contrast_flips,
    contrast_of,
    fixed_hit_rate,
    length_dependent,
    move_option,
    option_ids,
    options_of,
    random_hit_rate,
    name_choice,
    read_choice,
    relabelling,
    remaining_yield,
    right_options,
    rule_that_fires,
    source_of,
    states_from_grid,
)

RICH, POOR, EMPTY = WORKING_SET


def _grid() -> Grid:
    return Grid({RICH: (1, 1, 0, 1, 0, 1), POOR: (0, 0, 0, 0, 0, 0), EMPTY: (0, 0, 0, 0, 0, 0)})


def _state(current: str = POOR) -> State:
    return State(point_id="t", current=current,
                 tallies=(Tally(RICH, 2, 2, 2), Tally(POOR, 2, 0, 0), Tally(EMPTY, 1, 0, 0)))


class StateTests(unittest.TestCase):
    def test_the_options_are_stay_then_each_other_check_then_stop(self) -> None:
        self.assertEqual(options_of(_state()),
                         (STAY, move_option(RICH), move_option(EMPTY), STOP))

    def test_each_option_names_the_check_it_works(self) -> None:
        state = _state()
        self.assertEqual(check_of_option(state, STAY), POOR)
        self.assertEqual(check_of_option(state, move_option(RICH)), RICH)
        self.assertIsNone(check_of_option(state, STOP))

    def test_an_option_that_is_not_on_the_list_is_refused(self) -> None:
        with self.assertRaises(MiniError):
            check_of_option(_state(), "move-to-somewhere-else")

    def test_two_tallies_for_one_check_are_refused(self) -> None:
        with self.assertRaises(MiniError):
            State(point_id="t", current=RICH, tallies=(Tally(RICH, 1, 0, 0), Tally(RICH, 2, 0, 0)))

    def test_a_state_whose_current_check_has_no_tally_is_refused(self) -> None:
        with self.assertRaises(MiniError):
            State(point_id="t", current=EMPTY, tallies=(Tally(RICH, 1, 0, 0),))

    def test_asking_for_a_tally_that_is_not_there_is_refused(self) -> None:
        with self.assertRaises(MiniError):
            _state().tally_of("creib.forge.conformance.oracle.parse_content")


class GridTests(unittest.TestCase):
    def test_remaining_yield_is_the_tail_of_the_row(self) -> None:
        grid, state = _grid(), _state(current=RICH)
        self.assertEqual(remaining_yield(grid, state, STAY), 2)
        self.assertEqual(remaining_yield(grid, state, move_option(POOR)), 0)
        self.assertEqual(remaining_yield(grid, state, STOP), 0)

    def test_the_right_option_is_the_one_with_the_most_left_to_give(self) -> None:
        self.assertEqual(right_options(_grid(), _state()), frozenset({move_option(RICH)}))

    def test_stop_is_right_only_when_nothing_is_left_anywhere(self) -> None:
        spent = State(point_id="t", current=RICH,
                      tallies=(Tally(RICH, 6, 4, 4), Tally(POOR, 6, 0, 0), Tally(EMPTY, 6, 0, 0)))
        self.assertEqual(right_options(_grid(), spent), frozenset({STOP}))

    def test_a_grid_row_cannot_count_negative_classes(self) -> None:
        with self.assertRaises(MiniError):
            Grid({RICH: (1, -1)})

    def test_a_check_the_grid_has_no_row_for_is_refused(self) -> None:
        with self.assertRaises(MiniError):
            Grid({RICH: (1,)}).row(POOR)

    def test_a_baseline_over_no_state_is_refused(self) -> None:
        with self.assertRaises(MiniError):
            random_hit_rate(_grid(), ())
        with self.assertRaises(MiniError):
            fixed_hit_rate(_grid(), (), STAY)

    def test_the_twelve_points_do_not_all_have_the_same_right_answer(self) -> None:
        # If they did, a constant policy would score full marks and the block would measure nothing.
        grid = _grid()
        points = states_from_grid(grid)
        self.assertEqual(len(points), 12)
        answers = {frozenset(right_options(grid, point)) for point in points}
        self.assertGreater(len(answers), 1)
        self.assertLess(max(fixed_hit_rate(grid, points, option)
                            for option in (STAY, STOP, move_option(RICH))), 1.0)

    def test_a_point_whose_key_needs_the_grids_length_is_marked(self) -> None:
        # Amendment A1: at the deepest cut every check is spent, so ``stop`` is right -- and the
        # figures shown say the opposite, because a check with five ways found looks worth moving to
        # and the model cannot know there is no seventh segment.
        grid = _grid()
        points = states_from_grid(grid)
        deep = [point for point in points if point.point_id.endswith(".s6")]
        self.assertEqual(len(deep), 3)
        for point in deep:
            self.assertEqual(right_options(grid, point), frozenset({STOP}), point.point_id)
            self.assertTrue(length_dependent(grid, point), point.point_id)
        for point in points:
            if point not in deep:
                self.assertFalse(length_dependent(grid, point), point.point_id)

    def test_the_two_baseline_sets_differ_so_reporting_one_would_hide_the_other(self) -> None:
        grid = _grid()
        points = states_from_grid(grid)
        free = [point for point in points if not length_dependent(grid, point)]
        self.assertEqual(len(free), 9)
        self.assertNotEqual(fixed_hit_rate(grid, points, STAY), fixed_hit_rate(grid, free, STAY))
        self.assertEqual(fixed_hit_rate(grid, free, STOP), 0.0)

    def test_a_grid_holding_no_check_of_the_working_set_is_refused(self) -> None:
        with self.assertRaises(MiniError):
            states_from_grid(Grid({"creib.forge.conformance.oracle.parse_content": (1,)}))


class BriefTests(unittest.TestCase):
    def test_repeat_is_the_same_bytes_as_plain(self) -> None:
        self.assertEqual(brief(_state(), REPEAT), brief(_state(), PLAIN))

    def test_every_reordering_holds_every_block_plain_holds_and_in_another_order(self) -> None:
        state = _state()
        plain = brief(state, PLAIN)
        for variant in (REORDERED, REORDERED_2, REORDERED_3):
            moved = brief(state, variant)
            for block in ("You are running a search", "## The checks, in full",
                          "## What has been spent", "## The options"):
                self.assertIn(block, plain)
                self.assertIn(block, moved)
            self.assertNotEqual(plain, moved, variant)
            # The same blocks in a different order: the same characters, so the same length.
            self.assertEqual(len(plain), len(moved), variant)

    def test_the_three_reorderings_are_three_different_orders(self) -> None:
        state = _state()
        self.assertEqual(len({brief(state, variant)
                              for variant in (PLAIN, REORDERED, REORDERED_2, REORDERED_3)}), 4)
        self.assertEqual(len({ORDERS[variant]
                              for variant in (PLAIN, REORDERED, REORDERED_2, REORDERED_3)}), 4)

    def test_the_instruction_is_last_in_every_brief(self) -> None:
        for variant in BRIEFS:
            self.assertTrue(brief(_state(), variant).rstrip().endswith(
                "names none of them."), variant)

    def test_every_order_is_a_permutation_of_the_declared_blocks(self) -> None:
        for variant, order in ORDERS.items():
            self.assertEqual(len(set(order)), len(order), variant)
            self.assertTrue(set(order) <= set(BLOCKS), variant)
        self.assertEqual(set(ORDERS), set(BRIEFS))

    def test_relabelled_names_no_check_and_keeps_every_figure(self) -> None:
        state = _state()
        text = brief(state, RELABELLED)
        for tally in state.tallies:
            self.assertNotIn(tally.name, text)
        for name in ("check_one", "check_two", "check_three"):
            self.assertIn(name, text)
        self.assertIn("2 segment(s) run, 2 pair(s) found, 2 distinct way(s)", text)

    def test_relabelled_renames_the_move_options_and_nothing_else(self) -> None:
        shown = option_ids(_state(), RELABELLED)
        self.assertEqual(shown[STAY], STAY)
        self.assertEqual(shown[STOP], STOP)
        self.assertEqual(shown[move_option(RICH)], "move-to-check_one")

    def test_contrast_swaps_two_checks_figures_and_moves_nothing_else(self) -> None:
        state = _state()
        swapped = contrast_of(state)
        self.assertEqual(swapped.current, state.current)
        self.assertEqual(options_of(swapped), options_of(state))
        self.assertEqual(swapped.tally_of(POOR).real_classes, 2)
        self.assertEqual(swapped.tally_of(RICH).real_classes, 0)
        self.assertEqual(sum(t.segments for t in swapped.tallies),
                         sum(t.segments for t in state.tallies))

    def test_the_contrast_changes_what_the_figures_indicate(self) -> None:
        self.assertTrue(contrast_flips(_grid(), _state()))

    def test_a_contrast_needs_a_second_check_to_swap_with(self) -> None:
        with self.assertRaises(MiniError):
            contrast_of(State(point_id="t", current=RICH, tallies=(Tally(RICH, 1, 0, 0),)))

    def test_ablated_drops_the_figures_and_keeps_the_sources_and_options(self) -> None:
        text = brief(_state(), ABLATED)
        self.assertNotIn("## What has been spent", text)
        self.assertIn("## The checks, in full", text)
        self.assertIn("## The options", text)

    def test_every_brief_but_the_recoded_one_shows_the_source_unchanged(self) -> None:
        source = source_of(RICH)
        for variant in BRIEFS:
            shown = brief(_state(), variant)
            if variant == RELABELLED:
                self.assertIn("def check_one(content: str)", shown)
                self.assertNotIn("recover_json_object", shown)
                continue
            self.assertIn(source.strip().splitlines()[0], shown)

    def test_the_recoding_renames_a_check_wherever_it_appears(self) -> None:
        # refusal_phrase_in's body calls _plain_quotes, so a recoding that renamed only the
        # definitions would leave the call naming a function the brief no longer shows.
        shown = brief(_state(), RELABELLED)
        self.assertIn("check_three(content).lower()", shown)
        self.assertNotIn("_plain_quotes", shown)

    def test_the_form_briefs_change_no_figure_and_the_content_briefs_do(self) -> None:
        state = _state()
        figures = "2 segment(s) run, 2 pair(s) found, 2 distinct way(s) of breaking it"
        for variant in FORM_BRIEFS:
            self.assertIn(figures, brief(state, variant).replace("check_one", "x").replace(
                state.tally_of(RICH).name, "x"))
        self.assertNotIn("recover_json_object: 2 segment(s) run, 2 pair(s) found, 2 distinct",
                         brief(state, CONTRAST))

    def test_an_unknown_brief_is_refused(self) -> None:
        with self.assertRaises(MiniError):
            brief(_state(), "shorter")

    def test_a_check_whose_source_cannot_be_read_is_refused(self) -> None:
        with self.assertRaises(MiniError):
            source_of("creib.forge.conformance.oracle.no_such_function_at_all")

    def test_more_checks_than_neutral_names_is_refused(self) -> None:
        state = State(point_id="t", current=RICH,
                      tallies=tuple(Tally(f"m.f{index}", 0, 0, 0) for index in range(4))
                      + (Tally(RICH, 0, 0, 0),))
        with self.assertRaises(MiniError):
            relabelling(state)


class ReadingTests(unittest.TestCase):
    def test_a_body_that_is_the_id_alone_is_read(self) -> None:
        self.assertEqual(read_choice("stay", _state(), PLAIN), STAY)
        self.assertEqual(read_choice("  `stop`  ", _state(), PLAIN), STOP)

    def test_an_id_inside_a_sentence_is_read_when_it_is_the_only_one_there(self) -> None:
        self.assertEqual(read_choice("I would stay, because it is yielding.", _state(), PLAIN), STAY)

    def test_a_body_naming_two_ids_names_neither(self) -> None:
        self.assertEqual(read_choice("either stay or stop", _state(), PLAIN), "")

    def test_a_body_naming_no_id_names_none(self) -> None:
        self.assertEqual(read_choice("keep going with what we have", _state(), PLAIN), "")

    def test_a_relabelled_id_is_read_back_to_the_check_it_means(self) -> None:
        self.assertEqual(read_choice("move-to-check_one", _state(), RELABELLED), move_option(RICH))

    def test_a_relabelled_id_is_not_read_under_the_plain_brief(self) -> None:
        self.assertEqual(read_choice("move-to-check_one", _state(), PLAIN), "")

    def test_the_campaign_ids_are_read_by_the_same_rule(self) -> None:
        shown = {option: option for option in campaign_options()}
        self.assertEqual(name_choice("`fields-form`", shown), "fields-form")
        self.assertEqual(name_choice("nothing on that list", shown), "")

    def test_agreement_counts_only_points_both_briefs_answered(self) -> None:
        self.assertEqual(agreement({"a": STAY, "b": STOP, "c": ""}, {"a": STAY, "b": STAY, "c": STAY}),
                         (1, 2))


class CampaignTests(unittest.TestCase):
    def test_each_declared_state_fires_the_rule_it_is_named_for(self) -> None:
        for state in campaign_states():
            expected = UNCHANGED if state.state_id == "none-fires" else state.state_id
            if state.state_id == "breaks-and-one-change":
                expected = "real-line-breaks"
            if state.state_id == "fields-and-breaks":
                expected = "fields-form"
            self.assertEqual(rule_that_fires(state), expected, state.state_id)

    def test_the_option_set_is_every_rule_and_running_it_again(self) -> None:
        options = campaign_options()
        self.assertEqual(options[-1], UNCHANGED)
        self.assertIn("fields-form", options)
        self.assertEqual(len(set(options)), len(options))

    def test_every_contrast_fires_a_different_rule_and_the_key_is_spread(self) -> None:
        fired = []
        for state in campaign_states():
            contrast = rule_that_fires(campaign_contrast_of(state))
            self.assertNotEqual(contrast, rule_that_fires(state), state.state_id)
            fired.append(contrast)
        self.assertGreater(len(set(fired)), 3)

    def test_the_campaign_briefs_reorder_the_blocks_it_has(self) -> None:
        state = campaign_states()[1]
        plain = campaign_brief(state, PLAIN)
        for variant in (REORDERED, REORDERED_2, REORDERED_3):
            moved = campaign_brief(state, variant)
            self.assertNotEqual(plain, moved, variant)
            self.assertEqual(len(plain), len(moved), variant)

    def test_the_campaign_briefs_move_the_figures_and_not_the_options(self) -> None:
        state = campaign_states()[1]
        options = "\n".join(line for line in campaign_brief(state, PLAIN).splitlines()
                            if line.startswith("- `"))
        for variant in BRIEFS:
            text = campaign_brief(state, variant)
            if variant != ABLATED:
                self.assertIn("## What the round did", text)
            for line in options.splitlines():
                self.assertIn(line, text)
        self.assertNotIn("## What the round did", campaign_brief(state, ABLATED))
        self.assertNotEqual(campaign_brief(state, CONTRAST), campaign_brief(state, PLAIN))

    def test_the_campaign_relabelled_brief_is_the_plain_one_because_there_is_nothing_to_rename(self) -> None:
        state = campaign_states()[0]
        self.assertEqual(campaign_brief(state, RELABELLED), campaign_brief(state, PLAIN))

    def test_a_state_describing_more_rows_than_it_ran_is_refused(self) -> None:
        with self.assertRaises(MiniError):
            CampaignState(state_id="x", format_failures=0, drops=0, ran=1, escaped_breaks=2,
                          multi_part_pairs=0, cells_in_grid=1, cells_executed=1, duplicates=0,
                          stop_reason="completed", in_fields_form=True,
                          carries_break_instruction=True, carries_one_change_instruction=True)

    def test_a_state_running_more_cells_than_its_grid_holds_is_refused(self) -> None:
        with self.assertRaises(MiniError):
            CampaignState(state_id="x", format_failures=0, drops=0, ran=1, escaped_breaks=0,
                          multi_part_pairs=0, cells_in_grid=1, cells_executed=2, duplicates=0,
                          stop_reason="completed", in_fields_form=True,
                          carries_break_instruction=True, carries_one_change_instruction=True)

    def test_an_undeclared_state_has_no_contrast(self) -> None:
        with self.assertRaises(MiniError):
            campaign_contrast_of(CampaignState(
                state_id="invented", format_failures=0, drops=0, ran=1, escaped_breaks=0,
                multi_part_pairs=0, cells_in_grid=1, cells_executed=1, duplicates=0,
                stop_reason="completed", in_fields_form=True, carries_break_instruction=True,
                carries_one_change_instruction=True))

    def test_an_unknown_campaign_brief_is_refused(self) -> None:
        with self.assertRaises(MiniError):
            campaign_brief(campaign_states()[0], "terser")


if __name__ == "__main__":
    unittest.main()


class DriverTests(unittest.TestCase):
    """The manifests the driver writes must compile before a call is paid for."""

    @staticmethod
    def _driver():
        import importlib.util

        spec = importlib.util.spec_from_file_location("mini_decide", ROOT / "tools" / "mini_decide.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules["mini_decide"] = module
        spec.loader.exec_module(module)
        return module

    @staticmethod
    def _compiled(body: dict) -> object:
        import json
        import tempfile

        from creib.forge.mini.manifest import compile_manifest

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            return compile_manifest(path)

    def test_a_grid_manifest_compiles(self) -> None:
        driver = self._driver()
        for check in WORKING_SET:
            plan = self._compiled(driver._grid_manifest(check, 0))
            self.assertIn("conjecture", [stage.stage_id for stage in plan.stages])

    def test_a_decision_manifest_compiles_and_asks_for_one_call(self) -> None:
        driver = self._driver()
        plan = self._compiled(driver._decision_manifest("mini.decide1.test", brief(_state(), PLAIN)))
        self.assertEqual([stage.stage_id for stage in plan.stages], ["decide", "verdict", "end"])
        self.assertEqual(plan.kinds[driver.DECISION_KIND].commitment_call, "single")

    def test_the_grid_names_the_check_and_forbids_choosing_another(self) -> None:
        driver = self._driver()
        built = driver._grid_manifest(WORKING_SET[1], 3)
        self.assertIn(f"open:{WORKING_SET[1]}", built["problem"])
        self.assertIn("not yours to choose", built["problem"])
        self.assertEqual(built["endpoint"]["options"]["seed"], driver.SEED)

    def test_the_grid_is_at_least_as_long_as_the_longest_cut(self) -> None:
        driver = self._driver()
        self.assertGreaterEqual(driver.GRID_SEGMENTS, max(driver.CUTS))

    def test_every_declared_brief_is_put_at_every_point(self) -> None:
        driver = self._driver()
        self.assertEqual(set(driver.BRIEFS), set(BRIEFS))


class AddTests(unittest.TestCase):
    """The what-to-add family, which is asked and not scored. Its briefs still have to be honest."""

    def test_the_ladder_is_the_one_block_two_climbed(self) -> None:
        states = add_states()
        self.assertEqual([len(state.present) for state in states], [0, 1, 2])
        self.assertEqual(add_options(states[0])[0], ADD_NOTHING)
        self.assertEqual(len(add_options(states[0])), 1 + len(ADDITIONS))
        self.assertEqual(len(add_options(states[-1])), 2)

    def test_the_step_that_bundles_two_changes_says_so(self) -> None:
        text = add_brief(add_states()[0], PLAIN)
        self.assertIn("two changes, made together", text)

    def test_the_call_cost_of_each_step_is_shown(self) -> None:
        text = add_brief(add_states()[0], PLAIN)
        self.assertIn("This adds 2 model call(s) to every segment", text)
        self.assertIn("This adds no model call to a segment", text)

    def test_a_loop_carrying_the_costly_step_is_shown_the_higher_cost(self) -> None:
        self.assertEqual(add_states()[0].calls_per_segment, 3)
        self.assertEqual(add_states()[1].calls_per_segment, 5)
        self.assertIn("costs 5 model call(s) per segment", add_brief(add_states()[1], PLAIN))

    def test_relabelling_moves_the_ids_and_leaves_every_description_word_for_word(self) -> None:
        state = add_states()[0]
        plain, renamed = add_brief(state, PLAIN), add_brief(state, RELABELLED)
        for _, description, _ in ADDITIONS:
            self.assertIn(description, plain)
            self.assertIn(description, renamed)
        self.assertIn("add-part_two", renamed)
        self.assertNotIn("add-the-readings-port", renamed)

    def test_the_contrast_turns_what_the_loop_produced_around_and_moves_nothing_else(self) -> None:
        state = add_states()[0]
        swapped = add_contrast_of(state)
        self.assertEqual(swapped.present, state.present)
        self.assertEqual(swapped.segments, state.segments)
        self.assertEqual(swapped.calls_per_segment, state.calls_per_segment)
        self.assertEqual(swapped.real_classes, 0)
        self.assertEqual(add_contrast_of(swapped).real_classes, swapped.segments)

    def test_ablated_drops_the_figures_and_keeps_the_options(self) -> None:
        text = add_brief(add_states()[0], ABLATED)
        self.assertNotIn("## The loop as it stands", text)
        self.assertIn("## The options", text)

    def test_an_undeclared_addition_is_refused(self) -> None:
        with self.assertRaises(MiniError):
            AddState(state_id="x", present=("the-kitchen-sink",), segments=1, finds=0,
                     real_classes=0, calls_per_segment=3)

    def test_an_unknown_add_brief_is_refused(self) -> None:
        with self.assertRaises(MiniError):
            add_brief(add_states()[0], "quicker")

    def test_more_additions_than_neutral_names_is_refused(self) -> None:
        import creib.forge.mini.decide as module

        held = module.ADDITIONS
        try:
            module.ADDITIONS = held + (("a", "a", 0), ("b", "b", 0))
            with self.assertRaises(MiniError):
                module.add_relabelling(module.AddState(
                    state_id="x", present=(), segments=1, finds=0, real_classes=0,
                    calls_per_segment=3))
        finally:
            module.ADDITIONS = held
