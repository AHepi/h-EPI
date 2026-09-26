/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Log 35. Can a language that grows close the gap log 34 found? The checker's rule language (things with
 * listed states, events, rules) may here gain new kinds of thing: each kind has a starting value, named
 * changes and named tests, each a short JavaScript expression. A model lists new things of those kinds,
 * and its rules read them ("balance is zero") and change them ("balance does add one"). Everything else
 * is the rule language as it was.
 *
 *   read_growing_model  - checks every name in a model and reports what does not fit
 *   run_growing         - runs a model on many sequences in a separate process with no access to files,
 *                         the network or the account key, and with a time limit
 *   growing_language    - the arm: DeepSeek writes a model; the program runs it on every observation and
 *                         reports which fail and how; up to 6 models; the best is graded on the tests
 * The fixed-language and universal-language arms are log 34's, unchanged. The devices: log 34's balance
 * gate with two deeper test cases, a redesigned peg tube whose observations refute separate counts of
 * each colour, and log 25's grudge as a control.
 * The plan and conjectures: "35 Plan - a language that grows.md".
 *
 * Run with:
 *   DEEPSEEK_API_KEY=... NODE_USE_ENV_PROXY=1 node "35 growing language.js" OUTFOLDER [REPEATS]
 *   node "35 growing language.js" --summarise FOLDER
 *   node "35 growing language.js" --probe FOLDER   (after the run, at no cost: each arm's best model on cases
 *                                                past the planned tests; added after reading the results)
 */
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');
const L = require('./09 loop.js');
const K = require('./25 construction worlds.js');
const X = require('./34 language test.js');

const ROUNDS = 6;
const STEP_LIMIT = 60;
const lower = t => String(t == null ? '' : t).trim().replace(/\s+/g, ' ').toLowerCase();
const repeat = (n, action) => Array(n).fill(action);
function scramble_key(text) {
  let h = 2166136261;
  for (const ch of text) { h ^= ch.charCodeAt(0); h = Math.imul(h, 16777619) >>> 0; }
  return h;
}

// ------------------------------------------------------------------
// The devices
// ------------------------------------------------------------------
const GATE = Object.assign({}, X.GATE, {
  long_tests: () => X.GATE.long_tests().concat([repeat(500, 'push').concat(repeat(500, 'pull')), repeat(500, 'push').concat(repeat(499, 'pull'))]),
});

// The peg tube's near rival: separate counts of each colour. A peg comes out if one of its colour is
// anywhere inside; taking out a colour that has none jams it.
function separate_counts(events) {
  const count = { red: 0, blue: 0 };
  for (const e of events) {
    const [colour, way] = e.split(' ');
    if (way === 'in') { count[colour]++; continue; }
    if (!count[colour]) return { light: 'red' };
    count[colour]--;
  }
  return { light: count.red + count.blue ? 'amber' : 'green' };
}
const peg_colour = i => ((i * 7) % 3 === 0 ? 'blue' : 'red');
const pattern_in = n => Array.from({ length: n }, (_, i) => `${peg_colour(i)} in`);
const right_order_out = n => pattern_in(n).reverse().map(a => a.replace(' in', ' out'));
const PEGS = {
  id: 'peg tube',
  request: X.PEGS.request,
  visible: X.PEGS.visible,
  actions: X.PEGS.actions,
  truth: X.PEGS.truth,
  obvious: X.PEGS.obvious,
  rival: separate_counts,
  longest: 5,
  long_tests: () => X.PEGS.long_tests().concat([
    repeat(8, 'red in').concat(repeat(8, 'blue in'), ['red out']),
    repeat(30, 'red in').concat(repeat(30, 'red out')),
    pattern_in(20).concat(right_order_out(20)),
    pattern_in(20).concat(right_order_out(20).slice(0, 19), [right_order_out(20)[19].startsWith('red') ? 'blue out' : 'red out']),
    // Cases separate counts must get wrong: a peg of the right colour is inside, but not on top.
    repeat(15, 'red in').concat(['blue in'], repeat(15, 'red out'), ['blue out']),
    repeat(10, 'blue in').concat(repeat(10, 'red in'), repeat(10, 'blue out'), repeat(10, 'red out')),
    pattern_in(20).concat(pattern_in(20).map(a => a.replace(' in', ' out'))),
  ]),
};
const GRUDGE = X.GRUDGE;
const DEVICES = [GATE, PEGS, GRUDGE];

