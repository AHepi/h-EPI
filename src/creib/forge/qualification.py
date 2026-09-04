"""Executable, claim-limited qualification for the synthetic HRC-1 fixture.

The fixture contains planted defects and declared benign controls.  This
module can freeze an input before controller disclosure and can replay a
candidate's declared exposure IDs against that fixed controller surface.  A
matching result is only an engineering result relative to HRC-1; it is not a
semantic verdict, a fidelity judgment, or evidence of truth.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path, PurePosixPath
import re
import unicodedata
from typing import Any, Mapping, Sequence

from creib.canonical import canonical_bytes, domain_digest
from creib.errors import PolicyViolation, RecordError
from creib.strict_json import loads_strict

from .translation import load_translation_inventory, validate_translation_snapshot


EXPOSURE_REPORT_SCHEMA = "creib.translation-qualification-exposure-report.v1"
FREEZE_SCHEMA = "creib.translation-qualification-freeze.v1"
RESULT_SCHEMA = "creib.translation-qualification-result.v1"

EXPOSURE_REPORT_ID_DOMAIN = f"{EXPOSURE_REPORT_SCHEMA}.report-id"
FREEZE_ID_DOMAIN = f"{FREEZE_SCHEMA}.freeze-id"
RESULT_ID_DOMAIN = f"{RESULT_SCHEMA}.qualification-id"

QUALIFICATION_SCOPE = "HRC_1_DECLARED_CONTROLLER_EXPOSURES_ONLY"
QUALIFICATION_LIMIT = (
    "This result compares declared exposure IDs with the frozen HRC-1 "
    "controller. It cannot confirm source meaning, translation fidelity, or "
    "the truth of any proposition."
)

_LEGACY_FIXTURE_SUCCESS_LABEL = "ALL_DECLARED_EXPOSURES_REPRODUCED"
ALL_REPRODUCED = "ALL_DECLARED_EXPOSURE_TOKENS_MATCH_CONTROLLER"
MISSED = "DECLARED_EXPOSURES_MISSED"
FALSE_POSITIVES = "UNDECLARED_EXPOSURES_REPORTED"
MISMATCH = "DECLARED_EXPOSURE_MISMATCH"

REPORT_FROZEN = "DECLARED_EXPOSURE_REPORT_FROZEN_AWAITING_CONTROLLER_REPLAY"
SNAPSHOT_FROZEN = "CANDIDATE_FROZEN_AWAITING_DECLARED_EXPOSURES"

MANIFEST_REL = "forge/translation/qualification/HRC-1.manifest.json"
AUTHORITY_REL = "forge/translation/qualification/HRC-1.authority.txt"
BLIND_PACKET_REL = "forge/translation/qualification/HRC-1.blind-packet.json"
CHARTER_REL = "forge/translation/qualification/HRC-1.translation-charter.json"
COMMITMENT_REL = (
    "forge/translation/qualification/HRC-1.construction-key.commitment.json"
)
KEY_REL = "forge/translation/qualification/controller/HRC-1.construction-key.json"
OBLIGATIONS_REL = (
    "forge/translation/qualification/controller/HRC-1.source-obligations.json"
)
MUTATIONS_REL = (
    "forge/translation/qualification/controller/HRC-1.mutation-ledger.json"
)
CONTROLS_REL = (
    "forge/translation/qualification/controller/HRC-1.benign-controls.json"
)

# HRC-1 is a built-in qualification instrument, not a caller-defined fixture.
# This out-of-band binding prevents a coherently rewritten repository tree from
# minting a different instrument while retaining the trusted HRC-1 name.
HRC_1_MANIFEST_SHA256 = (
    "4c71f2038b3e9b6eab35f2f7fa946ff810dbbba0f1801f537dbe29b7d0c8b9cd"
)

_FIXTURE_PATHS = frozenset(
    {
        AUTHORITY_REL,
        BLIND_PACKET_REL,
        CHARTER_REL,
        COMMITMENT_REL,
        KEY_REL,
        OBLIGATIONS_REL,
        MUTATIONS_REL,
        CONTROLS_REL,
    }
)
_BLIND_PATHS = (AUTHORITY_REL, COMMITMENT_REL, CHARTER_REL)

_HEX = re.compile(r"^[0-9a-f]{64}$")
_DOMAIN_SHA = re.compile(r"^sha256:[0-9a-f]{64}$")
_REPORT_ID = re.compile(r"^QER:[0-9a-f]{64}$")
_FREEZE_ID = re.compile(r"^QFZ:[0-9a-f]{64}$")
_CASE_ID = re.compile(r"^HRC-[MC]-[A-Z0-9-]+$")
_EXPOSURE_ID = re.compile(r"^[A-Z][A-Z0-9_]*$")

_REPORT_KEYS = {
    "schema_version",
    "report_id",
    "authority_id",
    "source_authority_sha256",
    "construction_key_commitment_sha256",
    "candidate_snapshot_freeze_id",
    "observations",
    "automatic_semantic_effect",
    "semantic_verdict",
    "translation_fidelity_verdict",
}
_OBSERVATION_KEYS = {"case_id", "observed_exposure_ids"}
_FREEZE_KEYS = {
    "schema_version",
    "freeze_id",
    "authority_id",
    "input_kind",
    "content_id",
    "artifact_sha256",
    "artifact_byte_length",
    "record_closure_sha256",
    "qualification_status",
    "automatic_semantic_effect",
    "semantic_verdict",
    "translation_fidelity_verdict",
}


def _object(value: Any, where: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise RecordError(f"{where} must be an object")
    return value


def _array(value: Any, where: str) -> list[Any]:
    if type(value) is not list:
        raise RecordError(f"{where} must be an array")
    return value


def _text(value: Any, where: str) -> str:
    if type(value) is not str or not value.strip():
        raise RecordError(f"{where} must be a non-empty string")
    if unicodedata.normalize("NFC", value) != value:
        raise RecordError(f"{where} must be NFC-normalized")
    if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
        raise RecordError(f"{where} contains a Unicode surrogate")
    return value


def _exact_keys(value: Mapping[str, Any], expected: set[str], where: str) -> None:
    actual = set(value)
    if actual != expected:
        raise RecordError(
            f"{where} has missing keys {sorted(expected - actual)} and "
            f"extra keys {sorted(actual - expected)}"
        )


def _plain_sha(value: Any, where: str) -> str:
    checked = _text(value, where)
    if not _HEX.fullmatch(checked):
        raise RecordError(f"{where} must be a lowercase SHA-256 hex digest")
    return checked


def _read_bytes(path: Path, where: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise RecordError(f"cannot read {where}: {exc}") from exc


def _load_object_bytes(raw: bytes, where: str) -> dict[str, Any]:
    """Parse one already-captured byte string as a strict JSON object."""

    try:
        source = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RecordError(f"{where} is not UTF-8") from exc
    return _object(loads_strict(source), where)


def _without(value: Mapping[str, Any], key: str) -> dict[str, Any]:
    return {name: item for name, item in value.items() if name != key}


def _content_id(
    value: Mapping[str, Any], *, id_field: str, prefix: str, domain: str
) -> str:
    digest = domain_digest(domain, _without(value, id_field))
    return f"{prefix}:{digest.removeprefix('sha256:')}"


def _verify_no_semantic_promotion(record: Mapping[str, Any], where: str) -> None:
    if record.get("automatic_semantic_effect") != "NONE":
        raise PolicyViolation(f"{where} automatic_semantic_effect must be NONE")
    if record.get("semantic_verdict") is not None:
        raise PolicyViolation(f"{where} semantic_verdict must be null")
    if record.get("translation_fidelity_verdict") is not None:
        raise PolicyViolation(f"{where} translation_fidelity_verdict must be null")


def compute_exposure_report_id(report: Mapping[str, Any]) -> str:
    """Return the deterministic ID of a declared exposure report."""

    return _content_id(
        report,
        id_field="report_id",
        prefix="QER",
        domain=EXPOSURE_REPORT_ID_DOMAIN,
    )


def validate_exposure_report(report: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a report without consulting any withheld controller record."""

    checked = _object(report, "declared exposure report")
    canonical_bytes(checked)
    _exact_keys(checked, _REPORT_KEYS, "declared exposure report")
    if checked["schema_version"] != EXPOSURE_REPORT_SCHEMA:
        raise RecordError("declared exposure report has the wrong schema_version")
    report_id = _text(checked["report_id"], "report_id")
    if not _REPORT_ID.fullmatch(report_id):
        raise RecordError("report_id must use the QER: content-addressed namespace")
    if report_id != compute_exposure_report_id(checked):
        raise RecordError("report_id does not match the canonical report content")
    if checked["authority_id"] != "HRC-1":
        raise RecordError("declared exposure report authority_id must be HRC-1")
    _plain_sha(checked["source_authority_sha256"], "source_authority_sha256")
    _plain_sha(
        checked["construction_key_commitment_sha256"],
        "construction_key_commitment_sha256",
    )
    snapshot_freeze_id = checked["candidate_snapshot_freeze_id"]
    if snapshot_freeze_id is not None:
        if type(snapshot_freeze_id) is not str or not _FREEZE_ID.fullmatch(
            snapshot_freeze_id
        ):
            raise RecordError(
                "candidate_snapshot_freeze_id must be null or a QFZ: identifier"
            )

    observations = _array(checked["observations"], "observations")
    case_ids: list[str] = []
    for index, raw in enumerate(observations):
        observation = _object(raw, f"observations[{index}]")
        _exact_keys(observation, _OBSERVATION_KEYS, f"observations[{index}]")
        case_id = _text(observation["case_id"], f"observations[{index}].case_id")
        if not _CASE_ID.fullmatch(case_id):
            raise RecordError(f"observations[{index}].case_id is not an HRC case ID")
        case_ids.append(case_id)
        exposures = _array(
            observation["observed_exposure_ids"],
            f"observations[{index}].observed_exposure_ids",
        )
        checked_exposures: list[str] = []
        for exposure_index, exposure in enumerate(exposures):
            exposure_id = _text(
                exposure,
                f"observations[{index}].observed_exposure_ids[{exposure_index}]",
            )
            if not _EXPOSURE_ID.fullmatch(exposure_id):
                raise RecordError("observed exposure IDs must use uppercase tokens")
            checked_exposures.append(exposure_id)
        if checked_exposures != sorted(checked_exposures):
            raise RecordError("observed exposure IDs must be in lexical order")
        if len(checked_exposures) != len(set(checked_exposures)):
            raise RecordError("observed exposure IDs must not contain duplicates")
    if case_ids != sorted(case_ids):
        raise RecordError("observations must be in lexical case_id order")
    if len(case_ids) != len(set(case_ids)):
        raise RecordError("observations must not repeat a case_id")
    _verify_no_semantic_promotion(checked, "declared exposure report")
    return checked


