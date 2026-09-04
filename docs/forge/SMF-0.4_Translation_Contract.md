# SMF-0.4 generic translation harness contract

## Purpose and claim boundary

This harness is meant to make a difficult semantic translation criticizable,
traceable, and hard to change silently. In human terms, it content-binds an
operator-supplied source and replays supported selections from those exact
bytes, makes every consequential reading and added premise visible, carries
those choices into a neutral model, maps the model back to what licensed it,
and asks targeted questions about every change. It does not archive an
external source merely by recording its digest.

It is fail-closed, not foolproof. It can prove operational facts such as byte
identity, record identity, closure completeness, and deterministic replay. It
can show that a proposed translation is traceable relative to its declared
choices. It cannot prove that all relevant source meaning has been noticed,
that one interpretation is uniquely correct, or that no future criticism will
succeed. A missing semantic judgment therefore remains `UNRESOLVED`; it is not
converted into a score, confidence value, consensus result, or default answer.

The governing non-inductive rule is:

> Surviving a criticism leaves a proposal unrefuted for the declared scope. It
> does not confirm, support, or make the proposal probable.

The words **MUST**, **MUST NOT**, and **SHOULD** below state the harness
contract. A stage may send work back to any earlier stage. Several mechanisms
may be live at once; the workflow schedules actions without deleting rival
criticisms.

## Three different things the harness can establish

| Result | What it establishes | What it does not establish |
|---|---|---|
| Operational integrity | Exact bytes, canonical records, content identities, references, inventories, and replay agree | Semantic faithfulness |
| Translation integrity | Every declared source obligation goes forward, every model element comes back, and losses or additions are explicit | That the declared obligations and readings are complete or correct |
| Scoped workflow disposition | A human has authorized, rejected, suspended, or reframed a precisely bound proposal for a stated use | Truth, unique source meaning, or acceptance of an added project premise as source authority |

Keeping these results separate is mandatory. Formal success, test survival,
review publication, and agreement between implementations MUST NOT be promoted
into semantic confirmation.

## Normative stages and gates

The thirteen gates below are conceptual requirements, not a one-to-one list of
runtime report keys. The controller exposes thirteen status slices:
`translation_integrity` aggregates the selected closure, project-import checks
are included in `neutral_model`, and review is displayed before test synthesis
and routing. Slice order is deterministic presentation only, not gate priority.

### Gate 1 — Content-bind the source before interpreting it

The harness MUST begin with a `TDOC:` source-document record bound to the exact
artifact digest and byte length. Each used passage MUST have a `TSPAN:` record.
A UTF-8 span may contain several byte ranges only in strictly increasing,
non-overlapping order; adjacent ranges are permitted and exact replay composes
them in ordinal order. V1 fails closed on multi-region PDF spans because it does
not yet bind a deterministic region-composition order. Context spans are
explicit. Literal extraction and reviewed transcription are recorded as
derived snapshots, not silently substituted for the authority.

The source gate closes only when operator-supplied external artifact bytes
match the bound document record and every selected locator can be replayed. A byte change,
different crop, changed normalization, or repaired transcription creates new
identity and a successor record. It MUST NOT rewrite the old source record.

### Gate 2 — State the job before extracting a model

The `TCHAR:` charter fixes the question being answered, the intended output,
the system boundary, what is in and out of scope, and the distinctions that
must not disappear. It also identifies either one sole semantic authority or
an explicit set of co-authorities. Advisory and contextual sources do not gain
authority by being numerous or recent.

The charter MUST retain the fail-closed constitution encoded by the v1 schema:
the output is a neutral semantic model; formalism cannot override valid prose;
test survival means only unrefuted; research serves criticism discovery;
ambiguity preserves rivals; missing mappings remain open losses; conflicts
remain visible for review; and a human semantic decision is required. The
charter itself remains a proposal.

### Gate 3 — Extract source obligations, including what remains open

