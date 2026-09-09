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
| Eleven test families | See below (the tenth, REPEAT, and the eleventh, CYCLE, are off unless a pilot asks for them) |
| Failure routing | Every non-matching observation carries `live_loci`, a non-empty subset of CANDIDATE (the model), AUXILIARY (prompt, executor, format plumbing), TEST (the oracle), SCOPE (the task as framed). No family that involved a model call ever routes to a single locus |
| Human triage | The run stops at `AWAITING_HUMAN_TRIAGE`; nothing is promoted |

### The families, as executed

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
| REPEAT | Send the baseline request again, `repeats` times, byte-identical | The form values differ between identical requests: the run's own noise floor, which every comparison family inherits. Off when `repeats` is 0 |
| CYCLE | Show the model its previous answer and ask it to check and correct it, `cycles.count` times in a chain, with nothing else (`none`) or with the schema and grounding checks that answer failed (`external`); the answer key is never shown | Scored against the case's own oracle like the baseline, and compared with the step before: whether the form changed, and how each field's verdict moved. Off unless `cycles` is configured |
| UNIT_DEPENDENCE | Split the case document into units at its own markdown headings and remove one at a time, everything else present; each variant records the unit, its heading, its relation to the claim the case preamble names (`self`, `declared`, `other`) and the terms it is taken to define, all computed from the document by pattern | Records whether the form moved against the same model's baseline reply; no key, no pass or fail. Off unless `unit_dependence` is configured |

A `BASELINE` pseudo-family supplies the reference output that NEGATION, IMPORT_DEPENDENCY, UNIT_DEPENDENCE, ROUND_TRIP, REPEAT, and the first CYCLE compare against.

## Configurability

Everything problem-specific lives under `forge/conformance/pilots/<name>/`: `pilot.json` (models, endpoint, negations, twins, ambiguities, load-bearing sentence ids, controls, refusal phrases, `repeats`, grounding, `cycles`, `unit_dependence`), `form.schema.json`, `instructions.md`, `corpus.json`. The form profile admits string, boolean, and integer fields, and arrays of strings, optionally from a closed list, unique, and bounded in count; an array field is recorded, compared between replies, and checked against its own schema, and admits only the `unknown` or `absent` oracle, never a listed value. Nothing about the incident form is in `src/`. A second pilot is a new directory, not a code change. The executor is an `ollama-chat` adapter reading its key only from `OLLAMA_API_KEY` (or, with `"auth": "none"` in the endpoint, no key at all, for a local Ollama); `run --replay-dir <observations>` re-scores recorded replies through the `ReplayExecutor` without any network call, matched by request digest, so an oracle correction never requires re-spending model calls.

```sh
PYTHONPATH=src python tools/run_conformance_pilot.py validate --pilot forge/conformance/pilots/incident-form/pilot.json
PYTHONPATH=src python tools/run_conformance_pilot.py plan     --pilot forge/conformance/pilots/incident-form/pilot.json
PYTHONPATH=src python tools/run_conformance_pilot.py oracle-check --pilot forge/conformance/pilots/incident-form/pilot.json
OLLAMA_API_KEY=… PYTHONPATH=src python tools/run_conformance_pilot.py run --pilot … --model gpt-oss:20b --output-dir forge/conformance/runs/incident-form --created-on 2026-09-05T22:00:00Z
PYTHONPATH=src python tools/run_conformance_pilot.py report --run forge/conformance/runs/incident-form/run.*.json --observations-dir forge/conformance/runs/incident-form --markdown report.md
PYTHONPATH=src python tools/run_conformance_pilot.py evidence --observations-dir forge/conformance/runs/leave-request --trigger SPAN_NOT_IN_DOCUMENT
PYTHONPATH=src python tools/run_conformance_pilot.py run --pilot … --model gpt-oss:20b --replay-dir forge/conformance/runs/incident-form --output-dir /tmp/rescore --created-on 2026-09-06T12:00:00Z
```

A declared ambiguity names one field, and each rival reading in the corpus gives that field's key under the rival rule. A rule that settles one reading can settle others with it: the day-first rule of the travel claim fixes the departure date and, through it, the return date and the night count; a rule on whether an UNKNOWN readiness counts as ready moves every label that depended on it. A rival reading therefore carries an optional `also` list of keys for the other fields the same rule fixes, and under that rule those keys are scored in place of the baseline's, so that a correct answer under the appended rule is not a mismatch of the key's own making. The travel claim absorbed this by admitting both readings in the baseline key; the appraisal-labelling pilot uses `also`.

`evidence` lists, per model and per criticism trigger (or grounding verdict, written `GROUNDING:<verdict>`), the observation ids that carry it. It exists so that `docs/failure-modes.md` can point at records instead of paraphrasing them.

