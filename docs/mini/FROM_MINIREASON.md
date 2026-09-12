# What a sibling project has that this block does not

Read 12 September 2026, at the operator's suggestion, from
[AHepi/miniReason](https://github.com/AHepi/miniReason) at `3859f3d`.

**Provenance first, because it changes what these findings are.** miniReason extracts the same mini
engine from this repository at `b2a3328` — the commit immediately *before* this session's work began.
It is not a prior warning that went unread. It is a parallel line of work that ran on the same day
and reached the general statement of several problems while this block was hitting the particular
instances of them. That makes the agreement worth more, not less: two lines of work, one engine, and
the same defects named from opposite ends.

Six things are taken. Each says what it would cost here.

---

## 1. The measure's unit was never declared, and it changes the effect by a factor of three

> *"Compare corresponding stages and record actual tokens; equal ceilings are not equal spending."*
> — `docs/workflows/reason-use.md`

This block's pre-registered measure is **per model call**. It was never asked what a call costs. The
records carry every call's prompt and completion tokens, so the question is answerable without
spending anything. Over the first two repeats, which are complete for every arm:

| arm | finds | sends | tokens | per send | per 1,000 tokens |
|---|---|---|---|---|---|
| **R** no loop | 27 | 114 | 582,829 | **0.237** | **0.0463** |
| **F** full loop | 25 | 165 | 689,678 | 0.152 | 0.0362 |
| **W** wired | 27 | 165 | 810,223 | 0.164 | 0.0333 |
| **A** adjudicated | 29 | 170 | 716,556 | 0.171 | 0.0405 |

`R` leads the best loop arm by **1.39×** per send and by **1.14×** per token. Scaled to `A`'s token
spend, `R` would find about 33 against `A`'s 29.

The ordering does not move. The size of the gap moves by nearly three. **Per call is the
pre-registered figure and is the one that flatters the conclusion that the loop is not paying for
itself; per token is not pre-registered and is the one that goes against it.** Both belong in any
reading, with that sentence attached.

`W` is the arm this most changes. It spends the most tokens of any arm — 810k against `R`'s 583k —
and on a token basis it is **last**, behind the arm it is supposed to improve on.

**Cost here:** none. It is a second reading of records already taken. Done, and the reader should
carry both columns.

---

## 2. A matched control: the same calls, spent differently

miniReason's arms are `bare`, `native`, `matched`, `matched_native`, `mini`, `mini_native`
(`experiments/plans/E016-reason-original.json`). `matched` is the one this block does not have: the
**same call count as the loop arm, spent without the loop**.

`R` is not that. `R` is *fewer* calls, normalised afterwards. So "the loop does not pay for itself"
and "more calls do not pay for themselves" are not separated anywhere in this block, and the second
would explain the first without the loop being at fault at all.

**Cost here:** a fifth arm. Five calls a segment, no criticism stage — the conjecture and reading
run, then run again, and the best of the two is kept. New arm, new manifests, 240 calls a repeat.

---

## 3. A leakage audit, run before the arm runs

Every miniReason plan carries one (`experiments/plans/E018-reason-different.json`):

```json
"leakage_audit": {
  "checked_fields": ["source", "construction", "use_data", "use_questions", "system",
                     "instruction_respond", "instruction_use"],
  "excluded_identities": {"R-specific-new-target-rival": "36ff5cec…",
                          "whole_original_criticism": "1ac0e2a2…"},
  "inspection_limit": "Exact whole-occurrence and declared literal exclusions … no guarantee
                       against paraphrase …",
  "status": "DECLARED_LITERAL_EXCLUSIONS_PASSED"
}
```

**This would have caught ERRATA C18 before the block ran.** Arm `F` is the arm meant to withhold the
reading. A declared exclusion — *the reading's content appears in no field of F's prompt, here is its
hash* — fails immediately, because the executor copies the reading's kernel, expectation, both texts,
rewrite description and identity code verbatim into the row that `F`'s execution port renders.

Note what the audit does **not** claim: it states its own inspection limit, and it says the produced
account may itself repeat excluded material and that this is not censored. An honest check that names
what it cannot see.

**Cost here:** a preflight function and a field on the plan. Small, and it is the highest-value item
on this list.

---

## 4. The strong probe for whether carried content is used

> *"ECS §5.2 requires sensitivity to relevant content, not merely causal carriage of an artifact ID.
> A content-preserving recoding and a content-changing contrast on an active route are stronger
> probes than observing that a port was populated."* — `docs/lessons/semantics.md`

That sentence is the criticism of this block's central contrast. `F` → `W` is *observing that a port
was populated*. miniReason's `E016`–`E020` are the strong version, five plans over the same material:

| plan | what the carried account is |
|---|---|
| E016 | the original criticism |
| E017 | the same content, reviewed and **recoded** |
| E018 | a **different** relevant criticism |
| E019 | **omitted**, zero bytes |
| E020 | produced and **not returned** |

Recoding alone proves nothing — an arm that merely carries is unmoved by recoding too. The pair is
the test: if behaviour moves under *content change* and not under *recoding*, the content is being
used. Nothing in this block distinguishes a loop whose carried criticism is used from one where
something is merely present in the brief.

And the no-return arm is built the way this block's is not: **the call still runs and is still paid
for**, the field is simply empty, so the arms differ in the return path alone and not in cost.

**Cost here:** three more arms over the same material — recoded, different, omitted — plus a
no-return arm that keeps the call. It is the experiment this block should have been.

---

## 5. Two calls per artifact is a choice, and this block never made it

> *"Mini defaults to separate body and commitment calls. Original experiments declare
> `commitment_call: single` unless a test deliberately changes it; this makes call accounting
> explicit."* — `docs/lessons/configuration.md`

Every kind in this block except the reading uses the default two-call shape. The conjecture's second
call is a paid call in every segment of every arm, and **nothing reads what it produces** — the
`conj` port renders bodies only, and the install map reads the conjecture's body. It is dead text,
bought 192 times.

**Cost here:** one line per kind. It would cut the conjecture stage from two calls to one and remove
about a fifth of the block's sends, with nothing lost that anything reads.

---

## 6. Errata and lessons are different files, and the second kind does not exist here

miniReason splits `docs/errata/` (configurations, inquiry-preparation, interpretations, operations,
sources) from `docs/lessons/` (configuration, expressibility, method, operations, semantics). An
erratum is what went wrong with evidence; a lesson is what transfers.

This repository has nineteen errata and no lessons file. Item 4 above is exactly what that costs: the
general rule — *a populated port is the weak probe; recode and change the content* — is a lesson, and
there was nowhere to put it, so the same mistake was available to be made twice (C12, then C18).

**Cost here:** a directory and the discipline of asking, after each erratum, what transfers.

---

## What was not taken

Their **decision ledger** — an append-only receipt written *before* each action — is not adopted
here, and the reason should be recorded rather than implied: it is a large standing cost per
decision, and of this block's nineteen errata I can identify none that a receipt written beforehand
would have caught. C16 is the closest, and what failed there was a text replacement that silently did
nothing, which a receipt would have recorded as done. A check that reads back what it wrote catches
that; a receipt does not.

Their **native-reasoning arm** is not taken either, because this block's endpoint and model are
different and the comparison would need its own block. It is named in the research agenda as the
thing that would test whether the loop beats simply turning thinking on — which nothing here has ever
compared against, and which is the cheapest possible rival to a loop.
