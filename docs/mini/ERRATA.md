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

## The pattern

Of the twenty-odd items above, **three** are about the model. All the rest are about the apparatus:
what it could execute, what it could see, what it recorded, and what I measured. Every headline null
in this session — K1, C1 twice, C9 — has turned out on inspection to be a fact about the machinery
rather than about the loop.

The one thing that survived every repair, unchanged, is the conjecture step. It found real kernel
boundaries under every configuration, including the cheapest, and the machinery kept failing to
execute, see, or count them.

A5 and C12 to C16 were added after the rest, while building and first running the block that was meant
to settle the question. C12 was found by reading the run headers, A5 by counting what a segment
actually sends, and C13 and C14 by alarms firing on live segments — the only items here that a
machine caught rather than a person, and C14 was additionally diagnosed, correctly and in prose, by
the arm's own critic.

C12 was added after the rest, while building the block that was meant to settle the question. It is
the only item here that withdraws the *mechanism* of a positive result rather than a null, and it
found its way in the same way as all the others: by reading what the record says the run did,
instead of what the code that wrote it was supposed to do.
