# Cause and effect in the checker

Log entry 28. The owner asked me to fit causal relations into the checker, test it on a corpus of text, and say what it presupposes about cause. The plan, with five conjectures and the rule for choosing the corpus, was committed before any paragraph was turned into a model ("28 Plan - causal checker.md"). Every number here comes from the records in `runs/28 causal checker/`. What the checker presupposes is in "28 What the causal checker presupposes.md".

## The short answer

- **The checker works.** It answers "what if" questions by holding a thing and running the model. It tells seeing from making, and it answers "why" with "but for" tests. 30 tests pass, none calling an AI. One was added after the run: the route it prints ran past the held thing and round a loop in a frog model; it now stops at the held thing. No answer changed.
- **On 150 questions from a corpus other people wrote and answered, it gave people's answer on 101.** A direct answer from the same kind of AI, with no model, gave people's answer on 128.
- **Almost all of that gap is things the model does not contain.** When the reader could find both the change and the effect in the model (70 questions), the checker gave people's answer on 53 and the direct answer on 58. When it could not (80 questions), the checker can only say "no effect": 48 against 70.
- **On 11 questions, the checker and the direct answer agree with each other and not with people**, for example "more eggs laid, more frogs?", which people answered "fewer". Some of the corpus's answers are one reading among two, and some I cannot make sense of.
- **The checker never failed to settle an answer**, and nothing it was handed failed to read.

## An example first

Paragraph 689 is about growing plants. The translator (an AI that saw only the paragraph) wrote, among others:
- "sunlight raises plants";
- "weeds growing near the plants lower plants";
- "weeds removed lower weeds growing near the plants";
- "plants raise plants that grow to maturity";
- "weeds growing near the plants lower plants that grow to maturity".

The question "suppose more seeds of weeds are available, how will it affect less crops?" was put to the reader (an AI that saw the model and the question, but not the paragraph or the answer). The reader linked "more seeds of weeds" to "weeds growing near the plants: more" and marked the link. It matched "less crops" to "plants that grow to maturity", pointing to less.

The checker held the weeds at "more" and ran the model: plants went to "less", and so did plants that grow to maturity, by both routes. "Less crops" happens more, so the answer is "more". People said "more" too.

The question "suppose more weeds grow, how will it affect more space for plants?" went differently. The model has no "space", so the reader matched the effect to nothing, and the checker could only say "no effect". People said "less".

## Everything

| Questions | How many | Checker same as people | Direct answer same as people |
|---|---|---|---|
| in paragraph (the change is a step of the paragraph) | 50 | 28 | 42 |
| from outside (the change comes from outside the paragraph) | 50 | 25 | 39 |
| unrelated (people's answer is always "no effect") | 50 | 48 | 47 |
| all | 150 | 101 | 128 |

Split by whether the reader found both the change and the effect in the model:

| | How many | Checker same as people | Direct answer same as people |
|---|---|---|---|
| both found | 70 | 53 | 58 |
| in paragraph | 38 | 28 | 31 |
| from outside | 30 | 25 | 26 |
| unrelated | 2 | 0 | 1 |
| one or both not found | 80 | 48 | 70 |

Other counts:
- The reader linked an outside change to a model thing 19 times (13 from outside, 5 in paragraph, 1 unrelated); the checker gave people's answer on 15 of those.
- The checker never said "unsettled" and never met an unreadable model or reading.
- Seeing and making differ in every model. Across the five models, 341 pairs of things go together when seen but not when made, and 497 go together both ways. For example, in paragraph 517's model: in the runs where more frogs end up on land, more eggs hatched in 3 of 5. But making more frogs reach land changes no eggs. That is the dark room and the lamp, in a frog model. (The frog model for paragraph 515 has a loop from frogs back to eggs, so there making frogs does change the eggs.)

## The conjectures

1. **Unrelated questions: the checker gives "no effect" on at least 45 of 50.** *Not refuted:* 48.
2. **In paragraph: the checker gives people's answer on at least 35 of 50.** *Refuted:* 28.
3. **From outside: less often than in paragraph.** *Not refuted:* 25 against 28, a small difference. Where both were found in the model, the other way round: 25 of 30 against 28 of 38.
4. **The direct answerer gives people's answer more often than the checker.** *Not refuted:* 128 against 101.
5. **Why they disagree: reading and model more than half, unsettled at most one in ten.** *Not refuted.* Of 49 disagreements, my reading after seeing the answers (in `disagreements.json`):
   - (a) reading: 36. In 32 the question's words matched nothing in the model, for example "weather", "space", "polliwogs" (a word for tadpoles the reader did not match), "fertile". In 4 a word was matched to the wrong thing, or linked when it should not have been: "living in a rain forest" was linked to "more rain" on a question people call unrelated.
   - (b) model: 2. The frog model in paragraph 517 has no way back from frogs to eggs.
   - (c) unsettled: 0.
   - (d) arguable: 11. My fixed list said "one of two fair readings". Most of these are not that: they are answers that both the checker and the direct answerer contradict, such as "more eggs laid, more frogs?", answered "fewer". One is an "unrelated" question that is not unrelated: "fewer eggs are laid" was paired with a frog paragraph, because three of the five paragraphs are about frogs. The direct answerer agreed with the checker, not people, on all 11.

## What this means for the idea

- **The checker draws out consequences faithfully, and nothing more.** Where the model held both ends of the question, the checker and a direct answer did about as well (53 and 58 of 70), and most of the checker's misses there were questions where the direct answer agreed with the checker.
- **Its weak point is what the model leaves out,** as presupposition 5 predicts ("what is not in the model has no effect"). The direct answerer knows about weather, space and polliwogs. The model knows only what the translator wrote, and the checker cannot tell "no effect" from "not modelled".
- **Linking the world's words to the model's things is a causal claim in its own right, and the checker never tests it.** "A rain forest has more rain" was the reader's claim, and it produced the checker's one wrong "effect" on an unrelated question.
- **Nothing here needed sizes.** No question came out unsettled. The corpus's questions are about one push at a time, so presupposition 8 (no sizes) was never tested.
- **The corpus is a weak world.** People's answers disagree with the plain reading of the paragraph in several places. Agreement with them is a stand-in for being right, and here a rough one.

## What was not tested

- DeepSeek, as translator or reader: the owner asked to wait for a top-up. All three roles were played by Claude, the AI running this project, in separate conversations that could not see each other's work or people's answers.
- The "why" questions and the seeing-and-making contrast against people's judgements. The corpus has no such questions; both were checked only on hand-made examples and counted on the models.
- Questions with two pushes at once, sizes, timing or chance.
- A second corpus, or paragraphs on more than three topics.

## Traps

- **Reading 101 against 128 as the checker reasoning worse.** It reasons only over what the model holds; most of the gap is what the model does not hold.
- **Reading agreement with people as being right.** On 11 questions, both AIs disagreed with people in the same way.
- **Reading this as a result about DeepSeek.** DeepSeek was not used.
- **Reading the causes of disagreement as measured.** They are my reading, made after seeing the answers.
