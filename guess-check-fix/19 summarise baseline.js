/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Reads the records of "19 baseline and more thinking.js" (one or more folders run on the same
 * questions) and writes the tables of log 19 to FIRST_FOLDER/summary.md:
 *   1. every arm: held-back and nearby questions right, DeepSeek calls, output tokens, cut-off replies
 *   2. the same counts leaving out every question whose situation the loop asked the world about.
 *      Those situations are found by replaying each "guesser fixes first" arm from DeepSeek's recorded
 *      replies (the loop is fully fixed by them); a replay that does not reproduce the recorded final
 *      model is reported and stops the summary.
 *   3. each world: questions right, both repeats, for the main arms
 * No DeepSeek call is made.
 *
 * Run with:  node "19 summarise baseline.js" FOLDER [MORE FOLDERS]
 */
const fs = require('fs');
const path = require('path');
const C = require('./03 checker.js');
const L = require('./09 loop.js');
const B = require('./19 baseline and more thinking.js');
const WORLDS = require('./03 test worlds.js').concat(require('./18 more test worlds.js'));

const folders = process.argv.slice(2);
const files = fs.readdirSync(folders[0]).filter(f => f.endsWith('.json')).sort();
const records = files.map(f => {
  const rec = JSON.parse(fs.readFileSync(path.join(folders[0], f), 'utf8'));
  for (const other of folders.slice(1)) {
    const extra = path.join(other, f);
    if (fs.existsSync(extra)) Object.assign(rec.arms, JSON.parse(fs.readFileSync(extra, 'utf8')).arms);
  }
  return rec;
});
const cut_offs = a => (typeof a.cut_off === 'number' ? a.cut_off : a.log ? a.log.filter(e => (e.tokens_out || 0) >= 32000).length : a.calls === 1 ? (a.tokens_out >= 32000 ? 1 : 0) : null);

(async () => {
  // Situations the loop asked the world about, per world and repeat, by replay.
  const asked = {};
  let replays = 0;
  for (const rec of records) {
    const world = WORLDS.find(w => w.id === rec.world);
    const situations = new Set();
    for (const [name, arm] of Object.entries(rec.arms)) {
      if (!name.startsWith('guesser fixes first') || !arm.log) continue;
      const replies = arm.log.map(e => e.replied);
      let i = 1;
      const replay = await L.run_task(world, 'guesser fixes first', { guesser: async () => replies[i++] }, { raw: L.read_reply(replies[0]), log: [] });
      if (JSON.stringify(replay.model) !== JSON.stringify(arm.model)) throw new Error(`the replay of ${rec.world} repeat ${rec.repeat}, ${name} did not reproduce its final model`);
      replays++;
      replay.added_jobs.forEach(a => situations.add(JSON.stringify(C.prepare_jobs({ jobs: [a.job] }).jobs[0].situation)));
    }
    const { questions } = B.build_questions(world);
    asked[`${rec.world} ${rec.repeat}`] = new Set(questions.filter(q => situations.has(JSON.stringify(q.situation))).map(q => q.id));
  }

  const arms = [...new Set(records.flatMap(r => Object.keys(r.arms)))];
  const lines = ['# Baseline and more thinking: summary', '', `From ${records.length} world-and-repeat records in ${folders.map(f => `\`${path.basename(f)}\``).join(', ')}. ${replays} loop runs were replayed from their recorded replies and all reproduced their final models.`, '',
    '## Every question', '', '| Arm | Held-back right | Nearby right | DeepSeek calls | Output tokens | Replies cut off |', '|---|---|---|---|---|---|'];
  const lines2 = ['', '## Leaving out every situation the loop asked the world about', '', '| Arm | Held-back right | Nearby right |', '|---|---|---|'];
  for (const name of arms) {
    const t = { hr: 0, ht: 0, nr: 0, nt: 0, calls: 0, tokens: 0, cut: 0, cut_known: true, hr2: 0, ht2: 0, nr2: 0, nt2: 0 };
    for (const rec of records) {
      const a = rec.arms[name]; if (!a) continue;
      t.hr += a.held_back_right; t.ht += a.held_back_total; t.nr += a.nearby_right; t.nt += a.nearby_total; t.calls += a.calls; t.tokens += a.tokens_out;
      const c = cut_offs(a); if (c === null) t.cut_known = false; else t.cut += c;
      const skip = asked[`${rec.world} ${rec.repeat}`];
      for (const g of a.graded) {
        if (skip.has(g.id)) continue;
        if (g.kind === 'held-back') { t.ht2++; if (g.right) t.hr2++; } else { t.nt2++; if (g.right) t.nr2++; }
      }
    }
    lines.push(`| ${name} | ${t.hr}/${t.ht} | ${t.nr}/${t.nt} | ${t.calls} | ${t.tokens} | ${t.cut_known ? t.cut : 'not recorded'} |`);
    lines2.push(`| ${name} | ${t.hr2}/${t.ht2} | ${t.nr2}/${t.nt2} |`);
  }
  const main = arms.filter(n => /^DeepSeek alone, high thinking$|^DeepSeek alone, max thinking, reply limit|majority of 5|^guesser fixes first, high thinking$|with the world's answers/.test(n));
  const lines3 = ['', '## Each world: questions right (held-back and nearby), both repeats', '', `| World | ${main.join(' | ')} |`, `|---|${main.map(() => '---').join('|')}|`];
  for (const world of [...new Set(records.map(r => r.world))]) {
    lines3.push(`| ${world} | ${main.map(n => records.filter(r => r.world === world && r.arms[n]).reduce((s, r) => s + r.arms[n].held_back_right + r.arms[n].nearby_right, 0)).join(' | ')} |`);
  }
  const text = lines.concat(lines2, lines3).join('\n') + '\n';
  fs.writeFileSync(path.join(folders[0], 'summary.md'), text);
  console.log(text);
})();
