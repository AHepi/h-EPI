# Mini prototype — the request, verbatim, split into numbered requirements

This file is the authority for everything else under `docs/mini/`. Nothing in
`DESIGN.md`, `SPEC.md`, or `DELIVERY.md` may claim an obligation that does not
trace to a number here, and every later artifact cites these numbers.

The operator's words are reproduced first, unedited. The requirements below are
a split of those words into numbered obligations, not a paraphrase: each one
quotes the sentence it comes from.

## The request as sent

> Can you get a window to build and return a spec for mini. It needs to build and test first. This is not for DeepReason but for that conformance repo h-EPI.
>
> It's a prototype since current authority and frozen surfaces are not relevant. I want the conjecture and criticism seats to be made from the same generic artifact: a template. It needs generic input and output ports where input types can be added at will at manifest compile time. There needs to be options to add other artifact types. All artifacts only need a body and commitments to compile and accepted during runtime. Formatting should be specifiable and compilable at the beginning of a run; otherwise default to freeform. Both body and commitments can accept any format, the only requirement is that "body" and "commitments" are in the initial submission form. Which means there needs to be a way of submitting keywords and syntax that can be compiled and recognised during runtime so that incorrect formats fail. Failure rates for all artifact types needs to be customisable at submission. Evidence needs to be split and tagged the same way as full DeepReason does it. Except wiring. Append-only log needs to work the same way it currently does, but logging extendable for new artifact types.
>
> Wiring and authority needs to achieve a few things: Allow cycles to operate in whatever order the user wants: Conjecturers->Conjecturer->New Type->Critic->New Type->End. This is just an example. Where evidence goes after batching goes needs to customisable. Where the contents of artifacts go needs to be customisable. All of this requires a default permission and authorisation layer that to have defaults for default runs. But it needs to be adaptable to the user's desired behaviour.
>
> Attention: It also needs to be adaptable and respond to new artifact types, but I'm not sure how to implement it. Signals need to be adaptable somehow too, but I'm unsure how to achieve it. All I know is attention needs to be determined by the machine not the user. And be switched off by default.

## The requirements

### Order of work

**R1 — Build and test before the specification.**
> "It needs to build and test first."

The specification is written from code that exists and passes its tests, not
from a plan. A section of `SPEC.md` that names no module and no test is a
proposal and is marked as one.

**R2 — The work lands in h-EPI.**
> "This is not for DeepReason but for that conformance repo h-EPI."

Shapes may be taken from DeepReason; code is not copied. h-EPI's own rules
(`CLAUDE.md`) govern every line written.

**R3 — It is a prototype; DeepReason's authority layer and frozen surfaces do not bind it.**
> "It's a prototype since current authority and frozen surfaces are not relevant."

Nothing here owes DeepReason compatibility, and no DeepReason surface is
treated as frozen. h-EPI's own rules still bind (R2).

### One artifact template

**R4 — Conjecture and criticism seats are made from one generic artifact template.**
> "I want the conjecture and criticism seats to be made from the same generic artifact: a template."

There is no conjecturer class and no critic class. Both are instances of one
template, distinguished only by the record that declares them.

**R5 — Generic input and output ports; input types can be added at manifest compile time.**
> "It needs generic input and output ports where input types can be added at will at manifest compile time."

A kind declares what it is shown (input ports) and what it produces (output
port). The set of available input port *types* is extensible by the manifest at
compile, not by editing code.

**R6 — Other artifact types can be added.**
> "There needs to be options to add other artifact types."

A third, fourth, nth kind is added by writing a record, never by editing code.

### What an artifact is

**R7 — Body and commitments are all an artifact needs, to compile and at runtime.**
> "All artifacts only need a body and commitments to compile and accepted during runtime."

A kind whose declaration adds nothing beyond those two fields compiles. A
submission carrying only those two fields is accepted at runtime.

**R8 — Format is specifiable and compiled at the start of a run; freeform otherwise.**
> "Formatting should be specifiable and compilable at the beginning of a run; otherwise default to freeform."

The format specification is compiled once, before any model is called, and a
malformed specification stops the run there. Absent a specification, nothing is
checked beyond R7's two fields.

**R9 — Any format is admissible in either field; only the two field names are required.**
> "Both body and commitments can accept any format, the only requirement is that 'body' and 'commitments' are in the initial submission form."

