# Semantic Model Forge 0.3 adaptive inquiry protocol

## Status and purpose

SMF-0.3 is an additive work-routing protocol around the deterministic SMF calibration. It records which criticisms remain live and decides what kind of work is authorized next after an exact calibration observation has been preserved. It does not decide what CR-1.0 means, authenticate a reviewer, confirm a model, identify a unique cause of failure, or infer that external research is needed from a test result alone.

The implementation is in `src/creib/forge/inquiry.py`. `tools/run_semantic_inquiry.py` exposes planning, triage publication, contextual event publication, and chain-verification commands. The active machine contracts are `forge/schema/adaptive-inquiry-v2.schema.json` and `forge/schema/inquiry-event-v2.schema.json`. The exclusive v1 schemas and records remain unchanged as validation and replay evidence; active construction and publication neither reinterpret nor extend them.

The governing epistemic limit is unchanged:

> When a claim survives criticism, it remains unrefuted; pass counts, consensus, and confidence do not justify it.

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

The ledger chronology is part of the binding rather than decorative metadata: `as_of_date` cannot be later than `created_on`. The v2 case digest is a domain-separated digest over the complete binding object and either the exact selected human-triage ID or null. The triage ID covers its lineage link, every locus assessment, every dependency, every evidence-bound assessment disposition, and the scheduling action. Every published triage successor therefore changes the case digest. This conservative rollover preserves old questions and events as history rather than carrying their question states into a changed problem situation.

Content-addressed record IDs use canonical no-float JSON and exclude only their own ID field:

| Prefix | Record |
|---|---|
| `HT:` | Human failure triage |
| `LA:` | Live locus assessment |
| `AD:` | Human assessment disposition |
| `EB:` | Embedded disposition-evidence binding |
| `NA:` | Next scheduling action |
| `AT:` | Rival-falsifier attack target |
| `IQ:` | Critical question |
| `AIP:` | Adaptive inquiry plan |
| `IE:` | Inquiry event |

The planner also derives a nonempty, canonical `available_attack_targets` collection from the exact issue and recomputed warrant. Each `AT:` record binds one rival claim and one falsifier condition. This is a review menu: it tells the human exactly what external attacks are available, but it grants no permission to execute any of them.

## Human-triage gate

A calibration observation does not identify its own failure locus. Suppose the expected result depends on candidate adequacy (C), acceptable auxiliaries (A), an adequate test (T), and applicable scope (S). A failed expected result can criticize their conjunction, but at most licenses the inclusive alternative

\[
\neg C \lor \neg A \lor \neg T \lor \neg S.
\]

It does not say which disjunct is false, that exactly one is false, or that every proposed disjunct is genuinely defective. Several may remain live, and a single mechanism may cross loci.

The active v2 `human_failure_triage` therefore declares `overall_status: UNRESOLVED` and one or more content-addressed `locus_assessments`. Each assessment contains:

- one or more canonically ordered loci drawn from `CANDIDATE`, `AUXILIARY`, `TEST`, and `SCOPE`;
- a concrete criticism mechanism, its relevance to this exact observation, and a discriminator that could defeat it;
- one uncertainty location: `INTERNAL_DEDUCTION_OR_MODEL_FINDING`, `INTERNAL_HARNESS_SPECIFICATION`, `CR_AUTHORITY_INTERPRETATION`, `EXTERNAL_CRITICAL_INSTRUMENT`, `APPLICATION_EMPIRICAL`, or `UNLOCATED`; an `UNLOCATED` assessment may remain live but cannot be selected for action;
- a scope and canonically ordered dependencies on other assessments;
- `status: LIVE`, `epistemic_effect: CRITICISM_ONLY`, and `can_establish_unique_cause: false`.

`UNRESOLVED` is the overall condition, not a locus. A `LIVE` assessment record preserves a criticism worth discriminating, not an established defect or causal attribution. Omitting a locus leaves it unassessed; it does not exonerate it. `SCOPE` can mean either that the case may lie outside the present boundary or that the boundary itself may be defective, so its presence never vetoes simultaneous in-scope criticisms.

