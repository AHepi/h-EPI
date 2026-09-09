# Mini prototype — delivery

What was built, requirement by requirement, and the command that proves each.

Branch `claude/mini-prototype`. Nothing is merged; merging is the operator's
act.

## How to check any of this yourself

```sh
python3.12 tools/check.py bootstrap
source .venv/bin/activate
export PYTHONPATH=src
python tools/check.py all                     # lint, the whole suite, pilots, citations
python -m unittest discover -s tests/mini     # the mini suite alone, 204 tests
```

The full suite is **532 tests, 0 failed** — 250 that were there before, 282
added here. No test calls a model. `python tools/check.py all` is green at every
commit on this branch.

## The table

| # | Requirement | State | The command that proves it |
|---|---|---|---|
| R1 | Build and test before the specification | built | the branch history: build (phase 3), suite (phase 4), then `docs/mini/SPEC.md` written from the code |
| R2 | The work lands in h-EPI | built | everything is under `src/creib/forge/mini/`, `forge/mini/`, `tests/mini/`, `docs/mini/`; nothing outside was changed except the new `tools/run_mini.py` |
| R3 | A prototype; DeepReason's authority does not bind it | built | no DeepReason code is imported anywhere; `grep -rn deepreason src/creib/forge/mini` prints nothing |
| R4 | Conjecture and criticism from one template | built | `python -m unittest mini.test_template.OneTemplateTests.test_both_shipped_seats_are_the_same_template` |
| R5 | Generic ports; input types added at compile | built | `python -m unittest mini.test_ports` (14 tests) |
| R6 | Other artifact types can be added | built | `python -m unittest mini.test_template.OneTemplateTests.test_a_kind_declared_only_in_a_manifest_is_compiled_scheduled_produced_and_logged` |
| R7 | Body and commitments are all an artifact needs | built | `python -m unittest mini.test_template.BodyAndCommitmentsTests` (14 tests) |
| R8 | Format compiled at run start, freeform by default | built | `python -m unittest mini.test_formats.FreeformTests mini.test_formats.MalformedSpecificationTests` |
| R9 | Any format in either field; only the two names required | built | `python -m unittest mini.test_formats.OtherChecksTests` |
| R10 | Keywords and syntax compiled; incorrect formats fail | built | `python -m unittest mini.test_formats.KeywordGrammarTests` |
| R11 | Failure rates customisable per kind, at submission | built, with assumption A5 | `python -m unittest mini.test_failures` (15 tests) |
| R12 | Evidence split and tagged as DeepReason does, without its wiring | built | `python -m unittest mini.test_evidence` (28 tests) |
| R13 | Append-only log, extensible for new kinds | built, with assumption A8 | `python -m unittest mini.test_log` (20 tests) |
| R14 | Cycles run in whatever order the user declares | built | `python -m unittest mini.test_wiring.DeclaredOrderTests` |
| R15 | Where evidence goes after batching is customisable | built | `python -m unittest mini.test_wiring.DeclaredRoutingTests.test_evidence_can_be_aimed_at_one_port_type mini.test_wiring.DeclaredRoutingTests.test_evidence_can_be_routed_to_scratch` |
| R16 | Where artifact contents go is customisable | built, with assumption A9 | `python -m unittest mini.test_wiring.DefaultRoutingTests mini.test_wiring.DeclaredRoutingTests` |
| R17 | A default permission layer, adaptable per run | built, with assumption A10 | `python -m unittest mini.test_policy` (14 tests) |
| R18 | Attention adapts to new artifact types | built | `python -m unittest mini.test_attention.DemonstrationPolicyTests.test_the_policy_sees_a_kind_it_was_never_written_for` |
| R19 | Signals are adaptable | built | `python -m unittest mini.test_attention.SignalRegistryTests.test_a_new_signal_is_a_registration_and_nothing_else` |
| R20 | Attention determined by the machine, not the user | built | `python -m unittest mini.test_architecture` (6 tests) |
| R21 | Attention off by default | built | `python -m unittest mini.test_attention.OffByDefaultTests` |

## Amendment 1

| # | Requirement | State | The command that proves it |
|---|---|---|---|
| R22 | One routing rule for artifacts and evidence alike | built, with assumption B1 | `python -m unittest mini.test_wiring.DeclaredRoutingTests mini.test_wiring.RoutingRefusalTests` |
| R23 | The stage list is one cycle, repeated until a typed host stop | built, with assumptions B3–B7 | `python -m unittest mini.test_cycles` (43 tests) |
| R24 | The compiled format rendered in full, on every attempt | built | `python -m unittest mini.test_formats.TheFormatIsShownTests` |
| R25 | A seat may be a model or a machine, and the record says which | built, with assumption B8 | `python -m unittest mini.test_machines` (9 tests) |
| R26 | The blind-spot run, rebuilt on R22–R25 | built, with assumptions B9 and B10 | `python -m unittest mini.test_blindspot.TheBlindSpotRunTests mini.test_blindspot.TheStandingRuleTests` |
| R27 | A compare command that ranks nothing | built, with assumptions B11–B13 | `python -m unittest mini.test_blindspot.CompareTests` |
| R28 | The order of work and the standing obligations | followed | the branch history: REQUEST, DESIGN, code and tests, SPEC rewritten from the code, then this table; `python tools/check.py all` green at each |

