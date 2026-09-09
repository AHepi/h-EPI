"""Refusal sites the deletion sweep listed as surviving, each reached by a test.

``tools/refusal_sweep.py`` deletes each ``raise`` under ``src/creib`` in turn and runs the suite;
a site the suite still passes with is a refusal nothing exercises. The sweep of 9 September 2026
listed these among them, and each test below supplies the input that trips the site, so that
its deletion is noticed. Sites the sweep lists as masked by an earlier guard (the appraisal
loader's checks of ``schema_version``, ``kind`` and ``readiness``, which the JSON schema refuses
first) or as invariants no input reaches (the appraisal's fixed-point checks) are recorded in
the sweep report, not tested here: a test cannot reach them without bypassing the guard in front.
"""

from __future__ import annotations

import unittest

from creib.canonical import canonical_bytes
from creib.errors import RecordError
from creib.forge.conformance import claims as claims_module
from creib.forge.conformance.common import any_string, array_value, identifier, object_value, optional_text, text


class CanonicalProfileRefusals(unittest.TestCase):
    def test_a_non_string_object_key_is_refused(self) -> None:
        with self.assertRaisesRegex(RecordError, "non-string object key at \\$"):
            canonical_bytes({1: "one"})
        with self.assertRaisesRegex(RecordError, r"non-string object key at \$\.outer"):
            canonical_bytes({"outer": {2: "two"}})

    def test_a_value_outside_the_profile_is_refused_where_it_stands(self) -> None:
        with self.assertRaisesRegex(RecordError, r"value outside canonical profile at \$\.total: float"):
            canonical_bytes({"total": 1.5})
        with self.assertRaisesRegex(RecordError, r"value outside canonical profile at \$\[1\]: tuple"):
            canonical_bytes([1, (2, 3)])
        with self.assertRaisesRegex(RecordError, r"value outside canonical profile at \$: bytes"):
            canonical_bytes(b"raw")


class ValueHelperRefusals(unittest.TestCase):
    """The loaders' value helpers, reached directly and through a claim condition, which is not schema-checked when compiled."""

    def test_object_and_array_shapes_are_refused_by_name(self) -> None:
        with self.assertRaisesRegex(RecordError, "here must be an object"):
            object_value(["not", "an", "object"], "here")
        with self.assertRaisesRegex(RecordError, "here must be an array"):
            array_value({"not": "an array"}, "here")
        with self.assertRaisesRegex(RecordError, r"condition\.field_value must be an object"):
            claims_module.compile_condition({"field_value": "destination_city"})
        with self.assertRaisesRegex(RecordError, r"condition\.field_value\.values must be an array"):
            claims_module.compile_condition({"field_value": {"field": "destination_city", "values": "Melbourne"}})

    def test_text_must_be_non_empty_and_free_of_surrogates(self) -> None:
        with self.assertRaisesRegex(RecordError, "here must be a non-empty string"):
            text("   ", "here")
        with self.assertRaisesRegex(RecordError, "here must be a non-empty string"):
            text(7, "here")
        with self.assertRaisesRegex(RecordError, "here contains a Unicode surrogate"):
            text("bad \ud800 text", "here")
        self.assertIsNone(optional_text(None, "here"))
        with self.assertRaisesRegex(RecordError, "here contains a Unicode surrogate"):
            optional_text("\udfff", "here")
        with self.assertRaisesRegex(RecordError, r"condition\.trigger must be a non-empty string"):
            claims_module.compile_condition({"trigger": ""})

    def test_any_string_admits_empty_and_refuses_non_strings_and_surrogates(self) -> None:
        self.assertEqual(any_string("", "here"), "")
        with self.assertRaisesRegex(RecordError, "here must be a string"):
            any_string(None, "here")
        with self.assertRaisesRegex(RecordError, "here contains a Unicode surrogate"):
            any_string("x\ud83dx", "here")

    def test_an_identifier_must_be_stable(self) -> None:
        with self.assertRaisesRegex(RecordError, "here must be a stable identifier"):
            identifier("has a space", "here")
        with self.assertRaisesRegex(RecordError, "here must be a stable identifier"):
            identifier("ünstable", "here")
        self.assertEqual(identifier("TRV-001", "here"), "TRV-001")


class ClaimConditionRefusals(unittest.TestCase):
    def test_a_grounding_condition_must_name_a_verdict(self) -> None:
        with self.assertRaisesRegex(RecordError, "must name at least one grounding verdict"):
            claims_module.compile_condition({"criticised_field": {"grounding_verdict": []}})
        self.assertTrue(callable(claims_module.compile_condition({"criticised_field": {"grounding_verdict": ["GROUNDED"]}})))


if __name__ == "__main__":
    unittest.main()


# --------------------------------------------------------------------------
# The rest of the 9 September report: every surviving site an input can reach.
# --------------------------------------------------------------------------

