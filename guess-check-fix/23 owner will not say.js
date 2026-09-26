/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Log 23. In log 22 DeepSeek, made to ask 20 questions, first asked the owner their own buried question
 * back, so its right answers to that question showed nothing about its reasoning. Here the owner refuses:
 * asking the buried question gets "I can't tell you that one; that's what I'm asking you", and still uses
 * up one of the 20 questions. Can DeepSeek work the answer out from what it is allowed to ask?
 *
 * On log 21's long messages, per world and repeat:
 *   answer straight away            - as in logs 21 and 22
 *   must ask 20, owner will not say - log 22's twenty questions, one at a time, with the refusal
 * Then both answer the other test questions of log 19, given the answers they had.
 *
 * A question that starts like the owner's and carries on past it (the owner's question plus more events)
 * is not refused, because it is a different situation; it is counted as a near copy, so any leak shows.
 *
 * Run with:
 *   DEEPSEEK_API_KEY=... NODE_USE_ENV_PROXY=1 node "23 owner will not say.js" OUTFOLDER [REPEATS] [WORLD,WORLD]
 *   node "23 owner will not say.js" --summarise FOLDER
 */
const fs = require('fs');
const path = require('path');
const B = require('./19 baseline and more thinking.js');
const T = require('./21 long texts.js');
const W = require('./22 twenty questions.js');

const WORLDS = require('./03 test worlds.js').concat(require('./18 more test worlds.js'));
const ARM = 'must ask 20, owner will not say';

async function run_world(world, repeat, D) {
  const { embedded, tests } = T.embedded_question(world);
  const text = T.message(world, 'long', embedded);
  const as_world = Object.assign({}, world, { request: text });
  const test_keys = new Set(tests.map(q => JSON.stringify(q.situation)));
  const test_after = async answers => {
    const g = D.make_deepseek_guesser();
    const d = await B.ask_direct(g, as_world, tests, answers);
    return { graded: B.grade_direct(tests, d.answers), tokens_out: d.tokens_out, cut_off: g.counts.cut_off };
  };
  const arms = {};
  const straight = await T.answer_straight(D, world, text, embedded, []);
  arms['answer straight away'] = Object.assign(straight, { tests: await test_after([]) });
  const refused = await W.must_ask(D, world, text, embedded, test_keys, { refuse: true });
  arms[ARM] = Object.assign(refused, { answers_given: refused.answers.length, tests: await test_after(refused.answers) });
  const asked_keys = new Set(refused.answers.map(a => JSON.stringify(a.situation)));
  return { world: world.id, repeat, guesser: D.MODEL_NAME, embedded: { id: embedded.id, in_prose: T.question_in_prose(embedded), world_says: embedded.parts },
    left_out_of_scoring: tests.filter(q => asked_keys.has(JSON.stringify(q.situation))).map(q => q.id), arms };
}

