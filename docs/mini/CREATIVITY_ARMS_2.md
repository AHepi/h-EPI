# CREATIVITY-ARMS-2: the same comparison, with the machinery repaired

A pre-registration. Written and committed before any arm was run. Block 1 is
`docs/mini/CREATIVITY_ARMS.md` and its records are left exactly as they are; this is a **new method
version**, so no number here is compared arm-for-arm with a number there.

## Why there is a second block

Block 1 answered nothing it was built to answer. `docs/mini/ERRATA.md` lists why, item by item: of
roughly twenty oversights, three are about the model and the rest are about the apparatus — what it
could execute, what its critic could see, what its commitment format admitted, what its baseline's
seeds exercised, and what I measured. **Every headline null turned out to be a fact about the
machinery.**

The one positive result — arm `W` doubling arm `F`'s yield — survived as a number and lost its
cause. C12: `W`'s criticise **stage** never declared the `reads` port its **kind** declared, so the
critic never saw a reading in any of the sixteen segments, while being told to attack one by name.
Two other settings moved with it. The doubling is unattributed, and this block does not try to
recover it: it declares the port on the stage, holds the conjecture's rendering constant across every
arm, and measures the wiring as a first question.

## What is already known, measured before any model call

`tools/creativity_block2.py enumerate`, at zero model calls, over every function reachable by import
and **61** reply-shaped seed texts — block 1's fourteen and forty-seven more chosen so that a
function about something other than JSON has a chance to answer two ways.

| | |
|---|---|
| functions reachable | **66** |
| **non-constant over the pool** | **10** |
| executions | 120,780 |
| raise on at least one side | 96,924 (80%) |
| collapses | 9,121 |
| **collapses on non-constant functions** | **1,801** |
| **distinct non-constant functions with any collapse** | **4** |

Two things follow and are fixed here rather than discovered later. **Finding a collapse is worth
nothing**: a loop-free enumerator finds 1,801 of them on live functions for free, and it will beat
every model arm on that measure by three orders of magnitude. And widening the target space from the
registered four kernels to sixty-six functions was largely illusory — **ten are non-constant and
four of those collapse at all.**

The record is `forge/mini/runs/creativity-2/E/enumeration.json`.

## The measures

**Primary, and reported first whichever way it falls:** `collapse_on_non_constant` — a claimed pair
the machine confirms collapsed, on a function that is not constant over the pool. The enumerator
scores 1,801 on it. **It is expected to win, and that is the point of reporting it**: the model's
contribution cannot be finding a collapse.

**The one the enumerator cannot score on, by construction:** `grounded_T1` — the same, plus the
conjecture's prose quoting six or more consecutive words occurring verbatim in that function's own
docstring or source. The enumerator writes no prose. This is where a model can contribute something
the host cannot do for free, and `CON-MEASURE-EXCLUDES-BASELINE` says plainly that a measure only
one arm can score on is not a common measure — so both are reported, in this order, every time.

**Reported beside them, per arm and per repeat, whichever way they fall:** model calls, executed
rows, unrunnable rows, `format_drops`, over-sensitivity, distinct targets, distinct pairs,
`criticisms`, `attacks_landed`, `evidence_edges`, the grounds used by name, and **the number of rows
on which the live executor and the post-hoc verifier disagree**.

## The arms

Four arms, sixteen segments each, three repeats. **528 model calls.**

| arm | segments | criticism | critic sees | install map | adjudication | calls ×3 |
|---|---|---|---|---|---|---|
| **R** repeated | 16 | no | — | no | no | 96 |
| **F** full | 16 | yes | source, conj, execs | **yes** | no | 144 |
| **W** wired | 16 | yes | + **reads** | yes | no | 144 |
| **A** adjudicated | 16 | yes | + reads | yes | **yes** | 144 |

`S` and `N` are dropped. `S` — one conjecture at two calls — is stable across three blocks and
nothing further is learnt by paying for it again. `N` is dropped because block 1's `N`-against-`F`
null was **withdrawn** (ERRATA A1): `F` repeated a pair twice while being told not to, so the
contrast measured the carry being disobeyed, not the carry being worthless.

**`F` → `W` is one wiring change**, plus the instruction that says what to do with it — a port a seat
is not told to read is not a treatment, so the pair moves together by design and the arm measures the
pair. Nothing else differs: the same kinds, the same install map, the same conjecture rendering, the
same failure policy. `tests/mini/test_block2_arms.py` asserts each of those, including the one
assertion block 1 needed and did not have: that every stage lists every port its kind declares.

**`W` → `A` is the warrant and the adjudication.** `A`'s criticism commitment carries
`{attacks, ground, why}` under a JSON Schema, a machine seat resolves the named target against the
record, and status is computed from the attack relation rather than stored.

