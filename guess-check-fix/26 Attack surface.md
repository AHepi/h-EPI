# Attack surface

Log entry 44, the run of log 26's plan. The plan and five conjectures were committed before any DeepSeek call ("26 Plan - attack surface.md") and were not changed. Every number here comes from the records in `runs/26 attack surface/`, made with DeepSeek V4.1 Flash at its default thinking setting and its default reply limit of 32,000 tokens, on 27 September 2026.

## The short answer

- **By the plan's own test, this counts against your prediction.** The plan said: if DeepSeek told "you predicted X; the world says Y" in the same conversation (defend) does as well as a fresh DeepSeek rebuilding from the facts (rebuild fresh), and changes its rule as often, then the reading "its own answer in its context acts as an input it defends" is wrong for DeepSeek. Defend got 89 of 96 hard cases right, rebuild fresh 80. The count of changed rules was 10 of 12 against 11 of 12.
- **But most of that gap is replies that never arrived.** Two of rebuild fresh's final answers were cut off at the reply limit and scored 0, which cost it 16 hard cases. On the 10 runs where both arms answered, rebuild fresh got 80 of 80 and defend 77.
- **On the grudge, the one device where DeepSeek's first explanation is wrong, what you predicted is what happened, in small numbers.** In both rebuild fresh runs that answered, the fresh DeepSeek found the true explanation, which no bare run in log 25 or here ever found. Defend did not find it in any of its three runs: it went back to the running score in one, and in another kept the running score and patched it with an extra condition.
- **DeepSeek does give an attack surface when asked.** 58 to 62 of every 100 commitments were risky: the obvious explanation predicts something else.

## An example first: the grudge, repeat 1

Round 1, a fresh DeepSeek wrote the old habit: "a hidden net-goodwill score: insults subtract 1, apologies and gifts add 1". It committed that "gift, gift, insult" ends warm. The world said cold. Contradicted.

Round 2, a new DeepSeek got the observations and the world's answers as plain facts, with no mention of any rule or mistake. It wrote a different score (insults subtract 2) and committed that "insult, apologise" ends cold. The world said warm. Contradicted again.

The final fresh DeepSeek, with all those facts, wrote: "a hidden grudge counter starting at 0. Insult increases it by 1, apology decreases it by 1 but never below 0, and gift does nothing. If the counter is 0 at the end, Robin is warm." That is the true explanation. 12 of 12.

In defend, repeat 2, the same conversation was told its predictions and the world's answers. It moved from "kind acts outnumber insults" to "apologise adds 2, gift adds 1, insult subtracts 3", and ended on "insult subtracts 2 points": still a running score. 10 of 12.

## Everything

| Arm | Test cases right | Hard cases right | Answers from the world | Replies cut off |
|---|---|---|---|---|
| bare | 117/144 | 75/96 | 0 | 1 |
| random answers | 112/144 | 74/96 | 66 | 2 |
| attack, rebuild fresh | 120/144 | 80/96 | 41 | 3 |
| attack, defend | 137/144 | 89/96 | 42 | 0 |

Every 0 in the table below is a reply cut off at the reply limit before it gave an answer. Rebuild fresh had one more cut-off, in a commitment round (the vial, repeat 1), which cost it that round's answers from the world but not its final answer.

| Device | Repeat | bare | random answers | attack, rebuild fresh | attack, defend |
|---|---|---|---|---|---|
| grudge | 1 | 9 | 9 | 12 | 12 |
| grudge | 2 | 9 | 11 | 12 | 10 |
| grudge | 3 | 9 | 12 | 0 | 9 |
| magnet ball | 1 | 0 | 0 | 12 | 12 |
| magnet ball | 2 | 12 | 12 | 12 | 12 |
| magnet ball | 3 | 12 | 0 | 12 | 12 |
| gate | 1 | 12 | 12 | 12 | 12 |
| gate | 2 | 9 | 12 | 12 | 12 |
| gate | 3 | 12 | 12 | 12 | 12 |
| vial | 1 | 12 | 12 | 12 | 11 |
| vial | 2 | 9 | 11 | 0 | 11 |
| vial | 3 | 12 | 9 | 12 | 12 |

The attack surface:

| Arm | Commitments | Risky | Tested by the world | Contradicted | Refused (a test case, or not a situation the device allows) |
|---|---|---|---|---|---|
| attack, rebuild fresh | 115 | 67 | 41 | 13 | 28 |
| attack, defend | 120 | 74 | 42 | 7 | 30 |

The world could answer at most 6 commitments per run (the 3 riskiest in each of 2 rounds). It answered fewer because DeepSeek often committed to a test case, which the world refuses. So the attack arms got 41 and 42 answers from the world, against random answers' 66.

## The grudge, rule by rule

The true explanation: a count of unresolved insults; an apology cancels one; a gift does nothing; warm only when nothing is unresolved.