The `TOG:` obligation graph separates a source-authority claim from the
translator's duty derived from it. Target and context spans are distinct. Each
target span MUST be covered by at least one obligation; where no responsible
claim can yet be made, the graph MUST record an `OPEN_RESIDUE` duty instead of
guessing.

Obligations protect terms, relations, identity conditions, quantifiers,
negations, modalities, scope, dependencies, qualifications, examples, and
exceptions. Typed edges record dependence, qualification, exclusion,
contrast, examples, exceptions, and scope. The dependency graph MUST be
acyclic. Every span selected by the snapshot MUST have exactly one `TARGET` or
`CONTEXT` graph binding; an extra content-bound but unclassified span is not
harmless context. An elegant later model does not license deletion of an
awkward source obligation.

### Gate 4 — Preserve rival interpretations before choosing among them

Every material interpretive question MUST have a `TIS:` interpretation set
with at least two distinct `TI:` branches. Each branch states its source spans,
interpreted obligations, preserved features, discriminating consequences,
possible falsifiers, known loss risks, and declared or still-unprojected model
effect. Exclusive, overlapping, and partly compatible rivals are all
representable.

A branch cannot borrow provenance from elsewhere in the graph: its spans MUST
cover the source-claim spans of every obligation it interprets, and every
feature it claims to preserve MUST belong to one of those obligations.

The set MUST also publish its exact `admissible_branch_sets`. Every branch
remains admissible by itself. An `EXCLUSIVE` set permits only those
singletons. An `OVERLAPPING` set explicitly permits the full set, as well as
any other compatible subsets the translator is prepared to defend. A
`PARTIALLY_COMPATIBLE` set has at least three branches, permits at least one
proper plural subset, and forbids the full set. The neutral model and every
scoped review variant may use only one of these declared combinations. Thus
the harness does not force a single reading when several mechanisms can apply,
but it also does not assume that every combination is coherent.

A branch is a `SOURCE_INTERPRETATION`, not source authority. The harness MUST
NOT select a branch because it is the only branch currently left, because most
sources or systems agree with it, or because its formalization passes. If a
serious rival cannot yet be stated, the stage remains open.

### Gate 5 — Name every premise the source did not supply

A `TIMP:` project-import record is required for every meaning-bearing causal,
epistemic, methodological, physical, or semantic premise that the source does
not entitle. An import MUST say that no source entitlement is claimed, state
its scope and motivation, preserve alternatives, expose its independence and
necessity as proposed claims with discriminators, name affected model
elements, and include a deletion-test prediction.

The declared affected keys MUST equal the signature members and model clauses
directly based on that import. Under-reporting and attaching unrelated elements
both invalidate the snapshot.

Imports can be useful and even necessary for the project. They MUST NOT be
smuggled into `SOURCE_AUTHORITY` or `SOURCE_INTERPRETATION`. Research may
criticize or replace an import, but cannot retroactively make it part of the
source.

### Gate 6 — Build a formalism-independent semantic interface

The `TNS:` neutral signature names the entities, roles, relations, properties,
events, processes, modalities, boundaries, and identity conditions required by
the proposal. Each meaning-bearing member cites interpretation or import
records. A purely structural member is marked `STRUCTURAL_SCAFFOLD` with no
semantic effect.

The `TNM:` neutral model supplies operative prose clauses, clause dependencies,
open ports, and a complete semantic dependency closure. Every clause states
which signature members it uses and whether its basis is source interpretation
or project import. Open ports keep unresolved questions connected to the
members and clauses they affect.

Member and clause `element_key` namespaces are globally disjoint. Every open
port affects at least one selected member or clause, and every interpretation
set containing an `UNPROJECTED` branch is covered by an open port. An unresolved
reading may therefore remain unmodeled, but it cannot become disconnected from
the model surface where its consequences must later be addressed.

V1 neutral models have `execution_semantics: NONE_V1`, remain `PROPOSED`, and
carry a null semantic verdict. They are an inspectable semantic interface, not
an executable theory and not a proof that prose has been captured.

