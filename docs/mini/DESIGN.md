# Mini prototype — design

Authority: `REQUEST.md`. Every section names the requirements it discharges.
Every reading of an open phrase is a numbered assumption in §12, and any one of
them can be overturned by a sentence from the operator.

This is the design as it was decided before the build. `SPEC.md` is written
afterwards, from the code, and is the document to read for what actually
exists.

## 1. Shape of the thing

One new package, `src/creib/forge/mini/`, beside the conformance harness and
sharing its foundations (canonical bytes, strict JSON, typed errors, offline
schema validation). Nothing under `src/creib/forge/conformance/` changes.

    src/creib/forge/mini/
      common.py     schema names, versions, small typed helpers
      kinds.py      the artifact template and the kind registry      (R4, R6)
      ports.py      the input-port-type registry                     (R5)
      formats.py    the format grammar and its compiler              (R8, R9, R10)
      failures.py   the per-kind failure policy                      (R11)
      evidence.py   cutting, tiers, the legend, citation checks      (R12)
      log.py        the append-only hash-chained log and replay      (R13)
      routing.py    where output and evidence go                     (R15, R16)
      policy.py     permission and authorisation                     (R17)
      signals.py    the signal registry                              (R19)
      attention.py  the attention-policy registry                    (R18, R20, R21)
      manifest.py   compile: manifest -> run plan                    (R5, R8, R14)
      executor.py   the scripted responder, and a live one           (R1)
      runner.py     the loop that walks stages and writes the record

    forge/mini/schema/      four schemas, one per document kind
    forge/mini/manifests/   example manifests
    forge/mini/policies/    the shipped default policy document
    tests/mini/             the offline suite

## 2. The one artifact template (R4, R6, R7)

There is no conjecturer type and no critic type in the code. There is one
template, and a **kind record** that fills it in:

```json
{
  "kind_id": "mini.conjecture.v1",
  "title": "Conjecture",
  "input_ports": [
    {"port_id": "problem",  "port_type": "problem",         "params": {}},
    {"port_id": "evidence", "port_type": "evidence_legend", "params": {"tiers": ["evidence"]}}
  ],
  "output_port": {"port_id": "out", "produces_kind": "mini.conjecture.v1"},
  "optional_fields": [],
  "format": null,
  "failure_policy": null
}
```

Conjecturer and critic ship as two such records in the default manifest. A
third kind is a third record; the example manifest of §7 adds one and the suite
proves it is compiled, scheduled, produced and logged with no code edit (R6).

A **submission** is a JSON object. Two keys are required and nothing else is
(R7, R9):

    {"body": "<any text>", "commitments": "<any text>"}

Three further keys are always recognised and always optional, because they are
properties of the template rather than of any kind (A13): `citations` (§5),
`about`, and `answers` (§9). A kind may name more in `optional_fields`; a key
that is neither required, recognised, nor declared is refused.

## 3. Input port types, extensible at compile (R5)

A **port type** says where a port draws from and how it renders. Four ship:

| port type | draws from | params |
|---|---|---|
| `problem` | the run's problem statement | — |
| `evidence_legend` | evidence blocks of the named tiers | `tiers` |
| `artifacts_of_kind` | artifacts already produced of one kind | `kind_id` |
| `scratch` | one scratch destination | `destination` |

A manifest extends the registry at compile time in a `port_types` section:

```json
{"port_type": "criticisms", "draws_from": {"artifact_kinds": ["mini.criticism.v1"]},
 "render": {"rule": "list_bodies", "header": "Criticisms so far"}}
```

`draws_from` names exactly one of `artifact_kinds` or `evidence_tiers`. The
render rules are a closed vocabulary: `list_bodies`,
`list_bodies_and_commitments`, `legend`, `text`. A kind naming a port type no
registry entry defines is refused at compile with `MINI_PORT_TYPE_UNKNOWN`, and
an extension whose render rule is outside the vocabulary with
`MINI_RENDER_RULE_UNKNOWN`.

## 4. Format: compiled at run start, freeform by default (R8, R9, R10)

A kind may carry a **format specification** for `body`, for `commitments`, or
for both. It is a small declarative grammar of five checks combined by `all_of`
(A4) — the smallest set that covers every shape the operator listed:

| check | field | what it requires |
|---|---|---|
| `keywords` | `keywords`, `case_sensitive` | every keyword occurs in the text |
| `sections` | `markers` | every marker occurs, at the start of a line, in the given order |
| `regex` | `pattern` | the pattern is found in the text |
| `line_shape` | `pattern`, `applies_to` (`every_line` / `any_line`) | the shape holds of every, or some, non-blank line |
| `json_schema` | `schema` | the text parses as strict JSON and validates against the fragment |

The whole specification is compiled **once, before the first call**, into a
checker (R8). A malformed specification — an unknown check, an uncompilable
regex, an invalid schema fragment, an empty keyword list — refuses the run
before anything is called, with `MINI_FORMAT_SPEC_INVALID`.

Absent a specification the format is **freeform**: nothing is checked beyond
the two fields being present and non-empty. A submission that fails a compiled
format is a typed `FORMAT_FAILURE` event on the record, never a silent
acceptance.

## 5. Evidence, split and tagged, without the wiring (R12)

Supplied sources are cut into **blocks**: paragraph-level spans separated by
blank lines, carrying the source id, the byte offsets of the span in the
source, and the digest of the span's text (A6). A block's id is a digest over
that content, so cutting is deterministic and a block is content-addressed.

Each block carries a **tier** tag. Two ship — `evidence` for supplied sources,
`generated` for artifacts the run produced — and the manifest extends the
vocabulary in a `tiers` section (A7). An unknown tier is refused.

A seat sees evidence as a **legend**: block id prefix, source, and excerpt, one
line per block, rendered by the `evidence_legend` port.

An artifact may carry `citations`: `[{"block": "<id or prefix>", "quote": "…"}]`.
Every citation is checked and produces one typed measure:

    MINI_CITATION_VERIFIED         the block resolves and the quote occurs in it
    MINI_CITATION_UNKNOWN_BLOCK    no block has that id
    MINI_CITATION_AMBIGUOUS        the prefix names more than one block
    MINI_CITATION_WITHHELD         the block exists but was not shown to this stage
    MINI_CITATION_QUOTE_MISMATCH   the quote does not occur in the block

The quote check is a byte check with whitespace folded on both sides, the same
reading h-EPI's grounding spans already use: folding never inserts whitespace
where the source had none, so a quote that joins words the source separated
still fails.

**"Except wiring"** is discharged literally: a citation measure is written to
the record and read by nothing that decides anything. It reaches no policy
decision, no routing decision, and no status — this prototype mints no status
at all.

## 6. The append-only log (R13)

One `log.jsonl` per run root, one canonical JSON line per event. An event:

```json
{"schema_version": "creib.mini.event.v1", "seq": 3, "prev": "<64 hex>",
 "type": "ARTIFACT_SUBMITTED", "stage_id": "crit-1", "kind_id": "mini.criticism.v1",
 "body_ref": "<64 hex>", "commitments_ref": "<64 hex>", "payload": {…},
 "event_id": "<64 hex>"}
```

`event_id` is a digest over the domain-framed canonical bytes of everything
else; `prev` is the previous event's `event_id`, and `prev` at sequence 0 is the
digest of the run header, which is fixed before any call. That is the hash
chain: flipping one byte anywhere breaks the event's own id and the next
event's `prev` (A8).

Bodies and commitments are **blob references**, not inline text: the bytes go
to `blobs/<digest>`, content-addressed, written once and never overwritten.

**Adding an artifact kind adds no event type.** The event carries `kind_id`,
`body_ref` and `commitments_ref`; a kind nobody had written when the log format
was fixed logs through the same shape. The event types are a closed set about
the *run*, not about the kinds: `RUN_STARTED`, `STAGE_ENTERED`,
`ARTIFACT_SUBMITTED`, `FORMAT_FAILURE`, `SUBMISSION_DROPPED`, `REFUSED`,
`EVIDENCE_BATCHED`, `ROUTED`, `ATTENTION_CHOSE`, `RUN_ENDED`.

One function applies one event to state; replay of the log alone rebuilds the
final state, and the state's digest is what a replay reproduces.

## 7. Order is the user's (R14)

The manifest declares the cycle as an ordered list of stages ending in an end
stage:

```json
"stages": [
  {"stage_id": "conj-1", "kind_id": "mini.conjecture.v1", "ports": ["problem", "evidence"]},
  {"stage_id": "conj-2", "kind_id": "mini.conjecture.v1", "ports": ["problem", "prior"]},
  {"stage_id": "note-1", "kind_id": "example.note.v1",    "ports": ["problem", "conjectures"]},
  {"stage_id": "crit-1", "kind_id": "mini.criticism.v1",  "ports": ["conjectures"]},
  {"stage_id": "note-2", "kind_id": "example.note.v1",    "ports": ["criticisms"]},
  {"stage_id": "end",    "end": true}
]
```

