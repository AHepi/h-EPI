# Semantic Model Forge 0.1 architecture

## Status

`SMF-0.1` is a proposed engineering architecture for iteratively developing a sufficiently specified semantic model class and then extracting mathematics from it. It is not a semantic amendment, a new epistemological authority, or evidence that CR-1.0 is correct. Every output remains fallible and conjectural. An explicit human disposition can authorize scoped use; it cannot confer certainty.

The forge is problem-led rather than evidence-led. It begins with a witnessed defect, ambiguity, unexplained distinction, false positive, false negative, or failed derivation. It does not collect observations and then infer a model from their repetition. Research, examples, tests, formal solvers, and language models are instruments for exposing error in stated conjectures.

## Authority boundary

The sole semantic and formal authority for this work remains `Creativity as Explanatory Self-Correction`, Model CR-1.0, identified by SHA-256 `08ff81e848fea976b558345402d85723173be8f40f1041fb00d6267f1e026b8b`. Its active formal span is physical PDF pages 219–234, printed folios 218–233. The repository records this identity in `authority/source_manifest.json` and in the frozen bootstrap manifest.

SMF may inspect, test, criticize, interpret, or propose a successor to CR-1.0. It may not silently repair CR-1.0, add a premise to it, promote an interpretation into it, or report a forge result as something CR-1.0 already says. Any successor model is a separately identified candidate until a human explicitly designates it otherwise. The original authority bytes and all prior candidate versions remain unchanged.

External literature has only two permitted roles. A primary source may expose a conflict or ambiguity in a proposed reading of CR-1.0, and engineering literature may suggest an instrument for finding or recording defects. Neither role grants external literature authority to define the target semantics. Frequency of citations, source consensus, retrieval rank, model agreement, and test survival confer no semantic entitlement.

## Governing epistemic constraint

The forge operationalizes the following asymmetry:

\[
\text{problem} \longrightarrow \text{conjecture} \longrightarrow
\text{criticism/test} \longrightarrow \text{new problem situation}.
\]

The first arrow is not a truth-preserving inference. A test is discriminating only relative to rival conjectures, a stated interpretation, auxiliary assumptions, and an expected difference. An observation never interprets itself. A passed test removes or weakens a particular criticism under the current test construction; it does not confirm the candidate, increase its probability of truth, or close inquiry.

Criticism is always criticism of an already recorded conjecture, interpretation, import, test, or formal claim. The controller rejects an unattached `CriticismRecord`; it does not let criticism manufacture its target retrospectively.

The following transitions are therefore illegal in SMF: repeated examples to a universal semantic rule; corpus frequency to intended meaning; model consensus to acceptance; predictive success to explanation; test count to confidence in truth; score threshold to closure; and formal satisfiability to semantic adequacy. Statistical techniques may be used inside search, retrieval, clustering, or an explicitly statistical object model, but their outputs remain candidate material for criticism.

## Two distinct objects of criticism

SMF keeps the semantic model and the forge mechanism separate. A semantic iteration changes a candidate account of problems, conjectures, criticism, explanatory content, authorship, knowledge, realization, or another target distinction. A forge iteration changes an engineering instrument such as a prompt, counterexample generator, minimizer, retrieval strategy, or test constructor. A successful forge experiment does not establish a semantic claim, and a semantic repair does not validate the instrument that happened to propose it.

Both kinds of change are versioned. Neither kind may mutate the protected authority boundary. A forge change is evaluated against fixed replay material for that experiment, while any newly exposed failure is retained as a candidate regression case. Only the human reviewer may accept the change, revise its intended scope, or suspend judgment.

## Architectural components

