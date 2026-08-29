"""Read-only verification of authority anchors and bridge mappings."""

from __future__ import annotations

import hashlib
import os
import re
import stat
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN
from pathlib import Path
from typing import Any, Callable

from .canonical import canonical_bytes
from .errors import AnchorMismatch, AuthorityMismatch, FormalReplayMismatch, PolicyViolation, RecordError
from .models import validate_anchor, validate_declaration, validate_manifest
from .strict_json import load_strict

EXPECTED_MANIFEST = {
    "document_id": "CR-1.0",
    "sha256": "08ff81e848fea976b558345402d85723173be8f40f1041fb00d6267f1e026b8b",
    "byte_length": 1_734_769,
    "page_count": 286,
    "page_size_millipoints": [612_000, 792_000],
    "active_span": {
        "physical_pdf_pages": [219, 234],
        "printed_folios": [218, 233],
    },
}

EXPECTED_ANCHORS = {
    "DF-10": {
        "title_raw": "DF-10 (successful explanatory-knowledge creation).",
        "section_raw": "2. Eliminable semantic definitions",
        "physical_pdf_page": 224,
        "printed_footer_page": 223,
        "tight_bbox_millipoints": [53_671, 284_853, 558_013, 387_170],
        "word_count": 68,
        "word_snapshot_sha256": "f8d48220bda47bf3824781f8f76f00f7c16cda95dc71035df05c4da426e4f3be",
        "reviewed_sha256": "a602a92526bf8a81e812a4a45ef1b5e8de47b308f2888f70481bd728c466b0c8",
        "source_dependencies": [],
        "declared_exhaustive": False,
        "source_status_raw": "[R: S-BOI1, S-FOR3, S-FOR8]",
        "source_scope": "whole clause",
        "source_tags": ["S-BOI1", "S-FOR3", "S-FOR8"],
        "regions": [
            {"name": "title", "bbox_millipoints": [54_000, 284_853, 308_896, 293_321]},
            {"name": "formula", "bbox_millipoints": [72_580, 322_326, 539_419, 336_589]},
            {"name": "prose", "bbox_millipoints": [53_671, 352_698, 558_012, 375_094]},
            {"name": "source-tag-continuation", "bbox_millipoints": [54_000, 378_701, 130_469, 387_169]},
        ],
    },
    "TH-3": {
        "title_raw": "TH-3 Retention is required by successful explanatory creation but is not suffi-\ncient",
        "section_raw": "8. Key theorems and non-entailments",
        "physical_pdf_page": 230,
        "printed_footer_page": 229,
        "tight_bbox_millipoints": [54_000, 89_639, 559_575, 238_822],
        "word_count": 116,
        "word_snapshot_sha256": "7e38c0169754f7779e3fd15c266593eade0d33863a0c9c3872a82ca0eabe8989",
        "reviewed_sha256": "8c16b3073b182d89f8dfb606b8ff67ff07c2299c0ae64a26f3aee42e45ad5545",
        "source_dependencies": ["MS-4", "MS-8", "SC-7", "SC-8", "DF-7a", "DF-10", "IR-2", "IR-4"],
        "declared_exhaustive": True,
        "source_status_raw": "Source entitlement: S-BOI1, S-FOR3, S-FOR8; the typed separation is R.",
        "source_scope": "the typed separation",
        "source_tags": ["S-BOI1", "S-FOR3", "S-FOR8"],
        "regions": [
            {"name": "clause", "bbox_millipoints": [54_000, 89_639, 559_575, 238_822]},
        ],
    },
}

EXPECTED_ANCHOR_DIGESTS = {
    "DF-10": "sha256:2ce383d202be73bd20465f0d0cbd39565fb418cdb6a90af006dae4d8bc260bff",
    "TH-3": "sha256:9a77b972f262b74b411a40999c0c5b235b5abfbd0091fd4c4ba9499462cdaa1c",
}

EXPECTED_DECLARATIONS = {
    "EIB-DF10-CANDIDATE",
    "EIB-TH3A-PILOT",
    "EIB-TH3B-PILOT",
}

EXPECTED_PARAMETERS = [
    {"name": "M", "sort": "CRModel", "binding": "explicit"},
    {"name": "s", "sort": "M.Sys", "binding": "explicit"},
    {"name": "x", "sort": "M.Content", "binding": "explicit"},
    {"name": "p", "sort": "M.Problem", "binding": "explicit"},
    {"name": "b", "sort": "M.Background", "binding": "explicit"},
    {"name": "h", "sort": "M.Hist", "binding": "explicit"},
    {"name": "ctx", "sort": "IntervalContext(M)", "binding": "explicit"},
]

EXPECTED_OPAQUE_PORTS = [
    {"name": "Endpoint", "signature": "Interval → Time → Prop", "binding": "model-field"},
    {
        "name": "CCPResult",
        "signature": "Sys → Content → Problem → Background → Hist → Interval → Prop",
        "binding": "model-field",
    },
    {
        "name": "K_E",
        "signature": "Content → Problem → Background → Hist → Time → Prop",
        "binding": "model-field",
    },
    {
        "name": "Retained",
        "signature": "Sys → Content → Hist → Time → Prop",
        "binding": "model-field",
    },
]

