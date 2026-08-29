from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from creib.errors import RecordError
from creib.models import validate_manifest
from creib.strict_json import load_strict, loads_strict


class StrictJSONTests(unittest.TestCase):
    def test_excessive_nesting_is_a_typed_record_error(self) -> None:
        deeply_nested = "[" * 2_000 + "0" + "]" * 2_000
        with self.assertRaisesRegex(RecordError, "nesting exceeds"):
            loads_strict(deeply_nested)

    def test_json_read_failure_is_a_typed_record_error(self) -> None:
        with patch.object(Path, "read_bytes", side_effect=OSError("unavailable")):
            with self.assertRaisesRegex(RecordError, "cannot read"):
                load_strict(Path("unavailable.json"))

    def test_duplicate_key_is_rejected(self) -> None:
        with self.assertRaises(RecordError):
            loads_strict('{"x": 1, "x": 2}')

    def test_non_finite_numbers_are_rejected(self) -> None:
        for token in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(token=token), self.assertRaises(RecordError):
                loads_strict('{"x": ' + token + "}")

    def test_floats_are_rejected(self) -> None:
        with self.assertRaises(RecordError):
            loads_strict('{"coordinate": 1.0}')

    def test_lone_unicode_surrogate_is_rejected(self) -> None:
        with self.assertRaises(RecordError):
            loads_strict('{"text": "\\ud800"}')

    def test_boolean_does_not_coerce_to_integer(self) -> None:
        manifest = loads_strict(
            """{
              "schema_version":"cr-eib.source-manifest.v1",
              "document_id":"CR-1.0",
              "semantic_authority":true,
              "supplied_filename":"authority.pdf",
              "sha256":"0000000000000000000000000000000000000000000000000000000000000000",
              "byte_length":true,
              "page_count":1,
              "page_size_millipoints":[1,1],
              "active_span":{"physical_pdf_pages":[1,1],"printed_folios":[1,1]},
              "authority_file_committed":false
            }"""
        )
        with self.assertRaises(RecordError):
            validate_manifest(manifest)


if __name__ == "__main__":
    unittest.main()
