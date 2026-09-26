# The owner will not say

*A word first: "the owner" in this report is the **pretend owner**, a made-up person who writes the test message and whose answers the hidden correct version of each world supplies. It never means the real owner of this project, who asked nothing in these tests.*

Log entry 23. In log 22, DeepSeek, made to ask 20 questions, first asked the owner their own buried question back, so its right answers showed nothing about its reasoning. Here the owner refuses: asking the buried question gets "I can't tell you that one; that's what I'm asking you", and it still uses up one of the 20. Every number comes from the records in `runs/23 owner will not say`, made with DeepSeek V4.1 Flash at its default thinking setting on 24 September 2026, on log 21's long messages: ten worlds, two repeats.

## The short answer

- **Refused, DeepSeek works the answer out from the questions it may ask, including where its own first reading was wrong.** The borrowed lantern is the world DeepSeek has misread since log 18. Answering straight away, it got the owner's question wrong in both repeats. Refused, and asking around it, it got it right in both.
- **Overall: 19 of 20 right after the 20 questions, against 18 of 20 answering straight away.** The one it lost (the hidden ball) it lost because of a limit in this test: the owner only ever says how a situation ends, and that question was about the middle.
- **It still tries to ask the owner's question: 39 times, in all 20 runs, up to 6 times in one run** (the hidden ball, which has almost nothing else to ask about).
- **It asked near copies** (the owner's question plus more events) 21 times in 11 runs. In the borrowed lantern the near copy could not have given the answer away; in general I can't rule it out. In the 9 runs with no near copy it was right 8 times.
- **It helps with the rest too:** afterwards, 35 of 38 other held-back jobs and 318 of 357 nearby situations right (straight away: 27 and 300).
- **It is expensive:** 2.1 million output tokens against 342,000 for answering straight away.

## An example first: the borrowed lantern

The owner's question: Ada lends her lantern, the stranger searches, then night falls; how does it end for Ada? The owner means she is found (the search goes on). DeepSeek's own reading, every time since log 18: she stays lost (the search was one moment, before she was lost).

Repeat 1:
1. It asks the owner's question. **Refused.**
2. to 4. Parts of it: lending then searching; night alone with the lantern gone.
5. "The stranger has the lantern, searches, then night falls." It expects "lost". The owner says "found". **Surprised.** That's the same thing it had wrong, in a situation the owner will answer.
6. to 20. It checks around that: searching when Ada is already lost, night with and without the lantern, searching twice.

Its final answer: "found". Right. Repeat 2 was the same: refused at question 5, surprised at questions 8 and 17 by situations of the same shape, final answer "found".

## Everything

"Fair" leaves out every test question whose situation DeepSeek asked the owner about.

| Arm | Owner's question answered right | Other held-back right, fair | Nearby right, fair | Output tokens |
|---|---|---|---|---|
| answer straight away | 18/20 | 27/38 | 300/357 | 341,730 |
| must ask 20, owner will not say | 19/20 | 35/38 | 318/357 | 2,127,316 |

What DeepSeek did with its 400 questions:

- asked the owner's own question and was refused 39 times, in all 20 runs (most: 6, in the hidden ball)
- asked a near copy 21 times, in 11 runs; right in 11 of those 11 runs, and in 8 of the 9 runs without one
- repeated its own earlier question 36 times
- surprised by 55 of 359 comparable answers
- never tried to stop early; 3 replies were not a question and were sent back

By world: straight away was wrong on the owner's question twice (both borrowed lantern); after the 20 questions, once (hidden ball, repeat 1). Every other run was right both ways. The full table is in `runs/23 owner will not say/results.md`.

## The one it lost: the hidden ball

The question: with the screen down and the ball starting at spot 1, is it ever seen at spot 2 along the way? The owner means yes. Answering straight away, DeepSeek said yes. Refused five times, it asked about other starting points, and every answer was the same, "it ends seen at 4", because the owner only reports how things end. None of that could show the middle. After 20 identical endings it changed its answer to no. This is a gap in what the owner in this test can say, not in the reasoning.

## Comparing with log 22

With the owner's answers to their own question (log 22), the nearby count after 20 questions was 345 of 350; here, refused, 318 of 357. The two runs used different questions and fair sets, so the numbers are not strictly comparable. What is clear is that refusals used up about two of the twenty questions per run.

## What was not tested

- An owner who can say what happens along the way, not only how it ends.
- Blocking near copies too.
- A real person answering, other models, fewer questions.

## What it cost

$2.93 of DeepSeek credit ($7.45 before, $4.52 after).

## Traps

- **Reading 19 against 18 as a big overall gain.** On the owner's question it is one run. The borrowed lantern is where the difference is real: wrong twice straight away, right twice after asking.
- **Reading the near copies as proven harmless.** In the borrowed lantern they could not settle the question; elsewhere I did not check each one.
- **Reading the hidden-ball miss as a reasoning failure.** The owner's answers could not show what the question asked about.