EXPECTED_DECLARATION_POLICY = {
    "EIB-DF10-CANDIDATE": {
        "authoritative_id": "DF-10",
        "source_anchor_digest": "sha256:2ce383d202be73bd20465f0d0cbd39565fb418cdb6a90af006dae4d8bc260bff",
        "mapping_status": "candidate",
        "proposed_inferential_status": "DEF",
        "parameters": EXPECTED_PARAMETERS,
        "opaque_ports": EXPECTED_OPAQUE_PORTS,
        "dependencies": {
            "source_declared": [],
            "reconstructed_source": ["MS-8", "SC-7", "DF-7a"],
            "bridge": [],
        },
        "claim_scope": "Candidate typing of DF-10 only; opaque semantic ports remain uninterpreted and the t_I endpoint is supplied by an explicit interval context.",
        "symbol": "CREIB.EIB_DF10_CANDIDATE",
        "path": "formal/CREIB/Bridge/DF10Candidate.lean",
        "sha256": "14b4fe0ac3a9f1d707f1ac942b85a67a41915d4977211325d6465169c8ca2128",
        "closed_proposition": False,
        "explicit_negative_required_for_countermodel": False,
        "replay_status": "verified",
        "replay_command": "cd formal && lake build",
        "expected_axioms": [],
    },
    "EIB-TH3A-PILOT": {
        "authoritative_id": "TH-3",
        "source_anchor_digest": "sha256:9a77b972f262b74b411a40999c0c5b235b5abfbd0091fd4c4ba9499462cdaa1c",
        "mapping_status": "candidate",
        "proposed_inferential_status": "DER",
        "parameters": EXPECTED_PARAMETERS,
        "opaque_ports": EXPECTED_OPAQUE_PORTS,
        "dependencies": {
            "source_declared": ["MS-4", "MS-8", "SC-7", "SC-8", "DF-7a", "DF-10", "IR-2", "IR-4"],
            "reconstructed_source": [],
            "bridge": ["EIB-DF10-CANDIDATE"],
        },
        "claim_scope": "Definitional unfolding of EIB-DF10-CANDIDATE over the minimal unconstrained port signature; not adjudication of authoritative TH-3 or its dependency closure.",
        "symbol": "CREIB.EIB_TH3a_unfold",
        "path": "formal/CREIB/Pilot/TH3.lean",
        "sha256": "ef9096ff0fe7ef133757ccb57ba3fc52a41638b339539af1737584936c3cb11a",
        "closed_proposition": True,
        "explicit_negative_required_for_countermodel": False,
        "replay_status": "verified",
        "replay_command": "cd formal && lake build",
        "expected_axioms": [],
    },
    "EIB-TH3B-PILOT": {
        "authoritative_id": "TH-3",
        "source_anchor_digest": "sha256:9a77b972f262b74b411a40999c0c5b235b5abfbd0091fd4c4ba9499462cdaa1c",
        "mapping_status": "candidate",
        "proposed_inferential_status": "DER",
        "parameters": EXPECTED_PARAMETERS,
        "opaque_ports": EXPECTED_OPAQUE_PORTS,
        "dependencies": {
            "source_declared": ["MS-4", "MS-8", "SC-7", "SC-8", "DF-7a", "DF-10", "IR-2", "IR-4"],
            "reconstructed_source": [],
            "bridge": ["EIB-DF10-CANDIDATE"],
        },
        "claim_scope": "An explicit finite typed model refutes uniform sufficiency over the minimal unconstrained bridge signature. It does not establish source-level TH-3 until all declared dependencies are mapped and accepted.",
        "symbol": "CREIB.EIB_TH3b_relative_non_sufficiency",
        "path": "formal/CREIB/Pilot/TH3Countermodel.lean",
        "sha256": "38a68f131389ecca67d5a798262a663edc7c6dcedb7e58b6695ad12fa30679e5",
        "closed_proposition": True,
        "explicit_negative_required_for_countermodel": True,
        "replay_status": "verified",
        "replay_command": "cd formal && lake build",
        "expected_axioms": [],
    },
}

