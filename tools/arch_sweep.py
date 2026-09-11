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
    "response-verdict, refusal-phrase, each written in full with its \"conformance.kernel.\" "
    "prefix: conformance.kernel.recovery, conformance.kernel.recovered-from-prose, "
    "conformance.kernel.response-verdict, conformance.kernel.refusal-phrase. A kernel named "
    "without that prefix does not exist and the run is lost. The commitments are a STRING "
    "holding JSON of the form "
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


def _executions(root: Path) -> list[dict[str, Any]]:
    """Every pair this run executed, read from the record rather than from a log line."""

    from creib.forge.mini.common import RUN_HEADER_DOMAIN, content_id
    from creib.forge.mini.log import BlobStore, replay
    from creib.strict_json import load_strict

    state = replay(root / "log.jsonl", content_id(RUN_HEADER_DOMAIN, load_strict(root / "run-header.json")))
    blobs = BlobStore(root / "blobs")
    out: list[dict[str, Any]] = []
    for key in state.artifact_order:
        record = state.artifacts[key]
        if str(record["kind_id"]) != EXEC:
            continue
        payload = json.loads(blobs.get(str(record["commitments_ref"])).decode("utf-8"))
        out.extend(payload.get("executions", []))
    return out


def _quotes(text: str, rules: str) -> int:
    """How many quoted runs of the stated reading occur verbatim in the documented rules."""

    import re

    from creib.forge.conformance.oracle import _normalise_whitespace as norm

    found = 0
    for match in re.finditer(r'["\u201c\'\u201d]([^"\u201c\u201d\']{25,400})["\u201c\u201d\']', text):
        span = match.group(1).strip()
        if len(span.split()) >= 4 and norm(span.lower()) in rules:
            found += 1
    return found


def _read(args: argparse.Namespace) -> int:
    from creib.forge.conformance.oracle import _normalise_whitespace as norm
    from creib.forge.mini.conformance_kernels import kernel_rules_text

    root = Path(args.root)
    index = json.loads((Path(args.manifests) / "architectures.json").read_text()) if args.manifests else {}
    rules = norm(kernel_rules_text().lower())
    per: dict[str, dict[str, Any]] = {}
    for directory in sorted(root.glob("a*")):
        if not (directory / "log.jsonl").is_file():
            continue
        runs = _executions(directory)
        ran = [e for e in runs if e.get("executed") in ("moved", "unchanged")]
        contra = [e for e in ran if e.get("as_expected") is False]
        per[directory.name] = {
            "proposals": len(runs),
            "executed": len(ran),
            "unrunnable": len(runs) - len(ran),
            "contradicted": len(contra),
            "quoted": sum(1 for e in contra if _quotes(str(e.get("reading", "")) + str(e.get("rewrite", "")), rules)),
            "behaviours": {(str(e.get("kernel")), str(e.get("before")), str(e.get("after"))) for e in ran},
            # Amendment 2. The pre-registered behaviour is (kernel, answer-before, answer-after), and
            # the answers are functions of texts the proposer chose freely, so two architectures share
            # one only by choosing the same text. The probe is the same row coarsened to the finite
            # grid (kernel, what was expected, what happened): 6 x 2 x 3 cells, shareable by accident
            # far more easily than a text is. Both are reported; neither replaces the other.
            "probes": {(str(e.get("kernel")), str(e.get("expect")), str(e.get("executed"))) for e in ran},
        }
    everything: dict[tuple[str, str, str], set[str]] = {}
    probes_seen: dict[tuple[str, str, str], set[str]] = {}
    for name, row in per.items():
        for behaviour in row["behaviours"]:
            everything.setdefault(behaviour, set()).add(name)
        for probe in row["probes"]:
            probes_seen.setdefault(probe, set()).add(name)
    rows = []
    for name, row in sorted(per.items()):
        unique = [b for b in row["behaviours"] if everything[b] == {name}]
        unique_probes = [b for b in row["probes"] if probes_seen[b] == {name}]
        meta = index.get(name, {})
        rows.append({"architecture": name, "lagged_edges": meta.get("lagged_edges"),
                     "ordering": " ".join(x[0] for x in meta.get("ordering", [])),
                     **{k: row[k] for k in ("proposals", "executed", "unrunnable", "contradicted", "quoted")},
                     "distinct_behaviours": len(row["behaviours"]), "unique_to_it": len(unique),
                     "distinct_probes": len(row["probes"]), "unique_probes": len(unique_probes),
                     "unique_behaviours": sorted(unique), "unique_probe_cells": sorted(unique_probes)})
    union = len(everything)
    a00 = len(per.get("a00", {}).get("behaviours", ()))
    p_union = len(probes_seen)
    p_a00 = len(per.get("a00", {}).get("probes", ()))
    summary = {"architectures_read": len(per), "union_of_behaviours": union,
               "synchronous_alone": a00, "gained_over_synchronous": union - a00,
               "union_of_probes": p_union, "synchronous_probes_alone": p_a00,
               "probes_gained_over_synchronous": p_union - p_a00,
               "proposals": sum(r["proposals"] for r in per.values()),
               "unrunnable": sum(r["unrunnable"] for r in per.values())}
    (root / "reading.json").write_text(json.dumps({"summary": summary, "rows": rows}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    head = (f"{'arch':<5} {'lag':>3} {'prop':>4} {'exec':>4} {'lost':>4} {'contra':>6} {'quoted':>6} "
            f"{'behav':>5} {'uniq':>4} {'probe':>5} {'uniq':>4}  ordering")
    print(head, flush=True)
    for row in rows:
        print(f"{row['architecture']:<5} {str(row['lagged_edges']):>3} {row['proposals']:>4} {row['executed']:>4} "
              f"{row['unrunnable']:>4} {row['contradicted']:>6} {row['quoted']:>6} {row['distinct_behaviours']:>5} "
              f"{row['unique_to_it']:>4} {row['distinct_probes']:>5} {row['unique_probes']:>4}  {row['ordering']}", flush=True)
    print(f"\nproposals {summary['proposals']}, of which {summary['unrunnable']} did not run", flush=True)
    print(f"behaviours (pre-registered): union {union}, synchronous alone {a00}, gained {union - a00}", flush=True)
    print(f"probes (amendment 2):        union {p_union}, synchronous alone {p_a00}, gained {p_union - p_a00}", flush=True)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    planner = sub.add_parser("plan", help="write one manifest per architecture")
    planner.add_argument("--out", required=True)
    planner.add_argument("--cycles", type=int, default=3)
    planner.set_defaults(handler=_plan)
    reader = sub.add_parser("read", help="read every architecture and find what only one of them produced")
    reader.add_argument("--root", required=True)
    reader.add_argument("--manifests", default="forge/mini/manifests/arch-sweep")
    reader.set_defaults(handler=_read)
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except (MiniError, RecordError) as error:
        sys.stderr.write(f"{error}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
