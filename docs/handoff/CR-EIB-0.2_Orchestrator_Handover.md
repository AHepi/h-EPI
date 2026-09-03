# CR-EIB-0.2 orchestrator handover

> Historical handover. For the current continuation point, use `CR-EIB-0.3_Orchestrator_Handover.md`.

## Mission and non-negotiable authority boundary

Continue the executable-bridge work for CR-1.0 without confusing a compiled
formalization with the source model. The authority is the PDF whose SHA-256 is:

```text
08ff81e848fea976b558345402d85723173be8f40f1041fb00d6267f1e026b8b
```

The Markdown handoff plan, repository prose, bridge choices, Python verifier,
Lean declarations, research papers, and external model audits are subordinate
implementation evidence. None may add source premises or settle an ambiguous
reading. Preserve these three independent status surfaces:

| Surface | Current value | Meaning |
|---|---|---|
| `operational_status` | `PASS` with PDF and Lean replayed together | The pinned bytes and formal package replayed successfully. |
| `mapping_fidelity_status` | `UNREVIEWED` | Human semantic review has not accepted the source-to-IR mapping. |
| `bridge_conformance_status` | `BLOCKED` | The tracked pilot is not full CR-1.0 conformance. |

No source-level creativity theorem has been proved or refuted.

## Repository and history state

Repository: `https://github.com/AHepi/h-EPI`

At the start of this increment, local `main` was `3a751c2` and remote
`origin/main` was `018d890`. Their trees were identical, but their histories are
replayed/divergent (`ahead 7, behind 8`). Do not force-push or destructively reset
to reconcile this. Use the installed `h-epi-safe-publish` skill and transplant
the authorized change onto `origin/main` if required by its procedure.

The implementation commit is the commit containing this handover and the audit
artifacts. Resolve its final published SHA with `git rev-parse origin/main` after
push and verify the remote tree, not merely the local branch label.

The implementation first landed on remote `main` as `30e078a`. Its initial
`bridge pilot` run built all Lean modules and printed empty axiom sets for the
14 release declarations, but the action's additional namespace-wide audit
rejected three Lean-generated structure injectivity declarations that use
`propext`. A workflow-only intermediate commit (`b7d7140`) allowed `propext`,
but that was superseded because the repository intentionally keeps the broader
namespace allowlist empty. The final source-level correction disables generated
injectivity declarations in `DF10Refinement.lean`, matching the existing core
and role-refinement modules. Both the whole namespace and the exact 14-result
release audit therefore remain zero-axiom checks.

## What this increment built

### Additive formal spine

The legacy pilot is preserved. The new layer is additive because moving an
arbitrary legacy `Problem` carrier into a `Content` subtype is not conservative
without an explicit transport.

| Layer | Main artifacts | Contract |
|---|---|---|
| Role refinement | `ContentRole`, `ContentRoleRefinement`, `RoleEligible`, `RoleContent`, `ProblemContent` | Roles are bridge eligibility predicates on shared Content; they are not required disjoint and do not prove contextual causal role satisfaction. |
| Endpoint witness | `EndTimeWitness` | Carries `(I, t_I)` and endpoint evidence; no totality, uniqueness, maximality, or global selector is assumed. |
| Refined DF-10 | `DF10OpaquePorts`, `EIB_DF10_REFINED` | Preserves the three conjunctions, the same `x`, and the same selected `t_I` for `K_E` and `Retained`. |
| Projection | `EIB_DF10_refined_projection` | Exact only over the declared witness-carrying surface. |
| Legacy interop | `LegacyProblemTransport`, `EIB_DF10_refined_legacy_transport` | Requires an explicit carrier relationship; no silent migration. |
| Model expansion | `DF10EKCExpansion`, `EIB_DF10_canonical_model_expansion_exists` | IR-7-style expansion only for the added `EKC` symbol over a fixed refined opaque-port base with unchanged reduct. |
| Refined countermodel | `EIB_TH3b_refined_countermodel_exists`, `EIB_TH3b_refined_relative_non_sufficiency` | Relative existential and uniform non-sufficiency results; not source-level TH-3. |

