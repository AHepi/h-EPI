# Mini — the specification, written from what was built

Authority: `REQUEST.md`. Design and assumptions: `DESIGN.md`. This document is
written from the code that exists and passes its tests; every section names the
module, the schema, and the test that make it true. What is proposed and not
built is in the last section, and nowhere else.

---

## Part one: what this is, in plain words

You give it a problem, some source documents, and a description of the run you
want. It asks a model a series of questions in the order you wrote, keeps
everything it gets back, and writes down exactly what happened.

**An artifact** is one thing a seat produced — a conjecture, a criticism, or
whatever else you decided to have it produce. Every artifact has a **body** and
a set of **commitments**, and those two are all any artifact needs. Everything
else is optional.

**A seat** is not a kind of thing in the code. There is one template, and you
fill it in: what this seat is shown, and what it produces. Fill it in one way
and you have a conjecturer. Fill it in another way and you have a critic. Fill
it in a third way and you have something neither of us has named yet, and the
run handles it without a line of code being changed. That is the whole point of
the design, and the suite proves it by inventing a third kind inside a test.

**Evidence** is the sources you supplied, cut into paragraphs. Each paragraph
gets an identity that comes from its own words, so the same document always
cuts the same way. A seat is shown a list of these paragraphs with short
extracts. If an artifact quotes one, the run checks the quoted words really
occur in that paragraph and writes down what it found. That check decides
nothing. It is a note on the record, not a verdict.

**The record** is one file per run, one line per thing that happened, written
once and never rewritten. Each line carries a fingerprint of itself and a
fingerprint of the line before it. Change one character anywhere and reading
the record stops with a refusal. Reading the whole record back reproduces the
run exactly, and nothing else is needed to do that.

**Where things go** is yours to decide. The order the seats run in is a list
you write. Where each seat's output goes afterwards — to another seat, into the
evidence pile, onto a shelf, or nowhere — is a rule you write. If you write
nothing, an ordinary conjecture-then-criticism run works anyway.

**What a seat is allowed to do** comes from a permission document that ships
with the repository. By default a seat may read what its own description says
it is shown, may keep its own output, and may not push anything into another
seat's inbox. You can grant it that permission for one run; the grant is
written into the record, and so is every refusal.

**Attention** is switched off. When it is off, the run follows the order you
wrote, exactly. When you switch it on, a small function looks at counts drawn
from the record — how many artifacts of each sort, how many criticisms nobody
has answered — and picks what runs next. You cannot tell it what to pick; you
can only choose which function is in charge. That is deliberate, and the code
refuses a function that could be handed the record itself.

**Nothing here decides anything is true, or false, or better.** No artifact
stands or falls. The run produces things and writes down what happened. Judging
them is somebody else's job, later.

---

## Part two: the contracts

### 1. The artifact template and its kinds (R4, R6, R7)

**Module** `src/creib/forge/mini/kinds.py`.
**Schema** `forge/mini/schema/mini-kind.schema.json`.
**Tests** `tests/mini/test_template.py`.

A kind is a JSON record, either a section of the manifest's `kinds` array or a
file it names:

```json
{
  "kind_id": "mini.conjecture.v1",
  "title": "Conjecture",
  "input_ports": [
    {"port_id": "problem",  "port_type": "problem"},
    {"port_id": "evidence", "port_type": "evidence_legend", "params": {"tiers": ["evidence"]}}
  ],
  "output_port": {"port_id": "out", "produces_kind": "mini.conjecture.v1"},
  "optional_fields": [],
  "format": null,
  "failure_policy": null
}
```

`ArtifactKind` is the only class; `kind_from_dict` is the only reader. There is
no conjecturer class and no critic class, and
`test_both_shipped_seats_are_the_same_template` asserts the two shipped kinds
are instances of one type.

A kind's output port must produce the kind's own id
(`MINI_KIND_OUTPUT_MISMATCH`); two ports may not share an id
(`MINI_KIND_PORT_DUPLICATE`); a kind may not redeclare a template field
(`MINI_SUBMISSION_UNKNOWN_FIELD`).

**A new kind is a record and nothing else.**
`test_a_kind_declared_only_in_a_manifest_is_compiled_scheduled_produced_and_logged`
declares `example.note.v1` in a manifest written inside the test, runs it, and
asserts the kind was compiled, scheduled, produced, and logged. No file under
`src/` names it.

