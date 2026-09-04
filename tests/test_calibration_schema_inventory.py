from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "forge" / "schema"
CALIBRATION_SCHEMA = SCHEMA_DIR / "calibration-run.schema.json"


class CalibrationSchemaInventoryTests(unittest.TestCase):
    def test_execution_contract_covers_exact_schema_inventory(self) -> None:
        schema = json.loads(CALIBRATION_SCHEMA.read_text(encoding="utf-8"))
        digest_map = schema["$defs"]["execution_contract"]["properties"][
            "implementation_file_sha256"
        ]

        inventory = {
            path.relative_to(ROOT).as_posix()
            for path in SCHEMA_DIR.glob("*.schema.json")
        }
        required_schema_paths = {
            path for path in digest_map["required"] if path.startswith("forge/schema/")
        }
        declared_schema_paths = {
            path
            for path in digest_map["properties"]
            if path.startswith("forge/schema/")
        }

        self.assertEqual(required_schema_paths, inventory)
        self.assertEqual(declared_schema_paths, inventory)
        self.assertEqual(required_schema_paths, declared_schema_paths)
        self.assertIs(digest_map["additionalProperties"], False)


if __name__ == "__main__":
    unittest.main()
