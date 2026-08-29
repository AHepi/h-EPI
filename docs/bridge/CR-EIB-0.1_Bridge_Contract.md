# CR-EIB-0.1 — Fidelity-Graded Executable Interpretation Bridge

Status: Draft 0.1  
Date: 2026-08-29  
Semantic authority: Creativity_Semantic_Model_CR-1.0(1).pdf  
Authority SHA-256: 08ff81e848fea976b558345402d85723173be8f40f1041fb00d6267f1e026b8b  
Active authority span: physical PDF pages 219–234, printed folios 218–233  
Bridge status: non-authoritative, versioned interpretation layer  
Bridge conformance: BLOCKED pending per-declaration dispositions and typed bodies  
Target proof kernel: Lean 4  
Target search interchange: SMT-LIB 2.7  

## 1. Decision

CR-EIB-0.1 is the bridge between the authoritative PDF and executable machinery.
It is not a revision of CR-1.0 and does not silently complete the PDF. The PDF
remains the sole semantic and formal authority. Every executable choice introduced
here is an independently versioned interpretation that can be accepted, rejected,
or replaced without changing the source.

The bridge makes the active model representable and checkable by combining four
layers.

| Layer | Function | Authority |
|---|---|---|
| Authority ledger | Preserves source bytes, spans, identifiers, marks, and hashes | PDF only |
| Typed interpretation | Adds explicit sorts, binders, signatures, contexts, and named opaque ports | CR-EIB only |
| Automation | Parses, elaborates, generates obligations, searches for models, and proposes proofs | Untrusted |
| Independent checking | Replays proof terms, certificates, and concrete witnesses against the typed interpretation | Kernel-checked |

The bridge gate is distinct from the existing CR-1.0 bootstrap gate. The source
bootstrap remains FAIL because the PDF itself is not a closed typed calculus.
CR-EIB may pass its own conformance gate when every interpretive addition is
explicit, source-anchored, typed, and independently checked.

## 2. Non-negotiable invariants

| ID | Invariant |
|---|---|
| EIB-I01 | No bridge record may overwrite, paraphrase away, or renumber an authoritative clause. |
| EIB-I02 | Every invented sort, argument, predicate, baseline, or dependency is labeled as an EIB choice. |
| EIB-I03 | Missing evidence is UNAVAILABLE, never Boolean false. |
| EIB-I04 | A solver verdict is provisional until a small checker replays its certificate or witness. The report must distinguish fresh-process replay from an independently implemented checker. |
| EIB-I05 | A bounded search reports only the stated bound; “none found through scope N” is not a theorem. |
| EIB-I06 | Proof correctness and statement fidelity are separate gates. A kernel can prove a mistranslation. |
| EIB-I07 | Explains, Authors, K_E, True, Possible, causal uptake, and physical realization are not replaced by heuristic scores. |
| EIB-I08 | The inference-status alphabet remains exactly DEF, IMP, DER. Source marks X, R, M, Q, and O occupy a separate field. |
| EIB-I09 | A declaration may receive DER only for an explicit closed proposition with complete dependencies and a replayable proof. A non-entailment DER may use a fully typed countermodel plus satisfaction checks; an arbitrary SAT result is not DER. |
| EIB-I10 | Every extension must be conservative over the old vocabulary unless it is visibly declared as a new assumption module. |

## 3. Trust boundary

The trusted computing base is deliberately small. Parsing, normalization,
translation, tactics, model search, language models, and solver implementations
may be wrong without being able to confer PROVED status.

| Component | Trust treatment | Required evidence |
|---|---|---|
| Authority PDF | Normative source | File hash and page/span anchor |
| Source-to-IR mapping | Reviewable interpretation | Mapping record, declared preservation class, coverage, and translation obligation |
| Typed IR schema | Versioned bridge contract | Schema tests and kernel representation |
| Lean tactics and generators | Untrusted proof producers | Kernel-accepted proof term |
| Lean kernel | Proof checker | Successful build, no sorry, explicit axiom audit |
| Fresh-process Lean replay | Replay using the same kernel implementation | Fresh replay of exported proof objects |
| Independently implemented checker | Higher-assurance replay when configured | Agreement on the exported proof object and trusted statement |
| SMT solver or model finder | Untrusted search engine | Replayed model, trace, or proof certificate |
| Evidence adapter | Untrusted importer | Content hash, provenance, scope, review state, and explicit polarity |
| Human semantic approval | Required for fidelity | Approval of the theorem statement and its source mapping, not merely its proof |

The minimum high-assurance path is:

    PDF clause
        → immutable source anchor
        → typed CR-EIB declaration
        → generated proof obligation
        → candidate proof or model
        → independent replay
        → separately reported fidelity and proof verdicts

## 4. Declaration record

Every authoritative clause and every EIB addition is represented by one immutable
declaration record. Unnumbered source material receives a proxy identifier in the
EIB namespace while retaining its literal source span.