def build_exposure_report(
    *,
    source_authority_sha256: str,
    construction_key_commitment_sha256: str,
    observations: Mapping[str, Sequence[str]],
    candidate_snapshot_freeze_id: str | None = None,
) -> dict[str, Any]:
    """Build a canonical report from explicit case-to-exposure declarations."""

    rows = [
        {
            "case_id": case_id,
            "observed_exposure_ids": sorted(exposure_ids),
        }
        for case_id, exposure_ids in sorted(observations.items())
    ]
    report: dict[str, Any] = {
        "schema_version": EXPOSURE_REPORT_SCHEMA,
        "report_id": "QER:" + "0" * 64,
        "authority_id": "HRC-1",
        "source_authority_sha256": source_authority_sha256,
        "construction_key_commitment_sha256": (
            construction_key_commitment_sha256
        ),
        "candidate_snapshot_freeze_id": candidate_snapshot_freeze_id,
        "observations": rows,
        "automatic_semantic_effect": "NONE",
        "semantic_verdict": None,
        "translation_fidelity_verdict": None,
    }
    report["report_id"] = compute_exposure_report_id(report)
    return validate_exposure_report(report)


def compute_freeze_id(freeze: Mapping[str, Any]) -> str:
    """Return the deterministic ID of a qualification freeze record."""

    return _content_id(
        freeze, id_field="freeze_id", prefix="QFZ", domain=FREEZE_ID_DOMAIN
    )


