/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * The loop. It hands a task to a guesser (an AI that writes models) and runs this cycle:
 *   1. GUESS  - the guesser writes a model (things, events, start, rules) as filled-in blanks.
 *   2. CHECK  - the checker runs the model on the owner's jobs and says what failed and why.
 *   3. FIX    - two kinds of fix, and the checker keeps a fix only if it repairs something and
 *               breaks nothing that worked (no backsliding):
 *               small fix: the checker tries every one-step change to the existing rules and applies
 *                          one that works. When several work equally, in the full loop it asks the
 *                          world a deciding question to choose between them.
 *               new part:  when no small fix works, the guesser is asked for just the new rule(s),
 *                          or a new thing to keep track of, that the failing job needs.
 *               clearing out: a new part can make old rules wrong. When the new part's rules disagree
 *                          with old rules, the checker also tries the model without those old rules.
 *               last resort: when the guesser's tries are used up, the checker searches for one new
 *                          rule itself, and marks it as fitted by the checker.
 *               (An earlier version had the guesser rewrite the whole model from the checker's
 *               advice. The 1.5B small AI could not apply advice it was given; see the project log.)
 *   4. ASK    - once every job passes, the checker looks for rules that are loose and builds a
 *               deciding test for each: a situation where the model and a near neighbour disagree.
 *               The world (a hidden true model, standing in for reality or for the owner) answers.
 *               Each answer becomes a new job, and the loop goes back to FIX.
 *   5. END    - jobs held back from the start are run once, to see if the model fits things
 *               it was never shown.
 *
 * Four ways of running, to compare, all starting from one shared first guess:
 *   one guess      - step 1 only
 *   rewrite        - the guesser rewrites its whole model from the checker's report (the earlier design)
 *   guess and fix  - steps 1 to 3, with no questions to the world
 *   full loop      - steps 1 to 5
 *
 * Who the guesser is: by default the small AI, run locally through llama.cpp's server (address in
 * SMALL_AI_ADDRESS). Any other guesser can be passed in as options.guesser: a function that takes
 * the messages and settings and returns the reply text. The Sonnet page does this.
 * Every request and reply is saved, so a run can be read afterwards.
 */
const fs = require('fs');
const C = require('./03 checker.js');

const SMALL_AI_ADDRESS = (typeof process !== 'undefined' && process.env && process.env.SMALL_AI_ADDRESS) || 'http://127.0.0.1:8081/v1/chat/completions';

// The shape the guesser must fill in. The small AI's server holds the reply to this shape, so it is always readable JSON.
const MODEL_SHAPE = {
  type: 'object',
  properties: {
    things: { type: 'object', additionalProperties: { type: 'array', items: { type: 'string' } } },
    events: { type: 'array', items: { type: 'string' } },
    start: { type: 'object', additionalProperties: { type: 'string' } },
    rules: { type: 'array', items: { type: 'object', properties: { name: { type: 'string' }, when: { type: 'array', items: { type: 'string' } }, then: { type: 'string' } }, required: ['name', 'when', 'then'] } },
  },
  required: ['things', 'events', 'start', 'rules'],
};

// The shape for a new part: only what is being added.
const NEW_PART_SHAPE = {
  type: 'object',
  properties: {
    new_things: { type: 'object', additionalProperties: { type: 'array', items: { type: 'string' } } },
    new_start: { type: 'object', additionalProperties: { type: 'string' } },
    new_rules: MODEL_SHAPE.properties.rules,
  },
  required: ['new_things', 'new_start', 'new_rules'],
};

// Positive instructions only: say what to do.
const GUIDE = `You build small models that a checker can run.

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

Reply with the model as JSON only.`;

