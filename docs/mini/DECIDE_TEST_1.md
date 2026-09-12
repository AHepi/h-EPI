# DECIDE-TEST-1 — can the small model decide, with no larger model in the room

Pre-registered. Committed before any record of this block exists; the commit that adds this file adds
no run under `forge/mini/runs/decide-1/`. Anything added to this file after the first record says so
in its own heading.

## Why this block exists

Everything mini has been run for so far measures **output**: how many finds a loop produces, how many
ways of breaking a check they represent, what an addition to the loop costs. Nothing has ever asked
the model to **decide** — and mini's own unattended operation does not either. `tools/mini_campaign.py`
reads a round's records and picks the next round by five fixed rules, each naming the register entry it
came from (`creib.forge.mini.campaign`). The machine decides; the model writes. `docs/mini/AUTONOMY.md`
says as much in its own table.

So the question this block is for has not been put to a model once: **without a larger model present,
can a small model decide when to add something and what to do next?**

## What is scored, and what cannot be

Two decisions were asked for. Only one of them can be scored on this task, and saying why is part of
the pre-registration rather than a result.

**What to do next — scored.** Three checks of the harness differ in measured yield, so choosing among
them has a right answer that a grid of runs establishes. That is this block's scored decision.

**What to add — asked, and not scored, and the reason is a measurement.** Block 2 ran four arms
differing in what the loop carries: rules only, plus an attacking seat and a carried brief, plus the
readings port, plus the warrant schema. On five measures the four arms come out in five different
orders, and the spread within one arm across three repeats is 2 to 10 collapse classes
(`docs/mini/CREATIVITY_ARMS_2.md`, ERRATA C23). The additions did not differ enough to be worth
deciding between, so a choice among them has no measured better answer and scoring one would be
scoring noise. `CLAUDE.md`: *a control whose corruption leaves the reference output unchanged is
refused when the plan is built.* The same refusal applies here.

The model is asked anyway, three times — once for the plain loop, once for the loop with the first step
taken, once with the first two — with what the plain loop cost and produced across this block's own grid
in front of it, and with what each further step would cost in model calls. Three states, eight briefs
each, **24 calls**. There is no key, so what is reported is what it chose, and whether the choice moved
with the form and with the content. The first step is shown as the two changes it was, because block 2
made the attacking seat and the carried brief together and no run separates them: a brief that tidied
that into one change would be describing an experiment nobody ran.

## The working set

Three checks, chosen because `creib.forge.mini.rule_readings` implements each one's documented rule
apart from its body, so every outcome in this block is adjudicated by machine and no model's word is
taken for whether a find is real:

- `creib.forge.conformance.oracle.recover_json_object`
- `creib.forge.conformance.oracle.refusal_phrase_in`
- `creib.forge.conformance.oracle._plain_quotes`

A find is **real** when it holds up under every reading of its check's rule, and the count of real
**collapse classes** — distinct ways of making the check answer the same where its rule requires a
move — is the outcome measure throughout.

## The grid: where the right answer comes from

For each of the three checks, **six segments** of the plain loop (conjecture, reading, execution), with
the check **named by the machine** so the model is not choosing. Three checks, eighteen segments, three
model calls each: **54 calls**. What the grid yields per check is the ground truth. Nothing about the
right answer is taken from block 2; block 2 only says what to expect, and the grid may contradict it.

Expected from block 2, written down so the grid can refute it: `recover_json_object` yields real
classes, `refusal_phrase_in` yields none under the reading its own code follows, `_plain_quotes` yields
none. If the grid disagrees, the grid is what scores the decisions.

## The decision points

Twelve. A point is a state the grid actually passed through: after *s* segments on check *C*, with
what has been spent and found on all three checks as at that moment. `s` is 1, 2, 4 and 6 for each of
the three checks. The three grids are interleaved in a fixed order so that a state's other-check
figures are real rather than invented.

At each point the machine enumerates **four options** and the model chooses one:

- `stay` — another segment on the check now being worked
- `move-to-<other>` — the first other check, named
- `move-to-<other>` — the second other check, named
- `stop` — this search has nothing left to find

The reply is one line of JSON: `{"choice": "<one option id>", "because": "<one sentence>"}`.

