"""``claims --without-run``: a re-score stands in for the run it re-scored, and the two are never counted together.

The option leaves out one supplied run by id or by a prefix that names exactly one; the summary
says which runs were left out; a prefix that names none or several is refused. Without it, a
directory holding the original beside a directory holding its re-score is refused by the replay
check, so the option is the only way to read the corrected records with the rest of the basis.
"""

from __future__ import annotations

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
            # A one-character prefix shared by two runs names two.
            other = run_pilot(spec=_CONFIG.spec, corpus=_CORPUS, plan=_PLAN, model="qwen3.5:397b", executor=_fake(), executor_kind="fake",
                              output_dir=Path(directory) / "other", created_on="2026-09-09T12:00:00Z", families=(Family.BASELINE,), limit=2)
            shared = ""
            for a, b in zip(live.run_record.run_id, other.run_record.run_id):
                if a != b:
                    break
                shared += a
            if shared:
                with self.assertRaisesRegex(RecordError, "names 2 of the supplied runs"):
                    claims_module.without_runs(list(live.observations) + list(other.observations), [live.run_record, other.run_record], [shared])


if __name__ == "__main__":
    unittest.main()