EXPECTED_FORMAL_PACKAGE = {
    "formal/CREIB.lean": "22081eed25468edd266f61a2f291fd761f1ec6c4b442aabfe012abb77d2e2082",
    "formal/CREIB/Audit/Axioms.lean": "258fd255bf7704291d4de03913d57f0ff15589cc6437c69a3def00740746eecb",
    "formal/CREIB/Audit/DeclarationBindings.lean": "165c6e90803670172d3e67b008f78665d2da66296607801e8f4d7c02ba3014dd",
    "formal/CREIB/Bridge/DF10Candidate.lean": "14b4fe0ac3a9f1d707f1ac942b85a67a41915d4977211325d6465169c8ca2128",
    "formal/CREIB/Core/Model.lean": "7a56c781e785f8ddba704f07dc785c9677179646f1250329ead39fbb0d35dd0a",
    "formal/CREIB/Pilot/TH3.lean": "ef9096ff0fe7ef133757ccb57ba3fc52a41638b339539af1737584936c3cb11a",
    "formal/CREIB/Pilot/TH3Countermodel.lean": "38a68f131389ecca67d5a798262a663edc7c6dcedb7e58b6695ad12fa30679e5",
    "formal/lake-manifest.json": "835bdc7555981c3189d81c1a1756f21c780c8fdd60dc07ed96aaed80ba4c54f8",
    "formal/lakefile.toml": "06dc9683188f3d1b967431c49f8999bb96e6ba901f75c34bb75267ad32594181",
    "formal/lean-toolchain": "3aac669c7a910ec2389f4e4f921b605adf6ebf2d1e0c9b9cd0be4d33f3f5db71",
}

EXPECTED_AXIOM_FREE_DECLARATIONS = [
    "CREIB.EIB_DF10_fold_unfold",
    "CREIB.EIB_TH3a_unfold",
    "CREIB.TH3Countermodel.concreteWitness",
    "CREIB.EIB_TH3b_countermodel_exists",
    "CREIB.EIB_TH3b_relative_non_sufficiency",
]


def _exact_keys(value: dict[str, Any], keys: set[str], where: str) -> None:
    if set(value) != keys:
        raise RecordError(
            f"{where} keys differ; missing={sorted(keys - set(value))}, extra={sorted(set(value) - keys)}"
        )


def _safe_repository_file(root: Path, relative: str) -> Path:
    root = root.resolve(strict=True)
    candidate = root
    for part in Path(relative).parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise PolicyViolation(f"symlinked evidence path is forbidden: {relative}")
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, ValueError) as exc:
        raise PolicyViolation(f"evidence path escapes or is missing: {relative}") from exc
    if not resolved.is_file():
        raise PolicyViolation(f"evidence path is not a regular file: {relative}")
    return resolved


def _enforce_pilot_policy(manifest: dict[str, Any], anchors: dict[str, dict[str, Any]]) -> None:
    for key, expected in EXPECTED_MANIFEST.items():
        if manifest[key] != expected:
            raise AuthorityMismatch(f"CR-1.0 manifest mismatch for {key}")
    if set(anchors) != set(EXPECTED_ANCHORS):
        raise AnchorMismatch(
            f"pilot anchor set differs; missing={sorted(set(EXPECTED_ANCHORS) - set(anchors))}, "
            f"extra={sorted(set(anchors) - set(EXPECTED_ANCHORS))}"
        )
    for authoritative_id, expected in EXPECTED_ANCHORS.items():
        if authoritative_id not in anchors:
            raise AnchorMismatch(f"required pilot anchor is missing: {authoritative_id}")
        anchor = anchors[authoritative_id]
        locator = anchor["locator"]
        snapshot = anchor["transcription"]["literal_word_snapshot"]
        reading = anchor["transcription"]["reviewed_reading"]
        declared = anchor["dependencies"]["source_declared"]
        assertion = anchor["source_status"]["assertions"][0]
        checks = {
            "title_raw": anchor["title_raw"],
            "section_raw": locator["section_raw"],
            "physical_pdf_page": locator["physical_pdf_page"],
            "printed_footer_page": locator["printed_footer_page"],
            "tight_bbox_millipoints": locator["tight_bbox_millipoints"],
            "word_count": snapshot["word_count"],
            "word_snapshot_sha256": snapshot["sha256"],
            "reviewed_sha256": reading["sha256"],
            "source_dependencies": declared["exact_ids"],
            "declared_exhaustive": declared["declared_exhaustive"],
            "source_status_raw": anchor["source_status"]["raw"],
            "source_scope": assertion["scope_raw"],
            "source_tags": anchor["source_status"]["source_tags"],
            "regions": locator["regions"],
        }
        for key, actual in checks.items():
            if actual != expected[key]:
                raise AnchorMismatch(f"{authoritative_id} pilot policy mismatch for {key}")


def _validate_bridge_graph(declarations: dict[str, dict[str, Any]]) -> None:
    for declaration_id, declaration in declarations.items():
        for dependency in declaration["dependencies"]["bridge"]:
            if dependency not in declarations:
                raise PolicyViolation(f"unresolved bridge dependency: {declaration_id} -> {dependency}")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(declaration_id: str) -> None:
        if declaration_id in visiting:
            raise PolicyViolation(f"bridge dependency cycle includes {declaration_id}")
        if declaration_id in visited:
            return
        visiting.add(declaration_id)
        for dependency in declarations[declaration_id]["dependencies"]["bridge"]:
            visit(dependency)
        visiting.remove(declaration_id)
        visited.add(declaration_id)

    for declaration_id in declarations:
        visit(declaration_id)


def _formal_manifest_bytes() -> bytes:
    return "".join(
        f"{digest}  {path}\n" for path, digest in EXPECTED_FORMAL_PACKAGE.items()
    ).encode("utf-8")


