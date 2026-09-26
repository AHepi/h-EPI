/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Builds the "occasions" for log 39: each is one fix the checker's small-fix search found for a model with
 * a planted mistake, which the fix-acceptance method must accept or reject. For each occasion it records
 * only what a method may see:
 *   jobs    - each job's name, whether it passed before the fix and after it
 *   nearby  - up to 40 situations near the jobs, each in words, with how the model before and after the
 *             fix says it ends
 * and, kept apart, what the world says each nearby situation ends as (a method may ask up to three), and
 * the occasion's kind, from the world:
 *   losing  - the fix loses a job that passed before (the current method rejects these)
 *   bad     - the fix repairs a job and loses none, but makes the model disagree with the world somewhere
 *             nearby where it agreed before (the current method accepts these: log 17's failure)
 *   good    - the fix repairs a job, loses none, and breaks nothing nearby
 * Everything is built from the ten worlds and log 18's planted mistakes, by fixed rules, with no AI.
 */
const C = require('./03 checker.js');

const WORLDS = require('./03 test worlds.js').concat(require('./18 more test worlds.js'));
const NEARBY = 40;
function scramble_key(text) {
  let h = 2166136261;
  for (const ch of text) { h ^= ch.charCodeAt(0); h = Math.imul(h, 16777619) >>> 0; }
  return h;
}
const shown_jobs = world => C.prepare_jobs({ jobs: world.jobs.filter(j => !j.held_back) }).jobs;

// How a model ends a situation, in words, for the things the jobs ask about.
function ending_words(model, situation, things) {
  const problems = [];
  const resolved = C.resolve_situation(model, situation, problems, 'occasion');
  if (problems.length) return '(cannot run)';
  const r = C.run(model, resolved);
  return things.map(t => {
    const name = Object.keys(model.things).find(x => x.toLowerCase() === t.toLowerCase());
    return `${t} ${name ? [...new Set(r.final_states.map(s => s[name]))].join('/') : '(missing)'}`;
  }).join(', ');
}

// Every model one step from the truth that fails a shown job: log 18's visible planted mistakes, all of them.
function mistaken_models(world) {
  const truth = C.prepare_model(world.world);
  const jobs = shown_jobs(world);
  const out = [];
  truth.rules.forEach((rule, index) => {
    const variants = [{ description: `rule "${rule.name}" removed`, model: Object.assign({}, truth, { rules: truth.rules.filter((_, j) => j !== index) }) }]
      .concat(C.neighbours(truth, index).map(n => ({ description: `in rule "${rule.name}": ${n.description}`, model: n.model })));
    for (const v of variants) if (C.check(v.model, jobs).failed.length) out.push(v);
  });
  return out;
}

function occasions_of(world) {
  const truth = C.prepare_model(world.world);
  const jobs = shown_jobs(world);
  const all_jobs = C.prepare_jobs({ jobs: world.jobs }).jobs;
  const things = [...new Set(all_jobs.flatMap(j => j.expect.map(e => String(e).split(/ is /)[0].replace(/^not /, ''))))];
  const nearby = C.candidate_situations(truth, truth, all_jobs, NEARBY, null).list.slice(0, NEARBY);
  const world_says = nearby.map(c => ending_words(truth, c.situation, things));
  const out = [];
  for (const start of mistaken_models(world)) {
    const before = start.model;
    const was = new Set(C.check(before, jobs).passed);
    const candidates = [];
    before.rules.forEach((rule, index) => {
      candidates.push({ description: `rule "${rule.name}" removed`, model: Object.assign({}, before, { rules: before.rules.filter((_, j) => j !== index) }) });
      for (const n of C.neighbours(before, index)) candidates.push({ description: `in rule "${rule.name}": ${n.description}`, model: n.model });
    });
    for (const fix of candidates) {
      const now = new Set(C.check(fix.model, jobs).passed);
      const repaired = [...now].filter(j => !was.has(j));
      if (!repaired.length) continue;
      const lost = [...was].filter(j => !now.has(j));
      const before_says = nearby.map(c => ending_words(before, c.situation, things));
      const after_says = nearby.map(c => ending_words(fix.model, c.situation, things));
      const broke = nearby.map((_, i) => before_says[i] === world_says[i] && after_says[i] !== world_says[i]).filter(Boolean).length;
      const kind = lost.length ? 'losing' : broke ? 'bad' : 'good';
      out.push({
        id: `${world.id} | ${start.description} | fix: ${fix.description}`, world: world.id, kind, broke,
        case: {
          jobs: jobs.map(j => ({ name: j.name, before: was.has(j.name) ? 'pass' : 'fail', after: now.has(j.name) ? 'pass' : 'fail' })),
          nearby: nearby.map((c, i) => ({ id: i, situation: C.describe_situation(c), before: before_says[i], after: after_says[i] })),
        },
        world_says,
      });
    }
  }
  return out;
}

// The fixed selection: per world, up to 3 of each kind, by a fixed scramble of the ids.
function occasions(per_kind = 3) {
  const out = [];
  for (const world of WORLDS) {
    const all = occasions_of(world).sort((a, b) => scramble_key(a.id) - scramble_key(b.id));
    for (const kind of ['bad', 'good', 'losing']) out.push(...all.filter(o => o.kind === kind).slice(0, per_kind));
  }
  return out;
}

module.exports = { occasions, occasions_of, mistaken_models, WORLDS, NEARBY };

if (require.main === module) {
  const list = occasions();
  const by = {};
  for (const o of list) { by[o.world] = by[o.world] || { bad: 0, good: 0, losing: 0 }; by[o.world][o.kind]++; }
  console.log(JSON.stringify(by, null, 1));
  console.log('total', list.length);
}
