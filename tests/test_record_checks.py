"""Each record-side guard the deletion sweep still found unexercised is sent one bad record.

These are the refusal sites on the record, runner, report, comparison and oracle modules that
survived the sweep rerun recorded under H26 in ``docs/failure-modes.md`` and are reachable
from an input: a response present where the variant made no call, a run whose counts repeat
a key, a record under an unknown schema version, a run that references an observation it was
not handed, a verdict outside the vocabulary. A test here shows the guard fires on one such
input; it does not show the guard is the right one.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
import tempfile
import unittest

from creib.errors import RecordError
from creib.forge.conformance import (
    FakeExecutor,
    Family,
    build_report,
    load_corpus,
    load_observation,
    load_observation_directory,
    load_pilot_config,
    load_run,
    plan,
    response_from_content,
    run_pilot,
    score,
)
from creib.forge.conformance import oracle as oracle_module
from creib.forge.conformance import records as records_module
from creib.forge.conformance.compare import compare_runs
from creib.forge.conformance.corpus import Oracle

ROOT = Path(__file__).resolve().parents[1]
PILOTS = ROOT / "forge" / "conformance" / "pilots"
LEAVE = ROOT / "forge" / "conformance" / "runs" / "leave-request"
CREATED_ON = "2026-09-05T00:00:00Z"

_CONFIG = load_pilot_config(PILOTS / "incident-form" / "pilot.json")
_CORPUS = load_corpus(_CONFIG.corpus_path, _CONFIG.spec)
_PLAN = plan(_CONFIG.spec, _CORPUS)


def _first_observation():
    return load_observation(sorted(LEAVE.glob("observation.*.json"))[0])


def _runs_by_model():
    runs = [load_run(path) for path in sorted(LEAVE.glob("run.*.json"))]
    by_model: dict[str, list] = {}
    for run in runs:
        by_model.setdefault(run.model, []).append(run)
    return by_model


class RecordGuardTests(unittest.TestCase):
    def test_bindings_must_not_be_empty(self) -> None:
        # the observation schema requires one binding first; the loader is the second guard
        with self.assertRaisesRegex(RecordError, "spec_bindings must not be empty"):
            records_module._bindings_from([], "observation.spec_bindings")

    def test_response_presence_must_agree_with_the_model_call_flag(self) -> None:
        observation = _first_observation()
        self.assertTrue(observation.variant.model_call)
        fields = {f.name: getattr(observation, f.name) for f in dataclasses.fields(observation) if f.name != "observation_id"}
        fields["response"] = None
        fields["request_digest"] = None
        rebuilt = records_module.build_observation(**fields)
        with self.assertRaisesRegex(RecordError, "response presence disagrees with the variant's model_call flag"):
            records_module.observation_from_dict(rebuilt.to_dict())

    def test_run_counts_cannot_repeat_a_key(self) -> None:
        path = sorted(LEAVE.glob("run.*.json"))[0]
        record = records_module._load_canonical(path)
        tampered = json.loads(json.dumps(record))
        tampered["family_counts"].append(dict(tampered["family_counts"][0]))
        with self.assertRaisesRegex(RecordError, "family_counts repeats a key"):
            records_module.run_from_dict(tampered)

    def test_record_naming_and_paths(self) -> None:
        with self.assertRaisesRegex(RecordError, "unknown conformance record schema_version 'x'"):
            records_module.record_filename({"schema_version": "x"})
        with self.assertRaises(TypeError):
            records_module.publish_record(_first_observation(), "somewhere")  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            load_observation("observation.json")  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            records_module.enumerate_record_directory("runs")  # type: ignore[arg-type]
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(RecordError, "cannot read record"):
                load_observation(Path(directory) / "observation.0000000000000000.json")
            with self.assertRaisesRegex(RecordError, "observation directory does not exist"):
                records_module.enumerate_record_directory(Path(directory) / "missing")


class RunnerGuardTests(unittest.TestCase):
    def _arguments(self, directory: Path, **overrides):
        arguments = dict(
            spec=_CONFIG.spec,
            corpus=_CORPUS,
            plan=_PLAN,
            model="gpt-oss:20b",
            executor=FakeExecutor(lambda request: response_from_content("{}")),
            executor_kind="fake",
            output_dir=directory,
            created_on=CREATED_ON,
            families=(Family.BASELINE,),
            limit=1,
        )
        arguments.update(overrides)
        return arguments

    def test_argument_checks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            with self.assertRaisesRegex(RecordError, "unknown executor kind 'oracle'"):
                run_pilot(**self._arguments(out, executor_kind="oracle"))
            other = load_pilot_config(PILOTS / "travel-claim" / "pilot.json")
            foreign = plan(other.spec, load_corpus(other.corpus_path, other.spec))
            with self.assertRaisesRegex(RecordError, "plan does not belong to this specification and corpus"):
                run_pilot(**self._arguments(out, plan=foreign))
            with self.assertRaises(TypeError):
                run_pilot(**self._arguments("somewhere"))  # type: ignore[arg-type]

    def test_a_dependent_family_needs_its_baseline(self) -> None:
        without_baselines = dataclasses.replace(_PLAN, variants=tuple(v for v in _PLAN.variants if v.family is not Family.BASELINE))
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(RecordError, "needs a baseline for case"):
                run_pilot(**self._arguments(Path(directory), plan=without_baselines, families=(Family.NEGATION,)))

    def test_a_configuration_failure_in_the_executor_aborts_the_run(self) -> None:
        def refuse(request):
            raise RecordError("no key in the environment")

        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(RecordError, "no key in the environment"):
                run_pilot(**self._arguments(Path(directory), executor=FakeExecutor(refuse)))


class ReportAndCompareGuardTests(unittest.TestCase):
    def test_a_report_needs_every_observation_a_run_references(self) -> None:
        runs = [load_run(path) for path in sorted(LEAVE.glob("run.*.json"))]
        observations = load_observation_directory(LEAVE)
        with self.assertRaisesRegex(RecordError, "references observation .* that was not supplied"):
            build_report(runs, observations[:-1])

    def test_compare_refuses_a_request_recorded_twice_in_one_run(self) -> None:
        by_model = _runs_by_model()
        left, right = next(runs for runs in by_model.values() if len(runs) >= 2)[:2]
        observations = load_observation_directory(LEAVE)
        original = next(o for o in observations if o.run_id == left.run_id and o.response is not None)
        # a second observation of the same request in the same run: a different id (the time
        # differs), the same digest and repeat index, listed by a run record that names both
        fields = {f.name: getattr(original, f.name) for f in dataclasses.fields(original) if f.name != "observation_id"}
        fields["created_on"] = "2026-09-05T00:00:01Z"
        twin = records_module.build_observation(**fields)
        self.assertNotEqual(twin.observation_id, original.observation_id)
        listing_both = dataclasses.replace(left, observation_ids=left.observation_ids + (twin.observation_id,))
        with self.assertRaisesRegex(RecordError, "holds two observations for"):
            compare_runs(listing_both, right, observations + [twin])


class OracleGuardTests(unittest.TestCase):
    def test_the_verdict_vocabularies_fail_closed(self) -> None:
        # the observation schema closes each vocabulary first; the loader is the second guard
        scoring = _first_observation().scoring.to_dict()
        tampered = json.loads(json.dumps(scoring))
        tampered["response_verdict"] = "GOOD"
        with self.assertRaisesRegex(RecordError, "response_verdict is unknown"):
            oracle_module.scoring_from_dict(tampered)
        tampered = json.loads(json.dumps(scoring))
        tampered["grounding_verdicts"] = [{"field": "x", "verdict": "FLOATING", "span": None, "detail": None}]
        with self.assertRaisesRegex(RecordError, r"grounding_verdicts\[0\].verdict is unknown"):
            oracle_module.scoring_from_dict(tampered)
        tampered = json.loads(json.dumps(scoring))
        tampered["field_verdicts"][0]["verdict"] = "PASS"
        with self.assertRaisesRegex(RecordError, r"field_verdicts\[0\].verdict is unknown"):
            oracle_module.scoring_from_dict(tampered)

    def test_non_finite_numbers_are_invalid_json(self) -> None:
        for content in ('{"a": NaN}', '{"a": Infinity}', '{"a": -Infinity}'):
            parsed, verdict, detail, _ = oracle_module.parse_content(content, ())
            self.assertIsNone(parsed, content)
            self.assertEqual(verdict, "INVALID_JSON", content)
            self.assertIn("non-finite", detail or "", content)

    def test_only_value_oracles_compare_with_a_present_value(self) -> None:
        absent = Oracle(field="site", kind="absent", value=None, values=None, pattern=None, oracle_status="source_scoped", rationale="t")
        with self.assertRaisesRegex(RecordError, "oracle kind absent is not comparable to a present value"):
            oracle_module._oracle_verdict("Dock 3", absent)

    def test_a_model_call_variant_needs_a_response(self) -> None:
        baseline = next(v for v in _PLAN.variants if v.family is Family.BASELINE)
        with self.assertRaisesRegex(RecordError, "a response is required unless the variant is a model-free control"):
            score(baseline, None)


if __name__ == "__main__":
    unittest.main()
