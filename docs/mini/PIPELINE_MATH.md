# The mini math, rebuilt around what mini is for

The earlier `ARCHITECTURE_SPACE.md` counted acyclic orientations of one fixed wiring. It assumed
three things that are not true of mini, and each assumption removed the thing mini exists to do.

1. It pinned a terminal stage, so it counted `(n-1)!` orderings where mini admits `n!`.
2. It held the artifact kinds fixed, so the kinds were not a variable.
3. **It held the wiring fixed for the whole run.** A run is fixed once its config compiles, but the
   *serialisation* of runs is not. Nothing stops segment two being configured from segment one's
   result.

The third is the one that matters, because it is where the Blueprint locates creativity:

> Build a continuing inquiry system in which a language model can propose new representations and
> methods, receive evidence about their consequences, and **change the actual organization used on
> the next task**. Do not make the core product a transcript.

Counting orientations of a frozen graph answers a question about one task. The organisation
changing between tasks is a different object, and this is its mathematics.

## Objects

A **use** is not a content object. Following the Blueprint, a use is `(content, question, premises,
scope)`: which content was applied to which question under which premises. The same conclusion may
have several independent sufficient arguments, and those are separate uses.

A **contract** `κ` is `(target, respect, admitted changes, repair obligations, protected
achievements)`. It is the *interpreted* problem, held separately from the original formulation, and
it is criticisable. A revised contract is a new identified claim; it does not rewrite the original
demand or turn a past failure into a success.

An **organisation** `O` is mini's operative state: the kinds, the stages and their order, the port
edges, the windows, the instruction texts, and the seat assignments. In mini an organisation is
exactly a compilable manifest.

A **segment** is one run: `R = run(O, κ)`, a record.

A **pipeline** is a sequence

```
(O₁, κ₁) → R₁ → (O₂, κ₂) → R₂ → … → (O_m, κ_m) → R_m
```

with two maps carrying information forward:

- the **install map** `ι`, where `O_{i+1} = ι(O_i, R_i)` — the organisation used next,
- the **contract revision** `ρ`, where `κ_{i+1} = ρ(κ_i, R_i)` — the question asked next.

`ι` is the Blueprint's `install`, and `ρ` its `revise_question`. The old math is the case `m = 1`.

## T-A. The return path is the only thing a pipeline has that repetition does not

**Claim.** If `ι` and `ρ` are both constant — that is, they ignore `R_i` — then a pipeline of `m`
segments is exactly `m` independent runs of a fixed organisation on a fixed contract.

**Proof.** Immediate: with `ι(O, R) = O'` and `ρ(κ, R) = κ'` independent of `R`, no function of
`R_i` appears in the definition of segment `i+1`. The segments share no information, so the joint
distribution of `(R₁,…,R_m)` is a product. ∎

**Corollary, and it is the whole experimental design.** Any advantage a pipeline shows over equal-
budget repetition is attributable to `ι` or `ρ` and to nothing else about serialisation. So the
control for a pipeline is not "fewer runs" or "one architecture": it is **the same pipeline with the
return path cut**. This is the Blueprint's no-return control, which "retains the correct new syntax
tree in the experiment's data but does not install it", and whose failure "distinguishes producing a
repair artifact from actually repairing the use path."

Mini has never run that control. Every earlier block varied what a single organisation was shown.

## T-B. What `ι` can reach, exactly

**Claim.** In mini, `ι` can produce any compilable manifest over the registered vocabulary, and
nothing outside it.

**Proof.** A manifest is data: kinds, stages, ports, windows, instructions and seat assignments are
all fields, so a map from a record to a manifest can set any of them. A stage naming a machine seat
compiles only if that seat is in the registry, and a seat is a function registered in code at import
time. A record cannot add one. ∎

This is the honest bound on mini's creativity, and it is the Blueprint's own:

> The designer supplied the task, candidate primitives, ticket registers, representation-extension
> rule, and exact reference checker. … The mechanism did not invent comparison.

So mini can **reorganise**; it cannot **invent a seat**. Whether reorganisation is enough to find a
kernel boundary is an empirical question, not a theorem, and it is the question worth running.

## T-C. Nothing pins the terminal stage, and a cycle need not end in one verdict

**Claim.** The orderings of `n` stages that mini admits number `n!`, not `(n-1)!`, and a cycle may
carry any number of verdict-kind stages including none.

**Proof.** The compiler requires an end stage marker, not a distinguished kind before it; the
terminal marker carries no kind at all. Nothing in the schema limits the multiplicity of any kind in
a stage list. ∎

The earlier count of 36 architectures was therefore a count over one manifest's convention. This
matters because a single terminal verdict forces every cycle's output into one commitment, which is
the shape the Blueprint warns against: several independent sufficient arguments for the same
conclusion are separate uses, and collapsing them loses exactly the structure criticism operates on.

## T-D. Where to put the schema so a wrong answer survives to be criticised

The Blueprint is explicit about order:

> Raw prose enters inquiry before any semantic classification. A translator can propose structured
> fields, but its interpretation is another fallible content object.

**Claim.** Placing a strict schema on the conjecture and placing it on a downstream interpretation
of the conjecture are not equivalent, and they differ in what happens to a wrong answer.

**Argument.** A schema on the conjecture is enforced by the runner: a reply that misses it is a
format failure, retried and then fatal, and the content is discarded before anything can read it. A
schema on a *separate* interpreting artifact leaves the conjecture in the record as prose. The
interpretation may then be wrong, and being wrong it is a target: it can be challenged, and the
disagreement between the prose and its interpretation is itself a finding. ∎

This is the formal version of "a false conjecture or commitment is not a bad thing". Falsity is only
informative where the false thing survives in the record. A strict form deletes it.

## T-E. What a commitment buys, stated so it can be tested

