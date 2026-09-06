# How the conformance harness works

## Claim boundary

This harness applies a criticism-first method to one problem: a language model that must fill a form from a document and does not do it properly. It produces criticism-bearing observations and routes each failure to the loci that could be at fault. It does not rank models, score them, declare any model fit for use, or confirm that any model understands forms. Survival of criticism leaves a model's output unrefuted for the declared scope; it does not confirm it.

The method was developed for a formal semantic-model project (see `docs/history.md`); this repository keeps only the part that fills and checks forms.

## How the method maps onto the problem

| Concept | In this harness |
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

Everything problem-specific lives under `forge/conformance/pilots/<name>/`: `pilot.json` (models, endpoint, negations, twins, ambiguities, load-bearing sentence ids, controls, refusal phrases, grounding), `form.schema.json`, `instructions.md`, `corpus.json`. Nothing about the incident form is in `src/`. A second pilot is a new directory, not a code change. The executor is an `ollama-chat` adapter reading its key only from `OLLAMA_API_KEY` (or, with `"auth": "none"` in the endpoint, no key at all, for a local Ollama); `run --replay-dir <observations>` re-scores recorded replies through the `ReplayExecutor` without any network call, matched by request digest, so an oracle correction never requires re-spending model calls.

```sh
PYTHONPATH=src python tools/run_conformance_pilot.py validate --pilot forge/conformance/pilots/incident-form/pilot.json
PYTHONPATH=src python tools/run_conformance_pilot.py plan     --pilot forge/conformance/pilots/incident-form/pilot.json
PYTHONPATH=src python tools/run_conformance_pilot.py oracle-check --pilot forge/conformance/pilots/incident-form/pilot.json
OLLAMA_API_KEY=… PYTHONPATH=src python tools/run_conformance_pilot.py run --pilot … --model gpt-oss:20b --output-dir forge/conformance/runs/incident-form --created-on 2026-09-05T22:00:00Z
PYTHONPATH=src python tools/run_conformance_pilot.py report --run forge/conformance/runs/incident-form/run.*.json --observations-dir forge/conformance/runs/incident-form --markdown report.md
PYTHONPATH=src python tools/run_conformance_pilot.py evidence --observations-dir forge/conformance/runs/leave-request --trigger SPAN_NOT_IN_DOCUMENT
PYTHONPATH=src python tools/run_conformance_pilot.py run --pilot … --model gpt-oss:20b --replay-dir forge/conformance/runs/incident-form --output-dir /tmp/rescore --created-on 2026-09-06T12:00:00Z
```

`evidence` lists, per model and per criticism trigger (or grounding verdict, written `GROUNDING:<verdict>`), the observation ids that carry it. It exists so that `docs/failure-modes.md` can point at records instead of paraphrasing them.

`run` exits 1 when any observation carries live loci. That means unresolved criticisms are present, not that the run failed.

## Using it for your own form

The incident form above is a test battery with an answer key. Most real use is simpler: you have a form and a document and you want the filled form back, with the form's own rules enforced and nothing pretended about correctness. That is a plain fill. The template under `forge/conformance/pilots/leave-request/` is the smallest working example. It was run live against three models with grounding spans and abstention switched on (see the next section); its 30 records (24 observations, 6 runs) are committed under `forge/conformance/runs/leave-request/`.

Starting inside the repository's virtual environment:

```sh
export PYTHONPATH=src
export OLLAMA_API_KEY=…                      # read only from the environment, never written anywhere

# 1. Copy the template and edit the four files.
cp -r forge/conformance/pilots/leave-request forge/conformance/pilots/my-form

# 2. Check the configuration before spending any model calls.
python tools/run_conformance_pilot.py validate --pilot forge/conformance/pilots/my-form/pilot.json
python tools/run_conformance_pilot.py plan     --pilot forge/conformance/pilots/my-form/pilot.json

# 3. Fill: one model call per case.
python tools/run_conformance_pilot.py run --pilot forge/conformance/pilots/my-form/pilot.json \
    --model gpt-oss:120b --family BASELINE \
    --output-dir forge/conformance/runs/my-form --created-on "$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# 4. Read the filled forms back.
python tools/run_conformance_pilot.py fills --observations-dir forge/conformance/runs/my-form
```

Where each thing goes:

| What | Where | Notes |
|---|---|---|
| The form | `form.schema.json` | JSON Schema 2020-12 with `additionalProperties: false` and a `required` list. Each field may use only `type` plus `pattern`, `enum`, `maxLength`, `minLength`, `format`. Other keywords are rejected by name. |
| The rules | `instructions.md` | A heading, one preamble line, a blank line, then numbered sentences `1.` … one per line, ending with a newline. Sentence 1 should demand JSON only. Mention each field by its backticked name in exactly one sentence so the obligation can cite it. |
| The document(s) | `corpus.json` | One case per document. `renderings` holds the text under `prose`, `table`, or `email`; `rendering` names the one used by default. Every required field needs an oracle entry; use `"kind": "unknown"` when you have no answer key. `varied` must be null unless `pair_of` names another case. |
| Provenance and abstention | `pilot.json` → `grounding` | `"mode": "none"` leaves the fill exactly as the form describes it. `"mode": "spans"` asks the model to quote, for each listed field, the words of the document it took the value from, and lets the listed `abstain_fields` be `null` when the document does not state them. See "Grounding and abstention" below. |
| The LLM endpoint | `pilot.json` → `endpoint` | `kind` is `ollama-chat`, `base_url` is the server (`https://ollama.com` for the cloud, `http://localhost:11434` for a local Ollama), `models` lists the model ids you may pass to `--model`. The key comes from `OLLAMA_API_KEY` only; add `"auth": "none"` for a local server that needs no key, and no Authorization header is sent. |
| The results | `--output-dir` | One `observation.*.json` per fill holding the request digest, the raw reply, the parsed form, per-field verdicts, and live loci; one `run.*.json` per model. Content-addressed; never overwritten. |

`fills` prints one JSON line per fill: `filled_form` is what the model returned, `structural_issues` lists violations of the form's own rules (wrong type, outside the enum, pattern, length, missing required key, extra key), `unjudged_fields` lists fields with no answer key, and `live_loci` is empty when nothing was flagged. A plain-fill run is labelled `INCONCLUSIVE_NO_SCORED_OUTPUT`: the form was filled and its rules held, and nothing about the values was confirmed. That label is deliberate. If you later add answer keys for some fields, those fields become judged and the labels change accordingly.

`run` exits 1 when any observation carries live loci and 0 otherwise is reserved; treat exit 1 as "look at the loci", not as failure. The full battery (drop `--family BASELINE`) needs pairs, renderings, negations, and controls to produce variants; with a single plain case it adds only an instruction-removal probe and a round trip.

## The hard battery

`forge/conformance/pilots/travel-claim/` is the third pilot, built to be difficult for a small model rather than representative. It keeps the machine unchanged and pushes every configuration surface at once:

- Thirteen fields, of which only two can be copied verbatim. The rest must be normalised (`E-41207` from "staff number 27 044"; `+61417220391` from "0417 220 391"), derived (a return date from "came home on the Wednesday" after a stated Sunday; "Mon 3 Nov to Thu 6 Nov 2025" with the year stated once), counted (nights between two dates), summed (itemised amounts including "three nights at $189.00" into whole cents), or mapped onto an enum from paraphrase ("giving evidence at a Senate committee hearing" is `other`).
- Distractors in every document: a transit city that is not the destination, a hotel's or a colleague's phone number one digit away from the claimant's, a manager who is copied in but did not approve, a pre-trip estimate that is not an amount claimed, a foreign-currency face value beside its converted charge.
- Statements that must be read, not matched: a correction that supersedes an earlier date in the same document, "receipts attached except the taxi receipt", and two booleans stated by double negation.
- Every family has material: two negations (date format, phone format), a role twin (claimant and approver), two declared ambiguities with rivals (day-first or month-first numeric dates; a stated total that disagrees with the itemised sum by $27.00), seven boundary cases, three load-bearing sentences, four controls on two reference cases, three renderings on four cases, one optional field for deletion, and a round trip per baseline.
- Grounding on for seven fields with abstention allowed on the return date and night count, and one case (BND-101) where the document is genuinely silent and null is the only answer the key admits.

Ninety variants per model, of which eighty-two call the model. Round one ran on plan `dde8e4f8…` (corpus digest `400ee484…`); what the four models did with it is in `docs/small-models.md`, and what it taught the machine is H11 to H15 in `docs/failure-modes.md`. Round one also exposed a defect in this battery's own answer key: "two nights at $205.00" was keyed as a nightly rate and read as a total by all four models (H13). The corrected corpus is a new plan; round-one records stand as scored.

A reply that is one JSON object with a repeated key is parsed with the last value winning and recorded as a provisional recovery that names the repeated keys, in the same way a fenced object is recovered from prose (H11); the reply is scored, and the malformation stays visible in the record.

## Grounding and abstention

