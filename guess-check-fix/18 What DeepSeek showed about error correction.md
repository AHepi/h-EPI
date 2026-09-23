# What DeepSeek showed about error correction

Log entries 17 and 18. Every number here comes from the run records in `runs/`, made with DeepSeek V4.1 Flash as the guesser on 23 September 2026. Nothing here was run on Sonnet or on the small AI.

## The short answer

- **DeepSeek's first guesses are usually right on what it is shown.** 18 of 20 first guesses passed every shown job. What it gets wrong is what it was *not* shown: 11 of 64 held-back jobs failed after the first guess alone.
- **Those mistakes cannot be found by checking the shown jobs, however hard you check.** The checker's small fixes and DeepSeek's rewrites from the checker's report repaired **none** of the 20 hidden mistakes planted on purpose, because nothing was failing.
- **Two things do find them, and they find different ones:** asking the world (the owner, or a real test) about situations near the jobs, and DeepSeek rereading its model against the request. The full loop repaired 11 of 20 hidden mistakes, DeepSeek's self review 9 of 20; only 4 were repaired by both, and 16 of 20 by one or the other.
- **Whole rewrites carry a cost.** When DeepSeek rewrites the whole model it fixes the broken part and also re-guesses every other part in its own reading of the request. Where the request is open to two readings, that can undo parts that were right.
- **Best overall so far: "guesser fixes first"**, the full loop in which DeepSeek gets the first go at repairing anything the world contradicts. On the ten worlds it ended with every job passing in 15 of 20 runs (full loop 13, guess and fix 11, first guess alone 9), and it repaired all 10 visible planted mistakes and 11 of 20 hidden ones.

## An example first: the lighthouse story

The request says Mara stays "because she has seen Tev cannot keep the light alone". DeepSeek's model said: Mara realises Tev can't cope **when she lights the lamp during the storm**. The world's version: she realises it because **the lamp was dark during the storm**. Both pass every shown job.

What happened in the first run (log 17):
1. The loop asked the world: storm, then Mara finds the letter, with no lamp-lighting. The world said she stays. So DeepSeek's model was wrong.
2. The checker repaired it the cheapest way: delete the lamp condition, so *any* storm makes her realise. That fits every job it knew.
3. A held-back job caught it: if the lamp was already lit when the storm came (Tev didn't fail), she leaves. The repaired model says she stays.

The checker's repair was itself a guess, and nothing tested it. Three changes (log 17) fixed this:
- **The checker can now swap a condition for one about a different thing** ("Mara lights the lamp" becomes "the lamp is dark"). Before, deleting was the only repair it could see.
- **A fix is a guess too.** Before the full loop keeps a checker fix, it asks the world about one situation where the model before and after the fix disagree.
- **Look for surprises.** When no rival rule is in sight, the loop asks the world about situations one change away from the jobs where the model takes a route no job has tested. Once a round, it also changes the starting state of something **no rule looks at**: by the model's own account that can't matter, so it's the hard-to-vary skill's "change something that should not matter" test. That's what finally caught the lamp: in the model the lamp did nothing, and in the world it mattered.

With these, the same DeepSeek guess replayed through the full loop passes both held-back jobs, and the world was never asked about either held-back situation directly.

## The planted mistakes

To test error correction directly, each world's true model was given a known mistake, then handed to each corrector as if it were DeepSeek's first guess. The mistakes were picked by a fixed shuffle, not by hand: from each world, one **visible** mistake (a shown job fails) and two **hidden** ones (every shown job passes, a held-back job fails). Two more were written by hand because they need a whole new thing to repair. A mistake counts as **repaired** only when every shown and held-back job passes **and** none of up to 400 nearby situations ends differently from the world.

| Corrector | Visible (10): repaired | Hidden (20): repaired | Needs a new thing (2): repaired | Made worse |
|---|---|---|---|---|
| checker alone | 6 | 0 | 0 | 1 |
| rewrite (DeepSeek, from the checker's report) | **10** | 0 | 0 | 0 |
| self review (DeepSeek, no report) | 6 | 9 | 0 | 3 |
| guess and fix | 7 | 0 | 1 | 0 |
| full loop | **10** | 11 | 1 | 1 |
| guesser fixes first | **10** | 11 | 1 | 1 |
| review first | 6 | **12** | 1 | 3 |

The full table, every mistake with every corrector's result, is in `runs/18 planted mistakes/results.md`.

What the table says:
- **DeepSeek can use criticism.** Given the checker's report it repaired all 10 visible mistakes. The small AI in the earlier chat never could (log 08).
- **The checker alone can make things worse.** On a door-game mistake it made every shown job pass while the model got more wrong overall (302 nearby situations wrong before, 375 after). That's fitting, not correcting.
- **Self review finds hidden mistakes nobody reported**, 9 of 20, with no questions to anyone. But 3 times it made things worse: it rewrote the puzzle and the watering system in its own reading.
- **"Review first" (self review, then guesser fixes first) did not add up to the two separately.** It repaired one more hidden mistake but four fewer visible ones. In all four, the review fixed the planted mistake and re-guessed other parts in DeepSeek's own reading, and the later steps never undid it.

## What is still wrong

- **Borrowed lantern:** DeepSeek reads "the stranger goes out searching" as one moment; the world reads it as something that keeps going. Surprise-hunting did not reach that situation. A second kind of poke (add an event the model says does nothing) was tried and dropped: it landed on the wrong events and changed nothing (log 18).
- **Ghost lantern:** DeepSeek lets the lantern light without the key. The world is only ever asked about the things the shown jobs ask about, and no shown job asks about the lantern, so no question can catch this.
- **River crossing:** the request is honestly ambiguous about two things (can the farmer "cross with the fox" when the fox is on the other bank; does the fox eat the goose before the goose eats the grain). The world's reading is one choice, not the only right one.
- **Needs a new thing:** for the to-do app without a put-off count, the full loop made it worse (44 nearby situations wrong became 52). DeepSeek was asked for a new part but none was accepted.

## What was not tested

- Whether any of this holds on other models. Only DeepSeek V4.1 Flash was run.
- Whether the world's answers could come from a real person. In every run the hidden true model answered, instantly and always correctly.
- How much repeats vary. Each world was run twice; that shows the two repeats often differ, not how often.
- Timing mistakes in the "nearby situations" grade: it compares end states only, so it cannot see the hidden ball's timing mistakes. The held-back jobs still do.

## What it cost

The DeepSeek balance went from $21.52, read just before the second run, to $20.11 after the last run: $1.41 for everything in log 18. The first run (log 17) was made before the first balance check and is not in that figure. Over all runs DeepSeek sent 272 replies and about 2.6 million output tokens, most of it thinking. 2 replies were cut off at the reply limit.

## Traps

- **Reading "repaired" as "right".** A repaired model matches this world's reading of the request. Where the request is ambiguous (the river, the lantern search), a different reading can be just as defensible.
- **Reading held-back scores in the full loop as unseen tests.** The world is sometimes asked about a held-back situation. Each results table has a column saying how many; the planted-mistakes grade uses nearby situations as well for this reason.
- **Mixing the fifth way's two names.** The planted-mistakes records from the first run call it "full loop, guesser first"; everywhere else it is "guesser fixes first". They are the same way of running (log 18).
