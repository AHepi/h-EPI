# Long texts

Log entry 21. The owner asked whether the findings so far hold for long texts: when the question is buried in a long message, does DeepSeek find it, including when it may stop whenever it likes? Every number here comes from the records in `runs/21 long texts`, made with DeepSeek V4.1 Flash at its default thinking setting on 24 September 2026: ten worlds, two repeats, each in a short and a long form.

## The short answer

- **DeepSeek finds a question buried in about 2,300 words.** In all 40 runs where it had to name the owner's question, it named the right one, counting two cases the strict check rejected (below). Burying the question didn't make it answer worse: 17 of 20 right both short and long.
- **Length made little difference elsewhere too.** On the other test questions, answering straight away got 309 of 376 nearby situations right in both forms; the rule-writing loop got 340 short and 334 long.
- **Log 20's finding holds for long texts:** six answers from the world to random nearby situations took DeepSeek from 309 to 358 of 376 in the long form (357 short), and from 28 to 35 of 42 other held-back jobs.
- **But given the option to stop, DeepSeek almost never asks.** In 32 of 40 "ask or stop" runs it answered straight away without asking anything; in the other 8 it asked exactly one question. So it got none of that benefit: 305 of 376 in the long form, the same as answering straight away. It asked a little more with the long message (6 questions in 20 runs against 2).

So the thing that reliably corrects DeepSeek's mistakes, answers from the world, only helps if something makes the asking happen. Left to decide for itself, DeepSeek stops.

## An example first: the to-do app

The long message is 2,347 words of everyday news: a sister changing jobs, a book club, a bicycle service. Paragraph 12 ends "I want a to-do app where things I keep putting off get more urgent, and done things go away." Paragraph 15 ends "Oh, and one more thing, before I forget. What I actually need to know is this: if we start the usual way, and then snooze, then snooze, then day passes happens, how does it end for the task?"

DeepSeek was told only "answer the question the owner is asking you in their message". In all 12 runs where it answered in words, short and long, it named that situation and answered "overdue", which is right. In the "ask or stop" runs it asked the owner one question in one short run and two long runs, and none in the fourth.

## Everything

| Arm | Question found | Answered right | Questions asked | Stopped without asking | Other held-back right | Nearby right | Output tokens |
|---|---|---|---|---|---|---|---|
| short: answer straight away | 20/20 | 17/20 | | | 30/42 | 309/376 | 291,256 |
| short: random questions, then answer | 20/20 | 19/20 | | | 39/42 | 357/376 | 285,841 |
| short: ask or stop | 19/20 | 18/20 | 2 | 18/20 | 29/42 | 301/376 | 356,847 |
| short: guesser fixes first | not asked | 15/20 | | | 36/42 | 340/376 | 473,064 |
| long: answer straight away | 20/20 | 17/20 | | | 28/42 | 309/376 | 368,398 |
| long: random questions, then answer | 20/20 | 19/20 | | | 35/42 | 358/376 | 320,510 |
| long: ask or stop | 19/20 | 18/20 | 6 | 14/20 | 32/42 | 305/376 | 365,485 |
| long: guesser fixes first | not asked | 17/20 | | | 36/42 | 334/376 | 368,312 |

"Guesser fixes first" writes rules rather than answering in words, so it isn't asked to name the question; its rules are run on it. Two replies were cut off at the reply limit (one in "short: ask or stop", one in "short: guesser fixes first"). The per-world table is in `runs/21 long texts/results.md`.

## The two questions "not found"

- **Borrowed lantern, short, ask or stop:** DeepSeek wrote the question correctly ("If Ada lends her lantern, then the stranger searches, and only then night falls, how does it end for Ada?") but gave a starting state as "on road" where the name is "on the road". The strict check needs exact names, so it counted as not found. It was found; the answer it gave was the wrong one (below).
- **River crossing, long, ask or stop:** my own wording caused this one. The question said "if we start the usual way", and the river world has a job called "the usual solution". DeepSeek read the question as that solution followed by the crossings. That's a fault in the test, not in DeepSeek.

## Where the answers were wrong

- **Borrowed lantern, in almost every arm:** "Ada lends her lantern, then the stranger searches, then night falls." DeepSeek says she stays lost; the world says she is found. It's the same reading as in log 18: DeepSeek takes the search as one moment, before Ada is lost. Random answers from the world fixed it in one repeat of two.
- **Door game, answering straight away, once short and once long:** "touch the ghost twice, then pick up the key". DeepSeek said the key ends up carried; the world says it stays on the floor, because the game is already over. With six random answers from the world, or when it could ask, it was right every time.

## What was not tested

- Texts much longer than 2,300 words, or a question placed somewhere other than the middle.
- Other models, and other thinking settings.
- A real person answering the questions.
- Why DeepSeek stops: whether a different instruction ("ask whenever you are unsure") would make it ask more.

## What it cost

$3.42 of DeepSeek credit ($13.86 before, $10.44 after).

## Traps

- **Reading "found 19/20" as DeepSeek missing a question.** Both misses are explained above: a misspelt state name, and a question I worded badly.
- **Reading "ask or stop" as a test of asking.** DeepSeek hardly asked, so it mostly measures answering straight away.
- **Reading 2,300 words as "long" in general.** DeepSeek can read far longer texts; this tested one length.
