# CR-EIB-0.4 orchestrator handover

## Outcome

The Semantic Model Forge no longer forces a failed test into one exclusive failure diagnosis. Its active v2 inquiry contract preserves every live candidate, auxiliary, test, and scope criticism, including mechanisms that cross several loci. A separate `next_action` chooses only the work to run next. That operational choice cannot rank the criticisms, identify a unique cause, close an unselected criticism, or promote the model.

The current authority-bound run and no-triage plan replay exactly. The published triage lineage has no genesis record or claim, so the plan remains `AWAITING_HUMAN_TRIAGE`, with a non-authorizing attack-target menu, no research questions, and a null semantic verdict. No conversational agreement was converted into a machine-actionable human record.

## Authority and status boundaries

The sole semantic and formal authority remains the externally supplied PDF *Creativity as Explanatory Self-Correction*, Model CR-1.0:

```text
SHA-256: 08ff81e848fea976b558345402d85723173be8f40f1041fb00d6267f1e026b8b
Bytes:   1734769
Pages:   286
```

The active formal span remains physical PDF pages 219–234, printed folios 218–233. Repository prose, source mappings, corpus annotations, project imports, research reports, tests, countermodels, and Lean declarations remain subordinate artifacts with separately typed status.

No source-level creativity theorem has been proved or refuted. No SMF result establishes that a formalization is faithful to CR-1.0.

| Surface | Current result | What it does and does not establish |
|---|---|---|
| Authority binding | `MECHANICALLY_VALID` | Exact PDF identity, byte length, page structure, and pinned anchors only. |
| Calibration | `RUN_COMPLETE` | The scheduled mechanics completed; the result is not a semantic verdict. |
| Epistemic status | `UNRESOLVED` | No test or research count can promote the model. |
| Human review | `AWAITING_HUMAN` | No digest-bound v2 triage exists for the current case. |
| Adaptive route | `AWAITING_HUMAN_TRIAGE` | No work route or research question is authorized. |
| Naive disconnected repair | `NO_HARDENING` | Its old-language fixture behavior is unchanged after erasure. |
| Connected causal-role proposal | `UNRESOLVED` | It has not discharged the strength-preservation obligations. |
| Formalization readiness | `BLOCKED` | Mapping, dependency, witness, and review obligations remain open. |
| CR-EIB operational integrity | `PARTIAL` locally | Exact PDF replay passed; Lean was unavailable locally. |
| Mapping fidelity | `UNREVIEWED` | No human review has accepted the source-to-formal mapping. |
| Bridge conformance | `BLOCKED` | Operational checks cannot promote mapping or full-model status. |
| Bootstrap gate | `FAIL` | Package integrity passes, but declaration-level mappings and typed bodies remain incomplete. |

## Repository and publication state

Repository: `https://github.com/AHepi/h-EPI`

Target branch: `main`

The clean remote starting point for this increment was commit `78491c1e9bf7212b9532339084912b43f6a08571`, tree `fc9750696633970a2fd15e768b8a9f256f32cd67`. The implementation commit is the commit containing this handover; after publication, resolve it with `git rev-parse origin/main`. Do not force-push or rewrite the branch.

## Why the contract changed

The v1 triage encoded exactly one disposition. That was stronger than the observation justified. If an expected result depends on candidate adequacy \(C\), auxiliaries \(A\), test adequacy \(T\), and applicable scope \(S\), then a counter-result attacks their conjunction:

\[
C \land A \land T \land S \Rightarrow E, \qquad \neg E.
\]

The permitted criticism is the inclusive alternative

\[
\neg C \lor \neg A \lor \neg T \lor \neg S.
\]

It does not identify one false conjunct. Several criticisms can remain live, and one mechanism can involve more than one locus. The old scalar route also let an `OUT_OF_SCOPE` label short-circuit the other possibilities. V2 removes both errors.

## Active v2 contract

Each `human_failure_triage.v2` record has `overall_status: UNRESOLVED` and a nonempty, canonically ordered `locus_assessments` collection. An assessment:

