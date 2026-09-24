/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Log 30. Does a few sentences put at the very top of DeepSeek's standing instructions (its "system
 * prompt") change the range and quality of the questions it asks?
 *
 * The task is log 22's: a long message (about 2,300 words) with the pretend owner's question buried in
 * the middle; DeepSeek must ask the pretend owner a fixed number of questions, one at a time, saying
 * what it expects each time, before it answers. The only thing that differs between arms is the text
 * put at the top of the standing instructions (ARMS below). Nothing else changes.
 *
 * Recorded for each run:
 *   range   - how many different situations it asked about, how many repeated an earlier one, how many
 *             different things it started differently from usual, how many different events it used,
 *             events per question, how often its expectation was wrong (the answer surprised it),
 *             whether it asked the pretend owner's own question back
 *   quality - whether it then answered the pretend owner's question right, and how many of log 19's
 *             other test questions it got right given the answers it collected ("fair": leaving out
 *             test questions it asked about itself)
 *   overlap - how many of its situations the arm with nothing at the top also asked, same world; the
 *             same arm run twice ("nothing at the top, again") shows how much two plain runs overlap
 *
 * Run with:
 *   DEEPSEEK_API_KEY=... NODE_USE_ENV_PROXY=1 node "30 system prompt questions.js" OUTFOLDER ROUND [WORLD,WORLD]
 *   node "30 system prompt questions.js" --summarise FOLDER
 * ROUND is "1" (the arms fixed before any run) or "2" (arms written after reading round 1).
 */
const fs = require('fs');
const path = require('path');
const C = require('./03 checker.js');
const B = require('./19 baseline and more thinking.js');
const T = require('./21 long texts.js');
const W = require('./22 twenty questions.js');

const WORLDS = require('./03 test worlds.js').concat(require('./18 more test worlds.js'));
const QUESTIONS = 10;

// Round 1: written before any run. "nothing at the top" is log 22's instructions unchanged.
const ROUND_ONE = {
  'nothing at the top': null,
  // The same again: DeepSeek varies from run to run, so this shows how much two plain runs differ.
  'nothing at the top, again': null,
  'filler': 'You are a helpful assistant. Write clearly and politely, in plain words. Keep to the format you are asked for. Be accurate, and do not make things up. Take your time and be careful.',
  'doubt': 'Treat your current idea of how this works as a guess that may be wrong. Each time, ask the question whose answer you are least sure of: the one most likely to show that your idea is wrong.',
  'spread': 'Make each question test something no earlier question tested: a different thing, a different event, or a different order of events. Never ask about the same situation twice.',
  'explain': 'Before each question, work out the rules you think lie behind what the owner describes, including anything hidden that cannot be seen directly. Then ask the question that would best tell apart two different sets of rules that could both be true.',
  'detective': 'You are a patient detective. You never assume; you check.',
};
// Round 2: written after reading round 1, before running it. Round 1 showed every text at the top, filler
// included, moving the questions away from the plain run's by about the same amount. Is that the words'
// meaning, or only that the input differs? And can plain instructions move a measure they name?
const ROUND_TWO = {
  'doubt, again': ROUND_ONE.doubt,
  'filler, again': ROUND_ONE.filler,
  'meaningless': 'Reference number 4471-B.',
  'long questions': 'Make every question a long situation: at least four events, one after another.',
  'never ask it back': 'Never ask the owner the question they are asking you in their message; they want you to work that out yourself.',
};
const ROUNDS = { 1: ROUND_ONE, 2: ROUND_TWO };

// The range of one run's questions.
function range_of(world, asked) {
  const model = C.prepare_model(world.world);
  const situations = new Set();
  const changed_things = new Set();
  const events_used = new Set();
  for (const q of asked) {
    const situation = T.read_situation(q.ask);
    const key = T.canonical(world, situation);
    if (key) situations.add(key);
    const problems = [];
    const resolved = C.resolve_situation(model, situation, problems, 'range');
    for (const [thing, state] of Object.entries(resolved.start)) if (model.start[thing] !== state) changed_things.add(thing);
    for (const list of Object.values(resolved.events)) for (const e of list) events_used.add(e);
  }
  const comparable = asked.filter(q => q.surprised !== null);
  return {
    questions: asked.length,
    different_situations: situations.size,
    repeats: asked.filter(q => q.repeat_of_earlier).length,
    usable: asked.filter(q => q.usable).length,
    things_started_differently: changed_things.size,
    things_in_world: Object.keys(model.things).length,
    events_used: events_used.size,
    events_in_world: model.events.length,
    events_per_question: asked.length ? asked.reduce((s, q) => s + q.events, 0) / asked.length : 0,
    surprised: comparable.filter(q => q.surprised).length,
    comparable: comparable.length,
    owners_question_asked_back: asked.filter(q => q.is_the_owners_question).length,
    test_questions_asked: asked.filter(q => q.is_a_test_question).length,
    situation_keys: [...situations],
  };
}

