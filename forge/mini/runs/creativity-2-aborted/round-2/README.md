# Arm A's first repeat, discarded because its brief grew twice as fast as the arms it is compared with

Fifteen segments. It stopped at segment 14 of 16 with `MINI_MANIFEST_INVALID`: the carried brief had
reached **8310 characters** and the manifest schema caps `problem` at 8192.

## What the length was made of

`_install_text` kept **one** criticism — the last — and **every** landed refutation, from every
segment, forever. Arm A is the only arm that produces refutations, so it was the only arm whose brief
carried an ever-growing block the others did not have. At segment 14:

| arm | brief at s01 | at s07 | at s13 |
|---|---|---|---|
| R | 991 | 2276 | 3565 |
| F | 2077 | 3034 | 4217 |
| W | 3037 | 3846 | 5530 |
| **A** | 1832 | **5152** | **8075** |

So "the attacks land" and "the brief is half again as long" were one treatment. That is an
inconsistency in the install map's own design rather than a property of adjudication, and it makes
`W` → `A` uninterpretable whichever way it falls.

## The repair

The standing refutations now come from the **last** previous segment only, exactly as the criticism
does, and a declared ceiling of 7800 characters drops the oldest "already run" lines first if a brief
still grows past it. The ceiling applies identically to every arm.

Regenerating every brief in the block under the repaired map leaves **R, F and W byte-identical**
(16/16, 16/16, 15/15) and changes **A from segment 2 onward** (2/15 identical). So only this arm's
repeat was discarded; the other arms' records are the block's.
