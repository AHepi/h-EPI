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

---

# Amendment 1 — design

Authority: `REQUEST.md`, Amendment 1, R22–R28. Interpretations are numbered
from **B1**, kept apart from the A-series above so either set can be overturned
alone. Where this section and the design above disagree, this section governs
and names what it supersedes.

## 14. One routing rule (R22)

The asymmetry being removed: as built, a declared route for an artifact kind
*added* a destination while the default pull still delivered that kind to every
port drawing it, whereas an evidence tier's route *replaced* its default. Both
now replace.

**What a port draws, for a kind K:**

| K's routes | the ports K reaches |
|---|---|
| none declared | every port whose drawn kinds include K — the default |
| `nowhere` | none |
| `port(S, P)` | the port `P` of stage `S`, and no other |
| `scratch(D)` | scratch ports whose destination is `D` |
| `evidence_store(T)` | no artifact port; K's blocks reach evidence ports drawing tier `T` |

**And for an evidence tier T, the same shape:**

| T's routes | the ports T's blocks reach |
|---|---|
| none declared | every evidence port drawing T — the default |
| `nowhere` | none |
| `port_type(P)` | evidence ports of type `P` |
| `scratch(D)` | scratch ports whose destination is `D` |

**B1 — a kind or tier may carry more than one route.** "A push is additive on
top of whatever the route allows" has content only if a route and a push can
coexist, so `routing.artifacts` and `routing.evidence` may name one kind or tier
more than once, and its reach is the union of what those routes allow. This
supersedes the built refusal of a kind routed twice. `nowhere` may not be
combined with any other route for the same kind or tier: that is a typed
refusal, because the union of "nowhere" and anything is not nowhere.

**B2 — "reaches no port" is tested as absence from every port**, by rendering
every stage's brief and asserting the artifact's body appears in none of them —
not by asserting a routing event was written.

## 15. Cycles (R23)

**Supersedes** R14 as built (the stage list ran once) and A12 (attention's
scope). The stage list is the body of one cycle. The runner repeats it.

**The stop is the host's, and typed.** Three sources, checked in this order
before each cycle begins, and no other:

| stop | declared as | reason recorded |
|---|---|---|
| cycle cap | `cycles.max_cycles` | `cycle_cap` |
| budget cap | `cycles.max_calls` | `budget_cap` |
| a registered stop condition | `cycles.stop_condition` | `stop_condition:<id>` |

Nothing a seat writes can end a run. The end stage remains, and ends the
*cycle*, not the run; a run ends only on one of the three above, or when a
stage's failure tolerance is exceeded, which was already the host's decision.

**B3 — the budget cap counts model-seat calls, retries included.** Machine
seats cost nothing and are not counted. A run reaching the cap stops before the
next cycle, never mid-cycle: a half-finished cycle is harder to read than one
fewer cycle.

**B4 — the event record moves to `creib.mini.event.v2`.** Adding the cycle
coordinate changes the shape of a record, which this repository treats as a
version change. The v1 schema file is kept unchanged, the reader reads both, and
a v1 event replays under the v1 domain with cycle 0 — so the three runs already
committed stay readable and the failure-mode register's replay instructions stay
true.

**Windows.** A port declaration may carry `window`, evaluated against the cycle
coordinate of what it draws:

| window | draws |
|---|---|
| `all` (default) | every cycle |
| `this_cycle` | the cycle now running |
| `previous_cycle` | the cycle before this one |
| `{"last_n": N}` | the last N cycles, this one included |

**B5 — windows apply to evidence blocks as well as artifacts.** A block carries
the cycle it was batched in; supplied sources are batched before cycle 1 and
carry cycle 0, so `this_cycle` on an evidence port draws only what the run
itself generated.

**B6 — a stop condition is a registry, like signals and attention.** It declares
the signals it reads, is handed a view of exactly those, and returns a reason or
nothing. Two ship: `mini.stop.never`, the default, and
`mini.stop.no-artifact-last-cycle`, which stops when a whole cycle produced
nothing. A stop condition cannot reach the record for the same reason an
attention policy cannot.

**B7 — `max_repeats` bounds a stage per cycle.** Declared per stage, default 0.
Within one cycle a stage runs at most `1 + max_repeats` times, so the record's
stage count is bounded by the manifest whatever attention does. Attention may
reorder the stages remaining in the current cycle and may re-offer a stage only
while its repeat budget for that cycle is unspent.

**The cycle-count signal counts real cycles**, and its test drives the runner
over three cycles rather than assembling a state by hand.

## 16. The format, rendered in full (R24)

