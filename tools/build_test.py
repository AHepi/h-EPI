#!/usr/bin/env python3
"""BUILD-TEST-1: run reconstruction against relay, and read what came back.

    python tools/build_test.py run  --out forge/mini/runs/buildtest/<block> --plan <plan.json>
    python tools/build_test.py read --root forge/mini/runs/buildtest/<block>

The protocol is ``docs/mini/BUILD_TEST.md``, pre-registered before any arm ran. A plan is a list
of conditions; each condition is one arm on one endpoint, and each proposal in it is one model
call. Nothing here retries, repairs, ranks or promotes.

Keys are read at call time from ``OLLAMA_API_KEY`` and from the file named by
``DEEPSEEK_KEY_FILE``, and appear in no record this writes.

Standard library plus the package; ``PYTHONPATH=src``.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from creib.errors import RecordError  # noqa: E402
from creib.forge.mini import buildtest  # noqa: E402
from creib.forge.mini.common import MiniError  # noqa: E402
from creib.forge.mini.usetest import load_subject, subject_source  # noqa: E402
from creib.strict_json import load_strict  # noqa: E402

INVALID = "MINI_BUILDTEST_PLAN_INVALID"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _conditions(plan: Any) -> list[buildtest.Condition]:
    if type(plan) is not dict or type(plan.get("conditions")) is not list:
        raise MiniError(INVALID, "a plan is an object carrying a list of conditions")
    built: list[buildtest.Condition] = []
    for index, raw in enumerate(plan["conditions"]):
        if type(raw) is not dict:
            raise MiniError(INVALID, f"condition {index} is not an object")
        endpoint = buildtest.Endpoint(
            path=str(raw["path"]),
            model=str(raw["model"]),
            think=raw.get("think"),
            timeout_seconds=int(raw.get("timeout_seconds", 900)),
            max_tokens=raw.get("max_tokens"),
        )
        built.append(
            buildtest.Condition(
                arm=str(raw["arm"]),
                endpoint=endpoint,
                proposals=int(raw.get("proposals", 10)),
                grid_cells=tuple(str(cell) for cell in raw.get("grid_cells", ())),
            )
        )
    return built


def _run(args: argparse.Namespace) -> int:
    out = Path(args.out)
    plan = load_strict(Path(args.plan))
    conditions = _conditions(plan)
    source = subject_source()
    with tempfile.TemporaryDirectory() as scratch:
        path = Path(scratch) / "subject.py"
        path.write_text(source, encoding="utf-8")
        subject = load_subject(path)
        _write(out / "subject.py", source)
        for condition in conditions:
            name = condition.condition_id.replace("/", "__")
            target = out / f"{name}.json"
            if target.exists() and not args.overwrite:
                print(f"{condition.condition_id}: already recorded, skipped", flush=True)
                continue
            record = buildtest.run_condition(condition, subject, source)
            _write(target, json.dumps(record, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
            m = record["measures"]
            print(
                f"{condition.condition_id}: {m['proposals']} proposals, {m['executed']} executed, "
                f"{m['contradicted']} contradicted, {m['distinct_behaviours']} distinct behaviours",
                flush=True,
            )
    return 0


def _read(args: argparse.Namespace) -> int:
    root = Path(args.root)
    records = {}
    for path in sorted(root.glob("*.json")):
        if path.name == "reading.json":
            continue
        records[path.stem] = load_strict(path)
    rows = []
    for name, record in records.items():
        condition = record["condition"]
        measures = record["measures"]
        other = _partner(name, records)
        rows.append(
            {
                "condition": condition["condition_id"],
                "arm": condition["arm"],
                "path": condition["endpoint"]["path"],
                "model": condition["endpoint"]["model"],
                "quantisation": condition["endpoint"]["quantisation"],
                "think": condition["endpoint"]["think"],
                "grid": bool(condition["grid_cells"]),
                **{key: measures[key] for key in ("proposals", "executed", "degenerate", "unrunnable", "contradicted", "distinct_behaviours", "reproduces_h43")},
                "calls_failed": sum(1 for call in record["calls"] if not call["ok"]),
                "unique_to_arm": len(buildtest.unique_to_arm(record, other)) if other else None,
            }
        )
    _write(root / "reading.json", json.dumps(rows, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    header = f"{'condition':<62} {'prop':>4} {'exec':>4} {'contra':>6} {'distinct':>8} {'uniq':>4} {'fail':>4}"
    print(header, flush=True)
    for row in rows:
        print(
            f"{row['condition']:<62} {row['proposals']:>4} {row['executed']:>4} {row['contradicted']:>6} "
            f"{row['distinct_behaviours']:>8} {str(row['unique_to_arm']):>4} {row['calls_failed']:>4}",
            flush=True,
        )
    return 0


def _partner(name: str, records: dict[str, Any]) -> Any:
    """The same cell with the other arm, when the block ran both."""

    for arm, other in (("arm-R", "arm-L"), ("arm-L", "arm-R")):
        if arm in name:
            return records.get(name.replace(arm, other))
    return None


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    runner = sub.add_parser("run", help="run every condition of a plan")
    runner.add_argument("--plan", required=True)
    runner.add_argument("--out", required=True)
    runner.add_argument("--overwrite", action="store_true", help="re-run a condition that is already recorded")
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
