# CR-EIB 0.2 DF-7a / CCPWitness mapping design

> **UNREVIEWED — NON-AUTHORITATIVE DESIGN ONLY.**
>
> This document is not a source anchor, mapping record, declaration record,
> choice-registry entry, Lean declaration, or acceptance decision. It is not
> verifier input. It records source-led questions for human semantic review.

## Status

| Field | Value |
|---|---|
| Document class | Source-led mapping design note |
| Mapping fidelity | `UNREVIEWED` |
| Authority status | `NON-AUTHORITATIVE` |
| Accepted reading | None |
| Accepted loss or addition | None |
| Executable effect | None |
| Current port status | `CCPResult` remains opaque |
| Permitted next use | Human review of the source readings and open questions |

Nothing in this file authorizes a change to `authority/source_anchors.json`,
`bridge/declarations/`, `formal/`, or the interpretation-choice registry.
The locator observations below must be independently checked and promoted
through the repository's normal authority process before they can become a
canonical source anchor.

## Authority-byte binding for this inspection

| Property | Inspected value |
|---|---|
| Document ID | CR-1.0 |
| Supplied filename | `Creativity_Semantic_Model_CR-1.0(1).pdf` |
| SHA-256 | `08ff81e848fea976b558345402d85723173be8f40f1041fb00d6267f1e026b8b` |
| Byte length | `1,734,769` |
| Page count | `286` |
| Page geometry | `612000 × 792000` millipoints, rotation `0` |
| Locator coordinate system | Top-left CropBox millipoints |
| Text geometry inspected with | `pdftotext -bbox` 24.02.0 |
| Page metadata inspected with | `pdfinfo` 26.05.0 |
| Visual check | Rendered physical PDF pages 221–224, reviewed against printed footers |

This byte binding identifies the source inspected for the design. It does not
make the design authoritative and does not certify an interpretation.

## Exact design-time locator observations

The rows below are read-only locator observations, not serialized source
anchors. Bounding boxes are rounded to integer millipoints from the inspected
`pdftotext -bbox` output.

| Source region | Physical PDF page | Zero-based index | Printed footer | Section | Bounding box | Contextual role |
|---|---:|---:|---:|---|---|---|
| MS-4 | 222 | 221 | 221 | 1.2 Abstract model | `[54000, 102159, 560230, 199155]` | Upstream meaning of provenance and `CLine`; says its causal relations are substantive model imports |
| MS-6 | 222 | 221 | 221 | 1.2 Abstract model | `[54000, 249884, 559674, 297147]` | Upstream typing and meaning of `CritOf` and `BearsOn`, used by `PBCrit` |
| SC-2 | 222 | 221 | 221 | 1.3 Satisfaction clauses | `[54000, 502849, 558008, 537678]` | Representation requires a discriminable token/state plus an operation that uses the relevant difference |
| SC-3 | 222 | 221 | 221 | 1.3 Satisfaction clauses | `[54000, 545628, 559702, 592891]` | Causal-uptake context for `UsesReason`, including intervention-sensitive content preservation |
| SC-4 | 222 | 221 | 221 | 1.3 Satisfaction clauses | `[54000, 600841, 558008, 660537]` | Authorship context used by `OCA`; excludes mere retrieval and externally prepared selection |
| SC-7 | 223 | 222 | 222 | 1.3 Satisfaction clauses | `[54000, 59379, 559679, 94209]` | Upstream comparison point for retention and later accessibility; not automatically identical to DF-7a availability |
| SC-8 | 223 | 222 | 222 | 1.3 Satisfaction clauses | `[54000, 102159, 559688, 174288]` | Upstream necessary conditions on critical lineage, provenance, matched counterfactuals, causal roles, and endpoint |
| DF-4 / `OCA` | 223 | 222 | 222 | 2. Eliminable semantic definitions | `[54000, 404861, 557991, 480597]` | Direct definition used by DF-7a condition 1 |
| DF-5 / `PBCrit` | 223 | 222 | 222 | 2. Eliminable semantic definitions | `[54000, 569762, 559008, 657572]` | Direct definition used by DF-7a condition 2 |
| DF-6 / `Uptake` | 223 | 222 | 222 | 2. Eliminable semantic definitions | `[54000, 665880, 559581, 700710]` | Direct definition used by DF-7a condition 3 |
| DF-7a opening | 223 | 222 | 222 | 2. Eliminable semantic definitions | `[54000, 708660, 558001, 731056]` | Target predicate and existential introduction; continues on the next physical page |
| DF-7a conditions 1–5 | 224 | 223 | 223 | 2. Eliminable semantic definitions | `[54457, 59379, 558232, 131509]` | Five source conditions that a reviewed mapping would have to address |
| DF-10 | 224 | 223 | 223 | 2. Eliminable semantic definitions | `[53671, 284853, 558013, 387170]` | Downstream compatibility check only; forbidden as an input for choosing DF-7a meaning |

