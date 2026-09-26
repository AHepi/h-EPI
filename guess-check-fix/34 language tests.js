/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Tests "34 language test.js" without calling DeepSeek. Checks:
 *   - the devices follow the plan: balanced observations, the obvious reading refuted, the long test
 *     cases' endings as the plan lists them, and how deep each long case's hidden count or pile goes
 *   - a rule model that counts only to 6 fits every balance-gate observation but gets long cases wrong:
 *     the fixed language can only approximate
 *   - DeepSeek's functions run in a separate process: a function that never stops is cut off, and a
 *     function that tries to reach the account key or load a library cannot
 *   - the universal-language loop reports which observations fail and how, and keeps the best function
 *   - a whole device runs through all three arms, and the summary has a row for each
 * Run with:  node "34 language tests.js"
 */
const X = require('./34 language test.js');

let failed = 0;
function expect_that(name, ok, detail) {
  if (!ok) failed++;
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${name}${ok || !detail ? '' : `\n     ${detail}`}`);
}

// A rule model of the balance gate that counts from -6 to 6: enough for the observations, not for long cases.
function counting_model(limit) {
  const values = []; for (let v = -limit; v <= limit; v++) values.push(String(v));
  const rules = [];
  for (let v = -limit; v <= limit; v++) {
    if (v < limit) rules.push({ name: `push from ${v}`, when: ['push happens', `count is ${v}`], then: `count is ${v + 1}` });
    if (v > -limit) rules.push({ name: `pull from ${v}`, when: ['pull happens', `count is ${v}`], then: `count is ${v - 1}` });
  }
  rules.push({ name: 'open at zero', when: ['count is 0'], then: 'gate is open' }, { name: 'shut otherwise', when: ['count is not 0'], then: 'gate is shut' });
  return { things: { gate: ['open', 'shut'], count: values }, events: ['push', 'pull'], start: { gate: 'open', count: '0' }, rules };
}
const RIGHT_GATE = 'function visible(actions) { let d = 0; for (const a of actions) d += a === "push" ? 1 : -1; return { gate: d === 0 ? "open" : "shut" }; }';

function stand_in(device) {
  let program_calls = 0;
  const thing = Object.keys(device.visible)[0];
  return {
    MODEL_NAME: 'stand-in', asked: [],
    make_deepseek_guesser() {
      const self = this;
      const g = async messages => {
        g.counts.tokens_out += 5;
        self.asked.push(messages);
        const system = messages[0].role === 'system' ? messages[0].content : '';
        if (system.startsWith('You build small models')) return JSON.stringify(device.id === 'balance gate' ? counting_model(6) : { things: device.visible, events: device.actions, start: {}, rules: [] });
        if (system.startsWith('You write small JavaScript')) {
          program_calls++;
          const code = device.id === 'balance gate' && program_calls > 1 ? RIGHT_GATE : `function visible(actions) { return { ${JSON.stringify(thing)}: ${JSON.stringify(device.visible[thing][0])} }; }`;
          return 'Here it is.\n```javascript\n' + code + '\n```';
        }
        const { tests } = X.cases(device);
        return JSON.stringify({ rule: 'x', answers: Object.fromEntries(tests.map((t, i) => [`T${i + 1}`, t.see[thing]])) });
      };
      g.counts = { tokens_out: 0, cut_off: 0 };
      return g;
    },
  };
}

(async () => {
  // The devices follow the plan.
  const gate = X.cases(X.GATE), pegs = X.cases(X.PEGS), grudge = X.cases(X.GRUDGE);
  expect_that('balance gate: 20 observations, 10 open and 10 shut', gate.observations.length === 20 && gate.observations.filter(o => o.see.gate === 'open').length === 10);
  expect_that('peg tube: 24 observations, 8 for each light', pegs.observations.length === 24 && ['green', 'amber', 'red'].every(s => pegs.observations.filter(o => o.see.light === s).length === 8));
  expect_that('grudge: log 25\'s 14 observations and 12 tests', grudge.observations.length === 14 && grudge.tests.length === 12);
  expect_that('the observations refute the obvious reading on each device', [gate, pegs, grudge].every(c => c.observations.some(o => o.hard)));
  expect_that('balance gate long tests end as the plan lists: open, shut, open, open, open, shut', gate.tests.filter(t => t.long).map(t => t.see.gate).join() === 'open,shut,open,open,open,shut');
  expect_that('peg tube long tests end as the plan lists: green, amber, red, green, green, red', pegs.tests.filter(t => t.long).map(t => t.see.light).join() === 'green,amber,red,green,green,red');
  const deepest_count = events => { let d = 0, m = 0; for (const e of events) { d += e === 'push' ? 1 : -1; m = Math.max(m, Math.abs(d)); } return m; };
  const deepest_pile = events => { let d = 0, m = 0; for (const e of events) { d += e.endsWith(' in') ? 1 : -1; m = Math.max(m, d); } return m; };
  // The plan first said every long test goes deeper than 10; two do not (corrected in the plan before any run).
  expect_that('long tests go this deep: balance gate 30, 30, 20, 1, 25, 40; peg tube 12, 12, 12, 15, 10, 12', gate.tests.filter(t => t.long).map(t => deepest_count(t.events)).join() === '30,30,20,1,25,40' && pegs.tests.filter(t => t.long).map(t => deepest_pile(t.events)).join() === '12,12,12,15,10,12');
  expect_that('no test case is also an observation', [gate, pegs].every(c => c.tests.every(t => !c.observations.some(o => o.events.join('>') === t.events.join('>')))));

  // The fixed language can only approximate.
  const C = require('./03 checker.js');
  const model = C.prepare_model(counting_model(6));
  const jobs = C.prepare_jobs({ jobs: gate.observations.map(o => ({ name: o.name, events: o.events, expect: [`gate is ${o.see.gate}`] })) }).jobs;
  expect_that('a rule model counting to 6 fits every balance-gate observation', C.check(model, jobs).failed.length === 0, C.check(model, jobs).failed.join(', '));

  // The separate process.
  const loop = X.check_program(X.GATE, 'function visible(a) { while (true) {} }', gate.observations.slice(0, 2));
  expect_that('a function that never stops is cut off and reported', loop.every(c => !c.right && /timed out|did not finish/i.test(c.problem)), JSON.stringify(loop[0]));
  process.env.SECRET_FOR_THIS_TEST = 'do-not-leak-4471';
  const escape = X.run_program('function visible(a) { const p = this.constructor.constructor("return process")(); return { gate: String(p.env.SECRET_FOR_THIS_TEST) + "|" + typeof require }; }', [['push']]);
  expect_that('a function cannot reach the account key or other settings', escape.results && !JSON.stringify(escape).includes('do-not-leak-4471'), JSON.stringify(escape));
  expect_that('a function cannot load a library', escape.results && JSON.stringify(escape).includes('undefined|undefined'), JSON.stringify(escape));
  const right = X.check_program(X.GATE, RIGHT_GATE, gate.tests);
  expect_that('the right function gets every balance-gate test right, long ones included', right.every(c => c.right), JSON.stringify(right.filter(c => !c.right)));
  expect_that('a reply\'s function is read from its code block', X.read_program('text\n```javascript\n' + RIGHT_GATE + '\n```\nmore') === RIGHT_GATE);

  // The arms, with the stand-in.
  const s = stand_in(X.GATE);
  const fixed = await X.fixed_language(s, X.GATE, gate.observations, gate.tests);
  expect_that('fixed language: the counting-to-6 model fits every observation in one round', fixed.best_passes === 20 && fixed.calls === 1 && fixed.largest_hidden === 13);
  expect_that('fixed language: it gets long test cases wrong', fixed.graded.filter(g => g.long && !g.right).length >= 3, JSON.stringify(fixed.graded.filter(g => g.long)));
  const universal = await X.universal_language(s, X.GATE, gate.observations, gate.tests);
  const second_ask = s.asked.filter(m => m[0].content.startsWith('You write small JavaScript'))[1][1].content;
  expect_that('universal language: the report says which observations fail and what the function gave', /10 of 20 hold/.test(second_ask) && /Observed: gate is shut\. Your function: gate is open\./.test(second_ask), second_ask.slice(-400));
  expect_that('universal language: the right function is kept and gets every test right', universal.best_round === 2 && universal.graded.every(g => g.right));
  expect_that('every arm is told tests may be of any length', s.asked.every(m => m[m.length - 1].content.includes(X.ANY_LENGTH)));

  const rec = await X.run_device(X.PEGS, 1, stand_in(X.PEGS));
  expect_that('a whole device runs through all three arms', ['fixed language', 'universal language', 'bare'].every(a => rec.arms[a]));
  expect_that('bare answers are graded', rec.arms.bare.graded.every(g => g.right));
  const text = X.summarise([rec]);
  expect_that('the summary has a row for each arm', ['| peg tube | fixed language |', '| peg tube | universal language |', '| peg tube | bare |'].every(r => text.includes(r)));

  console.log(`\n${failed} test(s) failed.`);
  process.exit(failed ? 1 : 0);
})();
