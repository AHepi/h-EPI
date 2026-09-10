"""The loop: walk the declared stages, ask each seat, write the record.

Nothing here knows a conjecturer from a critic. It walks stages, renders each
stage's declared ports, asks the responder, reads the reply into a submission,
checks the compiled format, checks the citations, routes the output through the
permission layer, and writes every outcome — accepted, failed, dropped, refused
— to the append-only record.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Mapping

from creib.canonical import canonical_bytes

from .attention import ATTENTION_OFF, PendingStage, choose_next
from .common import ARTIFACT_DOMAIN, MiniError, content_id, digest_bytes
from .evidence import Block, check_citations, cut_source, render_legend
from .executor import Request, Responder
from .formats import FORMAT_FIELDS
from .kinds import PHASE_BODY, PHASE_BOTH, PHASE_COMMITMENTS, ArtifactKind, Submission, read_submission
from .log import (
    ARTIFACT_SUBMITTED,
    ATTENTION_CHOSE,
    BLOBS_DIR,
    EVIDENCE_BATCHED,
    FORMAT_FAILURE,
    PORT_EMPTY,
    LOG_NAME,
    REFUSED,
    ROUTED,
    RUN_ENDED,
    RUN_STARTED,
    STAGE_ENTERED,
    SUBMISSION_DROPPED,
    BlobStore,
    EventLog,
    MiniState,
    apply_event,
    build_event,
)
from .machines import MachineContext, MachineResponder, resolve_machine_seat
from .manifest import COMMITMENT_CALL_TWO, SEAT_MACHINE, VERDICT_KIND_ID, RunPlan, Stage
from .ports import PortType, port_draws_kinds, port_draws_tiers
from .routing import Destination
from .signals import compute_signals
from .stops import STOP_NEVER, should_stop

MAX_STEPS = 512


@dataclass(frozen=True)
class AttemptOutcome:
    """One phase's accepted reply, and what it actually took to get it.

    ``request_ref`` is the request that produced THIS reply, not the first one
    tried: a retry is shown the format error beside the brief, so recording the
    original would pair the accepted reply with bytes nobody sent (audit F6).
    ``usage`` keeps every attempt's counts, refused ones included, and the
    totals are their sum.
    """

    submission: Submission
    prompt_tokens: int
    completion_tokens: int
    reply_ref: str
    request_ref: str
    invocations: int
    usage: tuple[Mapping[str, Any], ...]


@dataclass(frozen=True)
class RunOutcome:
    """What the record says when the loop stops."""

    run_id: str
    root: Path
    genesis: str
    state_digest: str
    stop_reason: str
    stages_entered: tuple[str, ...]
    cycles_completed: int = 0


class _Recorder:
    """Appends one event, applies it, and carries the chain forward."""

    def __init__(self, log: EventLog, state: MiniState, genesis: str) -> None:
        self._log = log
        self._state = state
        self._prev = genesis
        self._seq = 0
        self.cycle = 0

    @property
    def seq(self) -> int:
        return self._seq

    def emit(self, event_type: str, payload: Mapping[str, Any], **fields: Any) -> None:
        event = build_event(seq=self._seq, prev=self._prev, cycle=self.cycle, type=event_type, payload=payload, **fields)
        self._log.append(event)
        apply_event(self._state, event)
        self._prev = event.event_id
        self._seq += 1


def block_text(blobs: BlobStore, block: Mapping[str, Any]) -> str:
    """Recover one block's own words from the source it was cut from."""

    window = blobs.get(str(block["source_ref"]))[int(block["span_start"]) : int(block["span_end"])]
    if digest_bytes(window) != block["text_sha256"]:
        raise MiniError("MINI_BLOB_CORRUPT", f"block {str(block['block_id'])[:16]} does not match the bytes it names")
    return window.decode("utf-8")