| Component | Responsibility | Prohibited authority |
|---|---|---|
| Authority store | Resolve the pinned CR-1.0 identity, locators, source marks, active namespace, and immutable excerpts used in a run. | Cannot amend, paraphrase into authority, or fill an omission. |
| Problem registrar | Open a precise defect record and bind it to a witnessed case, candidate version, and affected distinctions. | Cannot infer a problem merely from low scores or disagreement. |
| Conjecture workbench | Hold one or more explicit rival interpretations, model fragments, repair proposals, or mathematical encodings. | Cannot mark its own proposal accepted. |
| Research broker | Turn a live defect into discriminating, falsifier-first source questions and preserve complete retrieval provenance. | Cannot search for confirmation or aggregate sources into semantic confidence. |
| Claim classifier | Keep source claims, interpretations, project imports, and formal consequences in separate namespaces. | Cannot promote records across namespaces automatically. |
| Adversary | Propose counterexamples, unintended models, omitted intended cases, causal reversals, and near-neighbour cases. | Cannot decide that its generated case is coherent or relevant. |
| Test synthesizer | Produce dynamic competency questions, minimal pairs, countermodels, and metamorphic relations from the current distinction graph. | Cannot make a generated expected result authoritative. |
| Executor | Replay machine-checkable tests, compare artifacts, run solvers or proof kernels, and emit exact traces. | Cannot interpret a semantic outcome or turn a check into acceptance. |
| Counterexample triage | Determine whether a proposed failure attacks the candidate, an auxiliary, a test construction, a source reading, or nothing coherent. | Machine triage may recommend; final semantic triage belongs to the human reviewer. |
| Formal extractor | Propose signatures, definitions, axioms, bridges, countermodels, and theorem statements from a reviewed semantic slice. | Cannot create missing semantics by notation or choose among unresolved readings. |
| Human semantic oracle | Give scoped dispositions on meaning, intended cases, source readings, imports, test expectations, and candidate revisions. | Is a workflow authority, not an infallible epistemic source; every decision remains revisable and attributable. |
| Append-only ledger | Bind every artifact, dependency, result, decision, and supersession by identity. | Cannot erase an adverse result or rewrite a prior decision in place. |

The controller is deliberately thin. It validates state transitions, schedules independent advisory roles, freezes run inputs, and writes artifacts. It contains no semantic scoring function and no rule that treats majority agreement as acceptance.

### Research-provider policy

Contemporary research and discovery use AlphaXiv as the default channel. Consensus is an optional independent cross-check when it can materially test a retrieval, metadata, or interpretation question; it is not a co-equal mandatory source and its absence does not block a run. Any report retained in research-ledger v2 requires inspection of the exact primary-source version; direct primary discovery may bypass AlphaXiv without changing the epistemic boundary.

Both services are replaceable provider adapters. Provider responses, summaries, relevance rankings, and generated explanations are advisory records only. No provider belongs to the semantic authority boundary, and no provider-specific field may be required by the core `ResearchQuestionRecord`, `EvidenceRecord`, or claim schema. Replacing a provider must change provenance and replay identity without changing claim kind or adjudication authority.

## Typed claim separation

Every retained proposition that purports to bear on the candidate semantics, its source entitlement, or its formal consequences has exactly one claim kind. Operational fields such as identifiers, timestamps, queries, observed tool output, and workflow status are not thereby semantic claims. Claim-bearing prose in any record must either carry a claim kind itself or reference a separately typed claim record. Seed annotation titles and boundary notes are expressly marked `annotation_prose_status: unreviewed_non_authoritative` and `annotation_prose_semantic_effect: none`; changing that editorial prose cannot change any typed mechanical conclusion. A record may depend on records of other kinds, but a proposition cannot inhabit more than one kind or cross a boundary without an explicit bridge record.

