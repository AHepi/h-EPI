/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Tests "22 twenty questions.js" without calling DeepSeek. A stand-in plays DeepSeek: it asks a scripted
 * run of questions (one it cannot use, one repeated, the owner's own question, a wrong expectation), tries
 * to stop early, and then answers. Checks that exactly 20 questions are asked before any answer, that a
 * try to stop is refused and counted, that each question is marked usable, repeated, the owner's own,
 * surprising or not, and that a whole world runs through all three arms.
 * Run with:  node "22 twenty questions tests.js"
 */
const C = require('./03 checker.js');
const T = require('./21 long texts.js');
const W = require('./22 twenty questions.js');
const WORLDS = require('./03 test worlds.js').concat(require('./18 more test worlds.js'));

let failed = 0;
function expect_that(name, ok, detail) {
  if (!ok) failed++;
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${name}${ok || !detail ? '' : `\n     ${detail}`}`);
}
const world = WORLDS.find(w => w.id === 'reminder-app');
const { embedded, tests } = T.embedded_question(world);
const answer_of = q => (q.at === 'end' ? Object.fromEntries(q.parts.map(p => [p.thing, p.state])) : (q.at === 'ever' ? 'yes' : 'no'));
const final = { owner_asked: 'x', situation: { events: ['snooze', 'snooze', 'day passes'] }, answer: answer_of(embedded) };

function stand_in() {
  let asks = 0;
  const script = [
    { ask: { events: ['snooze'] }, i_expect: { task: 'urgent' } },          // surprise: the world says new
    { ask: { events: ['snooze'] }, i_expect: { task: 'new' } },             // repeat, no surprise
    { ask: { events: ['explode'] }, i_expect: { task: 'new' } },            // unusable
    { stop: true, answer: 'too soon' },                                     // a try to stop
    { ask: { events: ['snooze', 'snooze', 'day passes'] }, i_expect: { task: 'overdue' } }, // the owner's own question
  ];
  return {
    MODEL_NAME: 'stand-in',
    make_deepseek_guesser() {
      const g = async messages => {
        const last = messages[messages.length - 1].content;
        g.counts.tokens_out += 3;
        if (last.includes('Questions:\nQ1')) return JSON.stringify(Object.fromEntries(tests.map(q => [q.id, answer_of(q)])));
        if (messages[0].content.startsWith('You help the owner') && last.includes('exactly 20 questions') || /more question|of 20 asked/.test(last)) {
          const next = script[asks++] || { ask: { events: ['finish'] }, i_expect: { task: 'done' } };
          return JSON.stringify(next);
        }
        if (messages[0].content.startsWith('You help the owner')) return JSON.stringify(final);
        return JSON.stringify(world.world);
      };
      g.counts = { tokens_out: 0, cut_off: 0 };
      return g;
    },
  };
}

(async () => {
  const test_keys = new Set(tests.map(q => JSON.stringify(q.situation)));
  const r = await W.must_ask(stand_in(), world, T.message(world, 'long', embedded), embedded, test_keys);
  expect_that('exactly 20 questions are asked before the answer', r.asked.length === 20, r.asked.length);
  expect_that('a try to stop early is refused and counted', r.stop_tries === 1, `stop tries ${r.stop_tries}, not a question ${r.unreadable}`);
  expect_that('the first answer surprised it, the second did not', r.asked[0].surprised === true && r.asked[1].surprised === false);
  expect_that('the second question is marked a repeat', r.asked[1].repeat_of_earlier && !r.asked[0].repeat_of_earlier);
  expect_that('the unusable question is marked and not answered', r.asked[2].usable === false && r.answers.length === 19);
  expect_that('the owner\'s own question asked back is marked', r.asked[3].is_the_owners_question);
  expect_that('after 20 questions the answer is graded', r.grade.found_and_right);
  expect_that('an expectation about nothing the world answers is not counted', W.surprised({ colour: 'red' }, { expect: ['task is new'] }) === null);

  const rec = await W.run_world(world, 1, stand_in());
  expect_that('a whole world runs through all three arms', ['answer straight away', 'random 20, then answer', 'must ask 20, then answer'].every(n => rec.arms[n]), Object.keys(rec.arms).join(', '));
  expect_that('random 20 gives 20 answers', rec.arms['random 20, then answer'].answers_given === 20);
  expect_that('the summary lists what DeepSeek did with its questions', W.summarise([rec]).includes('asked back: 1 times, in 1 of 1 runs'));

  console.log(`\n${failed} test(s) failed.`);
  process.exit(failed ? 1 : 0);
})();