- names one or more of `CANDIDATE`, `AUXILIARY`, `TEST`, and `SCOPE`;
- states a concrete mechanism, why it matters here, what could discriminate it, its scope, uncertainty location, and dependencies;
- remains `LIVE` with `epistemic_effect: CRITICISM_ONLY`; and
- explicitly cannot establish a unique cause.

`UNRESOLVED` is an overall condition, not a fifth diagnosis. Omitting a locus leaves it unassessed; it does not clear it. A `SCOPE` assessment may criticize either case membership or the adequacy of the boundary, so its presence never vetoes another live criticism.

Assessments themselves are immutable. A separate append-only, content-addressed disposition chain can record one of three fallible human judgments for an exact assessment and exact input binding: `RETAINED` keeps or reopens it; `DEFEATED` records that its declared discriminator was answered in scope; and `STALE_BY_BINDING_CHANGE` records that an exact input change made it inapplicable without refuting it. The active evidence contract accepts only the exact bound calibration observation at the binding's declared observation pointer, or the exact input-binding delta needed for staleness. Every disposition repeats the discriminator and is fixed to workflow-only effects. The content-addressed envelope proves which evidence bytes and pointer were cited; it does not authenticate the reviewer or prove the reviewer's fallible statement about how those bytes bear on the discriminator. Runtime checks close label-only and unscheduled-frontier bypasses. Fixed fields enforce declarations that a disposition cannot establish a unique cause, confirm or promote the model, or let “not found,” source count, or provider agreement decide; the truth of free-text reasoning remains reviewable.

The nullable, content-addressed `next_action` is a scheduling record. It can address several compatible dependency-frontier assessments when one review or experiment genuinely serves them together. Otherwise it records a dependency-first step or an explicit human priority between independent fronts. Array position, diagnosis name, confidence, consensus, pass counts, and historical frequency never choose the action.

Triage state determines waiting routes, a selected action chooses the work class, and event state refines the external-question lifecycle:

| Selected work | Route |
|---|---|
| No triage | `AWAITING_HUMAN_TRIAGE` |
| Effective-live assessments but no action | `AWAITING_HUMAN_ACTION_SELECTION` |
| No assessment is effective-live because every one has a current-binding terminal disposition | `AWAITING_HUMAN_REASSESSMENT`, still unresolved |
| Harness or oracle work | `INTERNAL_HARNESS_WORK` |
| Deduction or model finding | `INTERNAL_MODEL_WORK` |
| CR-1.0 interpretation | `AUTHORITY_REVIEW` |
| Exact external discriminator | External-question lifecycle |

Every plan derives the complete canonical `available_attack_targets` menu from the bound issue and recomputed warrant. The menu is information for choosing work, not permission to perform it. An external action must bind the exact issue and warrant and select a canonical nonempty subset of attack-target IDs. Only those targets become questions. Each question copies the selected assessments, action text, selection reason, and complete selected target into its binding, and embeds the target's rival, claim, and falsifier in the query. Other menu entries and external-looking assessments remain live but authorize no search. Every question still requires rivals, falsifiers, a discriminator, admissible scope, a stop condition, direct primary-source inspection, and the rule that “not found” supplies no support. A recorded source report is additionally enveloped with the exact question, case, triage, action, and attack-target identities. Source reports in events and entries in the bound research ledger share one `entry_id` namespace: reusing an ID is allowed only for the exact same complete source report, while different content under that ID is rejected. The question-specific envelope remains separate from this identity rule. Together these checks prevent unchanged replay under another question and silent ID collision; they do not prove that a reusable report discriminates the rivals. AlphaXiv remains the current replaceable discovery channel after this gate, not an oracle, a primary-source substitute, or source authority.

V1 plans, triage, questions, and events retain their historical identities and intrinsic validators; existing v1 event chains remain replayable. They are read-only: they cannot be newly published, start or extend the active triage lineage, authorize a current v2 transition, or receive a v2 event successor.

## Publication and binding rules

A human-authored triage JSON is only a draft. Active workflow authority comes from one explicitly selected terminal `HT:` record in `forge/triage/`. `publish-triage` derives the current run/ledger bindings and attack-target menu independently, validates the draft, and publishes an ID-named record plus a no-clobber successor claim. The claim is a durable write-ahead reservation: if publication stops after the exact claim is written, a retry may roll forward only that byte-identical candidate after revalidating its context, parent, and successor. A complete matching claim-and-record pair is idempotent; a record without its claim, a conflicting claim, or any other incomplete public inventory fails closed. Directory order, modification time, a familiar filename, or an unselected loose file never chooses the head. Once genesis exists, planning without `--head-triage-id` fails; “no head” means “no published lineage,” not “ignore the lineage.”

