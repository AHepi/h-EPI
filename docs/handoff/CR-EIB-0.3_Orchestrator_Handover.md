# CR-EIB-0.3 orchestrator handover

## Mission and authority boundary

Continue the CR-1.0 work through the Semantic Model Forge without treating a test suite, research result, formal model, or proof assistant as a semantic authority. The sole semantic and formal authority remains the externally supplied PDF `Creativity as Explanatory Self-Correction`, Model CR-1.0:

```text
SHA-256: 08ff81e848fea976b558345402d85723173be8f40f1041fb00d6267f1e026b8b
Bytes:   1734769
Pages:   286
```

The active formal span remains physical PDF pages 219–234, printed folios 218–233. Repository prose, corpus annotations, research papers, source interpretations, project imports, executable fixtures, countermodels, and Lean declarations remain subordinate artifacts with separately typed status.

No source-level creativity theorem has been proved or refuted. No SMF run has established that a formalization is faithful to CR-1.0.

## Repository state

Repository: `https://github.com/AHepi/h-EPI`

Working branch: `codex/popperian-semantic-forge`

Base commit and current `HEAD` before publication:

```text
3ad132846e788b9775762d87398dc5d1f2edfdb4
```

This increment is present as uncommitted working-tree changes. It has not been staged, committed, pushed, or published. Preserve unrelated history and use the repository's safe publication workflow only after explicit authorization.

The two GitHub Actions workflows on base commit `3ad1328` were inspected on 2026-09-03 and were successful:

| Workflow | Run | Result |
|---|---|---|
| Bootstrap integrity | <https://github.com/AHepi/h-EPI/actions/runs/33283166037> | Success; 13 seconds. |
| Bridge pilot | <https://github.com/AHepi/h-EPI/actions/runs/33283166028> | Success; evidence records, Lean replay, and container replay smoke jobs all succeeded. |

Those remote results concern the published base, not the uncommitted SMF increment.

## Independent status surfaces

| Surface | Current result | Boundary |
|---|---|---|
| Exact authority binding in SMF run | `MECHANICALLY_VALID` | Digest, byte length, page structure, and pinned source anchors only. |
| SMF run | `RUN_COMPLETE` | All scheduled calibration mechanics returned and the record was written. |
| SMF epistemic status | `UNRESOLVED` | No mechanical result supplies a semantic disposition. |
| SMF review status | `AWAITING_HUMAN` | Both `semantic_verdict` and `human_disposition` are null. |
| Adaptive inquiry route | `AWAITING_HUMAN_TRIAGE` | No human failure-locus triage was supplied; zero research questions were generated. |
| Naive disconnected repair | `NO_HARDENING` | Existential erasure changes no old-language fixture classification. |
| Connected causal-role proposal | `UNRESOLVED` | A structurally eligible external warrant is only a route candidate; it does not authorize live research without human triage. |
| SMF formalization readiness | `BLOCKED` | The role primitive, positive tacit witness, source fork, and review records remain open. |
| Local CR-EIB operational integrity | `PARTIAL` | Exact PDF replay succeeded; no local Lean executable was available. |
| CR-EIB mapping fidelity | `UNREVIEWED` | No human review has accepted the source-to-formal mapping. |
| CR-EIB bridge conformance | `BLOCKED` | Operational checks cannot promote mapping or full-model status. |
| CR-1.0 bootstrap gate | `FAIL` | Package integrity passes, but declaration-level source mappings and typed bodies remain incomplete. |

The historical CR-EIB-0.2 handover records a mixed-environment operational `PASS` in which PDF and Lean were replayed together. That historical replay is compatible with the present local `PARTIAL`; the status is environment- and invocation-specific.

## What this increment built

### Semantic Model Forge architecture

`docs/forge/SMF-0.1_Architecture.md` defines a problem-led, criticism-first loop. It separates five claim kinds:

| Claim kind | Use |
|---|---|
| `SOURCE_AUTHORITY` | A digest- and locator-bound proposition attributed to CR-1.0. |
| `EXTERNAL_SOURCE_REPORT` | A bounded report about another source, without authority over CR-1.0. |
| `SOURCE_INTERPRETATION` | A contestable source reading or source-to-model crossing. |
| `PROJECT_IMPORT` | An added semantic, causal, methodological, or physical premise. |
| `FORMAL_CONSEQUENCE` | A theorem or countermodel relative to an exact dependency set. |

Operational fields are not semantic claims. No parser, search provider, model, test, vote, or proof changes a claim kind.

The architecture makes human semantic triage explicit. A proposed counterexample may be diagnosed as `CANDIDATE_DEFECT`, `AUXILIARY_DEFECT`, `TEST_DEFECT`, `OUT_OF_SCOPE`, or `UNRESOLVED`; no diagnosis has an automatic default. The broader revision dispositions remain human-only and defeasible.

### Research gate

Research is permitted only when all of the following are present together: a human-triaged external uncertainty, a live decision it could change, at least two distinct rivals, a possible falsifier for every rival, an expected discriminator, a bounded admissible source scope, and a stop condition. Internal modelling questions do not generate external searches. A failed test cannot locate its own failure locus.

AlphaXiv is the default contemporary discovery channel, as requested. The provider is replaceable and its output is never an oracle. Consensus is optional only as an independent cross-check. Search results may generate criticisms or locate primary records; they cannot confirm a model, aggregate into semantic confidence, or silently become CR-1.0 premises.

The retained engineering basis is recorded in `docs/forge/SMF-0.1_Research_Basis.md` and the v2 ledger at `forge/research/SMF-RESEARCH-2026-09-03.json`. The ledger contains eight source-only bounded reports, eight separate digest-bound `PROPOSED` project-use records, and zero engineering decisions; v2 rejects any decision record until an external human-attestation trust boundary exists. It uses CEGAR only as a counterexample/representation triage pattern, competency questions as fallible discriminators, metamorphic testing for local relations under an oracle problem, and contemporary AlphaXiv work as warnings about regression-derived oracles, model-judge overacceptance, and definition bloat. It does not import Bayesian selection, posterior truth warrant, convergence, majority judgment, or synthetic ground truth into the epistemic logic. Primary-source bytes are not archived by the ledger; exact version locators, inspection provenance, and bounded reports are preserved.

### Dynamic challenges and non-scalar hardening

`src/creib/forge/` implements strict immutable records for rivals, issues, research warrants, minimal-pair challenges, hardening assessments, and formalization readiness. The core includes fourteen seed challenge constructors, while runtime challenges may introduce a new stable snake-case defect family without changing the enum.

The seed corpus at `forge/corpus/cr-1.0-seed.json` contains ten provisional minimal-pair challenges and ten unresolved external issues. Challenge construction is always typed `project_import`; its annotations currently use only `source_interpretation` and `project_import`. There is no reviewed `source_authority` annotation in the seed. Every annotation's editorial `title` and `boundary_note` is separately marked `unreviewed_non_authoritative` with semantic effect `none`; arbitrary prose changes cannot alter typed mechanics. Every source reference resolves to an enumerated CR-1.0 source record and binds its exact subject digest, basis, relationship, locator, pages, use, and identifier inventory. Annotation coverage is one-to-one and duplicate identifiers fail closed. These checks establish record integrity, not faithful interpretation.

The hardening comparison is conjunctive and non-scalar. A candidate cannot receive `HARDENING_UNREFUTED` merely by passing tests or adding clauses. The current record exposes a named exclusion or resolved ambiguity, preservation dimensions, regressions and criticisms, permitted justification kinds, witness references, preservation-review references, and a human-decision reference only as diagnostics. Those legacy fields are not sufficient for positive promotion: the runtime keeps it unavailable pending schema and resolver support for the complete theory identities, both global non-broadening relations, exact fibers, non-vacuity, intended-model, dependency, mapping, and preservation obligations summarized below. Known loss yields `NO_HARDENING`; missing adjudication yields `UNRESOLVED`. A structurally eligible external warrant also remains `UNRESOLVED` until human failure-locus triage authorizes the research route. When no gain is claimed, `NO_HARDENING` does not assert preservation dimensions merely to obtain a negative status.

