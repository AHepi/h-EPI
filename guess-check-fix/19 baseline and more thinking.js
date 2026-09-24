/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Log 19. Two questions the owner asked:
 *   1. Baseline: does all this machinery beat simply asking DeepSeek?
 *   2. More tokens: would letting DeepSeek think harder, or ask it more times, solve the same problems?
 *
 * For each world a fixed set of questions is built once: every held-back job (except those about a
 * particular step, whose idea of a "step" belongs to the checker), and 20 nearby situations picked by a
 * fixed shuffle, each asking what the things the jobs care about end up as. The world answers them all.
 * Every arm below answers exactly those questions, and every DeepSeek call's tokens are counted.
 *
 * Arms, per world and repeat:
 *   DeepSeek alone, low / high / max thinking - given the request, the owner's word list and the shown
 *       jobs with their answers, it answers every question directly in one reply. No model, no checker.
 *   DeepSeek alone, high, majority of 5 - five such replies; each answer is the one most of them gave.
 *   DeepSeek alone, high, with the world's answers - also given every answer the world gave the loop in
 *       "guesser fixes first" (same information as the loop, no machinery).
 *   one guess, low / high / max thinking - a fresh first guess (a model), run by the checker on the questions.
 *   guesser fixes first, low / high / max thinking - the loop from that guess, with DeepSeek at the same setting.
 *
 * Replies are limited to 32,000 tokens, thinking included; a reply cut off there answers nothing and is
 * counted in the results. ONLY_UNLIMITED=1 runs just one more arm, DeepSeek alone at max thinking with
 * a limit of 200,000 tokens, so that the limit is not what stops thinking harder (log 19).
 *
 * Run with:
 *   DEEPSEEK_API_KEY=... NODE_USE_ENV_PROXY=1 node "19 baseline and more thinking.js" OUTFOLDER [REPEATS] [WORLD,WORLD]
 *   node "19 baseline and more thinking.js" --questions   (show the questions, no DeepSeek)
 */
const fs = require('fs');
const path = require('path');
const C = require('./03 checker.js');
const L = require('./09 loop.js');

const WORLDS = require('./03 test worlds.js').concat(require('./18 more test worlds.js'));
const EFFORTS = ['low', 'high', 'max'];
const NEARBY = 20;

function stable_key(text) {
  let h = 2166136261;
  for (const ch of text) { h ^= ch.charCodeAt(0); h = Math.imul(h, 16777619) >>> 0; }
  return h;
}
const lower = t => String(t).trim().toLowerCase();
function situation_in_words(situation) {
  const parts = [];
  const start = Object.entries(situation.start || {}).map(([t, s]) => `${t} is ${s}`);
  if (start.length) parts.push(`start with ${start.join(', ')}`);
  const events = Object.keys(situation.events || {}).sort((a, b) => Number(a) - Number(b)).flatMap(k => situation.events[k]);
  parts.push(events.length ? `events in order: ${events.join(', then ')}` : 'no events');
  return parts.join('; ');
}
const split_expectation = text => { const m = /^(.+?) is (not )?(.+)$/.exec(String(text).trim()); return m ? { thing: m[1], negated: !!m[2], state: m[3] } : null; };

