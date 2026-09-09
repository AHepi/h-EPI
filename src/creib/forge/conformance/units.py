"""Document units and the terms they define: the mechanical side of the UNIT_DEPENDENCE family.

A document under test is split into units at its own headings, with no manifest: every
heading at a configured level starts a unit that runs to the next heading at that level or
above. A unit is removed by deleting its lines and leaving every other line as it was.

Terms are whatever the configured patterns match in the document (a commitment name, a
symbol in a display, an abbreviation). A unit is taken to define a term when the term's
first occurrence is in it, when its heading names the term, or when it contains a display
that introduces the term with ``\\iff``. That is a heuristic over the document's own
conventions, not a reading of it; the family records what it computed, and the summary
compares it with what the model asserted and with what removal moved.

For one probe (a case whose preamble names the claim), each unit stands in one relation:
``self`` when its heading occurs in the preamble (the document's own argument for the
claim), ``declared`` when it defines a term the self units or the preamble use, and
``other`` otherwise. Nothing here calls a model or reads a key.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, Mapping

from creib.errors import RecordError

from .common import array_value, integer, object_value, text

_HEADING = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*$")
_FENCE = re.compile(r"^\s*(```|~~~)")
_DISPLAY_OPEN = re.compile(r"^\s*\\\[\s*$")
_DISPLAY_CLOSE = re.compile(r"^\s*\\\]\s*$")
UNIT_RELATIONS: tuple[str, ...] = ("self", "declared", "other")
MAX_HEADING_LEVEL = 6


@dataclass(frozen=True)
class Unit:
    unit_id: str
    level: int
    title: str
    start: int
    end: int

    def to_dict(self) -> dict[str, object]:
        return {"unit_id": self.unit_id, "level": self.level, "title": self.title, "start": self.start, "end": self.end}


@dataclass(frozen=True)
class UnitDependence:
    """Configuration of the UNIT_DEPENDENCE family; empty ``levels`` (the default) switches it off."""

    levels: tuple[int, ...]
    term_patterns: tuple[str, ...]
    min_occurrences: int

    @property
    def active(self) -> bool:
        return bool(self.levels)

    def to_dict(self) -> dict[str, object]:
        return {"levels": list(self.levels), "term_patterns": list(self.term_patterns), "min_occurrences": self.min_occurrences}


def unit_dependence_from_dict(raw: object, where: str = "unit_dependence") -> UnitDependence:
    if raw is None:
        return UnitDependence(levels=(), term_patterns=(), min_occurrences=1)
    record = object_value(raw, where)
    levels: list[int] = []
    for index, item in enumerate(array_value(record["levels"], f"{where}.levels")):
        level = integer(item, f"{where}.levels[{index}]", minimum=1)
        if level > MAX_HEADING_LEVEL:
            raise RecordError(f"{where}.levels[{index}] must be at most {MAX_HEADING_LEVEL}")
        if level in levels:
            raise RecordError(f"{where}.levels repeats {level}")
        levels.append(level)
    if not levels:
        raise RecordError(f"{where}.levels must name at least one heading level")
    patterns: list[str] = []
    for index, item in enumerate(array_value(record["term_patterns"], f"{where}.term_patterns")):
        pattern = text(item, f"{where}.term_patterns[{index}]")
        try:
            compiled = re.compile(pattern)
        except re.error as exc:
            raise RecordError(f"{where}.term_patterns[{index}] is not a valid regular expression: {exc}") from exc
        if compiled.groups > 1:
            raise RecordError(f"{where}.term_patterns[{index}] must have at most one capture group")
        if pattern in patterns:
            raise RecordError(f"{where}.term_patterns repeats {pattern!r}")
        patterns.append(pattern)
    if not patterns:
        raise RecordError(f"{where}.term_patterns must name at least one pattern")
    minimum = integer(record.get("min_occurrences", 1), f"{where}.min_occurrences", minimum=1)
    return UnitDependence(levels=tuple(levels), term_patterns=tuple(patterns), min_occurrences=minimum)


def _headings(lines: list[str]) -> list[tuple[int, int, str]]:
    """(line index, level, title) for every heading outside a fenced code block."""

    found: list[tuple[int, int, str]] = []
    fenced = False
    for index, line in enumerate(lines):
        if _FENCE.match(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        match = _HEADING.match(line)
        if match is not None:
            found.append((index, len(match.group(1)), match.group(2)))
    return found


def split_units(document: str, levels: tuple[int, ...]) -> tuple[Unit, ...]:
    """The units of a document at the given heading levels, in document order.

    A unit runs from its heading line to the line before the next heading whose level is at
    or above the deepest configured level; headings above every configured level (a part
    title) end a unit and belong to none, so they are never removed.
    """

    if not levels:
        raise RecordError("split_units needs at least one heading level")
    lines = document.split("\n")
    headings = _headings(lines)
    deepest = max(levels)
    units: list[Unit] = []
    for position, (start, level, title) in enumerate(headings):
        if level not in levels:
            continue
        end = len(lines)
        for later_start, later_level, _ in headings[position + 1:]:
            if later_level <= deepest:
                end = later_start
                break
        units.append(Unit(unit_id=f"U{len(units) + 1:02d}", level=level, title=title, start=start, end=end))
    return tuple(units)


def preamble_text(document: str) -> str:
    """The lines before the first heading; the part of a case document that a unit removal never touches."""

    lines = document.split("\n")
    headings = _headings(lines)
    if not headings:
        return document
    return "\n".join(lines[: headings[0][0]])


def unit_text(document: str, unit: Unit) -> str:
    return "\n".join(document.split("\n")[unit.start : unit.end])


def remove_unit(document: str, unit: Unit) -> str:
    """The document with the unit's lines deleted and every other line byte-identical."""

    lines = document.split("\n")
    if unit.start < 0 or unit.end > len(lines) or unit.start >= unit.end:
        raise RecordError(f"unit {unit.unit_id} does not lie inside the document")
    return "\n".join(lines[: unit.start] + lines[unit.end :])


