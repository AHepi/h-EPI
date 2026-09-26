/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Picks the texts and questions for log 28 and grades the causal checker's answers against people's.
 *
 * The corpus is WIQA ("What If Question Answering", Allen Institute for AI, 2019): short paragraphs
 * describing how something works (how rock forms, how a plant makes food), each with questions of the
 * form "suppose more rain falls, how will it affect more erosion?", answered by people with more, less
 * or no effect. Three kinds of question: the change is a step of the paragraph (in paragraph), the
 * change comes from outside the paragraph (from outside), or the change has nothing to do with the
 * paragraph and the answer is "no effect" (unrelated). The corpus is not stored in this repository
 * (its licence is not stated where it is published); this script downloads it to a folder you name.
 *
 *   node "28 causal corpus.js" select CORPUS_FOLDER
 *       downloads the corpus if needed, picks the paragraphs and questions by a fixed rule, and writes:
 *       - runs/28 causal checker/sample.json      the ids picked (kept in the repository)
 *       - CORPUS_FOLDER/paragraphs.json            the paragraphs' text (not kept)
 *       - CORPUS_FOLDER/questions.json             the questions, without people's answers (not kept)
 *       - CORPUS_FOLDER/answers.json               people's answers, read only when grading (not kept)
 *   node "28 causal corpus.js" grade CORPUS_FOLDER
 *       reads the models, readings and direct answers in runs/28 causal checker/, answers each question
 *       with the causal checker, and compares both with people's answers. Writes results.json and prints
 *       the tables.
 *
 * The rule for picking: the test part of the corpus; its paragraphs ordered by a fixed scramble (each id
 * scrambled with the word "log 28"), the first five taken; in each, for each kind of question, the first
 * ten questions in the same scramble. Nothing about the texts or answers is looked at in choosing.
 */
'use strict';
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { execFileSync } = require('child_process');
const K = require('./28 causal checker.js');

const CORPUS_URL = 'https://public-aristo-processes.s3-us-west-2.amazonaws.com/wiqa_dataset_no_explanation_v2/wiqa-dataset-v2-october-2019.zip';
const RUN_FOLDER = path.join(__dirname, 'runs', '28 causal checker');
const SCRAMBLE_WORD = 'log 28';
const PARAGRAPHS = 5;
const PER_KIND = 10;
const KIND_NAMES = { INPARA_EFFECT: 'in paragraph', EXOGENOUS_EFFECT: 'from outside', OUTOFPARA_DISTRACTOR: 'unrelated' };

const scramble = id => crypto.createHash('sha256').update(`${SCRAMBLE_WORD}:${id}`).digest('hex');
const by_scramble = (a, b) => (scramble(a) < scramble(b) ? -1 : scramble(a) > scramble(b) ? 1 : 0);
const write_json = (file, value) => fs.writeFileSync(file, JSON.stringify(value, null, 2) + '\n');
const read_json = file => JSON.parse(fs.readFileSync(file, 'utf8'));

function read_test_rows(corpus_folder) {
  const file = path.join(corpus_folder, 'test.jsonl');
  if (!fs.existsSync(file)) {
    fs.mkdirSync(corpus_folder, { recursive: true });
    const zip = path.join(corpus_folder, 'wiqa.zip');
    execFileSync('curl', ['-sS', '-m', '120', '-o', zip, CORPUS_URL]);
    execFileSync('unzip', ['-o', '-q', zip, '-d', corpus_folder]);
  }
  return fs.readFileSync(file, 'utf8').split('\n').filter(Boolean).map(line => JSON.parse(line));
}

function pick(rows) {
  const by_paragraph = {};
  for (const row of rows) (by_paragraph[row.metadata.para_id] = by_paragraph[row.metadata.para_id] || []).push(row);
  const paragraph_ids = Object.keys(by_paragraph).sort(by_scramble).slice(0, PARAGRAPHS);
  const picked = [];
  for (const para_id of paragraph_ids) {
    for (const kind of Object.keys(KIND_NAMES)) {
      const ids = by_paragraph[para_id].filter(r => r.metadata.question_type === kind).map(r => r.metadata.ques_id).sort(by_scramble).slice(0, PER_KIND);
      for (const id of ids) picked.push(by_paragraph[para_id].find(r => r.metadata.ques_id === id));
    }
  }
  return { paragraph_ids, picked };
}

function select(corpus_folder) {
  const rows = read_test_rows(corpus_folder);
  const { paragraph_ids, picked } = pick(rows);
  const paragraphs = {};
  for (const id of paragraph_ids) {
    const row = rows.find(r => r.metadata.para_id === id);
    paragraphs[id] = row.question.para_steps.filter(s => s && s.trim());
  }
  fs.mkdirSync(RUN_FOLDER, { recursive: true });
  write_json(path.join(RUN_FOLDER, 'sample.json'), {
    corpus: 'WIQA, test part', corpus_url: CORPUS_URL, scramble_word: SCRAMBLE_WORD, paragraphs: paragraph_ids,
    questions: picked.map(r => ({ id: r.metadata.ques_id, paragraph: r.metadata.para_id, kind: KIND_NAMES[r.metadata.question_type] })),
  });
  write_json(path.join(corpus_folder, 'paragraphs.json'), paragraphs);
  write_json(path.join(corpus_folder, 'questions.json'), picked.map(r => ({ id: r.metadata.ques_id, paragraph: r.metadata.para_id, question: r.question.stem })));
  write_json(path.join(corpus_folder, 'answers.json'), Object.fromEntries(picked.map(r => [r.metadata.ques_id, r.question.answer_label])));
  return { paragraphs: paragraph_ids.length, questions: picked.length };
}

