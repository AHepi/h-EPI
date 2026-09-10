# How to use the harness

*An operating guide for an agent or a person. `CLAUDE.md` holds the rules and is what `AGENTS.md` points at; this file holds the procedures. `docs/how-it-works.md` explains the method and the ten test families; this file assumes you have read it once and now want to do something. Every command below runs from the repository root with `PYTHONPATH=src`; none calls a model unless it says so.*

## Setup

```sh
python3.12 tools/check.py bootstrap     # once: .venv with the hash-locked dependencies
source .venv/bin/activate
export PYTHONPATH=src
python tools/check.py all               # lint, offline suite, every pilot validated and planned, every cited record id resolved; no model is called
```

For a hosted Ollama, export `OLLAMA_API_KEY` in the shell that runs `run`; it is read at call time and never written to a file, a record, a log, or an error message. For a local Ollama, set `"auth": "none"` and `"base_url": "http://localhost:11434"` in the pilot's endpoint and export nothing. In a Claude Code web session the SessionStart hook does the bootstrap and the exports.

The suite checks that every guard fails closed on the inputs the tests send; `python tools/refusal_sweep.py --jobs 4 --report sweep.json` checks, over about an hour, which `raise` statements the suite would not miss if they were deleted, and lists the rest. Run it when you add or change a guard. A listed site is one whose deletion the suite did not detect: unreached, or reached with the effect masked by a later guard or looked at by no assertion; which of these, and whether the check is dead code, is found by writing the test (H26 and H27 in `docs/failure-modes.md`).

Before any live run, know that it costs money and produces records that get committed. Use `--limit N` and a scratch `--output-dir` while developing, `--family BASELINE` for plain fills, and `--dry-run` to exercise the whole path with a canned executor and no network.

## The four files of a pilot

Everything problem-specific lives in one directory under `forge/conformance/pilots/<name>/`; nothing about your form goes in `src/`. Copy the template and edit:

```sh
cp -r forge/conformance/pilots/leave-request forge/conformance/pilots/my-form
```

| File | What to put in it |
|---|---|
| `form.schema.json` | JSON Schema 2020-12 with `additionalProperties: false` and a `required` list. Each field may use `type` plus `pattern`, `enum`, `maxLength`, `minLength`, `format`; any other keyword is rejected by name. Optional fields are those not in `required`. |
| `instructions.md` | A heading, one preamble line, a blank line, then numbered sentences `1.` … one per line. Sentence 1 should demand JSON only. Name each field by its backticked name in exactly one sentence, so that sentence can be cited, removed, or negated. |
| `corpus.json` | One case per document. `renderings` holds the same facts as `prose`, `table`, or `email`; `rendering` names the default. Every required field gets an oracle entry: `exact` (one value), `any_of` (several admitted readings; include `null` to expect abstention), `regex`, `enum`, `absent` (the field must not be emitted), or `unknown` (no answer key; the value is recorded and judged only against the schema). Mark a reading you are not sure of `interpretation_provisional`. |
| `pilot.json` | The models you may name, the endpoint, and the test surfaces: `negations`, `twins`, `ambiguity`, `load_bearing`, `controls`, `refusal_phrases`, `repeats`, `grounding`. The leave-request template has the minimum; the travel-claim pilot has everything switched on. |

Check the configuration before spending a call:

```sh
python tools/run_conformance_pilot.py validate     --pilot forge/conformance/pilots/my-form/pilot.json   # bindings and obligations
python tools/run_conformance_pilot.py plan         --pilot forge/conformance/pilots/my-form/pilot.json   # variants per family and the plan id
python tools/run_conformance_pilot.py oracle-check --pilot forge/conformance/pilots/my-form/pilot.json   # the model-free controls only
```

`validate` refuses anything it cannot bind: a negation, twin, control, or grounding list that names a field the form does not have, a load-bearing sentence id that does not exist, a `drop_required` control on an optional field, an oracle on an unknown field, a grounding mode whose lists are inconsistent. `plan` additionally refuses a control whose corruption leaves the reference output unchanged, so run both. `plan` prints the plan id; any edit to `pilot.json` moves it, so cite plan ids from run records, not from memory. `oracle-check` scores the corrupted reference outputs and must show every corruption rejected and the uncorrupted reference accepted; `CONTROL_ACCEPTED` there means your oracle cannot see that corruption and the battery would be vacuous on it.

