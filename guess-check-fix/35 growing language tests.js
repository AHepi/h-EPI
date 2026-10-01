/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Tests "35 growing language.js" without calling DeepSeek. Checks:
 *   - the devices follow the plan: the peg tube's observations include cases separate counts gets wrong,
 *     its long cases end as the plan lists, the gate has its two deeper cases
 *   - a model with a new kind reads cleanly, and unknown names are reported
 *   - a right growing-language model of each device gets every test case right, 1,000 actions included;
 *     a separate-counts model fails the observations it should
 *   - the separate process: an expression that never stops is cut off, one that tries to reach the account
 *     key cannot, and a model that never settles is reported
 *   - the arm reports a model's problems, then keeps and grades a right model
 *   - a whole device runs through all three arms, and the summary has a row for each
 *   - the probes after the run list each arm's answer beside the truth
 * Run with:  node "35 growing language tests.js"
 */
const G = require('./35 growing language.js');

let failed = 0;
function expect_that(name, ok, detail) {
  if (!ok) failed++;
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${name}${ok || !detail ? '' : `\n     ${detail}`}`);
}

const GATE_MODEL = {
  things: { gate: ['open', 'shut'] }, events: ['push', 'pull'], start: { gate: 'open' },
  kinds: { number: { start: 0, changes: { 'add one': 'value + 1', 'take one': 'value - 1' }, tests: { zero: 'value === 0' } } },
  new_things: { balance: 'number' },
  rules: [
    { name: 'push', when: ['push happens'], then: 'balance does add one' },
    { name: 'pull', when: ['pull happens'], then: 'balance does take one' },
    { name: 'open', when: ['balance is zero'], then: 'gate is open' },
    { name: 'shut', when: ['balance is not zero'], then: 'gate is shut' },
  ],
};
const PEG_MODEL = {
  things: { light: ['green', 'amber', 'red'], tube: ['working', 'jammed'] },
  events: ['red in', 'blue in', 'red out', 'blue out'], start: { light: 'green', tube: 'working' },
  kinds: { pile: { start: [], changes: { 'add red': 'value.concat(["red"])', 'add blue': 'value.concat(["blue"])', 'remove top': 'value.slice(0, -1)' },
    tests: { empty: 'value.length === 0', 'red on top': 'value[value.length - 1] === "red"', 'blue on top': 'value[value.length - 1] === "blue"' } } },
  new_things: { pegs: 'pile' },
  rules: [
    { name: 'red in', when: ['red in happens', 'tube is working'], then: 'pegs does add red' },
    { name: 'blue in', when: ['blue in happens', 'tube is working'], then: 'pegs does add blue' },
    { name: 'red out', when: ['red out happens', 'tube is working', 'pegs is red on top'], then: 'pegs does remove top' },
    { name: 'blue out', when: ['blue out happens', 'tube is working', 'pegs is blue on top'], then: 'pegs does remove top' },
    { name: 'red out jams', when: ['red out happens', 'pegs is not red on top'], then: 'tube is jammed' },
    { name: 'blue out jams', when: ['blue out happens', 'pegs is not blue on top'], then: 'tube is jammed' },
    { name: 'jammed shows red', when: ['tube is jammed'], then: 'light is red' },
    { name: 'empty shows green', when: ['tube is working', 'pegs is empty'], then: 'light is green' },
    { name: 'full shows amber', when: ['tube is working', 'pegs is not empty'], then: 'light is amber' },
  ],
};
const COUNTS_MODEL = {
  things: { light: ['green', 'amber', 'red'], tube: ['working', 'jammed'] },
  events: ['red in', 'blue in', 'red out', 'blue out'], start: { light: 'green', tube: 'working' },
  kinds: { number: { start: 0, changes: { up: 'value + 1', down: 'value - 1' }, tests: { none: 'value === 0' } } },
  new_things: { reds: 'number', blues: 'number' },
  rules: [
    { name: 'r in', when: ['red in happens', 'tube is working'], then: 'reds does up' },
    { name: 'b in', when: ['blue in happens', 'tube is working'], then: 'blues does up' },
    { name: 'r out', when: ['red out happens', 'tube is working', 'reds is not none'], then: 'reds does down' },
    { name: 'b out', when: ['blue out happens', 'tube is working', 'blues is not none'], then: 'blues does down' },
    { name: 'r jam', when: ['red out happens', 'reds is none'], then: 'tube is jammed' },
    { name: 'b jam', when: ['blue out happens', 'blues is none'], then: 'tube is jammed' },
    { name: 'red light', when: ['tube is jammed'], then: 'light is red' },
    { name: 'green light', when: ['tube is working', 'reds is none', 'blues is none'], then: 'light is green' },
    { name: 'amber red', when: ['tube is working', 'reds is not none'], then: 'light is amber' },
    { name: 'amber blue', when: ['tube is working', 'blues is not none'], then: 'light is amber' },
  ],
};

function stand_in(device) {
  let growing_calls = 0;
  const thing = Object.keys(device.visible)[0];
  return {
    MODEL_NAME: 'stand-in', asked: [],
    make_deepseek_guesser() {
      const self = this;
      const g = async messages => {
        g.counts.tokens_out += 5; self.asked.push(messages);
        const system = messages[0].role === 'system' ? messages[0].content : '';
        if (system.includes('You may also add new kinds of thing')) {
          growing_calls++;
          if (growing_calls === 1) return JSON.stringify(Object.assign({}, GATE_MODEL, { rules: GATE_MODEL.rules.concat([{ name: 'bad', when: ['balance is odd'], then: 'gate is shut' }]) }));
          return JSON.stringify(device.id === 'peg tube' ? PEG_MODEL : GATE_MODEL);
        }
        if (system.startsWith('You build small models')) return JSON.stringify({ things: device.visible, events: device.actions, start: {}, rules: [] });
        if (system.startsWith('You write small JavaScript')) return '```javascript\nfunction visible(a) { return { ' + JSON.stringify(thing) + ': ' + JSON.stringify(device.visible[thing][0]) + ' }; }\n```';
        return '{}';
      };
      g.counts = { tokens_out: 0, cut_off: 0 };
      return g;
    },
  };
}

(async () => {
  const gate = G.cases(G.GATE), pegs = G.cases(G.PEGS), grudge = G.cases(G.GRUDGE);
  expect_that('peg tube: 24 observations, 8 for each light, 4 that separate counts gets wrong', pegs.observations.length === 24 && ['green', 'amber', 'red'].every(s => pegs.observations.filter(o => o.see.light === s).length === 8) && pegs.observations.filter(o => o.rival_wrong).length === 4);
  expect_that('peg tube: 6 short tests, at least one separate counts gets wrong', pegs.tests.filter(t => !t.long).length === 6 && pegs.tests.some(t => !t.long && t.rival_wrong));
  expect_that('peg tube long tests end as the plan lists', pegs.tests.filter(t => t.long).map(t => t.see.light).join() === 'green,amber,red,green,green,red,red,green,green,red,red,red,red');
  expect_that('peg tube: the last three long tests are ones separate counts gets wrong', pegs.tests.filter(t => t.long).slice(-3).every(t => t.rival_wrong));
  expect_that('balance gate: log 34\'s 12 tests plus 500 and 500 (open), 500 and 499 (shut)', gate.tests.length === 14 && gate.tests[12].events.length === 1000 && gate.tests[12].see.gate === 'open' && gate.tests[13].see.gate === 'shut');
  expect_that('grudge: log 25\'s cases', grudge.observations.length === 14 && grudge.tests.length === 12);

  expect_that('a model with a new kind reads cleanly', G.read_growing_model(GATE_MODEL).problems.length === 0);
  const bad = G.read_growing_model(Object.assign({}, GATE_MODEL, { rules: [{ name: 'x', when: ['balance is odd'], then: 'balance does double' }], new_things: { balance: 'number', other: 'missing' } }));
  expect_that('unknown tests, changes and kinds are reported', ['"odd" is not a test', '"double" is not a change', 'which is not defined'].every(p => bad.problems.some(q => q.includes(p))), bad.problems.join(' | '));

  const gate_right = G.check_growing(G.GATE, GATE_MODEL, gate.observations.concat(gate.tests));
  expect_that('the right gate model gets every observation and test right, 1,000 actions included', gate_right.results.every(r => r.right), JSON.stringify(gate_right.results.filter(r => !r.right)));
  const peg_right = G.check_growing(G.PEGS, PEG_MODEL, pegs.observations.concat(pegs.tests));
  expect_that('the right peg model (a pile) gets every observation and test right', peg_right.results.every(r => r.right), JSON.stringify(peg_right.results.filter(r => !r.right).slice(0, 3)));
  const counts = G.check_growing(G.PEGS, COUNTS_MODEL, pegs.observations);
  expect_that('a separate-counts model fails exactly the 4 observations it should', counts.results.filter(r => !r.right).length === 4, JSON.stringify(counts.results.filter(r => !r.right)));

  const forever = G.check_growing(G.GATE, Object.assign({}, GATE_MODEL, { kinds: { number: { start: 0, changes: { 'add one': '(() => { while (true) {} })()', 'take one': 'value - 1' }, tests: { zero: 'value === 0' } } } }), gate.observations.slice(0, 3));
  expect_that('an expression that never stops is cut off and reported', forever.results.every(r => !r.right && /timed out|did not finish/i.test(r.problem || '')), JSON.stringify(forever.results[0]));
  process.env.SECRET_FOR_THIS_TEST = 'do-not-leak-3535';
  const escape = G.run_growing(G.read_growing_model(Object.assign({}, GATE_MODEL, { things: { gate: ['open', 'shut'], seen: ['nothing'] }, kinds: { number: { start: 0, changes: { 'add one': 'this.constructor.constructor("return process")().env.SECRET_FOR_THIS_TEST', 'take one': 'value - 1' }, tests: { zero: 'value === 0' } } } })).model, [['push']]);
  expect_that('an expression cannot reach the account key or other settings', !JSON.stringify(escape).includes('do-not-leak-3535'), JSON.stringify(escape));
  // A rule with no conditions fires on every step, so the count never stops changing.
  const restless = G.check_growing(G.GATE, Object.assign({}, GATE_MODEL, { rules: GATE_MODEL.rules.concat([{ name: 'keeps counting', when: [], then: 'balance does add one' }]) }), gate.observations.slice(0, 2));
  expect_that('a model that never settles is reported', restless.results.every(r => !r.right && /never settles/.test(r.problem || '')), JSON.stringify(restless.results[0]));

  const s = stand_in(G.GATE);
  const arm = await G.growing_language(s, G.GATE, gate.observations, gate.tests);
  const second = s.asked.filter(m => m[0].content.includes('You may also add new kinds of thing'))[1][1].content;
  expect_that('the arm reports a model\'s problems to DeepSeek', second.includes('The checker could not run it') && second.includes('"odd" is not a test'), second.slice(-300));
  expect_that('the arm keeps the right model, and it gets every test right', arm.best_round === 2 && arm.graded.every(g => g.right) && arm.shape.kinds === 1 && arm.shape.rules === 4);
  expect_that('the growth guide keeps the rule language\'s guide and ends by asking for JSON', G.GROWTH_GUIDE.startsWith('You build small models') && G.GROWTH_GUIDE.trim().endsWith('Reply with the model as JSON only.') && (G.GROWTH_GUIDE.match(/Reply with the model as JSON only/g) || []).length === 1);

  const rec = await G.run_device(G.PEGS, 1, stand_in(G.PEGS));
  expect_that('a whole device runs through all three arms', ['fixed language', 'growing language', 'universal language'].every(a => rec.arms[a]));
  expect_that('each graded test is marked with whether separate counts gets it wrong (1 short, 4 long)', rec.arms['growing language'].graded.filter(g => g.rival_wrong).length === 5);
  const text = G.summarise([rec]);
  expect_that('the summary has a row for each arm and lists the growing model\'s shape', ['| peg tube | fixed language |', '| peg tube | growing language |', '| peg tube | universal language |', 'peg tube repeat 1: 1 kinds, 1 new things, 9 rules'].every(r => text.includes(r)), text);

  const probed = G.probe_after_run([{ device: 'balance gate', repeat: 1, arms: { 'fixed language': { best_round: null, rounds: [] }, 'growing language': { best_round: 1, rounds: [{ round: 1, model: GATE_MODEL }] }, 'universal language': { best_round: null, rounds: [] } } }]);
  expect_that('the probes after the run list each arm beside the truth', probed[0].probes.length === 4 && probed[0].probes[0].truth === 'shut' && probed[0].probes.every(p => p.growing_language === p.truth) && probed[0].probes[0].fixed_language === 'no model', JSON.stringify(probed[0].probes[0]));

  console.log(`\n${failed} test(s) failed.`);
  process.exit(failed ? 1 : 0);
})();
