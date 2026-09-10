# BUILD-TEST-1: reconstruction against relay

A pre-registration. Written and committed before any arm was run.

## Why this test exists, and why it is not the use-test

MINI-USE-TEST-1 scores an arm by how many seeded defects its reproducers recover. That is a
count, and *Explanatory Construction Semantics 2.0* §9.3 says no endorsement, survival or feature
count enters as a warrant. Three blocks of it produced no clean comparison and, more to the
point, could not have answered the question mini was built for even if they had.

ECS 2.0 §6.3 defines an originative act as `Origin ⟺ Attempt ∧ New ∧ Build`. Run mini against
the three conjuncts:

- **Attempt** holds. A mini proposer is directed at a stated question.
- **New** — `¬∃d ∈ R_{<e}(s,h), d ≡_ℓ c` — cannot be established for a language model whose
  repertoire before the event is not inspectable. §6.2: "an incomplete archive makes a historical
  claim uncertain, not new." This is a limit of the substrate, not a defect of mini, and no
  experiment in this repository can remove it.
- **Build** — "an actual owned or controlled subhistory with a nontrivial binding construction,
  **not a composition of content-preserving transfers**" — is testable, and is what this protocol
  tests.

§6.2 gives the discriminating phrase: **"Learner reconstruction counts; relay does not."**

## The primary comparison

Two arms, differing in exactly one thing: what they are shown of the checks under test.

| Arm | Shown | Under §6.2 |
|---|---|---|
| **R** (reconstruct) | the documented rules only — every definition's signature and docstring, no code | must reconstruct what the check does from its description |
| **L** (relay) | the same rules **and** the complete source | may read the answer off the code |

Both are asked the same thing: build a reply text, build a second text differing from it, name
which check to run, and say what **the rule as written** says the check's answer ought to do
between them — `moves` or `unchanged`. A machine then runs the check on both texts and records
what actually happened.

**The prediction that makes this a test rather than a demonstration.** A relay arm predicts what
the code does, because it can see the code; its expectation should almost always match the
machine, and a matching expectation is not a finding. A reconstruction arm predicts what the
rule says; where rule and code have parted company its expectation should *fail*, and that
failure is the finding. So the arm with less information should produce **more** contradictions,
and every contradiction is a candidate place where the harness's documentation and its behaviour
disagree.

If R and L produce the same contradictions at the same rate, reconstruction bought nothing and
the proposer was relaying in both arms. If L produces more, the prediction is refuted outright
and this reading of §6.2 does not apply to these systems.

## What is removed, and why

**The grid is removed.** MINI-USE-TEST-1 handed each proposer one cell of a twenty-cell
enumeration of reply shapes that I wrote. ECS 2.0 §8.3 condition 3: an enabling condition is
admissible for an origination task only if it "does not include a competent replacement thinker
or **a complete functioning solution**". A pre-enumerated answer space is close enough to that
condition to make an origination claim unsafe, and the one finding mini has ever produced (H43)
lay on a cell the grid contained. Removing the grid is therefore not a simplification: it is
what makes a Build attribution admissible at all. Whether removing it also destroys the
proposer's ability to build anything valid is one of the things measured.

**The seal, the mutations and the strata are removed.** Nothing is seeded. The subject is the
harness's own reply-reading functions, unmodified. A contradiction here is a place where this
repository's documentation and this repository's behaviour disagree — which is what the
blind-spot loop was for before the use-test turned it into a defect hunt.

## Measures, fixed before any arm ran (§9.4)

Per arm, per condition, all mechanical:

1. `proposals` — replies that parsed into the required shape
2. `executed` — proposals whose two texts both ran through the named check
3. `contradicted` — executions where the machine's answer differs from the arm's expectation
4. `distinct_behaviours` — distinct `(kernel, answer-before, answer-after)` triples produced
5. `unique_to_arm` — behaviour triples this arm produced that the other arm, on the same model
   and path, did not
6. `reproduces_H43` — whether a contradiction is the known boundary, mechanically identified by
   running the same text against the documented rule's own predicate

None of these is a score and no arm is ranked. Measure 5 is the one that bears on §6.2: content
one arm produced and the other did not.

**A contradiction is not a defect.** It is a candidate. Whether the rule as written really says
otherwise is a reading, and readings are a person's work (§9.3, and this repository's own rule
that a candidate point becomes a kernel row only by a person's reading). This protocol classifies
contradictions into "reproduces H43" and "everything else", and stops there.

## Declared secondary factors

Crossed with the primary comparison, and declared here so that no post-hoc factor can be
introduced later:

- **Path and quantisation.** `api.deepseek.com` serves unquantised weights; `ollama.com` may
  serve quantised ones. `deepseek-v4-pro` is run on both, which makes the pair a quantisation
  comparison at fixed model and fixed prompt.
- **Model.** Several, so that a result on one is not read as a result about language models.
- **Reasoning setting.** On and off, recorded per call, after H4 showed a model's reasoning can
  be the difference between a usable reproducer and none.
- **Grid.** One condition restores the grid, so the §8.3 claim above is measured rather than
  assumed.

## What this cannot settle

`New` is unestablishable here and everywhere in this repository, so **no run under this protocol
can establish `Origin`, and none will be reported as doing so.** At most it can show that the
`Build` conjunct is or is not satisfied in the reconstruction sense §6.2 names.

`CreateEK` (§9.2) additionally requires `Deploy` — the system deploying the originated content in
the repaired state. Mini's permission layer sets `changes: nothing`; it mints no standing by
design. So mini cannot satisfy `CreateEK` whatever this test finds, and the safety property and
the creativity claim are in direct tension. That tension is recorded here, not resolved.

## Amendment 1, before any block ran, after smoke evidence

ECS 2.0 §9.4.3 says a change made after evidence has been examined is a new proposal and must be
defended as one rather than folded in silently. Two changes were made after four smoke calls on
scratch instances and before any block ran. Both are defended here.

**A refused reply is kept verbatim.** The first version recorded only that a reply could not be
read. Mini's own H1 says the record must say what the model actually returned. No measure
changes; a record that could not explain itself now can.

**An enclosing code fence is removed before a reply is read, and the record says it was.** Smoke
calls showed `gemma4:31b` returning a correctly-shaped proposal wrapped in a fence, which the
strict reader refused — mini register M4. Refusing it scores a model's formatting habit, and
this protocol measures construction; a fence around a whole reply is a content-preserving
wrapper and the fields being measured are inside the object, untouched by removing it. Leaving
it in place would have made the cross-model comparison a comparison of output conventions.

The within-arm comparison — R against L on one model — was unaffected either way, since both
arms of a model share its conventions. The change matters only for reading one model beside
another, and `fenced` is recorded per call so a reader can see where it applied.

Neither change dissolves a counterexample: nothing had yet been measured to be dissolved.

---

# Block 1: findings

Sixteen conditions, 192 model calls, eight paired cells, two paths, five models. Records under
`forge/mini/runs/buildtest/block-1/`; the baseline under `forge/mini/runs/buildtest/baseline/`.
Method version 1, pre-registered at `04fc606` with Amendment 1 at `73f8481`, both before any
condition ran.

## The result that decides the question, and it is not the arm comparison

While the block ran I noticed the protocol had no control: nothing measured whether its findings
were reachable without a loop at all. Four direct-audit calls were run outside the block —
`deepseek-v4-pro`, one call each, shown the same rules and the same source, asked outright for a
place where the code does what the docstring does not license. Thirteen minutes.

| Found by four direct-audit calls | Verified | Kernel row |
|---|---|---|
| `refusal_phrase_in` returns the first phrase in **list** order, not the first in the text | yes | none — **new** |
| a fence tagged anything but `json`/`JSON` has its object silently dropped | yes | none — **new** |
| `_span_occurs` answers `verbatim` on a span that is not verbatim | yes | already G-01, G-08 |
| an object nested in a top-level array is recovered | yes | P-05, at the oracle level |

| | calls | new candidates |
|---|---|---|
| BUILD-TEST-1, sixteen conditions | **192** | **1** |
| a direct audit, no loop | **4** | **2** |

The direct audit found the divergence BUILD-TEST-1's reconstruction arm found, stated it more
precisely than either arm did, and found a second one the block never touched — in one
forty-eighth of the calls. This should have been run before the block, not during it, and its
absence was a defect in the protocol rather than a discovery about mini.

