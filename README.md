# h-EPI

`h-EPI` is the implementation workspace for the CR-1.0 creativity semantic model and its proposed executable interpretation bridge.

## Current status

| Layer | Status | Meaning |
|---|---|---|
| CR-1.0 authority identity | **PINNED** | The designated PDF identity is pinned by SHA-256; an operator-supplied copy is checked only during `--pdf` replay and remains the sole semantic/formal authority. |
| Cold-start inventory integrity | **PASS** | The quarantined bootstrap package is internally consistent and reproducible. |
| CR-1.0 executable-calculus bootstrap | **FAIL** | Required declaration-level source mappings and typed bodies are incomplete. |
| CR-EIB-0.1 conformance | **BLOCKED** | The bridge is a non-authoritative proposal and cannot pass until its evidence obligations are discharged. |
| DF-10/TH-3 Lean replay | **PASS (relative)** | The candidate definition, unfolding, and explicit countermodel compile with no axioms; this is not source-level theorem adjudication. |

No theorem has yet been adjudicated as proved or refuted against the complete CR-1.0 authority. This repository does not contain a creativity classifier and does not automate judgments that something or someone is creative.

Lean is implemented for the narrow DF-10/TH-3 pilot; SMT remains an implementation target. Any checked pilot result is explicitly scoped to its encoded model and bridge declaration; it is not automatically a result about the whole CR-1.0 model.

The immutable cold-start package is under `baseline/cr-1.0/bootstrap-v0.1/`. Run its integrity and quarantine validator with:

```sh
python -m pip install -r requirements-ci.txt
python baseline/cr-1.0/bootstrap-v0.1/tools/validate_bootstrap.py
```

Run the bridge record checks and adversarial tests with:

```sh
python -m pip install -r requirements-bridge-ci.txt
PYTHONPATH=src python -m unittest discover -s tests -v
python tools/verify_bridge.py
```

The verifier reports `operational_status: PASS` only when both the authority PDF and the pinned Lean package are replayed successfully in the same invocation. Omitting either replay reports record integrity `PASS` and operational status `PARTIAL`. The legacy `status` field remains as an operational-only compatibility alias and is labeled by `status_scope`. `mapping_fidelity_status` and `bridge_conformance_status` are independent: a clean operational replay does not promote an unreviewed source mapping or unblock bridge conformance.

A full operator replay succeeded for the reviewed packet in its mixed native-tool environment, using an operator-supplied copy of the pinned authority PDF. CI cannot replay that external PDF and therefore cannot independently produce the same operational `PASS`. Native extractor or compiler version mismatches fail closed instead of being treated as equivalent replays.

The normative cold-start image definition now pins the reviewed `linux/amd64` inputs, and each replay runs the built image by its immutable content ID. See [CR-EIB-0.2 container replay](docs/reproduction/CR-EIB-0.2_Container_Replay.md) for the networkless, read-only full replay and its explicit status boundaries. The DevContainer is only a convenience wrapper over the same image definition.

Audit provenance is published as the [packet coverage and omission manifest](docs/audits/CR-EIB-0.2_packet-manifest.txt) and the [exact 14-declaration release axiom transcript](docs/audits/CR-EIB-0.2_Release_Axiom_Transcript.txt). The [external audit adjudication](docs/audits/CR-EIB-0.2_External_Audit_Adjudication.md) retains the pinned 254-declaration namespace result from the reviewed packet.

Inside an already verified environment, replay the source anchors against a lawfully held PDF copy with:

```sh
python tools/verify_bridge.py --pdf /path/to/Creativity_Semantic_Model_CR-1.0.pdf --lean
```

To replay only the formal pilot (overall status remains `PARTIAL` without the PDF):

```sh
python tools/verify_bridge.py --lean
```

## Semantic Model Forge (experimental)

`SMF-0.1` is a separate, non-authoritative criticism harness for developing the semantic model class before extracting more mathematics. It does not change the CR-EIB bridge, the pinned authority, or any mapping status. Its research gate starts from a live external unknown, requires rival answers, falsifiers, an expected discriminator, a bounded source scope, and a stop condition, and uses AlphaXiv as the default replaceable discovery channel. Research output can propose criticisms; it cannot confirm a model.

Run the first authority-bound calibration with a lawfully held copy of the exact PDF:

```sh
PYTHONPATH=src python tools/run_semantic_forge.py first-run \
  --authority /path/to/Creativity_Semantic_Model_CR-1.0.pdf \
  --output forge/runs/my-new-calibration.json
```

The calibration deliberately tests a weak typed-role projection, not CR-1.0 itself. It admits a causally grounded case and a labels-only contrast case, reports `NO_HARDENING` for the fixture's disconnected `RoleGrounded` addition under its finite contract, constructs one falsifier-first warrant using the current AlphaXiv default from a supplied external issue, reports formalization `BLOCKED`, and stops at `AWAITING_HUMAN`.

The additive adaptive-inquiry protocol binds a failed observation to its exact run, candidate, issue, warrant, evaluator, fixture, and research ledger. The ledger binding includes its creation and as-of dates; triage cannot predate ledger creation, and every generated question binds the triage date. Without a separately supplied human failure triage it stops at `AWAITING_HUMAN_TRIAGE`, proposes no research question, and leaves the semantic verdict null. After triage it can construct content-addressed critical questions and route them, but neither a search result nor failure to find one can promote the model. Current-case transitions must address an exact question regenerated from the current inventory; blocked and integration-only routes are non-actionable.

```sh
PYTHONPATH=src python tools/run_semantic_inquiry.py plan \
  --run-record forge/runs/SMF-CALIBRATION-CR-1-0-001.4219efce.json \
  --research-ledger forge/research/SMF-RESEARCH-2026-09-03.json
```

See the [SMF architecture](docs/forge/SMF-0.1_Architecture.md), [underspecification atlas](docs/forge/SMF-0.1_Underspecification_Atlas.md), [research basis](docs/forge/SMF-0.1_Research_Basis.md), [first run](docs/forge/SMF-0.1_First_Run.md), [mathematical target](docs/forge/SMF-0.2_Mathematical_Target.md), [adaptive inquiry protocol](docs/forge/SMF-0.3_Adaptive_Inquiry_Protocol.md), [current run record](forge/runs/SMF-CALIBRATION-CR-1-0-001.4219efce.json), [current no-triage plan](forge/plans/SMF-AIP-2d589a64.no-triage.json), [research ledger](forge/research/SMF-RESEARCH-2026-09-03.json), and [seed corpus](forge/README.md).

## Authority and redistribution

The authority PDF itself is intentionally not committed. Its expected digest is recorded in the baseline and bridge evidence. Local verification requires a lawfully held copy supplied by the operator.

No license has yet been granted for this repository. Publication alone does not grant permission to copy, modify, or redistribute its contents.
