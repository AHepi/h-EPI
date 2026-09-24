# Guess Check Fix - project story

## The goal

Let AIs plan, reason and carry things out, beyond code: write stories that work, understand vague requests, plan a video game, solve problems, explore ideas creatively, reason about cause and effect. The tool should guess, explore, and above all correct its own errors. It combines the owner's two earlier tools, the hard-to-vary skill and the Strata kit, following "Claude Fable Semantics – standalone theory", revision 1.

The idea in one line: an AI guesses, an ordinary program checks, and the fixing is split so each side does only what it can do.

## Where things stand

- **DeepSeek is now the guesser, and every result in log 17 and 18 comes from real DeepSeek runs** (DeepSeek V4.1 Flash, reached directly from this computer). Sonnet was never run; the Sonnet page still works with stand-ins.
- **Ten test worlds**: the first five, and five new ones for planning, problem solving, vague prose, a second story, and adding a new idea to a game without breaking it (log 18).
- **An error-correction test with planted mistakes**: 32 known mistakes, each handed to seven correctors (log 18).
- **The main finding**: DeepSeek's first guesses usually pass every shown job; its mistakes are in what it was not shown. Checking the shown jobs can never find those. Asking the world about nearby situations finds some; DeepSeek rereading its own model finds others. Whole rewrites fix the broken part but re-guess the rest. The full write-up is "18 What DeepSeek showed about error correction.md".
- **Best way of running so far: "guesser fixes first"**: 15 of 20 ten-world runs ended with every job passing, and it repaired all 10 visible and 11, then 13, of 20 hidden planted mistakes.
- **Tested against a baseline and against spending more tokens** (log 19). In that run the loop beat DeepSeek on its own (338 of 376 nearby situations right, against 300), and neither thinking harder nor asking five times closed the gap. Given the answers the loop collected from the world, DeepSeek on its own did better than the loop (356). Written up in "19 Baseline and more thinking.md".
- **The attack surface** (log 26): planned and built, not run; waiting for the owner to top up the DeepSeek account. DeepSeek commits in advance to what would cast doubt on its conjecture; the world answers the riskiest commitments; a fresh DeepSeek rebuilds from the facts alone, compared with feeding the attack back to it. The plan reads where an LLM sits in the semantics: a selected transport, the source of conjectures, not their critic. See "26 Plan - attack surface.md".
- **The construction test** (log 25), planned against the semantics and committed before running: four made-up devices whose right explanation needs a hidden thing, the same 14 observations for every arm, no way to ask for more. With the evidence fixed, the error-correction loop did not beat bare DeepSeek overall (84 of 96 hard cases against 85). On one device, the grudge, every bare run failed the same way, even asked five times or made to check itself, and writing an explicit explanation did better; but that came from the form, since the first explanation fitted all 14 observations in all 32 attempts and so was never refuted. Hard-to-vary criticism was the one correction that worked without new evidence, a little. Written up in "25 Construction test.md".
- **The owner will not say** (log 23): when the owner refuses to answer their own buried question, DeepSeek works it out from what it may ask. In the borrowed lantern, the world it had misread since log 18, it was wrong twice answering straight away and right twice after asking around the question. Overall 19 of 20 against 18 of 20; the one it lost was a limit of the test (the owner only says how things end). Written up in "23 The owner will not say.md".
- **Twenty questions** (log 22): made to ask 20 questions one at a time before answering, DeepSeek asks well: afterwards it was right on 345 of 350 nearby situations (20 random questions: 338; answering straight away: 287). But its first move, in 15 of 20 runs, is to ask the owner their own buried question back, and it costs six and a half times the tokens of random questions. Written up in "22 Twenty questions.md".
- **Long texts** (log 21): DeepSeek finds a question buried in about 2,300 words and answers it as well as in a short message, and answers from the world still help as much. But given the option to stop, it almost never asks (32 of 40 runs asked nothing), so it gets none of that help. Written up in "21 Long texts.md".
- **Who picks the questions does not matter much** (log 20, three repeats). Answers to questions picked at random helped DeepSeek as much as answers to the loop's questions, slightly more (524 against 516); DeepSeek's own choice of questions helped least (488). The loop's rule model was about level with DeepSeek alone (462 against 452). What reliably helps is more answers from the world. This overturns log 19's conclusion that the loop's value lay in finding the right questions. Written up in "20 Who picks the questions.md".
- **All tests pass**: 20 checker tests, 13 Sonnet-guesser tests, 26 error-correction tests, 11 baseline tests, 13 question-picking tests, 16 long-text tests, 11 twenty-questions tests, 9 refusal tests, 39 construction-test tests, 14 attack-surface tests, 12 browser tests.
- **The project now lives in the owner's h-EPI repository**, in the folder `guess-check-fix`, so it cannot be lost the way log 15 describes.

## How the pieces fit

**Three roles.** The **guesser** is the AI that writes the rules; in every run since log 17 that is DeepSeek. The **checker** is an ordinary program with no AI in it: it runs the rules and reports what passes and fails. The **world** is a hidden correct version of each task, standing in for the owner: it answers questions. "DeepSeek alone" (log 19 and 20) is DeepSeek not playing the guesser: it writes no rules and answers questions directly.

**An example first.** Take the lighthouse story. The loop gives DeepSeek the request and the shown jobs. DeepSeek writes a model in which Mara realises Tev can't cope "when she lights the lamp during the storm". Every shown job passes. In the full loop, the checker then looks for surprises: it notices no rule reads the lamp, so it asks the world, "if the lamp was already lit when the storm came, what happens?" The world says Mara leaves; the model says she stays. A job fails. In "guesser fixes first", DeepSeek is shown the checker's report, now including the world's answer, and rewrites the model; the checker keeps the rewrite only if it repairs the failing job and breaks none that passed. Any fix the checker makes itself is first cross-checked with one more question to the world. At the end, the held-back jobs DeepSeek never saw are run.

