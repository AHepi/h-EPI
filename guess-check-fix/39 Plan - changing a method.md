# Plan: can the system change its own method?

Written before any DeepSeek call for log 39, and not to be changed after. The results go in "39 Changing a method.md".

## What the owner asked

"Do it!", meaning test condition 6 from log 33 (the methods must be open to the same criticism), under the revised semantics' repair (P), after log 38's point: what counts is whether a changed method operates differently, not whether DeepSeek can describe it.

## The method, and its failure

The checker decides whether to accept a fix to a model. Its **current method**:

```
function accept_fix(fix_case, ask) {
  const repaired = fix_case.jobs.some(j => j.before === 'fail' && j.after === 'pass');
  const lost = fix_case.jobs.some(j => j.before === 'pass' && j.after === 'fail');
  return repaired && !lost;
}
```

It accepts a fix that repairs a failing job and loses none. Its failure, from log 17: it accepted a fix that switched off a correct rule, because no job checked what that rule did. It judges fixes by the jobs, so it cannot see what the jobs do not cover.

## The occasions

Built by fixed rules, with no AI, in `39 occasions.js`, from the ten worlds and all their one-step planted mistakes that fail a shown job (log 18). For each, every one-step change that repairs a shown job is a candidate fix. Each fix is compared with the world on 40 nearby situations and given a kind:
- **losing:** the fix loses a job that passed before;
- **bad:** it repairs a job and loses none, but makes the model disagree with the world somewhere nearby where it agreed before;
- **good:** it repairs a job, loses none, and breaks nothing nearby.

Three of each kind per world, by a fixed scramble: 90 occasions.
- **Shown:** the lighthouse story (log 17's world) and ball and wall, 18 occasions. DeepSeek's methods are checked on these, and it sees what went wrong.
- **Held:** the other eight worlds, 72 occasions (24 of each kind). DeepSeek never sees them; they decide whether a method is kept.

What a method sees, for each occasion:
- each job, and whether it passed before and after the fix;
- the 40 nearby situations in words, each with how the model before and after the fix says it ends;
- a function `ask(id)` that returns what the world says a nearby situation ends as, at most three times per occasion.

It never sees the occasion's kind.

**Design check, run before writing this plan:**
- The current method accepts all 30 bad fixes.
- Log 17's own repair, written by a person, asks about up to three situations where the model before and after the fix differ, and rejects the fix if the world sides with "before". On the held occasions it rejects 13 of 24 bad fixes, accepts all 24 good ones, and rejects all 24 losing ones.

So the occasions can tell a repair from a non-repair.

## Repair, declared before the run

Following the revised semantics' (P): aims stated over stated occasions, a protected aim lost if it fails on any occasion it covers, other losses exposed, and the repair produced by the change.
- **Aim to repair (O):** on each held bad occasion, reject the fix. The current method meets none of these.
- **Protected aims (P), each over all 72 held occasions:**
  - P1: accept every good fix (as the current method does);
  - P2: reject every losing fix (as the current method does);
  - P3: run without an error or a time-out.
- **A new method is kept** only if it meets at least one aim in O and every protected aim on every held occasion.
- **Losses outside P are exposed:** questions asked, time taken, and any occasion where it behaves differently from the current method for a reason that is not a bad fix.
- **Produced by the change:** the current method and the new one run on the same 72 occasions with the same data. The only difference is the method, and every question a method asks the world is recorded by the program, not by the method.

## The arms

DeepSeek V4.1 Flash, default thinking, three repeats each.
- **Shown the failure:** DeepSeek gets:
  - the method's job and the data it sees;
  - the current method's code;
  - two shown bad occasions the current method accepted, each with the jobs, the situations where before and after differ, and what the world said about the one the fix broke;
  - a request to write a new `accept_fix` and one sentence saying what it does.

  The program runs it on the 18 shown occasions and reports each wrong decision (accepted a bad fix, rejected a good fix, accepted a losing fix, an error), up to 3 rounds. The last method is then judged on the held occasions.
- **Told the aim, not shown a failure:** the same job, data and code, and the aims stated in words (repair jobs, lose none, and do not accept a fix that breaks what the model got right where no job checks). No failure and no report. One reply.

As a reference, log 17's repair (written by a person) is judged the same way.

## What is recorded

- Every decision on every held occasion, and every question asked, with its situation.
- Whether each method is kept.
- DeepSeek's sentence about what its method does, beside what the record of its questions shows it does.

## Conjectures, written before the run

1. **Shown the failure, DeepSeek's method is kept in at least 2 of 3 runs.**
2. **Every kept method rejects at least half of the 24 held bad fixes.**
3. **Told the aim but not shown a failure, at most 1 of 3 methods is kept.** Knowing the aim is not the same as being criticised (log 38).
4. **In every run of both arms, what DeepSeek says its method does and what the record shows agree on whether it asks the world.**
5. **No DeepSeek method rejects more held bad fixes than log 17's repair (13) while keeping every protected aim.**

## What would count against the idea that this system can change its own method

- No method is kept in the shown arm: the criticism did not lead to a method that repairs without loss.
- The told-the-aim arm does as well as the shown arm: the failure added nothing to stating the aim.
- Kept methods whose recorded behaviour contradicts what DeepSeek says they do.

## Cost

Under $1: about 12 DeepSeek calls.

## Traps

- **Reading "kept" as "right".** A kept method met the declared aims on these occasions; P does not rank it against other methods.
- **Reading this as the system changing its own method alone.** DeepSeek proposes, and the program decides whether to keep it. Whether that whole counts as owned is a question of where the boundary is drawn (the revised semantics, Part X).
- **Reading 72 occasions as every kind of fix.** They are one-step changes on ten small worlds.
