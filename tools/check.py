#!/usr/bin/env python3
"""Single entry point for every repository check.

CI, the container smoke replay, the publish skill, README, and CLAUDE.md all
call this script so the check list exists in exactly one place.  Each target
runs a fixed command set and fails closed on the first failure.  Nothing here
promotes a semantic status: a green run establishes structural and
deterministic behaviour only.

Targets:
  bootstrap    create .venv with Python 3.12 and the pinned dependencies
  lint         compileall, shipped-code assert guard, whitespace, Lean scan
  test-fast    every test module except the two slow scenario suites
  test         the complete unittest suite, one pass
  test-slow    only the two slow scenario suites
  verify       bootstrap validator plus bridge verifier (no PDF, no Lean)
  verify-lean  bridge verifier with the pinned Lean replay
  smoke        the networkless container smoke script (inside the image)
  all          lint, test, verify

Standard library only, so it runs inside the replay image and on any host.
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
SLOW_TEST_MODULES = (
    "tests.test_semantic_forge_inquiry",
    "tests.test_translation_review",
)
LEAN_FORBIDDEN = (
    r"^[[:space:]]*(axiom|opaque)[[:space:]]"
    r"|(^|[^[:alnum:]_])(sorry|admit)([^[:alnum:]_]|$)"
)


def _python() -> str:
    return sys.executable


def _env() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src")
    return env


def _run(command: list[str], *, cwd: Path = ROOT) -> None:
    print("+", " ".join(command), flush=True)
    completed = subprocess.run(command, cwd=cwd, env=_env())
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def _test_modules() -> list[str]:
    return sorted(
        f"tests.{path.stem}"
        for path in (ROOT / "tests").glob("test_*.py")
    )


def assert_guard() -> None:
    """Fail if shipped code contains ``assert``.

    The repository relies on explicit fail-closed checks that survive
    ``python -O``.  Making this a checked invariant replaces the former second
    full test pass under ``-O``, which exercised nothing the normal pass did
    not once no ``assert`` statement exists.
    """

    offenders: list[str] = []
    for directory in ("src", "tools"):
        for path in sorted((ROOT / directory).rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Assert):
                    offenders.append(f"{path.relative_to(ROOT)}:{node.lineno}")
    if offenders:
        print("assert statements in shipped code:", file=sys.stderr)
        for offender in offenders:
            print(f"  {offender}", file=sys.stderr)
        raise SystemExit(1)
    print("assert guard: no assert statements in src/ or tools/")


def lean_scan() -> None:
    """Reject unchecked Lean declarations in the formal package sources."""

    targets = [str(ROOT / "formal" / "CREIB"), str(ROOT / "formal" / "CREIB.lean")]
    completed = subprocess.run(
        ["grep", "-RInE", LEAN_FORBIDDEN, *targets],
        capture_output=True,
        text=True,
    )
    if completed.returncode == 0:
        print("forbidden unchecked Lean declaration found:", file=sys.stderr)
        print(completed.stdout, file=sys.stderr, end="")
        raise SystemExit(1)
    if completed.returncode != 1:
        print(f"Lean source scan failed: {completed.stderr}", file=sys.stderr)
        raise SystemExit(completed.returncode)
    print("lean scan: no axiom/opaque/sorry/admit in formal sources")


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
    pip = venv / "bin" / "python"
    _run([str(pip), "--version"])
    _run(
        [
            str(pip), "-m", "pip", "install", "--quiet", "--no-deps",
            "--only-binary=:all:", "--require-hashes",
            "-r", str(ROOT / "requirements-container.txt"),
        ]
    )
    print(f"bootstrap complete: {venv}/bin/python with PYTHONPATH={ROOT / 'src'}")


def target_lint(args: argparse.Namespace) -> None:
    _run([_python(), "-m", "compileall", "-q", "src", "tools", "tests"])
    assert_guard()
    whitespace_check()
    lean_scan()


def target_test(args: argparse.Namespace) -> None:
    _run([_python(), "-m", "unittest", "discover", "-s", "tests", *(["-v"] if args.verbose else [])])


def target_test_fast(args: argparse.Namespace) -> None:
    modules = [m for m in _test_modules() if m not in SLOW_TEST_MODULES]
    _run([_python(), "-m", "unittest", *(["-v"] if args.verbose else []), *modules])


def target_test_slow(args: argparse.Namespace) -> None:
    _run([_python(), "-m", "unittest", *(["-v"] if args.verbose else []), *SLOW_TEST_MODULES])


def target_verify(args: argparse.Namespace) -> None:
    _run([_python(), str(ROOT / "baseline/cr-1.0/bootstrap-v0.1/tools/validate_bootstrap.py")])
    _run([_python(), str(ROOT / "tools/verify_bridge.py")])


def target_verify_lean(args: argparse.Namespace) -> None:
    _run([_python(), str(ROOT / "tools/verify_bridge.py"), "--lean"])


def target_smoke(args: argparse.Namespace) -> None:
    _run(["bash", str(ROOT / "tools/container_smoke.sh"), *args.smoke_args])


def target_all(args: argparse.Namespace) -> None:
    target_lint(args)
    target_test(args)
    target_verify(args)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("target", choices=[
        "bootstrap", "lint", "test", "test-fast", "test-slow",
        "verify", "verify-lean", "smoke", "all",
    ])
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("smoke_args", nargs="*", help="passed through to container_smoke.sh")
    args = parser.parse_args(argv)
    {
        "bootstrap": target_bootstrap,
        "lint": target_lint,
        "test": target_test,
        "test-fast": target_test_fast,
        "test-slow": target_test_slow,
        "verify": target_verify,
        "verify-lean": target_verify_lean,
        "smoke": target_smoke,
        "all": target_all,
    }[args.target](args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
