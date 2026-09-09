"""Record version 3: per-attempt timing and transport kind, the refusal flag beside a recovered
object, replay provenance, the run's sending order, and the v2 records that keep loading.

The property these tests hold the version to is that nothing written under v2 changes: a v2
record loads, replays its id under the v2 domain, and carries none of the v3 keys, while a
record written now carries the version it was written under and the keys it has information
for. The new facts are recorded, not judged: a refusal phrase beside a form is a criticism
routed to plural loci, a timing is a number the harness measured, a replay names the reply it
re-scored, and a claims evaluation refuses a reply and its replay together.
"""

from __future__ import annotations

import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

from creib.errors import RecordError
from creib.forge.conformance import (
    ChatRequest,
    FakeExecutor,
    Family,
    OllamaChatExecutor,
    ReplayExecutor,
    load_corpus,
    load_observation,
    load_pilot_config,
    load_run,
    plan,
    response_from_content,
    route,
    run_pilot,
    score,
)
from creib.forge.conformance import claims as claims_module
from creib.forge.conformance.common import OBSERVATION_SCHEMA_VERSION, OBSERVATION_SCHEMA_VERSION_V2, RUN_SCHEMA_VERSION, RUN_SCHEMA_VERSION_V2
from creib.forge.conformance.executor import _response_from_attempt, transport_error_kind
from creib.forge.conformance.records import build_observation, build_run_record
from creib.forge.conformance.runner import select_variants
from creib.strict_json import loads_strict

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "forge" / "conformance" / "pilots" / "incident-form" / "pilot.json"
RUNS = ROOT / "forge" / "conformance" / "runs"
CREATED_ON = "2026-09-08T13:00:00Z"
DUMMY_KEY = "test-key-not-a-secret"

_CONFIG = load_pilot_config(PILOT)
_CORPUS = load_corpus(_CONFIG.corpus_path, _CONFIG.spec)
_PLAN = plan(_CONFIG.spec, _CORPUS)


def _reference(case_id: str) -> dict:
    return dict(_CORPUS.case(case_id).reference_output or ())


def _fake(refuse_case: str | None = None) -> FakeExecutor:
    def respond(request: ChatRequest):
        case = next(c for c in _CORPUS.cases if c.renderings[c.rendering] in request.user)
        body = json.dumps(_reference(case.case_id) if case.reference_output else {})
        if case.case_id == refuse_case:
            return response_from_content("I'm sorry, I can't comply with that, but here is the form anyway:\n" + body)
        return response_from_content(body)
    return FakeExecutor(respond)


