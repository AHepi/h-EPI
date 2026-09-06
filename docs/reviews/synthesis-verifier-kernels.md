# Verifiers That Cannot See: Four Reports on Checks Whose Verdicts Have Come Loose From the Truth

**Compiled 4 September 2026.** Four literature reviews prepared between 1 and 4 September 2026 against live problems in a conjecture–criticism harness and its verification tooling, plus a synthesis written after the fact. The four reports are reproduced in Parts I–IV exactly as prepared, with heading levels normalised for the compilation and nothing else altered. Every number, citation, caveat and gap stated in them stands as written. The synthesis in Part 0 is new, editorial, and should be read as a conjecture about what the four have in common — not as a finding any of them establishes.

**Contents.** This file keeps the compilation's header and its Part 0. Parts I to IV are the four reviews kept beside it in this directory, in the later form that carries their 4 September status notes:

- Part I: `artifact-requirements.md`
- Part II: `unreliable-eliminators.md`
- Part III: `checks-that-cannot-fail.md`
- Part IV: `refuting-versus-certifying.md`

---

# Part 0 — Synthesis: one object, four pathologies

## 0.1 The common object

Each report was commissioned against a different symptom: a sham proposal that passed a requirement; a critic that objects to everything and a judge that convicts 12% of known defects; a probe whose formula encoded its own premise and a checker that skipped what it could not parse; a 701-test suite in which mutation testing found 3 of 26 specification clauses held. Read together, they are about one object.

A verifier *V* is meant to produce a verdict that depends on the truth *T* of the thing it judges. In every case examined, that dependence has failed in the same way: **the fault lies in the verifier's kernel.** There is a transformation of the artifact — the fault, the sham, the fabrication — under which the verifier's output is invariant.

The four reports exhibit this at four sites:

| Report | Verifier | Invariance | Where the report says it |
|---|---|---|---|
| I — Artifact gaming | Existence / format check on a filed artifact | Filed-or-not, parses-or-not, is independent of whether the work was done. Schema compliance 100% with tool invocation 0% (2606.25605); a fabricated summary scores 1/1 (2605.02269). | Design table bands A–C |
| II — Unreliable eliminator | Critic and judge over 339 candidates | P(object \| sound) ≈ P(object \| defective) ≈ 1: likelihood ratio ≈ 1, zero bits. Judge hidden-failure rate ρ(F→P) ≈ 0.88, past the cliff at which no item is ever eliminated at any sample size (2607.07436). | §0 |
| III — Self-confirming checks | Oracle whose expected value flows from the system under test | m′/e′ = m/e exactly under a scaling fault; the fault is a symmetry of the comparison (2608.17214). Silent skip: the item never enters the check at all (2608.01000, 2608.26183). | C2, C6 |
| IV — Certification asymmetry | Test suite as evidence that a clause holds | Every published oracle-adequacy metric measures forward influence; a self-referential oracle scores perfectly on all of them. 62% of mutants are uncovered and hence certainly survived (2005.11532). | §1.5, §1.6 |

Stated as one sentence: in each report, P(pass | fault) = P(pass | no fault) for some class of fault, and the report's work is to find which class and what it costs.

## 0.2 The two formal shapes underneath

Two well-known structures account for most of the mathematics in the four reports. Neither is named in any of them as the governing structure; both are present in the equations.

**Hypothesis testing / signal detection.** The eliminator's 0.12 conviction rate on known defects is statistical power. The channel model of 2607.07436 — hidden-failure rate ρ(F→P), phantom-failure rate ρ(P→F), κ = 1 − ρ(F→P) − ρ(P→F) — is a confusion matrix, and the cliff at ρ(F→P) = (1−τ)/2 is the point at which power falls to size and the operating point sits on the ROC diagonal. The paper's design rule, that sample size shrinks the estimator's radius but never shrinks ρ(F→P), is the bias–variance split: *n* buys variance and never bias. And the honest form of a positive result in Part IV — "survived *N* mutants targeting *C* at budget *B* under operator set *O*" — is "failed to reject at this *n*", which is why a null can be failed-to-reject forever and never accepted.

