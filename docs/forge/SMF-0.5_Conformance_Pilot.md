# SMF-0.5 task-conformance pilot

## Claim boundary

This pilot points the forge's criticism-first method at a second problem: a language model that must fill a form from a case document and does not do it properly. It produces criticism-bearing observations and routes each failure to the loci that could be at fault. It does not rank models, score them, declare any model fit for use, or confirm that any model understands forms. Survival of criticism leaves a model's output unrefuted for the declared scope; it does not confirm it.

The pilot changes nothing about CR-1.0, the bridge, the calibration record, or any pinned implementation file. Its schemas live in `forge/conformance/schema/`, not `forge/schema/`, precisely so the calibration record's implementation contract is untouched.

## How the method maps onto the problem

| Forge concept | In this pilot |
|---|---|
| Source authority | The form schema (`form.schema.json`) and the numbered instructions (`instructions.md`), content-bound by SHA-256 in every record |
| Candidate translation | The model's JSON output for one case document |
| Obligations | One per form field: type, required, constraint, and the verbatim instruction sentence that grounds it; an obligation with no sentence is flagged `unsourced` |
| Rival interpretations | Declared ambiguities with at least two rival rules (here: whether `NN/NN/YYYY` is day-first or month-first) |
| Project imports | The oracle's own reading of contestable fields, marked `interpretation_provisional` or `project_import_provisional`, never `source_scoped` unless the instruction settles it |
| Nine test families | See below |
| Failure routing | Every non-matching observation carries `live_loci`, a non-empty subset of CANDIDATE (the model), AUXILIARY (prompt, executor, format plumbing), TEST (the oracle), SCOPE (the task as framed). No family that involved a model call ever routes to a single locus |
| Human triage | The run stops at `AWAITING_HUMAN_TRIAGE`; nothing is promoted |

### The nine families, as executed

| Family | Transformation | What a failure criticises |
|---|---|---|
| DELETION | Remove a non-required field from schema and instructions | Output still contains it: the schema is being ignored (check vacuity) |
| NEGATION | Invert a formatting instruction and its pattern | Output unchanged from baseline: the instruction is being ignored |
| RIVAL_SUBSTITUTION | Append one rival disambiguation rule at a time | Output does not follow the supplied rule: silent disambiguation |
| SEMANTIC_ROLE_TWIN | Swap the positions of two field labels | Values follow position, not label |
| SUBSTRATE_SWAP | Same case as prose, table, and email | Output differs by rendering |
| BOUNDARY_SHIFT | Empty phone, unicode name, over-length summary, ambiguous date, injury with "low" | Per-case oracle, most of it `interpretation_provisional` |
| IMPORT_DEPENDENCY | Remove one load-bearing instruction sentence | Records whether the output depended on it; no pass or fail |
| NON_VACUITY | Corrupted reference outputs with no model call | The oracle accepts a wrong output: TEST is live |
| ROUND_TRIP | Fill, render the filled form back to prose, fill again | Second output differs from the first |

A `BASELINE` pseudo-family supplies the reference output that NEGATION, IMPORT_DEPENDENCY, and ROUND_TRIP compare against.

## Configurability

Everything problem-specific lives under `forge/conformance/pilots/<name>/`: `pilot.json` (models, endpoint, negations, twins, ambiguities, load-bearing sentence ids, controls, refusal phrases), `form.schema.json`, `instructions.md`, `corpus.json`. Nothing about the incident form is in `src/`. A second pilot is a new directory, not a code change. The executor is an `ollama-chat` adapter reading its key only from `OLLAMA_API_KEY`; a `ReplayExecutor` re-scores recorded observations without any network call, so an oracle correction never requires re-spending model calls.