`run` exits 1 when any observation carries live loci. That means unresolved criticisms are present, not that the run failed.

A run that is interrupted (a killed process, a lost container) leaves the observations it had already published and no run record. Those observations are complete and valid on their own, but `report` works from run records and will not see them, and a rerun with the same `--created-on` would try to publish identical records over them and stop at the first collision. Either keep them as orphans or delete them, and rerun with a new `--created-on`; the rerun is a new run with new observation ids, and if `pilot.json` has changed in the meantime it is also a new plan id, even when no variant changed.

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
| Repeats | `pilot.json` → `repeats` | `0` sends each request once. `N` sends every baseline request `N` more times as REPEAT variants and records whether the form values came back the same, so the run measures its own noise floor. Costs `N` calls per case; a model that reproduces its output under a fixed seed needs `0`. |
| Cycles | `pilot.json` → `cycles` | Absent, or `{"count": 0}`, leaves every plan unchanged. `{"count": N, "criticism": ["none", "external"]}` adds, per case and per criticism source, a chain of `N` CYCLE variants: each shows the model its previous answer and asks it to check and correct it, with nothing else (`none`) or with the schema and grounding checks the previous answer failed (`external`). The answer key is never part of a criticism. Costs `N` calls per case per source. See "Cycles, beside the repeat floor" below. |
| Provenance and abstention | `pilot.json` → `grounding` | `"mode": "none"` leaves the fill exactly as the form describes it. `"mode": "spans"` asks the model to quote, for each listed field, the words of the document it took the value from, and lets the listed `abstain_fields` be `null` when the document does not state them. See "Grounding and abstention" below. |
| The LLM endpoint | `pilot.json` → `endpoint` | `kind` is `ollama-chat`, `base_url` is the server (`https://ollama.com` for the cloud, `http://localhost:11434` for a local Ollama), `models` lists the model ids you may pass to `--model`. The key comes from `OLLAMA_API_KEY` only; add `"auth": "none"` for a local server that needs no key, and no Authorization header is sent. `think` is the reasoning setting sent with every request: `true`, `false`, `null` (send nothing), or a level `low`, `medium`, `high` for the models that take one; the gpt-oss models ignore a boolean and cannot switch their trace off (L10), so a comparison across levels is a comparison the endpoint documents and a boolean is not. |
| Run-time overrides | `run --think ... --timeout-seconds ... --order ...` | `--think` and `--timeout-seconds` replace the endpoint's setting for one run and nothing else: the plan and every variant id are unchanged, the request digest carries the setting (a request at `high` is a different request from one at `low`), and the run record's `endpoint` carries what was actually sent, which is what a claim's `endpoint` predicate reads. `--order interleaved` sends each case's baseline followed at once by that case's other variants, instead of every baseline first, so that the requests a comparison pairs are close in time; the records are the same either way, and the run record lists its observations in sending order. `--order shuffled --seed N` sends the cases in an order drawn from the seed, each case's variants still together, so that a case's position in the run is not its position in the corpus; the run record carries `order` and `shuffle_seed`, a seed without `shuffled` or `shuffled` without a seed is refused, and a run record written before version 3 carries neither and was sent in family order or, where its write-up says so, interleaved. |
| The results | `--output-dir` | One `observation.*.json` per fill holding the request digest, the raw reply, the parsed form, per-field verdicts, and live loci; one `run.*.json` per model. Content-addressed; never overwritten. A results directory is read by enumeration: anything in it that is not one of these, or a record file named for a different record than it holds, is refused by name, never passed over (H19). |

`fills` prints one JSON line per fill: `filled_form` is what the model returned, `structural_issues` lists violations of the form's own rules (wrong type, outside the enum, pattern, length, missing required key, extra key), `unjudged_fields` lists fields with no answer key, and `live_loci` is empty when nothing was flagged. A plain-fill run is labelled `INCONCLUSIVE_NO_SCORED_OUTPUT`: the form was filled and its rules held, and nothing about the values was confirmed. That label is deliberate. If you later add answer keys for some fields, those fields become judged and the labels change accordingly.

`run` exits 1 when any observation carries live loci and 0 otherwise is reserved; treat exit 1 as "look at the loci", not as failure. The full battery (drop `--family BASELINE`) needs pairs, renderings, negations, and controls to produce variants; with a single plain case it adds only an instruction-removal probe and a round trip.

## Conjectures, tested by the records

A pilot may carry a `claims.json` beside its configuration: a list of universal statements about what a language model does when it fills that form, each with a declared scope (families, cases, models, whether a model was called) and a condition over one observation. `claims` tests every statement against every record supplied and reports one of three things per claim: `REFUTED`, with the refuting models, the surviving models, and example observation ids; `UNREFUTED_FOR_DECLARED_SCOPE`, with how many observations from how many models were tested; or `NOT_TESTED`, when the scope matched no record.

