/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Tests the pieces added in log 19, without calling DeepSeek:
 *   - the thinking setting reaches DeepSeek, and each call's tokens are written into the run's log
 *   - a direct question to DeepSeek carries no sentence asking for a model
 *   - "self review, three rounds" really reviews three times
 *   - the baseline's questions and grading: perfect answers are all right, empty answers all wrong,
 *     the true model is right on every question, and a majority vote picks the most common answer
 * Run with:  node "19 baseline tests.js"
 */
const C = require('./03 checker.js');
const L = require('./09 loop.js');
const D = require('./17 DeepSeek guesser.js');
const B = require('./19 baseline and more thinking.js');
const WORLDS = require('./03 test worlds.js').concat(require('./18 more test worlds.js'));

let failed = 0;
function expect_that(name, ok, detail) {
  if (!ok) failed++;
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${name}${ok || !detail ? '' : `\n     ${detail}`}`);
}
const as_deepseek = (content, tokens_out = 50) => ({ choices: [{ message: { role: 'assistant', content }, finish_reason: 'stop' }], usage: { prompt_tokens: 10, completion_tokens: tokens_out } });

(async () => {
  const world = WORLDS.find(w => w.id === 'ball-and-wall');

  // 1. Thinking setting and tokens.
  const sent = [];
  const g = D.make_deepseek_guesser(async body => { sent.push(body); return as_deepseek(JSON.stringify(world.world), 123); }, { effort: 'max' });
  const guess = await L.first_guess(world, { guesser: g });
  expect_that('the thinking setting reaches DeepSeek', sent[0].reasoning_effort === 'max');
  expect_that('each call\'s tokens are written into the log', guess.log[0].tokens_out === 123 && guess.log[0].tokens_in === 10, JSON.stringify(guess.log[0]).slice(0, 200));
  const plain = D.make_deepseek_guesser(async body => { sent.push(body); return as_deepseek('{}'); });
  await plain([{ role: 'user', content: 'Q' }]);
  expect_that('with no setting, DeepSeek\'s own default is used', !('reasoning_effort' in sent[sent.length - 1]));
  await plain([{ role: 'user', content: 'Q' }], { reply_shape: 'none' });
  expect_that('a direct question carries no sentence asking for a model', sent[sent.length - 1].messages[0].content === 'Q');

  // 2. Three rounds of self review.
  let reviews = 0;
  const reviewer = async messages => { if (messages[messages.length - 1].content.includes('Go through the task sentence by sentence')) reviews++; return JSON.stringify(world.world); };
  await L.run_task(world, 'self review', { guesser: reviewer, review_rounds: 3 }, { raw: world.world, log: [] });
  expect_that('"three rounds" reviews three times', reviews === 3, `reviewed ${reviews} times`);

  // 3. Questions and grading, on every world.
  let perfect_wrong = 0, empty_right = 0, truth_wrong = 0, questions_total = 0;
  for (const w of WORLDS) {
    const { questions } = B.build_questions(w);
    questions_total += questions.length;
    const perfect = Object.fromEntries(questions.map(q => [q.id, q.at === 'end' ? Object.fromEntries(q.parts.map(p => [p.thing, p.state])) : (q.at === 'ever' ? 'yes' : 'no')]));
    perfect_wrong += B.grade_direct(questions, perfect).filter(x => !x.right).length;
    empty_right += B.grade_direct(questions, {}).filter(x => x.right).length;
    truth_wrong += B.grade_model(questions, C.prepare_model(w.world)).filter(x => !x.right).length;
  }
  expect_that('every world has questions', questions_total > 150, `${questions_total}`);
  expect_that('perfect answers are all graded right', perfect_wrong === 0, `${perfect_wrong} wrong`);
  expect_that('empty answers are all graded wrong', empty_right === 0, `${empty_right} right`);
  expect_that('the true model is right on every question', truth_wrong === 0, `${truth_wrong} wrong`);
  const { questions } = B.build_questions(world);
  const q = questions[0];
  const right = { [q.id]: Object.fromEntries(q.parts.map(p => [p.thing, p.state])) };
  const wrong = { [q.id]: Object.fromEntries(q.parts.map(p => [p.thing, 'nonsense'])) };
  expect_that('a majority vote takes the most common answer', B.grade_direct([q], B.majority([right, wrong, right], [q]))[0].right && !B.grade_direct([q], B.majority([wrong, right, wrong], [q]))[0].right);
  const messages = B.direct_messages(world, questions, []);
  const shown_answer_given = messages[1].content.includes('rubber ball at solid wall');
  const held_back_answer_hidden = world.jobs.filter(j => j.held_back).every(j => !messages[1].content.includes(j.name));
  expect_that('DeepSeek alone sees the shown jobs\' answers but not the held-back answers', shown_answer_given && held_back_answer_hidden);

  console.log(`\n${failed} test(s) failed.`);
  process.exit(failed ? 1 : 0);
})();
