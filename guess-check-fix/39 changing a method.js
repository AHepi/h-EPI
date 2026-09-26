/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Log 39. Can the system change one of its own methods? The checker's method for accepting a fix
 * (accept it if it repairs a job and loses none) cannot see what no job checks, which is log 17's failure.
 * DeepSeek is asked for a new method, written in JavaScript; the program keeps it only if, on 72 occasions
 * DeepSeek never saw, it repairs the failure without losing what the current method got right, as the
 * revised semantics' repair (P) asks. The occasions come from "39 occasions.js".
 *
 *   run_method       - runs a method on occasions in a separate process with no access to files, the
 *                      network or the account key, and a time limit; the program, not the method, records
 *                      every question it asks the world (at most three per occasion)
 *   judge            - the declared aims: which held bad fixes it rejects (the aim to repair), and whether
 *                      it accepts every good fix, rejects every losing fix and never fails (the protected aims)
 *   shown_the_failure, told_the_aim - the two arms
 * The plan and conjectures: "39 Plan - changing a method.md".
 *
 * Run with:
 *   DEEPSEEK_API_KEY=... NODE_USE_ENV_PROXY=1 node "39 changing a method.js" OUTFOLDER [REPEATS]
 *   node "39 changing a method.js" --summarise FOLDER
 */
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');
const O = require('./39 occasions.js');

const ROUNDS = 3;
const SHOWN_WORLDS = ['lighthouse-story', 'ball-and-wall'];
const QUESTIONS = 3;

const CURRENT = `function accept_fix(fix_case, ask) {
  const repaired = fix_case.jobs.some(j => j.before === 'fail' && j.after === 'pass');
  const lost = fix_case.jobs.some(j => j.before === 'pass' && j.after === 'fail');
  return repaired && !lost;
}`;
// Log 17's repair, written by a person: ask about up to three situations where the model before and after
// the fix differ, and reject the fix if the world sides with "before".
const REFERENCE = `function accept_fix(fix_case, ask) {
  const repaired = fix_case.jobs.some(j => j.before === 'fail' && j.after === 'pass');
  const lost = fix_case.jobs.some(j => j.before === 'pass' && j.after === 'fail');
  if (!repaired || lost) return false;
  for (const n of fix_case.nearby.filter(n => n.before !== n.after).slice(0, 3)) {
    if (ask(n.id) === n.before) return false;
  }
  return true;
}`;

// ------------------------------------------------------------------
// Running a method in a separate process. The world's answers live only inside a closure the method
// cannot read; the list of questions asked is kept by the program.
// ------------------------------------------------------------------
const RUNNER = `
const vm = require('vm');
let input = '';
process.stdin.on('data', d => { input += d; });
process.stdin.on('end', () => {
  const { code, occasions, limit } = JSON.parse(input);
  const context = vm.createContext({});
  vm.runInContext(\`Object.defineProperty(globalThis, '__make_ask', { writable: false, configurable: false, value: function (answers, limit) {
    const asked = [];
    const ask = function (id) { if (asked.length >= limit) return null; asked.push(id); const a = answers[id]; return a === undefined ? null : a; };
    return { ask, asked: () => asked.slice() };
  } });\`, context);
  try { vm.runInContext(code, context, { timeout: 2000 }); if (vm.runInContext('typeof accept_fix', context) !== 'function') throw new Error('no function named accept_fix'); }
  catch (e) { process.stdout.write(JSON.stringify({ error: String(e && e.message || e).slice(0, 300) })); return; }
  const results = occasions.map(o => {
    try {
      context.__case = JSON.stringify(o.case); context.__answers = JSON.stringify(o.world_says); context.__limit = limit;
      const out = vm.runInContext('(function () { const h = __make_ask(JSON.parse(__answers), __limit); delete globalThis.__answers; const d = accept_fix(JSON.parse(__case), h.ask); return JSON.stringify({ decision: d, asked: h.asked() }); })()', context, { timeout: 1000 });
      const r = JSON.parse(out);
      const accept = r.decision === true || (r.decision && typeof r.decision === 'object' && r.decision.accept === true);
      const readable = typeof r.decision === 'boolean' || (r.decision && typeof r.decision === 'object' && typeof r.decision.accept === 'boolean');
      return readable ? { accept, asked: r.asked } : { error: 'it returned neither true nor false', asked: r.asked };
    } catch (e) { return { error: String(e && e.message || e).slice(0, 200) }; }
  });
  process.stdout.write(JSON.stringify({ results }));
});`;
function run_method(code, occasions) {
  const done = spawnSync(process.execPath, ['-e', RUNNER], { input: JSON.stringify({ code, occasions: occasions.map(o => ({ case: o.case, world_says: o.world_says })), limit: QUESTIONS }), env: {}, cwd: os.tmpdir(), timeout: 120000, maxBuffer: 64 * 1024 * 1024, encoding: 'utf8' });
  if (done.error || done.status !== 0) return { error: done.error ? `the method did not finish (${done.error.code || done.error.message})` : `the method stopped: ${String(done.stderr).slice(0, 200)}` };
  try { return JSON.parse(done.stdout); } catch (e) { return { error: 'the method gave no readable result' }; }
}

