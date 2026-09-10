# MINI-USE-TEST-1: the comparison in which mini may lose

The audit of 10 September said mini's evidence does not show that its full loop beats a simpler
machine-controlled test runner with limited model help, and asked for a decisive comparison. The
operator supplied the protocol. This is what was built, what is being run, and — first, because
it matters most — what this run of it cannot establish.

## What this run cannot establish, stated before any result

**I am the builder and the adjudicator.** The protocol asks for blinded adjudication by an
independent reviewer. That is not available here, so the primary criterion is mechanical
instead of judged: a packet counts as recovering the hidden defect when **its own reproducer,
run through the named kernel, tells the clean subject from the mutated one**. No reading of mine
enters that. Where a reading is unavoidable — was a claim a real boundary, was an ambiguity
correctly identified — it is mine, and it is marked as mine.

**What blinding is enforced, and how it is checkable.** No arm is shown the sealed file, the
clean subject, the mutation, another arm's output, or this repository's history of the defect.
The grid, the validators, the subject and the mutation corpus were frozen and committed
**before** any instance was drawn; the commit order is the evidence, and `frozen.json` carries
the digests. Packets are the same eight fields for every arm, and any word in a packet that
would name the method is reported rather than quietly removed.

**Strata.** The first pass runs S1 (local divergence), S2 (interaction) and S6 (clean control).
S3 would need mutations to mini's own runner rather than to a subject it reads; S4 needs a
genuinely ambiguous contract, which must be written rather than mutated; S5 has no executable
oracle by construction and is a reading test. None of the three is built, and no claim about
them is made either way.

**Instances per block.** The protocol asks for five per stratum. The frozen corpus holds three
mutations for S1 and three for S2, so a block is three instances, not five, and the comparison
is correspondingly weaker. Adding instances means adding mutations, which would have to be
frozen in a new block under the protocol's own rule against editing inside a registered one.

**Models.** Four are available to this session, not five: `gemma4:31b`, `qwen3.5:397b`,
`mistral-large-3:675b`, `nemotron-3-nano:30b`. The Latin square therefore cannot be run as
written. What is run instead: every arm is run on every instance, and the model for arm *a* on
instance *i* is `MODELS[(i + a) mod 4]`, so an arm meets a different model on each instance and
no arm is tied to one model. This removes the arm-by-model confound the rotation is for; it does
not give the balance a full square would.

## The subject

The code under test is a copy of the conformance harness's own reply-reading functions,
generated from their real source with the closure of everything they call
(`usetest.subject_source`). A seeded defect never touches this tree, and the functions are the
ones the harness runs. The copy carries six kernels over those functions — recovery, the prose
flag, the response verdict, the refusal phrase, span occurrence, grounding — each a function of
one text.

The clean subject already contains the defect this repository found in September (`H43`): a
fence holding a sentence beside its object is not read as a fenced candidate. That is a hazard
for the experiment, not a help: an arm may report it instead of the seeded mutation. The
adjudication distinguishes them, since only the seeded mutation makes the clean and mutated
subjects differ.

## The hidden-defect corpus

Six mutations, frozen before any was drawn. Each is a single determinate edit whose reproducer
tells the clean subject from the mutated one, and none of them changes a docstring, so the
defect is never visible in what a rule reader is shown. The three S2 mutations preserve every
one-dimensional behaviour and break a conjunction; the suite asserts both properties.

| id | stratum | kernel | what it breaks |
|---|---|---|---|
| `s1-whitespace-strip` | S1 | span-occurs | the occurrence check stops folding a run of spaces |
| `s1-refusal-last-wins` | S1 | refusal-phrase | the phrase reported is the list's last match, not its first |
| `s1-quotes-not-folded` | S1 | refusal-phrase | a typographic apostrophe is no longer folded |
| `s2-fence-single-only` | S2 | recovery | a fenced object wins only when there is exactly one fence |
| `s2-duplicates-outside-fence-only` | S2 | recovery | a repeated key is resolved last-wins only outside a fence |
| `s2-span-normalised-one-side` | S2 | span-occurs | the document is normalised and the span is not |