```sh
PYTHONPATH=src python tools/run_conformance_pilot.py validate --pilot forge/conformance/pilots/incident-form/pilot.json
PYTHONPATH=src python tools/run_conformance_pilot.py plan     --pilot forge/conformance/pilots/incident-form/pilot.json
PYTHONPATH=src python tools/run_conformance_pilot.py oracle-check --pilot forge/conformance/pilots/incident-form/pilot.json
OLLAMA_API_KEY=… PYTHONPATH=src python tools/run_conformance_pilot.py run --pilot … --model gpt-oss:20b --output-dir forge/conformance/runs/incident-form --created-on 2026-09-05T22:00:00Z
PYTHONPATH=src python tools/run_conformance_pilot.py report --run forge/conformance/runs/incident-form/run.*.json --observations-dir forge/conformance/runs/incident-form --markdown report.md
```

`run` exits 1 when any observation carries live loci. That means unresolved criticisms are present, not that the run failed.

## First oracle defect, found by the first live run

The first live baseline run (gpt-oss:20b, six cases) returned 56 field matches and 4 mismatches, all on `site`. The model wrote `cold store 2`, `plant room, Level B2`, `kitchen, Building C`, and `loading bay, Site 4 Parramatta`, exactly as the documents do; the oracle expected title-cased forms (`Cold store 2`, …). Instruction 8 says "as named in the document", so the oracle, not the model, had departed from the source. The routing had already kept TEST live alongside CANDIDATE on every one of those observations.

Every `site` oracle was changed from `exact` to `any_of` over the verbatim form found in each rendering plus the capitalised reading, status `interpretation_provisional`, before the multi-model run. ORD-004 also showed that the three renderings of one case name the place three different ways (`Car park, Gate 2`, `the car park at Gate 2`, `car park Gate 2`), so a substrate swap would otherwise have blamed the model for the source's own variation. The corrected corpus has digest `f21d38e7…f8e38`; the plan derived from it is `e450b2c9…b087`. Re-running the same six baselines gave 60 of 60 matches and no live loci.

Two further oracle readings were left as they were and are reported as live criticisms rather than corrected between runs, because the instruction does not settle them:

- ORD-004 `severity`: the document says nobody was injured and the reporter "rates it medium because it could have been serious". Instruction 9 gives floors (injury → at least medium, hospital → high) and says nothing about a reporter's explicit rating. The oracle takes the reporter's rating; several models apply only the floors and answer `low`. Both readings are live; TEST and CANDIDATE stay open together.
- BND-001 `phone`: no number is stated, and the form's E.164 pattern admits no "not provided" value, so no schema-valid answer exists. The oracle records the empty string with that rationale. What models do here is reported under SCOPE as much as CANDIDATE.

## Runs

Nine Ollama-hosted models were run against the full plan (117 variants each: 109 model calls and 8 model-free controls) on 2026-09-05 through the `ollama-chat` executor with `temperature 0`, `seed 7`, `think false`, and the form schema sent as `format`. Kimi K3 was excluded by the operator on cost. Records are under `forge/conformance/runs/incident-form/` (one observation per variant, one run record per model), content-addressed and bound to corpus digest `f21d38e7…f8e38`. All 1,053 observation records and 9 run records reload under the current loader. The tables below are generated from those records by a script, not typed by hand.

### Per-model outcome (nine models, 117 variants each: 109 model calls, 8 model-free controls)

| Model | Scored JSON | Recovered from fences/prose | Unparseable | Transport errors | Thinking channel | Observations with live loci | Scope label |
|---|---|---|---|---|---|---|---|
| gpt-oss:20b | 106 | 8 | 0 | 2 | 106 of 108 | 46 of 117 | `REFUTED_CASES_PRESENT` |
| nemotron-3-nano:30b | 109 | 0 | 0 | 0 | 0 of 109 | 59 of 117 | `REFUTED_CASES_PRESENT` |
| gemma4:31b | 109 | 109 | 0 | 0 | 0 of 109 | 57 of 117 | `REFUTED_CASES_PRESENT` |
| gpt-oss:120b | 109 | 0 | 0 | 0 | 109 of 109 | 53 of 117 | `REFUTED_CASES_PRESENT` |
| qwen3.5:397b | 109 | 9 | 0 | 0 | 0 of 109 | 49 of 117 | `REFUTED_CASES_PRESENT` |
| glm-5.3-flash | 82 | 82 | 26 | 0 | 0 of 108 | 67 of 117 | `REFUTED_CASES_PRESENT` |
| glm-5.3 | 43 | 43 | 61 | 0 | 0 of 104 | 90 of 117 | `REFUTED_CASES_PRESENT` |
| deepseek-v4-flash:0731 | 109 | 58 | 0 | 0 | 0 of 109 | 52 of 117 | `REFUTED_CASES_PRESENT` |
| mistral-large-3:675b | 109 | 109 | 0 | 0 | 0 of 109 | 54 of 117 | `REFUTED_CASES_PRESENT` |

