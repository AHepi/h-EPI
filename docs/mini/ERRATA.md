# Errata: every oversight in the mini investigation of 11 September 2026

Written at the operator's request, after CREATIVITY-ARMS-1 returned a result that does not settle
the question it was built to settle. Ordered by what each one cost, not by when it was found. Errors
I introduced are marked **mine**; defects I found in existing machinery are marked **found**.

The point of the list is the pattern at the end, not the count.

---

## A. Errors that inverted or withdrew a conclusion

### A1. "The return path alone buys nothing" — withdrawn (**mine**)

Stated after `N` and `F` came back equal, twice. It is wrong. `F` was told *"Do not repeat any pair
above"* and repeated **twice**; `N`, never told, repeated **once**; `W`, with the identical carry,
repeated **zero** times and reached the widest coverage in the block. The carry was never inert — it
was **obeyed toward the wrong target**, because it carried a confident misdiagnosis from a critic
that could not see the layer the errors were in.

**What it cost:** two pre-registered comparisons read as evidence against serialisation when they
were evidence about what serialisation was carrying.

### A2. "C6 fails, 0/8 — the mechanism is being shown, not citing" (**mine**)

The test searched for **reading** artifact ids. The critic refers to the reading through the
**conjecture's** id, because the reading renders as that conjecture's commitments line. Measured for
any artifact id of the run: `W` cites in **7/8** and discusses the reading in **7/8**; `F` in
**0/8**. **C6 holds.**

**What it cost:** a pre-registered gate was reported as failed, which by its own terms invalidated
the arm's headline result. The result was fine; the instrument was not.

### A3. "The enumerator grounded none because it writes no prose" (**mine**)

The real reason: **458 of its 460 collapses are on functions whose entire range over the fourteen
seeds is one value.** `control_kind` returns `None` for every seed. A constant function collapses
every pair trivially. It grounded nothing because it *found* nothing.

**What it cost:** the baseline was described as showing "the model contributes the reading over a
good search". It shows no such thing — the search was bad, and what the model contributes is
**choosing inputs that make a function vary at all**.

### A4. `grounded_T1` is a measure the baseline cannot score on by construction (**mine**)

It requires quoting six consecutive words of a docstring. A mechanical enumerator writes no prose, so
its score is zero *by definition*, not by measurement. A control that cannot score is not a control.

---

### A5. Every per-call figure in block 1 was low by between 1.7 and 2.0 (**mine**)

`ARMS` counted model **stages** and the table called them **calls**. A kind whose `commitment_call`
is `two` costs two calls; the conjecture and the criticism are both `two`, the reading is `single`.
And a refused submission is a call the arm paid for, which the arms did at different rates. Counted
from the records:

| arm | reported calls | actual | refusals | witnesses | per call, reported | per call, actual |
|---|---|---|---|---|---|---|
| S | 2 | **4** | 1 | 1 | 0.50 | **0.25** |
| R | 12 | **24** | 6 | 4 | 0.33 | **0.167** |
| N | 24 | **47** | 7 | 3 | 0.12 | **0.064** |
| F | 24 | **42** | 2 | 3 | 0.12 | **0.071** |
| W | 24 | **43** | 3 | 7 | 0.29 | **0.163** |
| A | 24 | **41** | 1 | 5 | 0.21 | **0.122** |

**What it cost:** one stated conclusion. *"`W` does not beat repetition: 0.29 per call against `R`'s
0.33"* becomes **0.163 against 0.167** — level, not behind. The rest of the ordering survives. The
witness counts were never wrong; the denominators were.

## B. Machinery defects that cost runs

