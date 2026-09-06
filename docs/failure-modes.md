# Failure-mode register

This register records what models did wrong, or did unexpectedly, when this harness asked them to fill a form, and what the harness itself could not see or got wrong. Every entry points at records. Nothing here is a score, and the presence of a model in an entry is not a judgement of that model: the same model appears in entries it exhibited and in entries it did not, and the counts are counts of observations, not of quality.

## How to read an entry

Each entry gives:

- **What happened**, in plain words, and the case that provoked it.
- **Trigger**: the criticism label the harness attached. `LENGTH_VIOLATION` means a string exceeded the form's `maxLength`; `MISMATCH` means the value differed from the declared expectation (the oracle); `INVALID_JSON` means no JSON object could be recovered from the reply; `SPAN_NOT_IN_DOCUMENT` means the words the model cited as its source do not occur in the document; `DEPENDENCE_CHANGED` and `DEPENDENCE_UNCHANGED` record whether removing an instruction sentence changed the output; `TRANSPORT_ERROR` means the call never returned a usable reply.
- **Live loci**: which of the four suspects the harness kept open. CANDIDATE is the model, AUXILIARY the prompt and plumbing, TEST the answer key or matcher, SCOPE the task as framed. A failed expectation criticises the whole conjunction, so the set is never a single locus after a model call.
- **Evidence**: observation ids. An id `ca60a007b34eaa50` is the file `observation.ca60a007b34eaa50.json` in the directory named. Records are content-addressed and were never edited; what they say can be read back with `fills` and listed by trigger with `evidence`.
- **Open question**: what a person still has to decide. The harness stops at `AWAITING_HUMAN_TRIAGE`; it does not decide.

Two runs supply the evidence:

| Run | Pilot | Models | Records | Where |
|---|---|---|---|---|
| Nine-model battery, 2026-09-05 | `incident-form` (answer key, 117 variants per model) | gpt-oss:20b, nemotron-3-nano:30b, gemma4:31b, gpt-oss:120b, qwen3.5:397b, glm-5.3-flash, glm-5.3, deepseek-v4-flash:0731, mistral-large-3:675b | 1,053 observations, 9 runs | branch `archive/cr-eib-0.6-full`, `forge/conformance/runs/incident-form/` |
| Grounding template, 2026-09-06 | `leave-request` (no answer key, spans and abstention on) | gpt-oss:120b, deepseek-v4-flash:0731, nemotron-3-nano:30b | 24 observations, 6 runs (full six-variant plan at 04:10Z; baselines repeated at 04:40Z) | this tree, `forge/conformance/runs/leave-request/` |

The archived records carry `schema_version` `creib.conformance-pilot.observation.v1`. The observation record gained required grounding keys after they were written and is now `v2`, so the current loader refuses them by version. Read them with the code on the archive branch (`fills`, `report`), or with the raw-JSON scan that produced the ids below; they were not converted, because a published record is never rewritten.

```sh
PYTHONPATH=src python tools/run_conformance_pilot.py evidence --observations-dir forge/conformance/runs/leave-request
PYTHONPATH=src python tools/run_conformance_pilot.py evidence --observations-dir forge/conformance/runs/leave-request --trigger LENGTH_VIOLATION
PYTHONPATH=src python tools/run_conformance_pilot.py fills    --observations-dir forge/conformance/runs/leave-request
```

## F. Form filling with an answer key (incident form, nine models)

The model lists per mode are in the table "Failure modes and which models exhibited them" in `docs/how-it-works.md`; the entries here add the records.

### F1. The reply is not bare JSON

**What happened.** Instruction 1 asks for a single JSON object and no other text. gemma4 and mistral-large wrapped every reply in a code fence; deepseek did so in about half of its replies; gpt-oss:20b, qwen3.5, glm-5.3-flash, and glm-5.3 did so sometimes. The harness recovered the object and recorded the recovery as a project import.
**Trigger.** None on its own: the field verdicts are computed on the recovered object. The recovery is visible in the observation's response fields.
**Live loci.** None when the recovered object matched; the disobedience is recorded, not routed.
**Evidence.** The "Recovered from fences/prose" column of the per-model table in `docs/how-it-works.md`: 8 of 106 for gpt-oss:20b, 109 of 109 for gemma4:31b and mistral-large-3:675b, 58 of 109 for deepseek-v4-flash:0731, 9 of 109 for qwen3.5:397b, all scored replies for both GLM models. Run ids: `1af60b7baec13071` (gpt-oss:20b), `89ac399e030601b6` (gemma4), `48498573d31f896a` (mistral-large), `a1ce20368be8058a` (deepseek), `c48b915cdc4092b5` (qwen3.5).
**Open question.** Whether to keep recovering. Recovery hides a real instruction failure from the field verdicts; not recovering would turn every fenced reply into `INVALID_JSON` and lose the content. The harness does the first and says so in the record.