## Use 1: fill your own form

A plain fill is one call per document, the form's own rules enforced, nothing pretended about correctness.

```sh
python tools/run_conformance_pilot.py run --pilot forge/conformance/pilots/my-form/pilot.json \
    --model gpt-oss:120b --family BASELINE \
    --output-dir forge/conformance/runs/my-form --created-on "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
python tools/run_conformance_pilot.py fills --observations-dir forge/conformance/runs/my-form
```

`fills` prints one JSON line per document with `filled_form`, `structural_issues`, the judged and unjudged fields, grounding verdicts and spans if configured, the fields left `null`, and `live_loci`. With no answer key the run is labelled `INCONCLUSIVE_NO_SCORED_OUTPUT`: the form was filled and its rules held, and nothing was confirmed. That is the honest label for a plain fill.

## Use 2: check an extraction step before it ships

Give the corpus an answer key and switch the surfaces on, then run the full battery.

1. **Answer key.** `exact` for values with one right answer; `any_of` where the document genuinely admits two readings, so that the key does not take a side it cannot defend (H13 in the register is what happens when it does); `unknown` where you have no key.
2. **Negations.** For a field with a formatting rule, give a replacement sentence, a replacement pattern, and a value transform (`iso_date_to_dmy`, `e164_au_to_national_spaced`). The model's output must change; `IDENTICAL_TO_BASELINE` means the instruction was ignored or the schema pattern dominated it.
3. **Twins.** Pairs of fields that carry the same kind of value in different roles (claimant and approver). The battery swaps their positions in the document and checks the values follow the labels.
4. **Ambiguities.** A field, a question, and rival instructions with labels. Each rival is appended to the instructions and the corpus says which value each rival should produce.
5. **Load-bearing sentences.** Sentence ids whose removal should change the output; `DEPENDENCE_UNCHANGED` records that it did not.
6. **Controls.** `swap_fields`, `drop_required`, `extra_key`, and `none` on cases with a reference output. They are mutation tests of your oracle and cost no calls.
7. **Repeats.** `"repeats": 2` sends every baseline request twice more and records `REPEAT_DIFFERS` when the form values differ. Any comparison family inherits this floor; measure it in the same run.
8. **Grounding.** `"mode": "spans"` with `span_fields`, `value_in_span_fields`, `abstain_fields`, and `span_relaxations` (`case_insensitive`, `date_range_completion`). A relaxation that accepted a span is named in the verdict.
9. **Cycles.** `"cycles": {"count": 3, "criticism": ["none", "external"]}` chains three further calls after each baseline, per source: the model sees its previous answer and is asked to check and correct it, alone or with the schema and grounding checks that answer failed. The key is never shown. Read the result with `cycles` beside the repeat floor (Use 10).
10. **Boundary and distractor cases.** Put the hard material in the documents: a correction mid-sentence, a transit city, a colleague copied in, a rate to multiply, a date fixed by a weekday, a document that is silent on a field the form has. T27 in `docs/small-models.md` says which probes discriminated across eighteen models and which sat at the floor.

Then, per model:

```sh
python tools/run_conformance_pilot.py run --pilot forge/conformance/pilots/my-form/pilot.json \
    --model gpt-oss:120b --retries 2 \
    --output-dir forge/conformance/runs/my-form --created-on "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
python tools/run_conformance_pilot.py report --run forge/conformance/runs/my-form/run.<id>.json \
    --observations-dir forge/conformance/runs/my-form --markdown my-form-report.md
python tools/run_conformance_pilot.py evidence --observations-dir forge/conformance/runs/my-form
```

`--retries` retries transport failures only; a completed empty reply stands as `EMPTY_RESPONSE`. `report` takes `--run` more than once and lists, per run, verdict counts by family, grounding verdicts, repeatability, and each failure mode with one example and its live loci; across runs it shows presence and absence only. `evidence` lists observation ids per model and trigger (or `GROUNDING:<verdict>`), which is what you cite.

## Use 3: compare models without ranking them

Run each model into the same output directory with its own `--created-on`, then pass every run record to `report`. The cross-model table says which failure modes each model exhibited and which it did not; it does not order them and no number in it can be summed into a score. Choose on which failures your task can tolerate. A model absent from a failure mode may not have been asked the question in a way that would expose it, and a model present in one may be there because of the key (check the live loci: TEST and SCOPE live on every model for the same case points at the key, not the models).

