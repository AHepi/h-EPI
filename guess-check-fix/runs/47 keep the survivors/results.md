# Keep the survivors: results

DeepSeek V4.1 Flash, default thinking, reply limit 200000. 6 repeats; every number comes from the records in this folder.

| Final answer | Right, up to four actions (of 106 per run, summed) | Right, five or six actions (of 972 per run, summed) | By repeat (short / long) | Telling sequences right (of 12) | Runs where it is the true grudge everywhere |
|---|---|---|---|---|---|
| survivors vote | 583 | 5087 | 100/916, 105/938, 91/770, 81/628, 105/941, 101/894 | 7 | 0 |
| shown the survivors | 595 | 5225 | 100/916, 105/940, 103/900, 81/628, 105/940, 101/901 | 7 | 0 |
| shown the facts only | 599 | 5282 | 105/940, 105/940, 104/913, 80/649, 100/918, 105/922 | 5 | 0 |

Rivals written: 72; ran on every sequence: 72; fitted every fact known when written: 68; agreeing with the true grudge on every sequence up to six actions: 0.
Survivors at the end, by repeat: 1, 6, 2, 1, 4, 2; runs with a survivor that is the true grudge everywhere: 0.
Runs where the world was asked a telling sequence: 4 of 6.
Survivor votes left undecided (ties), by repeat: 0, 0, 200, 0, 5, 8.
Replies cut off: 0. Output tokens: 518440.

Final functions, by repeat:

- repeat 1, shown the survivors: Robin has a grudge counter; insults add, apologies subtract and set hasApology, gifts subtract only before any apology; warm only if apologized and grudge is zero. (acts exactly as round 3 rival 2)
- repeat 1, shown the facts only: Track hidden anger: insult +1; apologise -1 (min 0); gift -1 only if anger >= 2; warm iff anger is 0.
- repeat 2, shown the survivors: Track a capped grudge: insults add 1, apologies subtract 1, gifts subtract 1 only when grudge is at least 2; warm iff grudge is zero. (acts exactly as round 2 rival 1)
- repeat 2, shown the facts only: Hidden anger: insult +1; apologise -1 (min 0); gift -1 only if anger >= 2; mood warm iff anger is 0. (acts exactly as round 2 rival 1)
- repeat 3, shown the survivors: Warm iff trust is positive and no insult remains unapologised; gifts add trust but do not forgive insults. (acts exactly as round 3 rival 3)
- repeat 3, shown the facts only: Robin keeps a hidden grudge count: insult +1, apologise -1 (minimum 0), gift no effect; mood is warm only when the count is 0.
- repeat 4, shown the survivors: Robin keeps an additive trust score: insult -1, apology +1, gift +1; warm when score >= 1. (acts exactly as round 2 rival 1)
- repeat 4, shown the facts only: Robin's hidden mood score starts at 0; insult -2, apology +1, gift +2; warm iff score > 0.
- repeat 5, shown the survivors: Robin's grudge rises with insults, apologies clear up to one or reduce by one, gifts reduce only a grudge of at least two, and Robin is warm only at grudge zero. (acts exactly as round 2 rival 1)
- repeat 5, shown the facts only: Robin starts cold with grudge 0; insults add 1 and make cold, gifts subtract 1, apologies clear grudge and warm if it is <=1, otherwise subtract 1 and stay cold.
- repeat 6, shown the survivors: Robin tracks a grudge debt: insults add 1; apologies clear debt 0-1 and warm, but if debt >= 2 they set it to 2 and stay cold; gifts remove 1 debt and warm only if there was no debt. (acts exactly as round 3 rival 2)
- repeat 6, shown the facts only: Robin has hidden anger 0/1/2+: insults raise it (capped at 2), apologise clears only anger 1 to 0, gifts do nothing; warm iff anger is 0.
