# CR-EIB 0.2 research basis

## Status and authority boundary

This note records engineering research used before introducing the CR-EIB 0.2
type-and-projection process. It is advisory. The supplied CR-1.0 PDF remains the
sole semantic and formal authority for the creativity calculus. No paper listed
here can add a CR-1.0 premise, repair a source ambiguity, or promote a bridge
choice from proposed to accepted.

The research question was: how should an authoritative semantic source be made
executable in Lean without confusing successful compilation with faithful
translation, and how should projections, assumptions, and conservative-extension
claims remain auditable?

## Research channels

AlphaXiv discovery and page-level PDF queries were used to identify and read the
most relevant current papers. Consensus search was independently run for work on
formal specification and conservative extension. Its full-record fetch endpoint
did not complete, so no repository claim or citation depends on a Consensus
search snippet. The search served as discovery-only corroboration and did not
alter the design.

## Adopted engineering practices

| Practice | Research basis | CR-EIB 0.2 consequence |
|---|---|---|
| Report formal validity separately from semantic fidelity | [Beyond Compilation: Evaluating Faithful Natural-Language-to-Lean Statement Formalization](https://www.alphaxiv.org/abs/2606.31002), especially pp. 1–4, shows that a declaration may compile while omitting hypotheses, changing domains, or becoming vacuous. It evaluates compilation and semantic faithfulness separately and treats independent model consensus as a conservative filter rather than an equivalence proof. | Lean replay status cannot imply source fidelity. Declaration records and verifier output expose operational replay, mapping fidelity, and bridge conformance as different judgments. |
| Preserve provenance, surrounding source context, and independent review | [FormaTheoria: Constructing Large-Scale Lean Theories from Mathematical Literature](https://www.alphaxiv.org/abs/2608.10894), especially pp. 1 and 6–7, treats dependency discovery, source defects, semantic fidelity, provenance, and review gates as distinct workflow concerns. | Every new interpretation points to source regions and named bridge choices, records losses and open obligations, and remains unaccepted while review or coverage is incomplete. |
| Make translation obligations explicit and retain boundary information | [Kairos: Generating Tick-Indexed Proof Obligations for Synchronous Temporal Contracts](https://www.alphaxiv.org/abs/2607.23178), especially pp. 1–2, connects source contracts to generated local obligations through a mechanized translation and preserves distinctions between temporal boundaries. | The DF-10 surface projection retains the selected pair `(I, t_I)` and its endpoint evidence. It does not erase to a bare interval or invent endpoint totality, uniqueness, or maximality. |
| Put generated interpretation outside the trusted semantic boundary | [Proof-Carrying Certificates for LLM Pipelines: A Trust-Boundary Architecture](https://www.alphaxiv.org/abs/2605.16407), especially pp. 1, 11–12, and 19, distinguishes kernel-checked structure from unverified semantic or human oracles and audits declared axioms and scope. | Kernel-checked projection and model-expansion theorems certify only their typed bridge statements. Opaque source predicates, role semantics, and source-level fidelity remain declared limitations rather than hidden assumptions. |

## Design consequence

The next bridge layer is additive. It preserves the legacy pilot, introduces a
shared-content role refinement as a visibly proposed interpretation, and proves
DF-10 expansion only relative to the already refined model and opaque ports. It
does not claim that migrating an arbitrary legacy `Problem` carrier into a
`Content` role subtype is conservative. That stronger claim would fail for old
models whose carriers cannot be related by the required equivalence.

The model-expansion theorem concerns only the new `EKC` symbol defined by the
DF-10 conjunction. The projection theorem concerns only unbundling the chosen
role and endpoint witnesses while preserving their evidence. Neither theorem
establishes contextual problemhood, critical-lineage identity, complete DF-7a
semantics, or authoritative TH-3.
