/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Adds cause and effect to the checker ("03 checker.js"). The checker already runs a rule model
 * and can hold a thing in one state whatever its rules say ("force"). This file uses that to ask
 * cause-and-effect questions of a model:
 *
 *   what_if           - hold one thing at a level, run the model, and compare with the usual run:
 *                       did the thing we care about go up, go down, or stay the same? Also gives the
 *                       route: the chain of rules that carried the change from one to the other.
 *   seeing_and_doing  - the difference between seeing and making. Seeing: among all the usual ways
 *                       the model can start, pick the runs where a thing ends in some state, and look
 *                       at what else is true in them. Making: hold that thing in that state and look
 *                       again. "The room is dark" tells you the lamp is off (seeing), but darkening
 *                       the room does not switch the lamp off (making).
 *   why               - why did a thing end the way it did in one situation? Take away each thing
 *                       that made the situation different from the usual start, one at a time, and
 *                       see whether the ending changes ("but for this, would it have happened?").
 *                       When no single one matters but a pair does, say so: two causes, each enough.
 *   answer_what_if_question - answers a corpus question of the form "suppose more X happens, how will
 *                       it affect less Y?" with more / less / no effect, from a reading that names which
 *                       thing to hold at which level and which thing the question asks about.
 *
 * A model can also give "influences" as a shorthand: {"from": "rain", "to": "runoff", "sign": "same"}
 * means more rain makes more runoff and less rain makes less; "opposite" means more makes less.
 * Things named in influences get three levels: "usual", "more", "less", and start at "usual".
 * add_influences turns them into ordinary rules, so the checker runs them like any other rule.
 *
 * Where the ideas come from: "Claude Fable Semantics - standalone theory", revision 1. Part II: a
 * causal link is a pattern of response to changes (it moves when a part is changed, stays put when
 * only looked at). Part V: an Account answers a "why" question by what would change under the
 * changes it is meant to cover. What this file takes for granted about cause is listed in
 * "28 What the causal checker presupposes.md".
 *
 * Runs in Node. No outside libraries.
 */
'use strict';
const checker = require('./03 checker.js');

const LEVELS = ['usual', 'more', 'less'];
const copy = value => JSON.parse(JSON.stringify(value));
const unique = list => [...new Set(list)];
const lower = text => String(text == null ? '' : text).trim().replace(/\s+/g, ' ').toLowerCase();

// ------------------------------------------------------------------
// The "influences" shorthand, turned into ordinary rules
// ------------------------------------------------------------------
function add_influences(raw_model) {
  const form = copy(raw_model);
  form.things = Object.assign({}, form.things || {});
  form.start = Object.assign({}, form.start || {});
  form.rules = (form.rules || []).slice();
  const influences = form.influences || [];
  delete form.influences;
  const problems = [];
  const leveled = new Set();
  for (const influence of influences) {
    for (const name of [influence.from, influence.to]) {
      if (!name) { problems.push('An influence is missing "from" or "to".'); continue; }
      if (!form.things[name]) { form.things[name] = LEVELS.slice(); leveled.add(name); }
      if (form.start[name] == null && form.things[name].includes('usual')) form.start[name] = 'usual';
    }
  }
  const missing_levels = unique(influences.flatMap(i => [i.from, i.to]).filter(Boolean))
    .filter(name => !LEVELS.every(level => form.things[name].includes(level)));
  for (const name of missing_levels) problems.push(`"${name}" is used in an influence, so it needs the states "usual", "more" and "less"; it has ${form.things[name].map(s => `"${s}"`).join(', ')}.`);
  influences.forEach((influence, index) => {
    if (!influence.from || !influence.to || missing_levels.includes(influence.from) || missing_levels.includes(influence.to)) return;
    const sign = lower(influence.sign || 'same');
    if (sign !== 'same' && sign !== 'opposite') { problems.push(`Influence ${index + 1}: "sign" must be "same" or "opposite", not "${influence.sign}".`); return; }
    const up = sign === 'same' ? 'more' : 'less';
    const down = sign === 'same' ? 'less' : 'more';
    const label = `${influence.from} ${sign === 'same' ? 'raises' : 'lowers'} ${influence.to}`;
    form.rules.push({ name: `${label} (more)`, when: [`${influence.from} is more`], then: `${influence.to} is ${up}` });
    form.rules.push({ name: `${label} (less)`, when: [`${influence.from} is less`], then: `${influence.to} is ${down}` });
  });
  return { form, problems };
}

function prepare(raw_model) {
  const { form, problems } = add_influences(raw_model);
  const model = checker.prepare_model(form);
  model.problems = problems.concat(model.problems);
  return model;
}

