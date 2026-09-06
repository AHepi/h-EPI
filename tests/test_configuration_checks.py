"""Each configuration check in the loaders is sent one bad configuration.

The refusal-site sweep (``tools/refusal_sweep.py``) found that most of the checks a pilot
author meets when writing a form, a corpus, a claims file, or an appraisal had never been
exercised by the suite: deleting the ``raise`` changed nothing the suite could see (record
H26 in ``docs/failure-modes.md``). Every test here reaches one such check with an input
that only that check refuses, and asserts the message the check gives. Checks the JSON
schema refuses first are reached through the function that carries them, so the second
guard is exercised too. A test here says the check fires on one bad input; it says nothing
about whether the check is the right one.
"""

from __future__ import annotations

import copy
import dataclasses
from pathlib import Path
import tempfile
import unittest

from creib.errors import RecordError
from creib.forge.conformance import Family, load_corpus, load_pilot_config, materialize_round_trip, plan
from creib.forge.conformance import appraisal as appraisal_module
from creib.forge.conformance import claims as claims_module
from creib.forge.conformance import corpus as corpus_module
from creib.forge.conformance import families as families_module
from creib.forge.conformance import spec as spec_module
from creib.forge.conformance.spec import Binding, build_task_spec
from creib.strict_json import loads_strict

ROOT = Path(__file__).resolve().parents[1]
PILOT_DIR = ROOT / "forge" / "conformance" / "pilots" / "incident-form"
BINDINGS = tuple(Binding(name, "0" * 64) for name in ("pilot.json", "form.schema.json", "instructions.md", "corpus.json"))

_CONFIG = load_pilot_config(PILOT_DIR / "pilot.json")
_CORPUS = load_corpus(_CONFIG.corpus_path, _CONFIG.spec)
_PLAN = plan(_CONFIG.spec, _CORPUS)


def _raw_config() -> dict:
    return loads_strict((PILOT_DIR / "pilot.json").read_text(encoding="utf-8"))


def _raw_form() -> dict:
    return loads_strict((PILOT_DIR / "form.schema.json").read_text(encoding="utf-8"))


def _instructions() -> str:
    return (PILOT_DIR / "instructions.md").read_text(encoding="utf-8")


def _raw_corpus() -> dict:
    return loads_strict((PILOT_DIR / "corpus.json").read_text(encoding="utf-8"))


def _build(config: dict | None = None, form: dict | None = None, instructions: str | None = None):
    return build_task_spec(
        raw_config=_raw_config() if config is None else config,
        form_schema_raw=_raw_form() if form is None else form,
        instructions_text=_instructions() if instructions is None else instructions,
        bindings=BINDINGS,
    )


def _parse_corpus(raw: dict, spec=None):
    return corpus_module.parse_corpus(raw, _CONFIG.spec if spec is None else spec, sha256="0" * 64)


def _oracle(**fields) -> dict:
    entry = {"field": "site", "kind": "exact", "value": "Dock 3", "values": None, "pattern": None, "oracle_status": "source_scoped", "rationale": "t"}
    entry.update(fields)
    return entry


