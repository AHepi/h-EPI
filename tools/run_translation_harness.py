#!/usr/bin/env python3
"""Run the fail-closed generic translation pipeline report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from creib.forge.translation_pipeline import (  # noqa: E402
    INVALID,
    READY,
    run_translation_pipeline,
)


def _source_binding(value: str) -> tuple[str, Path]:
    document_id, separator, path = value.partition("=")
    if not separator or not document_id or not path:
        raise argparse.ArgumentTypeError(
            "source binding must be DOCUMENT_ID=PATH"
        )
    return document_id, Path(path)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate every supplied translation-harness stage without "
            "claiming semantic fidelity or selecting among live criticisms"
        )
    )
    parser.add_argument("--records-dir", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument(
        "--source-document",
        action="append",
        type=_source_binding,
        default=[],
        metavar="DOCUMENT_ID=PATH",
        help="repeat once for every selected source document",
    )

    parser.add_argument("--review-dir", type=Path)
    parser.add_argument("--review-head-id")

    parser.add_argument("--old-snapshot", type=Path)
    parser.add_argument("--translation-delta", type=Path)
    parser.add_argument(
        "--inquiry-plan",
        action="append",
        type=Path,
        default=[],
        help="repeat to preserve multiple independently applicable routes",
    )

    parser.add_argument("--hardening-comparison", type=Path)
    parser.add_argument(
        "--hardening-evidence", action="append", type=Path, default=[]
    )
    parser.add_argument(
        "--hardening-decision", action="append", type=Path, default=[]
    )
    parser.add_argument("--hardening-resolution", type=Path)

    parser.add_argument("--qualification-report", type=Path)
    parser.add_argument("--qualification-report-freeze", type=Path)
    parser.add_argument("--qualification-candidate-freeze", type=Path)
    parser.add_argument(
        "--qualification-repository-root", type=Path, default=ROOT
    )
    return parser


def _emit(value: object) -> None:
    print(
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    sources: dict[str, Path] = {}
    duplicates: list[str] = []
    for document_id, path in args.source_document:
        if document_id in sources:
            duplicates.append(document_id)
        sources[document_id] = path
    if duplicates:
        _emit(
            {
                "report_type": "translation_harness_runtime_report",
                "overall_status": INVALID,
                "error": {
                    "error_type": "DuplicateSourceBinding",
                    "error": (
                        "duplicate --source-document bindings: "
                        + ", ".join(sorted(set(duplicates)))
                    ),
                },
                "next_actions": [
                    {
                        "stage": "source_identity",
                        "action": "Supply exactly one path per selected document ID.",
                    }
                ],
                "selected_route": None,
                "automatic_semantic_effect": "NONE",
                "semantic_verdict": None,
                "mapping_fidelity": "UNREVIEWED",
            }
        )
        return 2

    report = run_translation_pipeline(
        records_dir=args.records_dir,
        snapshot_path=args.snapshot,
        source_documents=sources,
        review_dir=args.review_dir,
        review_head_id=args.review_head_id,
        old_snapshot_path=args.old_snapshot,
        delta_path=args.translation_delta,
        inquiry_plan_paths=args.inquiry_plan,
        hardening_comparison_path=args.hardening_comparison,
        hardening_evidence_paths=args.hardening_evidence,
        hardening_decision_paths=args.hardening_decision,
        hardening_resolution_path=args.hardening_resolution,
        qualification_report_path=args.qualification_report,
        qualification_report_freeze_path=args.qualification_report_freeze,
        qualification_candidate_freeze_path=args.qualification_candidate_freeze,
        qualification_repository_root=args.qualification_repository_root,
    )
    _emit(report)
    if report["overall_status"] == READY:
        return 0
    if report["overall_status"] == INVALID:
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
