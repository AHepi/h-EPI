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

## Amendments, and one false claim about them

Five changes were made after this document was first committed. Each is listed with what it cost,
because a pre-registration that is quietly edited is not one.

1. **The source a seat is shown now carries addresses** (ERRATA C14). It showed eight function
   bodies with no module on any of them, one of which is mini's own wrapper rather than the harness
   under test, while the instruction asks for a full dotted path. Each body now says which of three
   it is: nameable, nameable but not runnable on one string with the reason, or not the harness's at
   all. **Three of the eight cannot carry a runnable claim**; the other five can,
   `refusal_phrase_in` among them because a binding for its second argument is declared in
   `openkernels.py`.
2. **`LOOP_STARVED` is fatal only where a segment had more than one row**, and the driver stops an
   arm after three consecutive segments that executed nothing. One claim naming a function the
   harness does not have is the model being wrong, which is a result; stopping an arm on it is the
   alarm doing the thing alarms exist to stop.
3. **A transport failure is retried rather than ending an arm.** A half-written root is set aside and
   the segment run again, up to three times, with a pause of 0, 20 and 90 seconds before each — the
   local egress proxy restarts on a different port, and three retries spent in three seconds ride out
   nothing.
4. **The carried brief keeps the last segment's refutations, not every segment's** (ERRATA C15), and
   is held to a declared ceiling of 7800 characters, dropping the oldest attempts first, identically
   on every arm. Only arm `A` produces refutations, so only arm `A`'s brief grew without bound —
   8075 characters at segment 13 against `W`'s 5530 — and it stopped at segment 14 on the manifest
   schema's 8192 cap. **"The attacks land" and "the brief is half again as long" were one
   treatment**, which would have confounded `W` → `A`, the block's own experiment, whichever way it
   fell.
5. **The runnable count in amendment 1 was first written as four of eight, and is three.** It was
   asserted from reading the annotation list rather than from running it.

Nothing in the measures, the arms, the predictions or the manifests changed under any of these.

Thirty-four segments were run before amendment 1 and are **set aside, not counted**, at
`forge/mini/runs/creativity-2-aborted/round-1/`. Fifteen segments of arm `A` were run before
amendment 4 and are set aside at `.../round-2/`; regenerating every brief in the block under the
repaired map leaves `R`, `F` and `W` **byte-identical** (16/16, 16/16, 15/15) and changes `A` from
segment 2 on, which is why one arm was re-run and not four.

**The false claim.** The commit that made amendments 1 to 3 says in its message *"The
pre-registration carries the amendment."* It did not. Both edits were written with a text
replacement anchored on a heading this document does not have, so both silently did nothing and
nobody looked. This section is the first time any of it was actually recorded, and it is recorded
here rather than in the commit that claimed it, because published history is not rewritten.

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

Four arms, sixteen segments each, three repeats. **864 model calls before any refusal**, and a
refused submission is a call too.

Calls, not stages: the conjecture and the criticism are each `commitment_call: two` and cost two
calls; the reading is `single` and costs one. Block 1 counted stages and called them calls, so every
per-call figure in it was low by between 1.7 and 2.0 (ERRATA A5). The corrected block-1 figures are
in that entry; they are not compared with anything here.

| arm | segments | criticism | critic sees | install map | adjudication | calls/segment | calls ×3 |
|---|---|---|---|---|---|---|---|
| **R** repeated | 16 | no | — | no | no | 3 | 144 |
| **F** full | 16 | yes | source, conj, execs | **yes** | no | 5 | 240 |
| **W** wired | 16 | yes | + **reads** | yes | no | 5 | 240 |
| **A** adjudicated | 16 | yes | + reads | yes | **yes** | 5 | 240 |

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

## The nine repairs, each answering a numbered erratum

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
8. **A declared shape for the translator's own three texts** (C13). Nine of thirty-nine block-1
   readings returned `kernel` and `expect` and **no pair of texts at all**, and nothing could see it:
   mini's format layer read `body` and `commitments` and a kind's own optional fields were outside it
   entirely. Not evenly spread — `N` 4 of 8, `W` **0 of 8** — so it ran under every arm difference in
   the block, including the positive one. `format.fields` now declares a shape for a kind's own
   fields, a missing one is a refusal with the shape rendered rather than a skip, and
   **ALM-TRANSLATOR-DROPPED-THE-TEXTS** names the mode in a finished segment.
9. **Calls counted as calls** (A5), everywhere: in the budget, in the reading, and in every figure
   reported per call. The reader counts each model stage entered at its own commitment cost and adds
   every refusal, from the record.

**Item 8 was found by item 7's machinery, on the first live segment of this block.** The alarm fired
after four calls, the arm stopped, and the mode was traced back through block 1. That aborted
segment is kept, outside the block, at `forge/mini/runs/creativity-2-aborted/`.

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