No model reached `UNREFUTED_FOR_DECLARED_SCOPE`; every completed run is `REFUTED_CASES_PRESENT`, which means at least one observation kept CANDIDATE live. It does not rank the models and the counts above are not scores.

### Field-level criticisms by model (mismatches against the proposed oracle, excluding model-free controls and IMPORT_DEPENDENCY)

| Model | `site` | `severity` | `phone` | `incident_date` | `incident_time` | `summary` | `reporter_name` | `subject_name` | `date_of_birth` | `injury_reported` |
|---|---|---|---|---|---|---|---|---|---|---|
| gpt-oss:20b | 6 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| nemotron-3-nano:30b | 15 | 1 | 1 | 1 | 4 | 2 | 0 | 0 | 0 | 0 |
| gemma4:31b | 13 | 7 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| gpt-oss:120b | 14 | 2 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| qwen3.5:397b | 11 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| glm-5.3-flash | 9 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| glm-5.3 | 3 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| deepseek-v4-flash:0731 | 14 | 0 | 1 | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| mistral-large-3:675b | 16 | 0 | 1 | 1 | 0 | 1 | 0 | 0 | 0 | 0 |

### Failure modes and which models exhibited them

| Failure mode | Present in | Absent in |
|---|---|---|
| Wraps the JSON in code fences or prose despite instruction 1 (recovered) | gpt-oss:20b, gemma4:31b, qwen3.5:397b, glm-5.3-flash, glm-5.3, deepseek-v4-flash:0731, mistral-large-3:675b | nemotron-3-nano:30b, gpt-oss:120b |
| Emits reasoning as message content with the JSON at the end (unparseable under recovery v1) | glm-5.3-flash, glm-5.3 | gpt-oss:20b, nemotron-3-nano:30b, gemma4:31b, gpt-oss:120b, qwen3.5:397b, deepseek-v4-flash:0731, mistral-large-3:675b |
| Drops or pads the `site` name (e.g. `Site 4 Parramatta` for `loading bay, Site 4 Parramatta`; `the yard`) | gpt-oss:20b, nemotron-3-nano:30b, gemma4:31b, gpt-oss:120b, qwen3.5:397b, glm-5.3-flash, glm-5.3, deepseek-v4-flash:0731, mistral-large-3:675b | - |
| Fabricates a phone number when none is stated (BND-001) | gpt-oss:20b, nemotron-3-nano:30b, gemma4:31b, qwen3.5:397b, deepseek-v4-flash:0731, mistral-large-3:675b | gpt-oss:120b, glm-5.3-flash, glm-5.3 |
| Returns an empty phone when none is stated (pattern violation, no fabrication) | gpt-oss:120b | gpt-oss:20b, nemotron-3-nano:30b, gemma4:31b, qwen3.5:397b, glm-5.3-flash, glm-5.3, deepseek-v4-flash:0731, mistral-large-3:675b |
| Ignores an explicit month-first rule on an ambiguous numeric date (RIVAL_SUBSTITUTION, BND-004) | nemotron-3-nano:30b, glm-5.3-flash, deepseek-v4-flash:0731, mistral-large-3:675b | gpt-oss:20b, gemma4:31b, gpt-oss:120b, qwen3.5:397b, glm-5.3 |
| Applies only the injury floor and overrides the reporter's explicit `medium` (ORD-004) | gemma4:31b, gpt-oss:120b, qwen3.5:397b, glm-5.3 | gpt-oss:20b, nemotron-3-nano:30b, glm-5.3-flash, deepseek-v4-flash:0731, mistral-large-3:675b |
| Misses the hospital rule (`medium` where hospital treatment means `high`) | - | gpt-oss:20b, nemotron-3-nano:30b, gemma4:31b, gpt-oss:120b, qwen3.5:397b, glm-5.3-flash, glm-5.3, deepseek-v4-flash:0731, mistral-large-3:675b |
| Exceeds the 200-character summary bound | nemotron-3-nano:30b, qwen3.5:397b, deepseek-v4-flash:0731, mistral-large-3:675b | gpt-oss:20b, gemma4:31b, gpt-oss:120b, glm-5.3-flash, glm-5.3 |
| Omits `incident_time` on some renderings only (substrate-dependent extraction) | nemotron-3-nano:30b | gpt-oss:20b, gemma4:31b, gpt-oss:120b, qwen3.5:397b, glm-5.3-flash, glm-5.3, deepseek-v4-flash:0731, mistral-large-3:675b |
| Output changed when a load-bearing instruction sentence was removed (dependence recorded) | gpt-oss:20b, nemotron-3-nano:30b, gemma4:31b, gpt-oss:120b, qwen3.5:397b, glm-5.3-flash, glm-5.3, deepseek-v4-flash:0731, mistral-large-3:675b | - |
| Output identical to baseline after a formatting instruction was inverted (instruction ignored) | - | gpt-oss:20b, nemotron-3-nano:30b, gemma4:31b, gpt-oss:120b, qwen3.5:397b, glm-5.3-flash, glm-5.3, deepseek-v4-flash:0731, mistral-large-3:675b |
| Round trip unstable (second fill differs from first) | - | gpt-oss:20b, nemotron-3-nano:30b, gemma4:31b, gpt-oss:120b, qwen3.5:397b, glm-5.3-flash, glm-5.3, deepseek-v4-flash:0731, mistral-large-3:675b |
| Emitted a key outside the schema while `format` was sent | - | gpt-oss:20b, nemotron-3-nano:30b, gemma4:31b, gpt-oss:120b, qwen3.5:397b, glm-5.3-flash, glm-5.3, deepseek-v4-flash:0731, mistral-large-3:675b |

