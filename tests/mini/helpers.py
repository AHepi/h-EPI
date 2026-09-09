"""Fixtures for the mini suite: a base manifest, and the scaffolding to compile
and run one in a temporary directory. Nothing here calls a model."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
from typing import Any, Mapping
import unittest

from creib.canonical import canonical_bytes
from creib.forge.mini.executor import ScriptedResponder
from creib.forge.mini.manifest import RunPlan, compile_manifest
from creib.forge.mini.runner import RunOutcome, run_mini

CONJECTURE_KIND: dict[str, Any] = {
    "kind_id": "k.conjecture",
    "title": "Conjecture",
    "input_ports": [
        {"port_id": "problem", "port_type": "problem"},
        {"port_id": "evidence", "port_type": "evidence_legend", "params": {"tiers": ["evidence"]}},
        {"port_id": "prior", "port_type": "artifacts_of_kind", "params": {"kind_id": "k.conjecture"}},
    ],
    "output_port": {"port_id": "out", "produces_kind": "k.conjecture"},
}

CRITICISM_KIND: dict[str, Any] = {
    "kind_id": "k.criticism",
    "title": "Criticism",
    "input_ports": [
        {"port_id": "problem", "port_type": "problem"},
        {"port_id": "conjectures", "port_type": "artifacts_of_kind", "params": {"kind_id": "k.conjecture"}},
    ],
    "output_port": {"port_id": "out", "produces_kind": "k.criticism"},
}

SOURCE_TEXT = "The first paragraph says one thing.\n\nThe second paragraph says another thing entirely."


def base_manifest() -> dict[str, Any]:
    """A two-kind, two-stage manifest with one source. Everything else default."""

    return {
        "schema_version": "creib.mini.manifest.v1",
        "manifest_id": "test.base",
        "problem": "What is going on here, and how might that reading be wrong?",
        "kinds": [copy.deepcopy(CONJECTURE_KIND), copy.deepcopy(CRITICISM_KIND)],
        "stages": [
            {"stage_id": "c1", "kind_id": "k.conjecture", "ports": ["problem", "evidence"]},
            {"stage_id": "x1", "kind_id": "k.criticism", "ports": ["problem", "conjectures"]},
            {"stage_id": "end", "end": True},
        ],
        "sources": [{"source_id": "s1", "text": SOURCE_TEXT}],
    }


def submission(body: str, commitments: str, **extra: Any) -> str:
    """One reply, as a seat would return it."""

    return json.dumps({"body": body, "commitments": commitments, **extra}, ensure_ascii=False)


DEFAULT_SCRIPT: dict[str, list[str]] = {
    "c1": [submission("The two paragraphs disagree.", "Read both before deciding.")],
    "x1": [submission("Disagreement is not the only reading.", "Say what would settle it.")],
}


class MiniTestCase(unittest.TestCase):
    """A temporary directory per test, and the three things every test needs."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def write_manifest(self, manifest: Mapping[str, Any], name: str = "manifest.json") -> Path:
        path = self.tmp / name
        path.write_bytes(canonical_bytes(dict(manifest)) + b"\n")
        return path

    def write_json(self, name: str, payload: Mapping[str, Any]) -> Path:
        path = self.tmp / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(canonical_bytes(dict(payload)) + b"\n")
        return path

    def compile(self, manifest: Mapping[str, Any], policy_dir: Path | None = None) -> RunPlan:
        return compile_manifest(self.write_manifest(manifest), policy_dir)

    def run_plan(self, plan: RunPlan, script: Mapping[str, list[str]], name: str = "run") -> RunOutcome:
        return run_mini(plan, self.tmp / name, ScriptedResponder(script))

    def run_manifest(
        self,
        manifest: Mapping[str, Any],
        script: Mapping[str, list[str]] | None = None,
        name: str = "run",
        policy_dir: Path | None = None,
    ) -> tuple[RunPlan, RunOutcome]:
        plan = self.compile(manifest, policy_dir)
        return plan, self.run_plan(plan, dict(script or DEFAULT_SCRIPT), name)

    def events(self, outcome: RunOutcome) -> list[dict[str, Any]]:
        lines = (outcome.root / "log.jsonl").read_text(encoding="utf-8").splitlines()
        return [json.loads(line) for line in lines if line.strip()]

    def events_of(self, outcome: RunOutcome, event_type: str) -> list[dict[str, Any]]:
        return [event for event in self.events(outcome) if event["type"] == event_type]

    def _every_brief(self, plan, outcome) -> str:
        """Every port of every producing stage, rendered — for absence assertions."""

        from creib.forge.mini.log import BlobStore, replay
        from creib.forge.mini.runner import render_brief

        state = replay(outcome.root / "log.jsonl", plan.genesis)
        blobs = BlobStore(outcome.root / "blobs")
        rendered = []
        for stage in plan.stages:
            if stage.end:
                continue
            brief, _ = render_brief(plan, state, blobs, stage)
            rendered.append(brief)
        return "\n".join(rendered)

    def assertRefuses(self, code: str, callable_object, *args: Any, **kwargs: Any) -> None:
        from creib.forge.mini.common import MiniError

        with self.assertRaises(MiniError) as caught:
            callable_object(*args, **kwargs)
        self.assertEqual(caught.exception.code, code, str(caught.exception))
