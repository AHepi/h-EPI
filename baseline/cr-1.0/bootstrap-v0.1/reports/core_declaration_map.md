# CR-1.0 core declaration map

## Authority, scope, and locator convention

The sole semantic and formal authority for this map is `Creativity_Semantic_Model_CR-1.0(1).pdf`. The handoff plan is procedural only. Where it changes, adds, or normalizes PDF material, the PDF form is preserved here and the difference is recorded in the ambiguity ledger.

This is a cold-start declaration inventory, not a repaired formalization. It does not accept, reject, or prove any `TH-*` result. Each theorem has `inferential_status: null` and is marked only with `target_status: DER`, pending later proof-kernel adjudication under its displayed dependencies.

Locators use `PDF n / footer m`, where `n` is the one-based physical PDF page and `m` is the printed page number in the footer. For example, Model CR-1.0 begins on `PDF 219 / footer 218`.

The inferential-status column uses only the requested candidates:

| Candidate | Use in this map |
|---|---|
| `DEF` | Intended exact eliminable abbreviation. This does not certify that the PDF body is already machine-eliminable. |
| `IMP` | Non-eliminable signature, semantic, causal, epistemic, modal, physical, bridge, rule, or model-class commitment. |
| `DER` | Claimed consequence or non-entailment. All `TH-*` entries remain unadjudicated `DER` candidates here. |

Source marks are orthogonal to these candidates. Model §0 uses `X`, `R`, `M`, `Q`, and `O` for source discipline (`PDF 219 / footer 218`). The report-wide claim-status table instead uses `D`, `X`, `Q`, `R`, `P`, `CT`, `E`, `T`, and `N` (`PDF 13 / footer 12`). Neither vocabulary, by itself, determines `DEF`, `IMP`, or `DER`.

## Identifier families and candidate inferential classes

| Family | Exact identifiers | Candidate | Authoritative section and locator |
|---|---|---|---|
| Type constraints | `TY-1`–`TY-3` | `IMP` | Model §1.1, `PDF 221 / footer 220` |
| Model structure | `MS-1`–`MS-9` | `IMP` | Model §1.2, `PDF 221–222 / footers 220–221` |
| Satisfaction clauses | `SC-1`–`SC-8` | `IMP` | Model §1.3, `PDF 222–223 / footers 221–222` |
| Semantic definitions | `DF-1`–`DF-4`, `DF-4a`, `DF-5`–`DF-7`, `DF-7a`, `DF-8`–`DF-21` | `DEF` | Model §2–§3, `PDF 223–225 / footers 222–224` |
| Reconstruction choices | `RC-1`–`RC-3` | `IMP` | Model §3, `PDF 225 / footer 224` |
| Deutschian postulates | `DP-1`–`DP-11` | `IMP` | Model §4, `PDF 226 / footer 225` |
| Adaptation bridge | `AB-1` | `IMP` | Model §4, `PDF 226 / footer 225` |
| Object moves | `OM-1`–`OM-10` | `IMP` | Model §5, `PDF 227 / footer 226` |
| Metalevel inference rules | `IR-1`–`IR-8` | `IMP` | Model §6, `PDF 227–228 / footers 226–227` |
| Constructor-theory layer | `CT-1`–`CT-7` | `DEF` candidates for `CT-1`–`CT-4`, `CT-6`; `IMP` candidate for `CT-7`; `CT-5` unavailable because it mixes `DEF`/`IMP` content | Model §7.1, `PDF 228 / footer 227` |
| Physical realization bridges | `BR-1`–`BR-8` | `IMP` | Model §7.2, `PDF 228–229 / footers 227–228` |
| Physical definitions | `DF-22`, `DF-23` | `DEF` | Model §7.2, `PDF 229 / footer 228` |
| Claimed results | `TH-1`–`TH-17` | `DER` candidate only | Model §8, `PDF 229–233 / footers 228–232` |

Primitive signature declarations and legal rules are not eliminable abbreviations. They are therefore mapped to `IMP` for bootstrap purposes. The fact that the PDF does not itself give those declarations an inferential status is an audit issue, not silently repaired here.

## Canonical sorts

Model §1.1 declares exactly these nineteen sorts (`PDF 221 / footer 220`):

```text
Sys, Time, Hist, State, Token, Content, Problem, AttemptExp,
Criticism, Standard, Observation, Operation, Background, Context,
Environment, Resource, PhysSubstrate, PhysAttribute, CTTask.
```

Candidate inferential class: `IMP` as primitive typed signature declarations.

The PDF immediately qualifies the declaration: “AttemptExp, Criticism, Standard and Problem are semantic roles of contents, not mutually exclusive substances.” It also permits explicit or inexplicit contents and requires system-level causal use rather than analyst resemblance. Standard many-sorted semantics does not automatically supply overlapping role sorts, so the overlap/coercion regime remains unresolved.

### Type constraints

| ID | Line-break-normalized PDF text | Candidate | Locator |
|---|---|---|---|
| `TY-1` | “Predicates are sorted. Tokens are not their contents; prediction is not explanation; retention is not truth; physical information is not explanatory knowledge.” | `IMP` | Model §1.1, `PDF 221 / footer 220` |
| `TY-2` | “Every use of new, general, possible, good, same explanation, reach, efficient or owned displays its baseline: system, content-equivalence level, theory, problem/background, resources or boundary.” | `IMP` | Model §1.1, `PDF 221 / footer 220` |
| `TY-3` | “Semantic, causal, epistemic and physical claims occupy distinct types. A cross-type inference requires a named bridge.” | `IMP` | Model §1.1, `PDF 221 / footer 220` |

## Abstract model tuple and exposed signatures

Model §1.2 gives the tuple exactly as follows (`PDF 221 / footer 220`):

\[
\mathcal M=\langle T,<,H,\Sigma,E,B,Rep,\equiv_L,Prov,CF,
Purports,Explains,SameJob,Var_V,BearsOn,CritOf,Pref,Reach,
CLine,StableOrg,R,Mem,K_E,True,Cost\rangle.
\]

The tuple and each non-eliminable primitive are `IMP` candidates. The exposed shapes below preserve only what the PDF states or displays. “Unresolved” does not supply a guessed signature.

| Symbol | PDF role or exposed application | Exposed shape/arity | Locator | Audit note |
|---|---|---|---|---|
| `T` | Time carrier in `(T,<)` | carrier, not a predicate | `MS-1`, `PDF 221 / 220` | Relation between sort `Time` and carrier `T` is unstated. |
| `<` | Strict partial order on `T` | binary on `T` | `MS-1`, `PDF 221 / 220` | None at declaration level. |
| `H` | Nonempty family of admissible histories | family/carrier | `MS-1`, `PDF 221 / 220` | Relationship to sort `Hist` is implicit. |
| `Σ` | Abstract state | `Σ(h,t)`; apparent `Hist × Time → State` | `MS-2`, `PDF 221 / 220` | Totality and admissible `(h,t)` pairs are unstated. |
| `E` | Typed events | `E(h,t)`; apparent set-valued binary map | `MS-2`, `SC-1`, `PDF 221–222 / 220–221` | No `Event` sort appears among the canonical sorts. |
| `B` | Declared system/environment boundary | `B(s,h,t)`; ternary with unresolved codomain | `MS-2`, `PDF 221 / 220` | No `Boundary` sort or membership relation is declared. |
| `Rep` | Causally accessible token/state related to content | PDF displays `Rep(s,z,h,t)`; arity 4 | `MS-3`, `PDF 222 / 221` | Text says token/state is related to content, but no token/state argument appears in the displayed form. |
| `≡_L` | Declared content-equivalence relation | binary on content, parameterized by `L` | `MS-3`, `DF-3`, `PDF 222–223 / 221–222` | `L` has no canonical sort. |
| `Prov` | Causal-credit graph | unresolved | `MS-4`, `PDF 222 / 221` | Nodes, edges, graph typing, and graph predicates are not declared. |
| `CF` | Interventions with held-fixed conditions | unresolved | `MS-4`, `PDF 222 / 221` | No intervention syntax or sort is declared. |
| `Purports` | Content is offered as explanation of problem against background | `Purports(x,p,b)`; arity 3 | `MS-5`, `PDF 222 / 221` | Sort of `x` is not fixed between `Content` and `AttemptExp`. |
| `Explains` | Primitive substantive semantic relation | `Explains(x,p,b)`; arity 3 | `MS-5`, `SC-5`, `PDF 222 / 221` | Domain interpretation is intentionally external. |
| `SameJob` | Types explanatory comparison | unresolved | `MS-6`, `PDF 222 / 221` | No displayed application or arity. |
| `Var_V` | Types explanatory variation/comparison | unresolved; parameter `V` | `MS-6`, `DF-8`, `PDF 222,224 / 221,223` | `V` and the relation’s argument positions are not typed. |
| `BearsOn` | Standard bears on problem/background | `BearsOn(k,p,b)`; arity 3 | `MS-6`, `DF-5`, `PDF 222–223 / 221–222` | None beyond sort assignment. |
| `CritOf` | Criticism alleges defect in candidate | `CritOf(c,x,p,b,k)`; arity 5 | `MS-6`, `DF-5`, `PDF 222–223 / 221–222` | Sort of candidate `x` is not fixed. |
| `Pref` | Time-indexed provisional preference among actual rivals | unresolved | `MS-6`, `PDF 222 / 221` | The prose says time-indexed, but no argument list is displayed. |
| `Reach` | Further problem/context reached by unchanged commitments | `Reach(x,p',b')`; arity 3 | `MS-6`, `DF-14`, `PDF 222,224 / 221,223` | “Context” is described by a problem/background pair rather than the declared `Context` sort. |
| `CLine` | Connected role-preserving causal lineage | `CLine(s,x_0,x_1,c,α,y,p,b,h,I)`; arity 10 | `MS-4`, `SC-8`, `PDF 222–223 / 221–222` | `I` and response/endpoint sorts are undeclared; `h,I` also occur in the satisfaction index. |
| `StableOrg` | Causal-stability predicate | `StableOrg(s,Q,χ)`; arity 3 | `MS-4`, `PDF 222 / 221` | `Q` and `χ` have no canonical sorts. |
| `R` | Available operation repertoire | `R(s,h,t)`; ternary, apparently set-valued | `MS-7`, `PDF 222 / 221` | Availability is modal, but its continuation relation is not separately exposed. |
| `Mem` | Causally accessible memory | `Mem(s,h,t)`; ternary with unresolved codomain | `MS-7`, `PDF 222 / 221` | Memory items and access relation are not typed. |
| `K_E` | Primitive explanatory-knowledge predicate | `K_E(x,p,b,h,t)`; arity 5 | `MS-8`, `PDF 222 / 221` | Earlier Part I displays a 3-place form; see ambiguity ledger. |
| `True` | Independent correspondence predicate | `True(x,p,b)`; arity 3 | `MS-8`, `PDF 222 / 221` | Application-supplied interpretation. |
| `Cost` | Declared resource accounting | unresolved | `MS-9`, `PDF 222 / 221` | No arguments, codomain, algebra, or resource aggregation law is declared. |