| Claim kind | Meaning | Minimum provenance | What it cannot establish |
|---|---|---|---|
| `SOURCE_AUTHORITY` | A bounded report of what CR-1.0 states, argues, qualifies, or leaves open. CR-1.0's own `X`, `R`, `M`, `Q`, and `O` marks are preserved rather than normalized away. | Authority digest, exact locator, bounded quotation or faithful paraphrase, source mark, reviewer status. | That the claim is true, complete, mathematically adequate, or endorsed as a new project premise. |
| `EXTERNAL_SOURCE_REPORT` | A bounded report of what a non-CR source states, including primary Popper or Deutsch texts and engineering literature. | Work identity, edition or version, exact locator, bounded quotation or faithful paraphrase, retrieval provenance, reviewer status. | CR-1.0 source entitlement, semantic adoption, truth, or authority over the target model. |
| `SOURCE_INTERPRETATION` | A proposed reading that makes a source passage or relation more determinate. | Typed source reports interpreted, alternatives considered, ambiguity, discriminating consequences, author, version. | That CR-1.0 explicitly contains the reading or that an external source governs the model. |
| `PROJECT_IMPORT` | An additional semantic, causal, epistemic, methodological, or physical premise adopted for a candidate model. | Motivation, independence statement, necessity claim, alternatives, tests, human disposition. | Source entitlement or derivability from definitions. |
| `FORMAL_CONSEQUENCE` | A theorem, countermodel, satisfiability result, or other consequence relative to named formal premises and bridges. | Exact formal artifact, transitive dependencies, toolchain identity, result trace, scope. | Faithfulness of the formalization, truth of its premises, physical realization, or source authorship. |

No language model, parser, proof assistant, vote, or passing test can change a claim kind. If one sentence mixes kinds, it is split. If it cannot be split without changing its meaning, it is rejected as an ill-typed claim.

## Core records

| Record | Required content |
|---|---|
| `ProblemRecord` | Stable identifier; triggering contradiction, ambiguity, false classification, failed theorem, or missing distinction; affected candidate; consequence if unresolved; current status. |
| `ConjectureRecord` | Exact candidate content; claim kind; intended scope; dependencies; competitors; author or generating system; creation time; artifact digest. |
| `ResearchQuestionRecord` | Live problem and typed premise references; rival answers; expected discriminator; possible answer classes; what would criticize each rival; admissible source scope; stop condition; query variants; `PROPOSED` status. |
| `EvidenceRecord` | Exact source identity and locator; bounded extract or paraphrase typed as `SOURCE_AUTHORITY` or `EXTERNAL_SOURCE_REPORT`; retrieval route; context; source status; candidate implications kept as separate typed conjectures; unresolved interpretation. |
| `CriticismRecord` | Targeted typed conjecture; separately typed alleged defect; witness; relevant distinction; dependencies; proposer; triage and human disposition. |
| `TestRecord` | Test family; source problem; candidate distinction; fixtures or transformations; `PROJECT_IMPORT` construction kind; separate typed basis for the expected preservation or reversal; oracle owner and adjudication state; applicability conditions; version. |
| `ResultRecord` | Frozen run identity; observed output; mechanical verdicts; semantic verdict if supplied by the human; artifacts; exceptions; links to resulting criticisms. |
| `RevisionRecord` | Prior and proposed candidate digests; criticism addressed; exact semantic and formal delta; imports added or removed; tests added, changed, retired, passed, and failed. |
| `DecisionRecord` | Human actor; object decided; disposition; reasons; scope; timestamp; superseded decision if any; unresolved consequences. |
| `FormalModuleRecord` | Signature, definitions, independent premises, bridge declarations, theorems, countermodels, proof status, semantic-review status, and transitive dependency closure. |

Every record is append-only. Corrections supersede rather than overwrite. Human prose is retained alongside normalized fields because mechanically invalid or incomplete prose may still carry the operative semantic distinction.

## Problem-led research protocol

A research run is inadmissible without a live `ProblemRecord`. The broker first conjectures a `ResearchQuestionRecord`; this question is itself open to criticism. The question must identify at least two answers or readings whose consequences for the model differ. It must state what possible finding would count against each rival. A question to which every possible answer leaves the same candidate models admissible is non-discriminating and should be revised or suspended.

The calibration router consumes an issue whose `internal` or `external` classification is supplied as a project-import input subject to human review. It can refuse a warrant for the former and propose a bounded warrant for the latter, but it does not infer from raw failures whether research is needed. The additive Adaptive Inquiry Protocol improves that boundary without pretending to solve it: it binds an exact failed observation, candidate, issue, warrant, evaluator, fixture, run, and research ledger; requires a separately supplied human failure triage; and then reduces the declared disposition and uncertainty location to a workflow route. With no triage it stops at `AWAITING_HUMAN_TRIAGE`, emits no question, and leaves the semantic verdict null. It cannot infer the failure locus or the truth of an `internal`/`external` classification.

