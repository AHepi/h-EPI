# Semantic Model Forge 0.3 adaptive inquiry protocol

## Status and purpose

SMF-0.3 is an additive work-routing protocol around the deterministic SMF calibration. It decides what kind of work is authorized next after an exact calibration observation has been preserved. It does not decide what CR-1.0 means, authenticate a reviewer, confirm a model, or infer that external research is needed from a test result alone.

The implementation is in `src/creib/forge/inquiry.py`. `tools/run_semantic_inquiry.py` exposes plan, append, and chain-verification commands. The machine contracts are `forge/schema/adaptive-inquiry.schema.json` and `forge/schema/inquiry-event.schema.json`.

The governing epistemic limit is unchanged:

> Survival of criticism leaves a claim unrefuted; pass counts, consensus, and confidence do not justify it.

Every inquiry plan has `semantic_verdict: null`, `epistemic_status: UNRESOLVED`, and `epistemic_effect: WORKFLOW_ROUTING_ONLY`. Every event has `semantic_verdict: null` and `epistemic_effect: MAY_CRITICIZE_OR_ROUTE_WORK_ONLY`.

## Exact input binding

Planning begins by reading one calibration record and one external-research ledger from single byte snapshots. The calibration record must remain canonical JSON plus one newline and must pass its current deterministic report contract against the repository. A stale calibration implementation or corpus therefore fails before inquiry routing with `INQUIRY_RUN_NOT_CURRENT`. The research ledger must pass its strict runtime parser.

An inquiry case binds the following surfaces independently:

| Surface | Bound fields |
|---|---|
| Calibration record | File SHA-256, run ID, and run-contract SHA-256 |
| Authority | Exact authority SHA-256 from the run contract |
| Candidate | Candidate ID and candidate-contract SHA-256 |
| Challenge | Challenge ID and challenge-contract SHA-256 |
| Fixture | Fixture-contract SHA-256 |
| Evaluator | Evaluator ID and evaluator-contract SHA-256 |
| Observation | Fixed JSON pointer, domain-separated digest, and `CRITICISM_CANDIDATE_NOT_SEMANTIC_VERDICT` kind |
| Issue | Issue ID and domain-separated digest of the complete parsed issue |
| Warrant | Warrant ID and domain-separated digest of the complete parsed warrant |
| Research ledger | Ledger ID, exact file SHA-256, domain-separated record digest, `created_on`, and `as_of_date` |

The current adapter selects `/fixture_evaluations/weak_typed_role_projection`. It cross-checks the selected challenge and the candidate, challenge, fixture, and evaluator contracts against the run execution contract. Both the run-level and fixture-level semantic verdicts must remain null.

The warrant is not trusted by ID. The runtime recomputes

```python
generate_research_warrant(
    issue,
    discovery_channels=warrant.discovery_channels,
)
```

and requires complete typed-record equality with the supplied warrant. An ineligible issue, changed question, rival, falsifier, scope, stop condition, channel order, or other warrant content fails the binding even if visible IDs are retained.

The ledger chronology is part of the binding rather than decorative metadata: `as_of_date` cannot be later than `created_on`. The case digest is a domain-separated digest over the complete binding object and either the exact human-triage ID or null. Consequently, changing the run, model, observation, issue, warrant, research ledger, ledger dates, or triage creates a different case.

Content-addressed record IDs use canonical no-float JSON and exclude only their own ID field:

| Prefix | Record |
|---|---|
| `HT:` | Human failure triage |
| `AT:` | Rival-falsifier attack target |
| `IQ:` | Critical question |
| `AIP:` | Adaptive inquiry plan |
| `IE:` | Inquiry event |

## Human-triage gate

A calibration observation does not identify its own failure locus. It may criticize the candidate, an auxiliary assumption, the fixture, the oracle, the selected scope, or their conjunction. SMF therefore generates no external question until a separately supplied `human_failure_triage` record passes its schema, content-address check, and exact binding check.

The triage record must declare:

- one disposition: `CANDIDATE_DEFECT`, `AUXILIARY_DEFECT`, `TEST_DEFECT`, `OUT_OF_SCOPE`, or `UNRESOLVED`;
- one uncertainty location: `INTERNAL_DEDUCTION_OR_MODEL_FINDING`, `INTERNAL_HARNESS_SPECIFICATION`, `CR_AUTHORITY_INTERPRETATION`, `EXTERNAL_CRITICAL_INSTRUMENT`, `APPLICATION_EMPIRICAL`, or `UNLOCATED`;
- a nonempty reason and scope;
- a `created_on` date no earlier than the bound research ledger's `created_on` date;
- `reviewer_kind: HUMAN`, `machine_generated: false`, `epistemic_effect: WORKFLOW_ROUTING_ONLY`, `can_promote_model: false`, and a null semantic verdict.

