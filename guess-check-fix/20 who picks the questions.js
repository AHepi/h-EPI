/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Log 20. Log 19 found that DeepSeek, answering questions directly, did better than the loop once it was
 * given the answers the world gave the loop. This file tests whether the loop's CHOICE of questions is
 * what helped, or whether any extra answers from the world would help as much.
 *
 * For each world and repeat, with DeepSeek at its default thinking setting:
 *   1. The loop ("guesser fixes first") runs from a fresh first guess and asks the world its questions.
 *      Say it asked N. Its own final model is graded too.
 *   2. Three sets of N questions are answered by the world, then handed to DeepSeek alone (log 19),
 *      which answers the fixed test questions directly:
 *        ask then answer          - the N questions the loop asked
 *        random questions         - N situations one or two changes from the jobs, by a fixed shuffle
 *        DeepSeek picks questions - DeepSeek is told it may ask the owner N questions and writes them
 *   3. DeepSeek alone with no extra answers, as in log 19.
 * The test questions are log 19's (held-back jobs and 20 nearby situations per world). Scores are also
 * given leaving out every test question whose situation any arm asked the world about, so no arm is
 * credited for having been told an answer.
 *
 * Run with:
 *   DEEPSEEK_API_KEY=... NODE_USE_ENV_PROXY=1 node "20 who picks the questions.js" OUTFOLDER [REPEATS] [WORLD,WORLD]
 *   node "20 who picks the questions.js" --summarise FOLDER   (rewrite results.md from the records, no DeepSeek)
 */
const fs = require('fs');
const path = require('path');
const C = require('./03 checker.js');
const L = require('./09 loop.js');
const B = require('./19 baseline and more thinking.js');

const WORLDS = require('./03 test worlds.js').concat(require('./18 more test worlds.js'));
const key_of = situation => JSON.stringify(situation);

function asked_things_of(world) {
  return [...new Set(C.prepare_jobs({ jobs: world.jobs }).jobs.flatMap(j => j.expect.map(e => String(e).split(/ is /)[0].replace(/^not /, ''))))];
}
// The world answers one situation: the end state of every thing the jobs ask about. null if it cannot.
function world_answer(world, situation, number) {
  const world_model = C.prepare_model(world.world);
  const problems = [];
  const resolved = C.resolve_situation(world_model, situation, problems, 'owner question');
  if (problems.length) return null;
  const result = C.run(world_model, resolved);
  const expect = [];
  for (const thing of asked_things_of(world)) {
    const ends = [...new Set(result.final_states.map(s => s[thing]))];
    if (ends.length !== 1 || result.clashes.some(c => c.thing === thing)) return null;
    expect.push(`${thing} is ${ends[0]}`);
  }
  const events = Object.keys(situation.events || {}).sort((a, b) => Number(a) - Number(b)).flatMap(k => situation.events[k]);
  return C.prepare_jobs({ jobs: [{ name: `owner answer ${number}`, start: situation.start || {}, events, expect }] }).jobs[0];
}

function random_situations(world, how_many, test_keys, salt) {
  const world_model = C.prepare_model(world.world);
  const all_jobs = C.prepare_jobs({ jobs: world.jobs }).jobs;
  const job_keys = new Set(all_jobs.map(j => key_of(j.situation)));
  return C.candidate_situations(world_model, world_model, all_jobs, 400, null).list
    .filter(c => c.steps.length && !job_keys.has(key_of(c.situation)) && !test_keys.has(key_of(c.situation)))
    .map(c => Object.assign({ key: B.stable_key(`${salt}|${key_of(c.situation)}`) }, c)).sort((a, b) => a.key - b.key)
    .map(c => c.situation).slice(0, how_many * 3);
}

