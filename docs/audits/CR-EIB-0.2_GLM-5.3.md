# Verdict

**PASS** — for the deliberately scoped DF-10/TH-3 candidate bridge pilot only (its role-refinement, endpoint-projection, and relative model-expansion spine included), not for CR-1.0 and not for source-level theorem adjudication. Every layer I could trace — authority identity, page anchors, transcriptions, declarations, schemas, pinned runtime verification, and the Lean proofs themselves — is internally consistent, every emitted PASS is earned by a content-addressed check, and each fidelity limitation I found is disclosed at the point of claim; the residual findings are hardening items and accurately labeled conformance gaps, with **no S0/S1 (blocker-level) findings**.

# Findings

**F-01 — FULL-CONFORMANCE GAP — S2 — Source-level TH-3 remains unadjudicated: seven of the eight source-declared dependencies have no typed mapping at all.**
- Evidence: `authority/transcriptions/TH-3.reviewed.txt:6` and `authority/source_anchors.json:160-165` record the exhaustive dependency list MS-4, MS-8, SC-7, SC-8, DF-7a, DF-10, IR-2, IR-4; the tracked declaration set (`src/creib/verify.py:86-91`, `EXPECTED_DECLARATIONS`) contains records only for DF-10 and TH-3; `bridge/declarations/EIB-TH3A-PILOT.json:29`, `EIB-TH3B-PILOT.json:29`, `formal/README.md:3`, and `README.md:15-17` all state the limitation.
- Violated claim: none — this is the disclosed boundary; the invariant at stake is CR-1.0 §8's own rule that each dependency line is exhaustive for the displayed result.
- Failing test/exploit: attempt to derive a source-level TH-3 verdict from the bundle — no accepted typed mapping exists for MS-4/MS-8/SC-7/SC-8/DF-7a/IR-2/IR-4, so `_bridge_conformance_status` (`src/creib/verify.py:577-625`) can only ever return `BLOCKED` for the tracked set.
- Smallest adequate repair: build, review, and accept v2 mappings for the seven missing IDs (the plan already stated in `docs/bridge/CR-EIB-0.1_Bridge_Contract.md:608-613`).
- Falsified by: accepted, exact, exclusion-free v2 mappings for all eight IDs yielding conformance `PASS`.

