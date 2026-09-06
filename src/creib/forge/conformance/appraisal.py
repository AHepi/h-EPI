"""Appraisal of the readings a refutation rests on.

A refutation of a conjecture rests on readings: the oracle's reading of a field on a case,
or a matcher's reading of a span. Those readings can themselves be criticised, and a
criticism can be criticised in turn. This module records such arguments and labels them
by a finite dependency-aware policy:

    in         ready, every essential argument in, every attacker out
    out        not ready, or an essential argument out, or an attacker in
    undecided  everything else

computed as the least fixed point from empty sets. It is grounded semantics over a finite
argument graph with necessary support; it decides nothing semantic. A refutation resting
on an ``out`` reading is not usable; one resting on an ``undecided`` reading is contested;
one resting only on ``in`` readings (or on none that anyone has argued about) is usable.
The labelling is a modelling choice recorded in the pilot, not a verdict on the model.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from creib.errors import RecordError
from creib.strict_json import load_strict

from .common import array_value, identifier, object_value, optional_text, text, validate_instance
from .records import ObservationRecord
from .families import Family
from .routing import TRIGGERS

APPRAISAL_SCHEMA_NAME = "conformance-appraisal.schema.json"
APPRAISAL_SCHEMA_VERSION = "creib.conformance-pilot.appraisal.v1"
READINESS: tuple[str, ...] = ("PASS", "FAIL", "UNKNOWN")
ARGUMENT_KINDS: tuple[str, ...] = ("reading", "criticism", "other")
LABELS: tuple[str, ...] = ("in", "out", "undecided")


@dataclass(frozen=True)
class Support:
    """What an argument supports: an oracle reading of a field on a case, or a matcher reading of a trigger."""

    case_id: str | None
    field: str | None
    corpus_sha256: str | None
    pilot_sha256: str | None
    trigger: str | None
    # The families the reading applies to; empty means every family. A baseline reading of a
    # field is not the reading a rival rule states explicitly for the same field (H24).
    families: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        record: dict[str, object] = {"case_id": self.case_id, "field": self.field, "corpus_sha256": self.corpus_sha256, "pilot_sha256": self.pilot_sha256, "trigger": self.trigger}
        if self.families:
            record["families"] = list(self.families)
        return record


@dataclass(frozen=True)
class Argument:
    argument_id: str
    statement: str
    kind: str
    supports: Support | None
    essential: tuple[str, ...]
    attacks: tuple[str, ...]
    readiness: str
    readiness_reason: str
    register: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "argument_id": self.argument_id,
            "statement": self.statement,
            "kind": self.kind,
            "supports": None if self.supports is None else self.supports.to_dict(),
            "essential": list(self.essential),
            "attacks": list(self.attacks),
            "readiness": self.readiness,
            "readiness_reason": self.readiness_reason,
            "register": self.register,
        }


@dataclass(frozen=True)
class Labels:
    inside: frozenset[str]
    outside: frozenset[str]
    undecided: frozenset[str]
    rounds: int

    def of(self, argument_id: str) -> str:
        if argument_id in self.inside:
            return "in"
        if argument_id in self.outside:
            return "out"
        if argument_id in self.undecided:
            return "undecided"
        raise RecordError(f"unknown argument {argument_id!r}")

    def to_dict(self) -> dict[str, object]:
        return {"in": sorted(self.inside), "out": sorted(self.outside), "undecided": sorted(self.undecided), "rounds": self.rounds}


def appraise(arguments: tuple[Argument, ...]) -> Labels:
    """Least fixed point of the in/out rules; terminates within 2|N| productive rounds."""

    nodes = {a.argument_id: a for a in arguments}
    if len(nodes) != len(arguments):
        raise RecordError("argument ids must be unique")
    for a in arguments:
        for other in a.essential + a.attacks:
            if other not in nodes:
                raise RecordError(f"argument {a.argument_id!r} refers to unknown argument {other!r}")
        if a.argument_id in a.essential:
            raise RecordError(f"argument {a.argument_id!r} lists itself as essential")
    attackers = {x: frozenset(a.argument_id for a in arguments if x in a.attacks) for x in nodes}
    inside: set[str] = set()
    outside: set[str] = set()
    rounds = 0
    while True:
        next_in = inside | {
            a.argument_id for a in arguments
            if a.readiness == "PASS" and set(a.essential) <= inside and attackers[a.argument_id] <= outside
        }
        next_out = outside | {
            a.argument_id for a in arguments
            if a.readiness == "FAIL" or (set(a.essential) & outside) or (attackers[a.argument_id] & inside)
        }
        if next_in & next_out:
            raise RecordError("appraisal invariant failed: an argument labelled both in and out")
        if next_in == inside and next_out == outside:
            return Labels(frozenset(inside), frozenset(outside), frozenset(nodes) - inside - outside, rounds)
        inside, outside = next_in, next_out
        rounds += 1
        if rounds > 2 * len(nodes):
            raise RecordError("appraisal did not reach a fixed point within the finite bound")


# --------------------------------------------------------------------------
# loading
# --------------------------------------------------------------------------


def _support_from_dict(raw: Any, where: str) -> Support | None:
    if raw is None:
        return None
    record = object_value(raw, where)
    case_id = None if record.get("case_id") is None else identifier(record["case_id"], f"{where}.case_id")
    field = optional_text(record.get("field"), f"{where}.field")
    corpus = optional_text(record.get("corpus_sha256"), f"{where}.corpus_sha256")
    pilot = optional_text(record.get("pilot_sha256"), f"{where}.pilot_sha256")
    trigger = optional_text(record.get("trigger"), f"{where}.trigger")
    if trigger is not None and trigger not in TRIGGERS:
        raise RecordError(f"{where}.trigger {trigger!r} is not a known trigger")
    if (case_id is None) != (field is None):
        raise RecordError(f"{where} needs both case_id and field, or neither")
    if case_id is None and trigger is None:
        raise RecordError(f"{where} supports nothing: give case_id and field, or trigger")
    if case_id is not None and trigger is not None:
        raise RecordError(f"{where} supports either a field reading or a trigger reading, not both")
    families: list[str] = []
    for index, item in enumerate(array_value(record.get("families", []), f"{where}.families")):
        name = text(item, f"{where}.families[{index}]")
        if name not in {family.value for family in Family}:
            raise RecordError(f"{where}.families[{index}] {name!r} is not a family")
        if name in families:
            raise RecordError(f"{where}.families repeats {name!r}")
        families.append(name)
    return Support(case_id=case_id, field=field, corpus_sha256=corpus, pilot_sha256=pilot, trigger=trigger, families=tuple(families))


def appraisal_from_dict(raw: Any) -> tuple[Argument, ...]:
    validate_instance(raw, APPRAISAL_SCHEMA_NAME)
    record = object_value(raw, "appraisal file")
    if record.get("schema_version") != APPRAISAL_SCHEMA_VERSION:
        raise RecordError("appraisal schema_version mismatch")
    arguments: list[Argument] = []
    for index, item in enumerate(array_value(record["arguments"], "arguments")):
        where = f"arguments[{index}]"
        entry = object_value(item, where)
        kind = text(entry["kind"], f"{where}.kind")
        if kind not in ARGUMENT_KINDS:
            raise RecordError(f"{where}.kind must be one of {list(ARGUMENT_KINDS)}")
        readiness = text(entry["readiness"], f"{where}.readiness")
        if readiness not in READINESS:
            raise RecordError(f"{where}.readiness must be one of {list(READINESS)}")
        arguments.append(
            Argument(
                argument_id=identifier(entry["argument_id"], f"{where}.argument_id"),
                statement=text(entry["statement"], f"{where}.statement"),
                kind=kind,
                supports=_support_from_dict(entry.get("supports"), f"{where}.supports"),
                essential=tuple(identifier(x, f"{where}.essential[{i}]") for i, x in enumerate(array_value(entry.get("essential", []), f"{where}.essential"))),
                attacks=tuple(identifier(x, f"{where}.attacks[{i}]") for i, x in enumerate(array_value(entry.get("attacks", []), f"{where}.attacks"))),
                readiness=readiness,
                readiness_reason=text(entry["readiness_reason"], f"{where}.readiness_reason"),
                register=optional_text(entry.get("register"), f"{where}.register"),
            )
        )
    result = tuple(arguments)
    appraise(result)  # fail closed on dangling references and on self-support
    return result


def load_appraisal(path: Path) -> tuple[Argument, ...]:
    if not isinstance(path, Path):
        raise TypeError("path must be pathlib.Path")
    try:
        raw = load_strict(path)
    except OSError as exc:
        raise RecordError(f"cannot read appraisal {path}: {exc}") from exc
    return appraisal_from_dict(raw)


# --------------------------------------------------------------------------
# what an observation rests on
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Appraisal:
    arguments: tuple[Argument, ...]
    labels: Labels

    @classmethod
    def build(cls, arguments: tuple[Argument, ...]) -> "Appraisal":
        return cls(arguments=arguments, labels=appraise(arguments))

    def readings_of(self, observation: ObservationRecord, fields: frozenset[str] | None = None, triggers: frozenset[str] | None = None) -> tuple[str, ...]:
        """Arguments whose supported reading this observation's criticisms rest on.

        ``fields`` and ``triggers`` restrict the question to the part of the observation a
        conjecture actually looked at: a refutation of "never emits an extra key" does not
        rest on the oracle's reading of a total that the same reply also got wrong. ``None``
        means every criticised field, or every raised trigger.
        """

        corpus = next((b.sha256 for b in observation.spec_bindings if b.path == "corpus.json"), None)
        pilot = next((b.sha256 for b in observation.spec_bindings if b.path == "pilot.json"), None)
        criticised = {v.field for v in observation.scoring.field_verdicts if v.verdict not in ("MATCH", "NOT_SCORED")}
        if fields is not None:
            criticised &= set(fields)
        raised = set(observation.routing.triggers)
        if triggers is not None:
            raised &= set(triggers)
        found: list[str] = []
        for a in self.arguments:
            s = a.supports
            if s is None:
                continue
            if s.corpus_sha256 is not None and (corpus is None or not corpus.startswith(s.corpus_sha256)):
                continue
            if s.pilot_sha256 is not None and (pilot is None or not pilot.startswith(s.pilot_sha256)):
                continue
            if s.families and observation.variant.family.value not in s.families:
                continue
            if s.case_id is not None and s.case_id == observation.variant.base_case_id and s.field in criticised:
                found.append(a.argument_id)
            elif s.trigger is not None and s.trigger in raised:
                found.append(a.argument_id)
        return tuple(found)

    def standing_of(self, observation: ObservationRecord, fields: frozenset[str] | None = None, triggers: frozenset[str] | None = None) -> str:
        """usable, contested, or defeated, from the labels of the readings the observation rests on."""

        labels = [self.labels.of(x) for x in self.readings_of(observation, fields, triggers)]
        if "out" in labels:
            return "defeated"
        if "undecided" in labels:
            return "contested"
        return "usable"


__all__ = [
    "APPRAISAL_SCHEMA_NAME",
    "APPRAISAL_SCHEMA_VERSION",
    "ARGUMENT_KINDS",
    "Appraisal",
    "Argument",
    "LABELS",
    "Labels",
    "READINESS",
    "Support",
    "appraisal_from_dict",
    "appraise",
    "load_appraisal",
]
