"""Input port types: where a port draws from, and how it renders (R5).

Four types ship. A manifest adds more at compile time by declaring a name, the
artifact kinds or the evidence tiers the type draws from, and a rendering rule
from a closed vocabulary. Nothing in this module knows any particular artifact
kind: a port type names kinds as data, so a kind invented in a manifest is
drawn from by a port type declared in the same manifest, and no code changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .common import MiniError, array_value, object_value, text

SOURCES: tuple[str, ...] = ("problem", "artifacts", "evidence", "scratch")
RENDER_RULES: tuple[str, ...] = ("text", "list_bodies", "list_bodies_and_commitments", "legend")

PORT_TYPE_PROBLEM = "problem"
PORT_TYPE_EVIDENCE_LEGEND = "evidence_legend"
PORT_TYPE_ARTIFACTS_OF_KIND = "artifacts_of_kind"
PORT_TYPE_SCRATCH = "scratch"


@dataclass(frozen=True)
class PortType:
    """One registered input port type."""

    port_type: str
    source: str
    kinds: tuple[str, ...]
    tiers: tuple[str, ...]
    render_rule: str
    header: str
    required_params: tuple[str, ...]
    builtin: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "port_type": self.port_type,
            "source": self.source,
            "kinds": list(self.kinds),
            "tiers": list(self.tiers),
            "render_rule": self.render_rule,
            "header": self.header,
            "builtin": self.builtin,
        }


BUILTIN_PORT_TYPES: tuple[PortType, ...] = (
    PortType(PORT_TYPE_PROBLEM, "problem", (), (), "text", "The problem", (), True),
    PortType(PORT_TYPE_EVIDENCE_LEGEND, "evidence", (), (), "legend", "Evidence", ("tiers",), True),
    PortType(PORT_TYPE_ARTIFACTS_OF_KIND, "artifacts", (), (), "list_bodies_and_commitments", "Artifacts so far", ("kind_id",), True),
    PortType(PORT_TYPE_SCRATCH, "scratch", (), (), "list_bodies", "Scratch", ("destination",), True),
)

_RULE_SOURCES: Mapping[str, tuple[str, ...]] = {
    "text": ("problem", "artifacts", "scratch"),
    "list_bodies": ("artifacts", "scratch"),
    "list_bodies_and_commitments": ("artifacts", "scratch"),
    "legend": ("evidence",),
}


def builtin_port_types() -> dict[str, PortType]:
    return {item.port_type: item for item in BUILTIN_PORT_TYPES}


def port_type_from_dict(raw: Any, where: str) -> PortType:
    """Read one manifest-declared port type."""

    entry = object_value(raw, where)
    name = text(entry.get("port_type"), f"{where}.port_type", "MINI_PORT_TYPE_DUPLICATE")
    draws = object_value(entry.get("draws_from"), f"{where}.draws_from", "MINI_PORT_TYPE_DRAWS_FROM_INVALID")
    has_kinds = "artifact_kinds" in draws
    has_tiers = "evidence_tiers" in draws
    if has_kinds == has_tiers:
        raise MiniError(
            "MINI_PORT_TYPE_DRAWS_FROM_INVALID",
            f"{where}.draws_from must name exactly one of artifact_kinds or evidence_tiers",
        )
    kinds: tuple[str, ...] = ()
    tiers: tuple[str, ...] = ()
    if has_kinds:
        items = array_value(draws["artifact_kinds"], f"{where}.draws_from.artifact_kinds", "MINI_PORT_TYPE_DRAWS_FROM_INVALID")
        kinds = tuple(text(item, f"{where}.draws_from.artifact_kinds[{index}]", "MINI_PORT_TYPE_DRAWS_FROM_INVALID") for index, item in enumerate(items))
        source = "artifacts"
    else:
        items = array_value(draws["evidence_tiers"], f"{where}.draws_from.evidence_tiers", "MINI_PORT_TYPE_DRAWS_FROM_INVALID")
        tiers = tuple(text(item, f"{where}.draws_from.evidence_tiers[{index}]", "MINI_PORT_TYPE_DRAWS_FROM_INVALID") for index, item in enumerate(items))
        source = "evidence"
    if not (kinds or tiers):
        raise MiniError("MINI_PORT_TYPE_DRAWS_FROM_INVALID", f"{where}.draws_from must not be empty")
    render = object_value(entry.get("render"), f"{where}.render", "MINI_RENDER_RULE_UNKNOWN")
    rule = text(render.get("rule"), f"{where}.render.rule", "MINI_RENDER_RULE_UNKNOWN")
    if rule not in RENDER_RULES:
        raise MiniError("MINI_RENDER_RULE_UNKNOWN", f"{where}.render.rule must be one of {list(RENDER_RULES)}, got {rule!r}")
    if source not in _RULE_SOURCES[rule]:
        raise MiniError(
            "MINI_PORT_TYPE_DRAWS_FROM_INVALID",
            f"{where} renders with {rule!r}, which cannot render what it draws from",
        )
    header = render.get("header") or name
    return PortType(name, source, kinds, tiers, rule, text(header, f"{where}.render.header", "MINI_RENDER_RULE_UNKNOWN"), (), False)


def check_port_params(port_type: PortType, params: Mapping[str, Any], where: str) -> None:
    """Refuse a port whose parameters do not fit its type."""

    if not port_type.builtin:
        if params:
            raise MiniError("MINI_PORT_PARAMS_INVALID", f"{where} takes no parameters: {port_type.port_type!r} fixes what it draws from")
        return
    unknown = sorted(set(params) - set(port_type.required_params))
    if unknown:
        raise MiniError("MINI_PORT_PARAMS_INVALID", f"{where} carries parameters {port_type.port_type!r} does not take: {unknown}")
    for name in port_type.required_params:
        if name not in params:
            raise MiniError("MINI_PORT_PARAMS_INVALID", f"{where} must carry the parameter {name!r}")
    if "tiers" in params:
        items = array_value(params["tiers"], f"{where}.params.tiers", "MINI_PORT_PARAMS_INVALID")
        if not items:
            raise MiniError("MINI_PORT_PARAMS_INVALID", f"{where}.params.tiers must not be empty")
        for index, item in enumerate(items):
            text(item, f"{where}.params.tiers[{index}]", "MINI_PORT_PARAMS_INVALID")
    for name in ("kind_id", "destination"):
        if name in params:
            text(params[name], f"{where}.params.{name}", "MINI_PORT_PARAMS_INVALID")


def port_draws_kinds(port_type: PortType, params: Mapping[str, Any]) -> tuple[str, ...]:
    if port_type.source != "artifacts":
        return ()
    if port_type.builtin:
        return (str(params["kind_id"]),)
    return port_type.kinds


def port_draws_tiers(port_type: PortType, params: Mapping[str, Any]) -> tuple[str, ...]:
    if port_type.source != "evidence":
        return ()
    if port_type.builtin:
        return tuple(str(item) for item in params["tiers"])
    return port_type.tiers
