"""R4, R6, R7: one template, kinds as records, body and commitments only."""

from __future__ import annotations

import copy
import json

from creib.forge.mini.kinds import kind_from_dict, read_submission
from creib.forge.mini.log import ARTIFACT_SUBMITTED, replay

from .helpers import CONJECTURE_KIND, MiniTestCase, base_manifest, submission

A_THIRD_KIND = {
    "kind_id": "example.note.v1",
    "title": "Note",
    "input_ports": [
        {"port_id": "problem", "port_type": "problem"},
        {"port_id": "conjectures", "port_type": "artifacts_of_kind", "params": {"kind_id": "k.conjecture"}},
    ],
    "output_port": {"port_id": "out", "produces_kind": "example.note.v1"},
}


class OneTemplateTests(MiniTestCase):
    def test_both_shipped_seats_are_the_same_template(self) -> None:
        """R4: conjecturer and critic differ only in the record that declares them."""

        plan, _ = self.run_manifest(base_manifest())
        conjecture, criticism = plan.kinds["k.conjecture"], plan.kinds["k.criticism"]
        self.assertIs(type(conjecture), type(criticism))
        self.assertEqual(conjecture.output_port.produces_kind, "k.conjecture")
        self.assertEqual(criticism.output_port.produces_kind, "k.criticism")

    def test_a_kind_declared_only_in_a_manifest_is_compiled_scheduled_produced_and_logged(self) -> None:
        """R6: a third kind is a third record, and no code knows its name."""

        manifest = base_manifest()
        manifest["kinds"].append(copy.deepcopy(A_THIRD_KIND))
        manifest["stages"] = [
            {"stage_id": "c1", "kind_id": "k.conjecture", "ports": ["problem"]},
            {"stage_id": "n1", "kind_id": "example.note.v1", "ports": ["problem", "conjectures"]},
            {"stage_id": "end", "end": True},
        ]
        script = {
            "c1": [submission("A conjecture.", "A commitment.")],
            "n1": [submission("A note about it.", "Nothing follows from a note.")],
        }
        plan, outcome = self.run_manifest(manifest, script)
        self.assertIn("example.note.v1", plan.kinds)
        self.assertEqual(outcome.stages_entered, ("c1", "n1"))
        logged = [event["kind_id"] for event in self.events_of(outcome, ARTIFACT_SUBMITTED)]
        self.assertEqual(logged, ["k.conjecture", "example.note.v1"])
        source = (self.tmp / "manifest.json").read_text(encoding="utf-8")
        self.assertIn("example.note.v1", source)

    def test_a_kind_read_from_its_own_file_compiles(self) -> None:
        """R6: a kind is a JSON document, or a section of the manifest."""

        self.write_json("kinds/note.json", {"schema_version": "creib.mini.kind.v1", "kind": copy.deepcopy(A_THIRD_KIND)})
        manifest = base_manifest()
        manifest["kinds"].append("kinds/note.json")
        plan = self.compile(manifest)
        self.assertIn("example.note.v1", plan.kinds)


