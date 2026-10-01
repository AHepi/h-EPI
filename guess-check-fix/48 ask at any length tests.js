/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Tests "48 ask at any length.js" and the setting it adds to log 47's code, without calling DeepSeek.
 * Checks:
 *   - with no setting, the world is asked only about situations of up to four actions (log 47 unchanged)
 *   - with the log 48 setting, the world may be asked about five or six actions, where two rivals that
 *     agree on everything up to four actions disagree
 *   - the world never answers an observation or a test case, and at most 9 questions are asked
 *   - the summary reports the length of the world's questions
 * Run with:  node "48 ask at any length tests.js"
 */
const G = require('./45 grudge again.js');
const S = require('./47 keep the survivors.js');
const L = require('./48 ask at any length.js');

let failed = 0;
function expect_that(name, ok, detail) {
  if (!ok) failed++;
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${name}${ok || detail === undefined ? '' : `\n     ${detail}`}`);
}
// Two rivals that agree on every sequence of up to four actions and differ on longer ones:
// the true grudge, and log 46's matching rival.
const TRUE = "// three levels\nfunction visible(a) { let g = 0; for (const x of a) { if (x === 'insult') g = Math.min(2, g + 1); else if (x === 'apologise' && g === 1) g = 0; else if (x === 'gift' && g === 2) g = 1; } return { mood: g === 0 ? 'warm' : 'cold' }; }";
const NEAR = "// anger and last action\nfunction visible(actions) { let anger = 0, last = null; for (const a of actions) { if (a === 'insult') { anger += last === 'insult' ? 2 : 1; last = 'insult'; } else if (a === 'apologise') { if (last === 'gift') anger = 0; else if (anger <= 1) anger = 0; else anger -= 1; last = 'apologise'; } else if (a === 'gift') last = 'gift'; } return { mood: anger === 0 ? 'warm' : 'cold' }; }";
const block = c => '```javascript\n' + c + '\n```';
function stand_in() {
  return {
    MODEL_NAME: 'stand-in',
    make_deepseek_guesser(send, settings) {
      const g = async messages => { g.counts.tokens_out += 1; return /Write the one explanation/.test(messages[messages.length - 1].content) ? block(TRUE) : [TRUE, NEAR].map(block).join('\n\n'); };
      g.counts = { tokens_out: 0, cut_off: 0 };
      return g;
    },
  };
}

(async () => {
  const { observations, test_keys } = G.setting();
  const obs = new Set(observations.map(o => o.events.join('>')));
  const D = G.with_higher_limit(stand_in());
  const four = await S.run_repeat(D, 1);
  expect_that('with no setting, nothing is asked: the two rivals agree on everything up to four actions', four.facts.length === 0, JSON.stringify(four.facts));
  const six = await S.run_repeat(D, 1, L.OPTIONS);
  expect_that('with the log 48 setting, the world is asked about five or six actions', six.facts.length > 0 && six.facts.every(f => f.events.length > 4), JSON.stringify(six.facts.map(f => f.events.length)));
  expect_that('the near rival is refuted and the true grudge survives', six.survivors.length > 0 && six.survivors.every(s => s.true_everywhere), six.survivors.map(s => s.comment).join(', '));
  expect_that('at most 9 questions, never an observation or a test case', six.facts.length <= 9 && six.facts.every(f => !obs.has(f.events.join('>')) && !test_keys.has(f.events.join('>'))));
  expect_that('the summary reports question lengths', /Runs with at least one answer about five or six actions: 1 of 1/.test(L.question_lengths([six])), L.question_lengths([six]));
  console.log(`\n${failed} test(s) failed.`);
  process.exit(failed ? 1 : 0);
})();
