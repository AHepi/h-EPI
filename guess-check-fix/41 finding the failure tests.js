/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Tests "41 finding the failure.js" without calling DeepSeek. Checks:
 *   - the record follows the plan: 8 fixes the current method accepted, 4 of which broke something no job
 *     checks, with 9 such breaks visible, and no word in it saying which fixes were bad
 *   - the question asked never says what is wrong
 *   - a reply that returns the method unchanged is counted as unchanged and not judged
 *   - a changed method is judged on the held occasions by log 39's aims
 *   - the "What is wrong:" line is read
 * Run with:  node "41 finding the failure tests.js"   (building the held occasions takes about a minute)
 */
const O = require('./39 occasions.js');
const M = require('./39 changing a method.js');
const F = require('./41 finding the failure.js');

let failed = 0;
function expect_that(name, ok, detail) {
  if (!ok) failed++;
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${name}${ok || !detail ? '' : `\n     ${detail}`}`);
}
function stand_in(code, wrong) {
  return { MODEL_NAME: 'stand-in', asked: [], make_deepseek_guesser() { const self = this; const g = async m => { self.asked.push(m); g.counts.tokens_out += 1; return '```javascript\n' + code + '\n```\nWhat is wrong: ' + wrong; }; g.counts = { tokens_out: 0, cut_off: 0 }; return g; } };
}

(async () => {
  const entries = F.record();
  expect_that('the record has 8 accepted fixes, 4 of which broke something', entries.length === 8 && entries.filter(e => e.broke).length === 4);
  const visible = entries.reduce((s, e) => s + e.shown_changed.filter(x => x.before === x.world && x.after !== x.world).length, 0);
  expect_that('9 breaks are visible in the record', visible === 9, visible);
  const words = F.record_words(entries);
  expect_that('the record says nothing about which fixes were bad', !/\b(bad|broke|wrong|mistake|should not)\b/i.test(words), (words.match(/\b(bad|broke|wrong|mistake|should not)\b/i) || [])[0]);
  expect_that('the job description and question never say what is wrong', !/break|no job checks|should not have/i.test(F.JOB + F.QUESTION));

  const { held } = M.split(O.occasions());
  const same = await F.ask_arm(stand_in(M.CURRENT, 'nothing'), entries, held, true);
  expect_that('returning the method unchanged is counted as unchanged and not judged', same.unchanged && same.held === null && same.what_is_wrong === 'nothing');
  const s = stand_in(M.REFERENCE, 'it accepts fixes that break situations no job checks');
  const changed = await F.ask_arm(s, entries, held, true);
  expect_that('a changed method is judged on the held occasions: the person\'s repair is kept with 13', !changed.unchanged && changed.held.kept && changed.held.bad_rejected === 13);
  expect_that('the with-the-record arm shows the record; the method-only arm does not', s.asked[0][1].content.includes('Fix 1 (accepted)'));
  const s2 = stand_in(M.CURRENT, 'nothing');
  await F.ask_arm(s2, entries, held, false);
  expect_that('the method-only arm has no record', !s2.asked[0][1].content.includes('Fix 1 (accepted)'));
  expect_that('what is wrong is read from its line', changed.what_is_wrong === 'it accepts fixes that break situations no job checks');

  console.log(`\n${failed} test(s) failed.`);
  process.exit(failed ? 1 : 0);
})();
