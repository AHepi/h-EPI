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
from creib.forge.generic_inquiry import _LOCUS_VALUES
from creib.forge.models import NON_INDUCTIVE_LIMIT
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

    def test_locus_vocabulary_matches_generic_inquiry(self) -> None:
        self.assertEqual(frozenset(LOCUS_VALUES), _LOCUS_VALUES)


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
            self.assertEqual(result.run_record.scope_label, "UNREFUTED_FOR_DECLARED_SCOPE")

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
