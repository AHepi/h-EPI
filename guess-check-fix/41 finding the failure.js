/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Log 41. Can the system find a method's failure itself? DeepSeek gets the checker's current fix-acceptance
 * method and is asked whether anything is wrong with it, without being told what. Two arms:
 *   with the record  - it also gets a record of the method at work in the correction loop: each fix the
 *                      method accepted, the jobs before and after, and, for each nearby situation the fix
 *                      changed, what the world said when asked afterwards
 *   method only      - the same question, with no record
 * It may say nothing is wrong and return the method unchanged, or name a failure and write a new method.
 * What it writes is judged by what it does, on log 39's 72 held occasions and log 39's aims (kept or not),
 * not by what it says. The record comes from the two worlds log 39 showed DeepSeek, so the held occasions
 * stay unseen.
 * The plan and conjectures: "41 Plan - finding the failure.md".
 *
 * Run with:
 *   DEEPSEEK_API_KEY=... NODE_USE_ENV_PROXY=1 node "41 finding the failure.js" OUTFOLDER [REPEATS]
 *   node "41 finding the failure.js" --record   (prints the record, with no DeepSeek call)
 *   DEEPSEEK_API_KEY=... NODE_USE_ENV_PROXY=1 node "41 finding the failure.js" --follow-up OUTFOLDER [REPEATS]
 *       the follow-up planned after log 41's first results: the with-the-record arm only, with the reply
 *       limit raised to 200,000 tokens
 */
const fs = require('fs');
const path = require('path');
const C = require('./03 checker.js');
const O = require('./39 occasions.js');
const M = require('./39 changing a method.js');
const W = require('./40 kept method at work.js');

const RECORD_WORLDS = ['lighthouse-story', 'ball-and-wall'];
const RECORD_ENTRIES = 8;
const SITUATIONS_PER_ENTRY = 8;

// The current method at work in the correction loop, in the two record worlds, and every fix it accepted.
function accepted_fixes() {
  const out = [];
  for (const world of O.WORLDS.filter(w => RECORD_WORLDS.includes(w.id))) {
    const s = W.setting(world);
    for (const start of W.starts_of(s)) {
      let model = start.model;
      for (let round = 1; round <= W.ROUNDS; round++) {
        if (!C.check(model, s.shown).failed.length) break;
        const list = W.candidates(s, model);
        if (!list.length) break;
        const pick = list.find(({ c, was }) => { const lost = [...was].some(j => !c.now.has(j)); return !lost; });
        if (!pick) break;
        const before_says = s.nearby.map(n => O.ending_words(model, n.situation, s.things));
        const after_says = s.nearby.map(n => O.ending_words(pick.c.model, n.situation, s.things));
        const changed = s.nearby.map((n, i) => ({ situation: C.describe_situation(n), before: before_says[i], after: after_says[i], world: s.world_says[i] })).filter(x => x.before !== x.after);
        out.push({
          world: world.id, start: start.description, round, fix: pick.c.description,
          jobs: s.shown.map(j => ({ name: j.name, before: pick.was.has(j.name) ? 'pass' : 'fail', after: pick.c.now.has(j.name) ? 'pass' : 'fail' })),
          changed, broke: changed.filter(x => x.before === x.world && x.after !== x.world).length,
        });
        model = pick.c.model;
      }
    }
  }
  return out;
}
// The record shown to DeepSeek: a fixed scramble of the accepted fixes, the first eight, each with up to eight changed situations.
function record() {
  return accepted_fixes().sort((a, b) => O.scramble_key(`${a.world}|${a.start}|${a.round}`) - O.scramble_key(`${b.world}|${b.start}|${b.round}`)).slice(0, RECORD_ENTRIES)
    .map(e => Object.assign({}, e, { shown_changed: e.changed.slice(0, SITUATIONS_PER_ENTRY) }));
}
function record_words(entries) {
  return entries.map((e, i) => `Fix ${i + 1} (accepted). Jobs: ${e.jobs.map(j => `${j.name}: ${j.before} before, ${j.after} after`).join('; ')}.\nNearby situations this fix changed (${e.changed.length}), and what the world said when asked afterwards:\n${e.shown_changed.map(x => `- ${x.situation}. Model before the fix: ${x.before}. After: ${x.after}. World: ${x.world}.`).join('\n')}${e.changed.length > e.shown_changed.length ? `\n- and ${e.changed.length - e.shown_changed.length} more` : ''}`).join('\n\n');
}