class SpecConfigurationCheckTests(unittest.TestCase):
    def test_lookups_refuse_unknown_names(self) -> None:
        with self.assertRaisesRegex(RecordError, "unknown instruction sentence 'S99'"):
            _CONFIG.spec.sentence("S99")
        with self.assertRaisesRegex(RecordError, "unknown form field 'nope'"):
            _CONFIG.spec.obligation("nope")

    def test_grounding_checks(self) -> None:
        fields = _CONFIG.spec.field_order
        with self.assertRaisesRegex(RecordError, "grounding is missing 'span_suffix'"):
            spec_module.grounding_from_dict({"mode": "none"}, fields)
        base = {"mode": "spans", "span_suffix": "_span", "span_fields": ["site"], "value_in_span_fields": [], "abstain_fields": []}
        with self.assertRaisesRegex(RecordError, "span_relaxations must not repeat"):
            spec_module.grounding_from_dict({**base, "span_relaxations": ["case_insensitive", "case_insensitive"]}, fields)

    def test_instruction_parsing_checks(self) -> None:
        with self.assertRaisesRegex(RecordError, "unnumbered text after the first"):
            spec_module.parse_instructions("Preamble\n\n1. `site` is the place.\nnot numbered\n")
        with self.assertRaisesRegex(RecordError, "numbered consecutively; found 3"):
            spec_module.parse_instructions("Preamble\n\n1. `site` is the place.\n3. `summary` is the rest.\n")
        with self.assertRaisesRegex(RecordError, "at least one numbered sentence"):
            spec_module.parse_instructions("Preamble only\n")
        with self.assertRaisesRegex(RecordError, "canonical form"):
            spec_module.parse_instructions("Preamble\n\n\n1. `site` is the place.")

    def test_form_schema_checks(self) -> None:
        form = _raw_form()
        form["properties"]["site"]["type"] = 12
        with self.assertRaisesRegex(RecordError, "not a valid JSON Schema"):
            spec_module.validate_form_schema(form, "form_schema")
        form = _raw_form()
        form["additionalProperties"] = True
        with self.assertRaisesRegex(RecordError, "violates the pilot form profile"):
            spec_module.validate_form_schema(form, "form_schema")
        form = _raw_form()
        form["required"].append("nowhere")
        with self.assertRaisesRegex(RecordError, "required names unknown field 'nowhere'"):
            spec_module.validate_form_schema(form, "form_schema")

    def test_endpoint_kind_is_checked_after_the_schema(self) -> None:
        endpoint = _raw_config()["endpoint"]
        endpoint["kind"] = "openai-chat"
        with self.assertRaisesRegex(RecordError, "endpoint.kind must be ollama-chat"):
            spec_module.endpoint_from_dict(endpoint)

    def _control_config(self, controls: list[dict]) -> dict:
        config = _raw_config()
        config["controls"] = controls
        return config

    def test_control_checks(self) -> None:
        reference = {"control_id": "C-CORRECT", "corruption": {"kind": "none"}}
        with self.assertRaisesRegex(RecordError, "swaps unknown field 'nope'"):
            _build(self._control_config([reference, {"control_id": "C-SWAP", "corruption": {"kind": "swap_fields", "fields": ["site", "nope"]}}]))
        with self.assertRaisesRegex(RecordError, "drops 'incident_time', which is not a required field"):
            _build(self._control_config([reference, {"control_id": "C-DROP", "corruption": {"kind": "drop_required", "field": "incident_time"}}]))
        with self.assertRaisesRegex(RecordError, "extra key 'site' is already a form field"):
            _build(self._control_config([reference, {"control_id": "C-EXTRA", "corruption": {"kind": "extra_key", "key": "site", "value": "x"}}]))
        drop = {"control_id": "C-DROP", "corruption": {"kind": "drop_required", "field": "phone"}}
        with self.assertRaisesRegex(RecordError, "unique control_id"):
            _build(self._control_config([reference, drop, dict(drop)]))
        with self.assertRaisesRegex(RecordError, "one uncorrupted reference"):
            _build(self._control_config([drop]))
        with self.assertRaisesRegex(RecordError, "at least one corruption"):
            _build(self._control_config([reference]))
        # the corruption vocabulary is closed by the schema first and by the loader second
        with self.assertRaisesRegex(RecordError, "not a known corruption"):
            spec_module._controls([{"control_id": "C-X", "corruption": {"kind": "truncate"}}], _CONFIG.spec.field_order, _CONFIG.spec.required_fields)

    def test_ambiguity_checks(self) -> None:
        def with_ambiguity(entries):
            config = _raw_config()
            config["ambiguity"] = entries
            return config

        rivals = [{"label": "a", "instruction": "Read it one way."}, {"label": "b", "instruction": "Read it the other way."}]
        with self.assertRaisesRegex(RecordError, r"ambiguity\[0\] names unknown field 'nope'"):
            _build(with_ambiguity([{"field": "nope", "question": "q?", "rivals": rivals}]))
        with self.assertRaisesRegex(RecordError, "rival labels must be unique"):
            _build(with_ambiguity([{"field": "site", "question": "q?", "rivals": [rivals[0], {**rivals[1], "label": "a"}]}]))
        with self.assertRaisesRegex(RecordError, "rival instructions must differ"):
            _build(with_ambiguity([{"field": "site", "question": "q?", "rivals": [rivals[0], {**rivals[1], "instruction": rivals[0]["instruction"]}]}]))
        one = {"field": "site", "question": "q?", "rivals": rivals}
        with self.assertRaisesRegex(RecordError, "ambiguity declares the same field twice"):
            _build(with_ambiguity([one, copy.deepcopy(one)]))

    def test_load_bearing_names_a_known_sentence(self) -> None:
        config = _raw_config()
        config["load_bearing"] = ["S1", "S99"]
        with self.assertRaisesRegex(RecordError, "load_bearing names unknown sentence 'S99'"):
            _build(config)

    def test_negation_checks(self) -> None:
        def with_negation(**changes):
            config = _raw_config()
            entry = dict(config["negations"][1])  # the phone negation on S7
            entry.update(changes)
            config["negations"] = [config["negations"][0], entry]
            return config

        with self.assertRaisesRegex(RecordError, r"negations\[1\] names unknown field 'nope'"):
            _build(with_negation(field="nope"))
        with self.assertRaisesRegex(RecordError, "names unknown sentence 'S99'"):
            _build(with_negation(sentence_id="S99"))
        with self.assertRaisesRegex(RecordError, "sentence S5 is not primarily about 'phone'"):
            _build(with_negation(sentence_id="S5"))
        with self.assertRaisesRegex(RecordError, "replacement_pattern is not a valid regex"):
            _build(with_negation(replacement_pattern="("))
        with self.assertRaisesRegex(RecordError, "negations declare the same field twice"):
            _build(with_negation(field="incident_date", sentence_id="S5"))

    def test_twin_checks(self) -> None:
        config = _raw_config()
        config["twins"] = [["reporter_name", "nope"]]
        with self.assertRaisesRegex(RecordError, r"twins\[0\] names unknown field 'nope'"):
            _build(config)
        # take the field name out of its own sentence: the field is then unsourced, which a
        # plain obligation tolerates, but a twin needs a sentence primarily about it
        instructions = _instructions().replace("8. `site` is the place", "8. The location is the place")
        config = _raw_config()
        config["twins"] = [["site", "summary"]]
        with self.assertRaisesRegex(RecordError, "field 'site' has no primary instruction sentence"):
            _build(config, instructions=instructions)

    def test_pilot_path_must_be_a_path(self) -> None:
        with self.assertRaises(TypeError):
            load_pilot_config(str(PILOT_DIR / "pilot.json"))  # type: ignore[arg-type]


