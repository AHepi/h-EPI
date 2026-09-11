# ARCH-SWEEP-1-CONTROL: the same architecture, thirty-six times

A pre-registration. Written and committed before any run of this control exists.

## Why it exists, and why it was missing

ARCH-SWEEP-1 ran 36 distinct architectures of one wiring, once each, and measured the union of
`(kernel, answer-before, answer-after)` behaviours: **21**, against the synchronous architecture's
**3**. Read on its own that is K4 holding, and K2 with it.

The block's own records refuse that reading. Eighteen of the 36 architectures do not run the
`rules` stage before the proposer, so their cycle-1 proposer prompt is byte-identical — one digest,
416 characters, reconstructed from the records rather than assumed. Those eighteen returned **three
different proposals**: ten `refusal-phrase`/`moves`, six `refusal-phrase`/`unchanged`, two
`recovery`/`moves`. Same prompt, same model, temperature 0, seed 7.

The endpoint is not deterministic, and the behaviour measure is keyed on text the proposer chose.
So a union of 21 over 36 runs is consistent with two stories and ARCH-SWEEP-1 cannot tell them
apart: the lattice found things one corner of it could not, or **thirty-six draws found things one
draw could not**. The second story needs no architecture at all.

## The control

Run `a00`, the fully synchronous architecture, **36 times**, changing nothing. Same manifest, same
model, same three cycles, same everything ARCH-SWEEP-1 held fixed. Read it with the same reader.

That is the null the sweep needed: 36 runs, one architecture, against 36 runs, 36 architectures.
Equal call count, equal cycles, equal everything but the variable.

## What is predicted, before the run

- **C1.** The 36 repeats of `a00` do **not** all produce the same behaviour set. If they did, the
  cycle-1 divergence above would have to be explained some other way, and this control would be
  measuring something other than what it claims.
- **C2 — the one that matters.** The union of behaviours over 36 repeats of `a00` is **smaller**
  than the union over the 36 distinct architectures (21). If it is not smaller, **K2 and K4 are
  withdrawn**: the sweep's gain is the draw, the lattice is idle on this question, and no amount of
  occupying the configuration space buys a behaviour that repetition would not.
- **C3.** The number of distinct cycle-1 proposals over 36 repeats is at least 2, and is compared
  with the 3 observed across the 18 byte-identical prompts in ARCH-SWEEP-1.

**C2 is the control.** It is stated so it can lose, and losing it withdraws this repository's two
surviving predictions about the configuration space. C1 and C3 are checks that the control is
measuring the draw and not something else.

## What it still cannot settle

A union that is smaller does not make the difference *architectural* — it makes it not-obviously-
the-draw, which is weaker and is all a single control buys. One wiring, one model, one task, three
cycles, one repeat count. And nothing here is `Origin`: `New` remains unestablishable, as it was
before.

## What the control shows

36 repeats of `a00`, all reaching `RUN_ENDED`. 216 executor rows, 110 named as repeats, **zero that
could not be run**, 106 executed.

- **C1 holds.** The 36 repeats produced **28 distinct behaviour sets**. Running one architecture
  thirty-six times is thirty-six different runs, so the control measures the draw, which is what it
  was for.
- **C2 holds.** Union of behaviours over 36 repeats of `a00` is **15**, against **21** over the 36
  distinct architectures — and the control had more executed rows to reach it with, 106 against 90.
  **K2 and K4 are not withdrawn.**
- **C3 holds, and by more than it predicted.** The prediction was at least 2 distinct cycle-1
  proposals from a byte-identical prompt; there are **6 by content** (7 by bytes — one differs only
  in the JSON's whitespace, which is worth saying once rather than counting twice). Among them a
  kernel the brief never named, `conformance.kernel.span-occurs`. ARCH-SWEEP-1 saw 3 across its own
  18 byte-identical prompts; 36 draws of the same prompt find 6.

## The result C2 does not cover

C2 was written against the pre-registered behaviour measure. The probe measure from ARCH-SWEEP-1's
Amendment 2 answers the opposite way: **9 probe cells for 36 repeats of one architecture, 8 for 36
distinct architectures.** On the finite grid — which kernel was probed, what was expected, what
happened — repetition covered slightly *more* than the lattice did, with more draws.

So the two measures split, and the split is the finding. Occupying the configuration space produced
more distinct behaviour triples per run than repeating one corner of it, and did not produce more
distinct probe cells. Since a behaviour triple is keyed on text the proposer chose and a probe cell
is not, the plainest reading is that the lattice **varies what gets written and not what gets
tested**. K2 and K4 survive their own test on the record; they survive it holding a result that
says what surviving it is worth.

## What this still cannot settle

A smaller union under repetition does not make the difference architectural — it makes it
not-obviously-the-draw, which is weaker, and is all one control buys. One wiring, one model, one
task, three cycles, one repeat count, and a proposer whose answer to a byte-identical prompt varies
six ways. Nothing here is `Origin`; `New` remains unestablishable.