**The parts, what each does, and what it hands on:**

| Part | What it does | What it hands on |
|---|---|---|
| `03 test worlds.js` | Five worlds: ball and wall, hidden ball, door game, lighthouse story, to-do app. Each has a request, jobs (some held back), and a hidden true model. | The request and shown jobs go to the guesser through the loop. The hidden true model answers the world's questions and grades held-back jobs. |
| `18 more test worlds.js` | Five more worlds, same layout: moving day (planning), river crossing (problem solving), plant watering (vague prose), borrowed lantern (a story), ghost lantern (a new idea added to the door game). | The same as above. |
| `03 checker.js` | Runs a model through each job, explains failures, finds small fixes, checks fixes (no backsliding), finds deciding tests, searches for one new rule. Never guesses. Since log 17 a small fix can swap a condition for one about a different thing. | Pass or fail with reasons, small fixes, fix verdicts, deciding tests, to the loop. |
| `09 loop.js` | Drives the cycle: guess, check, fix, ask the world, then the held-back jobs. Seven ways of running. Since log 17 the full loop cross-checks each checker fix with the world and looks for surprises. | Requests to the guesser; models to the checker; a record of each run. |
| `17 DeepSeek guesser.js` | Sends the loop's messages to DeepSeek V4.1 Flash and returns its reply. Reads the account key from the DEEPSEEK_API_KEY setting at each call and never writes it anywhere. Counts thinking, cut-off replies and failures. | DeepSeek's reply text, back to the loop. |
| `17 run with DeepSeek.js` | Runs worlds with DeepSeek: one shared first guess per world and repeat, then each way of running. Can reuse the first guesses of an earlier run. | A record per world and repeat, and `results.md`, in a folder under `runs/`. |
| `18 planted mistakes.js` | Plants known mistakes in the true models, hands each to the correctors, and grades the result on shown jobs, held-back jobs and 400 nearby situations. | A record per planted mistake, under `runs/`. |
| `18 summarise planted mistakes.js` | Counts, per corrector, how many planted mistakes ended repaired, better, unchanged or worse, with their tokens, and lists every one. | `results.md` in the run's folder. |
| `19 baseline and more thinking.js` | Builds one fixed set of questions per world and puts them to every arm: DeepSeek alone at each thinking setting, five times with a majority vote, and given the world's answers; and the first guess and guesser fixes first at each thinking setting. Counts every token. | A record per world and repeat, under `runs/`. |
| `20 who picks the questions.js` | Runs the loop, then hands DeepSeek alone the answers to the same number of questions picked three ways (by the loop, at random, by DeepSeek) and grades each on log 19's questions. `--summarise` rewrites the tables from the records. | A record per world and repeat, and `results.md`, under `runs/`. |
| `21 filler paragraphs.js` | Thirty paragraphs of everyday news that name nothing from any world; the padding a request is buried in. | Text, to file 21. |
| `21 long texts.js` | Buries each world's request and one held-back question in a long message, then compares answering straight away, random questions first, "ask or stop" and the rule-writing loop, in short and long form. `--show WORLD` prints the messages; `--summarise` rewrites the tables. | A record per world and repeat, and `results.md`, under `runs/`. |
| `22 twenty questions.js` | On log 21's long messages: DeepSeek must ask the owner 20 questions one at a time, saying what it expects each time, before it may answer; compared with 20 random questions and answering straight away. Records what it asks. `--summarise` rewrites the tables. | A record per world and repeat, and `results.md`, under `runs/`. |
| `23 owner will not say.js` | Log 22's twenty questions, but the owner refuses to answer their own buried question; compared with answering straight away. Counts refusals and near copies. `--summarise` rewrites the tables. | A record per world and repeat, and `results.md`, under `runs/`. |
| `25 construction worlds.js` | Four made-up devices (a grudge, a magnet ball, a counting gate, a charged vial), each needing a hidden thing; builds their 14 observations and 12 test cases. | Devices, observations and test cases, to the construction test. |
| `25 construction test.js` | Gives every arm the same observations and grades each on the same unseen test cases: bare, bare majority of 5, bare checking itself, conjecture and criticism, blind retries, and conjecture, criticism and hard to vary. `--summarise` rewrites the tables. | A record per device and repeat, and `results.md`, under `runs/`. |
| `26 attack surface.js` | DeepSeek commits to predictions that would cast doubt on its rule; the world answers the riskiest; a fresh DeepSeek rebuilds from facts, or the same conversation is told the result ("defend"); compared with bare and random answers. Not run yet. | A record per device and repeat, and `results.md`, under `runs/`. |
| `19 summarise baseline.js` | The log-19 tables, including the counts that leave out situations the loop asked the world about (found by replaying the loop from its recorded replies). | `summary.md` in the run's folder. |
| `16 Sonnet guesser.js`, `16 Sonnet page template.html`, `16 build the Sonnet page.js`, `16 Sonnet page.html` | The Sonnet page from log 16, rebuilt from the changed code. | A results table on screen, for when Sonnet is run. |
| `11 checker tests.js`, `16 Sonnet guesser tests.js`, `17 error correction tests.js`, `19 baseline tests.js`, `20 who picks tests.js`, `21 long text tests.js`, `22 twenty questions tests.js`, `23 owner will not say tests.js`, `25 construction test tests.js`, `26 attack surface tests.js`, `16 page test in a browser.py` | The tests. `17 error correction tests.js` replays DeepSeek's real guesses from the records, and tests the DeepSeek guesser with a stand-in. | ok or FAIL for each. |
| `15 Guide for the guesser.md` and `15 make the guide for the guesser.js` | The exact text the guesser is given. | Something to hand to any other model. |
| `15 How to work on this project.md` | How to read, change, run and document the project. | |
| `18 What DeepSeek showed about error correction.md` | The findings of log 17 and 18 in plain words. | |
| `19 Baseline and more thinking.md` | The findings of log 19 in plain words. | |
| `20 Who picks the questions.md` | The findings of log 20 in plain words. | |
| `21 Long texts.md` | The findings of log 21 in plain words. | |
| `22 Twenty questions.md` | The findings of log 22 in plain words. | |
| `23 The owner will not say.md` | The findings of log 23 in plain words. | |
| `25 Plan - construction test.md` | The plan and conjectures of log 25, committed before its runs. | |
| `25 Construction test.md` | The findings of log 25 in plain words. | |
| `26 Plan - attack surface.md` | Where an LLM sits in the semantics, and the plan and conjectures of log 26, committed before its runs. | |
| `runs/` | Every DeepSeek run: every request, every reply, every step, every final model. | The evidence for every number in the log. |