The immutable assessment record never changes status. Its current workflow state is derived from a separate, append-only human `assessment_disposition` chain:

| Disposition | Current-binding workflow meaning |
|---|---|
| `RETAINED` | The criticism remains live after review; it can also reopen an earlier terminal disposition. |
| `DEFEATED` | The exact criticism has been answered for the exact bindings and scope. This does not confirm the model or clear another criticism. |
| `STALE_BY_BINDING_CHANGE` | An exact input change made the criticism inapplicable in the new case. The criticism was not refuted. |

Each disposition is human-authored, content-addressed, bound to the full current inquiry inputs, repeats the assessment's exact discriminator, and embeds one or more `EB:` evidence bindings. The active contract accepts only (a) the complete calibration record whose canonical bytes reproduce the exact run binding, with its selected-value pointer exactly equal to the case's bound observation pointer, or (b) the exact old/new binding delta required for a staleness judgment. The runtime verifies native calibration shape, record identity, pointers, and digests; this closes a label-only evidence bypass. Selecting the exact bound observation anchors the evidence's provenance and the subject being reviewed. It does not authenticate the reviewer or prove that the stated human bearing on that evidence is correct. Fixed false fields mechanically preserve declarations that a disposition cannot establish a unique cause, promote the model, confirm target semantics, or be decided by search failure, source count, or provider agreement; consistency between those declarations and free-text human reasoning remains reviewable rather than machine-proved.

For example, the same labels-only contrast might criticize both the candidate's missing causal-role condition and the test's claim that every relevant feature was held fixed. The reviewer can schedule the test work first as an independent human priority. The candidate criticism stays live; going first does not make the test criticism truer.

The triage also contains one nullable `next_action`. A non-null action names one or more compatible assessments on the current dependency frontier, one route intent, an action, a reason, and one selection basis:

- `UPSTREAM_DEPENDENCY` for work that must be resolved before a dependent criticism can be tested;
- `SHARED_ACTION_FOR_MULTIPLE_LOCI` when one experiment or review discriminates several frontier assessments; or
- `INDEPENDENT_HUMAN_PRIORITY` when the human explicitly chooses among independent fronts.

The action has `epistemic_effect: SCHEDULING_ONLY` and `can_rank_semantic_truth: false`. It schedules work; it neither ranks diagnoses nor closes any selected or unselected assessment. `selection_basis` is a declared, fallible human rationale, not a machine-established graph fact. The runtime checks its arity and permits selection only from the effective-live dependency frontier; semantic claims such as whether one action genuinely serves several criticisms remain review obligations. A dependency is scheduling order, not an evidential premise: a dependent reaches the frontier only when every prerequisite has a current-binding `DEFEATED` or `STALE_BY_BINDING_CHANGE` disposition. `RETAINED`, no disposition, or an old-binding disposition leaves the prerequisite live. Selection cannot be inferred from array order, locus name, apparent plausibility, confidence, votes, source counts, or test counts. If live assessments exist but `next_action` is null, planning stops at `AWAITING_HUMAN_ACTION_SELECTION` with no generated question. If none remains live, it stops at `AWAITING_HUMAN_REASSESSMENT`, still unresolved and without a semantic verdict.

For `EXTERNAL_RESEARCH_REQUIRED`, the action must additionally bind one exact research target by issue ID and digest plus warrant ID and digest. For every other route intent, the research target is null. The selected assessments' locations must be compatible with the route intent. A dependent assessment cannot be selected while one of its live prerequisites remains behind it on the graph.

Every v2 triage also declares a `created_on` date no earlier than the bound research ledger's `created_on` date, `reviewer_kind: HUMAN`, `machine_generated: false`, `epistemic_effect: WORKFLOW_ROUTING_ONLY`, `can_promote_model: false`, and a null semantic verdict. The planner and CLI validate a supplied triage record but do not create one. These fields are workflow claims, not cryptographic authentication of a person. Human judgments remain fallible, scoped, versioned by content, and open to later criticism.

An external research target is complete only when it also names a canonical, nonempty subset of `attack_target_ids` from the current planner-derived menu. Issue and warrant identity alone do not select a question. For every non-external route, `research_target` is null.

