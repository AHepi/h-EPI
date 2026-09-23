# Status

**Where the project is today.**

- DeepSeek V4.1 Flash is the guesser. Every live result comes from DeepSeek, and every run's record is in `runs/`.
- Ten test worlds, seven ways of running, and a test with 32 planted mistakes.
- Best way of running so far: "guesser fixes first". It is not the default of any script yet; the run script runs all the ways.
- All tests pass: `11 checker tests.js` (20), `16 Sonnet guesser tests.js` (13), `17 error correction tests.js` (26), `16 page test in a browser.py` (12).
- The project lives in the h-EPI repository, folder `guess-check-fix`, on the branch `claude/deepseek-v4-project-j9k1ap`, waiting for the owner to merge it.

**Waiting on:** nothing from the owner to continue. The next step in the project story needs about a dollar of DeepSeek credit.

**Open questions:**
- Can DeepSeek repair only what is broken, if asked to return only the rules it changes, so a repair stops re-guessing parts that were right?
- How many questions to the world is a real owner willing to answer? The full loop asked up to 12 per task.
- The world can only be asked about the things the shown jobs mention (the ghost lantern case). Should the owner be able to be asked about anything in the model?
- Do the results hold on other models? Only DeepSeek has been run.

## Traps

- **Reading this as history.** This file is rewritten to match today. The project story's log holds the history.
- **The account key.** It was pasted into the chat that made log 17 and 18. It should be replaced with a new one on DeepSeek's site; the project never stores it.