**The submission form.** `read_submission` admits exactly:

| field | required | what it is |
|---|---|---|
| `body` | yes | a string, in whatever format the kind's specification admits |
| `commitments` | yes | a string, likewise |
| `citations` | no | `[{"block": "<id or prefix>", "quote": "…"}]` |
| `about` | no | artifact ids this artifact is about |
| `answers` | no | artifact ids this artifact answers |
| anything in `optional_fields` | no | a string |

Anything else is `MINI_SUBMISSION_UNKNOWN_FIELD`. A missing `body` or
`commitments` is `MINI_SUBMISSION_MISSING_FIELD`; a non-string one is
`MINI_SUBMISSION_FIELD_TYPE`; a reply that is not a JSON object is
`MINI_SUBMISSION_NOT_JSON`. Each has its own test.

`about` and `answers` carry no authority: naming an artifact changes nothing
about it. They exist so §9 can count unanswered criticisms without knowing what
a criticism is.

### 2. Input port types, extended at compile (R5)

**Module** `src/creib/forge/mini/ports.py`.
**Schema** `mini-manifest.schema.json`, `$defs.port_type`.
**Tests** `tests/mini/test_ports.py`.

Four types ship:

| port type | draws from | required params |
|---|---|---|
| `problem` | the run's problem statement | — |
| `evidence_legend` | evidence blocks of the named tiers | `tiers` |
| `artifacts_of_kind` | artifacts produced of one kind | `kind_id` |
| `scratch` | one scratch destination | `destination` |

A manifest extends the registry in `port_types`:

```json
{"port_type": "criticisms",
 "draws_from": {"artifact_kinds": ["mini.criticism.v1"]},
 "render": {"rule": "list_bodies", "header": "Criticisms so far"}}
```

`draws_from` names exactly one of `artifact_kinds` or `evidence_tiers`. The
render vocabulary is `text`, `list_bodies`, `list_bodies_and_commitments`,
`legend`, and a rule that cannot render what the type draws from is refused.

Refusals, each with a test: `MINI_PORT_TYPE_UNKNOWN` (a kind names a type
nothing defines), `MINI_PORT_TYPE_DUPLICATE`,
`MINI_PORT_TYPE_DRAWS_FROM_INVALID`, `MINI_RENDER_RULE_UNKNOWN`,
`MINI_PORT_PARAMS_INVALID`, and `MINI_KIND_UNKNOWN` / `MINI_TIER_UNKNOWN` when
a type draws from something nothing declares.

### 3. Format, compiled at run start (R8, R9, R10)

**Module** `src/creib/forge/mini/formats.py`.
**Schema** `mini-kind.schema.json`, `$defs.format_spec`.
**Tests** `tests/mini/test_formats.py`.

Five checks, combined by `all_of`, per field:

| check | fields | what it requires |
|---|---|---|
| `keywords` | `keywords`, `case_sensitive` (default true) | every keyword occurs |
| `sections` | `markers` | every marker begins a line, in the order given |
| `regex` | `pattern` | the pattern is found |
| `line_shape` | `pattern`, `applies_to` (`every_line`, `any_line`) | the shape holds of every, or of some, non-blank line |
| `json_schema` | `schema` | the text is strict JSON validating against the fragment |

`compile_format_spec` runs once, inside `compile_manifest`, before any
responder is reached. A specification that cannot be compiled is
`MINI_FORMAT_SPEC_INVALID` and stops the run there: an unknown check, an
uncompilable expression, an empty keyword list, an unknown line scope, an
invalid schema fragment, and a fragment carrying `$ref` (nothing may be
fetched) each have a test.

Absent a specification the kind is freeform: `CompiledFormat.freeform` is true
and `failures()` returns nothing. `body` and `commitments` must still each
carry something that is not only whitespace; an empty one is a typed
`FORMAT_FAILURE` on the record carrying `MINI_SUBMISSION_MISSING_FIELD`.

A submission failing a compiled format is a `FORMAT_FAILURE` event carrying the
reasons, never a silent acceptance
(`test_a_body_missing_the_keyword_is_a_typed_failure_on_the_record`), and the
reasons are shown to the seat on the retry
(`test_the_format_error_is_shown_to_the_seat_on_the_retry`).

