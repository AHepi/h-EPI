# Construction test

Log entry 25. The owner asked for a test of error correction as the semantics means it: can DeepSeek, with error correction, solve a problem a bare run can't, even with repeated loops? The plan and its conjectures were committed before the runs they are tested on ("25 Plan - construction test.md"). Every number here comes from the records in `runs/25 construction test`, made with DeepSeek V4.1 Flash at its default thinking setting on 24 September 2026: four made-up devices, three repeats (the sixth arm, two).

## The short answer

- **No, not overall.** Given the same evidence, the error-correction loop did not beat a bare DeepSeek that answers directly: 84 of 96 hard test cases, against 85 for five bare answers with a majority vote and 85 for a bare run that checks itself three times.
- **On one device a bare run failed every time, and writing an explicit explanation did better.** The neighbour's grudge: every bare arm scored 9 or 10 of 12 in all nine of its runs. The explanation arms scored 9 to 12, and higher than every bare run of the same repeat in 7 of 8 runs. Asking five times or checking itself three times did not move the bare runs at all: they all made the same mistake, "Robin is warm when kind acts outnumber insults".
- **But what helped was the form, not the correcting.** In all 32 explanation attempts, the very first explanation already fitted all 14 observations. The evidence never refuted anything, so criticism of failed observations never happened. On the grudge, the gain came from being made to write the explanation as states and rules, which led DeepSeek away from the running score it reached for in words.
- **The real limit: 14 observations cannot refute a wrong explanation that happens to fit them.** Explanations that fit everything still got as few as 95 of the 120 possible sequences right in the grudge and the vial. The semantics predicts exactly this (Derivation 3): what a history of observations leaves open, it leaves open.
- **Hard-to-vary criticism is the one correction that worked without new information, a little.** Once an explanation fitted, the checker criticised it for parts no observation holds in place, and DeepSeek wrote a new one. On repeats 2 and 3 this got 58 hard cases against 55 for conjecture and criticism, and its explanations had no such parts, where the others had up to 52. It helped on the vial (reach 110 of 120 in one run, against 95 to 98), and made the magnet ball slightly worse (111 against 120).
- **More tokens did not help on the problem that mattered.** On the grudge, five bare answers cost five times the tokens and scored the same 9 every time.

## An example first: the grudge

The description: you can insult Robin, apologise, or give a gift; all you see is whether Robin is warm or cold. The hidden rule: one insult hurts, and an apology mends a hurt; a second insult goes deep, and then an apology does nothing until a gift softens it back to hurt.

What the bare runs said, in their own words, in the three repeats: "warm if the number of kind actions is strictly greater than the number of insults"; "a hidden mood score: apologise and gift each add 1, insult subtracts 1"; "insult subtracts 2, apology adds 2, gift adds 1". All three fit the 14 observations. All three are a running score, the familiar way to think about feelings, and all three get "gift, then insult, then insult, then apologise" wrong: a score says the gift banked goodwill; Robin is in fact still cold.

The explanation arms wrote states: "standing", "anger", "cold type", with a level for "deep". That is the hidden thing the device needs. Most of their explanations still had small errors elsewhere (reach 95 to 118 of 120), and nothing in the 14 observations could show them.

## Everything

Hard test cases are the 8 per run that the obvious explanation gets wrong.

| Arm | Test cases right | Hard cases right | Easy cases right | Runs with every test right | DeepSeek calls | Output tokens |
|---|---|---|---|---|---|---|
| bare | 122/144 | 78/96 | 44/48 | 6/12 | 12 | 239,219 |
| bare, majority of 5 | 133/144 | 85/96 | 48/48 | 7/12 | 60 | 1,136,720 |
| bare, checks itself | 133/144 | 85/96 | 48/48 | 8/12 | 48 | 556,602 |
| conjecture and criticism | 130/144 | 84/96 | 46/48 | 6/12 | 12 | 119,344 |
| blind retries | 122/144 | 79/96 | 43/48 | 6/12 | 12 | 149,361 |
| conjecture, criticism and hard to vary (repeats 2 and 3) | 88/96 | 58/64 | 30/32 | 2/8 | 14 | 213,557 |

