# The Asymmetry Between Refuting and Certifying That a Test Suite Holds a Specification Clause

**A literature review and decision procedure**

Compiled 1 September 2026. Sources: ACM/IEEE/Springer venues via web retrieval, alphaXiv paper corpus, and Consensus. Where a figure is reported it is taken from the paper's own text; where a figure is absent from the literature this is stated rather than estimated.

**Repository status, 4 September 2026.** This is an advisory literature review, not CR-1.0 authority, a semantic-fidelity result, or an accepted h-EPI engineering decision. None of the added sources has yet been entered through the repository's primary-inspection research ledger, so the literature claims below remain external synthesis. Repository examples establish only the behavior of the named local code, fixtures, records, and replay scopes.

**Concrete project case.** The h-EPI repository does not contain a 26-clause, 701-test labelled mutation experiment. Its published 0.5 tranche recorded 499 passing Python tests in each of normal and optimized execution. The current uncommitted tranche adds exact two-inventory snapshot-delta derivation and stricter inventory accounting; its final local verification count is recorded in Section 6. Those counts are operational regression evidence, not a count of independently tested semantic commitments.

The project's actual qualification design is HRC-1, a finite controller containing 17 source obligations, 13 discriminator families, 34 planted mutations, and six benign controls. Together these define 40 cases and 82 expected case/exposure tokens. No blind candidate run or mutation-execution evidence is currently committed. The implemented qualifier compares a frozen report's declared tokens with the controller after freeze while explicitly denying that it verified mutation execution, execution evidence, producer blindness, semantic fidelity, or truth.

The relevant question is therefore not whether a passing test count “holds” CR-1.0. It is which precisely scoped claims each evidence surface can establish, which counterexamples can be independently replayed, and what remains unresolved.

---

## 0. Executive verdict

**Sub-question 1 — is the asymmetry established, folklore, contested, or unaddressed?**

**Split verdict.** The claim as posed bundles three propositions with three different statuses:

| Proposition | Status |
|---|---|
| Unrestricted test adequacy can be decided from a finite suite | **False in general** (Budd & Angluin 1982); finite exhaustive and proof-carrying scopes are exceptions |
| Static inspection always decides that a suite misses C | **False as stated** — undecidable in general; particular failed necessary conditions can have certificates |
| Refutation sometimes has a finite certificate when unrestricted confirmation does not | **Established for named constructions, including model-checking counterexamples and vacuity checks** |
| Oracle-provenance in one bounded static graph model | **Newly stated and measured, August 2026** (Canedo), n = 1 system |

The correct general statement is a **claim-scoped certificate asymmetry, not a decidability asymmetry**. A check can certify a finite mechanical relation within a frozen scope. A valid counterexample can refute a declared universal within that scope. Neither result automatically establishes semantic fidelity, uniquely identifies the cause of failure, or generalizes beyond the checked domain. For unrestricted program/test adequacy, confirmation quantifies over an open class of faulty implementations and cannot be reduced to a finite passing test set; finite exhaustive domains and proof-carrying systems are important exceptions to any blanket claim that positive certification is impossible.

The specific assembly — claim-scoped one-sided certificates for a specification-clause-versus-suite instrument — was not located in the reviewed sources. Its components exist; this review does not establish global novelty.

---

## 1. The formal status

### 1.1 The negative half is a theorem, and it is old

Budd and Angluin (*Two notions of correctness and their relation to testing*, Acta Informatica 18(1):31–45, 1982) examined two readings of "test data demonstrates correctness," asked under what conditions sufficient data exists and whether it can be automatically detected or generated, and established the relation between these questions and deciding equivalence of two programs.

The standard summary in the mutation literature, from DeMillo and Offutt (TSE 1991): Budd and Angluin show there is no effective procedure either for generating adequate test sets or for detecting that a given test set is adequate; the practical problem is that adequacy asks test cases to distinguish a correct program from all possible incorrect programs, which is undecidable.

Budd, DeMillo and Lipton had already noted in *Axiomatizing software test adequacy* that except for trivial classes of programs the conclusion is formally undecidable, and that this had been the major stumbling block in formalising testing.

So: **the impossibility result for unrestricted test adequacy is settled and has been for 44 years.** It does not rule out a scoped positive certificate for a finite exhaustively checked relation, or a proof from explicit premises.

### 1.2 The positive half is false as posed

"This suite does not hold C" is not statically decidable either:

- Unreachability is itself undecidable.
- Establishing that a specific mutant survives, without executing it, requires deciding a property of the mutant's behaviour.
- Even *with* execution, deciding whether an unkilled mutant is unkillable requires deciding program equivalence, the same undecidable problem Budd and Angluin identified.

What is true is weaker and more useful.

### 1.3 The correct statement: necessary conditions and refutation certificates

Detection decomposes into necessary conditions. The lineage:

- **PIE** — Voas, *PIE: a dynamic failure-based technique*, TSE 18(8):717–727, 1992. Propagation, Infection, Execution.
- **RIP** — Ammann and Offutt, *Introduction to Software Testing*, CUP 2008. Reachability, Infection, Propagation.
- **RIPR** — Li and Offutt. Adds Revealability: the test oracle must detect and report the propagated error.

The four conditions are individually necessary. Therefore:

> Proving that any one necessary condition fails refutes detection for the declared target, fault, run model, and verdict mapping.

For reachability, a sound proof or an over-approximation that excludes every path to the target
can supply such a certificate. For revealability, the corresponding certificate must exclude
every relevant effect path from the infected state to every declared verdict sink. Absence from
an under-approximation cannot establish either result: it shows only that the analysis found no
witness. Infection and propagation remain harder in general. This directionality is the
practical reason the decision procedure in Part 5 separates observations, heuristics, and
certificates.

A formal treatment of the first three conditions using Dijkstra guarded commands and the weakest-precondition transformer appears in *Formal Analysis of Reachability, Infection and Propagation Conditions in Mutation Testing* (arXiv:2410.21904, Sharif University, 2024), which generates full test specifications for killing surviving mutants.

### 1.4 The precedent is in model checking, under the name *vacuity*

Within the reviewed sources, model-checking vacuity provides the clearest established precedent,
and it comes from formal verification rather than testing.

**Beer, Ben-David, Eisner and Rodeh** (*Efficient detection of vacuity in temporal model checking*, FMSD 18(2):141–163, 2001; earlier ACTL version 1997) observed that model checkers generate counterexamples for invalid formulas but give no comparable feedback for valid ones, because valid formulas can hide real problems. Propositional antecedent failure — a formula trivially valid because the antecedent is unsatisfiable — generalises to vacuity: a subformula that does not affect the truth value.