**How a choice is scored.** From the grid, each option's **remaining yield**: for `stay`, the real
classes the grid found on that check in its segments after *s*; for a `move`, the real classes the grid
found on that check across all six of its segments. The right option is the one with the most
remaining yield. `stop` is right when every option's remaining yield is zero. Where options tie, the
tie is recorded and a choice of any tied option counts as right.

**Four baselines, all computed from the same grid and costing no calls.**

| baseline | what it is |
|---|---|
| uniform random | the expected hit rate of choosing one of the four options at random |
| always-stay | never move, never stop |
| best fixed option | the single option that would have scored best over all twelve points, in hindsight |
| the model's own modal choice | always choosing whatever the model chose most often |

The last is the one that matters. A model that says `stay` twelve times scores exactly what
always-stay scores, and that is not deciding, however high the number is.

## The eight briefs: form must not move the choice, content must

Each decision point is put eight times, one call each. This is the part taken from the miniReason
repository, whose own words are that *a content-preserving recoding and a content-changing contrast on
an active route are stronger probes than observing that a port was populated*
(`docs/mini/FROM_MINIREASON.md`).

| brief | what changes | what a decider requires |
|---|---|---|
| `plain` | nothing; the canonical stacking | — |
| `repeat` | nothing at all; the same bytes, a second call | the floor: how often the choice moves when nothing did |
| `reordered` | the same blocks stacked in a different order | the choice must not move |
| `reordered-2` | the same blocks in a second different order | the choice must not move |
| `reordered-3` | the same blocks in a third different order | the choice must not move |
| `relabelled` | every check renamed `check_one`, `check_two`, `check_three`, consistently, the shown source included | the choice must not move |
| `contrast` | the figures rewritten so a different option has the most remaining yield | the choice must move |
| `ablated` | the figures removed; task, sources and options remain | the choice must move, or the figures were never read |

**Three reorderings and not one.** The transfer from miniReason is a measure of how much stacking order
moves an answer, and one alternative order gives a single comparison rather than a rate. A brief is
stacked from four blocks -- the task, the checks in full, the figures, the options -- and each
reordering is a different permutation of them. The instruction is last in every brief, because it is the
shape of the reply and not part of the state, and moving it would change two things at once. The three
reorderings are byte-for-byte the same length as `plain`: the same characters, stacked differently. What
is reported is how many distinct choices the four orders produced at each point.

`repeat` is not ceremony. The endpoint is called at temperature zero with a fixed seed, and block 2's
rules-only arm produced a different check on 12 of 45 consecutive segments under a brief that never
changed, so the floor is not zero and has to be measured rather than assumed.

## The campaign-rule comparison

`creib.forge.mini.campaign` decides a round from six numbers by five ordered rules. The rules are
deterministic functions of those numbers, so the right answer is exact and no sampling is involved.

Eight states are enumerated: one that makes each of the five rules fire, one where none fires, and two
where two rules fire, which tests whether the model picks the one the ordering picks. The model is
shown the same six numbers in plain words and the same six options, and asked which one thing to do.
Its answer is compared with the first rule `decide()` fires.

Eight briefs each, as above: **64 calls**. Its briefs have three blocks rather than four, so the three
reorderings permute those three.

**This compares the model with a policy a person wrote, not with a measured optimum.** The five rules
are the five rewrites five rounds of experiments made by hand. Agreement with them is agreement with a
person's judgement about what to do, which is what the question asks for, and it is not evidence that
either the model or the rules chose well.

## The conjectures

Each is refutable by this block's records and none can be confirmed by them.

- **DEC-1.** The model's choice carries no information about which option has the most remaining
  yield: its hit rate over the twelve `plain` points does not exceed the uniform-random baseline.
  *Refuted by at least four more hits than random's expectation over the twelve points.*
- **DEC-2.** The model's choices are its modal choice: its hit rate does not exceed the hit rate of
  always choosing whatever it chose most often. *Refuted when its hit rate exceeds that.*
- **DEC-3.** The choice does not survive a change of form: the three reorderings and the relabelling
  agree with `plain` no more often than `contrast` does. *Refuted when form agreement exceeds contrast
  agreement.*