The triage lineage is additive. Genesis has sequence one, no predecessor, and no dispositions. Every successor increments the sequence, links the selected parent, and retains all earlier assessments and dispositions byte-for-byte. It may add multiple criticisms, append at most one disposition per pre-existing assessment, or change the one scheduled action; it cannot delete or rewrite history. Disposition sequences and predecessor links must form one chain for each assessment. Dependencies are scheduling edges, not evidential premises: a dependent reaches the frontier only after every prerequisite has a current-binding `DEFEATED` or `STALE_BY_BINDING_CHANGE` disposition. A same-binding disposition of an effective-live assessment must follow an action that selected it on the predecessor frontier; a terminal assessment can only be reopened by `RETAINED`. If a new disposition makes a carried selected assessment non-live, the successor must clear or replace the action. If all inquiry bindings remain equal, the successor declares `SAME_BINDINGS`. If a run, candidate, challenge, fixture, evaluator, observation, issue, warrant, or ledger snapshot changes, it declares `INPUT_BINDING_CHANGED`, preserves the authority and logical ledger identities, explains the exact change, and clears `next_action` for fresh human scheduling. Such a successor may append only exact staleness dispositions. Earlier dispositions remain history but lose operational effect under the new bindings. An action selected for an earlier case never carries forward silently.

Question events and assessment dispositions are intentionally different. Event `HUMAN_CRITICISM_RETAINED` retires one question into internal integration; assessment `RETAINED` keeps or reopens the criticism. Question `STALE_BY_MODEL_CHANGE` closes an old question; assessment `STALE_BY_BINDING_CHANGE` is a separately evidenced human workflow judgment. Events never synthesize dispositions.

Event publication is equally contextual and uses the same durable-claim recovery rule. Before any write, the runtime publisher requires an active v2 plan and regenerates it against the exact run, ledger, published triage head, and selected event head. It then rechecks the route, question membership, research binding, parent link, sequence, chronology, and event `from_state` against the replayed state of that exact question. Intrinsic plan validation checks only local structure and compatible head syntax; a nonempty question state or event-history block therefore requires an `IE:` head, but intrinsic validation cannot prove that the referenced event exists. Contextual regeneration provides that assurance by requiring the complete event-record and successor-claim inventories to match and replay to the selected head. Replay also forbids mixed v1/v2 ancestry; active operations require v2. Intrinsic schema validity, a self-consistent hash, or a successful historical replay is insufficient publication authority.

## Continuation inventory

| Continuation surface | Authoritative continuation reference |
|---|---|
| CR-1.0 identity and locators | `authority/source_manifest.json`, `authority/source_anchors.json`, and the operator-supplied PDF with the pinned identity above. |
| Bootstrap quarantine | `baseline/cr-1.0/bootstrap-v0.1/`; package integrity is distinct from the still-failing declaration-completeness gate. |
| Bridge declarations and choices | `bridge/declarations/`, `bridge/choices/interpretation-choices.json`, and `bridge/schema/`; these remain proposals with unreviewed mapping fidelity. |
| Formal pilot | `formal/CREIB/` and its pinned Lean package; the checked pilot is relative to its declarations, not a full CR-1.0 theorem. |
| Forge architecture and research boundary | `docs/forge/SMF-0.1_Architecture.md`, `SMF-0.1_Research_Basis.md`, and `SMF-0.2_Mathematical_Target.md`. |
| Active inquiry contract | `forge/schema/adaptive-inquiry-v2.schema.json`, `forge/schema/inquiry-event-v2.schema.json`, `src/creib/forge/inquiry.py`, and `tools/run_semantic_inquiry.py`. |
| Human-triage publication state | `forge/triage/`; its README specifies the only active lineage boundary. At this handover there is no published genesis or selected triage head. |
| Current run and no-triage plan | The exact paths and identities in the Active artifacts section below; both must be regenerated after any bound implementation or schema change. |
| Research inputs | `forge/corpus/cr-1.0-seed.json` and `forge/research/SMF-RESEARCH-2026-09-03.json`; their classifications and oracles remain reviewable project inputs. |
| Preserved inquiry history | Unsuffixed v1 schemas plus `forge/history/invalidated-runs/` and `forge/history/invalidated-plans/`; validate or replay, never reactivate or extend. |
| Human-facing protocol | `docs/forge/SMF-0.3_Adaptive_Inquiry_Protocol.md` and `.codex/skills/h-epi-human-handoff/SKILL.md`; the latter requires practical, falsifier-first, non-confirmatory handoffs. |
| Prior handovers | `CR-EIB-0.2_Orchestrator_Handover.md` and `CR-EIB-0.3_Orchestrator_Handover.md` are historical. This 0.4 file is the continuation point. |