The prevalence figure, reported by IBM Haifa and quoted by Gurfinkel and Chechik: **typically 20% of specifications pass vacuously during the first formal verification runs of a new hardware design, and vacuous passes always point to a real problem in either the design, the specification, or the environment.**

**Kupferman and Vardi** (*Vacuity detection in temporal model checking*, STTT 4(2):224–233, 2003) and subsequent surveys argue that vacuity and coverage are, in many aspects, essentially the same check: both repeat the verification process on some mutant input, with coverage mutating the system and vacuity mutating the specification.

**Ball and Kupferman**, *Vacuity in Testing*, TAP 2008 (LNCS 4966, pp. 4–17), carry this directly into testing. Their framing: if the system satisfies the *mutated specification*, some elements of the specification play no role in its satisfaction, so the specification is satisfied vacuously; if the *mutated system* satisfies the specification, some elements of the system are not covered by the specification. They note that coverage in model checking was adopted from testing, and propose that testing now inherit the theory of vacuity in return.

**Kupferman, Li and Seshia**, *A theory of mutations with applications to vacuity, coverage, and fault tolerance*, FMCAD 2008, unifies the three under a single mutation-theoretic account.

The implication for the present question is narrower: a proof certificate and a relevance or non-vacuity certificate answer different questions. Mutation is one way to probe relevance. A proof combined with model-existence, dependency, and relevance obligations can also establish a scoped non-vacuity claim. Formal verification does not make vacuity disappear; it supplies explicit ways to state and check the remaining obligation.

### 1.5 What the reviewed sources add

Among the sources reviewed through August 2026, one located paper states the
static-decidability half explicitly for the oracle-provenance case:

**Canedo, *Oracles That Cannot Fail: Anchoring and the Expectation That Moves With the Fault*, arXiv:2608.17214, 17 August 2026.**

The core definitions:

> **Specification-anchored:** the expected value is composed in the test from constants, published procedures, or specification values fixed outside the mutate target.
>
> **State-anchored:** the expected value is obtained, directly or transitively, from the running system under test.

And the claim that matters here:

> Anchoring is binary, decidable without running anything, and relative to a declared mutate target.

The mechanism is a cancellation. For a relative oracle, if a mutation scales measurement and
expectation together so that `m' = km` and `e' = ke`, with `e != 0` and `k != 0`, then
`m'/e' = m/e` exactly. A fixed absolute-error test `|m - e| <= tau` is not equivalent:
`|m' - e'| = |k||m - e|` in every case. Its Boolean verdict may still remain unchanged when the
difference is zero or stays on the same side of `tau`; invariance across the declared domain
requires those conditions or a covarying tolerance or other decision term. For the declared
target, fault family, decision expression, and input domain, either shape can become invariant
to that fault. It may still fail for unrelated defects.

Two boundaries the paper draws itself, both important:

1. **Only the bounded flow half is mechanically approachable.** A conservative static model can decide the predicate on its declared import-and-call graph. Arbitrary dynamic Python behavior, reflection, plugins, and runtime dispatch prevent this from being a general decidability claim. The *sizing* condition — whether the anchored value actually sizes the comparison such that the fault cancels — is not supplied by that analysis; establishing it required reading each oracle.
2. **Scope relativity.** An oracle is not state-anchored in the abstract; it is state-anchored with respect to a declared mutate target. Measured directly (Section 7.5 of the paper): the same unchanged oracle recovered 0 mutants under one declared scope and 3 under a wider scope containing the value's producer.

So the answer to "has this been stated?" is: **yes, in August 2026, for one of the four RIPR conditions, with the bounded flow analysis separated from the sizing question, and in a single-subject study by a single author.** It is not established as a prevalence result. It is stated and measured once.

### 1.6 The asymmetry, measured accidentally

The cleanest empirical demonstration was produced by people trying to do something else.

**Aghamohammadi and Mirian-Hosseinabadi**, *The Threat to the Validity of Predictive Mutation Testing: The Impact of Uncovered Mutants* (arXiv:2005.11532; STVR 2021).

Predictive Mutation Testing (Zhang, Zhang, Harman, Hao, Jia, Zhang, TSE 45(9):898–918, 2019; extended cross-project by Mao, Chen and Zhang, ICST 2019) predicts whether a mutant is killed without executing it, reporting AUC around 0.80 (Zhang et al., 163 projects) and 0.89 (Mao et al., 654 projects).

In the 654-project corpus:

| Quantity | Value |
|---|---|
| Covered mutants | 1,137,336 |
| Uncovered mutants | 1,894,940 (**62% of total**) |
| PMT AUC, all data | 0.814 mean / 0.833 median |
| PMT AUC, covered mutants only | **0.540 mean / 0.516 median** |
| Test projects worse than random | 18 of 66 (**27%**) |
| Improved model (RF + gradient boosting, ADASYN) | 0.613 mean / 0.609 median |
| Balanced accuracy: PMT(95) → improved | 0.122 → 0.230 |
| MCC: PMT(95) → improved | 0.138 → 0.239 |

Every non-executed mutant is certainly survived. Once that free negative is removed, predicting kill-versus-survive from static and dynamic features collapses to barely better than a coin flip.

**This quantifies one instance of the asymmetry.** Removing uncovered mutants reduced mean AUC from 0.814 to 0.540 in that corpus, showing that the easy one-sided negative carried much of the model's measured discrimination there. It does not identify the exact fraction of predictive power or establish the same decomposition elsewhere.

---

## 2. Static predictors of mutation survival (Sub-question 2)

### 2.1 Assertion quantity and assertion coverage

**Zhang and Mesbah**, *Assertions Are Strongly Correlated with Test Suite Effectiveness*, ESEC/FSE 2015, pp. 214–224. Five Java projects, 329,600 SLOC, 5,892 test cases, 24,701 assertions, 6,700 composed test suites, PIT default operators.

| Relationship | Pearson r or adjusted R² | Kendall τ |
|---|---|---|
| Assertion quantity vs. mutation score (random suites) | Pearson r 0.927–0.973 | τ 0.889–0.970 |
| Assertion quantity vs. mutation score (suite size controlled) | Pearson r 0.928–0.976 | τ 0.781–0.961 |
| Assertion (checked) coverage vs. mutation score | adjusted R² 0.94–0.99 | **τ 0.88–0.91** |
| Assertion coverage vs. *explicit* mutation score | adjusted R² 0.80–0.99 | τ 0.80–0.90 |
| Statement coverage vs. mutation score, assertion coverage controlled | — | 0.50–0.76 |
| Statement coverage vs. explicit mutation score, assertion coverage controlled | — | **0.01–0.63** |

Two further figures worth carrying:

- **28%–73%** of killed mutants across the five projects were killed *explicitly*, i.e. by an assertion rather than by an uncaught exception or crash. Explicitly-detectable mutants cannot be detected by non-assertion statements.
- Sensitivity: on JFreeChart, a **+4%** increase in assertion coverage produced roughly **+12.4%** mutation score and **+11%** explicit mutation score. A comparable +4% in statement coverage did not reliably move either.

Assertion coverage here is *checked coverage* (Schuler and Zeller, ICST 2011; STVR 23(7):531–551, 2013), computed by dynamic backward slicing from assertion statements. **It is not static.**

### 2.2 Assertion type effects — real, significant, and small

Same study, 9,177 JFreeChart assertions, 50 sample suites of 100 assertions per type, one-way ANOVA plus Tukey HSD.

| Comparison | Difference in mutation score | p adj |
|---|---|---|
| Boolean vs. Object | −0.0002 | 0.9985 (n.s.) |
| Number vs. Boolean | **−0.0470** | < 0.0001 |
| String vs. Number | −0.0156 | < 0.0001 |
| assertNull/NotNull vs. assertTrue/False | −0.0103 | 1e−07 |
| assertEquals/NotEquals vs. assertNull/NotNull | −0.0133 | < 0.0001 |

Ranking: boolean and object content types beat number, which beats string; `assertTrue/False` beats `assertEquals/Not`, which beats `assert(Not)Null`. F values are enormous (1544 and 87.87) but the effect sizes are 1–5 percentage points of mutation score. **Do not build a screen on assertion type.**

### 2.3 Code observability — the best purely static family

**Zhu, Zaidman and Panichella**, *How to kill them all: An exploratory study on the impact of code observability on mutation testing*, JSS 173:110864, 2021. Six Java projects, 467,017 LOC, 13,558 tests, 106,892 mutants (62,857 killed), 19,790 methods analysed, PIT 1.4.0 defaults, Spearman rank-order plus Random Forest.

**Baseline — 64 conventional OO and complexity metrics:** all |rho| < 0.27. Strongest were NSUP (number of superclasses) and DIT at −0.2634, then R-R (reuse ratio) −0.2524 and HIER −0.212. Cyclomatic complexity, contrary to expectation, was 0.0398. Method length was approximately zero and not significant.

**Nineteen proposed observability metrics:**

| Metric | Spearman rho | Category |
|---|---|---|
| `test_distance` | **−0.4921** | test directness |
| `direct_test_no` | **0.4177** | test directness |
| `assertion_density` | 0.4096 | assertion |
| `assertion-McCabe_Ratio` | 0.3956 | assertion |
| `assertion_no` | 0.3858 | assertion |
| `non_void_percent` | 0.2424 | return type |
| `getter_percentage` | −0.153 | return type |
| `is_void` | −0.1427 | return type |
| `is_static` | 0.1137 | access modifier |
| `nested_depth` | 0.053 | fault masking |
| `is_public` | −0.0639 | access modifier |
| `method_length` | ≈0 (n.s.) | fault masking |

**Random Forest feature importance:** `test_distance` ranked first in five of six projects and overall, with importance 0.29 against 0.06 for the runner-up — more than **4.8x** the next feature. Among methods that *are* directly tested, `is_void` takes first place at 0.22.

**Classification AUC (all data):** ZeroR 0.500, existing metrics 0.928, observability metrics 0.937, combined 0.963.

**Critical caveat on the assertion metrics.** In this corpus, assertion metrics are nearly collinear with test directness: `direct_test_no` vs `assertion_no` is 0.9604, vs `assertion-McCabe` 0.9472, vs `assertion_distance` 0.9334; `test_distance` against all three is −0.8707. In these six projects there are essentially no tests without assertions, so assertion count adds little information beyond "is there a direct test." **Assertion density is not an independent signal in this dataset.** Whether it is in yours depends on whether you have assertion-free tests.

**Anti-pattern rules** (J48 decision tree, leaves selected at accuracy >= 0.8, LOW = mutation score < 0.5). Six were validated by manual refactoring of 16 code fragments. The two operationally useful thresholds:

- `test_distance > 5` — no direct test. Fixed by adding a direct test.
- `test_distance <= 5` combined with `is_void = 1` and `assertion_density <= 0.14` (or `<= 0.22` at higher statement counts) — directly tested but under-asserted. Fixed by adding assertions.

Summary of the manual study: most cases fixed by adding direct tests when `test_distance > 5`; most cases fixed by adding assertions when `test_distance <= 5`; private methods required refactoring to protected/public; three void methods required refactoring to non-void; one required an added getter.

### 2.4 State field coverage — the first fully static oracle-quality metric

**Molina, Aguirre and Gorla**, *State Field Coverage: A Metric for Oracle Quality*, ASE 2025 (arXiv:2510.03071).

The metric: build a *type graph* from a class's reachable field definitions; the coverable labels are the edges plus a special label `f+` for each iterable field; state field coverage is the proportion of coverable labels the oracle references, directly or via invoked methods. Computed by parsing with JavaParser — **no execution.**

Subjects: 273 representation invariants from Korat across 11 data-structure classes; 249,027 test assertions from 51 Defects4J 2.0.1 versions across 215 classes and 97,267 tests. Correlation analysis on a 17-version subset with 83,032 assertions.

| Measure | Representation invariants | Test assertions |
|---|---|---|
| State field coverage range (mean) | 11.7%–100% (70.3%) | 0%–64.5% (**14.3%**) |
| Mutation score range (mean) | 9%–100% (50.2%) | 2.5%–92.8% (34.1%) |
| Checked coverage (mean) | — | 0%–68% (27.8%) |
| Pearson vs. mutation score | **0.54** | **~0.45** pooled |
| Pearson, per-project | — | **> 0.96** for most projects |

Over 75% of test assertions fall below 22% state field coverage.

**Cost, which is the point:**

| Analysis | Mean per project | Total |
|---|---|---|
| State field coverage (static) | 5,164 s (~1.4 h) | ~22 h, **~6 s per test** |
| Checked coverage (dynamic slicing) | 20,327 s (~5.6 h) | ~34 h over 6 projects |
| Mutation analysis | 72,903 s (~20 h) | **> 300 h (~12.5 days)** |

**Validation of the static approximation.** A dynamic variant of the metric was built for comparison. The static and dynamic computations agreed *exactly* in 40% of cases and differed by less than 10% in the remaining 60%.

**Real-fault result.** Ordering tests to maximise state field coverage growth beat random ordering at reaching the failing test in 17 of 27 Defects4J bugs (63%), requiring **34.7x fewer tests on average**; random won the other 10 cases by 1.8x.

