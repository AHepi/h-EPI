# Can the language express it?

Log entry 34. A test of condition 2 from log 33: the language an explanation is written in (its primitives and rules) must be able to express the explanation. The plan and five conjectures were committed before the run ("34 Plan - can the language express it.md"). Every number here comes from the records in `runs/34 language/`, made with DeepSeek V4.1 Flash at its default thinking setting on 26 September 2026: three devices, three arms, three repeats.

## The short answer

- **Yes, on these devices: the checker's rule language could not hold the explanations; JavaScript could.** Given the same observations and the same criticism, DeepSeek wrote JavaScript functions that were right on every test case, and on probes of up to 1,000 actions. In the rule language it never produced a model that was right beyond the observations on the balance gate or the peg tube.
- **The rule language failed in two ways, both the ones condition 2 predicts:**
  - **A model big enough to count far is too big to write.** Told tests might run to a hundred actions, DeepSeek tried to write counters with up to 101 states. In the three runs that produced no fitting model, 17 of 18 rule-language replies were cut off before they finished. The one that arrived had 303 rules and fitted no observation.
  - **A model small enough to write is an approximation.** The rule models that fitted every observation broke beyond their size. One counted only from -2 to 3, which covers every observation. It then got the long gate cases that end shut right, and every deep one that ends open wrong. Two peg models kept separate counts of red and blue pegs, which fits every observation but is not a pile.
- **The control came out as it should:** on the grudge, whose explanation fits the rule language, both languages got exactly the same answers (15 of 24 hard cases each). So the win is not simply DeepSeek writing JavaScript more easily.
- **A flaw in my test:** the peg tube's observations and test cases did not separate a real pile from separate counts. The rule models "got every long peg test right" by that gap. Probes run after the results, at no cost, show them wrong on the simplest case, "red in, blue in, red out".

## An example first

The balance gate: push and pull handles, and the gate is open exactly when there have been as many pushes as pulls.

DeepSeek's JavaScript, first try, every repeat, was a few lines: add one for a push, take one for a pull, and the gate is open at zero. It was right on all 20 observations, all 12 test cases, and 500 pushes then 500 pulls.

In the rule language the same idea needs one state for every number the count can reach, and a rule for each step between them. In one repeat DeepSeek wrote a count from -2 to 3 that fitted all 20 observations. It then said "shut" after 30 pushes and 30 pulls, because its count had stopped at 3. In the other two repeats it tried to write a count big enough for a hundred actions; 11 of 12 replies were cut off before they finished.

## Everything

Right of all, summed over three repeats. "Long" test cases are 23 to 81 actions. "Hard" ones are those the obvious reading gets wrong.

| Device | Arm | Long tests right | Short tests right | Hard tests right | Runs fitting every observation | Output tokens |
|---|---|---|---|---|---|---|
| balance gate | fixed language | 3/18 | 6/18 | 5/18 | 1/3 | 403,532 |
| balance gate | universal language | 18/18 | 18/18 | 18/18 | 3/3 | 39,094 |
| balance gate | bare | 18/18 | 18/18 | 18/18 | - | 34,505 |
| peg tube | fixed language | 12/18 | 12/18 | 6/9 | 2/3 | 378,991 |
| peg tube | universal language | 18/18 | 18/18 | 9/9 | 3/3 | 52,613 |
| peg tube | bare | 6/18 | 6/18 | 3/9 | - | 83,287 |
| grudge | fixed language | - | 27/36 | 15/24 | 3/3 | 239,206 |
| grudge | universal language | - | 27/36 | 15/24 | 3/3 | 51,586 |
| grudge | bare | - | 18/36 | 10/24 | - | 74,992 |

Run by run:
- **Balance gate, fixed language:**
  - repeat 1: all 6 replies cut off, no model;
  - repeat 2: a count from -2 to 3 (6 states), fitted all 20, right on the 2 long cases ending shut and on the shallow alternating one, wrong on the 3 deep ones ending open;
  - repeat 3: 5 replies cut off, and one model with 303 rules and a count of 101 states that fitted none.
- **Peg tube, fixed language:**
  - repeat 1: all 6 replies cut off;
  - repeats 2 and 3: fitted all 24. Repeat 2 used separate counts of red and blue pegs up to 10. Repeat 3 used seven "slots" for each colour.
- **Bare:** right on every gate case in every repeat: it counted through 81 actions in words without a slip. Its peg and grudge losses are three replies cut off before any answer (peg repeats 1 and 3, grudge repeat 1); peg repeat 2 described a pile and got every case right.

