# Keep the survivors

Log entry 47. On the grudge, rival explanations that fitted every fact were kept from round to round, and the final answer was made three ways from the same run: a vote of the survivors, a fresh DeepSeek shown the survivors, and a fresh DeepSeek shown only the facts. The plan and six conjectures were committed before any DeepSeek call ("47 Plan - keep the survivors.md"). Every number here comes from the records in `runs/47 keep the survivors/`, made with DeepSeek V4.1 Flash at its default thinking setting and a reply limit of 200,000 tokens, on 27 September 2026.

## The short answer

- **Keeping the survivors did not help.** A fresh DeepSeek shown only the facts got the most right: 5,282 of the 5,832 five- and six-action sequences, against 5,225 when shown the survivors and 5,087 for the survivors' vote. The plan named this as counting against the idea that keeping survivors matters.
- **Surviving is not the same as being good.** A rival survives by fitting the few facts the world was asked about. In one run the only survivor was the old running score, because nothing asked ever refuted it. Shown the survivors, DeepSeek copied one of them in 5 of 6 runs, including that running score.
- **But a new part appeared, over and over:** "a gift softens a grudge of two or more", which is exactly the true grudge's gift rule. Some of log 46's rivals had it, but no earlier final answer did. It is in 4 of the 12 final programs. Each still gets something else wrong. No final answer, and no rival, was the true grudge.

## An example first: repeat 4

Round 1: all four rivals DeepSeek wrote failed at least one of the 14 observations, so none was kept, and nothing was asked. Round 2: four new rivals, two of which fitted. One was "an additive trust score: insult -1, apology +1, gift +1; warm when score is at least 1", the old running score. The world was asked where the two disagreed; the other was refuted. Round 3: four more rivals, all refuted by the answers they made the world give. The running score was left standing alone.

Shown that one survivor, the final DeepSeek wrote it back exactly: 81 of 106 short, 628 of 972 long. The survivors' vote was the same rule. Shown only the facts, a fresh DeepSeek wrote a different running score: 80 and 649.

## Everything

For scale, from the plan: the true grudge 106 short and 972 long; the unresolved-insult count 104 and 913; the running score 81 and 628.

| Final answer | Short right (of 106 per run, summed over 6) | Long right (of 972 per run, summed over 6) | By repeat (short / long) | Telling sequences right (of 12) |
|---|---|---|---|---|
| survivors vote | 583 | 5,087 | 100/916, 105/938, 91/770, 81/628, 105/941, 101/894 | 7 |
| shown the survivors | 595 | 5,225 | 100/916, 105/940, 103/900, 81/628, 105/940, 101/901 | 7 |
| shown the facts only | 599 | 5,282 | 105/940, 105/940, 104/913, 80/649, 100/918, 105/922 | 5 |

- **Rivals:** 72 written, all ran on every sequence, 68 fitted every fact known when written. None agreed with the true grudge on every sequence up to six actions.
- **Survivors at the end, by repeat:** 1, 6, 2, 1, 4, 2.
- **The vote** was left undecided on 200 sequences in repeat 3 (two survivors, disagreeing), 5 in repeat 5 and 8 in repeat 6.
- **The world was asked a telling sequence** in 4 of 6 runs.
- **No reply was cut off.**

The final programs, in DeepSeek's own one-line summaries:

| Repeat | Shown the survivors | Shown the facts only |
|---|---|---|
| 1 | a grudge counter; gifts subtract only before any apology; warm only if apologised and the grudge is zero (a survivor, copied) | anger: insult +1, apology -1, **a gift -1 only if anger is 2 or more**; warm at 0 |
| 2 | **a capped grudge; a gift subtracts 1 only when the grudge is at least 2** (a survivor, copied) | the same as a survivor, written independently |
| 3 | warm if trust is positive and no insult is unapologised (a survivor, copied) | the unresolved-insult count |
| 4 | the running score (the only survivor, copied) | a running score |
| 5 | **a grudge; gifts reduce only a grudge of at least two** (a survivor, copied) | starts cold; apologies clear a grudge of 1 or less |
| 6 | a grudge debt; apologies at 2 or more leave it at 2 (a survivor, copied) | anger 0, 1, or 2 and above; an apology clears only 1; gifts do nothing |

What the "gift softens a grudge of two or more" programs still get wrong: an apology lowers a grudge of 2 to 1, where in the true grudge an apology does nothing to a deep grudge.

## The conjectures

1. **No reply is cut off.** *Not ruled out.*
2. **Shown the survivors gets more long sequences right than shown the facts only.** *Ruled out:* 5,225 against 5,282.
3. **The survivors' vote gets more long sequences right than shown the facts only.** *Ruled out:* 5,087 against 5,282.
4. **In at least 2 of 6 runs, a survivor agrees with the true grudge everywhere up to six actions.** *Ruled out:* none.
5. **In at least 1 of 6 runs, the shown-the-survivors final program is the true grudge.** *Ruled out:* none.
6. **In at least 4 of 6 runs, the world is asked a telling sequence.** *Not ruled out:* 4 of 6.

## What this means for the idea

- **Keeping what survives is only as good as what it survived.** A rival here survives by fitting at most 23 facts, all of four actions or fewer. Nothing checks it against the long sequences where the survivors disagree, so a survivor can be the old habit, or a rule that falls apart past four actions. Log 46's lost rival, which fitted everything up to four actions, was also wrong on longer ones.
- **Shown survivors, DeepSeek defers.** In 5 of 6 runs it took a survivor as it was, rather than building on them. Without them it did at least as well by writing its own. So handing the rivals to the last step handed over their weaknesses too.
- **Where the gain came from was the questions, again.** The new part, a gift that softens only a deep grudge, appeared in repeats 1, 2 and 5, and in each of them the world had been asked "insult, insult, gift, apologise" and answered warm. Repeats 3 and 4 were never asked about a gift after two insults, and did not write it. Repeat 6 was asked a different one ("insult, insult, gift, gift", cold) and did not write it either. The program's disputed questions found those situations; DeepSeek, given the answers, built the part (checked in the records after the results). That fits logs 45 and 46: contradiction from the world, aimed well, is what moves it.
- **In the semantics' terms, retention here had no content.** "Kept" meant "not yet refuted", and every survivor was equally kept. The semantics' repair keeps a change only if it holds on the occasions it covers. Here those occasions were short sequences only, and the losses were exposed only by my grading, not by anything the system itself looked at.

## Failures along the way

- None found in the code or the tests. All 13 tests passed first time.
- **A design gap, seen only in the results:** the world could be asked only about four actions or fewer, while I graded on five and six. So the survivors could never be tested where they differ most. I chose that in the plan without seeing that it guaranteed untested disagreement.

## What was not tested

- Asking the world about longer sequences where survivors disagree.
- Preferring among survivors by anything but survival (for example, fewer parts, or parts no fact holds in place).
- Other devices.

## What it cost

$0.30 of DeepSeek credit ($12.35 to $12.05).

## Traps

- **Reading this as "rivals do not help".** Log 46 showed rivals choosing questions helps. This shows only that keeping them for the last step did not.
- **Reading "copied a survivor" as DeepSeek failing.** Where the survivors were good (repeats 2 and 5), copying one was the best answer of the run.
- **Six repeats are not settled.**