// Grade: the checker's answer from each paragraph's model and each question's reading, and the direct
// answer, both against people's answer.
function grade(corpus_folder) {
  const sample = read_json(path.join(RUN_FOLDER, 'sample.json'));
  const answers = read_json(path.join(corpus_folder, 'answers.json'));
  const models = read_json(path.join(RUN_FOLDER, 'models.json'));
  const readings = read_json(path.join(RUN_FOLDER, 'readings.json'));
  const direct = read_json(path.join(RUN_FOLDER, 'direct answers.json'));
  const prepared = {};
  for (const [id, raw] of Object.entries(models)) prepared[id] = K.prepare(raw);
  const results = sample.questions.map(q => {
    const model = prepared[q.paragraph];
    const reading = readings[q.id];
    const checked = !model ? { answer: 'unreadable', because: 'no model' }
      : reading === undefined ? { answer: 'unreadable', because: 'no reading' }
      : K.answer_what_if_question(model, reading);
    return {
      id: q.id, paragraph: q.paragraph, kind: q.kind, people: answers[q.id],
      checker: checked.answer, because: checked.because, route: checked.outcome ? checked.outcome.route.map(r => r.rule) : [],
      direct: direct[q.id] || 'missing',
    };
  });
  const model_problems = Object.fromEntries(Object.entries(prepared).map(([id, m]) => [id, m.problems]));
  const seeing = seeing_and_making(models);
  write_json(path.join(RUN_FOLDER, 'results.json'), { model_problems, seeing_and_making: seeing, results });
  return { results, model_problems, seeing };
}

// For each model: over pairs of things (A, B), how often seeing A at "more" goes with B moving, and how
// often making A "more" moves B. Pairs where seeing says yes and making says no are associations that
// are not causes in the model (the dark room and the lamp). Starts change one outside thing at a time.
function seeing_and_making(models) {
  const out = {};
  for (const [id, raw] of Object.entries(models)) {
    const model = K.prepare(raw);
    const names = Object.keys(model.things).filter(t => model.things[t].includes('more'));
    let seen_only = 0, made_only = 0, both = 0, pairs = 0;
    for (const a of names) for (const b of names) {
      if (a === b) continue;
      pairs++;
      const sd = K.seeing_and_doing(model, a, 'more', b, { one_at_a_time: true });
      const seen = Object.keys(sd.seeing).some(s => s !== 'usual');
      const made = K.what_if(model, { [a]: 'more' }, b).verdict === 'changed';
      if (seen && made) both++; else if (seen) seen_only++; else if (made) made_only++;
    }
    out[id] = { things: names.length, pairs, seen_and_made: both, seen_not_made: seen_only, made_not_seen: made_only };
  }
  return out;
}

function tables(results) {
  const kinds = ['in paragraph', 'from outside', 'unrelated'];
  const row = (label, list) => {
    const same = key => list.filter(r => r[key] === r.people).length;
    const unsettled = list.filter(r => r.checker === 'unsettled').length;
    const unreadable = list.filter(r => r.checker === 'unreadable').length;
    return `| ${label} | ${list.length} | ${same('checker')} | ${unsettled} | ${unreadable} | ${same('direct')} |`;
  };
  const lines = ['| Questions | How many | Checker same as people | Checker unsettled | Checker unreadable | Direct answer same as people |', '|---|---|---|---|---|---|'];
  for (const kind of kinds) lines.push(row(kind, results.filter(r => r.kind === kind)));
  lines.push(row('all', results));
  const people = results.reduce((acc, r) => { acc[`${r.people} / ${r.checker}`] = (acc[`${r.people} / ${r.checker}`] || 0) + 1; return acc; }, {});
  lines.push('', 'People\'s answer / checker\'s answer, how often:', ...Object.entries(people).sort().map(([k, n]) => `- ${k}: ${n}`));
  return lines.join('\n');
}

if (require.main === module) {
  const [command, corpus_folder] = process.argv.slice(2);
  if (!corpus_folder) { console.log('Use: select CORPUS_FOLDER | grade CORPUS_FOLDER'); process.exit(1); }
  if (command === 'select') console.log(JSON.stringify(select(corpus_folder)));
  else if (command === 'grade') {
    const { results, model_problems, seeing } = grade(corpus_folder);
    console.log('Seeing and making, per model:', JSON.stringify(seeing));
    for (const [id, problems] of Object.entries(model_problems)) if (problems.length) console.log(`Paragraph ${id} model problems: ${problems.join(' ')}`);
    console.log(tables(results));
  } else console.log('Use: select CORPUS_FOLDER | grade CORPUS_FOLDER');
}

module.exports = { pick, select, grade, tables, seeing_and_making, scramble, KIND_NAMES, RUN_FOLDER };
