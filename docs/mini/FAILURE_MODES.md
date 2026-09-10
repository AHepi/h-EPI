# Mini prototype — what has been observed to go wrong

The register of failure modes the mini prototype has actually produced, each
naming the run root that shows it. Nothing here is inferred from memory: every
entry points at a committed record you can replay.

Two kinds of entry. **M** is a failure mode of the model or of the brief it was
given — something the harness saw and recorded correctly. **H** is a defect in
the harness itself, found by a live run.

Absence is recorded too: a mode not seen on these runs is not a mode that
cannot happen. Two runs of two calls each cannot show what models generally do.

## The runs these entries come from

| Root | Model | Manifest | Calls |
|---|---|---|---|
| `forge/mini/runs/default-gpt-oss-120b/` | gpt-oss:120b | `forge/mini/manifests/default/manifest.json` | 2 |
| `forge/mini/runs/default-glm-5.3-flash/` | glm-5.3-flash | the same | 3 |
| `forge/mini/runs/default-glm-5.3-flash-after-h1/` | glm-5.3-flash | the same | 3 |
| `forge/mini/runs/blind-spot-glm-5.3-flash/` | glm-5.3-flash | `forge/mini/manifests/blind-spot/` | 24 |
| `forge/mini/runs/conformance-blind-spot-gemma4-31b-1/` | gemma4:31b | `forge/mini/manifests/conformance-blind-spot/`, first revision | 16 |
| `forge/mini/runs/conformance-blind-spot-gemma4-31b-2/` | gemma4:31b | the same, input constrained to an instance | 21 |
| `forge/mini/runs/conformance-blind-spot-gemma4-31b-3/` | gemma4:31b | the same, proposal kind single-call | 10 |
| `forge/mini/runs/conformance-blind-spot-gemma4-31b-4/` | gemma4:31b | the same, after Amendment 4 | 10 |

The third root is the same plan and the same model sent again after H1 below was
fixed. It is not a repeat measurement of anything: it exists because the fix
could only be shown to work on a reply that a model actually refused to shape
properly, and the scripted responder cannot produce one that was not written by
hand.

Both ran the same plan: conjecture, then criticism, then end, over one short
supplied source cut into three blocks. Replay either with

```sh
python tools/run_mini.py replay --root forge/mini/runs/<root>
```

---

## M1 — Citations written into the prose instead of the field for them

**Seen on** `forge/mini/runs/default-gpt-oss-120b/`, both artifacts.

Both artifacts recorded **zero citations**, and both were in fact grounded. The
model put its block ids and its quotations inside the body prose, in the form
`[dcd587efbf…] "A team measured a model's replies twice…"`, rather than in the
optional `citations` field the wire schema offered it.

Extracting those prose claims by hand and running them through the same
`check_citations` the record uses verifies **all eleven** — five in the
conjecture, six in the criticism, every one `MINI_CITATION_VERIFIED`. The block
ids are real and the quoted words really occur in those blocks.

**Where the blame lies.** Not with the byte-check, which works, and not
straightforwardly with the model, which grounded its claims correctly and
legibly. With the brief: the instruction offered a field and did not ask for it
in a way this model acted on, and the legend the seat is shown puts the block
ids inside prose it is invited to imitate.

**What it does not show.** That models generally will not use the field. Two
calls cannot show that.

## M2 — The citations field filled with empty citations

**Seen on** `forge/mini/runs/default-glm-5.3-flash/`, the criticism artifact.

The opposite of M1 on the same manifest. This model **did** use the `citations`
field, and returned three entries whose `block` was the empty string. All three
were recorded `MINI_CITATION_UNKNOWN_BLOCK` with the detail "the citation names
no block". Nothing was quoted, so nothing could be checked.

The three real block ids were in the brief, in the legend, at the time.

**Where the blame lies.** Shared, and the record cannot separate the shares. The
wire schema requires `block` and `quote` on each citation entry but does not
constrain them to be non-empty, so an empty pair satisfies the schema the model
was sent. The check behaved correctly and said so three times.