The existence of an external issue and a mechanically generated `PROPOSED` warrant is therefore insufficient to authorize research. They express available attack options. Research begins only when a published human scheduling action selects its exact assessment and attack-target IDs.

## Append-only triage lineage

Active triage is not loaded from a free-floating pathname. It is selected by one explicit `HT:` head from the append-only publication directory. A JSON object outside that lineage remains a draft even if its schema, IDs, bindings, and prose are otherwise valid. No-triage planning is allowed only while the publication directory has neither a record nor a successor claim; once genesis exists, omitting the head is an error rather than a reset to “no triage.”

The first record has sequence one, no predecessor, `transition_kind: GENESIS`, and no dispositions. Each successor increments the sequence, names the selected parent, and must retain every predecessor assessment and disposition byte-for-byte. It may add multiple assessments, append at most one new disposition for each pre-existing assessment, or change the singular scheduling action. It cannot delete or rewrite an earlier record, and a new assessment must survive at least one published triage before it can be dispositioned.

Disposition chains are linear per assessment. Sequence numbers and predecessor IDs must extend the selected head, the assessment-origin triage and exact discriminator cannot change, and the new disposition date and bindings must equal its containing successor. A same-binding `RETAINED` or `DEFEATED` disposition of a live assessment must follow a predecessor action that selected it on the dependency frontier; a terminal assessment can only be reopened by `RETAINED`. If a disposition makes a selected assessment non-live, the same successor must clear or replace the action. A same-binding successor cannot use `STALE_BY_BINDING_CHANGE`. A changed-binding successor can append only staleness dispositions, each with the exact previous and current binding objects plus the complete canonical set of changed JSON pointers. A later `RETAINED` disposition can reopen the original assessment without rewriting it.

With unchanged inputs, the successor declares `SAME_BINDINGS`. If any case input changes, it declares `INPUT_BINDING_CHANGED`, preserves the authority identity and logical research-ledger identity, explains the change, carries every prior assessment and disposition forward, and clears `next_action`. Earlier dispositions remain history but have no operational effect under different bindings; every affected assessment is live again unless a new current-binding disposition is explicitly appended. The cleared action forces a new human scheduling choice in the new context; an old action cannot ride along with a changed run, candidate, observation, issue, warrant, or ledger snapshot.

Publication uses an ID-derived record filename and a permanent `NEXT-GENESIS.claim` or `NEXT-<parent>.claim` as a durable write-ahead reservation. The publisher fsyncs the exact claim before creating and fsyncing the final record link. If interruption leaves only that exact claim, retrying the identical successor validates the parent and candidate and rolls the reservation forward to the record. An already complete exact claim-record pair is an idempotent success; a different successor for the reserved parent is rejected as stale. Public verification remains strict: a claim-only state, record-only state, fork, orphan, extra claim or record, nonterminal head, or hand-edited content fails closed. Verification also checks canonical bytes, IDs, links, contiguous sequence, dates, complete inventory, and the explicitly selected unique terminal head. These controls make the selected repository lineage the operational record; they do not cryptographically authenticate the declared human.

Exclusive v1 triage remains intrinsically loadable as historical evidence, and v1 question/event chains remain replayable against their own immutable bindings. V1 cannot be newly published, cannot start or extend the active triage lineage, and cannot authorize a current v2 plan or event.

## Route reducer

The reducer returns exactly one route because execution needs one next work queue, not because reality has one failure locus. Diagnosis is plural; scheduling is singular. The singular action may address several compatible frontier assessments together.

