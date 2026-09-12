#!/usr/bin/env python3
"""DECIDE-TEST-1: run the grid, put the decisions, and score them against what the grid yielded.

    python tools/mini_decide.py plan   --out forge/mini/manifests/decide-1
    python tools/mini_decide.py grid   --model <model> --manifests <dir> --runs <dir>
    python tools/mini_decide.py points --runs <dir>
    python tools/mini_decide.py ask    --model <model> --manifests <dir> --runs <dir>
    python tools/mini_decide.py read   --runs <dir>

`docs/mini/DECIDE_TEST_1.md` is the pre-registration and was committed before any record here existed.
The question is whether a small model can decide what to do next with nothing larger in the room, so
nothing larger scores it: a choice is scored against what the grid actually yielded, and the campaign
comparison is against a function of six numbers that `creib.forge.mini.campaign` computes.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

from creib.errors import RecordError  # noqa: E402
from creib.forge.mini.common import MiniError  # noqa: E402
from creib.forge.mini.decide import (  # noqa: E402
    ABLATED,
    BRIEFS,
    CONTENT_BRIEFS,
    CONTRAST,
    FORM_BRIEFS,
    PLAIN,
    RELABELLED,
    REPEAT,
    STAY,
    STOP,
    UNCHANGED,
    WORKING_SET,
    Grid,
    add_brief,
    add_option_ids,
    add_options,
    add_states,
    agreement,
    brief,
    campaign_brief,
    campaign_options,
    campaign_states,
    contrast_flips,
    fixed_hit_rate,
    length_dependent,
    move_option,
    options_of,
    random_hit_rate,
    name_choice,
    read_choice,
    right_options,
    rule_that_fires,
    states_from_grid,
)

#: Segments a check gets in the grid, and the cuts a decision point is taken at. Both are declared in
#: the pre-registration; a grid shorter than its longest cut would make that cut's points unbuildable.
GRID_SEGMENTS = 6
CUTS: tuple[int, ...] = (1, 2, 4, 6)

#: The one transport policy, as in block 2: a closed connection is not a measurement.
TRANSPORT_ATTEMPTS = 3
TRANSPORT_BACKOFF: tuple[int, ...] = (0, 20, 90)

#: The seed, declared here so it is part of the plan rather than a shipped default. One seed for the
#: whole block: the pre-registration says a second is run only if the repeat floor is above zero.
SEED = 11

DECISION_KIND = "mini.decision.v1"
VERDICT_KIND = "mini.verdict.v1"


def _endpoint() -> dict[str, Any]:
    return {"kind": "ollama-chat", "base_url": "https://ollama.com", "timeout_seconds": 900,
            "options": {"temperature": 0, "seed": SEED}, "think": None}


def _grid_manifest(check: str, index: int) -> dict[str, Any]:
    """One grid segment: block 2's rules-only loop, with the check named by the machine.

    The loop is imported from `creativity_block2` rather than restated, so a grid segment differs from
    a block-2 segment in one thing and one only -- the sentence naming the check. Everything the model
    is shown about the task, and every stage it passes through, is what block 2 showed and used.
    """

    from creativity_block2 import PROBLEM, manifest

    named = (PROBLEM + "\n\n## The check to work on\n\n"
             f"Work only on `open:{check}`. Every conjecture you write is about that function and no "
             "other. Do not propose a pair about any other function, even one that looks more "
             "promising: which function to work on is not yours to choose in this run.")
    built = manifest("R", 0, index, named)
    built["manifest_id"] = f"mini.decide1.grid.{check.rsplit('.', 1)[-1]}.s{index:02d}"
    built["endpoint"] = _endpoint()
    return built


def _decision_manifest(manifest_id: str, text: str) -> dict[str, Any]:
    """One decision: a single seat, one call, no schema, and the brief as the whole of its input.

    No schema on purpose. A schema with retries would re-ask a seat that answered in prose, which costs
    calls and hides the answer; a reply that names no option is a result and is recorded as one.
    """

    return {
        "schema_version": "creib.mini.manifest.v1",
        "manifest_id": manifest_id,
        "problem": text,
        "cycles": {"max_cycles": 1},
        "endpoint": _endpoint(),
        "port_types": [],
        "kinds": [{"kind_id": DECISION_KIND, "title": "Decision", "commitment_call": "single",
                   "instruction": "Answer the question you have been given, in the shape it asks for.",
                   # Two retries, because a seat that misses mini's envelope is re-asked with the
                   # envelope rendered, and the shape of a reply is not what this block measures. How
                   # often a retry was needed is read out of the records and reported.
                   "failure_policy": {"retries": 2, "tolerance": None, "action": "stop",
                                      "skip_on_empty_port": False},
                   "input_ports": [{"port_id": "problem", "port_type": "problem", "window": "all"}],
                   "output_port": {"port_id": "out", "produces_kind": DECISION_KIND}},
                  # A cycle must end on a verdict stage, and a verdict is an artifact a seat produced
                  # and never a standing (SPEC: mini mints no standing). This one reads nothing,
                  # because there is nothing to read: the decision is the whole of the run.
                  {"kind_id": VERDICT_KIND, "title": "Verdict", "input_ports": [],
                   "failure_policy": {"retries": 0, "tolerance": None, "action": "stop",
                                      "skip_on_empty_port": False},
                   "output_port": {"port_id": "out", "produces_kind": VERDICT_KIND}}],
        "stages": [{"stage_id": "decide", "kind_id": DECISION_KIND, "ports": ["problem"]},
                   {"stage_id": "verdict", "kind_id": VERDICT_KIND, "seat": "machine", "ports": []},
                   {"stage_id": "end", "end": True}],
        "sources": [{"source_id": "contract", "text": "one decision, one call\n"}],
    }


def _write(path: Path, body: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def _finished(root: Path) -> bool:
    log = root / "log.jsonl"
    return log.is_file() and any("RUN_ENDED" in line for line in log.read_text().splitlines())


def _staging_for(staging: Path, root: Path, runs: Path) -> Path:
    """Where a run is written while it is in flight, outside the tree the record will live in."""

    try:
        inner = root.relative_to(runs)
    except ValueError:
        inner = Path(root.name)
    return staging / inner


def _run(label: str, manifest_path: Path, root: Path, args: argparse.Namespace) -> bool:
    """Run one manifest, write it outside the tree, and move it in only once it is a record.

    A root a model is still writing into is not a record, and nothing in a record's identity depends on
    where it was written -- the run header carries the manifest and no path -- so the run happens in a
    staging directory and the finished root is moved into place. That makes "a root under the runs tree
    is a finished record" true by construction rather than true because whoever commits was careful.

    An attempt that does not finish is moved to ``<runs>-aborted/`` rather than deleted, so what was set
    aside is still readable, as block 2 did with its own dead roots.
    """

    runs = Path(args.runs)
    staging = Path(args.staging)
    aborted = runs.with_name(runs.name + "-aborted")
    for attempt in range(TRANSPORT_ATTEMPTS):
        pause = TRANSPORT_BACKOFF[min(attempt, len(TRANSPORT_BACKOFF) - 1)]
        if pause:
            print(f"{label}: waiting {pause}s before attempt {attempt + 1}", flush=True)
            time.sleep(pause)
        working = _staging_for(staging, root, runs)
        if working.exists():
            shutil.rmtree(working)
        working.mkdir(parents=True, exist_ok=True)
        command = [sys.executable, str(ROOT / "tools" / "run_mini.py"), "live",
                   "--manifest", str(manifest_path), "--model", args.model,
                   "--output-dir", str(working), "--retries", str(args.retries)]
        if args.timeout_seconds:
            command += ["--timeout-seconds", str(args.timeout_seconds)]
        completed = subprocess.run(command, cwd=ROOT, env={**os.environ, "PYTHONPATH": str(ROOT / "src")})
        if completed.returncode == 0 and _finished(working):
            root.parent.mkdir(parents=True, exist_ok=True)
            if root.exists():
                shutil.rmtree(root)
            shutil.move(str(working), str(root))
            return True
        kept = _staging_for(aborted, root, runs).with_name(root.name + f".attempt{attempt}")
        kept.parent.mkdir(parents=True, exist_ok=True)
        if kept.exists():
            shutil.rmtree(kept)
        shutil.move(str(working), str(kept))
        print(f"{label}: attempt {attempt + 1} of {TRANSPORT_ATTEMPTS} did not finish "
              f"(exit {completed.returncode}); it was set aside as {kept}", flush=True)
    return False


# ------------------------------------------------------------------------------------------------
# Reading the grid
# ------------------------------------------------------------------------------------------------


def _grid_root(runs: Path, check: str, index: int) -> Path:
    return runs / "grid" / check.rsplit(".", 1)[-1] / f"s{index:02d}"


def _real_classes(segment: Path, check: str) -> tuple[list[Any], int]:
    """The collapse classes one segment produced that hold up under every reading, and its find count."""

    from creativity_arms import _record
    from creib.forge.mini.collapses import class_of, is_find
    from creib.forge.mini.conformance_kernels import REFUSAL_PHRASES
    from creib.forge.mini.rule_readings import READINGS_OF, REAL, UNSUPPORTED, verdict

    rows, _, _ = _record(segment)
    classes: list[Any] = []
    finds = 0
    for row in rows:
        if not is_find(row):
            continue
        finds += 1
        named = str(row.get("kernel")).rsplit(".", 1)[-1]
        readings = READINGS_OF.get(named, ())
        if not readings:
            continue
        got = {verdict(named, str(row.get("input")), str(row.get("rewritten")), reading,
                       REFUSAL_PHRASES) for reading in readings}
        if UNSUPPORTED in got or REAL not in got:
            continue
        classes.append(class_of(row).as_row())
    return (classes, finds)


def _read_grid(runs: Path) -> tuple[Grid, dict[str, tuple[int, ...]], dict[str, Any]]:
    """The grid as new real classes per segment, the finds per segment beside it, and what it cost."""

    from creativity_block2 import _calls

    rows: dict[str, tuple[int, ...]] = {}
    finds: dict[str, tuple[int, ...]] = {}
    spend: dict[str, Any] = {}
    for check in WORKING_SET:
        seen: set[Any] = set()
        per_segment: list[int] = []
        per_finds: list[int] = []
        calls = 0
        off_target = 0
        for index in range(GRID_SEGMENTS):
            segment = _grid_root(runs, check, index)
            if not _finished(segment):
                continue
            calls += _calls(segment)
            classes, found = _real_classes(segment, check)
            fresh = [klass for klass in classes if klass not in seen
                     and str(klass[0]).rsplit(".", 1)[-1] == check.rsplit(".", 1)[-1]]
            off_target += sum(1 for klass in classes
                              if str(klass[0]).rsplit(".", 1)[-1] != check.rsplit(".", 1)[-1])
            seen.update(fresh)
            per_segment.append(len(fresh))
            per_finds.append(found)
        if per_segment:
            rows[check] = tuple(per_segment)
            finds[check] = tuple(per_finds)
            spend[check] = {"segments": len(per_segment), "calls": calls,
                            "real_classes": len(seen), "finds": sum(per_finds),
                            "classes_on_another_check": off_target}
    if not rows:
        raise MiniError("MINI_COLLAPSE_CLASS_INVALID", f"no finished grid segment under {runs}")
    return (Grid(rows), finds, spend)


# ------------------------------------------------------------------------------------------------
# The commands
# ------------------------------------------------------------------------------------------------


def _plan(args: argparse.Namespace) -> int:
    out = Path(args.out)
    for check in WORKING_SET:
        for index in range(GRID_SEGMENTS):
            _write(out / "grid" / check.rsplit(".", 1)[-1] / f"s{index:02d}.json",
                   _grid_manifest(check, index))
    for state in campaign_states():
        for variant in BRIEFS:
            _write(out / "campaign" / state.state_id / f"{variant}.json",
                   _decision_manifest(f"mini.decide1.campaign.{state.state_id}.{variant}",
                                      campaign_brief(state, variant)))
    for adding in add_states():
        for variant in BRIEFS:
            _write(out / "add" / adding.state_id / f"{variant}.json",
                   _decision_manifest(f"mini.decide1.add.{adding.state_id}.{variant}",
                                      add_brief(adding, variant)))
    grid_calls = len(WORKING_SET) * GRID_SEGMENTS * 3
    campaign_calls = len(campaign_states()) * len(BRIEFS)
    add_calls = len(add_states()) * len(BRIEFS)
    point_calls = len(WORKING_SET) * len(CUTS) * len(BRIEFS)
    print(f"grid: {len(WORKING_SET)} checks x {GRID_SEGMENTS} segments x 3 calls = {grid_calls}", flush=True)
    print(f"points: {len(WORKING_SET)} x {len(CUTS)} cuts x {len(BRIEFS)} briefs = {point_calls} "
          "(written after the grid, because a point's figures are the grid's)", flush=True)
    print(f"add: {len(add_states())} states x {len(BRIEFS)} briefs = {add_calls} (not scored)", flush=True)
    print(f"campaign: {len(campaign_states())} states x {len(BRIEFS)} briefs = {campaign_calls}", flush=True)
    print(f"total {grid_calls + point_calls + add_calls + campaign_calls} calls at seed {SEED}",
          flush=True)
    return 0


def _grid(args: argparse.Namespace) -> int:
    manifests, runs = Path(args.manifests), Path(args.runs)
    wanted = WORKING_SET
    if args.check:
        wanted = tuple(check for check in WORKING_SET if check.rsplit(".", 1)[-1] == args.check)
        if not wanted:
            raise MiniError("MINI_COLLAPSE_CLASS_INVALID",
                            f"{args.check!r} is not in the working set: "
                            f"{[c.rsplit('.', 1)[-1] for c in WORKING_SET]}")
    for check in wanted:
        for index in range(GRID_SEGMENTS):
            root = _grid_root(runs, check, index)
            label = f"grid {check.rsplit('.', 1)[-1]} s{index:02d}"
            if _finished(root):
                print(f"{label}: already finished", flush=True)
                continue
            path = _write(manifests / "grid" / check.rsplit(".", 1)[-1] / f"s{index:02d}.json",
                          _grid_manifest(check, index))
            if not _run(label, path, root, args):
                print(f"{label}: giving up on this segment", flush=True)
    return 0


def _baselines(grid: Grid, states: "Sequence[Any]") -> dict[str, float]:
    """Every baseline over one set of points, so two sets are computed the same way and comparable."""

    return {"uniform_random": random_hit_rate(grid, states),
            "always_stay": fixed_hit_rate(grid, states, STAY),
            "always_stop": fixed_hit_rate(grid, states, STOP),
            **{f"always_{move_option(check)}": fixed_hit_rate(grid, states, move_option(check))
               for check in WORKING_SET}}


def _points(args: argparse.Namespace) -> int:
    """Write the decision points the grid puts the search in, and their briefs. No call is made."""

    runs = Path(args.runs)
    grid, finds, spend = _read_grid(runs)
    states = states_from_grid(grid, CUTS, finds)
    table = {
        "seed": SEED,
        "grid": {check: list(grid.row(check)) for check in grid.new_real_classes},
        "finds": {check: list(row) for check, row in finds.items()},
        "spend": spend,
        "points": [{"point_id": state.point_id, "current": state.current,
                    "options": list(options_of(state)),
                    "right": sorted(right_options(grid, state)),
                    "contrast_flips": contrast_flips(grid, state),
                    "length_dependent": length_dependent(grid, state),
                    "tallies": [{"check": tally.check, "segments": tally.segments,
                                 "finds": tally.finds, "real_classes": tally.real_classes}
                                for tally in state.tallies]}
                   for state in states],
        "baselines": _baselines(grid, states),
        "baselines_length_independent": _baselines(
            grid, [state for state in states if not length_dependent(grid, state)]),
    }
    _write(runs / "points.json", table)
    print(f"{'check':24}{'segments':>9}{'calls':>7}{'finds':>7}{'real classes':>14}", flush=True)
    for check, row in sorted(spend.items()):
        print(f"{check.rsplit('.', 1)[-1]:24}{row['segments']:9}{row['calls']:7}{row['finds']:7}"
              f"{row['real_classes']:14}", flush=True)
    print("", flush=True)
    print(f"{'point':26}{'right':40}{'contrast moves it':>18}{'key needs the grid length':>27}",
          flush=True)
    for point in table["points"]:
        print(f"{point['point_id']:26}{','.join(point['right']):40}"
              f"{str(point['contrast_flips']):>18}{str(point['length_dependent']):>27}", flush=True)
    print("", flush=True)
    for label, key in (("over all points", "baselines"),
                       ("over the length-independent points", "baselines_length_independent")):
        print(label, flush=True)
        for name, value in sorted(table[key].items()):
            print(f"  baseline {name:34} {value:.3f}", flush=True)
    return 0


def _add_states_from(grid: Grid, spend: dict[str, Any]) -> tuple[Any, ...]:
    """The what-to-add states, carrying what the plain loop did across the whole grid.

    Pooled over the three checks, because that is what the plain loop actually did in this block. A
    per-check figure would be the loop at its best or at its worst and neither is the loop.
    """

    segments = sum(row["segments"] for row in spend.values())
    found = sum(row["finds"] for row in spend.values())
    classes = sum(row["real_classes"] for row in spend.values())
    return add_states(segments=segments, finds=found, real_classes=classes)


def _ask(args: argparse.Namespace) -> int:
    manifests, runs = Path(args.manifests), Path(args.runs)
    grid, finds, spend = _read_grid(runs)
    for state in states_from_grid(grid, CUTS, finds):
        for variant in BRIEFS:
            root = runs / "points" / state.point_id / variant
            label = f"point {state.point_id} {variant}"
            if _finished(root):
                print(f"{label}: already finished", flush=True)
                continue
            path = _write(manifests / "points" / state.point_id / f"{variant}.json",
                          _decision_manifest(
                              f"mini.decide1.point.{state.point_id.replace('.', '-')}.{variant}",
                              brief(state, variant)))
            if not _run(label, path, root, args):
                print(f"{label}: giving up on this brief", flush=True)
    for adding in _add_states_from(grid, spend):
        for variant in BRIEFS:
            root = runs / "add" / adding.state_id / variant
            label = f"add {adding.state_id} {variant}"
            if _finished(root):
                print(f"{label}: already finished", flush=True)
                continue
            path = _write(manifests / "add" / adding.state_id / f"{variant}.json",
                          _decision_manifest(
                              f"mini.decide1.add.{adding.state_id}.{variant}",
                              add_brief(adding, variant)))
            if not _run(label, path, root, args):
                print(f"{label}: giving up on this brief", flush=True)
    for campaign in campaign_states():
        for variant in BRIEFS:
            root = runs / "campaign" / campaign.state_id / variant
            label = f"campaign {campaign.state_id} {variant}"
            if _finished(root):
                print(f"{label}: already finished", flush=True)
                continue
            path = _write(manifests / "campaign" / campaign.state_id / f"{variant}.json",
                          _decision_manifest(
                              f"mini.decide1.campaign.{campaign.state_id}.{variant}",
                              campaign_brief(campaign, variant)))
            if not _run(label, path, root, args):
                print(f"{label}: giving up on this brief", flush=True)
    return 0


def _reply(root: Path) -> tuple[str, str]:
    """The body and the commitments of the one decision a root holds; two empty strings when none."""

    from creib.forge.mini.common import RUN_HEADER_DOMAIN, content_id
    from creib.forge.mini.log import BlobStore, replay
    from creib.strict_json import load_strict

    if not _finished(root):
        return ("", "")
    state = replay(root / "log.jsonl", content_id(RUN_HEADER_DOMAIN, load_strict(root / "run-header.json")))
    blobs = BlobStore(root / "blobs")
    for key in state.artifact_order:
        record = state.artifacts[key]
        if str(record["kind_id"]) == DECISION_KIND:
            return (blobs.get(str(record["body_ref"])).decode("utf-8"),
                    blobs.get(str(record["commitments_ref"])).decode("utf-8"))
    return ("", "")


def _read(args: argparse.Namespace) -> int:
    runs = Path(args.runs)
    grid, finds, spend = _read_grid(runs)
    states = states_from_grid(grid, CUTS, finds)
    adding_states = _add_states_from(grid, spend)

    chosen: dict[str, dict[str, str]] = {variant: {} for variant in BRIEFS}
    reasons: dict[str, str] = {}
    for state in states:
        for variant in BRIEFS:
            body, commitments = _reply(runs / "points" / state.point_id / variant)
            if not body and not commitments:
                continue
            chosen[variant][state.point_id] = read_choice(body, state, variant)
            if variant == PLAIN:
                reasons[state.point_id] = commitments

    keyed = {state.point_id: right_options(grid, state) for state in states}
    answered = [point for point, choice in chosen[PLAIN].items() if choice]
    hits = sum(1 for point in answered if chosen[PLAIN][point] in keyed[point])
    print(f"{'point':26}{'chose':40}{'right':40}{'hit':>5}", flush=True)
    for state in states:
        choice = chosen[PLAIN].get(state.point_id, "(not run)")
        mark = "yes" if choice in keyed[state.point_id] else "no"
        print(f"{state.point_id:26}{choice or '(no option named)':40}"
              f"{','.join(sorted(keyed[state.point_id])):40}{mark:>5}", flush=True)
    print("", flush=True)
    counted: dict[str, int] = {}
    for choice in chosen[PLAIN].values():
        counted[choice or "(none)"] = counted.get(choice or "(none)", 0) + 1
    modal = max(counted, key=lambda name: (counted[name], name)) if counted else "(none)"
    modal_hits = (sum(1 for state in states if modal in options_of(state)
                      and modal in keyed[state.point_id]) / len(states)) if modal != "(none)" else 0.0
    print(f"answered {len(answered)} of {len(states)} points; hit {hits}", flush=True)
    print(f"hit rate {hits / len(answered) if answered else 0:.3f} against "
          f"uniform random {random_hit_rate(grid, states):.3f}, always-stay "
          f"{fixed_hit_rate(grid, states, STAY):.3f}, always-stop "
          f"{fixed_hit_rate(grid, states, STOP):.3f}", flush=True)
    print(f"what it chose: {counted}; its modal choice {modal} would have hit {modal_hits:.3f}", flush=True)

    print("", flush=True)
    print("agreement with the plain brief, and the floor a byte-identical brief sets", flush=True)
    floor = agreement(chosen[PLAIN], chosen[REPEAT])
    print(f"  {REPEAT:12} {floor[0]:3} of {floor[1]:3}  (the floor)", flush=True)
    for variant in FORM_BRIEFS + CONTENT_BRIEFS:
        same, both = agreement(chosen[PLAIN], chosen[variant])
        wanted = "must not move" if variant in FORM_BRIEFS else "must move"
        print(f"  {variant:12} {same:3} of {both:3}  ({wanted})", flush=True)
    flipping = [state.point_id for state in states if contrast_flips(grid, state)]
    same, both = agreement({point: chosen[PLAIN][point] for point in chosen[PLAIN] if point in flipping},
                           {point: chosen[CONTRAST][point] for point in chosen[CONTRAST] if point in flipping})
    print(f"  {CONTRAST:12} {same:3} of {both:3}  (on the {len(flipping)} point(s) where the contrast "
          "changes what the figures indicate; DEC-4 is measured here)", flush=True)

    # What to add: asked, not scored. There is no key, for the reason the pre-registration gives --
    # block 2's four arms did not separate, so no addition has a measured better answer. What is read
    # is what it chose and whether the choice moved with the form and with the content.
    add_chosen: dict[str, dict[str, str]] = {variant: {} for variant in BRIEFS}
    for adding in adding_states:
        for variant in BRIEFS:
            body, commitments = _reply(runs / "add" / adding.state_id / variant)
            if not body and not commitments:
                continue
            add_chosen[variant][adding.state_id] = name_choice(body, add_option_ids(adding, variant))
    print("", flush=True)
    print(f"{'what to add (not scored)':30}{'chose':50}{'options':>9}", flush=True)
    for adding in adding_states:
        choice = add_chosen[PLAIN].get(adding.state_id, "(not run)")
        print(f"{adding.state_id:30}{choice or '(no option named)':50}{len(add_options(adding)):>9}",
              flush=True)
    for variant in (REPEAT,) + FORM_BRIEFS + CONTENT_BRIEFS:
        same, both = agreement(add_chosen[PLAIN], add_chosen[variant])
        note = ("the floor" if variant == REPEAT else "must not move" if variant in FORM_BRIEFS
                else "must move")
        print(f"  {variant:12} {same:3} of {both:3}  ({note})", flush=True)

    campaign_chosen: dict[str, dict[str, str]] = {variant: {} for variant in BRIEFS}
    for campaign in campaign_states():
        for variant in BRIEFS:
            body, commitments = _reply(runs / "campaign" / campaign.state_id / variant)
            if not body and not commitments:
                continue
            campaign_chosen[variant][campaign.state_id] = name_choice(
                body, {option: option for option in campaign_options()})
    print("", flush=True)
    print(f"{'campaign state':26}{'chose':24}{'the rule that fired':24}{'hit':>5}", flush=True)
    campaign_hits = 0
    campaign_answered = 0
    for campaign in campaign_states():
        fired = rule_that_fires(campaign)
        choice = campaign_chosen[PLAIN].get(campaign.state_id, "(not run)")
        if choice and choice != "(not run)":
            campaign_answered += 1
            if choice == fired:
                campaign_hits += 1
        print(f"{campaign.state_id:26}{choice or '(no option named)':24}{fired:24}"
              f"{'yes' if choice == fired else 'no':>5}", flush=True)
    print("", flush=True)
    print(f"campaign: hit {campaign_hits} of {campaign_answered} answered, against uniform random "
          f"{1 / len(campaign_options()):.3f}", flush=True)
    for variant in (REPEAT,) + FORM_BRIEFS + CONTENT_BRIEFS:
        same, both = agreement(campaign_chosen[PLAIN], campaign_chosen[variant])
        note = ("the floor" if variant == REPEAT
                else "unavailable: nothing to rename" if variant == RELABELLED
                else "must not move" if variant in FORM_BRIEFS else "must move")
        print(f"  {variant:12} {same:3} of {both:3}  ({note})", flush=True)

    _write(runs / "reading.json", {
        "seed": SEED, "spend": spend,
        "points": {variant: chosen[variant] for variant in BRIEFS},
        "reasons": reasons,
        "key": {point: sorted(options) for point, options in keyed.items()},
        "hits": hits, "answered": len(answered),
        "baselines": {"uniform_random": random_hit_rate(grid, states),
                      "always_stay": fixed_hit_rate(grid, states, STAY),
                      "always_stop": fixed_hit_rate(grid, states, STOP)},
        "modal_choice": modal, "modal_hit_rate": modal_hits,
        "add": {variant: add_chosen[variant] for variant in BRIEFS},
        "campaign": {variant: campaign_chosen[variant] for variant in BRIEFS},
        "campaign_key": {state.state_id: rule_that_fires(state) for state in campaign_states()},
        "campaign_hits": campaign_hits, "campaign_answered": campaign_answered,
    })
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    planner = sub.add_parser("plan", help="write the grid and campaign manifests and say what it costs")
    planner.add_argument("--out", required=True)
    planner.set_defaults(handler=_plan)
    for name, handler, live in (("grid", _grid, True), ("ask", _ask, True)):
        command = sub.add_parser(name, help=f"run the {name} live")
        command.add_argument("--model", required=True)
        command.add_argument("--manifests", required=True)
        command.add_argument("--runs", required=True)
        command.add_argument("--timeout-seconds", type=int, default=None)
        command.add_argument("--retries", type=int, default=4)
        # One check at a time, so the three grids can run beside each other. The grids are
        # independent -- a segment is a fresh run with no carry -- so running them together changes
        # nothing about what each measures.
        command.add_argument("--check", default=None,
                             help="grid only: the bare name of one check of the working set")
        command.add_argument("--staging", required=True,
                             help="where a run is written while in flight, outside the runs tree; a "
                                  "finished root is moved in, an unfinished one to <runs>-aborted")
        command.set_defaults(handler=handler)
    pointer = sub.add_parser("points", help="read the grid and write the decision points it puts")
    pointer.add_argument("--runs", required=True)
    pointer.set_defaults(handler=_points)
    reader = sub.add_parser("read", help="score every decision against the grid")
    reader.add_argument("--runs", required=True)
    reader.set_defaults(handler=_read)
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except (MiniError, RecordError) as error:
        sys.stderr.write(f"{error}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