The blind-spot template can also be run and read by hand:

```sh
python tools/run_mini.py run --manifest forge/mini/manifests/blind-spot/manifest.json \
    --script forge/mini/scripts/blind-spot.json --output-dir /tmp/blind-spot
python tools/run_mini.py compare --root forge/mini/runs/blind-spot-stub --root /tmp/blind-spot
python tools/run_mini.py compare --root forge/mini/runs/blind-spot-stub --root /tmp/blind-spot --score   # refused
```

Every command above runs from the repository root with the environment of the
first section. `mini.<module>` works because `tests/mini/` is a package and
`tests` is on the path; equivalently
`python -m unittest discover -s tests -p test_formats.py`.

## The assumptions the table refers to

Four requirements are marked "built, with assumption". Each rests on one
reading of an open phrase, recorded in `DESIGN.md` §12 and overturnable by a
sentence:

- **A5 (R11)** — "failure rate" is read as three fields: `retries` (re-ask,
  error shown), then drop, with `tolerance` counting the drops the run permits
  and `action` saying what happens past it. All three actions the request names
  are reachable, and the default is "drop after one retry".
- **A8 (R13)** — "the same way it currently does" is read as typed events
  appended and never rewritten, replayed to rebuild state. The per-event hash
  chain is *added*; DeepReason's own log fences on sequence, not on a chain.
- **A9 (R16)** — a declared route replaces the default for the one kind or tier
  it names; everything else stays on the default pull.
- **A10 (R17)** — of "what its output may CHANGE", only `"nothing"` is
  implemented. Any other value is refused at compile rather than accepted and
  ignored.

The other eleven assumptions (A1–A4, A6, A7, A11–A15) sit under requirements the
table marks plainly "built", because the reading they take is the only one the
request's own words admit; they are listed in `DESIGN.md` §12 all the same.

### Amendment 1's assumptions

Thirteen, in `DESIGN.md` §14–§19, and the load-bearing ones are these:

- **B1 (R22)** — a kind or tier may carry more than one route, since "a push is
  additive on top of whatever the route allows" has content only if a route and
  a push can coexist. `nowhere` may not be combined with anything.
- **B3 (R23)** — the budget cap counts model-seat calls including retries, and
  stops before a cycle rather than inside one.
- **B4 (R23)** — the cycle coordinate changed the record's shape, so the event
  record is now v2 and the v1 schema is kept and still read.
- **B7 (R23)** — `max_repeats` per stage is what bounds attention, so the
  record's stage count stays bounded by the manifest.
- **B8 (R25)** — a machine seat is resolved by kind id and returns exactly what
  a model would have returned, so the same format checks both.
- **B9 (R26)** — what a kernel function, a transform, a proposal and the
  catalogue are. The amendment defines none of them; this is the largest single
  interpretation in the build.
- **B10 (R26)** — the standing rule. **Written wrongly first**, and the run
  found it: it marked a pair the catalogue correctly lists as not moving, and
  that did not move, as a defect. A defect is now the catalogue and the
  execution disagreeing, in either direction. `DESIGN.md` keeps both versions.
- **B11 (R27)** — the script was not in the record, so a run now records a
  `responder_id`; that is what makes "asked the same way" checkable at all.
- **B13 (R27)** — never promote, stated for `compare`.

## What is proposed and not built

`SPEC.md`, Part three, is the full list and the honest paragraph on attention.
In one line each:

| Thing | Why it is not here |
|---|---|
| An attention policy worth trusting | the plug is built and one demonstration policy ships; nothing measures whether re-ordering helps, and nothing can run one plan two ways to find out |
| A standing an artifact can gain or lose | `changes: "nothing"` is the only implemented value; the slot and its refusal exist so the shape is visible |
| A command that pairs two runs | the record supports it — same plan and script give byte-identical logs — but no command does it |
| Cutting evidence by anything but blank lines | tables, lists and headings are cut as prose |
| A structured optional field on a kind | `optional_fields` admit strings; structure goes in `commitments` under a JSON-schema format |
| Concurrency | one writer, one root, no lock; a second writer is detected on the next read, not prevented |

## Refusal sites

