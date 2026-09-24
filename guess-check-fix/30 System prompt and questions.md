# System prompt and questions

Log entries 30, 31 and 32 (role-play, at the end). The owner asked whether text put at the very top of DeepSeek's standing instructions (its "system prompt") changes the range and quality of the questions it asks, and to try different texts and look for patterns. The plan, round 1's six conjectures, and later round 2's six conjectures were each committed before their run ("30 Plan - system prompt and questions.md"). Every number here comes from the records in `runs/30 system prompt/`, made with DeepSeek V4.1 Flash at its default thinking setting on 24 September 2026. The task was log 22's, shortened to 10 questions: ten worlds, one run of each arm on each world.

"Pretend owner" means the made-up letter-writer whose question is buried in the long message, not the real owner.

## The short answer

- **The text at the top did not steer which questions DeepSeek asked.** Two runs with the same text overlapped no more than two runs with different texts. The same doubt text twice shared 50 situations, the same filler twice 47; different texts shared 40 to 55. The two plain runs sharing 59, which made round 1 look like a steering effect, was the high end of ordinary variation.
- **Instructions that named what to do were mostly ignored.**
  - "At least four events in every question": 21 of 100 questions had four or more; the average went from about 2.1 to 2.4.
  - "Never ask the owner the question they are asking you": DeepSeek still asked it back 11 times, in 9 of the 10 worlds (the plain runs: 17 and 15).
  - "Never ask about the same situation twice": 4 repeats, against 7 and 5 with no text at all.
- **One pattern held for every text, including a meaningless one: more of the pretend owner's answers surprised DeepSeek.** In the two plain runs, 15 of 100 answers differed from what it expected. With any text at the top, 18 to 29 of 100, in all ten texts. I do not know why.
- **Quality did not clearly change.** Every arm answered the pretend owner's question right in all 10 worlds. On the other test questions, arms ranged from 149 to 180 nearby questions right (of about 183), and the two plain runs alone differed by 11. The three new round-2 texts scored highest (168 to 180), but the two round-2 repeats of round-1 texts did not, so I cannot tell that from chance.
- **Range barely moved.** Every arm asked 90 to 96 different situations out of 100, and used 28 to 31 different events.

## An example first

In the reminder app, the pretend owner's buried question is about a task put off twice and then left for a day. With nothing at the top, DeepSeek's 10 questions included that very situation. Told "Never ask the owner the question they are asking you; they want you to work that out yourself", it asked it anyway, as its 9th question. The same happened in 8 other worlds; in the hidden ball, three of its ten questions were the pretend owner's own question.

## Everything

Totals over the ten worlds. "Also asked by plain" is how many of the arm's situations the first plain run also asked, same world.

| Arm (text at the top) | Different situations | Repeats | Events per question | Surprised, of 100 | Pretend owner's question asked back | Also asked by plain | Nearby right, fair | Output tokens |
|---|---|---|---|---|---|---|---|---|
| nothing | 93 | 7 | 2.2 | 15 | 17 | - | 153/183 | 509,973 |
| nothing, again | 95 | 5 | 2.1 | 15 | 15 | 59 | 164/183 | 432,993 |
| filler | 91 | 9 | 1.8 | 27 | 19 | 40 | 164/186 | 482,704 |
| filler, again | 93 | 7 | 1.7 | 24 (of 99) | 15 | 52 | 155/186 | 493,554 |
| doubt | 92 | 8 | 1.9 | 18 | 16 | 46 | 156/182 | 513,353 |
| doubt, again | 94 | 6 | 1.8 | 19 | 16 | 51 | 156/183 | 518,565 |
| spread | 96 | 4 | 1.7 | 19 | 11 | 47 | 149/182 | 544,867 |
| explain | 95 | 5 | 1.9 | 24 | 15 | 47 | 171/182 | 599,910 |
| detective | 91 | 9 | 1.9 | 29 | 16 | 47 | 158/185 | 583,344 |
| meaningless ("Reference number 4471-B.") | 92 | 8 | 2.1 | 19 | 16 | 49 | 176/184 | 460,784 |
| long questions | 90 | 10 | 2.4 | 24 | 20 | 49 | 180/186 | 452,951 |
| never ask it back | 96 | 4 | 1.6 | 21 | 11 | 45 | 168/181 | 675,210 |

