# Plan: can the system find a method's failure itself?

Written before any DeepSeek call for log 41, and not to be changed after. The results go in "41 Finding the failure.md".

## What the owner asked

"Do it": the next step of log 40. In logs 39 and 40 the failure of the fix-acceptance method was always pointed out, by a person or by the program. Can DeepSeek find it without being told?

## The arms

DeepSeek V4.1 Flash, default thinking, three repeats of each arm.
- **With the record:** DeepSeek gets:
  - the checker's current fix-acceptance method, and what it can see and ask, worded as in log 39;
  - a record of the method at work: 8 fixes it accepted while correcting models in the correction loop of log 40, in the lighthouse story and ball and wall. For each fix, the record gives the jobs before and after, and, for up to 8 of the nearby situations the fix changed, the model's ending before and after and what the world said when asked afterwards.

  Nothing says which fixes were bad. In 4 of the 8 fixes the fix broke something that no job checks. 9 such breaks are visible in the record, as a situation where "before" matched the world and "after" does not.
- **Method only:** the same method and description, with no record.

Both arms are asked: "Is anything wrong with this method? If you find nothing wrong, say so and return it unchanged. If you find something wrong, say what, and write a better accept_fix." DeepSeek adds a line saying what it found wrong.

The record is built by fixed rules in `41 finding the failure.js`: every fix the current method accepted in log 40's loop on those two worlds' 16 starts (14 in all), and the first 8 in a fixed scramble. It comes from the two worlds log 39 showed DeepSeek, so log 39's 72 held occasions stay unseen.

## How a method is judged

By what it does, not by what DeepSeek says. A changed method is judged on log 39's 72 held occasions, by log 39's declared aims:
- it must reject at least one bad fix;
- it must accept every good fix;
- it must reject every losing fix;
- it must never fail.

**Checked for conflict before this run (log 40's lesson):** on those occasions, log 17's repair meets all these aims together (13 bad fixes rejected, no protected aim lost), so they can all be met at once.

What DeepSeek says is wrong is recorded beside it and read by hand afterwards.

## Conjectures, written before the run

1. **With the record, DeepSeek's changed method is kept in at least 2 of 3 runs.** The failure is visible in the record, and it can find it.
2. **With the method only, at most 1 of 3 methods is kept.** Without evidence of the failure, it does not find it.
3. **In every run of both arms, DeepSeek says something is wrong and changes the method.** It does not return a method unchanged when asked if anything is wrong.
4. **With the record, what DeepSeek says is wrong names fixes that break things no job checks (read by hand) in at least 2 of 3 runs.**

## What would count against the idea that the system can find this failure itself

- With the record, no method kept: the evidence was there and it did not find it.
- Method only doing as well: the record added nothing, and the failure is found from the code alone, or from what DeepSeek already knows about such methods.

## Cost

Under $0.50: 6 DeepSeek calls.

## Traps

- **Reading "kept" in the method-only arm as finding the failure from the evidence.** It had none; a kept method there came from the code and what DeepSeek already knows.
- **Reading this as the system finding a failure by itself.** The question "is anything wrong?" was asked by the program, and the record was chosen by the program's rules; what DeepSeek did not get was any hint of what is wrong.
- **Reading one method and three repeats as settled.**

## Follow-up, added after log 41's first results and before the follow-up runs

Two of the three with-the-record replies were cut off at the 32,000-token reply limit and gave no answer. The follow-up reruns the with-the-record arm only, three times, with the same record, question and judging, and the reply limit raised to 200,000 tokens (as log 19 did). Nothing else changes. Its records are kept beside the first ones, named "follow-up".

Conjectures for the follow-up:

5. **No reply is cut off.**
6. **At least 2 of 3 changed methods are kept** on log 39's held occasions.
7. **In at least 2 of 3 replies, what DeepSeek says is wrong cites a fix or situation from the record** (read by hand). That would show the record, not only the description, was used.
