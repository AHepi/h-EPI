"""The kernel of each check, stated as boundary points and held by tests.

Every check in the machine is invariant under some transformation of what it reads: change the
reply, the document, or the record that way and the verdict does not move. That invariant set is
the check's kernel, the class of things it cannot do, and a general statement of it would be a
conjecture. What can be stated exactly is a boundary point: one transformation the verdict moves
under, as small as we can make it, beside one it does not, as close to the first as we can make
it. Each point below supplies both, and ``tests/test_kernel.py`` asserts both: the moved verdict
differs from the base, the unmoved one equals it. ``docs/kernel.md`` is generated from this
module by ``tools/kernel_table.py`` and a test refuses drift between the two.

A point that starts to fail because a check now sees what the point says it cannot is not a
broken test; it is the boundary moving, and the point is rewritten in the same change so that
the class stays exactly stated. Nothing here judges a model: the transformations are applied to
synthetic replies and documents, and the verdicts compared are the machine's own.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace
from typing import Any, Callable

from creib.errors import RecordError
from creib.forge.conformance import (
    ChatRequest,
    FakeExecutor,
    Family,
    ReplayExecutor,
    load_corpus,
    load_observation,
    load_pilot_config,
    plan,
    response_from_content,
    route,
    run_pilot,
    score,
)
from creib.forge.conformance import claims as claims_module
from creib.forge.conformance.appraisal import Appraisal, Argument, Support
from creib.forge.conformance.controls import _vocabularies
from creib.forge.conformance.dependence import _moved_fields, _reordered_fields
from creib.forge.conformance.executor import transport_error_kind
from creib.forge.conformance.oracle import _changed, _span_occurs, parse_content
from creib.forge.conformance.records import load_observation_directory
from creib.forge.conformance.units import UnitDependence, relate_units, remove_unit, split_units

ROOT = Path(__file__).resolve().parents[1]
PILOTS = ROOT / "forge" / "conformance" / "pilots"
RUNS = ROOT / "forge" / "conformance" / "runs"
CREATED_ON = "2026-09-09T09:00:00Z"

Verdicts = tuple[Any, Any, Any]


@dataclass(frozen=True)
class Boundary:
    """One point on the boundary of a check's kernel.

    ``moves_under`` names the transformation the verdict moves under (None when nothing moves
    it); ``unchanged_under`` the transformation it does not. ``evaluate`` returns the verdict
    for the base input, for the input transformed the first way (None when ``moves_under`` is
    None), and for the input transformed the second way.
    """

    check: str
    point: str
    moves_under: str | None
    unchanged_under: str
    evaluate: Callable[[], Verdicts]
    note: str = ""


# --------------------------------------------------------------------------
# fixtures, built once
# --------------------------------------------------------------------------

_cache: dict[str, Any] = {}


def _pilot(name: str) -> tuple[Any, Any, Any]:
    key = f"pilot:{name}"
    if key not in _cache:
        config = load_pilot_config(PILOTS / name / "pilot.json")
        corpus = load_corpus(config.corpus_path, config.spec)
        _cache[key] = (config, corpus, plan(config.spec, corpus))
    return _cache[key]


def _variant(pilot: str, family: Family, case_id: str) -> Any:
    _config, _corpus, planned = _pilot(pilot)
    return next(v for v in planned.variants if v.family is family and v.base_case_id == case_id)


def _ord_output() -> dict[str, Any]:
    return {
        "reporter_name": "Alice Nguyen", "subject_name": "Tom Baker", "date_of_birth": "1988-06-12", "incident_date": "2025-04-03",
        "incident_time": "14:30", "phone": "+61412345678", "site": "Warehouse B, Dock 3", "severity": "medium", "injury_reported": True,
        "summary": "Tom slipped and hurt his wrist",
    }


LR_GOOD = {
    "employee_name": "Maya Patel", "leave_type": "annual", "start_date": "2025-10-13", "end_date": "2025-10-17",
    "total_days": 5, "reason": "Family wedding in Adelaide.", "manager_notified": True,
}
LR_SPANS = {
    "employee_name_span": "Maya Patel", "leave_type_span": "annual leave", "start_date_span": "Monday 13 October 2025",
    "end_date_span": "Friday 17 October 2025", "total_days_span": "five working days", "reason_span": "for a family wedding in Adelaide",
}


def _field_verdict(variant: Any, output: dict[str, Any], field: str, *, phrases: tuple[str, ...] = ()) -> str | None:
    scoring = score(variant, response_from_content(json.dumps(output)), refusal_phrases=phrases)
    return {v.field: v.verdict for v in scoring.field_verdicts}.get(field)


def _grounding(variant: Any, output: dict[str, Any], field: str) -> str | None:
    scoring = score(variant, response_from_content(json.dumps(output)))
    return {g.field: g.verdict for g in scoring.grounding_verdicts}.get(field)


def _triggers(variant: Any, content: str, *, phrases: tuple[str, ...] = (), baseline: dict[str, Any] | None = None) -> tuple[str, ...]:
    scoring = score(variant, response_from_content(content), refusal_phrases=phrases, baseline_output=baseline)
    return route(variant, scoring).triggers


def _loci(variant: Any, content: str, *, baseline: dict[str, Any] | None = None) -> tuple[str, ...]:
    scoring = score(variant, response_from_content(content), baseline_output=baseline)
    return tuple(l.locus for l in route(variant, scoring).live_loci)


def _response(variant: Any, content: str, phrases: tuple[str, ...] = ()) -> tuple[str, bool]:
    scoring = score(variant, response_from_content(content), refusal_phrases=phrases)
    return scoring.response_verdict, scoring.recovered_from_prose


# A travel-claim run of BASELINE, REPEAT and NEGATION variants answered by a fake that returns the
# key, wrong on the destination for a fixed set of (case, repeat index), so that floor classes,
# claim predicates and the appraisal have records to read.
WRONG_DESTINATION = {("TRV-001", 1), ("TRV-001", 2), ("TRV-002", 0), ("TRV-002", 1), ("TRV-002", 2), ("TRV-003", 0)}


def _travel_run() -> Any:
    if "travel_run" not in _cache:
        config, corpus, planned = _pilot("travel-claim")
        by_variant = {v.variant_id: v for v in planned.variants}

        def respond(request: ChatRequest):
            variant = by_variant[request.variant_id]
            body = dict(corpus.case(variant.base_case_id).reference_output or ())
            if (variant.base_case_id, request.repeat_index or 0) in WRONG_DESTINATION and variant.family is not Family.NEGATION:
                body["destination_city"] = "Nowhere"
            return response_from_content(json.dumps(body))

        directory = tempfile.mkdtemp(prefix="kernel-travel-")
        _cache["travel_run"] = run_pilot(
            spec=config.spec, corpus=corpus, plan=planned, model="gemma4:31b", executor=FakeExecutor(respond), executor_kind="fake",
            output_dir=Path(directory), created_on=CREATED_ON, families=(Family.BASELINE, Family.REPEAT, Family.NEGATION), limit=None,
        )
    return _cache["travel_run"]


def _claim(condition: dict[str, Any], *, kind: str = "never", families: list[str] | None = None) -> tuple[Any, ...]:
    return claims_module.claims_from_dict({"schema_version": "creib.conformance-pilot.claims.v1", "title": "kernel", "claims": [
        {"claim_id": "K-01", "statement": "kernel point", "kind": kind, "scope": {"families": families, "cases": None, "models": None, "model_call": True}, "condition": condition, "note": None},
    ]})


def _observation(case_id: str, family: Family, repeat_index: int | None = None) -> Any:
    run = _travel_run()
    return next(o for o in run.observations if o.variant.base_case_id == case_id and o.variant.family is family and (o.variant.repeat_index or None) == repeat_index)


def _predicate(condition: dict[str, Any], observation: Any) -> bool:
    run = _travel_run()
    context = claims_module.Context(list(run.observations), [run.run_record])
    return claims_module.compile_condition(condition)(observation, context)


def _floor_class(condition: dict[str, Any], observation_id: str, families: list[str] | None = None) -> str:
    run = _travel_run()
    result = claims_module.evaluate_claims(_claim(condition, families=families), list(run.observations), runs=[run.run_record])[0]
    for (identifier, _m, _c, _f), floor in zip(result.examples, result.example_floors, strict=True):
        if identifier == observation_id:
            return floor
    raise RecordError(f"{observation_id[:16]} did not refute the claim")


def _argument(argument_id: str, readiness: str, *, statement: str = "the key's reading", attacks: tuple[str, ...] = (), support: Support | None = None) -> Argument:
    return Argument(argument_id=argument_id, statement=statement, kind="reading", supports=support, essential=(), attacks=attacks, readiness=readiness, readiness_reason="kernel point", register=None)


def _standing(arguments: tuple[Argument, ...]) -> str:
    observation = _observation("TRV-003", Family.BASELINE)
    fields, triggers = claims_module.condition_footprint({"field_verdict": {"field": "destination_city", "verdict": "MISMATCH"}})
    return Appraisal.build(arguments).standing_of(observation, fields, triggers)


DEST_SUPPORT = Support(case_id="TRV-003", field="destination_city", corpus_sha256=None, pilot_sha256=None, trigger=None)


UNIT_DOCUMENT = """Claim under test: the Recursion Lemma holds for every K-ALPHA structure.

