# CR-EIB 0.2 research basis

## Status and authority boundary

This note records engineering research used before introducing the CR-EIB 0.2
type-and-projection process and before designing a DF-7a source-to-IR mapping.
It is advisory. The supplied CR-1.0 PDF remains the sole semantic and formal
authority for the creativity calculus. No paper, search result, or tool listed
here can add a CR-1.0 premise, repair a source ambiguity, or promote a bridge
choice from proposed to accepted.

The research questions were:

- how should an authoritative semantic source be made executable in Lean
  without confusing successful compilation with faithful translation;
- how should projections, assumptions, ambiguity, and loss remain auditable;
- what can a pinned container establish about an operational replay; and
- how can human source-semantic review remain separate from mechanized proof?

## Research channels and evidence classes

Fresh, independent searches were run through AlphaXiv and Consensus for both
container reproducibility and source-to-IR review. AlphaXiv page-level PDF
queries were used to inspect selected papers. Every Consensus result relied on
below was fetched as a full paper record rather than cited from a search
snippet. The two services are discovery and cross-check channels, not semantic
authorities.

Material design claims below are grounded in original papers or official
specifications. AlphaXiv AI overviews and Consensus-generated summaries are not
treated as primary evidence. A preprint remains a preprint even when both
services retrieve it.

| Evidence class | Permitted use | Prohibited use |
|---|---|---|
| CR-1.0 authority bytes | Decide what the source says, subject to explicit human review of ambiguity | Be silently completed from papers or theorem needs |
| Primary paper or official specification | Support an engineering process or document a known limitation | Decide CR-1.0 types, binders, relations, or intended readings |
| AlphaXiv or Consensus discovery record | Find and independently cross-check candidate literature | Establish a repository claim without checking the primary source |
| Lean kernel or replay output | Check a typed proposition relative to imports and axioms | Certify that the proposition faithfully expresses the PDF |

## Primary evidence used