The texts in full are in the plan. Every arm answered the pretend owner's question right in 10 of 10 worlds.

Overlap between pairs of runs, situations shared, summed over the ten worlds:
- nothing and nothing, again: 59
- doubt and doubt, again: 50
- filler and filler, again: 47
- meaningless and the two plain runs: 49 and 55
- every other pair in round 1: 40 to 53

## The conjectures

Round 1, written before any run:
1. **Each instruction or character text overlaps plain less than the two plain runs do.** *Not refuted as written* (46 to 47 against 59). But round 2 showed the same text twice overlaps only 47 to 50, so the yardstick was one lucky pair, and this does not show steering.
2. **Filler changes nothing beyond chance.** *Refuted as written* (40, against at least 53), for the same reason: the yardstick was too high.
3. **Spread widens the range.** *Refuted* (96 situations against 93 and 95, but 30 events used against 31).
4. **Doubt and explain are surprised more often than plain.** *Not refuted* (18 and 24 against 15 and 15), but every other text did the same, filler and the detective most (27, 29).
5. **Doubt and explain ask the pretend owner's question back less often.** *Refuted* (16 and 15 against 17 and 15).
6. **No arm's nearby score differs from the plain average by more than 5%.** *Refuted*: explain 171 and spread 149, against a plain average of 158.5 (the two plain runs: 153 and 164).

Round 2, written after reading round 1 and before running it:

7. **The same text twice overlaps at least 50.** *Doubt not refuted (50); filler refuted (47).*
8. **The meaningless text overlaps either plain run at most 50.** *Refuted* (55 with the second).
9. **"Long questions" averages more than 3 events per question.** *Refuted* (2.4).
10. **"Never ask it back" asks it back fewer than 5 times.** *Refuted* (11).
11. **Filler's high surprise was chance: filler, again is within 5 of 15.** *Refuted* (24).
12. **Neither new instruction costs quality: within 5% of plain.** *Refuted, in the other direction*: 180 and 168, higher.

## What this means for the idea

- **A few sentences at the top do not steer DeepSeek's questioning in this task.** Two runs differ from each other about as much as two different texts do, and direct instructions ("at least four events", "never ask it back") were followed a fifth of the time or less. What DeepSeek asks seems set by the task message and its own habits, not by its standing instructions.
- **The one steady effect has no content: more surprise with any text at the top, even "Reference number 4471-B.".** Surprise means its expectation was wrong. So something about having any standing text above log 21's changes how sure it is, or what it expects, without changing what it asks about. I have no explanation that I could test from these records.
- **This fits the earlier finding about where a language model sits.** Telling it to doubt is not the same as doubting: the "doubt" text did not make it ask where it was unsure more than filler did. Log 25 found the same with self-checking: an instruction to criticise is not criticism.

## What was not tested

- More than one run of each arm on each world; the noise is large (the two plain runs differ by 11 nearby questions).
- The same texts put in the task message instead of the standing instructions, or at the end instead of the top.
- Other thinking settings, other models, and the full 20 questions.
- Why any text raises surprise; the thinking text was not saved.

## What it cost

$3.84 of DeepSeek credit: round 1 $2.21 ($21.85 to $19.64), round 2 $1.63 (to $18.01).

## Traps

- **Reading round 1 alone.** Its apparent steering came from comparing with one lucky pair of plain runs; round 2's repeats removed it.
- **Reading the round-2 quality scores as an effect of the texts.** The new texts scored high, the repeated texts did not, all in the same round; one run each.
- **Reading "surprised" as "asked better questions".** Surprise rose with a meaningless text too.
- **The hidden ball has no events,** so "long questions" could not be followed there; it asked only 2 different situations in that world.

## Round 3: role-play (log 32)

