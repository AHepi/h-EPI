/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * This is the checker. A small AI writes a "model": a list of things (each can be in a few
 * states) and rules ("when the ball is flying and the wall is standing, the ball becomes at wall").
 * The owner writes "jobs": in this situation, this thing should end up this way.
 *
 * The checker never guesses. It only runs models and reports what happens:
 *   check      - run every job, say which pass and fail, and why a failing one failed
 *   vary       - the hard-to-vary tests: remove each rule, swap each rule for a near neighbour,
 *                remove each event, look for a rule that just states the answer, look for jobs
 *                that always expect the same thing
 *   check_fix  - accept a fix only if it repairs a failing job and breaks no job that passed
 *   tweaks     - try every small change to the existing rules; if none repairs a job, say that
 *                something new is needed (a new rule or a new thing to keep track of)
 *   decide     - given two models, find a situation where they give different answers
 *
 * Where the ideas come from: "Claude Fable Semantics - standalone theory", revision 1.
 * Rules are the parts (components), things are the ports, a situation is one admitted change,
 * the jobs are the question's contract. Part numbers are noted next to each section.
 *
 * Runs in Node (require) and in a browser (window.Checker). No outside libraries.
 */
(function (root, make) {
  const api = make();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.Checker = api;
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  const STEP_LIMIT = 60;
  const copy = value => JSON.parse(JSON.stringify(value));
  const unique = list => [...new Set(list)];
  const tidy = text => String(text == null ? '' : text).trim().replace(/\s+/g, ' ');
  const lower = text => tidy(text).toLowerCase();

  // ------------------------------------------------------------------
  // Spelling help: find the closest known name, for "did you mean" hints
  // ------------------------------------------------------------------
  function letters_apart(a, b) {
    const rows = a.length + 1, cols = b.length + 1;
    const table = Array.from({ length: rows }, (_, i) => [i, ...Array(cols - 1).fill(0)]);
    for (let j = 0; j < cols; j++) table[0][j] = j;
    for (let i = 1; i < rows; i++) for (let j = 1; j < cols; j++) {
      table[i][j] = Math.min(table[i - 1][j] + 1, table[i][j - 1] + 1, table[i - 1][j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
    }
    return table[a.length][b.length];
  }
  function closest_name(word, choices) {
    const w = lower(word);
    let best = null, best_distance = Infinity;
    for (const choice of choices) {
      const c = lower(choice);
      let distance = letters_apart(w, c);
      if (c.includes(w) || w.includes(c)) distance = Math.min(distance, Math.abs(c.length - w.length) * 0.5);
      if (distance < best_distance) { best_distance = distance; best = choice; }
    }
    return best_distance <= Math.max(2, Math.floor(w.length / 3)) ? best : null;
  }
  function did_you_mean(word, choices) {
    const guess = closest_name(word, choices);
    return guess ? ` Did you mean "${guess}"?` : ` Known: ${choices.map(c => `"${c}"`).join(', ')}.`;
  }

  // ------------------------------------------------------------------
  // Reading a model (Part II: an organization is ports, components and admitted edits)
  // ------------------------------------------------------------------
  function as_list(value) {
    if (value == null) return [];
    if (Array.isArray(value)) return value;
    if (typeof value === 'string') return value.split(/\s*,\s*|\s+and\s+/i).filter(Boolean);
    return [value];
  }
  function read_things(raw_things, problems) {
    const things = {};
    if (!raw_things || typeof raw_things !== 'object') { problems.push('The model has no "things". List each thing and the states it can be in.'); return things; }
    const entries = Array.isArray(raw_things)
      ? raw_things.map(t => [t.name || t.thing, t.states])
      : Object.entries(raw_things);
    for (const [name, states] of entries) {
      const thing = tidy(name);
      const list = unique(as_list(states).map(tidy).filter(Boolean));
      if (!thing) { problems.push('A thing has no name.'); continue; }
      if (list.length < 2) problems.push(`Thing "${thing}" needs at least two states, so that a rule can change it.`);
      things[thing] = list;
    }
    return things;
  }
  function find_thing(things, name) {
    const wanted = lower(name);
    return Object.keys(things).find(t => lower(t) === wanted) || null;
  }
  function find_state(things, thing, name) {
    const wanted = lower(name);
    return (things[thing] || []).find(s => lower(s) === wanted) || null;
  }

  // A condition is "THING is STATE", "THING is not STATE" or "EVENT happens".
  function read_condition(text, model, where, problems) {
    const words = tidy(text).replace(/[.]$/, '');
    let match = words.match(/^(?:event\s+)?(.+?)\s+happens$/i) || words.match(/^event[:\s]+(.+)$/i);
    if (match) {
      const event = model.events.find(e => lower(e) === lower(match[1]));
      if (event) return { kind: 'event', event };
      problems.push(`${where}: "${match[1]}" is not a listed event.${did_you_mean(match[1], model.events)}`);
      return null;
    }
    match = words.match(/^(.+?)\s+is\s+not\s+(.+)$/i);
    let negated = true;
    if (!match) { match = words.match(/^(.+?)\s+(?:is|are)\s+(.+)$/i); negated = false; }
    if (!match) {
      const event = model.events.find(e => lower(e) === lower(words));
      if (event) return { kind: 'event', event };
      problems.push(`${where}: "${words}" should look like "THING is STATE", "THING is not STATE" or "EVENT happens".`);
      return null;
    }
    const thing = find_thing(model.things, match[1]);
    if (!thing) { problems.push(`${where}: "${match[1]}" is not a listed thing.${did_you_mean(match[1], Object.keys(model.things))}`); return null; }
    const state = find_state(model.things, thing, match[2]);
    if (!state) { problems.push(`${where}: "${match[2]}" is not a state of "${thing}".${did_you_mean(match[2], model.things[thing])}`); return null; }
    return { kind: 'state', thing, state, negated };
  }
  function read_setting(text, model, where, problems, notes) {
    const condition = read_condition(text, model, where, problems);
    if (!condition) return null;
    if (condition.kind === 'event') { problems.push(`${where}: a rule's result must be "THING is STATE"; an event cannot be a result.`); return null; }
    if (condition.negated) {
      const others = model.things[condition.thing].filter(s => s !== condition.state);
      if (others.length === 1) { notes.push(`${where}: read "${text}" as "${condition.thing} is ${others[0]}".`); return { thing: condition.thing, state: others[0] }; }
      problems.push(`${where}: a result must name the state the thing becomes. "${text}" does not say which of ${others.map(s => `"${s}"`).join(', ')} it becomes.`);
      return null;
    }
    return { thing: condition.thing, state: condition.state };
  }
  const condition_text = c => (c.kind === 'event' ? `${c.event} happens` : `${c.thing} is ${c.negated ? 'not ' : ''}${c.state}`);
  const setting_text = s => `${s.thing} is ${s.state}`;
  function rule_text(rule) {
    const when = rule.when.length ? `when ${rule.when.map(condition_text).join(' and ')}` : 'always (no conditions)';
    return `${when}, ${rule.then.map(setting_text).join(' and ')}${rule.strength === 'usually' ? ' (usually)' : ''}`;
  }

  function prepare_model(raw) {
    const problems = [], notes = [];
    if (typeof raw === 'string') { try { raw = JSON.parse(raw); } catch (e) { return { problems: [`The model is not readable JSON: ${e.message}`], notes, rules: [], things: {}, events: [], start: {} }; } }
    const model = { things: read_things(raw.things, problems), events: unique(as_list(raw.events).map(tidy).filter(Boolean)), start: {}, rules: [], problems, notes };
    const raw_start = raw.start || raw.starting || {};
    for (const [name, state] of Object.entries(raw_start)) {
      const thing = find_thing(model.things, name);
      if (!thing) { problems.push(`Start: "${name}" is not a listed thing.${did_you_mean(name, Object.keys(model.things))}`); continue; }
      const found = find_state(model.things, thing, state);
      if (!found) { problems.push(`Start: "${state}" is not a state of "${thing}".${did_you_mean(state, model.things[thing])}`); continue; }
      model.start[thing] = found;
    }
    for (const thing of Object.keys(model.things)) {
      if (!model.start[thing] && model.things[thing].length) { model.start[thing] = model.things[thing][0]; notes.push(`Start: "${thing}" had no starting state; used its first state, "${model.things[thing][0]}".`); }
    }
    const names = new Set();
    (raw.rules || []).forEach((r, index) => {
      let name = tidy(r.name || r.id || `rule ${index + 1}`);
      if (names.has(name)) { name = `${name} (${index + 1})`; notes.push(`Two rules shared a name; renamed one to "${name}".`); }
      names.add(name);
      const where = `Rule "${name}"`;
      const when = as_list(r.when != null ? r.when : r.if).map(c => read_condition(c, model, where, problems)).filter(Boolean);
      const then = as_list(r.then).map(s => read_setting(s, model, where, problems, notes)).filter(Boolean);
      if (!then.length) { problems.push(`${where} has no result. Give it "then": "THING is STATE".`); return; }
      const needs = {};
      for (const c of when) if (c.kind === 'state' && !c.negated) (needs[c.thing] = needs[c.thing] || []).push(c.state);
      for (const [thing, states] of Object.entries(needs)) {
        if (unique(states).length > 1) problems.push(`${where} can never fire: it needs ${thing} to be ${unique(states).map(x => `"${x}"`).join(' and ')} at the same time. A thing is in one state at a time; use one rule for each state.`);
      }
      for (const c of when) if (c.kind === 'state' && c.negated && (needs[c.thing] || []).includes(c.state)) problems.push(`${where} can never fire: it needs ${c.thing} to be "${c.state}" and not "${c.state}".`);
      const strength = lower(r.strength || r.how || '') === 'usually' || r.usually === true ? 'usually' : 'always';
      model.rules.push({ name, when, then, strength, made_by: r.made_by || null, reason: r.reason || r.why || null });
    });
    return model;
  }

  // ------------------------------------------------------------------
  // Reading jobs (Part III: a question is a target, a contract of admitted changes, and a query)
  // ------------------------------------------------------------------
  function read_events(raw_events) {
    const by_step = {};
    const add = (step, event) => { if (!event) return; (by_step[step] = by_step[step] || []).push(tidy(event)); };
    if (!raw_events) return by_step;
    if (Array.isArray(raw_events)) {
      raw_events.forEach((entry, index) => {
        if (entry && typeof entry === 'object' && !Array.isArray(entry)) add(Number(entry.step) || index + 1, entry.event);
        else as_list(entry).forEach(e => add(index + 1, e));
      });
    } else if (typeof raw_events === 'object') {
      for (const [step, list] of Object.entries(raw_events)) as_list(list).forEach(e => add(Number(step), e));
    } else as_list(raw_events).forEach((e, i) => add(i + 1, e));
    return by_step;
  }
  function prepare_jobs(raw) {
    if (typeof raw === 'string') raw = JSON.parse(raw);
    const list = Array.isArray(raw) ? raw : raw.jobs || [];
    return {
      question: raw.question || '',
      jobs: list.map((j, index) => ({
        name: tidy(j.name || j.job || `job ${index + 1}`),
        situation: { start: j.start || {}, events: read_events(j.events), force: j.force || {}, remove: as_list(j.remove) },
        expect: as_list(j.expect),
        at: j.at == null ? 'end' : j.at,
        from: j.from || 'given',
        held_back: !!j.held_back,
      })),
    };
  }
  // Resolve a job's words against one model's vocabulary.
  function resolve_situation(model, situation, problems, where) {
    const out = { start: {}, events: {}, force: {}, remove: [] };
    for (const [name, state] of Object.entries(situation.start || {})) {
      const thing = find_thing(model.things, name);
      const found = thing && find_state(model.things, thing, state);
      if (!found) { problems.push(`${where}: the model cannot start "${name}" as "${state}".${thing ? did_you_mean(state, model.things[thing]) : did_you_mean(name, Object.keys(model.things))}`); continue; }
      out.start[thing] = found;
    }
    for (const [name, state] of Object.entries(situation.force || {})) {
      const thing = find_thing(model.things, name);
      const found = thing && find_state(model.things, thing, state);
      if (!found) { problems.push(`${where}: the model cannot hold "${name}" at "${state}".`); continue; }
      out.force[thing] = found;
    }
    for (const [step, events] of Object.entries(situation.events || {})) {
      for (const e of events) {
        const event = model.events.find(x => lower(x) === lower(e));
        if (!event) { problems.push(`${where}: the model has no event "${e}".${did_you_mean(e, model.events)}`); continue; }
        (out.events[step] = out.events[step] || []).push(event);
      }
    }
    out.remove = (situation.remove || []).map(n => model.rules.find(r => lower(r.name) === lower(n))).filter(Boolean).map(r => r.name);
    return out;
  }

  // ------------------------------------------------------------------
  // Running a model through one situation (Part II equation O, stepped through time)
  // ------------------------------------------------------------------
  function holds(condition, state, events_now) {
    if (condition.kind === 'event') return events_now.includes(condition.event);
    const is_in = state[condition.thing] === condition.state;
    return condition.negated ? !is_in : is_in;
  }
  const same_state = (a, b) => Object.keys(a).every(k => a[k] === b[k]);
  const conditions_key = rule => rule.when.map(condition_text).sort();
  function more_specific(a, b) { // true when rule a's conditions include all of b's and more
    const ka = conditions_key(a), kb = conditions_key(b);
    return ka.length > kb.length && kb.every(k => ka.includes(k));
  }

  // Events happen in order. Before the first event, and after each event, the model runs on its own
  // until nothing changes (it settles) or it keeps repeating (a cycle). Then the next event happens.
  // Rules read the state before a step and change it all at once for the next step.
  function one_step(rules, before, events_now, situation, step, changes, clashes) {
    const proposals = {};
    for (const rule of rules) {
      if (!rule.when.every(c => holds(c, before, events_now))) continue;
      for (const setting of rule.then) {
        if (situation.force && situation.force[setting.thing] != null) continue; // a held thing ignores its rules
        (proposals[setting.thing] = proposals[setting.thing] || []).push({ rule, state: setting.state });
      }
    }
    const next = Object.assign({}, before);
    for (const [thing, offered] of Object.entries(proposals)) {
      let left = offered;
      if (unique(left.map(p => p.state)).length > 1 && left.some(p => p.rule.strength === 'always')) left = left.filter(p => p.rule.strength === 'always');
      if (unique(left.map(p => p.state)).length > 1) left = left.filter(p => !left.some(q => q.state !== p.state && more_specific(q.rule, p.rule)));
      const states = unique(left.map(p => p.state));
      if (states.length > 1) {
        clashes.push({ step, thing, offers: left.map(p => ({ rule: p.rule.name, state: p.state, strength: p.rule.strength })), firm: left.every(p => p.rule.strength === 'always') });
        continue; // unsettled: the thing keeps its state
      }
      if (states[0] !== before[thing]) {
        next[thing] = states[0];
        changes.push({ step, thing, from: before[thing], to: states[0], rules: unique(left.map(p => p.rule.name)) });
      }
    }
    return next;
  }

  function run(model, situation) {
    const removed = new Set(situation.remove || []);
    const rules = model.rules.filter(r => !removed.has(r.name));
    const first = Object.assign({}, model.start, situation.start || {}, situation.force || {});
    const history = [first];
    const events_at = {};
    const changes = [], clashes = [], cycles = [];
    const groups = Object.entries(situation.events || {})
      .filter(([, list]) => list && list.length)
      .sort((a, b) => Number(a[0]) - Number(b[0]))
      .map(([, list]) => list);
    let ending = 'settled', cycle_from = null;
    const settle = () => {
      const phase_start = history.length - 1;
      for (let n = 0; n < STEP_LIMIT; n++) {
        const step = history.length;
        const before = history[step - 1];
        const next = one_step(rules, before, [], situation, step, changes, clashes);
        if (same_state(next, before)) return { ending: 'settled' };
        history.push(next);
        const earlier = history.findIndex((h, i) => i >= phase_start && i < history.length - 1 && same_state(h, next));
        if (earlier >= 0) return { ending: 'cycle', from: earlier };
      }
      return { ending: 'limit' };
    };
    let outcome = settle();
    for (const events_now of groups) {
      if (outcome.ending === 'cycle') cycles.push(outcome.from);
      const step = history.length;
      events_at[step] = events_now.slice();
      history.push(one_step(rules, history[step - 1], events_now, situation, step, changes, clashes));
      outcome = settle();
    }
    ending = outcome.ending;
    const end_step = history.length - 1;
    if (ending === 'cycle') cycle_from = outcome.from;
    const final_states = ending === 'cycle' ? history.slice(cycle_from, end_step + 1) : [history[end_step]];
    return { history, changes, clashes, ending, end_step, final_states, events_at, cycles };
  }

  // What a thing ends as: one state, or several if the model keeps switching.
  function ending_of(result, thing) { return unique(result.final_states.map(s => s[thing])); }

  // ------------------------------------------------------------------
  // Checking jobs (Part V condition A: the answer to the question asked, held fixed)
  // ------------------------------------------------------------------
  function read_expectations(model, job, problems) {
    return job.expect.map(text => read_condition(text, model, `Job "${job.name}"`, problems)).filter(c => c && c.kind === 'state');
  }
  function expectation_met(result, condition, at) {
    const is_in = s => s[condition.thing] === condition.state;
    const test = s => (condition.negated ? !is_in(s) : is_in(s));
    const all_states = result.history.slice(0, result.end_step + 1);
    if (at === 'ever') return all_states.some(test);
    if (at === 'never') return !all_states.some(test);
    if (typeof at === 'number' || /^\d+$/.test(String(at))) {
      const n = Number(at);
      return n <= result.end_step ? test(result.history[n]) : result.final_states.every(test);
    }
    return result.final_states.every(test);
  }

  function check_job(model, job) {
    const problems = [];
    const situation = resolve_situation(model, job.situation, problems, `Job "${job.name}"`);
    const expectations = read_expectations(model, job, problems);
    if (problems.length) return { job: job.name, verdict: 'unreadable', problems, passed: false };
    const result = run(model, situation);
    const asked = unique(expectations.map(c => c.thing));
    const touching_clashes = result.clashes.filter(c => asked.includes(c.thing));
    const met = expectations.map(c => expectation_met(result, c, job.at));
    let verdict = met.every(Boolean) ? 'pass' : 'fail';
    if (touching_clashes.length) verdict = touching_clashes.some(c => c.firm) ? 'contradiction' : 'unsettled';
    const got = asked.map(thing => ({ thing, states: ending_of(result, thing) }));
    return { job: job.name, verdict, passed: verdict === 'pass', expectations, met, got, result, situation, clashes: touching_clashes, at: job.at, from: job.from, held_back: job.held_back };
  }

  function check(model, jobs_list) {
    const results = jobs_list.map(job => check_job(model, job));
    return { results, passed: results.filter(r => r.passed).map(r => r.job), failed: results.filter(r => !r.passed).map(r => r.job) };
  }

  // Why did a job fail? Look for the rules that could have produced the expected state
  // and say what stopped them (Part IX: a criticism must bear on its target).
  function explain_failure(model, check_result) {
    const lines = [];
    const r = check_result;
    if (r.verdict === 'unreadable') return r.problems;
    const route = r.result.changes.map(c => `step ${c.step}: ${c.rules.join(' + ')} made ${c.thing} ${c.to}`);
    lines.push(route.length ? `What happened: ${route.join('; ')}.` : 'What happened: no rule changed anything.');
    if (r.result.ending === 'cycle') lines.push(`The model never settles: it keeps switching (${r.got.map(g => `${g.thing}: ${g.states.join(' / ')}`).join('; ')}).`);
    if (r.result.ending === 'limit') lines.push(`The model was still changing after ${STEP_LIMIT} steps.`);
    for (const clash of r.clashes) {
      lines.push(`At step ${clash.step} rules disagree about ${clash.thing}: ${clash.offers.map(o => `"${o.rule}" says ${o.state}`).join(', ')}. ${clash.firm ? 'Both are firm rules, so the model contradicts itself.' : 'Neither gives way, so it is unsettled.'} Add a condition to each of these rules that tells their situations apart.`);
    }
    r.expectations.forEach((c, i) => {
      if (r.met[i]) return;
      const ended = ending_of(r.result, c.thing).join(' / ');
      const at_words = r.at === 'end' ? 'at the end' : r.at === 'ever' ? 'at some point' : r.at === 'never' ? 'never' : `at step ${r.at}`;
      lines.push(`Wanted ${condition_text(c)} ${at_words}; got ${c.thing} ${ended}.`);
      if (r.situation.force[c.thing]) { lines.push(`This job holds ${c.thing} fixed, so no rule can change it.`); return; }
      if (c.negated) {
        const culprits = r.result.changes.filter(x => x.thing === c.thing && x.to === c.state);
        culprits.forEach(x => lines.push(`At step ${x.step}, rule "${x.rules.join('" + "')}" made ${c.thing} ${c.state}.`));
        if (!culprits.length) lines.push(`${c.thing} was ${c.state} from the start and nothing changed it.`);
        return;
      }
      const makers = model.rules.filter(rule => rule.then.some(s => s.thing === c.thing && s.state === c.state));
      if (!makers.length) { lines.push(`No rule in the model can make ${c.thing} ${c.state}.`); return; }
      for (const maker of makers) {
        const made = r.result.changes.filter(x => x.rules.includes(maker.name) && x.thing === c.thing);
        if (made.length) {
          const later = r.result.changes.filter(x => x.thing === c.thing && x.step > made[made.length - 1].step);
          if (later.length) lines.push(`Rule "${maker.name}" made ${c.thing} ${c.state} at step ${made[0].step}, then at step ${later[0].step} rule "${later[0].rules.join('" + "')}" changed it to ${later[0].to}.`);
          continue;
        }
        if ((r.situation.remove || []).includes(maker.name)) { lines.push(`Rule "${maker.name}" is switched off in this job.`); continue; }
        const clashed = r.result.clashes.filter(x => x.offers.some(o => o.rule === maker.name));
        if (clashed.length) { lines.push(`Rule "${maker.name}" fired at step ${clashed[0].step} but was blocked by a disagreement (see above).`); continue; }
        const steps = r.result.history.slice(0, r.result.end_step + 1);
        const events_at = s => (r.result.events_at[s + 1] || []);
        const never = maker.when.filter(cond => !steps.some((st, s) => holds(cond, st, events_at(s))));
        if (never.length) lines.push(`Rule "${maker.name}" never fired: ${never.map(cond => `"${condition_text(cond)}" was never true`).join(', and ')}.`);
        else if (maker.when.length) lines.push(`Rule "${maker.name}" never fired: each of its conditions was true at some step, but never all at the same step.`);
      }
    });
    return lines;
  }

  // ------------------------------------------------------------------
  // Near neighbours of a rule, for the swap test (hard-to-vary; Part VI "Hard-to-vary")
  // ------------------------------------------------------------------
  function with_rule(model, index, rule) { const m = Object.assign({}, model, { rules: model.rules.slice() }); m.rules[index] = rule; return m; }
  function without_rules(model, names) { return Object.assign({}, model, { rules: model.rules.filter(r => !names.includes(r.name)) }); }

  function neighbours(model, index) {
    const rule = model.rules[index];
    const out = [];
    const add = (description, kind, changed) => out.push({ description, kind, rule_name: rule.name, rule: Object.assign({}, rule, changed), model: with_rule(model, index, Object.assign({}, rule, changed)) });
    rule.then.forEach((setting, i) => {
      for (const other of model.things[setting.thing]) {
        if (other === setting.state) continue;
        const then = rule.then.slice(); then[i] = { thing: setting.thing, state: other };
        add(`result "${setting_text(setting)}" changed to "${setting.thing} is ${other}"`, 'result', { then });
      }
    });
    const by_thing = {};
    rule.when.forEach(c => { if (c.kind === 'state' && !c.negated) (by_thing[c.thing] = by_thing[c.thing] || []).push(c); });
    for (const [thing, list] of Object.entries(by_thing)) {
      if (list.length < 2) continue;
      for (const keep of list) {
        const when = rule.when.filter(c => !(c.kind === 'state' && !c.negated && c.thing === thing) || c === keep);
        add(`only "${condition_text(keep)}" kept of the conditions on ${thing}`, 'unclash', { when });
      }
    }
    rule.when.forEach((cond, i) => {
      const when = rule.when.filter((_, j) => j !== i);
      add(`condition "${condition_text(cond)}" left out`, 'drop', { when });
      if (cond.kind === 'state') {
        add(`condition "${condition_text(cond)}" turned into "${condition_text(Object.assign({}, cond, { negated: !cond.negated }))}"`, 'flip', { when: rule.when.map((c, j) => (j === i ? Object.assign({}, c, { negated: !c.negated }) : c)) });
        for (const other of model.things[cond.thing]) {
          if (other === cond.state) continue;
          const changed = Object.assign({}, cond, { state: other });
          add(`condition "${condition_text(cond)}" changed to "${condition_text(changed)}"`, 'condition', { when: rule.when.map((c, j) => (j === i ? changed : c)) });
        }
      } else {
        for (const other of model.events) {
          if (other === cond.event) continue;
          add(`condition "${condition_text(cond)}" changed to "${other} happens"`, 'condition', { when: rule.when.map((c, j) => (j === i ? { kind: 'event', event: other } : c)) });
        }
      }
      // Swap the condition for one on a different thing the rule does not look at yet (log 17:
      // "Mara lights the lamp" had to become "the lamp is dark", which no other one-step change reaches).
      const used = new Set(rule.when.filter(c => c.kind === 'state').map(c => c.thing));
      for (const [thing, states] of Object.entries(model.things)) {
        if (used.has(thing) || rule.then.some(s => s.thing === thing)) continue;
        for (const state of states) {
          const changed = { kind: 'state', thing, state, negated: false };
          add(`condition "${condition_text(cond)}" replaced by "${condition_text(changed)}"`, 'replace', { when: rule.when.map((c, j) => (j === i ? changed : c)) });
        }
      }
    });
    return out;
  }

  // ------------------------------------------------------------------
  // Situations worth trying when looking for a difference (the change list)
  // Admitted changes are built from the jobs' own words: things the jobs mention, and all events.
  // ------------------------------------------------------------------
  const ordinal = n => (['first', 'second', 'third', 'fourth', 'fifth'][n - 1] || `${n}th`);
  function jobs_inputs(jobs_list) {
    const things = new Set();
    for (const job of jobs_list) {
      Object.keys(job.situation.start || {}).forEach(t => things.add(lower(t)));
      Object.keys(job.situation.force || {}).forEach(t => things.add(lower(t)));
    }
    return [...things];
  }
  function jobs_vocabulary(jobs_list) {
    const things = new Set();
    for (const job of jobs_list) {
      Object.keys(job.situation.start || {}).forEach(t => things.add(lower(t)));
      Object.keys(job.situation.force || {}).forEach(t => things.add(lower(t)));
      job.expect.forEach(text => { const m = tidy(text).match(/^(.+?)\s+is\s+(?:not\s+)?/i); if (m) things.add(lower(m[1])); });
    }
    return [...things];
  }
  function candidate_situations(model_a, model_b, jobs_list, limit, watch) {
    const vocabulary = jobs_vocabulary(jobs_list);
    const shared_things = Object.keys(model_a.things).filter(t => (watch === 'shared' || vocabulary.includes(lower(t))) && find_thing(model_b.things, t));
    const shared_events = model_a.events.filter(e => model_b.events.some(x => lower(x) === lower(e)));
    const bases = jobs_list.map(job => ({ from_job: job.name, situation: job.situation, steps: [] }));
    const seen = new Set();
    const out = [];
    const push = (base, situation, steps) => {
      const key = JSON.stringify(situation);
      if (seen.has(key) || out.length >= limit) return;
      seen.add(key); out.push({ from_job: base.from_job, situation, steps });
    };
    const inputs = jobs_inputs(jobs_list);
    const variants_of = (base, which) => {
      const list = [];
      const s = base.situation;
      const start_things = shared_things.filter(t => (which === 'inputs' ? inputs.includes(lower(t)) : !inputs.includes(lower(t))));
      for (const thing of (which === 'events' ? [] : start_things)) {
        const states_b = model_b.things[find_thing(model_b.things, thing)].map(lower);
        for (const state of model_a.things[thing]) {
          if (!states_b.includes(lower(state))) continue;
          const current = (s.start || {})[thing] || model_a.start[thing];
          if (lower(current) === lower(state)) continue;
          list.push({ situation: Object.assign({}, s, { start: Object.assign({}, s.start, { [thing]: state }) }), step: `${thing} starts ${state}` });
        }
      }
      if (which === 'outputs') return list;
      const ordered = Object.keys(s.events || {}).sort((a, b) => Number(a) - Number(b));
      const count_of = {};
      ordered.forEach(step => (s.events[step] || []).forEach(e => { count_of[e] = (count_of[e] || 0) + 1; }));
      const seen_so_far = {};
      for (const step of ordered) {
        const events = s.events[step] || [];
        events.forEach((e, i) => {
          seen_so_far[e] = (seen_so_far[e] || 0) + 1;
          const events_copy = copy(s.events); events_copy[step] = events.filter((_, j) => j !== i); if (!events_copy[step].length) delete events_copy[step];
          const which = count_of[e] > 1 ? `the ${ordinal(seen_so_far[e])} "${e}"` : `"${e}"`;
          list.push({ situation: Object.assign({}, s, { events: events_copy }), step: `${which} does not happen` });
        });
      }
      const order = Object.keys(s.events || {}).map(Number).sort((a, b) => a - b);
      const slots = [0].concat(order);
      for (const e of shared_events) slots.forEach((after, position) => {
        const events_copy = copy(s.events || {}); events_copy[String(after + 0.5)] = [e];
        const where = position === 0 ? 'first' : `after "${(s.events[String(after)] || []).join('" and "')}"`;
        list.push({ situation: Object.assign({}, s, { events: events_copy }), step: `"${e}" also happens ${where}` });
      });
      return list;
    };
    // Order: the jobs as they are; one change to an input or an event; two such changes;
    // then one change to the starting state of something the jobs only ask about.
    for (const base of bases) push(base, base.situation, []);
    for (const base of bases) for (const v of variants_of(base, 'inputs')) push(base, v.situation, [v.step]);
    for (const base of bases) for (const v of variants_of(base, 'inputs')) for (const w of variants_of({ situation: v.situation }, 'inputs')) push(base, w.situation, [v.step, w.step]);
    for (const base of bases) for (const v of variants_of(base, 'outputs')) push(base, v.situation, [v.step]);
    for (const base of bases) for (const v of variants_of(base, 'outputs')) for (const w of variants_of({ situation: v.situation }, 'inputs')) push(base, w.situation, [v.step, w.step]);
    return { list: out, observed: shared_things };
  }

  // Find situations where two models give different answers (Derivation 2: if none exists on the
  // change list, the two are one explanation at this level).
  function decide(model_a, model_b, jobs_list, options = {}) {
    const { list, observed } = candidate_situations(model_a, model_b, jobs_list, options.limit || 3000, options.watch);
    const timing_matters = jobs_list.some(j => j.at !== 'end');
    const route_of = (result, thing) => result.history.slice(0, result.end_step + 1).map(h => h[thing]).filter((v, i, a) => i === 0 || v !== a[i - 1]).join(' > ');
    const found = [];
    for (const c of list) {
      const pa = [], pb = [];
      const sa = resolve_situation(model_a, c.situation, pa, 'decide');
      const sb = resolve_situation(model_b, c.situation, pb, 'decide');
      if (pa.length || pb.length) continue;
      const ra = run(model_a, sa), rb = run(model_b, sb);
      const differences = [];
      for (const thing of observed) {
        const thing_b = find_thing(model_b.things, thing);
        const ea = ending_of(ra, thing), eb = ending_of(rb, thing_b);
        const clash_a = ra.clashes.some(x => x.thing === thing), clash_b = rb.clashes.some(x => x.thing === thing_b);
        if (ea.join('/').toLowerCase() !== eb.join('/').toLowerCase() || clash_a !== clash_b) differences.push({ thing, a: ea.join(' / ') + (clash_a ? ' (unsettled)' : ''), b: eb.join(' / ') + (clash_b ? ' (unsettled)' : '') });
        else if (timing_matters) {
          const ta = ra.history.slice(0, ra.end_step + 1).map(h => h[thing]).join('|').toLowerCase();
          const tb = rb.history.slice(0, rb.end_step + 1).map(h => h[thing]).join('|').toLowerCase();
          if (ta !== tb) differences.push({ thing, a: `${ea.join(' / ')}, by the steps ${ra.history.slice(0, ra.end_step + 1).map(h => h[thing]).join(', ')}`, b: `${eb.join(' / ')}, by the steps ${rb.history.slice(0, rb.end_step + 1).map(h => h[thing]).join(', ')}`, timing: true });
        }
      }
      if (differences.length) {
        found.push({ from_job: c.from_job, steps: c.steps, situation: c.situation, differences });
        if (found.length >= (options.max_found || 3)) break;
      }
    }
    return { found, tried: list.length, watched: observed };
  }
  function describe_situation(found) {
    const base = `the situation of job "${found.from_job}"`;
    return found.steps.length ? `${base}, but ${found.steps.join(' and ')}` : base;
  }

  // ------------------------------------------------------------------
  // The hard-to-vary sweep (Part VI: support sets, critical blocks, redundant routes)
  // ------------------------------------------------------------------
  function passing_set(model, jobs_list) { return new Set(check(model, jobs_list).passed); }
  function lost_jobs(model, jobs_list, baseline) { const now = passing_set(model, jobs_list); return [...baseline].filter(j => !now.has(j)); }

  function vary(model, jobs_list, options = {}) {
    const baseline_check = check(model, jobs_list);
    const baseline = new Set(baseline_check.passed);
    const report = { passing: [...baseline], failing: baseline_check.failed, rules: [], events: [], warnings: [], deciding_tests: [] };
    const job_from = Object.fromEntries(jobs_list.map(j => [j.name, j.from]));

    // Which rules ever do any work in any job? A rule that never changes anything is untested.
    const worked = new Set();
    for (const r of baseline_check.results) if (r.result) r.result.changes.forEach(c => c.rules.forEach(n => worked.add(n)));

    // Remove each rule; then pairs and triples among the rules whose removal alone costs nothing.
    const removal = {};
    for (const rule of model.rules) removal[rule.name] = lost_jobs(without_rules(model, [rule.name]), jobs_list, baseline);
    const free_alone = model.rules.filter(r => !removal[r.name].length && worked.has(r.name)).map(r => r.name);
    const joint = {};
    for (let i = 0; i < free_alone.length; i++) for (let j = i + 1; j < free_alone.length; j++) {
      const lost = lost_jobs(without_rules(model, [free_alone[i], free_alone[j]]), jobs_list, baseline);
      if (lost.length) { (joint[free_alone[i]] = joint[free_alone[i]] || []).push({ with: [free_alone[j]], lost }); (joint[free_alone[j]] = joint[free_alone[j]] || []).push({ with: [free_alone[i]], lost }); }
    }
    if (free_alone.length <= 8) {
      for (let i = 0; i < free_alone.length; i++) for (let j = i + 1; j < free_alone.length; j++) for (let k = j + 1; k < free_alone.length; k++) {
        const trio = [free_alone[i], free_alone[j], free_alone[k]];
        if (trio.some(a => (joint[a] || []).some(p => trio.includes(p.with[0])))) continue;
        const lost = lost_jobs(without_rules(model, trio), jobs_list, baseline);
        if (lost.length) trio.forEach(a => (joint[a] = joint[a] || []).push({ with: trio.filter(b => b !== a), lost }));
      }
    }

    // Swap each rule for its near neighbours.
    model.rules.forEach((rule, index) => {
      const survivors = neighbours(model, index).filter(n => {
        const now = passing_set(n.model, jobs_list);
        return [...baseline].every(j => now.has(j));
      });
      const entry = { rule: rule.name, text: rule_text(rule), removal_loses: removal[rule.name], joint: joint[rule.name] || [], survivors: survivors.map(s => ({ description: s.description, kind: s.kind, text: rule_text(s.rule), model: s.model })) };
      const held_by = entry.removal_loses;
      if (!worked.has(rule.name)) { entry.mark = 'unknown'; entry.why = 'it never changes anything in any job, so no job tests it'; entry.need = `a job in which ${rule.when.length ? rule.when.map(condition_text).join(' and ') : 'it can act'}`; }
      else if (!held_by.length && !entry.joint.length) { entry.mark = 'idle'; entry.why = 'removing it, alone or with other free rules, breaks no job'; }
      else if (!held_by.length) { entry.mark = 'two routes'; entry.why = entry.joint.map(p => `removing it together with "${p.with.join('" and "')}" breaks ${p.lost.map(j => `"${j}"`).join(', ')}`).join('; '); }
      else if (survivors.length) { entry.mark = 'loose'; entry.why = `breaks ${held_by.map(j => `"${j}"`).join(', ')} if removed, but a near neighbour passes every job: ${survivors.slice(0, 3).map(s => s.description).join('; ')}`; }
      else if (held_by.every(j => job_from[j] === 'added')) { entry.mark = 'held if'; entry.why = `held only by jobs someone added (${held_by.map(j => `"${j}"`).join(', ')}); held if those jobs are real`; }
      else { entry.mark = 'held'; entry.why = `removing it breaks ${held_by.map(j => `"${j}"`).join(', ')}, and no near neighbour passes every job`; }
      // What is really held, when only a condition is loose: the rule without that condition.
      const dropped = survivors.filter(s => s.kind === 'drop');
      if (dropped.length && entry.mark === 'loose') entry.really_held = dropped.map(s => rule_text(s.rule));
      report.rules.push(entry);
    });

    // Deciding tests: for each loose rule, a situation where the rule and its surviving neighbour disagree.
    if (options.decide !== false) {
      for (const entry of report.rules.filter(e => e.mark === 'loose')) {
        const asked = new Set();
        for (const survivor of entry.survivors.slice(0, options.per_rule || 3)) {
          const found = decide(model, survivor.model, jobs_list, { max_found: 1, limit: options.limit || 1500, watch: options.watch });
          const key = found.found[0] ? JSON.stringify(found.found[0].situation) : 'none';
          if (asked.has(key)) continue;
          asked.add(key);
          report.deciding_tests.push({ rule: entry.rule, variant: survivor.description, found: found.found[0] || null, tried: found.tried, watched: found.watched });
        }
      }
    }

    // Remove each event from each passing job: does the event (the scene) earn its place?
    for (const job of jobs_list) {
      if (!baseline.has(job.name)) continue;
      for (const [step, events] of Object.entries(job.situation.events || {})) {
        events.forEach((event, i) => {
          const changed = copy(job); changed.situation.events[step] = events.filter((_, j) => j !== i);
          const still = check_job(model, changed).passed;
          report.events.push({ job: job.name, event, step: Number(step), does_work: !still });
        });
      }
    }

    // The answer already sitting in the start, or stated by a rule with no conditions.
    const produced = {}, from_start = {};
    for (const r of baseline_check.results) {
      if (!r.passed || !r.expectations) continue;
      for (const c of r.expectations) {
        if (r.result.changes.some(x => x.thing === c.thing)) produced[c.thing] = true;
        else (from_start[c.thing] = from_start[c.thing] || []).push(r.job);
      }
    }
    for (const [thing, jobs_named] of Object.entries(from_start)) {
      if (!produced[thing]) report.warnings.push(`In every passing job that asks about ${thing}, its answer is just its starting state (${jobs_named.map(j => `"${j}"`).join(', ')}). The model never produces an answer for ${thing}; add a job where ${thing} has to change.`);
    }
    for (const rule of model.rules) if (!rule.when.length) report.warnings.push(`Rule "${rule.name}" has no conditions: it just states "${rule.then.map(setting_text).join(' and ')}" in every situation. That puts the answer in as a starting point.`);

    // Jobs that always expect the same answer cannot tell the model from one that always says it.
    const asked = {};
    for (const job of jobs_list) for (const text of job.expect) {
      const m = tidy(text).match(/^(.+?)\s+is\s+(not\s+)?(.+)$/i);
      if (m) (asked[lower(m[1])] = asked[lower(m[1])] || new Set()).add(`${m[2] ? 'not ' : ''}${lower(m[3])}`);
    }
    for (const [thing, answers] of Object.entries(asked)) {
      if (answers.size === 1) report.warnings.push(`No job expects ${thing} to be anything but "${[...answers][0]}". A model that always said so would pass too. Add a job where ${thing} should come out differently.`);
    }
    return report;
  }

  // ------------------------------------------------------------------
  // Checking a fix (Part XI, Repair: fix at least one failing job, keep every passing job)
  // ------------------------------------------------------------------
  function rule_signature(rule) { return `${conditions_key(rule).join(' & ')} => ${rule.then.map(setting_text).sort().join(' & ')} ${rule.strength}`; }
  function check_fix(old_model, new_model, jobs_list, options = {}) {
    const before = check(old_model, jobs_list), after = check(new_model, jobs_list);
    const was = new Set(before.passed), now = new Set(after.passed);
    const repaired = [...now].filter(j => !was.has(j));
    const lost = [...was].filter(j => !now.has(j));
    const old_sigs = new Map(old_model.rules.map(r => [rule_signature(r), r.name]));
    const new_sigs = new Map(new_model.rules.map(r => [rule_signature(r), r.name]));
    const added_rules = new_model.rules.filter(r => !old_sigs.has(rule_signature(r)));
    const removed_rules = old_model.rules.filter(r => !new_sigs.has(rule_signature(r)));
    const added_things = Object.keys(new_model.things).filter(t => !find_thing(old_model.things, t));
    const added_states = [];
    for (const t of Object.keys(new_model.things)) { const o = find_thing(old_model.things, t); if (o) new_model.things[t].forEach(s => { if (!find_state(old_model.things, o, s)) added_states.push(`${t}: ${s}`); }); }
    let verdict;
    if (!repaired.length && !lost.length) verdict = 'no change';
    else if (!repaired.length) verdict = 'worse';
    else if (lost.length) verdict = 'trade';
    else verdict = 'accepted';
    const kind = added_things.length || added_states.length ? 'new thing (construction)' : added_rules.length && !removed_rules.length ? 'new rule' : 'tweak of existing rules';
    // Patch check: a new rule held only by the jobs this fix repaired. Offer a new prediction it makes.
    const patches = [];
    if (verdict === 'accepted' || verdict === 'trade') {
      for (const rule of added_rules) {
        const without = without_rules(new_model, [rule.name]);
        const breaks = [...now].filter(j => !passing_set(without, jobs_list).has(j));
        if (breaks.length && breaks.every(j => repaired.includes(j))) {
          const prediction = options.decide === false ? null : decide(new_model, without, jobs_list, { max_found: 4 }).found.find(f => f.steps.length > 0) || null;
          patches.push({ rule: rule.name, text: rule_text(rule), held_only_by: breaks, prediction });
        }
      }
    }
    return { verdict, repaired, lost, kind, added_rules: added_rules.map(r => r.name), removed_rules: removed_rules.map(r => r.name), added_things, added_states, patches, still_failing: after.failed };
  }

  // ------------------------------------------------------------------
  // Tweak search: try every one-step change to the existing rules (a selection response, Part IV).
  // If nothing repairs a failing job without breaking another, say that something new is needed
  // (Derivation 10: the failure is structural, not a matter of tuning).
  // ------------------------------------------------------------------
  function tweaks(model, jobs_list, options = {}) {
    const before = check(model, jobs_list);
    const was = new Set(before.passed);
    const failing = before.failed;
    const helpful = [];
    const candidates = [];
    model.rules.forEach((_, index) => neighbours(model, index).forEach(n => candidates.push(n)));
    model.rules.forEach(rule => candidates.push({ description: `rule "${rule.name}" removed`, kind: 'remove', rule_name: rule.name, model: without_rules(model, [rule.name]) }));
    model.rules.forEach((rule, index) => {
      const used = new Set(rule.when.filter(c => c.kind === 'state').map(c => c.thing));
      for (const [thing, states] of Object.entries(model.things)) {
        if (used.has(thing)) continue;
        for (const state of states) {
          const narrower = Object.assign({}, rule, { when: rule.when.concat({ kind: 'state', thing, state, negated: false }) });
          candidates.push({ description: `condition "${thing} is ${state}" added`, kind: 'add', rule_name: rule.name, rule: narrower, model: with_rule(model, index, narrower) });
        }
      }
    });
    model.rules.forEach(rule => { if (rule.strength === 'always') candidates.push({ description: `rule "${rule.name}" marked "usually"`, kind: 'strength', rule_name: rule.name, model: with_rule(model, model.rules.indexOf(rule), Object.assign({}, rule, { strength: 'usually' })) }); });
    for (const c of candidates) {
      const now = passing_set(c.model, jobs_list);
      const repaired = failing.filter(j => now.has(j));
      const lost = [...was].filter(j => !now.has(j));
      if (repaired.length && !lost.length) {
        if (c.rule) c.model.rules = c.model.rules.map(r => (r.name === c.rule_name ? Object.assign({}, r, { made_by: 'checker small fix' }) : r));
        helpful.push({ description: `in rule "${c.rule_name}": ${c.description}`, kind: c.kind, repaired, rule_text: c.rule ? rule_text(c.rule) : null, model: c.model });
      }
    }
    const preference = ['unclash', 'add', 'condition', 'result', 'flip', 'drop', 'replace', 'remove', 'strength'];
    helpful.sort((a, b) => b.repaired.length - a.repaired.length || preference.indexOf(a.kind) - preference.indexOf(b.kind));
    const covered = new Set(helpful.flatMap(h => h.repaired));
    return { failing, helpful: helpful.slice(0, options.max || 6), needs_something_new: failing.filter(j => !covered.has(j)) };
  }

  // Turn a checked model back into its fill-in form (for saving, and for showing the small AI).
  function model_to_form(model) {
    return {
      things: copy(model.things), events: model.events.slice(), start: Object.assign({}, model.start),
      rules: model.rules.map(r => Object.assign({ name: r.name, when: r.when.map(condition_text), then: r.then.length === 1 ? setting_text(r.then[0]) : r.then.map(setting_text) },
        r.strength === 'usually' ? { strength: 'usually' } : {}, r.made_by ? { made_by: r.made_by } : {})),
    };
  }

  // ------------------------------------------------------------------
  // New rule search: try every single new rule with one or two conditions, over the things and
  // events the model already has. Still a selection response: it cannot invent a new thing.
  // Only rules that repair a failing job and break nothing are kept.
  // ------------------------------------------------------------------
  function new_rule_search(model, jobs_list, options = {}) {
    const before = check(model, jobs_list);
    const was = new Set(before.passed);
    if (!before.failed.length) return { helpful: [], tried: 0 };
    const conditions = [];
    for (const [thing, states] of Object.entries(model.things)) for (const state of states) conditions.push({ kind: 'state', thing, state, negated: false });
    for (const event of model.events) conditions.push({ kind: 'event', event });
    // Results: first the states the failing jobs ask for, then every other state.
    const wanted = [];
    for (const r of before.results) if (!r.passed && r.expectations) r.expectations.forEach(c => { if (!c.negated) wanted.push({ thing: c.thing, state: c.state }); });
    const results = wanted.concat(Object.entries(model.things).flatMap(([thing, states]) => states.map(state => ({ thing, state }))))
      .filter((x, i, a) => a.findIndex(y => y.thing === x.thing && y.state === x.state) === i);
    const limit = options.limit || 6000;
    const helpful = [];
    let tried = 0;
    const consider = when => {
      for (const then of results) {
        if (tried >= limit) return;
        if (when.some(c => c.kind === 'state' && c.thing === then.thing && c.state === then.state)) continue;
        tried++;
        const rule = { name: `checker rule ${model.rules.length + 1}`, when, then: [then], strength: 'always', made_by: 'checker new rule' };
        const candidate = Object.assign({}, model, { rules: model.rules.concat(rule) });
        const now = passing_set(candidate, jobs_list);
        const repaired = before.failed.filter(j => now.has(j));
        if (repaired.length && [...was].every(j => now.has(j))) helpful.push({ description: `new rule: ${rule_text(rule)}`, kind: 'new rule', repaired, model: candidate, conditions: when.length });
      }
    };
    for (const a of conditions) consider([a]);
    for (let i = 0; i < conditions.length && tried < limit; i++) for (let j = i + 1; j < conditions.length && tried < limit; j++) {
      const a = conditions[i], b = conditions[j];
      if (a.kind === 'state' && b.kind === 'state' && a.thing === b.thing) continue;
      consider([a, b]);
    }
    helpful.sort((x, y) => y.repaired.length - x.repaired.length || x.conditions - y.conditions);
    return { helpful: helpful.slice(0, options.max || 6), tried };
  }

  // Add the owner's word list to a model: things and states the jobs use that the model lacks.
  // These are given by the owner, not invented, so adding them is not a guess.
  function add_owner_words(model, owner_things) {
    const form = model_to_form(model);
    const added = [];
    for (const [thing, states] of Object.entries(owner_things)) {
      const existing = Object.keys(form.things).find(t => lower(t) === lower(thing));
      if (!existing) { form.things[thing] = states.slice(); form.start[thing] = states[0]; added.push(thing); continue; }
      for (const state of states) if (!form.things[existing].some(x => lower(x) === lower(state))) { form.things[existing].push(state); added.push(`${existing}: ${state}`); }
    }
    return { model: prepare_model(form), added };
  }

  // ------------------------------------------------------------------
  // Plain-words reports
  // ------------------------------------------------------------------
  function report_check(model, jobs_list) {
    const lines = [];
    if (model.problems.length) { lines.push('PROBLEMS READING THE MODEL (fix these first):'); model.problems.forEach(p => lines.push(`- ${p}`)); }
    const c = check(model, jobs_list);
    for (const r of c.results) {
      lines.push(`${r.passed ? 'PASS' : r.verdict.toUpperCase()}: job "${r.job}"`);
      if (!r.passed) explain_failure(model, r).forEach(l => lines.push(`  - ${l}`));
    }
    lines.push(`${c.passed.length} of ${c.results.length} jobs pass.`);
    return { text: lines.join('\n'), check: c };
  }
  function report_vary(model, jobs_list, options) {
    const v = vary(model, jobs_list, options);
    const lines = [];
    if (v.failing.length) lines.push(`Note: ${v.failing.length} job(s) fail, so these tests use only the passing jobs.`);
    for (const r of v.rules) {
      lines.push(`${r.mark.toUpperCase()}: rule "${r.rule}" (${r.text}) - ${r.why}.`);
      if (r.need) lines.push(`  To test it: ${r.need}.`);
      if (r.really_held) lines.push(`  What is really held: ${r.really_held[0]}.`);
    }
    for (const d of v.deciding_tests) {
      if (d.found) lines.push(`DECIDING TEST for rule "${d.rule}" (${d.variant}): in ${describe_situation(d.found)}, ${d.found.differences.map(x => `your model says ${x.thing} ends ${x.a}, the variant says ${x.b}`).join('; ')}. Which is right? That answer becomes a new job.`);
      else lines.push(`NO DIFFERENCE FOUND for rule "${d.rule}" (${d.variant}): ${d.tried} situations tried, watching ${d.watched.join(', ')}. At this level the two may be one explanation. Telling them apart would take a new question, such as one that asks about something else.`);
    }
    const idle_events = v.events.filter(e => !e.does_work);
    for (const e of idle_events) lines.push(`EVENT DOES NO WORK: in job "${e.job}", removing "${e.event}" (step ${e.step}) leaves the outcome the same.`);
    for (const w of v.warnings) lines.push(`WARNING: ${w}`);
    return { text: lines.join('\n'), vary: v };
  }
  function report_fix(old_model, new_model, jobs_list) {
    const f = check_fix(old_model, new_model, jobs_list);
    const lines = [];
    const words = { accepted: 'ACCEPTED: it repairs jobs and breaks none.', trade: 'NOT ACCEPTED YET: it repairs some jobs but breaks others.', worse: 'NOT ACCEPTED: it breaks jobs and repairs none.', 'no change': 'NO CHANGE: no job changed result.' };
    lines.push(words[f.verdict]);
    if (f.repaired.length) lines.push(`Repaired: ${f.repaired.map(j => `"${j}"`).join(', ')}.`);
    if (f.lost.length) lines.push(`Broken by this fix: ${f.lost.map(j => `"${j}"`).join(', ')}.`);
    lines.push(`Kind of fix: ${f.kind}.`);
    for (const p of f.patches) {
      lines.push(`PATCH (for now): rule "${p.rule}" does only the job(s) that forced it (${p.held_only_by.map(j => `"${j}"`).join(', ')}).`);
      if (p.prediction) lines.push(`  It also predicts: in ${describe_situation(p.prediction)}, ${p.prediction.differences.map(x => `${x.thing} ends ${x.a} (without the rule: ${x.b})`).join('; ')}. If that is right, the rule earns a second job.`);
    }
    if (f.still_failing.length) lines.push(`Still failing: ${f.still_failing.map(j => `"${j}"`).join(', ')}.`);
    return { text: lines.join('\n'), fix: f };
  }
  function report_tweaks(model, jobs_list) {
    const t = tweaks(model, jobs_list);
    const lines = [];
    if (!t.failing.length) return { text: 'Every job passes; no tweak needed.', tweaks: t };
    for (const h of t.helpful) lines.push(`SMALL FIX FOUND: ${h.description} repairs ${h.repaired.map(j => `"${j}"`).join(', ')} and breaks nothing.`);
    if (t.needs_something_new.length) lines.push(`NO SMALL CHANGE to the existing rules repairs ${t.needs_something_new.map(j => `"${j}"`).join(', ')}. Something new is needed: a new rule, or a new thing to keep track of.`);
    return { text: lines.join('\n'), tweaks: t };
  }

  return {
    prepare_model, prepare_jobs, run, check, check_job, explain_failure, vary, check_fix, tweaks, decide, model_to_form, rule_text_of: rule_text, new_rule_search, add_owner_words,
    report_check, report_vary, report_fix, report_tweaks, describe_situation, rule_text, neighbours, resolve_situation, candidate_situations,
  };
});

// Command line use: node checker.js check|vary|tweaks MODEL.json JOBS.json
//                   node checker.js fix OLD.json NEW.json JOBS.json
//                   node checker.js decide A.json B.json JOBS.json
if (typeof require !== 'undefined' && typeof module !== 'undefined' && require.main === module) {
  const fs = require('fs');
  const C = module.exports;
  const [command, ...paths] = process.argv.slice(2);
  const read = p => JSON.parse(fs.readFileSync(p, 'utf8'));
  const jobs = C.prepare_jobs(read(paths[paths.length - 1])).jobs;
  if (command === 'check') console.log(C.report_check(C.prepare_model(read(paths[0])), jobs).text);
  else if (command === 'vary') console.log(C.report_vary(C.prepare_model(read(paths[0])), jobs).text);
  else if (command === 'tweaks') console.log(C.report_tweaks(C.prepare_model(read(paths[0])), jobs).text);
  else if (command === 'fix') console.log(C.report_fix(C.prepare_model(read(paths[0])), C.prepare_model(read(paths[1])), jobs).text);
  else if (command === 'decide') {
    const d = C.decide(C.prepare_model(read(paths[0])), C.prepare_model(read(paths[1])), jobs);
    console.log(d.found.length ? d.found.map(f => `In ${C.describe_situation(f)}: ${f.differences.map(x => `${x.thing}: first ${x.a}, second ${x.b}`).join('; ')}`).join('\n') : `No difference found in ${d.tried} situations.`);
  } else console.log('Use: check | vary | tweaks MODEL JOBS, or fix OLD NEW JOBS, or decide A B JOBS');
}