def _as_block(blobs: BlobStore, entry: Mapping[str, Any]) -> Block:
    return Block(
        block_id=str(entry["block_id"]),
        source_id=str(entry["source_id"]),
        source_sha256=str(entry["source_sha256"]),
        tier=str(entry["tier"]),
        span_start=int(entry["span_start"]),
        span_end=int(entry["span_end"]),
        text_sha256=str(entry["text_sha256"]),
        text=block_text(blobs, entry),
    )


def _block_reaches_port(
    plan: RunPlan,
    state: MiniState,
    port_type: PortType,
    params: Mapping[str, Any],
    port_type_name: str,
    entry: Mapping[str, Any],
) -> bool:
    """Does one evidence block reach this port? The rule of section 14."""

    tier = str(entry["tier"])
    routes = plan.routing.for_evidence(tier)
    if not routes:
        return port_type.source == "evidence" and tier in port_draws_tiers(port_type, params)
    for route in routes:
        if route.target == "port_type":
            if port_type_name == route.port_type and port_type.source == "evidence" and tier in port_draws_tiers(port_type, params):
                return True
        elif route.target == "scratch":
            destination = str(route.destination)
            if (
                port_type.source == "scratch"
                and str(params.get("destination")) == destination
                and str(entry["block_id"]) in state.scratch_blocks.get(destination, [])
            ):
                return True
    return False


def _artifact_reaches_port(
    plan: RunPlan,
    state: MiniState,
    port_type: PortType,
    params: Mapping[str, Any],
    stage_id: str,
    port_id: str,
    record: Mapping[str, Any],
) -> bool:
    """Does one artifact reach this port? The same rule, for artifacts.

    With no route declared, the default draw applies. With a route declared, the
    default is REPLACED: the artifact reaches only where the run actually placed
    it, which is why a placement the permission layer refused reaches nothing.
    """

    kind_id = str(record["kind_id"])
    routes = plan.routing.for_artifact(kind_id)
    if not routes:
        return port_type.source == "artifacts" and kind_id in port_draws_kinds(port_type, params)
    artifact_id = str(record["artifact_id"])
    for route in routes:
        if route.target == "port":
            if artifact_id in state.pushed.get(f"{stage_id}::{port_id}", []):
                return True
        elif route.target == "scratch":
            destination = str(route.destination)
            if port_type.source == "scratch" and str(params.get("destination")) == destination:
                if artifact_id in state.scratch.get(destination, []):
                    return True
    return False


def _artifact_lines(blobs: BlobStore, records: tuple[Mapping[str, Any], ...], rule: str) -> list[str]:
    lines: list[str] = []
    for record in records:
        body = blobs.get(str(record["body_ref"])).decode("utf-8")
        lines.append(f"[{str(record['artifact_id'])[:16]}] ({record['kind_id']})")
        lines.append(body)
        if rule == "list_bodies_and_commitments":
            lines.append("commitments: " + blobs.get(str(record["commitments_ref"])).decode("utf-8"))
    return lines


