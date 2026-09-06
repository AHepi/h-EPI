# h-EPI: repository improvements and what the experiments support

Review date: 7 September 2026.

Reviewed repository: `AHepi/h-EPI`.

Reviewed branch: `claude/harness-repeatability-and-grounding-options`.

Pinned commit: `0cba0b8bb2efe2570b850ef2b7c0655e5ad88a06`.

## Scope and evidence

This is a targeted review of the branch's experiment reports, selected committed observations, claim specifications, corpus-generation code, executor interface, and refusal-site mutation tool. It is not an exhaustive audit of every observation or source file. No remote repository changes, new paid model calls, or full repository test-suite runs were performed. A direct clone was blocked by network name resolution; repository inspection used the connected GitHub reader. Two concrete findings were reproduced locally using isolated transcriptions of relevant source operations and recorded values. The accompanying script explicitly distinguishes that exercise from running a complete checkout.

The repository now describes itself as a document-to-form conformance harness; its earlier semantic-model project is archived separately. This matters: the experiments can test finite rule execution and named distinctions without constituting a complete test of creativity or explanatory universality. The external semantic authority and staged specification discussed in one report are not present in this branch, and this review does not certify that report's account of those absent documents. [R1, R2, R10]

## Overall assessment

Keep the criticism-first design. Immutable records, plural failure attribution, named conjectures, counterexample identifiers, explicit contested readings, and replay are useful foundations. The immediate priority is not a larger model sweep. It is making the relationship between the question asked, the information supplied, the predicate evaluated, and the conclusion published more exact.

Two confirmed findings affect interpretation of the semantic pilots. A negated-existential dossier omits a premise the answer key assumes. A separate claim about internal counting consistency is implemented by a different property: agreement with the answer key's count. These are local defects, not grounds for discarding every result. They demonstrate why the harness must remain under criticism alongside the models. [R3–R7]

## A premise disappears before the model sees it

In `tools/gen_signed_derivations_corpus.py`, the prose renderer writes the range-membership and completeness statement only when the outermost formula is `all` or `some`. Its table renderer has the same root-only condition. For `NOT SOME x IN R: P(x)`, the outermost operator is `not`, so the renderer omits that statement. The answer-key generator still receives `complete=True`. [R3]

The committed observation `a11d580fc5b9ffab` verifies that this is not merely a possible bug in unused code. The actual DER-11 input is:

> Derivation dossier DER-11. The target claim is NOT SOME x IN R: P(x). Cases on file: a negative case for P(m1); a negative case for P(m2); a negative case for P(m3).

The instructions require the record to assert that the member list is complete before deriving a negative existential. They then permit a positive case for its negation. The document does not assert completeness. Gemma returns `positive_derivable: no` and `positive_blocked_by: range_not_complete`. The key expects `yes` and `nothing`. On this issue, the response is consistent with the supplied rule, while the scorer uses information withheld from the model. [R4]

The report's S18 says that four models failed on the negated existential and that three blamed a range the dossier had declared complete. That last factual description is wrong for the visible dossier. S18 should be withdrawn or marked invalid as evidence of the claimed negation-composition failure pending a corrected experiment. This does not establish that every answer on DER-11 was otherwise sound: a model can both correctly notice a missing premise and make another error. Nor does it establish that the model matching the hidden key reasoned correctly. [R4, R7]

The local reproduction exposes a stronger structural problem. Holding the formula, cases, members and case identifier fixed, switching completeness from true to false leaves the rendered document identical but changes positive derivability from true to false. Two hidden states with different keys have become one visible question. No respondent can reliably recover a hidden distinction from that question alone.

The repair is recursive traversal of the formula tree for rendering range metadata. Tests should cover quantifiers beneath negation and connectives, not only top-level quantifiers. More broadly, every exact expected field should have a witness that the premises supporting it are represented in the model-visible request. For generated finite tasks, compare reconstructed visible facts against the generator's state, and deliberately mutate renderers to drop or flip a premise. An independently written visibility check is preferable to a renderer checking itself.

There are two different follow-up actions. Re-score the old response under the old, actually visible prompt, preserving the original record and recording a new assessment. Then run the repaired prompt as a new experiment. A response to the old prompt cannot be replayed as though the model had seen the repaired one.