def _verify_formal_package(root: Path) -> dict[str, bytes]:
    try:
        manifest_path = _safe_repository_file(root, "formal/formal-package.sha256")
        with manifest_path.open("rb") as handle:
            manifest_bytes = handle.read(20_001)
    except (OSError, PolicyViolation) as exc:
        raise FormalReplayMismatch("formal package manifest is unavailable or unsafe") from exc
    if manifest_bytes != _formal_manifest_bytes():
        raise FormalReplayMismatch("formal package manifest differs from the reviewed pilot")

    formal_directory = root / "formal"
    if formal_directory.is_symlink() or not formal_directory.is_dir():
        raise FormalReplayMismatch("formal package directory must be a real repository directory")
    actual_inputs = {
        path.relative_to(root).as_posix()
        for path in formal_directory.rglob("*.lean")
        if ".lake" not in path.parts
    }
    actual_inputs.update(
        {"formal/lake-manifest.json", "formal/lakefile.toml", "formal/lean-toolchain"}
    )
    if actual_inputs != set(EXPECTED_FORMAL_PACKAGE):
        raise FormalReplayMismatch(
            f"formal package input set differs; missing={sorted(set(EXPECTED_FORMAL_PACKAGE) - actual_inputs)}, "
            f"extra={sorted(actual_inputs - set(EXPECTED_FORMAL_PACKAGE))}"
        )
    verified_inputs: dict[str, bytes] = {}
    for relative, expected_digest in EXPECTED_FORMAL_PACKAGE.items():
        try:
            path = _safe_repository_file(root, relative)
            with path.open("rb") as handle:
                raw = handle.read(2_000_001)
        except (OSError, PolicyViolation) as exc:
            raise FormalReplayMismatch(f"formal package input is unavailable or unsafe: {relative}") from exc
        if len(raw) > 2_000_000 or hashlib.sha256(raw).hexdigest() != expected_digest:
            raise FormalReplayMismatch(f"formal package hash mismatch: {relative}")
        verified_inputs[relative] = raw
    return verified_inputs


def verify_lean(repo_root: Path) -> None:
    """Compile and replay the exact pinned Lean package and its axiom audit."""
    try:
        root = repo_root.resolve(strict=True)
    except OSError as exc:
        raise RecordError(f"repository root is unavailable: {repo_root}") from exc
    verified_inputs = _verify_formal_package(root)
    replay_environment = os.environ.copy()
    for variable in ("LAKE_HOME", "LEAN_PATH", "LEAN_SRC_PATH"):
        replay_environment.pop(variable, None)

    with tempfile.TemporaryDirectory(prefix="cr-eib-formal-replay-") as directory:
        formal_directory = Path(directory)
        for repository_path, raw in verified_inputs.items():
            target = formal_directory / Path(repository_path).relative_to("formal")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)

        version = _run(
            ["lake", "env", "lean", "--version"],
            cwd=formal_directory,
            env=replay_environment,
            error_cls=FormalReplayMismatch,
        )
        _verify_lean_version(version.stdout)

        _run(
            ["lake", "build"],
            cwd=formal_directory,
            env=replay_environment,
            error_cls=FormalReplayMismatch,
        )
        audit = _run(
            ["lake", "env", "lean", "CREIB/Audit/Axioms.lean"],
            cwd=formal_directory,
            env=replay_environment,
            error_cls=FormalReplayMismatch,
        )
        audit_text = (audit.stdout + audit.stderr).decode("utf-8", errors="replace")
        expected_lines = {
            f"'{declaration}' does not depend on any axioms"
            for declaration in EXPECTED_AXIOM_FREE_DECLARATIONS
        }
        actual_lines = {
            line.strip() for line in audit_text.splitlines() if "depend" in line and "axiom" in line
        }
        if actual_lines != expected_lines:
            raise FormalReplayMismatch("Lean axiom audit output differs from the empty expected set")


def _verify_lean_version(output: bytes) -> None:
    text = output.decode("utf-8", errors="replace")
    match = re.fullmatch(
        r"Lean \(version (4\.33\.1), [A-Za-z0-9_.-]+, commit ([0-9a-f]{40}), Release\)\r?\n?",
        text,
    )
    if not match or match.group(2) != "819816b2e0a3bf405af45ae5c7af2491d8f5bee6":
        raise FormalReplayMismatch("Lean version or compiler commit differs from the pinned replay")


