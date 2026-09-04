from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from creib.canonical import canonical_bytes, domain_digest
from creib.errors import RecordError
from creib.forge.qualification import (
    ALL_REPRODUCED,
    REPORT_FROZEN,
    SNAPSHOT_FROZEN,
    compute_freeze_id,
)
from creib.forge.source_replay import SourceReplayResult
from creib.forge.translation import (
    TranslationValidationResult,
    translation_record_digest,
)
from creib.forge.translation_pipeline import (
    BLOCKED,
    INVALID,
    NOT_SUPPLIED,
    READY,
    STAGE_ORDER,
    STRUCTURALLY_VALID,
    UNRESOLVED,
    run_translation_pipeline,
)
from creib.forge.translation_review import REVIEW_SCHEMA


ROOT = Path(__file__).resolve().parents[1]


class TranslationPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.records_dir = self.root / "records"
        self.records_dir.mkdir()
        self.snapshot_path = self.root / "snapshot.json"
        self.snapshot = {
            "schema_version": "creib.semantic-forge.translation-snapshot.v1",
            "snapshot_id": "snapshot",
            "predecessor_snapshot_id": None,
            "document_ids": ["document"],
            "span_ids": ["span"],
            "charter_id": "charter",
            "graph_id": "graph",
            "interpretation_set_ids": ["interpretations"],
            "signature_id": "signature",
            "model_id": "model",
            "import_ids": ["import"],
            "bridge_id": "bridge",
            "unresolved_record_ids": [],
            "record_closure_sha256": "sha256:" + "9" * 64,
        }
        self.write_snapshot()
        self.records = {
            "document": {"record": "document"},
            "span": {"record": "span"},
            "charter": {
                "record": "charter",
                "purpose": "Exercise one bounded translation.",
                "system_boundary": "The exact pipeline fixture.",
                "in_scope": ["The selected fixture."],
            },
            "graph": {
                "obligations": [
                    {
                        "obligation_id": "obligation",
                        "source_claim": {"claim_id": "claim"},
                        "translation_duty": {
                            "duty_id": "duty",
                            "protected_features": [{"feature_id": "feature"}],
                        },
                    }
                ],
                "edges": [],
            },
            "interpretations": {
                "branches": [
                    {"interpretation_id": "rival-a"},
                    {"interpretation_id": "rival-b"},
                ]
            },
            "signature": {
                "schema_version": (
                    "creib.semantic-forge.translation-neutral-signature.v1"
                ),
                "members": [],
            },
            "model": {
                "schema_version": "creib.semantic-forge.translation-neutral-model.v1",
                "interpretation_ids": ["rival-a", "rival-b"],
                "clauses": [],
                "open_ports": [],
                "theory_projection": {
                    "theory_record_sha256": "sha256:" + "7" * 64,
                    "execution_semantics": "DECLARED_EXECUTION_SEMANTICS",
                },
                "semantic_dependency_closure": {
                    "closure_sha256": "sha256:" + "8" * 64,
                },
            },
            "import": {"record": "import"},
            "bridge": {
                "forward_mappings": [],
                "reverse_mappings": [],
                "translation_deltas": [],
            },
        }
        self.validation = TranslationValidationResult("snapshot", 10, ())

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_snapshot(self) -> None:
        self.snapshot_path.write_text(json.dumps(self.snapshot), encoding="utf-8")

    def snapshot_binding(self) -> dict[str, str]:
        return {
            "role": "TRANSLATION_SNAPSHOT",
            "subject_id": self.snapshot["snapshot_id"],
            "binding_kind": "CANONICAL_RECORD",
            "sha256": translation_record_digest(self.snapshot).removeprefix(
                "sha256:"
            ),
        }

    def inquiry_plan(
        self,
        *,
        plan_id: str,
        route: str,
        assessment_id: str,
        action_id: str,
        research_target: dict[str, str] | None,
    ) -> dict[str, object]:
        uncertainty_locations = {
            "INTERNAL_HARNESS_WORK": "INTERNAL_HARNESS_SPECIFICATION",
            "INTERNAL_MODEL_WORK": "INTERNAL_DEDUCTION_OR_MODEL_FINDING",
            "AUTHORITY_REVIEW": "CR_AUTHORITY_INTERPRETATION",
            "EXTERNAL_RESEARCH_REQUIRED": "EXTERNAL_CRITICAL_INSTRUMENT",
        }
        return {
            "plan_id": plan_id,
            "route": route,
            "case_binding": {"component_bindings": [self.snapshot_binding()]},
            "locus_assessments": [
                {
                    "assessment_id": assessment_id,
                    "uncertainty_location": uncertainty_locations[route],
                    "depends_on_assessment_ids": [],
                }
            ],
            "live_locus_assessment_ids": [assessment_id],
            "selected_action_id": action_id,
            "next_action": {
                "selected_assessment_ids": [assessment_id],
                "research_target": research_target,
            },
        }

    def ready_review_state(self) -> SimpleNamespace:
        return SimpleNamespace(
            workflow_status="SCOPED_USE_AUTHORIZED",
            head_review_id="review-head",
            reviews=({"review_id": "review-head"},),
            current_decision_id="decision",
            effective_branch_states={
                "interpretations/rival-a": "LIVE_FOR_SCOPE",
                "interpretations/rival-b": "LIVE_FOR_SCOPE",
            },
            reviewer_authentication="EXTERNALLY_VERIFIED_TEST_FIXTURE",
            current_scope_binding={
                "scope_id": "scope",
                "charter_id": "charter",
                "purpose": "Exercise one bounded translation.",
                "system_boundary": "The exact pipeline fixture.",
                "in_scope": ["The selected fixture."],
            },
            authorized_variants=(
                {
                    "model_id": "model",
                    "selections": [
                        {
                            "interpretation_set_id": "interpretations",
                            "interpretation_id": "rival-a",
                        },
                        {
                            "interpretation_set_id": "interpretations",
                            "interpretation_id": "rival-b",
                        },
                    ],
                },
            ),
        )

    def run_pipeline(self, **kwargs):
        with (
            mock.patch(
                "creib.forge.translation_pipeline.load_translation_inventory",
                return_value=self.records,
            ),
            mock.patch(
                "creib.forge.translation_pipeline.validate_translation_snapshot",
                return_value=self.validation,
            ),
        ):
            return run_translation_pipeline(
                records_dir=self.records_dir,
                snapshot_path=self.snapshot_path,
                **kwargs,
            )

    def test_partial_run_keeps_every_omitted_or_open_stage_visible(self) -> None:
        report = self.run_pipeline()
        self.assertEqual(tuple(report["stages"]), STAGE_ORDER)
        self.assertEqual(
            report["stages"]["translation_integrity"]["status"],
            STRUCTURALLY_VALID,
        )
        self.assertEqual(report["stages"]["source_identity"]["status"], UNRESOLVED)
        self.assertEqual(report["stages"]["charter"]["status"], STRUCTURALLY_VALID)
        for stage in (
            "interpretation_review",
            "dynamic_test_synthesis",
            "research_routing_readiness",
            "hardening",
            "qualification",
        ):
            self.assertEqual(report["stages"][stage]["status"], NOT_SUPPLIED)
        self.assertEqual(
            report["stages"]["iteration_lineage"]["status"], UNRESOLVED
        )
        self.assertEqual(
            report["stages"]["iteration_lineage"]["details"]["closure_status"],
            "NOT_IMPLEMENTED_V1",
        )
        self.assertEqual(report["overall_status"], UNRESOLVED)
        self.assertTrue(report["next_actions"])
        self.assertIsNone(report["semantic_verdict"])
        self.assertEqual(report["mapping_fidelity"], "UNREVIEWED")
        for stage in report["stages"].values():
            self.assertIsNone(stage["semantic_verdict"])
            self.assertEqual(stage["mapping_fidelity"], "UNREVIEWED")

    def test_source_identity_requires_all_exact_byte_bindings(self) -> None:
        source = self.root / "authority.txt"
        source.write_text("authority\n", encoding="utf-8")
        exact_replay = SourceReplayResult(
            verified_document_ids=("document",),
            verified_span_ids=("span",),
            unresolved_span_ids=(),
            mechanically_grounded_claim_ids=("claim",),
            unresolved_claim_ids=(),
            limitations=(),
        )
        with mock.patch(
            "creib.forge.translation_pipeline.replay_translation_sources",
            return_value=exact_replay,
        ) as replay:
            report = self.run_pipeline(source_documents={"document": source})
        replay.assert_called_once()
        self.assertEqual(
            report["stages"]["source_identity"]["status"], STRUCTURALLY_VALID
        )
        self.assertEqual(
            report["stages"]["source_identity"]["details"][
                "mechanically_grounded_claim_ids"
            ],
            ["claim"],
        )

        partial_snapshot = dict(self.snapshot)
        partial_snapshot["document_ids"] = ["document", "document-two"]
        self.snapshot_path.write_text(json.dumps(partial_snapshot), encoding="utf-8")
        partial = self.run_pipeline(source_documents={"document": source})
        self.assertEqual(partial["stages"]["source_identity"]["status"], BLOCKED)
        self.assertEqual(
            partial["stages"]["source_identity"]["details"]["missing_document_ids"],
            ["document-two"],
        )

    def test_multiple_research_routes_remain_applicable_without_selection(self) -> None:
        external = self.root / "external-plan.json"
        internal = self.root / "internal-plan.json"
        external.write_text(
            json.dumps(
                self.inquiry_plan(
                    plan_id="external-plan",
                    route="EXTERNAL_RESEARCH_REQUIRED",
                    assessment_id="assessment-a",
                    action_id="action-a",
                    research_target={"issue_id": "issue-a"},
                )
            ),
            encoding="utf-8",
        )
        internal.write_text(
            json.dumps(
                self.inquiry_plan(
                    plan_id="internal-plan",
                    route="INTERNAL_HARNESS_WORK",
                    assessment_id="assessment-b",
                    action_id="action-b",
                    research_target=None,
                )
            ),
            encoding="utf-8",
        )
        with mock.patch(
            "creib.forge.translation_pipeline.validate_generic_inquiry_plan"
        ):
            report = self.run_pipeline(inquiry_plan_paths=(external, internal))
        stage = report["stages"]["research_routing_readiness"]
        self.assertEqual(stage["status"], UNRESOLVED)
        self.assertTrue(stage["details"]["preview_only"])
        self.assertFalse(stage["details"]["publication_authority"])
        self.assertEqual(
            report["applicable_routes"],
            [
                {
                    "plan_id": "external-plan",
                    "assessment_id": "assessment-a",
                    "route": "EXTERNAL_RESEARCH_REQUIRED",
                    "readiness": "SELECTED_FOR_ACTION",
                    "selected": True,
                },
                {
                    "plan_id": "internal-plan",
                    "assessment_id": "assessment-b",
                    "route": "INTERNAL_HARNESS_WORK",
                    "readiness": "SELECTED_FOR_ACTION",
                    "selected": True,
                },
            ],
        )
        self.assertEqual(
            [item["selected_action_route"] for item in stage["details"]["plans"]],
            ["EXTERNAL_RESEARCH_REQUIRED", "INTERNAL_HARNESS_WORK"],
        )
        self.assertIsNone(report["selected_route"])
        self.assertIn("NO_AUTOMATIC_RANKING", report["route_selection_policy"])

    def test_one_plan_reports_every_independent_assessment_route(self) -> None:
        plan_path = self.root / "mixed-plan.json"
        plan_path.write_text(
            json.dumps(
                {
                    "plan_id": "mixed-plan",
                    "route": "INTERNAL_MODEL_WORK",
                    "case_binding": {
                        "component_bindings": [self.snapshot_binding()]
                    },
                    "locus_assessments": [
                        {
                            "assessment_id": "assessment-a",
                            "uncertainty_location": (
                                "INTERNAL_DEDUCTION_OR_MODEL_FINDING"
                            ),
                            "depends_on_assessment_ids": [],
                        },
                        {
                            "assessment_id": "assessment-b",
                            "uncertainty_location": "CR_AUTHORITY_INTERPRETATION",
                            "depends_on_assessment_ids": [],
                        },
                    ],
                    "live_locus_assessment_ids": [
                        "assessment-a",
                        "assessment-b",
                    ],
                    "selected_action_id": "action-a",
                    "next_action": {
                        "selected_assessment_ids": ["assessment-a"],
                        "research_target": None,
                    },
                }
            ),
            encoding="utf-8",
        )
        with mock.patch(
            "creib.forge.translation_pipeline.validate_generic_inquiry_plan"
        ):
            report = self.run_pipeline(inquiry_plan_paths=(plan_path,))

        stage = report["stages"]["research_routing_readiness"]
        self.assertEqual(
            stage["details"]["plans"][0]["selected_action_route"],
            "INTERNAL_MODEL_WORK",
        )
        self.assertEqual(
            report["applicable_routes"],
            [
                {
                    "plan_id": "mixed-plan",
                    "assessment_id": "assessment-a",
                    "route": "INTERNAL_MODEL_WORK",
                    "readiness": "SELECTED_FOR_ACTION",
                    "selected": True,
                },
                {
                    "plan_id": "mixed-plan",
                    "assessment_id": "assessment-b",
                    "route": "AUTHORITY_REVIEW",
                    "readiness": "FRONTIER_UNSELECTED",
                    "selected": False,
                },
            ],
        )
        self.assertIsNone(report["selected_route"])

    def test_dynamic_synthesis_is_unresolved_until_semantic_bindings_exist(self) -> None:
        old_path = self.root / "old.json"
        delta_path = self.root / "delta.json"
        old_path.write_text(json.dumps({"snapshot_id": "old"}), encoding="utf-8")
        delta_path.write_text(json.dumps({"delta_id": "delta"}), encoding="utf-8")
        self.snapshot["predecessor_snapshot_id"] = "old"
        self.write_snapshot()
        synthesis = {
            "synthesis_id": "synthesis",
            "overall_status": "AWAITING_SEMANTIC_BINDINGS",
            "coverage": [
                {
                    "family": "NEGATION",
                    "coverage_status": "DEFERRED_MISSING_SEMANTIC_BINDINGS",
                    "missing_semantic_bindings": ["TYPED_EXPECTATION"],
                },
                {
                    "family": "ROUND_TRIP",
                    "coverage_status": "DEFERRED_MISSING_SEMANTIC_BINDINGS",
                    "missing_semantic_bindings": ["TYPED_COMPARATOR"],
                },
            ],
        }
        with (
            mock.patch(
                "creib.forge.translation_pipeline.synthesize_translation_tests",
                return_value=synthesis,
            ),
            mock.patch(
                "creib.forge.translation_pipeline.validate_translation_test_synthesis"
            ),
        ):
            report = self.run_pipeline(
                old_snapshot_path=old_path, delta_path=delta_path
            )
        stage = report["stages"]["dynamic_test_synthesis"]
        self.assertEqual(stage["status"], UNRESOLVED)
        self.assertFalse(stage["details"]["research_authorized"])
        self.assertEqual(len(stage["next_actions"]), 2)

        blocked = self.run_pipeline(old_snapshot_path=old_path)
        self.assertEqual(
            blocked["stages"]["dynamic_test_synthesis"]["status"], BLOCKED
        )

        self.snapshot["predecessor_snapshot_id"] = "different-old-snapshot"
        self.write_snapshot()
        mismatched = self.run_pipeline(
            old_snapshot_path=old_path, delta_path=delta_path
        )
        self.assertEqual(
            mismatched["stages"]["dynamic_test_synthesis"]["status"], INVALID
        )
        self.assertIn(
            "predecessor",
            mismatched["stages"]["dynamic_test_synthesis"]["error"]["error"],
        )

    def test_review_authorization_is_ready_but_never_a_fidelity_verdict(self) -> None:
        review_dir = self.root / "reviews"
        review_dir.mkdir()
        state = self.ready_review_state()
        with (
            mock.patch(
                "creib.forge.translation_pipeline.translation_review_bindings",
                return_value={"binding": "exact"},
            ),
            mock.patch(
                "creib.forge.translation_pipeline.translation_review_surface",
                return_value={"surface": "exact"},
            ),
            mock.patch(
                "creib.forge.translation_pipeline.verify_translation_review_chain",
                return_value=state,
            ),
        ):
            report = self.run_pipeline(
                review_dir=review_dir, review_head_id="review-head"
            )
        stage = report["stages"]["interpretation_review"]
        self.assertEqual(stage["status"], READY)
        self.assertIsNone(stage["semantic_verdict"])
        self.assertEqual(stage["mapping_fidelity"], "UNREVIEWED")

    def test_hardening_requires_current_review_and_current_artifacts(self) -> None:
        comparison_path = self.root / "comparison.json"
        review_dir = self.root / "reviews"
        review_dir.mkdir()
        review_state = self.ready_review_state()
        review_sha256 = domain_digest(
            f"{REVIEW_SCHEMA}.complete-record", review_state.reviews[-1]
        )
        comparison = {
            "comparison_id": "comparison",
            "execution_semantics": "DECLARED_EXECUTION_SEMANTICS",
            "successor": {
                "snapshot_ref": {
                    "record_id": self.snapshot["snapshot_id"],
                    "schema_version": self.snapshot["schema_version"],
                    "record_sha256": translation_record_digest(self.snapshot),
                },
                "model_ref": {
                    "record_id": self.snapshot["model_id"],
                    "schema_version": self.records["model"]["schema_version"],
                    "record_sha256": translation_record_digest(
                        self.records["model"]
                    ),
                },
                "signature_ref": {
                    "record_id": self.snapshot["signature_id"],
                    "schema_version": self.records["signature"]["schema_version"],
                    "record_sha256": translation_record_digest(
                        self.records["signature"]
                    ),
                },
                "review_head_ref": {
                    "record_id": "review-head",
                    "schema_version": REVIEW_SCHEMA,
                    "record_sha256": review_sha256,
                },
                "theory_record_sha256": "sha256:" + "7" * 64,
                "dependency_closure_sha256": "sha256:" + "8" * 64,
            },
        }
        comparison_path.write_text(json.dumps(comparison), encoding="utf-8")
        resolution = {
            "resolution_id": "resolution",
            "status": "HARDENING_INCONCLUSIVE",
            "reason_codes": ["BOUND_ARTIFACT_REPLAY_UNAVAILABLE_V1"],
            "effective_live_criticism_ids": [],
            "obligations": [{"state": "UNRESOLVED"}],
            "human_requirements": [{"state": "UNRESOLVED"}],
            "semantic_verdict": None,
        }

        blocked = self.run_pipeline(hardening_comparison_path=comparison_path)
        self.assertEqual(blocked["stages"]["hardening"]["status"], BLOCKED)
        self.assertEqual(
            blocked["stages"]["hardening"]["details"]["blocked_by"],
            "interpretation_review",
        )

        with (
            mock.patch(
                "creib.forge.translation_pipeline.translation_review_bindings",
                return_value={"binding": "exact"},
            ),
            mock.patch(
                "creib.forge.translation_pipeline.translation_review_surface",
                return_value={"surface": "exact"},
            ),
            mock.patch(
                "creib.forge.translation_pipeline.verify_translation_review_chain",
                return_value=review_state,
            ),
            mock.patch(
                "creib.forge.translation_pipeline.validate_hardening_comparison",
                side_effect=lambda value: value,
            ),
            mock.patch(
                "creib.forge.translation_pipeline.resolve_hardening_comparison",
                return_value=resolution,
            ),
        ):
            report = self.run_pipeline(
                review_dir=review_dir,
                review_head_id="review-head",
                hardening_comparison_path=comparison_path,
            )
        stage = report["stages"]["hardening"]
        self.assertEqual(stage["status"], UNRESOLVED)
        self.assertEqual(
            stage["details"]["hardening_status"], "HARDENING_INCONCLUSIVE"
        )
        self.assertFalse(stage["details"]["supplied_resolution_verified"])

    def test_hardening_rejects_a_stale_successor_snapshot_binding(self) -> None:
        comparison_path = self.root / "comparison-stale.json"
        comparison_path.write_text(
            json.dumps(
                {
                    "comparison_id": "comparison",
                    "execution_semantics": "DECLARED_EXECUTION_SEMANTICS",
                    "successor": {
                        "snapshot_ref": {
                            "record_id": "stale-snapshot",
                            "schema_version": self.snapshot["schema_version"],
                            "record_sha256": translation_record_digest(self.snapshot),
                        },
                        "model_ref": {
                            "record_id": self.snapshot["model_id"],
                            "schema_version": self.records["model"][
                                "schema_version"
                            ],
                            "record_sha256": translation_record_digest(
                                self.records["model"]
                            ),
                        },
                        "signature_ref": {
                            "record_id": self.snapshot["signature_id"],
                            "schema_version": self.records["signature"][
                                "schema_version"
                            ],
                            "record_sha256": translation_record_digest(
                                self.records["signature"]
                            ),
                        },
                        "review_head_ref": {
                            "record_id": "review-head",
                            "schema_version": REVIEW_SCHEMA,
                            "record_sha256": domain_digest(
                                f"{REVIEW_SCHEMA}.complete-record",
                                self.ready_review_state().reviews[-1],
                            ),
                        },
                        "theory_record_sha256": "sha256:" + "7" * 64,
                        "dependency_closure_sha256": "sha256:" + "8" * 64,
                    },
                }
            ),
            encoding="utf-8",
        )
        review_dir = self.root / "reviews-stale"
        review_dir.mkdir()
        with (
            mock.patch(
                "creib.forge.translation_pipeline.translation_review_bindings",
                return_value={"binding": "exact"},
            ),
            mock.patch(
                "creib.forge.translation_pipeline.translation_review_surface",
                return_value={"surface": "exact"},
            ),
            mock.patch(
                "creib.forge.translation_pipeline.verify_translation_review_chain",
                return_value=self.ready_review_state(),
            ),
            mock.patch(
                "creib.forge.translation_pipeline.validate_hardening_comparison",
                side_effect=lambda value: value,
            ),
        ):
            report = self.run_pipeline(
                review_dir=review_dir,
                review_head_id="review-head",
                hardening_comparison_path=comparison_path,
            )
        stage = report["stages"]["hardening"]
        self.assertEqual(stage["status"], INVALID)
        self.assertIn("current translation snapshot", stage["error"]["error"])

    def test_qualification_token_match_stays_unresolved_without_execution(self) -> None:
        report_path = self.root / "exposures.json"
        report_freeze_path = self.root / "report-freeze.json"
        candidate_freeze_path = self.root / "candidate-freeze.json"
        report_freeze = {"freeze_id": "report-freeze"}
        candidate_freeze = {
            "freeze_id": "candidate-freeze",
            "content_id": self.snapshot["snapshot_id"],
            "record_closure_sha256": self.snapshot["record_closure_sha256"],
        }
        report_path.write_text("{}", encoding="utf-8")
        report_freeze_path.write_text(json.dumps(report_freeze), encoding="utf-8")
        candidate_freeze_path.write_text(
            json.dumps(candidate_freeze), encoding="utf-8"
        )
        qualification = {
            "qualification_id": "qualification",
            "qualification_status": ALL_REPRODUCED,
            "case_counts": {"declared_controller_cases": 1},
            "missed_case_ids": [],
            "false_positive_case_ids": [],
            "blindness_verdict": None,
            "controller_declaration_match": True,
            "mutation_execution_verified": False,
            "execution_evidence_verified": False,
            "semantic_verdict": None,
            "translation_fidelity_verdict": None,
        }
        with (
            mock.patch(
                "creib.forge.translation_pipeline.validate_freeze_record",
                side_effect=lambda value: value,
            ),
            mock.patch(
                "creib.forge.translation_pipeline.freeze_translation_snapshot",
                return_value=(self.snapshot, candidate_freeze),
            ),
            mock.patch(
                "creib.forge.translation_pipeline.qualify_exposure_report",
                return_value=qualification,
            ) as qualify,
        ):
            report = self.run_pipeline(
                qualification_report_path=report_path,
                qualification_report_freeze_path=report_freeze_path,
                qualification_candidate_freeze_path=candidate_freeze_path,
                qualification_repository_root=ROOT,
            )
        qualify.assert_called_once_with(
            report_path=report_path,
            report_freeze=report_freeze,
            repository_root=ROOT,
            candidate_snapshot_freeze=candidate_freeze,
            candidate_snapshot_path=self.snapshot_path,
            candidate_records_dir=self.records_dir,
        )
        stage = report["stages"]["qualification"]
        self.assertEqual(stage["status"], UNRESOLVED)
        self.assertTrue(stage["details"]["controller_declaration_match"])
        self.assertFalse(stage["details"]["mutation_execution_verified"])
        self.assertFalse(stage["details"]["execution_evidence_verified"])
        self.assertIsNone(stage["semantic_verdict"])
        self.assertIn("no mutation execution", stage["claim"])

        missing_candidate = self.run_pipeline(
            qualification_report_path=report_path,
            qualification_report_freeze_path=report_freeze_path,
            qualification_repository_root=ROOT,
        )
        self.assertEqual(
            missing_candidate["stages"]["qualification"]["status"], BLOCKED
        )
        self.assertEqual(
            missing_candidate["stages"]["qualification"]["details"][
                "missing_inputs"
            ],
            ["qualification_candidate_freeze"],
        )

    def test_qualification_cannot_switch_snapshots_after_initial_validation(
        self,
    ) -> None:
        initial_id = "TSN:" + "a" * 64
        swapped_id = "TSN:" + "b" * 64
        initial_closure = "sha256:" + "a" * 64
        swapped_closure = "sha256:" + "b" * 64
        self.snapshot["snapshot_id"] = initial_id
        self.snapshot["record_closure_sha256"] = initial_closure
        self.write_snapshot()
        swapped = dict(self.snapshot)
        swapped["snapshot_id"] = swapped_id
        swapped["record_closure_sha256"] = swapped_closure
        swapped_bytes = canonical_bytes(swapped) + b"\n"

        def freeze_record(
            *,
            input_kind: str,
            content_id: str,
            artifact_bytes: bytes,
            record_closure_sha256: str | None,
            qualification_status: str,
        ) -> dict[str, object]:
            record: dict[str, object] = {
                "schema_version": "creib.translation-qualification-freeze.v1",
                "freeze_id": "QFZ:" + "0" * 64,
                "authority_id": "HRC-1",
                "input_kind": input_kind,
                "content_id": content_id,
                "artifact_sha256": hashlib.sha256(artifact_bytes).hexdigest(),
                "artifact_byte_length": len(artifact_bytes),
                "record_closure_sha256": record_closure_sha256,
                "qualification_status": qualification_status,
                "automatic_semantic_effect": "NONE",
                "semantic_verdict": None,
                "translation_fidelity_verdict": None,
            }
            record["freeze_id"] = compute_freeze_id(record)
            return record

        report_path = self.root / "swap-exposures.json"
        report_bytes = b"{}\n"
        report_path.write_bytes(report_bytes)
        report_freeze = freeze_record(
            input_kind="DECLARED_EXPOSURE_REPORT",
            content_id="QER:" + "c" * 64,
            artifact_bytes=report_bytes,
            record_closure_sha256=None,
            qualification_status=REPORT_FROZEN,
        )
        report_freeze_path = self.root / "swap-report-freeze.json"
        report_freeze_path.write_bytes(canonical_bytes(report_freeze) + b"\n")
        candidate_freeze = freeze_record(
            input_kind="TRANSLATION_SNAPSHOT",
            content_id=swapped_id,
            artifact_bytes=swapped_bytes,
            record_closure_sha256=swapped_closure,
            qualification_status=SNAPSHOT_FROZEN,
        )
        candidate_freeze_path = self.root / "swap-candidate-freeze.json"
        candidate_freeze_path.write_bytes(
            canonical_bytes(candidate_freeze) + b"\n"
        )

        def validate_then_swap(*_args):
            self.snapshot_path.write_bytes(swapped_bytes)
            return TranslationValidationResult(initial_id, 10, ())

        with (
            mock.patch(
                "creib.forge.translation_pipeline.load_translation_inventory",
                return_value=self.records,
            ),
            mock.patch(
                "creib.forge.translation_pipeline.validate_translation_snapshot",
                side_effect=validate_then_swap,
            ),
            mock.patch(
                "creib.forge.translation_pipeline.freeze_translation_snapshot"
            ) as replay,
            mock.patch(
                "creib.forge.translation_pipeline.qualify_exposure_report"
            ) as qualify,
        ):
            result = run_translation_pipeline(
                records_dir=self.records_dir,
                snapshot_path=self.snapshot_path,
                qualification_report_path=report_path,
                qualification_report_freeze_path=report_freeze_path,
                qualification_candidate_freeze_path=candidate_freeze_path,
                qualification_repository_root=ROOT,
            )

        stage = result["stages"]["qualification"]
        self.assertEqual(stage["status"], INVALID)
        self.assertIn(
            "initially validated translation snapshot", stage["error"]["error"]
        )
        replay.assert_not_called()
        qualify.assert_not_called()

    def test_invalid_translation_blocks_snapshot_bound_route_validation(self) -> None:
        plan_path = self.root / "plan.json"
        plan_path.write_text(
            json.dumps(
                {
                    "plan_id": "plan",
                    "route": "AUTHORITY_REVIEW",
                    "live_locus_assessment_ids": ["assessment"],
                    "selected_action_id": "action",
                    "next_action": {"research_target": None},
                }
            ),
            encoding="utf-8",
        )
        with (
            mock.patch(
                "creib.forge.translation_pipeline.load_translation_inventory",
                side_effect=RecordError("broken closure"),
            ),
            mock.patch(
                "creib.forge.translation_pipeline.validate_generic_inquiry_plan"
            ),
        ):
            report = run_translation_pipeline(
                records_dir=self.records_dir,
                snapshot_path=self.snapshot_path,
                inquiry_plan_paths=(plan_path,),
            )
        self.assertEqual(report["overall_status"], INVALID)
        self.assertEqual(report["stages"]["translation_integrity"]["status"], INVALID)
        self.assertEqual(report["stages"]["charter"]["status"], BLOCKED)
        self.assertEqual(
            report["stages"]["research_routing_readiness"]["status"], BLOCKED
        )

    def test_cli_emits_fail_closed_json_for_invalid_required_inputs(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools" / "run_translation_harness.py"),
                "--records-dir",
                str(self.root / "absent-records"),
                "--snapshot",
                str(self.root / "absent-snapshot.json"),
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 2)
        output = json.loads(completed.stdout)
        self.assertEqual(output["overall_status"], INVALID)
        self.assertIsNone(output["semantic_verdict"])
        self.assertEqual(output["mapping_fidelity"], "UNREVIEWED")
        self.assertTrue(output["next_actions"])


if __name__ == "__main__":
    unittest.main()
