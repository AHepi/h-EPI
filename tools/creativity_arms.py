#!/usr/bin/env python3
"""The Blueprint's decisive comparison, run on mini, for kernel boundaries.

    python tools/creativity_arms.py plan --out forge/mini/manifests/creativity
    python tools/creativity_arms.py enumerate --out forge/mini/runs/creativity/E
    python tools/creativity_arms.py read --root forge/mini/runs/creativity

Four model arms and two baselines, from *The Creativity Machine*, "The decisive LLM experiment":
a single-shot condition, an equal-budget repeated-generation condition, a condition with returned
evidence but no live installation, and the full representation-revising condition, over a
non-LLM enumeration baseline and a supplied-solution control.

``N`` and ``F`` differ in one thing: whether a segment's result changes the organisation the next
segment runs. That is the Blueprint's no-return control, and per T-A of ``docs/mini/PIPELINE_MATH.md``
it is the only pair that tests what serialisation buys.

The find is a T1 witness: a pair of texts the rule as written requires a check to separate, on
which the check gives the same answer. Nothing downstream of the check can recover the
distinction. Over-sensitivity -- a check separating what the rule says should agree -- is counted
apart, because no impossibility follows from it.
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
from creib.forge.mini.openkernels import (  # noqa: E402
    PAIR_EXECUTION_OPEN_KIND,
    open_kernel_brief,
    resolve_any_kernel,
)

CONJECTURE = "mini.conjecture.v1"
READING = "mini.pair-proposal.reading.v1"
CRITICISM = "mini.criticism.v1"
VERDICT = "mini.verdict.v1"
SOURCE = "mini.kernel-source.v1"
ADJUDICATION = "mini.adjudication.v1"

#: The contract, held separately from any arm's organisation. Every arm is given this and nothing
#: in it names a check, a text, or a transformation: a hidden supplied template explaining the
#: result is the first way the Blueprint says the attribution fails.
PROBLEM = (
    "The checks under test are this repository's own functions for reading a model's reply. Each "
    "takes one string and answers something about it.\n\n"
    "Find a pair of replies that the rule, as written, requires a check to tell apart, and on "
    "which the check gives the SAME answer. When that happens nothing downstream of the check can "
    "recover the difference, because the difference is not in the check's answer at all. That is "
    "the find.\n\n"
    "A pair the check tells apart where the rule says it should not is a different and weaker "
    "thing; say so if that is what you have."
)

#: Prose first. The Blueprint: "Raw prose enters inquiry before any semantic classification."
#: No schema here on purpose -- a conjecture that cannot be parsed is still in the record, and a
#: strict form would delete it before anything could read it.
CONJECTURE_INSTRUCTION = (
    "Write, in plain prose, one conjecture: name the function you are testing, quote the words of "
    "its documented rule you are reading, give the two reply texts in full, and say which answer "
    "the rule requires for each. Say what would make you wrong -- the observation that would show "
    "this conjecture false. Do not write JSON. Do not use a fenced block. Prose only.\n\n"
    + open_kernel_brief()
)

#: The translator, and the only place a schema sits. Its reading may be wrong; being wrong it is a
#: target rather than a discard, which is what putting the schema downstream of the prose buys.
READING_INSTRUCTION = (
    "You are reading someone else's prose conjecture, not writing your own. Render it as the "
    "machine needs it. If the prose is unclear, render your best reading of it and say in the body "
    "where you were unsure; do not substitute a conjecture of your own.\n\n"
    "The commitments are a STRING holding JSON of the form "
    '{"kernel": "<path>", "expect": "moves" or "unchanged"} and nothing else.\n\n'
    '"kernel" is the FUNCTION\'S FULL DOTTED IMPORT PATH, exactly as the conjecture gives it, '
    "beginning open:creib.forge.conformance. -- for example "
    "open:creib.forge.conformance.oracle.recover_json_object. **It is never the bracketed "
    "hexadecimal identifier printed beside an artifact.** That identifies the artifact you are "
    "reading; it is not the function the artifact is about. If the conjecture names no such path, "
    "write the path it most nearly names.\n\n"
    'This artifact carries '
    '"input", "rewritten" and "rewrite" as fields of its own, each a plain string: "input" and '
    '"rewritten" are the two reply texts exactly as the prose gave them, and "rewrite" says how '
    "they differ. Use \"moves\" when the rule requires the two answers to differ."
)

CRITICISM_INSTRUCTION = (
    "Do not conjecture. Read what the machine returned beside what was claimed. For each pair, say "
    "whether the conjecture misread the rule, or the rule as written and the code part company. "
    "Then say what a next conjecture should try instead, and name what it should avoid repeating. "
    "Quote the rule's words."
)

#: Arm A's critic carries a WARRANT rather than an opinion: its commitment names the artifact it
#: attacks and the ground it stands on, a machine seat resolves that name against the record, and
#: status is computed from the relation. "A bare verdict is never an edge"; this is the edge.
CRITICISM_ADJUDICATED = None  # set below, once CRITICISM_WIRED exists

#: Arm W's critic differs from F's in what it is told to do with the reading it can now see. The
#: kinds, their commitments and the install map are untouched; only ports and this text move.
CRITICISM_WIRED = CRITICISM_INSTRUCTION + (
    "\n\nYou are also shown the READING: the structured commitment a translator made of the "
    "conjecture's prose, naming the function and what it expected. Attack it. Name the reading's "
    "artifact id, quote the words of the conjecture it claims to render, and say whether it renders "
    "them. A reading that names a function the prose did not name, or a module the function does not "
    "live in, or an expectation the prose did not state, is a defect in the reading and not in the "
    "conjecture -- say which of the two is wrong, and how you can tell them apart."
)


CRITICISM_ADJUDICATED = CRITICISM_WIRED + (
    "\n\nYour commitments are a STRING holding JSON of the form "
    '{"attacks": "<the first 16 characters of the artifact id you are attacking>", '
    '"ground": "<one of: reading-misrenders-conjecture, conjecture-misreads-rule, '
    'rule-and-code-diverge, cannot-tell>", "why": "<one sentence>"} and nothing else.\n\n'
    "The id must be one printed in square brackets beside an artifact you were shown; a name "
    "matching nothing resolves to no attack. Use \"cannot-tell\" when you cannot decide -- it is "
    "an honest answer and it mints no attack, which is better than inventing a target."
)


def _kinds_and_ports(with_criticism: bool, wired: bool = False, adjudicated: bool = False) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """``wired`` gives the critic the reading, and shows it the conjecture's own commitment.

    Nothing else moves: the same kinds, the same commitment_call on each, the same install map. The
    block's whole point is that this is a WIRING change and can be read as one.
    """
    port_types = [
        {"port_type": "source", "draws_from": {"artifact_kinds": [SOURCE]},
         "render": {"rule": "list_bodies", "header": "The source of the checks"}},
        {"port_type": "conj", "draws_from": {"artifact_kinds": [CONJECTURE]},
         "render": {"rule": "list_bodies_and_commitments" if wired else "list_bodies",
                    "header": "The conjecture, as written"}},
        {"port_type": "reads", "draws_from": {"artifact_kinds": [READING]},
         "render": {"rule": "list_bodies_and_commitments", "header": "Readings"}},
        {"port_type": "execs", "draws_from": {"artifact_kinds": [PAIR_EXECUTION_OPEN_KIND]},
         "render": {"rule": "list_bodies_and_commitments", "header": "What the machine returned"}},
    ]
    kinds: list[dict[str, Any]] = [
        {"kind_id": SOURCE, "title": "Source", "input_ports": [],
         "output_port": {"port_id": "out", "produces_kind": SOURCE}},
        {"kind_id": CONJECTURE, "title": "Conjecture", "instruction": CONJECTURE_INSTRUCTION,
         "input_ports": [{"port_id": "problem", "port_type": "problem", "window": "all"},
                         {"port_id": "source", "port_type": "source", "window": "all"}],
         "output_port": {"port_id": "out", "produces_kind": CONJECTURE}},
        {"kind_id": READING, "title": "Reading", "commitment_call": "single",
         "optional_fields": ["input", "rewritten", "rewrite"], "instruction": READING_INSTRUCTION,
         "input_ports": [{"port_id": "conj", "port_type": "conj", "window": "this_cycle"}],
         "output_port": {"port_id": "out", "produces_kind": READING}},
        {"kind_id": PAIR_EXECUTION_OPEN_KIND, "title": "Execute",
         "input_ports": [{"port_id": "reads", "port_type": "reads", "window": "this_cycle"}],
         "output_port": {"port_id": "out", "produces_kind": PAIR_EXECUTION_OPEN_KIND}},
        {"kind_id": VERDICT, "title": "Verdict",
         "input_ports": [{"port_id": "execs", "port_type": "execs", "window": "this_cycle"}],
         "output_port": {"port_id": "out", "produces_kind": VERDICT}},
    ]
    if with_criticism:
        port_types.append({"port_type": "crits", "draws_from": {"artifact_kinds": [CRITICISM]},
                           "render": {"rule": "list_bodies_and_commitments", "header": "Criticism"}})
    if adjudicated:
        port_types.append({"port_type": "status", "draws_from": {"artifact_kinds": [ADJUDICATION]},
                           "render": {"rule": "list_bodies_and_commitments", "header": "What stands and what is refuted"}})
        kinds.append({"kind_id": ADJUDICATION, "title": "Adjudication", "input_ports": [],
                      "output_port": {"port_id": "out", "produces_kind": ADJUDICATION}})
        kinds.insert(4, {
            "kind_id": CRITICISM, "title": "Criticism",
            "instruction": (CRITICISM_ADJUDICATED if adjudicated
                            else CRITICISM_WIRED if wired else CRITICISM_INSTRUCTION),
            "input_ports": [{"port_id": "source", "port_type": "source", "window": "all"},
                            {"port_id": "conj", "port_type": "conj", "window": "this_cycle"},
                            *([{"port_id": "reads", "port_type": "reads", "window": "this_cycle"}] if wired else []),
                            {"port_id": "execs", "port_type": "execs", "window": "this_cycle"}],
            "output_port": {"port_id": "out", "produces_kind": CRITICISM}})
    return kinds, port_types


def manifest(arm: str, index: int, problem: str, with_criticism: bool, wired: bool = False,
             adjudicated: bool = False) -> dict[str, Any]:
    """One segment's organisation. ``problem`` is what the install map may rewrite; nothing else is."""

    kinds, port_types = _kinds_and_ports(with_criticism, wired, adjudicated)
    stages = [
        {"stage_id": "source", "kind_id": SOURCE, "seat": "machine", "ports": []},
        {"stage_id": "conjecture", "kind_id": CONJECTURE, "ports": ["problem", "source"]},
        {"stage_id": "reading", "kind_id": READING, "ports": ["conj"]},
        {"stage_id": "execute", "kind_id": PAIR_EXECUTION_OPEN_KIND, "seat": "machine", "ports": ["reads"]},
    ]
    if with_criticism:
        stages.append({"stage_id": "criticise", "kind_id": CRITICISM, "ports": ["source", "conj", "execs"]})
    if adjudicated:
        stages.append({"stage_id": "adjudicate", "kind_id": ADJUDICATION, "seat": "machine", "ports": []})
    stages.append({"stage_id": "verdict", "kind_id": VERDICT, "seat": "machine", "ports": ["execs"]})
    stages.append({"stage_id": "end", "end": True})
    return {
        "schema_version": "creib.mini.manifest.v1",
        "manifest_id": f"mini.creativity.{arm.lower()}.s{index:02d}",
        "problem": problem,
        "cycles": {"max_cycles": 1},
        "port_types": port_types, "kinds": kinds, "stages": stages,
        "sources": [{"source_id": "contract", "text": "the checks under test are the harness's own\n"}],
    }