def render_port(
    plan: RunPlan,
    state: MiniState,
    blobs: BlobStore,
    stage: Stage,
    port_id: str,
    cycle: int = 0,
) -> tuple[str, tuple[str, ...]]:
    """Render one port, and say which evidence blocks it exposed."""

    kind = plan.kinds[str(stage.kind_id)]
    port = kind.port(port_id)
    in_window = lambda item: port.window.admits(int(item.get("cycle", 0)), cycle)
    port_type = plan.port_types[port.port_type]
    header = f"## {port_type.header} ({port_id})"
    if port_type.source == "problem":
        return f"{header}\n{plan.problem}", ()
    if port_type.source == "artifacts":
        ordered = tuple(
            state.artifacts[key]
            for key in state.artifact_order
            if in_window(state.artifacts[key])
            and _artifact_reaches_port(plan, state, port_type, port.params, stage.stage_id, port_id, state.artifacts[key])
        )
        lines = _artifact_lines(blobs, ordered, port_type.render_rule) or ["(nothing yet)"]
        return "\n".join([header, *lines]), ()
    if port_type.source == "evidence":
        entries = [
            item
            for item in state.blocks
            if in_window(item) and _block_reaches_port(plan, state, port_type, port.params, port.port_type, item)
        ]
        blocks = [_as_block(blobs, item) for item in entries]
        return render_legend(blocks, header), tuple(block.block_id for block in blocks)
    records = tuple(
        state.artifacts[key]
        for key in state.artifact_order
        if in_window(state.artifacts[key])
        and _artifact_reaches_port(plan, state, port_type, port.params, stage.stage_id, port_id, state.artifacts[key])
    )
    lines = _artifact_lines(blobs, records, port_type.render_rule)
    entries = [
        item
        for item in state.blocks
        if in_window(item) and _block_reaches_port(plan, state, port_type, port.params, port.port_type, item)
    ]
    blocks = [_as_block(blobs, item) for item in entries]
    if blocks:
        lines.append(render_legend(blocks, "admitted blocks"))
    return "\n".join([header, *(lines or ["(nothing yet)"])]), tuple(block.block_id for block in blocks)


def empty_artifact_ports(plan: RunPlan, state: MiniState, stage: Stage, cycle: int) -> tuple[str, ...]:
    """Declared ARTIFACT ports of this stage that draw nothing.

    Only artifact ports. An evidence port with nothing admitted, or a scratch
    port with an empty shelf, is the ordinary state of a first cycle and says
    nothing; an artifact port drawing nothing is the condition where a critic
    criticises with nothing to criticise.
    """

    kind = plan.kinds[str(stage.kind_id)]
    empty: list[str] = []
    for port_id in stage.ports:
        port = kind.port(port_id)
        port_type = plan.port_types[port.port_type]
        if port_type.source != "artifacts":
            continue
        in_window = port.window.admits
        drew = any(
            in_window(int(state.artifacts[key].get("cycle", 0)), cycle)
            and _artifact_reaches_port(plan, state, port_type, port.params, stage.stage_id, port_id, state.artifacts[key])
            for key in state.artifact_order
        )
        if not drew:
            empty.append(port_id)
    return tuple(empty)


def render_brief(
    plan: RunPlan, state: MiniState, blobs: BlobStore, stage: Stage, cycle: int = 0
) -> tuple[str, frozenset[str]]:
    """Render everything a stage is shown, and the blocks it may cite."""

    kind = plan.kinds[str(stage.kind_id)]
    sections = [f"# {kind.title}"]
    if kind.instruction is not None:
        sections.append(kind.instruction)
    exposed: set[str] = set()
    for port_id in stage.ports:
        rendered, block_ids = render_port(plan, state, blobs, stage, port_id, cycle)
        sections.append(rendered)
        exposed.update(block_ids)
    compiled = plan.formats[kind.kind_id]
    example = sorted(exposed)[0][:16] if exposed else None
    worked = (
        "\n\nTo ground a claim, add a citation naming a block and quoting its own words, like this:\n"
        '  "citations": [{"block": "' + example + '", "quote": "<words copied from that block>"}]'
        if example
        else ""
    )
    sections.append(
        "## What to return\n"
        'A JSON object carrying "body" and "commitments". Both are strings and nothing else is required.'
        + worked
    )
    if not compiled.freeform:
        sections.append("## The shape this answer must take\n" + "\n\n".join(compiled.describe()))
    return "\n\n".join(sections), frozenset(exposed)