A plain fill records what the model returned and enforces the form's rules. It cannot see two of the most common ways a fill goes wrong: a value that is well-formed but came from nowhere in the document, and a value the model invented because the form demanded one and the document did not supply it. The `grounding` block in `pilot.json` adds both checks as configuration. No code changes; the default mode `none` leaves every existing pilot byte-for-byte unchanged, and the incident form runs that way.

```json
"grounding": {
  "mode": "spans",
  "span_suffix": "_span",
  "span_fields": ["employee_name", "leave_type", "start_date", "end_date", "total_days", "reason"],
  "value_in_span_fields": ["employee_name"],
  "abstain_fields": ["end_date", "total_days"]
}
```

What the machine does with it:

- **Prompt.** For each field in `span_fields` a companion key `<field><span_suffix>` is added to the schema the model sees, placed directly after its field, required whenever the field is required. Each field in `abstain_fields` becomes nullable (`["type", "null"]`, and `null` is appended to its enum if it has one), and its companion is nullable too. Two numbered sentences are appended to the instructions, continuing the numbering: one lists the companion keys and says to quote verbatim and to output no companion key for any other field; the other names each abstain field's companion key, or says it has none, and says when to answer `null`. (The first wording said "its companion key, if it has one" and a 30B model inferred a key the schema does not define; H14 in the register.) The bound `form.schema.json` and `instructions.md` are not changed; the record stores both the bound text and the grounding block, so the prompt is reproducible from the record alone.
- **Scoring.** The reply is validated against the widened schema. Companion keys are never `EXTRA_FIELD`; they are stripped from `filled_form` in `fills` output. The change-against-baseline comparison (NEGATION, IMPORT_DEPENDENCY, ROUND_TRIP) covers the declared form fields only, so a differently worded quotation, or a spurious key outside the form, is not a changed fill; keys outside the form are still reported per observation as `EXTRA_FIELD`. Each span field gets a grounding verdict: `GROUNDED` (the quoted text occurs in the document, whitespace-normalised), `SPAN_MISSING` (a value was given with no quotation), `SPAN_NOT_IN_DOCUMENT` (the quotation does not occur in the document as sent), `VALUE_NOT_IN_SPAN` (for `value_in_span_fields` only: the value is not a case-insensitive substring of its own quotation), or `ABSTAINED` (`null` on a field allowed to abstain). Fields in `abstain_fields` are configured, not guessed: `null` on any other field is a `TYPE_VIOLATION`, as before.
- **Routing.** `SPAN_MISSING` keeps CANDIDATE and AUXILIARY live (the model did not quote, or the prompt did not make it quote). `SPAN_NOT_IN_DOCUMENT` and `VALUE_NOT_IN_SPAN` keep CANDIDATE, TEST, and SCOPE live: invented provenance, or a matcher that is too strict, or a rendering that changed the text. `ABSTAINED` and `GROUNDED` are not criticisms and route nowhere. Grounding never judges the value: a `GROUNDED` field with an `unknown` oracle is still `NOT_SCORED`, and a run of plain fills stays `INCONCLUSIVE_NO_SCORED_OUTPUT`.
- **Records.** Every observation stores `variant.grounding`, `scoring.grounding_verdicts` (field, verdict, span, detail), and the triggers; every run record stores `grounding_verdict_counts`. `fills` prints `grounding` and `abstained_fields` per fill; `evidence --trigger GROUNDING:ABSTAINED` lists the observations that abstained.
- **Round trips.** A ROUND_TRIP variant renders the baseline fill back to prose (`End date: not stated` for a null) and asks the model to fill again with the same grounding block. Fields the baseline abstained on get an `unknown` oracle rather than an exact one: the identity of a null is not asserted, and stability is carried by the change-against-baseline comparison, which does compare nulls. The first live run wrote records with an exact oracle holding `null`; none of them could be reloaded, and the regression test `test_round_trip_of_an_abstained_baseline_materialises_reloads_and_scores` now guards it.

Limits of the check, so that no one reads more into a verdict than it carries:

- A `GROUNDED` span shows that the quoted words exist in the document. It does not show that the value was correctly derived from them, or that they were the right words to use.
- The span match is verbatim after whitespace normalisation and is case-sensitive, so `sick` is not found in a document that says `Sick leave`. That is a deliberate reading of "verbatim"; it is also why TEST stays live on `SPAN_NOT_IN_DOCUMENT`.
- `value_in_span` is a substring test. It is meaningful for fields copied as written (a name) and meaningless for fields that are normalised (`2025-10-13` will never occur inside `Monday 13 October 2025`), which is why it is a separate list and the template applies it to one field only.
- Abstention is only checked where the configuration allows it. Whether a model abstains where it should is a question the corpus has to pose (LR-002 poses it); the harness cannot know which values a document leaves unstated.
- To make abstention the expected answer rather than a tolerated one, give the field an `any_of` oracle whose `values` include `null`. A null then scores `MATCH`, a value scores `MISMATCH` with CANDIDATE live (the model invented what the document does not say), and a null against any other oracle stays `MISMATCH`. The travel-claim battery's BND-101 uses this for the return date and the night count.
- Model-free controls (NON_VACUITY) are reference outputs in the bound form's own shape and are validated against the bound form schema, not the prompt schema with its companion span keys. The first plan of a grounded pilot with controls rejected its own uncorrupted reference until this was made explicit; `test_model_free_controls_are_scored_against_the_bound_form_not_the_prompt_schema` guards it.

