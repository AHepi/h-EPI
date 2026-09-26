/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Log 34. Does the language an explanation is written in have to be able to express it? The checker's
 * rule language gives every thing a fixed, finite list of states, so it cannot write a count or a pile
 * with no upper limit. JavaScript can express any computation. Same DeepSeek, same observations, same
 * criticism, two languages, and a bare arm answering in words:
 *   fixed language      - DeepSeek writes a rule model; the checker runs it on every observation and
 *                         reports which fail and how; up to 6 models; the best is graded on the tests
 *   universal language  - the same loop, but DeepSeek writes a JavaScript function from the list of
 *                         actions to what can be seen; it runs in a separate process with no access to
 *                         files, the network or the account key, and with a time limit
 *   bare                - DeepSeek answers the test cases directly, as in log 25
 * Three devices: the balance gate (needs a count with no limit), the peg tube (needs a pile with no
 * limit) and log 25's grudge (a control whose explanation fits the rule language).
 * The plan and conjectures: "34 Plan - can the language express it.md".
 *
 * Run with:
 *   DEEPSEEK_API_KEY=... NODE_USE_ENV_PROXY=1 node "34 language test.js" OUTFOLDER [REPEATS]
 *   node "34 language test.js" --summarise FOLDER
 */
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');
const C = require('./03 checker.js');
const L = require('./09 loop.js');
const K = require('./25 construction worlds.js');

const ROUNDS = 6;
const HIDDEN_HINT = 'Keep track of anything you cannot see directly, if you need to.';
const ANY_LENGTH = 'Your explanation will be tested on sequences of any length, including sequences of a hundred actions.';
const lower = t => String(t == null ? '' : t).trim().toLowerCase();

// A fixed scramble: the same order every time, from the words alone.
function scramble_key(text) {
  let h = 2166136261;
  for (const ch of text) { h ^= ch.charCodeAt(0); h = Math.imul(h, 16777619) >>> 0; }
  return h;
}
const repeat = (n, action) => Array(n).fill(action);

// ------------------------------------------------------------------
// The devices
// ------------------------------------------------------------------
const GATE = {
  id: 'balance gate',
  request: 'A gate has a push handle and a pull handle. You can push it or pull it. All you can see is whether the gate is open or shut.',
  visible: { gate: ['open', 'shut'] },
  actions: ['push', 'pull'],
  truth(events) { let d = 0; for (const e of events) d += e === 'push' ? 1 : -1; return { gate: d === 0 ? 'open' : 'shut' }; },
  obvious(events) { let s = 'open'; for (const e of events) s = e === 'push' ? 'shut' : 'open'; return { gate: s }; },
  longest: 6, observations_per_outcome: 10, short_tests_per_outcome: 3,
  long_tests: () => [
    repeat(30, 'push').concat(repeat(30, 'pull')),
    repeat(30, 'push').concat(repeat(29, 'pull')),
    repeat(20, 'pull').concat(repeat(20, 'push')),
    Array.from({ length: 50 }, (_, i) => (i % 2 ? 'pull' : 'push')),
    repeat(25, 'push').concat(repeat(10, 'pull'), repeat(15, 'pull')),
    repeat(40, 'push').concat(repeat(41, 'pull')),
  ],
};

