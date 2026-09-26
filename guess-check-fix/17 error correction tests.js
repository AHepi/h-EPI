/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Tests the changes made in log entry 17, and the DeepSeek guesser, without calling DeepSeek.
 *
 * The loop tests replay DeepSeek's real first guesses from the first DeepSeek run
 * ("runs/17 first DeepSeek run"), so they test the loop on the mistakes DeepSeek actually made:
 *   - the checker can swap a condition for one on a different thing ("Mara lights the lamp" to "the lamp is dark")
 *   - the full loop cross-checks a checker fix with the world before keeping it (a fix is a guess too)
 *   - the full loop looks for surprises, including poking a thing no rule reads
 *   - held-back jobs the world was asked about are listed, and only questions to the world count
 * The DeepSeek guesser tests use a stand-in that replies in DeepSeek's reply format.
 * Run with:  node "17 error correction tests.js"
 */
const C = require('./03 checker.js');
const L = require('./09 loop.js');
const D = require('./17 DeepSeek guesser.js');
const WORLDS = require('./03 test worlds.js');

let failed = 0;
function expect_that(name, ok, detail) {
  if (!ok) failed++;
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${name}${ok || !detail ? '' : `\n     ${detail}`}`);
}
const recorded = file => require(`./runs/17 first DeepSeek run/${file}.json`);
const world = id => WORLDS.find(w => w.id === id);
const nothing_new = async () => '{"new_things": {}, "new_start": {}, "new_rules": []}';
const replay = (file, mode, extra = {}) => {
  const rec = recorded(file);
  return L.run_task(world(rec.world), mode, Object.assign({ guesser: nothing_new }, extra), { raw: rec.first_guess.raw, log: [] });
};
const rules_of = model => model.rules.map(r => `${[].concat(r.when).join(' & ')} => ${r.then}`);

(async () => {
  // 1. The checker's new kind of small change.
  const story_guess = C.prepare_model(recorded('lighthouse-story repeat 2').first_guess.raw);
  const index = story_guess.rules.findIndex(r => r.name === 'mara sees storm night');
  const swaps = C.neighbours(story_guess, index).map(n => n.description);
  expect_that('a condition can be swapped for one on a different thing', swaps.includes('condition "mara lights lamp happens" replaced by "lamp is dark"'), swaps.join('; '));
  expect_that('a swap never reads the thing the rule sets', !swaps.some(s => s.includes('replaced by "storm night is')));

  // 2. The story: DeepSeek's guess ties the realisation to Mara lighting the lamp. The truth: the lamp was dark in the storm.
  const story = await replay('lighthouse-story repeat 2', 'full loop');
  expect_that('story: the full loop ends passing both held-back jobs', story.final.held_back_passed === 2, JSON.stringify(story.final));
  expect_that('story: without asking the world about either held-back situation', story.final.held_back_asked.length === 0, story.final.held_back_asked.join(', '));
  expect_that('story: a fix was cross-checked with the world', story.rounds.some(r => r.step === 'cross-check a fix with the world'));
  const story_off = await replay('lighthouse-story repeat 2', 'full loop', { look_for_surprises: false });
  expect_that('story: with surprise-hunting switched off, the lamp mistake survives', story_off.final.held_back_passed === 1, JSON.stringify(story_off.final));

  // 3. The to-do app: a cheap fix that silently disables "an urgent task becomes overdue after a day" is not kept.
  const todo = await replay('reminder-app repeat 2', 'full loop');
  const todo_rules = rules_of(todo.model);
  expect_that('to-do: the rule "urgent, then a day passes: overdue" survives', todo_rules.some(r => /day passes happens/.test(r) && /task is urgent/.test(r) && /overdue$/.test(r)), todo_rules.join(' | '));
  expect_that('to-do: a surprise was found', todo.added_jobs.some(a => a.surprise), JSON.stringify(todo.added_jobs.map(a => a.why)));
  expect_that('to-do: the guesser was asked for a new part', todo.rounds.some(r => r.step === 'new part'));

  // 4. Guess and fix never asks the world, so it is unchanged by any of this.
  const quiet = await replay('lighthouse-story repeat 2', 'guess and fix');
  expect_that('guess and fix asks the world nothing', quiet.questions_to_world === 0 && quiet.final.held_back_asked.length === 0);

  // 5. Held-back jobs counted as asked only when a question to the world had their situation.
  const ball = await replay('ball-and-wall repeat 1', 'guess and fix');
  expect_that('a held-back job is not "asked" just because a shown job shares its situation', ball.final.held_back_asked.length === 0, ball.final.held_back_asked.join(', '));

  // 5b. Guesser fixes first (log 18): on DeepSeek's river-puzzle guess, the checker's one-step patches
  // pass every job but break a held-back one. A guesser that rewrites correctly is asked first and wins.
  const river_world = require('./18 more test worlds.js').find(w => w.id === 'river-crossing');
  const river_guess = require('./runs/18 ten worlds after the fixes/river-crossing repeat 1.json').first_guess.raw;
  const rewriter = async messages => (messages[messages.length - 1].content.includes('Write the whole model again') ? JSON.stringify(river_world.world) : '{"new_things": {}, "new_start": {}, "new_rules": []}');
  const patched = await L.run_task(river_world, 'full loop', { guesser: nothing_new }, { raw: river_guess, log: [] });
  const rewritten = await L.run_task(river_world, 'guesser fixes first', { guesser: rewriter }, { raw: river_guess, log: [] });
  expect_that('river: the checker\'s patches alone lose a held-back job', patched.final.held_back_passed === 2, JSON.stringify(patched.final));
  expect_that('river: with the guesser rewriting first, every held-back job passes', rewritten.final.held_back_passed === 3 && rewritten.rounds.some(r => r.step === 'guesser rewrites first' && r.verdict === 'accepted'), JSON.stringify(rewritten.rounds.map(r => r.step)));
  const rewrites = rewritten.rounds.filter(r => r.step === 'guesser rewrites first').length;
  expect_that('the guesser is asked to rewrite at most three times', rewrites >= 1 && rewrites <= 3);

  // 5c. Self review and review first (log 18): a hidden mistake passes every shown job, so only a review
  // or a question to the world can find it. A reviewer that returns the true model repairs it at once.
  const todo_world = world('reminder-app');
  const hidden_mistake = C.model_to_form(Object.assign({}, C.prepare_model(todo_world.world), { rules: C.prepare_model(todo_world.world).rules.filter(r => r.name !== 'overdue after a day when urgent') }));
  const reviewer = async messages => (messages[messages.length - 1].content.includes('Go through the task sentence by sentence') ? JSON.stringify(todo_world.world) : '{"new_things": {}, "new_start": {}, "new_rules": []}');
  const no_review = await L.run_task(todo_world, 'guess and fix', { guesser: reviewer }, { raw: hidden_mistake, log: [] });
  const reviewed = await L.run_task(todo_world, 'self review', { guesser: reviewer }, { raw: hidden_mistake, log: [] });
  const review_first = await L.run_task(todo_world, 'review first', { guesser: reviewer }, { raw: hidden_mistake, log: [] });
  expect_that('a hidden mistake: guess and fix sees nothing to fix', no_review.final.held_back_passed < no_review.final.held_back_total && no_review.guesser_calls === 0);
  expect_that('self review repairs it, asking the world nothing', reviewed.final.held_back_passed === reviewed.final.held_back_total && reviewed.questions_to_world === 0);
  expect_that('review first starts with the review, then asks the world', review_first.rounds[1].step === 'self review' && review_first.final.held_back_passed === review_first.final.held_back_total && review_first.questions_to_world > 0, JSON.stringify(review_first.rounds.map(r => r.step)));
  const breaker = async () => JSON.stringify({ things: { task: ['new', 'done'] }, events: ['finish'], start: { task: 'new' }, rules: [] });
  const refused = await L.run_task(todo_world, 'self review', { guesser: breaker }, { raw: hidden_mistake, log: [] });
  expect_that('a review that breaks a shown job is not kept', refused.rounds[1].kept === false && refused.final.original_seen_passed === refused.final.original_seen_total);

  // 6. The DeepSeek guesser, with a stand-in for DeepSeek.
  const as_deepseek = (content, finish_reason = 'stop') => ({ choices: [{ message: { role: 'assistant', content, reasoning_content: 'thinking...' }, finish_reason }], usage: { prompt_tokens: 10, completion_tokens: 20 } });
  const sent = [];
  const g = D.make_deepseek_guesser(async body => { sent.push(body); return as_deepseek('{"things": {}}'); });
  const text = await g([{ role: 'system', content: 'GUIDE' }, { role: 'user', content: 'TASK' }], { temperature: 0.2, reply_shape: 'new part' });
  expect_that('the reply text comes back', text === '{"things": {}}');
  expect_that('the request names the model and a high reply limit', sent[0].model === 'deepseek-flash' && sent[0].max_tokens >= 16000);
  expect_that('the reply shape sentence is added to the last message', sent[0].messages[1].content.includes('"new_things"'));
  expect_that('the guide goes as a system message', sent[0].messages[0].role === 'system');
  expect_that('thinking is counted, not returned', g.counts.thinking_characters === 11 && g.counts.tokens_out === 20);

  let calls = 0;
  const flaky = D.make_deepseek_guesser(async body => { calls++; if (calls === 1) return { error: { message: 'busy' } }; return as_deepseek(body.messages.some(m => m.role === 'system') ? 'still full' : 'plain'); });
  expect_that('a failed request is tried again in the plainer form', await flaky([{ role: 'system', content: 'G' }, { role: 'user', content: 'T' }]) === 'plain' && flaky.counts.plain_form === 1);

  const cut = D.make_deepseek_guesser(async () => as_deepseek('{"things"', 'length'));
  await cut([{ role: 'user', content: 'T' }]);
  expect_that('a cut-off reply is counted', cut.counts.cut_off === 1);

  const saved_key = process.env.DEEPSEEK_API_KEY;
  process.env.DEEPSEEK_API_KEY = 'sk-test-secret';
  const leaky = D.make_deepseek_guesser(async () => { throw new Error('bad key sk-test-secret'); });
  let message = '';
  try { await leaky([{ role: 'user', content: 'T' }]); } catch (e) { message = e.message; }
  if (saved_key === undefined) delete process.env.DEEPSEEK_API_KEY; else process.env.DEEPSEEK_API_KEY = saved_key;
  expect_that('the key never appears in an error message', message && !message.includes('sk-test-secret') && message.includes('[key removed]'), message);

  console.log(`\n${failed} test(s) failed.`);
  process.exit(failed ? 1 : 0);
})();
