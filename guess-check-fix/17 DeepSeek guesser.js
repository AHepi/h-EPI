/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Lets DeepSeek V4.1 Flash play the guesser. The loop hands it the same messages it hands any
 * guesser; this file sends them to DeepSeek and gives back DeepSeek's reply text.
 *
 * It works like the Sonnet guesser (file 16), with three differences:
 *   - DeepSeek is reached directly from this computer, not from a page in the chat.
 *   - DeepSeek thinks before it answers. Its thinking is not part of the reply; only its length
 *     is counted. The reply limit is set high enough that thinking does not cut the answer off.
 *   - The account key is read from the DEEPSEEK_API_KEY setting at the moment of each call.
 *     It is never written into a file, a record or an error message.
 *
 * Like the Sonnet guesser, it adds one sentence to the last request naming the shape to reply in,
 * counts cut-off replies, and tries a plainer form of the request if a request fails.
 *
 * make_deepseek_guesser(send, settings) takes one function, send(body), that delivers a request and returns
 * the reply. send_to_deepseek is the real one; the tests pass a stand-in. settings.effort sets how much
 * DeepSeek thinks: 'low', 'high' (DeepSeek's default) or 'max' (log 19); settings.reply_limit
 * raises the reply limit for one guesser. After each reply the guesser's
 * last_usage says how many tokens that one call took, so the loop can write it into the run's log.
 */
const SHAPES = require('./16 Sonnet guesser.js').SHAPE_SENTENCES;

const MODEL_NAME = 'deepseek-flash';          // DeepSeek's own name for DeepSeek-V4.1-Flash
const ADDRESS = 'https://api.deepseek.com/chat/completions';
const REPLY_LIMIT = 32000;                    // thinking and answer together
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));

async function send_to_deepseek(body) {
  const key = process.env.DEEPSEEK_API_KEY;
  if (!key) throw new Error('DEEPSEEK_API_KEY is not set');
  const reply = await fetch(ADDRESS, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${key}` },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(600000),
  });
  const text = await reply.text();
  try { return JSON.parse(text); } catch (e) { return { error: { message: `reply ${reply.status} was not JSON` } }; }
}

function make_deepseek_guesser(send = send_to_deepseek, guesser_settings = {}) {
  const counts = { requests: 0, replies: 0, cut_off: 0, plain_form: 0, refused: 0, thinking_characters: 0, answer_characters: 0, tokens_in: 0, tokens_out: 0 };

  function full_form(messages, settings) {
    const rest = messages.map(m => ({ role: m.role, content: String(m.content) }));
    // A reply shape of 'none' (log 19: direct answers) adds no sentence about the model's shape.
    if (settings.reply_shape !== 'none') rest[rest.length - 1].content += `\n\n${SHAPES[settings.reply_shape] || SHAPES.model}`;
    const body = { model: MODEL_NAME, max_tokens: guesser_settings.reply_limit || REPLY_LIMIT, messages: rest };
    if (guesser_settings.effort) body.reasoning_effort = guesser_settings.effort;
    if (typeof settings.temperature === 'number') body.temperature = settings.temperature;
    return body;
  }
  function plain_form(messages, settings) {
    const body = full_form(messages, settings);
    const system = body.messages.filter(m => m.role === 'system').map(m => m.content).join('\n\n');
    body.messages = body.messages.filter(m => m.role !== 'system');
    if (system) body.messages[0].content = `${system}\n\n${body.messages[0].content}`;
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
        const choice = data && Array.isArray(data.choices) ? data.choices[0] : null;
        if (!choice || !choice.message) throw new Error(data && data.error ? String(data.error.message || 'an error reply') : 'the reply had no text in it');
        counts.replies++;
        if (choice.finish_reason === 'length') counts.cut_off++;
        counts.thinking_characters += (choice.message.reasoning_content || '').length;
        counts.answer_characters += (choice.message.content || '').length;
        if (data.usage) { counts.tokens_in += data.usage.prompt_tokens || 0; counts.tokens_out += data.usage.completion_tokens || 0; }
        guesser.last_usage = { tokens_in: (data.usage && data.usage.prompt_tokens) || 0, tokens_out: (data.usage && data.usage.completion_tokens) || 0 };
        return choice.message.content || '';
      } catch (problem) {
        counts.refused++;
        const key = process.env.DEEPSEEK_API_KEY;
        const message = String(problem && problem.message || problem);
        last_problem = key ? message.split(key).join('[key removed]') : message;
        await wait(attempt * 3000);
      }
    }
    throw new Error(`DeepSeek could not be reached after 3 tries: ${last_problem}`);
  }
  guesser.counts = counts;
  guesser.effort = guesser_settings.effort || 'high';
  return guesser;
}

module.exports = { make_deepseek_guesser, send_to_deepseek, MODEL_NAME, REPLY_LIMIT };