**Seen again** on `forge/mini/runs/default-glm-5.3-flash-after-h1/`, this time
on **both** artifacts, three empty citations each. So this model did it on every
artifact it completed across two runs of the same plan. That is two runs, not a
measurement of a rate.

**Against M1.** Two models, one manifest, two opposite behaviours: one grounded
its claims properly in the wrong place, the other used the right place with
nothing in it. Neither run says which is typical.

## M3 — A conjecture stage produced nothing, and the run went on

**Seen on** `forge/mini/runs/default-glm-5.3-flash/`, events 3 to 5.

The conjecture stage returned a reply that was not readable as JSON, twice — the
first attempt and the retry the failure policy allows. Both were recorded as
`FORMAT_FAILURE` carrying `MINI_SUBMISSION_NOT_JSON`, the submission was
dropped, and the run continued to the criticism stage and ended cleanly at the
end stage.

That is the shipped failure policy doing exactly what it is specified to do —
one retry with the error shown, then drop, then carry on — observed live rather
than only under the scripted responder.

**The consequence, which is worth stating.** The criticism stage then ran with
**no conjectures to criticise** and produced a criticism anyway, of the source
document rather than of any artifact. Nothing in the prototype notices that a
stage's input port was empty; nothing is specified to. Whether an empty input
port should be a recorded condition is an open design question, not a defect
against any requirement.

---

## M4 — A well-formed reply wrapped in a markdown code fence

**Seen on** `forge/mini/runs/default-glm-5.3-flash-after-h1/`, the criticism
stage's first attempt.

This is what M3's "unreadable" replies actually were, and it could only be seen
once H1 was fixed. The reply was **not** malformed. It was valid JSON of exactly
the right shape, wrapped in a markdown code fence:

    ```json
    {
      "body": "This criticism targets conjecture …",
      …
    }
    ```

The reader takes the reply as JSON, the fence is not JSON, and the whole thing
was refused as `MINI_SUBMISSION_NOT_JSON`. The retry, unfenced, was accepted, so
the run produced its artifact and the shipped one-retry default absorbed it.

**Where the blame lies, and the fork this opens.** It is a plumbing question,
not a model question, and it is genuinely open:

- **Strip a fence before reading.** Cheap, and it would have turned two of the
  three refusals across these runs into acceptances. But the harness would then
  be accepting something the model was not asked for, and every later reader of
  the record would have to know that the stored reply and the parsed submission
  can differ.
- **Leave it, and say so in the brief.** The record stays literal — what was
  stored is what was read — and the instruction carries the cost instead.

Nothing has been decided and nothing has been changed: the reader still refuses
a fenced reply. This is an entry in the register, not a fix.

**One more thing this run shows, in passing.** The conjecture stage succeeded
here and failed twice on the run before it, on the same plan and the same model.
Two sends of one request behaved differently. Every comparison anyone later
draws between two of these runs has to be read against that.

---

## H1 — A failing reply was not kept

**Found by** `forge/mini/runs/default-glm-5.3-flash/`, events 3 and 4.
**Status: FIXED**, shown by `forge/mini/runs/default-glm-5.3-flash-after-h1/`.

M3's two format failures record the *reason* a reply was refused and not the
reply. The reply itself is discarded, so the record cannot say what the model
actually returned — only that it was not readable as JSON.

This is a defect in the harness, not in the model. It contradicts the principle
the rest of the design is built on: an accepted submission's body and
commitments are content-addressed blobs kept verbatim, and a refused one should
be no different. A record that keeps only the reasons cannot be re-read later
against a changed check, which is exactly the move the design is meant to
support.

**Consequence on the record as it stands.** For the glm run, what that model
said at the conjecture stage is gone. The evidence that it said something
unreadable survives; the something does not.

