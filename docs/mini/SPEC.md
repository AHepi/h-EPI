# Mini — the specification, written from what was built

Authority: `REQUEST.md` — the original request (R1–R21), Amendment 1 (R22–R28),
Amendment 2 (R29–R36), Amendment 3 (R37) and Amendment 4 (R38–R40). Design and
assumptions: `DESIGN.md`, A1–A15, B1–B13, C1–C14 and D1–D9. Failure modes seen
in live runs: `FAILURE_MODES.md`.

This document is rewritten from the code that exists and passes its tests, as
Amendment 1 requires — not patched. Every contract names the module, the schema
and the test that make it true. What is proposed and not built is in the last
part, and nowhere else.

---

## Part one: what this is, in plain words

You give it a problem, some source documents, and a description of the run you
want. It asks a series of seats a series of questions, keeps everything it gets
back, and writes down exactly what happened.

**An artifact** is one thing a seat produced. Every artifact has a **body** and
some **commitments**, and those two are all any artifact needs.

**An artifact is written in two goes.** The first call sees everything the seat
is entitled to see and writes the body. The second call writes what is being
committed to, and **by default it sees only that body** — not the problem, not
the sources, not any other artifact. That is a default and not a law: whoever
configures the run decides what the second call sees, and the record says what
it saw. Both requests and both replies are kept, so "written blind" is something
you read off the record rather than something I am telling you.

**A seat** is not a kind of thing in the code. There is one template, and you
fill it in: what this seat is shown, and what it produces. Fill it in one way
and you have a conjecturer; another way and you have a critic; a third way and
you have something neither of us has named, and the run handles it with no code
written. A seat can also be a **machine** — a function of the record rather
than a model — and the record always says which of the two made each artifact,
so a computation is never mistaken for a judgement.

**A cycle** is the list of stages you wrote, and it always ends with a
**verdict** — one stage that looks at everything the cycle produced and says
what it makes of it. It repeats. What stops it is
always the host: a limit on cycles, a limit on calls, or a small function that
looks at counts drawn from the record. Nothing a seat writes can end a run —
a seat can say "stop, we are finished" as often as it likes and the run
continues, and there is a test that does exactly that.

**Evidence** is your sources, cut into paragraphs. Each paragraph has an
identity taken from its own words, so the same document always cuts the same
way. A seat sees a list of them with short extracts. If an artifact quotes one,
the run checks the quoted words really occur in it and writes down what it
found. That check decides nothing.

**Where things go is yours.** The order the seats run in is a list you write.
Where each seat's output goes afterwards — to another seat, into the evidence
pile, onto a shelf, or nowhere — is a rule you write, and a rule replaces the
default rather than adding to it. A port can also be told how far back to look:
only this cycle, only the last one, the last few, or everything.

**What a seat may do** comes from a permission document that ships with the
repository. By default a seat reads what its own description says it is shown,
keeps its own output, and may not push anything into another seat's inbox. You
can grant that for one run; the grant and every refusal go on the record.

**The record** is one file per run, one line per thing that happened, written
once and never rewritten. Each line carries a fingerprint of itself and of the
line before. Change one character and reading it stops. Reading it back
reproduces the run, and nothing else is needed to do that.

**Attention is off.** When off, the run follows your order exactly. When on, a
small function reads counts from the record and picks what runs next, within
the current cycle, and may repeat a stage only as often as your manifest allows.
You cannot tell it what to pick; you can only choose which function is in
charge.

**Things a seat writes badly are recovered where the record can show it.** An
answer wrapped in the three backticks people use for code is read, and the
record says it was unwrapped. Quotations a seat writes into its prose instead of
the field for them are pulled out and checked like any other, and the record says
where each came from. Nothing is silently tidied.

**Nothing decides anything is true, or better.** No artifact stands or falls.
Two runs can be set side by side, and `compare` will not order them, total
anything, or say which is better — it refuses even to be asked for a score.

---

## Part two: the contracts

### 1. The artifact template and its kinds (R4, R6, R7)

**Module** `kinds.py`. **Schema** `mini-kind.schema.json`.
**Tests** `test_template.py`.

A kind is a JSON record, a section of the manifest's `kinds` array or a file it
names:

```json
{
  "kind_id": "mini.conjecture.v1",
  "title": "Conjecture",
  "instruction": "Say what should be believed about the claim, and why it might be wrong.",
  "input_ports": [
    {"port_id": "problem",  "port_type": "problem"},
    {"port_id": "prior",    "port_type": "artifacts_of_kind",
     "params": {"kind_id": "mini.conjecture.v1"}, "window": "previous_cycle"}
  ],
  "output_port": {"port_id": "out", "produces_kind": "mini.conjecture.v1"},
  "optional_fields": [], "format": null, "failure_policy": null
}
```

`ArtifactKind` is the only class and `kind_from_dict` the only reader. There is
no conjecturer class and no critic class;
`test_both_shipped_seats_are_the_same_template` asserts the two shipped kinds
are instances of one type, and
`test_a_kind_declared_only_in_a_manifest_is_compiled_scheduled_produced_and_logged`
declares a third inside a test and watches it run.

Refusals: `MINI_KIND_OUTPUT_MISMATCH` (a kind producing another kind),
`MINI_KIND_PORT_DUPLICATE`, `MINI_SUBMISSION_UNKNOWN_FIELD` (a kind
redeclaring a template field).

**The submission form.** `read_submission` admits exactly:

| field | required | what it is |
|---|---|---|
| `body` | yes | a string, in whatever format the kind's specification admits |
| `commitments` | yes | a string, likewise |
| `citations` | no | `[{"block": "<id or prefix>", "quote": "…"}]` |
| `about` | no | artifact ids this artifact is about |
| `answers` | no | artifact ids this artifact answers |
| a kind's `optional_fields` | no | strings |

Anything else is refused. `about` and `answers` carry no authority; they exist
so §9 can count unanswered criticisms without knowing what a criticism is.

### 2. Input port types (R5)

**Module** `ports.py`. **Tests** `test_ports.py`.

Four ship — `problem`, `evidence_legend` (params `tiers`),
`artifacts_of_kind` (params `kind_id`), `scratch` (params `destination`) — and
a manifest extends the registry at compile in `port_types`, naming exactly one
of `artifact_kinds` or `evidence_tiers` and a rule from `text`, `list_bodies`,
`list_bodies_and_commitments`, `legend`. A rule that cannot render what the type
draws from is refused.

Refusals: `MINI_PORT_TYPE_UNKNOWN`, `MINI_PORT_TYPE_DUPLICATE`,
`MINI_PORT_TYPE_DRAWS_FROM_INVALID`, `MINI_RENDER_RULE_UNKNOWN`,
`MINI_PORT_PARAMS_INVALID`, and `MINI_KIND_UNKNOWN` / `MINI_TIER_UNKNOWN` when
a type draws from something nothing declares.

### 3. Format, compiled at run start, rendered in full (R8, R9, R10, R24)

**Module** `formats.py`. **Tests** `test_formats.py`.

Five checks, combined by `all_of`, per field: `keywords`, `sections`, `regex`,
`line_shape` (`every_line` / `any_line`), `json_schema`.

`compile_format_spec` runs inside `compile_manifest`, before any responder is
reached. `MINI_FORMAT_SPEC_INVALID` covers an unknown check, an uncompilable
expression, an empty keyword list, an unknown line scope, an invalid schema
fragment, and a fragment carrying `$ref` (nothing may be fetched), each tested.
Absent a specification the kind is freeform and only presence and non-emptiness
are checked.

**Rendered in full, on every attempt** (R24). `describe()` writes each check
out — the keyword list one per line, the markers in order, the expression, the
schema as text — into the brief, first attempt included; a retry adds the error
beside it rather than in place of it.
`test_the_schema_text_is_in_the_dispatched_request_bytes_on_attempt_one` reads
the bytes that would have gone over the wire, not the rendered brief.

### 4. Failure policy (R11)

**Module** `failures.py`. **Tests** `test_failures.py`.

```json
{"retries": 1, "tolerance": null, "action": "stop"}
```

Retries re-ask with the error shown; a submission still failing is dropped and
the run goes on; `tolerance` is how many drops of that kind the run permits (an
integer, a `{numerator, denominator}` fraction, or `null`); `action` says what
happens past it. The shipped default is exactly "drop after one retry".

**Every reply is kept**, the refused ones included: stored as a blob before it
is read, named on `FORMAT_FAILURE` in `body_ref`, and listed on
`SUBMISSION_DROPPED` in `refused_refs`. That was a defect a live run found;
`RefusedRepliesAreKeptTests` holds it, and `FAILURE_MODES.md` H1 records why.

