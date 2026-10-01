/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Tests "21 long texts.js" and "21 filler paragraphs.js" without calling DeepSeek:
 *   - the filler never uses the name of a thing or event from any world
 *   - the long message holds every sentence of the request and the embedded question exactly once,
 *     the question in the middle paragraph with nothing else from the request; it is about 2,300 words
 *   - "found" accepts the owner's situation written with or without the default start, and nothing else
 *   - the ask-or-stop loop: a stand-in that asks twice then answers; one that stops at once; one that never
 *     stops is held to 12 questions and then told to answer; replies that are not JSON are counted
 *   - a whole world runs through all arms with a stand-in
 * Run with:  node "21 long text tests.js"
 */
const C = require('./03 checker.js');
const B = require('./19 baseline and more thinking.js');
const T = require('./21 long texts.js');
const FILLER = require('./21 filler paragraphs.js');
const WORLDS = require('./03 test worlds.js').concat(require('./18 more test worlds.js'));

let failed = 0;
function expect_that(name, ok, detail) {
  if (!ok) failed++;
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${name}${ok || !detail ? '' : `\n     ${detail}`}`);
}
const answer_of = q => (q.at === 'end' ? Object.fromEntries(q.parts.map(p => [p.thing, p.state])) : (q.at === 'ever' ? 'yes' : 'no'));
const final_for = q => ({ stop: true, owner_asked: 'x', situation: { start: q.situation.start, events: Object.keys(q.situation.events).sort((a, b) => a - b).flatMap(k => q.situation.events[k]) }, answer: answer_of(q) });

// A stand-in for DeepSeek. script(messages) gives the reply for ask-or-stop turns.
function stand_in(world, script) {
  const { embedded, tests } = T.embedded_question(world);
  return {
    MODEL_NAME: 'stand-in',
    make_deepseek_guesser() {
      const g = async messages => {
        const last = messages[messages.length - 1].content;
        g.last_usage = { tokens_in: 1, tokens_out: 5 };
        g.counts.tokens_out += 5;
        if (messages[0].content.startsWith('You help the owner')) return script ? script(messages) : JSON.stringify(final_for(embedded));
        if (last.includes('Questions:\nQ1')) return JSON.stringify(Object.fromEntries(tests.map(q => [q.id, answer_of(q)])));
        return JSON.stringify(world.world);
      };
      g.counts = { tokens_out: 0, cut_off: 0 };
      return g;
    },
  };
}

(async () => {
  const names = new Set();
  for (const w of WORLDS) { Object.keys(w.world.things).forEach(t => names.add(t.toLowerCase().replace(/_/g, ' '))); w.world.events.forEach(e => names.add(e.toLowerCase())); }
  const clashes = [...names].filter(n => FILLER.some(p => new RegExp(`\\b${n}\\b`, 'i').test(p)));
  expect_that('the filler never names a thing or event of any world', clashes.length === 0, clashes.join(', '));

  let layout_ok = true, detail = '';
  for (const w of WORLDS) {
    const { embedded } = T.embedded_question(w);
    const long = T.message(w, 'long', embedded);
    const ask = T.question_in_prose(embedded);
    const paragraphs = long.split('\n\n');
    const middle = paragraphs[Math.floor(FILLER.length / 2)];
    const sentences = w.request.split(/(?<=[.!?])\s+(?=[A-Z"'])/);
    const words = long.split(/\s+/).length;
    if (long.split(ask).length !== 2 || !middle.includes(ask) || sentences.some(s => long.split(s).length !== 2 || middle.includes(s)) || words < 2200 || words > 2600) { layout_ok = false; detail += `${w.id} `; }
    if (T.message(w, 'short', embedded) !== `${w.request} ${ask}`) { layout_ok = false; detail += `${w.id}(short) `; }
  }
  expect_that('each long message holds the request and the question once, the question alone in the middle', layout_ok, detail);

  const world = WORLDS.find(w => w.id === 'reminder-app');
  const { embedded } = T.embedded_question(world);
  const plain = T.read_situation({ events: ['snooze', 'snooze', 'day passes'] });
  const with_default = T.read_situation({ start: { task: 'new', snoozes: '0' }, events: ['snooze', 'snooze', 'day passes'] });
  const other = T.read_situation({ events: ['snooze', 'day passes'] });
  expect_that('the embedded question here is "snooze, snooze, a day passes"', T.canonical(world, embedded.situation) === T.canonical(world, plain));
  expect_that('"found" accepts the default start written out', T.canonical(world, with_default) === T.canonical(world, plain));
  expect_that('"found" refuses a different situation', T.canonical(world, other) !== T.canonical(world, plain));
  const g1 = T.grade_final(world, embedded, final_for(embedded));
  const g2 = T.grade_final(world, embedded, Object.assign(final_for(embedded), { answer: { task: 'done' } }));
  const g3 = T.grade_final(world, embedded, null);
  expect_that('a right answer to the right situation is found and right', g1.found && g1.answer_right && g1.found_and_right);
  expect_that('a wrong answer to the right situation is found but not right', g2.found && !g2.answer_right);
  expect_that('no answer at all is neither', !g3.found && !g3.answer_right);

  const text = T.message(world, 'long', embedded);
  let turn = 0;
  const two_then_stop = stand_in(world, () => { turn++; return turn <= 2 ? JSON.stringify({ ask: { events: turn === 1 ? ['snooze'] : ['explode'] } }) : JSON.stringify(final_for(embedded)); });
  const r1 = await T.ask_or_stop(two_then_stop, world, text, embedded);
  expect_that('ask or stop: two questions, one the owner can answer, then a right answer', r1.asks === 2 && r1.answers.length === 1 && r1.unusable === 1 && r1.grade.found_and_right, JSON.stringify({ asks: r1.asks, answers: r1.answers.length, unusable: r1.unusable }));
  const r2 = await T.ask_or_stop(stand_in(world), world, text, embedded);
  expect_that('ask or stop: stopping at once asks nothing', r2.asks === 0 && r2.grade.found_and_right);
  let told_to_stop = false;
  const never = stand_in(world, messages => { if (messages[messages.length - 1].content.includes('last question')) { told_to_stop = true; return JSON.stringify(final_for(embedded)); } return JSON.stringify({ ask: { events: ['snooze'] } }); });
  const r3 = await T.ask_or_stop(never, world, text, embedded);
  expect_that('ask or stop: never stopping is held to 12 questions, then told to answer', r3.asks === 12 && told_to_stop && r3.final);
  let t4 = 0;
  const r4 = await T.ask_or_stop(stand_in(world, () => (++t4 === 1 ? 'I think I will ask about...' : JSON.stringify(final_for(embedded)))), world, text, embedded);
  expect_that('ask or stop: a reply that is not JSON is counted and the turn goes on', r4.unreadable === 1 && r4.final);

  const rec = await T.run_world(world, 1, stand_in(world));
  const arm_names = ['short', 'long'].flatMap(l => ['answer straight away', 'random questions, then answer', 'ask or stop', 'guesser fixes first'].map(a => `${l}: ${a}`));
  expect_that('a whole world runs through all eight arms', arm_names.every(n => rec.arms[n]), Object.keys(rec.arms).join(', '));
  expect_that('with answers from the true model every arm answers the embedded question right', arm_names.every(n => rec.arms[n].grade.answer_right));
  expect_that('random questions give 6 answers', rec.arms['long: random questions, then answer'].answers_given === 6);
  expect_that('the summary has a row per arm', T.summarise([rec]).split('\n\n')[0].split('\n').length === 2 + arm_names.length);

  console.log(`\n${failed} test(s) failed.`);
  process.exit(failed ? 1 : 0);
})();
