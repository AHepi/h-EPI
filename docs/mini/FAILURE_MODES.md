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

**Added 10 September 2026 (audit F-D).** The mismatch is wider than the excerpt:
the legend reports the block as exposed and the citation checker resolves a quote
against the block's *full* text, so a quote can be verified against words the seat
was never shown, and a citation with no quote can still resolve. The remedy is to
separate preview, full-span exposure and fetched access, and is not built. A
machine seat that emits a full artifact — the rules seat, the source seat, the
grid — bypasses the preview path entirely, which is why the experiments are not
reading 160-character rules.

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

## The experiments: thirty runs, five rounds and three addenda

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

A third run said leniency is not the fix at all.
`runs/experiments/round-4/r4-7-skeletons-mistral-after-m13b/` ran the same shape
on the same model with both readings repaired, and the model still lost every
call: it had written `"input": "```\n{"a": 1}\n```"`, leaving the inner quotes
unescaped as well as the breaks, and no reader should guess where a string ends.
The requirement itself was wrong. A JSON instance inside a JSON string inside a
JSON reply is three levels of escaping; a kind that declares the long fields as
its own optional fields needs one, the same level at which every model already
writes `body`. Those fields are now named in the brief and carried in the live
contract (`SPEC.md` §17), and the blind-spot seats read them over the
commitments. The manifests of round 5 use that form, and the register will say
whether it worked.

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

## M15 — A grid whose cells name differences biases the expectation

**Seen on** `runs/experiments/round-4/r4-4-grounding-grid/`: ten of twenty-one
proposals expected the answer to move, all ten for the same reason, and all ten
were wrong in the same way. The cells were named "span differing from the
document by a run of spaces", "by a line break", "value differing from the span
by case", and a seat handed a cell named after a difference reads the difference
as the point of the cell, although the rules it was shown say those differences
are normalised. **Status: OPEN.**

A cell that names a shape (`fence[ S A ] B`) says what to build and nothing
about what should happen; a cell that names a difference says both. The second
kind is easier to write and produces candidates that are all the same
misreading. What a grid's cells should name is the input's shape, leaving the
expectation entirely to the seat's reading of the rule.

## M16 — The escape sequence written out, in the form that does not need it

**Seen on** `runs/experiments/round-5/r5-2-skeletons-fields-qwen/`: four of five
disagreements in that run came from the seat writing the two characters
backslash and n into its `input` field where a line break belonged, so the reply
it built was one line and the fence it named was not a fence. **Status: OPEN**,
and a template's business.

It is the mirror of M13. Nesting the instance inside a JSON string made models
under-escape, and carrying it in a field of its own makes at least one of them
over-escape, since the habit of escaping outlives the reason for it. Nothing in
the machine should guess which characters a seat meant; an instruction that says
plainly to write real line breaks, not the two characters, is the remedy, and
the record shows the failure either way because the executor stores the text it
ran.

## M17 — A reasoning model's whole allowance spent before any answer began

**Seen on** six probes on scratch instances before MINI-USE-TEST-1 block 2, on
`deepseek-v4-pro:0813`. With the reasoning setting on and a per-call cap of 2,000
completion tokens, every reply was cut off inside its reasoning: three refused
replies reading `MINI_SUBMISSION_NOT_JSON`, no proposals, and the run stopped on
its own reservation. Raising the cap to 8,000 did not help: the model spent about
6,000 tokens a call and still returned nothing parseable, 24,195 completion tokens
for zero proposals. With reasoning off, replies parse at about 250 tokens a call.
**Status: OPEN**, and a property of the pairing rather than of either part.

A per-call cap and a reasoning setting are not independent. A cap chosen so a
ceiling can be walked bounds the answer *and* the reasoning, and a model that
reasons at length inside that budget returns a truncated prefix that is not the
shape anything asked for — so the run pays full price for every call and records
nothing. The cap is not wrong and the reasoning is not wrong; declaring both
without measuring the model between them is. The remedy used was to measure
first and to write the measurement into the block's pre-registration, so the
setting is a stated cost rather than an assumption.

## M18 — The notation handed to a seat written back as the text

