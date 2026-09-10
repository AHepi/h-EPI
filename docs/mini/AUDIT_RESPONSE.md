# The `claude/mini-finish` audit — what I accepted, and why

An audit of this branch was supplied on 2026-09-10, covering the mini package
only. This file records what I did with each finding. It is not the audit; it is
my disposition of it, so a reader can see which findings were accepted, on what
grounds, and which were declined.

**How I checked.** The audit states plainly that it ran copied fragments against
doubles rather than the package, on Python 3.13 rather than 3.12, and that it did
not run the repository's gate. That is the right way to state it, and it means
the findings are claims to be re-derived rather than results to be trusted. I
re-derived each of the six against the real code before touching anything. All
six hold.

| # | Finding | Verdict | Where it is fixed |
|---|---|---|---|
| F1 | An external kind file's format changes leave the run identity unchanged | **Accepted** | `kinds.py`, `ArtifactKind.to_dict` |
| F2 | `commitment_ports` bypass the read-permission preflight | **Accepted** | `runner.py`, `_check_reads` |
| F3 | A retry that succeeds is counted as one call | **Accepted** | `runner.py`, attempt accounting |
| F4 | The live request contradicts the phase it is sent for | **Accepted** | `executor.py`, phase contracts |
| F5 | Attention can be offered work after the verdict | **Accepted** | `runner.py`, `_offered` |
| F6 | A retry's recorded request is not the one that produced the reply, and refused attempts' usage is dropped | **Accepted; smaller remedy** | `runner.py`, attempt record |

## What I re-derived, finding by finding

**F1 holds.** Two kinds identical but for their body format serialise
identically, so an unchanged manifest naming an unchanged path whose kind file
changed only in its rules produces the same header and the same run id. The
manifest digest binds the manifest's own bytes and nothing it loads. This is the
worst of the six: a run's identity is meant to bind what the run *is*, and two
runs accepting different output languages were sharing one.

**F2 holds, and it is mine from an hour earlier.** `_check_reads` walks
`stage.ports`; `render_commitments_brief` walks `kind.commitment_ports`. A
commitment port whose type the policy forbids was rendered anyway. Amendment 3
made the second call's inputs configurable and I did not extend the permission
check to cover them — I added a road and left the gate on the old one.

**F3 holds.** `calls += 1 + (retries if attempt is None else 0)` counts a
success as one invocation however many attempts it took, so the host's budget is
not the budget the operator declared.

**F4 holds, and it explains evidence already on the record.** `LiveResponder`
sent one system instruction and one response schema for every phase. A
commitments call was told by its brief to return commitments only, and by its
schema to return both fields. The first live blind-spot attempt failed twice at
exactly that phase — once on a field of the wrong type, once on something that
was not JSON.

I reported those as a finding about the two-call shape being hard for a model
that sees only prose. **That reading was unfounded and I withdraw it.** The
model was being asked for two contradictory things at once, and the honest
account is that my dispatch was broken, not that the shape is demanding. The
live run has been stopped and will be redone once the contract is coherent;
recording a run made under a request I know to be self-contradictory would be
evidence about a defect wearing the clothes of evidence about the template.

**F5 holds and is worse than reported.** With only the end marker left,
`_offered` returns both the ordinary stage with repeat budget *and the verdict
itself*. My test passed only because the demonstration policy happened not to
choose them — exactly the trap the audit names: a test driven by a well-behaved
policy tests the policy, not the boundary.

**F6 holds; I accept the defect and take a smaller remedy.** The recorded
`request_ref` was the original brief, not the augmented one that produced the
accepted reply, and refused attempts' usage was dropped.

The audit asks for a versioned per-attempt ledger binding phase and attempt
coordinate to the request envelope, the outcome, usage and disposition. I have
not built that. What I have built closes the two concrete holes: the record now
names the request that actually produced the accepted reply, and carries usage
summed across every attempt with a per-attempt breakdown. The `calls` payload
was already free-form, so this needed no record version.

I decline the larger change here because it is a record-format decision with
compatibility consequences, and the audit itself says it is "not a suitable
last-minute addition to an otherwise narrow patch". It stays proposed, in
`SPEC.md` Part three.

## The upgrades beyond the six

**Taken:** the documentation reconciliations. `SPEC.md`'s opening described the
second call as unconditionally body-only, which Amendment 3 had already made
untrue, and `DELIVERY.md` carried a stale mini-suite count. Both corrected.

**Noted and not taken, with reasons:**

- *A recording executor below the adapter, exercising the whole dispatch
  envelope across modes.* This is the right generalisation of F2 and F4, and I
  have written only the specific tests those two findings demand. Worth
  building; not built.