**F-02 — FULL-CONFORMANCE GAP — S3 — The committed TH-3B countermodel trivializes `CCPResult`; no non-trivially constrained witness exists.**
- Evidence: `formal/CREIB/Pilot/TH3Countermodel.lean:40-43` (`CCPResult := … True`), versus the source proof requiring "a lineage-connected critical endpoint x" (`authority/transcriptions/TH-3.reviewed.txt:5`; authority physical page 230).
- Violated claim: none — `EIB-TH3B-PILOT.json:29` scopes the result to "the minimal unconstrained bridge signature"; the invariant at stake is IR-4 (a non-entailment countermodel must satisfy the premises' full typed constraints).
- Failing test: no committed model in which `ports.CCPResult` is non-constant; a skeptic can claim the refutation trades on the unconstrained port.
- Repair: add a second refined countermodel with a structured `CCPResult` (e.g., two-element `Content` with `CCPResult` holding for exactly one element), still with explicit `K_E` falsity.
- Falsified by: such a witness committed and replayed, or a Lean non-sufficiency proof under a DF-7a-shaped constraint.

**F-03 — HARDENING — S3 — The verifier's own sources are unpinned; the tamper-evidence chain terminates in reviewable-but-unhashed Python.**
- Evidence: every pin lives in `src/creib/verify.py:27-303` (`EXPECTED_MANIFEST`, `EXPECTED_ANCHORS`, `EXPECTED_DECLARATION_CANONICAL_SHA256`, `EXPECTED_FORMAL_PACKAGE`, …); no committed digest covers `src/creib/*.py` or `tools/verify_bridge.py` (`formal/formal-package.sha256:1-13` covers only `formal/`).
- Violated claim: none stated — the fail-closed list in `docs/bridge/DF10_TH3_Pilot.md:42-50` is record-level and each item holds; the gap is depth of the "tamper-evident" property.
- Exploit: in one commit, edit `EIB-DF10-CANDIDATE.json` and the matching `EXPECTED_DECLARATION_CANONICAL_SHA256`/policy entries in `verify.py`; `tools/verify_bridge.py` and both CI jobs pass.
- Repair: pin the verifier sources (a reviewed sha256 manifest over `src/creib` and `tools`, checked in CI) or anchor integrity externally (signed tag plus published replay transcript).
- Falsified by: a committed mechanism whose own modification fails CI.

**F-04 — HARDENING — S3 — The disclosed endpoint-witness fidelity loss has no committed divergence witness.**
- Evidence: source DF-10 evaluates `K_E` and `Retained` at `t_I`, determined by `I` (`authority/transcriptions/DF-10.reviewed.txt:3`; authority physical page 224); the bridge makes candidate-EKC truth depend on the supplied witness (`formal/CREIB/Bridge/DF10Candidate.lean:19-22`; `formal/CREIB/Core/RoleRefinement.lean:78-79`); the loss is declared at `bridge/declarations/EIB-DF10-REFINED-CANDIDATE.json:73-75`.
- Violated claim: none (declared loss; coverage `partial`, bridge status `blocked`).
- Failing test: no Lean example exhibits one interval with two admissible `EndTimeWitness` values at which the candidate EKC differs — the concrete cost that fidelity review must weigh is undocumented.
- Repair: add a two-witness model (`K_E` true at one admitted endpoint time, false at another), optionally with a witness-independence theorem under an endpoint-uniqueness hypothesis.
- Falsified by: a proof that EKC is witness-independent over the committed signature, or the committed divergence witness.

**F-05 — FULL-CONFORMANCE GAP — S3 — The committed anchor schema can represent only a single "R" source mark, so most of CR-1.0 cannot be anchored without schema evolution.**
- Evidence: `bridge/schema/source-anchor.schema.json:145-167` (assertion `mark` const `"R"`; `parse_status` enum `{parsed, scope-limited}`); the authority uses composite marks throughout (e.g., DF-4 "[R from X: S-BOI1, S-BOI7, S-CB12; …]", physical page 224; "[E/Q]", "[Q/R]", "[X]" elsewhere); the contract's own worked example records `source_mark_parse_status: unresolved` (`docs/bridge/CR-EIB-0.1_Bridge_Contract.md:98-101`), a value the committed schema rejects.
- Violated claim: none for the pilot (both anchored clauses are plain R, faithfully scoped at `source_anchors.json:62-73` and `148-158`).
- Failing test: an anchor for DF-4 cannot record the X component or `unresolved` status; an `[E/Q]` clause cannot be anchored at all (assertions `minItems 1` with `mark` const R).
- Repair: a sourceStatus v2 with a mark enum {X,R,M,Q,O} and expanded parse statuses.
- Falsified by: a committed schema version accepting the DF-4 and `[E/Q]` forms.

**F-06 — FULL-CONFORMANCE GAP — S3 — No SMT/witness-replay path exists although the contract's own release gate requires one.**
- Evidence: `docs/bridge/CR-EIB-0.1_Bridge_Contract.md:510-531` (§12), `:585` (Solver gate row), `:605-606` (S5 slice); no `solver/` artifacts in the tracked set; `README.md:17` ("SMT remains an implementation target").
- Violated claim: none (disclosed; the §14 gate is not claimed passed).
- Failing test: the §12 backend-result table has no implementing code; `NONE_THROUGH_SCOPE(N)` and `WITNESS_FOUND` verdicts can never be emitted.
- Repair: implement the minimal exporter and replay per S5, or amend the contract with an explicit pilot gate.
- Falsified by: a replayed, minimized witness, or an explicit gate amendment.

**F-07 — HARDENING — S3 — The four-valued evidence resolver is exported and tested but never invoked by the verification pipeline.**
- Evidence: `src/creib/__init__.py:3` exports it; `src/creib/verify.py` never imports `creib.evidence`; no evidence records are committed; `EIB-TH3B-PILOT.json:38-40` declares `explicit_negative_required_for_countermodel: true`.
- Violated claim: none — `bridge/README.md:41-44` correctly describes the resolver as governing *application* evidence — but the policy flag is presently declarative only.
- Failing test: the resolver's scope-mismatch and contradiction paths (`tests/test_evidence.py`) are unreachable from `verify_bundle`.
- Repair: wire a minimal evidence-record check into `verify_bundle` for TH-3B, or annotate the field as pending the evidence ledger (contract §10 BG-UD09 "ledger absent").
- Falsified by: a committed evidence record the pipeline accepts or rejects.

**F-08 — HARDENING — S3 — No known-answer vector pins the canonicalization/digest convention; the anchor-set wrapper has no published schema.**
- Evidence: `src/creib/canonical.py:31-44` — no test asserts a fixed payload→digest pair; all committed pins were self-generated by this code. Separately, `authority/source_anchors.json:1-3` (`cr-eib.source-anchor-set.v1`) has no schema under `bridge/schema/` (only five schemas exist, per `tests/test_schema_files.py:34-36`), slightly undercutting `bridge/README.md:53-55` ("The Draft 2020-12 schemas enforce record shape"); the wrapper is validated inline at `src/creib/verify.py:816-823`.
- Violated claim: none; the risks are cross-implementation identity reproduction and schema-layer parity.
- Failing test: a second implementation has no committed vector to reproduce `sha256("CR-EIB/source-anchor/v1\0" + canonical_payload)`; `source_anchors.json` cannot be schema-validated.
- Repair: commit a canonicalization vector test and a pinned source-anchor-set schema.
- Falsified by: both artifacts present and passing.

# Cross-layer consistency

**DF-10 (including its role/projection/expansion obligations): faithful but deliberately partial.** Authority → anchor is faithful: DF-10 sits at physical PDF page 224 / printed folio 223, consistent with the supplied extraction's folio chain (physical 219 = "218", physical 229 = "228") and the CR-1.0 table of contents (§2 at printed 222; 2.1 at 223); `authority/transcriptions/DF-10.reviewed.txt:1-5` matches the authority text verbatim modulo the four declared transformations, the absent source dependency line is recorded as absent rather than invented (`source_anchors.json:74-80`), and the `[R: S-BOI1, S-FOR3, S-FOR8]` mark is preserved with whole-clause scope. Anchor → declaration is faithful-as-candidate: the three conjuncts, source argument order, and the shared endpoint time are preserved (`EIB_DF10_CANDIDATE` / `EIB_DF10_REFINED`), and both deliberate deltas — the legacy independent `Problem` carrier and the witness-supplied `t_I` — are declared choices/losses with blocked, unreviewed status. Declaration → runtime verification is faithful: every record field is pinned and cross-checked, and every digest cross-checkable without recomputation agrees (manifest ↔ `authority.pdf.sha256` ↔ anchor authority blocks; anchor digests ↔ declaration references; typed-body hashes ↔ `formal/formal-package.sha256`). Verification → Lean is correct for its stated coverage: all theorems reduce to definitional unfolding or explicit finite witnesses; the model-expansion theorem genuinely quantifies over all (M, roles, base) with a kernel-checked reduct identity (`DF10Refinement.lean:190-219`), and the repo explicitly refuses the stronger Problem→Content conservativity claim, requiring an explicit transport (`DF10Refinement.lean:25-51`). The one substantive semantic delta — source `t_I` is determined by `I`, bridge EKC is witness-dependent — is real, disclosed (`EIB-LOSS-DF10-ENDPOINT-GLOBALITY`), and currently unquantified (F-04). Nothing in the chain contradicts the authority; the chain is incomplete by design and says so.

**TH-3A: faithful as a relative result.** The anchor is verbatim-faithful, including the exhaustive dependency line and the scope-limited R mark; the declaration correctly labels the Lean theorem a definitional unfolding of the *bridge candidate*; the Lean statement (`formal/CREIB/Pilot/TH3.lean:12-24`) is exactly the forward unfolding, mirroring the source's own "the implication is exact unfolding of DF-10." Incomplete with respect to the eight-dependency closure (F-01) — stated identically in `README.md`, `formal/README.md`, the pilot doc, and both claim scopes.

**TH-3B: faithful as a relative result and honestly weaker than the source.** Anchor and dependency mirror are exact. The declaration scopes the countermodel to the unconstrained signature; the Lean witness is genuine and explicit (`K_E := False`, not missing evidence — matching the declared evidence policy), and the `¬∀` shape is the correct relative rendering of "not-entails." Because the committed model trivializes `CCPResult`, it would not satisfy the source's own "lineage-connected" premise constraint, so it does not by itself establish source-level non-sufficiency — the repository states this verbatim and keeps source TH-3 unadjudicated. The chain is faithful-but-incomplete, accurately disclosed; the controller remains the final adjudicator of whether that scoping is acceptable for a candidate pilot (I judge that it is).

# Missing adversarial tests

1. **Coordinated-hash-update Lean mutation test** (invariant: the binding examples, not just hashes, carry semantic weight — EIB-I06). Mutate `EIB_DF10_CANDIDATE`'s body (e.g., drop the `K_E` conjunct) in a scratch copy, update every committed hash and `EXPECTED_*` pin, and assert the build fails via `DeclarationBindings.lean` / `Iff.rfl`. Today no test demonstrates this layer catches what hashes alone cannot.
2. **Two-endpoint divergence witness** (invariant: source `t_I` is `I`-determined; bridge EKC is witness-dependent — F-04). A model with two `EndTimeWitness` values for one interval where `K_E` holds at one and fails at the other, making the candidate EKC both true and false for the same (s,x,p,b,h,I).
3. **Non-trivial-`CCPResult` refined countermodel** (invariant: IR-4; F-02). A witness where `ports.CCPResult` is inhabited non-constantly, showing non-sufficiency survives modest constraint and is not an artifact of trivialization.
4. **Golden pdfinfo/pdftotext transcript fixture for physical pages 219-234** (invariant: anchor-replay reproducibility). The `--pdf` parsers (`_verify_active_span_geometry`, `_verify_bbox_span`) are currently tested only against invented XML; a hash-pinned capture of real tool output would let CI regression-test the parsers without the PDF.
5. **Known-answer canonicalization vector** (invariant: content-addressed identity framing — F-08). A committed payload→digest pair for `canonical_bytes`/`domain_digest` (sorted keys, separators, UTF-8 retention, domain+NUL framing) so any second verifier can reproduce anchor identity.

# Accepted checks

- **Authority identity**: `authority/source_manifest.json:5-9`, `authority/authority.pdf.sha256:1`, and both anchor authority blocks (`source_anchors.json:10-16, 98-104`) agree on digest `08ff81e8…`, 1,734,769 bytes, 286 letter-size pages, active span 219-234 ↔ 218-233 — all matching the supplied PDF header block.
- **Page anchors**: DF-10 at physical 224/printed 223 and TH-3 at physical 230/printed 229 are consistent with the extraction's folio chain and TOC; the verifier enforces the folio↔physical mapping page-by-page and rejects the known-stale 229/228 locator (`tests/test_records.py:58-70`; `src/creib/verify.py:159-164, 1065-1074`).
- **Transcription fidelity**: both reviewed readings match the authority text verbatim modulo declared transformations (math-glyph stripping, `_E/_s/_I` subscripts, `CCPResult` joining, `suffi-cient`/`CCPRe-sult` dehyphenation, literal `not-entails`); the R-mark scopes are preserved faithfully and differently where the source differs (whole clause vs "the typed separation").
- **Strict JSON and canonicalization**: duplicate keys, floats/NaN, surrogates, deep nesting, and bool-as-integer are all rejected with typed errors (`src/creib/strict_json.py`; `tests/test_strict_json.py`); the canonical profile is int/str/bool/null with sorted keys and domain-`\0` framing.
- **Content-addressed fail-closed anchors**: mutation without rehash fails the digest; rehashed mutation dangles declarations; coordinated rehash fails the pinned identity map; extra anchors are rejected even when content-addressed (`tests/test_records.py:39-57, 606-631`; `tests/test_verifier.py:606-631`).
- **Declaration/Lean/runtime parity**: parameters, binder order, sorts, and port arities of all four declarations match their Lean counterparts (`DeclarationBindings.lean:9-174` compile-pins every cited proposition); CI rejects `axiom`/`opaque`/`sorry`/`admit` (`bridge-pilot.yml:29-42`) and requires exactly the 14 reviewed empty-axiom results (`verify.py:770-783`).
- **Lean content**: every theorem reduces to definitional unfolding or an explicit finite witness; the countermodel's `K_E` falsity is an explicit interpretation, not absent evidence; no vacuity (all witness types inhabited); `EIB_TH3b_*` correctly matches the source's `not-entails` as a relative `¬∀`.
- **Status separation and fail-closed CLI**: record PASS, operational PASS/PARTIAL, fidelity UNREVIEWED, conformance BLOCKED stay separate; operational PASS requires PDF and Lean replay in one invocation; a Lean failure after PDF success yields FAIL, not PASS (`tests/test_verifier.py:106-155`); no code path emits a semantic verdict about creativity.
- **Path/alias handling**: symlinked evidence, traversal, and non-regular files rejected; the PDF is opened `O_NOFOLLOW`, hashed before parsing, and parsed only from a private verified copy (`verify.py:247-272, 313-327`).
- **Role-refinement honesty**: `RoleEligible` is eligibility-only and its loss is declared; `unrestricted_role_overlap` matches the source's roles-not-substances doctrine (§1.1); the model-expansion certificate is correctly limited to the added `EKC` symbol.
- **Mutation resistance and read-only verification**: 30+ mutation tests across anchors, declarations, schemas, formal package, typed bodies, CLI matrix, parsers, axiom audit, and Lean version; `verify_bundle` provably rewrites nothing (`tests/test_verifier.py:279-291`).
- **Reproducible bridge cold start**: fresh clone + pinned requirements + unittest + `tools/verify_bridge.py` is deterministic (no randomness, pinned tool versions, temp-dir Lean replay from verified bytes — `tests/test_verifier.py:157-189`).

# Uncertainty

- This was a static audit: I could not execute Python, Lean, pdftotext, or pdfinfo. Every "verified"/"PASS" claim was checked for internal consistency (pin cross-references, framing algorithms, proof-term review), but I could not recompute SHA-256 digests of file contents or compile the Lean package. The Lean proofs were reviewed line-by-line; all reduce to definitional steps (`Iff.rfl`, direct witnesses), but compilation itself rests on the pinned CI replay and the operator's reported run.
- Word-snapshot digests, word counts (68/116), and bbox coordinates cannot be recomputed without the PDF binary; I confirmed their consistency with the supplied `-layout` extraction and with the verifier's page-by-page folio and geometry checks that any `--pdf` replay enforces.
- The 23 omitted files — the entire `baseline/cr-1.0/bootstrap-v0.1/` tree including `validate_bootstrap.py` and its checksums — were not reviewed; the README rows "Cold-start inventory integrity PASS" and "CR-1.0 executable-calculus bootstrap FAIL" could not be verified here.
- Toolchain facts I could not confirm: availability of pdftotext 24.02.0 / pdfinfo 26.05.0 (a deliberately mixed version pair), the Lean 4.33.1 release commit `819816b2…`, and whether poppler's `pdfinfo -box` emits all five page boxes for this PDF as the geometry check requires.
- Clause-level page attribution inside the model chapter was independently confirmed only for the two anchored clauses (via the extraction's folio chain pinned at physical 219="218" and 229="228", plus the TOC); mid-chapter locators for other clauses were not needed and not verified.
- The "full operator replay succeeded" claim (`README.md:36`) is an operator report; the README itself discloses that CI cannot independently produce the same operational PASS without the PDF.
- Ambiguous authority passages bearing on future fidelity review (not on current pilot claims): the source never states whether interval endpoints are unique or how `t_I` is selected; the bridge's relational, witness-supplied reading is one defensible interpretation, and adjudicating it is precisely the disclosed, blocked mapping-review work.
