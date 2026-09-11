# The config map: every setting, what it decides, and how it is misread

Tags are the spine. `CFG-*` is a setting, `MIS-*` a way it has been or can be misunderstood,
`CON-*` a confound (in `CONFOUNDS.md`), `ALM-*` an alarm (in `src/creib/forge/mini/alarms.py`),
`CONF-*` a registered configuration (in `forge/mini/configs/registry.json`). Every tag is checked
by `python tools/config_map.py audit`, which fails if one names nothing.

**Read the misreadings.** Each is a mistake someone made, mostly me, and the entry names what it
cost. A settings reference that lists only what a key does is a reference for people who already
understand it.

---

## 1. What decides whether a run keeps going

### CFG-MAX-CYCLES — `cycles.max_cycles`
How many times the stage list runs. Ends the run with `cycle_cap`.
- **MIS-MAX-CYCLES-1** — *"more cycles means more exploration."* A cycle re-enters the same stage
  list with the same instructions. Whether anything new happens depends on what the ports deliver
  between cycles (`CFG-WINDOW`), not on the count. Arms with 8 one-cycle segments and arms with
  1 eight-cycle run are **not** the same machine: the first can change its organisation between
  segments and the second cannot.

### CFG-STOP-CONDITION — `cycles.stop_condition`
A named condition evaluated between cycles: `mini.stop.never` (default) or
`mini.stop.no-artifact-last-cycle`. Ends the run with the condition's own name.
- **MIS-STOP-1** — *"the default is a safe default."* `mini.stop.never` means a run that produces
  nothing keeps paying for cycles until `CFG-MAX-CYCLES`.

### CFG-MAX-CALLS — `cycles.max_calls`
A ceiling on model calls. A call is reserved **before** it is sent, so the send that would exceed
is never made; ends the run with `call_budget_spent`.
- **MIS-MAX-CALLS-1** — *"the budget is per cycle."* It is per run, and reserved per call, which is
  why `calls_for_mini` needs no slack arithmetic.

### CFG-COMPLETION-BUDGET — `cycles.max_completion_tokens` + `cycles.completion_tokens_per_call`
Declared together or not at all. The per-call figure is the request's own cap; the total ends the
run with `completion_budget_spent`.
- **MIS-COMPLETION-1** — *"a bigger cap makes better answers."* A reasoning model can spend the
  whole per-call cap in its thinking channel and emit nothing (register M17). The cap bounds the
  spend, not the answer.

### CFG-TOLERANCE — `kinds[].failure_policy.tolerance`
How many refused submissions a kind bears, as a count or a fraction.
- **MIS-TOLERANCE-1** — *"tolerance is about quality."* It is a **termination** control. With
  `CFG-ACTION` at `stop`, tightening `CFG-FORMAT` shortens the run. See **CON-FORMAT-KILLS-RUN**.

### CFG-ACTION — `kinds[].failure_policy.action`
What happens once `CFG-TOLERANCE` is passed: `stop` (the default) ends the run with
`format_failures_exceeded`; `drop` continues without the artifact.
- **MIS-ACTION-1** — *"`drop` is the lossy option."* `drop` loses an artifact; `stop` loses the rest
  of the run. Which is lossier depends on what you were measuring, and the default is `stop`.

---

## 2. What decides whether a submission is accepted

### CFG-FORMAT — `kinds[].format`
`{body, commitments}`, each a list of checks from a closed set: `keywords`, `sections`, `regex`,
`line_shape`, `json_schema`. Any failure is a `FORMAT_FAILURE`; the refused reply is still stored
as a blob and named on the event.
- **MIS-FORMAT-1** — *"asking for JSON in the instruction is the same as declaring a schema."* It is
  not. Arm A asked for `{"attacks","ground","why"}` in prose with no `CFG-FORMAT`, and **four of
  eight criticisms wrote prose**, so the attack machinery engaged in under half the arm (ERRATA C6).
- **MIS-FORMAT-2** — *"a stricter schema means better data."* A required closed field with no escape
  value takes fabrication from 0–2% to 100% (DeepReason), and prompt-level instruction not to
  fabricate is **voided** by the schema. Strictness needs an escape road, not just teeth.
- **MIS-FORMAT-3** — *"a format only affects the artifact it is on."* It decides what reaches every
  downstream port, so a schema on one kind silently shapes what every later stage can see. M23 is
  this: a `pattern` on the use-test's kernel field forbade three of six kernels, and the seeded
  defect of one instance was in a forbidden one.

### CFG-INSTRUCTION — `kinds[].instruction`
The text a model seat is given for this kind, beside its rendered ports.
- **MIS-INSTRUCTION-1** — *"the instruction is what the seat is told."* The seat is told the
  instruction **and** every rendered port, and the two can contradict. Asking for `"<id>"` while the
  port prints `[<artifact id>]` beside each artifact got the artifact id, in 9 of 11 executions. The
  ambiguity was in the pair. See **CON-INSTRUCTION-AMBIGUITY**.
- **MIS-INSTRUCTION-2** — *"a clear instruction can replace a schema."* It cannot: arm A asked for
  JSON in prose and four of eight replies were prose. Enforcement is `CFG-FORMAT`.