### What the observations say, and what they do not

**Output framing is the most widespread criticism and it is not about the form.** Seven of nine models violated instruction 1 ("a single JSON object and no other text") in at least some calls: gemma4 and mistral-large wrapped every answer in a code fence, deepseek did so in about half, and both GLM models emitted their reasoning as message content with the JSON at the end, even with `think` set to false. The oracle recovered fenced JSON and labelled it as a project import; it did not recover GLM's trailing objects under the recovery rule in force during the runs, so those observations are recorded as unparseable. Re-scoring the same recorded responses offline under the widened rule (every balanced object in the text, most keys wins) turns all 87 of them into scored objects, most with 9 or 10 of 10 fields matching. The committed records keep the original scoring; the re-scoring is reported here, not substituted. Live loci for this mode are CANDIDATE and AUXILIARY together: the model disobeyed the instruction, and the harness's recovery rule was too narrow to see what it had produced.

**The `site` criticism is present for every model, which makes it a criticism of the instruction.** Instruction 8 says "the place where the incident occurred as named in the document". Every model, on the same cases, either dropped a qualifier (`Site 4 Parramatta` for `loading bay, Site 4 Parramatta`) or added one (`the yard`, `mezzanine store shelf`, `Gate 2 car park`). When a probe fails identically across nine models of different sizes and families, the plural routing is doing its job by keeping TEST and SCOPE live: the specification does not say what granularity "site" means. A human decides whether to sharpen instruction 8 or accept the variation; the harness records that it cannot decide.

**Fabrication under constraint is a real model-side mode.** Case BND-001 states no phone number, and the form's E.164 pattern admits no "not provided" value. Six models invented a number (`+61000000000`, and nemotron `+61123456789`). gpt-oss:120b returned an empty string, which violates the pattern but invents nothing; the two GLM models were unparseable on that case. SCOPE is live because the form gives no honest answer; CANDIDATE is live because inventing a phone number is a specific choice, and the two do not cancel.