**Seen on** four probes on scratch instances before block 2. Handed the cell
`fence[ A ]` and told to build the input from it, the proposer put the four
characters `fence[ A ]` in the input field. Every proposal was
`INVALID_INSTANTIATION` before anything ran, and the arm's packet then reported
the *validator* as the defect — a false positive about the harness, produced by
a machinery fault, at full price. **Status: CLOSED** by a worked example.

The instruction said to build the input from the cell and never showed a cell
built. A description of a rendering is not a rendering, and M8 is the same
failure one level up: a seat asked for an instance gives a description of one.
The remedy is an example of a shape that is **not in the grid** — here
`fence[ S ]` and `fence[ S ] A` — so the seat is shown what building means
without being shown an answer. Notation-copying stopped at once: nought of three
proposals executed became two of six and three of six.

## M19 — The rewrite leaves the grammar the input satisfied

**Seen on** the same probes, after M18 was closed: of six proposals, two to
three built a valid input and a rewritten text that is no cell of the grammar,
so the pair could not be run. **Status: OPEN**, and narrower than M18.

A pair is two texts, and validating one of them is half a validation. The
instruction says the rewrite must itself be a cell and says why a fence holding
one object is changed by adding rather than by emptying, and models still leave
the grammar — most often by removing the part that was the fence's only content.
The record shows it either way, since the executor stores both texts and names
which one failed. It is left open and measured rather than patched inside a
registered block.

## M20 — The neutral packet announces which arm wrote it

**Seen on** every mini arm of MINI-USE-TEST-1 block 2, all three instances:
`forge/mini/runs/usetest/v4-s2-1`, `v4-s2-2`, `v4-s2-3`. **Status: OPEN.**

The protocol ends every arm in the same eight fields with nothing in them that
says which arm or model produced it, so that the adjudication can be blind, and
`Packet.leaks()` exists to check that. Every mini arm leaked on every instance —
the words `kernel`, `cell` and `proposal` — where the two arms that are not mini
leaked once between them across six packets.

The cause is not carelessness in a prompt. A mini arm is walked through a grid of
cells and told which kernel it is testing, so its truthful account of what it did
uses the vocabulary only a mini arm has. Neutrality and a faithful report are in
tension here, and the packet's eight fields ask for both. The leaks are recorded
per packet and the block reported them, so the machinery caught it; what it means
is that a blind adjudication of these packets is not currently possible, and
saying the adjudication was blind would be false.

## H4 — What the two paths actually do, and what the first version of this entry got wrong

**Found by** twenty-two calls with one brief, one subject and one model
(`deepseek-v4-pro`, reasoning on, `num_predict` 32,000 unless stated, temperature 0, seed 7),
recorded in `forge/mini/runs/probes/deepseek-api/`. **Status: OPEN.**

**The first version of this entry was written from one call and overstated its case.** It said
the same model "runs to the full 32,000 through ollama.com and emits no content at all", and
offered a truncating cap as one candidate mechanism. Repeats refuted both parts: the capped call
succeeded on the next attempt and on many after it, and the empty reply has been seen exactly
once in fourteen calls on that path. What follows is what twenty-two calls support.

| Path | How sent | Calls | Returned content | Failed |
|---|---|---|---|---|
| `ollama.com` | one at a time | 6 | 6 | 0 |
| `ollama.com` | five at once | 10 | **4** | **6, all HTTP 500** |
| `api.deepseek.com` | one at a time | 2 | 2 | 0 |
| `api.deepseek.com` | five at once | 5 | **5** | **0** |

**What this supports.** Sent one at a time, both paths answer. Sent five at once, `ollama.com`
returned `HTTP 500 Internal Server Error` on six of ten calls across two batches, and
`api.deepseek.com` returned none on five. DeepSeek's own documentation says a concurrency limit
there yields `429`, and the limit for this model is 500 concurrent connections, so five is not
near it; whatever produces the 500s belongs to the other path.

**What this does not support, and the caution matters.** That earlier runs were affected. Both
five-at-once batches were taken in one window today, and mini blocks 2 and 3 ran for hours at
five concurrent with almost no failed calls — block 2's arm C produced twenty proposals from
twenty cycles. A six-in-ten failure rate is not compatible with that, so the rate is
time-varying and these probes measure the path **now** rather than the path as it was when the
blocks ran. Nothing here licenses reinterpreting an earlier null result as a transport artefact.