The DF-7a source span is therefore discontinuous across a page boundary. Any
future anchor would need to represent both regions without absorbing DF-7,
which begins below the conditions on physical page 224.

## Direction of semantic influence

| Role in this design | Source material | Rule |
|---|---|---|
| Target | DF-7a | Interpret only after reading the bound PDF regions and their upstream source context |
| Upstream context | MS-4, MS-6, SC-2, SC-3, SC-4, and SC-8 | Constrain the directly invoked predicates and critical lineage; preserve their causal, representational, authorship, and counterfactual burden |
| Direct definitions | DF-4, DF-5, and DF-6 | Supply the located source definitions of `OCA`, `PBCrit`, and `Uptake`; a mapping may not replace them with theorem-convenient ports |
| Comparison requiring a decision | SC-7 | Supplies the source's retention notion, but DF-7a does not explicitly identify endpoint availability with retention |
| Downstream consumers | DF-7, DF-10, TH-3, and the current Lean pilot | May reveal incompatibility after a reading is selected; may not select or revise the reading |

Proof convenience is quarantined from source interpretation. In particular, a
reading is not preferred because it makes DF-10 easy to unfold, makes a TH-3
countermodel possible, or fits the current opaque `CRModel`. A proof failure
may expose an inconsistency in a proposed bridge, but it cannot change what the
PDF means without renewed human source review.

## Source-led observations without a type decision

The following is a minimal paraphrase of the located source, not an accepted
formalization.

| Observation | What is explicit in the located source | What remains undecided |
|---|---|---|
| Result surface | DF-7a uses the surface predicate `CCPResult(s,y,p,b,h,I)` and existentially introduces `x_0`, `x_1`, `c`, `k`, and `alpha`. | The located opening does not supply a complete typed binder list for those symbols or for the later `t_0`, `t_1`, and `t_2`. |
| Origin | Condition 1 requires an `OCA` occurrence involving `x_0` at `t_0`. | The interval-membership and order relation for `t_0` are not stated locally. |
| Criticism and descent | Condition 2 uses the narrow phrase “`x_1=x_0 or a lineage descendant of it`” with `PBCrit` at `t_1`. | Lineage descent is not locally defined as graph reachability, content revision, or another relation. |
| Uptake | Condition 3 requires `Uptake` involving `c`, `x_1`, `alpha`, `t_1`, and `t_2`. | Any temporal consequences must come from a reviewed mapping of `Uptake`, not from adding a convenient global order here. |
| Critical lineage | Condition 4 requires the same participants and endpoint in `CLine`. MS-4 places the attempt, response, and endpoint in one causal episode; SC-8 imposes a predeclared provenance subgraph, matched counterfactuals, and causal roles. | SC-8 states necessary conditions. Treating that list as a sufficient definition would strengthen the source. |
| Endpoint | SC-8 describes `y` as the endpoint produced by the response and allows retained, revised, rejected, or reframed outcomes. DF-7a additionally coordinates `y` with the “`resulting problem situation`”. | Whether these are two carriers, two roles of one carrier, or projections of a structured endpoint is unresolved. |
| Availability | DF-7a requires the endpoint and resulting problem situation to be represented and “`available for possible further conjecture`”. SC-7 characterizes retention by being “`accessible to a relevant possible later operation`”. | The lexical similarity does not establish `EndpointAvailable = Retained`, nor does it fix the system, history, or time arguments of representation and availability. |

