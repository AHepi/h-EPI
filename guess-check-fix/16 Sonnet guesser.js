/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Lets Claude Sonnet 4.6 play the guesser. The loop hands it the same messages it would hand
 * the small AI; this file sends them to Sonnet and gives back Sonnet's reply text.
 *
 * Two differences from the small AI, both forced by how Sonnet is reached from the page:
 *   - The small AI's server held every reply to a fixed shape. Sonnet can't be held that way,
 *     so this file adds one sentence to the last request, naming the shape to reply in.
 *   - Sonnet's replies are capped at 1000 tokens (about 700 words) by the page's connection.
 *     A reply cut off at the cap is counted, so a cut-off failure is not mistaken for a bad guess.
 *
 * If Sonnet refuses a request, it is tried again in a plainer form: the guide joined onto the
 * first request, and no randomness setting. Both forms are counted.
 *
 * make_sonnet_guesser(send) takes one function, send(body), that delivers a request and returns
 * the reply. The page passes one that uses its connection to Sonnet; the tests pass a stand-in.
 * Runs in Node (require) and in a browser (window.SonnetGuesser).
 */
(function (root, make) {
  const api = make();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.SonnetGuesser = api;
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  const MODEL_NAME = 'claude-sonnet-4-6';
  const REPLY_LIMIT = 1000;
  const SHAPE_SENTENCES = {
    'model': 'Reply with the whole model as JSON only, in this shape: {"things": {"THING": ["STATE", "STATE"]}, "events": ["EVENT"], "start": {"THING": "STATE"}, "rules": [{"name": "NAME", "when": ["CONDITION"], "then": "THING is STATE"}]}.',
    'new part': 'Reply with the new parts as JSON only, in this shape: {"new_things": {"THING": ["STATE", "STATE"]}, "new_start": {"THING": "STATE"}, "new_rules": [{"name": "NAME", "when": ["CONDITION"], "then": "THING is STATE"}]}. Give {} or [] for a part with nothing new.',
  };
  const wait = ms => new Promise(resolve => setTimeout(resolve, ms));

  function make_sonnet_guesser(send) {
    const counts = { requests: 0, replies: 0, cut_off: 0, plain_form: 0, refused: 0 };

    function full_form(messages, settings) {
      const system = messages.filter(m => m.role === 'system').map(m => m.content).join('\n\n');
      const rest = messages.filter(m => m.role !== 'system').map(m => ({ role: m.role, content: String(m.content) }));
      rest[rest.length - 1].content += `\n\n${SHAPE_SENTENCES[settings.reply_shape] || SHAPE_SENTENCES.model}`;
      const body = { model: MODEL_NAME, max_tokens: REPLY_LIMIT, messages: rest };
      if (system) body.system = system;
      if (typeof settings.temperature === 'number') body.temperature = settings.temperature;
      return body;
    }
    function plain_form(messages, settings) {
      const body = full_form(messages, settings);
      if (body.system) { body.messages[0].content = `${body.system}\n\n${body.messages[0].content}`; delete body.system; }
      delete body.temperature;
      return body;
    }

    async function guesser(messages, settings = {}) {
      let last_problem = null;
      for (let attempt = 1; attempt <= 3; attempt++) {
        const body = attempt === 1 ? full_form(messages, settings) : plain_form(messages, settings);
        if (attempt > 1) counts.plain_form++;
        counts.requests++;
        try {
          const data = await send(body);
          if (!data || data.error || !Array.isArray(data.content)) throw new Error(data && data.error ? (data.error.message || JSON.stringify(data.error)) : 'the reply had no text in it');
          counts.replies++;
          if (data.stop_reason === 'max_tokens') counts.cut_off++;
          return data.content.filter(b => b.type === 'text').map(b => b.text).join('\n');
        } catch (problem) {
          counts.refused++;
          last_problem = problem;
          await wait(attempt * 2000);
        }
      }
      throw new Error(`Sonnet could not be reached after 3 tries: ${last_problem && last_problem.message}`);
    }
    guesser.counts = counts;
    return guesser;
  }

  return { make_sonnet_guesser, MODEL_NAME, REPLY_LIMIT, SHAPE_SENTENCES };
});
