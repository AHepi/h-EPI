# CR-EIB-0.5 orchestrator handover

> Historical handover. For the current continuation point, use `STATUS.md` and `CR-EIB-0.6_Orchestrator_Handover.md`.

## Outcome

This increment adds the first generic, fail-closed semantic translation
harness around the Semantic Model Forge. It does not claim that the existing
Popper translation is correct. Its job is to make a translation proposal
inspectable before more mathematics is extracted: content-bind and replay
operator-supplied source bytes, state the job, preserve rival readings and their
compatible combinations, expose imported premises, build a neutral model,
trace it both ways, generate attacks from a declared change, route failures
without guessing one cause, and refuse to call an unwitnessed repair an
improvement. A digest record does not archive the external source artifact.

The governing limit remains:

> Survival of criticism leaves a proposal unrefuted for the declared scope. It
> does not confirm, support, or make the proposal probable.

The harness is not foolproof and does not describe itself as such. It closes
known silent-loss paths and reports missing capabilities as `UNRESOLVED`. In
particular, the integrated pipeline cannot return `READY` in v1 because its
end-to-end iteration lineage has not yet been implemented. Independently,
reviewer authentication is unavailable: the review slice cannot become
`READY`, so the integrated hardening slice remains blocked rather than
evaluated.

## What is now implemented

| Stage | Implemented boundary | Current result limit |
|---|---|---|
| Source identity and replay | Content-bound source records; strictly ordered, non-overlapping multi-range UTF-8 replay; `pdftotext`-version-bound single-region PDF word-snapshot replay; strict reviewed-transcription checks | Multi-region PDF composition fails closed until a deterministic order is bound; `pdfinfo` is required but its version is not pinned; PDF word replay is not character-and-whitespace transcription |
| Translation charter | Purpose, output, system boundary, in/out scope, protected distinctions, authority roles, and non-inductive constitution are frozen | The charter remains a proposal |
| Obligation graph | Target/context separation, exact classification of every selected span, verbatim source claims, open residue, typed protected features and dependencies, exact closure; branches cannot borrow unrelated spans or features | Completeness of the extracted obligations still requires criticism |
| Rival interpretations | At least two branches with consequences, falsifiers, loss risks, and exact model effects | No branch is selected by popularity, formal success, or survival |
| Compatible combinations | Every branch is independently admissible; `EXCLUSIVE`, `OVERLAPPING`, and `PARTIALLY_COMPATIBLE` sets carry exact `admissible_branch_sets` | Compatibility is declared and reviewable, not inferred as truth |
| Project imports | Source-free causal, semantic, physical, epistemic, and methodological premises have a separate record and deletion prediction; affected keys must equal their direct model use | Usefulness cannot promote an import to source authority |
| Neutral signature and model | Formalism-independent entities, roles, relations, clauses, dependencies, non-colliding element keys, connected open ports, and exact semantic closure | Production models have `NONE_V1` execution semantics |
| Two-way bridge and snapshot | Exact forward coverage, element-specific reverse incidence, directed source-to-clause dependency witnesses or exact open shifts, canonical inventory, and a content-addressed snapshot | V1 dependency-shift records lack an explicit edge ID and directed witness path; mapping fidelity remains `UNREVIEWED`; semantic verdict remains null |
| Human review | Append-only, claim-first branch dispositions and scoped translation decisions with exact scope and model bindings; changed bindings replay immediate snapshot/set lineage, and staleness follows a content-addressed branch across replacement sets until an explicit reopening | Reviewer authentication is not established by v1, so recorded authorization cannot make review `READY` or unblock integrated hardening |
| Dynamic attacks | All nine families are synthesized: deletion, negation, rival substitution, semantic-role twin, substrate swap, boundary shift, import dependency, non-vacuity, and round trip | The supplied delta is not yet derived from both inventories, and the attacks remain deferred without typed oracles and executors |
| Failure inquiry and research gate | Candidate, auxiliary, test, and scope criticisms can remain live together; every assessment route remains visible with selected/frontier/blocked state; exact external targets require a human-selected action | Route preview publishes nothing and chooses no winner; AlphaXiv is only a designated, replaceable discovery surface, and no retrieval adapter is implemented |
| Hardening | Exact comparison, conjunctive obligations, evidence records, human requirements, and inventory-bound resolution | Standalone v1 has no artifact resolver or model executor; caller finite payloads stay `INCONCLUSIVE`, so `HARDENING_UNREFUTED` is reserved but unreachable; integrated evaluation is additionally blocked on review authentication |
| Qualification | Code-pinned HRC-1 manifest; corrected public commitment; read-once fixture capture; actual candidate inventory/snapshot and report replay before controller disclosure; 34 mutations, six controls, and exact declaration-token comparison | The strongest runner label is `ALL_DECLARED_EXPOSURE_TOKENS_MATCH_CONTROLLER`; no mutation execution or blindness evidence has been completed, and Popper hostile replay is also open |

