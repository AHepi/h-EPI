# CR-1.0 bootstrap source manifest, source-status registry, and coverage matrix

## 0. Authority, scope, and locator convention

This file is a cold-start bootstrap audit. It does not prove any theorem, adjudicate any countermodel, or repair CR-1.0.

The sole semantic and formal authority used here is the supplied PDF, **Creativity as Explanatory Self-Correction**. The executable-calculus handoff is treated only as procedure. A handoff paraphrase, addition, or conflict is recorded below as an ambiguity and is not imported into CR-1.0.

Locator notation is deliberately two-dimensional:

- `PDF p.N` means the 1-indexed physical page in the supplied 286-page PDF.
- `report p.M` means the printed footer number in the report.
- From physical PDF p.2 through p.286, `PDF page = report page + 1`. PDF p.1 is the unnumbered cover.
- Locators such as `BOI print 148–163 / source-PDF 159–174` are locators into an externally supplied book and are not pages of this report.

### Authority snapshot

| Field | Recorded value | Exact report/source locus |
|---|---|---|
| Authority file | `Creativity_Semantic_Model_CR-1.0(1).pdf` | Supplied artifact |
| Report title | *Creativity as Explanatory Self-Correction* | PDF p.1 |
| Report author metadata | `Research synthesis prepared for Aza` | PDF metadata |
| PDF SHA-256 | `08ff81e848fea976b558345402d85723173be8f40f1041fb00d6267f1e026b8b` | Computed over supplied PDF |
| PDF structure | 286 pages; US Letter 612×792 pt; PDF 1.5; unencrypted | PDF metadata |
| Producer | `xdvipdfmx (20220710)`; creator `LaTeX via pandoc` | PDF metadata |
| Creation metadata | `Sat Aug 29 13:45:57 2026 AEST` | PDF metadata |
| Extracted text | 17,451 lines; 1,148,984 bytes; 286 form-feed delimiters | Bootstrap workfile `CR-1.0.txt` (not packaged) |
| Extracted-text SHA-256 | `e5abe5e6f3a71ba9f391830e4b5fe1898b83f96ca0f2148f3355938a5224bb38` | Computed over extracted text |
| Corpus cut-off | 29 August 2026 | Recent addendum, PDF p.164 / report p.163; bibliography, PDF p.284 / report p.283 |
| Procedural handoff | `CR-1.0_Executable_Calculus_Handoff_Plan(2).md`; SHA-256 `afc2fbc6d18f6340b67a266f657a58112de9fa00d5c7d3ee557195332a8e404e` | Procedural only; handoff lines 11–15, 423–474 |

## 1. Report-level coverage matrix

Every physical page of the authority PDF is covered by exactly one top-level row below. Shared boundary pages occur where one section ends and the next begins on the same printed page.

| Report section ID / unit | Physical PDF pages | Printed report pages | Source basis | Local source/status discipline | Coverage finding |
|---|---:|---:|---|---|---|
| Cover | 1 | unnumbered | Report identity | None | Title only. |
| Contents | 2–10 | 1–9 | Report structure | None | Gives the report's section-level page map. |
| Executive result | 11–12 | 10–11 | Whole corpus | None locally | Instantiation summaries are not given `S-*` tags. |
| Reading map and claim-status discipline | 13–14 | 12–13 | Whole report | `D/X/Q/R/P/CT/E/T/N` at PDF p.13 / report p.12 | Global claim scheme; not identical to Model §0's source-mark scheme. |
| Part I, §§1–11, “Deutsch's explanatory framework” | 15–27 | 14–26 | BOI, FOR, SCC, constructor-theory papers, authored/public sources | Global claim marks, especially `X/R/Q/CT`; summary table at PDF pp.15–16 | Source prose and footnotes occur, but there are no `S-*` identifiers. The map's rows themselves have status but no row-level source tag. |
| Part II, §§12–14, orientation | 28–29 | 27–28 | All indexed corpora | Descriptive | States index scope and negative findings. |
| BOI clean-room concept and argument index | 30–83 | 29–82 | Supplied 498-page BOI PDF only | `[E/Q/R/H]`, including `[E/Q]`, `[Q/R]`, `[Q/H]`, `[H/E]`; registry at PDF p.30 / report p.29 | Full introduction, Chapters 1–18, syntheses, A–Z concordance, ambiguity register, chapter map, and focused locators. |
| FOR clean-room analytical index | 84–117 | 83–116 | Supplied 403-page FOR PDF only | `Explicit/Reconstruction/Gap/Dated-contested`; registry at PDF p.84 / report p.83 | Full preface, Chapters 1–14, consolidated index, legal moves, warnings, and locator table. |
| Marletto and constructor-theory dossier, §§1–14 | 118–142 | 117–141 | SCC EPUB plus constructor-theory primary literature | `D/P/R/E/C/A`; registry at PDF p.119 / report p.118 | SCC chapter map, exact CT vocabulary, primary-paper index, dependency ledger, contribution/limit analysis, and source bibliography. |
| Deutsch public-corpus dossier | 143–163 | 142–162 | Authored texts, technical papers, interviews/talks, reports, and secondary criticism | Authority weights `A/B/C/S` plus access status; registry at PDF p.143 / report p.142 | Dated-correction analysis, primary inventory, concept extraction, tension register, and source-handling rules. No stable claim IDs shared with Model CR-1.0. |
| Recent primary-source addendum, items 1–5 | 164–167 | 163–166 | Strange Loop; Altman–Deutsch; CT Time; Tests of CT; Do It podcast | `Direct update/Physical-layer update/No update`; registry at PDF p.164 / report p.163 | Directly names CR clauses affected, but none of the five sources receives an `S-*` tag. |
| Unified A–Z concordance | 168–214 | 167–213 | BOI, FOR, SCC, CT, CTI, CTL | `E/R/Q/C`; registry at PDF p.168 / report p.167 | Cross-source terminology and ambiguity register. Letter meanings differ from other sections. |
| Part III, §§15–19, semantic-model orientation | 215–218 | 214–217 | Whole synthesis | None locally | Source-facing orientation is untagged. |
| Model CR-1.0, §§0–10 | 219–234 | 218–233 | Frozen 23-tag source registry plus model clauses | `X/R/M/Q/O`; registry at PDF p.219 / report p.218 | The only report unit using `S-*` identifiers. Every `S-*` token in the entire PDF is in PDF pp.219–233. |
| Adversarial source audit and revision-record title | 235 | 234 | Transition page | None | Separates final model from the retained precursor audit. |
| Source-grounding audit of the superseded precursor | 236–256 | 235–255 | Supplied sources plus a legacy candidate calculus | `D/R/M/U`; registry at PDF p.236 / report p.235; legacy anchors `BOI-*`, `FOR-*`, `SCC-*` | Explicitly an error/revision record. Its identifiers and marks must be namespaced away from final Model CR-1.0. |
| Downstream applications and adversarial audit, §§1–22 | 257–283 | 256–282 | Final CR clauses, application imports, prose source citations, empirical placeholders | `K/C/E/N`; registry at PDF p.257 / report p.256 | No `S-*` occurrence anywhere in this unit, despite source-specific applications. |
| Bibliography and source registry | 284–286 | 283–285 | Broad primary and comparative corpus | Category only | Bibliographic identities, not a claim-to-source or clause-to-source mapping. |

### 1.1 Exact Model CR-1.0 section coverage