| Condition | Route |
|---|---|
| No triage | `AWAITING_HUMAN_TRIAGE` |
| At least one effective-live assessment with `next_action: null` | `AWAITING_HUMAN_ACTION_SELECTION` |
| No effective-live assessment in the present set | `AWAITING_HUMAN_REASSESSMENT` |
| Selected route intent is internal harness work | `INTERNAL_HARNESS_WORK` |
| Selected route intent is internal deduction or model finding | `INTERNAL_MODEL_WORK` |
| Selected route intent is CR-1.0 interpretation | `AUTHORITY_REVIEW` |
| Selected external route is not authorized by the typed policy | `POLICY_BLOCKED` |
| A current question is marked stale | `POLICY_BLOCKED`; a changed input snapshot, explicitly rebound triage successor, and fresh action are required |
| A research entry awaits human discrimination review | `AWAITING_HUMAN_REVIEW` |
| A human-retained criticism candidate exists | `INTERNAL_INTEGRATION_REQUIRED` |
| At least one current question is proposed or active | `RESEARCH_IN_PROGRESS` |
| A valid external action selects an exact target with a rival falsifier that has no question state | `EXTERNAL_RESEARCH_REQUIRED` |
| Every current question for the action's selected targets is non-criticizing and terminal | `NO_NEW_RESEARCH_UNDER_CURRENT_PROTOCOL` |

Triage state determines the waiting routes, the selected action chooses the work class, and event state refines the external-question lifecycle. Merely recording a `SCOPE` assessment cannot return `OUT_OF_SCOPE` or suppress work on another live locus. `AUTHORITY_REVIEW` is intentionally distinct from external research: external reports cannot settle CR-1.0 interpretation. `AWAITING_HUMAN_REASSESSMENT` means only that the present criticism set has no effective-live member; it neither confirms the model nor substitutes for a separate model-level decision. `NO_NEW_RESEARCH_UNDER_CURRENT_PROTOCOL` means only that every current question generated for the action's selected targets is in `RETIRED_NONDISCRIMINATING`, `RETIRED_MISFRAMED`, or `RETIRED_OUT_OF_SCOPE`; it leaves the overall state unresolved and supplies no support to either rival. The current protocol has no operator-authored “search exhausted” transition.

When one action has several questions in different lifecycle states, the external reducer uses this precedence: stale question, then awaiting human review, then retained criticism requiring integration, then active or proposed research, then a selected target with no question, and finally the state in which every current selected-target question is non-criticizing and terminal. This ordering chooses the safest next queue; it does not rank the truth of the associated criticisms.

The reducer never consumes a confidence value, score, pass count, citation count, source count, provider vote, or consensus measure. Choosing an action changes workflow order only.

## Critical-question construction

After an exact v2 action selects `EXTERNAL_RESEARCH_REQUIRED`, the planner checks its nonempty `attack_target_ids` against the current `available_attack_targets` menu and instantiates questions only for that selected subset. Naming the issue and warrant alone does not authorize every rival falsifier. Other menu entries and external-looking assessments remain live but generate nothing until a later published action selects them.

An attack target hashes the exact issue digest, warrant digest, rival ID, rival claim, and falsifier condition. It is content-addressed rather than position-addressed, so changed attack content cannot reuse an old target merely by keeping its list position.

Each critical question additionally binds:

- the case digest;
- the exact triage ID and triage `created_on` date;
- the exact scheduling-action ID and selected locus-assessment IDs;
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

The generated query asks for a counterexample, boundary case, explicit denial, or discriminating instrument directed at one exact rival falsifier. It requires a direct primary-source locator or reproducible construction and the premise attacked. Its final instruction is that failure to find an attack leaves the question open: absence supplies no support and cannot retire the question under the current protocol.

The query also embeds the selected action text and reason plus the complete selected assessments' mechanisms, discriminators, relevance, and scopes. Thus the external task applies the actual scheduled criticisms rather than replacing them with a generic literature search. These questions are mechanically exact relative to an already structured issue. The generator does not know that the issue's rivals, falsifiers, scope, or expected discriminator are semantically correct. It does not invent a new rival, shared-premise attack, or oracle when those inputs are inadequate.

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
| `HUMAN_OUT_OF_SCOPE` | `HUMAN` | `PROPOSED`, `ACTIVE`, or `AWAITING_HUMAN_REVIEW` → `RETIRED_OUT_OF_SCOPE` for that question only; it cannot veto other live assessments or questions |
| `MODEL_CHANGED` | `MACHINE` | `PROPOSED`, `ACTIVE`, or `AWAITING_HUMAN_REVIEW` → `STALE_BY_MODEL_CHANGE` |

