/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Tests "39 changing a method.js" and "39 occasions.js" without calling DeepSeek. Checks:
 *   - the occasions follow the plan: 90 in all, 3 of each kind per world, 72 held in eight worlds
 *   - the current method accepts every bad fix and is not kept; log 17's repair is kept and rejects 13 of
 *     the 24 held bad fixes (the plan's design check)
 *   - a method gets at most three answers from the world per fix, and the program records which it asked
 *   - a method cannot read the world's answers directly, reach the account key, or run for ever
 *   - the shown arm reports wrong decisions and keeps going; the told-the-aim arm gets one reply
 *   - what a method says it does is read from its "What it does:" line
 * Run with:  node "39 changing a method tests.js"   (building the occasions takes about a minute)
 */
const O = require('./39 occasions.js');
const M = require('./39 changing a method.js');

let failed = 0;
function expect_that(name, ok, detail) {
  if (!ok) failed++;
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${name}${ok || !detail ? '' : `\n     ${detail}`}`);
}

const REJECT_ALL = 'function accept_fix(fix_case, ask) { return false; }';
function stand_in() {
  let shown_calls = 0;
  return {
    MODEL_NAME: 'stand-in', asked: [],
    make_deepseek_guesser() {
      const self = this;
      const g = async messages => {
        g.counts.tokens_out += 5; self.asked.push(messages);
        const last = messages[messages.length - 1].content;
        if (last.includes('The current method has a failure')) {
          shown_calls++;
          const code = shown_calls === 1 ? REJECT_ALL : M.REFERENCE;
          return 'Here.\n```javascript\n' + code + '\n```\nWhat it does: asks the world about places where the fix changes the answer, and rejects the fix if the world sides with the old model.';
        }
        return '```javascript\n' + M.CURRENT + '\n```\nWhat it does: accepts a fix that repairs a job and loses none.';
      };
      g.counts = { tokens_out: 0, cut_off: 0 };
      return g;
    },
  };
}

(async () => {
  const all = O.occasions();
  const { shown, held } = M.split(all);
  expect_that('90 occasions, 3 of each kind in each of the ten worlds', all.length === 90 && O.WORLDS.every(w => ['bad', 'good', 'losing'].every(k => all.filter(o => o.world === w.id && o.kind === k).length === 3)));
  expect_that('18 shown occasions (lighthouse story, ball and wall) and 72 held', shown.length === 18 && held.length === 72 && held.filter(o => o.kind === 'bad').length === 24);
  expect_that('a method never sees an occasion\'s kind or the world\'s answers in its case', held.every(o => !('kind' in o.case) && !JSON.stringify(o.case).includes('world')));

  const current = M.judge(M.CURRENT, held);
  expect_that('the current method rejects no held bad fix, so it is not kept', current.bad_rejected === 0 && !current.kept);
  const reference = M.judge(M.REFERENCE, held);
  expect_that('log 17\'s repair is kept and rejects 13 of 24 held bad fixes', reference.kept && reference.bad_rejected === 13, JSON.stringify({ kept: reference.kept, bad: reference.bad_rejected, losses: reference.protected_losses }));
  expect_that('log 17\'s repair keeps every protected aim', !reference.protected_losses.good_not_accepted.length && !reference.protected_losses.losing_accepted.length && !reference.protected_losses.errors.length);
  expect_that('its questions are recorded by the program, at most three per fix', reference.questions_asked > 0 && reference.rows.every(r => r.asked.length <= 3));

  const greedy = M.run_method('function accept_fix(c, ask) { const got = [0,1,2,3,4].map(i => ask(i)); return got[3] === null && got[4] === null; }', held.slice(0, 2));
  expect_that('a fourth and fifth question get no answer, and only three are recorded', greedy.results.every(r => r.accept === true && r.asked.length === 3), JSON.stringify(greedy.results));
  const peek = M.run_method('function accept_fix(c, ask) { return typeof globalThis.__answers !== "undefined"; }', held.slice(0, 3));
  expect_that('a method cannot read the world\'s answers directly', peek.results.every(r => r.accept === false), JSON.stringify(peek.results));
  process.env.SECRET_FOR_THIS_TEST = 'do-not-leak-3939';
  const escape = M.run_method('function accept_fix(c, ask) { const p = this.constructor.constructor("return process")(); throw new Error(String(p.env.SECRET_FOR_THIS_TEST)); }', held.slice(0, 1));
  expect_that('a method cannot reach the account key or other settings', !JSON.stringify(escape).includes('do-not-leak-3939'), JSON.stringify(escape));
  const forever = M.judge('function accept_fix(c, ask) { while (true) {} }', held.slice(0, 2));
  expect_that('a method that never stops is cut off and counted as a protected loss', !forever.kept && forever.protected_losses.errors.length === 2, JSON.stringify(forever.rows[0]));
  const nonsense = M.judge('function accept_fix(c, ask) { return "maybe"; }', held.slice(0, 1));
  expect_that('an answer that is neither true nor false is an error', nonsense.protected_losses.errors.length === 1);

  const s = stand_in();
  const arm = await M.shown_the_failure(s, shown, held);
  const second = s.asked.filter(m => m[m.length - 1].content.includes('The current method has a failure'))[1];
  expect_that('the shown arm opens with two bad fixes the current method accepted, with what the world said', s.asked[0][1].content.includes('Fix 1.') && s.asked[0][1].content.includes('The fix broke this'));
  expect_that('the shown arm reports wrong decisions on the shown fixes', second && second[1].content.includes('rejected a fix that repaired a job and broke nothing'), second ? second[1].content.slice(-300) : 'no second round');
  expect_that('the shown arm keeps going and ends with the repair, kept on the held fixes', arm.calls === 2 && arm.held.kept && arm.held.bad_rejected === 13);
  expect_that('what the method says it does is read', /asks the world/.test(arm.said) && M.says_it_asks(arm.said));
  const told = await M.told_the_aim(stand_in(), shown, held);
  expect_that('the told-the-aim arm gets one reply, and the current method it returned is not kept', told.calls === 1 && told.held && !told.held.kept);
  expect_that('saying "accepts a fix that repairs a job" is not saying it asks the world', !M.says_it_asks(told.said));

  const text = M.summarise([{ repeat: 1, arms: { 'shown the failure': arm, 'told the aim': told } }], M.summary_of(reference), M.summary_of(current));
  expect_that('the summary lists the current method, the reference and each arm', ['| current method | no |', '| log 17\'s repair (written by a person) | yes | 13 |', '| shown the failure, repeat 1 | yes |', '| told the aim, repeat 1 | no |'].every(r => text.includes(r)), text.split('\n').slice(0, 6).join('\n'));

  console.log(`\n${failed} test(s) failed.`);
  process.exit(failed ? 1 : 0);
})();