```sh
PYTHONPATH=src python tools/run_conformance_pilot.py claims --claims forge/conformance/pilots/travel-claim/claims.json \
    --observations-dir forge/conformance/runs/travel-claim-sweep --observations-dir forge/conformance/runs/travel-claim-round3 \
    --markdown claims.md
```

A `never` claim ("a model never emits a key the schema does not define") is refuted by one observation where its condition holds; an `always` claim by one where it does not. The condition vocabulary is small and fixed: a trigger, a live locus, a response verdict, a field verdict (optionally on a named field, optionally only where the value is null), a grounding verdict (optionally only where a relaxation was used), the change-against-baseline flag, a null value, a present key, the thinking channel, the kind of recovery, `all_of`, `any_of`, `not`, and `baseline`, which evaluates a nested condition on the baseline observation of the same run and case, so that "a swapped rendering mismatched where the baseline did not" can be said. Anything outside the vocabulary fails closed.

Survival is not confirmation. A claim unrefuted across eighteen models and three thousand observations is unrefuted for exactly those records, and the next record may refute it; every result carries the non-inductive limit, and no output of the command counts survivals as evidence. A survival is also only as good as the check behind it. For every claim the command counts how many supplied observations outside the declared scope satisfied the refuting predicate, and an unrefuted claim whose predicate held nowhere, in or out of scope, is reported as not shown able to fail: its condition names a trigger or verdict that no supplied record ever carried, so the records could not have refuted it whatever the models did. A claim about refusals tested on records with no refusal in them survives vacuously, and the output says so rather than listing it beside a survival that was tested. The summary line names these claims. What the command adds is that a general statement about language models made in a document can be checked, by anyone, against the records the document cites, and that a refutation names its counterexamples. `docs/what-the-records-refute.md` is the travel-claim conjectures read this way.

Each refutation is also placed against the repeat floor of its own run and case: the REPEAT observations of that case other than the refuting observation itself. The class says whether the refuting condition also held on every one of them (`all`), on some (`some`), on none (`none`), or whether no repeat was supplied (`absent`); the counts are in `refuting_by_floor`, each example carries its class, and the Markdown states them in words. For a condition that compares a reply with the baseline, `all` says the repeats moved too and the refutation is not distinguished from the floor; for a condition about a reply's own content, `all` says the condition recurred on every identical request. The class describes two records beside each other and withdraws nothing: a `never` claim is refuted by one observation whatever its class, and a document that cites the refutation says which class it is in. The baseline is the reply the repeats are compared with and is not a member of the floor.

A reply and its replay are one reply. From record version 3 an observation written by the replay executor names the observation it re-scored in `replayed_from`, and `claims` refuses a set of observations that holds both, or that holds one observation twice, naming the pair; supply the original run or its re-score, not both. A re-scored run in its own directory (`docs/failure-modes.md`, H22, H28) is now refused by the machine rather than avoided by hand when it is supplied beside its source.

## Readings under criticism

A refutation rests on readings. When `claims` reports DERIV-04 refuted by an observation, it relies on the answer key's reading of `nights_away` on that case; when it reports PROV-01 refuted, it relies on the span matcher's reading of what counts as a quotation under the configuration then in force. Those readings can be wrong, and the register records cases where they were (H13: a nightly rate that the key read one way and four models read the other). Until the appraisal existed, a refutation counted the same whether or not the reading under it was in dispute.

A pilot may carry an `appraisal.json` beside its claims: a finite list of arguments. An argument is a `reading` (what the key or a matcher took a case and field, or a trigger, to mean, with the corpus or pilot digest prefix it applies to), a `criticism` of other arguments, or `other`. Each names the arguments it attacks and the arguments essential to it, and carries a readiness: `PASS` when a person has checked that it is stated consistently and is ready to stand, `FAIL` when it has been withdrawn, `UNKNOWN` when nobody has decided, with the reason written beside it. Readiness is a decision a person recorded in the file, never inferred from records, and it says nothing about the model: the readiness of "the key reads this phrase as a nightly rate" is whether the key does say that, not whether it is right.

`claims --appraisal` labels every argument `in`, `out`, or `undecided` by one fixed rule. An argument is in when it is ready, every argument essential to it is in, and every argument that attacks it is out. It is out when it is not ready, or an essential argument is out, or an attacker is in. Anything else is undecided. The labels are the least fixed point of those two rules starting from empty sets; on a finite graph it is reached in at most twice as many rounds as there are arguments, and the code raises if it is not, or if any argument would be both in and out. So a mutual attack with nothing outside it stays undecided, a support cycle does not bootstrap itself into in, and a criticism of a criticism restores the reading it defended; `test_labelling_policy` fixes each of these. The rule decides nothing semantic. It propagates the readiness a person recorded through the attacks and supports they recorded, and it can be replayed by anyone from the file.

