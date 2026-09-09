# Cycles: what a further pass changes, read beside the repeat floor

*Written after the five-model cycles run on the travel-claim pilot. Every observation id below is the file `observation.<id>.json` under `forge/conformance/runs/travel-claim-cycles/`; every conjecture id is in the pilot's `claims.json`, committed as `bda06bf` before any cycle record existed.*

## The question, and the form it can be put in

Whether giving a model more cycles improves its answers is a general, positive claim about models, and this harness cannot make one: its report never computes accuracy and no finite set of records confirms anything. What it can do is put the question as conjectures that one record breaks, run them, and say what survived, beside the one thing any cycle experiment has to clear first: the run's own repeat floor, the moves a byte-identical request makes with nothing asked to change.

The CYCLE family (`docs/how-it-works.md`, "Cycles, beside the repeat floor") asks the question in two forms:

- **Self-revision** (criticism `none`). The model is shown its previous answer after the document and asked to check it against the instructions, the schema, and the document, and to return the complete form again. Nothing else is added. This is the model as its own critic, the design the reviews under `docs/reviews/` call a self-confirming check.
- **External criticism** (criticism `external`). The same, with the failed checks of the previous answer listed by field: a missing required key, an extra key, a type, pattern, enum, or length violation, a span that is missing, absent from the document, or not containing its value. These come from the form schema and the document alone. `MISMATCH` and `UNEXPECTED_PRESENT` come from the answer key and are excluded in code, in the record schema, and by a test. Where no such check failed, the cycle says so.

Three cycles follow each of the nine ordinary cases per source, so a chain is baseline, cycle 1, cycle 2, cycle 3; each cycle is scored against the case's own oracle and compared with the step it follows. The same run repeats each baseline twice (REPEAT), which is the floor.

## Conjectures written before the run

| Id | Says, in the never form | Floor |
|---|---|---|
| CYC-01 | A cycle never turns a matched field into a miss when no criticism named it | CYC-09 |
| CYC-02 | Self-revision never turns a missed field into a match | CYC-10 |
| CYC-03 | External criticism never turns a missed field into a match | CYC-10 |
| CYC-04 | Self-revision never changes the answer | STAB-01 |
| CYC-05 | Told nothing failed, the model never changes the answer | |
| CYC-06 | A field the criticism named is never left unchanged | |
| CYC-07 | A named schema check never fails on the same field afterwards | |
| CYC-08 | A named grounding check never fails on the same field afterwards | |
| CYC-09 | A repeat never turns a matched field into a miss | the floor |
| CYC-10 | A repeat never turns a missed field into a match | the floor |
| CYC-11 | A later cycle never changes an answer the cycle before left unchanged | |
| CYC-12 | A cycle never returns something other than a JSON object | |
| CYC-13 | A cycle never withdraws a stated return date to null | |
| CYC-14 | Self-revision never moves the claimed total onto the key | CYC-10 |

CYC-09 and CYC-10 were already refuted by the round-three records when the file was committed (four and eight refuting repeats): the floor predicate fires on records that exist, which is what a pre-registered floor is for.

## Correction of 9 September 2026

The tables and the reading below were generated from the records under `forge/conformance/runs/travel-claim-cycles/` and stand as written. Nine of mistral-large-3:675b's cycle observations in them were scored on a draft the reply quoted before its corrected answer, because the JSON recovery took the object with the most keys (`docs/failure-modes.md`, H40). The five runs were re-scored through the replay executor under the corrected recovery into `forge/conformance/runs/travel-claim-cycles-rescore/` (run ids `dff45f17f0aa43cf`, `7b5240a6ee61dc9e`, `3d846ec45fdaf883`, `54d445cb8f64b5d1`, `a916879c950fd978`). Four runs re-score to the same verdicts. For mistral the corrected rows are:

| model | row | n | unavailable | identical | differing | match to miss | miss to match |
| --- | --- | --- | --- | --- | --- | --- | --- |
| mistral-large-3:675b | cycle 1, criticism external | 9 | 0 | 9 | 0 | 0 | 0 |
| mistral-large-3:675b | cycle 2, criticism external | 9 | 0 | 9 | 0 | 0 | 0 |
| mistral-large-3:675b | cycle 3, criticism external | 9 | 1 | 8 | 0 | 0 | 0 |
| mistral-large-3:675b | cycle 1, criticism none | 9 | 0 | 9 | 0 | 0 | 0 |
| mistral-large-3:675b | cycle 2, criticism none | 9 | 1 | 8 | 0 | 0 | 0 |
| mistral-large-3:675b | cycle 3, criticism none | 9 | 1 | 8 | 0 | 0 | 0 |