## Recursion Lemma

For a K-ALPHA structure the K-BETA closure is finite, by Lemma 4.

## Definitions

\\[
K-ALPHA \\iff \\text{every chain terminates}
\\]

**Definition 2.** K-BETA is defined as the least closed superset.

### Lemma 4

Every K-GAMMA chain is bounded.

## Remarks

See the Recursion Lemma. A K-ALPHA structure is also K-DELTA.
"""
UNIT_CONFIG = UnitDependence(levels=(2, 3), term_patterns=(r"K-[A-Z]+",), min_occurrences=1)


def _relations(document: str) -> dict[str, str]:
    """Unit relation by heading title; a title is looked up by its first word so that a heading may grow (U-05)."""

    return {r.unit.title.split(" (")[0]: r.relation for r in relate_units(document, UNIT_CONFIG)}


def _controls_stub(text_value: str, items: list[str]) -> Any:
    variant = SimpleNamespace(form_schema={"properties": {"essential": {"type": "array", "items": {"enum": items}}}}, field_order=("essential",), input_document=text_value)
    return SimpleNamespace(variant=variant)


def _record_files(pilot_dir: str) -> list[Path]:
    return sorted(p for p in (RUNS / pilot_dir).iterdir() if p.name.startswith("observation."))


def _v2_pair() -> tuple[Any, Any]:
    """One derivations reply and its re-score under the visible key: a v2 pair with no replayed_from."""

    if "v2_pair" not in _cache:
        originals = {}
        for path in _record_files("signed-derivations")[:120]:
            raw = json.loads(path.read_text(encoding="utf-8"))
            originals[(raw["request_digest"], raw["variant"].get("repeat_index"))] = path
        for path in _record_files("signed-derivations-visible-key"):
            raw = json.loads(path.read_text(encoding="utf-8"))
            key = (raw["request_digest"], raw["variant"].get("repeat_index"))
            if key in originals:
                _cache["v2_pair"] = (load_observation(originals[key]), load_observation(path))
                break
        else:
            raise RecordError("no derivations reply has a re-score with the same request digest")
    return _cache["v2_pair"]


def _v3_pair() -> tuple[Any, Any]:
    """A live reply and its replay, both written under version 3, so the replay names its source."""

    if "v3_pair" not in _cache:
        config, corpus, planned = _pilot("incident-form")
        by_variant = {v.variant_id: v for v in planned.variants}

        def respond(request: ChatRequest):
            variant = by_variant[request.variant_id]
            return response_from_content(json.dumps(dict(corpus.case(variant.base_case_id).reference_output or ())))

        directory = Path(tempfile.mkdtemp(prefix="kernel-replay-"))
        live = run_pilot(spec=config.spec, corpus=corpus, plan=planned, model="gemma4:31b", executor=FakeExecutor(respond), executor_kind="fake",
                         output_dir=directory / "live", created_on=CREATED_ON, families=(Family.BASELINE,), limit=1)
        again = run_pilot(spec=config.spec, corpus=corpus, plan=planned, model="gemma4:31b", executor=ReplayExecutor(directory / "live"), executor_kind="replay",
                          output_dir=directory / "again", created_on=CREATED_ON, families=(Family.BASELINE,), limit=1)
        _cache["v3_pair"] = (live.observations[0], again.observations[0])
    return _cache["v3_pair"]


def _claims_accept(observations: list[Any]) -> str:
    try:
        claims_module.evaluate_claims(_claim({"trigger": "EXTRA_FIELD"}), observations)
    except RecordError:
        return "refused"
    return "accepted"


def _records_directory(files: list[Path], stray: bool = False) -> str:
    with tempfile.TemporaryDirectory() as directory:
        for path in files:
            shutil.copy(path, Path(directory) / path.name)
        if stray:
            (Path(directory) / "notes.txt").write_text("not a record\n", encoding="utf-8")
        try:
            return f"loaded {len(load_observation_directory(Path(directory)))}"
        except RecordError:
            return "refused"


def _cite(sentence: str, record_name: str) -> int:
    import importlib.util

    spec = importlib.util.spec_from_file_location("check_tool_kernel", ROOT / "tools" / "check.py")
    check = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(check)
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "docs").mkdir()
        (root / "docs" / "note.md").write_text(sentence + "\n", encoding="utf-8")
        target = root / "forge" / "conformance" / "runs" / "pilot"
        target.mkdir(parents=True)
        (target / record_name).write_text("{}", encoding="utf-8")
        return len(check.cite_check(root)["problems"])


# --------------------------------------------------------------------------
# the points
# --------------------------------------------------------------------------

def _schema_points() -> list[Boundary]:
    lr = _variant("leave-request", Family.BASELINE, "LR-001")

    def out(**changes: Any) -> dict[str, Any]:
        return {**LR_GOOD, **LR_SPANS, **changes}

    return [
        Boundary("Schema: pattern", "S-01", "a date written outside the pattern (`13/10/2025`)", "a string that fits the pattern and is no date (`2025-13-45`)",
                 lambda: (_field_verdict(lr, out(), "start_date"), _field_verdict(lr, out(start_date="13/10/2025"), "start_date"), _field_verdict(lr, out(start_date="2025-13-45"), "start_date")),
                 "the leave-request fields carry the `unknown` oracle, so the field verdict is the schema check alone"),
        Boundary("Schema: enumeration", "S-02", "a listed value in another case (`Annual`)", "another listed value the document does not support (`sick`)",
                 lambda: (_field_verdict(lr, out(), "leave_type"), _field_verdict(lr, out(leave_type="Annual"), "leave_type"), _field_verdict(lr, out(leave_type="sick"), "leave_type"))),
        Boundary("Schema: maxLength", "S-03", "one character over the bound (161 of 160)", "a string exactly at the bound with no meaning (160 times `x`)",
                 lambda: (_field_verdict(lr, out(), "reason"), _field_verdict(lr, out(reason="x" * 161), "reason"), _field_verdict(lr, out(reason="x" * 160), "reason"))),
        Boundary("Schema: integer type", "S-04", "the number as a string (`\"5\"`), or JSON `true` where an integer is due", "an integer of any size or sign (`5000`, `-5`)",
                 lambda: (_field_verdict(lr, out(), "total_days"), _field_verdict(lr, out(total_days="5"), "total_days"), _field_verdict(lr, out(total_days=5000), "total_days"))),
        Boundary("Schema: boolean type", "S-05", "the word as a string (`\"true\"`), or `1` for `true`", "the other truth value (`false` where the document says the manager was told)",
                 lambda: (_field_verdict(lr, out(), "manager_notified"), _field_verdict(lr, out(manager_notified=1), "manager_notified"), _field_verdict(lr, out(manager_notified=False), "manager_notified"))),
        Boundary("Schema: closed key set", "S-06", "one key the form does not define (`EXTRA_FIELD`)", "the same keys in another order",
                 lambda: (_triggers(lr, json.dumps(out())), _triggers(lr, json.dumps(out(note="x"))), _triggers(lr, json.dumps(dict(reversed(list(out().items()))))))),
    ]


def _oracle_points() -> list[Boundary]:
    ord_v = _variant("incident-form", Family.BASELINE, "ORD-001")
    trv = _variant("travel-claim", Family.BASELINE, "TRV-001")
    bnd = _variant("travel-claim", Family.BOUNDARY_SHIFT, "BND-101")
    lr = _variant("leave-request", Family.BASELINE, "LR-001")
    _config, trv_corpus, _plan = _pilot("travel-claim")
    trv_ref = dict(trv_corpus.case("TRV-001").reference_output or ())
    bnd_ref = dict(trv_corpus.case("BND-101").reference_output or ())

    def ord_out(**changes: Any) -> dict[str, Any]:
        return {**_ord_output(), **changes}

    return [
        Boundary("`exact` oracle", "O-01", "a second space inside the value (`Alice  Nguyen`), or a change of case", "any change to another field of the same reply",
                 lambda: (_field_verdict(ord_v, ord_out(), "reporter_name"), _field_verdict(ord_v, ord_out(reporter_name="Alice  Nguyen"), "reporter_name"), _field_verdict(ord_v, ord_out(summary="wrist, said Alice"), "reporter_name")),
                 "the span check normalises whitespace (G-01); the oracle does not"),
        Boundary("`exact` oracle on a number", "O-02", "the next integer (`196641`)", "nothing on the field; the float `196640.0` is refused before any oracle runs (P-04)",
                 lambda: (_field_verdict(trv, trv_ref, "total_claimed_cents"), _field_verdict(trv, {**trv_ref, "total_claimed_cents": 196641}, "total_claimed_cents"), _field_verdict(trv, {**trv_ref, "purpose": "training"}, "total_claimed_cents"))),
        Boundary("`any_of` oracle", "O-03", "a value outside the admitted readings (`Warehouse B Dock 3`, no comma)", "which admitted reading was taken (`warehouse B, Dock 3`)",
                 lambda: (_field_verdict(ord_v, ord_out(), "site"), _field_verdict(ord_v, ord_out(site="Warehouse B Dock 3"), "site"), _field_verdict(ord_v, ord_out(site="warehouse B, Dock 3"), "site"))),
        Boundary("`regex` oracle", "O-04", "a summary without the required word (`hurt his arm`)", "a summary that contains the word and says the opposite (`No injury to the wrist`)",
                 lambda: (_field_verdict(ord_v, ord_out(), "summary"), _field_verdict(ord_v, ord_out(summary="Tom slipped and hurt his arm"), "summary"), _field_verdict(ord_v, ord_out(summary="No injury to the wrist; Tom was fine"), "summary"))),
        Boundary("`unknown` oracle", "O-05", None, "any value at all (`Nobody` for the employee's name)",
                 lambda: (_field_verdict(lr, {**LR_GOOD, **LR_SPANS}, "employee_name"), None, _field_verdict(lr, {**LR_GOOD, **LR_SPANS, "employee_name": "Nobody"}, "employee_name"))),
        Boundary("`absent` oracle", "O-06", "the key present with any value, `null` included (`UNEXPECTED_PRESENT`)", "any change to another field",
                 lambda: (_field_verdict(trv, trv_ref, "project_code"), _field_verdict(trv, {**trv_ref, "project_code": None}, "project_code"), _field_verdict(trv, {**trv_ref, "purpose": "training"}, "project_code")),
                 "a present `null` is a present key"),
        Boundary("Expected abstention (`any_of` holding `null`)", "O-07", "a value where the document gives none (`2025-05-27`)", "why the field is null: with a span quoting an unrelated sentence, or with no span at all",
                 lambda: (_field_verdict(bnd, bnd_ref, "trip_end"), _field_verdict(bnd, {**bnd_ref, "trip_end": "2025-05-27"}, "trip_end"), _field_verdict(bnd, {**bnd_ref, "trip_end_span": "The flight receipt is attached."}, "trip_end")),
                 "the span is judged by the grounding check, not by the oracle"),
    ]


def _parse_points() -> list[Boundary]:
    ord_v = _variant("incident-form", Family.BASELINE, "ORD-001")
    body = json.dumps(_ord_output())

    def recovered(content: str) -> Any:
        parsed, _verdict, _detail, _recovered = parse_content(content, ())
        return parsed

    return [
        Boundary("JSON recovery", "P-01", "prose or a code fence around the object (`recovered_from_prose` becomes true)", "blank lines and indentation around a bare object",
                 lambda: (_response(ord_v, body), _response(ord_v, "Here is the form:\n" + body), _response(ord_v, "\n\n  " + json.dumps(_ord_output(), indent=2) + "\n"))),
        Boundary("JSON recovery: which object", "P-02", "the later object growing to as many keys as the earlier one (ties go to the last)", "the order of two objects with different key counts: the larger wins wherever it stands",
                 lambda: (recovered('first {"a": 1, "b": 2} then {"a": 3}'), recovered('first {"a": 1, "b": 2} then {"a": 3, "b": 4}'), recovered('first {"a": 3} then {"a": 1, "b": 2}')),
                 "a model's final, smaller answer after a larger draft is not the object scored"),
        Boundary("JSON recovery: repeated key", "P-03", "the order of the two values (the last wins)", "which of the two the model meant",
                 lambda: (recovered('x {"a": 1, "a": 2}')["a"], recovered('x {"a": 2, "a": 1}')["a"], recovered('x {"a": 1, "b": 0, "a": 2}')["a"])),
        Boundary("Strict JSON", "P-04", "a float for an integer value (`5.0` is refused as `INVALID_JSON`)", "pretty-printing, key order, and escaped characters",
                 lambda: (_response(ord_v, '{"total_days": 5}')[0], _response(ord_v, '{"total_days": 5.0}')[0], _response(ord_v, '{\n  "total_days": 5\n}')[0])),
        Boundary("An array reply", "P-05", "one stray character before the array: `[{…}]` is `NOT_AN_OBJECT`, `x [{…}]` recovers the object inside", "how many objects the array holds",
                 lambda: (_response(ord_v, '[{"a": 1}]')[0], _response(ord_v, 'x [{"a": 1}]')[0], _response(ord_v, '[{"a": 1}, {"b": 2}]')[0])),
    ]


def _refusal_points() -> list[Boundary]:
    ord_v = _variant("incident-form", Family.BASELINE, "ORD-001")
    config, _corpus, _plan = _pilot("incident-form")
    phrases = config.spec.refusal_phrases
    body = json.dumps(_ord_output())
    return [
        Boundary("Refusal heuristic", "R-01", "a listed phrase in any case, with straight or typographic apostrophes (`I’m sorry`)", "a refusal in words the list does not hold (`I decline to do this.`), which is `INVALID_JSON` like any other prose",
                 lambda: (_response(ord_v, "Nothing here.", phrases)[0], _response(ord_v, "I\u2019m sorry, no.", phrases)[0], _response(ord_v, "I decline to do this.", phrases)[0])),
        Boundary("Refusal beside a form", "R-02", "a listed phrase in prose around a recovered object (`I cannot stress how clear this is:`), which raises `REFUSAL_SUSPECTED`", "prose without a listed phrase around the same object",
                 lambda: (_triggers(ord_v, body, phrases=phrases), _triggers(ord_v, "I cannot stress how clear this document is:\n" + body, phrases=phrases), _triggers(ord_v, "Happy to help:\n" + body, phrases=phrases)),
                 "the check fires on a non-refusal that contains a listed phrase; the flag is a criticism to read, not a verdict"),
    ]


def _span_points() -> list[Boundary]:
    lr = _variant("leave-request", Family.BASELINE, "LR-001")
    document = lr.input_document or ""

    def out(**changes: Any) -> dict[str, Any]:
        return {**LR_GOOD, **LR_SPANS, **changes}

    def occurs(span: str, relaxations: tuple[str, ...] = ()) -> bool:
        return _span_occurs(span, document, relaxations) is not None

    range_document = "Away 24 to 26 June 2025 for the audit."
    return [
        Boundary("Span occurrence", "G-01", "one letter inside the quotation (`family weding`)", "runs of spaces or a line break inside the quotation (`family\n  wedding`)",
                 lambda: (_grounding(lr, out(), "reason"), _grounding(lr, out(reason_span="for a family weding in Adelaide"), "reason"), _grounding(lr, out(reason_span="for a family \n  wedding in Adelaide"), "reason"))),
        Boundary("Span occurrence: which sentence", "G-02", "a quotation that is not in the document (`wedding in Sydney`)", "a quotation of an unrelated sentence that is (`Hi,` as the source of the reason)",
                 lambda: (_grounding(lr, out(), "reason"), _grounding(lr, out(reason_span="for a family wedding in Sydney"), "reason"), _grounding(lr, out(reason_span="Hi,"), "reason"))),
        Boundary("Span occurrence: length", "G-03", "an empty or blank quotation (`SPAN_MISSING`)", "a one-character quotation that occurs anywhere (`.`)",
                 lambda: (_grounding(lr, out(), "reason"), _grounding(lr, out(reason_span="  "), "reason"), _grounding(lr, out(reason_span="."), "reason"))),
        Boundary("Span occurrence: case", "G-04", "case, when no relaxation is configured (`maya patel`)", "case, under `case_insensitive`; the record names the relaxation, the verdict does not move",
                 lambda: (occurs("Maya Patel"), occurs("maya patel"), occurs("maya patel", ("case_insensitive",)))),
        Boundary("Span occurrence: date ranges", "G-05", "a date inside the range that is not an endpoint (`25 June 2025`)", "whether an endpoint was quoted or completed from the range (`24 June 2025` from `24 to 26 June 2025`); the record says which",
                 lambda: (_span_occurs("24 to 26 June 2025", range_document, ("date_range_completion",)) is not None,
                          _span_occurs("25 June 2025", range_document, ("date_range_completion",)) is not None,
                          _span_occurs("24 June 2025", range_document, ("date_range_completion",)) is not None)),
        Boundary("Value in span", "G-06", "a quotation that does not contain the value (`VALUE_NOT_IN_SPAN`)", "a quotation that contains the value by coincidence: `Adelaide` as the employee's name, quoted from `for a family wedding in Adelaide`",
                 lambda: (_grounding(lr, out(), "employee_name"), _grounding(lr, out(employee_name_span="for a family wedding in Adelaide"), "employee_name"),
                          _grounding(lr, out(employee_name="Adelaide", employee_name_span="for a family wedding in Adelaide"), "employee_name"))),
        Boundary("Value in span: whitespace", "G-08", "a line break inside the quoted name (`Maya \n Patel`): the quotation is found, the value is not inside it", "a trailing space on the quotation",
                 lambda: (_grounding(lr, out(), "employee_name"), _grounding(lr, out(employee_name_span="Maya \n Patel"), "employee_name"), _grounding(lr, out(employee_name_span="Maya Patel "), "employee_name")),
                 "the occurrence check normalises whitespace (G-01) and the containment check does not; a candidate for the same normalisation, recorded here rather than changed"),
        Boundary("Value in span: fields not configured", "G-07", "a quotation absent from the document (`sick leave`)", "a value the quotation does not support, on a field outside `value_in_span_fields` (`sick` quoted from `annual leave`)",
                 lambda: (_grounding(lr, out(), "leave_type"), _grounding(lr, out(leave_type_span="sick leave"), "leave_type"), _grounding(lr, out(leave_type="sick"), "leave_type"))),
    ]


def _change_points() -> list[Boundary]:
    trv = _variant("travel-claim", Family.BASELINE, "TRV-001")
    _config, corpus, _plan = _pilot("travel-claim")
    ref = dict(corpus.case("TRV-001").reference_output or ())
    fields = trv.field_order
    wrong = {**ref, "destination_city": "Nowhere"}
    left = {"essential": ["K-ALPHA", "K-BETA"]}
    right = {"essential": ["K-BETA", "K-ALPHA"]}
    stub_left = SimpleNamespace(scoring=SimpleNamespace(parsed_output=left))
    stub_right = SimpleNamespace(scoring=SimpleNamespace(parsed_output=right))
    stub_other = SimpleNamespace(scoring=SimpleNamespace(parsed_output={"essential": ["K-ALPHA", "K-GAMMA"]}))
    return [
        Boundary("Change against the baseline", "C-01", "one form field's value", "a companion span key, or a key outside the form (H12)",
                 lambda: (_changed(ref, ref, fields), _changed({**ref, "purpose": "training"}, ref, fields), _changed({**ref, "destination_city_span": "elsewhere", "note": "x"}, ref, fields))),
        Boundary("Change against the baseline: size", "C-02", None, "the size and direction of a change: one cent and everything are both `changed`",
                 lambda: (_changed({**ref, "total_claimed_cents": 196641}, ref, fields), None, _changed({**ref, "total_claimed_cents": 0}, ref, fields))),
        Boundary("Change against the baseline: agreement", "C-03", "a reply that differs from a baseline that was wrong", "a reply wrong in exactly the way the baseline was wrong: two identical errors are `unchanged`",
                 lambda: (_changed(ref, ref, fields), _changed(ref, wrong, fields), _changed(wrong, wrong, fields))),
        Boundary("Change against the baseline: arrays", "C-04", "the order of an array's items (`changed_vs_baseline` compares canonical bytes)", "nothing about arrays: the same items in the same order",
                 lambda: (_changed(left, left, ("essential",)), _changed(right, left, ("essential",)), _changed(dict(left), left, ("essential",))),
                 "the `dependence` table reads the same records the other way (D-01)"),
        Boundary("`dependence` table: arrays", "D-01", "a different item", "the order of the items, counted apart as `reordered_only`",
                 lambda: (_moved_fields(stub_left, stub_left, ("essential",)), _moved_fields(stub_other, stub_left, ("essential",)), _moved_fields(stub_right, stub_left, ("essential",))),
                 "`_reordered_fields` names the field the order changed on"),
    ]


def _claims_points() -> list[Boundary]:
    baseline_001 = _observation("TRV-001", Family.BASELINE)
    return [
        Boundary("`field_value` predicate", "Q-01", "case or type of the value (`melbourne`, compared as canonical JSON)", "which of the listed values matched (`[\"Melbourne\", \"Sydney\"]`)",
                 lambda: (_predicate({"field_value": {"field": "destination_city", "values": ["Melbourne"]}}, baseline_001),
                          _predicate({"field_value": {"field": "destination_city", "values": ["melbourne"]}}, baseline_001),
                          _predicate({"field_value": {"field": "destination_city", "values": ["Melbourne", "Sydney"]}}, baseline_001))),
        Boundary("Transport kind", "Q-02", "a refused connection (`ConnectionRefusedError`), which is `other`", "the difference between the remote end closing and resetting the connection (`RemoteDisconnected`, `ConnectionResetError`): both `disconnected`",
                 lambda: (transport_error_kind("RemoteDisconnected: Remote end closed connection without response")[0],
                          transport_error_kind("ConnectionRefusedError: [Errno 111] Connection refused")[0],
                          transport_error_kind("ConnectionResetError: [Errno 104] Connection reset by peer")[0])),
        Boundary("Transport kind: timeouts", "Q-03", "an HTTP status whose body says the gateway timed out (`HTTPError: status 504`), which is `http_status`", "which layer timed out on the client side (`TimeoutError`, or a URLError that says `timed out`): both `timeout`",
                 lambda: (transport_error_kind("TimeoutError: The read operation timed out")[0],
                          transport_error_kind("HTTPError: status 504: upstream request timed out")[0],
                          transport_error_kind("URLError: <urlopen error timed out>")[0]),
                 "the status is read first; a body that says `timed out` under a status is the server's report, not the client's timeout"),
        Boundary("Floor class: structural `none`", "Q-04", None, "why a refutation is `none`: a condition a repeat could never satisfy (a NEGATION reply identical to its baseline) and one it could (a wrong destination on the baseline, right on both repeats) carry the same class",
                 lambda: (_floor_class({"trigger": "IDENTICAL_TO_BASELINE"}, _observation("TRV-001", Family.NEGATION).observation_id, ["NEGATION"]),
                          None,
                          _floor_class({"field_verdict": {"field": "destination_city", "verdict": "MISMATCH"}}, _observation("TRV-003", Family.BASELINE).observation_id)),
                 "the class is read with the condition in hand; H39"),
        Boundary("Floor class: size", "Q-05", None, "how many repeats the floor holds: `all` over one other repeat (a repeat of TRV-001) and over two (the baseline of TRV-002) is one label",
                 lambda: (_floor_class({"field_verdict": {"field": "destination_city", "verdict": "MISMATCH"}}, _observation("TRV-001", Family.REPEAT, 1).observation_id),
                          None,
                          _floor_class({"field_verdict": {"field": "destination_city", "verdict": "MISMATCH"}}, _observation("TRV-002", Family.BASELINE).observation_id))),
    ]


def _unit_points() -> list[Boundary]:
    def count(document: str) -> int:
        return len(split_units(document, (2, 3)))

    bold = UNIT_DOCUMENT.replace("### Lemma 4\n", "**Lemma 4.**\n")
    fenced = UNIT_DOCUMENT + "\n```\n## Not a heading\n```\n"
    extra = UNIT_DOCUMENT + "\n## Appendix\n\nMore.\n"
    lower = UNIT_DOCUMENT.replace("the Recursion Lemma holds", "the recursion lemma holds")
    paren = UNIT_DOCUMENT.replace("the Recursion Lemma holds", "the Recursion Lemma (below) holds")
    no_display = UNIT_DOCUMENT.replace("\\[\nK-ALPHA \\iff \\text{every chain terminates}\n\\]\n", "K-ALPHA means that every chain terminates.\n")
    means = UNIT_DOCUMENT.replace("K-BETA is defined as", "K-BETA means")
    gamma_used = UNIT_DOCUMENT.replace("by Lemma 4.", "by Lemma 4, since every K-GAMMA chain is bounded.")
    gamma_headed = gamma_used.replace("### Lemma 4\n", "### Lemma 4 (K-GAMMA)\n")
    cited = gamma_used.replace("by Lemma 4,", "by Lemma 4 (see below),")
    recursion = next(r.unit for r in relate_units(UNIT_DOCUMENT, UNIT_CONFIG) if r.unit.title == "Recursion Lemma")
    return [
        Boundary("Unit splitting", "U-01", "a heading line at a configured level (`## Appendix`)", "a bold line standing as a heading (`**Lemma 4.**`), which joins the unit before it",
                 lambda: (count(UNIT_DOCUMENT), count(extra), count(bold) + 1),
                 "the third value is the bold document's count plus one, so equality says the bold line made no unit"),
        Boundary("Unit splitting: fences", "U-02", "a heading line at a configured level", "a heading line inside a fenced code block",
                 lambda: (count(UNIT_DOCUMENT), count(extra), count(fenced))),
        Boundary("Unit relation `self`", "U-03", "the case of the heading in the claim (`the recursion lemma` no longer names the unit)", "words around the heading in the claim (`the Recursion Lemma (below)`)",
                 lambda: (_relations(UNIT_DOCUMENT)["Recursion Lemma"], _relations(lower)["Recursion Lemma"], _relations(paren)["Recursion Lemma"]),
                 "the relation is a case-sensitive substring test of the heading against the preamble"),
        Boundary("Unit relation `declared`", "U-04", "a definition given as an `\\iff` display: without it the Definitions unit is `other`", "a definition given in prose (`is defined as`, `means`): neither is read as defining",
                 lambda: (_relations(UNIT_DOCUMENT)["Definitions"], _relations(no_display)["Definitions"], _relations(means)["Definitions"]),
                 "a term's first occurrence and its heading also define it; K-BETA first occurs in the claim's own unit, so its prose definition elsewhere counts for nothing"),
        Boundary("Unit relation: terms", "U-05", "the term in the later unit's heading (`### Lemma 4 (K-GAMMA)`)", "a dependency stated by name (`by Lemma 4`), or by a term the claim's unit uses first: the lemma stays `other`",
                 lambda: (_relations(gamma_used)["Lemma 4"], _relations(gamma_headed)["Lemma 4"], _relations(cited)["Lemma 4"]),
                 "a term's first occurrence defines it, so a unit after the claim's unit is `declared` only through its heading or an `\\iff` display"),
        Boundary("Unit removal", "U-06", None, "references to the removed unit left in the rest of the document (`See the Recursion Lemma.`)",
                 lambda: ("See the Recursion Lemma." in UNIT_DOCUMENT, None, "See the Recursion Lemma." in remove_unit(UNIT_DOCUMENT, recursion))),
    ]


def _control_points() -> list[Boundary]:
    items = ["K-ALPHA", "K-A", "K-BETA"]

    def on_page(text_value: str) -> frozenset[str]:
        return _vocabularies(_controls_stub(text_value, items), _controls_stub("", items))[0]

    return [
        Boundary("Controls: vocabulary on the page", "V-01", "a page that holds none of the list", "whether an item stands on its own or inside a longer item: `K-A` is on a page that holds only `K-ALPHA`",
                 lambda: (on_page("only K-ALPHA here"), on_page("only K-BETA here") - {"K-BETA"}, on_page("K-A and K-ALPHA here")),
                 "a substring test; a candidate for a word-boundary match, recorded here rather than changed"),
    ]


def _record_points() -> list[Boundary]:
    travel = _record_files("travel-claim-v3-order")[:1]
    leave = _record_files("leave-request")[:1]
    return [
        Boundary("Records directory", "K-01", "a file that is not a record (`notes.txt`)", "records of different pilots in one directory: nothing binds a directory to a pilot",
                 lambda: (_records_directory(travel + travel[:0] + leave[:0] + _record_files("travel-claim-v3-order")[1:2]), _records_directory(travel, stray=True), _records_directory(travel + leave))),
        Boundary("A reply beside its replay", "K-02", "a version 3 replay beside the reply it names in `replayed_from` (refused)", "a version 2 re-score beside its original, which names no source (accepted and counted twice)",
                 lambda: (_claims_accept([_v3_pair()[0]]), _claims_accept(list(_v3_pair())), _claims_accept(list(_v2_pair()))),
                 "H38; the derivations pair in this tree is such a case"),
        Boundary("Citation check", "K-03", "an id that names no record", "an id that names a record the sentence is not about",
                 lambda: (_cite("Run `" + "a" * 16 + "` was complete.", "run." + "a" * 16 + ".json"), _cite("Run `" + "b" * 16 + "` was complete.", "run." + "a" * 16 + ".json"),
                          _cite("Observation `" + "a" * 16 + "` shows the refusal.", "run." + "a" * 16 + ".json"))),
    ]


def _routing_points() -> list[Boundary]:
    ord_v = _variant("incident-form", Family.BASELINE, "ORD-001")
    neg = _variant("incident-form", Family.NEGATION, "ORD-001")
    good = _ord_output()
    nonsense = {**good, "reporter_name": "X", "subject_name": "Y", "site": "Z"}
    return [
        Boundary("Routing", "L-01", "no criticism at all (no live locus)", "which field is wrong and how: a wrong name and a wrong site route to the same loci",
                 lambda: (_loci(ord_v, json.dumps({**good, "reporter_name": "Alice Nguyen "})), _loci(ord_v, json.dumps(good)), _loci(ord_v, json.dumps({**good, "site": "Dock 9"})))),
        Boundary("Routing: a negation answered like the baseline", "L-02", "a reply that differs from the baseline (TEST becomes live)", "a baseline that was itself wrong: two identical wrong replies keep TEST out of the loci",
                 lambda: ("TEST" in _loci(neg, json.dumps(good), baseline=good), "TEST" in _loci(neg, json.dumps({**good, "site": "Dock 9"}), baseline=good), "TEST" in _loci(neg, json.dumps(nonsense), baseline=nonsense)),
                 "`IDENTICAL_TO_BASELINE` subsumes every mismatch of a NEGATION variant"),
    ]


def _appraisal_points() -> list[Boundary]:
    return [
        Boundary("Appraisal standing", "A-01", "one argument with readiness `UNKNOWN` supporting the reading (usable becomes contested)", "an argument with readiness `PASS` supporting it: a reading nobody has argued about and one argued and passed stand alike",
                 lambda: (_standing(()), _standing((_argument("R1", "UNKNOWN", support=DEST_SUPPORT),)), _standing((_argument("R1", "PASS", support=DEST_SUPPORT),))),
                 "absence of argument is not endorsement; the label cannot tell them apart"),
        Boundary("Appraisal labels", "A-02", "an attack from an argument labelled `in`", "what the arguments say: two contradictory statements, both `PASS` and unattacked, are both `in`",
                 lambda: (tuple(Appraisal.build((_argument("R1", "PASS", statement="the date is day-first"), _argument("R2", "PASS", statement="the date is month-first"))).labels.of(x) for x in ("R1", "R2")),
                          tuple(Appraisal.build((_argument("R1", "PASS", statement="the date is day-first", attacks=("R2",)), _argument("R2", "PASS", statement="the date is month-first"))).labels.of(x) for x in ("R1", "R2")),
                          tuple(Appraisal.build((_argument("R1", "PASS", statement="the date is month-first"), _argument("R2", "PASS", statement="the date is day-first"))).labels.of(x) for x in ("R1", "R2")))),
    ]


def boundaries() -> tuple[Boundary, ...]:
    points = (
        _schema_points() + _oracle_points() + _parse_points() + _refusal_points() + _span_points() + _change_points()
        + _claims_points() + _unit_points() + _control_points() + _record_points() + _routing_points() + _appraisal_points()
    )
    ids = [p.point for p in points]
    if len(set(ids)) != len(ids):
        raise RecordError("boundary point ids repeat")
    return tuple(points)


__all__ = ["Boundary", "boundaries"]
