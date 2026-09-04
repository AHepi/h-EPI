#!/usr/bin/env python3
"""Build and resolve isolated semantic-forge hardening records."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from creib.canonical import canonical_bytes  # noqa: E402
from creib.errors import CREIBError, RecordError  # noqa: E402
from creib.forge.hardening import (  # noqa: E402
    DECISION_SCHEMA,
    EVIDENCE_SCHEMA,
    build_hardening_decision,
    build_hardening_evidence,
    derive_hardening_obligations,
    derive_human_decision_requirements,
    load_canonical_record,
    publish_content_addressed_record,
    resolve_hardening_comparison,
    validate_hardening_comparison,
)


def _emit(record: dict[str, Any], output: Path | None) -> None:
    if output is None:
        sys.stdout.buffer.write(canonical_bytes(record) + b"\n")
    else:
        publish_content_addressed_record(record, output)
        print(str(output))


def _records(directory: Path, schema_version: str) -> list[dict[str, Any]]:
    if not directory.exists():
        return []
    if not directory.is_dir():
        raise RecordError(f"hardening inventory path is not a directory: {directory}")
    records: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*.json")):
        record = load_canonical_record(path)
        if record.get("schema_version") != schema_version:
            raise RecordError(f"unexpected record family in {directory}: {path.name}")
        records.append(record)
    return records


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Derive hardening obligations, replay typed evidence, and resolve "
            "the exact non-scalar conjunction"
        )
    )
    commands = parser.add_subparsers(dest="command", required=True)

    obligations = commands.add_parser("obligations")
    obligations.add_argument("--comparison", type=Path, required=True)

    evidence = commands.add_parser("evidence")
    evidence.add_argument("--comparison", type=Path, required=True)
    evidence.add_argument("--obligation-id", required=True)
    evidence.add_argument("--payload", type=Path, required=True)
    evidence.add_argument("--output", type=Path)

    decision = commands.add_parser("decision")
    decision.add_argument("--comparison", type=Path, required=True)
    decision.add_argument("--requirement-id", required=True)
    decision.add_argument(
        "--disposition",
        required=True,
        choices=(
            "ACCEPT_FOR_DECLARED_SCOPE",
            "SUSPEND",
            "COMPARISON_DEFECT",
            "DEFEATS_HARDENING",
        ),
    )
    decision.add_argument("--reason", required=True)
    decision.add_argument("--created-on", required=True)
    decision.add_argument("--sequence", type=int, default=1)
    decision.add_argument("--previous-decision-id")
    decision.add_argument("--evidence", type=Path, action="append", default=[])
    decision.add_argument("--output", type=Path)

    resolve = commands.add_parser("resolve")
    resolve.add_argument("--comparison", type=Path, required=True)
    resolve.add_argument("--evidence-dir", type=Path, required=True)
    resolve.add_argument("--decision-dir", type=Path, required=True)
    resolve.add_argument("--output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        comparison = validate_hardening_comparison(
            load_canonical_record(args.comparison)
        )
        if args.command == "obligations":
            result = {
                "comparison_id": comparison["comparison_id"],
                "obligations": list(derive_hardening_obligations(comparison)),
                "human_requirements": list(
                    derive_human_decision_requirements(comparison)
                ),
                "semantic_verdict": None,
            }
            _emit(result, None)
        elif args.command == "evidence":
            payload = load_canonical_record(args.payload)
            result = build_hardening_evidence(
                comparison, args.obligation_id, payload
            )
            _emit(result, args.output)
        elif args.command == "decision":
            evidence = [load_canonical_record(path) for path in args.evidence]
            result = build_hardening_decision(
                comparison,
                args.requirement_id,
                disposition=args.disposition,
                reason=args.reason,
                created_on=args.created_on,
                decision_sequence=args.sequence,
                previous_decision_id=args.previous_decision_id,
                considered_evidence=evidence,
            )
            _emit(result, args.output)
        elif args.command == "resolve":
            result = resolve_hardening_comparison(
                comparison,
                _records(args.evidence_dir, EVIDENCE_SCHEMA),
                _records(args.decision_dir, DECISION_SCHEMA),
            )
            _emit(result, args.output)
        else:  # pragma: no cover - argparse makes this unreachable
            raise AssertionError("unknown hardening command")
        return 0
    except (CREIBError, TypeError, ValueError, OSError) as exc:
        exit_code = exc.exit_code if isinstance(exc, CREIBError) else 1
        error = {
            "status": "INVALID",
            "semantic_verdict": None,
            "error": str(exc),
            "exit_code": exit_code,
        }
        sys.stderr.buffer.write(canonical_bytes(error) + b"\n")
        return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
