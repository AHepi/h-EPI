"""R29: a script addressed by coordinate, so attention can be switched on and off."""

from __future__ import annotations

import json
from pathlib import Path

from creib.forge.mini.attention import ATTENTION_MOST_UNANSWERED, ATTENTION_OFF
from creib.forge.mini.compare import compare_roots
from creib.forge.mini.executor import Request, ScriptedResponder
from creib.forge.mini.log import ATTENTION_CHOSE, STAGE_ENTERED
from creib.strict_json import load_strict

from .helpers import MiniTestCase, base_manifest, submission

ROOT = Path(__file__).resolve().parents[2]
BLIND_SPOT = ROOT / "forge" / "mini" / "manifests" / "blind-spot" / "manifest.json"
SCRIPT = ROOT / "forge" / "mini" / "scripts" / "blind-spot.json"


def _blind_spot(attention: str | None) -> dict:
    manifest = dict(load_strict(BLIND_SPOT))
    manifest["sources"] = [
        {"source_id": "catalogue", "text": (BLIND_SPOT.parent / "catalogue.json").read_text(encoding="utf-8")}
    ]
    if attention is not None:
        manifest["attention"] = {"policy": attention}
    return manifest


def _script() -> dict:
    return json.loads(json.dumps(load_strict(SCRIPT)))


class TwoFormsTests(MiniTestCase):
    def test_an_ordered_script_is_consumed_in_order(self) -> None:
        responder = ScriptedResponder({"c1": ["first", "second"]})
        self.assertEqual(responder.reply(Request("c1", "k", 0, "b", cycle=1)).text, "first")
        self.assertEqual(responder.reply(Request("c1", "k", 0, "b", cycle=1)).text, "second")

    def test_a_coordinate_script_answers_by_cycle_and_attempt(self) -> None:
        responder = ScriptedResponder({"c1": {"1": ["one-a", "one-b"], "2": ["two-a"]}})
        self.assertEqual(responder.reply(Request("c1", "k", 0, "b", cycle=2)).text, "two-a")
        self.assertEqual(responder.reply(Request("c1", "k", 1, "b", cycle=1)).text, "one-b")
        self.assertEqual(responder.reply(Request("c1", "k", 0, "b", cycle=1)).text, "one-a")

    def test_a_coordinate_script_does_not_run_out_by_being_asked_twice(self) -> None:
        """The point of the form: the same coordinate always gives the same reply."""

        responder = ScriptedResponder({"c1": {"1": ["only"]}})
        self.assertEqual(responder.reply(Request("c1", "k", 0, "b", cycle=1)).text, "only")
        self.assertEqual(responder.reply(Request("c1", "k", 0, "b", cycle=1)).text, "only")

    def test_a_coordinate_the_script_does_not_name_is_refused(self) -> None:
        responder = ScriptedResponder({"c1": {"1": ["only"]}})
        self.assertRefuses("MINI_SCRIPT_EXHAUSTED", responder.reply, Request("c1", "k", 0, "b", cycle=2))

    def test_both_forms_may_appear_in_one_script(self) -> None:
        responder = ScriptedResponder({"c1": {"1": ["by coordinate"]}, "x1": ["in order"]})
        self.assertEqual(responder.reply(Request("c1", "k", 0, "b", cycle=1)).text, "by coordinate")
        self.assertEqual(responder.reply(Request("x1", "k", 0, "b", cycle=1)).text, "in order")

    def test_the_committed_blind_spot_script_is_addressed_by_coordinate(self) -> None:
        script = _script()
        self.assertTrue(all(isinstance(value, dict) for value in script.values()))
        self.assertEqual(sorted(script["propose-1"]), ["1", "2", "3"])


