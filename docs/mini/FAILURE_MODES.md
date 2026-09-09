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

## H1 — A failing reply is not kept

**Found by** `forge/mini/runs/default-glm-5.3-flash/`, events 3 and 4.
**Status: OPEN.**

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

**The fix, when it lands.** Store the raw reply as a blob and name it on the
`FORMAT_FAILURE` event, which already carries a `body_ref` field for exactly
this shape. It needs no new event type and no schema change.
