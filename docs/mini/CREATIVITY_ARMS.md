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