The information-theoretic reading is the same picture from the other side. A binary channel with crossover at or past ½ has zero capacity; Part II notes that its own case violates the channel model's assumption ρ(F→P) + ρ(P→F) < 1, so κ ≤ 0. And Part II's sentence — *no aggregation rule downstream, voting, weighting, argumentation semantics, label models, can extract information that is not in the signal* — is the data-processing inequality stated in words.

**The Σ₁ / Π₁ asymmetry.** Part IV's executive verdict is that the asymmetry between refuting and certifying is a *certificate* asymmetry, not a decidability asymmetry. Detection decomposes into necessary conditions (reachability, infection, propagation, revealability); violating any one yields a finite witness that the suite does not hold the clause. Holding quantifies over all faulty implementations and has no finite witness (Budd & Angluin 1982). One killed mutant is a Σ₁ certificate of non-invariance. Invariance under every fault is Π₁. This is the same shape that model checking discovered earlier under the name *vacuity* (Beer et al. 1997–2001; Ball & Kupferman 2008): a valid formula needs an interesting witness that its validity was non-trivial, and that witness is obtained by mutation, not by inspecting the proof.

The two shapes compose. The Σ₁/Π₁ structure says *what kind of evidence is available*; the signal-detection structure says *how much of it a given instrument can carry*. Part III's Tier 4 and Part II's step 11 both arrive at the same conclusion by different routes: the reliable quantity is coverage (the answer is in the pool; the clause is provably not held), and the unreliable quantity is selection (this one is right; this one is held).

## 0.3 A third structure: correlated identities

One result in Part II does not fit either shape above and is worth isolating. Li & Hai (2607.23931) measure same-model temperature resampling at a median latent correlation of 1.00, and prove that as ρ → 1 every fixed *k*-of-*n* rule converges to single-agent behaviour. Under correlation the infinite-committee error floor is Φ(−Φ⁻¹(p)/√ρ) > 0 — the Vasicek one-factor copula, the same expression Basel II uses for portfolio default risk. The 339 candidates are a diversified portfolio built from one underlying. This is the piece that the Byzantine reading below handles best.

## 0.4 The Byzantine Generals reading: what holds, what breaks, and where the inversion actually is

The conjecture that prompted this compilation is that the four reports have the formal structure of the Byzantine Generals Problem (Lamport, Shostak & Pease 1982) and its Nakamoto-consensus descendant, inverted. The mapping holds in pieces and fails as a whole, and the inversion is real but sits in a specific place.

**What holds.**

1. *Sybil.* Part II's 339 correlated candidates are a Sybil attack: many identities, one adversary. The collapse theorem is the formal statement of why identity-counting is worthless without cost, which is Nakamoto's founding premise. Cross-family generation (Part II, step 7) is the harness's only Sybil-resistance measure, and it is weak — cross-family ρ̂ ≈ 0.58–0.60, not zero.

2. *Signed messages.* Lamport's result that unforgeable signatures remove the *n* > 3*f* bound entirely is the theorem behind Part I's rule that the receipt must be emitted by the executor and never by the agent. Evidence-Carrying Termination's 252/288 → 0/288 (2608.23623) is the informal echo: the certificate binds every claim to receipts the agent could not author.

3. *Full-node validation.* Band H of Part I's design table — typed certificate plus deterministic replay — is the full-node rule: every node re-executes, nobody trusts the miner's word. Bands A–C are simplified payment verification.

4. *Confirmation depth.* "Survived *N* mutants at budget *B*" and "*k* confirmations deep" are the same kind of statement: cumulative cost to overturn, never finality. Nakamoto finality is probabilistic for the same Π₁ reason that "held" cannot be certified.

**What breaks.**

