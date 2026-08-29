# Executable interpretation bridge

CR-EIB is a versioned, non-authoritative interpretation layer. It cannot modify what the CR-1.0 PDF says.

The current pilot contains three candidate declarations:

| Bridge declaration | Source anchor | What is checked |
|---|---|---|
| `EIB-DF10-CANDIDATE` | `DF-10` | An explicitly typed conjunction with an interval-endpoint witness |
| `EIB-TH3A-PILOT` | `TH-3` | Definitional unfolding of the candidate DF-10 body |
| `EIB-TH3B-PILOT` | `TH-3` | A finite typed countermodel to uniform sufficiency |

All source inferential statuses remain `null`. `DEF` and `DER` are proposed bridge statuses only. Every formal parameter is explicit, and all four uninterpreted semantic ports are named `CRModel` fields. The TH-3b logical witness uses an explicit false interpretation for `K_E`; separately, application evidence must contain an accepted explicit negative before the evidence resolver supports a witness. Unavailable evidence resolves to `blocked`, never false.

The Lean replay is valid relative to the minimal unconstrained port signature. CR-EIB conformance remains blocked until the full source dependency closure is mapped and accepted.

The Draft 2020-12 schemas enforce record shape. `creib.verify` additionally enforces cross-record identity, exact pilot metadata, source-file hashes, dependency resolution, acyclicity, and evidence policy; tests validate every committed instance through both layers.
