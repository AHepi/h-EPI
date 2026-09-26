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
| 19 | Replies from DeepSeek at the highest thinking setting thought until the 32,000-token limit and answered nothing (7 of them). | Those arms were run again with a 200,000-token limit; no reply was cut off. Cut-offs are counted in every table. |
| 19 | A test of mine called an answer leaked from a held-back job when it was the answer to a shown job. | The test checks that no held-back job's name appears. |
| 19 | Corrector names with commas would have been split, the log-18 comma bug again. | The planted-mistakes script splits its list at semicolons. |
| 19 | The loop's questions were not saved in the arms' records, and they were needed for the fair counts. | Recovered by replaying each loop from DeepSeek's recorded replies; every replay reproduced its final model. |
| 20 | A test of mine assumed the question-picking summary had one table; it has three. | The test checks the first table and that the others are there. |
| 20 | A sentence in the write-up miscounted the worlds where random questions were ahead. | Corrected against the tables, which now come from the script. |
| 21 | A one-sentence request landed in the same paragraph as the buried question, making it easy to find. | Request sentences skip the question's paragraph; a test checks. |
| 21 | Filler paragraphs used words that are names in the worlds (a stone wall, lamps, letters, a goose, "place", "seen", "forecast"). | Replaced before any run; a test checks the filler names nothing from any world. |
| 21 | The buried question's wording ("start the usual way") clashed with a job name in the river world, and DeepSeek read it as that job. | Not fixed in this run; recorded in the findings as a fault of the test. |
| 22 | The stand-in in my tests looked for words the real instruction does not use, so its first turn counted as a try to stop. | The stand-in looks for the instruction's real words. |
| 22 | "Questions that changed a starting state" counted every question, because DeepSeek writes out default starts. | It now counts only states that differ from the usual start. |
| 24 | My summary to the owner said "your question" for the made-up letter-writer's question, and "owner" meant two different people in the documents. | Word list: "owner" is the real owner, "pretend owner" the made-up one; the reports for logs 21 to 23 say which is meant. |
| 25 | A test check reported a test answer as leaked when the test's actions merely matched the end of a longer observation. | The check matches whole observation lines. |
| 25 | My plan and tests assumed 120 sequences of up to four actions for every device; the gate has two actions, so 30. | Corrected before any run, and the correction noted in the plan. |
| 25 | The first hard-to-vary arm demanded that every part do work; the true magnet-ball explanation has a part the observations never test, so it could never finish, and could push DeepSeek to delete a right rule. Found by a test before any run. | The arm aims for the fewest such parts and stops when a round no longer reduces them. |
| 26 | My first test's stand-in committed to a situation that is one of the grudge's test cases, so the world rightly refused it and the test failed. | The test picks an unseen situation that is not a test case, by rule. |
| 28 | The route came out empty: it followed changes within one run, but an effect is a difference between two runs. | Traced through what holds the thing at the end; a change of meaning, reported in log 29. |
| 28 | That new tracing ran past a held thing and round a loop. | It stops at held things; a test with a loop. |
| 28 | Two opposite pushes gave "changed", because the nearer one arrived first. | Any clash on or upstream of the thing asked about reads "unsettled"; my judgement, made after the test failed, reported in log 29. |
| 28 | An event list was read letter by letter. | Lists go through the checker's own reader. |
| 30 | My test expected 4 different situations from a script that asks 3; I counted two identical questions as different. | The test's numbers corrected; the code was right. |
| 30 | Calling DeepSeek with the key typed into the command was refused by the session's safety check. | The key is to be stored in the environment's settings, never in a command or file. |
| 31 | The owner's key file began with an invisible marker some editors add, and it was sent as part of the key, so DeepSeek refused it. | The marker is removed when the key is read from the file. |
| 34 | My plan said every long test case goes deeper than 10; two do not. Found by a test before any run. | The plan corrected with a note; the cases unchanged. |
| 34 | My code-block reader kept a trailing line break. | Trimmed. |
| 34 | The peg tube's observations and test cases could not tell a pile from separate counts of each colour, so two wrong rule models scored full marks. Found after the run. | Probes that separate them, run after the results and marked as such; the next device is to be checked for its near rivals before any run. |
| 35 | Nine of the peg tube's first ten long tests could be got right by separate counts of each colour, by coincidence. Found by a check before any run. | Three tests separate counts must get wrong were added; the plan noted it. |
| 35 | My test of a model that never settles used a rule that stops firing once the gate shuts, so the model settled. | The test uses a rule with no conditions. |
| 35 | My test expected 4 peg tests that separate counts gets wrong; there are 5. | The count corrected. |
| 39 | My check of whether DeepSeek's sentence says its method asks the world looked only for words like "ask" and "the world", and missed "checks up to three nearby situations". Found after the run. | Kept as planned and reported beside a hand reading; a check of words is not a check of meaning. |
| 40 | I protected "every shown job the current method repairs" without checking whether it could conflict with the aim to repair; on some starts the only repairs available break something, so no method could meet both. Found after the run. | The plan kept as written; the next plan checks its aims for conflict on the occasions before the run. |
| 31 | Round 1's comparison used one pair of plain runs as the measure of chance; that pair happened to overlap more than any other. | Round 2 repeated two texts word for word, which showed it. |

## Traps

- **Filing a finding as a lesson.** A result about how well a guesser did belongs in the log. This file is for things that broke and were fixed.
- **Fixing without a test.** Each fix above has a test in "11 checker tests.js", "16 Sonnet guesser tests.js", "17 error correction tests.js", "19 baseline tests.js", "20 who picks tests.js", "21 long text tests.js", "22 twenty questions tests.js", "23 owner will not say tests.js", "25 construction test tests.js", "26 attack surface tests.js", "28 causal checker tests.js", "30 system prompt tests.js", "34 language tests.js", "35 growing language tests.js", "39 changing a method tests.js", "40 kept method at work tests.js" or "16 page test in a browser.py", except the small AI's, which need the small AI to test, and the run-script and browser-path fixes, which were checked by running them.
