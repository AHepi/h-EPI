"""Run a campaign of blind-spot rounds to its end, deciding the next round from the last one.

A round is a set of manifests run live, one per model. What made the earlier rounds need a
person between them was not the running but the deciding: reading each record and rewriting the
next round's manifests. Each of those rewrites turned out to follow from something already in
mini's own register, and this module states them as rules that fire on measurements a record
carries.

A rule changes how a seat is asked, never what counts as a finding. Nothing here promotes a
candidate, classifies a disagreement, or decides that anything is a blind spot; those are the
readings ``docs/mini/AUTONOMY.md`` says a person makes, and the campaign stops at them by
having no opinion at all.
"""

from __future__ import annotations

import copy
import json
import math
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from .report import RunReading

#: The long fields a grid proposer writes: nested inside the commitments string they need three
#: levels of escaping, and carried by the kind they need one (register M13).
LONG_FIELDS: tuple[str, ...] = ("input", "rewritten", "rewrite", "cell")

_FIELDS_TAIL = (
    ' The commitments are a STRING whose content is JSON of the form {"kernel": "<id>", "expect": "moves" or "unchanged"} '
    "and nothing else. The long fields are NOT in the commitments: this artifact carries "
    '"input", "rewritten", "rewrite" and "cell" as fields of its own, beside "body" and "commitments", each a plain string. '
    "Write the input and the rewritten text out in full there, as instances, never as descriptions."
)
_REAL_BREAKS = (
    " Write real line breaks in those fields, by ending the line, and never the two characters backslash and n: "
    "the fields are strings of the reply and nothing will unescape them for you."
)
_ONE_CHANGE = (
    " The rewritten text differs from the input in exactly ONE part: one line added, removed or moved, and every other "
    "line identical character for character. A pair that differs in more than one part says nothing about any of them."
)


