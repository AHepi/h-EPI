"""A re-score reads a cycle chain, or a round trip, as far as the recorded replies go.

A cycle's request carries the previous step's output, and a round-trip request carries the
baseline's. When a re-score reads that output differently from the recorded run (a corrected
parser, H40), the request the next step makes was never sent and has no recorded reply; the
step and those after it are PREREQUISITE_UNAVAILABLE, the record says why, and the rest of the
run re-scores. Until 9 September only a cycle step degraded so and a round trip stopped the run
(H45). Outside a replay a missing reply still aborts the run, since a live executor that cannot
answer is the operator's problem.
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from creib.errors import RecordError
from creib.forge.conformance import ChatRequest, FakeExecutor, Family, ReplayExecutor, load_corpus, load_pilot_config, plan, response_from_content, run_pilot

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "forge" / "conformance" / "pilots" / "travel-claim" / "pilot.json"
CREATED_ON = "2026-09-09T11:00:00Z"

_CONFIG = load_pilot_config(PILOT)
_CORPUS = load_corpus(_CONFIG.corpus_path, _CONFIG.spec)
_PLAN = plan(_CONFIG.spec, _CORPUS)


def _fake() -> FakeExecutor:
    def respond(request: ChatRequest):
        case = next(c for c in _CORPUS.cases if c.renderings[c.rendering] in request.user)
        return response_from_content(json.dumps(dict(case.reference_output or ())))
    return FakeExecutor(respond)


def _run(executor, kind: str, directory: Path):
    return run_pilot(
        spec=_CONFIG.spec, corpus=_CORPUS, plan=_PLAN, model="gemma4:31b", executor=executor, executor_kind=kind,
        output_dir=directory, created_on=CREATED_ON, families=(Family.BASELINE, Family.CYCLE), limit=None,
    )


def _fake_with_round_trips() -> FakeExecutor:
    """Answers a baseline with its case's key and a round-trip request, whose document is rendered from the baseline output, with the first case's key."""

    def respond(request: ChatRequest):
        case = next((c for c in _CORPUS.cases if c.renderings[c.rendering] in request.user), None)
        if case is None:
            case = _CORPUS.cases[0]
        return response_from_content(json.dumps(dict(case.reference_output or ())))
    return FakeExecutor(respond)


def _run_round_trips(executor, kind: str, directory: Path):
    return run_pilot(
        spec=_CONFIG.spec, corpus=_CORPUS, plan=_PLAN, model="gemma4:31b", executor=executor, executor_kind=kind,
        output_dir=directory, created_on=CREATED_ON, families=(Family.BASELINE, Family.ROUND_TRIP), limit=None,
    )


class ReplayOfRoundTripsTests(unittest.TestCase):
    """A round-trip request carries the baseline's output; under a re-score that reads the baseline differently the request has no recorded reply."""

    def test_a_round_trip_with_no_recorded_reply_is_unavailable_and_the_rest_of_the_re_score_completes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            live = _run_round_trips(_fake_with_round_trips(), "fake", Path(directory) / "live")
            round_trips = {o.variant.base_case_id: o for o in live.observations if o.variant.family is Family.ROUND_TRIP}
            self.assertEqual(len(round_trips), 9)
            self.assertTrue(all(o.response is not None and o.scoring.response_verdict == "JSON_OBJECT" for o in round_trips.values()))
            (Path(directory) / "live" / f"observation.{round_trips['TRV-001'].observation_id[:16]}.json").unlink()
            replayed = _run_round_trips(ReplayExecutor(Path(directory) / "live"), "replay", Path(directory) / "again")
            again = {o.variant.base_case_id: o for o in replayed.observations if o.variant.family is Family.ROUND_TRIP}
            missing = again["TRV-001"]
            self.assertEqual(missing.scoring.response_verdict, "PREREQUISITE_UNAVAILABLE")
            self.assertIn("no recorded reply for the request this variant makes under the re-score", missing.scoring.response_detail or "")
            self.assertIsNone(missing.response)
            self.assertIsNone(missing.replayed_from)
            self.assertEqual(missing.variant.variant_id, missing.planned_variant_id, "the record carries the planned variant, not a materialised one whose request was never answered")
            for case_id, observation in again.items():
                if case_id != "TRV-001":
                    self.assertEqual(observation.scoring.response_verdict, "JSON_OBJECT", case_id)
                    self.assertEqual(observation.replayed_from, round_trips[case_id].observation_id)
            self.assertEqual(len(replayed.observations), len(live.observations), "the run completes and writes a run record")
            self.assertIsNotNone(replayed.run_record)

    def test_outside_a_replay_a_round_trip_with_no_reply_still_aborts(self) -> None:
        def refuse_round_trips(request: ChatRequest):
            case = next((c for c in _CORPUS.cases if c.renderings[c.rendering] in request.user), None)
            if case is None:
                raise RecordError("no reply for a round-trip request")
            return response_from_content(json.dumps(dict(case.reference_output or ())))
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(RecordError, "no reply for a round-trip request"):
                _run_round_trips(FakeExecutor(refuse_round_trips), "fake", Path(directory) / "live")


