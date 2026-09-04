# Generic hardening protocol v1

This directory is reserved for immutable records produced by the isolated
hardening protocol. The protocol compares one exact translation snapshot with
one exact successor. It does not decide whether either translation is faithful
to CR-1.0 and it does not treat test survival as confirmation.

## Record families

The protocol keeps four records separate:

- `hardening-comparison.v1` freezes the baseline, successor, signatures,
  target role, gain, protected material, imports, translation delta, and
  criticism-state snapshot. It carries no result status.
- `hardening-evidence.v1` is one replayable mechanical observation for one
  derived `HO:` obligation. Evidence is bound to the complete comparison,
  checker implementation, input records, and typed payload.
- `hardening-decision.v1` is one fallible human disposition for one derived
  semantic requirement. It cannot supply mechanical evidence or promote a
  project import to source authority.
- `hardening-resolution.v1` is generated from the complete evidence and
  decision inventories. It reports every conjunct independently and has no
  score or semantic verdict.

Suggested published layout:

```text
forge/hardening/
  comparisons/
  evidence/
  decisions/
  resolutions/
```

Keep drafts outside those directories. Published files are canonical UTF-8
JSON followed by one newline and use their content-addressed ID as the
filename. A resolver should read the complete evidence and decision
directories so an inconvenient counterwitness cannot be omitted by selecting
only favorable files.

## Status rule

The derived obligations are conjunctive. Any replayed counterwitness or an
exact human `DEFEATS_HARDENING` disposition yields `NO_HARDENING`. Missing or
inconclusive evidence, an open human decision, an effective-live criticism, or
unavailable execution semantics yields `UNRESOLVED`. The record vocabulary
reserves `HARDENING_UNREFUTED` for a fully witnessed mechanical conjunction
plus every required scoped human decision. V1 cannot reach it because it has no
bound artifact resolver or model executor.

`HARDENING_UNREFUTED` is scoped criticism status. It is not truth,
probability, support, convergence, or finality.

## Execution boundary

V1 implements a deterministic parser for payloads that a caller declares to
describe a finite and exhaustive model class. It deliberately treats every
such payload as `INCONCLUSIVE`: without a bound artifact resolver or model
executor, the declaration is not mechanical evidence. Nonexhaustive search may
later expose a counterexample but cannot discharge a universal condition. The
proof-certified mode is likewise reserved for a later replayable proof adapter.

A neutral semantic model with `execution_semantics: NONE_V1` cannot discharge
model satisfaction, non-broadening, gain, non-vacuity, or model-level
preservation. Its evidence is therefore `INCONCLUSIVE` and its resolution
remains `UNRESOLVED`, regardless of human acceptance.

## Human requirements

The runtime derives separate requirements for:

- the declared scope and boundary;
- the protected registry;
- the relevance of the targeted gain;
- the type and translation-delta classification; and
- every exact project-import set used for the comparison.

Human decisions remain append-only. Successors form a single sequence for one
requirement. They are content-bound inputs, but the record does not establish
the reviewer's identity or make the judgment infallible.

## Command line

`tools/run_hardening.py` exposes four operations:

```text
obligations  derive the exact mechanical and human requirements
evidence     build and replay one typed evidence record
decision     build one human-decision record
resolve      resolve the complete evidence and decision inventories
```

Publication is no-clobber and durable. Reusing a path is idempotent only when
the bytes are identical.