Each refuting observation is then given a standing: `defeated` if any reading it rests on is out, `contested` if any is undecided, `usable` otherwise. A reading is one the observation rests on only if it supports the case and field, or the trigger, that the conjecture's condition looks at, on the corpus or pilot digest that scored the observation. A contested reading of the purpose field does not contest a refutation about an extra key in the same reply, and a conjecture that looks at no field in particular (a response verdict, a token count) rests on every argued reading the observation carries. A claim with any usable refutation is `REFUTED`; one whose refutations are all contested or defeated, with at least one contested, is `REFUTED_ON_CONTESTED_READING`; one whose refutations are all defeated is `UNREFUTED_FOR_DECLARED_SCOPE` with the defeated count shown. The output names, per claim, how many refutations were usable, contested, and defeated, and which readings were involved.

```sh
PYTHONPATH=src python tools/run_conformance_pilot.py claims --claims forge/conformance/pilots/travel-claim/claims.json \
    --appraisal forge/conformance/pilots/travel-claim/appraisal.json \
    --observations-dir forge/conformance/runs/travel-claim --observations-dir forge/conformance/runs/travel-claim-round2 \
    --observations-dir forge/conformance/runs/travel-claim-round3 --observations-dir forge/conformance/runs/travel-claim-sweep
```

The travel-claim appraisal has eleven arguments. Two round-one readings of "N nights at $X" as a nightly rate are attacked by the criticism recorded as H13, which a person marked ready because the phrasing was corrected in the corpus; both readings are out. Three readings are attacked by criticisms nobody has settled (the purpose of "requirements workshops", whether a mixed day-first and month-first reading of a date pair is an error or a reading the key should admit, and whether every refused span in rounds one and two was a completed range), and are undecided. Over the records at the time of writing that leaves three conjectures resting partly on argued readings: DERIV-04 (21 usable refutations, 4 contested), READ-07 (13 and 7), and PROV-01 (7 and 17, the seventeen being the pre-relaxation span verdicts). None changes status, because each keeps a usable refutation. The two readings labelled out support no refutation in the current claims file, because every arithmetic conjecture had been scoped away from BND-104 and TRV-004 when H13 was found; the appraisal turns that exclusion from a choice buried in a scope list into an argument anyone can read and attack.

A reading nobody has argued about is treated as usable. That is absence of argument, not endorsement, and it is exactly the position every refutation was in before: the appraisal only ever weakens a refutation, never strengthens one, and a claims file run without `--appraisal` gives the same counts as before.

## Comparing two runs

The request digest is a function of the prompt, the schema, the options, and the model name, so two runs of one model on one plan send byte-identical requests, and a repeat is the same request sent again. `compare` pairs each request of one run with the same request of another, repeat by repeat, and reports how many pairs returned identical form values, which fields differed and how often, and how the oracle's verdicts moved between the two sides.

```sh
PYTHONPATH=src python tools/run_conformance_pilot.py compare \
    --run forge/conformance/runs/travel-claim-round3/run.dd5bc9ae4cf55b46.json \
    --run forge/conformance/runs/travel-claim-sweep/run.ede862c99337c1f4.json \
    --observations-dir forge/conformance/runs/travel-claim-round3 --observations-dir forge/conformance/runs/travel-claim-sweep \
    --markdown gemma-drift.md
```

Identity compares the declared form fields of the two replies and never consults the oracle, so a difference is drift and not a wrong answer; the verdict moves say separately how each side was read, so drift in a total can be told from drift in a field nobody scored. Each run's own repeat floor is printed beside the comparison, because a difference across runs means nothing until it is read against the difference within one. Requests only one run made are counted and not paired; a round trip is such a request whenever the baseline it was built from differed, since its document is the model's own earlier answer. The two runs must be of the same model, because the model name is inside every digest, and the command refuses anything else. Nothing in the output ranks or prefers either run.

## Cycles, beside the repeat floor

Whether a further cycle helps is a question the harness can put but not answer in the affirmative. The CYCLE family asks it in the only form it can test: each cycle shows the model its previous answer, appended after the document with a fixed revision sentence, and asks for the complete form again. With criticism `none` nothing else is shown, which is self-revision, the model as its own critic. With criticism `external` the failed checks of the previous answer are listed by field and verdict, drawn only from the vocabulary that the form schema and the document produce on their own: a missing required key, an extra key, a type, pattern, enum, or length violation, a span that is missing, absent from the document, or not containing its value. `MISMATCH` and `UNEXPECTED_PRESENT` come from the answer key and are excluded in code, in the record schema, and by a test; a cycle that fed the key back would measure copying, not revision. A cycle whose previous step returned no usable object is `PREREQUISITE_UNAVAILABLE`, and the chain stays unavailable from there.

