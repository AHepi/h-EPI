# Verdict

**PASS** for the candidate pilot. The snapshot is internally coherent, executable through checked CI/local paths, and tamper-evident: authority identity, anchors, transcriptions, declarations, schemas, choice registry, and Lean files are cross-pinned by content hashes, and every verdict surface keeps record integrity (`PASS`/`PARTIAL` operational status) strictly separate from mapping fidelity (`UNREVIEWED`) and bridge conformance (`BLOCKED`). No path found that emits a verdict stronger than the disclosed evidence warrants. This says nothing about CR-1.0 itself.

# Findings

No S0/S1 (release-blocker) findings.

---

**F-01 — FULL-CONFORMANCE GAP, S2 — TH-3 pilot result is relative to unconstrained ports; none of TH-3's eight source dependencies has an accepted typed mapping.**

- *Authority evidence:* `authority/transcriptions/TH-3.reviewed.txt` line 6 declares `Depends exactly on: MS-4, MS-8, SC-7, SC-8, DF-7a, DF-10, IR-2, IR-4`; mirrored in `authority/source_anchors.json` lines 160–165.
- *Repo evidence:* `formal/CREIB/Core/Model.lean` lines 11–35 define `CRModel` with only seven carriers plus `Endpoint`, `CCPResult`, `K_E`, `Retained` as unrestricted `Prop`-valued fields — no provenance (`MS-4`), no lineage (`SC-8`/`DF-7a` witnesses), no retention semantics (`SC-7`), no history-family or time-order structure. `bridge/declarations/EIB-TH3A-PILOT.json` line 29 and `EIB-TH3B-PILOT.json` line 29 disclose this verbatim (`"not adjudication of authoritative TH-3 or its dependency closure"`; `"does not establish source-level TH-3 until all declared dependencies are mapped and accepted"`); `docs/bridge/DF10_TH3_Pilot.md` lines 25–31 and `docs/bridge/CR-EIB-0.1_Bridge_Contract.md` lines 608–613 state the same; `README.md` lines 13–17 scope the Lean `PASS` as "not source-level theorem adjudication."
- *Violated invariant:* none within pilot scope. This matters for full CR-EIB conformance (contract release-gate rows, `CR-EIB-0.1_Bridge_Contract.md` lines 575–588).
- *Concrete counterexample/demonstration:* the singleton model in `formal/CREIB/Pilot/TH3Countermodel.lean` lines 32–67 sets `CCPResult := True`, `Retained := True`, `K_E := False`, so the TH-3 antecedent holds without any lineage, endpoint, or retention structure — proving only that the *eroded signature* does not force the conjunction.
- *Smallest adequate repair:* implement and accept typed mappings for `MS-4`, `MS-8`, `SC-7`, `SC-8`, `DF-7a` (the `CCPWitness` specified in contract lines 300–304), then re-prove the negated universal over the constrained model class and re-run the countermodel job.
- *Falsifier for this finding:* accepted dependency mappings under which the singleton model becomes inadmissible and the non-entailment is re-established over the constrained class.

---

**F-02 — HARDENING, S3 — Contract I09's "complete dependencies" condition vs. `proposed_inferential_status: "DER"` on records whose source dependencies are unmapped.**

- *Evidence:* invariant EIB-I09 in `docs/bridge/CR-EIB-0.1_Bridge_Contract.md` line 48 conditions DER on "complete dependencies and a replayable proof." `bridge/declarations/EIB-TH3A-PILOT.json` lines 8, 24–28 and `EIB-TH3B-PILOT.json` lines 8, 24–28 propose DER while source-declared IDs have no bridge declarations. The machine-enforced DER gate checks only `closed_proposition` and empty `expected_axioms` (`src/creib/models.py` lines 701–702); mapping-level completeness is enforced separately by `_enforce_accepted_mapping_policy` (`src/creib/verify.py` lines 448–517) and the conformance gate (lines 577–625), both dormant for candidates.
- *Assessment:* contained, because `claim_scope` rides inside each record and no report surface ever prints a DER verdict (checked `src/creib/cli.py` lines 39–63 and `src/creib/verify.py` lines 924–942: only `operational_status`, `mapping_fidelity_status`, `bridge_conformance_status` are emitted). A reader of the contract could nonetheless misread the DER label.
- *Repair:* one sentence in §2/§11 clarifying that proposed DER asserts record-level evidence only, with dependency-completeness adjudicated by the acceptance/conformance gates.
- *Falsifier:* exhibit any emitted artifact presenting DER detached from `claim_scope`; none exists in the snapshot.

---

**F-03 — HARDENING, S3 — Missing adversarial tests on four concrete invariants.**