**Limitations that matter for the negative screen.** Stateless classes yield an empty type graph and therefore 0% coverage vacuously — 38 of 51 project versions (75%) had non-empty type graphs, and 27 of those 38 (71%) had positive coverage. Assertions that verify only method return values yield 0% coverage under the current definition. A zero supports a scoped negative only when the type graph is non-empty, the obligation governs object state rather than a return value, and the metric-to-obligation mapping is independently justified.

### 2.5 Behavioural gaps — a structurally analogous problem

**Paul and Holmes** (UBC), *Beyond Coverage and Kill Scores: Empirically Measuring Test Suite Behavioural Gaps*, arXiv:2606.10417, June 2026.

This is structurally analogous to clause-to-suite analysis: documented expected behaviors are mapped against an existing suite, with unmapped ones emitted as gaps. Their Java/LLM pipeline differs materially from h-EPI's Python, JSON, Lean, and semantic-model workflow. BFINDER builds per-method call graphs, extracts expected behaviors from documentation and source with an LLM, maps test cases to behaviors, and emits `UTB = EB − TB`.

Ten Defects4J Java libraries, 8,922 methods, 20,729 extracted behaviours.

| Measure | Value |
|---|---|
| Behaviour extraction precision | **93.1% ± 2.7%** |
| Untested-behaviour identification precision | **71.3% ± 5.6%** |
| Behavioural gap, developer suites | **17.5%** (range 6.6%–29.3%; 15.1% excluding jfreechart) |
| Behavioural gap, EvoSuite | 20.6% |
| Behavioural gap, ASTER | 27.1% |
| Cost | 3–4 min/method local; < 10 s/method commercial; 6K–8K tokens/method |

**The result that bears hardest on this review — behavioural gaps do not alias structural metrics:**

| Structural metric | Spearman rho | OLS R² | Cohen's h | Methods at *perfect* score still containing a gap |
|---|---|---|---|---|
| Line coverage | 0.112 | 0.007 | 0.22 | **38.2%** |
| Mutation kill score | 0.377 | 0.162 | 0.41 | **29.6%** |

Untested behaviours concentrate somewhat in low-kill-score methods (44.3% of gaps fall in the <= 70% kill bucket, which holds only 24.3% of methods), but kill score explains only 16% of the variance. Chi-square homogeneity p < 0.001 for both.

Every project exhibited gaps, including `commons-cli` at 98.2% line coverage and 93% kill score (6.6% gap) and `commons-csv` at 99.6% and 95% (9.1% gap).

Most common gap categories: exceptions, side effects, null/empty input handling, construction and configuration, content of returned value, algorithmic logic. None judged inherently untestable. Five gaps revealed genuine code-documentation inconsistencies, reported upstream and all fixed.

**Read this as a corpus-specific limit on what one mutation score implied.** In that study, 29.6% of methods with a perfect mutation kill score still had at least one extracted documented-behavior gap. A survival or kill result is therefore a statement about its operator population and mapping, not automatically about a broader clause.

---

## 3. Self-fulfilling oracles (Sub-question 3)

### 3.1 The name problem

No single established academic term was located in the reviewed sources. The candidates:

- **"Tautological test"** — practitioner folklore only (blog literature). The associated rule of thumb is *never calculate an expected value within your test; logic driving assertions is a smell*.
- **"Redundant Assertion"** — a catalogued test smell (Peruma's extension of van Deursen et al.'s catalogue): assertion statements that are always true or always false. Narrower than the phenomenon.
- **"Regression oracle" / "characterization test" / "golden master"** — the deliberate version, where recording current behaviour is the intent.
- **"Oracle anchoring"** — Canedo 2026. The formal treatment located in this review.

### 3.2 Oracle anchoring: the formalisation

Canedo (arXiv:2608.17214) identifies **four channels** by which a value from the mutate target reaches a verdict. Three lie in the assertion, one upstream:

1. **Expected value** — what the assertion compares against. *The only one the cited review
   located in prior literature.*
2. **Tolerance band** — the width of the acceptable interval.
3. **Conditioning variable** — the state the assertion is evaluated at.
4. **Generator** — the scenario placement, which runs before any assertion exists.

The measured cost distribution is the surprise: in the study's costliest oracle, closing the expected-value channel recovered **1** mutant; closing the conditioning variable recovered **8** more. The channel the literature names is not the expensive one.

**The sizing condition** — the paper's own refinement, and the reason this is not a blanket prohibition:

> Self-reference costs detection when the anchored value sizes the comparison the oracle makes and the fault moves it proportionally, so that measured and expected cancel. Where the anchored value only places a scenario, feeds a bound carrying large slack, or measures a quantity another suite covers directly, the self-reference is latent: real, statically identifiable, and free.

In the study's own data a blanket claim would be wrong 3 times out of 6. Of 6 ablated instances, the **2 that sized their comparison carried 11 of the 12 recovered mutants.**

### 3.3 Measurements

**Canedo 2026.** Deployed air traffic control simulator, 12 model-free property suites, 4 modules, 366 distinct mutants (Stryker).

| Intervention | Effect |
|---|---|
| Property suites vs. pre-existing hand-written tests | **+3 mutants** of 366 (4 after re-anchoring one suite) |
| Efficiency per test | 6x to 33x more efficient |
| Re-anchor holding oracle on published procedure (no production change) | **recovers 8 of 46** |
| Deliberately state-anchor a healthy debounce oracle | **costs 4 of 19** |
| Reference-model suite on debounce population | kills 18 of 19 — *exactly what specification anchoring kills* |
| Same oracle, narrow mutate scope excluding the value's producer | recovery **0** |
| Same oracle, scope including the producer | recovery **+3**, all 3 in the producer, none in the block the oracle exists to test |

Two production defects had reached deployment; both were found by writing the oracle the anchoring analysis said was missing. On one, the telemetry showed complementary senses 100% of the time across 147 recorded activations — and would have shown exactly that in a world where every advisory was wrong, *because the only instrument pointed at it was itself state-anchored.*

**The claim that most directly answers your sub-question 4:**

> Anchoring is a provenance property that published oracle adequacy metrics cannot see. Every metric surveyed by Hossain and Dwyer, the model-checking coverage taxonomy, and current hardware assertion-quality metrics measure forward influence. **A self-referential oracle scores perfectly on all of them.**

And on tooling:

> The flow half of that predicate is decidable on the import-and-call graph, and **no shipping linter or test-smell detector we swept implements even that much**, which is a tractable tooling gap and not a research problem.

For this review, that statement is evidence about the paper's bounded graph model and tool sweep, not a theorem about arbitrary programs or all available tooling.

The paper also notes that the published test-smell rule — never compute an expected value in the test — applied literally to their repair would **revert it**, because their repair replaced a state-anchored read with a computation from published procedure.

