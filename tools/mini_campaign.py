#!/usr/bin/env python3
"""Run a campaign of mini blind-spot rounds to its end, without anyone in the middle.

    python tools/mini_campaign.py run --plan <plan.json> --rounds 3 --output-dir <scratch>

A plan names the shapes: for each, the manifest directory it starts from and the model to run
it on. Each round runs its shapes live, at most ``--concurrency`` at a time, reads every record
it wrote, writes that reading beside it, and decides the next round from the measurements alone
(``creib.forge.mini.campaign``). The manifests and the decision note for round N+1 are written
before round N+1 is run, so the pre-registration is on disk before the records exist.

The campaign stops when the rounds are spent, when every shape's rules say it has nothing left
to run, or when a round contradicts nothing and changes nothing.

What it does not do, and cannot: decide that a disagreement is a blind spot. That reading is a
person's, for the reasons set out in ``docs/mini/AUTONOMY.md``; the campaign lays every
disagreement out with the texts that produced it and stops there. It does not push or merge
either: publication is a pull request and a human action.

The key is never read here. ``run_mini.py live`` reads ``OLLAMA_API_KEY`` inside the harness's
own executor, which is the one place in this repository that touches it; this tool passes the
environment it was given to the subprocess and looks at nothing in it.

Standard library plus the package; ``PYTHONPATH=src``.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from creib.errors import RecordError  # noqa: E402
from creib.forge.mini.campaign import Decision, decide, render_decisions  # noqa: E402
from creib.forge.mini.common import MiniError  # noqa: E402
from creib.forge.mini.report import RunReading, read_run, render  # noqa: E402
from creib.strict_json import load_strict  # noqa: E402

_PLAN_INVALID = "MINI_CAMPAIGN_PLAN_INVALID"


def _shapes_of(plan: Mapping[str, Any], where: str) -> list[dict[str, str]]:
    shapes = plan.get("shapes")
    if type(shapes) is not list or not shapes:
        raise MiniError(_PLAN_INVALID, f"{where}.shapes must be a non-empty array")
    read: list[dict[str, str]] = []
    for index, item in enumerate(shapes):
        if type(item) is not dict:
            raise MiniError(_PLAN_INVALID, f"{where}.shapes[{index}] must be an object")
        for name in ("shape", "manifest_dir", "model"):
            if type(item.get(name)) is not str or not item[name].strip():
                raise MiniError(_PLAN_INVALID, f"{where}.shapes[{index}].{name} must be a non-empty string")
        read.append({"shape": item["shape"], "manifest_dir": item["manifest_dir"], "model": item["model"]})
    if len({item["shape"] for item in read}) != len(read):
        raise MiniError(_PLAN_INVALID, f"{where}.shapes must name each shape once")
    return read


def _write_manifest_dir(source: Path, target: Path, manifest: Mapping[str, Any], manifest_id: str) -> None:
    """Write a round's manifest directory: the manifest as decided, its sources as they were."""

    target.mkdir(parents=True, exist_ok=True)
    written = dict(manifest)
    written["manifest_id"] = manifest_id
    (target / "manifest.json").write_text(json.dumps(written, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for item in written.get("sources", []):
        path = item.get("path")
        if type(path) is str and (source / path).exists():
            (target / path).write_bytes((source / path).read_bytes())


def _commit(paths: Sequence[Path], message: str) -> None:
    """Stage exactly these paths and commit them, so a decided round is on the record before it runs.

    A conjecture is committed before the records it is about exist; a campaign that decided its
    own next round and ran it uncommitted would have written its pre-registration afterwards.
    Explicit paths, never ``-A``; the whitespace check runs as it does by hand; nothing is
    pushed, because publication is a pull request and a human action.
    """

    named = [str(path.relative_to(ROOT)) for path in paths]
    subprocess.run(["git", "add", *named], cwd=str(ROOT), check=True)
    checked = subprocess.run(["git", "diff", "--cached", "--check"], cwd=str(ROOT), capture_output=True, text=True)
    if checked.returncode != 0:
        raise MiniError("MINI_CAMPAIGN_COMMIT_REFUSED", f"the staged paths carry whitespace git refuses:\n{checked.stdout}")
    done = subprocess.run(["git", "commit", "-q", "-m", message], cwd=str(ROOT), capture_output=True, text=True)
    if done.returncode != 0:
        raise MiniError("MINI_CAMPAIGN_COMMIT_REFUSED", f"git refused the commit: {done.stdout}{done.stderr}")


def _launch(shape: Mapping[str, str], manifest_dir: Path, output_dir: Path, timeout_seconds: int, retries: int) -> subprocess.Popen:
    command = [
        sys.executable,
        str(ROOT / "tools" / "run_mini.py"),
        "live",
        "--manifest",
        str(manifest_dir / "manifest.json"),
        "--model",
        shape["model"],
        "--output-dir",
        str(output_dir),
        "--timeout-seconds",
        str(timeout_seconds),
        "--retries",
        str(retries),
    ]
    log = (output_dir.parent / f"{shape['shape']}.out").open("w", encoding="utf-8")
    return subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, cwd=str(ROOT))


def _run_round(
    shapes: Sequence[Mapping[str, str]],
    manifest_dirs: Mapping[str, Path],
    round_dir: Path,
    concurrency: int,
    timeout_seconds: int,
    retries: int,
    poll_seconds: int,
) -> dict[str, int]:
    """Run one round, at most ``concurrency`` live at a time, and return each shape's exit code."""

    waiting = list(shapes)
    running: dict[str, subprocess.Popen] = {}
    codes: dict[str, int] = {}
    while waiting or running:
        while waiting and len(running) < concurrency:
            shape = waiting.pop(0)
            output = round_dir / shape["shape"]
            running[shape["shape"]] = _launch(shape, manifest_dirs[shape["shape"]], output, timeout_seconds, retries)
            print(f"  started {shape['shape']} on {shape['model']}", flush=True)
        for name in list(running):
            code = running[name].poll()
            if code is None:
                continue
            codes[name] = int(code)
            print(f"  ended   {name} (exit {code})", flush=True)
            del running[name]
        if running:
            time.sleep(poll_seconds)
    return codes


def _read_round(shapes: Sequence[Mapping[str, str]], round_dir: Path) -> dict[str, RunReading]:
    readings: dict[str, RunReading] = {}
    for shape in shapes:
        root = round_dir / shape["shape"]
        try:
            reading = read_run(root)
        except (RecordError, MiniError, OSError) as error:
            print(f"  unreadable {shape['shape']}: {error}", flush=True)
            continue
        (round_dir / f"{shape['shape']}.reading.md").write_text(render(reading), encoding="utf-8")
        (round_dir / f"{shape['shape']}.reading.json").write_text(
            json.dumps(reading.as_dict(), indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8"
        )
        readings[shape["shape"]] = reading
    return readings


def _campaign(args: argparse.Namespace) -> int:
    plan = load_strict(Path(args.plan))
    if type(plan) is not dict:
        raise MiniError(_PLAN_INVALID, "a plan is a JSON object")
    shapes = _shapes_of(plan, "plan")
    output_dir = Path(args.output_dir)
    manifest_root = Path(args.manifest_dir) if args.manifest_dir else output_dir / "manifests"
    manifest_dirs = {shape["shape"]: ROOT / shape["manifest_dir"] for shape in shapes}
    sources = dict(manifest_dirs)
    campaign_id = str(plan.get("campaign_id") or "campaign")

    for number in range(1, args.rounds + 1):
        round_name = f"{campaign_id}-round-{number}"
        round_dir = output_dir / round_name
        round_dir.mkdir(parents=True, exist_ok=True)
        print(f"[{round_name}] {len(shapes)} shapes, at most {args.concurrency} at a time", flush=True)
        codes = _run_round(shapes, manifest_dirs, round_dir, args.concurrency, args.timeout_seconds, args.retries, args.poll_seconds)
        readings = _read_round(shapes, round_dir)
        contradicted = sum(len(reading.disagreements) for reading in readings.values())
        print(f"[{round_name}] {len(readings)} records read, {contradicted} executions contradicted a proposal", flush=True)
        (round_dir / "round.json").write_text(
            json.dumps(
                {
                    "round": round_name,
                    "exit_codes": codes,
                    "readings": {name: reading.as_dict() for name, reading in sorted(readings.items())},
                },
                indent=2,
                ensure_ascii=False,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        if number == args.rounds:
            break

        decisions: list[Decision] = []
        for shape in shapes:
            reading = readings.get(shape["shape"])
            if reading is None:
                continue
            manifest = load_strict(manifest_dirs[shape["shape"]] / "manifest.json")
            decisions.append(decide(shape["shape"], reading, manifest))
        if not decisions or all(decision.stop for decision in decisions):
            print(f"[{round_name}] every shape has nothing left to run; the campaign stops here", flush=True)
            break
        if contradicted == 0 and all(not decision.rules_fired for decision in decisions):
            print(f"[{round_name}] nothing contradicted and no rule fired; the campaign stops here", flush=True)
            break

        next_name = f"{campaign_id}-round-{number + 1}"
        next_root = manifest_root / next_name
        next_root.mkdir(parents=True, exist_ok=True)
        (next_root / "decisions.md").write_text(render_decisions(next_name, decisions, readings), encoding="utf-8")
        surviving: list[dict[str, str]] = []
        for decision in decisions:
            if decision.stop or decision.manifest is None:
                continue
            target = next_root / decision.shape
            _write_manifest_dir(sources[decision.shape], target, decision.manifest, f"mini.campaign.{next_name}.{decision.shape}")
            manifest_dirs[decision.shape] = target
            surviving.append(next(item for item in shapes if item["shape"] == decision.shape))
        shapes = surviving
        print(f"[{round_name}] wrote {next_name}: {len(shapes)} shapes, decisions in {next_root / 'decisions.md'}", flush=True)
        if args.commit:
            fired = sorted({rule for decision in decisions for rule in decision.rules_fired})
            _commit(
                [next_root],
                f"Mini campaign {next_name}: {len(shapes)} shapes decided from the last round's records"
                + (f" by {', '.join(fired)}" if fired else " with no rule fired")
                + "\n\nDecided and committed by tools/mini_campaign.py before this round was run;\n"
                "the measurements it fired on are in the round's readings beside its records.",
            )
            print(f"[{round_name}] committed {next_name}", flush=True)
    print("campaign finished", flush=True)
    return 0


def _read(args: argparse.Namespace) -> int:
    reading = read_run(Path(args.root))
    sys.stdout.write(json.dumps(reading.as_dict(), indent=2, ensure_ascii=False, sort_keys=True) + "\n" if args.json else render(reading))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    campaign = sub.add_parser("run", help="run a campaign of rounds to its end")
    campaign.add_argument("--plan", required=True)
    campaign.add_argument("--output-dir", required=True)
    campaign.add_argument("--manifest-dir", default=None, help="where each decided round's manifests are written")
    campaign.add_argument("--rounds", type=int, default=3)
    campaign.add_argument("--concurrency", type=int, default=5)
    campaign.add_argument("--timeout-seconds", type=int, default=600)
    campaign.add_argument("--retries", type=int, default=1)
    campaign.add_argument("--poll-seconds", type=int, default=10)
    campaign.add_argument("--commit", action="store_true", help="commit each decided round's manifests before running it; never pushes")
    campaign.set_defaults(handler=_campaign)

    reader = sub.add_parser("read", help="read one run root and say what it holds")
    reader.add_argument("--root", required=True)
    reader.add_argument("--json", action="store_true")
    reader.set_defaults(handler=_read)

    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except (MiniError, RecordError) as error:
        sys.stderr.write(f"{error}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