def verify_bundle(
    repo_root: Path,
    *,
    with_records: bool = False,
) -> dict[str, Any] | tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    """Validate all tracked pilot records without changing any input bytes."""
    try:
        root = repo_root.resolve(strict=True)
    except OSError as exc:
        raise RecordError(f"repository root is unavailable: {repo_root}") from exc
    manifest_path = _safe_repository_file(root, "authority/source_manifest.json")
    anchors_path = _safe_repository_file(root, "authority/source_anchors.json")
    checksum_path = _safe_repository_file(root, "authority/authority.pdf.sha256")
    manifest = validate_manifest(load_strict(manifest_path))
    with checksum_path.open("rb") as handle:
        checksum_bytes = handle.read(513)
    expected_checksum = f"{manifest['sha256']}  {manifest['supplied_filename']}\n".encode("utf-8")
    if checksum_bytes != expected_checksum:
        raise AuthorityMismatch("authority.pdf.sha256 disagrees with the source manifest")
    anchor_set = load_strict(anchors_path)
    if type(anchor_set) is not dict:
        raise RecordError("source_anchors.json must contain an object")
    _exact_keys(anchor_set, {"schema_version", "anchors"}, "anchor set")
    if anchor_set["schema_version"] != "cr-eib.source-anchor-set.v1":
        raise RecordError("unknown source-anchor-set schema version")
    if type(anchor_set["anchors"]) is not list:
        raise RecordError("anchor set anchors must be an array")

    anchors_by_digest: dict[str, dict[str, Any]] = {}
    anchors_by_id: dict[str, dict[str, Any]] = {}
    anchor_digests_by_id: dict[str, str] = {}
    for raw_anchor in anchor_set["anchors"]:
        payload = validate_anchor(raw_anchor, manifest)
        digest = raw_anchor["anchor_digest"]
        authoritative_id = payload["authoritative_id"]
        if digest in anchors_by_digest or authoritative_id in anchors_by_id:
            raise RecordError("duplicate anchor digest or authoritative identifier")
        anchors_by_digest[digest] = payload
        anchors_by_id[authoritative_id] = payload
        anchor_digests_by_id[authoritative_id] = digest

    _enforce_pilot_policy(manifest, anchors_by_id)
    if anchor_digests_by_id != EXPECTED_ANCHOR_DIGESTS:
        raise AnchorMismatch("pilot anchor identity map differs from the reviewed authority slice")

    for anchor in anchors_by_id.values():
        reading = anchor["transcription"]["reviewed_reading"]
        path = _safe_repository_file(root, reading["path"])
        with path.open("rb") as handle:
            raw = handle.read(1_000_001)
        if len(raw) > 1_000_000:
            raise AnchorMismatch(f"reviewed transcription exceeds the size limit: {reading['path']}")
        if hashlib.sha256(raw).hexdigest() != reading["sha256"]:
            raise AnchorMismatch(f"reviewed transcription hash mismatch: {reading['path']}")
        if not raw.endswith(b"\n") or b"\r" in raw:
            raise AnchorMismatch(f"reviewed transcription newline policy mismatch: {reading['path']}")
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise AnchorMismatch(f"reviewed transcription is not UTF-8: {reading['path']}") from exc

    declaration_directory = root / "bridge" / "declarations"
    if declaration_directory.is_symlink() or not declaration_directory.is_dir():
        raise PolicyViolation("bridge declaration directory must be a real repository directory")
    try:
        declaration_directory.resolve(strict=True).relative_to(root)
    except (OSError, ValueError) as exc:
        raise PolicyViolation("bridge declaration directory escapes the repository") from exc
    declaration_paths = sorted(declaration_directory.glob("*.json"))
    if not declaration_paths:
        raise PolicyViolation("no bridge declarations were found")
    declarations: dict[str, dict[str, Any]] = {}
    for declaration_path in declaration_paths:
        if declaration_path.is_symlink():
            raise PolicyViolation(f"symlinked declaration is forbidden: {declaration_path}")
        declaration = validate_declaration(load_strict(declaration_path), anchors_by_digest)
        declaration_id = declaration["declaration_id"]
        if declaration_id in declarations:
            raise RecordError(f"duplicate bridge declaration: {declaration_id}")
        declarations[declaration_id] = declaration
    if set(declarations) != EXPECTED_DECLARATIONS:
        raise PolicyViolation(
            f"pilot declaration set differs; missing={sorted(EXPECTED_DECLARATIONS - set(declarations))}, "
            f"extra={sorted(set(declarations) - EXPECTED_DECLARATIONS)}"
        )
    for declaration_id, expected in EXPECTED_DECLARATION_POLICY.items():
        declaration = declarations[declaration_id]
        typed_path = _safe_repository_file(root, declaration["typed_body"]["path"])
        with typed_path.open("rb") as handle:
            typed_bytes = handle.read(2_000_001)
        if len(typed_bytes) > 2_000_000:
            raise PolicyViolation(f"typed body exceeds the size limit: {declaration_id}")
        if hashlib.sha256(typed_bytes).hexdigest() != declaration["typed_body"]["sha256"]:
            raise PolicyViolation(f"typed-body hash mismatch: {declaration_id}")
        actual = {
            "authoritative_id": declaration["authoritative_id"],
            "source_anchor_digest": declaration["source_anchor_digest"],
            "mapping_status": declaration["mapping_status"],
            "proposed_inferential_status": declaration["proposed_inferential_status"],
            "parameters": declaration["parameters"],
            "opaque_ports": declaration["opaque_ports"],
            "dependencies": declaration["dependencies"],
            "claim_scope": declaration["claim_scope"],
            "symbol": declaration["typed_body"]["symbol"],
            "path": declaration["typed_body"]["path"],
            "sha256": declaration["typed_body"]["sha256"],
            "closed_proposition": declaration["typed_body"]["closed_proposition"],
            "explicit_negative_required_for_countermodel": declaration["evidence_policy"][
                "explicit_negative_required_for_countermodel"
            ],
            "replay_status": declaration["replay"]["status"],
            "replay_command": declaration["replay"]["command"],
            "expected_axioms": declaration["replay"]["expected_axioms"],
        }
        if actual != expected:
            raise PolicyViolation(f"pilot declaration metadata drift: {declaration_id}")

    _validate_bridge_graph(declarations)
    _verify_formal_package(root)

    report = {
        "status": "PARTIAL",
        "record_status": "PASS",
        "authority": manifest["document_id"],
        "authority_pdf_checked": False,
        "formal_package_status": "PASS",
        "formal_replay_checked": False,
        "anchors_valid": sorted(anchors_by_id),
        "declarations_valid": sorted(declarations),
        "scope": "record integrity and relative pilot wiring only",
    }
    if with_records:
        return report, manifest, list(anchors_by_id.values())
    return report


