#!/usr/bin/env python3
"""Run the SMF-0.5 task-conformance pilot without ever confirming a model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from creib.errors import CREIBError, RecordError  # noqa: E402
from creib.forge.conformance.common import publish_no_clobber  # noqa: E402
from creib.forge.conformance.corpus import load_corpus  # noqa: E402
from creib.forge.conformance.executor import CannedExecutor, OllamaChatExecutor, ReplayExecutor  # noqa: E402
from creib.forge.conformance.families import Family, plan as build_plan  # noqa: E402
from creib.forge.conformance.oracle import score  # noqa: E402
from creib.forge.conformance.records import load_observation_directory, load_run  # noqa: E402
from creib.forge.conformance.report import build_report, render_markdown  # noqa: E402
from creib.forge.conformance.routing import route  # noqa: E402
from creib.forge.conformance.runner import run_pilot  # noqa: E402
from creib.forge.conformance.spec import load_pilot_config  # noqa: E402


def _emit(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Point the criticism-first method at form filling by an LLM: validate a pilot, "
            "plan its variants, check the oracle's non-vacuity, run one model, and report "
            "plural verdicts for human triage"
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="load config, spec, and corpus; print bindings and obligations")
    validate.add_argument("--pilot", type=Path, required=True)

    plan = subparsers.add_parser("plan", help="print variant counts per family and the plan_id; no model calls")
    plan.add_argument("--pilot", type=Path, required=True)

    oracle_check = subparsers.add_parser("oracle-check", help="run only the model-free NON_VACUITY controls")
    oracle_check.add_argument("--pilot", type=Path, required=True)

    run = subparsers.add_parser("run", help="execute variants for one model and publish records")
    run.add_argument("--pilot", type=Path, required=True)
    run.add_argument("--model", required=True)
    run.add_argument("--family", action="append", choices=[family.value for family in Family], default=None)
    run.add_argument("--limit", type=int, default=None)
    run.add_argument("--output-dir", type=Path, required=True)
    run.add_argument("--created-on", required=True, help="RFC 3339 timestamp recorded verbatim")
    run.add_argument("--dry-run", action="store_true", help="use the canned executor; no network")
    run.add_argument(
        "--replay-dir",
        type=Path,
        help="re-score from the responses recorded in this observations directory, matched by request digest; no network. "
        "Use it after correcting an oracle: the recorded replies are scored again and new records are written to --output-dir",
    )
    run.add_argument("--retries", type=int, default=0)

    fills = subparsers.add_parser("fills", help="print the filled forms from recorded observations (what the model actually returned)")
    fills.add_argument("--observations-dir", type=Path, required=True)
    fills.add_argument("--run", type=Path, help="restrict to one run record")
    fills.add_argument("--family", default="BASELINE", choices=[family.value for family in Family] + ["ALL"])
    evidence = subparsers.add_parser("evidence", help="list observation ids per model and criticism trigger, for the failure-mode register")
    evidence.add_argument("--observations-dir", type=Path, required=True)
    evidence.add_argument("--trigger", help="restrict to one trigger or grounding verdict")
    report = subparsers.add_parser("report", help="aggregate run records into an unranked report")
    report.add_argument("--run", type=Path, action="append", required=True)
    report.add_argument("--observations-dir", type=Path, required=True)
    report.add_argument("--markdown", type=Path, default=None)
    return parser


def _load(pilot_path: Path):
    config = load_pilot_config(pilot_path)
    corpus = load_corpus(config.corpus_path, config.spec)
    return config, corpus


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "validate":
            config, corpus = _load(args.pilot)
            spec = config.spec
            _emit(
                {
                    "pilot_id": spec.pilot_id,
                    "title": spec.title,
                    "source_bindings": spec.bindings_dict(),
                    "corpus": {
                        "corpus_id": corpus.corpus_id,
                        "sha256": corpus.sha256,
                        "case_count": len(corpus.cases),
                        "boundary_case_count": len(corpus.boundary_cases),
                        "pairs": [[a.case_id, b.case_id] for a, b in corpus.pairs()],
                    },
                    "models": list(spec.models),
                    "endpoint": spec.endpoint.to_dict(),
                    "obligations": [obligation.to_dict() for obligation in spec.obligations],
                    "load_bearing": list(spec.load_bearing),
                    "charter": spec.charter.to_dict(),
                    "semantic_verdict": None,
                }
            )
            return 0
        if args.command == "plan":
            config, corpus = _load(args.pilot)
            built = build_plan(config.spec, corpus)
            _emit(
                {
                    "pilot_id": built.pilot_id,
                    "plan_id": built.plan_id,
                    "corpus_sha256": built.corpus_sha256,
                    "counts": {family: count for family, count in built.counts},
                    "variant_count": len(built.variants),
                    "model_call_variant_count": sum(1 for variant in built.variants if variant.model_call),
                    "semantic_verdict": None,
                }
            )
            return 0
        if args.command == "oracle-check":
            config, corpus = _load(args.pilot)
            built = build_plan(config.spec, corpus)
            results = []
            unresolved = False
            for variant in built.variants:
                if variant.family is not Family.NON_VACUITY:
                    continue
                scoring = score(variant, None)
                routing = route(variant, scoring, format_sent=False)
                unresolved = unresolved or bool(routing.live_loci)
                results.append(
                    {
                        "variant_id": variant.variant_id,
                        "case_id": variant.base_case_id,
                        "control_id": variant.control_id,
                        "expectation_kind": variant.expectation_kind.value,
                        "response_verdict": scoring.response_verdict,
                        "schema_valid": scoring.schema_valid,
                        "field_verdicts": {verdict.field: verdict.verdict for verdict in scoring.field_verdicts},
                        "triggers": list(routing.triggers),
                        "live_loci": routing.to_dict()["live_loci"],
                    }
                )
            _emit({"pilot_id": built.pilot_id, "plan_id": built.plan_id, "controls": results, "unresolved": unresolved, "semantic_verdict": None})
            return 0
        if args.command == "run":
            config, corpus = _load(args.pilot)
            spec = config.spec
            built = build_plan(spec, corpus)
            families = None if args.family is None else tuple(Family(name) for name in args.family)
            if args.dry_run and args.replay_dir is not None:
                raise RecordError("--dry-run and --replay-dir are exclusive")
            if args.dry_run:
                executor = CannedExecutor()
                executor_kind = "canned"
            elif args.replay_dir is not None:
                executor = ReplayExecutor(args.replay_dir)
                executor_kind = "replay"
            else:
                executor = OllamaChatExecutor(
                    base_url=spec.endpoint.base_url,
                    timeout_seconds=spec.endpoint.timeout_seconds,
                    retries=args.retries,
                    auth=spec.endpoint.auth,
                )
                executor_kind = "ollama-chat"
            result = run_pilot(
                spec=spec,
                corpus=corpus,
                plan=built,
                model=args.model,
                executor=executor,
                executor_kind=executor_kind,
                output_dir=args.output_dir,
                created_on=args.created_on,
                families=families,
                limit=args.limit,
            )
            record = result.run_record
            _emit(
                {
                    "run_record_path": str(result.run_path),
                    "run_id": record.run_id,
                    "model": record.model,
                    "observation_count": len(result.observations),
                    "observations_with_live_loci": record.observations_with_live_loci,
                    "family_counts": dict(record.family_counts),
                    "response_verdict_counts": dict(record.response_verdict_counts),
                    "field_verdict_counts": dict(record.field_verdict_counts),
                    "live_locus_counts": dict(record.live_locus_counts),
                    "scope_label": record.scope_label,
                    "overall_status": record.overall_status,
                    "route": record.route,
                    "format_enforced_by_server": record.format_enforced_by_server,
                    "epistemic_limit": record.epistemic_limit,
                    "semantic_verdict": None,
                }
            )
            return 1 if result.unresolved else 0
        if args.command == "fills":
            observations = load_observation_directory(args.observations_dir)
            if args.run is not None:
                run_id = load_run(args.run).run_id
                observations = [o for o in observations if o.run_id == run_id]
            if args.family != "ALL":
                observations = [o for o in observations if o.variant.family.value == args.family]
            structural = {"MISSING_REQUIRED", "EXTRA_FIELD", "TYPE_VIOLATION", "PATTERN_VIOLATION", "ENUM_VIOLATION", "LENGTH_VIOLATION"}
            for observation in sorted(observations, key=lambda o: (o.model, o.variant.base_case_id, o.variant.family.value)):
                scoring = observation.scoring
                companions = set(observation.variant.span_keys)
                filled = None if scoring.parsed_output is None else {k: v for k, v in scoring.parsed_output.items() if k not in companions}
                _emit({
                    "case_id": observation.variant.base_case_id,
                    "model": observation.model,
                    "family": observation.variant.family.value,
                    "response_verdict": scoring.response_verdict,
                    "filled_form": filled,
                    "grounding": [{"field": g.field, "verdict": g.verdict, "span": g.span} for g in scoring.grounding_verdicts],
                    "abstained_fields": [g.field for g in scoring.grounding_verdicts if g.verdict == "ABSTAINED"],
                    "structural_issues": [
                        {"field": v.field, "issue": v.verdict} for v in scoring.field_verdicts if v.verdict in structural
                    ],
                    "judged_against_answer_key": [
                        {"field": v.field, "verdict": v.verdict} for v in scoring.field_verdicts if v.verdict in ("MATCH", "MISMATCH", "UNEXPECTED_PRESENT")
                    ],
                    "unjudged_fields": [v.field for v in scoring.field_verdicts if v.verdict == "NOT_SCORED"],
                    "live_loci": list(observation.routing.loci),
                    "observation_id": observation.observation_id,
                })
            return 0
        if args.command == "evidence":
            observations = load_observation_directory(args.observations_dir)
            rows: dict[tuple[str, str], list[dict[str, object]]] = {}
            for observation in observations:
                keys = list(observation.routing.triggers) + [f"GROUNDING:{g.verdict}" for g in observation.scoring.grounding_verdicts]
                for key in keys:
                    if args.trigger is not None and key != args.trigger:
                        continue
                    rows.setdefault((observation.model, key), []).append(
                        {"observation_id": observation.observation_id, "case_id": observation.variant.base_case_id, "family": observation.variant.family.value}
                    )
            for (model, key), items in sorted(rows.items()):
                _emit({"model": model, "trigger": key, "count": len(items), "observations": sorted(items, key=lambda i: (i["case_id"], i["family"]))})
            return 0
        if args.command == "report":
            runs = [load_run(path) for path in args.run]
            observations = load_observation_directory(args.observations_dir)
            report = build_report(runs, observations)
            if args.markdown is not None:
                publish_no_clobber(args.markdown, render_markdown(report).encode("utf-8"))
            _emit(report)
            return 0
        raise RecordError(f"unknown command {args.command!r}")
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