- **DEC-4.** The choice does not follow the figures: `contrast` agrees with `plain` as often as
  `repeat` does. *Refuted when contrast agreement falls below the repeat floor.*
- **DEC-5.** The figures are not read: `ablated` agrees with `plain` as often as `repeat` does.
  *Refuted when ablated agreement falls below the repeat floor.*
- **DEC-6.** On the campaign's own option set the model agrees with the rule that fired no more often
  than chance. *Refuted by agreement above the uniform-random baseline over the eight states.*

DEC-3, DEC-4 and DEC-5 are the ones worth the calls. A model can be right about `stay` while reading
nothing, because `stay` is right at most points on this task. It cannot be insensitive to form and
sensitive to content while reading nothing.

## What this block does not control, declared before it runs

- **What to add is not scored**, for the reason given above. Only the sensitivity measures apply to it,
  and its `relabelled` brief renames the option ids while leaving every description word for word, so
  what moves is the name and not what the thing does.
- **One model, one endpoint, one temperature, one task.** Nothing here is about models in general, and
  a claim of that shape would have to be written into a pilot's `claims.json` and tested there.
- **The grid is six segments a check.** A check whose yield arrives at segment seven is recorded as
  yielding nothing, and a `move` toward it is scored wrong. The grid's own length is a scope limit on
  every hit rate in this block.
- **`stop` is scored against a grid that also stops.** A `stop` called right at *s* = 6 is right
  relative to six segments of evidence and not in general.
- **Equal ceilings are not equal spending.** A decision call and a segment do not cost the same, so
  every figure is reported in model calls and the two are never added together.
- **Twelve points and eight states are small.** A hit rate over twelve points has a wide interval, and
  the block is designed so that the sensitivity measures, which are 84 paired comparisons rather than
  12, carry the weight.
- **The three checks are not a sample of the harness.** They are the three whose rules are implemented,
  which is a property of this repository's reading and not of the checks.

## Decisions taken while building it, before any record existed

Each of these is part of the pre-registration and not an amendment: the commit that adds this file adds
the code that does them and no run.

**The reply shape puts the answer in the body and nothing inside anything.** The option id is the whole
of the reply's `body` and the reason is the whole of its `commitments`. Asking for a JSON object nested
inside the commitments string is what broke 12 of block 2's 16 escaped readings (ERRATA C21), and there
is no reason to repeat it when the answer is one word. The instruction shows a complete worked reply.

**A reply that misses mini's envelope is re-asked twice.** The shape of a reply is not what this block
measures, so a seat that answers in prose is asked again with the envelope rendered, exactly as block 2
learned to do (ERRATA C13). How often a retry was needed is read out of the records and reported.

**The choice is read by two rules, in order.** The body is the option id after whitespace and backticks
come off; failing that, exactly one id occurs somewhere in the body and no other does. A body naming
two ids names neither, because nothing here will guess which was meant, and it is recorded as naming
none.

**`relabelled` renames the check inside the source as well as in the labels.** A brief that renamed the
labels while the source still said `def recover_json_object` would leave the model its memory of the
name, and then a choice that did not move under relabelling would show nothing about form. The neutral
names are therefore valid identifiers, `check_one` and the rest, and every occurrence of a check's name
in the shown source is replaced, the call `refusal_phrase_in` makes to `_plain_quotes` included.

**DEC-4 is measured only where the contrast changes what the figures indicate.** A contrast that swaps
two checks' figures and leaves the indicated option where it was tests nothing: the figures moved and
what they say did not. `creib.forge.mini.decide.contrast_flips` decides this from the figures alone,
before any reply is read, and `points.json` records it per point.

**The campaign comparison has no `relabelled` brief.** Its options are the changes themselves and its
figures are numbers, so there is no name to make neutral: renaming would have to change the words that
say what an option does, which is content and not form. The brief is the plain one and the pairing is
reported as unavailable rather than as agreement.

**The campaign contrast is a rotation through the declared states.** The first version flipped every
number at once, and seven of the eight contrasts then fired the same rule, so a model that always named
that rule would have looked sensitive to content. Each state's contrast is instead the next declared
state's numbers, which spreads the key across six of the six options by construction.

**One seed, 11, declared in the driver.** The endpoint, its temperature of zero and its seed are written
into every manifest, so what was sent is in the record rather than in a shipped default.

