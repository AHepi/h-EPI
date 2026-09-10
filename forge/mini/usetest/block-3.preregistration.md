# MINI-USE-TEST-1, block 3: pre-registration

Written and committed before any instance of this block was drawn or any arm was run. Method
version 5. The freeze it runs against (`subject.clean.py`, `grid.txt`, `frozen.json`) is
unchanged and was committed at `8c276d3`; nothing in the test space moves for this block.

## Why a third block

Block 2 (`deff05f`, method version 4) achieved information parity and a ceiling reserved before
each send, and every one of its six arms recovered nought of three — including arm A, which had
recovered three of three in block 1. That was traced to the block's own configuration rather
than to any arm. Reasoning was off, because M17 says this model cannot return a parseable reply
inside a per-call cap small enough to walk a twenty-cell grid; with it off, arm A named the
seeded mutation correctly and then wrote a reproducer with the trailing object left out, which
does not separate the clean subject from the mutated one. The diagnosis survived; the
demonstration did not.

The operator's instruction was to raise the token allowance to match rather than shrink the grid
or change the model. Block 3 is that: **the same six arms, the same three mutations, the same
grid, reasoning on, and a per-call allowance large enough to hold it.**

Blocks are never compared arm for arm across method versions, and block 3 is not compared with
block 2 or block 1. What can be said across them is what the pre-registrations say was changed.

## What changed from block 2, and nothing else did

| | Block 2 | Block 3 |
|---|---|---|
| reasoning setting | off | **on** |
| completion tokens reserved and capped per send | 4,000 | **32,000** |
| completion tokens for the whole arm | 164,000 | **1,312,000** |
| invocations | 41 | 41 |
| timeout | 600 s | **900 s** |
| arms, grid, model, criterion, instances | — | unchanged |

The arms are A, B, C, C-rules, D and E exactly as block 2 defined them; the source seat feeds the
proposer and critic of C, D and E, and C-rules withholds it with nothing else changed. The model
is `deepseek-v4-pro:0813` throughout. Temperature 0, seed 7.

## What the probes said before this block was registered

Two probes on scratch instances, outside the block and not part of it, at the configuration
above:

| Arm | Calls | Completion tokens | Seconds per call | Pairs executed |
|---|---|---|---|---|
| C | 5 | 75,493 (15,098 a call) | 76 | 2 of 3 |
| D | 5 | 65,088 (13,017 a call) | 63 | 0 of 2 |

Arm C executed two of three proposals where block 2's arm C executed four to six of twenty. The
one failure was M19, a rewrite that leaves the grammar. So reasoning on does what it was expected
to do to construction, and 32,000 is the first per-call allowance at which a mini proposer
returns anything at all: at 2,000 and at 8,000 every reply was cut off inside its reasoning and
no proposal survived.

The whole block is about 385 model calls, roughly 5.8 million completion tokens and two hours of
wall clock at five concurrent processes.

## The criterion

Unchanged, and mechanical. `sealed.json` is opened only after every packet in the instance is
written. A packet **recovers the hidden defect** when its own `reproducer`, run through the
seeded kernel, tells the clean subject from the mutated one. A cell counts as **covered** only
when a validator proves the executed text is the cell that was assigned.

## The instances

The same three S2 mutations as blocks 1 and 2, so difficulty is held fixed: `s2-fence-single-only`,
`s2-duplicates-outside-fence-only`, `s2-span-normalised-one-side`, drawn as `v5-s2-1`, `v5-s2-2`,
`v5-s2-3`. Earlier blocks' records stay where they are.

## What is predicted, before the run

- **Q1.** Arm A recovers at least 1 of 3. In block 2 it recovered 0; the probe that gave it
  reasoning and a 16,000 cap recovered 1 of 3, and 32,000 is twice that.
- **Q2.** Arm C covers more cells than block 2's arm C did, because reasoning fixed construction
  in the probe. Cell coverage, not defect recovery, is what this predicts.
- **Q3.** Arm C still recovers no more defects than arm A. Block 2 answered the parity question
  negatively and nothing here is designed to change it.
- **Q4.** Arm C and arm C-rules stay level on defects recovered. Block 2 found the source made no
  difference; if reasoning on reverses that, the earlier reading was about the model's capacity
  to use the source rather than about the loop.
- **Q5.** No arm breaches the ceiling, and every run's record names the endpoint it was given.

Q1 is the one that tests the explanation block 2 gave for its own null result. If arm A stays at
nought with reasoning on and a cap that fits, then block 2's account of why it fell was wrong,
and something other than the reasoning setting is responsible.

## What this block cannot settle, and what it carries forward unfixed

Strata S1, S3, S4 and S5 are not built, so H2, H3 and H5 remain not run. One model runs every
arm: nothing here generalises past `deepseek-v4-pro:0813`. Three instances is three instances.

Two known defects are carried into this block deliberately rather than repaired, because
repairing them inside a registered protocol would be a further method change and the operator
asked for the allowance change alone:

- **M20, the packets are not blind.** Every mini arm's packet leaks the vocabulary of the grid
  (`kernel`, `cell`, `proposal`). The adjudication of this block is therefore **not blind** for
  the mini arms, and will not be described as such.
- **M19, rewrites that leave the grammar.** Still the dominant reason a pair cannot be run. If
  arm C's coverage rises under Q2 it is because reasoning reduced M19, and that will be reported
  as a measurement of construction rather than of search.