### F2. Reasoning is emitted as message content with the JSON at the end

**What happened.** With `think` set to false, glm-5.3 and glm-5.3-flash returned their reasoning as the message text and placed the JSON object at the end. The recovery rule in force during the run took one object from a fence or from the whole message and found none; those replies are recorded as unparseable. Re-scoring the same recorded replies offline under a widened rule (every balanced object in the text, the one with most keys wins) parses all 87; the committed records keep the original scoring.
**Trigger.** `INVALID_JSON`.
**Live loci.** CANDIDATE and AUXILIARY: the model disobeyed instruction 1, and the harness's recovery rule was too narrow to see what it had produced.
**Evidence.** 61 observations for glm-5.3 (run `527a1f75a920758d`; e.g. `93fd399a4adbc450` BND-005, `bc142c6bd8021cc5` ORD-002), 26 for glm-5.3-flash (run `f00fe2fdf60273ab`; e.g. `46e6a41e29a4e207` ORD-002, `d9df4039999dc37a` ORD-003-P). Because their baselines were unparseable, 15 and 4 dependent variants respectively are `PREREQUISITE_UNAVAILABLE` (e.g. `b3f767804037544f`, `c209498d22383c2a`, `2ce38aa224fa5b0a`).
**Open question.** Whether the `think` flag is honoured by these models on this endpoint, and whether the widened recovery rule (now in force) should be applied by a `ReplayExecutor` re-score of the archived run.

### F3. A free-text field is copied verbatim past its length bound

**What happened.** The `summary` field has `maxLength` 200. On BND-003, whose source text is long, deepseek, mistral-large, and qwen3.5 exceeded it; nemotron also exceeded it on ORD-005 in one rendering. The form schema was sent as `format` and did not stop it. The same mode recurs in the grounding run (G2).
**Trigger.** `LENGTH_VIOLATION`.
**Live loci.** CANDIDATE and TEST (the oracle for a boundary case is provisional); AUXILIARY where the bound was sent as `format` and not enforced.
**Evidence.** `879cc6d200009b00` (deepseek, BND-003), `22c19f2961fffc0d` (mistral-large, BND-003), `a37f41921ba0d4fa` (qwen3.5, BND-003), `c298cd7b1b28a5b9` (nemotron, ORD-005 SUBSTRATE_SWAP), `0de6b334d338d455` (nemotron, BND-003).
**Open question.** None for the harness: the bound is the form's own rule. For the prompt author: whether to state the bound in words as well as in the schema.

### F4. Fabrication when the form leaves no honest answer

