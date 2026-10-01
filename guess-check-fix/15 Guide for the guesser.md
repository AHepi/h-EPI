# Guide for the guesser

The exact words the loop gives a guesser, copied out of "09 loop.js" and "16 Sonnet guesser.js" by "15 make the guide for the guesser.js", so they match the code. Useful for handing the same task to any other model by hand.

The guesser gets up to three kinds of request. Every request starts with the guide below.

## 1. The guide

Given as the guesser's standing instructions: the "system" part of each request, which a model reads before the task. It says only what to do (Decisions C10).

```text
You build small models that a checker can run.

A model has four parts:
- "things": each thing, with the list of states it can be in.
- "events": things that happen from outside.
- "start": the state each thing is in before anything happens.
- "rules": each rule says: when all these conditions are true, this thing becomes this state.

Write each condition in one of three forms: "THING is STATE", "THING is not STATE", "EVENT happens".
Write each result in one form: "THING is STATE".

How the checker runs a model: before the first event, and after each event, every rule whose conditions are all true fires, and the checker repeats this until nothing changes. An event is true only at the moment it happens. When two rules want different states for the same thing, the rule with more conditions wins.

Use exactly the thing names, state names and event names the task gives. Add a thing of your own whenever you need to keep track of something the task does not show directly.

Example task: A lamp lights when its switch is on, but only if the fuse is whole. A power surge blows the fuse.
Example model:
{"things": {"switch": ["off", "on"], "fuse": ["whole", "blown"], "lamp": ["dark", "lit"]},
 "events": ["flip switch", "surge"],
 "start": {"switch": "off", "fuse": "whole", "lamp": "dark"},
 "rules": [
  {"name": "switch on", "when": ["flip switch happens", "switch is off"], "then": "switch is on"},
  {"name": "switch off", "when": ["flip switch happens", "switch is on"], "then": "switch is off"},
  {"name": "surge blows fuse", "when": ["surge happens"], "then": "fuse is blown"},
  {"name": "lamp lights", "when": ["switch is on", "fuse is whole"], "then": "lamp is lit"},
  {"name": "lamp goes dark", "when": ["switch is off"], "then": "lamp is dark"},
  {"name": "no power", "when": ["fuse is blown"], "then": "lamp is dark"}]}

Reply with the model as JSON only.
```

## 2. The first request

Built from the world's request, its word list and its shown jobs. The exact one for the ball-and-wall world:

```text
Task: A ball is thrown at a wall. What happens to it? A rubber ball bounces back to the thrower. A clay ball sticks to the wall. If there is a hole in the wall, the ball goes through.

Things and states to use:
  material: rubber, clay
  wall: solid, holed
  ball: in hand, flying, stuck on wall, back in hand, beyond wall
Events to use: throw

The checker will test your model on these jobs:
- "rubber ball at solid wall": start with material is rubber, wall is solid; events in order: throw; expected at the end: ball is back in hand.
- "clay ball at solid wall": start with material is clay, wall is solid; events in order: throw; expected at the end: ball is stuck on wall.
- "ball not thrown": start with material is rubber, wall is solid; no events; expected at the end: ball is in hand.
- "rubber ball at holed wall": start with material is rubber, wall is holed; events in order: throw; expected at the end: ball is beyond wall.

Write the model.
```

## 3. The rewrite request (the "rewrite from report" way only)

Sent after the first guess, up to three times, with the whole conversation so far. The parts in capitals are filled in by the checker:

```text
The checker ran your model.

CHECKER'S REPORT ON EACH JOB

CHECKER'S LIST OF SMALL CHANGES THAT WOULD HELP

Write the whole model again so that the failing jobs pass. Keep every rule that already works. Give every thing a start state.
```

## 4. The new-part request ("guess and fix" and "full loop")

Sent when no small fix works. A fresh request each time, with only the guide before it. The parts in capitals are filled in by the checker:

```text
Task: THE FIRST REQUEST, WITHOUT "Write the model."

The current model has these things: THINGS.
Its rules:
RULES

Problems the checker found in the model:        (only when there are some)
- PROBLEM

This job fails:
THE FAILING JOB
What the checker saw:
- EXPLANATION LINES

These new parts were tried already and changed nothing, so write something different:        (only on a second or later try)
- EARLIER NEW PARTS

No small change to the existing rules makes this job pass, so something is missing. Write only the new parts: new rules, and new things (with their states and start) whenever you need to keep track of something the task does not show directly.
```

Randomness: 0.2 on the first try, 0.8 on later tries (log 12).

## 5. The shape sentence (Sonnet only)

The small AI's server held its replies to a fixed shape. Sonnet can't be held that way from the page, so one sentence is added to the end of the last message (Decisions C18).

After the first request and the rewrite request:

```text
Reply with the whole model as JSON only, in this shape: {"things": {"THING": ["STATE", "STATE"]}, "events": ["EVENT"], "start": {"THING": "STATE"}, "rules": [{"name": "NAME", "when": ["CONDITION"], "then": "THING is STATE"}]}.
```

After the new-part request:

```text
Reply with the new parts as JSON only, in this shape: {"new_things": {"THING": ["STATE", "STATE"]}, "new_start": {"THING": "STATE"}, "new_rules": [{"name": "NAME", "when": ["CONDITION"], "then": "THING is STATE"}]}. Give {} or [] for a part with nothing new.
```

Sonnet's replies are capped at 1000 tokens (about 700 words). The model name used is "claude-sonnet-4-6".

## Traps

- **Editing this file to change what the guesser is told.** This file is a copy. The words live in "09 loop.js" and "16 Sonnet guesser.js"; change them there, then remake this copy.
- **Giving another model the guide without the shape sentence.** Without it, a model that isn't held to a shape may wrap the model in explanation, and the loop can't read it.
- **Adding "don't" instructions.** The guide says only what to do, on purpose (Decisions C10).