### Gate 7 — Require a two-way bridge and freeze a snapshot

The `TBR:` bridge MUST contain exactly one forward mapping for every source
obligation and exactly one reverse mapping for every signature member and
model clause selected by the snapshot. A forward mapping says what model
elements represent an obligation and gives a back-translation. A reverse
mapping identifies the exact interpretation, project import, or structural
scaffold that licenses a model element. Its source-obligation IDs MUST equal
the direct forward incidence of that exact element; sharing an interpretation
branch does not smear every obligation in the branch across every element.

Each source `DEPENDS_ON` edge MUST be witnessed by a positive-length,
correctly directed model-clause dependency path from an element mapped from the
dependent obligation to one mapped from its prerequisite. A same element,
member use, reverse path, or prose assertion is not a witness. If that path is
absent or directionally mixed, v1 requires an exact open `DEPENDENCY_SHIFT`
over the two source endpoints and their complete mapped-element footprint,
attached only to the dependent obligation's forward mapping. Because the v1
delta itself has unordered endpoint sets and no directed witness path, its
direction is derived from that exclusive attachment and remains a format
limitation to remove in a successor schema.

Anything partial, absent, disputed, stronger, weaker, different, or unresolved
MUST create an open translation delta. Delta kinds include omission, addition,
strengthening, weakening, collapsed or split distinctions, and modal, scope,
identity, or dependency shifts. `CLAIMED_EXACT` and
`EQUIVALENT_CANDIDATE` mean only that exactness is being proposed; review is
still required.

The `TSN:` snapshot content-binds the source documents and spans, charter,
obligation graph, interpretation sets, imports, signature, model, bridge, and
unresolved inventory. Snapshot validation closes the record graph and checks
two-way coverage. It reports operational integrity with mapping fidelity still
`UNREVIEWED` and semantic verdict still null.

The implemented command-line checks are:

```sh
PYTHONPATH=src python tools/run_semantic_translation.py verify-source \
  --document-record /path/to/translation-source-document.json \
  --source /path/to/exact-authority-artifact

PYTHONPATH=src python tools/run_semantic_translation.py verify \
  --records-dir /path/to/translation-records \
  --snapshot /path/to/translation-snapshot.json

PYTHONPATH=src python tools/run_translation_harness.py \
  --records-dir /path/to/translation-records \
  --snapshot /path/to/translation-snapshot.json \
  --source-document TDOC:full-content-id=/path/to/exact-authority-artifact
```

`verify-source` checks raw artifact bytes against one document record, so that
command alone does not close all of Gate 1. `verify` schema-checks the selected
inventory and validates the snapshot's identities, closure, and two-way trace;
it does not access external source bytes or assign mapping fidelity.

The integrated harness command additionally replays every selected locator and
literal snapshot for the registered profiles. UTF-8 ranges use exact byte
offsets, strict decoding, item count, and a framed digest; a one-segment
verbatim claim can therefore be compared character for character. PDF regions
use a pinned `pdftotext` version, page count, page geometry, rotation, word
centres, order, count, and a canonical word-snapshot digest. That proves the
selected word snapshot, not exact character spacing or punctuation. A reviewed
transcription becomes character-level grounding only when its bytes replay and
its declared transformation list is empty against an exact character-level
selection. Unsupported profiles, unavailable tools, PDF transcription
relations, and descriptive locator metadata remain explicit limitations;
executable disagreement invalidates the source stage.

The PDF profile also invokes `pdfinfo` for page count, geometry, and rotation.
Its version is not recorded or pinned in v1, so PDF replay is not fully
toolchain-version-bound even though the `pdftotext` version is exact.

### Gate 8 — Generate adversarial questions from the exact change

For every supplied old/new snapshot delta, the deterministic test synthesizer
MUST retain all nine families:

