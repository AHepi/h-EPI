#!/usr/bin/env python3
"""Verify a formalism-independent semantic translation snapshot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from creib.errors import CREIBError, RecordError  # noqa: E402
from creib.forge.schema_validation import load_local_schema_catalog  # noqa: E402
from creib.forge.translation import (  # noqa: E402
    TRANSLATION_SCHEMA_TO_FILE,
    load_translation_inventory,
    validate_translation_snapshot,
    verify_source_document_bytes,
)
from creib.strict_json import load_strict  # noqa: E402


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate generic translation records and their two-way source/model "
            "trace without treating integrity as semantic fidelity"
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    verify = subparsers.add_parser("verify", help="verify a selected translation snapshot")
    verify.add_argument("--records-dir", type=Path, required=True)
    verify.add_argument("--snapshot", type=Path, required=True)
    verify.add_argument("--schema-dir", type=Path, default=ROOT / "forge" / "schema")

    source = subparsers.add_parser("verify-source", help="verify external authority bytes")
    source.add_argument("--document-record", type=Path, required=True)
    source.add_argument("--source", type=Path, required=True)
    source.add_argument("--schema-dir", type=Path, default=ROOT / "forge" / "schema")
    return parser


def _emit(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")))


def _schema_validate(record: object, catalog: object) -> None:
    if type(record) is not dict:
        raise RecordError("translation record must be an object")
    schema = record.get("schema_version")
    try:
        schema_name = TRANSLATION_SCHEMA_TO_FILE[schema]
    except (KeyError, TypeError) as exc:
        raise RecordError("unknown generic translation schema version") from exc
    catalog.validate(record, schema_name)


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        catalog = load_local_schema_catalog(args.schema_dir)
        if args.command == "verify-source":
            record = load_strict(args.document_record)
            _schema_validate(record, catalog)
            verify_source_document_bytes(record, args.source)
            _emit(
                {
                    "operational_status": "SOURCE_BYTES_VERIFIED",
                    "document_id": record["document_id"],
                    "semantic_verdict": None,
                }
            )
            return 0

        records = load_translation_inventory(args.records_dir)
        snapshot = load_strict(args.snapshot)
        for record in records.values():
            _schema_validate(record, catalog)
        _schema_validate(snapshot, catalog)
        result = validate_translation_snapshot(snapshot, records)
        _emit(result.to_dict())
        return 0
    except CREIBError as exc:
        _emit(
            {
                "operational_status": "INVALID",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "semantic_verdict": None,
            }
        )
        return exc.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
