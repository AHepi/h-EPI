# Failure modes of candidate selection under correlated generation and unreliable criticism

**Status update, 4 September 2026.** This is a non-authoritative engineering review. Its
numerical scenario is a conditional external threat model, not an observation from the h-EPI
repository. The current repository contains no 339-candidate corpus and no measured critic or
judge operating point. It contains ten unresolved research issues, ten seed challenges, one
unresolved mechanical calibration, an unexecuted HRC-1 programme with 34 mutations and six
benign controls, and a local exact two-inventory delta implementation. The literature below may
motivate criticisms of that machinery; it cannot supply CR-1.0 semantics, a correct
interpretation, or an automatic elimination rule.

**Original scenario.** Literature review against a stated situation with 339 accepted,
purportedly contradictory analyses; the correct one assumed present; no execution oracle; a
critic objection rate near 1.0 on sound and defective content alike; and a judge convicting
about 12% of known-defective items. Those assumptions remain external to h-EPI and are not
reproduced by its current artifacts.

**Method.** alphaXiv discovery + full-text reads. Papers read in full are marked **[read]**;
papers surfaced but not verified beyond abstract are marked *[abstract only]* and no numbers
are quoted from them.

---

## 0. The conditional channel result

Two of the measured properties are not equally bad, and conflating them will send the repair
effort to the wrong place.

**A saturated objection flag supplies no ranking signal. Low defect recall limits pruning
power; false conviction of sound candidates determines whether pruning is safe.**

Zhang et al. model a grader as a binary channel. Let

\[
a=P(\widehat P\mid F),\qquad b=P(\widehat F\mid P),\qquad
\kappa=1-a-b,
\]

and let \(p=P(P)\). The observed pass probability is
\(q=a+\kappa p\). If elimination occurs when \(q\le\pi_\tau\), then, for
\(\kappa>0\), elimination requires

\[
p\le\frac{\pi_\tau-a}{\kappa}.
\]

No item is eliminable when \(a>\pi_\tau\); at equality, only \(p=0\) can meet a
non-strict rule. If \(\kappa=0\), the report is independent of quality; if \(\kappa<0\), the
ordering reverses. For symmetric error \(a=b=r\), attenuation about one half preserves ordering
only for \(r<1/2\), and a fixed threshold below one half is unreachable throughout
\(\pi_\tau<r<1/2\). This is a threshold-specific result, not a theorem that repeated independent
witness searches can never help. (arXiv:2607.07436)

Their empirical sweep confirms it: genuine contribution-based retirement collapses to
0 / 0.3 / 0 at ρ(F→P) = 0.20 / 0.45 / 0.70 against a clean baseline of 1.3, and in the
headroom-bearing subset from ≈7 per run to 0 by ρ(F→P) = 0.45. Replicated across three
subsets and two domains, including a code-generation control with a real unit-test verifier.

The decisive contrast is their real LLM judge. It had the *highest* realised corruption in the
sweep — 0.59, **all of it phantom failures** — and elimination stayed fully alive (10.3
retirements, above the clean baseline of 1.3), because its hidden-failure rate was ≈ 0.01.
A judge that cries wolf constantly is noisy and starvation-prone but did not disable the cited
retirement rule. A judge that waves failures through can disable that rule.

Conditionally mapping the original 12% end-to-end sensitivity into this one-channel model gives
\(a\approx0.88\). If \(\kappa\ge0\), then because
\(\pi_\tau=(1-\tau)/2\le0.5\) for \(\tau\in[0,1]\), no value of \(\tau\)
rescues that channel; raising \(\tau\) lowers \(\pi_\tau\) and makes elimination harder. If
\(\kappa<0\), the channel reverses quality ordering and the decision rule must be inverted or
replaced rather than tuned as if it were informative in the original direction. But the
original critic and judge are separate
stages, so their marginal rates cannot simply be added or substituted into one channel. If
elimination requires critic objection \(C\) and judge conviction \(J\), measure the end-to-end
event \(Z=C\land J\):