class ReplayOfCycleChainsTests(unittest.TestCase):
    def test_a_step_with_no_recorded_reply_is_unavailable_and_the_chain_is_read_as_far_as_it_goes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            live = _run(_fake(), "fake", Path(directory) / "live")
            cycles = [o for o in live.observations if o.variant.family is Family.CYCLE and o.variant.base_case_id == "TRV-001"]
            self.assertEqual(len(cycles), 6, "one case, two criticism sources, three cycles")
            self.assertTrue(all(o.response is not None for o in cycles))
            # Remove the recorded replies of the external-criticism chain: the re-score has nothing to answer its
            # first step with. (All three steps are removed because the fake answers every step alike, so the
            # three requests carry one digest, H31, and any one recorded reply would answer the first step.)
            for o in cycles:
                if o.variant.cycle_criticism == "external":
                    (Path(directory) / "live" / f"observation.{o.observation_id[:16]}.json").unlink()
            replayed = _run(ReplayExecutor(Path(directory) / "live"), "replay", Path(directory) / "again")
            by_step = {(o.variant.cycle_criticism, o.variant.cycle_index): o for o in replayed.observations if o.variant.family is Family.CYCLE and o.variant.base_case_id == "TRV-001"}
            others = [o for o in replayed.observations if o.variant.family is Family.CYCLE and o.variant.base_case_id != "TRV-001"]
            self.assertTrue(all(o.scoring.response_verdict == "JSON_OBJECT" for o in others), "every other chain re-scores in full")
            self.assertEqual(by_step[("external", 1)].scoring.response_verdict, "PREREQUISITE_UNAVAILABLE")
            self.assertIn("no recorded reply for the request this step makes under the re-score", by_step[("external", 1)].scoring.response_detail or "")
            self.assertIsNone(by_step[("external", 1)].response)
            self.assertIsNone(by_step[("external", 1)].replayed_from)
            for index in (2, 3):
                self.assertEqual(by_step[("external", index)].scoring.response_verdict, "PREREQUISITE_UNAVAILABLE", "the steps after it follow")
            for index in (1, 2, 3):
                self.assertEqual(by_step[("none", index)].scoring.response_verdict, "JSON_OBJECT", "the other chain re-scores in full")
                self.assertIsNotNone(by_step[("none", index)].replayed_from)
            self.assertEqual(len(replayed.observations), len(live.observations), "the run completes and writes a run record")
            self.assertIsNotNone(replayed.run_record)

    def test_outside_a_replay_a_missing_reply_still_aborts(self) -> None:
        def refuse(request: ChatRequest):
            raise RecordError("no executor can answer this")
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(RecordError, "no executor can answer this"):
                _run(FakeExecutor(refuse), "fake", Path(directory) / "live")


if __name__ == "__main__":
    unittest.main()
