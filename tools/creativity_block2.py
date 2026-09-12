#!/usr/bin/env python3
"""CREATIVITY-ARMS-2: the same comparison with the machinery repaired.

    python tools/creativity_block2.py enumerate --out forge/mini/runs/creativity-2/E
    python tools/creativity_block2.py block --arm W --repeat 0 --model deepseek-v4-pro \
        --manifests forge/mini/manifests/creativity-2 --runs forge/mini/runs/creativity-2
    python tools/creativity_block2.py read   --root forge/mini/runs/creativity-2
    python tools/creativity_block2.py verify --root forge/mini/runs/creativity-2

Block 1 is ``tools/creativity_arms.py`` and it is left exactly as it ran. This is a new method
version, so nothing here is compared arm-for-arm with a block-1 number; the seven differences are
listed in ``docs/mini/NEXT_BLOCK.md`` and each answers a numbered entry of ``docs/mini/ERRATA.md``:

1. a format schema on the criticism commitment, with ``cannot-tell`` kept as an escape road (C6);
2. the ``test-is-unsound`` ground, so the executor itself can be attacked (C5);
3. a baseline whose seeds make each function vary, and a measure both it and the arms can score
   on (A3, A4);
4. a declared stochastic floor: three repeats, differing in the endpoint seed and nothing else (C7);
5. sixteen segments per arm, and only the four arms whose contrast is live (the power problem);
6. arity binding and module relocation in the live executor, with the post-hoc verifier kept as a
   check ON it rather than a substitute FOR it (C9);
7. one failure policy, identical on every kind of every arm, so "how strict is the form" and "how
   long does the run live" are not varied together (CON-FORMAT-KILLS-RUN).

What it still does not repair is named in the same document: mini dispatches on kind rather than on
interface structure, and a commitment carries no eval and no budget (C3, C4).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from creib.errors import RecordError  # noqa: E402
from creib.forge.mini.common import MiniError  # noqa: E402
from creib.forge.mini.openkernels import PAIR_EXECUTION_OPEN_KIND, resolve_any_kernel  # noqa: E402

from creativity_arms import (  # noqa: E402
    ADJUDICATION,
    CONJECTURE,
    CONJECTURE_INSTRUCTION,
    CRITICISM,
    CRITICISM_INSTRUCTION,
    CRITICISM_WIRED,
    PROBLEM,
    READING,
    READING_INSTRUCTION as READING_INSTRUCTION_BLOCK1,
    SOURCE,
    VERDICT,
    _bound,
    _grounded,
    _record,
    _rule_text,
    _standing_of,
)

#: The translator's three texts, declared as a shape rather than only asked for in prose. Nine of
#: thirty-nine readings in block 1 returned ``kernel`` and ``expect`` and no pair at all; the format
#: layer read only ``body`` and ``commitments``, so nothing could tell those replies from an answer
#: and each was recorded as the executor refusing an ``unrunnable`` claim. A missing field is now a
#: refusal with the shape rendered, and the seat is asked again.
READING_FIELDS: dict[str, Any] = {
    name: {"all_of": [{"check": "regex", "pattern": r"\S"}]} for name in ("input", "rewritten", "rewrite")
}

#: Block 1's instruction, and a whole worked reply under it. The instruction alone was what failed:
#: it named the three fields in a sentence and nearly a quarter of the replies did not carry them.
READING_INSTRUCTION = READING_INSTRUCTION_BLOCK1 + (
    "\n\nThe three texts are fields of the REPLY, beside \"body\" and \"commitments\", not inside "
    "the commitments string. A reply that omits any of them is refused and you are asked again. In "
    "full, a well formed reply looks exactly like this:\n\n"
    '{"body": "<what you were unsure of, in prose>",\n'
    ' "commitments": "{\\"kernel\\": \\"<the full dotted path>\\", \\"expect\\": \\"moves\\"}",\n'
    ' "input": "<the first reply text, in full>",\n'
    ' "rewritten": "<the second reply text, in full>",\n'
    ' "rewrite": "<how the two differ>"}'
)

#: One policy, on every kind of every arm. Three retries rather than one: a seat whose answer misses
#: a declared shape is re-asked with the shape rendered, and a kind with no declared shape can never
#: use them, so the SAME policy costs the unschema'd arms nothing. Tolerance stays unlimited, which
#: is what stops an arm dying younger for being asked a stricter question (CON-FORMAT-KILLS-RUN).
FAILURE_POLICY: dict[str, Any] = {"retries": 3, "tolerance": None, "action": "stop",
                                  "skip_on_empty_port": False}

#: The endpoint, declared in the manifest so the seed is a declared part of the plan rather than a
#: shipped default nobody wrote down. The seed is the ONLY thing that differs between repeats.
SEEDS: tuple[int, ...] = (7, 8, 9)
REPEATS = len(SEEDS)
SEGMENTS = 16

#: The five grounds, closed, with the escape road kept first-class. ``test-is-unsound`` is the one
#: this block adds, and its target is an EXECUTION rather than a conjecture: the machinery to say
#: "the test was wrong" is what ERRATA C5 says was missing.
GROUND_PATTERN = ("^(reading-misrenders-conjecture|conjecture-misreads-rule|rule-and-code-diverge|"
                  "test-is-unsound|cannot-tell)$")

CRITICISM_SCHEMA: dict[str, Any] = {
    "check": "json_schema",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["attacks", "ground", "why"],
        "properties": {
            "attacks": {"type": "string", "minLength": 8, "maxLength": 64},
            "ground": {"type": "string", "pattern": GROUND_PATTERN},
            "why": {"type": "string", "minLength": 1, "maxLength": 2000},
        },
    },
}

#: Arm A's critic. The wired text unchanged, plus the warrant, plus the one new ground. The schema
#: above is what makes a missed shape a RETRY rather than a silent prose answer: four of eight of
#: block 1's criticisms wrote prose where JSON was asked for and nothing checked.
CRITICISM_ADJUDICATED = CRITICISM_WIRED + (
    "\n\nYour commitments are a STRING holding JSON of the form "
    '{"attacks": "<the first 16 characters of the artifact id you are attacking>", '
    '"ground": "<one of: reading-misrenders-conjecture, conjecture-misreads-rule, '
    'rule-and-code-diverge, test-is-unsound, cannot-tell>", "why": "<one sentence>"} and nothing '
    "else.\n\n"
    "The id must be one printed in square brackets beside an artifact you were shown; a name "
    "matching nothing resolves to no attack.\n\n"
    "Use \"test-is-unsound\" when the fault is in the RUN rather than in what was claimed: the "
    "executor refused a claim it should have been able to run, bound the wrong thing, or answered "
    "on something other than what the claim named. Its target is the EXECUTION artifact, not the "
    "conjecture. The machine has already recorded, against each reading, whether the run bore its "
    "claim out; attacking the execution as unsound is how a reading the machine wrongly refused "
    "gets back up.\n\n"
    "Use \"cannot-tell\" when you cannot decide -- it is an honest answer and it mints no attack, "
    "which is better than inventing a target."
)

#: Four arms, sixteen segments each, three repeats. ``S`` and ``N`` are dropped: ``S`` because one
#: conjecture at two calls is stable across three blocks and nothing further is learnt by running it
#: again, ``N`` because block 1's N-against-F null was withdrawn (ERRATA A2) -- F repeated itself
#: twice while being told not to, so the contrast measured the carry being ignored, not the carry
#: being worthless, and the live contrast is F against W.
ARMS: dict[str, dict[str, Any]] = {
    "R": {"segments": SEGMENTS, "criticism": False, "install": False},
    "F": {"segments": SEGMENTS, "criticism": True, "install": True},
    "W": {"segments": SEGMENTS, "criticism": True, "install": True, "wired": True},
    "A": {"segments": SEGMENTS, "criticism": True, "install": True, "wired": True, "adjudicated": True},
}


def _endpoint(seed: int) -> dict[str, Any]:
    return {"kind": "ollama-chat", "base_url": "https://ollama.com", "timeout_seconds": 900,
            "options": {"temperature": 0, "seed": seed}, "think": None}


def _kinds_and_ports(with_criticism: bool, wired: bool, adjudicated: bool) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """One policy on every kind, one schema on arm A's criticism, and ``wired`` meaning what it says.

    Block 1's ``wired`` did two things and neither was the one it was named for (ERRATA C12): it
    rendered the CONJECTURE's commitments where F rendered only its body, and it told the critic to
    attack a reading its stage never declared a port for, so the readings were never rendered. Here
    the conjecture is rendered the same way for every arm, and ``wired`` is the readings port on the
    criticism STAGE plus the instruction that says what to do with it. One change, and the text that
    makes it usable: a port a seat is not told to read is not a treatment.
    """

    port_types = [
        {"port_type": "source", "draws_from": {"artifact_kinds": [SOURCE]},
         "render": {"rule": "list_bodies", "header": "The source of the checks"}},
        {"port_type": "conj", "draws_from": {"artifact_kinds": [CONJECTURE]},
         "render": {"rule": "list_bodies", "header": "The conjecture, as written"}},
        {"port_type": "reads", "draws_from": {"artifact_kinds": [READING]},
         "render": {"rule": "list_bodies_and_commitments", "header": "Readings"}},
        {"port_type": "execs", "draws_from": {"artifact_kinds": [PAIR_EXECUTION_OPEN_KIND]},
         "render": {"rule": "list_bodies_and_commitments", "header": "What the machine returned"}},
    ]
    kinds: list[dict[str, Any]] = [
        {"kind_id": SOURCE, "title": "Source", "input_ports": [], "failure_policy": FAILURE_POLICY,
         "output_port": {"port_id": "out", "produces_kind": SOURCE}},
        {"kind_id": CONJECTURE, "title": "Conjecture", "instruction": CONJECTURE_INSTRUCTION,
         "failure_policy": FAILURE_POLICY,
         "input_ports": [{"port_id": "problem", "port_type": "problem", "window": "all"},
                         {"port_id": "source", "port_type": "source", "window": "all"}],
         "output_port": {"port_id": "out", "produces_kind": CONJECTURE}},
        {"kind_id": READING, "title": "Reading", "commitment_call": "single",
         "optional_fields": ["input", "rewritten", "rewrite"], "instruction": READING_INSTRUCTION,
         "failure_policy": FAILURE_POLICY, "format": {"fields": READING_FIELDS},
         "input_ports": [{"port_id": "conj", "port_type": "conj", "window": "this_cycle"}],
         "output_port": {"port_id": "out", "produces_kind": READING}},
        {"kind_id": PAIR_EXECUTION_OPEN_KIND, "title": "Execute", "failure_policy": FAILURE_POLICY,
         "input_ports": [{"port_id": "reads", "port_type": "reads", "window": "this_cycle"}],
         "output_port": {"port_id": "out", "produces_kind": PAIR_EXECUTION_OPEN_KIND}},
        {"kind_id": VERDICT, "title": "Verdict", "failure_policy": FAILURE_POLICY,
         "input_ports": [{"port_id": "execs", "port_type": "execs", "window": "this_cycle"}],
         "output_port": {"port_id": "out", "produces_kind": VERDICT}},
    ]
    if with_criticism:
        port_types.append({"port_type": "crits", "draws_from": {"artifact_kinds": [CRITICISM]},
                           "render": {"rule": "list_bodies_and_commitments", "header": "Criticism"}})
        criticism: dict[str, Any] = {
            "kind_id": CRITICISM, "title": "Criticism", "failure_policy": FAILURE_POLICY,
            "instruction": (CRITICISM_ADJUDICATED if adjudicated
                            else CRITICISM_WIRED if wired else CRITICISM_INSTRUCTION),
            "input_ports": [{"port_id": "source", "port_type": "source", "window": "all"},
                            {"port_id": "conj", "port_type": "conj", "window": "this_cycle"},
                            *([{"port_id": "reads", "port_type": "reads", "window": "this_cycle"}] if wired else []),
                            {"port_id": "execs", "port_type": "execs", "window": "this_cycle"}],
            "output_port": {"port_id": "out", "produces_kind": CRITICISM}}
        if adjudicated:
            criticism["format"] = {"commitments": {"all_of": [CRITICISM_SCHEMA]}}
        kinds.insert(4, criticism)
    if adjudicated:
        port_types.append({"port_type": "status", "draws_from": {"artifact_kinds": [ADJUDICATION]},
                           "render": {"rule": "list_bodies_and_commitments",
                                      "header": "What stands and what is refuted"}})
        kinds.append({"kind_id": ADJUDICATION, "title": "Adjudication", "input_ports": [],
                      "failure_policy": FAILURE_POLICY,
                      "output_port": {"port_id": "out", "produces_kind": ADJUDICATION}})
    return kinds, port_types


def manifest(arm: str, repeat: int, index: int, problem: str) -> dict[str, Any]:
    spec = ARMS[arm]
    kinds, port_types = _kinds_and_ports(spec["criticism"], spec.get("wired", False),
                                         spec.get("adjudicated", False))
    stages = [
        {"stage_id": "source", "kind_id": SOURCE, "seat": "machine", "ports": []},
        {"stage_id": "conjecture", "kind_id": CONJECTURE, "ports": ["problem", "source"]},
        {"stage_id": "reading", "kind_id": READING, "ports": ["conj"]},
        {"stage_id": "execute", "kind_id": PAIR_EXECUTION_OPEN_KIND, "seat": "machine", "ports": ["reads"]},
    ]
    if spec["criticism"]:
        stages.append({"stage_id": "criticise", "kind_id": CRITICISM,
                       "ports": ["source", "conj"] + (["reads"] if spec.get("wired") else []) + ["execs"]})
    if spec.get("adjudicated"):
        stages.append({"stage_id": "adjudicate", "kind_id": ADJUDICATION, "seat": "machine", "ports": []})
    stages.append({"stage_id": "verdict", "kind_id": VERDICT, "seat": "machine", "ports": ["execs"]})
    stages.append({"stage_id": "end", "end": True})
    return {
        "schema_version": "creib.mini.manifest.v1",
        "manifest_id": f"mini.creativity2.{arm.lower()}.r{repeat}.s{index:02d}",
        "problem": problem,
        "cycles": {"max_cycles": 1},
        "endpoint": _endpoint(SEEDS[repeat]),
        "port_types": port_types, "kinds": kinds, "stages": stages,
        "sources": [{"source_id": "contract", "text": "the checks under test are the harness's own\n"}],
    }


# ---------------------------------------------------------------------------------------------
# The install map: unchanged from block 1 in what it computes, and it reads this block's layout.
# ---------------------------------------------------------------------------------------------


#: The most a carried brief may grow to. The manifest schema caps ``problem`` at 8192 characters and
#: arm A reached 8310 at segment 14 of 16, which ended the arm on a schema refusal rather than on
#: anything about the subject. The ceiling is declared, applies identically to every arm, and drops
#: the OLDEST "already run" lines first, because the standing refutations and the last criticism are
#: the part of the brief that is about what to do next.
BRIEF_CEILING = 7800


def _install_text(previous: Sequence[Path]) -> str:
    """What the next segment's operative brief becomes.

    The standing refutations come from the LAST previous segment only, exactly as the criticism
    does. Accumulating every landed attack from every segment forever was an inconsistency in this
    map's own design: it kept one criticism and all refutations, so arm A's brief grew at twice the
    rate of the arms it is compared with, and "the attacks land" and "the brief is much longer" were
    one treatment.
    """

    tried: list[str] = []
    last_criticism = ""
    standing: list[str] = []
    for root in previous:
        executions, _, criticisms = _record(root)
        # rstripped here rather than in block 1's tool, which stays as it ran: the truncation at
        # 160 characters can cut mid-word and leave a trailing space, which then reaches a record
        # blob and stays there for good, because a record is never edited.
        standing = [line.rstrip() for line in _standing_of(root)] or standing
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
        parts.extend(["", "## What has been refuted, computed from the attacks that landed", ""])
        parts.extend(standing)
        parts.append("")
        parts.append("A refuted conjecture is not merely criticised: an attack on it landed and "
                     "nothing has yet overturned that attack. Do not re-propose one.")
    if last_criticism:
        parts.extend(["", "## The standing criticism of the last attempt", "", last_criticism.strip()])
    return _under_ceiling(parts, len(tried))


def _under_ceiling(parts: list[str], tried: int) -> str:
    """Hold the brief to the ceiling: drop the oldest attempts first, then trim the tail.

    The oldest "already run" lines go first because the standing refutations and the last criticism
    are the part of the brief that is about what to do next. If dropping every attempt but one still
    leaves it over, the tail is cut, because a brief the schema refuses ends the arm and a brief that
    is one paragraph short does not.
    """

    def joined(rows: list[str]) -> str:
        return "\n".join(rows)

    if len(joined(parts)) <= BRIEF_CEILING:
        return joined(parts)
    note = "- ({} earlier attempt(s) dropped: this brief is held to {} characters)"
    rows = list(parts)
    first = next((i for i, line in enumerate(rows) if line.startswith("- ")), None)
    dropped = 0
    while first is not None and dropped < max(tried - 1, 0) and len(joined(rows)) > BRIEF_CEILING:
        rows.pop(first)
        dropped += 1
    if dropped:
        rows.insert(first, note.format(dropped, BRIEF_CEILING))
    text = joined(rows)
    if len(text) > BRIEF_CEILING:
        cut = "\n\n(this brief was cut to fit its ceiling)"
        text = text[:BRIEF_CEILING - len(cut)].rstrip() + cut
    return text


def _segment_dir(root: Path, arm: str, repeat: int, index: int) -> Path:
    return root / arm / f"r{repeat}" / f"s{index:02d}"


def _build(arm: str, repeat: int, index: int, runs: Path, manifests: Path) -> Path:
    """Write segment ``index``'s manifest and its proposed organisation; return the manifest path."""

    previous = [_segment_dir(runs, arm, repeat, i) for i in range(index)
                if (_segment_dir(runs, arm, repeat, i) / "log.jsonl").is_file()]
    text = _install_text(previous) if previous else PROBLEM
    target = _segment_dir(manifests, arm, repeat, index)
    target.mkdir(parents=True, exist_ok=True)
    (target / "proposed_organisation.txt").write_text(text, encoding="utf-8")
    installed = text if ARMS[arm]["install"] else PROBLEM
    path = target / "manifest.json"
    path.write_text(json.dumps(manifest(arm, repeat, index, installed), indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    return path


# ---------------------------------------------------------------------------------------------
# The mechanical baseline, repaired: seeds chosen so each function VARIES before a pair is counted.
# ---------------------------------------------------------------------------------------------

#: Block 1's fourteen seeds, and enough beside them that a function about something other than JSON
#: has a chance of answering two ways. 458 of block 1's 460 collapses were on functions constant
#: over its seeds, which makes "460 collapses" a statement about the seed list (ERRATA A3, A4).
SEEDS_POOL: tuple[str, ...] = (
    '{"a": 1}', '{"a": 1} ', '{"a":1}', '{"b": 2, "a": 1}', '{"a": 1, "a": 2}',
    '```json\n{"a": 1}\n```', '```json\n{"a": 1}\n``` trailing', 'Here is the answer: {"a": 1}',
    "I'm sorry, I cannot help.", "I’m sorry, I cannot help.", "I CANNOT HELP.",
    "The system recovered from the failure.", "", "   ",
    "absent", "unknown", "present", "ABSENT", " absent ", "not_applicable",
    "PASS", "FAIL", "UNKNOWN", "REFUTED", "UNREFUTED_FOR_DECLARED_SCOPE",
    "moves", "unchanged", "true", "false", "null", "0", "1", "-1", "1.5",
    "2026-09-11", "11/09/2026", "GBP 10.00", "10.00", "£10.00",
    "a", "a b", "a\nb", "a\r\nb", "\ta", "a\t", "A" * 200,
    "[]", "[1, 2]", '{"a": {"b": 1}}', '{"a": [1, 2]}', "{}",
    "open:creib.forge.conformance.oracle.recover_json_object",
    "conformance.kernel.refusal-phrase", "mini.conjecture.v1",
    "The model declined.", "As an AI language model, I cannot.", "Sorry, no.",
    "é", "é́", "é", "﻿{\"a\": 1}",
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


def varying_functions() -> dict[str, bool]:
    """Every reachable one-string function, and whether it answers two ways over the pool.

    A function constant over everything the pool can show it has no pair that separates, so every
    pair of it collapses and none of those collapses is worth counting. This is the denominator
    block 1 did not have.
    """

    from creib.forge.mini.openkernels import RAISED

    out: dict[str, bool] = {}
    for path in _open_functions():
        try:
            kernel = resolve_any_kernel(path)
        except MiniError:
            continue
        answers = {kernel.verdict(seed) for seed in SEEDS_POOL}
        answered = {a for a in answers if a != RAISED}
        out[path] = len(answered) > 1
    return out


def _enumerate(args: argparse.Namespace) -> int:
    from creib.forge.mini.openkernels import RAISED

    varies = varying_functions()
    rows: list[dict[str, Any]] = []
    collapses = separations = unreadable = 0
    varying_collapses = 0
    for path, non_constant in varies.items():
        kernel = resolve_any_kernel(path)
        answers = {seed: kernel.verdict(seed) for seed in SEEDS_POOL}
        for i, x in enumerate(SEEDS_POOL):
            for y in SEEDS_POOL[i + 1:]:
                before, after = answers[x], answers[y]
                if RAISED in (before, after):
                    unreadable += 1
                    continue
                if before == after:
                    collapses += 1
                    if non_constant:
                        varying_collapses += 1
                        rows.append({"kernel": path, "input": x, "rewritten": y,
                                     "before": before, "after": after, "executed": "unchanged"})
                else:
                    separations += 1
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    summary = {
        "functions": len(varies),
        "non_constant_functions": sum(1 for v in varies.values() if v),
        "seed_texts": len(SEEDS_POOL),
        "pairs_per_function": len(SEEDS_POOL) * (len(SEEDS_POOL) - 1) // 2,
        "executions": collapses + separations + unreadable,
        "collapses": collapses,
        "collapses_on_non_constant": varying_collapses,
        "separations": separations,
        "unreadable": unreadable,
        "distinct_non_constant_kernels_collapsing": len({r["kernel"] for r in rows}),
    }
    (out / "enumeration.json").write_text(
        json.dumps({"summary": summary, "non_constant": sorted(k for k, v in varies.items() if v),
                    "collapses": rows}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for key, value in summary.items():
        print(f"{key:<38} {value}", flush=True)
    return 0


# ---------------------------------------------------------------------------------------------
# Reading. Every measure is per (arm, repeat) so the floor is visible rather than averaged away.
# ---------------------------------------------------------------------------------------------


#: What one entry into a model stage costs in calls. A kind whose ``commitment_call`` is ``two``
#: costs two; the reading, declared ``single``, costs one. Block 1 counted STAGES and called them
#: calls, so every per-call figure in it was low by between 1.7 and 2.0 -- unevenly, because a
#: refused submission is a call the arm paid for and the arms refused at different rates (C13).
CALLS_PER_STAGE: dict[str, int] = {CONJECTURE: 2, CRITICISM: 2, READING: 1}


def _calls(segment: Path) -> int:
    """Model calls this segment actually made: every model stage entered, plus every refusal."""

    made = 0
    for line in (segment / "log.jsonl").read_text(encoding="utf-8").splitlines():
        event = json.loads(line)
        if event["type"] == "STAGE_ENTERED":
            made += CALLS_PER_STAGE.get(str(event.get("kind_id")), 0)
        elif event["type"] == "FORMAT_FAILURE":
            made += 1
    return made


def _segments(root: Path, arm: str, repeat: int) -> list[Path]:
    """This cell's FINISHED segments, and nothing else.

    A log file is not a finished segment. A transport failure leaves a root holding a conjecture, a
    reading and no execution, and this used to return those beside the real ones because it asked
    only whether a log existed: R.r1 read as twenty segments where sixteen had finished, and the call
    count and the row count were both inflated by the difference. A run that did not reach its end is
    not a measurement of anything.
    """

    place = root / arm / f"r{repeat}"
    if not place.is_dir():
        return []
    return [s for s in sorted(place.glob("s*"))
            if _finished(s) and ".dead" not in s.name]


def _dropped(segment: Path) -> int:
    """Submissions this segment dropped on format. Recorded per arm, per repair 7."""

    return sum(1 for line in (segment / "log.jsonl").read_text(encoding="utf-8").splitlines()
               if '"SUBMISSION_DROPPED"' in line)


def _adjudication(segment: Path) -> dict[str, int]:
    """What the adjudication stage computed, or zeroes when the segment did not adjudicate."""

    from creib.forge.mini.common import RUN_HEADER_DOMAIN, content_id
    from creib.forge.mini.log import BlobStore, replay
    from creib.strict_json import load_strict

    out = {"criticisms": 0, "attacks_landed": 0, "evidence_edges": 0}
    if not (segment / "log.jsonl").is_file():
        return out
    state = replay(segment / "log.jsonl", content_id(RUN_HEADER_DOMAIN, load_strict(segment / "run-header.json")))
    blobs = BlobStore(segment / "blobs")
    for key in state.artifact_order:
        record = state.artifacts[key]
        if str(record["kind_id"]) != ADJUDICATION:
            continue
        try:
            parsed = json.loads(blobs.get(str(record["commitments_ref"])).decode("utf-8"))
        except (ValueError, TypeError):
            continue
        for name in out:
            value = parsed.get(name)
            if isinstance(value, int):
                out[name] += value
    return out


def _grounds_used(segment: Path) -> dict[str, int]:
    """Which grounds a segment's criticisms stood on, counted by name."""

    from creib.forge.mini.common import RUN_HEADER_DOMAIN, content_id
    from creib.forge.mini.log import BlobStore, replay
    from creib.strict_json import load_strict

    counts: dict[str, int] = {}
    state = replay(segment / "log.jsonl", content_id(RUN_HEADER_DOMAIN, load_strict(segment / "run-header.json")))
    blobs = BlobStore(segment / "blobs")
    for key in state.artifact_order:
        record = state.artifacts[key]
        if str(record["kind_id"]) != CRITICISM:
            continue
        try:
            parsed = json.loads(blobs.get(str(record["commitments_ref"])).decode("utf-8"))
        except (ValueError, TypeError):
            counts["(not JSON)"] = counts.get("(not JSON)", 0) + 1
            continue
        ground = str(parsed.get("ground", "(none)")) if isinstance(parsed, dict) else "(not an object)"
        counts[ground] = counts.get(ground, 0) + 1
    return counts


def _cell(root: Path, arm: str, repeat: int, varies: dict[str, bool]) -> dict[str, Any]:
    executions: list[dict[str, Any]] = []
    prose: list[str] = []
    dropped = 0
    adjudication = {"criticisms": 0, "attacks_landed": 0, "evidence_edges": 0}
    grounds: dict[str, int] = {}
    segments = _segments(root, arm, repeat)
    calls = 0
    for segment in segments:
        calls += _calls(segment)
        rows, conjectures, _ = _record(segment)
        executions.extend(rows)
        prose.extend(conjectures)
        dropped += _dropped(segment)
        for name, value in _adjudication(segment).items():
            adjudication[name] += value
        for name, value in _grounds_used(segment).items():
            grounds[name] = grounds.get(name, 0) + value
    joined = "\n".join(prose)
    ran = [e for e in executions if e.get("executed") in ("moved", "unchanged")]
    collapse = [e for e in ran if str(e.get("expect")) == "moves" and e.get("executed") == "unchanged"]
    grounded = [e for e in collapse if _grounded(joined, _rule_text(str(e.get("kernel"))))]
    non_constant = [e for e in collapse if varies.get(str(e.get("kernel")), False)]
    return {
        "segments_run": len(segments),
        "model_calls": calls,
        "executor_rows": len(executions),
        "executed": len(ran),
        "unrunnable": len(executions) - len(ran),
        "format_drops": dropped,
        "collapse_T1": len(collapse),
        "collapse_on_non_constant": len(non_constant),
        "grounded_T1": len(grounded),
        "oversensitive": len([e for e in ran if str(e.get("expect")) == "unchanged" and e.get("executed") == "moved"]),
        "distinct_targets": len({str(e.get("kernel")) for e in ran}),
        "distinct_pairs": len({(str(e.get("kernel")), str(e.get("input")), str(e.get("rewritten"))) for e in ran}),
        "criticisms": adjudication["criticisms"],
        "attacks_landed": adjudication["attacks_landed"],
        "evidence_edges": adjudication["evidence_edges"],
        "grounds": grounds,
    }


_KEYS = ("segments_run", "model_calls", "executor_rows", "executed", "unrunnable", "format_drops",
         "collapse_T1", "collapse_on_non_constant", "grounded_T1", "oversensitive",
         "distinct_targets", "distinct_pairs", "criticisms", "attacks_landed", "evidence_edges")


def _read(args: argparse.Namespace) -> int:
    root = Path(args.root)
    enumeration = root / "E" / "enumeration.json"
    varies: dict[str, bool] = {}
    if enumeration.is_file():
        varies = {path: True for path in json.loads(enumeration.read_text())["non_constant"]}
    else:
        varies = varying_functions()
    table: dict[str, dict[str, Any]] = {}
    for arm in ARMS:
        for repeat in range(REPEATS):
            if _segments(root, arm, repeat):
                table[f"{arm}.r{repeat}"] = _cell(root, arm, repeat, varies)
    order = sorted(table)
    print(f"{'measure':<26}" + "".join(f"{a:>9}" for a in order), flush=True)
    for key in _KEYS:
        print(f"{key:<26}" + "".join(f"{table[a][key]:>9}" for a in order), flush=True)
    print("", flush=True)
    for name in order:
        used = table[name]["grounds"]
        if used:
            print(f"{name} grounds: " + ", ".join(f"{g}={c}" for g, c in sorted(used.items())), flush=True)
    (root / "reading.json").write_text(json.dumps(table, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


def _verify(args: argparse.Namespace) -> int:
    """Re-execute every claim after the fact. Kept as a CHECK ON the live executor, not a substitute.

    Repair 6: the live executor now binds a declared second argument and relocates a misfiled module
    itself, so this pass should agree with it everywhere. Where the two disagree, the disagreement
    is the finding, and it is printed rather than folded into a total.
    """

    from creib.forge.mini.openkernels import OPEN_MODULES, OPEN_PACKAGE, OPEN_PREFIX

    root = Path(args.root)
    out: dict[str, list[dict[str, Any]]] = {}
    disagreements = 0
    for arm in ARMS:
        for repeat in range(REPEATS):
            rows: list[dict[str, Any]] = []
            for segment in _segments(root, arm, repeat):
                executions, _, _ = _record(segment)
                for entry in executions:
                    kernel = str(entry.get("kernel", ""))
                    source, rewritten = str(entry.get("input", "")), str(entry.get("rewritten", ""))
                    row = {"arm": arm, "repeat": repeat, "segment": segment.name, "kernel": kernel,
                           "expect": str(entry.get("expect", "")), "live": str(entry.get("executed", "")),
                           "relocated_to": None, "input": source, "rewritten": rewritten}
                    call, why = _bound(kernel)
                    if call is None and "no such function" in (why or ""):
                        name = kernel.rpartition(".")[2]
                        for candidate in OPEN_MODULES:
                            call, _ = _bound(f"{OPEN_PREFIX}{OPEN_PACKAGE}{candidate}.{name}")
                            if call is not None:
                                row["relocated_to"] = f"{OPEN_PREFIX}{OPEN_PACKAGE}{candidate}.{name}"
                                break
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
                    expected_live = {"collapse": "unchanged", "separates": "moved"}.get(str(row["verdict"]))
                    row["agrees"] = expected_live is None or expected_live == row["live"]
                    if not row["agrees"]:
                        disagreements += 1
                    rows.append(row)
            if rows:
                out[f"{arm}.r{repeat}"] = rows
    (root / "verified.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{'cell':<8} {'claims':>7} {'executable':>11} {'T1 collapse':>12} {'separates':>10} "
          f"{'relocated':>10} {'disagrees':>10}", flush=True)
    for name, rows in sorted(out.items()):
        runnable = [r for r in rows if r["verdict"] in ("collapse", "separates")]
        t1 = [r for r in runnable if r["verdict"] == "collapse" and r["expect"] == "moves"]
        print(f"{name:<8} {len(rows):>7} {len(runnable):>11} {len(t1):>12} "
              f"{len([r for r in runnable if r['verdict'] == 'separates']):>10} "
              f"{len([r for r in rows if r['relocated_to']]):>10} "
              f"{len([r for r in rows if not r['agrees']]):>10}", flush=True)
    if disagreements:
        print(f"\nThe live executor and this pass disagree on {disagreements} row(s). "
              "That disagreement is a finding about the executor, not a number to fold in.", flush=True)
    return 0


# ---------------------------------------------------------------------------------------------
# The driver. One (arm, repeat) per process; the alarms stop it the moment it stops measuring.
# ---------------------------------------------------------------------------------------------


#: Consecutive segments that executed nothing before the arm is stopped. One is the model naming a
#: function that is not there, which is a result; a run of them is a loop reading only refusals,
#: which is not a measurement of anything. The alarm cannot tell those apart from inside one
#: segment, so the caller counts.
STARVED_RUN = 3

#: Transport failures tolerated per segment. A closed connection is not a measurement, and stopping
#: an arm on one throws away the segments after it; a dead root is moved aside and the segment is
#: run again, so the record never holds a half-written run.
TRANSPORT_ATTEMPTS = 3

#: Seconds to wait before each retry. Without a pause the three attempts are spent in seconds, which
#: rides out nothing: four cells stopped together on ``Connection refused`` from the local proxy
#: while it was restarting, and every one of them had burnt its three attempts before it was back.
TRANSPORT_BACKOFF: tuple[int, ...] = (0, 20, 90)


#: The alarm names that say this segment executed nothing at all.
STARVED_NAMES = frozenset({"LOOP_STARVED", "NOTHING_EXECUTED"})


def starved_streak(previous: int, names: "set[str] | frozenset[str]") -> int:
    """Consecutive segments that executed nothing, counted by the caller and not by one record.

    One segment cannot tell a loop reading refusals from a model naming a function the harness does
    not have. A run of them can. So the alarm reports the row ratio and this counts the run.
    """

    return previous + 1 if STARVED_NAMES & set(names) else 0


def _finished(segment: Path) -> bool:
    """Whether this root holds a run that reached RUN_ENDED, rather than a half-written one."""

    log = segment / "log.jsonl"
    return log.is_file() and "RUN_ENDED" in log.read_text(encoding="utf-8")


#: Where a half-written root goes. OUTSIDE the block's own records tree: a directory of records is
#: read by enumeration, and a root that is neither a finished record nor an error naming one is a
#: thing a reader has to know to skip. Leaving them in place let the block's own reader count them.
DEAD_ROOTS = "creativity-2-aborted/dead"


def _set_aside(segment: Path) -> Path | None:
    """Move a half-written root out of the block entirely, so the segment runs again into a clean one."""

    if not segment.exists():
        return None
    place = segment.parents[3] / DEAD_ROOTS / segment.parents[1].name / segment.parent.name
    place.mkdir(parents=True, exist_ok=True)
    for n in range(1, 100):
        target = place / f"{segment.name}.dead{n}"
        if not target.exists():
            segment.rename(target)
            return target
    raise MiniError("MINI_BLOCK_ROOT_CROWDED", f"{segment} has too many dead roots beside it")


def _run_segment(arm: str, repeat: int, index: int, manifest_path: Path, segment: Path,
                 args: argparse.Namespace) -> bool:
    """Run one segment, retrying a transport failure into a clean root. True when it finished."""

    for attempt in range(TRANSPORT_ATTEMPTS):
        pause = TRANSPORT_BACKOFF[min(attempt, len(TRANSPORT_BACKOFF) - 1)]
        if pause:
            print(f"{arm}.r{repeat} s{index:02d}: waiting {pause}s before attempt {attempt + 1}", flush=True)
            time.sleep(pause)
        dead = _set_aside(segment)
        if dead is not None:
            print(f"{arm}.r{repeat} s{index:02d}: a half-written root was set aside as {dead.name}", flush=True)
        segment.mkdir(parents=True, exist_ok=True)
        command = [sys.executable, str(ROOT / "tools" / "run_mini.py"), "live",
                   "--manifest", str(manifest_path), "--model", args.model,
                   "--output-dir", str(segment), "--retries", str(args.retries)]
        if args.timeout_seconds:
            command += ["--timeout-seconds", str(args.timeout_seconds)]
        completed = subprocess.run(command, cwd=ROOT, env={**__import__("os").environ,
                                                           "PYTHONPATH": str(ROOT / "src")})
        if completed.returncode == 0 and _finished(segment):
            return True
        print(f"{arm}.r{repeat} s{index:02d}: attempt {attempt + 1} of {TRANSPORT_ATTEMPTS} did not "
              f"finish (exit {completed.returncode})", flush=True)
    return False


def _block(args: argparse.Namespace) -> int:
    """Run one arm's one repeat, segment by segment, stopping on any fatal alarm.

    Every mode this checks for cost this repository runs before anyone was looking. A block that
    finishes with its critic reading nothing, or its translator writing artifact ids where function
    paths belong, produces a null that means nothing about the subject; ``docs/mini/ERRATA.md``
    records two such blocks. So the run stops rather than finishing.

    What it does NOT stop on: one segment whose single claim named a function the harness does not
    have. That is the model being wrong, which is a result. Only a RUN of such segments is a loop
    reading refusals, and only the caller can see a run.
    """

    from creib.forge.mini.alarms import FATAL, alarms_for, preflight

    runs, manifests = Path(args.runs), Path(args.manifests)
    arm, repeat = args.arm, args.repeat
    starved = 0
    for index in range(ARMS[arm]["segments"]):
        segment = _segment_dir(runs, arm, repeat, index)
        if _finished(segment):
            print(f"{arm}.r{repeat} s{index:02d}: already run", flush=True)
            continue
        path = _build(arm, repeat, index, runs, manifests)
        found = preflight(path, ROOT)
        for alarm in found:
            print(f"{arm}.r{repeat} s{index:02d} preflight {alarm}", flush=True)
        if any(a.severity == FATAL for a in found):
            print(f"{arm}.r{repeat}: STOPPING before segment {index:02d}; the machinery is unfit to measure", flush=True)
            return 1
        if not _run_segment(arm, repeat, index, path, segment, args):
            print(f"{arm}.r{repeat}: STOPPING at segment {index:02d}; {TRANSPORT_ATTEMPTS} attempts "
                  "did not reach RUN_ENDED", flush=True)
            return 1
        previous = _segment_dir(manifests, arm, repeat, index - 1) / "proposed_organisation.txt"
        found = alarms_for(segment,
                           previous_brief=previous.read_text(encoding="utf-8") if previous.is_file() else None,
                           brief=(_segment_dir(manifests, arm, repeat, index) / "proposed_organisation.txt").read_text(encoding="utf-8"))
        for alarm in found:
            print(f"{arm}.r{repeat} s{index:02d} {alarm}", flush=True)
        if any(a.severity == FATAL for a in found):
            print(f"{arm}.r{repeat}: STOPPING after segment {index:02d}; the machinery is unfit to measure", flush=True)
            return 1
        starved = starved_streak(starved, {a.name for a in found})
        if starved >= STARVED_RUN:
            print(f"{arm}.r{repeat}: STOPPING after segment {index:02d}; {starved} segments in a row "
                  "executed nothing, which is a loop reading refusals rather than results", flush=True)
            return 1
        print(f"{arm}.r{repeat} s{index:02d}: done", flush=True)
    print(f"{arm}.r{repeat}: {ARMS[arm]['segments']} segments complete", flush=True)
    return 0


def _classes(args: argparse.Namespace) -> int:
    """Read every cell on the collapse-class measure beside the pre-registered find measure.

    A find is one pair the check answered the same on where its rule required a move. A collapse
    class is the check together with the shapes of the two texts (``creib.forge.mini.collapses``),
    so a class counts a distinct WAY of making the check collapse and a find counts a distinct pair
    of texts. The block was pre-registered on finds; this measure was written afterwards and is a
    description of the records, not a conjecture they were run to test.

    It matters because it reorders the arms: on finds per segment ``A`` leads, on classes per
    segment ``W`` does, and on either measure per call ``R`` leads because it is the cheapest.
    """

    from creib.forge.mini.collapses import class_of, is_find

    root = Path(args.root)
    rows: list[dict[str, Any]] = []
    pooled: dict[str, set[Any]] = {}
    order: list[tuple[str, int, int, Any]] = []
    for arm in sorted(ARMS):
        for repeat in range(REPEATS):
            segments = _segments(root, arm, repeat)
            if not segments:
                continue
            calls = 0
            found: list[Any] = []
            for segment in segments:
                calls += _calls(segment)
                executions, _, _ = _record(segment)
                for entry in executions:
                    if not is_find(entry):
                        continue
                    klass = class_of(entry).as_row()
                    found.append(klass)
                    order.append((arm, repeat, int(segment.name[1:]), klass))
            pooled.setdefault(arm, set()).update(found)
            rows.append({"arm": arm, "repeat": repeat, "segments": len(segments), "calls": calls,
                         "finds": len(found), "classes": len(set(found))})
    if not rows:
        raise MiniError("MINI_COLLAPSE_CLASS_INVALID", f"no finished segment under {root}")
    print(f"{'cell':8}{'segments':>9}{'calls':>7}{'finds':>7}{'classes':>9}"
          f"{'finds/seg':>11}{'classes/seg':>13}{'classes/call':>14}", flush=True)
    for row in rows:
        cell = f"{row['arm']}.r{row['repeat']}"
        print(f"{cell:8}{row['segments']:9}{row['calls']:7}{row['finds']:7}{row['classes']:9}"
              f"{row['finds'] / row['segments']:11.3f}{row['classes'] / row['segments']:13.3f}"
              f"{row['classes'] / row['calls']:14.4f}", flush=True)
    print("", flush=True)
    print(f"{'arm':8}{'segments':>9}{'calls':>7}{'finds':>7}{'classes':>9}"
          f"{'finds/seg':>11}{'classes/seg':>13}{'classes/call':>14}", flush=True)
    for arm in sorted(pooled):
        mine = [r for r in rows if r["arm"] == arm]
        segments = sum(r["segments"] for r in mine)
        calls = sum(r["calls"] for r in mine)
        finds = sum(r["finds"] for r in mine)
        classes = len(pooled[arm])
        print(f"{arm:8}{segments:9}{calls:7}{finds:7}{classes:9}{finds / segments:11.3f}"
              f"{classes / segments:13.3f}{classes / calls:14.4f}", flush=True)
    every = set().union(*pooled.values())
    alone = sum(1 for klass in every if sum(klass in pooled[a] for a in pooled) == 1)
    counted: dict[Any, int] = {}
    for _, _, _, klass in order:
        counted[klass] = counted.get(klass, 0) + 1
    biggest = sorted(counted.values(), reverse=True)[:5]
    print("", flush=True)
    print(f"pooled across every arm: {sum(counted.values())} finds in {len(every)} classes; "
          f"the five largest hold {sum(biggest)} of them; {alone} class(es) were reached by one arm only",
          flush=True)
    # The cells ran at the same time, so there is no order between them and no "first cell to reach
    # a class". What is well defined is how early in a RUN a class becomes available: the smallest
    # segment index at which any cell reached it, and how many cells of twelve ever did.
    earliest: dict[Any, int] = {}
    cells_of: dict[Any, set[tuple[str, int]]] = {}
    for arm, repeat, index, klass in order:
        earliest[klass] = min(earliest.get(klass, index), index)
        cells_of.setdefault(klass, set()).add((arm, repeat))
    print("", flush=True)
    print("each class: its finds, the earliest segment index any cell reached it at, and how many "
          "of the twelve cells ever did", flush=True)
    for klass, count in sorted(counted.items(), key=lambda item: (-item[1], str(item[0]))):
        check = str(klass[0]).rsplit(".", 1)[-1]
        print(f"  {count:4} finds  from s{earliest[klass]:02d}  in {len(cells_of[klass]):2} cell(s)  "
              f"{check}  {klass[1]} -> {klass[2]}", flush=True)
    (root / "classes.json").write_text(
        json.dumps({"cells": rows, "classes_by_arm": {a: len(v) for a, v in sorted(pooled.items())},
                    "pooled_classes": len(every), "reached_by_one_arm_only": alone},
                   indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


def _rules(args: argparse.Namespace) -> int:
    """Adjudicate every find against the documented rule, read apart from the code.

    The pre-registered find measure asked two things of a pair and only ever checked one. The
    executor recorded that the check answers the same on both texts, and ``verify`` re-ran every
    claim and found no disagreement. Whether the RULE requires the two to differ was taken from the
    model's prose and never checked at all. ``creib.forge.mini.rule_readings`` implements the rule of
    two checks from their docstrings; a find is ``real`` under a reading when the rule's two answers
    differ, ``unsupported`` when they do not, and ``unread`` when no reading of that check exists.

    ``unsupported`` is not ``refuted``: the conjecture the pair was offered for may still hold of some
    other pair. It says this pair does not show it.
    """

    from creib.forge.mini.collapses import class_of, is_find
    from creib.forge.mini.conformance_kernels import REFUSAL_PHRASES
    from creib.forge.mini.rule_readings import READINGS_OF, REAL, UNREAD, UNSUPPORTED, verdict

    root = Path(args.root)
    finds: list[tuple[str, int, int, dict[str, Any], Any]] = []
    for arm in sorted(ARMS):
        for repeat in range(REPEATS):
            for segment in _segments(root, arm, repeat):
                executions, _, _ = _record(segment)
                for entry in executions:
                    if is_find(entry):
                        finds.append((arm, repeat, int(segment.name[1:]), entry,
                                      class_of(entry).as_row()))
    if not finds:
        raise MiniError("MINI_COLLAPSE_CLASS_INVALID", f"no find under {root}")
    verdicts: dict[tuple[str, str], str] = {}
    for _, _, _, entry, _ in finds:
        check = str(entry.get("kernel")).rsplit(".", 1)[-1]
        for reading in READINGS_OF.get(check, ("",)):
            key = (str(entry.get("input")) + "\x00" + str(entry.get("rewritten")), reading)
            verdicts[key] = verdict(check, str(entry.get("input")), str(entry.get("rewritten")),
                                    reading or "first-in-text", REFUSAL_PHRASES) if reading else UNREAD
    rows: list[dict[str, Any]] = []
    for check in sorted({str(e.get("kernel")).rsplit(".", 1)[-1] for _, _, _, e, _ in finds}):
        mine = [f for f in finds if str(f[3].get("kernel")).rsplit(".", 1)[-1] == check]
        readings = READINGS_OF.get(check, ())
        if not readings:
            rows.append({"check": check, "reading": "-", "finds": len(mine), "real": 0,
                         "unsupported": 0, "unread": len(mine)})
            continue
        for reading in readings:
            got = [verdicts[(str(f[3].get("input")) + "\x00" + str(f[3].get("rewritten")), reading)]
                   for f in mine]
            rows.append({"check": check, "reading": reading, "finds": len(mine),
                         "real": got.count(REAL), "unsupported": got.count(UNSUPPORTED),
                         "unread": got.count(UNREAD)})
    print(f"{'check':24}{'reading':26}{'finds':>7}{'real':>7}{'unsupported':>13}{'unread':>8}", flush=True)
    for row in rows:
        print(f"{row['check']:24}{row['reading']:26}{row['finds']:7}{row['real']:7}"
              f"{row['unsupported']:13}{row['unread']:8}", flush=True)

    # The same adjudication by class, because a class is what a find is evidence of: one way of
    # making the check collapse. A class every one of whose finds is unsupported is not a way.
    print("", flush=True)
    # A class is a WAY of making the check collapse, so one find that holds up under every reading
    # shows the way exists, and the class is real however many of its other finds do not hold up. A
    # class is unsupported when not one of its finds survives every reading.
    print("by collapse class: real when one of its finds holds up under every reading", flush=True)
    worst: dict[Any, str] = {}
    for _, _, _, entry, klass in finds:
        check = str(entry.get("kernel")).rsplit(".", 1)[-1]
        readings = READINGS_OF.get(check, ())
        got = [verdicts[(str(entry.get("input")) + "\x00" + str(entry.get("rewritten")), reading)]
               for reading in readings] or [UNREAD]
        here = UNSUPPORTED if UNSUPPORTED in got else (REAL if REAL in got else UNREAD)
        if worst.get(klass) != REAL:
            worst[klass] = here
    counted: dict[Any, int] = {}
    for _, _, _, _, klass in finds:
        counted[klass] = counted.get(klass, 0) + 1
    tally: dict[str, int] = {}
    found: dict[str, int] = {}
    for klass, label in worst.items():
        tally[label] = tally.get(label, 0) + 1
        found[label] = found.get(label, 0) + counted[klass]
    for label in (REAL, UNSUPPORTED, UNREAD):
        print(f"  {label:14} {tally.get(label, 0):3} class(es), {found.get(label, 0):4} find(s)", flush=True)
    (root / "rules.json").write_text(
        json.dumps({"by_check": rows, "classes_by_least_favourable_reading": tally,
                    "finds_by_least_favourable_reading": found}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    return 0


def _plan(args: argparse.Namespace) -> int:
    """Write every arm's first manifest, so the block can be validated before a call is paid for."""

    manifests = Path(args.out)
    for arm in ARMS:
        for repeat in range(REPEATS):
            path = _build(arm, repeat, 0, Path(args.out) / "_norun", manifests)
            print(f"{arm}.r{repeat} s00 -> {path}", flush=True)
    # Calls, not stages: the conjecture and the criticism each cost two, the reading one, and a
    # refused submission is a call as well. A block that budgets in stages under-counts by about
    # double (C13).
    calls = {a: s["segments"] * (5 if s["criticism"] else 3) * REPEATS for a, s in ARMS.items()}
    print(f"model calls per arm across {REPEATS} repeats, before any refusal: {calls}; "
          f"total {sum(calls.values())}", flush=True)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    planner = sub.add_parser("plan", help="write each arm's first manifest and say what the block costs")
    planner.add_argument("--out", required=True)
    planner.set_defaults(handler=_plan)
    enumerator = sub.add_parser("enumerate", help="the repaired non-LLM baseline")
    enumerator.add_argument("--out", required=True)
    enumerator.set_defaults(handler=_enumerate)
    runner = sub.add_parser("block", help="run one arm's one repeat, stopping on any fatal alarm")
    runner.add_argument("--arm", required=True, choices=sorted(ARMS))
    runner.add_argument("--repeat", type=int, required=True, choices=list(range(REPEATS)))
    runner.add_argument("--model", required=True)
    runner.add_argument("--manifests", required=True)
    runner.add_argument("--runs", required=True)
    runner.add_argument("--timeout-seconds", type=int, default=None)
    runner.add_argument("--retries", type=int, default=4,
                        help="transport retries per call; a closed connection is not a measurement")
    runner.set_defaults(handler=_block)
    reader = sub.add_parser("read", help="read every cell on the pre-registered measures")
    reader.add_argument("--root", required=True)
    reader.set_defaults(handler=_read)
    adjudicator = sub.add_parser("rules", help="adjudicate every find against the rule read apart from the code")
    adjudicator.add_argument("--root", required=True)
    adjudicator.set_defaults(handler=_rules)
    classifier = sub.add_parser("classes", help="read every cell on the collapse-class measure as well")
    classifier.add_argument("--root", required=True)
    classifier.set_defaults(handler=_classes)
    verifier = sub.add_parser("verify", help="re-execute every claim, and name where it disagrees with the executor")
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