In the target architecture, the broker generates disconfirming searches before any background expansion. Search formulations target contrary passages, changed positions, boundary cases, explicit denials, counterexamples, and alternative terminology. A neutral source search may follow to locate the primary text. The target broker rejects a request such as “find support for definition D”; an admissible replacement asks whether the source excludes a case admitted by D, admits a case excluded by D, or distinguishes terms that D collapses. SMF-0.1 does not yet semantically inspect and reject arbitrary support-seeking issue prose; it only constructs falsifier-first queries from a supplied, structurally eligible issue.

Retrieved material does not flow directly into a model. It first becomes an `EvidenceRecord`, then one or more `SOURCE_AUTHORITY` or `EXTERNAL_SOURCE_REPORT` claims, then competing `SOURCE_INTERPRETATION` records if interpretation is needed. Any source-to-model crossing is represented as an explicit source interpretation or project import. Source quantity is never accumulated into a confidence score.

In the target architecture, a human-adjudicated research episode may end when the declared source scope has been inspected, the discriminator has been answered as far as the material permits, or the question is shown to be non-discriminating. `NO_DECISIVE_SOURCE`, `AMBIGUOUS`, and `QUESTION_DEFECTIVE` are ordinary target outcomes, and none triggers an automatic repair. Protocol v1 cannot authenticate exhaustive scope inspection, so an unsuccessful search remains active rather than manufacturing any such outcome.

## Dynamic semantic tests

In the target architecture, the suite is generated from the current problem and distinction graph rather than treated as a fixed constitutional checklist. Tests remain conjectures about what would discriminate the intended class. A human may revise or retire a test, but only through a reasoned, append-only decision that preserves its earlier results. SMF-0.1 implements a seed attack vocabulary, deterministic calibration selection, and content-addressed critical questions constructed from the exact falsifier conditions of a human-triaged external issue. General issue discovery, arbitrary model-delta synthesis, and semantic evaluation of generated questions remain future work.

### Competency questions

Each material term or relation receives questions about identity, scope, required relata, admissible variation, causal role, positive cases, near misses, counterexamples, and consequences. Questions are typed by purpose so that a scoping question cannot silently become a validation result and a formal query cannot decide a source interpretation. A competency question is useful only when rival candidate models answer differently or when failure exposes a missing representation.

### Minimal pairs

A minimal-pair test contains two explicitly modeled cases intended to differ in one semantic feature. The record states the held-fixed conditions, the changed feature, the expected classification relation, and why CR-1.0 or an accepted interpretation makes the difference material. If the formal class gives the same result for a pair that the human judges different, the class is under-discriminating. If it separates a pair the human judges equivalent, it is over-discriminating. If the pair cannot hold the other features fixed, the test is defective rather than evidence against the candidate.

Pairs are constructed dynamically around each new primitive, definition, bridge, or claimed theorem. Particularly important contrasts include conjecture versus deduction, criticism versus negative feedback, explanation versus prediction, authorship versus surface emission, retention versus knowledge, semantic content versus physical information, finite success versus disposition, and abstract consistency versus physical possibility.

### Metamorphic relations

A metamorphic test declares a transformation and the semantic relation expected between the original and transformed case. Meaning-preserving recoding, paraphrase, token renaming, and implementation substitution should preserve classifications only where the candidate claims substrate or encoding independence. Provenance reversal, external-selector substitution, deletion of reason-specific uptake, conjecture/criticism order reversal, and silent standard replacement should change classifications only where the relevant definition makes that feature necessary.

The relation is always local and conditional. There is no general rule that paraphrase preserves all content or that every implementation substitution is irrelevant. A violated relation generates a criticism; it does not identify whether the candidate, fixture, transformation, or expected relation is at fault.

### Formal countermodels and deletion tests

