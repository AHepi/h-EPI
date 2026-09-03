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
from creib.forge.inquiry import (
    build_adaptive_inquiry_plan,
    compute_human_triage_id,
    compute_locus_assessment_id,
)
from creib.strict_json import load_strict


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "validate_semantic_forge.py"
CORPUS = ROOT / "forge" / "corpus" / "cr-1.0-seed.json"
RESEARCH_LEDGER = ROOT / "forge" / "research" / "SMF-RESEARCH-2026-09-03.json"
RUN_RECORD = (
    ROOT
    / "forge"
    / "runs"
    / "SMF-CALIBRATION-CR-1-0-001.4219efce.json"
)
LEGACY_PLAN = (
    ROOT
    / "forge"
    / "history"
    / "invalidated-plans"
    / "SMF-AIP-2d589a64.no-triage.json"
)


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


def _v2_no_triage_plan() -> dict[str, object]:
    with tempfile.TemporaryDirectory() as directory:
        return build_adaptive_inquiry_plan(
            repo_root=ROOT,
            run_record_path=RUN_RECORD,
            research_ledger_path=RESEARCH_LEDGER,
            triage_dir=Path(directory),
        )


def _v2_genesis_triage() -> dict[str, object]:
    bindings = _v2_no_triage_plan()["bindings"]
    assessment: dict[str, object] = {
        "assessment_id": "LA:" + "0" * 64,
        "status": "LIVE",
        "loci": ["TEST"],
        "mechanism": "The finite contrast may not test the declared distinction.",
        "relevance": "A better contrast could change the next work item.",
        "discriminator": "Construct and review one exact same-reduct contrast.",
        "scope": "The bound weak typed-role calibration only.",
        "uncertainty_location": "INTERNAL_HARNESS_SPECIFICATION",
        "depends_on_assessment_ids": [],
        "epistemic_effect": "CRITICISM_ONLY",
        "can_establish_unique_cause": False,
    }
    assessment["assessment_id"] = compute_locus_assessment_id(assessment)
    triage: dict[str, object] = {
        "$schema": "../schema/adaptive-inquiry-v2.schema.json",
        "schema_version": "creib.semantic-forge.human-failure-triage.v2",
        "record_type": "human_failure_triage",
        "triage_id": "HT:" + "0" * 64,
        "sequence": 1,
        "previous_triage_id": None,
        "transition_kind": "GENESIS",
        "transition_reason": "Begin one explicit criticism lineage.",
        "created_on": "2026-09-03",
        "bindings": bindings,
        "overall_status": "UNRESOLVED",
        "locus_assessments": [assessment],
        "assessment_dispositions": [],
        "next_action": None,
        "reviewer_kind": "HUMAN",
        "machine_generated": False,
        "epistemic_effect": "WORKFLOW_ROUTING_ONLY",
        "can_promote_model": False,
        "semantic_verdict": None,
    }
    triage["triage_id"] = compute_human_triage_id(triage)
    return triage


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

    def test_adaptive_filename_lookalikes_do_not_trigger_runtime(self) -> None:
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "https://example.test/custom-adaptive.schema.json",
            "type": "object",
        }
        instance = {"record_type": "adaptive_inquiry_plan"}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            instance_path = root / "instance.json"
            instance_path.write_text(
                json.dumps(instance, sort_keys=True, separators=(",", ":")) + "\n",
                encoding="utf-8",
            )
            for schema_name in (
                "adaptive-inquiry.schema.json",
                "adaptive-inquiry-v2.schema.json",
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

    def test_historical_v1_adaptive_plan_retains_intrinsic_runtime_validation(self) -> None:
        result, report = _run(
            "--instance",
            str(LEGACY_PLAN),
            "--schema",
            "adaptive-inquiry.schema.json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            report["validation_status"],
            "SCHEMA_AND_INTRINSIC_RUNTIME_VALID",
        )
        self.assertIs(report["runtime_contract_checked"], True)
        self.assertEqual(report["runtime_contract_scope"], "INTRINSIC_RECORD_ONLY")

    def test_v2_adaptive_plan_gets_intrinsic_runtime_validation(self) -> None:
        plan = _v2_no_triage_plan()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plan.json"
            path.write_text(
                json.dumps(plan, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                + "\n",
                encoding="utf-8",
            )
            result, report = _run(
                "--instance",
                str(path),
                "--schema",
                "adaptive-inquiry-v2.schema.json",
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            report["validation_status"],
            "SCHEMA_AND_INTRINSIC_RUNTIME_VALID",
        )
        self.assertIs(report["runtime_contract_checked"], True)
        self.assertEqual(report["runtime_contract_scope"], "INTRINSIC_RECORD_ONLY")

    def test_v2_adaptive_plan_hash_tamper_is_not_schema_only_success(self) -> None:
        plan = _v2_no_triage_plan()
        plan["plan_id"] = "AIP:" + "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plan.json"
            path.write_text(
                json.dumps(plan, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                + "\n",
                encoding="utf-8",
            )
            result, report = _run(
                "--instance",
                str(path),
                "--schema",
                "adaptive-inquiry-v2.schema.json",
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(report["validation_status"], "INVALID")
        self.assertIn("content-addressed ID mismatch", report["error"])

    def test_v2_triage_gets_intrinsic_runtime_validation(self) -> None:
        triage = _v2_genesis_triage()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "triage.json"
            path.write_text(
                json.dumps(
                    triage,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n",
                encoding="utf-8",
            )
            result, report = _run(
                "--instance",
                str(path),
                "--schema",
                "adaptive-inquiry-v2.schema.json",
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            report["validation_status"],
            "SCHEMA_AND_INTRINSIC_RUNTIME_VALID",
        )
        self.assertEqual(report["runtime_contract_scope"], "INTRINSIC_RECORD_ONLY")

    def test_v2_triage_nested_hash_tamper_is_not_schema_only_success(self) -> None:
        triage = _v2_genesis_triage()
        triage["locus_assessments"][0]["assessment_id"] = "LA:" + "f" * 64
        triage["triage_id"] = compute_human_triage_id(triage)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "triage.json"
            path.write_text(
                json.dumps(
                    triage,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n",
                encoding="utf-8",
            )
            result, report = _run(
                "--instance",
                str(path),
                "--schema",
                "adaptive-inquiry-v2.schema.json",
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(report["validation_status"], "INVALID")
        self.assertIn("locus assessment content-addressed ID mismatch", report["error"])

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
