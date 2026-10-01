# Rivals choose the questions

Log entry 46. On the grudge, instead of DeepSeek choosing what to ask the world, DeepSeek wrote four rival explanations as small programs, and the program asked the world about the situations where the rivals disagreed most. The plan and six conjectures were committed before any DeepSeek call ("46 Plan - rivals choose.md"). Every number here comes from the records in `runs/46 rivals choose/`, made with DeepSeek V4.1 Flash at its default thinking setting and a reply limit of 200,000 tokens, on 27 September 2026.

## The short answer

- **The rivals got the world asked the right questions.** In 4 of 6 runs the world was asked about a sequence that shows a deep grudge, against 1 of 12 in log 45, where DeepSeek chose its own questions.
- **DeepSeek then built new kinds of explanation.** 5 of the 6 final rules had a new part: levels of anger, an apology that fails after two insults in a row. Random answers gave 4 running scores and 2 unresolved-insult counts, both old habits. The nearest rule to the true grudge any run has written came from here, and it got 105 of 106.
- **More cases right, but not the true grudge.** Rivals choose got 559 of 636, random answers 527. No final rule was the true grudge.
- **Once the right explanation, for these sequences, was on the table and was lost.** In one run, one of the four rivals agreed with the world on all 120 sequences. But the final DeepSeek sees only the facts, never the rivals, and wrote a different rule that got 86. Nothing in the system keeps a rival that survives.

## An example first: repeat 2

Round 1, a fresh DeepSeek wrote four rivals. They included "a trust score: apology and gift add 1, insult subtracts 2", and "an anger level: apologies clear anger of 0 or 1 but only reduce higher anger by 1". They disagree about "insult, insult, apologise, apologise", so the program asked the world. The world said cold. That one fact refutes the unresolved-insult count, in which two apologies after two insults mend everything.

The final fresh DeepSeek, given that fact and five others, wrote: "Three hidden states: Warm, Upset (cold but recoverable), and Angry (cold and permanent). Insult: Warm to Upset, Upset to Angry. Apologise: Upset to Warm; Angry stays Angry. Gift: no change." That is the true grudge's three levels, except that in the true grudge a gift softens Angry to Upset. 105 of 106.

## Everything

| Arm | Every case right (of 106, summed over 6) | By repeat | The two telling sequences right (of 12) | Answers from the world | Runs where the world was asked a telling sequence | Replies cut off |
|---|---|---|---|---|---|---|
| random answers | 527 | 104, 80, 81, 80, 79, 103 | 5 | 36 | - | 0 |
| rivals choose | 559 | 104, 105, 86, 94, 80, 90 | 7 | 35 | 4 | 0 |

For scale: the true grudge 106, the unresolved-insult count 104, the running score 81.

The rivals: 48 written, all 48 ran on every sequence, and all 48 fitted every fact known when they were written. One agreed with the world on all 120 sequences (repeat 3, round 2).

The final rules, read by hand, blind to arm (the list was mixed this time; checked by a test):

| Arm | true grudge | unresolved-insult count | running score | other |
|---|---|---|---|---|
| random answers | 0 | 2 | 4 | 0 |
| rivals choose | 0 | 0 | 1 | 5 |

Rivals choose, run by run:

| Repeat | Telling sequence asked | Final rule | Right of 106 |
|---|---|---|---|
| 1 | no | an apology fails after two insults in a row; a gift resets the count of insults in a row | 104 |
| 2 | yes | Warm, Upset, Angry; an apology cannot mend Angry; a gift does nothing | 105 |
| 3 | yes, both | a parity rule on the last run of insults and the number of apologies | 86 |
| 4 | no | three levels of mood starting at neutral | 94 |
| 5 | yes | a running score (insult -2, apology +1, gift +2) | 80 |
| 6 | yes | resentment and goodwill | 90 |

## The rival that matched, and was lost

In repeat 3, round 2, one rival said: "hidden anger plus last action; consecutive insults sting more, and an apology immediately after a gift wipes anger clean". It agrees with the world on all 120 sequences of up to four actions. It is not the true grudge by another name. A check I ran after the results, not in the plan, shows it differs from the world on 2 of the 243 five-action sequences, such as "insult, insult, apologise, apologise, apologise". It is a different explanation that happens to fit everything up to four actions.

The program knew it fitted every fact, but so did the other three rivals of that round. The final DeepSeek was given only facts, as the plan said, and wrote a parity rule that got 86.

## The conjectures

1. **No reply is cut off.** *Not ruled out:* none was.
2. **Rivals choose gets more of the 106 cases right than random answers.** *Not ruled out:* 559 against 527.
3. **In at least 3 of 6 runs, the world is asked a telling sequence.** *Not ruled out:* 4 of 6.
4. **In at least 1 run, some rival agrees with the true grudge on all 120 sequences.** *Not ruled out:* 1, in repeat 3. It is a different explanation that agrees up to four actions.
5. **At least 1 final rule is the true grudge.** *Ruled out:* none.
6. **Every rivals-choose final rule gets at least 81.** *Ruled out:* repeat 5 got 80.

## What this means for the idea

- **Rival explanations can find the questions that matter, where DeepSeek's own commitments could not.** DeepSeek could imagine rivals that differ from its first habit, and the program, by finding where they disagree, put the world's answer exactly where it bites. In the semantics' terms, criticism came from outside the conjecture (the world), and was aimed by a structure the system built from several conjectures, not by DeepSeek's view of its own.
- **Facts that bite led to construction, not just re-tuning.** Five of six final rules added a new kind of hidden part. In log 45 only one run was asked such a question, and it too bent its rule towards a deep grudge; here it happened in most runs, so this is the clearest sign so far that the questions asked change the kind of explanation DeepSeek writes, not only its weights.
- **But new is not right.** Three of the five new explanations got fewer cases right than the old unresolved-insult count, which random answers reached twice. A new part that fits six facts can be wrong everywhere else.
- **The system lacks retention.** A rival that fitted every fact, and agreed with the world on every sequence tested, was thrown away because the next step saw only facts. The semantics' "a change is kept only if ..." needs something that keeps. The next step here is obvious: carry the surviving rivals forward, test them against each other, and keep the ones not refuted.

## Failures along the way

- **One test was wrong before the run.** My check that the reading list names no arm also read the heading, which names the plan file, "46 Plan - rivals choose.md", and so contains "rivals". Narrowed to the rule lines; the program was unchanged.
- **Log 45's scramble fault is fixed here:** a seeded shuffle, and a test that the arms are mixed. The key shows them mixed.
- **The five-action check of the matching rival was not planned.** It is reported as a check made after the results.

## What was not tested

- Keeping the surviving rivals and letting them compete across rounds.
- Showing the final DeepSeek the rivals that survived, not only the facts.
- Longer sequences in the grading, where the matching rival and the true grudge differ.
- Other devices.

## What it cost

$0.35 of DeepSeek credit ($12.70 to $12.35).

## Traps

- **Reading "other" as "better".** Five new kinds of explanation, three of them worse than the old count.
- **Reading the matching rival as DeepSeek finding the true grudge.** It fits every sequence up to four actions and is wrong beyond.
- **Six repeats are not settled.** Random answers here scored 527; in log 45, 556.
