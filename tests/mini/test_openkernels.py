"""Kernels named by import path rather than drawn from the registry (mini register M24).

Before this, a proposer could only name a boundary point somebody had written a ``register_kernel``
call for. These tests pin the three bounds the module declares -- the module allowlist, one
argument, and a raise counting as unreadable rather than a move -- and reach every refusal, because
each one is a refusal a proposer can provoke by writing a path.
"""

from __future__ import annotations

import json

from creib.forge.mini import conformance_kernels as kernels  # noqa: F401  registers the harness checks
from creib.forge.mini.blindspot import PAIR_EXECUTION_KIND, VERDICT_KIND
from creib.forge.mini.common import MiniError
from creib.forge.mini.log import BlobStore, replay
from creib.forge.mini.openkernels import (
    OPEN_MODULES,
    PAIR_EXECUTION_OPEN_KIND,
    RAISED,
    is_open_kernel_id,
    open_kernel_brief,
    resolve_any_kernel,
    resolve_open_kernel,
)

from .helpers import MiniTestCase, submission

WHITESPACE = "open:creib.forge.conformance.oracle._normalise_whitespace"
DMY = "open:creib.forge.conformance.families.iso_date_to_dmy"


def _proposal(kernel: str, source: str, rewritten: str, expect: str) -> str:
    return submission("a body", json.dumps(
        {"kernel": kernel, "input": source, "rewritten": rewritten, "expect": expect, "rewrite": "t"}))


