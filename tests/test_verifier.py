from __future__ import annotations

import hashlib
import io
import json
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from creib.canonical import domain_digest
from creib.errors import AnchorMismatch, AuthorityMismatch, FormalReplayMismatch, PolicyViolation
from creib.cli import main
from creib.models import validate_anchor, validate_manifest
from creib.strict_json import load_strict
from creib.verify import (
    EXPECTED_AXIOM_FREE_DECLARATIONS,
    EXPECTED_SCHEMA_CANONICAL_SHA256,
    _bridge_conformance_status,
    _decode_declared_nfc,
    _enforce_accepted_mapping_policy,
    _inspect_verified_pdf,
    _safe_repository_file,
    _validate_global_metadata_ids,
    _verify_active_span_geometry,
    _verify_axiom_audit,
    _verify_bbox_span,
    _verify_lean_version,
    verify_bundle,
    verify_lean,
    verify_pdf,
)


ROOT = Path(__file__).resolve().parents[1]


class VerifierTests(unittest.TestCase):
    @staticmethod
    def active_span_geometry() -> str:
        lines: list[str] = []
        for page in range(219, 235):
            lines.extend(
                [
                    f"Page  {page} size:  612 x 792 pts (letter)",
                    f"Page  {page} rot:   0",
                ]
            )
        for page in range(219, 235):
            for name in ("MediaBox", "CropBox", "BleedBox", "TrimBox", "ArtBox"):
                lines.append(f"Page  {page} {name}:  0.00 0.00 612.00 792.00")
        return "\n".join(lines)

    @staticmethod
    def active_span_bbox_xml(*, with_synthetic_anchor: bool = False) -> bytes:
        pages = []
        for offset, folio in enumerate(range(218, 234)):
            anchor_words = ""
            if with_synthetic_anchor and folio == 223:
                anchor_words = (
                    '<word xMin="100.000" yMin="100.000" '
                    'xMax="120.000" yMax="110.000">alpha</word>'
                    '<word xMin="130.000" yMin="100.000" '
                    'xMax="150.000" yMax="110.000">beta</word>'
                )
            pages.append(
                '<page width="612.000" height="792.000">'
                f"{anchor_words}"
                f'<word xMin="296.000" yMin="763.000" xMax="316.000" yMax="773.000">{folio}</word>'
                "</page>"
            )
        return ("<html><body><doc>" + "".join(pages) + "</doc></body></html>").encode()

    @staticmethod
    def synthetic_word_snapshot_anchor() -> dict[str, object]:
        return {
            "authoritative_id": "TEST-ANCHOR",
            "locator": {
                "physical_pdf_page": 224,
                "printed_footer_page": 223,
                "tight_bbox_millipoints": [90_000, 90_000, 160_000, 120_000],
            },
            "transcription": {
                "literal_word_snapshot": {
                    "word_count": 2,
                    "sha256": "2648d1eaf3d40ccba9a1eace722d60f48f0a26a2223e9bf4e3c17fe9393fa881",
                }
            },
        }

    def copied_repository(self, directory: str) -> Path:
        target = Path(directory) / "repo"
        shutil.copytree(
            ROOT,
            target,
            ignore=shutil.ignore_patterns(".git", ".lake", "__pycache__", "*.pyc"),
        )
        return target

    @staticmethod
    def accepted_declaration(
        authoritative_id: str,
        *,
        source_declared: list[str] | None = None,
        reconstructed_source: list[str] | None = None,
        bridge: list[str] | None = None,
    ) -> dict[str, object]:
        return {
            "schema_version": "cr-eib.bridge-declaration.v2",
            "authoritative_id": authoritative_id,
            "mapping_status": "accepted",
            "interpretation": {
                "class": "explicitation",
                "bridge_status": "accepted",
                "review_status": "accepted",
                "choice_ids": ["EIB-C-TY01"],
                "coverage": {"status": "exact", "excluded": []},
                "loses": [],
            },
            "replay": {"status": "verified"},
            "proof_obligations": [
                {"obligation_id": "EIB-PO-TEST", "status": "verified"}
            ],
            "dependencies": {
                "source_declared": source_declared or [],
                "reconstructed_source": reconstructed_source or [],
                "bridge": bridge or [],
            },
        }

    def test_repository_records_pass_but_pdf_replay_is_partial(self) -> None:
        report = verify_bundle(ROOT)
        self.assertEqual(report["status"], "PARTIAL")
        self.assertEqual(report["operational_status"], "PARTIAL")
        self.assertEqual(report["status_scope"], "operational-verification-only")
        self.assertEqual(report["mapping_fidelity_status"], "UNREVIEWED")
        self.assertEqual(report["bridge_conformance_status"], "BLOCKED")
        self.assertEqual(report["record_status"], "PASS")
        self.assertEqual(report["schema_status"], "PASS")
        self.assertFalse(report["authority_pdf_checked"])
        self.assertFalse(report["formal_replay_checked"])

    def test_cli_pass_requires_pdf_and_formal_replay_together(self) -> None:
        for arguments, expected_status, pdf_checked, lean_checked in (
            ([], "PARTIAL", False, False),
            (["--pdf", "unused.pdf"], "PARTIAL", True, False),
            (["--lean"], "PARTIAL", False, True),
            (["--pdf", "unused.pdf", "--lean"], "PASS", True, True),
        ):
            with self.subTest(arguments=arguments), patch(
                "creib.cli.verify_pdf"
            ) as pdf_replay, patch("creib.cli.verify_lean") as lean_replay:
                output = io.StringIO()
                with redirect_stdout(output):
                    exit_code = main(["--repo-root", str(ROOT), *arguments])
                payload = json.loads(output.getvalue())
                self.assertEqual(exit_code, 0)
                self.assertEqual(payload["status"], expected_status)
                self.assertEqual(payload["operational_status"], expected_status)
                self.assertEqual(payload["mapping_fidelity_status"], "UNREVIEWED")
                self.assertEqual(payload["bridge_conformance_status"], "BLOCKED")
                self.assertEqual(payload["authority_pdf_checked"], pdf_checked)
                self.assertEqual(payload["formal_replay_checked"], lean_checked)
                self.assertEqual(pdf_replay.call_count, int(pdf_checked))
                self.assertEqual(lean_replay.call_count, int(lean_checked))

    def test_formal_failure_after_pdf_success_is_fail_not_pass(self) -> None:
        output = io.StringIO()
        with patch("creib.cli.verify_pdf"), patch(
            "creib.cli.verify_lean", side_effect=FormalReplayMismatch("replay failed")
        ), redirect_stdout(output):
            exit_code = main(
                ["--repo-root", str(ROOT), "--pdf", "unused.pdf", "--lean"]
            )
        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 6)
        self.assertEqual(payload["status"], "FAIL")
        self.assertEqual(payload["operational_status"], "FAIL")
        self.assertEqual(payload["mapping_fidelity_status"], "NOT_EVALUATED")
        self.assertEqual(payload["bridge_conformance_status"], "NOT_EVALUATED")

    def test_lean_replay_uses_clean_verified_snapshot(self) -> None:
        audit_output = "\n".join(
            f"'{declaration}' does not depend on any axioms"
            for declaration in EXPECTED_AXIOM_FREE_DECLARATIONS
        ).encode("utf-8")
        observed_directories: list[Path] = []

        def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
            cwd = Path(str(kwargs["cwd"]))
            observed_directories.append(cwd)
            self.assertNotEqual(cwd, ROOT / "formal")
            self.assertFalse((cwd / ".lake").exists())
            self.assertEqual(
                (cwd / "lake-manifest.json").read_bytes(),
                (ROOT / "formal" / "lake-manifest.json").read_bytes(),
            )
            self.assertTrue((cwd / "CREIB" / "Core" / "Model.lean").is_file())
            if command[-1] == "--version":
                stdout = (
                    b"Lean (version 4.33.1, x86_64-unknown-linux-gnu, commit "
                    b"819816b2e0a3bf405af45ae5c7af2491d8f5bee6, Release)\n"
                )
            elif command == ["lake", "env", "lean", "CREIB/Audit/Axioms.lean"]:
                stdout = audit_output
            else:
                stdout = b""
            return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr=b"")

        with patch("creib.verify._run", side_effect=fake_run):
            verify_lean(ROOT)
        self.assertEqual(len(observed_directories), 3)
        self.assertEqual(len(set(observed_directories)), 1)
        self.assertFalse(observed_directories[0].exists())

    def test_missing_lean_tool_is_formal_replay_failure(self) -> None:
        for failure, message in (
            (FileNotFoundError(), "tool is unavailable"),
            (PermissionError(), "could not execute"),
        ):
            with self.subTest(failure=type(failure).__name__), patch(
                "creib.verify.subprocess.run", side_effect=failure
            ):
                with self.assertRaisesRegex(FormalReplayMismatch, message):
                    verify_lean(ROOT)

    def test_lean_version_and_commit_are_token_exact(self) -> None:
        valid = (
            b"Lean (version 4.33.1, x86_64-unknown-linux-gnu, commit "
            b"819816b2e0a3bf405af45ae5c7af2491d8f5bee6, Release)\n"
        )
        _verify_lean_version(valid)
        mutations = (
            valid.replace(b"4.33.1", b"4.33.10"),
            valid.replace(b"bee6,", b"bee60,"),
            valid.replace(b", Release)", b", Debug)"),
        )
        for output in mutations:
            with self.subTest(output=output), self.assertRaises(FormalReplayMismatch):
                _verify_lean_version(output)

    def test_axiom_audit_rejects_missing_extra_and_duplicate_results(self) -> None:
        lines = [
            f"'{declaration}' does not depend on any axioms"
            for declaration in EXPECTED_AXIOM_FREE_DECLARATIONS
        ]
        _verify_axiom_audit("\n".join(lines).encode("utf-8"))
        mutations = {
            "missing": lines[:-1],
            "extra": [*lines, "'CREIB.Unreviewed' does not depend on any axioms"],
            "duplicate": [*lines, lines[0]],
        }
        for label, mutated in mutations.items():
            with self.subTest(label=label), self.assertRaises(FormalReplayMismatch):
                _verify_axiom_audit("\n".join(mutated).encode("utf-8"))

    def test_declared_transcription_normalization_is_enforced(self) -> None:
        self.assertEqual(_decode_declared_nfc("Café\n".encode(), "test.txt"), "Café\n")
        with self.assertRaisesRegex(AnchorMismatch, "not NFC"):
            _decode_declared_nfc("Cafe\N{COMBINING ACUTE ACCENT}\n".encode(), "test.txt")

    def test_bundle_checks_declared_normalization_for_every_transcription(self) -> None:
        with patch("creib.verify._decode_declared_nfc", wraps=_decode_declared_nfc) as check:
            verify_bundle(ROOT)
        self.assertEqual(check.call_count, 2)

    def test_reviewed_transcription_byte_tamper_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = self.copied_repository(directory)
            transcription = repository / "authority" / "transcriptions" / "DF-10.reviewed.txt"
            original = transcription.read_bytes()
            mutated = original.replace(b"DF-10", b"DF-1O", 1)
            self.assertNotEqual(mutated, original)
            transcription.write_bytes(mutated)
            with self.assertRaisesRegex(AnchorMismatch, "reviewed transcription hash mismatch"):
                verify_bundle(repository)

    def test_missing_repository_root_has_stable_json_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing"
            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = main(["--repo-root", str(missing)])
        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 2)
        self.assertEqual(payload["status"], "FAIL")
        self.assertEqual(payload["operational_status"], "FAIL")

    def test_raw_io_and_recursion_failures_have_stable_cli_json(self) -> None:
        failures = (
            (OSError("read failed"), "verification input/output failed"),
            (RecursionError("too deep"), "verification input nesting exceeds"),
        )
        for failure, expected_message in failures:
            with self.subTest(failure=type(failure).__name__), patch(
                "creib.cli.verify_bundle", side_effect=failure
            ):
                output = io.StringIO()
                with redirect_stdout(output):
                    exit_code = main(["--repo-root", str(ROOT)])
                payload = json.loads(output.getvalue())
                self.assertEqual(exit_code, 2)
                self.assertEqual(payload["status"], "FAIL")
                self.assertEqual(payload["operational_status"], "FAIL")
                self.assertEqual(payload["exit_code"], 2)
                self.assertIn(expected_message, payload["error"])

    def test_cli_boundary_does_not_mask_process_control_exceptions(self) -> None:
        for failure in (KeyboardInterrupt(), SystemExit(17)):
            with self.subTest(failure=type(failure).__name__), patch(
                "creib.cli.verify_bundle", side_effect=failure
            ), self.assertRaises(type(failure)):
                main(["--repo-root", str(ROOT)])

    def test_verification_does_not_rewrite_inputs(self) -> None:
        tracked = [
            ROOT / "authority" / "source_manifest.json",
            ROOT / "authority" / "source_anchors.json",
            ROOT / "bridge" / "choices" / "interpretation-choices.json",
            *sorted((ROOT / "bridge" / "schema").glob("*.json")),
            *sorted((ROOT / "bridge" / "declarations").glob("*.json")),
            *sorted((ROOT / "authority" / "transcriptions").glob("*.txt")),
        ]
        before = {path: hashlib.sha256(path.read_bytes()).digest() for path in tracked}
        verify_bundle(ROOT)
        after = {path: hashlib.sha256(path.read_bytes()).digest() for path in tracked}
        self.assertEqual(before, after)

    def test_unresolved_v2_interpretation_choice_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = self.copied_repository(directory)
            path = repository / "bridge" / "declarations" / "EIB-DF10-REFINED-CANDIDATE.json"
            declaration = load_strict(path)
            declaration["interpretation"]["choice_ids"][0] = "EIB-C-TY99"
            path.write_text(
                json.dumps(declaration, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(PolicyViolation, "unresolved interpretation choice"):
                verify_bundle(repository)

    def test_choice_registry_semantic_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = self.copied_repository(directory)
            path = repository / "bridge" / "choices" / "interpretation-choices.json"
            registry = load_strict(path)
            registry["choices"].append(
                {
                    "choice_id": "EIB-C-TY99",
                    "statement": "Unreviewed extra interpretation choice.",
                    "authority_status": "not-a-source-fact",
                    "bridge_status": "proposed",
                }
            )
            path.write_text(
                json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(PolicyViolation, "choice registry differs"):
                verify_bundle(repository)

    def test_published_schema_semantic_drift_is_rejected(self) -> None:
        for relative in EXPECTED_SCHEMA_CANONICAL_SHA256:
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as directory:
                repository = self.copied_repository(directory)
                path = repository / relative
                schema = load_strict(path)
                schema["title"] += " drift"
                path.write_text(
                    json.dumps(schema, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                with self.assertRaisesRegex(PolicyViolation, "schema canonical digest mismatch"):
                    verify_bundle(repository)

    def test_v2_required_projection_and_model_expansion_are_fail_closed(self) -> None:
        for missing_kind in ("source-projection", "model-expansion"):
            with self.subTest(missing_kind=missing_kind), tempfile.TemporaryDirectory() as directory:
                repository = self.copied_repository(directory)
                path = repository / "bridge" / "declarations" / "EIB-DF10-REFINED-CANDIDATE.json"
                declaration = load_strict(path)
                declaration["proof_obligations"] = [
                    obligation
                    for obligation in declaration["proof_obligations"]
                    if obligation["kind"] != missing_kind
                ]
                path.write_text(
                    json.dumps(declaration, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                with self.assertRaisesRegex(PolicyViolation, missing_kind):
                    verify_bundle(repository)

    def test_verified_obligation_artifact_hash_is_checked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = self.copied_repository(directory)
            path = repository / "bridge" / "declarations" / "EIB-DF10-REFINED-CANDIDATE.json"
            declaration = load_strict(path)
            declaration["proof_obligations"][0]["artifact"]["sha256"] = "0" * 64
            path.write_text(
                json.dumps(declaration, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(PolicyViolation, "proof-artifact hash mismatch"):
                verify_bundle(repository)

    def test_verified_obligation_artifact_must_be_in_reviewed_formal_package(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = self.copied_repository(directory)
            path = repository / "bridge" / "declarations" / "EIB-DF10-REFINED-CANDIDATE.json"
            declaration = load_strict(path)
            artifact = declaration["proof_obligations"][0]["artifact"]
            artifact["path"] = "README.md"
            artifact["sha256"] = hashlib.sha256(
                (repository / "README.md").read_bytes()
            ).hexdigest()
            path.write_text(
                json.dumps(declaration, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(PolicyViolation, "outside the reviewed formal package"):
                verify_bundle(repository)

    def test_verified_obligation_symbol_binding_is_pinned(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = self.copied_repository(directory)
            path = repository / "bridge" / "declarations" / "EIB-DF10-REFINED-CANDIDATE.json"
            declaration = load_strict(path)
            declaration["proof_obligations"][0]["artifact"]["symbol"] = "CREIB.DoesNotExist"
            path.write_text(
                json.dumps(declaration, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(PolicyViolation, "unreviewed proof-artifact symbol"):
                verify_bundle(repository)

    def test_v2_metadata_ids_are_unique_across_declarations_and_kinds(self) -> None:
        def declaration(identifier: str, *, coverage_id: str) -> dict[str, object]:
            return {
                "schema_version": "cr-eib.bridge-declaration.v2",
                "interpretation": {
                    "preserves": [
                        {"preservation_id": identifier, "statement": "preserved"}
                    ],
                    "loses": [],
                    "coverage": {
                        "coverage_id": coverage_id,
                        "excluded": [],
                    },
                },
                "proof_obligations": [],
            }

        declarations = {
            "EIB-A": declaration("EIB-META-SHARED", coverage_id="EIB-COV-A"),
            "EIB-B": declaration("EIB-PRES-B", coverage_id="EIB-META-SHARED"),
        }
        with self.assertRaisesRegex(PolicyViolation, "not globally unique"):
            _validate_global_metadata_ids(declarations)

    def test_accepted_mapping_rejects_nonaccepted_choice_before_pilot_pins(self) -> None:
        declarations = {
            "EIB-DF10-CANDIDATE": self.accepted_declaration("DF-10")
        }
        choices = {"EIB-C-TY01": {"bridge_status": "proposed"}}
        with self.assertRaisesRegex(PolicyViolation, "non-accepted choice"):
            _enforce_accepted_mapping_policy(declarations, choices)

    def test_accepted_mapping_requires_complete_obligations_and_dependencies(self) -> None:
        accepted = self.accepted_declaration("TH-3", bridge=["EIB-BASE"])
        accepted["proof_obligations"][0]["status"] = "open"
        base = {
            "schema_version": "cr-eib.bridge-declaration.v2",
            "mapping_status": "candidate",
        }
        declarations = {"EIB-MAPPED": accepted, "EIB-BASE": base}
        choices = {"EIB-C-TY01": {"bridge_status": "accepted"}}

        with self.assertRaisesRegex(PolicyViolation, "incomplete proof obligations"):
            _enforce_accepted_mapping_policy(declarations, choices)

        accepted["proof_obligations"][0]["status"] = "verified"
        with self.assertRaisesRegex(PolicyViolation, "non-accepted bridge declaration"):
            _enforce_accepted_mapping_policy(declarations, choices)

    def test_accepted_mapping_requires_exact_lossless_coverage(self) -> None:
        accepted = self.accepted_declaration("DF-10")
        interpretation = accepted["interpretation"]
        interpretation["coverage"]["status"] = "partial"
        declarations = {"EIB-MAPPED": accepted}
        choices = {"EIB-C-TY01": {"bridge_status": "accepted"}}

        with self.assertRaisesRegex(PolicyViolation, "exact exclusion-free coverage"):
            _enforce_accepted_mapping_policy(declarations, choices)

        interpretation["coverage"]["status"] = "exact"
        interpretation["coverage"]["excluded"] = [
            {"exclusion_id": "EIB-EXC-TEST", "statement": "unmapped meaning"}
        ]
        with self.assertRaisesRegex(PolicyViolation, "exact exclusion-free coverage"):
            _enforce_accepted_mapping_policy(declarations, choices)

        interpretation["coverage"]["excluded"] = []
        interpretation["loses"] = [
            {"loss_id": "EIB-LOSS-TEST", "statement": "unresolved meaning"}
        ]
        with self.assertRaisesRegex(PolicyViolation, "semantic losses"):
            _enforce_accepted_mapping_policy(declarations, choices)

    def test_accepted_mapping_rejects_refinement_and_assumption_classes(self) -> None:
        choices = {"EIB-C-TY01": {"bridge_status": "accepted"}}
        for interpretation_class in ("refinement", "assumption"):
            declaration = self.accepted_declaration("DF-10")
            declaration["interpretation"]["class"] = interpretation_class
            with self.subTest(interpretation_class=interpretation_class), self.assertRaisesRegex(
                PolicyViolation, "equivalence-capable"
            ):
                _enforce_accepted_mapping_policy({"EIB-MAPPED": declaration}, choices)
        abbreviation = self.accepted_declaration("DF-10")
        abbreviation["interpretation"]["class"] = "abbreviation"
        _enforce_accepted_mapping_policy({"EIB-MAPPED": abbreviation}, choices)

    def test_accepted_mapping_requires_accepted_source_dependency_closure(self) -> None:
        choices = {"EIB-C-TY01": {"bridge_status": "accepted"}}
        dependency = self.accepted_declaration("DF-10")
        for dependency_kind in ("source_declared", "reconstructed_source"):
            dependent = self.accepted_declaration(
                "TH-3", **{dependency_kind: ["DF-10"]}
            )
            with self.subTest(dependency_kind=dependency_kind), self.assertRaisesRegex(
                PolicyViolation, f"unresolved {dependency_kind} dependency"
            ):
                _enforce_accepted_mapping_policy({"EIB-TH3": dependent}, choices)
            _enforce_accepted_mapping_policy(
                {"EIB-TH3": dependent, "EIB-DF10": dependency}, choices
            )

    def test_bridge_conformance_is_derived_fail_closed(self) -> None:
        dependency = self.accepted_declaration("DF-10")
        dependent = self.accepted_declaration("TH-3", source_declared=["DF-10"])
        declarations = {"EIB-DF10": dependency, "EIB-TH3": dependent}
        self.assertEqual(_bridge_conformance_status(declarations, "UNREVIEWED"), "BLOCKED")
        self.assertEqual(_bridge_conformance_status(declarations, "ACCEPTED"), "PASS")
        dependent["dependencies"]["source_declared"] = ["MS-4"]
        self.assertEqual(_bridge_conformance_status(declarations, "ACCEPTED"), "BLOCKED")

    def test_bad_pdf_hash_stops_before_inspector(self) -> None:
        manifest = validate_manifest(load_strict(ROOT / "authority" / "source_manifest.json"))
        anchor_set = load_strict(ROOT / "authority" / "source_anchors.json")
        anchors = [validate_anchor(record, manifest) for record in anchor_set["anchors"]]
        called = False

        def inspector(_data: bytes, _manifest: dict, _anchors: list) -> None:
            nonlocal called
            called = True

        with tempfile.TemporaryDirectory() as directory:
            bad_pdf = Path(directory) / "authority.pdf"
            bad_pdf.write_bytes(b"\0" * manifest["byte_length"])
            with self.assertRaises(AuthorityMismatch):
                verify_pdf(bad_pdf, manifest, anchors, inspector=inspector)
        self.assertFalse(called)

    def test_active_span_geometry_parser_rejects_interior_drift(self) -> None:
        manifest = validate_manifest(load_strict(ROOT / "authority" / "source_manifest.json"))
        valid = self.active_span_geometry()
        _verify_active_span_geometry(valid, manifest)
        mutations = {
            "rotation": valid.replace("Page  230 rot:   0", "Page  230 rot:   90"),
            "missing CropBox": valid.replace(
                "Page  225 CropBox:  0.00 0.00 612.00 792.00\n", ""
            ),
            "sub-millipoint": valid.replace(
                "Page  225 MediaBox:  0.00", "Page  225 MediaBox:  0.0001"
            ),
        }
        for label, mutated in mutations.items():
            with self.subTest(label=label), self.assertRaises((AuthorityMismatch, AnchorMismatch)):
                _verify_active_span_geometry(mutated, manifest)

    def test_active_span_footer_parser_rejects_wrong_or_missing_folio(self) -> None:
        manifest = validate_manifest(load_strict(ROOT / "authority" / "source_manifest.json"))
        valid = self.active_span_bbox_xml()
        _verify_bbox_span(valid, manifest, [])
        mutations = {
            "wrong folio": valid.replace(b">225</word>", b">0225</word>"),
            "outside footer": valid.replace(b'yMin="763.000"', b'yMin="740.000"', 1),
            "missing page": valid.replace(
                b'<page width="612.000" height="792.000"><word xMin="296.000" yMin="763.000" xMax="316.000" yMax="773.000">233</word></page>',
                b"",
            ),
        }
        for label, mutated in mutations.items():
            with self.subTest(label=label), self.assertRaises(AuthorityMismatch):
                _verify_bbox_span(mutated, manifest, [])

    def test_synthetic_anchor_word_snapshot_fixture_passes(self) -> None:
        manifest = validate_manifest(load_strict(ROOT / "authority" / "source_manifest.json"))
        _verify_bbox_span(
            self.active_span_bbox_xml(with_synthetic_anchor=True),
            manifest,
            [self.synthetic_word_snapshot_anchor()],
        )

    def test_anchor_word_snapshot_rejects_text_coordinate_and_count_mutations(self) -> None:
        manifest = validate_manifest(load_strict(ROOT / "authority" / "source_manifest.json"))
        valid = self.active_span_bbox_xml(with_synthetic_anchor=True)
        beta_word = (
            b'<word xMin="130.000" yMin="100.000" '
            b'xMax="150.000" yMax="110.000">beta</word>'
        )
        mutations = {
            "text": (
                valid.replace(b">alpha</word>", b">Alpha</word>", 1),
                "literal word-snapshot mismatch",
            ),
            "coordinate-with-same-selection": (
                valid.replace(b'xMin="100.000"', b'xMin="101.000"', 1),
                "literal word-snapshot mismatch",
            ),
            "word-count": (
                valid.replace(beta_word, b"", 1),
                "word-count mismatch",
            ),
        }
        for label, (mutated, message) in mutations.items():
            self.assertNotEqual(mutated, valid)
            with self.subTest(label=label), self.assertRaisesRegex(AnchorMismatch, message):
                _verify_bbox_span(
                    mutated,
                    manifest,
                    [self.synthetic_word_snapshot_anchor()],
                )

    def test_pdfinfo_version_drift_is_rejected(self) -> None:
        manifest = validate_manifest(load_strict(ROOT / "authority" / "source_manifest.json"))
        anchor_set = load_strict(ROOT / "authority" / "source_anchors.json")
        anchors = [validate_anchor(record, manifest) for record in anchor_set["anchors"]]

        def fake_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[bytes]:
            if command == ["pdfinfo", "-v"]:
                return subprocess.CompletedProcess(
                    command,
                    0,
                    stdout=b"",
                    stderr=b"pdfinfo version 26.05.1\n",
                )
            if command[0] == "pdfinfo":
                return subprocess.CompletedProcess(
                    command,
                    0,
                    stdout=b"Pages: 286\nPage size: 612 x 792 pts (letter)\n",
                    stderr=b"",
                )
            raise AssertionError(f"unexpected command before pdfinfo version rejection: {command}")

        with patch("creib.verify._run", side_effect=fake_run), self.assertRaisesRegex(
            AuthorityMismatch, "pdfinfo version differs"
        ):
            _inspect_verified_pdf(b"synthetic verified PDF bytes", manifest, anchors)

    def test_pdftotext_version_drift_is_rejected(self) -> None:
        manifest = validate_manifest(load_strict(ROOT / "authority" / "source_manifest.json"))
        anchor_set = load_strict(ROOT / "authority" / "source_anchors.json")
        anchors = [validate_anchor(record, manifest) for record in anchor_set["anchors"]]

        def fake_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[bytes]:
            if command == ["pdfinfo", "-v"]:
                return subprocess.CompletedProcess(
                    command,
                    0,
                    stdout=b"",
                    stderr=b"pdfinfo version 26.05.0\n",
                )
            if command[:2] == ["pdftotext", "-v"]:
                return subprocess.CompletedProcess(
                    command,
                    0,
                    stdout=b"",
                    stderr=b"pdftotext version 24.02.1\n",
                )
            if command[0] == "pdfinfo":
                return subprocess.CompletedProcess(
                    command,
                    0,
                    stdout=b"Pages: 286\nPage size: 612 x 792 pts (letter)\n",
                    stderr=b"",
                )
            raise AssertionError(f"unexpected command before pdftotext version rejection: {command}")

        with patch("creib.verify._run", side_effect=fake_run), patch(
            "creib.verify._verify_active_span_geometry"
        ), self.assertRaisesRegex(AnchorMismatch, "pdftotext version mismatch for DF-10"):
            _inspect_verified_pdf(b"synthetic verified PDF bytes", manifest, anchors)

    def test_repository_path_rejects_intermediate_symlink_component(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory) / "repo"
            real = repository / "real"
            real.mkdir(parents=True)
            (real / "evidence.txt").write_text("evidence\n", encoding="utf-8")
            (repository / "alias").symlink_to(real, target_is_directory=True)
            with self.assertRaisesRegex(PolicyViolation, "symlinked evidence path is forbidden"):
                _safe_repository_file(repository, "alias/evidence.txt")

    def test_pdf_symlink_is_rejected(self) -> None:
        manifest = validate_manifest(load_strict(ROOT / "authority" / "source_manifest.json"))
        anchor_set = load_strict(ROOT / "authority" / "source_anchors.json")
        anchors = [validate_anchor(record, manifest) for record in anchor_set["anchors"]]
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target.pdf"
            target.write_bytes(b"not the authority")
            link = Path(directory) / "authority.pdf"
            link.symlink_to(target)
            with self.assertRaises(AuthorityMismatch):
                verify_pdf(link, manifest, anchors)

    def test_mapping_symbol_path_and_command_drift_are_rejected(self) -> None:
        mutations = {
            "mapping status": lambda declaration: declaration.__setitem__("mapping_status", "accepted"),
            "symbol": lambda declaration: declaration["typed_body"].__setitem__("symbol", "CREIB.DoesNotExist"),
            "path": lambda declaration: declaration["typed_body"].__setitem__("path", "README.md"),
            "command": lambda declaration: declaration["replay"].__setitem__("command", "false"),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                repository = self.copied_repository(directory)
                path = repository / "bridge" / "declarations" / "EIB-TH3B-PILOT.json"
                declaration = load_strict(path)
                mutate(declaration)
                path.write_text(json.dumps(declaration, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                with self.assertRaises(PolicyViolation):
                    verify_bundle(repository)

    def test_typed_body_byte_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = self.copied_repository(directory)
            typed_body = repository / "formal" / "CREIB" / "Pilot" / "TH3Countermodel.lean"
            typed_body.write_text(typed_body.read_text(encoding="utf-8") + "\n-- drift\n", encoding="utf-8")
            with self.assertRaisesRegex(PolicyViolation, "typed-body hash mismatch"):
                verify_bundle(repository)

    def test_non_leaf_formal_package_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = self.copied_repository(directory)
            model = repository / "formal" / "CREIB" / "Core" / "Model.lean"
            model.write_text(model.read_text(encoding="utf-8") + "\n-- drift\n", encoding="utf-8")
            with self.assertRaisesRegex(FormalReplayMismatch, "formal package hash mismatch"):
                verify_bundle(repository)

    def test_extra_anchor_is_rejected_even_with_valid_content_address(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = self.copied_repository(directory)
            path = repository / "authority" / "source_anchors.json"
            anchor_set = load_strict(path)
            extra = json.loads(json.dumps(anchor_set["anchors"][0]))
            extra["payload"]["authoritative_id"] = "FAKE-1"
            extra["anchor_digest"] = domain_digest("CR-EIB/source-anchor/v1", extra["payload"])
            anchor_set["anchors"].append(extra)
            path.write_text(json.dumps(anchor_set, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(AnchorMismatch, "pilot anchor set differs"):
                verify_bundle(repository)

    def test_coordinated_anchor_rehash_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = self.copied_repository(directory)
            path = repository / "authority" / "source_anchors.json"
            anchor_set = load_strict(path)
            th3 = anchor_set["anchors"][1]
            th3["payload"]["transcription"]["declared_transformations"][0] = (
                "invented transformation"
            )
            th3["anchor_digest"] = domain_digest("CR-EIB/source-anchor/v1", th3["payload"])
            path.write_text(json.dumps(anchor_set, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(AnchorMismatch, "identity map differs"):
                verify_bundle(repository)

    def test_authority_checksum_file_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = self.copied_repository(directory)
            checksum = repository / "authority" / "authority.pdf.sha256"
            checksum.write_text("0" * 64 + "  wrong.pdf\n", encoding="utf-8")
            with self.assertRaises(AuthorityMismatch):
                verify_bundle(repository)


if __name__ == "__main__":
    unittest.main()