def render_commitments_brief(
    plan: RunPlan,
    kind: ArtifactKind,
    body: str,
    state: MiniState | None = None,
    blobs: BlobStore | None = None,
    stage: Stage | None = None,
    cycle: int = 0,
) -> str:
    """What the second call is shown: the body, whatever ports the kind sends
    it, and the shape asked for.

    BY DEFAULT that is the body alone — no problem, no evidence legend, no other
    artifact, no earlier commitments — so the commitments are written from the
    writing itself. That is a default and not a law: a kind may declare
    ``commitment_ports``, and the record says what the call actually saw (R37).
    """

    compiled = plan.formats[kind.kind_id]
    alone = not kind.commitment_ports
    sections = [
        "# Commitments",
        "Below is one piece of writing. Say what is being committed to if it is taken up.",
    ]
    if kind.instruction is not None:
        # The kind's own words are what the seat IS asked to do, not evidence or another
        # artifact; they go to both calls, and the blind default of the second call is untouched.
        sections.append(kind.instruction)
    if alone:
        sections.append("You are shown nothing else, and nothing else is relevant.")
    sections.extend(["## The writing", body])
    if kind.commitment_ports and state is not None and blobs is not None and stage is not None:
        for port_id in kind.commitment_ports:
            rendered, _ = render_port(plan, state, blobs, stage, port_id, cycle)
            sections.append(rendered)
    sections.append('## What to return\nA JSON object carrying "commitments", a string, and nothing else.')
    if not compiled.freeform_for("commitments"):
        sections.append("## The shape this answer must take\n" + "\n\n".join(compiled.describe_field("commitments")))
    return "\n\n".join(sections)


def _batch_evidence(plan: RunPlan, blobs: BlobStore, recorder: _Recorder) -> None:
    for source in plan.sources:
        reference = blobs.put(source.raw)
        blocks = cut_source(source.source_id, source.raw, source.tier)
        for route in plan.routing.for_evidence(source.tier) or (None,):
            recorder.emit(
                EVIDENCE_BATCHED,
                {
                    "source_id": source.source_id,
                    "source_ref": reference,
                    "tier": source.tier,
                    "blocks": [block.to_dict() for block in blocks],
                    "to": {} if route is None else route.to_dict(),
                },
            )


def _store_artifact(blobs: BlobStore, stage: Stage, submission: Submission, seq: int) -> tuple[str, str, str]:
    body_ref = blobs.put(submission.body.encode("utf-8"))
    commitments_ref = blobs.put(submission.commitments.encode("utf-8"))
    artifact_id = content_id(
        ARTIFACT_DOMAIN,
        {
            "stage_id": stage.stage_id,
            "kind_id": stage.kind_id,
            "seq": seq,
            "body_ref": body_ref,
            "commitments_ref": commitments_ref,
        },
    )
    return artifact_id, body_ref, commitments_ref


def _route_output(
    plan: RunPlan,
    state: MiniState,
    blobs: BlobStore,
    recorder: _Recorder,
    stage: Stage,
    artifact_id: str,
    body_ref: str,
) -> None:
    kind_id = str(stage.kind_id)
    for destination in plan.routing.for_artifact(kind_id):
        _route_one(plan, state, blobs, recorder, stage, artifact_id, body_ref, destination)


def _route_one(
    plan: RunPlan,
    state: MiniState,
    blobs: BlobStore,
    recorder: _Recorder,
    stage: Stage,
    artifact_id: str,
    body_ref: str,
    destination: Destination,
) -> None:
    kind_id = str(stage.kind_id)
    if not plan.policy.may_write(kind_id, destination):
        recorder.emit(
            REFUSED,
            {"code": "MINI_POLICY_WRITE_REFUSED", "detail": f"policy {plan.policy.policy_id!r} does not let {kind_id!r} write there", "to": destination.to_dict()},
            stage_id=stage.stage_id,
            kind_id=kind_id,
            artifact_id=artifact_id,
        )
        return
    recorder.emit(
        ROUTED,
        {"to": destination.to_dict()},
        stage_id=stage.stage_id,
        kind_id=kind_id,
        artifact_id=artifact_id,
    )
    if destination.target == "evidence_store":
        raw = blobs.get(body_ref)
        blocks = cut_source(artifact_id[:16], raw, str(destination.tier))
        recorder.emit(
            EVIDENCE_BATCHED,
            {
                "source_id": artifact_id[:16],
                "source_ref": body_ref,
                "tier": str(destination.tier),
                "blocks": [block.to_dict() for block in blocks],
                "to": {},
            },
            stage_id=stage.stage_id,
            kind_id=kind_id,
            artifact_id=artifact_id,
        )