| id | defect | whose | cost |
|---|---|---|---|
| **M21** | ARCH-SWEEP's instruction named kernels without their `conformance.kernel.` prefix | mine | 9 of 21 proposals lost, at a rate that varied by architecture — a break correlated with the treatment |
| **M22** | the pair-execution seat read "this cycle" whatever window its stage declared | found | **18 of 36 architectures — exactly half, and the lagged half** — produced nothing, which would have manufactured the monotone decline K3 exists to test for |
| **M23** | the use-test's mini arms are schema-forbidden from naming three of six kernels, while the arm they are compared against is not | found | on instance 3 the seeded defect was in a kernel the mini arms could not name. **"Nought of three, for every arm" is not a comparison there.** |
| **M24** | ARCH-SWEEP's pre-registration said "No grid" and its instruction carried one | mine | attribution of K1's failure to the enumeration — later **withdrawn** by OPEN-SWEEP-1 |
| **M25** | `mini.adjudication.v1`-class seats registered by tests and not by the tool | mine | 36 runs of OPEN-SWEEP spent; later 3 segments of arm A |
| **M26** | the test written to catch M25 was defeated by M25's own mechanism — registration is a process-global side effect, another test imported the module, so it passed in the suite and failed alone | mine | arm A's first three segments, and a false sense that the class was closed |
| — | the reading stage wrote an **artifact id** into the `kernel` field: the instruction said `"<id>"` and an id was sitting in its context | mine | 9 of 11 executions in the first arms block |
| — | the runner stepped over a segment that died at its first stage, in silence | mine | `F/s01` produced nothing and `F/s02`'s carry held only `s00`; the arm whose point is accumulation did not accumulate |
| — | the two open-kernel widenings (bind a second argument, relocate a module) **did not compose**: relocation rejected any candidate that needed the binding, which is exactly the case both were written for | mine | a whole rerun that starved the loop again, for a new reason |
| — | the first status computation marked a target refuted and never unmarked it, making refutation **absorbing** | mine | caught before it ran; it would have made the fallibilist property untrue |

---

## C. Design oversights, measured against the operator's harness spec

### C1. Commitments are written by every seat and read by almost none (**mine**)

Every kind takes `commitment_call: two`, so all five write one. Only the **reading's** is consumed.
The conjecture's is rendered nowhere (`conj` showed bodies only). The criticism's is consumed by no
kind at all — `crits` was declared as a port type and nothing read it. **Three of five streams were
dead ends**, and the critic had no port on `reads`, so it could not see the commitment saying what
the conjecture was *taken* to claim.

### C2. Mini has no attack relation, so criticism could not land (**found**)

The spec: *"an attack edge exists where an artifact carries a warrant against a target"*, and
*"a bare verdict is never an edge"*. Mini had only bare verdicts. No warrants, no targets, no
computed status — nothing could be refuted or reinstated, so criticism could act **only** by being
rendered into the next prompt. The spec names the failure surface exactly: criticism *"ritualizes…
leaves commitments unevaluated, never reinstates, never attacks a test"*, and grounded semantics is
*"exactly as skeptical as its attack supply"*. **Mini's attack supply was zero** — which is the
single best explanation for every flat loop arm in this session.

### C3. Type dispatch where the spec is interface dispatch (**found, unrepaired**)

*"Artifacts are untyped. There is NO `kind` field. Dispatch is on interface structure only."* Mini
dispatches entirely on kind, through ports a manifest declares. Arm A adds an attack relation on top
of that, and therefore still cannot let an artifact attack something merely because it carries a
warrant against it.

### C4. Commitments have no `eval`, no budget, and no verdict (**found, unrepaired**)

The spec's commitment is `{eval: program|rubric|predicate, budget, observation_valued}` with
`V(κ,c) ∈ {pass, fail, overrun}`, and demarcation is `crit(a) ⇔ interface.commitments ≠ ∅`. Mini's
commitments are prose or a JSON blob. There is no decidable test attached to them, so "attack
surface" is a metaphor here rather than a count.

### C5. No validity node, so a **test** cannot be attacked (**found, unrepaired**)

The spec makes every demonstrative warrant carry an attackable `validity_node`, and any attacker of
it attacks the warrant. Arm A can attack an artifact and cannot attack the check that judged it. The
one criticism in this block that most deserved to land — that the executor's arity bound refused a
true conjecture — has nowhere to go.

### C6. The criticism commitment had no format schema, so it mostly wasn't one (**mine**)

Arm A's instruction asks for `{"attacks", "ground", "why"}` as JSON. **Four of eight criticisms wrote
prose instead**, so the attack machinery engaged in under half the arm. DeepReason's note gives the
shape of the fix and the trap in one line: a required closed field *without* an escape road takes
fabrication from 0–2% to 100%, and prompt-level instruction is **voided** by the schema. The escape
road (`cannot-tell`) exists in the ground enum; the schema that would enforce the shape does not.

### C7. No stochastic floor by design (**mine**)

DeepReason: *"nothing is interpretable without the no-criticism control arm and the stochastic
floor."* `R` is the no-criticism arm by design; `N` turned out to be the floor **by accident**,
because not installing means its eight segments run a byte-identical brief. Relying on an accident
is not a design.

### C8. Relative novelty is trivially satisfied and was reported anyway (**mine**)

The contract names no check, so every target reached is novel relative to the initial organisation.
It discriminates nothing. It was pre-registered as a measure and should have been pre-registered as
a definition.