const case_of = (device, name, events, long) => {
  const see = device.truth(events);
  const thing = Object.keys(device.visible)[0];
  return { name, events, see, hard: device.obvious(events)[thing] !== see[thing], rival_wrong: device.rival ? device.rival(events)[thing] !== see[thing] : false, long };
};
function peg_cases() {
  const thing = 'light';
  const shuffled = K.sequences(PEGS.actions, PEGS.longest).sort((a, b) => scramble_key(`peg tube 35|${a.join('>')}`) - scramble_key(`peg tube 35|${b.join('>')}`));
  const is = (events, state) => PEGS.truth(events)[thing] === state;
  const rival_wrong = events => separate_counts(events)[thing] !== PEGS.truth(events)[thing];
  const observations = [], short_tests = [];
  for (const state of ['green', 'amber', 'red']) {
    const pool = shuffled.filter(e => is(e, state));
    if (state === 'red') {
      const order = pool.filter(rival_wrong), other = pool.filter(e => !rival_wrong(e));
      observations.push(...order.slice(0, 4), ...other.slice(0, 4));
      short_tests.push(order[4], other[4]);
    } else {
      observations.push(...pool.slice(0, 8));
      short_tests.push(...pool.slice(8, 10));
    }
  }
  observations.sort((a, b) => scramble_key(a.join('>')) - scramble_key(b.join('>')));
  return {
    observations: observations.map((e, i) => case_of(PEGS, `observation ${i + 1}`, e, false)),
    tests: short_tests.map((e, i) => case_of(PEGS, `test ${i + 1}`, e, false))
      .concat(PEGS.long_tests().map((e, i) => case_of(PEGS, `test ${short_tests.length + i + 1}`, e, true))),
  };
}
function cases(device) {
  if (device.id === 'peg tube') return peg_cases();
  const c = X.cases(device.id === 'balance gate' ? X.GATE : device);
  if (device.id !== 'balance gate') return c;
  const extra = GATE.long_tests().slice(6).map((e, i) => case_of(GATE, `test ${c.tests.length + i + 1}`, e, true));
  return { observations: c.observations, tests: c.tests.concat(extra) };
}

