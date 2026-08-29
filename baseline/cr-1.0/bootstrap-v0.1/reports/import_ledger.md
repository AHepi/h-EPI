# CR-1.0 import-ledger skeleton

## 0. Authority, purpose, and status discipline

This is a cold-start audit skeleton, not a proof file and not an alternate calculus. The sole semantic and formal authority is *Creativity as Explanatory Self-Correction*, especially the active “Model CR-1.0” (report/footer pp. 218–233; physical PDF pp. 219–234) and “Downstream applications and adversarial audit” (report/footer pp. 256–282; physical PDF pp. 257–283). Report/footer pp. 234–255 are the explicitly superseded precursor audit: they may expose historical defects but cannot supply active clauses, identifiers, premises, or warrants. The handoff is used only for procedure and file organization. A handoff-only formulation has no CR-1.0 standing unless the active report independently states it.

Every exact CR clause that bundles several primitive symbols is kept under its report ID, with all bundled symbols named in `Statement / role`. Nothing below promotes an unresolved warrant or independence claim to an accepted import. No result is proved here.

The governing inferential-status vocabulary is **only** `DEF`, `IMP`, and `DER`:

- `DEF` is reserved for an eliminable definition and licenses exact folding/unfolding only.
- `IMP` marks a nondefinitional rule, primitive interpretation, postulate, principle, or bridge condition explicitly adopted by CR-1.0. It is inferentially usable only in that declared module and never supplies an actual-system witness by itself.
- `DER` is reserved for a proved result with a complete dependency certificate. This skeleton proves nothing, so it assigns no new `DER` status.
- `null` means the item is not inferentially available. Every unresolved or application-specific import has `proof_available: false` and remains quarantined.

Non-inferential distinctions appear under **declaration role**, never in the status field. Section defaults are: TY = formation/audit constraint; IR = metarule; MS = model primitive/structural constraint; SC = satisfaction constraint; RC = reconstruction policy; DP/AB = source-profiled postulate; CT = constructor-theory definition or principle; BR = physical-realization bridge condition; I-* = independent application-import request.

Report page references use the printed footer, not the PDF viewer’s one-page-higher physical index.

## 1. Source-key registry used in warrant fields

These are the report’s own source tags and exact locators (report pp. 218–220). A tag in a later record expands to the locator here.

| Tag | Exact locator in the report’s registry |
|---|---|
| `S-BOI1` | Deutsch, *The Beginning of Infinity*, ch. 1, print pp. 1–33 / supplied PDF pp. 12–44. |
| `S-BOI3` | *BOI*, ch. 3, print pp. 42–77 / PDF pp. 53–88. |
| `S-BOI4` | *BOI*, ch. 4, print pp. 78–106 / PDF pp. 89–117. |
| `S-BOI6` | *BOI*, ch. 6, print pp. 124–147 / PDF pp. 135–158. |
| `S-BOI7` | *BOI*, ch. 7, print pp. 148–163 / PDF pp. 159–174. |
| `S-BOI10` | *BOI*, ch. 10, print pp. 223–257 / PDF pp. 234–268. |
| `S-BOI14` | *BOI*, ch. 14, print pp. 353–368 / PDF pp. 364–379. |
| `S-BOI15` | *BOI*, ch. 15, print pp. 369–397 / PDF pp. 380–408. |
| `S-BOI16` | *BOI*, ch. 16, print pp. 398–417 / PDF pp. 409–428. |
| `S-FOR1` | Deutsch, *The Fabric of Reality*, ch. 1, print pp. 1–31 / supplied PDF pp. 13–43. |
| `S-FOR3` | *FOR*, ch. 3, print pp. 55–72 / PDF pp. 67–84. |
| `S-FOR8` | *FOR*, ch. 8, print pp. 167–193 / PDF pp. 179–205. |
| `S-FOR10` | *FOR*, ch. 10, print pp. 222–257 / PDF pp. 234–269. |
| `S-FOR12` | *FOR*, ch. 12, print pp. 289–320 / PDF pp. 301–332; creative/noncreative gap at print p. 316 / PDF p. 328. |
| `S-FOR13` | *FOR*, ch. 13, print pp. 321–343 / PDF pp. 333–355. |
| `S-SCC3` | Marletto, *The Science of Can and Can’t*, ch. 3; the registry gives no finer page span. |
| `S-SCC5` | *Science*, ch. 5, print pp. 139–157. |
| `S-SCC7` | *Science*, ch. 7, print pp. 204–226, especially pp. 215–221. |
| `S-CT13` | Deutsch, “Constructor Theory,” *Synthese* 190 (2013), pp. 4331–4359. |
| `S-CTI15` | Deutsch and Marletto, “Constructor Theory of Information,” *Proc. R. Soc. A* 471 (2015), article 20140540; the registry gives no internal page range. |
| `S-CTL15` | Marletto, “Constructor Theory of Life,” *J. R. Soc. Interface* 12 (2015), article 20141226; the registry gives no internal page range. |
| `S-CB12` | Deutsch, “Creative Blocks,” *Aeon*, 3 October 2012; web article, no page range. |
| `S-MAI20` | Marletto, “Constructing the Universe,” IAI interview (2020); web interview, no page range. |

`No itemized tag` means exactly that: the report states the clause but does not attach an external-source tag to that clause. It must not be silently backfilled from thematic similarity.

## 2. Reusable independence and discharge plans

These codes are plans only. A completed witness must be typed, hold every nonvaried premise fixed, and be checked under IR-4 and IR-8.

| Code | Planned independence witness |
|---|---|
| `W-TYP` | Two interpretations with the same tokens/traces but different sort or cross-type assignments; show the target typing constraint is not recoverable from behavior. |
| `W-STR` | Two models with the same actual trace but different order, history family, event/state structure, or boundary. |
| `W-SEM` | Trace-equivalent models with identical surface tokens but different content, role, explanation, comparison, or reach relations. |
| `W-CAU` | Same events and outputs, but different provenance, intervention responses, causal lineage, or authorship credit. |
| `W-EPI` | Same critical lineage and retention, but vary `K_E`, `True`, or provisional preference independently. |
| `W-MOD` | Same finite actual history, but one model has suitable admissible continuations/stable organization and the other terminates or is bounded. |
| `W-PHY` | Same abstract CR history with two physical models or realization maps, only one satisfying the named theory, fidelity, resources, or bridge. |
| `W-APP` | Same CR classification with two application interpretations or empirical dossiers that disagree on the imported domain predicate. |
| `W-SRC` | Compare the claimed source reading against a weaker reading that preserves the cited text; unresolved if the source does not discriminate them. |

The report’s discriminating-test battery is at pp. 260–262: `T-BND` boundary matrix; `T-PROV` provenance audit; `T-SEM` semantic invariance; `T-CRI` reason intervention; `T-PROB` problem intervention; `T-STD` standard intervention; `T-GEN` authorship test; `T-UPT` uptake specificity; `T-RET` retention/reuse; `T-TRN` representation transfer; `T-ABL` mechanism ablation; `T-ALT` rival-model tournament; `T-SUC` independent success; `T-PHY` physical fidelity; `T-LONG` expanding-horizon trial. Their limitations remain part of every cited discharge plan.

## 3. Logical, typing, and audit imports

### AUD-LANG-1-TYPES — sort-domain declaration (owner: active model §1.1)

- **Layer:** Logical/ontological typing.
- **Statement / role:** Declare the exact sorts `Sys`, `Time`, `Hist`, `State`, `Token`, `Content`, `Problem`, `AttemptExp`, `Criticism`, `Standard`, `Observation`, `Operation`, `Background`, `Context`, `Environment`, `Resource`, `PhysSubstrate`, `PhysAttribute`, and `CTTask`.
- **Scope:** The entire many-sorted signature.
- **Alternatives:** Fewer/more sorts; subtype hierarchies; one untyped domain; reification of roles as objects; dependent types.
- **Independence-witness plan:** `W-TYP`: preserve all surface formulas under an untyped encoding, then exhibit an illicit cross-sort substitution blocked by the report’s signature.
- **Conceptual necessity:** Makes semantic, causal, epistemic, and physical category separations checkable.
- **Source warrant:** Active CR model p. 220, §1.1; no itemized source tag.
- **Discharge test:** Signature declaration, inhabitedness policy where needed, and automated sort checking.
- **Non-entailments:** Declaring a sort supplies no inhabitant or actual-system witness.
- **Direct / known dependents:** TY-1–TY-3 and every MS/SC/DF/DP/CT/BR clause.
- **Inferential status / availability:** `inferential_status: null`; `proof_available: false`; `owner_status: IMP` for the active §1.1 language declaration. This audit key cannot enter proof closure.

### AUD-LANG-1-ROLES — content-role and inexplicit-content policy (owner: active model §1.1)

- **Layer:** Semantic/type policy.
- **Statement / role:** `AttemptExp`, `Criticism`, `Standard`, and `Problem` are semantic roles of contents, not mutually exclusive substances; contents may be explicit or inexplicit, but role assignment requires system-level causal use rather than resemblance judged by an analyst.
- **Scope:** Every role-bearing content and tacit/nonverbal application.
- **Alternatives:** Mutually exclusive ontological kinds; verbal-only content; analyst resemblance; role by token syntax.
- **Independence-witness plan:** `W-SEM`: same content occupies multiple roles in one interpretation; contrast causally used inexplicit state with analyst-only resemblance.
- **Conceptual necessity:** Permits role overlap and tacit realization without making semantics unconstrained.
- **Source warrant:** Active CR model p. 220, §1.1, paragraph immediately before TY-1; no itemized source tag.
- **Discharge test:** Role-by-role representation/use evidence; for nonverbal criticism, I-MIND-TACIT and causal interventions.
- **Non-entailments:** Type membership, verbal form, or resemblance does not entail a semantic role; role overlap is not type identity.
- **Direct / known dependents:** SC-2, DF-1/DF-2/DF-5, I-MIND-TACIT, I-ART/I-AR-SHARED.
- **Inferential status / availability:** `inferential_status: null`; `proof_available: false`; `owner_status: IMP` for the active §1.1 role policy. This audit key cannot enter proof closure.

### TY-1 — sortedness and type separations

- **Layer:** Logical/type discipline.
- **Statement / role:** Predicates are sorted; tokens are not contents; prediction is not explanation; retention is not truth; physical information is not explanatory knowledge.
- **Scope:** Every well-formed CR formula and application mapping.
- **Alternatives:** One untyped universe; coercions between token/content or physical/epistemic roles; extensional identification of the contrasted predicates.
- **Independence-witness plan:** `W-TYP`: preserve a trace while swapping a token for its interpreted content or a retained item for a true one; verify the untyped rival validates an illicit inference.
- **Conceptual necessity:** Prevents category errors and makes bridge requirements visible.
- **Source warrant:** CR p. 220, TY-1; no itemized external tag.
- **Discharge test:** Static signature/type check plus IR-8 cross-type audit.
- **Non-entailments:** Token identity does not entail content identity; prediction does not entail explanation; retention does not entail truth; physical information does not entail `K_E`.
- **Direct / known dependents:** All MS/SC/DF/DP/CT/BR clauses; TH-16 explicitly depends on all TY clauses.
- **Inferential status / availability:** `IMP`; exact CR formation constraint only; no actual-world witness follows.

### TY-2 — displayed baselines

- **Layer:** Logical/audit discipline.
- **Statement / role:** Every use of *new*, *general*, *possible*, *good*, *same explanation*, *reach*, *efficient*, or *owned* displays its relevant system, equivalence, theory, problem/background, resource, or boundary baseline.
- **Scope:** Core predicates and every application claim.
- **Alternatives:** Context-default baselines; post-hoc boundary choice; unqualified novelty/generality/efficiency.
- **Independence-witness plan:** Hold the output fixed and vary system boundary, equivalence level, historical baseline, theory, or budget; classification should change.
- **Conceptual necessity:** Blocks equivocation across relative predicates.
- **Source warrant:** CR p. 220, TY-2; application dossier p. 259; no itemized external tag.
- **Discharge test:** Dossier completeness check and `T-BND`, `T-PROV`, `T-LONG`, `T-PHY` as applicable.
- **Non-entailments:** New-to-user does not entail new-to-system or new-to-history; finite breadth does not entail generality; logical consistency does not entail physical possibility.
- **Direct / known dependents:** DF-3, DF-4a, DF-8, DF-9, DF-11–DF-14, DF-18–DF-20, CT-4, application tuple `A`.
- **Inferential status / availability:** `IMP`; exact CR audit constraint only.

### TY-3 — named bridges for cross-type inference

- **Layer:** Logical/type firewall.
- **Statement / role:** Semantic, causal, epistemic, and physical claims occupy distinct types; every crossing requires a named bridge.
- **Scope:** All mixed-layer conclusions.
- **Alternatives:** Semantic descent from physics; behavior-to-meaning inference; retention-to-success; computation-to-thinking.
- **Independence-witness plan:** `W-TYP` plus `W-PHY`: fix one layer and vary the other while removing the bridge.
- **Conceptual necessity:** Enforces the report’s layer firewall.
- **Source warrant:** CR p. 220, TY-3; application firewall p. 256; no itemized external tag.
- **Discharge test:** IR-8 crossing inventory and IR-5 bridge-transfer audit.
- **Non-entailments:** No listed cross-type implication holds merely by sharing a realization or trace.
- **Direct / known dependents:** IR-5, BR-1–BR-8, RC-1–RC-3, TH-10, TH-14–TH-16, all world-facing applications.
- **Inferential status / availability:** `IMP`; exact CR type-firewall constraint only.

### IR-1 — sorted first-order and ordinary mathematical consequence

- **Layer:** Logical metarule.
- **Statement / role:** Sorted first-order consequence and ordinary mathematical reasoning are valid within a declared module.
- **Scope:** Only the active module and declared signature.
- **Alternatives:** Higher-order, probabilistic, paraconsistent, intuitionistic, or proof-assistant-specific bases.
- **Independence-witness plan:** Exhibit an inference valid only in an alternative base while all CR premises stay fixed; keep it unavailable under IR-1.
- **Conceptual necessity:** Supplies the minimal consequence relation used by the calculus.
- **Source warrant:** CR p. 226, IR-1; model rule, no external source tag.
- **Discharge test:** Declare logic/module and mechanically type-check each inference.
- **Non-entailments:** Does not import induction from data, existence, semantics, physics, or modal facts.
- **Direct / known dependents:** Every derivation; IR-8 audits its use.
- **Inferential status / availability:** `IMP`; exact CR metarule.

### IR-2 — exact definitional folding and unfolding

- **Layer:** Logical metarule.
- **Statement / role:** A defined predicate may be folded/unfolded exactly; a definition provides neither existential witnesses nor world facts.
- **Scope:** DF, DF-22/23, and other explicitly definitional clauses only.
- **Alternatives:** Treating definitions as biconditional substantive laws or existential commitments.
- **Independence-witness plan:** Expand a model with empty extensions for defined predicates where the definiens lacks witnesses.
- **Conceptual necessity:** Preserves the definition/postulate firewall.
- **Source warrant:** CR p. 226, IR-2; no external tag.
- **Discharge test:** Exact syntactic expansion and witness inventory.
- **Non-entailments:** A definition never proves an actual creator or physical realization.
- **Direct / known dependents:** Every DF theorem; TH-3 uses IR-2 explicitly; TH-16 stresses the no-existence consequence.
- **Inferential status / availability:** `IMP`; exact CR metarule.

### IR-3 — allowed proof moves

- **Layer:** Logical metarule.
- **Statement / role:** Modus ponens, quantifier rules, finite-history induction, and explicit case analysis are permitted.
- **Scope:** Formal proofs over declared finite histories and cases.
- **Alternatives:** Unrestricted induction over empirical instances; infinitary induction; implicit exhaustive cases.
- **Independence-witness plan:** Construct an infinite/open application where finite-history induction cannot settle the modal conclusion.
- **Conceptual necessity:** Makes permitted proof machinery explicit.
- **Source warrant:** CR p. 226, IR-3; no external tag.
- **Discharge test:** Proof-step checker with induction measure and exhaustive-case certificate.
- **Non-entailments:** Finite-history induction does not license empirical induction or open-endedness.
- **Direct / known dependents:** Formal theorem proofs; TH-12’s finite/open distinction.
- **Inferential status / availability:** `IMP`; exact CR metarule.

### IR-4 — typed countermodel criterion

- **Layer:** Logical/metatheoretic rule.
- **Statement / role:** Non-entailment requires a fully typed model satisfying all premises and falsifying the conclusion.
- **Scope:** Every `not-entails` result.
- **Alternatives:** Intuitive counterexamples; absence of proof; partial or ill-typed models.
- **Independence-witness plan:** Compare a fully checked countermodel with a merely verbal scenario; only the former discharges the rule.
- **Conceptual necessity:** Prevents non-entailment claims from outrunning the formal premises.
- **Source warrant:** CR p. 226, IR-4; no external tag.
- **Discharge test:** Model validation against the transitively closed premise set.
- **Non-entailments:** Failure to find a countermodel does not prove entailment.
- **Direct / known dependents:** TH-1–TH-17 non-entailment arguments; application A-TH results.
- **Inferential status / availability:** `IMP`; exact CR metarule.

### IR-5 — physical bridge transfer

