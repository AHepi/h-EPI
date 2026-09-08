"""The UNIT_DEPENDENCE family: units found in the document by pattern, one removed at a time,
the reply compared with the same model's baseline and never with a key.

The property these tests hold the family to is that nothing about the document is declared:
the units, the terms, the unit that carries the claim's own argument, and the units that
define the terms that argument uses are all computed from the document's text, recorded on
the variant, and read back by the dependence table and the claim predicates. Everything else
is bookkeeping: the chain to the baseline, the replay of ids, the array field the form
profile now admits, and counts that describe two records without scoring either.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from creib.canonical import canonical_bytes
from creib.errors import RecordError
from creib.forge.conformance import (
    ChatRequest,
    FakeExecutor,
    Family,
    load_corpus,
    load_pilot_config,
    load_run,
    plan,
    render_dependence_markdown,
    response_from_content,
    route,
    run_pilot,
    score,
    summarise_dependence,
)
from creib.forge.conformance import claims as claims_module
from creib.forge.conformance.corpus import parse_oracle
from creib.forge.conformance.families import _unit_fields_from_dict, variant_from_dict
from creib.forge.conformance.units import (
    Unit,
    UnitDependence,
    defining_units,
    document_terms,
    preamble_text,
    relate_units,
    remove_unit,
    split_units,
    terms_in,
    unit_dependence_from_dict,
    unit_table_markdown,
)
from creib.strict_json import loads_strict

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import gen_unit_dependence_corpus as generator  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PILOT_DIR = ROOT / "forge" / "conformance" / "pilots" / "semantics-unit-dependence"
INCIDENT_DIR = ROOT / "forge" / "conformance" / "pilots" / "incident-form"
TOOL = ROOT / "tools" / "run_conformance_pilot.py"
CREATED_ON = "2026-09-08T00:00:00Z"
PATTERNS = ("K-[A-Z]+", r"\\mathrm\{([A-Za-z]+)\}", r"\b(UED|UU|UC|OCA)\b")

DOC = """Claim under assessment: Recursion is not universality

Question here.

# Part I

## Alpha K-REAL

Text about \\mathrm{Usable} and K-REAL twice: K-REAL.

## Recursion is not universality

**Claim.** Body uses K-REAL and UED.

### Sub

deeper text

# Part II

## Beta

Define

\\[
\\mathrm{UED} \\iff x
\\]

```
# not a heading
```

## Gamma

