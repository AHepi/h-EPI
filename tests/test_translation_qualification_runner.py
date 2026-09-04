from __future__ import annotations

import copy
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from creib.canonical import canonical_bytes, domain_digest
from creib.errors import PolicyViolation, RecordError
from creib.forge.qualification import (
    ALL_REPRODUCED,
    CONTROLS_REL,
    FALSE_POSITIVES,
    HRC_1_MANIFEST_SHA256,
    MANIFEST_REL,
    MISMATCH,
    MISSED,
    SNAPSHOT_FROZEN,
    build_exposure_report,
    compute_exposure_report_id,
    compute_freeze_id,
    compute_qualification_id,
    freeze_exposure_report,
    freeze_translation_snapshot,
    load_hrc_qualification_fixture,
    qualify_exposure_report,
    validate_exposure_report,
    validate_freeze_record,
    verify_frozen_exposure_report,
)
from tests.test_translation_records import _bundle


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "run_translation_qualification.py"
_USE_DEFAULT_CANDIDATE = object()


class TranslationQualificationRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        candidate = _bundle()
        cls.candidate_record_payloads = [
            (record_id, canonical_bytes(record) + b"\n")
            for record_id, record in sorted(candidate["records"].items())
        ]
        cls.candidate_snapshot_payload = (
            canonical_bytes(candidate["snapshot"]) + b"\n"
        )
        cls.fixture = load_hrc_qualification_fixture(ROOT)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            records_dir = root / "records"
            records_dir.mkdir()
            for index, (_record_id, payload) in enumerate(
                cls.candidate_record_payloads
            ):
                (records_dir / f"{index:02d}.json").write_bytes(payload)
            snapshot_path = root / "snapshot.json"
            snapshot_path.write_bytes(cls.candidate_snapshot_payload)
            _snapshot, cls.candidate_snapshot_freeze = freeze_translation_snapshot(
                snapshot_path, records_dir
            )

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.work = Path(self.temporary.name)
        self.candidate_records_dir = self.work / "candidate-records"
        self.candidate_records_dir.mkdir()
        self.candidate_record_paths: dict[str, Path] = {}
        for index, (record_id, payload) in enumerate(self.candidate_record_payloads):
            path = self.candidate_records_dir / f"{index:02d}.json"
            path.write_bytes(payload)
            self.candidate_record_paths[record_id] = path
        self.candidate_snapshot_path = self.work / "candidate-snapshot.json"
        self.candidate_snapshot_path.write_bytes(self.candidate_snapshot_payload)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def report(
        self,
        observations: dict[str, tuple[str, ...]] | None = None,
        *,
        candidate_snapshot_freeze_id: str | None | object = _USE_DEFAULT_CANDIDATE,
    ) -> dict[str, object]:
        if candidate_snapshot_freeze_id is _USE_DEFAULT_CANDIDATE:
            candidate_snapshot_freeze_id = self.candidate_snapshot_freeze[
                "freeze_id"
            ]
        if candidate_snapshot_freeze_id is not None and type(
            candidate_snapshot_freeze_id
        ) is not str:
            raise TypeError("candidate snapshot freeze ID must be a string or null")
        return build_exposure_report(
            source_authority_sha256=self.fixture.source_authority_sha256,
            construction_key_commitment_sha256=(
                self.fixture.construction_key_commitment_sha256
            ),
            observations=observations or dict(self.fixture.expected_cases),
            candidate_snapshot_freeze_id=candidate_snapshot_freeze_id,
        )

    def fabricated_snapshot_freeze(
        self, *, content_seed: str = "1"
    ) -> dict[str, object]:
        freeze: dict[str, object] = {
            "schema_version": "creib.translation-qualification-freeze.v1",
            "freeze_id": "QFZ:" + "0" * 64,
            "authority_id": "HRC-1",
            "input_kind": "TRANSLATION_SNAPSHOT",
            "content_id": "TSN:" + content_seed * 64,
            "artifact_sha256": "2" * 64,
            "artifact_byte_length": 12,
            "record_closure_sha256": domain_digest(
                "test.translation-qualification", f"closure-{content_seed}"
            ),
            "qualification_status": SNAPSHOT_FROZEN,
            "automatic_semantic_effect": "NONE",
            "semantic_verdict": None,
            "translation_fidelity_verdict": None,
        }
        freeze["freeze_id"] = compute_freeze_id(freeze)
        return validate_freeze_record(freeze)

    def write_report(self, report: dict[str, object], name: str = "report.json") -> Path:
        path = self.work / name
        path.write_bytes(canonical_bytes(report) + b"\n")
        return path

    def frozen_report(
        self, observations: dict[str, tuple[str, ...]] | None = None
    ) -> tuple[Path, dict[str, object], dict[str, object]]:
        path = self.write_report(self.report(observations))
        report, freeze = freeze_exposure_report(path)
        return path, report, freeze

    def test_fixture_replay_exposes_exact_controller_surface(self) -> None:
        self.assertEqual(len(self.fixture.expected_cases), 40)
        self.assertEqual(
            set(self.fixture.case_kinds.values()), {"MUTATION", "BENIGN_CONTROL"}
        )
        self.assertEqual(
            sum(kind == "MUTATION" for kind in self.fixture.case_kinds.values()),
            34,
        )
        self.assertEqual(
            sum(kind == "BENIGN_CONTROL" for kind in self.fixture.case_kinds.values()),
            6,
        )

    def test_fixture_hashes_and_parses_each_captured_artifact_once(self) -> None:
        original_read_bytes = Path.read_bytes
        reads: list[Path] = []

        def captured_read(path: Path) -> bytes:
            reads.append(path.resolve())
            return original_read_bytes(path)

        with mock.patch.object(
            Path, "read_bytes", autospec=True, side_effect=captured_read
        ):
            load_hrc_qualification_fixture(ROOT)

        expected = {
            (ROOT / relative).resolve()
            for relative in (
                MANIFEST_REL,
                "forge/translation/qualification/HRC-1.authority.txt",
                "forge/translation/qualification/HRC-1.blind-packet.json",
                "forge/translation/qualification/HRC-1.construction-key.commitment.json",
                "forge/translation/qualification/HRC-1.translation-charter.json",
                "forge/translation/qualification/controller/HRC-1.construction-key.json",
                "forge/translation/qualification/controller/HRC-1.source-obligations.json",
                "forge/translation/qualification/controller/HRC-1.mutation-ledger.json",
                CONTROLS_REL,
            )
        }
        self.assertEqual(set(reads), expected)
        self.assertEqual(Counter(reads), Counter({path: 1 for path in expected}))

    def test_exact_report_has_only_the_scoped_success_status(self) -> None:
        path, _report, freeze = self.frozen_report()
        result = qualify_exposure_report(
            report_path=path,
            report_freeze=freeze,
            repository_root=ROOT,
            candidate_snapshot_freeze=self.candidate_snapshot_freeze,
            candidate_snapshot_path=self.candidate_snapshot_path,
            candidate_records_dir=self.candidate_records_dir,
        )
        self.assertEqual(result["qualification_status"], ALL_REPRODUCED)
        self.assertEqual(result["qualification_id"], compute_qualification_id(result))
        self.assertEqual(result["exact_case_ids"], sorted(self.fixture.expected_cases))
        self.assertEqual(result["detected_case_ids"], sorted(self.fixture.expected_cases))
        self.assertEqual(result["missed_case_ids"], [])
        self.assertEqual(result["false_positive_case_ids"], [])
        self.assertEqual(result["missed_exposure_ids"], [])
        self.assertEqual(result["false_positive_exposure_ids"], [])
        self.assertTrue(result["runner_verified_freeze_before_controller_load"])
        self.assertTrue(result["controller_declaration_match"])
        self.assertFalse(result["mutation_execution_verified"])
        self.assertFalse(result["execution_evidence_verified"])
        self.assertIsNone(result["blindness_verdict"])
        self.assertIsNone(result["semantic_verdict"])
        self.assertIsNone(result["translation_fidelity_verdict"])
        self.assertEqual(result["automatic_semantic_effect"], "NONE")
        expected_exposure_count = sum(
            len(value) for value in self.fixture.expected_cases.values()
        )
        self.assertEqual(len(result["detected_exposure_ids"]), expected_exposure_count)

    def test_partial_miss_and_extra_are_reported_by_exact_pair_id(self) -> None:
        observations = dict(self.fixture.expected_cases)
        miss_case = "HRC-M-A01-AUTHORITY-BYTE"
        missed_exposure = observations[miss_case][0]
        observations[miss_case] = observations[miss_case][1:]
        extra_case = "HRC-C-B01-INDEPENDENT-CLAUSE-ORDER"
        observations[extra_case] = tuple(
            sorted((*observations[extra_case], "TRANSLATION_CORRECT"))
        )
        path, _report, freeze = self.frozen_report(observations)
        result = qualify_exposure_report(
            report_path=path,
            report_freeze=freeze,
            repository_root=ROOT,
            candidate_snapshot_freeze=self.candidate_snapshot_freeze,
            candidate_snapshot_path=self.candidate_snapshot_path,
            candidate_records_dir=self.candidate_records_dir,
        )
        self.assertEqual(result["qualification_status"], MISMATCH)
        self.assertEqual(result["missed_case_ids"], [miss_case])
        self.assertEqual(result["false_positive_case_ids"], [extra_case])
        self.assertEqual(
            result["missed_exposure_ids"], [f"{miss_case}::{missed_exposure}"]
        )
        self.assertEqual(
            result["false_positive_exposure_ids"],
            [f"{extra_case}::TRANSLATION_CORRECT"],
        )
        self.assertFalse(result["controller_declaration_match"])
        self.assertFalse(result["mutation_execution_verified"])
        self.assertFalse(result["execution_evidence_verified"])
        self.assertIsNone(result["translation_fidelity_verdict"])

    def test_unreported_case_is_a_fail_closed_miss(self) -> None:
        observations = dict(self.fixture.expected_cases)
        missing_case = sorted(observations)[0]
        expected = observations.pop(missing_case)
        path, _report, freeze = self.frozen_report(observations)
        result = qualify_exposure_report(
            report_path=path,
            report_freeze=freeze,
            repository_root=ROOT,
            candidate_snapshot_freeze=self.candidate_snapshot_freeze,
            candidate_snapshot_path=self.candidate_snapshot_path,
            candidate_records_dir=self.candidate_records_dir,
        )
        self.assertEqual(result["qualification_status"], MISSED)
        self.assertEqual(result["unreported_case_ids"], [missing_case])
        self.assertEqual(result["missed_case_ids"], [missing_case])
        self.assertEqual(
            result["missed_exposure_ids"],
            sorted(f"{missing_case}::{exposure}" for exposure in expected),
        )

    def test_unknown_case_and_exposure_are_false_positives(self) -> None:
        observations = dict(self.fixture.expected_cases)
        unknown = "HRC-M-Z99-UNKNOWN"
        observations[unknown] = ("INVENTED_EXPOSURE",)
        path, _report, freeze = self.frozen_report(observations)
        result = qualify_exposure_report(
            report_path=path,
            report_freeze=freeze,
            repository_root=ROOT,
            candidate_snapshot_freeze=self.candidate_snapshot_freeze,
            candidate_snapshot_path=self.candidate_snapshot_path,
            candidate_records_dir=self.candidate_records_dir,
        )
        self.assertEqual(result["qualification_status"], FALSE_POSITIVES)
        self.assertEqual(result["unknown_case_ids"], [unknown])
        self.assertEqual(result["false_positive_case_ids"], [unknown])
        self.assertEqual(
            result["false_positive_exposure_ids"],
            [f"{unknown}::INVENTED_EXPOSURE"],
        )

    def test_report_id_is_deterministic_and_order_independent_at_build_boundary(self) -> None:
        forward = dict(self.fixture.expected_cases)
        reverse = dict(reversed(list(forward.items())))
        first = self.report(forward)
        second = self.report(reverse)
        self.assertEqual(first, second)
        self.assertEqual(first["report_id"], compute_exposure_report_id(first))

        changed = copy.deepcopy(first)
        changed["observations"][0]["observed_exposure_ids"].append("EXTRA")  # type: ignore[index,union-attr]
        changed["observations"][0]["observed_exposure_ids"].sort()  # type: ignore[index,union-attr]
        changed["report_id"] = compute_exposure_report_id(changed)
        self.assertNotEqual(first["report_id"], changed["report_id"])

    def test_report_cannot_claim_semantics_or_fidelity(self) -> None:
        for field, value in (
            ("semantic_verdict", "TRUE"),
            ("translation_fidelity_verdict", "CONFIRMED"),
            ("automatic_semantic_effect", "PROMOTE"),
        ):
            report = self.report()
            report[field] = value
            report["report_id"] = compute_exposure_report_id(report)
            with self.subTest(field=field), self.assertRaises(PolicyViolation):
                validate_exposure_report(report)

    def test_freeze_detects_even_nonsemantic_postfreeze_byte_change(self) -> None:
        path, _report, freeze = self.frozen_report()
        path.write_bytes(path.read_bytes() + b"\n")
        with self.assertRaisesRegex(RecordError, "does not match its freeze"):
            verify_frozen_exposure_report(path, freeze)

    def test_snapshot_freeze_binds_verified_id_bytes_and_closure(self) -> None:
        snapshot_id = "TSN:" + "1" * 64
        closure = domain_digest("test.translation-qualification", "closure")
        snapshot = {
            "schema_version": "creib.semantic-forge.translation-snapshot.v1",
            "snapshot_id": snapshot_id,
            "record_closure_sha256": closure,
        }
        path = self.work / "snapshot.json"
        raw = canonical_bytes(snapshot) + b"\n"
        path.write_bytes(raw)
        changed = copy.deepcopy(snapshot)
        changed["record_closure_sha256"] = domain_digest(
            "test.translation-qualification", "changed-closure"
        )
        with mock.patch(
            "creib.forge.qualification.load_translation_inventory", return_value={}
        ), mock.patch(
            "creib.forge.qualification.validate_translation_snapshot",
            return_value=SimpleNamespace(snapshot_id=snapshot_id),
        ), mock.patch.object(
            Path,
            "read_bytes",
            side_effect=[raw, canonical_bytes(changed) + b"\n"],
        ) as read_bytes:
            loaded, freeze = freeze_translation_snapshot(path, self.work)
        self.assertEqual(read_bytes.call_count, 1)
        self.assertEqual(loaded, snapshot)
        self.assertEqual(freeze["qualification_status"], SNAPSHOT_FROZEN)
        self.assertEqual(freeze["content_id"], snapshot_id)
        self.assertEqual(freeze["record_closure_sha256"], closure)
        self.assertEqual(freeze["freeze_id"], compute_freeze_id(freeze))
        validate_freeze_record(freeze)

    def test_report_freeze_hashes_and_parses_one_captured_read(self) -> None:
        report = self.report()
        changed = self.report(
            {"HRC-M-Z99-UNKNOWN": ("INVENTED_EXPOSURE",)}
        )
        raw = canonical_bytes(report) + b"\n"
        with mock.patch.object(
            Path,
            "read_bytes",
            side_effect=[raw, canonical_bytes(changed) + b"\n"],
        ) as read_bytes:
            loaded, freeze = freeze_exposure_report(self.work / "report.json")
        self.assertEqual(read_bytes.call_count, 1)
        self.assertEqual(loaded, report)
        self.assertEqual(freeze["artifact_sha256"], hashlib.sha256(raw).hexdigest())

    def test_report_and_candidate_snapshot_freeze_must_bind_each_other(self) -> None:
        report = self.report(candidate_snapshot_freeze_id=None)
        path = self.write_report(report)
        _loaded, report_freeze = freeze_exposure_report(path)
        with self.assertRaisesRegex(RecordError, "must bind a candidate"):
            qualify_exposure_report(
                report_path=path,
                report_freeze=report_freeze,
                repository_root=ROOT,
                candidate_snapshot_freeze=self.candidate_snapshot_freeze,
                candidate_snapshot_path=self.candidate_snapshot_path,
                candidate_records_dir=self.candidate_records_dir,
            )

        mismatched_freeze = self.fabricated_snapshot_freeze(content_seed="3")
        report = self.report()
        path = self.write_report(report, "bound-report.json")
        _loaded, report_freeze = freeze_exposure_report(path)
        with self.assertRaisesRegex(RecordError, "does not match the report binding"):
            qualify_exposure_report(
                report_path=path,
                report_freeze=report_freeze,
                repository_root=ROOT,
                candidate_snapshot_freeze=mismatched_freeze,
                candidate_snapshot_path=self.candidate_snapshot_path,
                candidate_records_dir=self.candidate_records_dir,
            )

        result = qualify_exposure_report(
            report_path=path,
            report_freeze=report_freeze,
            candidate_snapshot_freeze=self.candidate_snapshot_freeze,
            candidate_snapshot_path=self.candidate_snapshot_path,
            candidate_records_dir=self.candidate_records_dir,
            repository_root=ROOT,
        )
        self.assertEqual(result["qualification_status"], ALL_REPRODUCED)
        self.assertEqual(
            result["candidate_snapshot_freeze_id"],
            self.candidate_snapshot_freeze["freeze_id"],
        )

    def test_self_addressed_fabricated_candidate_freeze_is_rejected(self) -> None:
        fabricated = self.fabricated_snapshot_freeze()
        report = self.report(
            candidate_snapshot_freeze_id=fabricated["freeze_id"]  # type: ignore[arg-type]
        )
        path = self.write_report(report, "fabricated-subject.json")
        _loaded, report_freeze = freeze_exposure_report(path)
        with mock.patch(
            "creib.forge.qualification._load_pinned_hrc_manifest"
        ) as manifest_load, self.assertRaisesRegex(
            RecordError, "translation snapshot does not match its freeze record"
        ):
            qualify_exposure_report(
                report_path=path,
                report_freeze=report_freeze,
                repository_root=ROOT,
                candidate_snapshot_freeze=fabricated,
                candidate_snapshot_path=self.candidate_snapshot_path,
                candidate_records_dir=self.candidate_records_dir,
            )
        manifest_load.assert_not_called()

    def test_postfreeze_snapshot_mutation_fails_before_manifest_load(self) -> None:
        path, _report, report_freeze = self.frozen_report()
        self.candidate_snapshot_path.write_bytes(
            self.candidate_snapshot_path.read_bytes() + b"\n"
        )
        with mock.patch(
            "creib.forge.qualification._load_pinned_hrc_manifest"
        ) as manifest_load, self.assertRaisesRegex(
            RecordError, "translation snapshot does not match its freeze record"
        ):
            qualify_exposure_report(
                report_path=path,
                report_freeze=report_freeze,
                repository_root=ROOT,
                candidate_snapshot_freeze=self.candidate_snapshot_freeze,
                candidate_snapshot_path=self.candidate_snapshot_path,
                candidate_records_dir=self.candidate_records_dir,
            )
        manifest_load.assert_not_called()

    def test_postfreeze_selected_record_mutation_fails_before_manifest_load(
        self,
    ) -> None:
        path, _report, report_freeze = self.frozen_report()
        selected_path = next(iter(self.candidate_record_paths.values()))
        selected_path.write_bytes(selected_path.read_bytes() + b"\n")
        with mock.patch(
            "creib.forge.qualification._load_pinned_hrc_manifest"
        ) as manifest_load, self.assertRaisesRegex(
            RecordError, "not canonical JSON"
        ):
            qualify_exposure_report(
                report_path=path,
                report_freeze=report_freeze,
                repository_root=ROOT,
                candidate_snapshot_freeze=self.candidate_snapshot_freeze,
                candidate_snapshot_path=self.candidate_snapshot_path,
                candidate_records_dir=self.candidate_records_dir,
            )
        manifest_load.assert_not_called()

    def test_public_report_bindings_fail_before_controller_capture(self) -> None:
        cases = (
            (
                "wrong-authority",
                "0" * 64,
                self.fixture.construction_key_commitment_sha256,
                "different HRC-1 authority bytes",
            ),
            (
                "wrong-commitment",
                self.fixture.source_authority_sha256,
                "0" * 64,
                "different construction-key commitment",
            ),
        )
        for name, authority_sha, commitment_sha, error in cases:
            with self.subTest(name=name):
                report = build_exposure_report(
                    source_authority_sha256=authority_sha,
                    construction_key_commitment_sha256=commitment_sha,
                    observations=dict(self.fixture.expected_cases),
                    candidate_snapshot_freeze_id=self.candidate_snapshot_freeze[
                        "freeze_id"
                    ],
                )
                path = self.write_report(report, f"{name}.json")
                _loaded, report_freeze = freeze_exposure_report(path)
                with mock.patch(
                    "creib.forge.qualification._load_hrc_fixture_from_pinned_manifest"
                ) as controller_load, self.assertRaisesRegex(RecordError, error):
                    qualify_exposure_report(
                        report_path=path,
                        report_freeze=report_freeze,
                        repository_root=ROOT,
                        candidate_snapshot_freeze=self.candidate_snapshot_freeze,
                        candidate_snapshot_path=self.candidate_snapshot_path,
                        candidate_records_dir=self.candidate_records_dir,
                    )
                controller_load.assert_not_called()

    def test_fixture_tamper_fails_before_evaluation(self) -> None:
        copied_root = self.work / "copy"
        target = copied_root / "forge" / "translation" / "qualification"
        target.parent.mkdir(parents=True)
        shutil.copytree(ROOT / "forge" / "translation" / "qualification", target)
        key_path = target / "controller" / "HRC-1.construction-key.json"
        key_path.write_bytes(key_path.read_bytes() + b"\n")
        with self.assertRaisesRegex(RecordError, "(byte length|digest) mismatch"):
            load_hrc_qualification_fixture(copied_root)

    def test_coherently_rewritten_fixture_cannot_redefine_hrc_1(self) -> None:
        copied_root = self.work / "rewritten"
        target = copied_root / "forge" / "translation" / "qualification"
        target.parent.mkdir(parents=True)
        shutil.copytree(ROOT / "forge" / "translation" / "qualification", target)

        controls_path = target / "controller" / "HRC-1.benign-controls.json"
        controls = json.loads(controls_path.read_text(encoding="utf-8"))
        controls["controls"][0]["transformation"] += " Coherent rewrite."
        controls_bytes = canonical_bytes(controls) + b"\n"
        controls_path.write_bytes(controls_bytes)

        manifest_path = target / "HRC-1.manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        control_item = next(
            item
            for item in manifest["artifact_inventory"]
            if item["path"] == CONTROLS_REL
        )
        control_item["byte_length"] = len(controls_bytes)
        control_item["sha256"] = hashlib.sha256(controls_bytes).hexdigest()
        manifest_path.write_bytes(canonical_bytes(manifest) + b"\n")

        with self.assertRaisesRegex(RecordError, "pinned SHA-256"):
            load_hrc_qualification_fixture(copied_root)

    def test_repository_manifest_matches_the_out_of_band_pin(self) -> None:
        actual = hashlib.sha256((ROOT / MANIFEST_REL).read_bytes()).hexdigest()
        self.assertEqual(actual, HRC_1_MANIFEST_SHA256)

    def test_cli_success_and_mismatch_have_distinct_exit_codes(self) -> None:
        report_path = self.write_report(self.report())
        freeze_path = self.work / "freeze.json"
        candidate_freeze_path = self.work / "candidate-freeze.json"
        candidate_freeze_path.write_bytes(
            canonical_bytes(self.candidate_snapshot_freeze) + b"\n"
        )
        frozen = subprocess.run(
            [
                sys.executable,
                str(TOOL),
                "freeze-report",
                "--report",
                str(report_path),
                "--output",
                str(freeze_path),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(frozen.returncode, 0, frozen.stderr)
        self.assertTrue(freeze_path.is_file())
        qualified = subprocess.run(
            [
                sys.executable,
                str(TOOL),
                "qualify-report",
                "--report",
                str(report_path),
                "--freeze",
                str(freeze_path),
                "--candidate-freeze",
                str(candidate_freeze_path),
                "--candidate-snapshot",
                str(self.candidate_snapshot_path),
                "--candidate-records-dir",
                str(self.candidate_records_dir),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(qualified.returncode, 0, qualified.stderr)
        self.assertEqual(json.loads(qualified.stdout)["qualification_status"], ALL_REPRODUCED)

        observations = dict(self.fixture.expected_cases)
        observations.pop(sorted(observations)[0])
        missing_path = self.write_report(self.report(observations), "missing.json")
        _report, missing_freeze = freeze_exposure_report(missing_path)
        missing_freeze_path = self.work / "missing-freeze.json"
        missing_freeze_path.write_bytes(canonical_bytes(missing_freeze) + b"\n")
        mismatch = subprocess.run(
            [
                sys.executable,
                str(TOOL),
                "qualify-report",
                "--report",
                str(missing_path),
                "--freeze",
                str(missing_freeze_path),
                "--candidate-freeze",
                str(candidate_freeze_path),
                "--candidate-snapshot",
                str(self.candidate_snapshot_path),
                "--candidate-records-dir",
                str(self.candidate_records_dir),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(mismatch.returncode, 7, mismatch.stderr)
        self.assertEqual(json.loads(mismatch.stdout)["qualification_status"], MISSED)

    def test_cli_qualification_requires_actual_candidate_paths(self) -> None:
        report_path = self.write_report(self.report())
        _report, report_freeze = freeze_exposure_report(report_path)
        report_freeze_path = self.work / "report-freeze.json"
        candidate_freeze_path = self.work / "candidate-freeze.json"
        report_freeze_path.write_bytes(canonical_bytes(report_freeze) + b"\n")
        candidate_freeze_path.write_bytes(
            canonical_bytes(self.candidate_snapshot_freeze) + b"\n"
        )
        missing = subprocess.run(
            [
                sys.executable,
                str(TOOL),
                "qualify-report",
                "--report",
                str(report_path),
                "--freeze",
                str(report_freeze_path),
                "--candidate-freeze",
                str(candidate_freeze_path),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(missing.returncode, 2)
        self.assertIn("--candidate-snapshot", missing.stderr)
        self.assertIn("--candidate-records-dir", missing.stderr)


if __name__ == "__main__":
    unittest.main()
