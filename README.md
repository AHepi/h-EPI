# h-EPI

`h-EPI` is the implementation workspace for the CR-1.0 creativity semantic model and its proposed executable interpretation bridge.

## Current status

| Layer | Status | Meaning |
|---|---|---|
| CR-1.0 authority identity | **VERIFIED** | The designated PDF is identified by SHA-256 and remains the sole semantic/formal authority. |
| Cold-start inventory integrity | **PASS** | The quarantined bootstrap package is internally consistent and reproducible. |
| CR-1.0 executable-calculus bootstrap | **FAIL** | Required declaration-level source mappings and typed bodies are incomplete. |
| CR-EIB-0.1 conformance | **BLOCKED** | The bridge is a non-authoritative proposal and cannot pass until its evidence obligations are discharged. |

No theorem has yet been adjudicated as proved or refuted against the complete CR-1.0 authority. This repository does not contain a creativity classifier and does not automate judgments that something or someone is creative.

Lean and SMT are implementation targets. Any checked pilot result is explicitly scoped to its encoded model and evidence record; it is not automatically a result about the whole CR-1.0 model.

The immutable cold-start package is under `baseline/cr-1.0/bootstrap-v0.1/`. Run its integrity and quarantine validator with:

```sh
python -m pip install -r requirements-ci.txt
python baseline/cr-1.0/bootstrap-v0.1/tools/validate_bootstrap.py
```

## Authority and redistribution

The authority PDF itself is intentionally not committed. Its expected digest is recorded in the baseline and bridge evidence. Local verification requires a lawfully held copy supplied by the operator.

No license has yet been granted for this repository. Publication alone does not grant permission to copy, modify, or redistribute its contents.
