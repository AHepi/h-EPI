/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Tests "46 rivals choose.js" without calling DeepSeek. Checks:
 *   - rival functions are read from their code blocks and run on every sequence in the separate process
 *   - a rival that breaks, or gives something other than warm or cold, is marked with its problem
 *   - the true grudge is recognised as agreeing with the world on all 120 sequences
 *   - the disputed situations are where fitting rivals split, never an observation, a known fact or a test case
 *   - a whole repeat runs through both arms, asks the world at most 6 times, and asks for the 200,000 limit
 *   - the scrambled list for reading names no arm and mixes the arms
 * Run with:  node "46 rivals choose tests.js"
 */
const K = require('./25 construction worlds.js');
const G = require('./45 grudge again.js');
const R = require('./46 rivals choose.js');

let failed = 0;
function expect_that(name, ok, detail) {
  if (!ok) failed++;
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${name}${ok || detail === undefined ? '' : `\n     ${detail}`}`);
}
const device = K.DEVICES.find(d => d.id === 'grudge');
const SCORE = "// running score\nfunction visible(a) { let s = 0; for (const x of a) s += x === 'insult' ? -1 : 1; return { mood: s > 0 ? 'warm' : 'cold' }; }";
const COUNT = "// unresolved insults\nfunction visible(a) { let c = 0; for (const x of a) { if (x === 'insult') c++; else if (x === 'apologise') c = Math.max(0, c - 1); } return { mood: c === 0 ? 'warm' : 'cold' }; }";
const TRUE = "// three levels\nfunction visible(a) { let g = 0; for (const x of a) { if (x === 'insult') g = Math.min(2, g + 1); else if (x === 'apologise' && g === 1) g = 0; else if (x === 'gift' && g === 2) g = 1; } return { mood: g === 0 ? 'warm' : 'cold' }; }";
const BROKEN = "// broken\nfunction visible(a) { return { mood: 'grumpy' }; }";
const block = c => '```javascript\n' + c + '\n```';

function stand_in(codes, final_rule) {
  const settings_seen = [];
  return {
    MODEL_NAME: 'stand-in', settings_seen,
    make_deepseek_guesser(send, settings) {
      settings_seen.push(settings);
      const g = async messages => {
        const last = messages[messages.length - 1].content;
        g.counts.tokens_out += 1;
        const cases = [...last.matchAll(/^T(\d+): (.+?)\. At the end/gm)];
        if (cases.length) return JSON.stringify({ rule: final_rule, answers: Object.fromEntries(cases.map(m => [`T${m[1]}`, 'cold'])) });
        return codes.map(block).join('\n\nNext rival:\n\n');
      };
      g.counts = { tokens_out: 0, cut_off: 0 };
      return g;
    },
  };
}

(async () => {
  const read = R.read_rivals([SCORE, COUNT, TRUE, BROKEN].map(block).join('\ntext\n'));
  expect_that('four rivals are read from their code blocks', read.length === 4);
  const p_true = R.predictions_of(TRUE), p_count = R.predictions_of(COUNT), p_broken = R.predictions_of(BROKEN);
  const truth = e => K.ending(device, e)[0].split(' is ')[1];
  const all = K.sequences(device.world.events, 4);
  expect_that('the three-level rival agrees with the world on all 120 sequences', p_true.said && all.every(s => p_true.said[s.join('>')] === truth(s)));
  expect_that('the unresolved-insult rival differs from the world on exactly 2', p_count.said && all.filter(s => p_count.said[s.join('>')] !== truth(s)).length === 2);
  expect_that('a rival giving something other than warm or cold is marked with its problem', !!p_broken.problem && !p_broken.said, JSON.stringify(p_broken));

  const { observations, test_keys } = G.setting();
  const known = new Set(observations.map(o => o.events.join('>')));
  const disputed = R.most_disputed([{ said: p_true.said }, { said: p_count.said }], known, test_keys, 3, 'x');
  expect_that('between the true grudge and the count, the disputed situations are the telling ones', disputed.length === 2 && disputed.every(d => G.TELLING.includes(d.join('>'))), JSON.stringify(disputed));
  const p_score = R.predictions_of(SCORE);
  const d2 = R.most_disputed([{ said: p_score.said }, { said: p_count.said }, { said: p_true.said }], known, test_keys, 3, 'x');
  expect_that('disputed situations are never an observation or a test case', d2.length === 3 && d2.every(d => !known.has(d.join('>')) && !test_keys.has(d.join('>'))));
  expect_that('one fitting rival asks nothing', R.most_disputed([{ said: p_true.said }], known, test_keys, 3, 'x').length === 0);

  const s = stand_in([SCORE, COUNT, TRUE, BROKEN], 'RULE-A');
  const rec = await R.run_repeat(G.with_higher_limit(s), 1);
  const rc = rec.arms['rivals choose'];
  expect_that('a whole repeat runs through both arms, each graded on 106', R.ARMS.every(n => rec.arms[n].graded.length === 106));
  expect_that('every call asks for the 200,000-token reply limit', s.settings_seen.every(x => x && x.reply_limit === 200000));
  expect_that('the world is asked at most 6 times, never about a test case', rc.facts.length <= 6 && rc.facts.every(f => !test_keys.has(f.events.join('>'))), rc.facts.length);
  expect_that('round 1 marks the broken rival and keeps the true one as fitting', rc.rounds[0].rivals[3].problem && rc.rounds[0].rivals[2].fits && rc.rounds[0].rivals[2].true_everywhere);
  expect_that('round 2 is told the answers and, with the running score now refuted, asks about the telling sequences', rc.rounds[1].asked.every(k => G.TELLING.includes(k)), JSON.stringify(rc.rounds.map(r => r.asked)));

  const recs = [];
  for (let r = 1; r <= 6; r++) recs.push(await R.run_repeat(G.with_higher_limit(stand_in([SCORE, COUNT], `RULE-${r}`)), r));
  const { text, key } = R.rules_for_reading(recs);
  expect_that('the rules for reading name no arm (the heading names the plan file, so only the rule lines are checked)', !/random|rivals/i.test(text.split('\n').filter(l => l.startsWith('**R')).join('\n')));
  const neighbours_same = key.slice(1).filter((k, i) => k.arm === key[i].arm).length;
  expect_that('the scrambled list mixes the arms (fewer than 9 of 11 neighbours share an arm)', neighbours_same < 9 && key.length === 12, `${neighbours_same}: ${key.map(k => k.arm[0]).join('')}`);

  console.log(`\n${failed} test(s) failed.`);
  process.exit(failed ? 1 : 0);
})();