## Model-structure commitments

| ID | Line-break-normalized PDF text | Candidate | Locator |
|---|---|---|---|
| `MS-1` | “`(T,<)` is a strict partial order; `H` is a nonempty family of admissible histories, not only the actual trace.” | `IMP` | Model §1.2, `PDF 221 / footer 220` |
| `MS-2` | “`E(h,t)` supplies typed events and `Σ(h,t)` the abstract state. `B(s,h,t)` fixes a declared system/environment boundary. Nested boundaries are permitted but cannot be changed after seeing which one yields the preferred attribution.” | `IMP` | Model §1.2, `PDF 221 / footer 220` |
| `MS-3` | “`Rep(s,z,h,t)` relates a causally accessible token/state to content `z`; `≡_L` is the declared content-equivalence relation. Encoding changes may preserve content and surface similarity may fail to preserve it.” | `IMP` | Model §1.2, `PDF 222 / footer 221` |
| `MS-4` | “`Prov` is a causal-credit graph spanning architecture/design, inherited or trained repertoire, stored content, episode inputs, tools/interlocutors, candidates, criticisms and revisions. `CLine(s,x_0,x_1,c,alpha,y,p,b,h,I)` marks one connected, role-preserving subgraph in which an authored attempt `x_0`, the criticized candidate `x_1`, reason-specific response `alpha`, and endpoint problem situation `y` belong to the same causal episode. `StableOrg(s,Q,chi)` is an independently interpreted causal-stability predicate over declared perturbations, resources and problem class. `CF` supplies interventions with declared held-fixed conditions. These relations are substantive modeling imports, not consequences of drawing arrows.” | `IMP` | Model §1.2, `PDF 222 / footer 221` |
| `MS-5` | “`Purports(x,p,b)` says that `x` is offered as an explanation of problem `p` against background `b`. It can be false or fail to explain. `Explains(x,p,b)` is a primitive, substantive semantic relation. It is not defined as prediction, compression, usefulness, acceptance or survival.” | `IMP` | Model §1.2, `PDF 222 / footer 221` |
| `MS-6` | “`SameJob`, `Var_V` and `BearsOn` type explanatory comparison. `CritOf(c,x,p,b,k)` alleges a defect in `x` relative to problem-bearing standard `k`. `Pref` is a time-indexed, provisional preference among actual rivals. `Reach(x,p',b')` records a further problem/context to which unchanged explanatory commitments of `x` apply.” | `IMP` | Model §1.2, `PDF 222 / footer 221` |
| `MS-7` | “`R(s,h,t)` is the available operation repertoire; `Mem(s,h,t)` is causally accessible memory. Availability is modal over admissible continuations, not actual occurrence.” | `IMP` | Model §1.2, `PDF 222 / footer 221` |
| `MS-8` | “`K_E(x,p,b,h,t)` is a primitive explanatory-knowledge predicate: `x` constitutes a fallible improvement in the explanatory problem situation, not merely persistence or endorsement. `True(x,p,b)` is an independent correspondence predicate when an application supplies one. CR-1.0 does not reduce `K_E` to a score or identify it with perfect truth. Applications must supply domain-specific epistemic and truth interpretations.” | `IMP` | Model §1.2, `PDF 222 / footer 221` |
| `MS-9` | “`Cost` records declared resources. No unboundedness or efficiency claim is meaningful without it.” | `IMP` | Model §1.2, `PDF 222 / footer 221` |

## Satisfaction commitments and primitive predicates

The satisfaction form is `M,h,t |= φ`. `SC-4` and `SC-8` instead use the indexed form `M,h,I |= ...` (`PDF 222–223 / footers 221–222`). All `SC-*` clauses are `IMP` candidates because they impose substantive interpretations rather than merely abbreviating already formal bodies.

| ID | Line-break-normalized PDF text | Primitive exposed | Locator |
|---|---|---|---|
| `SC-1` | “`M,h,t \|= e` iff typed event `e ∈ E(h,t)`.” | event membership | `PDF 222 / footer 221` |
| `SC-2` | “`M,h,t \|= Represents(s,z)` iff an internal discriminable token/state realizes `z` and at least one available operation uses the difference between it and relevant alternatives. An observer’s label alone is insufficient.” | `Represents(s,z)` | `PDF 222 / footer 221` |
| `SC-3` | “`M,h,t \|= UsesReason(s,c,α)` iff reason-content-preserving recodings of `c` preserve the relevant response family, while interventions changing the alleged defect—matched where possible for format, salience and channel—change `α` in defect-appropriate ways. This is an `M` reconstruction of content-sensitive causation.” | `UsesReason(s,c,α)` | `PDF 222 / footer 221` |
| `SC-4` | “`M,h,I \|= Authors_s(x,p)` iff the causal-credit explanation over the predeclared boundary assigns construction or reconstruction of the problem-specific explanatory organization in `x` to operations of `s`, rather than merely to retrieval, a stock answer, a designer-prepared response, a fixed evaluator that already embodies the target adaptation, or an external selector. Prior enabling knowledge does not by itself defeat authorship.” | `Authors_s(x,p)` | `PDF 222 / footer 221` |
| `SC-5` | “`M,h,t \|= Explains(x,p,b)` only under the supplied explanation interpretation for the domain. Predictive fit is neither necessary nor sufficient by this clause.” | imported interpretation of `Explains` | `PDF 222 / footer 221` |
| `SC-6` | “`Possible_Θ(φ)` is true iff a named physical theory `Θ` admits an arbitrarily accurate realization at the stated tolerance when that is what its modality means. Abstract consistency alone is not physical possibility.” | `Possible_Θ(φ)` | `PDF 222 / footer 221` |
| `SC-7` | “`M,h,t \|= Retained_s(x)` iff a token/state carrying `x`, or a causally sufficient reconstructible disposition for it, is accessible to a relevant possible later operation of `s`. Retention is neither endorsement nor `K_E`.” | `Retained_s(x)` | `PDF 223 / footer 222` |
| `SC-8` | “`M,h,I \|= CLine(s,x_0,x_1,c,alpha,y,p,b,h,I)` only if one predeclared `Prov` subgraph and its matched counterfactuals establish all of the following: `x_0` is the originating attempt; `x_1` is `x_0` or a revision/reconstruction descended from it; `c` targets `x_1` on problem `p`; the reason-content of `c` makes a defect-appropriate causal difference to response `alpha`; and `y` is the retained/revised/rejected/reframed endpoint produced by that response. Temporal co-occurrence or analyst-assigned topic similarity is insufficient.” | constrained `CLine` | `PDF 223 / footer 222` |

## Eliminable semantic definitions

Model §2 states: “The following are abbreviations. They classify models but assert neither existence nor physical realization.” Each `DF-*` below is therefore a `DEF` candidate. The “visible references” column is a bootstrap cross-reference extracted from the displayed body; the PDF does not provide exhaustive direct-dependency certificates for definitions.

