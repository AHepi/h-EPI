"""Loud alarms for the failure modes this repository has already paid for.

Each one is computed from a finished segment's record and says the machinery is unfit to measure,
which is a different claim from the subject being uninteresting. Conflating those produced three
withdrawn conclusions in ``docs/mini/ERRATA.md``.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from creib.forge.mini.alarms import FATAL, WARN, Alarm, alarms_for, preflight

ROOT = Path(__file__).resolve().parents[2]


def _names(alarms: list[Alarm]) -> set[str]:
    return {a.name for a in alarms}


class AlarmsOnRealRecordsTests(unittest.TestCase):
    """Committed records this session produced, so the alarms are tested against what happened."""

    def test_a_starved_loop_raises_a_fatal_alarm(self) -> None:
        """CREATIVITY-ARMS-1's first blocks spent two whole arms on this without noticing."""

        starved = ROOT / "forge/mini/runs/creativity-starved/F/s00"
        if not starved.is_dir():
            self.skipTest("the starved records are not in this checkout")
        alarms = alarms_for(starved)
        self.assertIn("LOOP_STARVED", _names(alarms))
        self.assertEqual([a.severity for a in alarms if a.name == "LOOP_STARVED"], [FATAL])

    def test_a_healthy_segment_raises_nothing_fatal(self) -> None:
        healthy = ROOT / "forge/mini/runs/creativity/A/s00"
        if not healthy.is_dir():
            self.skipTest("arm A's records are not in this checkout")
        self.assertEqual([a for a in alarms_for(healthy) if a.severity == FATAL], [])

    def test_prose_commitments_raise_a_warning_and_not_a_stop(self) -> None:
        """A criticism asked for in prose and not enforced is usually prose; that is worth saying,
        and it is not a reason to throw the segment away."""

        wired = ROOT / "forge/mini/runs/creativity/W/s00"
        if not wired.is_dir():
            self.skipTest("arm W's records are not in this checkout")
        alarms = alarms_for(wired)
        self.assertIn("COMMITMENTS_ARE_PROSE", _names(alarms))
        self.assertEqual([a.severity for a in alarms if a.name == "COMMITMENTS_ARE_PROSE"], [WARN])


class AlarmsOnSyntheticRecordsTests(unittest.TestCase):
    def test_a_missing_log_and_a_segment_that_never_ended(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "nothing"
            empty.mkdir()
            self.assertEqual(_names(alarms_for(empty)), {"SEGMENT_NEVER_STARTED"})
            (empty / "log.jsonl").write_text('{"type": "RUN_STARTED"}\n', encoding="utf-8")
            alarms = alarms_for(empty)
            self.assertEqual(_names(alarms), {"SEGMENT_DIED"})
            self.assertEqual(alarms[0].severity, FATAL)

    def test_the_carry_stalling_is_reported_when_two_briefs_are_identical(self) -> None:
        """F/s01 and F/s02 carried byte-identical briefs and nothing said so for a whole block."""

        healthy = ROOT / "forge/mini/runs/creativity/A/s00"
        if not healthy.is_dir():
            self.skipTest("arm A's records are not in this checkout")
        same = alarms_for(healthy, previous_brief="a brief", brief="a brief")
        self.assertIn("CARRY_STALLED", _names(same))
        moved = alarms_for(healthy, previous_brief="a brief", brief="a different brief")
        self.assertNotIn("CARRY_STALLED", _names(moved))


class PreflightTests(unittest.TestCase):
    def test_a_manifest_naming_an_unregistered_seat_is_refused_before_any_call(self) -> None:
        """M25 cost thirty-six runs and M26 cost three more; both were visible before the first call."""

        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "manifest.json"
            manifest.write_text(json.dumps({
                "schema_version": "creib.mini.manifest.v1", "manifest_id": "test.unregistered",
                "problem": "p", "cycles": {"max_cycles": 1}, "port_types": [], "kinds": [],
                "stages": [{"stage_id": "x", "kind_id": "mini.nothing-registers-this.v1", "seat": "machine"},
                           {"stage_id": "end", "end": True}],
            }), encoding="utf-8")
            alarms = preflight(manifest, ROOT)
            self.assertEqual(_names(alarms), {"SEAT_NOT_REGISTERED_BY_THE_TOOL"})
            self.assertEqual(alarms[0].severity, FATAL)

    def test_a_manifest_whose_seats_the_tool_registers_passes(self) -> None:
        good = ROOT / "forge/mini/manifests/creativity/A/s00/manifest.json"
        if not good.is_file():
            self.skipTest("arm A's manifests are not in this checkout")
        self.assertEqual(preflight(good, ROOT), [])