The owner asked: "What about role playing? Does that work?" Round 1's one-line detective had done nothing that filler text did not. So round 3 gave DeepSeek three fuller characters, each with a name, a history and a way of working, and told it to stay in character. Each character ran twice on the ten worlds, 60 runs, with five conjectures committed before running. The characters in brief:
- **scientist:** Dr. Ada Reyes, who designs the experiment most likely to prove her idea wrong;
- **child:** Mia, seven, who asks "but what if...?";
- **cross-examiner:** a barrister who treats the pretend owner as a witness whose account may break, and never asks what they could already answer.

The full texts are in `30 system prompt questions.js`.

### The short answer

No. Role-play did what every other text did, and no more.
- **A character did not steer which questions were asked.** Each character's two runs shared 47 (scientist), 57 (child) and 51 (cross-examiner) situations. Each character shared 42 to 54 with the plain runs, and two different characters shared 46 to 48. The two plain runs had shared 59.
- **Each character failed to do the one thing its role was built around.**
  - The scientist was surprised 26 and 24 times in 100, no more than filler (27 and 24).
  - The child's questions were no shorter: 2.0 and 1.9 events each.
  - The cross-examiner asked the pretend owner's own question back 15 and 11 times; plain runs did it 17 and 15.
- **Surprise rose, as with every other text:** 22 to 34 in 100, against 15 and 15 plain.
- **Quality:** the cross-examiner's second run got 179 of 182 nearby questions and all 20 held-back ones right, the best of any run, but its first run got 168. The child's first run was the first arm of any round to miss the pretend owner's question. In the river crossing it restated the question wrongly, and in the plant watering it found the question but answered wrong. The child's second run got all 10. One run each, so I cannot tell this from chance.

### Everything

| Arm | Different situations | Repeats | Events per question | Surprised | Pretend owner's question asked back | Also asked by plain | Pretend owner's question right | Nearby right, fair | Output tokens |
|---|---|---|---|---|---|---|---|---|---|
| scientist | 88 | 11 | 2.1 | 26 of 99 | 18 | 42 | 10/10 | 166/187 | 506,332 |
| scientist, again | 93 | 7 | 2.0 | 24 of 98 | 14 | 53 | 10/10 | 158/184 | 532,402 |
| child | 93 | 7 | 2.0 | 34 of 99 | 14 | 54 | 8/10 | 147/186 | 561,430 |
| child, again | 91 | 9 | 1.9 | 26 of 100 | 17 | 46 | 10/10 | 149/182 | 431,818 |
| cross-examiner | 93 | 7 | 2.0 | 24 of 100 | 15 | 43 | 10/10 | 168/185 | 758,830 |
| cross-examiner, again | 96 | 4 | 1.8 | 22 of 100 | 11 | 45 | 10/10 | 179/182 | 811,717 |

For comparison, the plain runs: 93 and 95 different situations, 2.2 and 2.1 events per question, 15 surprised each, 17 and 15 asked back, 153 and 164 nearby right. All three rounds in one table: `runs/30 system prompt/all three rounds.md`.

### The conjectures

13. **A role does not steer which situations are asked** (each character's two runs share no more than it shares with either plain run, give or take 5). *Not refuted:* 47 against 42 to 53; 57 against 46 to 54; 51 against 43 to 49.
14. **The scientist is surprised more than 29 in 100, in both runs.** *Refuted* (26, 24).
15. **The child asks below 1.6 events per question, in both runs.** *Refuted* (2.0, 1.9).
16. **The cross-examiner asks the pretend owner's question back fewer than 11 times, in both runs.** *Refuted* (15, 11).
17. **Every run's nearby count is between 149 and 180.** *Refuted*, by the child's first run (147).

### What this means for the idea

A role changes the words DeepSeek uses. It does not change what it asks, or how it asks, beyond what any text at the top does. The cross-examiner was the most expensive character: about two-thirds more output tokens than the plain runs (759,000 and 812,000 against 510,000 and 433,000). A character built around refutation (the scientist) did not seek refutation any more than polite filler did. This is the same finding as rounds 1 and 2, now for role-play: the questioning comes from the task and DeepSeek's habits, not from who it is told to be.

### What it cost

$2.25 ($18.01 to $15.76). All three rounds together: $6.09.
