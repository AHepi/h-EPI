/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * The error-correction test (log 18). DeepSeek's first guesses are often right, so the first run
 * hardly exercised correction. Here the mistakes are planted on purpose, so every run has something
 * to correct, and what "corrected" means is known exactly.
 *
 * How the mistakes are planted: take a world's hidden true model and make every one-step change the
 * checker knows (remove a rule, drop, flip or swap a condition, change a result). Each changed model
 * is sorted into:
 *   visible mistake - it fails at least one shown job, so the checker can see it
 *   hidden mistake  - it passes every shown job but fails a held-back job; only questions, a review
 *                     or luck can find it
 * From each world, one visible and two hidden mistakes are picked by a fixed shuffle of their
 * descriptions (not chosen by hand). Two more are written by hand, because they need a whole new
 * thing to repair: the hidden ball without "where the ball really is", and the to-do app without
 * a count of put-offs.
 *
 * Each planted model is then handed to seven correctors, as if it were the guesser's first guess:
 *   checker alone  - small fixes and the checker's own new rule search; DeepSeek is never asked
 *   rewrite        - DeepSeek rewrites the model from the checker's report
 *   self review    - DeepSeek reviews the model against the request, with no report from the checker
 *   guess and fix  - checker's small fixes, DeepSeek asked for new parts
 *   full loop      - guess and fix plus questions to the world
 *   guesser fixes first - the full loop, but when jobs fail DeepSeek rewrites the model first
 *   review first   - self review, then guesser fixes first
 *
 * Graded three ways: shown jobs, held-back jobs, and "nearby situations": up to 400 situations one or
 * two changes from the jobs, run on both the corrected model and the world, counting where they end
 * differently. That last one catches a correction that fits the jobs but is still wrong.
 *
 * Run with:
 *   DEEPSEEK_API_KEY=... NODE_USE_ENV_PROXY=1 node "18 planted mistakes.js" OUTFOLDER [WORLD,WORLD]
 *   node "18 planted mistakes.js" --list      (show the planted mistakes, no DeepSeek)
 * ONLY=a,b runs only those correctors (a corrector added later runs on the same planted mistakes).
 */
const fs = require('fs');
const path = require('path');
const C = require('./03 checker.js');
const L = require('./09 loop.js');

const ALL_WORLDS = require('./03 test worlds.js').concat(require('./18 more test worlds.js'));
const CORRECTORS = ['checker alone', 'rewrite', 'self review', 'guess and fix', 'full loop', 'guesser fixes first', 'review first'];

function stable_shuffle_key(text) {
  let h = 2166136261;
  for (const ch of text) { h ^= ch.charCodeAt(0); h = Math.imul(h, 16777619) >>> 0; }
  return h;
}
const jobs_of = (world, held_back) => C.prepare_jobs({ jobs: world.jobs.filter(j => !!j.held_back === held_back) }).jobs;

// Where does a model end differently from the world, near the jobs?
function nearby_differences(model, world) {
  const world_model = C.prepare_model(world.world);
  const all_jobs = C.prepare_jobs({ jobs: world.jobs }).jobs;
  const asked = [...new Set(all_jobs.flatMap(j => j.expect.map(e => String(e).split(/ is /)[0].replace(/^not /, ''))))];
  const list = C.candidate_situations(world_model, world_model, all_jobs, 400, null).list;
  let differ = 0, cannot_run = 0; const examples = [];
  for (const c of list) {
    const pw = [], pm = [];
    const sw = C.resolve_situation(world_model, c.situation, pw, 'grade');
    const sm = C.resolve_situation(model, c.situation, pm, 'grade');
    if (pw.length) continue;
    if (pm.length) { cannot_run++; continue; }
    const rw = C.run(world_model, sw), rm = C.run(model, sm);
    const ends = (r, m, thing) => { const t = Object.keys(m.things).find(x => x.toLowerCase() === thing.toLowerCase()); return t ? [...new Set(r.final_states.map(s => s[t]))].join('/').toLowerCase() : '(missing)'; };
    const wrong = asked.filter(t => ends(rw, world_model, t) !== ends(rm, model, t));
    if (wrong.length) { differ++; if (examples.length < 3) examples.push(`${C.describe_situation(c)}: ${wrong.map(t => `${t} ${ends(rm, model, t)}, world says ${ends(rw, world_model, t)}`).join('; ')}`); }
  }
  return { tried: list.length, differ, cannot_run, examples };
}

