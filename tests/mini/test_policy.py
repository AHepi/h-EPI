"""R17: what a stage may read, may write, and may change."""

from __future__ import annotations

import copy

from creib.forge.mini.log import REFUSED, ROUTED
from creib.forge.mini.policy import DEFAULT_POLICY_ID, load_policy, policy_from_dict

from .helpers import MiniTestCase, base_manifest, submission

PUSH_TO_A_CONJECTURERS_PORT = {
    "artifacts": [{"from_kind": "k.criticism", "to": {"target": "port", "stage_id": "c2", "port_id": "prior"}}]
}


def _two_conjecturers() -> dict:
    manifest = base_manifest()
    manifest["stages"] = [
        {"stage_id": "c1", "kind_id": "k.conjecture", "ports": ["problem"]},
        {"stage_id": "x1", "kind_id": "k.criticism", "ports": ["problem", "conjectures"]},
        {"stage_id": "c2", "kind_id": "k.conjecture", "ports": ["problem", "prior"]},
        {"stage_id": "end", "end": True},
    ]
    manifest["routing"] = copy.deepcopy(PUSH_TO_A_CONJECTURERS_PORT)
    return manifest


_SCRIPT = {
    "c1": [submission("A conjecture.", "c")],
    "x1": [submission("An objection.", "c")],
    "c2": [submission("A second conjecture.", "c")],
}


class DefaultPolicyTests(MiniTestCase):
    def test_the_shipped_document_says_what_the_three_sentences_say(self) -> None:
        policy = load_policy(DEFAULT_POLICY_ID)
        self.assertEqual(policy.defaults.read, "declared_ports")
        self.assertIn("own_output", policy.defaults.write)
        self.assertNotIn("port", policy.defaults.write)
        self.assertEqual(policy.defaults.changes, "nothing")
        self.assertEqual(policy.grants, ())

    def test_the_default_forbids_a_critic_writing_into_a_conjecturers_port(self) -> None:
        _, outcome = self.run_manifest(_two_conjecturers(), _SCRIPT)
        refusals = self.events_of(outcome, REFUSED)
        self.assertEqual(len(refusals), 1)
        self.assertEqual(refusals[0]["payload"]["code"], "MINI_POLICY_WRITE_REFUSED")
        self.assertEqual(refusals[0]["kind_id"], "k.criticism")
        self.assertEqual(refusals[0]["payload"]["to"]["port_id"], "prior")
        self.assertEqual(self.events_of(outcome, ROUTED), [])

    def test_the_refusal_does_not_stop_the_run(self) -> None:
        _, outcome = self.run_manifest(_two_conjecturers(), _SCRIPT)
        self.assertEqual(outcome.stages_entered, ("c1", "x1", "c2", "verdict"))
        self.assertEqual(outcome.stop_reason, "cycle_cap")


