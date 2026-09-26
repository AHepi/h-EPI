# Plan: does the language have to be able to express the explanation?

Written before any code for log 34 was run, and not to be changed after. The results go in "34 Can the language express it.md".

## What the owner asked

After log 33 listed seven conditions that seem necessary for a universal explainer, the owner asked me to flesh out conditions 2 and 6, then: "Do it!", meaning write this plan and run the test of condition 2.

## Condition 2, as tested here

"The language (the set of primitives and rules) must be able to express any explanation: universal, or able to grow." The checker's rule language is not universal: every thing has a fixed, finite list of states. So a count with no upper limit cannot be written in it, and every model of such a count is an approximation. This test tests the "universal" half only; a language that grows is not tested.

## The devices

Each device has actions, one thing that can be seen, and a true rule nobody is told. Every case starts fresh.

- **Balance gate** (needs a count with no upper limit). A gate with a push handle and a pull handle; you see whether it is open or shut. True rule: the gate is open exactly when there have been as many pushes as pulls. The obvious reading, pushing shuts it and pulling opens it, is refuted by the observations.
- **Peg tube** (needs a pile with no upper limit, a stack). You can slide a red or a blue peg into a tube, or take out a red or a blue peg; a light shows green, amber or red. True rule: pegs pile up and only the top one can come out. Taking out a peg that is not on top, or taking one out of an empty tube, jams the tube for good (red); otherwise the light is green when the tube is empty and amber when it holds pegs. The obvious reading, counting pegs in and out and ignoring colour and order, is refuted by the observations.
- **The grudge, from log 25** (a control: its explanation is finite and fits the rule language). Its observations and test cases are exactly log 25's.

**Observations:**
- Balance gate: 20, drawn by a fixed scramble from the sequences of up to six actions, 10 with the gate open and 10 shut.
- Peg tube: 24, from sequences of up to four actions, 8 for each light.
- Grudge: log 25's 14.

**Test cases** (shown to no one):
- Balance gate and peg tube: 6 short unseen ones, of the same lengths as the observations, drawn by the same scramble; and 6 long ones of 23 to 81 actions, written out below. In 10 of the 12 long ones the hidden count or pile goes deeper than 10.

*Corrected before any run: this first said "20 to 81 actions" and that every long case goes deeper than 10. A test measured them: the alternating balance-gate case only ever goes 1 deep (long but shallow, which checks that length alone does not beat a rule model), and the peg case "10 in, 5 out, 5 in, 10 out" reaches exactly 10. The cases themselves are unchanged.*
- Grudge: log 25's 12.

A test case is "hard" when the obvious reading gets it wrong.

Long test cases:
- Balance gate:
  - 30 pushes then 30 pulls: open.
  - 30 pushes then 29 pulls: shut.
  - 20 pulls then 20 pushes: open.
  - push and pull alternating, 50 actions: open.
  - 25 pushes, then 10 pulls, then 15 pulls: open.
  - 40 pushes then 41 pulls: shut.
- Peg tube, made by a fixed rule from a colour pattern:
  - 12 pegs in, then out in the right order: green.
  - 12 in, then 11 out in the right order: amber.
  - 12 in, then out with the 7th removal the wrong colour: red.
  - 15 in, then out in the right order: green.
  - 10 in, 5 out in the right order, 5 more in, 10 out in the right order: green.
  - 12 in, then out with the last removal wrong: red.

## The arms

The same DeepSeek V4.1 Flash at default thinking. Every arm gets the same description, the same observations, the same sentence "Keep track of anything you cannot see directly, if you need to", and the same sentence "Your explanation will be tested on sequences of any length, including sequences of a hundred actions."
- **Fixed language:** log 25's conjecture and criticism. DeepSeek writes a rule model in the checker's language; the checker runs it on every observation and reports exactly which fail and how; up to 6 models; the best is kept and graded by running it on the test cases.
- **Universal language:** the same loop, but DeepSeek writes a JavaScript function from the list of actions to what can be seen. JavaScript can express any computation. The program runs it on every observation, reports exactly which fail and how, and grades the best by running it on the test cases. Each function runs in a separate process with no access to files, the network or the account key, and with a time limit.
- **Bare:** DeepSeek answers the test cases directly, with its rule in words, as in log 25.

That is three devices, three arms and three repeats: 27 runs. About $1 to $3 of DeepSeek credit ($15.76 left).

## Conjectures, written before the run

1. **On the balance gate and the peg tube, the universal language gets more long test cases right than the fixed language,** summed over repeats.
2. **The fixed language gets fewer than half the balance gate's long test cases right** (fewer than 9 of 18), because a rule model can only count as far as the states it lists.
3. **On the grudge, the universal language does not beat the fixed language by more than 2 hard cases,** summed over repeats. If it does, the win on the other devices may come from DeepSeek writing JavaScript more easily than rule models, not from what the language can express.
4. **Bare DeepSeek gets fewer long test cases right than the universal language,** on the balance gate and the peg tube together. Counting through 60 actions in words is error-prone.
5. **On the peg tube, the universal language fits all 24 observations in at least 2 of 3 repeats,** and its best functions get at least 12 of 18 long test cases right.

## What would count against condition 2

- The fixed language getting as many long test cases right as the universal language. Then DeepSeek approximated well enough, or the tests did not reach past its approximations.
- The universal language beating the fixed language just as much on the grudge. Then the difference is familiarity with the notation, not what it can express.

## Traps

- **Reading a win for JavaScript as a win for universality.** Conjecture 3 is the control.
- **Reading this as a test of growth.** DeepSeek is handed a universal language; it does not build one.
- **Reading three repeats as settled.** Log 30 showed large run-to-run variation.