function plant(world) {
  const truth = C.prepare_model(world.world);
  const shown = jobs_of(world, false), held = jobs_of(world, true);
  const variants = [];
  truth.rules.forEach((rule, index) => {
    variants.push({ description: `rule "${rule.name}" removed`, model: Object.assign({}, truth, { rules: truth.rules.filter((_, j) => j !== index) }) });
    for (const n of C.neighbours(truth, index)) variants.push({ description: `in rule "${rule.name}": ${n.description}`, model: n.model });
  });
  const visible = [], hidden = [];
  for (const v of variants) {
    const s = C.check(v.model, shown), h = C.check(v.model, held);
    if (s.failed.length) visible.push(v);
    else if (h.failed.length) hidden.push(v);
  }
  const pick = (list, n) => list.map(v => Object.assign({ key: stable_shuffle_key(`${world.id}|${v.description}`) }, v)).sort((a, b) => a.key - b.key).slice(0, n);
  const planted = pick(visible, 1).map(v => ({ kind: 'visible', how: 'picked by the fixed shuffle', description: v.description, form: C.model_to_form(v.model) }))
    .concat(pick(hidden, 2).map(v => ({ kind: 'hidden', how: 'picked by the fixed shuffle', description: v.description, form: C.model_to_form(v.model) })));
  if (world.id === 'hidden-ball') {
    planted.push({ kind: 'needs a new thing', how: 'written by hand', description: 'no "where the ball really is": what is seen follows only what was seen before',
      form: { things: { screen: ['down', 'up'], seen: ['at 1', 'at 2', 'at 3', 'at 4', 'nothing'] }, events: [], start: { screen: 'down', seen: 'at 1' },
        rules: [{ name: 'a', when: ['seen is at 1', 'screen is down'], then: 'seen is at 2' }, { name: 'b', when: ['seen is at 2'], then: 'seen is at 3' }, { name: 'c', when: ['seen is at 3'], then: 'seen is at 4' },
          { name: 'hide', when: ['seen is at 1', 'screen is up'], then: 'seen is nothing' }] } });
  }
  if (world.id === 'reminder-app') {
    planted.push({ kind: 'needs a new thing', how: 'written by hand', description: 'no count of put-offs: one put-off makes a task urgent',
      form: { things: { task: ['new', 'urgent', 'overdue', 'done'] }, events: ['snooze', 'finish', 'day passes'], start: { task: 'new' },
        rules: [{ name: 'put off', when: ['snooze happens', 'task is new'], then: 'task is urgent' }, { name: 'overdue', when: ['day passes happens', 'task is urgent'], then: 'task is overdue' },
          { name: 'finish', when: ['finish happens'], then: 'task is done' }] } });
  }
  return planted.map(p => Object.assign(p, {
    before: { shown: `${C.check(C.prepare_model(p.form), shown).passed.length}/${shown.length}`, held_back: `${C.check(C.prepare_model(p.form), held).passed.length}/${held.length}`, nearby: nearby_differences(C.prepare_model(p.form), world) },
  }));
}

async function correct(world, planted, corrector, guesser) {
  const refuse = async () => { throw new Error('the checker-alone corrector must not ask the guesser'); };
  const options = corrector === 'checker alone' ? { guesser: refuse, new_part_calls: 0 } : { guesser };
  const mode = corrector === 'checker alone' ? 'guess and fix' : corrector;
  const r = await L.run_task(world, mode, options, { raw: planted.form, log: [] });
  const model = C.prepare_model(r.model);
  return { corrector, shown: `${r.final.original_seen_passed}/${r.final.original_seen_total}`, held_back: `${r.final.held_back_passed}/${r.final.held_back_total}`,
    held_back_asked: r.final.held_back_asked, questions_to_world: r.questions_to_world, deepseek_asked: r.guesser_calls,
    nearby: nearby_differences(model, world), rounds: r.rounds, model: r.model, log: r.log };
}

module.exports = { plant, nearby_differences, CORRECTORS, ALL_WORLDS };

if (require.main === module) {
  const [out_folder, which] = process.argv.slice(2);
  const worlds = ALL_WORLDS.filter(w => !which || which.split(',').includes(w.id));
  if (out_folder === '--list') {
    for (const w of worlds) for (const p of plant(w)) console.log(`${w.id.padEnd(17)} ${p.kind.padEnd(17)} shown ${p.before.shown} held-back ${p.before.held_back} nearby wrong ${p.before.nearby.differ}/${p.before.nearby.tried} | ${p.description}`);
    process.exit(0);
  }
  const D = require('./17 DeepSeek guesser.js');
  fs.mkdirSync(out_folder, { recursive: true });
  (async () => {
    const tasks = [];
    for (const w of worlds) plant(w).forEach((p, i) => tasks.push({ w, p, i: i + 1 }));
    let next = 0;
    const lines = [];
    const worker = async () => {
      while (next < tasks.length) {
        const { w, p, i } = tasks[next++];
        const guesser = D.make_deepseek_guesser();
        const results = [];
        for (const corrector of (process.env.ONLY ? process.env.ONLY.split(',') : CORRECTORS)) {
          try { results.push(await correct(w, p, corrector, guesser)); } catch (e) { results.push({ corrector, failed: String(e.message || e) }); }
          const x = results[results.length - 1];
          const line = x.failed ? `${w.id} mistake ${i} | ${corrector} | failed: ${x.failed}` : `${w.id} mistake ${i} (${p.kind}) | ${corrector.padEnd(13)} | shown ${x.shown} | held-back ${x.held_back} | nearby wrong ${x.nearby.differ}/${x.nearby.tried} (was ${p.before.nearby.differ}) | questions ${x.questions_to_world} | DeepSeek asked ${x.deepseek_asked}`;
          console.log(line); lines.push(line);
        }
        fs.writeFileSync(path.join(out_folder, `${w.id} mistake ${i}.json`), JSON.stringify({ world: w.id, planted: p, guesser: D.MODEL_NAME, counts: guesser.counts, results }, null, 1) + '\n');
      }
    };
    await Promise.all(Array.from({ length: Number(process.env.AT_ONCE) || 8 }, worker));
    fs.writeFileSync(path.join(out_folder, 'progress lines.txt'), lines.sort().join('\n') + '\n');
  })();
}