1. *Transcription tamper end-to-end:* mutating `authority/transcriptions/*.txt` must make `verify_bundle` raise `AnchorMismatch` (evidence-binding invariant; the hash check exists at `src/creib/verify.py` lines 842–853). The closest tests only test the NFC helper and its call count (`tests/test_verifier.py` lines 232–240); no test flips transcription bytes.
2. *Extractor-version fail-closed paths:* the `pdfinfo 26.05.0` and per-anchor `pdftotext 24.02.0` pins (`src/creib/verify.py` lines 1196–1202, 2225–2231) have no mismatch tests, unlike the Lean-version pin (tested at lines 202–215).
3. *K_E-independence negative control:* no Lean check that adjoining `∀ …, K_E ↔ Retained` makes the previously refuted implication valid. This would formally demonstrate that TH-3B's countermodel depends essentially on `K_E`'s independence, guarding the MS-8/TY-1 non-conflation invariant the pilot claims to respect (`formal/README.md` line 5; `bridge/README.md` lines 41–44).
4. *Evidence-resolver inputs:* no tests for UNKNOWN polarity or CONTESTED/unreviewed evidence on the `CCPResult`/`Retained` atoms, though `resolve_atom` handles them (`src/creib/evidence.py` lines 70–72; tested paths at `tests/test_evidence.py` lines 23–74 cover only accepted inputs and scope mismatch).
- *Falsifier:* point to committed tests exercising each path; on inspection none exist.

---

**F-04 — HARDENING, S3 — Reproducibility depends on an exact mixed native toolchain.**

- *Evidence:* replay requires `pdftotext 24.02.0` with `pdfinfo 26.05.0` (provenance recorded at `authority/source_anchors.json` lines 84–88, 168–174; enforced fail-closed in `src/creib/verify.py`), plus a pinned Lean 4.33.1 commit (`src/creib/verify.py` lines 786–793). `README.md` line 36 discloses the "mixed native-tool environment" and that mismatches "fail closed instead of being treated as equivalent replays." Atypical poppler version pairing; CI omits PDF replay entirely.
- *Repair:* document acquisition of the exact binaries or ship a pinned container for `--pdf` replay. No correctness impact.
- *Falsifier:* a CI job replaying the PDF on unpinned poppler versions without failure; none exists.

# Cross-layer consistency

- **DF-10 (authority → anchor → declaration → runtime → Lean): faithful within declared partial coverage.** The supplied authority page (physical 224, footer 223) text matches `authority/transcriptions/DF-10.reviewed.txt` lines 1–5 modulo the declared transformations in `authority/source_anchors.json` lines 55–60; locator fields match (lines 24–26) and status `[R: S-BOI1, S-FOR3, S-FOR8]` matches (lines 62–72). The legacy declaration preserves the conjunction with an explicitly witnessed endpoint (`formal/CREIB/Bridge/DF10Candidate.lean` lines 12–22); the refined record's losses (role semantics, port meanings, endpoint globality, lineage evidence) are enumerated at `bridge/declarations/EIB-DF10-REFINED-CANDIDATE.json` lines 63–80 and excluded from coverage (lines 81–99). Runtime pins statement-level parity via `formal/CREIB/Audit/DeclarationBindings.lean` lines 9–59 and file/artifact hashes (`src/creib/verify.py` lines 894–921). No contradiction found.
- **DF-10 role/projection/expansion obligations: faithful and honestly scoped.** Role refinement is sort-eligibility only, explicitly not contextual causal role satisfaction (`formal/CREIB/Core/RoleRefinement.lean` lines 20–30; `bridge/README.md` lines 24–29) — consistent with, but weaker than, the source's TY-1 role doctrine, and flagged as a loss. The endpoint projection preserves `(I, t_I)` with its evidence (`formal/CREIB/Bridge/DF10Refinement.lean` lines 114–128). The model-expansion theorem (lines 156–220) is a sound relative expansion over a fixed refined base, and the record expressly denies any legacy Problem-carrier migration conservativity (declaration lines 94–97; `docs/bridge/CR-EIB-0.2_Research_Basis.md` lines 36–47) — matching the source's IR-7 strong test without overreach.
- **TH-3A: faithful as definitional unfolding of the legacy candidate.** `formal/CREIB/Pilot/TH3.lean` lines 12–24 is exactly the source's "exact unfolding of DF-10" (`authority/transcriptions/TH-3.reviewed.txt` line 5), with the eight source dependencies mirrored exactly (declaration lines 24–27; enforced by `src/creib/models.py` lines 491–492). Explicitly not source adjudication (claim_scope line 29).
- **TH-3B: faithful in logical shape, relative to unconstrained ports.** Negated-uniform-implication plus explicit finite countermodel (`formal/CREIB/Pilot/TH3Countermodel.lean` lines 72–121) matches the source's `not-entails` with identical argument sharing; the refined lift (`formal/CREIB/Pilot/TH3Refinement.lean` lines 62–127) is disclosed as auxiliary pending a separately identified refined TH-3 declaration (`bridge/README.md` lines 35–39). The evidence policy requiring an accepted explicit negative for the witness (declaration lines 37–39) is implemented four-valued in `src/creib/evidence.py` lines 85–108, with missing → `blocked`, never false. No surface contradicts the scope; the controller remains adjudicator of source-level TH-3.