| Model report section ID | Physical PDF pages | Printed report pages | Identifier families / source coverage |
|---|---:|---:|---|
| Model §0, Status and source discipline; Source registry | 219–221 | 218–220 | Defines `X/R/M/Q/O`; defines all 23 `S-*` tags. |
| Model §1.1, Types | 221 | 220 | `TY-1`–`TY-3`; no source marks or `S-*` tags. |
| Model §1.2, Abstract model | 221–222 | 220–221 | `MS-1`–`MS-9`; no source marks or `S-*` tags. |
| Model §1.3, Satisfaction clauses | 222–223 | 221–222 | `SC-1`–`SC-8`; only `SC-3` has a source mark (`M`), with no source tag. |
| Model §2, Eliminable semantic definitions | 223–225 | 222–224 | `DF-1`–`DF-21`, including `DF-4a` and `DF-7a`; source marks occur only on the clauses itemized in §5 below. |
| Model §2.1, Contrast classes | 224–225 | 223–224 | `DF-15`–`DF-21`; no source marks or tags. |
| Model §3, Two knowledge types | 225 | 224 | `RC-1`–`RC-3`; a section-level source line, but no `X/R/M/Q/O` mark on any `RC-*`. |
| Model §4, Explicit Deutschian postulates | 226 | 225 | `DP-1`–`DP-11` and `AB-1`; every one has a compound or atomic source mark and source tags. |
| Model §5, Legal object moves | 227 | 226 | `OM-1`–`OM-10`; no source marks or tags. |
| Model §6, Metalevel inference rules | 227–228 | 226–227 | `IR-1`–`IR-8`; no source marks or tags. |
| Model §7.1, Exact physical vocabulary | 228 | 227 | `CT-1`–`CT-7`; `CT-7` has source tags but no `X/R/M/Q/O` mark. |
| Model §7.2, Bridge conditions | 228–229 | 227–228 | `BR-1`–`BR-8`, `DF-22`, `DF-23`; no clause-level source marks/tags. One following unnumbered paragraph is marked `R/M`. |
| Model §8, Key theorems and non-entailments | 229–233 | 228–232 | `TH-1`–`TH-17`; all have dependency lines, but only eight have explicit `R` or `M` source-entitlement marks. |
| Model §9, Explicit non-derivability boundary | 233–234 | 232–233 | Untagged boundary statements. |
| Model §10, Reconstruction choices and falsification points | 234 | 233 | Untagged reconstruction/audit prose. |

### 1.2 Downstream application section coverage

| Application report section ID | Physical PDF pages | Printed report pages | Coverage |
|---|---:|---:|---|
| Status and scope; §1 Four-level interface | 257–258 | 256–257 | Defines `K/C/E/N`; maps OCA, CCP, EKC, GCD, OCap, UED, physical bridges, and knowledge types. |
| §2 Independent-import ledger; §2.1 dossier schema | 258–260 | 257–259 | `I-EXP` through `I-RES`; application tuple. |
| §3 Cross-domain test battery | 261–263 | 260–262 | `T-BND` through `T-LONG`; no source tags. |
| §§4–6 Cognition, humans, scientific inquiry | 263–266 | 262–265 | Conditional mappings, countermodels, tests. |
| §§7–8 Art; education/communication | 266–268 | 265–267 | Source-specific imports `I-AR-SHARED`, `I-COMM`; prose source locators only. |
| §§9–10 Current LLM systems; AGI | 268–270 | 267–269 | System-boundary taxonomy, dated correction, conditional AGI module. |
| §§11–13 Theorem provers; evolutionary algorithms; natural selection | 270–273 | 269–272 | Mathematical and evolutionary mappings/countermodels. |
| §§14–15 Organizations; constructor theory/realization | 273–276 | 272–275 | Group composition and CT bridge analysis. |
| §§16–17 Stress cases; cross-application comparison | 276–277 | 275–276 | Search, memes, animals, human-machine teams, alien/oracle cases, comparison matrix. |
| §18 Derived application results `A-TH1`–`A-TH8` | 277–279 | 276–278 | Dependency certificates, but no `S-*` source tags. |
| §19.1–§19.18 Adversarial application audit | 279–281 | 278–280 | Interpretation, level, novelty, boundary, uptake, success, open-endedness, bridge, and constructor failure modes. |
| §§20–22 Legal transformations, checklist, outcome | 281–283 | 280–282 | Legal/illegal application moves, completeness checklist, consolidated outcome. |

## 2. Source corpus manifest

### 2.1 Primary supplied books and report-internal indexes

| Source | Report index locus | Source-edition locator convention | Formal `S-*` coverage |
|---|---|---|---|
| David Deutsch, *The Beginning of Infinity* (2011) | PDF pp.30–83 / report pp.29–82; bibliography PDF p.284 / report p.283 | Supplied 498-page PDF; main-text source-PDF page = print page + 11; introduction print vii–viii / source-PDF 10–11. Convention defined at PDF p.30 / report p.29. | Nine tags: `S-BOI1`, `3`, `4`, `6`, `7`, `10`, `14`, `15`, `16`. |
| David Deutsch, *The Fabric of Reality* (1997) | PDF pp.84–117 / report pp.83–116; bibliography PDF p.284 / report p.283 | Supplied 403-page PDF; main-text source-PDF page = print page + 12. Convention defined at PDF p.84 / report p.83. | Six tags: `S-FOR1`, `3`, `8`, `10`, `12`, `13`. |
| Chiara Marletto, *The Science of Can and Can't* (2021) | PDF pp.118–142 / report pp.117–141; bibliography PDF p.284 / report p.283 | Supplied EPUB. Dossier says it contains print-page anchors (PDF p.118 / report p.117); concordance later says it has no stable print pagination and locates SCC by chapter (PDF p.168 / report p.167). | Three tags: `S-SCC3`, `S-SCC5`, `S-SCC7`. |

### 2.2 Constructor-theory primary research and official portals

| Source | Exact report locus | Formal tag |
|---|---|---|
| David Deutsch, “Constructor Theory,” *Synthese* 190 (2013), 4331–4359 | Dossier §6.1, PDF p.130 / report p.129; bibliography PDF p.284 / report p.283 | `S-CT13` |
| Deutsch & Marletto, “Constructor Theory of Information,” *Proc. R. Soc. A* 471 (2015), 20140540 | Dossier §6.2, PDF p.131 / report p.130; bibliography PDF p.284 / report p.283 | `S-CTI15` |
| Marletto, “Constructor Theory of Life,” *J. R. Soc. Interface* 12 (2015), 20141226 | Dossier §6.3, PDF p.132 / report p.131; bibliography PDF p.284 / report p.283 | `S-CTL15` |
| Marletto, “Constructor Theory of Probability” (2016) | Dossier §6.4, PDF p.132 / report p.131; bibliography PDF p.284 / report p.283 | None |
| Marletto, “Constructor Theory of Thermodynamics” (2016; revised 2017) | Dossier §6.5, PDF p.133 / report p.132; bibliography PDF p.284 / report p.283 | None |
| Marletto & Vedral, gravity-mediated entanglement/information-witness work (2017 onward) | Dossier §6.6, PDF p.133 / report p.132 | None |
| Marletto, “The Information-Theoretic Foundation of Thermodynamic Work Extraction” (2022) | Bibliography PDF p.284 / report p.283 | None |
| Marletto & Deutsch, “Constructor Theory of Time” (2025) | Dossier §6.7, PDF p.134 / report p.133; recent addendum §3, PDF p.165 / report p.164; bibliography PDF p.284 / report p.283 | None |
| Marletto, Deutsch & Vedral, “Tests of Constructor Theory” (2026) | Dossier §6.8, PDF p.134 / report p.133; recent addendum §4, PDF p.166 / report p.165; bibliography PDF p.284 / report p.283 | None |
| Constructor Theory, “Research” and “Frequently Asked Questions” | Bibliography PDF p.284 / report p.283; programme discussed throughout dossier | None |

