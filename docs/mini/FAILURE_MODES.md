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
(`0955d330f7e1b550`), last verdict at event 48 (`562f12b3d21952ee`).
**Status: OPEN.**

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

**Seen at** event 1 (`9a6c7ad784dab925`), which batches the catalogue into
**one** block. **Status: OPEN, and it is the sharp edge of a decision.**

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

**Seen at** events 8 (`447d7dd781dd51a9`) and 26 (`9e0af2e9ba78127b`); six
commitments-phase failures across the run, one submission dropped.
**Status: OPEN.**

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
