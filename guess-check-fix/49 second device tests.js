/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Tests "49 heater.js" and "49 second device.js" without calling DeepSeek. Checks:
 *   - the heater behaves as its description says (up, up is cold; up, down is warm; the dial does
 *     nothing while tripped; waiting resets to off)
 *   - a hand-written copy of the true heater matches it on every sequence up to six actions, and gets
 *     every graded case right
 *   - common sense is wrong on some observations, and the "turning down also resets" rival is caught
 *   - the prompt names the heater's actions and what can be seen, never another device's
 *   - a whole repeat runs through the three arms; the world is asked at most 6 times, never an
 *     observation or a test case; bare gets no answers from the world
 *   - every call asks for the 200,000-token reply limit
 * Run with:  node "49 second device tests.js"
 */
const K = require('./25 construction worlds.js');
const G = require('./45 grudge again.js');
const { DEVICE } = require('./49 heater.js');
const H = require('./49 second device.js');

let failed = 0;
function expect_that(name, ok, detail) {
  if (!ok) failed++;
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${name}${ok || detail === undefined ? '' : `\n     ${detail}`}`);
}
const end = s => K.ending(DEVICE, s)[0].split(' is ')[1];
const TRUE = "// low, high, tripped\nfunction visible(a) { let h = 1; for (const x of a) { if (x === 'turn up') h = h === 3 ? 3 : h + 1; else if (x === 'turn down') h = h === 3 ? 3 : Math.max(0, h - 1); else if (x === 'wait' && h === 3) h = 0; } return { room: h === 1 || h === 2 ? 'warm' : 'cold' }; }";
const DOWN_RESETS = "// down also resets\nfunction visible(a) { let h = 1; for (const x of a) { if (x === 'turn up') h = h === 3 ? 3 : h + 1; else if (x === 'turn down') h = h === 3 ? 0 : Math.max(0, h - 1); else if (x === 'wait' && h === 3) h = 0; } return { room: h === 1 || h === 2 ? 'warm' : 'cold' }; }";
const block = c => '```javascript\n' + c + '\n```';
function stand_in() {
  const settings_seen = [], prompts = [];
  return {
    MODEL_NAME: 'stand-in', settings_seen, prompts,
    make_deepseek_guesser(send, settings) {
      settings_seen.push(settings);
      const g = async messages => { const last = messages[messages.length - 1].content; prompts.push(last); g.counts.tokens_out += 1; return /Write the one explanation/.test(last) ? block(TRUE) : [TRUE, DOWN_RESETS].map(block).join('\n\n'); };
      g.counts = { tokens_out: 0, cut_off: 0 };
      return g;
    },
  };
}

(async () => {
  expect_that('up, up is cold; up, down is warm; tripped ignores the dial; waiting resets to off', end(['turn up', 'turn up']) === 'cold' && end(['turn up', 'turn down']) === 'warm' && end(['turn up', 'turn up', 'turn down', 'turn up']) === 'cold' && end(['turn up', 'turn up', 'wait']) === 'cold' && end(['turn up', 'turn up', 'wait', 'turn up']) === 'warm');
  const s = H.setting();
  const t = H.grade(H.predictions_of(TRUE).said, s.observation_keys);
  expect_that('a hand-written true heater matches on every sequence and every graded case', H.true_everywhere(H.predictions_of(TRUE).said) && t.short_right === 106 && t.long_right === 972 && t.hard_right === t.hard_all, JSON.stringify(t));
  expect_that('common sense is wrong on some observations', s.observations.some(o => !o.obvious_right));
  const d = H.grade(H.predictions_of(DOWN_RESETS).said, s.observation_keys);
  expect_that('the "turning down also resets" rival is caught', d.long_right < 972, JSON.stringify(d));

  const st = stand_in();
  const rec = await H.run_repeat(G.with_higher_limit(st), 1);
  expect_that('the prompts name the heater\'s actions and what can be seen, not the grudge\'s', st.prompts.every(p => p.includes('"turn up"') && p.includes('"room"') && !/insult|Robin/.test(p)));
  expect_that('every call asks for the 200,000-token reply limit', st.settings_seen.every(x => x && x.reply_limit === 200000));
  expect_that('bare gets no answers from the world; random answers gets 6', rec.arms['bare'].world_answers === 0 && rec.arms['random answers'].world_answers === 6);
  const rc = rec.arms['rivals choose'];
  expect_that('rivals choose asks at most 6, never an observation or a test case', rc.world_answers <= 6 && rc.facts.every(f => !s.observation_keys.has(f.events.join('>')) && !s.test_keys.has(f.events.join('>'))), rc.world_answers);
  expect_that('the random answers are never an observation or a test case', rec.arms['random answers'].facts.every(f => !s.observation_keys.has(f.events.join('>')) && !s.test_keys.has(f.events.join('>'))));
  expect_that('the world\'s answers are the true heater\'s', rc.facts.concat(rec.arms['random answers'].facts).every(f => f.state === end(f.events)));
  expect_that('rivals choose asks where the two rivals disagree, if anywhere up to four actions', rc.rounds[0].fitting >= 1);
  expect_that('each arm is graded', H.ARMS.every(n => rec.arms[n].short_all === 106 && rec.arms[n].long_all === 972 && rec.arms[n].true_everywhere));
  expect_that('the summary builds', /\| bare \| 106 \|/.test(H.summarise([rec])));
  console.log(`\n${failed} test(s) failed.`);
  process.exit(failed ? 1 : 0);
})();
