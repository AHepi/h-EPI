/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Runs the loop with DeepSeek V4.1 Flash as the guesser, on the test worlds, and saves everything.
 *
 * For each world and each repeat: one shared first guess from DeepSeek, then the six ways of
 * running (one guess, rewrite, guess and fix, full loop, guesser fixes first, review first), all starting from that guess. A repeat is
 * a fresh first guess, so repeats show how much DeepSeek's guesses differ from one ask to the next.
 *
 * Each world's record (every request, every reply, every step the loop took, the final model and
 * the scores) is saved to OUTFOLDER/WORLD repeat N.json. A table of results is printed and saved
 * to OUTFOLDER/results.md.
 *
 * Run with:
 *   DEEPSEEK_API_KEY=... NODE_USE_ENV_PROXY=1 node "17 run with DeepSeek.js" OUTFOLDER [REPEATS] [WORLD,WORLD]
 * The worlds files can be changed with WORLDS_FILE=a.js,b.js (default "03 test worlds.js").
 * MODES=a,b runs only those ways. REUSE_FROM=FOLDER takes each first guess from an earlier run's
 * records instead of asking DeepSeek again, so a way added later starts from the same guesses.
 */
const fs = require('fs');
const path = require('path');
const L = require('./09 loop.js');
const D = require('./17 DeepSeek guesser.js');
// The four ways of running, plus the fifth added in log 18.
const WAYS = process.env.MODES ? process.env.MODES.split(',') : L.WAYS_OF_RUNNING.concat('guesser fixes first', 'review first');

const [out_folder, repeats_text, which] = process.argv.slice(2);
if (!out_folder) { console.error('Give an output folder.'); process.exit(2); }
const REPEATS = Number(repeats_text) || 1;
const WORLDS = (process.env.WORLDS_FILE || '03 test worlds.js').split(',').flatMap(f => require(path.resolve(__dirname, f)))
  .filter(w => !which || which.split(',').includes(w.id));
fs.mkdirSync(out_folder, { recursive: true });

async function run_world(world, repeat) {
  const guesser = D.make_deepseek_guesser();
  const options = { guesser, seed: repeat };
  const started = new Date().toISOString();
  const earlier = process.env.REUSE_FROM && path.join(process.env.REUSE_FROM, `${world.id} repeat ${repeat}.json`);
  const guess = earlier ? Object.assign({ reused_from: earlier }, JSON.parse(fs.readFileSync(earlier, 'utf8')).first_guess) : await L.first_guess(world, options);
  const results = {};
  for (const mode of WAYS) {
    results[mode] = await L.run_task(world, mode, options, guess);
    const f = results[mode].final;
    console.log(`${world.id} repeat ${repeat} | ${mode.padEnd(13)} | shown jobs ${f.original_seen_passed}/${f.original_seen_total} | held-back ${f.held_back_passed}/${f.held_back_total} | questions ${results[mode].questions_to_world} | DeepSeek asked ${results[mode].guesser_calls}`);
  }
  const record = { world: world.id, kind: world.kind, repeat, guesser: D.MODEL_NAME, started, finished: new Date().toISOString(),
    first_guess: guess, counts: guesser.counts, results };
  fs.writeFileSync(path.join(out_folder, `${world.id} repeat ${repeat}.json`), JSON.stringify(record, null, 1) + '\n');
  return record;
}

(async () => {
  const jobs = [];
  for (const world of WORLDS) for (let r = 1; r <= REPEATS; r++) jobs.push([world, r]);
  const records = await Promise.all(jobs.map(([w, r]) => run_world(w, r).catch(e => ({ world: w.id, repeat: r, failed: String(e.message || e) }))));
  const lines = ['| World | Repeat | Way of running | Shown jobs | Held-back jobs | Held-back situations the world was asked about | Questions to the world | DeepSeek asked |', '|---|---|---|---|---|---|---|---|'];
  for (const rec of records) {
    if (rec.failed) { lines.push(`| ${rec.world} | ${rec.repeat} | run failed: ${rec.failed} | | | | | |`); continue; }
    for (const mode of Object.keys(rec.results)) {
      const r = rec.results[mode]; const f = r.final;
      lines.push(`| ${rec.world} | ${rec.repeat} | ${mode} | ${f.original_seen_passed}/${f.original_seen_total} | ${f.held_back_passed}/${f.held_back_total} | ${(f.held_back_asked || []).length} | ${r.questions_to_world} | ${r.guesser_calls} |`);
    }
  }
  fs.writeFileSync(path.join(out_folder, 'results.md'), `# Results\n\nGuesser: ${D.MODEL_NAME}. Every number below comes from a real DeepSeek run.\n\n${lines.join('\n')}\n`);
  console.log(lines.join('\n'));
})();