A commitment is a statement of what would make the conjecture wrong. Its value is not that it is
usually right. Following the Blueprint's diagnosis rules, its value is that it creates a **decidable
disagreement between two things the machine holds**: the commitment, and what the machine observes.

**Claim.** A conjecture with no commitment admits no mechanical disagreement; a conjecture with a
commitment admits one per commitment. So the number of places a run can be mechanically wrong — its
attack surface — is the number of commitments, not the number of conjectures.

This gives the measure. Not "how often was the model right", but **how many decidable disagreements
did the run produce**, and of those, how many survived to change the next organisation. Correctness
is not the target; usable disagreement is.

## The conditions this mathematics implies

The Blueprint names the comparison, and T-A says which pair of arms is decisive:

| arm | loop | criticism returned | organisation changes |
|---|---|---|---|
| **S** single shot | no | no | no |
| **R** repeated, equal budget | no | no | no |
| **N** no-return | yes | yes | **no** |
| **F** full | yes | yes | **yes** |

`S` against `R` measures what repetition buys. `R` against `N` measures what the loop buys.
**`N` against `F` measures what the return path buys, and that is the only pair that tests mini's
reason for existing.** A mechanical enumeration baseline and a supplied-solution control sit beneath
all four, per the Blueprint, to show what the host contributes without the model.

Costs are recorded per arm — calls, tokens, wall time — and a timeout is not scored as a refutation.

## T-F. What a find must look like, taken from T1

The Blueprint says what a real defect looks like, and it is sharper than "the answer changed when I
did not expect it to":

> A pair of situations with the same complete available view but incompatible required responses
> proves a stronger failure: every decision rule over that view fails.

Translated to a check `k` over reply texts: a **T1 witness** is a pair `(x, y)` where the rule as
written requires `k` to separate them and `k(x) = k(y)`. Nothing downstream of `k` can recover the
distinction, because it is not in `k`'s output at all. That is a boundary of the check.

The opposite direction — `k(x) ≠ k(y)` where the rule says they should agree — is a different
defect. It is over-sensitivity, not lost information, and no impossibility follows from it. Both are
worth recording; **only the first instantiates T1**, and counting them together hides the one that
carries a proof.

## T-G. Novelty is decidable here, and `New` is not needed

The blocking problem in every earlier attempt was that `New` is unestablishable: nobody can show a
proposal was absent from pretraining. The Blueprint sidesteps it:

> Report novelty relative to the initial working organization separately from historical or
> training-set novelty.

**Relative novelty is decidable.** The initial organisation `O₁` is a manifest: a finite list of
kinds, stages, instructions, and a finite set of things it names. A find is novel relative to `O₁`
exactly when it is not in that list. No claim about the model's training is required, and none is
made. This is the measure the experiments below use, and it is stated as the weak thing it is.

## The failure conditions, adopted verbatim as stopping rules

The Blueprint names four ways the attribution fails, and each is a condition to check rather than a
caveat to recite:

1. **a hidden supplied template explains the result** — so the instruction must not name the find;
2. **the evaluator does all the constructive work** — so the mechanical enumeration baseline must be
   run, and if it matches the model arms the model contributed nothing;
3. **the explanation is causally disconnected** — so the no-return arm must be run, and if the full
   arm does not beat it, the criticism never reached the operative state;
4. **the repair fails its unchanged obligations** — so what a segment already established must still
   hold after the organisation changes.

A timeout is not scored as a refutation.

## What DeepReason's compiled notes add, and where they bite here

Read from `AHepi/DeepReason` (read-only; that repository's rule forbids running its instruments in
a review window). Its notes are marked external and unverified by its own instruments; they are
design intelligence, not evidence, and are used that way.

**A required field with no escape road manufactures an answer.**
`docs/RESEARCH_STRUCTURED_OUTPUT_COERCION_2026-08-22.md` reports the same model fabricating at
**0–2% in prose and 100% under a required-field schema**, "because the format removed honesty's
slot", and states that prompt-level instructions not to fabricate are **voided** by a required
schema: "enforcement lives in the schema's escape road, not the prompt".

This names the mechanism behind Break 1 of CREATIVITY-ARMS-1 exactly. The reading stage had a
required `kernel` field, no way to say *the prose names none*, and an artifact identifier sitting in
its context — so it emitted that. Clarifying the prompt fixed the symptom here (five of five
path-shaped, against two of eleven), and the note says why that fix is the weaker one: **the field
still has no escape value**. T-D said put the schema downstream of the prose; this adds that the
schema itself must admit "I cannot tell".

It also independently supports the prose-first shape: "separate deliberation from emission… reason
free, serialize/extract in a second call", with "keep emission schemas light".

**Presence is not use.** The same note: "written state is not used state (presence decodes at 1.000
even when causally inert)." This is the precise hazard of arm `F`. Carrying the previous segment's
criticism in the brief does not mean the segment used it, and a difference between `N` and `F`
could be either. It is the reason T-A's control is necessary and the reason a null result there is
readable.

**A settled endpoint is not evidence criticism worked.**
`docs/RESEARCH_CONVERGENCE_VS_ATTRACTOR_2026-08-28.md` is binding on any reading of narrowing:
"presume observed narrowing generator-intrinsic until control arms say otherwise", "nothing is
interpretable without the no-criticism control arm and the stochastic floor", and "undetermined is a
legitimate and frequent verdict".

The design meets the first two by accident rather than design, and it is worth saying which:
`R` is the no-criticism arm, and **`N` is the stochastic floor** — not installing means its four
segments run a byte-identical brief, so they are four independent draws of one organisation. `F`'s
four segments are four draws of a changing one. The floor is therefore inside the contrast rather
than beside it, which is what makes the contrast readable at this size at all.