**Strengthens** R8 and R10 as built, where the brief carried a one-line
description per check and the schema text was never shown. `describe` now
renders the compiled format in full — the keyword list, the section markers, the
expression, the line shape, and the JSON schema as text — into the brief on
every attempt, first included. On a retry the validation error is shown beside
that rendering, not instead of it.

The test asserts the schema text appears in the **dispatched request bytes**, so
it is driven through the live responder against a stand-in executor and reads
the body that would have gone over the wire.

## 17. Machine seats (R25)

A stage declares `seat`: `"model"` (default) or `"machine"`.

**B8 — a machine seat is resolved by kind id**, as the amendment says: a
registry maps a kind id to a deterministic function of the record. The function
is handed a typed context — the plan, the state, the stage, the blob store — and
returns a reply string in exactly the shape a model would have returned, so the
same submission reader and the same compiled format check it. A machine seat
that returns something its kind's format refuses is a `FORMAT_FAILURE` like any
other; it is not privileged.

**Provenance.** Every `ARTIFACT_SUBMITTED` and every `FORMAT_FAILURE` records
`seat`, so a reading and a function of the record are never confused when the
record is read back.

## 18. The blind-spot run (R26)

The template hunts for places where one of this prototype's own checks fails to
see something it claims to see.

**B9 — what a proposal, a kernel and the catalogue are.** The amendment names
"the executor that runs a proposal through the kernel functions" without saying
what a kernel function is here, so the smallest self-contained reading:

- A **kernel function** is a registered, deterministic verdict of this
  prototype's own machinery over a piece of text — the citation quote check, the
  keyword format check, the block cutter. Registered, so more can be added.
- A **transform** is a registered, deterministic rewrite of a piece of text —
  folding whitespace, changing case, wrapping in a code fence, reordering
  paragraphs.
- A **proposal** commits JSON naming a kernel, a transform, and an input, and
  claims the kernel's verdict moves, or does not, under that transform.
- The **catalogue** is a committed JSON document listing the kernel/transform
  pairs already known, and whether each is known to move. It is supplied as a
  run source, so it is cut into blocks and the critic can cite it like any other
  evidence.
- The **machine executor** applies the transform, runs the kernel before and
  after, and commits `moved` or `unchanged` with both verdicts.

**B10 — the standing rule**, computed by the machine verdict seat and filled by
a model verdict seat under the same schema:

| executed | catalogue | standing |
|---|---|---|
| moved | does not list the pair | `candidate point` |
| moved | says it does not move | `defect` |
| unchanged | says it moves | `defect` |
| unchanged | does not list the pair | `rejected` (it is an invariance; see §19) |
| either | agrees with what happened | `rejected` |

A candidate point is a boundary nobody had written down. A defect is the
catalogue and the execution DISAGREEING, in either direction. Neither is
promoted by anything in the loop: the verdict is an artifact, it mints no
standing, and a person turns the last one into boundary points or does not.

**B10 was first written wrongly**, and the run found it. It said "unchanged and
catalogued is a defect", which marked a pair the catalogue correctly lists as
not moving, and that did not move, as a defect — the catalogue agreeing with the
execution, recorded as a fault. The rule now turns on agreement, and the
catalogue's own claim is carried on the verdict beside `catalogued` so the
reading is visible on the record rather than buried in the rule. The first
version is left here because a design document that silently acquires the right
answer is not a record of anything.

**The shape of the run**: several proposer stages of one kind drawing earlier
proposals and earlier verdicts at window `all`; one machine executor; one critic
reading proposals beside executions and citing the catalogue; one verdict stage
drawing this cycle's executions and criticisms at `this_cycle` and all earlier
verdicts at `all`. Three cycles under the scripted responder.

## 19. Comparison, never optimisation (R27)

`compare` takes two run roots, prints their verdict artifacts side by side, and
prints each root's executed-invariance ledger.

**B11 — "byte-identical sources and script" is made checkable.** The script was
not in the record, so a run now records a `responder_id` on `RUN_STARTED`: the
digest of the script file for the scripted responder, and `model:<name>` for the
live one. `compare` refuses two roots whose source digests or responder ids
differ, and says which. The manifests may differ — that is the point of
comparing.

**B12 — the executed-invariance ledger** is the kernel/transform pairs the
catalogue does not list, that a **machine** seat executed, and that came out
`unchanged`. A model's prose about an invariance never enters the ledger; only a
machine seat's executed result does.

**B13 — never promote, stated as this repository states it.** `compare` prints
no score, no total, no ordering, and no count presented as merit. A template's
own verdict counts are never an objective: a run that produced more candidate
points is not thereby a better run, and nothing in this prototype may be tuned
to raise that number. A `--score` flag is refused by name, so the refusal is
reachable and tested rather than merely intended. This is h-EPI's own rule —
"the report never ranks models, computes scores, or uses words like best, worst,
pass, or accuracy" — applied to a mini run's own output.

