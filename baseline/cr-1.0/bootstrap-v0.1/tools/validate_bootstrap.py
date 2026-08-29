#!/usr/bin/env python3
"""Validate CR-1.0 bootstrap structure without interpreting or repairing it."""

from __future__ import annotations

import hashlib
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterator, Tuple

import yaml


ROOT = Path(__file__).resolve().parents[1]
ALLOWED_INFERENTIAL_STATUSES = {None, "DEF", "IMP", "DER"}


class UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""


def construct_unique_mapping(
    loader: UniqueKeyLoader, node: yaml.nodes.MappingNode, deep: bool = False
) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise ValueError(f"duplicate YAML key: {key!r}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_unique_mapping
)

REQUIRED_FILES = (
    "README.md",
    "authority/source_manifest.yaml",
    "authority/coverage_matrix.yaml",
    "authority/source_status_registry.yaml",
    "authority/identifier_inventory.yaml",
    "authority/import_ledger.yaml",
    "authority/authority_hierarchy.yaml",
    "authority/ambiguities.yaml",
    "authority/audit_ledger.yaml",
    "authority/bootstrap_gate_report.yaml",
    "language/core_declaration_map.yaml",
    "language/terminology_concordance.yaml",
    "reports/source_registry.md",
    "reports/identifier_inventory.md",
    "reports/core_declaration_map.md",
    "reports/import_ledger.md",
    "reports/terminology_and_ambiguities.md",
    "reports/bootstrap_gate_report.md",
    "checksums.sha256",
)