### 4. Failure policy (R11)

**Module** `src/creib/forge/mini/failures.py`.
**Schema** `mini-kind.schema.json`, `$defs.failure_policy`.
**Tests** `tests/mini/test_failures.py`.

```json
{"retries": 1, "tolerance": null, "action": "stop"}
```

- `retries` — how many times the seat is re-asked, with the format error shown.
- A submission still failing is **dropped**: `SUBMISSION_DROPPED` is written,
  the stage produces nothing, and the run goes on.
- `tolerance` — how many drops of that kind the run permits: an integer,
  `{"numerator": a, "denominator": b}` as a fraction of that kind's
  submissions, or `null` for unlimited.
- `action` — `"stop"` ends the run with `stop_reason` `format_failures_exceeded`
  once tolerance is passed, or `"drop"` goes on dropping.

The shipped default is one retry and unlimited tolerance, which is exactly
"drop after one retry": the action never fires in a default run
(`test_the_default_is_drop_after_one_retry_and_never_stops`). The boundary is
tested both ways: the last drop the tolerance permits does not stop the run,
and the next one does.

`MINI_FAILURE_POLICY_INVALID` covers an unknown action, an out-of-range retry
count, a zero denominator, and a tolerance that is neither a number nor a
fraction.

### 5. Evidence (R12)

**Module** `src/creib/forge/mini/evidence.py`.
**Tests** `tests/mini/test_evidence.py`.

`cut_source(source_id, raw, tier)` cuts at runs of blank lines, trims
whitespace from each span, and returns blocks carrying `span_start`,
`span_end`, `text_sha256`, `tier`, and a `block_id` that is a digest over that
content under the domain `creib.mini.evidence-block.v1`. Cutting is
deterministic in the bytes, and one changed byte gives different ids. A source
that is not UTF-8 is `MINI_SOURCE_INVALID`.

Tiers are a registry: `evidence` and `generated` ship, and a manifest's `tiers`
section extends it. An undeclared tier anywhere is `MINI_TIER_UNKNOWN`; a tier
declared twice is `MINI_TIER_DUPLICATE`.

`render_legend` renders a legend of id prefixes, source, tier, and a folded
excerpt.

`check_citations` gives one measure per claimed citation:

| code | when |
|---|---|
| `MINI_CITATION_VERIFIED` | the block resolves, was shown, and carries the quoted words |
| `MINI_CITATION_UNKNOWN_BLOCK` | no block has that id, or none was named |
| `MINI_CITATION_AMBIGUOUS` | the prefix names more than one block |
| `MINI_CITATION_WITHHELD` | the block exists but was not shown to this stage |
| `MINI_CITATION_QUOTE_MISMATCH` | the quoted words do not occur in it |

The quote check folds whitespace on both sides. Folding never inserts
whitespace where the source had none, so a quote joining words the source
separated still fails
(`test_a_quote_that_joins_words_the_source_separated_fails`), while a quote
differing only in line wrapping verifies.

**"Except wiring", discharged.** A measure is written into the
`ARTIFACT_SUBMITTED` event and read by nothing that decides anything: not
routing, not the permission layer, not any standing.
`test_the_measures_are_on_the_record_and_change_nothing` asserts a run carrying
a bad citation reaches the same terminal as one that does not. The signal of
§9 counts verified citations, which is about which stage runs next, never about
whether an artifact stands.

### 6. The append-only record (R13)

**Module** `src/creib/forge/mini/log.py`.
**Schema** `forge/mini/schema/mini-event.schema.json`.
**Tests** `tests/mini/test_log.py`.

One `log.jsonl` per run root, one canonical JSON line per event:

```json
{"schema_version": "creib.mini.event.v1", "seq": 3, "prev": "<64 hex>",
 "type": "ARTIFACT_SUBMITTED", "stage_id": "criticism",
 "kind_id": "mini.criticism.v1", "artifact_id": "<64 hex>",
 "body_ref": "<64 hex>", "commitments_ref": "<64 hex>",
 "payload": {…}, "event_id": "<64 hex>"}
```

`event_id` is a digest over the domain-framed canonical bytes of every other
field. `prev` is the previous event's `event_id`; at sequence 0 it is the
digest of the run header, fixed before any call and written beside the log as
`run-header.json`.