### 5. Evidence (R12)

**Module** `evidence.py`. **Tests** `test_evidence.py`.

`cut_source` cuts at blank lines, trims each span, and gives each block its byte
offsets, its text digest, its tier, and an id that is a digest of that content.
Cutting is deterministic in the bytes. Tiers are a registry — `evidence` and
`generated` ship, a manifest extends it.

`check_citations` gives one typed measure per claim: `MINI_CITATION_VERIFIED`,
`MINI_CITATION_UNKNOWN_BLOCK`, `MINI_CITATION_AMBIGUOUS`,
`MINI_CITATION_WITHHELD`, `MINI_CITATION_QUOTE_MISMATCH`. The quote check folds
whitespace on both sides; folding never inserts whitespace, so a quote joining
words the source separated still fails.

**"Except wiring", discharged**: a measure is written to the record and read by
nothing that decides anything — not routing, not permission, not any standing.

### 6. The append-only record (R13, R23)

**Module** `log.py`. **Schemas** `mini-event.schema.json` (v2) and
`mini-event.v1.schema.json` (frozen). **Tests** `test_log.py`, `test_cycles.py`.

```json
{"schema_version": "creib.mini.event.v2", "seq": 7, "cycle": 2,
 "prev": "<64 hex>", "type": "ARTIFACT_SUBMITTED", "stage_id": "criticise",
 "kind_id": "mini.criticism.v1", "artifact_id": "<64 hex>",
 "body_ref": "<64 hex>", "commitments_ref": "<64 hex>",
 "payload": {"seat": "model", …}, "event_id": "<64 hex>"}
```

`event_id` is a digest over every other field; `prev` is the previous event's
id, and at sequence 0 it is the digest of the run header. Reading verifies all
three (`MINI_LOG_EVENT_ID_MISMATCH`, `MINI_LOG_SEQUENCE_BROKEN`,
`MINI_LOG_CHAIN_BROKEN`); one flipped character inside a blob reference, still
well-shaped hexadecimal, is refused.

**Ten event types, and a new kind adds none.** `RUN_STARTED`, `STAGE_ENTERED`,
`ARTIFACT_SUBMITTED`, `FORMAT_FAILURE`, `SUBMISSION_DROPPED`, `REFUSED`,
`EVIDENCE_BATCHED`, `ROUTED`, `ATTENTION_CHOSE`, `RUN_ENDED`. Bodies and
commitments are blob references; the kind is a field.

**Two versions are read.** Adding the cycle coordinate changed the record's
shape, so v1 is frozen and still read: `_SCHEMAS` dispatches on the version in
the line and a v1 event replays under the v1 domain with cycle 0.
`test_a_version_one_record_still_replays` reads a committed run made before
cycles existed, so `FAILURE_MODES.md`'s replay instructions stay true.

`apply_event` is the one function that changes state; `replay(path, genesis)`
rebuilds it from the log alone and its digest equals what the run reported.

### 7. Cycles, and what stops a run (R23)

**Modules** `manifest.py`, `stops.py`, `windows.py`, `runner.py`.
**Tests** `test_cycles.py`.

The stage list is the body of **one cycle**. The end stage ends the cycle. Three
things end the run, checked before each cycle and never inside one:

| stop | declared | reason recorded |
|---|---|---|
| cycle cap | `cycles.max_cycles` (default 1) | `cycle_cap` |
| budget cap | `cycles.max_calls` | `budget_cap` |
| a registered condition | `cycles.stop_condition` (default `mini.stop.never`) | `stop_condition:<id>` |

A stop condition declares the signals it reads and is handed a view of exactly
those; a function that could take the record is refused at registration
(`MINI_STOP_CONDITION_SIGNATURE`). Two ship: `mini.stop.never` and
`mini.stop.no-artifact-last-cycle`.
`test_nothing_a_seat_writes_ends_the_run` runs three cycles of a seat writing
"STOP. The run is over." and gets three cycles.

**Windows.** A port may carry `window`: `all` (default), `this_cycle`,
`previous_cycle`, or `{"last_n": N}`, filtered on the cycle coordinate. Supplied
sources carry cycle 0, so `this_cycle` on an evidence port draws only what the
run generated.