def _call_record(phase: str, outcome: AttemptOutcome) -> dict[str, Any]:
    """One call, as the record carries it."""

    return {
        "phase": phase,
        "request_ref": outcome.request_ref,
        "reply_ref": outcome.reply_ref,
        "invocations": outcome.invocations,
        "usage": [dict(item) for item in outcome.usage],
    }


def _check_reads(plan: RunPlan, recorder: _Recorder, stage: Stage, two_calls: bool = False) -> bool:
    """Preflight every port the stage will actually read, both calls included.

    A commitments call reads ports of its own (R37), and a permission check that
    walked only the first call's ports let a forbidden port through the second
    (audit F2). Ports a run will not read — a machine seat's, or a single-call
    kind's — are not checked, because refusing a setting nobody uses would
    refuse a legal configuration.
    """

    kind = plan.kinds[str(stage.kind_id)]
    ports = tuple(stage.ports) + (tuple(kind.commitment_ports) if two_calls else ())
    for port_id in dict.fromkeys(ports):
        port = kind.port(port_id)
        if not plan.policy.may_read(kind.kind_id, port.port_type):
            recorder.emit(
                REFUSED,
                {
                    "code": "MINI_POLICY_READ_REFUSED",
                    "detail": f"policy {plan.policy.policy_id!r} does not let {kind.kind_id!r} read a port of type {port.port_type!r}",
                    "port_id": port_id,
                },
                stage_id=stage.stage_id,
                kind_id=kind.kind_id,
            )
            return False
    return True


def _attempt_submission(
    plan: RunPlan,
    recorder: _Recorder,
    responder: Responder,
    stage: Stage,
    kind: ArtifactKind,
    brief: str,
    blobs: BlobStore,
    cycle: int = 0,
    phase: str = PHASE_BOTH,
) -> AttemptOutcome | None:
    """Ask the seat, and keep every reply — the refused ones included.

    A refused reply is stored as a blob and named on its FORMAT_FAILURE event,
    so the record says what the model actually returned and not only why it was
    turned away (FAILURE_MODES H1). An accepted body is kept verbatim; a refused
    one is no different.
    """

    compiled = plan.formats[kind.kind_id]
    checked = FORMAT_FIELDS if phase == PHASE_BOTH else (phase,)
    policy = kind.failure_policy
    reasons: tuple[str, ...] = ()
    refused_refs: list[str] = []
    usage: list[dict[str, Any]] = []
    for attempt in range(policy.retries + 1):
        # The rendered format is already in the brief, on every attempt; a retry
        # adds the error BESIDE it rather than in place of it.
        shown = brief if attempt == 0 else brief + "\n\n## The last reply was refused, for these reasons\n" + "\n".join(reasons)
        reply = responder.reply(
            Request(
                stage_id=stage.stage_id,
                kind_id=kind.kind_id,
                attempt=attempt,
                brief=shown,
                cycle=cycle,
                phase=phase,
            )
        )
        reply_ref = blobs.put(reply.text.encode("utf-8"))
        usage.append({"attempt": attempt, "prompt_tokens": reply.prompt_tokens, "completion_tokens": reply.completion_tokens})
        try:
            submission = read_submission(reply.text, kind, phase)
        except MiniError as error:
            reasons = (str(error),)
            refused_refs.append(reply_ref)
            recorder.emit(
                FORMAT_FAILURE,
                {"attempt": attempt, "reasons": list(reasons), "code": error.code, "seat": stage.seat, "phase": phase},
                stage_id=stage.stage_id,
                kind_id=kind.kind_id,
                body_ref=reply_ref,
            )
            continue
        if any(not getattr(submission, name).strip() for name in checked):
            reasons = ("body and commitments must each carry something",)
            refused_refs.append(reply_ref)
            recorder.emit(
                FORMAT_FAILURE,
                {"attempt": attempt, "reasons": list(reasons), "code": "MINI_SUBMISSION_MISSING_FIELD", "seat": stage.seat, "phase": phase},
                stage_id=stage.stage_id,
                kind_id=kind.kind_id,
                body_ref=reply_ref,
            )
            continue
        reasons = compiled.failures(submission.as_fields(), checked)
        if not reasons:
            return AttemptOutcome(
                submission=submission,
                prompt_tokens=sum(int(item["prompt_tokens"]) for item in usage),
                completion_tokens=sum(int(item["completion_tokens"]) for item in usage),
                reply_ref=reply_ref,
                request_ref=blobs.put(shown.encode("utf-8")),
                invocations=attempt + 1,
                usage=tuple(usage),
            )
        refused_refs.append(reply_ref)
        recorder.emit(
            FORMAT_FAILURE,
            {"attempt": attempt, "reasons": list(reasons), "code": "MINI_FORMAT_FAILURE", "seat": stage.seat, "phase": phase},
            stage_id=stage.stage_id,
            kind_id=kind.kind_id,
            body_ref=reply_ref,
        )
    recorder.emit(
        SUBMISSION_DROPPED,
        {
            "attempts": policy.retries + 1,
            "reasons": list(reasons),
            "refused_refs": refused_refs,
            "phase": phase,
            "usage": usage,
        },
        stage_id=stage.stage_id,
        kind_id=kind.kind_id,
    )
    return None