class OneScriptBothWaysTests(MiniTestCase):
    """R29's own test: one script, attention off and attention on."""

    def _run(self, attention: str | None, name: str):
        return self.run_manifest(_blind_spot(attention), _script(), name=name)

    def test_the_same_script_drives_the_run_with_attention_off_and_on(self) -> None:
        off_plan, off = self._run(ATTENTION_OFF, "off")
        on_plan, on = self._run(ATTENTION_MOST_UNANSWERED, "on")
        self.assertEqual(off.cycles_completed, 3)
        self.assertEqual(on.cycles_completed, 3)
        self.assertEqual(off.stages_entered, on.stages_entered)

    def test_the_two_logs_differ_only_where_the_policy_acted(self) -> None:
        """On this template the policy finds nothing to prefer, so the only
        difference is the header — which is what attention being idle means."""

        _, off = self._run(ATTENTION_OFF, "off")
        _, on = self._run(ATTENTION_MOST_UNANSWERED, "on")
        self.assertEqual(self.events_of(on, ATTENTION_CHOSE), [])

        def without_header(outcome):
            return [
                {key: event[key] for key in ("cycle", "type", "stage_id", "kind_id", "artifact_id")}
                for event in self.events(outcome)
                if event["type"] != "RUN_STARTED"
            ]

        self.assertEqual(without_header(off), without_header(on))
        started = self.events_of(on, "RUN_STARTED")[0]["payload"]["attention_policy"]
        self.assertEqual(started, ATTENTION_MOST_UNANSWERED)

    def test_compare_sets_the_two_roots_side_by_side(self) -> None:
        from creib.forge.mini.runner import run_mini

        first = run_mini(self.compile(_blind_spot(ATTENTION_OFF)), self.tmp / "a", ScriptedResponder(_script()), "script:one")
        second = run_mini(
            self.compile(_blind_spot(ATTENTION_MOST_UNANSWERED)), self.tmp / "b", ScriptedResponder(_script()), "script:one"
        )
        rendered = compare_roots(first.root, second.root)
        self.assertEqual(rendered.count("### verdicts"), 2)
        self.assertEqual(rendered.count("### executed-unchanged ledger"), 2)


class ReorderingTests(MiniTestCase):
    """What the ordered form could not do: a stage keeps its reply across a re-order."""

    def _manifest(self, attention: str) -> dict:
        manifest = base_manifest()
        manifest["kinds"].append(
            {
                "kind_id": "k.note",
                "title": "Note",
                "input_ports": [{"port_id": "problem", "port_type": "problem"}],
                "output_port": {"port_id": "out", "produces_kind": "k.note"},
            }
        )
        manifest["stages"] = [
            {"stage_id": "c1", "kind_id": "k.conjecture", "ports": ["problem"]},
            {"stage_id": "x1", "kind_id": "k.criticism", "ports": ["problem", "conjectures"]},
            {"stage_id": "n1", "kind_id": "k.note", "ports": ["problem"]},
            {"stage_id": "c2", "kind_id": "k.conjecture", "ports": ["problem", "prior"]},
            {"stage_id": "end", "end": True},
        ]
        manifest["attention"] = {"policy": attention}
        return manifest

    def test_each_stage_keeps_its_own_reply_when_the_policy_reorders(self) -> None:
        conjecture_id = None
        script = {
            "c1": {"1": [submission("the first conjecture", "c")]},
            "x1": {"1": [submission("an objection", "c", about=["PLACEHOLDER"])]},
            "n1": {"1": [submission("a note", "c")]},
            "c2": {"1": [submission("the second conjecture", "c")]},
        }
        _, first = self.run_manifest(self._manifest(ATTENTION_OFF), script, name="first")
        conjecture_id = self.events_of(first, "ARTIFACT_SUBMITTED")[0]["artifact_id"]
        script["x1"] = {"1": [submission("an objection", "c", about=[conjecture_id])]}

        _, ordered = self.run_manifest(self._manifest(ATTENTION_OFF), script, name="ordered")
        _, reordered = self.run_manifest(self._manifest(ATTENTION_MOST_UNANSWERED), script, name="reordered")
        self.assertEqual(ordered.stages_entered, ("c1", "x1", "n1", "c2", "verdict"))
        self.assertEqual(reordered.stages_entered, ("c1", "x1", "c2", "n1", "verdict"))
        self.assertTrue(self.events_of(reordered, ATTENTION_CHOSE))

        def bodies(outcome) -> dict[str, str]:
            from creib.forge.mini.log import BlobStore

            store = BlobStore(outcome.root / "blobs")
            return {
                event["stage_id"]: store.get(event["body_ref"]).decode("utf-8")
                for event in self.events_of(outcome, "ARTIFACT_SUBMITTED")
            }

        # Every stage got its own reply on both runs, though the order moved.
        self.assertEqual(bodies(ordered), bodies(reordered))
        self.assertEqual(bodies(reordered)["c2"], "the second conjecture")