import dataclasses
import json as _json
from pathlib import Path as _Path
import tempfile as _tempfile
from types import SimpleNamespace as _NS

from creib.forge import schema_validation
from creib.forge.conformance import ChatRequest, FakeExecutor, Family, OllamaChatExecutor, ReplayExecutor, load_corpus, load_pilot_config, plan, run_pilot, response_from_content
from creib.forge.conformance import controls as _controls, cycles as _cycles, dependence as _dependence
from creib.forge.conformance.common import (
    boolean, canonical_text, decode_utf8, field_name, file_binding, hex_digest, model_id, publish_no_clobber, rfc3339, scalar, sentence_id, unique_texts,
)
from creib.forge.conformance.executor import _reject_duplicate_keys
from creib.forge.conformance.families import Criticism, materialize_cycle, variant_from_dict
from creib.forge.conformance.oracle import parse_content
from creib.forge.conformance.prompt import build_chat_request
from creib.forge.conformance.records import build_observation, build_run_record, compute_run_id, publish_record
from creib.strict_json import load_strict, loads_strict

_ROOT = _Path(__file__).resolve().parents[1]
_TRAVEL = load_pilot_config(_ROOT / "forge" / "conformance" / "pilots" / "travel-claim" / "pilot.json")
_TRAVEL_CORPUS = load_corpus(_TRAVEL.corpus_path, _TRAVEL.spec)
_TRAVEL_PLAN = plan(_TRAVEL.spec, _TRAVEL_CORPUS)
_INCIDENT = load_pilot_config(_ROOT / "forge" / "conformance" / "pilots" / "incident-form" / "pilot.json")
_INCIDENT_CORPUS = load_corpus(_INCIDENT.corpus_path, _INCIDENT.spec)
_INCIDENT_PLAN = plan(_INCIDENT.spec, _INCIDENT_CORPUS)


def _travel_variant(family: Family, case_id: str = "TRV-001"):
    return next(v for v in _TRAVEL_PLAN.variants if v.family is family and v.base_case_id == case_id)


def _incident_run(directory: _Path):
    def respond(request: ChatRequest):
        case = next(c for c in _INCIDENT_CORPUS.cases if c.renderings[c.rendering] in request.user)
        return response_from_content(_json.dumps(dict(case.reference_output or ())))
    return run_pilot(spec=_INCIDENT.spec, corpus=_INCIDENT_CORPUS, plan=_INCIDENT_PLAN, model="gemma4:31b", executor=FakeExecutor(respond), executor_kind="fake",
                     output_dir=directory, created_on="2026-09-09T13:00:00Z", families=(Family.BASELINE,), limit=1)


class MoreValueHelperRefusals(unittest.TestCase):
    def test_each_shaped_string_helper_refuses_its_shape(self) -> None:
        for helper, value, message in (
            (field_name, "NotSnake", "must be a snake_case field name"),
            (sentence_id, "x3", "must be a sentence identifier such as S3"),
            (model_id, "bad model!", "must be a model identifier"),
            (hex_digest, "XYZ", "must be a lowercase SHA-256 hex digest"),
            (rfc3339, "2026-09-09", "must be an RFC 3339 timestamp with seconds"),
        ):
            with self.subTest(helper=helper.__name__):
                with self.assertRaisesRegex(RecordError, f"here {message}"):
                    helper(value, "here")

    def test_boolean_scalar_and_unique_texts(self) -> None:
        with self.assertRaisesRegex(RecordError, "here must be a boolean"):
            boolean("true", "here")
        with self.assertRaisesRegex(RecordError, "here must be a string, boolean, integer, or null"):
            scalar(1.5, "here")
        self.assertEqual(scalar(3, "here"), 3)
        with self.assertRaisesRegex(RecordError, "here must not contain duplicates"):
            unique_texts(["S1", "S1"], "here")


class FileGuardRefusals(unittest.TestCase):
    def test_file_binding_refuses_an_unreadable_path_and_a_path_outside_the_root(self) -> None:
        with _tempfile.TemporaryDirectory() as directory:
            root = _Path(directory)
            with self.assertRaisesRegex(RecordError, "cannot read"):
                file_binding(root, root)  # a directory cannot be read as a file
            outside = root / "outside.json"
            outside.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(RecordError, "is outside the pilot directory"):
                file_binding(outside, root / "pilot")

    def test_decode_utf8_names_the_place(self) -> None:
        with self.assertRaisesRegex(RecordError, "here is not UTF-8"):
            decode_utf8(b"\xff\xfe", "here")

    def test_publish_no_clobber_refusals(self) -> None:
        with _tempfile.TemporaryDirectory() as directory:
            root = _Path(directory)
            with self.assertRaises(TypeError):
                publish_no_clobber(str(root / "a.json"), b"{}")
            target = root / "records" / "a.json"
            publish_no_clobber(target, b"{}\n")
            with self.assertRaisesRegex(RecordError, "record path exists"):
                publish_no_clobber(target, b"{}\n")
            blocker = root / "file-not-directory"
            blocker.write_text("x", encoding="utf-8")
            with self.assertRaisesRegex(RecordError, "cannot create record directory"):
                publish_no_clobber(blocker / "under-a-file.json", b"{}\n")