SC-8 also rules out mere temporal co-occurrence and analyst-assigned topic
similarity as sufficient critical-lineage evidence. A mapping that records only
event order or a topic label would therefore erase an express source
restriction.

## Alternative endpoint and problem-situation readings

All alternatives in this table are `OPEN`. Listing one does not propose it.

| Alternative | Possible typed reading | What it preserves | Addition or loss risk |
|---|---|---|---|
| Separate content endpoint | `y` is a `Content`; a separate value or relation records the resulting `ProblemSituation`. | Keeps an endpoint content usable by DF-10 while representing the coordinated problem situation separately. | Adds a carrier/relation not bound in DF-7a and may over-read the grammar as ontological distinctness. |
| Problem-situation endpoint | `y` is a `ProblemSituation`; a projection or relation supplies endpoint content where later clauses need it. | Gives the problem-situation wording direct type priority. | Adds a content projection and risks letting downstream DF-10 requirements drive the source reading. |
| Structured endpoint | `y` denotes a structure containing endpoint content, problem situation, and their link. | Makes both roles explicit and prevents accidental identity. | Reifies structure absent from the surface syntax and may falsely imply total, unique projections. |
| One carrier with overlapping roles | `y` inhabits a common carrier with separate `Content` and `ProblemSituation` role evidence. | Respects the possibility that one object bears multiple semantic roles. | Introduces a common carrier and role predicates not stated in DF-7a. |
| Identity with the original problem context | The resulting problem situation is identified with, or derived only from, `p`. | Minimizes new carriers. | Risks erasing the source's result transition, conflating a problem with a problem situation, and excluding reframing. |

No alternative may be accepted by appealing to the existing proposed
`EIB-C-TY08` choice. That choice is downstream bridge material and is itself
reversible.

## Other unresolved readings

| Source question | Alternatives that require review | Main preservation risk |
|---|---|---|
| What does interval scope apply to? | The occurrence times are members of `I`; the entire causal episode is indexed by `I`; each witness has an occurrence-in-interval proof; or the grammar literally types the existential objects as interval members. | Converting episode scope into object membership, or omitting interval evidence entirely. |
| What temporal order is required? | Preserve only order already carried by reviewed `OCA`, `PBCrit`, and `Uptake` mappings; add an explicit partial order among `t_0`, `t_1`, and `t_2`; or use an episode trace that derives order. | Adding `t_0 ≤ t_1 ≤ t_2` without a source basis, or losing the direction internal to uptake. |
| What is a lineage descendant? | Reachability in the MS-4 provenance graph; a separate content-version relation; or a relation derived from reviewed `CLine` evidence. | Counting any temporal successor as a descendant, duplicating incompatible lineage relations, or failing to represent condition 2 separately. |
| How is SC-8 attached to `CLine`? | Keep `CLine` opaque with separately checked necessary obligations; carry explicit provenance and matched-counterfactual evidence; or define `CLine` by the listed conditions. | The last option changes a source necessary condition into a biconditional unless further authority supports it. |
| What is representation? | Reuse a reviewed `Represents` relation; retain a token-or-state witness; or introduce endpoint-specific representation evidence. | Booleanizing an evidential relation or inventing hidden time and system arguments without disclosure. |
| What is availability? | A distinct endpoint-availability relation; a reviewed consequence of SC-7 retention; or an explicit later-operation accessibility witness. | Collapsing availability into endorsement or `K_E`, or assuming equivalence with retention. |
| What is `alpha`? | An opaque response carrier; an event/process; or content produced by uptake. | Selecting a carrier only because it fits an existing Lean signature. |
| What is `k`? | A `Standard` carrier; content with standard-role evidence; or an opaque argument to `PBCrit`. | Losing the source role or assuming a disjoint carrier without review. |
| How are matched counterfactuals represented? | Explicit interventions and held-fixed conditions; an opaque reviewed evidence object; or an unstructured proposition. | Erasing the causal test into ordinary graph connectivity. |

## Open addition and loss register

Every row is `OPEN / UNACCEPTED`. The table records risks to be adjudicated,
not authorized deviations.

