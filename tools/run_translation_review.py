#!/usr/bin/env python3
"""Publish and verify explicit human translation-review lineages."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from creib.canonical import canonical_bytes  # noqa: E402
from creib.errors import CREIBError  # noqa: E402
from creib.forge.translation_review import (  # noqa: E402
    TranslationReviewError,
    load_translation_inputs,
    load_translation_review,
    publish_translation_review,
    translation_review_bindings,
    translation_review_surface,
    verify_translation_review_chain,
)


DEFAULT_REVIEW_DIR = ROOT / "forge" / "translation" / "reviews"


def _inputs(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument(
        "--interpretation-set",
        dest="interpretation_sets",
        action="append",
        type=Path,
        required=True,
        help="repeat once for every interpretation set named by the snapshot",
    )
    parser.add_argument("--review-dir", type=Path, default=DEFAULT_REVIEW_DIR)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Preserve fallible source-to-model review without treating human "
            "selection, formal success, or agreement as semantic confirmation"
        )
    )
    commands = parser.add_subparsers(dest="command", required=True)

    publish = commands.add_parser(
        "publish", help="publish one claim-first, no-clobber review successor"
    )
    _inputs(publish)
    publish.add_argument("--review", type=Path, required=True)
    publish.add_argument("--expected-head-review-id")

    verify = commands.add_parser(
        "verify", help="verify one explicitly selected terminal review head"
    )
    _inputs(verify)
    verify.add_argument("--head-review-id")

    surface = commands.add_parser(
        "surface", help="derive the exact source, rival, and model-effect review surface"
    )
    _inputs(surface)
    return parser


def _publish(args: argparse.Namespace) -> dict[str, object]:
    snapshot, sets = load_translation_inputs(args.snapshot, args.interpretation_sets)
    review = load_translation_review(args.review)
    path = publish_translation_review(
        args.review_dir,
        review,
        expected_head_review_id=args.expected_head_review_id,
        snapshot=snapshot,
        interpretation_sets=sets,
    )
    return {
        "publication_status": "CREATED_NO_CLOBBER",
        "review_id": review["review_id"],
        "review_path": str(path),
        "workflow_status": verify_translation_review_chain(
            args.review_dir,
            str(review["review_id"]),
            expected_bindings=translation_review_bindings(snapshot),
            expected_surface=translation_review_surface(snapshot, sets),
        ).workflow_status,
        "semantic_verdict": None,
    }


def _verify(args: argparse.Namespace) -> dict[str, object]:
    snapshot, sets = load_translation_inputs(args.snapshot, args.interpretation_sets)
    state = verify_translation_review_chain(
        args.review_dir,
        args.head_review_id,
        expected_bindings=translation_review_bindings(snapshot)
        if args.head_review_id is not None
        else None,
        expected_surface=translation_review_surface(snapshot, sets)
        if args.head_review_id is not None
        else None,
    )
    return {
        "verification_status": "INTRINSIC_CHAIN_INTEGRITY_VALID",
        "head_review_id": state.head_review_id,
        "review_count": len(state.reviews),
        "workflow_status": state.workflow_status,
        "current_decision_id": state.current_decision_id,
        "reviewer_authentication": state.reviewer_authentication,
        "current_scope_binding": state.current_scope_binding,
        "authorized_variants": list(state.authorized_variants),
        "effective_branch_states": state.effective_branch_states,
        "epistemic_status": "UNRESOLVED",
        "semantic_verdict": None,
        "epistemic_effect": "INTEGRITY_AND_WORKFLOW_RESOLUTION_ONLY",
    }


def _surface(args: argparse.Namespace) -> dict[str, object]:
    snapshot, sets = load_translation_inputs(args.snapshot, args.interpretation_sets)
    return {
        "bindings": translation_review_bindings(snapshot),
        "review_surface": translation_review_surface(snapshot, sets),
        "authorization": None,
        "semantic_verdict": None,
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "publish":
            result = _publish(args)
        elif args.command == "verify":
            result = _verify(args)
        else:
            result = _surface(args)
        print(canonical_bytes(result).decode("utf-8"))
        return 0
    except CREIBError as exc:
        code = getattr(exc, "error_code", exc.__class__.__name__)
        print(
            canonical_bytes(
                {
                    "error": str(exc),
                    "error_code": code,
                    "semantic_verdict": None,
                }
            ).decode("utf-8"),
            file=sys.stderr,
        )
        return exc.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