const peg_colour = i => ((i * 7) % 3 === 0 ? 'blue' : 'red');
const pegs_in = (from, n) => Array.from({ length: n }, (_, i) => `${peg_colour(from + i)} in`);
// Take out the pegs put in as colours from..from+n-1, top first; "wrong" is the removal number (1-based) that takes the other colour.
function pegs_out(from, n, count = n, wrong = 0) {
  const out = [];
  for (let k = 0; k < count; k++) {
    const colour = peg_colour(from + n - 1 - k);
    out.push(`${k + 1 === wrong ? (colour === 'red' ? 'blue' : 'red') : colour} out`);
  }
  return out;
}
const PEGS = {
  id: 'peg tube',
  request: 'A narrow tube takes coloured pegs. You can slide a red peg in, slide a blue peg in, take a red peg out, or take a blue peg out. A light on the tube shows green, amber or red.',
  visible: { light: ['green', 'amber', 'red'] },
  actions: ['red in', 'blue in', 'red out', 'blue out'],
  truth(events) {
    const pile = [];
    for (const e of events) {
      const [colour, way] = e.split(' ');
      if (way === 'in') { pile.push(colour); continue; }
      if (!pile.length || pile[pile.length - 1] !== colour) return { light: 'red' }; // jammed for good
      pile.pop();
    }
    return { light: pile.length ? 'amber' : 'green' };
  },
  obvious(events) { let n = 0; for (const e of events) n += e.endsWith(' in') ? 1 : -1; return { light: n < 0 ? 'red' : n > 0 ? 'amber' : 'green' }; },
  longest: 4, observations_per_outcome: 8, short_tests_per_outcome: 2,
  long_tests: () => [
    pegs_in(0, 12).concat(pegs_out(0, 12)),
    pegs_in(0, 12).concat(pegs_out(0, 12, 11)),
    pegs_in(0, 12).concat(pegs_out(0, 12, 12, 7)),
    pegs_in(0, 15).concat(pegs_out(0, 15)),
    pegs_in(0, 10).concat(pegs_out(0, 10, 5), pegs_in(5, 5), pegs_out(5, 5), pegs_out(0, 5)),
    pegs_in(0, 12).concat(pegs_out(0, 12, 12, 12)),
  ],
};

// The grudge: log 25's device, observations and test cases exactly.
const grudge_device = K.DEVICES.find(d => d.id === 'grudge');
const as_state = line => { const m = /^(.+?) is (.+)$/.exec(line); return m ? { [m[1]]: m[2] } : {}; };
const GRUDGE = {
  id: 'grudge',
  request: grudge_device.request,
  visible: { mood: grudge_device.world.things.mood },
  actions: grudge_device.world.events,
  truth: events => as_state(K.ending(grudge_device, events)[0]),
  obvious: events => {
    const model = C.prepare_model(grudge_device.obvious);
    const job = C.prepare_jobs({ jobs: [{ name: 'x', events, expect: [] }] }).jobs[0];
    const r = C.run(model, C.resolve_situation(model, job.situation, [], 'x'));
    return { mood: r.final_states[r.final_states.length - 1].mood };
  },
};
const DEVICES = [GATE, PEGS, GRUDGE];

const case_of = (device, name, events, long) => {
  const see = device.truth(events);
  const thing = Object.keys(device.visible)[0];
  return { name, events, see, hard: device.obvious(events)[thing] !== see[thing], long };
};
// Observations and test cases, by the plan's fixed rules.
function cases(device) {
  if (device.id === 'grudge') {
    const { observations, tests } = K.observations_and_tests(grudge_device);
    const convert = (list, long) => list.map(o => ({ name: o.name, events: o.events, see: as_state(o.expect[0]), hard: !o.obvious_right, long }));
    return { observations: convert(observations, false), tests: convert(tests, false) };
  }
  const thing = Object.keys(device.visible)[0];
  const shuffled = K.sequences(device.actions, device.longest).sort((a, b) => scramble_key(`${device.id}|${a.join('>')}`) - scramble_key(`${device.id}|${b.join('>')}`));
  const observations = [], short_tests = [];
  for (const state of device.visible[thing]) {
    const with_state = shuffled.filter(events => device.truth(events)[thing] === state);
    observations.push(...with_state.slice(0, device.observations_per_outcome));
    short_tests.push(...with_state.slice(device.observations_per_outcome, device.observations_per_outcome + device.short_tests_per_outcome));
  }
  observations.sort((a, b) => scramble_key(a.join('>')) - scramble_key(b.join('>')));
  return {
    observations: observations.map((events, i) => case_of(device, `observation ${i + 1}`, events, false)),
    tests: short_tests.map((events, i) => case_of(device, `test ${i + 1}`, events, false))
      .concat(device.long_tests().map((events, i) => case_of(device, `test ${short_tests.length + i + 1}`, events, true))),
  };
}

