#!/usr/bin/env python3
"""Plan and preserve additive Semantic Model Forge inquiry events."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from creib.canonical import canonical_bytes  # noqa: E402
from creib.errors import CREIBError  # noqa: E402
from creib.strict_json import loads_strict  # noqa: E402
from creib.forge.inquiry import (  # noqa: E402
    InquiryError,
    build_adaptive_inquiry_plan,
    build_inquiry_event,
    dumps_adaptive_inquiry_plan,
    load_human_triage,
    load_research_ledger_binding,
    loads_adaptive_inquiry_plan,
    publish_inquiry_event,
    validate_adaptive_inquiry_plan_against_inputs,
    validate_inquiry_question_against_plan,
    validate_inquiry_transition_against_plan,
    verify_inquiry_chain,
)


DEFAULT_LEDGER = ROOT / "forge" / "research" / "SMF-RESEARCH-2026-09-03.json"


def _base(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--research-ledger", type=Path, default=DEFAULT_LEDGER)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Route exact semantic-forge criticism candidates without treating "
            "research, agreement, or test survival as confirmation"
        )
    )
    commands = parser.add_subparsers(dest="command", required=True)

    plan = commands.add_parser("plan", help="build an exact adaptive inquiry plan")
    _base(plan)
    plan.add_argument("--run-record", type=Path, required=True)
    plan.add_argument(
        "--triage",
        type=Path,
        help="separately supplied human triage record; omitted means fail closed",
    )
    plan.add_argument("--events-dir", type=Path)
    plan.add_argument("--head-event-id")

    verify = commands.add_parser("verify", help="verify one explicitly selected event chain")
    _base(verify)
    verify.add_argument("--events-dir", type=Path, required=True)
    verify.add_argument("--head-event-id", required=True)

    append = commands.add_parser("append", help="append one no-clobber inquiry transition")
    _base(append)
    append.add_argument(
        "--run-record",
        type=Path,
        required=True,
        help="current exact calibration record from which the supplied plan originated",
    )
    append.add_argument("--events-dir", type=Path, required=True)
    append.add_argument("--expected-head-event-id")
    append.add_argument("--plan", type=Path, required=True)
    append.add_argument("--question-id", required=True)
    append.add_argument(
        "--event-type",
        required=True,
        choices=(
            "QUESTION_PROPOSED",
            "QUESTION_ACTIVATED",
            "RESEARCH_CANDIDATE_RECORDED",
            "HUMAN_CRITICISM_RETAINED",
            "HUMAN_NONDISCRIMINATING",
            "HUMAN_MISFRAMED",
            "HUMAN_OUT_OF_SCOPE",
            "MODEL_CHANGED",
        ),
    )
    append.add_argument(
        "--actor-kind",
        required=True,
        choices=("MACHINE", "HUMAN", "OPERATOR"),
    )
    append.add_argument("--occurred-on", required=True)
    append.add_argument("--reason-code", required=True)
    append.add_argument("--reason", required=True)
    append.add_argument(
        "--research-entry",
        type=Path,
        help=(
            "exact standalone v2 source-entry snapshot produced after the active "
            "question; it need not be pre-seeded in the background ledger"
        ),
    )
    return parser


def _read_text(path: Path, where: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise InquiryError("INQUIRY_INPUT_READ_FAILED", f"cannot read {where}: {exc}") from exc


def _plan_command(args: argparse.Namespace) -> dict[str, object]:
    triage = None if args.triage is None else load_human_triage(args.triage)
    return build_adaptive_inquiry_plan(
        repo_root=args.repo_root,
        run_record_path=args.run_record,
        research_ledger_path=args.research_ledger,
        triage=triage,
        events_dir=args.events_dir,
        head_event_id=args.head_event_id,
    )


def _verify_command(args: argparse.Namespace) -> dict[str, object]:
    ledger, binding = load_research_ledger_binding(args.research_ledger)
    state = verify_inquiry_chain(
        args.events_dir,
        args.head_event_id,
        research_ledger=ledger,
        research_binding=binding,
    )
    return {
        "verification_status": "INTRINSIC_CHAIN_INTEGRITY_VALID",
        "head_event_id": state.head_event_id,
        "event_count": len(state.events),
        "question_state": {
            key: value.value for key, value in sorted(state.question_states.items())
        },
        "semantic_verdict": None,
        "epistemic_effect": "INTEGRITY_REPLAY_ONLY",
    }


def _append_command(args: argparse.Namespace) -> dict[str, object]:
    plan = loads_adaptive_inquiry_plan(_read_text(args.plan, "inquiry plan"))
    if plan["state_head_event_id"] != args.expected_head_event_id:
        raise InquiryError(
            "INQUIRY_PLAN_STALE_HEAD",
            "supplied plan was not regenerated at the caller's expected head",
        )
    validate_adaptive_inquiry_plan_against_inputs(
        plan,
        repo_root=args.repo_root,
        run_record_path=args.run_record,
        research_ledger_path=args.research_ledger,
        events_dir=args.events_dir,
    )
    validate_inquiry_transition_against_plan(args.event_type, plan)
    ledger, binding = load_research_ledger_binding(args.research_ledger)
    if plan["bindings"]["research_ledger"] != binding:  # type: ignore[index]
        raise InquiryError(
            "INQUIRY_RESEARCH_LEDGER_MISMATCH",
            "plan is not bound to the supplied research ledger",
        )
    state = verify_inquiry_chain(
        args.events_dir,
        args.expected_head_event_id,
        research_ledger=ledger,
        research_binding=binding,
    )
    if args.event_type == "QUESTION_PROPOSED":
        questions = {
            item["question_id"]: item
            for item in plan["proposed_questions"]  # type: ignore[index]
        }
        missing_message = "question ID is not currently proposed by the exact plan"
    else:
        plan_question_state = plan["question_state"]
        if args.question_id not in plan_question_state:  # type: ignore[operator]
            raise InquiryError(
                "INQUIRY_QUESTION_NOT_ACTIONABLE",
                "question ID is not recognized in the regenerated plan question_state",
            )
        questions = state.questions
        missing_message = (
            "question ID is recognized by the plan but absent from the selected event chain"
        )
    try:
        question = questions[args.question_id]
    except KeyError as exc:
        raise InquiryError(
            "INQUIRY_QUESTION_NOT_ACTIONABLE",
            missing_message,
        ) from exc
    validate_inquiry_question_against_plan(question, plan)
    current = state.question_states.get(args.question_id)
    from_state = None if current is None else current.value
    research_entry = None
    if args.research_entry is not None:
        decoded = loads_strict(_read_text(args.research_entry, "research entry"))
        if type(decoded) is not dict:
            raise InquiryError(
                "INQUIRY_RESEARCH_ENTRY_INVALID",
                "research entry must be a JSON object",
            )
        research_entry = decoded
    event = build_inquiry_event(
        sequence=len(state.events) + 1,
        previous_event_id=args.expected_head_event_id,
        event_type=args.event_type,
        occurred_on=args.occurred_on,
        actor_kind=args.actor_kind,
        question=question,
        from_state=from_state,
        reason_code=args.reason_code,
        reason=args.reason,
        research_ledger=ledger,
        research_ledger_binding=binding,
        research_entry=research_entry,
    )
    output = publish_inquiry_event(
        args.events_dir,
        event,
        expected_head_event_id=args.expected_head_event_id,
        research_ledger=ledger,
        research_binding=binding,
    )
    return {
        "publication_status": "CREATED_NO_CLOBBER",
        "event": event,
        "event_path": str(output),
        "semantic_verdict": None,
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "plan":
            result = _plan_command(args)
            print(dumps_adaptive_inquiry_plan(result))
        elif args.command == "verify":
            result = _verify_command(args)
            print(canonical_bytes(result).decode("utf-8"))
        else:
            result = _append_command(args)
            print(canonical_bytes(result).decode("utf-8"))
        return 0
    except (CREIBError, TypeError, ValueError, RecursionError) as exc:
        exit_code = exc.exit_code if isinstance(exc, CREIBError) else 1
        print(
            json.dumps(
                {
                    "operation_status": "FAILED",
                    "error_code": getattr(exc, "error_code", "INVALID_ARGUMENT"),
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "semantic_verdict": None,
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
