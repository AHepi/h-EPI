/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Tests "47 keep the survivors.js" without calling DeepSeek. Checks:
 *   - grading covers every sequence of one to six actions that is not an observation: 106 short, 972 long
 *   - the true grudge gets everything; the unresolved-insult count is caught on the long sequences
 *   - the survivors' vote answers by majority and leaves ties undecided
 *   - rivals refuted by the world's answers are dropped; every survivor fits every fact
 *   - the next round's DeepSeek is shown the survivors' code
 *   - the world is asked at most 9 times, never about an observation or a test case
 *   - the final functions are graded, and one that acts exactly as a survivor is named as such
 *   - every call asks for the 200,000-token reply limit
 * Run with:  node "47 keep the survivors tests.js"
 */
const K = require('./25 construction worlds.js');
const G = require('./45 grudge again.js');
const S = require('./47 keep the survivors.js');

let failed = 0;
function expect_that(name, ok, detail) {
  if (!ok) failed++;
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${name}${ok || detail === undefined ? '' : `\n     ${detail}`}`);
}
const SCORE = "// running score\nfunction visible(a) { let s = 0; for (const x of a) s += x === 'insult' ? -1 : 1; return { mood: s > 0 ? 'warm' : 'cold' }; }";
const COUNT = "// unresolved insults\nfunction visible(a) { let c = 0; for (const x of a) { if (x === 'insult') c++; else if (x === 'apologise') c = Math.max(0, c - 1); } return { mood: c === 0 ? 'warm' : 'cold' }; }";
const TRUE = "// three levels\nfunction visible(a) { let g = 0; for (const x of a) { if (x === 'insult') g = Math.min(2, g + 1); else if (x === 'apologise' && g === 1) g = 0; else if (x === 'gift' && g === 2) g = 1; } return { mood: g === 0 ? 'warm' : 'cold' }; }";
const block = c => '```javascript\n' + c + '\n```';

function stand_in() {
  const settings_seen = [], prompts = [];
  return {
    MODEL_NAME: 'stand-in', settings_seen, prompts,
    make_deepseek_guesser(send, settings) {
      settings_seen.push(settings);
      const g = async messages => {
        const last = messages[messages.length - 1].content;
        prompts.push(last);
        g.counts.tokens_out += 1;
        if (/Write the one explanation/.test(last)) return block(/These rival explanations fit/.test(last) ? TRUE : COUNT);
        return [SCORE, COUNT, TRUE].map(block).join('\n\n');
      };
      g.counts = { tokens_out: 0, cut_off: 0 };
      return g;
    },
  };
}

(async () => {
  const { observations, test_keys } = G.setting();
  const obs = new Set(observations.map(o => o.events.join('>')));
  const t = S.grade(S.predictions_of(TRUE).said, obs);
  expect_that('grading covers 106 short and 972 long sequences; the true grudge gets them all', t.short_all === 106 && t.long_all === 972 && t.short_right === 106 && t.long_right === 972 && t.telling_right === 2, JSON.stringify(t));
  const c = S.grade(S.predictions_of(COUNT).said, obs);
  expect_that('the unresolved-insult count gets 104 short and is caught on long sequences', c.short_right === 104 && c.long_right < 972, JSON.stringify(c));

  const said = n => S.predictions_of(n).said;
  const v = S.vote([{ said: said(TRUE) }, { said: said(TRUE) }, { said: said(COUNT) }]);
  expect_that('the vote follows the majority', S.true_everywhere(v.said) && v.ties === 0);
  const v2 = S.vote([{ said: said(TRUE) }, { said: said(COUNT) }]);
  expect_that('a tie is left undecided', v2.ties > 0 && Object.keys(v2.said).length === S.EVERY.length - v2.ties);

  const s = stand_in();
  const rec = await S.run_repeat(G.with_higher_limit(s), 1);
  expect_that('every call asks for the 200,000-token reply limit', s.settings_seen.every(x => x && x.reply_limit === 200000));
  expect_that('the world is asked at most 9 times, never an observation or a test case', rec.facts.length <= 9 && rec.facts.every(f => !obs.has(f.events.join('>')) && !test_keys.has(f.events.join('>'))), rec.facts.length);
  const truth = e => K.ending(K.DEVICES.find(d => d.id === 'grudge'), e)[0].split(' is ')[1];
  expect_that('the world\'s answers are the true grudge\'s', rec.facts.every(f => f.mood === truth(f.events)));
  expect_that('refuted rivals are dropped: only three-level rivals survive', rec.survivors.length > 0 && rec.survivors.every(r => r.true_everywhere), rec.survivors.map(r => r.comment).join(', '));
  expect_that('round 2 is shown the survivors\' code', s.prompts.filter(p => /These rival explanations still fit/.test(p)).length === 2 && s.prompts[1].includes('three levels'));
  const shown = rec.finals['shown the survivors'], only = rec.finals['shown the facts only'];
  expect_that('the final functions are graded: shown the survivors wrote the true grudge, facts only the count', shown.true_everywhere && !only.true_everywhere && only.short_right === 104);
  expect_that('a final function that acts exactly as a survivor is named', shown.same_as_a_survivor.length > 0 && only.same_as_a_survivor.length === 0);
  expect_that('the survivors\' vote is graded', rec.finals['survivors vote'].short_right === 106 && rec.finals['survivors vote'].long_right === 972);
  expect_that('the summary builds', /survivors vote \| 106 \| 972/.test(S.summarise([rec])));

  console.log(`\n${failed} test(s) failed.`);
  process.exit(failed ? 1 : 0);
})();