Nothing defined here; mentions \\mathrm{Usable}.
"""


def _config(**overrides) -> UnitDependence:
    raw = {"levels": [2, 3], "term_patterns": list(PATTERNS), "min_occurrences": 1}
    raw.update(overrides)
    return unit_dependence_from_dict(raw)


_CONFIG = load_pilot_config(PILOT_DIR / "pilot.json")
_CORPUS = load_corpus(_CONFIG.corpus_path, _CONFIG.spec)
_PLAN = plan(_CONFIG.spec, _CORPUS)


class UnitSplittingTests(unittest.TestCase):
    def test_units_follow_headings_and_skip_fences_and_part_titles(self) -> None:
        units = split_units(DOC, (2, 3))
        self.assertEqual([(u.unit_id, u.level, u.title) for u in units], [
            ("U01", 2, "Alpha K-REAL"), ("U02", 2, "Recursion is not universality"), ("U03", 3, "Sub"), ("U04", 2, "Beta"), ("U05", 2, "Gamma"),
        ])
        # a level-3 unit ends the level-2 unit above it; a part title ends a unit and belongs to none
        self.assertEqual(units[1].end, units[2].start)
        self.assertIn("# Part II", DOC.split("\n")[units[2].end])
        # a fenced line that looks like a heading is not one
        self.assertNotIn("not a heading", [u.title for u in units])
        only_two = split_units(DOC, (2,))
        self.assertEqual([u.title for u in only_two], ["Alpha K-REAL", "Recursion is not universality", "Beta", "Gamma"])
        self.assertIn("### Sub", "\n".join(DOC.split("\n")[only_two[1].start:only_two[1].end]), "at level 2 alone the subsection stays inside its section")
        with self.assertRaisesRegex(RecordError, "at least one heading level"):
            split_units(DOC, ())

    def test_removal_leaves_every_other_line_byte_identical(self) -> None:
        units = split_units(DOC, (2, 3))
        without = remove_unit(DOC, units[1])
        lines = DOC.split("\n")
        self.assertEqual(without.split("\n"), lines[: units[1].start] + lines[units[1].end :])
        self.assertNotIn("## Recursion is not universality", without)
        self.assertIn("### Sub", without)
        self.assertEqual(preamble_text(DOC), "Claim under assessment: Recursion is not universality\n\nQuestion here.\n")
        self.assertEqual(preamble_text("no headings at all"), "no headings at all")
        with self.assertRaisesRegex(RecordError, "does not lie inside"):
            remove_unit(DOC, Unit(unit_id="U99", level=2, title="x", start=5, end=999))

    def test_terms_definitions_and_relations_come_from_the_text(self) -> None:
        config = _config()
        self.assertEqual(terms_in(DOC, PATTERNS), ("K-REAL", "UED", "Usable"))
        self.assertEqual(document_terms(DOC, _config(min_occurrences=3)), ("K-REAL",))
        units = split_units(DOC, config.levels)
        defining = defining_units(DOC, units, config)
        self.assertEqual(defining["K-REAL"], ("U01",), "heading and first occurrence")
        self.assertEqual(defining["Usable"], ("U01",), "first occurrence only; a later mention does not define")
        self.assertEqual(defining["UED"], ("U02", "U04"), "first occurrence and the iff display")
        relations = relate_units(DOC, config)
        self.assertEqual([(r.unit.unit_id, r.relation) for r in relations], [("U01", "declared"), ("U02", "self"), ("U03", "other"), ("U04", "declared"), ("U05", "other")])
        self.assertEqual(next(r.defines for r in relations if r.unit.unit_id == "U01"), ("K-REAL", "Usable"))
        table = unit_table_markdown(DOC, config, {"P-01": relations})
        self.assertIn("| U02 | 2 | Recursion is not universality |", table)
        self.assertIn("| P-01 | U02 | U01, U04 | 2 units |", table)
        with self.assertRaisesRegex(RecordError, "no unit at heading levels"):
            relate_units("plain text without headings", config)
        with self.assertRaisesRegex(RecordError, "active unit_dependence"):
            relate_units(DOC, UnitDependence(levels=(), term_patterns=(), min_occurrences=1))

    def test_configuration_checks(self) -> None:
        self.assertFalse(unit_dependence_from_dict(None).active)
        self.assertTrue(_config().active)
        self.assertEqual(_config().to_dict()["min_occurrences"], 1)
        for raw, message in (
            ({"levels": [], "term_patterns": ["x"]}, "at least one heading level"),
            ({"levels": [7], "term_patterns": ["x"]}, "at most 6"),
            ({"levels": [2, 2], "term_patterns": ["x"]}, "repeats 2"),
            ({"levels": [2], "term_patterns": []}, "at least one pattern"),
            ({"levels": [2], "term_patterns": ["("]}, "not a valid regular expression"),
            ({"levels": [2], "term_patterns": ["(a)(b)"]}, "at most one capture group"),
            ({"levels": [2], "term_patterns": ["x", "x"]}, "repeats 'x'"),
            ({"levels": [2], "term_patterns": ["x"], "min_occurrences": 0}, "min_occurrences"),
        ):
            with self.assertRaisesRegex(RecordError, message):
                unit_dependence_from_dict(raw)


class PlanningTests(unittest.TestCase):
    def test_absent_configuration_is_off_and_adds_nothing(self) -> None:
        config = load_pilot_config(INCIDENT_DIR / "pilot.json")
        self.assertFalse(config.spec.unit_dependence.active)
        counts = dict(plan(config.spec, load_corpus(config.corpus_path, config.spec)).counts)
        self.assertEqual(counts["UNIT_DEPENDENCE"], 0)
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "pilot"
            shutil.copytree(INCIDENT_DIR, target)
            raw = loads_strict((target / "pilot.json").read_text(encoding="utf-8"))
            raw["unit_dependence"] = {"levels": [2], "term_patterns": ["K-[A-Z]+"]}
            (target / "pilot.json").write_text(json.dumps(raw, indent=2), encoding="utf-8")
            loaded = load_pilot_config(target / "pilot.json")
            with self.assertRaisesRegex(RecordError, "no unit at heading levels"):
                plan(loaded.spec, load_corpus(loaded.corpus_path, loaded.spec))

    def test_every_unit_is_removed_once_per_probe_with_its_relation_recorded(self) -> None:
        counts = dict(_PLAN.counts)
        self.assertEqual((counts["BASELINE"], counts["REPEAT"], counts["UNIT_DEPENDENCE"]), (5, 10, 290), "five probes, fifty-eight units each")
        units = [v for v in _PLAN.variants if v.family is Family.UNIT_DEPENDENCE and v.base_case_id == "DEP-03"]
        self.assertEqual(len(units), 58)
        by_relation = {}
        for variant in units:
            by_relation.setdefault(variant.removed_unit_relation, []).append(variant.removed_unit_id)
        self.assertEqual(by_relation["self"], ["U46"])
        self.assertEqual(by_relation["declared"], ["U07", "U39", "U40", "U41", "U42"])
        self.assertEqual(len(by_relation["other"]), 52)
        removed = next(v for v in units if v.removed_unit_id == "U42")
        self.assertEqual(removed.removed_unit_title, "Universal explanatory disposition")
        self.assertEqual(removed.removed_unit_defines, ("RecursiveCapacity", "UC", "UED", "UU"))
        self.assertNotIn("### Universal explanatory disposition", removed.input_document or "")
        self.assertIn("### Universal creative inquiry", removed.input_document or "")
        self.assertIn("Claim under assessment: Recursion is not universality", removed.input_document or "")
        self.assertIs(removed.expectation_kind.value, "RECORD_DEPENDENCE") if False else self.assertEqual(removed.expectation_kind.value, "RECORD_DEPENDENCE")
        # the body carries the unit keys only for this family, and ids replay from content
        body = removed.to_dict()
        self.assertEqual(body["removed_unit_relation"], "declared")
        rebuilt = variant_from_dict(loads_strict(canonical_bytes(body).decode("utf-8")))
        self.assertEqual(rebuilt, removed)
        baseline = next(v for v in _PLAN.variants if v.family is Family.BASELINE)
        self.assertNotIn("removed_unit_id", baseline.to_dict())
        again = plan(load_pilot_config(PILOT_DIR / "pilot.json").spec, _CORPUS)
        self.assertEqual(again.plan_id, _PLAN.plan_id)

    def test_unit_keys_are_checked_on_the_way_back_in(self) -> None:
        with self.assertRaisesRegex(RecordError, "set without removed_unit_id"):
            _unit_fields_from_dict({"removed_unit_title": "x"})
        with self.assertRaisesRegex(RecordError, "not a known relation"):
            _unit_fields_from_dict({"removed_unit_id": "U01", "removed_unit_title": "x", "removed_unit_relation": "cousin", "removed_unit_defines": []})
        self.assertEqual(_unit_fields_from_dict({"removed_unit_id": None}), {})


class ArrayFieldTests(unittest.TestCase):
    def test_the_form_profile_admits_an_array_of_strings_and_scores_its_constraints(self) -> None:
        baseline = next(v for v in _PLAN.variants if v.family is Family.BASELINE)
        for output, expected in (
            ({"follows": "follows", "essential": ["UED", "K-RECURSION"]}, "NOT_SCORED"),
            ({"follows": "follows", "essential": ["nope"]}, "ENUM_VIOLATION"),
            ({"follows": "follows", "essential": ["UED", "UED"]}, "LENGTH_VIOLATION"),
            ({"follows": "follows", "essential": [1]}, "TYPE_VIOLATION"),
            ({"follows": "follows", "essential": "UED"}, "TYPE_VIOLATION"),
        ):
            scoring = score(baseline, response_from_content(json.dumps(output)), refusal_phrases=())
            self.assertEqual({v.field: v.verdict for v in scoring.field_verdicts}["essential"], expected, output)
        with self.assertRaisesRegex(RecordError, "admits only the unknown or absent oracle"):
            parse_oracle({"field": "essential", "kind": "exact", "value": "UED", "values": None, "pattern": None, "oracle_status": "source_scoped", "rationale": "r"}, "o", _CONFIG.spec.form_schema["properties"])


def _fake() -> FakeExecutor:
    """Replies keyed on which unit is missing; the second identical request for DEP-01 moves.

    DEP-03 and DEP-05 depend on U42 (the UED definition): without it, follows becomes
    not_determined. DEP-03 without its own section drops UED from the essential list.
    Any request without the Purpose section (U02) gets a reply that is not a form.
    """

    seen: dict[str, int] = {}
    baseline = {
        "DEP-01": {"follows": "follows", "essential": ["K-REAL"]},
        "DEP-02": {"follows": "follows", "essential": ["Usable", "Standing"]},
        "DEP-03": {"follows": "follows", "essential": ["K-RECURSION", "UED"]},
        "DEP-04": {"follows": "not_determined", "essential": ["K-RECURSION"]},
        "DEP-05": {"follows": "follows", "essential": ["UED"]},
    }

    def respond(request: ChatRequest):
        case_id = next(c.case_id for c in _CORPUS.cases if c.renderings["prose"].split("\n", 1)[0] in request.user)
        if "### Purpose" not in request.user:
            return response_from_content("not a form")
        reply = dict(baseline[case_id])
        if "### Universal explanatory disposition" not in request.user and case_id in ("DEP-03", "DEP-05"):
            reply["follows"] = "not_determined"
        if "## Recursion is not universality" not in request.user and case_id == "DEP-03":
            reply["essential"] = ["K-RECURSION"]
        seen[request.request_digest] = seen.get(request.request_digest, 0) + 1
        if case_id == "DEP-01" and seen[request.request_digest] == 2:
            reply["follows"] = "not_determined"
        return response_from_content(json.dumps(reply))

    return FakeExecutor(respond)


class RunTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.directory = tempfile.mkdtemp()
        cls.result = run_pilot(
            spec=_CONFIG.spec, corpus=_CORPUS, plan=_PLAN, model="gpt-oss:20b", executor=_fake(), executor_kind="fake",
            output_dir=Path(cls.directory) / "out", created_on=CREATED_ON, families=(Family.BASELINE, Family.REPEAT, Family.UNIT_DEPENDENCE), limit=None, order="interleaved",
        )

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.directory, ignore_errors=True)

    def _unit(self, case_id: str, unit_id: str):
        return next(o for o in self.result.observations if o.variant.base_case_id == case_id and o.variant.removed_unit_id == unit_id)

    def test_removals_chain_to_the_baseline_and_route_plurally(self) -> None:
        baselines = {o.variant.base_case_id: o for o in self.result.observations if o.variant.family is Family.BASELINE}
        moved = self._unit("DEP-03", "U42")
        self.assertEqual(moved.baseline_observation_id, baselines["DEP-03"].observation_id)
        self.assertTrue(moved.scoring.changed_vs_baseline)
        self.assertEqual(moved.routing.triggers, ("DEPENDENCE_CHANGED",))
        self.assertEqual(set(moved.routing.loci), {"AUXILIARY", "TEST", "SCOPE"}, "no key and no model verdict: the document as sent, the probe and its floor, the choice of units")
        self.assertTrue(all(v.verdict == "NOT_SCORED" for v in moved.scoring.field_verdicts), "dependence is recorded, never scored")
        still = self._unit("DEP-03", "U50")
        self.assertFalse(still.scoring.changed_vs_baseline)
        self.assertEqual(still.routing.triggers, ("DEPENDENCE_UNCHANGED",))
        self.assertEqual(set(still.routing.loci), {"AUXILIARY", "TEST", "SCOPE"})
        gone = self._unit("DEP-03", "U02")
        self.assertEqual(gone.scoring.response_verdict, "INVALID_JSON")
        self.assertIsNone(gone.scoring.changed_vs_baseline)
        self.assertEqual(self.result.run_record.scope_label, "REFUTED_CASES_PRESENT", "the five non-form replies keep the model live; a removal that parsed never does, since nothing is scored")
        self.assertEqual(dict(self.result.run_record.response_verdict_counts).get("INVALID_JSON"), 5)
        self.assertEqual(dict(self.result.run_record.family_counts).get("UNIT_DEPENDENCE"), 290)

    def test_the_table_reads_relations_the_floor_and_the_asserted_list_from_records(self) -> None:
        summary = summarise_dependence([self.result.run_record], self.result.observations)
        rows = {row["relation"]: row for row in summary["rows"]}
        self.assertEqual((rows["self"]["observations"], rows["declared"]["observations"], rows["other"]["observations"]), (5, 7, 278), "one self per probe; declared U31, U07 and U39 to U42, U42; the rest other")
        self.assertEqual(rows["declared"]["moved"], 2, "U42 on DEP-03 and DEP-05")
        self.assertEqual(rows["declared"]["moved_by_field"], {"follows": 2, "essential": 0})
        self.assertEqual(rows["self"]["moved"], 1, "DEP-03 without its own section drops UED")
        self.assertEqual(rows["self"]["moved_by_field"], {"follows": 0, "essential": 1})
        self.assertEqual(rows["other"]["unavailable"], 5, "the Purpose unit removed on every probe drew a non-form")
        self.assertEqual(rows["other"]["moved"], 0)
        floor = {row["case_id"]: row for row in summary["floor"]}
        self.assertEqual((floor["DEP-01"]["repeats"], floor["DEP-01"]["moved"]), (2, 1))
        self.assertEqual(floor["DEP-03"]["moved"], 0)
        assertion = summary["assertions"][0]
        self.assertEqual(assertion["asserted_and_moved"], 2, "U42 defines UED, which DEP-03 and DEP-05 named")
        self.assertGreaterEqual(assertion["asserted_and_unmoved"], 1, "U07 defines K-RECURSION, named by DEP-03 and DEP-04, and its removal moved nothing")
        probe = next(row for row in summary["probes"] if row["case_id"] == "DEP-03")
        self.assertEqual(probe["asserted"], ["K-RECURSION", "UED"])
        self.assertEqual(probe["moved_units_by_field"], {"follows": ["U42"], "essential": ["U46"]})
        markdown = render_dependence_markdown(summary)
        for heading in ("## Removals by relation", "## Repeat floor", "## The model's asserted dependencies against removal", "## Probes", "## Examples"):
            self.assertIn(heading, markdown)
        self.assertIn("U42 Universal explanatory disposition (declared)", markdown)
        # a run whose observations are missing is refused, as everywhere else
        with self.assertRaisesRegex(RecordError, "was not supplied"):
            summarise_dependence([self.result.run_record], self.result.observations[:3])

    def test_the_pre_registered_conjectures_evaluate_over_the_records(self) -> None:
        claims = claims_module.load_claims(PILOT_DIR / "claims.json")
        results = {r.claim.claim_id: r for r in claims_module.evaluate_claims(claims, list(self.result.observations), runs=[self.result.run_record])}
        self.assertEqual(results["UDP-03"].status, "UNREFUTED_FOR_DECLARED_SCOPE", "the own-argument removal moved essential, not follows")
        self.assertEqual(results["UDP-02"].status, "REFUTED", "U07 and U39 to U41 left both fields unmoved")
        self.assertEqual(results["UDP-01"].status, "UNREFUTED_FOR_DECLARED_SCOPE")
        self.assertEqual(results["UDP-04"].status, "REFUTED", "DEP-01's second repeat moved")
        self.assertEqual(results["UDP-05"].status, "UNREFUTED_FOR_DECLARED_SCOPE")
        self.assertEqual(results["UDP-06"].status, "UNREFUTED_FOR_DECLARED_SCOPE")
        self.assertEqual(results["UDP-07"].status, "UNREFUTED_FOR_DECLARED_SCOPE")
        self.assertFalse(results["UDP-07"].shown_able_to_fail, "no call timed out anywhere, so the survival is not shown able to fail")
        self.assertFalse(results["UDP-01"].shown_able_to_fail, "no other-unit removal moved follows anywhere, so the survival is not shown able to fail")
        self.assertFalse(results["UDP-03"].shown_able_to_fail, "the self removal moved essential, never follows; liveness is of the whole condition, not of one conjunct")

    def test_claim_predicates_and_their_refusals(self) -> None:
        context = claims_module.Context(list(self.result.observations), [self.result.run_record])
        holds = lambda condition, o: claims_module.compile_condition(condition, "c")(o, context)
        moved = self._unit("DEP-03", "U42")
        self.assertTrue(holds({"unit": {"relation": ["declared"]}}, moved))
        self.assertTrue(holds({"unit": {"removed": ["U42", "U07"]}}, moved))
        self.assertFalse(holds({"unit": {"relation": ["self"]}}, moved))
        self.assertTrue(holds({"value_changed": {"field": "follows"}}, moved))
        self.assertFalse(holds({"value_changed": {"field": "essential"}}, moved))
        self.assertTrue(holds({"field_value": {"field": "follows", "values": ["not_determined", "does_not_follow"]}}, moved))
        self.assertTrue(holds({"field_value": {"field": "essential", "values": [["K-RECURSION", "UED"]]}}, moved), "arrays compare as canonical JSON")
        baseline = next(o for o in self.result.observations if o.variant.family is Family.BASELINE and o.variant.base_case_id == "DEP-03")
        self.assertFalse(holds({"unit": {"relation": ["other"]}}, baseline), "a baseline removed nothing")
        self.assertFalse(holds({"value_changed": {"field": "follows"}}, baseline), "nothing to compare a baseline with")
        gone = self._unit("DEP-03", "U02")
        self.assertFalse(holds({"value_changed": {"field": "follows"}}, gone), "an unparsed reply changed nothing")
        self.assertFalse(holds({"field_value": {"field": "follows", "values": ["follows"]}}, gone))
        for condition, message in (
            ({"unit": {}}, "must name a relation or a removed unit"),
            ({"unit": {"relation": ["cousin"]}}, "unknown relations"),
            ({"field_value": {"field": "follows", "values": []}}, "at least one value"),
        ):
            with self.assertRaisesRegex(RecordError, message):
                claims_module.compile_condition(condition, "c")
        fields, _ = claims_module.condition_footprint({"all_of": [{"field_value": {"field": "follows", "values": ["x"]}}, {"value_changed": {"field": "essential"}}, {"unit": {"relation": ["self"]}}]})
        self.assertEqual(fields, frozenset({"follows", "essential"}))

    def test_an_array_compares_as_a_set_and_a_reorder_is_counted_apart(self) -> None:
        from types import SimpleNamespace
        from creib.forge.conformance.dependence import _moved_fields, _reordered_fields
        def fake(output):
            return SimpleNamespace(scoring=SimpleNamespace(parsed_output=output))
        base = fake({"follows": "follows", "essential": ["UED", "K-RECURSION"]})
        self.assertEqual(_moved_fields(fake({"follows": "follows", "essential": ["K-RECURSION", "UED"]}), base, ("follows", "essential")), ())
        self.assertEqual(_reordered_fields(fake({"follows": "follows", "essential": ["K-RECURSION", "UED"]}), base, ("follows", "essential")), ("essential",))
        self.assertEqual(_moved_fields(fake({"follows": "follows", "essential": ["UED"]}), base, ("follows", "essential")), ("essential",))
        self.assertEqual(_reordered_fields(fake({"follows": "follows", "essential": ["UED"]}), base, ("follows", "essential")), ())
        self.assertEqual(_moved_fields(fake({"follows": "not_determined"}), base, ("follows", "essential")), ("follows", "essential"))

    def test_the_dependence_subcommand_writes_the_table(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            markdown = Path(directory) / "dependence.md"
            completed = subprocess.run(
                [sys.executable, str(TOOL), "dependence", "--observations-dir", str(Path(self.directory) / "out"), "--markdown", str(markdown)],
                capture_output=True, text=True, cwd=str(ROOT), env={"PYTHONPATH": str(ROOT / "src"), "PATH": ""},
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            summary = json.loads(completed.stdout.strip().splitlines()[-1])
            self.assertEqual(len(summary["rows"]), 3)
            self.assertIn("## Removals by relation", markdown.read_text(encoding="utf-8"))


class GeneratorTests(unittest.TestCase):
    def test_probes_are_the_argued_sections_and_the_claim_is_the_heading(self) -> None:
        config = _config()
        corpus, extra = generator.build(DOC, config, "T-CORPUS", generator.DEFAULT_LABELS, 2, "0" * 64)
        self.assertEqual([c["case_id"] for c in corpus["cases"]], ["DEP-01"])
        case = corpus["cases"][0]
        self.assertTrue(case["renderings"]["prose"].startswith("Claim under assessment: Recursion is not universality\n\n"))
        self.assertIn("self U02; declared U01, U04", case["notes"])
        self.assertEqual([o["kind"] for o in case["expected"]], ["unknown", "unknown"])
        self.assertEqual(extra["form_schema"]["properties"]["essential"]["items"]["enum"], ["K-REAL", "UED", "Usable"])
        with self.assertRaisesRegex(RecordError, "no section carries an argument label"):
            generator.build(DOC, config, "T", ("Lemma",), 2, "0" * 64)
        with self.assertRaisesRegex(RecordError, "no term the patterns match"):
            generator.build(DOC, _config(term_patterns=["ZZZ"]), "T", generator.DEFAULT_LABELS, 2, "0" * 64)
        ambiguous = DOC.replace("## Gamma", "## Recursion")
        with self.assertRaisesRegex(RecordError, "expected exactly one self unit"):
            generator.build(ambiguous, config, "T", generator.DEFAULT_LABELS, 2, "0" * 64)

    def test_main_reads_the_pilot_configuration_and_writes_both_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "pilot"
            shutil.copytree(PILOT_DIR, target)
            document = Path(directory) / "doc.md"
            document.write_text(DOC, encoding="utf-8")
            raw = loads_strict((target / "pilot.json").read_text(encoding="utf-8"))
            raw["unit_dependence"]["min_occurrences"] = 1
            (target / "pilot.json").write_text(json.dumps(raw, indent=2), encoding="utf-8")
            generator.main(["--document", str(document), "--pilot-dir", str(target), "--corpus-id", "T-CORPUS", "--units-markdown", str(Path(directory) / "units.md")])
            written = loads_strict((target / "corpus.json").read_text(encoding="utf-8"))
            self.assertEqual(written["corpus_id"], "T-CORPUS")
            self.assertIn("| U02 | 2 | Recursion is not universality |", (Path(directory) / "units.md").read_text(encoding="utf-8"))
            loaded = load_pilot_config(target / "pilot.json")
            counts = dict(plan(loaded.spec, load_corpus(loaded.corpus_path, loaded.spec)).counts)
            self.assertEqual(counts["UNIT_DEPENDENCE"], 5)
            raw["unit_dependence"] = None
            del raw["unit_dependence"]
            (target / "pilot.json").write_text(json.dumps(raw, indent=2), encoding="utf-8")
            with self.assertRaisesRegex(RecordError, "no active unit_dependence"):
                generator.main(["--document", str(document), "--pilot-dir", str(target), "--corpus-id", "T"])


if __name__ == "__main__":
    unittest.main()
