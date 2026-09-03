#!/usr/bin/env python3
"""Run the deterministic SMF-0.1 first calibration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from creib.errors import CREIBError, RecordError  # noqa: E402
from creib.forge.calibration import (  # noqa: E402
    CANDIDATE_ID,
    CalibrationRunError,
    NAIVE_REVISION_ID,
    ROLE_CHALLENGE_ID,
    ROLE_ISSUE_ID,
    dumps_calibration_report,
    publish_calibration_report,
    replay_calibration_report,
    run_first_calibration,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Verify the CR-1.0 authority and run the non-authoritative "
            "semantic-forge calibration fixture"
        )
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=("first-run", "replay"),
        default="first-run",
    )
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument(
        "--authority",
        "--pdf",
        dest="pdf",
        type=Path,
        required=True,
        help="local copy of the exact CR-1.0 authority PDF",
    )
    parser.add_argument(
        "--corpus",
        type=Path,
        default=ROOT / "forge" / "corpus" / "cr-1.0-seed.json",
    )
    parser.add_argument("--challenge", default=ROLE_CHALLENGE_ID)
    parser.add_argument("--research-issue", default=ROLE_ISSUE_ID)
    parser.add_argument("--candidate", default=CANDIDATE_ID)
    parser.add_argument("--revision", default=NAIVE_REVISION_ID)
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "also create this run-record file; creation is exclusive so an "
            "existing record is never overwritten"
        ),
    )
    parser.add_argument(
        "--run-record",
        type=Path,
        help="canonical persisted run record to verify with the replay command",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        expected_selections = {
            "challenge": ROLE_CHALLENGE_ID,
            "research_issue": ROLE_ISSUE_ID,
            "candidate": CANDIDATE_ID,
            "revision": NAIVE_REVISION_ID,
        }
        for field, expected in expected_selections.items():
            if getattr(args, field) != expected:
                raise ValueError(
                    f"SMF-0.1 first-run requires {field.replace('_', '-')} {expected!r}"
                )
        if args.command == "replay":
            if args.run_record is None:
                raise CalibrationRunError(
                    "RUN_RECORD_REQUIRED",
                    "the replay command requires --run-record",
                )
            if args.output is not None:
                raise CalibrationRunError(
                    "REPLAY_OUTPUT_FORBIDDEN",
                    "the replay command does not create a replacement run record",
                )
            report = replay_calibration_report(
                args.run_record,
                repo_root=args.repo_root,
                pdf_path=args.pdf,
                corpus_path=args.corpus,
            )
        else:
            if args.run_record is not None:
                raise CalibrationRunError(
                    "RUN_RECORD_OPTION_FORBIDDEN",
                    "--run-record is only valid with the replay command",
                )
            try:
                report = run_first_calibration(
                    repo_root=args.repo_root,
                    pdf_path=args.pdf,
                    corpus_path=args.corpus,
                )
            except OSError as exc:
                raise CalibrationRunError(
                    "INPUT_OUTPUT_FAILED",
                    "semantic-forge input/output failed",
                ) from exc
            except RecursionError as exc:
                raise CalibrationRunError(
                    "INPUT_NESTING_EXCEEDED",
                    "semantic-forge input nesting exceeds the supported depth",
                ) from exc
        serialized = dumps_calibration_report(report, repo_root=args.repo_root)
        if args.output is not None:
            publish_calibration_report(
                args.output,
                report,
                repo_root=args.repo_root,
            )
        print(serialized)
        return 0
    except (CREIBError, TypeError, ValueError) as exc:
        exit_code = exc.exit_code if isinstance(exc, CREIBError) else 1
        print(
            json.dumps(
                {
                    "run_status": "RUN_FAILED",
                    "result_scope": "OPERATIONAL_FAILURE_ONLY",
                    "semantic_verdict": None,
                    "human_disposition": None,
                    "error_code": getattr(
                        exc,
                        "error_code",
                        "SEMANTIC_FORGE_RECORD_ERROR"
                        if isinstance(exc, CREIBError)
                        else "INVALID_ARGUMENT",
                    ),
                    "error_type": type(exc).__name__,
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
