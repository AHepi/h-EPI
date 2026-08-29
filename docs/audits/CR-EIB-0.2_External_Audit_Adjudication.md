# CR-EIB-0.2 external audit adjudication

## Scope and authority

The CR-1.0 PDF is the sole semantic and formal authority. GLM 5.3 and Kimi K3
were independent advisory reviewers. Their reports do not establish source
meaning, proof, refutation, mapping fidelity, or bridge conformance.

Both final reviews received the same full-authority packet:

| Item | SHA-256 |
|---|---|
| CR-1.0 PDF | `08ff81e848fea976b558345402d85723173be8f40f1041fb00d6267f1e026b8b` |
| Final audit packet | `9ef0da16f8dcd940b7dda409de569ae57ef1bb338c2353a0f6d78701fa4fdc8c` |
| GLM 5.3 report | `c938fb5f407cac65f8814397335f630923d12ba5009c902926983faf1d5929ad` |
| Kimi K3 report | `43a2c5d5dc617e9b6c69a3a3a4df11ea86bdd3e5353d02c42ddb7a54d9cef2b6` |

GLM used maximum reasoning and returned 84,610 output tokens. Kimi used its
maximum supported thinking mode and returned 32,287 output tokens. Neither
request supplied an output-token budget. Hidden reasoning was not persisted or
treated as a verdict.

## Controller verdict

No final-audit finding is an S0/S1 release blocker for the candidate pilot. No
auditor found a contradiction with the anchored PDF clauses or a path that
promotes operational replay into semantic acceptance. The scoped pilot is fit
to publish with:

| Status | Result |
|---|---|
| Operational integrity | `PASS` only after same-invocation PDF and Lean replay |
| Mapping fidelity | `UNREVIEWED` |
| Full CR-1.0 bridge conformance | `BLOCKED` |
| Source-level TH-3 adjudication | Not established |

The controller accepts GLM's scoped `PASS`. Kimi's `CONDITIONAL PASS` rests on
its inability to execute a static packet; the controller independently executed
the full replay successfully.

## Findings and dispositions

| Report finding | Disposition |
|---|---|
| GLM F-01: seven TH-3 dependencies lack accepted typed mappings | Accepted full-conformance gap. This is the next semantic gate and remains explicitly blocked. |
| GLM F-02: the relative countermodel uses constant-true `CCPResult` | Accepted as a useful stronger-test target, not a defect in the stated unconstrained-signature theorem. Source-level promotion remains prohibited. |
| GLM F-03: verifier Python is not self-hashed | Deferred. A self-hash updated in the same change is not an independent trust root; commit review, remote commit identity, CI, and future signed releases are the meaningful anchors. |
| GLM F-04: no two-endpoint divergence witness | Deferred fidelity-review aid. Endpoint totality, uniqueness, and witness independence are expressly not claimed. |
| GLM F-05: source-anchor v1 models only the pilot's plain `R` marks | Accepted full-conformance gap. Evolve a versioned source-status schema before anchoring composite X/R/M/Q/O marks. |
| GLM F-06: no SMT/witness-replay slice | Accepted and already disclosed future work. It does not affect the Lean-only pilot verdict. |
| GLM F-07: evidence resolver is not wired to bundle verification | Deferred until evidence records and the import ledger exist. The current resolver is explicitly application-facing. |
| GLM F-08: no canonicalization known-answer vector or anchor-set wrapper schema | Accepted low-priority interoperability hardening. |
| Kimi F-1: stage table overstated machine replay of reviewed readings | Accepted and corrected after the audit. Machine-replayed PDF snapshots and hash-pinned human-reviewed transcriptions are now separate rows. No code, declaration, or theorem changed. |
| Kimi F-2: CI Python requirements are version-pinned but not hash-locked | Deferred supply-chain hardening. The operational verifier has no third-party Python dependency; the exposure is limited to CI test fidelity. |

## Material defects found and fixed during audit

Earlier audit passes and local independent reviews found issues that were fixed
before the final packet:

| Defect | Resolution |
|---|---|
| Refined DF-10 reused the immutable legacy declaration ID while TH-3 still consumed the legacy symbol | Restored `EIB-DF10-CANDIDATE` byte-for-byte and introduced `EIB-DF10-REFINED-CANDIDATE`. |
| Accepted mappings could retain partial coverage, losses, unsupported interpretation classes, or unresolved source dependencies | Added equivalence-capable-class, exact/lossless, accepted-choice/review, verified-obligation, and accepted dependency-closure gates in both model and bundle policy layers. |
| Three new schemas were pinned but two older published schemas were not | Canonically pinned and drift-tested all five published schemas. |
| Declared NFC normalization was not enforced | Added NFC fixed-point validation and adversarial tests. |
| Axiom-audit failure directions and DER policy branches lacked tests | Added missing/extra/duplicate axiom-output and DER closed/empty-axiom mutation tests. |
| Refined TH-3B had an existential witness but no matching uniform `not-forall` theorem | Added and axiom-audited `EIB_TH3b_refined_relative_non_sufficiency`. |
| Some reviewed proof artifacts lacked proposition-level Lean bindings | Bound every audited DF-10 artifact and refined countermodel theorem in `DeclarationBindings.lean`. |
| Deep JSON and residual I/O failures could escape stable CLI diagnostics | Converted them to typed, stable failures without masking interrupts. |

## Executed evidence

The controller ran 76 tests under normal Python and 76 under `python -O`, checked
all formal-package hashes, built all 12 Lean jobs, confirmed 14 audited
declarations have empty axiom lists, and ran the authority PDF plus Lean replay
in one invocation. The final executable report was:

```text
operational_status: PASS
mapping_fidelity_status: UNREVIEWED
bridge_conformance_status: BLOCKED
record_status: PASS
schema_status: PASS
formal_package_status: PASS
authority_pdf_checked: true
formal_replay_checked: true
```

Credentials were supplied only through hidden interactive input. No credential,
raw model reasoning, or authority PDF byte stream is stored in the repository.