### C9. The arity bound refused the finds, and the measure never recovered (**mine, stated**)

`Kernel.verdict: Callable[[str], str]` refused every conjecture about `refusal_phrase_in`, which is
what the model kept finding. `grounded_T1` read zero for arms that had found real boundaries. The
post-hoc verifier repaired the reading but not the arms, so the pre-registered measure is known to
undercount and was reported beside a hand reading throughout.

### C10. The old `ARCHITECTURE_SPACE.md` was wrong on three counts (**mine**)

It pinned a terminal stage (`n!` orderings, not `(n-1)!`), held the artifact kinds fixed, and held
the wiring fixed for a whole run. The third removed the thing the Blueprint locates creativity in.

### C11. My own hand-verification of W2 was criticised by the machine and may be wrong (**mine**)

`W/s02`'s critic argues the fence rule is determinate under *"holds exactly one object"*, that the
code obeys it, and that the conjecture misread it. That is a direct criticism of this session's own
W2 finding, produced by the thing under test, and it has not been adjudicated.

---

### C12. "Wired" never wired anything: `W`'s critic never saw a reading (**mine**)

Found while building block 2, by reading the run headers rather than the source.
`_kinds_and_ports` declared a `reads` input port on `W`'s and `A`'s criticism **kind**, and
`manifest()` then built the criticise **stage** with `ports: ["source", "conj", "execs"]` in every
arm. Only a stage's ports are rendered. So the readings were never in the prompt, in either arm, in
any of the sixteen segments. `STAGE_ENTERED` says so in every record:

```
W/s00 criticise {"ports": ["source", "conj", "execs"]}
A/s00 criticise {"ports": ["source", "conj", "execs"]}
```

What actually differed between `F` and `W` was two things bundled: the `conj` port type rendered
`list_bodies_and_commitments` where `F` rendered `list_bodies`, and the instruction told the critic
to attack a reading it could not see — naming its artifact id, quoting its words, saying whether it
renders the prose.

**What it cost:** the one effect this session claimed to have established. `W` did double `F`'s
yield, and that number stands; what it is an effect *of* does not. It is now unattributed between
three candidates — seeing the conjecture's commitments, being asked to separate a defect in the
reading from a defect in the conjecture, and the readings themselves, which were absent. The third
was the one I named, and it is the only one that was definitely not operating.

**What it means for what I wrote:** `docs/mini/CONFIG_MAP.md`'s `CFG-INPUT-PORTS`, the registry
entries for `CONF-ARMS-W` and `CONF-ARMS-A`, and my summary of C5 and C6 all describe a critic
reading the readings. None of them did. The numbers in those entries are what the records say; the
mechanism beside them is withdrawn. Block 2 declares the port on the stage and holds the conjecture
render constant, so `F`→`W` there is the wiring change alone.

**My own rule, broken.** `docs/mini/CONFOUNDS.md` opens: *"Two settings that move together cannot be
told apart by a result that moves with both."* I wrote that, and the arm I wrote it about varied two
settings together and named the effect after a third that was not varying at all.

### C13. Nine of thirty-nine readings returned no texts, and nothing could see it (**found**)

The translator's three texts ride as the kind's **own optional fields**, because nesting them in the
commitments string needs a second level of escaping (register M13). The format layer read `body` and
`commitments` and **nothing else**, so a reply carrying `kernel` and `expect` and no pair at all
passed every check. The executor then called the claim `unrunnable` — which reads as the executor
refusing something, not as an empty reply.

It is **9 of 39** across block 1, and not evenly spread:

| arm | readings carrying the texts | readings that dropped them |
|---|---|---|
| S | 1 | 0 |
| R | 4 | **2** |
| N | 4 | **4** |
| F | 6 | **2** |
| W | **8** | **0** |
| A | 7 | **1** |

The reading stage is byte-identical in every arm — same kind, same instruction, same port. So this
is draw variance in one stage, and it lands directly on the headline measure: a textless reading
yields nothing. Witnesses per reading that carried its texts: `R` 4/4, `W` 7/8, `A` 5/7, `N` 3/4,
`F` 3/6. **The gap between `W` and `N` largely closes.**

**What it cost:** an uncontrolled source of every arm difference in the block, running under the one
positive result. Repaired in the machine rather than the prompt: `format.fields` declares a shape for
a kind's own fields, a missing one is a refusal with the shape rendered rather than a skip, and
**ALM-TRANSLATOR-DROPPED-THE-TEXTS** names the mode in a finished segment. The first live segment of
block 2 hit it, the alarm stopped the arm after four calls, and that is how it was found.