A claimed entailment is attacked by searching for a fully typed model satisfying the stated premises and falsifying the conclusion. A proposed definition or import is also subjected to deletion, renaming, role-swapping, and independence tests. If removing a clause changes no accepted classification, dependency, countermodel, or theorem, the clause has no demonstrated work. If a conclusion survives after an allegedly necessary import is removed, the necessity claim is criticized. These tests do not prove dispensability in every future extension; they expose the current absence of work.

## Counterexample triage

Generated counterexamples are not presumed valid. Every proposed counterexample receives one of the following human-reviewable diagnoses.

| Diagnosis | Meaning | Permitted next move |
|---|---|---|
| `CANDIDATE_DEFECT` | The case is coherent, falls within declared scope, and the candidate misclassifies it for the alleged reason. | Open a repair problem and preserve the case as a regression candidate. |
| `AUXILIARY_DEFECT` | The failure depends on a disputable fixture, boundary, source reading, or bridge rather than the targeted semantic clause. | Open the auxiliary as the new problem; do not patch the target automatically. |
| `TEST_DEFECT` | The pair, transformation, expected relation, or held-fixed conditions are incoherent or non-discriminating. | Revise or retire the test with reasons. |
| `OUT_OF_SCOPE` | The case is coherent but outside the declared model scope. | Preserve the boundary finding and check whether the scope itself is criticized. |
| `UNRESOLVED` | More than one diagnosis remains live. | Suspend; no repair or closure follows. |

This triage blocks definition growth driven by spurious or ill-posed counterexamples.

## Semantic ratchet

SMF has no scalar quality, confidence, coverage, or progress score. Semantically unlike losses cannot be compensated by weighted gains, and a threshold cannot turn fallible survival into acceptance. The comparison between candidate versions is a structured delta containing the criticisms addressed, criticisms left open, intended cases preserved or lost, counterfeit cases excluded or newly admitted, distinctions added or collapsed, imports added or removed, source mappings changed, formal consequences changed, and unresolved decisions created.

The delta tracks two independent strength axes. *Old-language model restriction* asks whether existential erasure of new vocabulary leaves a proper subset of the prior models. *Role-expansion narrowing* asks whether, over a preserved old or target-neutral history, the revision removes a witnessed rival semantic-role expansion, potentially leaving a unique expansion. A unique role expansion can harden an ambiguity without excluding any old history; excluding an old model can leave every surviving history role-ambiguous. Each claimed gain must therefore name its axis and witness rather than collapsing both into “stronger.”

A revision may advance the semantic ratchet only when a human accepts that it addresses the named criticism without hiding an unaccepted loss. Every claimed old-model exclusion or role-expansion narrowing must cite a typed, digest-bound witness record, every preservation claim must cite a typed, digest-bound review record, and a `HARDENING_UNREFUTED` result must cite the human decision that licenses the scoped comparison. The checked successor must also be consistent and non-vacuous, satisfy old-result non-broadening over the declared old-result signature and global role-assignment non-broadening over every declared control reduct, retain a nonempty registered intended-base family, and compare exact localized role fibers over immutable common-language transports. These requirements are conjunctive and non-compensatory on either strength axis: no gain witness offsets a missing preservation review, and no number of preserved cases offsets one registered loss. Missing references leave the comparison `UNRESOLVED`. Earlier accepted distinctions and adverse cases are replayed, but they are not immutable axioms: the reviewer may revise them by recording why the earlier judgment was mistaken and what downstream artifacts must be reconsidered. This makes the ratchet historical and defeasible rather than a one-way accumulation of clauses.

The current promotion fails closed because SMF-0.1 lacks both schema support for the full mathematical obligations and a resolver for typed, digest-bound gain-witness, preservation-review, and human-decision records. It cannot emit `HARDENING_UNREFUTED` even when plain reference strings are supplied or a mechanical countermodel or uniqueness check succeeds. A future promotion remains blocked until schema evolution, ledger-backed resolution, and every conjunctive gain, non-vacuity, non-broadening, exact-fiber, intended-model, and preservation obligation are discharged.

Definition length, number of conjuncts, number of tests passed, number of sources, model agreement, and theorem count are reported only as raw diagnostics. They are never proxies for semantic improvement. A local exception added only to silence one case is flagged as possible ad hoc repair. A wider repair must display what common defect mechanism it removes and which other distinctions it affects.