// ------------------------------------------------------------------
// Words
// ------------------------------------------------------------------
const see_words = see => Object.entries(see).map(([t, s]) => `${t} is ${s}`).join(' and ');
function evidence_in_words(device, observations) {
  const things = Object.entries(device.visible).map(([t, s]) => `${t} (${s.join(', ')})`).join('; ');
  return `${device.request}\n\nWhat you can see: ${things}. Actions: ${device.actions.join(', ')}. Every observation starts fresh, from the same starting point. ${HIDDEN_HINT} ${ANY_LENGTH}\n\nObservations:\n${observations.map(o => `- ${o.name}: ${o.events.join(', ')}. At the end: ${see_words(o.see)}.`).join('\n')}`;
}
const questions_in_words = (device, tests) => tests.map((t, i) => `T${i + 1}: ${t.events.join(', ')}. At the end, what is the ${Object.keys(device.visible).join(' and the ')}?`).join('\n');

// ------------------------------------------------------------------
// Running a JavaScript function in a separate process: no files, no network, no account key, a time limit
// ------------------------------------------------------------------
const RUNNER = `
const vm = require('vm');
let input = '';
process.stdin.on('data', d => { input += d; });
process.stdin.on('end', () => {
  const { code, cases } = JSON.parse(input);
  const out = [];
  let context;
  try {
    context = vm.createContext({});
    vm.runInContext(code, context, { timeout: 1000 });
    if (vm.runInContext('typeof visible', context) !== 'function') throw new Error('no function named visible');
  } catch (e) { process.stdout.write(JSON.stringify({ error: String(e && e.message || e) })); return; }
  for (const actions of cases) {
    try {
      context.__actions = JSON.stringify(actions);
      out.push({ value: vm.runInContext('JSON.stringify(visible(JSON.parse(__actions)))', context, { timeout: 500 }) });
    } catch (e) { out.push({ error: String(e && e.message || e).slice(0, 200) }); }
  }
  process.stdout.write(JSON.stringify({ results: out }));
});`;
function run_program(code, list_of_actions) {
  const done = spawnSync(process.execPath, ['-e', RUNNER], { input: JSON.stringify({ code, cases: list_of_actions }), env: {}, cwd: os.tmpdir(), timeout: 30000, maxBuffer: 16 * 1024 * 1024, encoding: 'utf8' });
  if (done.error || done.status !== 0) return { error: done.error ? `the program did not finish (${done.error.code || done.error.message})` : `the program stopped: ${String(done.stderr).slice(0, 200)}` };
  try { return JSON.parse(done.stdout); } catch (e) { return { error: 'the program gave no readable result' }; }
}
// What a function gave, read as the visible thing's state, or a problem.
function read_result(device, r) {
  const thing = Object.keys(device.visible)[0];
  if (!r || r.error) return { problem: r ? r.error : 'no result' };
  let value;
  try { value = JSON.parse(r.value); } catch (e) { return { problem: 'the result is not readable' }; }
  const state = value && typeof value === 'object' ? value[thing] : undefined;
  if (!device.visible[thing].includes(state)) return { problem: `it gave ${JSON.stringify(value)}, not ${thing} as one of ${device.visible[thing].join(', ')}` };
  return { state };
}
function check_program(device, code, list) {
  const thing = Object.keys(device.visible)[0];
  const ran = run_program(code, list.map(c => c.events));
  if (ran.error) return list.map(c => ({ name: c.name, right: false, problem: ran.error }));
  return list.map((c, i) => {
    const got = read_result(device, ran.results[i]);
    return { name: c.name, right: got.state === c.see[thing], got: got.state, problem: got.problem };
  });
}
function read_program(text) {
  const blocks = [...String(text || '').matchAll(/```(?:javascript|js)?\s*\n([\s\S]*?)```/gi)].map(m => m[1]);
  const block = blocks.reverse().find(b => /function\s+visible|visible\s*=/.test(b));
  if (block) return block.trim();
  const reply = L.read_reply(text);
  return reply && typeof reply.program === 'string' ? reply.program : null;
}