// The fixed questions for one world, with the world's answers.
function build_questions(world) {
  const world_model = C.prepare_model(world.world);
  const all_jobs = C.prepare_jobs({ jobs: world.jobs }).jobs;
  const held = all_jobs.filter(j => j.held_back);
  const asked_things = [...new Set(all_jobs.flatMap(j => j.expect.map(e => split_expectation(e).thing)))];
  const questions = [];
  const left_out = [];
  for (const job of held) {
    if (!['end', 'ever', 'never'].includes(job.at)) { left_out.push(job.name); continue; }
    const parts = job.expect.map(split_expectation);
    questions.push({ id: `Q${questions.length + 1}`, kind: 'held-back', job: job.name, situation: job.situation, at: job.at, parts,
      words: job.at === 'end' ? `${situation_in_words(job.situation)}. At the end, what state is each of these in: ${parts.map(p => p.thing).join(', ')}?`
        : `${situation_in_words(job.situation)}. ${parts.map(p => `Is ${p.thing} ${p.state} at any point, from the start to the end? Answer yes or no.`).join(' ')}` });
  }
  const job_situations = new Set(all_jobs.map(j => JSON.stringify(j.situation)));
  const candidates = C.candidate_situations(world_model, world_model, all_jobs, 400, null).list
    .filter(c => c.steps.length && !job_situations.has(JSON.stringify(c.situation)))
    .map(c => Object.assign({ key: stable_key(`${world.id}|${JSON.stringify(c.situation)}`) }, c)).sort((a, b) => a.key - b.key);
  for (const c of candidates) {
    if (questions.filter(q => q.kind === 'nearby').length >= NEARBY) break;
    const problems = [];
    const resolved = C.resolve_situation(world_model, c.situation, problems, 'question');
    if (problems.length) continue;
    const result = C.run(world_model, resolved);
    if (result.clashes.length) continue;
    const ends = {};
    let settled = true;
    for (const thing of asked_things) { const e = [...new Set(result.final_states.map(s => s[thing]))]; if (e.length !== 1) settled = false; ends[thing] = e[0]; }
    if (!settled) continue;
    questions.push({ id: `Q${questions.length + 1}`, kind: 'nearby', situation: c.situation, at: 'end', parts: asked_things.map(thing => ({ thing, negated: false, state: ends[thing] })),
      words: `${situation_in_words(c.situation)}. At the end, what state is each of these in: ${asked_things.join(', ')}?` });
  }
  return { questions, left_out };
}

// Grade DeepSeek's direct answers: {Q1: {thing: state}, Q2: "yes"}.
function grade_direct(questions, answers) {
  return questions.map(q => {
    const a = answers && answers[q.id];
    let right;
    if (q.at === 'end') {
      const got = a && typeof a === 'object' ? Object.fromEntries(Object.entries(a).map(([k, v]) => [lower(k), lower(v)])) : {};
      right = q.parts.every(p => (p.negated ? got[lower(p.thing)] !== undefined && got[lower(p.thing)] !== lower(p.state) : got[lower(p.thing)] === lower(p.state)));
    } else {
      const said = lower(typeof a === 'object' && a ? Object.values(a)[0] : a);
      right = said.startsWith(q.at === 'ever' ? 'yes' : 'no');
    }
    return { id: q.id, kind: q.kind, right };
  });
}
// Grade a model on the same questions, by running it.
function grade_model(questions, model) {
  return questions.map(q => {
    let right = false;
    if (q.kind === 'held-back') {
      const expect = q.parts.map(p => `${p.thing} is ${p.negated ? 'not ' : ''}${p.state}`);
      right = C.check_job(model, { name: q.id, situation: q.situation, expect, at: q.at }).passed;
    } else {
      const problems = [];
      const resolved = C.resolve_situation(model, q.situation, problems, 'question');
      if (!problems.length) {
        const result = C.run(model, resolved);
        right = q.parts.every(p => { const t = Object.keys(model.things).find(x => lower(x) === lower(p.thing)); return t && [...new Set(result.final_states.map(s => lower(s[t])))].join('/') === lower(p.state); });
      }
    }
    return { id: q.id, kind: q.kind, right };
  });
}
function majority(answer_sets, questions) {
  const out = {};
  for (const q of questions) {
    if (q.at === 'end') {
      out[q.id] = {};
      for (const p of q.parts) {
        const votes = {};
        for (const set of answer_sets) { const a = set && set[q.id]; const v = a && typeof a === 'object' ? Object.entries(a).find(([k]) => lower(k) === lower(p.thing)) : null; if (v) votes[lower(v[1])] = (votes[lower(v[1])] || 0) + 1; }
        const best = Object.entries(votes).sort((a, b) => b[1] - a[1])[0];
        if (best) out[q.id][p.thing] = best[0];
      }
    } else {
      const votes = {};
      for (const set of answer_sets) { const a = set && set[q.id]; const v = lower(typeof a === 'object' && a ? Object.values(a)[0] : a); if (v) votes[v.startsWith('y') ? 'yes' : 'no'] = (votes[v.startsWith('y') ? 'yes' : 'no'] || 0) + 1; }
      const best = Object.entries(votes).sort((a, b) => b[1] - a[1])[0];
      if (best) out[q.id] = best[0];
    }
  }
  return out;
}