## 20. What Amendment 1 does not change

The permission layer still mints no standing; `changes: "nothing"` is still the
only implemented value. Citations are still measures that decide nothing. The
record is still append-only and hash-chained, and a refused reply is still kept.
Attention is still off by default, and a stop condition is not attention: it
decides whether the run continues, never which stage runs next.

---

# Amendment 2 — design

Authority: `REQUEST.md`, Amendment 2, R29–R36. Interpretations are numbered from
**C1**, apart from the A- and B-series. Where this section and anything above
disagree, this governs and names what it supersedes.

## 21. Scripts addressed by coordinate (R29)

The scripted responder gains a second script form, and keeps the first.

```json
{"criticise": {"1": ["reply for cycle 1, attempt 0", "attempt 1"], "2": ["…"]}}
```

**C1 — the form is told apart by shape, not by a flag.** A stage whose value is
a list is an ORDERED script, consumed as before; a stage whose value is an
object is a COORDINATE script, keyed by cycle and then indexed by attempt. Both
may appear in one script, so a manifest's stages migrate one at a time.

**Which tests migrate.** The blind-spot script migrates, because R29's own test
needs it. Every other test keeps the ordered form, because the ordered form is
the shorter thing to write when a stage runs once per run and nothing re-orders
it. `SPEC.md` says which is which.

**C2 — what "differ only where the policy re-ordered" comes to on this template.**
The demonstration policy prefers the stage whose kind has the most unanswered
criticisms, counted through `about`, and the blind-spot script's artifacts name
nothing in `about`. So on this template the policy finds nothing to prefer and
returns nothing, and the two roots' logs differ only in the run header's
attention field. That is the result, and it is worth having: attention switched
on but idle is the same run as attention off, which is what `off` being the
default is supposed to mean. A second test, on a manifest where the policy does
re-order, shows the coordinate script delivering each stage its own reply across
a re-ordering — the thing the ordered form could not do.

## 22. Fenced replies (R30)