const JOB = `The checker keeps small models of how something works, and jobs that say how certain situations must end. When a model fails a job, the checker tries small fixes. A method called accept_fix decides whether to accept each fix.

accept_fix(fix_case, ask) gets:
- fix_case.jobs: a list of {name, before, after}, where before and after are "pass" or "fail": whether the job passed before the fix and after it.
- fix_case.nearby: a list of {id, situation, before, after}: situations near the jobs, in words, and how the model before the fix and after it says each one ends.
- ask(id): asks the world how the nearby situation with that id really ends; it returns an ending in the same words as before and after. It may ask at most ${M.QUESTIONS} times per fix; after that ask returns null.
It must return true to accept the fix or false to reject it.

The method the checker uses now:
\`\`\`javascript
${M.CURRENT}
\`\`\``;
const QUESTION = 'Is anything wrong with this method? If you find nothing wrong, say so and return it unchanged. If you find something wrong, say what, and write a better accept_fix.\n\nReply with the method in one ```javascript code block. After it, write one line that starts "What is wrong:" and says what you found wrong, or "nothing".';
const SYSTEM = 'You write small JavaScript functions that a checker can run.';

function read(text) {
  const r = M.read_reply(text);
  const wrong = (/What is wrong:\s*(.+)/i.exec(String(text || '')) || [])[1] || null;
  return { code: r.code, wrong: wrong ? wrong.trim() : null };
}
const same_as_current = code => !!code && code.replace(/\s+/g, '') === M.CURRENT.replace(/\s+/g, '');

// settings: guesser settings, such as { reply_limit: 200000 } for the follow-up (log 41, after its first results).
async function ask_arm(D, entries, held, with_record, settings) {
  const g = settings ? D.make_deepseek_guesser(undefined, settings) : D.make_deepseek_guesser();
  const text = with_record
    ? `${JOB}\n\nA record of the method at work: fixes it accepted while correcting models, in no particular order.\n\n${record_words(entries)}\n\n${QUESTION}`
    : `${JOB}\n\n${QUESTION}`;
  const reply = read(await g([{ role: 'system', content: SYSTEM }, { role: 'user', content: text }], { reply_shape: 'none' }));
  const unchanged = !reply.code || same_as_current(reply.code);
  return { code: reply.code, what_is_wrong: reply.wrong, unchanged, held: reply.code && !unchanged ? M.summary_of(M.judge(reply.code, held)) : null, tokens_out: g.counts.tokens_out, cut_off: g.counts.cut_off };
}

function summarise(records) {
  const lines = ['| Arm, repeat | Changed the method | Kept on the held occasions | Held bad fixes rejected (of 24) | Good fixes not accepted | Losing fixes accepted | Errors | Questions asked |', '|---|---|---|---|---|---|---|---|'];
  for (const r of records) for (const arm of ['with the record', 'method only']) {
    const a = r.arms[arm], h = a.held;
    lines.push(`| ${arm}, ${r.repeat} | ${a.unchanged ? 'no' : 'yes'} | ${h ? (h.kept ? 'yes' : 'no') : '-'} | ${h ? h.bad_rejected : '-'} | ${h ? h.protected_losses.good_not_accepted.length : '-'} | ${h ? h.protected_losses.losing_accepted.length : '-'} | ${h ? h.protected_losses.errors.length : '-'} | ${h ? h.questions_asked : '-'} |`);
  }
  const said = ['', 'What DeepSeek said is wrong:', ''];
  for (const r of records) for (const arm of ['with the record', 'method only']) said.push(`- ${arm}, repeat ${r.repeat}: ${r.arms[arm].what_is_wrong || '(nothing said)'}`);
  return lines.concat(said).join('\n');
}
const results_text = (records, failed) => `# Finding the failure: results\n\nDeepSeek V4.1 Flash, default thinking. ${records.length} repeats of two arms; every number comes from the records in this folder. A changed method is judged on log 39's 72 held occasions by log 39's aims.\n\n${summarise(records)}\n${failed.length ? `\nRuns that failed:\n${failed.join('\n')}\n` : ''}`;

