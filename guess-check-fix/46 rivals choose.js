/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Log 46. Log 45 found that DeepSeek's own commitments aim where its current rule differs from the
 * obvious one, never where it differs from a rule it has not imagined, so on the grudge the world was
 * almost never asked about a deep grudge. Here rival explanations choose the questions instead.
 *
 * On the grudge, with log 25's 14 observations, two rounds. Each round a fresh DeepSeek gets the
 * observations and every answer from the world so far, and writes four rival explanations, each as a
 * small JavaScript function, each fitting every known fact but differing from the others as much as it
 * can about situations not yet seen. The program runs every rival on every sequence of one to four
 * actions (in a separate process with no files, network or key: log 34's runner), keeps the rivals
 * that fit every known fact, and has the world answer the 3 situations where those rivals are most
 * evenly split. The world still refuses log 25's 12 test cases. After two rounds, a fresh DeepSeek
 * answers all 106 sequences that are not observations from the observations and the world's answers:
 * the same final question as log 45.
 *
 * The control is log 45's random answers arm, run again beside it: 6 answers from the world about
 * random situations, then the same final question.
 *
 * The final rules are written out in a scrambled order, with no arm named, for reading by hand.
 *
 * Run with:
 *   DEEPSEEK_API_KEY=... NODE_USE_ENV_PROXY=1 node "46 rivals choose.js" OUTFOLDER [REPEATS]
 *   node "46 rivals choose.js" --summarise OUTFOLDER    (after "hand reading.json" is written)
 */
const fs = require('fs');
const path = require('path');
const K = require('./25 construction worlds.js');
const X = require('./25 construction test.js');
const A = require('./26 attack surface.js');
const G = require('./45 grudge again.js');
const P = require('./34 language test.js');

const ROUNDS = 2;
const RIVALS = 4;
const ASKED_PER_ROUND = 3;
const ARMS = ['random answers', 'rivals choose'];
const device = K.DEVICES.find(d => d.id === 'grudge');
const ALL = K.sequences(device.world.events, 4);
const key_of = events => events.join('>');
const mix = text => [...text].reduce((h, ch) => Math.imul(h ^ ch.charCodeAt(0), 16777619) >>> 0, 2166136261);

const RIVAL_ASK = (observations, facts) => `${X.evidence_in_words(device, observations)}${facts.length ? `\n\nMore observations, each also from the start:\n${facts.map(f => `- ${f.events.join(', then ')}. At the end: ${f.answer}.`).join('\n')}` : ''}

Write ${RIVALS} rival explanations of Robin's mood. Each must fit every observation above. Make them as different from each other as you can about situations nobody has observed yet: different hidden things, different ways each action works. They are rivals, so at most one of them can be right.

Write each as a JavaScript function named visible that takes the list of actions, in order, as an array of strings ("insult", "apologise", "gift"), starting fresh, and returns {"mood": "warm"} or {"mood": "cold"}. Start each function with a one-line comment saying the explanation in words. Use no outside libraries. Put each rival in its own \`\`\`javascript code block.`;

function read_rivals(text) {
  return [...String(text || '').matchAll(/```(?:javascript|js)?\s*\n([\s\S]*?)```/gi)].map(m => m[1].trim()).filter(b => /function\s+visible|visible\s*=/.test(b)).slice(0, RIVALS);
}
// What a rival says about every sequence: a map from sequence to mood, or a problem.
function predictions_of(code) {
  const ran = P.run_program(code, ALL);
  if (ran.error) return { problem: ran.error };
  const said = {};
  for (let i = 0; i < ALL.length; i++) {
    const r = ran.results[i];
    let value = null;
    try { value = r && !r.error ? JSON.parse(r.value) : null; } catch (e) { value = null; }
    const mood = value && typeof value === 'object' ? value.mood : undefined;
    if (mood !== 'warm' && mood !== 'cold') return { problem: `on ${ALL[i].join(', ')} it gave ${r && r.error ? r.error : JSON.stringify(value)}` };
    said[key_of(ALL[i])] = mood;
  }
  return { said };
}
const truth = events => K.ending(device, events)[0].split(' is ')[1];
const agrees_with_truth_everywhere = said => ALL.every(s => said[key_of(s)] === truth(s));

// The situations where the fitting rivals are most evenly split, excluding what is known or refused.
function most_disputed(rivals, known_keys, refused_keys, how_many, salt) {
  if (rivals.length < 2) return [];
  return ALL.filter(s => !known_keys.has(key_of(s)) && !refused_keys.has(key_of(s)))
    .map(s => { const warm = rivals.filter(r => r.said[key_of(s)] === 'warm').length; return { events: s, split: Math.min(warm, rivals.length - warm), order: mix(`${salt}|${key_of(s)}`) }; })
    .filter(x => x.split > 0)
    .sort((a, b) => b.split - a.split || a.order - b.order)
    .slice(0, how_many).map(x => x.events);
}

async function rivals_choose(D, observations, every_case, test_keys, repeat) {
  const facts = [];
  const rounds = [];
  let tokens = 0, cut = 0;
  for (let round = 1; round <= ROUNDS; round++) {
    const g = D.make_deepseek_guesser();
    const text = await g([{ role: 'user', content: RIVAL_ASK(observations, facts) }], { reply_shape: 'none' });
    tokens += g.counts.tokens_out; cut += g.counts.cut_off;
    const known = observations.map(o => ({ events: o.events, mood: o.expect[0].split(' is ')[1] })).concat(facts.map(f => ({ events: f.events, mood: f.answer.split(' is ')[1] })));
    const rivals = read_rivals(text).map(code => {
      const p = predictions_of(code);
      const fits = !!p.said && known.every(k => p.said[key_of(k.events)] === k.mood);
      return { code, comment: (code.match(/^\s*\/\/\s*(.*)$/m) || [])[1] || null, problem: p.problem || null, fits, said: p.said || null, true_everywhere: !!p.said && agrees_with_truth_everywhere(p.said) };
    });
    const fitting = rivals.filter(r => r.fits);
    const known_keys = new Set(known.map(k => key_of(k.events)));
    const asked = most_disputed(fitting, known_keys, test_keys, ASKED_PER_ROUND, `log 46 ${repeat} ${round}`);
    for (const events of asked) facts.push({ events, answer: K.ending(device, events).join(' and ') });
    rounds.push({ round, rivals: rivals.map(({ said, ...rest }) => rest), fitting: fitting.length, asked: asked.map(key_of), text });
  }
  const final = await A.with_facts(D, device, observations, every_case, facts);
  return Object.assign(final, { rounds, facts, tokens_out: tokens + final.tokens_out, cut_off: cut + final.cut_off, calls: ROUNDS + 1 });
}

async function run_repeat(D, repeat) {
  const { observations, tests, every_case, test_keys } = G.setting();
  const arms = {};
  arms['random answers'] = await A.with_facts(D, device, observations, every_case, A.random_facts(device, observations, test_keys, ROUNDS * ASKED_PER_ROUND, `grudge log 46 ${repeat}`));
  arms['rivals choose'] = await rivals_choose(D, observations, every_case, test_keys, repeat);
  for (const n of ARMS) Object.assign(arms[n], G.scores(arms[n].graded, every_case, tests));
  return { device: device.id, repeat, guesser: D.MODEL_NAME, reply_limit: 200000, arms };
}

// A scrambled order that mixes the arms: each item's place comes from a seeded random draw.
function scrambled(items, seed) {
  let state = mix(seed) || 1;
  const next = () => { state ^= state << 13; state >>>= 0; state ^= state >>> 17; state ^= state << 5; state >>>= 0; return state / 4294967296; };
  const out = items.slice();
  for (let i = out.length - 1; i > 0; i--) { const j = Math.floor(next() * (i + 1)); [out[i], out[j]] = [out[j], out[i]]; }
  return out;
}
function rules_for_reading(records) {
  const all = scrambled(records.flatMap(r => ARMS.map(n => ({ repeat: r.repeat, arm: n, rule: r.arms[n].rule || '(no rule: the reply gave none)' }))), 'log 46 reading')
    .map((x, i) => Object.assign({ id: `R${i + 1}` }, x));
  const text = `# Final grudge rules, to read by hand\n\nScrambled; the arm of each is in "rules key.json". Read each against the categories in "46 Plan - rivals choose.md" and write the reading into "hand reading.json" before opening the key.\n\n${all.map(x => `**${x.id}.** ${x.rule}`).join('\n\n')}\n`;
  return { text, key: all.map(({ id, repeat, arm }) => ({ id, repeat, arm })) };
}

function summarise(records, reading) {
  const lines = ['| Arm | Every case right (of 106, summed) | By repeat | The two telling sequences right | Answers from the world | World asked about a telling sequence (runs) | Output tokens | Replies cut off |', '|---|---|---|---|---|---|---|---|'];
  for (const n of ARMS) {
    const runs = records.map(r => r.arms[n]);
    const sum = f => runs.reduce((s, a) => s + f(a), 0);
    const told = runs.filter(a => (a.facts || []).some(f => G.TELLING.includes(key_of(f.events)))).length;
    lines.push(`| ${n} | ${sum(a => a.every_case_right)} | ${runs.map(a => a.every_case_right).join(', ')} | ${sum(a => a.telling_right)} of ${2 * runs.length} | ${sum(a => a.world_answers)} | ${n === 'random answers' ? '-' : told} | ${sum(a => a.tokens_out)} | ${sum(a => a.cut_off)} |`);
  }
  const rv = records.flatMap(r => r.arms['rivals choose'].rounds);
  const all_rivals = rv.flatMap(x => x.rivals);
  lines.push('', `Rivals written: ${all_rivals.length}; readable and run on every sequence: ${all_rivals.filter(r => !r.problem).length}; fitting every known fact: ${all_rivals.filter(r => r.fits).length}; agreeing with the true grudge on all 120 sequences: ${all_rivals.filter(r => r.true_everywhere).length}. Rounds with fewer than two fitting rivals (no questions asked): ${rv.filter(x => x.fitting < 2).length} of ${rv.length}.`);
  let hand = '';
  if (reading) {
    const key = JSON.parse(reading.key_text);
    const cats = ['true grudge', 'unresolved-insult count', 'running score', 'other', 'no rule'];
    hand = `\n\nFinal rules read by hand (blind to arm), by category:\n\n| Arm | ${cats.join(' | ')} |\n|---|${cats.map(() => '---').join('|')}|\n` +
      ARMS.map(n => `| ${n} | ${cats.map(c => key.filter(k => k.arm === n && reading.read[k.id] === c).length).join(' | ')} |`).join('\n');
  }
  return lines.join('\n') + hand;
}

module.exports = { read_rivals, predictions_of, most_disputed, rivals_choose, run_repeat, scrambled, rules_for_reading, summarise, ARMS, RIVAL_ASK };

if (require.main === module) {
  const [first, second] = process.argv.slice(2);
  const read_records = folder => fs.readdirSync(folder).filter(f => /^grudge repeat \d+\.json$/.test(f)).sort().map(f => JSON.parse(fs.readFileSync(path.join(folder, f), 'utf8')));
  if (first === '--summarise') {
    const records = read_records(second);
    const reading = { read: JSON.parse(fs.readFileSync(path.join(second, 'hand reading.json'), 'utf8')), key_text: fs.readFileSync(path.join(second, 'rules key.json'), 'utf8') };
    const text = `# Rivals choose: results\n\nDeepSeek V4.1 Flash, default thinking, reply limit 200000. ${records.length} repeats; every number comes from the records in this folder.\n\n${summarise(records, reading)}\n`;
    fs.writeFileSync(path.join(second, 'results.md'), text);
    console.log(text);
  } else {
    const D = G.with_higher_limit(require('./17 DeepSeek guesser.js'));
    const REPEATS = Number(second) || 1;
    fs.mkdirSync(first, { recursive: true });
    (async () => {
      const jobs = [];
      for (let r = 1; r <= REPEATS; r++) jobs.push(r);
      const records = await Promise.all(jobs.map(async r => {
        try { const rec = await run_repeat(D, r); fs.writeFileSync(path.join(first, `grudge repeat ${r}.json`), JSON.stringify(rec, null, 1) + '\n'); console.log(`repeat ${r} done`); return rec; }
        catch (e) { console.log(`repeat ${r} failed: ${e.message}`); return null; }
      }));
      const done = records.filter(Boolean);
      const { text, key } = rules_for_reading(done);
      fs.writeFileSync(path.join(first, 'rules to read.md'), text);
      fs.writeFileSync(path.join(first, 'rules key.json'), JSON.stringify(key, null, 1) + '\n');
      console.log(`${done.length} of ${REPEATS} repeats recorded; final rules written for reading by hand.`);
    })();
  }
}
