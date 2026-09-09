"""The offline schema catalog: fail-closed loading, no network, byte-keyed cache."""

from __future__ import annotations

from pathlib import Path
import shutil
import tempfile
import unittest

from creib.errors import RecordError
from creib.forge.schema_validation import (
    DEFAULT_SCHEMA_DIR,
    clear_schema_catalog_cache,
    load_local_schema_catalog,
)


class SchemaCatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        clear_schema_catalog_cache()

    def tearDown(self) -> None:
        clear_schema_catalog_cache()

    def test_conformance_schemas_load_and_validate(self) -> None:
        catalog = load_local_schema_catalog(DEFAULT_SCHEMA_DIR)
        self.assertEqual(
            catalog.schema_names,
            (
                "conformance-appraisal.schema.json",
                "conformance-claims.schema.json",
                "conformance-corpus.schema.json",
                "conformance-observation.schema.json",
                "conformance-observation.v2.schema.json",
                "conformance-pilot-config.schema.json",
                "conformance-run.schema.json",
                "conformance-run.v2.schema.json",
            ),
        )
        with self.assertRaises(RecordError):
            catalog.validate({"schema_version": "x"}, "conformance-pilot-config.schema.json")
        with self.assertRaises(RecordError):
            catalog.validate({}, "not-a-schema.json")

    def test_identical_bytes_return_the_same_checked_catalog(self) -> None:
        first = load_local_schema_catalog(DEFAULT_SCHEMA_DIR)
        self.assertIs(first, load_local_schema_catalog(DEFAULT_SCHEMA_DIR))
        # The public snapshot contract: every call is disposable and mutation-proof.
        self.assertIsNot(first.schemas, first.schemas)
        snapshot = first.schemas["conformance-pilot-config.schema.json"]
        snapshot["required"] = []
        with self.assertRaises(RecordError):
            first.validate({"schema_version": "x"}, "conformance-pilot-config.schema.json")

    def test_changed_schema_bytes_miss_the_cache_and_are_rechecked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            schema_dir = Path(temporary) / "schema"
            shutil.copytree(DEFAULT_SCHEMA_DIR, schema_dir)
            target = schema_dir / "conformance-run.schema.json"
            original = target.read_bytes()
            before = load_local_schema_catalog(schema_dir)
            self.assertIn(b'"const": "UNRESOLVED"', original)

            # A byte change that keeps the schema valid must produce a new catalog.
            target.write_bytes(original.replace(b'"const": "UNRESOLVED"', b'"const": "UNRESOLVED_X"', 1))
            after = load_local_schema_catalog(schema_dir)
            self.assertIsNot(before, after)

            # A byte change that makes the schema invalid must fail closed on the
            # next load even though a valid catalog for the same directory was
            # loaded a moment ago.
            target.write_bytes(original.replace(b'"type": "object"', b'"type": 5', 1))
            with self.assertRaises(RecordError):
                load_local_schema_catalog(schema_dir)

            # Restoring the original bytes returns to the original checked view.
            target.write_bytes(original)
            self.assertIs(load_local_schema_catalog(schema_dir), before)

    def test_unresolvable_reference_and_network_retrieval_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            schema_dir = Path(temporary)
            (schema_dir / "a.schema.json").write_text(
                '{"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "https://example.invalid/a.schema.json", '
                '"type": "object", "properties": {"x": {"$ref": "https://example.invalid/missing.schema.json"}}}'
            )
            with self.assertRaises(RecordError):
                load_local_schema_catalog(schema_dir)
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(RecordError):
                load_local_schema_catalog(Path(temporary))


if __name__ == "__main__":
    unittest.main()
