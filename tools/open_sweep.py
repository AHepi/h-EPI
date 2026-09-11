#!/usr/bin/env python3
"""OPEN-SWEEP-1: ARCH-SWEEP-1's synchronous architecture with the answer space opened.

    python tools/open_sweep.py plan --out forge/mini/manifests/open-sweep
    python tools/open_sweep.py read --root forge/mini/runs/open-sweep \
        --against forge/mini/runs/arch-sweep-control

The protocol is ``docs/mini/OPEN_SWEEP.md``. The manifest is ``a00``'s, with two changes and no
others: the execution stage takes the open seat, and the proposer's instruction names a rule and
fifteen modules instead of four kernels.
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

sys.path.insert(0, str(ROOT / "tools"))

from creib.errors import RecordError  # noqa: E402
from creib.forge.mini.common import MiniError  # noqa: E402
from creib.forge.mini.openkernels import (  # noqa: E402
    PAIR_EXECUTION_OPEN_KIND,
    open_kernel_brief,
)

import arch_sweep  # noqa: E402

#: The closed instruction with its enumeration replaced by a rule and a module list. Everything
#: either side of that clause is ARCH-SWEEP-1's text, unchanged, so the arms differ in the answer
#: space and not in how the task is put.
OPEN_PROPOSER = (
    "Build two texts. \"input\" is any reply text you like; \"rewritten\" is a second text, "
    "different from the first, changed however you judge most informative. Say what the RULE AS "
    "WRITTEN says the check's answer ought to do between them: \"moves\" or \"unchanged\". Quote "
    "the words you read it from in the body.\n\n"
    + open_kernel_brief()
    + "\nThe commitments are a STRING holding JSON of the form "
    '{"kernel": "<id>", "expect": "moves" or "unchanged"} and nothing else; this artifact carries '
    '"input", "rewritten" and "rewrite" as fields of its own, each a plain string. Do not repeat a '
    "pair already proposed."
)


def manifest(index: int, cycles: int) -> dict[str, Any]:
    """``a00``'s manifest, with the execution seat opened and the proposer's clause replaced."""

    body = arch_sweep.manifest(("rules", "source", "propose", "execute", "criticise"), 0, (), cycles)
    body["manifest_id"] = f"mini.opensweep.r{index:02d}"
    for port in body["port_types"]:
        if port["port_type"] == "execs":
            port["draws_from"]["artifact_kinds"] = [PAIR_EXECUTION_OPEN_KIND]
    for kind in body["kinds"]:
        if kind["kind_id"] == arch_sweep.EXEC:
            kind["kind_id"] = PAIR_EXECUTION_OPEN_KIND
            kind["output_port"]["produces_kind"] = PAIR_EXECUTION_OPEN_KIND
        if kind["kind_id"] == arch_sweep.PROP:
            kind["instruction"] = OPEN_PROPOSER
    for stage in body["stages"]:
        if stage.get("kind_id") == arch_sweep.EXEC:
            stage["kind_id"] = PAIR_EXECUTION_OPEN_KIND
    return body


def _plan(args: argparse.Namespace) -> int:
    out = Path(args.out)
    for index in range(args.runs):
        target = out / f"r{index:02d}" / "manifest.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(manifest(index, args.cycles), indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8")
    print(f"{args.runs} open-arm manifests written to {out}", flush=True)
    return 0


def _rows(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for directory in sorted(root.glob("[ar]*")):
        if (directory / "log.jsonl").is_file():
            rows.extend(arch_sweep._executions(directory))
    return rows


def _summary(rows: Sequence[dict[str, Any]], rules: str) -> dict[str, Any]:
    ran = [entry for entry in rows if entry.get("executed") in ("moved", "unchanged")]
    contra = [entry for entry in ran if entry.get("as_expected") is False]
    return {
        "entries": len(rows),
        "ran": len(ran),
        "duplicate": sum(1 for entry in rows if entry.get("executed") == "duplicate"),
        "unrunnable": sum(1 for entry in rows
                          if entry.get("executed") not in ("moved", "unchanged", "duplicate")),
        "contradicted": len(contra),
        "quoted": sum(1 for entry in contra
                      if arch_sweep._quotes(str(entry.get("reading", "")) + str(entry.get("rewrite", "")), rules)),
        "behaviours": len({(str(e.get("kernel")), str(e.get("before")), str(e.get("after"))) for e in ran}),
        "probes": len({(str(e.get("kernel")), str(e.get("expect")), str(e.get("executed"))) for e in ran}),
        "distinct_kernels": len({str(e.get("kernel")) for e in rows}),
        "open_kernels_named": len({str(e.get("kernel")) for e in rows
                                   if str(e.get("kernel")).startswith("open:")}),
        "open_kernels_run": len({str(e.get("kernel")) for e in ran
                                 if str(e.get("kernel")).startswith("open:")}),
    }


def _read(args: argparse.Namespace) -> int:
    from creib.forge.conformance.oracle import _normalise_whitespace as norm
    from creib.forge.mini.conformance_kernels import kernel_rules_text

    rules = norm(kernel_rules_text().lower())
    arms = {"open": _summary(_rows(Path(args.root)), rules)}
    if args.against:
        arms["closed"] = _summary(_rows(Path(args.against)), rules)
    keys = list(next(iter(arms.values())))
    print(f"{'measure':<20}" + "".join(f"{name:>12}" for name in arms), flush=True)
    for key in keys:
        print(f"{key:<20}" + "".join(f"{arms[name][key]:>12}" for name in arms), flush=True)
    Path(args.root, "reading.json").write_text(json.dumps(arms, indent=2, sort_keys=True) + "\n",
                                               encoding="utf-8")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    planner = sub.add_parser("plan", help="write the open arm's manifests")
    planner.add_argument("--out", required=True)
    planner.add_argument("--runs", type=int, default=36)
    planner.add_argument("--cycles", type=int, default=3)
    planner.set_defaults(handler=_plan)
    reader = sub.add_parser("read", help="read the open arm beside the closed one")
    reader.add_argument("--root", required=True)
    reader.add_argument("--against", default=None)
    reader.set_defaults(handler=_read)
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except (MiniError, RecordError) as error:
        sys.stderr.write(f"{error}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