| ID | Line-break-normalized authoritative body | Visible core references | Source mark/tags | Locator |
|---|---|---|---|---|
| `DF-1` represented problem | `Problem_s(p,b,t)` iff `s` represents a conflict, inadequacy or unresolved relation among ideas relative to background `b`. A bare externally imposed reward is not yet a Deutschian problem unless it receives such a role. | `SC-2`/representation role | `[R: S-BOI1, S-FOR3]` | `PDF 223 / footer 222` |
| `DF-2` attempted explanation | `Attempt_s(x,p,b,t)` iff `Problem_s(p,b,t)`, `s` represents `x`, and `Purports(x,p,b)`. `Explains(x,p,b)` is not required. | `DF-1`, `SC-2`, `MS-5` | `[R]` | `PDF 223 / footer 222` |
| `DF-3` system-relative newness | `New_s^L(x,t)` iff there is no earlier `x'` such that `s` represented `x'` as explanatory content, could deploy it in at least one problem-bearing operation, and `x' ≡_L x`. Historical novelty is `New_H^L`; the two are independent. Reconstructing another person’s explanation can therefore be new-to-system without being new-to-history. | `MS-1`, `MS-3`, `MS-7`, `SC-2` | `[R: S-FOR1, S-BOI10, S-BOI16]` | `PDF 223 / footer 222` |
| `DF-4` originative creative act | `OCA(s,x,p,b,h,t) ≡ Attempt_s(x,p,b,t) ∧ New_s^L(x,t) ∧ Authors_s(x,p)`. No criticism, retention, truth or success conjunct occurs. OCA is authorship of a new attempted explanation. | `DF-2`, `DF-3`, `SC-4` | `[R from X: S-BOI1, S-BOI7, S-CB12; correction supported by S-FOR1]` | `PDF 223 / footer 222` |
| `DF-4a` originative creativity capacity | `OCap(s,Q,chi)` iff `Q` is a nonempty declared problem class, `StableOrg(s,Q,chi)` holds, and for each admissible represented problem in `Q` under enabling conditions `chi`, there is an admissible continuation in which `s` performs an `OCA` by that organization. `Q` may be narrow or singleton; no criticism, success, cross-domain generality or universality is required. This is the direct modal counterpart of Deutsch’s shortest definition, the capacity to create new explanations. | `MS-1`, `MS-4`, `DF-4` | `[R from X: S-BOI1, S-CB12]` | `PDF 223 / footer 222` |
| `DF-5` problem-bearing criticism | `PBCrit(s,c,x,p,b,k,t)` holds iff `s` represents criticism `c`, `CritOf(c,x,p,b,k)`, and `BearsOn(k,p,b)`. Correctness is not required; the alleged defect must be contentful and criticizable. Inexplicit realization is allowed by `SC-2`. | `MS-6`, `SC-2` | `[R: S-FOR3, S-BOI1, S-BOI14]` | `PDF 223 / footer 222` |
| `DF-6` critical uptake | `Uptake(s,c,x,α,h,t,t')` iff `PBCrit` holds at `t`, response `α` at `t'>t` is rejection, revision, test, reasoned retention, reframing or restandardization, and `UsesReason(s,c,α)` holds. Mere negative-token sensitivity or temporal succession is insufficient. | `DF-5`, `SC-3`, `MS-1` | `[R/M: S-FOR3, S-BOI7]` | `PDF 223 / footer 222` |
| `DF-7a` result-indexed critical lineage | `CCPResult(s,y,p,b,h,I)` iff there exist `x_0,x_1,c,k,alpha` in interval `I` such that: (1) `OCA(s,x_0,p,b,h,t_0)` occurs; (2) `PBCrit(s,c,x_1,p,b,k,t_1)` holds for `x_1=x_0` or a lineage descendant of it; (3) `Uptake(s,c,x_1,alpha,h,t_1,t_2)` holds; (4) `CLine(s,x_0,x_1,c,alpha,y,p,b,h,I)` holds; and (5) endpoint `y` and the resulting problem situation are represented and available for possible further conjecture. | `DF-4`, `DF-5`, `DF-6`, `SC-8`, representation and availability commitments | no source tag displayed on the clause | `PDF 223–224 / footers 222–223` |
| `DF-7` critical creative process | `CCP(s,p,b,h,I)` iff `CCPResult(s,y,p,b,h,I)` for some endpoint `y`. The process may end worse than it began. | `DF-7a` | `[R from X: S-FOR3, S-BOI1]` | `PDF 224 / footer 223` |
| `DF-8` hard to vary | `HTV_V(x,p,b,t)` iff, for material same-job variants `x'` in declared family `V`, preserving apparent fit while altering a content-bearing part generally destroys explanatory adequacy unless additional explanatory work repairs it. This is a comparative relation, not a scalar, syntactic rigidity or truth certificate. | `MS-5`, `MS-6` | `[R from X: S-BOI1]` | `PDF 224 / footer 223` |
| `DF-9` current good explanation | `GoodNow_V(x,p,b,A,t)` iff `x` is an actual rival in `A`, `Explains(x,p,b)`, is currently undefeated by applicable criticisms, is comparatively hard to vary, and is provisionally preferred over the other actual rivals by problem-bearing reasons. `GoodNow` does not entail truth or finality. | `MS-5`, `MS-6`, `DF-8` | `[R: S-BOI1, S-FOR3]` | `PDF 224 / footer 223` |
| `DF-10` successful explanatory-knowledge creation | `EKC(s,x,p,b,h,I) ≡ CCPResult(s,x,p,b,h,I) ∧ K_E(x,p,b,h,t_I) ∧ Retained_s(x,h,t_I)`. The endpoint that receives `K_E` is explicitly the endpoint of the critical lineage; an unrelated retained insight cannot satisfy the definition. `K_E`, not self-retention, supplies success. | `DF-7a`, `MS-8`, `SC-7` | `[R: S-BOI1, S-FOR3, S-FOR8]` | `PDF 224 / footer 223` |
| `DF-11` stable critical capacity | `Cap_CR(s,Q,χ)` iff `Q` is a non-singleton declared problem class, `StableOrg(s,Q,χ)` holds, and that organization supports `OCA` and lineage-connected `CCP` across the declared perturbations and enabling conditions/resources `χ`, while preserving or reconstructing the capacity after episodes. This is stronger than `OCap` and is not established by luck or finite success. | `MS-4`, `DF-4`, `DF-7` | no source tag displayed | `PDF 224 / footer 223` |
| `DF-12` general creative disposition | `GCD(s,Q,χ)` iff `Cap_CR(s,Q,χ)`, the same `StableOrg` supports problem formation, criticism and revision across `Q`, and it can transform represented problems or standards rather than only execute a fixed answer list. Generality is relative to declared `Q,χ`; `Q` need not be open-ended. | `MS-4`, `DF-11` | `[R: S-BOI6, S-BOI7, S-BOI16]` | `PDF 224 / footer 223` |
| `DF-13` universal explanatory disposition; strong profile | Let `Q_D` be the declared class of explanatory problems in domain `D`. `UED(s,D,χ)` iff `GCD(s,Q_D,χ)` and, for every physically admitted `p` in `Q_D`, no fixed subdomain restriction in the stable organization bars all admissible continuations containing originative conjecture and critical improvement for `p`, given the suitable time, memory, evidence, criticism and other resources already listed in `χ`. It does not mean present knowledge, certainty, infinite speed or survival. By definition it extends `GCD`; the no-domain-bar clause remains a strong Deutschian conjecture. | `DF-12`, physical/modal and resource vocabulary | `[X/R/Q: S-BOI6, S-BOI7, S-BOI16]` | `PDF 224 / footer 223` |
| `DF-14` explanatory reach | `XReach(x)` is the set of `(p',b')` such that `Reach(x,p',b')` follows from unchanged explanatory commitments of `x` plus stated background. `WideReach_D(x)` means that this set meets a separately declared coverage condition over domain `D`; “wide” is otherwise undefined. Reach may be unknown to the author. | `MS-6` | `[R from X: S-BOI1]` | `PDF 224 / footer 223` |
| `DF-15` | `Generator` emits candidate tokens; no explanation, problem or authorship is required. | contrast primitive | no tag displayed | `PDF 224 / footer 223` |
| `DF-16` | `Predictor` maps conditions to outcome claims; causal or counterfactual explanation is not required. | contrast primitive | no tag displayed | `PDF 224 / footer 223` |
| `DF-17` | `MechanicalDeductor` applies a fixed consequence relation to supplied premises; a derived result need not be a new subsidiary explanation. | consequence relation not otherwise declared | no tag displayed | `PDF 225 / footer 224` |
| `DF-18` | `FixedSearch(D,N,V)` visits/generates members of a domain using a fixed successor/generator `N` and evaluator `V` at the declared semantic level. | `D,N,V` undeclared | no tag displayed | `PDF 225 / footer 224` |
| `DF-19` | `Learner_μ,m` undergoes experience-caused persistent change that improves performance under supplied distribution `μ` and metric `m`. | `μ,m` undeclared | no tag displayed | `PDF 225 / footer 224` |
| `DF-20` | `Computer_f` physically realizes declared encoded input/output relation `f`. `UniversalComputer_F(U)` means that, with suitable programs and resources, `U` can realize every computation in declared class `F`. | physical realization, programs, `f,F` undeclared | no tag displayed | `PDF 225 / footer 224` |
| `DF-21` | `NaturalSelection(P,E)` has heritable variants in population `P` and differential replication in environment `E`; mutations need not represent the adaptation as a problem or explanation. | population, heredity, replication primitives | no tag displayed | `PDF 225 / footer 224` |
| `DF-22` physical originative act | `PhysOCA_Θ,ρ(U,...)` iff `U` satisfies `BR-1`–`BR-7`, `Θ` admits the physical history/interventions, and the realized abstract history satisfies `OCA`. | `SC-6`, `DF-4`, `BR-1`–`BR-7` | no tag displayed | `PDF 229 / footer 228` |
| `DF-23` physical creative disposition | `PhysGCD_Θ,ρ(U,Q,χ)` iff `U` satisfies all eight bridges and realizes `GCD(U,Q,χ)` robustly. | `DF-12`, `BR-1`–`BR-8` | no tag displayed | `PDF 229 / footer 228` |

## Explanatory and physical knowledge declarations

