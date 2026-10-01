/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Log 21. The owner asked whether the earlier findings hold for long texts: when the question is buried
 * in a long message, does DeepSeek find it, and does it find it when it may stop whenever it likes?
 *
 * For each world, one held-back job is chosen by a fixed shuffle and turned into a question in plain
 * words, "the embedded question" ("What I actually need to know is: ..."). Two messages carry it:
 *   short - the world's request, then the embedded question
 *   long  - the request's sentences spread through about 2,300 words of everyday news (file 21 filler),
 *           with the embedded question tucked into the middle paragraph
 * DeepSeek is told only: answer what the owner is asking you in this message. It must say which
 * situation the owner asked about, and answer it. The shown jobs with their answers come after the
 * message, the same for both lengths.
 *
 * Four arms per world, length and repeat:
 *   answer straight away  - one reply
 *   random questions      - 6 answers from the world to random nearby situations are given first
 *   ask or stop           - each turn DeepSeek either asks the owner about a situation (the world
 *                           answers) or stops and answers; at most 12 questions
 *   guesser fixes first   - the rule-writing loop, whose model answers by being run
 * The embedded question is graded twice: "found" (DeepSeek named the right situation) and "right"
 * (its answer is the world's). Then every arm answers the other test questions of log 19 (held-back
 * and nearby), given any answers it collected, to see whether log 20's findings hold for long texts.
 *
 * Run with:
 *   DEEPSEEK_API_KEY=... NODE_USE_ENV_PROXY=1 node "21 long texts.js" OUTFOLDER [REPEATS] [WORLD,WORLD]
 *   node "21 long texts.js" --show WORLD        (print both messages, no DeepSeek)
 *   node "21 long texts.js" --summarise FOLDER  (rewrite results.md from the records)
 */
const fs = require('fs');
const path = require('path');
const C = require('./03 checker.js');
const L = require('./09 loop.js');
const B = require('./19 baseline and more thinking.js');
const P = require('./20 who picks the questions.js');
const FILLER = require('./21 filler paragraphs.js');

const WORLDS = require('./03 test worlds.js').concat(require('./18 more test worlds.js'));
const LENGTHS = ['short', 'long'];
const RANDOM_QUESTIONS = 6;
const MAX_ASKS = 12;

