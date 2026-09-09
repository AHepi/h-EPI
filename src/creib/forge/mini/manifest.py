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


@dataclass(frozen=True)
class Stage:
    stage_id: str
    kind_id: str | None
    ports: tuple[str, ...]
    end: bool

    def to_dict(self) -> dict[str, object]:
        return {"stage_id": self.stage_id, "kind_id": self.kind_id, "ports": list(self.ports), "end": self.end}


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
    policy: Policy
    policy_overrides: tuple[Mapping[str, Any], ...]
    attention: AttentionPolicy
    sources: tuple[Source, ...]

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
        kind_id: compile_format_spec(kind.format_spec, f"kind {kind_id!r} format")
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
        stages.append(Stage(stage_id=stage_id, kind_id=kind_id, ports=ports, end=False))
    if not stages[-1].end:
        raise MiniError("MINI_STAGE_NO_END", "the stage list must end in a stage marked end")
    for index, stage in enumerate(stages[:-1]):
        if stage.end:
            raise MiniError("MINI_STAGE_END_NOT_LAST", f"stages[{index}] is marked end but is not the last stage")

    routing = routing_from_dict(manifest.get("routing"), "routing")
    stage_ids = {stage.stage_id: stage for stage in stages}
    for kind_id, destination in routing.artifacts.items():
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
    for tier, destination in routing.evidence.items():
        if tier not in tiers:
            raise MiniError("MINI_TIER_UNKNOWN", f"routing names the tier {tier!r}, which nothing declares")
        if destination.target == "port_type" and str(destination.port_type) not in port_types:
            raise MiniError("MINI_ROUTE_INVALID", f"routing sends the tier {tier!r} to the port type {destination.port_type!r}, which nothing declares")

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
        "policy": policy.to_dict(),
        "attention": attention.policy_id,
        "sources": [source.to_dict() for source in sources],
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
        policy=policy,
        policy_overrides=overrides,
        attention=attention,
        sources=tuple(sources),
    )
