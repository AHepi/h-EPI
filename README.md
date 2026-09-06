# Conformance harness

A small, fail-closed harness for one question: **when a language model fills a form from a document, what exactly did it do, and where should the blame go when it is wrong?**

You give it three things: a form (a JSON Schema), the rules for filling it (numbered sentences), and one or more documents. It calls a model, records the returned form byte-for-byte in a content-addressed record, enforces the form's own constraints, compares each field to whatever expectation you declared, and routes every failure to a *plural* set of suspects: the model, the prompt and plumbing, the answer key, or the task as framed. It never declares a model correct. If you declare no expectation for a field, it records the value and judges nothing. Switched on in configuration, it also asks the model to quote the words each value came from and checks that they exist in the document, and lets the model answer `null` on fields you say may be unstated, so that "the document does not say" is recorded instead of an invented value.

[![ci](https://github.com/AHepi/h-EPI/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/AHepi/h-EPI/actions/workflows/ci.yml)

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

`fills` prints one JSON line per document: the returned form, any violations of the form's own rules, which fields were judged against an expectation and how, which were not judged, the grounding verdict and quoted span for each configured field, which fields the model left `null`, and the live suspects. `run` exits 1 when any observation carries live suspects, which means "look", not "failed".

## What is where

| Path | What it is |
|---|---|
| `forge/conformance/pilots/leave-request/` | The smallest working configuration: one form, two emails, no answer key, grounding spans and abstention switched on. Copy this. Run live against three models; its records are in `forge/conformance/runs/leave-request/`. |
| `forge/conformance/pilots/incident-form/` | The full test battery: nine fields, fourteen documents in three renderings, an answer key, declared ambiguities, negations, controls. Nine models were run against it; the findings are in the document below. |
| `forge/conformance/pilots/travel-claim/` | The hard battery: thirteen fields that need normalising, deriving, counting, and summing, with distractors, corrections, double negations, an abstention case, grounding spans on, and every test family exercised. Built to probe small models; the findings are in `docs/small-models.md`. |
| `forge/conformance/schema/` | The four record schemas: pilot config, corpus, observation, run. |
| `src/creib/forge/conformance/` | The machine: spec, corpus, the nine test families, prompt, executor, oracle, routing, records, runner, report. |
| `src/creib/{canonical,strict_json,errors}.py`, `src/creib/forge/schema_validation.py` | Shared foundations: canonical bytes and digests, strict JSON, typed errors, offline schema validation. |
| `tools/run_conformance_pilot.py` | The command line: `validate`, `plan`, `oracle-check`, `run`, `fills`, `evidence`, `report`. |
| `tools/check.py` | Every repository check: `lint`, `test`, `pilots`, `all`, `bootstrap`. |
| `docs/how-it-works.md` | The method, the nine test families, the grounding and abstention configuration, what nine models did on the incident form, and the limits. |
| `docs/failure-modes.md` | The register of failure modes, model limitations, and harness defects, each pointing at the observation records that show it. |
| `docs/small-models.md` | What the records show about the smaller models on the hard battery, with the larger sibling as contrast, and what they do not show. |
| `docs/history.md` | Where this came from and how to recover the earlier project. |

## Rules of the machine

- A run's strongest label is *unrefuted for the declared scope*; nothing is ever confirmed.
- A failed field criticises the whole tested conjunction. Live suspects are a set, never one after a model call.
- Every record is content-addressed and published without overwrite. Records never contain the API key.
- The model's reply is kept verbatim; if the answer key later changes, recorded replies can be re-scored offline without new model calls.

Read `CLAUDE.md` for the rules an agent working here must follow.