function embedded_question(world) {
  const { questions } = B.build_questions(world);
  const held = questions.filter(q => q.kind === 'held-back');
  const chosen = held.map(q => ({ q, key: B.stable_key(`${world.id}|embedded|${q.id}`) })).sort((a, b) => a.key - b.key)[0].q;
  return { embedded: chosen, tests: questions.filter(q => q.id !== chosen.id) };
}
function situation_in_prose(situation) {
  const start = Object.entries(situation.start || {}).map(([t, s]) => `${t} is ${s}`);
  const events = Object.keys(situation.events || {}).sort((a, b) => Number(a) - Number(b)).flatMap(k => situation.events[k]);
  return `${start.length ? `we start with ${start.join(' and ')}` : 'we start the usual way'}, ${events.length ? `and then ${events.join(', then ')} happens` : 'and nothing happens'}`;
}
function question_in_prose(q) {
  if (q.at === 'end') return `What I actually need to know is this: if ${situation_in_prose(q.situation)}, how does it end for the ${q.parts.map(p => p.thing.replace(/_/g, ' ')).join(' and the ')}?`;
  const p = q.parts[0];
  return `What I actually need to know is this: if ${situation_in_prose(q.situation)}, is ${p.thing.replace(/_/g, ' ')} ever ${p.state} at any point along the way?`;
}
function sentences_of(text) { return text.split(/(?<=[.!?])\s+(?=[A-Z"'])/).filter(Boolean); }

function message(world, length, embedded) {
  const ask = question_in_prose(embedded);
  if (length === 'short') return `${world.request} ${ask}`;
  const request = sentences_of(world.request);
  const paragraphs = FILLER.slice();
  const middle = Math.floor(paragraphs.length / 2);
  // Spread the request's sentences evenly over the paragraphs, each added to the end of one.
  request.forEach((s, i) => {
    let at = Math.min(paragraphs.length - 1, Math.floor(((i + 1) * paragraphs.length) / (request.length + 1)));
    if (at === middle) at = middle - 3; // the embedded question's paragraph carries nothing else
    paragraphs[at] = `${paragraphs[at]} ${s}`;
  });
  paragraphs[middle] = `${paragraphs[middle]} Oh, and one more thing, before I forget. ${ask}`;
  return paragraphs.join('\n\n');
}

const FINAL_SHAPE = '{"owner_asked": "the owner\'s question in your own words", "situation": {"start": {"THING": "STATE"}, "events": ["EVENT", "EVENT"]}, "answer": ANSWER}. ANSWER is {"THING": "STATE"} for a question about how things end, or "yes" or "no" for a yes-or-no question. Use exactly the names listed above.';
function opening(world, text, extra_answers) {
  const shown = C.prepare_jobs({ jobs: world.jobs.filter(j => !j.held_back) }).jobs;
  const extra = extra_answers && extra_answers.length ? `\n\nMore answers from the owner:\n${extra_answers.map(L.job_in_words).join('\n')}` : '';
  return `The owner's message:\n"""\n${text}\n"""\n\n${L.vocabulary_in_words(world)}\n\nAnswers the owner has given before (each: a situation, and what is expected):\n${shown.map(L.job_in_words).join('\n')}${extra}`;
}
const SYSTEM = 'You help the owner with what they ask. Your job: answer the question the owner is asking you in their message.';

// Resolve a situation fully against the world: every start state filled in, events in order.
function canonical(world, situation) {
  const world_model = C.prepare_model(world.world);
  const problems = [];
  const resolved = C.resolve_situation(world_model, situation, problems, 'grade');
  if (problems.length) return null;
  const events = Object.keys(resolved.events).sort((a, b) => Number(a) - Number(b)).flatMap(k => resolved.events[k]);
  return JSON.stringify({ start: Object.assign({}, world_model.start, resolved.start), events });
}
function read_situation(raw) {
  if (!raw || typeof raw !== 'object') return null;
  const events = Array.isArray(raw.events) ? raw.events : typeof raw.events === 'string' ? [raw.events] : [];
  return C.prepare_jobs({ jobs: [{ name: 'reply', start: raw.start && typeof raw.start === 'object' ? raw.start : {}, events, expect: [] }] }).jobs[0].situation;
}
function grade_final(world, embedded, final) {
  const situation = final ? read_situation(final.situation) : null;
  const target = canonical(world, embedded.situation);
  const found = !!situation && canonical(world, situation) === target;
  const right_answer = !!final && B.grade_direct([embedded], { [embedded.id]: final.answer })[0].right;
  return { found, answer_right: right_answer, found_and_right: found && right_answer, owner_asked: final ? final.owner_asked : null };
}

async function answer_straight(D, world, text, embedded, extra_answers) {
  const g = D.make_deepseek_guesser();
  const reply = await g([{ role: 'system', content: SYSTEM }, { role: 'user', content: `${opening(world, text, extra_answers)}\n\nReply with JSON only, in this shape: ${FINAL_SHAPE}` }], { reply_shape: 'none' });
  const final = L.read_reply(reply);
  return { final, grade: grade_final(world, embedded, final), asks: 0, tokens_out: g.counts.tokens_out, cut_off: g.counts.cut_off, transcript: [reply] };
}

async function ask_or_stop(D, world, text, embedded) {
  const g = D.make_deepseek_guesser();
  const messages = [{ role: 'system', content: SYSTEM }, { role: 'user', content: `${opening(world, text, [])}\n\nYou may ask the owner how a situation ends before you answer, up to ${MAX_ASKS} times, or you may answer at any time. Each turn, reply with JSON only, one of:\n- to ask: {"ask": {"start": {"THING": "STATE"}, "events": ["EVENT", "EVENT"]}}\n- to stop and answer: ${FINAL_SHAPE.replace('{"owner_asked"', '{"stop": true, "owner_asked"')}` }];
  const answers = [];
  const transcript = [];
  let asks = 0, unusable = 0, unreadable = 0, final = null;
  for (let turn = 0; turn <= MAX_ASKS + 2 && !final; turn++) {
    const reply = await g(messages, { reply_shape: 'none' });
    transcript.push(reply);
    messages.push({ role: 'assistant', content: reply });
    const r = L.read_reply(reply);
    if (r && r.ask && asks < MAX_ASKS) {
      asks++;
      const a = P.world_answer(world, read_situation(r.ask), answers.length + 1);
      if (a) { answers.push(a); messages.push({ role: 'user', content: `The owner says: ${L.job_in_words(a).replace(/^- "owner answer \d+": /, '')}` }); } else { unusable++; messages.push({ role: 'user', content: 'The owner could not follow that situation. Use only the names listed.' }); }
      if (asks >= MAX_ASKS) messages.push({ role: 'user', content: 'That was your last question. Stop and answer now.' });
    } else if (r && (r.stop || r.answer !== undefined)) {
      final = r;
    } else {
      unreadable++;
      messages.push({ role: 'user', content: 'Reply with JSON only, either {"ask": ...} or {"stop": true, ...}.' });
    }
  }
  return { final, grade: grade_final(world, embedded, final), asks, unusable, unreadable, answers, tokens_out: g.counts.tokens_out, cut_off: g.counts.cut_off, transcript };
}

async function run_world(world, repeat, D) {
  const { embedded, tests } = embedded_question(world);
  const test_keys = new Set(tests.concat(embedded).map(q => JSON.stringify(q.situation)));
  const random_answers = [];
  for (const s of P.random_situations(world, RANDOM_QUESTIONS, test_keys, `${world.id} long texts ${repeat}`)) {
    if (random_answers.length >= RANDOM_QUESTIONS) break;
    const a = P.world_answer(world, s, random_answers.length + 1);
    if (a) random_answers.push(a);
  }
  const arms = {};
  for (const length of LENGTHS) {
    const text = message(world, length, embedded);
    const as_world = Object.assign({}, world, { request: text });
    const test_after = async (answers) => {
      const g = D.make_deepseek_guesser();
      const d = await B.ask_direct(g, as_world, tests, answers);
      return Object.assign(B.tally(B.grade_direct(tests, d.answers)), { tokens_out: d.tokens_out, cut_off: g.counts.cut_off });
    };
    const straight = await answer_straight(D, world, text, embedded, []);
    arms[`${length}: answer straight away`] = Object.assign(straight, { tests: await test_after([]) });
    const randomly = await answer_straight(D, world, text, embedded, random_answers);
    arms[`${length}: random questions, then answer`] = Object.assign(randomly, { answers_given: random_answers.length, tests: await test_after(random_answers) });
    const asked = await ask_or_stop(D, world, text, embedded);
    arms[`${length}: ask or stop`] = Object.assign(asked, { tests: await test_after(asked.answers) });
    const loop_guesser = D.make_deepseek_guesser();
    const guess = await L.first_guess(as_world, { guesser: loop_guesser });
    const loop = await L.run_task(as_world, 'guesser fixes first', { guesser: loop_guesser }, guess);
    const model = C.prepare_model(loop.model);
    const e = B.grade_model([embedded], model)[0].right;
    arms[`${length}: guesser fixes first`] = { grade: { found: null, answer_right: e, found_and_right: null }, questions_to_world: loop.questions_to_world,
      tests: Object.assign(B.tally(B.grade_model(tests, model)), { tokens_out: 0 }), tokens_out: loop.log.reduce((s, x) => s + (x.tokens_out || 0), 0), cut_off: loop.log.filter(x => (x.tokens_out || 0) >= 32000).length, model: loop.model };
  }
  return { world: world.id, repeat, guesser: D.MODEL_NAME, embedded: { id: embedded.id, job: embedded.job, in_prose: question_in_prose(embedded), world_says: embedded.parts },
    long_message_words: message(world, 'long', embedded).split(/\s+/).length, random_answers: random_answers.map(a => a.situation), arms };
}

function summarise(records) {
  const names = [...new Set(records.flatMap(r => Object.keys(r.arms)))];
  const lines = ['| Arm | Embedded question found | Embedded question answered right | Found and right | Questions asked (ask or stop) | Stopped without asking | Other held-back right | Nearby right | Output tokens | Replies cut off |', '|---|---|---|---|---|---|---|---|---|---|'];
  for (const n of names) {
    const t = { found: 0, right: 0, both: 0, runs: 0, asks: 0, zero: 0, hr: 0, ht: 0, nr: 0, nt: 0, tokens: 0, cut: 0, is_loop: /guesser fixes first/.test(n), is_ask: /ask or stop/.test(n) };
    for (const r of records) {
      const a = r.arms[n]; if (!a) continue;
      t.runs++; t.found += a.grade.found ? 1 : 0; t.right += a.grade.answer_right ? 1 : 0; t.both += a.grade.found_and_right ? 1 : 0;
      if (t.is_ask) { t.asks += a.asks; if (!a.asks) t.zero++; }
      t.hr += a.tests.held_back_right; t.ht += a.tests.held_back_total; t.nr += a.tests.nearby_right; t.nt += a.tests.nearby_total;
      t.tokens += (a.tokens_out || 0) + (a.tests.tokens_out || 0); t.cut += (a.cut_off || 0) + (a.tests.cut_off || 0);
    }
    lines.push(`| ${n} | ${t.is_loop ? 'not asked' : `${t.found}/${t.runs}`} | ${t.right}/${t.runs} | ${t.is_loop ? 'not asked' : `${t.both}/${t.runs}`} | ${t.is_ask ? t.asks : ''} | ${t.is_ask ? `${t.zero}/${t.runs}` : ''} | ${t.hr}/${t.ht} | ${t.nr}/${t.nt} | ${t.tokens} | ${t.cut} |`);
  }
  const by_world = ['', 'Embedded question found and answered right, by world (both repeats), "answer straight away" and "ask or stop":', '', '| World | short, straight | long, straight | short, ask or stop | long, ask or stop |', '|---|---|---|---|---|'];
  for (const w of [...new Set(records.map(r => r.world))]) {
    const cell = n => records.filter(r => r.world === w && r.arms[n]).map(r => (r.arms[n].grade.found_and_right ? 'yes' : r.arms[n].grade.found ? 'found, wrong' : 'not found')).join(', ');
    by_world.push(`| ${w} | ${cell('short: answer straight away')} | ${cell('long: answer straight away')} | ${cell('short: ask or stop')} | ${cell('long: ask or stop')} |`);
  }
  return lines.concat(by_world).join('\n');
}
const results_text = (records, failed) => `# Long texts: results\n\nDeepSeek V4.1 Flash, default thinking. ${records.length} world-and-repeat runs; every number comes from the records in this folder. "Guesser fixes first" is not asked to name the owner's question; its model is run on it.\n\n${summarise(records)}\n${failed.length ? `\nRuns that failed:\n${failed.join('\n')}\n` : ''}`;

module.exports = { embedded_question, question_in_prose, message, canonical, read_situation, grade_final, ask_or_stop, answer_straight, run_world, summarise, opening, FINAL_SHAPE, SYSTEM };

if (require.main === module) {
  const [first, second, third] = process.argv.slice(2);
  if (first === '--show') {
    const world = WORLDS.find(w => w.id === second);
    const { embedded } = embedded_question(world);
    for (const length of LENGTHS) console.log(`===== ${length} (${message(world, length, embedded).split(/\s+/).length} words)\n${message(world, length, embedded)}\n`);
  } else if (first === '--summarise') {
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
      const ok = records.filter(r => !r.failed);
      const text = results_text(ok, records.filter(r => r.failed).map(r => `- ${r.world} repeat ${r.repeat}: ${r.failed}`));
      fs.writeFileSync(path.join(first, 'results.md'), text);
      console.log(text);
    })();
  }
}