- **Layer:** Logical/physical bridge rule.
- **Statement / role:** Only predicates preserved by one predeclared realization map over a counterfactual family may cross from abstract to physical.
- **Scope:** `PhysOCA`, `PhysGCD`, and any physical attribution.
- **Alternatives:** Trace-only realization; per-case remapping; observer resemblance; abstract consistency as possibility.
- **Independence-witness plan:** `W-PHY`: keep the abstract trace fixed, but let one mapping fail under recoding/intervention while another remains stable.
- **Conceptual necessity:** Stops semantic/causal predicates from descending automatically into physical descriptions.
- **Source warrant:** CR p. 226, IR-5; physical layer pp. 227–228; no external tag for the rule.
- **Discharge test:** `T-PHY`, `T-SEM`, `T-CRI`, `T-ABL` under one frozen map.
- **Non-entailments:** Abstract satisfaction does not entail physical realization; physical copying does not entail semantic preservation.
- **Direct / known dependents:** BR-1–BR-8, DF-22, DF-23, TH-14, TH-15, legal application pattern p. 280.
- **Inferential status / availability:** `IMP`; exact CR bridge-transfer metarule, while its preservation antecedent remains application-specific.

### IR-6 — transitive dependency closure

- **Layer:** Logical/audit metarule.
- **Statement / role:** Citing a theorem imports every definition, postulate, bridge, and empirical premise in its dependency list.
- **Scope:** All theorem and application dependency certificates.
- **Alternatives:** Immediate dependencies only; theorem names as opaque warrants.
- **Independence-witness plan:** Remove one transitive dependency from a candidate proof and seek a model satisfying the remainder but falsifying the result.
- **Conceptual necessity:** Enforces no-hidden-import discipline.
- **Source warrant:** CR p. 226, IR-6; no external tag.
- **Discharge test:** Graph closure plus cycle and missing-node checks.
- **Non-entailments:** A cited theorem does not erase or weaken its premises.
- **Direct / known dependents:** Every displayed theorem dependency line; application legal pattern pp. 280–281.
- **Inferential status / availability:** `IMP`; exact CR metarule.

### IR-7 — strong model-expansion conservativity test

- **Layer:** Metatheoretic audit rule.
- **Statement / role:** A definitional module is conservatively acceptable only if every core model can expand without changing core predicates; the report does not identify this with the weaker proof-theoretic test.
- **Scope:** Proposed definitional extensions.
- **Alternatives:** No-new-old-language-theorem criterion; unique expansion; mere notational convenience.
- **Independence-witness plan:** Produce a core model that cannot expand, or two expansions that force different old-predicate values.
- **Conceptual necessity:** Prevents substantive semantics from being hidden as definitions.
- **Source warrant:** CR p. 226, IR-7; no external tag.
- **Discharge test:** Model-expansion audit over arbitrary core models.
- **Non-entailments:** Explains, `K_E`, authorship, and physical realization are not conservative abbreviations.
- **Direct / known dependents:** Module admission; report’s non-derivability/audit discussion pp. 232–255.
- **Inferential status / availability:** `IMP`; exact CR metatheoretic rule; equivalence to weaker conservativity remains unasserted.

### IR-8 — no-hidden-import audit

- **Layer:** Metatheoretic/audit rule.
- **Statement / role:** Before theorem acceptance: unfold every DF, close theorem dependencies, inventory witnesses and every normative/physical/modal crossing, then attempt a countermodel with exactly the listed dependencies.
- **Scope:** Every theorem or application claim.
- **Alternatives:** Informal plausibility, source citation as logical premise, or absence of disproof.
- **Independence-witness plan:** Deliberately omit one audit stage and construct a false-positive proof that the full audit rejects.
- **Conceptual necessity:** Operationalizes the no-hidden-import law.
- **Source warrant:** CR pp. 226–227, IR-8; application legal pattern p. 280.
- **Discharge test:** Completed audit checklist with typed countermodel attempt.
- **Non-entailments:** Source warrant does not substitute for a logical premise; audit failure invalidates acceptance.
- **Direct / known dependents:** Every theorem/application; completion checklist pp. 280–281.
- **Inferential status / availability:** `IMP`; exact CR audit metarule.

## 4. Abstract-model primitives and satisfaction imports

### MS-1 — time order and admissible histories (`T`, `<`, `H`)

- **Layer:** Ontological/structural and modal.
- **Statement / role:** `(T,<)` is a strict partial order; `H` is a nonempty family of admissible histories, not merely the actual trace.
- **Scope:** All temporal and dispositional clauses.
- **Alternatives:** Linear/discrete time; a single actual history; branching time with different accessibility; stochastic histories.
- **Independence-witness plan:** `W-STR` and `W-MOD`: preserve the observed trace while varying incomparable times or admissible continuations.
- **Conceptual necessity:** Supports temporal order, counterfactual availability, capacity, and finite/open separation.
- **Source warrant:** CR p. 220, MS-1; no itemized external tag.
- **Discharge test:** State the time structure and admissibility rule; check nonemptiness and strict-order axioms.
- **Non-entailments:** Actual occurrence does not entail availability; a finite history does not entail or refute an open disposition.
- **Direct / known dependents:** SC-1, SC-7; DF-3, DF-4a, DF-6–DF-13; TH-1, TH-2, TH-6, TH-7, TH-12, TH-16.
- **Inferential status / availability:** `IMP`; exact CR model-structure import; application histories still require evidence.

### MS-2 — events and abstract states (`E`, `Σ`)

- **Layer:** Ontological/structural.
- **Statement / role:** `E(h,t)` supplies typed events and `Σ(h,t)` supplies the abstract state.
- **Scope:** Every event/history realization.
- **Alternatives:** State-only or event-only ontology; interval events; process ontology; coarse-graining choices.
- **Independence-witness plan:** `W-STR`: preserve outputs while changing event segmentation or state granularity.
- **Conceptual necessity:** Provides carriers for causal, representational, and transition claims.
- **Source warrant:** CR p. 220, MS-2; SC-1 p. 221; no itemized external tag.
- **Discharge test:** Typed event/state inventory with a declared granularity and time indexing.
- **Non-entailments:** Co-occurrence does not entail causation, content, lineage, or authorship.
- **Direct / known dependents:** SC-1–SC-4, SC-7–SC-8; all event-indexed DF predicates; physical realization.
- **Inferential status / availability:** `IMP`; exact CR model-structure import.

### AUD-MS-2-B — declared system/environment boundary (`B`; owner: MS-2)

- **Layer:** Ontological/structural and causal attribution.
- **Statement / role:** `B(s,h,t)` fixes a system/environment boundary; nested boundaries are allowed, but post-outcome boundary switching is forbidden.
- **Scope:** System-relative novelty, provenance, ownership, memory, and all physical/application attributions.
- **Alternatives:** Privileged biological boundary; component, session, agent-loop, team, or institutional boundaries; post-hoc maximal/minimal boundary.
- **Independence-witness plan:** `W-STR`/`W-CAU`: same full history classified at nested boundaries with different crossings and credit.
- **Conceptual necessity:** Makes endogenous origin and ownership non-gameable.
- **Source warrant:** CR p. 220, MS-2; BR-1 p. 227; application dossier p. 259 and audit pp. 278–280; no itemized tag.
- **Discharge test:** `T-BND`, `T-PROV`; preregister nested boundaries and disclose all crossings.
- **Non-entailments:** Boundary relativity is not arbitrariness; enlarging a boundary does not transfer component authorship automatically.
- **Direct / known dependents:** SC-4, DF-3–DF-4, BR-1, BR-6, TH-7, TH-14, I-GROUP, I-AI-SYS.
- **Inferential status / availability:** `inferential_status: null`; `proof_available: false`; `owner_status: IMP` for MS-2. This audit key cannot enter proof closure.

### AUD-MS-3-REP — representation relation (`Rep`; owner: MS-3/SC-2)

- **Layer:** Semantic with causal-access constraint.
- **Statement / role:** `Rep(s,z,h,t)` links a causally accessible token/state to content `z`; under SC-2 an internal discriminable state must realize `z` and an available operation must use its difference from relevant alternatives.
- **Scope:** Every represented problem, candidate, criticism, standard, observation, and memory claim.
- **Alternatives:** Observer labeling; pure syntactic covariance; functional-role, teleosemantic, inferentialist, or interpretivist semantics.
- **Independence-witness plan:** `W-SEM`: trace-equivalent systems, one with systematic discriminable use across recodings and one with analyst-only labels.
- **Conceptual necessity:** Blocks syntax/output resemblance from satisfying semantic roles.
- **Source warrant:** CR pp. 220–221, MS-3 and SC-2; no itemized external tag; semantic theory remains a substantive model/application burden.
- **Discharge test:** `T-SEM`, `T-PROB`, `T-CRI`, `T-ABL`; verify systematic use and relevant-alternative sensitivity.
- **Non-entailments:** Token occurrence, correlation, decodability, or physical distinguishability does not entail representation.
- **Direct / known dependents:** DF-1–DF-7, DF-14, SC-3–SC-4, BR-2, BR-4–BR-7, TH-1–TH-9, TH-13, TH-17.
- **Inferential status / availability:** `inferential_status: null`; `proof_available: false`; `owner_status: IMP` for MS-3/SC-2. This audit key cannot enter proof closure.

### AUD-MS-3-EQUIV — declared content equivalence (`≡_L`; owner: MS-3)

- **Layer:** Semantic/baseline.
- **Statement / role:** `≡_L` is the declared content-equivalence relation; encoding changes may preserve content and surface similarity may fail to do so.
- **Scope:** Newness, reconstruction, paraphrase invariance, and historical/system comparisons.
- **Alternatives:** Token identity; semantic identity; task-equivalence; explanatory-commitment equivalence; graded similarity.
- **Independence-witness plan:** `W-SEM`: same tokens under two `L` policies, or paraphrases with fixed content versus near-identical strings with changed defect.
- **Conceptual necessity:** Makes novelty and recoding claims level-relative.
- **Source warrant:** CR p. 220, MS-3; TY-2 p. 220; no itemized tag.
- **Discharge test:** Predeclare `L`; use `T-SEM` and provenance checks on equivalent/non-equivalent pairs.
- **Non-entailments:** Surface novelty does not entail content novelty; semantic equivalence does not entail identical provenance.
- **Direct / known dependents:** DF-3, DF-14, SC-3, BR-4, BR-5, TH-17; application dossier `L` p. 259.
- **Inferential status / availability:** `inferential_status: null`; `proof_available: false`; `owner_status: IMP` for MS-3. This audit key cannot enter proof closure.

### AUD-MS-4-PROV — provenance graph (`Prov`; owner: MS-4/SC-4)

- **Layer:** Causal/authorship.
- **Statement / role:** A causal-credit graph spans design/architecture, inherited or trained repertoire, stored content, episode inputs, tools/interlocutors, candidates, criticisms, and revisions.
- **Scope:** Every authorship, reconstruction, lineage, and ownership attribution.
- **Alternatives:** Last-emitter credit; designer-only credit; runtime-only credit; Shapley-like or structural-causal allocation; unmodeled distributed credit.
- **Independence-witness plan:** `W-CAU`: same output and internal trace with rival causal-credit graphs assigning organization to retrieval, evaluator, target, or distributed system.
- **Conceptual necessity:** Localizes problem-specific explanatory organization without treating prior influence as automatically disqualifying.
- **Source warrant:** CR p. 220, MS-4; SC-4 pp. 221–222; DP-3 p. 225 with `S-BOI7`, `S-BOI10`, `S-BOI16`, `S-CB12`.
- **Discharge test:** `T-PROV`, `T-GEN`, `T-BND`, `T-ABL`.
- **Non-entailments:** Emission, novelty, training exposure, or external communication alone neither establishes nor defeats authorship.
- **Direct / known dependents:** SC-4, SC-8, DF-4, DF-7a, BR-1, BR-6–BR-7, TH-3–TH-9, TH-13, TH-17.
- **Inferential status / availability:** `inferential_status: null`; `proof_available: false`; `owner_status: IMP` for MS-4/SC-4. This audit key cannot enter proof closure.

### AUD-MS-4-CF — counterfactual family (`CF`; owner: MS-4)

- **Layer:** Causal/modal.
- **Statement / role:** `CF` supplies interventions together with declared held-fixed conditions.
- **Scope:** Reason use, authorship, lineage, stability, and physical realization.
- **Alternatives:** Pure observational dependence; Rubin-style potential outcomes; structural equations; intervention families with different invariances.
- **Independence-witness plan:** `W-CAU`: observationally identical systems that diverge under matched defect/content interventions.
- **Conceptual necessity:** Distinguishes causal use of reasons from temporal succession or generic sensitivity.
- **Source warrant:** CR p. 220, MS-4; SC-3/SC-8 pp. 221–222; no itemized tag for the formal intervention choice.
- **Discharge test:** `T-SEM`, `T-CRI`, `T-UPT`, `T-ABL`, with held-fixed variables named.
- **Non-entailments:** Correlation or before/after change does not entail reason-specific causation.
- **Direct / known dependents:** SC-3, SC-4, SC-8, StableOrg, BR-5, BR-8, all causal application claims.
- **Inferential status / availability:** `inferential_status: null`; `proof_available: false`; `owner_status: IMP` for MS-4. This audit key cannot enter proof closure.

### AUD-MS-4-CLINE — connected critical lineage (`CLine`; owner: MS-4/SC-8)

- **Layer:** Causal/semantic lineage.
- **Statement / role:** One predeclared, role-preserving `Prov` subgraph connects authored attempt `x0`, its criticized self/descendant `x1`, criticism `c`, reason-specific response `α`, and endpoint problem situation `y`; SC-8 requires the matched counterfactuals and rejects co-occurrence/topic similarity.
- **Scope:** `CCPResult`, CCP, and EKC.
- **Alternatives:** Temporal sequence only; topical similarity; separate episodes; analyst-composed lineage.
- **Independence-witness plan:** `W-CAU`: identical events with one connected role-preserving graph and one disconnected graph joining an unrelated retained insight.
- **Conceptual necessity:** Prevents criticism, revision, and success from being assembled across unrelated episodes.
- **Source warrant:** CR pp. 220 and 222, MS-4 and SC-8; the lineage solution is R/M with no itemized tag.
- **Discharge test:** `T-PROV`, `T-CRI`, `T-UPT`, `T-RET`, `T-ABL`.
- **Non-entailments:** Co-occurrence, topic match, or an eventual good result does not entail a connected critical lineage.
- **Direct / known dependents:** DF-7a, DF-7, DF-10; TH-1–TH-3, TH-7–TH-9, TH-12–TH-13.
- **Inferential status / availability:** `inferential_status: null`; `proof_available: false`; `owner_status: IMP` for MS-4/SC-8. This audit key cannot enter proof closure.

### AUD-MS-4-STABLEORG — stable causal organization (`StableOrg`; owner: MS-4)

- **Layer:** Modal/dispositional and causal.
- **Statement / role:** `StableOrg(s,Q,χ)` is independently interpreted causal stability over declared perturbations, resources, and problem class.
- **Scope:** OCap, stable critical capacity, GCD, UED, and PhysGCD.
- **Alternatives:** Trait score; repeated success; ergodic average; one lucky path; reconstructible network rather than persisting component.
- **Independence-witness plan:** `W-MOD`: same finite success trace, but only one model preserves/reconstructs organization across perturbations and new problems.
- **Conceptual necessity:** Separates an act/process from a capacity/disposition.
- **Source warrant:** CR p. 220, MS-4; DF-4a and DF-11–DF-13 pp. 222–223; no itemized tag for the stability predicate.
- **Discharge test:** `T-RET`, `T-TRN`, `T-ABL`, `T-LONG`, with `Q`, `χ`, horizons, and resources frozen.
- **Non-entailments:** Finite success, repeated benchmarks, or persistence of one token does not entail a stable creative organization.
- **Direct / known dependents:** DF-4a, DF-11, DF-12, DF-13, BR-8, DF-23, TH-1, TH-7, TH-12–TH-16.
- **Inferential status / availability:** `inferential_status: null`; `proof_available: false`; `owner_status: IMP` for MS-4. This audit key cannot enter proof closure.

### AUD-MS-5-PURPORTS — explanatory purport (`Purports`; owner: MS-5)

- **Layer:** Semantic.
- **Statement / role:** `Purports(x,p,b)` means content `x` is offered as an explanation of problem `p` against background `b`; it may be false or fail to explain.
- **Scope:** Attempted explanation and OCA.
- **Alternatives:** Analyst-imposed purpose; answerhood; prediction; candidate membership; artifact function.
- **Independence-witness plan:** `W-SEM`: same product, one system uses it as an explanation of a represented problem and the other emits it without that role.
- **Conceptual necessity:** Keeps explanatory attempts distinct from arbitrary novel products.
- **Source warrant:** CR p. 221, MS-5; application I-EXP p. 258; source-facing motivation `S-BOI1`, `S-FOR1` through DP-1.
- **Discharge test:** `T-PROB`, `T-SEM`, `T-PROV`; predeclare problem/background and actual rivals.
- **Non-entailments:** Novel, valuable, useful, accepted, or problem-correlated output does not entail explanatory purport.
- **Direct / known dependents:** DF-2, DF-4, TH-1, TH-4–TH-9, TH-13, TH-17, I-EXP.
- **Inferential status / availability:** `inferential_status: null`; `proof_available: false`; `owner_status: IMP` for MS-5. This audit key cannot enter proof closure.

### AUD-MS-5-EXPLAINS — primitive explanation relation (`Explains`; owner: MS-5/SC-5)

