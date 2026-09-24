/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Tests "30 system prompt questions.js" without calling DeepSeek. A stand-in plays DeepSeek, asks a
 * scripted run of questions and records every message it is sent. Checks:
 *   - the arm's text is at the very top of the standing instructions, and the rest is unchanged
 *   - with nothing at the top, the standing instructions are exactly log 21's
 *   - exactly ten questions are asked before the answer
 *   - the range counts: different situations, repeats, things started differently, events used
 *   - the summary has a row per arm and counts overlap with "nothing at the top"
 *   - the round-one arms are fixed: seven arms, "nothing at the top" twice among them
 *   - round two repeats two round-one texts word for word
 * Run with:  node "30 system prompt tests.js"
 */
const T = require('./21 long texts.js');
const S = require('./30 system prompt questions.js');
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
  const systems = [];
  const script = [
    { ask: { events: ['snooze'] }, i_expect: { task: 'urgent' } },
    { ask: { events: ['snooze'] }, i_expect: { task: 'new' } },
    { ask: { events: ['snooze', 'day passes'] }, i_expect: { task: 'new' } },
  ];
  return {
    systems, MODEL_NAME: 'stand-in',
    make_deepseek_guesser() {
      const g = async messages => {
        const last = messages[messages.length - 1].content;
        systems.push(messages[0].content);
        g.counts.tokens_out += 3;
        if (last.includes('Questions:\nQ1')) return JSON.stringify(Object.fromEntries(tests.map(q => [q.id, answer_of(q)])));
        if (last.includes('exactly 10 questions') || /more question|of 10 asked/.test(last)) return JSON.stringify(script[asks++] || { ask: { events: ['finish'] }, i_expect: { task: 'done' } });
        return JSON.stringify({ owner_asked: 'x', situation: embedded.situation, answer: answer_of(embedded) });
      };
      g.counts = { tokens_out: 0, cut_off: 0 };
      return g;
    },
  };
}

(async () => {
  expect_that('round one has seven arms, fixed, including "nothing at the top" twice', Object.keys(S.ROUND_ONE).length === 7 && S.ROUND_ONE['nothing at the top'] === null && S.ROUND_ONE['nothing at the top, again'] === null);

  expect_that('round two repeats doubt and filler word for word', S.ROUND_TWO['doubt, again'] === S.ROUND_ONE.doubt && S.ROUND_TWO['filler, again'] === S.ROUND_ONE.filler && Object.keys(S.ROUND_TWO).length === 5);

  const s1 = stand_in();
  const doubt = await S.run_arm(world, 'doubt', S.ROUND_ONE.doubt, s1);
  expect_that('the arm\'s text is at the very top, and log 21\'s instructions follow unchanged', s1.systems[0] === `${S.ROUND_ONE.doubt}\n\n${T.SYSTEM}`, s1.systems[0]);
  expect_that('exactly ten questions are asked', doubt.asked.length === 10, doubt.asked.length);

  const s2 = stand_in();
  const plain = await S.run_arm(world, 'nothing at the top', null, s2);
  expect_that('with nothing at the top, the instructions are exactly log 21\'s', s2.systems[0] === T.SYSTEM);
  const r = plain.range;
  // The script asks "snooze" twice, then "snooze, day passes", then "finish" seven times: 3 different, 7 repeats.
  expect_that('range: 10 questions, 3 different situations, 7 repeats', r.questions === 10 && r.different_situations === 3 && r.repeats === 7, JSON.stringify(r));
  expect_that('range: events used are counted once each', r.events_used === 3, r.events_used);
  expect_that('range: the first answer surprised it', r.surprised >= 1 && r.comparable >= 2, JSON.stringify(r));

  const text = S.summarise([plain, doubt]);
  expect_that('the summary has a row for each arm', text.includes('| nothing at the top | 1 |') && text.includes('| doubt | 1 |'));
  expect_that('overlap with "nothing at the top" is counted (the same script, so all 3)', /\| doubt \| 1 \|[^\n]*\| 3 \| \d\/1 \|/.test(text), text.split('\n').find(l => l.startsWith('| doubt')));

  console.log(`\n${failed} test(s) failed.`);
  process.exit(failed ? 1 : 0);
})();
