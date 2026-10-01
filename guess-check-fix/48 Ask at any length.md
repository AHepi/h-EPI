# Ask at any length

Log entry 48. Log 47 again, with one change: the world could be asked about any situation of up to six actions where the standing rivals disagreed, not only up to four. The plan and six conjectures were committed before any DeepSeek call ("48 Plan - ask at any length.md"). Every number here comes from the records in `runs/48 ask at any length/`, made with DeepSeek V4.1 Flash at its default thinking setting and a reply limit of 200,000 tokens, on 30 September 2026.

## The short answer

- **Keeping the survivors still did not help; it did worse.** Long sequences right, of 5,832: shown the facts only 5,527, shown the survivors 5,028, survivors' vote 3,259. The plan named this as counting against the idea that testing survivors where they differ was what was missing.
- **The long questions killed the rivals.** Rivals disagree most on six-action sequences, so almost every question was six actions long (38 of 54), and each answer refuted most of the rivals. Two runs ended with no survivor at all, and the others with one or two, often strange ones ("each earlier action counts 0.7 times as much").
- **The facts themselves helped.** A fresh DeepSeek shown only the facts did better on long sequences than in log 47 (5,527 against 5,282), because some of its facts were now about long sequences. It still never wrote the true grudge.
- **The telling short sequences were never asked.** Asking at any length pulled every question to where rivals split most, which was always long. So the situations that show a deep grudge most plainly ("insult, insult, apologise, apologise") were asked in 0 of 6 runs, against 4 of 6 in log 47.

## An example first: repeat 3

Round 1: four rivals fitted every fact; the world was asked three six-action situations; two rivals were refuted. Round 2: four new ones joined; three more questions, five and six actions long; three survivors. Round 3: four more joined; three six-action questions refuted all seven. Nothing survived.

The survivors' vote had nothing to vote with. Shown the survivors, a fresh DeepSeek got an empty list (see Failures) and wrote a grudge counter with a special case for two apologies in a row: 91 of 106 short, 857 of 972 long. Shown the facts only, a fresh DeepSeek wrote a similar counter: 101 and 938.

## Everything

| Final answer | Short right (of 106 per run, summed over 6) | Long right (of 972 per run, summed over 6) | By repeat (short / long) | Telling sequences right (of 12) |
|---|---|---|---|---|
| survivors vote | 378 | 3,259 | 86/787, 0/0, 0/0, 90/753, 105/922, 97/797 | 4 |
| shown the survivors | 563 | 5,028 | 86/787, 86/787, 91/857, 90/753, 105/922, 105/922 | 7 |
| shown the facts only | 620 | 5,527 | 105/921, 105/922, 101/938, 104/913, 104/913, 101/920 | 5 |

Log 47, for comparison (long right): vote 5,087, shown the survivors 5,225, shown the facts only 5,282.

- **The world's 54 answers, by length:** 1 of three actions, 6 of four, 9 of five, 38 of six. Every run asked at least one of five or six actions.
- **Rivals:** 72 written, all ran, all fitted every fact known when written; none agreed with the true grudge everywhere.
- **Survivors at the end, by repeat:** 1, 0, 0, 1, 1, 2. The vote was undecided on every sequence in the two runs with none (1,092 each), and on 129 in repeat 6.
- **Shown the survivors copied one** in 3 of the 4 runs that had survivors.
- **No reply was cut off.**

## The conjectures

1. **No reply is cut off.** *Not ruled out.*
2. **In at least 4 of 6 runs, the world is asked about five or six actions.** *Not ruled out:* 6 of 6.
3. **Shown the survivors gets more long sequences right than in log 47 (5,225).** *Ruled out:* 5,028.
4. **In this run, shown the survivors gets at least as many long sequences right as shown the facts only.** *Ruled out:* 5,028 against 5,527.
5. **The survivors' vote gets more long sequences right than in log 47 (5,087).** *Ruled out:* 3,259, with two runs having no survivors.
6. **In at least 1 run, a survivor agrees with the true grudge everywhere.** *Ruled out.*

## What this means for the idea

- **Keeping rivals has now failed twice, for two different reasons.** In log 47, survivors were tested too little, so poor ones lived. Here they were tested hard, so nearly all died, and the few left were whatever happened to fit. Either way, "not yet refuted" did not pick out a good explanation, and handing survivors to DeepSeek made its answer worse, because it mostly copied one.
- **What the world is asked matters more than what is kept.** Long questions made the facts-only answer better on long sequences; short telling questions (log 47) produced the "gift softens a deep grudge" part. No choice of questions so far got both.
- **Choosing questions by "where the rivals split most" has a blind side.** It goes where the current rivals differ most, which is not where the true explanation differs from them. The telling situations were never most disputed here. That is the same limit log 45 found in DeepSeek's own questions, moved from DeepSeek into the program.
- **In the semantics' terms:** criticism from outside (the world) did real work every time; retention by survival alone did not add anything. Something would have to prefer among survivors, or among what to ask, and the revised semantics deliberately leaves that choice outside the theory (log 37).

## Failures along the way

- **The checks were slow today.** The repository's full checks took several minutes instead of under one; they passed, and the plan was committed before the run.
- **An empty survivor list was shown as if it held rivals.** In repeats 2 and 3 no rival survived, but the "shown the survivors" DeepSeek still got the sentence "These rival explanations fit every observation above:" followed by nothing. My test never tried a run with no survivors. In those two runs that arm scored 86 and 91 short against the facts-only arm's 105 and 101. I cannot tell whether the stray sentence caused that. The records are left as they are; the code is not changed yet.

## What was not tested

- A mix of questions: some where rivals split most, some short situations.
- Any way of preferring among survivors other than survival.
- Another device. Every result from log 44 on is about the grudge.

## What it cost

$0.45 of DeepSeek credit ($12.05 to $11.60).

## Traps

- **Reading this as "rivals do not help".** Rivals choosing the questions helped in log 46; keeping them for the final answer is what failed, twice.
- **Comparing with log 47 as one experiment.** Different days; within this run, facts only beat both survivor answers.
- **Six repeats are not settled.**