**Probes after the run** (`probes after the run.json`). These cases were added after I saw the results, and run at no cost on each arm's best model or function:
- Balance gate: 500 pushes then 500 pulls; 500 then 499; 100 pulls then 100 pushes. JavaScript right in all 9. Rules wrong in 3 of 6 where a model existed (repeat 2's count said shut every time; repeat 3's 101-state model, which fitted no observation, said open every time).
- Peg tube: "red in, blue in, red out"; 8 red in, 8 blue in, red out; a six-step case with a wrong-order removal; 30 red in and 30 out; 20 in and out in the right order. JavaScript right in all 15. Rules wrong in 8 of 10 where a model existed, including "red in, blue in, red out" in both.

## The conjectures

1. **On the balance gate and peg tube, the universal language gets more long test cases right than the fixed language.** *Not refuted:* 36 of 36 against 15 of 36.
2. **The fixed language gets fewer than 9 of 18 of the balance gate's long cases right.** *Not refuted:* 3. But two of its three runs produced no usable model at all, so most of this is the cut-offs, not the approximation.
3. **On the grudge, the universal language does not beat the fixed language by more than 2 hard cases.** *Not refuted:* 15 and 15.
4. **Bare DeepSeek gets fewer long cases right than the universal language, on the gate and peg together.** *Not refuted as written* (24 against 36). But the reason I gave, counting errors, did not happen. It counted perfectly on the gate, and all of its losses are two replies cut off before any answer.
5. **On the peg tube, the universal language fits all 24 observations in at least 2 of 3 repeats, and gets at least 12 of 18 long cases right.** *Not refuted:* 3 of 3 and 18 of 18. The probes, not the planned test cases, show its functions were real piles.

## What this means for the idea

- **Condition 2 stands up here, and the way the rule language failed says why it matters.** A language that cannot express a count has two bad options. It can write a large approximation, whose size grows with how far it must reach until it can no longer be written. Or it can write a small one, which breaks past its edge. Correcting inside such a language moves between approximations. That is the "defaults to the nearest approximation" of our earlier conversation, now seen in a run.
- **The limit was the checker's language, not DeepSeek.** In words (bare) and in JavaScript, DeepSeek had the right explanation, a count or a pile. It could not put it into the rule language. So the project's own checker was the narrow part: the same limit log 28 found for cause and effect ("what is not in the model has no effect").
- **Compact expression is part of it.** JavaScript let the explanation be five lines with a loop, where the rule language needed a rule per number. That is the practical half of condition 2 from log 33 (naming and reusing constructions), and it showed up as 4 to 10 times fewer output tokens.
- **Nothing here tests growth, or condition 6.** DeepSeek was handed a universal language; it did not build one, and it did not change its own methods.

## What was not tested

- A language that grows: the rule language with a way for DeepSeek to add a new kind of thing.
- Devices whose observations separate the explanation from its near rivals by design; the peg tube's did not, and I only caught it with probes afterwards.
- More repeats, other models, other thinking settings.

## What it cost

$0.73 of DeepSeek credit ($15.71 to $14.98).

## Traps

- **Reading the peg tube's 12 of 18 for the rule language as partly right.** Those models were counts, not piles; the planned tests could not tell, the probes could.
- **Reading the gate's 3 of 18 as the approximation limit alone.** Two of three runs were cut off before any model arrived; that is part of the same limit (the model too big to write), but a different way of failing.
- **Reading "universal language" as DeepSeek becoming universal.** The program around it supplied the language.
- **Reading the probes as planned.** They were written after the results, to check a gap the results revealed.

## Correction after reading the revised semantics (log 36)

The owner uploaded a revised semantics on 26 September 2026 (it renames revision 1's "derivations" as "arguments" and its "normative relation" as the "appraisal relation"). Under it, a claim that no argument rules out gets nothing from that, and "a finite list of failures does not rule out a bypass" (Part XIII). Two readings above go too far:
- **"Condition 2 stands up here."** The runs cannot show that. That a rule language with finite states cannot hold an unlimited count is ruled in by an argument with no test in it: with finitely many states, two different counts must share a state, and from there the same actions lead both to the same answer when only one is right. The runs showed how DeepSeek's attempts broke, not that the limit exists.
- **"Big enough models were too big to write."** Log 35 found a bypass: binary counting reaches 256 in 41 rules. The failure here was one way of writing a count.