class CorpusConfigurationCheckTests(unittest.TestCase):
    PROPERTIES = _CONFIG.spec.form_schema["properties"]

    def _parse_oracle(self, **fields):
        return corpus_module.parse_oracle(_oracle(**fields), "o", self.PROPERTIES)

    def test_unknown_case(self) -> None:
        with self.assertRaisesRegex(RecordError, "unknown case 'nope'"):
            _CORPUS.case("nope")

    def test_oracle_shape_checks(self) -> None:
        with self.assertRaisesRegex(RecordError, "not a known oracle kind"):
            self._parse_oracle(kind="fuzzy")
        with self.assertRaisesRegex(RecordError, "must be a non-final status"):
            self._parse_oracle(oracle_status="final")
        with self.assertRaisesRegex(RecordError, "values must not be empty"):
            self._parse_oracle(kind="any_of", value=None, values=[])
        with self.assertRaisesRegex(RecordError, "exact oracle needs value only"):
            self._parse_oracle(values=["Dock 3"])
        with self.assertRaisesRegex(RecordError, "is not of form type boolean"):
            self._parse_oracle(field="injury_reported", value="yes")
        with self.assertRaisesRegex(RecordError, "regex oracle needs pattern only"):
            self._parse_oracle(kind="regex", pattern="^D", value="Dock 3")
        with self.assertRaisesRegex(RecordError, "regex oracle applies only to string fields"):
            self._parse_oracle(field="injury_reported", kind="regex", value=None, pattern="^t")
        with self.assertRaisesRegex(RecordError, "pattern is not a valid regex"):
            self._parse_oracle(kind="regex", value=None, pattern="(")
        with self.assertRaisesRegex(RecordError, "any_of oracle needs values only"):
            self._parse_oracle(kind="any_of", values=["Dock 3"])
        with self.assertRaisesRegex(RecordError, "values must be distinct"):
            self._parse_oracle(kind="any_of", value=None, values=["Dock 3", "Dock 3"])
        with self.assertRaisesRegex(RecordError, "enum oracle lists values outside the form enum"):
            self._parse_oracle(field="severity", kind="enum", value=None, values=["low", "extreme"])
        with self.assertRaisesRegex(RecordError, "unknown oracle carries no value"):
            self._parse_oracle(kind="unknown")
        with self.assertRaisesRegex(RecordError, "absent oracle carries no value"):
            self._parse_oracle(kind="absent")

    def _corpus_with(self, mutate):
        raw = _raw_corpus()
        mutate(raw)
        return _parse_corpus(raw)

    def test_case_shape_checks(self) -> None:
        # the schema closes the renderings object first; the loader is the second guard
        case = _raw_corpus()["cases"][0]
        case["renderings"]["sms"] = "short"
        with self.assertRaisesRegex(RecordError, "renderings has an unknown substrate"):
            corpus_module._parse_case(case, "cases[0]", _CONFIG.spec)

        def missing_base_rendering(raw):
            del raw["cases"][0]["renderings"]["prose"]

        with self.assertRaisesRegex(RecordError, "base rendering 'prose' has no text"):
            self._corpus_with(missing_base_rendering)

        def field_twice(raw):
            raw["cases"][0]["expected"].append(dict(raw["cases"][0]["expected"][0]))

        with self.assertRaisesRegex(RecordError, "expected lists a field twice"):
            self._corpus_with(field_twice)

        def pair_without_varied(raw):
            raw["cases"][0]["pair_of"] = "ORD-002"

        with self.assertRaisesRegex(RecordError, "must declare varied exactly when pair_of is set"):
            self._corpus_with(pair_without_varied)

        def own_pair(raw):
            raw["cases"][0]["pair_of"] = "ORD-001"
            raw["cases"][0]["varied"] = "nothing"

        with self.assertRaisesRegex(RecordError, "cannot be its own pair"):
            self._corpus_with(own_pair)

        def unknown_pair(raw):
            raw["cases"][0]["pair_of"] = "ORD-999"
            raw["cases"][0]["varied"] = "nothing"

        with self.assertRaisesRegex(RecordError, "pairs with unknown case 'ORD-999'"):
            self._corpus_with(unknown_pair)

        def duplicate_ids(raw):
            raw["cases"][1]["case_id"] = raw["cases"][0]["case_id"]

        with self.assertRaisesRegex(RecordError, "case_id values must be unique"):
            self._corpus_with(duplicate_ids)

    def test_reference_output_checks(self) -> None:
        def unknown_field(raw):
            raw["cases"][0]["reference_output"].append({"field": "nope", "value": "x"})

        with self.assertRaisesRegex(RecordError, "reference_output names unknown field 'nope'"):
            self._corpus_with(unknown_field)

        def repeated_field(raw):
            raw["cases"][0]["reference_output"].append(dict(raw["cases"][0]["reference_output"][0]))

        with self.assertRaisesRegex(RecordError, "reference_output repeats a field"):
            self._corpus_with(repeated_field)

    def test_rival_expectation_checks(self) -> None:
        def rival_on(case_index, **changes):
            def mutate(raw):
                rival = copy.deepcopy(_raw_corpus()["cases"][12]["rival_expected"][0])  # BND-004 day_first
                rival.update(changes)
                raw["cases"][case_index]["rival_expected"] = [rival]
            return mutate

        with self.assertRaisesRegex(RecordError, "names field 'site' without a declared ambiguity"):
            self._corpus_with(rival_on(0, field="site"))
        with self.assertRaisesRegex(RecordError, "label 'year_first' is not a declared rival"):
            self._corpus_with(rival_on(0, label="year_first"))
        wrong_field = dict(_raw_corpus()["cases"][12]["rival_expected"][0]["oracle"], field="site", value="Dock 3")
        with self.assertRaisesRegex(RecordError, "oracle field must be 'incident_date'"):
            self._corpus_with(rival_on(0, oracle=wrong_field))

        def repeated_pair(raw):
            raw["cases"][12]["rival_expected"].append(copy.deepcopy(raw["cases"][12]["rival_expected"][0]))

        with self.assertRaisesRegex(RecordError, r"repeats a \(field, label\) pair"):
            self._corpus_with(repeated_pair)

    def test_corpus_path_checks(self) -> None:
        with self.assertRaises(TypeError):
            load_corpus(str(_CONFIG.corpus_path), _CONFIG.spec)  # type: ignore[arg-type]
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(RecordError, "cannot read corpus"):
                load_corpus(Path(directory) / "missing.json", _CONFIG.spec)


