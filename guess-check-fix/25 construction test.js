/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Log 25. Can error correction, in the sense of the semantics (conjecture, criticism, construction of a
 * new explanation), get DeepSeek to solve problems a bare run cannot, even when the bare run is repeated
 * or loops over its own work?
 *
 * The problems are the made-up devices of "25 construction worlds.js". Every arm gets the same evidence:
 * the device's description and its 14 observations. No arm may ask for anything more. Every arm is told
 * the same thing about what it cannot see: "Keep track of anything you cannot see directly, if you need
 * to." Every arm is graded on the same 12 unseen test cases (8 that the obvious explanation gets wrong).
 *
 * Arms, per device and repeat, all DeepSeek V4.1 Flash at its default thinking setting:
 *   bare                  - answers the test cases directly, once
 *   bare, majority of 5   - five bare answers; each test case gets the answer most of them gave
 *   bare, checks itself   - states its rule and answers; then three times: "check your rule against every
 *                           observation, one by one, revise it if any disagree, and answer again"
 *   conjecture and criticism - writes an explanation as a model the checker can run; the checker runs it on
 *                           every observation and reports exactly which fail and what the model said
 *                           instead; DeepSeek writes a new explanation; up to 6 explanations. The one
 *                           that fits the most observations answers the test cases, by being run.
 *   blind retries         - the same, but the report says only how many observations fail
 * For the two model arms, "reach" is also measured: of all sequences of up to four actions (120, or 30 for
 * the gate, which has two actions), how many the final explanation gets right.
 *
 * Run with:
 *   DEEPSEEK_API_KEY=... NODE_USE_ENV_PROXY=1 node "25 construction test.js" OUTFOLDER [REPEATS] [DEVICE,DEVICE]
 *   node "25 construction test.js" --summarise FOLDER
 */
const fs = require('fs');
const path = require('path');
const C = require('./03 checker.js');
const L = require('./09 loop.js');
const K = require('./25 construction worlds.js');

const ROUNDS = 6;
const SELF_CHECKS = 3;
const MAJORITY = 5;
const HIDDEN_HINT = 'Keep track of anything you cannot see directly, if you need to.';
const lower = t => String(t).trim().toLowerCase();

function evidence_in_words(device, observations) {
  const things = device.visible.map(t => `${t} (${device.world.things[t].join(', ')})`).join('; ');
  return `${device.request}\n\nWhat you can see: ${things}. Actions: ${device.world.events.join(', ')}. Every observation starts fresh, from the same starting point. ${HIDDEN_HINT}\n\nObservations:\n${observations.map(o => `- ${o.name}: ${o.events.join(', then ')}. At the end: ${o.expect.join(' and ')}.`).join('\n')}`;
}
function questions_in_words(device, tests) {
  return tests.map((t, i) => `T${i + 1}: ${t.events.join(', then ')}. At the end, what is the ${device.visible.join(' and the ')}?`).join('\n');
}
const ANSWER_SHAPE = device => `Reply with JSON: {"rule": "your explanation in a sentence or two", "answers": {"T1": "STATE", "T2": "STATE"}}, with one answer per test, each one of: ${device.world.things[device.visible[0]].join(', ')}.`;

function grade_answers(device, tests, answers) {
  return tests.map((t, i) => {
    const said = answers ? answers[`T${i + 1}`] : undefined;
    const want = t.expect[0].split(' is ')[1];
    return { test: t.name, hard: !t.obvious_right, right: lower(typeof said === 'object' && said ? Object.values(said)[0] : said) === lower(want) };
  });
}
function grade_model(device, tests, model) {
  const jobs = C.prepare_jobs({ jobs: tests }).jobs;
  const passed = new Set(C.check(model, jobs).passed);
  return tests.map(t => ({ test: t.name, hard: !t.obvious_right, right: passed.has(t.name) }));
}
function reach(device, model) {
  const all = K.sequences(device.world.events, 4).map((events, i) => ({ name: `s${i}`, events, expect: K.ending(device, events) }));
  return { right: C.check(model, C.prepare_jobs({ jobs: all }).jobs).passed.length, of: all.length };
}
const hidden_things = (device, model) => Object.keys(model.things || {}).filter(t => !device.visible.includes(t));

async function bare(D, device, observations, tests) {
  const g = D.make_deepseek_guesser();
  const text = await g([{ role: 'user', content: `${evidence_in_words(device, observations)}\n\nPredict these new cases, which also start fresh:\n${questions_in_words(device, tests)}\n\n${ANSWER_SHAPE(device)}` }], { reply_shape: 'none' });
  const reply = L.read_reply(text);
  return { reply, graded: grade_answers(device, tests, reply && reply.answers), tokens_out: g.counts.tokens_out, cut_off: g.counts.cut_off, calls: 1 };
}

