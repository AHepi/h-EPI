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

## The pattern

Of the twenty-odd items above, **three** are about the model. All the rest are about the apparatus:
what it could execute, what it could see, what it recorded, and what I measured. Every headline null
in this session — K1, C1 twice, C9 — has turned out on inspection to be a fact about the machinery
rather than about the loop.

The one thing that survived every repair, unchanged, is the conjecture step. It found real kernel
boundaries under every configuration, including the cheapest, and the machinery kept failing to
execute, see, or count them.