class FamilyConfigurationCheckTests(unittest.TestCase):
    def _baseline(self):
        return next(v for v in _PLAN.variants if v.family is Family.BASELINE)

    def test_variant_guards(self) -> None:
        with self.assertRaisesRegex(RecordError, "no grounding configuration"):
            dataclasses.replace(self._baseline(), grounding=None).span_key("site")
        record = self._baseline().to_dict()
        record["family"] = "NOPE"
        with self.assertRaisesRegex(RecordError, "unknown family or expectation kind"):
            families_module.variant_from_dict(record)
        record = self._baseline().to_dict()
        record["field_order"] = record["field_order"][:-1]
        with self.assertRaisesRegex(RecordError, "field_order does not match its form schema"):
            families_module.variant_from_dict(record)
        with self.assertRaisesRegex(RecordError, "unknown variant 'nope'"):
            _PLAN.variant("nope")
        with self.assertRaisesRegex(RecordError, "only ROUND_TRIP variants"):
            materialize_round_trip(self._baseline(), {"site": "Dock 3"})
        with self.assertRaisesRegex(RecordError, "cannot render non-scalar value for site"):
            families_module.render_round_trip_document({"site": ["a", "b"]}, ("site",))

    def test_value_transforms_refuse_other_shapes(self) -> None:
        with self.assertRaisesRegex(RecordError, "needs an ISO date"):
            families_module.iso_date_to_dmy("3 April 2025")
        with self.assertRaisesRegex(RecordError, r"needs \+61 E.164"):
            families_module.e164_au_to_national_spaced("0412 345 678")

    def _spec_with_negation(self, field: str, sentence_id: str):
        config = _raw_config()
        config["negations"] = [{"field": field, "sentence_id": sentence_id, "replacement_sentence": f"`{field}` is written differently.", "replacement_pattern": "^.*$", "value_transform": "iso_date_to_dmy"}]
        spec = _build(config)
        return spec, load_corpus(_CONFIG.corpus_path, spec)

    def test_negation_refuses_oracles_it_cannot_re_express(self) -> None:
        spec, corpus = self._spec_with_negation("injury_reported", "S10")
        with self.assertRaisesRegex(RecordError, "negation of injury_reported needs a string oracle"):
            plan(spec, corpus)
        spec, corpus = self._spec_with_negation("summary", "S11")
        with self.assertRaisesRegex(RecordError, "cannot re-express a regex oracle"):
            plan(spec, corpus)

    def test_controls_need_their_fields_in_the_reference_output(self) -> None:
        def without(field: str):
            raw = _raw_corpus()
            for case in raw["cases"]:
                if case["reference_output"] is not None:
                    case["reference_output"] = [item for item in case["reference_output"] if item["field"] != field]
            return _parse_corpus(raw)

        with self.assertRaisesRegex(RecordError, "C-SWAP-DATES swaps fields absent from ORD-001 reference output"):
            plan(_CONFIG.spec, without("date_of_birth"))
        with self.assertRaisesRegex(RecordError, "C-DROP-PHONE drops a field absent from ORD-001 reference output"):
            plan(_CONFIG.spec, without("phone"))


