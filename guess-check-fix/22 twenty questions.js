/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Log 22. In log 21 DeepSeek, free to stop, almost never asked the owner anything. The owner asked:
 * make it ask 20 questions first, and see what it does.
 *
 * On log 21's long messages (about 2,300 words, one question buried in the middle), per world and repeat:
 *   must ask 20          - DeepSeek asks the owner 20 questions, one at a time, seeing each answer before
 *                          the next, and says with each what it expects the answer to be. It may not
 *                          answer before the 20th. Then it answers the owner's question.
 *   random 20            - the world's answers to 20 random situations near the jobs are given first
 *   answer straight away - as in log 21
 * Then each arm answers the other test questions of log 19, given the answers it had.
 *
 * What is recorded about DeepSeek's 20 questions: usable or not; the same situation asked twice; the
 * owner's own buried question asked back; a test question's situation asked; whether the answer
 * surprised it (the world's answer differs from what it expected on some thing); tries to stop early;
 * how many events and changed starting states each question had.
 *
 * Run with:
 *   DEEPSEEK_API_KEY=... NODE_USE_ENV_PROXY=1 node "22 twenty questions.js" OUTFOLDER [REPEATS] [WORLD,WORLD]
 *   node "22 twenty questions.js" --summarise FOLDER
 */
const fs = require('fs');
const path = require('path');
const C = require('./03 checker.js');
const L = require('./09 loop.js');
const B = require('./19 baseline and more thinking.js');
const P = require('./20 who picks the questions.js');
const T = require('./21 long texts.js');

const WORLDS = require('./03 test worlds.js').concat(require('./18 more test worlds.js'));
const QUESTIONS = 20;
const lower = t => String(t).trim().toLowerCase();

// How many starting states differ from the world's usual start (writing out a default is not a change).
function starts_changed(world, situation) {
  const world_model = C.prepare_model(world.world);
  const problems = [];
  const resolved = C.resolve_situation(world_model, situation, problems, 'count');
  return Object.entries(resolved.start).filter(([thing, state]) => world_model.start[thing] !== state).length;
}
// Did the answer differ from what DeepSeek expected, on any thing it named an expectation for?
function surprised(expect, answer_job) {
  if (!expect || typeof expect !== 'object') return null;
  const world_says = Object.fromEntries(answer_job.expect.map(e => { const m = /^(.+?) is (.+)$/.exec(e); return [lower(m[1]), lower(m[2])]; }));
  const compared = Object.entries(expect).filter(([k]) => world_says[lower(k)] !== undefined);
  if (!compared.length) return null;
  return compared.some(([k, v]) => world_says[lower(k)] !== lower(v));
}

async function must_ask(D, world, text, embedded, test_keys) {
  const g = D.make_deepseek_guesser();
  const messages = [{ role: 'system', content: T.SYSTEM }, { role: 'user', content: `${T.opening(world, text, [])}\n\nBefore you answer, you must ask the owner exactly ${QUESTIONS} questions, one at a time. Each question is a situation; the owner tells you how it ends. Ask whatever will help you most. With each question, say how you expect it to end.\n\nEach turn, reply with JSON only: {"ask": {"start": {"THING": "STATE"}, "events": ["EVENT", "EVENT"]}, "i_expect": {"THING": "STATE"}}. After the owner answers your ${QUESTIONS}th question you will be asked for your answer.` }];
  const asked = [];
  const answers = [];
  const seen = new Set();
  const embedded_key = T.canonical(world, embedded.situation);
  let stop_tries = 0, unreadable = 0;
  for (let turn = 0; asked.length < QUESTIONS && turn < QUESTIONS + 10; turn++) {
    const reply = await g(messages, { reply_shape: 'none' });
    messages.push({ role: 'assistant', content: reply });
    const r = L.read_reply(reply);
    if (!r || !r.ask) {
      if (r && (r.stop || r.answer !== undefined)) stop_tries++; else unreadable++;
      messages.push({ role: 'user', content: `You must ask ${QUESTIONS - asked.length} more question${QUESTIONS - asked.length === 1 ? '' : 's'} first. Reply with {"ask": ..., "i_expect": ...}.` });
      continue;
    }
    const situation = T.read_situation(r.ask);
    const key = T.canonical(world, situation);
    const a = P.world_answer(world, situation, answers.length + 1);
    const events = Object.values(situation.events).flat().length;
    const entry = { number: asked.length + 1, ask: r.ask, i_expect: r.i_expect || null, usable: !!a, events, starts_changed: starts_changed(world, situation),
      repeat_of_earlier: !!key && seen.has(key), is_the_owners_question: !!key && key === embedded_key, is_a_test_question: !!a && test_keys.has(JSON.stringify(a.situation)),
      world_says: a ? a.expect : null, surprised: a ? surprised(r.i_expect, a) : null };
    if (key) seen.add(key);
    asked.push(entry);
    if (a) { answers.push(a); messages.push({ role: 'user', content: `The owner says: ${L.job_in_words(a).replace(/^- "owner answer \d+": /, '')} (${asked.length} of ${QUESTIONS} asked)` }); } else messages.push({ role: 'user', content: `The owner could not follow that situation; use only the names listed. (${asked.length} of ${QUESTIONS} asked)` });
  }
  messages.push({ role: 'user', content: `That was your last question. Now answer the question the owner is asking you in their message. Reply with JSON only, in this shape: ${T.FINAL_SHAPE}` });
  const reply = await g(messages, { reply_shape: 'none' });
  const final = L.read_reply(reply);
  return { final, grade: T.grade_final(world, embedded, final), asked, answers, stop_tries, unreadable, tokens_out: g.counts.tokens_out, cut_off: g.counts.cut_off, final_reply: reply };
}

async function run_world(world, repeat, D) {
  const { embedded, tests } = T.embedded_question(world);
  const text = T.message(world, 'long', embedded);
  const as_world = Object.assign({}, world, { request: text });
  const test_keys = new Set(tests.map(q => JSON.stringify(q.situation)));
  const all_test_keys = new Set(tests.concat(embedded).map(q => JSON.stringify(q.situation)));
  const random_answers = [];
  for (const s of P.random_situations(world, QUESTIONS, all_test_keys, `${world.id} twenty ${repeat}`)) {
    if (random_answers.length >= QUESTIONS) break;
    const a = P.world_answer(world, s, random_answers.length + 1);
    if (a) random_answers.push(a);
  }
  const test_after = async answers => {
    const g = D.make_deepseek_guesser();
    const d = await B.ask_direct(g, as_world, tests, answers);
    return { graded: B.grade_direct(tests, d.answers), tokens_out: d.tokens_out, cut_off: g.counts.cut_off };
  };
  const arms = {};
  const straight = await T.answer_straight(D, world, text, embedded, []);
  arms['answer straight away'] = Object.assign(straight, { tests: await test_after([]) });
  const randomly = await T.answer_straight(D, world, text, embedded, random_answers);
  arms['random 20, then answer'] = Object.assign(randomly, { answers_given: random_answers.length, tests: await test_after(random_answers) });
  const forced = await must_ask(D, world, text, embedded, test_keys);
  arms['must ask 20, then answer'] = Object.assign(forced, { answers_given: forced.answers.length, tests: await test_after(forced.answers) });
  const asked_keys = new Set(random_answers.concat(forced.answers).map(a => JSON.stringify(a.situation)));
  return { world: world.id, repeat, guesser: D.MODEL_NAME, embedded: { id: embedded.id, in_prose: T.question_in_prose(embedded), world_says: embedded.parts },
    left_out_of_scoring: tests.filter(q => asked_keys.has(JSON.stringify(q.situation))).map(q => q.id), arms };
}

function summarise(records) {
  const names = [...new Set(records.flatMap(r => Object.keys(r.arms)))];
  const lines = ['| Arm | Owner\'s question found | Answered right | Other held-back right, fair | Nearby right, fair | Answers from the owner | Output tokens | Replies cut off |', '|---|---|---|---|---|---|---|---|'];
  for (const n of names) {
    const t = { found: 0, right: 0, runs: 0, hr: 0, ht: 0, nr: 0, nt: 0, given: 0, tokens: 0, cut: 0 };
    for (const r of records) {
      const a = r.arms[n]; if (!a) continue;
      const skip = new Set(r.left_out_of_scoring);
      t.runs++; t.found += a.grade.found ? 1 : 0; t.right += a.grade.answer_right ? 1 : 0; t.given += a.answers_given || 0;
      t.tokens += (a.tokens_out || 0) + a.tests.tokens_out; t.cut += (a.cut_off || 0) + (a.tests.cut_off || 0);
      for (const g of a.tests.graded) { if (skip.has(g.id)) continue; if (g.kind === 'held-back') { t.ht++; if (g.right) t.hr++; } else { t.nt++; if (g.right) t.nr++; } }
    }
    lines.push(`| ${n} | ${t.found}/${t.runs} | ${t.right}/${t.runs} | ${t.hr}/${t.ht} | ${t.nr}/${t.nt} | ${t.given} | ${t.tokens} | ${t.cut} |`);
  }
  const all = records.flatMap(r => (r.arms['must ask 20, then answer'] || { asked: [] }).asked.map(q => {
    const world = WORLDS.find(w => w.id === r.world);
    return Object.assign({ world: r.world }, q, { starts_changed: starts_changed(world, T.read_situation(q.ask)) });
  }));
  const first_back = records.map(r => ((r.arms['must ask 20, then answer'] || { asked: [] }).asked.find(q => q.is_the_owners_question) || {}).number).filter(Boolean);
  const count = f => all.filter(f).length;
  const with_expectation = all.filter(q => q.surprised !== null);
  const halves = [all.filter(q => q.number <= 10 && q.surprised !== null), all.filter(q => q.number > 10 && q.surprised !== null)];
  const behaviour = ['', `What DeepSeek did with its ${all.length} questions (${records.length} runs of 20):`, '',
    `- usable by the owner: ${count(q => q.usable)}`,
    `- the same situation as one it had already asked: ${count(q => q.repeat_of_earlier)}`,
    `- the owner's own buried question, asked back: ${count(q => q.is_the_owners_question)} times, in ${records.filter(r => (r.arms['must ask 20, then answer'] || { asked: [] }).asked.some(q => q.is_the_owners_question)).length} of ${records.length} runs; it was the first question in ${first_back.filter(n => n === 1).length} runs (first asked at question ${first_back.join(', ')})`,
    `- the situation of one of the other test questions: ${count(q => q.is_a_test_question)}`,
    `- with an expectation that could be compared: ${with_expectation.length}; the owner's answer surprised it: ${with_expectation.filter(q => q.surprised).length}`,
    `- surprised in questions 1 to 10: ${halves[0].filter(q => q.surprised).length} of ${halves[0].length}; in questions 11 to 20: ${halves[1].filter(q => q.surprised).length} of ${halves[1].length}`,
    `- tries to stop before the 20th question: ${records.reduce((s, r) => s + ((r.arms['must ask 20, then answer'] || {}).stop_tries || 0), 0)}; replies that were not a question: ${records.reduce((s, r) => s + ((r.arms['must ask 20, then answer'] || {}).unreadable || 0), 0)}`,
    `- events per question: ${all.length ? (all.reduce((s, q) => s + q.events, 0) / all.length).toFixed(1) : 0} on average; questions that changed a starting state from the usual one: ${count(q => q.starts_changed > 0)}`];
  const by_world = ['', 'By world (both repeats): the owner\'s question answered right (straight / random 20 / must ask 20), and DeepSeek\'s surprises out of comparable questions:', '', '| World | Straight | Random 20 | Must ask 20 | Surprised | Repeats of its own questions |', '|---|---|---|---|---|---|'];
  for (const w of [...new Set(records.map(r => r.world))]) {
    const rs = records.filter(r => r.world === w);
    const cell = n => rs.map(r => (r.arms[n].grade.answer_right ? 'right' : 'wrong')).join(', ');
    const qs = rs.flatMap(r => r.arms['must ask 20, then answer'].asked);
    by_world.push(`| ${w} | ${cell('answer straight away')} | ${cell('random 20, then answer')} | ${cell('must ask 20, then answer')} | ${qs.filter(q => q.surprised).length}/${qs.filter(q => q.surprised !== null).length} | ${qs.filter(q => q.repeat_of_earlier).length} |`);
  }
  return lines.concat(behaviour, by_world).join('\n');
}
const results_text = (records, failed) => `# Twenty questions: results\n\nDeepSeek V4.1 Flash, default thinking, log 21's long messages. ${records.length} world-and-repeat runs; every number comes from the records in this folder. "Fair" leaves out every test question whose situation either arm asked the owner about.\n\n${summarise(records)}\n${failed.length ? `\nRuns that failed:\n${failed.join('\n')}\n` : ''}`;

module.exports = { must_ask, run_world, summarise, surprised, starts_changed };

if (require.main === module) {
  const [first, second, third] = process.argv.slice(2);
  if (first === '--summarise') {
    const records = fs.readdirSync(second).filter(f => f.endsWith('.json')).sort().map(f => JSON.parse(fs.readFileSync(path.join(second, f), 'utf8')));
    const text = results_text(records, []);
    fs.writeFileSync(path.join(second, 'results.md'), text);
    console.log(text);
  } else {
    const D = require('./17 DeepSeek guesser.js');
    const worlds = WORLDS.filter(w => !third || third.split(',').includes(w.id));
    const REPEATS = Number(second) || 1;
    fs.mkdirSync(first, { recursive: true });
    (async () => {
      const jobs = [];
      for (const w of worlds) for (let r = 1; r <= REPEATS; r++) jobs.push([w, r]);
      const records = await Promise.all(jobs.map(async ([w, r]) => {
        try {
          const rec = await run_world(w, r, D);
          fs.writeFileSync(path.join(first, `${w.id} repeat ${r}.json`), JSON.stringify(rec, null, 1) + '\n');
          console.log(`${w.id} repeat ${r} done`);
          return rec;
        } catch (e) { console.log(`${w.id} repeat ${r} failed: ${e.message}`); return { world: w.id, repeat: r, failed: String(e.message) }; }
      }));
      const text = results_text(records.filter(r => !r.failed), records.filter(r => r.failed).map(r => `- ${r.world} repeat ${r.repeat}: ${r.failed}`));
      fs.writeFileSync(path.join(first, 'results.md'), text);
      console.log(text);
    })();
  }
}