**What is not the explanation.** `num_predict` was suspected and is cleared: capped calls
succeeded eleven times. Non-determinism was suspected of being a property of the path and is
cleared: the same request gave eval counts from 4,089 to 12,869 through `ollama.com` and
completion counts from 7,580 to 21,307 through `api.deepseek.com`, so a reasoning model at
temperature 0 with a fixed seed is not reproducible on either. That last fact is the one with
reach beyond this entry, because a repeat of the same bytes is not a repeat of the same
computation, and the repeat floor is read as though it were.

**The one unexplained observation** is the single empty reply, at an eval count of exactly the
cap, in block 3's arm A on `v5-s2-2`. One occurrence in fourteen calls on that path, cause
unknown, recorded rather than explained.

## H5 — The permission layer declares what the machinery does not enforce

**Found by** `forge/construct/runs/mini-can-install/`, which is forty lines and settles a claim
this repository's own documents had wrong. **Status: OPEN.**

`CLAUDE.md` says mini mints no standing and that the permission layer's `changes` is `nothing`,
with any other value refused at compile. The refusal is real: `policy.py` raises
`MINI_POLICY_CHANGE_UNSUPPORTED` on anything else. But that declaration governs what a **seat is
permitted to claim**, and a registered machine seat is arbitrary Python handed the whole record.
Nothing in the policy, the compiler or the runner prevents such a seat from holding an object
outside the record and mutating it.

The demonstration does exactly that. A machine seat reads the cycle's proposal, verifies it by
exhaustive check, and installs it into a controller that lives outside the run. Three cycles, the
policy still reporting `changes = nothing`, and the controller goes from 34 contract violations to
0 and stays there. Mini installed.

**What this corrects.** It had been claimed, in this session and in the CONSTRUCT-TEST
pre-registration, that mini is *architecturally* pinned at the no-return control — unable, by
construction, to let a proposal reach an operative state. That is false, and the error was
conflating a convention of every template written so far with a limit of the machine. Every mini
template in this tree happens to be sealed; none had to be.

**What remains true.** `changes` is compile-refused at anything but `nothing`; every mini run in
this repository to date was sealed; and a cycle must still end in a verdict stage, which the
demonstration satisfies rather than evades.

**Why it is a defect and not a feature.** The installation above took its standing from an
exhaustive verifier, not from a seat's judgement, so it respects what the rule is *for*. The same
mechanism would install on a seat's say-so and nothing would notice. A permission layer that
declares a restriction the machinery does not enforce is a layer that will be believed.

## What the thirty runs show, and do not

The control pre-registered in the README (a fence holding a sentence beside its
object, and a bare object after it, scored on the bare object against the
docstring) was found by the last shape of the third round, by a proposer shown the docstring
and not the code, handed the control's cell in a notation, writing the
docstring's expectation, with the machine's answer differing: `r3-7`, events 80
and 146, and again at 168 on two more cells of the same class. The runs that did not find it failed in ways worth naming: a proposer that reads the code expects what the code does; a
proposer asked for a disagreement confirms invariances instead; a proposer
that picks its own cell picks the easy ones; a proposer handed a cell in words
builds a different reply. Three smaller points the kernel table lacked were
found earlier and are now rows (P-09, R-03, G-09), and five catalogue rows were
shown to overclaim their class (`round-1/s3-refute-invariances/`). None of this
is a survey of what the harness's checks are blind to, and the loop mints
nothing: every standing above was read by a person before it became a row or
a register entry, as the template says it must be.

## M21 — The seat is told a short name for something the machine knows by a long one

ARCH-SWEEP-1's proposer instruction said "Your kernel is one of recovery, recovered-from-prose,
response-verdict, refusal-phrase". The registry knows those checks as `conformance.kernel.recovery`
and its three siblings. A proposal naming the short form parses, reaches the executor, and dies
there with `MINI_KERNEL_UNKNOWN`; the pair is recorded `unrunnable` and produces no behaviour.

**Measured.** Nine architectures landed before the sweep was stopped: 18 proposals, **7 unrunnable
on this cause alone** (39%). Two architectures, `a02` and `a06`, contributed nothing at all; `a05`
lost two of three and `a08` its only one. The loss is not uniform, because whether a seat guesses
the prefix varies by what it was shown — which is exactly the variable the sweep exists to measure.
A machinery break correlated with the treatment is worse than one that is not.