## Why the harness does not choose only one mechanism

A failed expected result attacks a conjunction. If the result depended on the
candidate (C), auxiliaries (A), test (T), and scope (S), then failure
permits the inclusive criticism

\[
\neg C \lor \neg A \lor \neg T \lor \neg S.
\]

It does not reveal which disjunct is correct, and more than one can be live.
The harness therefore separates diagnosis from scheduling. One bounded action
may serve several dependency-frontier criticisms when the work is genuinely
shared. Otherwise a human selects one work package for practical reasons while
the other criticisms remain visible. Scheduling never ranks truth.

The same rule applies to interpretations. One reading may exclude another;
several may overlap; or only particular combinations may coexist. Exact
`admissible_branch_sets` express those possibilities without forcing one branch
or assuming that every branch can be combined with every other.

## When research is warranted

Research is not the default response to difficulty. The route depends on what
would discriminate the live rivals:

| Needed discriminator | Route |
|---|---|
| Exact wording or structure in the content-bound authority | `AUTHORITY_REVIEW` |
| Consequence of the current translation, model, bridge, or import | `INTERNAL_MODEL_WORK` |
| Defect in a fixture, comparator, oracle, or runner | `INTERNAL_HARNESS_WORK` |
| External application fact, counterexample, or critical instrument absent from the frozen materials | `EXTERNAL_RESEARCH_REQUIRED` |
| Failure not yet located well enough to choose | Wait for plural human triage |

An external route requires genuine rivals, falsifiers, an expected
discriminator, a bounded source scope, a stop condition, a live external locus,
and an explicit subset of attack targets. AlphaXiv is the designated preferred
discovery surface after that gate, but this repository has no AlphaXiv or other
retrieval adapter. Its externally obtained rankings and summaries cannot decide
the issue; the primary source or reproducible construction must be inspected
directly.
Agreement, paper count, recency, and failure to find a criticism have no
confirmatory effect.

## Repository and published-state boundary

Repository: `https://github.com/AHepi/h-EPI`

Target branch: `main`

The clean remote base for this tranche was commit
`0162af9e9f445ceb9f1ec6621331deea8bd49b13`, tree
`7ff951d19da6b805a5e9615d06eed3c9f21ccf56`. A fresh fetch on 2026-09-04
showed the working base neither ahead nor behind `origin/main`. The publication
commit is the commit containing this handover; its exact path inventory is the
tree delta from that base. Publication must leave no unrelated staged or
unstaged path and must verify that local `HEAD` equals remote `main`.