The `_FENCE` finding is the sharper of the two: `re.compile(r"```(?:json|JSON)?\s*(.*?)```")`
means a reply that writes ```` ```python ```` around its answer has that answer discarded and an
earlier bare object scored instead. P-01, P-02, P-06 and P-10 all concern fences; none concerns
the tag. Models tag fences routinely.

## The primary comparison: reconstruction against relay

| | arm R (rules only) | arm L (rules and source) |
|---|---|---|
| proposals | 88 | 96 |
| executed | 88 | 96 |
| contradictions | 14 | 10 |
| distinct behaviours | 67 | 61 |
| behaviours unique to the arm | 44 | 38 |

R leads on every total and on none of them decisively. **The lead is carried by one cell.** On
behaviours unique to an arm — the measure §6.2 actually bears on — L wins four cells, R wins
three, one is tied, and R's aggregate lead comes from `mistral-large-3:675b` alone (10 against 2).
On contradictions R wins two cells, L wins one, five are level. Remove mistral and the arms are
indistinguishable.

**The prediction is not refuted and not supported, and it was never diagnostic.** It said the arm
with less information should contradict more, because a relay arm reads the answer off the code
while a reconstruction arm predicts from the rule. The confound was there from the start and I
did not see it when I wrote it: less information also means more misreading, and a misreading
produces a contradiction that looks exactly like a finding. R contradicting more is equally
consistent with R reading worse. The measure does not identify what it was built to identify.

## What a contradiction is worth

The task tells every arm to quote the words it read its expectation from. Of 24 contradictions:

| | arm R | arm L |
|---|---|---|
| quotes words that occur in the docstrings | 4 | 2 |
| quotes something not in the docstrings | 1 | 4 |
| offers no quote at all | **9** | **4** |

Thirteen of 24 cite nothing. Six survive a verbatim-quote filter. Reading those six against the
live code: three exhibit the refusal-ordering divergence, two misread "recovered from prose **or
a fence**" as though prose and fence should differ, and one restates the case-insensitivity
already recorded at R-01.

The three that exhibit the divergence split in a way the counts hide. Arm R aimed at it twice —
`cannot assist or I cannot` against its reversal, on two models and two paths, deliberately
constructed to separate text order from list order. Arm L exhibited it once by accident, while
testing typographic apostrophes, in a text that happened to contain two phrases in the awkward
order. That asymmetry is the only thing in 192 calls that looks like §6.2's distinction, and it
rests on three observations.

## The grid, and what the use-test's low yield was really about

The grid condition restored the enumerated answer space for both arms on one model.

| | contradictions | distinct behaviours | unique | shared between arms |
|---|---|---|---|---|
| grid | 0 and 0 | 9 and 9 | 7 and 7 | 2 |
| no grid | 1 and 1 | 9 and 11 | 3 and 5 | — |

With the grid, **neither arm produced a single contradiction**, while still building twelve valid
pairs each. Handing over the answer space did not stop the proposer constructing; it stopped
anything surprising happening. That is consistent with §8.3 — an enabling condition that supplies
the solution — by a mechanism I had not predicted.

**And a correction to something I said earlier in this work.** I reported that removing the grid
lifted construction from about a quarter of proposals to essentially all of them, and attributed
it to the grid. That is wrong. The grid conditions here also executed 12 of 12. What the use-test
threw three-quarters of its proposals away for was its *cell validator* — the requirement that
the input match an assigned cell and the rewrite be another cell of the same grammar. BUILD-TEST-1
has no such requirement. The low yield was the grammar, not the enumeration.

## Secondary factors

**Reasoning.** On `deepseek-v4-pro:0813`, reasoning on gave arm R twelve distinct behaviours from
twelve proposals — every one different, the widest exploration in the block — and zero
contradictions. Reasoning off gave seven distinct and three contradictions. More reasoning
produced more variety and fewer disagreements, which is what a proposer that reads the rule
correctly should produce.

**Quantisation.** `deepseek-v4-pro` on the vendor path against `deepseek-v4-pro:0813` on
`ollama.com`: 1 contradiction against 3 for arm R, 9 distinct behaviours against 7. The vendor
path contradicted less and explored slightly more. The comparison is confounded — the vendor
path's default reasoning setting is not the Ollama condition's — and no claim is made from it.

**`deepseek-flash` produced zero contradictions on either arm** while producing 11 and 9 distinct
behaviours. Neither finding nor misreading: wide exploration with correct predictions throughout.
On the model that read the rules most accurately, the arm distinction vanished entirely.

## What this block establishes

1. A direct audit of four calls found more new candidate boundaries than 192 calls of the loop.
2. Showing the proposer the source does not change what it finds, on seven of eight cells.
3. A contradiction is not a finding: three-quarters cite no rule, and of those that do, half are
   misreadings.
4. The enumerated grid suppresses contradictions entirely without harming construction.
5. Arm R targeted the one genuine divergence; arm L reached it once by accident. Three
   observations, and the only support in the block for §6.2's distinction.

## What it does not establish

`New` remains unestablishable, so nothing here is `Origin`, and nothing here is `CreateEK` —
`Deploy` is excluded by mini's own `changes: nothing`. The pre-registered prediction was not
diagnostic, so its outcome carries no weight either way. One model family dominates the block.
Both new candidates await a person's reading before they are rows: "the first refusal phrase the
text contains" is genuinely ambiguous between text order and the order of the supplied tuple, and
whether an untagged-fence limitation is a defect or a deliberate narrowness is a decision, not a
measurement.