// ------------------------------------------------------------------
// The declared aims (the plan's repair)
// ------------------------------------------------------------------
function judge(code, occasions) {
  const ran = run_method(code, occasions);
  const results = ran.error ? occasions.map(() => ({ error: ran.error })) : ran.results;
  const rows = occasions.map((o, i) => ({ id: o.id, world: o.world, kind: o.kind, accept: !!results[i].accept, error: results[i].error || null, asked: results[i].asked || [] }));
  const of = kind => rows.filter(r => r.kind === kind);
  const repaired = of('bad').filter(r => !r.accept && !r.error).length;
  const p1 = of('good').filter(r => !(r.accept && !r.error)).map(r => r.id);   // good fixes not accepted
  const p2 = of('losing').filter(r => r.accept && !r.error).map(r => r.id);   // losing fixes accepted
  const p3 = rows.filter(r => r.error).map(r => r.id);                         // errors or time-outs
  const kept = repaired > 0 && !p1.length && !p2.length && !p3.length;
  return {
    kept, bad_rejected: repaired, bad_total: of('bad').length,
    protected_losses: { good_not_accepted: p1, losing_accepted: p2, errors: p3 },
    questions_asked: rows.reduce((s, r) => s + r.asked.length, 0), occasions_with_questions: rows.filter(r => r.asked.length).length,
    whole_method_error: ran.error || null, rows,
  };
}

// ------------------------------------------------------------------
// Words
// ------------------------------------------------------------------
const JOB_WORDS = `The checker keeps small models of how something works, and jobs that say how certain situations must end. When a model fails a job, the checker tries small fixes. A method called accept_fix decides whether to accept each fix.

accept_fix(fix_case, ask) gets:
- fix_case.jobs: a list of {name, before, after}, where before and after are "pass" or "fail": whether the job passed before the fix and after it.
- fix_case.nearby: a list of {id, situation, before, after}: situations near the jobs, in words, and how the model before the fix and after it says each one ends.
- ask(id): asks the world how the nearby situation with that id really ends; it returns an ending in the same words as before and after. You may ask at most ${QUESTIONS} times per fix; after that ask returns null.
It must return true to accept the fix or false to reject it.

The current method:
\`\`\`javascript
${CURRENT}
\`\`\``;
const REPLY_WORDS = 'Write a new accept_fix in one ```javascript code block. It will be used on many fixes you have not seen, in other models. After the code block, write one line that starts "What it does:" and says in a sentence what your method does.';

function case_words(o) {
  const jobs = o.case.jobs.map(j => `${j.name}: ${j.before} before, ${j.after} after`).join('; ');
  const differ = o.case.nearby.filter(n => n.before !== n.after);
  const broken = differ.filter(n => n.before === o.world_says[n.id] && n.after !== o.world_says[n.id]);
  return `Jobs: ${jobs}.\nNearby situations where the model before and after the fix differ (${differ.length} of ${o.case.nearby.length}):\n${differ.slice(0, 8).map(n => `- id ${n.id}: ${n.situation}. Before: ${n.before}. After: ${n.after}.`).join('\n')}${differ.length > 8 ? `\n- and ${differ.length - 8} more` : ''}\nWhat the world says about id ${broken[0].id}: ${o.world_says[broken[0].id]}. The fix broke this: the model had it right before the fix and wrong after it, and no job checks it.`;
}
function read_reply(text) {
  const blocks = [...String(text || '').matchAll(/```(?:javascript|js)?\s*\n([\s\S]*?)```/gi)].map(m => m[1].trim());
  const code = blocks.reverse().find(b => /accept_fix/.test(b)) || null;
  const said = (/What it does:\s*(.+)/i.exec(String(text || '')) || [])[1] || null;
  return { code, said: said ? said.trim() : null };
}
const says_it_asks = said => !!said && /\bask|\bquer|\bquestion|consult|check(s|ing)? with the world|the world/i.test(said);

