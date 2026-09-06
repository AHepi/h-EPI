from __future__ import annotations

import copy
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

from creib.canonical import canonical_bytes
from creib.errors import PolicyViolation, RecordError
from creib.forge.conformance import (
    CONFORMANCE_SCHEMA_DIR,
    LOCUS_VALUES,
    ChatRequest,
    ChatResponse,
    ExpectationKind,
    FakeExecutor,
    Family,
    OllamaChatExecutor,
    ReplayExecutor,
    build_chat_request,
    build_report,
    load_corpus,
    load_observation,
    load_observation_directory,
    load_pilot_config,
    load_run,
    materialize_round_trip,
    plan,
    publish_record,
    render_markdown,
    response_from_content,
    route,
    run_pilot,
    score,
)
from creib.forge.conformance import families as families_module
from creib.forge.conformance.executor import parse_chat_body, redact
from creib.forge.conformance.families import make_variant, variant_from_dict
from creib.forge.conformance.oracle import prerequisite_unavailable
from creib.forge.conformance.common import NON_INDUCTIVE_LIMIT
from creib.forge.schema_validation import load_local_schema_catalog
from creib.strict_json import load_strict, loads_strict


ROOT = Path(__file__).resolve().parents[1]
PILOT_DIR = ROOT / "forge" / "conformance" / "pilots" / "incident-form"
PILOT = PILOT_DIR / "pilot.json"
TOOL = ROOT / "tools" / "run_conformance_pilot.py"
CREATED_ON = "2026-09-05T00:00:00Z"
DUMMY_KEY = "sk-dummy-conformance-key-0123456789"

_CONFIG = load_pilot_config(PILOT)
_CORPUS = load_corpus(_CONFIG.corpus_path, _CONFIG.spec)
_PLAN = plan(_CONFIG.spec, _CORPUS)


def _variant(family: Family, case_id: str, index: int = 0):
    matches = [v for v in _PLAN.variants if v.family is family and v.base_case_id == case_id]
    return matches[index]


def _correct_output(case_id: str) -> dict[str, object]:
    case = _CORPUS.case(case_id)
    output: dict[str, object] = {}
    for oracle in case.expected:
        if oracle.kind == "exact":
            output[oracle.field] = oracle.value
        elif oracle.kind in ("any_of", "enum"):
            output[oracle.field] = (oracle.values or ())[0]
        elif oracle.kind == "regex":
            output[oracle.field] = dict(case.reference_output or ()).get(oracle.field, "wrist pallet")
    return output


def _fake(output_by_case: dict[str, dict[str, object]] | None = None) -> FakeExecutor:
    reference = {case.case_id: _correct_output(case.case_id) for case in _CORPUS.cases}
    if output_by_case:
        reference.update(output_by_case)

    def respond(request: ChatRequest) -> ChatResponse:
        properties = (request.format_schema or {}).get("properties", {})
        for case in _CORPUS.cases:
            if case.renderings[case.rendering] in request.user or any(text in request.user for text in case.renderings.values()):
                output = {k: v for k, v in reference[case.case_id].items() if k in properties}
                return response_from_content(json.dumps(output, ensure_ascii=False))
        output = {k: v for k, v in reference["ORD-001"].items() if k in properties}
        return response_from_content(json.dumps(output, ensure_ascii=False))

    return FakeExecutor(respond)


def _copy_pilot(directory: Path) -> Path:
    target = directory / "pilot"
    shutil.copytree(PILOT_DIR, target)
    return target / "pilot.json"


class SchemaAndVocabularyTests(unittest.TestCase):
    def test_conformance_schemas_load_through_repository_catalog(self) -> None:
        catalog = load_local_schema_catalog(CONFORMANCE_SCHEMA_DIR)
        self.assertEqual(
            catalog.schema_names,
            (
                "conformance-appraisal.schema.json",
                "conformance-claims.schema.json",
                "conformance-corpus.schema.json",
                "conformance-observation.schema.json",
                "conformance-pilot-config.schema.json",
                "conformance-run.schema.json",
            ),
        )
        for name in catalog.schema_names:
            self.assertTrue(catalog.schemas[name]["$id"].startswith("https://ahepi.example/smf/0.5/"))

    def test_no_conformance_schema_leaks_into_pinned_schema_directory(self) -> None:
        self.assertEqual([], [p.name for p in (ROOT / "forge" / "schema").glob("conformance-*")])

    def test_locus_vocabulary_is_the_four_criticism_loci(self) -> None:
        self.assertEqual(frozenset(LOCUS_VALUES), frozenset({"CANDIDATE", "AUXILIARY", "TEST", "SCOPE"}))


