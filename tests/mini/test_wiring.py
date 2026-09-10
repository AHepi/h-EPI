"""R14, R15, R16: the order is the user's, and so is where everything goes."""

from __future__ import annotations

import copy

from creib.forge.mini.log import ARTIFACT_SUBMITTED, EVIDENCE_BATCHED, ROUTED, STAGE_ENTERED
from creib.forge.mini.routing import destination_from_dict, routing_from_dict

from .helpers import MiniTestCase, base_manifest, submission

NOTE_KIND = {
    "kind_id": "example.note.v1",
    "title": "Note",
    "input_ports": [
        {"port_id": "problem", "port_type": "problem"},
        {"port_id": "generated", "port_type": "artifacts_of_kind", "params": {"kind_id": "k.conjecture"}},
        {"port_id": "criticisms", "port_type": "artifacts_of_kind", "params": {"kind_id": "k.criticism"}},
    ],
    "output_port": {"port_id": "out", "produces_kind": "example.note.v1"},
}


def _operator_example() -> dict:
    manifest = base_manifest()
    manifest["kinds"].append(copy.deepcopy(NOTE_KIND))
    manifest["stages"] = [
        {"stage_id": "conjecture-1", "kind_id": "k.conjecture", "ports": ["problem"]},
        {"stage_id": "conjecture-2", "kind_id": "k.conjecture", "ports": ["problem", "prior"]},
        {"stage_id": "note-1", "kind_id": "example.note.v1", "ports": ["problem", "generated"]},
        {"stage_id": "criticism", "kind_id": "k.criticism", "ports": ["problem", "conjectures"]},
        {"stage_id": "note-2", "kind_id": "example.note.v1", "ports": ["criticisms"]},
        {"stage_id": "end", "end": True},
    ]
    return manifest


_EXAMPLE_SCRIPT = {
    "conjecture-1": [submission("First conjecture.", "c")],
    "conjecture-2": [submission("Second conjecture.", "c")],
    "note-1": [submission("A note on both.", "c")],
    "criticism": [submission("An objection.", "c")],
    "note-2": [submission("A note on the objection.", "c")],
}


class DeclaredOrderTests(MiniTestCase):
    def test_the_operators_own_order_runs_as_written(self) -> None:
        """R14: Conjecturer, Conjecturer, New Type, Critic, New Type, End."""

        _, outcome = self.run_manifest(_operator_example(), _EXAMPLE_SCRIPT)
        self.assertEqual(
            outcome.stages_entered,
            ("conjecture-1", "conjecture-2", "note-1", "criticism", "note-2", "verdict"),
        )
        self.assertEqual(outcome.stop_reason, "cycle_cap")
        self.assertEqual(
            [event["kind_id"] for event in self.events_of(outcome, ARTIFACT_SUBMITTED)],
            ["k.conjecture", "k.conjecture", "example.note.v1", "k.criticism", "example.note.v1", "mini.verdict.v1"],
        )

    def test_the_shipped_operator_example_manifest_compiles_and_runs(self) -> None:
        from pathlib import Path

        from creib.forge.mini.manifest import compile_manifest

        root = Path(__file__).resolve().parents[2]
        plan = compile_manifest(root / "forge" / "mini" / "manifests" / "operator-example" / "manifest.json")
        self.assertEqual(
            [stage.stage_id for stage in plan.stages],
            ["conjecture-1", "conjecture-2", "note-1", "criticism", "note-2", "verdict", "end"],
        )
        outcome = self.run_plan(plan, {**_EXAMPLE_SCRIPT, "verdict": [submission("a verdict", "c")]})
        self.assertEqual(len(outcome.stages_entered), 6)

    def test_a_stage_list_that_does_not_end_is_refused(self) -> None:
        manifest = base_manifest()
        manifest["stages"] = manifest["stages"][:-1]
        self.assertRefuses("MINI_STAGE_NO_END", self.compile, manifest)

    def test_an_end_stage_that_is_not_last_is_refused(self) -> None:
        manifest = base_manifest()
        manifest["stages"] = [{"stage_id": "end", "end": True}, {"stage_id": "later", "end": True}]
        self.assertRefuses("MINI_STAGE_END_NOT_LAST", self.compile, manifest)

    def test_a_stage_naming_an_undeclared_kind_is_refused(self) -> None:
        manifest = base_manifest()
        manifest["stages"][0]["kind_id"] = "k.ghost"
        self.assertRefuses("MINI_KIND_UNKNOWN", self.compile, manifest)

    def test_a_stage_naming_a_port_its_kind_does_not_declare_is_refused(self) -> None:
        manifest = base_manifest()
        manifest["stages"][0]["ports"] = ["problem", "nowhere"]
        self.assertRefuses("MINI_PORT_UNKNOWN", self.compile, manifest)

    def test_a_stage_id_declared_twice_is_refused(self) -> None:
        manifest = base_manifest()
        manifest["stages"].insert(1, dict(manifest["stages"][0]))
        self.assertRefuses("MINI_STAGE_DUPLICATE", self.compile, manifest)

    def test_a_kind_declared_twice_is_refused(self) -> None:
        manifest = base_manifest()
        manifest["kinds"].append(copy.deepcopy(manifest["kinds"][0]))
        self.assertRefuses("MINI_KIND_DUPLICATE", self.compile, manifest)

    def test_asking_a_plan_for_a_stage_it_has_not_got_is_refused(self) -> None:
        plan = self.compile(base_manifest())
        self.assertRefuses("MINI_STAGE_UNKNOWN", plan.stage, "nowhere")


