# Small models on the hard battery

This document records what the travel-claim battery (`forge/conformance/pilots/travel-claim/`) showed about the smaller models the Ollama cloud serves, with a larger model run beside them as a contrast. It is a reading of records, not a ranking: each model is described by the kind of thing it got wrong, every model-side criticism keeps the answer key and the task framing as live suspects too, and nothing here says any model is fit for the job.

The battery was built for models around 12B parameters run locally. The cloud serves no Gemma 4 below 31B, so round one used the smallest models it does serve. `gemma4:12b` and `gemma4:26b` exist in the Ollama library and have not been run; the section "Running it locally" says how.

## Round one

| Run | Model | Parameters (active) | Calls | Wall time | Reply parsed | Records |
|---|---|---|---|---|---|---|
| `f16fb9d86694f2f8` | gemma4:31b | 31B dense | 82 | 97 s | 82 of 82 | 91 |
| `234ba4afe0f65690` | nemotron-3-nano:30b | 30B mixture, about 3B active | 82 | 118 s | 63 of 82 | 91 |
| `994c57cb32209741` | gpt-oss:20b | 21B mixture, about 3.6B active | 82 | 1,584 s | 82 of 82 | 91 |
| `ead3c752152a3f7e` | gpt-oss:120b (contrast) | 117B mixture, about 5B active | 82 | 390 s | 82 of 82 | 91 |

Plan `dde8e4f8…` on corpus digest `400ee484…`, 2026-09-06T05:30Z, temperature 0, seed 7, `think` false, grounding spans on. Records are under `forge/conformance/runs/travel-claim/`; an id below names `observation.<id>.json` there. Every run is labelled `REFUTED_CASES_PRESENT`, which means at least one observation kept the model live as a suspect; it does not mean the model failed the battery, and the four runs differ in what kept them there.

### What each model got wrong, and what it did not

