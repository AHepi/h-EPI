"""R25: a seat may be a model or a machine, and the record says which."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from creib.forge.mini.blindspot import VERDICT_KIND
from creib.forge.mini.log import ARTIFACT_SUBMITTED, FORMAT_FAILURE, replay
from creib.forge.mini.machines import (
    MachineContext,
    MachineSeat,
    register_machine_seat,
    registered_machine_seats,
    resolve_machine_seat,
)

from .helpers import MiniTestCase, base_manifest, submission

ROOT = Path(__file__).resolve().parents[2]
BLIND_SPOT = ROOT / "forge" / "mini" / "manifests" / "blind-spot" / "manifest.json"
SCRIPT = ROOT / "forge" / "mini" / "scripts" / "blind-spot.json"

A_MODEL_VERDICT = json.dumps(
    {
        "body": "My reading of this cycle.",
        "commitments": json.dumps(
            {
                "verdicts": [
                    {
                        "proposal": "0123456789abcdef",
                        "executed": "moved",
                        "catalogued": False,
                        "standing": "candidate point",
                    }
                ]
            }
        ),
    }
)


def _blind_spot_manifest() -> dict:
    from creib.strict_json import load_strict

    return dict(load_strict(BLIND_SPOT))


def _script() -> dict:
    """A fresh copy of the committed script, which is addressed by coordinate."""

    from creib.strict_json import load_strict

    return json.loads(json.dumps(load_strict(SCRIPT)))


class TheSameManifestBothWaysTests(MiniTestCase):
    """The amendment's own test: the verdict seat as model, then as machine."""

    def setUp(self) -> None:
        super().setUp()
        # The manifest names its catalogue by a path beside itself.
        self.catalogue = (BLIND_SPOT.parent / "catalogue.json").read_text(encoding="utf-8")

    def _manifest(self, seat: str) -> dict:
        manifest = _blind_spot_manifest()
        manifest["sources"] = [{"source_id": "catalogue", "text": self.catalogue}]
        manifest["cycles"] = {"max_cycles": 1}
        for stage in manifest["stages"]:
            if stage["stage_id"] == "verdict":
                stage["seat"] = seat
        return manifest

    def test_provenance_differs_and_the_same_format_checks_both(self) -> None:
        script = _script()
        machine_plan, machine_outcome = self.run_manifest(self._manifest("machine"), script, name="machine")
        model_script = _script()
        model_script["verdict"] = {"1": [A_MODEL_VERDICT]}
        model_plan, model_outcome = self.run_manifest(self._manifest("model"), model_script, name="model")

        def verdict_seat(plan, outcome) -> str:
            state = replay(outcome.root / "log.jsonl", plan.genesis)
            records = [r for r in state.artifacts.values() if r["kind_id"] == VERDICT_KIND]
            self.assertEqual(len(records), 1)
            return str(records[0]["seat"])

        self.assertEqual(verdict_seat(machine_plan, machine_outcome), "machine")
        self.assertEqual(verdict_seat(model_plan, model_outcome), "model")
        # Both got through the same compiled format, so neither was privileged.
        self.assertEqual(self.events_of(machine_outcome, FORMAT_FAILURE), [])
        self.assertEqual(self.events_of(model_outcome, FORMAT_FAILURE), [])
        self.assertEqual(machine_plan.formats[VERDICT_KIND].describe(), model_plan.formats[VERDICT_KIND].describe())

    def test_a_model_verdict_that_misses_the_schema_is_refused_like_any_other(self) -> None:
        script = _script()
        script["verdict"] = {"1": [json.dumps({"body": "b", "commitments": json.dumps({"verdicts": [{"nope": 1}]})})] * 2}
        _, outcome = self.run_manifest(self._manifest("model"), script, name="model-bad")
        failures = self.events_of(outcome, FORMAT_FAILURE)
        self.assertTrue(failures)
        self.assertEqual(failures[0]["payload"]["seat"], "model")

    def test_the_record_marks_every_artifact_with_the_seat_that_made_it(self) -> None:
        _, outcome = self.run_manifest(self._manifest("machine"), _script(), name="marked")
        seats = {event["kind_id"]: event["payload"]["seat"] for event in self.events_of(outcome, ARTIFACT_SUBMITTED)}
        self.assertEqual(seats["mini.proposal.v1"], "model")
        self.assertEqual(seats["mini.execution.v1"], "machine")
        self.assertEqual(seats["mini.verdict.v1"], "machine")