\[
\alpha=P(Z=1\mid\text{sound}),\qquad
\beta=P(Z=0\mid\text{defective}),
\]

as well as the stagewise rates. A 12% detection rate by itself establishes poor yield, not
unsafe pruning; safety depends on false conviction of sound candidates.

Two corollaries worth stating plainly:

1. **Harm was non-monotone across the three tested blindness levels.** The largest measured
   damage occurred at ρ(F→P) = 0.45 (−0.065 eval) and receded at 0.70 (+0.039), because in that
   experiment the failure pool starved generation too and the library went inert. This is an
   observed three-point pattern, not a general inverted-U law or a located global worst point.
2. **Raw deprecation counts did not identify the mechanism's condition.** They stayed near 10
   under bias because cap-eviction churn filled in, even while outcome metrics varied across the
   three blindness levels. Only separating *genuine elimination* from *churn* exposed whether
   the retirement mechanism was live. A ledger that counts rejections without distinguishing
   convicted-on-evidence from evicted-for-other-reasons can report activity while that mechanism
   is dead.

Separately, the near-1.0 objection rate has its own consequence. If
\(P(C=1\mid\text{sound})\approx P(C=1\mid\text{defective})\), the binary occurrence flag has
a likelihood ratio near one and supplies approximately no ranking information. This does not
show that objection text, named inference steps, severity, or joint critic patterns are equally
uninformative. Those richer signals must be measured rather than inferred from the saturated
flag. **This is a measurement problem before it is a selection problem.**

---

## 1. Truth discovery / knowledge fusion (sub-question 1)

**[read]** Kucuk, Paton, Chen, Wu, *Single and Multi Truth Data Fusion using LLMs*,
arXiv:2606.28062. Head-to-head F1 on three standard benchmarks:

| Method | Book | Movie | Flight |
|---|---|---|---|
| Majority Vote | 0.577 | 0.583 | 0.787 |
| Source Reliability Vote (iterative weighting) | 0.250 | 0.394 | 0.821 |
| DART (domain-aware Bayesian) | 0.600 | 0.777 | 0.806 |
| LTM (latent truth model) | 0.696 | 0.796 | 0.821 |
| LLM prompt (best config) | 0.782 | 0.817 | 0.912 |

Source counts: 894 (Book), 15 (Movie), 38 (Flight), across hundreds-to-thousands of *objects*.

**The binding assumption is not error independence — it is cross-object redundancy.** These
iterative-weighting methods estimate a source's reliability from its agreement pattern *across
many objects*, then use that estimate to weight its claim on the object at hand. With one
object, reliability is not identifiable from the corpus alone. An implementation may collapse
to equal-weight voting, emit a prior-driven posterior, or remain underdetermined; none is an
empirically learned reliability estimate for this corpus. Note also that SRV is the *worst*
method on two of three cited datasets — iterative weighting can concentrate on a confidently
wrong source and drive recall to 0.146.

The obfuscated-ID ablation is worth noting: scrambling flight identifiers so background
knowledge could not be used dropped best F1 only 0.9119 → 0.9048, and the LLM still beat every
baseline in 15 of 16 cells. The advantage persisted under this ablation; whether it came from
consistency patterns or another remaining cue is unresolved by the experiment.

**Applicability to 339 analyses of one object:** source reliabilities are not identifiable from
that corpus alone. An implementation can still emit a prior-driven posterior, but the result
comes from external anchors or assumptions rather than cross-object evidence in the corpus.

---

## 2. Minority-correct recovery and where voting fails (sub-question 2)

### 2a. Majority voting on hard problems

**[read]** Bahuguna, *When Self-Consistency Backfires*, arXiv:2608.11403. Pre-registered,
confirmatory split, full GPQA Diamond (198 problems), N = 64 samples.

- Majority voting **reduced** per-problem accuracy on 56.6% of problems (Qwen2.5-7B) and 65.7%
  (Llama-3-8B). Aggregate accuracy barely moved (0.342 → 0.369) while a majority of problems
  degraded underneath it.
