/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Log 45. Log 44 (the attack surface) left one question open: on the grudge, the one device where
 * DeepSeek's first explanation is wrong, does a fresh DeepSeek given only facts ("rebuild fresh") end with
 * a better explanation than one told its own mistakes in the same conversation ("defend")?
 *
 * This reruns three of log 44's arms on the grudge only, six repeats each, with two changes, both
 * written into "45 Plan - grudge again.md" before any run:
 *   - the reply limit is 200,000 tokens, so no reply should be cut off
 *   - the final question asks about every sequence of one to four actions that is not an observation
 *     (106 of them), not only log 25's 12 test cases, because the 12 cannot tell apart the true grudge
 *     from DeepSeek's "count of unresolved insults", which is wrong on only 2 of 120 sequences
 * The world still refuses to answer log 25's 12 test cases, as in log 44.
 * Everything else is log 26's code: commitments, the world's answers, the three riskiest tested.
 *
 * After the run, the final rules are written out shuffled, with no arm named, for reading by hand
 * ("rules to read.md"); the arm of each is kept in "rules key.json".
 *
 * Run with:
 *   DEEPSEEK_API_KEY=... NODE_USE_ENV_PROXY=1 node "45 grudge again.js" OUTFOLDER [REPEATS]
 *   node "45 grudge again.js" --summarise OUTFOLDER    (after "hand reading.json" is written)
 */
const fs = require('fs');
const path = require('path');
const K = require('./25 construction worlds.js');
const A = require('./26 attack surface.js');

const REPLY_LIMIT = 200000;
const ARMS = ['random answers', 'attack, rebuild fresh', 'attack, defend'];
const device = K.DEVICES.find(d => d.id === 'grudge');
// The two sequences where "count of unresolved insults, apology cancels one, gift does nothing" differs from the true grudge.
const TELLING = ['insult>insult>apologise>apologise', 'insult>insult>gift>apologise'];

function setting() {
  const { observations, tests } = K.observations_and_tests(device);
  const seen = new Set(observations.map(o => o.events.join('>')));
  const every_case = K.sequences(device.world.events, 4).filter(s => !seen.has(s.join('>')))
    .map((events, i) => ({ name: `case ${i + 1}`, events, expect: K.ending(device, events), obvious_right: K.obvious_is_right(device, events) }));
  return { observations, tests, every_case, test_keys: new Set(tests.map(t => t.events.join('>'))) };
}

function with_higher_limit(D) {
  return { MODEL_NAME: D.MODEL_NAME, make_deepseek_guesser: () => D.make_deepseek_guesser(undefined, { reply_limit: REPLY_LIMIT }) };
}

// How a run's answers do on all 106 cases, on log 25's 12 test cases, and on the two telling sequences.
function scores(graded, every_case, tests) {
  const test_names = new Set(tests.map(t => t.events.join('>')));
  const at = key => graded[every_case.findIndex(c => c.events.join('>') === key)];
  return {
    every_case_right: graded.filter(g => g.right).length,
    test_cases_right: graded.filter((g, i) => g.right && test_names.has(every_case[i].events.join('>'))).length,
    telling_right: TELLING.filter(k => at(k) && at(k).right).length,
  };
}

async function run_repeat(D, repeat) {
  const { observations, tests, every_case, test_keys } = setting();
  const arms = {};
  arms['random answers'] = await A.with_facts(D, device, observations, every_case, A.random_facts(device, observations, test_keys, 6, `grudge log 45 ${repeat}`));
  arms['attack, rebuild fresh'] = await A.attack(D, device, observations, every_case, test_keys, 'fresh');
  arms['attack, defend'] = await A.attack(D, device, observations, every_case, test_keys, 'defend');
  for (const n of ARMS) Object.assign(arms[n], scores(arms[n].graded, every_case, tests));
  return { device: device.id, repeat, guesser: D.MODEL_NAME, reply_limit: REPLY_LIMIT, arms };
}

const final_rule = a => (a.final_rule !== undefined ? a.final_rule : a.rule);
const shuffle_key = s => [...s].reduce((h, ch) => Math.imul(h ^ ch.charCodeAt(0), 16777619) >>> 0, 2166136261);

// Final rules, shuffled, with no arm named; and the key.
function rules_for_reading(records) {
  const all = records.flatMap(r => ARMS.map(n => ({ repeat: r.repeat, arm: n, rule: final_rule(r.arms[n]) || '(no rule: the reply gave none)' })))
    .sort((a, b) => shuffle_key(`log 45|${a.arm}|${a.repeat}`) - shuffle_key(`log 45|${b.arm}|${b.repeat}`))
    .map((x, i) => Object.assign({ id: `R${i + 1}` }, x));
  const text = `# Final grudge rules, to read by hand\n\nShuffled; the arm of each is in "rules key.json". Read each against the categories in "45 Plan - grudge again.md" and write the reading into "hand reading.json" before opening the key.\n\n${all.map(x => `**${x.id}.** ${x.rule}`).join('\n\n')}\n`;
  return { text, key: all.map(({ id, repeat, arm }) => ({ id, repeat, arm })) };
}

function summarise(records, reading) {
  const lines = ['| Arm | Every case right (of 106, summed) | By repeat | Test cases right (of 12, summed) | The two telling sequences right | Answers from the world | Output tokens | Replies cut off |', '|---|---|---|---|---|---|---|---|'];
  for (const n of ARMS) {
    const runs = records.map(r => r.arms[n]);
    const sum = f => runs.reduce((s, a) => s + f(a), 0);
    lines.push(`| ${n} | ${sum(a => a.every_case_right)} | ${runs.map(a => a.every_case_right).join(', ')} | ${sum(a => a.test_cases_right)} | ${sum(a => a.telling_right)} of ${2 * runs.length} | ${sum(a => a.world_answers)} | ${sum(a => a.tokens_out)} | ${sum(a => a.cut_off)} |`);
  }
  let hand = '';
  if (reading) {
    const key = JSON.parse(reading.key_text);
    const cats = ['true grudge', 'unresolved-insult count', 'running score', 'other', 'no rule'];
    hand = `\n\nFinal rules read by hand (blind to arm), by category:\n\n| Arm | ${cats.join(' | ')} |\n|---|${cats.map(() => '---').join('|')}|\n` +
      ARMS.map(n => `| ${n} | ${cats.map(c => key.filter(k => k.arm === n && reading.read[k.id] === c).length).join(' | ')} |`).join('\n');
  }
  return lines.join('\n') + hand;
}

module.exports = { setting, scores, run_repeat, rules_for_reading, summarise, with_higher_limit, TELLING, ARMS };

if (require.main === module) {
  const [first, second] = process.argv.slice(2);
  const read_records = folder => fs.readdirSync(folder).filter(f => /^grudge repeat \d+\.json$/.test(f)).sort().map(f => JSON.parse(fs.readFileSync(path.join(folder, f), 'utf8')));
  if (first === '--summarise') {
    const records = read_records(second);
    const reading = { read: JSON.parse(fs.readFileSync(path.join(second, 'hand reading.json'), 'utf8')), key_text: fs.readFileSync(path.join(second, 'rules key.json'), 'utf8') };
    const text = `# Grudge again: results\n\nDeepSeek V4.1 Flash, default thinking, reply limit ${REPLY_LIMIT}. ${records.length} repeats; every number comes from the records in this folder.\n\n${summarise(records, reading)}\n`;
    fs.writeFileSync(path.join(second, 'results.md'), text);
    console.log(text);
  } else {
    const D = with_higher_limit(require('./17 DeepSeek guesser.js'));
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