**Validity ceiling.** All measurements come from one system, by one author, with the simulator not public. Every number can be recomputed from the deposited dataset (Zenodo DOI 10.5281/zenodo.21940547) but no measurement can be re-run. Treat as a well-instrumented single-subject study, not as a prevalence estimate.

### 3.4 The indirect but decisive measurement

**Zhang and Mesbah (2015), Finding 6.** Randoop-generated regression assertions record baseline
behaviour as fixed expectations. Fifty sample suites of 100 human-written assertions killed
mutants effectively; fifty suites of 100 generated assertions **could hardly detect any
mutant**. Raising generated assertion count to 500 did not change the pattern.

This is adjacent evidence about weak generated oracles, not evidence of state anchoring. During
mutation analysis those recorded expectations normally remain fixed, so the mutant does not
move the expectation with it. The experiment instead shows that the generated regression
assertions were poor discriminators for the studied mutant population.

### 3.5 Dynamic detection: OraclePolish

**Huo and Clause**, *Improving oracle quality by detecting brittle assertions and unused inputs in tests*, FSE 2014, pp. 621–631. Dynamic tainting. Detects *brittle assertions* — assertions depending on values derived from uncontrolled inputs — and *unused inputs* — test-provided inputs never reaching an assertion.

Across more than 4,000 real JUnit test cases: **164 tests with brittle assertions, 1,618 tests with unused inputs.**

The taint mechanism is relevant to the anchoring predicate; the polarity is not quite the same (brittleness is about uncontrolled *external* inputs, anchoring about the mutate target). Canedo reports no matching tool in the paper's sweep. That is not evidence that no implementation exists anywhere.

### 3.6 The agent-authored base rate

**Banik, Chowdhury and Shamim**, *All Smoke, No Alarm: Oracle Signals in Agent-Authored Test Code*, arXiv:2606.18168, June 2026. 86,156 cumulative test-file patches from 33,596 agent-authored PRs across 2,807 repositories with 100+ stars, from OpenAI Codex, GitHub Copilot, Devin, Cursor and Claude Code.

| Measure | Value |
|---|---|
| Patches with **weak or no** explicit oracle signals | **80.2%** |
| Strong-oracle rate on newly created files, by agent | 18% to 67% |
| Strong oracles vs. merge likelihood (adjusted) | OR = 1.28, p < 0.001 |

Their taxonomy has eight categories; weak categories W1–W5 confirm execution without verifying output correctness. Their conclusion: coding agents generate test *structure* far more reliably than they generate *oracle logic*.

If part of a suite was machine-authored under conditions comparable to that corpus, these rates are an external warning signal, not an h-EPI prior or a project-specific estimate.

---

## 4. One-sided screens (Sub-question 4)

Nothing in the reviewed literature markets itself as "this suite provably does NOT check X." The closest located families, with different scopes and soundness conditions, are:

### 4.1 Run-scoped: uncoverage

For a named test run, a mutant that was not executed necessarily survived that run. This does not prove general unreachability or a clause failure. Aghamohammadi's 62% figure measures this case in its corpus.

### 4.2 Sound in the mirror direction: Trivial Compiler Equivalence

**Papadakis, Jia, Harman and Le Traon**, ICSE 2015. Under the method's compiler and binary assumptions, identical compiled binaries certify the relevant mutant as equivalent and hence unkillable by tests that observe no distinction outside that compilation boundary. This is a sound one-sided certificate discussed in the reviewed mutation literature. (Effect sizes not retrieved for this review.)

### 4.3 Oracle gaps: covered-but-unchecked

**Schuler and Zeller** — checked coverage, ICST 2011 / STVR 2013. Dynamic backward slice from assertions; the fraction of statements contributing to checked expressions.

**Koster and Kao** (FSE 2007) and **Vanoverberghe et al.** (SOFSEM 2012) — state coverage, based on output-defining statements and on the ratio of state updates read by assertions.

**Hossain, Dwyer, Elbaum and Nguyen-Tuong**, *Measuring and Mitigating Gaps in Structural Testing*, ICSE 2023. Formalises the *oracle gap*. Mature test suites exhibit gaps of up to **51 percentage points** between executed and checked code; a large-scale study found a strong negative correlation between the gap and fault-detection effectiveness; the tool ships a lightweight **static** assertion recommender.

**Maton, Kapfhammer and McMinn**, GAPGREP — connects checked coverage and mutation testing to identify execution gaps.

### 4.4 Extreme mutation and pseudo-testedness

**Niedermayr, Juergens and Wagner (2016)**: introduced pseudo-tested methods. Across 19 open-source projects, present in all of them, median relative share **10%** (10.1%).

**Vera-Pérez, Danglot, Monperrus and Baudry**, *A comprehensive study of pseudo-tested methods*, EMSE 24(3):1195–1225, 2019. Replication across 28,000+ methods, plus manual analysis of 101 instances. The mutation score of *required* methods averaged **52 percentage points above** that of pseudo-tested methods; Wilcoxon p < 0.01; **effect size 1.5, large** by standard SE guidelines. On one subject (scifio) only 1% of PIT mutants inside pseudo-tested methods were killed, against 84% in required methods.

**Maton, Kapfhammer and McMinn**, ICSME 2024, statement-level extension (SDL operator). Across 4 Apache Commons projects plus 23 random Maven Central projects, 722 pseudo-tested statements; **48% lie outside pseudo-tested methods**, so method granularity misses half the signal.

### 4.5 The precision-against-ground-truth comparison

**Maton, Kapfhammer and McMinn**, *Where Tests Fall Short: Empirically Analyzing Oracle Gaps in Covered Code*, ESEM 2025. Thirty Java classes from six open-source projects. Three Oracle Gap Calculation Approaches compared.

| Approach | Median mutation score of flagged gap | Median execution time |
|---|---|---|
| Pseudo-Tested Statement Identification (PTSI) | **0.32** | **19.9 s** |
| Checked Coverage, dynamic slicer (CC-DS) | 0.76 | 273.2 s |
| Checked Coverage, observational slicer (CC-OS) | 0.50 | 5,957.1 s |

Lower mutation score in the flagged region is an indirect proxy that the selected code is weakly checked; it is not a direct precision label against independently adjudicated clause failures. PTSI selected the lowest-scoring regions and had the lowest reported cost in that comparison—roughly 14x and 300x faster than the two alternatives. Qualitative analysis found data-loading statements, iteration statements and output updates most prominent in the gaps. The same paper reports a framing example in which statement coverage corresponded to only about **10% fault detection**.

This is the nearest thing in the literature to the precision/recall-against-mutation-ground-truth numbers requested.