Each cycle is scored against the case's own oracle, exactly as the baseline is, and its `changed_vs_baseline` and `baseline_observation_id` refer to the step it follows, so a chain is readable record by record. The materialised variant carries the previous answer as canonical JSON text and the criticisms shown, and the request digest covers both, so a cycle replays through `--replay-dir` as far as the recorded replies answer the requests the re-score makes: a re-score that reads a step's output differently from the recorded run changes the next step's request, which was never sent, and that step and those after it are `PREREQUISITE_UNAVAILABLE` with the reason in the record; a request identical to one the recorded run made at another step is answered by that step's reply, which `replayed_from` names (H40, H31).

```sh
PYTHONPATH=src python tools/run_conformance_pilot.py cycles --observations-dir forge/conformance/runs/travel-claim-cycles --markdown cycles.md
```

The `cycles` command tables, per run, criticism source, and cycle index, how many cycles returned the form of the step before and how many differed, and how the oracle's verdict per field moved between the two records: a match that became a miss, a miss that became a match, anything else. The same counts for the run's REPEAT variants sit in the same table as the floor, because a repeat is a cycle that was shown nothing and asked nothing, and a move a repeat makes on its own is not a move the cycle made. The criticised-field columns say how many fields an external cycle was told about, how many of those it changed, and how many still fail the same check afterwards. Nothing in the table is a score: a miss that became a match is two records and the key's reading of each, and the conjectures in a pilot's `claims.json` (`cycle`, `previous`, `verdict_move`, `criticised_field`) are the place to say what such a move would refute.

## Unit removal, with no key and no manifest

The families above vary the instructions one declared sentence at a time and score the reply against a key. The UNIT_DEPENDENCE family varies the document instead, declares nothing, and scores nothing. A pilot names the markdown heading levels at which the case document is split, and patterns for the terms the document uses (a commitment name, a symbol in a display, an abbreviation). The planner splits the document at its own headings into units, and for each unit and each case plans one variant with that unit's lines deleted and every other line as it was. A unit is related to the claim the case's preamble names as `self` when its heading occurs in the preamble, which is the document's own argument for the claim; as `declared` when it is taken to define a term that argument or the preamble uses, where a unit defines a term by first occurrence, by its heading, or by a display that introduces the term with `\iff`; and as `other` otherwise. The relation and the terms are recorded on the variant, so a table can be checked against the document by hand, and the heuristic is what it says: a pattern over the document's conventions, not a reading of it.

Nothing about the reply is judged. Both form fields carry the `unknown` oracle; the reply is compared with the same model's baseline reply on the full document, and the observation records `DEPENDENCE_CHANGED` or `DEPENDENCE_UNCHANGED`, routed to AUXILIARY (the document as sent), TEST (a probe with no key and a floor), and SCOPE (which units, which claim, which relation), never to the model alone. A run of this family is never unrefuted, since nothing is scored, and a parsed reply never makes the model a live suspect. The `dependence` command tables, per run and relation, how many removals left the form as the baseline had it and how many moved it, field by field, beside the run's own REPEAT floor, and sets the model's own list of what the claim depends on (the form's array field) beside what removal moved: a unit the model named whose removal moved nothing, and a unit it did not name whose removal moved the answer, are both visible. In that table an array field compares as a set, and a reply whose list held the same items in another order is counted apart as reordered only; the record's own `changed_vs_baseline` flag and the `value_changed` claim predicate compare exactly, so a conjecture that must ignore order says so by naming a scalar field. The claim predicates `unit`, `field_value`, and `value_changed` let a conjecture say what such a move would refute.

```sh
python tools/gen_unit_dependence_corpus.py --document my-document.md --pilot-dir forge/conformance/pilots/my-document --corpus-id MY-DOCUMENT-CORPUS-001
PYTHONPATH=src python tools/run_conformance_pilot.py run --pilot forge/conformance/pilots/my-document/pilot.json --model gpt-oss:120b --family BASELINE --family REPEAT --family UNIT_DEPENDENCE --order interleaved --output-dir forge/conformance/runs/my-document --created-on …
PYTHONPATH=src python tools/run_conformance_pilot.py dependence --observations-dir forge/conformance/runs/my-document --markdown dependence.md
```

A removal that moves nothing has three readings, and a second generator writes the controls that separate them, all computed from the document: the claim with no document (answered from the claim alone), with its own section only (answered from the argument), with that section and the units defining the terms it uses, with every other unit carrying a term the argument uses removed at once (the block the redundancy reading needs), with the whole vocabulary consistently renamed so that a reply naming the old names names what is not on the page, and with the claim negated. Each control is a case paired with its full-document case (`pair_of`, with `varied` naming the control as `control=<kind>`), so the corpus needs no new family: baselines and repeats do the work. The `controls` command tables, per run and kind, how many controls left each field as the full-document reply had it, beside each control's own repeat floor, which vocabulary each reply to the renamed document named, and whether the verdict followed the negation.