Model §3 reserves `K_E(x,p,b,h,t)` for fallible explanatory knowledge that improves a problem situation and `K_CT(i,e,ρ,τ)` for information `i` whose causal action helps it remain instantiated in a suitable environment `e` under perturbations `ρ` over horizon `τ` (`PDF 225 / footer 224`). These are separate primitive `IMP` candidates, not definitions of one another.

| ID | Authoritative commitment | Candidate | Source/locator |
|---|---|---|---|
| `RC-1` | “`K_E` is not stipulated to entail perfect truth. Deutschian knowledge is fallible and may contain error. If an application needs a factive predicate, add `True(x,p,b)` independently.” | `IMP` | Model §3, `PDF 225 / footer 224` |
| `RC-2` | “Human scientific knowledge commonly instantiates both predicates, but `K_E→K_CT` is a physical embodiment bridge, not a definition, and `K_CT→K_E` is false.” | `IMP` candidate; the embedded non-entailment is also claimed later by `TH-10` | Model §3, `PDF 225 / footer 224` |
| `RC-3` | The explanatory core does not automatically classify every artwork or artistic act. It applies only after an application independently establishes problem-directed, criticizable aesthetic knowledge and supplies either a mapping into `Purports/Explains/K_E` or a declared conservative aesthetic extension with parallel content and success relations. Output novelty, popularity, or felt response alone cannot discharge it. | `IMP` | `[S-BOI14]`, Model §3, `PDF 225 / footer 224` |

The section gives the collective source line `[S-BOI4, S-FOR8, S-SCC5, S-CT13, S-CTL15]`.

## Explicit Deutschian postulates and adaptation bridge

Model §4 explicitly says these clauses “restrict the model class and are not disguised definitions” (`PDF 226 / footer 225`). All are `IMP` candidates.

| ID | Line-break-normalized authoritative commitment | Source mark/tags | Locator |
|---|---|---|---|
| `DP-1` objective explanatory realism | Problems and explanations can concern an objective reality; change can be correction rather than mere perspective shift. `Explains` is not extensionally reducible to prediction, correlation, control, compression or usefulness. | `[X: S-BOI1, S-FOR1]` | `PDF 226 / footer 225` |
| `DP-2` conjectural origin | No observation-to-theory rule mechanically creates the explanatory content selected as relevant. A conjecture may be physically caused and use prior ideas, but need not be derived or justified before being proposed. There is no licensed inductive ascent from repeated instances to a universal explanatory law. | `[X: S-BOI1, S-FOR3]` | `PDF 226 / footer 225` |
| `DP-3` causal authorship | Creative attribution tracks where problem-specific explanatory organization was constructed or reconstructed, not who emitted the surface output. Design, training, stored repertoire, evaluators, tools, interaction and selection environments all remain possible causal contributors. | `[X/R: S-BOI7, S-BOI10, S-BOI16, S-CB12]` | `PDF 226 / footer 225` |
| `DP-4` fallibility | No explanation, criticism, standard, problem framing, proof method or institution is made immune to possible criticism by retention, authority, passing tests or status as a postulate. `GoodNow`, `K_E` and `Pref` never entail certainty or finality. | `[X: S-BOI1, S-FOR3, S-FOR10]` | `PDF 226 / footer 225` |
| `DP-5` reasoned criticism | Criticism compares actual rivals using reasons bearing on the represented problem. Observations become criticisms only through fallible interpretations of the setup, background and rival predictions. Surviving a test removes a criticism; it does not inductively confirm a theory. | `[X/R: S-FOR3, S-BOI1]` | `PDF 226 / footer 225` |
| `DP-6` good-explanation constraint | Among actual rivals, hard-to-vary, problem-bearing structure is an explanatory merit. It is not a complete metric, unique decision procedure or truth guarantee; problems, variation families and standards remain criticizable. | `[X/R: S-BOI1]` | `PDF 226 / footer 225` |
| `DP-7` knowledge growth | Explanatory progress requires more than origin: criticism/error elimination yields a provisionally improved, retained problem situation and normally new problems. It neither guarantees monotonicity nor convergence. | `[X/R: S-FOR3, S-BOI1]` | `PDF 226 / footer 225` |
| `DP-8` generality/universality | Persons are entities capable of creating explanatory knowledge; Deutsch argues that people are universal explainers and guesses that genuine AGIs are persons/general-purpose explainers. Intermediate universalities and the implementation mechanism remain open. | `[X/Q: S-BOI3, S-BOI6, S-BOI7, S-BOI16]` | `PDF 226 / footer 225` |
| `DP-9` physicality without computational sufficiency | Creativity is a physically instantiated software-level capacity, so non-biological realization is not barred by substrate alone. Universal computation permits relevant physical simulation in principle but supplies neither the creative program nor semantic authorship. | `[X/O: S-BOI6, S-BOI7, S-BOI16, S-FOR13]` | `PDF 226 / footer 225` |
| `DP-10` natural-selection contrast | Natural selection can create parochial adaptive/physical knowledge by heritable variation and differential replication. It need not represent problems, explanations or reasons. Person-level conjectures are purposive attempts; criticism can eliminate them without eliminating their author. Lower-level variation/selection may implement that higher-level process without erasing the distinction. | `[X: S-BOI4, S-BOI15, S-BOI16, S-FOR3, S-FOR8, S-CTL15]` | `PDF 226 / footer 225` |
| `AB-1` adaptation-to-physical-knowledge bridge | If a heritable recipe `i` has problem-specific causal effects that contribute to its differential replication and continued instantiation in environment `e` across perturbations `ρ` and horizon `τ`, then `K_CT(i,e,ρ,τ)`. Heritability or frequency alone is insufficient. | `[X/R: S-BOI4, S-FOR8, S-CTL15, S-SCC5]` | `PDF 226 / footer 225` |
| `DP-11` constructor asymmetry | Constructors concern reliable task performance and retained capacity. They do not by that fact originate the program, explanation or criterion they execute. Explanatory creativity can supply constructor know-how; constructorhood alone supplies no creativity. | `[X/R: S-BOI3, S-BOI6, S-CT13, S-SCC5, S-SCC7, S-MAI20]` | `PDF 226 / footer 225` |

## Legal object moves

Model §5 says object moves extend a modeled problem-solving history and “are not truth-preserving inference rules for the theorist” (`PDF 227 / footer 226`). They are mapped as `IMP` transition permissions, not `DER` steps.

| ID and exact move name | Permitted move and explicit non-consequence | Candidate | Locator |
|---|---|---|---|
| `OM-1 OpenProblem` | Register a represented conflict/inadequacy. No solution follows. | `IMP` | `PDF 227 / footer 226` |
| `OM-2 Conjecture` | Author or reconstruct an attempted explanation. Prior warrant is not required; truth does not follow. | `IMP` | `PDF 227 / footer 226` |
| `OM-3 Criticize` | Put forward a reason alleging a defect relative to the problem/background and a criticizable standard. | `IMP` | `PDF 227 / footer 226` |
| `OM-4 InterpretEvidence` | Connect an observation to an alleged defect through an explicit, fallible account of instruments, auxiliaries and rival predictions. Raw observation cannot skip this move. | `IMP` | `PDF 227 / footer 226` |
| `OM-5 CompareRivals` | Compare actual rivals doing the same explanatory job; provisionally prefer, suspend, or narrow without assigning certainty. | `IMP` | `PDF 227 / footer 226` |
| `OM-6 Reject/Revise` | Eliminate or transform an attempted explanation because of a recorded criticism. Rejection does not generate a replacement automatically. | `IMP` | `PDF 227 / footer 226` |
| `OM-7 ReasonedRetain` | Retain a candidate by addressing or surviving a criticism. Mere persistence is not this move. | `IMP` | `PDF 227 / footer 226` |
| `OM-8 Reframe/Restandardize` | Conjecture and criticize a problem or standard. Preserve the superseded version and reason; do not compare results across changed standards silently. | `IMP` | `PDF 227 / footer 226` |
| `OM-9 RepertoireExpand` | Create a new language distinction, operation, proof form, test or representational scheme. This is not explanatory reach (`DF-14`). | `IMP` | `PDF 227 / footer 226` |
| `OM-10 Record/Reconstruct/Iterate` | Preserve or causally reconstruct the lineage and begin a new cycle. Iteration does not guarantee progress. | `IMP` | `PDF 227 / footer 226` |

## Metalevel inference rules

The following are the only numbered metalevel rules in Model §6. They are `IMP` candidates because they constitute the imported proof discipline rather than consequences of the object theory.

| ID | Line-break-normalized authoritative rule | Locator |
|---|---|---|
| `IR-1` | Sorted first-order consequence and ordinary mathematical reasoning are valid within a declared module. | `PDF 227 / footer 226` |
| `IR-2` | A defined predicate may be folded/unfolded exactly. Definitions do not supply existential witnesses or world facts. | `PDF 227 / footer 226` |
| `IR-3` | A theorem may use modus ponens, quantifier rules, finite-history induction and explicit case analysis. | `PDF 227 / footer 226` |
| `IR-4` | Non-entailment is proved by a fully typed countermodel satisfying all premises and falsifying the conclusion. | `PDF 227 / footer 226` |
| `IR-5` | Physical attribution uses bridge transfer: only predicates shown preserved by one predeclared realization map over a counterfactual family may cross from abstract to physical. | `PDF 227 / footer 226` |
| `IR-6` | Dependency lists are transitively closed. Citing a theorem imports every definition, postulate, bridge and empirical premise in its own dependency list. | `PDF 227 / footer 226` |
| `IR-7` | The report uses the strong model-expansion test: a declared definitional module is conservatively acceptable only if every core model can expand without changing core predicates. Absence of a new old-language theorem is a weaker proof-theoretic check and is not asserted to be equivalent without further metatheoretic assumptions. `Explains`, `K_E`, authorship and physical realization are substantive modules, not conservative abbreviations. | `PDF 227 / footer 226` |
| `IR-8` | Before accepting a theorem: unfold every `DF`; expand cited theorem dependencies transitively; identify every existential witness; mark each descriptive-to-normative, semantic-to-physical and actual-to-modal crossing; then attempt a countermodel satisfying exactly the listed dependencies. Failure at any step invalidates the proof. | `PDF 228 / footer 227` |