**Why it survived the offline checks.** Nothing offline calls the proposer. `check.py pilots`
validates conformance pilots, not mini manifests; `compile` checks that the manifest is
well-formed, and the instruction is a free string inside a well-formed manifest. The break is only
visible once a model has read the instruction and a machine seat has tried to act on it.

**The repair.** The instruction now writes each id out in full and says that a kernel named without
the prefix does not exist. `forge/mini/runs/arch-sweep/` keeps the nine aborted runs as the record
of the break; the corrected sweep runs into `forge/mini/runs/arch-sweep-2/`.

**What it costs to state generally.** A seat is shown rendered text and answers in free text; the
machine that consumes the answer holds a vocabulary the rendering need not mention. Mini's
`format.commitments` can hold a `json_schema` with a `pattern`, and
`mini.conformance-blind-spot.v1` uses exactly that to require the prefix — so the guard existed and
this manifest did not use it. Adding it here would have turned a lost pair into a retried call,
which is a different number of model calls per architecture, so the repair for this sweep is the
instruction and not the pattern.

## M22 — The machine seat reads the record on a rule of its own, and the declared window is decoration

`_execute_pairs` selected the proposals to run with

```python
and int(context.state.artifacts[key].get("cycle", 0)) == context.cycle
```

Its stage declares a port, that port declares a window, and the seat consulted neither. Every
manifest written before ARCH-SWEEP-1 declared `this_cycle` on that port, so the seat and the
declaration agreed by coincidence and nothing showed.

**What it cost.** ARCH-SWEEP-1 varies the stage order over the 36 architectures of one wiring.
**Eighteen of them — exactly half — place `execute` before `propose`**, which lags that edge; they
declare `window: all` so the second cycle reaches the first cycle's proposals. Under the seat's own
rule they reach nothing, in any cycle, forever. In the aborted attempt `a02`, `a09` and `a10` each
ran all three cycles to `RUN_ENDED` and submitted three execution artifacts holding
`{"executions": []}` apiece, beside proposals the record shows were there.

**Why it is worse than a lost run.** The dead half is not a random half. It is the lagged half —
every architecture at five and six lagged edges is in it. ARCH-SWEEP-1's K3 predicts that distinct
behaviours do *not* fall monotonically as lagged edges increase, because monotone decline would
support the one available argument that the configuration space is useless. A defect that silently
zeroes the most-lagged architectures manufactures exactly that decline. Had the sweep been read as
it stood, the machinery would have produced the evidence for the conclusion, and the conclusion
would have looked measured.

**The repair.** `MachineContext.admits(kind_prefix)` finds the stage's declared port by what its
port type draws — not by port id, which is a manifest's own choice — and returns that port's
window. A stage declaring no such port keeps this cycle, so every earlier manifest is byte-for-byte
unaffected. The boundary is two tests in `tests/mini/test_pairs.py`: the same ordering with
`execute` before `propose`, running the earlier cycle's proposal under `window: all` and nothing at
all under `this_cycle`.

**The general form.** This is H5's shape in a second place. H5 was a permission layer declaring a
restriction the machinery did not enforce; this is a wiring declaring a window the machinery did
not read. Mini's whole claim is that the wiring is declared. Anywhere a seat reaches into
`context.state` and filters it by hand, the declaration is decoration, and only a reader comparing
the manifest against the seat will find it. Found that way here: by a person reading records,
not by the loop.

**The audit the general form deserved.** Asserting that a hand-filtering seat is a latent defect is
cheap; counting them is not. Six sites in `src/creib/forge/mini/` select records from
`context.state` by cycle without consulting a port: `blindspot.py` lines 289, 421, 590 and 621, and
`usetest.py` lines 1042 and 1051. Every manifest in the tree was then checked against them — for
each machine stage whose seat hand-filters, which window does its own declaration name?

**Exactly two declarations in the whole tree name a window their seat does not read, and both are
ARCH-SWEEP-1's**: `execute`/`props` and `verdict`/`execs`, each `window: all`. Every other manifest
declares `this_cycle` on those ports, which is what the seats do anyway — the coincidence that hid
this for the life of the prototype. The `next-cell` and `pair-prediction` seats have no such
declaration anywhere.

