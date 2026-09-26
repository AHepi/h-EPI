# How to work on this project

Four ways of working on Guess Check Fix: reading it, changing it, running it with DeepSeek, and keeping its documents up to date. Then the authority documents it follows, and a glossary that ties its plain words to theirs.

## Reading the project

Read in this order. Each file says what to read next.

1. **"Guess Check Fix - project story.md"**: the goal, where things stand, how the parts fit, the word list, and the log. Start here every time.
2. **"Status.md"**: what the project is waiting on today, and the open questions.
3. **"Decisions.md"**: why things are the way they are. The owner's decisions are quoted exactly.
4. **"Lessons.md"**: what broke while building and testing, and how it was fixed.
5. **"18 What DeepSeek showed about error correction.md"**, **"19 Baseline and more thinking.md"**, **"20 Who picks the questions.md"**, **"21 Long texts.md"**, **"22 Twenty questions.md"**, **"23 The owner will not say.md"** and **"25 Construction test.md"** (with its plan): the findings of the DeepSeek runs. Each later one qualifies the one before.
6. **The code files**, only when a change is planned. Each starts with a plain note saying what it does. Read them in the order the parts table gives: worlds, checker, loop, DeepSeek guesser, run scripts, Sonnet page.

An example: to find out why the checker applies small fixes itself instead of asking the guesser, the project story's log points to entry 08, and "Decisions.md" has C6, which says log 08 forced it.

## Changing the project