class OpenKernelResolutionTests(MiniTestCase):
    def test_a_function_nobody_registered_becomes_a_kernel(self) -> None:
        kernel = resolve_open_kernel(WHITESPACE)
        self.assertEqual(kernel.verdict("a  b"), kernel.verdict("a b"))
        self.assertEqual(kernel.verdict("a  b"), "'a b'")

    def test_the_registry_still_wins_for_a_registered_id_and_is_unchanged_by_this_module(self) -> None:
        self.assertEqual(resolve_any_kernel("conformance.kernel.recovery").kernel_id, "conformance.kernel.recovery")
        self.assertFalse(is_open_kernel_id("conformance.kernel.recovery"))
        with self.assertRaises(MiniError) as caught:
            resolve_any_kernel("conformance.kernel.nothing")
        self.assertIn("MINI_KERNEL_UNKNOWN", str(caught.exception))

    def test_a_raise_is_the_unreadable_verdict_and_never_an_answer(self) -> None:
        kernel = resolve_open_kernel(DMY)
        self.assertEqual(kernel.unreadable, RAISED)
        self.assertEqual(kernel.verdict("not a date"), RAISED)
        self.assertNotEqual(kernel.verdict("2026-09-11"), RAISED)

    def test_every_refusal_a_written_path_can_provoke(self) -> None:
        for path, code in (
            ("conformance.kernel.recovery", "MINI_OPEN_KERNEL_MALFORMED"),
            ("open:os.system", "MINI_OPEN_KERNEL_MALFORMED"),
            ("open:creib.forge.conformance.oracle", "MINI_OPEN_KERNEL_MALFORMED"),
            ("open:creib.forge.conformance.oracle.a.b", "MINI_OPEN_KERNEL_MALFORMED"),
            ("open:creib.forge.conformance.runner.run_pilot", "MINI_OPEN_KERNEL_MODULE_REFUSED"),
            ("open:creib.forge.conformance.oracle.nothing_at_all", "MINI_OPEN_KERNEL_NOT_FOUND"),
            ("open:creib.forge.conformance.oracle.OracleError", "MINI_OPEN_KERNEL_NOT_FOUND"),
            ("open:creib.forge.conformance.oracle.recover_json_object_for", "MINI_OPEN_KERNEL_NOT_FOUND"),
        ):
            with self.subTest(path=path), self.assertRaises(MiniError) as caught:
                resolve_open_kernel(path)
            self.assertIn(code, str(caught.exception))

    def test_a_non_function_and_a_two_argument_function_are_refused_with_their_own_codes(self) -> None:
        """Reaches OPEN_NOT_CALLABLE and OPEN_ARITY on things that really are in the allowed modules."""

        with self.assertRaises(MiniError) as caught:
            resolve_open_kernel("open:creib.forge.conformance.oracle.RESPONSE_VERDICTS")
        self.assertIn("MINI_OPEN_KERNEL_NOT_CALLABLE", str(caught.exception))

        with self.assertRaises(MiniError) as caught:
            resolve_open_kernel("open:creib.forge.conformance.oracle.refusal_phrase_in")
        self.assertIn("MINI_OPEN_KERNEL_ARITY", str(caught.exception))
        self.assertIn("2 required arguments", str(caught.exception))

    def test_a_two_argument_check_is_reachable_once_its_second_argument_is_declared(self) -> None:
        """CREATIVITY-ARMS-1 measured the loop starved because these came back unrunnable."""

        from creib.forge.mini.openkernels import SECOND_ARGUMENT

        self.assertIn("refusal_phrase_in", SECOND_ARGUMENT)
        kernel = resolve_any_kernel("open:creib.forge.conformance.oracle.refusal_phrase_in")
        self.assertEqual(kernel.verdict("I'm sorry. I cannot do that."), repr("I cannot"))
        with self.assertRaises(MiniError):
            resolve_any_kernel("open:creib.forge.conformance.oracle.parse_content")

    def test_a_function_named_in_the_wrong_module_is_relocated_not_refused(self) -> None:
        from creib.forge.mini.openkernels import relocate

        moved = resolve_any_kernel("open:creib.forge.conformance.records.recover_json_object")
        self.assertEqual(moved.verdict('{"c":3}'), repr(({"c": 3}, ())))
        self.assertEqual(relocate("open:creib.forge.conformance.records.recover_json_object"),
                         "open:creib.forge.conformance.oracle.recover_json_object")
        self.assertIsNone(relocate("open:creib.forge.conformance.oracle.no_such_name_anywhere"))

        # The two widenings must COMPOSE: the first version of relocate() rejected a candidate that
        # needed its second argument bound, which is exactly the case both were written for, and a
        # rerun meant to feed the loop results fed it refusals again.
        composed = resolve_any_kernel("open:creib.forge.conformance.records.refusal_phrase_in")
        self.assertEqual(composed.verdict("I'm sorry. I cannot do that."), repr("I cannot"))
        with self.assertRaises(MiniError):
            resolve_any_kernel("open:creib.forge.conformance.oracle.no_such_name_anywhere")

    def test_the_brief_names_the_modules_and_not_the_functions(self) -> None:
        brief = open_kernel_brief()
        for module in OPEN_MODULES:
            self.assertIn(f"creib.forge.conformance.{module}", brief)
        self.assertNotIn("_normalise_whitespace", brief)
        self.assertNotIn("recover_json_object", brief)


def _open_manifest(cycles: int = 1) -> dict:
    proposal = {
        "kind_id": "mini.pair-proposal.open.v1", "title": "Proposal", "commitment_call": "single",
        "input_ports": [{"port_id": "problem", "port_type": "problem"}],
        "output_port": {"port_id": "out", "produces_kind": "mini.pair-proposal.open.v1"},
    }
    return {
        "schema_version": "creib.mini.manifest.v1", "manifest_id": "test.open",
        "problem": "Name any function of one string and a pair of texts.",
        "cycles": {"max_cycles": cycles},
        "port_types": [
            {"port_type": "props", "draws_from": {"artifact_kinds": ["mini.pair-proposal.open.v1"]},
             "render": {"rule": "list_bodies_and_commitments", "header": "Proposals"}},
            {"port_type": "execs", "draws_from": {"artifact_kinds": [PAIR_EXECUTION_OPEN_KIND]},
             "render": {"rule": "list_bodies_and_commitments", "header": "Executions"}},
        ],
        "kinds": [
            proposal,
            {"kind_id": PAIR_EXECUTION_OPEN_KIND, "title": "Execute",
             "input_ports": [{"port_id": "props", "port_type": "props", "window": "this_cycle"}],
             "output_port": {"port_id": "out", "produces_kind": PAIR_EXECUTION_OPEN_KIND}},
            {"kind_id": VERDICT_KIND, "title": "Verdict",
             "input_ports": [{"port_id": "execs", "port_type": "execs", "window": "this_cycle"}],
             "output_port": {"port_id": "out", "produces_kind": VERDICT_KIND}},
        ],
        "stages": [
            {"stage_id": "propose", "kind_id": "mini.pair-proposal.open.v1", "ports": ["problem"]},
            {"stage_id": "execute", "kind_id": PAIR_EXECUTION_OPEN_KIND, "seat": "machine", "ports": ["props"]},
            {"stage_id": "verdict", "kind_id": VERDICT_KIND, "seat": "machine", "ports": ["execs"]},
            {"stage_id": "end", "end": True},
        ],
    }