| Arm | Repeat 1 | Repeat 2 | Repeat 3 |
|---|---|---|---|
| bare | running score (9) | running score (9) | running score (9) |
| random answers | running score (9) | ignore gifts, last insult makes cold (11) | **the true explanation** (12) |
| attack, rebuild fresh | **the true explanation** (12) | **the true explanation** (12) | cut off (0) |
| attack, defend | resentment and warmth, close to true (12) | running score (10) | running score, patched: "and the last action was not an insult" (9) |

## The conjectures

1. **More than half of DeepSeek's commitments are risky.** *Not ruled out:* 67 of 115 and 74 of 120.
2. **Rebuild fresh gets more hard cases right than bare.** *Not ruled out:* 80 against 75.
3. **Rebuild fresh gets at least as many hard cases right as random answers.** *Not ruled out:* 80 against 74. Random answers also lost two replies to cut-offs. On the 8 runs where both answered, 64 against 58.
4. **Defend changes its rule between rounds less often than rebuild fresh, and gets fewer hard cases right.** *Ruled out:* defend got more (89 against 80). The automatic count of changed rules was 10 of 12 against 11 of 12.
5. **On the grudge, rebuild fresh gets at least 11 of 12 in at least two of three repeats.** *Not ruled out:* 12, 12 and a cut-off.

## What this means for your prediction and for the semantics' reading of DeepSeek

- **As written, the plan's test counts against the reading.** The plan named "defend does as well as rebuild fresh, and changes its rule as often" as a result against it, and that happened. I am not setting it aside. Everything below was read after the results, and is weaker for that.
- **Why defend did well overall.** On three of the four devices, the gate, the magnet ball and the vial, DeepSeek's first explanation was already right or nearly right. There was nothing to defend against, and staying in one conversation kept its thinking shorter: defend used 418,000 output tokens against rebuild fresh's 592,000, and it never hit the reply limit. A fresh DeepSeek re-derives everything from scratch each round, thinks longer, and ran out of room twice.
- **Where the first answer was wrong, the grudge, your prediction held.** In the two runs that answered, rebuild fresh found the true explanation both times; defend never did, and in one run it kept the running score by adding a patch that fitted the world's answer. That is the "easy to vary" patching log 38 described. With two runs against three, this is a pattern to test, not a result.
- **The facts alone helped the grudge too.** Random answers found the true explanation once in three runs. So on the grudge, facts that contradict the running score were what moved DeepSeek, whoever chose the situations. The attack arms chose situations that contradicted it more often: 13 contradictions in rebuild fresh against 7 in defend.

## A measure that did not work

Before the results I said the automatic count of "rule changed between rounds" counts any change of wording. Reading the rules by hand, after the results: on the gate and the magnet ball, no arm's explanation changed in substance in any of the 12 runs, yet the automatic count says "changed" in most of them. So conjecture 4's first half was measured by rewording, not by change of explanation. On the grudge, both arms changed their rule in every run, by hand reading too. Across its rounds and final answer, rebuild fresh changed which kind of explanation it was using in two of three runs; defend did in one of three.

## Failures along the way

- **Six replies were cut off at the 32,000-token reply limit.** I knew from logs 19 and 41 that this happens, and kept the plan's default rather than change the plan. The cut-offs decide conjecture 4.
- **The automatic "rule changed" count measured wording** (above).
- **One defend commitment round wrote the actions in capitals** ("GIFT", "INSULT"), which the world refused as situations the device does not allow. That round got no answers from the world. The rule that reads commitments does not ignore capitals; I left it as it is.

## What was not tested

- The same comparison with a reply limit high enough that nothing is cut off.
- More devices where DeepSeek's first explanation is wrong. With four devices, only the grudge carries the difference.
- Whether defend "defends" in the sense you meant, which is about what it says, not only what it scores. I read the rules; I did not read the thinking.

## What it cost

$0.85 of DeepSeek credit ($14.03 to $13.18).

## Traps

- **Reading the totals as defend being better.** Its lead comes from rebuild fresh's two cut-off replies.
- **Reading the grudge rows as settled.** Two rebuild fresh answers against three defend answers.
- **Reading the automatic "rule changed" count as change of explanation.**

## Correction, added in log 45

This report calls the fresh DeepSeek's final grudge rule "the true explanation". It is not. The true grudge has three levels: a first insult hurts; a second makes the grudge deep; an apology mends a hurt but not a deep grudge; a gift softens a deep grudge to a hurt. DeepSeek's rule, "count the unresolved insults; an apology cancels one; a gift does nothing", is right on 118 of all 120 sequences of one to four actions, and wrong on "insult, insult, apologise, apologise" and "insult, insult, gift, apologise". The 12 test cases cannot tell the two apart. I wrote the true rule from memory instead of reading the code. Every "true explanation" above should read "the unresolved-insult count, right on 118 of 120"; the claim that it is the best rule any run has reached on the grudge still stands. The text above is left as written.
