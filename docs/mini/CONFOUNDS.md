# Confounds: settings that move together, and what that does to a comparison

A confound here is not a caveat. It is a **named pair or set of `CFG-*` settings whose interaction
makes a measured difference between two arms attributable to something other than the variable under
test.** Each entry says what couples, what it did or would do, how to hold it fixed, and what to
record so a reader can check it was held.

`python tools/config_map.py audit` fails if an entry names a setting that does not exist.

Every entry marked **observed** cost this repository runs. The others are reachable from the same
machinery and have not yet been paid for.

---

### CON-FORMAT-KILLS-RUN — a stricter form ends a run sooner
**Couples:** CFG-FORMAT, CFG-TOLERANCE, CFG-ACTION, CFG-RETRIES
**Status:** reachable, not yet observed — because no block has varied `CFG-FORMAT` across arms.

Tightening `CFG-FORMAT` raises the `FORMAT_FAILURE` rate; enough failures pass `CFG-TOLERANCE`; with
`CFG-ACTION: stop` the run ends with `format_failures_exceeded`. **So "how strict is the form" and
"how long does the run live" are one knob with two visible effects.** An arm with a stricter schema
dies younger and looks worse for a reason that has nothing to do with what it was testing.

**Hold it fixed:** identical `failure_policy` on every arm, and never vary `CFG-FORMAT` and
`CFG-TOLERANCE` in the same block.
**Record:** `format_failures_exceeded` per arm, and refused submissions per arm, beside any result.
**Alarm:** ALM-FORMAT-FAILURES-RISING.

---

### CON-STARVED-CRITIC — a loop fed refusals measures the executor
**Couples:** CFG-INPUT-PORTS, CFG-FORMAT, and whatever the executor can run
**Status:** **observed.** Cost two pre-registered comparisons.

If the executor refuses most submissions, the criticism stage reads refusals rather than results, so
any downstream comparison measures the machinery. CREATIVITY-ARMS-1's `N` read **7 unrunnable rows
against 1 result** and `F` **6 against 2**; C1 came back null and the null meant nothing.

**Hold it fixed:** check the executable rate before comparing arms.
**Record:** executed / unrunnable per arm, per segment.
**Alarm:** ALM-LOOP-STARVED (fatal). **Errata:** A1.

---

### CON-CARRY-AMPLIFIES — the return path carries the critic's errors too
**Couples:** CFG-PROBLEM (rewritten between runs), CFG-INPUT-PORTS on the critic
**Status:** **observed.** Inverted a conclusion.

Serialisation carries whatever the critic produced. A critic that cannot see the layer the errors
are in misattributes, and the carry then steers the next segment at a non-problem. `F` was told
*"Do not repeat any pair above"* and **repeated twice**; `N`, never told, repeated once; `W`, same
carry and a critic that could see the reading, repeated **zero**.

**So the return path cannot be evaluated independently of what the critic can see.** A block varying
the carry must hold the critic's ports fixed, and a block varying the ports must say the carry is
downstream of them.
**Record:** repeats of an earlier pair, per arm. **Errata:** A1. **Alarm:** ALM-CARRY-STALLED.

---

### CON-BASELINE-SEEDS — a mechanical baseline is only as good as its inputs
**Couples:** the baseline's seed set, CFG-FORMAT on the proposal
**Status:** **observed.** Made a headline comparison meaningless.

A non-LLM baseline exists to say what the host contributes without the model. If its inputs do not
exercise the subject, it measures its own inputs. **458 of the enumerator's 460 collapses were on
functions whose entire range over the fourteen seeds was one value** — it "found" 460 things and
none of them were anything.

**Hold it fixed:** the baseline's generator must first find, per function, two inputs producing
different answers, and only then look for a collapsing pair.
**Record:** collapses **on non-constant functions**, which both a baseline and a model arm can
score. **Errata:** A3, A4.

---

### CON-MEASURE-EXCLUDES-BASELINE — a measure the control cannot score on is not a control
**Couples:** the primary measure, the baseline's capabilities
**Status:** **observed.**