**Instruction following splits by rule type.** No model ignored an inverted formatting instruction: on all 18 NEGATION variants every model's output changed from its baseline. But an explicit disambiguation rule appended for the ambiguous date `03/04/2025` ("read as MM/DD/YYYY") was ignored by four of nine models, which kept the day-first reading. The rival-substitution family exists to expose exactly this kind of silent disambiguation; CANDIDATE, AUXILIARY (rule placement and phrasing), and TEST are all live.

**The severity rule exposed a specification gap rather than a model error.** On ORD-004 the reporter says nobody was injured and rates the incident medium. Instruction 9 gives floors and says nothing about a reporter's own rating. Four models answered `low` (the floors alone), five answered `medium` (the reporter). Both readings are recorded as live; the oracle's own reading is marked provisional. No model missed the hospital rule on scored variants.

**Round trips were stable, and the format schema was never enforced.** Every model with a usable baseline reproduced its own output after it was rendered back into prose and filled again. No model emitted a key outside the schema in a scored variant, so `format_enforced_by_server` stayed null everywhere: the observations neither prove nor refute server-side enforcement. The earlier raw probe without the schema in the prompt text produced invented camelCase keys from two models, which is why the instructions render the schema in the prompt as well.

**Import dependence is recorded, not judged.** Removing one of the four load-bearing sentences changed the output in a minority of cases for every model. Removing the severity rule changed it most often; removing the phone normalisation rule changed it least, which is consistent with models normalising to E.164 from prior knowledge. The harness records the dependence as evidence about the instruction, with AUXILIARY and SCOPE live, and assigns no credit or blame.

**What was not observed.** No refusal was suspected. No truncation occurred. Two calls to gpt-oss:20b exceeded the 180-second client timeout and are recorded as transport errors, which is why that run's scope label cannot be `UNREFUTED_FOR_DECLARED_SCOPE` even where its fields matched. Smaller models were not systematically worse than larger ones on these criticisms; the tables show which modes each model exhibited, and nothing more.

### Cost and duration

The nine runs made about 1,000 model calls in total. Server-side median latency ranged from 0.6 s (deepseek-v4-flash) to 12 s (gpt-oss:20b). Wall time was dominated by endpoint queueing for gpt-oss:20b, not by the models. The offline review of the pilot's own code by six Ollama models across five lenses, and the two-model verification of 24 review findings, cost well under a hundred calls.

## Configurability limits found by review

Six Ollama models reviewed the module across five lenses (92 raw findings, 52 distinct sites). Where they agreed and the code confirmed it, the module was changed; the rest are recorded here as limits rather than hidden:

- The substrate vocabulary is fixed at `prose`, `table`, `email` in one place (`corpus.RENDERINGS` and the corpus schema). A pilot needing another rendering kind extends that vocabulary and the schema; it is a declared limit, not a hidden constant.
- NEGATION value transforms (`iso_date_to_dmy`, `e164_au_to_national_spaced`) are a small registry in `families.py`. A pilot whose formatting instructions need a different inversion adds a transform there; the corpus cannot define one.
- The ROUND_TRIP re-rendering uses a fixed header sentence and derives labels from field names. Both are generic, but a pilot wanting different prose supplies neither from configuration yet.
- A missing `OLLAMA_API_KEY` aborts the run before any call, deliberately; every other executor failure is a recorded `TRANSPORT_ERROR` observation.

## What this pilot does not establish

- It does not establish that any model fills forms correctly in general. The corpus is fourteen short English documents.
- It does not establish that the oracles are right. Every contestable oracle is marked provisional, and one was already wrong (see above).
- It does not establish that `format` structured output is unenforced everywhere; it records `format_enforced_by_server: false` only where an extra or missing key proves it for that call.
- It does not compare models. Cross-model tables show which failure modes each model exhibited; they are not a ranking.