## A claim evaluates a different property from the one it names

`LAB-11` states: “A language model's usable count always equals the number of arguments it labelled in.” The implemented condition is a `MATCH` verdict on `usable_count`, meaning agreement with the answer key's count. The note acknowledges this is a proxy, but the proxy does not support the stated conclusion. [R5]

The committed GPT-OSS 20B observation `dcc7033bffce6cd0` provides a direct witness. It labels A1, A2 and A3 undecided, A4 and A5 out, and A6 in. Its `usable_count` is 1. It has therefore counted its own in-labels correctly. The key has two arguments in, so the recorded count mismatches the key and the LAB-11 predicate can classify this observation as a refutation. The model's label computation is wrong, but its internal counting is consistent. [R6]

Keep two separate claims: the returned count agrees with the reference count; and the returned count equals the count of in-labels in the returned answer. The latter requires a relational predicate over the output itself. Missing or malformed fields need their own status rather than being silently converted to zero or a logical counterexample.

Test the distinction with four synthetic outputs: correct labels with a consistent count, wrong labels with a consistent count, correct labels with an inconsistent count, and wrong labels with an inconsistent count. Only the two internally inconsistent outputs should refute the internal-consistency claim.

The published total of 109 LAB-11 counterexamples does not establish 109 internal inconsistencies. Some might be genuine, but the current predicate does not tell us which. The same review should be applied to every claim whose prose describes an internal relationship or invariance while its executable condition merely checks reference-key agreement. [R5, R6, R7]

## Separate observations from assessments

H22 records an unusually clear reason to improve the data model. A genuine refusal used typographic apostrophes, so the original heuristic missed it. The heuristic was repaired and replay produced a changed assessment, but those replayed records were not committed because the reporting path would count the same model replies twice. The docs explicitly leave the publication decision unresolved. H23 already repaired a different issue, pairing repeated sends with the appropriate responses; that repair does not solve assessment-version selection. [R8]

Give the model invocation, its response, the interpretation applied to it, and the report's selection policy separate identities. An invocation identifier must distinguish repeated sends even when their request digests match. An assessment should refer to the invocation and bind the parser, oracle, appraisal and claim versions. A report manifest should select a declared assessment view and count each invocation once. Keep every historical assessment available.

This allows a corrected detector to correct the current report without editing history or multiplying observations. It also permits sensitivity reports under rival readings. Report counts should distinguish model invocations, deterministic controls, transformed variants, repeated sends, base dossiers, and assessments. They are different denominators, not interchangeable sample sizes.

## Treat reasoning configuration as an experimental factor

The executor's `ChatRequest` types `think` as `bool | None`; the semantic pilots use `think=false`. Current Ollama documentation says GPT-OSS requires `low`, `medium`, or `high`, ignores Boolean values, and cannot have its trace fully disabled. Consequently, identical JSON settings did not establish equivalent reasoning conditions across models. [R9, E1]

Add capability-aware configuration that accepts each backend's actual setting vocabulary. Record requested settings separately from what the endpoint documents, what it acknowledges, and what the response visibly contains. A populated thinking channel is an observation, not proof of an internal causal mechanism; an absent channel is not proof that no reasoning occurred.

A useful causal experiment changes reasoning settings within the same model and deployment, using matched cases in interleaved order. For GPT-OSS, compare supported levels rather than inventing an off condition. Hold the prompt, parser and scoring interpretation fixed. Model family, architecture, training, total and active parameter counts, quantisation, serving conditions and token expenditure cannot all be collapsed into a single “size” explanation.

Record software commit and environment identity, endpoint, available model revision or digest, request and response timestamps, provider request identifier when available, requested options, retry history, and the relevant parser/scorer versions. Hosted backends may not disclose their exact revision; record that as unknown rather than treating a model alias as a pinned model.

## Make repeat controls local to the intervention

The repeat family is a valuable existing feature, not a missing one. The next improvement is to avoid treating one aggregate repeat count as a causal correction for every other comparison. The same models show different repeat patterns on formal labelling, explanatory classification and signed derivation. [R7]