| Potential addition or loss | Why it matters | Required human question |
|---|---|---|
| Add binders and types for `t_0`, `t_1`, and `t_2` | The source conditions use them but the DF-7a opening does not bind them. | Are they existential times, fields of events, or supplied by an episode context? |
| Assign carriers to `x_0`, `x_1`, `c`, `k`, `alpha`, `y`, and `I` | Lean requires choices the local source syntax does not fully determine. | Which assignments are source-preserving, and which are explicit CR-EIB additions? |
| Interpret witness membership in `I` as occurrence-time membership | This is a plausible type repair but changes the grammar. | Does the interval scope the episode, the events, or the objects? |
| Add a global temporal chain | It may simplify proof obligations while strengthening the clause. | Which order facts are actually inherited from reviewed dependencies? |
| Collapse endpoint content and resulting problem situation | A single carrier simplifies DF-10 compatibility. | Does the coordinated source phrase express identity, association, or distinct roles? |
| Equate endpoint availability with SC-7 retention | Both concern later access, but only SC-7 explicitly defines retention. | Is equivalence, implication, or independence intended? |
| Turn SC-8's necessary conditions into a definition | A witness structure naturally looks definitional. | Is sufficiency stated anywhere in the authority, or must `CLine` remain a substantive port? |
| Erase provenance interventions or matched counterfactuals | Plain graph reachability is easier to mechanize. | What explicit evidence is required to retain the causal-credit test? |
| Reduce representation or availability to Boolean flags | Booleans hide witnesses, scope, time, and provenance. | What evidence object or relation must remain inspectable? |
| Forget SC-8's negative sufficiency restriction | Event order and topic similarity could otherwise pass a weak checker. | How will a later mapping prevent those proxies from satisfying critical lineage? |
| Infer DF-7a meaning backward from DF-10 or TH-3 | This would make theorem needs the semantic authority. | Has the reading been selected without consulting downstream proof success? |

No item in this register has a disposition. A future reviewed mapping must
either preserve it, accept and justify it as an explicit bridge choice, or keep
the mapping blocked.

## Coverage questions, not a CCPWitness schema

A later mapping review will need to ask whether its proposed representation
keeps all of the following inspectable: the existential participants; the three
time references; interval scope; the `OCA`, `PBCrit`, `Uptake`, and
`CLine` conditions; condition-2 descent; provenance and matched
counterfactual evidence; endpoint production; the resulting problem situation;
and representation and availability for later conjecture.

This paragraph does not define `CCPWitness`. It proposes no field names,
types, constructor order, equality, or Lean encoding. Completeness of that list
is itself subject to source review.

## Separation of review and proof

| Stage | Authorized result | Forbidden shortcut |
|---|---|---|
| Source-semantic review | Human dispositions for each alternative, with rationale tied to the bound PDF regions | Selecting the reading that makes a desired theorem easiest |
| Independent semantic check | Confirmation that upstream context and explicit negative restrictions were not erased | Treating reviewer agreement or an LLM score as a proof of meaning |
| Type-and-IR review | A typed proposal that labels every added binder, carrier, relation, strengthening, and loss | Treating successful elaboration as semantic acceptance |
| Canonical record work | Only after approval: separate source-anchor and mapping-record changes under their own review | Promoting this design note into verifier input |
| Mechanization | Only after an accepted mapping: a separately identified Lean declaration and proof obligations | Reusing the legacy opaque port as if it were the reviewed definition |
| Audit | A machine-checkable closure certificate plus a separately reported human fidelity verdict | Calling kernel success a source-fidelity verdict |

Machine checks can verify hashes, locator geometry, schema completeness, typed
closure, explicit dependency references, proof replay, and axiom use. They can
reject a mapping whose selected obligations are missing. They cannot decide the
types of `y` or `alpha`, decide whether availability is retention, supply
the meaning of lineage descent, or mark the mapping accepted.

## Current outcome

The only current outcome is a bounded design for review. Mapping fidelity
remains `UNREVIEWED`; bridge conformance remains blocked on accepted
source mappings; `CCPResult` remains an opaque port. This file creates no
mapping record, source anchor, Lean declaration, accepted choice, proof claim,
or provisional semantic fact.
