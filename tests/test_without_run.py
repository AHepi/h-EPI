"""``claims --without-run``: a re-score stands in for the run it re-scored, and the two are never counted together.

The option leaves out one supplied run by id or by a prefix that names exactly one; the summary
says which runs were left out; a prefix that names none or several is refused. Without it, a
directory holding the original beside a directory holding its re-score is refused by the replay
check, so the option is the only way to read the corrected records with the rest of the basis.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
import tempfile
import unittest

from creib.errors import RecordError
from creib.forge.conformance import ChatRequest, FakeExecutor, Family, ReplayExecutor, load_corpus, load_pilot_config, plan, response_from_content, run_pilot
from creib.forge.conformance import claims as claims_module

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "forge" / "conformance" / "pilots" / "incident-form" / "pilot.json"
_CONFIG = load_pilot_config(PILOT)
_CORPUS = load_corpus(_CONFIG.corpus_path, _CONFIG.spec)
_PLAN = plan(_CONFIG.spec, _CORPUS)


def _fake() -> FakeExecutor:
    def respond(request: ChatRequest):
        case = next(c for c in _CORPUS.cases if c.renderings[c.rendering] in request.user)
        return response_from_content(json.dumps(dict(case.reference_output or ())))
    return FakeExecutor(respond)


def _claim():
    return claims_module.claims_from_dict({"schema_version": "creib.conformance-pilot.claims.v1", "title": "t", "claims": [
        {"claim_id": "W-01", "statement": "s", "kind": "never", "scope": {"families": None, "cases": None, "models": None, "model_call": True}, "condition": {"trigger": "EXTRA_FIELD"}, "note": None},
    ]})


class WithoutRunTests(unittest.TestCase):
    def test_the_re_score_stands_in_for_the_run_it_re_scored(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            live = run_pilot(spec=_CONFIG.spec, corpus=_CORPUS, plan=_PLAN, model="gemma4:31b", executor=_fake(), executor_kind="fake",
                             output_dir=Path(directory) / "live", created_on="2026-09-09T12:00:00Z", families=(Family.BASELINE,), limit=3)
            again = run_pilot(spec=_CONFIG.spec, corpus=_CORPUS, plan=_PLAN, model="gemma4:31b", executor=ReplayExecutor(Path(directory) / "live"), executor_kind="replay",
                              output_dir=Path(directory) / "again", created_on="2026-09-09T12:30:00Z", families=(Family.BASELINE,), limit=3)
            observations = list(live.observations) + list(again.observations)
            runs = [live.run_record, again.run_record]
            with self.assertRaisesRegex(RecordError, "reply and its replay"):
                claims_module.evaluate_claims(_claim(), observations, runs=runs)
            kept, kept_runs, excluded = claims_module.without_runs(observations, runs, [live.run_record.run_id[:16]])
            self.assertEqual(excluded, (live.run_record.run_id,))
            self.assertEqual({o.run_id for o in kept}, {again.run_record.run_id})
            self.assertEqual([r.run_id for r in kept_runs], [again.run_record.run_id])
            result = claims_module.evaluate_claims(_claim(), kept, runs=kept_runs)[0]
            self.assertEqual(result.tested, len(again.observations))
            self.assertEqual(claims_module.without_runs(observations, runs, []), (observations, runs, ()))

    def test_a_prefix_naming_no_run_or_several_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            live = run_pilot(spec=_CONFIG.spec, corpus=_CORPUS, plan=_PLAN, model="gemma4:31b", executor=_fake(), executor_kind="fake",
                             output_dir=Path(directory) / "live", created_on="2026-09-09T12:00:00Z", families=(Family.BASELINE,), limit=2)
            with self.assertRaisesRegex(RecordError, "names 0 of the supplied runs"):
                claims_module.without_runs(list(live.observations), [live.run_record], ["ffffffff"])
            with self.assertRaisesRegex(RecordError, "non-empty prefixes"):
                claims_module.without_runs(list(live.observations), [live.run_record], [""])
            # A prefix shared by two runs names two. Run ids are hashes, so two real runs share a prefix
            # only by chance; the resolution reads nothing but the id, so two records that differ in the
            # last character of the id stand for the case.
            first = dataclasses.replace(live.run_record, run_id="a" * 15 + "1")
            second = dataclasses.replace(live.run_record, run_id="a" * 15 + "2")
            with self.assertRaisesRegex(RecordError, "names 2 of the supplied runs"):
                claims_module.without_runs([], [first, second], ["a" * 15])
            kept, kept_runs, excluded = claims_module.without_runs([], [first, second], ["a" * 15 + "2"])
            self.assertEqual((kept, [r.run_id for r in kept_runs], excluded), ([], [first.run_id], (second.run_id,)))

    def test_observations_without_a_run_record_are_tested_and_named(self) -> None:
        """An observation is one reply, tested whether or not a run record names it; the output says which were read so."""

        with tempfile.TemporaryDirectory() as directory:
            live = run_pilot(spec=_CONFIG.spec, corpus=_CORPUS, plan=_PLAN, model="gemma4:31b", executor=_fake(), executor_kind="fake",
                             output_dir=Path(directory) / "live", created_on="2026-09-09T12:00:00Z", families=(Family.BASELINE,), limit=2)
            observations = list(live.observations)
            self.assertEqual(claims_module.runs_without_record(observations, [live.run_record]), {})
            without = claims_module.runs_without_record(observations, [])
            self.assertEqual(without, {live.run_record.run_id: len(observations)})
            with_record = claims_module.evaluate_claims(_claim(), observations, runs=[live.run_record])[0]
            no_record = claims_module.evaluate_claims(_claim(), observations, runs=[])[0]
            self.assertEqual((with_record.tested, no_record.tested), (len(observations), len(observations)))
            rendered = claims_module.render_claims_markdown((no_record,), without)
            self.assertIn(f"{len(observations)} observations of run `{live.run_record.run_id}`", rendered)
            self.assertIn("leave such a run out with `--without-run`", rendered)
            self.assertNotIn("no supplied run record names", claims_module.render_claims_markdown((with_record,), {}))
            self.assertNotIn("no supplied run record names", claims_module.render_claims_markdown((with_record,)))
            # Left out, the run's observations are neither tested nor named.
            kept, kept_runs, excluded = claims_module.without_runs(observations, [], [live.run_record.run_id])
            self.assertEqual((kept, kept_runs, excluded), ([], [], (live.run_record.run_id,)))
            self.assertEqual(claims_module.runs_without_record(kept, kept_runs), {})


if __name__ == "__main__":
    unittest.main()