- **Layer:** Semantic.
- **Statement / role:** `Explains(x,p,b)` is primitive and substantive; SC-5 requires a supplied domain interpretation, and predictive fit is neither necessary nor sufficient.
- **Scope:** Good explanation, explanatory reach, `K_E` interpretation, and domains that classify attempted products as explanatory.
- **Alternatives:** Prediction, compression, control, usefulness, acceptance, causal model adequacy, unification, or domain-specific explanatory theories.
- **Independence-witness plan:** `W-SEM`/`W-APP`: hold predictions and outputs fixed while two domain interpretations disagree about explanation.
- **Conceptual necessity:** Leaves the hardest semantic judgment visible rather than defining it by a proxy.
- **Source warrant:** CR pp. 221–222, MS-5 and SC-5; DP-1 p. 225 with `S-BOI1`, `S-FOR1`; I-EXP p. 258.
- **Discharge test:** I-EXP dossier; actual-rival comparison; `T-PROB`, `T-SEM`, `T-ALT`; for HTV also declare variation family.
- **Non-entailments:** Prediction, fit, compression, usefulness, survival, consensus, or hard-to-vary structure alone does not entail explanation or truth.
- **Direct / known dependents:** DF-8, DF-9, DF-14, DP-1, DP-5–DP-7, TH-2, TH-11, I-EXP, I-ART/I-AR-SHARED.
- **Inferential status / availability:** `inferential_status: null`; `proof_available: false`; `owner_status: IMP` for MS-5/SC-5. This audit key cannot enter proof closure.

### AUD-MS-6-SAMEJOB — explanatory-job relation (`SameJob`; owner: MS-6)

- **Layer:** Semantic comparison.
- **Statement / role:** `SameJob` identifies actual rivals that address the same explanatory job relative to the declared problem/background.
- **Scope:** HTV and GoodNow comparison.
- **Alternatives:** Same topic, same output type, same prediction set, same user rating, or analyst-selected comparison class.
- **Independence-witness plan:** `W-SEM`: hold candidates fixed and vary whether they solve the same explanandum under the same background.
- **Conceptual necessity:** Prevents comparisons across unlike explanatory tasks.
- **Source warrant:** CR p. 221, MS-6; DF-8/DF-9 p. 223; source motivation `S-BOI1`, `S-FOR3`.
- **Discharge test:** I-EXP/I-HTV with predeclared explanandum, background, and actual-rival set.
- **Non-entailments:** Similarity or shared predictions do not entail same explanatory job.
- **Direct / known dependents:** DF-8, DF-9, DP-5, DP-6, TH-11.
- **Inferential status / availability:** `inferential_status: null`; `proof_available: false`; `owner_status: IMP` for MS-6. This audit key cannot enter proof closure.

### AUD-MS-6-VAR — declared variation relation/family (`Var_V`; owner: MS-6)

- **Layer:** Semantic comparison.
- **Statement / role:** `Var_V` supplies material same-job variants under a declared family `V` for hard-to-vary comparison.
- **Scope:** HTV and GoodNow only under fixed problem/background.
- **Alternatives:** Random token mutation; all logically possible variants; syntactic perturbations; domain-expert substantive changes.
- **Independence-witness plan:** `W-SEM`: a candidate is robust under trivial surface edits but fragile under substantive variants, or vice versa.
- **Conceptual necessity:** Prevents “hard to vary” from becoming an unbound scalar slogan.
- **Source warrant:** CR p. 221, MS-6; DF-8/DF-9 p. 223; DP-6 p. 225 with `S-BOI1`; I-HTV p. 258.
- **Discharge test:** Predeclare `V`; vary content-bearing parts while holding explanandum/background fixed.
- **Non-entailments:** Syntactic rigidity does not entail HTV, explanation, goodness, or truth.
- **Direct / known dependents:** DF-8, DF-9, DP-6, TH-11, I-HTV.
- **Inferential status / availability:** `inferential_status: null`; `proof_available: false`; `owner_status: IMP` for MS-6. This audit key cannot enter proof closure.

### AUD-MS-6-BEARSON — problem-bearing standard relation (`BearsOn`; owner: MS-6)

- **Layer:** Semantic/normative.
- **Statement / role:** `BearsOn(k,p,b)` says standard `k` bears on the represented problem/background.
- **Scope:** Problem-bearing criticism and preference.
- **Alternatives:** Any reward, authority, popularity, fitness score, or generic negative signal counts as a standard.
- **Independence-witness plan:** `W-SEM`: same criticism token and response, but only one standard concerns the alleged defect in the declared problem.
- **Conceptual necessity:** Blocks proxy/evaluator smuggling into reasoned criticism.
- **Source warrant:** CR p. 221, MS-6; DF-5 p. 222; DP-5 p. 225 with `S-FOR3`, `S-BOI1`; no separate tag for `BearsOn`.
- **Discharge test:** `T-CRI`, `T-STD`, `T-UPT`, plus explicit proxy-to-problem interpretation.
- **Non-entailments:** Reward, selection, popularity, or authority does not entail a problem-bearing standard.
- **Direct / known dependents:** DF-5, DF-6, DF-7a, DP-5, TH-2, TH-9, TH-11.
- **Inferential status / availability:** `inferential_status: null`; `proof_available: false`; `owner_status: IMP` for MS-6. This audit key cannot enter proof closure.

### AUD-MS-6-CRITOF — criticism relation (`CritOf`; owner: MS-6)

- **Layer:** Semantic/normative.
- **Statement / role:** `CritOf(c,x,p,b,k)` alleges a defect in candidate `x` relative to problem `p`, background `b`, and standard `k`; correctness is not required.
- **Scope:** PBCrit, Uptake, CCP.
- **Alternatives:** Any negative signal; reward gradient; candidate rejection; analyst-imposed defect; only correct criticism.
- **Independence-witness plan:** `W-SEM`: matched negative tokens, one encodes a candidate-specific alleged defect and the other is irrelevant/generic.
- **Conceptual necessity:** Separates rational criticism from mere selection or change pressure.
- **Source warrant:** CR p. 221, MS-6; DF-5 p. 222; source-facing `S-FOR3`, `S-BOI1`, `S-BOI14`.
- **Discharge test:** `T-CRI`, `T-UPT`, `T-SEM`, including valid, invalid, irrelevant, paraphrased, and surface-matched controls.
- **Non-entailments:** Correctness is not required; rejection or response frequency does not entail criticism.
- **Direct / known dependents:** DF-5–DF-7a, SC-3, SC-8, DP-5, TH-2, TH-7–TH-9.
- **Inferential status / availability:** `inferential_status: null`; `proof_available: false`; `owner_status: IMP` for MS-6. This audit key cannot enter proof closure.

### AUD-MS-6-PREF — provisional preference (`Pref`; owner: MS-6)

- **Layer:** Epistemic/normative.
- **Statement / role:** `Pref` is a time-indexed, provisional preference among actual rivals.
- **Scope:** GoodNow, reasoned comparison, and current standards.
- **Alternatives:** Total ranking; scalar reward; consensus; posterior probability; permanent endorsement.
- **Independence-witness plan:** `W-EPI`: fix the rivals and evidence while models differ in current provisional preference without changing truth.
- **Conceptual necessity:** Represents current critical choice without smuggling certainty or truth.
- **Source warrant:** CR p. 221, MS-6; DF-9 p. 223; DP-4–DP-6 p. 225 with `S-BOI1`, `S-FOR3`.
- **Discharge test:** Record actual rivals, time, problem-bearing reasons, defeaters, and standard changes (`T-STD`).
- **Non-entailments:** Preference, survival, or consensus does not entail `Explains`, `K_E`, or `True`.
- **Direct / known dependents:** DF-9, OM-5/OM-7, DP-4–DP-6, TH-11.
- **Inferential status / availability:** `inferential_status: null`; `proof_available: false`; `owner_status: IMP` for MS-6. This audit key cannot enter proof closure.

### AUD-MS-6-REACH — explanatory reach (`Reach`; owner: MS-6)

- **Layer:** Semantic/modal comparison.
- **Statement / role:** `Reach(x,p',b')` records a further problem/context to which unchanged explanatory commitments of `x` apply.
- **Scope:** XReach and WideReach under a separately declared coverage condition.
- **Alternatives:** Induced generalization, transfer score, topical similarity, new derivations after changing the explanation.
- **Independence-witness plan:** `W-SEM`/`W-APP`: same original explanation, but only one further use preserves its explanatory commitments.
- **Conceptual necessity:** Separates explanatory reach from novelty, transformation, and induction.
- **Source warrant:** CR p. 221, MS-6; DF-14 p. 223; `S-BOI1`; I-REACH p. 258.
- **Discharge test:** `T-TRN` with commitment-preservation and declared domain coverage.
- **Non-entailments:** Novelty, transformation, broad output coverage, or data repetition does not entail reach; reach does not entail truth.
- **Direct / known dependents:** DF-14, TH-11, I-REACH, AGI/generality application comparisons.
- **Inferential status / availability:** `inferential_status: null`; `proof_available: false`; `owner_status: IMP` for MS-6. This audit key cannot enter proof closure.

### AUD-MS-7-R — available operation repertoire (`R`; owner: MS-7)

- **Layer:** Modal/operational.
- **Statement / role:** `R(s,h,t)` is the repertoire of operations available to system `s` at the indexed history/time.
- **Scope:** Representation use, deployment, retention, capacity, and repertoire expansion.
- **Alternatives:** Operations actually executed; logically specifiable operations; externally supplied tools; resource-free closure.
- **Independence-witness plan:** `W-MOD`: same trace, but one system has an unexercised operation in admissible continuations and the other lacks it.
- **Conceptual necessity:** Distinguishes capacity from occurrence.
- **Source warrant:** CR p. 221, MS-7; no itemized tag.
- **Discharge test:** Enumerate operations, access conditions, tools, and resource constraints; `T-ABL`, `T-LONG`.
- **Non-entailments:** Nonoccurrence does not entail unavailability; logical description does not entail physical availability.
- **Direct / known dependents:** SC-2, SC-7, DF-3, DF-4a, DF-11–DF-13, DF-20, BR-2/BR-7/BR-8, TH-12–TH-15.
- **Inferential status / availability:** `inferential_status: null`; `proof_available: false`; `owner_status: IMP` for MS-7. This audit key cannot enter proof closure.

### AUD-MS-7-MEM — causally accessible memory (`Mem`; owner: MS-7/SC-7)

- **Layer:** Causal/modal.
- **Statement / role:** `Mem(s,h,t)` is causally accessible memory; availability is over admissible continuations rather than actual reuse.
- **Scope:** Retention, reconstruction, lineage, and dispositions.
- **Alternatives:** Token persistence only; external notebook; reconstructible disposition; current context window; archival but inaccessible storage.
- **Independence-witness plan:** `W-MOD`/`W-CAU`: same stored token, only one system can access or reconstruct it in a relevant continuation.
- **Conceptual necessity:** Separates physical persistence from usable retention.
- **Source warrant:** CR p. 221, MS-7; SC-7 p. 222; no itemized tag.
- **Discharge test:** `T-RET`, `T-ABL`, boundary audit, delayed/context-shifted reuse.
- **Non-entailments:** Storage does not entail access, endorsement, `K_E`, or system ownership.
- **Direct / known dependents:** SC-7, DF-7a, DF-10–DF-13, BR-7–BR-8, TH-1–TH-3, TH-12.
- **Inferential status / availability:** `inferential_status: null`; `proof_available: false`; `owner_status: IMP` for MS-7/SC-7. This audit key cannot enter proof closure.

### AUD-MS-8-KE — explanatory knowledge (`K_E`; owner: MS-8)

- **Layer:** Epistemic.
- **Statement / role:** Primitive `K_E(x,p,b,h,t)` says `x` is a fallible improvement in the explanatory problem situation, not mere persistence or endorsement; applications must supply the domain interpretation.
- **Scope:** EKC and any explanatory-success claim.
- **Alternatives:** Factive knowledge; GoodNow; predictive fit; consensus; retention; score improvement; justified belief.
- **Independence-witness plan:** `W-EPI`: same CCP endpoint and retention, but one domain interpretation judges explanatory improvement and the other does not.
- **Conceptual necessity:** Keeps process, retention, and epistemic success distinct.
- **Source warrant:** CR p. 221, MS-8; §3 pp. 224–225; `S-BOI4`, `S-FOR8`, `S-SCC5`, `S-CT13`, `S-CTL15`; I-K_E p. 258.
- **Discharge test:** I-K_E plus `T-SUC`; evaluate independently of retention/self-report/evaluator selection.
- **Non-entailments:** CCP, Retained, GoodNow, HTV, fit, or survival does not entail `K_E`; `K_E` does not entail perfect truth or long-horizon `K_CT`.
- **Direct / known dependents:** DF-10, RC-1/RC-2, TH-2, TH-3, TH-8–TH-11, A-TH8, all EKC applications.
- **Inferential status / availability:** `inferential_status: null`; `proof_available: false`; `owner_status: IMP` for MS-8. This audit key cannot enter proof closure.

### AUD-MS-8-TRUE — correspondence truth (`True`; owner: MS-8)

- **Layer:** Epistemic/semantic.
- **Statement / role:** `True(x,p,b)` is an independent correspondence predicate supplied only where an application needs factivity.
- **Scope:** Explicit truth claims; not part of OCA, CCP, GoodNow, or the primitive meaning of `K_E`.
- **Alternatives:** Factive `K_E`; coherence; success; predictive accuracy; domain-relative formal validity.
- **Independence-witness plan:** `W-EPI`: hold all process and preference facts fixed while varying correspondence.
- **Conceptual necessity:** Makes fallibilism compatible with explicit factive claims without defining truth by retention or success.
- **Source warrant:** CR p. 221, MS-8; RC-1 p. 224; I-K_E p. 258; no independent source tag attached to the truth predicate.
- **Discharge test:** Provide a separate truth theory and domain evidence; use `T-SUC` where operationalized.
- **Non-entailments:** `K_E`, GoodNow, Pref, consensus, retention, HTV, or wide reach does not entail `True`.
- **Direct / known dependents:** RC-1, TH-2, TH-10, TH-11, I-K_E, I-MATH domain claims.
- **Inferential status / availability:** `inferential_status: null`; `proof_available: false`; `owner_status: IMP` for MS-8. This audit key cannot enter proof closure.

### MS-9 — declared cost/resource relation (`Cost`)

- **Layer:** Resource/physical-modal.
- **Statement / role:** `Cost` records declared resources; no unboundedness or efficiency claim is meaningful without it.
- **Scope:** Possibility, capacity, reliability, simulation, GCD/UED, and physical bridges.
- **Alternatives:** Ignore costs; asymptotic only; fixed budget; time/energy/memory/sample/communication/repair vectors.
- **Independence-witness plan:** `W-PHY`/`W-MOD`: same abstract capacity under one budget but not another.
- **Conceptual necessity:** Prevents possibility or generality from silently assuming infinite resources.
- **Source warrant:** CR p. 221, MS-9; I-RES p. 259; no itemized tag.
- **Discharge test:** Resource ledger plus `T-PHY`, `T-LONG`, perturbation/repair accounting.
- **Non-entailments:** Logical or CT possibility does not entail practicality, cheapness, efficiency, or bounded reliability.
- **Direct / known dependents:** CT-4, BR-3, BR-8, DF-11–DF-13, DF-20, I-RES, I-AGI.
- **Inferential status / availability:** `IMP`; exact MS-9 resource import; numerical budgets remain independently supplied.

### SC-1 — event satisfaction

- **Layer:** Structural semantics.
- **Statement / role:** `M,h,t |= e` iff typed event `e` belongs to `E(h,t)`.
- **Scope:** Event atoms.
- **Alternatives:** Interval/event-occurrence semantics; event tokens inferred from state differences.
- **Independence-witness plan:** `W-STR`: same states with differing event membership.
- **Conceptual necessity:** Fixes the satisfaction base case.
- **Source warrant:** CR p. 221, SC-1; no itemized tag.
- **Discharge test:** Typed membership check.
- **Non-entailments:** Event membership supplies no content, causation, or normative role.
- **Direct / known dependents:** All event-based satisfaction clauses and histories.
- **Inferential status / availability:** `IMP`; exact CR satisfaction constraint.

### SC-2 — representation satisfaction

- **Layer:** Semantic/causal.
- **Statement / role:** Represents requires an internal discriminable realization plus at least one available operation that uses its difference from relevant alternatives; observer labeling is insufficient.
- **Scope:** All semantic role realization.
- **Alternatives:** Decodability, correlation, resemblance, or token occurrence alone.
- **Independence-witness plan:** `W-SEM`: analyst-decodable but causally idle state versus a state used across alternatives.
- **Conceptual necessity:** Supplies the minimal anti-observer-imposition constraint on `Rep`.
- **Source warrant:** CR p. 221, SC-2; reconstruction/modeling clause with no itemized tag.
- **Discharge test:** `T-SEM`, `T-ABL`, relevant-alternative interventions.
- **Non-entailments:** External interpretability does not entail system representation.
- **Direct / known dependents:** DF-1–DF-7, TH-1, TH-2, TH-4–TH-9, TH-13, TH-17, BR-2/BR-4.
- **Inferential status / availability:** `IMP`; exact CR satisfaction constraint; positive cases require application evidence.

### SC-3 — reason-specific causal uptake (`UsesReason`)

