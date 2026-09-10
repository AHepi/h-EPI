#!/usr/bin/env python3
"""Command line for the mini prototype: compile a manifest, run it, replay it.

    python tools/run_mini.py compile --manifest forge/mini/manifests/default/manifest.json
    python tools/run_mini.py run     --manifest … --script … --output-dir …
    python tools/run_mini.py replay  --root <a run root>
    python tools/run_mini.py live    --manifest … --model … --output-dir …
    python tools/run_mini.py compare --root <a run root> --root <another>

Only ``live`` calls a model. ``run`` drives the scripted responder, so the
replies come from the script file and nothing leaves the machine. ``live``
reads the key from ``OLLAMA_API_KEY`` at call time through the conformance
harness's own executor; it costs money and writes records meant to be kept.

Standard library plus the package; ``PYTHONPATH=src``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from creib.errors import CREIBError
from creib.strict_json import load_strict
from creib.forge.mini import conformance_kernels  # noqa: F401  registers the conformance harness's checks as kernels
from creib.forge.mini.executor import LiveResponder, ScriptedResponder
from creib.forge.mini.compare import UNSUPPORTED, compare_roots
from creib.forge.mini.common import MiniError, digest_bytes
from creib.forge.mini.log import LOG_NAME, replay
from creib.forge.mini.manifest import compile_manifest
from creib.forge.mini.runner import run_mini


def _plan_summary(plan) -> dict[str, object]:
    return {
        "manifest_id": plan.manifest_id,
        "run_id": plan.run_id,
        "genesis": plan.genesis,
        "kinds": sorted(plan.kinds),
        "port_types": sorted(plan.port_types),
        "tiers": list(plan.tiers),
        "stages": [stage.to_dict() for stage in plan.stages],
        "policy_id": plan.policy.policy_id,
        "policy_grants": [grant.to_dict() for grant in plan.policy.grants],
        "attention_policy": plan.attention.policy_id,
        "formats": {kind_id: list(compiled.describe()) for kind_id, compiled in plan.formats.items()},
        "sources": [source.to_dict() for source in plan.sources],
    }


def target_compile(args: argparse.Namespace) -> int:
    plan = compile_manifest(Path(args.manifest))
    print(json.dumps(_plan_summary(plan), ensure_ascii=False, sort_keys=True, indent=2))
    return 0


def target_run(args: argparse.Namespace) -> int:
    plan = compile_manifest(Path(args.manifest))
    script_path = Path(args.script)
    script = load_strict(script_path)
    responder_id = f"script:{digest_bytes(script_path.read_bytes())[:16]}"
    outcome = run_mini(plan, Path(args.output_dir), ScriptedResponder(script), responder_id)
    print(
        json.dumps(
            {
                "run_id": outcome.run_id,
                "root": str(outcome.root),
                "stop_reason": outcome.stop_reason,
                "cycles_completed": outcome.cycles_completed,
                "stages_entered": list(outcome.stages_entered),
                "state_digest": outcome.state_digest,
            },
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
    )
    return 0


def target_compare(args: argparse.Namespace) -> int:
    if getattr(args, "score", False):
        raise MiniError(
            UNSUPPORTED,
            "compare computes no score. A template's own verdict counts are not a measure of a run, "
            "and nothing here may be tuned to raise one.",
        )
    print(compare_roots(Path(args.root[0]), Path(args.root[1])))
    return 0


def target_live(args: argparse.Namespace) -> int:
    plan = compile_manifest(Path(args.manifest))
    responder = LiveResponder(args.model, timeout_seconds=args.timeout_seconds, retries=args.retries)
    outcome = run_mini(plan, Path(args.output_dir), responder, f"model:{args.model}")
    print(
        json.dumps(
            {
                "run_id": outcome.run_id,
                "model": args.model,
                "timeout_seconds": args.timeout_seconds,
                "root": str(outcome.root),
                "calls": responder.calls,
                "stop_reason": outcome.stop_reason,
                "stages_entered": list(outcome.stages_entered),
                "state_digest": outcome.state_digest,
            },
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
    )
    return 0


def target_replay(args: argparse.Namespace) -> int:
    root = Path(args.root)
    header = load_strict(root / "run-header.json")
    from creib.forge.mini.common import RUN_HEADER_DOMAIN, content_id

    genesis = content_id(RUN_HEADER_DOMAIN, header)
    state = replay(root / LOG_NAME, genesis)
    print(
        json.dumps(
            {
                "run_id": state.run_id,
                "genesis": genesis,
                "state_digest": state.digest(),
                "stages_entered": state.stages_entered,
                "artifacts": len(state.artifact_order),
                "blocks": len(state.blocks),
                "refusals": state.refusals,
                "stop_reason": state.stop_reason,
            },
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="target", required=True)
    compile_parser = sub.add_parser("compile")
    compile_parser.add_argument("--manifest", required=True)
    compile_parser.set_defaults(run=target_compile)
    run_parser = sub.add_parser("run")
    run_parser.add_argument("--manifest", required=True)
    run_parser.add_argument("--script", required=True)
    run_parser.add_argument("--output-dir", required=True)
    run_parser.set_defaults(run=target_run)
    live_parser = sub.add_parser("live")
    live_parser.add_argument("--manifest", required=True)
    live_parser.add_argument("--model", required=True)
    live_parser.add_argument("--output-dir", required=True)
    live_parser.add_argument("--timeout-seconds", type=int, default=180)
    live_parser.add_argument("--retries", type=int, default=0)
    live_parser.set_defaults(run=target_live)
    compare_parser = sub.add_parser("compare")
    compare_parser.add_argument("--root", action="append", required=True)
    # Declared so it can be REFUSED by name rather than merely absent: a flag
    # nobody declared produces an argparse error, which is not this repository
    # saying it will not rank things.
    compare_parser.add_argument("--score", action="store_true")
    compare_parser.set_defaults(run=target_compare)
    replay_parser = sub.add_parser("replay")
    replay_parser.add_argument("--root", required=True)
    replay_parser.set_defaults(run=target_replay)
    args = parser.parse_args(argv)
    if args.target == "compare" and len(args.root) != 2:
        parser.error("compare takes exactly two --root arguments")
    try:
        return args.run(args)
    except CREIBError as error:
        print(str(error), file=sys.stderr)
        return error.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