The bibliography explicitly says that “constructor theory of knowledge” denotes an incomplete research programme distributed across these works, not a completed parallel foundational paper (PDF p.284 / report p.283).

### 2.3 Deutsch authored/public corpus

| Source or inventory group | Exact report locus | Formal tag / status |
|---|---|---|
| Official FOR synopsis (1997-era) | Public inventory PDF p.145 / report p.144 | No tag; weight `A` |
| Edge, “The Beginning of Infinity” conversation/exposition (2004/2005) | PDF p.145 / report p.144 | No tag; `A/B` |
| “The truth is not out there” (2006) | PDF p.145 / report p.144 | No tag; `A` |
| “A new way to explain explanation” authored/talk text (2008–09) | PDF p.146 / report p.145 | No tag; `A` |
| Official BOI page (2011) | PDF p.146 / report p.145 | No tag; `A` |
| “Creative Blocks” (Aeon and official mirror, 2012) | PDF p.147 / report p.146; bibliography PDF p.284 / report p.283 | `S-CB12`; `A` |
| “Constructor Theory” authored paper (2013) | PDF p.148 / report p.147 | `S-CT13`; `A` |
| Deutsch–Marletto CTI paper (2014/2015) | PDF p.148 / report p.147 | `S-CTI15`; `A (joint)` |
| Official constructor-theory/knowledge portal (2015) | PDF p.149 / report p.148 | No separate tag; `A / portal` |
| “My first conversation with ChatGPT” (2022) | PDF p.149 / report p.148; bibliography PDF p.284 / report p.283 | No tag; `A` |
| “My opinion about theories of consciousness, creativity or artificial general intelligence” | PDF p.150 / report p.149 | No tag; `A`; report says displayed date must be verified |
| Sam Altman–David Deutsch discussion (2025) | PDF p.150 / report p.149; addendum §§2, PDF pp.164–165 / report pp.163–164; bibliography PDF p.285 / report p.284 | No tag; `B`; `Direct update` in addendum |
| TED, “Chemical scum that dream of distant quasars” (2005) | PDF p.151 / report p.150 | No tag; `B` |
| TED, “A new way to explain explanation” (2009) | PDF p.151 / report p.150 | No tag; `B` |
| Philosophy Bites, “David Deutsch on Explanation” (2011) | PDF p.151 / report p.150 | No tag; `B` |
| Guardian interview/profile (2011) | PDF p.152 / report p.151 | No tag; `B/C` |
| Sam Harris, “Surviving the Cosmos” (2014–16) | PDF p.152 / report p.151 | No tag; `B` |
| Talks at Google, “The Beginning of Infinity” (2016) | PDF p.152 / report p.151 | No tag; `B`; exact upload/timestamp required by report |
| Naval Ravikant/Deutsch long-form conversation (2019) | PDF p.153 / report p.152 | No tag; `B` |
| Eric Weinstein/Deutsch Portal conversation (2019) | PDF p.153 / report p.152 | No tag; `B` |
| Lex Fridman Podcast #142 (2020) | PDF p.154 / report p.153 | No tag; `B` |
| Naval/Deutsch follow-up clips on creativity/art (2021) | PDF p.154 / report p.153 | No tag; `B` |
| ToKCast Deutsch interviews (2022–24) | PDF p.155 / report p.154; generic Hall entry in bibliography PDF p.285 / report p.284 | No stable episode tag; `B` |
| Closer To Truth interviews (2023–24) | PDF p.155 / report p.154 | No tag; `B` |
| Tim Ferriss episode 662 with Deutsch and Naval (2023) | PDF p.155 / report p.154; bibliography PDF p.285 / report p.284 | No tag; `B` |
| Official articles archive; Taking Children Seriously corpus; “The Final Prejudice”/education talks | PDF p.156 / report p.155 | No tag; `A/index`, `A/B` or `C` depending authorship |
| Deutsch, “Beyond Reward and Punishment” (2019) | Part I uses at PDF pp.18, 22 / report pp.17, 21; bibliography PDF p.284 / report p.283 | No tag |
| Kristin Sainani, “Q&A: David Deutsch” (2015) | Part I citation PDF p.24 / report p.23; bibliography PDF p.285 / report p.284 | No tag; report treats surrounding profile material separately from direct quotation |
| Strange Loop interview (2025) | Addendum §1, PDF p.164 / report p.163; bibliography PDF p.285 / report p.284 | No tag; `Direct update`/corroboration |
| Do It podcast, “The Fun Criterion...” (2026) | Addendum §5, PDF pp.166–167 / report pp.165–166; bibliography PDF p.285 / report p.284 | No tag; `Direct update` |

### 2.4 Marletto public explanations and interviews

| Source | Exact report locus | Formal tag |
|---|---|---|
| “Formulating Science in Terms of Possible and Impossible Tasks” (Edge, 2014) | Bibliography PDF p.285 / report p.284 | None |
| “Constructing the Universe: An Interview with Chiara Marletto” (IAI, 2020) | Part I citation PDF p.27 / report p.26; bibliography PDF p.285 / report p.284 | `S-MAI20` |
| Brett Hall, “Chiara Marletto,” ToKCast episode 200 (2023) | Bibliography PDF p.285 / report p.284 | None |
| Constructor Theory, “Talks” | Bibliography PDF p.285 / report p.284 | None |

### 2.5 Background and comparative sources

| Source class | Sources listed | Exact report locus | Formal tags |
|---|---|---|---|
| Popperian background | Popper, *Logic of Scientific Discovery*; *Conjectures and Refutations*; *Objective Knowledge* | Bibliography PDF p.285 / report p.284 | None |
| Evolutionary background | Dawkins, *The Selfish Gene*; *The Extended Phenotype* | Bibliography PDF p.285 / report p.284 | None |
| Comparative creativity/cognition/AI | Boden; Finke/Ward/Smith; Runco/Jaeger; Beaty et al.; Cropley/Cropley; Mitchell | Bibliography PDF pp.285–286 / report pp.284–285 | None; bibliography says these do not define the Deutschian core |
| Public-dossier secondary criticism | Boden; Legg & Hutter; Godfrey-Smith; reconstructive cultural-evolution literature; Bender et al.; Chalmers; computational-creativity evaluation literature | PDF pp.161–162 / report pp.160–161 | Weight `S`; none |

### 2.6 Bibliography-to-inventory completeness finding

The bibliography opens by saying that it lists the sources used (PDF p.284 / report p.283), but it is not a complete one-to-one reproduction of the public inventory. Inventory items without individual bibliography entries include, among others: the official FOR/BOI pages; the Edge BOI conversation; “The truth is not out there”; “A new way to explain explanation”; the undated “My opinion...” post; the official articles archive; TED 2005/2009; Philosophy Bites; Guardian; Sam Harris; Talks at Google; the 2019 Naval and Weinstein discussions; Lex Fridman; Closer To Truth; TCS/“The Final Prejudice”; Legg–Hutter; Godfrey-Smith; the cultural-evolution cluster; Bender et al.; Chalmers; and the computational-creativity evaluation cluster. Their exact report inventory loci are PDF pp.145–156 and 161–162 / report pp.144–155 and 160–161.

## 3. Frozen Model CR-1.0 `S-*` source registry

### 3.1 Registry integrity summary

- Defined tags: **23**.
- Definition tokens: **23**, one per tag, at Model §0, PDF pp.219–221 / report pp.218–220.
- Total `S-*` tokens in the entire PDF: **153**.
- Operative/non-definition tokens: **130**.
- Undefined `S-*` uses: **0**.
- Duplicate `S-*` definitions: **0**.
- `S-*` tokens outside Model CR-1.0: **0**.
- Registry-only tag with zero operative use: **`S-FOR12`**.

