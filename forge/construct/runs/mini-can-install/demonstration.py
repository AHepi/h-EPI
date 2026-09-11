"""Can a mini configuration install into an operative state? Built to settle that, not argue it."""
import json, sys, tempfile
sys.path.insert(0, "/home/user/h-EPI/src")
from pathlib import Path
from creib.forge.construct.candidates import VIEW_TWO, render, verify
from creib.forge.construct.controller import contract_check, starting_controller
from creib.forge.mini.machines import MachineSeat, register_machine_seat
from creib.forge.mini.manifest import compile_manifest
from creib.forge.mini.executor import ScriptedResponder
from creib.forge.mini.runner import run_mini

# The operative state a mini seat will change: one controller, outside the record.
CONTROLLER = starting_controller(False)
PROPOSE, INSTALL = "construct.propose.v1", "construct.install.v1"

def install_seat(context):
    """A machine seat that verifies this cycle's proposal and INSTALLS it. Arbitrary Python."""
    installed, note = None, "nothing proposed this cycle"
    for record in context.artifacts_of_kind(PROPOSE, context.cycle):
        tree = json.loads(context.commitments(record)).get("tree")
        verdict = verify(tree, VIEW_TWO, 4)
        if verdict.accepted:
            CONTROLLER.install(tree, VIEW_TWO, "verified inside a mini run")
            installed, note = render(tree), "installed"
        else:
            note = f"rejected at check {verdict.checked}"
    check = contract_check(CONTROLLER, 4)
    return json.dumps({"body": f"{note}; the controller now commits {check['violations']} violations of {check['cases']}.",
                       "commitments": json.dumps({"installed": installed, "violations": check["violations"]}, sort_keys=True)})

try:
    register_machine_seat(MachineSeat(INSTALL, "Verifies a proposal and installs it.", install_seat))
except Exception:
    pass

manifest = {
  "schema_version": "creib.mini.manifest.v1",
  "manifest_id": "construct.inside.mini",
  "problem": "Propose a decision program for the controller.",
  "cycles": {"max_cycles": 3},
  "port_types": [{"port_type": "proposals", "draws_from": {"artifact_kinds": [PROPOSE]},
                  "render": {"rule": "list_bodies_and_commitments", "header": "Proposals"}},
                 {"port_type": "installs", "draws_from": {"artifact_kinds": [INSTALL]},
                  "render": {"rule": "list_bodies", "header": "What the controller does now"}}],
  "kinds": [
    {"kind_id": PROPOSE, "title": "Proposal", "commitment_call": "single",
     "input_ports": [{"port_id": "problem", "port_type": "problem", "window": "all"},
                     {"port_id": "installs", "port_type": "installs", "window": "all"}],
     "output_port": {"port_id": "out", "produces_kind": PROPOSE},
     "instruction": "Propose a decision program as a JSON syntax tree in commitments."},
    {"kind_id": "mini.verdict.v1", "title": "Verdict", "commitment_call": "single",
     "input_ports": [{"port_id": "installs", "port_type": "installs", "window": "this_cycle"}],
     "output_port": {"port_id": "out", "produces_kind": "mini.verdict.v1"}},
    {"kind_id": INSTALL, "title": "Install",
     "input_ports": [{"port_id": "proposals", "port_type": "proposals", "window": "this_cycle"}],
     "output_port": {"port_id": "out", "produces_kind": INSTALL}}],
  "stages": [{"stage_id": "propose", "kind_id": PROPOSE, "ports": ["problem", "installs"]},
             {"stage_id": "install", "kind_id": INSTALL, "seat": "machine", "ports": ["proposals"]},
             {"stage_id": "verdict", "kind_id": "mini.verdict.v1", "ports": ["installs"]},
             {"stage_id": "end", "end": True}],
}

bad = json.dumps({"tree": {"op": "field", "name": "active"}})
good = json.dumps({"tree": {"op": "and", "left": {"op": "field", "name": "active"},
                            "right": {"op": "equal", "left": "current", "right": "incoming"}}})
script = {"verdict": [json.dumps({"body": "noted", "commitments": "{}"})] * 3, "propose": [json.dumps({"body": "first try", "commitments": bad}),
                      json.dumps({"body": "with the register", "commitments": good}),
                      json.dumps({"body": "same again", "commitments": good})]}

print("before the run:", contract_check(CONTROLLER, 4)["violations"], "violations")
with tempfile.TemporaryDirectory() as d:
    p = Path(d) / "m.json"; p.write_text(json.dumps(manifest))
    plan = compile_manifest(p)
    print("policy changes =", plan.policy.defaults.changes)
    outcome = run_mini(plan, Path(d) / "run", ScriptedResponder(script))
    print("stop:", outcome.stop_reason, "| cycles:", outcome.cycles_completed)
print("after the run: ", contract_check(CONTROLLER, 4)["violations"], "violations")
print("installs recorded on the controller:", [i["program"] for i in CONTROLLER.installs])
