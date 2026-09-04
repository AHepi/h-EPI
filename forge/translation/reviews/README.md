# Translation review lineage

This directory is the publication boundary for generic human translation
review. It intentionally contains no review genesis yet.

A translation snapshot is a content-addressed pre-review case. It binds the
source spans, translation charter, obligation graph, rival interpretation
sets, neutral model, declared model effects, imports, bridge, and unresolved
records. A snapshot is not accepted merely because it validates.

The review surface repeats each set's question, `rival_relation`, and exact
`admissible_branch_sets`, plus the complete content-addressed material for every
branch: its reading, source and obligation bindings, preserved features, model
effect, discriminators, falsifiers, and known loss risks. Every branch remains
independently admissible. An `EXCLUSIVE` set permits exactly its singletons; an
`OVERLAPPING` set must explicitly permit the full branch set; and a
`PARTIALLY_COMPATIBLE` set has at least three branches, permits at least one
proper plural subset, and forbids the full set. A scoped variant may select only
one of those declared combinations. Duplicate, absent, or unprojected branches
fail validation, as does any mismatch between the selected branches and their
model-effect closure.

Human review uses a separate append-only lineage:

- `BD:` records retain, exclude for scope, or mark stale one exact branch;
- `TD:` records explicitly authorize scoped use, reject the current set,
  suspend unresolved, or require reframing; and
- `TR:` records preserve the cumulative dispositions and decisions under one
  explicitly selected head.

Even one non-excluded branch is not selected automatically. Excluding every
known branch does not automatically reject the review case. Passing tests,
proof success, source counts, provider agreement, silence, and timeouts create
no human decision. A scoped-use decision neither confirms source meaning nor
accepts a project import.

The replayed workflow status has a deliberately narrow meaning:

- `AWAITING_HUMAN_REVIEW` means no decision under the current snapshot binding;
- `SCOPED_USE_SELECTED_AUTHENTICATION_REQUIRED` means a locally recorded
  `AUTHORIZE_SCOPED_USE` decision names one or more complete variants, but its
  reviewer identity has not been authenticated by the record;
- `REJECTED_FOR_SCOPE` means the current proposal set was explicitly rejected;
- `SUSPENDED_UNRESOLVED` means work is paused without a winner; and
- `REFRAME_REQUIRED` means the review question or alternatives need revision.

Every one of these remains epistemically `UNRESOLVED`: it is workflow state,
not a truth, interpretation, or model-confirmation verdict.

`reviewer_kind: HUMAN` and `machine_generated: false` are declarations, not
identity proof. Every v1 review, disposition, and decision therefore fixes
`reviewer_authentication: NOT_ESTABLISHED_BY_RECORD`. A pipeline must keep the
review stage unresolved—and must not admit hardening or promotion—until a
separate authenticated approval is exactly bound to the decision, review
head, scope, snapshot, and model.

Every translation decision contains a content-addressed `TRS:` scope binding:
the exact charter ID, declared purpose, system boundary, and nonempty in-scope
subset. Every authorized variant also names the exact `TNM:` model it targets.
Downstream orchestration must still compare the variant's selected branch set
with that model's current direct interpretation projection; the review record
does not infer that equality from prose.

Published files have the form `TR-<full-hash>.json`. Every record has one
claim-first reservation: `NEXT-GENESIS.claim` for genesis or
`NEXT-<parent-hash>.claim` for a successor. The claim and record contain the
same canonical JSON plus one newline and are hard links when publication
completes normally. A retry may roll forward only an exact claim-only
reservation after revalidating its parent and current translation snapshot.

A model, signature, bridge, or interpretation change within the same document,
charter, and obligation graph requires an explicit `INPUT_BINDING_CHANGED`
successor. That head carries no new translation decision, and every prior
authorization becomes inoperative under the new binding. It must add one exact
`STALE_BY_BINDING_CHANGE` disposition for every predecessor-surface branch;
partial coverage cannot silently leave an old branch review looking current.
The binding also persists the successor snapshot's predecessor ID, and every
interpretation-set surface persists its supersession ID. The new snapshot must
point to the immediately preceding review snapshot. Carried set IDs remain
unchanged, while each removed set ID must be named exactly once by a newly added
set; missing, duplicate, foreign, or carried-set replacement targets fail on
publication and replay. A decision cannot authorize a branch whose current
disposition is stale until a later exact `RETAINED_OPEN` record reopens it.
Changing the document
set, charter, or obligation graph changes the review subject and requires a new
lineage rather than a rollover.

No directory order or modification time selects a review. Every consumer must
name the terminal `TR:` head and the exact `TSN:` snapshot. Omitting the head is
valid only while the lineage is empty. Orphan records, sibling claims, forks,
changed historical content, and malformed or incomplete inventories fail
closed.

Use `tools/run_translation_review.py surface` to derive the exact review
surface, `publish` to publish an operator-supplied human record, and `verify`
to replay an explicitly selected head. Verification reports integrity and
workflow state only; semantic status remains `UNRESOLVED`.