The 23 identifiers are therefore lexically closed, but the registry is a selective entitlement registry, not a complete manifest of the report's sources.

### 3.2 Exhaustive tag definitions and operative occurrences

`Token count` includes the one definition occurrence. Every operative reference below is in Model CR-1.0; page pairs are `PDF/report`.

| Tag | Token count | Definition and external locator | Principal entitlement | Exhaustive operative clause/section occurrences |
|---|---:|---|---|---|
| `S-BOI1` | 20 | PDF 219/report 218; BOI Ch.1, print 1–33 / source-PDF 12–44 | explanation, problem, creativity, conjecture/criticism, anti-induction, hard-to-vary, reach, fallibility | `DF-1`, `DF-4`, `DF-4a`, `DF-5`, PDF 223/222; `DF-7`, `DF-8`, `DF-9`, `DF-10`, `DF-14`, PDF 224/223; `DP-1`, `DP-2`, `DP-4`–`DP-7`, PDF 226/225; `TH-1`, PDF 229/228; `TH-2`, PDF 229–230/228–229; `TH-3`, PDF 230/229; `TH-11`, PDF 231–232/230–231. |
| `S-BOI3` | 5 | PDF 219/report 218; BOI Ch.3, print 42–77 / source-PDF 53–88 | person, constructor, universal constructor, people as universal constructors, physical efficacy of knowledge | `DP-8`, `DP-11`, PDF 226/225; `TH-5`, PDF 230/229; `TH-15`, PDF 232–233/231–232. |
| `S-BOI4` | 8 | PDF 219/report 218; BOI Ch.4, print 78–106 / source-PDF 89–117 | variation/selection, adaptive vs explanatory knowledge, creativity/selection contrast, no favorable randomness | Model §3 Sources line, PDF 225/224; `DP-10`, `AB-1`, PDF 226/225; `TH-4`, PDF 230/229; `TH-8`, `TH-9`, `TH-10`, PDF 231/230. |
| `S-BOI6` | 10 | PDF 219/report 218; registry says BOI Ch.6, print 124–147 / source-PDF 135–158 | jumps to universality; universal computation, explanation, construction; digital correction | `DF-12`, `DF-13`, PDF 224/223; `DP-8`, `DP-9`, `DP-11`, PDF 226/225; `TH-5`, PDF 230/229; `TH-12`, `TH-13`, PDF 232/231; `TH-15`, PDF 232–233/231–232. Locator conflict recorded in §7. |
| `S-BOI7` | 12 | PDF 219/report 218; BOI Ch.7, print 148–163 / source-PDF 159–174 | AGI, behavior/origin distinction, programmer adaptation, artificial evolution, implementation gap | `DF-4`, `DF-6`, PDF 223/222; `DF-12`, `DF-13`, PDF 224/223; `DP-3`, `DP-8`, `DP-9`, PDF 226/225; `TH-4`, PDF 230/229; `TH-7`, PDF 230–231/229–230; `TH-12`, `TH-13`, PDF 232/231. |
| `S-BOI10` | 4 | PDF 220/report 219; BOI Ch.10, print 223–257 / source-PDF 234–268 | communication as fallible reconstruction, not literal semantic copying | `DF-3`, PDF 223/222; `DP-3`, PDF 226/225; `TH-17`, PDF 233/232. |
| `S-BOI14` | 3 | PDF 220/report 219; BOI Ch.14, print 353–368 / source-PDF 364–379 | art/reason, objective but fallible standards, inexplicit knowledge, hard-to-vary works | `DF-5`, PDF 223/222; `RC-3`, PDF 225/224. |
| `S-BOI15` | 3 | PDF 220/report 219; BOI Ch.15, print 369–397 / source-PDF 380–408 | rational/anti-rational culture, subpersonal variation/selection, person-level criticism | `DP-10`, PDF 226/225; `TH-9`, PDF 231/230. |
| `S-BOI16` | 10 | PDF 220/report 219; BOI Ch.16, print 398–417 / source-PDF 409–428 | creativity as software, reconstruction of meanings, universal explanatory reach, unknown mechanism | `DF-3`, PDF 223/222; `DF-12`, `DF-13`, PDF 224/223; `DP-3`, `DP-8`, `DP-9`, `DP-10`, PDF 226/225; `TH-9`, PDF 231/230; `TH-17`, PDF 233/232. |
| `S-FOR1` | 7 | PDF 220/report 219; FOR Ch.1, print 1–31 / source-PDF 13–43 | explanation vs prediction; creative subsidiary explanation vs mechanical consequence-taking; four strands | `DF-3`, `DF-4`, PDF 223/222; `DP-1`, PDF 226/225; `TH-1`, PDF 229/228; `TH-4`, PDF 230/229; `TH-17`, PDF 233/232. |
| `S-FOR3` | 16 | PDF 220/report 219; FOR Ch.3, print 55–72 / source-PDF 67–84 | problem–theory–criticism–error elimination–new problem; actual rivals; anti-induction; evolutionary disanalogy | `DF-1`, `DF-5`, `DF-6`, PDF 223/222; `DF-7`, `DF-9`, `DF-10`, PDF 224/223; `DP-2`, `DP-4`, `DP-5`, `DP-7`, `DP-10`, PDF 226/225; `TH-2`, PDF 229–230/228–229; `TH-3`, PDF 230/229; `TH-8`, `TH-9`, PDF 231/230. |
| `S-FOR8` | 8 | PDF 220/report 219; FOR Ch.8, print 167–193 / source-PDF 179–205 | replicators, adaptation, embodied knowledge, counterfactual causal contribution | `DF-10`, PDF 224/223; Model §3 Sources line, PDF 225/224; `DP-10`, `AB-1`, PDF 226/225; `TH-3`, PDF 230/229; `TH-8`, `TH-10`, PDF 231/230. |
| `S-FOR10` | 4 | PDF 220/report 219; FOR Ch.10, print 222–257 / source-PDF 234–269 | open-ended mathematical creativity, limits of fixed proof generators, physical computation | `DP-4`, PDF 226/225; `TH-2`, PDF 229–230/228–229; `TH-4`, PDF 230/229. |
| `S-FOR12` | 1 | PDF 220/report 219; FOR Ch.12, print 289–320 / source-PDF 301–332 | no authorless knowledge on a loop; physics lacked a creative/noncreative criterion | **No operative occurrence.** |
| `S-FOR13` | 3 | PDF 220/report 219; FOR Ch.13, print 321–343 / source-PDF 333–355 | four strands; computation permits artificial mentality but does not explain it | `DP-9`, PDF 226/225; `TH-13`, PDF 232/231. |
| `S-SCC3` | 3 | PDF 220/report 219; SCC Ch.3 | information media, copying/permutations, interoperability, physical universality | `CT-7`, PDF 228/227; `TH-13`, PDF 232/231. |
| `S-SCC5` | 7 | PDF 220/report 219; SCC Ch.5, print 139–157 | physical knowledge as resilient/causally active information; catalysts | Model §3 Sources line, PDF 225/224; `AB-1`, `DP-11`, PDF 226/225; `CT-7`, PDF 228/227; `TH-8`, `TH-10`, PDF 231/230. |
| `S-SCC7` | 3 | PDF 220/report 219; SCC Ch.7, print 204–226, esp. 215–221 | universal-constructor analogy; new knowledge by thinking; laws of creativity open | `DP-11`, PDF 226/225; `CT-7`, PDF 228/227. |
| `S-CT13` | 6 | PDF 220/report 219; Deutsch, “Constructor Theory,” *Synthese* 190 (2013), 4331–4359 | substrate, attribute, task, constructor, possible/impossible tasks | Model §3 Sources line, PDF 225/224; `DP-11`, PDF 226/225; `CT-7`, PDF 228/227; `TH-5`, PDF 230/229; `TH-14`, PDF 232/231. |
| `S-CTI15` | 3 | PDF 220/report 219; Deutsch & Marletto, CTI, *Proc. R. Soc. A* 471 (2015), 20140540 | information variables/media, cloning, permutations, interoperability | `CT-7`, PDF 228/227; `TH-14`, PDF 232/231. |
| `S-CTL15` | 7 | PDF 221/report 220; Marletto, CTL, *J. R. Soc. Interface* 12 (2015), 20141226 | no-design laws, replicator–vehicle architecture, accurate self-reproduction, natural selection | Model §3 Sources line, PDF 225/224; `DP-10`, `AB-1`, PDF 226/225; `CT-7`, PDF 228/227; `TH-8`, `TH-10`, PDF 231/230. |
| `S-CB12` | 7 | PDF 221/report 220; Deutsch, “Creative Blocks,” Aeon, 3 Oct. 2012 | producing new explanations; output-specification and behavioral insufficiency | `DF-4`, `DF-4a`, PDF 223/222; `DP-3`, PDF 226/225; `TH-4`, PDF 230/229; `TH-7`, PDF 230–231/229–230; `TH-12`, PDF 232/231. |
| `S-MAI20` | 3 | PDF 221/report 220; Marletto, “Constructing the Universe,” IAI interview (2020) | programmed universal constructor vs human originator of new ideas | `DP-11`, PDF 226/225; `TH-5`, PDF 230/229. |