### Explicitly forbidden metalevel transformations

Immediately after `IR-8`, the PDF states that the following “are not rules” (`PDF 228 / footer 227`). Each exclusion is part of the `IMP` proof-rule boundary.

| Forbidden transformation |
|---|
| `data → theory by induction` |
| `prediction → explanation` |
| `output novelty → authorship` |
| `reward/selection → criticism` |
| `survival → K_E` |
| `copying → understanding` |
| `computation → thinking` |
| `constructor → creator` |
| `finite performance → general/open-ended disposition` |
| `hard-to-vary → truth` |
| `abstract consistency → physical possibility` |

## Constructor-theoretic realization layer

### Exact physical vocabulary

Model §7.1 places all clauses relative to a physical theory `Θ_CT` (`PDF 228 / footer 227`). The exact-vocabulary bodies of `CT-1`–`CT-4` and `CT-6` are procedural `DEF` candidates; `CT-7` remains an `IMP` candidate because it names a primitive counterfactual physical-knowledge relation whose governing laws are an open programme. `CT-5` atomically combines definition-like vocabulary with the substantive interoperability principle, so it remains unavailable (`inferential_status: null`) until the authority supplies a split or one lawful classification.

| ID | Line-break-normalized authoritative clause | Candidate | Locator |
|---|---|---|---|
| `CT-1` | A substrate is a physical system; an attribute is a set of its states; a variable is a set of mutually disjoint attributes. | `DEF` candidate | `PDF 228 / footer 227` |
| `CT-2` | A task is a set of input-attribute/output-attribute pairs on substrates. | `DEF` candidate | `PDF 228 / footer 227` |
| `CT-3` | `ConstructorFor(C,T)` means `C` causes task `T` while retaining the ability to cause it again in the relevant respect. | `DEF` candidate | `PDF 228 / footer 227` |
| `CT-4` | `Possible_CT(T)` means the laws impose no positive lower bound preventing arbitrarily accurate/reliable approximations to a constructor for `T`; it does not mean currently buildable or cheap. | `DEF` candidate | `PDF 228 / footer 227` |
| `CT-5` | An information variable supports possible cloning and every permutation; an information medium bears at least one information variable. Interoperability says composites of information media bear the corresponding product variable. | unavailable; mixed `DEF`/`IMP` clause | `PDF 228 / footer 227` |
| `CT-6` | `UniversalConstructor(C,D)` means `C`, with suitable programs and raw materials, can perform every physically possible construction task in declared domain `D`. | `DEF` candidate | `PDF 228 / footer 227` |
| `CT-7` | `K_CT(i,e,ρ,τ)` is the counterfactual physical-knowledge relation in §3. The report does not claim a completed standalone constructor theory of knowledge; the governing laws remain an open program. | `IMP` | `[S-CT13, S-CTI15, S-CTL15, S-SCC3, S-SCC5, S-SCC7]`, `PDF 228 / footer 227` |

### Physical realization bridge conditions

Model §7.2 declares that a physical region/history `U,H_P` realizes a CR model under one map `ρ` only if all applicable bridge conditions hold (`PDF 228–229 / footers 227–228`). Each bridge is an `IMP` candidate.

| ID | Line-break-normalized authoritative condition | Locator |
|---|---|---|
| `BR-1 Boundary/provenance` | Boundary, scale, design/training history, stores, tools, interlocutors, evaluators and episode channels are declared before attribution. | `PDF 228 / footer 227` |
| `BR-2 Information embodiment` | Semantic roles map to physically discriminable attributes; required copying, transformation and memory operations are possible at stated tolerance. Constructor-theoretic information can discharge physical discrimination, not meaning. | `PDF 228 / footer 227` |
| `BR-3 Transition fidelity` | Every asserted abstract transition corresponds to a physically admitted task/history; costs, noise, repair and side effects are counted. | `PDF 228 / footer 227` |
| `BR-4 Semantic anchoring` | Token/content assignments are supported by systematic production, use, reconstruction and correction across contexts. Neither CT information nor observer resemblance fixes meaning. | `PDF 228 / footer 227` |
| `BR-5 Reason-specific counterfactuals` | The same `ρ` preserves paraphrase/recoding and distinguishes changes in alleged defects; matched interventions redirect repairs in the content-appropriate manner required by `SC-3`. | `PDF 228 / footer 227` |
| `BR-6 Authorship credit` | A causal audit across all provenance layers supports `SC-4`. Runtime novelty is insufficient; prior influence is not automatically disqualifying; reconstruction can be creative. | `PDF 229 / footer 228` |
| `BR-7 Composition and role-conditional memory` | Subsystem/task composition preserves every role relation actually asserted by the abstract predicate being realized. If that predicate asserts criticism, correction, endpoint lineage or retention, the corresponding state or reconstructible disposition must persist under declared perturbations. A bare `OCA` imports no criticism or retention merely by satisfying this bridge. | `PDF 229 / footer 228` |
| `BR-8 Dispositional robustness` | A disposition claim is supported by a stable causal organization over a nontrivial intervention and problem family, not by one lucky possible path. Resources and scaffolding are explicit. | `PDF 229 / footer 228` |

The unnumbered paragraph following `DF-23` is an `R/M` reconstruction, not a numbered declaration. It rejects one extensional CT task “output a new good explanation” and proposes a network/history of component tasks for representation, conjecture, evidence interpretation, criticism, revision, memory, and network revision; it keeps `Explains`, authorship, and `K_E` as independent semantic/epistemic bridges (`PDF 229 / footer 228`). Because it has no declaration identifier, it cannot enter a dependency closure without an explicit later declaration; this is recorded rather than repaired.

## Claimed theorem obligations and exact dependency lines

Every entry below has `inferential_status: null` and `target_status: DER`. Proof text in the PDF was deliberately not reproduced or checked for this bootstrap map.

