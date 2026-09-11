# ARCH-SWEEP-1: every architecture of one wiring, on the kernel-gap question

A pre-registration. Written and committed before any architecture was run.

## Why, and why it is small

Every block in this repository — five experiment rounds, three use-test blocks, BUILD-TEST-1,
CONSTRUCT-TEST-1 — ran the fully synchronous architecture and nothing else. `ARCHITECTURE_SPACE.md`
shows that is one point of a lattice: for this wiring there are **36 distinct architectures**, and
the ordering of the stage list is what selects among them. The question mini was built for — can a
loop find blind spots nobody wrote down — has therefore never been asked of the space, only of one
corner of it.

Theorem 7 makes the experiment affordable. The space saturates at **three cycles**: a one-cycle run
distinguishes two states per edge and cannot tell the architectures apart, and a fourth cycle adds
no distinction. So three cycles per architecture is not a budget compromise; it is the whole space.

## The wiring, and one thing removed

`rules`, `source`, `propose`, `execute`, `criticise`, with `verdict` pinned last. Eight port edges.
120 orderings compile; they realise **36 architectures**, one fully synchronous and thirty-five
lagged, every one an acyclic orientation as Theorem 1 requires.

**No grid.** BUILD-TEST-1 measured an enumerated answer space driving contradictions to zero on
both arms while construction stayed perfect. Handing one over here would make every architecture
look alike for a reason that has nothing to do with architecture.

## The measure

Per architecture, all mechanical:

1. `proposals` parsed, `executed` pairs, `contradicted` — the machine's answer differing from the
   proposer's stated expectation.
2. `quoted` — contradictions whose stated reading quotes words that occur verbatim in the
   docstrings. BUILD-TEST-1 found thirteen of twenty-four contradictions citing no rule at all, so
   the unfiltered count is known to be mostly noise.
3. `behaviours` — distinct `(kernel, answer-before, answer-after)` triples produced.
4. **`unique`** — behaviours this architecture produced that **no other architecture** did. This is
   the measure the whole sweep exists for.

No architecture is ranked. A candidate boundary becomes a kernel row only by a person's reading.

## Held fixed

One model throughout, `deepseek-v4-pro` on the vendor path, reasoning at the endpoint's default,
temperature 0, seed 7, `window: all` on every port, three cycles, the same problem text, the same
proposer instruction, the same critic instruction. The **only** thing that varies across the 36
runs is the order of the stage list.

## What is predicted, before the run

- **K1.** The synchronous architecture `A00` produces at least one contradiction that quotes the
  rule. It is the architecture every earlier block ran, and BUILD-TEST-1 produced such
  contradictions from an equivalent brief.
- **K2.** At least one lagged architecture produces a behaviour `A00` does not. **If none does, the
  ablation lattice bought nothing here**, and mini's configurability — whatever the theorems say
  about its size — is empirically idle on this question.
- **K3.** Distinct behaviours do not fall monotonically as lagged edges increase. Monotone decline
  would be evidence that these seats behave monotonically in what they are shown after all, which
  Theorem 4 says would collapse the space to its maximum.
- **K4.** The union of behaviours over all 36 architectures is strictly larger than `A00`'s alone.
  K4 is K2 aggregated, and is the number that says whether the space is worth occupying.

**K2 is the experiment.** K1 is a sanity check on the brief. K3 tests the assumption behind the
only available uselessness proof. K4 is the summary.

## What this cannot settle

Nothing here is `Origin`; `New` remains unestablishable. One wiring, one model, one task, three
cycles. A behaviour unique to an architecture is not thereby a blind spot: it is a pair the machine
ran that no other architecture ran, and whether it exposes a divergence between documentation and
code is a reading a person makes. And 36 runs of three cycles is one sample of each architecture —
Theorem 7 bounds what more cycles could add, it says nothing about what a second sample would.