# Missing adversarial tests

Highest-value only (each tied to a stated invariant; see F-03 for evidence):

1. `verify_bundle` raised `AnchorMismatch` on mutated reviewed-transcription bytes — invariant: anchor-to-transcription evidence binding.
2. `AuthorityMismatch` on `pdftotext`/`pdfinfo` version drift — invariant: native extractor parity is fail-closed.
3. Lean negative control: under `∀ …, K_E ↔ Retained`, the TH-3B implication becomes valid — invariant: port non-conflation (MS-8, TY-1) is load-bearing for non-sufficiency.
4. Evidence-resolver rejection of UNKNOWN/CONTESTED/unreviewed atoms on all three ports — invariant: only accepted, in-scope, decided evidence drives `SUPPORTED`.

# Accepted checks

Attack surfaces inspected and found adequately handled:

- **Strict JSON:** duplicate keys, floats, `NaN`/`±Infinity`, lone surrogates, deep nesting, non-string keys all rejected (`src/creib/strict_json.py` lines 12–68; tests `tests/test_strict_json.py` lines 12–56; bool-vs-int distinctness covered at lines 40–56).
- **Tamper evidence:** content-addressed anchors with domain separation (`authority/README.md` lines 5–9; digest recomputed at `src/creib/models.py` lines 331–333); coordinated rehash and extra-anchor attacks fail (`tests/test_verifier.py` lines 606–631); anchor mutation breaks declaration references (`tests/test_records.py` lines 39–56); declaration/schema/choice-registry/formal-package canonical digests all pinned (`src/creib/verify.py` lines 93–110, 257–303).
- **Path/alias handling:** per-component symlink rejection, root containment, regular-file and size limits (`src/creib/verify.py` lines 313–327); normalized relative paths (`src/creib/models.py` lines 97–102); PDF opened `O_NOFOLLOW`, hashed before parsing, parsed from a private copy (lines 1247–1272); the legacy `status` field is an alias explicitly scoped by `status_scope` (`src/creib/cli.py` lines 44–45; `README.md` line 34).
- **Fail-closed verdicts:** `PASS` requires PDF and Lean replays in one invocation (tested, `tests/test_verifier.py` lines 118–140); formal failure after PDF success yields FAIL/exit 6 (lines 142–155); fidelity `UNREVIEWED` and conformance `BLOCKED` for this bundle (lines 551–625; README lines 12–13, 34 match).
- **Lean hygiene:** pinned toolchain+commit, clean-room replay from verified bytes with scrubbed env (lines 729–767), exact empty axiom set required for all 14 reviewed declarations including refined auxiliaries (lines 770–783; `formal/CREIB/Audit/Axioms.lean` lines 6–19), statement-pinning bindings (`formal/CREIB/Audit/DeclarationBindings.lean`), `warningAsError` in every file, and a CI grep rejecting `axiom`/`opaque`/`sorry`/`admit` (`.github/workflows/bridge-pilot.yml` lines 29–42). Hand review of all proofs: every step is `rfl`/`True.intro`/structural; no hidden discharger found.
- **Acceptance gate:** accepted mappings require v2, accepted review+bridge+choices, exact exclusion-free lossless coverage, verified obligations, and accepted dependency closure, enforced and tested (`tests/test_verifier.py` lines 425–509; `tests/test_records.py` lines 151–210).
- **Known SEM-19 locator error:** TH-3 fixed at physical 230/footer 229, locked by policy and a dedicated rehash-resistant test (`authority/README.md` line 15; `tests/test_records.py` lines 58–70); verified correct against the supplied authority text.

# Uncertainty

- I could not execute Lean, Python, or CI from this static packet. Compile/replay success is asserted by CI config and an operator replay claim (`README.md` line 36); my line-level review found all proofs definitional, so failure risk is low but nonzero.
- Bounding boxes, word counts, word-snapshot digests, and page geometry in `authority/source_anchors.json` (lines 23–36, 112–122) cannot be verified from a text-only extraction; page-level locations and clause text do verify against the supplied PDF text (DF-10 on physical 224/footer 223; TH-3 on physical 230/footer 229; span 219–234 ↔ folios 218–233).
- The literal-snapshot↔reviewed-reading link is hash-pinned but human-reviewed, not machine-checked (disclosed in `docs/bridge/DF10_TH3_Pilot.md` line 8).
- The 28 omitted files (bootstrap package, prior audit reports, handoff plan) are out of scope per the packet manifest; README's "cold-start inventory PASS" and bootstrap-FAIL rows rest on unreviewed material but are self-undermining claims, not overclaims.
- The source's `not-entails` quantifies over CR-1.0's constrained model class; the pilot quantifies over unconstrained ports. The shape is faithful and the restriction is disclosed everywhere, but whether the constrained non-entailment survives accepted dependency mappings cannot be determined from this snapshot.
