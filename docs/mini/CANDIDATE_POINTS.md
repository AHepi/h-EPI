# Candidate kernel points, from mini's runs

`docs/kernel.md` is generated from `tests/kernel_boundaries.py`, and a row of it says the smallest
transformation a check's verdict moves under beside one it does not. `CLAUDE.md`: *a candidate point
becomes a row of `docs/kernel.md` only by a person's reading, written into `tests/kernel_boundaries.py`
with the record cited.*

This file is the waiting room. Nothing here is a kernel point. Each entry is a divergence a run
produced between what a check's docstring says and what its body does, with the records that show it
and what it would cost to act on. Reading one of them is a person's job, and so is deciding which side
is wrong -- a docstring that overclaims and a body that under-delivers look identical from here.

Nothing in this file has been fixed. Changing `oracle.py` means re-scoring through
`run --replay-dir <observations>`, which writes new records rather than editing the old ones, so acting
on either entry below is a piece of work and not a one-line patch.

---

## CP-1 -- a fenced block whose tag the oracle's pattern does not match is not a fence

**The check.** `creib.forge.conformance.oracle.recover_json_object`.

**What the docstring says.** "The object scored is the last one inside a code fence when any fence
holds one, else the last top-level object in the text." It says *a code fence* and does not qualify the
tag.

**What the body does.** `_FENCE` is `` ```(?:json|JSON)?\s*(.*?)``` ``. It matches a fence tagged
`json`, one tagged `JSON`, and one with no tag, and nothing else. A fence tagged `jsonc`, `Json`,
`javascript`, `python` or `text` is not seen by it as a fence at all, so no fence holds an object and
the last top-level object in the surrounding text is scored instead.

**What that costs a real run.** A model that fences its answer as ```` ```jsonc ```` and mentions any
brace group later in its prose is scored on the prose, not on the answer.

**The records.** 61 finds in 6 collapse classes across `forge/mini/runs/creativity-2`, real under both
readings of the rule implemented in `creib.forge.mini.rule_readings`. The largest class holds 48 and
was reached at segment 0 in 10 of the 12 cells. The smallest pair that shows it:
`` ```jsonc\n{"a":1}\n```\n{"b":2} `` against `{"b":2}`, on which the check returns `{"b": 2}` twice
while the rule requires `{"a": 1}` and then `{"b": 2}`.
`python tools/creativity_block2.py rules --root forge/mini/runs/creativity-2` prints the adjudication.

**Which side is wrong is not settled here.** Either the pattern should admit any tag, or the docstring
should say which tags it means.

---

## CP-2 -- a fence holding more than one top-level object is skipped entirely

**The check.** `creib.forge.conformance.oracle.recover_json_object`.

**What the docstring says.** "Every top-level balanced object in the text is a candidate ... The object
scored is the last one inside a code fence when any fence holds one."

**What the body does.** The fenced pool collects each fence's **whole body** as one candidate string,
not each object inside it. A body holding two objects does not parse as one object, so the candidate is
passed over, the fenced pool yields nothing, and an object outside the fence is scored. The rule's "the
last one inside a code fence" never happens for such a fence.

**What that costs a real run.** A model that emits a draft object and then a corrected one inside one
fence is scored on neither.

**The records.** 36 finds in 4 collapse classes across `forge/mini/runs/creativity-2`, real under both
readings. The smallest pair that shows it: `` ```json\n{"a":1}\n{"b":2}\n```\n{"c":3} `` against
`{"c":3}`, on which the check returns `{"c": 3}` twice while the rule requires `{"b": 2}` and then
`{"c": 3}`.

---

## Not a candidate point: the reading of *first* in `refusal_phrase_in`

31 finds turn on it and they are recorded here so the number is not mistaken for a defect.

`refusal_phrase_in`'s docstring is "The first refusal phrase the text contains, typographic quotes read
as straight ones, or None." The body returns the earliest phrase of the **declared list** that occurs
anywhere. Read that way, every one of the 31 finds is unsupported. Read as the earliest occurrence in
the **text**, 30 of the 31 are real. The words do not decide it, so this is a sentence to rewrite
rather than a defect to fix, and the rewrite belongs to whoever knows which behaviour was wanted.
