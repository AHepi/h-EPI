"""The citation checker: every record id a document cites names exactly one record.

A cited sixteen-hex prefix resolves to one record file in this tree or to one path in
``docs/archived-records.txt``, which lists the records that live on another branch. A
prefix that names no record fails the check unless the sentence citing it says the record is
``not committed``, in which case the checker lists it so the reader sees the gap; a prefix that
names two records fails. The real tree is checked here too, so a citation that stops resolving
fails the suite and not only ``tools/check.py cite``.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

_spec = importlib.util.spec_from_file_location("check_tool", ROOT / "tools" / "check.py")
check = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check)

A = "a" * 16
B = "b" * 16
C = "c" * 16
D = "d" * 16


def _tree(root: Path, docs: dict[str, str], records: tuple[str, ...] = (), archived: str | None = None) -> None:
    for relative, text in docs.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    for relative in records:
        path = root / "forge" / "conformance" / "runs" / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf-8")
    if archived is not None:
        (root / "docs").mkdir(parents=True, exist_ok=True)
        (root / "docs" / "archived-records.txt").write_text(archived, encoding="utf-8")


class CiteCheckTests(unittest.TestCase):
    def test_a_cited_id_resolves_to_one_record_in_the_tree_or_the_archive_index(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _tree(
                root,
                {"docs/notes.md": f"Observation `{A}` and run `{B}`.\n", "README.md": f"See `{C}` on the archive branch.\n"},
                records=(f"pilot/observation.{A}.json", f"pilot/run.{B}.json"),
                archived=f"# comment\narchive/old forge/conformance/runs/old/observation.{C}.json\n",
            )
            result = check.cite_check(root)
            self.assertEqual(result["cited"], 3)
            self.assertEqual(result["resolved_in_tree"], 2)
            self.assertEqual(result["resolved_in_archive"], 1)
            self.assertEqual(result["problems"], [])
            self.assertEqual(result["declared_uncommitted"], [])

    def test_an_id_that_names_no_record_fails_unless_its_sentence_says_not_committed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _tree(root, {"docs/notes.md": f"Cites `{A}` freely.\nThe re-scored records are not committed (`{B}`).\n"})
            result = check.cite_check(root)
            self.assertEqual(len(result["problems"]), 1)
            self.assertIn(f"docs/notes.md:1 `{A}`", result["problems"][0])
            self.assertEqual(result["declared_uncommitted"], [f"docs/notes.md:2 `{B}`"])

    def test_an_id_carried_by_two_records_is_ambiguous(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _tree(root, {"agent.md": f"`{A}`\n"}, records=(f"one/observation.{A}.json", f"two/observation.{A}.json"))
            result = check.cite_check(root)
            self.assertEqual(len(result["problems"]), 1)
            self.assertIn("names 2 records", result["problems"][0])

    def test_a_malformed_archive_index_line_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _tree(root, {"docs/notes.md": "nothing cited\n"}, archived="archive/old not-a-record.txt\n")
            with self.assertRaises(SystemExit):
                check.cite_check(root)
            _tree(root, {}, archived="only-one-field\n")
            with self.assertRaises(SystemExit):
                check.cite_check(root)

    def test_files_outside_the_citing_set_are_not_read(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _tree(root, {"docs/notes.md": "clean\n", "src/thing.py": f"# `{D}` is not a citation\n"})
            self.assertEqual(check.cite_check(root)["cited"], 0)

    def test_this_tree_cites_only_records_that_exist(self) -> None:
        result = check.cite_check(ROOT)
        self.assertEqual(result["problems"], [], "\n".join(result["problems"]))
        self.assertGreater(result["resolved_in_tree"], 0)
        # H22 cites a re-score that its sentence says was not committed; nothing else may.
        self.assertTrue(all("failure-modes.md" in line for line in result["declared_uncommitted"]), result["declared_uncommitted"])


if __name__ == "__main__":
    unittest.main()
