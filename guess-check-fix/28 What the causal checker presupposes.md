# What the causal checker presupposes about cause

Log entry 28. The owner asked: "Once you have a working checker, I'll be interested to know what it presupposes about causality." This is my reading of `28 causal checker.js` and the checker beneath it. Each point says what the checker takes for granted, gives a small example, and says whether the corpus run ("28 Causal checker.md") bore on it.

## An example first

The checker is handed a model of how frogs grow: more eggs laid, more tadpoles hatch, more frogs. The question is "suppose fewer eggs are laid, how will it affect the frogs?".

The checker holds "eggs laid" at "less", leaves every other rule alone, runs the model until nothing changes, and compares the frogs with a run where nothing was held. The frogs come out "less", so the answer is that fewer frogs appear.

Every step of that took something for granted.

## What it takes for granted

1. **A cause is a difference made by holding something.** "A causes B" means: hold A at another level, and B ends differently from the usual run. That is the semantics' reading (Part II: a causal link moves when a part is changed and stays put when it is only looked at) and the interventionist reading familiar from Pearl and Woodward. Nothing else counts as a cause: not a regularity, not a story, not a mechanism no one can hold.

2. **Every causal claim is against a usual run.** "More eggs" means more than usual. The answer to "why?" is always "why this rather than the usual". What counts as usual is chosen by whoever writes the start of the model. The corpus's questions have the same shape ("suppose more ... happens").

3. **Holding one thing disturbs nothing else.** Holding "eggs laid" at "less" switches off only the rules that set eggs laid; every other rule runs as before. Real changes are rarely that clean: "humans collect the frogspawn" also disturbs the pond. The checker cannot say "this change comes with side effects" unless the model already has them as separate things.

4. **The things are given.** The checker finds causes only between things someone named. Whether "tadpole growth" and "tadpoles" are one thing or two, and whether "the weather" is a thing at all, is the translator's guess, not the checker's.

5. **What is not in the model has no effect.** A change the model does not mention changes nothing. The checker cannot tell "no effect" from "not modelled". And to connect a change in the world's words ("a drought") to a thing in the model ("water available"), someone outside the checker must supply the link. That link is itself a causal claim the checker never tests.

6. **Direction is written in, not found.** Causes run along rules, from conditions to results. The checker tells seeing from making (the dark room tells you the lamp is off; darkening the room does not switch it off), but only in the direction the model already holds. If a rule points the wrong way, the checker faithfully reports the wrong direction.

7. **Time is steps, and everything settles.** A cause acts one step before its effect, and between events the model runs until nothing changes. So an effect is where things end up, not how fast or when along the way. A loop (frogs make eggs make frogs) ends at a fixed level; it cannot grow without limit.

8. **No sizes.** With influences, a quantity is usual, more or less. Two pushes in opposite directions (more rain, but more plant cover) cannot be weighed, so the checker says "unsettled". It cannot say "a little", "a lot", or "enough to tip it over".

9. **An influence points one way everywhere.** "More water helps plants" holds at every level. The checker cannot say "water helps up to a point, then drowns them" unless the translator writes rules for each level.

10. **No chance.** Every rule fires whenever its conditions hold. "Usually" is only a tie-breaker between rules, not a probability. "Some of the eggs are not fertilised" can only be read as "fewer eggs hatch".

11. **"Why" means "but for".** In one situation, a thing is a cause if taking it away changes the outcome. Background conditions that were there all along (oxygen for a match) are never causes, because they were not a difference from the usual start. When two causes are each enough on their own (rain and a sprinkler), no single one passes the test. The checker reports the pair, but it cannot tell that case from one where the second cause was only a backup that never acted.

12. **Causes are states and events.** Not people, reasons or intentions. A missing thing can be a cause only if the model has a state for it being missing.

13. **The checker only draws consequences.** Whether the model is true is settled outside it, by the world. In the corpus run, people's answers stand in for the world, and they are a reading, not the world.

## Which of these the corpus run bore on

(Filled in from the records after the run; see "28 Causal checker.md".)