`body` and `commitments` are the only required keys of the submission. What
they contain is whatever the format specification for that kind admits, and
freeform by default.

**R10 — Keywords and syntax are submitted, compiled, and recognised at runtime; incorrect formats fail.**
> "Which means there needs to be a way of submitting keywords and syntax that can be compiled and recognised during runtime so that incorrect formats fail."

The operator writes the keywords and the syntax as data. Failure is a recorded,
typed outcome, never a silent acceptance.

**R11 — Failure rates are customisable per artifact type, at submission.**
> "Failure rates for all artifact types needs to be customisable at submission."

Every kind carries its own tolerance for format failures, and the tolerance is
consulted where the submission is checked.

### Evidence and the record

**R12 — Evidence is split and tagged as DeepReason does it, without DeepReason's wiring.**
> "Evidence needs to be split and tagged the same way as full DeepReason does it. Except wiring."

Content-addressed blocks, tier tags, a legend shown to a seat, and byte-checked
citations. "Except wiring" excludes DeepReason's coupling of evidence to a
scheduler and to a status machine: a citation check here changes no standing.

**R13 — The append-only log works as it does now, and is extensible for new artifact types.**
> "Append-only log needs to work the same way it currently does, but logging extendable for new artifact types."

Typed events, appended and never rewritten, replayed to rebuild state. A new
artifact type adds no new event type.

### Wiring and authority

**R14 — Cycles run in whatever order the user declares.**
> "Allow cycles to operate in whatever order the user wants: Conjecturers->Conjecturer->New Type->Critic->New Type->End. This is just an example."

The order is data the operator writes. The quoted order is an example that must
run as written, not the only admissible order.

**R15 — Where evidence goes after batching is customisable.**
> "Where evidence goes after batching goes needs to customisable."

The destination of a batch of evidence blocks is declared, not fixed.

**R16 — Where the contents of artifacts go is customisable.**
> "Where the contents of artifacts go needs to be customisable."

A stage's output is routed by declaration: to a later stage's port, into the
evidence store, to a scratch destination, or nowhere.

**R17 — A default permission and authorisation layer, with defaults for default runs, adaptable to the user.**
> "All of this requires a default permission and authorisation layer that to have defaults for default runs. But it needs to be adaptable to the user's desired behaviour."

A shipped default policy governs what each stage may read, write, and change; a
run may override it; an attempt outside it is refused with a typed reason.

### Attention

**R18 — Attention adapts to new artifact types.**
> "It also needs to be adaptable and respond to new artifact types, but I'm not sure how to implement it."

A policy written before a kind existed must still see that kind.

**R19 — Signals are adaptable.**
> "Signals need to be adaptable somehow too, but I'm unsure how to achieve it."

A signal is added by registering it, never by editing whatever consumes it.

**R20 — Attention is determined by the machine, not the user.**
> "All I know is attention needs to be determined by the machine not the user."

When attention is on, the next stage is chosen by a function of the record, not
by the operator's declared order.

**R21 — Attention is off by default.**
> "And be switched off by default."

A run that declares nothing runs the operator's declared order exactly.

## What the operator did not say

R18 and R19 are marked open by the operator's own words ("I'm not sure how to
implement it", "I'm unsure how to achieve it"). `DESIGN.md` records the smallest
reading taken for each, as a numbered assumption that one sentence can overturn.

---

# Amendment 1

Sent after the first delivery was pushed. The operator's words are reproduced
below unedited; the split into numbered requirements follows, continuing the
numbering at R22. Where Amendment 1 and the original request disagree,
Amendment 1 governs, and the superseded sentence is named.

## The amendment as sent

