#!/usr/bin/env python3
"""Validate semantic-forge schemas and an instance without network access."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from creib.errors import CREIBError  # noqa: E402
from creib.strict_json import load_strict  # noqa: E402
from creib.forge.schema_validation import (  # noqa: E402
    LocalSchemaCatalog,
    load_local_schema_catalog,
    validate_semantic_forge_instance,
)


def _validate_specialized_runtime_contract(
    instance: object,
    *,
    schema_name: str,
    schema_dir: Path,
    catalog: LocalSchemaCatalog,
) -> str:
    """Run context-free executable checks in addition to JSON Schema.

    Some record families need bound external context (for example an inquiry
    event needs the selected chain head and research-ledger snapshot).  Those
    remain explicitly schema-only here instead of being mislabeled as fully
    mechanically valid.
    """

    if catalog.has_full_record_runtime_contract(schema_name):
        # LocalSchemaCatalog.validate already dispatched the parser selected
        # by this schema's canonical identity.
        return "FULL_RECORD"
    if schema_name == "calibration-run.schema.json":
        default_dir = ROOT / "forge" / "schema"
        if schema_dir.resolve() != default_dir.resolve():
            return "NONE"
        from creib.forge.calibration import validate_calibration_report

        validate_calibration_report(instance, repo_root=ROOT)  # type: ignore[arg-type]
        return "CURRENT_REPOSITORY_REPLAY"
    if schema_name == "adaptive-inquiry.schema.json":
        if type(instance) is not dict or instance.get("record_type") != "adaptive_inquiry_plan":
            return "NONE"
        from creib.forge.inquiry import validate_adaptive_inquiry_plan

        validate_adaptive_inquiry_plan(instance)
        # Exact run/ledger/event replay needs paths which are deliberately not
        # inferred by this generic validator.  The inquiry CLI performs that
        # contextual regeneration before it can append an event.
        return "INTRINSIC_RECORD_ONLY"
    return "NONE"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Strict-load local semantic-forge schemas and validate one JSON "
            "instance through a fail-closed offline registry"
        )
    )
    parser.add_argument(
        "--schema-dir",
        type=Path,
        default=ROOT / "forge" / "schema",
    )
    parser.add_argument(
        "--instance",
        "--corpus",
        dest="instance",
        type=Path,
        default=ROOT / "forge" / "corpus" / "cr-1.0-seed.json",
    )
    parser.add_argument("--schema", default="corpus.schema.json")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        catalog = load_local_schema_catalog(args.schema_dir)
        instance = load_strict(args.instance)
        validate_semantic_forge_instance(
            instance,
            schema_name=args.schema,
            catalog=catalog,
        )
        runtime_scope = _validate_specialized_runtime_contract(
            instance,
            schema_name=args.schema,
            schema_dir=args.schema_dir,
            catalog=catalog,
        )
        print(
            json.dumps(
                {
                    "instance": str(args.instance),
                    "schema": args.schema,
                    "schema_count": len(catalog.schema_names),
                    "schema_names": list(catalog.schema_names),
                    "validation_status": (
                        "SCHEMA_AND_INTRINSIC_RUNTIME_VALID"
                        if runtime_scope == "INTRINSIC_RECORD_ONLY"
                        else (
                            "SCHEMA_AND_RUNTIME_VALID"
                            if runtime_scope != "NONE"
                            else "SCHEMA_VALID_ONLY"
                        )
                    ),
                    "runtime_contract_checked": runtime_scope != "NONE",
                    "runtime_contract_scope": runtime_scope,
                    "semantic_verdict": None,
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        return 0
    except (CREIBError, TypeError, ValueError) as exc:
        exit_code = exc.exit_code if isinstance(exc, CREIBError) else 1
        print(
            json.dumps(
                {
                    "validation_status": "INVALID",
                    "semantic_verdict": None,
                    "error": str(exc),
                    "exit_code": exit_code,
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
