# Plan: a kept method at work

Written before log 40 was run, and not to be changed after. The results go in "40 A kept method at work.md".

## What the owner asked

"Do iy" (do it): the next step of log 39. Put the fix-acceptance methods DeepSeek wrote, which the program kept, to work inside the checker's correction loop. Does the change operate where it is used, and not only one decision at a time?

## The loop

This is the checker alone, with no AI. It starts from a model with a planted mistake that fails a shown job, and repeats up to 5 rounds:
1. Stop if every shown job passes.
2. List every one-step change to the model that makes at least one failing shown job pass. These are the same kinds of change as log 39's: remove a rule, or change a rule to a neighbour.
3. Order them by how many failing jobs they repair (most first), then by a fixed scramble.
4. Hand each to the fix-acceptance method in that order, and apply the first one it accepts. If it accepts none, stop.

The method sees exactly what it saw in log 39: each job before and after, 40 nearby situations with the model's endings before and after, and three questions to the world per fix. Only the questions for fixes up to and including the accepted one count, because a loop would stop asking there. Every method runs in log 39's separate process, which records every question.

## The starts

Eight planted-mistake models per world, by a fixed scramble, from all 1,294 one-step planted mistakes that fail a shown job (log 18's kind): 80 starts.
- 16 are in the two worlds log 39 showed DeepSeek, the lighthouse story and ball and wall.
- 64 are in the eight it never saw.

The results are reported for the 64 held-out starts, and for the 16 separately.

## The methods

- the current method (repairs a job, loses none);
- log 17's repair, written by a person;
- the three methods DeepSeek wrote when shown the failure in log 39, each kept there (repeats 1, 2 and 3).

The told-the-aim methods made exactly the person's repair's decisions in log 39, so they are not run again.

## What is measured, for each start

- **damage:** nearby situations the model had right at the start and wrong at the end;
- **repaired:** whether every shown job passes at the end;
- **held-back jobs** passing at the end (jobs the loop never sees);
- **questions** asked of the world.

## Aims, declared before the run (the revised semantics' repair)

- **Aim to repair (O):** on a held-out start where the current method ends with damage, end with less damage.
- **Protected aims (P), over every held-out start:**
  - P1: if the current method ends with every shown job passing, so does the new method;
  - P2: the new method never fails (no error or time-out).
- **Other losses are exposed:** held-back jobs passing, questions asked, and starts where it ends with more damage than the current method.
- **Produced by the change:** the same starts, the same candidates, the same order, and the same world. Only the method differs.

## Conjectures, written before the run

1. **Each of DeepSeek's three kept methods ends with less total damage than the current method** on the 64 held-out starts.
2. **Each ends with no more total damage than the person's repair.**
3. **Each keeps P1 on every held-out start:** where the current method ends with every shown job passing, it does too.
4. **Each asks fewer questions in total than the person's repair.**
5. **Each ends with at most half the current method's total damage.**

## What would count against the idea that the change operates where it is used

- Damage no lower than with the current method: rejecting bad fixes one at a time did not carry through the loop, because the loop found another damaging fix instead.
- P1 failing: the stricter method stops the loop before it repairs what the current method repairs.

## Cost

No DeepSeek credit; everything runs on this computer.

## Traps

- **Reading less damage as better models overall.** A method can end with less damage by accepting fewer fixes. P1 and the held-back jobs are there to show this.
- **Reading the 16 starts in the shown worlds as held out.** DeepSeek's methods were tuned on fixes from those worlds.