- **Layer:** Causal/semantic.
- **Statement / role:** `UsesReason(s,c,α)` holds when reason-content-preserving recodings preserve the response family and alleged-defect changes, matched where possible on format/salience/channel, produce defect-appropriate response changes.
- **Scope:** Uptake, CCP, reasoned criticism, and physical bridge BR-5.
- **Alternatives:** Generic negative-token sensitivity; reward dependence; post-hoc rationalization; any causal influence of criticism tokens.
- **Independence-witness plan:** `W-CAU`: matched models with identical revision rates, one tracking defect content and one tracking tone/authority/format.
- **Conceptual necessity:** Distinguishes reason use from compliance or selection.
- **Source warrant:** CR pp. 221–222, SC-3, explicitly marked M reconstruction; source motivation for Uptake at DF-6 is `S-FOR3`, `S-BOI7`.
- **Discharge test:** `T-SEM`, `T-CRI`, `T-UPT`, `T-ABL`, including invalid/irrelevant/paraphrased controls.
- **Non-entailments:** Revision after criticism, reward change, or verbal rationale does not entail reason-specific uptake.
- **Direct / known dependents:** DF-6, DF-7a, BR-5, TH-7, TH-9, TH-12–TH-14, A-TH2.
- **Inferential status / availability:** `IMP`; exact SC-3 reconstruction; actual counterfactual satisfaction remains independently evidenced.

### SC-4 — causal authorship (`Authors_s`)

- **Layer:** Causal/authorship.
- **Statement / role:** Authorship assigns construction or reconstruction of problem-specific explanatory organization to operations of `s` across the predeclared boundary, not merely to retrieval, stock answers, designer-prepared responses, target-encoding evaluators, or external selectors; prior enabling knowledge does not itself defeat authorship.
- **Scope:** OCA, creative reconstruction, causal credit.
- **Alternatives:** Historical firstness; last-token emitter; no-prior-exposure criterion; designer credit; distributed/shared credit.
- **Independence-witness plan:** `W-CAU`: trace-equivalent lookup/preadapted and reconstructive models with different causal-credit explanations.
- **Conceptual necessity:** Captures the report’s origin/provenance discriminator.
- **Source warrant:** CR pp. 221–222, SC-4; DP-3 p. 225 with `S-BOI7`, `S-BOI10`, `S-BOI16`, `S-CB12`.
- **Discharge test:** `T-PROV`, `T-GEN`, `T-BND`, `T-ABL`, rival lookup/evaluator models.
- **Non-entailments:** Surface emission or runtime novelty is insufficient; prior communication is not automatically disqualifying.
- **Direct / known dependents:** DF-4, DF-7a, BR-6, TH-1, TH-4–TH-9, TH-13–TH-17.
- **Inferential status / availability:** `IMP`; exact SC-4 authorship reconstruction; attribution remains evidence-dependent.

### SC-5 — domain-supplied explanation satisfaction

- **Layer:** Semantic.
- **Statement / role:** `Explains` is satisfied only under the supplied domain interpretation; predictive fit is neither necessary nor sufficient under this clause.
- **Scope:** Every positive explanation judgment.
- **Alternatives:** Domain-general decision rule; prediction/compression/usefulness proxies.
- **Independence-witness plan:** `W-APP`: identical predictions under rival explanation theories.
- **Conceptual necessity:** Prevents a hidden explanation metric.
- **Source warrant:** CR p. 221, SC-5; I-EXP p. 258; `S-BOI1`, `S-FOR1` support DP-1, not a decision procedure.
- **Discharge test:** I-EXP plus rival/explanandum/background declaration and `T-ALT`.
- **Non-entailments:** Predictive success neither entails nor is required for explanation by this clause.
- **Direct / known dependents:** MS-5E, DF-8/DF-9, DP-1, TH-2, TH-11, I-EXP.
- **Inferential status / availability:** `IMP`; exact SC-5 constraint; domain judgments remain independent.

### SC-6 — named-theory physical possibility (`Possible_Θ`)

- **Layer:** Physical/modal.
- **Statement / role:** `Possible_Θ(φ)` holds iff named theory `Θ` admits the required arbitrarily accurate realization at the stated tolerance when that is the intended modality; abstract consistency is insufficient.
- **Scope:** Physical possibility, CT tasks, and bridge transfer.
- **Alternatives:** Logical consistency; nonzero chance; present buildability; finite approximation; theory-relative nomological possibility.
- **Independence-witness plan:** `W-PHY`: same abstract model, two physical theories or tolerances, only one admitting the realization.
- **Conceptual necessity:** Anchors modal claims in explicit physics and approximation semantics.
- **Source warrant:** CR p. 221, SC-6; CT-4 p. 227 with `S-CT13`; I-PHYS p. 258.
- **Discharge test:** Named `Θ`, tolerance/accuracy quantifiers, `T-PHY`, resource/error analysis.
- **Non-entailments:** Abstract consistency does not entail physical possibility; physical possibility does not entail buildability, cheapness, or actual occurrence.
- **Direct / known dependents:** CT-4, BR-2/BR-3/BR-8, DF-22/DF-23, TH-14/TH-15, I-PHYS/I-CT.
- **Inferential status / availability:** `IMP`; exact SC-6 physical-modal import; each positive claim still needs a named theory and evidence.

### SC-7 — retention (`Retained_s`)

- **Layer:** Causal/modal and epistemic firewall.
- **Statement / role:** Retention holds when a content-carrying state, or a causally sufficient reconstructible disposition, is accessible to a relevant possible later operation; it is neither endorsement nor `K_E`.
- **Scope:** EKC, memory, stable capacities.
- **Alternatives:** Token persistence; immediate reuse; external archive; endorsement; long-run frequency.
- **Independence-witness plan:** `W-MOD`/`W-EPI`: same endpoint with storage but no access, or access without endorsement/knowledge.
- **Conceptual necessity:** Allows reconstructible memory while preserving success independence.
- **Source warrant:** CR p. 222, SC-7; DF-10 p. 223; `S-BOI1`, `S-FOR3`, `S-FOR8` source the EKC reconstruction.
- **Discharge test:** `T-RET`, `T-ABL`, delayed/context-shifted accessibility under a frozen boundary.
- **Non-entailments:** Persistence or accessibility does not entail endorsement, `K_E`, truth, or authorship.
- **Direct / known dependents:** DF-10–DF-13, BR-7/BR-8, TH-1–TH-3, TH-12.
- **Inferential status / availability:** `IMP`; exact SC-7 satisfaction constraint; actual retention remains application evidence.

### SC-8 — critical-lineage satisfaction

- **Layer:** Causal/semantic.
- **Statement / role:** One predeclared provenance subgraph and matched counterfactuals must connect origin, descendant candidate, candidate-directed criticism, defect-appropriate response, and endpoint; temporal co-occurrence or topic similarity is insufficient.
- **Scope:** CCPResult, CCP, and EKC.
- **Alternatives:** Event-order chain; analyst narrative; endpoint-only success; unrelated retained insight.
- **Independence-witness plan:** `W-CAU`: same event multiset and order with connected versus disconnected role-preserving provenance.
- **Conceptual necessity:** Enforces same-episode, same-endpoint critical correction.
- **Source warrant:** CR p. 222, SC-8; R/M reconstruction, no itemized external tag.
- **Discharge test:** `T-PROV`, `T-UPT`, `T-RET`, `T-ABL`; verify every enumerated SC-8 conjunct.
- **Non-entailments:** Topic continuity, time order, or a later successful result does not entail lineage.
- **Direct / known dependents:** DF-7a, DF-7, DF-10, TH-1–TH-3, TH-7–TH-9, TH-12–TH-13.
- **Inferential status / availability:** `IMP`; exact SC-8 satisfaction constraint; satisfaction requires evidence.

### AUD-DF-4A-11-13-QCHI — declared problem class and enabling conditions (`Q`, `χ`; owners: DF-4a, DF-11–DF-13)

- **Layer:** Modal/dispositional.
- **Statement / role:** OCap uses a nonempty declared `Q`; stable critical capacity and GCD use non-singleton `Q`; `χ` lists enabling conditions, perturbations, scaffolding, and resources.
- **Scope:** DF-4a, DF-11, DF-12, DF-13, BR-8, I-AGI.
- **Alternatives:** Benchmark list; open-ended natural-language domain; all possible problems; tacit/default scaffolding.
- **Independence-witness plan:** `W-MOD`: same system is capable over one bounded `Q,χ` but not another; vary hidden scaffolding.
- **Conceptual necessity:** Makes generality and capacity relative rather than absolute.
- **Source warrant:** CR pp. 222–223, DF-4a and DF-11–DF-13; `S-BOI1`, `S-CB12`, `S-BOI6`, `S-BOI7`, `S-BOI16`; I-AGI p. 258.
- **Discharge test:** Predeclare `Q,χ`; `T-LONG`, `T-TRN`, perturbation/resource audit.
- **Non-entailments:** Finite benchmark breadth does not entail GCD/UED; singleton OCap does not entail generality.
- **Direct / known dependents:** OCap, Cap_CR, GCD, UED, BR-8, DF-23, TH-1, TH-7, TH-12, TH-13, TH-15.
- **Inferential status / availability:** `inferential_status: null`; `proof_available: false`; `owner_status: DEF` for DF-4a and DF-11–DF-13. This audit key cannot enter proof closure.

### AUD-DF-13-NDB — UED no-domain-bar clause (owner: DF-13)

- **Layer:** Modal/dispositional, source-qualified conjecture.
- **Statement / role:** For every physically admitted problem in declared domain `D`, no fixed subdomain restriction in the stable organization bars all admissible continuations containing originative conjecture and critical improvement, given the resources in `χ`.
- **Scope:** UED only; it extends GCD.
- **Alternatives:** Broad but bounded GCD; finite benchmark generality; universal hardware; unrestricted omnipotence.
- **Independence-witness plan:** `W-MOD`: two systems share every observed episode, but one has a hidden terminal/subdomain bar in unobserved continuations.
- **Conceptual necessity:** States the strong universality claim without collapsing it into finite breadth.
- **Source warrant:** CR p. 223, DF-13, marked X/R/Q; `S-BOI6`, `S-BOI7`, `S-BOI16`.
- **Discharge test:** No finite discharge is sufficient; `T-LONG` can provide fallible evidence while countermodels remain. The strong claim stays source-qualified.
- **Non-entailments:** GCD, finite success, universal computation, or universal construction does not entail UED.
- **Direct / known dependents:** DF-13, TH-12, TH-13, I-AGI.
- **Inferential status / availability:** `inferential_status: null`; `proof_available: false`; `owner_status: DEF` for DF-13. This audit key cannot enter proof closure.

### AUD-IR-5-BR-RHO — one predeclared realization map (`ρ`; owners: IR-5, BR-1–BR-8)

- **Layer:** Physical bridge.
- **Statement / role:** A single map `ρ` connects a target physical region/history to CR roles and must preserve every transferred predicate across the declared counterfactual family.
- **Scope:** IR-5, BR-1–BR-8, DF-22/DF-23, physical application tuple.
- **Alternatives:** Per-trial interpretation; trace-fitting; multiple incompatible maps; coarse-grained functional or mechanistic realizations.
- **Independence-witness plan:** `W-PHY`: one mapping generalizes across recodings/interventions while a post-hoc map works only on the successful trace.
- **Conceptual necessity:** Prevents physical realization from becoming unconstrained reinterpretation.
- **Source warrant:** CR p. 226, IR-5; pp. 227–228, bridge layer; application tuple p. 259; no itemized source tag for the map requirement.
- **Discharge test:** Freeze `ρ` before intervention; run `T-PHY`, `T-SEM`, `T-CRI`, `T-ABL` and predicate-by-predicate preservation audit.
- **Non-entailments:** Correlation, token decoding, or one successful trace does not entail realization.
- **Direct / known dependents:** BR-1–BR-8, DF-22, DF-23, TH-14, TH-15, every physical attribution.
- **Inferential status / availability:** `inferential_status: null`; `proof_available: false`; `owner_status: IMP` for IR-5 and BR-1–BR-8. This audit key cannot enter proof closure.

### AUD-PHYS-TASK-NET — component task-network reconstruction (owner: active physical layer §7.2)

- **Layer:** Physical realization/modeling reconstruction.
- **Statement / role:** CR-1.0 does not model creativity as one extensional CT task “output a new good explanation.” It proposes a network/history of component tasks for representation, conjecture, evidence interpretation, criticism, revision, memory, and network revision; `Explains`, authorship, and `K_E` remain independent bridges.
- **Scope:** Constructor-theoretic realization and any task-level creativity claim.
- **Alternatives:** One extensional success task; answer set pre-encoding; end-to-end behavior specification; task network with different components/causal organization.
- **Independence-witness plan:** `W-PHY`/`W-CAU`: same input-output extension under a pre-encoded lookup constructor and under a component network with auditable semantic/causal roles.
- **Conceptual necessity:** Exposes the provenance problem and prevents successful outputs from defining creative organization.
- **Source warrant:** Active CR model p. 228, §7.2 paragraph after DF-23, explicitly marked R/M. Source motivation is DP-3/`S-CB12`; no source tag warrants the task-network solution itself.
- **Discharge test:** Declare component tasks and their composition; verify BR-1–BR-8 predicate by predicate; retain I-EXP/I-K_E/SC-4 as independent.
- **Non-entailments:** Extensional task success does not entail explanation, authorship, epistemic success, OCA, or GCD; the proposed network does not prove noncomputability.
- **Direct / known dependents:** Physical programme pp. 273–275, DF-22/DF-23 application reasoning, constructor/creator non-equivalences.
- **Inferential status / availability:** `inferential_status: null`; `proof_available: false`; `owner_status: IMP` for the active R/M reconstruction. This audit key cannot enter proof closure.

## 5. Epistemic reconstruction choices

### RC-1 — fallible `K_E`, independent factivity

- **Layer:** Epistemic reconstruction choice.
- **Statement / role:** `K_E` is not stipulated to entail perfect truth; add `True(x,p,b)` independently when factivity is required.
- **Scope:** EKC and every truth-bearing application claim.
- **Alternatives:** Factive knowledge; verisimilitude; justified-success semantics; no truth predicate.
- **Independence-witness plan:** `W-EPI`: preserve `K_E` while varying `True`, including a fallibly improved but partly false explanation.
- **Conceptual necessity:** Preserves the report’s fallibilism and stops EKC from becoming certainty.
- **Source warrant:** CR p. 224, RC-1; MS-8 p. 221; source-facing fallibility `S-BOI1`, `S-FOR3`, `S-FOR10` through DP-4.
- **Discharge test:** Separate I-K_E and truth dossiers; test success independently of retention and factivity.
- **Non-entailments:** `K_E` does not entail perfect truth, certainty, or finality.
- **Direct / known dependents:** TH-2, TH-10, TH-11, I-K_E, legal application step 7 p. 280.
- **Inferential status / availability:** `IMP`; exact RC-1 reconstruction policy; any factive application remains independently warranted.

### RC-2 — explanatory/physical knowledge bridge is not definitional

- **Layer:** Epistemic/physical bridge policy.
- **Statement / role:** Human scientific knowledge may instantiate both `K_E` and `K_CT`, but `K_E -> K_CT` needs a physical embodiment bridge and `K_CT -> K_E` is false.
- **Scope:** Mixed knowledge claims and TH-10.
- **Alternatives:** Identity of knowledge types; universal `K_E -> K_CT`; universal `K_CT -> K_E`; no overlap.
- **Independence-witness plan:** `W-EPI`/`W-PHY`: resilient false doctrine or gene for `K_CT` without `K_E`; short-lived explanatory advance for `K_E` without long-horizon `K_CT`.
- **Conceptual necessity:** Prevents persistence/truth/understanding conflation.
- **Source warrant:** CR p. 224, RC-2; sources `S-BOI4`, `S-FOR8`, `S-SCC5`, `S-CT13`, `S-CTL15`.
- **Discharge test:** Separate I-K_E and I-K_CT; provide a named embodiment bridge for any forward implication.
- **Non-entailments:** Neither knowledge predicate entails the other at arbitrary environment/horizon.
- **Direct / known dependents:** TH-10; natural-selection, scientific-knowledge, and physical-realization applications.
- **Inferential status / availability:** `IMP`; exact RC-2 bridge policy; positive cross-type instances remain independently warranted.

### RC-3 — conservative art scope

- **Layer:** Semantic/application boundary.
- **Statement / role:** The explanatory core applies to art only when an application independently establishes problem-directed, criticizable aesthetic knowledge and a defensible `Purports`/`Explains`/`K_E` mapping, or declares a conservative parallel extension.
- **Scope:** Artwork and artistic-act classifications.
- **Alternatives:** All art is explanation; no art is explanation; novelty/popularity/feeling as sufficient success; separate aesthetic predicates.
- **Independence-witness plan:** `W-APP`: identical artifact under a defensible problem-directed interpretation and under a product-only interpretation.
- **Conceptual necessity:** Prevents the model from forcing all art into propositional science.
- **Source warrant:** CR p. 224, RC-3; `S-BOI14`; application I-ART/I-AR-SHARED pp. 259, 265–266.
- **Discharge test:** I-ART, I-AR-SHARED, I-EXP and, for tacit criticism, I-MIND-TACIT; reason/standard interventions.
- **Non-entailments:** Novelty, popularity, felt response, OCA, CCP, HTV, or GoodNow does not entail objective artistic success or beauty.
- **Direct / known dependents:** Art applications, I-ART, I-AR-SHARED, I-MIND-TACIT.
- **Inferential status / availability:** `IMP`; exact RC-3 scope policy; positive artistic mappings remain independently warranted.

## 6. Explicit Deutschian postulates and adaptation bridge

### DP-1 — objective explanatory realism

