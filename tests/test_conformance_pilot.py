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
            self.assertEqual(set(lines[-1]["status_counts"]), {"REFUTED", "UNREFUTED_FOR_DECLARED_SCOPE", "NOT_TESTED"})
            text = markdown.read_text()
            self.assertIn("`UNREFUTED_FOR_DECLARED_SCOPE` means no supplied record refuted the claim; it is not a proof.", text)
            self.assertTrue(text.rstrip().endswith(NON_INDUCTIVE_LIMIT))


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
        self.assertEqual(sum(1 for v in self.plan.variants if v.model_call), 135)

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
