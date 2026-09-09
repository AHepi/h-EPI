# What a model's reading of a document depends on, found with no key and no manifest

*Written after five complete runs of the `semantics-unit-dependence` pilot: gemma4:31b, gpt-oss:120b, qwen3.5:397b, mistral-large-3:675b, and gpt-oss:20b at the low reasoning setting, each sent the whole semantics document with one of its fifty-eight units removed at a time, for five of the document's own argued consequences; a sixth run, gpt-oss:20b at the pilot's boolean setting, was stopped fourteen calls short of its end at the maintainer's instruction and has no run record; its 296 published observations stay in the directory without a run record: the removal tables, which `dependence` reads through run records, do not see them; `claims` reads every observation in a directory and does, so the conjecture table is generated with `--without-run 3bbf9932aab16166` (H43; "Correction of 9 September" below). Every observation id is a file under `forge/conformance/runs/semantics-unit-dependence/`; the conjectures UDP-01 to UDP-07 were committed as `bcec03b` before any record existed.*

## The question

Every earlier pilot in this repository compiled a semantics into numbered instruction sentences and an answer key by hand, and varied one sentence at a time. That is a manifest. A large model auditing a document does not need one: it reads the document, finds the definitions the argument rests on, and asks what happens without them. The question this pilot puts is whether that behaviour has a mechanical form the harness can run on weaker models, with nothing declared and nothing scored.

## The mechanism

The document is split into units at its own markdown headings, at the levels the pilot names (here 2 and 3). There are fifty-eight. For each probe, every unit is removed once, with every other line byte-identical, and the model is asked the same two questions it was asked on the full document: does the claim under assessment follow from the document as written (`follows`, `does_not_follow`, `not_determined`), and which of the document's named commitments and defined terms does it depend on (`essential`, a list drawn from a closed vocabulary). The reply is compared field by field with the same model's reply on the full document, and that comparison is the whole result: moved, unmoved, or unavailable when one of the two replies was not a form. No key exists. Both fields carry the `unknown` oracle, every field verdict is `NOT_SCORED`, and the run label is the no-scored-output one unless a repeat differed, which keeps the model live through `REPEAT_DIFFERS` as it does everywhere else in the harness.

The probes are found mechanically too. A section is a probe when its body carries the document's own argument markup, a bold `Claim.`, `Counterexample.`, `Derivation.`, `Construction.` or `Consequence.` label, and the claim under assessment is the section's heading, restated in a short preamble before the whole document. Five sections qualify:

| Probe | Claim (the section heading) | Own argument | Definitions the argument uses |
|---|---|---|---|
| DEP-01 | Historical acyclicity does not imply semantic acyclicity | U44 | none found by pattern |
| DEP-02 | Losing a premise loses an argument, not automatically its conclusion | U45 | U31 (Usable, Essential, Standing, Licensed) |
| DEP-03 | Recursion is not universality | U46 | U07 (K-RECURSION), U39, U40, U41, U42 (universality, UU, UC, UED) |
| DEP-04 | Provisional reasoning does not require a completed hierarchy of judges | U47 | none found by pattern |
| DEP-05 | A finite record does not logically determine universal capacity | U48 | U42 (UED) |

The vocabulary is what three patterns find in the document: commitment names of the form `K-NAME`, symbols inside `\mathrm{}` in displays, and the bare abbreviations UED, UU, UC and OCA. Twenty-nine terms occur at least twice, two of them noise the patterns could not tell from a symbol (`adv`, a superscript, and `understand`, a function name); they are in the list because the rule that put them there is the rule that put the others there. A unit is taken to define a term when the term first occurs in it, when its heading names it, or when it contains a display introducing it with `\iff`. That is a heuristic over the document's conventions and is recorded on every variant so it can be checked against the document. Two probes have no declared unit at all: the acyclicity argument and the provisional-reasoning construction name no formal term, so for them every unit but their own is `other`.

Each unit therefore stands in one of three relations to a probe, computed before any model is called: `self`, the document's own argument for the claim; `declared`, a unit defining a term that argument uses; `other`. The model-free unit table, every unit and the terms it is taken to define, is the first output and is in the pilot's generator output.

Two repeats of every baseline give the floor. Every count of "moved" below is read against how often a byte-identical request moved on its own.

## What the removal can and cannot show

A removal that moves the reply criticises three things together: the document as sent, since the unit did work or its absence changed position and length; the probe, which has no key and a floor; and the choice of units, claim and relation, which a pattern made. A removal that moves nothing says the unit had no observable effect on this reply, which is consistent with the document carrying the content elsewhere, with the model answering from the claim alone, and with the model not reading the unit at all. Nothing here says which reply was right. The model's own list of essential terms is set beside what removal moved, for the units that define at least one term: a unit the model named whose removal moved nothing, and a unit it did not name whose removal moved the answer, are the two cells to read.