1. deletion;
2. negation;
3. rival substitution;
4. semantic-role twins;
5. substrate swap;
6. boundary shift;
7. import dependency;
8. non-vacuity; and
9. round trip.

These are different attacks, not alternatives from which one winner is chosen.
Each family asks a different way in which a translation can look tidy while
losing meaning, changing strength, or becoming vacuous.

The current v1 synthesizer validates that the content-addressed delta names the
two snapshots and that the successor names its predecessor. It does not yet
derive the partitions, replacements, transports, or affected nested members
from both inventories. Those fields are caller declarations and remain a
separate unresolved criticism surface.

Given that declaration, the synthesizer deliberately emits nine
`DEFERRED_MISSING_SEMANTIC_BINDINGS` obligations. It binds the exact old and
new snapshots, delta, targets, question, and required semantic inputs, but it
does not invent an expectation, verdict, next action, failure locus, or
research authorization. A later executor may run a family only after the
declared semantics, held-fixed conditions, fixtures, comparators, and typed
expectation for that family have been supplied independently.

### Gate 9 — Triage failure loci and decide whether research is needed

An observation can reveal a criticism candidate; it cannot locate its own
cause. The stage-neutral inquiry record therefore allows `CANDIDATE`,
`AUXILIARY`, `TEST`, and `SCOPE` loci to remain live together. Each human locus
assessment names the mechanism, relevance, discriminator, scope, uncertainty
location, and any dependency on another assessment.

Research is warranted only when a live discriminator depends on information
or a critical instrument outside the content-bound authority and current project
records. Source wording goes to `AUTHORITY_REVIEW`; a translation or model
question goes to `INTERNAL_MODEL_WORK`; a harness or test defect goes to
`INTERNAL_HARNESS_WORK`; an external critical instrument or application fact
may go to `EXTERNAL_RESEARCH_REQUIRED`. An unlocated issue cannot be scheduled.

External research requires all of the following:

- an exact issue with genuine rivals and falsifier conditions;
- a bound research warrant and ledger state;
- a human-selected frontier assessment located externally; and
- an explicit subset of attack targets.

Research MUST search for criticism, discriminating evidence, and better
rivals. It MUST NOT use paper counts, recency, citation counts, provider
agreement, or model agreement as confirmation. Contemporary research services
are discovery surfaces, not semantic authorities. The current v3 inquiry
runtime normalizes explicit inputs and previews this route; it does not infer a
failure locus, perform retrieval, or publish a decision.

The integrated report derives a route row for every live assessment, including
whether it is selected, unselected on the dependency frontier, blocked by a
dependency, or still unlocated. The plan's singular route is reported
separately as the selected action route. An unscheduled independent route is
therefore visible without being treated as authorized.

### Gate 10 — Record human review as an append-only lineage

The review surface MUST reproduce the exact snapshot binding, source spans,
rival branches, and declared model effects. Human `BD:` branch dispositions
may retain a branch as open, exclude it for one scope, or mark it stale after
an input change. A separate human `TD:` translation decision may authorize
scoped use, reject the current set for scope, suspend unresolved, or reframe
the review problem. The cumulative `TR:` head binds both lineages.

