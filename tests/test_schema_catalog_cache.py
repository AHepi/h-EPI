"""The catalog cache wraps the pinned loader and is keyed by schema bytes only."""

from __future__ import annotations

from pathlib import Path
import shutil
import tempfile
import unittest

from creib.errors import RecordError
from creib.forge.schema_catalog_cache import (
    cached_local_schema_catalog,
    clear_schema_catalog_cache,
)
from creib.forge.schema_validation import DEFAULT_SCHEMA_DIR, load_local_schema_catalog


class SchemaCatalogCacheTests(unittest.TestCase):
    def setUp(self) -> None:
        clear_schema_catalog_cache()

    def tearDown(self) -> None:
        clear_schema_catalog_cache()

    def test_identical_bytes_return_the_same_checked_catalog(self) -> None:
        first = cached_local_schema_catalog(DEFAULT_SCHEMA_DIR)
        second = cached_local_schema_catalog(DEFAULT_SCHEMA_DIR)
        self.assertIs(first, second)
        # The pinned loader is untouched and still rebuilds on every call.
        self.assertIsNot(
            load_local_schema_catalog(DEFAULT_SCHEMA_DIR),
            load_local_schema_catalog(DEFAULT_SCHEMA_DIR),
        )
        self.assertEqual(
            first.schema_names, load_local_schema_catalog(DEFAULT_SCHEMA_DIR).schema_names
        )
        # The public snapshot contract is unchanged: every call is disposable.
        self.assertIsNot(first.schemas, first.schemas)

    def test_snapshot_mutation_cannot_alter_validation(self) -> None:
        catalog = cached_local_schema_catalog(DEFAULT_SCHEMA_DIR)
        snapshot = catalog.schemas["challenge.schema.json"]
        snapshot["required"] = []
        with self.assertRaises(RecordError):
            catalog.validate({"schema_version": "x"}, "challenge.schema.json")

    def test_changed_schema_bytes_miss_the_cache_and_are_rechecked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            schema_dir = Path(temporary) / "schema"
            shutil.copytree(DEFAULT_SCHEMA_DIR, schema_dir)
            target = schema_dir / "challenge.schema.json"
            before = cached_local_schema_catalog(schema_dir)
            original = target.read_bytes()

            # A byte change that keeps the schema valid must produce a new
            # catalog whose content reflects the change.
            changed = original.replace(
                b'"title": "SMF-0.1 runtime-compatible minimal pair"',
                b'"title": "SMF-0.1 runtime-compatible minimal pair (edited)"',
            )
            self.assertNotEqual(changed, original)
            target.write_bytes(changed)
            after = cached_local_schema_catalog(schema_dir)
            self.assertIsNot(before, after)
            self.assertEqual(
                after.schemas["challenge.schema.json"]["title"],
                "SMF-0.1 runtime-compatible minimal pair (edited)",
            )
            self.assertEqual(
                before.schemas["challenge.schema.json"]["title"],
                "SMF-0.1 runtime-compatible minimal pair",
            )

            # A byte change that makes the schema invalid must fail closed on
            # the next load even though a valid catalog for the same directory
            # was loaded a moment ago.
            target.write_bytes(original.replace(b'"type": "object"', b'"type": 5', 1))
            with self.assertRaises(RecordError):
                cached_local_schema_catalog(schema_dir)

            # Restoring the original bytes returns to the original checked view.
            target.write_bytes(original)
            restored = cached_local_schema_catalog(schema_dir)
            self.assertIs(restored, before)

    def test_unreadable_schema_directory_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(RecordError):
                cached_local_schema_catalog(Path(temporary))


if __name__ == "__main__":
    unittest.main()
