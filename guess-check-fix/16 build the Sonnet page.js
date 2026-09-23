/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Builds "16 Sonnet page.html" from "16 Sonnet page template.html" by copying in the project's code
 * files, unchanged: the checker, the test worlds, the loop and the Sonnet guesser. The page then runs
 * the same code the tests run. Rebuild after changing any of those files:  node "16 build the Sonnet page.js"
 */
const fs = require('fs');
const path = require('path');
const here = __dirname;
const CODE_FILES = ['03 checker.js', '03 test worlds.js', '09 loop.js', '16 Sonnet guesser.js'];

function wrap(name) {
  const text = fs.readFileSync(path.join(here, name), 'utf8');
  if (/<\/script/i.test(text)) throw new Error(`${name} contains text that would end the page's code early`);
  return `<script>\n/* ===== ${name} ===== */\n(function () {\n  const module = { exports: {} };\n  const exports = module.exports;\n  const require = page_require;\n${text}\n  page_files[${JSON.stringify(name)}] = module.exports;\n})();\n</script>`;
}
const template = fs.readFileSync(path.join(here, '16 Sonnet page template.html'), 'utf8');
if (!template.includes('<!-- PROJECT CODE -->')) throw new Error('The template has lost its "PROJECT CODE" marker');
const page = template.replace('<!-- PROJECT CODE -->', CODE_FILES.map(wrap).join('\n'));
fs.writeFileSync(path.join(here, '16 Sonnet page.html'), page);
console.log(`Built "16 Sonnet page.html" (${Math.round(page.length / 1024)} KB) from ${CODE_FILES.length} code files.`);
