# Plan: a language that grows

Written before any code for log 35 was run, and not to be changed after. The results go in "35 A language that grows.md".

## What the owner asked

After log 34: "Do it", meaning test the other half of condition 2. Can a language that can grow close the gap log 34 found between the checker's rule language and a universal one?

## The question

In log 34 the rule language could not hold an unlimited count or pile, and JavaScript could. But in the JavaScript arm the whole explanation became a program, and the checker's own tools (reporting which rule failed, the hard-to-vary sweep) no longer apply to its parts. A language that grows keeps the explanation as things, events and rules, and lets the guesser add a new primitive when the old ones cannot hold what it needs.

## How the rule language may grow

A model may define **new kinds of thing**, each with:
- a starting value;
- named **changes**, each a short JavaScript expression giving the new value from the old (`value + 1`);
- named **tests**, each a short JavaScript expression giving true or false (`value === 0`).

A model then lists **new things** of those kinds, and its rules use them like any other part:
- a condition "balance is zero" or "balance is not zero" reads a test;
- a result "balance does add one" applies a change.

Everything else is the rule language as it is: finite things with listed states, events, a start, and rules that fire when their conditions hold, settling after each event.

The program accepts a model only if every name in it is known and every expression runs. It runs the model, and each kind's expressions, in a separate process with no access to files, the network or the account key, and with a time limit.

**Where the growth is, and where it is not.** The new kind's inside is written in JavaScript, which is universal, so this is a language that grows by borrowing from a universal one, as people define new terms in words. What is tested is whether DeepSeek, given the chance, adds the primitive the explanation needs and keeps the rest of the explanation in rules.

## The devices

- **Balance gate**, as in log 34: open exactly when pushes equal pulls. The same 20 observations, and log 34's 12 test cases plus 2 deeper ones: 500 pushes then 500 pulls (open), and 500 then 499 (shut).
- **Peg tube, redesigned.** Log 34's tube could not tell a pile from separate counts of each colour. Now the near rival is named: **separate counts**. In that rival, a peg can come out if one of its colour is anywhere inside; an empty colour jams. The observations and test cases are chosen to refute it.
  - **Observations:** 24, drawn by a fixed scramble from sequences of up to five actions, 8 for each light. At least 4 of the 8 red ones are cases the separate-counts rival gets wrong.
  - **Short test cases:** 6 unseen, 2 for each light, at least one the rival gets wrong.
  - **Long test cases (13):**
    - log 34's six;
    - 8 red in, 8 blue in, then red out (red);
    - 30 red in, 30 red out (green);
    - 20 in by log 34's colour pattern, then out in the right order (green);
    - the same 20 in, then out with the last removal the wrong colour (red);
    - 15 red in, 1 blue in, 15 red out, 1 blue out (red);
    - 10 blue in, 10 red in, 10 blue out, 10 red out (red);
    - the 20 in, then out bottom first (red).

    The last three are cases separate counts must get wrong.

    *Added before any run: a check of the first ten long cases found that separate counts got 9 of them right by coincidence, which would have repeated log 34's gap in the long tests, so three cases it must get wrong were added.*
- **Grudge**, log 25's, as the control: its explanation fits the rule language, so growth is not needed.

## The arms

Every arm gets the same description, observations and criticism, and the sentences "Keep track of anything you cannot see directly, if you need to" and "Your explanation will be tested on sequences of any length, including sequences of a hundred actions."
- **fixed language:** log 34's arm, unchanged.
- **growing language:** the rule language with new kinds, as above. Same loop: up to 6 models; the report names each failing observation, what was seen and what the model gave, and any names or expressions that do not work.
- **universal language:** log 34's JavaScript arm, unchanged, as the ceiling.

That is three devices, three arms and three repeats: 27 runs, about $1.50 to $3 ($14.98 left).

## What is measured

- Test cases right: long, short, hard, and for the peg tube the ones the separate-counts rival gets wrong.
- Whether the best model fits every observation.
- Replies cut off.
- In the growing language, how many new kinds and new things each model defines, and how many rules it keeps. This shows whether the explanation stayed in rules or moved inside a kind.

## Conjectures, written before the run

1. **The growing language gets more long test cases right than the fixed language,** on the gate and peg tube together, summed over repeats.
2. **The growing language gets within 3 of the universal language on long test cases,** on the gate and peg tube together (of 63). Growth closes the gap.
3. **Growth does no harm where it is not needed:** on the grudge, the growing language is within 2 hard cases of the fixed language.
4. **DeepSeek uses growth when it needs it, and not otherwise:** it defines at least one new kind in every gate and peg run of the growing arm, and in at most one of the three grudge runs.
5. **Growth avoids the too-big-to-write failure:** at most 2 replies cut off in the growing arm's gate and peg runs together.
6. **The redesigned tube separates a pile from counts:** the fixed language gets fewer than half its peg long test cases right (fewer than 20 of 39).

## What would count against the idea that a growing language closes the gap

- The growing language no better than the fixed one on long cases: DeepSeek did not use growth, or used it wrongly.
- The growing language matching the universal one only by putting the whole device inside one kind, with rules that merely pass its answer through. The kinds-and-rules counts will show this.

## Traps

- **Reading "grows" as DeepSeek inventing a language.** It adds a primitive through a door the program provides, written in a universal language.
- **Reading the gate's deep cases as settled by observations.** No finite set of observations can rule out a big enough approximation; only the long cases do.
- **Reading three repeats as settled.**