> AMENDMENT 1 to docs/mini/REQUEST.md — append these words verbatim as new requirements before acting, then revise DESIGN.md, the code, the tests and SPEC.md in that order. The operator's intent, now specified:
>
> 1. PORTS READ THROUGH ROUTING. One rule for artifacts and evidence alike: a port's DEFAULT draw is every artifact of its drawn kinds; a DECLARED route for a kind REPLACES that default for the kind it names; a PUSH is additive on top of whatever the route allows; a kind routed NOWHERE reaches no port, and the test for it asserts absence from every port, not only the routed event. Remove the asymmetry with evidence tiers.
>
> 2. CYCLES ARE FIRST-CLASS. The manifest's stage list is the body of ONE cycle. The runner repeats the cycle until a typed stop the HOST decides: a cycle cap, a budget cap, or a registered machine stop-condition over signals — never a seat's prose and never a verdict artifact's content. Stage ids are unique within a cycle; every artifact and every event carries (cycle, stage) coordinates. A port declaration may carry a window: `this_cycle`, `previous_cycle`, `last_n: N`, `all` (default `all`). The cycle-count signal counts real cycles; its test drives the runner, not the state directly. Attention may reorder the remaining stages of the current cycle and may REPEAT a stage only up to `max_repeats` declared per stage in the manifest (default 0), so the record's cycle and stage counts stay bounded by the manifest. Per-cycle kind ids are no longer needed for scoping; keep the template's ability to declare them, but the blind-spot run uses windows.
>
> 3. THE FORMAT IS SHOWN BEFORE THE FIRST ATTEMPT. `describe` renders the compiled format in full into the seat's brief — the JSON schema text, the keyword list, the grammar — on every attempt, and on a retry the validation error is shown beside the rendered format. Test: the schema text appears in the dispatched request bytes for a json_schema format on attempt one.
>
> 4. MACHINE SEATS ARE A RESPONDER KIND. A stage's seat may be a MODEL or a MACHINE: a registered responder keyed by kind id that runs a deterministic function over the record (the executor that runs a proposal through the kernel functions; a verdict that is computed from execution results). The record states per artifact which kind of seat produced it, so a reading and a function of the record are never confused. Test: the same manifest with the verdict seat as model (stub) and as machine produces artifacts whose provenance differs and whose bodies are checked by the same format.
>
> 5. THE BLIND-SPOT RUN IS THE FIRST TEMPLATE, rebuilt on 1–4: several proposer stages of one kind drawing earlier proposals and earlier verdicts (windows `all`); one machine executor; one critic reading proposals beside executions and citing the catalogue's blocks; one verdict stage drawing THIS cycle's executions and criticisms and all earlier verdicts, committing a JSON verdict per proposal (executed moved / unchanged; catalogued or not; standing: candidate point / defect / rejected), with the verdict schema rendered per 3. Run it under the stub for three cycles; the last verdict artifact is the deliverable a person turns into boundary points. Nothing in the loop promotes anything.
>
> 6. COMPARISON, NOT OPTIMISATION. Add a `compare` command that takes two run roots with byte-identical sources and script and prints their verdict artifacts side by side with their executed-invariance ledgers (invariances the catalogue lacked that a machine seat confirmed executed). It prints no score, no count-as-merit, and no ranking; a template's own verdict counts are never an objective, and DESIGN.md states that rule under h-EPI's "never promote". Test: `compare` over two stub roots emits both ledgers and refuses a `--score` flag.
>
> Record any further interpretation as a numbered assumption. Rerun `python tools/check.py all` at every commit; push the branch; update DELIVERY.md's table for the new requirements; SPEC.md is rewritten from the code that results, not patched. Stop when pushed.

## The requirements

### Ports and routing

**R22 — One routing rule for artifacts and evidence alike.**
> "PORTS READ THROUGH ROUTING. One rule for artifacts and evidence alike: a port's DEFAULT draw is every artifact of its drawn kinds; a DECLARED route for a kind REPLACES that default for the kind it names; a PUSH is additive on top of whatever the route allows; a kind routed NOWHERE reaches no port, and the test for it asserts absence from every port, not only the routed event. Remove the asymmetry with evidence tiers."

**Supersedes** the original R16's reading as built, in which a declared route for
an artifact kind added a destination while the default pull still delivered that
kind to every port drawing it. Under R22 the route replaces the default, exactly
as evidence tiers already behaved. The test obligation is strengthened: absence
from every port, not merely the presence of a routing event.

### Cycles

**R23 — The stage list is one cycle, repeated until a typed stop the host decides.**
> "CYCLES ARE FIRST-CLASS. The manifest's stage list is the body of ONE cycle. The runner repeats the cycle until a typed stop the HOST decides: a cycle cap, a budget cap, or a registered machine stop-condition over signals — never a seat's prose and never a verdict artifact's content. Stage ids are unique within a cycle; every artifact and every event carries (cycle, stage) coordinates. A port declaration may carry a window: `this_cycle`, `previous_cycle`, `last_n: N`, `all` (default `all`). The cycle-count signal counts real cycles; its test drives the runner, not the state directly. Attention may reorder the remaining stages of the current cycle and may REPEAT a stage only up to `max_repeats` declared per stage in the manifest (default 0), so the record's cycle and stage counts stay bounded by the manifest. Per-cycle kind ids are no longer needed for scoping; keep the template's ability to declare them, but the blind-spot run uses windows."