`execute`/`props` is the one repaired above; it is the one the sweep's measure runs through.
`verdict`/`execs` is **not** repaired, and the reason is stated rather than implied: the sweep was
already running when the audit was done, the reading takes its rows from the execution artifacts
and never from a verdict, and in this wiring no port draws from `mini.verdict.v1` at all, so the
artifact is terminal and read by nobody. It is inert for this block and it is still a seat ignoring
its declaration. It stays named here, unfixed, rather than folded into a running experiment.

## M23 — The compared arms were not allowed to name the same things

MINI-USE-TEST-1 compares a direct-audit arm against four mini arms on the same drawn instance. The
mini arms' proposal kind carries, at `src/creib/forge/mini/usetest.py:1163`:

> Your kernel is one of recovery, recovered-from-prose, response-verdict.

and, at `:1217`, the same three ids again as a check the runner refuses on:

```python
"kernel": {"type": "string", "pattern": "^(recovery|recovered-from-prose|response-verdict)$"},
```

The subject registers **six** kernels (`usetest.py:203-209`), and `run_kernel` (`:367-376`) runs
any of them on any string. Arm A is handed no kernel list at all.

**What it cost, measured.** `forge/mini/runs/usetest/v4-s2-3/sealed.json` carries
`mutation_id: s2-span-normalised-one-side`, `kernel: span-occurs`, reproducer
`{"span": "five  days", "document": "Amara was away for five days."}`. **The seeded defect of that
instance lives in a kernel the four mini arms are refused from naming.** Counted from the
transcripts of that instance: arm C named `recovery` 19 times and `response-verdict` once, arm
C-rules `recovery` 20 times, arms D and E `recovery` 14 times each. Zero proposals named
`span-occurs`, in any arm, on any instance. Arm A, on the same instance, names the span check six
times.

**Why this is not the coverage finding already recorded.** `USE_TEST.md:83` marks the span and
grounding families non-enumerable, and `:202-207` reports that the arms never walked far enough
into the twenty-cell grid — "machine-enumerated coverage is not an advantage, it is a tax". Both
are about **budget and grid coverage**. Neither says the arms were *refused permission*. The
document nowhere states the three-kernel pattern; a reader of `USE_TEST.md` learns that the grid
does not systematically cover the span family, not that a proposal naming it is a
`MINI_FORMAT_FAILURE` before anything runs.

The two are different defects with different remedies, and the difference matters because
`USE_TEST.md:209-212` proposes the remedy for the one it saw: "A block at a ceiling that lets the
grid be walked, held equal across arms, would test H1." **That remedy does not touch this.** At any
ceiling whatever, arms C, C-rules, D and E cannot name `span-occurs`, so on instance 3 they cannot
state the defect they are being scored on finding while the arm they are compared against can.

**What follows for the block.** "Nought of three, for every arm" (`USE_TEST.md:274`) stands as a
count. It does not stand as a comparison on instance 3, where the arms were not asked the same
question. Two of the six seeded mutations — `s1-whitespace-strip` and
`s2-span-normalised-one-side` — live in the families the pattern excludes. The block is not
withdrawn here, because withdrawing it is a person's decision and because nothing above shows what
the arms would have done with permission; it is marked as carrying an asymmetry its own document
does not disclose.

**The general form.** An arm comparison is only a comparison where the arms may say the same
things. A restriction that lives in a format schema rather than in prose is invisible to everyone
reading the write-up, and this one survived every earlier review of the block.

## M24 — The pre-registration forbade the grid and the instruction contained one

ARCH-SWEEP-1's pre-registration says, in its own words (`docs/mini/ARCH_SWEEP.md:24-26`):

> **No grid.** BUILD-TEST-1 measured an enumerated answer space driving contradictions to zero on
> both arms while construction stayed perfect. Handing one over here would make every architecture
> look alike for a reason that has nothing to do with architecture.