def _term_spans(text_value: str, patterns: Iterable[str]) -> dict[tuple[int, int], str]:
    """Every span a pattern matches, keyed by the span of the term itself (the capture group when there is one).

    Two patterns that match the same characters (a symbol inside a display and the bare
    abbreviation) count as one occurrence, not two.
    """

    spans: dict[tuple[int, int], str] = {}
    for pattern in patterns:
        compiled = re.compile(pattern)
        for match in compiled.finditer(text_value):
            group = 1 if compiled.groups else 0
            spans[match.span(group)] = match.group(group)
    return spans


def terms_in(text_value: str, patterns: Iterable[str]) -> tuple[str, ...]:
    """Every term a pattern matches in the text, sorted and unique; the capture group when the pattern has one."""

    return tuple(sorted(set(_term_spans(text_value, patterns).values())))


def term_occurrences(document: str, patterns: Iterable[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for term in _term_spans(document, patterns).values():
        counts[term] = counts.get(term, 0) + 1
    return counts


def document_terms(document: str, config: UnitDependence) -> tuple[str, ...]:
    """The terms the document uses at least ``min_occurrences`` times, sorted."""

    counts = term_occurrences(document, config.term_patterns)
    return tuple(sorted(term for term, count in counts.items() if count >= config.min_occurrences))


def _display_blocks(lines: list[str]) -> list[tuple[int, int]]:
    blocks: list[tuple[int, int]] = []
    open_at: int | None = None
    for index, line in enumerate(lines):
        if open_at is None and _DISPLAY_OPEN.match(line):
            open_at = index
        elif open_at is not None and _DISPLAY_CLOSE.match(line):
            blocks.append((open_at, index + 1))
            open_at = None
    return blocks


def defining_units(document: str, units: tuple[Unit, ...], config: UnitDependence) -> dict[str, tuple[str, ...]]:
    """term -> the unit ids taken to define it (first occurrence, heading, or an ``\\iff`` display)."""

    lines = document.split("\n")
    terms = document_terms(document, config)
    result: dict[str, list[str]] = {term: [] for term in terms}
    if not terms:
        return {}
    for term in terms:
        first_line: int | None = None
        for index, line in enumerate(lines):
            if term in terms_in(line, config.term_patterns):
                first_line = index
                break
        for unit in units:
            defines = False
            if first_line is not None and unit.start <= first_line < unit.end:
                defines = True
            if term in terms_in(unit.title, config.term_patterns):
                defines = True
            if not defines:
                for open_at, close_at in _display_blocks(lines):
                    if open_at < unit.start or close_at > unit.end:
                        continue
                    block = "\n".join(lines[open_at:close_at])
                    if "\\iff" in block and term in terms_in(block, config.term_patterns):
                        defines = True
                        break
            if defines and unit.unit_id not in result[term]:
                result[term].append(unit.unit_id)
    return {term: tuple(ids) for term, ids in result.items()}


@dataclass(frozen=True)
class UnitRelation:
    unit: Unit
    relation: str
    defines: tuple[str, ...]


def relate_units(document: str, config: UnitDependence) -> tuple[UnitRelation, ...]:
    """Each unit of a case document with its relation to the claim the preamble names.

    ``self``: the unit's heading occurs in the preamble. ``declared``: the unit defines a term
    that a self unit or the preamble uses. ``other``: neither. Every unit also carries the
    terms it is taken to define, so a record says what the classification rested on.
    """

    if not config.active:
        raise RecordError("relate_units needs an active unit_dependence configuration")
    units = split_units(document, config.levels)
    if not units:
        raise RecordError(f"the document has no unit at heading levels {list(config.levels)}")
    preamble = preamble_text(document)
    defining = defining_units(document, units, config)
    self_ids = {unit.unit_id for unit in units if unit.title and unit.title in preamble}
    used: set[str] = set(terms_in(preamble, config.term_patterns))
    for unit in units:
        if unit.unit_id in self_ids:
            used.update(terms_in(unit_text(document, unit), config.term_patterns))
    declared_ids = {unit_id for term, ids in defining.items() if term in used for unit_id in ids} - self_ids
    defines_by_unit: dict[str, list[str]] = {unit.unit_id: [] for unit in units}
    for term, ids in defining.items():
        for unit_id in ids:
            defines_by_unit[unit_id].append(term)
    relations: list[UnitRelation] = []
    for unit in units:
        relation = "self" if unit.unit_id in self_ids else "declared" if unit.unit_id in declared_ids else "other"
        relations.append(UnitRelation(unit=unit, relation=relation, defines=tuple(sorted(defines_by_unit[unit.unit_id]))))
    return tuple(relations)


def unit_table_markdown(document: str, config: UnitDependence, relations: Mapping[str, tuple[UnitRelation, ...]] | None = None) -> str:
    """The document's units and the terms each is taken to define; model-free."""

    units = split_units(document, config.levels)
    defining = defining_units(document, units, config)
    defines_by_unit: dict[str, list[str]] = {unit.unit_id: [] for unit in units}
    for term, ids in defining.items():
        for unit_id in ids:
            defines_by_unit[unit_id].append(term)
    rows = ["| unit | level | title | lines | defines |", "|---|---|---|---|---|"]
    for unit in units:
        rows.append(f"| {unit.unit_id} | {unit.level} | {unit.title} | {unit.start + 1}-{unit.end} | {', '.join(sorted(defines_by_unit[unit.unit_id])) or '-'} |")
    parts = ["## Units", "", *rows, ""]
    undefined = [term for term, ids in defining.items() if not ids]
    if undefined:
        parts.append(f"Terms that no unit is taken to define: {', '.join(undefined)}.")
        parts.append("")
    if relations:
        parts.append("## Relations by probe")
        parts.append("")
        parts.append("| probe | self | declared | other |")
        parts.append("|---|---|---|---|")
        for probe_id, items in relations.items():
            by_relation = {name: [r.unit.unit_id for r in items if r.relation == name] for name in UNIT_RELATIONS}
            parts.append(f"| {probe_id} | {', '.join(by_relation['self']) or '-'} | {', '.join(by_relation['declared']) or '-'} | {len(by_relation['other'])} units |")
        parts.append("")
    return "\n".join(parts)


__all__ = [
    "MAX_HEADING_LEVEL",
    "UNIT_RELATIONS",
    "Unit",
    "UnitDependence",
    "UnitRelation",
    "defining_units",
    "document_terms",
    "preamble_text",
    "relate_units",
    "remove_unit",
    "split_units",
    "term_occurrences",
    "terms_in",
    "unit_dependence_from_dict",
    "unit_table_markdown",
    "unit_text",
]
