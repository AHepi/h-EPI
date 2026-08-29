from __future__ import annotations

import copy
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from creib.strict_json import load_strict


ROOT = Path(__file__).resolve().parents[1]


class SchemaFileTests(unittest.TestCase):
    def test_versioned_schemas_are_strict_json_with_unique_ids(self) -> None:
        schemas = [load_strict(path) for path in sorted((ROOT / "bridge" / "schema").glob("*.json"))]
        self.assertEqual(len(schemas), 3)
        identifiers = [schema["$id"] for schema in schemas]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        for schema in schemas:
            self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
            self.assertFalse(schema["additionalProperties"])
            Draft202012Validator.check_schema(schema)

    def test_committed_instances_validate_against_published_schemas(self) -> None:
        manifest_schema = load_strict(ROOT / "bridge" / "schema" / "source-manifest.schema.json")
        anchor_schema = load_strict(ROOT / "bridge" / "schema" / "source-anchor.schema.json")
        declaration_schema = load_strict(ROOT / "bridge" / "schema" / "declaration.schema.json")
        Draft202012Validator(manifest_schema).validate(
            load_strict(ROOT / "authority" / "source_manifest.json")
        )
        anchor_set = load_strict(ROOT / "authority" / "source_anchors.json")
        anchor_validator = Draft202012Validator(anchor_schema)
        for anchor in anchor_set["anchors"]:
            anchor_validator.validate(anchor)
        declaration_validator = Draft202012Validator(declaration_schema)
        for path in sorted((ROOT / "bridge" / "declarations").glob("*.json")):
            declaration_validator.validate(load_strict(path))

    def test_short_coordinate_arrays_are_schema_invalid(self) -> None:
        manifest_schema = load_strict(ROOT / "bridge" / "schema" / "source-manifest.schema.json")
        manifest = copy.deepcopy(load_strict(ROOT / "authority" / "source_manifest.json"))
        manifest["page_size_millipoints"] = []
        with self.assertRaises(ValidationError):
            Draft202012Validator(manifest_schema).validate(manifest)

        anchor_schema = load_strict(ROOT / "bridge" / "schema" / "source-anchor.schema.json")
        anchor = copy.deepcopy(load_strict(ROOT / "authority" / "source_anchors.json")["anchors"][0])
        anchor["payload"]["locator"]["tight_bbox_millipoints"] = []
        with self.assertRaises(ValidationError):
            Draft202012Validator(anchor_schema).validate(anchor)


if __name__ == "__main__":
    unittest.main()
