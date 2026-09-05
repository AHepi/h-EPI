# CR-EIB-0.6 orchestrator handover

## Outcome

This tranche repairs the developer/agent harness and adds the first pilot that points the forge's criticism-first method at a second problem. It changes no semantic status, no authority binding, no declaration, no calibration record, and no pinned implementation file. Durable rules now live in `/CLAUDE.md`; current state lives in `docs/handoff/STATUS.md`; this file is narrative only.

The governing limit is unchanged:

> Survival of criticism leaves a proposal unrefuted for the declared scope. It does not confirm, support, or make the proposal probable.

## Why the harness needed repair

At the base commit `e48d5d8`, CI on `main` was red for the second consecutive push. The `evidence-records` job had a five-minute budget and ran the complete suite twice (normal and `python -O`) while a single pass took about ten minutes; the container smoke job had a thirty-minute budget and was still on its first test pass at twenty-seven minutes. The commit that made the suite slow added 4,434 lines to one test module; nothing in the harness could notice a five-fold test-time regression, and because every commit in the repository's history is a direct push to `main`, nothing could block it.

A fresh Claude Code web session could not run the suite at all: the container's default Python is 3.11, `jsonschema` is absent, and system `pip` is blocked. There was no `CLAUDE.md`, no `.claude/` directory, and the two skills existed only under `.codex/skills/`. The publish skill refused to operate on any branch except `main` and pushed straight to it.

Measured on a 4-core container with Python 3.12, one pass of the 499-test suite took 955 s. Two modules accounted for 89 percent: `test_semantic_forge_inquiry` (667 s) and `test_translation_review` (184 s). A profile of one 119-second test showed 78 s inside `load_local_schema_catalog`, called 35 times, each call re-running the metaschema check on all 28 schema files (980 `check_schema` calls). Three modules already memoise that loader; `calibration.py` and `translation_review.py` did not. `src/` and `tools/` contain no `assert` statement, so the second `-O` pass exercised nothing the first did not.

## What this tranche changed