async function run_arm(world, arm_name, system_top, D) {
  const { embedded, tests } = T.embedded_question(world);
  const text = T.message(world, 'long', embedded);
  const as_world = Object.assign({}, world, { request: text });
  const test_keys = new Set(tests.map(q => JSON.stringify(q.situation)));
  const asked = await W.must_ask(D, world, text, embedded, test_keys, { questions: QUESTIONS, system_top: system_top || undefined });
  const g = D.make_deepseek_guesser();
  const d = await B.ask_direct(g, as_world, tests, asked.answers);
  const asked_keys = new Set(asked.answers.map(a => JSON.stringify(a.situation)));
  return {
    world: world.id, arm: arm_name, system_top, guesser: D.MODEL_NAME, questions: QUESTIONS,
    embedded: { id: embedded.id, in_prose: T.question_in_prose(embedded) },
    owners_question: asked.grade, asked: asked.asked, stop_tries: asked.stop_tries, unreadable: asked.unreadable,
    range: range_of(world, asked.asked),
    tests: B.grade_direct(tests, d.answers),
    left_out_of_scoring: tests.filter(q => asked_keys.has(JSON.stringify(q.situation))).map(q => q.id),
    tokens_out: asked.tokens_out + d.tokens_out, cut_off: asked.cut_off + g.counts.cut_off,
  };
}

function summarise(records) {
  const arms = [...new Set(records.map(r => r.arm))];
  const baseline = {};
  for (const r of records.filter(r => r.arm === 'nothing at the top')) baseline[r.world] = new Set(r.range.situation_keys);
  const lines = [
    '| Arm | Runs | Different situations | Repeats | Things started differently | Events used | Events per question | Surprised / comparable | Owner\'s question asked back | Also asked by "nothing at the top" | Owner\'s question right | Held-back right, fair | Nearby right, fair | Output tokens |',
    '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|',
  ];
  for (const arm of arms) {
    const rs = records.filter(r => r.arm === arm);
    const sum = f => rs.reduce((s, r) => s + f(r), 0);
    let hr = 0, ht = 0, nr = 0, nt = 0;
    for (const r of rs) {
      const skip = new Set(r.left_out_of_scoring);
      for (const g of r.tests) { if (skip.has(g.id)) continue; if (g.kind === 'held-back') { ht++; if (g.right) hr++; } else { nt++; if (g.right) nr++; } }
    }
    const shared = sum(r => (baseline[r.world] ? r.range.situation_keys.filter(k => baseline[r.world].has(k)).length : 0));
    const events_per_question = sum(r => r.range.events_per_question * r.range.questions) / Math.max(1, sum(r => r.range.questions));
    lines.push(`| ${arm} | ${rs.length} | ${sum(r => r.range.different_situations)} | ${sum(r => r.range.repeats)} | ${sum(r => r.range.things_started_differently)} | ${sum(r => r.range.events_used)} | ${events_per_question.toFixed(1)} | ${sum(r => r.range.surprised)}/${sum(r => r.range.comparable)} | ${sum(r => r.range.owners_question_asked_back)} | ${arm === 'nothing at the top' ? '-' : shared} | ${sum(r => (r.owners_question.answer_right ? 1 : 0))}/${rs.length} | ${hr}/${ht} | ${nr}/${nt} | ${sum(r => r.tokens_out)} |`);
  }
  const worlds = [...new Set(records.map(r => r.world))];
  const by_world = ['', 'Different situations asked, by world:', '', `| World | ${arms.join(' | ')} |`, `|---|${arms.map(() => '---').join('|')}|`];
  for (const w of worlds) by_world.push(`| ${w} | ${arms.map(a => { const r = records.find(x => x.world === w && x.arm === a); return r ? r.range.different_situations : '-'; }).join(' | ')} |`);
  return lines.concat(by_world).join('\n');
}
const results_text = (records, failed) => `# System prompt and questions: results\n\nDeepSeek V4.1 Flash, default thinking, log 21's long messages, ${QUESTIONS} questions a run. ${records.length} runs; every number comes from the records in this folder. "Fair" leaves out every test question the run asked the pretend owner about.\n\n${summarise(records)}\n${failed.length ? `\nRuns that failed:\n${failed.join('\n')}\n` : ''}`;

module.exports = { ROUND_ONE, ROUND_TWO, ROUNDS, QUESTIONS, range_of, run_arm, summarise };

if (require.main === module) {
  const [first, second, third] = process.argv.slice(2);
  if (first === '--summarise') {
    const records = fs.readdirSync(second).filter(f => f.endsWith('.json')).sort().map(f => JSON.parse(fs.readFileSync(path.join(second, f), 'utf8')));
    const text = results_text(records, []);
    fs.writeFileSync(path.join(second, 'results.md'), text);
    console.log(text);
  } else {
    const D = require('./17 DeepSeek guesser.js');
    const arms = ROUNDS[second];
    if (!arms || !Object.keys(arms).length) { console.log(`Round "${second}" has no arms.`); process.exit(1); }
    const worlds = WORLDS.filter(w => !third || third.split(',').includes(w.id));
    fs.mkdirSync(first, { recursive: true });
    (async () => {
      const jobs = [];
      for (const w of worlds) for (const [name, top] of Object.entries(arms)) jobs.push([w, name, top]);
      const records = await Promise.all(jobs.map(async ([w, name, top]) => {
        try {
          const rec = await run_arm(w, name, top, D);
          fs.writeFileSync(path.join(first, `${w.id} - ${name}.json`), JSON.stringify(rec, null, 1) + '\n');
          console.log(`${w.id} - ${name} done`);
          return rec;
        } catch (e) { console.log(`${w.id} - ${name} failed: ${e.message}`); return { world: w.id, arm: name, failed: String(e.message) }; }
      }));
      const text = results_text(records.filter(r => !r.failed), records.filter(r => r.failed).map(r => `- ${r.world}, ${r.arm}: ${r.failed}`));
      fs.writeFileSync(path.join(first, 'results.md'), text);
      console.log(text);
    })();
  }
}