- Grid oracle (best N per problem) sits 14 pts (Qwen) / 17 pts (Llama) above N = 1. Real
  headroom.
- **None of the 22 evaluated verifier-free operating points reached it.** Plurality-agreement gate captured 0.8% (Qwen) and
  −1.6% (Llama) of headroom measured against MV(64). Token-entropy gate: 0.5% / 0.9%. Neither
  moved accuracy more than 0.002. All 22 operating points swept; none won.
- Mechanism: confidence does not track correctness. In the highest-agreement bin the plurality
  answer was correct 52.5% (Qwen) and 28.6% (Llama) — for Llama, *lower* than its
  lowest-agreement bin, i.e. non-monotone.

### 2b. Correlated error and the jury theorem

**[read]** Li & Hai, *State-dependent error correlations shape voting thresholds*,
arXiv:2607.23931. 174,384 votes, 28 models, 4 binary screening benchmarks (fact verification,
math solution verification, code review, truthfulness).

- **Same-model temperature resampling: median latent correlation ρ̂ = 1.00, mean 0.84. The
  majority-of-three gain was 0.001.** Resampling one model produces near-clones.
- Cross-family pairs: ρ̂_G ≈ 0.58, ρ̂_B ≈ 0.60. Substantial dependence even across families.
- **Vasicek floor.** Under independence Condorcet drives committee error to zero exponentially.
  Under correlation ρ, infinite-majority error converges to Φ(−Φ⁻¹(p)/√ρ) > 0. For an agent of
  accuracy 0.8 at the measured 5th–95th percentile cross-family correlations, **21–90% of
  single-agent error survives unlimited aggregation.**
- **Collapse theorem.** As ρ → 1, every fixed k-of-n rule converges to single-agent behaviour,
  A(p,ρ) → p, for all n and all k. The same limit applies to bounded-size vote-only rules that
  return the common vote on unanimous inputs; arbitrary rules with different tie-breaking or
  unanimity behavior require their own statement.
- Correlation erodes the protection of *both* extreme rules: unanimity's false-acceptance rate
  rises strictly above p^n, and polyarchy's rescue rate falls.
- With ρ_B > ρ_G the vote-count likelihood ratio can become **non-monotone**: unanimous approval
  carries *lower* evidential weight than 8-of-9. Overwhelming agreement becomes suspicious.
- Positive result: cost-sensitive threshold selection under independence cut scaled loss
  60.25 → 52.50; modelling measured dependence cut it further to 50.77 (incremental 1.73,
  95% bootstrap CI 0.68–2.33; total reduction from majority 15.73%, CI 13.41–16.75%).
  Held-out identity-line R² rose from 0.840 (independence) to 0.967 (full dependence matrix).

**Conditional implication.** Shared generation provenance creates a dependence risk; it does
not establish \(\rho\approx1\) for a new corpus. If a held-out audit measures dependence near
that endpoint, the collapse theorem explains why additional same-source votes add almost no
information. Until then, the cited result is a reason to measure dependence, not an estimate of
the 339 candidates' effective sample size.

### 2c. What does recover minority-correct answers

**[read]** Cai, Kulik, Choudhury, *ARBITER*, arXiv:2605.26172. Zero-external-information
post-consensus recovery on 3 models × 3 math benchmarks.

- Confirms wrong-majority failure is common and headroom is real: Qwen3-4B GSM8K consensus
  94.54%, same-pool top-2 oracle 97.27%.
- **The negative ladder is the important part.** Broad self-review, top-up vote merging,
  raw-trace review, answer-memo review, basin-principle judging, a trained trajectory encoder,
  a cluster-GNN router, and framing-first replacement **all degraded** the consensus baseline —
  some catastrophically (raw-trace review 70.87% vs 76.96%; answer-memo review 63–66.5% vs
  74.71%; basin judging −5 to −22 net). Their conclusion: *structure is not truth.* Coherence,
  stability, hidden-state geometry and graph reconstruction detect commitment, not correctness.
