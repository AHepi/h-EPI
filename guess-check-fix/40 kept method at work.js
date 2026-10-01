/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Log 40. Log 39's kept fix-acceptance methods, put to work in the checker's own correction loop, with no
 * AI. From a model with a planted mistake, each round lists every one-step change that makes a failing
 * shown job pass, orders them (most jobs repaired first, then a fixed scramble), and applies the first one
 * the method accepts; up to 5 rounds, stopping when every shown job passes or nothing is accepted.
 * Measured at the end: damage (nearby situations right at the start and wrong at the end), whether every
 * shown job passes, held-back jobs passing, and questions asked of the world.
 * The methods run in log 39's separate process, which records every question.
 * The plan and conjectures: "40 Plan - a kept method at work.md".
 *
 * Run with:  node "40 kept method at work.js" OUTFOLDER
 *            node "40 kept method at work.js" --summarise FOLDER
 */
const fs = require('fs');
const path = require('path');
const C = require('./03 checker.js');
const O = require('./39 occasions.js');
const M = require('./39 changing a method.js');

const ROUNDS = 5;
const STARTS_PER_WORLD = 8;
const SHOWN_WORLDS = ['lighthouse-story', 'ball-and-wall'];

function methods() {
  const out = { 'current method': M.CURRENT, 'log 17\'s repair (a person)': M.REFERENCE };
  for (let r = 1; r <= 3; r++) {
    const file = path.join(__dirname, 'runs', '39 changing a method', `repeat ${r}.json`);
    out[`DeepSeek's method, repeat ${r}`] = JSON.parse(fs.readFileSync(file, 'utf8')).arms['shown the failure'].code;
  }
  return out;
}

// What a world looks like to the loop: its shown jobs, held-back jobs, nearby situations and the world's endings.
function setting(world) {
  const truth = C.prepare_model(world.world);
  const all_jobs = C.prepare_jobs({ jobs: world.jobs }).jobs;
  const things = [...new Set(all_jobs.flatMap(j => j.expect.map(e => String(e).split(/ is /)[0].replace(/^not /, ''))))];
  const nearby = C.candidate_situations(truth, truth, all_jobs, O.NEARBY, null).list.slice(0, O.NEARBY);
  return { world, shown: O.shown_jobs(world), held: C.prepare_jobs({ jobs: world.jobs.filter(j => j.held_back) }).jobs, things, nearby, world_says: nearby.map(c => O.ending_words(truth, c.situation, things)) };
}
const endings = (s, model) => s.nearby.map(c => O.ending_words(model, c.situation, s.things));

function starts_of(s) {
  return O.mistaken_models(s.world).sort((a, b) => O.scramble_key(`${s.world.id}|start|${a.description}`) - O.scramble_key(`${s.world.id}|start|${b.description}`)).slice(0, STARTS_PER_WORLD);
}

// One-step changes that make at least one failing shown job pass, in the loop's order.
function candidates(s, model) {
  const was = new Set(C.check(model, s.shown).passed);
  const list = [];
  model.rules.forEach((rule, index) => {
    list.push({ description: `rule "${rule.name}" removed`, model: Object.assign({}, model, { rules: model.rules.filter((_, j) => j !== index) }) });
    for (const n of C.neighbours(model, index)) list.push({ description: `in rule "${rule.name}": ${n.description}`, model: n.model });
  });
  return list.map(c => {
    const now = new Set(C.check(c.model, s.shown).passed);
    return Object.assign(c, { now, repaired: [...now].filter(j => !was.has(j)).length });
  }).filter(c => c.repaired > 0)
    .sort((a, b) => b.repaired - a.repaired || O.scramble_key(a.description) - O.scramble_key(b.description))
    .map(c => ({ c, was }));
}