function direct_messages(world, questions, extra_answers) {
  const shown = C.prepare_jobs({ jobs: world.jobs.filter(j => !j.held_back) }).jobs;
  const extra = extra_answers && extra_answers.length ? `\n\nMore answers, given by the owner when asked:\n${extra_answers.map(L.job_in_words).join('\n')}` : '';
  return [
    { role: 'system', content: 'You answer questions about what happens in situations described in words. Work out each answer from the task and the answers you are given.' },
    { role: 'user', content: `Task: ${world.request}\n\n${L.vocabulary_in_words(world)}\n\nAnswers the owner has given (each: a situation, and what is expected):\n${shown.map(L.job_in_words).join('\n')}${extra}\n\nQuestions:\n${questions.map(q => `${q.id}: ${q.words}`).join('\n')}\n\nReply with JSON only, one entry per question. For a question about the end, give each thing's state using the state names above: {"Q1": {"THING": "STATE"}}. For a yes-or-no question give "yes" or "no": {"Q2": "yes"}.` },
  ];
}
async function ask_direct(guesser, world, questions, extra_answers) {
  const messages = direct_messages(world, questions, extra_answers);
  const body_guesser = async () => {
    const text = await guesser(messages, { reply_shape: 'none' });
    return { text, usage: guesser.last_usage };
  };
  const { text, usage } = await body_guesser();
  return { answers: L.read_reply(text), text, tokens_out: usage ? usage.tokens_out : 0, tokens_in: usage ? usage.tokens_in : 0 };
}
const tally = graded => ({ held_back_right: graded.filter(g => g.kind === 'held-back' && g.right).length, held_back_total: graded.filter(g => g.kind === 'held-back').length,
  nearby_right: graded.filter(g => g.kind === 'nearby' && g.right).length, nearby_total: graded.filter(g => g.kind === 'nearby').length });
const log_tokens = log => log.reduce((sum, e) => sum + (e.tokens_out || 0), 0);

module.exports = { build_questions, grade_direct, grade_model, majority, direct_messages, ask_direct, situation_in_words, stable_key, tally };

async function run_world(world, repeat, D) {
  const { questions, left_out } = build_questions(world);
  const arms = {};
  const record_arm = (name, graded, extra) => { arms[name] = Object.assign(tally(graded), extra, { graded }); };
  if (process.env.ONLY_UNLIMITED) {
    const g = D.make_deepseek_guesser(undefined, { effort: 'max', reply_limit: 200000 });
    const d = await ask_direct(g, world, questions);
    record_arm('DeepSeek alone, max thinking, reply limit 200,000', grade_direct(questions, d.answers), { calls: 1, tokens_out: d.tokens_out, cut_off: g.counts.cut_off, reply: d.text });
    return { world: world.id, repeat, guesser: D.MODEL_NAME, questions: questions.map(q => ({ id: q.id, kind: q.kind, job: q.job, words: q.words, world_says: q.parts })), left_out_timing_jobs: left_out, arms };
  }
  for (const effort of EFFORTS) {
    const g = D.make_deepseek_guesser(undefined, { effort });
    const d = await ask_direct(g, world, questions);
    record_arm(`DeepSeek alone, ${effort} thinking`, grade_direct(questions, d.answers), { calls: 1, tokens_out: d.tokens_out, reply: d.text });
    const guess_guesser = D.make_deepseek_guesser(undefined, { effort });
    const guess = await L.first_guess(world, { guesser: guess_guesser });
    const one = await L.run_task(world, 'one guess', { guesser: guess_guesser }, guess);
    record_arm(`one guess, ${effort} thinking`, grade_model(questions, C.prepare_model(one.model)), { calls: 1, tokens_out: log_tokens(one.log), model: one.model });
    const fixes = await L.run_task(world, 'guesser fixes first', { guesser: guess_guesser }, guess);
    record_arm(`guesser fixes first, ${effort} thinking`, grade_model(questions, C.prepare_model(fixes.model)), { calls: 1 + fixes.guesser_calls, tokens_out: log_tokens(fixes.log), questions_to_world: fixes.questions_to_world, held_back_asked: fixes.final.held_back_asked, model: fixes.model, rounds: fixes.rounds, log: fixes.log });
    if (effort === 'high') {
      const extra = C.prepare_jobs({ jobs: fixes.added_jobs.map(a => a.job) }).jobs;
      const w = await ask_direct(D.make_deepseek_guesser(undefined, { effort }), world, questions, extra);
      record_arm(`DeepSeek alone, high thinking, with the world's answers`, grade_direct(questions, w.answers), { calls: 1, tokens_out: w.tokens_out, world_answers_given: extra.length, reply: w.text });
      const replies = [d];
      for (let i = 0; i < 4; i++) replies.push(await ask_direct(D.make_deepseek_guesser(undefined, { effort }), world, questions));
      record_arm(`DeepSeek alone, high thinking, majority of 5`, grade_direct(questions, majority(replies.map(r => r.answers), questions)), { calls: 5, tokens_out: replies.reduce((s, r) => s + r.tokens_out, 0) });
    }
  }
  return { world: world.id, repeat, guesser: D.MODEL_NAME, questions: questions.map(q => ({ id: q.id, kind: q.kind, job: q.job, words: q.words, world_says: q.parts })), left_out_timing_jobs: left_out, arms };
}

