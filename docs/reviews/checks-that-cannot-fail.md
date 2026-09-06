# Checks That Cannot Fail

**A taxonomy of self-confirmation, its detection, and what transfers from formal methods**

Prepared 1 September 2026. Sources: alphaXiv corpus (2026 preprints), plus the classical formal-methods and mutation-testing literature.

**Repository status update, 4 September 2026.** This is an advisory engineering report, not an
accepted h-EPI research basis or semantic authority. Its newer sources are absent from the
current eight-entry research ledger and require direct inspection of exact primary versions,
bounded source-only reports, limitations, and separate proposed-use records before project
incorporation. Repository examples below establish only the behavior of named code, fixtures,
and replay scopes.

---

## 1. Does the class have a name?

This review found three partially overlapping names. None covers the whole class, and the gaps
between them are a load-bearing finding of this report.

**Vacuity / vacuous pass** (formal methods, 1997–). A property holds for a trivial reason — canonically *antecedent failure*, where the precondition of an implication is unsatisfiable in the model, so the consequent never affects the verdict. Named by Beatty and Bryant (1994) as antecedent failure; generalised and given detection algorithms by Beer, Ben-David, Eisner and Rodeh (CAV 1997; *Formal Methods in System Design* 18(2), 2001). This is the mature literature, and it is narrower than it looks.

**Oracle anchoring** (software testing, 2026). An oracle obtains its expected value, directly or transitively, from the system it is judging; a fault moves measurement and expectation together and the comparison cancels. Named and measured by Canedo, *Oracles That Cannot Fail* (arXiv:2608.17214). The paper's own definition of the shape:

> A test oracle whose expected value covaries with the system it judges can become invariant to the declared fault. When measurement and expectation move together, the comparison may cancel across the declared input domain, so generating more inputs does not expose that fault family.

This bounded restatement is the one used in this report. It does not claim that such an oracle cannot reveal unrelated defects.

**Vacuous pass in verifiers / fail-open** (software supply chain, 2026; CWE-703, CWE-754, CWE-390). A gate reports success along a path where it never examined the thing it claims to examine. Hill, *Four Ways to Forge a Bundle My Own Verifier Calls Clean* (arXiv:2608.26183), Definition 1: acceptance returned "while an intended binding, comparison, or coverage obligation was absent, bypassed, or semantically unexamined."

### Where the two externally reported instances land

They land in **different classes with different primary detectors**, which is why one incident
produced two symptoms.

| Reported instance | Class | Named by |
|---|---|---|
| Probe whose formula encoded its own premise | **State anchoring** (C2 below) | Canedo 2026 |
| Document-checker that silently skipped unparsable claims | **Silent skip / unenumerated obligation** (C6 below) | Hill 2026; Chen et al. 2026 |

The first is outside ordinary antecedent-vacuity checking unless provenance is included. The
second is invisible to refusal-site deletion when the missing obligation never generated a
refusal site, although parser, enumerator, artifact, or boundary mutations can expose some such
omissions. An organisation that installs only one detector will still be exposed to other
mechanisms.

---

## 2. The generative axis

Sorting by *why the check cannot go red* produces the taxonomy and predicts which detector applies. There are four structural mechanisms plus one boundary case.

1. **The trigger never fires.** A guard, antecedent, or assertion is present but unreached.
2. **The comparison cancels.** Both sides of the comparison move with the fault.
3. **The subject never runs.** The thing to be checked was mocked out, empty, absent, or skipped.
4. **There is nothing to compare against.** No assertion, or an assertion on a constant.
5. *(Boundary)* **The check is merely weak, not structurally incapable.** It can go red — just not on this fault.

Traditional formula-vacuity analyses do not by themselves reach mechanism 2. Common mutation
operators may miss mechanism 3, while artifact or boundary mutations and extreme mutation can
expose some instances. The relevant question is the declared fault family, not the tool label.

---

## 3. Sub-question 1 — Vacuity in formal methods

### Detection algorithms

The core schema is *mutate and re-check*. For a formula φ, a subformula ψ occurring with a single polarity is **not affecting** if φ and φ[ψ ← ⊥] (or ⊤) are equivalent in the model M. If M ⊨ φ and also M ⊨ φ[ψ ← ⊥], the pass was vacuous with respect to ψ.

Principal variants and their cost:

| Method | Cost | Source |
|---|---|---|
| Subformula replacement, single-occurrence, w-ACTL subset | 1 extra model-check per candidate subformula; Beer et al. give a construction producing a single witness formula w(φ) — one extra run | Beer, Ben-David, Eisner & Rodeh, FMSD 18(2), 2001 |
| Full vacuity via formula mutation (all subformulas, all polarities) | Linear in \(\lvert\varphi\rvert\) model-checking runs; generating an *interesting witness* is PSPACE-complete for LTL and CTL | Kupferman & Vardi, *Vacuity Detection in Temporal Model Checking* |
| Enhanced vacuity, multiple occurrences and general polarity | Higher; addresses formulas Beer et al.'s subset excludes | Armoni, Fix, Flaisher, Grumberg, Piterman, Tiemeyer & Vardi, CAV 2003 |
| Thorough vacuity for CTL | Reported as "very small overhead, and even, occasionally, in less time than plain model checking" | Purandare & Somenzi |
| Proof-core / resolution-based (BMC) | Extracts vacuity from the resolution proof of a successful BMC run; VAQTREE reported faster than the naive method in 72% of cases | Ben-David, Copty, Fisman & Ruah, FMSD |
| Temporal antecedent failure (regular-expression specs) | Refines vacuity for the SVA-style specifications used industrially | Ben-David, Fisman & Ruah, *Vacuity in practice*, FMSD 46(1), 2015 |