### C14. The source a seat is shown had no addresses, and one body was not even the subject (**found**)

The `mini.kernel-source.v1` seat shows eight function bodies. Seven are
`creib.forge.conformance.oracle`; the eighth, `_grounding_kernel`, is
`creib.forge.mini.conformance_kernels` — **mini's own wrapper, not the harness under test**. None of
the eight carried the module it lives in, and the brief asks the seat to name a function by its full
dotted path in one of fifteen `creib.forge.conformance.*` modules.

So the seat was shown bodies and asked for addresses it had not been given. Across thirty-four
segments of block 2's first repeat it wrote each of the two runnable functions under **both**
`oracle.` and `records.`; the executor's relocation absorbed that, which is why it stayed invisible
until it hit the one body relocation cannot save. Arm `A` then named `_grounding_kernel` three
segments running and the arm stopped.

Worse, the annotation makes a second thing visible that nothing said before: of the eight bodies
shown, **three cannot carry a runnable claim at all** — `parse_content` takes two required
arguments, `_span_occurs` takes three, `_grounding_kernel` is not the harness's, and a kernel is one
string. The other five are nameable and runnable, `refusal_phrase_in` among them because
`SECOND_ARGUMENT` in `openkernels.py` binds its second argument. That is CON-ARITY-HIDES-FINDS as a
number rather than a worry: three of eight of what the seat is shown is unusable and nothing told it
so.

*(Corrected 11 September, after the count was checked by running it. The first version of this
entry, and the commit message that carries it, say "four cannot carry a runnable claim" and "half of
what the seat is shown is unusable". Both are wrong: it is three of eight, not four. The claim was
asserted from reading the list rather than from running it, which is the rule this repository has
about counting — **"Count it, don't claim it"** — broken on the entry that exists because somebody
did not check what the seat could reach.)*

**What it cost:** thirty-four segments of a repeat, set aside at
`forge/mini/runs/creativity-2-aborted/round-1/` rather than counted. **Found by the streak guard
added four hours earlier**, and diagnosed correctly, in prose, by the arm's own critic — which then
committed `cannot-tell` and so never landed the attack.

**Repaired:** each body now carries the module it lives in and says which of three it is — nameable,
nameable but unrunnable with the reason, or not the harness's at all. A test resolves every `open:`
name the source offers, so a name the seat is told to write and the executor refuses fails the suite
rather than a run.

### C15. The install map kept one criticism and every refutation, so arm A's brief grew twice as fast (**mine**)

`_install_text` carries the **last** criticism and, for an arm that adjudicates, **every** landed
refutation from every previous segment. Only arm `A` produces refutations, so only arm `A` carried a
block that grew without bound — and it is the arm `W` is compared with.

| arm | brief at s01 | at s07 | at s13 |
|---|---|---|---|
| R | 991 | 2276 | 3565 |
| F | 2077 | 3034 | 4217 |
| W | 3037 | 3846 | 5530 |
| **A** | 1832 | **5152** | **8075** |

At segment 14 of 16 it reached **8310 characters** against the manifest schema's cap of 8192 and the
arm stopped on `MINI_MANIFEST_INVALID`, three attempts running.

Two things are wrong with that and only one is the crash. *"The attacks land"* and *"the brief is half
again as long"* were **one treatment**, so `W` → `A` — the block's whole experiment — was confounded
whichever way it fell. And a brief with no ceiling makes the arm's length a function of how well its
critic is doing, which is not a variable anybody declared.

**Repaired:** the standing refutations come from the last previous segment only, exactly as the
criticism does; and a declared ceiling of 7800 characters drops the oldest "already run" lines first,
identically on every arm, saying in the brief how many were dropped.

**What it cost:** fifteen segments of arm `A`, discarded at
`forge/mini/runs/creativity-2-aborted/round-2/`. Regenerating every brief in the block under the
repaired map leaves `R`, `F` and `W` **byte-identical** — 16/16, 16/16, 15/15 — and changes `A` from
segment 2 on, so the other arms' records are still the block's. That check is the reason only one
arm was re-run rather than all four.

### C16. Two edits to the pre-registration silently did nothing, and a commit said otherwise (**mine**)

Amendments 1 to 3 of `docs/mini/CREATIVITY_ARMS_2.md` were written with a text replacement anchored
on the heading `## What is being asked`. That document has no such heading. Both replacements
returned the unchanged text, neither raised anything, and the commit that carried them says in its
message: *"The pre-registration carries the amendment."* It did not, for two days of work, and the
fourth amendment — written the same way, anchored on the third — did not either.

