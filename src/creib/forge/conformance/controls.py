"""What the controls for an unmoved removal said, control by control, beside the full document.

A controls corpus pairs each probe with cases computed from the document: the claim with
no document, with its own argument only, with that argument and the definitions it uses,
with every other unit carrying a term the argument uses removed at once, with the whole
vocabulary consistently renamed, and with the claim negated. Each control case names its
full-document case as ``pair_of`` and its kind in ``varied`` as ``control=<kind>``. The
table this module builds says, for each run and kind, how many controls left each field as
the full-document baseline had it and how many moved it, beside the control case's own
repeat floor; for the renamed document it says which vocabulary each reply used, the one on
the page or the one the document no longer contains; for the negated claim it says whether
the verdict followed the negation.

Nothing here is a score. A moved field is a description of two records; the table does not
say which reply is right, sums nothing into a figure, and orders no models.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from creib.errors import RecordError

from .common import NON_INDUCTIVE_LIMIT
from .corpus import Corpus
from .families import Family
from .records import ObservationRecord, RunRecord

CONTROL_PREFIX = "control="


def control_kind(varied: str | None) -> tuple[str, str | None] | None:
    """(kind, detail) from a case's ``varied`` text, or None when the case is not a control."""

    if varied is None or not varied.startswith(CONTROL_PREFIX):
        return None
    rest = varied[len(CONTROL_PREFIX):]
    if not rest:
        raise RecordError(f"varied {varied!r} names no control kind")
    kind, _, detail = rest.partition(":")
    return kind, (detail or None)


def _run_observations(run: RunRecord, by_id: Mapping[str, ObservationRecord]) -> list[ObservationRecord]:
    found: list[ObservationRecord] = []
    for observation_id in run.observation_ids:
        observation = by_id.get(observation_id)
        if observation is None:
            raise RecordError(f"run {run.run_id} references observation {observation_id} that was not supplied")
        if observation.run_id != run.run_id:
            raise RecordError(f"observation {observation_id} belongs to a different run")
        found.append(observation)
    return found


def _as_set_if_list(value: Any) -> Any:
    if isinstance(value, list):
        return sorted(str(item) for item in value)
    return value