Published review records are content-addressed, claim-first, no-clobber, and
append-only. A successor cannot drop or alter an earlier disposition or
decision. A changed model, signature, bridge, or interpretation binding within
the same document, charter, and obligation graph requires an explicit
`INPUT_BINDING_CHANGED` head; earlier authorization becomes inoperative and the
new binding must survive one decision-free review head before another decision.
Each review binding persists the selected snapshot's predecessor identity, and
each interpretation-set surface persists its supersession identity. On an
input-binding change, the new snapshot must name the preceding review's
snapshot as its immediate predecessor. Carried interpretation sets retain their
identities; every removed set must be superseded exactly once by a newly added
set. Missing, duplicate, foreign, or carried-set supersession targets fail both
publication and later review-only replay.
That head adds an exact `STALE_BY_BINDING_CHANGE` disposition for every branch
on the predecessor surface, with each disposition carrying the complete changed
binding-pointer set. Partial or zero staleness coverage is invalid.
A scoped authorization cannot select a branch whose current disposition is
`STALE_BY_BINDING_CHANGE`; a later exact `RETAINED_OPEN` disposition must reopen
that branch first. Branch state follows the content-addressed `TI:` identity,
not the pair of its `TIS:` container and branch ID. If a superseding set carries
an unchanged branch, the predecessor's stale disposition therefore remains its
head; the replacement set cannot make that branch appear fresh. A reopening
disposition under the replacement set must explicitly extend that same branch
chain through `previous_disposition_id`.
A different document set, charter, or obligation graph is a different review
subject and MUST start a new lineage. Consumers MUST name the selected terminal
head; directory order and modification time have no authority.

Even `AUTHORIZE_SCOPED_USE` is a fallible workflow permission. It does not
confirm a unique reading, accept a project import, promote the model, or assign
a semantic verdict. Authentication of the human reviewer is outside the v1
runtime.

That absence is an operational dependency, not only a publication caveat. The
integrated controller cannot promote the review slice to `READY`, and it blocks
its hardening slice on that review prerequisite. The standalone hardening
runtime can still validate a supplied comparison and report its limited
`NO_HARDENING` or `UNRESOLVED` outcome.

### Gate 11 — Test hardening without hiding lost strength

A claimed repair MUST be expressed as a comparison between exact baseline and
successor theory bindings. The `HC:` comparison freezes the target role, old
results and controls, declared scope, intended gain, protected positives,
exclusions and consequences, necessary clauses, imports, change inventory,
and currently live criticisms.

The hardening runtime derives conjunctive `HO:` obligations. Depending on the
comparison, they cover old-result and target-role non-broadening, successor
non-vacuity, scope and type/dependency preservation, the targeted gain,
registered positive/exclusion/consequence preservation, and independence of
claimed necessary clauses. Separate `HE:` records hold replayable mechanical
observations. Separate append-only `HD:` records capture fallible human
judgments about scope, protected material, gain relevance, change
classification, and import use. Human judgment cannot replace missing
mechanical evidence, and mechanical evidence cannot supply the human scope
decision.

Under the intended resolver contract, any replayed counterwitness or human
`DEFEATS_HARDENING` decision yields `NO_HARDENING`. Missing or inconclusive evidence, a missing human decision, an
effective live criticism, unavailable execution semantics, or the reserved
but unavailable proof checker yields `UNRESOLVED`. Only a fully witnessed
conjunction with every required scoped decision can yield
`HARDENING_UNREFUTED`, and only for the declared comparison. The resulting
`HR:` resolution is explicitly non-final and has no semantic verdict.

The v1 checker parses finite declarations but has no artifact resolver or model
executor. It therefore reports every caller-supplied finite payload as
`INCONCLUSIVE`; the positive status is reserved but currently unreachable. A
production `TNM:` model with `NONE_V1` execution semantics likewise cannot
receive a positive hardening result.
Equally important, the protection registry is itself criticizable: the harness
can prevent silent loss only for distinctions and consequences that were
actually declared or later exposed by tests.

### Gate 12 — Close the iteration lineage before calling the loop complete

An iterative harness needs more than individually valid stages. One
content-addressed, append-only lineage MUST bind the exact test execution to its
observation, the observation to plural inquiry, each human research
disposition to the resulting work, the authorized revision to a successor
snapshot, that successor to a derived old/new delta, and the replayed delta to
the hardening comparison. A revision cannot inherit evidence, review, or test
results merely because identifiers look familiar.

The v1 pipeline exposes this requirement as `iteration_lineage` with six
required edges. No record family implements those edges yet, so this stage is
always `UNRESOLVED` and the integrated controller cannot return `READY`. This
is a deliberate release boundary: the present parts can be inspected and used
separately, but the repository does not yet contain a foolproof or even fully
closed repair loop.

