"""Every boundary point holds: the verdict moves under the one transformation and not under the other.

The points are the catalogue in ``kernel_boundaries.py``; ``docs/kernel.md`` is generated from
the same catalogue by ``tools/kernel_table.py``, and the last test refuses a document that has
drifted from it. A point that fails because a check now sees what it says it cannot is the
boundary moving: rewrite the point and regenerate the document in the same change.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))

import kernel_boundaries  # noqa: E402

_spec = importlib.util.spec_from_file_location("kernel_table_tool", ROOT / "tools" / "kernel_table.py")
kernel_table = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(kernel_table)


class KernelBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.points = kernel_boundaries.boundaries()

    def test_every_point_moves_under_one_transformation_and_not_the_other(self) -> None:
        for point in self.points:
            with self.subTest(point=point.point):
                base, moved, unchanged = point.evaluate()
                if point.moves_under is None:
                    self.assertIsNone(moved, f"{point.point} declares nothing moves the verdict but supplies a moved verdict")
                else:
                    self.assertIsNotNone(moved, f"{point.point} declares a transformation the verdict moves under but supplies no verdict for it")
                    self.assertNotEqual(moved, base, f"{point.point}: the verdict did not move under: {point.moves_under}")
                self.assertEqual(unchanged, base, f"{point.point}: the verdict moved under what the point says it cannot see: {point.unchanged_under}")

    def test_points_are_named_once_and_cover_every_check_in_the_table(self) -> None:
        ids = [p.point for p in self.points]
        self.assertEqual(len(ids), len(set(ids)))
        checks = {p.check.split(":")[0].strip("`").lower() for p in self.points}
        for named in ("schema", "`exact` oracle", "`any_of` oracle", "`unknown` oracle", "span occurrence", "value in span", "change against the baseline",
                      "refusal heuristic", "routing", "appraisal standing", "records directory", "citation check", "unit splitting", "transport kind"):
            self.assertIn(named.strip("`").lower(), checks, f"no point for {named}")

    def test_the_document_is_generated_from_the_catalogue(self) -> None:
        rendered = kernel_table.render(self.points)
        committed = (ROOT / "docs" / "kernel.md").read_text(encoding="utf-8")
        self.assertEqual(committed, rendered, "docs/kernel.md has drifted from tests/kernel_boundaries.py; run python tools/kernel_table.py")


if __name__ == "__main__":
    unittest.main()
