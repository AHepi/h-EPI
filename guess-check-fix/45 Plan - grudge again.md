# Plan: the grudge again

Written before any DeepSeek call for log 45, and not to be changed after. The results go in "45 Grudge again.md".

## What the owner asked

"Do it": log 44's next step. On the grudge, where DeepSeek's first explanation is wrong, does a fresh DeepSeek given only facts ("rebuild fresh") end with a better explanation than one told its own mistakes in the same conversation ("defend")? The owner predicts defend clings to its first answer.

## A mistake of mine this plan corrects

Log 44's report called the fresh DeepSeek's final grudge rule "the true explanation". It is not. The true grudge (in "25 construction worlds.js") has three levels. A first insult hurts; a second makes the grudge deep. An apology mends a hurt but not a deep grudge. A gift softens a deep grudge to a hurt. Robin is warm only with no grudge.

DeepSeek's rule, "count the unresolved insults; an apology cancels one; a gift does nothing", is right on 118 of all 120 sequences of one to four actions. It is wrong on "insult, insult, apologise, apologise" and "insult, insult, gift, apologise" (the two telling sequences). Log 25's 12 test cases cannot tell it from the true grudge. I wrote the true rule from memory instead of reading the code. A correction note is added to "26 Attack surface.md".

## The run

- **Device:** the grudge only, with log 25's 14 observations.
- **Arms:** random answers, attack with rebuild fresh, and attack with defend, exactly as in log 26's code: commitments, the three riskiest tested in each of two rounds, at most 6 answers from the world. Bare is left out; it has failed the same way in every run so far (log 25 and log 44).
- **Six repeats of each arm.** DeepSeek V4.1 Flash, default thinking.
- **Two changes from log 44, both decided now:**
  - the reply limit is 200,000 tokens instead of 32,000, so no reply should be cut off;
  - the final question asks about every sequence that is not an observation, 106 of them, instead of only the 12 test cases.
- The world still refuses to answer log 25's 12 test cases.
- Random answers use new random situations (not log 44's).
- The rule that reads commitments is unchanged: actions written in capitals are still refused.

## What is measured

1. **Every case right, of 106,** from the final answers. The true grudge gets 106; the unresolved-insult count gets 104; the running score (kind acts outnumber insults) gets 81.
2. **The two telling sequences.**
3. **The final rule, read by hand, blind to arm.** The final rules are written out shuffled, with no arm named. I sort each into one of these categories before opening the key:
   - **true grudge:** a second insult makes things worse in a way an apology alone cannot mend, and a gift softens it; warm only with no grudge;
   - **unresolved-insult count:** insults counted, an apology cancels one, and a gift has no effect;
   - **running score:** kind acts and insults added up with weights, with or without extra conditions;
   - **other;**
   - **no rule.**

   The blinding is imperfect: I may guess the arm from the style of a rule.

## Conjectures, written before the run

1. **No reply is cut off.**
2. **The owner's prediction, on the numbers:** summed over six repeats, rebuild fresh gets more of the 106 cases right than defend.
3. **The owner's prediction, on the rules:** fewer of rebuild fresh's final rules than defend's are running scores.
4. **Defend ends on a running score in at least 3 of 6 repeats.**
5. **Rebuild fresh gets at least as many of the 106 right as random answers.**
6. **No more than 2 of the 18 final rules are the true grudge.** The observations never show a deep grudge being mended, and the world answers at most 6 more situations.

## What would count against the owner's prediction

- Defend gets at least as many of the 106 cases right as rebuild fresh, and no more of its final rules are running scores.

## Cost

About $0.50 to $1: 18 runs, about 6 DeepSeek calls per repeat for each attack arm and one for random answers, with longer final answers than log 44.

## Traps

- **Reading six repeats as settled.**
- **Reading the unresolved-insult count as the true grudge.** It is 118 of 120 right, and it is still wrong.
- **Reading rebuild fresh against random answers as only about the attack.** Rebuild fresh also gets fewer answers from the world whenever DeepSeek commits to a test case.