```sh
python tools/gen_unit_controls_corpus.py --document my-document.md --source-pilot forge/conformance/pilots/my-document --pilot-dir forge/conformance/pilots/my-document-controls --corpus-id MY-DOCUMENT-CONTROLS-001
PYTHONPATH=src python tools/run_conformance_pilot.py controls --pilot forge/conformance/pilots/my-document-controls/pilot.json --observations-dir forge/conformance/runs/my-document-controls --markdown controls.md
```

The generator turns a markdown document into probes with no key: every section whose body carries the document's own argument markup (a bold `Claim.`, `Counterexample.`, `Derivation.`, `Construction.` or `Consequence.` label) is one case, the claim under assessment is the section's heading restated in a short preamble, and the whole document follows. It prints the model-free unit table, which is the first result: every unit, the terms it is taken to define, and each probe's self and declared units, before any model is called. What it cannot do is decide which reply is right, or whether a unit that moved nothing is redundant in the document or unread by the model; those stay live.

## The hard battery

`forge/conformance/pilots/travel-claim/` is the third pilot, built to be difficult for a small model rather than representative. It keeps the machine unchanged and pushes every configuration surface at once:

- Fourteen fields, of which only two can be copied verbatim. The rest must be normalised (`E-41207` from "staff number 27 044"; `+61417220391` from "0417 220 391"), derived (a return date from "came home on the Wednesday" after a stated Sunday; "Mon 3 Nov to Thu 6 Nov 2025" with the year stated once), counted (nights between two dates), summed (itemised amounts including "three nights at $189.00" into whole cents), or mapped onto an enum from paraphrase ("giving evidence at a Senate committee hearing" is `other`).
- Distractors in every document: a transit city that is not the destination, a hotel's or a colleague's phone number one digit away from the claimant's, a manager who is copied in but did not approve, a pre-trip estimate that is not an amount claimed, a foreign-currency face value beside its converted charge.
- Statements that must be read, not matched: a correction that supersedes an earlier date in the same document, an amount corrected mid-sentence ("$640.00, sorry, $460.00, she transposed the digits"), "receipts attached except the taxi receipt", two booleans stated by double negation, and a stated night count that disagrees with the dates.
- Dates that are fixed but never written as dates: "came home on the Wednesday" after a stated Sunday, "returned four nights later", and "the last Friday of February 2025 ... came back on the Monday", across a month boundary. Sentence 6 says a date fixed by a weekday or an interval counts as stated, so abstaining on it is a criticism of the model, not of the sentence.
- Two optional fields (`cost_centre`, `project_code`) that most documents do not mention and that the instructions say to omit; a placeholder value here is an invented value.
- Every family has material: two negations (date format, phone format), a role twin (claimant and approver), three declared ambiguities with rivals (day-first or month-first numeric dates; a stated total that disagrees with the itemised sum by $27.00; a stated night count that disagrees with the dates by one), ten boundary cases, three load-bearing sentences, four controls on three reference cases, three renderings on five cases with label synonyms in one table ("Sign-off", "Staff no.", "Away from", "Back"), two optional fields for deletion, and a round trip per baseline.
- Grounding on for seven fields with abstention allowed on the return date and night count, and one case (BND-101) where the document is genuinely silent and null is the only answer the key admits.

Round one ran on plan `dde8e4f8…` (corpus digest `400ee484…`): fourteen cases, ninety variants per model, eighty-two model calls. What the four models did with it is in `docs/small-models.md`, and what it taught the machine is H11 to H15 in `docs/failure-modes.md`. Round one also exposed a defect in this battery's own answer key: "two nights at $205.00" was keyed as a nightly rate and read as a total by all four models (H13). The corrected corpus, with five more cases and the second optional field, is plan `ab55e0fa…` on corpus digest `c83bb4d0…`: nineteen cases, 129 variants per model, 117 model calls. Round-one records stand as scored under their own plan.