Every readable mistral cycle returned the form the step before it had returned; the invented `cost_centre` and `project_code` in the paragraph on mistral below, the "appeared, disappeared, and reappeared" chains, and the mistral part of the eleven miss-to-match moves in "Against the floor" were the harness scoring the model's quoted draft and then showing the model that draft again. What stands for mistral is the other half of the paragraph: its five wrong totals stood through every chain, unrepaired. In the conjecture table, STRUCT-07 and STRUCT-10 were refuted on these records by mistral alone and are unrefuted on the re-score; CYC-01 to CYC-05 and CYC-11 keep their refutations by the other models and lose every one by mistral. Three mistral steps are unavailable in the re-score: a re-score follows a chain only while the recorded replies answer the requests it now makes, and where the corrected step output differs from what the recorded run showed the model, the next request was never sent. Where it equals a request the recorded run made at another step, that step's reply answers it and the record names it in `replayed_from`. The re-score is never supplied to `claims` beside the original directory; `claims` refuses the pair.

## Second run, 9 September 2026, under the corrected parser

The battery was run again live on gemma4:31b, qwen3.5:397b and mistral-large-3:675b (BASELINE, REPEAT and CYCLE, `--timeout-seconds 600`, three runs at once beside two others), because the corrected reading of the first run rested on a re-score that could not follow every chain. Records: `forge/conformance/runs/travel-claim-cycles-2/` (runs `0a3c4613bc5639a6` gemma4:31b, `8f584d1ebf7358b5` qwen3.5:397b, `d7cb84cb7f7dc994` mistral-large-3:675b); every one of the 243 calls returned a JSON object. The same fourteen CYC conjectures, written before the first run, are read against it.

| model | row | n | identical | differing | match to miss | miss to match |
| --- | --- | --- | --- | --- | --- | --- |
| gemma4:31b | cycles, criticism external (1, 2, 3) | 9, 9, 9 | 9, 9, 8 | 0, 0, 1 | 0, 0, 1 | 0, 0, 0 |
| gemma4:31b | cycles, criticism none (1, 2, 3) | 9, 9, 9 | 9, 9, 9 | 0, 0, 0 | 0, 0, 0 | 0, 0, 0 |
| gemma4:31b | repeat | 18 | 16 | 2 | 0 | 0 |
| qwen3.5:397b | cycles, criticism external (1, 2, 3) | 9, 9, 9 | 8, 9, 9 | 1, 0, 0 | 0, 0, 0 | 1, 0, 0 |
| qwen3.5:397b | cycles, criticism none (1, 2, 3) | 9, 9, 9 | 8, 9, 9 | 1, 0, 0 | 0, 0, 0 | 1, 0, 0 |
| qwen3.5:397b | repeat | 18 | 11 | 7 | 1 | 3 |
| mistral-large-3:675b | cycles, criticism external (1, 2, 3) | 9, 9, 9 | 9, 9, 8 | 0, 0, 1 | 0, 0, 1 | 0, 0, 0 |
| mistral-large-3:675b | cycles, criticism none (1, 2, 3) | 9, 9, 9 | 9, 7, 7 | 0, 2, 2 | 0, 1, 1 | 0, 1, 1 |
| mistral-large-3:675b | repeat | 18 | 16 | 2 | 0 | 0 |

The moves, every one: gemma4:31b's third external cycle on TRV-005 turned a right total wrong (`3050034f9e63d990`); qwen3.5:397b's first cycle on TRV-006, under both criticism sources, moved `employee_id` onto the key (`10426e27efc85854`, `da6470ee3b93e98a`), which two of its repeats also did (`005c5692be53c007`, `62adf535bef77046`); mistral-large-3:675b added `cost_centre` as null at the third external cycle of TRV-002-P (`fea7b2b07c8314a1`), added `project_code` as null at the second self-check cycle of TRV-003-P (`162abf4e87e5ec93`) and removed it at the third (`328e40484593f9fe`), and moved the total of TRV-004 onto the key at the second self-check cycle (`2854f7c3a65a74c3`) and off it again at the third (`8f6ef916930b9cdc`).