**What it cost:** nothing to the records, which are unaffected, and everything to the thing a
pre-registration is for. A block whose amendments exist only in a commit message is a block whose
plan cannot be checked against what ran.

**Repaired:** the amendments are now written into the document, with what each cost and what was set
aside because of it. The commit message that claimed it stays as it is, because published history is
not rewritten, and the correction says so instead.

**The rule this broke.** Every other `.replace` in this session's tooling carries an `assert … in s`
before it. These two did not, because they were typed into a shell heredoc rather than a file, and a
one-off felt like it did not need one. A silent no-op is the one failure a text replacement has, and
it is the reason the check exists.

### C17. The block's own reader counted runs that never finished (**found, by a check I set running**)

`_segments` asked only whether a root held a `log.jsonl`. A transport failure leaves a root holding a
conjecture, a reading and no execution — the driver sets it aside as `<name>.deadN` and runs the
segment again — and those set-aside roots sat **inside the block's own records tree**, where the
glob found them. So:

| cell | segments the reader counted | segments that finished |
|---|---|---|
| R.r1 | **20** | 16 |
| W.r1 | **20** | 16 |
| A.r1 | **20** | 16 |
| F.r2 | **19** | 16 |

Both `model_calls` and `executor_rows` carried the difference, and so would any per-call figure read
off them. **The numbers already reported are unaffected**, because every reading given so far was of
the first repeat, whose three set-aside roots happen to hold no log at all — but that is luck, not
design, and a reading of the second or third repeat would have been wrong.

Two things were wrong, not one. The reader's test was too weak (*a log exists* rather than *the run
reached its end*), and the set-aside roots were in the wrong place. A records directory is read by
enumeration; a root that is neither a finished record nor an error naming one is a thing every reader
has to know to skip, and nothing knew.

**Repaired:** `_segments` requires `RUN_ENDED` and refuses a `.dead` name; `_set_aside` moves a root
out of the block entirely, to `forge/mini/runs/creativity-2-aborted/dead/`; the eighteen existing
ones were moved there with a note saying what they are; and three tests pin it, one of which asserts
that the block tree holds no set-aside root at all.

**How it was found.** By the completeness critic in the verification I ran over the description of
this block's wiring — an agent asked what the claim list left out, read `_segments`, and noticed that
its glob matches a name the driver itself creates. It is the second defect in this block found by a
check rather than by a person, and the first found in the measurement path.

### C18. Arm F's critic already sees everything the reading committed to (**found, by a check I set running**)

The block's first prediction is that `W` beats `F` because `W`'s critic is shown the reading and
`F`'s is not. `F`'s critic **is** shown the reading's content — all of it — inside the execution's
commitments line, because the `execs` port renders with `list_bodies_and_commitments` and
`execute_pairs_with` copies the reading's fields into each row:

```
commitments: {"executions": [{"proposal": "c20ac90c7d7be592",
  "kernel": "open:creib.forge.conformance.oracle.recover_json_object",
  "expect": "moves", "input": "```python\n{\"x\": 1}\n```\n{\"y\": 2}",
  "rewritten": "{\"y\": 2}", "rewrite": "moves",
  "before": "({'y': 2}, ())", "after": "({'y': 2}, ())", "as_expected": false}]}