- **Layer:** Semantic/epistemic postulate.
- **Statement / role:** Problems and explanations can concern objective reality; correction is not merely perspective change; `Explains` is not extensionally reducible to prediction, correlation, control, compression, or usefulness.
- **Scope:** Source-facing CR models using objective explanation/correction.
- **Alternatives:** Instrumentalism, perspectivism, predictive or compression reduction, pragmatism.
- **Independence-witness plan:** `W-SRC`/`W-SEM`: compare an objective-explanation model with a proxy-reductive model agreeing on all predictions.
- **Conceptual necessity:** Gives “correction” objective rather than preference-only content.
- **Source warrant:** CR p. 225, DP-1, mark X; `S-BOI1`, `S-FOR1`.
- **Discharge test:** Source-entitlement audit plus domain I-EXP/I-K_E; seek proxy-equivalent countermodels.
- **Non-entailments:** Objectivity does not supply a decision procedure, truth guarantee, or unique explanation.
- **Direct / known dependents:** DP-6, DF-8/DF-9, TH-4, TH-11, scientific/art applications.
- **Inferential status / availability:** `IMP`; exact DP-1 postulate, not an empirical fact or definition.

### DP-2 — conjectural origin and anti-induction

- **Layer:** Epistemic/causal postulate.
- **Statement / role:** No observation-to-theory rule mechanically creates the relevant explanatory content; conjectures may be caused and use prior ideas without prior derivation/justification; repeated instances do not license inductive ascent to a universal explanatory law.
- **Scope:** Conjecture/origin claims, science, learning, and applications that contrast explanation with induction.
- **Alternatives:** Enumerative induction, Bayesian generation as sufficient content source, data-to-theory algorithms, prior-justification requirements.
- **Independence-witness plan:** `W-SRC`/`W-CAU`: hold data fixed while rival conjectures arise; separately model a mechanical rule whose design encodes the explanatory organization.
- **Conceptual necessity:** Preserves conjectural origin and blocks raw-data theory generation by fiat.
- **Source warrant:** CR p. 225, DP-2, mark X; `S-BOI1`, `S-FOR3`.
- **Discharge test:** Audit whether explanatory organization resides in the target, generator, prior, or evaluator; compare actual rivals.
- **Non-entailments:** Physical causation does not equal logical derivation; repeated success does not establish a universal explanation.
- **Direct / known dependents:** OM-2, OM-4/OM-5, scientific inquiry application pp. 264–265; source-facing interpretation of OCA.
- **Inferential status / availability:** `IMP`; exact DP-2 postulate.

### DP-3 — causal authorship

- **Layer:** Causal/authorship postulate.
- **Statement / role:** Creative credit tracks construction or reconstruction of problem-specific explanatory organization, not surface emission; design, training, repertoire, evaluators, tools, interaction, and selection may all contribute.
- **Scope:** OCA and all component/composite attributions.
- **Alternatives:** Historical originality, last-emitter rule, no-training criterion, designer monopoly, equal shared credit.
- **Independence-witness plan:** `W-CAU`: trace-equivalent lookup, external-selector, reconstructive, and distributed-credit models.
- **Conceptual necessity:** Makes the origin claim causally discriminating while permitting creative reconstruction.
- **Source warrant:** CR p. 225, DP-3, mark X/R; `S-BOI7`, `S-BOI10`, `S-BOI16`, `S-CB12`.
- **Discharge test:** `T-PROV`, `T-GEN`, `T-BND`, `T-ABL`, explicit rival causal-credit graphs.
- **Non-entailments:** Output emission/novelty is insufficient; prior exposure neither establishes nor automatically defeats authorship.
- **Direct / known dependents:** SC-4, DF-4, TH-4, TH-5, TH-7, TH-13, TH-17, BR-6.
- **Inferential status / availability:** `IMP`; exact DP-3 postulate; each attribution still needs evidence.

### DP-4 — fallibility

- **Layer:** Epistemic postulate.
- **Statement / role:** No explanation, criticism, standard, framing, proof method, institution, or postulate becomes immune to criticism through retention, authority, testing, or status; GoodNow, `K_E`, and Pref imply neither certainty nor finality.
- **Scope:** Every epistemic and standard claim.
- **Alternatives:** Verification, incorrigible foundations, postulate immunity, monotonic confirmation.
- **Independence-witness plan:** `W-EPI`: a retained/currently preferred result later fails; contrast an immunity model.
- **Conceptual necessity:** Keeps error correction open and success provisional.
- **Source warrant:** CR p. 225, DP-4, mark X; `S-BOI1`, `S-FOR3`, `S-FOR10`.
- **Discharge test:** Preserve possible criticism/revision routes; audit certainty/finality language and standard revision.
- **Non-entailments:** Passing tests, authority, retention, GoodNow, or `K_E` does not entail certainty/finality.
- **Direct / known dependents:** DF-9/DF-10, OM-8, TH-2, TH-11, scientific inquiry, standards audit.
- **Inferential status / availability:** `IMP`; exact DP-4 postulate.

### DP-5 — reasoned criticism

- **Layer:** Semantic/epistemic postulate.
- **Statement / role:** Criticism compares actual rivals by reasons bearing on the represented problem; observations become criticisms only through fallible interpretations of setup, background, and rival predictions; survival removes a criticism but does not inductively confirm.
- **Scope:** PBCrit, Uptake, science, and reason-sensitive applications.
- **Alternatives:** Raw-data criticism; reward/selection as criticism; any rejected candidate as criticized; Bayesian confirmation.
- **Independence-witness plan:** `W-SEM`/`W-CAU`: same observation or negative signal with and without a problem-bearing interpretation and defect-specific use.
- **Conceptual necessity:** Separates rational correction from selection and generic feedback.
- **Source warrant:** CR p. 225, DP-5, mark X/R; `S-FOR3`, `S-BOI1`.
- **Discharge test:** `T-CRI`, `T-UPT`, `T-SEM`; declare rivals, auxiliaries, instruments, and alleged defect.
- **Non-entailments:** Observation, rejection, reward, or survival does not entail criticism or confirmation.
- **Direct / known dependents:** DF-5/DF-6, OM-3–OM-7, TH-9, scientific/theorem-prover applications.
- **Inferential status / availability:** `IMP`; exact DP-5 postulate; application role/evidence remains separate.

### DP-6 — good-explanation constraint

- **Layer:** Semantic/epistemic postulate.
- **Statement / role:** Among actual rivals, hard-to-vary problem-bearing structure is an explanatory merit, but not a complete metric, unique procedure, or truth guarantee; the problem, variation family, and standards remain criticizable.
- **Scope:** HTV and GoodNow comparisons.
- **Alternatives:** Scalar simplicity, fit, compression, elegance, popularity, or unrestricted rigidity.
- **Independence-witness plan:** `W-SEM`: compare substantive versus superficial variations and two rival variation families yielding different rankings.
- **Conceptual necessity:** Captures the source’s good-explanation constraint without overformalizing it.
- **Source warrant:** CR p. 225, DP-6, mark X/R; `S-BOI1`.
- **Discharge test:** I-EXP/I-HTV; declare `V`, explanandum, background, rivals, and standards.
- **Non-entailments:** HTV does not entail truth, finality, uniqueness, or a scalar ranking.
- **Direct / known dependents:** DF-8, DF-9, TH-11, I-HTV.
- **Inferential status / availability:** `IMP`; exact DP-6 postulate; any concrete HTV judgment remains an independent application import.

### DP-7 — knowledge growth through criticism/error elimination

- **Layer:** Epistemic/process postulate.
- **Statement / role:** Explanatory progress requires more than origin: criticism/error elimination produces a provisionally improved, retained problem situation and normally new problems, without guaranteed monotonicity or convergence.
- **Scope:** Source-facing knowledge-growth narratives and EKC applications.
- **Alternatives:** Origin-only creativity; monotonic cumulative learning; convergence guarantees; selection-only progress.
- **Independence-witness plan:** `W-EPI`: OCA without critical improvement; CCP that worsens; later correction that reopens problems.
- **Conceptual necessity:** Separates explanation production from explanatory knowledge growth.
- **Source warrant:** CR p. 225, DP-7, mark X/R; `S-FOR3`, `S-BOI1`.
- **Discharge test:** One CLine endpoint, independent I-K_E, retention/reuse, and new-problem audit.
- **Non-entailments:** OCA or CCP alone does not entail progress; progress does not imply monotonicity/convergence.
- **Direct / known dependents:** DF-10, OM-10, scientific/community applications; no theorem may import more than the exact postulate.
- **Inferential status / availability:** `IMP`; exact DP-7 postulate; positive progress remains dependent on independently interpreted `K_E`.

### DP-8 — generality/universality conjecture

- **Layer:** Modal/person/AGI postulate.
- **Statement / role:** Persons can create explanatory knowledge; the source argues that people are universal explainers and guesses that genuine AGIs are persons/general-purpose explainers; intermediate universalities and implementation remain open.
- **Scope:** Person, UED, and AGI source-facing claims.
- **Alternatives:** Graded/specialized intelligence; creativity without personhood; personhood without UED; intermediate universalities.
- **Independence-witness plan:** `W-SRC`/`W-MOD`: preserve observed human/AI performance while varying hidden domain bars, personhood, or intermediate capacity.
- **Conceptual necessity:** Records the strong source conjecture without baking it into OCA/GCD.
- **Source warrant:** CR p. 225, DP-8, mark X/Q; `S-BOI3`, `S-BOI6`, `S-BOI7`, `S-BOI16`.
- **Discharge test:** Separate I-MIND, I-INT, I-AGI, I-ETH, `Q,χ`, and expanding-horizon evidence; no finite certification.
- **Non-entailments:** OCA, CCP, EKC, GCD, universal computation, or benchmark breadth does not entail personhood, consciousness, AGI, or UED.
- **Direct / known dependents:** DF-13 source profile, TH-15, I-AGI/person applications.
- **Inferential status / availability:** `IMP`; exact DP-8 postulate only with the X/Q split visible. Universal/person/AGI attribution has `inferential_status: null`, `proof_available: false` absent independent imports.

### DP-9 — physicality without computational sufficiency

- **Layer:** Physical/computational postulate.
- **Statement / role:** Creativity is physically instantiated at a software level, so substrate alone does not bar nonbiological realization; universal computation permits relevant simulation in principle but provides neither the creative program nor semantic authorship.
- **Scope:** Artificial realization, computation, and implementation claims.
- **Alternatives:** Biological essentialism; computational sufficiency; nonphysical creativity; program/semantics identity.
- **Independence-witness plan:** `W-PHY`: a universal computer running a constant/copy program versus the same hardware running a putative creative organization; preserve substrate while varying organization.
- **Conceptual necessity:** Blocks both substrate chauvinism and hardware/computation sufficiency.
- **Source warrant:** CR p. 225, DP-9, mark X/O; `S-BOI6`, `S-BOI7`, `S-BOI16`, `S-FOR13`.
- **Discharge test:** I-COMP, I-PHYS, actual program/realization, BR-1–BR-8; keep the implementation gap open.
- **Non-entailments:** Computed, simulated, universal-computer, or fixed low-level software does not entail thinking, authorship, AGI, or noncreativity.
- **Direct / known dependents:** TH-13, TH-15, A-TH7, LLM/AGI/theorem-system applications.
- **Inferential status / availability:** `IMP`; exact DP-9 postulate with the O qualifier retained; concrete mechanism claims remain independent application imports.

### DP-10 — natural-selection contrast

- **Layer:** Causal/evolutionary/epistemic postulate.
- **Statement / role:** Natural selection can create parochial adaptive/physical knowledge by heritable variation and differential replication without represented problems/explanations/reasons; person-level conjectures are purposive attempts, and criticism can eliminate them without eliminating the author; lower-level selection may implement the higher-level process without erasing the distinction.
- **Scope:** Evolution, evolutionary algorithms, `K_CT`, and criticism contrasts.
- **Alternatives:** Selection is criticism; all adaptation is explanation; strict process identity; no implementation relation.
- **Independence-witness plan:** `W-SEM`: minimal replicators with selection but no semantic roles; rational critic without reproduction; multilevel implementation pair.
- **Conceptual necessity:** Preserves shared variation/selection structure while blocking semantic collapse.
- **Source warrant:** CR p. 225, DP-10, mark X; `S-BOI4`, `S-BOI15`, `S-BOI16`, `S-FOR3`, `S-FOR8`, `S-CTL15`.
- **Discharge test:** I-EVO, I-K_CT, AB-1, provenance and representation/reason interventions.
- **Non-entailments:** Selection, adaptation, novelty, or survival does not entail PBCrit, OCA, CCP, `K_E`, foresight, or explanation.
- **Direct / known dependents:** TH-8, TH-9, natural-selection/evolutionary-algorithm applications, A-TH6.
- **Inferential status / availability:** `IMP`; exact DP-10 postulate; actual biological/evolutionary facts remain independent application imports.

### AB-1 — adaptation-to-physical-knowledge bridge

- **Layer:** Causal/physical-knowledge bridge postulate.
- **Statement / role:** If a heritable recipe `i` has problem-specific causal effects contributing to its differential replication and continued instantiation in environment `e` across perturbations `ρ` and horizon `τ`, then `K_CT(i,e,ρ,τ)`; heritability or frequency alone is insufficient.
- **Scope:** Natural selection and adaptation claims about `K_CT`.
- **Alternatives:** Frequency-only, heritability-only, survival-only, etiological function, repair-based or constructor-based accounts.
- **Independence-witness plan:** `W-PHY`: equally frequent/heritable recipes, only one causally contributes to replication/persistence under the declared perturbations.
- **Conceptual necessity:** Supplies the missing causal bridge from selection facts to physical knowledge.
- **Source warrant:** CR p. 225, AB-1, mark X/R; `S-BOI4`, `S-FOR8`, `S-CTL15`, `S-SCC5`.
- **Discharge test:** I-EVO and I-K_CT; manipulate recipe, environment, perturbations, horizon, and replication/repair mechanism.
- **Non-entailments:** Frequency, heredity, survival, or selection alone does not entail `K_CT`; `K_CT` does not entail explanation or `K_E`.
- **Direct / known dependents:** TH-8, TH-9, A-TH6, evolutionary/natural-selection applications.
- **Inferential status / availability:** `IMP`; exact AB-1 postulate; any actual antecedent and `K_CT` attribution remains independently evidenced.

### DP-11 — constructor asymmetry

- **Layer:** Physical/causal-authorship postulate.
- **Statement / role:** Constructors reliably perform tasks while retaining capacity; that status does not originate the program, explanation, or criterion executed. Creativity can provide constructor know-how, but constructorhood alone supplies no creativity.
- **Scope:** Constructor/creator comparisons and universal construction claims.
- **Alternatives:** Constructor equals creator; every creator is a persisting constructor; program execution counts as origin.
- **Independence-witness plan:** `W-PHY`/`W-CAU`: programmed copier/universal constructor with no authored explanation; one-shot originator lacking universal/repeat capacity.
- **Conceptual necessity:** Separates task reliability from explanatory provenance.
- **Source warrant:** CR p. 225, DP-11, mark X/R; `S-BOI3`, `S-BOI6`, `S-CT13`, `S-SCC5`, `S-SCC7`, `S-MAI20`.
- **Discharge test:** CT task/capacity audit plus `T-PROV`/`T-GEN` for origin credit.
- **Non-entailments:** Constructor or universal constructor does not entail OCA/GCD; OCA does not entail universal construction.
- **Direct / known dependents:** TH-5, TH-15, A-CT1–A-CT3 pp. 274–275, A-TH5.
- **Inferential status / availability:** `IMP`; exact DP-11 postulate; overlap claims require application evidence.

## 7. Constructor-theory vocabulary and physical-knowledge import

### CT-1 — substrate, attribute, variable

- **Layer:** Physical/constructor-theory vocabulary.
- **Statement / role:** A substrate is a physical system; an attribute is a set of its states; a variable is a set of mutually disjoint attributes.
- **Scope:** Physical models relative to `Θ_CT`.
- **Alternatives:** State-vector variables, observables, coarse-grained macrostates, overlapping attributes.
- **Independence-witness plan:** `W-PHY`: same abstract CR token mapping under disjoint versus overlapping physical attributes.
- **Conceptual necessity:** Supplies the carrier vocabulary for tasks and information.
- **Source warrant:** CR p. 227, CT-1; `S-CT13`; the collective CT source line also lists `S-CTI15`, `S-CTL15`, `S-SCC3`, `S-SCC5`, `S-SCC7`.
- **Discharge test:** Name substrates/state sets; verify disjointness for every claimed variable.
- **Non-entailments:** A substrate/attribute/variable does not entail information, meaning, constructorhood, or creativity.
- **Direct / known dependents:** CT-2–CT-7, BR-2/BR-3, TH-5/TH-6/TH-15.
- **Inferential status / availability:** `DEF`; exact CT-1 vocabulary definition; actual physical assignments have `inferential_status: null`, `proof_available: false` until evidenced.

### CT-2 — task

- **Layer:** Physical/constructor-theory vocabulary.
- **Statement / role:** A task is a set of input-attribute/output-attribute pairs on substrates.
- **Scope:** Constructor and possibility claims.
- **Alternatives:** Dynamical trajectory, algorithm, function over microstates, operational transformation.
- **Independence-witness plan:** `W-PHY`: same extensional pair set realized by different dynamics, or same dynamics supporting different coarse-grained task specifications.
- **Conceptual necessity:** Expresses counterfactual physical transformations without importing semantics.
- **Source warrant:** CR p. 227, CT-2; `S-CT13`.
- **Discharge test:** Enumerate attributes/pairs and tolerances; distinguish task specification from actual history.
- **Non-entailments:** A task does not entail an available constructor, semantic purpose, success criterion, or authorship.
- **Direct / known dependents:** CT-3, CT-4, CT-6, BR-3, TH-5/TH-6/TH-15.
- **Inferential status / availability:** `DEF`; exact CT-2 vocabulary definition.

### CT-3 — constructor-for relation

