# CREATIVITY-ARMS-1: the Blueprint's decisive comparison, on kernel boundaries

A pre-registration. Written and committed before any arm was run.

## What is being asked

Not "does mini's loop beat a reader" — that was the wrong question, asked of the wrong thing. The
Blueprint asks whether a model can **change the organisation used on the next task**, and says the
core product must not be a transcript. `docs/mini/PIPELINE_MATH.md` T-A shows the only pair of arms
that tests it.

The find is a **T1 witness**: a pair of replies the rule as written requires a check to separate, on
which the check answers the same. Nothing downstream of the check can recover the difference,
because it is not in the answer. Over-sensitivity — the check separating what the rule says should
agree — is counted apart, because no impossibility follows from it.

## What is already known, measured before any model call

The mechanical enumeration baseline ran first, at zero model calls, over every function reachable by
import and a fixed set of fourteen reply-shaped seed texts.

- **66** functions are reachable; **6006** executions.
- **4795 (80%) raise.** Most of this harness's one-string functions are not about replies at all.
- **460 collapses**, over **8** distinct functions, and **0** of them quote any rule, because the
  enumerator writes no prose.
- Filtering further: 14 functions are live on two or more seeds, 10 of those are non-constant, and
  **6 of those carry a docstring**. **The target space for a T1 witness against a written rule is
  six functions, not sixty-six.**

Two things follow, and both are fixed here rather than discovered later. **Finding a collapse is
worth nothing** — a loop-free enumerator found 460 for free, so the measure cannot be "collapses".
And the widening to sixty-six was largely illusory for this task; the honest denominator is six.

## The measure

`grounded_T1`: a claimed pair where the machine confirms the collapse **and** the conjecture's prose
quotes six or more consecutive words that occur verbatim in that function's own docstring or source.
The enumerator scores **0** on it by construction. It is the one measure on which the model can
contribute something the host cannot do for free.

Reported beside it: executed rows, unrunnable, raw collapses, over-sensitivity, distinct targets,
distinct pairs, and model calls.

## The arms, matched on model calls

| arm | segments | criticism | organisation changes between segments | calls |
|---|---|---|---|---|
| **S** single shot | 1 | no | — | 2 |
| **R** repeated | 6 | no | no | 12 |
| **N** no-return | 4 | **yes** | **no** | 12 |
| **F** full | 4 | **yes** | **yes** | 12 |
| **E** enumeration | — | — | — | **0** |

`N` and `F` are the same machinery, the same segment count, the same stages, the same instructions.
The install map computes the same bytes in both. In `F` those bytes become the next segment's
operative brief; in `N` they are written to `proposed_organisation.txt` and the next segment runs the
original. That is the Evidence Report's no-return control: it "retains the correct new syntax tree in
the experiment's data but does not install it".

Prose first, per the Blueprint: the conjecture carries **no schema**, so a conjecture that cannot be
parsed stays in the record. A separate reading stage — the translator — carries the only schema, and
its reading may be wrong, in which case it is a target rather than a discard.

Nothing in the contract text names a check, a text, or a transformation. A hidden supplied template
explaining the result is the first way the Blueprint says the attribution fails.

## What is predicted, before the run

- **C1 — the experiment.** `F` produces more `grounded_T1` than `N` at equal calls. **If it does
  not, the return path buys nothing**, serialisation is idle on this task, and mini's reason for
  existing is unsupported by the one comparison built to test it.
- **C2 — the floor.** Some model arm produces `grounded_T1 > 0`. If every model arm scores zero
  while the enumerator produced 460 collapses for free, the model contributed nothing the host does
  not already do, and **mini is out on this task** regardless of C1.
- **C3.** `F` reaches more distinct targets than `N`. The carry names what has been tried; if the
  model uses it, coverage moves.
- **C4.** `R` produces more than `S` per call, so that repetition is doing something before any loop
  is credited with it.

**C2 gates C1.** A difference between `N` and `F` in a measure that is zero everywhere is not a
result.

## What this cannot settle, and the honest risk

Six targets, one model, one seed vocabulary, one budget, four segments. Relative novelty is
trivially satisfied — the contract names nothing, so every target reached is novel relative to the
initial organisation — and is therefore **not** a discriminating measure here; it is reported and
not leaned on. Nothing here is `Origin`.

