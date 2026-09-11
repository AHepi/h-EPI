# The space of mini configurations, and an attempt to prove it useless

Every proposition below is checked by enumeration in `tests/mini/test_configspace.py`. No model is
called. The attempt to prove the space useless **fails**, and the precise point at which it fails
is the useful result.

## 1. The object

A mini template declares stages, and each stage's ports draw artifacts of other stages' kinds. Two
things decide what a seat is shown:

- the **ordering** of the stage list, which decides whether a producer has produced yet when its
  consumer runs;
- each port's **window**, which filters by the cycle coordinate the record already carries.

Write a **wiring** as `(S, z, E)`: stages `S`, a distinguished last stage `z` (mini requires a
cycle to end in a verdict), and edges `E ⊆ S × S` where `(c, p) ∈ E` means *c reads p*.

An **ordering** is a permutation of `S ∖ {z}` followed by `z`. For an edge `e = (c, p)` under
ordering `σ`, define the **lag**

> `ℓ_σ(e) = 0` if `σ(p) < σ(c)`, else `1`.

A **configuration** is an ordering together with a window per edge. Its meaning is the function

> `delivered(ℓ, w, t)` = the producing cycles that reach `c` on `e` at cycle `t`
> `= { k : 1 ≤ k ≤ t − ℓ and w admits k at t }`

which is exactly `creib.forge.mini.windows.Window.admits` composed with "a producer placed after
its consumer has produced only through `t − 1`".

The blind-spot wiring this repository runs has `S ∖ {z}` = rules, source, cell, propose, execute,
criticise, `z` = verdict, and seven edges.

## 2. Theorem 1 — the architectures are the acyclic orientations

*A lag vector `ℓ: E → {0,1}` is realisable by some ordering iff the orientation that sends `p → c`
when `ℓ(e)=0` and `c → p` when `ℓ(e)=1` is acyclic. Edges incident to `z` are forced to `ℓ=0`.*

**Proof.** An ordering is a linear extension. A lag vector fixes, for each edge, which endpoint
comes first; the orientation records exactly that. A set of such constraints has a linear
extension iff the digraph they define has no directed cycle. `z` is last, so every edge incident to
it is oriented toward `z`. ∎

**Count.** By Stanley (1973) the number of acyclic orientations of a graph `G` is `|χ_G(−1)|`. For
the blind-spot wiring the free-edge graph is two pendants on a triangle, `χ_G(k) = k(k−1)³(k−2)`,
so `|χ_G(−1)| = |(−1)(−2)³(−3)| = 24`.

**Checked.** 5040 orderings of seven stages; 720 compile (`MINI_VERDICT_NOT_LAST` refuses the
rest); those 720 realise exactly **24** distinct lag vectors, every one acyclic, matching `|χ_G(−1)|`.

## 3. Theorem 2 — every delivered set is a suffix interval, and there is a maximum

*For every `ℓ, w, t`, `delivered(ℓ, w, t)` is `∅` or an interval `[a, b]` with `b ∈ {t, t−1}`. The
partial order by inclusion has the unique maximum `[1, t]`, attained only by `ℓ=0, w=all`.*

**Checked** for every named window, both lags, cycles 1–5.

A corollary worth naming: **`previous_cycle` makes an edge's lag unobservable**, since both lags
deliver `{t−1}`. Ordering is not a free parameter on such an edge.

## 4. Theorem 3 — the maximal configuration dominates

*Let `M` be the configuration with every edge same-cycle and every window `all`. For every
configuration `C`, every edge, and every cycle, `delivered_C ⊆ delivered_M`.*

**Proof.** Immediate from Theorem 2: `[1,t]` contains every reachable set. ∎

## 5. The attempted proof of uselessness, and where it fails

**Theorem 4 (conditional collapse).** *Suppose every seat's output depends monotonically on what it
is shown — that adding an artifact to a delivered set never makes a seat's contribution worse.
Then no configuration outperforms `M`, and the whole space has exactly one useful point.*

