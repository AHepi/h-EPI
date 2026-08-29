# Verdict

**PASS** (for the candidate DF-10/TH-3 bridge pilot only — not a verdict on CR-1.0). The chain authority PDF → content-addressed anchor → transcription → candidate declaration → pinned Lean body → replayed axiom audit is internally consistent, executable as claimed, and fail-closed: every operational `PASS` requires byte-exact PDF and pinned-Lean replay in the same invocation, while mapping fidelity and bridge conformance stay independently `UNREVIEWED`/`BLOCKED`, and every semantic limitation (opaque ports, unmapped TH-3 dependency closure, non-conservative legacy migration) is disclosed rather than hidden. No S0/S1 defects were found; the remaining findings are one accurately disclosed full-conformance gap (S2), one S2 test-coverage hardening item on the word-snapshot binding path, and S3 hardening items, none of which permit an unjustified verdict about CR-1.0. The controller remains the final adjudicator and should re-execute the replays, since this audit is static.

# Findings

There are **no S0 or S1 findings**. Ordered by severity:

---

**F-01 | FULL-CONFORMANCE GAP | S2 — TH-3's source-declared dependency closure is recorded but unmapped; DF-7a lineage content is absent from the executable layer**
- **Evidence:** CR-1.0 authority PDF physical p. 230 (printed folio 229), "Depends exactly on: MS-4, MS-8, SC-7, SC-8, DF-7a, DF-10, IR-2, IR-4"; `authority/transcriptions/TH-3.reviewed.txt:6`; mirrored in `authority/source_anchors.json:160-166` and `bridge/declarations/EIB-TH3A-PILOT.json:25` / `EIB-TH3B-PILOT.json:25`; `CCPResult`, `K_E`, `Retained` are opaque ports (`formal/CREIB/Core/Model.lean:23-28`, `formal/CREIB/Bridge/DF10Refinement.lean:16-24`); loss record `EIB-LOSS-DF10-LINEAGE-EVIDENCE` (`bridge/declarations/EIB-DF10-REFINED-CANDIDATE.json:76-79`); scope disclaimers `EIB-TH3A-PILOT.json:29`, `EIB-TH3B-PILOT.json:29`, `bridge/README.md:35-39, 46-51`, `docs/bridge/DF10_TH3_Pilot.md:25-31`.
- **Violated claim/invariant:** none in the limited pilot — this is the disclosed gap against CR-EIB full conformance (CR-1.0's own IR-6/IR-8 transitive-closure discipline cannot be discharged while DF-7a, SC-7/SC-8, MS-4/MS-8, IR-2/IR-4 are unmapped).
- **Concrete failing configuration:** setting `mapping_status: "accepted"` on `EIB-TH3B-PILOT.json` fails today with `PolicyViolation` ("unresolved source_declared dependency") via `src/creib/verify.py:511-517` — the gate correctly blocks promotion.
- **Smallest adequate repair:** map the eight dependency IDs (or a refined TH-3 declaration for the role-refined layer, currently only an "auxiliary" lift per `bridge/README.md:35-39`).
- **Falsified by:** accepted typed mappings for MS-4, MS-8, SC-7, SC-8, DF-7a, DF-10, IR-2, IR-4 existing and passing the acceptance gates at `src/creib/verify.py:448-517`.

---

**F-02 | HARDENING | S2 — The anchor word-snapshot binding path has zero mutation coverage in the test suite**
- **Evidence:** the anchor loop that binds authority text to anchor identity is `src/creib/verify.py:159-174` (`_verify_bbox_span`: word-center selection, word count, framed digest); the only tests of `_verify_bbox_span` pass `anchors=[]` and mutate only footers (`tests/test_verifier.py:545-559`); the anchor-bearing path is otherwise exercised only by the operator `--pdf` replay, which CI never runs (`.github/workflows/bridge-pilot.yml:22-28`; disclosed at `README.md:36`).
- **Violated invariant:** "Source anchoring: Any source-text or locator mutation changes the content hash and invalidates the mapping" (`docs/bridge/CR-EIB-0.1_Bridge_Contract.md:547-548`).
- **Concrete failing test (missing):** build bbox XML containing the DF-10/TH-3 anchor words (as `tests/test_verifier.py:55-64` does for folios), mutate one in-bbox word's text or coordinates, and assert `AnchorMismatch`. Today a regression in `_select_word_centers` (`src/creib/verify.py:1054-1062`) or the framing string (`:171`) would ship with all tests green.
- **Smallest adequate repair:** add the mutation test above (plus one for the `word_count` mismatch branch).
- **Falsified by:** such a test existing and passing, or a demonstration that the anchor-bearing path is covered elsewhere.

---

**F-03 | HARDENING | S3 — Path-traversal and symlinked-component defenses are claimed but untested**
- **Evidence:** `docs/bridge/DF10_TH3_Pilot.md:47-50` claims "path traversal … rejected or blocked"; the defenses are `_safe_relative` (`src/creib/models.py:97-102`) and `_safe_repository_file` (`src/creib/verify.py:313-327`); tests only exercise a symlinked PDF (`tests/test_verifier.py:561-571`) and a safe-but-wrong path (`:577`, `:377`).
- **Violated invariant:** evidence paths never escape the repository root.
- **Concrete failing test (missing):** declaration `typed_body.path` = `"../formal/CREIB/Bridge/DF10Candidate.lean"` and an absolute path → `RecordError`; a symlinked path component → `PolicyViolation`.
- **Smallest repair:** three unit tests. **Falsified by:** their existence.

---

**F-04 | HARDENING | S3 — The verifier's pin tables are an unbound trust root**
- **Evidence:** all tamper-evidence terminates in `EXPECTED_*` constants (`src/creib/verify.py:27-303`); the trust-boundary table (`docs/bridge/CR-EIB-0.1_Bridge_Contract.md:57-68`) does not list the Python verifier or its pins as a trusted component.
- **Violated invariant:** tamper-evidence is relative to reviewed pins, but the pins themselves have no in-repo digest or documented review step.
- **Concrete exploit:** edit `bridge/declarations/EIB-TH3A-PILOT.json` *and* the matching `EXPECTED_DECLARATION_POLICY`/`EXPECTED_DECLARATION_CANONICAL_SHA256` entries (`src/creib/verify.py:105-110, 211-232`); every check passes and nothing in the repository detects the coordinated edit.
- **Smallest repair:** record the verifier source digest in the handover/audit ledger and name it in the trust table.
- **Falsified by:** any documented mechanism binding `src/creib/verify.py`'s pins to a reviewed artifact.

---

**F-05 | HARDENING | S3 — Mutually inconsistent pinned extractor versions impair cold-start replay**
- **Evidence:** anchors pin `pdftotext 24.02.0` and `pdfinfo 26.05.0` (`authority/source_anchors.json:84-88, 168-174`); `src/creib/verify.py:196-202, 218-231` enforces both exactly; a single poppler build normally ships both tools at one version, so an operator holding the anchor's pdftotext release still fails the pdfinfo check. Direction of failure is closed (disclosed at `README.md:36`: "Native extractor or compiler version mismatches fail closed").
- **Violated claim:** "reproducible cold-start behavior" is materially harder than the pinned-hash discipline alone suggests.
- **Concrete failing scenario:** stock poppler 24.02 for both tools → `AuthorityMismatch` ("pdfinfo version differs") despite matching the anchor's extractor provenance.
- **Smallest repair:** publish a reproducible toolchain image/digest for the mixed pair, or re-anchor with one consistent poppler build (creating new anchor identities, per `authority/README.md:13`).
- **Falsified by:** a documented, obtainable environment in which a fresh operator reproduces the full `--pdf --lean` replay.

---

**F-06 | FULL-CONFORMANCE GAP | S3 — Evidence-record ingestion is not wired into verification**
- **Evidence:** `src/creib/evidence.py:56-108` implements four-valued resolution (missing → `BLOCKED`, never false; explicit negative required for the TH-3b witness), tested at `tests/test_evidence.py`, and declaration `evidence_policy` fields are pinned — but `verify_bundle` (`src/creib/verify.py:796-945`) loads no evidence records; the contract marks the ledger absent (`docs/bridge/CR-EIB-0.1_Bridge_Contract.md:446, 462`).
- **Violated claim:** none in the pilot (no runtime verdict depends on evidence); disclosed gap for CR-EIB.
- **Concrete gap:** an "available, accepted, positive" K_E record can never currently reach the resolver through the verifier.
- **Smallest repair:** an evidence-record loader + resolver integration once evidence bundles exist. **Falsified by:** evidence records flowing through `verify_bundle`.

---

**F-07 | HARDENING | S3 — Documentation/diagnostics drift: contract §4 record shape vs. implemented schemas; fidelity summary collapses while any v1 record exists**
- **Evidence:** `docs/bridge/CR-EIB-0.1_Bridge_Contract.md:86-133` (YAML-ish sample with different field names) vs. implemented `bridge/schema/declaration.schema.json` / `declaration-v2.schema.json`; `_mapping_fidelity_status` returns `UNREVIEWED` whenever any declaration is v1 (`src/creib/verify.py:551-574`), so the v2 record's review state cannot surface until all records migrate (conservative, but masks `in-review`/`rejected` states).
- **Violated claim:** documentation accurately describes the implemented record format.
- **Concrete failure:** a reader implementing records from contract §4 produces files the verifier rejects.
- **Smallest repair:** mark §4 as a superseded sketch; aggregate per-record review states instead of schema-version gating.
- **Falsified by:** corrected docs / per-record fidelity aggregation.

# Cross-layer consistency

**DF-10 (definition; role-refinement, endpoint projection, relative model-expansion obligations): FAITHFUL at the typed-surface level, INCOMPLETE semantically, NOT contradicted.**
Authority → anchor: the locator arithmetic (physical 224 ↔ folio 223; active span 219–234 ↔ 218–233, `authority/source_manifest.json:10-13`) matches the supplied PDF text exactly, and `authority/transcriptions/DF-10.reviewed.txt:1-5` is verbatim against CR-1.0 authority PDF physical p. 224 (title, three-conjunct formula, prose, `[R: S-BOI1, S-FOR3, S-FOR8]` tag), with declared transformations (`authority/source_anchors.json:55-60`) matching the observable glyph/subscript/joining differences; source-declared dependencies are correctly empty. Anchor → declaration: both candidates bind the anchor digest, mirror the empty source deps (enforced at `src/creib/models.py:491-492`), and preserve argument order, content identity, conjunction, and the shared endpoint time (`EIB-DF10-REFINED-CANDIDATE.json:45-62`); the role refinement tracks the PDF's TY-1 "semantic roles of contents" but only as sort eligibility (disclosed loss `:63-67`), the endpoint is relational with an explicit witness (loss `:72-75`), and DF-7a lineage evidence is absent (loss `:76-79`). Declaration → Lean: `EIB_DF10_CANDIDATE` (`formal/CREIB/Bridge/DF10Candidate.lean:12-22`) and `EIB_DF10_REFINED` (`DF10Refinement.lean:79-91`) state exactly the source-shaped conjunction; fold/unfold (`:93-108`), projection (`:114-128`), legacy transport (`:134-149`), and the canonical EKC expansion with reduct identity (`:180-220`) are definitional and shape-pinned at compile time by `formal/CREIB/Audit/DeclarationBindings.lean`. Lean → replay: bytes, toolchain (v4.33.1 + commit), and the empty axiom set are pinned (`src/creib/verify.py:257-303, 729-793`). The model-expansion obligation satisfies IR-7's *shape* only relative to the refined opaque-port base, and the legacy Problem→Content migration is explicitly excluded from any conservativity claim (`EIB-EXC-DF10-LEGACY-MIGRATION`, `:94-97`) — consistent with CR-1.0 IR-7's refusal to treat substantive modules as conservative abbreviations.

**TH-3A (implication direction): FAITHFUL at port level, INCOMPLETE, NOT contradicted.**
The source direction `EKC → CCPResult ∧ K_E ∧ Retained` (CR-1.0 PDF physical p. 230) is mirrored exactly by `EIB_TH3a_unfold` (`formal/CREIB/Pilot/TH3.lean:12-24`) as a definitional unfolding of the legacy candidate, matching the source's own "exact unfolding of DF-10" proof strategy. Incomplete: the eight source-declared dependencies are recorded and mirrored (`EIB-TH3A-PILOT.json:25`) but unmapped, and the claim scope says adjudication is not performed. No bridge statement conflicts with the PDF clause.

**TH-3B (non-sufficiency direction): FAITHFUL at port level, INCOMPLETE, NOT contradicted.**
The pilot's `¬∀` (`formal/CREIB/Pilot/TH3Countermodel.lean:98-121`) uses an explicitly inhabited singleton `CRModel` with `CCPResult = True`, `Retained = True`, `K_E = False` (`:32-48`) — non-vacuous (the model class is inhabited; the witness is concrete), matching the source proof's "retained but does not satisfy the independently interpreted K_E" (PDF p. 230 / `TH-3.reviewed.txt:5`), with the evidence policy requiring an accepted explicit negative before any runtime witness (`EIB-TH3B-PILOT.json:39`; `src/creib/evidence.py:85-108`). It refutes uniform sufficiency only over the unconstrained port signature — strictly weaker than adjudicating source TH-3 over the DF-7a/SC-constrained model class — which is disclosed at `EIB-TH3B-PILOT.json:29`, `bridge/README.md:41-44, 46-51`, and `formal/README.md:20-23`. The refined lift (`TH3Refinement.lean:97-127`) is correctly labeled auxiliary pending a separately identified refined declaration.

# Missing adversarial tests

1. **Word-snapshot text mutation** (invariant: any source-text mutation changes the anchor hash — contract §13.1): feed `_verify_bbox_span` bbox XML containing the DF-10/TH-3 anchors with one in-bbox word's text or coordinates mutated; expect `AnchorMismatch`. Currently only footer mutations with `anchors=[]` (`tests/test_verifier.py:545-559`). (F-02.)
2. **Path traversal / symlinked components** (invariant: evidence paths never escape the repo): `"../…"`, absolute paths, symlinked path components against `_safe_relative`/`_safe_repository_file`. (F-03.)
3. **Lean negative controls for the endpoint-witness coverage** (invariants: EIB-C-TY03; losses `EIB-LOSS-DF10-ENDPOINT-GLOBALITY` and exclusion `EIB-EXC-DF10-NO-ENDPOINT-WITNESS`): a `CRModel` with `Endpoint := fun _ _ => False` (witnessing that the no-endpoint exclusion is a real, non-vacuous coverage boundary) and an interval with two endpoint times (witnessing non-uniqueness).
4. **Evidence-resolution gaps** (invariant: missing evidence is UNAVAILABLE, never false): missing/unaccepted `CCPResult` or `Retained` evidence must yield `BLOCKED` — only missing `K_E` and scope mismatch are currently tested (`tests/test_evidence.py:28-74`).
5. **Axiom-audit discrimination** (invariant: empty expected-axiom set): feed a `'X' depends on axioms: [propext]` line into `_verify_axiom_audit` and expect mismatch; current tests only add/remove/duplicate "does not depend" lines (`tests/test_verifier.py:217-230`).

# Accepted checks

- **Authority identity chain:** manifest/checksum/anchor cross-consistency (SHA-256, 1,734,769 bytes, 286 pages, letter geometry, active span) matches the supplied PDF header and page footers; drift-tested (`tests/test_verifier.py:633-639`).
- **Page anchors:** DF-10 at physical 224/folio 223 and TH-3 at physical 230/folio 229 match the supplied PDF text; the folio arithmetic is enforced (`src/creib/verify.py:131-163`) and the stale SEM-19 locator (229/228) is rejected even when rehashed (`tests/test_records.py:58-70`).
- **Transcription fidelity:** both reviewed readings are verbatim against the packet's PDF text (DF-10 formula/prose/tag; TH-3 dehyphenated title, formula, proof, dependency line, entitlement line), with declared transformations matching the observed differences; UTF-8/NFC/LF/final-newline and hash pinning enforced (`src/creib/verify.py:339-347, 842-853`).
- **Source-status and dependency discipline:** `source_inferential_status` stays `null` (`tests/test_records.py:94-99`); TH-3's R-mark is parsed scope-limited to "the typed separation," honestly reflecting the PDF wording; declaration `source_declared` must mirror the anchor exactly (`src/creib/models.py:491-492`).
- **Semantic translation and quantifiers:** the three conjuncts, argument order, shared `x`, and shared `t_I` are preserved; TH-3's non-entailment is correctly formalized as `¬∀(premises → conclusion)` with a concrete typed witness; the source's "full conjunction ≡ EKC" is the fold/unfold theorem.
- **Strict JSON / canonicalization / hashes:** duplicate keys, floats, NaN/Infinity, surrogates, nesting depth, and bool/int coercion are rejected (`src/creib/strict_json.py`; `tests/test_strict_json.py`); canonical digests pin schemas, choice registry, and all four declarations; coordinated anchor rehashing and extra anchors are rejected (`tests/test_verifier.py:606-631`).
- **Vacuity / assumptions in Lean:** no `sorry`/`axiom`/`opaque` (CI grep, `.github/workflows/bridge-pilot.yml:29-42`; empty axiom audit replayed exactly, `src/creib/verify.py:770-783`); the countermodel explicitly inhabits `CRModel`, so the `¬∀` results are witnessed, not vacuous; all pilot theorems are defeq and labeled as definitional/relative.
- **Declaration/schema/runtime parity:** v1/v2 schemas match the Python validators and committed instances; Lean statement shapes are compile-time pinned by `DeclarationBindings.lean:9-174`; typed-body and non-leaf formal drift are rejected (`tests/test_verifier.py:590-604`).
- **Adversarial record validation:** binder reordering, hidden arguments, unresolved choices, duplicate obligation IDs, obligation-kind removal, artifact hash/path/symbol drift, mapping/symbol/path/command promotion, and v2 acceptance gating (exact exclusion-free coverage, no losses, accepted choices and dependency closure) are all tested fail-closed (`tests/test_records.py`, `tests/test_verifier.py`, `tests/test_schema_files.py`).
- **Replay hygiene and status separation:** Lean builds from verified bytes in a clean temp directory with exact version/commit tokens (`tests/test_verifier.py:157-215`); PDF is hashed before parsing through a private copy with symlink/O_NOFOLLOW defenses; `operational_status: PASS` requires both replays together, and a Lean failure after PDF success yields `FAIL`, not `PASS` (`tests/test_verifier.py:118-155`); conformance is structurally `BLOCKED` in this snapshot.

# Uncertainty

- **No execution was performed.** All digests (word snapshots, reviewed readings, canonical digests, formal-package hashes, the Lean 4.33.1 commit `819816b2…`, and the claimed passing operator replay) are accepted only as internally consistent with the repository's own claims; the controller should re-run `tools/verify_bridge.py --pdf … --lean`, the unittest suite, and `lake build`.
- **Word counts and geometry are not statically reproducible.** The anchor word counts (68 for DF-10, 116 for TH-3) exceed a plain-token count of the reviewed readings because pdftotext `-bbox` fragments styled mathematical glyphs; this is plausible and consistent with the declared transformations, but I could not reproduce it without the PDF. Likewise, tight/region bboxes and the footer region are plausible and internally validated but unverifiable here. My verbatim transcription check was performed against the packet's `-layout` extraction, not raw PDF bytes.
- **Omitted evidence.** 28 files were intentionally omitted (bootstrap package, prior CR-EIB-0.2 audits, handover, SEM-19 ledger). `README.md:10`'s "Cold-start inventory integrity PASS" and `README.md:36`'s "full operator replay succeeded" are therefore unverified claims about layers/executions outside this snapshot; the CI's inability to replay the PDF is, however, accurately disclosed.
- **Toolchain plausibility.** The pdftotext-24.02.0 / pdfinfo-26.05.0 pairing is unusual for a single poppler build; it is consistent with the disclosed "mixed native-tool environment" and fails closed, but I cannot confirm such a pair is obtainable (F-05).
- **Ambiguous PDF passages.** None material to DF-10/TH-3. The formal status of `t_I` (endpoint totality/uniqueness) is genuinely underspecified in CR-1.0; the bridge's relational, witness-supplied reading is a disclosed interpretation (EIB-C-TY03), not a contradiction. The relative model-expansion theorem engages only the port base, not MS-1–MS-9 model structure — disclosed, but its strength should not be over-read.
- **Version-label drift** between the CR-EIB-0.1 contract and the 0.2 implementation (F-07) could not be reconciled against the omitted handover document, which was not supplied and was not treated as authority.
