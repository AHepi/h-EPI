/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Tests "40 kept method at work.js" on one world, without any AI. Checks:
 *   - eight starts per world, each failing a shown job
 *   - candidates repair at least one failing job, most repaired first
 *   - a method that accepts nothing stops the loop at once with no damage and no repair
 *   - the current method accepts the first candidate each round
 *   - questions are counted only for fixes up to the one accepted
 *   - a method that fails stops the loop and is recorded as a failure
 *   - the summary has a row per method and counts losses of P1 against the current method
 * Run with:  node "40 kept method at work tests.js"
 */
const C = require('./03 checker.js');
const O = require('./39 occasions.js');
const M = require('./39 changing a method.js');
const W = require('./40 kept method at work.js');

let failed = 0;
function expect_that(name, ok, detail) {
  if (!ok) failed++;
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${name}${ok || !detail ? '' : `\n     ${detail}`}`);
}

const world = O.WORLDS.find(w => w.id === 'ball-and-wall');
const s = W.setting(world);
const starts = W.starts_of(s);
expect_that('eight starts, each failing a shown job', starts.length === 8 && starts.every(st => C.check(st.model, s.shown).failed.length > 0));
const list = W.candidates(s, starts[0].model);
expect_that('candidates each repair a failing job, most repaired first', list.length > 0 && list.every(x => x.c.repaired > 0) && list.every((x, i) => i === 0 || list[i - 1].c.repaired >= x.c.repaired));

const none = W.correct(s, starts[0], 'function accept_fix(c, ask) { return false; }');
expect_that('accepting nothing stops at once: no damage, no repair', none.stopped === 'the method accepted no change' && none.damage === 0 && !none.shown_all_pass && none.trail.length === 0, JSON.stringify(none));
const current = W.correct(s, starts[0], M.CURRENT);
expect_that('the current method accepts the first candidate each round', current.trail[0] === list[0].c.description && current.questions === 0, JSON.stringify(current.trail));
const asks_then_accepts = W.correct(s, starts[0], 'function accept_fix(c, ask) { ask(0); return true; }');
expect_that('questions count only up to the accepted fix: one per round here', asks_then_accepts.questions === asks_then_accepts.rounds, JSON.stringify({ q: asks_then_accepts.questions, r: asks_then_accepts.rounds }));
const broken = W.correct(s, starts[0], 'function accept_fix(c, ask) { throw new Error("broken"); }');
expect_that('a method that fails stops the loop and is recorded', broken.stopped === 'the method failed' && /broken/.test(broken.error));

const rows = [{ world: world.id, held_out: true, start: starts[0].description, methods: { 'current method': current, 'accept nothing': none } }];
const text = W.summarise(rows);
expect_that('the summary has a row per method and counts P1 losses against the current method', text.includes('| current method |') && new RegExp(`\\| accept nothing \\| 0 \\| 0 \\| 0 \\|[^\\n]*\\| ${current.shown_all_pass ? 1 : 0} \\| 0 \\|`).test(text), text);

console.log(`\n${failed} test(s) failed.`);
process.exit(failed ? 1 : 0);