The planner and CLI validate a supplied triage record but do not create one. The declared human fields are workflow claims, not cryptographic authentication of a person. Human judgments remain fallible, scoped, versioned by content, and open to later criticism.

The existence of an external issue and a mechanically generated `PROPOSED` warrant is therefore insufficient to authorize research. They express a possible route conditional on human triage; they are not the triage.

## Route reducer

The reducer uses precedence, not a score. It returns exactly one route:

| Condition | Route |
|---|---|
| No triage, or triage leaves the location `UNLOCATED` | `AWAITING_HUMAN_TRIAGE` |
| Disposition is `OUT_OF_SCOPE` | `OUT_OF_SCOPE` |
| Disposition is `AUXILIARY_DEFECT` or `TEST_DEFECT`, or location is internal harness specification | `INTERNAL_HARNESS_WORK` |
| Location is internal deduction or model finding | `INTERNAL_MODEL_WORK` |
| Location is CR-1.0 interpretation | `AUTHORITY_REVIEW` |
| External or application route is not authorized by the typed policy | `POLICY_BLOCKED` |
| A current question is marked stale | `POLICY_BLOCKED`; a new model snapshot and triage are required |
| A research entry awaits human discrimination review | `AWAITING_HUMAN_REVIEW` |
| A human-retained criticism candidate exists | `INTERNAL_INTEGRATION_REQUIRED` |
| At least one current question is proposed or active | `RESEARCH_IN_PROGRESS` |
| Human triage locates an external or application discriminator and a rival falsifier has no question state | `EXTERNAL_RESEARCH_REQUIRED` |
| Every exact target has a terminal human disposition under the current protocol | `NO_NEW_RESEARCH_UNDER_CURRENT_PROTOCOL` |

`AUTHORITY_REVIEW` is intentionally distinct from external research. External reports cannot settle CR-1.0 interpretation. `NO_NEW_RESEARCH_UNDER_CURRENT_PROTOCOL` means only that every current question has received a terminal human disposition; it leaves the semantic question unresolved and supplies no support to either rival. Protocol v1 has no operator-authored “search exhausted” transition.

The reducer never consumes a confidence value, score, pass count, citation count, source count, provider vote, or consensus measure.

## Critical-question construction

After an exact triage locates an `EXTERNAL_CRITICAL_INSTRUMENT` or `APPLICATION_EMPIRICAL` gap, the planner instantiates one question for every falsifier condition of every rival in the bound issue.

An attack target hashes the exact issue digest, warrant digest, rival ID, rival claim, and falsifier condition. It is content-addressed rather than position-addressed, so changed attack content cannot reuse an old target merely by keeping its list position.

Each critical question additionally binds:

- the case digest;
- the exact triage ID and triage `created_on` date;
- the authority, candidate, challenge, fixture, and evaluator as one model-binding digest;
- the triggering observation digest;
- the expected discriminator and decision relevance;
- the warrant's admissible source scope and stop condition;
- the ordered discovery channels;
- the default contemporary discovery channel bound by the current research-provider policy (AlphaXiv in the present ledger);
- direct inspection of the primary source as required;
- `provider_output_is_oracle: false`;
- `not_found_effect: ABSENCE_SUPPLIES_NO_SUPPORT`;
- `can_confirm_target_semantics: false`;
- `source_count_can_promote: false`; and
- `provider_agreement_can_promote: false`.

The generated query asks for a counterexample, boundary case, explicit denial, or discriminating instrument directed at one exact rival falsifier. It requires a direct primary-source locator or reproducible construction and the premise attacked. Its final instruction is that failure to find an attack leaves the question open: absence supplies no support and cannot retire the question in protocol v1.

These questions are mechanically exact relative to an already structured issue. The generator does not know that the issue's rivals, falsifiers, scope, or expected discriminator are semantically correct. It does not invent a new rival, shared-premise attack, or oracle when those inputs are inadequate.

## Event lifecycle

Question history is an append-only chain selected by an explicit head ID. No directory ordering or “latest file” rule chooses the authoritative head.