- **Layer:** Physical/constructor-theory vocabulary.
- **Statement / role:** `ConstructorFor(C,T)` means `C` causes task `T` while retaining the ability to cause it again in the relevant respect.
- **Scope:** Repeatable/reconstructible task performance.
- **Alternatives:** One-shot cause; catalyst; cyclic device; replaceable network; approximate retained capacity.
- **Independence-witness plan:** `W-PHY`: same first transformation with and without retained/reconstructible capacity.
- **Conceptual necessity:** Distinguishes a constructor from a one-off causal mechanism.
- **Source warrant:** CR p. 227, CT-3; `S-CT13`, with examples/motivation `S-SCC5`.
- **Discharge test:** Repeated/counterfactual task trials at declared tolerance; measure degradation/repair.
- **Non-entailments:** Repeated task capacity does not entail origin of its program, semantic role, or creativity.
- **Direct / known dependents:** CT-4, CT-6, DP-11, BR-3/BR-8, TH-5/TH-15.
- **Inferential status / availability:** `DEF`; exact CT-3 definition; actual capacity has `inferential_status: null`, `proof_available: false` until evidenced.

### CT-4 — constructor-theoretic possibility

- **Layer:** Physical/modal vocabulary.
- **Statement / role:** `Possible_CT(T)` means the laws impose no positive lower bound preventing arbitrarily accurate/reliable approximations to a constructor for `T`; it does not mean currently buildable or cheap.
- **Scope:** Task possibility relative to `Θ_CT`.
- **Alternatives:** Actual construction; nonzero probability; finite target accuracy; engineering feasibility; ordinary modal possibility.
- **Independence-witness plan:** `W-PHY`: a task with improving approximation sequence versus one with a positive error floor, holding current engineering fixed.
- **Conceptual necessity:** Gives the intended constructor-theoretic modality.
- **Source warrant:** CR p. 227, CT-4; `S-CT13`; compare SC-6 p. 221.
- **Discharge test:** Named physical laws, asymptotic accuracy/reliability criterion, tolerance and resource accounting.
- **Non-entailments:** Possibility does not entail buildability, present capability, low cost, or actual performance.
- **Direct / known dependents:** CT-5/CT-6, BR-2/BR-3, TH-5/TH-6/TH-15, I-CT/I-PHYS.
- **Inferential status / availability:** `DEF`; exact CT-4 definition; any positive physical possibility has `inferential_status: null`, `proof_available: false` until warranted under `Θ_CT`.

### CT-5 — information variables/media and interoperability

- **Layer:** Physical/information-theoretic.
- **Statement / role:** An information variable supports possible cloning and every permutation; an information medium carries at least one such variable. Interoperability states that composites of information media carry the corresponding product variable.
- **Scope:** Physical information, copying, composition, and memory.
- **Alternatives:** Shannon information; distinguishability only; copying without all permutations; interoperability omitted or restricted.
- **Independence-witness plan:** `W-PHY`: media each satisfying local operations while the composite does or does not support the product variable.
- **Conceptual necessity:** Supplies physical discrimination/copying/composition, but not meaning.
- **Source warrant:** CR p. 227, CT-5; `S-CTI15`, `S-SCC3`.
- **Discharge test:** Demonstrate/derive cloning, permutations, and product-variable support under the named theory and tolerance.
- **Non-entailments:** CT information does not entail semantic content, understanding, `K_E`, or creativity.
- **Direct / known dependents:** BR-2, BR-4, BR-7, TH-5/TH-6/TH-10/TH-15.
- **Inferential status / availability:** `inferential_status: null`; `proof_available: false`; `classification_blocker: mixed DEF/IMP clause`. CT-5 bundles eliminable vocabulary with the substantive interoperability principle, so it cannot receive exactly one lawful status without an authoritative split; the exact clause is quarantined pending that split.

### CT-6 — universal constructor

- **Layer:** Physical/modal.
- **Statement / role:** `UniversalConstructor(C,D)` means that, with suitable programs and raw materials, `C` can perform every physically possible construction task in declared domain `D`.
- **Scope:** Universal construction only, relative to domain/resources/programs.
- **Alternatives:** Universal computer; self-reproducer; universal constructor over another domain; current program repertoire.
- **Independence-witness plan:** `W-PHY`/`W-CAU`: universal hardware executing only supplied copy programs versus a limited originator.
- **Conceptual necessity:** States construction reach without semantic authorship.
- **Source warrant:** CR p. 227, CT-6; `S-BOI3`, `S-BOI6`, `S-CT13`; asymmetry also `S-MAI20`.
- **Discharge test:** Declare `D`, program/raw-material assumptions, physical possibility, and retained/reconstructible task capacity.
- **Non-entailments:** Universal construction does not entail OCA, GCD, UED, universal explanation, or authorship; OCA does not entail universal construction.
- **Direct / known dependents:** DP-11, TH-5, TH-6, TH-15, A-CT1–A-CT3, A-TH5.
- **Inferential status / availability:** `DEF`; exact CT-6 definition; actual universality has `inferential_status: null`, `proof_available: false` until evidenced.

### CT-7 — constructor-theoretic physical knowledge (`K_CT`)

- **Layer:** Physical/causal-epistemic analogue.
- **Statement / role:** `K_CT(i,e,ρ,τ)` is information whose causal action helps it remain instantiated in a suitable environment under declared perturbations and horizon; the report explicitly does not claim a completed standalone constructor theory of knowledge.
- **Scope:** Physical knowledge, adaptation, and RC-2.
- **Alternatives:** Mere persistence, copying, fitness, causal efficacy, truth, understanding, explanatory knowledge.
- **Independence-witness plan:** `W-PHY`: equally persistent items, only one causally maintains/reconstructs itself under the declared perturbations; vary environment/horizon.
- **Conceptual necessity:** Keeps physical resilient information distinct from explanatory success.
- **Source warrant:** CR pp. 224 and 227, §3 and CT-7; `S-CT13`, `S-CTI15`, `S-CTL15`, `S-SCC3`, `S-SCC5`, `S-SCC7`; open-program caveat at `S-SCC7` print pp. 215–221.
- **Discharge test:** I-K_CT, named environment, perturbation class, horizon, causal maintenance mechanism; for selection use AB-1.
- **Non-entailments:** Persistence, heredity, survival, frequency, information, truth, explanation, understanding, OCA, or CCP is not equivalent to `K_CT`; `K_CT -> K_E` is false.
- **Direct / known dependents:** RC-2, AB-1, TH-8–TH-10, natural-selection and constructor applications.
- **Inferential status / availability:** `IMP`; CT-7 is a primitive counterfactual physical-knowledge relation and open programme, not an eliminable definition. Every actual attribution still has `inferential_status: null`, `proof_available: false` until independently discharged.

## 8. Physical bridge conditions

### BR-1 — boundary and provenance

- **Layer:** Physical/causal bridge.
- **Statement / role:** Declare boundary, scale, design/training history, stores, tools, interlocutors, evaluators, and episode channels before attribution.
- **Scope:** Every `PhysOCA`/`PhysGCD` attribution.
- **Alternatives:** Post-hoc boundary; undocumented external channels; component-only or team-only default.
- **Independence-witness plan:** `W-STR`/`W-CAU`: nested-boundary models with identical global events but different imported organization/credit.
- **Conceptual necessity:** Prevents endogenous-origin boundary games.
- **Source warrant:** CR p. 227, BR-1, R/M reconstruction; no itemized external tag. Application T-BND/T-PROV pp. 260–261.
- **Discharge test:** `T-BND`, `T-PROV`; preregistration and complete crossing ledger.
- **Non-entailments:** A favorable boundary does not establish privileged scale or component authorship.
- **Direct / known dependents:** DF-22, DF-23, TH-14, TH-15, physical applications.
- **Inferential status / availability:** `IMP`; exact BR-1 bridge condition. Satisfaction has `inferential_status: null`, `proof_available: false` until demonstrated.

### BR-2 — information embodiment

- **Layer:** Physical/semantic bridge.
- **Statement / role:** Semantic roles map to physically discriminable attributes; required copying, transformation, and memory operations are possible at stated tolerance. CT information discharges discrimination, not meaning.
- **Scope:** Physical realization of any semantic predicate.
- **Alternatives:** Observer-readable states; correlation; digital encoding without operational access; semantic identity with CT information.
- **Independence-witness plan:** `W-PHY`: same semantic interpretation with one physically discriminable/operable encoding and one causally inaccessible encoding.
- **Conceptual necessity:** Provides physical carriers while preserving the semantic firewall.
- **Source warrant:** CR p. 227, BR-2; CT-1–CT-5 p. 227; no itemized tag for the bridge itself.
- **Discharge test:** `T-PHY`, `T-SEM`; operation/tolerance/fidelity demonstration.
- **Non-entailments:** Physical information/discrimination does not entail meaning, explanation, criticism, or authorship.
- **Direct / known dependents:** DF-22, DF-23, TH-14, TH-15; constructor application table p. 273.
- **Inferential status / availability:** `IMP`; exact BR-2 bridge condition. Satisfaction has `inferential_status: null`, `proof_available: false` until demonstrated.

### BR-3 — transition fidelity

- **Layer:** Physical/dynamical bridge.
- **Statement / role:** Every asserted abstract transition corresponds to a physically admitted task/history; cost, noise, repair, and side effects are counted.
- **Scope:** Physical event/state transitions.
- **Alternatives:** Ideal functional equivalence; trace matching; noise-free abstraction; uncosted simulation.
- **Independence-witness plan:** `W-PHY`: same abstract transition, only one physical model admits it at the tolerance/resources once side effects are included.
- **Conceptual necessity:** Stops idealized semantic histories from bypassing physics.
- **Source warrant:** CR p. 227, BR-3; CT-2–CT-4; no itemized tag for the bridge.
- **Discharge test:** `T-PHY`; task, theory, tolerance, noise, cost, repair, and side-effect ledger.
- **Non-entailments:** Abstract or simulated transition does not entail physical admissibility, reliability, or feasibility.
- **Direct / known dependents:** DF-22, DF-23, TH-14, TH-15.
- **Inferential status / availability:** `IMP`; exact BR-3 bridge condition. Satisfaction has `inferential_status: null`, `proof_available: false` until demonstrated.

### BR-4 — semantic anchoring

- **Layer:** Physical/semantic bridge.
- **Statement / role:** Token/content assignments require systematic production, use, reconstruction, and correction across contexts; CT information and observer resemblance do not fix meaning.
- **Scope:** Every physically realized representation/role.
- **Alternatives:** Resemblance, decoder success, covariance, designer intention, one-context use.
- **Independence-witness plan:** `W-SEM`/`W-PHY`: same physical token statistics, only one mapping remains systematic across recoding/context interventions.
- **Conceptual necessity:** Prevents analyst-imposed semantics.
- **Source warrant:** CR p. 227, BR-4; SC-2 p. 221; no itemized tag for the bridge.
- **Discharge test:** `T-SEM`, `T-PROB`, `T-CRI`, `T-TRN` under one `ρ`.
- **Non-entailments:** Copying, decoding, resemblance, or correlation does not entail semantic content.
- **Direct / known dependents:** DF-22, DF-23, TH-14, TH-15, A-TH2.
- **Inferential status / availability:** `IMP`; exact BR-4 bridge condition. Satisfaction has `inferential_status: null`, `proof_available: false` until demonstrated.

### BR-5 — reason-specific counterfactual preservation

- **Layer:** Physical/causal-semantic bridge.
- **Statement / role:** The same `ρ` preserves paraphrase/recoding and distinguishes alleged-defect changes; matched interventions redirect repairs as required by SC-3.
- **Scope:** Physical realization of UsesReason/Uptake/CCP/GCD.
- **Alternatives:** Generic token sensitivity, reward dependence, per-condition semantic remapping.
- **Independence-witness plan:** `W-CAU`/`W-PHY`: same revision frequency, only one physical mechanism tracks defect content under matched recodings.
- **Conceptual necessity:** Transfers reason-sensitive causation rather than mere response dependence.
- **Source warrant:** CR p. 227, BR-5; SC-3 pp. 221–222; bridge is R/M with no itemized tag.
- **Discharge test:** `T-SEM`, `T-CRI`, `T-UPT`, `T-ABL` under frozen `ρ`.
- **Non-entailments:** Negative-token response, correlation, or verbal rationale does not entail physical reason use.
- **Direct / known dependents:** DF-22, DF-23, TH-14, TH-15, A-TH2.
- **Inferential status / availability:** `IMP`; exact BR-5 bridge condition. Satisfaction has `inferential_status: null`, `proof_available: false` until demonstrated.

### BR-6 — physical authorship credit

- **Layer:** Physical/causal-authorship bridge.
- **Statement / role:** A causal audit across all provenance layers supports SC-4; runtime novelty is insufficient, prior influence is not automatically disqualifying, and reconstruction may be creative.
- **Scope:** Physical OCA/GCD and distributed/component attribution.
- **Alternatives:** Last-emitter, no-training, designer-only, runtime-only, or boundary-maximizing credit.
- **Independence-witness plan:** `W-CAU`: lookup/external-selector versus internal reconstruction with identical output.
- **Conceptual necessity:** Connects abstract authorship to real causal organization.
- **Source warrant:** CR p. 228, BR-6; SC-4 pp. 221–222; DP-3 p. 225 with `S-BOI7`, `S-BOI10`, `S-BOI16`, `S-CB12`.
- **Discharge test:** `T-PROV`, `T-GEN`, `T-BND`, `T-ABL` and rival credit models.
- **Non-entailments:** Runtime novelty or emission does not entail authorship; prior exposure does not settle it.
- **Direct / known dependents:** DF-22, DF-23, TH-14, TH-15, LLM/group/education applications.
- **Inferential status / availability:** `IMP`; exact BR-6 bridge condition. Satisfaction has `inferential_status: null`, `proof_available: false` until demonstrated.

### BR-7 — composition and role-conditional memory

- **Layer:** Physical/compositional bridge.
- **Statement / role:** Subsystem/task composition preserves every role relation asserted by the realized abstract predicate; if criticism, correction, endpoint lineage, or retention is asserted, the corresponding state or reconstructible disposition persists under declared perturbations. Bare OCA imports none of those stronger roles.
- **Scope:** Composite systems and PhysOCA/PhysGCD.
- **Alternatives:** Closure under composition by default; token-level memory only; aggregation without system-level roles.
- **Independence-witness plan:** `W-PHY`: components individually realize fragments, but only one composite preserves the cross-component role/lineage under perturbation.
- **Conceptual necessity:** Blocks illicit upward inheritance and level collapse.
- **Source warrant:** CR p. 228, BR-7; no itemized external tag.
- **Discharge test:** `T-RET`, `T-ABL`, `T-BND`, composition/provenance graph; role-by-role preservation.
- **Non-entailments:** Component realization does not entail composite agency; OCA does not import criticism, retention, CCP, or EKC.
- **Direct / known dependents:** DF-22, DF-23, TH-14, TH-15, I-GROUP, memory applications.
- **Inferential status / availability:** `IMP`; exact BR-7 bridge condition. Satisfaction has `inferential_status: null`, `proof_available: false` until demonstrated.

### BR-8 — dispositional robustness

- **Layer:** Physical/modal bridge.
- **Statement / role:** Disposition claims require stable causal organization over a nontrivial intervention/problem family, not one lucky path; resources and scaffolding are explicit.
- **Scope:** PhysGCD and any physical capacity/generality claim; not required by bare PhysOCA under DF-22.
- **Alternatives:** Repeated observed success; benchmark breadth; one possible path; unbounded resources; fragile fixed list.
- **Independence-witness plan:** `W-MOD`/`W-PHY`: trace-equivalent systems, only one survives perturbation/transfer with capacity preserved or reconstructed.
- **Conceptual necessity:** Transfers modal stability rather than episodic success.
- **Source warrant:** CR p. 228, BR-8; DF-23 p. 228; no itemized external tag.
- **Discharge test:** `T-RET`, `T-TRN`, `T-ABL`, `T-LONG`, resource/scaffolding audit.
- **Non-entailments:** Finite success, OCA, CCP, or EKC does not entail a physical disposition, GCD, or UED.
- **Direct / known dependents:** DF-23, TH-14, TH-15, I-AGI/I-RES.
- **Inferential status / availability:** `IMP`; exact BR-8 bridge condition. Satisfaction has `inferential_status: null`, `proof_available: false` until demonstrated.

## 9. Independent application-import ledger

Every I-* record below is stated by the report’s independent-import table (pp. 257–259). None is part of the minimal CR classifier, and none is inferentially available merely because this ledger names it.

### I-EXP — domain interpretation of explanatory roles

- **Layer:** Application semantic import.
- **Statement / role:** Supply a domain interpretation of `Purports` and primitive `Explains`, including the problem, background, explanatory adequacy, and rival relation.
- **Scope:** Any application asserting AttemptExp, explanation, OCA/CCP/EKC in an explanatory domain, HTV, or GoodNow.
- **Alternatives:** Prediction, compression, usefulness, causal-model, unification, mechanistic, mathematical, artistic, or practice-relative accounts.
- **Independence-witness plan:** `W-APP`: identical CR trace under two defensible domain explanation theories that disagree on `Purports` or `Explains`.
- **Conceptual necessity:** CR intentionally supplies no domain-general explanation decision procedure.
- **Source warrant:** Independent-import table, report p. 258. No source tag is assigned to this I-* row; source motivation for objective/nonreductive explanation is `S-BOI1` and `S-FOR1`, but those sources do not discharge a domain interpretation.
- **Discharge test:** Predeclare problem/background, candidate role, actual rivals, adequacy criteria, and proxy links; use `T-PROB`, `T-SEM`, `T-ALT`.
- **Non-entailments:** Output novelty, prediction, fit, utility, acceptance, survival, or analyst labeling does not supply explanatory role.
- **Direct / known dependents:** SC-5, DF-2/DF-4, DF-8/DF-9, I-HTV, scientific inquiry pp. 264–265, art pp. 265–266, theorem systems pp. 269–270.
- **Inferential status / availability:** `target_status: IMP`; `inferential_status: null`; `proof_available: false`; unavailable until a domain dossier discharges the requested import.