**Supersedes** the original R14 as built, in which the stage list ran once and the
end stage was the only terminal. It also supersedes assumption A12's reading of
attention's scope: attention now reorders within the current cycle and may
repeat a stage under a declared bound. The stop is the host's and is typed;
nothing a seat writes can end a run.

### The brief

**R24 — The compiled format is rendered in full, on every attempt.**
> "THE FORMAT IS SHOWN BEFORE THE FIRST ATTEMPT. `describe` renders the compiled format in full into the seat's brief — the JSON schema text, the keyword list, the grammar — on every attempt, and on a retry the validation error is shown beside the rendered format. Test: the schema text appears in the dispatched request bytes for a json_schema format on attempt one."

**Strengthens** the original R8/R10 as built, in which the brief carried a short
description of each check and the full schema text was never shown. The test
obligation names the dispatched request bytes, not the rendered brief.

### Seats

**R25 — A seat may be a model or a machine, and the record says which.**
> "MACHINE SEATS ARE A RESPONDER KIND. A stage's seat may be a MODEL or a MACHINE: a registered responder keyed by kind id that runs a deterministic function over the record (the executor that runs a proposal through the kernel functions; a verdict that is computed from execution results). The record states per artifact which kind of seat produced it, so a reading and a function of the record are never confused. Test: the same manifest with the verdict seat as model (stub) and as machine produces artifacts whose provenance differs and whose bodies are checked by the same format."

### The first template

**R26 — The blind-spot run, rebuilt on R22 to R25.**
> "THE BLIND-SPOT RUN IS THE FIRST TEMPLATE, rebuilt on 1–4: several proposer stages of one kind drawing earlier proposals and earlier verdicts (windows `all`); one machine executor; one critic reading proposals beside executions and citing the catalogue's blocks; one verdict stage drawing THIS cycle's executions and criticisms and all earlier verdicts, committing a JSON verdict per proposal (executed moved / unchanged; catalogued or not; standing: candidate point / defect / rejected), with the verdict schema rendered per 3. Run it under the stub for three cycles; the last verdict artifact is the deliverable a person turns into boundary points. Nothing in the loop promotes anything."

### Comparison

**R27 — A compare command that ranks nothing.**
> "COMPARISON, NOT OPTIMISATION. Add a `compare` command that takes two run roots with byte-identical sources and script and prints their verdict artifacts side by side with their executed-invariance ledgers (invariances the catalogue lacked that a machine seat confirmed executed). It prints no score, no count-as-merit, and no ranking; a template's own verdict counts are never an objective, and DESIGN.md states that rule under h-EPI's 'never promote'. Test: `compare` over two stub roots emits both ledgers and refuses a `--score` flag."

### How the work is to be done

**R28 — The order of work, and the standing obligations.**
> "Record any further interpretation as a numbered assumption. Rerun `python tools/check.py all` at every commit; push the branch; update DELIVERY.md's table for the new requirements; SPEC.md is rewritten from the code that results, not patched. Stop when pushed."

Amendment 1's own further interpretations are numbered from B1 in `DESIGN.md`,
kept apart from the original A-series so either can be overturned alone.

---

# Amendment 2

Sent after Amendment 1 was pushed. The operator's words are reproduced below
unedited; the split into numbered requirements follows, continuing at R29. Where
Amendment 2 and anything earlier disagree, Amendment 2 governs, and the
superseded sentence is named.

## The amendment as sent

