# Conformance harness

A small, fail-closed harness for one question: **when a language model fills a form from a document, what exactly did it do, and where should the blame go when it is wrong?**

You give it three things: a form (a JSON Schema), the rules for filling it (numbered sentences), and one or more documents. It calls a model, records the returned form byte-for-byte in a content-addressed record, enforces the form's own constraints, compares each field to whatever expectation you declared, and routes every failure to a *plural* set of suspects: the model, the prompt and plumbing, the answer key, or the task as framed. It never declares a model correct. Switched on in configuration, it also asks the model to quote the words each value came from and checks that they exist in the document, lets the model answer `null` on fields you say may be unstated, sends each request again to measure how often the same request returns a different form, and shows a model its own previous answer to record what a further cycle changes.

It has been run against eighteen hosted models on a battery built to be hard, producing 4,110 records for about ten dollars. What those records refute, and what they leave standing, is in `docs/`.

[![ci](https://github.com/AHepi/h-EPI/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/AHepi/h-EPI/actions/workflows/ci.yml)

## What it is for

Every use below produces named failure modes and the records that show them, never a score. The evidence for each is in the documents cited.

- **Checking an extraction step before it ships.** Invoices, claims, incident reports, intake forms: anything where a document becomes structured fields. Write the form, the rules, and a few hard documents, and the battery says where the model breaks. On the hard battery that was multiplied line items, dates fixed by a weekday, placeholder values in optional fields, and appended rules that some models ignore (`docs/small-models.md`).
- **Designing the form and the prompt.** The request is as much under test as the model. An abstention option was the difference between six of nine models inventing a phone number and eighteen of eighteen declining to invent a date; a reworded sentence stopped a spurious key (`docs/failure-modes.md`, F4, H14). Prompt changes can be tested with the same rigour as model changes.
- **Choosing among models without ranking them.** Cross-model tables show which failure modes each model exhibits, so a choice can be made on which failures the task can tolerate: a family that fabricates placeholders, a model that cannot multiply a nightly rate, a model whose repeats differ fourteen times in eighteen.
- **Catching drift and regressions.** The same requests can be re-sent after a model update or an endpoint change, and `compare` pairs the two runs request by request: identical forms, differing fields, verdict moves, each run's own noise floor. One model got five totals wrong on requests it had answered correctly eight hours earlier (`docs/small-models.md`, T24, T29).
- **Measuring an endpoint's noise floor.** Repeats under a fixed seed give a per-model count of differing replies. Sixteen of eighteen models differed at least once; every comparison of two calls needs that number.
- **Auditing citations.** With grounding on, the harness checks that a model's quoted sources exist in the document. Six of eighteen models cited words that were not there, and twelve completed a date range into a date the document never wrote.
- **Evaluating local small models before an on-premise deployment.** The hard battery was built for models around 12B, and a local Ollama runs with no key.
- **Finding defects in your own answer key.** When every model disagrees with the key the same way, the key is the suspect; that found a wrong reading in the first round (H13). Readings that have been argued about are recorded, and each refutation says whether it rests on one.
- **Audit evidence.** Content-addressed, replayable records show exactly what a model returned on which request. A changed answer key means re-scoring the recorded replies offline, never editing a record.
- **Testing whether a model can execute a stated formal rule, or respect stated distinctions.** Two pilots put the semantics behind the appraisal to five models of five sizes: the labelling policy's least fixed point, with every key computed by the harness's own code, and twelve episodes classified under the distinctions the semantics forbids collapsing. The two models that reason before answering computed the fixed point on 35 of 36 dossiers and the three that do not on 24 of 54, whatever their size; on the distinctions every model made at least one forbidden identification (`docs/semantics-battery.md`).
- **Research on model behaviour.** Universal conjectures are stated in a file and tested mechanically against every record. Forty-six were tested on the hard battery; thirty-one were refuted with counterexample ids, and the fifteen survivors say whether the check behind them was ever seen to fail (`docs/what-the-records-refute.md`).

## What it is not for

- Leaderboards, accuracy figures, or any ranking. It refuses to compute them by design.
- Claims about understanding, reasoning, or general capability. No record touches those; `docs/reports/` says why.
- Task shapes other than document to form. A different shape needs a new form profile in the code.

## Fill a form in four commands

```sh
python3.12 tools/check.py bootstrap          # once: .venv with the hash-locked dependencies
source .venv/bin/activate
export PYTHONPATH=src
export OLLAMA_API_KEY=…                      # read from the environment only; never written anywhere

cp -r forge/conformance/pilots/leave-request forge/conformance/pilots/my-form   # edit the four files
python tools/run_conformance_pilot.py validate --pilot forge/conformance/pilots/my-form/pilot.json
python tools/run_conformance_pilot.py run      --pilot forge/conformance/pilots/my-form/pilot.json \
    --model gpt-oss:120b --family BASELINE --output-dir forge/conformance/runs/my-form \
    --created-on "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
python tools/run_conformance_pilot.py fills    --observations-dir forge/conformance/runs/my-form
```

`fills` prints one JSON line per document: the returned form, any violations of the form's own rules, which fields were judged against an expectation and how, which were not judged, the grounding verdict and quoted span for each configured field, which fields the model left `null`, and the live suspects. `run` exits 1 when any observation carries live suspects, which means "look", not "failed". `agent.md` walks through every use above, command by command.

## What is where

| Path | What it is |
|---|---|
| `agent.md` | How to use the harness for each of the uses above: setup, the four files, the full battery, comparing models, repeats, citations, conjectures, cycles, re-scoring, reading the output, publishing. |
| `CLAUDE.md` (`AGENTS.md` is a symlink to it) | The rules an agent working here must follow. |
| `forge/conformance/pilots/leave-request/` | The smallest working configuration: one form, two emails, no answer key, grounding spans and abstention switched on. Copy this. Run live against three models; its records are in `forge/conformance/runs/leave-request/`. |
| `forge/conformance/pilots/incident-form/` | The full test battery: nine fields, fourteen documents in three renderings, an answer key, declared ambiguities, negations, controls. Nine models were run against it; the findings are in `docs/how-it-works.md`. |
| `forge/conformance/pilots/travel-claim/` | The hard battery: fourteen fields that need normalising, deriving, counting, and summing, with distractors, corrections, double negations, an abstention case, grounding spans on, repeats, and every test family exercised. Carries the sixty conjectures of `claims.json` (forty-six about filling, fourteen about cycles) and, in `appraisal.json`, the readings they rest on that have been argued about. Eighteen models were run against it; the findings are in `docs/small-models.md`, and the five-model cycles run is read in `docs/cycles.md`. |
| `forge/conformance/pilots/appraisal-labelling/`, `forge/conformance/pilots/explanatory-distinctions/`, `forge/conformance/pilots/signed-derivations/` | The semantics battery: dossiers labelled under the appraisal's own policy (keys generated by `tools/gen_appraisal_labelling_corpus.py` from `appraise`), episodes classified under the semantics' distinctions (`tools/gen_explanatory_distinctions_corpus.py`), and signed cases derived under its finite rules (`tools/gen_signed_derivations_corpus.py`, whose checker the suite tests), each with conjectures written before the run. Five models were run on each; the findings are in `docs/semantics-battery.md`, with its corrections after review. `signed-derivations-visible-key/` is the sibling pilot that re-scores the derivation replies against the key the visible dossiers support (H28). |
| `forge/conformance/runs/` | The committed records: leave-request, the travel-claim rounds one to three, the sweep, the cycles run and its rerun, the reasoning-level runs, the three semantics pilots, the derivations re-score, and the repaired derivations run. |
| `forge/conformance/schema/` | The six schemas: pilot config, corpus, observation, run, claims, appraisal. |
| `forge/mini/` | Mini, a second machine beside the harness: its manifests (`default`, `operator-example`, `blind-spot`, `conformance-blind-spot`), schemas, policies, scripts, and its records under `runs/`, each a hash-chained log with every reply stored verbatim. |
| `src/creib/forge/conformance/` | The machine: spec, corpus, the twelve test families, units, prompt, executor, oracle, routing, records, runner, report, compare, cycles, dependence, claims, appraisal. |
| `forge/conformance/pilots/semantics-unit-dependence/` | A document, not a form: five probes generated from the semantics document's argued sections, fifty-eight units removed one at a time, no key; the conjectures UDP-01 to UDP-07. |
| `tools/gen_unit_dependence_corpus.py` | Turns a markdown document into unit-dependence probes: one per section carrying the document's own argument markup, the claim its heading, with unknown oracles; prints the model-free unit table. |
| `forge/conformance/pilots/semantics-unit-controls/` | The controls for an unmoved removal, generated from the same document: the claim alone, the argument alone, the argument with its definitions, every other carrier of a term removed as a block, the vocabulary renamed, the claim negated; the conjectures UDC-01 to UDC-08. |
| `tools/gen_unit_controls_corpus.py` | Writes those controls as cases paired with their full-document case; no key. |
| `src/creib/{canonical,strict_json,errors}.py`, `src/creib/forge/schema_validation.py` | Shared foundations: canonical bytes and digests, strict JSON, typed errors, offline schema validation. |
| `tools/run_conformance_pilot.py` | The command line: `validate`, `plan`, `oracle-check`, `run` (live, `--dry-run`, or `--replay-dir` to re-score recorded replies), `fills`, `evidence`, `report`, `compare` (two runs of one model, request by request), `cycles` (what each further cycle changed, beside the repeat floor), `dependence` (what removing each unit of the document moved, by relation, beside the repeat floor), `controls` (each control for an unmoved removal beside the full-document reply), `claims` (with `--appraisal`, the run records loaded for the `endpoint` predicate, and `--without-run` to let a re-score stand in for one run of a directory); `run` takes `--think`, `--timeout-seconds`, `--order interleaved` and `--order shuffled --seed N` as run-time settings recorded in the run record. |
| `tools/check.py` | Every repository check: `lint`, `test`, `pilots`, `cite` (every record id the documents cite names exactly one record), `all`, `bootstrap`. |
| `tools/run_mini.py` | The mini command line: `compile`, `run` (scripted, no model), `live` (the manifest's endpoint through the harness's own executor), `replay`, `compare` (refuses `--score`). |
| `tools/refusal_sweep.py` | Mutation of the harness itself: each `raise` under `src/creib` is replaced by `pass` in turn and the offline suite is run against the mutant; the report names the refusal sites the suite never exercises. |
| `docs/how-it-works.md` | The method, the eleven test families, the configuration surfaces, the conjectures and the appraisal, what each check cannot see, what nine models did on the incident form, and the limits. |
| `docs/failure-modes.md` | The register of failure modes, model limitations, and harness defects, each pointing at the observation records that show it. |
| `docs/kernel.md` | What each check cannot see, as boundary points: the smallest change each verdict moves under beside a change it does not, every row held by a test and the document generated from the catalogue. |
| `docs/small-models.md` | What the records show about the smaller models on the hard battery, across three rounds and a sweep of eighteen models, and what they do not show. |
| `docs/what-the-records-refute.md` | Forty-six general claims about language models filling a form, each machine-tested against every record: refuted with counterexamples, or unrefuted for the records run, with the standing of each refutation and whether each survival was shown able to fail. |
| `docs/reasoning-levels.md` | The reasoning setting as a factor: gpt-oss:20b and gpt-oss:120b at low, medium and high on the same requests, with eight pre-registered conjectures; what the level moved, what it did not, and what a timeout refutes. |
| `docs/document-dependence.md` | What a model's reading of a document's own consequences depends on, found with no key and no manifest: every headed unit of a semantics document removed in turn, on five models, beside the repeat floor and beside what each model said it depended on. |
| `docs/cycles.md` | Whether a further cycle helps, put as fourteen pre-registered conjectures and a table of what each cycle changed beside the run's own repeat floor, on five models; what it shows and what it cannot. |
| `docs/semantics-battery.md` | What five models did on the labelling policy, the explanatory distinctions, and the signed derivations, with the pre-registered conjectures' outcomes, the contested readings, and what it does not show. |
| `docs/reports/` | Two reports: what is actually provable in the semantics the appraisal was drawn from, and what role a model can play in generation given the evidence. |
| `docs/reviews/` | Five literature reviews on checks whose verdicts have come loose from what they judge, kept as advisory external syntheses; their README lists what the harness took from them and what it did not. |
| `docs/mini/` | Mini's request, design, specification, delivery table, register, and audit response; `SPEC.md` is the reference, written from the code, and `FAILURE_MODES.md` the register of what its live runs showed, the harness's own checks under its blind-spot loop included. |
| `docs/history.md` | Where this came from and how to recover the earlier project. |

## Rules of the machine

- A run's strongest label is *unrefuted for the declared scope*; nothing is ever confirmed.
- A failed field criticises the whole tested conjunction. Live suspects are a set, never one after a model call.
- Every record is content-addressed and published without overwrite. Records never contain the API key.
- The model's reply is kept verbatim; if the answer key later changes, recorded replies are re-scored offline without new model calls, into new records.
- A conjecture about models is written down before the run that tests it, is refuted by one record, and is never confirmed.

Read `CLAUDE.md` for the rules an agent working here must follow and `agent.md` for how to use the harness.
