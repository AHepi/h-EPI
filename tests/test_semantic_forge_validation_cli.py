from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from creib.forge.calibration import (
    build_calibration_report,
    load_calibration_corpus,
)
from creib.strict_json import load_strict


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "validate_semantic_forge.py"
CORPUS = ROOT / "forge" / "corpus" / "cr-1.0-seed.json"
RESEARCH_LEDGER = ROOT / "forge" / "research" / "SMF-RESEARCH-2026-09-03.json"


def _authority_binding(corpus) -> dict[str, object]:
    return {
        "status": "MECHANICALLY_VALID",
        "document_id": corpus.authority.document_id,
        "sha256": corpus.authority.sha256,
        "byte_length": corpus.authority.byte_length,
        "physical_pdf_pages": corpus.authority.physical_pdf_pages,
        "semantic_authority": "EXTERNAL_CR_1_0_PDF_ONLY",
        "verification_scope": (
            "PDF identity, byte length, page structure, and pinned source anchors; "
            "not a semantic verdict"
        ),
    }


def _run(*arguments: str) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(ROOT / "src")
    result = subprocess.run(
        [sys.executable, str(TOOL), *arguments],
        cwd=ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    return result, json.loads(result.stdout)


class SemanticForgeValidationCLITests(unittest.TestCase):
    def test_default_corpus_reports_schema_and_runtime_coverage(self) -> None:
        result, report = _run()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["validation_status"], "SCHEMA_AND_RUNTIME_VALID")
        self.assertIs(report["runtime_contract_checked"], True)
        self.assertIsNone(report["semantic_verdict"])

    def test_canonical_filenames_with_custom_ids_are_schema_only(self) -> None:
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "https://example.test/custom.schema.json",
            "type": "object",
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            instance_path = root / "instance.json"
            instance_path.write_text("{}\n", encoding="utf-8")
            for schema_name in (
                "challenge.schema.json",
                "corpus.schema.json",
                "research-issue.schema.json",
                "research-ledger.schema.json",
            ):
                with self.subTest(schema_name=schema_name):
                    schema_dir = root / schema_name.removesuffix(".schema.json")
                    schema_dir.mkdir()
                    (schema_dir / schema_name).write_text(
                        json.dumps(schema, sort_keys=True, separators=(",", ":"))
                        + "\n",
                        encoding="utf-8",
                    )
                    result, report = _run(
                        "--schema-dir",
                        str(schema_dir),
                        "--instance",
                        str(instance_path),
                        "--schema",
                        schema_name,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(report["validation_status"], "SCHEMA_VALID_ONLY")
                    self.assertIs(report["runtime_contract_checked"], False)
                    self.assertEqual(report["runtime_contract_scope"], "NONE")

    def test_research_hash_tamper_is_not_labeled_valid(self) -> None:
        changed = load_strict(RESEARCH_LEDGER)
        changed["entries"][0]["bounded_source_report"] += " Altered."
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "research.json"
            path.write_text(
                json.dumps(changed, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                + "\n",
                encoding="utf-8",
            )
            result, report = _run(
                "--instance",
                str(path),
                "--schema",
                "research-ledger.schema.json",
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(report["validation_status"], "INVALID")
        self.assertIn("report_sha256 mismatch", report["error"])

    def test_calibration_meaning_tamper_is_not_schema_only_success(self) -> None:
        corpus = load_calibration_corpus(CORPUS)
        report = build_calibration_report(
            corpus,
            _authority_binding(corpus),
            repo_root=ROOT,
        )
        changed = copy.deepcopy(report)
        changed["human_review"]["question"] = "MACHINE CONFIRMED TARGET SEMANTICS"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "run.json"
            path.write_text(
                json.dumps(changed, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                + "\n",
                encoding="utf-8",
            )
            result, outcome = _run(
                "--instance",
                str(path),
                "--schema",
                "calibration-run.schema.json",
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(outcome["validation_status"], "INVALID")
        self.assertIn("exact deterministic regeneration", outcome["error"])


if __name__ == "__main__":
    unittest.main()