Reading verifies all three: the identity replays (`MINI_LOG_EVENT_ID_MISMATCH`),
the sequence is unbroken (`MINI_LOG_SEQUENCE_BROKEN`), and each event links to
the one before (`MINI_LOG_CHAIN_BROKEN`). One flipped character inside a blob
reference — still well shaped, still hexadecimal — is refused
(`test_flipping_one_byte_of_an_event_breaks_its_own_identity`).

Ten event types, all about the run: `RUN_STARTED`, `STAGE_ENTERED`,
`ARTIFACT_SUBMITTED`, `FORMAT_FAILURE`, `SUBMISSION_DROPPED`, `REFUSED`,
`EVIDENCE_BATCHED`, `ROUTED`, `ATTENTION_CHOSE`, `RUN_ENDED`.

**A new kind adds no event type.** Bodies and commitments are blob references
into `blobs/<digest>`, written once and never overwritten, and the kind is a
field of the event. `test_a_new_artifact_kind_adds_no_event_type` runs a kind
invented in the test and asserts the event types stay inside the shipped set;
`test_body_and_commitments_are_blob_references_not_inline_text` asserts the
body text is not in the log at all.

`apply_event` is the one function that changes state; `replay(path, genesis)`
rebuilds state from the log alone, and its digest equals the digest the run
reported. Running the same plan against the same script twice writes
byte-identical logs.

Blobs verify their own digest on read (`MINI_BLOB_CORRUPT`) and refuse a
reference that is not there (`MINI_BLOB_MISSING`). A run refuses a root that
already holds a record (`MINI_RUN_ROOT_OCCUPIED`): a record is never written
over.

### 7. Order, and where things go (R14, R15, R16)

**Modules** `src/creib/forge/mini/manifest.py`, `routing.py`, `runner.py`.
**Tests** `tests/mini/test_wiring.py`.

Stages are an ordered list ending in an end stage. The operator's own example
runs as written and ships as
`forge/mini/manifests/operator-example/manifest.json`:

    conjecture-1 → conjecture-2 → note-1 → criticism → note-2 → end

`test_the_operators_own_order_runs_as_written` asserts the stage sequence and
the kinds produced; `test_the_shipped_operator_example_manifest_compiles_and_runs`
runs the committed file.

Refusals: `MINI_STAGE_NO_END`, `MINI_STAGE_END_NOT_LAST`,
`MINI_STAGE_DUPLICATE`, `MINI_KIND_UNKNOWN`, `MINI_PORT_UNKNOWN`, each tested.

**Routing.** Two lists of rules:

```json
"routing": {
  "artifacts": [{"from_kind": "mini.criticism.v1",
                 "to": {"target": "port", "stage_id": "note-2", "port_id": "criticisms"}}],
  "evidence":  [{"from_tier": "evidence",
                 "to": {"target": "port_type", "port_type": "quiet_evidence"}}]
}
```

An artifact goes to a `port`, the `evidence_store` as a named tier, `scratch`,
or `nowhere`. A batch of evidence goes to a `port_type`, `scratch`, or
`nowhere`. Every one of those six destinations has a test that drives it end to
end.

**The default is a pull.** With no routing, a port draws from the kinds or
tiers its type names, so a conjecture-then-criticism run needs no routing at
all (`test_with_no_routing_a_critic_still_sees_the_conjectures`). A declared
rule replaces the default for the one kind or tier it names. A tier routed
`nowhere` is in the store and shown to nobody, which is what the withheld
citation measure of §5 reports.

Refusals: `MINI_ROUTE_TARGET_UNKNOWN`, `MINI_ROUTE_INVALID` (missing what a
target needs, a kind or tier routed twice, a stage or port that does not
exist, the end stage as a destination, an unknown port type),
`MINI_TIER_UNKNOWN`.

### 8. Permission and authorisation (R17)

**Module** `src/creib/forge/mini/policy.py`.
**Document** `forge/mini/policies/mini.policy.default.v1.json`.
**Schema** `forge/mini/schema/mini-policy.schema.json`.
**Tests** `tests/mini/test_policy.py`.