| Primary source | Result used here | Practical boundary |
|---|---|---|
| [Translation Validation](https://doi.org/10.1007/BFb0054170), Pnueli, Siegel, and Singerman (TACAS 1998) | Per-run translation validation requires a common formal semantic framework and a stated refinement relation between source and target. | CR-1.0 prose is not already a fully formal source language. The method motivates per-mapping validation, but it cannot automatically prove the intended meaning of an ambiguous PDF passage. |
| [Towards Trustworthy Automated Program Verifiers](https://doi.org/10.1145/3656438), Parthasarathy et al. (OOPSLA 2024), with [extended version](https://arxiv.org/abs/2404.03614) | An independently checkable proof can validate each implemented translation into an intermediate verification language when the input and target languages have formal semantics. | A future CR-EIB certificate may check typed closure and preservation obligations after semantic choices are accepted. It cannot substitute for the human choice that supplies a formal source reading. |
| [Validating a Lean Proof](https://lean-lang.org/doc/reference/latest/ValidatingProofs/), official Lean reference | Kernel replay, axiom inspection, and `lean4checker` validate formal artifacts only under the assumption that the formal statement has its intended informal meaning. | Proof success and source fidelity remain different verdicts. |
| [Reliable Evaluation and Benchmarks for Statement Autoformalization](https://aclanthology.org/2025.emnlp-main.907/), Poiroux et al. (EMNLP 2025) | Typechecking alone is not a semantic evaluation; automated equivalence metrics are evaluated against human judgments and remain imperfect. | Automated checks may reject or triage a mapping. They may not accept DF-7a semantics. |
| [Identifying and fixing ambiguities in, and semantically accurate formalisation of, behavioural requirements](https://doi.org/10.1007/s10270-023-01142-0), Nguyen et al. (Software and Systems Modeling 2024) | Ambiguity removal and formalization require domain knowledge and, in some cases, stakeholder decisions; implied additions should be exposed. | An unresolved source phrase must produce alternatives and an open decision, not a theorem-driven default. |
| [OCI Content Descriptors](https://github.com/opencontainers/image-spec/blob/main/descriptor.md), Open Container Initiative | An OCI digest is a content identifier that can be independently verified against image bytes. | A mutable image tag or a Dockerfile alone does not identify the replay environment. |
| [Dockerfile reference](https://docs.docker.com/reference/dockerfile/) and [reproducible-build guidance](https://docs.docker.com/build/ci/github-actions/reproducible-builds/), official Docker documentation | BuildKit exposes `SOURCE_DATE_EPOCH` and deterministic-output controls for eliminating identified sources of image variance. | These controls address known nondeterminism; they do not make an unpinned recipe or live package repository reproducible. |
| [Development Container Specification](https://containers.dev/implementors/spec/) | A DevContainer can wrap a Dockerfile or image with development-specific configuration. | The wrapper is a usability surface. The content-addressed OCI image and recorded replay perimeter carry the evidence identity. |
| [Managing Toolchains with Elan](https://lean-lang.org/doc/reference/latest/Build-Tools-and-Distribution/Managing-Toolchains-with-Elan/) and [Lake](https://lean-lang.org/doc/reference/latest/Build-Tools-and-Distribution/Lake/), official Lean reference | A project should select a specific `lean-toolchain`; a committed Lake manifest identifies the transitive package versions used by the package. | A floating Lean channel or regeneration of the manifest during replay changes the evidence identity. |
| [What's in a build environment?](https://reproducible-builds.org/docs/perimeter/), Reproducible Builds project | Reproducibility claims are relative to a declared environment including tool versions, architecture, directory, locale, timezone, and relevant environment variables. Containers help define that perimeter but can hide host assumptions. | A container narrows the environment; it does not by itself establish bit-for-bit reproducibility across hosts. |
| [It's Not Just Timestamps: A Study on Docker Reproducibility](https://arxiv.org/abs/2602.17678), Solarin (2026 preprint) | In two clean builds on one platform and architecture, only 30 of 1,123 buildable sampled Dockerfiles were bitwise reproducible as written; floating versions, caches, logs, generated files, and metadata were recurring causes. | This is a recent preprint with a same-host, one-Dockerfile-per-repository design. It supports caution and test design, not a universal rate or a guarantee for this repository. |

## Advisory discovery results

The fresh searches produced useful, non-authoritative signals:

| Channel | Independently retrieved work | Advisory consequence |
|---|---|---|
| AlphaXiv and Consensus | Solarin's Docker reproducibility preprint: [AlphaXiv record](https://www.alphaxiv.org/abs/2602.17678) and [fetched Consensus record](https://consensus.app/papers/it’s-not-just-timestamps-a-study-on-docker-reproducibility-solarin/ff6d3989fd9b510f9fc1cb71d2739777/) | Both searches warn against equating containerization with reproducible image bytes. The implementation consequence is checked against the primary preprint and official OCI, Docker, Lean, and Reproducible Builds documentation. |
| Consensus | Fetched records for [translation validation](https://consensus.app/papers/translation-validation-pnueli-siegel/b1f96ff49d225da39fac90f735af9aa8/), [per-run IVL validation](https://consensus.app/papers/towards-trustworthy-automated-program-verifiers-parthasarathy-dardinier/162f4e20c10c57c3aa4c9575982de635/), and [requirements ambiguity](https://consensus.app/papers/identifying-and-fixing-ambiguities-in-and-semantically-nguyen-sayar/0bfaa47abe8b5bfeb82282092e88b4dc/) | The independent search supported a per-mapping validation process with explicit ambiguity decisions. Claims were checked against the DOI, ACM/arXiv, and Springer primary records. |
| AlphaXiv | [Lean Atlas](https://www.alphaxiv.org/abs/2604.16347) and [ProofFlow](https://www.alphaxiv.org/abs/2510.15981) | Dependency cones and source-step graphs can focus review and preserve traceability. Their semantic checks do not remove the need for a human reviewer of definitions and propositions. |
| AlphaXiv | [The Faithfulness Gap](https://www.alphaxiv.org/abs/2606.16541) | Counterfactual probes and directional drift categories are useful review prompts. The paper is a recent preprint, and its learned or generated natural-language bridge is not an authority oracle. |

AlphaXiv discovery and PDF retrieval completed. One earlier batched PDF response
was truncated and interleaved, so the relevant papers were queried separately
before any claim was retained. Consensus search and required full-record fetches
completed in the fresh pass. Consensus records provide metadata and abstracts,
not guaranteed full text; one result without enough primary content was
excluded. These connector limitations are part of the research provenance.

## Adopted engineering practices

| Practice | Research basis | CR-EIB 0.2 consequence |
|---|---|---|
| Report formal validity separately from semantic fidelity | [Beyond Compilation: Evaluating Faithful Natural-Language-to-Lean Statement Formalization](https://www.alphaxiv.org/abs/2606.31002), especially pp. 1–4, shows that a declaration may compile while omitting hypotheses, changing domains, or becoming vacuous. It evaluates compilation and semantic faithfulness separately and treats independent model consensus as a conservative filter rather than an equivalence proof. | Lean replay status cannot imply source fidelity. Declaration records and verifier output expose operational replay, mapping fidelity, and bridge conformance as different judgments. |
| Preserve provenance, surrounding source context, and independent review | [FormaTheoria: Constructing Large-Scale Lean Theories from Mathematical Literature](https://www.alphaxiv.org/abs/2608.10894), especially pp. 1 and 6–7, treats dependency discovery, source defects, semantic fidelity, provenance, and review gates as distinct workflow concerns. | Every new interpretation points to source regions and named bridge choices, records losses and open obligations, and remains unaccepted while review or coverage is incomplete. |
| Make translation obligations explicit and retain boundary information | [Kairos: Generating Tick-Indexed Proof Obligations for Synchronous Temporal Contracts](https://www.alphaxiv.org/abs/2607.23178), especially pp. 1–2, connects source contracts to generated local obligations through a mechanized translation and preserves distinctions between temporal boundaries. | The DF-10 surface projection retains the selected pair `(I, t_I)` and its endpoint evidence. It does not erase to a bare interval or invent endpoint totality, uniqueness, or maximality. |
| Put generated interpretation outside the trusted semantic boundary | [Proof-Carrying Certificates for LLM Pipelines: A Trust-Boundary Architecture](https://www.alphaxiv.org/abs/2605.16407), especially pp. 1, 11–12, and 19, distinguishes kernel-checked structure from unverified semantic or human oracles and audits declared axioms and scope. | Kernel-checked projection and model-expansion theorems certify only their typed bridge statements. Opaque source predicates, role semantics, and source-level fidelity remain declared limitations rather than hidden assumptions. |

The four works in this table are current AlphaXiv-discovered design signals,
not CR-1.0 evidence. They remain advisory under the evidence classes above.

## Container-replay consequence

A permanent OCI image plus a DevContainer wrapper is realistic for portable,
cold-start operational replay. The evidence does not support calling the recipe
itself a reproducible build.

The replay environment should therefore pin the base image and final image by
digest, the platform, the exact Lean toolchain, the Lake dependency manifest,
the Python and PDF-extractor inputs, and the replay command. Runtime replay
should begin from the nominated image without `LD_PRELOAD`, inherited build
caches, or network access, and should record tool versions, input hashes, exit
statuses, and output hashes. Locale, timezone, work directory, user, umask, and
other relevant environment choices belong to the declared perimeter.

Until independent no-cache image builds produce the same digest, the defensible
claim is `cold-start operational replay in a content-addressed environment`,
not `bitwise-reproducible container build`. The new replay supplements the
existing scoped audit; it does not retroactively change the meaning of an
earlier `PASS`.

## DF-7a source-to-IR consequence

The appropriate target is a review-carrying mapping with a machine-checkable
closure certificate, not a machine proof of the PDF's intended meaning. The
mapping design must bind the authority bytes and exact source regions, preserve
the surrounding MS-4, SC-7, and SC-8 context, enumerate alternative readings,
and record every type addition, strengthening, erasure, or unresolved phrase.

For any DF-7a encoding intended to become an accepted source mapping, human
semantic review comes first and formal type review follows selection of a
reading. Exploratory kernel replay may still use opaque ports or explicitly
non-authoritative alternatives, as the current relative pilot does, but that
replay cannot count toward mapping acceptance or source-dependency closure.
Machine checks may verify that a selected reading is internally typed, that its
declared fields cover the selected source obligations, and that proofs use no
undeclared axioms. They may not select the reading or infer it from what makes
DF-10 or TH-3 provable.

The current source-led design is recorded in
[CR-EIB-0.2 DF-7a / CCPWitness mapping design](./CR-EIB-0.2_DF7a_CCPWitness_Mapping_Design.md).
It is explicitly `UNREVIEWED`, creates no mapping record or source anchor,
and accepts no interpretation.

## Existing bridge consequence

The next bridge layer is additive. It preserves the legacy pilot, introduces a
shared-content role refinement as a visibly proposed interpretation, and proves
DF-10 expansion only relative to the already refined model and opaque ports. It
does not claim that migrating an arbitrary legacy `Problem` carrier into a
`Content` role subtype is conservative. That stronger claim would fail for old
models whose carriers cannot be related by the required equivalence.

The model-expansion theorem concerns only the new `EKC` symbol defined by the
DF-10 conjunction. The projection theorem concerns only unbundling the chosen
role and endpoint witnesses while preserving their evidence. Neither theorem
establishes contextual problemhood, critical-lineage identity, complete DF-7a
semantics, or authoritative TH-3.
