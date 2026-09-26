# Changing a method

Log entry 39. A test of condition 6 from log 33: can the system change one of its own methods, under the revised semantics' repair (P)? The plan, the aims, the occasions and five conjectures were committed before any DeepSeek call ("39 Plan - changing a method.md"). Every number here comes from the records in `runs/39 changing a method/`, made with DeepSeek V4.1 Flash at its default thinking setting on 26 September 2026.

## The short answer

- **Yes, for this method: every method DeepSeek wrote was kept.** The program kept a new fix-acceptance method only if, on 72 fixes from eight worlds DeepSeek never saw, it rejected at least one fix that broke something no job checks. It also had to accept every fix that broke nothing, reject every fix that lost a job, and never fail. All six methods met all of that.
- **Shown the failure, DeepSeek did better than the person who repaired it in log 17.** Its three methods rejected 16, 20 and 18 of the 24 held bad fixes. Log 17's repair, written by a person, rejects 13. It found a better way to spend its three questions to the world.
- **Told only the aim, DeepSeek wrote the person's repair exactly.** All three methods made the same 72 decisions, and asked the same 137 questions, as log 17's repair.
- **What DeepSeek said its methods do matches what the record shows they did,** read by hand. My automatic check of this was too narrow and missed three of the six sentences.

## An example first

The checker has models with a planted mistake. For each, its small-fix search finds changes that make a failing job pass. The current method accepts such a fix if it repairs a job and loses none. That is how log 17 accepted a fix that switched off a correct rule: no job checked what the rule did.

A new method may look at 40 nearby situations, with what the model said before and after the fix, and may ask the world about three of them.

In repeat 2, shown two fixes the current method wrongly accepted, DeepSeek's first method got 15 of the 18 shown fixes right. After the report of which it got wrong, its second got all 18. It said of that method:

> "It accepts a fix only if it repairs at least one job without breaking any passing job, then checks up to three nearby situations most similar to jobs that were already passing (or repaired if none), rejecting if any was correct before the fix and wrong after."

The code does exactly that:
- it drops situations that are a job itself;
- it scores the rest by how many words they share with the names of jobs that passed before the fix;
- it asks the world about the top three.

The idea is new here, in that neither the person's repair nor the instruction contained it: a fix most likely breaks what was right near the jobs that were already right. On the held fixes it rejected 20 of 24 bad ones, where the person's repair rejects 13.

## Everything

Held occasions: 72 fixes in eight worlds, 24 of each kind. None was shown to DeepSeek.

| Method | Kept | Held bad fixes rejected (of 24) | Good fixes not accepted | Losing fixes accepted | Errors | Questions asked |
|---|---|---|---|---|---|---|
| current method | no | 0 | 0 | 0 | 0 | 0 |
| log 17's repair (written by a person) | yes | 13 | 0 | 0 | 0 | 137 |
| shown the failure, repeat 1 | yes | 16 | 0 | 0 | 0 | 116 |
| shown the failure, repeat 2 | yes | 20 | 0 | 0 | 0 | 118 |
| shown the failure, repeat 3 | yes | 18 | 0 | 0 | 0 | 112 |
| told the aim, repeat 1 | yes | 13 | 0 | 0 | 0 | 137 |
| told the aim, repeat 2 | yes | 13 | 0 | 0 | 0 | 137 |
| told the aim, repeat 3 | yes | 13 | 0 | 0 | 0 | 137 |

Rounds in the shown arm, on the 18 shown fixes:
- repeat 1: all 18 right first time;
- repeat 2: 15, then 18;
- repeat 3: 17, then 18.

**Produced by the change:** each method ran on the same 72 occasions, with the same data, as the current method and the person's repair. The only difference is the method. Every question each asked the world is in the record, kept by the program, not reported by the method.

## The conjectures

1. **Shown the failure, DeepSeek's method is kept in at least 2 of 3 runs.** *Not ruled out:* 3 of 3.
2. **Every kept method rejects at least half of the 24 held bad fixes.** *Not ruled out:* 13 to 20.
3. **Told the aim but not shown a failure, at most 1 of 3 methods is kept.** *Ruled out:* 3 of 3 were kept. Each was the person's repair, decision for decision.
4. **What DeepSeek says and what the record shows agree on whether it asks the world, in every run.** *By the planned check, ruled out:* it counted three disagreements. But the check was mine and too narrow: it looked for words like "ask" or "the world" and missed "checks up to three changed nearby situations". Read by hand after the results, all six sentences describe asking about nearby situations, and every method did ask.
5. **No DeepSeek method rejects more held bad fixes than log 17's repair while keeping every protected aim.** *Ruled out:* 16, 20 and 18.

## What this means for the idea

- **This exhibits a bypass to one proposed barrier.** The barrier: "the system cannot repair its own fix-acceptance method without a person writing the change". DeepSeek proposed the change; the program checked it against declared aims on fixes it never saw, and kept it. That rules the barrier out for this method and these occasions, for whoever accepts the records and the declared aims as premises. It does not show the system can revise any method.
- **What people still supplied:** the aims, the occasions, the choice of which method to open up, and the tool it could use (three questions to the world). In the semantics' terms these are declared inputs, and where the boundary is drawn decides whether the whole counts as the system's own.
- **Stating the aim was enough to get the obvious repair; showing the failure got a better one.** This refines log 38. Telling DeepSeek to "doubt" (log 30) changed nothing, because doubt is a disposition with nothing to run. Here the aim named an operation the program could carry out (ask the world, compare with before and after), and DeepSeek wrote it. Being shown concrete failures, and told which of its decisions were wrong, led it to something neither the instruction nor the person had: where to look first.
- **Knowing and operating came together here.** What DeepSeek said its method does matched what the record shows it did. That is the reverse of logs 30 to 32, where it could state a rule that did not operate. The difference: here the program ran what it wrote, and kept only what worked.

## What was not tested

- A method other than fix acceptance, or a change to the checker's language or aims.
- The kept method used inside the full loop over many rounds; here each decision was judged one at a time.
- Whether DeepSeek can find a method's failure itself. The failure was shown to it.
- Other models, more repeats, bigger worlds.

## Failures along the way

- **My check of whether DeepSeek's sentence says it asks the world was too narrow** (conjecture 4). It is kept as it was; the hand reading is reported beside it.
- **A design check before the run:** the current method accepts all 30 bad fixes; the person's repair rejects 19 of 30 (13 of the 24 held). So the occasions can tell a repair from a non-repair.

## What it cost

$0.08 of DeepSeek credit ($14.30 to $14.22).

## Traps

- **Reading "kept" as "the best method".** A kept method met the declared aims on these occasions; the semantics' repair orders nothing.
- **Reading the shown arm's better scores as settled.** Three repeats, 24 bad fixes each; the word-overlap idea relies on how nearby situations are described ("job X, but ..."), which may not carry over.
- **Reading this as the system changing its method by itself.** DeepSeek proposed; the program, with aims a person declared, decided.
