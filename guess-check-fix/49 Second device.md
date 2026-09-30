# A second device: the heater

Log entry 49. Every result from log 44 to 48 was about the grudge. This took the main comparison to a second made-up device, the heater: bare DeepSeek, DeepSeek given 6 random answers from the world, and rivals choosing the world's 6 questions (as log 46). Every arm ended with a fresh DeepSeek writing one explanation as a small program, graded on every sequence of up to six actions. The plan and six conjectures were committed before any DeepSeek call ("49 Plan - second device.md"). Every number here comes from the records in `runs/49 second device/`, made with DeepSeek V4.1 Flash at its default thinking setting and a reply limit of 200,000 tokens, on 30 September 2026.

## The short answer

- **No run found the true heater, in any arm.** 18 final explanations and 48 rivals; none right everywhere.
- **Rivals choosing the questions did worst here,** the reverse of the grudge. Long sequences right, of 5,832: random answers 5,049, bare 4,765, rivals choose 4,604. The plan named this as counting against the grudge's pattern holding.
- **The same blind spot as log 48, more plainly.** The one short situation that shows what waiting does ("up, up, wait, up", which ends warm) was asked in no run of either arm that asked the world anything. No rival treated waiting as mattering, so the rivals never disagreed there, so the program never asked. Choosing questions where the rivals disagree cannot find a part none of the rivals has.

## An example first

In the true heater, turning up twice trips a cut-out and the room goes cold. The dial then does nothing until you wait, which resets the heater to off.

None of the 14 observations shows that waiting does anything. After a trip, waiting turns the heater off, and the room is cold either way. Only one more action after the wait, a turn up, shows it: the room warms again. Within four actions, that is exactly one situation: "up, up, wait, up".

The best explanation of the run, bare repeat 6, said: "Turning up past 3 overheats the heater, making the room permanently cold." That gets 105 of 106 short sequences and 922 of 972 long: it has the cut-out, but a cut-out that never resets. All five explanations that scored 105 (four from random answers, and this one) miss exactly one short situation, the same one: "up, up, wait, up" (checked after the results).

## Everything

For scale, from the plan: the true heater 106 short and 972 long; common sense 83 and 741; "a count of ups minus downs" 100 and 836.

| Arm | Short right (of 106 per run, summed over 6) | Hard short right (where common sense is wrong) | Long right (of 972 per run, summed over 6) | By repeat (short / long) | Answers from the world |
|---|---|---|---|---|---|
| bare | 526 | 97 of 138 | 4,765 | 90/865, 78/763, 90/768, 90/740, 73/707, 105/922 | 0 |
| random answers | 579 | 113 of 138 | 5,049 | 105/921, 105/922, 82/693, 105/896, 105/904, 77/713 | 36 |
| rivals choose | 509 | 97 of 138 | 4,604 | 101/900, 86/720, 88/789, 92/806, 55/625, 87/764 | 36 |

- **Rivals:** 48 written, all ran, all fitted every fact known when written; none was the true heater everywhere.
- **"Up, up, wait, up"** was asked in 0 of 12 runs that asked the world anything. It is the only situation of up to four actions that shows the reset. It is neither an observation nor a test case, so the world would have answered it.
- **No reply was cut off.** DeepSeek wrote about 1.6 million output tokens, far more than on the grudge.

What DeepSeek's explanations looked like: most kept a dial position and a room state, and several had the dial run backwards ("turn up lowers it") or had five hidden states "as coded". Only one (bare, repeat 6) named overheating. A few gave waiting some effect (random answers, repeat 4: "wait: if x is 0, warm"), but none had waiting reset a cut-out.

## The conjectures

1. **No reply is cut off.** *Not ruled out.*
2. **Bare DeepSeek is the true heater everywhere in at most 3 of 6 runs.** *Not ruled out:* 0 of 6. The device was not too easy.
3. **Rivals choose gets more long sequences right than bare.** *Ruled out:* 4,604 against 4,765.
4. **Rivals choose gets more long sequences right than random answers.** *Ruled out:* 4,604 against 5,049.
5. **Rivals choose is the true heater everywhere in more runs than random answers.** *Ruled out:* 0 against 0.
6. **At least one rival is the true heater everywhere.** *Ruled out.*

## What this means for the idea

- **"Rivals choose the questions" is not a general gain.** On the grudge it helped (log 46); on the heater it did worst. With two devices it goes both ways, so I no longer claim it helps.
- **The blind spot is now the main finding.** Log 45: DeepSeek's own questions aimed where its rule differed from the obvious one. Log 48: the program's questions aimed where the rivals differed most. Here: no rival imagined that waiting matters, so the one situation that shows it was never asked. Every way of choosing questions tried so far can only look where some current guess already points. A part that no guess contains is reached only by luck. Random answers had a small chance of hitting it, and did not.
- **Why random answers beat the rivals here, as far as I can tell:** random questions spread across the space, while the rivals' questions clustered on the details the rivals argued about (where the dial is, what turning down does). DeepSeek then fitted those details with odd, specific rules that broke on long sequences (repeat 5 of rivals choose: 55 of 106). This is a reading of the records, not a test.
- **In the semantics' terms:** criticism from the world only bites where it is aimed. Aiming it by the current conjectures finds errors within their shared frame, never outside it. Finding "waiting matters" needs either a conjecture that has it, or a question that is not chosen by the conjectures at all.

## Failures along the way

- **My first heater design was too weak,** and was fixed before the plan (see the plan). The fixed design has its own gap, seen only after the run: just one short situation shows the reset. I checked offline which rules the design separates, but not how many situations show each hidden part. So this device tests "can the system find a part shown by one situation in 106", which is harder than I set out to test.
- **My plan's cost estimate was low:** $0.90 against $0.40 to $0.60, because DeepSeek thought far longer on the heater.
- **A test that could never fail** (it ended with "or true") was in my first draft of the tests. Found and removed before the plan was committed.

## What was not tested

- A heater whose reset is shown by more short situations.
- Questions chosen by a rule that does not depend on the current guesses, beside rivals choosing.
- Longer questions on this device.

## What it cost

$0.90 of DeepSeek credit ($11.60 to $10.70).

## Traps

- **Reading this as "random questions are best".** On the grudge, rivals choose beat random answers (log 46); here the reverse. Two devices, six repeats each.
- **Reading "no run found the true heater" as DeepSeek failing where a person would not.** The deciding situation was never asked; no one, person or program, sees the reset without it.
- **Reading one extra device as a general result.**
