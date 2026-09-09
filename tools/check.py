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
  cite        every record id cited in the documents names exactly one record
  all         lint, test, pilots, cite

Standard library only.
"""

from __future__ import annotations

import argparse
import ast
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PILOTS = ROOT / "forge" / "conformance" / "pilots"
RUNS = ROOT / "forge" / "conformance" / "runs"
ARCHIVED_INDEX = ROOT / "docs" / "archived-records.txt"
CITING_FILES = ("README.md", "agent.md", "CLAUDE.md")
CITING_TREES = ("docs",)
# A record id is cited as its sixteen-hex-digit prefix in backticks; that prefix is the one a
# record file's name carries.
CITED_ID = re.compile(r"`([0-9a-f]{16})`")
# A sentence that cites a record it says was never published carries this phrase; the checker
# lists such citations instead of failing on them, so the reader sees them.
UNCOMMITTED_MARKER = "not committed"


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


def _record_locations(root: Path) -> dict[str, list[str]]:
    """Sixteen-hex prefix -> locations of the record files carrying it, in this tree and on the declared archive branches."""

    locations: dict[str, list[str]] = {}
    for path in sorted((root / "forge" / "conformance" / "runs").rglob("*.json")):
        parts = path.name.split(".")
        if len(parts) == 3 and parts[0] in ("observation", "run") and CITED_ID.fullmatch(f"`{parts[1]}`"):
            locations.setdefault(parts[1], []).append(str(path.relative_to(root)))
    index = root / ARCHIVED_INDEX.relative_to(ROOT)
    if index.exists():
        for lineno, line in enumerate(index.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip() or line.startswith("#"):
                continue
            fields = line.split()
            if len(fields) != 2:
                raise SystemExit(f"{index.relative_to(root)}:{lineno}: expected '<branch> <path>', got {line!r}")
            branch, recorded = fields
            parts = Path(recorded).name.split(".")
            if len(parts) != 3 or parts[0] not in ("observation", "run") or not CITED_ID.fullmatch(f"`{parts[1]}`"):
                raise SystemExit(f"{index.relative_to(root)}:{lineno}: {recorded!r} is not a record file name")
            locations.setdefault(parts[1], []).append(f"{branch}:{recorded}")
    return locations


def _citing_files(root: Path) -> list[Path]:
    files = [root / name for name in CITING_FILES if (root / name).exists()]
    for tree in CITING_TREES:
        files.extend(sorted((root / tree).rglob("*.md")))
    return files


def cite_check(root: Path = ROOT) -> dict[str, object]:
    """Resolve every cited record id; the result lists what resolved where, what a sentence declares uncommitted, and what fails."""

    locations = _record_locations(root)
    resolved_tree = 0
    resolved_archive = 0
    declared_uncommitted: list[str] = []
    problems: list[str] = []
    cited = 0
    for path in _citing_files(root):
        where = path.relative_to(root)
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for prefix in CITED_ID.findall(line):
                cited += 1
                hits = locations.get(prefix, [])
                if len(hits) == 1:
                    if ":" in hits[0]:
                        resolved_archive += 1
                    else:
                        resolved_tree += 1
                elif not hits:
                    if UNCOMMITTED_MARKER in line:
                        declared_uncommitted.append(f"{where}:{lineno} `{prefix}`")
                    else:
                        problems.append(f"{where}:{lineno} `{prefix}` names no record in this tree or in {ARCHIVED_INDEX.relative_to(ROOT)}")
                else:
                    problems.append(f"{where}:{lineno} `{prefix}` names {len(hits)} records: {', '.join(hits)}")
    return {
        "cited": cited,
        "resolved_in_tree": resolved_tree,
        "resolved_in_archive": resolved_archive,
        "declared_uncommitted": declared_uncommitted,
        "problems": problems,
    }


def target_cite(args: argparse.Namespace) -> None:
    result = cite_check(ROOT)
    print(
        f"citations: {result['cited']} record ids cited; {result['resolved_in_tree']} name one record in this tree, "
        f"{result['resolved_in_archive']} one record listed in {ARCHIVED_INDEX.relative_to(ROOT)}"
    )
    for line in result["declared_uncommitted"]:
        print(f"  declared not committed by its sentence: {line}")
    if result["problems"]:
        print("record citations that resolve to no record or to more than one:", file=sys.stderr)
        for problem in result["problems"]:
            print(f"  {problem}", file=sys.stderr)
        raise SystemExit(1)


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
    target_cite(args)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("target", choices=["bootstrap", "lint", "test", "pilots", "cite", "all"])
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)
    {"bootstrap": target_bootstrap, "lint": target_lint, "test": target_test, "pilots": target_pilots, "cite": target_cite, "all": target_all}[args.target](args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
