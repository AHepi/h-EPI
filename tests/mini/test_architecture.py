"""The architecture check: an attention policy cannot reach the record.

The request says attention must be determined by the machine, not the user
(R20). What makes that structural rather than a promise is that a policy is
handed a view of the signals it declared and the stages still to run, and
nothing else — and that registration refuses a function whose signature could
take anything else. This file is the check that goes red if either weakens.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
from typing import Any

from creib.forge.mini import attention as attention_module
from creib.forge.mini.attention import (
    AttentionPolicy,
    PendingStage,
    SignalView,
    choose_next,
    register_attention_policy,
    registered_attention_policies,
)

from .helpers import MiniTestCase

FORBIDDEN_IMPORTS = ("log", "evidence", "runner", "manifest", "signals", "executor", "kinds", "routing", "policy")


class _RecordingView(SignalView):
    """A view that remembers what a policy asked for."""


class AttentionIsolationTests(MiniTestCase):
    def test_the_attention_module_imports_nothing_that_touches_the_record(self) -> None:
        source = Path(inspect.getsourcefile(attention_module)).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                imported.append(node.module)
            elif isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
        reached = [name for name in imported for part in FORBIDDEN_IMPORTS if name.split(".")[-1] == part]
        self.assertEqual(reached, [], f"attention reached {reached}; it may see signals only")

    def test_every_registered_policy_takes_only_signals_and_stages(self) -> None:
        for policy in registered_attention_policies():
            with self.subTest(policy=policy.policy_id):
                self.assertEqual(tuple(inspect.signature(policy.choose).parameters), ("signals", "stages"))

    def test_a_policy_that_would_take_the_record_is_refused_at_registration(self) -> None:
        def reads_the_record(signals: Any, stages: Any, state: Any) -> None:
            return None

        self.assertRefuses(
            "MINI_ATTENTION_SIGNATURE",
            register_attention_policy,
            AttentionPolicy("mini.attention.test-peeker", (), "wants the record", reads_the_record),
        )

    def test_a_policy_reaching_past_its_declared_signals_is_refused_when_it_runs(self) -> None:
        policy = register_attention_policy(
            AttentionPolicy(
                "mini.attention.test-overreacher",
                ("mini.signal.cycle-count",),
                "asks for a signal it never declared",
                lambda signals, stages: signals["mini.signal.artifacts-by-kind"] and None,
            )
        )
        self.assertRefuses(
            "MINI_ATTENTION_UNDECLARED_SIGNAL",
            choose_next,
            policy,
            {"mini.signal.cycle-count": 1, "mini.signal.artifacts-by-kind": {}},
            (PendingStage("s1", "k"),),
        )

    def test_every_shipped_policy_reads_only_what_it_declared(self) -> None:
        for policy in registered_attention_policies():
            if policy.policy_id.startswith("mini.attention.test-"):
                continue
            with self.subTest(policy=policy.policy_id):
                view = SignalView({name: {} for name in policy.reads_signals}, policy.reads_signals, policy.policy_id)
                policy.choose(view, (PendingStage("s1", "k.any"),))
                self.assertLessEqual(set(view.read), set(policy.reads_signals))

    def test_the_view_is_the_only_thing_a_policy_is_handed(self) -> None:
        seen: list[tuple[object, object]] = []
        policy = register_attention_policy(
            AttentionPolicy(
                "mini.attention.test-observer",
                (),
                "records what it was handed",
                lambda signals, stages: seen.append((signals, stages)) or None,
            )
        )
        choose_next(policy, {"mini.signal.cycle-count": 4}, (PendingStage("s1", "k.any"),))
        handed_signals, handed_stages = seen[0]
        self.assertIsInstance(handed_signals, SignalView)
        self.assertEqual(list(handed_signals), [])
        self.assertEqual(handed_stages, (PendingStage("s1", "k.any"),))
        self.assertFalse(hasattr(handed_signals, "artifacts"))
