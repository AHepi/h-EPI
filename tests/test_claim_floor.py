"""Each refutation placed against the repeat floor of its own run and case.

A refuting observation's floor is the REPEAT observations of the same run and case other than
itself; the class says whether the refuting condition also held on every one of them, on some,
on none, or whether there was none. This is a description of the records beside each other,
never a verdict on the model: a claim is refuted by one observation whatever the floor says.
The same evaluation refuses one observation supplied twice, since one reply is counted once.
"""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from creib.errors import RecordError
from creib.forge.conformance import ChatRequest, FakeExecutor, Family, load_corpus, load_pilot_config, plan, response_from_content, run_pilot
from creib.forge.conformance import claims as claims_module

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "forge" / "conformance" / "pilots" / "travel-claim" / "pilot.json"
CREATED_ON = "2026-09-08T15:00:00Z"

_CONFIG = load_pilot_config(PILOT)
_CORPUS = load_corpus(_CONFIG.corpus_path, _CONFIG.spec)
_PLAN = plan(_CONFIG.spec, _CORPUS)

# Which replies to a case are wrong on the destination city: keyed by (case, repeat index or 0).
WRONG = {
    ("TRV-001", 1), ("TRV-001", 2),          # both repeats wrong, baseline right: each repeat's floor is the other, `all`
    ("TRV-002", 1),                          # one repeat wrong: its floor is the other repeat, `none`
    ("TRV-003", 0),                          # baseline wrong, repeats right: `none`
    ("TRV-004", 0), ("TRV-004", 1),          # baseline and one repeat wrong: baseline `some`, the repeat `none`
}


def _fake() -> FakeExecutor:
    def respond(request: ChatRequest):
        case = next(c for c in _CORPUS.cases if c.renderings[c.rendering] in request.user)
        body = dict(case.reference_output or ())
        if (case.case_id, request.repeat_index or 0) in WRONG:
            body["destination_city"] = "Nowhere"
        return response_from_content(json.dumps(body))
    return FakeExecutor(respond)


def _claim(scope_families=None, models=None):
    return claims_module.claims_from_dict({"schema_version": "creib.conformance-pilot.claims.v1", "title": "t", "claims": [
        {"claim_id": "F-01", "statement": "the model never differs from the key on the destination", "kind": "never",
         "scope": {"families": scope_families, "cases": None, "models": models, "model_call": True},
         "condition": {"field_verdict": {"field": "destination_city", "verdict": "MISMATCH"}}, "note": None},
    ]})


class FloorClassTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.directory = tempfile.TemporaryDirectory()
        cls.result = run_pilot(
            spec=_CONFIG.spec, corpus=_CORPUS, plan=_PLAN, model="gemma4:31b", executor=_fake(), executor_kind="fake",
            output_dir=Path(cls.directory.name), created_on=CREATED_ON, families=(Family.BASELINE, Family.REPEAT), limit=None,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.directory.cleanup()

    def test_each_refutation_is_classed_against_the_repeats_of_its_run_and_case(self) -> None:
        results = claims_module.evaluate_claims(_claim(), list(self.result.observations), runs=[self.result.run_record])
        result = results[0]
        self.assertEqual(result.status, "REFUTED")
        self.assertEqual(result.refuting, len(WRONG))
        self.assertEqual((result.floor_all, result.floor_some, result.floor_none, result.floor_absent), (2, 1, 3, 0))
        by_class = {}
        for (observation_id, _model, case_id, family), floor in zip(result.examples, result.example_floors, strict=True):
            observation = next(o for o in self.result.observations if o.observation_id == observation_id)
            by_class[(case_id, observation.variant.repeat_index or 0)] = floor
            self.assertEqual(family, observation.variant.family.value)
        expected = {
            ("TRV-001", 1): "all", ("TRV-001", 2): "all",
            ("TRV-002", 1): "none",
            ("TRV-003", 0): "none",
            ("TRV-004", 0): "some", ("TRV-004", 1): "none",
        }
        # Examples are capped; every example listed carries the class its floor gives it.
        self.assertEqual(len(by_class), min(len(WRONG), claims_module._MAX_EXAMPLES))
        self.assertEqual(by_class, {key: expected[key] for key in by_class})
        payload = result.to_dict()
        self.assertEqual(payload["refuting_by_floor"], {"all": 2, "some": 1, "none": 3, "absent": 0})
        self.assertEqual({e["floor"] for e in payload["examples"]}, {"all", "some", "none"})
        rendered = claims_module.render_claims_markdown(results)
        self.assertIn("also held on every repeat for 2, on some repeats for 1, on no repeat for 3; 0 had no repeat", rendered)
        self.assertIn("floor: some", rendered)

    def test_without_repeats_supplied_every_refutation_has_no_floor(self) -> None:
        baselines = [o for o in self.result.observations if o.variant.family is Family.BASELINE]
        result = claims_module.evaluate_claims(_claim(), baselines, runs=[self.result.run_record])[0]
        self.assertEqual(result.refuting, 2, "TRV-003 and TRV-004 baselines are wrong")
        self.assertEqual((result.floor_all, result.floor_some, result.floor_none, result.floor_absent), (0, 0, 0, 2))
        self.assertIn("2 had no repeat to compare with", claims_module.render_claims_markdown((result,)))

    def test_a_floor_is_read_even_when_the_scope_excludes_the_repeats(self) -> None:
        # Scope admits baselines only; the repeats still supply the floor of the two refuting baselines.
        result = claims_module.evaluate_claims(_claim(scope_families=["BASELINE"]), list(self.result.observations), runs=[self.result.run_record])[0]
        self.assertEqual(result.refuting, 2)
        self.assertEqual((result.floor_all, result.floor_some, result.floor_none, result.floor_absent), (0, 1, 1, 0))
        self.assertEqual(result.witnesses_outside_scope, 4, "the four wrong repeats hold the condition outside the scope")

    def test_one_observation_supplied_twice_is_refused(self) -> None:
        observations = list(self.result.observations)
        with self.assertRaisesRegex(RecordError, "supplied twice"):
            claims_module.evaluate_claims(_claim(), observations + observations[:1], runs=[self.result.run_record])

    def test_floor_classes_are_a_closed_list(self) -> None:
        self.assertEqual(claims_module.FLOOR_CLASSES, ("all", "some", "none", "absent"))


if __name__ == "__main__":
    unittest.main()