A semantic proof or relevance core can make vacuity analysis cheap. A trace of what the checker
consulted is weaker: a value may be read but ignored, or may move both sides of a comparison.
h-EPI therefore treats exact incidence and dependency closure as structural evidence rather
than proof that an input affected the verdict.

### Measured prevalence

The recurring historical industrial observation is that **approximately 20% of specifications passed vacuously in initial verification runs at IBM Haifa Research Laboratory** (Beer et al.). Hill cites it as external context for a refusal-site gap in one later verifier. It is evidence that double-digit vacuity occurred in that setting, not a transferable industry baseline.

Caveats worth stating: it is a single site, ~1997, hardware, and "initial runs" — post-triage rates would be lower. No comparably-cited replication has appeared.

### Which ideas transfer

Kupferman and Vardi's structural observation is the one to carry: vacuity and coverage "are essentially the same: both are based on repeating the verification process on some mutant input, whereas in coverage, mutations are in the system." That motivates two complementary operators — *mutate the checker* and *mutate the artifact* — which reappear in the reviewed 2026 informal-checker work as refusal-site deletion and as tamper fixtures or fault injection.

What does not transfer is covered in §6.

---

## 4. The taxonomy

Each class: mechanism, detector, cost, evidence strength, citation.

---

### C1 — Antecedent failure / dead guard
*Mechanism 1: the trigger never fires.*

A conditional obligation whose condition is never satisfiable in the system under check. The classical case.

- **Detection:** subformula mutation and re-check; proof-core extraction where available.
- **Cost:** ~1 to |φ| extra verification runs; potentially cheap with a sound relevance core,
  not with a consultation log alone.
- **Prevalence:** approximately 20% of specifications in the cited IBM Haifa initial runs.
- **Evidence:** **Strong.** Thirty years, multiple algorithm families, industrial deployment.
- **Cite:** Beer et al. FMSD 2001; Kupferman & Vardi; Armoni et al. CAV 2003.

---

### C2 — State anchoring (self-referential expectation)
*Mechanism 2: the comparison cancels.* **This matches the externally reported probe.**

For a relative oracle, a fault scaling measurement and expected value together can yield
\(m'=km\) and \(e'=ke\); when \(e\ne0\) and \(k\ne0\), \(m'/e'=m/e\) exactly. An
absolute-error oracle \(\lvert m-e\rvert\le\tau\) is not generally invariant under the same
scaling: \(\lvert m'-e'\rvert=\lvert k\rvert\lvert m-e\rvert\) in every case. Its Boolean
verdict can still remain unchanged when the difference is zero or stays on the same side of
\(\tau\); invariance across the declared domain requires those conditions or a covarying
tolerance or other decision term. Relative to the declared target, fault family, decision
expression, and input domain, either shape can become invariant to that fault. This does not
mean it cannot fail for unrelated defects.

Canedo identifies **four channels** by which the mutated code reaches the oracle's terms. Of the
literature located in that study, only the first was previously named:

1. **Expected value** — the yardstick the assertion compares against. *(Named in the test-smell literature; never measured.)*
2. **Tolerance band** — the width of the permitted deviation.
3. **Conditioning variable** — the state the assertion is evaluated at.
4. **Generator** — the scenario placer, which runs before any assertion exists.

In the study's costliest oracle, closing channel 1 recovered 1 mutant and closing channel 3
recovered 8 more. Channel 3 carried most of the cost and was not named in the prior work located
by that study.

**The sizing condition** is what makes the class predictive rather than merely alarming. Self-reference costs detection only when the anchored value *sizes the comparison* and the fault moves it proportionally. Where the anchored value only places a scenario, feeds a bound with large slack, or measures a quantity covered elsewhere, the provenance flow may be present without costing kills in the cited mutant population. In Canedo's own data, 6 anchored instances were found; the 2 that sized their comparison carried 11 of the 12 recovered mutants. A blanket "self-reference is fatal" claim would have been false 3 times in 6.

**Anchoring is scope-relative.** One unchanged oracle, run against two declared mutate targets differing only in whether they contained the producer of the value it read, recovered nothing under one and 3 mutants under the other. A report that an oracle is anchored is incomplete until it says *anchored with respect to what*. For a practitioner without a mutant population, the module or package boundary is the recommended proxy.

- **Detection (primary):** bounded static provenance check. Relative to the declared mutate target,
  trace every verdict-sizing input: expected value, tolerance band, conditioning variable, and
  scenario generator. The *flow* half is decidable only within the chosen static model;
  arbitrary dynamic Python behavior, reflection, plugins, and runtime dispatch exceed that
  model. The *sizing* half requires examining each oracle.
- **Cost:** reported as minutes per suite in Canedo's subject, with no mutant population required for the flow screen; h-EPI cost is unmeasured. The paper's tool sweep found no matching shipping linter.
- **Detection (pricing):** mutation testing is one empirical way to learn what each instance
  costs; a sound proof or independent analysis may also discriminate relevant anchors.
- **Prevalence:** unmeasured outside this one study. 6 instances across 12 property suites in one deployed system, of which 2 were costly.
- **Evidence:** **Weak-to-moderate.** Single system, single author, self-measured, one external comparison point (Ravi & Coblenz, 40 Python projects). The *mechanism* is an algebraic identity and needs no empirical support; the *prevalence* has none.
- **Cite:** Canedo, arXiv:2608.17214.

**Critical negative result:** this class is not directly scored by the oracle-adequacy metrics located in the cited survey. See §5.

---

### C3 — Unexecuted assertion ("rotten green")
*Mechanism 1.*

A test passes because some or all of its assertions were never reached — early return, guard always taken, empty loop body, assertion inside an unentered branch.

