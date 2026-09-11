"""Every machine seat a shipped manifest names must be registered on the command line's import path.

A seat is registered by a module-level ``register_machine_seat`` call, so it exists only if
something imported the module it lives in. Importing it inside a test proves nothing about the
tool: ``tools/run_mini.py`` has its own imports, and a seat the tests reach directly but the tool
does not is a manifest that compiles under ``unittest`` and dies under ``run_mini live`` -- which is
how OPEN-SWEEP-1's first thirty-six runs were spent (mini register M25).

So this test asks the command line, in a FRESH interpreter. Registration is a process-global
side effect, so any other test importing a seat module makes an in-process check pass whether or not
the command line imports it: the first version of this file failed in isolation and passed inside
the suite, defeated by exactly the mechanism it exists to catch (M25, second occurrence).
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


_PROBE = """
import importlib.util, json, sys
from pathlib import Path
root = Path(sys.argv[1])
sys.path.insert(0, str(root / "src"))
spec = importlib.util.spec_from_file_location("run_mini_under_test", root / "tools" / "run_mini.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
from creib.forge.mini.machines import registered_machine_seats
print(json.dumps(sorted(seat.kind_id for seat in registered_machine_seats())))
"""


def _seats_the_command_line_registers() -> set[str]:
    """What ``tools/run_mini.py`` registers, asked of an interpreter that imported nothing else."""

    finished = subprocess.run([sys.executable, "-c", _PROBE, str(ROOT)],
                              capture_output=True, text=True, check=True)
    return set(json.loads(finished.stdout.strip().splitlines()[-1]))


class ShippedManifestSeatTests(unittest.TestCase):
    def test_every_machine_seat_named_by_a_shipped_manifest_resolves_after_the_tool_imports(self) -> None:
        registered = _seats_the_command_line_registers()
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
