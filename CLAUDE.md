# h-EPI — agent entry point

Read this file first, then `docs/handoff/STATUS.md` (current state, overwritten each tranche), then the live handover it names under `docs/handoff/`. Older handovers are history; `docs/audits/` are advisory. This file holds only durable rules. Do not copy per-tranche state into it.

`AGENTS.md` is a symlink to this file so Codex reads the same rules. The two skills under `.codex/skills/` are symlinked into `.claude/skills/`; invoke `h-epi-safe-publish` to publish and `h-epi-human-handoff` to explain results to a person.

## What this repository is

An implementation workspace for the CR-1.0 creativity semantic model: a fail-closed executable interpretation bridge (`src/creib`, `bridge/`, `formal/`) and the Semantic Model Forge, a criticism-first harness for translating a source into a model without confirming it (`src/creib/forge`, `forge/`). "Harness" has two senses here: the forge's translation harness (project code) and the developer/agent harness (this file, skills, CI, hooks). Keep them distinct.

## Authority boundary

- The sole semantic and formal authority is the operator-held CR-1.0 PDF, SHA-256 `08ff81e848fea976b558345402d85723173be8f40f1041fb00d6267f1e026b8b`, 1,734,769 bytes, 286 pages. It is never committed (`.gitignore` excludes `*.pdf`). Never stage, print, or transmit it.
- Repository prose, tests, Lean declarations, schemas, corpus annotations, research reports, and external model audits are subordinate evidence. They may not add source premises or settle an ambiguous reading.
- No source-level theorem has been proved or refuted. Never write text that implies otherwise.

## Never promote

- Passing tests, a compiling proof, schema validity, agreement between models, paper counts, "not found", or green CI never change `mapping_fidelity_status` (`UNREVIEWED`), `bridge_conformance_status` (`BLOCKED`), a claim kind, or any epistemic status. Survival of criticism leaves a proposal unrefuted for its declared scope; it does not confirm it.
- Dispositions, triage, reviews, and decisions are human, append-only, content-addressed records. Never hand-edit a published record, never fabricate a triage or disposition, never turn conversational agreement into a machine record.
- Never retarget an immutable declaration ID (`EIB-*`). Add a new ID.
- A failed test criticizes the tested conjunction (candidate, auxiliaries, test, scope). Keep every live locus visible; do not pick one cause.

## Status vocabulary

Three independent surfaces: `operational_status` (PASS only when PDF and Lean replay together, else PARTIAL), `mapping_fidelity_status`, `bridge_conformance_status`. Forge routes: `AWAITING_HUMAN_TRIAGE`, `AWAITING_HUMAN_ACTION_SELECTION`, `AWAITING_HUMAN_REASSESSMENT`, `INTERNAL_*_WORK`, `AUTHORITY_REVIEW`, `EXTERNAL_RESEARCH_REQUIRED`. `UNRESOLVED` is an epistemic state, not a failure. `tools/run_translation_harness.py` exit 1 means "correctly refused to call the pipeline ready", exit 2 means invalid input, exit 0 is reserved.

## Environment

- Python 3.12 exactly. In a Claude Code web session the SessionStart hook (`.claude/hooks/session-start.sh`) creates `.venv` and exports `PATH`/`PYTHONPATH`. Elsewhere run `python3.12 tools/check.py bootstrap`, then use `.venv/bin/python`.
- Every Python invocation needs `PYTHONPATH=src`; the package is not installed.
- Dependencies are the hash-locked set in `requirements-container.txt`; the two `requirements-*-ci.txt` files are its unhashed CI subsets.
- Lean 4.33.1, `pdftotext` 24.02.0, `pdfinfo` 26.05.0, and Docker are optional toolchains. If one is absent, report that tier as `UNAVAILABLE`. Never simulate or infer its result.

## Verification tiers

All checks go through one entry point so CI, skills, README, and this file agree:

| Target | What | Wall time (4-core container) |
|---|---|---|
| `python tools/check.py lint` | compileall, shipped-code assert guard, whitespace, Lean source scan | seconds |
| `python tools/check.py test-fast` | every test module except the two slow scenario suites | ~2 min |
| `python tools/check.py test-slow` | `test_semantic_forge_inquiry`, `test_translation_review` | ~11 min |
| `python tools/check.py test` | complete suite, one pass | ~13 min |
| `python tools/check.py verify` | bootstrap validator + bridge verifier (no PDF, no Lean) | seconds |
| `python tools/check.py verify-lean` | bridge verifier with pinned Lean replay | needs `lake` |
| `python tools/check.py smoke` | container smoke script (run inside the replay image) | needs Docker |

Run `lint` and `test-fast` before every commit and the full `test` before opening a pull request. The suite runs once; the former second pass under `python -O` is replaced by the assert guard in `lint`. Do not add `assert` to `src/` or `tools/`.

## Pinned implementation contract

The committed calibration record (`forge/runs/SMF-CALIBRATION-*.json`) hashes the files in `_IMPLEMENTATION_CODE_PATHS` in `src/creib/forge/calibration.py` and every `forge/schema/*.schema.json`. Changing any of them, or adding a schema file to `forge/schema/`, makes the calibration replay tests fail until the maintainer regenerates the record with the authority PDF. Before editing those files, say so and expect that step; do not edit the record or the tests to compensate. New schemas for new subsystems belong in their own directory (for example `forge/conformance/schema/`).

## Publishing

- Work on a branch (`claude/*`, `codex/*`, or a human-chosen name). Never commit on or push to `main`; publication is a pull request and merging is a human action.
- Push only to the branch's own upstream: `git push -u origin HEAD`. Never `--force`, never `HEAD:main`, never rebase, reset, amend, or rewrite published history. `.claude/settings.json` denies these commands.
- Stage explicit paths only. Run `git diff --cached --check`. Never stage PDFs, archives, credentials, or `.venv`.
- Publication requires explicit user authorization. Use the `h-epi-safe-publish` skill.
- Record the branch, commit SHA, and pull request URL in the handover.

## Handover discipline

Durable rules live here. Current state (status tuple, active artifact paths and digests, CI state, test count, next ordered task) lives in `docs/handoff/STATUS.md`, overwritten each tranche and kept under 3 KB. The narrative of what a tranche built and why goes in a new `docs/handoff/CR-EIB-0.N_Orchestrator_Handover.md`; earlier handovers are never edited except to add the superseded banner. Do not restate these rules in a handover; link this file.

## Research gate

External discovery (AlphaXiv, Consensus, or any other surface) is allowed only after a human-selected external action binds an exact issue, warrant, and attack-target subset. MCP servers for those surfaces may be attached to a session; their presence authorizes nothing. Record every source report in the research ledger format with content digests. Agreement, ranking, recency, and "not found" have no confirmatory effect.

## Style

- LF line endings, no trailing whitespace, strict JSON (no duplicate keys, no floats, no NaN), canonical bytes for records, content-addressed IDs.
- Type-annotated Python with `from __future__ import annotations`, frozen dataclasses, `RecordError` for input failures, no `print` in library code.
- Plain-language handoffs: lead with the practical outcome, translate every status label the first time it matters, keep every live criticism visible, never equate green with confirmation.