**What this settles about the first run's correction.** The re-score of the first run (above) read every readable mistral cycle as identical to the step before, and that reading was too strong: the re-score could not follow a chain past a changed step and reused recorded replies where requests coincided. Live, mistral's cycles differ from the step before in 5 of 54, and the invented optional key that C4 described occurs in two of them, once removed again at the next cycle. The first run's nine such observations were a misreading of drafts (H40); the behaviour behind them is real at about a fifth of that rate, and it is confined to the cycle prompts: none of the model's eighteen repeats added a key. Against the floor: mistral's repeats differ 2 in 18 and its cycles 5 in 54; gemma's 2 in 18 and 1 in 54; qwen's 7 in 18 and 2 in 54, and qwen's two cycle repairs are the repair its repeats made twice on their own. On this run a further cycle changed less than a repeat did, on the fields the repeats also move, plus, for mistral, an optional key the repeats never add.

**The conjectures on the second run alone.** CYC-01 refuted 4 times (mistral 3, gemma 1); CYC-02 3 (mistral 2, qwen 1); CYC-03 once (qwen); CYC-04 5 (mistral 4, qwen 1); CYC-05 3; CYC-09 once; CYC-11 4 (mistral 3, gemma 1); CYC-14, that a self-revision cycle never moves a total onto the key, refuted for the first time by mistral's second self-check cycle on TRV-004, whose third cycle moved it off again; CYC-12 and XPRT-03 unrefuted, since every call returned an object within the budget. `docs/what-the-records-refute.md` is regenerated with these records in its basis.

## What the run showed

Five models, the same size ladder as the semantics battery: gemma4:31b, gpt-oss:20b, gpt-oss:120b, qwen3.5:397b, mistral-large-3:675b. Each ran BASELINE, REPEAT, and CYCLE only: 9 baselines, 18 repeats, 54 cycles, 81 calls. Four runs completed every call; gpt-oss:20b's cycle calls timed out at the pilot's 180 seconds eighteen times, each after two retries, and 28 cycles behind them were never sent (H30), so its chains are read as far as they go. Records are under `forge/conformance/runs/travel-claim-cycles/`; the run ids are `0c9fc624ac3ba3ad` (gpt-oss:120b), `b06f3c8b81595cea` (mistral-large-3:675b), `1d11684a0369ced6` (gemma4:31b), `b71849f755a6c881` (qwen3.5:397b) and `324cdee92312eed7` (gpt-oss:20b).

Per run, criticism source and cycle index (generated by `cycles`; `told of` counts cycles shown at least one failed check):

