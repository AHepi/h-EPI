# Semantic Model Forge 0.1 research basis

**Research date:** 2026-09-03

**Status:** bounded external-source reports and unaccepted project-use proposals; non-authoritative

## Scope and authority

This note records the external methods considered while designing SMF-0.1. It does not supply semantics for creativity, problems, conjectures, criticism, explanation, authorship, knowledge, or physical realization. The sole semantic and formal authority remains the pinned CR-1.0 PDF identified by SHA-256 `08ff81e848fea976b558345402d85723173be8f40f1041fb00d6267f1e026b8b`.

CR-1.0 itself supplies the controlling non-inductivist constraints. Its anti-inductivist discussion in §3.2 rejects an observation-to-universal-law rule; Model CR-1.0's DP-2 rejects licensed inductive ascent from repeated instances; DP-4 keeps every explanation, criticism, standard, problem framing, proof method, and institution open to criticism; DP-5 says test survival removes a criticism rather than confirming a theory; and IR-4 uses typed countermodels for non-entailment. Those are authority constraints. The papers below suggest ways to engineer a workflow under those constraints, and nothing more.

The research questions were whether iterative refinement can be organized around concrete counterexamples without assuming every counterexample is genuine; whether questions can make a semantic class's intended scope and distinctions inspectable; how to test relations when exact output oracles are unavailable; where human semantic judgment remains necessary; and what failure modes arise when language models repeatedly generate and repair definitions.

## Evidence classes

| Evidence class | Permitted use in SMF | Prohibited use |
|---|---|---|
| CR-1.0 authority bytes | Constrain what the active model says and how its own source-status distinctions are preserved. | Silent repair or replacement by an engineering method. |
| Primary engineering paper | Motivate a candidate workflow, record an observed limitation, or suggest an instrument. | Decide a CR-1.0 semantic relation or establish epistemological truth. |
| Empirical study | Warn about behavior observed under the study's stated design. | Universalize the result to all models, concepts, prompts, or reviewers. |
| Search or discovery result | Locate the primary record. | Serve as evidence without inspection of the primary abstract or paper page. |
| LLM output | Propose questions, cases, interpretations, and repairs. | Act as a semantic authority, judge, vote, or closure mechanism. |

All retained reports and linked project-use proposals are therefore engineering inputs. None is an accepted engineering decision or a semantic authority.

Research-ledger v2 records AlphaXiv as the default discovery provider for contemporary work from 2024 onward, not as a mandatory route or an authority. That preference becomes operational only after a published v2 human action selects an external route and exact rival-falsifier attack-target IDs; the planner's target menu alone authorizes nothing. Direct primary-source discovery remains permitted, and Consensus is available only as an optional independent cross-check when a second discovery path would materially probe a result. All discovery providers are replaceable. Neither generated summaries nor rankings may support a retained report: the exact primary-source version named in the record must be inspected at its recorded primary locator. This routing preference changes convenience and provenance, not semantic authority.

## Research-ledger v2 provenance and status

The retained research state is `forge/research/SMF-RESEARCH-2026-09-03.json`, schema version `creib.semantic-forge.external-research-ledger.v2`. It separates three record roles that must not be collapsed:

| Record role | Current count and status | Permitted effect |
|---|---|---|
| External-source report | Eight entries; every `report_scope` is `source_claims_only` and every human-adjudication status is `UNREVIEWED`. | Preserve a project-authored, source-only paraphrase that may criticize or guide engineering. It cannot confirm target semantics. |
| Project-use proposal | Eight digest-bound records; every `proposal_status` is `PROPOSED`. | State a possible project use separately from what the cited source reports. Every proposal has `semantic_authority: false` and `can_promote_hardening: false`. |
| Engineering decision | Zero records; v2 requires `engineering_decisions` to remain empty. | No use has been accepted, rejected, or deferred. A future version needs an external human-attestation trust boundary before it may carry operative decisions. |

Each retained report records a canonical identifier and URL, an exact named version and versioned URL, publication year, as-of and retrieval dates, discovery route, and a primary-inspection locator, version, date, and inspected scope. The inspection version must match the canonical-source version. The bounded report has its own digest, the full entry has another digest, and each project-use proposal is bound to the exact source-entry digest. The source descriptions below paraphrase only the corresponding bounded reports; the possible SMF uses belong to the separate `PROPOSED` records.

The current ledger bindings are:

```text
ledger_sha256 (canonical record): 3b49afff0d0f83a1ccc4a74dbfd662a5507074b6490a47870f361751420271bf
ledger file SHA-256:               9c70fb98a460de146a60eb4f7e66f7255fa189449d177fc5f951fcd0c6d11d56
previous_ledger_sha256:            null
```

