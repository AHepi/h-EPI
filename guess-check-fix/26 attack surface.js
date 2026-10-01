/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Log 26. The owner's idea: a conjecture is worthless without an attack surface. Make DeepSeek commit, in
 * advance, to what would cast doubt on its conjecture; test those commitments; and do not feed the attack
 * back to it, because it will defend its first answer.
 *
 * Read against the semantics (see "26 Plan - attack surface.md"): DeepSeek is a selected transport, a
 * source of conjectures; asking again or rereading is selection; once its answer is in its own context,
 * the answer has become an input. So the attack lives outside it: its commitments are recorded before any
 * test, the world answers them, the verdict is a mechanical comparison, and a fresh DeepSeek rebuilds
 * from the facts alone.
 *
 * On log 25's four devices, the same 14 observations, graded on the same 12 test cases. Arms, per device
 * and repeat, each with at most 6 answers from the world:
 *   bare                     - answers the test cases from the observations (as in log 25)
 *   random answers           - the world's answers to 6 random unseen situations are added first
 *   attack, rebuild fresh    - two rounds. Each round a fresh DeepSeek states its rule and commits to 5
 *                              predictions for unseen situations, riskiest first ("if I am right, this
 *                              happens"). The world answers the 3 riskiest. A fresh DeepSeek then gets the
 *                              observations and every answer so far, never its old rule or the word
 *                              "wrong". After two rounds a fresh DeepSeek answers the test cases from the
 *                              observations and all the world's answers.
 *   attack, defend           - the same commitments and world answers, but fed back into the same
 *                              conversation ("you predicted X; the world says Y"), and the test cases are
 *                              answered there: the case the owner expects to fail.
 * The world never answers a test case; such a commitment gets "not available" and uses up its place.
 * Recorded: every commitment; whether it was risky (the obvious explanation predicts otherwise); whether
 * the world contradicted it; whether the rule changed between rounds.
 *
 * Run with (not before the owner tops up):
 *   DEEPSEEK_API_KEY=... NODE_USE_ENV_PROXY=1 node "26 attack surface.js" OUTFOLDER [REPEATS] [DEVICE,DEVICE]
 *   node "26 attack surface.js" --summarise FOLDER
 */
const fs = require('fs');
const path = require('path');
const C = require('./03 checker.js');
const L = require('./09 loop.js');
const K = require('./25 construction worlds.js');
const X = require('./25 construction test.js');

const ROUNDS = 2;
const COMMITMENTS = 5;
const TESTED_PER_ROUND = 3;
const lower = t => String(t).trim().toLowerCase();

function fact_in_words(device, events, answer) { return `- ${events.join(', then ')}. At the end: ${answer}.`; }
function evidence_with_facts(device, observations, facts) {
  return X.evidence_in_words(device, observations) + (facts.length ? `\n\nMore observations, each also from the start:\n${facts.map(f => fact_in_words(device, f.events, f.answer)).join('\n')}` : '');
}
const COMMIT_SHAPE = device => `Reply with JSON only: {"rule": "your explanation in a sentence or two", "commitments": [{"events": ["ACTION", "ACTION"], "predict": "STATE", "why": "why this would cast doubt on the rule if it came out otherwise"}]}. Give ${COMMITMENTS} commitments, riskiest first: situations not among the observations, up to four actions from the start, where your rule predicts something definite that a different rule would not. Each STATE is one of: ${device.world.things[device.visible[0]].join(', ')}.`;
const COMMIT_ASK = (device, observations, facts) => `${evidence_with_facts(device, observations, facts)}\n\nState the rule you think is at work. Then say what would cast doubt on it: the situations where, if your rule is right, a particular result must come out, and where a wrong rule would most likely show itself.\n\n${COMMIT_SHAPE(device)}`;

// The world answers a committed situation, unless it is a test case or cannot be read.
function world_answers(device, events, test_keys) {
  const known = device.world.events;
  if (!Array.isArray(events) || !events.length || events.length > 4 || events.some(e => !known.includes(e))) return { available: false, why: 'not a situation the device allows' };
  if (test_keys.has(events.join('>'))) return { available: false, why: 'not available' };
  return { available: true, answer: K.ending(device, events).join(' and ') };
}
function read_commitments(reply) {
  const list = reply && Array.isArray(reply.commitments) ? reply.commitments : [];
  return list.slice(0, COMMITMENTS).map(c => ({ events: Array.isArray(c && c.events) ? c.events.map(String) : [], predict: c && c.predict != null ? String(c.predict) : '', why: c && c.why ? String(c.why) : '' }));
}
function judge(device, commitment, test_keys) {
  const w = world_answers(device, commitment.events, test_keys);
  const allowed = Array.isArray(commitment.events) && commitment.events.length > 0 && commitment.events.length <= 4 && commitment.events.every(e => device.world.events.includes(e));
  const risky = allowed ? risky_against_obvious(device, commitment) : null;
  if (!w.available) return Object.assign({}, commitment, { tested: false, why_not: w.why, risky });
  const world_state = w.answer.split(' is ')[1];
  return Object.assign({}, commitment, { tested: true, world_says: w.answer, held: lower(commitment.predict) === lower(world_state), risky });
}
// Risky: the obvious explanation predicts something other than the commitment.
function risky_against_obvious(device, commitment) {
  const obvious = C.prepare_model(device.obvious);
  const job = C.prepare_jobs({ jobs: [{ name: 'x', events: commitment.events, expect: [`${device.visible[0]} is ${commitment.predict}`] }] }).jobs[0];
  return !C.check_job(obvious, job).passed;
}

async function attack(D, device, observations, tests, test_keys, mode) {
  const rounds = [];
  const facts = [];
  const g_defend = D.make_deepseek_guesser();
  const conversation = [];
  let tokens = 0, cut = 0;
  for (let round = 1; round <= ROUNDS; round++) {
    let text;
    if (mode === 'defend') {
      if (round === 1) conversation.push({ role: 'user', content: COMMIT_ASK(device, observations, []) });
      else conversation.push({ role: 'user', content: `Your commitments were tested:\n${rounds[rounds.length - 1].commitments.filter(c => c.tested).map(c => `- ${c.events.join(', then ')}: you predicted ${c.predict}; the world says ${c.world_says.split(' is ')[1]}.`).join('\n')}\n\nState your rule again, revised if you need to, and commit again. ${COMMIT_SHAPE(device)}` });
      text = await g_defend(conversation, { reply_shape: 'none' });
      conversation.push({ role: 'assistant', content: text });
    } else {
      const g = D.make_deepseek_guesser();
      text = await g([{ role: 'user', content: COMMIT_ASK(device, observations, facts) }], { reply_shape: 'none' });
      tokens += g.counts.tokens_out; cut += g.counts.cut_off;
    }
    const reply = L.read_reply(text);
    const commitments = read_commitments(reply).map(c => judge(device, c, test_keys));
    for (const c of commitments.slice(0, TESTED_PER_ROUND)) if (c.tested) facts.push({ events: c.events, answer: c.world_says });
    commitments.forEach((c, i) => { if (i >= TESTED_PER_ROUND) { c.tested = false; c.why_not = 'not among the three riskiest'; delete c.world_says; delete c.held; } });
    rounds.push({ round, rule: reply ? reply.rule : null, commitments, text });
  }
  let answers;
  if (mode === 'defend') {
    conversation.push({ role: 'user', content: `Your last commitments were tested:\n${rounds[rounds.length - 1].commitments.filter(c => c.tested).map(c => `- ${c.events.join(', then ')}: you predicted ${c.predict}; the world says ${c.world_says.split(' is ')[1]}.`).join('\n')}\n\nNow predict these new cases, which also start fresh:\n${X.questions_in_words(device, tests)}\n\nReply with JSON: {"rule": "your explanation", "answers": {"T1": "STATE"}}.` });
    const text = await g_defend(conversation, { reply_shape: 'none' });
    answers = L.read_reply(text);
    tokens += g_defend.counts.tokens_out; cut += g_defend.counts.cut_off;
  } else {
    const g = D.make_deepseek_guesser();
    const text = await g([{ role: 'user', content: `${evidence_with_facts(device, observations, facts)}\n\nPredict these new cases, which also start fresh:\n${X.questions_in_words(device, tests)}\n\nReply with JSON: {"rule": "your explanation", "answers": {"T1": "STATE"}}.` }], { reply_shape: 'none' });
    answers = L.read_reply(text);
    tokens += g.counts.tokens_out; cut += g.counts.cut_off;
  }
  return { rounds, facts, final_rule: answers ? answers.rule : null, graded: X.grade_answers(device, tests, answers && answers.answers), tokens_out: tokens, cut_off: cut, calls: ROUNDS + 1, world_answers: facts.length };
}

async function with_facts(D, device, observations, tests, facts) {
  const g = D.make_deepseek_guesser();
  const text = await g([{ role: 'user', content: `${evidence_with_facts(device, observations, facts)}\n\nPredict these new cases, which also start fresh:\n${X.questions_in_words(device, tests)}\n\nReply with JSON: {"rule": "your explanation", "answers": {"T1": "STATE"}}.` }], { reply_shape: 'none' });
  const reply = L.read_reply(text);
  return { rule: reply ? reply.rule : null, graded: X.grade_answers(device, tests, reply && reply.answers), tokens_out: g.counts.tokens_out, cut_off: g.counts.cut_off, calls: 1, world_answers: facts.length };
}

function random_facts(device, observations, test_keys, how_many, salt) {
  const seen = new Set(observations.map(o => o.events.join('>')));
  return K.sequences(device.world.events, 4).filter(s => !seen.has(s.join('>')) && !test_keys.has(s.join('>')))
    .map(s => ({ s, key: [...`${salt}|${s.join('>')}`].reduce((h, ch) => Math.imul(h ^ ch.charCodeAt(0), 16777619) >>> 0, 2166136261) })).sort((a, b) => a.key - b.key)
    .slice(0, how_many).map(x => ({ events: x.s, answer: K.ending(device, x.s).join(' and ') }));
}

async function run_device(device, repeat, D) {
  const { observations, tests } = K.observations_and_tests(device);
  const test_keys = new Set(tests.map(t => t.events.join('>')));
  const arms = {};
  arms['bare'] = await with_facts(D, device, observations, tests, []);
  arms['random answers'] = await with_facts(D, device, observations, tests, random_facts(device, observations, test_keys, ROUNDS * TESTED_PER_ROUND, `${device.id} attack ${repeat}`));
  arms['attack, rebuild fresh'] = await attack(D, device, observations, tests, test_keys, 'fresh');
  arms['attack, defend'] = await attack(D, device, observations, tests, test_keys, 'defend');
  return { device: device.id, repeat, guesser: D.MODEL_NAME, arms };
}

const ARMS = ['bare', 'random answers', 'attack, rebuild fresh', 'attack, defend'];
function summarise(records) {
  const lines = ['| Arm | Test cases right | Hard cases right | Answers from the world | Output tokens | Replies cut off |', '|---|---|---|---|---|---|'];
  for (const n of ARMS) {
    const t = { right: 0, all: 0, hard: 0, hard_all: 0, answers: 0, tokens: 0, cut: 0 };
    for (const r of records) { const a = r.arms[n]; if (!a) continue; a.graded.forEach(g => { t.all++; if (g.right) t.right++; if (g.hard) { t.hard_all++; if (g.right) t.hard++; } }); t.answers += a.world_answers; t.tokens += a.tokens_out; t.cut += a.cut_off; }
    lines.push(`| ${n} | ${t.right}/${t.all} | ${t.hard}/${t.hard_all} | ${t.answers} | ${t.tokens} | ${t.cut} |`);
  }
  const surface = ['', 'The attack surface: commitments made, how many were risky (the obvious explanation predicts otherwise), how many the world tested, and how many it contradicted; and how often the rule changed between rounds.', '', '| Arm | Commitments | Risky | Tested | Contradicted | Refused (a test case, or not allowed) | Rule changed between rounds |', '|---|---|---|---|---|---|---|'];
  for (const n of ['attack, rebuild fresh', 'attack, defend']) {
    const all = records.flatMap(r => (r.arms[n] ? r.arms[n].rounds.flatMap(x => x.commitments) : []));
    const changed = records.filter(r => r.arms[n] && r.arms[n].rounds.length > 1 && lower(r.arms[n].rounds[0].rule) !== lower(r.arms[n].rounds[1].rule)).length;
    surface.push(`| ${n} | ${all.length} | ${all.filter(c => c.risky).length} | ${all.filter(c => c.tested).length} | ${all.filter(c => c.tested && !c.held).length} | ${all.filter(c => c.why_not && c.why_not !== 'not among the three riskiest').length} | ${changed} of ${records.filter(r => r.arms[n]).length} |`);
  }
  const by_device = ['', 'Test cases right (of 12), by device and repeat:', '', `| Device | Repeat | ${ARMS.join(' | ')} |`, `|---|---|${ARMS.map(() => '---').join('|')}|`];
  for (const r of records) by_device.push(`| ${r.device} | ${r.repeat} | ${ARMS.map(n => (r.arms[n] ? r.arms[n].graded.filter(g => g.right).length : '')).join(' | ')} |`);
  return lines.concat(surface, by_device).join('\n');
}
const results_text = (records, failed) => `# Attack surface: results\n\nDeepSeek V4.1 Flash, default thinking, log 25's devices. ${records.length} device-and-repeat runs; every number comes from the records in this folder.\n\n${summarise(records)}\n${failed.length ? `\nRuns that failed:\n${failed.join('\n')}\n` : ''}`;

module.exports = { world_answers, read_commitments, judge, risky_against_obvious, attack, with_facts, random_facts, run_device, summarise, COMMIT_ASK };

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
    fs.mkdirSync(first, { recursive: true });
    (async () => {
      const jobs = [];
      for (const d of devices) for (let r = 1; r <= REPEATS; r++) jobs.push([d, r]);
      const records = await Promise.all(jobs.map(async ([d, r]) => {
        try { const rec = await run_device(d, r, D); fs.writeFileSync(path.join(first, `${d.id} repeat ${r}.json`), JSON.stringify(rec, null, 1) + '\n'); console.log(`${d.id} repeat ${r} done`); return rec; }
        catch (e) { console.log(`${d.id} repeat ${r} failed: ${e.message}`); return { device: d.id, repeat: r, failed: String(e.message) }; }
      }));
      const text = results_text(records.filter(r => !r.failed), records.filter(r => r.failed).map(r => `- ${r.device} repeat ${r.repeat}: ${r.failed}`));
      fs.writeFileSync(path.join(first, 'results.md'), text);
      console.log(text);
    })();
  }
}