| model | row | n | unavailable | not comparable | identical | differing | match to miss | miss to match | other moves | told of | criticised fields | changed | still failing |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gpt-oss:120b | cycle 1, criticism external | 9 | 0 | 0 | 7 | 2 | 0 | 2 | 0 | 2 | 2 | 2 | 0 |
| gpt-oss:120b | cycle 2, criticism external | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| gpt-oss:120b | cycle 3, criticism external | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| gpt-oss:120b | cycle 1, criticism none | 9 | 0 | 0 | 7 | 2 | 0 | 2 | 0 | 0 | 0 | 0 | 0 |
| gpt-oss:120b | cycle 2, criticism none | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| gpt-oss:120b | cycle 3, criticism none | 9 | 0 | 0 | 8 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| gpt-oss:120b | repeat | 18 | 0 | 0 | 14 | 4 | 0 | 4 | 0 | 0 | 0 | 0 | 0 |
| gemma4:31b | cycle 1, criticism external | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| gemma4:31b | cycle 2, criticism external | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| gemma4:31b | cycle 3, criticism external | 9 | 0 | 0 | 8 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| gemma4:31b | cycle 1, criticism none | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| gemma4:31b | cycle 2, criticism none | 9 | 0 | 0 | 8 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| gemma4:31b | cycle 3, criticism none | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| gemma4:31b | repeat | 18 | 0 | 0 | 17 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| gpt-oss:20b | cycle 1, criticism external | 9 | 0 | 5 | 3 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| gpt-oss:20b | cycle 2, criticism external | 9 | 5 | 3 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| gpt-oss:20b | cycle 3, criticism external | 9 | 8 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| gpt-oss:20b | cycle 1, criticism none | 9 | 0 | 7 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| gpt-oss:20b | cycle 2, criticism none | 9 | 7 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| gpt-oss:20b | cycle 3, criticism none | 9 | 8 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| gpt-oss:20b | repeat | 18 | 0 | 0 | 17 | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| mistral-large-3:675b | cycle 1, criticism external | 9 | 0 | 0 | 8 | 1 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| mistral-large-3:675b | cycle 2, criticism external | 9 | 0 | 0 | 5 | 4 | 3 | 2 | 0 | 0 | 0 | 0 | 0 |
| mistral-large-3:675b | cycle 3, criticism external | 9 | 0 | 0 | 6 | 3 | 0 | 3 | 0 | 0 | 0 | 0 | 0 |
| mistral-large-3:675b | cycle 1, criticism none | 9 | 0 | 0 | 8 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| mistral-large-3:675b | cycle 2, criticism none | 9 | 0 | 0 | 6 | 3 | 2 | 1 | 0 | 0 | 0 | 0 | 0 |
| mistral-large-3:675b | cycle 3, criticism none | 9 | 0 | 0 | 5 | 4 | 3 | 2 | 0 | 0 | 0 | 0 | 0 |
| mistral-large-3:675b | repeat | 18 | 0 | 0 | 14 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| qwen3.5:397b | cycle 1, criticism external | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| qwen3.5:397b | cycle 2, criticism external | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| qwen3.5:397b | cycle 3, criticism external | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| qwen3.5:397b | cycle 1, criticism none | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| qwen3.5:397b | cycle 2, criticism none | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| qwen3.5:397b | cycle 3, criticism none | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| qwen3.5:397b | repeat | 18 | 0 | 0 | 14 | 4 | 0 | 2 | 0 | 0 | 0 | 0 | 0 |

Field moves, from the step before to the cycle or repeat:

| model | row | move | count |
| --- | --- | --- | --- |
| gpt-oss:120b | cycle 1, criticism external | contact_phone: PATTERN_VIOLATION -> MATCH | 2 |
| gpt-oss:120b | cycle 1, criticism none | contact_phone: PATTERN_VIOLATION -> MATCH | 2 |
| gpt-oss:120b | cycle 3, criticism none | purpose: MATCH -> MISMATCH | 1 |
| gpt-oss:120b | repeat | contact_phone: PATTERN_VIOLATION -> MATCH | 4 |
| gemma4:31b | cycle 3, criticism external | total_claimed_cents: MATCH -> MISMATCH | 1 |
| gemma4:31b | cycle 2, criticism none | total_claimed_cents: MATCH -> MISMATCH | 1 |
| gpt-oss:20b | cycle 1, criticism external | total_claimed_cents: MATCH -> MISMATCH | 1 |
| gpt-oss:20b | repeat | purpose: MISMATCH -> MATCH | 1 |
| mistral-large-3:675b | cycle 1, criticism external | cost_centre: MATCH -> UNEXPECTED_PRESENT | 1 |
| mistral-large-3:675b | cycle 1, criticism external | project_code: MATCH -> UNEXPECTED_PRESENT | 1 |
| mistral-large-3:675b | cycle 2, criticism external | cost_centre: MATCH -> UNEXPECTED_PRESENT | 3 |
| mistral-large-3:675b | cycle 2, criticism external | cost_centre: UNEXPECTED_PRESENT -> MATCH | 1 |
| mistral-large-3:675b | cycle 2, criticism external | project_code: UNEXPECTED_PRESENT -> MATCH | 1 |
| mistral-large-3:675b | cycle 3, criticism external | cost_centre: UNEXPECTED_PRESENT -> MATCH | 3 |
| mistral-large-3:675b | cycle 1, criticism none | cost_centre: MATCH -> UNEXPECTED_PRESENT | 1 |
| mistral-large-3:675b | cycle 2, criticism none | cost_centre: MATCH -> UNEXPECTED_PRESENT | 2 |
| mistral-large-3:675b | cycle 2, criticism none | cost_centre: UNEXPECTED_PRESENT -> MATCH | 1 |
| mistral-large-3:675b | cycle 3, criticism none | cost_centre: MATCH -> UNEXPECTED_PRESENT | 2 |
| mistral-large-3:675b | cycle 3, criticism none | cost_centre: UNEXPECTED_PRESENT -> MATCH | 2 |
| mistral-large-3:675b | cycle 3, criticism none | project_code: MATCH -> UNEXPECTED_PRESENT | 1 |
| qwen3.5:397b | repeat | total_claimed_cents: MISMATCH -> MATCH | 2 |