### 4.6 The definitional work

**Jahangirova, Clark, Harman and Tonella**, *Test oracle assessment and improvement*, ISSTA 2016, pp. 247–258; *An empirical validation of oracle improvement*, TSE 47(8):1708–1728, 2021. Tool: **OASIs**.

They define oracle deficiencies as **false positives** (a correct, expected program state for which the oracle fails) and **false negatives** (an incorrect, unexpected state for which the oracle holds). False positives are found by evolutionary search over test cases; **false negatives are computed as mutations the oracle does not detect.**

One operational definition used in the reviewed work is mutation-based. Canedo notes that Jahangirova's false-negative criterion matches the anchoring diagnostic signature: the mutant is strongly killed, the conditions in the assertions do not change value, and at least one variable visible at the assertion point differs.

**Vera-Pérez et al.** partition undetected mutants into no-infection, no-propagation, and weak-oracle symptoms and measure the split — the RIPR decomposition applied to survivors.

---

## 5. Decision procedure (Sub-question 5)

### 5.1 The decision table

| # | Signal | Honest conclusion | Soundness | Measured predictive power | Source |
|---|---|---|---|---|---|
| 0 | Clause names no observable | Operational check is underspecified | Sound as a specification diagnosis; not a clause refutation | — | — |
| 1 | Named governed code is absent from a validated execution trace | That run did not exercise the named path | Sound for the run and path; general reachability requires additional assumptions | 62% of all mutants in the cited corpus were uncovered and therefore survived that corpus's tests | Aghamohammadi & Mirian-Hosseinabadi 2020 |
| 2 | No value assertion references the observable | No direct value-comparison oracle was found | Not a complete revealability proof: exceptions, exits, validator rejection, and proof-checker failure may still reveal a fault | 28–73% of kills in the cited projects were explicit assertion kills | Zhang & Mesbah 2015 |
| 3 | State field coverage = 0 on governed field (non-empty type graph, stateful class) | The field is absent from the metric's oracle slice | Sound for that static model; a transport-limited negative signal, not a clause certificate | Pearson 0.54 / ~0.45 / >0.96 per-project; ~6 s per test | Molina et al., ASE 2025 |
| 4 | Expected value flows from the mutate target and sizes the comparison | Oracle is invariant to the declared covarying fault family | Relative to target, fault, comparison, domain, and correctness of the bounded flow model | 2 of 6 sizing instances carried 11 of 12 recovered mutants; re-anchor +8 of 46; anchor −4 of 19 | Canedo, arXiv:2608.17214 |
| 5 | `test_distance > 5` (no direct test) | External risk association for review ordering | Unsound as a project verdict | rho = −0.4921; RF importance 0.29, 4.8x next feature | Zhu, Zaidman & Panichella, JSS 2021 |
| 6 | `is_void = 1` with no getter on the mutated field | External risk association for review ordering | Unsound as a project verdict | rho = −0.1427; top feature (0.22) among directly-tested methods | Zhu et al. 2021 |
| 7 | `assertion_density <= 0.14` (or <= 0.22 at higher NOS) with direct test present | External risk association for review ordering | Unsound as a project verdict; collinear with #5 (\|rho\| > 0.87) | rho = 0.4096; anti-pattern rules validated at accuracy >= 0.8 | Zhu et al. 2021 |
| 8 | Assertion count / assertion coverage high | **Weak positive only** | Not a certificate | Count: Pearson r 0.927–0.976, Kendall τ 0.781–0.970; coverage: adjusted R² 0.80–0.99, Kendall τ 0.80–0.91 | Zhang & Mesbah 2015 |
| 9 | Assertion type (assertTrue > assertEquals > assertNull) | Nearly nothing | Not a certificate | 1–5 percentage points of mutation score | Zhang & Mesbah 2015 |
| 10 | OO / complexity metrics | Nothing | Not a certificate | all \|rho\| < 0.27; McCabe 0.0398 | Zhu et al. 2021 |
| 11 | Pseudo-tested statement (extreme mutation) — *cheap dynamic* | Suite did not distinguish a validated extreme mutant in that run | Clause-level force requires non-equivalence, determinism, and an independently justified mutant-to-clause mapping | flagged gaps at median mutation score 0.32; 19.9 s median | Maton et al., ESEM 2025 |
| 12 | Method body deletable without failure — *cheap dynamic* | Suite did not distinguish that validated deletion in that run | Same mapping and execution qualifications as #11 | required vs. pseudo-tested gap 52 pp, effect size 1.5 | Vera-Pérez et al., EMSE 2019 |
| 13 | Targeted mutation restricted to the clause's governing code | "Survived N mutants at budget B" | Not a certificate of holding | 29.6% of perfect-kill-score methods still have an untested documented behaviour | Paul & Holmes, arXiv:2606.10417 |

### 5.2 Running order

**Tier 0 — low-cost structural screening.** Signals 0, 1, 2, 3. For each clause: name the governed observable, check whether a validated trace reaches the governing code, and identify every verdict sink that may reveal a fault. Record only the observation licensed by the corresponding table row. A necessary-condition or clause-level conclusion requires a separate proof that the analysis is complete for that condition and that the condition maps to the clause.

*Soundness caveat.* Reflection, dependency injection, dynamic dispatch and code generation all break naive reachability. A missing path in an under-approximation is not a refutation. A reachability refutation requires a sound proof or over-approximation that excludes the path.

**Tier 1 — bounded oracle provenance.** Signal 4. For each verdict, ask where its expected side, tolerance, condition, and generator came from. Treat flow from the mutate target as a dependence risk and test whether a declared fault moves the compared quantities covariantly. Where there is no declared mutate target, a module or package boundary is only a provisional scope, not a proof boundary.

Check all four channels, not only the expected value. The conditioning variable carried 8 of the 9 mutants in the one case where the split was measured.

**Tier 2 — cheap heuristics for triage.** Signals 5, 6, 7. Base rates, not proofs. Use these to order manual review, not to conclude anything.

**Tier 3 — targeted execution.** Signals 11 and 12. Extreme mutation restricted to the governing methods can supply a strong negative witness when the mutant is independently validated, the run is deterministic or adequately repeated, and the mutant-to-clause mapping is sound. The cited Java timing and precision results are useful scheduling evidence, not established costs for h-EPI's Python, JSON, Lean, and semantic-model workflow.

**Tier 4 — targeted stress testing.** Signal 13. This does not by itself certify “held.” The honest form is “remained unrefuted by N independently mapped mutants targeting C at budget B under operator set O.” A finite exhaustive replay or proof may support a stronger bounded claim, but only within its declared premises and input universe.

### 5.3 What each tier can honestly conclude