// ------------------------------------------------------------------
// The arms
// ------------------------------------------------------------------
const SYSTEM = 'You write small JavaScript functions that a checker can run.';
async function shown_the_failure(D, shown, held) {
  const g = D.make_deepseek_guesser();
  const failures = shown.filter(o => o.kind === 'bad').slice(0, 2);
  const opening = `${JOB_WORDS}\n\nThe current method has a failure. Here are two fixes it accepted that it should not have:\n\nFix 1.\n${case_words(failures[0])}\n\nFix 2.\n${case_words(failures[1])}\n\n${REPLY_WORDS}`;
  const rounds = [];
  let last = null;
  for (let round = 1; round <= ROUNDS; round++) {
    let ask = opening;
    if (last && last.code) {
      const wrong = last.judged.rows.filter(r => (r.kind === 'bad' && r.accept) || (r.kind === 'good' && !r.accept) || (r.kind === 'losing' && r.accept) || r.error);
      const lines = wrong.map(r => { const o = shown.find(x => x.id === r.id); return `- ${r.error ? `an error: ${r.error}` : r.kind === 'bad' ? 'accepted a fix that broke something no job checks' : r.kind === 'good' ? 'rejected a fix that repaired a job and broke nothing' : 'accepted a fix that loses a job'}.${r.kind === 'bad' && r.accept ? `\n${case_words(o)}` : ''}`; });
      ask = `${opening}\n\nYour last method:\n\`\`\`javascript\n${last.code}\n\`\`\`\n\nThe checker ran it on ${shown.length} fixes. ${shown.length - wrong.length} of ${shown.length} were decided as they should be. These were not:\n${lines.join('\n')}\n\n${REPLY_WORDS}`;
    } else if (last) ask = `${opening}\n\nYour last reply had no accept_fix function in a code block.`;
    const text = await g([{ role: 'system', content: SYSTEM }, { role: 'user', content: ask }], { reply_shape: 'none' });
    const reply = read_reply(text);
    const judged_shown = reply.code ? judge(reply.code, shown) : null;
    const right = judged_shown ? judged_shown.rows.filter(r => !r.error && ((r.kind === 'good') === r.accept)).length : 0;
    rounds.push({ round, code: reply.code, said: reply.said, shown_right: right });
    last = { code: reply.code, judged: judged_shown };
    if (reply.code && right === shown.length) break;
  }
  const final = [...rounds].reverse().find(r => r.code) || null;
  return { rounds, code: final ? final.code : null, said: final ? final.said : null, held: final ? summary_of(judge(final.code, held)) : null, tokens_out: g.counts.tokens_out, cut_off: g.counts.cut_off, calls: rounds.length };
}

async function told_the_aim(D, shown, held) {
  const g = D.make_deepseek_guesser();
  const ask = `${JOB_WORDS}\n\nA good method accepts a fix that repairs a failing job and loses none, and does not accept a fix that breaks something the model got right where no job checks it.\n\n${REPLY_WORDS}`;
  const text = await g([{ role: 'system', content: SYSTEM }, { role: 'user', content: ask }], { reply_shape: 'none' });
  const reply = read_reply(text);
  return { rounds: [{ round: 1, code: reply.code, said: reply.said }], code: reply.code, said: reply.said, held: reply.code ? summary_of(judge(reply.code, held)) : null, tokens_out: g.counts.tokens_out, cut_off: g.counts.cut_off, calls: 1 };
}
// What is kept in the record for the held occasions: everything but the world's answers.
const summary_of = j => Object.assign({}, j, { rows: j.rows.map(r => ({ id: r.id, kind: r.kind, accept: r.accept, error: r.error, asked: r.asked })) });

function split(occasions) {
  return { shown: occasions.filter(o => SHOWN_WORLDS.includes(o.world)), held: occasions.filter(o => !SHOWN_WORLDS.includes(o.world)) };
}

