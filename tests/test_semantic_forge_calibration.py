from __future__ import annotations

import copy
from contextlib import redirect_stdout
from dataclasses import replace
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from creib.forge.calibration import (
    PINNED_ROLE_CHALLENGE_CONTRACT_SHA256,
    PINNED_SEED_CORPUS_SHA256,
    ROLE_CHALLENGE_ID,
    ROLE_ISSUE_ID,
    RUN_ID,
    CalibrationRunError,
    attack_search_targets,
    build_calibration_report,
    dumps_calibration_report,
    evaluate_naive_existential_erasure,
    evaluate_weak_role_projection,
    internal_erasure_issue,
    load_calibration_report,
    load_calibration_corpus,
    publish_calibration_report,
    replay_calibration_report,
    run_first_calibration,
    validate_calibration_report,
)
from creib.canonical import bytes_digest, canonical_bytes, domain_digest
from creib.forge.engine import generate_research_warrant
from creib.errors import AuthorityMismatch, RecordError
from creib.forge.models import (
    HardeningStatus,
    ReadinessStatus,
    UnknownKind,
)
from creib.strict_json import load_strict


ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = ROOT / "forge" / "corpus" / "cr-1.0-seed.json"


def authority_binding(corpus) -> dict[str, object]:
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


def walk_keys(value):
    if type(value) is dict:
        for key, item in value.items():
            yield key
            yield from walk_keys(item)
    elif type(value) is list:
        for item in value:
            yield from walk_keys(item)


class SemanticForgeCalibrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.corpus = load_calibration_corpus(CORPUS_PATH)
        cls.report = build_calibration_report(
            cls.corpus,
            authority_binding(cls.corpus),
        )

    def test_strict_load_parses_every_runtime_record_and_selects_role_pair(self) -> None:
        self.assertTrue(self.corpus.challenges)
        self.assertTrue(self.corpus.issues)
        self.assertEqual(
            len(self.corpus.challenges),
            len({item.challenge_id for item in self.corpus.challenges}),
        )
        self.assertEqual(
            len(self.corpus.issues),
            len({item.issue_id for item in self.corpus.issues}),
        )
        self.assertEqual(self.corpus.challenge(ROLE_CHALLENGE_ID).challenge_id, ROLE_CHALLENGE_ID)
        self.assertEqual(self.corpus.issue(ROLE_ISSUE_ID).issue_id, ROLE_ISSUE_ID)

    def test_loader_rejects_duplicate_or_incomplete_annotation_coverage(self) -> None:
        source = load_strict(CORPUS_PATH)
        mutations = {}

        duplicate_challenge = copy.deepcopy(source)
        duplicate_challenge["challenges"].append(
            copy.deepcopy(duplicate_challenge["challenges"][0])
        )
        mutations["duplicate challenge"] = duplicate_challenge

        duplicate_issue = copy.deepcopy(source)
        duplicate_issue["research_issues"].append(
            copy.deepcopy(duplicate_issue["research_issues"][0])
        )
        mutations["duplicate issue"] = duplicate_issue

        duplicate_challenge_annotation = copy.deepcopy(source)
        duplicate_challenge_annotation["challenge_annotations"].append(
            copy.deepcopy(duplicate_challenge_annotation["challenge_annotations"][0])
        )
        mutations["duplicate challenge annotation"] = duplicate_challenge_annotation

        duplicate_issue_annotation = copy.deepcopy(source)
        duplicate_issue_annotation["research_issue_annotations"].append(
            copy.deepcopy(duplicate_issue_annotation["research_issue_annotations"][0])
        )
        mutations["duplicate issue annotation"] = duplicate_issue_annotation

        incomplete = copy.deepcopy(source)
        incomplete["challenge_annotations"].pop()
        mutations["incomplete coverage"] = incomplete

        for name, mutation in mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "corpus.json"
                path.write_text(json.dumps(mutation), encoding="utf-8")
                with self.assertRaisesRegex(
                    RecordError,
                    "identifiers must be unique|coverage must be one-to-one|non-unique",
                ):
                    load_calibration_corpus(path)

    def test_loader_rejects_unknown_fields_and_inductive_policy_drift(self) -> None:
        source = load_strict(CORPUS_PATH)
        mutations = []
        unknown_field = copy.deepcopy(source)
        unknown_field["confidence"] = 1
        mutations.append(unknown_field)
        inductive_policy = copy.deepcopy(source)
        inductive_policy["epistemic_policy"]["passing_tests_confirms"] = True
        mutations.append(inductive_policy)
        provider_oracle = copy.deepcopy(source)
        provider_oracle["research_policy"]["provider_output_is_oracle"] = True
        mutations.append(provider_oracle)

        for mutation in mutations:
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "corpus.json"
                path.write_text(json.dumps(mutation), encoding="utf-8")
                with self.assertRaises(RecordError):
                    load_calibration_corpus(path)

    def test_weak_typed_projection_admits_grounded_and_labels_only_contrast(self) -> None:
        result = evaluate_weak_role_projection(
            self.corpus.challenge(ROLE_CHALLENGE_ID)
        )
        admissions = {
            item["case_id"]: item["admitted_by_weak_projection"]
            for item in result["case_results"]
        }
        self.assertEqual(
            admissions,
            {
                "GROUNDED-ROLE-ASSIGNMENT": True,
                "LABELS-ONLY-CONTRAST": True,
            },
        )
        self.assertEqual(
            result["result_scope"], "NON_AUTHORITATIVE_MECHANICAL_FIXTURE"
        )
        self.assertEqual(
            result["mechanical_observation"],
            "BOTH_GROUNDED_AND_LABELS_ONLY_CONTRASTS_ADMITTED",
        )
        self.assertIsNone(result["semantic_verdict"])

    def test_role_evaluator_rejects_contrary_content_with_same_id_and_type(self) -> None:
        challenge = self.corpus.challenge(ROLE_CHALLENGE_ID)
        contrary = replace(
            challenge,
            oracle="status=source_scoped; labels alone establish semantic roles",
        )
        self.assertEqual(contrary.challenge_id, challenge.challenge_id)
        self.assertEqual(contrary.defect_type, challenge.defect_type)
        with self.assertRaisesRegex(RecordError, "not registered for this challenge content"):
            evaluate_weak_role_projection(contrary)

    def test_role_challenge_contract_is_pinned_to_complete_record(self) -> None:
        challenge = self.corpus.challenge(ROLE_CHALLENGE_ID)
        digest = domain_digest(
            "creib.semantic-forge.challenge-contract.v1",
            challenge.to_dict(),
        ).removeprefix("sha256:")
        self.assertEqual(digest, PINNED_ROLE_CHALLENGE_CONTRACT_SHA256)

    def test_disconnected_predicate_erases_to_same_fixture_results(self) -> None:
        result = evaluate_naive_existential_erasure()
        self.assertFalse(result["new_predicate_connected_to_admission"])
        self.assertTrue(result["old_language_result_preserved"])
        self.assertEqual(
            result["mechanical_observation"],
            "EXISTENTIAL_ERASURE_CHANGES_NOTHING_IN_FIXTURE",
        )
        self.assertIsNone(result["semantic_verdict"])

    def test_research_is_warranted_only_for_external_role_issue(self) -> None:
        internal = internal_erasure_issue()
        external = self.corpus.issue(ROLE_ISSUE_ID)
        self.assertIs(internal.unknown_kind, UnknownKind.INTERNAL)
        self.assertIsNone(generate_research_warrant(internal))
        warrant = generate_research_warrant(external)
        self.assertIsNotNone(warrant)
        self.assertEqual(warrant.discovery_channels, ("AlphaXiv",))
        targets = attack_search_targets(external)
        self.assertEqual(
            len(targets),
            sum(len(rival.falsifier_conditions) for rival in external.rivals),
        )
        for target in targets:
            self.assertIn("counterexample, boundary case, or explicit denial", target["attack_query"])

    def test_report_stays_unresolved_and_awaits_human_semantic_judgment(self) -> None:
        report = self.report
        self.assertEqual(report["run_status"], "RUN_COMPLETE")
        self.assertEqual(report["mechanical_status"], "MECHANICALLY_VALID")
        self.assertEqual(report["epistemic_status"], "UNRESOLVED")
        self.assertEqual(report["review_status"], "AWAITING_HUMAN")
        self.assertIsNone(report["semantic_verdict"])
        self.assertIsNone(report["human_disposition"])
        human_review = report["human_review"]
        self.assertEqual(
            human_review["allowed_loci"],
            ["CANDIDATE", "AUXILIARY", "TEST", "SCOPE"],
        )
        self.assertIs(human_review["multiple_loci_may_coexist"], True)
        self.assertEqual(human_review["overall_status"], "UNRESOLVED")
        self.assertIsNone(human_review["human_triage_record"])
        self.assertNotIn("allowed_dispositions", human_review)
        self.assertNotIn("human_disposition", human_review)
        self.assertIsNone(report["research_routing"]["internal_erasure_warrant"])
        self.assertEqual(
            report["research_routing"]["external_role_warrant"]["discovery_channels"],
            ["AlphaXiv"],
        )
        self.assertEqual(
            report["corpus_trace"]["corpus_sha256"],
            self.corpus.corpus_sha256,
        )
        self.assertEqual(self.corpus.corpus_sha256, PINNED_SEED_CORPUS_SHA256)
        execution = report["execution_contract"]
        self.assertEqual(execution["run_id"], RUN_ID)
        self.assertEqual(execution["corpus_sha256"], PINNED_SEED_CORPUS_SHA256)
        self.assertEqual(
            set(execution["implementation_file_sha256"]),
            {
                "src/creib/__init__.py",
                "src/creib/canonical.py",
                "src/creib/errors.py",
                "src/creib/evidence.py",
                "src/creib/models.py",
                "src/creib/strict_json.py",
                "src/creib/verify.py",
                "src/creib/forge/__init__.py",
                "src/creib/forge/models.py",
                "src/creib/forge/engine.py",
                "src/creib/forge/research.py",
                "src/creib/forge/inquiry.py",
                "src/creib/forge/schema_validation.py",
                "src/creib/forge/calibration.py",
                "tools/run_semantic_forge.py",
                "tools/run_semantic_inquiry.py",
                "tools/validate_semantic_forge.py",
            }
            | {
                path.relative_to(ROOT).as_posix()
                for path in (ROOT / "forge" / "schema").glob("*.schema.json")
            },
        )

    def test_loader_retains_validated_annotation_content_and_digests(self) -> None:
        source = load_strict(CORPUS_PATH)
        expected = {
            record["record_id"]: bytes_digest(canonical_bytes(record))
            for record in source["challenge_annotations"]
        }
        observed = {
            record.record_id: record.canonical_sha256
            for record in self.corpus.challenge_annotations
        }
        self.assertEqual(observed, expected)
        for record in self.corpus.challenge_annotations:
            self.assertEqual(
                json.loads(record.canonical_json)["record_id"],
                record.record_id,
            )
        self.assertEqual(
            self.report["corpus_trace"]["challenge_annotation_sha256"],
            expected,
        )

    def test_corpus_is_read_once_for_hash_and_parse(self) -> None:
        from creib.forge import calibration

        original = calibration._read_bytes
        corpus_reads = []

        def observed(path, where):
            if where == "corpus":
                corpus_reads.append(path)
            return original(path, where)

        with patch("creib.forge.calibration._read_bytes", side_effect=observed):
            loaded = load_calibration_corpus(CORPUS_PATH)
        self.assertEqual(loaded.corpus_sha256, PINNED_SEED_CORPUS_SHA256)
        self.assertEqual(corpus_reads, [CORPUS_PATH])

    def test_changed_corpus_cannot_reuse_fixed_first_run_id(self) -> None:
        source = load_strict(CORPUS_PATH)
        mutations = []

        changed_content = copy.deepcopy(source)
        changed_content["title"] += " changed"
        mutations.append(changed_content)

        changed_id = copy.deepcopy(source)
        changed_id["corpus_id"] = "SMF-CORPUS-CUSTOM"
        mutations.append(changed_id)

        for mutation in mutations:
            with self.subTest(corpus_id=mutation["corpus_id"]), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "corpus.json"
                path.write_text(json.dumps(mutation), encoding="utf-8")
                corpus = load_calibration_corpus(path)
                with self.assertRaisesRegex(RecordError, "fixed first-run ID"):
                    build_calibration_report(corpus, authority_binding(corpus))

    def test_changed_run_id_is_rejected(self) -> None:
        changed = copy.deepcopy(self.report)
        changed["run_id"] = "SMF-CALIBRATION-CR-1-0-CUSTOM"
        with self.assertRaisesRegex(RecordError, "run_id"):
            validate_calibration_report(changed, repo_root=ROOT)

    def test_every_authority_binding_status_and_scope_field_is_exact(self) -> None:
        mutations = {
            "status": "SEMANTICALLY_CONFIRMED",
            "document_id": "CR-1.0-LOOKALIKE",
            "sha256": "0" * 64,
            "byte_length": self.corpus.authority.byte_length + 1,
            "physical_pdf_pages": self.corpus.authority.physical_pdf_pages + 1,
            "semantic_authority": "FORGE_OUTPUT",
            "verification_scope": "SEMANTIC THEOREM CONFIRMED",
        }
        for field, replacement in mutations.items():
            with self.subTest(field=field):
                changed = authority_binding(self.corpus)
                changed[field] = replacement
                with self.assertRaises(AuthorityMismatch):
                    build_calibration_report(self.corpus, changed, repo_root=ROOT)

    def test_canonicalized_scope_tamper_is_rejected_on_load(self) -> None:
        changed = copy.deepcopy(self.report)
        changed["authority_binding"]["verification_scope"] = (
            "SEMANTIC THEOREM CONFIRMED"
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tampered.json"
            path.write_bytes(
                json.dumps(
                    changed,
                    ensure_ascii=False,
                    allow_nan=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
                + b"\n"
            )
            with self.assertRaisesRegex(
                RecordError,
                "verification_scope|non-semantic verification scope",
            ):
                load_calibration_report(path, repo_root=ROOT)

    def test_semantically_changed_run_payload_cannot_keep_contract_identity(self) -> None:
        changed = copy.deepcopy(self.report)
        changed["research_routing"]["external_role_warrant"]["question"] = (
            "A different question with the same run contract"
        )
        with self.assertRaisesRegex(RecordError, "exact deterministic regeneration"):
            validate_calibration_report(changed, repo_root=ROOT)

    def test_assessments_and_readiness_do_not_overclaim(self) -> None:
        assessments = self.report["hardening_assessments"]
        self.assertEqual(
            assessments["naive_disconnected_revision"]["status"],
            HardeningStatus.NO_HARDENING.value,
        )
        self.assertEqual(
            assessments["naive_disconnected_revision"]["preserved_dimensions"],
            [],
        )
        substantive = assessments["substantive_connected_proposal"]
        self.assertEqual(
            substantive["status"],
            HardeningStatus.UNRESOLVED.value,
        )
        self.assertEqual(substantive["excluded_countermodels"], [])
        self.assertNotIn("source_text", substantive["justification_bases"])
        readiness = self.report["formalization_readiness"]
        self.assertEqual(readiness["status"], ReadinessStatus.BLOCKED.value)
        self.assertEqual(readiness["ungrounded_primitives"], ["RoleGrounded"])
        self.assertEqual(len(readiness["missing_negative_witnesses"]), 1)

    def test_report_has_no_scalar_or_social_warrant_fields(self) -> None:
        prohibited = {"score", "confidence", "pass_count", "consensus", "winner"}
        self.assertTrue(prohibited.isdisjoint(set(walk_keys(self.report))))

    def test_report_serialization_is_deterministic(self) -> None:
        first = dumps_calibration_report(self.report)
        second = dumps_calibration_report(
            build_calibration_report(self.corpus, authority_binding(self.corpus))
        )
        self.assertEqual(first, second)
        self.assertEqual(json.loads(first), self.report)

    def test_exact_reference_publish_load_and_replay(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "run.json"
            publish_calibration_report(path, self.report, repo_root=ROOT)
            self.assertEqual(
                path.read_bytes(),
                dumps_calibration_report(self.report, repo_root=ROOT).encode("utf-8")
                + b"\n",
            )
            self.assertEqual(
                load_calibration_report(path, repo_root=ROOT),
                self.report,
            )
            with patch(
                "creib.forge.calibration.verify_authority_binding",
                return_value=authority_binding(self.corpus),
            ):
                replayed = replay_calibration_report(
                    path,
                    repo_root=ROOT,
                    pdf_path=ROOT / "not-read-because-verifier-is-patched.pdf",
                    corpus_path=CORPUS_PATH,
                )
            self.assertEqual(replayed, self.report)

    def test_replay_detects_implementation_drift_before_authority_recheck(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "run.json"
            publish_calibration_report(path, self.report, repo_root=ROOT)
            changed = copy.deepcopy(
                self.report["execution_contract"]["implementation_file_sha256"]
            )
            changed["src/creib/forge/calibration.py"] = "0" * 64
            with patch(
                "creib.forge.calibration.implementation_file_digests",
                return_value=changed,
            ), self.assertRaisesRegex(RecordError, "implementation_file_sha256"):
                replay_calibration_report(
                    path,
                    repo_root=ROOT,
                    pdf_path=ROOT / "authority-is-not-reached.pdf",
                    corpus_path=CORPUS_PATH,
                )

    def test_atomic_publish_refuses_overwrite_and_missing_parent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            output = parent / "run.json"
            publish_calibration_report(output, self.report, repo_root=ROOT)
            original = output.read_bytes()
            with self.assertRaises(CalibrationRunError) as exists:
                publish_calibration_report(output, self.report, repo_root=ROOT)
            self.assertEqual(exists.exception.error_code, "RUN_RECORD_EXISTS")
            self.assertEqual(output.read_bytes(), original)
            self.assertEqual(
                [path for path in parent.iterdir() if path.name != "run.json"],
                [],
            )

            missing = parent / "missing" / "run.json"
            with self.assertRaises(CalibrationRunError) as absent:
                publish_calibration_report(missing, self.report, repo_root=ROOT)
            self.assertEqual(
                absent.exception.error_code,
                "RUN_RECORD_PARENT_MISSING",
            )

    def test_atomic_publish_cleans_temporary_file_after_publish_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            output = parent / "run.json"
            with patch(
                "creib.forge.calibration.os.link",
                side_effect=PermissionError("publication denied"),
            ), self.assertRaises(CalibrationRunError) as failure:
                publish_calibration_report(output, self.report, repo_root=ROOT)
            self.assertEqual(
                failure.exception.error_code,
                "RUN_RECORD_PUBLISH_FAILED",
            )
            self.assertFalse(output.exists())
            self.assertEqual(list(parent.iterdir()), [])

    def test_cli_persistence_failure_is_structured(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "run_semantic_forge_test_module",
            ROOT / "tools" / "run_semantic_forge.py",
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            missing_output = Path(directory) / "missing" / "run.json"
            stdout = io.StringIO()
            with patch.object(
                module,
                "run_first_calibration",
                return_value=self.report,
            ), redirect_stdout(stdout):
                exit_code = module.main(
                    [
                        "first-run",
                        "--repo-root",
                        str(ROOT),
                        "--authority",
                        str(ROOT / "unused.pdf"),
                        "--output",
                        str(missing_output),
                    ]
                )
        failure = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 2)
        self.assertEqual(failure["run_status"], "RUN_FAILED")
        self.assertEqual(failure["error_code"], "RUN_RECORD_PARENT_MISSING")
        self.assertEqual(failure["error_type"], "CalibrationRunError")
        self.assertIsNone(failure["semantic_verdict"])

    def test_noncanonical_run_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "run.json"
            path.write_text(
                json.dumps(self.report, ensure_ascii=False, sort_keys=True),
                encoding="utf-8",
            )
            with self.assertRaises(CalibrationRunError) as failure:
                load_calibration_report(path, repo_root=ROOT)
            self.assertEqual(failure.exception.error_code, "RUN_RECORD_NONCANONICAL")

    def test_full_report_is_optimization_invariant(self) -> None:
        program = """
from pathlib import Path
from creib.forge.calibration import (
    build_calibration_report,
    dumps_calibration_report,
    load_calibration_corpus,
)
root = Path.cwd()
corpus = load_calibration_corpus(root / 'forge/corpus/cr-1.0-seed.json')
binding = {
    'status': 'MECHANICALLY_VALID',
    'document_id': corpus.authority.document_id,
    'sha256': corpus.authority.sha256,
    'byte_length': corpus.authority.byte_length,
    'physical_pdf_pages': corpus.authority.physical_pdf_pages,
    'semantic_authority': 'EXTERNAL_CR_1_0_PDF_ONLY',
    'verification_scope': 'PDF identity, byte length, page structure, and pinned source anchors; not a semantic verdict',
}
report = build_calibration_report(corpus, binding, repo_root=root)
print(dumps_calibration_report(report, repo_root=root))
"""
        environment = {"PYTHONPATH": str(ROOT / "src")}
        normal = subprocess.run(
            [sys.executable, "-c", program],
            cwd=ROOT,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )
        optimized = subprocess.run(
            [sys.executable, "-O", "-c", program],
            cwd=ROOT,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(normal.stdout, optimized.stdout)

    def test_full_run_uses_verified_binding_before_report(self) -> None:
        binding = authority_binding(self.corpus)
        with patch(
            "creib.forge.calibration.verify_authority_binding",
            return_value=binding,
        ) as verifier:
            report = run_first_calibration(
                repo_root=ROOT,
                pdf_path=ROOT / "not-read-because-verifier-is-patched.pdf",
                corpus_path=CORPUS_PATH,
            )
        verifier.assert_called_once()
        self.assertEqual(report["authority_binding"], binding)


if __name__ == "__main__":
    unittest.main()
