# Plan: the construction test

Written before any run of log 25, and not changed after. The results go in "25 Construction test.md".

## What the owner asked

"My actual goal is error correction. [...] the semantics I gave you is about creativity, not spotting little semantic tricks. At the heart of creativity is error correction. Maybe go over the semantics to see what I'm actually testing. Then run a test that meets the standards. If anything, we know Deepseek has a limited knowledge base. But can we get it to solve a problem a bare run can't? Even with repeated loops."

## What the semantics asks for

- **Creativity is construction.** When the world contradicts an explanation, a system can respond by **selection**, re-tuning within what it already has, or by **construction**, building a new explanation with a represented target, often with a part it did not have (Part IV, "Two responses to a violation"). Only construction can be originative (Part X). Derivation 10 is the model case: a layer that predicts from what it sees fails when a thing is hidden; no re-tuning fixes it ("the fidelity failure is structural, not parametric"); a new organization with a persistent thing does.
- **Error correction is conjecture and criticism** (Part I) producing a **repair**: a failing obligation fixed, protected ones kept (Part XI, condition P).
- **An explanation is judged by fidelity under change** (Part V), not by fitting: it must answer the question for changes in its contract it was not shown. That is reach.

## The test

- **Problems DeepSeek cannot know:** four made-up devices (a neighbour's grudge, a ball in a tray that is sometimes magnetised, a gate that counts, a vial that stores a charge). Each has a rule against the obvious reading, and the right explanation needs a hidden thing nobody mentions. Checked before any run: the observations refute the obvious explanation in every device, and in every device the observations contain the same visible state and action leading to different outcomes, so no explanation using only what can be seen can fit them.
- **Same evidence for every arm:** the description and 14 observations, and the same sentence about unseen things. No arm may ask for anything more. So any difference comes from what is done with the evidence, not from extra information (the confound in logs 19 and 20).
- **Graded on 12 unseen test cases per device**, no longer than the observations: 8 the obvious explanation gets wrong, 4 it gets right.
- **Arms:** bare; bare, majority of 5 (more tokens, which is selection); bare, checks itself (three rounds of rereading its own rule against every observation, which is repeated loops without an outside critic); conjecture and criticism (an explicit explanation, run against every observation by the checker, with exactly what failed reported back, up to 6 explanations); blind retries (the same, told only how many fail, which is selection with blind variation).

## Conjectures, written before the run

Each can be refuted by the records.

1. **Conjecture and criticism gets more test cases right than every bare arm**, summed over all runs, on the 8 hard cases per run.
2. **Bare, majority of 5 does no better than bare** on the hard cases (within two cases, summed): more tries of the same kind do not construct.
3. **Bare, checks itself does no better than bare** on the hard cases (within two cases, summed).
4. **Conjecture and criticism does better than blind retries** on the hard cases: what makes the difference is criticism with content, not more tries.
5. **Where conjecture and criticism explains all 14 observations, its explanation has a hidden thing**, and its reach is at least nine tenths of all sequences of up to four actions (120 sequences, or 30 for the gate).

*Corrected before any run: conjecture 5 first said "at least 110 of 120", but the gate has only two actions and so 30 sequences.*

## Added after repeat 1, before repeats 2 and 3

Repeat 1 (all five arms, one run per device) showed explanations that fit all 14 observations and still got test cases wrong: in the vial both explanation arms, in the magnet ball blind retries (53 of 120 sequences right). The loop stops once everything fits, so a wrong explanation that fits is never criticised again. Read offline, at no cost, the checker's hard-to-vary sweep separated them: the true models have at most two parts the observations do not hold in place (idle: removing them changes no observation; unknown: no observation makes them act), and the wrong fitting ones had 12 to 28.

So a sixth arm is added: **conjecture, criticism and hard to vary.** Like conjecture and criticism, but once an explanation fits, the checker criticises it for those parts and DeepSeek writes a new one, with the same limit of 6 explanations and the same 14 observations. It keeps the fitting explanation with the fewest such parts, and stops when a new one has no fewer. A true explanation can have a part the observations happen not to test, so the aim is fewest, not none.

This arm was designed after seeing repeat 1, so repeat 1 is not evidence for it. The conjecture below is tested on repeats 2 and 3 only:

6. **Conjecture, criticism and hard to vary gets more hard test cases right than conjecture and criticism**, summed over repeats 2 and 3, and its kept explanations have fewer parts not held in place.

## How much

$4.52 of DeepSeek credit is left. First one repeat of all four devices; if the cost allows, more repeats with the same code. (Repeat 1 cost $0.73; repeats 2 and 3 are run with the sixth arm added.) Every record is kept, whichever way it comes out.

## Traps

- **A win for conjecture and criticism partly because its answers are computed by running the explanation.** Test cases are no longer than the observations (four actions at most), so the working-out is short; the bare arms are asked for their rule too, so a right rule with a wrong prediction can be seen in the records.
- **Choosing devices where the bare runs fail.** The devices were fixed, and checked only against the true and obvious explanations, before any DeepSeek call.