- The only clean positive: keep consensus as the prior and override **only** on additive
  same-model evidence. Across the 3×3 matrix, 168 overrides → 78 recoveries, 35 degradations,
  net +43 examples; gains 0.0 to +3.0 pp; best cell (Llama-3.1-8B, MMLU-HS-Math, 78.52 → 80.00)
  recovered ≈22% of oracle headroom.

**[read]** Marina et al., *Boosting Self-Consistency with Ranking (RISC)*, arXiv:2606.05054.
Reframes selection as learning-to-rank over five features (frequency, semantic centrality,
reasoning-trace consistency) with a LambdaRank model. +4.28% to +6.51% relative accuracy over
self-consistency at matched budget on PopQA; matched SC accuracy at 82% fewer LLM calls. Their
own limitation: a substantial gap to oracle remains.

**What RISC needs that a one-shot corpus lacks:** labelled training questions where *both*
correct and incorrect candidates exist, split at question level. It is supervised.

---

## 3. Argumentation frameworks (sub-question 3)

**Answer: empirical application exists and is growing, but the measured results are weak, and
the specific thing you would want — Dung admissibility/grounded/preferred extensions computed
over automatically extracted natural-language attack graphs, scored against ground truth — I
did not find measured.**

**[read]** Sanayei, Vesic, Blanco, Surdeanu, *Can LLMs Judge Debates?*, arXiv:2509.15739.
The one systematic measurement I verified. 325 arguments, 303 relations, NoDE benchmark
(12AngryMen + DebatePedia), gold rankings from QuAD gradual semantics, ~50,000 pairwise checks
per model.

- **Ranking alignment with QuAD is moderate at best.** Best result: Spearman ρ = 0.56,
  Kendall τ = 0.49 (Llama 3.1 405B, few-shot CoT, DebatePedia). Best on 12AngryMen: ρ = 0.44.
  Zero-shot vanilla on the 8B model was ρ = −0.04 on 12AngryMen and 0.03 on DebatePedia.
  GPT-4o / Claude 3 / Command R+ / Llama 3 70B under identical instructions were in the same
  moderate band.
- **Recovering the graph is the bottleneck.** Signed directed edge recovery (both endpoints and
  relation type must match): F1 0.33–0.36 zero-shot CoT, rising to 0.56–0.71 with CoT exemplars.
  Shorter debates score higher; longer ones degrade.
- **Models are reading discourse order, not structure.** Randomising argument order via
  topological sorts — preserving the graph exactly — reduced performance across the board.
- DeepSeek R1, a dedicated reasoner at 685B, was on par on one dataset and *underperformed all
  general-purpose models* on the other. In these reported comparisons, step-by-step
  specialisation did not confer robustness to non-linear structure.

*[abstract only]* Also in this space: ArgBench (arXiv:2604.17366), ArgLLM-App
(arXiv:2602.24172), argumentation for contestable decision support (arXiv:2603.14643),
neurosymbolic inference-time argumentation for claim verification (arXiv:2605.20098),
LLM argument mining + description logics (arXiv:2603.02858), multi-agent debate with confidence
gating for argument relations (arXiv:2606.16047). I did not verify their numbers.

**The load-bearing consequence for the original scenario.** Dung semantics are a function of
the attack relation. If the relation is recovered at F1 near 0.6, the computed extension is
exposed to upstream graph error before any semantics run, although a particular graph error
need not change the extension. A high item-level objection rate does not, however, imply a
complete pairwise attack graph. For an irreflexive complete bidirected graph the grounded
extension is empty and preferred or stable extensions are the singleton sets; dense,
asymmetric, or uncertain graphs need separate analysis. **Argumentation semantics cannot
independently validate or repair an unvalidated attack relation.**

---

## 4. Weak supervision label models (sub-question 4)

**[read]** Ratner, Hancock, Dunnmon, Sala, Pandey, Ré, *Training Complex Models with Multi-Task
Weak Supervision (MeTaL)*, arXiv:1810.02840.