```json
{"schema_version": "creib.mini.policy.v1",
 "policy_id": "mini.policy.default.v1",
 "defaults": {"read": "declared_ports",
              "write": ["own_output", "evidence_store", "scratch", "nowhere"],
              "changes": "nothing"},
 "grants": []}
```

- **read** — a stage may read the ports its kind declares and its stage names.
  A grant may narrow that to a whitelist of port types.
- **write** — a stage may write its own output, the evidence store, scratch,
  and nowhere. `port` is absent from the defaults, so pushing into another
  stage's input port needs a grant naming that exact stage and port.
- **changes** — `"nothing"`. Any other value is
  `MINI_POLICY_CHANGE_UNSUPPORTED` at compile. The slot is there so a later
  policy can grant a standing; this prototype mints none, and refuses to
  pretend otherwise.

A run overrides in `policy.grants`. The compiled grants are written into the
`RUN_STARTED` event (`test_the_overrides_are_recorded_on_the_run`).

The three tests the request asks for, by name:
`test_the_default_forbids_a_critic_writing_into_a_conjecturers_port` (one
`REFUSED` event carrying `MINI_POLICY_WRITE_REFUSED`, no `ROUTED` event),
`test_an_override_permits_the_write` (no refusal, one `ROUTED` event), and the
refusal is on the record in both. A forbidden read is
`MINI_POLICY_READ_REFUSED`, the stage produces nothing, and the run continues.

### 9. Signals and attention (R18, R19, R20, R21)

**Modules** `src/creib/forge/mini/signals.py`, `attention.py`.
**Tests** `tests/mini/test_attention.py`, `tests/mini/test_architecture.py`.

**Signals.** A declaration and a function, registered together. Five ship:

| signal | unit | what it counts |
|---|---|---|
| `mini.signal.artifacts-by-kind` | artifacts | per kind id |
| `mini.signal.citations-verified-by-artifact` | citations | per artifact id |
| `mini.signal.unanswered-criticisms-by-kind` | criticisms | per kind id |
| `mini.signal.tokens-by-kind` | tokens | per kind id |
| `mini.signal.cycle-count` | cycles | returns to the first stage entered |

Every one is keyed by an id the record already carries, never by a name in the
code. `test_a_new_signal_is_a_registration_and_nothing_else` registers a sixth
from inside a test and reads it off a real run; no consumer changed.
`MINI_SIGNAL_DUPLICATE` and `MINI_SIGNAL_UNKNOWN` are tested.

**Attention policies.** A policy declares the signals it reads and a function
of exactly `(signals, stages)`. Two ship:

- `mini.attention.off` — returns nothing. **The default.** A run declaring no
  attention section, and a run declaring `off`, enter the same stages in the
  same order, and neither writes an attention event
  (`test_off_runs_the_declared_order_and_writes_no_attention_event`).
- `mini.attention.most-unanswered-criticisms` — of the stages still to run,
  prefers the one whose kind has the most unanswered criticisms about it, ties
  broken by declared order. `test_the_demonstration_policy_reorders_the_declared_order`
  shows it moving a later conjecturer ahead of a note.

**An unanswered criticism** is defined without naming a kind: an artifact that
names another in `about` and that no artifact names in `answers`, counted
against the kind of the artifact it is about.
`test_the_policy_sees_a_kind_it_was_never_written_for` drives the shipped
policy on kinds called `invented.kind.v9` and `another.kind.v9` and it picks
correctly (R18).

**The architecture check** (`tests/mini/test_architecture.py`) is what makes
"the machine, not the user" structural rather than a promise:

1. `attention.py` imports nothing that touches the record — asserted by parsing
   its own source.
2. Every registered policy's function takes exactly `(signals, stages)`.
3. A function that would take a third parameter is refused at registration with
   `MINI_ATTENTION_SIGNATURE`. There is no parameter through which a record
   could arrive.
4. A policy asking for a signal it did not declare is refused when it runs with
   `MINI_ATTENTION_UNDECLARED_SIGNAL`.
5. Every shipped policy, driven with a recording view, reads only what it
   declared.

A policy choosing a stage that is not pending is `MINI_ATTENTION_STAGE_UNKNOWN`.

### 10. Compile, and the loop

**Modules** `src/creib/forge/mini/manifest.py`, `runner.py`, `executor.py`.
**Command line** `tools/run_mini.py` — `compile`, `run`, `replay`.