All 14 audited public results have empty axiom lists. Proposition-level bindings
in `formal/CREIB/Audit/DeclarationBindings.lean` guard their intended types.

### Immutable declaration identities

There are four declarations:

| Declaration | Schema | Lean symbol | Relation |
|---|---|---|---|
| `EIB-DF10-CANDIDATE` | v1 | `CREIB.EIB_DF10_CANDIDATE` | Restored byte-for-byte legacy identity. |
| `EIB-DF10-REFINED-CANDIDATE` | v2 | `CREIB.EIB_DF10_REFINED` | New role/endpoint-explicit candidate. |
| `EIB-TH3A-PILOT` | v1 | `CREIB.EIB_TH3a_unfold` | Depends on the legacy DF-10 declaration. |
| `EIB-TH3B-PILOT` | v1 | `CREIB.EIB_TH3b_relative_non_sufficiency` | Depends on the legacy DF-10 declaration. |

Do not retarget an established declaration ID to a different carrier, binder
list, or Lean symbol. Add a new immutable ID instead. A separately identified
refined TH-3 record remains future work.

### Metadata and verifier hardening

The v2 declaration schema adds ordered dependent binders, interpretation choice
IDs, preservation/loss/coverage records, separate review state, and typed proof
obligations. The registry contains 17 proposed, explicitly non-authoritative
choices. Only the refined DF-10 record is v2; v1 remains supported.

The verifier now:

- pins all four declarations, the choice registry, all five published schemas,
  and the 13-file formal package;
- rejects hidden or reordered binders, unresolved choices, duplicate metadata
  IDs, unreviewed artifact paths/symbols, and schema/record drift;
- permits mapping acceptance only for equivalence-capable interpretation
  classes with accepted review and choices, exact exclusion-free/lossless
  coverage, verified obligations, and accepted source/bridge dependency closure;
- validates UTF-8, NFC, LF endings, strict JSON, deep nesting, and stable typed
  CLI failures without masking interrupts;
- derives bridge conformance fail-closed instead of using a constant; and
- keeps operational replay, fidelity, and conformance separate.

## Research basis

`docs/bridge/CR-EIB-0.2_Research_Basis.md` records the engineering research.
AlphaXiv page queries supported separate compilation/fidelity judgments,
source-context provenance and independent review, explicit translation
obligations that retain boundary information, and a narrow proof-carrying trust
boundary. Consensus search was run independently, but its full-record fetches
did not complete; no claim relies on a Consensus snippet.

The user requires fresh AlphaXiv and Consensus research whenever a genuinely new
tool or process is proposed. Keep calls bounded and do not repeatedly retry a
stalled connector. Existing verifier hardening and extension of the current
formal pattern do not automatically require inventing a new process.

## Independent external audits

GLM 5.3 and Kimi K3 independently received the same complete PDF extraction and
current repository snapshot. Both used maximum available reasoning and no
output-token budget. They are advisory only.

| Item | SHA-256 |
|---|---|
| Final packet | `cd6a958505f1162f660da9c666b61d966d07bc58e8253f03e906c26b8cee403c` |
| GLM report (`PASS`, scoped) | `48de0f874b785471e5bbe6f5ac30d8b1f64aa71e5a5034d4d22cb48d0917b75b` |
| Kimi report (`PASS`, scoped) | `c314a3a360cca8cd5971417730c241fb43ee4e80c013f81e161d2ff1a6798570` |

Neither found an S0/S1 blocker, authority contradiction, or false semantic-PASS
path. The exact reports and controller dispositions are under `docs/audits/`.
The final re-audit followed the strict namespace-axiom correction. GLM returned
46,338 output tokens and Kimi returned 33,446. Prior audit reports and this
handover were omitted from their packet to preserve reviewer independence. No
formal source, declaration, schema, verifier, workflow, or test byte changed
after packet construction; only the excluded audit and handover artifacts were
refreshed.

Credentials were entered through hidden interactive input only. No API key or
raw model reasoning is stored. Do not recover or restate keys from conversation
history; obtain fresh session-scoped credentials if another audit is authorized.

## Reproduction