## Amendment A1: three of the twelve points have a key the model cannot see

Made after the block began and before any reply was read. Where it sits on the pre-registration rule
(`CLAUDE.md`: *a conjecture written after the records is a description of them, and the document that
reports it says so*): the limit itself is pre-registered above, in two sentences -- *the grid's own
length is a scope limit on every hit rate in this block*, and *a `stop` called right at s = 6 is right
relative to six segments of evidence and not in general*. What is new is the number and a second
reported figure beside the first. It was computed from the grid, which was complete before the first
decision call was sent, and no reply had been read when it was written, so no reply could have
influenced it. That is not the same as having been pre-registered, and this heading says so.

**What the grid turned out to be.** Six segments each: `recover_json_object` gave five distinct ways of
breaking it, one per segment bar the last; `refusal_phrase_in` gave six finds and not one that survives
the reading of *first* its own code follows, so zero; `_plain_quotes` gave no T1 witness at all. The key
over the twelve points is therefore `stay` at three, `move-to-recover_json_object` at six, and `stop` at
three, and the contrast changes what the figures indicate at every one of the twelve.

**The problem with the three `stop` points.** They are the deepest cut, where every check's segments are
used up, so every option's remaining yield is zero and `stop` is the right answer. But the figures a
model is shown say the opposite: a check with five ways found in six segments looks like one worth
moving to, and the model cannot know the grid has no seventh segment. On those three points a reasonable
reading of the figures is scored wrong, and scoring it wrong is an artefact of how long the grid is.

**What is done about it.** `creib.forge.mini.decide.length_dependent` marks such a point -- nothing left
anywhere, and some check spent to the end of its grid -- and every hit rate is reported twice, over all
twelve points and over the nine whose key does not depend on the grid's length. The baselines differ
between the two, so both sets are given here:

| baseline | over all twelve | over the nine |
|---|---|---|
| uniform random | 0.250 | 0.250 |
| always `stay` | 0.250 | 0.333 |
| always `stop` | 0.250 | 0.000 |
| always `move-to-recover_json_object` (the best fixed option) | 0.500 | 0.667 |

DEC-1 and DEC-2 are read on the nine, because that is the set whose key the figures support, and the
figure over all twelve is reported beside it. Neither figure is chosen after seeing the model's hit
rate: this paragraph is committed before any reply is read.

## The cost

| part | calls |
|---|---|
| the grid | 54 |
| twelve decision points, eight briefs each | 96 |
| three what-to-add states, eight briefs each (not scored) | 24 |
| eight campaign states, eight briefs each | 64 |
| **total, one seed** | **238** |

A second seed on the `plain` briefs only adds 20, and is run only if the first seed's repeat floor is
above zero, because that is the condition under which a second seed says something.

---

# What the block found

238 calls, one seed, all of them in, nothing set aside. Read with
`python tools/mini_decide.py read --runs forge/mini/runs/decide-1`.

## The one-sentence answer

The small model **can** make the decision that is a written rule over measurements, and it is
demonstrably reading the measurements to do it; whether it can make the decision that is a judgement
about where to look next **this block cannot say**, because on that question one call is not a
measurement -- the same brief sent twice scored 0.778 and 0.333.

## The campaign decision: a rule over six numbers, and the model computes it

Eight states, each a set of six numbers on which `creib.forge.mini.campaign` fires one of five ordered
rules or none. The key is what `decide()` returns, so it is exact and no sampling is in it. The chance
rate over six options is 0.167.

| brief | agrees with the rule that fired |
|---|---|
| `plain` | 5 of 8 = **0.625** |
| `repeat` (identical bytes) | 5 of 8 = **0.625** |
| `reordered` | 4 of 8 = 0.500 |
| `reordered-2` | 6 of 8 = 0.750 |
| `reordered-3` | 5 of 8 = 0.625 |
| `relabelled` (also identical bytes here) | 6 of 8 = 0.750 |
| `contrast`, scored against the rule **its own** numbers fire | 5 of 8 = **0.625** |
| `ablated`, the numbers removed | 1 of 8 = **0.125** |