class SpecAndCorpusTests(unittest.TestCase):
    def test_bindings_and_obligations(self) -> None:
        spec = _CONFIG.spec
        self.assertEqual([b.path for b in spec.source_bindings], ["pilot.json", "form.schema.json", "instructions.md", "corpus.json"])
        for binding in spec.source_bindings:
            self.assertRegex(binding.sha256, r"^[0-9a-f]{64}$")
        self.assertEqual(len(spec.obligations), 10)
        phone = spec.obligation("phone")
        self.assertTrue(phone.required)
        self.assertEqual(phone.source_sentence_ids, ("S7",))
        self.assertIn("E.164", phone.source_claim or "")
        self.assertFalse(spec.obligation("incident_time").required)
        self.assertFalse(any(o.unsourced for o in spec.obligations))
        self.assertIsNotNone(spec.obligation("incident_date").ambiguity)
        self.assertEqual(spec.charter.non_inductive_constitution, NON_INDUCTIVE_LIMIT)
        self.assertEqual(spec.instructions, (PILOT_DIR / "instructions.md").read_text(encoding="utf-8"))

    def test_corpus_shape_and_pairs(self) -> None:
        self.assertEqual(len(_CORPUS.cases), 14)
        self.assertEqual(len(_CORPUS.boundary_cases), 5)
        self.assertEqual([(a.case_id, b.case_id) for a, b in _CORPUS.pairs()], [("ORD-001", "ORD-001-P"), ("ORD-002", "ORD-002-P"), ("ORD-003", "ORD-003-P")])
        for case in _CORPUS.cases:
            for oracle in case.expected:
                self.assertTrue(oracle.rationale.strip())

    def test_unsourced_obligation_is_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            pilot = _copy_pilot(Path(directory))
            instructions = pilot.parent / "instructions.md"
            lines = instructions.read_text(encoding="utf-8").split("\n")
            kept = [line for line in lines if not line.startswith("8. ")]
            renumbered = []
            counter = 0
            for line in kept:
                if line[:2].rstrip(".").isdigit() or line[:3].rstrip(".").isdigit():
                    counter += 1
                    renumbered.append(f"{counter}. " + line.split(". ", 1)[1])
                else:
                    renumbered.append(line)
            instructions.write_text("\n".join(renumbered), encoding="utf-8")
            config_raw = loads_strict(pilot.read_text(encoding="utf-8"))
            config_raw["load_bearing"] = ["S1", "S5", "S7", "S8"]
            for negation in config_raw["negations"]:
                if negation["field"] == "phone":
                    negation["sentence_id"] = "S7"
            pilot.write_text(json.dumps(config_raw), encoding="utf-8")
            spec = load_pilot_config(pilot).spec
            site = spec.obligation("site")
            self.assertTrue(site.unsourced)
            self.assertIsNone(site.source_claim)

    def test_fail_closed_rejections(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            pilot = _copy_pilot(Path(directory))
            original = pilot.read_text(encoding="utf-8")
            pilot.write_text(original.replace('"pilot_id":', '"title": "dup",\n  "pilot_id":', 1), encoding="utf-8")
            with self.assertRaisesRegex(RecordError, "duplicate JSON key"):
                load_pilot_config(pilot)
            pilot.write_text(original, encoding="utf-8")
            corpus_path = pilot.parent / "corpus.json"
            corpus_original = corpus_path.read_text(encoding="utf-8")
            corpus_path.write_text(corpus_original.replace('"boundary": false', '"boundary": 0.0', 1), encoding="utf-8")
            with self.assertRaisesRegex(RecordError, "floating-point"):
                load_corpus(corpus_path, _CONFIG.spec)
            raw = loads_strict(corpus_original)
            raw["cases"][0]["expected"][0]["field"] = "not_a_field"
            with self.assertRaisesRegex(RecordError, "unknown form field"):
                load_corpus_from_raw = __import__("creib.forge.conformance.corpus", fromlist=["parse_corpus"]).parse_corpus
                load_corpus_from_raw(raw, _CONFIG.spec, sha256="0" * 64)
            raw = loads_strict(corpus_original)
            del raw["cases"][0]["expected"][0]["oracle_status"]
            with self.assertRaisesRegex(RecordError, "oracle_status"):
                load_corpus_from_raw(raw, _CONFIG.spec, sha256="0" * 64)
            raw = loads_strict(corpus_original)
            raw["cases"][0]["expected"] = [o for o in raw["cases"][0]["expected"] if o["field"] != "phone"]
            with self.assertRaisesRegex(RecordError, "required field 'phone' has no oracle"):
                load_corpus_from_raw(raw, _CONFIG.spec, sha256="0" * 64)


class FamilyTests(unittest.TestCase):
    def test_family_counts_and_plan_stability(self) -> None:
        self.assertEqual(
            dict(_PLAN.counts),
            {
                "BASELINE": 9,
                "DELETION": 9,
                "NEGATION": 18,
                "RIVAL_SUBSTITUTION": 2,
                "SEMANTIC_ROLE_TWIN": 9,
                "SUBSTRATE_SWAP": 12,
                "BOUNDARY_SHIFT": 5,
                "IMPORT_DEPENDENCY": 36,
                "NON_VACUITY": 8,
                "ROUND_TRIP": 9,
                "REPEAT": 0,
                "CYCLE": 0,
            },
        )
        again = plan(load_pilot_config(PILOT).spec, load_corpus(_CONFIG.corpus_path, _CONFIG.spec))
        self.assertEqual(again.plan_id, _PLAN.plan_id)
        self.assertEqual([v.variant_id for v in again.variants], [v.variant_id for v in _PLAN.variants])

    def test_deletion_removes_field_and_expects_absence(self) -> None:
        variant = _variant(Family.DELETION, "ORD-001")
        self.assertNotIn("incident_time", variant.form_schema["properties"])
        self.assertNotIn("incident_time", variant.field_order)
        self.assertNotIn("incident_time", variant.instructions)
        self.assertEqual(variant.oracle("incident_time").kind, "absent")

    def test_negation_swaps_sentence_pattern_and_oracle(self) -> None:
        variant = _variant(Family.NEGATION, "ORD-001", 0)
        self.assertEqual(variant.form_schema["properties"]["incident_date"]["pattern"], "^[0-9]{2}/[0-9]{2}/[0-9]{4}$")
        self.assertIn("DD/MM/YYYY", variant.instructions)
        self.assertEqual(variant.oracle("incident_date").value, "03/04/2025")
        phone_variant = _variant(Family.NEGATION, "ORD-002", 1)
        self.assertEqual(phone_variant.oracle("phone").value, "02 9876 5432")
        self.assertEqual(_variant(Family.NEGATION, "ORD-001", 1).oracle("phone").value, "0412 345 678")

    def test_rival_substitution_appends_rule_and_follows_it(self) -> None:
        variants = [v for v in _PLAN.variants if v.family is Family.RIVAL_SUBSTITUTION]
        self.assertEqual({v.rival_label for v in variants}, {"day_first", "month_first"})
        for variant in variants:
            self.assertTrue(variant.instructions.rstrip("\n").endswith("convention)."))
            self.assertEqual(variant.oracle("incident_date").kind, "exact")

    def test_semantic_role_twin_swaps_positions_only(self) -> None:
        baseline = _variant(Family.BASELINE, "ORD-002")
        twin = _variant(Family.SEMANTIC_ROLE_TWIN, "ORD-002")
        self.assertEqual(twin.field_order[:2], ("subject_name", "reporter_name"))
        self.assertEqual([o.to_dict() for o in twin.expected], [o.to_dict() for o in baseline.expected])
        second = next(line for line in twin.instructions.split("\n") if line.startswith("2. "))
        self.assertTrue(second.startswith("2. `subject_name`"), second)

    def test_substrate_swap_boundary_import_and_round_trip_shapes(self) -> None:
        case = _CORPUS.case("ORD-001")
        swaps = [v for v in _PLAN.variants if v.family is Family.SUBSTRATE_SWAP and v.base_case_id == "ORD-001"]
        self.assertEqual({v.substrate for v in swaps}, {"table", "email"})
        for swap in swaps:
            self.assertEqual(swap.input_document, case.renderings[swap.substrate])
            self.assertEqual([o.to_dict() for o in swap.expected], [o.to_dict() for o in case.expected])
        boundary = [v for v in _PLAN.variants if v.family is Family.BOUNDARY_SHIFT]
        self.assertEqual({v.base_case_id for v in boundary}, {"BND-001", "BND-002", "BND-003", "BND-004", "BND-005"})
        imports = [v for v in _PLAN.variants if v.family is Family.IMPORT_DEPENDENCY and v.base_case_id == "ORD-001"]
        self.assertEqual({v.removed_sentence_id for v in imports}, {"S1", "S5", "S7", "S9"})
        for variant in imports:
            self.assertIs(variant.expectation_kind, ExpectationKind.RECORD_DEPENDENCE)
            self.assertNotIn(_CONFIG.spec.sentence(variant.removed_sentence_id).text, variant.instructions)
        planned = _variant(Family.ROUND_TRIP, "ORD-001")
        self.assertIsNone(planned.input_document)
        self.assertEqual(planned.round_trip_of, _variant(Family.BASELINE, "ORD-001").variant_id)
        materialised = materialize_round_trip(planned, _correct_output("ORD-001"))
        self.assertIn("Reporter name: Alice Nguyen", materialised.input_document or "")
        self.assertEqual(materialised.oracle("phone").value, "+61412345678")
        self.assertEqual(materialised.oracle("phone").oracle_status, "project_import_provisional")

    def test_non_vacuity_controls_are_model_free(self) -> None:
        controls = [v for v in _PLAN.variants if v.family is Family.NON_VACUITY]
        self.assertEqual(len(controls), 8)
        self.assertTrue(all(not v.model_call and v.control_output is not None for v in controls))

    def test_variant_record_round_trip_and_tamper_detection(self) -> None:
        variant = _variant(Family.NEGATION, "ORD-001")
        rebuilt = variant_from_dict(loads_strict(canonical_bytes(variant.to_dict()).decode("utf-8")))
        self.assertEqual(rebuilt.variant_id, variant.variant_id)
        tampered = variant.to_dict()
        tampered["held_fixed"] = "something else"
        with self.assertRaisesRegex(RecordError, "variant_id does not replay"):
            variant_from_dict(tampered)


class OracleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.variant = _variant(Family.BASELINE, "ORD-001")
        self.output = _correct_output("ORD-001")
        self.phrases = _CONFIG.spec.refusal_phrases

    def _score(self, content: str, **kwargs):
        return score(self.variant, response_from_content(content, **kwargs), refusal_phrases=self.phrases)

    def test_response_level_verdicts(self) -> None:
        good = self._score(json.dumps(self.output))
        self.assertEqual(good.response_verdict, "JSON_OBJECT")
        self.assertTrue(good.schema_valid)
        self.assertTrue(all(v.verdict == "MATCH" for v in good.field_verdicts))
        error = ChatResponse("", False, False, None, None, None, None, None, "URLError: unreachable", "0" * 64)
        self.assertEqual(score(self.variant, error).response_verdict, "TRANSPORT_ERROR")
        self.assertEqual(self._score("   ").response_verdict, "EMPTY_RESPONSE")
        self.assertEqual(self._score('{"reporter_name": "Ali', done_reason="length").response_verdict, "TRUNCATED")
        self.assertEqual(self._score("this is not json at all").response_verdict, "INVALID_JSON")
        self.assertEqual(self._score("[1, 2, 3]").response_verdict, "NOT_AN_OBJECT")
        self.assertEqual(self._score("I'm sorry, I cannot help with that request.").response_verdict, "REFUSAL_SUSPECTED")
        # H22: the first live refusal was written with typographic apostrophes and slipped past the list.
        curly = self._score("I\u2019m sorry, but I can\u2019t comply with that.")
        self.assertEqual(curly.response_verdict, "REFUSAL_SUSPECTED")
        self.assertIn("matched refusal phrase", curly.response_detail or "")
        self.assertEqual(self._score("I\u2019m not able to comply with that.").response_verdict, "INVALID_JSON", "a phrase outside the list is still not a refusal to this heuristic")
        floaty = self._score('{"reporter_name": 1.5}')
        self.assertEqual(floaty.response_verdict, "INVALID_JSON")
        self.assertIn("floating-point", floaty.response_detail or "")

    def test_recovery_from_prose_is_labelled_project_import(self) -> None:
        recovered = self._score("Here is the form:\n```json\n" + json.dumps(self.output) + "\n```\nDone.")
        self.assertEqual(recovered.response_verdict, "JSON_OBJECT")
        self.assertTrue(recovered.recovered_from_prose)
        self.assertEqual(recovered.recovery_status, "project_import_provisional")
        self.assertTrue(all(v.verdict == "MATCH" for v in recovered.field_verdicts))

    def test_field_level_verdicts(self) -> None:
        def verdict_of(mutation: dict[str, object], drop: tuple[str, ...] = ()) -> dict[str, str]:
            output = {**self.output, **mutation}
            for key in drop:
                output.pop(key, None)
            scoring = self._score(json.dumps(output, ensure_ascii=False))
            return {v.field: v.verdict for v in scoring.field_verdicts}

        self.assertEqual(verdict_of({"reporter_name": "Someone Else"})["reporter_name"], "MISMATCH")
        self.assertEqual(verdict_of({}, drop=("phone",))["phone"], "MISSING_REQUIRED")
        self.assertEqual(verdict_of({"notes": "x"})["notes"], "EXTRA_FIELD")
        self.assertEqual(verdict_of({"injury_reported": "yes"})["injury_reported"], "TYPE_VIOLATION")
        self.assertEqual(verdict_of({"phone": "0412 345 678"})["phone"], "PATTERN_VIOLATION")
        self.assertEqual(verdict_of({"severity": "critical"})["severity"], "ENUM_VIOLATION")
        self.assertEqual(verdict_of({"summary": "wrist " * 50})["summary"], "LENGTH_VIOLATION")
        absent_case = _variant(Family.BASELINE, "ORD-002")
        with_time = {**_correct_output("ORD-002"), "incident_time": "10:00"}
        verdicts = {v.field: v.verdict for v in score(absent_case, response_from_content(json.dumps(with_time))).field_verdicts}
        self.assertEqual(verdicts["incident_time"], "UNEXPECTED_PRESENT")
        dependence = _variant(Family.IMPORT_DEPENDENCY, "ORD-001")
        scoring = score(dependence, response_from_content(json.dumps(self.output)), baseline_output=self.output)
        self.assertTrue(all(v.verdict == "NOT_SCORED" for v in scoring.field_verdicts))
        self.assertIs(scoring.changed_vs_baseline, False)
        changed = score(dependence, response_from_content(json.dumps({**self.output, "site": "elsewhere"})), baseline_output=self.output)
        self.assertIs(changed.changed_vs_baseline, True)


class RoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.output = _correct_output("ORD-001")

    def _route(self, variant, content: str, baseline=None, **kwargs):
        scoring = score(variant, response_from_content(content, **kwargs), refusal_phrases=_CONFIG.spec.refusal_phrases, baseline_output=baseline)
        return route(variant, scoring)

    def test_full_match_is_the_only_empty_set_and_is_not_confirmation(self) -> None:
        routing = self._route(_variant(Family.BASELINE, "ORD-001"), json.dumps(self.output))
        self.assertEqual(routing.live_loci, ())
        self.assertTrue(routing.unrefuted_for_variant)
        self.assertEqual(routing.route, "AWAITING_HUMAN_TRIAGE")

    def test_model_involved_routes_are_never_single_locus(self) -> None:
        cases = [
            (Family.BASELINE, json.dumps({**self.output, "reporter_name": "X"}), {"CANDIDATE", "TEST"}),
            (Family.BASELINE, "garbage", {"CANDIDATE", "AUXILIARY"}),
            (Family.BASELINE, "", {"CANDIDATE", "AUXILIARY"}),
            (Family.BASELINE, json.dumps({**self.output, "notes": "x"}), {"CANDIDATE", "AUXILIARY", "TEST"}),
            (Family.SEMANTIC_ROLE_TWIN, json.dumps({**self.output, "reporter_name": "Tom Baker", "subject_name": "Alice Nguyen"}), {"CANDIDATE", "TEST"}),
            (Family.SUBSTRATE_SWAP, json.dumps({**self.output, "site": "Dock"}), {"CANDIDATE", "SCOPE", "TEST"}),
            (Family.DELETION, json.dumps(self.output), {"CANDIDATE", "TEST"}),
            (Family.RIVAL_SUBSTITUTION, None, {"CANDIDATE", "AUXILIARY", "TEST"}),
        ]
        for family, content, expected in cases:
            with self.subTest(family=family.value, content=content[:20] if content else None):
                if family is Family.RIVAL_SUBSTITUTION:
                    variant = [v for v in _PLAN.variants if v.family is family][0]
                    content = json.dumps({**_correct_output("BND-004"), "incident_date": "2025-12-25"})
                else:
                    variant = _variant(family, "ORD-001")
                routing = self._route(variant, content)
                self.assertGreaterEqual(len(routing.live_loci), 2)
                self.assertEqual(set(routing.loci), expected)
                self.assertFalse(routing.unrefuted_for_variant)
                for locus in routing.live_loci:
                    self.assertTrue(locus.reason.endswith("."))
        transport = route(_variant(Family.BASELINE, "ORD-001"), score(_variant(Family.BASELINE, "ORD-001"), ChatResponse("", False, False, None, None, None, None, 503, "HTTPError: status 503", "0" * 64)))
        self.assertEqual(set(transport.loci), {"AUXILIARY", "SCOPE"})
        boundary = self._route(_variant(Family.BOUNDARY_SHIFT, "BND-001"), json.dumps({**_correct_output("BND-001"), "phone": ""}))
        self.assertEqual(set(boundary.loci), {"CANDIDATE", "TEST", "SCOPE"})
        prerequisite = route(_variant(Family.ROUND_TRIP, "ORD-001"), prerequisite_unavailable("baseline unusable"))
        self.assertEqual(set(prerequisite.loci), {"AUXILIARY", "TEST"})

    def test_negation_identical_to_baseline_routes_three_loci(self) -> None:
        variant = _variant(Family.NEGATION, "ORD-001")
        routing = self._route(variant, json.dumps(self.output), baseline=self.output)
        self.assertIn("IDENTICAL_TO_BASELINE", routing.triggers)
        self.assertEqual(set(routing.loci), {"CANDIDATE", "AUXILIARY", "SCOPE"})

    def test_format_not_enforced_is_recorded(self) -> None:
        routing = self._route(_variant(Family.BASELINE, "ORD-001"), json.dumps({**self.output, "notes": "x"}))
        self.assertIn("FORMAT_NOT_ENFORCED", routing.triggers)
        self.assertIs(routing.format_enforced_by_server, False)

    def test_import_dependency_records_dependence_plurally(self) -> None:
        variant = _variant(Family.IMPORT_DEPENDENCY, "ORD-001")
        unchanged = self._route(variant, json.dumps(self.output), baseline=self.output)
        self.assertEqual(unchanged.triggers, ("DEPENDENCE_UNCHANGED",))
        self.assertEqual(set(unchanged.loci), {"AUXILIARY", "TEST", "SCOPE"})
        changed = self._route(variant, json.dumps({**self.output, "site": "x"}), baseline=self.output)
        self.assertEqual(changed.triggers, ("DEPENDENCE_CHANGED",))
        self.assertEqual(set(changed.loci), {"AUXILIARY", "SCOPE"})

    def test_non_vacuity_controls(self) -> None:
        for control in [v for v in _PLAN.variants if v.family is Family.NON_VACUITY]:
            routing = route(control, score(control, None), format_sent=False)
            self.assertEqual(routing.live_loci, (), control.control_id)
            self.assertTrue(routing.unrefuted_for_variant)
        accepted = [v for v in _PLAN.variants if v.family is Family.NON_VACUITY and v.control_id == "C-SWAP-DATES"][0]
        undetectable = make_variant(**{**{k: getattr(accepted, k) for k in accepted.__dataclass_fields__ if k != "variant_id"}, "control_output": tuple(_correct_output("ORD-001").items())})
        routing = route(undetectable, score(undetectable, None), format_sent=False)
        self.assertEqual(routing.triggers, ("CONTROL_ACCEPTED",))
        self.assertEqual(set(routing.loci), {"TEST", "AUXILIARY"})
        correct = [v for v in _PLAN.variants if v.family is Family.NON_VACUITY and v.control_id == "C-CORRECT"][0]
        rejected = make_variant(**{**{k: getattr(correct, k) for k in correct.__dataclass_fields__ if k != "variant_id"}, "control_output": tuple({**_correct_output("ORD-001"), "site": "wrong"}.items())})
        routing = route(rejected, score(rejected, None), format_sent=False)
        self.assertEqual(routing.triggers, ("CONTROL_REJECTED",))
        self.assertEqual(routing.loci, ("TEST",))


class RecordsAndRunnerTests(unittest.TestCase):
    def _run(self, directory: Path, executor, executor_kind: str, families=(Family.BASELINE, Family.NEGATION, Family.NON_VACUITY, Family.ROUND_TRIP, Family.IMPORT_DEPENDENCY), limit=None):
        return run_pilot(
            spec=_CONFIG.spec,
            corpus=_CORPUS,
            plan=_PLAN,
            model="gpt-oss:20b",
            executor=executor,
            executor_kind=executor_kind,
            output_dir=directory,
            created_on=CREATED_ON,
            families=families,
            limit=limit,
        )

    def test_records_are_content_addressed_no_clobber_and_tamper_evident(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            result = self._run(out, _fake(), "fake", families=(Family.BASELINE, Family.NEGATION, Family.NON_VACUITY, Family.ROUND_TRIP))
            self.assertEqual(result.run_record.overall_status, "UNRESOLVED")
            self.assertEqual(result.run_record.route, "AWAITING_HUMAN_TRIAGE")
            self.assertEqual(result.run_record.epistemic_limit, NON_INDUCTIVE_LIMIT)
            self.assertIn(result.run_record.scope_label, ("REFUTED_CASES_PRESENT", "UNREFUTED_FOR_DECLARED_SCOPE"))
            first = result.observation_paths[0]
            loaded = load_observation(first)
            self.assertEqual(loaded.observation_id, result.observations[0].observation_id)
            self.assertEqual(load_run(result.run_path).run_id, result.run_record.run_id)
            with self.assertRaisesRegex(RecordError, "exists"):
                publish_record(result.observations[0], out)
            raw = first.read_bytes()
            tampered = raw.replace(b'"model":"gpt-oss:20b"', b'"model":"gpt-oss:20c"')
            self.assertNotEqual(raw, tampered)
            (out / "tampered.json").write_bytes(tampered)
            with self.assertRaises(RecordError):
                load_observation(out / "tampered.json")
            for path in result.observation_paths:
                text = path.read_text(encoding="utf-8")
                self.assertTrue(text.endswith("\n"))
            round_trips = [o for o in result.observations if o.variant.family is Family.ROUND_TRIP]
            self.assertTrue(round_trips)
            self.assertNotEqual(round_trips[0].variant.variant_id, round_trips[0].planned_variant_id)
            self.assertIsNotNone(round_trips[0].variant.input_document)
            unresolved_negation = [o for o in result.observations if o.variant.family is Family.NEGATION]
            self.assertTrue(all("IDENTICAL_TO_BASELINE" in o.routing.triggers or o.scoring.changed_vs_baseline for o in unresolved_negation))

    def test_replay_executor_reproduces_scoring(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first"
            second = Path(directory) / "second"
            recorded = self._run(first, _fake(), "fake", limit=10)
            replayed = self._run(second, ReplayExecutor(first), "replay", limit=10)
            by_planned = {o.planned_variant_id: o for o in recorded.observations}
            self.assertEqual(len(recorded.observations), len(replayed.observations))
            for observation in replayed.observations:
                original = by_planned[observation.planned_variant_id]
                self.assertEqual(observation.scoring.to_dict(), original.scoring.to_dict())
                self.assertEqual(observation.routing.to_dict(), original.routing.to_dict())
                self.assertEqual(observation.request_digest, original.request_digest)
            self.assertEqual(len(load_observation_directory(first)), len(recorded.observations))

    def test_report_has_no_ranking_and_ends_with_the_limit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = self._run(Path(directory), _fake({"ORD-001": {**_correct_output("ORD-001"), "site": "Dock"}}), "fake", families=(Family.BASELINE, Family.NON_VACUITY))
            report = build_report([result.run_record], result.observations)
            self.assertEqual(report["epistemic_limit"], NON_INDUCTIVE_LIMIT)
            self.assertEqual(report["overall_status"], "UNRESOLVED")
            modes = report["runs"][0]["failure_modes"]
            self.assertTrue(any(m["trigger"] == "MISMATCH" and m["example_case_id"] == "ORD-001" for m in modes))
            markdown = render_markdown(report)
            self.assertTrue(markdown.rstrip("\n").endswith(NON_INDUCTIVE_LIMIT))
            for word in ("best", "rank", "score"):
                self.assertNotIn(word, markdown.lower().replace("scope", ""))


class RecordVersionTests(unittest.TestCase):
    """Records name their schema version; a record from an earlier version is refused by name, not by a missing key."""

    def test_v1_records_are_refused_by_version(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            result = run_pilot(
                spec=_CONFIG.spec, corpus=_CORPUS, plan=_PLAN, model="gpt-oss:20b", executor=_fake(), executor_kind="fake",
                output_dir=out, created_on=CREATED_ON, families=(Family.BASELINE,), limit=1,
            )
            observation_path = out / f"observation.{result.observations[0].observation_id[:16]}.json"
            self.assertTrue(observation_path.exists())
            for path in (observation_path, out / f"run.{result.run_record.run_id[:16]}.json"):
                record = load_strict(path)
                self.assertTrue(str(record["schema_version"]).endswith(".v2"))
                record["schema_version"] = str(record["schema_version"]).replace(".v2", ".v1")
                old = out / ("old-" + path.name)
                old.write_bytes(canonical_bytes(record) + b"\n")
                loader = load_observation if path.name.startswith("observation.") else load_run
                with self.assertRaisesRegex(RecordError, r"schema_version 'creib\.conformance-pilot\.(observation|run)\.v1'"):
                    loader(old)
                with self.assertRaisesRegex(RecordError, "unknown conformance record schema_version"):
                    publish_record(record, out)


class AccountingTests(unittest.TestCase):
    """What was loaded plus what was refused equals what was there; a check that cannot fail is named as such (H19, H20)."""

    LEAVE = ROOT / "forge" / "conformance" / "runs" / "leave-request"

    def test_records_directory_is_enumerated_and_anything_else_is_refused_by_name(self) -> None:
        from creib.forge.conformance.records import enumerate_record_directory
        with tempfile.TemporaryDirectory() as temporary:
            copy = Path(temporary) / "records"
            shutil.copytree(self.LEAVE, copy)
            listing = enumerate_record_directory(copy)
            self.assertEqual(len(listing.observation_paths), 24)
            self.assertEqual(len(listing.run_paths), 6)
            self.assertEqual(listing.entries, len(list(copy.iterdir())))
            self.assertEqual(len(load_observation_directory(copy)), 24)
            stray = copy / "notes.md"
            stray.write_text("scratch\n")
            with self.assertRaisesRegex(RecordError, "not a record: notes.md"):
                load_observation_directory(copy)
            stray.unlink()
            (copy / "more").mkdir()
            with self.assertRaisesRegex(RecordError, "not a record file: more"):
                load_observation_directory(copy)
            (copy / "more").rmdir()
            link = copy / "observation.0000000000000000.json"
            link.symlink_to(listing.observation_paths[0].name)
            with self.assertRaisesRegex(RecordError, "symlink"):
                load_observation_directory(copy)
            link.unlink()
            self.assertEqual(len(load_observation_directory(copy)), 24)

    def test_record_file_name_must_carry_the_id_of_the_record_it_holds(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copy = Path(temporary) / "records"
            shutil.copytree(self.LEAVE, copy)
            observation = sorted(copy.glob("observation.*.json"))[0]
            run = sorted(copy.glob("run.*.json"))[0]
            moved = copy / "observation.ffffffffffffffff.json"
            observation.rename(moved)
            with self.assertRaisesRegex(RecordError, "named for a different record"):
                load_observation(moved)
            with self.assertRaisesRegex(RecordError, "named for a different record"):
                load_observation_directory(copy)
            moved.rename(observation)
            wrong_run = copy / "run.ffffffffffffffff.json"
            run.rename(wrong_run)
            with self.assertRaisesRegex(RecordError, "named for a different record"):
                load_run(wrong_run)
            # a record under any other name is still readable by its own id
            elsewhere = Path(temporary) / "kept.json"
            elsewhere.write_bytes(wrong_run.read_bytes())
            self.assertEqual(load_run(elsewhere).run_id, load_strict(elsewhere)["run_id"])

    def test_a_control_whose_corruption_changes_nothing_is_refused_at_plan_time(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copy = Path(temporary) / "pilot"
            shutil.copytree(PILOT.parent, copy)
            corpus_path = copy / "corpus.json"
            raw = load_strict(corpus_path)
            case = next(c for c in raw["cases"] if c["case_id"] == "ORD-001")
            values = {item["field"]: item["value"] for item in case["reference_output"]}
            for item in case["reference_output"]:
                if item["field"] == "incident_date":
                    item["value"] = values["date_of_birth"]
            corpus_path.write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")
            config = load_pilot_config(copy / "pilot.json")
            corpus = load_corpus(config.corpus_path, config.spec)
            with self.assertRaisesRegex(RecordError, "control C-SWAP-DATES is vacuous on ORD-001"):
                plan(config.spec, corpus)


class SecrecyTests(unittest.TestCase):
    def test_key_never_reaches_records_or_errors(self) -> None:
        executor = OllamaChatExecutor(base_url="https://ollama.example", timeout_seconds=5, retries=1)
        self.assertNotIn(DUMMY_KEY, repr(executor))
        request = ChatRequest("gpt-oss:20b", "sys", "user", None, {"temperature": 0, "seed": 7}, False)
        self.assertNotIn("Authorization", json.dumps(request.to_dict()))
        with patch.dict(os.environ, {"OLLAMA_API_KEY": ""}):
            with self.assertRaisesRegex(RecordError, "OLLAMA_API_KEY is not set"):
                executor.complete(request)
        body = json.dumps({"error": f"bad Authorization header: Bearer {DUMMY_KEY}"}).encode("utf-8")

        def failing_urlopen(http_request, timeout):
            self.assertEqual(http_request.get_header("Authorization"), "Bearer " + DUMMY_KEY)
            raise urllib.error.HTTPError(http_request.full_url, 401, "Unauthorized", {}, io.BytesIO(body))

        with patch.dict(os.environ, {"OLLAMA_API_KEY": DUMMY_KEY}), patch("urllib.request.urlopen", failing_urlopen):
            response = executor.complete(request)
        self.assertEqual(response.http_status, 401)
        self.assertEqual(len(response.prior_attempts), 1)
        serialised = json.dumps(response.to_dict())
        for forbidden in (DUMMY_KEY, "Authorization", "Bearer"):
            self.assertNotIn(forbidden, serialised)
        variant = _variant(Family.BASELINE, "ORD-001")
        scoring = score(variant, response)
        self.assertEqual(scoring.response_verdict, "TRANSPORT_ERROR")
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"OLLAMA_API_KEY": DUMMY_KEY}):
            result = run_pilot(
                spec=_CONFIG.spec, corpus=_CORPUS, plan=_PLAN, model="gpt-oss:20b",
                executor=FakeExecutor(lambda req: response), executor_kind="fake",
                output_dir=Path(directory), created_on=CREATED_ON, families=(Family.BASELINE,), limit=2,
            )
            for path in (*result.observation_paths, result.run_path):
                text = path.read_text(encoding="utf-8")
                for forbidden in (DUMMY_KEY, "Authorization", "Bearer"):
                    self.assertNotIn(forbidden, text)
            self.assertEqual(result.run_record.transport_error_count, 2)
            # A run made entirely of transport errors has scored nothing; it is neither refuted nor unrefuted.
            self.assertEqual(result.run_record.scope_label, "INCONCLUSIVE_NO_SCORED_OUTPUT")

    def test_redaction_and_float_duration_conversion(self) -> None:
        self.assertEqual(redact(f"token {DUMMY_KEY} Authorization: Bearer abc", DUMMY_KEY), "token [REDACTED] [REDACTED_HEADER]: [REDACTED_AUTH]")
        body = json.dumps({"message": {"content": "{}", "thinking": "hmm"}, "done": True, "done_reason": "stop", "total_duration": 12.0, "eval_count": 3}).encode("utf-8")
        response = parse_chat_body(body, http_status=200, attempt=1, secret=None)
        self.assertEqual(response.total_duration_ns, 12)
        self.assertTrue(response.thinking_present)
        canonical_bytes(response.to_dict())


class CLITests(unittest.TestCase):
    def _run(self, *arguments: str) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(ROOT / "src")
        result = subprocess.run([sys.executable, str(TOOL), *arguments], cwd=ROOT, env=environment, check=False, capture_output=True, text=True)
        return result, json.loads(result.stdout)

    def test_plan_command(self) -> None:
        result, report = self._run("plan", "--pilot", str(PILOT))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["plan_id"], _PLAN.plan_id)
        self.assertEqual(report["counts"]["NON_VACUITY"], 8)

    def test_run_dry_run_command(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result, report = self._run(
                "run", "--pilot", str(PILOT), "--model", "gpt-oss:20b", "--family", "BASELINE", "--family", "NON_VACUITY",
                "--limit", "6", "--output-dir", directory, "--created-on", CREATED_ON, "--dry-run",
            )
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertTrue(Path(report["run_record_path"]).exists())
            self.assertEqual(report["overall_status"], "UNRESOLVED")
            self.assertEqual(report["epistemic_limit"], NON_INDUCTIVE_LIMIT)
            self.assertGreater(report["observations_with_live_loci"], 0)


if __name__ == "__main__":
    unittest.main()


class RobustnessRegressionTests(unittest.TestCase):
    """Defects found by review after the first live runs; each was confirmed against the code."""

    def setUp(self) -> None:
        self.baseline = _variant(Family.BASELINE, "ORD-001")
        self.output = _correct_output("ORD-001")
        self.phrases = _CONFIG.spec.refusal_phrases

    def _score(self, content: str, variant=None, **kwargs):
        return score(variant or self.baseline, response_from_content(content), refusal_phrases=self.phrases, **kwargs)

    def test_http_client_exceptions_become_transport_errors(self) -> None:
        import http.client

        executor = OllamaChatExecutor(base_url="https://example.invalid", timeout_seconds=1)
        request = build_chat_request(self.baseline, model="gpt-oss:20b", endpoint=_CONFIG.spec.endpoint)
        for exc in (http.client.IncompleteRead(b"partial"), http.client.BadStatusLine("garbage"), http.client.RemoteDisconnected("gone")):
            with patch.dict(os.environ, {"OLLAMA_API_KEY": DUMMY_KEY}), patch("urllib.request.urlopen", side_effect=exc):
                response = executor.complete(request)
            self.assertIsNotNone(response.transport_error, type(exc).__name__)
            self.assertEqual(score(self.baseline, response).response_verdict, "TRANSPORT_ERROR")

    def test_oversized_integer_literal_is_invalid_json_not_a_crash(self) -> None:
        scoring = self._score('{"reporter_name": ' + "9" * 5000 + "}")
        self.assertEqual(scoring.response_verdict, "INVALID_JSON")

    def test_json_after_reasoning_prose_is_recovered(self) -> None:
        prose = "Let me work through the fields. Dates like {day}/{month} are day-first here.\n\nFinal answer:\n" + json.dumps(self.output, indent=2) + "\n"
        scoring = self._score(prose)
        self.assertEqual(scoring.response_verdict, "JSON_OBJECT")
        self.assertTrue(scoring.recovered_from_prose)
        self.assertTrue(all(v.verdict == "MATCH" for v in scoring.field_verdicts))
        trailing = json.dumps(self.output) + "\nNote: the summary is {short}."
        self.assertEqual(self._score(trailing).response_verdict, "JSON_OBJECT")

    def test_empty_done_reason_and_non_numeric_counters_do_not_abort(self) -> None:
        body = json.dumps({"message": {"content": json.dumps(self.output)}, "done": True, "done_reason": "", "eval_count": "many", "total_duration": True}).encode()
        response = parse_chat_body(body, http_status=200, attempt=1, secret=DUMMY_KEY)
        self.assertIsNone(response.done_reason)
        self.assertIsNone(response.eval_count)
        self.assertIsNone(response.total_duration_ns)
        self.assertIsNone(response.transport_error)

    def test_model_content_is_not_rewritten_for_ordinary_words(self) -> None:
        body = json.dumps({"message": {"content": json.dumps({**self.output, "summary": "Bearer of bad news at the authorization desk"})}, "done": True, "done_reason": "stop"}).encode()
        response = parse_chat_body(body, http_status=200, attempt=1, secret=DUMMY_KEY)
        self.assertIn("Bearer of bad news at the authorization desk", response.content)
        leaked = json.dumps({"message": {"content": "key " + DUMMY_KEY}, "done": True, "done_reason": "stop"}).encode()
        self.assertNotIn(DUMMY_KEY, parse_chat_body(leaked, http_status=200, attempt=1, secret=DUMMY_KEY).content)

    def test_whitespace_content_and_empty_key_round_trip_through_publication(self) -> None:
        def respond(request: ChatRequest) -> ChatResponse:
            if "ORD-001" in request.user or "Alice" in request.user:
                return response_from_content("   ")
            return response_from_content(json.dumps({**self.output, "": "stray"}))

        with tempfile.TemporaryDirectory() as directory:
            result = run_pilot(
                spec=_CONFIG.spec, corpus=_CORPUS, plan=_PLAN, model="gpt-oss:20b",
                executor=FakeExecutor(respond), executor_kind="fake",
                output_dir=Path(directory), created_on=CREATED_ON, families=(Family.BASELINE,), limit=3,
            )
            verdicts = {o.scoring.response_verdict for o in result.observations}
            self.assertIn("EMPTY_RESPONSE", verdicts)
            reloaded = load_observation_directory(Path(directory))
            self.assertEqual(len(reloaded), len(result.observations))
            self.assertEqual(load_run(result.run_path).run_id, result.run_record.run_id)

    def test_scope_label_is_inconclusive_when_nothing_was_scored(self) -> None:
        error = ChatResponse("", False, False, None, None, None, None, None, "URLError: unreachable", "0" * 64)
        with tempfile.TemporaryDirectory() as directory:
            result = run_pilot(
                spec=_CONFIG.spec, corpus=_CORPUS, plan=_PLAN, model="gpt-oss:20b",
                executor=FakeExecutor(lambda req: error), executor_kind="fake",
                output_dir=Path(directory), created_on=CREATED_ON, families=(Family.BASELINE,), limit=2,
            )
        self.assertEqual(result.run_record.scope_label, "INCONCLUSIVE_NO_SCORED_OUTPUT")
        self.assertNotIn("CANDIDATE", {locus for o in result.observations for locus in o.routing.loci})

    def test_negation_without_usable_baseline_routes_somewhere(self) -> None:
        variant = _variant(Family.NEGATION, "ORD-001")
        scoring = score(variant, response_from_content(json.dumps(self.output)), refusal_phrases=self.phrases, baseline_output=None)
        routing = route(variant, scoring)
        self.assertIn("PREREQUISITE_UNAVAILABLE", routing.triggers)
        self.assertTrue(routing.live_loci)

    def test_reemitted_deleted_key_proves_format_not_enforced(self) -> None:
        variant = _variant(Family.DELETION, "ORD-001")
        deleted = [f for f in self.output if f not in variant.field_order]
        self.assertTrue(deleted)
        scoring = score(variant, response_from_content(json.dumps(self.output)), refusal_phrases=self.phrases)
        routing = route(variant, scoring, format_sent=True)
        self.assertIn("UNEXPECTED_PRESENT", routing.triggers)
        self.assertIn("FORMAT_NOT_ENFORCED", routing.triggers)
        self.assertIs(routing.format_enforced_by_server, False)


class SecondReviewRegressionTests(unittest.TestCase):
    """Findings on which several independent reviewers agreed, confirmed by reading the code."""

    def setUp(self) -> None:
        self.baseline = _variant(Family.BASELINE, "ORD-001")
        self.output = _correct_output("ORD-001")

    def test_http_error_whose_body_read_raises_is_still_a_transport_error(self) -> None:
        import http.client

        class BrokenHTTPError(urllib.error.HTTPError):
            def read(self, *args, **kwargs):  # noqa: D401 - test double
                raise http.client.IncompleteRead(b"half")

        error = BrokenHTTPError("https://example.invalid/api/chat", 502, "Bad Gateway", {}, None)
        executor = OllamaChatExecutor(base_url="https://example.invalid", timeout_seconds=1)
        request = build_chat_request(self.baseline, model="gpt-oss:20b", endpoint=_CONFIG.spec.endpoint)
        with patch.dict(os.environ, {"OLLAMA_API_KEY": DUMMY_KEY}), patch("urllib.request.urlopen", side_effect=error):
            response = executor.complete(request)
        self.assertEqual(response.http_status, 502)
        self.assertIn("HTTPError", response.transport_error or "")
        self.assertEqual(score(self.baseline, response).response_verdict, "TRANSPORT_ERROR")

    def test_executor_that_raises_becomes_a_recorded_transport_error_not_an_aborted_run(self) -> None:
        class Exploding:
            def complete(self, request: ChatRequest) -> ChatResponse:
                raise RuntimeError("secret-looking text " + DUMMY_KEY)

        with tempfile.TemporaryDirectory() as directory:
            result = run_pilot(
                spec=_CONFIG.spec, corpus=_CORPUS, plan=_PLAN, model="gpt-oss:20b",
                executor=Exploding(), executor_kind="fake",
                output_dir=Path(directory), created_on=CREATED_ON, families=(Family.BASELINE,), limit=2,
            )
            errors = [o for o in result.observations if o.scoring.response_verdict == "TRANSPORT_ERROR"]
            self.assertEqual(len(errors), 2)
            self.assertTrue(all(o.response.transport_error == "ExecutorException: RuntimeError" for o in errors))
            self.assertEqual(result.run_record.scope_label, "INCONCLUSIVE_NO_SCORED_OUTPUT")
            for path in (*result.observation_paths, result.run_path):
                self.assertNotIn(DUMMY_KEY, path.read_text(encoding="utf-8"))

    def test_missing_api_key_still_aborts_before_any_call(self) -> None:
        executor = OllamaChatExecutor(base_url="https://example.invalid", timeout_seconds=1)
        request = build_chat_request(self.baseline, model="gpt-oss:20b", endpoint=_CONFIG.spec.endpoint)
        env = {k: v for k, v in os.environ.items() if k != "OLLAMA_API_KEY"}
        with patch.dict(os.environ, env, clear=True), self.assertRaises(RecordError):
            executor.complete(request)

    def test_loader_rejects_a_consistent_record_with_a_single_locus_on_a_model_call(self) -> None:
        import dataclasses
        from creib.forge.conformance.common import content_id
        from creib.forge.conformance.records import OBSERVATION_DOMAIN, observation_from_dict

        wrong = FakeExecutor(lambda req: response_from_content(json.dumps({**self.output, "site": "elsewhere"})))
        with tempfile.TemporaryDirectory() as directory:
            result = run_pilot(
                spec=_CONFIG.spec, corpus=_CORPUS, plan=_PLAN, model="gpt-oss:20b",
                executor=wrong, executor_kind="fake",
                output_dir=Path(directory), created_on=CREATED_ON, families=(Family.BASELINE,), limit=1,
            )
        observation = result.observations[0]
        self.assertGreaterEqual(len(observation.routing.live_loci), 2)
        forged_routing = dataclasses.replace(observation.routing, live_loci=observation.routing.live_loci[:1])
        draft = dataclasses.replace(observation, routing=forged_routing, observation_id="0" * 64)
        forged = dataclasses.replace(draft, observation_id=content_id(OBSERVATION_DOMAIN, draft.body()))
        with self.assertRaises(PolicyViolation):
            observation_from_dict(forged.to_dict())

    def test_substrate_swap_uses_the_corpus_rendering_vocabulary(self) -> None:
        from creib.forge.conformance.corpus import RENDERINGS

        swaps = [v for v in _PLAN.variants if v.family is Family.SUBSTRATE_SWAP]
        self.assertTrue(swaps)
        self.assertTrue(all(v.substrate in RENDERINGS for v in swaps))



LR_GOOD = {
    "employee_name": "Maya Patel", "leave_type": "annual", "start_date": "2025-10-13", "end_date": "2025-10-17",
    "total_days": 5, "reason": "Family wedding in Adelaide.", "manager_notified": True,
}
LR_SPANS = {
    "employee_name_span": "Maya Patel", "leave_type_span": "annual leave", "start_date_span": "Monday 13 October 2025",
    "end_date_span": "Friday 17 October 2025", "total_days_span": "five working days", "reason_span": "for a family wedding in Adelaide",
}


class PlainFillTests(unittest.TestCase):
    """A form with no answer key can be filled and recorded without any verdict on content."""

    TEMPLATE = ROOT / "forge" / "conformance" / "pilots" / "leave-request" / "pilot.json"

    def setUp(self) -> None:
        self.config = load_pilot_config(self.TEMPLATE)
        self.corpus = load_corpus(self.config.corpus_path, self.config.spec)
        self.plan = plan(self.config.spec, self.corpus)
        self.baseline = next(v for v in self.plan.variants if v.family is Family.BASELINE and v.base_case_id == "LR-001")

    def test_template_pilot_validates_and_plans_without_code_changes(self) -> None:
        self.assertEqual({o.field for o in self.config.spec.obligations}, set(self.config.spec.form_schema["properties"]))
        self.assertEqual(sorted(v.family.value for v in self.plan.variants), ["BASELINE", "BASELINE", "IMPORT_DEPENDENCY", "IMPORT_DEPENDENCY", "ROUND_TRIP", "ROUND_TRIP"])
        self.assertTrue(all(o.kind == "unknown" for case in self.corpus.cases for o in case.expected))

    def test_unknown_oracle_records_without_judging_and_keeps_form_constraints(self) -> None:
        scoring = score(self.baseline, response_from_content(json.dumps({**LR_GOOD, **LR_SPANS})))
        self.assertEqual({v.verdict for v in scoring.field_verdicts}, {"NOT_SCORED"})
        self.assertEqual({g.verdict for g in scoring.grounding_verdicts}, {"GROUNDED"})
        routing = route(self.baseline, scoring)
        self.assertEqual(routing.live_loci, ())
        self.assertFalse(routing.unrefuted_for_variant, "unscored fields must not read as unrefuted")
        bad = {**LR_GOOD, **LR_SPANS, "leave_type": "holiday", "total_days": "five"}
        verdicts = {v.field: v.verdict for v in score(self.baseline, response_from_content(json.dumps(bad))).field_verdicts}
        self.assertEqual(verdicts["leave_type"], "ENUM_VIOLATION")
        self.assertEqual(verdicts["total_days"], "TYPE_VIOLATION")
        self.assertIn("CANDIDATE", route(self.baseline, score(self.baseline, response_from_content(json.dumps(bad)))).loci)

    def test_plain_fill_run_is_inconclusive_not_unrefuted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = run_pilot(
                spec=self.config.spec, corpus=self.corpus, plan=self.plan, model="gpt-oss:120b",
                executor=FakeExecutor(lambda req: response_from_content(json.dumps({**LR_GOOD, **LR_SPANS}))), executor_kind="fake",
                output_dir=Path(directory), created_on=CREATED_ON, families=(Family.BASELINE,), limit=1,
            )
            self.assertEqual(result.run_record.scope_label, "INCONCLUSIVE_NO_SCORED_OUTPUT")
            self.assertEqual(dict(result.run_record.grounding_verdict_counts), {"GROUNDED": 6})
            completed = subprocess.run(
                [sys.executable, str(TOOL), "fills", "--observations-dir", directory],
                capture_output=True, text=True, env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            lines = [json.loads(line) for line in completed.stdout.splitlines() if line.strip()]
            self.assertEqual(len(lines), 1)
            self.assertEqual(lines[0]["filled_form"], LR_GOOD, "companion span keys are stripped from the filled form")
            self.assertEqual(lines[0]["structural_issues"], [])
            self.assertEqual(sorted(lines[0]["unjudged_fields"]), sorted(LR_GOOD))
            self.assertEqual({g["verdict"] for g in lines[0]["grounding"]}, {"GROUNDED"})
            self.assertEqual(load_observation_directory(Path(directory))[0].variant.grounding.mode, "spans")


class RoundOneImprovementTests(unittest.TestCase):
    """Changes made from the first travel-claim run: local endpoints, duplicate keys, change detection, prompt wording."""

    def test_endpoint_auth_none_needs_no_key_and_sends_no_authorization_header(self) -> None:
        from creib.forge.conformance.executor import OllamaChatExecutor
        from creib.forge.conformance.spec import endpoint_from_dict
        raw = {"kind": "ollama-chat", "base_url": "http://localhost:11434", "timeout_seconds": 60, "options": {"temperature": 0, "seed": 7}, "think": False}
        self.assertEqual(endpoint_from_dict(raw).auth, "bearer", "absent means bearer, so older records keep their meaning")
        self.assertEqual(endpoint_from_dict({**raw, "auth": "none"}).auth, "none")
        with self.assertRaisesRegex(RecordError, "endpoint.auth"):
            endpoint_from_dict({**raw, "auth": "basic"})
        variant = _variant(Family.BASELINE, "ORD-001")
        request = build_chat_request(variant, model="gpt-oss:20b", endpoint=_CONFIG.spec.endpoint)
        captured = []
        def fake_urlopen(http_request, timeout):
            captured.append(http_request)
            raise urllib.error.URLError("connection refused")
        with patch.dict(os.environ, {}, clear=True), patch("creib.forge.conformance.executor.urllib.request.urlopen", fake_urlopen):
            with self.assertRaisesRegex(RecordError, "OLLAMA_API_KEY is not set"):
                OllamaChatExecutor(base_url="http://localhost:11434", auth="bearer")._attempt(request, 1)
            response = OllamaChatExecutor(base_url="http://localhost:11434", auth="none")._attempt(request, 1)
        self.assertIsNotNone(response.transport_error, "a refused connection is a recorded transport error, not an exception")
        self.assertEqual(len(captured), 1)
        self.assertFalse(captured[0].has_header("Authorization"))
        self.assertEqual(captured[0].full_url, "http://localhost:11434/api/chat")

    def test_committed_records_still_load_and_replay_their_ids(self) -> None:
        # Every published run record under forge/conformance/runs/ must keep loading; a serialisation
        # change that alters header bytes (as adding an always-written endpoint key did) shows up here.
        runs_root = ROOT / "forge" / "conformance" / "runs"
        run_paths = sorted(runs_root.glob("*/run.*.json"))
        self.assertTrue(run_paths, "no committed run records found")
        for path in run_paths:
            record = load_run(path)
            self.assertEqual(path.name, f"run.{record.run_id[:16]}.json")
            self.assertNotIn("auth", json.loads(path.read_text())["endpoint"], "bearer is the absent default")
        for directory in sorted({p.parent for p in run_paths}):
            for path in sorted(directory.glob("observation.*.json"))[:3]:
                self.assertEqual(path.name, f"observation.{load_observation(path).observation_id[:16]}.json")
        from creib.forge.conformance.spec import endpoint_from_dict
        raw = {"kind": "ollama-chat", "base_url": "http://localhost:11434", "timeout_seconds": 60, "options": {"temperature": 0, "seed": 7}, "think": False}
        self.assertNotIn("auth", endpoint_from_dict(raw).to_dict())
        self.assertEqual(endpoint_from_dict({**raw, "auth": "none"}).to_dict()["auth"], "none")

    def test_replay_dir_rescores_recorded_replies_without_a_network(self) -> None:
        pilot = ROOT / "forge" / "conformance" / "pilots" / "leave-request" / "pilot.json"
        env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
        env.pop("OLLAMA_API_KEY", None)
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            base = [sys.executable, str(TOOL), "run", "--pilot", str(pilot), "--model", "gpt-oss:120b", "--family", "BASELINE", "--created-on", CREATED_ON]
            canned = subprocess.run(base + ["--dry-run", "--output-dir", first], capture_output=True, text=True, env=env)
            self.assertIn(canned.returncode, (0, 1), canned.stderr)
            replayed = subprocess.run(base + ["--replay-dir", first, "--output-dir", second], capture_output=True, text=True, env=env)
            self.assertIn(replayed.returncode, (0, 1), replayed.stderr)
            originals = {o.request_digest: o for o in load_observation_directory(Path(first))}
            copies = load_observation_directory(Path(second))
            self.assertEqual(len(copies), len(originals))
            for copy in copies:
                self.assertEqual(copy.scoring.parsed_output, originals[copy.request_digest].scoring.parsed_output)
                self.assertNotEqual(copy.observation_id, originals[copy.request_digest].observation_id, "a re-score is a new record")
            self.assertEqual(load_run(next(Path(second).glob("run.*.json"))).executor_kind, "replay")
            both = subprocess.run(base + ["--dry-run", "--replay-dir", first, "--output-dir", second], capture_output=True, text=True, env=env)
            self.assertNotEqual(both.returncode, 0)

    def test_replay_pairs_each_repeat_with_the_reply_that_repeat_received(self) -> None:
        """H23: with repeats, one request digest has several recorded replies; the replay must not refuse or conflate them."""
        from creib.forge.conformance.executor import ReplayExecutor
        from creib.forge.conformance.prompt import build_chat_request
        round3 = ROOT / "forge" / "conformance" / "runs" / "travel-claim-round3"
        config = load_pilot_config(ROOT / "forge" / "conformance" / "pilots" / "travel-claim" / "pilot.json")
        corpus = load_corpus(config.corpus_path, config.spec)
        travel_plan = plan(config.spec, corpus)
        recorded = [o for o in load_observation_directory(round3) if o.model == "nemotron-3-nano:30b" and o.response is not None]
        by_key = {(o.request_digest, o.variant.repeat_index or 0): o for o in recorded}
        self.assertTrue(any(o.variant.repeat_index for o in recorded), "the round-three records carry repeats")
        differing = [o for o in recorded if o.variant.family is Family.REPEAT and o.scoring.changed_vs_baseline is True]
        self.assertTrue(differing, "nemotron's repeats differed, which is what makes the pairing observable")
        executor = ReplayExecutor(round3)
        for observation in differing[:3]:
            variant = next(v for v in travel_plan.variants if v.base_case_id == observation.variant.base_case_id and v.family is Family.REPEAT and v.repeat_index == observation.variant.repeat_index)
            materialised = variant if variant.input_document is not None else None
            self.assertIsNotNone(materialised)
            request = build_chat_request(materialised, model="nemotron-3-nano:30b", endpoint=config.spec.endpoint)
            self.assertEqual(request.request_digest, observation.request_digest)
            self.assertEqual(executor.complete(request), observation.response)
            baseline = by_key[(observation.request_digest, 0)]
            self.assertNotEqual(executor.complete(request), baseline.response)
        import dataclasses
        ninth = dataclasses.replace(build_chat_request(materialised, model="nemotron-3-nano:30b", endpoint=config.spec.endpoint), repeat_index=9)
        self.assertEqual(ninth.request_digest, observation.request_digest, "the repeat index is outside the digest")
        with self.assertRaisesRegex(RecordError, "repeat 9"):
            executor.complete(ninth)

    def test_duplicate_keys_are_recovered_last_wins_and_named(self) -> None:
        from creib.forge.conformance.oracle import parse_content
        content = '{"a": 1, "b": "x", "a": 2}'
        parsed, verdict, detail, recovered = parse_content(content, ())
        self.assertEqual((parsed, verdict, recovered), ({"a": 2, "b": "x"}, "JSON_OBJECT", True))
        self.assertIn("duplicate keys ['a']", detail)
        # inside prose too, and a float still refuses
        parsed, verdict, _, recovered = parse_content('Here you go:\n```json\n{"a": 1, "a": 3}\n```', ())
        self.assertEqual((parsed, verdict, recovered), ({"a": 3}, "JSON_OBJECT", True))
        _, verdict, _, _ = parse_content('{"a": 1.5, "a": 2}', ())
        self.assertEqual(verdict, "INVALID_JSON")
        # scored as a provisional recovery, like prose recovery
        variant = _variant(Family.BASELINE, "ORD-001")
        good = _correct_output("ORD-001")
        first_key = next(iter(good))
        duplicated = "{" + json.dumps(first_key) + ": \"wrong\", " + json.dumps(good)[1:]
        scoring = score(variant, response_from_content(duplicated))
        self.assertEqual(scoring.response_verdict, "JSON_OBJECT")
        self.assertTrue(scoring.recovered_from_prose)
        self.assertEqual(scoring.recovery_status, "project_import_provisional")
        self.assertTrue(scoring.all_match)

    def test_change_against_baseline_compares_form_fields_only(self) -> None:
        from creib.forge.conformance.oracle import _changed
        fields = ("a", "b")
        self.assertIs(_changed({"a": 1, "b": 2, "junk": 1}, {"a": 1, "b": 2}, fields), False)
        self.assertIs(_changed({"a": 1, "b": 2, "a_span": "one"}, {"a": 1, "b": 2, "a_span": "1"}, fields), False)
        self.assertIs(_changed({"a": 1, "b": 3}, {"a": 1, "b": 2}, fields), True)
        self.assertIs(_changed({"a": 1}, {"a": 1, "b": 2}, fields), True, "a dropped field is a change")
        self.assertIsNone(_changed(None, {"a": 1}, fields))

    def test_abstention_sentence_names_each_companion_or_its_absence(self) -> None:
        config = load_pilot_config(ROOT / "forge" / "conformance" / "pilots" / "travel-claim" / "pilot.json")
        corpus = load_corpus(config.corpus_path, config.spec)
        variant = next(v for v in plan(config.spec, corpus).variants if v.family is Family.BASELINE)
        text = variant.prompt_instructions()
        self.assertIn("Output no companion key for any other field.", text)
        self.assertIn("for `trip_end` also output null for `trip_end_span`; `nights_away` has no companion key", text)
        self.assertNotIn("if it has one", text)


class ConfigurableProbeTests(unittest.TestCase):
    """Repeats, span relaxations, grounding in the report, and grounding-aware routing; all off by default."""

    TRAVEL = ROOT / "forge" / "conformance" / "pilots" / "travel-claim" / "pilot.json"

    def setUp(self) -> None:
        self.config = load_pilot_config(self.TRAVEL)
        self.corpus = load_corpus(self.config.corpus_path, self.config.spec)
        self.plan = plan(self.config.spec, self.corpus)

    def test_repeats_zero_adds_nothing_and_keeps_variant_ids(self) -> None:
        self.assertEqual(_CONFIG.spec.repeats, 0)
        self.assertEqual(dict(_PLAN.counts)["REPEAT"], 0)
        body = _variant(Family.BASELINE, "ORD-001").body()
        self.assertNotIn("repeat_index", body, "an absent key keeps every earlier variant id replaying")
        self.assertNotIn("span_relaxations", _CONFIG.spec.grounding.to_dict())
        with tempfile.TemporaryDirectory() as directory:
            copy = Path(directory) / "travel-claim"
            shutil.copytree(self.TRAVEL.parent, copy)
            raw = json.loads((copy / "pilot.json").read_text()); raw["repeats"] = 11
            (copy / "pilot.json").write_text(json.dumps(raw))
            with self.assertRaisesRegex(RecordError, r"repeats.*(at most|maximum)"):
                load_pilot_config(copy / "pilot.json")

    def test_repeat_variants_reuse_the_baseline_request_and_record_the_noise_floor(self) -> None:
        self.assertEqual(self.config.spec.repeats, 2)
        repeats = [v for v in self.plan.variants if v.family is Family.REPEAT]
        baselines = {v.base_case_id: v for v in self.plan.variants if v.family is Family.BASELINE}
        self.assertEqual(len(repeats), 2 * len(baselines))
        for variant in repeats:
            base = baselines[variant.base_case_id]
            self.assertIn(variant.repeat_index, (1, 2))
            self.assertNotEqual(variant.variant_id, base.variant_id)
            self.assertEqual(
                build_chat_request(variant, model="gemma4:31b", endpoint=self.config.spec.endpoint).request_digest,
                build_chat_request(base, model="gemma4:31b", endpoint=self.config.spec.endpoint).request_digest,
                "a repeat is the same request; only the variant differs",
            )
            rebuilt = variant_from_dict(loads_strict(canonical_bytes(variant.to_dict()).decode("utf-8")))
            self.assertEqual(rebuilt.repeat_index, variant.repeat_index)
        # A deterministic executor: repeats identical, no trigger. A drifting one: REPEAT_DIFFERS, AUXILIARY and CANDIDATE live.
        good = {
            "claimant_name": "Hannah Kowalski", "claimant_name_span": "Hannah Kowalski", "approver_name": "Marcus Oyelaran", "approver_name_span": "Marcus Oyelaran",
            "employee_id": "E-41207", "employee_id_span": "41207", "trip_start": "2025-10-07", "trip_start_span": "Tuesday 7 October 2025",
            "trip_end": "2025-10-10", "trip_end_span": "Friday 10 October 2025", "nights_away": 3, "destination_city": "Melbourne", "destination_city_span": "Melbourne",
            "purpose": "conference", "total_claimed_cents": 196640, "advance_received": False, "receipts_attached": True,
            "contact_phone": "+61431555018", "contact_phone_span": "0431 555 018", "cost_centre": "CC-3120",
        }
        calls = {"n": 0}
        def drifting(request):
            calls["n"] += 1
            return response_from_content(json.dumps({**good, "total_claimed_cents": 196640 + (10000 if calls["n"] % 2 == 0 else 0)}))
        with tempfile.TemporaryDirectory() as directory:
            steady = run_pilot(spec=self.config.spec, corpus=self.corpus, plan=self.plan, model="gemma4:31b",
                               executor=FakeExecutor(lambda req: response_from_content(json.dumps(good))), executor_kind="fake",
                               output_dir=Path(directory) / "steady", created_on=CREATED_ON, families=(Family.REPEAT,), limit=2)
            steady_repeats = [o for o in steady.observations if o.variant.family is Family.REPEAT]
            self.assertEqual(len(steady_repeats), 2)
            self.assertTrue(all(o.scoring.changed_vs_baseline is False for o in steady_repeats))
            self.assertTrue(all("REPEAT_DIFFERS" not in o.routing.triggers for o in steady_repeats))
            self.assertTrue(all(o.baseline_observation_id is not None for o in steady_repeats))
            drift = run_pilot(spec=self.config.spec, corpus=self.corpus, plan=self.plan, model="gemma4:31b",
                              executor=FakeExecutor(drifting), executor_kind="fake",
                              output_dir=Path(directory) / "drift", created_on=CREATED_ON, families=(Family.REPEAT,), limit=2)
            drift_repeats = [o for o in drift.observations if o.variant.family is Family.REPEAT]
            differing = [o for o in drift_repeats if "REPEAT_DIFFERS" in o.routing.triggers]
            self.assertTrue(differing, "the drifting executor must produce at least one differing repeat")
            for o in differing:
                self.assertEqual(set(o.routing.loci) >= {"AUXILIARY", "CANDIDATE"}, True)
            report = build_report([drift.run_record], drift.observations)
            summary = report["runs"][0]["repeatability"]
            self.assertEqual(summary["repeat_observations"], 2)
            self.assertEqual(summary["differing_from_baseline"], len(differing))
            self.assertIn("grounding_verdicts", report["runs"][0])
            markdown = render_markdown(report)
            self.assertIn("### Repeatability", markdown)
            self.assertIn("### Grounding verdicts", markdown)
            self.assertIn("REPEAT_DIFFERS", markdown)
            for record in load_observation_directory(Path(directory) / "drift"):
                self.assertIsNotNone(record.variant.repeat_index if record.variant.family is Family.REPEAT else 1)

    def test_span_relaxations_are_configured_and_recorded(self) -> None:
        from creib.forge.conformance.corpus import Oracle
        from creib.forge.conformance.oracle import _span_occurs
        document = "She travelled 24 to 26 June 2025. Dates | Mon 3 Nov to Thu 6 Nov 2025. Subject: Sick leave."
        self.assertIsNone(_span_occurs("24 June 2025", document, ()))
        self.assertEqual(_span_occurs("24 June 2025", document, ("date_range_completion",)), "date_range_completion")
        self.assertEqual(_span_occurs("Mon 3 Nov 2025", document, ("date_range_completion",)), "date_range_completion")
        self.assertEqual(_span_occurs("Thu 6 Nov 2025", document, ("date_range_completion",)), "verbatim", "the range end with its month is literally present")
        self.assertIsNone(_span_occurs("25 June 2025", document, ("date_range_completion",)), "only the endpoints of a range are completions")
        self.assertIsNone(_span_occurs("sick", document, ()))
        self.assertEqual(_span_occurs("sick", document, ("case_insensitive",)), "case_insensitive")
        self.assertEqual(_span_occurs("Sick leave", document, ("case_insensitive",)), "verbatim")
        # configuration: unknown relaxation refused; mode none refuses any; empty is omitted from the body
        from creib.forge.conformance.spec import grounding_from_dict
        base = {"mode": "spans", "span_suffix": "_span", "span_fields": ["a"], "value_in_span_fields": [], "abstain_fields": []}
        with self.assertRaisesRegex(RecordError, "unknown relaxation"):
            grounding_from_dict({**base, "span_relaxations": ["fuzzy"]}, ("a", "b"))
        with self.assertRaisesRegex(RecordError, "span_relaxations to be empty"):
            grounding_from_dict({"mode": "none", "span_suffix": "_span", "span_fields": [], "value_in_span_fields": [], "abstain_fields": [], "span_relaxations": ["case_insensitive"]}, ("a",))
        self.assertNotIn("span_relaxations", grounding_from_dict({**base, "span_relaxations": []}, ("a", "b")).to_dict())
        self.assertEqual(grounding_from_dict(base, ("a", "b")).span_relaxations, ())
        # the travel-claim battery accepts completed range dates and records that it did so
        variant = next(v for v in self.plan.variants if v.family is Family.BOUNDARY_SHIFT and v.base_case_id == "BND-105")
        self.assertEqual(variant.grounding.span_relaxations, ("date_range_completion",))
        good = {
            "claimant_name": "Mei-Ling Chow", "claimant_name_span": "Mei-Ling Chow", "approver_name": "Daniel Okonkwo", "approver_name_span": "Daniel Okonkwo",
            "employee_id": "E-29901", "employee_id_span": "E-29901", "trip_start": "2025-09-03", "trip_start_span": "3 September 2025",
            "trip_end": "2025-09-07", "trip_end_span": "7 September 2025", "nights_away": 4, "destination_city": "Auckland", "destination_city_span": "Auckland",
            "purpose": "conference", "total_claimed_cents": 337342, "advance_received": True, "receipts_attached": True,
            "contact_phone": "+61466120553", "contact_phone_span": "0466 120 553",
        }
        scoring = score(variant, response_from_content(json.dumps(good)))
        by_field = {g.field: g for g in scoring.grounding_verdicts}
        self.assertEqual(by_field["trip_start"].verdict, "GROUNDED")
        self.assertIn("date_range_completion", by_field["trip_start"].detail or "")
        self.assertIsNone(by_field["trip_end"].detail, "a verbatim match carries no relaxation note")
        self.assertEqual(route(variant, scoring).triggers, ())

    def test_length_violation_keeps_auxiliary_live_only_under_grounding(self) -> None:
        # incident form: grounding off; travel claim: grounding on. Same over-long value, different suspects.
        incident = _variant(Family.BASELINE, "ORD-001")
        long_site = {**_correct_output("ORD-001"), "site": "x" * 61}
        plain = route(incident, score(incident, response_from_content(json.dumps(long_site))))
        self.assertIn("LENGTH_VIOLATION", plain.triggers)
        self.assertEqual(set(plain.loci), {"CANDIDATE", "TEST"})
        grounded = next(v for v in self.plan.variants if v.family is Family.BASELINE and v.base_case_id == "TRV-001")
        long_city = {
            "claimant_name": "Hannah Kowalski", "claimant_name_span": "Hannah Kowalski", "approver_name": "Marcus Oyelaran", "approver_name_span": "Marcus Oyelaran",
            "employee_id": "E-41207", "employee_id_span": "41207", "trip_start": "2025-10-07", "trip_start_span": "Tuesday 7 October 2025",
            "trip_end": "2025-10-10", "trip_end_span": "Friday 10 October 2025", "nights_away": 3,
            "destination_city": "Melbourne, with a stopover in Canberra on the return leg", "destination_city_span": "Melbourne",
            "purpose": "conference", "total_claimed_cents": 196640, "advance_received": False, "receipts_attached": True,
            "contact_phone": "+61431555018", "contact_phone_span": "0431 555 018", "cost_centre": "CC-3120",
        }
        routed = route(grounded, score(grounded, response_from_content(json.dumps(long_city))))
        self.assertIn("LENGTH_VIOLATION", routed.triggers)
        self.assertEqual(set(routed.loci), {"CANDIDATE", "TEST", "AUXILIARY"})
        self.assertTrue(any("quote verbatim" in locus.reason for locus in routed.live_loci if locus.locus == "AUXILIARY"))


class ClaimsTests(unittest.TestCase):
    """Conjectures are refuted by one record or left unrefuted for the declared scope; never confirmed."""

    LEAVE = ROOT / "forge" / "conformance" / "runs" / "leave-request"
    CLAIMS = ROOT / "forge" / "conformance" / "pilots" / "travel-claim" / "claims.json"

    def _claim(self, cid, kind, condition, **scope):
        from creib.forge.conformance.claims import Claim, Scope
        return Claim(claim_id=cid, statement=cid, kind=kind, scope=Scope(families=scope.get("families"), cases=scope.get("cases"), models=scope.get("models"), model_call=scope.get("model_call")), condition=condition, note=None)

    def test_refuted_unrefuted_and_not_tested(self) -> None:
        from creib.forge.conformance.claims import evaluate_claims
        observations = load_observation_directory(self.LEAVE)
        results = evaluate_claims((
            self._claim("spans-real", "never", {"grounding_verdict": {"verdict": "SPAN_NOT_IN_DOCUMENT"}}),
            self._claim("parses", "always", {"response_verdict": "JSON_OBJECT"}, model_call=True),
            self._claim("no-such-case", "never", {"trigger": "MISMATCH"}, cases=["LR-999"]),
            self._claim("abstains", "always", {"all_of": [{"value_null": {"field": "end_date"}}, {"value_null": {"field": "total_days"}}]}, cases=["LR-002"], families=["BASELINE"]),
            self._claim("repeat-only", "never", {"trigger": "REPEAT_DIFFERS"}, families=["REPEAT"]),
        ), observations)
        by_id = {r.claim.claim_id: r for r in results}
        self.assertEqual(by_id["spans-real"].status, "REFUTED")
        self.assertEqual(by_id["spans-real"].refuting_models, ("nemotron-3-nano:30b",))
        self.assertEqual(by_id["spans-real"].refuting, 2)
        self.assertTrue(all(len(e) == 4 for e in by_id["spans-real"].examples))
        self.assertEqual(by_id["parses"].status, "UNREFUTED_FOR_DECLARED_SCOPE")
        self.assertEqual(by_id["parses"].tested, 24)
        self.assertEqual(by_id["no-such-case"].status, "NOT_TESTED")
        self.assertEqual(by_id["abstains"].status, "UNREFUTED_FOR_DECLARED_SCOPE")
        self.assertEqual(by_id["abstains"].tested, 6)
        self.assertEqual(by_id["repeat-only"].status, "NOT_TESTED", "no REPEAT variants exist in that run")
        for result in results:
            self.assertIn("epistemic_limit", result.to_dict())
            self.assertNotIn("confirmed", json.dumps(result.to_dict()).lower())

    def test_survival_says_whether_the_check_was_shown_able_to_fail(self) -> None:
        from creib.forge.conformance.claims import evaluate_claims, render_claims_markdown
        observations = load_observation_directory(self.LEAVE)
        results = evaluate_claims((
            self._claim("no-refusal", "never", {"trigger": "REFUSAL_SUSPECTED"}),
            self._claim("length-elsewhere", "never", {"trigger": "LENGTH_VIOLATION"}, models=["gpt-oss:120b"]),
            self._claim("spans-real", "never", {"grounding_verdict": {"verdict": "SPAN_NOT_IN_DOCUMENT"}}),
        ), observations)
        by_id = {r.claim.claim_id: r for r in results}
        self.assertEqual(by_id["no-refusal"].status, "UNREFUTED_FOR_DECLARED_SCOPE")
        self.assertEqual(by_id["no-refusal"].witnesses_outside_scope, 0)
        self.assertFalse(by_id["no-refusal"].shown_able_to_fail)
        self.assertEqual(by_id["length-elsewhere"].status, "UNREFUTED_FOR_DECLARED_SCOPE")
        self.assertEqual(by_id["length-elsewhere"].witnesses_outside_scope, 6, "deepseek and nemotron each raised LENGTH_VIOLATION three times")
        self.assertTrue(by_id["length-elsewhere"].shown_able_to_fail)
        self.assertTrue(by_id["spans-real"].shown_able_to_fail)
        self.assertEqual(by_id["spans-real"].witnesses_outside_scope, 0)
        self.assertEqual(by_id["no-refusal"].to_dict()["shown_able_to_fail"], False)
        text = render_claims_markdown(results)
        self.assertIn("has not been shown able to fail", text)
        self.assertIn("held on 6 supplied observations outside the declared scope", text)

    def test_conditions_fail_closed(self) -> None:
        from creib.forge.conformance.claims import compile_condition
        for bad in ({"trigger": "NOPE"}, {"response_verdict": "NOPE"}, {"field_verdict": {"verdict": "NOPE"}}, {"locus": "MODEL"}, {"recovered": "sometimes"}, {"trigger": "MISMATCH", "locus": "TEST"}, {"unknown": 1}, {"all_of": []}, {"baseline": {"nope": 1}}, {"output_tokens": {}}, {"output_tokens": {"min": -1}}):
            with self.assertRaises(RecordError, msg=repr(bad)):
                compile_condition(bad)

    def test_baseline_relative_conditions(self) -> None:
        from creib.forge.conformance.claims import evaluate_claims
        observations = load_observation_directory(self.LEAVE)
        results = evaluate_claims((
            self._claim("rt-vs-base", "never", {"all_of": [{"trigger": "LENGTH_VIOLATION"}, {"baseline": {"not": {"trigger": "LENGTH_VIOLATION"}}}]}, families=["ROUND_TRIP"]),
            self._claim("rt-inherits", "always", {"any_of": [{"not": {"trigger": "LENGTH_VIOLATION"}}, {"baseline": {"trigger": "LENGTH_VIOLATION"}}]}, families=["ROUND_TRIP"]),
            self._claim("no-baseline", "never", {"baseline": {"trigger": "MISMATCH"}}, families=["BASELINE"]),
        ), observations)
        by_id = {r.claim.claim_id: r for r in results}
        self.assertEqual(by_id["rt-vs-base"].status, "UNREFUTED_FOR_DECLARED_SCOPE", "the round-trip length violations were inherited from their baselines")
        self.assertEqual(by_id["rt-inherits"].status, "UNREFUTED_FOR_DECLARED_SCOPE")
        self.assertEqual(by_id["no-baseline"].tested, 12)
        from creib.forge.conformance.claims import compile_condition, Context
        long_reply = compile_condition({"output_tokens": {"min": 1}})
        counted = [o for o in observations if o.response is not None and o.response.eval_count is not None]
        self.assertTrue(counted)
        self.assertTrue(all(long_reply(o, Context(observations)) for o in counted))
        self.assertFalse(compile_condition({"output_tokens": {"max": 0}})(counted[0], Context(observations)))

    def test_pilot_claims_file_loads_and_cli_runs(self) -> None:
        from creib.forge.conformance.claims import load_claims
        claims = load_claims(self.CLAIMS)
        self.assertGreater(len(claims), 30)
        self.assertEqual(len({c.claim_id for c in claims}), len(claims))
        with tempfile.TemporaryDirectory() as directory:
            markdown = Path(directory) / "claims.md"
            completed = subprocess.run(
                [sys.executable, str(TOOL), "claims", "--claims", str(self.CLAIMS), "--observations-dir", str(self.LEAVE), "--markdown", str(markdown)],
                capture_output=True, text=True, env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            lines = [json.loads(line) for line in completed.stdout.splitlines() if line.strip()]
            self.assertEqual(lines[-1]["claims"], len(claims))
            self.assertEqual(set(lines[-1]["status_counts"]), {"REFUTED", "REFUTED_ON_CONTESTED_READING", "UNREFUTED_FOR_DECLARED_SCOPE", "NOT_TESTED"})
            self.assertIsInstance(lines[-1]["unrefuted_not_shown_able_to_fail"], list)
            text = markdown.read_text()
            self.assertIn("`UNREFUTED_FOR_DECLARED_SCOPE` means no supplied record refuted the claim, or every refutation rests on a reading of the key that the appraisal labels out; it is not a proof.", text)
            self.assertTrue(text.rstrip().endswith(NON_INDUCTIVE_LIMIT))


class SupportFamiliesTests(unittest.TestCase):
    """A reading's support may name the families it applies to; a rival variant's explicit rule is not the baseline reading (H24)."""

    def test_families_restrict_which_observations_rest_on_a_reading(self) -> None:
        from creib.forge.conformance.appraisal import Appraisal, load_appraisal
        from creib.forge.conformance.claims import evaluate_claims, load_claims
        pilot = ROOT / "forge" / "conformance" / "pilots" / "explanatory-distinctions"
        observations = load_observation_directory(ROOT / "forge" / "conformance" / "runs" / "explanatory-distinctions")
        appraisal = Appraisal.build(load_appraisal(pilot / "appraisal.json"))
        rivals = [o for o in observations if o.variant.family is Family.RIVAL_SUBSTITUTION and o.variant.base_case_id == "D-02"]
        baselines = [o for o in observations if o.variant.family is Family.BASELINE and o.variant.base_case_id == "D-02"]
        self.assertTrue(rivals and baselines)
        for o in rivals:
            self.assertEqual(appraisal.readings_of(o, frozenset({"originative_contribution"}), frozenset()), ())
        criticised = [o for o in baselines if any(v.field == "originative_contribution" and v.verdict == "MISMATCH" for v in o.scoring.field_verdicts)]
        self.assertTrue(criticised)
        self.assertIn("R-D02-RECONSTRUCTION-ORIGINATIVE", appraisal.readings_of(criticised[0], frozenset({"originative_contribution"}), frozenset()))
        results = {r.claim.claim_id: r for r in evaluate_claims(load_claims(pilot / "claims.json"), observations, appraisal)}
        self.assertEqual(results["DIS-13"].status, "REFUTED", "the rival rule states the expected answer; nothing about it is contested")
        self.assertEqual(results["DIS-13"].refuting_contested, 0)
        with tempfile.TemporaryDirectory() as directory:
            raw = json.loads((pilot / "appraisal.json").read_text(encoding="utf-8"))
            raw["arguments"][0]["supports"]["families"] = ["NOT_A_FAMILY"]
            path = Path(directory) / "appraisal.json"; path.write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaisesRegex(RecordError, "not a family"):
                load_appraisal(path)


class GeneratedCorpusTests(unittest.TestCase):
    """The generated corpora are reproducible from their generators, so their answer keys come from code, not memory."""

    def test_generators_reproduce_the_committed_corpora(self) -> None:
        for script in ("gen_appraisal_labelling_corpus.py", "gen_explanatory_distinctions_corpus.py", "gen_signed_derivations_corpus.py"):
            completed = subprocess.run(
                [sys.executable, str(ROOT / "tools" / script)],
                capture_output=True, text=True, cwd=str(ROOT), env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("unchanged", completed.stdout, script)

    def test_labelling_keys_are_the_harness_labels(self) -> None:
        from creib.forge.conformance.appraisal import Argument, appraise
        config = load_pilot_config(ROOT / "forge" / "conformance" / "pilots" / "appraisal-labelling" / "pilot.json")
        corpus = load_corpus(config.corpus_path, config.spec)
        checked = 0
        for case in corpus.cases:
            expected = {oracle.field: oracle for oracle in case.expected}
            arguments = []
            for line in case.renderings["table"].splitlines():
                cells = [cell.strip() for cell in line.split("|")]
                if len(cells) == 4 and cells[0][:2] in {"A1", "A2", "A3", "A4", "A5", "A6"}:
                    aid = cells[0][:2]
                    essential = tuple(x for x in cells[2].split(", ") if x != "-")
                    attacks = tuple(x for x in cells[3].split(", ") if x != "-")
                    arguments.append(Argument(argument_id=aid, statement=aid, kind="other", supports=None, essential=essential, attacks=attacks, readiness=cells[1], readiness_reason="t", register=None))
            self.assertEqual(len(arguments), 6, case.case_id)
            labels = appraise(tuple(arguments))
            for aid in ("A1", "A2", "A3", "A4", "A5", "A6"):
                self.assertEqual(expected[f"label_{aid.lower()}"].value, labels.of(aid), f"{case.case_id} {aid}")
            self.assertEqual(expected["usable_count"].value, len(labels.inside), case.case_id)
            checked += 1
        self.assertEqual(checked, 18)

    def test_a_rival_reading_fixes_the_other_fields_its_rule_moves(self) -> None:
        config = load_pilot_config(ROOT / "forge" / "conformance" / "pilots" / "appraisal-labelling" / "pilot.json")
        corpus = load_corpus(config.corpus_path, config.spec)
        planned = plan(config.spec, corpus)
        rivals = {(v.base_case_id, v.rival_label): v for v in planned.variants if v.family is Family.RIVAL_SUBSTITUTION}
        as_ready = {o.field: o.value for o in rivals[("LAB-03", "unknown_as_ready")].expected}
        never_ready = {o.field: o.value for o in rivals[("LAB-03", "unknown_never_ready")].expected}
        self.assertEqual((as_ready["label_a4"], as_ready["label_a3"], as_ready["usable_count"]), ("in", "out", 1), "the unknown attacker becomes ready and its target goes out")
        self.assertEqual((never_ready["label_a4"], never_ready["label_a3"], never_ready["usable_count"]), ("undecided", "undecided", 0), "the baseline key stands")
        raw = json.loads(config.corpus_path.read_text(encoding="utf-8"))
        case = next(c for c in raw["cases"] if c["case_id"] == "LAB-03")
        bad = json.loads(json.dumps(raw))
        bad_case = next(c for c in bad["cases"] if c["case_id"] == "LAB-03")
        bad_case["rival_expected"][0]["also"].append(dict(case["rival_expected"][0]["oracle"]))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "corpus.json"
            path.write_text(json.dumps(bad), encoding="utf-8")
            with self.assertRaisesRegex(RecordError, "ambiguity's own field"):
                load_corpus(path, config.spec)


class SignedDerivationRulesTests(unittest.TestCase):
    """The derivation checker behind the signed-derivations keys: hand-worked dossiers and monotonicity."""

    @classmethod
    def setUpClass(cls) -> None:
        import importlib.util
        spec = importlib.util.spec_from_file_location("gen_signed", ROOT / "tools" / "gen_signed_derivations_corpus.py")
        cls.gen = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.gen)

    def test_hand_worked_dossiers(self) -> None:
        g = self.gen; A = g.A; M = ["m1", "m2", "m3"]
        self.assertEqual(g.derive(("all", "P"), {"P(m1)": g.POS, "P(m2)": g.POS, "P(m3)": g.POS}, M, False), (False, False), "no universal from finitely many positives")
        self.assertEqual(g.derive(("all", "P"), {"P(m1)": g.POS, "P(m2)": g.POS, "P(m3)": g.POS}, M, True), (True, False))
        self.assertEqual(g.derive(("all", "P"), {"P(m1)": g.NEG}, M, False), (False, True), "one counterexample refutes")
        self.assertEqual(g.derive(("some", "P"), {"P(m1)": g.NEG, "P(m2)": g.NEG, "P(m3)": g.NEG}, M, False), (False, False))
        self.assertEqual(g.derive(("some", "P"), {"P(m1)": g.NEG, "P(m2)": g.NEG, "P(m3)": g.NEG}, M, True), (False, True))
        self.assertEqual(g.derive(("and", A("p"), A("q")), {"p": g.POS}, [], True, searches=("q",)), (False, False), "a failed search is not a case")
        self.assertEqual(g.derive(("and", A("p"), A("q")), {"p": g.POS}, [], True, searches=("q",), search_counts=True), (False, True))
        self.assertEqual(g.derive(("not", A("p")), {"p": g.NEG}, [], True), (True, False))
        self.assertEqual(g.derive(("not", ("all", "P")), {"P(m2)": g.NEG}, M, False), (True, False))
        self.assertEqual(g.derive(("or", A("p"), A("q")), {"p": g.NEG, "q": g.NEG}, [], True), (False, True))
        both = {"p": g.BOTH, "q": g.POS}
        self.assertEqual(g.derive(("and", A("p"), A("q")), both, [], True), (True, True))
        self.assertEqual(g.derive(("and", A("p"), A("q")), both, [], True, clean=True), (False, False), "no derivation free of the contested leaf")
        self.assertEqual(g.blocked_by(("all", "P"), {"P(m1)": g.POS, "P(m2)": g.POS, "P(m3)": g.POS}, M, False, "positive"), "range_not_complete")
        self.assertEqual(g.blocked_by(("all", "P"), {"P(m1)": g.POS, "P(m2)": g.NEG}, M, False, "positive"), "missing_leaf_case")
        self.assertEqual(g.blocked_by(("all", "P"), {"P(m1)": g.POS}, M, True, "positive"), "missing_leaf_case")

    def test_adding_cases_or_completeness_never_removes_a_derivation(self) -> None:
        import itertools, random
        g = self.gen; A = g.A; M = ["m1", "m2", "m3"]
        rng = random.Random(7)
        shapes = [("and", A("p"), A("q")), ("or", A("p"), A("q")), ("not", ("and", A("p"), A("q"))), ("all", "P"), ("some", "P"), ("all", ("or", "P", "Q")), ("not", ("all", "P"))]
        for _ in range(300):
            formula = rng.choice(shapes)
            names = g.leaves_of(formula, M)
            cases = {n: rng.choice([g.POS, g.NEG, g.NONE, g.BOTH]) for n in names}
            complete = rng.choice([True, False])
            before = g.derive(formula, cases, M, complete)
            richer = {n: tuple(set(cases[n]) | set(rng.choice([g.POS, g.NEG, g.NONE]))) for n in names}
            after = g.derive(formula, richer, M, complete or rng.choice([True, False]))
            self.assertTrue(all(b <= a for b, a in zip(before, after)), (formula, cases, richer))
            # a clean derivation is a derivation
            clean = g.derive(formula, cases, M, complete, clean=True)
            self.assertTrue(all(c <= b for c, b in zip(clean, before)))


class FailClosedGuardTests(unittest.TestCase):
    """Refusal sites the deletion sweep found the suite never reached (H26): the constitution's own guards."""

    LEAVE = ROOT / "forge" / "conformance" / "runs" / "leave-request"

    def _run_dict(self):
        from creib.forge.conformance.records import _load_canonical
        path = sorted(self.LEAVE.glob("run.*.json"))[0]
        return path, _load_canonical(path)

    def test_a_run_record_cannot_promote(self) -> None:
        import dataclasses
        from creib.errors import PolicyViolation
        from creib.forge.conformance.records import run_from_dict
        path, record = self._run_dict()
        loaded = load_run(path)
        # In code: the record type refuses to be built with any promoting value.
        for key, value, kind in (
            ("overall_status", "PASSED", PolicyViolation),
            ("route", "DONE", PolicyViolation),
            ("epistemic_limit", "Enough passes confirm the model.", PolicyViolation),
            ("scope_label", "CONFIRMED", PolicyViolation),
            ("executor_kind", "oracle", RecordError),
        ):
            with self.assertRaises(kind, msg=key):
                dataclasses.replace(loaded, **{key: value})
        # On disk: the schema refuses the same values before the type is built.
        for key, value in (("overall_status", "PASSED"), ("route", "DONE")):
            tampered = json.loads(json.dumps(record)); tampered[key] = value
            with self.assertRaises(RecordError, msg=key):
                run_from_dict(tampered)

    def test_a_run_record_is_tamper_evident(self) -> None:
        from creib.forge.conformance.records import run_from_dict
        _, record = self._run_dict()
        header = json.loads(json.dumps(record)); header["model"] = header["model"] + "x"
        with self.assertRaisesRegex(RecordError, "run_id does not replay"):
            run_from_dict(header)
        body = json.loads(json.dumps(record)); body["observations_with_live_loci"] = int(body["observations_with_live_loci"]) + 1
        with self.assertRaisesRegex(RecordError, "content_digest does not replay"):
            run_from_dict(body)

    def test_a_record_file_must_be_canonical_bytes(self) -> None:
        path, record = self._run_dict()
        with tempfile.TemporaryDirectory() as directory:
            pretty = Path(directory) / path.name
            pretty.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(RecordError, "not canonical"):
                load_run(pretty)

    def test_an_observation_must_carry_a_digest_exactly_when_it_carries_a_response_and_a_canonical_parse(self) -> None:
        import dataclasses
        from creib.forge.conformance.records import build_observation, observation_from_dict
        loaded = next(o for o in load_observation_directory(self.LEAVE) if o.response is not None)
        fields = {f.name: getattr(loaded, f.name) for f in dataclasses.fields(loaded) if f.name != "observation_id"}
        # A record whose id replays but whose digest is missing reaches the presence guard, not the id guard.
        no_digest = build_observation(**{**fields, "request_digest": None})
        with self.assertRaisesRegex(RecordError, "request digest exactly when"):
            observation_from_dict(no_digest.to_dict())
        # The scoring parser checks the canonical text before the id is rebuilt, so a dict tamper reaches it.
        uncanonical = loaded.to_dict()
        uncanonical["scoring"]["parsed_output_canonical"] = " " + str(uncanonical["scoring"]["parsed_output_canonical"])
        with self.assertRaisesRegex(RecordError, "not canonical"):
            observation_from_dict(uncanonical)

    def test_routing_records_keep_the_route_and_the_vocabularies(self) -> None:
        from creib.errors import PolicyViolation
        from creib.forge.conformance.routing import routing_from_dict
        good = {"live_loci": [{"locus": "CANDIDATE", "reason": "x"}, {"locus": "TEST", "reason": "y"}], "route": "AWAITING_HUMAN_TRIAGE", "triggers": ["MISMATCH"], "unrefuted_for_variant": False, "format_enforced_by_server": None}
        routing_from_dict(good)
        with self.assertRaises(PolicyViolation):
            routing_from_dict({**good, "route": "RESOLVED"})
        with self.assertRaisesRegex(RecordError, "not a known locus"):
            routing_from_dict({**good, "live_loci": [{"locus": "MODEL", "reason": "x"}]})
        with self.assertRaisesRegex(RecordError, "unknown trigger"):
            routing_from_dict({**good, "triggers": ["WRONG"]})

    def test_a_model_call_never_routes_to_a_single_locus_and_every_trigger_has_a_rule(self) -> None:
        from unittest import mock
        from creib.errors import PolicyViolation
        from creib.forge.conformance import routing as routing_module
        variant = _variant(Family.BASELINE, "ORD-001")
        scoring = score(variant, response_from_content(json.dumps({**_correct_output("ORD-001"), "site": "elsewhere"})), refusal_phrases=_CONFIG.spec.refusal_phrases)
        self.assertIn("MISMATCH", [v.verdict for v in scoring.field_verdicts])

        class OneLocus:
            loci = (("CANDIDATE", "only the model"),)
            def applies(self, trigger, family):
                return trigger == "MISMATCH"

        with mock.patch.object(routing_module, "ROUTING_TABLE", (OneLocus(),)):
            with self.assertRaisesRegex(PolicyViolation, "single locus"):
                routing_module.route(variant, scoring, format_sent=False)
        with mock.patch.object(routing_module, "ROUTING_TABLE", ()):
            with self.assertRaisesRegex(RecordError, "no rule for trigger"):
                routing_module.route(variant, scoring, format_sent=False)

    def test_reports_and_comparisons_refuse_an_observation_from_another_run(self) -> None:
        from creib.forge.conformance.compare import compare_runs
        observations = load_observation_directory(self.LEAVE)
        runs = sorted((load_run(p) for p in self.LEAVE.glob("run.*.json")), key=lambda r: (r.model, r.created_on))
        first = runs[0]
        foreign = next(o for o in observations if o.run_id != first.run_id)
        import dataclasses
        by_id = {o.observation_id: o for o in observations}
        by_id[first.observation_ids[0]] = dataclasses.replace(foreign, observation_id=first.observation_ids[0])
        with self.assertRaisesRegex(RecordError, "belongs to a different run"):
            build_report([first], list(by_id.values()))
        other = next(r for r in runs if r.model == first.model and r.run_id != first.run_id)
        with self.assertRaisesRegex(RecordError, "belongs to a different run"):
            compare_runs(first, other, list(by_id.values()))

    def test_run_pilot_refuses_an_undeclared_model_no_families_and_a_bad_limit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            common = dict(spec=_CONFIG.spec, corpus=_CORPUS, plan=_PLAN, executor=_fake(), executor_kind="fake", output_dir=Path(directory), created_on=CREATED_ON)
            with self.assertRaisesRegex(RecordError, "not declared"):
                run_pilot(model="nobody:1b", families=(Family.BASELINE,), **common)
            with self.assertRaisesRegex(RecordError, "no families"):
                run_pilot(model="gpt-oss:20b", families=(), **common)
            with self.assertRaisesRegex(RecordError, "limit must be"):
                run_pilot(model="gpt-oss:20b", families=(Family.BASELINE,), limit=0, **common)


class CompareTests(unittest.TestCase):
    """Two runs of one model are paired request by request; identity never consults the oracle and nothing is ranked."""

    LEAVE = ROOT / "forge" / "conformance" / "runs" / "leave-request"

    def _runs(self, model):
        runs = sorted((load_run(path) for path in self.LEAVE.glob("run.*.json") if load_run(path).model == model), key=lambda r: r.created_on)
        self.assertEqual(len(runs), 2, model)
        return runs

    def test_shared_requests_are_paired_and_accounted_for(self) -> None:
        from creib.forge.conformance.compare import compare_runs, render_compare_markdown
        observations = load_observation_directory(self.LEAVE)
        earlier, later = self._runs("gpt-oss:120b")
        comparison = compare_runs(earlier, later, observations)
        self.assertEqual(comparison["left"]["run_id"], earlier.run_id)
        self.assertEqual(comparison["shared_requests"], 2, "the later run repeated the two baseline requests only")
        self.assertEqual(comparison["only_left"], 4)
        self.assertEqual(comparison["only_right"], 0)
        self.assertEqual(comparison["identical"] + comparison["differing"] + comparison["not_comparable"], comparison["shared_requests"])
        self.assertEqual(sum(r["shared"] for r in comparison["by_family"]), comparison["shared_requests"])
        self.assertEqual({r["family"] for r in comparison["by_family"]}, {"BASELINE"})
        self.assertEqual(sum(e["fields"] != [] for e in comparison["examples"]), comparison["differing"])
        self.assertEqual(comparison["left"]["repeat_floor"]["repeats"], 0, "no repeats were configured for that run")
        # symmetry of the pairing: swapping the runs swaps the sides and nothing else
        swapped = compare_runs(later, earlier, observations)
        self.assertEqual((swapped["shared_requests"], swapped["identical"], swapped["differing"]), (comparison["shared_requests"], comparison["identical"], comparison["differing"]))
        self.assertEqual(swapped["only_left"], comparison["only_right"])
        text = render_compare_markdown(comparison)
        self.assertTrue(text.rstrip().endswith(NON_INDUCTIVE_LIMIT))
        import re
        for word in ("score", "scores", "best", "worst", "accuracy", "ranking"):
            self.assertIsNone(re.search(rf"\b{word}\b", text.lower()), word)
        self.assertIn("a difference is drift, not a wrong answer", text)

    def test_field_differences_and_verdict_moves_are_counted_by_field(self) -> None:
        from creib.forge.conformance.compare import compare_runs
        observations = load_observation_directory(self.LEAVE)
        for model in ("nemotron-3-nano:30b", "deepseek-v4-flash:0731"):
            earlier, later = self._runs(model)
            comparison = compare_runs(earlier, later, observations)
            self.assertEqual(comparison["shared_requests"], 2)
            counted = sum(r["count"] for r in comparison["differing_fields"])
            listed = sum(len(e["fields"]) for e in comparison["examples"])
            self.assertEqual(counted, listed, "every differing field of every differing pair is counted once")
            for move in comparison["field_verdict_moves"]:
                self.assertNotEqual(move["left"], move["right"])
            if comparison["differing"] == 0:
                self.assertEqual(comparison["differing_fields"], [])

    def test_different_models_and_the_same_run_are_refused(self) -> None:
        from creib.forge.conformance.compare import compare_runs
        observations = load_observation_directory(self.LEAVE)
        gpt = self._runs("gpt-oss:120b")[0]
        nemotron = self._runs("nemotron-3-nano:30b")[0]
        with self.assertRaisesRegex(RecordError, "different models"):
            compare_runs(gpt, nemotron, observations)
        with self.assertRaisesRegex(RecordError, "two different runs"):
            compare_runs(gpt, gpt, observations)
        with self.assertRaisesRegex(RecordError, "was not supplied"):
            compare_runs(gpt, self._runs("gpt-oss:120b")[1], [])

    def test_cli_compare_runs_and_writes_markdown(self) -> None:
        earlier, later = self._runs("gpt-oss:120b")
        paths = {load_run(p).run_id: p for p in self.LEAVE.glob("run.*.json")}
        with tempfile.TemporaryDirectory() as directory:
            markdown = Path(directory) / "compare.md"
            completed = subprocess.run(
                [sys.executable, str(TOOL), "compare", "--run", str(paths[earlier.run_id]), "--run", str(paths[later.run_id]), "--observations-dir", str(self.LEAVE), "--markdown", str(markdown)],
                capture_output=True, text=True, env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            emitted = json.loads(completed.stdout.strip().splitlines()[-1])
            self.assertEqual(emitted["shared_requests"], 2)
            self.assertIn("epistemic_limit", emitted)
            self.assertTrue(markdown.exists())
            one = subprocess.run([sys.executable, str(TOOL), "compare", "--run", str(paths[earlier.run_id]), "--observations-dir", str(self.LEAVE)], capture_output=True, text=True, env={**os.environ, "PYTHONPATH": str(ROOT / "src")})
            self.assertNotEqual(one.returncode, 0)


class AppraisalTests(unittest.TestCase):
    """Readings a refutation rests on are labelled in, out, or undecided; refutations become usable, contested, or defeated."""

    APPRAISAL = ROOT / "forge" / "conformance" / "pilots" / "travel-claim" / "appraisal.json"
    CLAIMS = ROOT / "forge" / "conformance" / "pilots" / "travel-claim" / "claims.json"

    def _arg(self, aid, readiness="PASS", essential=(), attacks=(), supports=None):
        from creib.forge.conformance.appraisal import Argument
        return Argument(argument_id=aid, statement=aid, kind="other", supports=supports, essential=tuple(essential), attacks=tuple(attacks), readiness=readiness, readiness_reason="test", register=None)

    def test_labelling_policy(self) -> None:
        from creib.forge.conformance.appraisal import appraise
        labels = appraise((self._arg("a"), self._arg("b", attacks=["a"]), self._arg("c", readiness="FAIL"), self._arg("d", essential=["c"]), self._arg("e", readiness="UNKNOWN"), self._arg("f", essential=["e"])))
        self.assertEqual(labels.of("b"), "in"); self.assertEqual(labels.of("a"), "out", "attacked by an in argument")
        self.assertEqual(labels.of("c"), "out"); self.assertEqual(labels.of("d"), "out", "an essential argument is out")
        self.assertEqual(labels.of("e"), "undecided", "an unknown check never becomes in by being unattacked")
        self.assertEqual(labels.of("f"), "undecided", "an undecided essential argument blocks its dependent")
        # mutual attack stays undecided; an external defeater resolves it; a support cycle does not bootstrap
        mutual = appraise((self._arg("x", attacks=["y"]), self._arg("y", attacks=["x"])))
        self.assertEqual((mutual.of("x"), mutual.of("y")), ("undecided", "undecided"))
        resolved = appraise((self._arg("x", attacks=["y"]), self._arg("y", attacks=["x"]), self._arg("z", attacks=["x"])))
        self.assertEqual((resolved.of("z"), resolved.of("x"), resolved.of("y")), ("in", "out", "in"))
        cycle = appraise((self._arg("p", essential=["q"]), self._arg("q", essential=["p"])))
        self.assertEqual((cycle.of("p"), cycle.of("q")), ("undecided", "undecided"))
        # reinstatement: a criticism of the criticism restores the reading
        chain = appraise((self._arg("reading"), self._arg("crit", attacks=["reading"]), self._arg("counter", attacks=["crit"])))
        self.assertEqual((chain.of("reading"), chain.of("crit"), chain.of("counter")), ("in", "out", "in"))
        with self.assertRaisesRegex(RecordError, "unknown argument"):
            appraise((self._arg("lone", attacks=["ghost"]),))
        with self.assertRaisesRegex(RecordError, "itself"):
            appraise((self._arg("self", essential=["self"]),))

    def test_labels_are_the_least_fixed_point_on_every_two_node_graph_and_on_sampled_larger_ones(self) -> None:
        """Every two-node graph (4 essential edge sets, 16 attack edge sets, 9 readiness assignments: 576 cases)
        and 150 seeded random graphs of three or four nodes: the iterative labels are closed under the two
        rules and contained in every other closed labelling. Self-support is refused by the loader, which is
        why the two-node count is 576 and not 2,304."""
        from itertools import product
        import random
        from creib.forge.conformance.appraisal import appraise

        def closed(args, inside, outside):
            attackers = {a.argument_id: {b.argument_id for b in args if a.argument_id in b.attacks} for a in args}
            for a in args:
                should_in = a.readiness == "PASS" and set(a.essential) <= inside and attackers[a.argument_id] <= outside
                should_out = a.readiness == "FAIL" or bool(set(a.essential) & outside) or bool(attackers[a.argument_id] & inside)
                if (should_in and a.argument_id not in inside) or (should_out and a.argument_id not in outside):
                    return False
            return True

        def check(args):
            labels = appraise(args)
            ids = [a.argument_id for a in args]
            self.assertTrue(closed(args, set(labels.inside), set(labels.outside)))
            for assignment in product(("in", "out", "undecided"), repeat=len(ids)):
                inside = {i for i, l in zip(ids, assignment) if l == "in"}
                outside = {i for i, l in zip(ids, assignment) if l == "out"}
                if closed(args, inside, outside):
                    self.assertTrue(labels.inside <= inside and labels.outside <= outside, (ids, assignment))

        pairs = [("a", "b"), ("b", "a")]
        loops = [("a", "a"), ("b", "b")]
        count = 0
        for ess_bits, att_bits, ready in product(range(4), range(16), product(("PASS", "FAIL", "UNKNOWN"), repeat=2)):
            essential = {x: [] for x in "ab"}; attacks = {x: [] for x in "ab"}
            for bit, (src, dst) in enumerate(pairs):
                if ess_bits >> bit & 1:
                    essential[src].append(dst)
            for bit, (src, dst) in enumerate(pairs + loops):
                if att_bits >> bit & 1:
                    attacks[src].append(dst)
            args = tuple(self._arg(x, readiness=r, essential=essential[x], attacks=attacks[x]) for x, r in zip("ab", ready))
            check(args); count += 1
        self.assertEqual(count, 576)
        rng = random.Random(7)
        for _ in range(150):
            ids = [f"n{i}" for i in range(rng.randint(3, 4))]
            args = tuple(
                self._arg(
                    x,
                    readiness=rng.choice(("PASS", "PASS", "FAIL", "UNKNOWN")),
                    essential=[y for y in ids if y != x and rng.random() < 0.25],
                    attacks=[y for y in ids if rng.random() < 0.25],
                )
                for x in ids
            )
            check(args)

    def test_pilot_appraisal_loads_and_classes_refutations(self) -> None:
        from creib.forge.conformance.appraisal import Appraisal, load_appraisal
        from creib.forge.conformance.claims import evaluate_claims, load_claims
        appraisal = Appraisal.build(load_appraisal(self.APPRAISAL))
        self.assertEqual(appraisal.labels.of("C-H13-AMBIGUOUS"), "in")
        self.assertEqual(appraisal.labels.of("R-BND104-NIGHTLY-R1"), "out")
        self.assertEqual(appraisal.labels.of("R-TRV005-CLIENT-VISIT"), "undecided")
        # round-one records: the BND-104 total refutations rest on a defeated reading
        observations = load_observation_directory(ROOT / "forge" / "conformance" / "runs" / "travel-claim")
        bnd104 = [o for o in observations if o.variant.base_case_id == "BND-104" and any(v.field == "total_claimed_cents" and v.verdict == "MISMATCH" for v in o.scoring.field_verdicts)]
        self.assertTrue(bnd104)
        self.assertTrue(all(appraisal.standing_of(o) == "defeated" for o in bnd104))
        self.assertTrue(all("R-BND104-NIGHTLY-R1" in appraisal.readings_of(o) for o in bnd104))
        # a conjecture about a different field, or about a trigger, does not rest on that reading
        self.assertTrue(all(appraisal.standing_of(o, frozenset({"destination_city"}), frozenset()) == "usable" for o in bnd104))
        self.assertTrue(all(appraisal.standing_of(o, frozenset(), frozenset({"EXTRA_FIELD"})) == "usable" for o in bnd104))
        from creib.forge.conformance.claims import condition_footprint
        self.assertEqual(condition_footprint({"trigger": "EXTRA_FIELD"}), (frozenset(), frozenset({"EXTRA_FIELD"})))
        self.assertEqual(condition_footprint({"field_verdict": {"verdict": "MISMATCH"}}), (None, frozenset()))
        self.assertEqual(condition_footprint({"all_of": [{"output_tokens": {"min": 1}}, {"field_verdict": {"verdict": "MISMATCH", "field": "total_claimed_cents"}}]}), (frozenset({"total_claimed_cents"}), frozenset()))
        self.assertEqual(condition_footprint({"grounding_verdict": {"verdict": "SPAN_NOT_IN_DOCUMENT"}}), (frozenset(), frozenset({"SPAN_NOT_IN_DOCUMENT"})))
        claims = tuple(c for c in load_claims(self.CLAIMS) if c.claim_id in ("ARITH-02", "READ-07", "STRUCT-01"))
        plain = {r.claim.claim_id: r for r in evaluate_claims(claims, observations)}
        judged = {r.claim.claim_id: r for r in evaluate_claims(claims, observations, appraisal)}
        self.assertEqual(plain["STRUCT-01"].status, judged["STRUCT-01"].status, "a claim resting on no argued reading is unchanged")
        self.assertEqual(plain["STRUCT-01"].refuting_usable, plain["STRUCT-01"].refuting)
        for cid, r in judged.items():
            self.assertEqual(r.refuting, r.refuting_usable + r.refuting_contested + r.refuting_defeated)
            self.assertIn(r.status, ("REFUTED", "REFUTED_ON_CONTESTED_READING", "UNREFUTED_FOR_DECLARED_SCOPE", "NOT_TESTED"))
        with tempfile.TemporaryDirectory() as directory:
            markdown = Path(directory) / "c.md"
            completed = subprocess.run(
                [sys.executable, str(TOOL), "claims", "--claims", str(self.CLAIMS), "--observations-dir", str(ROOT / "forge" / "conformance" / "runs" / "travel-claim"), "--appraisal", str(self.APPRAISAL), "--markdown", str(markdown)],
                capture_output=True, text=True, env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            summary = json.loads(completed.stdout.strip().splitlines()[-1])
            self.assertIn("appraisal_labels", summary)
            self.assertIn("REFUTED_ON_CONTESTED_READING", summary["status_counts"])
            self.assertIn("standing under the appraisal", markdown.read_text())


class HardPilotTests(unittest.TestCase):
    """The travel-claim battery: every family present, controls behave, grounding does not break model-free controls."""

    PILOT = ROOT / "forge" / "conformance" / "pilots" / "travel-claim" / "pilot.json"

    def setUp(self) -> None:
        self.config = load_pilot_config(self.PILOT)
        self.corpus = load_corpus(self.config.corpus_path, self.config.spec)
        self.plan = plan(self.config.spec, self.corpus)

    def test_plan_exercises_every_family(self) -> None:
        counts = dict(self.plan.counts)
        self.assertEqual(set(counts), {f.value for f in Family})
        self.assertEqual(counts["BASELINE"], 9)
        self.assertEqual(counts["NON_VACUITY"], 12)
        self.assertEqual(counts["RIVAL_SUBSTITUTION"], 6)
        self.assertEqual(counts["REPEAT"], 18)
        self.assertEqual(counts["CYCLE"], 54, "nine ordinary cases, two criticism sources, three cycles each")
        self.assertEqual(sum(1 for v in self.plan.variants if v.model_call), 189)

    def test_model_free_controls_are_scored_against_the_bound_form_not_the_prompt_schema(self) -> None:
        # Regression: with grounding on, the prompt schema requires companion span keys; reference
        # outputs never carry them, so the uncorrupted control was rejected and CONTROL_REJECTED fired.
        controls = [v for v in self.plan.variants if v.family is Family.NON_VACUITY]
        self.assertTrue(controls)
        for variant in controls:
            scoring = score(variant, None)
            routing = route(variant, scoring, format_sent=False)
            if variant.control_id == "C-CORRECT":
                self.assertTrue(scoring.schema_valid, variant.base_case_id)
                self.assertTrue(scoring.all_match, variant.base_case_id)
                self.assertEqual(routing.triggers, ())
            else:
                self.assertFalse(scoring.all_match, variant.control_id)
                self.assertEqual(routing.triggers, ())

    def test_prompt_carries_generated_grounding_sentences_and_nullable_abstain_fields(self) -> None:
        variant = next(v for v in self.plan.variants if v.family is Family.BOUNDARY_SHIFT and v.base_case_id == "BND-107")
        request = build_chat_request(variant, model="gemma4:31b", endpoint=self.config.spec.endpoint)
        self.assertIn("16. For each of `claimant_name`", request.user)
        self.assertIn("17. For `trip_end`, `nights_away`", request.user)
        self.assertNotIn("project_code", request.format_schema["required"])
        self.assertEqual(request.format_schema["properties"]["nights_away"]["type"], ["integer", "null"])
        self.assertIn("claimant_name_span", request.format_schema["required"])
        self.assertNotIn("cost_centre", request.format_schema["required"])

    def test_expected_abstention_case_is_judged_not_merely_tolerated(self) -> None:
        variant = next(v for v in self.plan.variants if v.family is Family.BOUNDARY_SHIFT and v.base_case_id == "BND-101")
        good = {
            "claimant_name": "Noor Haddad", "claimant_name_span": "Noor Haddad", "approver_name": "Ben Castellano", "approver_name_span": "Ben Castellano",
            "employee_id": "E-61234", "employee_id_span": "employee number 61234", "trip_start": "2025-05-20", "trip_start_span": "20 May 2025",
            "trip_end": None, "trip_end_span": None, "nights_away": None, "destination_city": "Perth", "destination_city_span": "Perth",
            "purpose": "client_visit", "total_claimed_cents": 84560, "advance_received": False, "receipts_attached": True,
            "contact_phone": "+61409771245", "contact_phone_span": "0409 771 245",
        }
        scoring = score(variant, response_from_content(json.dumps(good)))
        verdicts = {v.field: v.verdict for v in scoring.field_verdicts}
        self.assertEqual((verdicts["trip_end"], verdicts["nights_away"]), ("MATCH", "MATCH"))
        self.assertEqual(route(variant, scoring).live_loci, ())
        invented = {**good, "trip_end": "2025-05-23", "trip_end_span": "20 May 2025", "nights_away": 3}
        scoring = score(variant, response_from_content(json.dumps(invented)))
        verdicts = {v.field: v.verdict for v in scoring.field_verdicts}
        self.assertEqual((verdicts["trip_end"], verdicts["nights_away"]), ("MISMATCH", "MISMATCH"))
        self.assertIn("CANDIDATE", route(variant, scoring).loci)


class GroundingTests(unittest.TestCase):
    """Provenance spans and abstention are configuration; the default leaves behaviour unchanged."""

    TEMPLATE = ROOT / "forge" / "conformance" / "pilots" / "leave-request" / "pilot.json"

    def setUp(self) -> None:
        self.config = load_pilot_config(self.TEMPLATE)
        self.corpus = load_corpus(self.config.corpus_path, self.config.spec)
        variants = plan(self.config.spec, self.corpus).variants
        self.lr1 = next(v for v in variants if v.family is Family.BASELINE and v.base_case_id == "LR-001")
        self.lr2 = next(v for v in variants if v.family is Family.BASELINE and v.base_case_id == "LR-002")

    def _score(self, variant, output):
        return score(variant, response_from_content(json.dumps(output)))

    def test_default_mode_none_changes_nothing(self) -> None:
        incident = _variant(Family.BASELINE, "ORD-001")
        self.assertIsNone(incident.grounding)
        self.assertEqual(incident.prompt_form_schema(), incident.form_schema)
        self.assertEqual(incident.prompt_instructions(), incident.instructions)
        self.assertEqual(incident.prompt_field_order, incident.field_order)
        scoring = score(incident, response_from_content(json.dumps(_correct_output("ORD-001"))))
        self.assertEqual(scoring.grounding_verdicts, ())

    def test_prompt_schema_and_instructions_are_derived_from_config(self) -> None:
        schema = self.lr1.prompt_form_schema()
        self.assertEqual(schema["properties"]["end_date"]["type"], ["string", "null"])
        self.assertEqual(schema["properties"]["total_days"]["type"], ["integer", "null"])
        self.assertEqual(schema["properties"]["employee_name"]["type"], "string")
        self.assertIn("employee_name_span", schema["properties"])
        self.assertEqual(schema["properties"]["end_date_span"]["type"], ["string", "null"])
        self.assertIn("employee_name_span", schema["required"])
        self.assertNotIn("manager_notified_span", schema["properties"])
        self.assertEqual(self.lr1.prompt_field_order[:2], ("employee_name", "employee_name_span"))
        text = self.lr1.prompt_instructions()
        self.assertTrue(text.startswith(self.lr1.instructions.rstrip("\n")))
        self.assertIn("9. For each of `employee_name`", text)
        self.assertIn("10. For `end_date`, `total_days`: when the document does not state the value, output null", text)
        self.assertNotIn("_span", self.lr1.form_schema["properties"], "the bound form schema itself is untouched")

    def test_grounding_verdicts(self) -> None:
        good = {**LR_GOOD, **LR_SPANS}
        self.assertEqual({g.verdict for g in self._score(self.lr1, good).grounding_verdicts}, {"GROUNDED"})
        missing = {k: v for k, v in good.items() if k != "reason_span"}
        by_field = {g.field: g.verdict for g in self._score(self.lr1, missing).grounding_verdicts}
        self.assertEqual(by_field["reason"], "SPAN_MISSING")
        invented = {**good, "start_date_span": "Monday 13 September 2025"}
        by_field = {g.field: g.verdict for g in self._score(self.lr1, invented).grounding_verdicts}
        self.assertEqual(by_field["start_date"], "SPAN_NOT_IN_DOCUMENT")
        wrong_span = {**good, "employee_name_span": "Thanks,"}
        by_field = {g.field: g.verdict for g in self._score(self.lr1, wrong_span).grounding_verdicts}
        self.assertEqual(by_field["employee_name"], "VALUE_NOT_IN_SPAN")
        whitespace = {**good, "reason_span": "for a family   wedding in\nAdelaide"}
        by_field = {g.field: g.verdict for g in self._score(self.lr1, whitespace).grounding_verdicts}
        self.assertEqual(by_field["reason"], "GROUNDED", "whitespace differences are normalised")

    def test_abstention(self) -> None:
        # LR-001 states every value; abstaining is still allowed on the configured fields, and the
        # remaining spans are verbatim from that document, so nothing is flagged.
        abstained = {**LR_GOOD, **LR_SPANS, "end_date": None, "end_date_span": None, "total_days": None, "total_days_span": None}
        scoring = self._score(self.lr1, abstained)
        self.assertTrue(scoring.schema_valid)
        verdicts = {v.field: v.verdict for v in scoring.field_verdicts}
        self.assertEqual(verdicts["end_date"], "NOT_SCORED")
        grounding = {g.field: g.verdict for g in scoring.grounding_verdicts}
        self.assertEqual(grounding["end_date"], "ABSTAINED")
        self.assertEqual(grounding["total_days"], "ABSTAINED")
        self.assertEqual(route(self.lr1, scoring).live_loci, ())
        # Against LR-002 (Tom's email) the same spans are not in the document: invented provenance is flagged.
        flagged = route(self.lr2, self._score(self.lr2, abstained))
        self.assertIn("SPAN_NOT_IN_DOCUMENT", flagged.triggers)
        # null on a field that may not abstain is a type violation, as before
        not_allowed = {**LR_GOOD, **LR_SPANS, "employee_name": None, "employee_name_span": None}
        verdicts = {v.field: v.verdict for v in self._score(self.lr1, not_allowed).field_verdicts}
        self.assertEqual(verdicts["employee_name"], "TYPE_VIOLATION")

    def test_expected_abstention_is_an_answer_key_entry(self) -> None:
        # An any_of oracle whose values include null says "the document does not state this":
        # abstaining matches it, and a value where abstention was expected is a mismatch.
        from creib.forge.conformance.corpus import Oracle
        expected = tuple(
            Oracle(field=o.field, kind="any_of", value=None, values=(None,), pattern=None, oracle_status="source_scoped", rationale="not stated")
            if o.field in ("end_date", "total_days") else o
            for o in self.lr2.expected
        )
        variant = make_variant(**{**{k: getattr(self.lr2, k) for k in self.lr2.__dataclass_fields__ if k != "variant_id"}, "expected": expected})
        abstained = {**LR_GOOD, **LR_SPANS, "employee_name": "Tom Nguyen", "employee_name_span": "Tom Nguyen", "end_date": None, "end_date_span": None, "total_days": None, "total_days_span": None}
        verdicts = {v.field: v.verdict for v in self._score(variant, abstained).field_verdicts}
        self.assertEqual((verdicts["end_date"], verdicts["total_days"]), ("MATCH", "MATCH"))
        invented = {**abstained, "end_date": "2025-11-07", "end_date_span": "Monday 3 November 2025", "total_days": 5, "total_days_span": "within the week"}
        scoring = self._score(variant, invented)
        verdicts = {v.field: v.verdict for v in scoring.field_verdicts}
        self.assertEqual((verdicts["end_date"], verdicts["total_days"]), ("MISMATCH", "MISMATCH"))
        self.assertIn("CANDIDATE", route(variant, scoring).loci)
        # A null against an oracle that does not admit it is still a mismatch.
        strict = make_variant(**{**{k: getattr(self.lr2, k) for k in self.lr2.__dataclass_fields__ if k != "variant_id"}, "expected": tuple(
            Oracle(field=o.field, kind="exact", value="2025-11-07", values=None, pattern=None, oracle_status="source_scoped", rationale="x") if o.field == "end_date" else o for o in self.lr2.expected)})
        self.assertEqual({v.field: v.verdict for v in self._score(strict, abstained).field_verdicts}["end_date"], "MISMATCH")

    def test_round_trip_of_an_abstained_baseline_materialises_reloads_and_scores(self) -> None:
        # Regression: the first live grounding run wrote records whose ROUND_TRIP variants carried an
        # exact oracle with a null value (the baseline had abstained); every record then failed to reload.
        planned = next(v for v in plan(self.config.spec, self.corpus).variants if v.family is Family.ROUND_TRIP and v.base_case_id == "LR-002")
        baseline_output = {
            **LR_GOOD, **LR_SPANS, "employee_name": "Tom Nguyen", "employee_name_span": "Tom Nguyen",
            "end_date": None, "end_date_span": None, "total_days": None, "total_days_span": None,
        }
        materialised = materialize_round_trip(planned, baseline_output)
        kinds = {o.field: o.kind for o in materialised.expected}
        self.assertEqual((kinds["end_date"], kinds["total_days"], kinds["employee_name"]), ("unknown", "unknown", "exact"))
        self.assertIn("End date: not stated", materialised.input_document)
        self.assertIsNotNone(materialised.grounding, "grounding configuration survives materialisation")
        self.assertEqual(materialised.prompt_form_schema()["properties"]["end_date"]["type"], ["string", "null"])
        rebuilt = variant_from_dict(loads_strict(canonical_bytes(materialised.to_dict()).decode("utf-8")))
        self.assertEqual(rebuilt.variant_id, materialised.variant_id)
        # A stable re-fill (same nulls; spans quoted from the rendered document) raises nothing.
        stable = {
            "employee_name": "Tom Nguyen", "employee_name_span": "Tom Nguyen", "leave_type": "annual", "leave_type_span": "annual",
            "start_date": "2025-10-13", "start_date_span": "2025-10-13", "end_date": None, "end_date_span": None,
            "total_days": None, "total_days_span": None, "reason": "Family wedding in Adelaide.",
            "reason_span": "Family wedding in Adelaide.", "manager_notified": True,
        }
        scoring = score(materialised, response_from_content(json.dumps(stable)), baseline_output=baseline_output)
        self.assertIs(scoring.changed_vs_baseline, False)
        self.assertEqual(route(materialised, scoring).triggers, ())
        # Filling a value the baseline abstained on is recorded as a change against the baseline, not judged.
        drifted = {**stable, "end_date": "2025-10-17", "end_date_span": "2025-10-13"}
        scoring = score(materialised, response_from_content(json.dumps(drifted)), baseline_output=baseline_output)
        self.assertIs(scoring.changed_vs_baseline, True)
        self.assertEqual({v.field: v.verdict for v in scoring.field_verdicts}["end_date"], "NOT_SCORED")
        # Different provenance wording alone is not a change in the filled values.
        reworded = {**stable, "reason_span": "Reason: Family wedding in Adelaide."}
        self.assertIs(score(materialised, response_from_content(json.dumps(reworded)), baseline_output=baseline_output).changed_vs_baseline, False)

    def test_abstaining_against_a_declared_expectation_is_a_mismatch(self) -> None:
        import dataclasses
        from creib.forge.conformance.corpus import Oracle

        expecting = tuple(
            dataclasses.replace(o, kind="exact", value="2025-10-17", oracle_status="source_scoped", rationale="stated") if o.field == "end_date" else o
            for o in self.lr1.expected
        )
        variant = dataclasses.replace(self.lr1, expected=expecting)
        abstained = {**LR_GOOD, **LR_SPANS, "end_date": None, "end_date_span": None}
        verdicts = {v.field: v.verdict for v in score(variant, response_from_content(json.dumps(abstained))).field_verdicts}
        self.assertEqual(verdicts["end_date"], "MISMATCH")

    def test_grounding_criticisms_route_plurally_and_are_recorded(self) -> None:
        invented = {**LR_GOOD, **LR_SPANS, "start_date_span": "Monday 13 September 2025"}
        scoring = self._score(self.lr1, invented)
        routing = route(self.lr1, scoring)
        self.assertIn("SPAN_NOT_IN_DOCUMENT", routing.triggers)
        self.assertEqual(set(routing.loci), {"CANDIDATE", "TEST", "SCOPE"})
        with tempfile.TemporaryDirectory() as directory:
            result = run_pilot(
                spec=self.config.spec, corpus=self.corpus, plan=plan(self.config.spec, self.corpus), model="gpt-oss:120b",
                executor=FakeExecutor(lambda req: response_from_content(json.dumps(invented))), executor_kind="fake",
                output_dir=Path(directory), created_on=CREATED_ON, families=(Family.BASELINE,), limit=1,
            )
            self.assertEqual(result.run_record.scope_label, "REFUTED_CASES_PRESENT")
            reloaded = load_observation_directory(Path(directory))[0]
            self.assertEqual({g.field: g.verdict for g in reloaded.scoring.grounding_verdicts}["start_date"], "SPAN_NOT_IN_DOCUMENT")
            completed = subprocess.run(
                [sys.executable, str(TOOL), "evidence", "--observations-dir", directory, "--trigger", "SPAN_NOT_IN_DOCUMENT"],
                capture_output=True, text=True, env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            row = json.loads(completed.stdout.splitlines()[0])
            self.assertEqual((row["model"], row["trigger"], row["count"]), ("gpt-oss:120b", "SPAN_NOT_IN_DOCUMENT", 1))

    def test_deleting_a_field_drops_its_companion(self) -> None:
        import dataclasses
        from creib.forge.conformance.spec import Grounding

        deletion = _variant(Family.DELETION, "ORD-001")
        grounded = dataclasses.replace(deletion, grounding=Grounding("spans", "_span", ("incident_time", "site"), ("site",), ()))
        self.assertNotIn("incident_time", grounded.field_order)
        self.assertEqual(grounded.active_span_fields, ("site",))
        self.assertNotIn("incident_time_span", grounded.prompt_form_schema()["properties"])
        self.assertIn("site_span", grounded.prompt_form_schema()["properties"])

    def test_config_validation_fails_closed(self) -> None:
        from creib.forge.conformance.spec import grounding_from_dict

        fields = ("a", "b")
        base = {"mode": "spans", "span_suffix": "_span", "span_fields": ["a"], "value_in_span_fields": [], "abstain_fields": []}
        grounding_from_dict(base, fields)
        for broken in (
            {**base, "mode": "maybe"},
            {**base, "span_suffix": "span"},
            {**base, "span_fields": ["zzz"]},
            {**base, "value_in_span_fields": ["b"]},
            {**base, "mode": "none"},
            {**base, "span_fields": [], "abstain_fields": []},
            {**base, "span_fields": ["a", "a"]},
        ):
            with self.subTest(broken=broken), self.assertRaises(RecordError):
                grounding_from_dict(broken, fields)
        with self.assertRaises(RecordError):
            grounding_from_dict(base, ("a", "a_span"))
