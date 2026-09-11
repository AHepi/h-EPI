#!/usr/bin/env python3
"""ARCH-SWEEP-1: run every architecture of one wiring, and see which finds what.

    python tools/arch_sweep.py plan --out forge/mini/manifests/arch-sweep
    python tools/arch_sweep.py read --root forge/mini/runs/arch-sweep

The protocol is ``docs/mini/ARCH_SWEEP.md``. Theorem 7 of ``ARCHITECTURE_SPACE.md`` says the space
saturates at three cycles, so three is what each architecture runs; a fourth would add nothing to
distinguish them.
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
from creib.forge.mini.common import MiniError  # noqa: E402
from creib.forge.mini.configspace import Wiring  # noqa: E402

RULES, SOURCE, PROP, EXEC, CRIT, VERD = (
    "mini.kernel-rules.v1", "mini.kernel-source.v1", "mini.pair-proposal.sweep.v1",
    "mini.pair-execution.v1", "mini.criticism.v1", "mini.verdict.v1")

#: The wiring swept. No grid cell: BUILD-TEST-1 measured an enumerated answer space suppressing
#: contradictions to zero on both arms while construction stayed perfect, so handing one over would
#: make every architecture look identical for a reason that has nothing to do with architecture.
WIRING = Wiring(
    stages=("rules", "source", "propose", "execute", "criticise"),
    last="verdict",
    edges=(("propose", "rules"), ("criticise", "rules"), ("criticise", "source"),
           ("execute", "propose"), ("criticise", "propose"), ("criticise", "execute"),
           ("verdict", "execute"), ("verdict", "criticise")),
)
KIND_OF = {"rules": RULES, "source": SOURCE, "propose": PROP, "execute": EXEC, "criticise": CRIT, "verdict": VERD}
MACHINE = {"rules", "source", "execute", "verdict"}
PORTS = {"propose": [("rules", "rules")], "execute": [("props", "propose")],
         "criticise": [("rules", "rules"), ("source", "source"), ("props", "propose"), ("execs", "execute")],
         "verdict": [("execs", "execute"), ("crits", "criticise")], "rules": [], "source": []}
DRAWS = {"rules": RULES, "source": SOURCE, "props": PROP, "execs": EXEC, "crits": CRIT}
HEADERS = {"rules": "The documented rules of the checks", "source": "The source of the checks",
           "props": "Proposals", "execs": "Executions", "crits": "Criticisms"}
RENDER = {"props": "list_bodies_and_commitments", "execs": "list_bodies_and_commitments"}
LONG = ("input", "rewritten", "rewrite")

PROBLEM = (
    "The checks under test are this repository's own reply-reading functions. The question is "
    "whether there is a reply, and a single edit of it, on which a check's answer does something "
    "the rule as written does not allow. A machine runs the check on both texts and records what "
    "came back; nothing here decides that anything is a defect."
)
PROPOSER = (
    "Build two texts. \"input\" is any reply text you like; \"rewritten\" is a second text, "
    "different from the first, changed however you judge most informative. Say what the RULE AS "
    "WRITTEN says the check's answer ought to do between them: \"moves\" or \"unchanged\". Quote "
    "the words you read it from in the body. Your kernel is one of recovery, recovered-from-prose, "
    "response-verdict, refusal-phrase. The commitments are a STRING holding JSON of the form "
    '{"kernel": "<id>", "expect": "moves" or "unchanged"} and nothing else; this artifact carries '
    '"input", "rewritten" and "rewrite" as fields of its own, each a plain string. Do not repeat a '
    "pair already proposed."
)
CRITIC = (
    "Do not propose. Read the executions beside the proposals: for each expectation that failed, "
    "say whether the proposer misread the rule or the rule as written and the code part company. "
    "Quote the rule's words and name the line of code. Say what a proposer should build next."
)


def manifest(order: Sequence[str], index: int, signature: Sequence[str], cycles: int) -> dict[str, Any]:
    port_types = [{"port_type": p, "draws_from": {"artifact_kinds": [k]},
                   "render": {"rule": RENDER.get(p, "list_bodies"), "header": HEADERS[p]}} for p, k in DRAWS.items()]
    kinds, stages = [], []
    for name in list(order) + ["verdict"]:
        kid = KIND_OF[name]
        kind: dict[str, Any] = {
            "kind_id": kid, "title": name.title(),
            "input_ports": [{"port_id": pid, "port_type": pid, "window": "all"} for pid, _ in PORTS[name]],
            "output_port": {"port_id": "out", "produces_kind": kid},
        }
        if name == "propose":
            kind.update({"commitment_call": "single", "optional_fields": list(LONG), "instruction": PROPOSER,
                         "input_ports": kind["input_ports"] + [{"port_id": "problem", "port_type": "problem", "window": "all"}]})
        if name == "criticise":
            kind["instruction"] = CRITIC
        kinds.append(kind)
        stage = {"stage_id": name, "kind_id": kid, "ports": [pid for pid, _ in PORTS[name]] + (["problem"] if name == "propose" else [])}
        if name in MACHINE:
            stage["seat"] = "machine"
        stages.append(stage)
    stages.append({"stage_id": "end", "end": True})
    return {
        "schema_version": "creib.mini.manifest.v1",
        "manifest_id": f"mini.archsweep.a{index:02d}",
        "problem": PROBLEM,
        "cycles": {"max_cycles": cycles},
        "port_types": port_types, "kinds": kinds, "stages": stages,
        "sources": [{"source_id": "registry", "text": "the checks under test are named in the rules artifact\n"}],
    }


def _plan(args: argparse.Namespace) -> int:
    out = Path(args.out)
    architectures = sorted(WIRING.architectures().items(), key=lambda kv: (WIRING.lag_of(kv[0]), kv[1][0]))
    index = {}
    for i, (signature, (order, realised)) in enumerate(architectures):
        body = manifest(order[:-1], i, signature, args.cycles)
        target = out / f"a{i:02d}" / "manifest.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        index[f"a{i:02d}"] = {"ordering": list(order), "signature": list(signature),
                              "lagged_edges": WIRING.lag_of(signature), "orderings_realising_it": realised}
    (out / "architectures.json").write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{len(architectures)} architectures written to {out}", flush=True)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    planner = sub.add_parser("plan", help="write one manifest per architecture")
    planner.add_argument("--out", required=True)
    planner.add_argument("--cycles", type=int, default=3)
    planner.set_defaults(handler=_plan)
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except (MiniError, RecordError) as error:
        sys.stderr.write(f"{error}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
