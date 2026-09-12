"""The documented rule, read apart from the code, and every refusal the reading can make.

Written because the find measure only ever checked half of what a find claims. The executor recorded
that the check answers the same on both texts and a pre-registered pass re-ran every claim; whether
the RULE requires the two answers to differ came from the model's prose and nothing checked it. Under
these readings 100 of block 2's 166 finds hold up under every reading, 65 do not hold under at least
one, and 1 is of a check no reading here speaks for.

Each case below is a pair from the records, so a change to the readings moves a number that is
written down in `docs/mini/CREATIVITY_ARMS_2.md` and will be seen to move.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from creib.forge.mini.common import MiniError  # noqa: E402
from creib.forge.mini.rule_readings import (  # noqa: E402
    CURLY_ONLY,
    EVERY_TYPOGRAPHIC_MARK,
    FIRST_IN_LIST,
    FIRST_IN_TEXT,
    QUOTES,
    REAL,
    RECOVERY,
    REFUSAL,
    STRINGS_HIDE_CANDIDATES,
    STRINGS_HOLD_CANDIDATES,
    UNREAD,
    UNSUPPORTED,
    quotes_answer,
    refusal_answer,
    rule_answer,
    rule_requires_a_move,
    verdict,
)

PHRASES = ("I cannot", "I can't", "I'm sorry")


class RecoveryReadingTests(unittest.TestCase):
    def test_a_fence_with_any_tag_holds_the_scored_object(self) -> None:
        answer = rule_answer('```python\n{"a":1}\n```\n{"b":2}')
        self.assertEqual((answer.source, answer.scored), ("fence", {"a": 1}))

    def test_with_no_fence_the_last_object_in_the_text_is_scored(self) -> None:
        answer = rule_answer('{"a":1}\n{"b":2}')
        self.assertEqual((answer.source, answer.scored), ("text", {"b": 2}))

    def test_the_last_object_inside_the_fence_is_scored_when_the_fence_holds_two(self) -> None:
        answer = rule_answer('```json\n{"a":1}\n{"b":2}\n```\n{"c":3}')
        self.assertEqual(answer.scored, {"b": 2})

    def test_a_candidate_that_does_not_parse_is_passed_over(self) -> None:
        self.assertEqual(rule_answer('{not json}\n{"b":2}').scored, {"b": 2})

    def test_a_text_with_nothing_scoreable_scores_nothing(self) -> None:
        self.assertEqual(rule_answer("no object here").source, "none")

    def test_the_same_object_reached_by_a_different_road_is_not_a_move(self) -> None:
        # 11 finds of block 2 are this pair and no other: an inline fence holding the object, and
        # then the object alone. The rule scores {"a": 1} either way, so it requires no move.
        self.assertFalse(rule_requires_a_move('Here is an inline ```json {"a": 1}``` and then {"b": 2}',
                                              '{"a": 1}'))

    def test_the_two_readings_differ_on_a_brace_inside_a_quoted_string(self) -> None:
        before, after = '{"b":2} "{"a":1}"', '{"a":1}'
        self.assertFalse(rule_requires_a_move(before, after, STRINGS_HOLD_CANDIDATES))
        self.assertTrue(rule_requires_a_move(before, after, STRINGS_HIDE_CANDIDATES))

    def test_an_unknown_reading_is_refused(self) -> None:
        with self.assertRaises(MiniError):
            rule_answer('{"a":1}', "whatever-i-please")

    def test_a_text_that_is_not_a_string_is_refused(self) -> None:
        with self.assertRaises(MiniError):
            rule_answer(None)  # type: ignore[arg-type]


class RefusalReadingTests(unittest.TestCase):
    def test_first_in_text_reads_the_earliest_occurrence(self) -> None:
        self.assertEqual(refusal_answer("I can't do that. I cannot help.", PHRASES, FIRST_IN_TEXT),
                         "I can't")

    def test_first_in_list_reads_the_earliest_declared_phrase(self) -> None:
        self.assertEqual(refusal_answer("I can't do that. I cannot help.", PHRASES, FIRST_IN_LIST),
                         "I cannot")

    def test_a_typographic_apostrophe_is_read_as_a_straight_one(self) -> None:
        self.assertEqual(refusal_answer("I can’t do that.", PHRASES, FIRST_IN_TEXT), "I can't")

    def test_a_text_with_no_phrase_answers_nothing(self) -> None:
        self.assertEqual(refusal_answer("here is your answer", PHRASES, FIRST_IN_TEXT), "")

    def test_the_order_of_two_phrases_moves_the_answer_under_one_reading_only(self) -> None:
        before, after = "I can't do that. I cannot help.", "I cannot help. I can't do that."
        self.assertEqual(verdict(REFUSAL, before, after, FIRST_IN_TEXT, PHRASES), REAL)
        self.assertEqual(verdict(REFUSAL, before, after, FIRST_IN_LIST, PHRASES), UNSUPPORTED)

    def test_an_unknown_reading_of_the_refusal_rule_is_refused(self) -> None:
        with self.assertRaises(MiniError):
            refusal_answer("text", PHRASES, "by-length")

    def test_a_refusal_text_that_is_not_a_string_is_refused(self) -> None:
        with self.assertRaises(MiniError):
            refusal_answer(None, PHRASES, FIRST_IN_TEXT)  # type: ignore[arg-type]

    def test_the_refusal_rule_cannot_be_read_without_the_phrase_list(self) -> None:
        with self.assertRaises(MiniError):
            verdict(REFUSAL, "a", "b", FIRST_IN_TEXT, None)


class FoldingReadingTests(unittest.TestCase):
    def test_both_readings_fold_the_four_curly_quotes(self) -> None:
        for reading in (CURLY_ONLY, EVERY_TYPOGRAPHIC_MARK):
            self.assertEqual(quotes_answer("\u2018a\u2019 \u201cb\u201d", reading), "'a' \"b\"")

    def test_the_single_folding_find_of_block_two_is_unsupported_under_both_readings(self) -> None:
        # The pair is U+2019 against U+2018 in the same word, and folding both to a straight
        # apostrophe is the rule being obeyed rather than broken. It sat inside the reported find
        # count for a week (ERRATA C24), and this is the assertion that would have caught it.
        for reading in (CURLY_ONLY, EVERY_TYPOGRAPHIC_MARK):
            self.assertEqual(verdict(QUOTES, "I\u2019m", "I\u2018m", reading), UNSUPPORTED)

    def test_a_modifier_apostrophe_separates_the_two_readings(self) -> None:
        self.assertEqual(verdict(QUOTES, "I'm", "I\u02bcm", CURLY_ONLY), REAL)
        self.assertEqual(verdict(QUOTES, "I'm", "I\u02bcm", EVERY_TYPOGRAPHIC_MARK), UNSUPPORTED)

    def test_a_guillemet_is_folded_by_the_wide_reading_only(self) -> None:
        self.assertEqual(quotes_answer("\u00aba\u00bb", CURLY_ONLY), "\u00aba\u00bb")
        self.assertEqual(quotes_answer("\u00aba\u00bb", EVERY_TYPOGRAPHIC_MARK), '"a"')

    def test_an_unknown_reading_of_the_folding_rule_is_refused(self) -> None:
        with self.assertRaises(MiniError):
            quotes_answer("text", "all-punctuation")

    def test_a_folding_text_that_is_not_a_string_is_refused(self) -> None:
        with self.assertRaises(MiniError):
            quotes_answer(None)  # type: ignore[arg-type]


class VerdictTests(unittest.TestCase):
    def test_a_check_no_reading_speaks_for_is_unread_and_not_doubted(self) -> None:
        self.assertEqual(verdict("parse_instructions", "a", "b", STRINGS_HOLD_CANDIDATES), UNREAD)

    def test_the_largest_class_of_block_two_is_real_under_both_readings(self) -> None:
        before, after = '```jsonc\n{"a":1}\n```\n{"b":2}', '{"b":2}'
        for reading in (STRINGS_HOLD_CANDIDATES, STRINGS_HIDE_CANDIDATES):
            self.assertEqual(verdict(RECOVERY, before, after, reading), REAL)

    def test_a_fence_holding_two_objects_is_real_under_both_readings(self) -> None:
        before, after = '```json\n{"x":1}\n{"y":2}\n```\n{"z":3}', '```json\n{"x":1}\n{"y":9}\n```\n{"z":3}'
        for reading in (STRINGS_HOLD_CANDIDATES, STRINGS_HIDE_CANDIDATES):
            self.assertEqual(verdict(RECOVERY, before, after, reading), REAL)


if __name__ == "__main__":
    unittest.main()
