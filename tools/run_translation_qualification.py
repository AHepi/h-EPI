#!/usr/bin/env python3
"""Freeze and replay HRC-1 declared-exposure qualification inputs."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from creib.canonical import canonical_bytes  # noqa: E402
from creib.errors import CREIBError, RecordError  # noqa: E402
from creib.forge.qualification import (  # noqa: E402
    ALL_REPRODUCED,
    freeze_exposure_report,
    freeze_translation_snapshot,
    qualify_exposure_report,
    validate_freeze_record,
)
from creib.strict_json import load_strict  # noqa: E402


QUALIFICATION_MISMATCH_EXIT_CODE = 7


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Freeze a translation qualification input before controller "
            "disclosure, or replay a frozen exposure declaration against HRC-1"
        )
    )
    commands = parser.add_subparsers(dest="command", required=True)

    report = commands.add_parser(
        "freeze-report",
        help="validate and freeze an exposure report without reading the controller",
    )
    report.add_argument("--report", type=Path, required=True)
    report.add_argument("--output", type=Path)

    snapshot = commands.add_parser(
        "freeze-snapshot",
        help="validate and freeze a translation snapshot and its exact closure",
    )
    snapshot.add_argument("--snapshot", type=Path, required=True)
    snapshot.add_argument("--records-dir", type=Path, required=True)
    snapshot.add_argument("--output", type=Path)

    qualify = commands.add_parser(
        "qualify-report",
        help="compare a previously frozen declaration with the HRC-1 controller",
    )
    qualify.add_argument("--report", type=Path, required=True)
    qualify.add_argument("--freeze", type=Path, required=True)
    qualify.add_argument(
        "--candidate-freeze",
        type=Path,
        required=True,
        help="frozen translation snapshot bound by the report",
    )
    qualify.add_argument(
        "--candidate-snapshot",
        type=Path,
        required=True,
        help="actual translation snapshot whose bytes are bound by the freeze",
    )
    qualify.add_argument(
        "--candidate-records-dir",
        type=Path,
        required=True,
        help="actual canonical record inventory selected by the snapshot",
    )
    qualify.add_argument("--repository-root", type=Path, default=ROOT)
    qualify.add_argument("--output", type=Path)
    return parser


def _load_freeze(path: Path, where: str) -> dict[str, Any]:
    try:
        value = load_strict(path)
    except OSError as exc:
        raise RecordError(f"cannot read {where}: {exc}") from exc
    if type(value) is not dict:
        raise RecordError(f"{where} must contain a JSON object")
    return validate_freeze_record(value)


def _emit(record: dict[str, Any], output: Path | None) -> None:
    payload = canonical_bytes(record) + b"\n"
    if output is None:
        sys.stdout.buffer.write(payload)
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError as exc:
        raise RecordError(f"refusing to overwrite existing output: {output}") from exc
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        try:
            output.unlink()
        except OSError:
            pass
        raise
    print(str(output))


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "freeze-report":
            _report, result = freeze_exposure_report(args.report)
        elif args.command == "freeze-snapshot":
            _snapshot, result = freeze_translation_snapshot(
                args.snapshot, args.records_dir
            )
        else:
            report_freeze = _load_freeze(args.freeze, "report freeze")
            candidate_freeze = _load_freeze(
                args.candidate_freeze, "candidate snapshot freeze"
            )
            result = qualify_exposure_report(
                report_path=args.report,
                report_freeze=report_freeze,
                repository_root=args.repository_root,
                candidate_snapshot_freeze=candidate_freeze,
                candidate_snapshot_path=args.candidate_snapshot,
                candidate_records_dir=args.candidate_records_dir,
            )
        _emit(result, args.output)
        if (
            args.command == "qualify-report"
            and result["qualification_status"] != ALL_REPRODUCED
        ):
            return QUALIFICATION_MISMATCH_EXIT_CODE
        return 0
    except (CREIBError, OSError, TypeError, ValueError) as exc:
        exit_code = exc.exit_code if isinstance(exc, CREIBError) else 1
        error = {
            "qualification_status": "QUALIFICATION_INPUT_INVALID",
            "automatic_semantic_effect": "NONE",
            "semantic_verdict": None,
            "translation_fidelity_verdict": None,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "exit_code": exit_code,
        }
        sys.stderr.buffer.write(canonical_bytes(error) + b"\n")
        return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