The possible dispositions are `ACCEPT_SCOPED_REVISION`, `REJECT_REVISION`, `RETAIN_CURRENTLY_UNREFUTED`, `SUSPEND_JUDGMENT`, and `REFRAME_PROBLEM`. Only the human semantic oracle may assign them. `RETAIN_CURRENTLY_UNREFUTED` records the absence of a presently accepted defeating criticism; it is not confirmation. No disposition marks a model finally true or immune from future criticism.

## LLM boundary

Language models may draft rival definitions, propose counterexamples, generate minimal-pair variants, compose falsifier-first queries, extract candidate passages, identify dependency gaps, minimize witnesses, translate reviewed clauses into candidate formalisms, and criticize other model outputs. Every such artifact is marked `PROPOSED` with model, provider, prompt, context, parameters, and run identity where available.

Language models may not adjudicate source meaning, set the expected semantic label of a test, declare a counterexample valid, accept an import, assign final causal authorship, promote a formalization as faithful, close a problem, or change the authority boundary. Using several models creates several fallible conjecturers and critics, not a vote. Agreement is a search signal only; disagreement opens a problem rather than resolving one.

An LLM judge may be used for inexpensive triage only if its output is clearly advisory and sampled items reach human review. Its accept/reject token never enters the semantic ratchet as a decision.

Research providers obey the same boundary. AlphaXiv is the default contemporary discovery channel and Consensus may independently cross-check selected questions, but neither is an oracle. Both are modular adapters whose outputs must be traced to inspected primary material before a source claim is retained.

## Human semantic oracle

“Oracle” names a role in the engineering workflow, not an infallible person or source of justified certainty. The human reviewer owns decisions that require understanding what a source passage means, why a distinction matters, whether a case is intended, whether a criticism bears on the stated problem, and whether a new import is indispensable. The reviewer may accept, reject, reframe, or suspend, and may later criticize any prior decision.

The harness must always present the exact candidate, its alternatives, the strongest outstanding criticism, the semantic delta, affected tests, source locators, and formal consequences before requesting a disposition. It must permit free prose alongside any structured choice. Silence, timeout, model consensus, test success, or resource exhaustion leaves the mechanical run at `AWAITING_HUMAN`; it never fabricates the human disposition `SUSPEND_JUDGMENT` and never implies acceptance.

## Mathematical extraction

Formalization begins from a bounded semantic slice with explicit human dispositions; it does not begin from an attractive notation. A readiness check defaults to `BLOCKED` when no explicit semantic-review record is supplied, even if the caller lists no known blockers. `PROVISIONALLY_READY` also fails closed in SMF-0.1 because the current schema and runtime cannot represent or resolve all typed, digest-bound review records and mathematical obligations; neither an empty blocker list nor plain reference strings can authorize it. A future promotion remains blocked until schema evolution and ledger-backed resolution cover source mapping, project imports, dependency closure, successor non-vacuity, global non-broadening, exact role fibers, intended-model coverage, witnesses, preservation, review, and human decisions. The extractor first declares types and identity conditions, then primitive semantic relations, then independent project imports, then eliminable definitions, then bridge conditions, and only then theorem candidates. Every theorem receives a transitive dependency closure and is attacked with a typed countermodel before proof effort is interpreted as informative.

Machine checking answers questions such as whether a candidate is well typed, satisfiable, conservative under a stated expansion criterion, internally derivable, or refutable by a model. It cannot answer whether `Explains`, `Authors`, `UsesReason`, `K_E`, or another substantive relation has been interpreted faithfully. A theorem produced from an import is a conditional consequence of that import, not independent support for it.

Where the semantic model remains underdetermined, the extractor emits rival modules or an opaque interface with an explicit open obligation. It may not choose whichever reading makes a theorem provable. Failure to find an adequate invariant is recorded as a live mathematical problem; the semantics are not weakened merely to obtain closure.

## Iteration protocol