### I-HTV — hard-to-vary interpretation

- **Layer:** Application semantic/epistemic import.
- **Statement / role:** Declare substantive variants while holding explanandum and accepted background fixed, then assess whether adequacy survives without new explanatory work.
- **Scope:** DF-8, DF-9, DP-6, and any hard-to-vary claim.
- **Alternatives:** Syntactic rigidity, edit distance, parameter sensitivity, simplicity, robustness, compression, or a scalar hardness metric.
- **Independence-witness plan:** `W-APP`: the same explanation ranks differently under trivial versus problem-bearing variation families.
- **Conceptual necessity:** No canonical variation family or scalar metric is definitional.
- **Source warrant:** Report p. 258, I-HTV; `S-BOI1` motivates HTV at DF-8/DP-6, but the report gives no source tag that fixes an application’s family.
- **Discharge test:** Freeze `V`, problem, background, same-job relation, and adequacy criterion; publish successful and destructive variants.
- **Non-entailments:** Rigidity or HTV does not entail explanation, truth, finality, or uniqueness.
- **Direct / known dependents:** DF-8, DF-9, DP-6, TH-11, scientific/artistic applications.
- **Inferential status / availability:** `target_status: IMP`; `inferential_status: null`; `proof_available: false`; the requested application import is not yet adopted.

### I-REACH — explanatory reach relation

- **Layer:** Application semantic/modal import.
- **Statement / role:** Supply the relation between an explanation and further problems/contexts to which its unchanged explanatory commitments apply.
- **Scope:** `Reach`, XReach, WideReach, cross-domain claims.
- **Alternatives:** Transfer score, topical coverage, downstream derivability, induction, generalization after modifying the explanation.
- **Independence-witness plan:** `W-APP`: same new explanation and same later success, but only one later use preserves the original commitments.
- **Conceptual necessity:** Novelty and transformation do not themselves provide reach.
- **Source warrant:** Report p. 258, I-REACH; `S-BOI1` supports source-facing reach at DF-14, not an application relation.
- **Discharge test:** `T-TRN`; declare commitment identity, further context, background additions, and domain coverage.
- **Non-entailments:** Novelty, transformation, transfer performance, or repeated application does not entail explanatory reach; reach does not entail truth or induction.
- **Direct / known dependents:** DF-14, TH-11, GCD/UED/AGI application claims.
- **Inferential status / availability:** `target_status: IMP`; `inferential_status: null`; `proof_available: false`; the requested application import is not yet adopted.

### I-K_E — domain explanatory-knowledge and truth interpretation

- **Layer:** Application epistemic import.
- **Statement / role:** Supply a domain interpretation of primitive `K_E` and, where factivity is claimed, a separate interpretation of `True`.
- **Scope:** EKC, epistemic progress, success, and truth claims.
- **Alternatives:** Factive knowledge, verisimilitude, explanatory improvement, proof-relative correctness, empirical adequacy, practice-relative success.
- **Independence-witness plan:** `W-EPI`/`W-APP`: same CCP endpoint and retention, different independent success/truth interpretations.
- **Conceptual necessity:** CCP, retention, and GoodNow do not entail `K_E` or truth.
- **Source warrant:** Report p. 258, I-K_E; MS-8 p. 221 and RC-1 pp. 224–225. Source-facing fallibility uses `S-BOI1`, `S-FOR3`, `S-FOR10`, but no source tag supplies a universal application criterion.
- **Discharge test:** `T-SUC`; independent evaluator/theory, rival epistemic models, anti-circularity check against retention/self-report.
- **Non-entailments:** Retention, survival, preference, consensus, HTV, fit, CCP, or OCA does not entail `K_E`/`True`; `K_E` is not certainty.
- **Direct / known dependents:** DF-10, TH-2/TH-3/TH-8–TH-11, all EKC claims, science/education/AI/math applications.
- **Inferential status / availability:** `target_status: IMP`; `inferential_status: null`; `proof_available: false`; the requested application import is not yet adopted.

### I-K_CT — concrete physical-knowledge attribution

- **Layer:** Application physical/causal import.
- **Statement / role:** Apply `K_CT(i,e,ρ,τ)` to a particular item, environment, perturbation class, horizon, and causal persistence mechanism.
- **Scope:** Genes, adaptations, recipes, memories, doctrines, and other physical-knowledge claims.
- **Alternatives:** Survival, frequency, copying, heredity, causal efficacy, repair, or resilience without the full relation.
- **Independence-witness plan:** `W-PHY`: same observed persistence with and without problem-specific causal contribution under perturbation; vary environment/horizon.
- **Conceptual necessity:** The formal type does not establish any actual physical-knowledge instance.
- **Source warrant:** Report p. 258, I-K_CT; CT-7 p. 227; `S-CT13`, `S-CTI15`, `S-CTL15`, `S-SCC3`, `S-SCC5`, `S-SCC7`; open-program caveat remains.
- **Discharge test:** Named `i,e,ρ,τ`; causal ablation/perturbation; for adaptations, AB-1 and I-EVO.
- **Non-entailments:** Persistence, frequency, heritability, selection, truth, understanding, explanation, `K_E`, OCA, or CCP does not follow by label.
- **Direct / known dependents:** CT-7, AB-1, TH-8–TH-10, evolutionary/natural-selection/constructor applications.
- **Inferential status / availability:** `target_status: IMP`; `inferential_status: null`; `proof_available: false`; the requested application import is not yet adopted.

### I-MIND — thinking, representation, reason, and consciousness account

- **Layer:** Application philosophy/science of mind import.
- **Statement / role:** Supply an account of thinking, representation, reason use, and consciousness where applicable.
- **Scope:** Brains, persons, nonhuman animals, AGI, AI systems, and any mental attribution.
- **Alternatives:** Functionalism, representationalism, enactivism, biological naturalism, interpretivism, higher-order or no-consciousness accounts.
- **Independence-witness plan:** `W-APP`: same computation/constructor behavior under rival mind theories; vary consciousness while preserving CR process predicates.
- **Conceptual necessity:** Neither computation nor constructor theory defines thinking.
- **Source warrant:** Report p. 258, I-MIND; `S-FOR13` says computation permits artificial mentality in principle but does not explain mentality; DP-8’s person claims remain qualified.
- **Discharge test:** Domain theory plus `T-SEM`, `T-CRI`, `T-ABL`; separate representation/reason evidence from consciousness evidence.
- **Non-entailments:** Computation, constructorhood, OCA, CCP, EKC, GCD, or verbal self-report does not entail thinking, consciousness, or personhood.
- **Direct / known dependents:** Cognition/person applications pp. 262–264, AGI pp. 268–269, nonhuman-animal cases p. 275, I-ETH.
- **Inferential status / availability:** `target_status: IMP`; `inferential_status: null`; `proof_available: false`; the requested application import is not yet adopted.

### I-MIND-TACIT — nonverbal candidate-specific critical content

- **Layer:** Application semantic/cognitive import.
- **Statement / role:** Provide a theory under which nonverbal but discriminable states carry candidate-specific critical content and causally guide revision.
- **Scope:** Tacit criticism, inexplicit standards, affective tension, artistic and human cognition.
- **Alternatives:** Post-hoc analyst attribution; generic arousal/discomfort; embodied but noncontentful control signal; verbal-only criticism.
- **Independence-witness plan:** `W-SEM`/`W-CAU`: equally felt/discriminable states, only one systematically tracks distinct alleged defects and drives matching repairs.
- **Conceptual necessity:** Otherwise the analyst can label any felt tension as criticism.
- **Source warrant:** Report p. 258, I-MIND-TACIT; human/art mappings pp. 263 and 265–266; audit p. 279. `S-BOI14` supports inexplicit knowledge but does not by itself discharge a concrete mapping.
- **Discharge test:** Discriminability, converging measures, systematic defect interventions, recoding invariance, causal ablation; leave open if unavailable.
- **Non-entailments:** Discomfort, affect, salience, or subsequent revision does not entail candidate-specific criticism.
- **Direct / known dependents:** Human-person and art applications, PBCrit/Uptake where criticism is tacit.
- **Inferential status / availability:** `target_status: IMP`; `inferential_status: null`; `proof_available: false`; the requested application import is not yet adopted.

### I-INT — intelligence theory

- **Layer:** Application cognitive/competence import.
- **Statement / role:** Supply a theory of intelligence, competence, autonomy, domain generality, transfer, and resources.
- **Scope:** Any claim that a CR predicate establishes intelligence or autonomy.
- **Alternatives:** Psychometric, task-performance, adaptive, rational-agency, learning-efficiency, or general problem-solving accounts.
- **Independence-witness plan:** `W-APP`: same OCA/CCP/GCD facts under intelligence theories that classify competence/autonomy differently.
- **Conceptual necessity:** CR-1.0 does not identify creativity with intelligence.
- **Source warrant:** Report p. 258, I-INT; no source tag assigned. DP-8 is X/Q and does not provide a complete intelligence theory.
- **Discharge test:** Define competence, autonomy dimensions, transfer domains, and resource bounds independently of the CR classifier.
- **Non-entailments:** OCA, CCP, EKC, GCD, or UED does not by itself entail intelligence, autonomy, consciousness, or personhood.
- **Direct / known dependents:** I-AGI and any intelligence application claim.
- **Inferential status / availability:** `target_status: IMP`; `inferential_status: null`; `proof_available: false`; the requested application import is not yet adopted.

### I-AGI — quantified general-intelligence profile

- **Layer:** Application modal/intelligence import.
- **Statement / role:** Supply a quantified general-intelligence profile over problem classes, representations, enabling conditions, autonomy, transfer, and resource scaling; the application proposes GCD over declared expanding `Q*` only as its creative component and treats UED as stronger.
- **Scope:** AGI certification/profile claims.
- **Alternatives:** Benchmark breadth, conversation quality, psychometric generality, economic task coverage, universal computation, personhood-first definitions.
- **Independence-witness plan:** `W-MOD`/`W-APP`: finite trace-equivalent bounded and open-capacity systems; same GCD under different noncreative competence profiles.
- **Conceptual necessity:** “General” is otherwise unbound, and CR creativity is only one component.
- **Source warrant:** Report p. 258, I-AGI; proposed module pp. 268–269; DP-8 p. 225 with `S-BOI3`, `S-BOI6`, `S-BOI7`, `S-BOI16`. The report explicitly says the profile is not Deutsch’s formal definition or a finite certification test.
- **Discharge test:** Declare expanding `Q*`, encodings/environments, `χ`, autonomy and resource scaling; `T-LONG`, `T-TRN`, `T-RET`; retain finite underdetermination.
- **Non-entailments:** Universal computation, broad benchmarks, conversation, one or many OCA/CCP/EKC episodes, GCD, or UED does not by itself entail full AGI, consciousness, personhood, or moral status.
- **Direct / known dependents:** AGI application pp. 268–269, A-TH3 p. 277, I-INT/I-MIND/I-ETH/I-RES.
- **Inferential status / availability:** `target_status: IMP`; `inferential_status: null`; `proof_available: false`; the requested application import is not yet adopted.

### I-PHYS — physical theory, implementation doctrine, and realization facts

- **Layer:** Application physical import.
- **Statement / role:** Supply named physical theory `Θ`, an implementation doctrine, and system-specific realization facts.
- **Scope:** Any `Possible_Θ`, PhysOCA, PhysGCD, or physical attribution.
- **Alternatives:** Classical, quantum, constructor-theoretic, computational, functionalist, mechanistic, or multiple-realizability doctrines.
- **Independence-witness plan:** `W-PHY`: same abstract CR model under theories/maps that disagree on physical admissibility or preservation.
- **Conceptual necessity:** Abstract consistency is not physical possibility.
- **Source warrant:** Report p. 258, I-PHYS; SC-6 p. 221, IR-5 p. 226, BR layer pp. 227–228. No source tag fixes an application’s physical theory.
- **Discharge test:** Name `Θ`, `ρ`, target region, tolerance, dynamics, interventions, costs, and bridge evidence; `T-PHY`.
- **Non-entailments:** Abstract or computational realization does not entail physical possibility, actual instantiation, semantic preservation, or practical feasibility.
- **Direct / known dependents:** DF-22/DF-23, TH-14/TH-15, every physical application.
- **Inferential status / availability:** `target_status: IMP`; `inferential_status: null`; `proof_available: false`; the requested application import is not yet adopted.

### I-EVERETT — Everettian ontology and multiverse knowledge criterion

- **Layer:** Application physical/metaphysical import.
- **Statement / role:** Supply Everettian quantum ontology and any proposed multiverse-wide physical criterion of knowledge.
- **Scope:** Claims that specifically invoke the Everett strand or multiverse knowledge.
- **Alternatives:** Other quantum interpretations; interpretation-neutral quantum theory; no multiverse-wide knowledge predicate.
- **Independence-witness plan:** `W-PHY`/`W-APP`: preserve all minimal CR semantic/causal facts while varying quantum ontology.
- **Conceptual necessity:** *FOR* uses Everett as one of four strands, but it is contested physical interpretation and not part of the minimal semantic classifier.
- **Source warrant:** Report p. 258, I-EVERETT; the four-strand source entitlement is `S-FOR1` and `S-FOR13`. The I-* row has no separate source tag.
- **Discharge test:** Explicit quantum ontology, bridge to the claimed physical-knowledge criterion, and empirical/theoretical warrants; compare interpretation-neutral alternatives.
- **Non-entailments:** OCA, CCP, EKC, GCD, CT vocabulary, or quantum information does not entail Everettian ontology or quantum creativity.
- **Direct / known dependents:** Everett-specific downstream claims only; constructor application rejects a special quantum-creativity inference at pp. 274–275.
- **Inferential status / availability:** `target_status: IMP`; `inferential_status: null`; `proof_available: false`; the requested application import is not yet adopted.

### I-COMP — computability and universal-computation assumptions

- **Layer:** Application computational/physical import.
- **Statement / role:** Supply the computability class, universal-computation claim, encoding, simulation assumptions, programs, and resources.
- **Scope:** Computer contrast class, artificial realization, theorem systems, AGI, and fixed-software compatibility.
- **Alternatives:** Turing computability, probabilistic/quantum computation, hypercomputation, finite-state systems, analog models, resource-bounded simulation.
- **Independence-witness plan:** `W-PHY`: same universal hardware with constant/copy versus creative candidate program; same high-level history under different low-level update policies.
- **Conceptual necessity:** Universal execution does not provide creative organization or semantics.
- **Source warrant:** Report p. 258, I-COMP; `S-BOI6`, `S-FOR10`, `S-FOR13`; DP-9 p. 225.
- **Discharge test:** State computation class, encoding, interpreter/program, resource scaling, and physical simulation theorem; audit semantics/authorship separately.
- **Non-entailments:** Computation, universal computation, simulation, or fixed code does not entail thinking, OCA, GCD, AGI, or noncreativity.
- **Direct / known dependents:** DF-20, TH-13, TH-15, A-TH7, AGI and theorem-system applications.
- **Inferential status / availability:** `target_status: IMP`; `inferential_status: null`; `proof_available: false`; the requested application import is not yet adopted.

### I-CT — constructor-theory module adoption

- **Layer:** Application physical/constructor-theory import.
- **Statement / role:** Adopt the relevant CT vocabulary and principles: substrates, attributes, variables, tasks, constructors, possible/impossible tasks, information media, interoperability, and approximation conditions.
- **Scope:** Any actual constructor-theoretic attribution or CT-based bridge discharge.
- **Alternatives:** Dynamical physical theory without CT; partial CT module; different possibility/approximation semantics; no interoperability principle.
- **Independence-witness plan:** `W-PHY`: same physical behavior under an ordinary dynamical description and under a CT module; vary which bridge obligations CT actually discharges.
- **Conceptual necessity:** These are physical definitions/principles, not semantic clauses.
- **Source warrant:** Report p. 258, I-CT; CT-1–CT-7 p. 227; `S-CT13`, `S-CTI15`, `S-CTL15`, `S-SCC3`, `S-SCC5`, `S-SCC7`.
- **Discharge test:** Identify adopted CT clauses, named `Θ_CT`, approximation/tolerance, and predicate-by-predicate contribution to BR-2–BR-8; do not use constructor labels as semantic warrants.
- **Non-entailments:** CT information, constructorhood, or universal construction does not entail meaning, authorship, OCA, GCD, `K_E`, thinking, or AGI.
- **Direct / known dependents:** CT-1–CT-7 actual claims, TH-5/TH-6/TH-15 physical attribution, constructor application pp. 273–275, A-TH5.
- **Inferential status / availability:** `target_status: IMP`; `inferential_status: null`; `proof_available: false`; exact CT definitions become `DEF` only after the module is declared, and physical principles/instances need separate warrant.

### I-ART — artistic purposes, interpretations, and success standards