**Proof.** By Theorem 3, `M` delivers a superset on every edge at every cycle. By monotonicity, no
seat does better on a subset. ∎

This is the only route to a uselessness proof the structure offers, and it is a real one: **if
seats were monotone, mini's 24,525 distinguishable configurations would collapse to one**, and
every config-mutation study in this repository would be measuring noise.

**Theorem 5 (the antecedent is false here).** *Monotonicity is refuted by this repository's own
records.*

- `forge/mini/runs/buildtest/block-1/`: arm R is shown the checks' documented rules and no code;
  arm L is shown the rules **and** the complete source, a strict superset. Across eight paired
  cells R produced 14 contradictions to L's 10, 67 distinct behaviours to 61, and 44 behaviours
  unique to it against L's 38. A strictly larger delivered set did not produce a weakly better
  contribution.
- Same block, `qwen3.5:397b`: its `repeated` condition, shown nothing of the run's own history,
  found the guard at the seventh proposal and reached zero violations; both of its evidence
  conditions, shown strictly more, exhausted eight proposals and accepted none.

So Theorem 4's antecedent fails, its conclusion does not follow, and **no proof of uselessness is
available by this route.** That is not a proof of usefulness. It is the precise statement of what
would have to be shown.

## 6. Theorem 6 — what the space actually is

*The configuration space is a lattice of information ablations over a single record.* Every
configuration delivers, on each edge, a subset of what `M` delivers; the maximum withholds nothing;
`ℓ=1, w=this_cycle` withholds everything. Nothing in the space gives a seat information the record
does not hold, and nothing gives a seat more than `M` does.

Therefore the space's usefulness is **exactly** the usefulness of controlled withholding, and the
question "is mini's configurability useful for finding blind spots nobody wrote down" reduces to
the question "are these seats non-monotone in a way that can be steered". Section 5 shows they are
non-monotone. Whether it can be *steered* is not settled by any theorem here.

## 7. Theorem 7 — the space saturates at three cycles

*Let `B(t)` be the number of configurations distinguishable by what they deliver over cycles
`1…t`. For the blind-spot wiring, `B(1) = 128`, `B(2) = 8352`, `B(t) = 24525` for all `t ≥ 3`.*

**Checked** by enumeration over all 2187 window assignments and all 24 lag vectors.

Two consequences with teeth:

- **A one-cycle run distinguishes only two states per edge** — the producer's artifact, or nothing.
  It cannot tell 24 architectures apart. Several early rounds in this repository ran three cycles;
  the shortest could not have measured what they varied.
- **A fourth cycle adds no new architecture.** Longer runs buy repetition, not discrimination.
  Three cycles is the whole space.

## 8. Size

| | |
|---|---|
| orderings of seven stages | 5040 |
| orderings that compile | 720 |
| distinct architectures (lag vectors) | **24** |
| named window assignments | 3⁷ = 2187 |
| naive product | 52,488 |
| **distinguishable configurations** | **24,525** |
| collapse from `previous_cycle` | 27,963 |
| window assignments under which all orderings coincide | 9 |

The overcount is not small: **more than half** the naive product is `previous_cycle` edges making
their ordering irrelevant. A study that varies ordering on such an edge varies nothing.

## 9. What this settles, and what it does not

**Settled.** The space is finite, computable, and 24,525 wide for this wiring. Its architectures
are acyclic orientations, counted by a chromatic polynomial at −1. It has a maximum that dominates
everything. It saturates at three cycles. It is a lattice of ablations, not a space of capabilities.

**Not settled, and not provable from here.** Whether any of its 24,524 non-maximal points is worth
occupying. That requires showing a seat that does better when shown less, *reliably and by
design* — and the two instances in Section 5 are an aggregate and a single model, which is evidence
that monotonicity fails, not evidence that ablation can be steered.

**What follows.** The experiment is now well-posed and small: 24 architectures, one wiring, three
cycles each, one model, measured on candidate boundaries found and deduped across architectures.
Twenty-four runs of three cycles settles the discrimination question for the ordering dimension
completely, because Theorem 7 says there is nothing beyond it to see.
