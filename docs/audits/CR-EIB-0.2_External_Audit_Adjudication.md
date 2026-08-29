# CR-EIB-0.2 external audit adjudication

## Scope and authority

The CR-1.0 PDF is the sole semantic and formal authority. GLM 5.3 and Kimi K3
were independent advisory reviewers. Their reports do not establish source
meaning, proof, refutation, mapping fidelity, or bridge conformance.

Both final reviews received the same full-authority packet. Prior audit reports
and the orchestrator handover were omitted to prevent the earlier model outputs
from biasing the new reviews; every omission was listed in the packet manifest.

| Item | SHA-256 |
|---|---|
| CR-1.0 PDF | `08ff81e848fea976b558345402d85723173be8f40f1041fb00d6267f1e026b8b` |
| Final audit packet | `cd6a958505f1162f660da9c666b61d966d07bc58e8253f03e906c26b8cee403c` |
| GLM 5.3 report | `48de0f874b785471e5bbe6f5ac30d8b1f64aa71e5a5034d4d22cb48d0917b75b` |
| Kimi K3 report | `c314a3a360cca8cd5971417730c241fb43ee4e80c013f81e161d2ff1a6798570` |

GLM used maximum reasoning and returned 46,338 output tokens. Kimi used its
maximum supported thinking mode and returned 33,446 output tokens. Neither
request supplied an output-token budget. Hidden reasoning was not persisted or
treated as a verdict.

## Controller verdict

Both final auditors returned a scoped `PASS` and found no S0/S1 release
blocker. Neither found a contradiction with the anchored PDF clauses or a path
that promotes operational replay into semantic acceptance. The candidate pilot
is fit to publish with:

| Status | Result |
|---|---|
| Operational integrity | `PASS` only after same-invocation PDF and Lean replay |
| Mapping fidelity | `UNREVIEWED` |
| Full CR-1.0 bridge conformance | `BLOCKED` |
| Source-level TH-3 adjudication | Not established |

Both reports were static and therefore asked the controller to execute the
replays. The controller did so, including the stricter namespace-wide Lean
audit described below.

## Findings and dispositions

| Report finding | Disposition |
|---|---|
| GLM F-01 / Kimi F-01: TH-3's eight source dependencies lack accepted typed mappings | Accepted full-conformance gap. DF-7a/`CCPWitness` and the remaining dependency closure are the next semantic gate. |
| GLM F-02: no adversarial mutation test reaches the anchor word-snapshot binding path | Accepted S2 test hardening. The controller executed the real PDF replay successfully; add text, coordinate, and word-count mutations before widening the anchor set. |
| GLM F-03: repository-path traversal and symlinked-component defenses lack direct tests | Accepted S3 test hardening. The validation code is fail-closed, but dedicated negative fixtures should be added. |
| GLM F-04: verifier pin tables are an unbound trust root | Partly accepted as a trust-boundary documentation issue. A mutable self-hash is not an independent trust root; reviewed commit/tree identity, protected CI, and a future signed release are the appropriate external anchors. |
| GLM F-05 / Kimi F-04: mixed pinned Poppler versions impair cold-start reproduction | Accepted disclosed hardening gap. Preserve fail-closed behavior and publish an obtainable pinned environment or re-anchor under a consistent toolchain. |
| GLM F-06: evidence-record ingestion is not wired into bundle verification | Accepted full-conformance gap and deferred until evidence records and the ledger exist. No current verdict depends on that resolver. |
| GLM F-07: the 0.1 contract's record sketch and conservative fidelity aggregation can confuse implementers | Accepted documentation/diagnostic hardening. The published schemas and runtime remain the executable contract; mark the old sketch as superseded before external record authorship. |
| Kimi F-02: proposed `DER` can be misread as dependency-complete | Accepted S3 documentation hardening. Candidate records carry explicit claim scopes, and acceptance/conformance gates block unresolved dependencies, so no current verdict is overstated. |
| Kimi F-03: transcription, extractor-version, port-independence, and evidence-resolver negative controls are incomplete | Accepted test/model hardening. Prioritize the transcription/extractor mutations and a Lean `K_E ↔ Retained` negative control. |

## Material defects found and fixed during audit

Earlier audit passes, the first remote CI run, and local independent reviews
found issues that were corrected before the final packet:

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
| The first remote namespace audit found generated structure `mk.injEq` helpers using `propext` | Added file-scoped `set_option genInjectivity false` to `DF10Refinement.lean`, repinned the formal and declaration hashes, retained the empty workflow allowlist, and verified all 254 `CREIB` declarations use no axioms. |

## Executed evidence

The controller ran 76 tests under normal Python and 76 under `python -O`,
checked every formal-package hash, built all 12 Lean jobs, confirmed the exact 14
release declarations have empty axiom lists, and ran the authority PDF plus Lean
replay in one invocation. The pinned namespace auditor additionally reported:

```json
{"allowed":[],"audited":254,"axiomsUsed":[],"ok":true,"root":"CREIB","violations":[]}
```

The final executable report was:

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