function job_in_words(job) {
  const parts = [];
  const start = Object.entries(job.situation.start || {}).map(([t, s]) => `${t} is ${s}`);
  if (start.length) parts.push(`start with ${start.join(', ')}`);
  const events = Object.keys(job.situation.events || {}).sort((a, b) => Number(a) - Number(b)).flatMap(k => job.situation.events[k]);
  parts.push(events.length ? `events in order: ${events.join(', then ')}` : 'no events');
  const at = job.at === 'end' ? 'at the end' : job.at === 'ever' ? 'at some point' : job.at === 'never' ? 'never' : `at step ${job.at}`;
  parts.push(`${job.at === 'never' ? 'must never have' : `expected ${at}:`} ${job.expect.join(' and ')}`);
  return `- "${job.name}": ${parts.join('; ')}.`;
}
function vocabulary_in_words(world) {
  const owner_things = new Set();
  for (const job of world.jobs) {
    Object.keys(job.start || {}).forEach(t => owner_things.add(t));
    (Array.isArray(job.expect) ? job.expect : [job.expect]).forEach(e => owner_things.add(e.split(/ is /)[0]));
  }
  const lines = [...owner_things].map(t => `  ${t}: ${world.world.things[t].join(', ')}`);
  return `Things and states to use:\n${lines.join('\n')}\nEvents to use: ${world.world.events.length ? world.world.events.join(', ') : '(none)'}`;
}

// The owner's word list: the things and states the shown jobs use. Given by the owner, not guessed.
function owner_word_list(world) {
  const list = {};
  for (const job of world.jobs.filter(j => !j.held_back)) {
    Object.keys(job.start || {}).forEach(t => { list[t] = world.world.things[t]; });
    (Array.isArray(job.expect) ? job.expect : [job.expect]).forEach(e => { const t = e.split(/ is /)[0]; list[t] = world.world.things[t]; });
  }
  return list;
}