`grounded_T1` required quoting six consecutive words of a docstring. A mechanical enumerator writes
no prose, so its score was zero **by definition**. A control that cannot score is decoration.

**Hold it fixed:** every arm, including the mechanical one, must be able to score on the primary
measure. **Errata:** A4.

---

### CON-ARITY-HIDES-FINDS — the executor's reach decides what a measure can see
**Couples:** the kernel resolver's arity and module rules, the primary measure
**Status:** **observed.** Made `grounded_T1` read zero for arms that had found real boundaries.

`Kernel.verdict: Callable[[str], str]` refused every conjecture about a two-argument check, which is
what the model kept finding. The measure read zero while the arms were right.

**Hold it fixed:** resolution inside the arms, with the post-hoc reader kept as a cross-check.
**Record:** the disagreement rate between the live executor and the post-hoc verifier — **a
disagreement is itself the finding.** **Errata:** C9.

---

### CON-SEAT-REGISTRATION — the tests' import path is not the tool's
**Couples:** CFG-SEAT, what `tools/run_mini.py` imports
**Status:** **observed twice.** 36 runs, then 3 segments.

A seat exists only if something imported its module. Registration is process-global, so a test
importing it makes the suite pass while the tool still fails — and the check gets weaker as the
suite grows.

**Hold it fixed:** ask a **fresh interpreter** what the tool registers.
**Alarm:** ALM-SEAT-NOT-REGISTERED-BY-THE-TOOL (fatal, preflight). **Errata:** M25, M26.

---

### CON-PORT-NOT-DECLARED — a port on a kind that no stage declares is not a treatment
**Couples:** CFG-INPUT-PORTS, CFG-STAGES, CFG-RENDER, CFG-INSTRUCTION
**Status:** **observed** — CREATIVITY-ARMS-1, arms `W` and `A`, all sixteen segments (ERRATA C12).

A kind may declare an input port and a stage may then not list it. Only a stage's ports are
rendered, so the kind's declaration is inert: the seat is never shown that port's artifacts. Because
the manifest still *reads* as though the seat has them, an arm can be named for a wiring change that
never happened, and any real difference is then attributed to it.

In block 1 this coupled with two settings that **did** move: `W` rendered the conjecture's
commitments where `F` rendered only its body (`CFG-RENDER`), and `W`'s instruction told the critic to
attack a reading it could not see (`CFG-INSTRUCTION`). `W` doubled `F`'s yield. That number stands;
its mechanism is unattributed between three candidates, one of which was not operating at all.

**Hold it fixed:** read `STAGE_ENTERED`'s `ports` in the record, not the kind's `input_ports` in the
manifest, and check that an arm named for a port declares it on the stage that is supposed to read
it. Vary the port and the instruction that uses it together — a port a seat is not told to read is
not a treatment either — and vary nothing else.
**Record:** the criticise stage's `ports` per arm, from the record, beside any result the arm's
wiring is supposed to explain.
**Alarm:** none yet. A preflight that compares an arm's declared treatment against the stage ports
its manifest builds would have caught this before the first call; nothing does that today.

---

### CON-DRAW-VARIANCE — one repeat is not a measurement
**Couples:** the number of repeats, the endpoint's determinism
**Status:** **observed.** The endpoint returned **six different answers to a byte-identical prompt**.

Every arm in every block this session was one repeat. A two-witness gap between arms at one repeat
is not a result.

**Hold it fixed:** a declared stochastic floor — repeats of each arm — not one inherited by accident
because an arm happened to run a byte-identical brief.
**Record:** the spread across repeats beside every between-arm difference. **Errata:** C7.

---

### CON-INSTRUCTION-AMBIGUITY — a field name that names two things in one context
**Couples:** CFG-INSTRUCTION, CFG-RENDER on the port feeding that seat
**Status:** **observed.** Cost 9 of 11 executions.

An instruction asking for `"<id>"` while the port renders `[<artifact id>]` beside every artifact
gets the artifact id. The ambiguity is in the **pair**, not in either half.

**Hold it fixed:** name the field by its content and say what it is not.
**Record:** malformed-field rate per arm. **Alarm:** ALM-ID-WHERE-A-NAME-BELONGS (fatal).
