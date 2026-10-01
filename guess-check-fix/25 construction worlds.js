/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Four made-up devices for log 25, each with a rule DeepSeek cannot know from its training and that runs
 * against the obvious reading. In each, the right explanation needs a hidden thing nobody mentions: a
 * count, a switch, a grudge, a charge. That is what the semantics calls construction (Part IV,
 * Derivation 10): no re-tuning of the obvious explanation can succeed; a new part has to be built.
 *
 * Each device has:
 *   request     - a plain description: what can be seen and what can be done. No hint of the hidden thing.
 *   world       - the hidden true model (with its hidden thing).
 *   visible     - the things that can be seen; only these are ever reported or asked about.
 *   obvious     - the explanation the description suggests. A test checks the observations refute it.
 * observations_and_tests(device) lists every sequence of up to four actions from the start, runs it on
 * the true model, and puts them in a fixed shuffle. The first 14 are the observations (shown to everyone).
 * From the rest come 12 test cases (shown to no one): 8 where the obvious explanation is wrong, which only
 * an explanation with the hidden thing gets right, and 4 where it is right, which catch an explanation
 * that has gone too far. Test cases are never longer than the observations.
 */
const C = require('./03 checker.js');

const DEVICES = [
  {
    id: 'grudge',
    kind: 'a person\'s feelings',
    request: 'Robin is a neighbour. You can insult Robin, apologise to Robin, or give Robin a gift. All you can see is whether Robin is warm or cold towards you.',
    visible: ['mood'],
    world: {
      things: { mood: ['warm', 'cold'], grudge: ['none', 'hurt', 'deep'] },
      events: ['insult', 'apologise', 'gift'],
      start: { mood: 'warm', grudge: 'none' },
      rules: [
        { name: 'first insult hurts', when: ['insult happens', 'grudge is none'], then: 'grudge is hurt' },
        { name: 'second insult goes deep', when: ['insult happens', 'grudge is hurt'], then: 'grudge is deep' },
        { name: 'an apology mends a hurt', when: ['apologise happens', 'grudge is hurt'], then: 'grudge is none' },
        { name: 'a gift softens a deep grudge', when: ['gift happens', 'grudge is deep'], then: 'grudge is hurt' },
        { name: 'warm without a grudge', when: ['grudge is none'], then: 'mood is warm' },
        { name: 'cold when hurt', when: ['grudge is hurt'], then: 'mood is cold' },
        { name: 'cold when deep', when: ['grudge is deep'], then: 'mood is cold' },
      ],
    },
    obvious: {
      things: { mood: ['warm', 'cold'] }, events: ['insult', 'apologise', 'gift'], start: { mood: 'warm' },
      rules: [{ name: 'insult', when: ['insult happens'], then: 'mood is cold' }, { name: 'apology', when: ['apologise happens'], then: 'mood is warm' }, { name: 'gift', when: ['gift happens'], then: 'mood is warm' }],
    },
  },
  {
    id: 'magnet-ball',
    kind: 'physical cause and effect',
    request: 'A steel ball sits in a long tray with three places: left, middle and right. You can tilt the tray left, tilt it right, or shake it. All you can see is where the ball is.',
    visible: ['ball'],
    world: {
      things: { ball: ['left', 'middle', 'right'], magnet: ['off', 'on'] },
      events: ['tilt left', 'tilt right', 'shake'],
      start: { ball: 'middle', magnet: 'off' },
      rules: [
        { name: 'shaking turns the magnet on', when: ['shake happens', 'magnet is off'], then: 'magnet is on' },
        { name: 'shaking turns the magnet off', when: ['shake happens', 'magnet is on'], then: 'magnet is off' },
        { name: 'rolls left from the middle', when: ['tilt left happens', 'magnet is off', 'ball is middle'], then: 'ball is left' },
        { name: 'rolls left from the right', when: ['tilt left happens', 'magnet is off', 'ball is right'], then: 'ball is middle' },
        { name: 'rolls right from the middle', when: ['tilt right happens', 'magnet is off', 'ball is middle'], then: 'ball is right' },
        { name: 'rolls right from the left', when: ['tilt right happens', 'magnet is off', 'ball is left'], then: 'ball is middle' },
        { name: 'pushed right from the middle', when: ['tilt left happens', 'magnet is on', 'ball is middle'], then: 'ball is right' },
        { name: 'pushed right from the left', when: ['tilt left happens', 'magnet is on', 'ball is left'], then: 'ball is middle' },
        { name: 'pushed left from the middle', when: ['tilt right happens', 'magnet is on', 'ball is middle'], then: 'ball is left' },
        { name: 'pushed left from the right', when: ['tilt right happens', 'magnet is on', 'ball is right'], then: 'ball is middle' },
      ],
    },
    obvious: {
      things: { ball: ['left', 'middle', 'right'] }, events: ['tilt left', 'tilt right', 'shake'], start: { ball: 'middle' },
      rules: [
        { name: 'l1', when: ['tilt left happens', 'ball is middle'], then: 'ball is left' }, { name: 'l2', when: ['tilt left happens', 'ball is right'], then: 'ball is middle' },
        { name: 'r1', when: ['tilt right happens', 'ball is middle'], then: 'ball is right' }, { name: 'r2', when: ['tilt right happens', 'ball is left'], then: 'ball is middle' },
      ],
    },
  },
  {
    id: 'gate',
    kind: 'a puzzle',
    request: 'A garden gate has a knocker and a bell. You can knock or ring. All you can see is whether the gate is open or shut.',
    visible: ['gate'],
    world: {
      things: { gate: ['shut', 'open'], knocks: ['even', 'odd'], rings: ['even', 'odd'] },
      events: ['knock', 'ring'],
      start: { gate: 'shut', knocks: 'even', rings: 'even' },
      rules: [
        { name: 'knock counts', when: ['knock happens', 'knocks is even'], then: 'knocks is odd' },
        { name: 'knock counts again', when: ['knock happens', 'knocks is odd'], then: 'knocks is even' },
        { name: 'ring counts', when: ['ring happens', 'rings is even'], then: 'rings is odd' },
        { name: 'ring counts again', when: ['ring happens', 'rings is odd'], then: 'rings is even' },
        { name: 'opens', when: ['knocks is odd', 'rings is even'], then: 'gate is open' },
        { name: 'shut after even knocks', when: ['knocks is even'], then: 'gate is shut' },
        { name: 'shut after odd rings', when: ['rings is odd'], then: 'gate is shut' },
      ],
    },
    obvious: {
      things: { gate: ['shut', 'open'] }, events: ['knock', 'ring'], start: { gate: 'shut' },
      rules: [{ name: 'knock opens', when: ['knock happens'], then: 'gate is open' }],
    },
  },
  {
    id: 'vial',
    kind: 'an unknown chemistry',
    request: 'A glass vial holds a clear liquid. You can add salt, add acid, or heat the vial. All you can see is the colour of the liquid: clear, green or purple.',
    visible: ['colour'],
    world: {
      things: { colour: ['clear', 'green', 'purple'], charge: ['0', '1', '2'] },
      events: ['add salt', 'add acid', 'heat'],
      start: { colour: 'clear', charge: '0' },
      rules: [
        { name: 'salt charges', when: ['add salt happens', 'charge is 0'], then: 'charge is 1' },
        { name: 'salt charges more', when: ['add salt happens', 'charge is 1'], then: 'charge is 2' },
        { name: 'acid discharges', when: ['add acid happens', 'charge is 2'], then: 'charge is 1' },
        { name: 'acid discharges more', when: ['add acid happens', 'charge is 1'], then: 'charge is 0' },
        { name: 'heat shows no charge', when: ['heat happens', 'charge is 0'], then: 'colour is clear' },
        { name: 'heat shows a little charge', when: ['heat happens', 'charge is 1'], then: 'colour is green' },
        { name: 'heat shows a full charge', when: ['heat happens', 'charge is 2'], then: 'colour is purple' },
      ],
    },
    obvious: {
      things: { colour: ['clear', 'green', 'purple'] }, events: ['add salt', 'add acid', 'heat'], start: { colour: 'clear' },
      rules: [{ name: 'salt', when: ['add salt happens'], then: 'colour is green' }, { name: 'acid', when: ['add acid happens'], then: 'colour is purple' }, { name: 'heat', when: ['heat happens'], then: 'colour is clear' }],
    },
  },
];

