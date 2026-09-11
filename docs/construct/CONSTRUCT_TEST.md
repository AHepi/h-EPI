# CONSTRUCT-TEST-1: does a model's proposal change what the next action does?

A pre-registration. Written and committed before any model was called.

## Why this test, after BUILD-TEST-1

Three blocks of MINI-USE-TEST-1 and one block of BUILD-TEST-1 measured whether a loop *finds*
things, and answered no: a four-call direct audit found more new candidate boundaries than 192
calls of the loop. But all four blocks measured the same kind of thing — the quality of a produced
artifact — and *The Creativity Machine* (11 September 2026) says that is the wrong measure:

> Do not make the core product a transcript in which successive agents describe how thoughtfully
> they have criticized one another.

and

> In every case the effect must occur in the operative state rather than only in a congratulatory
> summary.

Mini cannot satisfy that. Its permission layer sets `changes: nothing` by design, so a proposal it
accepts never reaches anything operative; a person reads the record and acts. That is exactly the
Evidence Report's **no-return control** — retain the correct artifact, do not install it — which
that report reports *failing by construction*. **Mini is architecturally pinned at a control
condition.** This protocol measures the thing mini was built unable to do.

## The measure

One number, and it is not about the proposal: **how many contract violations the controller
commits after the episode**, counted against a reference relation the proposer never sees, over
every case in the finite domain.

At four starts the reference model has **61 reachable states and 98 decision cases**. The deployed
program before any episode is `active`, which commits **34 violations**. A correct program commits
none.

Secondary, recorded and never combined into an average: proposals made, proposals accepted, calls,
completion tokens, wall time, and which obligation each violation breaks — accepting an obsolete
result and missing a current one are separate failures and are reported separately.

## The conditions

| Condition | Proposer | Evidence returned between proposals | Installation |
|---|---|---|---|
| `enumeration` | none — the language, smallest first | — | yes |
| `supplied-solution` | none — the answer is handed over | — | yes |
| `single-shot` | model, asked once | no | yes |
| `repeated` | model, up to the budget | no | yes |
| `evidence-sealed` | model, up to the budget | **yes** | **no** |
| `evidence-install` | model, up to the budget | **yes** | **yes** |

**`evidence-sealed` against `evidence-install` is the experiment.** Same proposer, same brief, same
returned counterexample, same returned rejections, same verifier. They differ in one thing: whether
an accepted tree reaches the operative state. If the violation count falls in one and not the
other, the installation path is doing the work and the transcript is not.

`enumeration` is the number every model condition must beat. It reaches the guard in **eight
proposals**. A model condition that succeeds in fewer has contributed something the host did not
already supply; one that needs more, or fails, has not.

`supplied-solution` shows what the measure looks like when nothing was constructed. A condition
that merely matches it has demonstrated nothing about a proposer.

## The task, and one departure from the Evidence Report

A serialized asynchronous-callback controller, chosen because it is exactly decidable on a finite
domain. Stage one exposes `active` alone, and **every** function of that one bit fails — the class,
not a poor candidate — because two situations expose the same view and require opposite answers.
Stage two admits a typed comparison of the two ticket registers.

The Evidence Report states both that the four-start model holds 46 states and 81 cases and that the
installed guard is `active and current == incoming`. Those are not jointly satisfiable. Deduping
states on `(live, pending)` gives 46 and 81 exactly — but then `current` is the live ticket,
nothing when nothing is live, and a bare `current == incoming` answers every case, so the
conjunction is redundant. Making `current` a register that retains through a cancel makes the
conjunction necessary — fifteen cases separate them — and gives 61 and 98. Holding both requires a
state key that omits `current`, under which eight merged groups contain members exposing
*different* values of `current`, so acceptance would depend on which member the fixed point kept.
This protocol keeps every exposed field in the state's identity and reports 61 and 98. Three tests
pin the discrepancy.

## The controls, and what each would show by failing

- **no-return.** The verified guard, retained and not applied: violations must be unchanged. If
  they fall anyway, something other than installation is changing the controller and the whole
  measure is unsound.
- **corrupted-evaluator.** An evaluator that accepts the constant-false program: an independent
  contract check must still find it missing every current result. An acceptance label is not
  correctness.
- **identity-aliasing.** Ticket identities reused modulo M: the verified guard must start accepting
  obsolete callbacks, because a program is verified against the representation it was checked in.
  The control is **refused as vacuous** when starts do not exceed the modulus, since then no
  identity is reused and nothing is corrupted.

## What is predicted, before the run

- **C1.** `evidence-install` ends with fewer violations than `evidence-sealed`. If not, the
  installation path is not what separates them and the Blueprint's central claim fails here.
- **C2.** `evidence-sealed` ends at exactly 34 — unchanged — however good its proposals are.
- **C3.** At least one model condition reaches zero violations in fewer than eight proposals,
  beating the enumeration baseline on cost. If none does, the model contributed nothing the
  language did not already contain.
- **C4.** `single-shot` does no better than `evidence-install`. Returned evidence should matter or
  the evidence channel is decoration.
- **C5.** Every control holds.

C1 and C2 are near-certain by construction and are registered anyway, because a protocol whose
controls are not predicted in advance cannot be said to have tested them. **C3 is the one that can
surprise.** It is the only prediction here about a model rather than about wiring.

## What this cannot settle