The risk worth stating: the install map makes the brief **longer** each segment. If the model does
worse with a longer brief than with a clean one, `F` loses to `N` for a reason that has nothing to
do with the return path being useless, and the arms cannot tell those apart. Segment-by-segment
counts are recorded so that at least the shape of any decline is visible.

## Amendment 1, after v1 was stopped: two machinery breaks, neither of them the arms

v1 ran ten of fifteen segments and was stopped. Its records are kept at
`forge/mini/runs/creativity-v1-broken/`. Nothing in it is read as a result, because two defects
meant it was measuring the machinery and not the arms.

**Break 1 — the translator wrote an artifact identifier where the function's path belonged.** Nine
of eleven executions died with `MINI_KERNEL_UNKNOWN: no kernel 'd5f9cd6096f01e80'`. The reading
stage sees conjectures rendered as `[<16 hex>] (mini.conjecture.v1)`, and the instruction asked for
`{"kernel": "<id>"}`. Asked for an id with an id in front of it, the model supplied that one. **The
ambiguity is mine**: "id" named two different things in the same context. The instruction now says
the field is the function's full dotted import path, gives an example, and says in as many words
that it is never the bracketed hexadecimal identifier beside an artifact.

**Break 2 — a segment that died was stepped over in silence.** Three segments ended at their first
stage without reaching `RUN_ENDED`. The runner moved to the next index regardless, so `F/s01`
produced nothing and `F/s02`'s carry therefore held only `s00`'s single row: `F/s01` and `F/s02`
carried byte-identical briefs. **The arm whose whole point is accumulation did not accumulate.** The
runner now checks `RUN_ENDED`, retries once, and says loudly when a segment dies twice, and the call
timeout is raised.

**Not amended: the arity bound.** The open resolver admits functions of one string, and `W1` — the
one hand-verified find so far — is about `refusal_phrase_in`, which takes two. Widening now would
change every arm's numbers after evidence, so it stands, `grounded_T1` is known to undercount, and
`W1` is reported beside it. Worth saying plainly: widening would most help **S**, the arm with no
loop, which is the arm arguing *against* mini's reason for existing. Leaving it alone is not
self-serving in either direction.

## The block, read

Fifteen segments, all reaching `RUN_ENDED`. Read twice: by the pre-registered mechanical measure,
and by the post-hoc verifier that binds a declared second argument and relocates a function named in
the wrong module. The verifier is the honest reading — the live executor refused nearly everything
for reasons that have nothing to do with whether a claim is true.

| arm | calls | claims | executable | **verified T1 witnesses** | distinct targets | per call |
|---|---|---|---|---|---|---|
| **S** single shot | 2 | 1 | 1 | **1** | 1 | **0.50** |
| **R** repeated | 12 | 6 | 4 | **4** | **2** | 0.33 |
| **N** no-return | 12 | 4 | 2 | **2** | 1 | 0.17 |
| **F** full | 12 | 4 | 2 | **2** | 1 | 0.17 |
| **E** enumeration | 0 | — | 1211 | 460 collapses, **0 grounded** | 8 | — |

- **C1 fails.** `F` and `N` are equal at two apiece. **The return path produced no difference in the
  measure it exists for.**
- **C2 holds.** Every model arm produced verified T1 witnesses; the enumerator produced 460
  collapses and grounded none. The model contributes the reading, exactly as the baseline predicted.
- **C3 fails.** `F` and `N` each reached one distinct target — and *different* ones. `F` stayed on
  `refusal_phrase_in` for all four segments; `N` stayed on `recover_json_object`.
- **C4 fails.** `S` yields 0.50 witnesses per call, `R` 0.33, `N` and `F` 0.17. **Adding the loop
  halved the yield; adding the return path changed nothing.**

Only `R` — no criticism, no carry — reached both targets. But at four draws apiece, one arm holding
one target is within chance if the target is near-evenly drawn, so **the locking is not claimed**;
what is claimed is the equality of `F` and `N`, which is the pre-registered comparison.

The union over every model arm is **two** distinct targets of the six eligible.

## Extension 1, declared before it runs

`C1` came out null on four draws a side. A null at that size is thin, so the decisive pair is
extended by four segments each — same manifests, same install map, same everything — to sixteen
total draws across `N` and `F`. Nothing else changes and no other arm is extended: this is more of
the same comparison, not a new one, and it is declared here before it is run so that the enlarged
numbers cannot be read as a fresh block chosen after seeing the first.

**If `F` and `N` remain within one witness of each other at eight draws a side, C1 is settled null**
for this task, this model and this budget.