function correct(s, start, code) {
  let model = start.model;
  const at_start = endings(s, model);
  let questions = 0, rounds = 0, stopped = 'every shown job passes', error = null;
  const trail = [];
  for (let round = 1; round <= ROUNDS; round++) {
    if (!C.check(model, s.shown).failed.length) { stopped = 'every shown job passes'; break; }
    const list = candidates(s, model);
    if (!list.length) { stopped = 'no change repairs a job'; break; }
    const before_says = endings(s, model);
    const occasions = list.map(({ c, was }) => ({
      case: {
        jobs: s.shown.map(j => ({ name: j.name, before: was.has(j.name) ? 'pass' : 'fail', after: c.now.has(j.name) ? 'pass' : 'fail' })),
        nearby: s.nearby.map((n, i) => ({ id: i, situation: C.describe_situation(n), before: before_says[i], after: O.ending_words(c.model, n.situation, s.things) })),
      },
      world_says: s.world_says,
    }));
    const ran = M.run_method(code, occasions);
    if (ran.error) { error = ran.error; stopped = 'the method failed'; break; }
    const pick = ran.results.findIndex(r => r.accept && !r.error);
    const upto = pick >= 0 ? pick + 1 : ran.results.length;
    questions += ran.results.slice(0, upto).reduce((sum, r) => sum + (r.asked || []).length, 0);
    const errors = ran.results.slice(0, upto).filter(r => r.error);
    if (errors.length) { error = errors[0].error; stopped = 'the method failed'; break; }
    rounds = round;
    if (pick < 0) { stopped = 'the method accepted no change'; break; }
    trail.push(list[pick].c.description);
    model = list[pick].c.model;
    if (round === ROUNDS && C.check(model, s.shown).failed.length) stopped = 'out of rounds';
  }
  const at_end = endings(s, model);
  return {
    start: start.description, rounds, stopped, error, trail, questions,
    shown_all_pass: !C.check(model, s.shown).failed.length,
    held_passing: C.check(model, s.held).passed.length, held_total: s.held.length,
    damage: s.nearby.filter((_, i) => at_start[i] === s.world_says[i] && at_end[i] !== s.world_says[i]).length,
    wrong_at_start: s.nearby.filter((_, i) => at_start[i] !== s.world_says[i]).length,
    wrong_at_end: s.nearby.filter((_, i) => at_end[i] !== s.world_says[i]).length,
  };
}

function run_all() {
  const m = methods();
  const records = [];
  for (const world of O.WORLDS) {
    const s = setting(world);
    for (const start of starts_of(s)) {
      const row = { world: world.id, held_out: !SHOWN_WORLDS.includes(world.id), start: start.description, methods: {} };
      for (const [name, code] of Object.entries(m)) row.methods[name] = correct(s, start, code);
      records.push(row);
    }
  }
  return records;
}

function summarise(records) {
  const names = Object.keys(records[0].methods);
  const block = (rows, title) => {
    const current = n => rows.map(r => r.methods['current method']);
    const lines = [`${title} (${rows.length} starts)`, '', '| Method | Total damage | Starts with damage | Starts ending with every shown job passing | Held-back jobs passing | Questions asked | Failures | Starts losing P1 | Starts with more damage than the current method |', '|---|---|---|---|---|---|---|---|---|'];
    for (const n of names) {
      const res = rows.map(r => r.methods[n]);
      const cur = current();
      const p1 = res.filter((x, i) => cur[i].shown_all_pass && !x.shown_all_pass).length;
      const worse = res.filter((x, i) => x.damage > cur[i].damage).length;
      lines.push(`| ${n} | ${res.reduce((s, x) => s + x.damage, 0)} | ${res.filter(x => x.damage > 0).length} | ${res.filter(x => x.shown_all_pass).length} | ${res.reduce((s, x) => s + x.held_passing, 0)}/${res.reduce((s, x) => s + x.held_total, 0)} | ${res.reduce((s, x) => s + x.questions, 0)} | ${res.filter(x => x.error).length} | ${p1} | ${worse} |`);
    }
    return lines.join('\n');
  };
  return [block(records.filter(r => r.held_out), 'Held-out worlds'), '', block(records.filter(r => !r.held_out), 'The two worlds log 39 showed DeepSeek')].join('\n');
}
const results_text = records => `# A kept method at work: results\n\nThe checker's correction loop, with no AI, from planted-mistake starts, with each fix-acceptance method. Every number comes from records.json in this folder. Damage: nearby situations (of 40) the model had right at the start and wrong at the end.\n\n${summarise(records)}\n`;

module.exports = { methods, setting, starts_of, candidates, correct, run_all, summarise, ROUNDS, STARTS_PER_WORLD };

if (require.main === module) {
  const [first, second] = process.argv.slice(2);
  if (first === '--summarise') {
    const records = JSON.parse(fs.readFileSync(path.join(second, 'records.json'), 'utf8'));
    const text = results_text(records);
    fs.writeFileSync(path.join(second, 'results.md'), text);
    console.log(text);
  } else {
    fs.mkdirSync(first, { recursive: true });
    const records = run_all();
    fs.writeFileSync(path.join(first, 'records.json'), JSON.stringify(records, null, 1) + '\n');
    const text = results_text(records);
    fs.writeFileSync(path.join(first, 'results.md'), text);
    console.log(text);
  }
}
