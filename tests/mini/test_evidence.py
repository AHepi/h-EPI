"""R12: evidence split and tagged, and every citation byte-checked."""

from __future__ import annotations

import copy

from creib.forge.mini.evidence import (
    CITATION_AMBIGUOUS,
    CITATION_QUOTE_MISMATCH,
    CITATION_UNKNOWN_BLOCK,
    CITATION_VERIFIED,
    CITATION_WITHHELD,
    check_citations,
    cut_source,
    folded,
    render_legend,
)
from creib.forge.mini.log import ARTIFACT_SUBMITTED, EVIDENCE_BATCHED

from .helpers import MiniTestCase, base_manifest, submission

TEXT = "The first paragraph says one thing.\n\nThe second paragraph says another thing entirely.\n\nA third."


class CuttingTests(MiniTestCase):
    def test_cutting_is_deterministic_and_content_addressed(self) -> None:
        first = cut_source("s1", TEXT.encode("utf-8"), "evidence")
        second = cut_source("s1", TEXT.encode("utf-8"), "evidence")
        self.assertEqual([block.block_id for block in first], [block.block_id for block in second])
        self.assertEqual(len(first), 3)

    def test_a_block_carries_the_byte_span_it_was_cut_from(self) -> None:
        raw = TEXT.encode("utf-8")
        for block in cut_source("s1", raw, "evidence"):
            self.assertEqual(raw[block.span_start : block.span_end].decode("utf-8"), block.text)

    def test_one_changed_byte_gives_different_block_ids(self) -> None:
        first = cut_source("s1", TEXT.encode("utf-8"), "evidence")
        second = cut_source("s1", TEXT.replace("first", "third").encode("utf-8"), "evidence")
        self.assertNotEqual(first[0].block_id, second[0].block_id)

    def test_the_tier_tag_is_carried_on_every_block(self) -> None:
        blocks = cut_source("s1", TEXT.encode("utf-8"), "generated")
        self.assertEqual({block.tier for block in blocks}, {"generated"})

    def test_a_source_that_is_not_utf8_is_refused(self) -> None:
        self.assertRefuses("MINI_SOURCE_INVALID", cut_source, "s1", b"\xff\xfe not text", "evidence")

    def test_a_source_of_only_whitespace_cuts_to_nothing(self) -> None:
        self.assertEqual(cut_source("s1", b"\n\n   \n\n", "evidence"), ())

    def test_the_legend_lists_ids_and_excerpts(self) -> None:
        blocks = cut_source("s1", TEXT.encode("utf-8"), "evidence")
        rendered = render_legend(blocks, "## Evidence")
        for block in blocks:
            self.assertIn(block.block_id[:16], rendered)
        self.assertIn("first paragraph", rendered)

    def test_an_empty_legend_says_so(self) -> None:
        self.assertIn("nothing admitted", render_legend((), "## Evidence"))

    def test_folding_never_joins_words_the_source_separated(self) -> None:
        self.assertEqual(folded("a   b\n c"), "a b c")
        self.assertNotIn("ab", folded("a b"))