- **Detection:** combined static + dynamic call-site analysis at assertion granularity, accounting for helper methods, inherited helpers and trait composition. Tools: DrTest (Pharo), RTj (Java).
- **Cost:** cheap; one instrumented run of the existing suite. No false negatives reported; some false positives from conditional use and multiple test contexts.
- **Prevalence:** **nonzero across the surveyed corpora.** 294 rotten tests were found in 19,905 Pharo test cases (Delplanque et al., ICSE 2019); some had been "sleeping" for at least five years. Surveys of roughly 100 mature projects each in Java, Pharo and Python found rotten green tests in all three language corpora, but *fully* rotten tests were rare (worst project observed: 17 of 59 tests, ratio 0.28; most projects far lower). Hidden bugs were found behind rotten tests in Pharo and Python.
- **Related smells named in the same work:** *missed fail* (`assertTrue(false)` instead of `fail()`), *missed skip*.
- **Evidence:** **Strong.** Large corpus, three languages, replicated, tool available.
- **Cite:** Delplanque, Ducasse, Polito, Black & Etien, ICSE 2019; Aranega, Delplanque, Martinez, Black, Ducasse, Etien, Fuhrman & Polito, *EMSE* 26:130, 2021.

---

### C4 — Pseudo-tested code (assertion-free in effect)
*Mechanism 4: nothing to compare against.*

A method is covered by the test suite, yet no test fails when its entire body is removed. Coverage says tested; nothing is checked.

- **Detection:** **extreme mutation** — replace the whole method body with a default return. One mutant per method (a few for typed returns).
- **Cost:** far cheaper than instruction-level mutation. Method-granularity, and computationally tractable enough for CI. Implemented in Descartes (a PIT engine).
- **Prevalence:** **the strongest number in this report.** Present in *every* project examined, including very well-tested ones with high statement coverage. Niedermayr, Juergens & Wagner (2016): 19 open-source Java projects, median 10.1%, range 6–53%. Vera-Pérez, Danglot, Monperrus & Baudry (2018), independent replication over 28,000+ methods: present in all subjects, ratio 1–46%. Mutation score of required methods averaged 52 points above pseudo-tested methods (p < 0.01, effect size 1.5).
- **Evidence:** **Strong.** Original study plus first independent replication, large corpus, consistent direction.
- **Cite:** Niedermayr, Juergens & Wagner, CSED 2016; Vera-Pérez et al., *EMSE* 24(3), 2018.

---

### C5 — Dead refusal site (fail-open verifier)
*Mechanisms 1 and 3.* **The closest published analogue to a document-checker or evidence verifier.**

A verifier's reject path exists in source but has never been observed firing. The gate passes because the refusal statement is unreachable, guarded on an operand the submitter controls, or bypassed.

Hill's general form, which is the sentence to hand to an engineer: *a comparison guarded on both operands existing is not a check, it is a suggestion. The party supplying one operand decides whether the comparison happens.*

- **Detection:** **refusal-site deletion mutation.** Enumerate every statement that appends a named failure reason; replace each with `pass`, one at a time; a mutant is *caught* if the unit suite fails, or a liveness control stops passing, or any committed tamper fixture stops being refused.
- **Cost:** **cheap and measured.** 143 mutants swept in 5 minutes 46 seconds on an Apple M4.
- **Prevalence:** on one real verifier, **75 of 112 refusal sites could be deleted with the entire test suite, the liveness control, and the tamper corpus all still green** — a liveness score of 0.330.
- **Two further results in that subject and operator:**
  - *Bug-specific hardening did not buy liveness in this subject.* Fixing four demonstrated forgeries and adding a fixture per fix moved the score from 37/112 to 39/119. On the 112 pre-existing sites the caught set was **exactly 37 before and after** — zero improvement. The four fixes required seven new refusal statements, themselves covered at 2/7.
  - *One hand-written tamper corpus did not scale in the cited subject.* A 16-fixture corpus written expressly to prove the verifier could refuse scored 10/112 = 0.089 alone and added no marginal kills downstream of a unit suite that already asserted each fixture's verdict. There is no general *n*/total ceiling merely because fixture outcomes are Boolean: one well-chosen fixture can expose multiple mutation sites.
- **Validation:** the operator anticipated **3 of 4** independently hand-found forgeries. It was blind to the fourth for a structural reason — see C6.
- **Evidence:** **Weak-to-moderate.** Single verifier, self-measured, closed-loop registry, one external audit as the only outside data point. The author says so prominently. The *method* is composed entirely of prior art (statement deletion; grading a checker by mutation, per muSE, MASC, Chen & Furia, Delcourt et al.); the contribution is the site selection and the subject.
- **Cite:** Hill, arXiv:2608.26183.

---

### C6 — Silent skip / unenumerated obligation
*Mechanism 3: the subject never runs.* **This matches the externally reported document-checker pattern.**

The check never sees the item. No refusal fires because no refusal exists for an item that was never enumerated. Instances: a claim the parser could not read and dropped; an artifact covered by no check; a file inside a symlinked directory that `rglob` never descends; a pattern that matches nothing; `str.replace` that silently no-ops; `dict.get(k, default)`; `grep | true`.

**Why refusal-site deletion cannot find this instance.** Hill's fourth forgery was an *absent
obligation*: no refusal site existed for an evidence artifact covered by no check, and the fix
had to create one. "An operator that deletes existing refusal statements cannot, by
construction, see a refusal that was never written." This is a property of that operator family,
not of mutation in general; parser, enumerator, artifact, or boundary mutations may expose other
instances.

**Why review cannot certify completeness by itself.** Chen, Chen, Lin, Long & Vong,
*Judging Is Not Enumerating* (arXiv:2608.01000), analyze the asymmetry. Review interrogates the
items the artifact names. An over-inclusion is a written token exposed by one membership query.
An omission names no token; to query it, the reviewer must first author it. An independent
reviewer can still discover omissions—as h-EPI's historical audits did—but no human or machine
can certify recall of an unknown universe under a sub-universe query budget without an
independent coverage certificate.