class DefaultRoutingTests(MiniTestCase):
    def test_with_no_routing_a_critic_still_sees_the_conjectures(self) -> None:
        """R16: the default pull gives an ordinary run sensible behaviour."""

        from creib.forge.mini.log import BlobStore, replay
        from creib.forge.mini.runner import render_brief

        plan, outcome = self.run_manifest(base_manifest())
        state = replay(outcome.root / "log.jsonl", plan.genesis)
        brief, _ = render_brief(plan, state, BlobStore(outcome.root / "blobs"), plan.stage("x1"))
        self.assertIn("The two paragraphs disagree.", brief)

    def test_an_empty_routing_section_is_the_default(self) -> None:
        manifest = base_manifest()
        manifest["routing"] = {}
        plan, outcome = self.run_manifest(manifest)
        self.assertEqual(plan.routing.artifacts, {})
        self.assertEqual(self.events_of(outcome, ROUTED), [])
        self.assertEqual(len(self.events_of(outcome, ARTIFACT_SUBMITTED)), 3)


class DeclaredRoutingTests(MiniTestCase):
    def test_a_critics_output_can_be_pushed_into_a_new_kinds_port(self) -> None:
        """R16, with the permission the default policy withholds."""

        manifest = _operator_example()
        manifest["kinds"][2]["input_ports"].append(
            {"port_id": "pushed", "port_type": "artifacts_of_kind", "params": {"kind_id": "k.criticism"}}
        )
        manifest["stages"][4]["ports"] = ["pushed"]
        manifest["routing"] = {
            "artifacts": [{"from_kind": "k.criticism", "to": {"target": "port", "stage_id": "note-2", "port_id": "pushed"}}]
        }
        manifest["policy"] = {
            "base": "mini.policy.default.v1",
            "grants": [
                {
                    "kind_id": "k.criticism",
                    "may_write": [{"target": "port", "stage_id": "note-2", "port_id": "pushed"}],
                }
            ],
        }
        _, outcome = self.run_manifest(manifest, _EXAMPLE_SCRIPT)
        routed = [event for event in self.events_of(outcome, ROUTED) if event["kind_id"] == "k.criticism"]
        self.assertEqual(len(routed), 1)
        self.assertEqual(routed[0]["payload"]["to"]["stage_id"], "note-2")

    def test_an_artifact_can_be_routed_into_the_evidence_store(self) -> None:
        manifest = base_manifest()
        manifest["routing"] = {
            "artifacts": [{"from_kind": "k.conjecture", "to": {"target": "evidence_store", "tier": "generated"}}]
        }
        _, outcome = self.run_manifest(manifest)
        generated = [event for event in self.events_of(outcome, EVIDENCE_BATCHED) if event["payload"]["tier"] == "generated"]
        self.assertEqual(len(generated), 1)
        self.assertTrue(generated[0]["payload"]["blocks"])

    def test_an_artifact_can_be_routed_to_scratch_and_read_back_from_it(self) -> None:
        manifest = base_manifest()
        manifest["kinds"][1]["input_ports"].append(
            {"port_id": "notes", "port_type": "scratch", "params": {"destination": "shelf"}}
        )
        manifest["stages"][1]["ports"] = ["problem", "notes"]
        manifest["routing"] = {
            "artifacts": [{"from_kind": "k.conjecture", "to": {"target": "scratch", "destination": "shelf"}}]
        }
        plan, outcome = self.run_manifest(manifest)
        from creib.forge.mini.log import BlobStore, replay
        from creib.forge.mini.runner import render_brief

        state = replay(outcome.root / "log.jsonl", plan.genesis)
        self.assertEqual(len(state.scratch["shelf"]), 1)
        brief, _ = render_brief(plan, state, BlobStore(outcome.root / "blobs"), plan.stage("x1"))
        self.assertIn("The two paragraphs disagree.", brief)

    def test_a_kind_routed_nowhere_reaches_no_port_at_all(self) -> None:
        """R22, B2: absence from every port, not merely a routing event."""

        manifest = base_manifest()
        manifest["routing"] = {"artifacts": [{"from_kind": "k.conjecture", "to": {"target": "nowhere"}}]}
        plan, outcome = self.run_manifest(manifest)
        self.assertEqual(self.events_of(outcome, ROUTED)[0]["payload"]["to"], {"target": "nowhere"})
        self.assertNotIn("The two paragraphs disagree.", self._every_brief(plan, outcome))

    def test_a_declared_route_replaces_the_default_draw(self) -> None:
        """R22: routed to scratch, the conjecture no longer reaches the critic's port."""

        manifest = base_manifest()
        manifest["routing"] = {
            "artifacts": [{"from_kind": "k.conjecture", "to": {"target": "scratch", "destination": "shelf"}}]
        }
        plan, outcome = self.run_manifest(manifest)
        from creib.forge.mini.log import BlobStore, replay
        from creib.forge.mini.runner import render_brief

        state = replay(outcome.root / "log.jsonl", plan.genesis)
        critic, _ = render_brief(plan, state, BlobStore(outcome.root / "blobs"), plan.stage("x1"))
        self.assertIn("nothing yet", critic)
        self.assertNotIn("The two paragraphs disagree.", critic)

    def test_a_push_is_additive_on_top_of_what_the_route_allows(self) -> None:
        """R22, B1: scratch and a push together, both delivered."""

        manifest = base_manifest()
        manifest["kinds"][1]["input_ports"].append(
            {"port_id": "notes", "port_type": "scratch", "params": {"destination": "shelf"}}
        )
        manifest["kinds"][1]["input_ports"].append(
            {"port_id": "pushed", "port_type": "artifacts_of_kind", "params": {"kind_id": "k.conjecture"}}
        )
        manifest["stages"][1]["ports"] = ["notes", "pushed"]
        manifest["routing"] = {
            "artifacts": [
                {"from_kind": "k.conjecture", "to": {"target": "scratch", "destination": "shelf"}},
                {"from_kind": "k.conjecture", "to": {"target": "port", "stage_id": "x1", "port_id": "pushed"}},
            ]
        }
        manifest["policy"] = {
            "base": "mini.policy.default.v1",
            "grants": [
                {"kind_id": "k.conjecture", "may_write": [{"target": "port", "stage_id": "x1", "port_id": "pushed"}]}
            ],
        }
        plan, outcome = self.run_manifest(manifest)
        from creib.forge.mini.log import BlobStore, replay
        from creib.forge.mini.runner import render_brief, render_port

        state = replay(outcome.root / "log.jsonl", plan.genesis)
        blobs = BlobStore(outcome.root / "blobs")
        for port_id in ("notes", "pushed"):
            rendered, _ = render_port(plan, state, blobs, plan.stage("x1"), port_id)
            self.assertIn("The two paragraphs disagree.", rendered, port_id)

    def test_a_push_the_policy_refused_reaches_no_port(self) -> None:
        """R22: the route replaces the default, and a refused push delivers nothing."""

        manifest = base_manifest()
        manifest["kinds"][1]["input_ports"].append(
            {"port_id": "pushed", "port_type": "artifacts_of_kind", "params": {"kind_id": "k.conjecture"}}
        )
        manifest["stages"][1]["ports"] = ["problem", "conjectures", "pushed"]
        manifest["routing"] = {
            "artifacts": [{"from_kind": "k.conjecture", "to": {"target": "port", "stage_id": "x1", "port_id": "pushed"}}]
        }
        plan, outcome = self.run_manifest(manifest)
        self.assertEqual(self.events_of(outcome, "REFUSED")[0]["payload"]["code"], "MINI_POLICY_WRITE_REFUSED")
        self.assertNotIn("The two paragraphs disagree.", self._every_brief(plan, outcome))

    def test_evidence_can_be_aimed_at_one_port_type(self) -> None:
        """R15: where a batch of evidence goes is declared, not fixed."""

        manifest = base_manifest()
        manifest["port_types"] = [
            {
                "port_type": "quiet_evidence",
                "draws_from": {"evidence_tiers": ["evidence"]},
                "render": {"rule": "legend", "header": "Quiet evidence"},
            }
        ]
        manifest["kinds"][1]["input_ports"].append({"port_id": "quiet", "port_type": "quiet_evidence"})
        manifest["stages"][1]["ports"] = ["problem", "quiet"]
        manifest["routing"] = {
            "evidence": [{"from_tier": "evidence", "to": {"target": "port_type", "port_type": "quiet_evidence"}}]
        }
        plan, outcome = self.run_manifest(manifest)
        from creib.forge.mini.log import BlobStore, replay
        from creib.forge.mini.runner import render_brief

        state = replay(outcome.root / "log.jsonl", plan.genesis)
        blobs = BlobStore(outcome.root / "blobs")
        conjecturer, exposed_to_conjecturer = render_brief(plan, state, blobs, plan.stage("c1"))
        critic, exposed_to_critic = render_brief(plan, state, blobs, plan.stage("x1"))
        self.assertEqual(exposed_to_conjecturer, frozenset())
        self.assertNotEqual(exposed_to_critic, frozenset())
        self.assertIn("nothing admitted", conjecturer)
        self.assertIn("first paragraph", critic)

    def test_evidence_can_be_routed_to_scratch(self) -> None:
        manifest = base_manifest()
        manifest["kinds"][0]["input_ports"].append(
            {"port_id": "shelf", "port_type": "scratch", "params": {"destination": "shelf"}}
        )
        manifest["stages"][0]["ports"] = ["problem", "shelf"]
        manifest["routing"] = {
            "evidence": [{"from_tier": "evidence", "to": {"target": "scratch", "destination": "shelf"}}]
        }
        plan, outcome = self.run_manifest(manifest)
        from creib.forge.mini.log import BlobStore, replay
        from creib.forge.mini.runner import render_brief

        state = replay(outcome.root / "log.jsonl", plan.genesis)
        self.assertEqual(len(state.scratch_blocks["shelf"]), 2)
        brief, exposed = render_brief(plan, state, BlobStore(outcome.root / "blobs"), plan.stage("c1"))
        self.assertEqual(len(exposed), 2)
        self.assertIn("first paragraph", brief)