class CitationTests(MiniTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.blocks = {block.block_id: block for block in cut_source("s1", TEXT.encode("utf-8"), "evidence")}
        self.ids = list(self.blocks)
        self.exposed = frozenset(self.ids)

    def _one(self, citation: dict, exposed: frozenset[str] | None = None):
        return check_citations([citation], self.blocks, self.exposed if exposed is None else exposed)[0]

    def test_a_good_citation_verifies(self) -> None:
        measure = self._one({"block": self.ids[0][:16], "quote": "first paragraph"})
        self.assertEqual(measure.code, CITATION_VERIFIED)
        self.assertEqual(measure.block_id, self.ids[0])

    def test_a_citation_with_no_quote_verifies_as_unquoted(self) -> None:
        measure = self._one({"block": self.ids[0]})
        self.assertEqual(measure.code, CITATION_VERIFIED)
        self.assertFalse(measure.quoted)

    def test_a_citation_to_an_unknown_id(self) -> None:
        self.assertEqual(self._one({"block": "deadbeef" * 8}).code, CITATION_UNKNOWN_BLOCK)

    def test_a_citation_naming_no_block_at_all(self) -> None:
        self.assertEqual(self._one({"quote": "x"}).code, CITATION_UNKNOWN_BLOCK)

    def test_a_citation_to_a_withheld_id(self) -> None:
        measure = self._one({"block": self.ids[0], "quote": "first paragraph"}, exposed=frozenset())
        self.assertEqual(measure.code, CITATION_WITHHELD)
        self.assertEqual(measure.block_id, self.ids[0])

    def test_a_citation_with_a_misquote(self) -> None:
        self.assertEqual(self._one({"block": self.ids[0], "quote": "words never written"}).code, CITATION_QUOTE_MISMATCH)

    def test_a_quote_that_joins_words_the_source_separated_fails(self) -> None:
        self.assertEqual(self._one({"block": self.ids[0], "quote": "firstparagraph"}).code, CITATION_QUOTE_MISMATCH)

    def test_a_quote_whose_only_difference_is_line_wrapping_verifies(self) -> None:
        self.assertEqual(self._one({"block": self.ids[0], "quote": "first\n  paragraph"}).code, CITATION_VERIFIED)

    def test_an_ambiguous_prefix(self) -> None:
        measures = check_citations([{"block": ""}], self.blocks, self.exposed)
        self.assertEqual(measures[0].code, CITATION_UNKNOWN_BLOCK)
        shared = self.ids[0][:1]
        matching = [block_id for block_id in self.ids if block_id.startswith(shared)]
        if len(matching) > 1:
            self.assertEqual(self._one({"block": shared}).code, CITATION_AMBIGUOUS)


class CitationsOnTheRecordTests(MiniTestCase):
    def test_the_measures_are_on_the_record_and_change_nothing(self) -> None:
        manifest = base_manifest()
        plan = self.compile(manifest)
        blocks = cut_source("s1", manifest["sources"][0]["text"].encode("utf-8"), "evidence")
        script = {
            "c1": [
                submission(
                    "A conjecture.",
                    "c",
                    citations=[
                        {"block": blocks[0].block_id[:16], "quote": "first paragraph"},
                        {"block": "0" * 64, "quote": "x"},
                    ],
                )
            ],
            "x1": [submission("An objection.", "c")],
        }
        outcome = self.run_plan(plan, script)
        submitted = self.events_of(outcome, ARTIFACT_SUBMITTED)[0]
        codes = [item["code"] for item in submitted["payload"]["citations"]]
        self.assertEqual(codes, [CITATION_VERIFIED, CITATION_UNKNOWN_BLOCK])
        self.assertEqual(len(self.events_of(outcome, ARTIFACT_SUBMITTED)), 2)
        self.assertEqual(outcome.stop_reason, "end_stage")

    def test_a_block_routed_nowhere_is_never_shown_and_a_citation_to_it_is_withheld(self) -> None:
        manifest = base_manifest()
        manifest["routing"] = {"evidence": [{"from_tier": "evidence", "to": {"target": "nowhere"}}]}
        plan = self.compile(manifest)
        blocks = cut_source("s1", manifest["sources"][0]["text"].encode("utf-8"), "evidence")
        script = {
            "c1": [submission("A conjecture.", "c", citations=[{"block": blocks[0].block_id, "quote": "first paragraph"}])],
            "x1": [submission("An objection.", "c")],
        }
        outcome = self.run_plan(plan, script)
        submitted = self.events_of(outcome, ARTIFACT_SUBMITTED)[0]
        self.assertEqual(submitted["payload"]["citations"][0]["code"], CITATION_WITHHELD)

    def test_supplied_sources_are_batched_into_blocks_on_the_record(self) -> None:
        _, outcome = self.run_manifest(base_manifest())
        batched = self.events_of(outcome, EVIDENCE_BATCHED)
        self.assertEqual(len(batched), 1)
        self.assertEqual(len(batched[0]["payload"]["blocks"]), 2)
        self.assertEqual(batched[0]["payload"]["tier"], "evidence")

    def test_a_manifest_may_extend_the_tier_vocabulary(self) -> None:
        manifest = base_manifest()
        manifest["tiers"] = [{"tier": "memory"}]
        manifest["sources"].append({"source_id": "s2", "text": "Remembered.", "tier": "memory"})
        manifest["kinds"][0]["input_ports"][1]["params"] = {"tiers": ["evidence", "memory"]}
        _, outcome = self.run_manifest(manifest)
        tiers = {event["payload"]["tier"] for event in self.events_of(outcome, EVIDENCE_BATCHED)}
        self.assertEqual(tiers, {"evidence", "memory"})

    def test_a_source_tagged_with_an_undeclared_tier_is_refused(self) -> None:
        manifest = base_manifest()
        manifest["sources"][0]["tier"] = "hearsay"
        self.assertRefuses("MINI_TIER_UNKNOWN", self.compile, manifest)

    def test_a_tier_declared_twice_is_refused(self) -> None:
        manifest = base_manifest()
        manifest["tiers"] = [{"tier": "evidence"}]
        self.assertRefuses("MINI_TIER_DUPLICATE", self.compile, manifest)

    def test_a_source_from_a_file_is_read(self) -> None:
        (self.tmp / "note.txt").write_text("From a file.\n\nSecond bit.", encoding="utf-8")
        manifest = base_manifest()
        manifest["sources"] = [{"source_id": "s1", "path": "note.txt"}]
        _, outcome = self.run_manifest(manifest)
        self.assertEqual(len(self.events_of(outcome, EVIDENCE_BATCHED)[0]["payload"]["blocks"]), 2)

    def test_a_source_naming_both_text_and_a_path_is_refused(self) -> None:
        manifest = base_manifest()
        manifest["sources"] = [{"source_id": "s1", "text": "x", "path": "note.txt"}]
        self.assertRefuses("MINI_SOURCE_INVALID", self.compile, manifest)

    def test_a_source_naming_a_file_that_is_not_there_is_refused(self) -> None:
        manifest = base_manifest()
        manifest["sources"] = [{"source_id": "s1", "path": "absent.txt"}]
        self.assertRefuses("MINI_SOURCE_INVALID", self.compile, manifest)

    def test_a_source_id_declared_twice_is_refused(self) -> None:
        manifest = base_manifest()
        manifest["sources"] = [{"source_id": "s1", "text": "a"}, {"source_id": "s1", "text": "b"}]
        self.assertRefuses("MINI_SOURCE_INVALID", self.compile, manifest)