| Supervision | NER | RE | Doc | Average |
|---|---|---|---|---|
| Gold (small dev set) | 63.7 | 28.4 | 62.7 | 51.6 |
| Hierarchical majority vote | 76.9 | 43.9 | 74.2 | 65.0 |
| Data programming | 78.4 | 49.0 | 75.8 | 67.7 |
| MeTaL | 82.2 | 56.7 | 76.6 | **71.8** |

+6.8 points over majority vote; +4.1 over the non-multi-task label model. Unipolar-source
modelling contributed 2.8 of those points.

**What it needs.** (a) *n* unlabelled data points — 2,630 to 62,547 in these experiments — with
estimation error scaling n^(−1/2); their Figure 5 shows accuracy 63.7 → 77.2 → 80.6 → 82.2 as
n goes 0 → 5k → 25k → 63k. (b) 9–19 labelling functions per task, each applying across many
items. (c) The dependency structure G_source, supplied by the user, plus a testable
identifiability condition — many correlation structures give **non-identifiable** accuracy
estimates with no unique solution. (d) A symmetry-breaking assumption: sources on average
better than chance, or at least one source conditionally independent of the rest.

**The gap is structural, not a matter of tuning.** The label model recovers source accuracies
from agreement/disagreement *rates across items*. A single contradictory corpus is n = 1. There
are no rates. Every measured accuracy above comes from exactly the redundancy the situation
lacks.

*[abstract only]* Related: confidence intervals for label probabilities in programmatic weak
supervision (arXiv:2508.03896), partial-identification evaluation of weak supervision without
ground truth (arXiv:2312.04601), learning dependency structures for weak supervision
(arXiv:1903.05844).

---

## 5. Unreliable eliminators (sub-question 5) — the critical one

### 5a. The channel result

Covered in §0. arXiv:2607.07436. For the paper's threshold rule and
\(\kappa>0\), no elimination is possible when
\(\rho(F\to P)>\pi_\tau=(1-\tau)/2\). Lowering \(\tau\) raises this particular threshold;
raising it moves in the wrong direction. When the hidden-failure rate is about 0.88, no
\(\tau\in[0,1]\) suffices, so the channel or the decision rule must change. This does not rule
out gains from repeated independently informative witness searches.

### 5b. Detection quality and elimination are empirically separable

**[read]** Yang et al., *Precise but Uncoupled*, arXiv:2607.15388. 4,181 Omni-MATH problems,
matched gpt-oss-120b actors, two collaborative protocols.

| | Planner–Executor–Reviewer | Broadcast deliberation |
|---|---|---|
| Reviewer precision | **0.861** | 0.644 |
| Reviewer recall | 0.754 | **0.872** |
| Uptake of verified-useful critique | 0.336 | **0.935** |
| Reviewer-guided repair rate | 0.051 | **0.286** |
| Resistance to misleading review | **0.921** | 0.708 |
| Neglect (wrong candidate, no revision attempted) | 48.8% | 26.2% |
| Final pass rate | 85.2% | 89.2% |

**The higher-precision reviewer produced 5.6× less repair.** Precision stayed high (0.81–0.87)
across the hard tiers while uptake stayed at 0.32–0.37. A cross-family replication with Gemma 3
actors reversed the overall protocol ranking but preserved the separation: reviewer precision
0.881, uptake 0.092, repair 0.009.

The structural difference: in PER the critique enters a *separable advice field* and the solver
can acknowledge it while preserving its candidate; in broadcast the critique enters the shared
candidate state and submission requires collective re-approval, so bypass is hard by
construction. Their within-protocol probes point the same way — forcing explicit acknowledgment
made things *worse*, while putting reviewer guidance directly in the solver's working context
partially recovered the gap.

### 5c. Measuring the eliminator: the defect-injection audit

The one method with a measured procedure attached. arXiv:2607.07436, §5 and Fig. 5. Construct
clean items, inject one known defect per defect class, ask each grader whether it noticed. Their
five "QC-visible" classes (orphan citation, unregistered tag, broken cross-reference, unsourced
number, deleted summary) and two "QC-invisible" semantic classes (claim negation — flip
"growth" to "decline"; number swap — perturb a digit while keeping the citation marker). The
deterministic grader caught every QC-visible injection (recall 1.0, n = 155 per class) and
essentially none of the QC-invisible ones. This is how they estimated the real LLM judge's
hidden-failure rate near 0.01 and explained why retirement remained live. That rate alone does
not establish safe elimination; false conviction of sound items must also be measured.