## The seven repairs, each answering a numbered erratum

1. **A format schema on the criticism commitment** (C6). Four of eight of block 1's `A` criticisms
   wrote prose where JSON was asked for and nothing checked, so the attack machinery engaged in under
   half the arm. The schema makes a missed shape a **retry** with the shape rendered.
   `cannot-tell` stays first-class: DeepReason measures the same model fabricating at 0–2% in prose
   and **100%** under a required closed field with no escape road, and prompt-level instruction is
   *voided* by the schema.
2. **A validity node** (C5). New ground **`test-is-unsound`**, whose target is an *execution*. The
   machine now mints its own edges: an execution attacks the reading it ran whenever the run did not
   bear the claim out — the check answered as the rule requires, or the claim could not be run at
   all. Attacking the execution refutes it, and a refuted attacker stops refuting, so the reading
   comes back. No new status rule: reinstatement already falls out of the fixed point. This is the
   criticism block 1 most deserved to hear and had nowhere to put — *the executor refused a true
   conjecture on an arity bound*.
3. **A baseline whose seeds make functions vary** (A3, A4), and the non-constant denominator above.
4. **A declared stochastic floor** (C7). Three repeats differing in the endpoint seed and **nothing
   else**; a test asserts the manifests are otherwise byte-identical. Every number in block 1 was one
   draw, from an endpoint that answered a byte-identical prompt six different ways.
5. **Sixteen segments** (the power problem). `W` 7 against `A` 5 at eight segments is not a result.
6. **Arity and module resolution in the live executor** (C9). The post-hoc verifier stays as a check
   **on** the executor rather than a substitute **for** it: where the two disagree, that disagreement
   is the finding and it is printed rather than folded into a total.
7. **One failure policy on every kind of every arm** (CON-FORMAT-KILLS-RUN): three retries, unlimited
   tolerance. Strictness and lifetime are one knob; holding tolerance unlimited is what stops an arm
   dying younger for being asked a stricter question. `format_drops` is recorded per arm anyway.

## What is predicted, before the run

- **P1.** `W` beats `F` on `grounded_T1` per call, at every repeat. If it does not, **the critic
  seeing the readings buys nothing**, and block 1's doubling — already without a cause — has no
  replacement.
- **P2 — the experiment.** `A` beats `W`. If it does not, **criticism that lands buys nothing over
  criticism that is only read**, at a point where the format no longer suppresses it, the test can be
  attacked, and there are enough draws to tell. That is the loop losing on the best version this
  repository can build, and it will be reported as such.
- **P3.** `A` repeats an earlier pair less often than `F` does — the carry steering correctly because
  the critic can attribute correctly.
- **P4.** `test-is-unsound` is used at least once. If the machinery to attack a test exists and
  nobody attacks a test, that is worth knowing about the critic, not about the machinery.
- **P5.** The enumerator beats every model arm on `collapse_on_non_constant` by at least an order of
  magnitude. Stated so that it cannot later be presented as a surprise.

**Every arm is expected to lose to `R` on cost alone at least once.** `R` is 2 calls a segment where
the loop arms are 3, and in block 1 it beat all of them per call. A loop that does not beat plain
repetition per call has not earned its wiring, and that comparison is reported on every repeat.

## When the block stops itself

`tools/creativity_block2.py block` preflights every manifest before the call that would pay for it
and reads every finished segment. Any **fatal** alarm stops that arm's repeat where it stands rather
than letting it finish and be compared. The modes are `docs/mini/CONFIG_MAP.md`'s alarm list, and
each one cost this repository runs before anyone was looking.

## What this block will not settle, named rather than omitted

**ERRATA C3 and C4 stand unrepaired.** Mini still dispatches on kind rather than on interface
structure, and a commitment still carries no `eval`, no budget and no `V(κ,c) ∈ {pass, fail,
overrun}`. So "attack surface" remains a metaphor here rather than a count, and
`crit(a) ⇔ interface.commitments ≠ ∅` is not a demarcation this machine can compute. A block that
fixed those is a different machine, and saying so is cheaper than pretending this one is it.

**C11 stands.** Block 1's `W/s02` critic argues this repository's own W2 finding is a misreading of
the fence rule rather than a divergence in the code. Nothing here adjudicates that, and a person
should.

**Block 1's effect stays unattributed** whichever way `F` → `W` falls here. A first test is not a
retrospective explanation of a different arm.

And the result that needs no further block: **the conjecture step found real kernel boundaries under
every configuration tried, including the cheapest.** Whatever the loop turns out to be worth, that is
not what is in question.
