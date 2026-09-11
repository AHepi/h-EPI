"""Compile: a manifest becomes a run plan, before anything is called (R5, R8, R14).

Everything that can be refused is refused here. A port whose type no registry
entry defines, a stage naming a kind nobody declared, a route to a stage that
does not exist, a format specification that cannot be compiled, a policy that
claims a power this prototype does not implement: each stops the compile with a
typed reason, and no model is reached.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from creib.errors import RecordError
from creib.strict_json import load_strict

from .attention import ATTENTION_OFF, AttentionPolicy, resolve_attention_policy
from .common import (
    KIND_SCHEMA_NAME,
    MANIFEST_SCHEMA_NAME,
    RUN_HEADER_DOMAIN,
    MiniError,
    array_value,
    content_id,
    digest_bytes,
    object_value,
    text,
    validate_instance,
)
from .evidence import BUILTIN_TIERS, TIER_EVIDENCE
from .formats import CompiledFormat, compile_format_spec
from .kinds import ArtifactKind, kind_from_dict
from .policy import DEFAULT_POLICY_ID, Grant, Policy, grant_from_dict, load_policy, with_grants
from .ports import (
    PortType,
    builtin_port_types,
    check_port_params,
    port_draws_kinds,
    port_draws_tiers,
    port_type_from_dict,
)
from .routing import Routing, routing_from_dict
from .executor import DEFAULT_ENDPOINT, endpoint_from_manifest
from .stops import STOP_NEVER, StopCondition, resolve_stop_condition


#: Every cycle ends with exactly one stage of this kind (R35 c).
VERDICT_KIND_ID = "mini.verdict.v1"

COMMITMENT_CALL_TWO = "two"
COMMITMENT_CALL_SINGLE = "single"

SEAT_MODEL = "model"
SEAT_MACHINE = "machine"
SEATS: tuple[str, ...] = (SEAT_MODEL, SEAT_MACHINE)


@dataclass(frozen=True)
class Stage:
    """One turn in a cycle. ``max_repeats`` is what bounds attention."""

    stage_id: str
    kind_id: str | None
    ports: tuple[str, ...]
    end: bool
    seat: str = SEAT_MODEL
    max_repeats: int = 0

    def to_dict(self) -> dict[str, object]:
        return {
            "stage_id": self.stage_id,
            "kind_id": self.kind_id,
            "ports": list(self.ports),
            "end": self.end,
            "seat": self.seat,
            "max_repeats": self.max_repeats,
        }


@dataclass(frozen=True)
class Cycles:
    """What ends a run: a cycle cap, a budget cap, a registered condition.

    ``max_completion_tokens`` and ``completion_tokens_per_call`` are declared together and
    turn the call cap from something read between cycles into something reserved before every
    send. They are absent by default and, when absent, are written to no compiled manifest, so
    a manifest compiled before they existed keeps the digest it had.
    """

    max_cycles: int
    max_calls: int | None
    stop_condition: StopCondition
    max_completion_tokens: int | None = None
    completion_tokens_per_call: int | None = None

    def to_dict(self) -> dict[str, object]:
        written: dict[str, object] = {
            "max_cycles": self.max_cycles,
            "max_calls": self.max_calls,
            "stop_condition": self.stop_condition.condition_id,
        }
        if self.max_completion_tokens is not None:
            written["max_completion_tokens"] = self.max_completion_tokens
        if self.completion_tokens_per_call is not None:
            written["completion_tokens_per_call"] = self.completion_tokens_per_call
        return written


@dataclass(frozen=True)
class Source:
    source_id: str
    tier: str
    raw: bytes

    def to_dict(self) -> dict[str, object]:
        return {"source_id": self.source_id, "tier": self.tier, "sha256": digest_bytes(self.raw)}


@dataclass(frozen=True)
class RunPlan:
    """Everything the loop needs, fixed before the first call."""

    manifest_id: str
    manifest_digest: str
    run_id: str
    genesis: str
    header: Mapping[str, Any]
    problem: str
    tiers: tuple[str, ...]
    port_types: Mapping[str, PortType]
    kinds: Mapping[str, ArtifactKind]
    formats: Mapping[str, CompiledFormat]
    stages: tuple[Stage, ...]
    routing: Routing
    cycles: Cycles
    policy: Policy
    policy_overrides: tuple[Mapping[str, Any], ...]
    attention: AttentionPolicy
    sources: tuple[Source, ...]
    #: The service a live run calls. Declared in the manifest, it is part of the header and so
    #: of the run's identity; absent, the shipped default applies and the header carries no key,
    #: so a manifest that says nothing keeps the identity it had before endpoints existed.
    endpoint: Any = DEFAULT_ENDPOINT
    endpoint_declared: bool = False

    def stage(self, stage_id: str) -> Stage:
        for item in self.stages:
            if item.stage_id == stage_id:
                return item
        raise MiniError("MINI_STAGE_UNKNOWN", f"no stage {stage_id!r} in this plan")


def _load_kind_entry(entry: Any, base_dir: Path, where: str) -> dict[str, Any]:
    if type(entry) is str:
        path = base_dir / entry
        try:
            raw = load_strict(path)
        except RecordError as error:
            raise MiniError("MINI_KIND_FILE_UNREADABLE", f"{where} names {entry!r}, which cannot be read: {error}") from error
        validate_instance(raw, KIND_SCHEMA_NAME, "MINI_KIND_FILE_UNREADABLE")
        return object_value(dict(raw)["kind"], f"{path}.kind")
    return object_value(entry, where)


def compile_manifest(path: Path, policy_dir: Path | None = None) -> RunPlan:
    """Read one manifest and compile it into a run plan."""

    if not isinstance(path, Path):
        raise TypeError("path must be pathlib.Path")
    try:
        raw_bytes = path.read_bytes()
        raw = load_strict(path)
    except (OSError, RecordError) as error:
        raise MiniError("MINI_MANIFEST_INVALID", f"cannot read the manifest at {path}: {error}") from error
    validate_instance(raw, MANIFEST_SCHEMA_NAME, "MINI_MANIFEST_INVALID")
    manifest = dict(raw)
    base_dir = path.parent
    manifest_digest = digest_bytes(raw_bytes)

    tiers: list[str] = list(BUILTIN_TIERS)
    for index, item in enumerate(manifest.get("tiers") or []):
        name = text(object_value(item, f"tiers[{index}]").get("tier"), f"tiers[{index}].tier", "MINI_TIER_DUPLICATE")
        if name in tiers:
            raise MiniError("MINI_TIER_DUPLICATE", f"tiers[{index}] declares {name!r}, which already exists")
        tiers.append(name)

    port_types: dict[str, PortType] = builtin_port_types()
    for index, item in enumerate(manifest.get("port_types") or []):
        declared = port_type_from_dict(item, f"port_types[{index}]")
        if declared.port_type in port_types:
            raise MiniError("MINI_PORT_TYPE_DUPLICATE", f"port_types[{index}] declares {declared.port_type!r}, which already exists")
        port_types[declared.port_type] = declared

    kinds: dict[str, ArtifactKind] = {}
    for index, item in enumerate(array_value(manifest.get("kinds"), "kinds")):
        kind = kind_from_dict(_load_kind_entry(item, base_dir, f"kinds[{index}]"), f"kinds[{index}]")
        if kind.kind_id in kinds:
            raise MiniError("MINI_KIND_DUPLICATE", f"kinds[{index}] declares {kind.kind_id!r}, which already exists")
        kinds[kind.kind_id] = kind

    for kind in kinds.values():
        for port in kind.input_ports:
            where = f"kind {kind.kind_id!r} port {port.port_id!r}"
            port_type = port_types.get(port.port_type)
            if port_type is None:
                raise MiniError(
                    "MINI_PORT_TYPE_UNKNOWN",
                    f"{where} names the port type {port.port_type!r}, which no registry entry defines",
                )
            check_port_params(port_type, port.params, where)
            for drawn in port_draws_kinds(port_type, port.params):
                if drawn not in kinds:
                    raise MiniError("MINI_KIND_UNKNOWN", f"{where} draws from the kind {drawn!r}, which nothing declares")
            for drawn in port_draws_tiers(port_type, port.params):
                if drawn not in tiers:
                    raise MiniError("MINI_TIER_UNKNOWN", f"{where} draws from the tier {drawn!r}, which nothing declares")

    formats = {
        kind_id: compile_format_spec(kind.format_spec, f"kind {kind_id!r} format", kind.optional_fields)
        for kind_id, kind in kinds.items()
    }

    stages: list[Stage] = []
    seen_stages: set[str] = set()
    for index, item in enumerate(array_value(manifest.get("stages"), "stages")):
        entry = object_value(item, f"stages[{index}]")
        stage_id = text(entry.get("stage_id"), f"stages[{index}].stage_id", "MINI_STAGE_DUPLICATE")
        if stage_id in seen_stages:
            raise MiniError("MINI_STAGE_DUPLICATE", f"stages[{index}] declares {stage_id!r}, which already exists")
        seen_stages.add(stage_id)
        end = bool(entry.get("end", False))
        if end:
            stages.append(Stage(stage_id=stage_id, kind_id=None, ports=(), end=True))
            continue
        seat = entry.get("seat", SEAT_MODEL)
        if seat not in SEATS:
            raise MiniError("MINI_STAGE_UNKNOWN", f"stages[{index}].seat must be one of {list(SEATS)}, got {seat!r}")
        repeats = entry.get("max_repeats", 0)
        if type(repeats) is not int or not 0 <= repeats <= 16:
            raise MiniError("MINI_CYCLES_INVALID", f"stages[{index}].max_repeats must be a whole number from 0 to 16")
        kind_id = text(entry.get("kind_id"), f"stages[{index}].kind_id", "MINI_KIND_UNKNOWN")
        if kind_id not in kinds:
            raise MiniError("MINI_KIND_UNKNOWN", f"stages[{index}] names the kind {kind_id!r}, which nothing declares")
        ports = tuple(
            text(port, f"stages[{index}].ports[{position}]", "MINI_PORT_UNKNOWN")
            for position, port in enumerate(array_value(entry.get("ports") or [], f"stages[{index}].ports"))
        )
        declared_ports = {port.port_id for port in kinds[kind_id].input_ports}
        unknown = sorted(set(ports) - declared_ports)
        if unknown:
            raise MiniError("MINI_PORT_UNKNOWN", f"stages[{index}] names ports kind {kind_id!r} does not declare: {unknown}")
        stages.append(
            Stage(stage_id=stage_id, kind_id=kind_id, ports=ports, end=False, seat=str(seat), max_repeats=repeats)
        )
    if not stages[-1].end:
        raise MiniError("MINI_STAGE_NO_END", "the stage list must end in a stage marked end")
    for index, stage in enumerate(stages[:-1]):
        if stage.end:
            raise MiniError("MINI_STAGE_END_NOT_LAST", f"stages[{index}] is marked end but is not the last stage")
    verdicts = [index for index, stage in enumerate(stages) if stage.kind_id == VERDICT_KIND_ID]
    if not verdicts:
        raise MiniError(
            "MINI_VERDICT_MISSING",
            f"a cycle ends with one stage of kind {VERDICT_KIND_ID!r}; this stage list has none",
        )
    if len(verdicts) > 1:
        raise MiniError(
            "MINI_VERDICT_DUPLICATE",
            f"a cycle ends with ONE stage of kind {VERDICT_KIND_ID!r}; this stage list has {len(verdicts)}",
        )
    if verdicts[0] != len(stages) - 2:
        raise MiniError(
            "MINI_VERDICT_NOT_LAST",
            f"the {VERDICT_KIND_ID!r} stage must be the last stage before the end stage",
        )

    routing = routing_from_dict(manifest.get("routing"), "routing")
    stage_ids = {stage.stage_id: stage for stage in stages}
    for kind_id, destinations in routing.artifacts.items():
      for destination in destinations:
        if kind_id not in kinds:
            raise MiniError("MINI_ROUTE_INVALID", f"routing names the kind {kind_id!r}, which nothing declares")
        if destination.target == "port":
            target_stage = stage_ids.get(str(destination.stage_id))
            if target_stage is None or target_stage.kind_id is None:
                raise MiniError("MINI_ROUTE_INVALID", f"routing sends {kind_id!r} to the stage {destination.stage_id!r}, which is not a producing stage")
            if str(destination.port_id) not in {port.port_id for port in kinds[target_stage.kind_id].input_ports}:
                raise MiniError("MINI_ROUTE_INVALID", f"routing sends {kind_id!r} to the port {destination.port_id!r}, which that stage's kind does not declare")
        if destination.target == "evidence_store" and str(destination.tier) not in tiers:
            raise MiniError("MINI_TIER_UNKNOWN", f"routing sends {kind_id!r} to the tier {destination.tier!r}, which nothing declares")
    for tier, destinations in routing.evidence.items():
      for destination in destinations:
        if tier not in tiers:
            raise MiniError("MINI_TIER_UNKNOWN", f"routing names the tier {tier!r}, which nothing declares")
        if destination.target == "port_type" and str(destination.port_type) not in port_types:
            raise MiniError("MINI_ROUTE_INVALID", f"routing sends the tier {tier!r} to the port type {destination.port_type!r}, which nothing declares")

    cycles_raw = object_value(manifest.get("cycles") or {}, "cycles", "MINI_CYCLES_INVALID")
    max_cycles = cycles_raw.get("max_cycles", 1)
    if type(max_cycles) is not int or max_cycles < 1:
        raise MiniError("MINI_CYCLES_INVALID", "cycles.max_cycles must be a whole number of cycles, at least 1")
    max_calls = cycles_raw.get("max_calls")
    if max_calls is not None and (type(max_calls) is not int or max_calls < 1):
        raise MiniError("MINI_CYCLES_INVALID", "cycles.max_calls must be a whole number of calls, at least 1")
    max_completion_tokens = cycles_raw.get("max_completion_tokens")
    if max_completion_tokens is not None and (type(max_completion_tokens) is not int or max_completion_tokens < 1):
        raise MiniError("MINI_CYCLES_INVALID", "cycles.max_completion_tokens must be a whole number of tokens, at least 1")
    per_call = cycles_raw.get("completion_tokens_per_call")
    if per_call is not None and (type(per_call) is not int or per_call < 1):
        raise MiniError("MINI_CYCLES_INVALID", "cycles.completion_tokens_per_call must be a whole number of tokens, at least 1")
    if (max_completion_tokens is None) != (per_call is None):
        raise MiniError(
            "MINI_CYCLES_INVALID",
            "cycles.max_completion_tokens and cycles.completion_tokens_per_call are declared together or not at all: "
            "a total with no per-call allowance cannot be reserved before a send, and an allowance with no total bounds nothing",
        )
    if max_completion_tokens is not None and per_call is not None and per_call > max_completion_tokens:
        raise MiniError(
            "MINI_CYCLES_INVALID",
            "cycles.completion_tokens_per_call may not exceed cycles.max_completion_tokens; the first send could never be reserved",
        )
    cycles = Cycles(
        max_cycles=max_cycles,
        max_calls=max_calls,
        max_completion_tokens=max_completion_tokens,
        completion_tokens_per_call=per_call,
        stop_condition=resolve_stop_condition(
            text(cycles_raw.get("stop_condition", STOP_NEVER), "cycles.stop_condition", "MINI_STOP_CONDITION_UNKNOWN")
        ),
    )

    policy_raw = manifest.get("policy") or {}
    base_id = policy_raw.get("base", DEFAULT_POLICY_ID)
    policy = load_policy(text(base_id, "policy.base", "MINI_POLICY_UNKNOWN"), policy_dir)
    grants_raw = array_value(policy_raw.get("grants") or [], "policy.grants", "MINI_POLICY_UNKNOWN")
    overrides = tuple(object_value(item, f"policy.grants[{index}]", "MINI_POLICY_UNKNOWN") for index, item in enumerate(grants_raw))
    grants: list[Grant] = []
    for index, item in enumerate(overrides):
        grant = grant_from_dict(item, f"policy.grants[{index}]")
        if grant.kind_id not in kinds:
            raise MiniError("MINI_KIND_UNKNOWN", f"policy.grants[{index}] names the kind {grant.kind_id!r}, which nothing declares")
        grants.append(grant)
    policy = with_grants(policy, tuple(grants))

    attention_raw = manifest.get("attention") or {}
    attention = resolve_attention_policy(text(attention_raw.get("policy", ATTENTION_OFF), "attention.policy", "MINI_ATTENTION_POLICY_UNKNOWN"))

    sources: list[Source] = []
    seen_sources: set[str] = set()
    for index, item in enumerate(manifest.get("sources") or []):
        entry = object_value(item, f"sources[{index}]", "MINI_SOURCE_INVALID")
        source_id = text(entry.get("source_id"), f"sources[{index}].source_id", "MINI_SOURCE_INVALID")
        if source_id in seen_sources:
            raise MiniError("MINI_SOURCE_INVALID", f"sources[{index}] declares {source_id!r}, which already exists")
        seen_sources.add(source_id)
        has_text, has_path = "text" in entry, "path" in entry
        if has_text == has_path:
            raise MiniError("MINI_SOURCE_INVALID", f"sources[{index}] must carry exactly one of text or path")
        if has_text:
            body = text(entry["text"], f"sources[{index}].text", "MINI_SOURCE_INVALID").encode("utf-8")
        else:
            source_path = base_dir / text(entry["path"], f"sources[{index}].path", "MINI_SOURCE_INVALID")
            try:
                body = source_path.read_bytes()
            except OSError as error:
                raise MiniError("MINI_SOURCE_INVALID", f"sources[{index}] names {source_path}, which cannot be read: {error}") from error
        tier = entry.get("tier", TIER_EVIDENCE)
        if tier not in tiers:
            raise MiniError("MINI_TIER_UNKNOWN", f"sources[{index}] is tagged {tier!r}, which nothing declares")
        sources.append(Source(source_id=source_id, tier=str(tier), raw=body))

    endpoint_declared = manifest.get("endpoint") is not None
    endpoint = endpoint_from_manifest(manifest["endpoint"]) if endpoint_declared else DEFAULT_ENDPOINT

    manifest_id = text(manifest.get("manifest_id"), "manifest_id")
    problem = text(manifest.get("problem"), "problem")
    header: dict[str, Any] = {
        "manifest_id": manifest_id,
        "manifest_digest": manifest_digest,
        "problem": problem,
        "tiers": list(tiers),
        "port_types": [port_types[name].to_dict() for name in sorted(port_types)],
        "kinds": [kinds[name].to_dict() for name in sorted(kinds)],
        "stages": [stage.to_dict() for stage in stages],
        "routing": routing.to_dict(),
        "cycles": cycles.to_dict(),
        "policy": policy.to_dict(),
        "attention": attention.policy_id,
        "sources": [source.to_dict() for source in sources],
        **({"endpoint": endpoint.to_dict()} if endpoint_declared else {}),
    }
    genesis = content_id(RUN_HEADER_DOMAIN, header)
    return RunPlan(
        manifest_id=manifest_id,
        manifest_digest=manifest_digest,
        run_id=genesis[:16],
        genesis=genesis,
        header=header,
        problem=problem,
        tiers=tuple(tiers),
        port_types=port_types,
        kinds=kinds,
        formats=formats,
        stages=tuple(stages),
        routing=routing,
        cycles=cycles,
        policy=policy,
        policy_overrides=overrides,
        attention=attention,
        sources=tuple(sources),
        endpoint=endpoint,
        endpoint_declared=endpoint_declared,
    )