A research-candidate event embeds a strict v2 envelope created after the exact question exists. The envelope binds the question ID, case digest, triage ID, action ID, and attack-target ID, and then embeds one standalone immutable source-entry snapshot. This prevents unchanged replay under another question and forces any potentially reusable report through explicit rebinding and full validation; it does not establish that the report discriminates the rivals. The background ledger remains bound as the provider and epistemic policy snapshot, but the new report need not be chronologically pre-seeded into it. Its source-report `entry_id` nevertheless shares one identity namespace with entries in that bound ledger: reuse of an existing ID is accepted only for the same canonical-byte, content-identical source report, and the same ID with different content is rejected. Runtime validation applies the complete entry parser, report and envelope digests, primary-inspection requirement, event-date chronology, provider policy, contemporaneity rule, non-authority fields, and exact equality of `attacked_harness_question` and `falsifier` with the active question. Every event date must be no earlier than its question's bound triage date. An arbitrary provider result cannot be inserted directly.

Question events and assessment dispositions are separate layers. `HUMAN_CRITICISM_RETAINED` retires one question into `INTERNAL_INTEGRATION_REQUIRED`; an assessment disposition of `RETAINED` keeps or reopens that criticism. `STALE_BY_MODEL_CHANGE` closes one old question, whereas `STALE_BY_BINDING_CHANGE` is a separately evidenced human workflow judgment about an assessment. No question event automatically writes an assessment disposition.

Human event names and actor fields do not let the machine issue a human disposition. The command requires the operator to request the transition explicitly, and the runtime rejects a machine actor for every human-only transition.

Intrinsic validation treats a plan's `state_head_event_id` as a typed lineage reference, not proof that the named event exists or that its chain replays. A nonempty question state or an event-history-dependent route requires such a reference, but only contextual regeneration against the selected event directory establishes file existence, complete inventory, and replay authority.

An intrinsically valid event object or plan is therefore not publication authority. Before writing, the publisher requires an active v2 plan and regenerates it from the exact current run, research ledger, published triage head, event directory, and selected event head. It then checks the route/event allowlist, exact question membership, plan and ledger bindings, parent link, sequence, chronology, complete inventory, and replayed question state. A stale plan, loose triage, changed target, nonexistent or wrong head, legacy plan, fabricated intrinsic state, or attempted extension of a v1 chain fails before publication.

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

Verification also requires the directory's complete record inventory to equal the selected lineage, every successor claim to contain the exact canonical successor bytes, the selected head to be terminal, and every event in the lineage to use one homogeneous schema version. V1 chains remain replayable only as homogeneous history; active planning and publication require a homogeneous v2 chain.

Publishing is contextual and no-clobber. The writer first completes the active-v2 plan regeneration and authorization checks above, then validates the selected event head and writes and fsyncs a same-directory temporary file. A permanent `NEXT-<parent>.claim` hard link atomically creates a durable write-ahead reservation, which is directory-fsynced before the event's final ID-derived hard link is created and fsynced. If interruption leaves the exact claim without its record, retrying that exact event revalidates the context, parent, and successor and rolls the reservation forward. An already complete exact claim-record pair is idempotent. A different claimant for the same parent receives `INQUIRY_EVENT_STALE_HEAD`, while an orphaned or content-conflicting record fails closed. Public chain verification remains strict and rejects incomplete claim-only publication. A new v2 genesis cannot bypass existing event files, and no new event may extend a chain containing v1 events.

For the current case, every question referenced by a plan or transition must be byte-for-byte equal to a question in the exact inventory regenerated from the current run, ledger, triage, and origin head. A caller cannot forge a new current-case question merely by computing self-consistent content hashes. Historical cases remain replayable against their own immutable bindings; they are not retroactively required to occur in today's inventory.

This mechanism is tamper-evident relative to a preserved head and files. It is not an external timestamp, signature, or protection against an actor replacing the entire event directory and every recorded head. A continuation-grade handover or repository commit must pin the selected head when a real chain exists.

## Strictly non-inductivist behavior