**Repeats.** `max_repeats` per stage (default 0) bounds how often attention may
re-offer it within one cycle, so the record's stage count is bounded by the
manifest whatever the policy does.

### 8. Routing, one rule (R14, R15, R16, R22)

**Modules** `routing.py`, `runner.py`. **Tests** `test_wiring.py`.

A port's **default draw** is everything of the kinds or tiers its type names. A
**declared route replaces** that default for the one kind or tier it names. A
kind or tier may carry several routes and its reach is their union; `nowhere`
may not be combined with anything.

| routes for a kind | the ports it reaches |
|---|---|
| none | every port whose drawn kinds include it |
| `nowhere` | none |
| `port(S, P)` | that port, if the run actually placed it there |
| `scratch(D)` | scratch ports for `D` |
| `evidence_store(T)` | no artifact port; its blocks reach evidence ports drawing `T` |

Evidence tiers take the same shape with `port_type(P)`, `scratch(D)`,
`nowhere`. A push the permission layer refused reaches nothing, because reach is
read from what the run recorded, not from what the manifest declared.

`test_a_kind_routed_nowhere_reaches_no_port_at_all` renders every port of every
stage and asserts absence, not merely that a routing event was written.

### 9. Permission and authorisation (R17)

**Module** `policy.py`. **Document** `forge/mini/policies/mini.policy.default.v1.json`.
**Tests** `test_policy.py`.

Defaults: read the ports your kind declares; write your own output, the evidence
store, scratch and nowhere; change **nothing**. `port` is absent from the
default writes, so pushing into another stage's inbox needs a grant naming that
stage and port. A run overrides in `policy.grants`, and the compiled grants go
into `RUN_STARTED`.

`changes` accepts only `"nothing"`; any other value is
`MINI_POLICY_CHANGE_UNSUPPORTED` at compile. The slot exists so a later policy
can grant a standing; this prototype mints none and refuses to pretend
otherwise.

### 10. Seats: model and machine (R25)

**Module** `machines.py`. **Tests** `test_machines.py`.

A stage declares `seat`: `"model"` (default) or `"machine"`. A machine seat is
registered by kind id, handed a `MachineContext` — plan, state, blobs, stage,
cycle — and returns a reply in the shape a model would have returned, so the
same reader and the same compiled format check it. `ARTIFACT_SUBMITTED` and
`FORMAT_FAILURE` both carry `seat`.

`test_provenance_differs_and_the_same_format_checks_both` runs one manifest with
the verdict seat as model and as machine.
`test_a_machine_seat_whose_answer_misses_its_format_is_refused_like_any_other`
shows a machine seat is not privileged.

### 11. Signals and attention (R18, R19, R20, R21)

**Modules** `signals.py`, `attention.py`. **Tests** `test_attention.py`,
`test_architecture.py`.

Six signals ship: artifacts by kind, citations verified by artifact, unanswered
criticisms by kind, tokens by kind, cycle count, artifacts in each cycle. Every
one is keyed by an id the record carries, never by a name in the code; a test
registers a seventh from inside a test and reads it off a real run.

An **unanswered criticism** is defined without naming a kind: an artifact naming
another in `about` that no artifact names in `answers`, counted against the kind
of the artifact it is about.

Two attention policies: `mini.attention.off` (**the default**) and
`mini.attention.most-unanswered-criticisms`. The architecture check is what
makes "the machine, not the user" structural: `attention.py` imports nothing
that touches the record (asserted by parsing its own source); every policy takes
exactly `(signals, stages)`; a function that would take a third parameter is
refused at registration; a policy asking for a signal it did not declare is
refused when it runs; every shipped policy reads only what it declared.

### 12. The blind-spot template (R26)

**Module** `blindspot.py`. **Manifest** `forge/mini/manifests/blind-spot/`.
**Run** `forge/mini/runs/blind-spot-stub/`. **Tests** `test_blindspot.py`.

Four **kernels** — deterministic verdicts of this prototype's own machinery over
one text: `cut-count`, `folded`, `json-readable`, `carries-because`. Five
**transforms** — `fold-whitespace`, `upper-case`, `wrap-in-code-fence`,
`reorder-paragraphs`, `append-blank-line`. A **catalogue** listing the pairs
already written down and whether each is known to move, supplied as an ordinary
source so it is cut into blocks a critic can cite.

