# CR-1.0 cold-start bootstrap v0.1

## Outcome

**Bootstrap gate: FAIL (fail closed).** The supplied PDF is identifiable and fully covered, and its active numbered declarations and source tags are inventoried. The active formal model cannot yet be translated into an executable typed calculus without making unauthorized choices about missing sorts, symbol arities, variable bindings, hidden baselines, mixed definition/principle clauses, and prose-only relations. No such choices were made.

No theorem was proved or refuted, no application was classified, and no creative system or physical realizer was implemented.

## Authority contract

| Rank | Material | Permitted use |
|---:|---|---|
| 1 | `Creativity_Semantic_Model_CR-1.0(1).pdf` | Sole semantic and formal authority. |
| 2 | Active “Model CR-1.0,” physical PDF pp. 219–234 (printed footer pp. 218–233) | Canonical active formal core within the PDF. |
| 3 | Earlier synthesis, indexes, public corpus, and concordance in the same PDF | Source interpretation and provenance support; cannot silently override the active model. |
| 4 | Superseded precursor audit, physical PDF pp. 235–256 (printed footer pp. 234–255) | Audit evidence only; never an alternate active namespace. |
| 5 | Downstream applications and adversarial audit, physical PDF pp. 257–283 (printed footer pp. 256–282) | Quarantined application/import/test specifications; not an alternate core. |
| Procedure only | `CR-1.0_Executable_Calculus_Handoff_Plan(2).md` | Bootstrap workflow and inferential-status discipline. Any conflict or addition is recorded, not imported into CR-1.0. |

## Verified source identity

| Source | SHA-256 | Size / extent |
|---|---|---|
| Authority PDF | `08ff81e848fea976b558345402d85723173be8f40f1041fb00d6267f1e026b8b` | 1,734,769 bytes; 286 physical PDF pages |
| Procedural handoff | `afc2fbc6d18f6340b67a266f657a58112de9fa00d5c7d3ee557195332a8e404e` | Markdown source |

## Inventory snapshot

| Namespace | Active count | Scope |
|---|---:|---|
| `TY` | 3 | Typed-language discipline |
| `MS` | 9 | Model structure |
| `SC` | 8 | Satisfaction conditions |
| `DF` | 25 | Definitions, including `DF-4a` and `DF-7a` |
| `RC` | 3 | Reconstruction constraints |
| `DP` | 11 | Deutschian postulates |
| `AB` | 1 | Adaptation bridge |
| `OM` | 10 | Object moves |
| `IR` | 8 | Inference rules |
| `CT` | 7 | Constructor-theory interface |
| `BR` | 8 | Realization bridges |
| `TH` | 17 | Results awaiting later adjudication |
| **Total active numbered declarations** | **110** | Physical PDF pp. 219–234 |
| `S-*` | 23 | Active source-tag registry |
| `I-*` | 24 | Downstream import requests |
| `T-*` | 15 | Downstream discriminating tests |
| `A-CT*` / `A-TH*` | 4 / 8 | Downstream audit findings |

## Why the gate stops

The exact blocker register is in `authority/audit_ledger.yaml` and `reports/bootstrap_gate_report.md`. The principal blocker classes are missing or overlapping sorts; unresolved arities and signatures; unbound or free variables; hidden baselines and context parameters; overloaded symbols; literal ellipsis and prose-only formula bodies; undefined terms; mixed definitional and substantive content under one identifier; and incomplete source-mark and locator coverage. Report-wide active/superseded identifier collisions are recorded but are nonblocking once their namespaces remain quarantined.

The report’s local source-status alphabets are preserved in separate namespaces. They are not translated automatically into the procedural inferential statuses `DEF`, `IMP`, and `DER`. Audit entries have `inferential_status: null` and `proof_available: false`. No `TH-*` item is marked `DER` in this bootstrap.

## Artifact map

| Artifact | Purpose |
|---|---|
| `authority/source_manifest.yaml` | Authority identity, hashes, scope, and source coverage |
| `authority/coverage_matrix.yaml` | Complete physical-page/report-section coverage |
| `authority/source_status_registry.yaml` | Namespaced status schemes, source tags, and gaps |
| `authority/identifier_inventory.yaml` | Active, superseded, downstream, and audit identifiers |
| `language/core_declaration_map.yaml` | Active declarations, locators, source marks, dependencies, and blockers |
| `authority/import_ledger.yaml` | Core and downstream import-ledger skeleton; unavailable items remain quarantined |
| `language/terminology_concordance.yaml` | Terms, symbols, roles, signatures, and collisions |
| `authority/authority_hierarchy.yaml` | Conformance precedence and quarantine boundaries |
| `authority/ambiguities.yaml` | Conflicts, candidate readings, exact locators, and stop/no-repair decisions |
| `authority/audit_ledger.yaml` | Non-inferential blockers, gaps, open questions, and proposed-repair slots |
| `authority/bootstrap_gate_report.yaml` | Machine-readable gate verdict and blocker index |
| `reports/` | Human-readable evidence reports behind the machine artifacts |
| `tools/validate_bootstrap.py` | Local integrity and status-discipline checks |
| `checksums.sha256` | Package-file integrity hashes |

The package is a bootstrap record, not a repository or implementation. A repository becomes useful only after the authority resolves the blockers or explicitly authorizes a versioned reconstruction.