## Word list

| Word | Plain meaning |
|---|---|
| model | What the guesser writes: things, events, a start, and rules. The checker can run it. |
| thing | Something that can be in one of a few states, like the ball (in hand, flying, stuck on wall). |
| state | One of the ways a thing can be. |
| event | Something that happens from outside, like a throw. |
| rule | "When these conditions are true, this thing becomes this state." |
| start | The state of each thing before anything happens. |
| job | A test from the owner: in this situation, this should come out. |
| shown job | A job the guesser sees. |
| held-back job | A job kept from the guesser until the end, to catch guesses that only fit what they were shown. |
| world | The hidden true model in each test world. It stands in for reality, or for the owner. |
| guesser | Whichever AI writes the models: the small AI, Sonnet, or DeepSeek. |
| small AI | Qwen 2.5, 1.5 billion size, run on the earlier computer. |
| Sonnet | Claude Sonnet 4.6, reached from the page inside the chat. Never run for real. |
| DeepSeek | DeepSeek V4.1 Flash, reached directly from this computer. Its own name for itself is "deepseek-flash". It thinks before it answers. |
| account key | The password-like code that lets this computer use DeepSeek. Read from a setting at each call, never written into any file. |
| checker | The ordinary program that runs models and reports. It never guesses. |
| loop | The program that passes work between the guesser and the checker. |
| small fix | A one-step change to an existing rule, found and applied by the checker. |
| new part | A new rule or a new thing, asked of the guesser when no small fix works. |
| clearing out | After a new part, the checker tries the model without the old rules that now disagree with it. |
| new rule search | The checker's last resort: try every single new rule itself. Its rules are marked as fitted. |
| fix check | A fix is kept only if it repairs a failing job and breaks none that passed (no backsliding). |
| deciding test | A situation where two candidate models give different answers, so the world can choose. |
| question to the world | A deciding test, a cross-check or a surprise probe put to the world. Its answer becomes a new job. |
| cross-check | Before the full loop keeps a checker fix, one question to the world about a situation where the model before and after the fix disagree. |
| look for surprises | When no rival rule is in sight, questions to the world about situations one change from the jobs where the model takes a route no job has tested. |
| route | The set of rules that change something in a situation. |
| poke | One surprise question per round that changes the start of a thing no rule reads, to test the model's claim that it cannot matter. |
| surprise | A question to the world whose answer the model got wrong. |
| owner | You, the person this project is for. |
| pretend owner | The made-up person who writes a test world's request (in logs 21 to 23, a long letter with a question buried in it) and whose answers the world supplies. Logs 21 to 23 and their write-ups call this person "the owner"; there it never means you. |
| owner's word list | The things and states the shown jobs use. Given by the owner, so adding them is not guessing. |
| ways of running | One guess, rewrite, guess and fix, full loop, guesser fixes first, self review, review first. |
| one guess | The first guess, nothing more. |
| rewrite | The guesser rewrites its whole model from the checker's report. |
| guess and fix | Small fixes by the checker, new parts from the guesser, clearing out, last-resort search. No questions to the world. |
| full loop | Guess and fix, plus questions to the world. |
| guesser fixes first | The full loop, but when jobs fail the guesser first rewrites the model from the checker's report; the checker's small fixes tidy what is left. |
| self review | The guesser rereads the model against the request, with no report from the checker, and corrects what it finds. |
| review first | Self review, then guesser fixes first. |
| planted mistake | A known mistake put into a world's true model on purpose, to test error correction. |
| visible mistake | A planted mistake that makes a shown job fail. |
| hidden mistake | A planted mistake that passes every shown job and fails a held-back job. |
| corrector | Any way of running, used to repair a planted mistake. "Checker alone" is guess and fix with no new parts from the guesser. |
| nearby situations | Up to 400 situations one or two changes from the jobs, run on a model and on the world to see where they end differently. |
| repaired | Every shown and held-back job passes and no nearby situation differs from the world. |
| repeat | A fresh first guess for the same world, to see how much the guesser's guesses differ. |
| baseline | What the project is compared against: DeepSeek alone. |
| DeepSeek alone | DeepSeek given the request, the owner's word list and the shown jobs with their answers, answering questions directly. No model, no checker, no loop. |
| thinking setting | How long DeepSeek thinks before answering: lowest, default or highest (DeepSeek's words: low, high, max). |
| tokens | The pieces of text a model reads and writes; DeepSeek charges by them. "Output tokens" here include its thinking. |
| cut off | A reply that reached the reply limit before it finished. A cut-off reply answers nothing. |
| majority of 5 | Asking DeepSeek alone the same questions five times and taking, for each answer, the one given most often. |
| arm | One of the ways compared in log 19 and 20, each answering the same questions. |
| ask then answer | The loop asks the world its questions; then DeepSeek alone is given the answers and answers directly. |
| random questions | Situations one or two changes from the jobs, picked by a fixed shuffle, put to the world instead of the loop's questions. |
| DeepSeek picks questions | DeepSeek is told it may ask the owner a number of questions and writes them itself. |
| fair count | A count that leaves out every test question whose situation some arm asked the world about. |
| long message | A world's request spread through about 2,300 words of everyday news, with the embedded question in the middle. |
| embedded question | One held-back job turned into a question in plain words ("What I actually need to know is this: ...") and put inside the owner's message. |
| ask or stop | Each turn DeepSeek either asks the owner how a situation ends, or stops and answers. At most 12 questions. |
| found | DeepSeek named the same situation as the embedded question, start and events in order. |
| must ask 20 | DeepSeek has to ask the owner 20 questions, one at a time, seeing each answer, before it may answer. |
| expectation | What DeepSeek says, with each question, it expects the answer to be. |
| surprised | The owner's answer differed from DeepSeek's expectation on something both named. |
| asked back | DeepSeek asked the owner the owner's own buried question. |
| refused | In log 23, the owner's reply to their own question: "I can't tell you that one; that's what I'm asking you." It still uses up one of the 20. |
| near copy | A question that starts like the owner's and carries on past it (the owner's question plus more events). Not refused; counted. |
| selection | In the semantics: correcting by re-tuning within what one already has, such as trying again. It cannot reach an answer that needs something new. |
| construction | In the semantics: correcting by building a new explanation, often with a part one did not have, such as a hidden thing. |
| device | One of the four made-up machines of log 25, each with a rule that needs a hidden thing. |
| observation | In log 25: one sequence of actions on a device and what was seen at the end. Every arm gets the same 14. |
| test case | In log 25: an unseen sequence of actions every arm is graded on. "Hard" test cases are the ones the obvious explanation gets wrong. |
| bare | DeepSeek answering the test cases directly from the observations. "Majority of 5" asks five times; "checks itself" rereads its rule against every observation three times. |
| conjecture and criticism | DeepSeek writes an explanation the checker can run; the checker reports exactly which observations fail; DeepSeek writes a new one; up to 6. |
| blind retries | The same, told only how many observations fail. |
| hard to vary (arm) | Conjecture and criticism that goes on, once an explanation fits, to criticise parts no observation holds in place (idle or untested). |
| reach | Of all sequences of up to four actions, how many an explanation gets right. |
| attack surface | What a conjecture commits to that could come out otherwise: its predictions for unseen cases, stated in advance. |
| commitment | One prediction DeepSeek makes in advance: "if my rule is right, this situation ends this way", with why it would cast doubt if not. |
| risky | A commitment the obvious explanation disagrees with. |
| rebuild fresh | After the world answers its commitments, a new DeepSeek conversation gets only the facts, never the old rule or any verdict. |
| defend | The same conversation is told "you predicted X; the world says Y" and carries on. |
| stand-in | A fake guesser used in tests, so everything but the real connection can be tested. |
| reply cap | Sonnet's replies are cut off at 1000 tokens by the page's connection. DeepSeek's limit is 32,000 tokens, thinking included, raised to 200,000 for two arms in log 19. |