A proposal commits `{"kernel", "transform", "input"}`. The machine **executor**
runs the kernel before and after and commits `moved` or `unchanged`. The machine
**verdict** sets each execution against the catalogue:

| executed | catalogue | standing | column |
|---|---|---|---|
| moved | does not list the pair | `candidate point` | moves |
| unchanged | does not list the pair | `candidate point` | unchanged: the blind spot nobody wrote down |
| moved | says it does not move | `defect`: the invariance is refuted by this input | — |
| unchanged | says it moves, on this input | `defect`: the row's own example is wrong | — |
| unchanged | says it moves, on another input or none named | `candidate point` | unchanged: an input the check is blind to |
| either | agrees | `rejected` | — |
| unrunnable, unreadable | anything | `rejected` | — |

A row is read as a kernel point is (`DESIGN.md` §31): an invariance is a claim
over the input class, a sensitivity is an example on the row's own input. Rows
carry the input they were checked on; the entry carries `same_input` and
`column`. `standing_for` and `column_for` in `blindspot.py` state the rule once;
`test_blindspot.TheStandingRuleTests` holds every row of this table.

Three proposer stages at window `all`, one machine executor, one critic, one
machine verdict at `this_cycle` for executions and criticisms and `all` for
earlier verdicts, three cycles. The last verdict is the deliverable a person
turns into boundary points, or does not. Nothing in the loop promotes anything.

### 13. Comparison, never optimisation (R27)

**Module** `compare.py`. **Command** `tools/run_mini.py compare`.
**Tests** `test_blindspot.py::CompareTests`.

Two roots, refused unless they were given the same sources and asked the same
way — checkable because a run records a `responder_id`, a digest of the script
or the model's name. Prints the verdicts side by side and each root's
**executed-invariance ledger**: pairs the catalogue does not list, that a
**machine** seat executed and found unchanged. A model's prose about an
invariance never enters a ledger.

Nothing is ordered or added up. `--score` is declared so it can be refused by
name, and a test asserts the rendered output contains none of *score*, *best*,
*worst*, *better*, *wins*, *rank*, *accuracy* or *total*.

### 14. Two calls per artifact (R35 a, b)

**Modules** `runner.py`, `kinds.py`, `formats.py`. **Tests** `test_two_calls.py`.

| call | is shown | returns |
|---|---|---|
| body | the stage's full brief: every declared port, the evidence legend, the compiled body format, the worked citation example | `body`, and optionally `citations`, `about`, `answers`, the kind's optional fields |
| commitments | the body text, the compiled commitments format, one line of instruction — **and whatever ports the kind's `commitment_ports` declares, which by default is none** | `commitments` |

**What an artifact sees is configuration** (R37). The blind second call is the
DEFAULT, not a law: a kind may name any of its own declared ports in
`commitment_ports`, and those are rendered into the second call as well. A port
the kind does not declare is `MINI_PORT_UNKNOWN` at compile. The record carries
`commitment_ports` on every artifact, so "written blind" is read off the record
rather than assumed from a default.

The two replies are joined by `Submission.joined`. The record's
`ARTIFACT_SUBMITTED` carries `calls`, a list of `{phase, request_ref,
reply_ref}`, so **both requests and both replies** are blobs anyone can read.
`test_by_default_the_second_call_sees_the_body_and_nothing_else` asserts the
second request contains the body and contains none of: the problem text,
another artifact's body, any block id, any of the source's words — of the
default. `WhatTheCommitmentsCallSeesTests` then shows a declared port arriving
in the same bytes, so the default is checked as a default.

The format splits across the calls: a body failure never reaches the second
call, and a commitments failure names its phase. `commitment_call: "single"`
per kind keeps the one-call shape, and the record carries which shape produced
each artifact either way. A machine seat makes one call and the record says
`machine_single`.

### 15. One verdict node per cycle (R35 c)

**Module** `manifest.py`. **Tests** `test_two_calls.py::VerdictNodeTests`.

Every cycle ends with exactly one stage of kind `mini.verdict.v1`. Compile
refuses a manifest with none (`MINI_VERDICT_MISSING`), with more than one
(`MINI_VERDICT_DUPLICATE`), or with one that is not the last stage before the
end stage (`MINI_VERDICT_NOT_LAST`). Every shipped manifest carries one, and a
test walks the directory to say so. Attention may not reach the verdict stage
until it is the only one left, so "ends with" survives a re-ordering policy.

