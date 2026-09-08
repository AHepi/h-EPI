# What a model's reading of a document depends on, found with no key and no manifest

*Written after five complete runs of the `semantics-unit-dependence` pilot: gemma4:31b, gpt-oss:120b, qwen3.5:397b, mistral-large-3:675b, and gpt-oss:20b at the low reasoning setting, each sent the whole semantics document with one of its fifty-eight units removed at a time, for five of the document's own argued consequences; a sixth run, gpt-oss:20b at the pilot's boolean setting, was still in progress when this was written and is read in its own section when its run record exists. Every observation id is a file under `forge/conformance/runs/semantics-unit-dependence/`; the conjectures UDP-01 to UDP-07 were committed as `bcec03b` before any record existed.*

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

Five runs are complete and are read here. The gpt-oss:20b run at the pilot's boolean reasoning setting generated about four thousand tokens a call, thirty-five seconds each, and was on course to take most of a day, so a second gpt-oss:20b run was started beside it with the reasoning setting `low` as a run-time override, recorded in that run record's `endpoint` and nowhere else; the plan and every request but the setting are the same. The low-setting run is the one read below. The boolean-setting run continues, its observations are committed as they are published, and it is read in its own section when its run record exists. Every table is generated by `dependence` and `claims` over the five complete runs.

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

**The conjectures**, generated by `claims` over the five runs:

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

## What this does not show

- That any unit is redundant in the document, or that any model read it. An unmoved removal is consistent with both.
- That a moved removal is a dependence rather than noise: the floor is the same run's repeats, and a move inside the floor is the model, not the unit.
- Anything about the document's argument being sound. The claim under assessment is the document's own heading; the probe asks whether the model's answer moves, not whether the answer is right.
- That the pattern heuristic found the document's dependencies. Two probes have no declared unit; the table records what the patterns found, and a person can check every row against the text.

*Every id above is a file under `forge/conformance/runs/semantics-unit-dependence/`; the conjectures' table is generated by `claims` over that directory with the run records loaded, and the removal tables by `dependence`.*
