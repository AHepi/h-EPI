from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

from creib.canonical import bytes_digest, canonical_bytes
from creib.errors import RecordError
from creib.forge import source_replay
from creib.forge.source_replay import (
    PDF_WORD_ALGORITHM,
    PDF_WORD_DIGEST_DOMAIN,
    PDF_WORD_SELECTION_RULE,
    PDF_WORD_TOOL,
    SourceReplayMismatch,
    UTF8_RANGE_ALGORITHM,
    UTF8_RANGE_DIGEST_DOMAIN,
    UTF8_RANGE_SELECTION_RULE,
    UTF8_RANGE_TOOL,
    UTF8_RANGE_TOOL_VERSION,
    replay_translation_sources,
)
from creib.forge.translation import (
    TranslationValidationResult,
    compute_translation_record_id,
)


def _provenance() -> dict[str, object]:
    return {
        "producer_kind": "HUMAN",
        "producer_id": "source-replay-test",
        "created_at": "2026-09-03T00:00:00Z",
        "generation_record_ids": [],
    }


def _seal(record: dict[str, object]) -> dict[str, object]:
    fields = {
        "creib.semantic-forge.translation-source-document.v1": "document_id",
        "creib.semantic-forge.translation-source-span.v1": "span_id",
    }
    field = fields[str(record["schema_version"])]
    record[field] = compute_translation_record_id(record)
    return record


def _literal(selected: bytes) -> dict[str, object]:
    digest = hashlib.sha256(
        UTF8_RANGE_DIGEST_DOMAIN.encode("ascii") + b"\0" + selected
    ).hexdigest()
    return {
        "algorithm": UTF8_RANGE_ALGORITHM,
        "tool": UTF8_RANGE_TOOL,
        "tool_version": UTF8_RANGE_TOOL_VERSION,
        "selection_rule": UTF8_RANGE_SELECTION_RULE,
        "item_count": len(selected),
        "digest_domain": UTF8_RANGE_DIGEST_DOMAIN,
        "sha256": digest,
    }


class TranslationSourceReplayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.raw = "prefix α exact claim\nsuffix\n".encode("utf-8")
        self.source_path = self.root / "authority.md"
        self.source_path.write_bytes(self.raw)
        self.selected = "α exact claim".encode("utf-8")
        self.start = self.raw.index(self.selected)
        self.end = self.start + len(self.selected)
        self.document = _seal(
            {
                "schema_version": (
                    "creib.semantic-forge.translation-source-document.v1"
                ),
                "document_id": "",
                "supersedes_document_id": None,
                "document_key": "authority",
                "title": "Authority",
                "artifact": {
                    "supplied_filename": "authority.md",
                    "media_type": "text/markdown",
                    "sha256": bytes_digest(self.raw),
                    "byte_length": len(self.raw),
                },
                "structure": {
                    "kind": "UTF8_TEXT",
                    "page_count": None,
                    "encoding": "UTF-8",
                },
                "legacy_refs": [],
                "provenance": _provenance(),
            }
        )
        self.span = self.make_span()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def make_span(
        self,
        *,
        start: int | None = None,
        end: int | None = None,
        literal: dict[str, object] | None = None,
        reviewed: dict[str, object] | None = None,
        locator_kind: str = "UTF8_BYTE_RANGE",
    ) -> dict[str, object]:
        if locator_kind == "UTF8_BYTE_RANGE":
            locator: dict[str, object] = {
                "kind": locator_kind,
                "start_byte": self.start if start is None else start,
                "end_byte_exclusive": self.end if end is None else end,
                "encoding": "UTF-8",
            }
        else:
            locator = {
                "kind": "PDF_REGION",
                "physical_page": 1,
                "page_index_zero_based": 0,
                "printed_label": None,
                "section_raw": None,
                "page_size_millipoints": [612000, 792000],
                "page_rotation_degrees": 0,
                "bbox_millipoints": [0, 0, 612000, 792000],
            }
        return _seal(
            {
                "schema_version": "creib.semantic-forge.translation-source-span.v1",
                "span_id": "",
                "supersedes_span_id": None,
                "document_id": self.document["document_id"],
                "span_key": "exact-claim",
                "segments": [
                    {
                        "ordinal": 1,
                        "locator": locator,
                        "literal_snapshot": literal or _literal(self.selected),
                        "reviewed_transcription": reviewed,
                    }
                ],
                "context_span_ids": [],
                "legacy_refs": [],
                "source_inferential_status": None,
                "provenance": _provenance(),
            }
        )

    def replay(
        self,
        *,
        span: dict[str, object] | None = None,
        statement: str = "α exact claim",
        document: dict[str, object] | None = None,
    ):
        active_document = document or self.document
        active_span = span or self.span
        document_id = str(active_document["document_id"])
        span_id = str(active_span["span_id"])
        graph_id = "graph"
        snapshot = {
            "snapshot_id": "snapshot-under-test",
            "document_ids": [document_id],
            "span_ids": [span_id],
            "graph_id": graph_id,
        }
        validation = TranslationValidationResult(
            snapshot_id="snapshot-under-test",
            record_count=3,
            unresolved_record_ids=(),
        )
        records = {
            document_id: active_document,
            span_id: active_span,
            graph_id: {
                "obligations": [
                    {
                        "source_claim": {
                            "claim_id": "claim-a",
                            "claim_kind": "SOURCE_AUTHORITY",
                            "expression_mode": "VERBATIM_TRANSCRIPTION",
                            "statement": statement,
                            "source_span_ids": [span_id],
                            "source_marks_raw": [],
                        }
                    }
                ]
            },
        }
        with mock.patch(
            "creib.forge.source_replay.validate_translation_snapshot",
            return_value=validation,
        ):
            return replay_translation_sources(
                snapshot=snapshot,
                validation=validation,
                records=records,
                source_documents={document_id: self.source_path},
                transcription_root=self.root,
            )

    def make_multi_range_span(
        self,
        ranges: list[tuple[int, int]],
    ) -> dict[str, object]:
        span = self.make_span()
        span["span_id"] = ""
        span["segments"] = [
            {
                "ordinal": ordinal,
                "locator": {
                    "kind": "UTF8_BYTE_RANGE",
                    "start_byte": start,
                    "end_byte_exclusive": end,
                    "encoding": "UTF-8",
                },
                "literal_snapshot": _literal(self.raw[start:end]),
                "reviewed_transcription": None,
            }
            for ordinal, (start, end) in enumerate(ranges, start=1)
        ]
        return _seal(span)

    def test_exact_utf8_range_and_verbatim_claim_replay(self) -> None:
        result = self.replay()
        self.assertTrue(result.complete)
        self.assertEqual(result.verified_span_ids, (self.span["span_id"],))
        self.assertEqual(result.mechanically_grounded_claim_ids, ("claim-a",))
        self.assertEqual(result.details()["semantic_verdict"], None)

    def test_adjacent_utf8_ranges_compose_in_ordinal_order(self) -> None:
        boundary = self.start + len("α ".encode("utf-8"))
        span = self.make_multi_range_span(
            [(self.start, boundary), (boundary, self.end)]
        )

        result = self.replay(span=span)

        self.assertTrue(result.complete)
        self.assertEqual(result.verified_span_ids, (span["span_id"],))
        self.assertEqual(result.mechanically_grounded_claim_ids, ("claim-a",))

    def test_utf8_range_composition_rejects_reverse_overlap_and_duplicate(self) -> None:
        boundary = self.start + len("α ".encode("utf-8"))
        cases = {
            "reverse": [(boundary, self.end), (self.start, boundary)],
            "overlap": [(self.start, boundary + 1), (boundary, self.end)],
            "duplicate": [(self.start, boundary), (self.start, boundary)],
        }
        for name, ranges in cases.items():
            with self.subTest(name=name), self.assertRaisesRegex(
                RecordError,
                "strictly increasing and non-overlapping",
            ):
                self.replay(span=self.make_multi_range_span(ranges))

    def test_multi_region_pdf_span_cannot_pass_source_identity(self) -> None:
        span = self.make_span(locator_kind="PDF_REGION")
        span["span_id"] = ""
        second = dict(span["segments"][0])
        second["ordinal"] = 2
        span["segments"] = [span["segments"][0], second]
        span = _seal(span)

        with self.assertRaisesRegex(
            RecordError,
            "multi-region PDF source spans are unsupported",
        ):
            self.replay(span=span)

    def test_mixed_locator_span_is_rejected_for_its_single_document(self) -> None:
        span = self.make_multi_range_span([(self.start, self.end)])
        pdf_segment = {
            "ordinal": 2,
            "locator": {
                "kind": "PDF_REGION",
                "physical_page": 1,
                "page_index_zero_based": 0,
                "printed_label": None,
                "section_raw": None,
                "page_size_millipoints": [612000, 792000],
                "page_rotation_degrees": 0,
                "bbox_millipoints": [0, 0, 612000, 792000],
            },
            "literal_snapshot": _literal(self.selected),
            "reviewed_transcription": None,
        }
        span["span_id"] = ""
        span["segments"].append(pdf_segment)
        span = _seal(span)

        with self.assertRaisesRegex(RecordError, "one locator kind"):
            self.replay(span=span)

    def test_replay_requires_validation_for_the_same_snapshot(self) -> None:
        document_id = str(self.document["document_id"])
        span_id = str(self.span["span_id"])
        current = TranslationValidationResult(
            snapshot_id="snapshot-under-test",
            record_count=3,
            unresolved_record_ids=(),
        )
        with mock.patch(
            "creib.forge.source_replay.validate_translation_snapshot",
            return_value=current,
        ):
            with self.assertRaisesRegex(RecordError, "does not bind"):
                replay_translation_sources(
                    snapshot={
                        "snapshot_id": "snapshot-under-test",
                        "document_ids": [document_id],
                        "span_ids": [span_id],
                        "graph_id": "graph",
                    },
                    validation=TranslationValidationResult(
                        snapshot_id="another-snapshot",
                        record_count=3,
                        unresolved_record_ids=(),
                    ),
                    records={
                        document_id: self.document,
                        span_id: self.span,
                        "graph": {"obligations": []},
                    },
                    source_documents={document_id: self.source_path},
                    transcription_root=self.root,
                )

    def test_source_is_snapshotted_once_before_verification_and_extraction(self) -> None:
        original = Path.read_bytes
        source_reads = 0

        def changing_read(path: Path) -> bytes:
            nonlocal source_reads
            if path == self.source_path:
                source_reads += 1
                return self.raw if source_reads == 1 else b"changed-after-verification"
            return original(path)

        with mock.patch.object(Path, "read_bytes", changing_read):
            result = self.replay()
        self.assertTrue(result.complete)
        self.assertEqual(source_reads, 1)

    def test_range_that_splits_multibyte_character_is_invalid(self) -> None:
        split = self.start + 1
        selected = self.raw[split:self.end]
        span = self.make_span(
            start=split,
            literal=_literal(selected),
        )
        with self.assertRaisesRegex(SourceReplayMismatch, "invalid UTF-8 sequence"):
            self.replay(span=span)

    def test_item_count_and_digest_are_both_replayed(self) -> None:
        wrong_count = _literal(self.selected)
        wrong_count["item_count"] = int(wrong_count["item_count"]) + 1
        with self.assertRaisesRegex(SourceReplayMismatch, "item_count"):
            self.replay(span=self.make_span(literal=wrong_count))

        wrong_digest = _literal(self.selected)
        wrong_digest["sha256"] = "0" * 64
        with self.assertRaisesRegex(SourceReplayMismatch, "digest"):
            self.replay(span=self.make_span(literal=wrong_digest))

    def test_unknown_or_near_match_profile_stays_unresolved(self) -> None:
        literal = _literal(self.selected)
        literal["digest_domain"] = UTF8_RANGE_DIGEST_DOMAIN + ".lookalike"
        result = self.replay(span=self.make_span(literal=literal))
        self.assertFalse(result.complete)
        self.assertEqual(result.mechanically_grounded_claim_ids, ())
        self.assertEqual(result.unresolved_claim_ids, ("claim-a",))
        self.assertIn("digest_domain", result.limitations[0][1])

    def test_exact_replay_rejects_nonverbatim_source_claim(self) -> None:
        with self.assertRaisesRegex(SourceReplayMismatch, "not the exact"):
            self.replay(statement="A paraphrase of α exact claim")

    def test_reviewed_transcription_is_bound_and_zero_transform_exact(self) -> None:
        transcript = self.root / "reviewed.txt"
        transcript.write_bytes(self.selected)
        reviewed = {
            "path": "reviewed.txt",
            "sha256": bytes_digest(self.selected),
            "encoding": "UTF-8",
            "unicode_normalization": "NFC",
            "eol": "LF",
            "final_newline": False,
            "declared_transformations": [],
        }
        self.assertTrue(self.replay(span=self.make_span(reviewed=reviewed)).complete)

        transcript.write_bytes(b"changed")
        with self.assertRaisesRegex(SourceReplayMismatch, "transcription digest"):
            self.replay(span=self.make_span(reviewed=reviewed))

    def test_unexecutable_transformation_does_not_ground_claim(self) -> None:
        transcript = self.root / "reviewed.txt"
        transcript.write_bytes(self.selected)
        reviewed = {
            "path": "reviewed.txt",
            "sha256": bytes_digest(self.selected),
            "encoding": "UTF-8",
            "unicode_normalization": "NFC",
            "eol": "LF",
            "final_newline": False,
            "declared_transformations": ["editorial punctuation change"],
        }
        result = self.replay(span=self.make_span(reviewed=reviewed))
        self.assertFalse(result.complete)
        self.assertEqual(result.mechanically_grounded_claim_ids, ())

    def test_reviewed_path_cannot_escape_replay_root(self) -> None:
        reviewed = {
            "path": "../outside.txt",
            "sha256": "0" * 64,
            "encoding": "UTF-8",
            "unicode_normalization": "NFC",
            "eol": "LF",
            "final_newline": False,
            "declared_transformations": [],
        }
        with self.assertRaisesRegex(SourceReplayMismatch, "escapes"):
            self.replay(span=self.make_span(reviewed=reviewed))

    def test_pdf_profile_without_exact_supported_algorithm_stays_unresolved(self) -> None:
        pdf_raw = b"%PDF-not-a-real-pdf\n"
        self.source_path.write_bytes(pdf_raw)
        document = dict(self.document)
        document["document_id"] = ""
        document["artifact"] = {
            "supplied_filename": "authority.pdf",
            "media_type": "application/pdf",
            "sha256": bytes_digest(pdf_raw),
            "byte_length": len(pdf_raw),
        }
        document["structure"] = {"kind": "PDF", "page_count": 1, "encoding": None}
        document = _seal(document)
        literal = _literal(self.selected)
        literal["algorithm"] = PDF_WORD_ALGORITHM + ".undeclared-variant"
        span = self.make_span(locator_kind="PDF_REGION", literal=literal)
        span["document_id"] = document["document_id"]
        span["span_id"] = ""
        span = _seal(span)
        result = self.replay(span=span, document=document)
        self.assertFalse(result.complete)
        self.assertEqual(result.verified_span_ids, ())

    def test_exact_pdf_word_replay_uses_private_verified_copy_but_not_claim_text(self) -> None:
        pdf_raw = b"%PDF-private-replay-fixture\n"
        self.source_path.write_bytes(pdf_raw)
        document = dict(self.document)
        document["document_id"] = ""
        document["artifact"] = {
            "supplied_filename": "authority.pdf",
            "media_type": "application/pdf",
            "sha256": bytes_digest(pdf_raw),
            "byte_length": len(pdf_raw),
        }
        document["structure"] = {"kind": "PDF", "page_count": 1, "encoding": None}
        document = _seal(document)
        words = [["exact", 1000, 1000, 2000, 2000]]
        literal = {
            "algorithm": PDF_WORD_ALGORITHM,
            "tool": PDF_WORD_TOOL,
            "tool_version": "24.02.0",
            "selection_rule": PDF_WORD_SELECTION_RULE,
            "item_count": 1,
            "digest_domain": PDF_WORD_DIGEST_DOMAIN,
            "sha256": hashlib.sha256(
                PDF_WORD_DIGEST_DOMAIN.encode("ascii")
                + b"\0"
                + canonical_bytes(words)
            ).hexdigest(),
        }
        span = self.make_span(locator_kind="PDF_REGION", literal=literal)
        span["document_id"] = document["document_id"]
        span["span_id"] = ""
        span = _seal(span)

        private_paths: list[Path] = []

        def page_info(path: Path, _page: int):
            private_paths.append(path)
            self.assertNotEqual(path, self.source_path)
            self.assertEqual(path.read_bytes(), pdf_raw)
            return 1, [612000, 792000], 0

        def page_words(path: Path, _page: int, _size: list[int]):
            self.assertEqual(path, private_paths[0])
            return words

        version = subprocess.CompletedProcess(
            args=["pdftotext", "-v"],
            returncode=0,
            stdout=b"",
            stderr=b"pdftotext version 24.02.0\n",
        )
        with (
            mock.patch("creib.forge.source_replay._run", return_value=version),
            mock.patch(
                "creib.forge.source_replay._pdf_page_info", side_effect=page_info
            ),
            mock.patch("creib.forge.source_replay._pdf_words", side_effect=page_words),
        ):
            result = self.replay(span=span, document=document)
        self.assertFalse(result.complete)
        self.assertEqual(result.mechanically_grounded_claim_ids, ())
        self.assertIn("character-and-whitespace", result.limitations[0][1])
        self.assertEqual(len(private_paths), 1)

    def test_pdf_bbox_parser_emits_exactly_four_coordinates_per_word(self) -> None:
        xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<doc><page width="612" height="792">
<word xMin="1" yMin="2" xMax="3" yMax="4">exact</word>
</page></doc>"""
        completed = subprocess.CompletedProcess(
            args=["pdftotext"], returncode=0, stdout=xml, stderr=b""
        )
        with mock.patch("creib.forge.source_replay._run", return_value=completed):
            words = source_replay._pdf_words(
                Path("unused.pdf"), 1, [612000, 792000]
            )
        self.assertEqual(words, [["exact", 1000, 2000, 3000, 4000]])


if __name__ == "__main__":
    unittest.main()