A reply that is one JSON object with a repeated key is parsed with the last value winning and recorded as a provisional recovery that names the repeated keys, in the same way a fenced object is recovered from prose (H11); the reply is scored, and the malformation stays visible in the record. Where a reply holds more than one top-level object, the one scored is the last inside a code fence when any fence holds one, else the last in the text, because a model places its final answer last and marks it; until 9 September 2026 the object with the most keys was taken, and nine cycle replies that quoted a draft before a corrected answer were scored on the draft (H40). `docs/kernel.md` P-02, P-06 and P-07 hold the rule and its limit.

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
- **Relaxations.** The span match is verbatim after whitespace normalisation. `span_relaxations` in the grounding block may add `case_insensitive` (accept `sick` for "Sick leave") and `date_range_completion` (accept "24 June 2025" when the document says "24 to 26 June 2025", or "Mon 3 Nov 2025" for "Mon 3 Nov to Thu 6 Nov 2025"; only the two ends of a range are completions). A span accepted through a relaxation is `GROUNDED` and its verdict detail names the relaxation, so the record shows that the match was not verbatim. The list is written to the variant only when non-empty; every variant written before the option existed keeps its id. Re-scoring round two of the hard battery through `run --replay-dir` with `date_range_completion` on turned all seven of gpt-oss:20b's completed-range spans from `SPAN_NOT_IN_DOCUMENT` to `GROUNDED` and three of nemotron's five, leaving the three that were not quotations at all.
- **Records.** Every observation stores `variant.grounding`, `scoring.grounding_verdicts` (field, verdict, span, detail), and the triggers; every run record stores `grounding_verdict_counts`, which the `run` summary and the `report` (a "Grounding verdicts" table per run) now show. `fills` prints `grounding` and `abstained_fields` per fill; `evidence --trigger GROUNDING:ABSTAINED` lists the observations that abstained.
- **Routing under grounding.** A `LENGTH_VIOLATION` on a grounded variant keeps AUXILIARY live as well as CANDIDATE and TEST, because the appended "quote verbatim" sentence is a suspect for an over-long value (G2 in the register). Without grounding the routing is unchanged.
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

Every `site` oracle was changed from `exact` to `any_of` over the verbatim form found in each rendering plus the capitalised reading, status `interpretation_provisional`, before the multi-model run. ORD-004 also showed that the three renderings of one case name the place three different ways (`Car park, Gate 2`, `the car park at Gate 2`, `car park Gate 2`), so a substrate swap would otherwise have blamed the model for the source's own variation. The corrected corpus has digest `f21d38e7…f8e38`; the plan derived from it at the time was `e450b2c9…b087`. Re-running the same six baselines gave 60 of 60 matches and no live loci. (The plan id of the same corpus has moved since: every variant's body gained its `grounding` entry when that configuration was added, and the pilot configuration is one of the plan's source bindings, so adding the `repeats` key moved it again. Variant ids did not change on that second occasion. A record is bound to the plan id that wrote it; read the id from the run record, not from prose.)

Two further oracle readings were left as they were and are reported as live criticisms rather than corrected between runs, because the instruction does not settle them:

- ORD-004 `severity`: the document says nobody was injured and the reporter "rates it medium because it could have been serious". Instruction 9 gives floors (injury → at least medium, hospital → high) and says nothing about a reporter's explicit rating. The oracle takes the reporter's rating; several models apply only the floors and answer `low`. Both readings are live; TEST and CANDIDATE stay open together.
- BND-001 `phone`: no number is stated, and the form's E.164 pattern admits no "not provided" value, so no schema-valid answer exists. The oracle records the empty string with that rationale. What models do here is reported under SCOPE as much as CANDIDATE.

## Record versions

Every observation and run record carries `schema_version`, and the code reads a record by the version it was written under: a version 2 record loads against the version 2 schema, kept unchanged as `conformance-observation.v2.schema.json` and `conformance-run.v2.schema.json`, and replays its id under the version 2 domain, so nothing published before the change moves. Version 3 (8 September 2026) adds what the audit of that day found missing from the records and present only in prose:

| Key | Where | What it records |
|---|---|---|
| `started_at`, `elapsed_ms` | each attempt, and the final response | the client's clock when the request was sent and the milliseconds until the response or the failure; measured around the call, not reported by the endpoint |
| `transport_kind` | a failed attempt | `timeout` (the client's own timeout fired), `disconnected` (the remote end closed the connection), `http_status` (a status was returned, carried beside it), `other`; read from the exception, which is still recorded in full, and the same reading the `transport_error` claim predicate makes |
| `refusal_phrase_present` | `scoring` | true when a configured refusal phrase occurs anywhere in the reply, whether or not a form was recovered from it; beside a recovered object it raises `REFUSAL_SUSPECTED` with AUXILIARY, CANDIDATE and TEST live |
| `replayed_from` | the observation | the id of the observation whose reply this one re-scored, or null for a live call |
| `order`, `shuffle_seed` | the run record | how the variants were sent: `family`, `interleaved`, or `shuffled` with the seed |

A key that is absent from a version 2 record is absent, not zero or false: no table reads a duration from a record that carries none, and the kind of a version 2 transport error is read from the exception text the record carries, which is the same reading `transport_kind` fixes in a version 3 record. The version 3 keys are written only when the harness has the information: a fake executor writes no timing, and a replay carries the recorded response, its timing included, and names its source in `replayed_from`.

Every record id cited in `docs/`, `README.md`, `agent.md`, and `CLAUDE.md` is resolved by `python tools/check.py cite`, part of `all`: a cited sixteen-hex prefix must name exactly one record file in this tree or one path in `docs/archived-records.txt`, which lists the records that live on the archive branch; a citation of a record its own sentence says is `not committed` is listed by the check rather than failed, and any other unresolved or ambiguous citation fails it.

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

## What each check cannot see

Every check in the machine is invariant under some transformation of the reply: change the reply that way and the verdict does not move. That set is the check's blind spot, and a criticism the check cannot raise is not absent, only unseen. The table lists it for each check so that a survival can be read against it.

| Check | What it sees | What it cannot see (the verdict is unchanged under) |
|---|---|---|
| Schema validation (keys, types, patterns, enumerations, lengths) | The shape of the object | Any value that fits the shape; a wrong date in the right format is valid |
| `exact` oracle | The declared field's value | Nothing on that field; everything on fields with no oracle |
| `any_of` oracle | Membership in the admitted readings | Which admitted reading was taken, and why |
| `unknown` oracle | Nothing; it records the value | Everything; the field is `NOT_SCORED` whatever it holds |
| Expected abstention (`any_of` containing `null`) | Whether the field is null | Whether the model abstained because it read the document or because it did not try |
| Span occurrence | Whether the quoted words occur in the document, after whitespace normalisation and any configured relaxation | Quoting the wrong sentence that does occur; under `case_insensitive`, case; under `date_range_completion`, that the date was completed rather than quoted |
| Value in span | Substring containment | A span that contains the value by coincidence; a value derived from the span rather than read from it |
| Change against the baseline (REPEAT, ROUND_TRIP, IMPORT_DEPENDENCY, SUBSTRATE_SWAP) | Exact equality of the form fields | Direction and size of a change; a wrong value that is wrong identically on both sides counts as stable; anything outside the form fields (H12) |
| Cycles (CYCLE, and the `cycles` table) | Whether the form changed against the step before and how each field's verdict moved | Why it changed; whether a move exceeds what a repeat does on its own, which only the REPEAT row beside it can say; a model that changes a field the criticism named to another wrong value, which counts as changed and still a miss |
| Refusal detection | A phrase list, compared after folding typographic apostrophes and quotes to their plain forms (H22) | A refusal phrased outside the list; and it fires on a non-refusal that contains a listed phrase |
| Thinking channel | Whether the reply carried the channel | Reasoning written into the content; whether the channel's contents bore on the answer |
| Output tokens (claims `output_tokens`) | A count | What the tokens said |
| `format_enforced_by_server` | An extra or missing key, which refutes enforcement | Anything else; it stays `null` for a model that never sends such a key |
| Model-free controls (NON_VACUITY) | Whether the oracle rejects three corruption kinds and accepts the reference | Faults outside those kinds; a wrong, schema-valid value in a field with an `unknown` oracle is not a corruption the controls exercise. A corruption that changes nothing is refused when the plan is built (H20) |
| Routing | The triggers raised | Which live locus is at fault; that is the point, and it is why every locus after a model call is plural |
| Claims | The record fields the predicate names | Everything else in the record; and a survival is a survival only where the predicate has been shown able to fire (H21) |
| Appraisal | The readiness a person recorded, propagated through recorded attacks and supports | Whether a reading is true; the labelling is bookkeeping over decisions, not a judgement of them |

The list is finite because the checks are, and it is the reason the harness never promotes: a survival of every check is a survival of exactly these checks, with these blind spots, on these records.

The table above is prose. `docs/kernel.md` states the same limits as boundary points, each held by a test: for every check, one transformation the verdict moves under, as small as it can be made, beside one it does not, as close to the first as it can be brought, both asserted by `tests/test_kernel.py` from the catalogue in `tests/kernel_boundaries.py`. The document is generated from the catalogue and a test refuses drift, so the class of things a check cannot see is stated exactly where it has been tested and nowhere else. Three points there mark boundaries that are arguably defects (a containment check that does not normalise whitespace where the occurrence check does; a closed-list item found on a page by substring; a later, smaller object losing to an earlier, larger one); they are recorded as boundaries until a person decides.

## What this pilot does not establish

- It does not establish that any model fills forms correctly in general. The corpus is fourteen short English documents.
- It does not establish that the oracles are right. Every contestable oracle is marked provisional, and one was already wrong (see above).
- It does not establish that `format` structured output is unenforced everywhere; it records `format_enforced_by_server: false` only where an extra or missing key proves it for that call.
- It does not compare models. Cross-model tables show which failure modes each model exhibited; they are not a ranking.
- It does not establish that a grounded value is right. `GROUNDED` says the cited words exist in the document; `ABSTAINED` says the model returned `null` where it was allowed to. Neither is a verdict on content.