function summarise(records, reference, current) {
  const lines = ['| Method | Kept | Held bad fixes rejected (of 24) | Good fixes not accepted | Losing fixes accepted | Errors | Questions asked | Says it asks the world | Asked the world |', '|---|---|---|---|---|---|---|---|---|'];
  const row = (name, h, said) => lines.push(`| ${name} | ${h ? (h.kept ? 'yes' : 'no') : 'no method'} | ${h ? h.bad_rejected : '-'} | ${h ? h.protected_losses.good_not_accepted.length : '-'} | ${h ? h.protected_losses.losing_accepted.length : '-'} | ${h ? h.protected_losses.errors.length : '-'} | ${h ? h.questions_asked : '-'} | ${said === undefined ? '-' : says_it_asks(said) ? 'yes' : 'no'} | ${h ? (h.questions_asked > 0 ? 'yes' : 'no') : '-'} |`);
  row('current method', current);
  row('log 17\'s repair (written by a person)', reference);
  for (const r of records) for (const arm of ['shown the failure', 'told the aim']) row(`${arm}, repeat ${r.repeat}`, r.arms[arm].held, r.arms[arm].said);
  const sayings = ['', 'What DeepSeek said each method does:', ''];
  for (const r of records) for (const arm of ['shown the failure', 'told the aim']) sayings.push(`- ${arm}, repeat ${r.repeat}: ${r.arms[arm].said || '(nothing said)'}`);
  return lines.concat(sayings).join('\n');
}
const results_text = (records, reference, current, failed) => `# Changing a method: results\n\nDeepSeek V4.1 Flash, default thinking. ${records.length} repeats of two arms; every number comes from the records in this folder. Held occasions: 72 (24 bad, 24 good, 24 losing), from eight worlds DeepSeek never saw. A method is kept only if it rejects at least one held bad fix, accepts every good fix, rejects every losing fix, and never fails.\n\n${summarise(records, reference, current)}\n${failed.length ? `\nRuns that failed:\n${failed.join('\n')}\n` : ''}`;

module.exports = { CURRENT, REFERENCE, run_method, judge, split, case_words, read_reply, says_it_asks, shown_the_failure, told_the_aim, summarise, summary_of, QUESTIONS };

if (require.main === module) {
  const [first, second] = process.argv.slice(2);
  const folder = first === '--summarise' ? second : first;
  if (first === '--summarise') {
    const records = fs.readdirSync(folder).filter(f => /^repeat \d+\.json$/.test(f)).sort().map(f => JSON.parse(fs.readFileSync(path.join(folder, f), 'utf8')));
    const b = JSON.parse(fs.readFileSync(path.join(folder, 'baseline.json'), 'utf8'));
    const text = results_text(records, b.reference, b.current, []);
    fs.writeFileSync(path.join(folder, 'results.md'), text);
    console.log(text);
  } else {
    const D = require('./17 DeepSeek guesser.js');
    const REPEATS = Number(second) || 1;
    fs.mkdirSync(folder, { recursive: true });
    const occasions = O.occasions();
    fs.writeFileSync(path.join(folder, 'occasions.json'), JSON.stringify(occasions.map(o => ({ id: o.id, world: o.world, kind: o.kind, broke: o.broke })), null, 1) + '\n');
    const { shown, held } = split(occasions);
    const b = { reference: summary_of(judge(REFERENCE, held)), current: summary_of(judge(CURRENT, held)) };
    fs.writeFileSync(path.join(folder, 'baseline.json'), JSON.stringify(b, null, 1) + '\n');
    (async () => {
      const records = await Promise.all(Array.from({ length: REPEATS }, (_, i) => i + 1).map(async repeat => {
        try {
          const arms = {};
          await Promise.all([['shown the failure', shown_the_failure], ['told the aim', told_the_aim]].map(async ([name, arm]) => { arms[name] = await arm(D, shown, held); }));
          const rec = { repeat, guesser: D.MODEL_NAME, arms };
          fs.writeFileSync(path.join(folder, `repeat ${repeat}.json`), JSON.stringify(rec, null, 1) + '\n');
          console.log(`repeat ${repeat} done`);
          return rec;
        } catch (e) { console.log(`repeat ${repeat} failed: ${e.message}`); return { repeat, failed: String(e.message) }; }
      }));
      const text = results_text(records.filter(r => !r.failed), b.reference, b.current, records.filter(r => r.failed).map(r => `- repeat ${r.repeat}: ${r.failed}`));
      fs.writeFileSync(path.join(folder, 'results.md'), text);
      console.log(text);
    })();
  }
}