Requirement they flag: the audit ports only to domains where an independently warranted oracle
or declared contract establishes that the mutation changes the target property. Citation and
numeric discipline can make such mutations cheap; diffuse failures do not.

*[abstract only]* On calibrating rather than merely measuring: uncertainty-guarded judging with
provable risk guarantees via abstention (arXiv:2608.17994), distance-aware calibration of LLM
judges (arXiv:2608.14950), judge epistemic stability under perturbation (arXiv:2608.12645),
construct validity for LLM-as-judge (arXiv:2608.24419), reward hacking of reference-free judges
in self-play (arXiv:2607.05904), audit-repair context shifting verifier thresholds toward
leniency (arXiv:2608.16003). I did not verify their numbers, but 2608.16003 is worth reading
directly: it measures whether wiring a checker next to a fixer changes what the checker reports,
an analogous topology worth testing if h-EPI later adds a semantic executor or fixer.

---

## 6. Decision table

Columns: mechanism → assumptions → measured performance → behaviour under an unreliable
eliminator → citation.

| Mechanism | Assumptions it needs | Measured performance | Under the original conditional miss/objection scenario; candidate dependence remains unmeasured | Citation |
|---|---|---|---|---|
| **Majority vote / self-consistency** | Errors approximately independent; correct answer is modal | Hurts 56.6%/65.7% of hard problems; agreement bins non-monotone in correctness | No project estimate is available; stronger same-generator dependence reduces the effective-sample-size benefit and approaches single-agent behavior as ρ→1 | 2608.11403; 2607.23931 |
| **Confidence / entropy gating** | Model confidence tracks correctness | Captures 0.5–0.8% of oracle headroom; accuracy moves <0.002 | No warranted benefit without a project measurement that confidence discriminates sound from defective candidates | 2608.11403 |
| **Iterative source-reliability weighting (SRV)** | Many objects × overlapping sources, or external reliability anchors | F1 0.250 / 0.394 / 0.821 — *worse than plain voting* on 2 of 3 | Reliability is not identifiable from one object alone; a result would be prior-driven and can lock onto a confidently wrong source | 2606.28062 |
| **Probabilistic truth discovery (LTM, DART)** | Same, plus a generative model of source reliability | F1 0.696 / 0.796 / 0.821 | Not corpus-identifiable at n=1 without external anchors or priors | 2606.28062 |
| **Weak-supervision label model (MeTaL / data programming)** | Multiple overlapping items; evaluated here on 2,630–62,547 items with 9–19 sources; known dependency graph; identifiability; non-adversarial sources | 71.8 avg vs 65.0 MV vs 51.6 gold-dev; error ∝ n^(−1/2) | Not corpus-identifiable at n=1; near-identical sources can make the model degenerate | 1810.02840 |
| **Dung / gradual argumentation semantics over NL claims** | Attack relation recoverable and independently validated | Rank correlation with QuAD ρ ≤ 0.56; edge recovery F1 0.33–0.71; degrades when order is scrambled | A saturated item-level objection flag does not determine the pairwise graph; an unvalidated graph yields an unvalidated extension | 2509.15739 |
| **Broad self-review / cluster judging / rerank-by-structure** | Coherence or geometry correlates with correctness | *Negative in the cited cells.* −1.6 to −22 net; raw-trace review 70.9% vs 76.96% baseline | Harmful in that experiment; structural coherence is not a correctness certificate | 2605.26172 |
| **Consensus-as-prior + sparse additive override (ARBITER-Δ)** | A meaningful consensus exists; evidence sources partly decorrelated | +0.0 to +3.0 pp; 168 overrides → 78 rec. / 35 deg., net +43; ≈22% of headroom in best cell | Net positive in the reported cells, not non-negative by construction; same-model evidence can double-count | 2605.26172 |
| **Learned reranker over candidate features (RISC)** | Labelled questions with both correct and incorrect candidates present | +4.3% to +6.5% relative over SC; 82% cost reduction at matched accuracy | Unavailable now; scoped human dispositions are workflow decisions, not correctness labels | 2606.05054 |
| **Cost-sensitive k-of-n threshold with measured state-conditional correlation** | ρ_G, ρ_B and per-agent p_G, p_B measured on held-out items | 15.73% loss reduction vs majority (CI 13.41–16.75); dependence modelling adds 1.73 over independence-thresholding | A candidate statistical rule after calibration, not a semantic retirement authority; ρ_B > ρ_G can make unanimity non-monotone evidence | 2607.23931 |
| **Failure-driven elimination (retire on observed defect)** | Grader's hidden-failure rate below (1−τ)/2 and an acceptably low false-elimination rate | Retirement 0 / 0.3 / 0 at ρ(F→P)=0.20 / 0.45 / 0.70 in the aggregate sweep; the headroom-bearing subset reached 0 by 0.45; a real judge at ≈0.01 kept retirement active despite 0.59 realised divergence | Under the conditional 0.88 end-to-end miss estimate and κ≥0, no τ in [0,1] rescues this rule; replace or improve the channel | 2607.07436 |
| **Defect-injection audit of the eliminator** | Mutations whose target-property change is established by an independently warranted oracle or declared contract | Deterministic grader recall 1.0 on syntactic classes, ≈0 on semantic ones (n=155/class); located a real judge at ρ(F→P)≈0.01 | A prerequisite for estimating this eliminator's operating point; measures but does not repair | 2607.07436 |
| **Bind critique to the candidate state (broadcast topology)** | Protocol can enforce re-approval of a shared candidate | Uptake 0.336 → 0.935; guided repair 0.051 → 0.286; final pass 85.2% → 89.2%, at higher token cost | Addresses uptake, not detection; its value depends on whether the critique carries independently measured information | 2607.15388 |
| **Cross-family generation** | Access to genuinely different generators | Same-model resample ρ̂ median 1.00 (majority-of-3 gain 0.001) vs cross-family ρ̂ ≈ 0.58–0.60 | A measured route to lower dependence in this cited comparison; not a universal estimate or a fix for the eliminator | 2607.23931 |