def walk(value: Any, path: str = "$" ) -> Iterator[Tuple[str, str, Any]]:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            yield child_path, str(key), child
            yield from walk(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, f"{path}[{index}]")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    errors: list[str] = []

    for rel in REQUIRED_FILES:
        if not (ROOT / rel).is_file():
            errors.append(f"missing required file: {rel}")

    yaml_documents: dict[str, Any] = {}
    for path in sorted(ROOT.rglob("*.yaml")):
        rel = path.relative_to(ROOT).as_posix()
        try:
            yaml_documents[rel] = yaml.load(
                path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader
            )
        except Exception as exc:
            errors.append(f"invalid YAML {rel}: {exc}")

    for rel, document in yaml_documents.items():
        for location, key, value in walk(document):
            if key == "inferential_status":
                if isinstance(value, (dict, list)):
                    errors.append(
                        f"non-scalar inferential_status at {rel}:{location}"
                    )
                    continue
                if value not in ALLOWED_INFERENTIAL_STATUSES:
                    errors.append(
                        f"illegal inferential_status at {rel}:{location}: {value!r}"
                    )
                if value == "DER":
                    errors.append(
                        f"DER is unavailable during bootstrap at {rel}:{location}"
                    )
            if key == "proof_available" and value is not False:
                errors.append(
                    f"proof_available must remain false in bootstrap at {rel}:{location}"
                )

    gate = yaml_documents.get("authority/bootstrap_gate_report.yaml")
    if isinstance(gate, dict):
        gate_record = gate.get("gate", {})
        verdict = gate.get(
            "verdict", gate_record.get("verdict", gate_record.get("decision"))
        )
        if verdict != "FAIL":
            errors.append(f"bootstrap verdict must be FAIL, found {verdict!r}")
        blockers = gate.get("active_model_blockers", [])
        expected_blockers = gate.get("counts", {}).get("active_model_blockers")
        if expected_blockers != 51 or len(blockers) != 51:
            errors.append(
                "bootstrap gate report must contain exactly 51 active/core-registry blockers"
            )
        qd05 = next(
            (
                item
                for item in gate.get("quarantine", {}).get("downstream_application", [])
                if item.get("audit_id") == "BG-QD05"
            ),
            {},
        )
        qd05_locator = (qd05.get("locators") or [{}])[0]
        if (
            qd05_locator.get("physical_pdf_pages") != "261-263"
            or qd05_locator.get("printed_footer_pages") != "260-262"
        ):
            errors.append("BG-QD05 test-registry locator must be PDF 261-263/footer 260-262")

    manifest = yaml_documents.get("authority/source_manifest.yaml")
    if isinstance(manifest, dict):
        serialized = yaml.safe_dump(manifest, sort_keys=False)
        required_hash = "08ff81e848fea976b558345402d85723173be8f40f1041fb00d6267f1e026b8b"
        if required_hash not in serialized:
            errors.append("authority PDF SHA-256 is absent from source_manifest.yaml")
        if len(manifest.get("sources", [])) != 23:
            errors.append("source_manifest.yaml must contain exactly 23 frozen S-* tags")

    coverage = yaml_documents.get("authority/coverage_matrix.yaml")
    if isinstance(coverage, dict):
        page_hits: Counter[int] = Counter()
        for unit in coverage.get("top_level_units", []):
            page_range = unit.get("physical_pdf_pages", {})
            start, end = page_range.get("start"), page_range.get("end")
            if isinstance(start, int) and isinstance(end, int):
                page_hits.update(range(start, end + 1))
        expected_pages = set(range(1, 287))
        if set(page_hits) != expected_pages:
            errors.append("coverage matrix does not cover exactly physical pages 1-286")
        duplicates = sorted(page for page, hits in page_hits.items() if hits != 1)
        if duplicates:
            errors.append(f"coverage matrix has overlapping page assignments: {duplicates}")

    core = yaml_documents.get("language/core_declaration_map.yaml")
    if isinstance(core, dict):
        clauses = core.get("clauses", {})
        expected_families = {
            "TY": 3,
            "MS": 9,
            "SC": 8,
            "DF": 25,
            "RC": 3,
            "DP": 11,
            "AB": 1,
            "OM": 10,
            "IR": 8,
            "CT": 7,
            "BR": 8,
            "TH": 17,
        }
        family_counts = Counter(item.get("family") for item in clauses.values())
        if len(clauses) != 110 or dict(family_counts) != expected_families:
            errors.append(
                f"core declaration count mismatch: {len(clauses)} / {dict(family_counts)}"
            )
        for theorem_id in (f"TH-{number}" for number in range(1, 18)):
            theorem = clauses.get(theorem_id, {})
            if (
                theorem.get("inferential_status") is not None
                or theorem.get("target_status") != "DER"
                or theorem.get("proof_available") is not False
            ):
                errors.append(f"theorem quarantine violation: {theorem_id}")
        ct5 = clauses.get("CT-5", {})
        if (
            ct5.get("inferential_status") is not None
            or ct5.get("proof_available") is not False
        ):
            errors.append("CT-5 mixed clause must remain quarantined")

    imports = yaml_documents.get("authority/import_ledger.yaml")
    if isinstance(imports, dict):
        records = imports.get("records", [])
        record_ids = [item.get("id") for item in records]
        if len(records) != 102 or len(set(record_ids)) != 102:
            errors.append("import ledger must contain 102 unique records")
        application_records = [
            item for item in records if str(item.get("id", "")).startswith("I-")
        ]
        if len(application_records) != 24:
            errors.append("import ledger must contain exactly 24 I-* requests")
        for item in application_records:
            if (
                item.get("target_status") != "IMP"
                or item.get("inferential_status") is not None
                or item.get("proof_available") is not False
            ):
                errors.append(f"application import quarantine violation: {item.get('id')}")
        for item in records:
            if str(item.get("id", "")).startswith("AUD-") and (
                item.get("inferential_status") is not None
                or item.get("proof_available") is not False
            ):
                errors.append(f"audit import quarantine violation: {item.get('id')}")
        ir8 = next((item for item in records if item.get("id") == "IR-8"), {})
        ir8_warrant = ir8.get("source_warrant", {})
        if (
            ir8_warrant.get("physical_pdf_declaration_pages") != ["228"]
            or ir8_warrant.get("report_footer_declaration_pages") != ["227"]
        ):
            errors.append("IR-8 must be located only at PDF 228/footer 227")

    identifiers = yaml_documents.get("authority/identifier_inventory.yaml")
    if isinstance(identifiers, dict):
        blockers = identifiers.get("bootstrap_gate", {}).get("blockers", [])
        if any("collision" in str(item).lower() for item in blockers):
            errors.append("superseded identifier collisions may not be active blockers")

    audit = yaml_documents.get("authority/audit_ledger.yaml")
    if isinstance(audit, dict):
        qd05 = next(
            (item for item in audit.get("records", []) if item.get("audit_id") == "BG-QD05"),
            {},
        )
        qd05_locator = (qd05.get("locators") or [{}])[0]
        if (
            qd05_locator.get("physical_pdf_pages") != "261-263"
            or qd05_locator.get("printed_footer_pages") != "260-262"
        ):
            errors.append("audit-ledger BG-QD05 locator is inconsistent")

    human_gate_path = ROOT / "reports/bootstrap_gate_report.md"
    if human_gate_path.is_file() and isinstance(gate, dict):
        human_gate = human_gate_path.read_text(encoding="utf-8")
        human_blockers = set(
            re.findall(r"^\| (BG-[A-Z0-9]+) \| BLOCKER \|", human_gate, re.MULTILINE)
        )
        machine_blockers = {
            item.get("audit_id") for item in gate.get("active_model_blockers", [])
        }
        if human_blockers != machine_blockers or len(human_blockers) != 51:
            errors.append("human and machine active blocker registers disagree")
        human_downstream = set(
            re.findall(
                r"^\| (BG-QD\d+) \| QUARANTINED DOWNSTREAM \|",
                human_gate,
                re.MULTILINE,
            )
        )
        if human_downstream != {f"BG-QD{number:02d}" for number in range(1, 6)}:
            errors.append("human downstream quarantine register must be BG-QD01 through BG-QD05")

    for path in sorted(ROOT.rglob("*")):
        if (
            path.is_file()
            and path.resolve() != Path(__file__).resolve()
            and path.suffix.lower() in {".md", ".yaml", ".py", ".sha256"}
        ):
            if "/workspace/scratch/" in path.read_text(encoding="utf-8"):
                errors.append(f"non-portable scratch path remains in {path.relative_to(ROOT)}")

    checksum_path = ROOT / "checksums.sha256"
    if checksum_path.is_file():
        for line_no, raw_line in enumerate(
            checksum_path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            line = raw_line.strip()
            if not line:
                continue
            try:
                expected, rel = line.split("  ", 1)
            except ValueError:
                errors.append(f"malformed checksum line {line_no}")
                continue
            target = ROOT / rel
            if rel == "checksums.sha256":
                errors.append("checksums.sha256 must not hash itself")
            elif not target.is_file():
                errors.append(f"checksum target missing: {rel}")
            elif sha256(target) != expected:
                errors.append(f"checksum mismatch: {rel}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(
        "PASS: package integrity and quarantine discipline validated; "
        "the CR-1.0 bootstrap gate itself remains FAIL."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
