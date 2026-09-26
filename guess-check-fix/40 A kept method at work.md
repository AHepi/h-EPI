# A kept method at work

Log entry 40. Log 39's kept fix-acceptance methods, put to work in the checker's own correction loop. The plan, aims and five conjectures were committed before the run ("40 Plan - a kept method at work.md"). Every number here comes from `runs/40 kept method at work/records.json`. No AI was called: the methods DeepSeek wrote in log 39 ran as they were, on this computer.

## The short answer

- **The change operated where it was used.** On 64 held-out starts, the loop using DeepSeek's methods ended with 25, 11 and 28 nearby situations broken that the model had right at the start. With the current method it was 84; with log 17's person-written repair, 25. No start ended with more damage than under the current method, and more held-back jobs passed at the end: 200 to 202 of 216, against 194.
- **But by the aims I declared, none of them, the person's repair included, counts as a repair in the loop.** Each left a shown job failing on 3 or 4 starts where the current method got every shown job passing, and my plan protected exactly that. On every one of those starts, the current method had made the job pass only with a fix that broke 1 to 8 nearby situations. The stricter methods refused every such fix and stopped with nothing broken.
- **So the two aims I declared conflict on those starts.** Passing every shown job and breaking nothing that was right could not both be had. That is a finding about my aims, not a fault the runs can pin on the methods. Which to keep is a choice the semantics leaves to whoever declares the aims.

## An example first

The reminder app, starting from a model with a planted mistake. Every one-step change that makes the failing shown job pass also changes how some nearby situations end. With the current method, the loop takes the first such change. The shown job then passes, but 8 nearby situations the model had right are now wrong, and only 2 of the 4 held-back jobs pass.

With DeepSeek's repeat-2 method, the loop asks the world about the changed situations for each candidate. It finds each one breaks something, rejects them all, and stops. The shown job still fails, nothing is broken, and all 4 held-back jobs pass.

## Everything

The 64 held-out starts, in the eight worlds DeepSeek never saw in log 39:

| Method | Total damage | Starts with damage | Starts with every shown job passing | Held-back jobs passing | Questions asked | Starts losing P1 |
|---|---|---|---|---|---|---|
| current method | 84 | 16 | 60 | 194/216 | 0 | - |
| log 17's repair (a person) | 25 | 9 | 57 | 203/216 | 215 | 3 |
| DeepSeek's method, repeat 1 | 25 | 4 | 57 | 200/216 | 229 | 4 |
| DeepSeek's method, repeat 2 | 11 | 6 | 56 | 202/216 | 229 | 4 |
| DeepSeek's method, repeat 3 | 28 | 6 | 57 | 200/216 | 216 | 3 |

No method failed to run, and none ended any start with more damage than the current method.

The starts losing P1 (every shown job passing under the current method, not under the stricter one):

| World | Current method: damage, held-back passing | Stricter methods: damage, held-back passing |
|---|---|---|
| reminder app | 7, 3 of 4 | 0, 3 of 4 (all four methods) |
| reminder app | 8, 2 of 4 | 0, 4 of 4 (three methods; not repeat 3) |
| moving day | 3, 1 of 3 | 0, 2 of 3 (all four) |
| moving day | 1, 2 of 3 | 0, 0 of 3 (repeats 1 and 3) |
| plant watering | 8, 4 of 4 | 0, 2 of 4 (repeat 2) |

So refusing the damaging fix helped the held-back jobs in three of these starts and hurt them in two.

The 16 starts in the two worlds log 39 showed DeepSeek:
- damage: current method 21; the person's repair and all three of DeepSeek's methods 2 each;
- shown jobs all passing: 12 for the current method, 10 for each of the others.

## The conjectures

1. **Each of DeepSeek's methods ends with less total damage than the current method.** *Not ruled out:* 25, 11 and 28 against 84.
2. **Each ends with no more damage than the person's repair.** *Ruled out for repeat 3* (28 against 25). Repeat 1 equals it (25); repeat 2 has less (11).
3. **Each keeps P1 on every held-out start.** *Ruled out:* each lost it on 3 or 4 starts, and so did the person's repair (3). By the declared aims, no method is a repair in loop use.
4. **Each asks fewer questions than the person's repair.** *Ruled out:* 229, 229 and 216 against 215. One decision at a time (log 39) they asked fewer; in the loop they rejected more candidates before accepting one, and asked about each.
5. **Each ends with at most half the current method's damage (42).** *Not ruled out:* 25, 11, 28.

## What this means for the idea

- **The method DeepSeek changed does its job where it is used.** Across the loop it prevented most of the damage the current method let through, never did worse on any start, and left more unseen jobs passing. That is operative return, in the semantics' words: the change affected how the system proceeds.
- **My aims were the weak point.** I protected "every shown job the current method repairs", not seeing that on some starts the only repairs available break something. When the aims conflict, the semantics says a system faces a recognized difficulty, and which aim to drop is a choice (Parts X and XI). That choice was mine to make in advance, and I made it without seeing the conflict. The plan is kept as it was.
- **Less damage partly comes from accepting less.** The traps in the plan named this: on the starts losing P1, the stricter methods stopped rather than accept a damaging fix. Held-back jobs going both ways on those starts shows this is a real trade, not a free gain.
- **Repeat 2's method, the one that looks first at situations like the jobs that already passed, did best:** 11 against 25. That fits log 39, where it also caught the most bad fixes (20 of 24). Three repeats are too few to say more.

## What was not tested

- Aims that do not conflict: for example, protecting only held-back jobs, or allowing a shown job to stay failing when every fix breaks something.
- The methods inside the full loop with DeepSeek writing new parts (log 17's "full loop"), not only the checker's small fixes.
- Whether the system can find a method's failure itself.

## What it cost

No DeepSeek credit.

## Traps

- **Reading "no method is a repair" as the methods failing.** The protected aim I chose conflicts with the aim to repair on the starts where it failed.
- **Reading less damage as better models overall.** On the starts where it stopped early, held-back jobs went both ways.
- **Reading the 16 starts in the shown worlds as held out.**
