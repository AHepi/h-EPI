# Current state

Overwritten each tranche. Rules live in `/CLAUDE.md`; narrative lives in the live handover below.

| Item | Value |
|---|---|
| Live handover | `docs/handoff/CR-EIB-0.6_Orchestrator_Handover.md` |
| Base commit of this tranche | `e48d5d8dd736432672895e1fc208b217508ab80c` (`main`) |
| Working branch | `claude/harness-improvement-assessment-qpsz3b` |
| Publication unit | pull request to `main`; merging is a human action |

## Status tuple

| Surface | State | Boundary |
|---|---|---|
| Authority identity | `PINNED` (SHA-256 `08ff81e8…026b8b`, 1,734,769 B, 286 pp) | digest, bytes, pages, registered replay only |
| Bootstrap | package integrity `PASS`; semantic bootstrap gate `FAIL` | declaration mappings and typed bodies incomplete |
| Bridge without PDF | operational `PARTIAL`; records, schemas, choices, formal package `PASS` | PDF and Lean replay not run in this environment |
| Mapping fidelity | `UNREVIEWED` | no source mapping accepted as lossless |
| Bridge conformance | `BLOCKED` | operational checks cannot promote it |
| Source theorem status | neither proved nor refuted | relative Lean results do not adjudicate CR-1.0 |
| Adaptive inquiry | `AWAITING_HUMAN_TRIAGE`; zero questions | a menu of attacks authorizes no research |
| Translation review / integrated hardening | never `READY` in v1; `BLOCKED` | reviewer authentication and iteration lineage absent |
| HRC-1 qualification | fixture and comparator present; execution absent | no blindness or mutation result |
| Task-conformance pilot (SMF-0.5) | nine models run; every run `REFUTED_CASES_PRESENT`; 1,053 observation records + 9 run records committed | criticism-bearing observations only; no model is confirmed, ranked, or scored |

## Active artifacts (calibration and plan unchanged this tranche)

| Artifact | Path | SHA-256 |
|---|---|---|
| Calibration record | `forge/runs/SMF-CALIBRATION-CR-1-0-001.4219efce.json` | `b83059255390e20da34cf416747bc13d5533a0794a7be7bdc0ba7760bc326fe2` |
| No-triage plan | `forge/plans/SMF-AIP-1210e0fa.no-triage.json` | `78f0c19d7fa609015a4ec6c610588d58460e77bcbba68778c1fd3f1b3bd38b8d` |
| Research ledger | `forge/research/SMF-RESEARCH-2026-09-03.json` | see file |
| Conformance pilot runs | `forge/conformance/runs/incident-form/` (9 run records, 1,053 observations) | corpus digest `f21d38e7…f8e38`; per-record `content_digest` |

The calibration record pins 17 implementation files and every `forge/schema/*.schema.json`; all 45 digests match at this commit. Any change to them requires the maintainer to regenerate the record with the authority PDF.

## Harness state

| Item | Value |
|---|---|
| CI on `main` at base commit | red: `bridge-pilot` runs #11 and #12 cancelled (5-min test budget vs ~10-min suite; 30-min container budget vs ~27-min first pass) |
| CI after this tranche | green on the working branch (run 33993548045, 18 min 17 s): `lint` 4 s; `evidence-records` test-fast 2 min 6 s, test-slow 14 min 19 s (budget 30); `lean-replay` 29 s; `container-replay-smoke` 18 min 13 s (budget 60); `-O` pass replaced by assert guard; verifier reports retained as artifacts |
| Test count | 548 (499 at base + 4 schema-cache + 45 conformance pilot) |
| Measured wall time (4-core container, Python 3.12) | `test-fast` ~90 s (454 tests); `test_translation_review` 11 s (was 184 s); `test_semantic_forge_inquiry` ~667 s (pinned path, unchanged) |
| Entry point | `python tools/check.py {lint,test-fast,test-slow,test,verify,verify-lean,smoke}` |
| Agent bootstrap | `.claude/hooks/session-start.sh` (web sessions) or `python3.12 tools/check.py bootstrap` |

## Next ordered task

Named in the live handover's "Next implementation order".
