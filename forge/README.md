# Semantic Model Forge 0.1

SMF-0.1 is a criticism harness for hardening a semantic model before further mathematics is extracted from it. It does not score confirmation, infer truth from repeated passes, or replace CR-1.0. The sole semantic and formal authority remains the externally supplied CR-1.0 PDF with SHA-256 `08ff81e848fea976b558345402d85723173be8f40f1041fb00d6267f1e026b8b`.

The seed corpus is deliberately problem-led. A minimal pair holds a base fixed, changes one mechanism, predicts a positive and negative classification, asks one critical question, and states its oracle. A pass leaves the tested conjecture unrefuted. A failure criticizes the whole tested conjunction, which includes the source reading, project imports, case construction, auxiliaries, and oracle.

## Authority labels

Every corpus record has a separate annotation. The constructed challenge or research issue is always marked `construction_kind: project_import`; its distinct `basis_kind` says what could ground the proposed contrast. The present seed uses only `source_interpretation` for contestable readings of exact, digest-bound source regions and `project_import` for operator or harness rules that must not be attributed to CR-1.0. It contains no reviewed `source_authority` annotation. The wider claim-kind policy reserves `source_authority`, `external_source_report`, and `formal_consequence` for records that can discharge their stronger provenance requirements. This prevents a source locator—or a source-adjacent paraphrase—from laundering the harness's own test construction into source authority. Machine pinning proves record integrity, not fidelity of interpretation.

The recognition-attention-value condition is explicitly a `project_import`. The same boundary is preserved for the operator decisions that conjecture precedes criticism, unresolved criticism may remain suspended, and episodes may overlap or absorb one another. Nearby CR-1.0 clauses are listed only as related constraints.

A challenge annotation records the scope of its proposed oracle as `source_scoped`, `interpretation_provisional`, or `project_import_provisional`; none means finally resolved or immune from criticism. An unresolved contrast remains a research issue with `status: "unresolved"` and `resolution: null` in its annotation. Absence of disproof, source silence, agreement, retrieval rank, and model confidence cannot convert it to false, true, or resolved.

## Files and record shapes

`schema/challenge.schema.json` validates the general runtime-compatible `MinimalPairChallenge` shape. Every oracle, including an on-the-fly one, must begin with one of the explicitly non-final statuses `source_scoped`, `interpretation_provisional`, or `project_import_provisional`, followed by a rationale; built-in dynamic templates default to `project_import_provisional`. The seed's other string prefixes—`held_fixed_base=`, `varied_mechanism=`, `positive_expected_classification=`, `negative_expected_classification=`, and `critical_question=`—remain a corpus convention rather than a frozen restriction on later cases. A standalone challenge still has no source-authority effect without its separately typed corpus annotation.

`schema/research-issue.schema.json` validates runtime-compatible external issues. Each issue names the decision and its relevance, carries at least two rival readings, gives falsifier conditions for every rival, predicts a finding that would discriminate them, bounds the admissible source scope, and declares when to stop. Missing any one of these blocks a research warrant.

`schema/corpus.schema.json` validates the corpus envelope, authority identity, non-inductive policy, source-boundary annotations, and provider policy. `corpus/cr-1.0-seed.json` contains ten initial minimal pairs and ten unresolved research issues. The counts are a seed inventory, not a claim of completeness.

Runtime records are kept free of annotation-only fields so they can be passed directly to the strict parsers in `creib.forge`. `challenge_annotations` and `research_issue_annotations` carry titles, authority distinctions, source locators, and unresolved status without changing those runtime shapes. Their editorial `title` and `boundary_note` prose is obligatorily marked `unreviewed_non_authoritative` with semantic effect `none`; the parser and validator reject any attempt to give that prose a typed mechanical effect.

`schema/research-ledger.schema.json` validates the v2 external research ledger. Every entry is a bounded report of source claims only, tied to a directly inspected, exact-version primary source and protected by content digests. Any possible use in the project is a separate `PROPOSED` record. V2 requires the engineering-decision collection to remain empty because it has no trusted human-attestation mechanism. `schema/adaptive-inquiry.schema.json` and `schema/inquiry-event.schema.json` validate exact inquiry plans, declared human triage, content-addressed questions, and append-only question events.

## Non-inductive research rule

Research starts from an external unknown whose answer would change a live decision. The warrant must expose rival readings and what could falsify each one before discovery. AlphaXiv is the preferred initial discovery channel, but providers remain replaceable and their outputs are never oracles. Statistical ranking may help locate criticism; it may not promote a claim, interpretation, or authority status.

The working loop is: reproduce a defect, state rivals, build a one-difference challenge when an oracle is available, run it, preserve the complete trace, revise one mechanism, and replay all prior challenges. Passing cases are retained as regression tests, not accumulated as inductive support.

The adaptive inquiry controller never infers a human diagnosis from a failed test. With no exact human triage it returns `AWAITING_HUMAN_TRIAGE` and no questions. A supplied triage may route work to the harness, model, authority review, or bounded external research. Research reports return to human review or internal integration; agreement and “not found” have no confirmatory effect.

## First calibration

Run the authority-bound calibration and optionally create an immutable run record:

```sh
PYTHONPATH=src python tools/run_semantic_forge.py first-run \
  --authority /path/to/Creativity_Semantic_Model_CR-1.0.pdf \
  --output forge/runs/my-new-calibration.json
```

The output file is created exclusively and is never overwritten. Its parent directory must already exist. When the pinned corpus or execution contract changes, use a new output path and retain the old record only as historical evidence; a preserved run is current only if strict replay succeeds. Every run remains mechanically scoped and requires human semantic disposition.

## Validation

From the repository root, strict JSON parsing, validation of every local `*.schema.json`, and seed-corpus validation can be run with:

```sh
PYTHONPATH=src python tools/validate_semantic_forge.py
```

The validator resolves relative references through a registry built only from the local schema directory. An unregistered reference fails closed; validation never retrieves a schema over the network. To keep resource identity unambiguous in v0.1, nested schema identifiers and anchor or dynamic-reference mechanisms are rejected; use root identifiers and local JSON Pointer references. For another local record, pass `--instance PATH --schema SCHEMA-NAME`.

Schema validity establishes record shape only. It does not establish source fidelity, resolve an issue, validate an oracle, or prove that a physical system instantiates the model.

For record types with executable invariants, the validation CLI also runs their specialized runtime loader and reports `SCHEMA_AND_RUNTIME_VALID`. For schemas without such a loader it reports `SCHEMA_VALID_ONLY`; it never labels schema-only success as mechanical semantic validation.