| Tier | Statement licensed |
|---|---|
| 0 | “The analysis observed O under frozen assumptions A.” A stronger necessary-condition claim requires a completeness proof and clause mapping. |
| 1 | “This oracle is invariant to declared fault family F over domain D under provenance model P.” |
| 2 | “This clause has features associated with outcome R in external corpus K”; no project verdict follows. |
| 3 | “The suite did not distinguish validated case M in run E”; a clause conclusion additionally requires mapping J. |
| 4 | “Not refuted at this budget, under these operators and auxiliaries.” A separate exhaustive certificate or proof can license only its own bounded proposition. |

---

## 6. Application to the current h-EPI tranche

The repository currently contains three distinct testing surfaces that must not be collapsed.

The Python suite checks runtime contracts, canonicalization, provenance bindings, fail-closed
validation, and named adversarial regressions. For the current uncommitted working tree, all
527 tests passed in normal execution in 708.658 seconds and all 527 passed under `python -O` in
712.177 seconds. These are operational results for one tree and environment. They do not
establish translation fidelity, source meaning, or adequacy against every semantic defect.

The translation-test synthesizer generates nine attack families from an exactly re-derived snapshot delta. Every generated family remains a criticism-only obligation because its typed fixture, held-fixed contract, comparator, executable projection, and human-authored expectation are absent. The runtime therefore assigns neither a semantic expectation nor a verdict.

HRC-1 supplies a finite future qualification surface: 34 mutations, six benign controls, and 82 exact exposure expectations over 40 cases. The current qualifier can detect missing and extra declarations and can verify freeze-before-controller-load ordering. It cannot verify that a producer executed the mutations, that observations came from execution, or that the producer remained blind to controller data. Exact token agreement is consequently a declaration-conformance result, not mutation adequacy.

The local snapshot-delta deriver is a useful positive counterexample to blanket claims that finite positive certificates are impossible. For quiescent supplied inventory directories, it can certify the exact retained, added, removed, explicit-replacement, and changed-member projections of the two snapshots' selected identity surfaces, and the contextual validator rejects a content-rehashed caller mismatch. The contract deliberately excludes semantic preservation and transported membership from that certificate.

The negative and positive boundaries are claim-specific. A replayed counterexample can defeat a universal mechanical obligation only when its scope, execution, oracle, and mapping to that obligation are independently validated. Missing evidence remains `UNRESOLVED`; it is never converted into negative evidence. Conversely, a finite exhaustive replay or proof certificate may establish a bounded mechanical claim. Even then, the permitted conclusion is scoped—for example, exact selected-identity-surface delta, exact controller-token agreement, or `HARDENING_UNREFUTED` for one declared comparison—not semantic truth or fidelity to CR-1.0.

Accordingly, the repository should avoid the undifferentiated phrase “the suite holds clause C.” It should instead report one of four precise statements: the suite detected a named case; the validator enforces a named invariant over a declared input class; a proof establishes a proposition from named premises; or a candidate remains unrefuted by named tests under named auxiliaries and scope.

---

## 7. Threats and open gaps

**Single-subject dependence.** The anchoring result — the one that most directly states the asymmetry — is one system, one author, one non-public codebase. Its algebraic cancellation mechanism is checkable within the declared fault and comparison; its prevalence figures are not generalisable. It should be read as a naming and a bounded mechanism, not a base rate.

**Corpus monoculture.** Zhang & Mesbah (5 projects), Zhu et al. (6 projects), Molina et al. (Defects4J), Paul & Holmes (10 Defects4J projects), Maton et al. (6 projects) draw heavily on the same Apache Commons and Defects4J subjects. `jfreechart` and `commons-lang` appear in four of the five. Effect sizes may not transfer to a formal-methods codebase.

**Tool dependence.** PIT, Major and Stryker generate different operator sets. Cross-study comparison of mutation scores is unreliable. Denominator conventions also differ; Canedo notes that no retrieved study shares its identity key and few share its denominator.

**Equivalent mutants everywhere.** Zhang & Mesbah, Zhu et al. and most others treat all mutants as non-equivalent, or treat master-suite-unkilled mutants as equivalent. Both choices bias absolute scores; correlations are less affected.

**A candidate tooling gap.** The cited 2026 study reports that its sweep found no shipping linter or test-smell detector implementing the bounded flow half of its anchoring predicate. For a codebase with a declared module boundary and a spec-to-observable map, a conservative provenance analysis is a plausible project, but its cost and coverage have not been measured for h-EPI. It would complement, not replace, execution, independent oracles, contextual replay, and proof checking.

**Repository provenance gap.** The bibliography below has not been converted into the repository's required source-only reports and separately justified proposed uses. The active research ledger contains eight `UNREVIEWED` entries and no accepted engineering decision based on these newer sources. Primary versions, retrieval dates, inspected scopes, and bounded claims must be recorded before this review can become repository-admissible research evidence.

---

## 8. Bibliography

**Foundations**

- Budd, T.A., Angluin, D. (1982). Two notions of correctness and their relation to testing. *Acta Informatica* 18(1), 31–45.
- Budd, T.A., DeMillo, R.A., Lipton, R.J. Axiomatizing software test adequacy.
- DeMillo, R.A., Offutt, A.J. (1991). Constraint-based automatic test data generation. *IEEE TSE* 17(9).
- Voas, J.M. (1992). PIE: a dynamic failure-based technique. *IEEE TSE* 18(8), 717–727.
- Ammann, P., Offutt, J. (2008/2016). *Introduction to Software Testing*. Cambridge University Press.
- Li, N., Offutt, J. RIPR: Reachability, Infection, Propagation, Revealability.
- Formal Analysis of Reachability, Infection and Propagation Conditions in Mutation Testing. arXiv:2410.21904, 2024.

**Vacuity (the model-checking precedent)**

- Beer, I., Ben-David, S., Eisner, C., Rodeh, Y. (1997/2001). Efficient detection of vacuity in ACTL formulas / in temporal model checking. *FMSD* 18(2), 141–163.
- Kupferman, O., Vardi, M.Y. (2003). Vacuity detection in temporal model checking. *STTT* 4(2), 224–233.
- **Ball, T., Kupferman, O. (2008). Vacuity in Testing.** TAP 2008, LNCS 4966, 4–17.
- Kupferman, O., Li, W., Seshia, S. (2008). A theory of mutations with applications to vacuity, coverage, and fault tolerance. FMCAD 2008.
- Gurfinkel, A., Chechik, M. Robust vacuity for branching temporal logic. arXiv:1002.4616.
- Chockler, H., Strichman, O. (2009). Before and after vacuity. *FMSD* 34(1), 37–58.

**Assertions and oracle quality**