Formalization readiness defaults to `BLOCKED`, including when a caller reports no known blockers but supplies no review record. `PROVISIONALLY_READY` is vocabulary for a future ledger-backed decision path; the current implementation cannot emit it from plain references or mechanical results.

### Adaptive inquiry and append-only question history

`src/creib/forge/inquiry.py` and `tools/run_semantic_inquiry.py` implement the additive SMF-0.3 inquiry protocol. A plan binds the exact calibration bytes and run contract, candidate, challenge, fixture, evaluator, observation, issue, recomputed warrant, human triage if supplied, and research-ledger record and file digests. The runtime does not fabricate triage. With none supplied, the live plan returns `AWAITING_HUMAN_TRIAGE`, zero questions, `UNRESOLVED`, and a null semantic verdict.

After exact declared-human triage, the reducer can route to internal harness work, internal model work, CR authority review, out-of-scope handling, policy blocking, bounded external research, human report review, or internal integration. The ledger binding includes `created_on` and `as_of_date`; triage cannot predate ledger creation, each critical question binds the exact triage date, and no event may predate its question's triage. Critical questions are content-addressed from exact rival falsifiers. Current-case transitions must address a question in the exact inventory regenerated from the active run, ledger, triage, and origin head, while historical cases remain valid under their own immutable bindings. Events form a checked hash chain with explicit heads, legal actor/transition constraints, nondecreasing dates, and atomic no-clobber publication. A route/event allowlist prevents continued research from `POLICY_BLOCKED` and `INTERNAL_INTEGRATION_REQUIRED`. A later source report is embedded as a strict standalone snapshot targeted at its active question. Agreement cannot promote a claim, and an unsuccessful search leaves the question open because protocol v1 has no unauthenticated exhaustion transition. See `docs/forge/SMF-0.3_Adaptive_Inquiry_Protocol.md`.

### Mathematical target

`docs/forge/SMF-0.2_Mathematical_Target.md` fixes a provisional target-neutral signature and a precise model-class question: whether semantic role relations are implicitly determined by a declared neutral reduct and held-fixed auxiliaries.

For a fixed candidate theory \(T\), typed target roles \(Q_{role}\), control signature \(\Gamma\), and a declared family-level or history-local scope \(\tau\), the uniqueness obligation is:

\[
\operatorname{ID}_T(Q_{role}\mid\Gamma;\tau)\;:\Longleftrightarrow\;
\forall M,N\models T,
\left(M\!\upharpoonright_\Gamma=N\!\upharpoonright_\Gamma
\Rightarrow
\operatorname{RView}_{\tau}^{M}(Q_{role})
=\operatorname{RView}_{\tau}^{N}(Q_{role})\right).
\]

A localized same-reduct role-relabel twin refutes implicit determination for that encoded theory. A positive result additionally requires satisfiability and expansions for a nonempty, versioned intended-base registry; bounded failure to find a twin proves none of these. The common signatures, transports, localization formulas, premises, and dependencies are immutable and digest-bound. The note separates intra-candidate rival expansions from inter-interpretation forks and distinguishes two hardening axes—old-result restriction and localized role-fiber narrowing—under conjunctive successor non-vacuity, old-result non-broadening, global role-assignment non-broadening, intended-model retention, exact-fiber, mapping, dependency, and preservation obligations.

The neutral signature and all reification choices are `PROJECT_IMPORT` until a reviewed source mapping exists. No current result licenses Lean extraction for the full CR target.

## Preserved first run

Run record:

```text
forge/runs/SMF-CALIBRATION-CR-1-0-001.4219efce.json
SHA-256: ac4737d3647ccf4f5f636e544fc4dd762f2fb9c446d1c02fa032417962899943
Bytes:   25931
Run contract: dc518e4ad9534b0822ffcb3ddb471a3c7d863d8b22e7d11f8fa6d497db1344a0
```