**The short answer.** Nothing in these records shows a further cycle doing what a repeat does not. Read model by model:

- **gpt-oss:120b.** Two baselines carried a phone number with a digit missing or a digit too many (`17e05be7899ff93e`, `44dd436060b41860`). The first cycle returned a valid number under both criticism sources, and so did all four repeats of those baselines: the slip was the noise floor, and the table's two miss-to-match moves in cycle 1 are the floor's four. After that every chain returned the previous form, except one third self-revision cycle that moved TRV-005's purpose to a reading the appraisal holds under criticism (`c011d596e5131e73`). Register entries C1 and C3.
- **qwen3.5:397b.** Fifty-four of fifty-four cycles returned the form of the step before. Four of eighteen repeats differed, and two of them moved a wrong total onto the key (`511af9daabb2765c`, `9ea32be19f6ba7fe`); the cycles on those cases kept the wrong total every time. Shown its previous answer, this model anchors to it; asked the same question with nothing shown, it sometimes moved. C2.
- **gemma4:31b.** Fifty-two of fifty-four cycles returned the previous form against a floor of one differing repeat in eighteen. The two that changed moved TRV-005's total from the key's reading to another figure (`7b88b5972394f12c`, `2b6186a1d77db0fc`). None of its three wrong totals moved. C2, C3, C5.
- **mistral-large-3:675b.** The cycles changed the form more often than the repeats did, and every change was for the worse or undid the change before: the optional keys `cost_centre` and `project_code` appeared as null where the document states neither, disappeared in the next cycle, and reappeared (nine UNEXPECTED_PRESENT observations, C4), while its five wrong totals stood through every chain. The revision sentence the harness appends, "return the complete form again", is a live suspect for the invented keys, and the record routes it so.
- **gpt-oss:20b.** Seven cycles completed out of fifty-four; the rest timed out or waited on a step that had. Six of the seven returned the form of the step before. The one that changed was the first external cycle on TRV-004, told that no check had failed, which after 8,597 generated tokens moved a total the baseline had right onto a wrong figure (`96a0a33a2ddf52a5`, from `0616e96656ab863e`). Its floor: 17 of 18 repeats identical, and the one that differed moved TRV-005's purpose onto the key's reading (`bef8446af9144a35`), a reading the appraisal holds under criticism. What a longer budget would have shown is untested. C7 and H30.

**Against the floor.** The repeat rows carry seven miss-to-match moves (four phones for gpt-oss:120b, two totals for qwen, one contested purpose for gpt-oss:20b) and no match-to-miss moves. The cycle rows carry eleven miss-to-match moves, every one of which is either a phone repair the repeats also made or mistral removing a key its own previous cycle had invented, and thirteen match-to-miss moves that the repeats never made: totals for gemma and gpt-oss:20b, a purpose for gpt-oss:120b, and the invented keys for mistral. On these cases a further cycle repaired nothing a repeat did not repair, and broke things a repeat did not break.

**External criticism had almost nothing to feed back.** The checks a cycle may show the model are the form schema's and the document's, never the key's, and on this battery those checks fired on two baselines in five models. Every other external cycle was told that no automatic check had failed. The conjectures about what a model does with a named check (CYC-06 to CYC-08) therefore rest on two fields of one model, both repaired; they are survivals of almost nothing and the table below says so.

## The conjectures, as they came out

Generated by `claims --appraisal` over the cycles run's records.