Legacy facts remain binding unless a separately authorized, append-only successor changes them: source reports, source interpretations, project imports, and formal consequences remain distinct claim kinds; the weak two-Boolean calibration is not the full model class or a genuine same-reduct role twin; the neutral signature and source-to-model mapping remain proposals; and positive hardening or readiness cannot be produced from passing tests, proof success, empty blocker lists, or plain references. The old DF-7a/`CCPWitness`, TH-3 dependency, DF-10 interpretation, SMT/witness, mapping, intended-model, non-vacuity, global non-broadening, exact-fiber, and preservation obligations therefore remain open alongside the new human-triage step.

## Active artifacts

Calibration record:

```text
Path:         forge/runs/SMF-CALIBRATION-CR-1-0-001.4219efce.json
SHA-256:      e033cb8e82c6a38799f8b8c8f7f3bf4694ac54046e099e98b17d8abc8fb3d999
Bytes:        26162
Run contract: e6b9cbe72539ef0be5b02e05a755365e3df6ffb58b6c5113b8cd60c199b208fd
Bound implementation files: 26
```

No-triage plan:

```text
Path:      forge/plans/SMF-AIP-a5d3d7fb.no-triage.json
Plan ID:   AIP:a5d3d7fb4ced18cf97dbc94d6d0b0a48842dbeabcd26a0644f9ae26a9a9cd386
SHA-256:   6679c04c8a37108dd50a7dd9d3c9e472ea697d7aec871c6ea073007c83125006
Bytes:     4923
Case:      sha256:fd836247b96d470b239641365439f090117f43d947ed8322af559c0033e26cf6
Route:     AWAITING_HUMAN_TRIAGE
Questions: 0
```

Unchanged inputs:

```text
Seed corpus SHA-256:     4219efceb5502aa8b9209884ec1d22533d6eb049277c8ae3354d08e38f7c47a6
Research ledger SHA-256: 9c70fb98a460de146a60eb4f7e66f7255fa189449d177fc5f951fcd0c6d11d56
```

The prior active records are preserved byte-for-byte:

```text
forge/history/invalidated-runs/SMF-CALIBRATION-CR-1-0-001.4219efce.pre-multilocus-triage.json
SHA-256: ac4737d3647ccf4f5f636e544fc4dd762f2fb9c446d1c02fa032417962899943

forge/history/invalidated-plans/SMF-AIP-2d589a64.no-triage.json
SHA-256: fd9edbee175ed3e23c1c5e0d3e92c132e75b7a94f2bb47d64a133ef473719693

forge/history/invalidated-runs/SMF-CALIBRATION-CR-1-0-001.4219efce.pre-append-only-triage.json
SHA-256: 5d5d2b9e8dd0f4103bb94bb7eb51e4ae917a0f8cac5cabac38196334c792742d

forge/history/invalidated-plans/SMF-AIP-48c3f4df.no-triage.json
SHA-256: 146d246baa135f2659fe1106efefe4ca2be257ce4007e7938c4580f88a7439e9

forge/history/invalidated-runs/SMF-CALIBRATION-CR-1-0-001.4219efce.pre-disposition-event-integrity.json
SHA-256: 724cdb6efcc5854f3783dc46b76e7d40bf427d33588fc3463cd394589d171d8b

forge/history/invalidated-plans/SMF-AIP-fe2e0f16.no-triage.json
SHA-256: 32336ae8045db26276475b018c6a20549a096edd9491ae25afb2dc4c4e9aa744

forge/history/invalidated-runs/SMF-CALIBRATION-CR-1-0-001.4219efce.pre-evidence-provenance-hardening.json
SHA-256: e142013b2e9f51c8bd667f0d19f85fa461bc29c3583ea0d6256880745fb4cdab

forge/history/invalidated-plans/SMF-AIP-b17b2120.no-triage.json
SHA-256: a8bccee689fcb17e2cdf20223af09b389505dbb12a128418884cd2c18d562810

forge/history/invalidated-runs/SMF-CALIBRATION-CR-1-0-001.4219efce.pre-dependency-frontier-question-validation.json
SHA-256: 18d64974514fc47232e06b4ea1a45ec22bb2715b48bd5f162c26a52e3d0de305

forge/history/invalidated-plans/SMF-AIP-f562d179.no-triage.json
SHA-256: 2b6df34a1ca11087b895e2985bac9f5730a7a392ff64694a745aaa0bfe784e9d

forge/history/invalidated-runs/SMF-CALIBRATION-CR-1-0-001.4219efce.pre-recoverable-publication.json
SHA-256: 2408f4ec4cd7a815e94a80979ca15beebdad823fe29bfeaaf6d565acf92ccfe0

forge/history/invalidated-plans/SMF-AIP-bfe35a0a.no-triage.json
SHA-256: 38a989ab1c52f1327575e6e62eb30d6e645f647f3b762f32470caa6417ea4567

forge/history/invalidated-runs/SMF-CALIBRATION-CR-1-0-001.4219efce.pre-contextual-idempotent-recovery.json
SHA-256: 0ae41d4de2fe9e0c76ec6abd0627cf256fa554528afe688e47c97d636ea5d220

forge/history/invalidated-runs/SMF-CALIBRATION-CR-1-0-001.4219efce.pre-canonical-pending-recovery.json
SHA-256: 4cd574daae2432b14572f883ad1719817bcb87a3abe4533e1e3a6f4e422a980a
```

History now contains 18 invalidated runs and 11 invalidated plans. Invalidation is operational, not a semantic judgment.

## Verification on 2026-09-03

| Check | Result |
|---|---|
| Full Python test suite | 313/313 passed. |
| Full optimized Python (`-O`) suite | 313/313 passed. |
| Focused inquiry, corpus, and validation suites | 111/111 passed in each mode as part of the full runs. |
| Offline schema catalog | 9 schemas loaded with all references resolved. |
| Corpus and research ledger | Full schema and runtime validation passed. |
| Active calibration | Current-repository replay passed against the exact PDF. |
| Active no-triage plan | Intrinsic validation and exact contextual regeneration passed. |
| Normal versus optimized artifacts | Calibration and plan bytes were identical to each other and to the active files. |
| Bootstrap validator | Package integrity `PASS`; CR-1.0 bootstrap gate remains `FAIL`. |
| Bridge without PDF | Operational `PARTIAL`; records, schemas, choices, and formal package `PASS`; mapping `UNREVIEWED`; bridge `BLOCKED`. |
| Bridge with exact PDF | Authority checked; the same operational, mapping, and bridge statuses remained. |
| Lean/Lake/Docker | Not available locally; no result was simulated. |
| Whitespace and repository checks | `git diff --check` and the staged-tree checks passed before publication. |

These checks establish deterministic integrity and resistance to the named regressions. They do not establish semantic adequacy.

## Remaining boundary

The forge is still a kernel around one deliberately weak role-projection calibration. It cannot authenticate a human reviewer, infer the correct locus assessments, invent a missing rival or falsifier, translate the complete CR-1.0 source span into the neutral signature, prove an external search exhaustive, or authorize positive hardening/readiness status.

Changing any assessment, dependency, or scheduled action creates a new conservative case identity. This prevents stale dispositions from carrying into a changed problem, but it also means an unrelated new assessment rolls over the current question set. That choice is safe and intentionally conservative; action-scoped carry-forward remains future work.

