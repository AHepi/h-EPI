# Twenty questions

Log entry 22. In log 21 DeepSeek, free to stop, almost never asked the owner anything. The owner said: make it ask 20 questions first, and see what it does. Every number here comes from the records in `runs/22 twenty questions`, made with DeepSeek V4.1 Flash at its default thinking setting on 24 September 2026, on log 21's long messages (about 2,300 words, one question buried in the middle): ten worlds, two repeats.

## The short answer

- **Made to ask, DeepSeek asks well.** One question at a time, seeing each answer before the next, its 20 questions helped at least as much as 20 random ones: afterwards it got 345 of 350 nearby situations right (random 20: 338; answering straight away: 287), and all 37 other held-back jobs (random 20: 37; straight away: 27). That's a change from log 20, where DeepSeek wrote all its questions at once without seeing any answers, and they helped least.
- **The first thing it does is ask the owner their own question back.** In 15 of 20 runs its very first question was the buried question itself, and in the other 5 it asked it by question 8. Over the 20 runs it asked the owner's own question 49 times. So its perfect score on the owner's question (20 of 20) says nothing about its reasoning: it was told the answer.
- **It learns as it goes.** With each question it said what it expected. The owner's answer surprised it 65 times in 399. Surprises were more frequent in questions 1 to 10 (37 of 200) than in 11 to 20 (28 of 199).
- **It never tried to stop early**, and all 400 questions used names the owner could follow.
- **It is expensive.** Its 20 questions cost 1.75 million output tokens across the 20 runs, six and a half times what 20 random questions cost (267,000). Most of it is thinking, rereading the long message at every turn.

## An example first: the borrowed lantern

This is the world DeepSeek misread in logs 18 to 21: it takes "the stranger goes out searching" as one moment, the owner means a search that goes on. Repeat 2, DeepSeek's 20 questions:

1. The owner's own question: Ada lends the lantern, the stranger searches, night falls. **Expected "lost". The owner said "found". Surprised.**
2. Same events, search after nightfall. Expected "found"; right.
3. Lend, then search, no nightfall. Expected "found"; the owner said still on the road. Surprised.
4. to 18. One event at a time, different orders and starting points: night alone with and without the lantern (surprised when it guessed "lost" and the answer was "home safe"), searching when already lost, lending when already lost.
19. The owner's own question again. Expected "found" this time; right.
20. Lend, then night, no search: "lost"; right.

Its final answer: "found", which is right. In question 1 it asked the owner to settle the very thing it had wrong, and from then on it explored around it.

## Everything

"Fair" leaves out every test question whose situation either arm asked the owner about (DeepSeek asked about the situation of another test question 49 times).

| Arm | Owner's question answered right | Other held-back right, fair | Nearby right, fair | Answers from the owner | Output tokens |
|---|---|---|---|---|---|
| answer straight away | 19/20 | 27/37 | 287/350 | 0 | 330,308 |
| random 20, then answer | 20/20 | 37/37 | 338/350 | 360 | 266,826 |
| must ask 20, then answer | 20/20 (it asked for this answer in every run) | 37/37 | 345/350 | 400 | 1,752,717 |

Random 20 gave 360 answers rather than 400 because some worlds, like the hidden ball, have fewer than 20 different nearby situations.

What DeepSeek did with its 400 questions:

- asked the same situation twice: 38 times, 20 of them in the hidden ball, which has almost nothing to vary (no events, one screen), and 10 in the river puzzle
- two events per question on average; about half the questions (198) changed a starting state from the usual one
- 3 replies were not a question; it was told to ask, and did
- surprised most in the hidden ball (16 of 40) and plant watering (13 of 40), never in the door game (0 of 40)

The by-world table is in `runs/22 twenty questions/results.md`.

## What this means for the idea

- **Asking is where the error correction comes from, and DeepSeek can do it well, if it must.** Left to decide (log 21) it asked nothing. Made to ask, one at a time, it probed the exact place it was wrong and went on from there.
- **The loop around it matters: seeing each answer before the next question.** Writing questions all at once (log 20) was worse than random; asking one at a time was at least as good as random.
- **Asking the owner their own question is the sensible move, and it spoils the test.** A real owner may not know the answer to their own question. Whether DeepSeek can reason its way to the answer, rather than ask for it, needs a test where the owner won't answer that one.
- The difference between DeepSeek's 20 and random 20 (345 against 338) is small, from two repeats; call it "at least as good", not "better".

## What was not tested

- Fewer than 20 questions asked one at a time: how quickly the benefit arrives.
- An owner who refuses to answer their own question.
- Other models, and a real person answering.

## What it cost

$2.81 of DeepSeek credit ($10.34 before, $7.53 after).

## Traps

- **Reading "20 of 20 right" on the owner's question as reasoning.** DeepSeek asked the owner that very question in every run.
- **Reading "must ask 20" as cheap.** Six and a half times the tokens of 20 random questions.
- **Reading 345 against 338 as DeepSeek beating random.** Two repeats; within the noise seen before.
