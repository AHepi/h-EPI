#!/usr/bin/env python3
"""Single entry point for every repository check.

CI, the SessionStart hook, the publish skill, README, and CLAUDE.md all call
this script so the check list exists in exactly one place. Each target runs
a fixed command set and fails closed on the first failure. A green run
establishes structural and deterministic behaviour only; it confirms
nothing about any model.

Targets:
  bootstrap   create .venv with Python 3.12 and the hash-locked dependencies
  lint        compileall, shipped-code assert guard, whitespace check
  test        the complete unittest suite (offline; no model calls)
  pilots      validate and plan every pilot under forge/conformance/pilots
  all         lint, test, pilots

Standard library only.
"""

from __future__ import annotations

import argparse
import ast
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PILOTS = ROOT / "forge" / "conformance" / "pilots"


def _env() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src")
    return env


def _run(command: list[str]) -> None:
    print("+", " ".join(command), flush=True)
    completed = subprocess.run(command, cwd=ROOT, env=_env())
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def assert_guard() -> None:
    """Fail if shipped code contains ``assert``.

    Shipped checks must survive ``python -O``, so they are explicit
    ``if ...: raise`` statements. This makes that a checked invariant.
    """

    offenders: list[str] = []
    for directory in ("src", "tools"):
        for path in sorted((ROOT / directory).rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            offenders.extend(f"{path.relative_to(ROOT)}:{node.lineno}" for node in ast.walk(tree) if isinstance(node, ast.Assert))
    if offenders:
        print("assert statements in shipped code:", file=sys.stderr)
        for offender in offenders:
            print(f"  {offender}", file=sys.stderr)
        raise SystemExit(1)
    print("assert guard: no assert statements in src/ or tools/")


def whitespace_check() -> None:
    if shutil.which("git") is None or not (ROOT / ".git").exists():
        print("whitespace check skipped: not a git checkout")
        return
    _run(["git", "diff", "--check", "HEAD"])


def target_bootstrap(args: argparse.Namespace) -> None:
    venv = ROOT / ".venv"
    interpreter = shutil.which("python3.12") or shutil.which("python3")
    if interpreter is None:
        raise SystemExit("no python3 interpreter found")
    if not venv.exists():
        _run([interpreter, "-m", "venv", str(venv)])
    python = str(venv / "bin" / "python")
    _run([python, "--version"])
    _run([python, "-m", "pip", "install", "--quiet", "--no-deps", "--only-binary=:all:", "--require-hashes",
          "-r", str(ROOT / "requirements-container.txt")])
    print(f"bootstrap complete: {venv}/bin/python with PYTHONPATH={ROOT / 'src'}")


def target_lint(args: argparse.Namespace) -> None:
    _run([sys.executable, "-m", "compileall", "-q", "src", "tools", "tests"])
    assert_guard()
    whitespace_check()


def target_test(args: argparse.Namespace) -> None:
    _run([sys.executable, "-m", "unittest", "discover", "-s", "tests", *(["-v"] if args.verbose else [])])


def target_pilots(args: argparse.Namespace) -> None:
    import json

    tool = str(ROOT / "tools" / "run_conformance_pilot.py")
    pilots = sorted(PILOTS.glob("*/pilot.json"))
    if not pilots:
        raise SystemExit(f"no pilot.json under {PILOTS}")
    for pilot in pilots:
        for command in ("validate", "plan"):
            completed = subprocess.run(
                [sys.executable, tool, command, "--pilot", str(pilot)], cwd=ROOT, env=_env(), capture_output=True, text=True
            )
            if completed.returncode != 0:
                print(completed.stdout, completed.stderr, file=sys.stderr)
                raise SystemExit(completed.returncode)
            payload = json.loads(completed.stdout)
            if command == "plan":
                print(f"{pilot.parent.name}: validated; plan {payload['plan_id'][:16]}… with {payload['variant_count']} variants ({payload['model_call_variant_count']} model calls)")


def target_all(args: argparse.Namespace) -> None:
    target_lint(args)
    target_test(args)
    target_pilots(args)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("target", choices=["bootstrap", "lint", "test", "pilots", "all"])
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)
    {"bootstrap": target_bootstrap, "lint": target_lint, "test": target_test, "pilots": target_pilots, "all": target_all}[args.target](args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