def machine_responder(plan: RunPlan, state: MiniState, blobs: BlobStore, stage: Stage, cycle: int) -> MachineResponder:
    """The responder for a machine seat: its kind's registered function."""

    seat = resolve_machine_seat(str(stage.kind_id))
    return MachineResponder(seat, MachineContext(plan=plan, state=state, blobs=blobs, stage=stage, cycle=cycle))


def _host_stop(plan: RunPlan, state: MiniState, cycle: int, calls: int) -> str | None:
    """Is there another cycle? Decided here, never by anything a seat wrote."""

    if cycle > plan.cycles.max_cycles:
        return "cycle_cap"
    if plan.cycles.max_calls is not None and calls >= plan.cycles.max_calls:
        return "budget_cap"
    condition = plan.cycles.stop_condition
    if condition.condition_id == STOP_NEVER:
        return None
    signals = compute_signals(state, condition.reads_signals)
    reason = should_stop(condition, signals, cycle)
    return None if reason is None else f"stop_condition:{condition.condition_id}"


def _offered(
    plan: RunPlan, remaining: list[Stage], repeats_used: Mapping[str, int]
) -> tuple[PendingStage, ...]:
    """The stages attention may choose from: what is left, plus what may repeat."""

    # The verdict stage is withheld until it is the only one left, so "a cycle
    # ends with the verdict" survives a re-ordering policy (C12).
    todo = [item for item in remaining if not item.end]
    if not todo:
        # Only the end marker is left: the cycle is finished, and a repeat
        # allowance is not a reason to reopen it. Offering work here let
        # attention continue a completed cycle, and let it re-run the verdict
        # (audit F5).
        return ()
    others = [item for item in todo if item.kind_id != VERDICT_KIND_ID]
    offered = [PendingStage(item.stage_id, str(item.kind_id)) for item in (others or todo)]
    if others:
        # While ordinary work remains, a repeat is ordinary work too — but the
        # verdict is never offered as one.
        for stage_id, used in repeats_used.items():
            stage = plan.stage(stage_id)
            if stage.kind_id != VERDICT_KIND_ID and used < stage.max_repeats:
                offered.append(PendingStage(stage_id, str(stage.kind_id)))
    return tuple(offered)