## Log

Entries 01 to 14 happened in the earlier chat, "Small LLMs planning and reasoning with error correction", and are written here from its record. Entries 01, 04, 08 and 13 keep the numbers that chat gave them; the others are numbered in order.

**01. Strata and cause and effect.** Strata refused "The shadow is long because the pole is tall" and "If the pole is tall then the shadow is long". Its instructions tell a translator to drop causes. Decided on a new small language of things and rules (Decisions C1).

**02. A small AI on the earlier computer.** Qwen 2.5, 1.5 billion size, through llama.cpp. Its server kept stopping between steps; fixed by starting it in the same step as the work.

**03. The checker and the five test worlds were written** (files 03).

**04. Time was wrong.** Checking each hidden true world against its own jobs: in two worlds, a state like "game over" arrived one step late. Changed how time works: after each event, everything settles before the next event.

**05. The hard-to-vary sweep on the true worlds.** Found that the scene where Mara lights the lamp changes nothing about the ending, and that for the to-do app the deciding test is the question "If you put a task off once, is it urgent yet?". Several report messages were noisy or unclear and were fixed.

**06. Better searching.** Deciding tests now try changes to the jobs' inputs first. The small-fix search can add one condition to a rule.

**07. Error correction on hand-written flawed models.** Ball and wall: the small-fix search found the missing condition. Hidden ball: no small change could work; adding a hidden thing, "where the ball really is", was accepted and passed held-back jobs it had never seen.

**08. The small AI could not use advice.** Its first guess on ball and wall passed 2 of 4 jobs. With the checker's report, still 2 of 4 after four rounds, even when told the exact fix. A wrong explanation line in the checker was fixed along the way. Decided: the checker applies small fixes, and the small AI is asked only for new parts (C6).

**09. The new loop was written** (file 09). A dry run on the small AI's earlier ball guess: one small fix took it from 2 to 4 of 4 jobs.

**10. A start-up failure.** The small AI's server was still loading when the loop started. The loop now waits until the server is ready, and retries.

**11. One pass with the small AI.** Four ways each; long runs had to go into the background because steps over five minutes are cut off. 17 checker tests written (file 11), all passing. Results, shown jobs then held-back jobs:

| World | Guess alone | Rewrite from report | Checker's small fixes |
|---|---|---|---|
| Ball and wall | 2/4, 2/3 | 2/4, 2/3 | 4/4, 3/3 |
| Door game | 2/4, 2/3 | 2/4, 2/3 | 3/4, 2/3 |
| Hidden ball | 0/5, 0/3 | 0/5, 0/3 | 0/5, 0/3 |
| Lighthouse story | 1/3, 0/2 | not finished | not finished |
| To-do app | not reached | | |

In the full loop, questions to the world changed nothing: ball and wall was already at 4/4 and 3/3, and in the door game the checker's fitted fix ("the ghost only hurts you when the key is on the floor") survived.

**12. The small AI never once supplied a working new part.** In the hidden-ball world it left out the screen and what is seen. It wrote rules that could never fire, like "when the ball is at 1 and at 2". It gave the identical reply each time it was asked again.

**13. Improvements, in a separate copy.** Rules that can never fire are reported, with a small fix for them; the owner's word list is added before fixing; a repeated request shows what already failed; the checker searches for one new rule as a last resort. That search found a shortcut in the hidden-ball world ("when the ball is at 1, what is seen is at 4") that the held-back jobs could not catch, so one held-back job was added, labelled as added later. 20 checker tests passed. Not run with the small AI. Nothing was delivered as a download.

**14. Bigger models.** Asked whether this would work on a 300B model, and whether Claude could call Haiku. Answer: probably much better, but untested. This computer has no account key and too little memory for a 300B model. The one Claude model reachable is Sonnet 4.6, through a page inside the chat.

**15. Rebuilt from the record.** New chat. The earlier computer had been reset, and nothing had been downloaded. Rebuilt from the earlier chat's record: the checker's original text, then its 32 recorded changes in order, each checked to find its exact old text before replacing it; the worlds; the tests; the loop. All 20 checker tests pass, the same as in entry 13. The loop can now take a different guesser, and its names say "guesser" rather than "small AI". Not rebuilt: the small AI's setup, the batch scripts, the results summariser, the raw run files. Also written: how to read, change and document the project, with the authority documents and a glossary; and the exact words the guesser is given, as a file of their own (files 15).

**16. The Sonnet page.** Built the page and its pieces (files 16). Tested with stand-ins for Sonnet, not with Sonnet: 13 tests with the loop, 12 in a browser at phone size, all passing. Two failures found and fixed:
- **The loop refused the right new part.** Given exactly the right missing piece for the hidden ball, the loop turned it down: the new rules disagreed with the old wrong rules, and the loop could only add. Now, after a new part, the checker also tries the model without the old rules that disagree with it. With that, the hidden ball goes to 5 of 5 shown jobs and 3 of 3 held back (Decisions C19).
- **The results hid two of the four ways on a phone.** Reshaped into one small table per world.

**17. DeepSeek, and three holes in error correction.** New chat. The owner uploaded the project, the theory, the hard-to-vary skill and the Strata kit, and asked to finish the project on DeepSeek V4.1 Flash, with error correction foremost (Decisions O5). The project was put into the owner's h-EPI repository, folder `guess-check-fix`. The DeepSeek guesser and a run script were written (files 17). First real run, five worlds, two repeats, four ways (`runs/17 first DeepSeek run`):
- DeepSeek's first guesses passed every shown job in 8 of 10 runs. In the hidden ball it invented "where the ball really is" on its own, which the small AI never did (log 12), with its timing one step off; given the checker's report it rewrote the model correctly in one round. DeepSeek can use criticism; the small AI could not (log 08).
- **The full loop made the lighthouse story worse** (2 of 2 held-back jobs, down to 1). DeepSeek's model tied Mara's realisation to her lighting the lamp. A question to the world exposed that; the checker repaired it by deleting the lamp condition, which fit every job and was still wrong. Cause: the checker could only swap a condition for another about the same thing, so "the lamp is dark" was out of its reach, and it had no reason to ask the world to choose.
- **The to-do app kept "one put-off makes it urgent"** in every way of running. The loop's questions were all about finishing tasks; it never asked what one put-off does, because it only asks where it can see a rival rule.
Fixed, each with tests: the checker can swap a condition for one about a different thing (C22); a checker fix is cross-checked with the world before it is kept (C23); the full loop looks for surprises, including a poke at a thing no rule reads (C24); held-back jobs the world was asked about are listed in every result (C25). Replaying DeepSeek's real guesses offline, the lighthouse story now passes both held-back jobs without the world being asked about either. A failed attempt along the way: the surprise questions first went unused because the loose-rule questions used up their rounds; they got rounds of their own. 19 new tests (file 17), all passing.