**The fix.** Every reply is now stored as a blob before it is read, and the
`FORMAT_FAILURE` event names it in the `body_ref` field the event shape already
carried; a `SUBMISSION_DROPPED` event lists every reply refused for that
submission in `refused_refs`. No new event type, no schema change. Four tests in
`tests/mini/test_failures.py::RefusedRepliesAreKeptTests` hold it, and the run
above shows it live.

**What the fix immediately bought.** M4. The very first refused reply the record
kept turned out not to be malformed at all — it was correct JSON in a markdown
fence. With H1 open, that would have stayed on the record as "not readable as
JSON" and nobody would have known why. This is the whole argument for keeping a
refused reply, made once, by the record, at the first opportunity.


---

## The blind-spot template's first live run

`forge/mini/runs/blind-spot-glm-5.3-flash/`, three cycles, glm-5.3-flash as the
proposers and critic, machine seats for the executor and the verdict. Fifty
events. Eight proposals, three executions, three criticisms, three verdicts, and
**no candidate point and no defect**: every execution came out `unrunnable`.

The run is committed because it is a true record of what happened. What it shows
is three defects of mine and nothing about which of this prototype's checks are
blind.

## M5 — The proposer is asked for registered ids and shown no registry

**Seen on** every proposal of the run; first execution at event 14
(event id 0955d330f7e1b550), last verdict at event 48 (event id 562f12b3d21952ee).
**Status: FIXED on 10 September**, in the shipped template: the registry is a source,
one kernel or transform per paragraph, so the legend shows every id, and the
proposal kind carries an instruction naming it (`DESIGN.md` D7, D8). The
conformance template was built the same way and its proposers named registered
ids in every one of 24 proposals across four runs.

The proposal kind asks for a kernel id, a transform id and an input. The model
returned names like `equals-hello`, `json-number`, `append 'x'`, `lowercase`,
`trim` and `uppercase`. None of these is registered. The executor could run
nothing, and the last verdict reads:

    equals-hello under lowercase unrunnable, not catalogued -> rejected
    equals-hello under uppercase unrunnable, not catalogued -> rejected
    equals-hello under trim      unrunnable, not catalogued -> rejected

**Where the blame lies.** With the manifest, and it is mine. The brief a proposer
is shown contains **no registered id at all** — checked directly against the
stored request bytes: neither `mini.kernel.` nor `mini.transform.` appears
anywhere in it. The template asks a model to name things from a registry it never
shows it. The names the model invented are reasonable guesses at what such a
registry might contain, which is the best anyone could do given the brief.

**What this does not show.** Anything about whether the model could propose good
boundary candidates. It was never given the vocabulary to propose one in.

## M6 — A JSON source cuts to a single block, and the legend hides its content

**Seen at** event 1 (event id 9a6c7ad784dab925), which batches the catalogue into
**one** block. **Status: FIXED by configuration on 10 September**: the catalogue is
written one row per paragraph, so each row is a block the legend shows and the
verdict reads; the cutting rule is untouched and no port type was added
(`DESIGN.md` D7).

The catalogue was supplied as a source precisely so a proposer could see which
pairs are already written down. Evidence is cut at blank lines (a decision, not a
gap — `SPEC.md` Part three). A JSON document has no blank lines, so the whole
catalogue became one block, and the legend renders a block as its first 160
characters. Those characters are the file's `catalogue` and `note` keys. The
points never appeared.

So M5 has a mechanism, and it is not that the manifest forgot to supply the
registry — it supplied it and the rendering swallowed it. The blank-line rule and
the legend excerpt are each defensible alone; together they make a structured
source invisible.

**Two roads, neither taken.** Cut a JSON source by its top-level items rather
than by blank lines, which reopens a settled decision. Or give the template a
port that renders the registry directly, and leave evidence cutting alone. The
second is smaller and does not disturb a decision the operator has made.

## M7 — A string field whose rendered format demands JSON