Nothing here establishes `Origin`: `New` is unestablishable for a model whose prior repertoire is
not inspectable, and the guard is a known idiom that is certainly in training data. This measures
whether a proposal **reaches the operative state and changes what the next action does** — the
`Deploy` conjunct — on one task, in one finite domain, with the candidate grammar, the reference
checker, the extension rule and the task all supplied by the experimenter. A more autonomous
system would construct those itself, and that would need its own evidence and its own charged cost.

---

# Block 1: findings

Six models, two paths, four conditions each, plus two non-model conditions and five controls.
Records under `forge/construct/runs/block-1/`. Method version 1, pre-registered at `ff45422`
before any model was called.

## The result

**Five of six models produced a correct, verified guard in the sealed condition, and the controller
still committed all 34 violations.**

| Model | sealed: correct artifact? | sealed: violations | install: violations |
|---|---|---|---|
| deepseek-v4-pro | yes | **34** | **0** |
| deepseek-flash | yes | **34** | **0** |
| deepseek-v4-pro:0813 | yes | **34** | **0** |
| gemma4:31b | yes | **34** | **0** |
| mistral-large-3:675b | yes | **34** | **0** |
| qwen3.5:397b | no | 34 | 34 |

Same proposer, same brief, same returned counterexample, same rejections, same verifier, the same
accepted syntax tree sitting in the record. The two conditions differ in one thing, and that one
thing is the entire difference between a controller that breaks its contract thirty-four times and
one that never breaks it.

A transcript containing a correct, verified, well-argued repair is worth exactly nothing to the
next action. That is not an inference from the Blueprint; it is the measured outcome of running its
own control on five models.

## The predictions

- **C1 — `evidence-install` ends with fewer violations than `evidence-sealed`. Confirmed** on all
  five models where it could be tested, 0 against 34 every time. Vacuous on `qwen3.5:397b`, which
  produced no accepted proposal in either condition, so there was nothing to install or withhold.
- **C2 — `evidence-sealed` ends at exactly 34. Confirmed on all six.** The number never moved,
  including on the five that had the answer in hand.
- **C3 — some model reaches zero in fewer than the baseline's eight proposals. Confirmed, and by a
  wide margin.** `deepseek-flash`, single-shot: one proposal, 162 completion tokens. Enumeration
  needs eight. `mistral-large-3:675b` reached it in one proposal once given the counterexample.
  This is the only prediction here about a model rather than about wiring, and it holds.
- **C4 — single-shot does no better than `evidence-install`. Refuted, in the direction that
  matters.** Single-shot failed on four of six models; on three of those four, the same model given
  the returned counterexample succeeded — `deepseek-v4-pro:0813` and `mistral-large-3:675b` in one
  proposal, `gemma4:31b` in three. For the two models on the vendor path the task was trivial
  either way, so evidence added nothing there. The evidence channel is not decoration for models
  that need it.
- **C5 — every control holds. Confirmed.** No-return: 34 unchanged sealed, 0 installed.
  Corrupted evaluator: accepts the constant-false program, and the independent contract check still
  finds it missing every current result. Identity aliasing: defeats the verified guard at every
  modulus below the start count, and refuses its own vacuous configuration.

## The counter-case, which is not tidied away

`qwen3.5:397b` is the one model where returned evidence **hurt**. Its `repeated` condition — eight
asks, nothing returned between them — found the guard at the seventh proposal and reached zero
violations. Both its evidence conditions exhausted eight proposals and accepted none. Whatever the
counterexample did for three other models, it moved this one away from the answer. One model, one
task; recorded because a protocol that reports only its confirmations is not reporting.

## Cost against the baseline

| | proposals to zero violations | completion tokens |
|---|---|---|
| enumeration (no model) | 8 | 0 |
| `deepseek-flash`, single-shot | **1** | 162 |
| `deepseek-v4-pro:0813`, evidence-install | **1** | 121 |
| `mistral-large-3:675b`, evidence-install | **1** | 121 |
| `qwen3.5:397b`, repeated | 7 | 673 |

Three models beat an exhaustive enumeration of the candidate language by a factor of eight on
proposals. That is a real contribution and a small one: the language has fourteen members, the
extension rule was supplied, and a model that has seen this idiom a million times is not thereby
shown to have constructed it.

## What broke

**Three models proposed an `equal` node whose operands were whole trees rather than field names.**
That is not the registered grammar. The evaluator raised `TypeError` rather than the refusal its
caller handles, so the exception escaped `verify` and ended the condition: `gemma4:31b`,
`qwen3.5:397b` and `mistral-large-3:675b` produced no records at all on the first attempt. Fixed by
refusing a malformed node as a rejected candidate. The grammar was **not** widened to admit the
shape three models independently reached for — that would be a post-hoc change to the registered
language, and the right record is that the brief's grammar is ambiguous to models and the
experiment refused their reading rather than adopting it.

## What this does not establish

Nothing here is `Origin`, and nothing here claims to be. `New` is unestablishable for a model whose
prior repertoire is not inspectable, and `active and current == incoming` is a stock idiom. The
task, the candidate grammar, the extension rule and the reference checker were all supplied by the
experimenter; the models chose among fourteen trees. What is established is narrower and was the
point: **a proposal that does not reach the operative state changes nothing, and the same proposal
that does reach it changes everything measurable here** — on five models, against a reference
relation none of them saw.
