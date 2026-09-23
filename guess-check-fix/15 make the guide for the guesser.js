/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Remakes "15 Guide for the guesser.md" by copying the exact words the guesser is given out of
 * "09 loop.js" and "16 Sonnet guesser.js". Run it after changing any of those words, so the
 * guide file always matches the code.
 */
const fs = require('fs');
const L = require(require('path').join(__dirname, '09 loop.js'));
const W = require(require('path').join(__dirname, '03 test worlds.js'));
const C = require(require('path').join(__dirname, '03 checker.js'));
const S = require(require('path').join(__dirname, '16 Sonnet guesser.js'));
const world = W[0];
const jobs = C.prepare_jobs({ jobs: world.jobs.filter(j => !j.held_back) }).jobs;
const first = `Task: ${world.request}\n\n${L.vocabulary_in_words(world)}\n\nThe checker will test your model on these jobs:\n${jobs.map(L.job_in_words).join('\n')}\n\nWrite the model.`;
const fence = t => '```text\n' + t + '\n```';
const doc = `# Guide for the guesser

The exact words the loop gives a guesser, copied out of "09 loop.js" and "16 Sonnet guesser.js" by "15 make the guide for the guesser.js", so they match the code. Useful for handing the same task to any other model by hand.

The guesser gets up to three kinds of request. Every request starts with the guide below.

## 1. The guide

Given as the guesser's standing instructions: the "system" part of each request, which a model reads before the task. It says only what to do (Decisions C10).

${fence(L.GUIDE)}

## 2. The first request

Built from the world's request, its word list and its shown jobs. The exact one for the ball-and-wall world:

${fence(first)}

## 3. The rewrite request (the "rewrite from report" way only)

Sent after the first guess, up to three times, with the whole conversation so far. The parts in capitals are filled in by the checker:

${fence('The checker ran your model.\n\nCHECKER\'S REPORT ON EACH JOB\n\nCHECKER\'S LIST OF SMALL CHANGES THAT WOULD HELP\n\nWrite the whole model again so that the failing jobs pass. Keep every rule that already works. Give every thing a start state.')}

## 4. The new-part request ("guess and fix" and "full loop")

Sent when no small fix works. A fresh request each time, with only the guide before it. The parts in capitals are filled in by the checker:

${fence('Task: THE FIRST REQUEST, WITHOUT "Write the model."\n\nThe current model has these things: THINGS.\nIts rules:\nRULES\n\nProblems the checker found in the model:        (only when there are some)\n- PROBLEM\n\nThis job fails:\nTHE FAILING JOB\nWhat the checker saw:\n- EXPLANATION LINES\n\nThese new parts were tried already and changed nothing, so write something different:        (only on a second or later try)\n- EARLIER NEW PARTS\n\nNo small change to the existing rules makes this job pass, so something is missing. Write only the new parts: new rules, and new things (with their states and start) whenever you need to keep track of something the task does not show directly.')}

Randomness: 0.2 on the first try, 0.8 on later tries (log 12).

## 5. The shape sentence (Sonnet only)

The small AI's server held its replies to a fixed shape. Sonnet can't be held that way from the page, so one sentence is added to the end of the last message (Decisions C18).

After the first request and the rewrite request:

${fence(S.SHAPE_SENTENCES['model'])}

After the new-part request:

${fence(S.SHAPE_SENTENCES['new part'])}

Sonnet's replies are capped at ${S.REPLY_LIMIT} tokens (about 700 words). The model name used is "${S.MODEL_NAME}".

## Traps

- **Editing this file to change what the guesser is told.** This file is a copy. The words live in "09 loop.js" and "16 Sonnet guesser.js"; change them there, then remake this copy.
- **Giving another model the guide without the shape sentence.** Without it, a model that isn't held to a shape may wrap the model in explanation, and the loop can't read it.
- **Adding "don't" instructions.** The guide says only what to do, on purpose (Decisions C10).
`;
fs.writeFileSync(require('path').join(__dirname, '15 Guide for the guesser.md'), doc);
console.log("Remade 15 Guide for the guesser.md");
