# Lessons

Failures in building and testing, and how each was fixed. Only cases where something failed to work: a build step, a test, the checker, the loop, or a guesser's attempt.

| Log | What failed | How it was fixed |
|---|---|---|
| 02 | The small AI's server stopped between steps. | Start it in the same step as the work, detached from the terminal. |
| 04 | States like "game over" arrived one step late, so a hidden true world failed its own jobs. | After each event, everything settles before the next event. |
| 05 | Checker reports were noisy or unclear (repeated events not told apart, warnings that fired on correct models). | Reworded and narrowed each message; repeated events named by position. |
| 08 | A checker explanation said a rule "never fired" when it had fired and been blocked by a disagreement. | The explanation now says the rule was blocked, and points to the disagreement. |
| 08 | The small AI could not apply a fix, even when told the exact one. | The checker applies small fixes; the small AI is asked only for new parts. |
| 10 | The small AI's server was still loading when the loop started, and the first request failed. | Wait until the server says it is ready; retry a failed request. |
| 11 | Steps longer than five minutes were cut off. | Long runs go into the background and save as they go. |
| 12 | The small AI gave the identical reply when asked again. | Raise the randomness on later tries, and list what was already tried. |
| 12 | The small AI wrote rules that could never fire ("when the ball is at 1 and at 2"). | The checker reports them, and offers a small fix that keeps one of the clashing conditions. |
| 13 | The held-back jobs could not catch a shortcut rule that jumped straight to the answer. | Added one held-back job that catches it, labelled as added later. |
| 15 | The project's files were lost: nothing had been downloaded, and the earlier computer was reset. | Rebuilt from the earlier chat's record; every change checked against its exact old text; all 20 checker tests pass again. |
| 16 | The loop refused the right new part for the hidden ball: the new rules disagreed with old wrong rules, and the loop could only add. | Clearing out: after a new part, the checker also tries the model without those old rules. |
| 16 | On a phone, the results grid hid two of the four ways off to the side. | One small table per world, with the four ways stacked. |
| 17 | The full loop made the lighthouse story worse: the checker's repair deleted a condition, fit every job, and was still wrong. | The checker can swap a condition for one about a different thing; each checker fix is cross-checked with the world. |
| 17 | The loop never asked about one put-off in the to-do app, because it only asked where it could see a rival rule. | The full loop looks for surprises near the jobs. |
| 17 | The surprise questions never ran: the loose-rule questions used up the rounds. | Surprise questions have rounds of their own. |
| 17 | The list of held-back jobs "asked about" counted a job just for sharing a situation with a shown job. | Only questions to the world count. |
| 17 | "No new parts" (zero) was read as "use the default of 3", so the checker-alone corrector would have asked DeepSeek. | Zero now means zero. |
| 18 | One of my river-crossing jobs expected something the puzzle does not settle. | The job asks only about the goose. Found before any run, by running each true model on its own jobs. |
| 18 | The checker's one-step patches in the river puzzle passed all 16 jobs and broke a held-back one. | "Guesser fixes first": the guesser rewrites first, the checker tidies. |
| 18 | The run script split the way named "full loop, guesser first" at its comma, so that run did the wrong thing. | Renamed "guesser fixes first"; the void run was deleted and run again. |
| 18 | The browser test could not start: this computer's browser is a different version from the one Playwright expects. | The test takes the browser's location from the BROWSER_PATH setting. |

## Traps

- **Filing a finding as a lesson.** A result about how well a guesser did belongs in the log. This file is for things that broke and were fixed.
- **Fixing without a test.** Each fix above has a test in "11 checker tests.js", "16 Sonnet guesser tests.js", "17 error correction tests.js" or "16 page test in a browser.py", except the small AI's, which need the small AI to test, and the run-script and browser-path fixes, which were checked by running them.