Measured asymmetry: planted over-inclusions were detected 71–86% of the time and planted
omissions only 10–15%, a 6–7× gap in the smaller tested scales. At 72B the ratio narrows to 2.3×
only by flooding (false-alarm additions on clean keys quintuple, 1.1 → 5.46 per item), which
trades the silent error for the visible one rather than repairing recall. A frontier reviewer
(GPT-5.1) looks symmetric on raw rates (1.4–1.5×) but inverts once corrected for what it does to
a *clean* key: +0.28 over chance at catching over-inclusions versus +0.04 at recovering omissions
on the complete-truth construction, and *negative* (−0.26) on the lexical one. A production
deployment of 43,227 scored items failed omission-first at 10:1.

Consequence for process design: a subtractive review loop with this measured asymmetry risks
pushing an authored specification toward under-acceptance: it removes visible over-inclusions
more readily than it reconstructs omissions.

- **Detection (the reliable families):**
  1. **Identity-keyed accounting invariant.** Let `U` be an independently bound universe,
     `E` the identities enumerated by the checker, `P` those successfully processed, and `R`
     those explicitly refused. Require \(E=U\) and \(E=P\mathbin{\dot\cup}R\); reject duplicate
     identities and overlap, and surface every unknown, unreadable, or unsupported entry in
     `R`. Count equality alone permits swaps, overlap, and duplicates. If the same parser
     constructs `U` and `E`, even the set equations cannot expose omissions before enumeration.
  2. **Prefer operations that fail loudly over operations that silently no-op.** Hill's operational rule; `str.replace`, `dict.get(k, default)`, `if k in a and k in b`, and `grep | true` are named as the same hazard in different clothes.
  3. **A pattern that matches nothing is evidence only if you have separately established that it can match.** At one commit `grep -rn severity tests/` returned zero — true and useful. At a later commit it returned 13. Negative greps require a positive control.
  4. **An external party with a different threat model.** Independent review can add threats the author did not model, but it neither guarantees difference nor certifies completeness.
- **Cost:** (1) is a few lines and is nearly free. (4) is the expensive one and has no substitute.
- **Evidence:** **Moderate-to-strong for the asymmetry** (Chen et al.: four constructions with orthogonal confounds, complete-truth replication, 24× parameter range, six model families, production-scale field data). **Weak for the verifier instances** (Hill: single system).
- **Cite:** Chen et al., arXiv:2608.01000; Hill, arXiv:2608.26183 §§2.2, 7.2, 9.

---

### C7 — Over-mocking / substrate-absent test
*Mechanism 3.*

The subject never executes because it has been replaced by a double; the test exercises the mock. **This is the least-measured class in the taxonomy.** No study retrieved reports a prevalence rate for over-mocked tests specifically.

The nearest measurements are indirect and all point at agent-generated code: Jhanglani, Desai, Kansara & AlOmar (arXiv:2607.12068) analysed 204,673 test files (24,941 human-authored, 179,732 agent-generated) from the AIDev dataset and found agents rely more heavily on unmocked file I/O (4.6% vs 3.5%) and non-deterministic APIs (5.2% vs 3.1%) — the *opposite* failure, insufficient isolation rather than excessive mocking.