## Use 4: catch drift and regressions

The request digest is a function of the prompt, the schema, the options, and the model name, so the same pilot re-run later sends byte-identical requests. Run again with a new `--created-on`, then pair the two runs:

```sh
python tools/run_conformance_pilot.py compare --run forge/conformance/runs/my-form/run.<earlier>.json --run forge/conformance/runs/my-form/run.<later>.json \
    --observations-dir forge/conformance/runs/my-form --markdown my-form-drift.md
```

The output pairs every shared request, repeat by repeat, and gives identical, differing, and not-comparable counts, the fields that differed with counts, the verdict moves per field (`MISMATCH` to `MATCH` and back), and each run's own repeat floor. Read the differences against that floor: a model whose repeats differ half the time within one run will differ across runs for the same reason. A request that only one run made is counted and not paired; round trips are the usual case, since their document is the model's own earlier answer. Both runs must be of the same model. Do not compare across an edit to `pilot.json` without checking the plan id: an edited configuration is a new plan even when no variant changed, and the command prints both plan ids.

## Use 5: measure the noise floor

Set `repeats` to 2 or more. The run summary and the report state how many repeats were identical to the baseline and how many differed, per case. A model whose repeats never differ can be run with `0`; one whose repeats differ half the time cannot support any single-observation claim, and every comparison family's findings for it must be read against that count. `claims` places each refutation against that floor by machine: whether the refuting condition also held on every other repeat of the same run and case (`all`), on some (`some`), on none (`none`), or whether there was no repeat to compare with (`absent`), in `refuting_by_floor` and on each example. The class describes the records and withdraws nothing. When a case's position in the run should not be its position in the corpus, run with `--order shuffled --seed <n>`; the order and the seed are in the run record.

## Use 6: audit citations

Switch on grounding for the fields whose provenance matters. `GROUNDED` means the quoted words occur in the document (after whitespace normalisation, and after any relaxation you configured, which the verdict names); `SPAN_NOT_IN_DOCUMENT` means they do not; `VALUE_NOT_IN_SPAN` means the value is not inside the quoted words; `ABSTAINED` means the model returned `null` where you allowed it. None of these says the value is right, and a quotation of the wrong sentence that does occur in the document is `GROUNDED`; the table of what each check cannot see in `docs/how-it-works.md` lists the rest.

```sh
python tools/run_conformance_pilot.py evidence --observations-dir forge/conformance/runs/my-form --trigger GROUNDING:SPAN_NOT_IN_DOCUMENT
```

## Use 7: test a general claim about models

Write the claim as a conjecture in the pilot's `claims.json` **before** the run whose records will test it, and commit it with the pilot change; a conjecture written after the records is a description of them, and the document that reports it must say so. Each claim has a kind (`never` or `always`), a scope (families, cases, models, whether a model was called), and a condition over one observation: a trigger, a locus, a response verdict, a field verdict, a grounding verdict, the change-against-baseline flag, a null value, a present key, a field's value (`field_value`, arrays included), whether a field's value moved against the compared observation (`value_changed`), the thinking channel, a recovery, a token count, the kind of transport error (`transport_error`: timeout, disconnected, http_status with an optional status, other), a run's setting (`endpoint`), a cycle's index or criticism, a verdict move, a criticised field, a count inside one reply, the removed unit's relation (`unit`), or `all_of`, `any_of`, `not`, `baseline` and `previous` (the same condition on the observation this one is compared with). Anything outside that vocabulary fails closed.

```sh
python tools/run_conformance_pilot.py claims --claims forge/conformance/pilots/my-form/claims.json \
    --observations-dir forge/conformance/runs/my-form --markdown my-form-claims.md
```

Each claim comes out `REFUTED` (with the refuting models, the survivors, and example ids), `UNREFUTED_FOR_DECLARED_SCOPE`, or `NOT_TESTED`. For an unrefuted claim, read the liveness line: if the refuting condition held on no supplied record inside or outside the scope, the check has not been shown able to fail and the survival is a fact about what the models did, not a test the harness passed. Cite claim ids and observation ids in anything you write, with each refutation's floor class (Use 5). Never supply a run and its re-score together: `claims` refuses an observation supplied beside the reply it was replayed from (`replayed_from`), and refuses one observation supplied twice. When a re-score should stand in for one run of a directory that holds several, leave that run out with `--without-run <run id or prefix>`; the summary lists what was left out.