def _run(
    command: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    error_cls: type[AnchorMismatch | FormalReplayMismatch] = AnchorMismatch,
    timeout_seconds: int = 300,
    output_limit: int = 2_000_000,
) -> subprocess.CompletedProcess[bytes]:
    if env is None:
        env = os.environ.copy()
    env["LANG"] = "C"
    env["LC_ALL"] = "C"
    try:
        result = subprocess.run(
            command,
            check=True,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
        )
        if len(result.stdout) > output_limit or len(result.stderr) > output_limit:
            raise error_cls(f"verification tool output exceeds limit: {command[0]}")
        return result
    except FileNotFoundError as exc:
        raise error_cls(f"required verification tool is unavailable: {command[0]}") from exc
    except OSError as exc:
        raise error_cls(f"verification tool could not execute: {command[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise error_cls(f"verification tool timed out: {command[0]}") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout).decode("utf-8", errors="replace").strip()
        raise error_cls(f"verification tool failed: {command[0]}: {detail}") from exc


_DECIMAL_TOKEN = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?\Z")


def _decimal(token: str, where: str) -> Decimal:
    if not _DECIMAL_TOKEN.fullmatch(token):
        raise AnchorMismatch(f"{where} is not a plain finite decimal")
    try:
        value = Decimal(token)
    except InvalidOperation as exc:
        raise AnchorMismatch(f"{where} is not a valid decimal") from exc
    if not value.is_finite():
        raise AnchorMismatch(f"{where} is non-finite")
    return value


def _exact_millipoints(token: str, where: str) -> int:
    scaled = _decimal(token, where) * 1000
    if scaled != scaled.to_integral_value():
        raise AnchorMismatch(f"{where} is not an exact millipoint value")
    return int(scaled)


def _rounded_millipoints(token: str, where: str) -> int:
    scaled = _decimal(token, where) * 1000
    return int(scaled.quantize(Decimal("1"), rounding=ROUND_HALF_EVEN))


def _parse_bbox_pages(xml_bytes: bytes) -> list[ET.Element]:
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise AnchorMismatch(f"pdftotext returned malformed bbox XML: {exc}") from exc
    return [element for element in root.iter() if element.tag.rsplit("}", 1)[-1] == "page"]


def _page_words(page: ET.Element, expected_size: list[int]) -> list[list[Any]]:
    try:
        width = _exact_millipoints(page.attrib["width"], "pdftotext page width")
        height = _exact_millipoints(page.attrib["height"], "pdftotext page height")
    except KeyError as exc:
        raise AnchorMismatch("pdftotext page lacks dimensions") from exc
    if [width, height] != expected_size:
        raise AuthorityMismatch("pdftotext active-span page geometry mismatch")

    words: list[list[Any]] = []
    for element in page.iter():
        if element.tag.rsplit("}", 1)[-1] != "word":
            continue
        try:
            point_values = [
                _decimal(element.attrib[name], f"pdftotext word {name}")
                for name in ("xMin", "yMin", "xMax", "yMax")
            ]
            coordinates = [
                _rounded_millipoints(element.attrib[name], f"pdftotext word {name}")
                for name in ("xMin", "yMin", "xMax", "yMax")
            ]
        except KeyError as exc:
            raise AnchorMismatch("pdftotext word lacks valid coordinates") from exc
        x_min, y_min, x_max, y_max = point_values
        if not (
            Decimal(0) <= x_min <= x_max <= Decimal(width) / 1000
            and Decimal(0) <= y_min <= y_max <= Decimal(height) / 1000
        ):
            raise AnchorMismatch("pdftotext word coordinates are inverted or out of page bounds")
        words.append([element.text or "", *coordinates])
    return words


def _select_word_centers(words: list[list[Any]], bbox: list[int]) -> list[list[Any]]:
    selected: list[list[Any]] = []
    for word in words:
        coordinates = word[1:]
        center_x = (coordinates[0] + coordinates[2]) // 2
        center_y = (coordinates[1] + coordinates[3]) // 2
        if bbox[0] <= center_x <= bbox[2] and bbox[1] <= center_y <= bbox[3]:
            selected.append(word)
    return selected


def _verify_active_span_geometry(detail: str, manifest: dict[str, Any]) -> None:
    physical_start, physical_end = manifest["active_span"]["physical_pdf_pages"]
    expected_pages = set(range(physical_start, physical_end + 1))
    number = r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?"
    size_re = re.compile(
        rf"^Page\s+([1-9][0-9]*)\s+size:\s+({number})\s+x\s+({number})\s+pts"
        r"(?:\s+\([^)]*\))?\s*$"
    )
    rotation_re = re.compile(r"^Page\s+([1-9][0-9]*)\s+rot:\s+(-?[0-9]+)\s*$")
    box_re = re.compile(
        rf"^Page\s+([1-9][0-9]*)\s+"
        rf"(MediaBox|CropBox|BleedBox|TrimBox|ArtBox):\s+"
        rf"({number})\s+({number})\s+({number})\s+({number})\s*$"
    )
    sizes: dict[int, list[int]] = {}
    rotations: dict[int, int] = {}
    boxes: dict[tuple[int, str], list[int]] = {}
    for line in detail.splitlines():
        if match := size_re.fullmatch(line):
            page = int(match.group(1))
            if page in sizes:
                raise AuthorityMismatch(f"duplicate active-span size for physical page {page}")
            sizes[page] = [
                _exact_millipoints(match.group(2), "pdfinfo page width"),
                _exact_millipoints(match.group(3), "pdfinfo page height"),
            ]
        elif match := rotation_re.fullmatch(line):
            page = int(match.group(1))
            if page in rotations:
                raise AuthorityMismatch(f"duplicate active-span rotation for physical page {page}")
            rotations[page] = int(match.group(2))
        elif match := box_re.fullmatch(line):
            page, name = int(match.group(1)), match.group(2)
            key = (page, name)
            if key in boxes:
                raise AuthorityMismatch(f"duplicate {name} for physical page {page}")
            boxes[key] = [
                _exact_millipoints(match.group(index), f"pdfinfo {name} coordinate")
                for index in range(3, 7)
            ]
        elif re.match(r"^Page\s+[0-9]+\s+(?:size|rot|\w+Box):", line):
            raise AuthorityMismatch(f"malformed active-span geometry line: {line[:80]}")

    if set(sizes) != expected_pages or set(rotations) != expected_pages:
        raise AuthorityMismatch("active-span size or rotation page set differs")
    expected_size = manifest["page_size_millipoints"]
    expected_box = [0, 0, *expected_size]
    box_names = ("MediaBox", "CropBox", "BleedBox", "TrimBox", "ArtBox")
    expected_box_keys = {(page, name) for page in expected_pages for name in box_names}
    if set(boxes) != expected_box_keys:
        raise AuthorityMismatch("active-span page-box set differs")
    for page in expected_pages:
        if sizes[page] != expected_size:
            raise AuthorityMismatch(f"active-span size mismatch for physical page {page}")
        if rotations[page] != 0:
            raise AuthorityMismatch(f"active-span rotation mismatch for physical page {page}")
        for name in box_names:
            if boxes[(page, name)] != expected_box:
                raise AuthorityMismatch(f"active-span {name} mismatch for physical page {page}")


def _verify_bbox_span(
    xml_bytes: bytes,
    manifest: dict[str, Any],
    anchors: list[dict[str, Any]],
) -> None:
    physical_start, physical_end = manifest["active_span"]["physical_pdf_pages"]
    printed_start, printed_end = manifest["active_span"]["printed_folios"]
    page_count = physical_end - physical_start + 1
    if printed_end - printed_start + 1 != page_count:
        raise AuthorityMismatch("active-span physical pages and printed folios do not align")
    pages = _parse_bbox_pages(xml_bytes)
    if len(pages) != page_count:
        raise AuthorityMismatch("pdftotext active-span page count mismatch")
    words_by_physical_page: dict[int, list[list[Any]]] = {}
    footer_bbox = [290_000, 760_000, 322_000, 778_000]
    for offset, page_element in enumerate(pages):
        physical_page = physical_start + offset
        words = _page_words(page_element, manifest["page_size_millipoints"])
        words_by_physical_page[physical_page] = words
        footer_words = [
            word
            for word in words
            if footer_bbox[0] <= word[1]
            and footer_bbox[1] <= word[2]
            and word[3] <= footer_bbox[2]
            and word[4] <= footer_bbox[3]
        ]
        expected_folio = str(printed_start + offset)
        if len(footer_words) != 1 or footer_words[0][0] != expected_folio:
            raise AuthorityMismatch(
                f"printed folio mismatch for physical page {physical_page}: expected {expected_folio}"
            )

    for anchor in anchors:
        locator = anchor["locator"]
        physical_page = locator["physical_pdf_page"]
        expected_folio = printed_start + physical_page - physical_start
        if locator["printed_footer_page"] != expected_folio:
            raise AnchorMismatch(f"anchor folio mapping mismatch for {anchor['authoritative_id']}")
        snapshot = anchor["transcription"]["literal_word_snapshot"]
        words = _select_word_centers(
            words_by_physical_page[physical_page], locator["tight_bbox_millipoints"]
        )
        if len(words) != snapshot["word_count"]:
            raise AnchorMismatch(f"word-count mismatch for {anchor['authoritative_id']}")
        framed = b"CR-EIB/pdftotext-word-snapshot/v1\0" + canonical_bytes(words)
        actual_digest = hashlib.sha256(framed).hexdigest()
        if actual_digest != snapshot["sha256"]:
            raise AnchorMismatch(f"literal word-snapshot mismatch for {anchor['authoritative_id']}")


def _inspect_verified_pdf(
    verified_bytes: bytes,
    manifest: dict[str, Any],
    anchors: list[dict[str, Any]],
) -> None:
    with tempfile.TemporaryDirectory(prefix="cr-eib-verified-") as directory:
        pdf_path = Path(directory) / "authority.pdf"
        pdf_path.write_bytes(verified_bytes)
        info = _run(["pdfinfo", str(pdf_path)]).stdout.decode("utf-8", errors="replace")
        pages_match = re.search(r"^Pages:\s+(\d+)\s*$", info, re.MULTILINE)
        size_match = re.search(r"^Page size:\s+([0-9.]+) x ([0-9.]+) pts", info, re.MULTILINE)
        if not pages_match or int(pages_match.group(1)) != manifest["page_count"]:
            raise AuthorityMismatch("verified PDF page count mismatch")
        if not size_match:
            raise AuthorityMismatch("verified PDF page geometry is unavailable")
        page_size = [round(float(size_match.group(1)) * 1000), round(float(size_match.group(2)) * 1000)]
        if page_size != manifest["page_size_millipoints"]:
            raise AuthorityMismatch("verified PDF page geometry mismatch")

        pdfinfo_version = _run(["pdfinfo", "-v"])
        pdfinfo_version_text = (pdfinfo_version.stderr + pdfinfo_version.stdout).decode(
            "utf-8", errors="replace"
        )
        pdfinfo_version_match = re.search(r"pdfinfo version ([0-9.]+)", pdfinfo_version_text)
        if not pdfinfo_version_match or pdfinfo_version_match.group(1) != "26.05.0":
            raise AuthorityMismatch("pdfinfo version differs from the reviewed anchor provenance")

        physical_start, physical_end = manifest["active_span"]["physical_pdf_pages"]
        detail = _run(
            [
                "pdfinfo",
                "-f",
                str(physical_start),
                "-l",
                str(physical_end),
                "-box",
                str(pdf_path),
            ]
        ).stdout.decode("utf-8", errors="replace")
        _verify_active_span_geometry(detail, manifest)

        version_result = _run(["pdftotext", "-v"])
        version_text = (version_result.stderr + version_result.stdout).decode("utf-8", errors="replace")
        version_match = re.search(r"pdftotext version ([0-9.]+)", version_text)
        if not version_match:
            raise AnchorMismatch("could not determine pdftotext version")
        actual_version = version_match.group(1)

        for anchor in anchors:
            snapshot = anchor["transcription"]["literal_word_snapshot"]
            if actual_version != snapshot["extractor_version"]:
                raise AnchorMismatch(
                    f"pdftotext version mismatch for {anchor['authoritative_id']}: "
                    f"expected {snapshot['extractor_version']}, got {actual_version}"
                )
        span_xml = _run(
            [
                "pdftotext",
                "-f",
                str(physical_start),
                "-l",
                str(physical_end),
                "-bbox",
                str(pdf_path),
                "-",
            ]
        ).stdout
        _verify_bbox_span(span_xml, manifest, anchors)


def verify_pdf(
    pdf_path: Path,
    manifest: dict[str, Any],
    anchors: list[dict[str, Any]],
    *,
    inspector: Callable[[bytes, dict[str, Any], list[dict[str, Any]]], None] = _inspect_verified_pdf,
) -> None:
    """Hash first, then parse the exact verified bytes through a private copy."""
    try:
        descriptor = os.open(
            pdf_path,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0),
        )
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            os.close(descriptor)
            raise AuthorityMismatch("authority PDF must be a regular file")
        with os.fdopen(descriptor, "rb") as handle:
            verified_bytes = handle.read(manifest["byte_length"] + 1)
    except OSError as exc:
        raise AuthorityMismatch(f"cannot read authority PDF: {exc}") from exc
    if len(verified_bytes) != manifest["byte_length"]:
        raise AuthorityMismatch("authority PDF byte length mismatch")
    actual_digest = hashlib.sha256(verified_bytes).hexdigest()
    if actual_digest != manifest["sha256"]:
        raise AuthorityMismatch("authority PDF SHA-256 mismatch")
    inspector(verified_bytes, manifest, anchors)