By device, test cases right of 12, repeats 1, 2, 3:

| Device | bare | majority of 5 | checks itself | conjecture and criticism | blind retries | hard to vary |
|---|---|---|---|---|---|---|
| gate | 12, 12, 12 | 12, 12, 12 | 12, 12, 12 | 12, 12, 12 | 12, 12, 12 | -, 12, 12 |
| grudge | 9, 9, 10 | 9, 9, 9 | 9, 9, 9 | 11, 11, 9 | 12, 10, 11 | -, 11, 11 |
| magnet ball | 12, 12, 12 | 12, 12, 12 | 12, 12, 12 | 12, 12, 12 | 2, 12, 12 | -, 11, 11 |
| vial | 11, 0, 11 | 11, 12, 11 | 12, 10, 12 | 9, 9, 9 | 9, 9, 9 | -, 9, 11 |

The bare 0 in the vial, repeat 2, is one reply that thought until the reply limit and gave no answer. 17 bare replies in all were cut off that way; the explanation arms had none.

## The conjectures

1. Conjecture and criticism gets more hard cases right than every bare arm: **refuted** (84 against 85 and 85).
2. Bare, majority of 5 does no better than bare: **refuted as written** (85 against 78); most of the gap is the one cut-off bare reply.
3. Bare, checks itself does no better than bare: **refuted as written** (85 against 78), for the same reason.
4. Conjecture and criticism does better than blind retries: **not refuted** (84 against 79), mostly from one blind run on the magnet ball that fitted all 14 observations with an explanation right on only 53 of 120 sequences.
5. Where conjecture and criticism explains all 14 observations, its explanation has a hidden thing and reaches nine tenths of all sequences: **refuted.** Every one had a hidden thing, but in the grudge and the vial the reach was 95 to 102 of 120.
6. Hard to vary gets more hard cases right than conjecture and criticism on repeats 2 and 3, with fewer parts not held in place: **not refuted** (58 against 55; 0 such parts in every run, against up to 52). Eight runs; a difference of three is small.

## What this means for the idea

- **Error correction needs something that can refute.** Here the only criticism available was 14 observations, and every first explanation passed them. The earlier logs had more to go on: questions to the world (logs 20 to 23) gave criticism that corrected mistakes, the borrowed lantern above all. With the evidence fixed, there was nothing for correction to act on, and a bare DeepSeek, which reasons in words, did as well.
- **The semantics' own standard for criticism, hard to vary, does something even without new evidence**: it made DeepSeek throw out parts nothing holds in place, and on the vial that raised reach. It is a weak lever on its own.
- **Where bare DeepSeek fails, it fails the same way every time.** On the grudge, the 15 single bare answers scored 9 or 10 (fourteen 9s and one 10), and in all three self-checking runs DeepSeek kept the same running-score rule through every one of its four rounds, even when told to check it against each observation. That is what the semantics calls a selected transport: its training's habit, faithful where it was shaped, wrong on the change it was never shaped against. More tries of the same kind cannot fix that; something with a different form did, partly.

## What was not tested

- The explanation arms with a way to find criticism: questions to the world chosen by the hard-to-vary sweep, against bare runs given the same number of answers.
- More devices. With four, one device (the grudge) carries the only clear gap.
- Other models, other thinking settings, a person answering.

## What it cost

$2.55 of DeepSeek credit ($4.48 before, $1.93 after): $0.73 for repeat 1, $1.82 for repeats 2 and 3 with the sixth arm.

## Traps

- **Reading the grudge result as error correction.** The explanation arms' first explanation already fitted; the gain came from writing states and rules, not from correcting.
- **Reading "fits all 14 observations" as "right".** Every explanation did, and most were wrong somewhere else.
- **Reading conjecture 6 as settled.** Eight runs; and the arm was designed after seeing repeat 1.