if (require.main === module) {
  const [out_folder, repeats_text, which] = process.argv.slice(2);
  const worlds = WORLDS.filter(w => !which || which.split(',').includes(w.id));
  if (out_folder === '--questions') {
    for (const w of worlds) { const { questions, left_out } = build_questions(w); console.log(`${w.id}: ${questions.filter(q => q.kind === 'held-back').length} held-back, ${questions.filter(q => q.kind === 'nearby').length} nearby; left out (about a step): ${left_out.join(', ') || 'none'}`); console.log(`   e.g. ${questions[0].words}\n   e.g. ${questions[questions.length - 1].words}`); }
    process.exit(0);
  }
  const D = require('./17 DeepSeek guesser.js');
  const REPEATS = Number(repeats_text) || 1;
  fs.mkdirSync(out_folder, { recursive: true });
  (async () => {
    const jobs = [];
    for (const w of worlds) for (let r = 1; r <= REPEATS; r++) jobs.push([w, r]);
    const records = await Promise.all(jobs.map(async ([w, r]) => {
      try {
        const rec = await run_world(w, r, D);
        fs.writeFileSync(path.join(out_folder, `${w.id} repeat ${r}.json`), JSON.stringify(rec, null, 1) + '\n');
        console.log(`${w.id} repeat ${r} done`);
        return rec;
      } catch (e) { console.log(`${w.id} repeat ${r} failed: ${e.message}`); return { world: w.id, repeat: r, failed: String(e.message) }; }
    }));
    const names = [...new Set(records.filter(r => !r.failed).flatMap(r => Object.keys(r.arms)))];
    const lines = ['| Arm | Held-back questions right | Nearby questions right | DeepSeek calls | Output tokens (thinking included) |', '|---|---|---|---|---|'];
    for (const n of names) {
      const t = { hr: 0, ht: 0, nr: 0, nt: 0, calls: 0, tokens: 0 };
      for (const rec of records.filter(r => !r.failed)) { const a = rec.arms[n]; if (!a) continue; t.hr += a.held_back_right; t.ht += a.held_back_total; t.nr += a.nearby_right; t.nt += a.nearby_total; t.calls += a.calls; t.tokens += a.tokens_out; }
      lines.push(`| ${n} | ${t.hr}/${t.ht} | ${t.nr}/${t.nt} | ${t.calls} | ${t.tokens} |`);
    }
    const failed = records.filter(r => r.failed).map(r => `- ${r.world} repeat ${r.repeat}: ${r.failed}`);
    fs.writeFileSync(path.join(out_folder, 'results.md'), `# Baseline and more thinking: results\n\nGuesser: DeepSeek V4.1 Flash. Every number below comes from the records in this folder, summed over ${records.length - failed.length} world-and-repeat runs.\n\n${lines.join('\n')}\n${failed.length ? `\nRuns that failed:\n${failed.join('\n')}\n` : ''}`);
    console.log(lines.join('\n'));
  })();
}