### 3.3 Theorem source-entitlement matrix

These are the source-entitlement lines displayed by Model §8. They are **not** transitive source-provenance closures. For example, reusing a `DP-*` dependency can bring source commitments not repeated on the theorem's entitlement line.

| Result ID | Physical/report locus | Displayed source entitlement | Explicit source mark on entitlement |
|---|---|---|---|
| `TH-1` | PDF 229 / report 228 | `S-BOI1`, `S-FOR1` | four-way separation `R` |
| `TH-2` | PDF 229–230 / report 228–229 | `S-BOI1`, `S-FOR3`, `S-FOR10` | none |
| `TH-3` | PDF 230 / report 229 | `S-BOI1`, `S-FOR3`, `S-FOR8` | typed separation `R` |
| `TH-4` | PDF 230 / report 229 | `S-FOR1`, `S-FOR10`, `S-BOI4`, `S-BOI7`, `S-CB12` | none |
| `TH-5` | PDF 230 / report 229 | `S-BOI3`, `S-BOI6`, `S-CT13`, `S-MAI20` | none |
| `TH-6` | PDF 230 / report 229 | Model-internal; no source tag | none |
| `TH-7` | PDF 230–231 / report 229–230 | `S-BOI7`, `S-CB12` | paired construction `M` |
| `TH-8` | PDF 231 / report 230 | `S-BOI4`, `S-FOR3`, `S-FOR8`, `S-CTL15`, `S-SCC5` | none |
| `TH-9` | PDF 231 / report 230 | `S-FOR3`, `S-BOI4`, `S-BOI15`, `S-BOI16` | none |
| `TH-10` | PDF 231 / report 230 | `S-BOI4`, `S-FOR8`, `S-SCC5`, `S-CTL15` | separation `R` |
| `TH-11` | PDF 231–232 / report 230–231 | `S-BOI1` | none |
| `TH-12` | PDF 232 / report 231 | `S-BOI6`, `S-BOI7`, `S-CB12` | formal result `M` |
| `TH-13` | PDF 232 / report 231 | `S-BOI6`, `S-BOI7`, `S-FOR13`, `S-SCC3` | none |
| `TH-14` | PDF 232 / report 231 | `S-CT13`, `S-CTI15` | realization scheme `M` |
| `TH-15` | PDF 232–233 / report 231–232 | `S-BOI3`, `S-BOI6` | displayed bridge decomposition `R` |
| `TH-16` | PDF 233 / report 232 | standard metalogic; no `S-*` tag | standard metalogic `(M)` |
| `TH-17` | PDF 233 / report 232 | `S-FOR1`, `S-BOI10`, `S-BOI16` | none |

## 4. Source-status registry: all local schemes

Source/status letters are section-local. A flat `status` field would be semantically unsafe.

| Scheme ID used in this audit | Exact registry locus | Raw marks | Exact local meanings / role |
|---|---|---|---|
| `global_claim_v1` | Reading map, PDF p.13 / report p.12 | `D, X, Q, R, P, CT, E, T, N` | Definition; explicit source claim; qualified conjecture; reconstruction; substantive postulate; CT import; empirical premise; derived result; non-entailment. |
| `boi_index_v1` | BOI index, PDF p.30 / report p.29 | `E, Q, R, H`; composites | Explicit; qualified/open; reconstruction; historical/context-bound. |
| `for_index_v1` | FOR index, PDF p.84 / report p.83 | words, not letters | Explicit; Reconstruction; Gap; Dated/contested. |
| `ct_dossier_v1` | Marletto dossier §1.2, PDF p.119 / report p.118 | `D, P, R, E, C, A` | Definition/stipulation; physical principle/meta-law; conditional result; empirical/accepted science; conjecture/programme/open problem; analogy/story/thought experiment. |
| `public_weight_v1` | Public dossier, PDF p.143 / report p.142 | `A, B, C, S`; composites | Authored/direct; recorded interview/talk; reliable report/reconstruction; secondary. Orthogonal access-status field also used. |
| `recent_delta_v1` | Addendum, PDF p.164 / report p.163 | phrase labels | Direct update; Physical-layer update; No update. |
| `concordance_v1` | Unified concordance, PDF p.168 / report p.167 | `E, R, Q, C`; slash composites | Explicit; reconstruction/synthesis; qualified/gap/stronger not established; contested/dated/source-specific. |
| `model_source_v1` | Model §0, PDF p.219 / report p.218 | `X, R, M, Q, O`; slash/“from” composites used but not defined | Explicit/direct argument; exactifying reconstruction; added modeling/audit choice; qualified conjecture/guess; acknowledged open problem. |
| `precursor_audit_v1` | Superseded audit, PDF p.236 / report p.235 | `D, R, M, U`; many composites | Direct support; faithful reconstruction; methodological choice; unsupported/overreaching. |
| `application_claim_v1` | Applications, PDF p.257 / report p.256 | `K, C, E, N` | CR consequence; conditional application result; empirical attribution; non-entailment. |

### 4.1 Collision ledger

| Raw letter | Incompatible local meanings found in the PDF |
|---|---|
| `D` | Definition (`global_claim_v1`, `ct_dossier_v1`) versus directly supported (`precursor_audit_v1`). |
| `X` | Explicit source claim (`global_claim_v1`, `model_source_v1`); not used in BOI/concordance, which use `E` for explicit. |
| `E` | Empirical premise/attribution (`global_claim_v1`, `application_claim_v1`, CT dossier) versus explicit (`boi_index_v1`, `concordance_v1`). |
| `R` | Reconstruction in most schemes versus a conditional result in `ct_dossier_v1`. |
| `P` | Substantive postulate globally versus proposed physical principle/meta-law in the CT dossier. |
| `C` | CT conjecture/programme; public reliable-report weight; concordance contested/dated; downstream conditional result. |
| `A` | CT analogy/story versus strongest authored/direct public-source weight. |
| `M` | Modeling/audit choice in final Model and precursor audit; elsewhere `M` also occurs as a mathematical model metavariable and must not be lexically reclassified as a source mark. |
| `Q` | Qualified conjecture globally/BOI/concordance; final Model separates acknowledged open problems into `O`, while earlier schemes often include open programmes under `Q` or `C`. |