One preservation limitation remains explicit. Every primary-inspection record has `preservation_status: versioned_locator_and_bounded_report_only` and `source_artifact_sha256: null`. The ledger therefore preserves the exact locator/version claim, inspection metadata, bounded project-authored report, and record digests, but not the inspected primary-source bytes or their digest. Rechecking the report still requires reacquiring the named remote version; if those bytes disappear or drift behind a locator, this ledger alone cannot reconstruct or byte-verify them.

## Counterexample-guided refinement

Clarke, Grumberg, Jha, Lu, and Veith introduced an automatic iterative abstraction-refinement methodology for program verification. Their abstract notes that an abstract model may admit spurious counterexamples and that those counterexamples can be analyzed to refine the abstraction; it also reports an implementation in NuSMV and experiments on hardware designs. See [“Counterexample-Guided Abstraction Refinement,” CAV 2000, LNCS 1855, pp. 154–169](https://doi.org/10.1007/10722167_15).

The separate project-use record `SMF-PROP-CEGAR-TRIAGE-001` proposes only the control pattern: start with an explicit candidate, search for a counterexample, assess every live way the counterexample may bear on the candidate, representation, auxiliaries, test, or scope, and schedule one discriminating next step. More than one locus may remain implicated, and a shared mechanism may cross them. In a semantic forge, “spurious” may mean that a case is incoherent, out of scope, fails to hold claimed background conditions fixed, or attacks an auxiliary rather than the target definition. If accepted later, the proposal would require plural counterexample triage before repair; selecting work would not identify a unique responsible object.

The CEGAR paper concerns formal abstraction in verification, not Popperian epistemology or philosophical conceptual analysis. It does not establish that semantic refinements converge, that a generated counterexample is intelligible, that the refined definition is better, or that automation can replace semantic judgment. The linked proposal consequently offers CEGAR only as an analogy for workflow structure and not as a transferable correctness theorem.

## Competency questions

Monfardini, Salamon, and Barcellos report that competency questions are used to state ontology requirements, help identify concepts, properties, and relations, and check whether an ontology represents the desired knowledge. Their survey of 63 ontology engineers found that respondents mainly used such questions to define scope and evaluate conceptualization, while reporting continued difficulties in writing, using, and managing them. See G. K. Q. Monfardini, J. S. Salamon, and M. P. Barcellos, [“Use of Competency Questions in Ontology Engineering: A Survey,” ER 2023, pp. 45–64](https://doi.org/10.1007/978-3-031-47262-6_3).

Keet and Khan's 2024 preprint reports a first model that distinguishes five purposes for competency questions: scoping, validating, foundational, relationship, and metaproperty. It also supplies an annotated repository of 438 questions and explicitly presents the taxonomy as a first model rather than an exhaustive result. See C. M. Keet and Z. C. Khan, [“Discerning and Characterising Types of Competency Questions for Ontologies,” arXiv:2412.13688](https://arxiv.org/abs/2412.13688), submitted 18 December 2024. Their related position paper argues that competency questions are complex acts with motivations beyond fact retrieval and may support knowledge acquisition, knowledge organization, and validation; see [“On the Roles of Competency Questions in Ontology Engineering,” LNAI 15370, pp. 123–132 (2025), first published online 20 November 2024](https://doi.org/10.1007/978-3-031-77792-9_8).

The separate project-use records `SMF-PROP-CQ-TRACE-001`, `SMF-PROP-CQ-PURPOSE-001`, and `SMF-PROP-CQ-MOTIVATION-001` propose the modest use that questions should have explicit scope, purpose, motivation, and a live decision they could change. They do not treat an ontology answer as semantic truth or a question set as complete. Under these proposals, each competency question would remain a conjectured discriminator: it would name rival candidate answers and the model consequence of their difference, and would be revised or suspended when every answer leaves the same candidates admissible.

The cited ontology literature studies ontology engineering practice. It does not establish that competency questions are sufficient for a philosophical model class, that they have a privileged Popperian status, or that generated answers should automatically become axioms. The human reviewer remains responsible for whether a question captures the intended distinction.

## Metamorphic testing and the oracle problem

Segura, Fraser, Sánchez, and Ruiz-Cortés describe metamorphic testing as an alternative when checking a single complex input-output result against an expected output is impractical. Instead, a transformation is applied to an input and the tester checks the expected relation between the original and transformed outputs. Their paper surveys research, applications, empirical practice, and open challenges. See [“A Survey on Metamorphic Testing,” IEEE Transactions on Software Engineering 42(9), 2016, pp. 805–824](https://doi.org/10.1109/TSE.2016.2532875).

The separate project-use record `SMF-PROP-METAMORPHIC-001` proposes adapting that idea to semantic relations. It would ask whether a classification should be preserved under recoding, paraphrase, or implementation substitution, and whether it should change under provenance reversal, removal of reason-specific uptake, or a swapped conjecture/criticism order. Each expected relation would remain local, conditional, and human-reviewable. A failed relation would open a problem among the candidate, fixture, transformation, and expected relation; it would not by itself identify the defective one.

Barr, Harman, McMinn, Shahbaz, and Yoo define the test-oracle problem as the difficulty of distinguishing correct from incorrect behavior for a test input. Their survey describes specifications, modelling, contracts, and metamorphic testing among approaches to oracle automation, while observing that when automated sources are inadequate the remaining source of oracle information may be a human using informal expectations and domain knowledge. See [“The Oracle Problem in Software Testing: A Survey,” IEEE Transactions on Software Engineering 41(5), 2015, pp. 507–525](https://doi.org/10.1109/TSE.2014.2372785).

The separate project-use record `SMF-PROP-HUMAN-ESCALATION-001` proposes an explicit human semantic-oracle boundary. The term would not make the reviewer infallible. It would instead prevent a machine from fabricating a definitive semantic verdict where the operative specification remains informal or contested. Any human disposition would remain versioned, reasoned, scoped, and open to later criticism.

Neither testing paper claims that metamorphic relations arise automatically, that a human oracle is always correct, or that passing a large test suite establishes truth. The linked proposals therefore retain the non-inductivist restrictions that test counts cannot supply confidence, expected relations remain conjectural, and survival can be reported only relative to named tests and interpretations.

## Language-model counterexample and repair loops

Drucker and Mahowald study an iterated conceptual-analysis game in which one language-model instance proposes a counterexample to a definition and another repairs the definition. Across 20 concepts and thousands of cycles, they report two observations directly relevant to SMF: extended iteration produced increasingly verbose definitions without improving judged accuracy, and the language-model judge accepted substantially more generated counterexamples than expert humans on the shared human-rated subset. On that 60-item early-chain subset, the five humans averaged 32% acceptance while the model judge accepted 60%. The abstract also reports that many generated counterexamples were judged invalid by both humans and the model judge and that some concepts resisted stable definitions. See [“The Counterexample Game: Iterated Conceptual Analysis and Repair in Language Models,” arXiv:2605.03936](https://arxiv.org/abs/2605.03936), submitted 5 May 2026.

For this architecture, the first observation is evidence of definition bloat without measured accuracy improvement in those experimental chains, not proof that all iteration worsens definitions; definition accuracy and concision were themselves rated by a language model. The second is a warning about relative judge overacceptance in that study, not a universal multiplier for all LLM judges. Human evaluation covered 60 counterexamples, not the complete experimental corpus. The study used particular concepts, prompts, models, chain lengths, and human judgments and did not test Popperian epistemology.

The separate project-use record `SMF-PROP-ANTI-BLOAT-001` proposes treating definition growth and language-model judge acceptance as possible defects rather than improvement evidence. In the broader proposed workflow, generator, critic, and adjudicator roles would remain separate; semantic counterexamples would require human validation; `TEST_DEFECT` would remain available; clause and import deltas would be recorded; and verbosity, iteration count, or LLM agreement would not measure improvement. Each repair would also have to state a common defect mechanism rather than merely append an exception for the latest example.

The paper is a 2026 preprint. It is used as a current empirical warning, not as authority for CR-1.0 or as a general theorem about conceptual analysis.

## Contemporary advisory signal from AlphaXiv discovery

Mo, Ulfat, Dwyer, and Hossain's 2026 preprint PROGRESS contrasts regression tests whose expected behavior is derived from the current program with intent-bearing properties generated from program context while attempting to limit implementation leakage. Its abstract warns that a regression-derived oracle can record a fault already present as expected behavior. The properties are independent of the current program's regression output, not necessarily independently authored specifications. See [“PROGRESS: Property-Guided Regression Search for Semantic Falsification,” arXiv:2607.27359](https://arxiv.org/abs/2607.27359).

The separate project-use record `SMF-PROP-INDEPENDENT-ORACLE-001` proposes only the narrow anti-leakage control that prior candidate behavior and old machine labels must not generate their own semantic oracle. Under that proposal, regression cases could preserve witnessed problems and already accepted decisions, while the reasons for their expected semantic relation would remain separately reviewable. PROGRESS is a software-testing preprint whose properties concern programs; it neither supplies the relevant semantic intent nor validates the particular property-generation machinery for this project.

## Proposed project uses

| Proposed SMF use | Research instrument | Non-inductivist restriction |
|---|---|---|
| Triage a counterexample before deciding whether to repair a candidate, auxiliary, test, or scope. | CEGAR distinguishes real verification failures from spurious abstract counterexamples. | A counterexample is a conjectured criticism, not self-authenticating evidence. |
| Retain each research question's scope, intended decision, and rationale. | The competency-question survey reports both practical uses and management difficulties. | Traceability exposes a proposed inference; it does not license that inference. |
| Type competency questions by purpose. | The first competency-question type model distinguishes five purposes. | A scoping question cannot silently become a validation verdict, and the taxonomy remains non-exhaustive. |
| Record a harness question's purpose and motivation separately from its query text. | The competency-question roles paper treats questions as purpose-bearing acts. | A question's framing remains criticizable and cannot become a CR-1.0 premise. |
| Use explicit local transformation relations as fallible semantic test instruments. | Metamorphic testing checks relations across transformed executions when exact individual outputs are hard to specify. | Expected relations remain fallible interpretations; survival is not confirmation. |
| Escalate explicitly to human review when the semantic specification remains informal or contested. | Oracle research recognizes residual reliance on human domain judgment when automation is inadequate. | A human disposition would be workflow-authoritative only within its recorded scope and would remain revisable. |
| Treat definition growth and language-model judge acceptance as possible defects. | The Counterexample Game reports judge overacceptance relative to humans and verbosity without improved accuracy in its tested chains. | Model agreement, iteration, and definition length never become evidence of truth. |
| Forbid deriving a semantic test's expected result from the candidate or stored behavior under test. | PROGRESS warns that behavior-derived regression assertions can preserve current defects. | Prior behavior cannot justify an expected semantic result; the intended relation remains independently criticizable. |

These are the eight conjectural uses represented by the v2 `PROPOSED` records, not accepted engineering decisions. Their usefulness must be tested in the actual forge and separately adjudicated; any failure may criticize the instrument rather than the semantic model. No report, proposal, provider result, citation count, or provider agreement can close a semantic question or promote a hardening status.

## Claims deliberately not made

SMF-0.1 does not claim that counterexample iteration converges on a necessary-and-sufficient definition, that competency questions exhaust intended meaning, that metamorphic testing solves the semantic oracle problem, that human reviewers are infallible, that language models cannot contribute philosophical criticism, or that mathematics can decide whether its primitives mean what CR-1.0 intends.

It also does not claim that a candidate surviving all current attacks is probably true. The research ledger itself cannot issue a semantic or hardening verdict; it can only retain bounded source reports and proposed engineering uses. A separate, properly adjudicated harness assessment could at most report that a scoped candidate is currently unrefuted relative to named criticisms, tests, interpretations, and auxiliaries. New problems remain possible, and no research record or run closes inquiry automatically.

## References

| Reference | Stable locator |
|---|---|
| E. M. Clarke, O. Grumberg, S. Jha, Y. Lu, and H. Veith, “Counterexample-Guided Abstraction Refinement,” *Computer Aided Verification*, LNCS 1855, 154–169 (2000). | [doi:10.1007/10722167_15](https://doi.org/10.1007/10722167_15) |
| G. K. Q. Monfardini, J. S. Salamon, and M. P. Barcellos, “Use of Competency Questions in Ontology Engineering: A Survey,” *Conceptual Modeling — ER 2023*, LNCS 14320, 45–64 (2023). | [doi:10.1007/978-3-031-47262-6_3](https://doi.org/10.1007/978-3-031-47262-6_3) |
| C. M. Keet and Z. C. Khan, “Discerning and Characterising Types of Competency Questions for Ontologies” (2024 preprint). | [arXiv:2412.13688](https://arxiv.org/abs/2412.13688) |
| C. M. Keet and Z. C. Khan, “On the Roles of Competency Questions in Ontology Engineering,” *Knowledge Engineering and Knowledge Management — EKAW 2024*, LNAI 15370, 123–132 (2025), first online 20 November 2024. | [doi:10.1007/978-3-031-77792-9_8](https://doi.org/10.1007/978-3-031-77792-9_8) |
| S. Segura, G. Fraser, A. B. Sánchez, and A. Ruiz-Cortés, “A Survey on Metamorphic Testing,” *IEEE Transactions on Software Engineering* 42(9), 805–824 (2016). | [doi:10.1109/TSE.2016.2532875](https://doi.org/10.1109/TSE.2016.2532875) |
| E. T. Barr, M. Harman, P. McMinn, M. Shahbaz, and S. Yoo, “The Oracle Problem in Software Testing: A Survey,” *IEEE Transactions on Software Engineering* 41(5), 507–525 (2015). | [doi:10.1109/TSE.2014.2372785](https://doi.org/10.1109/TSE.2014.2372785) |
| D. Drucker and K. Mahowald, “The Counterexample Game: Iterated Conceptual Analysis and Repair in Language Models” (2026 preprint). | [arXiv:2605.03936](https://arxiv.org/abs/2605.03936) |
| D. T. Mo, N. Ulfat, M. B. Dwyer, and S. B. Hossain, “PROGRESS: Property-Guided Regression Search for Semantic Falsification” (2026 preprint). | [arXiv:2607.27359](https://arxiv.org/abs/2607.27359) |
