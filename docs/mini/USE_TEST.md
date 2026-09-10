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