def validate_freeze_record(freeze: Mapping[str, Any]) -> dict[str, Any]:
    checked = _object(freeze, "qualification freeze")
    canonical_bytes(checked)
    _exact_keys(checked, _FREEZE_KEYS, "qualification freeze")
    if checked["schema_version"] != FREEZE_SCHEMA:
        raise RecordError("qualification freeze has the wrong schema_version")
    freeze_id = _text(checked["freeze_id"], "freeze_id")
    if not _FREEZE_ID.fullmatch(freeze_id):
        raise RecordError("freeze_id must use the QFZ: content-addressed namespace")
    if freeze_id != compute_freeze_id(checked):
        raise RecordError("freeze_id does not match the canonical freeze content")
    if checked["authority_id"] != "HRC-1":
        raise RecordError("qualification freeze authority_id must be HRC-1")
    kind = checked["input_kind"]
    if kind not in {"DECLARED_EXPOSURE_REPORT", "TRANSLATION_SNAPSHOT"}:
        raise RecordError("qualification freeze input_kind is unsupported")
    _plain_sha(checked["artifact_sha256"], "artifact_sha256")
    byte_length = checked["artifact_byte_length"]
    if type(byte_length) is not int or byte_length < 1:
        raise RecordError("artifact_byte_length must be a positive integer")
    content_id = _text(checked["content_id"], "content_id")
    closure = checked["record_closure_sha256"]
    if kind == "DECLARED_EXPOSURE_REPORT":
        if not _REPORT_ID.fullmatch(content_id):
            raise RecordError("report freeze content_id must use the QER: namespace")
        if closure is not None:
            raise RecordError("report freeze record_closure_sha256 must be null")
        if checked["qualification_status"] != REPORT_FROZEN:
            raise RecordError("report freeze has the wrong qualification_status")
    else:
        if not re.fullmatch(r"TSN:[0-9a-f]{64}", content_id):
            raise RecordError("snapshot freeze content_id must use the TSN: namespace")
        if type(closure) is not str or not _DOMAIN_SHA.fullmatch(closure):
            raise RecordError("snapshot freeze requires a domain-separated closure digest")
        if checked["qualification_status"] != SNAPSHOT_FROZEN:
            raise RecordError("snapshot freeze has the wrong qualification_status")
    _verify_no_semantic_promotion(checked, "qualification freeze")
    return checked