def run_mini(
    plan: RunPlan,
    root: Path,
    responder: Responder,
    responder_id: str = "unrecorded",
    endpoint: Any | None = None,
) -> RunOutcome:
    """Run one plan into one root, and return what the record says.

    The stage list is the body of one cycle; the cycle repeats until the host
    stops it. ``responder_id`` names what answered — a digest of a script, or a
    model — so two roots can later be checked for having been asked the same way.
    ``endpoint`` is what a live run actually sent to, run-time overrides included,
    and is written to the run's first event; a scripted run passes none.
    """

    if not isinstance(root, Path):
        raise TypeError("root must be pathlib.Path")
    log_path = root / LOG_NAME
    if log_path.exists():
        raise MiniError("MINI_RUN_ROOT_OCCUPIED", f"{root} already holds a record; a record is never written over")
    root.mkdir(parents=True, exist_ok=True)
    (root / "run-header.json").write_bytes(canonical_bytes(dict(plan.header)) + b"\n")

    blobs = BlobStore(root / BLOBS_DIR)
    state = MiniState()
    recorder = _Recorder(EventLog(log_path, plan.genesis), state, plan.genesis)
    recorder.emit(
        RUN_STARTED,
        {
            "run_id": plan.run_id,
            "manifest_id": plan.manifest_id,
            "manifest_digest": plan.manifest_digest,
            "responder_id": responder_id,
            "policy_id": plan.policy.policy_id,
            "policy_overrides": [dict(item) for item in plan.policy_overrides],
            "attention_policy": plan.attention.policy_id,
            "cycles": plan.cycles.to_dict(),
            "declared_order": [stage.stage_id for stage in plan.stages],
            # A live run records the endpoint actually used, overrides included, as the
            # conformance run record does; the plan's own endpoint is in the header.
            **({} if endpoint is None else {"endpoint": endpoint.to_dict()}),
        },
    )
    _batch_evidence(plan, blobs, recorder)

    calls = 0
    cycle = 0
    stop_reason = "cycle_cap"
    while True:
        cycle += 1
        stop = _host_stop(plan, state, cycle, calls)
        if stop is not None:
            stop_reason = stop
            break
        recorder.cycle = cycle
        remaining = list(plan.stages)
        repeats_used: dict[str, int] = {}
        halted = False
        steps = 0
        while remaining and steps < MAX_STEPS:
            steps += 1
            stage = remaining[0]
            if plan.attention.policy_id != ATTENTION_OFF:
                offered = _offered(plan, remaining, repeats_used)
                if offered:
                    signals = compute_signals(state, plan.attention.reads_signals)
                    chosen = choose_next(plan.attention, signals, offered)
                    if chosen is not None:
                        stage = plan.stage(chosen)
                        recorder.emit(
                            ATTENTION_CHOSE,
                            {"policy": plan.attention.policy_id, "chosen": chosen, "declared_next": remaining[0].stage_id},
                        )
            if stage.stage_id in repeats_used and stage not in remaining:
                repeats_used[stage.stage_id] += 1
            else:
                remaining = [item for item in remaining if item.stage_id != stage.stage_id]
                repeats_used.setdefault(stage.stage_id, 0)
            if stage.end:
                break
            recorder.emit(STAGE_ENTERED, {"ports": list(stage.ports)}, stage_id=stage.stage_id, kind_id=stage.kind_id)
            kind = plan.kinds[str(stage.kind_id)]
            empty = empty_artifact_ports(plan, state, stage, cycle)
            for port_id in empty:
                recorder.emit(
                    PORT_EMPTY,
                    {"port_id": port_id, "kind_id": kind.kind_id},
                    stage_id=stage.stage_id,
                    kind_id=kind.kind_id,
                )
            if empty and kind.failure_policy.skip_on_empty_port:
                recorder.emit(
                    SUBMISSION_DROPPED,
                    {"attempts": 0, "reasons": [f"the declared ports {list(empty)} drew nothing"], "refused_refs": []},
                    stage_id=stage.stage_id,
                    kind_id=kind.kind_id,
                )
                continue
            machine = stage.seat == SEAT_MACHINE
            two_calls = (not machine) and kind.commitment_call == COMMITMENT_CALL_TWO
            if not _check_reads(plan, recorder, stage, two_calls):
                continue
            brief, exposed = render_brief(plan, state, blobs, stage, cycle)
            seat_responder = machine_responder(plan, state, blobs, stage, cycle) if machine else responder
            first_phase = PHASE_BODY if two_calls else PHASE_BOTH
            attempt = _attempt_submission(
                plan, recorder, seat_responder, stage, kind, brief, blobs, cycle, first_phase
            )
            # The host's budget counts what was actually invoked, so a retry
            # that succeeded is not counted as one call (audit F3).
            if not machine:
                calls += attempt.invocations if attempt is not None else kind.failure_policy.retries + 1
            calls_made: list[dict[str, Any]] = []
            if attempt is not None:
                calls_made.append(_call_record(first_phase, attempt))
            if attempt is not None and two_calls:
                second_brief = render_commitments_brief(
                    plan, kind, attempt.submission.body, state, blobs, stage, cycle
                )
                second = _attempt_submission(
                    plan, recorder, seat_responder, stage, kind, second_brief, blobs, cycle, PHASE_COMMITMENTS
                )
                calls += second.invocations if second is not None else kind.failure_policy.retries + 1
                if second is None:
                    attempt = None
                else:
                    calls_made.append(_call_record(PHASE_COMMITMENTS, second))
                    attempt = replace(
                        attempt,
                        submission=attempt.submission.joined(second.submission),
                        prompt_tokens=attempt.prompt_tokens + second.prompt_tokens,
                        completion_tokens=attempt.completion_tokens + second.completion_tokens,
                    )
            if attempt is None:
                drops = state.drops_by_kind.get(kind.kind_id, 0)
                attempts = drops + state.submissions_by_kind.get(kind.kind_id, 0)
                if kind.failure_policy.exceeded(drops, attempts) and kind.failure_policy.action == "stop":
                    stop_reason = "format_failures_exceeded"
                    halted = True
                    break
                continue
            submission, reply_ref = attempt.submission, attempt.reply_ref
            prompt_tokens, completion_tokens = attempt.prompt_tokens, attempt.completion_tokens
            artifact_id, body_ref, commitments_ref = _store_artifact(blobs, stage, submission, recorder.seq)
            blocks = {str(item["block_id"]): _as_block(blobs, item) for item in state.blocks}
            measures = check_citations(submission.citations, blocks, exposed)
            recorder.emit(
                ARTIFACT_SUBMITTED,
                {
                    "seat": stage.seat,
                    "reply_ref": reply_ref,
                    "commitment_call": "machine_single" if machine else kind.commitment_call,
                    "commitment_ports": [] if machine else list(kind.commitment_ports),
                    "calls": calls_made,
                    "recovered": list(submission.recovered),
                    "about": list(submission.about),
                    "answers": list(submission.answers),
                    "citations": [measure.to_dict() for measure in measures],
                    "extra": dict(submission.extra),
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                },
                stage_id=stage.stage_id,
                kind_id=kind.kind_id,
                artifact_id=artifact_id,
                body_ref=body_ref,
                commitments_ref=commitments_ref,
            )
            _route_output(plan, state, blobs, recorder, stage, artifact_id, body_ref)
        if halted:
            break

    recorder.emit(RUN_ENDED, {"stop_reason": stop_reason, "cycles_completed": max(cycle - 1, 0)})
    return RunOutcome(
        run_id=plan.run_id,
        root=root,
        genesis=plan.genesis,
        state_digest=state.digest(),
        stop_reason=stop_reason,
        stages_entered=tuple(state.stages_entered),
        cycles_completed=max(cycle - 1, 0),
    )