1. **Check "Decisions.md" first.** A change that goes against one of the owner's decisions (O1 to O4) needs the owner's word. A change that goes against one of Claude's routine choices (C1 onward) is allowed, but adds a new decision saying which one it overturns and why.
2. **Make the change in the code files**, never in "16 Sonnet page.html". The page is built from them.
3. **Rebuild the page**: `node "16 build the Sonnet page.js"`.
4. **Run all four test files**, and keep the change only if every test says ok:
   - `node "11 checker tests.js"` (20 tests)
   - `node "16 Sonnet guesser tests.js"` (13 tests)
   - `node "17 error correction tests.js"` (26 tests; replays DeepSeek's real guesses from `runs/`, calls nothing)
   - `node "19 baseline tests.js"` (11 tests)
   - `node "20 who picks tests.js"` (13 tests)
   - `node "21 long text tests.js"` (16 tests)
   - `node "22 twenty questions tests.js"` (11 tests)
   - `node "23 owner will not say tests.js"` (9 tests)
   - `node "25 construction test tests.js"` (39 tests)
   - `node "26 attack surface tests.js"` (14 tests)
   - `python3 "16 page test in a browser.py"` (12 tests; needs Playwright and Chromium. If Playwright wants a different browser version than the one installed, point it at the installed one: `BROWSER_PATH=/opt/pw-browsers/chromium`)
5. **If the change touched the words the guesser is given** (in "09 loop.js" or "16 Sonnet guesser.js"), remake the guide file: `node "15 make the guide for the guesser.js"`.
6. **When a test fails and the failure is fixed**, add a line to "Lessons.md", and a test that would catch it again.
7. **New files** get the number of the log entry that creates them. A changed file keeps its number.

## Running it with DeepSeek

Every live run costs DeepSeek credit and writes records that belong in `runs/`. Set the account key for the one command only; it is never written into any file.

- **Worlds, all ways of running:** `DEEPSEEK_API_KEY=... NODE_USE_ENV_PROXY=1 node "17 run with DeepSeek.js" "runs/NN what it is" 2`
  - `WORLDS_FILE="03 test worlds.js,18 more test worlds.js"` for all ten worlds; a third argument such as `river-crossing,moving-day` for some.
  - `MODES="guesser fixes first"` for some ways only, and `REUSE_FROM="runs/..."` to start from an earlier run's first guesses (so a new way is compared on the same guesses).
- **Planted mistakes:** `DEEPSEEK_API_KEY=... NODE_USE_ENV_PROXY=1 node "18 planted mistakes.js" "runs/NN what it is"`; `ONLY="review first"` for some correctors only (several separated by semicolons); `node "18 planted mistakes.js" --list` shows the mistakes without calling DeepSeek.
- **Summary:** `node "18 summarise planted mistakes.js" "runs/FIRST" "runs/MORE"` writes `results.md` into the first folder.
- **Baseline and more thinking:** `DEEPSEEK_API_KEY=... NODE_USE_ENV_PROXY=1 node "19 baseline and more thinking.js" "runs/NN what it is" 2`; `ONLY_UNLIMITED=1` runs only DeepSeek alone at the highest setting with a 200,000-token limit; `node "19 baseline and more thinking.js" --questions` shows the questions without calling DeepSeek; `node "19 summarise baseline.js" "runs/FIRST" "runs/MORE"` writes `summary.md`.
- **Who picks the questions:** `DEEPSEEK_API_KEY=... NODE_USE_ENV_PROXY=1 node "20 who picks the questions.js" "runs/NN what it is" 3`; `node "20 who picks the questions.js" --summarise "runs/..."` rewrites its tables from the records.
- **Long texts:** `DEEPSEEK_API_KEY=... NODE_USE_ENV_PROXY=1 node "21 long texts.js" "runs/NN what it is" 2`; `node "21 long texts.js" --show WORLD` prints the short and long messages; `--summarise "runs/..."` rewrites the tables.
- **Twenty questions:** `DEEPSEEK_API_KEY=... NODE_USE_ENV_PROXY=1 node "22 twenty questions.js" "runs/NN what it is" 2`; `--summarise "runs/..."` rewrites the tables.
- **The owner will not say:** `DEEPSEEK_API_KEY=... NODE_USE_ENV_PROXY=1 node "23 owner will not say.js" "runs/NN what it is" 2`; `--summarise "runs/..."` rewrites the tables.
- **Construction test:** `DEEPSEEK_API_KEY=... NODE_USE_ENV_PROXY=1 node "25 construction test.js" "runs/NN what it is" REPEATS`; `FIRST_REPEAT=2` numbers the repeats from 2; `WITHOUT_HARD_TO_VARY=1` leaves out the sixth arm; `--summarise "runs/..."` rewrites the tables. Commit a plan with its conjectures before running.
- **Attack surface** (after a top-up): `DEEPSEEK_API_KEY=... NODE_USE_ENV_PROXY=1 node "26 attack surface.js" "runs/26 attack surface" 3`; `--summarise "runs/..."` rewrites the tables.
- **Planted-mistakes correctors from log 19** (names hold commas, so the list is split at semicolons): `ONLY="self review, max thinking, reply limit 200,000;guesser fixes first"`.
- `NODE_USE_ENV_PROXY=1` is needed only where the internet is reached through a proxy, as on the computer that made log 17 and 18.
- The DeepSeek balance can be read before and after a run (`https://api.deepseek.com/user/balance`) to say what it cost.

## Keeping the documents up to date

After every change or run:

- **Project story**: add a new numbered log entry at the bottom of the log, including failures. Never rewrite earlier entries. Update "where things stand", the parts table, the word list and the next step to match.
- **"Status.md"**: rewrite it to match today.
- **"Decisions.md"**: add new decisions at the bottom of their section. Quote the owner exactly.
- **"Lessons.md"**: add only things that broke and were fixed.
- **Word list**: a new word goes in the project story's word list the first time it is used. One word per thing: the same thing is never called by a second name.
- **Every document** ends with a Traps section.

## Authority documents

These are frozen: they are not changed unless the owner says so. None of them is in this project folder. They were uploaded in the earlier chat, "Small LLMs planning and reasoning with error correction", and again in the chat that made log 17 and 18; they would need to be uploaded again to be read.

| Document | What it is | Where it is |
|---|---|---|
| "Claude Fable Semantics – standalone theory", revision 1 | The theory the project follows. The hard-to-vary tests come from it. | Uploaded in the earlier chat. Not in this folder. |
| HardToVary.zip | The owner's hard-to-vary skill. | Uploaded in the earlier chat. Not in this folder. |
| strata-kit-source.zip | The owner's Strata kit. Its lessons were kept, not its code (Decisions C2). | Uploaded in the earlier chat. Not in this folder. |

## Glossary: this project's words and the theory's words

The left column is the word used everywhere in this project. The right column is where the same idea sits in "Claude Fable Semantics – standalone theory", revision 1. These links were made in the earlier chat. In the chat that made log 17 and 18 the document was read again and the lines below were checked against it; the rows from "cross-check" down were added then.

| This project's word | In the theory |
|---|---|
| thing | a port |
| state | the value a port holds |
| rule | a component |
| model | an organization; a candidate explanation (E) |
| event | an admitted edit that sets an input |
| start | the boundary condition |
| situation | one admitted edit together with its boundary |
| jobs | the question's contract and query |
| world | the target (D) |
| a job passes | question fidelity (A) |
| "the answer is already in the start" | fails non-circular dependence |
| "no job expects anything else" | fails non-vacuity |
| held, idle, two routes | critical blocks and redundant routes (Part VI) |
| deciding test | Derivation 2 |
| small fix, new rule search | selection (Part IV) |
| new part | construction (Part IV, Derivation 10) |
| fix check | Repair (Part XI, condition P) |
| held-back job | Derivations 3 and 4 |
| surprise | Part IV, Derivation 4 |
| cross-check | Repair's protected obligations (Part XI, condition P): a fix must not lose what it should protect, including what no job yet states |
| look for surprises | Derivation 4: surprise needs a history smaller than the changes the world admits |
| poke | Part II, kinds are edit-signatures: a part no admitted change can move is not shown to matter |
| the checker's one-step fixes cannot reach the right repair | Derivation 3 as revised: a fitted repair is open only where its population holds a differing survivor; one-step fixes are a small population |
| self review, guesser fixes first | a construction response (Part IV): a new organization with a represented target, not a re-tune |
| a whole rewrite re-guesses every part | Derivation 8 does not apply: a rewrite is not a content-preserving recoding |

## Traps

- **Changing the page instead of the code files.** The next build overwrites the page, and the change is lost silently.
- **Skipping the browser test because the other two passed.** The browser test is the only one that checks the page's layout and its connection handling.
- **Treating the glossary as settled.** It was checked against revision 1 in the chat that made log 17 and 18. A new revision of the theory means checking it again.
- **Leaving the account key in a command history or a file.** Set it for the one command, or in the terminal session only.
- **Leaving work only on this computer.** The computer resets between chats. Download the zip after every major change (log 15).