// ------------------------------------------------------------------
// The arms
// ------------------------------------------------------------------
const jobs_of = list => C.prepare_jobs({ jobs: list.map(c => ({ name: c.name, events: c.events, expect: [see_words(c.see)] })) }).jobs;
function grade_rules(model, tests) {
  const passed = new Set(C.check(model, jobs_of(tests)).passed);
  return tests.map(t => ({ test: t.name, hard: t.hard, long: t.long, right: passed.has(t.name) }));
}
// The size of the largest thing the model keeps that cannot be seen: how far a rule model can count.
const largest_hidden = (device, model) => Math.max(0, ...Object.entries(model.things || {}).filter(([t]) => !device.visible[t]).map(([, s]) => s.length));

async function fixed_language(D, device, observations, tests) {
  const g = D.make_deepseek_guesser();
  const jobs = jobs_of(observations);
  const opening = `Task: ${evidence_in_words(device, observations)}\n\nWrite a model that explains every observation. Use exactly the names above for what you can see and for the actions.`;
  const rounds = [];
  let best = null, current = null;
  for (let round = 1; round <= ROUNDS; round++) {
    const ask = current ? `${opening}\n\nYour last model:\n${JSON.stringify(C.model_to_form(current))}\n\nThe checker ran it on the observations.\n${C.report_check(current, jobs).text}\n\nWrite the whole model again so that every observation holds. You may add things you cannot see.` : opening;
    const raw = L.read_reply(await g([{ role: 'system', content: L.GUIDE }, { role: 'user', content: ask }], {}));
    const model = raw ? C.prepare_model(raw) : null;
    const passed = model ? C.check(model, jobs).passed.length : 0;
    rounds.push({ round, readable: !!model, passed, largest_hidden: model ? largest_hidden(device, model) : 0, model: raw });
    if (model) { current = model; if (!best || passed > best.passed) best = { model, passed, round }; }
    if (model && passed === jobs.length) break;
  }
  return {
    rounds, best_round: best ? best.round : null, best_passes: best ? best.passed : 0, observations: jobs.length,
    largest_hidden: best ? largest_hidden(device, best.model) : 0,
    graded: best ? grade_rules(best.model, tests) : tests.map(t => ({ test: t.name, hard: t.hard, long: t.long, right: false })),
    tokens_out: g.counts.tokens_out, cut_off: g.counts.cut_off, calls: rounds.length,
  };
}

const PROGRAM_SYSTEM = 'You write small JavaScript programs that a checker can run.';
async function universal_language(D, device, observations, tests) {
  const g = D.make_deepseek_guesser();
  const thing = Object.keys(device.visible)[0];
  const opening = `Task: ${evidence_in_words(device, observations)}\n\nWrite a JavaScript function named visible that takes the list of actions, in order, as an array of strings, starting fresh, and returns what can be seen at the end as an object, such as {"${thing}": "${device.visible[thing][0]}"}. Use exactly the names above. You may keep track of anything you cannot see. Use no outside libraries. Reply with the function in one \`\`\`javascript code block.`;
  const rounds = [];
  let best = null, current = null;
  for (let round = 1; round <= ROUNDS; round++) {
    let ask = opening;
    if (current) {
      const failing = current.checked.filter(c => !c.right);
      const lines = failing.map(c => { const o = observations.find(x => x.name === c.name); return `- ${c.name}: ${o.events.join(', ')}. Observed: ${see_words(o.see)}. Your function: ${c.problem ? c.problem : `${thing} is ${c.got}`}.`; });
      ask = `${opening}\n\nYour last function:\n\`\`\`javascript\n${current.code}\n\`\`\`\n\nThe checker ran it on the observations. ${observations.length - failing.length} of ${observations.length} hold. These do not:\n${lines.join('\n')}\n\nWrite the whole function again so that every observation holds.`;
    }
    const text = await g([{ role: 'system', content: PROGRAM_SYSTEM }, { role: 'user', content: ask }], { reply_shape: 'none' });
    const code = read_program(text);
    const checked = code ? check_program(device, code, observations) : null;
    const passed = checked ? checked.filter(c => c.right).length : 0;
    rounds.push({ round, readable: !!code, passed, code });
    if (code) { current = { code, checked }; if (!best || passed > best.passed) best = { code, passed, round }; }
    if (code && passed === observations.length) break;
  }
  const graded = best ? check_program(device, best.code, tests).map((c, i) => ({ test: tests[i].name, hard: tests[i].hard, long: tests[i].long, right: c.right, problem: c.problem })) : tests.map(t => ({ test: t.name, hard: t.hard, long: t.long, right: false }));
  return { rounds, best_round: best ? best.round : null, best_passes: best ? best.passed : 0, observations: observations.length, graded, tokens_out: g.counts.tokens_out, cut_off: g.counts.cut_off, calls: rounds.length };
}