- **Layer:** Application aesthetic/semantic/epistemic import.
- **Statement / role:** Supply purposes of works, interpretations, aesthetic standards, and a position on objective aesthetic improvement.
- **Scope:** Any artistic OCA/CCP/EKC, GoodNow, HTV, reach, beauty, or progress claim.
- **Alternatives:** Objective, intersubjective, practice-relative, creator-intent, reception, institutional, popularity, novelty, or affective accounts.
- **Independence-witness plan:** `W-APP`: same artifact and creative history under aesthetic theories that disagree on purpose, standards, or improvement.
- **Conceptual necessity:** Artistic success is not truth, popularity, novelty, or value by definition.
- **Source warrant:** Report p. 259, I-ART; art scope RC-3 p. 224; `S-BOI14`. The row remains an independent import because the source conjecture does not settle a domain theory.
- **Discharge test:** Declare work purpose/interpretation, standards and their revision, independent outcome assessment, and alternatives; use `T-STD`, `T-CRI`, `T-UPT`.
- **Non-entailments:** Popularity, sales, novelty, intensity, creator preference, OCA, CCP, HTV, or GoodNow does not entail objective beauty or aesthetic improvement.
- **Direct / known dependents:** RC-3, art application pp. 265–266, I-AR-SHARED/I-MIND-TACIT.
- **Inferential status / availability:** `target_status: IMP`; `inferential_status: null`; `proof_available: false`.

### I-AR-SHARED — art/reason shared-process postulate

- **Layer:** Application source-specific semantic/process import.
- **Statement / role:** Import the source-specific claim that art and explanatory reason can share conjecture, criticism, standards, and retained correction, while possibly sharing a virtual-rendering implementation class; where an artwork functions as an inexplicit attempted explanation, the mapping may interpret `Purports`/`Explains` accordingly.
- **Scope:** Art mapped into the explanatory core.
- **Alternatives:** Analogy only; shared implementation but different process; shared process but different success predicates; art outside explanatory roles.
- **Independence-witness plan:** `W-SRC`/`W-APP`: two mappings of the same art episode, one satisfying problem-directed explanatory roles and one only product-level aesthetic variation.
- **Conceptual necessity:** Similar examples or implementation classes do not establish identity of processes or success predicates.
- **Source warrant:** Report p. 259, I-AR-SHARED, and pp. 265–266. Exact locators stated there: *BOI* ch. 14, print pp. 353–368 (`S-BOI14`); *Science* pp. 13–18 (no registry tag for that span); *FOR* print pp. 117–122 (no dedicated registry tag). The report calls this a proposed shared-process postulate.
- **Discharge test:** I-EXP/I-ART plus represented problem, work-as-attempt, candidate-specific criticism, standard change, lineage, and retention; test common-process alternatives.
- **Non-entailments:** Shared process or virtual-rendering class does not entail identical artistic/scientific success, truth, beauty, or universal applicability to all art.
- **Direct / known dependents:** RC-3 and art application pp. 265–266.
- **Inferential status / availability:** `target_status: IMP`; `inferential_status: null`; `proof_available: false`.

### I-COMM — communication as conjectural reconstruction

- **Layer:** Application semantic/causal import.
- **Statement / role:** Treat communication as conjectural reconstruction of meaning rather than literal semantic transfer.
- **Scope:** Education, learning, cultural transmission, communicated explanations, and creative reconstruction.
- **Alternatives:** Shannon-style signal transfer as meaning transfer; copying; imitation; codebook decoding; inferential reconstruction.
- **Independence-witness plan:** `W-SEM`/`W-CAU`: identical copied words with different reconstructed meanings; different wordings with equivalent reconstructed content.
- **Conceptual necessity:** Physical copying does not fix semantic interpretation.
- **Source warrant:** Report p. 259, I-COMM; education mapping p. 266; `S-BOI10` (print pp. 223–257 / PDF pp. 234–268), `S-BOI16` (print pp. 398–417 / PDF pp. 409–428).
- **Discharge test:** Shared-problem/evidence account, semantic transfer tests, paraphrase/novel-example transfer, provenance and reconstruction audit.
- **Non-entailments:** Copying words or conforming behavior does not entail understanding; wording variation does not entail communication failure.
- **Direct / known dependents:** TH-17 application use; education pp. 266–267, cultural evolution p. 275, person/AI reconstruction claims.
- **Inferential status / availability:** `target_status: IMP`; `inferential_status: null`; `proof_available: false`.

### I-DEV — developmental facts

- **Layer:** Application empirical/developmental import.
- **Statement / role:** Supply age- and context-specific facts about children, learning, memory, language, and social scaffolding.
- **Scope:** Children, education, learning, and developmental capacity claims.
- **Alternatives:** Nativist, constructivist, sociocultural, behaviorist, information-processing, or domain-specific accounts.
- **Independence-witness plan:** `W-APP`: same CR definitions under developmental theories that predict different representations, memory, or scaffolding at a given age/context.
- **Conceptual necessity:** No developmental psychology follows from CR-1.0.
- **Source warrant:** Report p. 259, I-DEV; education application pp. 266–267. No primary source tag is assigned to the row.
- **Discharge test:** Age/context/sample declarations, validated measures, causal/scaffolding interventions, longitudinal or delayed-reconstruction evidence, I-MEAS.
- **Non-entailments:** CR classification, species membership, instruction, or test scores do not establish developmental mechanisms/capacities.
- **Direct / known dependents:** Education/children applications; I-MIND/I-COMM/I-MEAS.
- **Inferential status / availability:** `target_status: IMP`; `inferential_status: null`; `proof_available: false`.

### I-EVO — biological/evolutionary process facts

- **Layer:** Application evolutionary/causal import.
- **Statement / role:** Supply replicators, heritable variation, differential reproduction, selection environments, and levels of selection.
- **Scope:** Natural selection, evolutionary algorithms by analogy, cultural evolution, adaptation, and AB-1 applications.
- **Alternatives:** Replicator, developmental-systems, multilevel-selection, population-genetic, ecological, or algorithmic models.
- **Independence-witness plan:** `W-APP`/`W-PHY`: same population trace under rival heredity, environment, and causal-contribution models.
- **Conceptual necessity:** DF-21 is only a process class; it does not establish actual biological realization.
- **Source warrant:** Report p. 259, I-EVO; DP-10/AB-1 p. 225; `S-BOI4`, `S-BOI15`, `S-BOI16`, `S-FOR3`, `S-FOR8`, `S-CTL15`.
- **Discharge test:** Identify replicators/vehicles, inherited variants, environment, reproduction differential, level, horizon, causal perturbations, and designer/guidance paths.
- **Non-entailments:** Variation, novelty, fitness, survival, adaptation, or selection does not entail represented problems, criticism, OCA, CCP, `K_E`, foresight, or group agency.
- **Direct / known dependents:** AB-1 actual use, evolutionary algorithms pp. 270–271, natural selection pp. 271–272, A-TH6.
- **Inferential status / availability:** `target_status: IMP`; `inferential_status: null`; `proof_available: false`.

### I-GROUP — system-level composition rule

- **Layer:** Application compositional/causal import.
- **Statement / role:** Supply a rule for system-level representation, action, memory, and causal attribution across members.
- **Scope:** Scientific communities, organizations, institutions, dyads, teams, markets, and human-machine systems.
- **Alternatives:** Simple aggregation; distributed cognition; joint agency; organizational functionalism; no group agent; role-network composition.
- **Independence-witness plan:** `W-STR`/`W-CAU`: same member events, one composition yields persistent system-level roles/lineage and another is analyst aggregation only.
- **Conceptual necessity:** Aggregation does not automatically create a new agent.
- **Source warrant:** Report p. 259, I-GROUP; scientific community pp. 264–265; organization conditions pp. 272–273. No primary source tag is assigned to the row.
- **Discharge test:** Fixed system boundary/interface; organization-level tokens; causal criticism paths; turnover-resistant/reconstructible memory; credit rule; counterfactual transitions; BR-7.
- **Non-entailments:** Many members, communication, markets, consensus, or component creativity does not entail group OCA/CCP/GCD, consciousness, or personhood.
- **Direct / known dependents:** Community/organization/team applications, A-TH4, BR-7, I-ETH where group moral status is alleged.
- **Inferential status / availability:** `target_status: IMP`; `inferential_status: null`; `proof_available: false`.

### I-AI-SYS — exact artificial-system mechanism dossier

- **Layer:** Application empirical/causal-system import.
- **Statement / role:** Supply model architecture, version/date, training history, data provenance, inference procedure, tools, memory, prompts, controllers/evaluators, and human interventions for the exact system and boundary.
- **Scope:** LLMs, agents, training processes, evolutionary systems, and human-AI teams.
- **Alternatives:** Base forward pass, chat session, agent loop, training process, or composite team as target; proprietary/unknown mechanisms.
- **Independence-witness plan:** `W-CAU`/`W-STR`: identical transcript produced by lookup, fixed policy, hidden human loop, evaluator-driven scaffold, or internally reconstructive system.
- **Conceptual necessity:** “LLM” or “AI” is not a mechanistic description.
- **Source warrant:** Report p. 259, I-AI-SYS; boundary matrix and requirements pp. 267–268. Source-facing implementation/provenance concerns `S-BOI7`, `S-BOI16`, `S-CB12`, but do not supply system facts.
- **Discharge test:** `T-BND`, `T-PROV`, `T-GEN`, `T-ABL`, `T-RET`; exact version/date and all external crossings; rival-model tournament.
- **Non-entailments:** Text quality, novelty ratings, conversation length, benchmarks, self-reports, architecture class, or marketing label does not entail OCA/CCP/EKC/GCD/AGI/consciousness or locate causal credit.
- **Direct / known dependents:** LLM application pp. 267–268, evolutionary algorithms pp. 270–271, human-machine teams p. 275.
- **Inferential status / availability:** `target_status: IMP`; `inferential_status: null`; `proof_available: false`.

### I-MATH — formal and explanatory mathematics module

- **Layer:** Application logical/mathematical/epistemic import.
- **Statement / role:** Supply formal syntax, axioms, proof relation, soundness assumptions, and mathematical explanatory standards.
- **Scope:** Theorem provers, conjecture systems, mathematical EKC, proof and explanation claims.
- **Alternatives:** Different calculi/axioms; model-theoretic truth; proof-theoretic validity; explanatory proof, unification, elegance, importance, or formal correctness only.
- **Independence-witness plan:** `W-APP`: same proof string under different axioms/calculi; same valid theorem from brute enumeration versus explanatory organization.
- **Conceptual necessity:** Formal validity is domain-relative and not automatically explanatory.
- **Source warrant:** Report p. 259, I-MATH; theorem-system application pp. 269–270; `S-FOR10` supports open-ended mathematical creativity but does not fix a formal/explanatory standard.
- **Discharge test:** Declare syntax/axioms/rules/metatheory, checker evidence, soundness scope, problem/explanation mapping, and compute-matched enumeration/retrieval baselines.
- **Non-entailments:** Formal validity does not entail empirical truth, explanation, importance, elegance, historical novelty, authorship, or creative process; incompleteness does not by itself prove noncomputability.
- **Direct / known dependents:** Theorem-prover/math applications, I-K_E/I-EXP/I-COMP.
- **Inferential status / availability:** `target_status: IMP`; `inferential_status: null`; `proof_available: false`.

### I-MEAS — measurement and statistical model

- **Layer:** Application empirical/measurement import.
- **Statement / role:** Supply measurement validity, intervention assumptions, statistical model, uncertainty, and error bars.
- **Scope:** Every empirical attribution and discriminating test.
- **Alternatives:** Different operationalizations, proxy models, causal assumptions, sampling/error models, qualitative evidence.
- **Independence-witness plan:** `W-APP`: same raw observations under valid versus invalid proxy/measurement interpretations, or rival causal/statistical models.
- **Conceptual necessity:** Empirical evidence does not interpret itself.
- **Source warrant:** Report p. 259, I-MEAS; test battery pp. 260–262 and application cautions throughout. No primary source tag is assigned.
- **Discharge test:** Construct validity, calibration, intervention identifiability, preregistered analysis, uncertainty/error reporting, sensitivity and rival-model analysis.
- **Non-entailments:** Significance, decoding, benchmark score, correlation, or successful intervention does not by itself establish the semantic/causal target.
- **Direct / known dependents:** All E-status application attributions, T-* tests, cognition/AI/education/evolution studies, A-TH2.
- **Inferential status / availability:** `target_status: IMP`; `inferential_status: null`; `proof_available: false`.

### I-ETH — moral-status and decision-under-uncertainty module

- **Layer:** Application ethical/political import.
- **Statement / role:** Supply accounts of consciousness, personhood, interests, moral patients, and decision rules under uncertainty.
- **Scope:** Moral status, rights, precaution, treatment of humans/animals/AI/groups.
- **Alternatives:** Sentience, personhood, agency, relational, rights, precautionary, expected-moral-value, or no-status accounts.
- **Independence-witness plan:** `W-APP`: same OCA/CCP/GCD facts under ethical theories that assign different status/precaution.
- **Conceptual necessity:** No moral status follows from a process classifier.
- **Source warrant:** Report p. 259, I-ETH; AGI caution p. 269 and application non-entailments. No primary source tag is assigned; DP-8 remains X/Q and cannot discharge ethics.
- **Discharge test:** Independent consciousness/personhood/interests evidence, moral theory, uncertainty and action threshold; do not use creativity as proxy.
- **Non-entailments:** OCA, CCP, EKC, GCD, UED, intelligence, universal computation, or constructorhood does not entail consciousness, personhood, rights, or moral worth.
- **Direct / known dependents:** AGI/person/animal/group moral decisions and A-TH4.
- **Inferential status / availability:** `target_status: IMP`; `inferential_status: null`; `proof_available: false`.

### I-RES — resource budgets

- **Layer:** Application resource/physical-modal import.
- **Statement / role:** Supply time, energy, sample, memory, compute, communication, material, and repair budgets.
- **Scope:** Possibility, reliability, efficiency, capacity, simulation, GCD/UED/AGI, and bridge claims.
- **Alternatives:** Unlimited resources; asymptotic complexity only; fixed empirical budget; amortized or distributed costs.
- **Independence-witness plan:** `W-MOD`/`W-PHY`: same abstract organization succeeds under one resource/scaffolding profile and fails under another.
- **Conceptual necessity:** Possibility, reliability, and efficiency require declared resources.
- **Source warrant:** Report p. 259, I-RES; MS-9 p. 221, BR-3/BR-8 pp. 227–228. No source tag is assigned to an application budget.
- **Discharge test:** Complete resource vector, scaling law, tolerance, failures, repair and externalized costs; `T-PHY`, `T-LONG`.
- **Non-entailments:** Logical/CT possibility, finite success, or universal computation does not entail feasible, efficient, robust, or resource-bounded capacity.
- **Direct / known dependents:** MS-9, CT-4, BR-3, BR-8, GCD/UED/I-AGI/I-COMP/I-PHYS applications.
- **Inferential status / availability:** `target_status: IMP`; `inferential_status: null`; `proof_available: false`.

### AUD-APP-DOSSIER — application tuple completeness (owner: application §2.1)

- **Layer:** Application audit schema.
- **Statement / role:** An auditable application declares `A = <U,B,L,β,Q,K,ρ,Θ,CF,R,H,E_A>`: target region, boundary/scale, equivalence level, novelty baseline, problem class, standards, realization map, physical theory, intervention family, resources, observed histories, and empirical facts. If a used component is unspecified, the classification is incomplete.
- **Scope:** Every world-facing classification.
- **Alternatives:** Partial dossier; post-hoc fields; purely behavioral report; theorem-only attribution.
- **Independence-witness plan:** `W-APP`: remove one used component and construct rival completions yielding opposed classifications.
- **Conceptual necessity:** Operationalizes the layer firewall and exposes every application import.
- **Source warrant:** Report p. 259, application §2.1; completion checklist pp. 280–281. No CR clause ID or source tag is assigned; this is an application-audit record only.
- **Discharge test:** Field-by-field completeness, preregistration where feasible, transitive dependency closure, IR-8 audit, typed rival model.
- **Non-entailments:** A complete dossier does not guarantee a positive classification; an unknown field licenses only a bounded conditional or underdetermination result.
- **Direct / known dependents:** Legal transformation pattern pp. 280–281 and every I-* import/application section.
- **Inferential status / availability:** `inferential_status: null`; `proof_available: false`; `owner_status: IMP` for the report’s application-audit requirement. This audit key cannot enter proof closure.

## 10. Coverage and quarantine check

- Active exact-clause coverage: TY-1–TY-3; IR-1–IR-8; MS-1–MS-9; SC-1–SC-8; RC-1–RC-3; DP-1–DP-11; AB-1; CT-1–CT-7; BR-1–BR-8.
- Primitive-level audit coverage: every symbol in the active model tuple on report pp. 220–221 is either in its exact MS record or in an `AUD-*` subrecord tied to that owner. `UsesReason`, `Authors_s`, `Possible_Θ`, and `Retained_s` are covered under SC-3, SC-4, SC-6, and SC-7.
- Modal/physical audit coverage: admissible histories, operation repertoire, memory, stable organization, `Q,χ`, the DF-13 no-domain-bar clause, cost/resources, named theory, one realization map, component-task network, `K_CT`, and all eight physical bridges.
- Application coverage: all 24 exact I-* rows on report pp. 258–259 are present. Each has `target_status: IMP`, `inferential_status: null`, and `proof_available: false` until its application dossier is discharged.
- CT-5 is the sole exact-clause atomic-status ambiguity recorded here: its vocabulary and interoperability principle are bundled under one authoritative identifier, so the whole clause is quarantined rather than assigned two statuses.
- Every `AUD-*` key is implementation-local, has `inferential_status: null` and `proof_available: false`, and may not appear in proof closure; its `owner_status` is informational only.
- No new `DER` item is claimed, no independence witness is presented as completed, and no substantive source warrant is inferred from thematic similarity.
- Report pp. 234–255 remain superseded-audit material only and contribute no active premise, identifier, or warrant.