def _build_freeze(
    *,
    input_kind: str,
    content_id: str,
    artifact_bytes: bytes,
    record_closure_sha256: str | None,
    qualification_status: str,
) -> dict[str, Any]:
    freeze: dict[str, Any] = {
        "schema_version": FREEZE_SCHEMA,
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
    freeze["freeze_id"] = compute_freeze_id(freeze)
    return validate_freeze_record(freeze)


def freeze_exposure_report(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate and freeze a report without opening the controller fixture."""

    raw = _read_bytes(path, "declared exposure report")
    report = validate_exposure_report(
        _load_object_bytes(raw, "declared exposure report")
    )
    return report, _build_freeze(
        input_kind="DECLARED_EXPOSURE_REPORT",
        content_id=report["report_id"],
        artifact_bytes=raw,
        record_closure_sha256=None,
        qualification_status=REPORT_FROZEN,
    )


def verify_frozen_exposure_report(
    path: Path, freeze: Mapping[str, Any]
) -> dict[str, Any]:
    """Verify that a report is byte-identical to an immutable freeze record."""

    report, actual = freeze_exposure_report(path)
    expected = validate_freeze_record(freeze)
    if expected["input_kind"] != "DECLARED_EXPOSURE_REPORT":
        raise RecordError("qualification requires an exposure-report freeze")
    if expected != actual:
        raise RecordError("declared exposure report does not match its freeze record")
    return report


def freeze_translation_snapshot(
    snapshot_path: Path, records_dir: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate a translation snapshot and freeze its bytes and record closure."""

    raw = _read_bytes(snapshot_path, "translation snapshot")
    snapshot = _load_object_bytes(raw, "translation snapshot")
    inventory = load_translation_inventory(records_dir)
    validation = validate_translation_snapshot(snapshot, inventory)
    closure = snapshot.get("record_closure_sha256")
    if type(closure) is not str or not _DOMAIN_SHA.fullmatch(closure):
        raise RecordError("validated translation snapshot lacks a closure digest")
    freeze = _build_freeze(
        input_kind="TRANSLATION_SNAPSHOT",
        content_id=validation.snapshot_id,
        artifact_bytes=raw,
        record_closure_sha256=closure,
        qualification_status=SNAPSHOT_FROZEN,
    )
    return snapshot, freeze


def verify_frozen_translation_snapshot(
    snapshot_path: Path,
    records_dir: Path,
    freeze: Mapping[str, Any],
) -> dict[str, Any]:
    """Replay a candidate snapshot and inventory against its supplied freeze."""

    snapshot, actual = freeze_translation_snapshot(snapshot_path, records_dir)
    expected = validate_freeze_record(freeze)
    if expected["input_kind"] != "TRANSLATION_SNAPSHOT":
        raise RecordError("qualification requires a translation-snapshot freeze")
    if expected != actual:
        raise RecordError("translation snapshot does not match its freeze record")
    return snapshot


@dataclass(frozen=True)
class HRCQualificationFixture:
    repository_root: Path
    manifest: Mapping[str, Any]
    blind_packet: Mapping[str, Any]
    commitment: Mapping[str, Any]
    construction_key: Mapping[str, Any]
    mutation_ledger: Mapping[str, Any]
    benign_controls: Mapping[str, Any]
    expected_cases: Mapping[str, tuple[str, ...]]
    case_kinds: Mapping[str, str]
    controller_bindings: Mapping[str, str]

    @property
    def source_authority_sha256(self) -> str:
        return str(self.construction_key["source_file_sha256"])

    @property
    def construction_key_commitment_sha256(self) -> str:
        return str(self.manifest["construction_key_commitment_sha256"])


def _validate_artifact_inventory(
    repository_root: Path, manifest: Mapping[str, Any]
) -> tuple[dict[str, Mapping[str, Any]], dict[str, bytes]]:
    inventory = _array(
        manifest.get("artifact_inventory"), "manifest artifact_inventory"
    )
    by_path: dict[str, Mapping[str, Any]] = {}
    bytes_by_path: dict[str, bytes] = {}
    paths: list[str] = []
    for index, raw in enumerate(inventory):
        item = _object(raw, f"manifest artifact_inventory[{index}]")
        path_text = _text(item.get("path"), "artifact inventory path")
        pure = PurePosixPath(path_text)
        if pure.is_absolute() or ".." in pure.parts:
            raise RecordError(
                "qualification artifact path must remain repository-relative"
            )
        paths.append(path_text)
        if path_text in by_path:
            raise RecordError("qualification artifact inventory contains a duplicate path")
        path = repository_root / pure
        raw_bytes = _read_bytes(path, f"qualification artifact {path_text}")
        byte_length = item.get("byte_length")
        if type(byte_length) is not int or byte_length < 1:
            raise RecordError("qualification artifact byte_length must be positive")
        if len(raw_bytes) != byte_length:
            raise RecordError(f"qualification artifact byte length mismatch: {path_text}")
        expected_sha = _plain_sha(item.get("sha256"), "artifact inventory sha256")
        if hashlib.sha256(raw_bytes).hexdigest() != expected_sha:
            raise RecordError(f"qualification artifact digest mismatch: {path_text}")
        by_path[path_text] = item
        bytes_by_path[path_text] = raw_bytes
    if paths != sorted(paths):
        raise RecordError("qualification artifact inventory must be lexically ordered")
    if set(paths) != _FIXTURE_PATHS:
        raise RecordError(
            "HRC-1 artifact inventory is incomplete or contains an extra path"
        )
    return by_path, bytes_by_path


def _load_pinned_hrc_manifest(
    repository_root: Path,
) -> tuple[dict[str, Any], str]:
    """Capture and authenticate the built-in HRC-1 manifest before use."""

    raw = _read_bytes(repository_root / MANIFEST_REL, "HRC-1 manifest")
    actual_sha256 = hashlib.sha256(raw).hexdigest()
    if actual_sha256 != HRC_1_MANIFEST_SHA256:
        raise RecordError("HRC-1 manifest does not match its pinned SHA-256")
    manifest = _load_object_bytes(raw, "HRC-1 manifest")
    if (
        manifest.get("schema_version")
        != "creib.translation-qualification-manifest.v1"
    ):
        raise RecordError("HRC-1 manifest has the wrong schema_version")
    if manifest.get("authority_id") != "HRC-1":
        raise RecordError("HRC-1 manifest has the wrong authority_id")
    return manifest, actual_sha256


def _manifest_artifact_binding(
    manifest: Mapping[str, Any], path: str
) -> Mapping[str, Any]:
    matches = [
        _object(raw, "manifest artifact inventory item")
        for raw in _array(
            manifest.get("artifact_inventory"), "manifest artifact_inventory"
        )
        if type(raw) is dict and raw.get("path") == path
    ]
    if len(matches) != 1:
        raise RecordError(f"HRC-1 manifest must bind exactly one {path} artifact")
    _plain_sha(matches[0].get("sha256"), "artifact inventory sha256")
    return matches[0]


def _case_map(
    rows: Any, *, id_field: str, kind: str
) -> tuple[dict[str, tuple[str, ...]], dict[str, str]]:
    expected: dict[str, tuple[str, ...]] = {}
    kinds: dict[str, str] = {}
    for index, raw in enumerate(_array(rows, f"{kind} cases")):
        item = _object(raw, f"{kind} cases[{index}]")
        case_id = _text(item.get(id_field), f"{kind} case ID")
        if not _CASE_ID.fullmatch(case_id):
            raise RecordError(f"invalid {kind} case ID: {case_id}")
        if case_id in expected:
            raise RecordError(f"duplicate {kind} case ID: {case_id}")
        exposure_values = _array(item.get("expected_exposures"), "expected exposures")
        exposures: list[str] = []
        for value in exposure_values:
            exposure = _text(value, "expected exposure ID")
            if not _EXPOSURE_ID.fullmatch(exposure):
                raise RecordError("expected exposure IDs must use uppercase tokens")
            exposures.append(exposure)
        if not exposures or len(exposures) != len(set(exposures)):
            raise RecordError("expected exposure IDs must be nonempty and unique")
        expected[case_id] = tuple(sorted(exposures))
        kinds[case_id] = kind
    return expected, kinds


def _load_hrc_fixture_from_pinned_manifest(
    root: Path,
    manifest: Mapping[str, Any],
    manifest_sha256: str,
) -> HRCQualificationFixture:
    """Load controller data from the bytes authenticated by a pinned manifest."""

    inventory, artifact_bytes = _validate_artifact_inventory(root, manifest)
    blind = _load_object_bytes(artifact_bytes[BLIND_PACKET_REL], "HRC-1 blind packet")
    commitment = _load_object_bytes(
        artifact_bytes[COMMITMENT_REL], "HRC-1 commitment"
    )
    key = _load_object_bytes(artifact_bytes[KEY_REL], "HRC-1 construction key")
    obligations = _load_object_bytes(
        artifact_bytes[OBLIGATIONS_REL], "HRC-1 obligations"
    )
    ledger = _load_object_bytes(
        artifact_bytes[MUTATIONS_REL], "HRC-1 mutation ledger"
    )
    controls = _load_object_bytes(
        artifact_bytes[CONTROLS_REL], "HRC-1 benign controls"
    )

    allowed = _array(blind.get("translator_allowed_paths"), "blind packet paths")
    allowed_paths = [
        _text(_object(item, "blind packet path").get("path"), "blind packet path")
        for item in allowed
    ]
    if not blind.get("path_set_is_closed") or tuple(allowed_paths) != _BLIND_PATHS:
        raise RecordError("HRC-1 blind packet is not the fixed closed path set")
    for raw in allowed:
        item = _object(raw, "blind packet item")
        inventory_item = inventory[str(item["path"])]
        if (
            item.get("sha256") != inventory_item.get("sha256")
            or item.get("byte_length") != inventory_item.get("byte_length")
        ):
            raise RecordError("blind packet binding disagrees with the manifest")
    if any(
        path.startswith("forge/translation/qualification/controller/")
        for path in allowed_paths
    ):
        raise PolicyViolation("blind packet exposes a controller path")

    committed = _object(commitment.get("committed_artifact"), "committed artifact")
    if committed.get("path") != KEY_REL:
        raise RecordError("construction-key commitment names the wrong path")
    if (
        commitment.get("translator_access") != "BLIND_PACKET"
        or inventory[COMMITMENT_REL].get("translator_access") != "BLIND_PACKET"
    ):
        raise PolicyViolation(
            "the pre-disclosure construction-key commitment must be in the blind packet"
        )
    key_sha = hashlib.sha256(artifact_bytes[KEY_REL]).hexdigest()
    if (
        committed.get("sha256") != key_sha
        or committed.get("byte_length") != len(artifact_bytes[KEY_REL])
        or manifest.get("construction_key_commitment_sha256") != key_sha
    ):
        raise RecordError("construction-key commitment does not match the withheld key")
    if (
        commitment.get("disclosure_phase")
        != "AFTER_TRANSLATION_OUTPUTS_ARE_FROZEN"
    ):
        raise PolicyViolation("construction key does not require post-freeze disclosure")

    source_sha = hashlib.sha256(artifact_bytes[AUTHORITY_REL]).hexdigest()
    obligation_sha = hashlib.sha256(artifact_bytes[OBLIGATIONS_REL]).hexdigest()
    if key.get("source_file_sha256") != source_sha:
        raise RecordError("construction key is bound to different authority bytes")
    if key.get("obligation_record_sha256") != obligation_sha:
        raise RecordError("construction key is bound to different obligations")
    for name, record in (("mutation ledger", ledger), ("benign controls", controls)):
        if record.get("source_file_sha256") != source_sha:
            raise RecordError(f"{name} is bound to different authority bytes")
        if record.get("obligation_record_sha256") != obligation_sha:
            raise RecordError(f"{name} is bound to different obligations")
        terminal = _object(record.get("required_terminal_fields"), f"{name} boundary")
        if terminal != {"automatic_semantic_effect": "NONE", "semantic_verdict": None}:
            raise PolicyViolation(f"{name} permits an automatic semantic promotion")
    if obligations.get("source_file_sha256") != source_sha:
        raise RecordError("source obligations are bound to different authority bytes")
    boundary = _object(
        manifest.get("qualification_claim_boundary"), "qualification claim boundary"
    )
    if boundary != {
        "allowed_mechanical_result": _LEGACY_FIXTURE_SUCCESS_LABEL,
        "asserts_semantic_truth": False,
        "asserts_translation_fidelity": False,
        "semantic_verdict": None,
    }:
        raise PolicyViolation("manifest qualification claim boundary was weakened")

    mutation_cases, mutation_kinds = _case_map(
        ledger.get("mutations"), id_field="mutation_id", kind="MUTATION"
    )
    control_cases, control_kinds = _case_map(
        controls.get("controls"), id_field="control_id", kind="BENIGN_CONTROL"
    )
    if set(mutation_cases).intersection(control_cases):
        raise RecordError("mutation and benign-control case IDs overlap")
    expected_cases = {**mutation_cases, **control_cases}
    case_kinds = {**mutation_kinds, **control_kinds}

    counts = _object(manifest.get("construction_counts"), "manifest counts")
    if counts.get("mutations") != len(mutation_cases):
        raise RecordError("manifest mutation count does not match the ledger")
    if counts.get("benign_controls") != len(control_cases):
        raise RecordError("manifest benign-control count does not match the controller")
    obligation_rows = _array(obligations.get("obligations"), "source obligations")
    if counts.get("source_obligations") != len(obligation_rows):
        raise RecordError("manifest source-obligation count does not match")
    discriminators = _array(
        _object(key.get("construction_ground_truth"), "construction ground truth").get(
            "required_discriminator_families"
        ),
        "required discriminator families",
    )
    if counts.get("required_discriminator_families") != len(discriminators):
        raise RecordError("manifest discriminator count does not match")

    bindings = {
        "manifest_sha256": manifest_sha256,
        "construction_key_sha256": key_sha,
        "mutation_ledger_sha256": hashlib.sha256(
            artifact_bytes[MUTATIONS_REL]
        ).hexdigest(),
        "benign_controls_sha256": hashlib.sha256(
            artifact_bytes[CONTROLS_REL]
        ).hexdigest(),
        "obligation_record_sha256": obligation_sha,
        "source_authority_sha256": source_sha,
    }
    return HRCQualificationFixture(
        repository_root=root,
        manifest=manifest,
        blind_packet=blind,
        commitment=commitment,
        construction_key=key,
        mutation_ledger=ledger,
        benign_controls=controls,
        expected_cases=dict(sorted(expected_cases.items())),
        case_kinds=dict(sorted(case_kinds.items())),
        controller_bindings=bindings,
    )


def load_hrc_qualification_fixture(repository_root: Path) -> HRCQualificationFixture:
    """Replay the one code-pinned HRC-1 instrument and its controller bindings."""

    root = repository_root.resolve()
    manifest, manifest_sha256 = _load_pinned_hrc_manifest(root)
    return _load_hrc_fixture_from_pinned_manifest(root, manifest, manifest_sha256)


def _exposure_token(case_id: str, exposure_id: str) -> str:
    return f"{case_id}::{exposure_id}"


def compute_qualification_id(result: Mapping[str, Any]) -> str:
    """Return the deterministic ID of a completed qualification replay."""

    return _content_id(
        result,
        id_field="qualification_id",
        prefix="QRES",
        domain=RESULT_ID_DOMAIN,
    )


def qualify_exposure_report(
    *,
    report_path: Path,
    report_freeze: Mapping[str, Any],
    repository_root: Path,
    candidate_snapshot_freeze: Mapping[str, Any],
    candidate_snapshot_path: Path,
    candidate_records_dir: Path,
) -> dict[str, Any]:
    """Compare a frozen declaration with HRC-1's exact controller records.

    The report and candidate snapshot are replayed against their freezes before
    the pinned manifest or any controller record is loaded.  This order protects
    the runner protocol, although it cannot prove what information the producer
    possessed before invoking the runner.
    """

    report = verify_frozen_exposure_report(report_path, report_freeze)
    checked_report_freeze = validate_freeze_record(report_freeze)

    declared_subject = report["candidate_snapshot_freeze_id"]
    if declared_subject is None:
        raise RecordError("qualification report must bind a candidate snapshot freeze")
    checked_subject = validate_freeze_record(candidate_snapshot_freeze)
    if checked_subject["input_kind"] != "TRANSLATION_SNAPSHOT":
        raise RecordError("candidate subject must be a translation-snapshot freeze")
    if checked_subject["freeze_id"] != declared_subject:
        raise RecordError("candidate snapshot freeze does not match the report binding")
    verify_frozen_translation_snapshot(
        candidate_snapshot_path,
        candidate_records_dir,
        checked_subject,
    )

    # The report's public bindings are checked against the code-pinned manifest
    # before any artifact in the withheld controller is captured or parsed.
    root = repository_root.resolve()
    manifest, manifest_sha256 = _load_pinned_hrc_manifest(root)
    authority_binding = _manifest_artifact_binding(manifest, AUTHORITY_REL)
    if report["source_authority_sha256"] != authority_binding["sha256"]:
        raise RecordError("report is bound to different HRC-1 authority bytes")
    if (
        report["construction_key_commitment_sha256"]
        != manifest.get("construction_key_commitment_sha256")
    ):
        raise RecordError("report is bound to a different construction-key commitment")

    # Controller disclosure begins only after both frozen inputs and both
    # public HRC-1 bindings have passed the checks above.
    fixture = _load_hrc_fixture_from_pinned_manifest(root, manifest, manifest_sha256)

    observed = {
        row["case_id"]: tuple(row["observed_exposure_ids"])
        for row in report["observations"]
    }
    expected_ids = set(fixture.expected_cases)
    observed_ids = set(observed)
    all_case_ids = sorted(expected_ids.union(observed_ids))

    case_results: list[dict[str, Any]] = []
    detected_tokens: list[str] = []
    missed_tokens: list[str] = []
    false_positive_tokens: list[str] = []
    detected_case_ids: list[str] = []
    missed_case_ids: list[str] = []
    false_positive_case_ids: list[str] = []
    exact_case_ids: list[str] = []
    unreported_case_ids: list[str] = []
    unknown_case_ids: list[str] = []

    for case_id in all_case_ids:
        expected = set(fixture.expected_cases.get(case_id, ()))
        actual = set(observed.get(case_id, ()))
        detected = sorted(expected.intersection(actual))
        missed_ids = sorted(expected - actual)
        false_ids = sorted(actual - expected)
        detected_tokens.extend(_exposure_token(case_id, item) for item in detected)
        missed_tokens.extend(_exposure_token(case_id, item) for item in missed_ids)
        false_positive_tokens.extend(
            _exposure_token(case_id, item) for item in false_ids
        )
        if detected:
            detected_case_ids.append(case_id)
        if missed_ids:
            missed_case_ids.append(case_id)
        if false_ids:
            false_positive_case_ids.append(case_id)
        if case_id not in observed:
            unreported_case_ids.append(case_id)
        if case_id not in expected_ids:
            unknown_case_ids.append(case_id)

        if case_id not in expected_ids:
            case_status = "UNDECLARED_CASE"
        elif case_id not in observed:
            case_status = "NO_OBSERVATION"
        elif missed_ids and false_ids:
            case_status = "MISMATCH"
        elif missed_ids:
            case_status = "EXPECTED_EXPOSURE_MISSED"
        elif false_ids:
            case_status = "UNDECLARED_EXPOSURE_REPORTED"
        else:
            case_status = "DECLARED_EXPOSURES_REPRODUCED"
            exact_case_ids.append(case_id)
        case_results.append(
            {
                "case_id": case_id,
                "case_kind": fixture.case_kinds.get(case_id, "UNDECLARED"),
                "expected_exposure_ids": sorted(expected),
                "observed_exposure_ids": sorted(actual),
                "detected_exposure_ids": detected,
                "missed_exposure_ids": missed_ids,
                "false_positive_exposure_ids": false_ids,
                "case_status": case_status,
            }
        )

    if missed_tokens and false_positive_tokens:
        status = MISMATCH
    elif missed_tokens:
        status = MISSED
    elif false_positive_tokens:
        status = FALSE_POSITIVES
    else:
        status = ALL_REPRODUCED

    result: dict[str, Any] = {
        "schema_version": RESULT_SCHEMA,
        "qualification_id": "QRES:" + "0" * 64,
        "authority_id": "HRC-1",
        "qualification_scope": QUALIFICATION_SCOPE,
        "report_freeze_id": checked_report_freeze["freeze_id"],
        "candidate_snapshot_freeze_id": checked_subject["freeze_id"],
        "controller_bindings": dict(fixture.controller_bindings),
        "case_counts": {
            "declared_controller_cases": len(expected_ids),
            "reported_cases": len(observed_ids),
            "exactly_reproduced_cases": len(exact_case_ids),
            "cases_with_detected_exposures": len(detected_case_ids),
            "cases_with_missed_exposures": len(missed_case_ids),
            "cases_with_false_positives": len(false_positive_case_ids),
        },
        "qualification_status": status,
        "exact_case_ids": exact_case_ids,
        "detected_case_ids": detected_case_ids,
        "missed_case_ids": missed_case_ids,
        "false_positive_case_ids": false_positive_case_ids,
        "unreported_case_ids": unreported_case_ids,
        "unknown_case_ids": unknown_case_ids,
        "detected_exposure_ids": sorted(detected_tokens),
        "missed_exposure_ids": sorted(missed_tokens),
        "false_positive_exposure_ids": sorted(false_positive_tokens),
        "case_results": case_results,
        "runner_verified_freeze_before_controller_load": True,
        "controller_declaration_match": status == ALL_REPRODUCED,
        "mutation_execution_verified": False,
        "execution_evidence_verified": False,
        "blindness_verdict": None,
        "automatic_semantic_effect": "NONE",
        "semantic_verdict": None,
        "translation_fidelity_verdict": None,
        "epistemic_limit": QUALIFICATION_LIMIT,
    }
    result["qualification_id"] = compute_qualification_id(result)
    return result
