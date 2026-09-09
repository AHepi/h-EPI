"""The closed-list vocabulary rule (``docs/kernel.md``, V-01) against the committed controls records.

``controls`` says a list item is on a page when the item is a substring of the page's text, so
``K-A`` is on a page that holds only ``K-ALPHA``. The kernel point keeps the rule with the note
that on the committed controls records every renamed-vocabulary row is the same under a
longest-match rule and under a word-boundary rule. This test is that comparison: it recomputes
the renamed rows of every committed controls directory under the three rules and refuses a
difference. A future corpus whose vocabulary nests can move a row; when it does, this test
names the row, and the rule is a decision to make with the record in view, not a note to trust.
"""

from __future__ import annotations

from pathlib import Path
import re
from typing import Callable
import unittest
from unittest import mock

from creib.forge.conformance import load_corpus, load_pilot_config
from creib.forge.conformance import controls as controls_module
from creib.forge.conformance.records import enumerate_record_directory, load_observation_directory, load_run

ROOT = Path(__file__).resolve().parents[1]
PILOTS = ROOT / "forge" / "conformance" / "pilots"
RUNS = ROOT / "forge" / "conformance" / "runs"
DIRECTORIES = (("semantics-unit-controls", "semantics-unit-controls"), ("ecs-unit-controls", "ecs-unit-controls"))

Rule = Callable[[str, str, frozenset[str]], bool]


def substring(item: str, text: str, _items: frozenset[str]) -> bool:
    return item in text


def longest_match(item: str, text: str, items: frozenset[str]) -> bool:
    """Present when some occurrence of the item is not inside an occurrence of a longer item."""

    longer = [other for other in items if other != item and item in other]
    covering = [(m.start(), m.end()) for other in longer for m in re.finditer(re.escape(other), text)]
    for match in re.finditer(re.escape(item), text):
        if not any(start <= match.start() and match.end() <= end for start, end in covering):
            return True
    return False


def word_boundary(item: str, text: str, _items: frozenset[str]) -> bool:
    return re.search(r"(?<![A-Za-z0-9])" + re.escape(item) + r"(?![A-Za-z0-9])", text) is not None


def _items_of(observation) -> frozenset[str]:
    properties = observation.variant.form_schema.get("properties", {})
    found: set[str] = set()
    for field in controls_module._array_fields(observation):
        found.update(str(item) for item in (((properties.get(field) or {}).get("items") or {}).get("enum") or []))
    return frozenset(found)


def _vocabularies_under(rule: Rule):
    def vocabularies(full, renamed):
        items = _items_of(full)
        full_text = full.variant.input_document or ""
        renamed_text = renamed.variant.input_document or ""
        on_full = frozenset(item for item in items if rule(item, full_text, items))
        on_renamed = frozenset(item for item in items if rule(item, renamed_text, items) and item not in on_full)
        return on_full, on_renamed
    return vocabularies


def _loaded(pilot: str, directory: str):
    config = load_pilot_config(PILOTS / pilot / "pilot.json")
    corpus = load_corpus(config.corpus_path, config.spec)
    observations = load_observation_directory(RUNS / directory)
    runs = [load_run(path) for path in enumerate_record_directory(RUNS / directory).run_paths]
    return corpus, runs, observations


def _renamed_rows(loaded, rule: Rule) -> dict[tuple[str, str], tuple[int, int, int, int]]:
    corpus, runs, observations = loaded
    with mock.patch.object(controls_module, "_vocabularies", _vocabularies_under(rule)):
        summary = controls_module.summarise_controls(corpus, runs, observations)
    return {
        (row["model"], row["run_id"]): (row["replies_on_page_vocabulary"], row["replies_removed_vocabulary"], row["replies_both"], row["replies_empty"])
        for row in summary["rows"] if row["kind"] == "renamed"
    }


class VocabularyRuleTests(unittest.TestCase):
    def test_the_rules_differ_where_the_list_nests(self) -> None:
        items = frozenset({"K-A", "K-ALPHA"})
        self.assertTrue(substring("K-A", "only K-ALPHA here", items))
        self.assertFalse(longest_match("K-A", "only K-ALPHA here", items))
        self.assertFalse(word_boundary("K-A", "only K-ALPHA here", items))
        self.assertTrue(longest_match("K-A", "K-A and K-ALPHA here", items))
        self.assertTrue(word_boundary("K-A", "K-A and K-ALPHA here", items))

    def test_every_committed_renamed_row_is_the_same_under_the_three_rules(self) -> None:
        for pilot, directory in DIRECTORIES:
            with self.subTest(directory=directory):
                loaded = _loaded(pilot, directory)
                under = {name: _renamed_rows(loaded, rule) for name, rule in (("substring", substring), ("longest_match", longest_match), ("word_boundary", word_boundary))}
                self.assertTrue(under["substring"], "the directory holds renamed rows")
                for name in ("longest_match", "word_boundary"):
                    differing = {key: (under["substring"][key], under[name][key]) for key in under["substring"] if under["substring"][key] != under[name].get(key)}
                    self.assertEqual(differing, {}, f"renamed rows that move under the {name} rule (on-page, removed, both, empty)")


if __name__ == "__main__":
    unittest.main()
