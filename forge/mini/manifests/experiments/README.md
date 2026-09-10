# Experiments: can the blind-spot loop find what its authors did not?

Pre-registered before any of these manifests was run. Three rounds of five
concurrent live runs, each run a different shape, the shapes mutated between
rounds on what the records show. The operator's brief: figure out what might be
wrong first, then mutate; if three rounds show nothing, the angle needs a
rethink.

## The diagnosis the shapes test

The four runs of `forge/mini/manifests/conformance-blind-spot/` found only rows
the kernel table already covers by implication. Four things looked wrong:

1. **The transform registry is closed.** A proposer could only name rewrites the
   authors wrote, so the loop could rediscover their rows and nothing else. Pair
   proposals (`mini.pair-proposal.*`) let the proposer write the rewritten input
   itself; the executor runs the kernel on both texts and compares with what the
   proposer expected.
2. **The proposer never saw the check.** It saw one-line descriptions and
   reasoned by analogy with the catalogue. A machine seat
   (`mini.kernel-source.v1`) now emits the kernels' source as an artifact the
   proposer reads whole.
3. **Repetition.** Three stages of one kind at temperature zero produced one
   triple three times. Kinds with distinct targets and instructions, and an
   executor that names a duplicate instead of re-running it.
4. **Only reply-level checks, only a small model.** Grounding kernels over a JSON
   object (value, span, document), and the larger models in some shapes.

## The positive control

The tree these runs execute against carries a known, fixed defect in JSON
recovery: a fence that holds a sentence beside its object is not read as a
fenced candidate, so a bare object after the fence is scored instead of the
fenced one, against the docstring's stated rule (register entry H44 on the
`claude/harness-repeatability-and-grounding-options` branch, not yet on `main`).
A shape that works should be able to find it, or something of its kind, without
being told.

## What "works" means, decided before the runs

A run works when its verdicts hold at least one of:

- a `defect`: a catalogued invariance refuted by an input, or a row's own example
  shown wrong;
- for a pair shape, a pair whose executed outcome differs from the proposer's
  stated expectation, where the expectation was a fair reading of the docstring
  and the pair is not an instance of a row the catalogue already holds;
- for a transform shape, a `candidate point` whose pair is not covered by the
  catalogue or by a sentence in `docs/kernel.md`.

And at least half its proposals must have run: not dropped, not duplicates, not
unrunnable. Whether a candidate is "not covered" is a person's reading, made
after the run and written down with the run; the machine cannot decide it and is
not asked to.

## Round 1

| Shape | Model | What it varies |
|---|---|---|
| `s1-pairs-targeted` | gemma4:31b | pair proposals; three proposer kinds, one per check family; source shown; criticisms fed back |
| `s2-source-adversary` | mistral-large-3:675b | pair proposals; two proposers told to find where code and docstring disagree; source shown; criticisms fed back |
| `s3-refute-invariances` | qwen3.5:397b | registered transforms; proposers told to refute a catalogued "does not move" row with an input of its class; source shown |
| `s4-grounding-pairs` | gemma4:31b | pair proposals on the grounding kernels only; source shown |
| `s5-registry-feedback` | nemotron-3-nano:30b | the previous template with duplicates named, criticisms and executions fed back |

Three cycles each. Records under `forge/mini/runs/experiments/round-1/`.

### Round 1, read

Written when S1, S2 and S4 had ended and S5 was in its last cycle; S3
(qwen3.5:397b) had completed one cycle in an hour and was left to run. The
records are under `forge/mini/runs/experiments/round-1/` when committed, and
the reading of each is with its record.

- **S1** (gemma4:31b, pairs, source shown): nine pairs, nine run, no
  duplicate. Three candidate points, none survives reading: the recovery of a
  list of two objects returns the last object inside the list, which is the
  neighbour of P-05; the span's occurrence is case-sensitive where the value's
  containment is not, which is G-04 beside the containment line; and an input
  that held a second listed refusal phrase, a proposer's slip the critic
  diagnosed. The control was not found. The nearest pair, a fence then a bare
  object with the fence removed, tested the rule where the code follows it.
- **S2** (mistral-large-3:675b, told to find where code and docstring
  disagree): six pairs, five run, one duplicate. All six expected `unchanged`
  and all were unchanged. Asked for a disagreement, the adversary proposed
  invariances it had derived from the code and confirmed them; its criticisms
  ran to seven thousand characters restating the docstring.
- **S4** (gemma4:31b, grounding pairs): nine pairs, nine run. Two candidates,
  neither a point: typographic quotes around the span in the document, which the
  proposer expected to break the occurrence and did not (a substring still
  occurs); and a line break written into the document string, which made the
  JSON unreadable and was recorded as a move to `UNREADABLE_INPUT`. The second
  is an artefact of the input format and is now `unrunnable` (M11).
- **S5** (nemotron-3-nano:30b, the first template with feedback): in two
  cycles three candidates of the kind the table implies (a grounding input the
  kernel could not read, counted as unchanged; the response verdict unchanged
  under folded whitespace; the prose flag unchanged under upper case) and two
  catalogued triples rejected.

None met the criterion. What the records say is wrong:

1. **The expectation came from the code.** A proposer that reads the code
   predicts the code, and can disagree with it only by misreading. The control
   is a place where the rule and the code part; a reader of the code expects
   what the code does and never writes the rule's expectation down. Round 2
   shows most proposers the documented rules alone (`mini.kernel-rules.v1`:
   signatures and docstrings, not one line of code) and asks for the rule's
   expectation.
2. **Asked for a disagreement, the proposer produced confirmations.** The
   instruction "find where they disagree" has no target. Round 2 gives each
   proposer a target it cannot satisfy by confirming: a cell of a grid of reply
   shapes nobody has covered (C), a property someone claimed after reading the
   code (D), a reply written as a model writes one (E), and a second reader
   whose prediction from the code stands beside the expectation from the rule,
   with the machine between them (B).
3. **Two readings can be recorded beside each other.** A `mini.pair-prediction.*`
   artifact commits, for one proposal, what a reader of the code expects; the
   verdict names the pairing (`reading`: both held, expectation failed and
   prediction held, expectation held and prediction failed, both failed). The
   standing is still the proposer's expectation against the machine; a
   prediction names a reading and mints nothing.
4. **Input-format artefacts were counted as moves.** A kernel now declares the
   verdict it gives when it cannot read its input, and a pair or triple on which
   either side is that verdict is `unrunnable` (M11); a control character inside
   a JSON string is read as the line break that was meant.

## Round 2

The criterion is unchanged. For B, the class sought is a verdict whose reading
is "expectation failed, prediction held" or "both failed" on a fair reading of
the rule: the first is the rule and the code parting, the second is the code
doing what neither reader wrote down.

| Shape | Model | What it varies |
|---|---|---|
| `a-rules-first` | gemma4:31b | S1's shape with the rules seat in place of the source; the critic alone sees the code |
| `b-two-readers` | mistral-large-3:675b | rules-only proposers per family, a code-only predictor per proposal, the verdict reads the pairing |
| `c-grid-recovery` | gemma4:31b | recovery only, rules only; each proposal names a cell of the fence, prose, object grid no earlier proposal covered |
| `d-claimed-properties` | qwen3.5:397b | a seat that reads the code claims three properties the rules do not state; rules-only proposers write pairs to refute them |
| `e-replies-as-written` | nemotron-3-nano:30b | rules only; inputs are replies as a model writes them (headings, hedges, quoted drafts, labelled fences), rewrites one edit a model might make |

Three cycles each. Records under `forge/mini/runs/experiments/round-2/`.
