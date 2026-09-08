# What a model's reading of a document depends on, found with no key and no manifest

*Written after five runs of the `semantics-unit-dependence` pilot: gpt-oss:20b, gemma4:31b, gpt-oss:120b, qwen3.5:397b and mistral-large-3:675b, each sent the whole semantics document with one of its fifty-eight units removed at a time, for five of the document's own argued consequences. Every observation id is a file under `forge/conformance/runs/semantics-unit-dependence/`; the conjectures UDP-01 to UDP-07 were committed as `bcec03b` before any record existed. The results section is filled in below the design.*

## The question

Every earlier pilot in this repository compiled a semantics into numbered instruction sentences and an answer key by hand, and varied one sentence at a time. That is a manifest. A large model auditing a document does not need one: it reads the document, finds the definitions the argument rests on, and asks what happens without them. The question this pilot puts is whether that behaviour has a mechanical form the harness can run on weaker models, with nothing declared and nothing scored.

## The mechanism

The document is split into units at its own markdown headings, at the levels the pilot names (here 2 and 3). There are fifty-eight. For each probe, every unit is removed once, with every other line byte-identical, and the model is asked the same two questions it was asked on the full document: does the claim under assessment follow from the document as written (`follows`, `does_not_follow`, `not_determined`), and which of the document's named commitments and defined terms does it depend on (`essential`, a list drawn from a closed vocabulary). The reply is compared field by field with the same model's reply on the full document, and that comparison is the whole result: moved, unmoved, or unavailable when one of the two replies was not a form. No key exists. Both fields carry the `unknown` oracle, every field verdict is `NOT_SCORED`, and the run label is the no-scored-output one on every run.

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

The five runs are in progress at the time of this commit; the records are committed with the results when every job has written its run record, and this section is filled from `dependence` and `claims` over that directory, never from memory.

## What this does not show

- That any unit is redundant in the document, or that any model read it. An unmoved removal is consistent with both.
- That a moved removal is a dependence rather than noise: the floor is the same run's repeats, and a move inside the floor is the model, not the unit.
- Anything about the document's argument being sound. The claim under assessment is the document's own heading; the probe asks whether the model's answer moves, not whether the answer is right.
- That the pattern heuristic found the document's dependencies. Two probes have no declared unit; the table records what the patterns found, and a person can check every row against the text.

*Every id above is a file under `forge/conformance/runs/semantics-unit-dependence/`; the conjectures' table is generated by `claims` over that directory with the run records loaded, and the removal tables by `dependence`.*