The proposer instruction in `tools/arch_sweep.py:60-67` then said: *"Your kernel is one of recovery,
recovered-from-prose, response-verdict, refusal-phrase."* Four ids. The rules artifact the proposer
reads describes **six** (`kernel_rules_text`), and the registry holds **ten** at runtime
(the six `conformance.kernel.*` plus four `mini.kernel.*`). A repository-wide count finds **69**
single-argument `str`-taking functions under `src/creib/` that a kernel could in principle be.

An enumeration is a grid with the cells written into prose instead of a source file. The
pre-registration refused one and the instruction carried one.

**What it cost.** K1 predicted at least one contradiction quoting the rule and got **zero across 72
runs** — the sweep's 36 and the control's 36 — which is the outcome BUILD-TEST-1's measurement
predicts for an enumerated answer space. The attribution written when the block was read ("a fact
about the brief") is correct and too weak: it is a fact about **the enumeration in** the brief, and
the pre-registration had already said so before the instruction was written.

`r33` of the control proposed `conformance.kernel.span-occurs` — described in the rules artifact,
excluded by the instruction. One proposal in 72 runs left the enumeration, which is evidence the
enumeration was load-bearing rather than redundant.

**WITHDRAWN, 11 September, by OPEN-SWEEP-1.** The paragraph above attributes K1's zero
rule-quoting contradictions to the enumeration. OPEN-SWEEP-1 ran the same architecture 36 times
with the answer space opened from 4 nameable kernels to 66 reachable functions, none of them
listed, everything else held. It produced **one contradiction and zero quoting the rule** — the
closed arm's numbers exactly. The prediction the attribution implied did not occur, so the
attribution is withdrawn: the enumeration is not what suppressed rule-quoting contradictions.

Nothing replaces it. With one contradiction per arm, a quoting *rate* is not a measurement, so the
block cannot separate "the enumeration did not matter" from "contradictions are too rare in either
arm to measure". What stands from M24 is the fact — the pre-registration refused a grid and the
instruction carried one — not the consequence I drew from it. The rest of the entry is left as
written, with this said first, because the error worth keeping visible is that I explained a null
result by the most recent thing I had been shown to have done wrong.

**Not repaired by editing the instruction.** M21's repair wrote the four ids out in full; it did
not widen them to six, or to ten, or to the 69. A block that asks whether a loop finds boundary
points nobody wrote down, while naming the points it may look at, has answered a smaller question
than the one it asked.

## M25 — The seat the tests import is not the seat the command line has

A machine seat exists because a module-level `register_machine_seat` call ran, which happens only
if something imported the module it lives in. `tests/mini/test_openkernels.py` imports
`creib.forge.mini.openkernels` directly, so every offline check passed. `tools/run_mini.py` did not
import it. `check.py all` was green — 776 tests — on a seat the command line could not resolve.

**What it cost.** OPEN-SWEEP-1's first thirty-six runs. Each reached `rules`, `source` and
`propose`, then died at `execute` with

```
MINI_MACHINE_SEAT_UNKNOWN: a stage declares a machine seat for 'mini.pair-execution.open.v1',
which nothing registers
```

**Thirty-six proposer calls were spent**, one per run — 108 artifacts across the 36 logs. It was not
free, and the first report of it in this session said no model calls were made, which was wrong:
the failure is at the fourth stage, not at compile.

**What the spent calls bought, since they exist.** All 36 proposals named a function outside the
four kernels ARCH-SWEEP-1 enumerated, which is the widening being used. Only **two distinct
functions** of the 66 reachable were named — `oracle.recover_json_object` 30 times and
`oracle._grounding_kernel` 6 — and **10 of the 36 dropped the `open:` prefix**, which the registry
would refuse. Both numbers are read from `forge/mini/runs/open-sweep-aborted/`, they are proposals
that were never executed, and they are not O1, O2, O3 or O4, which are read from a block that runs.

**The repair, and why it is not just an import line.** `tools/run_mini.py` now imports
`openkernels`. On its own that fixes this seat and nothing else, so the test added with it asks the
general question: it loads `tools/run_mini.py` as the command line loads it, then checks that every
machine seat named by every shipped manifest under `forge/mini/manifests/` resolves. It fails
without the import line and passes with it.

**The general form.** A test that imports what it is testing proves the thing works when imported.
It proves nothing about whether the program under test imports it. Anywhere behaviour is registered
by import side-effect, the test has to enter through the same door the program does.
