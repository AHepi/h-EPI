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

## Amendments, after thirteen architectures were run and stopped

Thirteen architectures ran before the sweep was stopped. Their records are kept in
`forge/mini/runs/arch-sweep/`. Three amendments follow, all made **after** that evidence was seen
and therefore all stated here as new proposals to be defended, not folded into the text above.
The corrected sweep runs into `forge/mini/runs/arch-sweep-2/` and is the block these predictions
are read against.

**Amendment 1 — the proposer's instruction names the kernels in full.** The instruction said
"recovery, recovered-from-prose, response-verdict, refusal-phrase"; the executor knows them only as
`conformance.kernel.recovery` and siblings. Nine of the twenty-one proposals in the aborted runs
died on that mismatch with `MINI_KERNEL_UNKNOWN` and produced no behaviour — every loss in those
runs had this one cause. The loss was not evenly spread: `a05` and `a08` lost two of three, `a11`
its only one, `a07` none. **A machinery
break whose rate varies with the treatment confounds the measure it varies with**, and the measure
here is exactly whether architectures differ in what they produce. The defence for changing a
prompt after seeing evidence is that this changes what the machine can be asked, not what the
answer is allowed to be: no expectation, no kernel, no scoring rule moves. Registered as M21.

**Amendment 2 — a second, coarser measure is reported beside the pre-registered one.** The
pre-registered behaviour is `(kernel, answer-before, answer-after)`, and the answers are functions
of texts the proposer wrote freely. Two architectures can share such a triple only by writing the
same text. In the aborted runs they sometimes did — `a00` and `a03` both reached
`(refusal-phrase, "I'm sorry", "I'm sorry")` — so the measure is not dead, but its uniqueness count
is inflated by textual coincidence in a direction that always favours K2 and K4. The **probe** is
the same row coarsened onto a finite grid: `(kernel, what was expected, what happened)`, six
kernels by two expectations by three outcomes, thirty-six cells, which architectures can share by
accident far more easily than they can share a sentence. Both are reported. **The pre-registered
behaviour count remains the measure K2 and K4 are read against**; the probe count is a post-hoc
reading that says whether a K2 pass survives coarsening, and a K2 that passes on behaviours and
fails on probes is reported as exactly that.

**Amendment 3 — the pair-execution seat honours the window its stage declares.** The seat chose the
proposals to run by a rule written into it, `cycle == this cycle`, and never read the port its stage
declares. Every manifest before this sweep declared `this_cycle` there, so the two agreed and
nothing showed. **Eighteen of the 36 architectures — exactly half — put `execute` before `propose`**
and so can only work if the second cycle reaches the first cycle's proposals; under the seat's own
rule they reach nothing, ever. `a02`, `a09` and `a10` each ran three full cycles and submitted three
empty execution artifacts. The dead half is the lagged half: every architecture at five and six
lagged edges is in it, so the defect would have manufactured exactly the monotone decline K3 exists
to look for, and the sweep would have supplied the evidence for the uselessness argument by
breaking. `MachineContext.admits` now resolves the declared port by what it draws and returns its
window; a stage declaring no such port keeps this cycle, so no earlier manifest moves. Registered as
M22, with the boundary as two tests in `tests/mini/test_pairs.py`.

This is a change to the machine, not to the prompt, and it is the one kind of amendment that needs
saying twice: **the corrected sweep runs a machine that the aborted sweep did not run.** The two
blocks are not comparable arm for arm, and the thirteen aborted runs are kept as the record of the
break rather than as a baseline.

**Also recorded.** `unrunnable` is now a column of the reading, so the rate of machinery loss is
visible per architecture rather than inferable from a gap.

## What this cannot settle

Nothing here is `Origin`; `New` remains unestablishable. One wiring, one model, one task, three
cycles. A behaviour unique to an architecture is not thereby a blind spot: it is a pair the machine
ran that no other architecture ran, and whether it exposes a divergence between documentation and
code is a reading a person makes. And 36 runs of three cycles is one sample of each architecture —
Theorem 7 bounds what more cycles could add, it says nothing about what a second sample would.