#: A kind that exists only so a machine seat can be registered for it here; a
#: registry is module state, so a test that registers into it uses its own id.
_PROBE_KIND = "k.machine-probe"
register_machine_seat(
    MachineSeat(_PROBE_KIND, "returns a body with no keyword in it", lambda context: submission("nothing", "c"))
)


class MachineSeatRegistryTests(MiniTestCase):
    def test_a_machine_seat_is_resolved_by_kind_id(self) -> None:
        self.assertEqual(resolve_machine_seat(VERDICT_KIND).kind_id, VERDICT_KIND)
        self.assertIn(VERDICT_KIND, {seat.kind_id for seat in registered_machine_seats()})

    def test_a_stage_naming_a_machine_seat_nothing_registers_is_refused(self) -> None:
        manifest = base_manifest()
        manifest["kinds"].append(
            {
                "kind_id": "k.nobody-registers-this",
                "title": "Unregistered",
                "input_ports": [{"port_id": "problem", "port_type": "problem"}],
                "output_port": {"port_id": "out", "produces_kind": "k.nobody-registers-this"},
            }
        )
        manifest["stages"] = [
            {"stage_id": "m1", "kind_id": "k.nobody-registers-this", "seat": "machine", "ports": ["problem"]},
            {"stage_id": "end", "end": True},
        ]
        plan = self.compile(manifest)
        self.assertRefuses("MINI_MACHINE_SEAT_UNKNOWN", self.run_plan, plan, {})

    def test_registering_a_machine_seat_twice_is_refused(self) -> None:
        self.assertRefuses(
            "MINI_MACHINE_SEAT_DUPLICATE",
            register_machine_seat,
            MachineSeat(VERDICT_KIND, "again", lambda context: ""),
        )

    def test_an_unknown_seat_kind_is_refused_at_compile(self) -> None:
        manifest = base_manifest()
        manifest["stages"][0]["seat"] = "oracle"
        self.assertRefuses("MINI_STAGE_UNKNOWN", self.compile, manifest)

    def test_a_machine_seat_whose_answer_misses_its_format_is_refused_like_any_other(self) -> None:
        manifest = base_manifest()
        manifest["kinds"].append(
            {
                "kind_id": _PROBE_KIND,
                "title": "Probe",
                "input_ports": [{"port_id": "problem", "port_type": "problem"}],
                "output_port": {"port_id": "out", "produces_kind": _PROBE_KIND},
                "format": {"body": {"all_of": [{"check": "keywords", "keywords": ["BECAUSE"]}]}},
                "failure_policy": {"retries": 0},
            }
        )
        manifest["stages"] = [
            {"stage_id": "m1", "kind_id": _PROBE_KIND, "seat": "machine", "ports": ["problem"]},
            {"stage_id": "end", "end": True},
        ]
        _, outcome = self.run_manifest(manifest, {})
        failures = self.events_of(outcome, FORMAT_FAILURE)
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0]["payload"]["seat"], "machine")
        self.assertEqual(self.events_of(outcome, "SUBMISSION_DROPPED")[0]["kind_id"], _PROBE_KIND)

    def test_a_machine_seat_reads_the_record_through_its_context(self) -> None:
        from creib.forge.mini.log import BlobStore

        plan, outcome = self.run_manifest(base_manifest())
        state = replay(outcome.root / "log.jsonl", plan.genesis)
        context = MachineContext(
            plan=plan, state=state, blobs=BlobStore(outcome.root / "blobs"), stage=plan.stage("x1"), cycle=1
        )
        records = context.artifacts_of_kind("k.conjecture")
        self.assertEqual(len(records), 1)
        self.assertEqual(context.body(records[0]), "The two paragraphs disagree.")