The protocol distinguishes the existence of one concrete criticism candidate from its frequency. A concrete report changes the workflow from active research to human review because it supplies inspectable attack content. A second or hundredth agreeing report cannot promote the question beyond `AWAITING_HUMAN_REVIEW`, cannot change the model, and cannot create a semantic verdict.

Likewise:

- a passed test leaves the tested conjunction unrefuted by that test;
- a failed test initially criticizes the conjunction of candidate, auxiliaries, fixture, oracle, scope, and interpretation; several locus criticisms may remain live together;
- recording or selecting one locus criticism does not confirm it as the cause and does not exonerate any other locus;
- `next_action` orders work only; it does not increase confidence in a selected assessment or decrease confidence in an unselected one;
- provider ranking may affect discovery order but has no epistemic effect;
- AlphaXiv output is a discovery route, not a primary source or oracle;
- source frequency and citation count are neither accepted question fields nor reducer inputs;
- human retention produces a criticism candidate for internal integration, not automatic rejection or repair;
- failure to find an attack cannot retire a question or support a rival; and
- neither a plan nor an event can emit a positive semantic status.

## Live v2 no-triage result

On 2026-09-03 the additive planner was run against the current canonical calibration record and research ledger:

```bash
PYTHONPATH=src python tools/run_semantic_inquiry.py plan \
  --run-record forge/runs/SMF-CALIBRATION-CR-1-0-001.4219efce.json \
  --research-ledger forge/research/SMF-RESEARCH-2026-09-03.json \
  --triage-dir forge/triage
```

The command completed successfully and emitted exact run, model, observation, issue, warrant, and research-ledger bindings. Its operative result was:

```text
route:                AWAITING_HUMAN_TRIAGE
route_reason:         A mechanical observation cannot locate its own failure locus.
triage:               null
live_locus_assessment_ids: []
selected_action_id:   null
state_head_triage_id: null
proposed_questions:   []
question_state:       {}
state_head_event_id:  null
semantic_verdict:     null
epistemic_status:     UNRESOLVED
```

No persistent triage or event was created. The attack-target menu records what could be selected later; its presence does not change the route or authorize a question. Without genuine published human triage there is no selected scheduling action and no authorized question to propose, activate, research, or retire.

The canonical active v2 no-triage output is preserved as `forge/plans/SMF-AIP-1210e0fa.no-triage.json` with plan ID `AIP:1210e0fa967f4e044f8c0129b9ec650abd61dc8a17b88bfdbb18525e0deea94d` and file SHA-256 `78f0c19d7fa609015a4ec6c610588d58460e77bcbba68778c1fd3f1b3bd38b8d`. It contains four exact menu targets and zero authorized questions. The former v1 and superseded v2 no-triage plans remain in invalidated-plan history with their original bytes and identities.

## CLI surface

`plan` produces a deterministic routing record from a current calibration, research ledger, the append-only triage directory, an optional explicit published triage head, and an optional explicit event head. `--triage-dir` defaults to `forge/triage`. Omitting `--head-triage-id` is valid only while that lineage is empty. A selected head with assessments but no `next_action` stops at `AWAITING_HUMAN_ACTION_SELECTION`; the planner does not choose which criticism to pursue.

```sh
PYTHONPATH=src python tools/run_semantic_inquiry.py plan \
  --run-record forge/runs/SMF-CALIBRATION-CR-1-0-001.4219efce.json \
  --research-ledger forge/research/SMF-RESEARCH-2026-09-03.json \
  --triage-dir forge/triage
```

`publish-triage` accepts a human-authored v2 draft, derives the current exact bindings and attack-target menu independently, checks genesis or successor rules against the caller's expected head, and publishes atomically without overwrite. For the first record, omit `--expected-head-triage-id`; for a successor, name the currently selected terminal head.

```sh
PYTHONPATH=src python tools/run_semantic_inquiry.py publish-triage \
  --run-record forge/runs/SMF-CALIBRATION-CR-1-0-001.4219efce.json \
  --research-ledger forge/research/SMF-RESEARCH-2026-09-03.json \
  --triage-dir forge/triage \
  --triage /path/to/human-triage-v2.json
```