h-EPI's rule is that a new `raise` is a new refusal site and gets a test that
reaches it. There are 115 refusal sites in `src/creib/forge/mini/`; every one
has a negative test, and `tests/mini/test_refusals.py` exists for the sites the
requirement-shaped files do not already reach.

Whether the suite would in fact *notice* each one going quiet is a separate
question, and the repository's own instrument answers it:

```sh
git worktree add /tmp/mini-sweep HEAD
python tools/refusal_sweep.py --jobs 4 --report sweep.json \
    $(for f in src/creib/forge/mini/*.py; do echo --only $f; done)
```

The result of that run is in the "Sweep" section below.

## Live evidence

The offline delivery above stands on the scripted responder alone, and was
pushed before any model was called. The operator then supplied a key, so one
small live run was made through the default manifest, as the brief permits. It
is reported below as what the record shows and nothing more.

## Sweep

**Before Amendment 1**, over the 94 sites the first build had: **90 caught, 4
survived.** A survived site is one whose deletion the suite did not detect — the
guard may be unreached, or reached with its effect masked, or reached with an
effect no assertion looks at. All four were real gaps in my tests, not in the
code, and all four are named in the commit that fixed them:

- the unknown-refusal-code guard, which `assertRaises(RecordError)` passed
  either side of, because `MiniError` is a `RecordError`;
- the unwritable-blob path, which raised the wrong code — and the wrong name is
  why no test reached it;
- the unreadable-log path, caught one line later by the per-line reader instead;
- the root-must-be-a-path guard, whose deletion left the next line raising a
  `TypeError` of its own.

A confirming pass over those three files after the fixes: **24 of 24 caught, 0
survived.**

**After Amendment 1**, over all 115 sites: see the commit that follows this
table. The sweep takes about two hours and is not run before every commit; it is
run when guards change, which they did.

## Live run

One run, two calls, `gpt-oss:120b` through `https://ollama.com`, on the shipped
default manifest (conjecture, then criticism, then end) over one short supplied
source. The records are committed at
`forge/mini/runs/default-gpt-oss-120b/`.

```sh
export OLLAMA_API_KEY=…            # read at call time; in no file, no record, no log
python tools/run_mini.py live --manifest forge/mini/manifests/default/manifest.json \
    --model gpt-oss:120b --output-dir forge/mini/runs/default-gpt-oss-120b
python tools/run_mini.py replay --root forge/mini/runs/default-gpt-oss-120b
```

**What the record shows.** Seven events. The run entered `conjecture` and then
`criticism` in the declared order, produced one artifact at each, wrote no
format failure, no dropped submission and no refusal, and ended at the end stage.
Replaying the log alone reproduces the state digest the run reported. The source
cut into three blocks. No key appears anywhere under `forge/mini/runs/`
(`grep -ril "Bearer\|Authorization\|OLLAMA_API_KEY" forge/mini/runs/` prints
nothing).

**One finding, which is about the brief and not about the model.** Both
artifacts recorded **zero citations**, and both were in fact grounded. The model
put its block ids and its quotations inside the body prose — `[dcd587efbf…]
"A team measured a model's replies twice…"` — instead of in the `citations`
field the wire schema offered as optional. Extracting those prose claims by hand
and running them through the same `check_citations` used on the record verifies
all eleven of them: five in the conjecture, six in the criticism, every one
`MINI_CITATION_VERIFIED`.

So the citation channel recorded nothing while the artifacts were grounded. The
byte-check is not what failed; the brief is. What the record supports, and
nothing further: on this one run, with this model, this manifest and this
wording, the optional `citations` field went unused. It does not show that
models generally will not use it, and two calls could not show that.

**A second run, on a model the operator prefers to that one.** The same
manifest on `glm-5.3-flash`, three calls, at
`forge/mini/runs/default-glm-5.3-flash/`. Its conjecture stage returned an
unreadable reply twice, so the failure policy retried once, dropped the
submission and carried on to the criticism stage, which then ran with no
conjectures to criticise. Its criticism did use the `citations` field, and
filled it with three entries naming no block.

Those runs, and a third sent after the fix below, give four model-side or
brief-side findings and one defect in the harness, all registered with their run
roots in `docs/mini/FAILURE_MODES.md`.

The defect (H1) was mine: a reply refused for its format was not kept, only the
reason it was refused. It is fixed — every reply is stored before it is read —
and the fix paid for itself on the first run after it. The first refused reply
the record kept was not malformed at all: it was correct JSON inside a markdown
code fence (M4). With H1 open, that would have stayed on the record as
"unreadable" and nobody would have learned why.

**What these runs do not establish.** That the prototype works on anything
larger, that a repeat would return the same text, or that any artifact is any
good. Nothing here was compared with what the same model produces without the
harness, and neither run carries such an arm. Two models on one manifest behaved
oppositely on the same field; five calls cannot say which is typical.