Use the repository virtual environment or install the pinned CI requirements.
The local execution environment has a Lean `/proc/self/exe` detection issue. A
temporary, untracked shim was used only to make the installed pinned toolchain
discover its executable path:

```sh
env PYTHONPATH=src \
  PATH='/root/.elan/toolchains/leanprover--lean4---v4.33.1/bin':"$PATH" \
  LEAN_FIXED_APP_PATH='/root/.elan/toolchains/leanprover--lean4---v4.33.1/bin/lake' \
  LD_PRELOAD='/workspace/scratch/5869f88ffd90/tmp/lean_app_path_fix.so' \
  /workspace/scratch/5869f88ffd90/tmp/h-epi-audit-venv/bin/python \
  tools/verify_bridge.py \
  --pdf '/workspace/scratch/5869f88ffd90/upload/Creativity_Semantic_Model_CR-1.0(1).pdf' \
  --lean
```

Expected output includes:

```text
operational_status=PASS
mapping_fidelity_status=UNREVIEWED
bridge_conformance_status=BLOCKED
record_status=PASS
schema_status=PASS
formal_package_status=PASS
authority_pdf_checked=true
formal_replay_checked=true
```

Additional checks used for this increment:

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -O -m unittest discover -s tests -v
sha256sum -c formal/formal-package.sha256
git diff --check
```

Expected test count is 76 in each Python mode. The formal build has 12 jobs, the
release audit prints 14 declarations with no axioms, and the pinned broad audit
reports 254 `CREIB` declarations with `allowed=[]`, `axiomsUsed=[]`, and no
violations.

The exact native extractor provenance is intentionally fail-closed and mixed:
`pdftotext 24.02.0` and `pdfinfo 26.05.0`. CI cannot reproduce full operational
PASS because the authority PDF is not committed. README records this limitation.

## Open semantic gates

These are not coding cleanup. They require source-faithful interpretation and
human review:

| Priority | Gate | Why it blocks progress |
|---|---|---|
| 1 | Type and review DF-7a's complete `CCPWitness`, critical-lineage identity, endpoint problem situation, and retained availability | TH-3B's source proof relies on a lineage-connected endpoint, while the current countermodel is intentionally over unconstrained ports. |
| 2 | Map TH-3's remaining exhaustive dependencies: MS-4, MS-8, SC-7, SC-8, IR-2, IR-4 | Source-level TH-3 cannot be adjudicated until all eight dependencies, including DF-10 and DF-7a, have accepted mappings. |
| 3 | Review the four DF-10 interpretation choices and every declared loss/exclusion | Operational proof obligations do not establish role semantics, port meanings, endpoint globality, or lineage evidence. |
| 4 | Add separately identified refined TH-3A/TH-3B declarations only after their statements and dependency closure are designed | The current refined witness is auxiliary and must not overwrite the immutable legacy records. |
| 5 | Implement the SMT/witness-replay slice | Required by the broader CR-EIB release gate, but outside the current Lean-only pilot. |

## Deferred non-blocking hardening

The final audits suggested mutation tests for anchor word snapshots and native
extractor versions, direct traversal/symlink-component fixtures, a Lean
`K_E ↔ Retained` negative control, an obtainable pinned Poppler environment,
clarification of proposed `DER` and the superseded contract record sketch, and
wiring the evidence resolver once an evidence ledger exists. Earlier useful
hardening suggestions—canonicalization vectors, a source-anchor-set wrapper
schema, composite X/R/M/Q/O source-status schema v2, and endpoint-divergence
witnesses—remain deferred. None changes the current scoped verdict.

Do not "fix" the verifier-source self-hash suggestion by adding a mutable hash
manifest checked by the same code and calling it a trust root. Prefer reviewed
commits, remote commit identity, protected CI, and a signed release/tag if a
stronger external anchor is required.

## Recommended next orchestrator action

First verify the published commit and both GitHub Actions jobs. Then open a
source-mapping design task for DF-7a/`CCPWitness`, beginning with fresh targeted
AlphaXiv and Consensus research because that step creates a new source-to-IR
mapping process. Keep the PDF passages in view, produce explicit alternative
readings where the source is ambiguous, and do not write Lean until the human
mapping choice and its losses are reviewable.