**What happened.** BND-001 states no phone number, and the form's E.164 pattern admits no "not provided" value. Six models invented a number (`+61000000000`; nemotron `+61123456789`). gpt-oss:120b returned an empty string, which violates the pattern but invents nothing. The two GLM replies on this case were unparseable (F2).
**Trigger.** `MISMATCH` for the invented numbers; `PATTERN_VIOLATION` for the empty string.
**Live loci.** CANDIDATE (inventing a number is a specific choice), TEST (the oracle's empty-string reading is provisional), SCOPE (the form gives no honest answer).
**Evidence.** Invented: `127987738e0e8d8a` (deepseek), `61163f001c018aae` (nemotron), `bb688589e4fe74f6` (gpt-oss:20b), `06aad98724169229` (mistral-large), `27a45cf628df305d` (qwen3.5), `467a8d9724e21eb6` (gemma4). Empty: `bd47f6f931602d4f` (gpt-oss:120b). Unparseable: `ab0ed7d946b20b0b` (glm-5.3), `9b076fe099c91968` (glm-5.3-flash).
**Open question.** This is the mode the grounding configuration was built to address (G1). Whether a form should always offer an abstention is a decision about the form, not about the model.

### F5. The granularity of "as named in the document" is underdetermined

**What happened.** Instruction 8 asks for the place "as named in the document". Every model, on the same cases, either dropped a qualifier (`Site 4 Parramatta` for `loading bay, Site 4 Parramatta`) or added one (`the yard`, `Gate 2 car park`). A first version of the oracle was itself wrong here (title-cased forms) and was corrected before the nine-model run; see `docs/how-it-works.md`, "First oracle defect".
**Trigger.** `MISMATCH` on `site`, 101 field verdicts across the nine models (3 to 16 per model; the per-model table gives the split).
**Live loci.** CANDIDATE, TEST, and SCOPE together. When a probe fails identically across nine models of different sizes and families, the plural routing is doing its job: the specification does not say what "site" means.
**Evidence.** One example per model: `c35f3c6b0d379f26` (gemma4, ORD-002-P NEGATION), `efc5dd3f4d43c80f` (gpt-oss:120b, ORD-002-P SEMANTIC_ROLE_TWIN), `34fe23945b110227` (glm-5.3-flash, ORD-002 BASELINE), `5f7fac34e9c6fb79` (deepseek, BND-004), `d863261060b3d709` (nemotron, ORD-004 SUBSTRATE_SWAP), `a37f41921ba0d4fa` (qwen3.5, BND-003), `cc83c85fc4710d45` (gpt-oss:20b, BND-004), `22c19f2961fffc0d` (mistral-large, BND-003), `9c2c6238f4c23970` (glm-5.3, ORD-004 SUBSTRATE_SWAP).
**Open question.** Sharpen instruction 8, or accept the variation and widen the oracle. Either is a human decision; neither is a re-score of the models.

### F6. An explicit disambiguation rule is ignored

**What happened.** BND-004 contains the date `03/04/2025`. The RIVAL_SUBSTITUTION family appends one rule at a time: "read as DD/MM/YYYY" or "read as MM/DD/YYYY". Four models kept the day-first reading when told to read month-first.
**Trigger.** `MISMATCH` on `incident_date` under the `month_first` rival.
**Live loci.** CANDIDATE, AUXILIARY (where and how the rule was placed), TEST.
**Evidence.** `4a118b7d3c5ebb94` (nemotron), `af5ba55f1764fe21` (glm-5.3-flash), `14652cbdc8318e20` (deepseek), `c60a2d67b050a74c` (mistral-large). Followed the rule: `c603ae74ca97c07e` (gpt-oss:120b), `9fb5b128195fd90e` (qwen3.5), `d920cf7b085f2724` is gemma4 under the same rule with a `site` mismatch only.
**Open question.** Whether a rule appended at the end of the instructions is read at all by these models, which is a prompt-design question before it is a model question.

### F7. A severity rule with a gap is filled two different ways

**What happened.** ORD-004 says nobody was injured and the reporter "rates it medium because it could have been serious". Instruction 9 gives floors (injury means at least medium, hospital means high) and says nothing about a reporter's own rating. The oracle takes the reporter's rating; gemma4 and gpt-oss:120b answered `low` on the baseline, and qwen3.5 and glm-5.3 did so on other variants of the case.
**Trigger.** `MISMATCH` on `severity`.
**Live loci.** CANDIDATE and TEST, with the oracle marked provisional. This is a specification gap first.
**Evidence.** `a192ec85c2245274` (gemma4, BASELINE), `3af0ad7ce8bef0bd` (gpt-oss:120b, BASELINE), `db82dbf19de09c73` (qwen3.5, DELETION), `91a7a4c9eac5f48e` (glm-5.3, NEGATION). Answered `medium` on the baseline with no trigger: `276d925b94b1756e` (deepseek), `24f86518f3bfb3d9` (glm-5.3-flash), `2c46aff2ffdd44ac` (mistral-large), `a63ff6d843e3e9ba` (qwen3.5), `6f5089527877dc25` (nemotron), `4bf4aa6245efaa13` (gpt-oss:20b).
**Open question.** Add a sentence to instruction 9 about explicit ratings, then re-score the recorded replies through `ReplayExecutor` if the oracle changes. No new model calls are needed to settle the oracle side.

### F8. Extraction depends on the rendering

**What happened.** The same case rendered as prose, table, and email should give the same form. nemotron omitted or changed `incident_time` on some renderings of ORD-001 only.
**Trigger.** `MISMATCH` on `incident_time`, 4 field verdicts, all nemotron.
**Live loci.** CANDIDATE and SCOPE (the rendering may have altered the text the model saw).
**Evidence.** `533ecfe7a35c076b` (nemotron, ORD-001 SUBSTRATE_SWAP) and the other SUBSTRATE_SWAP observations of ORD-001 in run `d40fda50c7bffcd6`.
**Open question.** Whether the table rendering of a time is legible to smaller models, which is a question about the corpus as much as the model.

### F9. Two calls never returned

**What happened.** Two calls to gpt-oss:20b exceeded the 180-second client timeout. They are recorded as transport errors, and the run's scope label cannot be `UNREFUTED_FOR_DECLARED_SCOPE` however its other fields did.
**Trigger.** `TRANSPORT_ERROR`.
**Live loci.** AUXILIARY.
**Evidence.** `ba4ac50071f5b2d5` (ORD-006 BASELINE), `cf82ad1981083df5` (ORD-001 IMPORT_DEPENDENCY); one dependent variant is `PREREQUISITE_UNAVAILABLE` as a result.
**Open question.** None. A retry policy exists (`--retries`); whether to spend it is a cost decision.

### F10. Modes that were probed and not observed

These are recorded because "not observed" is evidence too, of the same weight as the rest: it says nothing beyond these cases.

- **Inverted formatting instruction ignored.** On all 138 scored NEGATION variants, every model's output changed from its baseline (`IDENTICAL_TO_BASELINE` never fired).
- **Round trip unstable.** On all 65 scored ROUND_TRIP variants the second fill equalled the first.
- **Key outside the schema while `format` was sent.** Never, so `format_enforced_by_server` stayed null everywhere: the observations neither prove nor refute server-side enforcement. (The 18 `EXTRA_FIELD` verdicts in the run are the model-free NON_VACUITY controls, which inject a `notes` key deliberately to check that the oracle rejects it.)
- **Hospital rule missed.** No model answered below `high` where hospital treatment was stated.
- **Refusal.** No reply matched a refusal phrase.

## G. Grounding spans and abstention (leave-request template, three models)

The template asks for a verbatim quotation (`<field>_span`) beside each of six fields and allows `null` on `end_date` and `total_days`. Case LR-001 (Maya Patel, annual leave) states every value; LR-002 (Tom Nguyen, sick leave) states neither the end date nor the number of days. Each model was run over the full six-variant plan at 04:10Z and its two baselines were repeated at 04:40Z.

### G1. All three models abstained where the document is silent

**What happened.** On LR-002 every model returned `null` for `end_date` and `total_days`, with `null` spans, in the baseline, in the round trip of its own output, and in the repeated baseline. No model invented an end date or a day count. Compare F4, where the form offered no abstention and six of nine models invented a value; the two runs use different forms and models, so this is a contrast, not a controlled comparison.
**Trigger.** None. `ABSTAINED` is a grounding verdict, not a criticism, and the field stays `NOT_SCORED`.
**Live loci.** None from abstention.
**Evidence.** Baselines `528a21833fa78335`, `53b1dbcc7fc0b87b` (gpt-oss:120b), `c264d7fd3fc3d640`, `a0076e382bc8efff` (deepseek), `ca60a007b34eaa50`, `dcf5e4abcc12de3a` (nemotron); round trips `fc6d19e0e4b6608e`, `22a31f655a2ef180`, `adb347362170f154`. `evidence --trigger GROUNDING:ABSTAINED` lists 6 verdicts per model.
**Open question.** Whether the models abstain because the configuration allowed it or because the document is plainly silent. A corpus case where the value is stated but hard to find would separate the two, and the harness cannot pose that case for you.

### G2. Asked to quote, two models copied the quotation into the value

**What happened.** Instruction 7 asks for a `reason` of at most 160 characters. On LR-002 deepseek copied the whole sentence (172 characters) into `reason` and cited the same sentence as its span; nemotron copied it with the following sentence as well (191 characters). gpt-oss:120b summarised (`Unwell, unable to work`, then `I'm unwell` on the repeat) and cited `I'm unwell`. On LR-001 all three summarised. The over-length value recurs identically in the round trip.
**Trigger.** `LENGTH_VIOLATION`.
**Live loci.** CANDIDATE and TEST on the baseline; CANDIDATE, AUXILIARY, and TEST on the round trip (the re-rendering template is a suspect there).
**Evidence.** `c264d7fd3fc3d640`, `a0076e382bc8efff`, `22a31f655a2ef180` (deepseek); `ca60a007b34eaa50`, `dcf5e4abcc12de3a`, `adb347362170f154` (nemotron). Summarised within the bound: `528a21833fa78335`, `53b1dbcc7fc0b87b` (gpt-oss:120b).
**Open question.** Whether the generated grounding sentence ("quote verbatim") bleeds into the value fields for some models. That is a prompt-design question about the sentence the harness appends, so AUXILIARY should be read as live here even though the routing table for `LENGTH_VIOLATION` does not name it. The same over-length mode appeared without any grounding instruction in F3, so grounding is not the sole cause.

### G3. The cited span is the normalised value, not the document's words

**What happened.** The document says `Sick leave`. nemotron returned `leave_type: "sick"` (correct for the enum) and `leave_type_span: "sick"`, which does not occur in the document; the other two models cited `Sick leave`. The same thing happened on the repeat.
**Trigger.** `SPAN_NOT_IN_DOCUMENT`.
**Live loci.** CANDIDATE, TEST, SCOPE.
**Evidence.** `ca60a007b34eaa50`, `dcf5e4abcc12de3a` (nemotron, LR-002). Cited correctly: `c264d7fd3fc3d640` (deepseek), `528a21833fa78335` (gpt-oss:120b).
**Open question.** Whether the matcher should be case-insensitive. The harness reads "verbatim" strictly and keeps TEST live so that this stays a visible decision. Making the match case-insensitive would hide the fact that the model wrote the value where a quotation was asked for.

### G4. A removed instruction sentence changes one model's output and not the others'

**What happened.** The template declares sentence 1 ("Output a single JSON object...") load-bearing. Removing it changed gpt-oss:120b's `reason` on LR-002 and nothing else; deepseek and nemotron returned outputs identical to their baselines on both cases.
**Trigger.** `DEPENDENCE_CHANGED` (gpt-oss:120b, LR-002); `DEPENDENCE_UNCHANGED` (all other five).
**Live loci.** AUXILIARY and SCOPE for a change; AUXILIARY, TEST, and SCOPE for no change. Neither is a criticism of the model; the family records dependence and judges nothing.
**Evidence.** Changed: `2e51c8da8507afe9`. Unchanged: `ed09aac456d21f43` (gpt-oss:120b LR-001), `996514bbf40f0d53`, `af5a2c167a15bb45` (deepseek), `6a97dcafb2f8a42c`, `2028c24c105e9f41` (nemotron).
**Open question.** See G5: with a model whose replies vary between identical calls, one changed output cannot be attributed to the removed sentence.

### G5. Identical requests do not always return identical replies

**What happened.** Every request carries `temperature 0` and `seed 7`, and the request digest recorded in each observation is identical between the 04:10Z and 04:40Z baselines of the same case. deepseek's `reason` on LR-001 changed from `for a family wedding in Adelaide` to `family wedding in Adelaide`; gpt-oss:120b's `reason` on LR-002 changed from `Unwell, unable to work` to `I'm unwell`. The other four pairs were byte-identical. nemotron was identical on both cases.
**Trigger.** None. Repeatability is not a family; it is visible only because both records exist.
**Live loci.** None recorded. Read AUXILIARY (the hosted endpoint) and CANDIDATE as live in your own triage.
**Evidence.** Pairs (04:10Z, 04:40Z): deepseek LR-001 `c49a253aec9b3099` / `912304e11a27c4df` (differs); gpt-oss:120b LR-002 `528a21833fa78335` / `53b1dbcc7fc0b87b` (differs); deepseek LR-002 `c264d7fd3fc3d640` / `a0076e382bc8efff`, gpt-oss:120b LR-001 `bee66daa37eaaf40` / `7437b81699f90c08`, nemotron LR-001 `f397d43479f7c26f` / `95145da2e75c7e54`, nemotron LR-002 `ca60a007b34eaa50` / `dcf5e4abcc12de3a` (identical).
**Open question.** Any family that compares one call against another (NEGATION, IMPORT_DEPENDENCY, ROUND_TRIP) inherits this noise floor. A repeated baseline in the same run would let the harness report it; that is a change to the machine, listed under H.

## L. Limitations of the models, as far as these records show

Stated as limitations, each tied to the entries above. None of them generalises beyond the documents and forms that were run.

- **L1. Output-format instructions are not reliably obeyed, and the endpoint's `format` schema did not enforce them.** Seven of nine models wrapped or buried the JSON (F1, F2); no model exceeded the schema's key set, so the observations cannot say whether `format` would have stopped one that did (F10).
- **L2. Copying is constraint-blind.** Models that copy source text into a bounded field do not check the bound (F3, G2). Stating the bound in the schema alone was not enough for four of nine models on the long case.
- **L3. A form that demands a value gets one.** Where no honest answer existed, six of nine models fabricated (F4). Where `null` was allowed, all three models tested used it (G1). The records support only the narrow claim: the option has to exist in the form.
- **L4. Ambiguity is resolved silently and from prior habit.** Four of nine models kept a day-first date reading against an explicit month-first rule (F6).
- **L5. "As named in the document" has no shared meaning across models** (F5). This is as much a limitation of instructions written in ordinary language as of the models that read them.
- **L6. Reasoning leaks into the answer channel for some models even when told not to think** (F2).
- **L7. Quotation drifts toward normalisation.** At least one model wrote its normalised value where a verbatim quotation was asked for (G3).
- **L8. Temperature 0 with a fixed seed is not repeatability on the hosted endpoint** (G5). Two of six repeated baselines differed in wording.
- **L9. Smaller was not systematically worse.** Across F1 to F9, the 20b and 30b models appear in some entries the 397b and 675b models do not, and the reverse. The records do not support a size ordering, and the harness does not compute one.

## H. Limitations and defects of the harness itself

Recorded with the same discipline: what it could not see, what it got wrong, and what was done about it.

- **H1. The recovery rule was too narrow for reasoning-in-content replies** (F2). Widened after the run; the archived records keep the original scoring, and the widened rule's effect was measured offline and reported, not substituted.
- **H2. The first oracle was wrong on `site`.** Title-cased expectations against verbatim instructions. Corrected before the nine-model run; TEST had been live on every affected observation. Two further oracle readings (F4, F7) were left provisional rather than corrected between runs.
- **H3. Change-against-baseline is exact.** A punctuation or wording drift counts as a change, so `DEPENDENCE_CHANGED` and `IDENTICAL_TO_BASELINE` cannot separate dependence from the noise floor in G5. A repeated baseline in the same run, or a tolerance declared in configuration, would be a change to the machine: code, schema, and test together.
- **H4. The span matcher is verbatim and case-sensitive after whitespace normalisation** (G3). It does not check that the quoted words are the right words, and a quotation of the wrong sentence that does occur in the document is `GROUNDED`.
- **H5. `format_enforced_by_server` can only ever be refuted.** It is set to false when an extra or missing key proves the schema was not enforced, and stays null otherwise (F10).
- **H6. The first grounding run's records could not be reloaded.** The ROUND_TRIP family built an `exact` oracle from the baseline output, and an exact oracle cannot hold the `null` an abstaining baseline returns; every record of that run failed on load. The oracle for an abstained baseline field is now `unknown` (stability is carried by the change-against-baseline comparison, which compares nulls), the test `test_round_trip_of_an_abstained_baseline_materialises_reloads_and_scores` guards it, and the run was repeated. The unloadable records were never committed.
- **H7. The observation and run records changed shape without a version change.** Adding the grounding keys made the archived v1 records fail with a missing-property error under the same version string. Both record kinds are now `v2`, a v1 record is refused by name (`test_v1_records_are_refused_by_version`), and the archived records stay readable with the code that wrote them.
- **H8. Routing for `LENGTH_VIOLATION` does not name AUXILIARY.** G2 suggests the appended grounding sentence may be a cause of over-length values. The routing table is fixed in `routing.py`; widening it is a code, schema, and test change and has not been made, because one case in two models is not enough to widen a rule.

## Adding an entry

1. Run `evidence` on the observations directory, with `--trigger` if you already know the label. Take the observation ids from there; never from memory.
2. Say what happened in plain words, name the trigger, list the live loci as the record has them, and give the ids. If you think a locus should be live that the routing did not name, say so in the open question, as G2 does; do not edit the record.
3. If the mode was probed and not seen, record that too (F10). Absence on these cases is the whole claim.
4. Do not rank, do not total across models, and do not write "pass" or "accuracy". An entry that reads as a verdict on a model has been written wrongly.