## Conjectures written before the run

| Id | Says, in the never form |
|---|---|
| UDP-01 | Removing an `other` unit never moves `follows` |
| UDP-02 | Removing a `declared` unit never leaves both fields unmoved |
| UDP-03 | Removing the claim's own argument never moves `follows` |
| UDP-04 | A repeat never moves `follows` |
| UDP-05 | On the full document a model never says a derived claim does not follow |
| UDP-06 | On the full document a model never returns an empty essential list |
| UDP-07 | Within 600 seconds a call on the whole document never times out |

## What the runs showed

Five runs are complete and are read here. The gpt-oss:20b run at the pilot's boolean reasoning setting generated about four thousand tokens a call, thirty-five seconds each, and was on course to take most of a day, so a second gpt-oss:20b run was started beside it with the reasoning setting `low` as a run-time override, recorded in that run record's `endpoint` and nowhere else; the plan and every request but the setting are the same. The low-setting run is the one read below. The boolean-setting run was stopped after 296 of its 310 calls, at the maintainer's instruction to stop using the gpt-oss models, before it could write a run record; its observations were committed as they were published and remain in the directory without a run record. `dependence` and `report` read a directory through its run records and do not see them; `claims` reads every observation in a directory and does, which this document said otherwise until 9 September (H43). The removal tables are generated by `dependence` over the five complete runs, and the conjecture table by `claims` with `--without-run 3bbf9932aab16166`, which leaves that run out and names it in the summary.