~~~yaml
declaration_id: EIB-DECL-0001
source:
  authority_sha256: 08ff81e848fea976b558345402d85723173be8f40f1041fb00d6267f1e026b8b
  authoritative_ids: [DF-4]
  physical_pdf_pages: [223]
  printed_folios: [222]
  bounding_boxes: required
  literal_transcription: required
  transcription_sha256: required
  extraction_tool_version: required
  rendered_region_sha256: optional
  source_mark_raw: "R from X"
  source_marks_parsed: [R, X]
  source_mark_parse_status: unresolved
  source_tags: [S-BOI1, S-BOI7, S-CB12, S-FOR1]
source_inferential_status: null
proposed_inferential_status: DEF
kind: definition
signature:
  arguments: required
  result: Prop
  binders: required
  hidden_arguments: []
normalized_body: required
interpretation:
  class: explicitation
  choice_ids: [EIB-C-TY01, EIB-C-AR09]
  preserves: required
  loses: []
  coverage: required
dependencies:
  direct: required
  transitive: generated
semantic_ports: required
proof_obligations: required
verification:
  fidelity_status: unreviewed
  typing_status: pending
  proof_status: unattempted
  bounded_search_status: not_run
  witness_replay_status: not_applicable
provenance:
  generated_by: required
  tool_versions: required
  created_at: required
  artifact_hashes: required
~~~

The source_inferential_status remains null unless CR-1.0 itself is formally
adjudicated. The proposed_inferential_status belongs only to CR-EIB and never
retroactively changes the PDF.

## 5. Independent status dimensions

The bridge must not compress unrelated questions into one “confidence” score.

| Dimension | Allowed values | Meaning |
|---|---|---|
| Source mark | X, R, M, Q, O, composite, absent | The PDF’s source-facing status |
| Proposed inferential status | DEF, IMP, DER, null | The role proposed inside CR-EIB |
| Mapping class | exact, planned_definition_relative_to_ports, explicitation, directional, opaque_port, assumption, unresolved | How source language becomes bridge language |
| Evidence availability | available, unavailable, contested, rejected, superseded | Whether an external semantic assertion may be imported |
| Proof status | unattempted, open, proved, refuted, failed, blocked | Kernel or countermodel result |
| Search status | not_run, witness_found, none_through_scope, unknown, error | Bounded or incomplete search result |
| Review status | unreviewed, accepted, rejected, superseded | Human semantic review state |

Unavailable evidence blocks an applicable conclusion. It does not supply the
negation of the missing assertion. Contested evidence remains outside the active
assumption set unless a named policy module explicitly chooses a polarity and
records that choice.

## 6. Typed core

### 6.1 Content roles

The PDF calls Problem, AttemptExp, Criticism, and Standard sorts while also
saying they are non-exclusive semantic roles of Content. CR-EIB resolves this
as overlapping dependent subtypes, not disjoint carriers.

| Construct | CR-EIB interpretation |
|---|---|
| ContentRole | problem, attempted_explanation, criticism, standard |
| HasRole | Opaque relation Content × ContentRole → Prop |
| RoleContent(r) | A Content paired with a witness of HasRole(content, r) |
| Problem | RoleContent(problem) |
| AttemptExp | RoleContent(attempted_explanation) |
| Criticism | RoleContent(criticism) |
| Standard | RoleContent(standard) |

This is EIB-C-TY01. One Content may inhabit several role subtypes. No
disjointness theorem is introduced.

### 6.2 Added carrier and index types

The following types make explicit objects already used or required by the active
model. They are opaque carriers unless a later module supplies lawful structure.

| Group | Types |
|---|---|
| Temporal | Event, Interval, Horizon |
| Response and episode | Response, ProblemSituation, Episode |
| Collections and indices | EquivLevel, ProblemClass, RivalClass, VariantFamily, Domain, ConstructionDomain |
| Enabling and measurement | EnablingEnvelope, ResourceEnvelope, Distribution, Metric, CostModel |
| Causal and provenance | Boundary, ProvGraph, ProvNode, ProvEdge, Intervention, HeldFixed, CounterfactualWorld |
| Physical and modal | Formula, PhysicalTheory, Tolerance, RealizationMap, PhysicalHistory, PhysicalRegion, Constructor, Program, ConstructorNetwork, PerturbationFamily |
| Evolutionary and computational | Population, Encoding, ConsequenceRelation, Successor |

Adding a carrier does not assert that it is inhabited. Where non-emptiness is
required, it must be a named IMP premise.

### 6.3 Choice registry

The types above are proposed bridge choices, not recovered source facts. Each
choice remains reversible until its mapping obligation is accepted.

