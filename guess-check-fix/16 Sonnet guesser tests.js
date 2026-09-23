/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Tests the loop with the Sonnet guesser plugged in, using a stand-in for Sonnet (no real Sonnet).
 * The stand-in replies in Sonnet's reply format, so everything except the real connection is tested:
 * the requests the guesser builds, reading the replies, the fall-back to a plainer request, the count
 * of cut-off replies, and all four ways of running on all five worlds.
 *
 * Two stand-ins:
 *   right first time - replies with each world's hidden true model (a perfect guesser)
 *   one piece short  - replies with a model missing one piece; asked for a new part, it supplies it
 * Run with:  node "16 Sonnet guesser tests.js"
 */
const L = require('./09 loop.js');
const C = require('./03 checker.js');
const S = require('./16 Sonnet guesser.js');
const WORLDS = require('./03 test worlds.js');

let failed = 0;
function expect_that(name, ok, detail) {
  if (!ok) failed++;
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${name}${ok || !detail ? '' : `\n     ${detail}`}`);
}
const reply_as_sonnet = (text, stop_reason = 'end_turn') => ({ content: [{ type: 'text', text }], stop_reason });
const world_of = body => WORLDS.find(w => body.messages[0].content.includes(w.request));
const is_new_part = body => body.messages[body.messages.length - 1].content.includes('Write only the new parts');

// What the "one piece short" stand-in leaves out of each world, and supplies when asked for a new part.
function short_model(world) {
  if (world.id === 'hidden-ball') {
    return { things: { screen: world.world.things.screen, seen: world.world.things.seen }, events: [], start: { screen: 'down', seen: 'at 1' },
      rules: [{ name: 'a', when: ['seen is at 1'], then: 'seen is at 2' }, { name: 'b', when: ['seen is at 2'], then: 'seen is at 3' }, { name: 'c', when: ['seen is at 3'], then: 'seen is at 4' },
        { name: 'hide', when: ['seen is at 1', 'screen is up'], then: 'seen is nothing' }, { name: 'reappear', when: ['seen is nothing'], then: 'seen is at 4' }] };
  }
  return Object.assign({}, world.world, { rules: world.world.rules.slice(0, -1) });
}
function missing_piece(world) {
  if (world.id === 'hidden-ball') {
    return { new_things: { place: world.world.things.place }, new_start: { place: '1' }, new_rules: world.world.rules };
  }
  return { new_things: {}, new_start: {}, new_rules: [world.world.rules[world.world.rules.length - 1]] };
}

async function run_all(guesser) {
  const table = [];
  for (const world of WORLDS) {
    const guess = await L.first_guess(world, { guesser });
    for (const mode of L.WAYS_OF_RUNNING) {
      const r = await L.run_task(world, mode, { guesser }, guess);
      table.push({ world: world.id, mode, shown: `${r.final.original_seen_passed}/${r.final.original_seen_total}`, held: `${r.final.held_back_passed}/${r.final.held_back_total}`, questions: r.questions_to_world, asked: r.guesser_calls, rounds: r.rounds.map(x => x.step) });
    }
  }
  return table;
}

(async () => {
  // 1. A perfect stand-in, replying with text around the JSON, the way chat models often do.
  const sent = [];
  const perfect = S.make_sonnet_guesser(async body => {
    sent.push(body);
    const world = world_of(body);
    return reply_as_sonnet(`Here is the model:\n\n\`\`\`json\n${JSON.stringify(world.world, null, 1)}\n\`\`\`\n`);
  });
  const perfect_table = await run_all(perfect);
  expect_that('the guide goes to Sonnet as its standing instructions', sent[0].system === L.GUIDE);
  expect_that('the request names Sonnet 4.6 and the 1000-token cap', sent[0].model === 'claude-sonnet-4-6' && sent[0].max_tokens === 1000);
  expect_that('the request ends with the shape to reply in', sent[0].messages[0].content.endsWith(S.SHAPE_SENTENCES.model));
  expect_that('a reply with text around the JSON is still read', perfect_table.filter(r => r.mode === 'one guess').every(r => r.rounds[0] === 'guess'));
  expect_that('a perfect guess passes every shown job in every world, every way', perfect_table.every(r => r.shown.split('/')[0] === r.shown.split('/')[1]),
    perfect_table.filter(r => r.shown.split('/')[0] !== r.shown.split('/')[1]).map(r => `${r.world} ${r.mode} ${r.shown}`).join('; '));
  expect_that('a perfect guess passes every held-back job too', perfect_table.every(r => r.held.split('/')[0] === r.held.split('/')[1]),
    perfect_table.filter(r => r.held.split('/')[0] !== r.held.split('/')[1]).map(r => `${r.world} ${r.mode} ${r.held}`).join('; '));
  expect_that('a perfect guess needs no second request', perfect_table.every(r => r.asked === 0) && sent.length === WORLDS.length);

  // 2. A stand-in one piece short: the loop has to correct it.
  const short = S.make_sonnet_guesser(async body => {
    const world = world_of(body);
    if (is_new_part(body)) return reply_as_sonnet(JSON.stringify(missing_piece(world)));
    return reply_as_sonnet(JSON.stringify(short_model(world)));
  });
  const short_table = await run_all(short);
  console.log('\n  one piece short, as the page would show it:');
  for (const r of short_table) console.log(`   ${r.world.padEnd(17)} ${r.mode.padEnd(14)} shown ${r.shown}  held back ${r.held}  questions ${r.questions}  Sonnet asked again ${r.asked}`);
  console.log('');
  const row = (world, mode) => short_table.find(r => r.world === world && r.mode === mode);
  expect_that('hidden ball: one guess alone fails, since it tracks only what is seen', row('hidden-ball', 'one guess').shown !== '5/5');
  expect_that('hidden ball: guess and fix gets every shown job by asking for a new part', row('hidden-ball', 'guess and fix').shown === '5/5' && row('hidden-ball', 'guess and fix').asked >= 1, JSON.stringify(row('hidden-ball', 'guess and fix')));
  expect_that('door game: the missing game-over rule is supplied as a new part', row('door-game', 'guess and fix').shown === '4/4', JSON.stringify(row('door-game', 'guess and fix')));
  expect_that('the rewrite way runs and asks Sonnet again', short_table.filter(r => r.mode === 'rewrite').some(r => r.asked > 0));

  // 3. Sonnet refuses the first form (for example, if the connection did not accept the guide as standing instructions).
  const forms = [];
  const picky = S.make_sonnet_guesser(async body => {
    forms.push(body.system ? 'full' : 'plain');
    if (body.system) return { error: { message: 'system is not allowed here' } };
    return reply_as_sonnet(JSON.stringify(WORLDS[0].world));
  });
  const text = await picky([{ role: 'system', content: L.GUIDE }, { role: 'user', content: 'Task: test' }], { temperature: 0.2, reply_shape: 'model' });
  expect_that('a refused request is tried again in the plainer form, and works', forms.join(',') === 'full,plain' && L.read_reply(text) !== null && picky.counts.plain_form === 1, forms.join(','));

  // 4. A reply cut off at the length cap is counted, and read as unreadable rather than as a bad model.
  const cut = S.make_sonnet_guesser(async () => reply_as_sonnet('{"things": {"ball": ["in hand", "fly', 'max_tokens'));
  const cut_text = await cut([{ role: 'system', content: 'x' }, { role: 'user', content: 'y' }], {});
  expect_that('a cut-off reply is counted and cannot be read', cut.counts.cut_off === 1 && L.read_reply(cut_text) === null);

  console.log(`\n${failed} test(s) failed.`);
  process.exit(failed ? 1 : 0);
})();