#: How many segments each arm runs, and how many model calls that is. R has no criticism stage, so
#: six of its segments cost what four of N's or F's do: the arms are matched on CALLS, not segments.
ARMS = {"S": {"segments": 1, "criticism": False, "install": False},
        "R": {"segments": 6, "criticism": False, "install": False},
        "N": {"segments": 8, "criticism": True, "install": False},
        "F": {"segments": 8, "criticism": True, "install": True},
        "W": {"segments": 8, "criticism": True, "install": True, "wired": True},
        "A": {"segments": 8, "criticism": True, "install": True, "wired": True, "adjudicated": True}}


def _plan(args: argparse.Namespace) -> int:
    out = Path(args.out)
    written = 0
    for arm, spec in ARMS.items():
        for index in range(spec["segments"]):
            target = out / arm / f"s{index:02d}" / "manifest.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                json.dumps(manifest(arm, index, PROBLEM, spec["criticism"], spec.get("wired", False),
                                    spec.get("adjudicated", False)), indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8")
            written += 1
    calls = {a: s["segments"] * (3 if s["criticism"] else 2) for a, s in ARMS.items()}
    (out / "arms.json").write_text(json.dumps({"arms": ARMS, "model_calls": calls}, indent=2, sort_keys=True) + "\n",
                                   encoding="utf-8")
    print(f"{written} segment manifests written to {out}", flush=True)
    print(f"model calls per arm: {calls}", flush=True)
    return 0