module.exports = { accepted_fixes, record, record_words, read, same_as_current, ask_arm, summarise, JOB, QUESTION };

if (require.main === module) {
  const [first, second] = process.argv.slice(2);
  if (first === '--record') {
    const all = accepted_fixes();
    const entries = record();
    console.log(`accepted fixes: ${all.length}, of which broke something: ${all.filter(e => e.broke).length}`);
    console.log(`record: ${entries.length} entries, broke something: ${entries.map(e => e.broke).join(', ')}`);
    console.log(record_words(entries).slice(0, 3000));
  } else if (first === '--follow-up') {
    const D = require('./17 DeepSeek guesser.js');
    const folder = second;
    const REPEATS = Number(process.argv[4]) || 3;
    fs.mkdirSync(folder, { recursive: true });
    const entries = record();
    const { held } = M.split(O.occasions());
    (async () => {
      const rows = await Promise.all(Array.from({ length: REPEATS }, (_, i) => i + 1).map(async repeat => {
        const a = await ask_arm(D, entries, held, true, { reply_limit: 200000 });
        const rec = { repeat, guesser: D.MODEL_NAME, reply_limit: 200000, arms: { 'with the record': a } };
        fs.writeFileSync(path.join(folder, `follow-up repeat ${repeat}.json`), JSON.stringify(rec, null, 1) + '\n');
        return rec;
      }));
      const lines = ['| Repeat | Cut off | Changed the method | Kept | Held bad fixes rejected (of 24) | Good fixes not accepted | Output tokens | What is wrong |', '|---|---|---|---|---|---|---|---|'];
      for (const r of rows) { const a = r.arms['with the record'], h = a.held; lines.push(`| ${r.repeat} | ${a.cut_off} | ${a.unchanged ? 'no' : 'yes'} | ${h ? (h.kept ? 'yes' : 'no') : '-'} | ${h ? h.bad_rejected : '-'} | ${h ? h.protected_losses.good_not_accepted.length : '-'} | ${a.tokens_out} | ${(a.what_is_wrong || '(nothing said)').replace(/\|/g, '/')} |`); }
      const text = `# Finding the failure, follow-up: results\n\nThe with-the-record arm only, reply limit 200,000 tokens, planned after log 41's first results. Every number comes from the "follow-up" records in this folder.\n\n${lines.join('\n')}\n`;
      fs.writeFileSync(path.join(folder, 'follow-up results.md'), text);
      console.log(text);
    })();
  } else if (first === '--summarise') {
    const records = fs.readdirSync(second).filter(f => /^repeat \d+\.json$/.test(f)).sort().map(f => JSON.parse(fs.readFileSync(path.join(second, f), 'utf8')));
    const text = results_text(records, []);
    fs.writeFileSync(path.join(second, 'results.md'), text);
    console.log(text);
  } else {
    const D = require('./17 DeepSeek guesser.js');
    const REPEATS = Number(second) || 1;
    fs.mkdirSync(first, { recursive: true });
    const entries = record();
    fs.writeFileSync(path.join(first, 'record shown.json'), JSON.stringify(entries.map(e => ({ world: e.world, start: e.start, round: e.round, fix: e.fix, broke: e.broke, changed: e.changed.length })), null, 1) + '\n');
    const { held } = M.split(O.occasions());
    (async () => {
      const records = await Promise.all(Array.from({ length: REPEATS }, (_, i) => i + 1).map(async repeat => {
        try {
          const arms = {};
          await Promise.all([['with the record', true], ['method only', false]].map(async ([name, w]) => { arms[name] = await ask_arm(D, entries, held, w); }));
          const rec = { repeat, guesser: D.MODEL_NAME, arms };
          fs.writeFileSync(path.join(first, `repeat ${repeat}.json`), JSON.stringify(rec, null, 1) + '\n');
          console.log(`repeat ${repeat} done`);
          return rec;
        } catch (e) { console.log(`repeat ${repeat} failed: ${e.message}`); return { repeat, failed: String(e.message) }; }
      }));
      const text = results_text(records.filter(r => !r.failed), records.filter(r => r.failed).map(r => `- repeat ${r.repeat}: ${r.failed}`));
      fs.writeFileSync(path.join(first, 'results.md'), text);
      console.log(text);
    })();
  }
}