## Use 8: record what a refutation rests on

A refutation rests on a reading of the key or the matcher. When a reading is argued about, put it in the pilot's `appraisal.json`: a `reading` argument that supports a case and field (or a trigger) on a corpus or pilot digest, a `criticism` that attacks it, and a readiness a person decided (`PASS`, `FAIL`, or `UNKNOWN`) with its reason. Never infer readiness from records.

```sh
python tools/run_conformance_pilot.py claims --claims … --appraisal forge/conformance/pilots/my-form/appraisal.json --observations-dir …
```

Every argument is labelled `in`, `out`, or `undecided` by a fixed least-fixed-point rule, and each refutation is classed `usable`, `contested`, or `defeated` by the readings its conjecture's condition actually looks at. A claim with only defeated refutations becomes unrefuted; one with only contested ones becomes `REFUTED_ON_CONTESTED_READING`. An appraisal can only weaken a refutation, never create one, and a reading nobody has argued about is usable, which is absence of argument, not endorsement.

## Use 9: correct an answer key, or the machine, without touching a record

Records are never edited. Change the oracle in `corpus.json` (or fix the code), then re-score the recorded replies offline:

```sh
python tools/run_conformance_pilot.py run --pilot forge/conformance/pilots/my-form/pilot.json --model gpt-oss:120b \
    --replay-dir forge/conformance/runs/my-form --output-dir /tmp/my-form-rescore --created-on "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
```

The replay executor pairs each request with the reply that same request received in the recorded run, repeat by repeat, and makes no network call. The result is a new run with new observation ids, each naming in `replayed_from` the observation whose reply it re-scored; the original records stand. Decide deliberately where re-scored records go: a re-scored run committed beside its original counts that model twice in every table that works from run records, and `claims` refuses the pair.

## Use 10: ask whether a further cycle helps

Switch on `cycles` and `repeats` in the same pilot, run `--family BASELINE --family REPEAT --family CYCLE`, and table the result:

```sh
python tools/run_conformance_pilot.py cycles --observations-dir forge/conformance/runs/my-form --markdown cycles.md
```

One row per model, criticism source, and cycle index says how many cycles returned the same form as the step before, how many differed, and how the key's verdict per field moved between the two records; the `repeat` row of the same model is the floor, the same moves with nothing asked to change. A cycle count that does not clear that floor has shown nothing, and one that does has shown a difference on these cases, not an improvement in general: the harness never says a later answer is better, only which fields moved which way. Write what a move would refute as conjectures before the run (`cycle`, `previous`, `verdict_move`, `criticised_field` are the predicates; the travel-claim pilot's CYC-01 to CYC-14 are an example) and let `claims` say what survived. The criticism a cycle is shown is drawn from the form schema and the document only; if you want the model to see the key's verdicts you are measuring how well it copies a correction, and the harness will not build that plan.

## Use 11: treat the reasoning setting as a factor

For a model that takes a level, run the same plan at each level and compare:

```sh
for level in low medium high; do
  python tools/run_conformance_pilot.py run --pilot forge/conformance/pilots/my-form/pilot.json --model gpt-oss:120b \
      --family BASELINE --family REPEAT --think "$level" --timeout-seconds 600 --order interleaved \
      --output-dir forge/conformance/runs/my-form-reasoning --created-on "$(date -u +%Y-%m-%dT%H:%M:00Z)"
done
python tools/run_conformance_pilot.py compare --run <low run> --run <high run> --observations-dir forge/conformance/runs/my-form-reasoning
```

The plan is the same at every level; each run record's `endpoint` says what was sent, and `compare` pairs the requests by case and repeat (their digests differ, since the setting is inside the request, so use `--run` pairs from the same plan and read the pairing by case). A claim scopes on the setting with the `endpoint` predicate, read from the run record, so write the conjectures about levels before the runs as with any other. The travel-claim pilot's THK-01 to THK-08 are an example. Do not read a boolean `think` as an off switch: the models that take a level ignore it (L10), and the records show the channel whatever was sent.

## Use 12: find what a model's reading of a document depends on, with no key

For a document with headings, let the harness find the units and the terms itself. Write `pilot.json` with a `unit_dependence` block (heading levels, term patterns) and a two-field form with an array of terms, generate the probes, and run baselines, repeats, and removals together:

```sh
python tools/gen_unit_dependence_corpus.py --document my-document.md --pilot-dir forge/conformance/pilots/my-document --corpus-id MY-DOCUMENT-CORPUS-001
python tools/run_conformance_pilot.py run --pilot forge/conformance/pilots/my-document/pilot.json --model gpt-oss:120b \
    --family BASELINE --family REPEAT --family UNIT_DEPENDENCE --order interleaved \
    --output-dir forge/conformance/runs/my-document --created-on "$(date -u +%Y-%m-%dT%H:%M:00Z)"
python tools/run_conformance_pilot.py dependence --observations-dir forge/conformance/runs/my-document --markdown dependence.md
```

Every section carrying the document's own argument markup becomes a probe whose claim is its heading; every headed unit is removed once per probe with everything else present; the reply is compared with the same model's baseline reply and with nothing else. The table says, per relation (the document's own argument for the claim, a definition that argument uses, anything else), how many removals moved the form and which fields, beside the repeat floor, and sets the model's own named dependencies beside what removal moved. The unit table the generator prints is model-free and is the first thing to read. A run of this family is always labelled as having no scored output, which is what it is; the conjectures in `claims.json` (`unit`, `value_changed`, `field_value`) are where a move becomes a refutation, and they are written before the run as with any other. The pilot `semantics-unit-dependence` is an example, and `docs/document-dependence.md` reads its run.

A removal that moved nothing is read by the controls: generate them from the same document with `tools/gen_unit_controls_corpus.py --source-pilot <the unit-dependence pilot>`, run baselines and repeats, and table them with `controls --pilot <controls pilot> --observations-dir …`. The claim alone, the argument alone, the argument with its definitions, every other carrier of a term removed as a block, the vocabulary renamed, and the claim negated each sit beside the full-document reply; `semantics-unit-controls` is the example.

## Reading the output

- **Run labels.** `UNREFUTED_FOR_DECLARED_SCOPE` is the strongest: every judged field matched and nothing more. `REFUTED_CASES_PRESENT` means the model is a live suspect on at least one observation; it does not mean the model failed the battery. `INCONCLUSIVE_NO_SCORED_OUTPUT` means some field went unjudged or a call did not complete, which is the normal label for a plain fill with no key.
- **Live loci.** Every failure after a model call names a set from CANDIDATE (the model), AUXILIARY (prompt, executor, format plumbing), TEST (the oracle), SCOPE (the task as framed). A set is never a single locus; the routing is in `routing.py` and each report translates every trigger in prose.
- **Triggers.** Response-level: `TRANSPORT_ERROR`, `EMPTY_RESPONSE`, `TRUNCATED`, `INVALID_JSON`, `NOT_AN_OBJECT`, `REFUSAL_SUSPECTED`, `PREREQUISITE_UNAVAILABLE`. Field-level: `MISMATCH`, `MISSING_REQUIRED`, `EXTRA_FIELD`, `TYPE_VIOLATION`, `PATTERN_VIOLATION`, `ENUM_VIOLATION`, `LENGTH_VIOLATION`, `UNEXPECTED_PRESENT`, `SCHEMA_INVALID`. Family-level: `IDENTICAL_TO_BASELINE`, `REPEAT_DIFFERS`, `DEPENDENCE_CHANGED`, `DEPENDENCE_UNCHANGED` (a removed instruction sentence or, for UNIT_DEPENDENCE, a removed unit of the document), `CONTROL_ACCEPTED`, `CONTROL_REJECTED`, `FORMAT_NOT_ENFORCED`. Grounding: `SPAN_MISSING`, `SPAN_NOT_IN_DOCUMENT`, `VALUE_NOT_IN_SPAN`.
- **Timing and transport.** From record version 3 every attempt carries `started_at` and `elapsed_ms`, measured by the client around the call, and a failed attempt carries `transport_kind`: `timeout` (the client's timeout fired), `disconnected` (the remote end closed the connection), `http_status`, or `other`. A version 2 record has none of these and says nothing about how long a call took; the exception text it carries is what H34 was read from.
- **Exit codes.** `run` exits 1 when any observation carries live loci. That means look, not failed.
- **What a survival is a survival of.** `docs/kernel.md` lists, check by check, the smallest change each verdict moves under and a change it does not, every row held by `tests/test_kernel.py`. Read a clean run against it: a value that fits the pattern, a quotation of the wrong sentence that occurs, a reply wrong in exactly the way its baseline was wrong, and a refusal phrased outside the list all pass.
- **Interrupted runs.** A killed run leaves its observations and no run record. They are valid on their own but `report` will not see them; delete them or keep them as orphans, and rerun with a new `--created-on`.

## Writing it up

- A new failure mode gets an entry in `docs/failure-modes.md` with observation ids from `evidence`, never from memory. Absence of a mode on the cases run is recorded too.
- Lead with what happened, translate every label the first time it appears, and keep every live suspect visible. Do not rank, do not total across models, and do not write pass, accuracy, best, or worst.
- A general claim in a document cites the claim id and the records, and says whether the conjecture was written before or after them.

## Publishing

Work on a branch (`claude/*`, `codex/*`, or a human-chosen name); never commit on or push to `main`. Before every commit run `python tools/check.py all` (lint, the offline suite, every pilot planned, and `cite`, which resolves every record id the documents cite), stage explicit paths (never `.venv`, key material, or documents you are not licensed to share), run `git diff --cached --check`, and confirm no key is in the diff (`git grep -l Bearer -- forge/conformance/runs` must print nothing). Push with `git push -u origin HEAD`; never force, never `HEAD:main`, never rebase, reset, or amend published history. Publication is a pull request and merging is a human action. The `h-epi-safe-publish` skill walks through the same steps.

## Use 13: run a mini template

Mini asks a series of seats a series of questions in cycles and keeps everything it gets back; a seat is a model or a registered machine function, and a kind of artifact is a record, never a class. The shipped templates are `forge/mini/manifests/default/` (conjecture, criticism, verdict), `operator-example/`, `blind-spot/` (mini's own checks as kernels), and `conformance-blind-spot/` (the harness's own checks as kernels, with a catalogue drawn from `docs/kernel.md`).

```sh
python tools/run_mini.py compile --manifest forge/mini/manifests/conformance-blind-spot/manifest.json
python tools/run_mini.py run --manifest … --script forge/mini/scripts/conformance-blind-spot.json --output-dir /tmp/stub   # no model called
export OLLAMA_API_KEY=…   # read inside the harness's executor at call time; nowhere else
python tools/run_mini.py live --manifest … --model gemma4:31b --output-dir forge/mini/runs/<root> --timeout-seconds 300
python tools/run_mini.py replay --root forge/mini/runs/<root>
python tools/run_mini.py compare --root <one> --root <another>   # refuses --score
```

To run a campaign of rounds to its end without watching it:

```sh
python tools/mini_campaign.py run --plan forge/mini/manifests/experiments/campaign-1.plan.json \
    --output-dir /tmp/campaign --manifest-dir forge/mini/manifests/experiments \
    --rounds 3 --concurrency 5 --commit      # decides and commits each round before running it; never pushes
python tools/mini_campaign.py read --root forge/mini/runs/experiments/round-5/r5-3-skeletons-fields-gemma
```

A plan names each shape's starting manifest directory and its model. Every round writes a reading beside each record and a note saying which rule fired on which measurement. Read `docs/mini/AUTONOMY.md` before expecting more of it than it does: it finds and lays out disagreements, and it does not decide that one is a blind spot.

The experiments under `forge/mini/manifests/experiments/` are run the same way (`live --manifest forge/mini/manifests/experiments/round-3/r3-7-grid-skeletons/manifest.json --model gemma4:31b --output-dir …`), and their README is the pre-registration to extend before a new round and the reading to extend after. A manifest may declare `endpoint` in exactly the shape a pilot's endpoint has; absent, the shipped default applies. For a local Ollama set `"auth": "none"` and no key is needed. Read a run from its record: the first event carries the endpoint actually sent to, every artifact says which seat made it and how many calls it took, and the last verdict artifact of a blind-spot run is the deliverable a person turns into boundary points. `docs/mini/SPEC.md` is the reference and `docs/mini/FAILURE_MODES.md` the register.

## What not to expect

The harness will not tell you a model is good, that it understood a document, or that it can fill forms in general. It will tell you, with records, what a model did on your documents and where the blame can lie when it was wrong. That is the whole product, and `docs/reports/` explains why it stops there.
