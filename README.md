# h-EPI

`h-EPI` is the implementation workspace for the CR-1.0 creativity semantic model and its proposed executable interpretation bridge.

[![bootstrap integrity](https://github.com/AHepi/h-EPI/actions/workflows/bootstrap-integrity.yml/badge.svg?branch=main)](https://github.com/AHepi/h-EPI/actions/workflows/bootstrap-integrity.yml) [![bridge pilot](https://github.com/AHepi/h-EPI/actions/workflows/bridge-pilot.yml/badge.svg?branch=main)](https://github.com/AHepi/h-EPI/actions/workflows/bridge-pilot.yml)

Working in this repository, as a person or an agent: read [`CLAUDE.md`](CLAUDE.md) (durable rules; `AGENTS.md` is the same file), then [`docs/handoff/STATUS.md`](docs/handoff/STATUS.md) (current state), then the live handover it names. Python 3.12 is required; create the environment with `python3.12 tools/check.py bootstrap` and run every check through `python tools/check.py <target>` (`lint`, `test-fast`, `test`, `verify`, `verify-lean`, `smoke`). Claude Code web sessions do this automatically through `.claude/hooks/session-start.sh`.

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
python3.12 tools/check.py bootstrap   # once: .venv with the hash-locked dependencies
.venv/bin/python tools/check.py verify   # bootstrap validator + bridge verifier
```

Run the bridge record checks and adversarial tests with:

```sh
.venv/bin/python tools/check.py lint        # compileall, assert guard, whitespace, Lean scan
.venv/bin/python tools/check.py test-fast   # ~1.5 min: every module except the two slow scenario suites
.venv/bin/python tools/check.py test        # ~13 min: the complete suite, one pass
```

The suite runs once. The former second pass under `python -O` is replaced by the assert guard in `lint`, which fails if any `assert` statement exists in `src/` or `tools/`. The same targets run in CI (`.github/workflows/bridge-pilot.yml`), in the container smoke replay, and in the publish skill.

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

`SMF-0.1` is a separate, non-authoritative criticism harness for developing the semantic model class before extracting more mathematics. It does not change the CR-EIB bridge, the pinned authority, or any mapping status. Its research gate starts from a live external unknown and requires rival answers, falsifiers, an expected discriminator, a bounded source scope, and a stop condition. It records AlphaXiv as the current replaceable default if an exact external action later authorizes discovery. Research output can propose criticisms; it cannot confirm a model.

`SMF-0.4` adds a generic source-to-model translation harness around that criticism kernel. It content-binds source documents and ordered source spans, freezes a translation charter, preserves source obligations and rival readings, separates project imports, builds a formalism-independent signature and model, and requires an element-specific two-way trace with directed dependency checks. Separate runtimes then handle append-only interpretation review, nine families of change-driven adversarial tests, plural failure routing, non-scalar hardening, and a freeze-ordered HRC-1 declared-exposure comparison. The contract defines thirteen conceptual gates. The controller exposes thirteen status slices, but they are not a one-to-one copy of those gates: `translation_integrity` is an aggregate, while project-import checks are part of `neutral_model`. Their order is presentation only. A structurally valid snapshot still has mapping fidelity `UNREVIEWED` and a null semantic verdict.

Inspect a candidate translation without silently skipping absent stages:

```sh
PYTHONPATH=src python tools/run_translation_harness.py \
  --records-dir /path/to/translation-records \
  --snapshot /path/to/translation-snapshot.json
```

The current tranche supplies contracts and validators, not an automatic prose translator or an oracle for correct interpretation. It does not commit a runnable end-to-end generic translation inventory, snapshot, v3 inquiry plan, review lineage, delta, hardening packet, or HRC candidate report; its generic behavior is exercised by test fixtures. The integrated pipeline replays operator-supplied UTF-8 byte ranges and `pdftotext`-version-bound PDF word snapshots. PDF replay also uses `pdfinfo`, whose version is not yet pinned, and character-and-whitespace-exact PDF transcription and unregistered extraction profiles remain open. Reviewer authentication is not implemented, so an otherwise valid scoped review cannot become `READY` and integrated hardening remains blocked; standalone hardening validation can still report its limited outcomes. Executable adapters for the nine semantic test families, one append-only end-to-end iteration lineage, a completed blind HRC mutation run, and a fresh independent Popper hostile trial also remain open.

Run the first authority-bound calibration with a lawfully held copy of the exact PDF:

```sh
PYTHONPATH=src python tools/run_semantic_forge.py first-run \
  --authority /path/to/Creativity_Semantic_Model_CR-1.0.pdf \
  --output forge/runs/my-new-calibration.json
```

The calibration deliberately tests a weak typed-role projection, not CR-1.0 itself. It admits a causally grounded case and a labels-only contrast case, reports `NO_HARDENING` for the fixture's disconnected `RoleGrounded` addition under its finite contract, constructs one falsifier-first warrant using the current AlphaXiv default from a supplied external issue, reports formalization `BLOCKED`, and stops at `AWAITING_HUMAN`.

The additive adaptive-inquiry protocol binds a failed observation to its exact run, candidate, issue, warrant, evaluator, fixture, and research ledger. Its active v2 triage can retain several live `CANDIDATE`, `AUXILIARY`, `TEST`, and `SCOPE` criticisms at once, including one mechanism that crosses loci. `UNRESOLVED` describes the overall epistemic state; a live locus assessment is a criticism to investigate, not a finding that the named component caused the failure. One nullable `next_action` schedules work on one or more compatible dependency-frontier assessments without closing the others.

Active triage is an append-only, content-addressed lineage under `forge/triage/`. A loose JSON file is only a draft: it becomes operational only when it is published without overwrite and its unique terminal ID is explicitly selected for planning. A successor must retain every prior assessment and disposition byte-for-byte. Separate human dispositions can retain, defeat, or mark one exact assessment stale for the exact current bindings. Same-binding treatment of a live assessment must follow the previously authorized frontier action and cite the exact bound calibration record; staleness must embed the exact binding delta. That makes scheduling dependencies traversable without turning treatment of an objection into confirmation. If the bound run, model, issue, warrant, observation, or ledger snapshot changes, the successor must say so explicitly and clear `next_action` for fresh human scheduling; old-binding dispositions have no current operational effect. With no published triage the planner stops at `AWAITING_HUMAN_TRIAGE`; with live assessments but no selected action it stops at `AWAITING_HUMAN_ACTION_SELECTION`; if the present set has no effective-live member it stops at `AWAITING_HUMAN_REASSESSMENT`, still `UNRESOLVED`.

Every plan exposes the exact rival-falsifier attack targets available from the bound issue and warrant. That list is a menu, not research authorization. Research questions are generated only for the target IDs explicitly selected by an external `next_action`; each question carries the selected assessments, action, exact attack target, scope, and stop rule. AlphaXiv is the designated replaceable discovery surface after that gate, never a primary-source substitute or oracle. This repository has no AlphaXiv or other retrieval adapter, and neither an externally obtained search result nor failure to find one can promote the model. The exclusive v1 records remain immutable validation and replay evidence; they cannot be newly published, extended, or used as active v2 routing inputs.

The named binding changes above are illustrative: a change to any case-bound input requires the same explicit successor and action reset.

```sh
PYTHONPATH=src python tools/run_semantic_inquiry.py plan \
  --run-record forge/runs/SMF-CALIBRATION-CR-1-0-001.4219efce.json \
  --research-ledger forge/research/SMF-RESEARCH-2026-09-03.json \
  --triage-dir forge/triage
```

See the [generic translation contract](docs/forge/SMF-0.4_Translation_Contract.md), [HRC-1 qualification fixture](docs/forge/SMF-0.4_Qualification_Fixture.md), [SMF architecture](docs/forge/SMF-0.1_Architecture.md), [underspecification atlas](docs/forge/SMF-0.1_Underspecification_Atlas.md), [research basis](docs/forge/SMF-0.1_Research_Basis.md), [first run](docs/forge/SMF-0.1_First_Run.md), [mathematical target](docs/forge/SMF-0.2_Mathematical_Target.md), [adaptive inquiry protocol](docs/forge/SMF-0.3_Adaptive_Inquiry_Protocol.md), [current orchestrator handover](docs/handoff/CR-EIB-0.5_Orchestrator_Handover.md), [current run record](forge/runs/SMF-CALIBRATION-CR-1-0-001.4219efce.json), [current no-triage plan](forge/plans/SMF-AIP-1210e0fa.no-triage.json), [research ledger](forge/research/SMF-RESEARCH-2026-09-03.json), [seed corpus](forge/corpus/cr-1.0-seed.json), and [forge guide](forge/README.md).

## Authority and redistribution

The authority PDF itself is intentionally not committed. Its expected digest is recorded in the baseline and bridge evidence. Local verification requires a lawfully held copy supplied by the operator.

No license has yet been granted for this repository. Publication alone does not grant permission to copy, modify, or redistribute its contents.