async function bare_checks_itself(D, device, observations, tests) {
  const g = D.make_deepseek_guesser();
  const messages = [{ role: 'user', content: `${evidence_in_words(device, observations)}\n\nPredict these new cases, which also start fresh:\n${questions_in_words(device, tests)}\n\n${ANSWER_SHAPE(device)}` }];
  const replies = [];
  for (let round = 0; round <= SELF_CHECKS; round++) {
    if (round > 0) messages.push({ role: 'user', content: `Check your rule against every observation above, one by one, working out what your rule says for each. If any disagree with what was observed, revise the rule until none do. Then answer the test cases again. ${ANSWER_SHAPE(device)}` });
    const text = await g(messages, { reply_shape: 'none' });
    messages.push({ role: 'assistant', content: text });
    replies.push(L.read_reply(text));
  }
  const last = replies[replies.length - 1];
  return { replies, graded: grade_answers(device, tests, last && last.answers), first_graded: grade_answers(device, tests, replies[0] && replies[0].answers), tokens_out: g.counts.tokens_out, cut_off: g.counts.cut_off, calls: replies.length };
}

async function explain_and_criticise(D, device, observations, tests, blind) {
  const g = D.make_deepseek_guesser();
  const jobs = C.prepare_jobs({ jobs: observations }).jobs;
  const opening = `Task: ${evidence_in_words(device, observations)}\n\nWrite a model that explains every observation. Use exactly the names above for what you can see and for the actions.`;
  const rounds = [];
  let best = null;
  let current = null;
  for (let round = 1; round <= ROUNDS; round++) {
    let ask = opening;
    if (current) {
      const check = C.check(current.model, jobs);
      const report = blind ? `${check.failed.length} of ${jobs.length} observations do not hold.` : C.report_check(current.model, jobs).text;
      ask = `${opening}\n\nYour last model:\n${JSON.stringify(C.model_to_form(current.model))}\n\nThe checker ran it on the observations.\n${report}\n\nWrite the whole model again so that every observation holds. You may add things you cannot see.`;
    }
    const text = await g([{ role: 'system', content: L.GUIDE }, { role: 'user', content: ask }], {});
    const raw = L.read_reply(text);
    const model = raw ? C.prepare_model(raw) : null;
    const passed = model ? C.check(model, jobs).passed.length : 0;
    rounds.push({ round, readable: !!model, passed, hidden_things: model ? hidden_things(device, model) : [], model: raw });
    if (model) { current = { model, passed }; if (!best || passed >= best.passed) best = { model, passed, round }; }
    if (model && passed === jobs.length) break;
  }
  const graded = best ? grade_model(device, tests, best.model) : tests.map(t => ({ test: t.name, hard: !t.obvious_right, right: false }));
  return { rounds, best_round: best ? best.round : null, best_passes: best ? best.passed : 0, observations: jobs.length, final_hidden_things: best ? hidden_things(device, best.model) : [],
    reach: best ? reach(device, best.model) : { right: 0, of: 120 }, graded, tokens_out: g.counts.tokens_out, cut_off: g.counts.cut_off, calls: rounds.length };
}

function majority(device, tests, replies) {
  const answers = {};
  tests.forEach((t, i) => {
    const votes = {};
    for (const r of replies) { const a = r && r.answers ? lower(r.answers[`T${i + 1}`]) : ''; if (a) votes[a] = (votes[a] || 0) + 1; }
    const top = Object.entries(votes).sort((a, b) => b[1] - a[1])[0];
    if (top) answers[`T${i + 1}`] = top[0];
  });
  return answers;
}

async function run_device(device, repeat, D) {
  const { observations, tests } = K.observations_and_tests(device);
  const arms = {};
  const once = [];
  for (let i = 0; i < MAJORITY; i++) once.push(await bare(D, device, observations, tests));
  arms['bare'] = once[0];
  arms['bare, majority of 5'] = { graded: grade_answers(device, tests, majority(device, tests, once.map(o => o.reply))), tokens_out: once.reduce((s, o) => s + o.tokens_out, 0), cut_off: once.reduce((s, o) => s + o.cut_off, 0), calls: MAJORITY, each_right: once.map(o => o.graded.filter(g => g.right).length) };
  arms['bare, checks itself'] = await bare_checks_itself(D, device, observations, tests);
  arms['conjecture and criticism'] = await explain_and_criticise(D, device, observations, tests, false);
  arms['blind retries'] = await explain_and_criticise(D, device, observations, tests, true);
  return { device: device.id, repeat, guesser: D.MODEL_NAME, observations, tests, arms };
}