`append` selects a content-addressed question from an exact plan, replays the selected event head, constructs one permitted transition, and publishes it without overwrite. It contextually regenerates the active v2 plan from the exact current run, ledger, published triage head, and origin event head, so intrinsic record validity or a self-rehashed stale plan cannot authorize a transition. Non-proposal transitions must name a question already present in the current plan state. The CLI applies an explicit route/event allowlist: a route can authorize only lifecycle events appropriate to that route, while `POLICY_BLOCKED` and `INTERNAL_INTEGRATION_REQUIRED` authorize no continued research. The caller must supply the actor kind, date, reason, and event type. A research-candidate transition also requires an exact v2 envelope containing the active question binding and its standalone source-report snapshot. `--triage-dir` defaults to `forge/triage`; the plan itself supplies the exact selected triage head.

`verify` replays one explicitly selected event head and reports only `INTRINSIC_CHAIN_INTEGRITY_VALID`, event count, and question states. Its epistemic effect is `INTEGRITY_REPLAY_ONLY`. This read path can preserve v1 history; successful replay does not authorize extending it.

## Current limitations

SMF-0.3 is a complete protocol slice for the first role-projection calibration, not a general semantic-model research agent.

1. The adapter is fixed to the weak typed-role projection and one observation pointer. It does not yet consume arbitrary challenge families, model deltas, hardening assessments, or full CR-1.0 model-class searches.
2. It cannot determine the semantic failure loci. Human assessments are mandatory; they remain criticisms rather than established causes, and the implementation does not authenticate the human cryptographically.
3. The attack-target menu and question generator expand already declared rival falsifiers. They cannot determine that those are the right or complete attacks, or invent a missing shared-premise attack.
4. An event-time report is preserved inside a question-bound event envelope. The protocol does not yet maintain a separate evolving catalog of those snapshots or import them into the background research ledger.
5. A changed run, model, observation, issue, warrant, locus assessment, dependency, scheduling action, or ledger produces a new case binding. The protocol does not silently migrate prior question dispositions into that case.
6. A stale question blocks the current case; it does not automatically create or approve a replacement.
7. Search protocols retain a human-readable stop condition, but the current protocol cannot authenticate or prove exhaustive execution. It therefore provides no `PROTOCOL_EXHAUSTED` event; a null search result leaves the active question open.
8. Event and triage claims prevent two published successors from the same selected parent in one directory, and complete-inventory verification exposes local forks and orphans. External preservation of the chosen head and repository tree remains necessary for durable tamper evidence.
9. Assessment dispositions currently accept only the exact bound calibration record, selected at the case's exact bound observation pointer, or an exact binding-change delta. This anchors evidence provenance and the subject of review and prevents arbitrary evidence labels, but it means a new source report, authority interpretation, proof, model, or application observation must first be incorporated into a new typed calibration/input contract before it can terminally disposition an assessment. The runtime preserves the selected bytes and stated human bearing but cannot authenticate the reviewer or prove that the bearing is sound. Model-level authorization is outside this v2 inquiry lineage. SMF-0.4 now provides separate translation-review and hardening-decision contracts, but their decisions are not inferred from, or written back into, v2 assessment dispositions; a present inquiry set with no effective-live assessment cannot supply them.
10. No v2 inquiry decision can authorize `HARDENING_UNREFUTED` or `PROVISIONALLY_READY`. The separate SMF-0.4 hardening contract reserves the first label for an explicitly finite, exhaustively replayed, fully witnessed comparison with all scoped human requirements resolved, but its v1 runtime lacks the artifact resolver and model executor needed to reach it. Inquiry scheduling supplies none of that evidence and cannot authorize `PROVISIONALLY_READY`. The legacy readiness path remains fail-closed.

The next authorized semantic action is therefore to author and publish a v2 genesis triage for the exact role-relabel criticism candidate, then select its returned terminal head when planning. It may retain candidate, auxiliary, test, and scope assessments together. A separate nullable `next_action` says which dependency-frontier work to do first; it may target several compatible assessments but leaves all others live. Until an external action selects exact attack-target IDs from the non-authorizing menu, “do more research” is not a justified machine conclusion.