## The frozen grammar, and what cannot be enumerated

The recovery family has twenty cells — what a fence holds, by what follows it — written in a
notation, with a validator that compiles each cell to predicates over the concrete text: how
many fenced regions, what each holds line by line, which objects must differ and which must be
the same. **A cell counts as covered only when the validator proves the text that actually ran
satisfies it.** A text that fails is `INVALID_INSTANTIATION`: not a candidate, and not coverage.
The rewrite removes one part, so it lands in a different cell of the same grammar, and the
record says which.

The span and grounding families are marked **non-enumerable**: whether a span stands in a given
relation to a document is the question the kernel exists to answer, so a validator for such a
cell would have to decide it in advance. Mini's arms may not claim systematic coverage there,
and two of the six mutations live there deliberately, which is what makes the decision rule
(`O`, `G`, `R`, `C`) testable rather than assumed.

## The five arms, at one ceiling

Eight model invocations and twelve thousand completion tokens per arm per instance, counted by
the harness rather than asked for in a prompt.

| Arm | What it is given | What it costs per cycle |
|---|---|---|
| A | rules and full source, no execution, one candidate | one call |
| B | rules, full source, and up to six machine-run tests per round, with the answers | one call a round |
| C | rules only, one machine-assigned cell at a time, machine execution with validation | one call |
| D | C plus a critic and the run's own history fed back | two calls |
| E | D with attention on | two calls |

The consequence is pre-registered and is not an accident: at a common ceiling the core walks
seven cells and the full loop about three, because the critic costs a call each cycle. Every arm
ends in one further call that writes the neutral packet, so the packet is not free for anyone.

## Adjudication

`sealed.json` is opened only after every packet is written. For each packet the machine runs its
reproducer through all six kernels against the clean subject and the mutated one and records
which kernels the reproducer separates. Recovering the hidden defect means separating them on
the seeded kernel. On a clean control, any separation is impossible, so a claim there is a
false positive by construction unless it is about the tree's own `H43`, which is recorded
separately as a true boundary.

## The hypotheses, as the protocol states them

H1: the core has its largest advantage in S2. H2: little advantage in S1 if B can read the rule
and run a reproducer. H3: full mini beats the core only where discovery depends on multi-stage
state. H4: attention gets no presumption. H5: turning a semantic question into an arbitrary
executable proxy counts against a method. H6: on a clean control mini must not create more
false-positive burden than the simpler arms.

H3 is not testable in this pass, since S3 is not built. H5 is not testable, since S5 is not
built. Both are recorded as not run rather than as passed.

## Where the records go

`forge/mini/usetest/` holds the freeze: the clean subject, the grid, and `frozen.json` with the
digests of both and of every mutation's edit. Instances and their runs go under
`forge/mini/runs/usetest/`. `tools/mini_usetest.py` is the command line: `freeze`, `draw`,
`run`, `adjudicate`.

---

# The first blocks: S2 on deepseek-v4-pro:0813, and where the machine broke

Three instances, five arms each, one model throughout at the operator's instruction. Running
every arm on one model loses the rotation's protection against a model-by-arm confound but
removes it entirely as an explanation of the differences below: the arms differ, the model does
not. Records under `forge/mini/runs/usetest/`.

## What the arms did

The criterion is mechanical: a packet recovers the hidden defect when **its own reproducer,
run through the seeded kernel, tells the clean subject from the mutated one**.

| Instance | Seeded | A | B | C | D | E |
|---|---|---|---|---|---|---|
| `s2-1` | fenced object wins only with one fence | **found** | no packet | no | no | no |
| `s2-2` | duplicates resolved only outside a fence | **found** | **found** | no | no | no |
| `s2-3` | span normalised on one side only | **found** | no packet | run failed | no | no |