async function deepseek_picks(guesser, world, how_many) {
  const shown = C.prepare_jobs({ jobs: world.jobs.filter(j => !j.held_back) }).jobs;
  const messages = [
    { role: 'system', content: 'You help work out exactly what someone means by a request, by choosing questions to ask them.' },
    { role: 'user', content: `Task: ${world.request}\n\n${L.vocabulary_in_words(world)}\n\nAnswers the owner has given (each: a situation, and what is expected):\n${shown.map(L.job_in_words).join('\n')}\n\nYou may ask the owner ${how_many} more questions. Each question is a situation: a starting state for any of the things above, and events in order, using exactly the names above. The owner will tell you how each situation ends. Choose the ${how_many} situations whose answers would tell you most about what the owner means, where the request and the answers so far leave it open.\n\nReply with JSON only: a list of ${how_many} situations, each {"start": {"THING": "STATE"}, "events": ["EVENT", "EVENT"]}.` },
  ];
  const text = await guesser(messages, { reply_shape: 'none' });
  const usage = guesser.last_usage;
  const reply = L.read_reply(text);
  const list = Array.isArray(reply) ? reply : reply && Array.isArray(reply.questions) ? reply.questions : reply && Array.isArray(reply.situations) ? reply.situations : [];
  const situations = list.slice(0, how_many).map(s => C.prepare_jobs({ jobs: [{ name: 'pick', start: (s && s.start) || {}, events: (s && s.events) || [], expect: [] }] }).jobs[0].situation);
  return { situations, written: list.length, text, tokens_out: usage ? usage.tokens_out : 0 };
}

async function run_world(world, repeat, D) {
  const { questions } = B.build_questions(world);
  const test_keys = new Set(questions.map(q => key_of(q.situation)));
  const arms = {};
  const record_arm = (name, graded, extra) => { arms[name] = Object.assign(B.tally(graded), extra, { graded }); };

  // 1. The loop, and the questions it asked.
  const loop_guesser = D.make_deepseek_guesser();
  const guess = await L.first_guess(world, { guesser: loop_guesser });
  const loop = await L.run_task(world, 'guesser fixes first', { guesser: loop_guesser }, guess);
  record_arm('guesser fixes first', B.grade_model(questions, C.prepare_model(loop.model)), { calls: 1 + loop.guesser_calls, tokens_out: loop.log.reduce((s, e) => s + (e.tokens_out || 0), 0) });
  const loop_answers = C.prepare_jobs({ jobs: loop.added_jobs.map(a => a.job) }).jobs;
  const n = loop_answers.length;

  // 2. The same number of answers, three ways of choosing the questions.
  const random_answers = [];
  for (const s of random_situations(world, n, test_keys, `${world.id} repeat ${repeat}`)) {
    if (random_answers.length >= n) break;
    const a = world_answer(world, s, random_answers.length + 1);
    if (a) random_answers.push(a);
  }
  const picker = D.make_deepseek_guesser();
  const picked = n ? await deepseek_picks(picker, world, n) : { situations: [], written: 0, tokens_out: 0 };
  const picked_answers = [];
  let picked_unusable = 0;
  for (const s of picked.situations) { const a = world_answer(world, s, picked_answers.length + 1); if (a) picked_answers.push(a); else picked_unusable++; }

  const direct = async (name, answers, extra) => {
    const g = D.make_deepseek_guesser();
    const d = await B.ask_direct(g, world, questions, answers);
    record_arm(name, B.grade_direct(questions, d.answers), Object.assign({ calls: 1, tokens_out: d.tokens_out, answers_given: answers.length, cut_off: g.counts.cut_off, reply: d.text }, extra));
  };
  await direct('DeepSeek alone', []);
  await direct('ask then answer (the loop picks the questions)', loop_answers);
  await direct('random questions, then answer', random_answers);
  await direct('DeepSeek picks questions, then answer', picked_answers, { questions_written: picked.written, questions_unusable: picked_unusable, picking_tokens_out: picked.tokens_out, picking_reply: picked.text });

  // Every situation any arm asked about, so scores can leave those test questions out.
  const asked_keys = [...new Set([...loop_answers, ...random_answers, ...picked_answers].map(j => key_of(j.situation)))];
  return { world: world.id, repeat, guesser: D.MODEL_NAME, questions_to_world: n,
    asked: { loop: loop_answers.map(j => j.situation), random: random_answers.map(j => j.situation), deepseek: picked_answers.map(j => j.situation) },
    left_out_of_scoring: questions.filter(q => asked_keys.includes(key_of(q.situation))).map(q => q.id),
    questions: questions.map(q => ({ id: q.id, kind: q.kind, job: q.job, words: q.words, world_says: q.parts })), arms, loop_rounds: loop.rounds, loop_log: loop.log, loop_model: loop.model };
}

