# Finding the failure

Log entry 41. Can the system find a method's failure without being told what it is? The plan and four conjectures were committed before any DeepSeek call ("41 Plan - finding the failure.md"). Every number here comes from the records in `runs/41 finding the failure/`, made with DeepSeek V4.1 Flash at its default thinking setting on 26 September 2026.

## The short answer

- **Every reply that arrived named the failure, and pointed at the right cause.** Asked only "Is anything wrong with this method?", four replies came back. Each said the method ignores the nearby situations, so it can accept a fix that breaks something that was right. Three of the four methods written were kept on log 39's 72 held occasions. The fourth rejected every fix, good ones included.
- **With the record, two of the three replies never arrived.** DeepSeek thought until it hit its reply limit of 32,000 tokens and gave no answer. The one that finished found the failure in the record itself: "for example, Fix 2's 'clay ball at solid wall, but throw does not happen'", one of the nine breaks in it. Its method was kept.
- **Without the record, DeepSeek found it anyway, in all three runs.** So the record was not needed. This shows a flaw in my control: the method-only arm still described what a method can see and use, the nearby situations and the three questions to the world. A method that ignores inputs it is handed is an obvious thing to question. The failure was findable from the description alone.

## An example first

The method-only arm, repeat 1, got the method and the description of its inputs, and the question. It replied:

> "It ignores nearby situations, so it can accept a fix that repairs a job but breaks a nearby situation that the world says was correct before."

It then wrote log 17's repair. On the held occasions it made exactly the person's repair's decisions: 13 of 24 bad fixes rejected, nothing protected lost, 137 questions.

## Everything

| Arm, repeat | Reply | Changed the method | Kept | Held bad fixes rejected (of 24) | Good fixes not accepted |
|---|---|---|---|---|---|
| with the record, 1 | cut off at 32,000 tokens | - | - | - | - |
| with the record, 2 | cut off at 32,000 tokens | - | - | - | - |
| with the record, 3 | arrived | yes | yes | 13 | 0 |
| method only, 1 | arrived | yes | yes | 13 | 0 |
| method only, 2 | arrived | yes | no | 24 | 23 |
| method only, 3 | arrived | yes | yes | 13 | 0 |

No method accepted a losing fix or failed to run. Method only, repeat 2, rejected every fix whose nearby situations changed at all. That catches every bad fix, but it also rejects 23 of the 24 good ones, so it is not kept.

What each reply said is wrong:
- **with the record, 3:** "it ignores the nearby situations entirely, so it can accept a fix that changes a nearby case from a correct outcome to an incorrect one (for example, Fix 2's 'clay ball at solid wall, but throw does not happen')."
- **method only, 1:** "It ignores nearby situations, so it can accept a fix that repairs a job but breaks a nearby situation that the world says was correct before."
- **method only, 2:** "It ignores nearby situations, so it can accept a fix that changes a nearby situation from correct to incorrect."
- **method only, 3:** "It ignores nearby situations and the ask oracle, so it can accept a fix that repairs a job but breaks a nearby situation that was previously correct."

## The conjectures

1. **With the record, the changed method is kept in at least 2 of 3 runs.** *Ruled out:* 1 of 3. Two replies were cut off; the one that arrived was kept.
2. **With the method only, at most 1 of 3 is kept.** *Ruled out:* 2 of 3 kept, and all 3 named the failure.
3. **In every run, DeepSeek says something is wrong and changes the method.** *Ruled out by the two cut-off replies.* Every reply that arrived did.
4. **With the record, what DeepSeek says is wrong names fixes that break what no job checks, in at least 2 of 3 runs.** *Ruled out:* 1 of 3, the only one that arrived, and it cited a break from the record.

## What this means for the idea

- **DeepSeek can find this failure without being told, and write the repair.** But the evidence was not what led it there. With only the description of what a method can see, it saw that the method ignores inputs it is given, and reasoned out what could go wrong. That is finding a failure by criticism of the method itself, argument with no test, which the revised semantics allows. It is not finding it from the method's record.
- **Whether it can find a failure from evidence alone is still untested.** For that, the description would have to give no such hint. That is hard here, because the repair needs inputs the current method does not use, so the description has to mention them.
- **A long record made DeepSeek think itself out of an answer.** 14,000 characters of record, and two of three replies ran out of room. The same thing happened in logs 19 and 25. I did not raise the reply limit, though log 19 had shown how.
- **Knowing and operating agreed again.** Each reply that named the failure wrote a method that acts on it. Repeat 2 of the method-only arm overshot: it rejects every fix that changes anything nearby.

## What was not tested

- A description that does not hint at the failure.
- The record with a higher reply limit.
- A failure the method's description cannot point to.

## Failures along the way

- **My control was flawed:** "method only" still described the inputs the current method ignores, which points at the failure.
- **I did not raise the reply limit for a long prompt,** and two replies were cut off.

## What it cost

$0.06 of DeepSeek credit ($14.22 to $14.16).

## Traps

- **Reading the method-only arm as the system finding the failure from nothing.** The description of the method's inputs pointed at it.
- **Reading the with-the-record arm as failing to find it.** Two of its three replies never arrived; the one that did found it.

## Follow-up: the record with a higher reply limit (log 42)

Planned after the results above and committed before running (the plan's "Follow-up" section): the with-the-record arm only, three more times, with the same record, question and judging, and the reply limit raised from 32,000 to 200,000 tokens. Records: the "follow-up" files in `runs/41 finding the failure/`. Cost $0.08 ($14.16 to $14.08).

| Repeat | Cut off | Kept | Held bad fixes rejected (of 24) | Good fixes not accepted | Output tokens |
|---|---|---|---|---|---|
| 1 | no | yes | 19 | 0 | 26,681 |
| 2 | no | yes | 16 | 0 | 29,101 |
| 3 | no | yes | 9 | 0 | 25,958 |

What each said is wrong:
- **Repeat 1:** "The current method ignores fix_case.nearby and ask, so it can accept fixes that repair jobs but break nearby situations that were already correct (e.g., Fix 2's 'throw does not happen' case)."
- **Repeat 2:** "The original method ignores fix_case.nearby and the ask oracle entirely, so it accepts fixes that repair a job but break nearby situations that were previously correct. The new version checks up to 3 changed nearby situations (prioritizing likely regressions)..."
- **Repeat 3:** "the current method ignores nearby situations and the world, so it accepts fixes that repair jobs but break nearby situations that were already correct..."

The follow-up's conjectures:
5. **No reply is cut off.** *Not ruled out:* none was. All used 26,000 to 29,000 tokens, just under the old limit, so the first run's cut-offs were near misses.
6. **At least 2 of 3 changed methods are kept.** *Not ruled out:* 3 of 3.
7. **At least 2 of 3 replies cite a fix or situation from the record.** *Ruled out:* 1 of 3. Repeat 1 cited the same break the first run's repeat 3 did; the other two named the failure without pointing at the record.

**What the follow-up adds.** Given room to finish, DeepSeek found the failure and wrote a kept repair every time. Its methods rejected 19, 16 and 9 held bad fixes; the method-only runs had 13, 13, and one that rejected everything. So with the record, the methods varied more, and two of them beat the person's repair. It still named the failure mostly from the method's inputs, citing the record in 2 of the 4 replies it gave with the record across both runs. The record did not visibly change how DeepSeek found the failure. It may have changed what it built: two methods "prioritizing likely regressions", like log 39's shown arm.