// ------------------------------------------------------------------
// Reading a growing model: every name must be known
// ------------------------------------------------------------------
function as_list(v) { return v == null ? [] : Array.isArray(v) ? v : [v]; }
function read_growing_model(raw) {
  const problems = [];
  if (!raw || typeof raw !== 'object') return { problems: ['The model is not readable.'] };
  const things = raw.things && typeof raw.things === 'object' ? raw.things : {};
  const kinds = raw.kinds && typeof raw.kinds === 'object' ? raw.kinds : {};
  const new_things = raw.new_things && typeof raw.new_things === 'object' ? raw.new_things : {};
  const events = as_list(raw.events).map(String);
  const start = {};
  for (const [t, states] of Object.entries(things)) {
    if (!Array.isArray(states) || !states.length) { problems.push(`Thing "${t}" needs a list of states.`); continue; }
    const s = raw.start && raw.start[t] != null ? String(raw.start[t]) : String(states[0]);
    if (!states.map(String).includes(s)) problems.push(`Start: "${s}" is not a state of "${t}".`);
    start[t] = s;
  }
  for (const [k, def] of Object.entries(kinds)) {
    if (!def || typeof def !== 'object') { problems.push(`Kind "${k}" needs a start, changes and tests.`); continue; }
    if (!('start' in def)) problems.push(`Kind "${k}" needs a "start" value.`);
    for (const part of ['changes', 'tests']) if (def[part] != null && typeof def[part] !== 'object') problems.push(`Kind "${k}": "${part}" must map names to expressions.`);
  }
  for (const [n, k] of Object.entries(new_things)) {
    if (!kinds[k]) problems.push(`New thing "${n}" is of kind "${k}", which is not defined.`);
    if (things[n]) problems.push(`"${n}" is both a thing and a new thing.`);
  }
  const find = (map, name) => Object.keys(map).find(x => lower(x) === lower(name));
  const read_condition = (text, where) => {
    const words = String(text).trim().replace(/[.]$/, '');
    let m = /^(.+?)\s+happens$/i.exec(words);
    if (m) { const e = events.find(x => lower(x) === lower(m[1])); if (!e) problems.push(`${where}: "${m[1]}" is not a listed event.`); return e ? { kind: 'event', event: e } : null; }
    m = /^(.+?)\s+is\s+not\s+(.+)$/i.exec(words);
    const negated = !!m;
    if (!m) m = /^(.+?)\s+is\s+(.+)$/i.exec(words);
    if (!m) { problems.push(`${where}: "${words}" should look like "THING is STATE", "THING is not STATE", "NEW THING is TEST" or "EVENT happens".`); return null; }
    const t = find(things, m[1]);
    if (t) { const s = things[t].map(String).find(x => lower(x) === lower(m[2])); if (!s) { problems.push(`${where}: "${m[2]}" is not a state of "${t}".`); return null; } return { kind: 'state', thing: t, state: s, negated }; }
    const n = find(new_things, m[1]);
    if (n) { const tests = (kinds[new_things[n]] || {}).tests || {}; const test = find(tests, m[2]); if (!test) { problems.push(`${where}: "${m[2]}" is not a test of the kind "${new_things[n]}".`); return null; } return { kind: 'test', thing: n, test, negated }; }
    problems.push(`${where}: "${m[1]}" is not a thing or a new thing.`);
    return null;
  };
  const read_result = (text, where) => {
    const words = String(text).trim().replace(/[.]$/, '');
    let m = /^(.+?)\s+does\s+(.+)$/i.exec(words);
    if (m) {
      const n = find(new_things, m[1]);
      if (!n) { problems.push(`${where}: "${m[1]}" is not a new thing.`); return null; }
      const changes = (kinds[new_things[n]] || {}).changes || {};
      const change = find(changes, m[2]);
      if (!change) { problems.push(`${where}: "${m[2]}" is not a change of the kind "${new_things[n]}".`); return null; }
      return { kind: 'change', thing: n, change };
    }
    m = /^(.+?)\s+is\s+(.+)$/i.exec(words);
    const t = m && find(things, m[1]);
    const s = t && things[t].map(String).find(x => lower(x) === lower(m[2]));
    if (!s) { problems.push(`${where}: a result must be "THING is STATE" or "NEW THING does CHANGE"; "${words}" is neither.`); return null; }
    return { kind: 'set', thing: t, state: s };
  };
  const rules = as_list(raw.rules).map((r, i) => {
    const name = String(r && r.name || `rule ${i + 1}`);
    const when = as_list(r && r.when).map(c => read_condition(c, `Rule "${name}"`)).filter(Boolean);
    const then = as_list(r && r.then).map(c => read_result(c, `Rule "${name}"`)).filter(Boolean);
    if (!then.length) problems.push(`Rule "${name}" has no usable result.`);
    return { name, when, then };
  });
  return { problems, model: { things, start, events, kinds, new_things, rules } };
}