function summarise(records) {
  const names = [...new Set(records.flatMap(r => Object.keys(r.arms)))];
  const lines = ['| Arm | Held-back right | Nearby right | Held-back right, asked-about left out | Nearby right, asked-about left out | Answers from the world given | Output tokens |', '|---|---|---|---|---|---|---|'];
  for (const name of names) {
    const t = { hr: 0, ht: 0, nr: 0, nt: 0, hr2: 0, ht2: 0, nr2: 0, nt2: 0, given: 0, tokens: 0 };
    for (const rec of records) {
      const a = rec.arms[name]; if (!a) continue;
      const skip = new Set(rec.left_out_of_scoring);
      t.hr += a.held_back_right; t.ht += a.held_back_total; t.nr += a.nearby_right; t.nt += a.nearby_total;
      t.given += a.answers_given || 0; t.tokens += (a.tokens_out || 0) + (a.picking_tokens_out || 0);
      for (const g of a.graded) { if (skip.has(g.id)) continue; if (g.kind === 'held-back') { t.ht2++; if (g.right) t.hr2++; } else { t.nt2++; if (g.right) t.nr2++; } }
    }
    lines.push(`| ${name} | ${t.hr}/${t.ht} | ${t.nr}/${t.nt} | ${t.hr2}/${t.ht2} | ${t.nr2}/${t.nt2} | ${name === 'guesser fixes first' ? '(its own questions)' : t.given} | ${t.tokens} |`);
  }
  // Fair counts (asked-about left out), held-back and nearby together, by world and by repeat.
  const fair = (rec, name) => rec.arms[name] ? rec.arms[name].graded.filter(g => !rec.left_out_of_scoring.includes(g.id) && g.right).length : 0;
  const by = (label, key_of_rec) => {
    const rows = {};
    for (const rec of records) { const k = key_of_rec(rec); rows[k] = rows[k] || names.map(() => 0); names.forEach((n, i) => { rows[k][i] += fair(rec, n); }); }
    return ['', `Fair count by ${label} (held-back and nearby right together):`, '', `| ${label} | ${names.join(' | ')} |`, `|---|${names.map(() => '---').join('|')}|`]
      .concat(Object.entries(rows).map(([k, v]) => `| ${k} | ${v.join(' | ')} |`));
  };
  return lines.concat(by('world', r => r.world), by('repeat', r => `repeat ${r.repeat}`)).join('\n');
}

module.exports = { world_answer, random_situations, deepseek_picks, summarise, run_world };

const results_text = (records, failed) => `# Who picks the questions: results\n\nDeepSeek V4.1 Flash, default thinking. ${records.length} world-and-repeat runs; every number comes from the records in this folder. "Fair" leaves out every test question whose situation any arm asked the world about.\n\n${summarise(records)}\n${failed.length ? `\nRuns that failed:\n${failed.join('\n')}\n` : ''}`;

if (require.main === module && process.argv[2] === '--summarise') {
  const folder = process.argv[3];
  const records = fs.readdirSync(folder).filter(f => f.endsWith('.json')).sort().map(f => JSON.parse(fs.readFileSync(path.join(folder, f), 'utf8')));
  const text = results_text(records, []);
  fs.writeFileSync(path.join(folder, 'results.md'), text);
  console.log(text);
} else if (require.main === module) {
  const [out_folder, repeats_text, which] = process.argv.slice(2);
  const D = require('./17 DeepSeek guesser.js');
  const worlds = WORLDS.filter(w => !which || which.split(',').includes(w.id));
  const REPEATS = Number(repeats_text) || 1;
  fs.mkdirSync(out_folder, { recursive: true });
  (async () => {
    const jobs = [];
    for (const w of worlds) for (let r = 1; r <= REPEATS; r++) jobs.push([w, r]);
    const records = await Promise.all(jobs.map(async ([w, r]) => {
      try {
        const rec = await run_world(w, r, D);
        fs.writeFileSync(path.join(out_folder, `${w.id} repeat ${r}.json`), JSON.stringify(rec, null, 1) + '\n');
        console.log(`${w.id} repeat ${r} done: ${rec.questions_to_world} questions`);
        return rec;
      } catch (e) { console.log(`${w.id} repeat ${r} failed: ${e.message}`); return { world: w.id, repeat: r, failed: String(e.message) }; }
    }));
    const ok = records.filter(r => !r.failed);
    const failed = records.filter(r => r.failed).map(r => `- ${r.world} repeat ${r.repeat}: ${r.failed}`);
    const text = results_text(ok, failed);
    fs.writeFileSync(path.join(out_folder, 'results.md'), text);
    console.log(text);
  })();
}