class OverrideTests(MiniTestCase):
    def test_an_override_permits_the_write(self) -> None:
        manifest = _two_conjecturers()
        manifest["policy"] = {
            "base": DEFAULT_POLICY_ID,
            "grants": [
                {"kind_id": "k.criticism", "may_write": [{"target": "port", "stage_id": "c2", "port_id": "prior"}]}
            ],
        }
        _, outcome = self.run_manifest(manifest, _SCRIPT)
        self.assertEqual(self.events_of(outcome, REFUSED), [])
        routed = self.events_of(outcome, ROUTED)
        self.assertEqual(len(routed), 1)
        self.assertEqual(routed[0]["payload"]["to"]["stage_id"], "c2")

    def test_an_override_of_a_different_port_does_not_permit_this_one(self) -> None:
        manifest = _two_conjecturers()
        manifest["policy"] = {
            "base": DEFAULT_POLICY_ID,
            "grants": [
                {"kind_id": "k.criticism", "may_write": [{"target": "port", "stage_id": "c2", "port_id": "evidence"}]}
            ],
        }
        _, outcome = self.run_manifest(manifest, _SCRIPT)
        self.assertEqual(len(self.events_of(outcome, REFUSED)), 1)

    def test_the_overrides_are_recorded_on_the_run(self) -> None:
        manifest = _two_conjecturers()
        grant = {"kind_id": "k.criticism", "may_write": [{"target": "port", "stage_id": "c2", "port_id": "prior"}]}
        manifest["policy"] = {"base": DEFAULT_POLICY_ID, "grants": [copy.deepcopy(grant)]}
        _, outcome = self.run_manifest(manifest, _SCRIPT)
        started = self.events_of(outcome, "RUN_STARTED")[0]
        self.assertEqual(started["payload"]["policy_overrides"], [grant])
        self.assertEqual(started["payload"]["policy_id"], DEFAULT_POLICY_ID)

    def test_a_read_the_policy_forbids_is_refused_on_the_record(self) -> None:
        manifest = base_manifest()
        manifest["policy"] = {
            "base": DEFAULT_POLICY_ID,
            "grants": [{"kind_id": "k.criticism", "may_read_port_types": ["problem"]}],
        }
        _, outcome = self.run_manifest(manifest)
        refusals = self.events_of(outcome, REFUSED)
        self.assertEqual(len(refusals), 1)
        self.assertEqual(refusals[0]["payload"]["code"], "MINI_POLICY_READ_REFUSED")
        self.assertEqual(refusals[0]["payload"]["port_id"], "conjectures")
        self.assertEqual(len(self.events_of(outcome, "ARTIFACT_SUBMITTED")), 2)

    def test_a_grant_naming_an_undeclared_kind_is_refused(self) -> None:
        manifest = base_manifest()
        manifest["policy"] = {"base": DEFAULT_POLICY_ID, "grants": [{"kind_id": "k.ghost"}]}
        self.assertRefuses("MINI_KIND_UNKNOWN", self.compile, manifest)

    def test_a_policy_document_that_is_not_there_is_refused(self) -> None:
        manifest = base_manifest()
        manifest["policy"] = {"base": "mini.policy.invented.v9"}
        self.assertRefuses("MINI_POLICY_UNKNOWN", self.compile, manifest)


class PolicyDocumentTests(MiniTestCase):
    def _document(self, **defaults) -> dict:
        return {
            "schema_version": "creib.mini.policy.v1",
            "policy_id": "mini.policy.test.v1",
            "defaults": {"read": "declared_ports", "write": ["own_output"], "changes": "nothing", **defaults},
            "grants": [],
        }

    def test_a_policy_claiming_to_change_a_standing_is_refused(self) -> None:
        """R17: the slot exists; this prototype implements only 'nothing'."""

        self.assertRefuses(
            "MINI_POLICY_CHANGE_UNSUPPORTED", policy_from_dict, self._document(changes="eliminates"), "policy"
        )

    def test_an_unknown_read_mode_is_refused(self) -> None:
        self.assertRefuses("MINI_POLICY_DEFAULT_UNKNOWN", policy_from_dict, self._document(read="everything"), "policy")

    def test_an_unknown_write_mode_is_refused(self) -> None:
        self.assertRefuses(
            "MINI_POLICY_DEFAULT_UNKNOWN", policy_from_dict, self._document(write=["the_internet"]), "policy"
        )

    def test_a_document_whose_id_does_not_match_its_name_is_refused(self) -> None:
        self.write_json("policies/mini.policy.test.v1.json", self._document())
        (self.tmp / "policies" / "mini.policy.other.v1.json").write_bytes(
            (self.tmp / "policies" / "mini.policy.test.v1.json").read_bytes()
        )
        self.assertRefuses("MINI_POLICY_UNKNOWN", load_policy, "mini.policy.other.v1", self.tmp / "policies")

    def test_a_run_may_name_a_policy_document_of_its_own(self) -> None:
        self.write_json(
            "policies/mini.policy.test.v1.json",
            {
                "schema_version": "creib.mini.policy.v1",
                "policy_id": "mini.policy.test.v1",
                "defaults": {"read": "declared_ports", "write": ["own_output", "evidence_store", "scratch", "nowhere"], "changes": "nothing"},
                "grants": [{"kind_id": "k.criticism", "may_write": [{"target": "port", "stage_id": "c2", "port_id": "prior"}]}],
            },
        )
        manifest = _two_conjecturers()
        manifest["policy"] = {"base": "mini.policy.test.v1"}
        plan = self.compile(manifest, policy_dir=self.tmp / "policies")
        outcome = self.run_plan(plan, dict(_SCRIPT))
        self.assertEqual(self.events_of(outcome, REFUSED), [])
        self.assertEqual(len(self.events_of(outcome, ROUTED)), 1)
