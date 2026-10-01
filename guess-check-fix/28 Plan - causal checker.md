# Plan: cause and effect in the checker

Written before any paragraph was turned into a model, and not to be changed after. The results go in "28 Causal checker.md"; what the checker takes for granted about cause goes in "28 What the causal checker presupposes.md".

## What the owner asked

"See if you can fit causal relations into the checker. For this you will need a corpus of text. I'm not sure how you will select it though. Once you have a working checker, I'll be interested to know what it presupposes about causality."

## What was built

`28 causal checker.js`, on top of the checker. The checker could already hold a thing in one state, whatever its rules say. The new part uses that for three kinds of question:

- **What if:** hold one thing at a level and compare with the usual run. Did the thing asked about go up, down, or stay the same, and which rules carried the change?
- **Seeing and making:** a dark room tells you the lamp is off, but making the room dark does not switch the lamp off. The checker gives both answers, so a model's direction of cause shows.
- **Why:** in one situation, take away each thing that made it differ from the usual start and see whether the outcome changes ("but for this..."). If no single one matters but a pair does, the checker reports two causes, each enough on its own.

A shorthand, "influences", lets a model say "more rain makes more runoff" ("same") or "more plant cover makes less erosion" ("opposite"). The checker turns each influence into ordinary rules on three levels: usual, more, less. 29 tests, all passing, none calling an AI (27 on the checker, 2 on picking the sample).

## The corpus, and how it was chosen

**WIQA** ("What If Question Answering", Allen Institute for AI, 2019). It holds short paragraphs about how something works, each with questions like "suppose more rain falls, how will it affect more erosion?". People answered each one with more, less or no effect. There are three kinds of question:
- **in paragraph:** the change is a step of the paragraph;
- **from outside:** the change comes from outside the paragraph;
- **unrelated:** the change has nothing to do with the paragraph, and people's answer is always no effect.

Why this corpus:
- Other people wrote it, before this project, for a different purpose. I did not choose texts that suit the checker.
- Its questions are exactly "what if" questions about how things work, which is what the checker can answer.
- People answered every question, and those answers stand in for the world. They are one reading, not the truth.

How the questions were picked, by a fixed rule written into `28 causal corpus.js` before anything was looked at:
- the test part of the corpus (41 paragraphs, 3,003 questions);
- its paragraphs in a fixed scramble (each id scrambled with the words "log 28"), and the first five taken;
- in each paragraph, for each kind, the first ten questions in the same scramble.

That gives 150 questions.

**What I saw before writing this plan:** the corpus's layout, two question stems from paragraphs not in the sample, and the five picked paragraphs. Three are about frogs growing from tadpoles, one about growing plants from seed, one about a cell copying its DNA. That is where the fixed rule landed, and it is kept, not re-drawn. I have not seen the picked questions or their answers.

The corpus is not stored in the repository, because its licence is not stated where it is published. The script downloads it, and the picked ids are kept in `runs/28 causal checker/sample.json`.

## Who does what

DeepSeek is not used: the owner asked to wait for a top-up. The translating is done by Claude, the AI running this project, in three separate conversations, each given only what its step needs:

1. **The translator** gets one paragraph at a time and the model language, never the questions. It writes a model of the causes in the process.
2. **The reader** gets each model, but not its paragraph, and the questions, never people's answers. For each question it says which thing in the model the supposed change touches, and at what level, and which thing the question asks about, and in which direction. It is told not to work out the answer. It may link an outside change to a model thing ("more rain" acts on "water"), and must mark each such link.
3. **The direct answerer** gets each paragraph and its questions, and answers more, less or no effect straight away. It sees no model and no answers. This is the baseline.

The checker then answers each question from the model and the reading. Both the checker's answers and the direct answers are compared with people's. Every model, reading and direct answer is kept in `runs/28 causal checker/`.

## Conjectures, written before the run

1. **Unrelated questions:** the checker gives people's answer (no effect) on at least 45 of 50.
2. **In paragraph:** the checker gives people's answer on at least 35 of 50.
3. **From outside:** the checker gives people's answer less often than in paragraph.
4. **The direct answerer gives people's answer more often than the checker**, over all 150.
5. **Why they disagree.** Each question where the checker and people differ is given one cause from a list fixed now:
   - (a) *reading:* the question's words were matched to the wrong thing, or a needed link was not made;
   - (b) *model:* an influence is missing or points the wrong way;
   - (c) *unsettled:* two influences push opposite ways and the checker cannot weigh them;
   - (d) *arguable:* people's answer is one of two fair readings of the question.

   The conjecture: (a) and (b) together are more than half, and (c) is at most one in ten. Giving causes is my reading after seeing the answers, and the report says so.

## What would count against the idea

- **Unrelated questions often given an effect:** the reader links anything to anything, and the checker is only as good as the links it is handed.
- **In paragraph no better than from outside:** the model adds nothing beyond the reader's own links.
- **Many unsettled answers:** a checker without sizes cannot answer ordinary "what if" questions.

## Traps

- **Reading agreement with people as the checker being right.** People's answers are one reading; some questions are awkward ("how will it affect less erosion?").
- **Reading the direct answerer's score as a limit of the checker.** They are the same kind of AI; the direct answerer uses what it knows, and the checker uses only what the model holds.
- **Reading this as a test of DeepSeek.** It is not; DeepSeek is not used here.
- **Three of five paragraphs are about frogs.** The questions overlap in topic; this is not five independent processes.
