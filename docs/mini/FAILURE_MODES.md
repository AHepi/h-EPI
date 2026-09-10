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

## H4 — The same model finishes on one path and never finishes on another

**Found by** three calls with the same brief, the same subject and the same 32,000-token cap,
recorded side by side in `forge/mini/runs/probes/deepseek-api/`. **Status: OPEN**, and the
strongest candidate cause of M17.

| Path | Model | Completion tokens | Of which reasoning | Finished | Content |
|---|---|---|---|---|---|
| `ollama.com` | `deepseek-v4-pro:0813` | **32,000**, exactly the cap | not reported separately | no | **empty** |
| `api.deepseek.com` | `deepseek-flash` | 14,004 | 13,679 | `stop` | a full packet |
| `api.deepseek.com` | `deepseek-v4-pro` | **11,345** | 10,991 | `stop` | a full packet |

The subject is `forge/mini/runs/usetest/v5-s2-2/subject.py` and the brief is arm A's, in all
three. The same model that reaches a natural stop in 11,345 tokens against the vendor's own API
runs to the full 32,000 through `ollama.com` and emits no content at all.

M17 read this as a model that reasons at length inside any affordable cap, and block 3 was
registered on that reading: raise the allowance until the reasoning fits. The reading was wrong,
or at least not the whole of it. The allowance was never the binding constraint — 11,345 was
enough on one path and 32,000 was not enough on another, for one model and one prompt.

What this does **not** establish is the mechanism. Two candidates, and nothing here separates
them: the cap may be applied to reasoning and content together on one path and to content alone
on the other, so that the same generation is truncated in one and not the other; or the serving
configuration may differ, so the model reasons far longer on one path than the other for reasons
that have nothing to do with the cap. Both are consistent with the table and neither is shown.

The consequence for anything already run is stated rather than repaired: **every mini result in
this repository was produced through `ollama.com`**, so a null result on a reasoning model is a
null result on that path, and the arm it belongs to has not been shown to fail anywhere else.

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