Read the three bold rows together. Sending the same bytes twice gives the same score. Changing the
numbers so a different rule fires gives the same score **against the new rule** -- so the model is
not pattern-matching an option list, it is computing over the numbers. Removing the numbers drops it
to 0.125, below the chance rate of 0.167. That is a decision being made from the state, not beside it.

Agreement between briefs says the same thing from the other side: `repeat` 8 of 8, `reordered-3` 8 of
8, `reordered` 7 of 8, `reordered-2` 7 of 8, `relabelled` 7 of 8 -- and `contrast` **0 of 8** and
`ablated` **0 of 8**. Stable under every change of form, moved by every change of content, with no
overlap between the two. Nothing in this family is ambiguous.

**DEC-6 is refuted**: 0.625 against a uniform-random baseline of 0.167, and the figure is unchanged
when the brief is resent.

What the three misses were, because they are not all the same kind of miss. On `none-fires`, where no
rule fires, it named `space-exhausted`, which does not fire: a plain error. On the two states where
**two** rules fire, it named the other one -- `one-change-per-pair` where the machine's ordering takes
`real-line-breaks`, and `real-line-breaks` where the ordering takes `fields-form`. Both of those name a
rule that genuinely fires on those numbers. So 5 of 8 match the machine exactly and 7 of 8 name a rule
the numbers warrant; what it does not reproduce is the machine's own precedence between two warranted
rules, which is a convention written into the rule order and not a fact about the numbers.

## The search decision: one call is not a measurement

Twelve points, four options each, the key from the grid. Three of the twelve have a key the figures
cannot reach (Amendment A1), so every figure is given over all twelve and over the nine.

| brief | hit rate over 12 | over the 9 |
|---|---|---|
| `plain` (**the pre-registered reading**) | 7/12 = 0.583 | 7/9 = **0.778** |
| `repeat` -- byte-identical to `plain` | 3/12 = 0.250 | 3/9 = **0.333** |
| `relabelled` | 7/12 = 0.583 | 7/9 = 0.778 |
| `reordered` | 3/12 = 0.250 | 3/9 = 0.333 |
| `reordered-2` | 3/12 = 0.250 | 3/9 = 0.333 |
| `reordered-3` | 2/12 = 0.167 | 1/9 = 0.111 |
| `contrast` | 3/12 = 0.250 | 3/9 = 0.333 |
| `ablated` | 1/12 = 0.083 | 1/9 = 0.111 |
| uniform random | 0.250 | 0.250 |
| best fixed option, in hindsight | 0.500 | 0.667 |

**The pre-registered reading and the byte-identical resend of it disagree by a factor of two.** The
pre-registration says the hit rate is read on `plain`; on `plain` it is 0.778, comfortably above the
0.250 chance rate and above the 0.667 a hindsight-optimal constant policy would get. On `repeat` --
the same bytes, the same endpoint, temperature zero, seed 11 -- it is 0.333, which is chance.

So, stated the way it has to be stated: **DEC-1's refuting condition is met on the brief the
pre-registration nominated and not met on an identical copy of that brief, and this block therefore
does not settle DEC-1.** The favourable figure is the pre-registered one and it is not being banked. A
refutation that disappears when the same bytes are sent again is not a refutation; it is a coin.

Everything else in this family follows from that. The repeat floor -- how often the same bytes agree
with themselves -- is **6 of 12**. Agreement with `plain` is `reordered` 6, `reordered-2` 7,
`reordered-3` 3, `relabelled` 9, `contrast` 5, `ablated` 1, all of 12. Only `ablated` sits clearly
below the floor; the three reorderings, the relabelling and the contrast are all within a few points
of it, and nothing whose agreement sits at the floor can be told from the floor.

- **DEC-2 is not refuted.** Over the nine, the model's 0.778 exceeds the best fixed policy's 0.667 by
  one point of nine. Its own choices split evenly between `stay` and `move-to-recover_json_object`, so
  there is no single modal choice; on the tie-break that favours the baseline it gets 0.667. One point
  is not a margin.
- **DEC-3 cannot be read as written.** Its condition compares "form agreement" with contrast
  agreement, and no aggregate over the four form briefs was pre-registered -- a defect in the
  pre-registration, not in the records. By their mean (6.25 of 12) form exceeds contrast (5 of 12); by
  `reordered-3` alone (3 of 12) it does not. Both are stated; neither is banked.
