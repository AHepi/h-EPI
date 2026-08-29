"""Command-line entry point for read-only CR-EIB verification."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .errors import CREIBError
from .verify import verify_bundle, verify_lean, verify_pdf


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify the CR-EIB DF-10/TH-3 pilot")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--pdf", type=Path, help="optional local copy of the CR-1.0 authority PDF")
    parser.add_argument("--lean", action="store_true", help="compile the pinned Lean pilot and replay its axiom audit")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.pdf is not None:
            report, manifest, anchors = verify_bundle(args.repo_root, with_records=True)
            verify_pdf(args.pdf, manifest, anchors)
            report["authority_pdf_checked"] = True
        else:
            report = verify_bundle(args.repo_root)
        if args.lean:
            verify_lean(args.repo_root)
            report["formal_replay_checked"] = True
        report["status"] = (
            "PASS"
            if report["authority_pdf_checked"] and report["formal_replay_checked"]
            else "PARTIAL"
        )
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 0
    except CREIBError as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc), "exit_code": exc.exit_code}, sort_keys=True))
        return exc.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
