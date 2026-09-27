/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Log 47. In log 46, rival explanations chose the world's questions well, but a rival that fitted
 * every fact was thrown away, because the final step saw only the facts. Here the survivors are kept.
 *
 * On the grudge, with log 25's 14 observations, three rounds. Each round a fresh DeepSeek sees the
 * observations, the world's answers so far and the code of every rival still standing, and writes four
 * new rivals, fitting every fact and differing from the survivors and from each other where nobody has
 * looked. The program runs every rival (in log 34's separate process with no files, network or key),
 * drops any that a known fact refutes, and has the world answer the 3 situations of up to four actions
 * where the standing rivals are most evenly split. The world still refuses log 25's 12 test cases.
 *
 * Three final answers from the same run, so the only difference between them is what the last step sees:
 *   survivors vote        - no DeepSeek: each case is answered by the majority of the rivals still
 *                           standing; a tie is no answer
 *   shown the survivors   - a fresh DeepSeek sees the observations, the facts and the survivors' code,
 *                           and writes one final function
 *   shown the facts only  - a fresh DeepSeek sees the observations and the facts, and writes one
 *                           final function
 * All three are graded by running them on every sequence of one to six actions that is not an
 * observation: 106 of up to four actions (as in logs 45 and 46) and 972 of five or six, where a rule
 * that is right only on short sequences shows itself.
 *
 * Run with:
 *   DEEPSEEK_API_KEY=... NODE_USE_ENV_PROXY=1 node "47 keep the survivors.js" OUTFOLDER [REPEATS]
 *   node "47 keep the survivors.js" --summarise OUTFOLDER
 */
const fs = require('fs');
const path = require('path');
const K = require('./25 construction worlds.js');
const X = require('./25 construction test.js');
const G = require('./45 grudge again.js');
const P = require('./34 language test.js');

const ROUNDS = 3;
const NEW_RIVALS = 4;
const ASKED_PER_ROUND = 3;
const FINALS = ['survivors vote', 'shown the survivors', 'shown the facts only'];
const device = K.DEVICES.find(d => d.id === 'grudge');
const key_of = events => events.join('>');
const mix = text => [...text].reduce((h, ch) => Math.imul(h ^ ch.charCodeAt(0), 16777619) >>> 0, 2166136261);
const SHORT = K.sequences(device.world.events, 4);                 // what the world may be asked about
const EVERY = K.sequences(device.world.events, 6);                 // what is graded
const truth = events => K.ending(device, events)[0].split(' is ')[1];

const FUNCTION_SHAPE = 'a JavaScript function named visible that takes the list of actions, in order, as an array of strings ("insult", "apologise", "gift"), starting fresh, and returns {"mood": "warm"} or {"mood": "cold"}. Start it with a one-line comment saying the explanation in words. Use no outside libraries.';
const facts_in_words = facts => (facts.length ? `\n\nMore observations, each also from the start:\n${facts.map(f => `- ${f.events.join(', then ')}. At the end: mood is ${f.mood}.`).join('\n')}` : '');
const rivals_in_words = rivals => rivals.map((r, i) => `Rival ${i + 1}:\n\`\`\`javascript\n${r.code}\n\`\`\``).join('\n\n');

const RIVAL_ASK = (observations, facts, standing) => `${X.evidence_in_words(device, observations)}${facts_in_words(facts)}

${standing.length ? `These rival explanations still fit every observation above:\n\n${rivals_in_words(standing)}\n\nWrite ${NEW_RIVALS} new rival explanations. Each must fit every observation above. Make them differ from the rivals above and from each other as much as you can about situations nobody has observed yet.` : `Write ${NEW_RIVALS} rival explanations of Robin's mood. Each must fit every observation above. Make them as different from each other as you can about situations nobody has observed yet: different hidden things, different ways each action works.`} They are rivals, so at most one of them can be right.

Write each as ${FUNCTION_SHAPE} Put each rival in its own \`\`\`javascript code block.`;

const FINAL_ASK = (observations, facts, survivors) => `${X.evidence_in_words(device, observations)}${facts_in_words(facts)}

${survivors ? `These rival explanations fit every observation above:\n\n${rivals_in_words(survivors)}\n\nYou may keep one of them, combine them, or write a new one. ` : ''}Write the one explanation of Robin's mood you think is right, as ${FUNCTION_SHAPE} Put it in one \`\`\`javascript code block.`;

function read_functions(text, how_many) {
  return [...String(text || '').matchAll(/```(?:javascript|js)?\s*\n([\s\S]*?)```/gi)].map(m => m[1].trim()).filter(b => /function\s+visible|visible\s*=/.test(b)).slice(0, how_many);
}
// What a function says on every graded sequence: a map from sequence to mood, or a problem.
function predictions_of(code) {
  const ran = P.run_program(code, EVERY);
  if (ran.error) return { problem: ran.error };
  const said = {};
  for (let i = 0; i < EVERY.length; i++) {
    const r = ran.results[i];
    let value = null;
    try { value = r && !r.error ? JSON.parse(r.value) : null; } catch (e) { value = null; }
    const mood = value && typeof value === 'object' ? value.mood : undefined;
    if (mood !== 'warm' && mood !== 'cold') return { problem: `on ${EVERY[i].join(', ')} it gave ${r && r.error ? r.error : JSON.stringify(value)}` };
    said[key_of(EVERY[i])] = mood;
  }
  return { said };
}
const comment_of = code => (code.match(/^\s*\/\/\s*(.*)$/m) || [])[1] || null;
const fits_all = (said, known) => !!said && known.every(k => said[key_of(k.events)] === k.mood);

function most_disputed(standing, known_keys, refused_keys, how_many, salt) {
  if (standing.length < 2) return [];
  return SHORT.filter(s => !known_keys.has(key_of(s)) && !refused_keys.has(key_of(s)))
    .map(s => { const warm = standing.filter(r => r.said[key_of(s)] === 'warm').length; return { events: s, split: Math.min(warm, standing.length - warm), order: mix(`${salt}|${key_of(s)}`) }; })
    .filter(x => x.split > 0)
    .sort((a, b) => b.split - a.split || a.order - b.order)
    .slice(0, how_many).map(x => x.events);
}

// Grading: how a map of answers does on the sequences that are not observations, short and long.
function grade(said, observation_keys) {
  const cases = EVERY.filter(s => !observation_keys.has(key_of(s)));
  const right = s => !!said && said[key_of(s)] === truth(s);
  const short = cases.filter(s => s.length <= 4), long = cases.filter(s => s.length > 4);
  return {
    short_right: short.filter(right).length, short_all: short.length,
    long_right: long.filter(right).length, long_all: long.length,
    telling_right: G.TELLING.filter(k => !!said && said[k] === truth(k.split('>'))).length,
  };
}
function vote(survivors) {
  const said = {};
  let ties = 0;
  for (const s of EVERY) {
    const warm = survivors.filter(r => r.said[key_of(s)] === 'warm').length;
    const cold = survivors.length - warm;
    if (warm === cold) { ties++; continue; }
    said[key_of(s)] = warm > cold ? 'warm' : 'cold';
  }
  return { said, ties };
}
const true_everywhere = said => !!said && EVERY.every(s => said[key_of(s)] === truth(s));

async function final_function(D, observations, facts, survivors) {
  const g = D.make_deepseek_guesser();
  const text = await g([{ role: 'user', content: FINAL_ASK(observations, facts, survivors) }], { reply_shape: 'none' });
  const code = read_functions(text, 1)[0] || null;
  const p = code ? predictions_of(code) : { problem: 'no function in the reply' };
  return { code, comment: code ? comment_of(code) : null, problem: p.problem || null, said: p.said || null, tokens_out: g.counts.tokens_out, cut_off: g.counts.cut_off, text };
}

async function run_repeat(D, repeat) {
  const { observations, test_keys } = G.setting();
  const observation_keys = new Set(observations.map(o => key_of(o.events)));
  const known = observations.map(o => ({ events: o.events, mood: o.expect[0].split(' is ')[1] }));
  const facts = [];
  let standing = [];
  const rounds = [];
  let tokens = 0, cut = 0;
  for (let round = 1; round <= ROUNDS; round++) {
    const g = D.make_deepseek_guesser();
    const text = await g([{ role: 'user', content: RIVAL_ASK(observations, facts, standing) }], { reply_shape: 'none' });
    tokens += g.counts.tokens_out; cut += g.counts.cut_off;
    const fresh = read_functions(text, NEW_RIVALS).map((code, i) => { const p = predictions_of(code); return { name: `round ${round} rival ${i + 1}`, code, comment: comment_of(code), problem: p.problem || null, said: p.said || null }; });
    const all_known = known.concat(facts);
    const added = fresh.filter(r => fits_all(r.said, all_known));
    standing = standing.concat(added);
    const asked = most_disputed(standing, new Set(all_known.map(k => key_of(k.events))), test_keys, ASKED_PER_ROUND, `log 47 ${repeat} ${round}`);
    for (const events of asked) facts.push({ events, mood: truth(events) });
    const before = standing.length;
    standing = standing.filter(r => fits_all(r.said, known.concat(facts)));
    rounds.push({
      round, written: fresh.map(({ said, ...r }) => Object.assign(r, { true_everywhere: true_everywhere(said) })),
      added: added.length, asked: asked.map(key_of), refuted_by_answers: before - standing.length, standing_after: standing.map(r => r.name), text,
    });
  }
  const survivors = standing;
  const finals = {};
  const voted = vote(survivors);
  finals['survivors vote'] = Object.assign(grade(voted.said, observation_keys), { ties: voted.ties, survivors: survivors.length });
  const shown = await final_function(D, observations, facts, survivors);
  const facts_only = await final_function(D, observations, facts, null);
  for (const [n, f] of [['shown the survivors', shown], ['shown the facts only', facts_only]]) {
    tokens += f.tokens_out; cut += f.cut_off;
    const { said, text, ...rest } = f;
    finals[n] = Object.assign(grade(said, observation_keys), rest, { true_everywhere: true_everywhere(said), same_as_a_survivor: survivors.filter(r => !!said && EVERY.every(s => r.said[key_of(s)] === said[key_of(s)])).map(r => r.name), text });
  }
  return {
    device: device.id, repeat, guesser: D.MODEL_NAME, reply_limit: 200000, rounds, facts,
    survivors: survivors.map(r => ({ name: r.name, comment: r.comment, true_everywhere: true_everywhere(r.said), ...grade(r.said, observation_keys) })),
    finals, tokens_out: tokens, cut_off: cut,
  };
}

function summarise(records) {
  const lines = ['| Final answer | Right, up to four actions (of 106 per run, summed) | Right, five or six actions (of 972 per run, summed) | By repeat (short / long) | Telling sequences right (of 12) | Runs where it is the true grudge everywhere |', '|---|---|---|---|---|---|'];
  for (const n of FINALS) {
    const f = records.map(r => r.finals[n]);
    const sum = k => f.reduce((s, x) => s + x[k], 0);
    const everywhere = n === 'survivors vote' ? records.filter(r => r.finals[n].short_right === 106 && r.finals[n].long_right === 972).length : f.filter(x => x.true_everywhere).length;
    lines.push(`| ${n} | ${sum('short_right')} | ${sum('long_right')} | ${f.map(x => `${x.short_right}/${x.long_right}`).join(', ')} | ${sum('telling_right')} | ${everywhere} |`);
  }
  const written = records.flatMap(r => r.rounds.flatMap(x => x.written));
  lines.push('',
    `Rivals written: ${written.length}; ran on every sequence: ${written.filter(r => !r.problem).length}; fitted every fact known when written: ${records.reduce((s, r) => s + r.rounds.reduce((t, x) => t + x.added, 0), 0)}; agreeing with the true grudge on every sequence up to six actions: ${written.filter(r => r.true_everywhere).length}.`,
    `Survivors at the end, by repeat: ${records.map(r => r.survivors.length).join(', ')}; runs with a survivor that is the true grudge everywhere: ${records.filter(r => r.survivors.some(s => s.true_everywhere)).length}.`,
    `Runs where the world was asked a telling sequence: ${records.filter(r => r.facts.some(f => G.TELLING.includes(key_of(f.events)))).length} of ${records.length}.`,
    `Survivor votes left undecided (ties), by repeat: ${records.map(r => r.finals['survivors vote'].ties).join(', ')}.`,
    `Replies cut off: ${records.reduce((s, r) => s + r.cut_off, 0)}. Output tokens: ${records.reduce((s, r) => s + r.tokens_out, 0)}.`,
    '', 'Final functions, by repeat:', '',
    ...records.flatMap(r => ['shown the survivors', 'shown the facts only'].map(n => `- repeat ${r.repeat}, ${n}: ${r.finals[n].comment || r.finals[n].problem || '(no comment)'}${r.finals[n].same_as_a_survivor.length ? ` (acts exactly as ${r.finals[n].same_as_a_survivor.join(', ')})` : ''}`)));
  return lines.join('\n');
}

module.exports = { read_functions, predictions_of, most_disputed, grade, vote, run_repeat, summarise, true_everywhere, FINALS, EVERY, SHORT };

if (require.main === module) {
  const [first, second] = process.argv.slice(2);
  const read_records = folder => fs.readdirSync(folder).filter(f => /^grudge repeat \d+\.json$/.test(f)).sort().map(f => JSON.parse(fs.readFileSync(path.join(folder, f), 'utf8')));
  const write_results = (folder, records, failed) => {
    const text = `# Keep the survivors: results\n\nDeepSeek V4.1 Flash, default thinking, reply limit 200000. ${records.length} repeats; every number comes from the records in this folder.\n\n${summarise(records)}\n${failed.length ? `\nRuns that failed:\n${failed.join('\n')}\n` : ''}`;
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
        try { const rec = await run_repeat(D, r); fs.writeFileSync(path.join(first, `grudge repeat ${r}.json`), JSON.stringify(rec, null, 1) + '\n'); console.log(`repeat ${r} done`); return rec; }
        catch (e) { console.log(`repeat ${r} failed: ${e.message}`); return { failed: `- repeat ${r}: ${e.message}` }; }
      }));
      write_results(first, records.filter(r => !r.failed), records.filter(r => r.failed).map(r => r.failed));
    })();
  }
}