| ID | Displayed result, line-break normalized | Exact displayed dependency line | Locator |
|---|---|---|---|
| `TH-1` | `OCA` does not entail `OCap`, `CCP`, `EKC`, or `GCD`; and `OCap` does not entail `CCP`, `EKC`, or `GCD`. | `MS-1–MS-5, SC-2, SC-4, SC-7, SC-8, DF-1–DF-4a, DF-7a, DF-7, DF-10–DF-12, IR-4`, with transitive expansion under `IR-6`. | `PDF 229 / footer 228` |
| `TH-2` | `CCP` does not entail `EKC`, and `CCP` does not entail `True`. | `MS-1–MS-8, SC-2–SC-5, SC-8, DF-1–DF-7, DF-7a, DF-10, DP-4, IR-4`, with transitive expansion under `IR-6`. | `PDF 229–230 / footers 228–229` |
| `TH-3` | `EKC(s,x,p,b,h,I) → CCPResult(s,x,p,b,h,I) ∧ K_E(x,p,b,h,t_I) ∧ Retained_s(x,h,t_I)`; but `CCPResult(s,x,p,b,h,I) ∧ Retained_s(x,h,t_I)` does not entail `EKC(s,x,p,b,h,I)`. | `MS-4, MS-8, SC-7, SC-8, DF-7a, DF-10, IR-2, IR-4`. | `PDF 230 / footer 229` |
| `TH-4` | None of `Generator`, `Predictor`, `MechanicalDeductor`, `FixedSearch`, `Learner`, or `Computer` entails `OCA`. | `MS-3–MS-6, SC-2, SC-4, DF-1–DF-4, DF-15–DF-20, DP-1, DP-3, IR-4`. | `PDF 230 / footer 229` |
| `TH-5` | `UniversalConstructor(C,D)` does not entail `OCA(C)` and does not entail `GCD(C)`. | `MS-3–MS-5, SC-2, SC-4, DF-1–DF-4, DF-12, CT-1–CT-6, DP-3, DP-11, IR-4`. | `PDF 230 / footer 229` |
| `TH-6` | `OCA(s,...)` does not entail `UniversalConstructor(s,D)`. | `MS-1–MS-5, SC-2, SC-4, DF-1–DF-4, CT-1–CT-6, IR-4`. | `PDF 230 / footer 229` |
| `TH-7` | For any finite external trace compatible with `OCA` or `GCD`, there is an externally trace-equivalent model in which outputs are supplied by a finite lookup/preadapted mechanism and `Authors` is false; the converse model can share the same trace while satisfying authorship. | `MS-1–MS-7, SC-2–SC-4, SC-8, DF-1–DF-7, DF-7a, DF-12, DF-18, DP-3, IR-4`, with transitive expansion under `IR-6`. | Statement `PDF 230 / 229`; dependency `PDF 231 / 230` |
| `TH-8` | Under `AB-1`, heritable variation plus differential replication can yield `K_CT`; neither `OCA`, `CCP`, nor `K_E` follows. | `MS-3–MS-8, SC-2, SC-4, SC-8, DF-1–DF-7, DF-7a, DF-21, CT-1–CT-7, DP-10, AB-1, IR-1, IR-4`, with transitive expansion under `IR-6`. | `PDF 231 / footer 230` |
| `TH-9` | Natural selection does not entail problem-bearing criticism. A critical process may use selection among ideas, but its selection is semantically constrained by represented problems and reasons; biological differential replication need have neither. | `MS-3–MS-8, SC-2, SC-4, SC-8, DF-1–DF-7, DF-7a, DF-21, CT-1–CT-7, DP-5, DP-10, AB-1, IR-1, IR-4, IR-6`. | `PDF 231 / footer 230` |
| `TH-10` | `K_CT` does not entail `K_E`, and `K_E` does not entail `K_CT` at an arbitrary declared persistence horizon. | `MS-8, CT-5, CT-7, RC-1, RC-2, IR-4`. | `PDF 231 / footer 230` |
| `TH-11` | `GoodNow` does not entail `True`; `HTV` does not entail `WideReach_D`; and `WideReach_D` does not entail `HTV` or truth. | `MS-5, MS-6, MS-8, SC-5, DF-8, DF-9, DF-14, DP-1, DP-4, DP-6, IR-4`. | Statement `PDF 231 / 230`; dependency `PDF 232 / 231` |
| `TH-12` | No finite set of `OCA`, `CCP`, or `EKC` episodes entails `GCD` or `UED`. | `MS-1, MS-4, MS-7, SC-3, SC-4, SC-8, DF-4, DF-7a, DF-7, DF-10–DF-13, IR-4`, with transitive expansion under `IR-6`. | `PDF 232 / footer 231` |
| `TH-13` | `UniversalComputer_F` does not entail `GCD`. | `MS-3–MS-7, SC-2–SC-4, SC-8, DF-1–DF-7, DF-7a, DF-12, DF-18, DF-20, DP-3, DP-9, IR-4`, with transitive expansion under `IR-6`. | `PDF 232 / footer 231` |
| `TH-14` | If one map `ρ` satisfies `BR-1–BR-7`, a named `Θ` admits the physical histories/interventions, and the realized abstract history satisfies `OCA`, then `PhysOCA_Θ,ρ`; analogously, all eight bridges plus robust `GCD` entail `PhysGCD_Θ,ρ`. | `SC-6, DF-4, DF-12, DF-22, DF-23, BR-1–BR-8, IR-2, IR-5`. | `PDF 232 / footer 231` |
| `TH-15` | Under six independently displayed assumptions—`UED(s,D_E,χ)`; task-specific correct `π_T`; an epistemic route to create/reconstruct, check, retain, and deploy it; a uniform programmable-constructor network; required resources; and `BR-1–BR-8` for one boundary/map—the system plus network/resources qualifies as a universal constructor over `D_C`. | `DF-13, CT-1–CT-6, DP-8, DP-9, DP-11, BR-1–BR-8, displayed premises 2–5, IR-1, IR-3, IR-5`. | Premises `PDF 232 / 231`; conclusion/dependency `PDF 233 / 232` |
| `TH-16` | The signature, structure, satisfaction clauses, and definitions admit a model containing no `OCA`, `OCap`, `CCP`, `EKC`, or `GCD` instance. | `TY-1–TY-3, MS-1–MS-9, SC-1–SC-8, DF-1–DF-23 including DF-4a and DF-7a, IR-4`. | `PDF 233 / footer 232` |
| `TH-17` | `OCA(s,x,...)` does not entail `New_H^L(x)`. | `MS-3, MS-4, SC-2, SC-4, DF-2–DF-4, IR-4`. | `PDF 233 / footer 232` |

## Explicit non-derivability boundary

Model §9 says CR-1.0 does not derive the following absent named additional premises (`PDF 233–234 / footers 232–233`). These are unnumbered `DER`-type non-entailment obligations, not accepted results in this map: they have no individual identifiers, no individual dependency certificates, and no countermodels attached in §9.

| Unnumbered boundary claim |
|---|
| the existence of any actual creator, person, or AGI |
| an algorithm that generates conjectures or decides `Explains`, `HTV`, `K_E`, or authorship |
| that creativity, intelligence, consciousness, free will, personhood, and moral status are equivalent |
| that any current AI system is or is not an AGI from outputs alone |
| that creativity is noncomputable, quantum, random, biologically unique, or substrate-free |
| that a good/current explanation is true, probable, final, simple, elegant, or guaranteed wide reach |
| that every artwork or artistic act is an explanation-class instance; non-explanatory artistic creativity requires the independently declared aesthetic extension in `RC-3` |
| that all `K_CT` is explanatory, or all `K_E` is physically resilient |
| that natural selection is rational criticism, purposive at the population level, or universally explanatory |
| that universal computation, an information medium, a constructor, or a universal constructor is a creator |
| that a creative episode or bounded competence yields `GCD`, `UED`, or open-ended progress |
| that abstract satisfiability makes the creative organization physically possible |
| that constructor theory supplies meanings, problem identity, explanation quality, authorship, or thinking |
| that *The Fabric of Reality* has a fifth strand or that a completed standalone constructor theory of knowledge presently exists |

The closing application condition in §9 is likewise substantive: actual attribution requires empirical facts about boundaries, representations, causal provenance, reason-specific interventions, memory, resources, and robustness in addition to `BR-1–BR-8` (`PDF 234 / footer 233`). It is unnumbered and therefore unavailable to a machine dependency closure until separately declared.

## Source dependency identifiers used by the core

The following source identifiers occur in the Model §0 registry; many are cited by one or more core declarations. Their bibliographic and entitlement details belong in the separate source registry; this map records only the exact source-identifier namespace exposed by the Model.

| Source family | Exact identifiers |
|---|---|
| *The Beginning of Infinity* | `S-BOI1`, `S-BOI3`, `S-BOI4`, `S-BOI6`, `S-BOI7`, `S-BOI10`, `S-BOI14`, `S-BOI15`, `S-BOI16` |
| *The Fabric of Reality* | `S-FOR1`, `S-FOR3`, `S-FOR8`, `S-FOR10`, `S-FOR12`, `S-FOR13` |
| *The Science of Can and Can't* | `S-SCC3`, `S-SCC5`, `S-SCC7` |
| Constructor-theory papers | `S-CT13`, `S-CTI15`, `S-CTL15` |
| Other primary/public source entries | `S-CB12`, `S-MAI20` |

Registry locators: `PDF 219–221 / footers 218–220`.

## Earlier source-facing definitions and disciplines relevant to the core

These earlier passages help interpret the Model but are not higher-authority formal declarations. They do not enter a proof merely because they precede the Model. Any substantive use requires a numbered core `IMP`, `DEF`, or later `DER` dependency.