function stable_key(text) {
  let h = 2166136261;
  for (const ch of text) { h ^= ch.charCodeAt(0); h = Math.imul(h, 16777619) >>> 0; }
  return h;
}
function sequences(events, longest) {
  let level = [[]];
  const all = [];
  for (let n = 1; n <= longest; n++) { level = level.flatMap(s => events.map(e => s.concat(e))); all.push(...level); }
  return all;
}
// What the true model says the visible things end as, after a sequence.
function ending(device, events) {
  const model = C.prepare_model(device.world);
  const job = C.prepare_jobs({ jobs: [{ name: 'x', events, expect: [] }] }).jobs[0];
  const result = C.run(model, C.resolve_situation(model, job.situation, [], 'x'));
  return device.visible.map(t => `${t} is ${[...new Set(result.final_states.map(s => s[t]))].join('/')}`);
}
function obvious_is_right(device, events) {
  const model = C.prepare_model(device.obvious);
  const job = C.prepare_jobs({ jobs: [{ name: 'x', events, expect: ending(device, events) }] }).jobs[0];
  return C.check_job(model, job).passed;
}
function observations_and_tests(device) {
  const shuffled = sequences(device.world.events, 4).map(events => ({ events, key: stable_key(`${device.id}|${events.join('>')}`) })).sort((a, b) => a.key - b.key);
  const make = (list, prefix) => list.map((s, i) => ({ name: `${prefix} ${i + 1}`, events: s.events, expect: ending(device, s.events), obvious_right: obvious_is_right(device, s.events) }));
  const rest = shuffled.slice(14);
  const hard = rest.filter(s => !obvious_is_right(device, s.events)).slice(0, 8);
  const easy = rest.filter(s => obvious_is_right(device, s.events)).slice(0, 4);
  return { observations: make(shuffled.slice(0, 14), 'observation'), tests: make(hard.concat(easy), 'test') };
}

module.exports = { DEVICES, observations_and_tests, sequences, ending, obvious_is_right };
