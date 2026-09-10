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