1. *Agreement is not soundness.* Byzantine fault tolerance solves consistency among honest nodes; it has no oracle and no validity condition stronger than "if all honest nodes propose *v*, decide *v*". A BFT protocol can converge on a wrong value with full honesty, and Bitcoin agrees on ordering, not truth. Every one of the four reports has an external truth, and the failure is a verifier that cannot see it.

2. *There is no honest set.* The BFT adversary model assumes a bounded set of *f* faulty nodes and an honest remainder that is simply correct. Part II has no honest remainder — every candidate is noisy and correlated, every verifier is substantially blind. That situation is outside the BFT model rather than an inversion of it. The threshold results look alike (3*f*+1; 51%; ρ(F→P) = (1−τ)/2) because all three are phase transitions, but the BFT thresholds count nodes and the eliminator threshold measures the error rate of a single instrument.

**Where the inversion is.** Nakamoto consensus works because of a cost asymmetry: production is expensive and verification is trivial. The harness the four reports describe is the mirror image. Production is nearly free — a schema-compliant artifact costs nothing, a temperature resample costs nothing, an LLM-authored test suite costs nothing — and verification is the expensive, unreliable side. All four reports are what running a consensus-shaped procedure on the wrong side of that asymmetry looks like. And the interventions that measurably work across all four — held-out expected values authored before the proposal, re-execution, executor-signed receipts, defect-injection audits of the verifier, extreme mutation — are all attempts to manufacture the asymmetry back: to make the artifact expensive to fake and cheap to check.

## 0.5 What the four reports jointly license

Pulling the decision rules together, in the order the reports themselves establish as dependency order:

1. **Audit the instrument before the finding.** Part II step 1 and Part III §9 and Tier 1 say the same thing: measure ρ(F→P) and ρ(P→F) separately, by defect injection, before any downstream mechanism is given an operating point. Part III adds the liveness control — proven able to fire, in this run, on this host.

2. **Enforce the accounting invariant.** `items_in == items_checked + items_refused` (Part III, Tier 0). This converts silent omission (C6) into a named refusal (C5), which is the only move that makes the class reachable by mutation.

3. **Run the free, sound refutations first.** Part IV Tier 0: governed observable named; governing code reached; some assertion transitively references it. Any clause failing any of these is provably not held, and the 23-of-26 labelled negatives measure this screen's recall in an afternoon.

4. **Check provenance, all four channels.** Part III C2 and Part IV Tier 1: expected value, tolerance band, conditioning variable, generator. The flow half is decidable on the import-and-call graph; the sizing half requires reading each oracle. No shipping tool implements even the flow half.

5. **Never accept a model-authored receipt; never let the visible score select.** Part I design table bands C and A, and the second anti-pattern. Provide a typed, scored no-proposal exit (the CEF and fallback evidence).

6. **Raise τ, not *n*.** Part II step 4: an objection is binding only if it names a defective inference step and a consequence; unnamed objections are abstentions. This is the only lever the channel model allows.

7. **Record positives as survival statements, never as status promotions.** Part IV §6.4; Part III reporting rules. Operator set, budget, and mutate scope attached.

None of this is new relative to the four reports. What the synthesis adds is the observation that the seven rules are seven ways of restoring the same dependency — verdict on truth — at seven different sites where it had silently gone.

## 0.6 What the synthesis does not establish

The invariance framing is a description, not a theorem. The claim that P(pass | fault) = P(pass | no fault) is exact for C2 anchoring (an algebraic identity) and for an existence check (by construction). For the eliminator it is an estimate with a stated 12% residual; for the certification asymmetry it is a statement about published metrics, not about all possible ones. The Byzantine mapping is offered as a source of design intuition from a field that solved the cost-asymmetry problem deliberately; nothing in Parts I–IV depends on it. The evidential caveats in each report — single-subject studies, unreplicated results, non-transferring rates, and the specific list in Part I §7, Part II §8, Part III's per-class evidence grades and Part IV §7 — apply to the synthesis with full force.