---

## 7. Preservation-first strategy for h-EPI

The repository does not currently need a statistical eliminator. Its safe next sequence is
identity- and criticism-preserving:

1. Define the unit being compared and the preservation invariant. Do not assume that shared
   conclusions imply equivalent reasoning or that all rival interpretations are exclusive.
2. Bind every candidate and source surface by exact identity. Group exact byte duplicates only
   for navigation; merging substantive positions requires an independently reviewed
   equivalence claim and preserved provenance.
3. Derive snapshot changes from both supplied inventories. The local
   `derive_translation_snapshot_delta` implementation now computes retention, additions,
   removals, explicit immediate replacements, and four nested change projections. Similarity
   and stable names cannot manufacture continuity.
4. Complete and run HRC-1's intended-blind 34-mutation and six-control programme. Its current
   controller is a finite conformance design, not yet an execution result; producer blindness
   remains unverified and its verdict is null.
5. Supply typed fixtures, held-fixed conditions, comparators, expectations, and executors for
   all nine generated semantic attack families. They currently remain
   `DEFERRED_MISSING_SEMANTIC_BINDINGS`.
6. Treat a failure as potentially bearing on candidate, auxiliary, test, and scope together.
   A forced binary “which candidate is wrong?” question is inadmissible because “both,”
   “neither,” test defect, scope defect, and unresolved can remain live.
7. Bind criticism to exact identities and append-only history without automatically deleting
   the target. Revision requires an authorized action; rejected or uncertain material remains
   recoverable history rather than silent churn.
8. Close the missing iteration lineage from test execution through observation, inquiry,
   research disposition, authorized revision, successor snapshot, exact delta, and hardening.
