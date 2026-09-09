"""R18, R19, R20, R21: signals, and attention as a plug that is off by default."""

from __future__ import annotations

import copy

from creib.forge.mini.attention import (
    ATTENTION_MOST_UNANSWERED,
    ATTENTION_OFF,
    AttentionPolicy,
    PendingStage,
    SignalView,
    choose_next,
    register_attention_policy,
    registered_attention_policies,
    resolve_attention_policy,
)
from creib.forge.mini.log import ATTENTION_CHOSE, MiniState, replay
from creib.forge.mini.signals import (
    SIGNAL_ARTIFACTS_BY_KIND,
    SIGNAL_CITATIONS_VERIFIED,
    SIGNAL_CYCLE_COUNT,
    SIGNAL_TOKENS_BY_KIND,
    SIGNAL_UNANSWERED_BY_KIND,
    SignalDecl,
    compute_signals,
    register_signal,
    registered_signals,
)

from .helpers import MiniTestCase, base_manifest, submission

NOTE_KIND = {
    "kind_id": "example.note.v1",
    "title": "Note",
    "input_ports": [{"port_id": "problem", "port_type": "problem"}],
    "output_port": {"port_id": "out", "produces_kind": "example.note.v1"},
}


class OffByDefaultTests(MiniTestCase):
    def test_no_attention_section_means_off(self) -> None:
        """R21: a run that declares nothing runs the declared order."""

        plan, outcome = self.run_manifest(base_manifest())
        self.assertEqual(plan.attention.policy_id, ATTENTION_OFF)
        self.assertEqual(self.events_of(outcome, ATTENTION_CHOSE), [])

    def test_off_runs_the_declared_order_and_writes_no_attention_event(self) -> None:
        """R21: declaring off is the same run as declaring nothing."""

        manifest = base_manifest()
        declared = base_manifest()
        declared["attention"] = {"policy": ATTENTION_OFF}
        _, silent = self.run_manifest(manifest, name="silent")
        _, explicit = self.run_manifest(declared, name="explicit")
        self.assertEqual(silent.stages_entered, ("c1", "x1", "verdict"))
        self.assertEqual(explicit.stages_entered, silent.stages_entered)
        self.assertEqual(
            [stage["stage_id"] for stage in self.events_of(explicit, "STAGE_ENTERED")],
            [stage["stage_id"] for stage in self.events_of(silent, "STAGE_ENTERED")],
        )
        self.assertEqual(self.events_of(explicit, ATTENTION_CHOSE), [])

    def test_an_unknown_attention_policy_is_refused(self) -> None:
        manifest = base_manifest()
        manifest["attention"] = {"policy": "mini.attention.telepathy"}
        self.assertRefuses("MINI_ATTENTION_POLICY_UNKNOWN", self.compile, manifest)


