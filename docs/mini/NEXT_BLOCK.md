# The block that would settle it

A design, not a pre-registration: nothing here has run. Every item answers a numbered entry in
`docs/mini/ERRATA.md`, and the entries it cannot answer are listed at the end rather than omitted.

## What went wrong, in one sentence

Every headline null so far — K1, C1 twice, C9 — turned out on inspection to be a fact about the
apparatus: what it could execute, what the critic could see, what the commitment format admitted,
what the baseline's seeds exercised. **The loop has never been measured with the machinery working.**

## The six repairs, each answering an erratum

### 1. A format schema on the criticism commitment, with the escape road (→ C6)

Four of eight of arm A's criticisms wrote prose where JSON was asked for, so the attack machinery
engaged in under half the arm. Mini already supports `format.commitments.all_of[{check: json_schema}]`
and `mini.conformance-blind-spot.v1` uses a `pattern` exactly this way.

```json
{"kernel": {"pattern": "^(reading-misrenders-conjecture|conjecture-misreads-rule|
  rule-and-code-diverge|test-is-unsound|cannot-tell)$"}}
```

`cannot-tell` stays, and stays first-class: DeepReason measures a required closed field **without**
an escape road taking fabrication from 0–2% to 100%, and prompt-level instruction is *voided* by the
schema. A retried format failure is cheaper than a criticism that cannot land.

### 2. A validity node, so a test can be attacked (→ C5)

New ground: **`test-is-unsound`**, whose target is the *execution* rather than the conjecture. The
one criticism this session most deserved to hear — *the executor refused a true conjecture on an
arity bound* — had nowhere to go. Attacking an execution marks its verdict withdrawn, and the
conjecture it refuted returns to `accepted` by the existing fixed-point computation. No new status
rule: reinstatement already falls out.

### 3. A baseline whose seeds make functions vary (→ A3, A4)

458 of the enumerator's 460 collapses were on functions constant over the seeds. Replace the fixed
fourteen with a generator that, **per function**, searches for two inputs producing different
answers, and only then looks for a collapsing pair. Report `collapses on non-constant functions`, a
number both the enumerator and the model arms can score on — which `grounded_T1` never was.

### 4. A declared stochastic floor (→ C7)

Three independent repeats of every arm, declared, not inherited from `N` happening to run a
byte-identical brief. With the endpoint answering a byte-identical prompt six different ways, a
difference of two witnesses at one repeat is not a measurement, and every number in this session was
one repeat.

### 5. Enough segments to separate the arms that matter (→ the power problem)

`W` 7 against `A` 5 at eight segments is not a result. The decisive contrasts are **F→W** (wiring)
and **W→A** (landing), and they need enough draws that a two-witness gap is not noise. Sixteen
segments per arm, three repeats: four arms only — `R`, `F`, `W`, `A` — dropping `S` and `N`, whose
answers are already clear and stable across three blocks.

### 6. Arity and module resolution in the arms, not in a post-hoc reader (→ C9)

The live executor now binds a declared second argument and relocates a misfiled module, and both are
tested to compose. The post-hoc verifier stays, as a check on the executor rather than a substitute
for it: **if the two disagree on any claim, that disagreement is the finding.**

### 7. Hold `failure_policy` identical across arms, and record what it ended (CON-FORMAT-KILLS-RUN)

Repair 1 adds a format schema. That is also a **termination** control: tightening `CFG-FORMAT` raises
the refusal rate, enough refusals pass `CFG-TOLERANCE`, and `CFG-ACTION: stop` ends the run with
`format_failures_exceeded`. **"How strict is the form" and "how long does the run live" are one knob
with two visible effects**, so an arm with a stricter schema dies younger and looks worse for a
reason that is not what it was testing.

Therefore: identical `failure_policy` on every arm; never vary `CFG-FORMAT` and `CFG-TOLERANCE` in
the same block; and record refusals and `format_failures_exceeded` **per arm** beside every result.
`ALM-FORMAT-FAILURES-RISING` fires when refusals reach the accepted count, fatal, so an arm dying on
its form stops rather than finishing and being compared.

## What it measures

Primary, and both arms can score on it: **verified T1 witnesses per model call**, where verification
runs in the arm rather than after it.

Beside it, and reported whichever way they fall:
`attacks landed / criticisms`, `cannot-tell` rate, distinct targets, distinct pairs, repeats of an
earlier pair, and **the disagreement rate between the live executor and the post-hoc verifier**.

## What it predicts

- **P1.** `W` beats `F` again. Replication of the one effect this session actually established,
  now with a floor under it.
- **P2 — the experiment.** `A` beats `W`. If it does not, **criticism that lands buys nothing over
  criticism that is read**, at a point where the format no longer suppresses it, the test can be
  attacked, and there are enough draws to tell. That is the loop losing on the best version this
  repository can build, and it should be reported as such.
- **P3.** `A`'s repeats of an earlier pair stay at zero while `F`'s do not — the carry steering
  correctly because the critic can attribute correctly.
- **P4.** `test-is-unsound` is used at least once. If the machinery to attack a test exists and
  nobody attacks a test, that is worth knowing about the critic, not about the machinery.

## What it still would not settle, named rather than omitted

**C3 and C4 stand unrepaired.** Mini would still dispatch on kind rather than on interface
structure, and its commitments would still carry no `eval`, no budget and no
`V(κ,c) ∈ {pass, fail, overrun}`. So "attack surface" remains a metaphor here rather than a count,
and `crit(a) ⇔ interface.commitments ≠ ∅` is not a demarcation this machine can compute. A block
that fixed those is a different machine, and saying so is cheaper than pretending this one is it.

**C11 stands.** The machine's own critic argued this session's W2 finding is a misreading of the
rule and not a divergence in the code. Nothing here adjudicates that, and a person should.

And the result that needs no further block: **the conjecture step found real kernel boundaries under
every configuration tried, including the cheapest.** Whatever the loop turns out to be worth, that
is not what is in question.
