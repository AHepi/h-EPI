"""Refusal-site deletion sweep: does the offline suite notice when a fail-closed check goes quiet?

Every ``raise`` statement under ``src/creib`` is a place the machine claims to fail closed.
This tool replaces each one, in turn, with ``pass`` in a temporary copy of ``src``, runs the
offline suite against that copy, and records whether the suite failed.  A site the suite
still passes with is a refusal the suite never exercises: either the input that would trip
it is untested, or the check is unreachable.  The report lists every site with its outcome
and the count of caught and surviving sites per file; it computes no score and the sweep
proves nothing about sites the suite does catch beyond that one deletion was noticed.

Usage (from the repository root, with the venv active):

    python tools/refusal_sweep.py --jobs 4 --report sweep.json [--only src/creib/forge/conformance/records.py]

The suite is run through ``python -m unittest discover -s tests`` with ``PYTHONPATH`` pointing
at the mutated copy.  The package finds its schema directory relative to its own location, so
the copy's root carries a symlink to the repository's ``forge`` directory; without it every
mutant fails at import and the sweep reports a perfect score for the wrong reason, which is
how the first run of this tool went (H25 in the register).  A mutant counts as caught only
when the run exits non-zero having run exactly as many tests as the unmutated suite; a run
that executed fewer tests could not import the mutant and is reported as ``broken``.  Tests
that drive the command line in a subprocess use the repository's own ``src``, not the
mutant, so a refusal reached only through the command line is not covered by this sweep.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


def sites(path: Path) -> list[tuple[int, int, str]]:
    """(first line, last line, source) of every raise statement in a file."""

    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Raise):
            found.append((node.lineno, node.end_lineno or node.lineno, ast.get_source_segment(path.read_text(encoding="utf-8"), node) or "raise"))
    return sorted(found)


def mutate(text: str, first: int, last: int) -> str:
    lines = text.split("\n")
    indent = len(lines[first - 1]) - len(lines[first - 1].lstrip())
    replacement = [" " * indent + "pass  # refusal site deleted by tools/refusal_sweep.py"]
    return "\n".join(lines[: first - 1] + replacement + lines[last:])


_RAN = re.compile(r"^Ran (\d+) tests?", re.M)


def run_suite(src_dir: Path) -> tuple[int, int, str]:
    """(exit code, tests run, stderr tail) for one suite run against ``src_dir``."""

    env = {**os.environ, "PYTHONPATH": str(src_dir), "PYTHONDONTWRITEBYTECODE": "1"}
    try:
        completed = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", str(ROOT / "tests"), "-q"],
            capture_output=True, text=True, env=env, cwd=str(ROOT), timeout=900,
        )
    except subprocess.TimeoutExpired as exc:
        # A deletion that turns a refusal into a loop or a hang is caught by the clock, not the suite.
        return -1, -1, ((exc.stderr or b"") if isinstance(exc.stderr, bytes) else (exc.stderr or "")).__str__()[-4000:] + "\ntimeout after 900 s"
    match = _RAN.search(completed.stderr)
    ran = int(match.group(1)) if match else 0
    return completed.returncode, ran, completed.stderr[-4000:]


def mutant_tree(temporary: Path) -> Path:
    """A copy of ``src`` beside a symlink to ``forge``, so the package finds its schemas."""

    copy = temporary / "src"
    shutil.copytree(SRC, copy, ignore=shutil.ignore_patterns("__pycache__"))
    (temporary / "forge").symlink_to(ROOT / "forge", target_is_directory=True)
    return copy


def one(job: tuple[Path, int, int, str], jobs_dir: Path, expected_tests: int) -> dict[str, object]:
    path, first, last, source = job
    relative = path.relative_to(ROOT).as_posix()
    with tempfile.TemporaryDirectory(dir=jobs_dir) as temporary:
        copy = mutant_tree(Path(temporary))
        target = copy / path.relative_to(SRC)
        target.write_text(mutate(path.read_text(encoding="utf-8"), first, last), encoding="utf-8")
        code, ran, stderr = run_suite(copy)
    if ran == -1:
        outcome = "timeout"
    elif ran != expected_tests:
        outcome = "broken"
    elif code == 0:
        outcome = "survived"
    else:
        outcome = "caught"
    return {"file": relative, "line": first, "source": source.split("\n")[0][:120], "outcome": outcome, "tests_run": ran, "tail": stderr[-600:] if outcome != "caught" else ""}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--only", type=Path, action="append", help="restrict to these source files (repository-relative)")
    args = parser.parse_args()
    files = [ROOT / p for p in args.only] if args.only else sorted(p for p in SRC.rglob("*.py") if "__pycache__" not in p.parts)
    jobs = [(path, first, last, source) for path in files for first, last, source in sites(path)]
    with tempfile.TemporaryDirectory() as temporary:
        baseline_code, baseline_ran, baseline_tail = run_suite(mutant_tree(Path(temporary)))
    if baseline_code != 0 or baseline_ran == 0:
        print("the unmutated suite does not pass through the mutant tree; fix that first", file=sys.stderr)
        print(baseline_tail, file=sys.stderr)
        return 2
    print(f"baseline: {baseline_ran} tests pass through the mutant tree", flush=True)
    results: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory() as jobs_dir:
        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            for index, result in enumerate(pool.map(lambda job: one(job, Path(jobs_dir), baseline_ran), jobs), start=1):
                results.append(result)
                print(f"[{index}/{len(jobs)}] {result['file']}:{result['line']} {result['outcome']}", flush=True)
    per_file: dict[str, dict[str, int]] = {}
    for result in results:
        row = per_file.setdefault(str(result["file"]), {"sites": 0, "caught": 0, "survived": 0, "broken": 0, "timeout": 0})
        row["sites"] += 1
        row[str(result["outcome"])] += 1
    report = {
        "schema_version": "creib.refusal-sweep.v1",
        "sites": len(jobs),
        "caught": sum(1 for r in results if r["outcome"] == "caught"),
        "survived": sum(1 for r in results if r["outcome"] == "survived"),
        "broken": sum(1 for r in results if r["outcome"] == "broken"),
        "timeout": sum(1 for r in results if r["outcome"] == "timeout"),
        "per_file": per_file,
        "results": results,
        "tests_in_suite": baseline_ran,
        "reading": "A survived site is a refusal whose deletion the suite did not detect: the site may be unreached, or reached with its effect masked by a later guard, or reached with an effect no assertion looks at. It says nothing about whether the check is right. A broken site could not be imported after deletion and was not tested; a timeout site turned into a hang, which the clock caught. Counts imply no score.",
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"sites {report['sites']}: caught {report['caught']}, survived {report['survived']}, broken {report['broken']}, timeout {report['timeout']}; report at {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
