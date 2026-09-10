# MINI-USE-TEST-1, block 2: pre-registration

Written and committed before any instance of this block was drawn or any arm was run. Method
version 4. The freeze it runs against (`subject.clean.py`, `grid.txt`, `frozen.json`) is
unchanged and was committed at `8c276d3`; nothing in the test space moves for this block.

## Why a second block, and why it is not comparable to the first

Block 1 (`d2d3f90`, method version 3) put arm A — one model reading the subject's rules and its
complete source — against three mini arms that were shown the rules and no code. Arm A recovered
3 of 3 seeded defects at one call each and the mini arms recovered none. That result cannot
separate two explanations: the loop is worse than a direct reading, or the loop was reading less.
Block 2 removes the second explanation.

Three things changed, so the arms of block 1 and block 2 are not comparable arm for arm, and no
row of this block will be placed beside a row of that one:

1. **Information parity.** The proposer and the critic of arms C, D and E are shown the
   subject's complete source through a machine seat (`mini.usetest-source.v1`), which is what arm
   A is shown. A new arm, **C-rules**, is arm C with that seat removed and nothing else changed.
2. **A ceiling reserved before the send.** A call and its completion allowance are taken out of
   the budget before each send; a send whose reservation will not fit is not made, and the run
   stops with a typed reason. The same figure is the request's own `num_predict`, so no reply can
   be larger than what was reserved for it. Block 1's ceiling was counted after the fact.
3. **A ceiling that admits the whole grid**, identical for every arm (below).

## The arms

| Arm | What it is | Shown the source | Calls per cycle |
|---|---|---|---|
| A | direct audit, one candidate, no execution | yes | — (1 call in total) |
| B | adversary that may run any test it likes | yes | — (up to the ceiling) |
| C | mini core: cell, propose, execute, verdict | **yes** | 1 |
| C-rules | arm C with the source seat removed | **no** | 1 |
| D | full mini: C plus a critic each cycle | **yes** | 2 |
| E | D with attention on | **yes** | 2 |

C-rules is the control on the brief. C beside C-rules says what withholding the code costs with
the loop, the grid, the model and the ceiling held fixed. C beside A says what the loop costs
with the information held fixed. Neither pair is informative without the other, which is why
block 1's numbers could not settle anything.

## The ceiling, identical for every arm

| | |
|---|---|
| invocations | **41** |
| completion tokens | **164,000** |
| completion tokens per call (reserved, and the request's cap) | **4,000** |
| model | `deepseek-v4-pro:0813` |
| reasoning setting | **off**, explicitly |
| timeout | 600 s |
| temperature, seed | 0, 7 |

41 invocations is what walking the whole grid costs the most expensive arm: 20 cells × 2 calls a
cycle for D and E, plus the one call every arm spends writing its packet. Arm C and C-rules spend
20 + 1 and have the rest spare; arm A spends 1. The ceiling is a ceiling, not a quota, and an arm
that does not need it is not penalised for that.

## Why the reasoning setting is off, and what that costs

Six probes on scratch instances, outside this block and not part of it, on
`deepseek-v4-pro:0813`:

- With reasoning **on** and a 2,000-token cap, every reply was cut off inside its reasoning: 3
  refused replies, 0 proposals.
- With reasoning **on** and an 8,000-token cap, the model spent about 6,000 tokens a call on
  reasoning and still returned nothing parseable: 24,195 completion tokens, 0 proposals.
- With reasoning **off**, replies parse at about 250 tokens a call.

Reasoning on is therefore not affordable for this model under any ceiling this block can pay for,
and it is set off rather than left to the endpoint's default. This is a limit of the block and is
recorded as one: block 1 ran with the setting unset, which for this model means the provider's
default, so block 1's arms and this block's arms differ in reasoning as well.

## The criterion

Unchanged from block 1, and mechanical. `sealed.json` is opened only after every packet in the
instance is written. A packet **recovers the hidden defect** when its own `reproducer`, run
through the seeded kernel, tells the clean subject from the mutated one. On a clean control any
separation is impossible, so a claim there is a false positive by construction unless it is about
the tree's own `H43`, which is recorded separately as a true boundary.

A cell counts as **covered** only when a validator proves the executed text is the cell that was
assigned. An assignment is a reservation and a proposal is a claim; neither is coverage.

## The instances

Three, the same three S2 mutations block 1 drew, so the difficulty is the same even though the
arms are not: `s2-fence-single-only`, `s2-duplicates-outside-fence-only`,
`s2-span-normalised-one-side`. They are drawn as `v4-s2-1`, `v4-s2-2`, `v4-s2-3` under
`forge/mini/runs/usetest/`. Block 1's records stay where they are and are not overwritten.

## What is predicted, before the run

- **P1.** With the source in front of it, arm C recovers more than 0 of 3. Block 1's mini arms
  recovered 0 of 3 without it.
- **P2.** Arm A still recovers 3 of 3 at one call. Nothing about arm A changed.
- **P3.** C beats C-rules on defects recovered. If it does not, the information gap was not what
  was stopping the mini arms, and the loop is the thing that is not working.
- **P4.** D and E do not beat C. Block 1 gave the critic no advantage and nothing here is
  designed to give it one.
- **P5.** No arm breaches the ceiling, and every run's record names the endpoint it was given.

P3 is the one that matters. P1 without P3 would say only that the source helps a model, which
nobody doubts. P3 is what would say the loop can use it.

## What this block cannot settle

Strata S1, S3, S4 and S5 are not built, so H2, H3 and H5 of the protocol are not testable here
and are recorded as not run rather than as passed. One model runs every arm, which removes a
model-by-arm confound and forfeits the rotation's protection against a model-specific result:
nothing here generalises past `deepseek-v4-pro:0813`. Three instances is three instances.