// ------------------------------------------------------------------
// Running with things held, and reading how a thing ended
// ------------------------------------------------------------------
function run_with(model, situation) {
  const problems = [];
  // Events may be given as a list in order (as in jobs) or already by step.
  const events = Array.isArray(situation.events) ? checker.prepare_jobs([{ events: situation.events }]).jobs[0].situation.events : situation.events || {};
  const resolved = checker.resolve_situation(model, {
    start: situation.start || {}, events, force: situation.force || {}, remove: situation.remove || [],
  }, problems, 'Situation');
  if (problems.length) return { problems };
  return { result: checker.run(model, resolved), resolved };
}
function ending(result, thing) {
  const states = unique(result.final_states.map(s => s[thing]));
  return states.length === 1 ? states[0] : null; // null: the model keeps switching (a cycle)
}

// The chain of rules that holds a thing where it ended, traced backwards. At the end of a settled run,
// the rules that fire and give the thing its final state are its support; then the support of the things
// those rules read, and so on back to what was held or started. A state set by an event (which is over
// by the end) is traced through the change the event made.
function route_to(result, thing, rules) {
  const final = result.history[result.end_step];
  const fires_on = (rule, state) => rule.when.every(c => c.kind === 'state' && (c.negated ? state[c.thing] !== c.state : state[c.thing] === c.state));
  const route = [];
  const visited = new Set();
  const queue = [thing];
  while (queue.length) {
    const name = queue.shift();
    if (visited.has(name)) continue;
    visited.add(name);
    let support = rules.filter(r => fires_on(r, final) && r.then.some(s => s.thing === name && s.state === final[name]));
    let step = null;
    if (!support.length) {
      const change = result.changes.filter(c => c.thing === name && c.to === final[name]).pop();
      if (!change) continue;
      support = rules.filter(r => change.rules.includes(r.name));
      step = change.step;
    }
    for (const rule of support) {
      route.push({ rule: rule.name, thing: name, to: final[name], step });
      for (const condition of rule.when) if (condition.kind === 'state') queue.push(condition.thing);
    }
  }
  return route.reverse();
}
// Every thing whose state can reach this one through the rules.
function upstream_of(model, thing) {
  const found = new Set();
  const queue = [thing];
  while (queue.length) {
    const name = queue.shift();
    for (const rule of model.rules) {
      if (!rule.then.some(s => s.thing === name)) continue;
      for (const c of rule.when) if (c.kind === 'state' && !found.has(c.thing)) { found.add(c.thing); queue.push(c.thing); }
    }
  }
  return found;
}
function find_thing_name(model, name) { return Object.keys(model.things).find(t => lower(t) === lower(name)) || null; }

// ------------------------------------------------------------------
// What if: hold one thing, compare with the usual run
// ------------------------------------------------------------------
function what_if(model, change, target, base = {}) {
  if (model.problems && model.problems.length) return { verdict: 'unreadable', problems: model.problems };
  const usual = run_with(model, base);
  const held = run_with(model, Object.assign({}, base, { force: Object.assign({}, base.force || {}, change) }));
  const problems = [].concat(usual.problems || [], held.problems || []);
  const target_thing = find_thing_name(model, target);
  if (!target_thing) problems.push(`The model has no thing "${target}".`);
  if (problems.length) return { verdict: 'unreadable', problems };
  const before = ending(usual.result, target_thing);
  const after = ending(held.result, target_thing);
  // Two rules pushing the thing, or anything upstream of it, to different states: without sizes the
  // model cannot say which push wins, so the answer is unsettled whatever state the run stopped in.
  const reaches = upstream_of(model, target_thing).add(target_thing);
  const clashes = held.result.clashes.filter(c => reaches.has(c.thing));
  const verdict = after == null || before == null ? 'keeps switching'
    : clashes.length ? 'unsettled'
    : after === before ? 'no change' : 'changed';
  return { verdict, thing: target_thing, before, after, route: verdict === 'changed' ? route_to(held.result, target_thing, model.rules) : [], clashes };
}

// ------------------------------------------------------------------
// Seeing and doing
// ------------------------------------------------------------------
// Things no rule ever sets: the ones only the outside can change. Their combinations are the
// usual ways the model can start ("admitted starts"), up to a limit.
function outside_things(model) {
  const set_by_rules = new Set(model.rules.flatMap(r => r.then.map(s => s.thing)));
  return Object.keys(model.things).filter(t => !set_by_rules.has(t));
}
function admitted_starts(model, limit = 512) {
  let starts = [{}];
  for (const thing of outside_things(model)) {
    const next = [];
    for (const start of starts) for (const state of model.things[thing]) next.push(Object.assign({}, start, { [thing]: state }));
    starts = next;
    if (starts.length > limit) return { starts: starts.slice(0, limit), cut: true };
  }
  return { starts, cut: false };
}
function seeing_and_doing(model, thing, state, other) {
  const { starts, cut } = admitted_starts(model);
  const seen = [], made = [];
  for (const start of starts) {
    const plain = run_with(model, { start });
    if (plain.problems) return { problems: plain.problems };
    if (ending(plain.result, thing) === state) seen.push(ending(plain.result, other));
    const held = run_with(model, { start, force: { [thing]: state } });
    if (held.problems) return { problems: held.problems };
    made.push(ending(held.result, other));
  }
  const tally = list => list.reduce((acc, s) => { const k = s == null ? 'keeps switching' : s; acc[k] = (acc[k] || 0) + 1; return acc; }, {});
  const seeing = tally(seen), doing = tally(made);
  const same = JSON.stringify(Object.keys(seeing).sort()) === JSON.stringify(Object.keys(doing).sort());
  return { starts: starts.length, cut, seeing, doing, differ: !same, seeing_runs: seen.length };
}