9. Authenticate review and bind a real model executor or proof checker wherever the claimed
   result depends on execution.
10. Run the fresh blind Popper translation and hostile restraint mutations. Disagreement may
    open a source-bound problem; agreement has no confirmatory force.
11. Keep voting, reranking, and clustering outside the semantic core. They may support
    reversible navigation or workload scheduling, but must not retire a candidate or promote a
    semantic claim without an independently warranted rule.

If a future corpus really does contain hundreds of candidates, first measure exact-duplicate
rates, cross-candidate dependence, end-to-end false elimination, and defect recall on validated
mutations plus controls. Poor recall does not by itself make partial pruning unsafe; a sound but
incomplete refuter can still remove some candidates. Conversely, no shortlist is guaranteed to
retain the correct answer without sound refutations or a separate coverage theorem.

---

## 8. Where this review found no measurement

Stated plainly, because several of these are load-bearing.

1. **No end-to-end result located for the original two-stage critic and judge.** The channel
   sweep covers one grader with ρ(F→P) in {0.2, 0.45, 0.7} and symmetric noise up to 0.4. A
   critic's objection rate on clean items is not the judge's end-to-end false-conviction rate,
   so those two marginals cannot be summed into κ. The composite event and both stagewise
   conditional rates must be measured. Any direct one-channel conclusion is an extrapolation.

2. **No measured procedure for repairing a miscalibrated critic.** Defect injection *measures*
   ρ(F→P); the deployment playbook's only prescriptions are "lower the effective ρ(F→P) or defer
   self-evolution," with no measured method for the former. The judge-calibration papers listed
   in §5c may cover this — I did not verify them.

3. **No measured application of Dung admissibility / grounded / preferred extensions to
   automatically extracted natural-language attack graphs with end-task accuracy against ground
   truth.** The one systematic measurement I read uses QuAD gradual semantics and scores *rank
   correlation*, not extension correctness. Whether a grounded extension over an
   LLM-extracted graph recovers a correct claim at a useful rate appears unmeasured.

4. **No measured truth-selection over long-form contradictory *analyses*.** The answer-selection
   studies use short or canonical outputs. The long-form argumentation study instead measures
   graph recovery and rank agreement, not truth-selection among complete analyses. The basin
   abstraction, coupling metrics, and oracle ceilings therefore do not yet establish how the
   same machinery behaves when candidates are paragraph-length arguments with no canonical
   answer string.

5. **The n = 1 case is a hole in both the truth-discovery and weak-supervision literatures.**
   Both fields measure accuracy on corpora with many objects and overlapping sources. With one
   object, source reliability is not identifiable from corpus agreement alone; a system can
   still emit a result by importing external anchors or priors, but the corpus does not estimate
   those quantities. I found no work that closes this gap.

6. **Nothing measured on whether an anti-relapse ledger alters correlated-error structure.**
   Plausible mechanism (excluding previously-refuted positions should decorrelate later
   candidates), no evidence either way.

7. **Whether backfire persists in reasoning-native models is flagged by the authors as the
   central open question**, with a failed preliminary attempt (samples exhausted the token
   budget on hidden reasoning). If your generator is reasoning-native, the 56.6%/65.7% figures
   may not transfer.

8. **The generator side is worse-measured than the selector side.** ARBITER, RISC and the
   backfire study all take the candidate pool as given. Almost nothing measures how to generate
   a pool whose correct member is *findable* — which is arguably the primary unsolved problem
   for a conjecture-generation harness, and the point at which this literature stops being
   useful.

---

## Reading order if you only read three

1. **arXiv:2607.07436** — the conditional threshold cliff, the tested non-monotonic pattern, the silent aggregate behavior, and the
   audit. It motivates an end-to-end measurement; it does not identify the operating point from
   the 12% marginal alone.
2. **arXiv:2607.23931** — why dependence must be measured before counting votes, and how
   cost-sensitive thresholds behaved under the study's measured correlation.
3. **arXiv:2605.26172** — the negative ladder. Nine plausible correction strategies, measured,
   almost all harmful. Worth reading before building any of them.
