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
