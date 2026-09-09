#!/usr/bin/env python3
"""Command line for the mini prototype: compile a manifest, run it, replay it.

    python tools/run_mini.py compile --manifest forge/mini/manifests/default/manifest.json
    python tools/run_mini.py run     --manifest … --script … --output-dir …
    python tools/run_mini.py replay  --root <a run root>

No model is called by any of these. ``run`` drives the scripted responder, so
the replies come from the script file and nothing leaves the machine.

Standard library plus the package; ``PYTHONPATH=src``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from creib.errors import CREIBError
from creib.strict_json import load_strict
from creib.forge.mini.executor import ScriptedResponder
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
    script = load_strict(Path(args.script))
    outcome = run_mini(plan, Path(args.output_dir), ScriptedResponder(script))
    print(
        json.dumps(
            {
                "run_id": outcome.run_id,
                "root": str(outcome.root),
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
    replay_parser = sub.add_parser("replay")
    replay_parser.add_argument("--root", required=True)
    replay_parser.set_defaults(run=target_replay)
    args = parser.parse_args(argv)
    try:
        return args.run(args)
    except CREIBError as error:
        print(str(error), file=sys.stderr)
        return error.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