### Gate 13 — Qualify the harness on unlike and hostile specimens

Qualification requires both kinds of specimen because they answer different
questions.

The fictional Harbor Relay Charter, HRC-1, is the sensitivity specimen. Its
blind packet, controller key commitment, 17 source obligations, 31 isolated
mutations, three compound mutations, and six benign controls specify a test of
whether the harness exposes planted source, obligation, interpretation, model,
bridge, research, decision, test, and hardening defects without flagging every
change as damage. The committed runner does not perform that trial: it compares
a separately produced frozen report's exposure tokens with the controller
declarations. The comparison is conjunctive, so one missing or extra token
blocks `ALL_DECLARED_EXPOSURE_TOKENS_MATCH_CONTROLLER`.

The frozen Popper/CR-1.0 case is the restraint specimen. A fresh translation
must be produced without seeing the existing candidate and frozen before the
two are compared. Agreement is not validation; disagreement opens a
source-bound problem. Hostile mutations then test whether the harness exposes
omitted spans, source-free witnesses, definitions stronger than the source,
collapsed availability or endpoint distinctions, silent rival selection,
global-order imports, bridge retargeting, and promotion of formal replay into
fidelity. The required behavior is to preserve alternatives and stop
`UNRESOLVED`, not to guess Popper's intended meaning.

The committed HRC artifacts and executable qualifier implement the runner's
two-phase ordering: it verifies the candidate-snapshot and exposure-report
freezes before it loads controller records. It then compares the report's
declared `case_id::exposure_id` token sets with the controller declarations for
all 34 mutations and six benign controls. This proves neither that the producer
was denied controller access nor that any mutation was executed. Snapshot-only
qualification stops at
`CANDIDATE_FROZEN_AWAITING_DECLARED_EXPOSURES`; the current runtime does not
apply natural-language model mutations or infer exposure observations on its
own. The Popper hostile trial is likewise specified but not yet executed as a
fresh independent translation. Those omissions remain release blockers for a
claim of full harness qualification.

## When several mechanisms apply at once

The unit of scheduling is one action, not one allegedly true diagnosis. Live
criticisms remain plural. A single action may address several frontier
assessments only when their required work is genuinely shared and the action
records `SHARED_ACTION_FOR_MULTIPLE_LOCI`.

| Situation | Mechanisms that stay active together | What may be scheduled now | What MUST remain visible |
|---|---|---|---|
| A passage has two consequential readings | Source spans, obligation, rival interpretation set, model-effect comparison, authority review | Review the exact passage and discriminator | Both readings and their consequences |
| A model clause needs a premise absent from the source | Project import, reverse bridge, import-dependency and deletion tests, human import-use judgment | Expose and test the added premise | Its alternatives, scope, dependency, and lack of source entitlement |
| A failed test might indict the model, auxiliary assumptions, test, and scope | All four locus assessments plus their dependency graph | An upstream frontier action, or one shared action serving several frontier loci | Every unselected and downstream criticism |
| The discriminator needs an outside fact or instrument | Internal trace work plus the external research gate | Bounded research against named attack targets after exact warranting | Existing rivals; null semantic verdict; provider agreement cannot decide |
| A repair narrows a bad role assignment but may discard valid cases | Translation delta, dynamic tests, hardening obligations, protection review, non-vacuity check | Build missing mechanical evidence and scoped human decisions | Every protected case, consequence, import, and live criticism |
| Model, signature, bridge, or interpretation bytes change within one review subject | New content identities, snapshot, changed-binding head, bridge and test replay | First publish a decision-free changed-binding review head | The complete old lineage; prior authorization is inoperative |
| Document set, charter, or obligation graph changes | A new review subject and lineage | Start review from a new genesis | The old lineage remains immutable history; it does not authorize the new subject |
| Two criticisms need unrelated work routes | Both assessments remain live | Schedule one explicitly chosen frontier action at a time | The unscheduled criticism; no inferred ranking of truth |