| Area | Change | Boundary |
|---|---|---|
| Entry point | `/CLAUDE.md` (durable rules), `AGENTS.md` symlink, `docs/handoff/STATUS.md` (current state), `docs/handoff/README.md` (index) | Rules are instructions to agents, not authority over the source |
| Skills | `.claude/skills/*` symlink to `.codex/skills/*`; `h-epi-safe-publish` rewritten for a working-branch and pull-request model; GitHub Data API fallback removed | Publication still requires explicit human authorization; merging is a human action |
| Session bootstrap | `.claude/hooks/session-start.sh` creates `.venv` with Python 3.12 and the hash-locked `requirements-container.txt` set; `.claude/settings.json` registers it and denies force-push, history rewriting, `HEAD:main`, and bulk staging | Web sessions only; local users run `python3.12 tools/check.py bootstrap` |
| Single check entry point | `tools/check.py` with `lint`, `test-fast`, `test-slow`, `test`, `verify`, `verify-lean`, `smoke`, `bootstrap`; CI, the smoke script, the skill, README, and CLAUDE.md all call it | Green establishes structural and deterministic behaviour only |
| Assert guard | `lint` fails if any `assert` exists in `src/` or `tools/`; this replaces the second `-O` test pass in CI and in the container smoke | A checked invariant replaces an assumed one |
| CI | `bridge-pilot.yml`: `lint` job; two-shard `evidence-records` (30-minute budget); `lean-replay`; `container-replay-smoke` (60-minute budget); `push` limited to `main`; `pull_request` and `workflow_dispatch`; concurrency cancellation; verifier reports retained as artifacts for 90 days. `actions/upload-artifact` pinned to `ea165f8d…7fa02` (v4.6.2, verified against the tag) | Budgets are set from measured time, not hope |
| Schema catalog cache | New unpinned module `src/creib/forge/schema_catalog_cache.py`: content-keyed memoisation (directory plus SHA-256 of every schema file's bytes) wrapping the pinned loader; `translation_review.py` routed through it | A cache hit requires byte-identical schemas; any change repeats the full check |
| Task-conformance pilot | See the SMF-0.5 section below | Criticism-bearing observations only; no model is confirmed |

Measured after the change, same container: `test-fast` 86 s for 405 tests; `test_translation_review` 11 s (from 184 s); `test_semantic_forge_inquiry` unchanged at about 667 s.

## Why the inquiry suite is still slow

The calibration record `forge/runs/SMF-CALIBRATION-CR-1-0-001.4219efce.json` pins the SHA-256 of 17 implementation files (`_IMPLEMENTATION_CODE_PATHS` in `calibration.py`) and every `forge/schema/*.schema.json`. `schema_validation.py`, `calibration.py`, and `inquiry.py` are on that list. The first attempt at this fix edited `schema_validation.py`; four replay tests immediately failed with "execution contract field `implementation_file_sha256` differs", exactly as designed. The edit was reverted, all 45 pinned digests were re-verified, and the cache was moved to a new unpinned module used only by unpinned callers.

The consequence is a harness fact worth stating plainly: any performance or correctness change to those 17 files, or any new schema file in `forge/schema/`, requires the maintainer to regenerate the calibration record with the authority PDF. That is the correct fail-closed behaviour and also the reason the slow path cannot be fixed from a session without the PDF. When the maintainer next regenerates the record, the two remaining uncached call sites (`calibration.py:358` and `:1228`) can be routed through `cached_local_schema_catalog` and the inquiry suite should drop from about 11 minutes to about 1.

## SMF-0.5 task-conformance pilot

`forge/conformance/` points the forge's criticism-first method at a second problem: a language model filling an incident-report form from a short case document. The form schema and eleven numbered instructions are the content-bound source; each of ten fields is an obligation grounded in a verbatim instruction sentence; one declared ambiguity (day-first versus month-first numeric dates) carries two rival rules; the nine adversarial test families are generated from a fourteen-case corpus (five boundary cases, three minimal pairs, three renderings each) and executed through a replaceable `ollama-chat` executor. Every observation is scored per field, routed to a plural set of live loci, and published as a content-addressed no-clobber record. The run stops at `AWAITING_HUMAN_TRIAGE`. Nothing about the incident form lives in `src/`; the pilot's schemas live in `forge/conformance/schema/` so the calibration record's contract over `forge/schema/` is untouched.

Nine Ollama-hosted models were run against the full 117-variant plan (about 1,000 model calls): gpt-oss:20b, nemotron-3-nano:30b, gemma4:31b, gpt-oss:120b, qwen3.5:397b, glm-5.3-flash, glm-5.3, deepseek-v4-flash:0731, mistral-large-3:675b. Kimi K3 was excluded on cost. All 1,053 observation records and 9 run records are committed under `forge/conformance/runs/incident-form/`. Every run is `REFUTED_CASES_PRESENT`; none is `UNREFUTED_FOR_DECLARED_SCOPE`. The full account, with generated tables and a failure-mode-by-model matrix, is `docs/forge/SMF-0.5_Conformance_Pilot.md`.

What the first live run taught, in order:

1. The first six baseline calls exposed the harness's own oracle: `site` values were title-cased while the documents use sentence case and instruction 8 says "as named in the document". The routing had kept TEST live alongside CANDIDATE on every one of those observations. Every `site` oracle became `any_of` over the verbatim and capitalised forms before the multi-model run.
2. The `site` criticism then appeared for all nine models on the same cases (dropped or added qualifiers), which makes it a criticism of instruction 8's granularity, recorded with TEST and SCOPE live, not a model defect.
3. Six models fabricated a phone number where none was stated and the form admits no "not provided" value; SCOPE and CANDIDATE stay live together.
4. Four models ignored an explicit month-first disambiguation rule; none ignored an inverted formatting instruction.
5. Both GLM models emitted reasoning as message content with the JSON at the end, even with `think` false; the recovery rule in force during the runs did not see the trailing object. The widened rule re-scores all 87 such responses offline to scored objects, most with nine or ten fields matching. The committed records keep their original scoring.
6. A review of the pilot module (three reviewers; 24 findings; verified against the code and by two Ollama models) found defects that could abort a run or leave a published record unloadable. All are fixed with regression tests (`tests/test_conformance_pilot.py`, 40 tests); every published record reloads. The one "blocker" finding was real in a shape the first direct check had not covered (a round-trip variant with no usable baseline is published without a response).

The pilot does not establish that any model fills forms correctly, that the oracles are right, or that `format` structured output is unenforced everywhere. It establishes that the method runs end to end on a second problem, that its plural routing distinguished specification gaps from model behaviour on real data, and that a new problem is a new directory under `forge/conformance/pilots/`, not a code change.

## Repository and published-state boundary

Repository: `https://github.com/AHepi/h-EPI`

Working branch: `claude/harness-improvement-assessment-qpsz3b`, cut from `main` at `e48d5d8dd736432672895e1fc208b217508ab80c`. Publication is a pull request to `main`; merging is a human action. `main` had no branch protection at the time of writing; the recommended ruleset (require the four workflow jobs, block force pushes and deletions, allow admin bypass) is a repository setting only the owner can apply.

## Verification

Local verification on 2026-09-05 in a 4-core Claude Code container with Python 3.12.3 and the hash-locked dependency set:

| Check | Observed result |
|---|---|
| `python tools/check.py lint` | compileall clean; no `assert` in `src/` or `tools/`; whitespace clean; no `axiom`/`opaque`/`sorry`/`admit` in formal sources |
| Complete Python suite, one pass (`python tools/check.py test`) | 543/543 passed in 647.2 s at commit `616fca9`; the five tests added in `5417dc7` were then run with their module: `tests.test_conformance_pilot` 45/45 passed in 2.4 s. Current total: 548 |
| `test_translation_review` alone | 19/19 in 10.8 s (184 s before the catalog cache) |
| `test_semantic_forge_inquiry` alone | 79/79 in about 667 s (pinned path; unchanged) |
| Bootstrap validator | package integrity and quarantine discipline `PASS`; CR-1.0 semantic bootstrap gate remains `FAIL` |
| Bridge verifier without PDF | operational `PARTIAL`; records, schemas, choices, formal package `PASS`; mapping `UNREVIEWED`; bridge `BLOCKED` |
| Pinned implementation contract | all 45 digests in the calibration record's `implementation_file_sha256` match the tree; `forge/schema/` still holds exactly 28 files |
| Conformance records | all 1,053 observation records and 9 run records reload under the current loader and validate against the four conformance schemas |
| SessionStart hook | fresh `.venv` on Python 3.12, hash-locked install, `PATH`/`PYTHONPATH` exported, smoke module green; idempotent on re-run |
| Lean, Lake, Docker, pdftotext, pdfinfo | `UNAVAILABLE` in this container; no compiler, container, or extractor result was simulated |

CI on the working branch at commit `ef19979` (workflow_dispatch, before the pilot landed):

| Job | Conclusion | Wall time | Notes |
|---|---|---|---|
| `lint` | success | 4 s | compileall, assert guard, whitespace, Lean scan |
| `evidence-records (test-fast)` | success | 2 min 6 s | 405 tests + bootstrap validator + verifier; report retained as artifact |
| `evidence-records (test-slow)` | success | 14 min 19 s | `test_semantic_forge_inquiry` + `test_translation_review`; budget 30 min |
| `lean-replay` | success | 29 s | zero-axiom audit; Lean report retained as artifact |
| `container-replay-smoke` | success | 18 min 13 s | image build 3 min 24 s; networkless single-pass replay 14 min 42 s; budget 60 min |
| whole run | success | 18 min 17 s | run 33993548045 on commit `ef19979`; `bootstrap-integrity` run 33993549234 succeeded in 12 s |

The pilot commits (`e6e1cd0`, `616fca9`, `6148cfe`, `7ac90cb`, `5417dc7`) have not yet been run through CI because `push` triggers only on `main`; the pull request run will cover them. The new tests are offline and run in the `test-fast` shard.

These checks establish deterministic and structural behaviour. They establish no semantic status, and the conformance results confirm no model.

## Next implementation order

1. **Apply the `main` ruleset** so the pull-request model is enforced by GitHub rather than by prose.
2. **Regenerate the calibration record** with the authority PDF, then route `calibration.py:358` and `:1228` through `cached_local_schema_catalog` and re-measure.
3. **Execute the conformance pilot's second problem.** Drop a second `pilot.json` (a different form, or a non-form task) into `forge/conformance/pilots/` to test that configurability holds without code changes.
4. **Decide the licence statement** (`LICENSE.md` stating what is permitted now) and whether external audit packet construction becomes a script.
5. Then resume the SMF-0.4 order from handover 0.5: derive the snapshot delta, execute the nine attacks, close the iteration lineage, bind human authentication, bind a real model executor, run HRC-1 blind qualification, run a fresh Popper translation.

This file supersedes `CR-EIB-0.5_Orchestrator_Handover.md` as the live continuation point.