No source-status mark by itself determines logical availability, derivability, truth, or the handoff's procedural `DEF/IMP/DER` classification.

## 5. Exhaustive Model §0 `X/R/M/Q/O` occurrence registry

### 5.1 Atomic definitions

At PDF p.219 / report p.218, Model §0 defines exactly:

| Mark | PDF definition |
|---|---|
| `X` | explicitly stated or directly argued by the cited source |
| `R` | reconstruction that makes an explicit claim more exact |
| `M` | added modeling or audit choice |
| `Q` | qualified conjecture or guess in the source |
| `O` | open problem acknowledged by the source |

The PDF gives no formal semantics for slash composition or the phrase `R from X`.

### 5.2 Exhaustive status-bearing occurrences under `model_source_v1`

There are **36** status-bearing occurrences after the registry: 18 contain `X`, 25 contain `R`, 7 contain `M`, 2 contain `Q`, and 1 contains `O` (53 atomic mark memberships because compounds count toward more than one letter). Mathematical metavariables such as `M,h,t |= φ`, predicate letters, and ordinary prose words are excluded.

| # | Report section ID / identifier | Raw mark exactly used | Source tags on the occurrence | Physical/report locus |
|---:|---|---|---|---|
| 1 | Model §1.3 `SC-3` | `M reconstruction` | none | PDF 222 / report 221 |
| 2 | Model §2 `DF-1` | `[R: ...]` | `S-BOI1`, `S-FOR3` | PDF 223 / report 222 |
| 3 | Model §2 `DF-2` | `[R]` | none | PDF 223 / report 222 |
| 4 | Model §2 `DF-3` | `[R: ...]` | `S-FOR1`, `S-BOI10`, `S-BOI16` | PDF 223 / report 222 |
| 5 | Model §2 `DF-4` | `[R from X: ...]` | `S-BOI1`, `S-BOI7`, `S-CB12`; correction `S-FOR1` | PDF 223 / report 222 |
| 6 | Model §2 `DF-4a` | `[R from X: ...]` | `S-BOI1`, `S-CB12` | PDF 223 / report 222 |
| 7 | Model §2 `DF-5` | `[R: ...]` | `S-FOR3`, `S-BOI1`, `S-BOI14` | PDF 223 / report 222 |
| 8 | Model §2 `DF-6` | `[R/M: ...]` | `S-FOR3`, `S-BOI7` | PDF 223 / report 222 |
| 9 | Model §2 `DF-7` | `[R from X: ...]` | `S-FOR3`, `S-BOI1` | PDF 224 / report 223 |
| 10 | Model §2 `DF-8` | `[R from X: ...]` | `S-BOI1` | PDF 224 / report 223 |
| 11 | Model §2 `DF-9` | `[R: ...]` | `S-BOI1`, `S-FOR3` | PDF 224 / report 223 |
| 12 | Model §2 `DF-10` | `[R: ...]` | `S-BOI1`, `S-FOR3`, `S-FOR8` | PDF 224 / report 223 |
| 13 | Model §2 `DF-12` | `[R: ...]` | `S-BOI6`, `S-BOI7`, `S-BOI16` | PDF 224 / report 223 |
| 14 | Model §2 `DF-13` | `[X/R/Q: ...]` | `S-BOI6`, `S-BOI7`, `S-BOI16` | PDF 224 / report 223 |
| 15 | Model §2 `DF-14` | `[R from X: ...]` | `S-BOI1` | PDF 224 / report 223 |
| 16 | Model §4 `DP-1` | `X` | `S-BOI1`, `S-FOR1` | PDF 226 / report 225 |
| 17 | Model §4 `DP-2` | `X` | `S-BOI1`, `S-FOR3` | PDF 226 / report 225 |
| 18 | Model §4 `DP-3` | `X/R` | `S-BOI7`, `S-BOI10`, `S-BOI16`, `S-CB12` | PDF 226 / report 225 |
| 19 | Model §4 `DP-4` | `X` | `S-BOI1`, `S-FOR3`, `S-FOR10` | PDF 226 / report 225 |
| 20 | Model §4 `DP-5` | `X/R` | `S-FOR3`, `S-BOI1` | PDF 226 / report 225 |
| 21 | Model §4 `DP-6` | `X/R` | `S-BOI1` | PDF 226 / report 225 |
| 22 | Model §4 `DP-7` | `X/R` | `S-FOR3`, `S-BOI1` | PDF 226 / report 225 |
| 23 | Model §4 `DP-8` | `X/Q` | `S-BOI3`, `S-BOI6`, `S-BOI7`, `S-BOI16` | PDF 226 / report 225 |
| 24 | Model §4 `DP-9` | `X/O` | `S-BOI6`, `S-BOI7`, `S-BOI16`, `S-FOR13` | PDF 226 / report 225 |
| 25 | Model §4 `DP-10` | `X` | `S-BOI4`, `S-BOI15`, `S-BOI16`, `S-FOR3`, `S-FOR8`, `S-CTL15` | PDF 226 / report 225 |
| 26 | Model §4 `AB-1` | `X/R` | `S-BOI4`, `S-FOR8`, `S-CTL15`, `S-SCC5` | PDF 226 / report 225 |
| 27 | Model §4 `DP-11` | `X/R` | `S-BOI3`, `S-BOI6`, `S-CT13`, `S-SCC5`, `S-SCC7`, `S-MAI20` | PDF 226 / report 225 |
| 28 | Model §7.2 unnumbered task-network paragraph after `DF-23` | `R/M reconstruction` | none | PDF 229 / report 228 |
| 29 | Model §8 `TH-1` source entitlement | separation `R` | `S-BOI1`, `S-FOR1` | PDF 229 / report 228 |
| 30 | Model §8 `TH-3` source entitlement | typed separation `R` | `S-BOI1`, `S-FOR3`, `S-FOR8` | PDF 230 / report 229 |
| 31 | Model §8 `TH-7` source entitlement | paired construction `M` | `S-BOI7`, `S-CB12` | PDF 231 / report 230 |
| 32 | Model §8 `TH-10` source entitlement | separation `R` | `S-BOI4`, `S-FOR8`, `S-SCC5`, `S-CTL15` | PDF 231 / report 230 |
| 33 | Model §8 `TH-12` source entitlement | formal result `M` | `S-BOI6`, `S-BOI7`, `S-CB12` | PDF 232 / report 231 |
| 34 | Model §8 `TH-14` source entitlement | realization scheme `M` | `S-CT13`, `S-CTI15` | PDF 232 / report 231 |
| 35 | Model §8 `TH-15` source entitlement | displayed bridge decomposition `R` | `S-BOI3`, `S-BOI6` | PDF 233 / report 232 |
| 36 | Model §8 `TH-16` source entitlement | standard metalogic `(M)` | none | PDF 233 / report 232 |

No other Model clause has an `O` mark. No other Model clause has a `Q` mark. `CT-7` describes an open programme and cites sources at PDF p.228 / report p.227, but it is not marked `O` or `Q`.

### 5.3 Earlier `X/R/Q` uses that are not Model §0 marks

The Part I map at PDF pp.15–16 / report pp.14–15 uses the earlier `global_claim_v1` scheme:

| Part I map row | Raw status |
|---|---|
| What is creativity? | `X` |
| What is an explanation? | `X, with an admitted analysis gap` |
| What makes an explanation good? | `X` |
| What is reach? | `X` |
| What is intelligence? | `R from explicit connections` |
| What is an AGI? | `X/Q` |
| What do art and reason share? | `X/Q` |
| What does natural selection share with creativity? | `X` |
| How do natural selection and creativity differ? | `X` |
| Does constructor theory define creativity? | `X/R` |