async function bare(D, device, observations, tests) {
  const g = D.make_deepseek_guesser();
  const thing = Object.keys(device.visible)[0];
  const text = await g([{ role: 'user', content: `${evidence_in_words(device, observations)}\n\nPredict these new cases, which also start fresh:\n${questions_in_words(device, tests)}\n\nReply with JSON: {"rule": "your explanation in a sentence or two", "answers": {"T1": "STATE", "T2": "STATE"}}, with one answer per test, each one of: ${device.visible[thing].join(', ')}.` }], { reply_shape: 'none' });
  const reply = L.read_reply(text);
  const answers = reply && reply.answers ? reply.answers : {};
  const graded = tests.map((t, i) => { const said = answers[`T${i + 1}`]; return { test: t.name, hard: t.hard, long: t.long, right: lower(typeof said === 'object' && said ? Object.values(said)[0] : said) === lower(t.see[thing]) }; });
  return { rule: reply ? reply.rule : null, graded, tokens_out: g.counts.tokens_out, cut_off: g.counts.cut_off, calls: 1 };
}

const ARMS = { 'fixed language': fixed_language, 'universal language': universal_language, 'bare': bare };
async function run_device(device, repeat, D) {
  const { observations, tests } = cases(device);
  const arms = {};
  await Promise.all(Object.entries(ARMS).map(async ([name, arm]) => { arms[name] = await arm(D, device, observations, tests); }));
  return { device: device.id, repeat, guesser: D.MODEL_NAME, observations: observations.length, tests: tests.map(t => ({ name: t.name, length: t.events.length, long: t.long, hard: t.hard, see: t.see })), arms };
}

function summarise(records) {
  const devices = [...new Set(records.map(r => r.device))];
  const lines = ['| Device | Arm | Runs | Long tests right | Short tests right | Hard tests right | Runs fitting every observation | Largest hidden thing (fixed language) | Output tokens |', '|---|---|---|---|---|---|---|---|---|'];
  for (const d of devices) for (const arm of Object.keys(ARMS)) {
    const rs = records.filter(r => r.device === d && r.arms[arm]);
    const all = rs.flatMap(r => r.arms[arm].graded);
    const count = f => `${all.filter(g => f(g) && g.right).length}/${all.filter(f).length}`;
    const fit = arm === 'bare' ? '-' : `${rs.filter(r => r.arms[arm].best_passes === r.arms[arm].observations).length}/${rs.length}`;
    const hidden = arm === 'fixed language' ? rs.map(r => r.arms[arm].largest_hidden).join(', ') : '-';
    lines.push(`| ${d} | ${arm} | ${rs.length} | ${count(g => g.long)} | ${count(g => !g.long)} | ${count(g => g.hard)} | ${fit} | ${hidden} | ${rs.reduce((s, r) => s + r.arms[arm].tokens_out, 0)} |`);
  }
  return lines.join('\n');
}
const results_text = (records, failed) => `# Can the language express it: results\n\nDeepSeek V4.1 Flash, default thinking. ${records.length} device-and-repeat runs; every number comes from the records in this folder. "Largest hidden thing" is how many states the best rule model's largest unseen thing has, in each run: how far it can count.\n\n${summarise(records)}\n${failed.length ? `\nRuns that failed:\n${failed.join('\n')}\n` : ''}`;

module.exports = { DEVICES, GATE, PEGS, GRUDGE, cases, run_program, check_program, read_program, fixed_language, universal_language, bare, run_device, summarise, evidence_in_words, ANY_LENGTH };

if (require.main === module) {
  const [first, second] = process.argv.slice(2);
  if (first === '--summarise') {
    const records = fs.readdirSync(second).filter(f => f.endsWith('.json')).sort().map(f => JSON.parse(fs.readFileSync(path.join(second, f), 'utf8')));
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