- **DEC-4's measure does not do what it was built to do**, and the records show why. See below.
- **DEC-5 is refuted, weakly.** `ablated` agrees with `plain` on 1 of 12 against a floor of 6 of 12, so
  removing the figures moves the choice further than nothing does. With a floor that wide, "weakly" is
  the honest adverb.

## Withdrawn before it was reported: what the contrast measures

On the first reading of this block I was about to report that the contrast does not move the choice --
5 of 12 agreement against a floor of 6 of 12 -- and conclude that what the figures *say* does not steer
the decision. Then I read the replies. The conclusion is not supported and the measure is at fault.

`contrast_of` swaps two checks' whole tallies, segments included. At `recover_json_object.s1` that
turned the check being worked into one with **no segments run**, and the reply said so: *"recover_json_
object has not been run yet, so the search should run a segment on it before moving to another check"*
-- a correct reading of the corrupted figures, reaching the same option by a different and valid route.
Agreement between briefs cannot tell that from insensitivity.

The measure that can, computed after the records and therefore a description of them: does each choice
equal what **its own brief's** figures point at? `plain` 10 of 12, `contrast` 8 of 12. The choice does
track the figures, on both briefs, and where the contrast moved it, it moved to what the corrupted
figures point at. The pre-registered agreement figure (5 of 12) and this one (8 of 12) point opposite
ways, and this one is the one that answers the question asked.

What a corrected contrast would do: swap the class counts and hold the segment counts fixed, so an
unexplored check cannot be manufactured. That is a new probe and a new block, not a re-reading of this
one. Recorded in `docs/mini/ERRATA.md`, C26.

## What to add: asked, unscored, and it always added something

Three states, no key, for the reason given above. It chose `add-the-attacking-seat-and-the-carried-
brief` on the plain loop and `add-the-warrant-schema` on both loops that already had something, so on
three states out of three it chose to spend calls rather than to add nothing -- including on the state
where the loop was shown as having found three distinct ways in eighteen segments. With three states
its repeat floor is 2 of 3 and nothing about sensitivity can be measured, which is what the
pre-registration said would happen.

## The stacking order, which is what miniReason explores

Four blocks, three permutations of them beside the canonical one. On the campaign family the order
changes nothing that can be told from the floor: 0.500, 0.750, 0.625 against 0.625, with an identical
brief giving 0.625.

On the search family `reordered-3` is the lowest row in every table -- hit rate 1 of 9, follows its own
figures 2 of 12, agreement with `plain` 3 of 12. It is the one permutation that puts the figures **last**,
after the task block; `plain` puts them third of four. Against a floor of 6 of 12 that difference cannot
be attributed to the ordering, and it is written here as a thing to test rather than a thing shown: one
permutation, twelve points, and a floor wide enough to hold most of the effect.

## The usable finding, which is free

The two families differ in the kind of decision and the tell costs one extra call: **send the same
brief twice.**

| | the campaign's rule over six numbers | which check to work next |
|---|---|---|
| identical brief, twice | same answer, 8 of 8 | different answer, 6 of 12 |
| score on the first copy | 0.625 | 0.778 |
| score on the second copy | 0.625 | 0.333 |
| numbers changed | follows them, 0.625 against the new key | cannot be told from the floor |
| numbers removed | falls to 0.125, below chance | falls to 0.111 |

A decision a small model can be given is one where resending the brief gives the same answer. That
test needs no larger model, no key, and no grid: it is one call, and it would have told us before any of
the other 236 which of these two questions was worth asking.

## What this block does not show

- Nothing about models in general. One model, one endpoint, temperature zero, seed 11, one task.
- Nothing about whether a second seed would move the search family. The pre-registration said a second
  seed runs only if the repeat floor is above zero; it is 6 of 12, so a second seed is now warranted and
  has not been run.
- Nothing about what to add, by design.
- Nothing about the machine's rule precedence being right. The campaign key is a policy a person wrote,
  and 0.625 agreement with it is agreement with that person's judgement.
- Nothing about `stop` as a decision. The three points where `stop` was the key are the three the
  figures cannot reach, and the model never chose `stop` on any plain brief.
