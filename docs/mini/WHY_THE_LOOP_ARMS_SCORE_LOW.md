# Why A, W and F score low

Asked 12 September 2026. The short answer is that **two of the three do not find less**, and the
measure was answering a different question from the one it was read as answering.

Every figure here is counted from `forge/mini/runs/creativity-2/`, with the eleven finds ERRATA C21
recovered included. Arm `A`'s third repeat is nine segments of sixteen, so the two-repeat table is
the one to read for `A`.

---

## 1. Each segment produces exactly one claim, so count per segment

This removes the call count entirely. It is the measure that was never taken.

| arm | segments | finds | per segment | calls per segment |
|---|---|---|---|---|
| **R** no loop | 48 | 46 | **0.958** | 3.56 |
| **F** full loop | 48 | 42 | 0.875 | 5.21 |
| **W** wired | 48 | 43 | 0.896 | 5.15 |
| **A** adjudicated | 41 | 39 | **0.951** | 5.32 |

First two repeats, complete for every arm: **R 0.938, A 0.938** — identical — with `W` 0.906 and
`F` 0.844.

**`A` finds exactly as often per segment as the arm with no loop at all.**

---

## 2. So `A`'s per-call deficit is the call count, and nothing else

First two repeats: `R` 30 finds from 114 calls, `A` 30 finds from 170.

- `R`'s lead per call: 0.26316 / 0.17647 = **1.4914**
- Calls per segment: 5.3125 / 3.5625 = **1.4912**

The same number to four figures — and that is **arithmetic, not a second piece of evidence**. When
two arms find the same amount per segment, the per-call ratio *is* the inverse call ratio. It is
worth stating only because it locates the entire `R`-over-`A` gap in one place: the criticism stage
costs two calls and produces no finds of its own.

"`A` scores badly per call" is therefore not a finding about criticism, adjudication, attack
relations or carried standing. It is the sentence *the criticism stage costs two calls*, restated as
a rate.

---

## 3. `F` and `W` do find less, and all of it is claims that broke

| arm | find | separates | over-sensitive | **broke** | total |
|---|---|---|---|---|---|
| R | 43 | 2 | 0 | **3** | 48 |
| F | 37 | 2 | 0 | **9** | 48 |
| W | 41 | 3 | 2 | **2** | 48 |
| A | 38 | 2 | 0 | **1** | 41 |

`F`'s rate of claims that were *wrong* — the check separated where the claim said it would not — is
2 of 48, the same as everyone's. Its entire deficit is 9 claims that **broke**: the check raised, or
the expectation never arrived. Not a worse conjecture. A claim the machinery could not put to the
test.

There is no trend with position: `F` breaks 2, 2, 4, 1 across the four quarters of a run, so this is
not the carried brief degrading as it grows.

---

## 4. What breaks a claim, exactly

The double-escaping of ERRATA C21, and it is decisive:

| | claims that broke |
|---|---|
| readings whose fields carry literal `\n` or `\"` | **12 of 16** |
| readings whose fields do not | **3 of 169** |

And the translator picks it up from the conjecture it is rendering:

| | reading came out escaped |
|---|---|
| conjecture contained literal escapes | 15 of 86 |
| conjecture did not | 1 of 99 |

So the chain is: the conjecture writer escapes its own quoted texts → the translator sometimes
carries that through → the check runs on text full of backslashes → it raises → the claim scores
zero.

`F`'s conjectures carry literal escapes in **32 of 48** segments (67%), against `R` 40%, `W` 35%,
`A` 44%, and it is elevated in all three of its repeats — 56%, 62%, 81%.

---

## 5. What this does NOT establish

**Why `F`'s conjectures escape more.** The spread *within* an arm across its three repeats is as
large as the gap *between* arms: `W` runs 7/16, 10/16, **0/16**; `A` runs 1/16, 11/16, 6/9. Three
repeats cannot separate a real arm effect from draw variance on a rate that moves that much. `F`
being high in all three is suggestive and it is not a measurement.

A successor that wanted to settle it would refuse a field value containing literal escape sequences
at the format layer — `format.fields` already exists (C13) and the check is two lines — and then the
question disappears rather than being answered, which is the right outcome for a defect.

**That the arms differ in yield at all, once the machinery works.** Score every broken claim as
though the machinery had held and all four arms land within one segment of each other: `R` 46/48,
`W` 43+2 = 45/48, `A` 39+1 = 40/41, `F` 42+3 = 45/48 (three of `F`'s nine break on texts where the
check legitimately raises, which is the model's choice and not a defect). That is not a measurement
either — it is an upper bound assuming every broken claim would have been a find — but it bounds how
much of the difference can be about the loop at all.

---

## 6. What it does establish, and what the pre-registration predicted

Per segment, the pre-registered ordering **holds, monotonically**:

**F 0.875 < W 0.896 < A 0.951**

P1 (`W` beats `F`) and P2 (`A` beats `W`) both hold on this measure, and both were invisible under
the per-call figure that was actually reported. But read what they are made of: `F` → `W` closes a
gap of 0.021 while broken claims fall from 9 to 2, and `W` → `A` closes 0.055 while they fall from 2
to 1.

**Each addition to the loop is recovering claims the loop's own machinery broke, not producing new
finds.** And `A`, having recovered all of it, arrives exactly at the rate of the arm that never had a
loop — at 49% more calls per segment.

That is the answer. Not *the loop finds less*: the loop finds the same, loses some of it to a defect
in a stage every arm shares, and spends half again as much getting there.