async function ask_guesser(messages, log, options = {}, shape = MODEL_SHAPE) {
  const temperature = options.temperature == null ? 0.2 : options.temperature;
  const started = Date.now();
  let text;
  if (options.guesser) {
    // Another guesser (for example Sonnet, in the page) gets the same messages and settings.
    text = await options.guesser(messages, { temperature, reply_shape: shape === NEW_PART_SHAPE ? 'new part' : 'model' });
  } else {
    // The small AI, through llama.cpp's server, with its reply held to the shape.
    const body = { messages, temperature, max_tokens: 1400, seed: options.seed || 1,
      response_format: { type: 'json_schema', json_schema: { name: 'reply', schema: shape } } };
    let data = null;
    for (let attempt = 1; attempt <= 3 && !data; attempt++) {
      try {
        const reply = await fetch(SMALL_AI_ADDRESS, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
        data = await reply.json();
      } catch (e) { if (attempt === 3) throw e; await new Promise(r => setTimeout(r, 20000)); }
    }
    text = data.choices ? data.choices[0].message.content : JSON.stringify(data);
  }
  log.push({ asked: messages[messages.length - 1].content, replied: text, seconds: Math.round((Date.now() - started) / 1000) });
  return text;
}
function read_reply(text) {
  if (typeof text !== 'string') return null;
  try { return JSON.parse(text); } catch (e) {
    const m = text.match(/\{[\s\S]*\}/); if (m) { try { return JSON.parse(m[0]); } catch (e2) { /* fall through */ } }
    return null;
  }
}

// The world answers a deciding test: run the situation on the hidden true model.
function world_answers(world_model, found) {
  const problems = [];
  const situation = C.resolve_situation(world_model, found.situation, problems, 'world');
  if (problems.length) return null;
  const result = C.run(world_model, situation);
  return found.differences.map(d => {
    const thing = Object.keys(world_model.things).find(t => t.toLowerCase() === d.thing.toLowerCase());
    if (!thing) return null;
    const ends = [...new Set(result.final_states.map(s => s[thing]))];
    return ends.length === 1 ? `${thing} is ${ends[0]}` : null;
  }).filter(Boolean);
}

function summary_line(model, jobs) {
  const c = C.check(model, jobs);
  return `${c.passed.length}/${jobs.length}`;
}

function rules_in_words(model) {
  return model.rules.map(r => `- "${r.name}": ${C.rule_text_of(r)}`).join('\n');
}
function things_in_words(model) {
  return Object.entries(model.things).map(([t, states]) => `${t} (${states.join(', ')}; starts ${model.start[t]})`).join('; ');
}
// Add the guesser's new parts to the model: new things (or new states of old things), their start, new rules.
function add_new_parts(model, reply) {
  const form = C.model_to_form(model);
  for (const [thing, states] of Object.entries(reply.new_things || {})) {
    const existing = Object.keys(form.things).find(t => t.toLowerCase() === thing.toLowerCase());
    if (existing) form.things[existing] = [...new Set(form.things[existing].concat(states))];
    else form.things[thing] = states;
  }
  for (const [thing, state] of Object.entries(reply.new_start || {})) {
    const existing = Object.keys(form.things).find(t => t.toLowerCase() === thing.toLowerCase());
    if (existing && !Object.keys(model.things).includes(existing)) form.start[existing] = state;
  }
  const names = new Set(form.rules.map(r => r.name.toLowerCase()));
  for (const rule of (Array.isArray(reply.new_rules) ? reply.new_rules : [])) {
    let name = rule.name || 'new rule';
    while (names.has(name.toLowerCase())) name = `${name} (new)`;
    names.add(name.toLowerCase());
    form.rules.push(Object.assign({}, rule, { name, made_by: 'guesser new part' }));
  }
  return C.prepare_model(form);
}
// After a new part is added: remove the old rules that disagree with the new part's rules in any job,
// and repeat until none disagree. A selection step (removing is a variation); no guessing.
function clear_out_clashing_rules(model, jobs) {
  let current = model;
  const removed = [];
  for (let round = 0; round < 5; round++) {
    const names = new Set();
    for (const r of C.check(current, jobs).results) {
      for (const clash of (r.result ? r.result.clashes : [])) {
        const rules_in_clash = clash.offers.map(o => current.rules.find(x => x.name === o.rule)).filter(Boolean);
        if (!rules_in_clash.some(x => x.made_by === 'guesser new part')) continue;
        rules_in_clash.filter(x => x.made_by !== 'guesser new part').forEach(x => names.add(x.name));
      }
    }
    if (!names.size) break;
    removed.push(...names);
    const form = C.model_to_form(current);
    form.rules = form.rules.filter(r => !names.has(r.name));
    current = C.prepare_model(form);
  }
  return { model: current, removed };
}
function add_job(jobs, new_job) {
  const prepared = C.prepare_jobs({ jobs: [new_job] }).jobs[0];
  if (jobs.some(j => JSON.stringify(j.situation) === JSON.stringify(prepared.situation) && JSON.stringify(j.expect) === JSON.stringify(prepared.expect))) return jobs;
  return jobs.concat(prepared);
}
// Situations one change from the jobs where the model takes a route no job takes (log 17).
// Chosen from the model and the jobs only; the world is not looked at until it is asked.
function surprise_probes(model, jobs, how_many) {
  const route_of = situation => {
    const problems = [];
    const resolved = C.resolve_situation(model, situation, problems, 'probe');
    if (problems.length) return null;
    const result = C.run(model, resolved);
    return [...new Set(result.changes.flatMap(c => c.rules))].sort().join(' + ');
  };
  const asked_things = [...new Set(jobs.flatMap(j => j.expect.map(e => String(e).split(/ is /)[0].replace(/^not /, ''))))];
  const known_routes = new Set(jobs.map(j => route_of(j.situation)));
  const job_situations = new Set(jobs.map(j => JSON.stringify(j.situation)));
  // Things no rule reads: by the model's own account their start cannot matter. One probe per round
  // pokes one of them, the hard-to-vary skill's "change something that should not matter" test.
  const read_things = new Set(model.rules.flatMap(r => r.when.filter(w => w.kind === 'state').map(w => w.thing.toLowerCase())));
  let poked_unread = false;
  const picked = [];
  for (const c of C.candidate_situations(model, model, jobs, 1500, 'shared').list) {
    if (picked.length >= how_many) break;
    if (!c.steps.length || job_situations.has(JSON.stringify(c.situation))) continue;
    const unread = c.steps.length === 1 && /^(.+) starts (.+)$/.exec(c.steps[0]);
    if (!poked_unread && unread && !read_things.has(unread[1].toLowerCase()) && !asked_things.includes(unread[1])) {
      poked_unread = true;
      picked.push({ from_job: c.from_job, steps: c.steps, situation: c.situation, differences: asked_things.map(thing => ({ thing })) });
      continue;
    }
    const route = route_of(c.situation);
    if (route === null || known_routes.has(route)) continue;
    known_routes.add(route);
    picked.push({ from_job: c.from_job, steps: c.steps, situation: c.situation, differences: asked_things.map(thing => ({ thing })) });
  }
  return picked;
}
function job_from_deciding_test(world_model, found, number) {
  const answers = world_answers(world_model, found);
  if (!answers || !answers.length) return null;
  const events = found.situation.events || {};
  return { name: `world answer ${number}`, start: found.situation.start, events: Object.keys(events).sort((a, b) => Number(a) - Number(b)).flatMap(k => events[k]), expect: answers, from: 'given' };
}

async function first_guess(world, options = {}) {
  const log = [];
  const jobs = C.prepare_jobs({ jobs: world.jobs.filter(j => !j.held_back) }).jobs;
  const messages = [{ role: 'system', content: GUIDE }, { role: 'user', content: `Task: ${world.request}\n\n${vocabulary_in_words(world)}\n\nThe checker will test your model on these jobs:\n${jobs.map(job_in_words).join('\n')}\n\nWrite the model.` }];
  const text = await ask_guesser(messages, log, options);
  return { raw: read_reply(text), log };
}

async function run_task(world, mode, options = {}, guess = null) {
  const log = [];
  const record = { world: world.id, mode, rounds: [], added_jobs: [], questions_to_world: 0, guesser_calls: 0 };
  const world_model = C.prepare_model(world.world);
  let jobs = C.prepare_jobs({ jobs: world.jobs.filter(j => !j.held_back) }).jobs;
  const held_back = C.prepare_jobs({ jobs: world.jobs.filter(j => j.held_back) }).jobs;
  const task_words = () => `Task: ${world.request}\n\n${vocabulary_in_words(world)}\n\nThe checker will test your model on these jobs:\n${jobs.map(job_in_words).join('\n')}`;
  const messages = [{ role: 'system', content: GUIDE }, { role: 'user', content: `${task_words()}\n\nWrite the model.` }];
  const save_progress = () => {
    if (options.progress && fs) fs.writeFileSync(options.progress, JSON.stringify({ rounds: record.rounds }, null, 1));
    if (options.on_progress) options.on_progress(record);
  };

  // 1. GUESS (shared between ways of running, when given)
  if (!guess) { guess = await first_guess(world, options); record.guesser_calls++; }
  log.push(...guess.log);
  let best = guess.raw && typeof guess.raw === 'object'
    ? C.prepare_model(Object.assign({}, guess.raw, { rules: (Array.isArray(guess.raw.rules) ? guess.raw.rules : []).map(r => Object.assign({}, r, { made_by: 'guesser first guess' })) }))
    : C.prepare_model({ things: {}, rules: [] });
  messages.push({ role: 'assistant', content: JSON.stringify(guess.raw) });
  record.rounds.push({ step: 'guess', seen: summary_line(best, jobs), problems: best.problems.length });
  save_progress();

  // Log 18: the guesser checks the model against the task by itself, with no report from the checker.
  // Kept only if it loses no shown job that passed (no backsliding); whether it caught a mistake the
  // shown jobs cannot see is found out from the held-back jobs.
  const self_review = async () => {
    const ask = `Here is a model for this task. It may contain mistakes, including mistakes the jobs above do not catch.\n\n${JSON.stringify(C.model_to_form(best))}\n\nGo through the task sentence by sentence and check that every part of it is in the model, and that every rule does what the task says, in every situation the task describes, not only in the jobs. Correct every mistake you find. Write the whole corrected model. If you find no mistake, write it unchanged.`;
    const reply = read_reply(await ask_guesser([{ role: 'system', content: GUIDE }, { role: 'user', content: `${task_words()}\n\n${ask}` }], log, options)); record.guesser_calls++;
    const candidate = reply ? C.prepare_model(reply) : null;
    const f = candidate ? C.check_fix(best, candidate, jobs, { decide: false }) : { verdict: 'unreadable', lost: [] };
    const keep = candidate && !f.lost.length && candidate.problems.length <= best.problems.length;
    if (keep) best = candidate;
    record.rounds.push({ step: 'self review', verdict: f.verdict, kept: !!keep, lost: f.lost, seen: summary_line(best, jobs) });
    save_progress();
  };

  if (mode === 'rewrite') {
    // The earlier design: the guesser rewrites the whole model from the checker's report.
    for (let round = 0; round < (options.fix_rounds || 3) && C.check(best, jobs).failed.length; round++) {
      const ask = `The checker ran your model.\n\n${C.report_check(best, jobs).text}\n\n${C.report_tweaks(best, jobs).text}\n\nWrite the whole model again so that the failing jobs pass. Keep every rule that already works. Give every thing a start state.`;
      messages.push({ role: 'user', content: ask });
      const candidate_raw = read_reply(await ask_guesser(messages, log, options)); record.guesser_calls++;
      const candidate = candidate_raw ? C.prepare_model(candidate_raw) : null;
      const f = candidate ? C.check_fix(best, candidate, jobs, { decide: false }) : { verdict: 'unreadable' };
      if (f.verdict === 'accepted') best = candidate;
      record.rounds.push({ step: 'rewrite', verdict: f.verdict, repaired: f.repaired, lost: f.lost, seen: summary_line(best, jobs) });
      messages.push({ role: 'assistant', content: JSON.stringify(C.model_to_form(best)) });
      if (messages.length > 10) messages.splice(2, messages.length - 6);
      save_progress();
    }
  } else if (mode === 'self review') {
    await self_review();
  } else if (mode !== 'one guess') {
    // Log 18: "review first" is the guesser's self review, then "guesser fixes first".
    if (mode === 'review first') await self_review();
    const words = C.add_owner_words(best, owner_word_list(world));
    if (words.added.length) {
      const form = C.model_to_form(words.model);
      form.events = [...new Set(form.events.concat(world.world.events))];
      best = C.prepare_model(form);
      record.rounds.push({ step: 'owner words added', added: words.added, seen: summary_line(best, jobs) });
    }
    const may_ask_world = ['full loop', 'guesser fixes first', 'review first'].includes(mode);
    // Log 18: in "guesser fixes first" (the full loop otherwise), when jobs fail the guesser first rewrites the whole model from
    // the checker's report (it now includes the world's answers); the checker's small fixes tidy what is left.
    const guesser_first = ['guesser fixes first', 'review first'].includes(mode);
    const rewrite_asked_for = new Set();
    let guesser_rewrites = 0;
    const question_budget = options.questions || 12;
    let new_part_calls = 0, small_fixes = 0, ask_rounds = 0, surprise_rounds = 0, rule_searches = 0;
    const tried_before = [];
    // A FIX IS A GUESS TOO (log 17): before the full loop keeps a checker fix, it asks the world about one
    // situation, not yet a job, where the model before and after the fix disagree. If the world sides with
    // the old model, the fix now breaks a job and is dropped. Each fix is cross-checked once.
    const cross_checked = new Set();
    const cross_check_fix = async fix => {
      if (cross_checked.has(fix.description) || record.questions_to_world >= question_budget) return false;
      cross_checked.add(fix.description);
      const job_situations = new Set(jobs.map(j => JSON.stringify(j.situation)));
      const d = C.decide(best, fix.model, jobs, { max_found: 25, limit: 1500, watch: 'shared' });
      for (const found of d.found) {
        if (job_situations.has(JSON.stringify(found.situation))) continue;
        const new_job = job_from_deciding_test(world_model, found, record.questions_to_world + 1);
        if (!new_job) continue;
        const before = jobs.length;
        jobs = add_job(jobs, new_job);
        if (jobs.length === before) continue;
        const sides_with_fix = C.check(fix.model, jobs.slice(-1)).passed.length > 0;
        const sides_with_old = C.check(best, jobs.slice(-1)).passed.length > 0;
        record.questions_to_world++;
        record.added_jobs.push({ job: new_job, why: `cross-check the fix: ${fix.description}`, sides_with_fix, sides_with_old });
        record.rounds.push({ step: 'cross-check a fix with the world', what: fix.description, world_sides_with: sides_with_fix ? 'the fix' : sides_with_old ? 'the model before the fix' : 'neither', seen: summary_line(best, jobs) });
        return true;
      }
      return false;
    };
    while (true) {
      // 3a. SMALL FIX: the checker tries every one-step change and applies the best one.
      const failing = C.check(best, jobs).failed;
      if (failing.length && guesser_first && guesser_rewrites < 3 && !rewrite_asked_for.has(failing.slice().sort().join('|'))) {
        rewrite_asked_for.add(failing.slice().sort().join('|'));
        guesser_rewrites++;
        const ask = `${task_words()}\n\nThe current model:\n${JSON.stringify(C.model_to_form(best))}\n\nThe checker ran it.\n\n${C.report_check(best, jobs).text}\n\n${C.report_tweaks(best, jobs).text}\n\nWrite the whole model again so that every job passes. Keep every rule that already works. Give every thing a start state.`;
        const candidate_raw = read_reply(await ask_guesser([{ role: 'system', content: GUIDE }, { role: 'user', content: ask }], log, options)); record.guesser_calls++;
        const candidate = candidate_raw ? C.prepare_model(candidate_raw) : null;
        const f = candidate ? C.check_fix(best, candidate, jobs, { decide: false }) : { verdict: 'unreadable' };
        if (f.verdict === 'accepted') best = candidate;
        record.rounds.push({ step: 'guesser rewrites first', verdict: f.verdict, repaired: f.repaired, lost: f.lost, seen: summary_line(best, jobs) });
        save_progress();
        continue;
      }
      if (failing.length) {
        const t = C.tweaks(best, jobs, { max: 12 });
        if (t.helpful.length && small_fixes < 12) {
          const top = t.helpful.filter(h => h.repaired.length === t.helpful[0].repaired.length);
          // When several small fixes work equally, ask the world to choose (full loop only).
          if (may_ask_world && top.length > 1 && record.questions_to_world < question_budget) {
            let asked = false;
            for (const other of top.slice(1, 12)) {
              const d = C.decide(top[0].model, other.model, jobs, { max_found: 1, limit: 800, watch: 'shared' });
              if (!d.found.length) continue;
              const new_job = job_from_deciding_test(world_model, d.found[0], record.questions_to_world + 1);
              if (!new_job) continue;
              const before = jobs.length;
              jobs = add_job(jobs, new_job);
              if (jobs.length === before) continue;
              record.questions_to_world++;
              record.added_jobs.push({ job: new_job, why: `choose between small fixes: ${top[0].description} / ${other.description}` });
              record.rounds.push({ step: 'ask world to choose', job: new_job.name, seen: summary_line(best, jobs) });
              asked = true;
              break;
            }
            if (asked) { save_progress(); continue; }
          }
          if (may_ask_world && await cross_check_fix(top[0])) { save_progress(); continue; }
          best = top[0].model;
          small_fixes++;
          record.rounds.push({ step: 'small fix', what: top[0].description, repaired: top[0].repaired, seen: summary_line(best, jobs) });
          save_progress();
          continue;
        }
        // 3b. NEW PART: no small fix works, so ask the guesser for what is missing.
        // 3c. When the guesser's tries are used up, the checker searches for one new rule (marked fitted).
        if (new_part_calls >= (options.new_part_calls ?? 3)) {
          const n = C.new_rule_search(best, jobs, { max: 6 });
          if (!n.helpful.length || rule_searches >= 6) break;
          const top = n.helpful.filter(h => h.repaired.length === n.helpful[0].repaired.length);
          if (may_ask_world && top.length > 1 && record.questions_to_world < question_budget) {
            let asked = false;
            for (const other of top.slice(1, 12)) {
              const d = C.decide(top[0].model, other.model, jobs, { max_found: 1, limit: 800, watch: 'shared' });
              if (!d.found.length) continue;
              const new_job = job_from_deciding_test(world_model, d.found[0], record.questions_to_world + 1);
              if (!new_job) continue;
              const before = jobs.length;
              jobs = add_job(jobs, new_job);
              if (jobs.length === before) continue;
              record.questions_to_world++;
              record.added_jobs.push({ job: new_job, why: `choose between new rules: ${top[0].description} / ${other.description}` });
              record.rounds.push({ step: 'ask world to choose', job: new_job.name, seen: summary_line(best, jobs) });
              asked = true;
              break;
            }
            if (asked) { save_progress(); continue; }
          }
          if (may_ask_world && await cross_check_fix(top[0])) { save_progress(); continue; }
          best = top[0].model;
          rule_searches++;
          record.rounds.push({ step: 'checker new rule', what: top[0].description, repaired: top[0].repaired, seen: summary_line(best, jobs) });
          save_progress();
          continue;
        }
        new_part_calls++;
        const failed_results = C.check(best, jobs).results.filter(r => !r.passed);
        const target = failed_results[0];
        const why = C.explain_failure(best, target).map(l => `- ${l}`).join('\n');
        const problems_now = best.problems.length ? `\nProblems the checker found in the model:\n${best.problems.map(p => `- ${p}`).join('\n')}\n` : '';
        const earlier = tried_before.length ? `\nThese new parts were tried already and changed nothing, so write something different:\n${tried_before.map(t => `- ${t}`).join('\n')}\n` : '';
        const ask = `${task_words()}\n\nThe current model has these things: ${things_in_words(best)}.\nIts rules:\n${rules_in_words(best)}\n${problems_now}\nThis job fails:\n${job_in_words(jobs.find(j => j.name === target.job))}\nWhat the checker saw:\n${why}\n${earlier}\nNo small change to the existing rules makes this job pass, so something is missing. Write only the new parts: new rules, and new things (with their states and start) whenever you need to keep track of something the task does not show directly.`;
        const retry_options = Object.assign({}, options, { temperature: new_part_calls === 1 ? 0.2 : 0.8, seed: (options.seed || 1) * 100 + new_part_calls });
        const reply = read_reply(await ask_guesser([{ role: 'system', content: GUIDE }, { role: 'user', content: ask }], log, retry_options, NEW_PART_SHAPE));
        if (reply) tried_before.push((Array.isArray(reply.new_rules) ? reply.new_rules : []).map(r => `"${[].concat(r.when || []).join(' and ')}" -> "${r.then}"`).join('; ').slice(0, 300) || '(no rules)');
        record.guesser_calls++;
        if (!reply) { record.rounds.push({ step: 'new part', verdict: 'unreadable' }); continue; }
        let candidate = add_new_parts(best, reply);
        let f = C.check_fix(best, candidate, jobs, { decide: false });
        let cleared_out = [];
        if (f.verdict !== 'accepted') {
          const cleared = clear_out_clashing_rules(candidate, jobs);
          if (cleared.removed.length) {
            const g = C.check_fix(best, cleared.model, jobs, { decide: false });
            if (g.verdict === 'accepted' || g.lost.length < f.lost.length) { candidate = cleared.model; f = g; cleared_out = cleared.removed; }
          }
        }
        let tuned = 0;
        // The new part may be nearly right: let the checker tune it with small fixes, keeping the no-backsliding rule.
        while (f.verdict !== 'accepted' && tuned < 3) {
          const t = C.tweaks(candidate, jobs, { max: 1 });
          if (!t.helpful.length) break;
          candidate = t.helpful[0].model; tuned++;
          f = C.check_fix(best, candidate, jobs, { decide: false });
        }
        // A new thing that repairs nothing yet but breaks nothing is kept, so later fixes can use it.
        const keep = f.verdict === 'accepted' || (f.verdict === 'no change' && (f.added_things.length || f.added_states.length) && candidate.problems.length <= best.problems.length);
        record.rounds.push({ step: 'new part', verdict: f.verdict, kept: keep, kind: f.kind, added_rules: f.added_rules, added_things: f.added_things, repaired: f.repaired, lost: f.lost, tuned_by_checker: tuned, old_rules_cleared_out: cleared_out, seen: summary_line(keep ? candidate : best, jobs) });
        if (keep) best = candidate;
        save_progress();
        continue;
      }
      // 4. ASK: every job passes; look for loose rules and let the world answer deciding tests.
      if (!may_ask_world || record.questions_to_world >= question_budget) break;
      let added = 0;
      if (ask_rounds < (options.ask_rounds || 2)) {
      ask_rounds++;
      const v = C.vary(best, jobs, { per_rule: 2, limit: 800, watch: 'shared' });
      for (const d of v.deciding_tests) {
        if (!d.found || added >= 3 || record.questions_to_world >= question_budget) continue;
        const new_job = job_from_deciding_test(world_model, d.found, record.questions_to_world + 1);
        if (!new_job) continue;
        const before = jobs.length;
        jobs = add_job(jobs, new_job);
        if (jobs.length === before) continue;
        record.questions_to_world++;
        record.added_jobs.push({ job: new_job, why: `loose rule "${d.rule}": ${d.variant}` });
        added++;
      }
      record.rounds.push({ step: 'ask world about loose rules', added, seen: summary_line(best, jobs) });
      save_progress();
      if (added) continue;
      }
      // 4b. LOOK FOR SURPRISES (log 17): no rival rule is in sight, but the model still makes predictions
      // no job has tested. Ask the world about situations one change from the jobs in which the model
      // takes a route (a set of rules that fire) that no job takes. A wrong prediction there is a surprise.
      if (options.look_for_surprises === false || surprise_rounds >= (options.surprise_rounds || 2)) break;
      surprise_rounds++;
      for (const probe of surprise_probes(best, jobs, options.surprises_per_round || 4)) {
        if (record.questions_to_world >= question_budget) break;
        const new_job = job_from_deciding_test(world_model, probe, record.questions_to_world + 1);
        if (!new_job) continue;
        const before = jobs.length;
        jobs = add_job(jobs, new_job);
        if (jobs.length === before) continue;
        const surprise = !C.check(best, jobs.slice(-1)).passed.length;
        record.questions_to_world++;
        record.added_jobs.push({ job: new_job, why: `look for surprises: ${C.describe_situation(probe)}`, surprise });
        added++;
      }
      record.rounds.push({ step: 'look for surprises', added, surprises: record.added_jobs.filter(a => a.surprise).length, seen: summary_line(best, jobs) });
      save_progress();
      if (!added) break;
    }
  }

  // 5. END: jobs held back from the start
  const final_seen = C.check(best, jobs);
  const final_held = C.check(best, held_back);
  const original_seen = C.prepare_jobs({ jobs: world.jobs.filter(j => !j.held_back) }).jobs;
  record.final = { original_seen_passed: C.check(best, original_seen).passed.length, original_seen_total: original_seen.length,
    all_seen_passed: final_seen.passed.length, all_seen_total: jobs.length,
    held_back_passed: final_held.passed.length, held_back_total: held_back.length, held_back_failed: final_held.failed, problems: best.problems,
    // Held-back jobs whose situation the loop asked the world about: these were no longer unseen at the end.
    held_back_asked: held_back.filter(h => jobs.some(j => /^world answer/.test(j.name) && JSON.stringify(j.situation) === JSON.stringify(h.situation))).map(h => h.name) };
  record.model = C.model_to_form(best);
  record.log = log;
  return record;
}

const WAYS_OF_RUNNING = ['one guess', 'rewrite', 'guess and fix', 'full loop'];

module.exports = { run_task, first_guess, GUIDE, job_in_words, vocabulary_in_words, world_answers, add_new_parts, clear_out_clashing_rules, owner_word_list, read_reply, WAYS_OF_RUNNING };

if (require.main === module) {
  // node "09 loop.js" WORLD SEED OUTFILE : one shared guess from the small AI, then the four ways of running
  const worlds = require('./03 test worlds.js');
  const [which, seed, out] = process.argv.slice(2);
  const world = worlds.find(w => w.id === which);
  const options = { seed: Number(seed) || 1, progress: out + '.progress' };
  (async () => {
    const guess = await first_guess(world, options);
    const results = {};
    for (const mode of (process.env.MODES || WAYS_OF_RUNNING.join(',')).split(',')) {
      results[mode] = await run_task(world, mode, options, guess);
      fs.writeFileSync(out, JSON.stringify({ world: which, seed: options.seed, results }, null, 1));
      const f = results[mode].final;
      console.log(`${which} seed ${options.seed} | ${mode.padEnd(13)} | shown jobs ${f.original_seen_passed}/${f.original_seen_total} | held-back ${f.held_back_passed}/${f.held_back_total} | questions ${results[mode].questions_to_world} | guesser asked ${results[mode].guesser_calls}`);
    }
  })();
}