def _moved_fields(left: Mapping[str, Any], right: Mapping[str, Any], fields: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(field for field in fields if (field in left) != (field in right) or _as_set_if_list(left.get(field)) != _as_set_if_list(right.get(field)))


def _array_fields(observation: ObservationRecord) -> tuple[str, ...]:
    properties = observation.variant.form_schema.get("properties", {})
    return tuple(field for field in observation.variant.field_order if isinstance(properties.get(field), Mapping) and properties[field].get("type") == "array")


def _vocabularies(full: ObservationRecord, renamed: ObservationRecord) -> tuple[frozenset[str], frozenset[str]]:
    """The closed-list items present in the full document's text and those present only in the renamed text."""

    items: set[str] = set()
    properties = full.variant.form_schema.get("properties", {})
    for field in _array_fields(full):
        enum = ((properties.get(field) or {}).get("items") or {}).get("enum") or []
        items.update(str(item) for item in enum)
    full_text = full.variant.input_document or ""
    renamed_text = renamed.variant.input_document or ""
    on_full = frozenset(item for item in items if item in full_text)
    on_renamed = frozenset(item for item in items if item in renamed_text and item not in on_full)
    return on_full, on_renamed


def summarise_controls(corpus: Corpus, runs: list[RunRecord], observations: Iterable[ObservationRecord]) -> dict[str, Any]:
    """Per run and control kind: fields moved against the full-document baseline, the floor, the vocabulary used, the negation's verdict."""

    by_id = {observation.observation_id: observation for observation in observations}
    pairs = list(corpus.pairs())
    rows: list[dict[str, Any]] = []
    detail_rows: list[dict[str, Any]] = []
    for run in runs:
        run_observations = _run_observations(run, by_id)
        fields: tuple[str, ...] = run_observations[0].variant.field_order if run_observations else ()
        baselines = {o.variant.base_case_id: o for o in run_observations if o.variant.family is Family.BASELINE}
        repeats: dict[str, list[ObservationRecord]] = {}
        for o in run_observations:
            if o.variant.family is Family.REPEAT:
                repeats.setdefault(o.variant.base_case_id, []).append(o)
        by_kind: dict[str, dict[str, Any]] = {}
        for full_case, control_case in pairs:
            parsed = control_kind(control_case.varied)
            if parsed is None:
                continue
            kind, detail = parsed
            row = by_kind.setdefault(kind, {
                "model": run.model, "run_id": run.run_id, "kind": kind, "pairs": 0, "unavailable": 0,
                "moved": 0, "unmoved": 0, "moved_by_field": {field: 0 for field in fields},
                "control_repeats": 0, "control_repeats_moved": 0,
                "replies_on_page_vocabulary": 0, "replies_removed_vocabulary": 0, "replies_both": 0, "replies_empty": 0,
                "negation_followed": 0, "negation_not_followed": 0,
            })
            full = baselines.get(full_case.case_id)
            control = baselines.get(control_case.case_id)
            row["pairs"] += 1
            control_repeats = [r for r in repeats.get(control_case.case_id, []) if r.scoring.parsed_output is not None]
            row["control_repeats"] += len(control_repeats)
            if control is not None and control.scoring.parsed_output is not None:
                for r in control_repeats:
                    if _moved_fields(r.scoring.parsed_output, control.scoring.parsed_output, fields):
                        row["control_repeats_moved"] += 1
            detail = {
                "model": run.model, "case_id": control_case.case_id, "kind": kind, "detail": detail, "pair_of": full_case.case_id,
                "full_values": None, "control_values": None, "moved_fields": [], "status": "unavailable",
                "control_observation_id": None if control is None else control.observation_id,
                "full_observation_id": None if full is None else full.observation_id,
            }
            if full is None or control is None or full.scoring.parsed_output is None or control.scoring.parsed_output is None:
                row["unavailable"] += 1
                detail_rows.append(detail)
                continue
            full_out, control_out = full.scoring.parsed_output, control.scoring.parsed_output
            detail["full_values"] = {field: full_out.get(field) for field in fields}
            detail["control_values"] = {field: control_out.get(field) for field in fields}
            moved = _moved_fields(control_out, full_out, fields)
            detail["moved_fields"] = list(moved)
            detail["status"] = "moved" if moved else "unmoved"
            if moved:
                row["moved"] += 1
                for field in moved:
                    row["moved_by_field"][field] += 1
            else:
                row["unmoved"] += 1
            if kind == "renamed":
                on_full, on_renamed = _vocabularies(full, control)
                for reply in [control] + control_repeats:
                    named: set[str] = set()
                    for field in _array_fields(reply):
                        value = (reply.scoring.parsed_output or {}).get(field)
                        if isinstance(value, list):
                            named.update(str(item) for item in value)
                    uses_page = bool(named & on_renamed)
                    uses_removed = bool(named & on_full)
                    if not named:
                        row["replies_empty"] += 1
                    elif uses_page and uses_removed:
                        row["replies_both"] += 1
                    elif uses_removed:
                        row["replies_removed_vocabulary"] += 1
                    else:
                        row["replies_on_page_vocabulary"] += 1
                detail["vocabulary"] = {"on_page": sorted(on_renamed & set(map(str, control_out.get(_array_fields(control)[0], []) if _array_fields(control) else []))), "removed": sorted(on_full & set(map(str, control_out.get(_array_fields(control)[0], []) if _array_fields(control) else [])))}
            if kind == "negated":
                # The claim was negated; the verdict follows the negation when a claim the full document
                # was said to yield is now said not to follow, and the reverse.
                full_follows = full_out.get(fields[0]) if fields else None
                control_follows = control_out.get(fields[0]) if fields else None
                followed = (full_follows == "follows" and control_follows == "does_not_follow") or (full_follows == "does_not_follow" and control_follows == "follows")
                row["negation_followed" if followed else "negation_not_followed"] += 1
                detail["negation"] = {"full": full_follows, "negated": control_follows, "followed": followed}
            detail_rows.append(detail)
        rows.extend(by_kind[kind] for kind in sorted(by_kind))
    return {
        "rows": rows,
        "details": detail_rows,
        "reading": (
            "Each row counts one run's control cases of one kind against the same model's baseline reply on the "
            "paired full-document case. 'moved' means at least one form field differs, an array compared as a "
            "set; 'unmoved' means none does; 'unavailable' means one of the two replies did not parse. The "
            "control's own repeats give its floor. For the renamed document, each reply is classed by the "
            "vocabulary it names: the one on the page, the one the document no longer contains, both, or none. "
            "For the negated claim, the verdict followed the negation when a claim said to follow is now said "
            "not to, or the reverse. None of this scores a reply or a model; a control that leaves the reply "
            "unmoved criticises the document as sent, the probe, and the choice of control together."
        ),
        "epistemic_limit": NON_INDUCTIVE_LIMIT,
    }


def _md_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(cell.replace("|", "\\|") for cell in row) + " |")
    return "\n".join(lines)