Arm A — the plain audit, given the rules and the full source, one call, no execution — found all
three. Arm B found one and lost two to a ceiling breach described below. The three mini arms
found none, and this was the stratum in which H1 predicted mini's largest advantage.

That is a real result and it should not be softened. It is also not yet a clean test of H1, for
the reason in break 4.

## Where the machine broke

Seven, in the order they were found. Three were in version 1 of this machinery, three more
appeared in version 2, and one is in mini itself.

**1. A fenced packet was thrown away (v1, fixed).** A model that wrapped its JSON answer in a
code fence had written a packet, and `packet_from` refused it, so an arm that had found
something was recorded as silent. Mini strips fences everywhere else; this did not. Any
comparison run under version 1 would have been biased toward whichever arm happened to fence
less.

**2. The shared ceiling is not enforced, and one reply can spend it all (v1 and v2, open).**
The protocol's primary control is a common ceiling. Version 1 let a mini arm spend ten
invocations against an allowance of eight, because mini checks its call budget between cycles
and not after each call (the audit's F-H). Under-setting the budget did not close it: arm E
still reached nine on one instance. Worse, on two instances arm B returned a single reply of
65,536 completion tokens against a 12,000 allowance — five times the ceiling in one call — and
the arm then stopped with no packet at all. **Parity is currently a hope, not a control.** A
hard limit belongs at the call, not between cycles, and this experiment cannot claim resource
parity until it is there.

**3. A cell with one part had no legal rewrite (v1, fixed).** The instruction said to remove one
part; the grid's first cells hold exactly one, and emptying a fence leaves no cell of the
grammar. Every proposal on those cells was thrown away as an invalid instantiation, and the
enumerator hands them out first. The rewrite is now one part added or removed.

**4. Enumeration cannot pay for itself at this ceiling (v2, open, and the deepest one).** Every
mini arm spent its whole budget on the grid's first two to five cells: `fence[ A ]`,
`fence[ A ] S`, and at most three more. The seeded defects live in cells with two fences, or in
the span family that is not enumerable at all. **At eight calls over a twenty-cell grid,
machine-enumerated coverage is not an advantage, it is a tax**: the arm pays a call per cell and
never reaches the cell that matters, while a one-shot reader of the source pays one call and
answers. Holding the ceiling is the protocol's rule and it was held; but H1 predicts an
advantage from systematic coverage, and coverage did not happen, so this block tests the budget
rather than the hypothesis. A block at a ceiling that lets the grid be walked, held equal
across arms, would test H1. That is a new block under a new method version, not an edit to this
one.

**5. The cell under test was the proposal's echo of it (v2, fixed as v3).** The executor
validated against the cell the proposal *said* it was given. One seat copied the whole rendered
port — artifact id, header, "3 of 20 cells named so far" — into that field, and its work was
thrown away for the rendering's fault rather than its own. The assignment is now read from the
assignment artifact and the echo is recorded beside it, which is the audit's F-A repair in
miniature: the host owns the task, and a claim about it is evidence, not authority.

**6. A transport timeout removes an arm from the design (open).** `s2-3` arm C died on a read
timeout inside mini and wrote no packet file, so that cell of the block is simply missing. A
comparison that loses arms to the network silently loses its balance; a failed arm needs a
recorded empty packet with the reason, not an absence.

**7. The concurrency guard over-admits (minor, open).** The launcher counts live runs with a
pattern that does not match how they are launched, so six ran against a cap of five.

## What this does and does not say about mini

It says, on this stratum, at this ceiling, with this grid, on one model: **the plain audit arm
beat all three mini arms, and the strongest simple baseline beat them too.** Nothing in the
mini arms' packets was about the subject's seeded defect; most of them complained about this
experiment's own machinery, which is what breaks 3, 4 and 5 made them do.

It does not say that mini's core has been ablated fairly, because break 4 means the core never
got to enumerate. The honest next step is one further block at a ceiling that admits the grid,
identical for every arm, under method version 3 — and if the core still loses there, the
protocol's conclusion is the one to take.