For each intervention of interest, interleave repeated original and altered requests on the same cases. Include unchanged requests and harmless rewrites alongside a premise deletion or meaningful rule change. Log order and time. Preserve a distinction between raw text difference, parsed field difference, meaning-preserving variation, and a changed task verdict.

A single changed answer after deleting a sentence does not isolate that sentence's effect if identical requests also change. Conversely, an unchanged answer does not prove the sentence was unused: another sentence, a familiar procedure, or an independent derivation may supply the same information. The needed experiment discriminates between such explanations rather than assigning a cognitive cause to an isolated pair.

The metamorphic-testing literature offers useful test designs based on transformations with declared semantic relationships. Those relationships must be checked for this harness's own rule system; classical equivalences should not be imported unexamined into a signed, possibly inconsistent case calculus. [E2]

## Distinguish literal quotation, derivation and evidential support

The repository already acknowledges that finding a quoted span in a document does not generally establish that it supports the returned field. It also provides explicitly configured relaxations, such as completing a date range. These are important distinctions, but a broad `GROUNDED` label can obscure them. [R8]

Expose separate observations for literal span location, a permitted normalisation, a derivation under stated rules, a value-to-source relationship, and unresolved semantic support. For example, the date 24 June 2025 may be derived from “24 to 26 June 2025”; it is not a contiguous verbatim quotation of that phrase. Preserve the actual quote and attach the date-completion transformation.

Use contrastive controls: a correct quote attached to the wrong person, an existing quote attached to the wrong field, a true value paired with irrelevant evidence, a copied stale correction, and a source edit that should change exactly one field. Also include changes that should not affect the field, so a test cannot reward indiscriminate sensitivity. Open semantic relevance may require criticisable judgement; such a judgement should not be relabelled a mechanical guarantee.

For finite arithmetic and calendar derivations, request typed operands and their source locations, then let a replaceable deterministic component compute the result. That does not make the extraction correct by fiat. It separates an extraction error from a computation error and gives critics a smaller, inspectable target.

## Strengthen mutation evidence without overstating it

The refusal-site sweep's first all-caught result was an instrument failure: the mutant environment could not import its required schemas. The repair runs a baseline through the same environment and requires the same test count. Current code also notes that subprocess-based command-line tests can still run the original package rather than the mutant. [R8, R11]

Extend the sweep to bind loaded module paths and hashes, actual executed test identifiers, skipped tests, failure kinds, and the failing assertion or error. A matching test count is useful but does not prove the same tests and code were exercised. The current implementation discards the stderr tail for caught mutants; preserve enough diagnostic evidence to distinguish a meaningful assertion from an unrelated error.

Change the interpretation of “survived.” It means deletion was not detected, not necessarily that the site was never exercised. A deletion can be masked by a later guard, or its effect can fail to propagate to a tested assertion. Keep reachability, behavioural effect, and detection separate.

Broaden mutations beyond `raise` deletion. Mutate a renderer to omit a completeness premise; replace an internal relational predicate with key agreement; attach a quote to the wrong field; change a polarity; suppress an appraisal dependency; or double-count a replay. These target semantic reporting failures like those found in this review. They should remain local test-fixture mutations, not changes to published observations.

## Correct the scope of the semantic claims

The report on what is provable in the semantics correctly distinguishes finite bookkeeping from claims about a real system's explanatory capacity. But its reasoning sometimes moves from “there is no decision procedure for these semantic predicates” to “nothing positive is provable.” That implication does not follow. Lack of a general decision procedure does not preclude individual proofs, structural theorems or conditional deductions. [R10]

The defensible restriction is that records and an evaluator's labels do not, without substantive interpretive premises, entail creativity or universality. That is different from forbidding explanatory theories about those capacities. The report should retain the former restriction without presenting the latter as a logical consequence of undecidability.

Bind the semantic pilots to the exact source versions, sections, declared interpretations and implementation departures on which they depend. This is especially important because the report says the two underlying version-1.1 documents and their reference checker are not in this repository. A source hash establishes identity, not fidelity, and a computable appraisal policy must remain subordinate to the semantic authority rather than silently redefining it.

## What the experiments support about LLMs

### Stable request settings are not a guarantee of stable hosted outputs