// ------------------------------------------------------------------
// Running a growing model, in a separate process
// ------------------------------------------------------------------
// This function is sent as text to the separate process; it uses nothing from outside itself but vm.
function growing_runner(vm, model, sequences, step_limit) {
  const context = vm.createContext({});
  const compiled = {};
  const compile = (kind, part, name, expr) => {
    const key = `${kind}|${part}|${name}`;
    compiled[key] = new vm.Script(`(function (value) { return (${expr}); })`).runInContext(context, { timeout: 200 });
    return compiled[key];
  };
  for (const [k, def] of Object.entries(model.kinds)) {
    for (const [n, e] of Object.entries(def.changes || {})) compile(k, 'changes', n, e);
    for (const [n, e] of Object.entries(def.tests || {})) compile(k, 'tests', n, e);
  }
  const copy = v => (v === undefined ? undefined : JSON.parse(JSON.stringify(v)));
  const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
  const call = (kind, part, name, value) => {
    const f = compiled[`${kind}|${part}|${name}`];
    context.__f = f; context.__v = JSON.stringify(value === undefined ? null : value);
    const out = vm.runInContext('JSON.stringify(__f(JSON.parse(__v)))', context, { timeout: 200 });
    return out === undefined ? undefined : JSON.parse(out);
  };
  const holds = (c, state, values, event) => {
    if (c.kind === 'event') return c.event === event;
    if (c.kind === 'state') return (state[c.thing] === c.state) !== c.negated;
    return (!!call(model.new_things[c.thing], 'tests', c.test, values[c.thing])) !== c.negated;
  };
  const step = (state, values, event) => {
    const offers = {}, changes = [];
    for (const rule of model.rules) {
      if (!rule.when.every(c => holds(c, state, values, event))) continue;
      for (const r of rule.then) {
        if (r.kind === 'set') (offers[r.thing] = offers[r.thing] || []).push({ state: r.state, weight: rule.when.length });
        else changes.push(r);
      }
    }
    const next_state = Object.assign({}, state);
    for (const [t, list] of Object.entries(offers)) {
      const most = Math.max(...list.map(o => o.weight));
      const top = [...new Set(list.filter(o => o.weight === most).map(o => o.state))];
      if (top.length === 1) next_state[t] = top[0]; // otherwise unsettled: the thing keeps its state
    }
    const next_values = Object.assign({}, values);
    for (const c of changes) next_values[c.thing] = copy(call(model.new_things[c.thing], 'changes', c.change, next_values[c.thing]));
    return { state: next_state, values: next_values };
  };
  const settle = (s) => {
    for (let n = 0; n < step_limit; n++) {
      const next = step(s.state, s.values, null);
      if (same(next.state, s.state) && same(next.values, s.values)) return { s, settled: true };
      s = next;
    }
    return { s, settled: false };
  };
  return sequences.map(events => {
    try {
      let s = { state: Object.assign({}, model.start), values: {} };
      for (const [n, k] of Object.entries(model.new_things)) s.values[n] = copy(model.kinds[k].start);
      let settled = true;
      let r = settle(s); s = r.s; settled = settled && r.settled;
      for (const e of events) { s = step(s.state, s.values, e); r = settle(s); s = r.s; settled = settled && r.settled; }
      return { state: s.state, settled };
    } catch (e) { return { error: String(e && e.message || e).slice(0, 200) }; }
  });
}
const RUNNER = `
const vm = require('vm');
let input = '';
process.stdin.on('data', d => { input += d; });
process.stdin.on('end', () => {
  const { model, sequences, step_limit } = JSON.parse(input);
  let out;
  try { out = { results: (${growing_runner.toString()})(vm, model, sequences, step_limit) }; }
  catch (e) { out = { error: String(e && e.message || e).slice(0, 300) }; }
  process.stdout.write(JSON.stringify(out));
});`;
function run_growing(model, sequences) {
  const done = spawnSync(process.execPath, ['-e', RUNNER], { input: JSON.stringify({ model, sequences, step_limit: STEP_LIMIT }), env: {}, cwd: os.tmpdir(), timeout: 120000, maxBuffer: 64 * 1024 * 1024, encoding: 'utf8' });
  if (done.error || done.status !== 0) return { error: done.error ? `the model did not finish (${done.error.code || done.error.message})` : `the model stopped: ${String(done.stderr).slice(0, 200)}` };
  try { return JSON.parse(done.stdout); } catch (e) { return { error: 'the model gave no readable result' }; }
}
function check_growing(device, raw, list) {
  const thing = Object.keys(device.visible)[0];
  const read = read_growing_model(raw);
  if (read.problems.length) return { problems: read.problems, results: list.map(c => ({ name: c.name, right: false, problem: 'the model has problems' })) };
  if (!read.model.things[thing]) return { problems: [`The model has no thing "${thing}", which is what can be seen.`], results: list.map(c => ({ name: c.name, right: false, problem: 'no visible thing' })) };
  const ran = run_growing(read.model, list.map(c => c.events));
  if (ran.error) return { problems: [ran.error], results: list.map(c => ({ name: c.name, right: false, problem: ran.error })) };
  return {
    problems: [],
    results: list.map((c, i) => {
      const r = ran.results[i];
      if (r.error) return { name: c.name, right: false, problem: r.error };
      const got = r.state[thing];
      return { name: c.name, right: got === c.see[thing] && r.settled, got, problem: r.settled ? null : `the model never settles; ${thing} was ${got} when it stopped` };
    }),
  };
}
const shape_of = raw => ({
  kinds: Object.keys((raw && raw.kinds) || {}).length,
  new_things: Object.keys((raw && raw.new_things) || {}).length,
  rules: as_list(raw && raw.rules).length,
  kind_expressions: Object.values((raw && raw.kinds) || {}).reduce((s, k) => s + Object.keys((k && k.changes) || {}).length + Object.keys((k && k.tests) || {}).length, 0),
});

