"""Reasoning levels, run-time endpoint overrides, the interleaved sending order, and the
run-level claim predicate that reads them back.

The pilot's endpoint says what is sent by default; a run may override the reasoning setting
and the call timeout, and the run record's endpoint then carries what was actually sent, so
a claim can scope on it. None of this touches a variant or a plan id.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from creib.errors import RecordError
from creib.forge.conformance import (
    ChatRequest,
    FakeExecutor,
    Family,
    load_corpus,
    load_pilot_config,
    load_run,
    plan,
    response_from_content,
    run_pilot,
)
from creib.forge.conformance import claims as claims_module
from creib.forge.conformance.runner import select_variants
from creib.forge.conformance.spec import THINK_LEVELS, endpoint_from_dict, think_setting
from creib.strict_json import loads_strict

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "forge" / "conformance" / "pilots" / "incident-form" / "pilot.json"
TOOL = ROOT / "tools" / "run_conformance_pilot.py"
CREATED_ON = "2026-09-07T00:00:00Z"

_CONFIG = load_pilot_config(PILOT)
_CORPUS = load_corpus(_CONFIG.corpus_path, _CONFIG.spec)
_PLAN = plan(_CONFIG.spec, _CORPUS)


def _raw_endpoint() -> dict:
    return loads_strict(PILOT.read_text(encoding="utf-8"))["endpoint"]


class ThinkSettingTests(unittest.TestCase):
    def test_levels_booleans_and_null_pass_and_nothing_else(self) -> None:
        for value in (None, True, False, *THINK_LEVELS):
            self.assertEqual(think_setting(value, "t"), value)
        for bad in ("off", "HIGH", 1, "", "auto"):
            with self.assertRaisesRegex(RecordError, "must be null, a boolean, or one of"):
                think_setting(bad, "t")
        endpoint = dict(_raw_endpoint()); endpoint["think"] = "high"
        self.assertEqual(endpoint_from_dict(endpoint).think, "high")
        endpoint["think"] = "maximal"
        with self.assertRaises(RecordError):
            endpoint_from_dict(endpoint)

    def test_the_level_is_sent_and_is_part_of_the_digest(self) -> None:
        base = dict(model="m", system="s", user="u", format_schema=None, options={"temperature": 0, "seed": 7})
        high = ChatRequest(think="high", **base)
        low = ChatRequest(think="low", **base)
        off = ChatRequest(think=False, **base)
        self.assertEqual(high.body()["think"], "high")
        self.assertEqual(len({high.request_digest, low.request_digest, off.request_digest}), 3, "each setting is a different request")
        self.assertNotIn("think", ChatRequest(think=None, **base).body(), "None sends nothing")


class OverrideAndOrderTests(unittest.TestCase):
    def _run(self, directory: Path, spec, **kwargs):
        return run_pilot(
            spec=spec, corpus=_CORPUS, plan=_PLAN, model="gpt-oss:20b",
            executor=FakeExecutor(lambda request: response_from_content("{}")), executor_kind="fake",
            output_dir=directory, created_on=CREATED_ON, **kwargs,
        )

    def test_the_run_record_carries_the_endpoint_actually_used(self) -> None:
        spec = _CONFIG.spec
        overridden = dataclasses.replace(spec, endpoint=dataclasses.replace(spec.endpoint, think="high", timeout_seconds=600))
        with tempfile.TemporaryDirectory() as directory:
            result = self._run(Path(directory), overridden, families=(Family.BASELINE,), limit=2)
            self.assertEqual(result.run_record.endpoint.think, "high")
            self.assertEqual(result.run_record.endpoint.timeout_seconds, 600)
            reloaded = load_run(result.run_path)
            self.assertEqual((reloaded.endpoint.think, reloaded.endpoint.timeout_seconds), ("high", 600))
            self.assertEqual(reloaded.plan_id, _PLAN.plan_id, "the plan is untouched by an endpoint override")
            # the request carried the level, so its digest differs from the pilot's default request
            default = self._run(Path(directory) / "default", spec, families=(Family.BASELINE,), limit=2)
            self.assertNotEqual(result.observations[0].request_digest, default.observations[0].request_digest)
            self.assertEqual(result.observations[0].variant.variant_id, default.observations[0].variant.variant_id)

    def test_interleaved_order_keeps_each_case_together_with_its_baseline_first(self) -> None:
        family_order = select_variants(_PLAN, order="family")
        interleaved = select_variants(_PLAN, order="interleaved")
        self.assertEqual(sorted(v.variant_id for v in family_order), sorted(v.variant_id for v in interleaved), "the same variants either way")
        baselines = [v for v in family_order if v.family is Family.BASELINE]
        self.assertEqual([v.family for v in family_order[: len(baselines)]], [Family.BASELINE] * len(baselines), "family order sends every baseline first")
        seen: list[str] = []
        for variant in interleaved:
            if variant.base_case_id not in seen:
                seen.append(variant.base_case_id)
                self.assertTrue(variant.family is Family.BASELINE or variant.base_case_id.startswith("BND"), f"{variant.base_case_id} opens with its baseline")
            else:
                self.assertEqual(variant.base_case_id, seen[-1], "a case's variants are contiguous")
        with self.assertRaisesRegex(RecordError, "order must be one of"):
            select_variants(_PLAN, order="random")
        with tempfile.TemporaryDirectory() as directory:
            result = self._run(Path(directory), _CONFIG.spec, families=(Family.BASELINE, Family.ROUND_TRIP, Family.REPEAT), order="interleaved")
            ids = [o.variant.base_case_id for o in result.observations]
            self.assertEqual(ids, sorted(ids, key=ids.index), "the run record lists observations in sending order")
            round_trips = [o for o in result.observations if o.variant.family is Family.ROUND_TRIP]
            self.assertTrue(round_trips and all(o.scoring.response_verdict != "PREREQUISITE_UNAVAILABLE" or o.scoring.parsed_output is None for o in round_trips), "each round trip followed its own baseline")

    def test_cli_overrides_are_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            completed = subprocess.run(
                [sys.executable, str(TOOL), "run", "--pilot", str(PILOT), "--model", "gpt-oss:20b", "--family", "BASELINE", "--limit", "1",
                 "--output-dir", directory, "--created-on", CREATED_ON, "--dry-run", "--think", "low", "--timeout-seconds", "600", "--order", "interleaved"],
                capture_output=True, text=True, cwd=str(ROOT), env={"PYTHONPATH": str(ROOT / "src"), "PATH": ""},
            )
            self.assertIn(completed.returncode, (0, 1), completed.stderr)
            summary = json.loads(completed.stdout.strip().splitlines()[-1])
            run = load_run(Path(summary["run_record_path"]))
            self.assertEqual((run.endpoint.think, run.endpoint.timeout_seconds), ("low", 600))
            bad = subprocess.run(
                [sys.executable, str(TOOL), "run", "--pilot", str(PILOT), "--model", "gpt-oss:20b", "--family", "BASELINE", "--limit", "1",
                 "--output-dir", directory + "/bad", "--created-on", CREATED_ON, "--dry-run", "--think", "maximal"],
                capture_output=True, text=True, cwd=str(ROOT), env={"PYTHONPATH": str(ROOT / "src"), "PATH": ""},
            )
            self.assertNotEqual(bad.returncode, 0)
            self.assertIn("must be null, a boolean, or one of", bad.stdout + bad.stderr)


class EndpointPredicateTests(unittest.TestCase):
    def test_claims_scope_on_the_run_setting(self) -> None:
        spec = _CONFIG.spec
        with tempfile.TemporaryDirectory() as directory:
            high = run_pilot(spec=dataclasses.replace(spec, endpoint=dataclasses.replace(spec.endpoint, think="high")), corpus=_CORPUS, plan=_PLAN, model="gpt-oss:20b",
                             executor=FakeExecutor(lambda r: response_from_content("{}")), executor_kind="fake", output_dir=Path(directory) / "high", created_on=CREATED_ON, families=(Family.BASELINE,), limit=1)
            low = run_pilot(spec=dataclasses.replace(spec, endpoint=dataclasses.replace(spec.endpoint, think="low", timeout_seconds=600)), corpus=_CORPUS, plan=_PLAN, model="gpt-oss:20b",
                            executor=FakeExecutor(lambda r: response_from_content("{}")), executor_kind="fake", output_dir=Path(directory) / "low", created_on=CREATED_ON, families=(Family.BASELINE,), limit=1)
            observations = list(high.observations) + list(low.observations)
            context = claims_module.Context(observations, [high.run_record, low.run_record])
            holds = lambda condition, o: claims_module.compile_condition(condition, "c")(o, context)
            self.assertTrue(holds({"endpoint": {"think": "high"}}, high.observations[0]))
            self.assertFalse(holds({"endpoint": {"think": "high"}}, low.observations[0]))
            self.assertTrue(holds({"endpoint": {"think": "low", "timeout_seconds": 600}}, low.observations[0]))
            self.assertFalse(holds({"endpoint": {"timeout_seconds": 600}}, high.observations[0]))
            without_runs = claims_module.Context(observations)
            self.assertFalse(claims_module.compile_condition({"endpoint": {"think": "high"}}, "c")(high.observations[0], without_runs), "no run record supplied, no claim about it")
            for bad in ({"endpoint": {}}, {"endpoint": {"think": "maximal"}}, {"endpoint": {"timeout_seconds": 0}}):
                with self.assertRaises(RecordError):
                    claims_module.compile_condition(bad, "c")
            self.assertEqual(claims_module.condition_footprint({"endpoint": {"think": "high"}}), (frozenset(), frozenset()))
            raw = {"schema_version": claims_module.CLAIMS_SCHEMA_VERSION, "title": "t", "claims": [
                {"claim_id": "T-1", "statement": "s", "kind": "never", "scope": None, "condition": {"all_of": [{"endpoint": {"think": "low"}}, {"response_verdict": "JSON_OBJECT"}]}, "note": None}]}
            results = claims_module.evaluate_claims(claims_module.claims_from_dict(raw), observations, runs=[high.run_record, low.run_record])
            self.assertEqual((results[0].status, results[0].refuting), ("REFUTED", 1))


if __name__ == "__main__":
    unittest.main()
