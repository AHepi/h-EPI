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

The full suite is **454 tests, 0 failed** — 250 that were there before, 204
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
reaches it. There are 94 refusal sites in `src/creib/forge/mini/`; every one has
a negative test, and `tests/mini/test_refusals.py` exists for the sites the
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

The offline delivery above stands on the scripted responder alone. Any live
evidence is reported in the "Live run" section below, as what the record shows
and nothing more.

## Sweep

*(pending: filled in from the sweep named above)*

## Live run

*(pending)*