Seed corpus:

```text
forge/corpus/cr-1.0-seed.json
SHA-256: 4219efceb5502aa8b9209884ec1d22533d6eb049277c8ae3354d08e38f7c47a6
```

Research ledger:

```text
forge/research/SMF-RESEARCH-2026-09-03.json
File SHA-256: 9c70fb98a460de146a60eb4f7e66f7255fa189449d177fc5f951fcd0c6d11d56
Ledger record: 3b49afff0d0f83a1ccc4a74dbfd662a5507074b6490a47870f361751420271bf
```

No-triage inquiry plan:

```text
forge/plans/SMF-AIP-2d589a64.no-triage.json
Plan ID: AIP:2d589a644ec7a39d586d98fc612d16ada752059d320fb022726aa80d571031e4
File SHA-256: fd9edbee175ed3e23c1c5e0d3e92c132e75b7a94f2bb47d64a133ef473719693
```

Ten superseded run records and five superseded inquiry plans are retained, with exact hashes and invalidation reasons, under `forge/history/`. They are not active replay or append targets.

The CLI verifies the exact authority and strict-loads the complete corpus before producing the run. `--output` uses exclusive creation and refuses to overwrite an existing record.

The calibration intentionally tests `SMF-FIXTURE-TYPED-ROLE-PROJECTION`, not CR-1.0. The fixture admits both a grounded role assignment and a labels-only contrast case because it checks only typed events and typed role predicates while deliberately omitting the SC-2/SC-3 causal-use and matched-counterfactual constraints. This mechanically records a criticism candidate about only the weak fixture projection.

The naive revision `SMF-0.1-VACUOUS-GROUNDING` adds an unconstrained `RoleGrounded` predicate. Both truth-value expansions preserve every fixture classification; after existential erasure its old-language shadow is unchanged. The harness therefore reports `NO_HARDENING` rather than mistaking a new predicate name for semantic strength.

Given its supplied, reviewable `INTERNAL` classification, the internal erasure issue produces no research warrant. The external role-realization seed issue mechanically produces one proposed AlphaXiv warrant and four possible falsifier-first attack targets for the local operational-discrimination and distributed network-role rivals. The live adaptive plan does not activate them: without human triage it generates zero questions. The connected proposal reports zero excluded countermodels and no reviewed preservation; it cannot be promoted.

## Verification performed on 2026-09-03

| Check | Result |
|---|---|
| `PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v` | 261 tests passed. |
| `PYTHONOPTIMIZE=1 PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v` | 261 tests passed. |
| Offline schema and specialized runtime validation | Seven schemas loaded; corpus, research ledger, and current run reported full specialized runtime validation. The standalone no-triage inquiry plan reported intrinsic-record validation only; transition authorization additionally requires exact contextual regeneration. |
| Bootstrap quarantine validator | Package integrity `PASS`; CR-1.0 bootstrap gate remains `FAIL`. |
| Bridge verifier with exact PDF | Authority checked; records, schemas, choice registry, and formal package `PASS`; operational `PARTIAL`; mapping `UNREVIEWED`; bridge `BLOCKED`. |
| First SMF calibration with exact PDF | `RUN_COMPLETE`, `MECHANICALLY_VALID`, `UNRESOLVED`, `AWAITING_HUMAN`. |
| Adaptive inquiry against current run, no triage | `AWAITING_HUMAN_TRIAGE`; zero proposed questions; null semantic verdict. |
| Normal versus optimized calibration serialization | Byte-identical. |
| `git diff --check` | Pass. |

Lean, Lake, and Docker were not available in the local environment. Do not simulate or infer their results. The successful remote base workflow provides separate historical replay evidence but does not test this uncommitted increment.

## Known implementation boundary