The labelling pilot reports different labels on byte-identical repeated requests for every one of its five models. GPT-OSS 120B matched all 18 initial labelling dossiers but differed on six of 32 repeats. This defeats the proposition that an initially correct response, temperature zero and a fixed seed guarantee reliable repetition in the tested service. It does not establish intrinsic nondeterminism of all LLMs or identify whether serving, hidden defaults, model computation or another factor caused the variability. [R7]

### Success is multidimensional and task-dependent

The two GPT-OSS models matched 35 of 36 initial formal-labelling dossiers between them, compared with 24 of 54 for the other three models. In explanatory distinctions, Gemma matched eight of twelve episodes while GPT-OSS 20B matched four and GPT-OSS 120B five, subject to the declared contested interpretations. This is a descriptive pattern, not a causal estimate of reasoning or a model ranking. [R7]

It suggests that executing a finite rule, complying with a definition, recognising missing information, maintaining a distinction, quoting correctly and repeating an answer are separable experimental targets. Parameter count and visible trace length do not provide a sufficient general account of the observed pattern. The experiments do not establish that size has no effect.

### Prompted rule compliance is not an epistemological identity

With the signed-derivation rules present, the reported baseline responses avoided deriving a universal from finite positive instances without the completeness premise. On deletion of the universal rule, three models produced that derivation in the reported probes. Those observations show behaviour changes across instructional contexts. They do not establish that a model is intrinsically inductivist or non-inductivist, and the intervention's causal magnitude needs local repeat controls. [R7]

The broader research question is whether a model can preserve the asymmetry across unfamiliar representations and transfer settings where the relevant prohibition is not handed to it in the tested wording. The answer is an open explanatory question, not a status inferred from a small collection of labelled forms.

### Losing a qualification can differ from getting the conclusion wrong

DER-14 is not affected by the DER-11 omission: its actual prompt does state completeness. Gemma derives both signed cases and marks the positive case conditional, but marks the negative case unconditional even though every negative derivation depends on a leaf carrying both polarities. The explicit field definition requires that qualification. The report records analogous omissions for all five models. [R7, R12]

This supports a precise local failure mode: an answer can match the derivability rule while failing to preserve the stated dependency qualification. It motivates a conjecture that inference and qualification maintenance are separable capabilities. It does not show that every LLM always loses conditions or that the repository's signed-case policy is itself the definition of rational inference.

### Models can be systematically wrong, and systematically penalised for a sound response

The genuine DER-14 mismatch and the invalid DER-11 penalty coexist. So do wrong argument labels and a correct count of those wrong labels in the LAB-07 record. It follows that an output-level criticism must identify what failed; a single mismatch flag cannot supply that explanation. [R4, R6, R12]

Agreement among models can help reveal an ambiguous or incorrect key, as the repository's own travel-claim revisions illustrate. Agreement is a reason to investigate, not an authority deciding the answer. Likewise, using several models does not by itself establish independence of errors: all can inherit the same ambiguity, training convention, prompt omission or scoring defect. [R13]

### These records permit criticism of guarantees, not a universal theory of LLM limitations

A sound counterexample can refute an unconditional behavioural guarantee that includes the tested setup. It cannot establish a population failure rate, a model's universal incapacity, or an internal mechanism. Here the counterexample itself must survive criticism of source visibility, task interpretation, the predicate and the serving context.

The unit being tested is the model deployment together with its prompt, renderer, parser, key and reporting interpretation. This does not make learning about models impossible. It indicates which interventions and additional evidence are needed to distinguish rival explanations.

Nor do finite successful forms certify creativity, consciousness, explanatory universality, or their absence. Different mechanisms can agree on the tested cases. The productive response is to propose explanatory accounts that make different predictions and build discriminating tests, rather than treating either successful compliance or a failure count as a direct measure of understanding.

## The most informative next experiment

Start with the signed-derivation tasks after repairing the renderer and the claim predicates. Hold the logical task fixed while varying completeness visibility, contested-leaf status and nested structure. Include the same questions under declared equivalent renderings, with fresh symbols and both complete and incomplete ranges. Predeclare the predicted differences and invariances.

