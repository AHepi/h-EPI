"""Where an artifact's contents go, and where a batch of evidence goes (R15, R16).

Two lists of rules, both written by the operator. One rule serves both. A port's default draw is
everything of the kinds or tiers its type names, so an ordinary conjecturer to
critic to end run needs no routing at all. A declared route REPLACES that
default for the one kind or tier it names, and leaves everything else on the
default; a push is additive on top of whatever the route allows, which is why a
kind or tier may carry more than one route.

A kind or tier routed nowhere reaches NO port. It stays in the store, which is
exactly the condition a withheld citation reports, and it is shown to nobody.
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
    """The declared routes; anything unnamed keeps the default draw."""

    artifacts: Mapping[str, tuple[Destination, ...]]
    evidence: Mapping[str, tuple[Destination, ...]]

    def for_artifact(self, kind_id: str) -> tuple[Destination, ...]:
        return self.artifacts.get(kind_id, ())

    def for_evidence(self, tier: str) -> tuple[Destination, ...]:
        return self.evidence.get(tier, ())

    def to_dict(self) -> dict[str, object]:
        return {
            "artifacts": {key: [item.to_dict() for item in self.artifacts[key]] for key in sorted(self.artifacts)},
            "evidence": {key: [item.to_dict() for item in self.evidence[key]] for key in sorted(self.evidence)},
        }


EMPTY_ROUTING = Routing(artifacts={}, evidence={})


def _collected(
    rules: Any, where: str, key: str, admitted: tuple[str, ...]
) -> dict[str, tuple[Destination, ...]]:
    """Group routes by the kind or tier they name; nowhere may not be combined."""

    collected: dict[str, list[Destination]] = {}
    for index, item in enumerate(rules or []):
        rule = object_value(item, f"{where}[{index}]", "MINI_ROUTE_INVALID")
        subject = text(rule.get(key), f"{where}[{index}].{key}", "MINI_ROUTE_INVALID")
        collected.setdefault(subject, []).append(
            destination_from_dict(rule.get("to"), f"{where}[{index}].to", admitted)
        )
    for subject, destinations in collected.items():
        targets = [destination.target for destination in destinations]
        if "nowhere" in targets and len(targets) > 1:
            raise MiniError(
                "MINI_ROUTE_INVALID",
                f"{where} routes {subject!r} nowhere and somewhere else; the union of nowhere and anything is not nowhere",
            )
    return {subject: tuple(destinations) for subject, destinations in collected.items()}


def routing_from_dict(raw: Any, where: str) -> Routing:
    if raw is None:
        return EMPTY_ROUTING
    entry = object_value(raw, where, "MINI_ROUTE_INVALID")
    return Routing(
        artifacts=_collected(entry.get("artifacts"), f"{where}.artifacts", "from_kind", ARTIFACT_TARGETS),
        evidence=_collected(entry.get("evidence"), f"{where}.evidence", "from_tier", EVIDENCE_TARGETS),
    )
