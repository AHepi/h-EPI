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
