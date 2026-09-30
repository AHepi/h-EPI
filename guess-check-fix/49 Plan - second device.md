# Plan: a second device, the heater

Written before any DeepSeek call for log 49, and not to be changed after. The results go in "49 Second device.md".

## What the owner asked

"Do it": log 48's next step. Every result from log 44 to 48 was about one device, the grudge. Before trusting the pattern, take it to a second device where common sense points the wrong way.

## The device ("49 heater.js")

A small room has an electric heater with a dial. You can turn the dial up, turn it down, or wait. All you can see is whether the room is warm or cold.

- **Common sense:** turning it up makes the room warm, turning it down makes it cold, waiting does nothing.
- **The truth:** the heater starts on low (room warm) and has three settings, off, low and high, plus a safety cut-out. Turning up on high trips the cut-out and the room goes cold. While tripped, the dial does nothing; only waiting resets it, to off.

## A design fault found and fixed before the plan

My first version started the heater off. Checking it offline, a wrong rival ("turning the dial down also resets the cut-out") got all 106 short sequences right and all but 9 of the 972 long ones, because tripping took three turns up and left almost no room to show a reset. The heater now starts on low, so two turns up trip it.

Checked offline, with log 25's way of choosing the 14 observations and 12 test cases:

| Rule | Observations fitted (of 14) | Short right (of 106) | Long right (of 972) |
|---|---|---|---|
| true heater (a hand-written copy, which matches the device everywhere) | 14 | 106 | 972 |
| common sense | 7 | 83 | 741 |
| a count of ups minus downs, warm at 1 or 2 | 13 | 100 | 836 |
| turning down also resets the cut-out | 13 | 106 | 942 |
| turning up while tripped resets it to low | 11 | 103 | 893 |

**This device differs from the grudge in one way that matters.** On the grudge, a wrong common-sense rule (the running score) fitted all 14 observations. Here common sense fails half the observations, and every wrong rule I could think of fails at least one. So plain DeepSeek may simply get it right. If it does, this device cannot show the grudge's pattern, and the report will say so.

## The run

Three arms, six repeats each; DeepSeek V4.1 Flash, default thinking, reply limit 200,000. Every arm ends with a fresh DeepSeek that sees the observations and whatever answers from the world its arm collected, and writes one explanation as a small JavaScript function. The world refuses log 25's 12 test cases.

- **Bare:** no answers from the world.
- **Random answers:** the world's answers about 6 random unseen situations of up to four actions.
- **Rivals choose (as log 46):**
  - two rounds; each round a fresh DeepSeek writes 4 rival functions fitting every known fact;
  - the program asks the world about the 3 situations of up to four actions where the fitting rivals are most evenly split;
  - the final DeepSeek sees the facts only, not the rivals (logs 47 and 48 found showing them did not help).

## What is measured

Each final function is run (in log 34's sealed-off process) on every sequence of one to six actions that is not an observation:
- **short:** 106 sequences of up to four actions, 23 of them hard (common sense gets them wrong);
- **long:** 972 of five or six actions.

Also: whether it is the true heater everywhere; every rival and whether it fitted; DeepSeek's one-line comment on each explanation.

## Conjectures, written before the run

1. **No reply is cut off.**
2. **Bare DeepSeek is the true heater everywhere in at most 3 of 6 runs.** If it is right more often, the device is too easy to test the grudge's pattern.
3. **Rivals choose gets more long sequences right than bare,** summed over six repeats.
4. **Rivals choose gets more long sequences right than random answers.**
5. **Rivals choose is the true heater everywhere in more runs than random answers.**
6. **At least one rival across all runs is the true heater everywhere.**

## What would count against the grudge's pattern holding here

- Rivals choose does no better than random answers on long sequences: then choosing questions by the rivals' disagreement, which helped on the grudge, does not help here.

## Cost

About $0.40 to $0.60: per repeat, one call for bare, one for random answers, three for rivals choose.

## Traps

- **Reading a bare success here as DeepSeek beating the grudge's habit.** The observations here refute common sense directly; on the grudge they did not.
- **Reading one extra device as a general result.** Two devices are still two.
- **Six repeats are not settled.**