class VersionTests(unittest.TestCase):
    def test_committed_v2_records_load_under_v2_and_carry_no_v3_keys(self) -> None:
        run_path = sorted((RUNS / "leave-request").glob("run.*.json"))[0]
        run = load_run(run_path)
        self.assertEqual(run.schema_version, RUN_SCHEMA_VERSION_V2)
        self.assertIsNone(run.order)
        self.assertIsNone(run.shuffle_seed)
        raw = loads_strict(run_path.read_text(encoding="utf-8"))
        self.assertNotIn("order", raw)
        observation_path = sorted((RUNS / "leave-request").glob("observation.*.json"))[0]
        observation = load_observation(observation_path)
        self.assertEqual(observation.schema_version, OBSERVATION_SCHEMA_VERSION_V2)
        self.assertIsNone(observation.replayed_from)
        self.assertFalse(observation.scoring.refusal_phrase_present)
        if observation.response is not None:
            self.assertIsNone(observation.response.started_at)
        raw = loads_strict(observation_path.read_text(encoding="utf-8"))
        self.assertNotIn("replayed_from", raw)
        self.assertNotIn("refusal_phrase_present", raw["scoring"])
        with self.assertRaisesRegex(RecordError, "cannot carry replayed_from"):
            build_observation(**{**{k: getattr(observation, k) for k in observation.__dataclass_fields__ if k != "observation_id"}, "replayed_from": "0" * 64})
        with self.assertRaisesRegex(RecordError, "cannot carry order"):
            build_run_record(**{**{k: getattr(run, k) for k in run.__dataclass_fields__ if k not in ("run_id", "content_digest")}, "order": "family"})

    def test_a_new_run_is_v3_and_records_its_order(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = run_pilot(
                spec=_CONFIG.spec, corpus=_CORPUS, plan=_PLAN, model="gpt-oss:20b", executor=_fake(), executor_kind="fake",
                output_dir=Path(directory), created_on=CREATED_ON, families=(Family.BASELINE, Family.REPEAT), limit=None, order="shuffled", seed=11,
            )
            run = result.run_record
            self.assertEqual((run.schema_version, run.order, run.shuffle_seed), (RUN_SCHEMA_VERSION, "shuffled", 11))
            reloaded = load_run(Path(directory) / f"run.{run.run_id[:16]}.json")
            self.assertEqual((reloaded.order, reloaded.shuffle_seed), ("shuffled", 11))
            observation = result.observations[0]
            self.assertEqual(observation.schema_version, OBSERVATION_SCHEMA_VERSION)
            self.assertIsNone(observation.replayed_from)
            raw = loads_strict((Path(directory) / f"observation.{observation.observation_id[:16]}.json").read_text(encoding="utf-8"))
            self.assertIn("replayed_from", raw)
            self.assertNotIn("started_at", raw["response"], "a fake executor measures nothing, so the key is absent, not null")
        with self.assertRaisesRegex(RecordError, "exactly when the order is shuffled"):
            build_run_record(**{**{k: getattr(run, k) for k in run.__dataclass_fields__ if k not in ("run_id", "content_digest")}, "order": "family", "shuffle_seed": 3})

    def test_shuffled_order_is_drawn_from_the_seed_and_keeps_each_case_together(self) -> None:
        first = select_variants(_PLAN, families=(Family.BASELINE, Family.REPEAT), order="shuffled", seed=7)
        again = select_variants(_PLAN, families=(Family.BASELINE, Family.REPEAT), order="shuffled", seed=7)
        other = select_variants(_PLAN, families=(Family.BASELINE, Family.REPEAT), order="shuffled", seed=8)
        interleaved = select_variants(_PLAN, families=(Family.BASELINE, Family.REPEAT), order="interleaved")
        self.assertEqual([v.variant_id for v in first], [v.variant_id for v in again])
        self.assertNotEqual([v.variant_id for v in first], [v.variant_id for v in other])
        self.assertEqual(sorted(v.variant_id for v in first), sorted(v.variant_id for v in interleaved))
        cases = [v.base_case_id for v in first]
        self.assertEqual(cases, sorted(cases, key=cases.index), "each case's variants stay contiguous")
        for case_id in dict.fromkeys(cases):
            block = [v for v in first if v.base_case_id == case_id]
            self.assertIs(block[0].family, Family.BASELINE, "the baseline leads its case")
        with self.assertRaisesRegex(RecordError, "exactly when the order is shuffled"):
            select_variants(_PLAN, order="shuffled")
        with self.assertRaisesRegex(RecordError, "exactly when the order is shuffled"):
            select_variants(_PLAN, order="family", seed=1)
        with self.assertRaisesRegex(RecordError, "non-negative integer"):
            select_variants(_PLAN, order="shuffled", seed=-1)


class TimingAndTransportTests(unittest.TestCase):
    def test_a_live_attempt_is_stamped_and_a_failure_carries_its_kind(self) -> None:
        variant = next(v for v in _PLAN.variants if v.family is Family.BASELINE)
        from creib.forge.conformance.prompt import build_chat_request
        request = build_chat_request(variant, model="gpt-oss:20b", endpoint=_CONFIG.spec.endpoint)
        body = json.dumps({"message": {"role": "assistant", "content": "{}"}, "done": True, "done_reason": "stop", "eval_count": 3, "prompt_eval_count": 10, "total_duration": 5000000}).encode("utf-8")

        class _Reply(io.BytesIO):
            status = 200
            def __enter__(self): return self
            def __exit__(self, *exc): return False

        with patch.dict(os.environ, {"OLLAMA_API_KEY": DUMMY_KEY}), patch("urllib.request.urlopen", lambda http_request, timeout: _Reply(body)):
            response = OllamaChatExecutor(base_url="https://ollama.example", timeout_seconds=5)._attempt(request, 1)
        self.assertRegex(response.started_at or "", r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
        self.assertIsInstance(response.elapsed_ms, int)
        self.assertGreaterEqual(response.elapsed_ms or 0, 0)
        self.assertIsNone(response.transport_kind)
        record = response.to_dict()
        self.assertEqual(_response_from_attempt(record, "r").started_at, response.started_at)

        def failing(http_request, timeout):
            raise urllib.error.HTTPError(http_request.full_url, 503, "overloaded", {}, io.BytesIO(b'{"error":"busy"}'))
        with patch.dict(os.environ, {"OLLAMA_API_KEY": DUMMY_KEY}), patch("urllib.request.urlopen", failing):
            failure = OllamaChatExecutor(base_url="https://ollama.example", timeout_seconds=5)._attempt(request, 1)
        self.assertEqual((failure.transport_kind, failure.http_status), ("http_status", 503))
        self.assertIsNotNone(failure.started_at)
        with self.assertRaisesRegex(RecordError, "must be one of"):
            _response_from_attempt({**failure.to_dict(), "transport_kind": "weather"}, "r")
        self.assertEqual(transport_error_kind("TimeoutError: The read operation timed out"), ("timeout", None))
        self.assertEqual(transport_error_kind("RemoteDisconnected: Remote end closed connection without response"), ("disconnected", None))
        self.assertEqual(transport_error_kind("HTTPError: status 503: {}"), ("http_status", 503))
        self.assertEqual(transport_error_kind("ExecutorException: ValueError"), ("other", None))


class RefusalBesideAFormTests(unittest.TestCase):
    def test_a_refusal_phrase_beside_a_recovered_object_is_recorded_and_routed(self) -> None:
        variant = next(v for v in _PLAN.variants if v.family is Family.BASELINE and v.base_case_id == "ORD-001")
        content = "I'm sorry, I can't comply with that, but here is the form anyway:\n" + json.dumps(_reference("ORD-001"))
        scoring = score(variant, response_from_content(content), refusal_phrases=_CONFIG.spec.refusal_phrases)
        self.assertEqual(scoring.response_verdict, "JSON_OBJECT")
        self.assertTrue(scoring.recovered_from_prose)
        self.assertTrue(scoring.refusal_phrase_present)
        self.assertTrue(scoring.to_dict()["refusal_phrase_present"])
        routing = route(variant, scoring)
        self.assertIn("REFUSAL_SUSPECTED", routing.triggers)
        self.assertTrue({"CANDIDATE", "AUXILIARY", "TEST"} <= set(routing.loci))
        plain = score(variant, response_from_content(json.dumps(_reference("ORD-001"))), refusal_phrases=_CONFIG.spec.refusal_phrases)
        self.assertFalse(plain.refusal_phrase_present)
        self.assertNotIn("refusal_phrase_present", plain.to_dict(), "written when true")
        self.assertNotIn("REFUSAL_SUSPECTED", route(variant, plain).triggers)
        with tempfile.TemporaryDirectory() as directory:
            result = run_pilot(
                spec=_CONFIG.spec, corpus=_CORPUS, plan=_PLAN, model="gpt-oss:20b", executor=_fake(refuse_case="ORD-001"), executor_kind="fake",
                output_dir=Path(directory), created_on=CREATED_ON, families=(Family.BASELINE,), limit=None,
            )
            flagged = [o for o in result.observations if o.scoring.refusal_phrase_present]
            self.assertEqual([o.variant.base_case_id for o in flagged], ["ORD-001"])
            self.assertEqual(flagged[0].scoring.response_verdict, "JSON_OBJECT")
            reloaded = load_observation(Path(directory) / f"observation.{flagged[0].observation_id[:16]}.json")
            self.assertTrue(reloaded.scoring.refusal_phrase_present)
            self.assertEqual(result.run_record.scope_label, "REFUTED_CASES_PRESENT")


class ReplayProvenanceTests(unittest.TestCase):
    def test_a_replay_names_the_reply_it_re_scored_and_claims_refuse_the_pair(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = run_pilot(
                spec=_CONFIG.spec, corpus=_CORPUS, plan=_PLAN, model="gpt-oss:20b", executor=_fake(), executor_kind="fake",
                output_dir=Path(directory) / "live", created_on=CREATED_ON, families=(Family.BASELINE, Family.REPEAT), limit=None,
            )
            replayed = run_pilot(
                spec=_CONFIG.spec, corpus=_CORPUS, plan=_PLAN, model="gpt-oss:20b", executor=ReplayExecutor(Path(directory) / "live"), executor_kind="replay",
                output_dir=Path(directory) / "again", created_on="2026-09-08T14:00:00Z", families=(Family.BASELINE, Family.REPEAT), limit=None,
            )
            sources = {o.observation_id for o in first.observations}
            for observation in replayed.observations:
                self.assertIn(observation.replayed_from, sources, "every replayed observation names a live one")
                self.assertEqual(observation.request_digest, next(o for o in first.observations if o.observation_id == observation.replayed_from).request_digest)
            reloaded = load_observation(Path(directory) / "again" / f"observation.{replayed.observations[0].observation_id[:16]}.json")
            self.assertEqual(reloaded.replayed_from, replayed.observations[0].replayed_from)
            claim = claims_module.claims_from_dict({"schema_version": "creib.conformance-pilot.claims.v1", "title": "t", "claims": [
                {"claim_id": "T-01", "statement": "s", "kind": "never", "scope": {"families": None, "cases": None, "models": None, "model_call": True}, "condition": {"trigger": "EXTRA_FIELD"}, "note": None},
            ]})
            both = list(first.observations) + list(replayed.observations)
            with self.assertRaisesRegex(RecordError, "reply and its replay"):
                claims_module.evaluate_claims(claim, both, runs=[first.run_record, replayed.run_record])
            alone = claims_module.evaluate_claims(claim, list(replayed.observations), runs=[replayed.run_record])
            self.assertEqual(alone[0].tested, len(replayed.observations))


if __name__ == "__main__":
    unittest.main()