class ExecutorRefusals(unittest.TestCase):
    def test_duplicate_keys_in_an_endpoint_reply_are_refused(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate JSON key in response: 'a'"):
            _json.loads('{"a": 1, "a": 2}', object_pairs_hook=_reject_duplicate_keys)

    def test_executor_configuration_guards(self) -> None:
        with self.assertRaisesRegex(RecordError, "timeout_seconds must be a positive integer"):
            OllamaChatExecutor(timeout_seconds=0)
        with self.assertRaisesRegex(RecordError, "retries must be a non-negative integer"):
            OllamaChatExecutor(retries=-1)
        with self.assertRaisesRegex(RecordError, "auth must be 'bearer' or 'none'"):
            OllamaChatExecutor(auth="basic")

    def test_a_fake_without_the_request_and_a_replay_with_a_string_path_are_refused(self) -> None:
        request = build_chat_request(_travel_variant(Family.BASELINE), model="gemma4:31b", endpoint=_TRAVEL.spec.endpoint)
        with self.assertRaisesRegex(RecordError, "FakeExecutor has no response for request"):
            FakeExecutor({}).complete(request)
        with self.assertRaises(TypeError):
            ReplayExecutor("not-a-path")


class VariantAndPromptRefusals(unittest.TestCase):
    def _cycle(self, previous: str = None, criticisms=()):
        planned = next(v for v in _TRAVEL_PLAN.variants if v.family is Family.CYCLE and v.cycle_criticism == "external")
        baseline = dict(_TRAVEL_CORPUS.case(planned.base_case_id).reference_output or ())
        return materialize_cycle(planned, canonical_text(baseline) if previous is None else previous, tuple(criticisms))

    def test_a_cycle_variant_refuses_an_unknown_criticism_source_and_an_oracle_verdict(self) -> None:
        raw = self._cycle(criticisms=(Criticism(field="claimant_name", verdict="SPAN_MISSING", detail=None),)).to_dict()
        with self.assertRaisesRegex(RecordError, "cycle_criticism 'internal' is not a known criticism source"):
            variant_from_dict({**raw, "cycle_criticism": "internal"})
        tampered = {**raw, "cycle_criticisms": [{**raw["cycle_criticisms"][0], "verdict": "MISMATCH"}]}
        with self.assertRaisesRegex(RecordError, "carries 'MISMATCH', which is not an oracle-free verdict"):
            variant_from_dict(tampered)

    def test_prompt_building_refusals(self) -> None:
        baseline = _travel_variant(Family.BASELINE)
        short = dataclasses.replace(baseline, field_order=baseline.field_order[:-1])
        with self.assertRaisesRegex(RecordError, "field_order does not cover the form schema properties"):
            build_chat_request(short, model="gemma4:31b", endpoint=_TRAVEL.spec.endpoint)
        with self.assertRaisesRegex(RecordError, "a cycle's previous answer must be a JSON object"):
            build_chat_request(self._cycle(previous='["not", "an", "object"]'), model="gemma4:31b", endpoint=_TRAVEL.spec.endpoint)
        round_trip = _travel_variant(Family.ROUND_TRIP)
        with self.assertRaisesRegex(RecordError, "has no document; materialise it first"):
            build_chat_request(round_trip, model="gemma4:31b", endpoint=_TRAVEL.spec.endpoint)


class RecordBuildingRefusals(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.directory = _tempfile.TemporaryDirectory()
        cls.result = _incident_run(_Path(cls.directory.name) / "live")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.directory.cleanup()

    def test_unknown_versions_and_orders_are_refused_when_records_are_built(self) -> None:
        observation = self.result.observations[0]
        fields = {k: getattr(observation, k) for k in observation.__dataclass_fields__ if k != "observation_id"}
        with self.assertRaisesRegex(RecordError, "unknown observation schema_version"):
            build_observation(**{**fields, "schema_version": "creib.conformance-pilot.observation.v9"})
        with self.assertRaisesRegex(RecordError, "unknown run schema_version"):
            compute_run_id({"schema_version": "creib.conformance-pilot.run.v9"})
        run = self.result.run_record
        run_fields = {k: getattr(run, k) for k in run.__dataclass_fields__ if k not in ("run_id", "content_digest")}
        with self.assertRaisesRegex(RecordError, "run order must be one of"):
            build_run_record(**{**run_fields, "order": "sideways"})

    def test_publishing_refuses_a_string_directory_and_a_second_copy(self) -> None:
        observation = self.result.observations[0]
        with self.assertRaises(TypeError):
            publish_record(observation, str(_Path(self.directory.name) / "again"))
        publish_record(observation, _Path(self.directory.name) / "again")
        with self.assertRaisesRegex(RecordError, "record path exists"):
            publish_record(observation, _Path(self.directory.name) / "again")

    def test_run_pilot_refuses_a_string_output_directory(self) -> None:
        with self.assertRaises(TypeError):
            run_pilot(spec=_INCIDENT.spec, corpus=_INCIDENT_CORPUS, plan=_INCIDENT_PLAN, model="gemma4:31b", executor=FakeExecutor({}), executor_kind="fake",
                      output_dir=str(_Path(self.directory.name) / "string"), created_on="2026-09-09T13:00:00Z", families=(Family.BASELINE,), limit=1)


class TableRefusals(unittest.TestCase):
    def test_an_observation_of_another_run_is_refused_by_every_table(self) -> None:
        run = _NS(run_id="run-a", observation_ids=("o-1",))
        by_id = {"o-1": _NS(observation_id="o-1", run_id="run-b")}
        for module in (_controls, _cycles, _dependence):
            with self.subTest(module=module.__name__):
                with self.assertRaisesRegex(RecordError, "observation o-1 belongs to a different run"):
                    module._run_observations(run, by_id)


class SchemaCatalogRefusals(unittest.TestCase):
    """A ``$ref`` that is not a string is refused by the meta-schema check before the catalogue's own guard: masked, not tested here."""

    GOOD = {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "https://example.test/good.schema.json", "type": "object"}

    def _catalog(self, files: dict[str, object]) -> None:
        with _tempfile.TemporaryDirectory() as directory:
            root = _Path(directory)
            for name, content in files.items():
                path = root / name
                if isinstance(content, bytes):
                    path.write_bytes(content)
                elif content == "DIRECTORY":
                    path.mkdir()
                else:
                    path.write_text(_json.dumps(content), encoding="utf-8")
            schema_validation.load_local_schema_catalog(root)

    def test_each_catalog_guard_names_its_reason(self) -> None:
        cases = {
            "unsupported keyword": {"a.schema.json": {**self.GOOD, "$anchor": "x"}},
            "nested \\$id is not supported": {"a.schema.json": {**self.GOOD, "properties": {"p": {"$id": "https://example.test/nested"}}}},
            "cannot read": {"a.schema.json": "DIRECTORY"},
            "JSON is not UTF-8": {"a.schema.json": b"\xff\xfe"},
            "schema must be a JSON object": {"a.schema.json": []},
            "schema must declare JSON Schema 2020-12": {"a.schema.json": {**self.GOOD, "$schema": "http://json-schema.org/draft-07/schema#"}},
            "schema must declare a non-empty \\$id": {"a.schema.json": {k: v for k, v in self.GOOD.items() if k != "$id"}},
            "invalid schema \\$id URI": {"a.schema.json": {**self.GOOD, "$id": "http://[::1"}},
            "schema \\$id must be absolute and fragment-free": {"a.schema.json": {**self.GOOD, "$id": "relative/path"}},
            "duplicate schema \\$id": {"a.schema.json": self.GOOD, "b.schema.json": self.GOOD},
        }
        for message, files in cases.items():
            with self.subTest(message=message):
                with self.assertRaisesRegex(RecordError, message):
                    self._catalog(files)

    def test_the_catalog_refuses_a_string_directory_and_an_empty_schema_name(self) -> None:
        with self.assertRaises(TypeError):
            schema_validation.load_local_schema_catalog("not-a-path")
        catalog = schema_validation.load_local_schema_catalog()
        with self.assertRaisesRegex(RecordError, "schema_name must be a non-empty string"):
            catalog.validator("")


class StrictJsonRefusals(unittest.TestCase):
    def test_a_surrogate_in_a_key_and_a_non_utf8_file_are_refused(self) -> None:
        with self.assertRaisesRegex(RecordError, "Unicode surrogate code point is forbidden in key"):
            loads_strict('{"\\ud800": 1}')
        with _tempfile.TemporaryDirectory() as directory:
            path = _Path(directory) / "bad.json"
            path.write_bytes(b"\xff\xfe{}")
            with self.assertRaisesRegex(RecordError, "JSON is not UTF-8"):
                load_strict(path)


class RecoveryConstantRefusals(unittest.TestCase):
    def test_nan_keeps_a_repeated_key_object_out_of_recovery(self) -> None:
        # With the constant refused the only candidate is passed over; without it NaN would parse as null and the object be scored.
        _parsed, verdict, _detail, _recovered = parse_content('x {"a": NaN, "a": 1}', ())
        self.assertEqual(verdict, "INVALID_JSON")
