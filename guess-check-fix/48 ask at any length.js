/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Log 48. Log 47 kept the rival explanations that survived, but the world could be asked only about
 * situations of up to four actions, while the final answers were graded on up to six. So survivors
 * were never tested where they differ most. This is log 47 run again with one change: the world may be
 * asked about any situation of up to six actions where the standing rivals disagree.
 *
 * Everything else is log 47's code ("47 keep the survivors.js"): three rounds of four new rivals, the
 * three most disputed situations asked each round, refuted rivals dropped, log 25's 12 test cases
 * refused, and three final answers from the same run (survivors vote, shown the survivors, shown the
 * facts only), graded on every sequence of one to six actions that is not an observation.
 *
 * Run with:
 *   DEEPSEEK_API_KEY=... NODE_USE_ENV_PROXY=1 node "48 ask at any length.js" OUTFOLDER [REPEATS]
 *   node "48 ask at any length.js" --summarise OUTFOLDER
 */
const fs = require('fs');
const path = require('path');
const G = require('./45 grudge again.js');
const S = require('./47 keep the survivors.js');

const OPTIONS = { question_length: 6, label: 'log 48' };

// What log 47's summary does not show: how long the world's questions were.
function question_lengths(records) {
  const by_length = {};
  for (const r of records) for (const f of r.facts) by_length[f.events.length] = (by_length[f.events.length] || 0) + 1;
  const long_runs = records.filter(r => r.facts.some(f => f.events.length > 4)).length;
  return `World's answers by length of situation: ${Object.keys(by_length).sort().map(n => `${n} actions: ${by_length[n]}`).join(', ')}. Runs with at least one answer about five or six actions: ${long_runs} of ${records.length}. Up to 9 graded sequences per run may be ones the world answered.`;
}

module.exports = { OPTIONS, question_lengths };

if (require.main === module) {
  const [first, second] = process.argv.slice(2);
  const read_records = folder => fs.readdirSync(folder).filter(f => /^grudge repeat \d+\.json$/.test(f)).sort().map(f => JSON.parse(fs.readFileSync(path.join(folder, f), 'utf8')));
  const write_results = (folder, records, failed) => {
    const text = `# Ask at any length: results\n\nDeepSeek V4.1 Flash, default thinking, reply limit 200000; the world may be asked about situations of up to six actions. ${records.length} repeats; every number comes from the records in this folder.\n\n${S.summarise(records)}\n\n${question_lengths(records)}\n${failed.length ? `\nRuns that failed:\n${failed.join('\n')}\n` : ''}`;
    fs.writeFileSync(path.join(folder, 'results.md'), text);
    console.log(text);
  };
  if (first === '--summarise') write_results(second, read_records(second), []);
  else {
    const D = G.with_higher_limit(require('./17 DeepSeek guesser.js'));
    const REPEATS = Number(second) || 1;
    fs.mkdirSync(first, { recursive: true });
    (async () => {
      const jobs = [];
      for (let r = 1; r <= REPEATS; r++) jobs.push(r);
      const records = await Promise.all(jobs.map(async r => {
        try { const rec = Object.assign(await S.run_repeat(D, r, OPTIONS), { question_length: OPTIONS.question_length }); fs.writeFileSync(path.join(first, `grudge repeat ${r}.json`), JSON.stringify(rec, null, 1) + '\n'); console.log(`repeat ${r} done`); return rec; }
        catch (e) { console.log(`repeat ${r} failed: ${e.message}`); return { failed: `- repeat ${r}: ${e.message}` }; }
      }));
      write_results(first, records.filter(r => !r.failed), records.filter(r => r.failed).map(r => r.failed));
    })();
  }
}