- *Comparison that identifies what differs.* `compare` checks source digests and
  responder identity, which is not equality of conditions. The audit's
  suggestion — declare the intervention, display everything else that moved — is
  better than what is there. Not built.
- *The `MAX_STEPS` boundary.* Whether a legal configuration can exhaust the
  inner loop before its verdict, and whether that should report an incomplete
  cycle rather than a normal one, is untested. Not built.

None of these three is a defect verdict and I have not treated them as one.

## What the audit did not establish, and I am not claiming

The audit ran fragments against doubles. My fixes are re-derived against the
real package and carry ordinary repository tests, but the audit's own
integration recommendations remain undone: no test yet loads a real external
kind file and compiles twice around a format-only edit; no adversarial attention
policy yet chooses every permitted post-verdict opportunity; the repaired live
contract has not been through a real endpoint. Those are named in `SPEC.md`
Part three rather than implied to be finished.

---

# The audit of 10 September 2026 — what I accepted, and why

A second audit was supplied on 2026-09-10 against `974e504`, the revision on
`main` that day. It reads the source, reproduces seven mechanisms with
standalone probes, and inspects one committed execution blob. It states its own
limits plainly: it did not install the package, run the suite, or rerun any
experiment, so its findings are claims to be re-derived. I re-derived all eight
against the real code before touching anything. **Six hold as stated, one is
correct and already registered, one is correct and intentional.**

| # | Finding | Verdict | Where it is answered |
|---|---|---|---|
| F-A | A named cell is not a completed, correctly targeted test | **Accepted** | `report.py`, cells counted three ways |
| F-B | Disagreement is a triage signal, not a defect oracle | **Accepted; already argued** | `AUTONOMY.md`, and the reader now shows agreements |
| F-C | Execution-affecting fields are outside artifact identity and ordinary rendering | **Accepted** | `runner.py`, identity payload and `_artifact_lines`; `common.py`, domain v2 |
| F-D | Evidence previews can omit the clause a reader must interpret | **Correct; registered as M6** | `FAILURE_MODES.md` M6, with the addition below |
| F-E | Run comparison admits confounds and overcompresses its evidence | **Accepted** | `compare.py`, gate wording, both executor kinds, witness rows |
| F-F | Completion accounting has no completed-verdict invariant | **Accepted** | `runner.py`, `steps_exhausted` |
| F-G | Successful calls lose their trace when a later phase fails | **Accepted** | `runner.py`, the drop event carries them |
| F-H | Soft cycle budgets are not hard spend controls | **Correct; intentional and documented** | `SPEC.md` §7; no change |

Each accepted finding has a regression in `tests/mini/test_audit_findings.py`
(`FAudit20260910Tests`) that fails on the behaviour it repairs.

## The executive point, which I accept and have acted on

The audit says the sentence "the control was found by the method, not by the
model" claims a causal separation the runs cannot support, because the grid, the
notation, the presentation, the critic, the cycles and the model varied together.
That is right, and it is exactly the kind of claim this repository exists to
refuse. The sentence is withdrawn in
`forge/mini/manifests/experiments/README.md`; what stands in its place is the
narrower thing the records support — three models, one shape, the same
contradiction, and no ablation. The synthesis's five-point "what the arrangement
has to be" now says in its own words that its five points are readings of runs
that differed in more than one thing, and that the critic, the second commitment
call, the repeated cycles and attention have never been shown to earn their cost
against a simpler arrangement.

The audit's proposed decisive comparison — the same material through
deterministic execution, through one direct rules-reading call, and through the
full loop, with held-out cases and blinded classification — has **not** been run.
It is the right next experiment and this response does not pretend otherwise.

## Finding by finding

**F-A, accepted.** `cells_named` counted a `cell` value in any artifact's fields,
the next-cell seat's own assignment included, and my readings reported that count
as coverage. The counting rule inside `blindspot.cells_named` is right for what it
is for — three seats in one cycle must be handed three different cells — and it
keeps its behaviour, with the reason written where it can be read. What changed is
the reader: `report.RunReading` now carries `cells_assigned`, `cells_attempted` and
`cells_executed` apart, `cells_uncovered` means no execution reached the cell, and
`cells_assigned_not_executed` names the gap. Over the sixteen committed grid runs
the distinction bites in four, and badly in two: `r4-1-skeletons-mistral` handed out
twenty cells and executed one; `r4-6` handed out twenty, attempted nineteen and
executed one. The reading of the day said "twenty cells named" in both cases, which
the audit is right to call a coverage claim it had not earned. The campaign's
`cover-the-grid` rule now fires on that gap, which is what it was for.