def _proposer_kinds(manifest: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [kind for kind in manifest["kinds"] if "proposal" in str(kind.get("kind_id", "")) and kind.get("instruction")]


def _proposer_stages(manifest: Mapping[str, Any]) -> list[dict[str, Any]]:
    kinds = {str(kind["kind_id"]) for kind in _proposer_kinds(manifest)}
    return [stage for stage in manifest["stages"] if str(stage.get("kind_id", "")) in kinds]


def to_fields_form(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Move a proposer's long fields out of the commitments string into the kind's own fields."""

    changed = copy.deepcopy(dict(manifest))
    for kind in _proposer_kinds(changed):
        kind["optional_fields"] = list(LONG_FIELDS)
        head = str(kind["instruction"])
        cut = head.find(" The commitments are a STRING")
        kind["instruction"] = (head if cut < 0 else head[:cut]) + _FIELDS_TAIL
        schema = kind.get("format", {}).get("commitments", {}).get("all_of", [{}])[0].get("schema")
        if type(schema) is dict:
            schema["required"] = [name for name in schema.get("required", []) if name not in LONG_FIELDS]
            schema["properties"] = {name: value for name, value in schema.get("properties", {}).items() if name not in LONG_FIELDS}
    return changed


def append_instruction(manifest: Mapping[str, Any], sentence: str) -> dict[str, Any]:
    """Add one sentence to every proposer's instruction, once."""

    changed = copy.deepcopy(dict(manifest))
    for kind in _proposer_kinds(changed):
        if sentence.strip() not in str(kind["instruction"]):
            kind["instruction"] = str(kind["instruction"]) + sentence
    return changed


def set_cycles(manifest: Mapping[str, Any], cycles: int) -> dict[str, Any]:
    changed = copy.deepcopy(dict(manifest))
    changed["cycles"] = {**dict(changed.get("cycles") or {}), "max_cycles": cycles}
    return changed


def _in_fields_form(manifest: Mapping[str, Any]) -> bool:
    kinds = _proposer_kinds(manifest)
    return bool(kinds) and all(set(LONG_FIELDS) <= set(kind.get("optional_fields") or ()) for kind in kinds)


def _escaped_breaks(reading: RunReading) -> int:
    """Executions whose input carries the two characters backslash and n and no line break."""

    return sum(1 for row in reading.executions if "\\n" in row.source and "\n" not in row.source)


@dataclass(frozen=True)
class Rule:
    """One way a round rewrites the next, with the register entry it comes from."""

    rule_id: str
    register: str
    why: str
    when: Callable[[RunReading, Mapping[str, Any]], bool]
    apply: Callable[[Mapping[str, Any]], dict[str, Any]] | None

    @property
    def stops(self) -> bool:
        """A rule with nothing to apply says the shape has nothing left to do."""

        return self.apply is None


def _cycles_to_cover(reading: RunReading, manifest: Mapping[str, Any]) -> int:
    proposers = max(1, len(_proposer_stages(manifest)))
    return max(1, math.ceil(len(reading.cells_in_grid) / proposers))


RULES: tuple[Rule, ...] = (
    Rule(
        "fields-form",
        "M13",
        "more replies were refused or dropped than the executor could run, and the long fields are still nested in the commitments string",
        lambda reading, manifest: (reading.format_failures + reading.drops) > reading.ran and not _in_fields_form(manifest),
        to_fields_form,
    ),
    Rule(
        "real-line-breaks",
        "M16",
        "two or more inputs carried the two characters backslash and n where a line break belonged",
        lambda reading, manifest: _escaped_breaks(reading) >= 2 and _REAL_BREAKS.strip() not in json.dumps(manifest),
        lambda manifest: append_instruction(manifest, _REAL_BREAKS),
    ),
    Rule(
        "one-change-per-pair",
        "M14",
        "more than half the pairs the executor ran differed in more than one part",
        lambda reading, manifest: reading.ran > 0 and reading.multi_part_pairs * 2 > reading.ran and _ONE_CHANGE.strip() not in json.dumps(manifest),
        lambda manifest: append_instruction(manifest, _ONE_CHANGE),
    ),
    Rule(
        "cover-the-grid",
        "SPEC 22",
        "the run ended on its cycle cap with cells of its grid never named",
        lambda reading, manifest: bool(reading.cells_uncovered) and reading.stop_reason == "cycle_cap",
        None,  # replaced below, since it needs the reading as well as the manifest
    ),
    Rule(
        "space-exhausted",
        "M10",
        "every cell was named and the executor is being handed repeats, so this shape has nothing left to run",
        lambda reading, manifest: bool(reading.cells_in_grid) and not reading.cells_uncovered and reading.executed.get("duplicate", 0) >= 2,
        None,
    ),
)


@dataclass(frozen=True)
class Decision:
    """What a round decided about one shape, and why, before the next round is run."""

    shape: str
    rules_fired: tuple[str, ...]
    why: tuple[str, ...]
    manifest: dict[str, Any] | None
    stop: bool

    def as_dict(self) -> dict[str, Any]:
        return {"shape": self.shape, "rules_fired": list(self.rules_fired), "why": list(self.why), "stop": self.stop}


def decide(shape: str, reading: RunReading, manifest: Mapping[str, Any]) -> Decision:
    """Apply every rule that fires, in order, to one shape's manifest."""

    current = copy.deepcopy(dict(manifest))
    fired: list[str] = []
    why: list[str] = []
    stop = False
    for rule in RULES:
        if not rule.when(reading, current):
            continue
        fired.append(rule.rule_id)
        why.append(f"{rule.rule_id} ({rule.register}): {rule.why}")
        if rule.rule_id == "cover-the-grid":
            current = set_cycles(current, _cycles_to_cover(reading, current))
            continue
        if rule.stops:
            stop = True
            continue
        current = rule.apply(current)
    if stop:
        return Decision(shape, tuple(fired), tuple(why), None, True)
    if not fired:
        return Decision(shape, (), ("no rule fired: this shape is run again unchanged",), current, False)
    return Decision(shape, tuple(fired), tuple(why), current, False)


def render_decisions(round_name: str, decisions: Sequence[Decision], readings: Mapping[str, RunReading]) -> str:
    """The pre-registration of a round the machine decided: what changed, and on what measurement."""

    lines = [f"# {round_name}", "", "Decided from the previous round's records, before this round was run.", ""]
    for decision in decisions:
        reading = readings.get(decision.shape)
        lines.append(f"## {decision.shape}")
        lines.append("")
        if reading is not None:
            lines.append(
                f"Last run: {reading.proposals} proposals, {reading.ran} run, {len(reading.disagreements)} contradicted, "
                f"{reading.format_failures} replies refused, {reading.drops} dropped, "
                f"{len(reading.cells_named)} of {len(reading.cells_in_grid)} cells named."
            )
            lines.append("")
        for item in decision.why:
            lines.append(f"- {item}")
        if decision.stop:
            lines.append("- this shape is not run again")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


__all__ = ["Decision", "LONG_FIELDS", "RULES", "Rule", "append_instruction", "decide", "render_decisions", "set_cycles", "to_fields_form"]
