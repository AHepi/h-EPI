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