// ------------------------------------------------------------------
// The growing-language arm
// ------------------------------------------------------------------
const GROWTH_GUIDE = `${L.GUIDE.replace(/\n*Reply with the model as JSON only\.\s*$/, '')}

You may also add new kinds of thing, when the things above cannot hold what you need to keep track of. A new kind has a starting value (any JSON value), named "changes" and named "tests". Each change is a short JavaScript expression that gives the new value from the old one, called value. Each test is a short JavaScript expression that gives true or false. Then list "new_things", each with its kind. Rules read a new thing with a condition "NEW THING is TEST" or "NEW THING is not TEST", and change it with a result "NEW THING does CHANGE". A new thing is not a thing with listed states; what can be seen must still be a thing with listed states.

Example with a new kind: a lamp that stays lit while more people have come in than gone out.
{"things": {"lamp": ["dark", "lit"]}, "events": ["come in", "go out"], "start": {"lamp": "dark"},
 "kinds": {"number": {"start": 0, "changes": {"add one": "value + 1", "take one": "value - 1"}, "tests": {"above zero": "value > 0"}}},
 "new_things": {"people inside": "number"},
 "rules": [
  {"name": "someone comes in", "when": ["come in happens"], "then": "people inside does add one"},
  {"name": "someone goes out", "when": ["go out happens"], "then": "people inside does take one"},
  {"name": "lit while anyone is in", "when": ["people inside is above zero"], "then": "lamp is lit"},
  {"name": "dark when empty", "when": ["people inside is not above zero"], "then": "lamp is dark"}]}

Reply with the model as JSON only.`;

async function growing_language(D, device, observations, tests) {
  const g = D.make_deepseek_guesser();
  const thing = Object.keys(device.visible)[0];
  const opening = `Task: ${X.evidence_in_words(device, observations)}\n\nWrite a model that explains every observation. Use exactly the names above for what you can see and for the actions.`;
  const rounds = [];
  let best = null, current = null;
  for (let round = 1; round <= ROUNDS; round++) {
    let ask = opening;
    if (current) {
      const failing = current.checked.results.filter(c => !c.right);
      const report = current.checked.problems.length
        ? `The checker could not run it:\n${current.checked.problems.map(p => `- ${p}`).join('\n')}`
        : `The checker ran it on the observations. ${observations.length - failing.length} of ${observations.length} hold. These do not:\n${failing.map(c => { const o = observations.find(x => x.name === c.name); return `- ${c.name}: ${o.events.join(', ')}. Observed: ${thing} is ${o.see[thing]}. Your model: ${c.problem ? c.problem : `${thing} is ${c.got}`}.`; }).join('\n')}`;
      ask = `${opening}\n\nYour last model:\n${JSON.stringify(current.raw)}\n\n${report}\n\nWrite the whole model again so that every observation holds.`;
    }
    const raw = L.read_reply(await g([{ role: 'system', content: GROWTH_GUIDE }, { role: 'user', content: ask }], {}));
    const checked = raw ? check_growing(device, raw, observations) : null;
    const passed = checked ? checked.results.filter(c => c.right).length : 0;
    rounds.push({ round, readable: !!raw, problems: checked ? checked.problems : ['unreadable reply'], passed, shape: raw ? shape_of(raw) : null, model: raw });
    if (raw) { current = { raw, checked }; if (!best || passed > best.passed) best = { raw, passed, round }; }
    if (raw && passed === observations.length) break;
  }
  let graded = tests.map(t => ({ test: t.name, hard: t.hard, long: t.long, right: false }));
  if (best) {
    const results = check_growing(device, best.raw, tests).results;
    graded = tests.map((t, i) => ({ test: t.name, hard: t.hard, long: t.long, right: results[i].right, problem: results[i].problem || undefined }));
  }
  return { rounds, best_round: best ? best.round : null, best_passes: best ? best.passed : 0, observations: observations.length, shape: best ? shape_of(best.raw) : null, graded, tokens_out: g.counts.tokens_out, cut_off: g.counts.cut_off, calls: rounds.length };
}