| Model | Run | Replies | Transport errors | Tokens, median of replies | Tokens, most | Seconds, median | Seconds, most | Run label |
|---|---|---|---|---|---|---|---|---|
| gemma4:31b | `25c3f269eb5d6d77` | 305 | 0 | 37 | 47 | 0.9 | 199 | `INCONCLUSIVE_NO_SCORED_OUTPUT` |
| gpt-oss:120b | `309e47f76fe6428a` | 305 | 0 | 577 (thinking channel) | 1,276 | 2.3 | 6 | `REFUTED_CASES_PRESENT` (three repeats differed) |
| qwen3.5:397b | `c0c0b8085920d1e5` | 305 | 0 | 44 | 83 | 2.0 | 3 | `REFUTED_CASES_PRESENT` (two repeats differed) |
| mistral-large-3:675b | `68e6d8f408b24353` | 303 | 2 | 37 | 63 | 1.7 | 7 | `INCONCLUSIVE_NO_SCORED_OUTPUT` |
| gpt-oss:20b, `think: low` | `d8c83006dbb18592` | 305 | 0 | 732 (thinking channel) | 18,180 | 9.2 | 215 | `REFUTED_CASES_PRESENT` (five repeats differed; one repeat's list carried a term outside the closed vocabulary) |

The prompt was between 16,083 and 17,547 tokens on every call. Each run is five baselines, ten repeats, and 290 removals: 58 units for each of five probes. Six of the low-setting gpt-oss:20b calls succeeded on the retry after the remote end closed the connection on the first attempt; every reply of that run carried a thinking channel, at `low`, as at every setting the endpoint documents for these models (L10).

**Removals by relation.** Each row counts removals of one run whose unit bears the named relation to the claim; a removal is moved when either field differs from the same model's baseline reply, with the array compared as a set, and reordered only when the list held the same items in another order.

| model | relation | n | unavailable | unmoved | of which reordered only | moved | moved: follows | moved: essential |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gemma4:31b | self | 5 | 0 | 3 | 0 | 2 | 0 | 2 |
| gemma4:31b | declared | 7 | 0 | 5 | 0 | 2 | 0 | 2 |
| gemma4:31b | other | 278 | 0 | 228 | 0 | 50 | 0 | 50 |
| gpt-oss:120b | self | 5 | 0 | 4 | 1 | 1 | 0 | 1 |
| gpt-oss:120b | declared | 7 | 0 | 5 | 0 | 2 | 0 | 2 |
| gpt-oss:120b | other | 278 | 0 | 188 | 3 | 90 | 0 | 90 |
| mistral-large-3:675b | self | 5 | 0 | 4 | 0 | 1 | 1 | 1 |
| mistral-large-3:675b | declared | 7 | 0 | 6 | 0 | 1 | 0 | 1 |
| mistral-large-3:675b | other | 278 | 2 | 222 | 7 | 54 | 0 | 54 |
| qwen3.5:397b | self | 5 | 0 | 1 | 0 | 4 | 0 | 4 |
| qwen3.5:397b | declared | 7 | 0 | 1 | 0 | 6 | 0 | 6 |
| qwen3.5:397b | other | 278 | 0 | 197 | 12 | 81 | 0 | 81 |
| gpt-oss:20b, low | self | 5 | 0 | 2 | 0 | 3 | 0 | 3 |
| gpt-oss:20b, low | declared | 7 | 0 | 5 | 0 | 2 | 0 | 2 |
| gpt-oss:20b, low | other | 278 | 0 | 134 | 7 | 144 | 0 | 144 |

**The repeat floor**, per model: gemma4:31b 0 of 10 repeats moved; gpt-oss:120b 3 of 10 (one on DEP-02, both on DEP-05); mistral-large-3:675b 0 of 10; qwen3.5:397b 2 of 10 (both on DEP-05) and one reordered only; gpt-oss:20b at low 5 of 10 (one on DEP-01, both on DEP-02, both on DEP-05). Every move a repeat made was on `essential`; no repeat moved `follows`.

**The model's own list against removal**, for the 90 removals per run of a unit that defines at least one term:

| model | units defining a term | named and moved | named and unmoved | not named and moved | not named and unmoved | unavailable |
| --- | --- | --- | --- | --- | --- | --- |
| gemma4:31b | 90 | 4 | 2 | 10 | 74 | 0 |
| gpt-oss:120b | 90 | 6 | 3 | 20 | 61 | 0 |
| mistral-large-3:675b | 90 | 5 | 2 | 13 | 69 | 1 |
| qwen3.5:397b | 90 | 12 | 2 | 13 | 63 | 0 |
| gpt-oss:20b, low | 90 | 9 | 2 | 38 | 41 | 0 |

**The conjectures**, generated by `claims` over the five runs (`claims --claims forge/conformance/pilots/semantics-unit-dependence/claims.json --observations-dir forge/conformance/runs/semantics-unit-dependence --without-run 3bbf9932aab16166`; 1,525 observations supplied, the stopped run's 296 left out):

| Claim | Statement | Status | Refuted by | Standing | Tested on |
|---|---|---|---|---|---|
| `UDP-01` | Removing a unit unrelated to the claim (neither its own argument nor a definition that argument uses) never moves the model's answer to whether the claim follows. | `UNREFUTED_FOR_DECLARED_SCOPE` | - | not shown able to fail on these records | 1450 observations, 5 models |
| `UDP-02` | Removing a unit that defines a term the claim's own argument uses never leaves both form fields unmoved. | `REFUTED` | 5 of 5 models, 22 observations (gemma4:31b, gpt-oss:120b, gpt-oss:20b, mistral-large-3:675b, qwen3.5:397b) | usable; no argued reading | 1450 observations, 5 models |
| `UDP-03` | Removing the document's own argument for the claim never moves the model's answer to whether the claim follows. | `REFUTED` | 1 of 5 models, 1 observations; not by gemma4:31b, gpt-oss:120b, gpt-oss:20b, qwen3.5:397b | usable; no argued reading | 1450 observations, 5 models |
| `UDP-04` | A byte-identical repeat of the request never moves the model's answer to whether the claim follows. | `UNREFUTED_FOR_DECLARED_SCOPE` | - | condition held on 1 records outside the scope, so the check can fail | 50 observations, 5 models |
| `UDP-05` | On the full document a model never says that a claim the document itself derives does not follow. | `REFUTED` | 1 of 5 models, 3 observations; not by gemma4:31b, gpt-oss:120b, gpt-oss:20b, qwen3.5:397b | usable; no argued reading | 75 observations, 5 models |
| `UDP-06` | On the full document a model never returns an empty list of essential terms. | `REFUTED` | 4 of 5 models, 11 observations; not by mistral-large-3:675b | usable; no argued reading | 75 observations, 5 models |
| `UDP-07` | Within a 600-second budget a call on the whole document never times out. | `REFUTED` | 1 of 5 models, 2 observations; not by gemma4:31b, gpt-oss:120b, gpt-oss:20b, qwen3.5:397b | usable; no argued reading | 1525 observations, 5 models |

**The yes-or-no answer moved once in 1,448 comparable removals.** Across five runs, five probes, and fifty-eight units, `follows` changed on one removal: mistral-large-3:675b, asked about the acyclicity claim with the document's own argument for it removed (U44), said it does not follow (`4a42d1157b22b318`, against its baseline `815bf4ff7e09d8d8`). Every other removal left `follows` where the baseline had it: every unit defining a term the argument uses, every unit carrying the argument itself, every other unit, for every model. UDP-03 is refuted by that one record; UDP-01 survives, and is not shown able to fail, because no removal of an unrelated unit moved `follows` anywhere; UDP-02 is refuted twenty-two times, by every model, because removing a defining unit left both fields unmoved far more often than not (gemma4:31b five of seven, gpt-oss:120b five, mistral-large-3:675b six, qwen3.5:397b one, gpt-oss:20b at low five). The same holds of the answer that disagreed with the document: mistral-large-3:675b said the claim "Recursion is not universality" does not follow, on the full document and on both repeats (`ba36cf1ab85e9a8e`, `0bab8e1bbb9c7396`, `61f51fd34b9e6f70`, UDP-05 refuted), and no removal of any of the fifty-eight units, the argument and the five definitions it uses included, moved that answer either. gpt-oss:20b at low said every claim follows and held that through all 290 removals (`0aa2aeb49a86f215`, `ddc6641aa7c5fe71`, `c097b1e7353020ad`, `098efeff38586dc8`, `4aa66067cb8ee987` are its baselines). On these records the models' verdicts on the document's own consequences did not rest on any unit the pattern could name, nor on the document's derivation. What that is consistent with is stated by the loci: the document as sent carries its distinctions in many places, a model may answer from the claim and the general run of the text, and a probe with no key cannot say which.

**The list of essential terms followed the vocabulary left in view.** Removing U31, the unit that defines `Usable`, `Essential`, `Standing` and `Licensed`, dropped `Essential` from every model's list for the claim that uses it: gemma4:31b from `Essential, Usable` to `Usable` (`4f3017e57a71dd21` against `3c9e92c52c753140`), gpt-oss:120b from `Essential, Standing, Usable` to `Standing, Usable` (`b596ab5935b5802e` against `f510caee0b208cca`), mistral-large-3:675b to `Bearing, Usable` (`af3611bee4bebca3` against `88a9e7ced7e17480`), qwen3.5:397b to `Bearing, Standing` (`3143da010a542742` against `63dccffb55157dfa`), gpt-oss:20b at low from `Essential, Usable, Standing` to `Usable` (`f870e9a9d8b794a2` against `ddc6641aa7c5fe71`). Removing U42, which defines `UED`, dropped it from gemma4:31b's list for the finite-record claim (`29b0d8e0cc02805c` against `922cd6692e8ca24d`) and from qwen3.5:397b's (`7b5e510538018f35` against `420a303eb111356d`). Removing U07, which defines `K-RECURSION`, moved nothing for any model on the claim that turns on it: every list that named `K-RECURSION` still named it (`590cf05e2b0eb54f`, `f5805cef56ba2295`, `48ea0a69823afcff`, `2144d35c659c28c5`, `a32d77299cc6153c`). The difference is in the text: `Essential` occurs in the document only inside U31, while `K-RECURSION` is named in its heading, in the claim's own section, and twice more. The term that vanished from the text vanished from the list; the term that stayed in view stayed. A removal test of one unit measures whether the document minus that unit still carries the term, not whether the model's answer needed the definition, and these lists say the models named what they could still see.

**On some probes the list is the floor.** gpt-oss:120b's list for the finite-record claim moved on both repeats (`4cb0f3502f784bc5`, `4fb7088e673500e8` against `4684909c25e442c5`) and on 56 of 56 other-unit removals, taking twenty-one distinct forms; qwen3.5:397b's moved on both repeats (`4db78248261cc3df`, `58bd4e1a5f379046`) and on 42 of 56, in twenty forms. On that probe those two lists are noise, and nothing a removal did to them is readable. gemma4:31b's list for the losing-a-premise claim is the opposite case: a floor of 0 of 2, and 38 of 56 other-unit removals flipped it from `Essential, Usable` to `Essential, Licensed, Standing, Usable` (`51c75db94dc61ad2`, `90f179aae391213a`), the eighteen removals that left it scattered through the document with no pattern the records show. That is the document as sent moving the reply, by position or length or something else, and the record does not say which. gpt-oss:120b added `K-CRITICISM` to an empty list on ten removals of units that name nothing the acyclicity argument uses (`3fbcf5cfbd3160cd`, `67672668602ec6d4`). gpt-oss:20b at low moved its list on 144 of 278 other-unit removals, the most of any run, with a floor of five differing repeats in ten: on the finite-record claim 53 of 56 removals and both repeats moved it (`6ad730149f865e62`, `9589e3930dd4edf3` against `4aa66067cb8ee987`), which is noise; on the provisional-reasoning claim 39 of 57 moved it and neither repeat did (`648f0900be46a6fa` against `098efeff38586dc8`), which is the document as sent again; and one repeat of the losing-a-premise claim named `InScope`, a term the document uses once and the closed list therefore omits (`030edcad379eb2f1`, ENUM_VIOLATION), the one reply in the five runs to leave the vocabulary. Reorders, counted apart, were qwen3.5:397b 12, gpt-oss:20b at low 7, mistral-large-3:675b 7, gpt-oss:120b 4, gemma4:31b 0.

**Where the pattern found no definition, three models named none.** For the acyclicity claim, whose argument uses no formal term, gemma4:31b, gpt-oss:120b and qwen3.5:397b returned an empty list on the full document and on every repeat, and gpt-oss:20b at low on the full document and one repeat (`139ea0e20870864d`, `25f618187f7a3234`, `878dcbac496d7047`, `0aa2aeb49a86f215`; UDP-06 refuted eleven times by these four). mistral-large-3:675b named `Bearing` and `Essential` (`815bf4ff7e09d8d8`), neither of which the acyclicity section mentions; with the section removed, qwen3.5:397b named `K-RECURSION, K-UNIVERSALITY, UED` (`c3de5a7e485ca610`), none of which it mentions either. For the provisional-reasoning claim, also without a declared unit, all four named `K-RECURSION` and almost nothing moved it.

**Transport.** Two mistral-large-3:675b calls came back 503, the model temporarily overloaded, on both attempts (`521e6c859eea1a7f`, `a45c01e5456a89f8`). UDP-07 says a call never times out; its condition says a transport error of any kind, so those two records refute it although neither is a timeout, the same gap between statement and condition H32 recorded for THK-08. The conjecture stands as written and the table shows it refuted; no call from any of the five runs exceeded the 600-second budget, and the longest, gpt-oss:20b's at low, took 215 seconds and 18,180 tokens; six of that run's calls were answered on the retry after the remote end closed the connection (H34).

**What the mechanism did.** It planned 1,450 comparisons from the document alone, with the units, the terms, the probes, and every unit's relation to every probe computed by pattern and recorded on the variant, and it ran them on four models in fifteen minutes with five slots and on the fifth, at the low setting, in two and a half hours. What it found is that on this document these five runs' yes-or-no answers about the document's own consequences did not depend on any unit, and that their named dependencies tracked the vocabulary left in the text. A single-unit removal measures whether the whole document minus that unit still does the work, which is indispensability; it cannot see a contribution that another unit also carries, and a document that names a commitment in four places will not lose it by losing one. The next step the records point to is removal of blocks, all the units defining a term at once, or the argument together with its definitions, which the same machinery can plan.

**Correction of 9 September.** This document said that `dependence`, `claims` and `report` do not read the stopped run's 296 observations because no run record names them. That is true of `dependence` and `report`, which read a directory through its run records, and false of `claims`, which reads every observation in a directory. An external audit of the branch regenerated the table above by the method this document stated, over the committed directory, and got 1,731 observations tested on UDP-01 where the table says 1,450 (`docs/reviews/branch-audit-2026-09-09.md`, finding 1); the difference is the stopped run's observations in scope. The table was generated on 8 September over a directory that held the five complete runs' records and nothing else, and the closing note said it was generated over the committed directory. It now reproduces from the committed directory with the command stated above it, whose summary names the run left out, and `claims` names the observations no supplied run record carries in its summary (`observations_without_run_record`) and at the head of its Markdown. With the 296 included, no status moves: UDP-01 is tested on 1,731 observations and remains unrefuted and not shown able to fail, UDP-07 on 1,821 with the same two refutations, UDP-02's refutations are 27 rather than 22 and UDP-06's 13 rather than 11, UDP-04 is tested on 60 and UDP-05 on 90 with the same refutations, and the models column is the same either way, the stopped run being gpt-oss:20b like the low-setting run the table reads. Register entry H43.

## Redundant, unread, or answered from the claim: the controls

*Written after four runs of the `semantics-unit-controls` pilot: gemma4:31b, nemotron-3-nano:30b, qwen3.5:397b and mistral-large-3:675b, the gpt-oss models set aside at the maintainer's instruction. Records are under `forge/conformance/runs/semantics-unit-controls/`; the conjectures UDC-01 to UDC-08 were committed as `bfef761` before any record existed.*

A removal that moved nothing has three readings, and the controls were generated from the same document to separate them. Each of the five probes was sent with no document, with its own section only, with that section and the units defining the terms it uses, with every other unit carrying a term the argument uses removed at once (one case per term and one for all of them), with the whole vocabulary consistently renamed, and with the claim negated in the preamble. Every control is a case paired with its full-document case; the form's closed list carries both the document's vocabulary and the renamed one. Thirty-nine cases, two repeats each, 117 calls per model, all of them parsed.

| Model | Run | Replies | Tokens, median | Seconds, median | Run label |
|---|---|---|---|---|---|
| gemma4:31b | `1b090546bcc4b143` | 117 | 34 | 0.7 | `REFUTED_CASES_PRESENT` |
| nemotron-3-nano:30b | `4ee005ccf9e58af0` | 117 | 19 | 0.5 | `REFUTED_CASES_PRESENT` |
| qwen3.5:397b | `5c14b2067a6d4fd4` | 117 | 40 | 1.7 | `REFUTED_CASES_PRESENT` |
| mistral-large-3:675b | `4cd4207effbc55fa` | 117 | 38 | 1.7 | `REFUTED_CASES_PRESENT` |

Every run label is the refuted one because repeats differed or a list left the closed vocabulary, as elsewhere; nothing here is scored.

**Controls by kind**, generated by `controls`: each control's baseline reply against the same model's reply on the paired full-document case, an array compared as a set, beside the control's own repeats.

| model | control | pairs | unavailable | unmoved | moved | moved: follows | moved: essential | control repeats moved |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gemma4:31b | block | 6 | 0 | 3 | 3 | 0 | 3 | 0 of 12 |
| gemma4:31b | blockall | 3 | 0 | 1 | 2 | 0 | 2 | 0 of 6 |
| gemma4:31b | negated | 5 | 0 | 4 | 1 | 0 | 1 | 0 of 10 |
| gemma4:31b | nodoc | 5 | 0 | 0 | 5 | 5 | 4 | 0 of 10 |
| gemma4:31b | renamed | 5 | 0 | 1 | 4 | 0 | 4 | 1 of 10 |
| gemma4:31b | self | 5 | 0 | 1 | 4 | 0 | 4 | 2 of 10 |
| gemma4:31b | selfdef | 5 | 0 | 1 | 4 | 0 | 4 | 0 of 10 |
| mistral-large-3:675b | block | 6 | 0 | 4 | 2 | 1 | 1 | 3 of 12 |
| mistral-large-3:675b | blockall | 3 | 0 | 0 | 3 | 1 | 2 | 3 of 6 |
| mistral-large-3:675b | negated | 5 | 0 | 4 | 1 | 1 | 0 | 1 of 10 |
| mistral-large-3:675b | nodoc | 5 | 0 | 0 | 5 | 5 | 5 | 0 of 10 |
| mistral-large-3:675b | renamed | 5 | 0 | 0 | 5 | 0 | 5 | 3 of 10 |
| mistral-large-3:675b | self | 5 | 0 | 0 | 5 | 1 | 5 | 1 of 10 |
| mistral-large-3:675b | selfdef | 5 | 0 | 0 | 5 | 1 | 5 | 5 of 10 |
| nemotron-3-nano:30b | block | 6 | 0 | 6 | 0 | 0 | 0 | 0 of 12 |
| nemotron-3-nano:30b | blockall | 3 | 0 | 3 | 0 | 0 | 0 | 0 of 6 |
| nemotron-3-nano:30b | negated | 5 | 0 | 5 | 0 | 0 | 0 | 0 of 10 |
| nemotron-3-nano:30b | nodoc | 5 | 0 | 4 | 1 | 1 | 0 | 6 of 10 |
| nemotron-3-nano:30b | renamed | 5 | 0 | 5 | 0 | 0 | 0 | 0 of 10 |
| nemotron-3-nano:30b | self | 5 | 0 | 4 | 1 | 1 | 1 | 3 of 10 |
| nemotron-3-nano:30b | selfdef | 5 | 0 | 4 | 1 | 1 | 1 | 2 of 10 |
| qwen3.5:397b | block | 6 | 0 | 0 | 6 | 0 | 6 | 5 of 12 |
| qwen3.5:397b | blockall | 3 | 0 | 0 | 3 | 0 | 3 | 4 of 6 |
| qwen3.5:397b | negated | 5 | 0 | 3 | 2 | 0 | 2 | 1 of 10 |
| qwen3.5:397b | nodoc | 5 | 0 | 0 | 5 | 5 | 4 | 0 of 10 |
| qwen3.5:397b | renamed | 5 | 0 | 1 | 4 | 0 | 4 | 3 of 10 |
| qwen3.5:397b | self | 5 | 0 | 1 | 4 | 0 | 4 | 2 of 10 |
| qwen3.5:397b | selfdef | 5 | 0 | 2 | 3 | 0 | 3 | 2 of 10 |

**The renamed document**, by the vocabulary each reply named (baseline and two repeats of five cases):

| model | replies naming the vocabulary on the page | naming the vocabulary the document no longer contains | naming both | naming nothing |
| --- | --- | --- | --- | --- |
| gemma4:31b | 12 | 0 | 0 | 3 |
| mistral-large-3:675b | 12 | 0 | 3 | 0 |
| nemotron-3-nano:30b | 0 | 0 | 0 | 15 |
| qwen3.5:397b | 12 | 0 | 0 | 3 |

**The negated claim**, whether the verdict followed the negation (a claim said to follow now said not to, or the reverse):

| model | verdict followed the negation | verdict did not follow |
| --- | --- | --- |
| gemma4:31b | 0 | 5 |
| mistral-large-3:675b | 1 | 4 |
| nemotron-3-nano:30b | 0 | 5 |
| qwen3.5:397b | 0 | 5 |

**The conjectures**, generated by `claims` over the four runs:

| Claim | Statement | Status | Refuted by | Standing | Tested on |
|---|---|---|---|---|---|
| `UDC-01` | With no document supplied, a model never says the claim follows. | `UNREFUTED_FOR_DECLARED_SCOPE` | - | condition held on 288 records outside the scope, so the check can fail | 60 observations, 4 models |
| `UDC-02` | With the claim negated, a model never says the negated claim follows. | `REFUTED` | 3 of 4 models, 45 observations; not by nemotron-3-nano:30b | usable; no argued reading | 60 observations, 4 models |
| `UDC-03` | On the renamed document, a model never names a term of the vocabulary the document no longer contains. | `REFUTED` | 1 of 4 models, 3 observations; not by gemma4:31b, nemotron-3-nano:30b, qwen3.5:397b | usable; no argued reading | 60 observations, 4 models |
| `UDC-04` | On the renamed document, a model never says the claim does not follow. | `REFUTED` | 2 of 4 models, 18 observations; not by gemma4:31b, qwen3.5:397b | usable; no argued reading | 60 observations, 4 models |
| `UDC-05` | With every other unit carrying a term the argument uses removed at once, a model never says the claim follows. | `REFUTED` | 3 of 4 models, 22 observations; not by nemotron-3-nano:30b | usable; no argued reading | 36 observations, 4 models |
| `UDC-06` | With only the document's own argument for the claim, a model never says the claim does not follow or is not determined. | `REFUTED` | 1 of 4 models, 12 observations; not by gemma4:31b, mistral-large-3:675b, qwen3.5:397b | usable; no argued reading | 60 observations, 4 models |
| `UDC-07` | On the full document a model never says that a claim the document itself derives does not follow. | `REFUTED` | 2 of 4 models, 18 observations; not by gemma4:31b, qwen3.5:397b | usable; no argued reading | 60 observations, 4 models |
| `UDC-08` | Within a 600-second budget a call never fails by the client's own timeout. | `UNREFUTED_FOR_DECLARED_SCOPE` | - | not shown able to fail on these records | 468 observations, 4 models |

**With no document, nobody said the claim follows.** Every model answered the claim alone with `not_determined` or `does_not_follow` and an empty list, on every probe and every repeat (gemma4:31b `e1b5607a893d1320`, qwen3.5:397b `2e77d37af49cf50b`, mistral-large-3:675b `6ec42ee832abcf54`; UDC-01 survives, shown able to fail by 288 records outside its scope). The `follows` the full document drew was not an answer from the claim alone, so the reading that the document is unread is refuted for three of the four models on this control.

**With any document, three models said the negated claim follows too.** "It is not the case that recursion is not universality", and the four other negations, drew `follows` from gemma4:31b on every case and repeat, from qwen3.5:397b on every one, and from mistral-large-3:675b on four of five (`1bd97a68e39117ed`, `6100284f11a76cb6`, `2b81061b45438040`; UDC-02 refuted 45 times). The one negation that was followed was mistral-large-3:675b's on the recursion claim, which it had said does not follow on the full document and now said follows (`c4f52bd6c7196fb5` against `41cb956839de7885`), the coherent pair. nemotron-3-nano:30b said `does_not_follow` to every claim and every negation alike. So the verdict these models return needs a document to be present and does not read the claim's polarity: it is neither an answer from the claim nor an answer from the document's content, and the loci name what is left, the document as sent, the probe, and the form.

**Removing every other carrier at once moved no verdict either, so redundancy is not why a single removal moved nothing.** With every unit but the argument's own that mentions any term the argument uses removed, ten units for the recursion claim, gemma4:31b, qwen3.5:397b and mistral-large-3:675b said `follows` where they had said it on the full document (`4053a9da4b67c339`, `809b80fcdc7fd927`; UDC-05 refuted 22 times), and nemotron-3-nano:30b said `does_not_follow` as always. The one verdict a block moved was mistral-large-3:675b's on the finite-record claim, to `does_not_follow` with the definition of `UED` and its three other carriers gone (`8318847c47c3bf46`, `23c21400fd8ce414`), and both repeats of those cases moved as well, so that is inside the floor. The lists moved with the blocks as they moved with single removals, following what stayed on the page: gemma4:31b's list for the losing-a-premise claim emptied when the one unit defining its terms went (`05425e29a572ac46`), although the argument's own section still names `Usable`.

**The lists named the vocabulary on the page, and the closed list offered names the page lacked.** On the renamed document, gemma4:31b and qwen3.5:397b named only the renamed vocabulary in every non-empty reply (twelve each; `3da3d4fa5e27db5c`, `236d66f338d8cfe1`), and every verdict stayed where it was; mistral-large-3:675b named the renamed vocabulary in twelve replies and, in three on the acyclicity claim, kept `Bearing` beside `TermDelta`, its renaming (`9335a4b746411acb`; UDC-03 refuted three times), a term the acyclicity section never mentions under either name and which that model had named on the full document too. UDC-04, that renaming never makes a claim not follow, is refuted only by nemotron-3-nano:30b's standing `does_not_follow` and mistral-large-3:675b's on the recursion claim, the same verdicts those models gave the full document, so no verdict moved under renaming. The form's closed list, carrying both vocabularies, did some work of its own: mistral-large-3:675b, sent the acyclicity claim with only its own section, named `TermAlpha`, `TermBeta`, `TermGamma` and `TermDelta` (`c57926f7252c9dc6`, `02b867bb1d681ea1`), names on no page it was sent, and nemotron-3-nano:30b, sent the losing-a-premise claim with its argument and definitions, named twenty-six items of the closed list, the renamed ones included (`4874f5f4fe795642`), and with the argument alone named four words the list does not hold (`c668e18f58390232`, ENUM_VIOLATION). A closed list is a control on the reply's vocabulary and a source of it (H35).

**The argument alone drew the same verdict as the whole document, and the model that disagreed with the document agreed with its argument.** With only the section carrying the claim's own argument, gemma4:31b and qwen3.5:397b said `follows` on every probe (UDC-06 refuted only by nemotron-3-nano:30b, twelve times, whose verdict is `does_not_follow` whatever it is sent); mistral-large-3:675b, which says the recursion claim does not follow from the full document (`41cb956839de7885`, UDC-07 refuted by it three times, as UDP-05 was), said it follows from its own section alone and from that section with its definitions (`7342a18e4092126b`, `fb1874f5c5e07efb`). For that model the rest of the document moved the verdict against the argument, which the unit removals had not found because no single unit carried the objection.

**What the controls separated.** For gemma4:31b, qwen3.5:397b and, on four probes in five, mistral-large-3:675b, the unmoved single removals were not redundancy (the blocks moved nothing), not an answer from the claim alone (no document, no `follows`), and not a reading of the claim (its negation followed too). What remains is a verdict that a document's presence supplies and its content does not move, which is what the loci said an unmoved removal was consistent with and could not choose between. For nemotron-3-nano:30b nothing moved the verdict, the document's presence included; its lists were empty except where the closed list supplied them. The lists, for every model that produced them, followed the vocabulary on the page and the vocabulary on offer.

## What this does not show

- That any unit is redundant in the document, or that any model read it. An unmoved removal is consistent with both.
- That a moved removal is a dependence rather than noise: the floor is the same run's repeats, and a move inside the floor is the model, not the unit.
- Anything about the document's argument being sound. The claim under assessment is the document's own heading; the probe asks whether the model's answer moves, not whether the answer is right.
- That the pattern heuristic found the document's dependencies. Two probes have no declared unit; the table records what the patterns found, and a person can check every row against the text.

*Every id above is a file under `forge/conformance/runs/semantics-unit-dependence/`; the conjectures' table is generated by `claims` over that directory with `--without-run 3bbf9932aab16166` (the stopped run, which has no run record), and the removal tables by `dependence`, which reads the directory through its run records.*