## Readiness and publication are different decisions

| Label | Minimum meaning | Allowed consequence |
|---|---|---|
| `SOURCE_BYTES_VERIFIED` | Artifact bytes match one source-document record | Extract spans from those bytes |
| `TRANSLATION_INTEGRITY_VALID` | The selected record graph, closure, and two-way coverage validate | Present the proposal for criticism |
| `AWAITING_HUMAN_REVIEW` / `SUSPENDED_UNRESOLVED` | No scoped translation permission exists | Continue review, tests, or research |
| `SCOPED_USE_SELECTED_AUTHENTICATION_REQUIRED` | A recorded human declaration names variants under exact bindings, but v1 has not authenticated the reviewer | Obtain and bind external authentication before downstream use |
| `HARDENING_UNREFUTED` | Every declared finite-comparison obligation and human requirement is presently satisfied | Describe only the scoped hardening comparison as unrefuted |
| `ALL_DECLARED_EXPOSURE_TOKENS_MATCH_CONTROLLER` | A frozen HRC report's declared exposure-token sets exactly matched the controller declarations, with no missing or extra tokens | Claim only exact declaration matching against that fixture version; do not claim mutation execution, blindness, or semantic fidelity |
| Repository publication | Immutable records or code were written and shared | Audit and reproduce those bytes |

None of these labels permits `TRANSLATION_CORRECT`, `SEMANTICALLY_TRUE`, or
`PROVED_SEMANTICS`. Publishing bytes is not publishing semantic authority. A
model is ready for wider use only when its exact charter, unresolved items,
review head, test coverage, research ledger, hardening scope, and qualification
limits travel with it.

## Current implementation boundary

The repository now contains schemas for the source-to-snapshot records, an
intrinsic and cross-record translation validator, registered UTF-8-range and
PDF-word source replay, a claim-first append-only review lineage, the nine-family deferred test
synthesizer, stage-neutral inquiry v3 adapters and route preview, an isolated
hardening comparison/evidence/decision/resolution runtime, and the HRC-1
qualification artifacts and freeze-before-controller-load comparison runner. A
thin pipeline controller gives every supplied or missing capability a visible
status slice and preserves all applicable research routes without selecting
among them. Those slices are not one-to-one with the conceptual gates described
above. It also reports the missing closed-loop iteration lineage as a
first-class unresolved stage.

No runnable end-to-end generic translation instance is committed in this
tranche. There is no committed generic source-to-snapshot inventory, v3 inquiry
plan, review lineage, delta, hardening packet, or HRC candidate exposure report
and freeze. The validators and orchestration paths are exercised by tests;
operators must supply those content-bound records for an integrated run.

The following capabilities are not supplied by this tranche and MUST NOT be
implied by its presence:

- an automatic translator from arbitrary prose into a complete model;
- exact character-and-whitespace replay for PDF selections, executable
  transformations for reviewed transcriptions, or arbitrary extraction
  profiles beyond the two registered profiles;
- a pinned `pdfinfo` version for the PDF profile;
- an oracle that invents correct interpretations or semantic expectations;
- executable adapters for the nine dynamic test families;
- a delta derivation and replay engine over both complete snapshot inventories;
- an external research provider or retrieval adapter;
- authenticated human identity for review records;
- integrated hardening evaluation before that review authentication is bound;
- a proof-certified hardening checker;
- a bound finite-model artifact resolver or executor capable of producing
  witnessed or counterwitnessed hardening evidence;
- a typed append-only lineage closing test execution through revision and
  hardening replay;
- a completed blind HRC mutation run; or
- a completed independent Popper translation and hostile replay.

The practical design goal is therefore not an impossible guarantee against
every mistake. It is that no known loss, addition, ambiguity, failed criticism,
stale decision, or missing dependency can pass silently as a faithful and
finished translation.