- Zhang, Y., Mesbah, A. (2015). Assertions are strongly correlated with test suite effectiveness. ESEC/FSE 2015, 214–224.
- Schuler, D., Zeller, A. (2011/2013). Assessing oracle quality with checked coverage. ICST 2011, 90–99; *STVR* 23(7), 531–551.
- Huo, C., Clause, J. (2014). Improving oracle quality by detecting brittle assertions and unused inputs in tests. FSE 2014, 621–631.
- Huo, C., Clause, J. (2016). Interpreting coverage information using direct and indirect coverage. ICST 2016, 234–243.
- Jahangirova, G., Clark, D., Harman, M., Tonella, P. (2016). Test oracle assessment and improvement. ISSTA 2016, 247–258.
- Jahangirova, G., Clark, D., Harman, M., Tonella, P. (2021). An empirical validation of oracle improvement. *IEEE TSE* 47(8), 1708–1728.
- Koster, K., Kao, D.C. (2007). State coverage: a structural test adequacy criterion for behavior checking. ESEC/FSE 2007, 541–544.
- Vanoverberghe, D., de Halleux, J., Tillmann, N., Piessens, F. (2012). State coverage: software validation metrics beyond code coverage. SOFSEM 2012, 542–553.
- Terragni, V., Jahangirova, G., Tonella, P., Pezzè, M. (2020). Evolutionary improvement of assertion oracles. ESEC/FSE 2020, 1178–1189.
- Barr, E.T., Harman, M., McMinn, P., Shahbaz, M., Yoo, S. (2015). The oracle problem in software testing: a survey. *IEEE TSE* 41(5), 507–525.
- **Molina, F., Aguirre, N., Gorla, A. (2025). State Field Coverage: A Metric for Oracle Quality.** ASE 2025. arXiv:2510.03071.
- **Canedo, A. (2026). Oracles That Cannot Fail: Anchoring and the Expectation That Moves With the Fault.** arXiv:2608.17214. Dataset: doi:10.5281/zenodo.21940547.

**Coverage, mutation and effectiveness**

- Inozemtseva, L., Holmes, R. (2014). Coverage is not strongly correlated with test suite effectiveness. ICSE 2014, 435–445.
- Just, R., Jalali, D., Inozemtseva, L., Ernst, M.D., Holmes, R., Fraser, G. (2014). Are mutants a valid substitute for real faults in software testing? FSE 2014, 654–665.
- Papadakis, M., Jia, Y., Harman, M., Le Traon, Y. (2015). Trivial Compiler Equivalence. ICSE 2015.
- Papadakis, M., Shin, D., Yoo, S., Bae, D.-H. (2018). Are mutation scores correlated with real fault detection? ICSE 2018.
- **Zhu, Q., Zaidman, A., Panichella, A. (2021). How to kill them all: an exploratory study on the impact of code observability on mutation testing.** *JSS* 173, 110864.
- Whalen, M., Gay, G., You, D., Heimdahl, M.P., Staats, M. (2013). Observable Modified Condition/Decision Coverage. ICSE 2013, 102–111.
- Visser, W. (2016). What makes killing a mutant hard. ASE 2016, 39–44.
- Just, R., Kurtz, B., Ammann, P. (2017). Inferring mutant utility from program context. ISSTA 2017, 284–294.

**Predictive mutation testing**

- Zhang, J., Zhang, L., Harman, M., Hao, D., Jia, Y., Zhang, L. (2019). Predictive mutation testing. *IEEE TSE* 45(9), 898–918.
- Mao, D., Chen, L., Zhang, L. (2019). An extensive study on cross-project predictive mutation testing. ICST 2019, 160–171.
- **Aghamohammadi, A., Mirian-Hosseinabadi, S.-H. (2021). An ensemble-based predictive mutation testing approach that considers impact of unreached mutants.** *STVR*. arXiv:2005.11532.
- Chekam, T.T., Papadakis, M., Bissyandé, T.F., Le Traon, Y., Sen, K. (2020). Selecting fault revealing mutants. *EMSE* 25(1), 434–487.

**Pseudo-testedness and oracle gaps**

- Niedermayr, R., Juergens, E., Wagner, S. (2016). Will my tests tell me if I break this code?
- **Vera-Pérez, O.L., Danglot, B., Monperrus, M., Baudry, B. (2019). A comprehensive study of pseudo-tested methods.** *EMSE* 24(3), 1195–1225.
- Vera-Pérez, O.L., Monperrus, M., Baudry, B. (2018). Descartes: a PITest engine to detect pseudo-tested methods. ASE 2018, 908–911.
- Hossain, S.B., Dwyer, M.B., Elbaum, S., Nguyen-Tuong, A. (2023). Measuring and mitigating gaps in structural testing. ICSE 2023, 1712–1723.
- Hossain, S.B., Dwyer, M.B. (2022). A brief survey on oracle-based test adequacy metrics. arXiv:2212.06118.
- Maton, M., Kapfhammer, G.M., McMinn, P. (2024). Exploring pseudo-testedness: empirically evaluating extreme mutation testing at the statement level. ICSME 2024.
- **Maton, M., Kapfhammer, G.M., McMinn, P. (2025). Where Tests Fall Short: Empirically Analyzing Oracle Gaps in Covered Code.** ESEM 2025.
- Betka, M., Wagner, S. (2021/2022). Extreme mutation testing in practice: an industrial case study. AST 2021. arXiv:2103.08480.

**Behavioural adequacy and generated tests**

- **Paul, P.P., Holmes, R. (2026). Beyond Coverage and Kill Scores: Empirically Measuring Test Suite Behavioural Gaps.** arXiv:2606.10417.
- **Banik, D., Chowdhury, K., Shamim, S.I. (2026). All Smoke, No Alarm: Oracle Signals in Agent-Authored Test Code.** arXiv:2606.18168.
- Shamshiri, S., Just, R., Rojas, J.M., Fraser, G., McMinn, P., Arcuri, A. (2015). Do automatically generated unit tests find real faults? ASE 2015.
- Palomba, F., Panichella, A., Zaidman, A., Oliveto, R., De Lucia, A. (2016). Automatic test case generation: what if test code quality matters? ISSTA 2016, 130–141.
- van Deursen, A., Moonen, L., van den Bergh, A., Kok, G. (2001). Refactoring test code. (Original test-smell catalogue.)
- Peruma, A. et al. Extended test-smell catalogue, incl. Redundant Assertion and Unknown Test.

---

*Prepared as a literature review, not as legal, safety-certification, or regulatory advice. Figures are reproduced from the cited papers; where a paper reports a range or a bound, the range or bound is carried through rather than collapsed to a point estimate.*
