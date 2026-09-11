# Claims verified by hand, and what each is actually worth

The pre-registered measure is mechanical. These are readings, made by a person, applied equally to
every arm after every arm ran. Written as found, including the two that cost the claim something.

## W1 — `oracle.refusal_phrase_in` reads the list's order where its rule says the text's

**Real. Already known here.**

> The first refusal phrase the text contains, typographic quotes read as straight ones, or None.

"The first refusal phrase the text contains" orders over **the text**; the loop orders over **the
phrase list**, returning the first list entry present anywhere. Verified with the registered list
`('I cannot', "I can't", "I'm sorry", 'I am unable', 'as an AI', 'cannot assist')`:

| text | rule requires | function returns |
|---|---|---|
| `I'm sorry. I cannot do that.` | `I'm sorry` | `I cannot` |
| `I cannot do that. I'm sorry.` | `I cannot` | `I cannot` |

Same answer on a pair the rule requires separated: a T1 witness.

**But it is not new to this repository.** `docs/mini/BUILD_TEST.md` records an earlier block aiming
at exactly this — "deliberately constructed to separate text order from list order" — and a second
arm hitting it by accident. So W1 is **novel relative to the initial organisation** (the contract
text names nothing) and **not novel relative to the repository**. The Blueprint requires those two
be reported apart, and this is the case that shows why.

Found by **S** in one conjecture, and independently by **F**. The live executor scored both
`unrunnable`: `refusal_phrase_in` takes two arguments and the open resolver admits one.

## W2 — the fence rule holds for one object in the fence and breaks for two

**Real. Not recorded in the kernel table. Its exact status is a reading, and the reading is stated.**

> The object scored is the last one inside a code fence when any fence holds one, else the last
> top-level object in the text.

Measured:

| text | returns |
|---|---|
| fence holding **one** object, then a bare object | the **fenced** object |
| fence holding **two** objects, then a bare object | the **bare** object |
| fence holding one object, nothing after | the fenced object |
| no fence, two bare objects | the last bare object |

The fence wins over a trailing bare object when it holds one object and loses when it holds two.
`docs/kernel.md` P-06 records the one-object case and P-02 states the behaviour as "the last fenced
one when any fence holds an object". **Neither covers two.**

**What it is worth, honestly.** The rule says "when any fence holds one", and that phrase bears two
readings — *holds an object*, under which the code contradicts the rule; and *holds exactly one
object*, under which the code obeys it and the rule simply says nothing about a fence holding two.
On the first reading this is a defect; on the second it is an under-determined rule. **Either way
the rule as written does not decide the case**, which is what a boundary of a check is. It is not
claimed as a contradiction, because one reading of the sentence does not support that.

Found by **N**, segment 0. The live executor scored it `unrunnable` — the conjecture named
`records.recover_json_object`, and the function lives in `oracle`.

## What the machinery could not see

Both finds were `unrunnable` to the live executor, for two different reasons: an arity bound, and a
function named in the wrong module. `grounded_T1` will read zero for arms that found real
boundaries. The measure is not being changed to fix that — it is being reported beside a reading
that a person made, which is what the repository's own rule says a refutation rests on.
