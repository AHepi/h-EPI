#!/usr/bin/env python3
"""CONSTRUCT-TEST-1: run the conditions and the controls, and read what changed.

    python tools/construct_test.py controls --out forge/construct/runs/<block>
    python tools/construct_test.py run --plan <plan.json> --out forge/construct/runs/<block>
    python tools/construct_test.py read --root forge/construct/runs/<block>

The protocol is ``docs/construct/CONSTRUCT_TEST.md``, pre-registered before any model was called.
Keys are read at call time from ``OLLAMA_API_KEY`` and the file named by ``DEEPSEEK_KEY_FILE``, and
appear in no record this writes.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from creib.errors import RecordError  # noqa: E402
from creib.forge.construct import lab  # noqa: E402
from creib.forge.mini.buildtest import Endpoint  # noqa: E402
from creib.forge.mini.common import MiniError  # noqa: E402
from creib.strict_json import load_strict  # noqa: E402


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def _controls(args: argparse.Namespace) -> int:
    out = Path(args.out)
    controls = [
        lab.no_return_control(args.max_starts),
        lab.corrupted_evaluator_control(args.max_starts),
    ]
    for modulus in range(1, args.max_starts):
        controls.append(lab.identity_aliasing_control(args.max_starts, modulus))
    _write(out / "controls.json", controls)
    for control in controls:
        detail = control.get("modulus")
        print(f"{control['control']}{'' if detail is None else f' M={detail}'}: held={control['held']}", flush=True)
    _write(out / "enumeration.json", lab.run_enumeration(args.max_starts, budget=0))
    _write(out / "supplied-solution.json", lab.run_supplied(args.max_starts))
    print("enumeration and supplied-solution recorded", flush=True)
    return 0


def _run(args: argparse.Namespace) -> int:
    out = Path(args.out)
    plan = load_strict(Path(args.plan))
    if type(plan) is not dict or type(plan.get("conditions")) is not list:
        raise MiniError("MINI_BUILDTEST_PLAN_INVALID", "a plan is an object carrying a list of conditions")
    for raw in plan["conditions"]:
        endpoint = Endpoint(
            path=str(raw["path"]),
            model=str(raw["model"]),
            think=raw.get("think"),
            timeout_seconds=int(raw.get("timeout_seconds", 900)),
            max_tokens=raw.get("max_tokens"),
        )
        condition = str(raw["condition"])
        name = f"{endpoint.path}__{endpoint.model}__{condition}".replace("/", "_")
        target = out / f"{name}.json"
        if target.exists() and not args.overwrite:
            print(f"{name}: already recorded, skipped", flush=True)
            continue
        record = lab.run_model(condition, endpoint, args.max_starts, int(raw.get("budget", 8)))
        record["endpoint"] = endpoint.to_dict()
        _write(target, record)
        after = record["after"]
        print(
            f"{name}: {len(record['proposals'])} proposals, {record['accepted_proposals']} accepted, "
            f"installed {record['installed_program']!r}, violations {after['violations']}/{after['cases']}",
            flush=True,
        )
    return 0


def _read(args: argparse.Namespace) -> int:
    root = Path(args.root)
    rows = []
    for path in sorted(root.glob("*.json")):
        if path.name in ("controls.json", "reading.json"):
            continue
        record = load_strict(path)
        endpoint = record.get("endpoint") or {}
        rows.append({
            "condition": record["condition"],
            "path": endpoint.get("path", "-"),
            "model": endpoint.get("model", "(none)"),
            "proposals": len(record["proposals"]),
            "accepted": record["accepted_proposals"],
            "installed": record["installed_program"],
            "violations": record["after"]["violations"],
            "cases": record["after"]["cases"],
            "accepted_obsolete": record["after"]["accepted_obsolete_result"],
            "missed_current": record["after"]["missed_current_result"],
            "calls": len(record["calls"]),
            "completion_tokens": sum(int(c.get("completion_tokens", 0)) for c in record["calls"]),
        })
    _write(root / "reading.json", rows)
    print(f"{'condition':<18} {'model':<22} {'prop':>4} {'acc':>4} {'viol':>5} {'tokens':>7}  installed", flush=True)
    for row in rows:
        print(
            f"{row['condition']:<18} {row['model']:<22} {row['proposals']:>4} {row['accepted']:>4} "
            f"{row['violations']:>5} {row['completion_tokens']:>7}  {row['installed']}",
            flush=True,
        )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    controls = sub.add_parser("controls", help="run every control and the two non-model conditions")
    controls.add_argument("--out", required=True)
    controls.add_argument("--max-starts", type=int, default=4)
    controls.set_defaults(handler=_controls)
    runner = sub.add_parser("run", help="run the model conditions of a plan")
    runner.add_argument("--plan", required=True)
    runner.add_argument("--out", required=True)
    runner.add_argument("--max-starts", type=int, default=4)
    runner.add_argument("--overwrite", action="store_true")
    runner.set_defaults(handler=_run)
    reader = sub.add_parser("read", help="read a block without a person")
    reader.add_argument("--root", required=True)
    reader.set_defaults(handler=_read)
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except (MiniError, RecordError) as error:
        sys.stderr.write(f"{error}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