**Seen at** events 8 and 26 (event ids 447d7dd781dd51a9 and 9e0af2e9ba78127b); six
commitments-phase failures across the run, one submission dropped.
**Status: FIXED on 10 September** as a wording: the rendered format now says a
STRING whose content is JSON text fitting the schema (`DESIGN.md` D9). Whether
commitments may be an object remains the operator's decision.

A submission's `commitments` is a string (assumption A3). The proposal kind's
commitments format is a JSON-schema fragment, so the rendered instruction says
*"must be JSON fitting exactly this schema"*. The model obliged, and returned:

    {"commitments": {"kernel": "equals-'hello'", "transform": "append 'x'", "input": "hello"}}

— an object where a string was required, refused as `MINI_SUBMISSION_FIELD_TYPE`.
Once, at event 24, it dropped the wrapper entirely and returned the triple as the
whole reply, refused as `MINI_SUBMISSION_MISSING_FIELD`.

**Where the blame lies.** With the rendering, and it is mine. A field that holds
a JSON string is described to the seat as though it held JSON. The accurate
instruction is that it must be a *string containing* JSON fitting the schema.
Whether the template should instead admit object-valued commitments is a change
to what an artifact is, and is the operator's to decide, not mine.

## What this run corrects in this register

**M4's fix was real but not sufficient, and my retraction of the earlier reading
was itself too broad.** The audit found that the live request contradicted the
phase it was sent for, and it did; that is fixed. I then said the earlier
commitments-phase failures were explained by it. This run shows a **second**
contradiction underneath the first — M7 — which the fix did not touch, and the
failures continued at the same rate. The honest position is that there were two
contradictions, both mine, one fixed and one open, and that nothing yet shows the
two-call shape itself to be the difficulty.

---

*A note on how event ids are written here.* The repository's citation check
reads any backticked sixteen-hexadecimal run as a conformance record id and
fails when it names no record. A mini event id is sixteen hexadecimal
characters, so they are written plainly above rather than in backticks. That is
a presentation constraint, not a claim about what they are.

---

## The conformance template's live runs

Four runs of `forge/mini/manifests/conformance-blind-spot/` on gemma4:31b, two
cycles each, one per revision of the manifest, under
`forge/mini/runs/conformance-blind-spot-gemma4-31b-1/` to `-4/`. The kernels are
the conformance harness's own functions and the catalogue is drawn from
`docs/kernel.md`; every row is re-derived by a test. The first three runs were
made before Amendment 4 and are the evidence for it; the fourth is after it.
Nothing here is a claim about the model. Every model reply in all four runs was
fenced and read through the fence rule; no run carried a transport failure.

## M8 — The proposer gives a description where an instance is asked for

**Seen on** run 1, every proposal: the input committed was the text
"a bare JSON object" (events 5, 8, 11, 20, 22, 24). **Status: FIXED by
configuration**: the proposal kind's commitments format constrains the input by
pattern to a JSON object or a sentence, and its instruction shows an instance of
each.

The executor ran the kernels on those seven words, so recovery returned
NO_OBJECT before and after every transform and recovery-from-prose returned "no"
both times; three catalogued sensitivities read as `defect` (event 18, cycle 1;
event 30, cycle 2), which is H2 below.

## M9 — A blind commitments call cannot write the instance the body chose

**Seen on** run 2, cycle 1: all three proposals dropped after a retry, six
commitments-phase failures (events 3 to 14); cycle 2's proposals used `{}`
as their input. **Status: FIXED by configuration** (`DESIGN.md` D8): the
proposal kind is `commitment_call: single`.

The proposal's commitments carry the kernel, transform and input its body reasons
about. The second call sees the body alone by default, and the body named the
kernel and the transform but not the instance, so the call could not write it
and wrote prose instead. This is the case for R37 made by the record, and the
reason the two-call default is wrong for a kind whose commitments carry
structured content the body chose.

## M10 — The proposer repeats itself

**Seen on** runs 3 and 4: run 3 proposed one pair four times in six; run 4's three
proposers in cycle 1 committed the same triple three times (events 3, 5, 7) and
two of three in cycle 2 the same again. **Status: OPEN.**