The latest published-base CI inspected on 2026-09-04 is evidence only for
commit `0162af9`: [bootstrap integrity run 33796575214](https://github.com/AHepi/h-EPI/actions/runs/33796575214)
succeeded, while [bridge pilot run 33796575235](https://github.com/AHepi/h-EPI/actions/runs/33796575235)
was cancelled after the `evidence-records` job exceeded its five-minute limit.
That cancellation is not evidence for or against this uncommitted tranche.
Issue [#1, Hardening Completion — CR-EIB-0.2](https://github.com/AHepi/h-EPI/issues/1),
was still open, unassigned, and without a milestone; its full-PDF container
replay and human DF-7a review items remain open. This increment neither edits
the issue nor creates a duplicate status monitor.

## Full status tuple

| Surface | Current state | Boundary |
|---|---|---|
| Authority identity | `PINNED`; local PDF mechanically valid | Digest, bytes, pages, and registered replay only |
| Generic translation records | Validators implemented; no committed end-to-end instance | Structural integrity, not semantic fidelity |
| Translation human review | No committed lineage; authentication unavailable | A local declaration cannot make review `READY` |
| Mapping fidelity | `UNREVIEWED` | No source mapping is accepted as lossless |
| Bridge conformance | `BLOCKED` | Operational checks cannot promote it |
| Dependency closure | Incomplete | TH-3 source dependencies remain open |
| Source theorem status | Neither proved nor refuted | Relative Lean results do not adjudicate CR-1.0 |
| Bootstrap | Package integrity `PASS`; semantic bootstrap gate `FAIL` | Required declaration mappings and typed bodies remain incomplete |
| Adaptive inquiry | `AWAITING_HUMAN_TRIAGE`; zero questions | A menu of attacks authorizes no research |
| Standalone hardening | Positive status unreachable in v1 | No artifact resolver or model executor |
| Integrated hardening/readiness | `BLOCKED` / never `READY` in v1 | Review authentication and iteration lineage are absent |
| HRC-1 qualification | Fixture and declaration comparator present; execution absent | No blindness or mutation result has been established |

The exact TH-3 machine queue remains: `none` for `MS-4`, `MS-8`, `SC-7`,
`SC-8`, `IR-2`, and `IR-4`; `review-only` for `DF-7a`; and `candidate-only`
for `DF-10`. The immutable declaration bindings remain
`EIB-DF10-CANDIDATE` → `CREIB.EIB_DF10_CANDIDATE`,
`EIB-DF10-REFINED-CANDIDATE` → `CREIB.EIB_DF10_REFINED`,
`EIB-TH3A-PILOT` → `CREIB.EIB_TH3a_unfold`, and `EIB-TH3B-PILOT` →
`CREIB.EIB_TH3b_relative_non_sufficiency`. The accepted DF-10 and TH-3 anchor
digests remain `sha256:2ce383d202be73bd20465f0d0cbd39565fb418cdb6a90af006dae4d8bc260bff`
and `sha256:9a77b972f262b74b411a40999c0c5b235b5abfbd0091fd4c4ba9499462cdaa1c`.

The historical external audits were not rerun and do not cover this tranche.
Their frozen packet SHA-256 remains
`cd6a958505f1162f660da9c666b61d966d07bc58e8253f03e906c26b8cee403c`;
the original scoped GLM 5.3 and Kimi K3 report hashes remain
`48de0f874b785471e5bbe6f5ac30d8b1f64aa71e5a5034d4d22cb48d0917b75b`
and `c314a3a360cca8cd5971417730c241fb43ee4e80c013f81e161d2ff1a6798570`.
Both used the maximum supported reasoning setting, no output-token cap, and
returned normally without indicated truncation. The controller adjudication
and inclusion/omission manifest remain under `docs/audits/`; the exact
14-declaration release transcript remains
`03e1c0eb2638f2702dee2f2dd55cc4d61d9b4c54a65261e2f81b7d85ebd0ae35`.
Those are historical advisory artifacts, not independent authorities.

## Active artifacts

No runnable end-to-end generic translation instance is committed. There is no
committed generic source-to-snapshot inventory, v3 inquiry plan, review lineage,
delta, hardening packet, or HRC candidate report and freeze. The schemas and
runtimes are exercised by tests. The artifacts below are the active legacy SMF
calibration and v2 no-triage plan; they are not an integrated SMF-0.4 run.

Authority identity:

```text
Document: CR-1.0
SHA-256:  08ff81e848fea976b558345402d85723173be8f40f1041fb00d6267f1e026b8b
Bytes:    1734769
Pages:    286
```

Calibration record:

```text
Path:         forge/runs/SMF-CALIBRATION-CR-1-0-001.4219efce.json
SHA-256:      b83059255390e20da34cf416747bc13d5533a0794a7be7bdc0ba7760bc326fe2
Bytes:        28404
Run contract: 2bb36991abb95f2c87c5ecdde86b67d3392a5b9558de229614e9f5daafae1404
```

No-triage plan:

```text
Path:      forge/plans/SMF-AIP-1210e0fa.no-triage.json
Plan ID:   AIP:1210e0fa967f4e044f8c0129b9ec650abd61dc8a17b88bfdbb18525e0deea94d
SHA-256:   78f0c19d7fa609015a4ec6c610588d58460e77bcbba68778c1fd3f1b3bd38b8d
Bytes:     4923
Case:      sha256:150473c161fdeedefe67e5410409882d491144566a7eeecb097aecabca22ec08
Route:     AWAITING_HUMAN_TRIAGE
Questions: 0
```

The immediately superseded bytes are preserved at:

```text
forge/history/invalidated-runs/SMF-CALIBRATION-CR-1-0-001.4219efce.pre-review-lineage-replay.json
forge/history/invalidated-plans/SMF-AIP-5c012c57.pre-review-lineage-replay.no-triage.json
```

Invalidation is operational, not a semantic judgment. Older histories and
handovers remain evidence of which criticism forced each change.

## Verification

Local release verification on 2026-09-04 produced:

| Check | Observed result |
|---|---|
| Pinned Python requirements | Already satisfied from the offline environment with `--no-index` |
| Complete normal Python suite | 499/499 passed in 608.118 seconds |
| Complete optimized Python suite | 499/499 passed in 612.422 seconds |
| Combined translation, source replay, review, qualification, pipeline, and synthesis suites | 128/128 passed in normal mode in 133.413 seconds and optimized mode in 133.417 seconds |
| Independent adversarial release audit | Previously accepted span reordering, selection, dependency reversal/smearing, stale-branch reuse, fabricated candidate, rewritten fixture, and A-to-B snapshot-switch probes now fail closed; no remaining blocker was found in the patched boundaries |
| Python compilation | `python -m compileall -q src tools tests` passed |
| Offline schema/runtime validation | 28 schemas loaded; full corpus record reported `SCHEMA_AND_RUNTIME_VALID` |
| Calibration replay | Normal and optimized bytes exactly matched the active 28,404-byte record, SHA-256 `b83059255390e20da34cf416747bc13d5533a0794a7be7bdc0ba7760bc326fe2` |
| No-triage plan regeneration | Normal and optimized bytes exactly matched the active 4,923-byte plan, SHA-256 `78f0c19d7fa609015a4ec6c610588d58460e77bcbba68778c1fd3f1b3bd38b8d` |
| Bootstrap validator | Package integrity and quarantine discipline `PASS`; CR-1.0 semantic bootstrap gate remains `FAIL` |
| Formal package digests | Every entry in `formal/formal-package.sha256` passed |
| Bridge without PDF | Operational `PARTIAL`; records, schemas, choices, and formal package `PASS`; PDF and formal replay false; mapping `UNREVIEWED`; bridge `BLOCKED` |
| Bridge with exact PDF | Authority replay true; operational still `PARTIAL` because formal replay was not run; mapping `UNREVIEWED`; bridge `BLOCKED` |
| Lean, Lake, Docker | Unavailable; no compiler or container result was simulated |
| Whitespace | Tracked diff and all untracked text passed trailing-whitespace checks; the staged-tree check is repeated at publication |

No full operational `PASS` is claimed: that would require the exact PDF and
pinned Lean package to replay successfully in the same invocation. No container
evidence was produced in this environment.

These checks establish deterministic and structural behavior against the named
regressions. They do not establish semantic adequacy.

## Next implementation order

1. **Derive the snapshot delta.** Load both complete inventories, compute exact
   retained, added, removed, replaced, and transported records and nested
   semantic members, and reject a caller declaration that differs.
2. **Execute the nine attacks.** Define typed fixtures, held-fixed conditions,
   comparators, and expectations for each family; preserve every result as a
   criticism-bearing observation rather than a score.
3. **Close the iteration lineage.** Add content-addressed edges from test
   execution through observation, inquiry, research disposition, authorized
   revision, successor snapshot, derived delta replay, and hardening.
4. **Bind human authentication.** Authenticate the exact review decision,
   scope, snapshot, model, and terminal head without turning identity proof into
   semantic authority.
5. **Bind a real model executor.** Replace declared finite payloads with
   replayable artifacts, or add a proof checker, so counterwitness and witnessed
   outcomes can be reproduced independently.
6. **Run HRC-1 blind qualification.** Isolate the translator to the closed
   packet, freeze its output, execute all mutations and controls, then reveal
   the controller and preserve misses and false positives.
7. **Run a fresh Popper translation.** Keep the existing candidate hidden,
   freeze an independent bounded translation, compare only afterwards, and run
   the hostile restraint mutations. Disagreement opens a source-bound problem;
   agreement proves nothing.
8. **Extract more mathematics only after review.** Formalize the exact scoped
   model variant, imports, unresolved ports, test coverage, and preservation
   obligations that survived the preceding criticism cycle.

This file supersedes `CR-EIB-0.4_Orchestrator_Handover.md` as the live
continuation point. Earlier handovers are historical snapshots.
