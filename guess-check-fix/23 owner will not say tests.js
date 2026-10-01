/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Tests "23 owner will not say.js" and the refusal in "22 twenty questions.js" without calling DeepSeek.
 * A stand-in asks the owner's own question (refused, and it still counts as one of the 20), a near copy
 * (answered, and flagged), and ordinary questions. Checks the refusal is never answered, the near copy
 * is flagged, log 22's behaviour is unchanged when refusal is off, and a whole world runs through.
 * Run with:  node "23 owner will not say tests.js"
 */
const T = require('./21 long texts.js');
const W = require('./22 twenty questions.js');
const O = require('./23 owner will not say.js');
const WORLDS = require('./03 test worlds.js').concat(require('./18 more test worlds.js'));

let failed = 0;
function expect_that(name, ok, detail) {
  if (!ok) failed++;
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${name}${ok || !detail ? '' : `\n     ${detail}`}`);
}
const world = WORLDS.find(w => w.id === 'reminder-app');
const { embedded, tests } = T.embedded_question(world);
const answer_of = q => (q.at === 'end' ? Object.fromEntries(q.parts.map(p => [p.thing, p.state])) : (q.at === 'ever' ? 'yes' : 'no'));

function stand_in() {
  let asks = 0;
  const script = [
    { ask: { events: ['snooze', 'snooze', 'day passes'] }, i_expect: { task: 'overdue' } },            // the owner's own question
    { ask: { events: ['snooze', 'snooze', 'day passes', 'finish'] }, i_expect: { task: 'done' } },    // a near copy
    { ask: { start: { task: 'new' }, events: ['snooze', 'snooze', 'day passes'] }, i_expect: { task: 'overdue' } }, // the owner's own, default written out
  ];
  const seen = [];
  return {
    seen,
    MODEL_NAME: 'stand-in',
    make_deepseek_guesser() {
      const g = async messages => {
        const last = messages[messages.length - 1].content;
        g.counts.tokens_out += 3;
        seen.push(last);
        if (last.includes('Questions:\nQ1')) return JSON.stringify(Object.fromEntries(tests.map(q => [q.id, answer_of(q)])));
        if (last.includes('exactly 20 questions') || /more question|of 20 asked/.test(last)) return JSON.stringify(script[asks++] || { ask: { events: ['finish'] }, i_expect: { task: 'done' } });
        if (messages[0].content.startsWith('You help the owner')) return JSON.stringify({ owner_asked: 'x', situation: { events: ['snooze', 'snooze', 'day passes'] }, answer: answer_of(embedded) });
        return JSON.stringify(world.world);
      };
      g.counts = { tokens_out: 0, cut_off: 0 };
      return g;
    },
  };
}

(async () => {
  const test_keys = new Set(tests.map(q => JSON.stringify(q.situation)));
  const s = stand_in();
  const r = await W.must_ask(s, world, T.message(world, 'long', embedded), embedded, test_keys, { refuse: true });
  expect_that('20 questions are still asked', r.asked.length === 20);
  expect_that('the owner\'s own question is refused, written either way', r.asked[0].refused && r.asked[2].refused, JSON.stringify(r.asked.slice(0, 3).map(q => q.refused)));
  expect_that('a refused question gets no answer', r.answers.length === 18 && s.seen.some(m => m.startsWith("The owner says: I can't tell you that one")));
  expect_that('the refusal never gives the answer away', !s.seen.some(m => m.includes("I can't tell you") && m.includes('overdue')));
  expect_that('a near copy is answered and flagged', r.asked[1].extends_owners_question && !r.asked[1].refused && r.asked[1].usable);
  const off = await W.must_ask(stand_in(), world, T.message(world, 'long', embedded), embedded, test_keys);
  expect_that('with refusal off (log 22), the owner\'s question is answered', !off.asked[0].refused && off.answers.length === 20);
  expect_that('a situation that does not start like the owner\'s is not a near copy', !W.extends_owners_question(JSON.stringify({ start: {}, events: ['finish'] }), JSON.stringify({ start: {}, events: ['snooze'] })));

  const rec = await O.run_world(world, 1, stand_in());
  expect_that('a whole world runs through both arms', rec.arms['answer straight away'] && rec.arms['must ask 20, owner will not say']);
  const summary = O.summarise([rec]);
  expect_that('the summary counts refusals and near copies', summary.includes('was refused: 2 times, in 1 of 1 runs') && summary.includes('near copy (the owner\'s question plus more events): 1 times'), summary.split('\n').filter(l => l.includes('refused') || l.includes('near copy')).join(' / '));

  console.log(`\n${failed} test(s) failed.`);
  process.exit(failed ? 1 : 0);
})();
