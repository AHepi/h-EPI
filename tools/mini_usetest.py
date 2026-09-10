#!/usr/bin/env python3
"""MINI-USE-TEST-1: run the comparison in which mini is allowed to lose.

    python tools/mini_usetest.py freeze  --out forge/mini/usetest
    python tools/mini_usetest.py draw    --instance s2-1 --mutation s2-fence-single-only --out <dir>
    python tools/mini_usetest.py run     --instance <dir> --arm B --model gemma4:31b
    python tools/mini_usetest.py adjudicate --instance <dir>

``freeze`` writes the clean subject, the frozen grid and the digests of both, and must be
committed before any mutation is drawn: the protocol's anti-cheating rule is that the test space
is fixed before the defect is chosen, and the git history is what makes that checkable.

``draw`` writes one hidden instance: the mutated subject, and beside it a sealed file holding
the truth about it. No arm is ever shown the sealed file, and no arm is shown the clean subject
or the mutation. ``run`` runs one arm on one instance under the shared ceiling and writes the
neutral packet. ``adjudicate`` opens the seal and asks the only question a machine can answer
about a packet: does its reproducer tell the clean subject from the mutated one?

The key is read inside the harness's own executor and nowhere else. Nothing here pushes.

Standard library plus the package; ``PYTHONPATH=src``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from creib.errors import RecordError  # noqa: E402
from creib.forge.mini import usetest  # noqa: E402
from creib.forge.mini.common import MiniError  # noqa: E402
from creib.strict_json import load_strict  # noqa: E402

INVALID = "MINI_USETEST_PLAN_INVALID"


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _freeze(args: argparse.Namespace) -> int:
    out = Path(args.out)
    subject = usetest.subject_source()
    grid = "\n\n".join(usetest.RECOVERY_GRID) + "\n"
    corpus = [
        {
            "mutation_id": item.mutation_id,
            "stratum": item.stratum,
            "kernel": item.kernel,
            "dimensions": list(item.dimensions),
            "consequence": item.consequence,
            "edit_digest": _digest(item.find + "\x00" + item.replace),
        }
        for item in usetest.CORPUS
    ]
    _write(out / "subject.clean.py", subject)
    _write(out / "grid.txt", grid)
    frozen = {
        "protocol": usetest.USE_TEST_ID,
        "subject_sha256": _digest(subject),
        "subject_closure": list(usetest.subject_closure()),
        "grid_sha256": _digest(grid),
        "grid_cells": list(usetest.RECOVERY_GRID),
        "non_enumerable": dict(usetest.NON_ENUMERABLE),
        "corpus": corpus,
        "packet_fields": list(usetest.PACKET_FIELDS),
        "dispositions": list(usetest.DISPOSITIONS),
        "ceiling": {"invocations": 8, "completion_tokens": 12000},
    }
    _write(out / "frozen.json", json.dumps(frozen, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"froze {len(usetest.RECOVERY_GRID)} cells and {len(corpus)} mutations under {out}", flush=True)
    print("commit this before drawing any mutation", flush=True)
    return 0


def _draw(args: argparse.Namespace) -> int:
    out = Path(args.out) / args.instance
    if (out / "subject.py").exists():
        raise MiniError(INVALID, f"{out} already holds an instance; a drawn instance is never redrawn")
    clean = usetest.subject_source()
    mutation = usetest.CLEAN if args.mutation in ("", "clean") else usetest.CORPUS_BY_ID.get(args.mutation)
    if mutation is None:
        raise MiniError(INVALID, f"no mutation {args.mutation!r}; the corpus holds {sorted(usetest.CORPUS_BY_ID)}")
    mutated = usetest.apply_mutation(clean, mutation)
    _write(out / "subject.py", mutated)
    _write(out / "instance.json", json.dumps(
        {
            "protocol": usetest.USE_TEST_ID,
            "instance": args.instance,
            "stratum": mutation.stratum,
            "subject_sha256": _digest(mutated),
            "clean_subject_sha256": _digest(clean),
        },
        indent=2, sort_keys=True) + "\n")
    truth: dict[str, Any] = {
        "instance": args.instance,
        "mutation_id": mutation.mutation_id,
        "stratum": mutation.stratum,
        "kernel": mutation.kernel,
        "dimensions": list(mutation.dimensions),
        "consequence": mutation.consequence,
        "reproducer": mutation.reproducer,
        "seeded": mutation.seeded,
    }
    if mutation.seeded:
        import tempfile

        with tempfile.TemporaryDirectory() as scratch:
            clean_path = Path(scratch) / "clean.py"
            clean_path.write_text(clean, encoding="utf-8")
            truth["clean_answer"] = usetest.run_kernel(usetest.load_subject(clean_path), mutation.kernel, mutation.reproducer)
        truth["mutated_answer"] = usetest.run_kernel(usetest.load_subject(out / "subject.py"), mutation.kernel, mutation.reproducer)
    _write(out / "sealed.json", json.dumps(truth, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"drew {args.instance}: stratum {mutation.stratum}, sealed in {out / 'sealed.json'}", flush=True)
    return 0


def _endpoint(args: argparse.Namespace) -> Any:
    """What every arm of this run sends to, built once and written into every record.

    A run whose record cannot name its timeout cannot explain a timeout death, and one that
    cannot name its reasoning setting cannot explain what that setting cost. Both are set here
    rather than left to a default, and both travel with the arm's result.
    """

    from creib.forge.conformance.spec import endpoint_from_dict

    return endpoint_from_dict(
        {
            "kind": "ollama-chat",
            "base_url": "https://ollama.com",
            "timeout_seconds": int(args.timeout_seconds),
            "options": {"temperature": 0, "seed": 7},
            "think": _think(args.think),
        }
    )


def _think(value: str) -> bool | str | None:
    """The reasoning setting as the harness reads it, from a word on the command line."""

    lowered = str(value).strip().lower()
    if lowered in ("off", "false", "no"):
        return False
    if lowered in ("on", "true", "yes"):
        return True
    if lowered in ("low", "medium", "high"):
        return lowered
    raise MiniError(INVALID, f"--think must be off, on, low, medium or high; got {value!r}")


def _executor(endpoint: Any, retries: int) -> Any:
    from creib.forge.conformance.executor import OllamaChatExecutor

    return OllamaChatExecutor(
        base_url=endpoint.base_url, timeout_seconds=endpoint.timeout_seconds, retries=retries, auth=endpoint.auth
    )


def _mini_arm(args: argparse.Namespace, instance: Path, ceiling: usetest.Ceiling, endpoint: Any) -> tuple[Any, list[dict[str, Any]]]:
    """Run one mini arm: the manifest under the shared ceiling, then one packet call.

    There is no slack arithmetic left. Mini reserves a call and its completion allowance
    before every send, so the run's own budget is the shared ceiling minus exactly the one
    call held back for the packet, and the cycle cap is the grid: enough cycles to walk every
    cell, with the reservation, not the cycle count, deciding when the arm stops.
    """

    from creib.forge.mini.executor import LiveResponder
    from creib.forge.mini.manifest import compile_manifest
    from creib.forge.mini.report import read_run
    from creib.forge.mini.runner import run_mini

    calls_for_mini = max(1, ceiling.invocations - 1)
    tokens_for_mini = max(
        ceiling.completion_tokens_per_call, ceiling.completion_tokens - ceiling.completion_tokens_per_call
    )
    manifest = usetest.arm_manifest(
        args.arm,
        instance.name,
        cycles=len(usetest.RECOVERY_GRID),
        max_calls=calls_for_mini,
        max_completion_tokens=tokens_for_mini,
        completion_tokens_per_call=ceiling.completion_tokens_per_call,
    )
    manifest_path = instance / f"arm-{args.arm.lower()}.manifest.json"
    _write(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    plan = compile_manifest(manifest_path)
    root = instance / f"arm-{args.arm.lower()}.run"
    responder = LiveResponder(
        args.model, endpoint=endpoint, retries=args.retries, completion_cap=ceiling.completion_tokens_per_call
    )
    outcome = run_mini(plan, root, responder, responder_id=f"model:{args.model}", endpoint=endpoint)
    reading = read_run(root)
    executions: list[dict[str, Any]] = []
    from creib.forge.mini.log import BlobStore, replay
    from creib.forge.mini.common import RUN_HEADER_DOMAIN, content_id

    state = replay(root / "log.jsonl", content_id(RUN_HEADER_DOMAIN, load_strict(root / "run-header.json")))
    blobs = BlobStore(root / "blobs")
    for key in state.artifact_order:
        record = state.artifacts[key]
        if str(record["kind_id"]) != usetest.EXECUTION_KIND:
            continue
        payload = json.loads(blobs.get(str(record["commitments_ref"])).decode("utf-8"))
        executions.extend(payload.get("executions", []))
    # What the run spent, as its own budget counted it: every send and every completion token,
    # refused replies included. ``tokens_by_kind`` counts only accepted replies, so version 3
    # charged the ceiling a figure smaller than the run had actually spent, and charged it to
    # the prompt counter besides.
    ceiling.charge_run(outcome.calls, outcome.completion_tokens)
    ceiling.machine_executions += sum(1 for item in executions if item.get("executed") in ("moved", "unchanged"))
    summary = json.dumps(executions, ensure_ascii=False, indent=2)[:8000]
    rules = usetest.rules_text((instance / "subject.py").read_text(encoding="utf-8"))
    packet_reply = usetest._ask(
        _executor(endpoint, args.retries),
        args.model,
        "You are reporting the result of a test campaign someone else ran. " + usetest._PACKET_INSTRUCTION,
        "## The documented rules of the checks\n\n" + rules + "\n\n## What was run, and what the checks answered\n\n" + summary,
        ceiling,
        usetest.PACKET_SCHEMA,
        think=endpoint.think,
    )
    transcript = [
        {"phase": "mini", "stop_reason": outcome.stop_reason, "calls": outcome.calls, "completion_tokens": outcome.completion_tokens, "executions": executions},
        {"phase": "report", "reply": packet_reply},
    ]
    return usetest.packet_from(packet_reply, instance.name, args.arm, args.model), transcript


def _run(args: argparse.Namespace) -> int:
    instance = Path(args.instance)
    subject = instance / "subject.py"
    if not subject.is_file():
        raise MiniError(INVALID, f"{instance} holds no subject; draw the instance first")
    os.environ[usetest.SUBJECT_ENV] = str(subject)
    endpoint = _endpoint(args)
    ceiling = usetest.Ceiling(
        invocations=args.invocations,
        completion_tokens=args.completion_tokens,
        completion_tokens_per_call=args.completion_tokens_per_call,
    )
    started = time.monotonic()
    stopped_on: str | None = None
    try:
        if args.arm in usetest.MINI_ARMS:
            packet, transcript = _mini_arm(args, instance, ceiling, endpoint)
        elif args.arm == usetest.ARM_A:
            packet, transcript = usetest.run_arm_a(_executor(endpoint, args.retries), args.model, subject, ceiling, think=endpoint.think)
        else:
            packet, transcript = usetest.run_arm_b(_executor(endpoint, args.retries), args.model, subject, ceiling, think=endpoint.think)
    except MiniError as error:
        # An arm that cannot reserve its next send, or that died on the transport, still leaves
        # a result: a packet-less record naming what stopped it. An arm that writes nothing at
        # all would be read as an arm that found nothing, which is a different thing.
        if error.code not in ("MINI_USETEST_CEILING_SPENT", "MINI_USETEST_CALL_FAILED", "MINI_LIVE_CALL_FAILED"):
            raise
        packet, transcript, stopped_on = None, [{"phase": "stopped", "code": error.code, "detail": str(error)}], error.code
    elapsed = int((time.monotonic() - started) * 1000)
    result = {
        "protocol": usetest.USE_TEST_ID,
        "instance": instance.name,
        "arm": args.arm,
        "model": args.model,
        "packet": packet.neutral() if packet is not None else None,
        "leaks": list(packet.leaks()) if packet is not None else [],
        "cost": {**ceiling.as_dict(), "wall_ms": elapsed},
        "method_version": usetest.METHOD_VERSION,
        # What the run was given, so a death can be explained from the record alone rather
        # than from whatever the operator remembers typing.
        "endpoint": endpoint.to_dict(),
        "stopped_on": stopped_on,
        # Parity is the comparison's primary control, so a breach is reported rather than left
        # to be noticed in the numbers.
        "ceiling_breached": ceiling.used_invocations > ceiling.invocations or ceiling.used_completion_tokens > ceiling.completion_tokens,
    }
    _write(instance / f"arm-{args.arm.lower()}.packet.json", json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    _write(instance / f"arm-{args.arm.lower()}.transcript.json", json.dumps(transcript, indent=2, ensure_ascii=False)[:400_000] + "\n")
    print(
        f"{instance.name} arm {args.arm} ({args.model}): {'a packet' if packet else 'no packet'}"
        + (f", stopped on {stopped_on}" if stopped_on else "")
        + f", {ceiling.as_dict()}",
        flush=True,
    )
    return 0


def _adjudicate(args: argparse.Namespace) -> int:
    """Open the seal and ask the one question a machine can answer: does the reproducer tell them apart?"""

    import tempfile

    instance = Path(args.instance)
    sealed = load_strict(instance / "sealed.json")
    clean_source = usetest.subject_source()
    rows: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory() as scratch:
        clean_path = Path(scratch) / "clean.py"
        clean_path.write_text(clean_source, encoding="utf-8")
        clean = usetest.load_subject(clean_path)
        mutated = usetest.load_subject(instance / "subject.py")
        for path in sorted(instance.glob("arm-*.packet.json")):
            result = load_strict(path)
            packet = result.get("packet")
            row: dict[str, Any] = {
                "arm": result.get("arm"),
                "model": result.get("model"),
                "packet": bool(packet),
                "cost": result.get("cost"),
                "leaks": result.get("leaks"),
            }
            if packet:
                reproducer = str(packet.get("reproducer", ""))
                separates: list[str] = []
                for kernel_id in usetest.KERNEL_IDS:
                    if usetest.run_kernel(clean, kernel_id, reproducer) != usetest.run_kernel(mutated, kernel_id, reproducer):
                        separates.append(kernel_id)
                row["reproducer_separates"] = separates
                row["claim"] = str(packet.get("claim", ""))[:200]
            rows.append(row)
    report = {
        "instance": instance.name,
        "stratum": sealed.get("stratum"),
        "mutation_id": sealed.get("mutation_id"),
        "seeded": sealed.get("seeded"),
        "seeded_kernel": sealed.get("kernel"),
        "arms": rows,
    }
    _write(instance / "adjudication.json", json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, ensure_ascii=False)[:4000], flush=True)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    freeze = sub.add_parser("freeze", help="write the clean subject, the frozen grid and their digests")
    freeze.add_argument("--out", default=str(ROOT / "forge" / "mini" / "usetest"))
    freeze.set_defaults(handler=_freeze)

    draw = sub.add_parser("draw", help="write one hidden instance and seal the truth about it")
    draw.add_argument("--instance", required=True)
    draw.add_argument("--mutation", required=True)
    draw.add_argument("--out", required=True)
    draw.set_defaults(handler=_draw)

    run = sub.add_parser("run", help="run one arm on one instance under the shared ceiling")
    run.add_argument("--instance", required=True)
    run.add_argument("--arm", required=True, choices=list(usetest.ARMS))
    run.add_argument("--model", required=True)
    run.add_argument("--invocations", type=int, default=8)
    run.add_argument("--completion-tokens", type=int, default=12000)
    run.add_argument(
        "--completion-tokens-per-call",
        type=int,
        default=2000,
        help="what each send reserves, and the cap the request carries; a reply cannot be larger than what was reserved for it",
    )
    run.add_argument("--timeout-seconds", type=int, default=600)
    run.add_argument(
        "--think",
        default="off",
        help="the reasoning setting sent with every call: off, on, low, medium or high; recorded with the arm's result",
    )
    run.add_argument("--retries", type=int, default=1)
    run.set_defaults(handler=_run)

    judge = sub.add_parser("adjudicate", help="open the seal and test every packet's reproducer")
    judge.add_argument("--instance", required=True)
    judge.set_defaults(handler=_adjudicate)

    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except (MiniError, RecordError) as error:
        sys.stderr.write(f"{error}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
