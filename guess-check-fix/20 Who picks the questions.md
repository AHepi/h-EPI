# Who picks the questions

Log entry 20. Every number here comes from the records in `runs/20 who picks the questions`, made with DeepSeek V4.1 Flash at its default thinking setting on 24 September 2026: ten worlds, three repeats each.

## The short answer

**This overturns what log 19 concluded.** Log 19 said the loop's real contribution was *finding the right questions* to ask the world. That was never tested against questions picked any other way. Now it has been, and:

- **Questions picked at random helped as much as the loop's questions, slightly more.** Handed the answers to the same number of questions (random: 262, the loop's: 270), DeepSeek then got 524 of 543 nearby situations right from the random ones and 516 from the loop's. On held-back jobs: 60 of 65 against 55. Random came out ahead in each of the three repeats, by 3 to 5 questions right each time.
- **DeepSeek choosing its own questions did worse than random**: 488 nearby, 57 held-back. It also cost more than twice the tokens, because choosing is itself a long reply.
- **The loop's own rule model was about level with DeepSeek alone** this time: 462 against 452 nearby, 49 against 54 held-back. In log 19 the loop was clearly ahead (327 against 292). Across the two runs, its advantage over DeepSeek alone is small and not dependable.

So what reliably improves DeepSeek's answers is **more answers from the world**, however the questions are chosen. The loop's cleverness about which questions to ask did not show up as a benefit here.

## An example first: the river puzzle

Questions right, three repeats, fair count (test questions some arm had asked about are left out):

| DeepSeek alone | the loop's own model | given the loop's questions' answers | given random questions' answers | given its own chosen questions' answers |
|---|---|---|---|---|
| 27 | 34 | 63 | 63 | 35 |

In log 19 this world was the best case for "asking the right question". Random questions did exactly as well as the loop's. DeepSeek's own choices barely helped: it asked about situations its reading already settled.

## Everything

The fixed test questions are log 19's: every held-back job except one about a particular step, and 20 nearby situations per world (8 for the hidden ball). "Fair" leaves out every test question whose situation any arm asked the world about.

| Arm | Held-back right | Nearby right | Held-back right, fair | Nearby right, fair | Answers from the world | Output tokens |
|---|---|---|---|---|---|---|
| DeepSeek alone | 77/93 | 469/564 | 54/65 | 452/543 | 0 | 391,757 |
| guesser fixes first (the loop's own model) | 77/93 | 482/564 | 49/65 | 462/543 | its own | 558,330 |
| ask then answer (the loop picks, DeepSeek answers) | 83/93 | 536/564 | 55/65 | 516/543 | 270 | 333,408 |
| random questions, then answer | 88/93 | 543/564 | 60/65 | 524/543 | 262 | 346,176 |
| DeepSeek picks questions, then answer | 84/93 | 508/564 | 57/65 | 488/543 | 270 | 827,524 |

By repeat (fair count, held-back and nearby together): random 197, 194, 193; the loop's questions 192, 191, 188; DeepSeek's questions 172, 184, 189; DeepSeek alone 169, 170, 167.

By world, random questions were ahead of the loop's in 4 worlds (ball and wall, lighthouse, plant watering, to-do app), level in 5, and behind in 1 (ghost lantern, 63 against 66). The per-world and per-repeat counts are in `runs/20 who picks the questions/results.md`. DeepSeek wrote all 270 of its chosen questions in usable form.

## What this means for the idea

- **Error correction by asking the world works; the checker's cleverness in choosing questions is not what makes it work.** A plain rule, "ask the owner about a few situations near the ones they already described", did as well.
- **The rule models themselves did not beat DeepSeek answering directly** on these questions. What they still give, and DeepSeek alone does not: a model the checker can run and test part by part (the hard-to-vary tests), and a repair of visible mistakes that keeps what was right (log 18, all 10 visible planted mistakes). Whether those are worth their cost depends on whether you need an explanation you can inspect, or only answers.

## A likely reason random did so well

Random questions come from the same kind of situation as the nearby test questions (one or two changes from a job), so they resemble what is tested. That could favour random on the nearby count. It does not explain the held-back count, where the jobs are the owner's own and random still did best (60 against 55).

## What was not tested

- Fewer questions. Here each arm got about nine answers per task. When questions are scarce, say two or three, choosing well may matter more than it did here.
- A real person answering. Every answer came from the hidden true model.
- Other models, and other thinking settings for this comparison.

## What it cost

$1.59 of DeepSeek credit ($15.58 before, $13.99 after).

## Traps

- **Reading log 19's "the loop's value is finding the questions" as still standing.** This entry refutes it for these worlds and this number of questions.
- **Reading random questions as free.** Each is still a question someone has to answer; here 262 of them.
- **Reading a difference of a few questions in one world as real.** Repeats differ by about that much; the pattern across all three repeats is what counts.