| Earlier passage | Exact or close line-break-normalized content relevant to CR-1.0 | Core concordance | Locator and audit status |
|---|---|---|---|
| Part I §2.1, shortest definition | “The Beginning of Infinity defines creativity as the capacity to create new explanations.” The report then separates origin, critical process, and knowledge creation, and later adds stable general and universal dispositions. | `DF-4a` is explicitly called the direct modal counterpart; `DF-4`, `DF-7`, `DF-10`, `DF-12`, `DF-13` separate the other levels. | `PDF 16–17 / footers 15–16`; source synthesis only. |
| Part I §2.2, conjectural origin | New explanatory content is not derived from observations or predicted by prior knowledge, but this is not a claim of physical uncausedness, supernatural origin, or independence from earlier ideas. | `DP-2`, `OM-2`; forbidden `data→theory by induction`. | `PDF 17 / footer 16`; source synthesis only. |
| Part I §2.3, non-sufficiency contrasts | Induction, sensory instruction, novel output, valuable/adapted output, randomness, mechanical deduction, imitation, complexity/scale, fixed-objective optimization, natural selection, and constructorhood are rejected as sufficient substitutes. | `DF-15–DF-21`, `DP-3`, `DP-10`, `DP-11`, `TH-4`–`TH-9`, `TH-13`. | `PDF 17–18 / footers 16–17`; source synthesis only. |
| Part I §3.1, problem cycle | `P_0 → TT_1, TT_2, … → EE → P_1`; the conjecture arrow is a licensed creative move, not a truth-preserving inference; problems, standards, tests, and criticisms can themselves be criticized. | `OM-1`–`OM-10`, especially `OM-2` and `OM-8`; `DP-2`, `DP-4`, `DP-5`, `DP-7`. | `PDF 18–19 / footers 17–18`; source synthesis only. |
| Part I §3.2, anti-induction | No legal rule `many observed As are B ⊢ ∀x(Ax→Bx)`. Statistical inference may occur inside an explanatory model but does not create or positively justify that model’s interpretation. | `DP-2`, `IR-8` forbidden list. | `PDF 19 / footer 18`; source synthesis only. |
| Part I §3.3–§3.4, criticism and fallibilism | Observation is not self-interpreting; tests discriminate only under rival explanations, background assumptions, and an account of the setup; surviving a test removes or weakens criticisms, not certainty or probability. | `SC-3`, `DF-5`, `DF-6`, `DP-4`, `DP-5`, `OM-4`, `OM-5`, `OM-7`. | `PDF 19 / footer 18`; source synthesis only. |
| Part I §4.1, explanation | `Explains(e,p,b)` is substantive and not shorthand for predictive accuracy; the sources provide diagnostics and examples rather than a complete truth-conditional definition. | `MS-5`, `SC-5`, `DP-1`. | `PDF 19–20 / footers 18–19`; source synthesis only. |
| Part I §4.2, hard to vary | Hard-to-vary is relative to the target problem, background, content-equivalence level, and variation family; it is not short description length, syntactic rigidity, unwillingness to edit, predictive accuracy, or a scalar truth certificate. | `DF-8`, `DF-9`, `DP-6`. | `PDF 20 / footer 19`; source synthesis only. |
| Part I §4.4, reach | Reach follows from explanatory content, is not acquired inductively, and is not identical to goodness; wide false claims and good local explanations are possible. | `MS-6`, `DF-14`, `TH-11`. | `PDF 20 / footer 19`; source synthesis only. |
| Part I §5, four universalities | Representation, computation, construction, and explanation are distinct universality domains. Cross-domain bridges are substantive; universal computation does not identify the creative program, and universal construction does not imply invention of programs. | `DF-13`, `DF-20`, `CT-6`, `DP-8`, `DP-9`, `DP-11`, `TH-5`, `TH-6`, `TH-13`, `TH-15`. | `PDF 20–21 / footers 19–20`; source synthesis only. |
| Part I §6.1, intelligence | “general intelligence ≈ a domain-general disposition to create, criticize, and improve explanations.” The approximation sign is expressly said to record a synthesis, not a formal identity. | No intelligence predicate is declared in CR-1.0; nearest formal profile is `GCD`, with `UED` stronger. | `PDF 21 / footer 20`; audit-only interpretive concordance. |
| Part I §6.2–§6.3, AGI and behavior | AGI is not benchmark aggregation; finite behavior underdetermines a creative process, lookup, script, or designer-supplied knowledge, and must be interpreted through causal architecture, provenance, counterfactual response, memory, and problem formation. | `SC-3`, `SC-4`, `DP-3`, `DP-8`, `TH-7`, §9 boundary. | `PDF 21–22 / footers 20–21`; source synthesis only. |
| Part I §7, natural selection | Biological variation/selection and conjecture/criticism share an abstract schema but differ in problem representation, selection, intermediates, preserved units, reach, and whether the author survives rejected variants. | `DF-21`, `DP-10`, `AB-1`, `TH-8`, `TH-9`. | `PDF 22–23 / footers 21–22`; source synthesis only. |
| Part I §8, art and reason | Artistic and scientific progress share a broad conjecture-and-criticism process, but objective beauty is an added conjecture and the semantic core does not entail aesthetic realism. | `RC-3`; no automatic art classification. | `PDF 23–24 / footers 22–23`; source synthesis only. |
| Part I §10.1, constructor vocabulary | Defines substrate, attribute, variable, task, constructor, possible/impossible task, information variable/medium, interoperability, programmable constructor, and physical knowledge. | `CT-1`–`CT-7`. | `PDF 25 / footer 24`; source synthesis/physical vocabulary. |
| Part I §10.3, two knowledge predicates | Displays `K_CT(i,e,ρ,τ)` and `K_E(x,p,b)` and says neither is reducible to the other by definition. | Model §1.2 later displays `K_E(x,p,b,h,t)`; the arity change is unresolved. | `PDF 26 / footer 25`; direct signature conflict recorded below. |
| Cross-book “Independent-import ledger” | Lists objective/explicable reality, universal physical laws, physical/computational realization, Popperian epistemology, evolution, emergent causal explanation, objective moral/aesthetic truth, institutions, digital error correction, and physical measure as not “defined into truth.” | Supports treating substantive premises as `IMP`, not `DEF`. It is not a numbered core ledger. | `PDF 70–71 / footers 69–70`; `[R]` reconstruction, audit/context only. |
| Cross-book “Dependency ledger” | Gives prose dependencies for observation/refutation, current goodness, physical knowledge, created knowledge, creativity, AGI/personhood, reach, universality, universal construction, progress, art, institutions, and probability. | Useful terminology concordance, but exact Model §8 `Depends exactly on` lines have higher conformance authority. | `PDF 71–72 / footers 70–71`; `[R]` reconstruction, audit/context only. |
| Cross-book “Licensed moves and forbidden shortcuts” | Permits data-to-criticism only through causal interpretation, problem-to-conjecture without entailment, tentative retention after criticism, reach derivation with content preserved, bridge-dependent cross-level moves, and rejects automatic successor generation and cross-universality slides. | Closely anticipates `OM-*`, `IR-*`, and the forbidden list, but is not the Model’s exact rule set. | `PDF 72–73 / footers 71–72`; `[R]` reconstruction, audit/context only. |

## Ambiguity and audit-only ledger

No entry below is a repair. “Blocking” means a cold-start typed parser or dependency checker cannot uniquely encode the authoritative clause without an explicit later decision.

