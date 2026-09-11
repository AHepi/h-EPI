"""Every machine seat a shipped manifest names must be registered on the command line's import path.

A seat is registered by a module-level ``register_machine_seat`` call, so it exists only if
something imported the module it lives in. Importing it inside a test proves nothing about the
tool: ``tools/run_mini.py`` has its own imports, and a seat the tests reach directly but the tool
does not is a manifest that compiles under ``unittest`` and dies under ``run_mini live`` -- which is
how OPEN-SWEEP-1's first thirty-six runs were spent (mini register M25).

So this test imports the command line itself and asks it, rather than importing the seats.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _import_the_command_line():
    """Load ``tools/run_mini.py`` as the command line loads it, for its registering imports."""

    spec = importlib.util.spec_from_file_location("run_mini_under_test", ROOT / "tools" / "run_mini.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ShippedManifestSeatTests(unittest.TestCase):
    def test_every_machine_seat_named_by_a_shipped_manifest_resolves_after_the_tool_imports(self) -> None:
        _import_the_command_line()
        from creib.forge.mini.machines import registered_machine_seats

        registered = {seat.kind_id for seat in registered_machine_seats()}
        declared: dict[str, list[str]] = {}
        for path in sorted((ROOT / "forge" / "mini" / "manifests").rglob("manifest.json")):
            body = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(body, dict):
                continue
            for stage in body.get("stages", []):
                if isinstance(stage, dict) and stage.get("seat") == "machine" and stage.get("kind_id"):
                    declared.setdefault(str(stage["kind_id"]), []).append(
                        str(path.relative_to(ROOT)))
        self.assertTrue(declared, "there must be shipped manifests with machine stages to check")
        missing = {kind: sorted(set(paths))[:3] for kind, paths in declared.items() if kind not in registered}
        self.assertEqual(missing, {}, f"seats no import of the command line registers: {missing}")