Its body call sees everything the cycle produced, through its declared ports and
their windows; its commitments call sees only its own body. Its seat may be
model or machine.

### 16. Scripts addressed by coordinate (R29)

**Module** `executor.py`. **Tests** `test_scripts.py`.

Two script forms, told apart by shape. A stage whose value is a **list** is
consumed in order. A stage whose value is an **object** is keyed by cycle and
indexed by attempt, so the stage gets the same reply wherever the cycle puts it.
Both may appear in one script; a `<stage>@commitments` entry answers the second
call, and without one the stage's own replies serve both phases, consumed
independently.

**Which is which:** the committed blind-spot script is by coordinate. Every
other test script is ordered, because ordered is the shorter thing to write when
a stage runs once and nothing re-orders it.

One script now drives the same manifest with attention off and on, and
`compare` sets the two roots side by side. On the blind-spot template the
demonstration policy finds nothing to prefer, so the two logs differ only in the
run header — asserted event by event, and worth asserting: attention on but idle
should be the same run as attention off.

### 17. What is recovered, and how the record shows it (R30, R31)

**Modules** `kinds.py`, `evidence.py`. **Tests** `test_recovery.py`.

**A fenced reply is read.** `strip_fence` removes a leading ```` ``` ```` fence
and its close before reading. `ARTIFACT_SUBMITTED` carries `recovered:
["fence"]` and names the verbatim reply in `reply_ref`, so the stored bytes and
the parsed submission are both reachable from one event. A reply that is still
not JSON after stripping is a `FORMAT_FAILURE`.

**Citations at both ends.** A declared citation must carry a non-empty `block`
and a non-empty `quote`; an empty pair is `MINI_SUBMISSION_FIELD_TYPE`, which
reaches the record as a format failure — a fact about the reply, not about the
evidence. The live wire schema carries the same requirement. The reader then
recovers bracketed `[<hex prefix>] "quote"` pairs from `body` prose, marks each
`recovered: prose`, and byte-checks them exactly as declared ones; every measure
says which it was. The committed gpt-oss run's two artifacts yield **eleven
recovered citations, every one verified**.

The brief shows one worked example of a declared citation, built from a block
the stage can actually see.

A third recovery is of the reading rather than of the reply: a model that writes a
raw line break inside a JSON string, where the two characters backslash and n
belong, is read as having meant the line break. The strict reading is always
tried first, the second reading admits a control character and nothing else — a
duplicate key, a float, a surrogate and text that is not JSON are refused as
before — and the artifact records `control-characters` beside `fence` and
`prose`. It applies where the reply itself is read (`read_submission`) and where
a field's own JSON is read against a declared schema (`json_schema`), which is
the case that cost one live run forty-one of its forty-two calls
(`FAILURE_MODES.md` M13).

A kind's own **optional fields** are now offered rather than merely admitted: the
brief names them, the live contract carries each as a string beside `body` and
`commitments`, and the blind commitments call is still entitled to one field and
nothing else. A kind that wants a long text written out declares it there, where
one level of escaping serves, instead of nesting it in the commitments string,
where three levels are needed and where the register's oldest open failure lives
(M9, M13). The blind-spot seats read a kind's optional fields over the
commitments, so the same proposal can be written either way.

### 18. An empty input port (R32)

**Module** `runner.py`. **Tests** `test_failures.py::EmptyPortTests`.

A declared **artifact** port that draws nothing writes `PORT_EMPTY` naming the
port, before dispatch. Only artifact ports: an empty evidence port is the
ordinary state of a first cycle. The kind's failure policy gains
`skip_on_empty_port`, default false, so the earlier behaviour is unchanged and
disclosed; set true, the stage writes its notice and produces nothing.

### 19. Compile, the loop, and the command line

`compile_manifest` refuses at the first thing that does not resolve and then
fixes a run header whose digest is the run id and the chain's genesis.
`run_mini` walks cycles and stages, asks attention when it is on, checks reads,
renders the brief, asks the seat, reads and checks the submission, applies the
failure policy, checks citations, writes the artifact, and routes the output
through the permission layer. Every outcome is an event.

`tools/run_mini.py`: `compile`, `run`, `live`, `replay`, `compare`. Only `live`
calls a model, at the endpoint of §20, taking `--think`, `--timeout-seconds` and
`--retries` as the conformance runner does.

### 20. The endpoint, the harness's own (R39)

**Modules** `executor.py`, `manifest.py`; the reader is the conformance package's
`endpoint_from_dict`. **Schema** `mini-manifest.schema.json`, `endpoint`, the
pilot's own definition. **Tests** `test_endpoint.py`.

A manifest may declare `endpoint` in exactly the shape a conformance pilot does:

```json
"endpoint": {"kind": "ollama-chat", "base_url": "http://localhost:11434",
             "timeout_seconds": 60, "options": {"temperature": 0, "seed": 3},
             "think": "low", "auth": "none"}