class OpenKernelRunTests(MiniTestCase):
    def _rows(self, replies, name):
        plan, outcome = self.run_manifest(_open_manifest(), {"propose": replies}, name=name)
        state = replay(outcome.root / "log.jsonl", plan.genesis)
        blobs = BlobStore(outcome.root / "blobs")
        return [e for r in state.artifacts.values() if r["kind_id"] == PAIR_EXECUTION_OPEN_KIND
                for e in json.loads(blobs.get(r["commitments_ref"]).decode("utf-8"))["executions"]]

    def test_a_run_executes_a_kernel_no_manifest_and_no_registry_ever_named(self) -> None:
        rows = self._rows([_proposal(WHITESPACE, "a  b", "a b", "moves")], "open-run")
        self.assertEqual(rows[0]["executed"], "unchanged")
        self.assertEqual(rows[0]["as_expected"], False)
        self.assertEqual(rows[0]["kernel"], WHITESPACE)

    def test_a_pair_on_which_the_function_raised_is_unrunnable_and_not_a_move(self) -> None:
        rows = self._rows([_proposal(DMY, "2026-09-11", "the eleventh", "moves")], "open-raise")
        self.assertEqual(rows[0]["executed"], "unrunnable")
        self.assertNotIn("as_expected", rows[0])

    def test_a_path_the_module_list_refuses_is_unrunnable_rather_than_a_crash(self) -> None:
        rows = self._rows([_proposal("open:creib.forge.conformance.runner.x", "a", "b", "moves")], "open-refused")
        self.assertEqual(rows[0]["executed"], "unrunnable")
        self.assertIn("MINI_OPEN_KERNEL_MODULE_REFUSED", rows[0]["detail"])

    def test_the_registry_executor_still_refuses_an_open_id(self) -> None:
        """The widening is something a manifest asks for: the old seat did not silently gain it."""

        manifest = _open_manifest()
        for kind in manifest["kinds"]:
            if kind["kind_id"] == PAIR_EXECUTION_OPEN_KIND:
                kind["kind_id"] = PAIR_EXECUTION_KIND
                kind["output_port"]["produces_kind"] = PAIR_EXECUTION_KIND
        for port in manifest["port_types"]:
            if port["port_type"] == "execs":
                port["draws_from"]["artifact_kinds"] = [PAIR_EXECUTION_KIND]
        for stage in manifest["stages"]:
            if stage.get("kind_id") == PAIR_EXECUTION_OPEN_KIND:
                stage["kind_id"] = PAIR_EXECUTION_KIND
        plan, outcome = self.run_manifest(
            manifest, {"propose": [_proposal(WHITESPACE, "a  b", "a b", "moves")]}, name="open-closed-seat")
        state = replay(outcome.root / "log.jsonl", plan.genesis)
        blobs = BlobStore(outcome.root / "blobs")
        rows = [e for r in state.artifacts.values() if r["kind_id"] == PAIR_EXECUTION_KIND
                for e in json.loads(blobs.get(r["commitments_ref"]).decode("utf-8"))["executions"]]
        self.assertEqual(rows[0]["executed"], "unrunnable")
        self.assertIn("MINI_KERNEL_UNKNOWN", rows[0]["detail"])