const ARMS = { 'fixed language': X.fixed_language, 'growing language': growing_language, 'universal language': X.universal_language };
async function run_device(device, repeat_number, D) {
  const { observations, tests } = cases(device);
  const arms = {};
  await Promise.all(Object.entries(ARMS).map(async ([name, arm]) => { arms[name] = await arm(D, device, observations, tests); }));
  // Mark which tests the rival (separate counts) gets wrong, so each arm's graded list can be split by it.
  for (const a of Object.values(arms)) for (const g of a.graded) { const t = tests.find(x => x.name === g.test); g.rival_wrong = !!(t && t.rival_wrong); }
  return { device: device.id, repeat: repeat_number, guesser: D.MODEL_NAME, observations: observations.length, observations_rival_wrong: observations.filter(o => o.rival_wrong).length,
    tests: tests.map(t => ({ name: t.name, length: t.events.length, long: t.long, hard: t.hard, rival_wrong: t.rival_wrong, see: t.see })), arms };
}

function summarise(records) {
  const devices = [...new Set(records.map(r => r.device))];
  const lines = ['| Device | Arm | Runs | Long tests right | Short tests right | Hard tests right | Rival-wrong tests right | Runs fitting every observation | Replies cut off | Output tokens |', '|---|---|---|---|---|---|---|---|---|---|'];
  for (const d of devices) for (const arm of Object.keys(ARMS)) {
    const rs = records.filter(r => r.device === d && r.arms[arm]);
    const all = rs.flatMap(r => r.arms[arm].graded);
    const count = f => `${all.filter(g => f(g) && g.right).length}/${all.filter(f).length}`;
    lines.push(`| ${d} | ${arm} | ${rs.length} | ${count(g => g.long)} | ${count(g => !g.long)} | ${count(g => g.hard)} | ${d === 'peg tube' ? count(g => g.rival_wrong) : '-'} | ${rs.filter(r => r.arms[arm].best_passes === r.arms[arm].observations).length}/${rs.length} | ${rs.reduce((s, r) => s + (r.arms[arm].cut_off || 0), 0)} | ${rs.reduce((s, r) => s + r.arms[arm].tokens_out, 0)} |`);
  }
  const shapes = ['', 'Growing language, the best model of each run: new kinds, new things, rules, and the kinds\' expressions (changes and tests):', ''];
  for (const r of records) { const a = r.arms['growing language']; if (a) shapes.push(`- ${r.device} repeat ${r.repeat}: ${a.shape ? `${a.shape.kinds} kinds, ${a.shape.new_things} new things, ${a.shape.rules} rules, ${a.shape.kind_expressions} expressions` : 'no model'}; fits ${a.best_passes} of ${a.observations}`); }
  return lines.concat(shapes).join('\n');
}
const results_text = (records, failed) => `# A language that grows: results\n\nDeepSeek V4.1 Flash, default thinking. ${records.length} device-and-repeat runs; every number comes from the records in this folder. "Rival-wrong" tests are the peg-tube cases that separate counts of each colour get wrong.\n\n${summarise(records)}\n${failed.length ? `\nRuns that failed:\n${failed.join('\n')}\n` : ''}`;

