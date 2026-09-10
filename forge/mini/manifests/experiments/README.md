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

### Round 2, read so far

Written when A (twice: the first run was moved aside by mistake and re-run,
so the shape has a repeat), B and C had ended, and D and E were in their
second cycle. S3 of round 1 had ended by then too.

- **S3** (qwen3.5:397b, registered transforms against the catalogue's "does
  not move" rows): nine proposals, nine run, five `defect` standings, the first
  on any run. Two are trivial (a sentence with no object, under a transform
  that adds one). Two refute the fold-whitespace rows with runs of spaces
  inside a string value or a key: the transform reaches inside strings and the
  row's invariance was written over the row's example, not its class. One is
  substantive: the response verdict under upper case on a reply holding a JSON
  literal (`"active": true` becomes `TRUE`, `INVALID_JSON`), which no row
  states. The criterion's first clause is met; what it shows is that the
  catalogue's invariance rows overclaim their class.
- **A** (gemma4:31b, rules only): two runs, nine pairs each, two pairs the same
  between them at temperature zero. One candidate in each run, the same one:
  the value's containment in the span is unchanged under a change of the
  value's case. The rules do not say so, the code folds case, and no row of
  `docs/kernel.md` records it (G-04 is the span's occurrence). The criterion's
  second clause is met, on a small point.
- **B** (mistral-large-3:675b, rules-only proposers, code-only predictors):
  nine pairs, nine run, five candidates. The readings: two "expectation
  failed, prediction held", two "expectation held, prediction failed", three
  "both failed", two "both held". Of the two where the rule's reader was wrong
  and the code's reader right, one is a misreading (an object inside a
  sentence taken for a nested one) and one is a point the table lacks: a
  listed refusal phrase inside a string value of the form itself is found by
  the scan, so a note field reading "I cannot verify this" raises the flag
  (R-02 covers prose around the object, not text inside it). Of the three
  "both failed", all are two misreadings of the same clause (the prose flag is
  set by a fence too; containment is containment). "Both failed" does not
  mean the code does what nobody wrote; it means two readers missed the same
  words. A person's reading stays necessary, as pre-registered.
- **C** (gemma4:31b, the grid): nine cells covered, nine pairs run, all
  expected `unchanged` and all unchanged. The grid reached the control's cell
  (a sentence inside the fence before the object) in cycle 2 but with nothing
  after the fence, where the code and the rule agree; the control needs that
  cell beside a different bare object after the fence, and nine proposals did
  not reach the conjunction.

What this says: the shape that targets a written row (S3) and the shape that
records two readings (B) produce findings; the shape that asks for the rule's
expectation alone (A) produces the same small one twice; the grid gets to the
neighbourhood of the control and stops one dimension short.

## Round 3

Mutations from the round-2 records, pre-registered before the runs:

| Shape | Model | What it varies |
|---|---|---|
| `r3-1-invariances-readable` | gemma4:31b | S3's shape on a second model, with the input required to be one the kernel reads, so a sentence with no object cannot refute a recovery row |
| `r3-2-grid-conjunctions` | gemma4:31b | the grid with two dimensions per cell (what the fence holds, what follows the fence), four cycles; the control's cell is one of twenty and is not named |
| `r3-3-two-readers-four` | gemma4:31b | B's shape on a second model, four cycles |
| `r3-4-sensitivities` | mistral-large-3:675b | the mirror of S3: rows that say the pair moves, and an input of the class on which it does not |
| `r3-5-replies-as-written-four` | gemma4:31b | E's shape on a second model, four cycles |

Records under `forge/mini/runs/experiments/round-3/`. The criterion is
unchanged. The control is found if a verdict on a pair or triple of the
control's shape (a fence holding a sentence and an object, a different bare
object after it) shows the bare object scored.

### Round 3, read so far, and one addendum

Written when r3-1, r3-2, r3-3, r3-4 and r3-5 had ended and E of round 2 was
still in its second cycle on nemotron-3-nano:30b.

- **r3-1** (S3's shape on gemma4:31b): six proposals, five of them the same
  triple, three dropped for a commitments string the model could not escape.
  S3's five defects did not replicate on this model; what S3 found is the
  shape on qwen3.5:397b, and the model is a factor.
- **r3-2** (the grid with two dimensions, four cycles): twelve cells named,
  eleven run, one duplicate, all rejected. The proposer chose "nothing" or "a
  sentence" as the part after the fence nine times in twelve and never put a
  different bare object after a fence that held a sentence: the control's cell
  was again not reached, now one choice short in twelve.
- **r3-3** (two readers on gemma4:31b, four cycles): twelve pairs, ten with
  both readings held. The one candidate is P-01's row (a leading newline does
  not set the prose flag). The one "expectation held, prediction failed" is the
  code's reader wrong about a phrase inside a string value.