class DemonstrationPolicyTests(MiniTestCase):
    def _manifest(self) -> dict:
        manifest = base_manifest()
        manifest["kinds"].append(copy.deepcopy(NOTE_KIND))
        manifest["stages"] = [
            {"stage_id": "c1", "kind_id": "k.conjecture", "ports": ["problem"]},
            {"stage_id": "x1", "kind_id": "k.criticism", "ports": ["problem", "conjectures"]},
            {"stage_id": "n1", "kind_id": "example.note.v1", "ports": ["problem"]},
            {"stage_id": "c2", "kind_id": "k.conjecture", "ports": ["problem", "prior"]},
            {"stage_id": "end", "end": True},
        ]
        manifest["attention"] = {"policy": ATTENTION_MOST_UNANSWERED}
        return manifest

    def test_the_demonstration_policy_reorders_the_declared_order(self) -> None:
        """R20: with attention on, the machine picks, not the declared order."""

        plan = self.compile(self._manifest())
        conjecture_id = None
        # The criticism names the conjecture, so a conjecturer stage becomes
        # the one with an unanswered criticism against its kind.
        script = {
            "c1": [submission("A conjecture.", "c")],
            "x1": [submission("An objection.", "c", about=["PLACEHOLDER"])],
            "n1": [submission("A note.", "c")],
            "c2": [submission("A second conjecture.", "c")],
        }
        first = self.run_plan(plan, dict(script), name="first")
        conjecture_id = self.events_of(first, "ARTIFACT_SUBMITTED")[0]["artifact_id"]
        script["x1"] = [submission("An objection.", "c", about=[conjecture_id])]
        second = self.run_plan(self.compile(self._manifest()), dict(script), name="second")
        self.assertEqual(second.stages_entered, ("c1", "x1", "c2", "n1", "verdict"))
        chosen = [event["payload"]["chosen"] for event in self.events_of(second, ATTENTION_CHOSE)]
        self.assertIn("c2", chosen)

    def test_the_policy_sees_a_kind_it_was_never_written_for(self) -> None:
        """R18: a kind invented in a manifest is visible through the signals."""

        state = MiniState()
        state.artifacts = {
            "a": {"artifact_id": "a", "kind_id": "invented.kind.v9", "about": [], "answers": [], "citations": []},
            "b": {"artifact_id": "b", "kind_id": "another.kind.v9", "about": ["a"], "answers": [], "citations": []},
        }
        state.artifact_order = ["a", "b"]
        counts = compute_signals(state, (SIGNAL_UNANSWERED_BY_KIND,))[SIGNAL_UNANSWERED_BY_KIND]
        self.assertEqual(counts, {"invented.kind.v9": 1})
        chosen = choose_next(
            resolve_attention_policy(ATTENTION_MOST_UNANSWERED),
            {SIGNAL_UNANSWERED_BY_KIND: counts},
            (PendingStage("s1", "invented.kind.v9"), PendingStage("s2", "another.kind.v9")),
        )
        self.assertEqual(chosen, "s1")

    def test_an_answered_criticism_stops_counting(self) -> None:
        state = MiniState()
        state.artifacts = {
            "a": {"artifact_id": "a", "kind_id": "k.conjecture", "about": [], "answers": [], "citations": []},
            "b": {"artifact_id": "b", "kind_id": "k.criticism", "about": ["a"], "answers": [], "citations": []},
            "c": {"artifact_id": "c", "kind_id": "k.conjecture", "about": [], "answers": ["b"], "citations": []},
        }
        state.artifact_order = ["a", "b", "c"]
        self.assertEqual(compute_signals(state, (SIGNAL_UNANSWERED_BY_KIND,))[SIGNAL_UNANSWERED_BY_KIND], {})

    def test_a_policy_choosing_a_stage_that_is_not_pending_is_refused(self) -> None:
        policy = register_attention_policy(
            AttentionPolicy("mini.attention.test-wanderer", (), "picks a stage nobody offered", lambda signals, stages: "elsewhere")
        )
        self.assertRefuses("MINI_ATTENTION_STAGE_UNKNOWN", choose_next, policy, {}, (PendingStage("s1", "k"),))