```

That is the reading's kernel, its expectation, both of its texts in full, its rewrite description,
**and its own sixteen-character identity code** — the same code `W` prints in brackets beside it.

So what `W` actually adds over `F` is: the reading's **prose body** (the translator's note on what it
was unsure of), the same content a second time under a `Readings` heading, and a bracketed label the
instruction can tell the critic to name. Not "the critic can see what the reading claimed" — it
already could.

**What it costs:** the pre-registration's `F` → `W` contrast is much narrower than it says, and so is
whatever `W` beating `F` turns out to mean. It does beat `F`, on every repeat so far; what it beats it
by is a labelled copy and a prose note, not access to the claim.

**Not repaired, and not repairable inside this block.** Narrowing it would mean changing what the
`execs` port renders, which changes `F`, `W` and `A` together and makes a fourth block. Registered as
CON-EXECS-CARRIES-THE-READING so that nothing built on `F` → `W` is read as more than it is.

**How it was found.** The same completeness critic that found C17, reading `execute_pairs_with`
against a stored `F` prompt. Three blocks have now been designed around this contrast and none of the
three noticed that the row the executor writes carries the proposal it ran.

### C19. The grounding filter has never once removed anything (**mine, stated**)

`grounded_T1` is the block's headline measure: a confirmed collapse **plus** the conjecture's prose
quoting six or more consecutive words that occur verbatim in that function's own docstring or source.
The pre-registration calls it *"the one the enumerator cannot score on, by construction"* and
*"where a model can contribute something the host cannot do for free"*.

Across **twelve cells of twelve**, `grounded_T1` equals `collapse_T1` exactly. Every confirmed
collapse passed the filter. It has never excluded a single row.

Half of what that sentence claims still holds: the mechanical enumerator scores zero on it because it
writes no prose, so the measure does separate an arm that writes prose from one that does not. What
does **not** hold is the implication that it separates well-grounded claims from poorly grounded ones
*within* the model arms. It does not, and it never has. Six consecutive words of a function's own
source is a threshold any conjecture that quotes the rule at all will clear, and every one of them
did.

So every "grounded per call" figure in this block is, exactly, a "confirmed collapse per call"
figure, and the distinction between the two measures carries no information about these records.

**What it costs:** nothing yet, because no conclusion has been drawn from the gap between the two —
there is no gap. It would cost a great deal the moment anyone read `grounded_T1` as evidence that a
find was well grounded rather than merely prose-bearing.

**Not repaired.** Tightening the threshold after seeing the records is fitting a measure to data. It
is named here, and a block that wants a filter that filters must pre-register a different one.

### C20. The measure's unit was never declared, and it changes the gap by nearly three (**mine**)

The pre-registered measure is `grounded_T1` **per model call**. Nothing ever asked what a call costs.
The records carry every call's prompt and completion tokens, so the question was answerable at any
point for nothing, and was not asked until a sibling project's method said *"equal ceilings are not
equal spending"*.

Over the first two repeats, complete for every arm:

| arm | finds | sends | tokens | per send | per 1,000 tokens |
|---|---|---|---|---|---|
| **R** | 27 | 114 | 582,829 | **0.237** | **0.0463** |
| **F** | 25 | 165 | 689,678 | 0.152 | 0.0362 |
| **W** | 27 | 165 | 810,223 | 0.164 | 0.0333 |
| **A** | 29 | 170 | 716,556 | 0.171 | 0.0405 |

`R` leads the best loop arm by **1.39×** per send and **1.14×** per token. The ordering does not
move; the size of the gap moves by nearly three.

**Which measure favours which conclusion, stated rather than left to a reader.** Per call is the
pre-registered figure and is the one that makes the loop look worst. Per token is not pre-registered
and is the one that goes against that reading. Both are reported from here on, with the unit named.

`W` is the arm this most changes, and against it: it spends more tokens than any other arm — 810k
against `R`'s 583k — and on a token basis it comes **last**, behind the arm it exists to improve on.

**Repaired** in the reading rather than the machine: `docs/mini/FROM_MINIREASON.md` carries both
columns and this entry carries the sentence about which flatters what. The reader still prints calls
only; a token column is a small change and is not made retroactively to a pre-registered measure.

### C21. An escaping defect discarded eleven confirmed finds, and correcting it widens R's lead (**found, by reading the record instead of the score**)

Fifteen rows across the block were scored `unrunnable`. **Eleven of them are confirmed finds**, and
all eleven pass the grounding filter.

The translator sometimes writes its own field values with **one extra level of JSON string
escaping** — a literal backslash-n where a newline belongs, a literal backslash-quote where a quote
belongs. The record stores the field exactly as it arrived, which is correct and is not the defect.
The executor then runs the check on text full of backslashes, the check raises, and the row is scored
as nothing. One defect with two faces: where the *commitments* were escaped the same way, `expect`
vanished entirely and the row was refused for having no expectation — although the reading had
written `"expect": "moves"`, in escaped form, right there in the blob.

Undoing exactly one level of escaping is well defined, so this is a rescue and not a reinterpretation:

| | refused rows | rescued | still unrunnable | separates on re-run |
|---|---|---|---|---|
| all arms | 15 | **11** | 3 | 1 |

**Where the finds went, and what correcting it does.** First two repeats, complete for every arm:

| arm | scored | rescued | corrected | change | per send | per 1,000 tokens |
|---|---|---|---|---|---|---|
| **R** | 27 | 3 | **30** | +11% | 0.263 | 0.0515 |
| **F** | 25 | 2 | 27 | +8% | 0.164 | 0.0391 |
| **W** | 27 | 2 | 29 | +7% | 0.176 | 0.0358 |
| **A** | 29 | 1 | 30 | +3% | 0.176 | 0.0419 |

`R` over the best loop arm goes from **1.39× to 1.49×** per send and from **1.14× to 1.23×** per
token. **The correction widens the gap it was reasonable to hope it would close.** I guessed the
other way out loud before finishing the count — on a partial rescue of seven rows the split looked
like `F` 3, `W` 2, `A` 1, `R` 1 — and the full count is `R` 3, `F` 5, `W` 2, `A` 1, which is
proportionally worst for the loop. The reading stage is byte-identical in all four arms, so this is
draw variance in one shared stage landing unevenly, not a property of any arm.

**What it cost:** 6.5% of the block's confirmed finds, thrown away in a way no measure could see,
for the whole run.

**Repaired:** nothing yet in the machine. Undoing one level of escaping inside the executor would
change what `unrunnable` means mid-block, and the honest move is to name it and correct the reading.
A successor should reject a reply whose field values contain literal escape sequences at the format
layer — `format.fields` already exists (C13) and a check for it is a two-line addition.

**How it was found.** The operator asked whether anything of value inside the runs had never reached
the end. Fifteen rows had been counted and none of them read.

### C22. The block never counted per segment, which is the measure that answers its own question (**mine**)

Every segment of every arm produces **exactly one claim**. So finds per segment is available, removes
the call count entirely, and was never computed. Taking it (`docs/mini/WHY_THE_LOOP_ARMS_SCORE_LOW.md`)
changes what the block is read as saying:

| arm | per segment | calls per segment |
|---|---|---|
| R | 0.958 | 3.56 |
| F | 0.875 | 5.21 |
| W | 0.896 | 5.15 |
| A | **0.951** | 5.32 |

`A` finds as often per segment as the arm with no loop. Over the two repeats complete for every arm
the two are **identical**, 0.938 each.

So `R`'s per-call lead over `A` — 1.4914 — is the calls-per-segment ratio, 1.4912, and that identity
is arithmetic rather than evidence: when two arms find the same per segment, the per-call ratio *is*
the inverse call ratio. It locates the whole gap in one place. **"A scores badly per call" is the
sentence "the criticism stage costs two calls", restated as a rate**, and it was read for two days as
though it were a result about criticism.

And the two pre-registered predictions **hold on this measure and were invisible on the reported
one**: per segment F 0.875 < W 0.896 < A 0.951, monotone, which is P1 and P2 exactly. What they are
made of is the finding: across those steps, claims that BROKE fall 9 → 2 → 1, so each addition to the
loop is recovering claims the loop's own machinery broke rather than producing new ones.

**What it cost:** the block's central comparison was reported for two days in a unit that could not
show its own pre-registered predictions, and the one measure that could was a division away the whole
time.

**Not repaired in the pre-registration**, which keeps per call as its declared primary — a measure is
not swapped after seeing the records. Per segment and per token are reported beside it, with this
entry saying which is which.

## The pattern

Of the twenty-odd items above, **three** are about the model. All the rest are about the apparatus:
what it could execute, what it could see, what it recorded, and what I measured. Every headline null
in this session — K1, C1 twice, C9 — has turned out on inspection to be a fact about the machinery
rather than about the loop.

The one thing that survived every repair, unchanged, is the conjecture step. It found real kernel
boundaries under every configuration, including the cheapest, and the machinery kept failing to
execute, see, or count them.

A5 and C12 to C22 were added after the rest, while building and first running the block that was meant
to settle the question. C12 was found by reading the run headers, A5 by counting what a segment
actually sends, and C13 and C14 by alarms firing on live segments — the only items here that a
machine caught rather than a person, and C14 was additionally diagnosed, correctly and in prose, by
the arm's own critic.

C12 was added after the rest, while building the block that was meant to settle the question. It is
the only item here that withdraws the *mechanism* of a positive result rather than a null, and it
found its way in the same way as all the others: by reading what the record says the run did,
instead of what the code that wrote it was supposed to do.

## C23 -- the arms result was reported on one measure, and five measures give five orderings

Block 2 was pre-registered on finds: one pair of reply texts a check answers the same on where its
documented rule requires a move. I reported the arms on that measure and said which ordering held. A
find is a pair of texts, and nothing in a count of them says how many distinct ways of breaking the
check they represent, nor whether the rule really requires the move.

Two readings written afterwards say both. `creib.forge.mini.collapses` partitions the finds by the
shape difference each exploits; `creib.forge.mini.rule_readings` implements the documented rule of two
checks from their docstrings rather than their bodies, so a find can be called real or unsupported
without a model's word for it. `python tools/creativity_block2.py classes` and `... rules` write them.

The cost of having reported only the pre-registered measure: **five measures, five orderings.**

| measure | A | F | R | W | order |
|---|---|---|---|---|---|
| finds per segment (pre-registered) | 0.938 | 0.771 | 0.896 | 0.854 | A > R > W > F |
| real finds per segment | 0.458 | 0.708 | 0.625 | 0.500 | F > R > W > A |
| collapse classes per segment | 0.271 | 0.188 | 0.250 | 0.292 | W > A > R > F |
| real classes per segment | 0.125 | 0.125 | 0.146 | 0.167 | W > R > A > F |
| real classes per model call | 0.024 | 0.024 | 0.041 | 0.032 | R > W > F > A |

`A` is first on the pre-registered measure and last on two of the others; `F` is last on three and
first on one. The second of the two pre-registered predictions, `W` below `A`, fails on three of the
four measures written afterwards. What I should have said, and am saying now, is that **three repeats
of four arms did not separate them**: the per-cell spread of collapse classes is 2 to 10 within one
arm.

What this does not say: that some later measure is the true one. All four of the new measures are
readings, each names what it cannot see, and `tests/mini/test_collapses.py` and
`tests/mini/test_rule_readings.py` assert those limits so that a reading which starts to see more
fails a test rather than quietly changing a number.

## C24 -- a third of the finds do not survive a reading of the rule, and one is false

Nothing in the block ever checked the half of a find that says *the rule requires these to differ*.
The executor checked the other half and `verify` re-ran every claim, which is why I kept calling the
find count checked. It was half-checked.

Adjudicated against the rule read apart from the code: of 166 finds, 111 are real under every reading
and 54 are unsupported under at least one. All 31 `refusal_phrase_in` finds are unsupported under one
of the two readings of the word *first* in "the first refusal phrase the text contains" -- the reading
the code follows -- so the block's second-largest group turns entirely on one word. Eleven finds are a
fence holding the object and then the object alone, which the rule scores the same either way, so they
never showed anything.

One find is false outright, and the module does not catch it because no reading of that check is
implemented: `_plain_quotes` on `I’m` against `I‘m`. The rule is "fold typographic
apostrophes and quotation marks to their ASCII forms", so both folding to `I'm` is the rule being
obeyed. It was reported inside the find count for a week.