const ARMS = ['bare', 'bare, majority of 5', 'bare, checks itself', 'conjecture and criticism', 'blind retries'];
function summarise(records) {
  const lines = ['| Arm | Test cases right | Of the 8 hard ones per run | Of the 4 easy ones per run | Runs with every test right | DeepSeek calls | Output tokens | Replies cut off |', '|---|---|---|---|---|---|---|---|'];
  for (const n of ARMS) {
    const t = { right: 0, all: 0, hard: 0, hard_all: 0, easy: 0, easy_all: 0, perfect: 0, runs: 0, calls: 0, tokens: 0, cut: 0 };
    for (const r of records) {
      const a = r.arms[n]; if (!a) continue;
      t.runs++; t.calls += a.calls; t.tokens += a.tokens_out; t.cut += a.cut_off;
      for (const g of a.graded) { t.all++; if (g.right) t.right++; if (g.hard) { t.hard_all++; if (g.right) t.hard++; } else { t.easy_all++; if (g.right) t.easy++; } }
      if (a.graded.every(g => g.right)) t.perfect++;
    }
    lines.push(`| ${n} | ${t.right}/${t.all} | ${t.hard}/${t.hard_all} | ${t.easy}/${t.easy_all} | ${t.perfect}/${t.runs} | ${t.calls} | ${t.tokens} | ${t.cut} |`);
  }
  const by_device = ['', 'Test cases right (of 12), by device and repeat:', '', `| Device | Repeat | ${ARMS.join(' | ')} |`, `|---|---|${ARMS.map(() => '---').join('|')}|`];
  for (const r of records) by_device.push(`| ${r.device} | ${r.repeat} | ${ARMS.map(n => (r.arms[n] ? r.arms[n].graded.filter(g => g.right).length : '')).join(' | ')} |`);
  const loops = ['', 'The two explanation arms: observations explained by the best explanation (of 14), its round, the hidden things it built, and its reach (of all sequences of up to four actions):', '', '| Device | Repeat | Arm | Explained | Round | Hidden things | Reach |', '|---|---|---|---|---|---|---|'];
  for (const r of records) for (const n of ['conjecture and criticism', 'blind retries']) {
    const a = r.arms[n]; if (!a) continue;
    loops.push(`| ${r.device} | ${r.repeat} | ${n} | ${a.best_passes}/${a.observations} | ${a.best_round || '-'} | ${a.final_hidden_things.join(', ') || 'none'} | ${a.reach.right}/${a.reach.of} |`);
  }
  return lines.concat(by_device, loops).join('\n');
}
const results_text = (records, failed) => `# Construction test: results\n\nDeepSeek V4.1 Flash, default thinking. ${records.length} device-and-repeat runs; every number comes from the records in this folder. Every arm had the same description and 14 observations; the 12 test cases were shown to none of them.\n\n${summarise(records)}\n${failed.length ? `\nRuns that failed:\n${failed.join('\n')}\n` : ''}`;

module.exports = { evidence_in_words, questions_in_words, grade_answers, grade_model, reach, majority, bare, bare_checks_itself, explain_and_criticise, run_device, summarise, HIDDEN_HINT };

if (require.main === module) {
  const [first, second, third] = process.argv.slice(2);
  if (first === '--summarise') {
    const records = fs.readdirSync(second).filter(f => f.endsWith('.json')).sort().map(f => JSON.parse(fs.readFileSync(path.join(second, f), 'utf8')));
    const text = results_text(records, []);
    fs.writeFileSync(path.join(second, 'results.md'), text);
    console.log(text);
  } else {
    const D = require('./17 DeepSeek guesser.js');
    const devices = K.DEVICES.filter(d => !third || third.split(',').includes(d.id));
    const REPEATS = Number(second) || 1;
    const START = Number(process.env.FIRST_REPEAT) || 1;
    fs.mkdirSync(first, { recursive: true });
    (async () => {
      const jobs = [];
      for (const d of devices) for (let r = START; r < START + REPEATS; r++) jobs.push([d, r]);
      const records = await Promise.all(jobs.map(async ([d, r]) => {
        try {
          const rec = await run_device(d, r, D);
          fs.writeFileSync(path.join(first, `${d.id} repeat ${r}.json`), JSON.stringify(rec, null, 1) + '\n');
          console.log(`${d.id} repeat ${r} done`);
          return rec;
        } catch (e) { console.log(`${d.id} repeat ${r} failed: ${e.message}`); return { device: d.id, repeat: r, failed: String(e.message) }; }
      }));
      const all = fs.readdirSync(first).filter(f => f.endsWith('.json')).sort().map(f => JSON.parse(fs.readFileSync(path.join(first, f), 'utf8')));
      const text = results_text(all, records.filter(r => r.failed).map(r => `- ${r.device} repeat ${r.repeat}: ${r.failed}`));
      fs.writeFileSync(path.join(first, 'results.md'), text);
      console.log(text);
    })();
  }
}
