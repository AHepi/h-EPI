/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Reads the records of a planted-mistakes run ("18 planted mistakes.js") and writes a summary,
 * results.md, in the same folder. For each corrector and each kind of mistake it counts how many
 * planted mistakes ended:
 *   repaired  - every shown and held-back job passes, and no nearby situation differs from the world
 *   better    - fewer nearby situations differ from the world than before, but not repaired
 *   unchanged - the same number differ as before
 *   worse     - more differ than before (a correction that made the model more wrong)
 * It also lists every planted mistake with each corrector's result, so no case is hidden in a count.
 *
 * Run with:  node "18 summarise planted mistakes.js" FOLDER [MORE FOLDERS]
 * Records with the same name in later folders add their correctors to the first folder's records.
 * The summary is written to the first folder.
 */
const fs = require('fs');
const path = require('path');

const [folder, ...more] = process.argv.slice(2);
const records = fs.readdirSync(folder).filter(f => f.endsWith('.json')).sort().map(f => {
  const rec = JSON.parse(fs.readFileSync(path.join(folder, f), 'utf8'));
  for (const other of more) {
    const extra = path.join(other, f);
    if (fs.existsSync(extra)) rec.results = rec.results.concat(JSON.parse(fs.readFileSync(extra, 'utf8')).results);
  }
  return rec;
});
const all_pass = text => { const [a, b] = text.split('/'); return a === b; };
function outcome(planted, r) {
  if (r.failed) return 'failed to run';
  if (all_pass(r.shown) && all_pass(r.held_back) && r.nearby.differ === 0) return 'repaired';
  if (r.nearby.differ < planted.before.nearby.differ) return 'better';
  if (r.nearby.differ === planted.before.nearby.differ) return 'unchanged';
  return 'worse';
}
const correctors = [...new Set(records.flatMap(rec => rec.results.map(r => r.corrector)))];
const kinds = [...new Set(records.map(rec => rec.planted.kind))];
const outcomes = ['repaired', 'better', 'unchanged', 'worse', 'failed to run'];

const lines = [`# Planted mistakes: results`, '', `${records.length} planted mistakes, guesser ${records[0] ? records[0].guesser : '?'}. Every number below comes from the records in this folder.`, ''];
for (const kind of kinds) {
  const of_kind = records.filter(rec => rec.planted.kind === kind);
  lines.push(`## ${kind} mistakes (${of_kind.length})`, '', `| Corrector | ${outcomes.join(' | ')} | DeepSeek asked, in total | Questions to the world, in total |`, `|---|${outcomes.map(() => '---').join('|')}|---|---|`);
  for (const c of correctors) {
    const counts = Object.fromEntries(outcomes.map(o => [o, 0]));
    let asked = 0, questions = 0;
    for (const rec of of_kind) {
      const r = rec.results.find(x => x.corrector === c);
      if (!r) continue;
      counts[outcome(rec.planted, r)]++;
      asked += r.deepseek_asked || 0; questions += r.questions_to_world || 0;
    }
    lines.push(`| ${c} | ${outcomes.map(o => counts[o]).join(' | ')} | ${asked} | ${questions} |`);
  }
  lines.push('');
}
lines.push('## Every planted mistake', '', 'Each cell: held-back jobs passed, then nearby situations that differ from the world (before correction: the "planted" column).', '');
lines.push(`| World | Kind | Mistake | Planted | ${correctors.join(' | ')} |`, `|---|---|---|---|${correctors.map(() => '---').join('|')}|`);
for (const rec of records) {
  const p = rec.planted;
  const cells = correctors.map(c => { const r = rec.results.find(x => x.corrector === c); return !r ? '' : r.failed ? 'failed to run' : `${r.held_back}, ${r.nearby.differ} (${outcome(p, r)})`; });
  lines.push(`| ${rec.world} | ${p.kind} | ${p.description.replace(/\|/g, '/')} | ${p.before.held_back}, ${p.before.nearby.differ} | ${cells.join(' | ')} |`);
}
fs.writeFileSync(path.join(folder, 'results.md'), lines.join('\n') + '\n');
console.log(lines.join('\n'));