What the block did find, and what I had not said plainly: 97 of the 111 surviving finds are two
divergences between one function's docstring and its body -- a fenced block whose tag the oracle's
pattern does not match is not treated as a fence (61 finds), and a fence holding more than one object
is skipped entirely (36). Both change which object a conformance run would score. Both are candidate
kernel points, recorded as such in `docs/mini/CANDIDATE_POINTS.md`, and promoting either is a person's
reading.

## C25 -- a quarter of DECIDE-TEST-1's key needed the grid's length, and the block had started

The pre-registration says twice that the grid's own length is a scope limit on every hit rate in the
block, and that a `stop` called right at the deepest cut is right relative to six segments of evidence
and not in general. Both sentences were committed before the first call. What was not committed was the
number: of the twelve decision points, **three** have a key that no reading of the figures can reach.

At the deepest cut every check's segments are used up, so every option's remaining yield is zero and
`stop` is the right answer. The figures the model is shown say the opposite -- `recover_json_object` with
five distinct ways found in six segments looks like a check worth moving to -- and the model cannot know
there is no seventh segment. On those three points a reasonable reading of the figures is scored wrong,
and that is an artefact of how long the grid is.

`creib.forge.mini.decide.length_dependent` now marks such a point and every hit rate is reported twice,
over all twelve and over the nine whose key the figures support. The baselines differ between the two
sets -- always-`stay` is 0.250 over twelve and 0.333 over nine, always-`stop` 0.250 and 0.000 -- so
reporting one figure would have hidden the other.

The timing, stated rather than glossed: the grid was complete and the first decision call had been sent
when this was written, and no reply had been read, so no reply could have influenced it. That is not the
same as pre-registration. The amendment is under its own heading in
`docs/mini/DECIDE_TEST_1.md`, which says the same thing there.

What it cost: nothing in calls, because the split is a reading of the grid. What it would have cost if
it had gone unnoticed: a headline hit rate a quarter of whose points punish a correct reading, against
baselines computed over the same contaminated set.
