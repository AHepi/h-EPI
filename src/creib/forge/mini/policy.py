"""Permission and authorisation: what a stage may read, write, and change (R17).

A shipped document states the defaults; a run adds grants. Read as three
sentences: a stage may read exactly the ports its kind declares and its stage
names; it may write its own output, the evidence store, and scratch, but may
not push into another stage's input port; and its output changes nothing about
any other artifact's standing.

That last sentence is the one this prototype cannot yet vary. The slot exists
so a later policy can grant a standing, and any value other than "nothing" is
refused at compile rather than accepted and quietly ignored.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from creib.errors import RecordError
from creib.strict_json import load_strict

from .common import (
    MINI_POLICY_DIR,
    POLICY_SCHEMA_NAME,
    MiniError,
    array_value,
    object_value,
    text,
)
from .routing import ARTIFACT_TARGETS, Destination, destination_from_dict

DEFAULT_POLICY_ID = "mini.policy.default.v1"
READ_MODES: tuple[str, ...] = ("declared_ports",)
WRITE_MODES: tuple[str, ...] = ("own_output", "evidence_store", "scratch", "nowhere")
CHANGES_NOTHING = "nothing"


@dataclass(frozen=True)
class PolicyDefaults:
    read: str
    write: tuple[str, ...]
    changes: str

    def to_dict(self) -> dict[str, object]:
        return {"read": self.read, "write": list(self.write), "changes": self.changes}


@dataclass(frozen=True)
class Grant:
    kind_id: str
    may_read_port_types: tuple[str, ...] | None
    may_write: tuple[Destination, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "kind_id": self.kind_id,
            "may_read_port_types": None if self.may_read_port_types is None else list(self.may_read_port_types),
            "may_write": [item.to_dict() for item in self.may_write],
        }


@dataclass(frozen=True)
class Policy:
    policy_id: str
    defaults: PolicyDefaults
    grants: tuple[Grant, ...]

    def grant_for(self, kind_id: str) -> Grant | None:
        for item in self.grants:
            if item.kind_id == kind_id:
                return item
        return None

    def may_read(self, kind_id: str, port_type: str) -> bool:
        grant = self.grant_for(kind_id)
        if grant is not None and grant.may_read_port_types is not None:
            return port_type in grant.may_read_port_types
        return self.defaults.read == "declared_ports"

    def may_write(self, kind_id: str, destination: Destination) -> bool:
        if destination.target in self.defaults.write:
            return True
        grant = self.grant_for(kind_id)
        if grant is None:
            return False
        for allowed in grant.may_write:
            if (
                allowed.target == destination.target
                and allowed.stage_id == destination.stage_id
                and allowed.port_id == destination.port_id
            ):
                return True
        return False

    def to_dict(self) -> dict[str, object]:
        return {
            "policy_id": self.policy_id,
            "defaults": self.defaults.to_dict(),
            "grants": [item.to_dict() for item in self.grants],
        }


def grant_from_dict(raw: Any, where: str) -> Grant:
    entry = object_value(raw, where, "MINI_POLICY_UNKNOWN")
    read_raw = entry.get("may_read_port_types")
    read = (
        None
        if read_raw is None
        else tuple(
            text(item, f"{where}.may_read_port_types[{index}]", "MINI_POLICY_UNKNOWN")
            for index, item in enumerate(array_value(read_raw, f"{where}.may_read_port_types", "MINI_POLICY_UNKNOWN"))
        )
    )
    write_raw = array_value(entry.get("may_write") or [], f"{where}.may_write", "MINI_POLICY_UNKNOWN")
    return Grant(
        kind_id=text(entry.get("kind_id"), f"{where}.kind_id", "MINI_POLICY_UNKNOWN"),
        may_read_port_types=read,
        may_write=tuple(
            destination_from_dict(item, f"{where}.may_write[{index}]", ARTIFACT_TARGETS)
            for index, item in enumerate(write_raw)
        ),
    )


def policy_from_dict(raw: Any, where: str) -> Policy:
    entry = object_value(raw, where, "MINI_POLICY_UNKNOWN")
    defaults_raw = object_value(entry.get("defaults"), f"{where}.defaults", "MINI_POLICY_UNKNOWN")
    read = text(defaults_raw.get("read"), f"{where}.defaults.read", "MINI_POLICY_DEFAULT_UNKNOWN")
    if read not in READ_MODES:
        raise MiniError("MINI_POLICY_DEFAULT_UNKNOWN", f"{where}.defaults.read must be one of {list(READ_MODES)}, got {read!r}")
    write_raw = array_value(defaults_raw.get("write"), f"{where}.defaults.write", "MINI_POLICY_DEFAULT_UNKNOWN")
    write = tuple(text(item, f"{where}.defaults.write[{index}]", "MINI_POLICY_DEFAULT_UNKNOWN") for index, item in enumerate(write_raw))
    unknown = sorted(set(write) - set(WRITE_MODES))
    if unknown:
        raise MiniError("MINI_POLICY_DEFAULT_UNKNOWN", f"{where}.defaults.write names modes nothing implements: {unknown}")
    changes = text(defaults_raw.get("changes"), f"{where}.defaults.changes", "MINI_POLICY_CHANGE_UNSUPPORTED")
    if changes != CHANGES_NOTHING:
        raise MiniError(
            "MINI_POLICY_CHANGE_UNSUPPORTED",
            f"{where}.defaults.changes is {changes!r}; this prototype mints no standing and implements only {CHANGES_NOTHING!r}",
        )
    grants_raw = array_value(entry.get("grants") or [], f"{where}.grants", "MINI_POLICY_UNKNOWN")
    return Policy(
        policy_id=text(entry.get("policy_id"), f"{where}.policy_id", "MINI_POLICY_UNKNOWN"),
        defaults=PolicyDefaults(read=read, write=write, changes=changes),
        grants=tuple(grant_from_dict(item, f"{where}.grants[{index}]") for index, item in enumerate(grants_raw)),
    )


def load_policy(policy_id: str, directory: Path | None = None) -> Policy:
    """Load one shipped policy document by its id."""

    base = MINI_POLICY_DIR if directory is None else directory
    path = base / f"{policy_id}.json"
    try:
        raw = load_strict(path)
    except RecordError as error:
        raise MiniError("MINI_POLICY_UNKNOWN", f"no policy document {policy_id!r} at {path}: {error}") from error
    from .common import validate_instance

    validate_instance(raw, POLICY_SCHEMA_NAME, "MINI_POLICY_UNKNOWN")
    policy = policy_from_dict(raw, str(path))
    if policy.policy_id != policy_id:
        raise MiniError("MINI_POLICY_UNKNOWN", f"{path} declares the policy id {policy.policy_id!r}, not {policy_id!r}")
    return policy


def with_grants(policy: Policy, grants: tuple[Grant, ...]) -> Policy:
    """A run's overrides: the base document plus this run's extra grants."""

    merged: list[Grant] = list(policy.grants)
    for grant in grants:
        merged = [item for item in merged if item.kind_id != grant.kind_id] + [grant]
    return Policy(policy_id=policy.policy_id, defaults=policy.defaults, grants=tuple(merged))
