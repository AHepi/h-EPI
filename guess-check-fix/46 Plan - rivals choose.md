# Plan: rivals choose the questions

Written before any DeepSeek call for log 46, and not to be changed after. The results go in "46 Rivals choose.md".

## What the owner asked

"Ok go": log 45's next step. Log 45 found that on the grudge DeepSeek's own commitments aim where its current rule differs from the obvious one, never where it differs from a rule it has not imagined. So the world was asked about a deep grudge in only 1 of 12 runs, and no run found the true grudge. Here, rival explanations choose what the world is asked.

## The run

- **Device:** the grudge, with log 25's 14 observations. The world refuses log 25's 12 test cases, as in logs 44 and 45.
- **Rivals choose (the new arm):** two rounds.
  - Each round, a fresh DeepSeek gets the observations and every answer from the world so far. It writes 4 rival explanations, each fitting every known fact but differing from the others as much as it can about unseen situations. Each rival is a small JavaScript function.
  - The program runs every rival on all 120 sequences of one to four actions, in log 34's separate process with no files, network or key. It keeps the rivals that fit every known fact.
  - The world answers the 3 unseen situations where the kept rivals are most evenly split (ties broken by a fixed scramble). If fewer than two rivals fit, or they never disagree, the world is asked nothing that round.
  - After two rounds, a fresh DeepSeek answers all 106 sequences that are not observations, from the observations and the world's answers: log 45's final question.
- **Random answers (the control):** 6 answers from the world about random unseen situations (new ones, not log 45's), then the same final question. It has at least as many answers from the world as rivals choose.
- **Six repeats of each.** DeepSeek V4.1 Flash, default thinking, reply limit 200,000.

## What is measured

1. **Every case right, of 106.** For scale: the true grudge 106, the unresolved-insult count 104, the running score 81.
2. **Runs in which the world was asked about a telling sequence** ("insult, insult, apologise, apologise" or "insult, insult, gift, apologise": where the count and the true grudge differ).
3. **The rivals:** how many fit, and how many agree with the true grudge on all 120 sequences (checked by the program).
4. **The final rule, read by hand, blind to arm,** in log 45's categories:
   - true grudge;
   - unresolved-insult count;
   - running score;
   - other;
   - no rule.

   This time the list is scrambled by a seeded shuffle, and a test checks that it mixes the arms (log 45's lesson). I may still guess an arm from a rule's style.

## Conjectures, written before the run

1. **No reply is cut off.**
2. **Summed over six repeats, rivals choose gets more of the 106 cases right than random answers.**
3. **In at least 3 of 6 rivals-choose runs, the world is asked about a telling sequence** (log 45: 1 of 12 attack runs).
4. **In at least 1 of 6 rivals-choose runs, some rival agrees with the true grudge on all 120 sequences.**
5. **At least 1 of the 6 rivals-choose final rules is the true grudge** (log 45: 0 of 18).
6. **Every rivals-choose final rule is at least as good as the running score** (81 or more of 106).

## What would count against the idea

- **Rivals choose does no better than random answers.** Then choosing the questions by the rivals' disagreement adds nothing on this device.
- **The world is asked about a telling sequence in no more rivals-choose runs than in log 45.** Then DeepSeek's rivals do not imagine the deep grudge either, and choosing between them cannot reach it.

## Cost

About $0.50 to $1: 6 repeats, 3 DeepSeek calls for rivals choose and 1 for random answers each.

## Traps

- **Reading a telling question as finding the true grudge.** The world's answer is a fact; DeepSeek still has to build the explanation.
- **Reading a rival that agrees with the true grudge as DeepSeek holding the true explanation.** It was one of four, and the program, not DeepSeek, found which fitted.
- **Six repeats are not settled.**