Each forge iteration freezes an authority digest, candidate digest, live problem, rival conjectures, research scope, test versions, tool versions, model configurations, prompts, and supplied human decisions. It executes applicable mechanical checks, presents semantic cases for human triage, and conditionally routes bounded research or adversarial generation only when the corresponding gate is discharged. It then produces a version-to-version delta. The iteration ends only in a human disposition or an explicit unresolved suspension.

The next iteration begins from the new problem situation, not from a numerical reward. One semantic mechanism should change at a time where separability is possible. Where several clauses share one defect mechanism and must change together, the revision records that coupling and provides deletion tests for each part.

Old failures are replayed against later candidates. A later finding that an old test was defective does not erase the failure; it appends a new test disposition and identifies which past comparisons are no longer licensed. This preserves learning without turning the test corpus into unquestionable authority.

## Harness self-improvement

Every forge component, prompt, schema, selection heuristic, and stopping rule is itself a replaceable versioned conjecture. A proposed harness change identifies the operational defect it addresses, the fixed replay set, the expected observable difference, and possible adverse effects. The change is run alongside the prior mechanism where practical. The resulting delta is reported without a scalar winner.

Self-improvement cannot change the CR-1.0 digest, claim-kind boundary, human-only dispositions, append-only history, or no-automatic-closure rule. Changing one of those is a new architecture proposal requiring explicit human authorization outside an ordinary run.

## Run status and stopping

SMF distinguishes mechanical completion from epistemic disposition.

| Status | Meaning |
|---|---|
| `RUN_COMPLETE` | Scheduled tools returned and required artifacts were recorded. |
| `MECHANICALLY_VALID` | Named syntax, type, proof, or replay checks passed relative to frozen inputs. |
| `CURRENTLY_UNREFUTED` | No criticism accepted in this run defeats the scoped candidate. |
| `CRITICIZED` | At least one human-accepted criticism bears on the scoped candidate or an indispensable auxiliary. |
| `UNRESOLVED` | Rival diagnoses or readings remain live, or the relevant source/test is insufficient; this is a run condition, not a human disposition. |
| `AWAITING_HUMAN` | A semantic disposition is required. |

No combination of mechanical statuses produces semantic closure. There is no automatic `CONFIRMED`, `PROVED_SEMANTICS`, or `FINAL` state. A completed run can end with an unresolved model; this is a valid and expected result.

## SMF-0.1 implementation boundary

The first implementation provides immutable authority resolution, strict issue, rival, warrant, challenge, hardening, and readiness records, fourteen seed challenge constructors, an open defect-family key for newly constructed challenges, and one deterministic calibration run. It also provides a digest-bound external-research ledger and an additive inquiry protocol with exact human-triage records, content-addressed falsifier questions, a fail-closed route reducer, and append-only no-clobber question events. The seed constructors are an attack vocabulary, not a complete or constitutional checklist. General issue/model-delta synthesis and ledger-backed human semantic-decision resolution remain subsequent implementation work. The implementation uses CR-1.0's existing source and dependency records rather than inventing a parallel authority map.

SMF-0.1 is successful as an engineering artifact if it can mechanically reproduce the declared fixture equalities and erasure invariance, propose the corresponding conditional criticisms without adjudicating them, keep internal work out of external research, construct a falsifier-first AlphaXiv warrant only for a decision-relevant external issue, preserve the source/report/interpretation/import/consequence boundary, and terminate awaiting a human decision. Its adaptive layer must additionally refuse to invent triage, bind every proposed question to the exact criticism candidate, and treat research as criticism-generating workflow input only. That success shows that the forge executes its declared discipline. It does not establish that the fixture is an in-scope defect, that a supplied classification is correct, that the proposed oracle is correct, that full CR-1.0 admits the same countermodel, or that any repaired semantic model is adequate.

The engineering research behind these choices is recorded in [SMF-0.1 Research Basis](./SMF-0.1_Research_Basis.md). The implemented post-failure routing boundary is specified in [SMF-0.3 Adaptive Inquiry Protocol](./SMF-0.3_Adaptive_Inquiry_Protocol.md).