The BOI index's many `[R]`, `[Q]`, `[Q/R]`, and related marks belong to `boi_index_v1`, not `model_source_v1`; their complete coverage is the BOI index at PDF pp.30–83 / report pp.29–82. The superseded audit's `R/M` compounds belong to `precursor_audit_v1`, not the final Model scheme.

## 6. Identifier integrity and namespace registry

### 6.1 Final Model identifier families

The final Model contains the following intended clause namespaces in PDF pp.221–234 / report pp.220–233:

| Family | Final Model range | Definition locus | Source-mark coverage finding |
|---|---|---|---|
| `TY-*` | `TY-1`–`TY-3` | PDF p.221 / report p.220 | all null |
| `MS-*` | `MS-1`–`MS-9` | PDF pp.221–222 / report pp.220–221 | all null |
| `SC-*` | `SC-1`–`SC-8` | PDF pp.222–223 / report pp.221–222 | only `SC-3 = M` |
| `DF-*` | `DF-1`–`DF-23`, plus `DF-4a`, `DF-7a` | PDF pp.223–225 and 228–229 / report pp.222–224 and 227–228 | 14 status-bearing definitions; `DF-7a`, `DF-11`, `DF-15`–`DF-23` null |
| `RC-*` | `RC-1`–`RC-3` | PDF p.225 / report p.224 | all null, though `RC-3` has `S-BOI14` and §3 has a source line |
| `DP-*` | `DP-1`–`DP-11` | PDF p.226 / report p.225 | all marked and tagged |
| `AB-*` | `AB-1` | PDF p.226 / report p.225 | `X/R`, tagged |
| `OM-*` | `OM-1`–`OM-10` | PDF p.227 / report p.226 | all null |
| `IR-*` | `IR-1`–`IR-8` | PDF pp.227–228 / report pp.226–227 | all null |
| `CT-*` | `CT-1`–`CT-7` | PDF p.228 / report p.227 | all null; `CT-7` has tags |
| `BR-*` | `BR-1`–`BR-8` | PDF pp.228–229 / report pp.227–228 | all null |
| `TH-*` | `TH-1`–`TH-17` | PDF pp.229–233 / report pp.228–232 | eight marked, nine null |

There is no duplicate definition detected inside the final Model namespace. The source-mark field is nevertheless absent for many clauses despite Model §0's statement that source commitments “are labeled” (PDF p.219 / report p.218). A missing mark must be represented as null; it cannot be inferred from a section title such as “reconstruction choice” or from prose similarity.

### 6.2 Superseded precursor collisions

The retained audit is explicitly about a different, superseded candidate (PDF p.236 / report p.235). It nevertheless reuses final-looking labels:

- precursor `DF-1`–`DF-30` are audited at PDF pp.240–246 / report pp.239–245;
- precursor `BR-1`–`BR-8` are audited at PDF pp.246–248 / report pp.245–247;
- precursor `TH-1`–`TH-22` are audited at PDF pp.248–250 / report pp.247–249;
- its final disposition then refers back to corrected final CR-1.0 identifiers at PDF pp.255–256 / report pp.254–255.

Consequences for a registry:

| Finding | Exact locus / consequence |
|---|---|
| Same lexical identifiers, different systems | `DF-1`–`DF-23`, `BR-1`–`BR-8`, and `TH-1`–`TH-17` occur in both final/legacy discussion. A flat identifier key would conflate distinct clauses. |
| Legacy-only identifiers | Precursor `DF-24`–`DF-30` and `TH-18`–`TH-22` are not missing final Model clauses. They are legacy identifiers. |
| Final-only inserted subidentifiers | `DF-4a` and `DF-7a` are final-model repairs and appear in the final-disposition crosswalk; they are not gaps in the precursor sequence. |
| Required namespace split | Preserve at least `model_cr_1_0::<id>` and `superseded_precursor::<id>`, plus a separate `final_disposition_reference::<id>` role on PDF pp.255–256. This is a registry observation, not a repair of either text. |

### 6.3 Alternate source-anchor namespace

The superseded audit defines `BOI-*`, `FOR-*`, and `SCC-*` anchors at PDF pp.237–238 / report pp.236–237. They are not aliases declared by the PDF for `S-BOI*`, `S-FOR*`, or `S-SCC*`.

- Legacy BOI anchors: `BOI-1`, `3`, `4`, `6`, `7`, `10`, `14`, `15`, `16`.
- Legacy FOR anchors: `FOR-1`, `3`, `5`, `8`, `10`, `12`, `13`, `14`.
- Legacy SCC anchors: `SCC-1`, `2`, `3`, `5`, `7`.

`FOR-5`, `FOR-14`, `SCC-1`, and `SCC-2` have no corresponding frozen `S-*` tag. The art application later relies on FOR Ch.5 and SCC pp.13–18 (PDF p.266 / report p.265), illustrating why silently aliasing only the overlapping numbers would lose coverage.

## 7. Source and status defects / ambiguity register

### A-01 — `S-BOI6` locator conflict

- Frozen Model registry: BOI Ch.6, **print 124–147 / source-PDF 135–158** (PDF p.219 / report p.218).
- BOI chapter map: BOI Ch.6, **print 125–147 / source-PDF 136–158** (PDF p.81 / report p.80; the chapter discussion begins PDF p.40 / report p.39).
- Superseded audit repeats the frozen registry's off-by-one version (PDF p.237 / report p.236).

Both report readings are preserved. The PDF does not resolve which external-source start page is intended.

### A-02 — SCC pagination basis conflict

- The Marletto dossier says the supplied EPUB contains print-page anchors and uses them (PDF p.118 / report p.117).
- The unified concordance says SCC has “no stable print pagination” and therefore locates it by chapter (PDF p.168 / report p.167).
- The frozen registry gives chapter-only `S-SCC3` but print ranges for `S-SCC5` and `S-SCC7` (PDF p.220 / report p.219).

The edition/location basis for the SCC print ranges is not reconciled.

### A-03 — Unregistered composite source-mark syntax

Model §0 defines only atomic `X/R/M/Q/O` (PDF p.219 / report p.218), but the Model uses `R from X`, `R/M`, `X/R`, `X/R/Q`, `X/Q`, and `X/O` (PDF pp.223–226 and 229–233 / report pp.222–225 and 228–232). The PDF does not define whether `/` means conjunction, clause partition, mixed provenance, or something else. Mixed clauses are not proposition-segmented. `DP-8` and `DP-9` are especially material because each combines explicit content with qualified/open content under one identifier.

### A-04 — Incomplete clause-level source marking

Model §0 says source commitments are labeled, yet the following final-model items have null `model_source_v1` marks:

- `TY-1`–`TY-3`; `MS-1`–`MS-9`;
- `SC-1`, `SC-2`, `SC-4`–`SC-8`;
- `DF-7a`, `DF-11`, `DF-15`–`DF-23`;
- `RC-1`–`RC-3`;
- `OM-1`–`OM-10`; `IR-1`–`IR-8`; `CT-1`–`CT-7`; `BR-1`–`BR-8`;
- `TH-2`, `TH-4`, `TH-5`, `TH-6`, `TH-8`, `TH-9`, `TH-11`, `TH-13`, `TH-17`;
- Model §§9–10 prose.

`DF-2` is marked `R` but has no source tag (PDF p.223 / report p.222). The task-network proposal is marked `R/M` but has no identifier or source tag (PDF p.229 / report p.228). `CT-7` has tags and calls the laws open, but has no mark (PDF p.228 / report p.227).

