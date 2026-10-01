# Plan: keep the survivors

Written before any DeepSeek call for log 47, and not to be changed after. The results go in "47 Keep the survivors.md".

## What the owner asked

"Ok do it": log 46's next step. In log 46, rival explanations chose the world's questions well, but in one run a rival that fitted every fact was thrown away: the final step saw only facts. Here, rivals that survive are kept.

## The run

- **Device:** the grudge, with log 25's 14 observations. The world refuses log 25's 12 test cases, and answers only situations of up to four actions.
- **Three rounds.** Each round:
  - a fresh DeepSeek sees the observations, the world's answers so far, and the code of every rival still standing;
  - it writes 4 new rivals, as small programs, that fit every fact and differ from the standing rivals and each other where nobody has looked;
  - the program runs them in log 34's sealed-off process, adds those that fit every known fact to the standing rivals, and asks the world about the 3 situations where the standing rivals are most evenly split;
  - any standing rival an answer refutes is dropped.
- **Three final answers from the same run,** differing only in what the last step sees:
  - **survivors vote:** no DeepSeek; each case is answered by the majority of the survivors; a tie is no answer;
  - **shown the survivors:** a fresh DeepSeek sees the observations, the facts and the survivors' code, and writes one final function;
  - **shown the facts only:** a fresh DeepSeek sees the observations and the facts, and writes one final function.
- **Six repeats.** DeepSeek V4.1 Flash, default thinking, reply limit 200,000.

## What is measured

Every final answer is graded by running it on every sequence of one to six actions that is not an observation:
- **short:** 106 sequences of up to four actions, as in logs 45 and 46;
- **long:** 972 sequences of five or six actions, which no one is ever asked about. A rule that is right only where it was checked shows itself here.

For scale, measured before this run:

| Rule | Short (of 106) | Long (of 972) |
|---|---|---|
| true grudge | 106 | 972 |
| log 46's matching rival | 106 | 961 |
| Warm, Upset, Angry, with gifts doing nothing (log 46's best final rule, as I would write it) | 105 | 922 |
| unresolved-insult count | 104 | 913 |
| running score | 81 | 628 |

Also recorded: every rival; which survived; which agree with the true grudge on every sequence up to six actions; which final functions act exactly as a survivor; the telling sequences; ties in the vote.

There is no hand reading this time: every final answer is a program, graded by running it.

## Conjectures, written before the run

1. **No reply is cut off.**
2. **Shown the survivors gets more long sequences right than shown the facts only,** summed over six repeats.
3. **The survivors' vote gets more long sequences right than shown the facts only.**
4. **In at least 2 of 6 runs, a survivor at the end agrees with the true grudge on every sequence up to six actions.**
5. **In at least 1 of 6 runs, the shown-the-survivors final function is the true grudge everywhere.**
6. **In at least 4 of 6 runs, the world is asked a telling sequence.**

## What would count against the idea that keeping survivors matters

- **Shown the survivors does no better than shown the facts only, and the vote no better either.** Then keeping the rivals adds nothing at the last step, and log 46's loss was a one-off.

## Cost

About $0.50 to $1: per repeat, 3 rival rounds (longer prompts than log 46, since the survivors' code is shown) and 2 final functions.

## Traps

- **Reading a survivor that agrees everywhere up to six actions as the true grudge.** Longer sequences could still tell them apart.
- **Reading the vote as DeepSeek's answer.** The vote is the program's, made from DeepSeek's rivals.
- **Comparing with log 46 directly.** This run asks the world 9 questions, log 46 asked 6.
- **Six repeats are not settled.**