- **r3-4** (the mirror of S3 on mistral-large-3:675b): three proposals in
  three cycles, five dropped for a fenced input the pattern refused. Two
  candidates, both the transform applied at its own fixed point (a bare object
  after a reply that already ends in one; upper case on upper case): the
  trivial way to refute a row that says the pair moves.
- **r3-5** (replies as written on gemma4:31b, four cycles): twelve replies
  with headings, hedges and corrected drafts, eleven run, all rejected. Three
  in cycle 4 put a fenced object before a bare "final note" object, the
  control's shape but for the sentence inside the fence, and the rule and the
  code agree there.
- **D** (claimed properties, qwen3.5:397b): nine properties claimed from the
  code, nine pairs written from the rules to refute them, nine survived. Two
  of the claims name the value-case point A found ("casefold provides
  undocumented case-insensitive relaxation").

The grid's proposer picks its own cell and picks the easy ones. The addendum
takes the choice away: `r3-6-grid-enumerated` lists the twenty cells as a
source and a machine seat (`mini.next-cell.v1`, one numbered kind per proposer
stage) names the cell named least often so far; the proposer instantiates the
cell it is given. Seven cycles of three, gemma4:31b, so every cell is named
at least once. This is the one shape whose dimensions were chosen knowing the
control; what it tests is whether a rule-reading proposer, handed the control's
cell, writes the rule's expectation and whether the machine then disagrees.

**r3-6 read.** Seven cycles, twenty-one proposals, every cell named, none
dropped, all rejected. The seat handed the proposer the control's cell in
cycle 3 ("a sentence then an object / a different bare object") and the
proposer wrote the sentence before the fence, not inside it, so the reply it
built was one the rule and the code agree on. The enumeration worked; the
instantiation of "what the fence holds" did not. One more addendum,
`r3-7-grid-skeletons`, writes each cell in a notation that leaves no room
(`fence[ S A ] B`: a fence holding a sentence then object A, and object B
after it), with the same seat, the same seven cycles and the same model. If
the proposer builds that cell as written and writes the rule's expectation,
the machine's answer on it is the control.

**r3-7 read.** Seven cycles, twenty-one proposals, every cell built as
written, none dropped, six candidates. Four are the control and its class: the
cell `fence[ S A ] B` (cycle 3) is the pre-registered control exactly, scored
on the bare `{"b": 2}` where the docstring says the fenced `{"a": 1}`; `fence[
A B ] C`, `fence[ A B ] A` and `fence[ A B ] fence[ C ]` (cycles 6 and 7) show
the same thing for a fence holding two objects. The proposer wrote the
docstring's expectation each time and the machine's answer differed each time.
The other two candidates are P-01's row read wrongly (the prose flag is set by
a fence too). The criterion is met on its first clause's neighbour (a pair
whose outcome differs from a fair reading of the docstring, on the control) and
the control was found without being named.

## What the three rounds show

Eighteen runs, five models, seven shapes and their mutations. What the
records say, in order of what it cost to learn:

1. **The expectation has to come from the rule, not the code.** Every run
   whose proposer read the code (round 1, D) either confirmed the code or
   misread it. The control is a place where the rule and the code part, and
   only a reader of the rule can write the expectation the code fails.