## The extension, and why its null cannot be read as the answer

Eight draws a side. **`F` 4 verified witnesses, `N` 4.** The pre-registered criterion — within one
witness at eight a side — is met, so C1 is null *as measured*.

| arm | calls | verified T1 | per call | distinct targets |
|---|---|---|---|---|
| **S** | 2 | 1 | **0.50** | 1 |
| **R** | 12 | 4 | 0.33 | 2 |
| **N** | 24 | 4 | 0.17 | 1 |
| **F** | 24 | 4 | 0.17 | 2 |

Twelve distinct witnesses across the block, over **two** targets of the six eligible. `F` and `N`
share none of their witnesses, which at these numbers says only that the pairs differ, not that the
arms do.

**And then the number that disqualifies the reading.** What did the criticism stages actually see?

| arm | `unrunnable` rows the loop read | rows carrying a result |
|---|---|---|
| **N** | **7** | 1 |
| **F** | **6** | 2 |

The loop was fed refusals. Nearly every criticism stage had nothing to criticise but machinery
failure, and the install map duly carried "the check answered unrunnable" into the next brief. **The
return path was not tested; it was starved**, by the same arity bound and wrong-module naming that
made `grounded_T1` read zero for arms that found real boundaries.

So C1's null does not support "the return path buys nothing". It supports "the return path was never
given anything to return", and the cause is this block's executor, not its arms. Following
DeepReason's own rule that *undetermined is a legitimate and frequent verdict*, the return path is
**undetermined here**, and the block that would settle it is the one that feeds the loop results
instead of refusals.

What does survive without qualification is the part that never depended on the executor: **the
conjecture step produces real kernel boundaries**, verified by hand, at the best rate per call in
the block, in the arm with no loop at all.

## Extension 2, declared before it runs: feed the loop results

The starved records are kept at `forge/mini/runs/creativity-starved/`. The live executor now does
what the post-hoc verifier did — binds a declared second argument, and relocates a function named in
the wrong module — so a conjecture the machinery would have refused becomes a row the criticism
stage can read. Both changes are in `openkernels.py` with tests, and both apply to every arm
identically.

`N` and `F` are rerun at eight segments each. Nothing else changes: same manifests, same install
map, same contract, same model, same budget.

**This is the test C1 was meant to be.** If `F` and `N` come out within one witness of each other
again, now that the loop is reading results rather than refusals, **the return path is out** for
this task, model and budget. If `F` pulls ahead, serialisation is doing the thing mini exists for
and the earlier null was the starvation.

## The defect the operator found: commitments are written and not read

Every kind in this block takes `commitment_call: two`, so every seat is asked twice and every
artifact carries a commitment. Where each one goes:

| artifact | commitment | who sees it |
|---|---|---|
| conjecture | prose, the claim itself | **nobody** — the `conj` port renders `list_bodies` |
| reading | `{"kernel", "expect"}` | the executor, and only the executor |
| execution | `{"executions": […]}` | critic and verdict |
| criticism | prose, what the next conjecture will do | **nobody** — `crits` is declared and no kind consumes it |
| verdict | `{"verdicts": […]}` | nobody; terminal |

**Three of five commitment streams are dead ends**, and the critic has no port on `reads`.

This contradicts T-D of `PIPELINE_MATH.md` in the same block that argued it. The point of putting
the schema on a separate reading, downstream of the prose, was that a wrong reading survives in the
record as a **target**: the disagreement between what the conjecture said and what the translator
made of it is itself a finding. The critic was given no way to see the reading, so that
disagreement could never be raised.

It bites on this block's dominant failure. The readings named the wrong module repeatedly —
`records.refusal_phrase_in` for a function that lives in `oracle` — and **the critic was
structurally incapable of noticing**, because the only place that name appears is the reading's
commitment, which it cannot see.

Mini has a citation mechanism (`check_citations`, and `citations` among the template submission
fields), but it is wired for evidence blocks rather than artifacts, and this manifest uses none of
it.

**What follows.** `F` finished at eight segments and `N` was still running when this was found, so
the pair is left to finish: both arms are blind in the same way, which keeps the comparison
internally valid and makes it a comparison between two crippled loops. The repair is a **wiring**
change with the artifact kinds untouched — the critic gains the `reads` port and is asked to attack
the commitment it finds there — and it is run as a declared third condition rather than folded into
`F`, so that what the wiring buys is measured rather than assumed.

## Arm W, declared before it runs: the same machine, wired so the commitment can be attacked

