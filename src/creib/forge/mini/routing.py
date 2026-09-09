"""Where an artifact's contents go, and where a batch of evidence goes (R15, R16).

Two lists of rules, both written by the operator. When neither is declared the
default is a pull: a port draws from the kinds or the tiers its port type
names, so an ordinary conjecturer to critic to end run needs no routing at all.
A declared rule replaces the default for the one kind or tier it names, and
leaves everything else on the default.

A block routed nowhere stays in the store and is never shown to a seat, which
is exactly the condition a withheld citation reports.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .common import MiniError, object_value, text

ARTIFACT_TARGETS: tuple[str, ...] = ("port", "evidence_store", "scratch", "nowhere")
EVIDENCE_TARGETS: tuple[str, ...] = ("port_type", "scratch", "nowhere")


@dataclass(frozen=True)
class Destination:
    """One routing destination, read from the manifest."""

    target: str
    stage_id: str | None = None
    port_id: str | None = None
    port_type: str | None = None
    tier: str | None = None
    destination: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            key: value
            for key, value in (
                ("target", self.target),
                ("stage_id", self.stage_id),
                ("port_id", self.port_id),
                ("port_type", self.port_type),
                ("tier", self.tier),
                ("destination", self.destination),
            )
            if value is not None
        }


def destination_from_dict(raw: Any, where: str, admitted: tuple[str, ...]) -> Destination:
    entry = object_value(raw, where, "MINI_ROUTE_INVALID")
    target = text(entry.get("target"), f"{where}.target", "MINI_ROUTE_TARGET_UNKNOWN")
    if target not in admitted:
        raise MiniError("MINI_ROUTE_TARGET_UNKNOWN", f"{where}.target must be one of {list(admitted)}, got {target!r}")
    destination = Destination(
        target=target,
        stage_id=entry.get("stage_id"),
        port_id=entry.get("port_id"),
        port_type=entry.get("port_type"),
        tier=entry.get("tier"),
        destination=entry.get("destination"),
    )
    required: Mapping[str, tuple[str, ...]] = {
        "port": ("stage_id", "port_id"),
        "port_type": ("port_type",),
        "scratch": ("destination",),
        "evidence_store": ("tier",),
        "nowhere": (),
    }
    for name in required[target]:
        if getattr(destination, name) is None:
            raise MiniError("MINI_ROUTE_INVALID", f"{where} routes to {target!r} and must name {name!r}")
    return destination


@dataclass(frozen=True)
class Routing:
    """The declared routes; anything unnamed keeps the default pull."""

    artifacts: Mapping[str, Destination]
    evidence: Mapping[str, Destination]

    def for_artifact(self, kind_id: str) -> Destination | None:
        return self.artifacts.get(kind_id)

    def for_evidence(self, tier: str) -> Destination | None:
        return self.evidence.get(tier)

    def to_dict(self) -> dict[str, object]:
        return {
            "artifacts": {key: self.artifacts[key].to_dict() for key in sorted(self.artifacts)},
            "evidence": {key: self.evidence[key].to_dict() for key in sorted(self.evidence)},
        }


EMPTY_ROUTING = Routing(artifacts={}, evidence={})


def routing_from_dict(raw: Any, where: str) -> Routing:
    if raw is None:
        return EMPTY_ROUTING
    entry = object_value(raw, where, "MINI_ROUTE_INVALID")
    artifacts: dict[str, Destination] = {}
    for index, item in enumerate(entry.get("artifacts") or []):
        rule = object_value(item, f"{where}.artifacts[{index}]", "MINI_ROUTE_INVALID")
        kind_id = text(rule.get("from_kind"), f"{where}.artifacts[{index}].from_kind", "MINI_ROUTE_INVALID")
        if kind_id in artifacts:
            raise MiniError("MINI_ROUTE_INVALID", f"{where} routes the kind {kind_id!r} twice")
        artifacts[kind_id] = destination_from_dict(rule.get("to"), f"{where}.artifacts[{index}].to", ARTIFACT_TARGETS)
    evidence: dict[str, Destination] = {}
    for index, item in enumerate(entry.get("evidence") or []):
        rule = object_value(item, f"{where}.evidence[{index}]", "MINI_ROUTE_INVALID")
        tier = text(rule.get("from_tier"), f"{where}.evidence[{index}].from_tier", "MINI_ROUTE_INVALID")
        if tier in evidence:
            raise MiniError("MINI_ROUTE_INVALID", f"{where} routes the tier {tier!r} twice")
        evidence[tier] = destination_from_dict(rule.get("to"), f"{where}.evidence[{index}].to", EVIDENCE_TARGETS)
    return Routing(artifacts=artifacts, evidence=evidence)