2. **The proposer must not choose the input's shape.** Left to choose, it
   chooses shapes the rule and the code agree on (C, r3-2, r3-5: thirty-three
   proposals in the control's neighbourhood, none on it), or changes several
   things at once so that no pair is a probe (E, M14). Enumerated by
   machine and handed one cell in a notation, it built the control's cell and
   wrote the rule's expectation (r3-7). The machine chooses what to test; the
   model instantiates and reads; the machine executes; a person reads the
   disagreement. That division is the finding about the method.
3. **A written row can be refuted by an input of its class.** S3 refuted five
   catalogue rows on qwen3.5:397b, one of them substantive (P-09); the same
   shape on gemma4:31b repeated one triple and dropped the rest. The model is a
   factor in whether a shape produces anything, and the record says which.
4. **Two readings beside each other separate a misreading from a point.** B's
   readings classed its five candidates; one was a point (R-03), the rest two
   readers missing one clause. The class "both failed" is not "the code does
   what nobody wrote"; a person still reads.
5. **Repeats at temperature zero are not repeats.** A's two runs shared two
   pairs of nine and found the same point (G-09) by different pairs.

What was found: one defect the tree carries (`docs/failure-modes.md` H43),
three rows the kernel table lacked (P-09, R-03, G-09), five catalogue rows that
overclaimed. What was not found: anything about the grounding matcher beyond
its case folding, anything about the refusal list beyond the scan's reach, and
nothing at all by any shape that let the proposer read the code and choose its
own input. The angle does not need a rethink; it needed the choice of what to
test taken away from the model.

**E of round 2, read when it ended.** Nine replies over three cycles on
nemotron-3-nano:30b, nine run, five candidates, none of them a point. The
model did not make one edit: every rewrite added a heading, an apology, a
label line and sometimes a stray brace at once, so a pair says nothing about
any one of them. Two of the five are the control's shape reached by accident,
with the object still recovered because it also stands as a top-level object;
three are the proposer failing to notice that its input was already recovered
from prose. What this run shows is a requirement on the shape rather than on
the check: a pair is only a probe if exactly one thing differs, and a small
model asked for a realistic reply will not hold the rest fixed. The machine
cannot enforce it (any two texts are a legal pair) and the record shows the
cost of not enforcing it.

## Round 4

Pre-registered before its runs. Two questions the third round leaves open: was
the control found by the method or by the model, and does the method carry to
the checks it has never been pointed at.

| Shape | Model | What it varies |
|---|---|---|
| `r4-1-skeletons-mistral` | mistral-large-3:675b | `r3-7` unchanged: the same twenty cells, notation, seat and cycles |
| `r4-2-skeletons-qwen` | qwen3.5:397b | `r3-7` unchanged, on the other large model |
| `r4-3-refusal-grid` | gemma4:31b | sixteen places a listed refusal phrase can stand; the rewrite replaces the phrase with words the list does not hold |
| `r4-4-grounding-grid` | gemma4:31b | five span-to-document relations by four value-to-span relations; the rewrite removes the cell's named differences |
| `r4-5-verdict-grid` | gemma4:31b | seven object shapes by three surroundings; the rewrite replaces the object with a well-formed one |

Each grid is enumerated by `mini.next-cell.v1` as `r3-7`'s was, and every
proposer is shown the rules and not the code. Cycles are set so that every cell
is named at least once (six or seven cycles of three).

**What I expect, written down before the runs, by someone who has read the
code.** This is a prediction to be scored against the records, not a finding.

- The replications reach the control's cell (`fence[ S A ] B`) in cycle 3. If
  either model builds the cell as written and writes the docstring's
  expectation, the disagreement is the same one; if a model builds a different
  reply, that is the instantiation failure M12 again on a larger model.
- In the refusal grid I expect the phrase to be seen wherever it stands, a
  key or a string value of the form included, because the scan reads the whole
  reply. Two cells should part from a plain reading of the rule: a phrase
  broken by a line break, which the scan does not normalise and so does not
  see, and a reply holding two listed phrases where the one standing later in
  the text is earlier in the list, since the answer is the list's first match
  and not the text's.
- In the grounding grid I expect the four span relations the table already
  covers to behave as G-01 and G-04 say, and nothing new; the value-case cell
  is G-09, added this week from round 2.
- In the verdict grid I expect one cell the table lacks: a bare object with a
  repeated key and no prose or fence around it is not read by the strict
  parser, is recovered, and is reported as recovered from prose, although
  there is no prose. P-01 states the flag moves under prose or a fence and
  says nothing about a repeated key.

The criterion for "works" is the one pre-registered above and unchanged.
Records under `forge/mini/runs/experiments/round-4/`.

**Round 4, addendum, pre-registered.** `r4-1-skeletons-mistral` lost
forty-one of forty-two calls to one escaping failure and so tested nothing;
the machine now reads a raw line break inside a reply's JSON as the line break
meant and records that it did (`docs/mini/FAILURE_MODES.md` M13,
`docs/mini/SPEC.md` §17). The same manifest, model, seat and cycles are run
again under the fix as `r4-6-skeletons-mistral-after-m13`, so the replication
question the round was asked to settle can be answered. Its first record stays
in the tree as the evidence for M13.

That re-run started under an intermediate machine, where the format layer
admitted the line break and the executor seat still refused it, and its record
is kept as the evidence for the second half of M13. The clean replication is
`r4-7-skeletons-mistral-after-m13b`, the same manifest, model, seat and cycles
again, with both readings the same reading.

### Round 4, read: the three new families

Written when the refusal, grounding and verdict grids had ended and the two
replications were still running.

- **`r4-3-refusal-grid`** (gemma4:31b): sixteen cells, eighteen proposals,
  fifteen moved, one unchanged, two duplicates, one candidate. The candidate is
  the proposer expecting an upper-case phrase not to count, which R-01 already
  says it does: a misreading, not a point. Everything else agreed. The row that
  came out of this run came out of an **agreement**: the cell that put a line
  break inside the phrase recorded `NONE` on both sides, meaning the scan never
  saw the phrase, and the proposer had read the rule the same way. The standing
  rule called it `rejected` and the candidate list does not hold it; it is in
  the record's own `before` and `after` values, and it is now `docs/kernel.md`
  R-04. The grid also showed the phrase is seen in a string value, in a key, and
  inside a fence, which is R-03's neighbourhood.
- **`r4-4-grounding-grid`** (gemma4:31b): twenty cells, twenty-one proposals,
  none dropped, ten candidates and no point. All ten are the same two rows the
  table already holds — the span check normalises whitespace (G-01) and the
  containment check folds case (G-09) — expected to matter by a proposer that
  had both rules in front of it. The cause is in the grid, not the model: a cell
  named "span differing from the document by a run of spaces" tells the seat the
  difference is the point of the cell, and it wrote `moves` ten times for that
  reason. A grid whose cells name differences biases the expectation toward
  `moves` (register M15).
- **`r4-5-verdict-grid`** (gemma4:31b): twenty-one cells, twenty-one proposals,
  three candidates and no point. One is the proposer choosing the recovery
  kernel, whose answer is the recovered object itself, so replacing the object
  necessarily moves it; two are an object holding a float, which is recovered by
  nothing and so is not "recovered from prose" however much prose surrounds it,
  which P-07 and P-01 hold between them.

So on three families never probed before, the loop's own standing rule produced
fourteen candidates and no point. The two rows this round added came from
somewhere else: R-04 from reading a record the rule had rejected, and P-10 from
the prediction written into this file before the runs, which no run tested
because the proposer handed that cell chose a different kernel. Both were
verified by evaluation before they were written, and both say so.

That is the round's finding, and it is about the method rather than the checks:
**a pair shape can only surface a disagreement, so a boundary both readers get
right stays invisible, and a person reading the record finds what the standing
rule cannot.** The transform-and-catalogue shape (`s3-refute-invariances`) does
not have this blind spot, because it sets an execution against a written row
rather than against a reader; it has the opposite one, that it can only test
rows someone already wrote. The two shapes are complements, and a round that
runs only one of them will miss what the other sees.

### Round 4, read: the replications, and the answer to the round's question

- **`r4-2-skeletons-qwen`** (qwen3.5:397b): twenty cells, twenty-one proposals,
  none dropped, two disagreements. One is the control, at the control's own
  cell: `fence[ S A ] B` in cycle 3, a fence holding a sentence and one object
  with a bare second object after it, scored on the bare one where the docstring
  says the fenced one; the proposer expected removing the bare object to change
  nothing, and it changed the answer. The other is P-01 misread.
- **`r4-6-skeletons-mistral-after-m13`** (mistral-large-3:675b, the
  intermediate machine): twenty proposals reached the executor and nineteen were
  named `unreadable`, because the format layer admitted the raw line break and
  the seat that read the string back did not. Evidence for the second half of
  M13 and for nothing else.
- **`r4-7-skeletons-mistral-after-m13b`** (mistral-large-3:675b, both readings
  repaired): eleven drops and twenty-nine format failures still, ten proposals
  through, four disagreements. Three are the control's class: `fence[ A S ] B`,
  `fence[ A B ] C` and `fence[ A B ] A`, each scored on the bare object after
  the fence where the docstring says the fenced one.

**The round's question is answered: the control was found by the method, not by
the model.** Three models, gemma4:31b, qwen3.5:397b and mistral-large-3:675b,
each shown the docstring and not the code, each handed the cells of the same
enumerated grid in the same notation, each wrote the docstring's expectation and
each was contradicted by the machine on the same class of reply. That is the
strongest thing in this file, and it is a claim about a way of arranging seats,
not about any model.

What it cost to get there is the round's other finding. Mistral lost forty-one
of forty-two calls in `r4-1`, nineteen of twenty executions in `r4-6`, and
eleven more proposals in `r4-7`, all to the requirement that a JSON instance be
written inside a JSON string inside a JSON reply. The machine now offers a
kind's own optional fields for exactly this (`docs/mini/SPEC.md` §17, register
M13), and round 5 is these grids written that way.