The permitted transitions and required actor kinds are:

| Event | Actor | Transition |
|---|---|---|
| `QUESTION_PROPOSED` | `MACHINE` | no state → `PROPOSED` |
| `QUESTION_ACTIVATED` | `HUMAN` | `PROPOSED` → `ACTIVE` |
| `RESEARCH_CANDIDATE_RECORDED` | `OPERATOR` | `ACTIVE` → `AWAITING_HUMAN_REVIEW` |
| `HUMAN_CRITICISM_RETAINED` | `HUMAN` | `AWAITING_HUMAN_REVIEW` → `RETIRED_WITH_CRITICISM_CANDIDATE` |
| `HUMAN_NONDISCRIMINATING` | `HUMAN` | `AWAITING_HUMAN_REVIEW` → `RETIRED_NONDISCRIMINATING` |
| `HUMAN_MISFRAMED` | `HUMAN` | `PROPOSED`, `ACTIVE`, or `AWAITING_HUMAN_REVIEW` → `RETIRED_MISFRAMED` |
| `HUMAN_OUT_OF_SCOPE` | `HUMAN` | `PROPOSED`, `ACTIVE`, or `AWAITING_HUMAN_REVIEW` → `RETIRED_OUT_OF_SCOPE` |
| `MODEL_CHANGED` | `MACHINE` | `PROPOSED`, `ACTIVE`, or `AWAITING_HUMAN_REVIEW` → `STALE_BY_MODEL_CHANGE` |

A research-candidate event embeds a standalone immutable v2 source-entry snapshot created after the exact question exists. The background ledger remains bound as the provider and epistemic policy snapshot, but the new report need not be chronologically pre-seeded into it. Runtime validation applies the complete entry parser, report and entry digests, primary-inspection requirement, event-date chronology, provider policy, contemporaneity rule, non-authority fields, and exact equality of `attacked_harness_question` and `falsifier` with the active question. Every event date must be no earlier than its question's bound triage date. The entry also receives a separate domain-separated digest in the event. An arbitrary provider result cannot be inserted directly.

Human event names and actor fields do not let the machine issue a human disposition. The command requires the operator to request the transition explicitly, and the runtime rejects a machine actor for every human-only transition.

## Append-only and replay integrity

Every event embeds the complete immutable question, previous event ID, contiguous sequence number, transition, actor kind, reason, research-ledger binding, and any exact research entry. Its `IE:` ID hashes all event content except the ID itself. Event files use the ID-derived filename and canonical JSON plus one newline.

Chain verification walks backward from the explicitly supplied head and checks:

- event schema and runtime invariants;
- content-addressed event and question IDs;
- exact research-ledger binding;
- standalone research-entry parsing, policy checks, exact question targeting, and digest when applicable;
- absence of cycles;
- a contiguous sequence beginning at one;
- every previous-event link;
- nondecreasing event dates;
- no event date earlier than the immutable question's bound triage date;
- no reuse of a research-entry ID for different content;
- equality of every repeated copy of a question; and
- each declared `from_state` against the replayed prior state.

Publishing is no-clobber. The writer first validates the selected head, then writes and fsyncs a same-directory temporary file. A permanent `NEXT-<parent>.claim` hard link atomically reserves the parent head before the event's final ID-derived hard link is created. A different claimant for the same parent receives `INQUIRY_EVENT_STALE_HEAD`; an existing event path receives `INQUIRY_EVENT_EXISTS`.

For the current case, every question referenced by a plan or transition must be byte-for-byte equal to a question in the exact inventory regenerated from the current run, ledger, triage, and origin head. A caller cannot forge a new current-case question merely by computing self-consistent content hashes. Historical cases remain replayable against their own immutable bindings; they are not retroactively required to occur in today's inventory.

This mechanism is tamper-evident relative to a preserved head and files. It is not an external timestamp, signature, or protection against an actor replacing the entire event directory and every recorded head. A continuation-grade handover or repository commit must pin the selected head when a real chain exists.

## Strictly non-inductivist behavior

The protocol distinguishes the existence of one concrete criticism candidate from its frequency. A concrete report changes the workflow from active research to human review because it supplies inspectable attack content. A second or hundredth agreeing report cannot promote the question beyond `AWAITING_HUMAN_REVIEW`, cannot change the model, and cannot create a semantic verdict.

Likewise:

- a passed test leaves the tested conjunction unrefuted by that test;
- a failed test initially criticizes the candidate, auxiliaries, fixture, oracle, scope, and interpretation together;
- provider ranking may affect discovery order but has no epistemic effect;
- AlphaXiv output is a discovery route, not a primary source or oracle;
- source frequency and citation count are neither accepted question fields nor reducer inputs;
- human retention produces a criticism candidate for internal integration, not automatic rejection or repair;
- failure to find an attack cannot retire a question or support a rival; and
- neither a plan nor an event can emit a positive semantic status.

## Live no-triage result

On 2026-09-03 the additive planner was run against the current canonical calibration record and research ledger:

```bash
.venv/bin/python tools/run_semantic_inquiry.py plan \
  --run-record forge/runs/SMF-CALIBRATION-CR-1-0-001.4219efce.json \
  --research-ledger forge/research/SMF-RESEARCH-2026-09-03.json
```

The command completed successfully and emitted exact run, model, observation, issue, warrant, and research-ledger bindings. Its operative result was:

```text
route:                AWAITING_HUMAN_TRIAGE
route_reason:         A mechanical observation cannot locate its own failure locus.
triage:               null
proposed_questions:   []
question_state:       {}
state_head_event_id:  null
semantic_verdict:     null
epistemic_status:     UNRESOLVED
```

No persistent event was created. This is deliberate: without genuine human triage there is no authorized question to propose, activate, research, or retire.

The canonical no-triage output is preserved at `forge/plans/SMF-AIP-2d589a64.no-triage.json` with plan ID `AIP:2d589a644ec7a39d586d98fc612d16ada752059d320fb022726aa80d571031e4` and file SHA-256 `fd9edbee175ed3e23c1c5e0d3e92c132e75b7a94f2bb47d64a133ef473719693`.

## CLI surface

`plan` produces a deterministic routing record from a current calibration, research ledger, optional human triage, and optional explicit event head. Omitting `--triage` fails closed as shown above.

`append` selects a content-addressed question from an exact plan, replays the selected head, constructs one permitted transition, and publishes it without overwrite. It also regenerates the plan from the exact current run, ledger, and origin head, so a self-rehashed stale plan cannot authorize a transition. Non-proposal transitions must name a question already present in the current plan state. The CLI applies an explicit route/event allowlist: a route can authorize only lifecycle events appropriate to that route, while `POLICY_BLOCKED` and `INTERNAL_INTEGRATION_REQUIRED` authorize no continued research. The caller must supply the actor kind, date, reason, and event type. A research-candidate transition also requires an exact standalone v2 source-entry snapshot targeted at that active question.

`verify` replays one explicitly selected event head and reports only `INTRINSIC_CHAIN_INTEGRITY_VALID`, event count, and question states. Its epistemic effect is `INTEGRITY_REPLAY_ONLY`.

## Current limitations

SMF-0.3 is a complete protocol slice for the first role-projection calibration, not a general semantic-model research agent.

1. The adapter is fixed to the weak typed-role projection and one observation pointer. It does not yet consume arbitrary challenge families, model deltas, hardening assessments, or full CR-1.0 model-class searches.
2. It cannot determine the semantic failure locus. Human triage is mandatory, and the implementation does not authenticate the human cryptographically.
3. Question generation expands already declared rival falsifiers. It cannot determine that those are the right rivals or invent a missing shared-premise attack.
4. An event-time report is preserved inside the event as a standalone source-entry snapshot. The protocol does not yet maintain a separate evolving catalog of those snapshots or import them into the background research ledger.
5. A changed run, model, observation, issue, warrant, triage, or ledger produces a new case binding. The protocol does not silently migrate prior question dispositions into that case.
6. A stale question blocks the current case; it does not automatically create or approve a replacement.
7. Search protocols retain a human-readable stop condition, but protocol v1 cannot authenticate or prove exhaustive execution. It therefore provides no `PROTOCOL_EXHAUSTED` event; a null search result leaves the active question open.
8. Event claims prevent two published successors from the same selected parent in one directory. External preservation of the chosen head remains necessary for durable tamper evidence.
9. No inquiry decision can currently authorize `HARDENING_UNREFUTED` or `PROVISIONALLY_READY`. The existing hardening and readiness schemas must evolve to encode both strength axes and all preservation obligations, then gain separately typed, digest-bound human decision resolution, before positive promotion can exist.

The next authorized semantic action is therefore human triage of the exact role-relabel criticism candidate. Until that record exists, “do more research” is not a justified machine conclusion.
