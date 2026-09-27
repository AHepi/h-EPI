/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Tests "45 grudge again.js" without calling DeepSeek. Checks:
 *   - the final question covers every sequence of one to four actions that is not an observation (106),
 *     including log 25's 12 test cases and the two telling sequences
 *   - scoring: the true grudge gets all 106 and both telling sequences; the "count of unresolved insults"
 *     rule gets 104 and neither telling sequence
 *   - every DeepSeek call asks for the 200,000-token reply limit
 *   - a whole repeat runs through the three arms, and the world still refuses log 25's test cases
 *   - the rules written for reading by hand name no arm, and the key maps each back
 *   - the summary counts the hand reading by arm
 * Run with:  node "45 grudge again tests.js"
 */
const K = require('./25 construction worlds.js');
const G = require('./45 grudge again.js');

let failed = 0;
function expect_that(name, ok, detail) {
  if (!ok) failed++;
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${name}${ok || detail === undefined ? '' : `\n     ${detail}`}`);
}
const device = K.DEVICES.find(d => d.id === 'grudge');
const truth = events => K.ending(device, events)[0].split(' is ')[1];
const counter = events => { let c = 0; for (const e of events) { if (e === 'insult') c++; else if (e === 'apologise') c = Math.max(0, c - 1); } return c === 0 ? 'warm' : 'cold'; };

// A stand-in that answers every question by a given rule, and commits to two situations.
function stand_in(rule_fn, rule_words) {
  const settings_seen = [];
  const prompts = [];
  return {
    MODEL_NAME: 'stand-in', settings_seen, prompts,
    make_deepseek_guesser(send, settings) {
      settings_seen.push(settings);
      const g = async messages => {
        const last = messages[messages.length - 1].content;
        prompts.push(last);
        g.counts.tokens_out += 1;
        const cases = [...last.matchAll(/^T(\d+): (.+?)\. At the end/gm)];
        if (cases.length) return JSON.stringify({ rule: rule_words, answers: Object.fromEntries(cases.map(m => [`T${m[1]}`, rule_fn(m[2].split(', then '))])) });
        return JSON.stringify({ rule: rule_words, commitments: [
          { events: ['insult', 'insult', 'gift', 'apologise'], predict: rule_fn(['insult', 'insult', 'gift', 'apologise']), why: 'x' },
          { events: ['gift', 'insult'], predict: rule_fn(['gift', 'insult']), why: 'x' },
        ] });
      };
      g.counts = { tokens_out: 0, cut_off: 0 };
      return g;
    },
  };
}

(async () => {
  const { observations, tests, every_case } = G.setting();
  const keys = new Set(every_case.map(c => c.events.join('>')));
  expect_that('the final question covers 106 sequences, none an observation', every_case.length === 106 && observations.every(o => !keys.has(o.events.join('>'))), every_case.length);
  expect_that('it includes log 25\'s 12 test cases and both telling sequences', tests.every(t => keys.has(t.events.join('>'))) && G.TELLING.every(k => keys.has(k)));

  const graded_by = f => every_case.map(c => ({ right: f(c.events) === truth(c.events) }));
  const t = G.scores(graded_by(truth), every_case, tests);
  expect_that('the true grudge gets 106, 12 test cases and both telling sequences', t.every_case_right === 106 && t.test_cases_right === 12 && t.telling_right === 2, JSON.stringify(t));
  const c = G.scores(graded_by(counter), every_case, tests);
  expect_that('the unresolved-insult count gets 104, all 12 test cases, and neither telling sequence', c.every_case_right === 104 && c.test_cases_right === 12 && c.telling_right === 0, JSON.stringify(c));

  const s = stand_in(counter, 'RULE-COUNTER');
  const D = G.with_higher_limit(s);
  const record = await G.run_repeat(D, 1);
  expect_that('every call asks for the 200,000-token reply limit', s.settings_seen.length > 0 && s.settings_seen.every(x => x && x.reply_limit === 200000), JSON.stringify(s.settings_seen));
  expect_that('a whole repeat runs through the three arms', G.ARMS.every(n => record.arms[n] && record.arms[n].graded.length === 106));
  expect_that('each arm scores as its rule does', G.ARMS.every(n => record.arms[n].every_case_right === 104 && record.arms[n].telling_right === 0), G.ARMS.map(n => record.arms[n].every_case_right).join(','));
  const fresh = record.arms['attack, rebuild fresh'];
  expect_that('the world answers a committed situation that is not a test case', fresh.rounds[0].commitments[0].tested === true);

  const tests_keys = new Set(tests.map(x => x.events.join('>')));
  const facts = record.arms['attack, rebuild fresh'].facts.concat(record.arms['attack, defend'].facts);
  expect_that('the world never answers one of log 25\'s test cases', facts.every(f => !tests_keys.has(f.events.join('>'))));

  const record2 = await G.run_repeat(G.with_higher_limit(stand_in(truth, 'RULE-TRUE')), 2);
  const { text, key } = G.rules_for_reading([record, record2]);
  expect_that('the rules for reading name no arm', !/random|rebuild|defend|attack/i.test(text));
  expect_that('the key maps each of the 6 rules back to its arm and repeat', key.length === 6 && new Set(key.map(k => k.id)).size === 6 && key.every(k => G.ARMS.includes(k.arm)));
  const read = Object.fromEntries(key.map(k => [k.id, k.repeat === 1 ? 'unresolved-insult count' : 'true grudge']));
  const summary = G.summarise([record, record2], { read, key_text: JSON.stringify(key) });
  expect_that('the summary counts the hand reading by arm', /\| attack, defend \| 1 \| 1 \| 0 \| 0 \| 0 \|/.test(summary), summary.split('\n').slice(-3).join(' / '));

  console.log(`\n${failed} test(s) failed.`);
  process.exit(failed ? 1 : 0);
})();