Each proposer stage draws the earlier proposals of the run through the `earlier`
port and is told to prefer a pair the catalogue does not list. At temperature 0
the same brief with one more artifact appended yields the same proposal. Whether
a different seed per stage, an instruction to name a pair no earlier proposal
names, or a format check against the earlier pairs is the right remedy is a
template decision, not a defect against any requirement.

## H2 — The verdict rule compared a proposal with a row without regard to the input

**Found by** run 1, events 18 and 30. **Status: FIXED** (`DESIGN.md` §31).

The catalogue was keyed on the pair alone. A row that says a pair moves is an
example on one input; a proposal on another input that did not move was read as
the catalogue disagreeing with the code, and three of six verdicts in run 1
said `defect` where the catalogue and the code agree. A kernel point in this
repository is keyed on its input, and the rule now reads a row as a point:
an invariance is a claim over the class, a sensitivity is an example. The same
rule now marks an uncatalogued invariance a candidate point for the unchanged
column instead of rejecting it; run 4's second verdict (event 31) is the first
record to carry one for the conformance checks: recovery, and the response
verdict, invariant under trailing prose, which `docs/kernel.md` holds only by
implication.

## H3 — A kind had no instruction field

**Found by** run 1, where the critic proposed instead of criticising, and by the
attempt to fix it: a kind's title is capped at 128 characters, and a role written
as a source on its own tier reached the seat as a 160-character legend line.
**Status: FIXED** (`DESIGN.md` §30): `instruction` on the kind, at the head of
both calls. Run 4's critic criticised in both cycles (events 12 and 27).

## What these runs show, and do not

Run 3 and run 4 each found the same thing: recovery-from-prose moves under
trailing prose, a row the kernel table's P-01 covers in its sentence and the
catalogue omitted, and, in run 4, recovery and the response verdict do not, two
unchanged-column rows the table lacks. Twelve proposals over four runs, most of
them repeats, are not a survey of which conformance checks are blind. What the
record shows is that the loop runs end to end against the harness's own
functions, that its verdict now reads a catalogue as the harness reads a kernel
point, and that a live model can be walked through it without a hand-written
reply.

## The experiments: eighteen runs, three rounds and two addenda

`forge/mini/manifests/experiments/README.md` pre-registers the diagnosis, the
positive control, the criterion and each round's shapes before its runs, and
reads each round after; the records are under `forge/mini/runs/experiments/`.
The entries below are what those runs corrected in mini. What they found in the
harness is in `docs/failure-modes.md` H43 and in `docs/kernel.md` P-09, R-03 and
G-09.

## M11 — A kernel's "cannot read this" was counted as a move

**Seen on** `runs/experiments/round-1/s4-grounding-pairs/` (cycle 3, a line
break written into a document string, read as a move to `UNREADABLE_INPUT` and
then as a candidate point) and `round-1/s5-registry-feedback/` (cycle 1, a
reply that was not a grounding input, unchanged at `UNREADABLE_INPUT` on both
sides and a candidate for the unchanged column). **Status: FIXED** (`SPEC.md`
§22).

A kernel now declares the verdict it gives when it cannot read its input, and
an execution on which either side is that verdict is `unrunnable`. The line
break was the proposer's meaning and is now read as such: a control character
inside a JSON string is admitted by the grounding kernels' reader, strict first,
and nothing else is loosened.

## M12 — The proposer instantiated a described cell the wrong way round

**Seen on** `runs/experiments/round-3/r3-6-grid-enumerated/`, cycle 3: the
machine handed the proposer the cell "a sentence then an object / a different
bare object", meaning a fence holding a sentence and an object, and the
proposer wrote the sentence before the fence. Twenty cells, twenty-one
proposals, none of them the reply the cell described. **Status: FIXED** by
notation, not code: `r3-7-grid-skeletons` writes each cell as `fence[ S A ] B`
with a legend, and the same seat, model and cycles then built every cell as
written (`runs/experiments/round-3/r3-7-grid-skeletons/`). A cell described in
words is an instruction; a cell written in a notation is a shape.