> AMENDMENT 2 to docs/mini/REQUEST.md — append these words verbatim as new requirements, then revise DESIGN.md, code, tests and SPEC.md in that order, on a new branch `claude/mini-finish` from `claude/mini-prototype`. The operator's decisions on the register's open items and the spec's "not built" list:
>
> 1. SCRIPTS ADDRESSED BY COORDINATE. The scripted responder answers by (cycle, stage, attempt), not by consumption order, so one script can drive the same manifest under attention `off` and under a policy, and `compare` can set the two roots side by side. Keep the ordered script as a second form for old tests, or migrate them; say which. Test: the blind-spot script replayed under `off` and under the demonstration policy yields two roots whose logs differ only where the policy re-ordered, and `compare` shows it.
>
> 2. FENCED REPLIES ARE READ AND THE READING IS RECORDED. A reply that is valid JSON inside a markdown code fence is accepted; the event records `recovered: fence` beside the verbatim stored reply, so the stored bytes and the parsed submission are both on the record. A reply that is not JSON after stripping is still a FORMAT_FAILURE. Test both.
>
> 3. CITATIONS: BOTH ENDS FIXED. The wire schema requires non-empty `block` and `quote` on every citation entry, so an empty pair is a format failure, not an unknown block. The reader additionally recovers bracketed `[<block-id-prefix>] "quote"` pairs found in `body` prose into the citations field, each marked `recovered: prose`, and byte-checks them exactly as declared citations; the brief shows one worked example of a declared citation. Tests: the gpt-oss run's two artifacts, re-read from their stored replies, yield eleven recovered citations all verified; an empty pair is refused.
>
> 4. AN EMPTY INPUT PORT IS A TYPED NOTICE. A stage whose declared artifact port draws nothing writes `PORT_EMPTY` naming the port before dispatch; the failure policy for the kind gains one option, `skip_on_empty_port` (default false, so today's behaviour is unchanged and disclosed). Test both settings on the glm run's shape.
>
> 5. THE BLIND-SPOT TEMPLATE RUNS LIVE, ONCE. With the operator's key present, one live run of `forge/mini/manifests/blind-spot/` through three cycles with a model proposer and machine executor and machine verdict, records committed under `forge/mini/runs/blind-spot-<model>/`; RESULTS reported as what the record shows (proposals, executions, verdicts, the last verdict artifact whole) and nothing more; every new failure mode registered in FAILURE_MODES.md with event ids. Absent a key, deliver 1–4 and 7 and say so.
>
> 6. LEAVE ALONE, AND SAY SO IN SPEC.md: standing stays `changes: "nothing"`; evidence cutting stays blank-line; optional fields stay strings; single writer. These are decisions, not gaps.
>
> 7. TWO CALLS PER ARTIFACT, AND ONE VERDICT NODE PER CYCLE. The operator's words, verbatim: "Keep the schema simple inside the artifacts, try filling commitments within the same artifact into a second call that only ever sees the body content and nothing else. And at the end of each cycle, add a single verdict node that sees everything for body generation, but only the body for the second call." Read as: (a) an artifact's schema stays the two required fields, `body` and `commitments`, and nothing structural is added inside them; (b) producing an artifact becomes TWO model calls by default — the FIRST call receives the stage's full brief (ports, evidence legend, format) and returns `body` only; the SECOND call receives the body text and nothing else — no problem, no evidence, no other artifacts, no earlier commitments — and returns `commitments` only, under the kind's commitments format; the two replies are joined into one artifact whose record carries both requests and both replies, so anyone can see that the commitments were written blind; a manifest may set `commitment_call: single` per kind to keep the old one-call behaviour, disclosed; (c) every cycle ends with ONE verdict stage of a registered kind `mini.verdict.v1`, whose body call sees everything the cycle produced (all artifacts of the cycle, evidence, earlier verdicts, per the port windows) and whose commitments call sees ONLY the verdict's own body; the verdict seat may be model or machine per R25, and a machine verdict skips the second call and says so on the record. Tests: the second call's dispatched request bytes contain the body and no block id, no problem text, no other artifact; a kind set to `single` dispatches once; the cycle-end verdict is present exactly once per cycle and its two requests differ exactly as (c) says; the blind-spot template is rebuilt on this shape.
>
> `python tools/check.py all` green at every commit; push the branch; DELIVERY.md's table extended to R29 onward; SPEC.md rewritten from the code, with Part three reduced to what is genuinely still unbuilt. Stop when pushed.

## The requirements

**R29 — The scripted responder answers by coordinate.**
> "SCRIPTS ADDRESSED BY COORDINATE. The scripted responder answers by (cycle, stage, attempt), not by consumption order, so one script can drive the same manifest under attention `off` and under a policy, and `compare` can set the two roots side by side. Keep the ordered script as a second form for old tests, or migrate them; say which. Test: the blind-spot script replayed under `off` and under the demonstration policy yields two roots whose logs differ only where the policy re-ordered, and `compare` shows it."

**Closes** the gap `SPEC.md` Part three named after Amendment 1: a run could not
be replayed with attention on and off from one script, because attention changed
which stage consumed which reply.

**R30 — A fenced reply is read, and the reading is on the record.**
> "FENCED REPLIES ARE READ AND THE READING IS RECORDED. A reply that is valid JSON inside a markdown code fence is accepted; the event records `recovered: fence` beside the verbatim stored reply, so the stored bytes and the parsed submission are both on the record. A reply that is not JSON after stripping is still a FORMAT_FAILURE. Test both."

**Decides** the fork left open in `FAILURE_MODES.md` M4: the reader strips the
fence, and the record carries both the stored bytes and the fact of the
recovery, so the two can never be confused.

**R31 — Citations fixed at both ends.**
> "CITATIONS: BOTH ENDS FIXED. The wire schema requires non-empty `block` and `quote` on every citation entry, so an empty pair is a format failure, not an unknown block. The reader additionally recovers bracketed `[<block-id-prefix>] \"quote\"` pairs found in `body` prose into the citations field, each marked `recovered: prose`, and byte-checks them exactly as declared citations; the brief shows one worked example of a declared citation. Tests: the gpt-oss run's two artifacts, re-read from their stored replies, yield eleven recovered citations all verified; an empty pair is refused."

**Closes** `FAILURE_MODES.md` M1 and M2 together: M1's prose citations are
recovered and checked, and M2's empty pairs become a format failure rather than
an unknown block.

**R32 — An empty input port is a typed notice.**
> "AN EMPTY INPUT PORT IS A TYPED NOTICE. A stage whose declared artifact port draws nothing writes `PORT_EMPTY` naming the port before dispatch; the failure policy for the kind gains one option, `skip_on_empty_port` (default false, so today's behaviour is unchanged and disclosed). Test both settings on the glm run's shape."

**Closes** `FAILURE_MODES.md` M3's open design question.

**R33 — One live run of the blind-spot template.**
> "THE BLIND-SPOT TEMPLATE RUNS LIVE, ONCE. With the operator's key present, one live run of `forge/mini/manifests/blind-spot/` through three cycles with a model proposer and machine executor and machine verdict, records committed under `forge/mini/runs/blind-spot-<model>/`; RESULTS reported as what the record shows (proposals, executions, verdicts, the last verdict artifact whole) and nothing more; every new failure mode registered in FAILURE_MODES.md with event ids. Absent a key, deliver 1–4 and 7 and say so."

**R34 — Four things are decisions, not gaps, and `SPEC.md` says so.**
> "LEAVE ALONE, AND SAY SO IN SPEC.md: standing stays `changes: \"nothing\"`; evidence cutting stays blank-line; optional fields stay strings; single writer. These are decisions, not gaps."

**R35 — Two calls per artifact, and one verdict node per cycle.**
> "TWO CALLS PER ARTIFACT, AND ONE VERDICT NODE PER CYCLE. The operator's words, verbatim: \"Keep the schema simple inside the artifacts, try filling commitments within the same artifact into a second call that only ever sees the body content and nothing else. And at the end of each cycle, add a single verdict node that sees everything for body generation, but only the body for the second call.\" Read as: (a) an artifact's schema stays the two required fields, `body` and `commitments`, and nothing structural is added inside them; (b) producing an artifact becomes TWO model calls by default — the FIRST call receives the stage's full brief (ports, evidence legend, format) and returns `body` only; the SECOND call receives the body text and nothing else — no problem, no evidence, no other artifacts, no earlier commitments — and returns `commitments` only, under the kind's commitments format; the two replies are joined into one artifact whose record carries both requests and both replies, so anyone can see that the commitments were written blind; a manifest may set `commitment_call: single` per kind to keep the old one-call behaviour, disclosed; (c) every cycle ends with ONE verdict stage of a registered kind `mini.verdict.v1`, whose body call sees everything the cycle produced (all artifacts of the cycle, evidence, earlier verdicts, per the port windows) and whose commitments call sees ONLY the verdict's own body; the verdict seat may be model or machine per R25, and a machine verdict skips the second call and says so on the record. Tests: the second call's dispatched request bytes contain the body and no block id, no problem text, no other artifact; a kind set to `single` dispatches once; the cycle-end verdict is present exactly once per cycle and its two requests differ exactly as (c) says; the blind-spot template is rebuilt on this shape."

**Supersedes** the one-call production of an artifact assumed everywhere before
it, and adds a structural obligation on every manifest: a cycle ends with a
verdict stage.

**R36 — The standing obligations.**
> "`python tools/check.py all` green at every commit; push the branch; DELIVERY.md's table extended to R29 onward; SPEC.md rewritten from the code, with Part three reduced to what is genuinely still unbuilt. Stop when pushed."

Amendment 2's own further interpretations are numbered from **C1** in
`DESIGN.md`, kept apart from the A- and B-series.

---

# Amendment 3

Sent while Amendment 2's live run was still going, correcting R35(b).

## The amendment as sent

> oh no. one modification. What an artifact sees is upto whoever configures mini. This is just the default setting.

## The requirement

**R37 — What an artifact sees is configuration, and the blind second call is
only the default.**
> "What an artifact sees is upto whoever configures mini. This is just the default setting."

**Corrects R35(b) as built.** The two-call shape was implemented with the
commitments call's exposure FIXED in code: the body text and nothing else, with
no way for a manifest to say otherwise short of turning the second call off
altogether. That made a default into a law, which is the opposite of this
prototype's whole point — every behaviour a run can vary is reachable as
configuration.

What R35(b) states remains the DEFAULT and is unchanged for anyone who declares
nothing: the second call sees the body alone. What changes is that a kind may
now declare what else its commitments call sees, and the record says what it
saw.

---

# Amendment 4

Sent on 10 September 2026, after the machinery had been merged to `main` and
the blind-spot loop had been pointed at the conformance harness's own checks.
The operator's words are reproduced below unedited; the split into numbered
requirements follows, continuing at R38.

## The amendment as sent

> Ok. That's a big oversight. You do the necessary repairs and integrate it fully so the API key doesn't need double or triple handling.

## The requirements

**R38 — The necessary repairs.**
> "You do the necessary repairs"

Read as the defects the integration found, and the register's open items: the
verdict rule that compared a proposal with a catalogue row without regard to the
input, so that three of six verdicts in the first conformance run read "defect"
where the catalogue and the code agree; a kind with no instruction field, so a
seat's role had to travel as a source on its own tier and a title is capped; and
M5, M6 and M7, open since the blind-spot template's first live run.

**R39 — Integrate it fully, with the key handled once.**
> "integrate it fully so the API key doesn't need double or triple handling."

Read as: a live run is configured, called and recorded the way a conformance run
is. The manifest declares an endpoint in the pilot's own shape, read by the
harness's own reader; the live responder builds the harness's own executor from
it, which is the one place in this repository that reads the key; an endpoint
with `auth: none` needs no key; the run-time overrides are the conformance
runner's flags and the record carries what was sent. The documents and records
that describe the prototype live in the tree beside the harness's own, and the
entry documents name it.

**R40 — The standing obligations.**
As R36: the gate green at every commit, the branch pushed, `DELIVERY.md`'s table
extended, `SPEC.md` rewritten from the code.

Amendment 4's interpretations are numbered from **D1** in `DESIGN.md`.

## Amendment 5 — the experiments (10 September 2026)

> "Time to run experiments. 5 concurrently. Each a different shape. Keep
> mutating until you get something that works. But don't just do random
> mutations. Figure out what might be wrong first." Then: "3 rounds of 5
> concurrent. If you're still not seeing results, this whole angle might
> need a rethink." And: "It's ok it waste tokens. It's the data from
> variations that I'm after."

**R41 — Figure out what might be wrong first.** Read as a written diagnosis
before any run, and a criterion for "works" decided before the runs and not
moved after: `forge/mini/manifests/experiments/README.md`, which also names the
positive control the tree carries.

**R42 — Five concurrent, each a different shape, three rounds.** Read as five
manifests per round, each a different wiring of kinds, ports and instructions,
run at once on the models the operator has named, with the round's shapes
committed before its records exist and read after.

**R43 — Keep mutating until something works, not at random.** Read as: each
round's shapes are written from the previous round's records, and the README
says which record moved which shape. Two addenda after round 3 were the two
mutations the third round's records called for.

**R44 — The data from variations.** Read as: every run's record is committed
whatever it found, the dropped and the duplicate included, and the reading of
each names what it found and what it did not.

**R45 — The standing obligations.** As R36 and R40. What a run found in the
harness goes to the harness's own register and kernel table by a person's
reading, cited to the record.

Amendment 5's interpretations are numbered from **D10** in `DESIGN.md`.