| Choice ID | Proposed interpretation | Current status |
|---|---|---|
| EIB-C-TY01 | Problem, AttemptExp, Criticism, and Standard are overlapping Content subtypes | proposed |
| EIB-C-TY02 | Event is a distinct opaque carrier | proposed |
| EIB-C-TY03 | An interval use that needs an endpoint carries an explicit endpoint witness | proposed |
| EIB-C-TY04 | alpha inhabits an opaque Response carrier | proposed |
| EIB-C-TY05 | Collection, domain, class, metric, encoding, and horizon objects receive distinct opaque carriers | proposed |
| EIB-C-TY06 | Formula and physical/modal carriers are reified only inside a named physical module | proposed |
| EIB-C-TY07 | Provenance and counterfactual objects receive explicit graph and intervention structures | proposed |
| EIB-C-TY08 | The CCPResult endpoint y is Content, with separate problem-situation evidence | proposed |
| EIB-C-TY09 | Point satisfaction, interval satisfaction, and event occurrence are separate forms | proposed |
| EIB-C-TY10 | A physical region reaches an abstract predicate only through an explicit abstractImage(realization, region) term | proposed |
| EIB-C-AR01 | Rep has a Token-or-State ground witness; Represents existentially hides that witness | proposed |
| EIB-C-AR02 | Retained has explicit system, content, history, and time arguments | proposed |
| EIB-C-AR03 | Authors receives an explicit episode, boundary, and provenance context | proposed |
| EIB-C-AR06 | Each contrast predicate receives the entity being classified | proposed |
| EIB-C-AR09 | OCA receives explicit history, interval, time, equivalence level, and boundary baselines | proposed |
| EIB-C-AR10 | Possible receives theory, tolerance, and resource baselines | proposed |
| EIB-C-AR11 | UED receives a physical-admissibility profile through its enabling envelope | proposed |

### 6.4 Interval and satisfaction alternatives

CR-EIB does not assume that every interval is nonempty or has a total terminal
time. An IntervalContext contains an Interval and, only when a declaration needs
t_I, an EndTimeWitness proving that a selected time is an admitted endpoint.

The proposed satisfaction forms are:

| Form | Provisional signature | Choice |
|---|---|---|
| HoldsAt | Model × Hist × Time × Formula → Prop | EIB-C-TY06, EIB-C-TY09 |
| HoldsDuring | Model × Hist × Interval × Formula → Prop | EIB-C-TY06, EIB-C-TY09 |
| Occurs | Model × Hist × Time × Event → Prop | EIB-C-TY02, EIB-C-TY09 |

The source expression M,h,t ⊨ e may elaborate to Occurs(M,h,t,e), and an
interval occurrence may elaborate to HoldsDuring. Those are explicit mapping
alternatives with equivalence obligations, not source facts.

Likewise, the proposed UsesReason signature with response and source/response
times is EIB-C-AR09-style explicitation. A one-time satisfaction reading remains
an alternate mapping until SC-3 and DF-6 are jointly normalized.

### 6.5 CRModel and provisional signature registry

The executable IR must define one explicit CRModel structure containing all
carriers, relations, time order, histories, provenance, counterfactuals,
operations, memory, and resource accounting. Every declaration receives an
explicit M : CRModel binder. Notation may hide M for display only; serialized IR
may not.

EpisodeContext contains M, system, history, interval, optional endpoint witness,
boundary, provenance graph, equivalence level, and resource envelope.
PhysicalContext contains M, physical theory, tolerance, realization map,
boundary, perturbation family, resource envelope, and admitted physical
histories.

The table below is a provisional registry for the first bridge work. It is not a
complete symbol table and does not close BG-AR08. A complete, versioned registry
for every symbol is a release artifact.

| Symbol | Provisional signature, after explicit M | Classification |
|---|---|---|
| Rep | Sys × (Token ⊕ State) × Content × Hist × Time → Prop | opaque port; EIB-C-AR01 |
| Represents | Sys × Content × Hist × Time → Prop | planned_definition_relative_to_ports |
| UsesReason | Sys × Criticism × Response × Hist × Time × Time → Prop | opaque port; mapping unresolved |
| Authors | EpisodeContext × Content × Problem → Prop | opaque port; EIB-C-AR03 |
| Explains | Content × Problem × Background → Prop | opaque port |
| K_E | Content × Problem × Background × Hist × Time → Prop | opaque port |
| True | Content × Problem × Background → Prop | opaque port |
| Possible | PhysicalContext × Formula → Prop | opaque port; EIB-C-AR10 |
| Retained | Sys × Content × Hist × Time → Prop | opaque port; EIB-C-AR02 |
| New | Sys × EquivLevel × Content × Hist × Time → Prop | planned_definition_relative_to_ports |
| CLine | Sys × Content × Content × Criticism × Response × Content × Problem × Background × Hist × Interval → Prop | opaque port constrained by SC-8 |
| OCA | EpisodeContext × Content × Problem × Background × Time → Prop | planned_definition_relative_to_ports |
| CCPResult | Sys × Content × Problem × Background × Hist × Interval → Prop | unresolved pending CCPWitness |
| CCP | Sys × Problem × Background × Hist × Interval → Prop | planned_definition_relative_to_ports |
| EKC | Sys × Content × Problem × Background × Hist × IntervalContext → Prop | planned_definition_relative_to_ports |
| PhysOCA | PhysicalContext × PhysicalRegion × OCAWitness → Prop | unresolved pending BR registry |
| PhysGCD | PhysicalContext × PhysicalRegion × ProblemClass × EnablingEnvelope → Prop | unresolved pending BR registry |

Purports, Problem_s, Attempt_s, PBCrit, Uptake, GCD, HTV, GoodNow, New_H,
CritOf, BearsOn, every contrast predicate, every constructor-theoretic symbol,
and every OM transition symbol must appear in the complete registry before their
declarations can execute.

