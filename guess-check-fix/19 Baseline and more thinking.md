# Baseline and more thinking

Log entry 19. The owner asked for two things: test the project against a baseline, and rule out that spending more tokens solves the same problems. Every number here comes from the records in `runs/19 ...`, made with DeepSeek V4.1 Flash on 23 and 24 September 2026. The tables are written by `19 summarise baseline.js` and `18 summarise planted mistakes.js`, which make no DeepSeek calls.

## The short answer

- **Against the baseline, the loop wins, but in one particular way.** "DeepSeek alone" gets the request, the owner's word list and the shown jobs with their answers, and answers questions directly: no model, no checker, no loop. On 376 nearby situations, "guesser fixes first" got 338 right, DeepSeek alone 300. On the 62 held-back situations it was 54 against 49, **but that lead disappears on held-back situations the loop never asked the world about: 29 of 37 against 30 of 37.**
- **More tokens do not close the nearby gap.** Thinking harder (385,000 tokens, no cut-offs) got 312 right. Asking five times and taking the majority (1.34 million tokens, four times the loop's) got 310. The loop got 338 with 332,000 tokens. The lowest thinking setting did best of the DeepSeek-alone arms (318).
- **More thinking does not help the loop either.** "Guesser fixes first" at the highest setting: 337 (default: 338), for 50% more tokens.
- **What does close the gap is information, not tokens.** Given the same answers the world gave the loop, DeepSeek alone got **356** nearby and 60 of 62 held-back right, better than the loop itself (338 and 54). So the loop's real contribution is **finding which questions to ask**. Once the answers are in, DeepSeek alone uses them better than the loop's rule models do.
- **For fixing hidden mistakes by rereading, more thinking does help, and I can't rule it out there.** Self review at the highest setting repaired 13 and then 11 of the 20 hidden planted mistakes in two runs, against 9 and 9 at the default. That is the same range as "guesser fixes first" (11 and 13). On the hidden mistakes it cost four to six times the loop's tokens and made 3 or 4 of them worse where the loop made none worse, and it repaired at most half the visible mistakes (3, then 5) where the loop repaired all 10.

## An example first: the river puzzle

River crossing, both repeats, questions right out of 46:

| DeepSeek alone | alone, highest thinking | alone, majority of 5 | guesser fixes first | alone, given the world's answers |
|---|---|---|---|---|
| 12 | 26 | 20 | 26 | 39 |

The request leaves two things open (log 18): can the farmer "cross with the fox" when the fox is on the other bank, and what gets eaten first. Thinking longer can't settle what the request doesn't say. It raised DeepSeek alone from 12 to 26, and so did the loop, but only the world's answers took it to 39. Asking the right question beat thinking harder.

## The ten worlds

The same questions were put to every arm: the 31 held-back jobs that don't ask about a particular step (the checker's idea of a "step" would be unfair to ask DeepSeek directly), and 20 nearby situations per world (8 for the hidden ball), picked by a fixed shuffle. That's 62 held-back and 376 nearby questions over two repeats.

| Arm | Held-back right | Nearby right | Output tokens |
|---|---|---|---|
| DeepSeek alone, default thinking (the baseline) | 49/62 | 300/376 | 262,212 |
| DeepSeek alone, lowest thinking | 51/62 | 318/376 | 211,293 |
| DeepSeek alone, highest thinking, limit 200,000 | 52/62 | 312/376 | 384,911 |
| DeepSeek alone, default, majority of 5 | 50/62 | 310/376 | 1,341,899 |
| first guess alone (a model), default | 52/62 | 303/376 | 156,723 |
| **guesser fixes first, default** | **54/62** | **338/376** | 331,609 |
| guesser fixes first, lowest | 52/62 | 322/376 | 228,287 |
| guesser fixes first, highest | 54/62 | 337/376 | 497,387 |
| DeepSeek alone, default, given the world's answers | 60/62 | 356/376 | 216,420 |

Leaving out every situation the loop asked the world about (the loop's advantage there is information it asked for):

| Arm | Held-back right | Nearby right |
|---|---|---|
| DeepSeek alone, default | 30/37 | 292/365 |
| DeepSeek alone, highest thinking, limit 200,000 | 32/37 | 303/365 |
| DeepSeek alone, majority of 5 | 32/37 | 301/365 |
| guesser fixes first, default | 29/37 | 327/365 |
| DeepSeek alone, given the world's answers | 35/37 | 345/365 |

By world (both repeats), the loop is ahead of DeepSeek alone in six worlds (ball and wall, borrowed lantern, lighthouse, moving day, to-do app, river crossing), level in three (door game, ghost lantern, hidden ball), and behind in one (plant watering, 42 against 48). The full table is in `runs/19 baseline and more thinking/summary.md`.

## The planted mistakes, with more tokens

The same 32 planted mistakes as log 18.

| Corrector | Visible (10) repaired | Hidden (20) repaired | Made worse | Output tokens |
|---|---|---|---|---|
| self review, default | 5 | 9 | 5 | 437,375 |
| self review, highest thinking | 3 | 13 | 6 | 554,768 |
| self review, highest thinking, limit 200,000 | 5 | 11 | 4 | 621,671 |
| self review, three rounds | 2 | 7 | 5 | 1,573,572 |
| **guesser fixes first, default** | **10** | 13 | 1 | 149,593 |
| guesser fixes first, highest thinking | 10 | 14 | 1 | 179,015 |

Reviewing three times made things worse, not better: 7 hidden repaired, against 9 from one review, for 3.6 times the tokens. Each review re-guesses the whole model again (log 18).

## Why this happens

The loop's problems are mostly **missing information**, not missing effort. DeepSeek's mistakes sit where the request can be read more than one way, like whether the stranger's search keeps going. More thinking picks one reading more carefully. It can't know which reading the owner meant. A question to the world can. That's the theory's point that finding the question is half the creative work (Derivation 5): the loop's machinery earns its place by finding questions, not by doing the reasoning.

## What was not tested

- Other models. Only DeepSeek V4.1 Flash.
- A real person answering the world's questions. The hidden true model answered, always correctly.
- Majority votes for the loop, or the loop at the lowest thinking setting with more rounds.
- How much this varies. Two repeats per world; "guesser fixes first" repaired 11 and then 13 hidden planted mistakes on identical inputs, so differences of about two are within noise.
- The individual replies of the majority-of-5 arm were not kept, so its cut-off replies cannot be counted.

## What it cost

$4.46 of DeepSeek credit for everything in this entry, including a four-call check of the thinking setting: the balance went from $20.11 after log 18 to $15.65.

## Traps

- **Reading "DeepSeek alone, given the world's answers" as a baseline.** It had information only the loop's questions produced. It shows what the questions are worth; it's not something DeepSeek alone could do.
- **Reading the held-back lead as the loop reasoning better.** It comes from situations the loop asked about. On the others, DeepSeek alone was level.
- **Reading "highest thinking" at the 32,000 limit.** Three of its replies were cut off before answering; use the "limit 200,000" row.
- **Treating one run's difference of one or two as real.** Repeats differ by about that much.
