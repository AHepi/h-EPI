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

`schema/research-ledger.schema.json` validates the v2 external research ledger. Every entry is a bounded report of source claims only, tied to a directly inspected, exact-version primary source and protected by content digests. Any possible use in the project is a separate `PROPOSED` record. V2 requires the engineering-decision collection to remain empty because it has no trusted human-attestation mechanism. `schema/adaptive-inquiry-v2.schema.json` and `schema/inquiry-event-v2.schema.json` validate active plural triage, exact evidence-bound assessment dispositions, inquiry plans, a non-authorizing menu of exact rival-falsifier targets, question-bound source-report envelopes, and append-only question events. The unsuffixed inquiry schemas preserve the exclusive v1 record shapes for historical validation and replay only; active v2 publication cannot create or extend them.

## Non-inductive research rule

Research starts from an external unknown whose answer would change a live decision. The warrant must expose rival readings and what could falsify each one before discovery. If a published action authorizes an exact external target, AlphaXiv is the designated preferred initial discovery channel; providers remain replaceable and their outputs are never oracles. This repository records that designation but has no external retrieval adapter. Statistical ranking may help locate criticism; it may not promote a claim, interpretation, or authority status.

The working loop is: reproduce a defect, state rivals, build a one-difference challenge when an oracle is available, run it, preserve the complete trace, revise one mechanism when its effects are separable, and replay all prior challenges. When isolation would misrepresent an interacting mechanism, revise one explicitly declared joint mechanism and keep each implicated locus visible. Passing cases are retained as regression tests, not accumulated as inductive support.

## Generic translation harness

SMF-0.4 makes the earlier criticism loop usable before a semantic model class has been safely fixed. Ten content-addressed record families bind a proposal to operator-supplied source bytes through multi-segment spans, a translation charter, source obligations, rival interpretations, explicit project imports, a neutral signature and model, a two-way bridge, and a content-addressed snapshot. The records do not archive an external source artifact. Runtime validation recomputes nested and top-level identities, enforces ordered non-overlapping UTF-8 composition, classifies every selected span, checks dependency closures and direction, binds element-specific forward/reverse incidence, and closes unresolved-record membership. Multi-region PDF spans fail closed until a deterministic composition profile exists. Every rival remains independently admissible, while explicit `admissible_branch_sets` also preserve compatible combinations; the neutral model may use only a declared combination.

That establishes translation integrity relative to the choices actually recorded. It does not establish that those choices are faithful. Interpretation decisions therefore live in a separate append-only human review lineage; successful formal replay cannot modify them. Changed review bindings persist immediate snapshot and interpretation-set lineage, invalidate every predecessor branch, and require an exact later reopening before a stale branch can be authorized. Given two snapshots and a caller-declared, content-addressed delta, the current synthesizer generates all nine adversarial test families, but it does not derive that delta from the two record closures. Every family remains deferred until both the delta and its semantic fixtures, held-fixed contract, comparator, and expectation are independently checked. No missing oracle is guessed.

The stage-neutral v3 inquiry adapter can accept translation, model, mathematical, round-trip, or harness observations without letting their origin choose a diagnosis. Candidate, auxiliary, test, and scope criticisms may coexist. A route for exact external research can be authorized only after a human-selected external action binds an issue, warrant, and nonempty attack-target subset. AlphaXiv is designated as a replaceable discovery surface at that gate, not an authority or confirmation mechanism; retrieval itself is outside this repository.

The hardening runtime keeps gain, non-broadening, non-vacuity, protected cases, exclusions, consequences, imports, evidence, and human scope decisions as separate conjuncts. The status vocabulary reserves scoped `HARDENING_UNREFUTED`, but v1 has no artifact resolver or model executor: caller-declared finite payloads remain `INCONCLUSIVE`, and production neutral models declare `NONE_V1`. No current comparison can therefore reach the positive status.

When exact source paths are supplied, the integrated controller replays registered UTF-8 byte ranges and `pdftotext`-version-bound PDF word snapshots in addition to the artifact bytes. PDF page count, geometry, and rotation are obtained with `pdfinfo`, whose version is not yet pinned. PDF word replay does not establish exact character spacing or punctuation, and unavailable tools or unsupported profiles remain explicit unresolved limitations. The controller also exposes the missing test-observation-inquiry-research-revision-delta-hardening lineage as an always-unresolved v1 stage. Separately, review authentication is unavailable, so the review stage cannot become `READY` and the integrated hardening stage remains blocked. It therefore cannot silently present this first tranche as a closed iterative repair system.

No runnable end-to-end generic translation instance is committed in this tranche. In particular, there is no committed generic source-to-snapshot inventory, v3 inquiry plan, review lineage, delta, hardening packet, or HRC candidate exposure report and freeze. The schemas and runtimes are exercised by tests; operators must supply those content-bound records to run the integrated command.

Run the integrated status report with:

```sh
PYTHONPATH=src python tools/run_translation_harness.py \
  --records-dir /path/to/translation-records \
  --snapshot /path/to/translation-snapshot.json
```

