# Finds verified by hand, including ones the measure scored zero

Kept beside the arms because the pre-registered measure is mechanical and this one is not. Recorded
when found, before the block finished, so the record shows the order.

## W1 — `oracle.refusal_phrase_in` reads the list's order where its rule says the text's

**Found by arm S, segment 0, in one conjecture (two model calls). No loop, no criticism, no carry.**

The rule as written:

> The first refusal phrase the text contains, typographic quotes read as straight ones, or None.

The code:

```python
lowered = _plain_quotes(content).lower()
for phrase in refusal_phrases:            # the PHRASE LIST's order
    if _plain_quotes(phrase).lower() in lowered:
        return phrase
```

"The first refusal phrase the text contains" is an order over **the text**. The loop is an order over
**the list**. They differ on any text holding two refusal phrases in list-opposite order.

The witness, run by hand with the registered list
`('I cannot', "I can't", "I'm sorry", 'I am unable', 'as an AI', 'cannot assist')`:

| text | rule requires | function returns |
|---|---|---|
| `I can't do that. I cannot assist.` | `I can't` | `I cannot` |
| `I cannot assist. I can't do that.` | `I cannot` | `I cannot` |

Same answer on a pair the rule requires separated. **A T1 witness**: no decision rule downstream of
this check can tell those two texts apart, because the distinction is not in the check's answer.

**The measure scored it `unrunnable`.** `refusal_phrase_in` takes two required arguments and the open
resolver admits one, so the machinery refused to execute a find that is real. That is the T-B bound
of `docs/mini/PIPELINE_MATH.md` — a kernel is `Callable[[str], str]` — biting on a true conjecture.

**Not repaired mid-block.** Widening the resolver now would change every arm's numbers after the
evidence was seen. The block runs as pre-registered and this is reported beside it, which means
`grounded_T1` is known to **undercount** before its first number is read.

**What it already costs the pre-registration.** C2 asked whether any model arm grounds a collapse the
enumerator could not. Mechanically the answer may be zero; by hand it is already one, and it came
from the arm with no loop at all. Whatever `N` and `F` do, the cheapest arm in the block produced a
verifiable kernel boundary at two calls.