The live runs of the template (three models, 2026-09-06: the full six-variant plan, then the two baselines repeated 30 minutes later to test repeatability; 24 model calls; records under `forge/conformance/runs/leave-request/`) are written up in `docs/failure-modes.md`, entries G1 to G5.

## First oracle defect, found by the first live run

The first live baseline run (gpt-oss:20b, six cases) returned 56 field matches and 4 mismatches, all on `site`. The model wrote `cold store 2`, `plant room, Level B2`, `kitchen, Building C`, and `loading bay, Site 4 Parramatta`, exactly as the documents do; the oracle expected title-cased forms (`Cold store 2`, …). Instruction 8 says "as named in the document", so the oracle, not the model, had departed from the source. The routing had already kept TEST live alongside CANDIDATE on every one of those observations.

Every `site` oracle was changed from `exact` to `any_of` over the verbatim form found in each rendering plus the capitalised reading, status `interpretation_provisional`, before the multi-model run. ORD-004 also showed that the three renderings of one case name the place three different ways (`Car park, Gate 2`, `the car park at Gate 2`, `car park Gate 2`), so a substrate swap would otherwise have blamed the model for the source's own variation. The corrected corpus has digest `f21d38e7…f8e38`; the plan derived from it at the time was `e450b2c9…b087`. Re-running the same six baselines gave 60 of 60 matches and no live loci. (The plan id of the same corpus is now `5683d72e…`, because every variant's body gained its `grounding` entry when that configuration was added; the archived records are bound to the plan id that wrote them.)

Two further oracle readings were left as they were and are reported as live criticisms rather than corrected between runs, because the instruction does not settle them:

- ORD-004 `severity`: the document says nobody was injured and the reporter "rates it medium because it could have been serious". Instruction 9 gives floors (injury → at least medium, hospital → high) and says nothing about a reporter's explicit rating. The oracle takes the reporter's rating; several models apply only the floors and answer `low`. Both readings are live; TEST and CANDIDATE stay open together.
- BND-001 `phone`: no number is stated, and the form's E.164 pattern admits no "not provided" value, so no schema-valid answer exists. The oracle records the empty string with that rationale. What models do here is reported under SCOPE as much as CANDIDATE.

## Runs

Nine Ollama-hosted models were run against the full plan (117 variants each: 109 model calls and 8 model-free controls) on 2026-09-05 through the `ollama-chat` executor with `temperature 0`, `seed 7`, `think false`, and the form schema sent as `format`. Kimi K3 was excluded by the operator on cost. The 1,053 observation records and 9 run records from those runs were removed from this tree with the rest of the earlier project; they are preserved, content-addressed and bound to corpus digest `f21d38e7…f8e38`, on the branch `archive/cr-eib-0.6-full` under `forge/conformance/runs/incident-form/`. They are `v1` records; the observation and run records became `v2` when the grounding keys were added, so the current loader refuses them by version and they are read with the code on that branch. The tables below were generated from those records by a script, not typed by hand; `docs/failure-modes.md` gives observation ids for each mode.

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
- Grounding spans are matched verbatim (whitespace-normalised, case-sensitive) against the document as sent. There is no fuzzy or offset-based matching, and no check that a span was taken from the right sentence; a quotation of the wrong sentence that does occur in the document is `GROUNDED`.

## What this pilot does not establish

- It does not establish that any model fills forms correctly in general. The corpus is fourteen short English documents.
- It does not establish that the oracles are right. Every contestable oracle is marked provisional, and one was already wrong (see above).
- It does not establish that `format` structured output is unenforced everywhere; it records `format_enforced_by_server: false` only where an extra or missing key proves it for that call.
- It does not compare models. Cross-model tables show which failure modes each model exhibited; they are not a ranking.
- It does not establish that a grounded value is right. `GROUNDED` says the cited words exist in the document; `ABSTAINED` says the model returned `null` where it was allowed to. Neither is a verdict on content.