### A-05 — `S-FOR12` is inert in the formal model

`S-FOR12` is defined once at PDF p.220 / report p.219 and never cited by any clause or theorem. Its subject is used in prose elsewhere, including the physical creative/noncreative gap in Part I (PDF p.16 / report p.15), but the frozen tag has zero operative use.

### A-06 — Recent direct provenance is absent from the frozen registry

The addendum says:

- Strange Loop strengthens authorship/provenance and performance-inventory limits (PDF p.164 / report p.163);
- the Altman–Deutsch correction bears on `SC-4`, `DF-4`, `DF-12`, `BR-1`, `BR-6`, and behavior-to-mechanism underdetermination (PDF pp.164–165 / report pp.163–164);
- CT Time and Tests of CT refine the physical layer (PDF pp.165–166 / report pp.164–165);
- the Do It interview supports content-sensitive conflict/criticism and bears on `SC-2`, `SC-3`, `BR-5` (PDF pp.166–167 / report pp.165–166).

None receives an `S-*` tag or appears in the named clause entitlements.

### A-07 — Application source coverage is prose-only

The entire applications unit contains zero `S-*` tokens. Clear source-specific cases include `I-AR-SHARED` and `I-COMM` (PDF p.260 / report p.259), art/virtual-rendering claims (PDF p.266 / report p.265), communication/reconstruction (PDF p.267 / report p.266), LLM historical correction and AGI interpretation (PDF pp.269–270 / report pp.268–269), mathematical creativity (PDF p.270 / report p.269), and natural-selection claims (PDF p.272 / report p.271).

### A-08 — Several frozen source locators are source identities, not claim locators

- `S-SCC3`: chapter only.
- `S-CT13`, `S-CTI15`, `S-CTL15`: article-level identities, no section/page pinpoint in the frozen registry.
- `S-CB12`: whole essay, no paragraph/section locator.
- `S-MAI20`: whole interview, no timestamp or paragraph locator.

The detailed dossier sometimes supplies better internal guidance, but the frozen tag itself remains coarse.

### A-09 — Theorem entitlement lines are not provenance closure

Model §8 calls each dependency line exhaustive for the displayed result and separately says source tags justify source-facing postulates (PDF p.229 / report p.228). The source-entitlement line does not enumerate the full sources of reused postulates. Therefore `TH-* -> displayed S-*` is not a complete transitive source dependency graph.

### A-10 — Status namespaces cannot be merged

The collision table in §4.1 is an internal-report ambiguity, not a typographical issue. Any extraction lacking `scheme_id` would invert meanings such as `E` (explicit versus empirical) and `C` (conjecture, reliable report, contested, or conditional result).

### A-11 — Bibliography and public inventory do not form one complete registry

The public dossier contains numerous used sources absent as individual bibliography entries; see §2.6. Conversely, the bibliography includes sources that have no claim-level tag. The phrase “bibliography and source registry” at PDF p.284 / report p.283 therefore denotes a broad bibliography, not a closed formal source registry.

### A-12 — Final/precursor identifier duplication is intentional but globally unsafe

The final Model and superseded audit reuse `DF-*`, `BR-*`, and `TH-*` labels. This is safe only when the report-unit namespace is retained. A global uniqueness check without section/version namespace will report true lexical collisions and may attach legacy meanings to final clauses.

## 8. Procedural-handoff ambiguity ledger

The entries below do not alter CR-1.0.

| ID | Handoff locus | PDF authority locus | Finding |
|---|---|---|---|
| `H-01` | lines 11–15 | Supplied artifact; PDF p.1 | Handoff names `Creativity_Semantic_Model_CR-1.0.pdf`; supplied file is `Creativity_Semantic_Model_CR-1.0(1).pdf`. The SHA-256 above fixes identity. |
| `H-02` | lines 19–31 (`DEF/IMP/DER`) | Global statuses PDF p.13/report p.12; Model marks PDF p.219/report p.218 | `DEF/IMP/DER` is procedural inferential metadata, not a PDF source-status registry and not an existing CR-1.0 classification. It must not be inferred from `X/R/M/Q/O`. |
| `H-03` | line 49 | `TY-2`, PDF p.221/report p.220 | Handoff expands the required-baseline word list with `stable` and `authored` and expands baseline dimensions. Those are procedural additions; the exact CR-1.0 `TY-2` wording controls conformance. |
| `H-04` | Part 1A, lines 85–213 | Exact Model §§1–7, PDF pp.221–229/report pp.220–228 | Part 1A paraphrases and relabels formal content without preserving every exact clause identifier. It is a work plan, not a replacement clause set. |
| `H-05` | lines 438–448 | Coverage matrix in §1 above | Handoff locations are explicitly approximate. Exact physical ranges are those recorded from the PDF here; notably the BOI index begins PDF p.30, although the handoff says “page 31 onward.” |
| `H-06` | lines 452–462 | Model §0, PDF p.219/report p.218 | Handoff restates atomic marks accurately but adds inferential consequences and says `Q/O` are unavailable to proofs. Those are procedural rules, not extra semantics in the PDF. It gives no semantics for the PDF's compound marks. |
| `H-07` | lines 464–474 | Entire PDF, especially Model §0 and Part III | Handoff's conformance hierarchy is procedural. Under the user's authority clarification, no handoff text can override or supplement any PDF clause. |
| `H-08` | lines 512–516 | Missing-mark findings §§5–7 above | Handoff says the bootstrap gate fails if any clause lacks `DEF/IMP/DER`. The PDF provides no such classification, so a gate pass cannot be reported merely from source marks. |
| `H-09` | lines 450, 514–516 | Model and all indexed report units | Handoff requires complete source/status and identifier capture. The frozen PDF has the internal locator, marking, and namespace defects catalogued above; these must remain ambiguity records rather than silent repairs. |
| `H-10` | lines 315, 327, 338, 350 | Frozen registry, PDF pp.219–221/report pp.218–220 | Every literal handoff `S-*` reference is defined by the PDF: `S-BOI1`, `S-FOR1`, `S-FOR3`, `S-CB12`; `S-BOI7`, `S-BOI10`, `S-BOI16`; and `S-BOI3`, `S-BOI6`. The handoff phrases “relevant art, communication, and AGI passages” and “related source entries” are not machine-resolvable identifiers and add no source entitlement. |

## 9. Bootstrap gate assessment limited to source/identifier work

| Check | Finding | Status |
|---|---|---|
| PDF identity and full-page coverage | Hash, metadata, page mapping, and all 286 physical pages recorded | PASS |
| Frozen `S-*` lexical closure | 23 unique definitions; 153 valid occurrences; no undefined or duplicate tag definition | PASS |
| Frozen source-tag operative coverage | `S-FOR12` is definition-only; recent/public/application sources are untagged | BLOCKED / incomplete |
| Exact source locators | `S-BOI6` has an unresolved off-by-one conflict; several tags are article/chapter-level only; SCC pagination basis conflicts | BLOCKED |
| Source-status extraction | Every final-Model status-bearing `X/R/M/Q/O` occurrence is listed above | PASS for observed marks |
| Source-status completeness | Many clauses have null marks; compound syntax is unregistered | BLOCKED |
| Global identifier uniqueness | Final namespace is internally coherent, but final and superseded namespaces collide lexically | PASS only with explicit namespace; FAIL if flat |
| Handoff conformance metadata | `DEF/IMP/DER` cannot be assigned from PDF source marks without a separate, explicit procedural classification | NOT ESTABLISHED |

The source-registry work product is therefore complete as an **audit record**, but the handoff's bootstrap gate cannot be marked passed from the authority PDF without carrying forward the recorded ambiguities and null fields.