Compare direct form filling with a mode that supplies typed premises to a small reference checker and a mode that produces an explicit, checkable derivation certificate. Those conditions are not equally difficult tasks and should not be labelled interchangeable model scores; their purpose is to locate the failing component. An oracle-supplied-premise condition can isolate rule execution, while an extraction condition tests whether the model recovers the premises itself.

Interleave repeated calls within each condition and use supported reasoning settings. Freeze the exploratory corpus, then create a separately held-out challenge set that was not used to design the repair. Store findings, rival explanations, contrary predictions and counterexamples with the exact configurations. None of this requires turning empirical counts into semantic justification.

The next increment should answer a narrower and more valuable question: when a response goes wrong, did the model miss a premise, fail a stated operation, lose a qualification, resolve an ambiguity, or receive a defective question? Once that distinction is reliable, broader experiments become substantially more informative.

## Source ledger

All repository references below use the pinned commit above. Paths identify exact inspected sources; named sections and observation prefixes locate the evidence.

### R1 — Repository description

`README.md`.

### R2 — Project boundaries and operating rules

`CLAUDE.md`, especially “What this repository is,” “Never promote,” and “Changing the machine.”

### R3 — Signed-dossier generation

`tools/gen_signed_derivations_corpus.py`, functions `derive`, `prose`, `table` and `build`; designed cases DER-11 and DER-14. In the inspected source, the prose and table checks are within lines 128–153; the DER-11 definition is around line 226.

### R4 — Missing-premise observation

`forge/conformance/runs/signed-derivations/observation.a11d580fc5b9ffab.json`.

### R5 — LAB-11 statement and executable condition

`forge/conformance/pilots/appraisal-labelling/claims.json`, around lines 474–498.

### R6 — Consistent count penalised by LAB-11's proxy

`forge/conformance/runs/appraisal-labelling/observation.dcc7033bffce6cd0.json`.

### R7 — Three semantic pilots

`docs/semantics-battery.md`, especially S1, S5, S9–S23 and the generated LAB-11 outcome. Reported aggregate counts were inspected but not independently reaggregated across all committed observations.

### R8 — Existing repairs and unresolved assessment-publication problem

`docs/failure-modes.md`, especially H4, H17–H27. These entries are historical at different code and corpus states; their counts should not be combined as one current sweep.

### R9 — Request interface and response metadata

`src/creib/forge/conformance/executor.py`, `ChatRequest`, `ChatResponse`, request digest and payload construction.

### R10 — Semantic-report argument and absent sources

`docs/reports/provable-in-the-semantics.md`, opening sections and “The substantive theory, and why nothing positive is provable in it.” The absent source documents were not independently audited here.

### R11 — Mutation instrument

`tools/refusal_sweep.py`, module documentation, `run_suite`, `one` and report interpretation.

### R12 — Genuine conditionality example

`forge/conformance/runs/signed-derivations/observation.4382f6952c5dc724.json`.

### R13 — Travel-claim experiments

`docs/small-models.md`, especially T2, T3, T17–T28 and comparison limits.

### Repository source base

Append a path from this ledger to:

`https://github.com/AHepi/h-EPI/blob/0cba0b8bb2efe2570b850ef2b7c0655e5ad88a06/`

### E1 — Official provider documentation

Ollama, “Thinking,” retrieved 7 September 2026.

`https://docs.ollama.com/capabilities/thinking`

The material used here is the documented setting vocabulary and GPT-OSS's treatment of Boolean values, not a general claim about the faithfulness of reasoning traces.

### E2 — External test-design literature

Zhou and colleagues, “LGMT: Logic-Grounded Metamorphic Testing for Evaluating the Reasoning Reliability of LLMs,” arXiv:2605.23965, version 3, revised 2 July 2026. The inspected abstract describes testing declared logical invariances. This is advisory method literature, not authority for h-EPI's semantic rules.

`https://arxiv.org/abs/2605.23965`

## Reproduction files

`isolated_witnesses.py` and `isolated_witnesses_results.json` reproduce the renderer information-loss witness and the LAB-11 predicate mismatch using isolated source-operation transcriptions. They do not reproduce live model calls, check every observation digest, or substitute for the repository's complete tests.