| Audit ID | Issue preserved from the PDF or PDF/handoff comparison | Exact locator | Bootstrap effect |
|---|---|---|---|
| `CM-A01` | The PDF gives no `DEF`/`IMP`/`DER` class for primitive sort declarations, tuple members, or legal rules. They are mapped here as `IMP` candidates only because they are non-eliminable. | Model §1, §5–§6, `PDF 221–228 / footers 220–227` | Blocking classification question unless the inferential-status policy explicitly covers signature and rule declarations. |
| `CM-A02` | Report-wide source statuses (`D,X,Q,R,P,CT,E,T,N`) differ from Model §0 source marks (`X,R,M,Q,O`). The two systems are not given a formal translation. | `PDF 13 / footer 12`; Model §0, `PDF 219 / footer 218` | Blocking for a single source-status field; must preserve both vocabularies or record scope. |
| `CM-A03` | The canonical many-sorted signature has no `Event` sort, yet `E(h,t)` supplies typed events and `SC-1` quantifies an event `e`. | Model §1.1–§1.3, `PDF 221–222 / footers 220–221` | Blocking unresolved sort. |
| `CM-A04` | No canonical sorts are declared for intervals, boundaries, equivalence levels, problem/rival/variation classes, enabling conditions, domains, response types, endpoint problem situations, physical theories, realization maps, perturbation classes, horizons, populations, distributions, metrics, programs, or function/classes. Symbols using them include `I,B,L,Q,A,V,χ,D,α,y,Θ,ρ,τ,P,μ,m,f,F`. | Model §1–§7, `PDF 221–229 / footers 220–228` | Blocking unresolved variables and arities. |
| `CM-A05` | `AttemptExp`, `Criticism`, `Standard`, and `Problem` are declared sorts but also “semantic roles of contents” that need not be mutually exclusive. Standard disjoint-sorted semantics is not reconciled with overlapping role membership or coercions to `Content`. | Model §1.1, `PDF 221 / footer 220` | Blocking domain-overlap/coercion rules. |
| `CM-A06` | `Rep(s,z,h,t)` is described as relating a token/state to content `z`, but the displayed four-place application has no token/state argument. `SC-2` introduces `Represents(s,z)` without formally linking it to `Rep`. | `MS-3`, `SC-2`, `PDF 222 / footer 221` | Blocking signature and elaboration ambiguity. |
| `CM-A07` | `Prov`, `CF`, `SameJob`, `Var_V`, `Pref`, `Cost`, and the codomains of `B`, `E`, `R`, and `Mem` have no complete signatures. `Pref` is said to be time-indexed without an argument list. | `MS-2`, `MS-4`, `MS-6`, `MS-7`, `MS-9`, `PDF 221–222 / footers 220–221` | Blocking unresolved arities/codomains. |
| `CM-A08` | Satisfaction indexing and object signatures drift: `SC-4` uses `M,h,I \|= Authors_s(x,p)` but `DF-4` calls `Authors_s(x,p)` inside an `OCA(...,h,t)` body; `SC-7` uses `Retained_s(x)` at satisfaction index `(h,t)` while `DF-10` calls `Retained_s(x,h,t_I)`; `SC-8` places `h,I` both in the satisfaction index and inside `CLine`. | `PDF 222–224 / footers 221–223` | Blocking arity/context convention. |
| `CM-A09` | `DF-6` defines `Uptake(s,c,x,α,h,t,t')` by saying `PBCrit` holds at `t`, but `PBCrit(s,c,x,p,b,k,t)` requires `p,b,k`; those variables are absent and not existentially bound in `DF-6`. | `DF-5`, `DF-6`, `PDF 223 / footer 222` | Blocking free-variable/dependency ambiguity. |
| `CM-A10` | `DF-7a` says there exist `x_0,x_1,c,k,alpha` in interval `I` but then uses `t_0,t_1,t_2` without quantifying them. It does not type `alpha` or `y`, and “endpoint `y` and the resulting problem situation” permits materially different readings of `y`. | `DF-7a`, `PDF 223–224 / footers 222–223` | Blocking quantifier and sort ambiguity. |
| `CM-A11` | Several clauses called eliminable definitions contain undeclared natural-language tests or quantifiers: “conflict/inadequacy,” “could deploy,” “material,” “generally,” “additional explanatory work,” “currently undefeated,” “applicable,” “supports,” “same organization,” “physically admitted,” “no fixed subdomain restriction,” and “coverage condition.” | `DF-1`, `DF-3`, `DF-4a`, `DF-8`–`DF-14`, `PDF 223–224 / footers 222–223` | Blocking exact unfolding unless primitives are separately imported; `DEF` status remains only a candidate. |
| `CM-A12` | `DF-13` is presented as a semantic definition but quantifies over “physically admitted” problems. No named bridge appears in the displayed body despite `TY-3` requiring one for cross-type inference. | `TY-3`, `DF-13`, `PDF 221,224 / footers 220,223` | Blocking semantic-to-physical layer crossing. |
| `CM-A13` | `DF-14` defines `XReach(x)` as a set of pairs for which `Reach(...)` “follows from” explanatory commitments. This mixes object-level semantic structure with metalevel consequence, while set and coverage-condition types are absent. | `DF-14`, `PDF 224 / footer 223` | Blocking level/signature ambiguity. |
| `CM-A14` | Part I displays `K_E(x,p,b)` while Model §1.2 and §3 reserve `K_E(x,p,b,h,t)`. The Model has higher authority, but the earlier definition is a real arity conflict that must remain in the record. | Part I §10.3, `PDF 26 / footer 25`; `MS-8`, `PDF 222 / footer 221`; Model §3, `PDF 225 / footer 224` | Blocking concordance issue; preserve Model arity 5 for conformance. |
| `CM-A15` | `ρ` denotes the perturbation class in `K_CT(i,e,ρ,τ)` but denotes the abstract/physical realization map in `BR-*`, `DF-22`, and `DF-23`. | Model §3, `PDF 225 / footer 224`; §7.2, `PDF 228–229 / footers 227–228` | Blocking overloaded symbol unless scope disambiguates it. |
| `CM-A16` | `CT-5` combines eliminable-looking vocabulary (“information variable,” “information medium”) with the substantive interoperability principle under one identifier. | `CT-5`, `PDF 228 / footer 227` | Atomic `DEF` versus `IMP` classification is unresolved; `inferential_status` remains `null`. |
| `CM-A17` | `CT-1`–`CT-7` are called “exact physical vocabulary,” but the report-wide `CT` status explicitly covers “definition, principle, or subsidiary-theory claim.” The Model does not separate every internal definition from every world-restricting commitment. | Report-wide status table, `PDF 13 / footer 12`; Model §7.1, `PDF 228 / footer 227` | Procedural candidates are `DEF` for `CT-1`–`CT-4` and `CT-6`, `IMP` for primitive `CT-7`, and `null` for mixed `CT-5`; physical-module elaboration remains blocking. |
| `CM-A18` | `RC-2` states `K_CT→K_E` is false before `TH-10` later claims that non-entailment with dependencies. If `RC-2` is an `IMP`, `TH-10` partly assumes what it claims; if it is a `DER`, §3 supplies no certificate. | `RC-2`, `PDF 225 / footer 224`; `TH-10`, `PDF 231 / footer 230` | Blocking dependency/circularity audit for `TH-10`; no theorem adjudication here. |
| `CM-A19` | `DP-8` mixes `X` and `Q`; `DP-9` mixes `X` and `O`; `DF-13` mixes `X/R/Q`. One identifier therefore contains source-backed, reconstructed, conjectural, or open-program material that a source-status-driven importer cannot atomically classify. | `DF-13`, `PDF 224 / footer 223`; `DP-8`, `DP-9`, `PDF 226 / footer 225` | Blocking atomic source-status issue. No clause split is proposed here. |
| `CM-A20` | `PhysOCA_Θ,ρ(U,...)` contains a literal ellipsis, so `DF-22` has unresolved arity. `DF-23` calls `GCD(U,Q,χ)` although `GCD` expects a `Sys` in its first position and `U` was introduced as a physical region/history component. | `DF-22`, `DF-23`, `PDF 229 / footer 228` | Blocking physical-definition typing. |
| `CM-A21` | `BR-7` is conditional on whichever abstract role is asserted, yet `DF-22` requires all `BR-1–BR-7` for a bare `OCA`. The text says a bare `OCA` imports no criticism or retention, but no formal parameterization of `BR-7` exposes which subconditions apply. | `BR-7`, `DF-22`, `PDF 229 / footer 228` | Blocking bridge elaboration ambiguity. |
| `CM-A22` | `IR-1` admits “ordinary mathematical reasoning” within a module without enumerating the mathematical axioms/rules. `IR-3` admits finite-history induction without stating an induction schema or well-founded history measure. | `IR-1`, `IR-3`, `PDF 227 / footer 226` | Blocking trusted-kernel boundary. |
| `CM-A23` | The procedural handoff strengthens `IR-3` by requiring the induction principle to be declared; the PDF does not contain that condition. The PDF form controls conformance, and the handoff addition must not be silently inserted. | Model `IR-3`, `PDF 227 / footer 226`; handoff Part 1A, “Metalevel legal moves” | Recorded PDF/handoff conflict. |
| `CM-A24` | The procedural handoff renames exact PDF object moves: PDF has `Reject/Revise`, `Reframe/Restandardize`, and `Record/Reconstruct/Iterate`; the handoff uses normalized CamelCase names. | Model §5, `PDF 227 / footer 226`; handoff Part 1A, “Object-level legal moves” | Preserve PDF identifiers/names; normalization is not authoritative. |
| `CM-A25` | The handoff adds baseline words and categories not present in PDF `TY-2` (for example history, rival class, domain, tolerance, “stable,” and “authored”) and omits none of the PDF’s authority by right. | `TY-2`, `PDF 221 / footer 220`; handoff Part 1A, “Logical form” | Preserve exact PDF baseline law; additional handoff checks are procedural, not semantic clauses. |
| `CM-A26` | Model §8 dependency ranges use nonstandard identifier interval syntax around inserted suffixes, for example `DF-1–DF-4a`, `DF-1–DF-7` followed separately by `DF-7a`, and “DF-1–DF-23 including DF-4a and DF-7a.” | `TH-1`, `TH-2`, `TH-7`–`TH-9`, `TH-13`, `TH-16`, `PDF 229–233 / footers 228–232` | Parser must preserve the textual ranges; exact range expansion is an audit decision. |
| `CM-A27` | `TH-15` depends on “displayed premises 2–5,” which have no stable identifiers. Premises 1 and 6 are represented by `DF-13` and `BR-1–BR-8`, but the middle imports cannot be transitively addressed by ID. | `TH-15`, `PDF 232–233 / footers 231–232` | Blocking dependency-identity issue; no IDs are invented here. |
| `CM-A28` | The §9 non-derivability boundary contains fourteen separate metaclaims without identifiers, direct dependency lines, or certificates. | Model §9, `PDF 233–234 / footers 232–233` | Audit-only `DER` obligations; unavailable as reusable results until adjudicated and identified. |
| `CM-A29` | The unnumbered R/M task-network reconstruction following `DF-23` contains substantive realization commitments but no declaration identifier or inferential status. | Model §7.2, `PDF 229 / footer 228` | Cannot enter a checked dependency closure. |
| `CM-A30` | Earlier cross-book synthesis says “a system is creative” if it can originate explanatory knowledge across open-ended problems using conjecture and criticism, which is stronger than the shortest modal definition and closer to `GCD/UED`. The passage is expressly `[R]`, not the formal Model definition. | `PDF 71 / footer 70`; Model `DF-4a`, `DF-12`, `DF-13`, `PDF 223–224 / footers 222–223` | Interpretive ambiguity only; Model predicates remain separated. |
| `CM-A31` | Earlier “licensed moves” allows `Conjecture → tentative knowledge` after surviving serious criticism and being best available. The Model instead keeps `K_E` primitive and makes `ReasonedRetain` insufficient by itself. | `PDF 72 / footer 71`; `MS-8`, `OM-7`, `DF-10`, `PDF 222,224,227 / footers 221,223,226` | Earlier `[R]` table cannot be imported as an inference rule. |
| `CM-A32` | The core says every use of “owned” displays its boundary baseline, yet `Authors_s(x,p)` has no boundary argument; the boundary appears only in the satisfaction prose as “predeclared.” Similar hidden baselines occur in `SameJob`, `Pref`, and constructor ability. | `TY-2`, `SC-4`, `MS-6`, `CT-3`, `PDF 221–222,228 / footers 220–221,227` | Baseline representation is not machine-explicit. |
| `CM-A33` | `DF-20` calls physical realization inside an eliminable contrast-class definition without specifying a physical theory, realization relation, bridge, or tolerance, despite `TY-3`, `SC-6`, and `IR-5`. | `DF-20`, `PDF 225 / footer 224`; `TY-3`, `SC-6`, `IR-5` | Blocking hidden physical import in a `DEF` candidate. |
| `CM-A34` | `DF-21` uses `E` for environment while tuple member `E(h,t)` is the event map. The scopes differ in prose, but a concrete syntax must disambiguate the same symbol. | `MS-2`, `DF-21`, `PDF 221,225 / footers 220,224` | Lexical overload. |
| `CM-A35` | The report states that each §8 dependency line is exhaustive, but definitions and several supporting unnumbered clauses have no exhaustive dependency certificates. No claim that the displayed theorem lists are actually closed is accepted in this map. | Model §8 opening, `PDF 229 / footer 228`; definition and unnumbered clauses throughout `PDF 223–234` | Deferred to dependency audit; no theorem proof performed. |

## Map completion statement

This map covers every numbered declaration family in Model CR-1.0 (`TY`, `MS`, `SC`, `DF`, `RC`, `DP`, `AB`, `OM`, `IR`, `CT`, `BR`, and `TH`), the exact canonical sort list, every tuple symbol, the explicit forbidden transformations, the unnumbered §9 non-derivability boundary, all displayed `TH-*` dependency lines, and the earlier source-facing definitions that materially constrain interpretation. It deliberately leaves the thirty-five recorded ambiguities unresolved and keeps every `TH-*` result unavailable with `inferential_status: null` and `target_status: DER`.