`W` is `F` with two wires moved and nothing else:

1. the criticism kind gains a `reads` port, so the critic sees the reading — the structured
   commitment a translator made of the conjecture's prose;
2. the `conj` port renders `list_bodies_and_commitments` instead of `list_bodies`, so the
   conjecture's own commitment is visible beside its prose.

Verified against `F`'s manifest: **the same kinds, the same `commitment_call` on every one, the same
install map, the same contract, the same budget.** Only ports and the critic's instruction move. The
instruction gains one paragraph telling the critic to name the reading's artifact id, quote the
conjecture's words it claims to render, and say **which of the two is wrong** when they disagree.

This is the operator's claim put to a test: *the way artifacts are wired up matters more than which
artifact types exist*. `F` against `W` holds the types fixed and moves the wiring.

- **C5.** `W` produces more verified T1 witnesses than `F` at equal calls.
- **C6.** `W`'s criticisms actually use the new port: their text names a reading's artifact id.
  Mechanically checkable, and if it fails the wiring was added and not used — the arm then says
  nothing about wiring and everything about the instruction.
- **C7 — the sharp one.** The rate of readings that name the wrong module or a function that does
  not exist **falls across `W`'s segments** and does not fall across `F`'s. That is the specific
  error the blind critic could not see, and it is the one the new wire exposes.

C6 gates C5 and C7: a wire nothing reads is not a wiring change.

## All five arms, read

| arm | calls | distinct verified T1 | per call | targets |
|---|---|---|---|---|
| **S** single shot | 2 | 1 | **0.50** | 1 |
| **R** repeated, no loop | 12 | 4 | 0.33 | 2 |
| **N** loop, no return | 24 | 3 | 0.12 | 1 |
| **F** loop + return, blind critic | 24 | 3 | 0.12 | 1 |
| **W** loop + return, critic sees the reading | 24 | **7** | 0.29 | 2 |
| **E** enumeration | 0 | 460 collapses, **0 grounded** | — | 8 |

- **C1 fails, twice.** `F` = `N` at three apiece, once starved and once fed. **The return path alone
  buys nothing.**
- **C5 holds, strongly.** `W` more than doubles `F` at identical calls with **only wiring changed** —
  same kinds, same `commitment_call` on each, same install map, same contract. It also eliminated
  both proposal defects outright: **zero** claims giving two identical texts (against `F`'s two,
  `N`'s three) and **zero** naming a function that does not exist (against `F`'s two). Six of `W`'s
  seven witnesses were found by no other arm.
- **C6 fails.** None of `W`'s eight criticisms names a reading's artifact id, though the instruction
  asks. The mechanism is **being shown**, not citing, and the pre-registered gate applies.
- **C7 fails.** `W` relocated eight of eight against `F`'s six: misnaming got *worse*. The wiring
  fixed the **pair**, not the **name**.
- **And the comparison that decides the loop:** `W` at 0.29 per call does not beat `R` at 0.33 per
  call, and both reach the same two targets. **The best-wired loop draws level with no loop at all.**

## Arm A, declared before it runs: criticism that can land

Every arm above had **zero attack supply**. Criticism produced prose that the next stage was shown,
and "a bare verdict is never an edge". Declaring the loop out on that evidence would repeat the
starvation error in a new place.

`A` is `W` plus the smallest machinery that makes a criticism land:

1. the critic's commitment names **the artifact it attacks** and **the ground** it stands on, from a
   closed set carrying `cannot-tell` as an escape road that mints no attack;
2. a machine seat resolves that name against the record — a name matching nothing, or more than one
   thing, resolves to no attack — and computes status from the relation, refuted iff some attacker
   of it is not itself refuted;
3. the install map carries **what was refuted**, not only what was said.

`W` against `A` is therefore: the same wiring, the same kinds, the same budget, and the difference
is whether criticism *does* anything.

- **C8.** `A` produces landed attacks at all — at least one criticism naming a target that resolves.
  If none does, the machinery is unused and `A` says nothing, exactly as C6 gated C5.
- **C9 — the experiment.** `A` produces more distinct verified T1 witnesses than `W`. If it does
  not, then criticism that lands buys nothing over criticism that is merely read, and **the loop is
  out on the strongest version of itself this repository can build.**
- **C10.** At least one `cannot-tell` is used. A closed ground enum with an escape road that nobody
  takes is a measurement that the escape was unnecessary, not that it was absent.