### 6.6 Required witness records for planned definitions

New may become a definition only after the following relations are typed:
RepresentedAsExplanatory, DeployableInProblemOperation, time order, and
content equivalence at EquivLevel. Its proposed history-indexed body is:

    New(M,s,L,x,h,t) iff there do not exist t' and x' such that
    t' < t, RepresentedAsExplanatory(M,s,x',h,t'),
    DeployableInProblemOperation(M,s,x',h,t'), and Equiv(M,L,x',x).

This body is an explicitation of DF-3 and needs a projection obligation back to
the source surface New_s^L(x,t).

CCPResult remains unresolved until CCPWitness is defined with x_0, x_1, c, k,
alpha, t_0, t_1, t_2, interval-membership and temporal-order proofs, lineage
descent, endpoint representation, endpoint availability, resulting
problem-situation evidence, PBCrit, Uptake, and CLine. Only then may CCPResult be
defined by existence of that witness.

EKC may become an exact CR-EIB definition relative to opaque CCPResult, K_E, and
Retained only after its IntervalContext contains an accepted EndTimeWitness. It
is not yet labeled exact.

PhysicalContext and OCAWitness remove the literal ellipsis from an EIB
interpretation of DF-22. They do not make PhysOCA or PhysGCD definitions until
every BR condition and the abstractImage relation are typed and enumerated.

The endpoint y proposal remains Content. Any use that requires an endpoint
problem situation must supply typed EndpointRepresentation,
EndpointAvailable, and ResultingProblemSituation evidence. EIB-C-TY08 is
deliberately reversible.

## 7. Making prose definitions executable without pretending to decide meaning

DF-8 through DF-21 contain prose relations that are not eliminable as written.
CR-EIB turns each irreducible phrase into a named, typed semantic port. The
surrounding clause may be classified as planned_definition_relative_to_ports.
It becomes exact only after the complete body is enumerated, typechecked, and
its fold/unfold equivalence is kernel-checked.

| Source phrase | Example port family |
|---|---|
| material same-job variant | MaterialVariant |
| explanatory adequacy | AdequateExplanation |
| additional explanatory work | RepairsByExplanation |
| actual rival | ActualRival |
| applicable or undefeated criticism | ApplicableCriticism, Undefeated |
| problem-bearing preference | ProblemBearingPreference |
| stable organization under perturbation | StableOrg |
| capacity preservation or reconstruction | CapacityRestored |
| physically admitted problem | PhysicallyAdmitted |
| bars every continuation | BarsContinuation |
| unchanged explanatory commitment | SameCommitment |
| coverage over a domain | CoversDomain |
| emits, maps, visits, generates, improves | Emits, Maps, Visits, Generates, Improves |
| physical realization of encoding | RealizesEncoding |
| heritability and differential replication | Heritable, DifferentialReplication |
| constructor-theoretic physical knowledge | K_CT |
| explanatory-role representation | RepresentedAsExplanatory |
| deployability in a problem-bearing operation | DeployableInProblemOperation |
| lineage descendant | LineageDescendant |
| endpoint representation and availability | EndpointRepresentation, EndpointAvailable |
| resulting endpoint problem situation | ResultingProblemSituation |
| bridge-condition satisfaction | SatisfiesBridge |
| physical-to-abstract image | AbstractImage |

A named port is not an algorithm. It is a typed location where a domain
interpretation or evidence bundle may be supplied. CR-EIB can prove conditional
consequences from accepted port assertions without claiming to compute their
truth.

## 8. Evidence contract for opaque ports

Every imported assertion over an opaque port must satisfy this contract.

| Field | Requirement |
|---|---|
| evidence_id | Stable, content-addressed identifier |
| port_id and signature version | Exact semantic port and arity |
| assertion | Fully typed positive or negative atom |
| scope | System, history, time or interval, boundary, domain, theory, tolerance, and resources as applicable |
| source | Identified evidence entity with fragment locator and checksum |
| derivation activity | Extraction, measurement, review, intervention, or interpretation method |
| responsible agent | Human, organization, software agent, and declared role |
| tool record | Tool, model, configuration, and version |
| temporal record | Creation and review timestamps |
| admissibility policy | Named policy profile and required reviewers |
| closed-world policy | false by default |
| review state | unreviewed, accepted, rejected, superseded |
| dependencies | Other evidence and interpretation records used |

The record shape follows the useful separation in W3C PROV-O among entities,
activities, and agents. Provenance explains how an assertion arose; it does not
certify that the assertion is true.

## 9. Mapping classes and composition

Each source-to-IR edge declares what it preserves and what it does not.

| Mapping class | Permitted claim |
|---|---|
| exact | Source and target have the same declared meaning over the covered fragment |
| planned_definition_relative_to_ports | A candidate body and required opaque ports are identified, but exactness has not been established |
| explicitation | Target exposes binders or baselines asserted in source prose; equivalence remains an obligation |
| directional | Target is an over- or under-approximation; only direction-safe verdicts transfer |
| opaque_port | Source meaning is represented by a typed external interface |
| assumption | New non-definitional content enters a named IMP module |
| unresolved | No executable translation is authorized |

Every edge records its covered constructs, kept observables, declared loss,
translation validator, and evidence. Along a multi-step route, coverage is the
intersection of covered fragments and assurance cannot exceed the weakest
unre-established step.

A concrete counterexample is accepted only after it is carried back and replayed
in source-level typed vocabulary. An unsatisfiable or universal verdict requires
either a replayed certificate or a kernel proof plus validated translations.

## 10. Disposition plan for the 51 bootstrap blockers

A policy is not a resolution. Each blocker below receives an explicit
disposition, but it remains open until the named choice, registry, body, or proof
obligation exists and passes review.

| Blocker | CR-EIB disposition | 0.1 status |
|---|---|---|
| BG-ID01 | Give every substantive unnumbered span a stable EIB-PROXY identifier with literal anchor | planned |
| BG-ID02 | Create TH-15.P2, TH-15.P3, TH-15.P4, and TH-15.P5 proxy premises | planned |
| BG-ID03 | Preserve raw ranges and add a separately reviewed explicit dependency expansion | planned |
| BG-ID04 | Keep source status null; store only a separately proposed DEF, IMP, or DER | planned |
| BG-TY01 | Apply EIB-C-TY01 overlapping Content subtypes | proposed choice |
| BG-TY02 | Apply EIB-C-TY02 Event carrier | proposed choice |
| BG-TY03 | Apply EIB-C-TY03 IntervalContext and endpoint witness; no total finish function | proposed choice |
| BG-TY04 | Apply EIB-C-TY04 Response carrier | proposed choice |
| BG-TY05 | Add distinct opaque index, class, domain, metric, encoding, and horizon carriers | schema incomplete |
| BG-TY06 | Add a named physical/modal module with Formula, theory, tolerance, realization, region, program, and network types | schema incomplete |
| BG-TY07 | Add typed ProvGraph, intervention, held-fixed, and counterfactual structures; type H as a history family | schema incomplete |
| BG-TY08 | Apply reversible EIB-C-TY08 endpoint-as-Content interpretation | proposed choice |
| BG-TY09 | Apply EIB-C-TY09 point/interval/event alternatives with per-clause mapping obligations | proposed choice |
| BG-TY10 | Require abstractImage(realization, region) before GCD or OCA attribution | obligation open |
| BG-AR01 | Apply EIB-C-AR01 Rep ground witness and existential Represents facade | proposed choice |
| BG-AR02 | Apply EIB-C-AR02 canonical Retained signature | proposed choice |
| BG-AR03 | Apply EIB-C-AR03 EpisodeContext for Authors; bare Authors is rejected | proposed choice |
| BG-AR04 | Replace unary or bare OCA and GCD uses only after complete canonical signatures exist | blocked by symbol registry |
| BG-AR05 | Namespace HTV_V, GoodNow_V, and True; reject lowercase or bare aliases without reviewed expansion | planned |
| BG-AR06 | Apply EIB-C-AR06 explicit classified-entity arguments to every contrast predicate | proposed choice |
| BG-AR07 | Replace PhysOCA ellipsis with PhysicalContext and OCAWitness | blocked by BR registry |
| BG-AR08 | Publish complete arities for Prov, CF, SameJob, Var, Pref, Cost, BearsOn, CritOf, Reach, and all other symbols | blocked by symbol registry |
| BG-AR09 | Apply EIB-C-AR09 explicit L, h, I, time, and boundary in OCA | proposed choice |
| BG-AR10 | Apply EIB-C-AR10 PhysicalContext to possible claims | proposed choice |
| BG-AR11 | Apply EIB-C-AR11 enabling envelope with theory, tolerance, realization, boundary, and resources | proposed choice |
| BG-UD01 | Register Represents, UsesReason, Authors, Possible, and Retained as typed ports or planned definitions | port registry incomplete |
| BG-UD02 | Define or import New_H only after a historical-content registry and equivalence baseline are typed | unresolved |
| BG-UD03 | Require the complete CCPWitness specified in section 6.6 | unresolved |
| BG-UD04 | Convert each prose atom in DF-8–DF-14 into a named typed port; bodies remain planned | port registry incomplete |
| BG-UD05 | Type Q_D as a domain-to-problem-class map, XReach as a set-valued relation, and t_I as an endpoint witness | proposed; bodies absent |
| BG-UD06 | Type the relations used by DF-15–DF-21 before claiming any contrast definition executable | unresolved |
| BG-UD07 | Keep K_CT as an opaque physical port until its exact typed interpretation is accepted | opaque port planned |
| BG-UD08 | Define a transition IR for OM-1–OM-10 or keep every OM non-executable | postponed |
| BG-UD09 | Route every hidden semantic or physical premise through the evidence/import contract | ledger absent |
| BG-UD10 | Type K_CT, realization, PhysOCA, PhysGCD, construction domains, programs, networks, and resources | physical registry absent |
| BG-UD11 | Proxy and type TH-15.P2–P5, including correct-program, deployment, compilation, and resource vocabulary | unresolved |
| BG-UD12 | Normalize each DP, RC, AB, CT, and BR postulate into a closed IMP or leave it blocked | unresolved |
| BG-UD13 | Close every TH formula and non-entailment claim before theorem adjudication | unresolved |
| BG-SY01 | Namespace PerturbationProfile and RealizationMap instead of overloading rho | planned |
| BG-SY02 | Namespace TimeCarrier, CTTask, EventFamily, and EvolutionEnvironment instead of T and E | planned |
| BG-SY03 | Namespace VariantFamily, FixedSearchEvaluator, ProblemDomain, ReachDomain, and ConstructionDomain | planned |
| BG-ST01 | Preserve concordance and active-model status schemes in separate namespaces; no automatic crosswalk | planned |
| BG-ST02 | Preserve each meaning of C in its own source-scheme namespace | planned |
| BG-ST03 | Preserve source_mark_raw verbatim; parsed components remain unresolved until scope is reviewed | planned |
| BG-ST04 | Record absent or collective marks as absent/ambiguous; never infer a mark | planned |
| BG-SR01 | Build a clause-to-claim-locator crosswalk with source-fragment anchors | absent |
| BG-SR02 | Treat missing DF warrants as unavailable; do not infer them from neighboring clauses | open blocker |
| BG-SR03 | Preserve each locator scheme explicitly and resolve the SCC discrepancy before use | open blocker |
| BG-SR04 | Keep S-MAI20 entitlement unavailable until an exact passage locator is supplied | open blocker |
| BG-SR05 | Instantiate the section 8 evidence contract for every semantic, causal, modal, epistemic, and physical import | ledger absent |
| BG-SR06 | Register the exact logical axiom fragment, ordinary-mathematics modules, and any finite-history induction principle | open blocker |

No row above is “resolved” merely because this contract names a treatment.
CR-EIB conformance remains BLOCKED until every open row has a concrete artifact
and validation result.

Downstream application and test namespaces remain quarantined until their own
typed imports and dossiers are admitted. They cannot be used to make the core
bridge pass.

## 11. Relative conservative-extension gate

Conservativity cannot be proved over an under-specified PDF directly. Let V0 be
the vocabulary of a named, accepted, typed CR-EIB base version and let V1 be the
new bridge vocabulary. Every conservativity claim is relative to that exact base
version and its registered assumptions.

For every declaration marked DEF, the bridge must prove a model-expansion
obligation: every admissible V0 model has a V1 expansion satisfying the new
definition while its reduct to V0 is unchanged.

For every explicitation, the bridge must state a projection from the explicit
target signature back to the source surface signature and prove the claimed
equivalence or one-way refinement over the declared coverage.

For every IMP, the assumption enters a named module. Results depending on that
module must expose it in their direct and transitive dependency closures.

Adding carrier structure, endpoint functions, inhabitance, or semantic
constraints is not automatically definitional. Anything that is not freely
expandable enters a named IMP module.

A practical regression check compares an enumerated old-vocabulary query corpus
before and after adding definitions. Changed results block release unless a
non-conservative assumption module was intentionally activated and is shown in
the result. Query regression is diagnostic coverage, not a proof of
conservativity.

## 12. Proof and solver protocol

Lean 4 is the canonical checker because its minimal kernel checks proof terms
independently of tactic implementation. The parser and elaborator emit Lean
declarations and obligations but remain outside the trust boundary.
Running the same Lean kernel in a fresh process is replay, not implementation
independence. A report may claim independently implemented checking only when a
separate checker has validated the exported proof and trusted statement.

SMT-LIB is an interchange for decidable fragments and finite or bounded search.
It is not the source of meaning and does not confer proof status. Each solver
route declares its supported logic, theory fragment, proof format, model format,
and replay capability. Unsupported UNSAT results remain UNCONFIRMED_UNSAT.

| Backend result | CR-EIB result |
|---|---|
| SAT with model, replay succeeds for an existential query | WITNESS_FOUND |
| SAT with model, replay succeeds for the negation of a closed claim | COUNTERMODEL_FOUND and CLAIM_REFUTED |
| Typed countermodel satisfies premises and falsifies conclusion | NON_ENTAILMENT_PROVED only after the explicit non-entailment proposition and checks are kernel-replayed |
| SAT with model, replay fails | BACKEND_DISAGREEMENT; release blocker |
| UNSAT with a certificate replayed by the configured checker | PROVED for the encoded fragment, subject to translation fidelity and checker assurance level |
| UNSAT without replayable certificate | UNCONFIRMED_UNSAT |
| No countermodel through finite scope N | NONE_THROUGH_SCOPE(N) |
| Timeout or unsupported theory | UNKNOWN |
| Lean proof accepted with clean axiom audit | PROVED for the formal statement |
| Lean proof accepted but source mapping unreviewed | PROOF_VALID, FIDELITY_UNREVIEWED |

Why3 may later broker multiple provers, but it is not required for the first
bridge. Alloy may be used as a design-time bounded model finder, but no Alloy
“check” is promoted to an unbounded theorem. TLA+ or Apalache enters only if a
future module gives OM-1–OM-10 a genuine transition-system semantics.

## 13. Validation strategy

### 13.1 Property and metamorphic tests

| Test family | Required relation |
|---|---|
| Parse and print | Parsing a normalized printed term returns the same typed IR |
| Alpha renaming | Consistent bound-variable renaming preserves meaning and verdict |
| Substitution | Capture-avoiding substitution preserves typing |
| Ill-typed rejection | Sort swaps, missing baselines, and unresolved overloads fail closed |
| Definition fold/unfold | Exact definitions give identical checked outcomes |
| Dependency order | Reordering an explicit dependency set does not change closure |
| Evidence absence | Removing an import changes applicability to blocked, not to false |
| Scope expansion | A bounded no-countermodel result reports the new bound and never upgrades itself to proof |
| Semantic negative control | Quantifier swaps, premise deletion, polarity reversal, and bound changes are detected |
| Source anchoring | Any source-text or locator mutation changes the content hash and invalidates the mapping |

### 13.2 Differential and witness checks

The reference evaluator and the SMT encoding are distinct paths. On their
declared shared finite conformance corpus, their SAT, UNKNOWN, rejection, and
normalized witness classes must agree. Unbounded UNSAT agreement is not required
from a finite evaluator. A disagreement inside the shared fragment blocks
release rather than being decided by majority vote.

Every model, trace, and countermodel is minimized when possible, serialized,
content-hashed, and replayed against the typed IR. Every proof certificate is
replayed by the smallest configured checker. “Smallest witness” may be claimed
only with a declared order, explored scope, and replayable minimality
certificate.

### 13.3 Semantic mutation testing

The conformance suite must kill non-equivalent mutants produced by swapping
quantifiers, negating relations, changing strict orders, dropping premises,
altering bounds, changing source IDs, perturbing binder indices, and replacing
opaque ports with constants. Surviving mutants identify missing obligations.

## 14. Release gate

CR-EIB-0.1 may be called executable only when all rows pass.

| Gate | Pass condition |
|---|---|
| Authority | PDF hash matches; every record has an exact span or explicit proxy span |
| Coverage | All 110 numbered declarations and every substantive unnumbered span are represented |
| Typing | No undeclared sort, free variable, unresolved overload, literal ellipsis, or hidden baseline |
| Status | Source marks and DEF/IMP/DER are separate; no DER lacks replayable evidence |
| Mapping | Every translation declares coverage, preservation direction, loss, and validation |
| Imports | Every opaque assertion has a complete evidence contract; unavailable is never false |
| Conservativity | Every definition passes model expansion; every non-definitional assumption is a named IMP |
| Proof | No sorry; explicit axiom audit; every claimed proof replayed at its stated assurance level |
| Solver | Zero unreplayed findings and zero unexplained differential disagreements |
| Tests | Each declaration has a test-applicability matrix; every applicable positive, negative, metamorphic, and ill-typed test is present, and every not_applicable entry is justified |
| Mutation | Every known non-equivalent semantic mutant is killed or explicitly blocked |
| Reproducibility | PDF, IR, dependencies, seeds, tools, models, certificates, and outputs are content-hashed and pinned |

Passing this gate establishes that CR-EIB is an auditable executable
interpretation. It does not establish that any real system is creative, that an
opaque semantic import is true, or that the bridge is itself part of CR-1.0.

## 15. First implementation slice

The first slice should prove the architecture before attempting all 110
declarations.

| Slice | Included material | Demonstration |
|---|---|---|
| S0 Authority | PDF manifest, anchors, proxy IDs, record schema | A source mutation invalidates its mapping |
| S1 Minimal typed core | CRModel, Sys, Content, Problem, Background, Hist, Time, IntervalContext, and opaque CCPResult, K_E, Retained ports | The DF-10 surface vocabulary elaborates with no hidden binder |
| S2 Candidate definition | EIB-DF10-CANDIDATE only | The proposed EKC body fold/unfold proof is kernel-replayed relative to the three opaque ports and an endpoint witness |
| S3 Pilot result | EIB-TH3a definitional implication and EIB-TH3b relative non-sufficiency | A proof and a finite typed countermodel exercise both checking paths |
| S4 Fidelity | Source anchor, proposed DF-10 mapping, explicit dependency closure, and relative model-expansion obligation | Proof validity and source fidelity are reported separately |
| S5 Search | Minimal typed IR to SMT-LIB exporter | A minimized witness is replayed; bounded absence is labeled honestly |

This is an architecture pilot, not adjudication of source TH-3. TH-3 remains
unadjudicated until its full source dependency closure—MS-4, MS-8, SC-7, SC-8,
DF-7a, DF-10, IR-2, and IR-4—has accepted typed mappings. TH-1, TH-16, and
TH-17 remain behind their larger dependency closures. The slice deliberately
postpones the constructor-theoretic and physical realization layers until the
abstract bridge, evidence ports, and checking path are working.

## 16. Repository contract

An empty private repository is sufficient. The initial tree should be:

    authority/
      source_manifest.yaml
      source_anchors.yaml
      authority.pdf.sha256
    bridge/
      schema/
      declarations/
      choices/
      evidence_contracts/
    formal/
      CREIB/
    solver/
      smtlib/
    witnesses/
    tests/
      conformance/
      properties/
      metamorphic/
      mutations/
    reports/
    tools/
    lock/

The PDF itself may remain outside Git if licensing or size policy requires it;
its hash, page count, and reproducible acquisition instruction must remain
inside. Generated verdicts never overwrite declarations. A change to a
declaration, mapping, schema, or evidence policy creates a new version and
revalidates every dependent result.

## 17. Research basis

Recent peer-reviewed work supports validating each translation rather than
trusting a front end. Parthasarathy et al. generate an independently checkable
Isabelle proof for each Viper-to-Boogie translation. Lin et al. likewise separate
a complex verifier from a small proof-certificate checker. Property-based and
property-targeted mutation testing provide evidence that semantic properties
exercise substantially more behavior than example-only unit tests.

Recent alphaXiv preprints reinforce two architectural ideas: generate multiple
interpretations from one semantic interface, and make each translation edge
declare coverage, preservation, loss, evidence, and source-level witness replay.
The fidelity-graded translation work is especially close to this project, but
its artifact and much of its text are LLM-generated without human semantic
review. CR-EIB therefore adopts its useful bookkeeping pattern, not its claims
as authority.

The decisive synthesis is:

    immutable source
        + typed explicit interpretation
        + opaque evidence ports
        + per-translation validation
        + proof or witness replay
        + conservative-extension tests
        = an honest executable bridge

## 18. Selected references

Consensus citation counts below are the search snapshot observed on 2026-08-29,
not permanent bibliometric claims.

| Ref | Source | Relevance |
|---|---|---|
| R1 | G. Parthasarathy, T. Dardinier, B. Bonneau, P. Müller, A. J. Summers, [“Towards Trustworthy Automated Program Verifiers: Formally Validating Translations into an Intermediate Verification Language”](https://consensus.app/papers/towards-trustworthy-automated-program-verifiers-parthasarathy-dardinier/162f4e20c10c57c3aa4c9575982de635/?utm_source=chatgpt), Proceedings of the ACM on Programming Languages 8, 2024; 9 citations in the snapshot | Per-run validation of front-end translation |
| R2 | Z. Lin, X. Chen, M.-T. Trinh, J. Wang, G. Roşu, [“Generating Proof Certificates for a Language-Agnostic Deductive Program Verifier”](https://consensus.app/papers/generating-proof-certificates-for-a-languageagnostic-lin-chen/67c908345a195f0baa91d5e0292e2f10/?utm_source=chatgpt), Proceedings of the ACM on Programming Languages 7, 2023; 11 citations in the snapshot | Small independent proof-certificate checking |
| R3 | S. Ravi, M. Coblenz, [“An Empirical Evaluation of Property-Based Testing in Python”](https://consensus.app/papers/an-empirical-evaluation-of-propertybased-testing-in-ravi-coblenz/dc572f4deca555149e7378adc6c9fdfc/?utm_source=chatgpt), Proceedings of the ACM on Programming Languages 9, 2025; 6 citations in the snapshot | Empirical strength of generated property tests |
| R4 | E. Bartocci, L. Mariani, D. Ničković, D. Yadav, [“Property-Based Mutation Testing”](https://consensus.app/papers/propertybased-mutation-testing-bartocci-mariani/80f8a3a5a6215927863affecec798831/?utm_source=chatgpt), 2023 IEEE Conference on Software Testing, Verification and Validation, 2023; 8 citations in the snapshot | Requirement-specific mutation adequacy |
| R5 | C. Kirsch, [“Untrusted Authors, Trusted Answers: A Calculus of Fidelity-Graded Translations”](https://www.alphaxiv.org/abs/2607.14137), alphaXiv/arXiv 2607.14137, 2026 | Coverage, loss, evidence grades, weakest-link composition, witness replay |
| R6 | E. Liang, [“SEMBridge: Tagless-Final Program Semantics with Weakest-Precondition and Bounded-Checking Interpretations”](https://www.alphaxiv.org/abs/2606.00220), alphaXiv/arXiv 2606.00220, 2026 | Multiple interpretations from one semantic interface; limited prototype |
| R7 | Lean 4 Language Reference, [“Validating a Lean Proof”](https://lean-lang.org/doc/reference/latest/ValidatingProofs/), current online reference | Minimal kernel, fresh replay, external checking, and theorem-meaning caveat |
| R8 | W3C, [PROV-O Recommendation](https://www.w3.org/TR/prov-o/) | Entity/activity/agent provenance and derivation vocabulary |
| R9 | [Why3 1.8 documentation](https://why3.org/doc/) | Typed verification IR and multi-prover orchestration |
| R10 | Alloy Analyzer, [model-finder documentation](https://alloytools.org/faq/what_kind_of_analysis_does_the_alloy_analyzer_do.html) | Finite-scope model and counterexample finding |

## 19. Acceptance consequence

Accepting CR-EIB-0.1 authorizes development of the bridge as a separate,
versioned reconstruction. It does not authorize changing the PDF, treating an
EIB choice as source fact, importing downstream applications into the core, or
calling any real system creative.

The next irreversible boundary is repository creation. Before that boundary,
the remaining work is to instantiate this contract for the 110 declarations,
assign EIB proxy IDs to the unnumbered spans, and produce the S0–S3 conformance
fixtures.
