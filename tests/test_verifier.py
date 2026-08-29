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
    _verify_active_span_geometry,
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
    def active_span_bbox_xml() -> bytes:
        pages = []
        for offset, folio in enumerate(range(218, 234)):
            pages.append(
                '<page width="612.000" height="792.000">'
                f'<word xMin="296.000" yMin="763.000" xMax="316.000" yMax="773.000">{folio}</word>'
                "</page>"
            )
        return ("<html><body><doc>" + "".join(pages) + "</doc></body></html>").encode()

    def copied_repository(self, directory: str) -> Path:
        target = Path(directory) / "repo"
        shutil.copytree(
            ROOT,
            target,
            ignore=shutil.ignore_patterns(".git", ".lake", "__pycache__", "*.pyc"),
        )
        return target

    def test_repository_records_pass_but_pdf_replay_is_partial(self) -> None:
        report = verify_bundle(ROOT)
        self.assertEqual(report["status"], "PARTIAL")
        self.assertEqual(report["record_status"], "PASS")
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

    def test_missing_repository_root_has_stable_json_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing"
            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = main(["--repo-root", str(missing)])
        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 2)
        self.assertEqual(payload["status"], "FAIL")

    def test_verification_does_not_rewrite_inputs(self) -> None:
        tracked = [
            ROOT / "authority" / "source_manifest.json",
            ROOT / "authority" / "source_anchors.json",
            *sorted((ROOT / "bridge" / "declarations").glob("*.json")),
            *sorted((ROOT / "authority" / "transcriptions").glob("*.txt")),
        ]
        before = {path: hashlib.sha256(path.read_bytes()).digest() for path in tracked}
        verify_bundle(ROOT)
        after = {path: hashlib.sha256(path.read_bytes()).digest() for path in tracked}
        self.assertEqual(before, after)

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