// After the run (log 35): two rule models counted in binary (eight things of 0 or 1), which wraps round at
// 256, and one counted from -100 to 100. No planned test reached either edge; these do. Added after reading
// the results.
const PROBES = {
  'balance gate': {
    '256 pushes': repeat(256, 'push'),
    '300 pushes then 44 pulls': repeat(300, 'push').concat(repeat(44, 'pull')),
    '150 pushes then 150 pulls': repeat(150, 'push').concat(repeat(150, 'pull')),
    '1000 pushes then 1000 pulls': repeat(1000, 'push').concat(repeat(1000, 'pull')),
  },
  'peg tube': {
    '50 in by the pattern, then out in the right order': pattern_in(50).concat(right_order_out(50)),
    '50 red in, blue in, 50 red out': repeat(50, 'red in').concat(['blue in'], repeat(50, 'red out')),
  },
};
function probe_after_run(records) {
  const out = [];
  for (const r of records) {
    const device = DEVICES.find(d => d.id === r.device);
    const probes = PROBES[r.device];
    if (!probes) continue;
    const thing = Object.keys(device.visible)[0];
    const list = Object.entries(probes).map(([name, events]) => ({ name, events, see: device.truth(events) }));
    const row = { device: r.device, repeat: r.repeat, probes: list.map(p => ({ probe: p.name, truth: p.see[thing] })) };
    const fixed = r.arms['fixed language'], growing = r.arms['growing language'], universal = r.arms['universal language'];
    const C = require('./03 checker.js');
    if (fixed.best_round) {
      const raw = fixed.rounds.find(x => x.round === fixed.best_round).model;
      const model = C.prepare_model(raw);
      list.forEach((p, i) => {
        const job = C.prepare_jobs({ jobs: [{ name: 'probe', events: p.events, expect: [] }] }).jobs[0];
        const res = C.run(model, C.resolve_situation(model, job.situation, [], 'probe'));
        row.probes[i].fixed_language = [...new Set(res.final_states.map(st => st[thing]))].join('/');
      });
    } else list.forEach((p, i) => { row.probes[i].fixed_language = 'no model'; });
    const g = growing.best_round ? check_growing(device, growing.rounds.find(x => x.round === growing.best_round).model, list).results : null;
    const u = universal.best_round ? X.check_program(device, universal.rounds.find(x => x.round === universal.best_round).code, list) : null;
    list.forEach((p, i) => {
      row.probes[i].growing_language = g ? (g[i].got || g[i].problem) : 'no model';
      row.probes[i].universal_language = u ? (u[i].got || u[i].problem) : 'no function';
    });
    out.push(row);
  }
  return out;
}

module.exports = { PROBES, probe_after_run, DEVICES, GATE, PEGS, GRUDGE, cases, separate_counts, read_growing_model, run_growing, check_growing, growing_language, run_device, summarise, GROWTH_GUIDE, shape_of };

if (require.main === module) {
  const [first, second] = process.argv.slice(2);
  if (first === '--probe') {
    const records = fs.readdirSync(second).filter(f => / repeat \d+\.json$/.test(f)).sort().map(f => JSON.parse(fs.readFileSync(path.join(second, f), 'utf8')));
    const probes = probe_after_run(records);
    fs.writeFileSync(path.join(second, 'probes after the run.json'), JSON.stringify(probes, null, 1) + '\n');
    for (const p of probes) console.log(`${p.device} repeat ${p.repeat}: ${p.probes.map(x => `${x.probe}: truth ${x.truth}, rules ${x.fixed_language}, growing ${x.growing_language}, JavaScript ${x.universal_language}`).join('; ')}`);
  } else if (first === '--summarise') {
    const records = fs.readdirSync(second).filter(f => / repeat \d+\.json$/.test(f)).sort().map(f => JSON.parse(fs.readFileSync(path.join(second, f), 'utf8')));
    const text = results_text(records, []);
    fs.writeFileSync(path.join(second, 'results.md'), text);
    console.log(text);
  } else {
    const D = require('./17 DeepSeek guesser.js');
    const REPEATS = Number(second) || 1;
    fs.mkdirSync(first, { recursive: true });
    (async () => {
      const jobs = [];
      for (const d of DEVICES) for (let r = 1; r <= REPEATS; r++) jobs.push([d, r]);
      const records = await Promise.all(jobs.map(async ([d, r]) => {
        try {
          const rec = await run_device(d, r, D);
          fs.writeFileSync(path.join(first, `${d.id} repeat ${r}.json`), JSON.stringify(rec, null, 1) + '\n');
          console.log(`${d.id} repeat ${r} done`);
          return rec;
        } catch (e) { console.log(`${d.id} repeat ${r} failed: ${e.message}`); return { device: d.id, repeat: r, failed: String(e.message) }; }
      }));
      const text = results_text(records.filter(r => !r.failed), records.filter(r => r.failed).map(r => `- ${r.device} repeat ${r.repeat}: ${r.failed}`));
      fs.writeFileSync(path.join(first, 'results.md'), text);
      console.log(text);
    })();
  }
}