The audit's deeper half — that the executor cannot establish that a proposal
implements the cell it was assigned — stands and is **not** repaired here. It
needs a host-owned task record, which is the workbench design the audit proposes;
what exists is the record showing when it went wrong (M12) and now a count that
does not hide it.

**F-B, accepted, and already argued in the same direction.** Disagreement with a
proposer's expectation is triage, not an oracle: a constant-wrong implementation
agreed with by a correct prediction is `rejected`, and an agreement can hide a
violation of an independently stated obligation. `AUTONOMY.md` argues the same
conclusion from the other side and R-04 is the worked instance — a boundary that
came out of an agreement the standing rule had rejected. The reader now shows
agreements and disagreements together so the queue is not the only thing visible.
The standing rule itself is unchanged, because narrowing it further would not make
it an oracle and widening it would make it one falsely.

**F-C, accepted; this one was mine and recent.** The fields form let a kind carry
the input under test in its own optional fields. The artifact identity did not
include them, so two artifacts that would execute differently could share an id;
and `_artifact_lines` rendered body and commitments only, so a critic shown a
proposal was not shown the text the machine would run. Both are repaired: the
identity payload carries the kind's optional fields and the domain is
`creib.mini.artifact.v2` so that ids written under the old payload stay as they
are, and an artifact port renders each optional field on its own line. The audit
is careful to say this is an incomplete identity projection and not a hash
collision, and that the event record did carry `extra`; that is accurate.

**F-D, correct, and registered as M6 since the blind-spot template's first live
run.** The evidence legend folds whitespace and shows 160 characters per block
while reporting the block as exposed, and the citation checker resolves against
the full block, so a quote can verify against text the seat was never shown. The
audit adds the interface mismatch, which M6 did not state, and it is added there.
It also notes correctly that a machine seat emitting a full artifact bypasses the
preview path entirely, which is why the grid and rules seats exist and why the
experiments are not reading 160-character rules.

**F-E, accepted, both halves.** The gate checked source digests and responder id
and the report then announced that both roots were "asked the same way": two runs
with different problems and different instructions passed it. The report now says
what was checked — same sources, same responder — and says whether the two were
compiled from the same manifest, which is a fact the record carries. The ledger
read only `mini.execution.v1`, so every experiment after the third round produced
an empty one; it now reads the pair executor too, and each row carries the input
it was run on and the verdict both sides returned. The heading is
`executed-unchanged ledger` and a row reads "unchanged under … on <input>", since
"is invariant under" generalised a single result into a property.

**F-F, accepted.** The inner loop stopped at `MAX_STEPS` with stages remaining and
said nothing; the outer counter then counted that cycle as completed. A cycle that
runs out of steps now ends the run with `stop_reason: steps_exhausted` and is not
counted among the completed. The audit is right that it did not establish that its
illustrative 513-stage manifest compiles; the regression patches `MAX_STEPS` to 1
instead, which exercises the same invariant without depending on that question.

**F-G, accepted.** In a two-call stage whose commitments phase fails, no artifact
is admitted, and the successful body call's structured record was attached only to
the artifact event that never happened. The drop event now carries the calls made
before the failing phase, so a call that was made, paid for and answered leaves a
record. The audit's wider recommendation — invocation records independent of
artifact admission — is **not** done; it is the deferred per-invocation ledger the
first audit response already records.

**F-H, correct and intentional.** The call budget is checked between cycles, as
`SPEC.md` §7 says. A started cycle can exceed it. The audit says plainly that this
is a documented semantic choice and not a violation, and asks for hard limits for
operational use. Nothing is changed; a hard limit on calls, tokens, time or cost
belongs with the campaign runner rather than the cycle rule, and is not built.

## What I did not take

- **The workbench redesign as a whole.** The audit's target — a machine-owned task
  record with an immutable id, materialised inputs, applicability conditions, and
  separate accounting for assignment, construction, execution and adjudication —
  is a good design and I have not built it. What is here now is the counting that
  stops the conflation (F-A) and the identity and rendering that stop the payload
  being invisible (F-C). The binding of a task to the execution that discharges it
  remains missing, and the register says so.
- **A per-invocation ledger.** Deferred, as before.
- **The decisive comparison.** Not run, as above.
- **Any change to the standing rule.** For the reason in F-B.

## What this audit does not establish, and I am not claiming

It did not run the suite, install the package, or rerun an experiment, and it says
so. It offers no model ranking and this response makes none. The seven probes
demonstrate mechanisms with adapted fragments; the regressions here are the same
claims put to the package, which is the only form in which I would rely on them.