| Claim | Statement | Status | Refuted by | Standing | Tested on |
|---|---|---|---|---|---|
| `CYC-01` | A further cycle never turns a field that matched the key into one that misses it, when no criticism named that field. | `REFUTED` | 4 of 5 models, 13 observations; not by qwen3.5:397b | 12 usable, 1 contested, 0 defeated; rests on `R-TRV005-CLIENT-VISIT` | 270 observations, 5 models |
| `CYC-02` | Asked to check its own answer with nothing else shown, a model never turns a field that missed the key into one that matches it. | `REFUTED` | 2 of 5 models, 5 observations; not by gemma4:31b, gpt-oss:20b, qwen3.5:397b | usable; no argued reading | 270 observations, 5 models |
| `CYC-03` | Shown the failed schema and grounding checks of its previous answer, a model never turns a field that missed the key into one that matches it. | `REFUTED` | 2 of 5 models, 6 observations; not by gemma4:31b, gpt-oss:20b, qwen3.5:397b | usable; no argued reading | 270 observations, 5 models |
| `CYC-04` | Asked to check its own answer with nothing else shown, a model never changes it. | `REFUTED` | 3 of 5 models, 12 observations; not by gpt-oss:20b, qwen3.5:397b | usable; no argued reading | 270 observations, 5 models |
| `CYC-05` | Told that no automatic check failed on its previous answer, a model never changes it. | `REFUTED` | 3 of 5 models, 10 observations; not by gpt-oss:120b, qwen3.5:397b | usable; no argued reading | 270 observations, 5 models |
| `CYC-06` | A field named by an external criticism is never left unchanged in the next cycle. | `UNREFUTED_FOR_DECLARED_SCOPE` | - | not shown able to fail on these records | 270 observations, 5 models |
| `CYC-07` | A schema check named by an external criticism never fails on the same field after the next cycle. | `UNREFUTED_FOR_DECLARED_SCOPE` | - | not shown able to fail on these records | 270 observations, 5 models |
| `CYC-08` | A grounding check named by an external criticism never fails on the same field after the next cycle. | `UNREFUTED_FOR_DECLARED_SCOPE` | - | not shown able to fail on these records | 270 observations, 5 models |
| `CYC-09` | A repeat of the same request never turns a field that matched the key into one that misses it. | `UNREFUTED_FOR_DECLARED_SCOPE` | - | condition held on 13 records outside the scope, so the check can fail | 90 observations, 5 models |
| `CYC-10` | A repeat of the same request never turns a field that missed the key into one that matches it. | `REFUTED` | 3 of 5 models, 7 observations; not by gemma4:31b, mistral-large-3:675b | usable; no argued reading | 90 observations, 5 models |
| `CYC-11` | A later cycle never changes an answer that the cycle before it left unchanged. | `REFUTED` | 3 of 5 models, 9 observations; not by gpt-oss:20b, qwen3.5:397b | usable; no argued reading | 270 observations, 5 models |
| `CYC-12` | A cycle never returns a reply that is not a JSON object. | `REFUTED` | 1 of 5 models, 18 observations; not by gemma4:31b, gpt-oss:120b, mistral-large-3:675b, qwen3.5:397b | usable; no argued reading | 270 observations, 5 models |
| `CYC-13` | A cycle never withdraws a return date the previous answer stated, answering null where the step before gave a value. | `UNREFUTED_FOR_DECLARED_SCOPE` | - | not shown able to fail on these records | 270 observations, 5 models |
| `CYC-14` | Asked to check its own answer with nothing else shown, a model never moves the total it claimed onto the key. | `UNREFUTED_FOR_DECLARED_SCOPE` | - | not shown able to fail on these records | 270 observations, 5 models |

Three things the table cannot say for itself. CYC-02, CYC-03 and CYC-14 carry the `cycle` predicate inside their condition, so no record outside the CYCLE family can satisfy them and their liveness witness is zero by construction: CYC-14's survival means no self-revision cycle moved a total onto the key, and the part of its condition that could fire, the move itself, is shown live by CYC-10's refutations on the repeats. CYC-13 (no cycle withdrew a return date) held on nothing anywhere: no cycle in the run touched `trip_end`, so it is not shown able to fail. CYC-09, the floor for match-to-miss, is unrefuted on this run's repeats and was refuted by four repeats in round three; the floor moved between runs of the same requests, which is itself T24's finding.

## What this does not show

- That cycles are useless, or harmful, in general. Nine cases, five models, three cycles, two criticism sources, one form. A document that a first pass reads wrongly in a way the schema can catch is the case where an external cycle could do work, and this battery has almost none: its errors are arithmetic and reading, which the schema cannot see and the key must not tell.
- That self-revision changes nothing. It changed forms in three of five models; what it did not do is move a field onto the key more often than resending the request did.
- Anything about the model as its own critic beyond these records. The reviews under `docs/reviews/` argue on other grounds that a critic correlated with the generator adds little; these records are consistent with that and do not test it.
- That the criticism a cycle was shown was the right criticism. Two fields were criticised in the whole run. A pilot whose baselines fail more schema and span checks would test the external design; this one tested the self-revision design and found the floor.

