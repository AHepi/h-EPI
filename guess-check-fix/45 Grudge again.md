# The grudge again

Log entry 45. On the grudge, where DeepSeek's first explanation is wrong, does a fresh DeepSeek given only facts ("rebuild fresh") end with a better explanation than one told its own mistakes in the same conversation ("defend")? The plan, the categories for reading rules and six conjectures were committed before any DeepSeek call ("45 Plan - grudge again.md"). Every number here comes from the records in `runs/45 grudge again/`, made with DeepSeek V4.1 Flash at its default thinking setting and a reply limit of 200,000 tokens, on 27 September 2026.

## The short answer

- **Your prediction did not hold here.** Defend got more cases right than rebuild fresh (598 against 563 of 636) and ended on the old running score less often (1 of 6 runs against 3 of 6). No reply was cut off, so this time there is no such excuse. This is what the plan named as counting against the prediction.
- **What decided each run was whether the world contradicted the running score, not which arm it was in.** All 12 attack runs started with the same running score. The runs that stayed on it were the ones the world never contradicted enough: one rebuild fresh run got no answers from the world at all, because every commitment it chose was a test case the world refuses, and one defend run had every tested prediction come out as it said.
- **No run found the true grudge.** The best rule, reached in 9 of 18 runs across all three arms, was the unresolved-insult count, right on 104 of 106 cases. Only one run was ever shown what happens after a deep grudge, and that run bent its rule towards it.

## An example first

**Defend, repeat 3.** Round 1: "a score starting at 0; each insult subtracts 1, each apologise or gift adds 1". The world said "apologise, gift, insult" ends cold, not warm as predicted. In the same conversation, round 2: "an unseen count of unapologized insults: insult adds 1, apology subtracts 1 but not below 0, gift does nothing". 104 of 106. It did not defend its first answer; it dropped it.

**Rebuild fresh, repeat 1.** Every commitment it chose, in both rounds, was one of the 12 test cases the world will not answer. So the final fresh DeepSeek got nothing but the 14 observations, and wrote the running score. 81 of 106.

## Everything

| Arm | Every case right (of 106, summed over 6) | By repeat | The two telling sequences right (of 12) | Answers from the world | Replies cut off |
|---|---|---|---|---|---|
| random answers | 556 | 84, 84, 104, 84, 104, 96 | 4 | 36 | 0 |
| attack, rebuild fresh | 563 | 81, 104, 104, 83, 104, 87 | 3 | 22 | 0 |
| attack, defend | 598 | 104, 104, 104, 101, 104, 81 | 2 | 27 | 0 |

For scale: the true grudge would get 106, the unresolved-insult count 104, the running score 81.

The final rules, read by hand:

| Arm | true grudge | unresolved-insult count | running score | other |
|---|---|---|---|---|
| random answers | 0 | 2 | 3 | 1 |
| attack, rebuild fresh | 0 | 3 | 3 | 0 |
| attack, defend | 0 | 4 | 1 | 1 |

Two rules I filed with notes before seeing the arms (in "hand reading notes.md"):
- one defend rule is the count with a cap at 2, one step towards the true grudge's "deep";
- one random-answers rule says two insults in a row before the last apology leave Robin cold, the nearest any rule came to "an apology cannot mend a deep grudge".

## Where the runs went

Every attack run, in both arms, started round 1 with the running score.

| | Moved to the unresolved-insult count or other | Stayed on a running score |
|---|---|---|
| rebuild fresh | repeats 2, 3, 5 | repeat 1 (no answers from the world at all); repeats 4 and 6 (contradicted, but only rewrote the weights: insult subtracts 2, or 5) |
| defend | repeats 1, 2, 3, 4, 5 | repeat 6 (every tested prediction held, so nothing contradicted it) |

Only one run, defend repeat 4, was answered by the world on a telling sequence ("insult, insult, apologise, apologise"). Its final rule ("no two insults in a row, and it ends with an apology") is the one that tries to account for a grudge an apology cannot mend. It got 101: better than the running score, worse than the count.

## The conjectures

1. **No reply is cut off.** *Not ruled out:* none was.
2. **Rebuild fresh gets more of the 106 cases right than defend.** *Ruled out:* 563 against 598.
3. **Fewer of rebuild fresh's final rules are running scores than defend's.** *Ruled out:* 3 against 1.
4. **Defend ends on a running score in at least 3 of 6 repeats.** *Ruled out:* 1 of 6.
5. **Rebuild fresh gets at least as many of the 106 right as random answers.** *Not ruled out,* barely: 563 against 556.
6. **No more than 2 of the 18 final rules are the true grudge.** *Not ruled out:* none was.

## What this means for your prediction and for the semantics' reading of DeepSeek

- **Your prediction, that DeepSeek told its mistakes in the same conversation defends its first answer, is ruled out for DeepSeek on this device and this way of telling it.** It dropped its first answer as readily as a fresh DeepSeek, and more often, in five of six runs. Log 44's grudge rows, which seemed to support the prediction, were two runs against three and are outweighed here.
- **What moved DeepSeek was contradiction from the world.** In every run where the world contradicted a prediction, DeepSeek changed its rule, in either arm; in two rebuild fresh runs the change was only new weights on the running score. In the two runs where nothing contradicted it, one in each arm, it kept the running score. That fits log 23, where DeepSeek changed its mind when a surprise came as a fact.
- **So the semantics' reading needs narrowing, not the prediction alone.** Log 26's plan read "its own answer in its context" as an input that stops criticism from having bearing. Here, its answer in its context did not stop it. What the records show is narrower: repeating or rereading its own answer without new facts leaves it unchanged (log 25), and new facts that contradict it change it, whether or not its old answer is in view.
- **Rebuild fresh has a cost the plan did not foresee.** A fresh DeepSeek does not know which situations the world already refused, and in repeat 1 it chose test cases in both rounds and learned nothing. Defend, in the same conversation, got 27 answers from the world against 22.
- **Why no run found the true grudge.** The 14 observations never show a deep grudge being mended, and the attack arms' commitments hit a telling sequence once in 12 runs. DeepSeek's commitments aim where its current rule and the obvious rule differ, not where its current rule and the true one differ. It cannot aim at a difference it has not imagined.

## Failures along the way

- **My "true explanation" in log 44 was wrong.** I wrote the true grudge from memory. Found while building this run; a correction note was added to "26 Attack surface.md" before this run.
- **The blind reading was less blind than planned.** My scramble of the 18 rules grouped them by arm, in three blocks of six; I found this only when I opened the key. My test checked that no arm was named, not that the arms were mixed. I did not know which block was which while reading, and the reading was saved before the key was opened, but a reader could have seen that each block of six had its own style.

## What was not tested

- Other ways of telling DeepSeek its mistakes, such as a direct criticism of its rule, not only the world's answers.
- Other devices where DeepSeek's first explanation is wrong.
- Whether a system that picks the situations where DeepSeek's own rival rules disagree would find the true grudge.

## What it cost

$0.48 of DeepSeek credit ($13.18 to $12.70).

## Traps

- **Reading this as DeepSeek being open to criticism in general.** It changed when the world contradicted a prediction it had committed to. That is one kind of criticism.
- **Reading 104 as the right explanation.** The unresolved-insult count is wrong on the two telling sequences.
- **Reading six repeats as settled.**
