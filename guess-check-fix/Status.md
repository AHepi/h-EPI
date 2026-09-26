# Status

**Where the project is today.**

- The changed method works where it is used (log 40): in the checker's correction loop, DeepSeek's methods let through far less damage than the current one; but my declared aims conflicted on a few starts, so by the plan none counts as a repair there.
- The system changed one of its own methods (log 39): DeepSeek rewrote the checker's fix-acceptance method, and the program kept it only because it met declared aims on fixes DeepSeek never saw; shown the failure, it beat the person's repair from log 17.
- A rule language that can grow closes the gap (log 35): given a door to add a new kind of thing, DeepSeek held an unlimited count and pile as well as in JavaScript. On the grudge the door let its old running-score habit in.
- The checker's rule language cannot hold an explanation that needs an unlimited count or pile (log 34); DeepSeek wrote such explanations in JavaScript every time. On a device the rule language can hold, both did the same.
- A system prompt, or a character to play (log 32), does not steer DeepSeek's questions (log 30): the same text twice differs as much as two different texts; instructions naming a measure were mostly ignored; any text raised how often an answer surprised it.
- Cause and effect are in the checker (log 28): "what if", seeing and making, and "why". On 150 questions from a corpus other people wrote and answered, it gave people's answer on 101, a direct answer 128; the gap is almost all things the models leave out. What it presupposes about cause is in "28 What the causal checker presupposes.md". Claude played every role; DeepSeek was not used.
- DeepSeek V4.1 Flash is the guesser. Every live result comes from DeepSeek, and every run's record is in `runs/`.
- Ten test worlds, seven ways of running, and a test with 32 planted mistakes.
- Best way of running so far: "guesser fixes first". It is not the default of any script yet; the run script runs all the ways.
- Tested against DeepSeek alone and against spending more tokens (log 19): more tokens do not close the gap between DeepSeek alone and the loop; answers from the world do.
- The attack surface (log 26): planned, built and tested offline; not run.
- The construction test (log 25): with the evidence fixed and no way to ask, the error-correction loop did not beat bare DeepSeek overall; on the grudge, writing an explicit explanation beat every bare run; the first explanation always fitted the evidence, so nothing was ever refuted.
- The owner will not say (log 23): refused an answer to its own question, DeepSeek worked it out from other questions, including in the world it had always misread.
- Twenty questions (log 22): made to ask 20 questions one at a time, DeepSeek asks well (at least as good as random questions) but first asks the owner their own question back, and costs six and a half times as much.
- Long texts (log 21): DeepSeek finds a question buried in about 2,300 words, and answers from the world help as much as with short requests; but when it may stop whenever it likes, it almost never asks.
- Who picks the questions (log 20): random questions helped as much as the loop's; DeepSeek's own choice helped least; the loop's rule model was about level with DeepSeek alone. More answers from the world is what reliably helps.
- All tests pass: `11 checker tests.js` (20), `16 Sonnet guesser tests.js` (13), `17 error correction tests.js` (26), `19 baseline tests.js` (11), `20 who picks tests.js` (13), `21 long text tests.js` (16), `22 twenty questions tests.js` (11), `23 owner will not say tests.js` (9), `25 construction test tests.js` (39), `26 attack surface tests.js` (14), `28 causal checker tests.js` (30), `30 system prompt tests.js` (10), `34 language tests.js` (23), `35 growing language tests.js` (21), `39 changing a method tests.js` (19), `40 kept method at work tests.js` (7), `16 page test in a browser.py` (12).
- DeepSeek balance after log 39: $14.22.
- The project lives in the h-EPI repository, folder `guess-check-fix`, on the branch `claude/deepseek-v4-project-j9k1ap`, waiting for the owner to merge it.

**Waiting on:** nothing. Next: log 26 runs as planned.

**Open questions:**
- To explore later (log 33): is humanity, with its writing and institutions, the universal explainer, and individual humans creative agents whose coming together produces it? Deutsch holds each person is one; what would a single person lack?
- Which of log 33's seven conditions for a universal explainer are necessary? Each can be tested by taking it away; conditions 2 (a language that can express any explanation) and 6 (methods open to criticism) are the ones the project lacks.
- Can the checker's "not in the model" answers be turned into criticism of the model, so the translator adds what a question needs (weather, space) rather than the checker saying "no effect"?
- Does DeepSeek, as translator and reader, do as well as Claude did in log 28?
- Does DeepSeek, asked, expose its conjecture to attack, and does rebuilding fresh from the world's answers beat defending in the same conversation?
- With a way to be refuted (questions chosen by the hard-to-vary sweep), does the explanation loop beat bare runs given the same number of answers?
- Does this work on a real request, with a real person answering?
- Would an owner who can say what happens along the way, not only how it ends, close the hidden-ball gap?
- How few questions, asked one at a time, give most of the benefit?
- Would a different instruction make DeepSeek ask on its own when it is unsure?
- Does choosing questions matter when there are only one to three of them?
- Are the rule models worth keeping? They did not answer better than DeepSeek alone in log 20; they do give a model that can be run and tested part by part, and they repaired every visible planted mistake (log 18).
- Can DeepSeek repair only what is broken, if asked to return only the rules it changes, so a repair stops re-guessing parts that were right?
- How many questions to the world is a real owner willing to answer? The full loop asked up to 12 per task.
- The world can only be asked about the things the shown jobs mention (the ghost lantern case). Should the owner be able to be asked about anything in the model?
- Do the results hold on other models? Only DeepSeek has been run.

## Traps

- **Reading this as history.** This file is rewritten to match today. The project story's log holds the history.
- **The account key.** It was pasted into the chat that made log 17 and 18. It should be replaced with a new one on DeepSeek's site; the project never stores it.