### CFG-COMMITMENT-CALL — `kinds[].commitment_call`
`two` (default: the seat is asked twice, body then commitment) or `single`.
- **MIS-COMMITMENT-CALL-1** — *"single is cheaper."* It is one call rather than two, and it also
  removes the separation between saying a thing and committing to it, which is the separation
  criticism operates on.

### CFG-OPTIONAL-FIELDS — `kinds[].optional_fields`
Extra named string fields an artifact may carry beside body and commitments.
- **MIS-OPTIONAL-1** — *"optional means the machine will cope without it."* The executor refuses a
  pair whose `input` is missing with "no texts given", which reads as a model failure and is a
  declaration gap.

### CFG-RETRIES — `kinds[].failure_policy.retries`
How many times a refused seat is asked again, with the reason appended.
- **MIS-RETRIES-1** — *"retries fix bad output."* They re-ask with the refusal reason, so they fix
  **format** misses and not content. A retry loop against a wrong `CFG-FORMAT` burns calls.

### CFG-SKIP-ON-EMPTY — `kinds[].failure_policy.skip_on_empty_port`
Whether a stage whose port delivered nothing is skipped rather than run.

---

## 3. What decides what a seat can see

### CFG-INPUT-PORTS — `kinds[].input_ports`
Which port types a kind reads. **This is the wiring**, and it is the one thing this session
measured a large effect from: giving the critic a `reads` port more than doubled verified findings
with every other setting held (CONF-ARMS-W).
- **MIS-PORTS-1** — *"the artifact exists, so the seat can see it."* It cannot. Three of five
  commitment streams in CREATIVITY-ARMS-1 were written by a seat and read by nobody, and the
  criticism's was consumed by **no kind at all** (ERRATA C1).
- **MIS-PORTS-2** — *"a machine seat reads its declared ports."* Until M22 it did not: the
  pair-execution seat filtered by "this cycle" whatever window its stage declared, which made
  **half the architecture lattice** produce nothing.

### CFG-WINDOW — `input_ports[].window`
Which cycles an artifact must come from: `all`, `this_cycle`, `previous_cycle`, `last_n`.
- **MIS-WINDOW-1** — *"`all` means everything."* It means every cycle, not every kind: `CFG-DRAWS-FROM`
  still decides which kinds. And a machine seat may ignore it (MIS-PORTS-2).

### CFG-RENDER — `port_types[].render.rule`
`text`, `list_bodies`, `list_bodies_and_commitments`, `legend`.
- **MIS-RENDER-1** — *"the port carries the artifact."* It carries a **rendering**. `list_bodies`
  shows bodies and **not commitments**, so a commitment written by an upstream seat is invisible
  through it — which is why the critic could not see the conjecture's own commitment in arm F.
- **MIS-RENDER-2** — *"`legend` shows the evidence."* It shows an id and a **160-character
  excerpt**. A source that must be read whole goes through a machine seat as an artifact, not
  through evidence.

### CFG-DRAWS-FROM — `port_types[].draws_from`
Exactly one of `artifact_kinds` or `evidence_tiers`.

### CFG-PROBLEM — `problem`
The contract text, rendered **whole** through a `problem` port.
- **MIS-PROBLEM-1** — *"the problem is fixed for the inquiry."* It is fixed for a **run**.
  Serialisation rewrites it between runs, and that is the entire return-path mechanism — no code
  change was needed for it (PIPELINE_MATH T-A).

### CFG-SOURCES — `sources[]`
`text` or `path`, with a tier.

---

## 4. What decides the shape of the loop

### CFG-STAGES / CFG-STAGE-ORDER — `stages[]`
The list and its order. Order selects the architecture: an edge from a later stage to an earlier one
is lagged.
- **MIS-STAGE-ORDER-1** — *"a terminal verdict stage is required."* Nothing pins it. `n` stages admit
  `n!` orderings, not `(n-1)!`; the earlier count of 36 architectures was a count over one
  manifest's convention (ERRATA C10).

### CFG-SEAT — `stages[].seat`
`model` (default) or `machine`.
- **MIS-SEAT-1** — *"a machine seat is available because a module defines it."* It is available only
  if something **the tool imports** registered it. Registration is a process-global side effect, so
  a test importing it makes the tests pass and the tool still fail: M25 cost 36 runs, M26 cost 3
  more, and **ALM-SEAT-NOT-REGISTERED-BY-THE-TOOL** now refuses before the first call.

### CFG-MAX-REPEATS — `stages[].max_repeats`
### CFG-ENDPOINT — `endpoint`
Overridable per run by `--think` / `--timeout-seconds`; the run's first event records what was sent.
- **MIS-ENDPOINT-1** — *"read the run's settings from the pilot."* Read them from the **record**. The
  plan is unchanged by an override.

### CFG-POLICY — `policy`
`changes` is `nothing` and compile refuses any other value.
- **MIS-POLICY-1** — *"the permission layer enforces what it declares."* A machine seat can install
  into a controller while the policy still reads `nothing` (register H5). The layer declares; it
  does not enforce.

### CFG-ATTENTION — `attention`
Which stage runs next among those a cycle offers, by a named policy.

### CFG-ROUTING — `routing`
Which artifacts and evidence tiers reach which destinations.
- **MIS-ATTENTION-1** — *"attention changes standing."* It steers what is looked at. Nothing in this
  repository lets a measure adjudicate.
