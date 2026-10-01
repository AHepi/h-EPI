/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Log 49. Every result from log 44 to log 48 was about one device, the grudge. This takes the main
 * comparison to a second device, the heater ("49 heater.js"), with log 25's way of choosing 14
 * observations and 12 test cases.
 *
 * Three arms, six repeats each. Every arm ends the same way: a fresh DeepSeek sees the observations and
 * whatever answers from the world its arm collected, and writes one explanation as a small JavaScript
 * function. The function is run (in log 34's separate process with no files, network or key) on every
 * sequence of one to six actions that is not an observation, and graded against the true heater.
 *   bare            - no answers from the world
 *   random answers  - the world's answers about 6 random unseen situations of up to four actions
 *   rivals choose   - as log 46: two rounds, each a fresh DeepSeek writes 4 rival functions fitting every
 *                     known fact; the program asks the world about the 3 situations of up to four actions
 *                     where the fitting rivals are most evenly split. The final DeepSeek sees the facts
 *                     only, never the rivals (logs 47 and 48 found showing them did not help).
 * The world refuses log 25's 12 test cases, as before.
 *
 * Run with:
 *   DEEPSEEK_API_KEY=... NODE_USE_ENV_PROXY=1 node "49 second device.js" OUTFOLDER [REPEATS]
 *   node "49 second device.js" --summarise OUTFOLDER
 */
const fs = require('fs');
const path = require('path');
const K = require('./25 construction worlds.js');
const X = require('./25 construction test.js');
const A = require('./26 attack surface.js');
const P = require('./34 language test.js');
const G = require('./45 grudge again.js');
const { DEVICE } = require('./49 heater.js');

const ROUNDS = 2;
const RIVALS = 4;
const ASKED_PER_ROUND = 3;
const ARMS = ['bare', 'random answers', 'rivals choose'];
const THING = DEVICE.visible[0];
const STATES = DEVICE.world.things[THING];
const key_of = events => events.join('>');
const mix = text => [...text].reduce((h, ch) => Math.imul(h ^ ch.charCodeAt(0), 16777619) >>> 0, 2166136261);
const SHORT = K.sequences(DEVICE.world.events, 4);
const EVERY = K.sequences(DEVICE.world.events, 6);
const truth = events => K.ending(DEVICE, events)[0].split(' is ')[1];

const FUNCTION_SHAPE = `a JavaScript function named visible that takes the list of actions, in order, as an array of strings (${DEVICE.world.events.map(e => `"${e}"`).join(', ')}), starting fresh, and returns {"${THING}": ${STATES.map(s => `"${s}"`).join(' or ')}}. Start it with a one-line comment saying the explanation in words. Use no outside libraries.`;
const facts_in_words = facts => (facts.length ? `\n\nMore observations, each also from the start:\n${facts.map(f => `- ${f.events.join(', then ')}. At the end: ${THING} is ${f.state}.`).join('\n')}` : '');
const RIVAL_ASK = (observations, facts) => `${X.evidence_in_words(DEVICE, observations)}${facts_in_words(facts)}

Write ${RIVALS} rival explanations. Each must fit every observation above. Make them as different from each other as you can about situations nobody has observed yet: different hidden things, different ways each action works. They are rivals, so at most one of them can be right.

Write each as ${FUNCTION_SHAPE} Put each rival in its own \`\`\`javascript code block.`;
const FINAL_ASK = (observations, facts) => `${X.evidence_in_words(DEVICE, observations)}${facts_in_words(facts)}

Write the one explanation you think is right, as ${FUNCTION_SHAPE} Put it in one \`\`\`javascript code block.`;

function read_functions(text, how_many) {
  return [...String(text || '').matchAll(/```(?:javascript|js)?\s*\n([\s\S]*?)```/gi)].map(m => m[1].trim()).filter(b => /function\s+visible|visible\s*=/.test(b)).slice(0, how_many);
}
function predictions_of(code) {
  const ran = P.run_program(code, EVERY);
  if (ran.error) return { problem: ran.error };
  const said = {};
  for (let i = 0; i < EVERY.length; i++) {
    const r = ran.results[i];
    let value = null;
    try { value = r && !r.error ? JSON.parse(r.value) : null; } catch (e) { value = null; }
    const state = value && typeof value === 'object' ? value[THING] : undefined;
    if (!STATES.includes(state)) return { problem: `on ${EVERY[i].join(', ')} it gave ${r && r.error ? r.error : JSON.stringify(value)}` };
    said[key_of(EVERY[i])] = state;
  }
  return { said };
}
const comment_of = code => (code.match(/^\s*\/\/\s*(.*)$/m) || [])[1] || null;
const fits_all = (said, known) => !!said && known.every(k => said[key_of(k.events)] === k.state);

function setting() {
  const { observations, tests } = K.observations_and_tests(DEVICE);
  return { observations, tests, test_keys: new Set(tests.map(t => key_of(t.events))), observation_keys: new Set(observations.map(o => key_of(o.events))) };
}
// Grading on every sequence of one to six actions that is not an observation; "hard" are the short
// ones where the common-sense explanation is wrong.
function grade(said, observation_keys) {
  const cases = EVERY.filter(s => !observation_keys.has(key_of(s)));
  const right = s => !!said && said[key_of(s)] === truth(s);
  const short = cases.filter(s => s.length <= 4), long = cases.filter(s => s.length > 4);
  const hard = short.filter(s => !K.obvious_is_right(DEVICE, s));
  return { short_right: short.filter(right).length, short_all: short.length, long_right: long.filter(right).length, long_all: long.length, hard_right: hard.filter(right).length, hard_all: hard.length };
}
const true_everywhere = said => !!said && EVERY.every(s => said[key_of(s)] === truth(s));

function most_disputed(rivals, known_keys, refused_keys, how_many, salt) {
  if (rivals.length < 2) return [];
  return SHORT.filter(s => !known_keys.has(key_of(s)) && !refused_keys.has(key_of(s)))
    .map(s => { const first = rivals.filter(r => r.said[key_of(s)] === STATES[0]).length; return { events: s, split: Math.min(first, rivals.length - first), order: mix(`${salt}|${key_of(s)}`) }; })
    .filter(x => x.split > 0)
    .sort((a, b) => b.split - a.split || a.order - b.order)
    .slice(0, how_many).map(x => x.events);
}

async function final_function(D, observations, facts, observation_keys) {
  const g = D.make_deepseek_guesser();
  const text = await g([{ role: 'user', content: FINAL_ASK(observations, facts) }], { reply_shape: 'none' });
  const code = read_functions(text, 1)[0] || null;
  const p = code ? predictions_of(code) : { problem: 'no function in the reply' };
  return Object.assign(grade(p.said || null, observation_keys), { code, comment: code ? comment_of(code) : null, problem: p.problem || null, true_everywhere: true_everywhere(p.said), facts, world_answers: facts.length, tokens_out: g.counts.tokens_out, cut_off: g.counts.cut_off, text });
}

async function rivals_choose(D, observations, s, repeat) {
  const known = observations.map(o => ({ events: o.events, state: o.expect[0].split(' is ')[1] }));
  const facts = [];
  const rounds = [];
  let tokens = 0, cut = 0;
  for (let round = 1; round <= ROUNDS; round++) {
    const g = D.make_deepseek_guesser();
    const text = await g([{ role: 'user', content: RIVAL_ASK(observations, facts) }], { reply_shape: 'none' });
    tokens += g.counts.tokens_out; cut += g.counts.cut_off;
    const all_known = known.concat(facts);
    const rivals = read_functions(text, RIVALS).map(code => { const p = predictions_of(code); return { code, comment: comment_of(code), problem: p.problem || null, said: p.said || null, fits: fits_all(p.said, all_known), true_everywhere: true_everywhere(p.said) }; });
    const fitting = rivals.filter(r => r.fits);
    const asked = most_disputed(fitting, new Set(all_known.map(k => key_of(k.events))), s.test_keys, ASKED_PER_ROUND, `log 49 ${repeat} ${round}`);
    for (const events of asked) facts.push({ events, state: truth(events) });
    rounds.push({ round, rivals: rivals.map(({ said, ...r }) => r), fitting: fitting.length, asked: asked.map(key_of), text });
  }
  const final = await final_function(D, observations, facts, s.observation_keys);
  return Object.assign(final, { rounds, tokens_out: tokens + final.tokens_out, cut_off: cut + final.cut_off });
}

async function run_repeat(D, repeat) {
  const s = setting();
  const arms = {};
  arms['bare'] = await final_function(D, s.observations, [], s.observation_keys);
  const random = A.random_facts(DEVICE, s.observations, s.test_keys, ROUNDS * ASKED_PER_ROUND, `heater log 49 ${repeat}`).map(f => ({ events: f.events, state: f.answer.split(' is ')[1] }));
  arms['random answers'] = await final_function(D, s.observations, random, s.observation_keys);
  arms['rivals choose'] = await rivals_choose(D, s.observations, s, repeat);
  return { device: DEVICE.id, repeat, guesser: D.MODEL_NAME, reply_limit: 200000, arms };
}

function summarise(records) {
  const lines = ['| Arm | Short right (of 106 per run, summed) | Hard short right (common sense wrong) | Long right (of 972 per run, summed) | By repeat (short / long) | True heater everywhere (runs) | Answers from the world | Replies cut off |', '|---|---|---|---|---|---|---|---|'];
  for (const n of ARMS) {
    const a = records.map(r => r.arms[n]);
    const sum = k => a.reduce((t, x) => t + x[k], 0);
    lines.push(`| ${n} | ${sum('short_right')} | ${sum('hard_right')} of ${sum('hard_all')} | ${sum('long_right')} | ${a.map(x => `${x.short_right}/${x.long_right}`).join(', ')} | ${a.filter(x => x.true_everywhere).length} | ${sum('world_answers')} | ${sum('cut_off')} |`);
  }
  const rivals = records.flatMap(r => r.arms['rivals choose'].rounds.flatMap(x => x.rivals));
  lines.push('', `Rivals written: ${rivals.length}; ran on every sequence: ${rivals.filter(r => !r.problem).length}; fitted every fact known when written: ${rivals.filter(r => r.fits).length}; the true heater everywhere up to six actions: ${rivals.filter(r => r.true_everywhere).length}.`,
    `Output tokens: ${records.reduce((t, r) => t + ARMS.reduce((u, n) => u + r.arms[n].tokens_out, 0), 0)}.`,
    '', 'Final explanations, in DeepSeek\'s one-line comments:', '',
    ...records.flatMap(r => ARMS.map(n => `- repeat ${r.repeat}, ${n} (${r.arms[n].short_right}/${r.arms[n].long_right}): ${r.arms[n].comment || r.arms[n].problem || '(no comment)'}`)));
  return lines.join('\n');
}

module.exports = { setting, grade, predictions_of, read_functions, most_disputed, run_repeat, summarise, true_everywhere, ARMS, EVERY };

if (require.main === module) {
  const [first, second] = process.argv.slice(2);
  const read_records = folder => fs.readdirSync(folder).filter(f => /^heater repeat \d+\.json$/.test(f)).sort().map(f => JSON.parse(fs.readFileSync(path.join(folder, f), 'utf8')));
  const write_results = (folder, records, failed) => {
    const text = `# Second device, the heater: results\n\nDeepSeek V4.1 Flash, default thinking, reply limit 200000. ${records.length} repeats; every number comes from the records in this folder.\n\n${summarise(records)}\n${failed.length ? `\nRuns that failed:\n${failed.join('\n')}\n` : ''}`;
    fs.writeFileSync(path.join(folder, 'results.md'), text);
    console.log(text);
  };
  if (first === '--summarise') write_results(second, read_records(second), []);
  else {
    const D = G.with_higher_limit(require('./17 DeepSeek guesser.js'));
    const REPEATS = Number(second) || 1;
    fs.mkdirSync(first, { recursive: true });
    (async () => {
      const jobs = [];
      for (let r = 1; r <= REPEATS; r++) jobs.push(r);
      const records = await Promise.all(jobs.map(async r => {
        try { const rec = await run_repeat(D, r); fs.writeFileSync(path.join(first, `heater repeat ${r}.json`), JSON.stringify(rec, null, 1) + '\n'); console.log(`repeat ${r} done`); return rec; }
        catch (e) { console.log(`repeat ${r} failed: ${e.message}`); return { failed: `- repeat ${r}: ${e.message}` }; }
      }));
      write_results(first, records.filter(r => !r.failed), records.filter(r => r.failed).map(r => r.failed));
    })();
  }
}
