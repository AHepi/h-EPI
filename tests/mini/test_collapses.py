"""The collapse-class reading partitions finds by a stated shape, and says so where it cannot see.

Written with the reading itself, because the reading changes which arm of block 2 leads: counted as
finds, ``A`` leads per segment; counted as classes, ``W`` does. A measure that reorders a result has
to be pinned, and the two boundary assertions below are the cases the module docstring says it
cannot separate -- if either starts to pass, the docstring is wrong and both move together.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from creib.forge.mini.common import MiniError  # noqa: E402
from creib.forge.mini.collapses import (  # noqa: E402
    BRACE_CAP,
    Shape,
    class_of,
    classes_of,
    is_find,
    ran,
    shape_of,
)


def _find(before: str, after: str, kernel: str = "open:creib.forge.conformance.oracle.f") -> dict:
    return {"expect": "moves", "executed": "unchanged", "kernel": kernel,
            "input": before, "rewritten": after}


class ShapeTests(unittest.TestCase):
    def test_a_fence_the_checks_pattern_matches_is_told_from_one_it_does_not(self) -> None:
        self.assertEqual(shape_of('```json\n{"a":1}\n```').fence, "json_or_bare")
        self.assertEqual(shape_of('```JSON\n{"a":1}\n```').fence, "json_or_bare")
        self.assertEqual(shape_of('```\n{"a":1}\n```').fence, "json_or_bare")
        self.assertEqual(shape_of('```python\n{"a":1}\n```').fence, "other_tag")
        self.assertEqual(shape_of('```Json\n{"a":1}\n```').fence, "other_tag")

    def test_no_fence_at_all_is_its_own_answer_and_not_a_matched_one(self) -> None:
        self.assertEqual(shape_of('{"a":1}').fence, "absent")

    def test_brace_groups_are_counted_inside_the_fence_and_outside_it_separately(self) -> None:
        shape = shape_of('```json\n{"a":1}\n{"b":2}\n```\n{"c":3}')
        self.assertEqual((shape.braced_inside, shape.braced_outside), (2, 1))

    def test_a_brace_group_inside_a_quoted_string_is_marked(self) -> None:
        self.assertTrue(shape_of('{"b":2} "{"a":1}"').braced_in_quotes)
        self.assertFalse(shape_of('{"b":2}').braced_in_quotes)

    def test_a_text_that_is_not_a_string_is_refused(self) -> None:
        with self.assertRaises(MiniError):
            shape_of(None)  # type: ignore[arg-type]


class BoundaryTests(unittest.TestCase):
    """The two things the docstring says the reading cannot see. Both must keep failing to see them."""

    def test_it_cannot_tell_a_parsing_brace_group_from_one_that_does_not_parse(self) -> None:
        self.assertEqual(shape_of('{"a":1}'), shape_of('{not json at all}'))

    def test_it_cannot_tell_four_brace_groups_from_five(self) -> None:
        four = "".join('{"a":1}' for _ in range(BRACE_CAP + 1))
        five = "".join('{"a":1}' for _ in range(BRACE_CAP + 2))
        self.assertEqual(shape_of(four), shape_of(five))
        self.assertEqual(shape_of(four).braced_outside, BRACE_CAP)

    def test_it_does_tell_the_cap_from_one_below_it(self) -> None:
        below = "".join('{"a":1}' for _ in range(BRACE_CAP - 1))
        at = "".join('{"a":1}' for _ in range(BRACE_CAP))
        self.assertNotEqual(shape_of(below), shape_of(at))


class RouteTests(unittest.TestCase):
    def test_a_route_is_the_check_and_both_shapes(self) -> None:
        klass = class_of(_find('```python\n{"a":1}\n```\n{"b":2}', '{"b":2}'))
        self.assertEqual(klass.check, "f")
        self.assertEqual(klass.before.fence, "other_tag")
        self.assertEqual(klass.after.fence, "absent")

    def test_two_finds_differing_only_in_which_other_tag_share_one_route(self) -> None:
        first = class_of(_find('```python\n{"a":1}\n```\n{"b":2}', '{"b":2}'))
        second = class_of(_find('```javascript\n{"x":9}\n```\n{"y":8}', '{"y":8}'))
        self.assertEqual(first, second)

    def test_two_finds_on_different_checks_never_share_a_route(self) -> None:
        first = class_of(_find("a", "b", kernel="open:m.one"))
        second = class_of(_find("a", "b", kernel="open:m.two"))
        self.assertNotEqual(first, second)

    def test_a_row_that_is_not_a_find_has_no_route(self) -> None:
        with self.assertRaises(MiniError):
            class_of({"expect": "moves", "executed": "moved", "kernel": "open:m.f",
                      "input": "a", "rewritten": "b"})

    def test_a_find_that_names_no_check_is_refused(self) -> None:
        with self.assertRaises(MiniError):
            class_of({"expect": "moves", "executed": "unchanged", "kernel": "",
                      "input": "a", "rewritten": "b"})

    def test_routes_of_passes_over_rows_that_are_not_finds(self) -> None:
        rows = [_find("a", "b"), {"expect": "moves", "executed": "moved", "kernel": "open:m.f",
                                  "input": "a", "rewritten": "b"},
                {"expect": "unchanged", "executed": "unchanged", "kernel": "open:m.f",
                 "input": "a", "rewritten": "b"}]
        self.assertEqual(len(classes_of(rows)), 1)

    def test_ran_and_is_find_read_the_executors_own_words(self) -> None:
        self.assertTrue(ran({"executed": "moved"}))
        self.assertTrue(ran({"executed": "unchanged"}))
        self.assertFalse(ran({"executed": "unrunnable"}))
        self.assertFalse(is_find({"expect": "unchanged", "executed": "unchanged"}))

    def test_a_shape_row_is_hashable_so_routes_can_be_counted(self) -> None:
        self.assertEqual(len({shape_of('{"a":1}'), shape_of('{"b":2}')}), 1)
        self.assertIsInstance(Shape("absent", 0, 0, False).as_row(), tuple)


if __name__ == "__main__":
    unittest.main()
