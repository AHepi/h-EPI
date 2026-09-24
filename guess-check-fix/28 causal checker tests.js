/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Tests "28 causal checker.js" on small hand-written models. No AI is called. Checks:
 *   - the lamp and the curtains: seeing a dark room tells you the lamp is off; making the room dark
 *     (holding it dark) does not switch the lamp off
 *   - what if: holding a thing changes what is downstream of it, not what is upstream, and the route
 *     names the rules that carried the change
 *   - two pushes the opposite way on one thing leave it unsettled, not changed
 *   - the "influences" shorthand: "same" and "opposite", levels added, a thing without the three
 *     levels refused
 *   - why: a but-for cause is found; two causes, each enough on its own, are reported as such
 *   - corpus questions: more / less / no effect, including a question about "less" of something,
 *     and a change or effect not in the model
 *   - picking the corpus sample: the same every time, five paragraphs, at most ten per kind of question
 * Run with:  node "28 causal checker tests.js"
 */
const K = require('./28 causal checker.js');

let failed = 0;
function expect_that(name, ok, detail) {
  if (!ok) failed++;
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${name}${ok || !detail ? '' : `\n     ${detail}`}`);
}

// The lamp and the curtains. The lamp and the curtains are set from outside; the room follows them.
const room = K.prepare({
  things: { lamp: ['off', 'on'], curtains: ['open', 'closed'], daylight: ['day', 'night'], room: ['dark', 'lit'] },
  start: { lamp: 'off', curtains: 'open', daylight: 'day', room: 'lit' },
  rules: [
    { name: 'lamp lights the room', when: ['lamp is on'], then: 'room is lit' },
    { name: 'daylight lights the room', when: ['daylight is day', 'curtains is open'], then: 'room is lit' },
    { name: 'dark when lamp off and curtains closed', when: ['lamp is off', 'curtains is closed'], then: 'room is dark' },
    { name: 'dark at night with lamp off', when: ['lamp is off', 'daylight is night'], then: 'room is dark' },
  ],
});
expect_that('the room model reads without problems', room.problems.length === 0, room.problems.join(' '));
const sd = K.seeing_and_doing(room, 'room', 'dark', 'lamp');
expect_that('seeing a dark room: the lamp is off in every such run', sd.seeing_runs > 0 && Object.keys(sd.seeing).join() === 'off', JSON.stringify(sd));
expect_that('making the room dark: the lamp is still on in some runs', sd.doing.on > 0 && sd.differ, JSON.stringify(sd));

const lamp_on = K.what_if(room, { lamp: 'on' }, 'room', { start: { curtains: 'closed' } });
expect_that('what if the lamp is on (curtains closed): the room changes to lit', lamp_on.verdict === 'changed' && lamp_on.after === 'lit', JSON.stringify(lamp_on));
expect_that('the route names the rule that carried it', lamp_on.route.some(r => r.rule === 'lamp lights the room'), JSON.stringify(lamp_on.route));
const dark_room = K.what_if(room, { room: 'dark' }, 'lamp', { start: { lamp: 'on' } });
expect_that('what if the room is held dark: the lamp does not change', dark_room.verdict === 'no change' && dark_room.after === 'on', JSON.stringify(dark_room));

// A chain with influences: rain raises runoff, runoff raises erosion, plant cover lowers erosion.
const hill = K.prepare({
  influences: [
    { from: 'rain', to: 'runoff', sign: 'same' },
    { from: 'runoff', to: 'erosion', sign: 'same' },
    { from: 'plant cover', to: 'erosion', sign: 'opposite' },
  ],
});
expect_that('influences add the three levels and start at usual', hill.problems.length === 0 && hill.things.rain.join() === 'usual,more,less' && hill.start.erosion === 'usual', JSON.stringify(hill.problems));
const more_rain = K.what_if(hill, { rain: 'more' }, 'erosion');
expect_that('more rain: more erosion, through runoff', more_rain.verdict === 'changed' && more_rain.after === 'more' && more_rain.route.map(r => r.thing).join() === 'runoff,erosion', JSON.stringify(more_rain));
const more_cover = K.what_if(hill, { 'plant cover': 'more' }, 'erosion');
expect_that('more plant cover: less erosion ("opposite")', more_cover.after === 'less', JSON.stringify(more_cover));
const upstream = K.what_if(hill, { erosion: 'more' }, 'rain');
expect_that('holding erosion high does not change the rain', upstream.verdict === 'no change', JSON.stringify(upstream));
const both = K.what_if(hill, { rain: 'more', 'plant cover': 'more' }, 'erosion');
expect_that('more rain and more plant cover together: erosion is unsettled, not changed', both.verdict === 'unsettled', JSON.stringify(both));
const bad = K.prepare({ things: { rain: ['wet', 'dry'] }, influences: [{ from: 'rain', to: 'runoff', sign: 'same' }] });
expect_that('a thing in an influence without the three levels is refused', bad.problems.some(p => p.includes('"rain"')), JSON.stringify(bad.problems));
const bad_sign = K.prepare({ influences: [{ from: 'rain', to: 'runoff', sign: 'up' }] });
expect_that('a sign other than "same" or "opposite" is refused', bad_sign.problems.some(p => p.includes('"sign"')), JSON.stringify(bad_sign.problems));
expect_that('what if refuses an unreadable model', K.what_if(bad, { rain: 'wet' }, 'runoff').verdict === 'unreadable');

// Why. A match lights only with oxygen present and a strike; a strike is a but-for cause.
const fire = K.prepare({
  things: { oxygen: ['present', 'absent'], match: ['unlit', 'lit'], lawn: ['dry', 'wet'] },
  events: ['strike', 'rain', 'sprinkler'],
  start: { oxygen: 'present', match: 'unlit', lawn: 'dry' },
  rules: [
    { name: 'striking lights', when: ['strike happens', 'oxygen is present'], then: 'match is lit' },
    { name: 'rain wets', when: ['rain happens'], then: 'lawn is wet' },
    { name: 'sprinkler wets', when: ['sprinkler happens'], then: 'lawn is wet' },
  ],
});
const lit = K.why(fire, { events: ['strike'] }, 'match');
expect_that('why is the match lit: but for the strike, it would not be', lit.verdict === 'but-for causes found' && lit.but_for.length === 1 && lit.but_for[0].event === 'strike', JSON.stringify(lit));
expect_that('the oxygen is not listed: it was the usual start, not a difference', !lit.differences.some(d => d.thing === 'oxygen'));
const wet = K.why(fire, { events: [['rain', 'sprinkler']] }, 'lawn');
expect_that('rain and sprinkler together: no but-for cause, two causes each enough', wet.verdict === 'two causes, each enough' && wet.each_enough.length === 1, JSON.stringify(wet));
expect_that('a difference reads in plain words', K.describe_difference(lit.but_for[0]) === '"strike" happening');

// Corpus questions.
const ask = (change, effect) => K.answer_what_if_question(hill, { change, effect }).answer;
expect_that('"more rain, how will it affect more erosion?" is more', ask({ thing: 'rain', level: 'more' }, { thing: 'erosion', direction: 'more' }) === 'more');
expect_that('"more rain, how will it affect less erosion?" is less', ask({ thing: 'rain', level: 'more' }, { thing: 'erosion', direction: 'less' }) === 'less');
expect_that('"less rain, how will it affect less erosion?" is more', ask({ thing: 'rain', level: 'less' }, { thing: 'erosion', direction: 'less' }) === 'more');
expect_that('"more erosion, how will it affect more rain?" is no effect', ask({ thing: 'erosion', level: 'more' }, { thing: 'rain', direction: 'more' }) === 'no_effect');
expect_that('a change not in the model is no effect', ask(null, { thing: 'erosion', direction: 'more' }) === 'no_effect');
expect_that('an effect not in the model is no effect', ask({ thing: 'rain', level: 'more' }, null) === 'no_effect');
expect_that('a direction other than more or less is unreadable', ask({ thing: 'rain', level: 'more' }, { thing: 'erosion', direction: 'up' }) === 'unreadable');
expect_that('an unknown thing is unreadable', ask({ thing: 'snow', level: 'more' }, { thing: 'erosion', direction: 'more' }) === 'unreadable');
const both_ways = K.answer_what_if_question(K.prepare({ influences: [{ from: 'a', to: 'b', sign: 'same' }, { from: 'a', to: 'c', sign: 'same' }, { from: 'c', to: 'b', sign: 'opposite' }] }), { change: { thing: 'a', level: 'more' }, effect: { thing: 'b', direction: 'more' } });
expect_that('two routes pushing opposite ways are unsettled', both_ways.answer === 'unsettled', JSON.stringify(both_ways));

// Picking the corpus sample, on made-up rows.
const P = require('./28 causal corpus.js');
const kinds = Object.keys(P.KIND_NAMES);
const rows = [];
for (let para = 1; para <= 8; para++) for (const kind of kinds) for (let n = 0; n < 12; n++) {
  rows.push({ metadata: { para_id: String(para), ques_id: `${para}:${kind}:${n}`, question_type: kind }, question: { stem: 'x', para_steps: ['a'], answer_label: 'more' } });
}
const first = P.pick(rows), again = P.pick(rows.slice().reverse());
expect_that('the sample is the same whatever order the corpus is read in', JSON.stringify(first.picked.map(r => r.metadata.ques_id).sort()) === JSON.stringify(again.picked.map(r => r.metadata.ques_id).sort()));
expect_that('five paragraphs, ten questions of each kind in each', first.paragraph_ids.length === 5 && first.picked.length === 150);

console.log(`\n${failed} test(s) failed.`);
process.exit(failed ? 1 : 0);
