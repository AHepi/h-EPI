/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Tests "26 attack surface.js" without calling DeepSeek. A stand-in states a rule it marks with a word
 * ("RULE-ONE") and commits to predictions, some of which the world contradicts. Checks:
 *   - rebuild fresh: the second round is a new conversation that holds the world's answers as facts, and
 *     never the old rule, the old predictions, or any verdict on them
 *   - defend: the second round is the same conversation, told "you predicted X; the world says Y"
 *   - the world never answers a test case or an action the device does not have; only the three riskiest
 *     commitments are tested; at most six answers from the world in all
 *   - a commitment is risky when the obvious explanation predicts otherwise
 *   - random answers: six, none a test case or an observation
 *   - a whole device runs through all four arms
 * Run with:  node "26 attack surface tests.js"
 */
const K = require('./25 construction worlds.js');
const A = require('./26 attack surface.js');

let failed = 0;
function expect_that(name, ok, detail) {
  if (!ok) failed++;
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${name}${ok || !detail ? '' : `\n     ${detail}`}`);
}
const device = K.DEVICES.find(d => d.id === 'grudge');
const { observations, tests } = K.observations_and_tests(device);
const test_keys = new Set(tests.map(t => t.events.join('>')));
const a_test = tests[0].events;
// An unseen situation the world will answer and the obvious explanation gets wrong (neither a test case nor an observation).
const open_risky = K.sequences(device.world.events, 4).find(e => !test_keys.has(e.join('>')) && !observations.some(o => o.events.join('>') === e.join('>')) && !K.obvious_is_right(device, e));
const open_answer = K.ending(device, open_risky)[0].split(' is ')[1];
const wrong_guess = open_answer === 'warm' ? 'cold' : 'warm';

function stand_in() {
  const calls = [];
  return {
    calls, MODEL_NAME: 'stand-in',
    make_deepseek_guesser() {
      const g = async messages => {
        calls.push(messages.map(m => m.content));
        g.counts.tokens_out += 1;
        const last = messages[messages.length - 1].content;
        if (last.includes('Predict these new cases')) return JSON.stringify({ rule: 'final', answers: Object.fromEntries(tests.map((t, i) => [`T${i + 1}`, 'cold'])) });
        return JSON.stringify({ rule: 'RULE-ONE: a running score', commitments: [
          { events: open_risky, predict: wrong_guess, why: 'the score says so' },                         // the world says otherwise
          { events: a_test, predict: 'warm', why: 'a test case' },                                          // refused: a test case
          { events: ['dance'], predict: 'warm', why: 'no such action' },                                     // refused: not allowed
          { events: ['insult'], predict: 'cold', why: 'plain' },                                             // not among the riskiest three
          { events: ['gift'], predict: 'warm', why: 'plain' },
        ] });
      };
      g.counts = { tokens_out: 0, cut_off: 0 };
      return g;
    },
  };
}

(async () => {
  expect_that('the world refuses a test case', !A.world_answers(device, a_test, test_keys).available);
  expect_that('the world refuses an action the device does not have', !A.world_answers(device, ['dance'], test_keys).available);
  expect_that('the world answers an allowed, unseen situation', A.world_answers(device, open_risky, test_keys).answer === `mood is ${open_answer}`);
  expect_that('a commitment the obvious explanation contradicts is risky', A.risky_against_obvious(device, { events: ['insult', 'insult', 'apologise'], predict: 'cold' }) && !A.risky_against_obvious(device, { events: ['insult'], predict: 'cold' }));

  const s = stand_in();
  const fresh = await A.attack(s, device, observations, tests, test_keys, 'fresh');
  const round_two = s.calls[1];
  expect_that('rebuild fresh: round two is a new conversation of one message', round_two.length === 1);
  expect_that('rebuild fresh: round two never sees the old rule, its predictions or a verdict', !/RULE-ONE|you predicted|wrong|refuted|commitment/i.test(round_two[0].replace(/State the rule[\s\S]*$/, '')), round_two[0].slice(-400));
  expect_that('rebuild fresh: round two holds the world\'s answer as a fact', round_two[0].includes(`${open_risky.join(', then ')}. At the end: mood is ${open_answer}.`));
  const r1 = fresh.rounds[0].commitments;
  expect_that('only the three riskiest are put to the world; test cases and unknown actions are refused', r1[0].tested && r1[0].held === false && !r1[1].tested && r1[1].why_not === 'not available' && !r1[2].tested && !r1[3].tested && r1[3].why_not === 'not among the three riskiest');
  expect_that('at most six answers from the world', fresh.facts.length <= 6);

  const s2 = stand_in();
  const defend = await A.attack(s2, device, observations, tests, test_keys, 'defend');
  const d2 = s2.calls[1];
  expect_that('defend: round two is the same conversation, told what it predicted and what the world says', d2.length === 3 && d2[1].includes('RULE-ONE') && d2[2].includes(`you predicted ${wrong_guess}; the world says ${open_answer}`));
  expect_that('defend: the test cases are answered in that same conversation', s2.calls[s2.calls.length - 1].length === 5 && defend.graded.length === 12);

  const facts = A.random_facts(device, observations, test_keys, 6, 'salt');
  expect_that('random answers: six, none a test case or an observation', facts.length === 6 && facts.every(f => !test_keys.has(f.events.join('>')) && !observations.some(o => o.events.join('>') === f.events.join('>'))));

  const rec = await A.run_device(device, 1, stand_in());
  expect_that('a whole device runs through all four arms', ['bare', 'random answers', 'attack, rebuild fresh', 'attack, defend'].every(n => rec.arms[n]));
  expect_that('the summary counts the attack surface', A.summarise([rec]).includes('| attack, rebuild fresh | 10 |'));

  console.log(`\n${failed} test(s) failed.`);
  process.exit(failed ? 1 : 0);
})();