## The rerun with a 600-second budget

gpt-oss:20b was run again on the same plan with the call timeout raised from 180 to 600 seconds as a run-time override (`--timeout-seconds 600`; the run record's endpoint carries it, the plan is unchanged, and the requests are byte-identical to the first run's), run `ca2c52483a6a1dbb`, records under `forge/conformance/runs/travel-claim-cycles-600s/`. Its runs shared the model with two other lanes for part of the morning, which a per-call timing would let a reader discount and these records cannot.

The budget was not the constraint, and the failure changed kind. Eighteen of its cycle calls came back without a response, the same count that had timed out at 180 seconds, and 29 cycles behind them were never sent; 34 of the 81 calls returned an object. Every one of the eighteen records reads `RemoteDisconnected`, the remote end closing the connection without a response, where the 180-second run's eighteen read `TimeoutError`, the client's own timeout; the client's 600-second timeout never fired, and the records do not say after how long the connection closed, since a per-call timing is not recorded (H34). At 600 seconds the constraint was the endpoint's, not the harness's; whether this model would have answered inside ten minutes is untested.

| model | row | n | unavailable | not comparable | identical | differing | match to miss | miss to match | other moves | told of | criticised fields | changed | still failing |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gpt-oss:20b | cycle 1, criticism external | 9 | 0 | 7 | 1 | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| gpt-oss:20b | cycle 2, criticism external | 9 | 7 | 1 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| gpt-oss:20b | cycle 3, criticism external | 9 | 8 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| gpt-oss:20b | cycle 1, criticism none | 9 | 0 | 6 | 2 | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| gpt-oss:20b | cycle 2, criticism none | 9 | 6 | 2 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| gpt-oss:20b | cycle 3, criticism none | 9 | 8 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| gpt-oss:20b | repeat | 18 | 0 | 0 | 12 | 6 | 4 | 4 | 0 | 0 | 0 | 0 | 0 |

| model | row | move | count |
| --- | --- | --- | --- |
| gpt-oss:20b | cycle 1, criticism external | total_claimed_cents: MISMATCH -> MATCH | 1 |
| gpt-oss:20b | cycle 2, criticism external | total_claimed_cents: MATCH -> MISMATCH | 1 |
| gpt-oss:20b | cycle 1, criticism none | total_claimed_cents: MISMATCH -> MATCH | 1 |
| gpt-oss:20b | repeat | nights_away: MATCH -> MISMATCH | 2 |
| gpt-oss:20b | repeat | purpose: MATCH -> MISMATCH | 2 |
| gpt-oss:20b | repeat | total_claimed_cents: MISMATCH -> MATCH | 2 |
| gpt-oss:20b | repeat | trip_end: MISMATCH -> MATCH | 2 |

Two things the eight completed cycles say. On TRV-006 the first cycle under both sources moved a contested total onto the key (`b04b52defd9e8a16`, `52860772b0780e29`, from `13ac4d00c92faa06`), and the second external cycle moved it off again (`d61d08686771c15e`); both repeats of that baseline made the same repair on their own (`08b35a61781c8ad1`, `4997be16e776d4c2`). CYC-14, that self-revision never moves a total onto the key, is refuted once by this run, and the floor made the same move twice. And the floor itself was high that morning: six of eighteen repeats differed, with verdicts moving both ways (`nights_away` and `purpose` off the key, `trip_end` and the total onto it), against one of eighteen in the first run of the same requests eight hours earlier (`compare` pairs the two runs: baselines 6 identical and 3 differing, repeats 15 and 3, and the cycles not comparable on either side). A model whose repeat floor moves between mornings by that much cannot be read on nine cases through cycles that mostly never arrived.

The repaired dossier for gpt-oss:20b's timeouts was a setting; raising it changed the kind of failure and not the count, eighteen client timeouts at 180 seconds becoming eighteen connections the remote end closed (H30, H34).

*Every count above is a count of observations under one key and one reading; the epistemic limit printed on every record applies.*