## M13 — A commitments string the model could not escape, repeated at temperature zero

**Seen on** `runs/experiments/round-3/r3-1-invariances-readable/`, cycle 3:
three proposer stages each produced a commitments string that was not readable
as JSON (an unescaped quote at character 119), each twice, and all three were
dropped; and on `round-3/r3-4-sensitivities/`, where five of eight proposals
were dropped for a fenced input the kind's pattern refused. **Status: OPEN.**

The first is M9's neighbour: a JSON instance inside a JSON string inside a JSON
reply is three levels of escaping, and a model that gets it wrong once at
temperature zero gets it wrong on the retry. The second is a template's pattern
written for one shape (a bare object or one sentence) refusing the input the
mirror shape needed. Neither is a defect against a requirement; both cost a
run its proposals, and the records say so.

**The escaping half is now fixed, after round 4 showed its size.**
`runs/experiments/round-4/r4-1-skeletons-mistral/` is the same shape that found
the control, on mistral-large-3:675b: forty-one format failures, twenty drops
and one surviving proposal in seven cycles, every failure the same one — a raw
line break inside the commitments string, where the model should have written
the two characters backslash and n. A reply is now read strictly first and, if
that fails on a control character alone, again admitting it, and the artifact
records `control-characters` beside `fence` and `prose` (`SPEC.md` §17). Nothing
else the strict reader refuses is admitted.

That fix was half a fix, and the next run said so: with the format layer
admitting the break, the machine seat that reads the same commitments string
back still read it strictly and marked two of the run's first three proposals
`unreadable` (`runs/experiments/round-4/r4-6-skeletons-mistral-after-m13/`,
cycle 1, under the intermediate machine). A seat that refuses what the format
accepted spends a call and records nothing, so `_proposal_of` now reads a
commitments string the way the format layer read it. The rule this leaves is
worth stating: wherever mini reads the same text twice, the two readings are the
same reading.

The template half — a pattern written for one shape refusing another — stays
open, and is a manifest's business rather than the machine's.

## M14 — A pair whose two texts differ in more than one thing

**Seen on** `runs/experiments/round-2/e-replies-as-written/`, all three cycles:
asked for a realistic model reply and one edit a model might make, the seat
added a heading, an apology, a label line inside the fence and a stray brace in
the same rewrite, and five of its nine pairs became candidate points that say
nothing about any one change. **Status: OPEN.**

A pair is a probe only if exactly one thing differs between its two texts, and
nothing in the machine can enforce that: any two strings are a legal pair, and
the difference is the proposer's to make. The shapes that worked took the choice
away in a different way (a cell in a notation, with the rewrite named as one
removal), which is a template's answer, not the machine's. A check that
diffed the two texts and refused a pair whose difference is not one part would
be a template decision with a real cost: it would need a notion of "part", which
the machine does not have and should not acquire for one family of manifests.

## What the eighteen runs show, and do not

The control pre-registered in the README (a fence holding a sentence beside its
object, and a bare object after it, scored on the bare object against the
docstring) was found by the last shape of the third round, by a proposer shown the docstring
and not the code, handed the control's cell in a notation, writing the
docstring's expectation, with the machine's answer differing: `r3-7`, events 80
and 146, and again at 168 on two more cells of the same class. The other seventeen runs did
not find it: a proposer that reads the code expects what the code does; a
proposer asked for a disagreement confirms invariances instead; a proposer
that picks its own cell picks the easy ones; a proposer handed a cell in words
builds a different reply. Three smaller points the kernel table lacked were
found earlier and are now rows (P-09, R-03, G-09), and five catalogue rows were
shown to overclaim their class (`round-1/s3-refute-invariances/`). None of this
is a survey of what the harness's checks are blind to, and the loop mints
nothing: every standing above was read by a person before it became a row or
a register entry, as the template says it must be.