SMF-0.1/0.3 is a working harness kernel and one deliberately weak calibration, not an autonomous semantic-model synthesizer. It can expand exact rival falsifiers into content-addressed questions only after human triage. It does not determine the semantic failure locus, generate a new issue graph from arbitrary model deltas, resolve append-only human semantic decisions into positive status, translate a complete CR-1.0 slice into the provisional neutral signature, or execute a full same-reduct role-twin search.

The calibration's two Boolean fixtures are an intentionally small test of the harness's status discipline. They do not establish that full CR-1.0 is underdetermined, that causal discrimination is sufficient, that a distributed interpretation is correct, or that any physical system instantiates the proposed relations.

The seed corpus is an attack vocabulary, not a complete checklist. Its oracles are fallible, typed conjectures. New problem mechanisms may require new defect keys, cases, rival interpretations, source work, and human disposition.

The exploit history and residual attack surface are preserved in `docs/audits/SMF-0.1_Adversarial_Hardening.md`. Passing those regressions establishes only resistance to the named implementation attacks, not semantic adequacy.

## Open semantic and formal gates

| Priority | Gate | Required discharge |
|---|---|---|
| 1 | Triage the first role-relabel fixture | Human selects one diagnosis and supplies reasons and scope; null remains valid until then. |
| 2 | Review the source-to-neutral mapping | Map every selected CR-1.0 carrier and relation into the provisional signature, with reifications, overlaps, arities, losses, and imports separately typed. |
| 3 | Fix one dependency-closed CR theory slice | Select reviewed interpretation and project-import sets without hiding rival readings. |
| 4 | Test role determination | Over nonempty registered intended-base coverage and immutable common-language transports, construct a localized same-reduct twin for `SMF-CR-CM-01`, or prove the corresponding typed, digest-bound implicit-determination statement `SMF-CR-ID-01`; if neither, leave it open. |
| 5 | Propose a substantive repair | Exhibit a consistent, non-vacuous successor with either a named old-language counterfeit excluded after existential erasure or an exact witnessed role-fiber narrowing over a preserved base history. |
| 6 | Preserve strength | Establish global non-broadening, retain a nonempty intended-base family, and replay exact role fibers, protected positive cases, prior exclusions, formal consequences, fixed scope and modality, plus clause-deletion independence witnesses. |
| 7 | Evolve schema and reassess readiness | Add typed, digest-bound fields and resolvers for the complete obligations; require explicit human review records and dependency closure before new Lean declarations. |
| 8 | Continue legacy bridge gates | DF-7a/`CCPWitness`, complete TH-3 dependencies, reviewed DF-10 choices, refined immutable TH-3 records, and the SMT/witness slice remain open. |

## Exact next orchestrator action

Present the first run's paired fixture and its exact human question:

> Does the paired fixture expose a genuine in-scope defect in this typed-role projection, or is the candidate, auxiliary, test, or scope specification at fault?

Record one of `CANDIDATE_DEFECT`, `AUXILIARY_DEFECT`, `TEST_DEFECT`, `OUT_OF_SCOPE`, or `UNRESOLVED`, together with free-form reasons, scope, and one uncertainty location: `INTERNAL_DEDUCTION_OR_MODEL_FINDING`, `INTERNAL_HARNESS_SPECIFICATION`, `CR_AUTHORITY_INTERPRETATION`, `EXTERNAL_CRITICAL_INSTRUMENT`, `APPLICATION_EMPIRICAL`, or `UNLOCATED`. Do not assume a default from the mechanical observation.

If that exact triage routes to external critical-instrument or application research, generate the bound inquiry plan, activate only the reviewed question, execute the falsifier-first AlphaXiv route within its recorded source scope and stop condition, and inspect the exact primary version before retaining any bounded external report. If triage routes elsewhere, do that work instead. Then construct the full CR target-neutral mapping and attempt the same-reduct twin obligation before writing new Lean. A negative bounded search leaves the theorem open; a found twin is a formal consequence of the exact encoded slice, not automatically a result about CR-1.0.

This file supersedes `CR-EIB-0.2_Orchestrator_Handover.md` as the continuation point. The older handover remains historical evidence and must not be deleted or rewritten as if it described this increment.