class ClaimsConfigurationCheckTests(unittest.TestCase):
    def _claims(self, claims: list[dict]):
        return claims_module.claims_from_dict({"schema_version": claims_module.CLAIMS_SCHEMA_VERSION, "title": "t", "claims": claims})

    def _claim(self, claim_id="C-1", **fields):
        entry = {"claim_id": claim_id, "statement": "s", "kind": "never", "scope": None, "condition": {"trigger": "EXTRA_FIELD"}, "note": None}
        entry.update(fields)
        return entry

    def test_condition_checks(self) -> None:
        with self.assertRaisesRegex(RecordError, "all_of must not be empty"):
            claims_module.compile_condition({"all_of": []}, "c")
        with self.assertRaisesRegex(RecordError, "any_of must not be empty"):
            claims_module.compile_condition({"any_of": []}, "c")
        with self.assertRaisesRegex(RecordError, "'FLOATING' is not a known grounding verdict"):
            claims_module.compile_condition({"grounding_verdict": {"verdict": "FLOATING"}}, "c")

    def test_file_checks(self) -> None:
        with self.assertRaisesRegex(RecordError, "families names unknown family 'NOPE'"):
            self._claims([self._claim(scope={"families": ["NOPE"], "cases": None, "models": None, "model_call": None})])
        with self.assertRaisesRegex(RecordError, "claim_id 'C-1' repeats"):
            self._claims([self._claim(), self._claim()])
        with self.assertRaises(TypeError):
            claims_module.load_claims("claims.json")  # type: ignore[arg-type]
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(RecordError, "cannot read claims"):
                claims_module.load_claims(Path(directory) / "missing.json")