Omitted optional stages remain `NOT_SUPPLIED`, invalid bindings fail closed, and all applicable research routes remain visible with no automatic selection. The contract's thirteen conceptual gates map onto thirteen controller status slices rather than matching them one-for-one: `translation_integrity` aggregates the selected closure, while project-import checks are reported within `neutral_model`, and slice order has no priority or normative-gate meaning. See `docs/forge/SMF-0.4_Translation_Contract.md` for the gates and `docs/forge/SMF-0.4_Qualification_Fixture.md` for the synthetic non-Popper control.

The pipeline command uses its exit status as a conjunctive automation signal:

- exit `0` is reserved for a future overall status of `READY`; the unimplemented
  iteration-lineage stage makes it unreachable in v1, while missing review
  authentication independently prevents integrated hardening from running;
- exit `2` when any supplied input makes the overall status `INVALID`; and
- exit `1` for a valid but incomplete `UNRESOLVED` or `BLOCKED` report, including omitted optional stages.

The JSON report remains the authoritative explanation of which stages caused
that exit. Exit `1` is not a test failure or negative semantic verdict; it means
the harness correctly refused to call the whole pipeline ready.

The adaptive inquiry controller never infers a human diagnosis from a failed test. A failure attacks the tested conjunction, so human triage can retain several live `CANDIDATE`, `AUXILIARY`, `TEST`, and `SCOPE` criticisms—including joint mechanisms—without claiming that any is the unique cause. `UNRESOLVED` is the overall state. A separate nullable `next_action` schedules one work package on one or more compatible dependency-frontier assessments; it does not rank or erase the rest. With no exact triage the controller returns `AWAITING_HUMAN_TRIAGE`; with live assessments but no action it returns `AWAITING_HUMAN_ACTION_SELECTION`; with no effective-live assessment it returns `AWAITING_HUMAN_REASSESSMENT` without confirming anything. Only an external action bound to one exact issue and warrant can generate research questions. Research reports return to human review or internal integration; agreement and “not found” have no confirmatory effect.

The planner always derives the complete canonical `available_attack_targets` menu from the exact bound issue and warrant. Seeing a target in that menu authorizes nothing. Only an external action may select a nonempty exact subset of those target IDs, and only those targets become questions. Each question carries the selected assessments and scheduling text so a generic search cannot replace the actual criticism. AlphaXiv is designated for discovery only after that gate; no adapter here performs the retrieval. Any externally obtained rankings and summaries do not replace direct primary-source inspection, and agreement or “not found” has no confirmatory effect.

Active v2 triage is read from the verified append-only lineage in `triage/`, not from an arbitrary loose file. Each successor retains all predecessor assessments and dispositions byte-for-byte and may add criticisms, append at most one new disposition per existing assessment, or change scheduling. `DEFEATED` and `STALE_BY_BINDING_CHANGE` make a prerequisite operationally complete only for the exact current bindings; `RETAINED` keeps or reopens it. Same-binding disposition of a live assessment must follow the predecessor's authorized frontier action and embed the exact bound calibration record; staleness must embed the exact input delta. Every disposition remains a fallible human workflow judgment, never a semantic verdict. A changed input binding must be declared, must preserve the authority and research-ledger identities, and must clear the action for human reselection; old-binding dispositions cease to affect the frontier. Planning without a head is allowed only while the lineage is genuinely empty; forks, orphan records, hand-edited claims, nonterminal heads, and unselected loose files fail closed.

## First calibration

Run the authority-bound calibration and optionally create an immutable run record:

```sh
PYTHONPATH=src python tools/run_semantic_forge.py first-run \
  --authority /path/to/Creativity_Semantic_Model_CR-1.0.pdf \
  --output forge/runs/my-new-calibration.json
```

The output file is created exclusively and is never overwritten. Its parent directory must already exist. When the pinned corpus or execution contract changes, use a new output path and retain the old record only as historical evidence; a preserved run is current only if strict replay succeeds. Every run remains mechanically scoped and requires human semantic review.

## Validation

From the repository root, strict JSON parsing, validation of every local `*.schema.json`, and seed-corpus validation can be run with:

```sh
PYTHONPATH=src python tools/validate_semantic_forge.py
```

The validator resolves relative references through a registry built only from the local schema directory. An unregistered reference fails closed; validation never retrieves a schema over the network. To keep resource identity unambiguous in v0.1, nested schema identifiers and anchor or dynamic-reference mechanisms are rejected; use root identifiers and local JSON Pointer references. For another local record, pass `--instance PATH --schema SCHEMA-NAME`.

Schema validity establishes record shape only. It does not establish source fidelity, resolve an issue, validate an oracle, or prove that a physical system instantiates the model.

For record types with executable invariants, the validation CLI also runs their specialized runtime loader and reports `SCHEMA_AND_RUNTIME_VALID`. For schemas without such a loader it reports `SCHEMA_VALID_ONLY`; it never labels schema-only success as mechanical semantic validation.