def render_controls_markdown(summary: Mapping[str, Any]) -> str:
    parts = ["# Controls beside the full document", "", str(summary["reading"]), ""]
    fields: list[str] = []
    for row in summary["rows"]:
        for field in row["moved_by_field"]:
            if field not in fields:
                fields.append(field)
    parts.append("## Controls by kind")
    parts.append("")
    headers = ["model", "control", "pairs", "unavailable", "unmoved", "moved"] + [f"moved: {field}" for field in fields] + ["control repeats moved"]
    table = [
        [str(r["model"]), str(r["kind"]), str(r["pairs"]), str(r["unavailable"]), str(r["unmoved"]), str(r["moved"])]
        + [str(r["moved_by_field"].get(field, 0)) for field in fields] + [f"{r['control_repeats_moved']} of {r['control_repeats']}"]
        for r in summary["rows"]
    ]
    parts.append(_md_table(headers, table) if table else "No control case was supplied.")
    parts.append("")
    renamed = [r for r in summary["rows"] if r["kind"] == "renamed"]
    if renamed:
        parts.append("## The renamed document: which vocabulary the replies named")
        parts.append("")
        parts.append(_md_table(["model", "replies naming the vocabulary on the page", "naming the vocabulary the document no longer contains", "naming both", "naming nothing"],
                               [[str(r["model"]), str(r["replies_on_page_vocabulary"]), str(r["replies_removed_vocabulary"]), str(r["replies_both"]), str(r["replies_empty"])] for r in renamed]))
        parts.append("")
    negated = [r for r in summary["rows"] if r["kind"] == "negated"]
    if negated:
        parts.append("## The negated claim: whether the verdict followed")
        parts.append("")
        parts.append(_md_table(["model", "verdict followed the negation", "verdict did not follow"], [[str(r["model"]), str(r["negation_followed"]), str(r["negation_not_followed"])] for r in negated]))
        parts.append("")
    parts.append("## Every pair")
    parts.append("")
    details = []
    for d in summary["details"]:
        fv = d["full_values"] or {}
        cv = d["control_values"] or {}
        details.append([
            str(d["model"]), str(d["case_id"]), str(d["kind"]) + (f" ({d['detail']})" if d.get("detail") else ""),
            "; ".join(f"{k}={v!r}" for k, v in fv.items()) or "-",
            "; ".join(f"{k}={v!r}" for k, v in cv.items()) or "-",
            str(d["status"]) + (": " + ", ".join(d["moved_fields"]) if d["moved_fields"] else ""),
        ])
    parts.append(_md_table(["model", "case", "control", "full document", "control", "status"], details) if details else "None.")
    parts.append("")
    parts.append(str(summary["epistemic_limit"]))
    parts.append("")
    return "\n".join(parts)


__all__ = ["CONTROL_PREFIX", "control_kind", "render_controls_markdown", "summarise_controls"]
