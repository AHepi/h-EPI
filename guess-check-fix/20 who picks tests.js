/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Tests "20 who picks the questions.js" without calling DeepSeek. A stand-in plays DeepSeek: it writes
 * the true model when asked for a model, answers every question correctly when asked directly, and
 * picks questions when asked to. Checks: the world's answers are right; random questions never repeat
 * a test question; DeepSeek's picked questions are read in either reply shape and unusable ones counted;
 * a whole run of one world completes, gives every arm the same number of answers, and leaves out of
 * scoring every test question some arm asked about.
 * Run with:  node "20 who picks tests.js"
 */
const C = require('./03 checker.js');
const B = require('./19 baseline and more thinking.js');
const P = require('./20 who picks the questions.js');
const WORLDS = require('./03 test worlds.js').concat(require('./18 more test worlds.js'));

let failed = 0;
function expect_that(name, ok, detail) {
  if (!ok) failed++;
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${name}${ok || !detail ? '' : `\n     ${detail}`}`);
}
const world = WORLDS.find(w => w.id === 'reminder-app');

// A stand-in for DeepSeek that answers from the true model.
function stand_in_for(world, pick_reply) {
  return {
    MODEL_NAME: 'stand-in',
    make_deepseek_guesser() {
      const g = async messages => {
        const last = messages[messages.length - 1].content;
        g.last_usage = { tokens_in: 1, tokens_out: 7 };
        if (last.includes('You may ask the owner')) return pick_reply;
        if (last.includes('Questions:\nQ1')) {
          const { questions } = B.build_questions(world);
          return JSON.stringify(Object.fromEntries(questions.map(q => [q.id, q.at === 'end' ? Object.fromEntries(q.parts.map(p => [p.thing, p.state])) : (q.at === 'ever' ? 'yes' : 'no')])));
        }
        return JSON.stringify(world.world);
      };
      g.counts = { cut_off: 0 };
      return g;
    },
  };
}

(async () => {
  const snooze_twice = C.prepare_jobs({ jobs: [{ name: 'x', events: ['snooze', 'snooze'], expect: [] }] }).jobs[0].situation;
  const a = P.world_answer(world, snooze_twice, 1);
  expect_that('the world answers a situation with its true end state', a && a.expect.includes('task is urgent'), JSON.stringify(a));
  const unknown = C.prepare_jobs({ jobs: [{ name: 'x', events: ['explode'], expect: [] }] }).jobs[0].situation;
  expect_that('a situation the world cannot read gets no answer', P.world_answer(world, unknown, 1) === null);

  const { questions } = B.build_questions(world);
  const test_keys = new Set(questions.map(q => JSON.stringify(q.situation)));
  const random = P.random_situations(world, 12, test_keys, 'salt');
  expect_that('random questions never repeat a test question', random.length > 0 && random.every(s => !test_keys.has(JSON.stringify(s))));
  expect_that('random questions change with the salt', JSON.stringify(P.random_situations(world, 12, test_keys, 'other salt')) !== JSON.stringify(random));

  const list_reply = '[{"start": {}, "events": ["snooze"]}, {"start": {}, "events": ["explode"]}]';
  const wrapped_reply = '{"questions": [{"start": {}, "events": ["snooze"]}]}';
  const stand_in = stand_in_for(world, list_reply);
  const picked = await P.deepseek_picks(stand_in.make_deepseek_guesser(), world, 2);
  expect_that('picked questions are read from a plain list', picked.situations.length === 2 && picked.written === 2);
  const wrapped = await P.deepseek_picks(stand_in_for(world, wrapped_reply).make_deepseek_guesser(), world, 2);
  expect_that('picked questions are read when wrapped in {"questions": ...}', wrapped.situations.length === 1);

  const rec = await P.run_world(world, 1, stand_in_for(world, list_reply));
  const n = rec.questions_to_world;
  expect_that('a whole run completes with every arm', ['guesser fixes first', 'DeepSeek alone', 'ask then answer (the loop picks the questions)', 'random questions, then answer', 'DeepSeek picks questions, then answer'].every(name => rec.arms[name]), Object.keys(rec.arms).join(', '));
  expect_that('the loop and random questions get the same number of answers', rec.arms['random questions, then answer'].answers_given === n && rec.arms['ask then answer (the loop picks the questions)'].answers_given === n, `loop ${n}, random ${rec.arms['random questions, then answer'].answers_given}`);
  expect_that('an unusable picked question is counted, not answered', rec.arms['DeepSeek picks questions, then answer'].questions_unusable === 1);
  const asked = new Set([...rec.asked.loop, ...rec.asked.random, ...rec.asked.deepseek].map(s => JSON.stringify(s)));
  expect_that('every test question some arm asked about is left out of scoring', questions.filter(q => asked.has(JSON.stringify(q.situation))).every(q => rec.left_out_of_scoring.includes(q.id)));
  expect_that('a stand-in that answers correctly is graded all right', rec.arms['DeepSeek alone'].nearby_right === rec.arms['DeepSeek alone'].nearby_total);
  const table = P.summarise([rec]);
  const first_table = table.split('\n\n')[0].split('\n');
  expect_that('the summary has a row per arm', first_table.length === 2 + Object.keys(rec.arms).length, first_table.length);
  expect_that('the summary counts by world and by repeat', table.includes('by world') && table.includes('by repeat'));

  console.log(`\n${failed} test(s) failed.`);
  process.exit(failed ? 1 : 0);
})();