**18. Ten worlds, planted mistakes, and who should do the correcting.** Five new worlds (file 18): moving day, river crossing, plant watering, borrowed lantern, ghost lantern. Each world's true model passes all its own jobs; one of my river-crossing jobs was wrong at first (it expected the grain to survive when the farmer rows off alone, but the puzzle eats both at once) and was corrected before any run. Runs, all with DeepSeek, all records in `runs/`:
- **Ten worlds, two repeats, four ways** (`runs/18 ten worlds after the fixes`). 18 of 20 first guesses passed every shown job; 11 of 64 held-back jobs failed after the first guess. Every run with everything passing: one guess 9 of 20, rewrite 11, guess and fix 11, full loop 13.
- **The full loop broke a right answer in the river puzzle**, in both repeats: DeepSeek's reading of the puzzle differs from the world's in two places the request leaves open; the questions exposed that, and the checker patched it with seven one-step fixes that passed all 16 jobs and broke "the other solution". So a fifth way was added: **guesser fixes first** (C26). Run on the same first guesses (`runs/18 ten worlds, guesser fixes first`): 15 of 20 runs with everything passing; the river puzzle 3 of 3 in both repeats. A failed first attempt: the way was first named "full loop, guesser first", and the run script split that name at its comma, so the first run of it was void and deleted; renamed. The planted-mistakes records below were made before the rename and still carry the old name.
- **Planted mistakes** (`runs/18 planted mistakes`, file 18, C27): 32 mistakes (10 visible, 20 hidden, 2 needing a new thing), picked by a fixed shuffle, each given to the correctors. Repaired: rewrite 10 visible, 0 hidden; checker alone 6 visible, 0 hidden, and once it made a model more wrong while making every shown job pass; **self review** (a new way, C28) 6 visible, 9 hidden, 3 made worse; full loop and guesser fixes first 10 visible, 11 hidden. Self review and the full loop repaired different hidden mistakes: 16 of 20 by one or the other, 4 by both.
- **Review first** (self review, then guesser fixes first; C29) to combine them (`runs/18 planted mistakes, review first`, `runs/18 ten worlds, review first`): 12 of 20 hidden repaired, but only 6 of 10 visible; ten worlds 15 of 20, the same as guesser fixes first. In each visible case it missed, the review fixed the planted mistake and re-guessed other rules in DeepSeek's own reading of the request. A whole rewrite is a new guess at every part.
- **Tried and dropped:** a second poke that adds an event the model says does nothing, aimed at the borrowed lantern (DeepSeek reads "the stranger goes out searching" as one moment, the world as ongoing). Replayed on all 20 first guesses it changed nothing overall (54 held-back jobs passed without it, 53 with it) and did not reach the lantern case. Removed.
- **Still wrong:** the borrowed lantern's search (above); the ghost lantern lights without the key, and no question can catch it because no shown job asks about the lantern; the to-do app without a put-off count got worse in the full loop (44 nearby situations wrong, then 52).
- The Sonnet page was rebuilt from the changed code; the browser test now takes the browser's location from a setting, because this computer's browser is a different version from the one Playwright expects. All four test files pass: 20, 13, 26 and 12 tests.
- Cost of everything in this entry: $1.41 of DeepSeek credit (balance $21.52 before the second run, $20.11 after the last). 272 DeepSeek replies over both entries, 2 cut off at the reply limit.
The findings are written up in "18 What DeepSeek showed about error correction.md".