```

Absent, the shipped default applies (`https://ollama.com`, 180 seconds,
temperature 0, seed 7, no reasoning setting, bearer) and the header carries no
key, so every manifest written before endpoints existed keeps its identity
(`test_absent_is_the_default_and_writes_no_header_key`). Declared, it is in the
header and moves the run id. A malformed one is `MINI_ENDPOINT_INVALID`.

`LiveResponder` builds the harness's `OllamaChatExecutor` from the endpoint and
sends its temperature, seed and reasoning setting with every request
(`test_the_endpoint_settings_reach_every_request`). The key is read inside that
executor at call time and nowhere else in this repository. When the responder
builds the executor itself and the endpoint's auth is bearer, an absent
`OLLAMA_API_KEY` is refused with `MINI_LIVE_KEY_MISSING` before any record is
written; `auth: none` needs no key
(`test_an_auth_none_endpoint_needs_no_key`). `--think` and `--timeout-seconds`
override the endpoint for one run, the plan unchanged, and the `RUN_STARTED`
event carries the endpoint actually sent to; a scripted run carries none
(`test_a_live_run_records_the_endpoint_used_and_a_scripted_run_records_none`).

### 21. A kind's instruction (R38)

**Module** `kinds.py`. **Schema** `mini-kind.schema.json`, `instruction`.
**Tests** `test_template.InstructionTests`.

`instruction` is what a kind's seat is asked to do. It heads every brief for the
kind, the commitments call's included, since it is the kind's own words and not
evidence or another artifact; the blind default of §14 is untouched. Absent,
nothing is shown and no header key is written; present, it moves the identity.

### 22. Pairs, two readings, the rules seat, and a grid enumerated by machine (R41 to R45)

**Module** `blindspot.py`, `conformance_kernels.py`. **Manifests**
`forge/mini/manifests/experiments/`. **Runs** `forge/mini/runs/experiments/`.
**Tests** `test_pairs.py`.

A **pair proposal** (any kind whose id starts `mini.pair-proposal.`) commits
`{"kernel", "input", "rewritten", "expect", "rewrite"}`: the proposer writes the
rewrite itself, so no transform registry stands between it and the check, and
says what the check's answer ought to do (`moves`, `unchanged`). The machine
**pair executor** (`mini.pair-execution.v1`) runs the kernel on both texts and
commits `before`, `after`, `executed` and `as_expected`; a pair the run already
executed is `duplicate` and not run again (M10), and a rewrite equal to its
input, an unknown kernel or an expectation outside the two words is
`unrunnable`. The verdict's standing for a pair (`standing_for_pair`):

| executed | expectation | standing | column |
|---|---|---|---|
| moved | unchanged | `candidate point` | moves |
| unchanged | moves | `candidate point` | unchanged |
| either | agrees | `rejected` | — |
| unrunnable, unreadable, duplicate | anything | `rejected` | — |

Nothing is a defect on the proposer's word: a pair has no catalogue row to
refute, and a disagreement between a reader and the machine is a candidate a
person reads.

A **prediction** (any kind whose id starts `mini.pair-prediction.`) is a second
reading of one pair by a seat that read something else: it commits
`{"proposal": <the proposal id's first sixteen characters>, "expect"}`. The
verdict pairs it with the execution and names the **reading** (`reading_for`):
both held; expectation failed and prediction held; expectation held and
prediction failed; both failed; no prediction; prediction unreadable. The
standing stays the proposer's expectation against the machine; a reading is a
name for how two readers fared and mints nothing. The records show that "both
failed" is as often two readers missing the same clause as the code doing what
nobody wrote.