// ------------------------------------------------------------------
// Why: but-for tests on what made the situation differ from the usual start
// ------------------------------------------------------------------
function why(model, situation, target) {
  const base = run_with(model, situation);
  if (base.problems) return { problems: base.problems };
  const thing = find_thing_name(model, target);
  if (!thing) return { problems: [`The model has no thing "${target}".`] };
  const outcome = ending(base.result, thing);
  // The differences: each start or held state unlike the model's start, and each event.
  const differences = [];
  for (const [name, state] of Object.entries(base.resolved.start)) if (model.start[name] !== state) differences.push({ kind: 'start', thing: name, state });
  for (const [name, state] of Object.entries(base.resolved.force)) differences.push({ kind: 'held', thing: name, state });
  for (const [step, events] of Object.entries(base.resolved.events)) for (const event of events) differences.push({ kind: 'event', step: Number(step), event });
  const without = drop => {
    const s = { start: {}, force: {}, events: {} };
    for (const d of differences) {
      if (drop.includes(d)) continue;
      if (d.kind === 'start') s.start[d.thing] = d.state;
      if (d.kind === 'held') s.force[d.thing] = d.state;
      if (d.kind === 'event') (s.events[d.step] = s.events[d.step] || []).push(d.event);
    }
    const r = run_with(model, s);
    return ending(r.result, thing);
  };
  const but_for = differences.filter(d => without([d]) !== outcome);
  const pairs = [];
  if (!but_for.length) {
    for (let i = 0; i < differences.length; i++) for (let j = i + 1; j < differences.length; j++) {
      if (without([differences[i], differences[j]]) !== outcome) pairs.push([differences[i], differences[j]]);
    }
  }
  return {
    thing, outcome, differences, but_for, each_enough: pairs,
    route: route_to(base.result, thing, model.rules),
    verdict: but_for.length ? 'but-for causes found' : pairs.length ? 'two causes, each enough' : 'no difference made it happen',
  };
}
function describe_difference(d) {
  if (d.kind === 'event') return `"${d.event}" happening`;
  return `${d.thing} ${d.kind === 'held' ? 'held at' : 'starting as'} ${d.state}`;
}

// ------------------------------------------------------------------
// Corpus questions: "suppose more X happens, how will it affect less Y?"
// ------------------------------------------------------------------
// A reading says: change = {thing, level} to hold (or null: the change is not in the model), and
// effect = {thing, direction} (direction "more" or "less": which way the question's effect phrase
// points), or null when the effect is not in the model. The answer: "more" when the model moves the
// effect's thing the way the phrase points, "less" when the other way, "no effect" when it stays.
function answer_what_if_question(model, reading) {
  if (!reading || !reading.change || !reading.effect) return { answer: 'no_effect', because: 'not in the model' };
  const direction = lower(reading.effect.direction);
  if (direction !== 'more' && direction !== 'less') return { answer: 'unreadable', because: `the effect's direction must be "more" or "less", not "${reading.effect.direction}"` };
  const outcome = what_if(model, { [reading.change.thing]: reading.change.level }, reading.effect.thing);
  if (outcome.verdict === 'unreadable') return { answer: 'unreadable', because: outcome.problems.join(' ') };
  if (outcome.verdict === 'keeps switching' || outcome.verdict === 'unsettled') return { answer: 'unsettled', because: outcome.verdict, outcome };
  if (outcome.verdict === 'no change') return { answer: 'no_effect', because: 'the held change does not reach it', outcome };
  const moved = outcome.after === 'more' || outcome.after === 'less' ? outcome.after
    : null;
  if (!moved) return { answer: 'unreadable', because: `the effect's thing changed from "${outcome.before}" to "${outcome.after}", which is not "more" or "less"`, outcome };
  return { answer: moved === direction ? 'more' : 'less', because: `${outcome.thing} goes from ${outcome.before} to ${outcome.after}`, outcome };
}

module.exports = {
  LEVELS, add_influences, prepare, run_with, ending, what_if, outside_things, admitted_starts,
  seeing_and_doing, why, describe_difference, answer_what_if_question, route_to, upstream_of,
};