**19. Against a baseline, and against spending more tokens.** The owner asked for both (Decisions O6). A fixed set of questions per world (62 held-back and 376 nearby over two repeats) was put to every arm, and every DeepSeek call's tokens were counted (files 19; `runs/19 ...`):
- **The baseline, DeepSeek alone, loses to the loop on nearby situations** (300 against 338 for guesser fixes first), and is level on held-back situations the loop never asked the world about (30 of 37 against 29). The loop's held-back lead came from situations it asked about.
- **More tokens do not close the gap.** DeepSeek alone at the highest thinking setting got 312 (385,000 tokens); five times with a majority vote, 310 (1.34 million tokens, four times the loop's 332,000); the lowest setting did best of them, 318. Guesser fixes first at the highest setting got 337, no better than at the default.
- **Information closes it.** DeepSeek alone, given the answers the world gave the loop, got 356 and 60 of 62, better than the loop. The loop's value is in finding the questions.
- **Planted mistakes:** self review at the highest setting repaired 13, then 11, hidden mistakes, against 9 at the default: the same range as guesser fixes first (13 here, 11 in log 18). So for rereading hidden mistakes more thinking does help, at four to six times the loop's tokens, with 3 or 4 made worse where the loop made none worse, and at most half the visible mistakes repaired where the loop repaired all 10. Three rounds of review did worse than one (7 hidden, 3.6 times the tokens).
- **Failures along the way:** four replies from DeepSeek alone (three at the highest setting) thought until the 32,000-token limit and gave no answer, as did four self reviews at the highest setting; both were run again with a 200,000-token limit, with no cut-offs. A test of mine was wrong (it treated an answer that belongs to a shown job as a leaked held-back answer) and was corrected. Corrector names with commas would have hit the log-18 comma bug again; the planted-mistakes script now splits its list at semicolons.
- The "never asked" counts need the loop's questions, which the arms did not save; they were recovered by replaying each loop from DeepSeek's recorded replies. All 60 replays reproduced their recorded final models.
- 11 new tests (file 19), all passing. Cost: $4.46 of DeepSeek credit ($20.11 to $15.65).
Written up in "19 Baseline and more thinking.md".

**20. Who picks the questions.** The owner asked what the guesser is (it is the AI that writes the rules: DeepSeek; a plain explanation of the three roles is now at the top of "How the pieces fit") and to go ahead with the next step. That step was refined before running: log 19 had shown that the loop's answers help DeepSeek alone, but not that the loop's choice of questions is what helps. So, per world and repeat (ten worlds, three repeats; `runs/20 who picks the questions`, files 20): the loop ran and asked the world its questions; then DeepSeek alone was given the answers to the same number of questions picked three ways, by the loop ("ask then answer"), at random, and by DeepSeek itself, and all were graded on log 19's questions. Fair count (leaving out test questions any arm asked about):
- Random questions 524 of 543 nearby and 60 of 65 held-back; the loop's questions 516 and 55; DeepSeek's own questions 488 and 57; the loop's own rule model 462 and 49; DeepSeek alone 452 and 54. Random was ahead of the loop's questions in each of the three repeats.
- **This refutes log 19's conclusion** that the loop's value lies in finding the right questions: with about nine questions per task, any questions near the jobs did as well. The loop's rule model was not clearly better than DeepSeek alone this time (it was in log 19).
- DeepSeek's own choice of questions was the weakest, and it barely helped in the river puzzle (35 against 63 for the others): it asked about what its reading already settled.
- A possible bias, stated: random questions are the same kind of situation as the nearby test questions. It does not explain the held-back count, where random also did best.
- Along the way: a sentence of mine in the write-up miscounted the worlds where random was ahead (it is 4 ahead, 5 level, 1 behind) and was corrected; the tables by world and repeat now come from the script. A test of mine assumed one table in the summary and was corrected.
- 13 new tests (file 20), all passing. Cost: $1.59 ($15.58 to $13.99).
Written up in "20 Who picks the questions.md".

**21. Long texts, a buried question, and the option to stop.** The owner asked whether the findings hold for long texts, when the question is embedded and DeepSeek may exit the loop when it likes; nothing so far had tested either, so it was tested (files 21; `runs/21 long texts`; ten worlds, two repeats). Each world's request was spread through about 2,300 words of everyday news (thirty paragraphs written to name nothing from any world), with one held-back job asked in plain words in the middle paragraph. DeepSeek was told only to answer what the owner asks.
- **It found the buried question** in all 40 runs where it had to name it, counting two the strict check rejected: one misspelt state name ("on road" for "on the road"), and one caused by my wording ("start the usual way" read as the river world's "usual solution"). It answered it right as often long as short (17 of 20 both, answering straight away).
- **Answers from the world still help as much:** six random ones took the other questions from 309 to 358 of 376 in the long form.
- **Given the option to stop, DeepSeek almost never asked:** 32 of 40 runs asked nothing; 8 asked one question. So "ask or stop" scored like answering straight away (305 against 309, long form), not like random questions (358).
- The borrowed lantern's reading (the search as one moment) was wrong in almost every arm again; random answers fixed it in one repeat of two.
- Along the way: the first layout put a one-sentence request in the same paragraph as the question, right beside it; request sentences now avoid that paragraph (a test checks). Filler words that overlapped world names (a stone wall, lamps, letters, a goose, "place", "seen", "forecast") were replaced before any run; a test checks none remain.
- 16 new tests (file 21), all passing. Cost: $3.42 ($13.86 to $10.44).
Written up in "21 Long texts.md".

**22. Twenty questions.** The owner turned down the next step of log 21 ("No. That's not smart enough. Get it to ask 20 questions first. See what it does"; Decisions O9). On log 21's long messages (ten worlds, two repeats; files 22; `runs/22 twenty questions`), DeepSeek had to ask the owner 20 questions, one at a time, saying what it expected each time, before it could answer; compared with 20 random questions and with answering straight away. Fair count (test questions either arm asked about left out):
- **It asked well.** Afterwards: 345 of 350 nearby right and 37 of 37 other held-back jobs (random 20: 338 and 37; straight away: 287 and 27). In log 20, DeepSeek writing its questions all at once helped least; asking one at a time and seeing each answer, it did at least as well as random.
- **Its first move is to ask the owner's own question back:** the first question in 15 of 20 runs, by question 8 in the rest, 49 times in all. So its 20 of 20 on the owner's question is not evidence of reasoning.
- **It learned as it went:** surprised by 65 of 399 answers, 37 in questions 1 to 10 and 28 in 11 to 20. It never tried to stop early; every question was usable; 38 repeated an earlier one (30 of them in the hidden ball and river puzzle).
- **It cost six and a half times as much** as 20 random questions (1.75 million output tokens against 267,000).
- Along the way: my stand-in in the tests looked for words the real instruction does not use, so its first turn read as a try to stop; fixed. My count of "questions that changed a starting state" counted defaults written out; it now compares with the usual start (198 of 400, not 400).
- 11 new tests (file 22), all passing. Cost: $2.81 ($10.34 to $7.53).
Written up in "22 Twenty questions.md".

**23. The owner will not say.** The owner asked whether the budget allowed log 22's next step, and if so to do it (Decisions O10); it did ($7.45 before). Log 22's twenty questions on the long messages, but the owner refuses to answer their own buried question ("I can't tell you that one; that's what I'm asking you"), which still uses up one of the 20 (files 23; `runs/23 owner will not say`; ten worlds, two repeats):
- **Owner's question right: 19 of 20 after the 20 questions, 18 of 20 answering straight away.** The difference is the borrowed lantern: wrong in both repeats straight away, right in both after asking. In each, a question of the same shape as the refused one ("the stranger searches, then night falls") surprised it, and it carried that over.
- **The one it lost** (hidden ball, repeat 1) was a limit of the test: the question asks what is seen along the way, and the owner only ever says how a situation ends; twenty endings of "seen at 4" moved it from yes (right) to no.
- It still asked the owner's question 39 times (all 20 runs; up to 6 in one), and asked near copies 21 times in 11 runs (right in all 11; in the 9 runs without one, right in 8).
- Other test questions, fair count: 35 of 38 held-back and 318 of 357 nearby, against 27 and 300 straight away.
- 2.1 million output tokens against 342,000 straight away.
- 9 new tests (file 23), all passing. Cost: $2.93 ($7.45 to $4.52), above my estimate of $2 to $2.50.
Written up in "23 The owner will not say.md".

**24. A word clash.** The owner asked what "your question" meant, having asked nothing: my summary of log 23 said "your question" and "you refuse" for the made-up letter-writer in the tests. That also broke the one-word rule: "owner" meant the real owner in the Decisions file and the made-up letter-writer in logs 21 to 23. Fixed without rewriting the log: the word list now has "owner" (the real one) and "pretend owner" (the made-up one), and the reports for logs 21 to 23 each open with a note saying which is meant. No code changed, and no DeepSeek credit was used.

**25. The construction test.** The owner said the goal is error correction as the semantics means it, not spotting tricks, and asked for a test that meets its standard: can DeepSeek solve a problem a bare run can't, even with repeated loops (Decisions O11). Read against the semantics: creativity is construction (a new explanation, often with a new part), not selection (re-tuning); error correction is conjecture and criticism; an explanation is judged by what it gets right beyond its evidence. So (files 25; plan and five conjectures committed before any run; `runs/25 construction test`): four made-up devices whose right explanation needs a hidden thing, checked offline to be unreachable from what can be seen; every arm the same 14 observations and no way to ask more; graded on 12 unseen test cases, 8 the obvious explanation gets wrong. Arms: bare; bare, majority of 5; bare, checks itself; conjecture and criticism; blind retries; and, added after repeat 1 with its own conjecture committed first, conjecture, criticism and hard to vary. Three repeats.
- **Overall, no:** hard cases right: conjecture and criticism 84 of 96, bare majority of 5 and bare checks itself 85, bare 78 (one bare reply cut off), blind retries 79.
- **The gate and the magnet ball:** bare DeepSeek worked out both from the observations.
- **The grudge:** every bare run failed the same way (a running score of kind acts against insults), 9 or 10 of 12, even asked five times or made to check itself four rounds, keeping the same rule each round. The explanation arms beat every bare run of the same repeat in 7 of 8 runs. But the first explanation fitted all 14 observations in all 32 explanation attempts on every device, so it was never refuted: the gain came from writing states and rules, not from correcting.
- **The vial:** bare did better (11 or 12) than the explanation arms (9), whose explanations fitted everything and were wrong elsewhere.
- **Conjectures:** 1, 2, 3 and 5 refuted; 4 and 6 not refuted (6: hard to vary 58 against 55 on repeats 2 and 3, with no unchecked parts left; small).
- Before any run, tests found a false alarm in a check, a wrong count (the gate has 30 sequences, not 120), and a flaw in the first hard-to-vary arm (it demanded no unchecked parts, which even the true explanations have); all fixed, the plan corrected with a note.
- 39 new tests (file 25), all passing. Cost: $2.55 ($4.48 to $1.93).
Written up in "25 Construction test.md".

**26. The attack surface, planned.** The owner proposed commitments DeepSeek fills in about what would cast doubt on its conjecture, warned that feeding the attack back makes it defend its first answer, and asked where an LLM sits in the semantics, saying the semantics is now what is being tested (Decisions O12). Read against the semantics: an LLM is a selected transport (Part IV), so asking again, voting and rereading are selection responses, which log 25 bore out; feeding its answer back puts the answer into the input (Part V, non-circular dependence), so the criticism has no bearing on what produces the answer (Part IX); the LLM is the source of conjectures, and construction happens in the system around it, which keeps its commitments, has the world answer them, and passes on only facts. Built (file 26), with 14 tests, all passing, and the plan with five conjectures and three results that would count against this reading committed before any run ("26 Plan - attack surface.md"). Not run: the owner asked to wait for a top-up. The earlier next step (the hard-to-vary sweep choosing questions) is set aside for this one, which the owner asked to try first. Along the way my first test picked, for its stand-in, a situation that is one of the grudge's test cases, which the world rightly refused; the test now picks its situation by rule.

## Next step

When the DeepSeek account is topped up, run the attack-surface test as planned, three repeats on the four devices (about $1 to $1.50). on the grudge and the vial, let the hard-to-vary sweep choose a few questions to the world where the explanation's unchecked parts would decide the answer, and compare with bare runs given answers to the same number of random questions (about a dollar of DeepSeek credit; $1.93 is left). the owner writes a long message with their own question in it, DeepSeek asks up to 20 questions one at a time, and the owner answers them in the chat. A few cents of DeepSeek credit; it needs the owner's time rather than money.

## Traps

- **Reading the log 01 to 14 as first-hand.** Those entries are written from the earlier chat's record, not from files. Its raw run files are gone.
- **Reading stand-in results as a real model's.** Every result in entry 16 comes from a stand-in, and so do the offline replays in entry 17 and 18 where a stand-in played the guesser. The live results are only those whose records are in `runs/`.
- **Comparing DeepSeek with the small AI directly.** The loop changed in entries 13, 16, 17 and 18 after the small AI's only runs.
- **Reading "repaired" as "right".** It means matching this world's reading of the request. The river puzzle and the lantern story can be read another way.
- **Reading full-loop held-back scores as unseen tests.** The world is sometimes asked about a held-back situation; every results table says how many.
- **The fifth way's two names.** "full loop, guesser first" in the first planted-mistakes records is "guesser fixes first".
- **Running log 26 before the owner tops up.** The owner asked to wait.
- **Reading log 25's grudge result as error correction.** The first explanation already fitted every observation; the gain came from its form.
- **Reading "the owner" in logs 21 to 23 as the real owner.** It is the pretend owner, the made-up letter-writer (log 24).
- **Reading log 23's hidden-ball miss as a reasoning failure.** The owner in that test only says how things end.
- **Reading log 22's "20 of 20" on the owner's question as reasoning.** DeepSeek asked the owner that very question in every run.
- **Reading log 21's "ask or stop" as a test of asking.** DeepSeek hardly asked, so it mostly measures answering straight away.
- **Reading log 19's "the loop's value is finding the questions" as standing.** Log 20 refutes it for about nine questions per task.
- **Reading log 19's "given the world's answers" arm as a baseline.** It used information only the loop's questions produced.
- **Reading a difference of one or two as real.** The same way of running on the same inputs differed by two between log 18 and log 19.
- **Putting the account key in a file.** It is read from the DEEPSEEK_API_KEY setting only. It was pasted into the chat that made log 17 and 18, so it should be replaced with a new one.
