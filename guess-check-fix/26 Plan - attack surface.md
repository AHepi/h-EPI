# Plan: the attack surface

Written before any run of log 26, and not to be changed after. Not run yet: the owner asked to wait until the DeepSeek account is topped up.

## What the owner asked

"What about a series of commitments DeepSeek (ds) has to fill in that asks 'what would it take to prove this conjecture is wrong'. Error correction comes from spotting holes, sure. But it also comes from exposing your guesses to attack. A conjecture is worthless without an attack surface. So try that first. Try getting ds to imagine what it would take to refute a conjecturer. Or, actually, what it would take to cast doubt. You can't feed the conjecture and possible refutation back to Deepseek because it'll just 'disagree', reject the attack and default to its first answer. Any thoughts? Go back to the semantics, see what it suggests given the type of generators LLMs actually are. Because that determines where it sits in this scheme. I'm now testing the semantics here."

## Where an LLM sits in the semantics

- **An LLM is a selected transport** (Part IV, "Selected"): a population of candidate transports, a variation operator, a history of encountered cases, and survival on that history (training). Nothing in that history represents the target or criticises it. So it is faithful where its history reached and, wherever its population allows, unconstrained elsewhere (Derivation 3). Log 25's grudge shows it: every bare answer, 18 of them, reached for the same habit, a running score of kindness against insults.
- **Asking again, voting and rereading are selection responses** (Part IV, "Two responses to a violation"): re-tuning within the population. They cannot fix a failure that is "structural, not parametric" (Derivation 10). Log 25: five bare answers scored the same; the self-check kept the same rule for four rounds.
- **Feeding its conjecture back puts the answer into the input.** Once its answer is in its own context, the next reply is conditioned on it, which is what non-circular dependence forbids (Part V: the target's answer must not appear as an unanalysed boundary input). A criticism then is "an adverse signal", not yet a criticism with bearing (Part IX, K1), and it does not land on the route that produces the answer (Part IX, reason use). That is the owner's "it defaults to its first answer".
- **So the LLM is the variation operator: a source of conjectures, not their critic.** Construction, which needs a represented target, a criticism with bearing and a binding newly built (Part X, Build), happens in the system around it, under a declared boundary (Parts X and XII): an outside record keeps the conjecture's commitments, the world answers them, and only facts go back in. In log 23 DeepSeek did change its mind, when a surprise came as a fact and not as criticism of its answer.

## What the semantics suggests for an attack surface

- **The attack surface is the conjecture's contract, made explicit** (Part V, non-vacuity): the changes it claims to cover, stated, so that exclusions are not silent. A conjecture with no stated predictions for unseen cases has no contract to break.
- **Commitments are frozen before the test** (Derivation 7; Part VIII, historical index): a later narrowing is a new claim, recorded as one, so an attack cannot be dodged by moving the goalposts.
- **A failed commitment casts doubt; it does not refute the conjecture alone** (Part IX, K3: a failed test refutes the conjunction). The owner's word, "doubt", is the right one.
- **The verdict is mechanical and outside DeepSeek:** its prediction against the world's answer. It is not DeepSeek's to accept or reject.

## The test

On log 25's four devices, the same 14 observations, graded on the same 12 test cases (8 hard), three repeats, DeepSeek V4.1 Flash at its default thinking setting. Each arm has at most 6 answers from the world:

- **bare:** answers the test cases from the observations.
- **random answers:** the world's answers to 6 random unseen situations first.
- **attack, rebuild fresh:** two rounds. Each round a fresh DeepSeek states its rule and commits to 5 predictions for unseen situations, riskiest first, each with why it would cast doubt if it came out otherwise. The world answers the 3 riskiest. The next fresh DeepSeek gets the observations and every answer so far as facts, never the old rule, its predictions, or any verdict. After two rounds a fresh DeepSeek answers the test cases from the observations and all the world's answers.
- **attack, defend:** the same commitments and world answers, fed back into the same conversation ("you predicted X; the world says Y"), which also answers the test cases. The owner expects this to fail.

The world never answers a test case (a commitment to one gets "not available" and uses up its place). Recorded: every commitment; whether it was risky (the obvious explanation predicts otherwise); whether the world contradicted it; whether the rule changed between rounds.

## Conjectures, written before the run

1. **DeepSeek, asked, gives an attack surface:** more than half its commitments are risky (the obvious explanation predicts otherwise).
2. **Attack, rebuild fresh gets more hard cases right than bare**, summed over all runs.
3. **Attack, rebuild fresh gets at least as many hard cases right as random answers**, with the same number of answers from the world.
4. **Attack, defend changes its rule between rounds less often than attack, rebuild fresh, and gets fewer hard cases right** (the owner's prediction).
5. **On the grudge, where every bare run in log 25 failed the same way, attack, rebuild fresh gets at least 11 of 12 in at least two of three repeats.**

## What would count against the semantics' placement of the LLM

- If **defend does as well as rebuild fresh, and changes its rule as often**, the reading "its own answer in its context acts as an input that it defends" is wrong for DeepSeek.
- If **rebuild fresh does no better than random answers**, then exposing the conjecture to attack adds nothing beyond the information the answers carry, and the attack surface is doing no work of its own here.
- If **DeepSeek's commitments are mostly safe** (the obvious explanation predicts the same), asking an LLM for its attack surface does not produce one.

## Cost

About $1 to $1.50 of DeepSeek credit, estimated from log 25 (four devices, three repeats, about eight calls per device and repeat).

## Traps

- **Reading a win for rebuild fresh as the attack surface's doing.** Conjecture 3 is the check: random answers give the same amount of information.
- **Reading "risky" as "right".** A risky commitment is one the obvious explanation disagrees with; it may still be wrong.
