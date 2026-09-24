/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Tests "25 construction worlds.js" and "25 construction test.js" without calling DeepSeek:
 *   - each device: the true explanation fits every observation and test case; the obvious one is refuted
 *     by the observations and gets exactly the 4 easy test cases right; the observations show the same
 *     visible state and action leading to different outcomes, so a hidden thing is needed
 *   - every arm is told the same sentence about unseen things, and no arm sees a test case's answer
 *   - grading: the true explanation answering in words is all right; a model arm with the true model is
 *     all right with reach 120 of 120; the obvious model's reach is lower
 *   - conjecture and criticism: a stand-in that first writes the obvious model and, once shown the
 *     failures, writes the true one, ends right; blind retries tells it only how many fail
 *   - a whole device runs through all five arms
 * Run with:  node "25 construction test tests.js"
 */
const C = require('./03 checker.js');
const K = require('./25 construction worlds.js');
const X = require('./25 construction test.js');

let failed = 0;
function expect_that(name, ok, detail) {
  if (!ok) failed++;
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${name}${ok || !detail ? '' : `\n     ${detail}`}`);
}

function stand_in(device) {
  const { tests } = K.observations_and_tests(device);
  const seen = [];
  return {
    seen, MODEL_NAME: 'stand-in',
    make_deepseek_guesser() {
      const g = async messages => {
        const last = messages[messages.length - 1].content;
        seen.push(last);
        g.counts.tokens_out += 2;
        if (messages[0].role === 'system') return JSON.stringify(last.includes('Your last model') && !last.includes('observations do not hold.') ? device.world : device.obvious);
        return JSON.stringify({ rule: 'x', answers: Object.fromEntries(tests.map((t, i) => [`T${i + 1}`, t.expect[0].split(' is ')[1]])) });
      };
      g.counts = { tokens_out: 0, cut_off: 0 };
      return g;
    },
  };
}

(async () => {
  for (const d of K.DEVICES) {
    const { observations, tests } = K.observations_and_tests(d);
    const oj = C.prepare_jobs({ jobs: observations }).jobs, tj = C.prepare_jobs({ jobs: tests }).jobs;
    const truth = C.prepare_model(d.world), obvious = C.prepare_model(d.obvious);
    const trans = {}; let conflict = false;
    for (const o of observations) { let prev = K.ending(d, []).join(); for (let i = 0; i < o.events.length; i++) { const now = K.ending(d, o.events.slice(0, i + 1)).join(); const k = `${prev}+${o.events[i]}`; if (trans[k] && trans[k] !== now) conflict = true; trans[k] = now; prev = now; } }
    expect_that(`${d.id}: the true explanation fits all 14 observations and 12 test cases`, C.check(truth, oj).passed.length === 14 && C.check(truth, tj).passed.length === 12);
    expect_that(`${d.id}: the observations refute the obvious explanation`, C.check(obvious, oj).failed.length > 0);
    expect_that(`${d.id}: the obvious explanation gets exactly the 4 easy test cases right`, C.check(obvious, tj).passed.length === 4 && tests.filter(t => t.obvious_right).length === 4);
    expect_that(`${d.id}: the observations need a hidden thing`, conflict);
    expect_that(`${d.id}: no test case is longer than 4 actions or repeats an observation`, tests.every(t => t.events.length <= 4 && !observations.some(o => o.events.join() === t.events.join())));
    const words = X.evidence_in_words(d, observations) + X.questions_in_words(d, tests);
    expect_that(`${d.id}: every arm hears about unseen things, and sees no test answer`, words.includes(X.HIDDEN_HINT) && !tests.some(t => words.includes(`: ${t.events.join(', then ')}. At the end: `)));
    const r_true = X.reach(d, truth), r_obvious = X.reach(d, obvious);
    expect_that(`${d.id}: the true model reaches every sequence of up to four actions, the obvious one fewer`, r_true.right === r_true.of && r_true.of === K.sequences(d.world.events, 4).length && r_obvious.right < r_obvious.of);
  }

  const d = K.DEVICES.find(x => x.id === 'magnet-ball');
  const { observations, tests } = K.observations_and_tests(d);
  const s = stand_in(d);
  const loop = await X.explain_and_criticise(s, d, observations, tests, false);
  expect_that('conjecture and criticism: obvious first, true once shown the failures, then all right', loop.rounds.length === 2 && loop.best_passes === 14 && loop.graded.every(g => g.right) && loop.final_hidden_things.includes('magnet'), JSON.stringify(loop.rounds.map(r => r.passed)));
  expect_that('the report names what failed', s.seen.some(m => m.includes('Your last model') && /fail/i.test(m) && !m.includes('observations do not hold.')));
  const s2 = stand_in(d);
  const blind = await X.explain_and_criticise(s2, d, observations, tests, true);
  expect_that('blind retries: told only how many fail', s2.seen.some(m => /\d+ of 14 observations do not hold\./.test(m)) && blind.rounds.length === 6 && blind.best_passes < 14);
  expect_that('a majority takes the most common answer', X.majority(d, tests.slice(0, 1), [{ answers: { T1: 'left' } }, { answers: { T1: 'right' } }, { answers: { T1: 'left' } }]).T1 === 'left');

  const rec = await X.run_device(d, 1, stand_in(d));
  expect_that('a whole device runs through all five arms', ['bare', 'bare, majority of 5', 'bare, checks itself', 'conjecture and criticism', 'blind retries'].every(n => rec.arms[n]));
  expect_that('bare arms answering from the truth are all right', rec.arms['bare'].graded.every(g => g.right) && rec.arms['bare, checks itself'].graded.every(g => g.right));
  expect_that('the summary has a row per arm', X.summarise([rec]).split('\n\n')[0].split('\n').length === 7);

  console.log(`\n${failed} test(s) failed.`);
  process.exit(failed ? 1 : 0);
})();
