# Status

**Where the project is today.**

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
- All tests pass: `11 checker tests.js` (20), `16 Sonnet guesser tests.js` (13), `17 error correction tests.js` (26), `19 baseline tests.js` (11), `20 who picks tests.js` (13), `21 long text tests.js` (16), `22 twenty questions tests.js` (11), `23 owner will not say tests.js` (9), `25 construction test tests.js` (39), `26 attack surface tests.js` (14), `16 page test in a browser.py` (12).
- DeepSeek balance after log 25: $1.93.
- The project lives in the h-EPI repository, folder `guess-check-fix`, on the branch `claude/deepseek-v4-project-j9k1ap`, waiting for the owner to merge it.

**Waiting on:** the owner, to top up the DeepSeek account ($1.93 left). Then log 26 runs as planned.

**Open questions:**
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