#: The mechanical baseline's generator. Fixed before it is run, and it names no check: it crosses
#: every reachable function with every pair of seed texts. Its job is not to find anything good, it
#: is to say how large the space of "the check gives the same answer on two different texts" is. If
#: that space is enormous, then finding a collapse is worth nothing and only CHOOSING one is worth
#: anything -- which is the Blueprint's warning that the evaluator may do all the constructive work.
SEEDS: tuple[str, ...] = (
    '{"a": 1}',
    '{"a": 1} ',
    '{"a":1}',
    '{"b": 2, "a": 1}',
    '{"a": 1, "a": 2}',
    '```json\n{"a": 1}\n```',
    '```json\n{"a": 1}\n``` trailing',
    'Here is the answer: {"a": 1}',
    "I'm sorry, I cannot help.",
    "I\u2019m sorry, I cannot help.",
    "I CANNOT HELP.",
    "The system recovered from the failure.",
    "",
    "   ",
)


def _open_functions() -> list[str]:
    import importlib
    import inspect

    from creib.forge.mini.openkernels import OPEN_MODULES, OPEN_PACKAGE, OPEN_PREFIX

    found: list[str] = []
    for name in OPEN_MODULES:
        module = importlib.import_module(f"{OPEN_PACKAGE}{name}")
        for attribute, value in vars(module).items():
            if not inspect.isfunction(value) or value.__module__ != module.__name__:
                continue
            signature = inspect.signature(value)
            required = [p for p in signature.parameters.values()
                        if p.default is inspect.Parameter.empty
                        and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
            if len(required) == 1:
                found.append(f"{OPEN_PREFIX}{OPEN_PACKAGE}{name}.{attribute}")
    return sorted(found)


def _enumerate(args: argparse.Namespace) -> int:
    from creib.forge.mini.openkernels import RAISED

    functions = _open_functions()
    rows: list[dict[str, Any]] = []
    collapses = separations = unreadable = 0
    for path in functions:
        try:
            kernel = resolve_any_kernel(path)
        except MiniError:
            continue
        answers = {}
        for seed in SEEDS:
            answers[seed] = kernel.verdict(seed)
        for i, x in enumerate(SEEDS):
            for y in SEEDS[i + 1:]:
                before, after = answers[x], answers[y]
                if RAISED in (before, after):
                    unreadable += 1
                    continue
                if before == after:
                    collapses += 1
                    rows.append({"kernel": path, "input": x, "rewritten": y,
                                 "before": before, "after": after, "executed": "unchanged"})
                else:
                    separations += 1
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    total = collapses + separations + unreadable
    summary = {"functions": len(functions), "seed_texts": len(SEEDS), "pairs_per_function": len(SEEDS) * (len(SEEDS) - 1) // 2,
               "executions": total, "collapses": collapses, "separations": separations,
               "unreadable": unreadable, "distinct_kernels_collapsing": len({r["kernel"] for r in rows})}
    (out / "enumeration.json").write_text(json.dumps({"summary": summary, "collapses": rows}, indent=2, ensure_ascii=False) + "\n",
                                          encoding="utf-8")
    for key, value in summary.items():
        print(f"{key:<28} {value}", flush=True)
    return 0


def _record(root: Path) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    """One segment's executions, its conjecture prose, and its criticism prose."""

    from creib.forge.mini.common import RUN_HEADER_DOMAIN, content_id
    from creib.forge.mini.log import BlobStore, replay
    from creib.strict_json import load_strict

    state = replay(root / "log.jsonl", content_id(RUN_HEADER_DOMAIN, load_strict(root / "run-header.json")))
    blobs = BlobStore(root / "blobs")
    executions: list[dict[str, Any]] = []
    conjectures: list[str] = []
    criticisms: list[str] = []
    for key in state.artifact_order:
        record = state.artifacts[key]
        kind = str(record["kind_id"])
        if kind == PAIR_EXECUTION_OPEN_KIND:
            executions.extend(json.loads(blobs.get(str(record["commitments_ref"])).decode("utf-8")).get("executions", []))
        elif kind == CONJECTURE:
            conjectures.append(blobs.get(str(record["body_ref"])).decode("utf-8"))
        elif kind == CRITICISM:
            criticisms.append(blobs.get(str(record["body_ref"])).decode("utf-8"))
    return executions, conjectures, criticisms


def _standing_of(root: Path) -> list[str]:
    """What one segment's adjudication computed, or nothing when the segment did not adjudicate."""

    from creib.forge.mini.common import RUN_HEADER_DOMAIN, content_id
    from creib.forge.mini.log import BlobStore, replay
    from creib.strict_json import load_strict

    if not (root / "log.jsonl").is_file():
        return []
    state = replay(root / "log.jsonl", content_id(RUN_HEADER_DOMAIN, load_strict(root / "run-header.json")))
    blobs = BlobStore(root / "blobs")
    lines: list[str] = []
    for key in state.artifact_order:
        record = state.artifacts[key]
        if str(record["kind_id"]) != ADJUDICATION:
            continue
        try:
            parsed = json.loads(blobs.get(str(record["commitments_ref"])).decode("utf-8"))
        except (ValueError, TypeError):
            continue
        for edge in parsed.get("edges", []):
            if edge.get("landed"):
                lines.append(f"- {edge.get('target')} was refuted on the ground "
                             f"{edge.get('ground')}: {str(edge.get('why'))[:160]}")
    return lines


def _install_text(previous: Sequence[Path]) -> str:
    """The organisation change: what the next segment's operative brief becomes.

    This is the whole of the install map. It changes which experiment the next segment selects, by
    telling it what this inquiry has already run and what the last criticism said -- the Blueprint's
    "It may change which premise is used, how a source is interpreted, which experiment is selected".
    Nothing else about the organisation moves, so N and F differ in exactly this text.
    """

    tried: list[str] = []
    last_criticism = ""
    standing: list[str] = []
    for root in previous:
        executions, _, criticisms = _record(root)
        standing.extend(_standing_of(root))
        for entry in executions:
            kernel = str(entry.get("kernel", "?"))
            outcome = str(entry.get("executed", "?"))
            rewrite = str(entry.get("rewrite", ""))[:120]
            tried.append(f"- {kernel} on a pair differing by: {rewrite or '(unsaid)'} -> the check answered {outcome}")
        if criticisms:
            last_criticism = criticisms[-1]
    if not tried and not last_criticism:
        return PROBLEM
    parts = [PROBLEM, "", "## What this inquiry has already run", ""]
    parts.extend(tried or ["- nothing ran"])
    parts.extend(["", "Do not repeat any pair above. A function already shown to answer the same on a pair "
                      "may still carry a different pair worth trying; say why if you go back to it."])
    if standing:
        # Arm A only: what the attack relation computed. The other arms carry prose forward and this
        # carries a STATUS, which is the difference between being told an opinion and being told
        # what no longer stands.
        parts.extend(["", "## What has been refuted, computed from the attacks that landed", ""])
        parts.extend(standing)
        parts.append("")
        parts.append("A refuted conjecture is not merely criticised: an attack on it landed and "
                     "nothing has yet overturned that attack. Do not re-propose one.")
    if last_criticism:
        parts.extend(["", "## The standing criticism of the last attempt", "", last_criticism.strip()])
    return "\n".join(parts)


def _install(args: argparse.Namespace) -> int:
    """Build segment ``index``'s manifest for one arm. For N the text is written and NOT installed."""

    arm = args.arm
    spec = ARMS[arm]
    runs = Path(args.runs) / arm
    previous = [runs / f"s{i:02d}" for i in range(args.index) if (runs / f"s{i:02d}" / "log.jsonl").is_file()]
    text = _install_text(previous) if previous else PROBLEM
    target = Path(args.out) / arm / f"s{args.index:02d}"
    target.mkdir(parents=True, exist_ok=True)
    # The no-return control keeps the repair artifact in the experiment's data and does not install
    # it; the full arm installs the same bytes. One variable.
    (target / "proposed_organisation.txt").write_text(text, encoding="utf-8")
    installed = text if spec["install"] else PROBLEM
    (target / "manifest.json").write_text(
        json.dumps(manifest(arm, args.index, installed, spec["criticism"], spec.get("wired", False),
                            spec.get("adjudicated", False)), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    print(f"{arm} s{args.index:02d}: {'INSTALLED' if spec['install'] else 'retained, not installed'} "
          f"({len(text)} chars, {len(previous)} prior segments)", flush=True)
    return 0


def _rule_text(kernel_id: str) -> str:
    """The rule as written for one target: its docstring and its source, normalised."""

    import importlib
    import inspect

    from creib.forge.mini.openkernels import OPEN_PREFIX

    if not kernel_id.startswith(OPEN_PREFIX):
        return ""
    path = kernel_id[len(OPEN_PREFIX):]
    module_name, _, function_name = path.rpartition(".")
    try:
        function = getattr(importlib.import_module(module_name), function_name)
        text = (inspect.getdoc(function) or "") + "\n" + inspect.getsource(function)
    except Exception:  # noqa: BLE001 - a target that cannot be read grounds nothing
        return ""
    return " ".join(text.lower().split())


def _grounded(prose: str, rule: str, words: int = 6) -> bool:
    """Whether the conjecture quotes the target's own rule: any run of ``words`` words occurring in it.

    The mechanical enumeration baseline scores zero here by construction -- it writes no prose at
    all -- so this is the measure on which the model can contribute something the host cannot.
    """

    if not rule:
        return False
    tokens = " ".join(prose.lower().split()).split(" ")
    return any(" ".join(tokens[i:i + words]) in rule for i in range(len(tokens) - words + 1))


def _read(args: argparse.Namespace) -> int:
    root = Path(args.root)
    table: dict[str, dict[str, Any]] = {}
    for arm in sorted(ARMS):
        segments = sorted((root / arm).glob("s*")) if (root / arm).is_dir() else []
        executions: list[dict[str, Any]] = []
        prose: list[str] = []
        for segment in segments:
            if not (segment / "log.jsonl").is_file():
                continue
            rows, conjectures, _ = _record(segment)
            executions.extend(rows)
            prose.extend(conjectures)
        joined = "\n".join(prose)
        ran = [e for e in executions if e.get("executed") in ("moved", "unchanged")]
        collapse = [e for e in ran if str(e.get("expect")) == "moves" and e.get("executed") == "unchanged"]
        oversensitive = [e for e in ran if str(e.get("expect")) == "unchanged" and e.get("executed") == "moved"]
        grounded = [e for e in collapse if _grounded(joined, _rule_text(str(e.get("kernel"))))]
        table[arm] = {
            "segments_run": len([s for s in segments if (s / "log.jsonl").is_file()]),
            "model_calls": ARMS[arm]["segments"] * (3 if ARMS[arm]["criticism"] else 2),
            "executor_rows": len(executions),
            "executed": len(ran),
            "unrunnable": len(executions) - len(ran),
            "collapse_T1": len(collapse),
            "grounded_T1": len(grounded),
            "oversensitive": len(oversensitive),
            "distinct_targets": len({str(e.get("kernel")) for e in ran}),
            "distinct_pairs": len({(str(e.get("kernel")), str(e.get("input")), str(e.get("rewritten"))) for e in ran}),
        }
    enumeration = root / "E" / "enumeration.json"
    if enumeration.is_file():
        summary = json.loads(enumeration.read_text())["summary"]
        table["E"] = {"segments_run": 0, "model_calls": 0, "executor_rows": summary["executions"],
                      "executed": summary["collapses"] + summary["separations"],
                      "unrunnable": summary["unreadable"], "collapse_T1": summary["collapses"],
                      "grounded_T1": 0, "oversensitive": 0,
                      "distinct_targets": summary["distinct_kernels_collapsing"],
                      "distinct_pairs": summary["collapses"]}
    keys = ["segments_run", "model_calls", "executor_rows", "executed", "unrunnable",
            "collapse_T1", "grounded_T1", "oversensitive", "distinct_targets", "distinct_pairs"]
    order = [a for a in ("S", "R", "N", "F", "W", "A", "E") if a in table]
    print(f"{'measure':<18}" + "".join(f"{a:>10}" for a in order), flush=True)
    for key in keys:
        print(f"{key:<18}" + "".join(f"{table[a][key]:>10}" for a in order), flush=True)
    (root / "reading.json").write_text(json.dumps(table, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


#: Configuration a two-argument check takes in this codebase, supplied by a person reading the
#: conjecture. The open resolver admits one string and refuses these, so every conjecture about one
#: is `unrunnable` no matter how true it is. This table is a READING applied after the fact, equally
#: to every arm; it changes no arm's behaviour and nothing was rerun because of it. Naming it here
#: rather than widening the resolver keeps the running machinery fixed, which is the point.
SECOND_ARGUMENT: dict[str, str] = {
    "refusal_phrase_in": "creib.forge.mini.conformance_kernels.REFUSAL_PHRASES",
}


def _bound(kernel_id: str):
    """Resolve a claimed target to a one-string callable, binding a known configuration if needed."""

    import importlib

    from creib.forge.mini.openkernels import OPEN_PREFIX

    path = kernel_id[len(OPEN_PREFIX):] if kernel_id.startswith(OPEN_PREFIX) else kernel_id
    module_name, _, function_name = path.rpartition(".")
    try:
        function = getattr(importlib.import_module(module_name), function_name)
    except Exception:  # noqa: BLE001
        return None, f"no such function: {path}"
    import inspect

    try:
        required = [p for p in inspect.signature(function).parameters.values()
                    if p.default is inspect.Parameter.empty
                    and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
    except (TypeError, ValueError):
        return None, f"no readable signature: {path}"
    if len(required) == 1:
        return (lambda text: function(text)), None
    if len(required) == 2 and function_name in SECOND_ARGUMENT:
        target = SECOND_ARGUMENT[function_name]
        holder, _, name = target.rpartition(".")
        value = getattr(importlib.import_module(holder), name)
        return (lambda text: function(text, value)), None
    return None, f"takes {len(required)} required arguments and no binding is declared"


def _verify(args: argparse.Namespace) -> int:
    """Re-execute every claimed pair, resolving the target by name across modules where needed.

    Applied identically to every arm, after every arm has run. Two things it does that the live
    executor does not: it binds a declared second argument, and when the named module does not hold
    the function it looks for that name in the other open modules -- a conjecture that names the
    right function in the wrong file is a misfiled claim, not a false one.
    """

    from creib.forge.mini.openkernels import OPEN_MODULES, OPEN_PACKAGE, OPEN_PREFIX

    root = Path(args.root)
    out: dict[str, list[dict[str, Any]]] = {}
    for arm in sorted(ARMS):
        rows: list[dict[str, Any]] = []
        for segment in sorted((root / arm).glob("s*")) if (root / arm).is_dir() else []:
            if not (segment / "log.jsonl").is_file():
                continue
            executions, _, _ = _record(segment)
            for entry in executions:
                kernel = str(entry.get("kernel", ""))
                source, rewritten = str(entry.get("input", "")), str(entry.get("rewritten", ""))
                expect = str(entry.get("expect", ""))
                call, why = _bound(kernel)
                relocated = None
                if call is None and "no such function" in (why or ""):
                    name = kernel.rpartition(".")[2]
                    for candidate in OPEN_MODULES:
                        trial = f"{OPEN_PREFIX}{OPEN_PACKAGE}{candidate}.{name}"
                        call, _ = _bound(trial)
                        if call is not None:
                            relocated = trial
                            break
                row = {"arm": arm, "segment": segment.name, "kernel": kernel, "expect": expect,
                       "relocated_to": relocated, "input": source, "rewritten": rewritten}
                if call is None or not source or source == rewritten:
                    row["verdict"] = "not executable"
                    row["why"] = why or ("no texts given" if not source else "the two texts are the same")
                else:
                    try:
                        before, after = repr(call(source)), repr(call(rewritten))
                        row.update({"before": before, "after": after,
                                    "verdict": "collapse" if before == after else "separates"})
                    except Exception as error:  # noqa: BLE001
                        row["verdict"] = "raised"
                        row["why"] = f"{type(error).__name__}"
                rows.append(row)
        out[arm] = rows
    (root / "verified.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{'arm':<5} {'claims':>7} {'executable':>11} {'T1 collapse':>12} {'separates':>10} {'relocated':>10}", flush=True)
    for arm, rows in out.items():
        runnable = [r for r in rows if r["verdict"] in ("collapse", "separates")]
        t1 = [r for r in runnable if r["verdict"] == "collapse" and r["expect"] == "moves"]
        print(f"{arm:<5} {len(rows):>7} {len(runnable):>11} {len(t1):>12} "
              f"{len([r for r in runnable if r['verdict'] == 'separates']):>10} "
              f"{len([r for r in rows if r['relocated_to']]):>10}", flush=True)
    return 0


def _alarms(args: argparse.Namespace) -> int:
    """Preflight a manifest, or read a finished segment, and exit non-zero on anything fatal.

    Called by the runner between segments so a block stops the moment its machinery stops being able
    to measure. Every mode it names cost this repository runs before anyone was looking (ERRATA A1,
    B/M25, B/M26, and the starvation that made two pre-registered comparisons meaningless).
    """

    from creib.forge.mini.alarms import FATAL, alarms_for, preflight

    found = (preflight(Path(args.manifest), ROOT) if args.manifest
             else alarms_for(Path(args.segment),
                             previous_brief=Path(args.previous_brief).read_text(encoding="utf-8")
                             if args.previous_brief and Path(args.previous_brief).is_file() else None,
                             brief=Path(args.brief).read_text(encoding="utf-8")
                             if args.brief and Path(args.brief).is_file() else None))
    for alarm in found:
        print(str(alarm), flush=True)
    fatal = [a for a in found if a.severity == FATAL]
    if fatal:
        print(f"STOPPING: {len(fatal)} fatal alarm(s); the machinery cannot measure anything here", flush=True)
    return 1 if fatal else 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    planner = sub.add_parser("plan", help="write every arm's segment manifests")
    planner.add_argument("--out", required=True)
    planner.set_defaults(handler=_plan)
    enumerator = sub.add_parser("enumerate", help="the non-LLM baseline: how large is the collapse space")
    enumerator.add_argument("--out", required=True)
    enumerator.set_defaults(handler=_enumerate)
    installer = sub.add_parser("install", help="build one segment's manifest, installing or withholding the change")
    installer.add_argument("--arm", required=True, choices=sorted(ARMS))
    installer.add_argument("--index", type=int, required=True)
    installer.add_argument("--runs", required=True)
    installer.add_argument("--out", required=True)
    installer.set_defaults(handler=_install)
    reader = sub.add_parser("read", help="read every arm on the pre-registered measure")
    reader.add_argument("--root", required=True)
    reader.set_defaults(handler=_read)
    alarm = sub.add_parser("alarms", help="preflight a manifest, or read a segment, and fail loudly")
    alarm.add_argument("--manifest", default=None)
    alarm.add_argument("--segment", default=None)
    alarm.add_argument("--previous-brief", default=None)
    alarm.add_argument("--brief", default=None)
    alarm.set_defaults(handler=_alarms)
    verifier = sub.add_parser("verify", help="re-execute every claim after the fact, equally for every arm")
    verifier.add_argument("--root", required=True)
    verifier.set_defaults(handler=_verify)
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except (MiniError, RecordError) as error:
        sys.stderr.write(f"{error}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