class BodyAndCommitmentsTests(MiniTestCase):
    def test_two_fields_are_enough(self) -> None:
        """R7: a submission carrying only body and commitments is accepted."""

        kind = kind_from_dict(copy.deepcopy(CONJECTURE_KIND), "kind")
        read = read_submission(submission("A body.", "A commitment."), kind)
        self.assertEqual(read.body, "A body.")
        self.assertEqual(read.commitments, "A commitment.")
        self.assertEqual(read.citations, ())

    def test_a_submission_missing_the_body_is_refused(self) -> None:
        kind = kind_from_dict(copy.deepcopy(CONJECTURE_KIND), "kind")
        self.assertRefuses("MINI_SUBMISSION_MISSING_FIELD", read_submission, json.dumps({"commitments": "x"}), kind)

    def test_a_submission_missing_the_commitments_is_refused(self) -> None:
        kind = kind_from_dict(copy.deepcopy(CONJECTURE_KIND), "kind")
        self.assertRefuses("MINI_SUBMISSION_MISSING_FIELD", read_submission, json.dumps({"body": "x"}), kind)

    def test_a_field_of_the_wrong_type_is_refused(self) -> None:
        kind = kind_from_dict(copy.deepcopy(CONJECTURE_KIND), "kind")
        self.assertRefuses("MINI_SUBMISSION_FIELD_TYPE", read_submission, json.dumps({"body": 1, "commitments": "x"}), kind)

    def test_a_reply_that_is_not_json_is_refused(self) -> None:
        kind = kind_from_dict(copy.deepcopy(CONJECTURE_KIND), "kind")
        self.assertRefuses("MINI_SUBMISSION_NOT_JSON", read_submission, "not json at all", kind)

    def test_a_reply_that_is_not_an_object_is_refused(self) -> None:
        kind = kind_from_dict(copy.deepcopy(CONJECTURE_KIND), "kind")
        self.assertRefuses("MINI_SUBMISSION_NOT_JSON", read_submission, "[1, 2]", kind)

    def test_a_field_the_kind_never_declared_is_refused(self) -> None:
        kind = kind_from_dict(copy.deepcopy(CONJECTURE_KIND), "kind")
        self.assertRefuses(
            "MINI_SUBMISSION_UNKNOWN_FIELD",
            read_submission,
            submission("a", "b", surprise="x"),
            kind,
        )

    def test_a_kind_may_declare_further_optional_fields(self) -> None:
        raw = copy.deepcopy(CONJECTURE_KIND)
        raw["optional_fields"] = ["rationale"]
        kind = kind_from_dict(raw, "kind")
        self.assertEqual(read_submission(submission("a", "b"), kind).extra, {})
        self.assertEqual(read_submission(submission("a", "b", rationale="why"), kind).extra, {"rationale": "why"})

    def test_a_kind_may_not_redeclare_a_template_field(self) -> None:
        raw = copy.deepcopy(CONJECTURE_KIND)
        raw["optional_fields"] = ["citations"]
        self.assertRefuses("MINI_SUBMISSION_UNKNOWN_FIELD", kind_from_dict, raw, "kind")

    def test_a_kind_producing_another_kind_is_refused(self) -> None:
        raw = copy.deepcopy(CONJECTURE_KIND)
        raw["output_port"] = {"port_id": "out", "produces_kind": "k.criticism"}
        self.assertRefuses("MINI_KIND_OUTPUT_MISMATCH", kind_from_dict, raw, "kind")

    def test_a_kind_declaring_one_port_twice_is_refused(self) -> None:
        raw = copy.deepcopy(CONJECTURE_KIND)
        raw["input_ports"].append({"port_id": "problem", "port_type": "problem"})
        self.assertRefuses("MINI_KIND_PORT_DUPLICATE", kind_from_dict, raw, "kind")

    def test_asking_a_kind_for_a_port_it_does_not_have_is_refused(self) -> None:
        kind = kind_from_dict(copy.deepcopy(CONJECTURE_KIND), "kind")
        self.assertRefuses("MINI_PORT_UNKNOWN", kind.port, "nowhere")

    def test_about_and_answers_are_read_as_lists_of_ids(self) -> None:
        kind = kind_from_dict(copy.deepcopy(CONJECTURE_KIND), "kind")
        read = read_submission(submission("a", "b", about=["x"], answers=["y"]), kind)
        self.assertEqual((read.about, read.answers), (("x",), ("y",)))

    def test_about_carrying_something_other_than_ids_is_refused(self) -> None:
        kind = kind_from_dict(copy.deepcopy(CONJECTURE_KIND), "kind")
        self.assertRefuses("MINI_SUBMISSION_FIELD_TYPE", read_submission, submission("a", "b", about=[1]), kind)

    def test_citations_that_are_not_objects_are_refused(self) -> None:
        kind = kind_from_dict(copy.deepcopy(CONJECTURE_KIND), "kind")
        self.assertRefuses("MINI_SUBMISSION_FIELD_TYPE", read_submission, submission("a", "b", citations=["x"]), kind)

    def test_an_accepted_artifact_replays_from_the_log(self) -> None:
        plan, outcome = self.run_manifest(base_manifest())
        state = replay(outcome.root / "log.jsonl", plan.genesis)
        self.assertEqual(len(state.artifact_order), 2)
        self.assertEqual(state.digest(), outcome.state_digest)
