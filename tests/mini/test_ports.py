"""R5: input port types are a registry the manifest extends at compile time."""

from __future__ import annotations

import copy

from creib.forge.mini.ports import BUILTIN_PORT_TYPES, check_port_params, port_type_from_dict

from .helpers import MiniTestCase, base_manifest, submission

A_DECLARED_PORT_TYPE = {
    "port_type": "criticisms",
    "draws_from": {"artifact_kinds": ["k.criticism"]},
    "render": {"rule": "list_bodies", "header": "Criticisms so far"},
}


class DeclaredPortTypeTests(MiniTestCase):
    def test_a_manifest_may_declare_a_new_port_type_and_a_kind_may_use_it(self) -> None:
        manifest = base_manifest()
        manifest["port_types"] = [copy.deepcopy(A_DECLARED_PORT_TYPE)]
        manifest["kinds"].append(
            {
                "kind_id": "k.reply",
                "title": "Reply",
                "input_ports": [{"port_id": "criticisms", "port_type": "criticisms"}],
                "output_port": {"port_id": "out", "produces_kind": "k.reply"},
            }
        )
        manifest["stages"] = [
            {"stage_id": "c1", "kind_id": "k.conjecture", "ports": ["problem"]},
            {"stage_id": "x1", "kind_id": "k.criticism", "ports": ["problem", "conjectures"]},
            {"stage_id": "r1", "kind_id": "k.reply", "ports": ["criticisms"]},
            {"stage_id": "end", "end": True},
        ]
        script = {
            "c1": [submission("A conjecture.", "c")],
            "x1": [submission("An objection.", "c")],
            "r1": [submission("A reply to the objection.", "c")],
        }
        plan, outcome = self.run_manifest(manifest, script)
        self.assertIn("criticisms", plan.port_types)
        self.assertEqual(outcome.stages_entered, ("c1", "x1", "r1", "verdict"))

    def test_a_port_naming_a_type_no_registry_entry_defines_is_refused(self) -> None:
        manifest = base_manifest()
        manifest["kinds"][0]["input_ports"].append({"port_id": "invented", "port_type": "nobody-declared-this"})
        self.assertRefuses("MINI_PORT_TYPE_UNKNOWN", self.compile, manifest)

    def test_a_declared_port_type_that_repeats_a_built_in_is_refused(self) -> None:
        manifest = base_manifest()
        manifest["port_types"] = [
            {"port_type": "problem", "draws_from": {"artifact_kinds": ["k.conjecture"]}, "render": {"rule": "list_bodies"}}
        ]
        self.assertRefuses("MINI_PORT_TYPE_DUPLICATE", self.compile, manifest)

    def test_a_port_type_drawing_from_both_or_neither_is_refused(self) -> None:
        for draws in ({}, {"artifact_kinds": ["k.conjecture"], "evidence_tiers": ["evidence"]}):
            with self.subTest(draws=draws):
                self.assertRefuses(
                    "MINI_PORT_TYPE_DRAWS_FROM_INVALID",
                    port_type_from_dict,
                    {"port_type": "p", "draws_from": draws, "render": {"rule": "list_bodies"}},
                    "port_types[0]",
                )

    def test_a_port_type_drawing_from_an_empty_list_is_refused(self) -> None:
        self.assertRefuses(
            "MINI_PORT_TYPE_DRAWS_FROM_INVALID",
            port_type_from_dict,
            {"port_type": "p", "draws_from": {"artifact_kinds": []}, "render": {"rule": "list_bodies"}},
            "port_types[0]",
        )

    def test_a_rendering_rule_outside_the_vocabulary_is_refused(self) -> None:
        self.assertRefuses(
            "MINI_RENDER_RULE_UNKNOWN",
            port_type_from_dict,
            {"port_type": "p", "draws_from": {"artifact_kinds": ["k.conjecture"]}, "render": {"rule": "interpretive-dance"}},
            "port_types[0]",
        )

    def test_a_rendering_rule_that_cannot_render_what_it_draws_from_is_refused(self) -> None:
        self.assertRefuses(
            "MINI_PORT_TYPE_DRAWS_FROM_INVALID",
            port_type_from_dict,
            {"port_type": "p", "draws_from": {"artifact_kinds": ["k.conjecture"]}, "render": {"rule": "legend"}},
            "port_types[0]",
        )

    def test_a_port_type_drawing_from_an_undeclared_kind_is_refused(self) -> None:
        manifest = base_manifest()
        manifest["port_types"] = [
            {"port_type": "ghosts", "draws_from": {"artifact_kinds": ["k.ghost"]}, "render": {"rule": "list_bodies"}}
        ]
        manifest["kinds"][0]["input_ports"].append({"port_id": "ghosts", "port_type": "ghosts"})
        self.assertRefuses("MINI_KIND_UNKNOWN", self.compile, manifest)

    def test_a_port_drawing_from_an_undeclared_tier_is_refused(self) -> None:
        manifest = base_manifest()
        manifest["kinds"][0]["input_ports"][1]["params"] = {"tiers": ["hearsay"]}
        self.assertRefuses("MINI_TIER_UNKNOWN", self.compile, manifest)


_EVIDENCE_LEGEND = {item.port_type: item for item in BUILTIN_PORT_TYPES}["evidence_legend"]


class PortParameterTests(MiniTestCase):
    def test_a_built_in_port_missing_its_parameter_is_refused(self) -> None:
        manifest = base_manifest()
        manifest["kinds"][0]["input_ports"][1] = {"port_id": "evidence", "port_type": "evidence_legend"}
        self.assertRefuses("MINI_PORT_PARAMS_INVALID", self.compile, manifest)

    def test_a_built_in_port_with_an_unknown_parameter_is_refused(self) -> None:
        manifest = base_manifest()
        manifest["kinds"][0]["input_ports"][0] = {"port_id": "problem", "port_type": "problem", "params": {"depth": "2"}}
        self.assertRefuses("MINI_PORT_PARAMS_INVALID", self.compile, manifest)

    def test_a_declared_port_type_takes_no_parameters(self) -> None:
        manifest = base_manifest()
        manifest["port_types"] = [copy.deepcopy(A_DECLARED_PORT_TYPE)]
        manifest["kinds"][0]["input_ports"].append(
            {"port_id": "criticisms", "port_type": "criticisms", "params": {"kind_id": "k.criticism"}}
        )
        self.assertRefuses("MINI_PORT_PARAMS_INVALID", self.compile, manifest)

    def test_an_empty_tier_list_is_refused(self) -> None:
        port_type = _EVIDENCE_LEGEND
        self.assertRefuses("MINI_PORT_PARAMS_INVALID", check_port_params, port_type, {"tiers": []}, "port")

    def test_a_tier_that_is_not_a_string_is_refused(self) -> None:
        port_type = _EVIDENCE_LEGEND
        self.assertRefuses("MINI_PORT_PARAMS_INVALID", check_port_params, port_type, {"tiers": [3]}, "port")