class AppraisalConfigurationCheckTests(unittest.TestCase):
    def _argument(self, argument_id="A", supports=None, **fields):
        entry = {"argument_id": argument_id, "statement": "s", "kind": "other", "supports": supports, "essential": [], "attacks": [], "readiness": "PASS", "readiness_reason": "r", "register": None}
        entry.update(fields)
        return entry

    def _appraisal(self, arguments: list[dict]):
        return appraisal_module.appraisal_from_dict({"schema_version": appraisal_module.APPRAISAL_SCHEMA_VERSION, "title": "t", "arguments": arguments})

    def test_label_lookup_and_uniqueness(self) -> None:
        argument = appraisal_module.Argument(argument_id="A", statement="s", kind="other", supports=None, essential=(), attacks=(), readiness="PASS", readiness_reason="r", register=None)
        with self.assertRaisesRegex(RecordError, "unknown argument 'B'"):
            appraisal_module.appraise((argument,)).of("B")
        with self.assertRaisesRegex(RecordError, "argument ids must be unique"):
            appraisal_module.appraise((argument, argument))

    def test_support_checks(self) -> None:
        with self.assertRaisesRegex(RecordError, "trigger 'NOPE' is not a known trigger"):
            self._appraisal([self._argument(supports={"trigger": "NOPE"})])
        with self.assertRaisesRegex(RecordError, "needs both case_id and field, or neither"):
            self._appraisal([self._argument(supports={"case_id": "ORD-001"})])
        with self.assertRaisesRegex(RecordError, "supports nothing"):
            self._appraisal([self._argument(supports={})])
        with self.assertRaisesRegex(RecordError, "not both"):
            self._appraisal([self._argument(supports={"case_id": "ORD-001", "field": "site", "trigger": "EXTRA_FIELD"})])
        # the schema refuses a repeated family first; the loader is the second guard
        with self.assertRaisesRegex(RecordError, "families repeats 'BASELINE'"):
            appraisal_module._support_from_dict({"case_id": "ORD-001", "field": "site", "families": ["BASELINE", "BASELINE"]}, "s")

    def test_file_checks(self) -> None:
        with self.assertRaises(TypeError):
            appraisal_module.load_appraisal("appraisal.json")  # type: ignore[arg-type]
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(RecordError, "cannot read appraisal"):
                appraisal_module.load_appraisal(Path(directory) / "missing.json")


if __name__ == "__main__":
    unittest.main()