`read_submission` strips a leading ```` ``` ```` fence (with or without a
language tag) and its closing fence before reading, and records the recovery.

**C3 — the recovery is named on the artifact, and the raw reply is referenced
from it.** Every reply was already stored verbatim before being read (H1's fix).
The `ARTIFACT_SUBMITTED` event now names that blob in `reply_ref` and lists what
was recovered in `recovered`, so the stored bytes and the parsed submission are
both reachable from one event and cannot be mistaken for each other. A reply
that is not JSON after the fence is stripped is a `FORMAT_FAILURE` exactly as
before.

**Supersedes** `FAILURE_MODES.md` M4's open fork, in the direction of stripping.

## 23. Citations, both ends (R31)

**The declaring end.** A citation entry must carry a non-empty `block` and a
non-empty `quote`. An entry missing either is `MINI_SUBMISSION_FIELD_TYPE`,
which reaches the record as a `FORMAT_FAILURE` — not as an unknown block. The
wire schema sent to a live model carries the same requirement.

**The recovering end.** After reading, the reader scans `body` for bracketed
pairs of the form `[<hex prefix>] "quoted words"` and adds each to `citations`
marked `recovered: prose`. Recovered citations are byte-checked exactly as
declared ones; the measure carries which it was, so nobody has to guess.

**C4 — what the recogniser matches.** A bracketed run of 8 to 64 hexadecimal
characters, then optional whitespace, then a quoted run in straight or curly
quotes. It is deliberately narrow: it recovers the shape the record has actually
seen a model use, and it does not try to find citations in prose that does not
carry a block id.

**C5 — a recovered citation never displaces a declared one.** Recovery appends;
a block cited both ways produces two measures. Counting citations is not a
purpose this prototype has, so the duplicate costs nothing and hiding it would
cost the reader.

**The brief shows one worked example** of a declared citation, built from a real
block id the stage can see, so the shape a seat is asked for is demonstrated
rather than described.

**Supersedes** `FAILURE_MODES.md` M1 and M2 as open items.

## 24. An empty input port (R32)

A stage whose declared artifact port draws nothing writes `PORT_EMPTY` naming
the port, before dispatch. It is a notice, not a refusal.

**C6 — only artifact ports.** An evidence port with nothing admitted, or a
scratch port with an empty shelf, is the ordinary state of a run's first cycle
and says nothing. An artifact port drawing nothing is the condition M3 recorded,
where a critic criticised with nothing to criticise.

The kind's failure policy gains `skip_on_empty_port`, default **false**, so
today's behaviour is unchanged; a stage set to skip writes its `PORT_EMPTY` and
then a `SUBMISSION_DROPPED` carrying the reason, and produces nothing.

**PORT_EMPTY is a new event type.** It is about the run, not about any kind, so
"a new artifact kind adds no event type" is untouched: the vocabulary grows when
the run learns to notice something new, never when a manifest declares a kind.

## 25. Two calls per artifact (R35 a, b)

**Supersedes** the one-call production of an artifact assumed everywhere before.

An artifact is produced by two calls by default:

| call | is shown | returns |
|---|---|---|
| body | the stage's full brief: every declared port, the evidence legend, the compiled format, the worked citation example | `body`, and optionally `citations`, `about`, `answers`, and the kind's own optional fields |
| commitments | the body text, and the compiled format for `commitments`. Nothing else — no problem, no evidence, no other artifact, no earlier commitments | `commitments` |

The two replies are joined into one artifact. The record carries **both requests
and both replies**, each as a blob, on the `ARTIFACT_SUBMITTED` event under
`calls`, so that the commitments were written blind is a thing anyone can check
from the record rather than a thing this document asserts.

**C7 — what "and nothing else" is taken to exclude, exactly.** The second call's
prompt contains the body text, the rendered commitments format, and a one-line
instruction. It contains no problem statement, no block id, no source excerpt,
no other artifact's text, and no commitments from any earlier artifact. The test
asserts absence of each in the dispatched request bytes rather than trusting the
construction.

**C8 — the format is split across the calls.** A kind's `body` format checks the
first call's reply; its `commitments` format checks the second call's. A failure
in either is a `FORMAT_FAILURE` naming the phase, and the retry re-asks **that
call** with its own error shown, not the other.

**C9 — `commitment_call: single` keeps the old shape**, per kind, and is
disclosed: the artifact's record carries `commitment_call` either way, so a
one-call artifact is never mistaken for a blind-written one.

**C10 — a machine seat makes one call and says so.** A machine seat computes the
whole artifact from the record; there is no second call to make blind, and the
record carries `commitment_call: "machine_single"` rather than pretending
otherwise.

## 26. One verdict node per cycle (R35 c)

**Every cycle ends with exactly one stage of kind `mini.verdict.v1`**, and
compile refuses a manifest without one, with more than one, or with one that is
not the last stage before the end stage: `MINI_VERDICT_MISSING`,
`MINI_VERDICT_DUPLICATE`, `MINI_VERDICT_NOT_LAST`.

**C11 — this binds every manifest, and the shipped ones are rebuilt.** The
default and operator-example manifests gain a verdict stage. A structural rule
that the repository's own examples do not follow is not a rule.

**C12 — attention may not reach the verdict early.** The verdict stage is
withheld from the set attention chooses among until it is the only stage left in
the cycle, so "ends with" survives a re-ordering policy.

The verdict's body call sees everything the cycle produced, through its declared
ports and their windows; its commitments call sees only its own body, exactly as
every other artifact's does. Its seat may be model or machine.

## 26a. What the commitments call sees is declared (R37)

**Corrects §25 as built.** The commitments call's exposure was fixed in code.
It is now declared, and the default is what §25 describes.

A kind may carry `commitment_ports`, a list of its own declared input ports:

```json
{"kind_id": "…", "input_ports": [{"port_id": "problem", …}, {"port_id": "evidence", …}],
 "commitment_ports": ["problem"]}
```

**C13 — the list is the kind's own ports, rendered independently of the stage.**
`commitment_ports` must name ports the KIND declares; a port it does not declare
is `MINI_PORT_UNKNOWN` at compile. What the stage named for the body call does
not constrain it, because the two calls are two different questions and the
operator configuring the run is entitled to answer them differently. Absent the
field, the list is empty and the second call sees the body alone, exactly as
before.

**C14 — the record says what the second call saw.** `ARTIFACT_SUBMITTED` carries
`commitment_ports`, so "written blind" is a fact read off the record rather than
assumed from the default. A reader who finds an empty list knows the call saw
nothing but the body; a reader who finds ports listed knows precisely what else
reached it.

The test that asserts absence in the dispatched bytes now asserts it **of the
default**, and a second test shows a declared port arriving in the second call's
bytes — so the default is checked as a default rather than as a law.

## 27. Four decisions, not gaps (R34)

`SPEC.md` records these as settled, and stops listing them as absences: the
permission layer's `changes` stays `"nothing"`; evidence is cut at blank lines;
a kind's optional fields are strings; one writer per run root.

## 28. What Amendment 2 does not change

The record is still append-only and hash-chained, and a refused reply is still
kept. Citations are still measures that decide nothing. Attention is still off
by default and still cannot reach the record. `compare` still ranks nothing. The
stop is still the host's.