class RoutingRefusalTests(MiniTestCase):
    def test_a_route_to_an_unknown_target_is_refused(self) -> None:
        self.assertRefuses(
            "MINI_ROUTE_TARGET_UNKNOWN", destination_from_dict, {"target": "the-moon"}, "routing", ("port", "nowhere")
        )

    def test_a_route_missing_what_its_target_needs_is_refused(self) -> None:
        self.assertRefuses(
            "MINI_ROUTE_INVALID", destination_from_dict, {"target": "port", "stage_id": "s"}, "routing", ("port",)
        )

    def test_a_kind_may_carry_more_than_one_route(self) -> None:
        """R22, B1: a push is additive on top of whatever the route allows."""

        routing = routing_from_dict(
            {
                "artifacts": [
                    {"from_kind": "k", "to": {"target": "scratch", "destination": "shelf"}},
                    {"from_kind": "k", "to": {"target": "port", "stage_id": "s", "port_id": "p"}},
                ]
            },
            "routing",
        )
        self.assertEqual([item.target for item in routing.for_artifact("k")], ["scratch", "port"])

    def test_nowhere_may_not_be_combined_with_another_route(self) -> None:
        for section, key in (("artifacts", "from_kind"), ("evidence", "from_tier")):
            with self.subTest(section=section):
                self.assertRefuses(
                    "MINI_ROUTE_INVALID",
                    routing_from_dict,
                    {
                        section: [
                            {key: "x", "to": {"target": "nowhere"}},
                            {key: "x", "to": {"target": "scratch", "destination": "shelf"}},
                        ]
                    },
                    "routing",
                )

    def test_an_unrouted_kind_reaches_every_port_that_draws_it(self) -> None:
        self.assertEqual(routing_from_dict(None, "routing").for_artifact("k"), ())

    def test_routing_an_undeclared_kind_is_refused(self) -> None:
        manifest = base_manifest()
        manifest["routing"] = {"artifacts": [{"from_kind": "k.ghost", "to": {"target": "nowhere"}}]}
        self.assertRefuses("MINI_ROUTE_INVALID", self.compile, manifest)

    def test_routing_to_a_stage_that_does_not_exist_is_refused(self) -> None:
        manifest = base_manifest()
        manifest["routing"] = {
            "artifacts": [{"from_kind": "k.conjecture", "to": {"target": "port", "stage_id": "ghost", "port_id": "prior"}}]
        }
        self.assertRefuses("MINI_ROUTE_INVALID", self.compile, manifest)

    def test_routing_to_the_end_stage_is_refused(self) -> None:
        manifest = base_manifest()
        manifest["routing"] = {
            "artifacts": [{"from_kind": "k.conjecture", "to": {"target": "port", "stage_id": "end", "port_id": "prior"}}]
        }
        self.assertRefuses("MINI_ROUTE_INVALID", self.compile, manifest)

    def test_routing_to_a_port_that_stages_kind_does_not_declare_is_refused(self) -> None:
        manifest = base_manifest()
        manifest["routing"] = {
            "artifacts": [{"from_kind": "k.conjecture", "to": {"target": "port", "stage_id": "x1", "port_id": "ghost"}}]
        }
        self.assertRefuses("MINI_ROUTE_INVALID", self.compile, manifest)

    def test_routing_into_an_undeclared_tier_is_refused(self) -> None:
        manifest = base_manifest()
        manifest["routing"] = {
            "artifacts": [{"from_kind": "k.conjecture", "to": {"target": "evidence_store", "tier": "hearsay"}}]
        }
        self.assertRefuses("MINI_TIER_UNKNOWN", self.compile, manifest)

    def test_routing_an_undeclared_tier_is_refused(self) -> None:
        manifest = base_manifest()
        manifest["routing"] = {"evidence": [{"from_tier": "hearsay", "to": {"target": "nowhere"}}]}
        self.assertRefuses("MINI_TIER_UNKNOWN", self.compile, manifest)

    def test_routing_evidence_to_an_undeclared_port_type_is_refused(self) -> None:
        manifest = base_manifest()
        manifest["routing"] = {
            "evidence": [{"from_tier": "evidence", "to": {"target": "port_type", "port_type": "ghost"}}]
        }
        self.assertRefuses("MINI_ROUTE_INVALID", self.compile, manifest)
