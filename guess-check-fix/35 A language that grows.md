# A language that grows

Log entry 35. The other half of condition 2 from log 33: can the checker's rule language, if the guesser may add a new kind of thing to it, hold what log 34 showed it could not? The plan and six conjectures were committed before the run ("35 Plan - a language that grows.md"). Every number here comes from the records in `runs/35 growing language/`, made with DeepSeek V4.1 Flash at its default thinking setting on 26 September 2026: three devices, three arms, three repeats.

## The short answer

- **Yes: with the door to add a new kind, the rule language held the explanations as well as JavaScript did.** On the balance gate and the peg tube, the growing language got every long test case right (63 of 63), the same as JavaScript. It stayed right on probes of up to 2,000 actions, with no reply cut off. The fixed rule language got 23 of 63.
- **DeepSeek added the right primitive, and mostly kept the explanation in rules.** For the gate it added a number, "add one", "take one", "zero", with four rules around it, every time. For the peg tube it added a pile. In one run the pile was a general one, with the logic in 9 rules. In another it put most of the tube, jamming included, inside one new kind.
- **A surprise in the fixed language: DeepSeek invented binary counting.** In two of three gate runs it wrote eight things, each 0 or 1, and 41 rules that together count up to 256. That is a far more compact approximation than log 34's one-state-per-number counts. It got every planned long test right, but it is still an approximation: probes show it says "open" after 256 pushes. So log 34's "too big to write" was about one way of writing a count, not about the rule language as such.
- **The peg tube stayed out of the fixed language's reach:** all 18 replies were cut off, with no model in any run.
- **Growth was used even where it was not needed, and it let the old habit back in.** On the grudge, DeepSeek added a new kind in every run, and each was a running score of insults against kindness: the habit that failed in log 25. It scored 10, 11 and 9 of 12, where log 25's bare runs, with the same habit, scored 9 or 10.

## An example first

The peg tube: slide red or blue pegs in, take them out, and a light shows green, amber or red. Only the top peg can come out; taking out a peg that is not on top jams the tube for good.

In the growing language, DeepSeek's first-round model in repeat 1 added two new kinds:
- a **pile**, with changes "push red", "push blue" and "pop", and tests "empty", "red top", "blue top";
- a **fault**, which is set once and stays set.

Nine ordinary rules did the rest: "when red out happens and the pile is red top, the pile does pop"; "when red out happens and the pile is not red top, the fault does set"; "when the fault is clear and the pile is empty, the light is green"; and so on.

It fitted all 24 observations. It was right on every test case, including "15 red in, 1 blue in, 15 red out, 1 blue out", which a model counting each colour gets wrong, and on 50 pegs in and out.

In the fixed language, all six replies in each of the three runs were cut off before a model arrived.

## Everything

Right of all, summed over three repeats. "Rival-wrong" tests are the peg-tube cases that separate counts of each colour get wrong.

| Device | Arm | Long tests right | Short tests right | Hard tests right | Rival-wrong tests right | Runs fitting every observation | Replies cut off | Output tokens |
|---|---|---|---|---|---|---|---|---|
| balance gate | fixed language | 23/24 | 18/18 | 21/21 | - | 3/3 | 3 | 175,903 |
| balance gate | growing language | 24/24 | 18/18 | 21/21 | - | 3/3 | 0 | 14,965 |
| balance gate | universal language | 24/24 | 18/18 | 21/21 | - | 3/3 | 0 | 20,267 |
| peg tube | fixed language | 0/39 | 0/18 | 0/24 | 0/15 | 0/3 | 18 | 576,000 |
| peg tube | growing language | 39/39 | 18/18 | 24/24 | 15/15 | 3/3 | 0 | 54,779 |
| peg tube | universal language | 39/39 | 18/18 | 24/24 | 15/15 | 3/3 | 0 | 45,345 |
| grudge | fixed language | - | 27/36 | 15/24 | - | 3/3 | 1 | 87,373 |
| grudge | growing language | - | 30/36 | 19/24 | - | 3/3 | 0 | 28,361 |
| grudge | universal language | - | 28/36 | 16/24 | - | 3/3 | 1 | 68,217 |

What the fixed language wrote for the gate:
- repeat 1: a count from -100 to 100 in 402 rules, after two replies were cut off;
- repeats 2 and 3: eight things of 0 or 1 and 41 rules, counting in binary.

What the growing language wrote:
- **Gate:** one kind, one new thing and 4 rules, every run.
- **Peg tube:**
  - repeat 1: two kinds, a pile and a fault, with 9 rules;
  - repeat 2: two kinds and 9 rules;
  - repeat 3: one kind that holds both the pile and the jam, with 7 rules that pass actions in and read the light out.
- **Grudge:** one number kind in every run, a running score:
  - repeat 1: insult takes two, apology and gift add one, warm while positive;
  - repeat 2: anger up for an insult, down for an apology.

**Probes after the run** (`probes after the run.json`). These were added after I saw the results, and run at no cost:

| Probe | Truth | Fixed language (repeats 1, 2, 3) | Growing and JavaScript |
|---|---|---|---|
| 256 pushes | shut | shut, **open**, **open** | right in every repeat |
| 300 pushes then 44 pulls | shut | shut, **open**, **open** | right in every repeat |
| 150 pushes then 150 pulls | open | **shut**, open, open | right in every repeat |
| 1000 pushes then 1000 pulls | open | **shut**, open, open | right in every repeat |

On the peg tube, 50 pegs in and out in the right order, and 50 red in, a blue in, then 50 red out: growing and JavaScript right in every repeat; the fixed language had no model.

## The conjectures

1. **The growing language gets more long test cases right than the fixed language, on the gate and peg tube together.** *Not refuted:* 63 of 63 against 23 of 63.
2. **The growing language gets within 3 of the universal language on those long cases.** *Not refuted:* 63 and 63.
3. **Growth does no harm where it is not needed: on the grudge, within 2 hard cases of the fixed language.** *Refuted as written, in the other direction:* 19 against 15. The growing arm's running score happened to score a little higher. Its answers are the log 25 habit, not the true explanation.
4. **DeepSeek adds a new kind in every gate and peg run, and in at most one of three grudge runs.** *Refuted:* it added one in every run, grudge included.
5. **At most 2 replies cut off in the growing arm's gate and peg runs.** *Not refuted:* none.
6. **The fixed language gets fewer than half the peg long cases right.** *Not refuted:* 0 of 39. But every one of its 18 replies was cut off, so this measures failing to write a model at all.

## What this means for the idea

- **Condition 2's growing half holds here.** A door to add a primitive let the rule language say what it could not, with small models and no cut-offs. Most of the explanation stayed in rules the checker can report on part by part. In one peg run it did not: most of the tube went inside one new kind.
- **Log 34 overstated the fixed language's limit.** Binary counting reaches very far with very little. The honest version: a fixed language with finite states can only approximate an unlimited count, but a clever enough encoding makes the approximation cheap. The limit is where it breaks (256 here), not whether it can be written. The peg tube, a pile of coloured pegs, stayed out of reach in both logs.
- **DeepSeek's invention of binary counting is itself a small construction.** No one asked for it. It built a new way to represent a number out of the rule language's existing parts: the "recombination" we talked about, done well. It is still inside a finite language, so it is still an approximation.
- **Growth without criticism invites the familiar.** On the grudge, where the rule language already had what was needed, the new-kind door was used to write the running score, the habit that failed in log 25. A door to new primitives needs criticism behind it too; on its own it lets the model's habits in as easily as the right idea. With only 14 observations, nothing here could refute the running score (log 25's finding again).

## What was not tested

- A growing language whose new kinds are built from the rule language's own parts, not written in JavaScript.
- Whether the checker's own tools (reporting which rule failed, the hard-to-vary sweep) work on models with new kinds.
- Condition 6: DeepSeek changing its own methods.
- More repeats, other models.

## Failures along the way

- **Before any run**, a check of the peg tube's first ten long cases found that separate counts got 9 of them right by coincidence, which would have repeated log 34's gap. Three cases it must get wrong were added, and the plan was updated with a note.
- **Two of my tests failed before any run, both my mistakes, not the code's:**
  - a model meant never to settle did settle, because its rule stopped firing once the gate shut;
  - I expected 4 peg tests that separate counts gets wrong, and there are 5, one short and four long.

  Both tests were corrected.

## What it cost

$0.68 of DeepSeek credit ($14.98 to $14.30).

## Traps

- **Reading the fixed language's 23 of 24 on the gate as holding a count.** It is binary counting up to 256; the probes break it.
- **Reading the growing arm's better grudge score as a better explanation.** It is the running score, the habit log 25 found; it happens to score a little higher here.
- **Reading "grows" as DeepSeek inventing a language.** It added primitives through a door the program provides, and wrote their insides in JavaScript.
- **Reading one log's fixed-language failure mode as fixed.** Log 34's gate runs wrote one-state-per-number counts that were cut off; this log's wrote binary. The same arm varies from run to run.

## Correction after reading the revised semantics (log 36)

- **What this log rules out, and what it does not.** The growing language holding every long case is an exhibited bypass. It rules out the proposed barrier "the rule language, even with a door to new kinds, cannot hold these counts and piles", for whoever accepts the records and the grading as premises (Part XIII of the revised semantics: "an argument that exhibits one bypass rules out a proposed barrier"). "Growth closes the gap" as a general claim is only not ruled out, and gets nothing from that.
- **"DeepSeek's invention of binary counting is itself a small construction."** Too strong. The revised semantics counts "a small binding newly prepared inside received content" as construction of that binding, but only for an owned subhistory that prepares a represented organization (Part X). Nothing in these records shows either, and binary counting itself is inherited. What the records show is that it used binary counting on this gate without being asked.
