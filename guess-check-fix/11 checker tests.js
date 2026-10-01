/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Tests for the checker, using hand-written models (no guesser involved).
 * Each test says what should happen. Run it with:  node "11 checker tests.js"
 * It prints one line per test and ends with the number that failed. Run it after every change to the checker.
 */
const C = require('./03 checker.js');
const WORLDS = Object.fromEntries(require('./03 test worlds.js').map(w => [w.id, w]));
const shown = id => C.prepare_jobs({ jobs: WORLDS[id].jobs.filter(j => !j.held_back) }).jobs;
const every = id => C.prepare_jobs({ jobs: WORLDS[id].jobs }).jobs;

let failed = 0;
function expect_that(name, ok, detail) {
  if (!ok) failed++;
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${name}${ok || !detail ? '' : `\n     ${detail}`}`);
}

// 1. Every hidden true world passes all of its own jobs, shown and held back.
for (const id of Object.keys(WORLDS)) {
  const result = C.check(C.prepare_model(WORLDS[id].world), every(id));
  expect_that(`world "${id}" passes all its jobs`, !result.failed.length, `failing: ${result.failed.join(', ')}`);
}

// 2. Misspelled names are caught, with a suggestion.
const misspelled = C.prepare_model({ things: { ball: ['in hand', 'flying'] }, events: ['throw'], rules: [{ name: 'r', when: ['throw happens'], then: 'ball is flyng' }] });
expect_that('a misspelled state is reported with a suggestion', misspelled.problems.some(p => p.includes('Did you mean "flying"')), misspelled.problems.join(' | '));

// 3. Two firm rules that disagree are reported as a contradiction, not silently resolved.
const fighting = C.prepare_model({ things: { ball: ['in hand', 'flying', 'back in hand', 'stuck on wall'], material: ['rubber', 'clay'], wall: ['solid', 'holed'] }, events: ['throw'], start: { ball: 'in hand' },
  rules: [{ name: 'bounce', when: ['throw happens'], then: 'ball is back in hand' }, { name: 'stick', when: ['throw happens'], then: 'ball is stuck on wall' }] });
const fight = C.check(fighting, shown('ball-and-wall')).results[0];
expect_that('two firm rules disagreeing gives a contradiction', fight.verdict === 'contradiction', fight.verdict);

// 4. The more specific rule wins over a less specific one.
const specific = C.prepare_model({ things: fighting.things, events: ['throw'], start: { ball: 'in hand' },
  rules: [{ name: 'bounce', when: ['throw happens'], then: 'ball is back in hand' }, { name: 'stick', when: ['throw happens', 'material is clay'], then: 'ball is stuck on wall' }] });
const clay = C.check(specific, shown('ball-and-wall')).results.find(r => r.job === 'clay ball at solid wall');
expect_that('the rule with more conditions wins', clay.passed, clay.verdict);

// 5. After each event the model settles before the next event (no one-step-late states).
const door = C.check(C.prepare_model(WORLDS['door-game'].world), every('door-game'));
expect_that('game over arrives before the next event', door.passed.includes('over, then key'));

// 6. The sweep: in the lighthouse story, the lamp-lighting scene does no work in the story as told.
const story = C.vary(C.prepare_model(WORLDS['lighthouse-story'].world), shown('lighthouse-story'));
expect_that('the sweep finds the scene that does no work', story.events.some(e => e.job === 'the story as told' && e.event === 'mara lights lamp' && !e.does_work));
expect_that('the lamp rule is marked idle', story.rules.find(r => r.rule === 'Mara lights it').mark === 'idle');

// 7. The sweep: for the to-do app, a deciding test is found about putting a task off once.
const todo = C.vary(C.prepare_model(WORLDS['reminder-app'].world), shown('reminder-app'));
expect_that('a deciding test is found for the to-do app', todo.deciding_tests.some(d => d.found && d.found.steps.some(s => s.includes('does not happen'))));

// 8. Small fix search: finds the missing condition when one exists.
const no_material = C.prepare_model({ things: fighting.things, events: ['throw'], start: { ball: 'in hand' },
  rules: [{ name: 'bounce', when: ['throw happens', 'wall is solid'], then: 'ball is back in hand' }, { name: 'stick', when: ['throw happens', 'wall is solid'], then: 'ball is stuck on wall' }, { name: 'through', when: ['throw happens', 'wall is holed'], then: 'ball is beyond wall' }] });
const small = C.tweaks(no_material, shown('ball-and-wall'));
expect_that('small fix search adds the missing material condition', small.helpful.length && small.helpful[0].description.includes('material is'), small.helpful.map(h => h.description).join(' | '));

// 9. Small fix search: says something new is needed when no small change can work (the hidden ball).
const seen_only = C.prepare_model({ things: { screen: ['down', 'up'], seen: ['at 1', 'at 2', 'at 3', 'at 4', 'nothing'] }, start: { screen: 'down', seen: 'at 1' },
  rules: [{ name: 'a', when: ['seen is at 1'], then: 'seen is at 2' }, { name: 'b', when: ['seen is at 2'], then: 'seen is at 3' }, { name: 'c', when: ['seen is at 3'], then: 'seen is at 4' },
    { name: 'hide', when: ['seen is at 1', 'screen is up'], then: 'seen is nothing' }, { name: 'reappear', when: ['seen is nothing'], then: 'seen is at 4' }] });
const stuck = C.tweaks(seen_only, shown('hidden-ball'));
expect_that('no small change can fix a model that only tracks what is seen', stuck.needs_something_new.length > 0);

// 10. The fix check: adding a hidden "place" thing is accepted as a new thing, and passes held-back jobs.
const with_place = C.prepare_model(Object.assign({}, WORLDS['hidden-ball'].world));
const fix = C.check_fix(seen_only, with_place, shown('hidden-ball'), { decide: false });
expect_that('adding a thing to track is accepted as construction', fix.verdict === 'accepted' && fix.kind.startsWith('new thing'), `${fix.verdict}, ${fix.kind}`);

// 11. The fix check refuses a fix that breaks a job that used to pass.
const worse = C.prepare_model({ things: fighting.things, events: ['throw'], start: { ball: 'in hand' }, rules: [{ name: 'stick', when: ['throw happens'], then: 'ball is stuck on wall' }] });
const refused = C.check_fix(C.prepare_model(WORLDS['ball-and-wall'].world), worse, shown('ball-and-wall'), { decide: false });
expect_that('a fix that breaks a passing job is not accepted', refused.verdict === 'worse' || refused.verdict === 'trade', refused.verdict);

// 12. Two rivals that pass the same jobs: the checker finds a situation that tells them apart.
const rival = JSON.parse(JSON.stringify(WORLDS['reminder-app'].world));
rival.rules = rival.rules.map(r => (r.name === 'urgent after two snoozes' ? Object.assign({}, r, { when: ['snoozes is 1', 'task is new'] }) : r));
const told_apart = C.decide(C.prepare_model(WORLDS['reminder-app'].world), C.prepare_model(rival), shown('reminder-app'));
expect_that('two rivals are told apart by a deciding test', told_apart.found.length > 0);

// 13. A rule that needs one thing in two states at once is reported as never able to fire.
const impossible = C.prepare_model({ things: { ball: ['at 1', 'at 2', 'at 3'] }, rules: [{ name: 'moves', when: ['ball is at 1', 'ball is at 2'], then: 'ball is at 3' }] });
expect_that('an impossible rule is reported', impossible.problems.some(p => p.includes('can never fire')), impossible.problems.join(' | '));

// 14. The one-new-rule search finds a missing rule over things the model already has.
const missing_stick = C.prepare_model({ things: fighting.things, events: ['throw'], start: { ball: 'in hand' },
  rules: [{ name: 'bounce', when: ['throw happens', 'wall is solid', 'material is rubber'], then: 'ball is back in hand' }, { name: 'through', when: ['throw happens', 'wall is holed'], then: 'ball is beyond wall' }] });
const found_rule = C.new_rule_search(missing_stick, shown('ball-and-wall'));
expect_that('the new rule search finds a rule for the clay ball', found_rule.helpful.some(h => h.repaired.includes('clay ball at solid wall')), found_rule.helpful.map(h => h.description).join(' | '));

// 15. The owner's word list fills in things the model left out, without touching its rules.
const filled = C.add_owner_words(C.prepare_model({ things: { ball: ['at 1', 'at 2'] }, rules: [] }), { screen: ['down', 'up'], ball: ['at 1', 'at 2', 'at 3'] });
expect_that('owner words are added', filled.added.includes('screen') && filled.added.includes('ball: at 3'), filled.added.join(', '));

console.log(`\n${failed} test(s) failed.`);
process.exit(failed ? 1 : 0);