function summarise(records) {
  const lines = ['| Arm | Owner\'s question answered right | Other held-back right, fair | Nearby right, fair | Output tokens | Replies cut off |', '|---|---|---|---|---|---|'];
  for (const n of ['answer straight away', ARM]) {
    const t = { right: 0, runs: 0, hr: 0, ht: 0, nr: 0, nt: 0, tokens: 0, cut: 0 };
    for (const r of records) {
      const a = r.arms[n]; if (!a) continue;
      const skip = new Set(r.left_out_of_scoring);
      t.runs++; t.right += a.grade.answer_right ? 1 : 0;
      t.tokens += (a.tokens_out || 0) + a.tests.tokens_out; t.cut += (a.cut_off || 0) + (a.tests.cut_off || 0);
      for (const g of a.tests.graded) { if (skip.has(g.id)) continue; if (g.kind === 'held-back') { t.ht++; if (g.right) t.hr++; } else { t.nt++; if (g.right) t.nr++; } }
    }
    lines.push(`| ${n} | ${t.right}/${t.runs} | ${t.hr}/${t.ht} | ${t.nr}/${t.nt} | ${t.tokens} | ${t.cut} |`);
  }
  const runs = records.map(r => ({ world: r.world, repeat: r.repeat, a: r.arms[ARM], straight: r.arms['answer straight away'] }));
  const all = runs.flatMap(x => x.a.asked);
  const with_copy = runs.filter(x => x.a.asked.some(q => q.extends_owners_question));
  const without_copy = runs.filter(x => !x.a.asked.some(q => q.extends_owners_question));
  const right = list => list.filter(x => x.a.grade.answer_right).length;
  const behaviour = ['', `What DeepSeek did with its ${all.length} questions (${runs.length} runs of 20):`, '',
    `- asked the owner's own question and was refused: ${all.filter(q => q.refused).length} times, in ${runs.filter(x => x.a.asked.some(q => q.refused)).length} of ${runs.length} runs; the most in one run: ${Math.max(0, ...runs.map(x => x.a.asked.filter(q => q.refused).length))}`,
    `- asked a near copy (the owner's question plus more events): ${all.filter(q => q.extends_owners_question).length} times, in ${with_copy.length} runs`,
    `- the owner's question answered right in runs with a near copy: ${right(with_copy)} of ${with_copy.length}; without one: ${right(without_copy)} of ${without_copy.length}`,
    `- the same situation as one it had already asked: ${all.filter(q => q.repeat_of_earlier).length}`,
    `- with an expectation that could be compared: ${all.filter(q => q.surprised !== null).length}; surprised: ${all.filter(q => q.surprised).length}`,
    `- tries to stop before the 20th question: ${runs.reduce((s, x) => s + x.a.stop_tries, 0)}; replies that were not a question: ${runs.reduce((s, x) => s + x.a.unreadable, 0)}`];
  const by_world = ['', 'By world: the owner\'s question answered right (answer straight away / must ask 20, owner will not say), and refusals:', '', '| World | Repeat | Straight away | Owner will not say | Refused | Near copies |', '|---|---|---|---|---|---|'];
  for (const x of runs) by_world.push(`| ${x.world} | ${x.repeat} | ${x.straight.grade.answer_right ? 'right' : 'wrong'} | ${x.a.grade.answer_right ? 'right' : 'wrong'} | ${x.a.asked.filter(q => q.refused).length} | ${x.a.asked.filter(q => q.extends_owners_question).length} |`);
  return lines.concat(behaviour, by_world).join('\n');
}
const results_text = (records, failed) => `# The owner will not say: results\n\nDeepSeek V4.1 Flash, default thinking, log 21's long messages. ${records.length} world-and-repeat runs; every number comes from the records in this folder. "Fair" leaves out every test question whose situation DeepSeek asked the owner about.\n\n${summarise(records)}\n${failed.length ? `\nRuns that failed:\n${failed.join('\n')}\n` : ''}`;

module.exports = { run_world, summarise };

if (require.main === module) {
  const [first, second, third] = process.argv.slice(2);
  if (first === '--summarise') {
    const records = fs.readdirSync(second).filter(f => f.endsWith('.json')).sort().map(f => JSON.parse(fs.readFileSync(path.join(second, f), 'utf8')));
    const text = results_text(records, []);
    fs.writeFileSync(path.join(second, 'results.md'), text);
    console.log(text);
  } else {
    const D = require('./17 DeepSeek guesser.js');
    const worlds = WORLDS.filter(w => !third || third.split(',').includes(w.id));
    const REPEATS = Number(second) || 1;
    fs.mkdirSync(first, { recursive: true });
    (async () => {
      const jobs = [];
      for (const w of worlds) for (let r = 1; r <= REPEATS; r++) jobs.push([w, r]);
      const records = await Promise.all(jobs.map(async ([w, r]) => {
        try {
          const rec = await run_world(w, r, D);
          fs.writeFileSync(path.join(first, `${w.id} repeat ${r}.json`), JSON.stringify(rec, null, 1) + '\n');
          console.log(`${w.id} repeat ${r} done`);
          return rec;
        } catch (e) { console.log(`${w.id} repeat ${r} failed: ${e.message}`); return { world: w.id, repeat: r, failed: String(e.message) }; }
      }));
      const text = results_text(records.filter(r => !r.failed), records.filter(r => r.failed).map(r => `- ${r.world} repeat ${r.repeat}: ${r.failed}`));
      fs.writeFileSync(path.join(first, 'results.md'), text);
      console.log(text);
    })();
  }
}