`compile_manifest` reads the manifest, validates it against
`mini-manifest.schema.json`, and builds the tier list, the port-type registry,
the kind registry, the compiled formats, the stages, the routing, the policy,
the attention policy, and the sources — refusing at the first thing that does
not resolve. It then fixes a run header, whose digest is the run id and the
genesis of the hash chain.

`run_mini` walks the stages: it asks attention for the next one when attention
is on, checks the reads the policy permits, renders the brief from the declared
ports, asks the responder, reads and checks the submission, applies the failure
policy, checks the citations, writes `ARTIFACT_SUBMITTED`, and routes the
output through the policy. Every outcome — accepted, failed, dropped, refused,
routed — is an event.

`ScriptedResponder` is the only responder in the offline suite. It returns
prepared replies per stage in order, so retries consume the next one and a
script can answer badly then well. It calls nothing, and no test in
`tests/mini/` reaches a network.

---

## Part three: what is proposed and not built

Written plainly, because a specification that quietly omits its gaps is worse
than no specification.

**Attention has a plug and no brain.** What ships is the shape: a signal
registry, a policy registry, a view that refuses to answer for a signal a
policy did not declare, and one demonstration policy of about ten lines. What
does not exist is any reason to believe that policy is a good one. It has never
been run against a live model, it has no measure of whether re-ordering
produced anything better, and "most unanswered criticisms" is a guess dressed
as a rule.

What attention should become, on the evidence this build produced: the signal
interface is the durable part and should stay; the policy is the disposable
part and should be treated as one. A real attention policy needs a way to be
*compared against the declared order on the same run*, which this prototype
cannot do — there is no way to run one plan two ways and set the results beside
each other. That, not a cleverer policy, is what should be built next. Until it
exists, the honest default is off, which is what ships.

**Also proposed and not built:**

- **A standing.** `changes: "nothing"` is the only value implemented. The slot
  and the refusal are built so the shape is visible; nothing behind them is.
- **Anything that compares two runs.** The record supports it — same plan, same
  script, byte-identical log — but there is no command that pairs two roots.
- ~~**A live responder.**~~ Built after the offline delivery, when the operator
  supplied a key: `LiveResponder` in `executor.py` builds a request and hands it
  to the conformance harness's own `OllamaChatExecutor`, so there is one place
  in this repository where a key is touched. One live run is recorded; see
  `DELIVERY.md`.
- **A place for citations a model will actually use.** Two live runs, two
  opposite behaviours: one model grounded its claims correctly inside the body
  prose and left the `citations` field empty; the other used the field and put
  nothing citable in it. The byte-check is not what needs work. See
  `docs/mini/FAILURE_MODES.md` M1 and M2.
- ~~**Keeping a reply that was refused.**~~ Fixed after a live run exposed it:
  every reply is stored before it is read, a `FORMAT_FAILURE` names it in
  `body_ref`, and a `SUBMISSION_DROPPED` lists them all in `refused_refs`.
  `docs/mini/FAILURE_MODES.md` H1.
- **Deciding what to do about a fenced reply.** A reply that is correct JSON
  inside a markdown code fence is refused as unreadable. Whether the reader
  should strip the fence, or the brief should carry the cost, is an open fork
  stated in `docs/mini/FAILURE_MODES.md` M4. Nothing was changed either way.
- **Noticing that a stage's input port was empty.** A stage whose port draws
  from a kind that produced nothing runs anyway, and nothing records that it
  did. See `docs/mini/FAILURE_MODES.md` M3.
- **Cycles as a first-class idea.** The `cycle-count` signal counts returns to
  the first stage entered. A run whose attention policy re-orders freely makes
  that number harder to read than it looks. Nothing depends on it yet.
- **Evidence beyond paragraphs.** Cutting is at blank lines. Tables, lists and
  headings are cut the same way as prose, which is right for the sources the
  suite uses and probably wrong for a real document.
- **A second submission field type.** A kind's `optional_fields` admit strings
  only. A kind wanting a structured extra field must put it in `commitments`
  under a JSON-schema format.
- **Concurrency.** One writer, one run root, no locking. A second process
  writing the same log would corrupt it and the chain would catch it on the
  next read, which is detection, not prevention.