A **kernel** may declare `unreadable`, the verdict it gives when it cannot read
its input at all; an execution on which either side is that verdict is
`unrunnable`, not a move (M11). The grounding kernels
(`conformance.kernel.span-occurs`, `conformance.kernel.grounding`) read one JSON
object with `value`, `span` and `document` and declare `UNREADABLE_INPUT`; a
control character a proposer wrote into a string is read as the line break that
was meant (`loads_strict(..., control_characters=True)`, strict first).

Two machine seats put the checks in front of a proposer as artifacts, whole,
where the legend would show 160 characters: `mini.kernel-source.v1` emits the
harness functions' source and `mini.kernel-rules.v1` their signatures and
docstrings and not one line of code, each with its sha256 in the commitments.
A proposer that reads the rules and not the code writes the rule's expectation,
which is the only reading that can part from the code without misreading it.

A **grid** is a source (`grid`, one cell per paragraph) enumerated by machine:
`mini.next-cell.v1` names the cell named least often so far in any artifact's
`cell` commitment, its own earlier outputs included, and ties go to the grid's
order. A port window is counted in cycles, so a proposer that must see one cell
and not its neighbours' draws a numbered kind of its own
(`mini.next-cell.1.v1` to `.3.v1`, the same seat). The proposer instantiates the
cell it is given and writes the rule's expectation; which cells get covered is
not its choice. `NextCellTests` holds the walk.

`forge/mini/manifests/experiments/README.md` is the pre-registration and the
reading of the eighteen runs that used these, in order, with what each shape
found and did not; `FAILURE_MODES.md` carries what they corrected.

---

## Part three: decisions, and what is genuinely still unbuilt

### Four things that are settled, not missing (R34)

The operator has decided these. They are not gaps and this document stops
listing them as absences:

| Decision | What it means |
|---|---|
| Standing stays `changes: "nothing"` | The permission layer will not grant an artifact a standing. Nothing in a mini run makes any other artifact stand or fall, and the slot exists only so the shape is visible. |
| Evidence is cut at blank lines | A paragraph is the unit. Tables, lists and headings are cut as prose, deliberately. |
| A kind's optional fields are strings | Structure goes inside `commitments` under a JSON-schema format, not into new field types. |
| One writer per run root | No locking. A second writer is detected on the next read, which is enough for a prototype and is a choice, not an oversight. |

### What attention still has, and still has not

The plug is built and the socket is now testable: one script drives the same
manifest with attention off and on, and `compare` sets the two roots side by
side. That was the missing half after Amendment 1, and it is here.

What is still missing is any reason to believe the one demonstration policy is a
good one. It has never been run against a live model. "Most unanswered
criticisms" remains a guess dressed as a rule, and on the blind-spot template it
finds nothing to prefer at all. Building a policy worth trusting means running
the same template several ways and reading the verdicts — which the machinery
now permits and nobody has done.

### Genuinely unbuilt

| Thing | Where it stands |
|---|---|
| An attention policy worth trusting | see above: testable now, untested |
| A live blind-spot run at any scale | one run of the shipped template on glm-5.3-flash and four of the conformance template on gemma4:31b exist (`FAILURE_MODES.md`); a dozen proposals over two cycles is not a survey of which checks are blind |
| A versioned per-attempt ledger | the record now names the request that produced each accepted reply and carries every attempt's usage, which closes the two concrete holes; binding phase, coordinate, envelope, outcome and disposition in a versioned record remains proposed (`AUDIT_RESPONSE.md` F6) |
| A recording executor below the adapter, across every mode | the generalisation of two audit findings; only the two specific tests exist |
| Comparison that says what differs | `compare` checks sources and responder identity, which is not equality of conditions |
| The `MAX_STEPS` boundary | whether a legal configuration can exhaust the inner loop before its verdict is untested |
| Recovering a citation from prose that carries no block id | the recogniser is deliberately narrow and finds only the shape the record has actually seen |
| A transport failure as a typed outcome rather than a stopped run | a live call that times out or disconnects raises out of the loop and leaves a partial record; `--retries` softens it and does not fix it |
| Concurrency | one writer, by decision above |

### One thing worth saying plainly about the blind-spot template

It found a defect on its first outing, and the defect was in my own standing
rule, not in any kernel. That is what this shape is good for. It is also a
warning: a handful of proposals over three cycles, written into a script by
hand, is not a survey of anything. The record shows what those pairs did.
