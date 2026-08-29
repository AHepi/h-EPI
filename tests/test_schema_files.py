from __future__ import annotations

import copy
import hashlib
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from creib.canonical import canonical_bytes
from creib.strict_json import load_strict
from creib.verify import EXPECTED_SCHEMA_CANONICAL_SHA256


ROOT = Path(__file__).resolve().parents[1]


class SchemaFileTests(unittest.TestCase):
    def test_runtime_schema_identities_are_canonically_pinned(self) -> None:
        expected_paths = {
            "bridge/schema/source-anchor.schema.json",
            "bridge/schema/source-manifest.schema.json",
            "bridge/schema/declaration.schema.json",
            "bridge/schema/declaration-v2.schema.json",
            "bridge/schema/interpretation-choice-registry.schema.json",
        }
        self.assertEqual(set(EXPECTED_SCHEMA_CANONICAL_SHA256), expected_paths)
        for relative, expected_digest in EXPECTED_SCHEMA_CANONICAL_SHA256.items():
            schema = load_strict(ROOT / relative)
            actual_digest = hashlib.sha256(canonical_bytes(schema)).hexdigest()
            self.assertEqual(actual_digest, expected_digest)

    def test_versioned_schemas_are_strict_json_with_unique_ids(self) -> None:
        schemas = [load_strict(path) for path in sorted((ROOT / "bridge" / "schema").glob("*.json"))]
        self.assertEqual(len(schemas), 5)
        identifiers = [schema["$id"] for schema in schemas]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        for schema in schemas:
            self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
            self.assertFalse(schema["additionalProperties"])
            Draft202012Validator.check_schema(schema)

    def test_committed_instances_validate_against_published_schemas(self) -> None:
        manifest_schema = load_strict(ROOT / "bridge" / "schema" / "source-manifest.schema.json")
        anchor_schema = load_strict(ROOT / "bridge" / "schema" / "source-anchor.schema.json")
        declaration_schemas = {
            "cr-eib.bridge-declaration.v1": load_strict(
                ROOT / "bridge" / "schema" / "declaration.schema.json"
            ),
            "cr-eib.bridge-declaration.v2": load_strict(
                ROOT / "bridge" / "schema" / "declaration-v2.schema.json"
            ),
        }
        choice_schema = load_strict(
            ROOT / "bridge" / "schema" / "interpretation-choice-registry.schema.json"
        )
        Draft202012Validator(manifest_schema).validate(
            load_strict(ROOT / "authority" / "source_manifest.json")
        )
        anchor_set = load_strict(ROOT / "authority" / "source_anchors.json")
        anchor_validator = Draft202012Validator(anchor_schema)
        for anchor in anchor_set["anchors"]:
            anchor_validator.validate(anchor)
        Draft202012Validator(choice_schema).validate(
            load_strict(ROOT / "bridge" / "choices" / "interpretation-choices.json")
        )
        for path in sorted((ROOT / "bridge" / "declarations").glob("*.json")):
            declaration = load_strict(path)
            Draft202012Validator(declaration_schemas[declaration["schema_version"]]).validate(
                declaration
            )

    def test_declaration_versions_are_not_interchangeable(self) -> None:
        v1_schema = load_strict(ROOT / "bridge" / "schema" / "declaration.schema.json")
        v2_schema = load_strict(ROOT / "bridge" / "schema" / "declaration-v2.schema.json")
        v1 = load_strict(ROOT / "bridge" / "declarations" / "EIB-TH3A-PILOT.json")
        v2 = load_strict(
            ROOT / "bridge" / "declarations" / "EIB-DF10-REFINED-CANDIDATE.json"
        )
        with self.assertRaises(ValidationError):
            Draft202012Validator(v1_schema).validate(v2)
        with self.assertRaises(ValidationError):
            Draft202012Validator(v2_schema).validate(v1)

    def test_v2_verified_obligation_requires_a_strict_artifact(self) -> None:
        schema = load_strict(ROOT / "bridge" / "schema" / "declaration-v2.schema.json")
        declaration = copy.deepcopy(
            load_strict(
                ROOT / "bridge" / "declarations" / "EIB-DF10-REFINED-CANDIDATE.json"
            )
        )
        declaration["proof_obligations"][0]["artifact"] = None
        with self.assertRaises(ValidationError):
            Draft202012Validator(schema).validate(declaration)

    def test_choice_registry_rejects_implicit_authority(self) -> None:
        schema = load_strict(
            ROOT / "bridge" / "schema" / "interpretation-choice-registry.schema.json"
        )
        registry = copy.deepcopy(
            load_strict(ROOT / "bridge" / "choices" / "interpretation-choices.json")
        )
        registry["choices"][0]["authority_status"] = "source-fact"
        with self.assertRaises(ValidationError):
            Draft202012Validator(schema).validate(registry)

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