class SignalRegistryTests(MiniTestCase):
    def test_the_five_shipped_signals_are_registered(self) -> None:
        declared = {item.signal_id for item in registered_signals()}
        for signal_id in (
            SIGNAL_ARTIFACTS_BY_KIND,
            SIGNAL_CITATIONS_VERIFIED,
            SIGNAL_UNANSWERED_BY_KIND,
            SIGNAL_TOKENS_BY_KIND,
            SIGNAL_CYCLE_COUNT,
        ):
            self.assertIn(signal_id, declared)

    def test_the_shipped_signals_read_a_real_record(self) -> None:
        plan, outcome = self.run_manifest(base_manifest())
        state = replay(outcome.root / "log.jsonl", plan.genesis)
        values = compute_signals(
            state,
            (SIGNAL_ARTIFACTS_BY_KIND, SIGNAL_CITATIONS_VERIFIED, SIGNAL_TOKENS_BY_KIND, SIGNAL_CYCLE_COUNT),
        )
        self.assertEqual(values[SIGNAL_ARTIFACTS_BY_KIND], {"k.conjecture": 1, "k.criticism": 1, "mini.verdict.v1": 1})
        self.assertEqual(set(values[SIGNAL_CITATIONS_VERIFIED].values()), {0})
        self.assertTrue(values[SIGNAL_TOKENS_BY_KIND]["k.conjecture"] > 0)
        self.assertEqual(values[SIGNAL_CYCLE_COUNT], 1)

    def test_a_new_signal_is_a_registration_and_nothing_else(self) -> None:
        """R19: adding a signal edits no consumer."""

        register_signal(
            SignalDecl("mini.signal.test-artifacts-total", "artifacts", "How many artifacts in all."),
            lambda state: len(state.artifact_order),
        )
        plan, outcome = self.run_manifest(base_manifest())
        state = replay(outcome.root / "log.jsonl", plan.genesis)
        self.assertEqual(compute_signals(state, ("mini.signal.test-artifacts-total",)), {"mini.signal.test-artifacts-total": 3})

    def test_registering_a_signal_twice_is_refused(self) -> None:
        self.assertRefuses(
            "MINI_SIGNAL_DUPLICATE",
            register_signal,
            SignalDecl(SIGNAL_CYCLE_COUNT, "cycles", "again"),
            lambda state: 0,
        )

    def test_a_signal_id_that_is_not_an_identifier_is_refused(self) -> None:
        self.assertRefuses(
            "MINI_SIGNAL_UNKNOWN", register_signal, SignalDecl("9 not an id", "u", "d"), lambda state: 0
        )

    def test_asking_for_an_unregistered_signal_is_refused(self) -> None:
        self.assertRefuses("MINI_SIGNAL_UNKNOWN", compute_signals, MiniState(), ("mini.signal.absent",))

    def test_the_cycle_count_counts_real_cycles(self) -> None:
        """R23: driven through the runner over three cycles, not assembled by hand."""

        manifest = base_manifest()
        manifest["cycles"] = {"max_cycles": 3}
        script = {
            "c1": [submission(f"conjecture {index}", "c") for index in range(3)],
            "x1": [submission(f"criticism {index}", "c") for index in range(3)],
        }
        plan, outcome = self.run_manifest(manifest, script)
        state = replay(outcome.root / "log.jsonl", plan.genesis)
        self.assertEqual(compute_signals(state, (SIGNAL_CYCLE_COUNT,))[SIGNAL_CYCLE_COUNT], 3)
        self.assertEqual(outcome.cycles_completed, 3)
        self.assertEqual(outcome.stages_entered, ("c1", "x1", "verdict") * 3)


class SignalViewTests(MiniTestCase):
    def test_a_view_answers_only_what_the_policy_declared(self) -> None:
        view = SignalView({"a": 1, "b": 2}, ("a",), "mini.attention.test")
        self.assertEqual(view["a"], 1)
        self.assertEqual(list(view), ["a"])
        self.assertEqual(len(view), 1)

    def test_asking_for_an_undeclared_signal_is_refused(self) -> None:
        view = SignalView({"a": 1}, ("a",), "mini.attention.test")
        self.assertRefuses("MINI_ATTENTION_UNDECLARED_SIGNAL", lambda: view["b"])

    def test_a_declared_signal_that_was_not_computed_reads_as_nothing(self) -> None:
        view = SignalView({}, ("a",), "mini.attention.test")
        self.assertEqual(view["a"], {})


class RegistrationTests(MiniTestCase):
    def test_registering_a_policy_twice_is_refused(self) -> None:
        self.assertRefuses(
            "MINI_ATTENTION_POLICY_DUPLICATE",
            register_attention_policy,
            AttentionPolicy(ATTENTION_OFF, (), "again", lambda signals, stages: None),
        )

    def test_resolving_a_policy_nobody_registered_is_refused(self) -> None:
        self.assertRefuses("MINI_ATTENTION_POLICY_UNKNOWN", resolve_attention_policy, "mini.attention.absent")

    def test_the_two_shipped_policies_are_registered(self) -> None:
        ids = {policy.policy_id for policy in registered_attention_policies()}
        self.assertLessEqual({ATTENTION_OFF, ATTENTION_MOST_UNANSWERED}, ids)