For a published lineage, “changing an assessment” cannot mean mutating or dropping its record. It means adding a new assessment in a successor; only a newly added assessment can introduce a new dependency. Workflow treatment of an assessment is likewise additive: append a disposition that names the original assessment and accepted evidence type. An input-binding change requires an explicit successor with `next_action: null`; old dispositions remain inspectable but no longer control the frontier. The evidence envelope proves content and pointer integrity, not reviewer identity or the correctness of the human bearing statement. New source reports, authority interpretations, proofs, model-finder results, and application observations must first enter a typed bound calibration/input contract; arbitrary disposition evidence is deliberately unsupported. Action-scoped carry-forward and the separate model-level decision contract remain future work.

## Next work in human terms

The next step is not to choose which explanation is “the winner.” It is to write one exact human triage record that keeps every criticism we still consider worth testing. For the present labels-only fixture, the review should explicitly consider:

1. **Candidate:** the weak projection may be missing a causal-use condition.
2. **Auxiliary:** the Boolean reification, source mapping, or held-fixed assumptions may be wrong.
3. **Test:** the finite contrast may not yet be a genuine same-reduct role twin, and its oracle is provisional.
4. **Scope:** it is unsettled whether the weak projection is being asked to do the same job as the CR-1.0 model class.

Those are starting criticisms, not accepted findings. The human record must state the concrete mechanism, relevance, discriminator, scope, uncertainty location, and dependencies for each one retained.

Turn that judgment into an operational, append-only workflow record in this order:

1. Read the current no-triage plan's bindings and `available_attack_targets`; treat the latter only as a menu of exact possible falsifiers.
2. Author a v2 genesis triage against those exact bindings. Keep every plausible criticism live, state what would defeat each one, leave the required disposition list empty, and either leave `next_action` null or choose one dependency-frontier work package. If the action is external, select only the exact attack-target IDs needed for that work.
3. Publish the draft with `publish-triage` against the same run and research ledger. For genesis, omit the expected parent; for later records, supply the current terminal head. Do not copy the draft directly into the directory or edit claims.
4. Regenerate `plan` with the returned `triage_id` as `--head-triage-id`. Check that `state_head_triage_id`, `live_locus_assessment_ids`, `selected_action_id`, route, and any proposed questions match the human choice.
5. If and only if the route exposes an exact question, publish its event through `append` using the exact regenerated plan and event head. The publisher will recheck the run, ledger, triage head, event head, route, and question before writing.
6. After a previously authorized discriminator is actually reviewed and represented in the bound calibration input, append a successor containing an evidence-bound `RETAINED` or `DEFEATED` disposition for that selected assessment. Use `STALE_BY_BINDING_CHANGE` only with an exact input delta. Regenerate the plan; do not edit the assessment, infer a disposition from question closure, or treat a set with no effective-live assessment as model confirmation.

A sensible dependency order for the content of that triage is:

1. Review the source-to-neutral mapping and the intended scope together where one authority review can address both.
2. Independently construct a genuine same-reduct test rather than treating the current two-Boolean fixture as decisive.
3. Use those results to sharpen the candidate-level attack and any proposed repair.
4. Use AlphaXiv only if a remaining discriminator is genuinely external and an exact external action passes the rivals/falsifiers/scope/stop gate.

The one `next_action` is just the dispatch ticket for the first executable work package. It can name several compatible criticisms, and it leaves every other assessment live for later actions. Until that record exists, the correct machine behavior is to wait rather than research, repair, or formalize by default.

What should change the next choice is a declared discriminator: a source passage that defeats an interpretation, a repaired same-reduct fixture that defeats the test criticism, a model or countermodel that bears on the candidate, or an application observation that attacks an empirical mechanism. Mere completion, agreement, repeated survival, AlphaXiv rank, source count, or failure to find a criticism changes none of those assessments by itself. A disposition must remain an explicit, separately published human judgment bound to an accepted exact evidence type and current inputs. Even when every present criticism has a current-binding terminal disposition and none remains effective-live, the machine asks for human reassessment rather than confirming the model.

This file supersedes `CR-EIB-0.3_Orchestrator_Handover.md` as the continuation point. Earlier handovers remain immutable historical evidence.