That is the operator's own example, and it ships as
`forge/mini/manifests/operator-example/manifest.json`. Compile refuses a stage
list that does not end in an end stage, an end stage anywhere but last, a stage
naming an unregistered kind, and a stage naming a port its kind does not
declare.

## 8. Routing (R15, R16)

Two routing sections, both lists of rules.

```json
"routing": {
  "artifacts": [
    {"from_kind": "mini.criticism.v1",
     "to": {"target": "port", "stage_id": "note-2", "port_id": "criticisms"}},
    {"from_kind": "mini.conjecture.v1", "to": {"target": "evidence_store", "tier": "generated"}},
    {"from_kind": "example.note.v1", "to": {"target": "scratch", "destination": "notes"}}
  ],
  "evidence": [
    {"from_tier": "evidence", "to": {"target": "port_type", "port_type": "evidence_legend"}},
    {"from_tier": "memory",   "to": {"target": "nowhere"}}
  ]
}
```

Destinations for an artifact: `port` (push into a named stage's port),
`evidence_store` (become generated-tier blocks), `scratch`, `nowhere`.
Destinations for a batch of evidence blocks: `port_type`, `scratch`, `nowhere`.

**The default, when a routing section is absent or empty**, is a *pull*: a port
draws from the kinds or tiers its port type declares, so a conjecturer→critic→
end run needs no routing at all. A declared rule replaces the default for the
one kind or tier it names, and leaves every other kind and tier on the default
(A9). A block routed `nowhere` stays in the store and is never shown — which is
exactly the condition the withheld-citation measure of §5 reports.

## 9. Permission and authorisation (R17)

A registered, versioned policy document ships at
`forge/mini/policies/mini.policy.default.v1.json`:

```json
{"schema_version": "creib.mini.policy.v1", "policy_id": "mini.policy.default.v1",
 "defaults": {"read": "declared_ports",
              "write": ["own_output", "evidence_store", "scratch"],
              "changes": "nothing"},
 "grants": []}
```

Read as three sentences, per artifact kind and per port:

- **read** — a stage may read exactly the ports its kind declares and its stage
  names. Nothing else.
- **write** — a stage may write its own output, the evidence store, and
  scratch. It may **not** push into another stage's input port. That is the
  default the brief names: a critic cannot write into a conjecturer's port.
- **changes** — a stage's output changes nothing about any other artifact's
  standing. This prototype mints no status; the slot exists so a later policy
  can grant one, and any value other than `"nothing"` is refused at compile
  with `MINI_POLICY_CHANGE_UNSUPPORTED` (A10) rather than silently ignored.

A run overrides it in the manifest's `policy` section, naming the base document
and adding grants:

```json
"policy": {"base": "mini.policy.default.v1",
           "grants": [{"kind_id": "mini.criticism.v1",
                       "may_write": [{"target": "port", "stage_id": "conj-2", "port_id": "prior"}]}]}
```

Overrides are typed and recorded: the compiled grant list is written into the
`RUN_STARTED` event. A read or write the policy forbids is refused with a typed
reason and the refusal is a `REFUSED` event on the record — not a silence, and
not an exception that loses the run.

`about` and `answers` are the template's two generic links between artifacts.
They carry no authority: naming an artifact in `about` changes nothing about
it. They exist because §11 needs a kind-blind way to see that one artifact
answers another.

## 10. Failure policy (R11)

Per kind, three fields (A5):

```json
"failure_policy": {"retries": 1, "tolerance": null, "action": "stop"}
```

- **retries** — a submission that fails its format is re-asked this many times,
  with the format error shown to the seat. That is the operator's
  retry-with-the-error-shown.
- A submission still failing after its retries is **dropped**: the stage
  produces nothing, a `SUBMISSION_DROPPED` event is written, and the run goes
  on. That is the operator's drop-the-submission.
- **tolerance** — how many dropped submissions of that kind the run permits. An
  integer, a fraction `{"numerator": a, "denominator": b}` of that kind's
  submissions, or `null` for unlimited.
- **action** — what happens when the tolerance is exceeded: `"stop"` ends the
  run typed (`stop_reason` on the `RUN_ENDED` event) — the operator's
  stop-the-run — or `"drop"` goes on dropping.

The shipped default is `retries: 1`, `tolerance: null`, `action: "stop"`, which
is exactly "drop after one retry": with unlimited tolerance the action never
fires and every exhausted submission is dropped.

## 11. Signals and attention (R18, R19, R20, R21)

A **signal** is a named, typed quantity computed from the record by a
registered function. Adding one is a registration; nothing that consumes
signals is edited (R19). Five ship:

    mini.signal.artifacts-by-kind             count per kind id
    mini.signal.citations-verified-by-artifact count per artifact id
    mini.signal.unanswered-criticisms-by-kind  count per kind id
    mini.signal.tokens-by-kind                 count per kind id
    mini.signal.cycle-count                    one integer

An **attention policy** is a registered function that reads *only* signals and
returns the stage to run next, or nothing at all, meaning "follow the declared
order". A policy declares the signals it reads; it is handed a view containing
exactly those and nothing else, so it cannot reach the record. Two ship:

- `mini.attention.off` — returns nothing, always. **This is the default** (R21).
  A run that declares no attention section runs the declared order exactly, and
  writes no attention event.
- `mini.attention.most-unanswered-criticisms` — of the stages still to run,
  prefers the one whose kind has the most unanswered criticisms about it,
  breaking ties by declared order.

An **unanswered criticism** is defined without naming any kind (A11): an
artifact that names another artifact in `about`, and that no artifact names in
`answers`. The signal counts them per kind of the artifact they are about. A
kind invented after the policy was written is therefore visible to it, because
the policy sees counts keyed by kind id and never a kind's name (R18).

That the machine decides and the user does not (R20) is what the shape
enforces: the policy is a function of signals, and the only thing the operator
can do is choose which registered policy is on.

## 12. Assumptions

Each is the smallest reading of an open phrase. One sentence overturns any of
them.

| # | Where the request is open | The reading taken |
|---|---|---|
| A1 | "mini" | A small conjecture–criticism run loop, built as a new package beside the conformance harness. Nothing existing changes. |
| A2 | "at manifest compile time" | A `compile` step that turns the manifest into a run plan, before any model is called. Every refusal in this design happens there or at submission, never silently at render. |
| A3 | "body and commitments … can accept any format" | Both are strings in the submission. Any structure the operator wants lives inside the string and is checked by the format specification. |
| A4 | "keywords and syntax that can be compiled" | Five checks — keywords, section markers, regex, line shape, JSON-schema fragment — combined by `all_of`. The smallest set covering everything the request lists. |
| A5 | "failure rates … customisable at submission" | `retries` / `tolerance` / `action` as in §10. All three actions the request names are reachable, and the default is "drop after one retry". |
| A6 | "evidence needs to be split" | Paragraph-level spans on blank lines, with byte offsets into the source. |
| A7 | "tagged the same way as full DeepReason" | A tier label from a registry the manifest extends; `evidence` and `generated` ship. |
| A8 | "the append-only log … the same way it currently does" | Typed events appended to `log.jsonl` and never rewritten; replay rebuilds state from the log alone. The per-event hash chain is added because the brief requires one; DeepReason's own log fences on sequence, not on a chain. |
| A9 | "where the contents of artifacts go" | A declared rule replaces the default for the one kind or tier it names; everything else stays on the default pull. |
| A10 | "what its output may CHANGE" | Only `"nothing"` is implemented. Any other value is refused at compile rather than accepted and ignored. |
| A11 | "the most unanswered criticisms" | An artifact naming another in `about` that no artifact names in `answers`, counted by the kind of the artifact it is about. Kind-blind on purpose. |
| A12 | attention `off` is "byte-identical to the declared order" | The sequence of stages entered in the record is exactly the declared order, and no attention event is written. |
| A13 | "anything else a kind adds is optional" | `citations`, `about` and `answers` are always-optional properties of the template; anything further must be declared by the kind, and an undeclared key is refused. |
| A14 | "where evidence goes after batching" | The batch is the whole cut of the supplied sources; its destination is declared per tier. |
| A15 | the live run | Permitted only after everything offline is delivered, only through the default manifest, and reported as what the record shows and nothing more. |

## 13. What this design does not attempt

- No status, no standing, no elimination. The prototype produces artifacts and
  measures; nothing is accepted, refuted, or ranked.
- No live-model dependence anywhere in the suite. Every test drives a scripted
  responder.
- No attention brain. The plug is built and one demonstration policy ships;
  what attention should become is written up honestly in `SPEC.md`.