**gemma4:31b** failed on one thing. Every one of its 19 field criticisms is `total_claimed_cents` on a document where a nightly rate had to be multiplied by a number of nights (TRV-001 `07a5671e33532f37`: 206,640 for 196,640 cents, a hotel of three nights at $189.00 a night added as $667.00; TRV-004 `5a73ccedb7b98999`: 104,705 for 94,705; BND-104 `18ae935c3a96adb9`). Where every amount was a flat figure, its totals matched, including the foreign-currency case (BND-105 `41c629e68e51f19c`) and the itemised-sum rival (`7f619d2fb2a1e236`). It normalised every identifier and phone number, derived the return date from "came home on the Wednesday" (TRV-003 `a7800193bbc620cc`), honoured the mid-document correction, ignored the copied-in colleague and the transit cities, read both double negations (BND-106 `ed0b9aaa4e0605b7`), followed all four appended rival rules, and abstained exactly where the document is silent (BND-101 `33c673b7d04e725a`). All 426 quoted spans occur in their documents. Its round trips were stable on all seven cases. It did not, however, obey instruction 1: every one of its 82 replies was wrapped in a ```` ```json ```` code fence and recovered from the prose by the parser (`recovered_from_prose` is true on each, with a provisional recovery status), the same habit it showed on the incident form (F1 in the register). The recovery is what let its content be scored at all.

**nemotron-3-nano:30b** failed on structure before content. Seventeen of its 82 replies were complete JSON objects with a repeated key (`destination_city_span`, sometimes also `contact_phone_span`) and were rejected whole by the strict parser (`5303386b6cf9f70c`, `1113b64943dcc654`, `15cfa86aefbb4c9f`); see H11 in the register for what the machine now does with these. It added a companion key the schema does not define, `nights_away_span`, in 47 of its replies, and `cost_centre_span` in 6. It invented a cost centre on every document that states none, always a placeholder: `CC-1234` fourteen times, `CC-0001` ten, `CC-0000` three (`cb0576d80302f9b4`, `281720f0cd161e44`, `e6697b60ddeae102`). It left `E30988` unnormalised eight times (`731bec3a2dc3f076`) and wrote one total in dollars instead of cents (BND-102 `9eac4ca9e005a940`: 1,255). Its totals were wrong on 37 model-call variants, on flat sums as well as multiplied ones (TRV-002 `cb0576d80302f9b4`: 111,025 for 119,755; BND-105 `0ecd24ce0f92f126`: 221,842 for 337,342, the hotel dropped). It mapped "soil sampling at the Broken Hill site" to `other` rather than `fieldwork` on every TRV-004 variant and "the Antarctic Science Symposium" to `other` rather than `conference`. It ignored both appended rules that asked it to change a reading (month-first `81330e1eaeef3f75`, itemised sum `e12a2c526e57ba11`), as it had on the incident form. What it did not do: it did not invent a return date or a night count where the document is silent (BND-101 `e6697b60ddeae102`), it read both double negations, it derived the Wednesday correctly on the baseline, and its form values were identical between every baseline and its round trip; the three round trips flagged as changed (`2f12068ee8ad95a5`, `8b9b1fd0b32842e5`, `ff67aa95217c1286`) differed only in the spurious keys, which is why the change comparison now looks at form fields alone (H12).

**gpt-oss:20b** looked like the contrast model more than like the other two small ones. Its 82 replies all parsed; it followed all four rival rules; its round trips were stable; it abstained on BND-101 (`a4ba9a34853129b6`). Its criticisms: on five of the seven TRV-003 variants it returned `null` for a return date the document fixes as "the Wednesday" after a stated Sunday (`895f20fe00ea4484`, `bd76cff07faa81fe`), though its baseline derived it (`12d6a28438a1c444`); one total dropped $100 (BND-105 `1451fe5ed8d4bdd3`); the ambiguous-phrasing totals (T4 below); and four quoted spans that do not occur in the document because the model completed a date range into a full date (`24 June 2025` for "24 to 26 June 2025", `05e856ddf3cb9ec3`; `15 July 2025`, `debf7a132b0b0272`).

**gpt-oss:120b**, the contrast, returned `null` for the derivable return date on all seven TRV-003 variants including the baseline (`6920f52f8edd83a7`), where the two smaller gpt-oss and gemma models derived it at least once. That is the only place the larger model was criticised more often than a smaller one. It also mistyped an approver's name once (`Omar El-Syed`, `28250d2f7328c318`), which the span check caught as provenance not in the document. Everything else matched, and its output never depended on a removed load-bearing sentence (21 of 21 unchanged).

### Findings that cut across the four

- **T1. Multiplying a nightly rate is where arithmetic breaks.** On the unambiguous phrasing ("three nights at $189.00 a night", TRV-001) one of four models mis-added; on flat sums three of four were right on every case. The failure is specific enough that the round-two battery adds more of it.
- **T2. "N nights at $X" without "a night" is ambiguous, and the answer key took one side.** BND-104 ("two nights at $205.00") was read as $205 total by all four models; TRV-004 ("motel three nights at $142.00") split the gpt-oss models between readings across variants (`99bc683c7328f7fa` 66,305 against `52ffa951b18690d4` 94,705 from the same model). An identical failure across four models of three families is a criticism of the key: TEST and SCOPE were live on every one of these observations, and the round-two corpus admits both readings on the ambiguous phrasing while adding cases whose phrasing is not ambiguous. The round-one records are unchanged (H13).
- **T3. Abstention competes with derivation.** The generated sentence says to output `null` "when the document does not state the value". A return date given as "the Wednesday" after a stated Sunday is not stated as a date. Two of four models took the strict reading on some or all variants, the larger more consistently. CANDIDATE, AUXILIARY (the sentence the machine appends), and SCOPE (what "state" means) are all live; the round-two instructions say that a date the document fixes by a weekday or an interval counts as stated.
- **T4. Structure failures cluster in the smallest active-parameter model.** Duplicate keys, spurious companion keys, placeholder values for an optional field the document does not mention, and a dollars-for-cents unit error all appear in nemotron-3-nano and in none of the other three. The 20B mixture with a similar active size did not show them, so active parameter count alone does not predict this.
- **T5. Rule following splits the same way it did on the incident form.** The two appended rival rules were followed by three models and ignored by nemotron, the same model that ignored the month-first rule on the incident form (F6 in the register).
- **T6. Quoted provenance fails in two different ways.** A span that is the normalised value (`sick` for "Sick leave", earlier run) and a span that is a completed reconstruction (`24 June 2025` for "24 to 26 June 2025", gpt-oss:20b) are both `SPAN_NOT_IN_DOCUMENT`. The second is arguably a fair quotation of a range; TEST stays live so a person can decide whether the matcher should accept a date that a range contains.
- **T7. Framing, and what was not observed.** One model (gemma4:31b) fenced every reply and was recovered every time; the other three returned bare objects. No model invented a return date or night count on the silent case; no reply was truncated or refused; no round trip changed a form value; no model confused claimant with approver, took a transit city as the destination, or took the copied-in colleague as the approver.

### What this does not show

- Nothing about `gemma4:12b`, which is the model the battery was built for. It was not served by the endpoint used and has not been run.
- Nothing about correctness in general: fourteen documents, one form, one day, one seed. The earlier repeatability finding (G5 in the register) means single observations of drift, such as the `Omar El-Syed` typo, may not recur.
- No ordering by size. The 31B dense model failed in one place; the 117B mixture failed in a place the 31B did not; the two mixtures of similar active size failed in different kinds of place.

## Running it locally

The battery was built to be run against a local model, and the machine now supports that without an API key. In `pilot.json`, point the endpoint at the local server and declare that no key is used:

```json
"endpoint": {
  "kind": "ollama-chat",
  "base_url": "http://localhost:11434",
  "timeout_seconds": 600,
  "options": {"temperature": 0, "seed": 7},
  "think": false,
  "auth": "none"
}
```

Add the local model id to `models` (for example `gemma4:12b`, after `ollama pull gemma4:12b`), then:

```sh
export PYTHONPATH=src
python tools/run_conformance_pilot.py validate --pilot forge/conformance/pilots/travel-claim/pilot.json
python tools/run_conformance_pilot.py run --pilot forge/conformance/pilots/travel-claim/pilot.json \
    --model gemma4:12b --output-dir forge/conformance/runs/travel-claim-local \
    --created-on "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
python tools/run_conformance_pilot.py fills    --observations-dir forge/conformance/runs/travel-claim-local
python tools/run_conformance_pilot.py evidence --observations-dir forge/conformance/runs/travel-claim-local
```

With `auth` set to `none` no Authorization header is sent and `OLLAMA_API_KEY` is not read; if the variable happens to be set, replies are still redacted against it. Expect 117 calls per model for the full battery (the round-two plan); a 12B model on a laptop GPU takes a few seconds per call. Use `--family BASELINE --limit 3` first. Once records exist, add what they show to this document and to `docs/failure-modes.md`, with observation ids from `evidence`.