- **Detection:** deletion-style extreme mutation of the *subject* (if replacing the real implementation's body with the declared extreme stub changes nothing, the test did not distinguish that deletion in the run) — i.e. C4's detector applied with the mocks in place. Also: assert on an observable the mock cannot produce.
- **Cost:** as C4.
- **Evidence:** **Very weak.** The mechanism is uncontroversial; the prevalence is unmeasured. Flag this as an open measurement gap, not as a solved class.

---

### C8 — Weak acceptance (boundary case)
*Mechanism 5: the check can go red, just not on this fault.*

Distinguished deliberately, because checker mutation alone may miss them; attacks on the artifact, subject, boundary, and enumeration complement it.

- **Detection:** adversarial exploit generation. Produce candidate incorrect artifacts and see whether the check accepts them.
- **Cost:** Rajan (arXiv:2606.16062): $6.04 in API spend plus local Docker for a 49-task audit; $8.29 for a 20-task replication.
- **Prevalence:** **28.5%** of a 49-task SWE-bench Verified sample had test suites weak enough that a Docker-verified incorrect patch passed. **25.0%** on 20 R2E-Gym tasks (a lower bound — single-shot attack budget; SWE-bench restricted to single-shot falls to 18.4%). Independently triangulated: OpenAI reported 59.4% of *failed* tasks having flawed tests; Berkeley's audit broke 8 agent benchmarks via 45 confirmed process-isolation exploits; SWE-ABS rejects 19.71% of agent patches that survived the original suite.
- **Downstream validation:** across 134 frontier model submissions, within the same human-rated difficulty stratum, Pass@1 is **+14.14 pp higher on flagged-hackable tasks** (95% CI [+11.80, +16.48]; p < 10⁻⁶; I² = 0%; 123 of 134 models sign-positive).
- **Evidence:** **Moderate-to-strong.** Audit samples are small (n=49, n=20) but the meta-analysis is n=134 with zero heterogeneity, and four independent measurements agree in direction.
- **Cite:** Rajan, arXiv:2606.16062.

---

## 5. Sub-question 5 — Detection without ground truth

Five families. Which one exposes a fault depends on the declared target, mutation, oracle, and
independent anchor; none is complete across the taxonomy.

### 5.1 Mutation of the check itself
Covered above: refusal-site deletion (C5), extreme mutation (C4). Applied to LLM judges by Delcourt, Ben Chaaben, Rouatbi, Marchezan & Sahraoui (arXiv:2608.14315): 11 mutation operators inject known semantic defects into domain class diagrams, and a judge is scored on whether it detects them. 547 mutants × 6 judge configurations = 3,282 judgments; overall kill ratio 82.4%; correlation with manual precision r = 0.624, pairwise ordering agreement 73.3%.

Two cautions from that study that are candidate design lessons for other judge audits:
- **Verbose judges inflate kill ratios.** Reporting many issues increases the chance of matching an injected defect. One model had a high kill ratio and low manual precision simultaneously. Kill ratio and precision must be reported together.
- **Easy operators dominate the aggregate.** Operators adding unrelated elements scored 95.8% and 97.8%; removing an attribute scored 62.3%. Aggregate scores conceal blind spots; report per-operator.

### 5.2 Injected faults / known-good probes
A low-cost, high-yield method in the cited experiments; its cost and yield are not yet measured for h-EPI.

**The gold-sanity gate.** Before consulting the judge, run each generated check against the *known-correct* artifact. If the check fails on the correct artifact, discard it. Rajan measured what this catches that an LLM judge alone does not: **65 of 105 decisive LLM-generated tests failed on the gold patch itself — a 61.9% per-augmentation defect rate.** The 3-sample self-consistency LLM judge endorsed all six of the sampled invalid augmentations as blocking. The judge correctly read the test code and reasoned about what it would check *if it ran*; it did not catch that the code does not run, runs incorrectly, or asserts the opposite of documented behaviour.

Chen et al. report the same gate from the other direction: discarding any authored verifier that rejects a known-correct probe cuts false-rejection from **58–92% down to ≤5%** — but only 5–39% of suites survive. Most of that loss is recoverable: rewriting each wrong expected value to what a reference execution returns raises yield **3.3–10.6×**, by the largest factor for the weakest author, whose survivors go from 43% vacuous to none. That decomposition is diagnostic: the model chooses discriminating inputs well (94% of wrong solutions still caught once expectations are corrected) and computes their expected outputs badly.

**Ablation worth knowing:** in Rajan's loop, *retry presence* is load-bearing and *retry style* is not. Gate + judge with no retry: 3 of 11 tasks upgraded. Gate + retry + judge: 9 of 11. Replacing the diversity-biased retry prompt with a neutral "generate additional tests" and dropping temperature left the result at 9 of 11. Dropping the judge from 3 samples to 1 cost one task and 56% of the budget.

**Liveness control.** Hill's version, adjacent to every sweep: was the detector demonstrated able to fire, *in this run, on this host*, against a fault-aligned case? Not merely "it has a test." His CI floor caught an untested comparator when the refusal-coverage score dropped below the floor.

### 5.3 Differential and counterfactual execution
Coleman, Shen, Sosonkina & Xu (arXiv:2608.14527) apply identical deterministic faults to an original and an LLM-modernised implementation through injection sites in *shared driver code*, so the converted kernels are the only varying component. 12 sites, 10 fault modes, magnitude-parameterised as η = 2⁻ᴮ, 2,200+ runs. The primary comparison: 200 paired injections with identical outcome classification, iteration count, injection count and final energy — including reproducing all 15 silent data corruptions in one configuration and all 25 in another, at the same magnitudes, phases and seeds.

The candidate design point is that **paired comparison can detect disagreements hidden by matching aggregate distributions**: "identical marginal distributions can conceal disagreements between individual runs."

Another useful control is *dormant-harness validation*: with no site enabled, compare the instrumented build with the reference trajectory at the precision required by the declared contract. A mismatch shows that the instrument is not dormant under that comparison.

### 5.4 Metamorphic relations
Present in the toolkit (Chen et al.'s metamorphic testing lineage; Canedo's suites use them) but with a specific limitation for this class: a metamorphic relation between two quantities that covary under the declared mutation can cancel just as an anchored oracle does. The relation needs a fault-sensitive term or an anchor outside that covariance path; external anchoring is not required for every possible metamorphic relation.

### 5.5 Reference models
Canedo's within-system control is the useful negative result. On one fixed 19-mutant population, a reference-model suite killed 18 of 19; the specification-anchored property suite killed **exactly the same 18**, with an empty diff in both directions. In that system and fault population, the reference model detected no additional mutant once the property suite anchored outside the mutate target. This does not establish equivalence for other properties, models, or fault families.

---

## 6. What transfers from formal methods, and what does not

### Transfers

**The mutate-and-recheck schema.** Kupferman and Vardi's observation motivates two complementary operators for informal checkers: mutate the checker (refusal-site deletion, extreme mutation) or mutate the artifact (tamper fixtures, fault injection, adversarial patch generation). Both appear in the reviewed 2026 informal-checker work.

**The interesting-witness requirement.** Beer et al.'s insistence that a valid formula be accompanied by a demonstration that the validity was non-trivial. This operationalises directly as a liveness control: a passing gate must be accompanied by evidence, in this run, that the gate can refuse.

**Proof- and relevance-core leverage.** Where a checker emits a sound core showing which
premises affected the result, some vacuity questions can be answered without a full rerun. A
mere access or consultation log is insufficient: read-but-ignored values and jointly moving
measurements can still appear covered. The core's own semantics and completeness are part of
the trust boundary.

**The distinction between an unreachable check and a genuinely redundant one.** Formal methods have always had to separate these; so must anything that reports a mutation survivor.

### Does not transfer

**The cited formula-vacuity checks do not detect this state-anchoring case.** Canedo states the bounded negative result explicitly:

> Our defect, a relation between two quantities both produced by the mutated component, is formally non-vacuous under every definition we retrieved, since replacing either side by false falsifies the formula. The check does not merely miss it; **it certifies it healthy.**

Ball and Kupferman's *Vacuity in Testing* (TAP 2008) is the nearest result in the cited vacuity literature: they place a real oracle inside the vacuity framework and define vacuity as branch coverage of it. That construction does not itself impose the provenance restriction considered here; a covarying self-reference can therefore remain outside what its branch criterion detects.

**The surveyed oracle-adequacy metrics do not directly score provenance.** Hossain and Dwyer's 2007–2023 catalogue reports metrics based on whether an element is executed and affects an oracle value through a dependency chain. Schuler and Zeller's checked coverage is a sharp example. A self-referential oracle can score highly on such forward-influence measures while a declared fault moves both sides together. This is a claim about the located metrics and the covarying fault family, not every published metric or every self-reference.

**The vacuity formalism needs a formula.** Informal checkers need not expose a subformula lattice
to quantify over. What survives the transfer is the *operator family* (delete or weaken a clause
and re-check), not the algorithm, not the complexity results, and not the completeness
guarantees.

**Refusal-site deletion cannot find an obligation with no refusal site.** That limit is
structural for this operator; mutations of parsers, enumerators, artifacts, or boundaries may
still expose the omission. §4 C6.

**Mutation scores are operator- and mapping-bounded.** Paul and Holmes (arXiv:2606.10417) extracted 20,729 documented behaviors from 8,922 methods across ten well-tested Java libraries at 93.1% precision and found at least 17.5% entirely untested. In that corpus, **29.6% of methods with a *perfect* mutation kill score still contained at least one extracted documented-behavior gap**, and 38.2% of methods with perfect line coverage did. Spearman ρ was 0.377 for kill score (R² = 0.162) and 0.112 for line coverage. EvoSuite left 20.6% and ASTER 27.1% of extracted behaviors unvalidated. Separately, Just et al. reported that **17% of real faults were coupled to no mutant generated by their common operators.** These are corpus-specific limits, not universal ceilings.

**A perfect mutation score against a narrow operator is not a correctness claim.** Hill states this precisely: 1.000 against a refusal-site deletion operator "means that obligation is discharged, not that the verifier is correct." The score is not an upper bound on anything, because it constrains nothing outside its own enumerated population.

---

## 7. Sub-question 4 — Generated artifacts specifically

Measured rates, ordered by strength of evidence.

| Finding | Rate | n | Source |
|---|---|---|---|
| LLM-generated tests that **fail on the gold solution itself** | **61.9%** | 105 decisive sanity checks | Rajan, 2606.16062 |
| LLM-authored code test suites: **fraction of oracle-correct solutions admitted** | 19–42% | HumanEval+/MBPP+ | Chen et al., 2608.01000 |
| Same, **false-rejection rate before gating** | 58–92% → ≤5% after | four author families | Chen et al. |
| Weakest author's surviving suites that were **vacuous** | 43% → 0% after expected-value repair | — | Chen et al. |
| One-shot 14B suites that **execute correctly and reject the canonical solution** | 70% (115 of 164) | 164 | Chen et al. |
| Agent-generated tests: **unrecognised / non-standard assertion patterns** | 11.58% vs 1.46% human | 204,673 files | Jhanglani et al., 2607.12068 |
| Agent-generated tests: **flakiness candidate rate** | 0.41–0.46 vs 0.30 human | same | Jhanglani et al. |
| Benchmark tasks whose suites **accept a verified-incorrect patch** | 28.5% / 25.0% | 49 / 20 tasks | Rajan |

Two structural findings matter more than any single rate.

**The judging–authoring scissors.** Models judged membership better than they authored the artifact that defined membership in the cited incompleteness-proof construction. The gap was +0.34 to +0.29 F1 across a 24× parameter range. Asked to emit a *predicate* rather than its extension, the same models reached F1 ≈ 0.99 with every predicate executable. The project lesson is conditional: prefer a replayable predicate when it expresses the required set without weakening the obligation, and independently test its boundary. This escape is unavailable when the acceptable set has no adequate rule representation.

**Same-model self-repair failed in the cited experiments.** In Chen et al.'s tested constructions, ten diverse samples surfaced at most 55% of the acceptable set, and the membership judge degraded on the model's own high-temperature proposals. The transferable project rule is narrower: same-model review is not independent evidence; externally anchored checks are needed for claims that require independence.

**An unwitting instance, worth noting.** Jhanglani et al.'s own AST analyser could not parse pytest-style bare `assert` statements. Their tables show 1,730 of 24,941 human files and 29,353 of 179,732 agent files as containing assertions — figures the paper's own threats-to-validity section concedes "invalidated a direct comparison." It is an external example of the same silent-skip pattern.

---

### Repository case study: h-EPI

h-EPI already implements several exact countermeasures relative to declared universes. Snapshot
validation closes selected record identities, span classification, forward obligation coverage,
reverse model-element coverage, and unresolved membership. The inventory loader now enumerates
every descendant of the supplied records directory and rejects symlinks, special entries, and
non-JSON files instead of silently omitting them. This closes that directory boundary; it does
not prove that an operator supplied every semantically relevant record, and it assumes the
directory remains quiescent during its non-atomic enumeration-and-read pass.

The local snapshot-delta implementation is the strongest C2 countermeasure. It loads both
inventories, derives every mechanical field from nine selected top-level and thirteen owned
component kinds, and rejects a caller mismatch even after rehashing. Caller preservation prose
is content-bound but deliberately inert. Tests now compare the production result against an
independently enumerated fixture surface as well as literal counts and symmetric differences.
This is strong tamper and self-consistency evidence, not an independent semantic oracle or a
second production implementation.

Other classes remain open. All nine semantic attack families, including `NON_VACUITY`, are
synthesized but deferred because typed fixtures, comparators, expectations, and executors are
missing. HRC-1 specifies 34 mutations and six benign controls, yet its runner verifies only
declared exposure-token correspondence and explicitly denies mutation execution, execution
evidence, producer blindness, and semantic effect. There is no systematic refusal-site deletion
sweep, assertion-reachability instrument, or extreme-mutation campaign.

The project also exposes a cross-cutting class missing from the original taxonomy:
**intrinsic-versus-contextual self-confirmation**. A record can have a valid schema and
self-consistent content hash while making a false claim about another artifact or epoch.
Standalone delta validation therefore checks only intrinsic shape and identity, while the
pipeline replays it against both exact inventories. The same distinction applies to publication
authority, HRC fixture pins, source replay, and mutable self-hashes.

For this repository, four assurance dimensions should remain separate: coverage of an
independently bound input universe, provenance of the expected value, execution and refusal
liveness, and binding to the correct context, epoch, and external trust root. Structural
integrity is a fifth dimension; semantic fidelity remains outside all five unless separately
reviewed.

---

## 8. Sub-question 6 — Candidate audit sequence

For an organisation whose verification artifacts are partly machine-generated. The ordering is
an engineering proposal assembled from heterogeneous studies, not a generally validated
cost-optimal rule. Each tier states what it catches and what it misses.

### Tier 0 — Static, no subject execution; h-EPI cost unmeasured
1. **Anchoring / provenance check.** For each assertion, does the expected-side value flow from the artifact under check? Check all four channels: expected value, tolerance band, conditioning variable, generator. A bounded static graph can answer its modeled flow question; the sizing half and behavior outside that model require separate inspection.
   *Catches:* some C2 risks in the declared graph. *Misses:* behavior outside the model and the other classes. *Cost:* unmeasured for h-EPI. *Note:* the cited paper's sweep found no matching shipping linter.
2. **Identity-keyed accounting.** Bind an independent universe `U`; require the enumerated
   identities `E` to equal `U`, then require successfully processed `P` and explicitly refused
   `R` to be disjoint, duplicate-free, and exactly partition `E`. Surface unknown entries as
   refusals. A count equation or parser-defined universe is insufficient.
   *Catches:* C6 after independent enumeration. *Cost:* small once a manifest exists.
3. **Fail-loud audit.** Grep the checker for silent-no-op idioms: `str.replace`, `dict.get(k, default)`, `if k in a and k in b`, `grep | true`, swallowed exceptions, default enum branches, `rglob`/`is_file` asymmetries.
   *Catches:* C5, C6 precursors. *Cost:* an afternoon, once.

### Tier 1 — One extra execution per gate
4. **Assertion or verdict-sink reachability.** Instrument assertions, exceptions, process exits,
   validator refusals, and proof-checker failures rather than assuming every oracle is a value
   comparison.
   *Catches:* C3. *Misses:* C2, C4, C6. *Cost:* one instrumented run.
5. **Fault-aligned liveness control adjacent to every refusal family.** Does the checker pass on
   a known-good artifact and refuse an independently specified bad artifact for this exact
   obligation, in this run, on this host?
   *Catches:* gross C1 and C5; it can expose C2 when the negative control independently specifies
   the covarying fault. *Misses:* C2 when the control is generic or shares the same anchor.
   *Cost:* one run.
6. **Paired positive and negative sanity gate on every generated check.** Run the check against a
   known-correct artifact and an independently specified fault in its claimed family before
   consulting any judge. The positive alone catches false rejection but says nothing about
   rejecting defects.
   *Catches:* invalid gold-rejecting checks and gross weak acceptance. *Cost:* at least two
   executions per generated check.
7. **Empty / null / absent-input probe where the contract requires rejection.** Feed the checker
   nothing only when empty input is independently specified as invalid.
   *Catches:* the four-byte forgery class within that contract. *Cost:* trivial.

### Tier 2 — Minutes to hours, automated
8. **Refusal-site deletion sweep** over the checker's own source, with the Tier-1 controls as the kill predicate.
   *Catches:* C5. *Misses:* C6 (absent obligations), C2 (an anchored oracle's refusal *is* live). *Cost:* ~6 minutes for 143 sites. *Set a CI floor and let it fail the build.*
9. **Extreme mutation** of the artifact under check.
   *Catches:* C4, C7. *Cost:* one mutant per method.
10. **Vacuity check** wherever the specification is temporal or has a formula.
    *Catches:* C1. *Cost:* near-free with proof cores.

### Tier 3 — Expensive, periodic rather than per-commit
11. **Full instruction-level mutation.** Scope it as Google does: diff-based, one mutant per covered line, arid-line suppression. Report property-only survivor diffs rather than scores.
    *Catches:* C2's *cost* (the sizing half), residual C4. *Misses:* 17% of real faults are coupled to no common-operator mutant; 29.6% behavioural gap survives a perfect score.
12. **Adversarial exploit generation** against the check.
    *Catches:* C8. *Cost:* ~$6 per 49 tasks plus containerised execution.
13. **Differential fault injection** with paired comparison, where you have two implementations or a reference.
    *Catches:* off-nominal divergence invisible to nominal tests. *Cost:* thousands of runs.

### Tier 4 — Independent threat-model review
14. **An external party with a different threat model**, running your protocol against artifacts they built.
    *Catches:* omissions outside the currently bound universe. This is the remaining response
    when no independent manifest or coverage certificate exists; it discovers omissions but
    does not certify completeness. *Cost:* real, and irreducible.

### Reporting rules that go with the battery
- **Report per-operator, not aggregate.** Easy operators inflate kill ratios (95.8%, 97.8% vs 62.3% in the judge study).
- **Report kill ratio and precision together.** A verbose checker scores well on the first and badly on the second.
- **Report survivor diffs by identity, not score deltas.** Scores move when the denominator moves; Hill's four fixes showed a −0.003 score change concealing exactly zero improvement on the pre-existing population.
- **State the mutate scope.** Changing the declared target may change an oracle's anchoring
  classification.
- **Pre-register predictions.** Both Canedo and Coleman et al. recorded predictions before intervening and reported where they were wrong; that is what distinguishes the measurement from the anecdote.

---

## 9. On the externally reported 11-of-15 ratio

The 11-of-15 observation belongs to the original external incident record; it is not a count in
the h-EPI repository and cannot be refreshed from the current test corpus.

There is no published base rate for "fraction of errors made while building a verification instrument that reduce to self-confirmation." The closest available comparison is Hill's §9: **seven instrument failures during a single study, four of them inside instruments built specifically to detect this class, across three distinct tools — and the most dangerous was not the one that broke, it was the one that returned a perfect 1.000.**

Canedo reports the same reflexively: a reproducibility gate that "agreed with itself while disagreeing with the draft on 5 figures, and it printed a table rather than failing." Rajan's headline result (10 of 11 tasks upgraded) did not survive Docker re-verification and became 9 of 11 with a gate. Chen et al. built four constructions with orthogonal confounds specifically because using a judge to grade judge-authorship is circular.

The pattern is consistent with those studies, but a single incident cannot establish a rate or
transport their prevalence. The applicable discipline is narrower: validate each instrument's
declared universe, liveness, provenance, and contextual binding before using its output as a
finding.

---

## 10. Bibliography

**Formal methods — vacuity**
- Beer, Ben-David, Eisner & Rodeh. *Efficient Detection of Vacuity in ACTL Formulas.* CAV 1997, LNCS 1254, 279–290. Extended: *Formal Methods in System Design* 18(2):141–163, 2001. — Origin; the ~20% IBM Haifa figure.
- Kupferman & Vardi. *Vacuity Detection in Temporal Model Checking.* — General method for CTL*; vacuity/coverage equivalence; PSPACE-completeness of interesting witnesses.
- Armoni, Fix, Flaisher, Grumberg, Piterman, Tiemeyer & Vardi. *Enhanced Vacuity Detection in Linear Temporal Logic.* CAV 2003, LNCS 2725, 368–380.
- Ben-David, Copty, Fisman & Ruah. *VAQTREE* (resolution-proof vacuity from BMC). FMSD.
- Ben-David, Fisman & Ruah. *Vacuity in Practice: Temporal Antecedent Failure.* FMSD 46(1), 2015.
- Purandare & Somenzi. Thorough vacuity for CTL at small overhead.
- Ball & Kupferman. *Vacuity in Testing.* TAP 2008, LNCS 4966, 4–17. — The nearest miss; puts an oracle inside the vacuity framework without asking the provenance question.
- Beatty & Bryant. DAC 1994. — Antecedent failure, first observation.

**Test-suite and oracle adequacy**
- Niedermayr, Juergens & Wagner. *Will My Tests Tell Me If I Break This Code?* CSED 2016. — Pseudo-tested methods; 19 projects, median 10.1%, range 6–53%.
- Vera-Pérez, Danglot, Monperrus & Baudry. *A Comprehensive Study of Pseudo-tested Methods.* EMSE 24(3), 2018. arXiv:1807.05030. — 28K+ methods; 1–46%; first replication.
- Delplanque, Ducasse, Polito, Black & Etien. *Rotten Green Tests.* ICSE 2019. — 294 of 19,905 Pharo tests; DrTest.
- Aranega, Delplanque, Martinez, Black, Ducasse, Etien, Fuhrman & Polito. *Rotten Green Tests in Java, Pharo and Python.* EMSE 26:130, 2021.
- Martinez et al. *RTj: A Java Framework for Detecting and Refactoring Rotten Green Test Cases.* arXiv:1912.07322.
- Schuler & Zeller. *Checked Coverage: An Indicator for Oracle Quality.* STVR 23(7):531–551, 2013.
- Hossain & Dwyer. Survey of oracle-based adequacy metrics, 2007–2023.
- Petrović & Ivanković. *State of Mutation Testing at Google.* ICSE-SEIP 2018. — Diff-based, one mutant per covered line, arid-line suppression.
- Jia & Harman. *An Analysis and Survey of the Development of Mutation Testing.* TSE 37(5), 2011.
- Just et al. — 17% of real faults coupled to no common-operator mutant.
- Jahangirova et al. — Oracle false positives/negatives; OASIs.
- Ravi & Coblenz. — Property vs unit tests over 40 Python projects; unit outkill ~3:1; 15% overlap; 96% of mutations found within 350 inputs.

**2026 preprints — the informal-checker literature**
- Canedo. *Oracles That Cannot Fail: Anchoring and the Expectation That Moves With the Fault.* arXiv:2608.17214. Dataset: doi:10.5281/zenodo.21940547.
- Hill. *Four Ways to Forge a Bundle My Own Verifier Calls Clean: Refusal-Site Mutation Testing of an Evidence-Bundle Verifier.* arXiv:2608.26183. Code: github.com/egnaro9/vac-protocol; doi:10.5281/zenodo.22018308.
- Chen, Chen, Lin, Long & Vong. *Judging Is Not Enumerating: Silent Omissions in LLM-Authored Acceptable Sets.* arXiv:2608.01000.
- Rajan. *Auditing Reward Hackability in Code RL Training Environments.* arXiv:2606.16062.
- Paul & Holmes. *Beyond Coverage and Kill Scores: Empirically Measuring Test Suite Behavioural Gaps.* arXiv:2606.10417.
- Delcourt, Ben Chaaben, Rouatbi, Marchezan & Sahraoui. *Breaking Models to Test the Judge.* MODELS 2026, arXiv:2608.14315.
- Coleman, Shen, Sosonkina & Xu. *Validating LLM-Modernized Scientific Software Through Differential Fault Injection.* arXiv:2608.14527.
- Jhanglani, Desai, Kansara & AlOmar. *Beyond Test Presence.* arXiv:2607.12068.
- Krishnamurthy, Chitnis & Prodromakis. *Closing the Loop on LLM-Generated RTL Assertions with Quality-Aware Formal Verification.* arXiv:2606.21451.

**Standards**
- CWE-703 (improper check for unusual conditions), CWE-754 (improper check for unusual or exceptional conditions), CWE-390 (detection of error condition without action).
