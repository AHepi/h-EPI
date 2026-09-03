# Human-triage lineage

This directory is the append-only publication boundary for active plural human triage. A triage JSON elsewhere is a draft, even when its schema and content-addressed ID are valid. It acquires workflow authority only by no-clobber publication here and explicit selection of the verified terminal head.

## Records and heads

- A record is named `HT-<64 lowercase hex>.json`, exactly matching its `triage_id`, and contains canonical JSON plus one newline.
- `NEXT-GENESIS.claim` reserves the first record. Each later `NEXT-<parent digest>.claim` reserves that parent for one successor.
- A plan selects one terminal record using `--head-triage-id`. Directory order, modification time, a copied filename, or an unselected loose record never chooses the head.
- Planning with no head is permitted only when this directory has no triage record or successor claim. Once a genesis is published, omitting the head fails closed.
- Verification rejects forks, cycles, gaps, orphan records, extra claims, changed claim bytes, nonterminal selections, and noncanonical files.

## Additive successors

A genesis record has `sequence: 1`, `previous_triage_id: null`, and `transition_kind: GENESIS`. Every successor increments the sequence, names the selected parent, and retains every predecessor `locus_assessment` and `assessment_disposition` byte-for-byte. It may add assessments, append at most one new disposition per pre-existing assessment, and select, clear, or replace the singular scheduling action. Assessments are never rewritten or deleted. A fallible human may append an evidence-bound `RETAINED`, `DEFEATED`, or `STALE_BY_BINDING_CHANGE` workflow disposition; none confirms the model or supplies a model-level verdict.

Use `transition_kind: SAME_BINDINGS` when the complete inquiry binding is unchanged. Use `INPUT_BINDING_CHANGED` when the run, candidate, challenge, fixture, evaluator, observation, issue, warrant, or research-ledger snapshot changes. A binding-change successor must preserve the authority identity and logical research-ledger identity, retain all earlier assessments and dispositions, explain the transition, and set `next_action: null` so a human explicitly reschedules work for the new context. Earlier dispositions remain history but have no operational effect under different bindings; only exact staleness dispositions may be added in the binding-change successor. Silent rebinding and action carryover fail closed.

The planner derives a canonical menu of exact rival-falsifier attack targets from the current issue and warrant. This menu helps the reviewer identify possible external attacks but grants no authority by itself. An external `next_action` must select a nonempty subset of those exact target IDs; any missing, altered, or unavailable target fails publication. Non-external actions carry no research target.

Publish with `tools/run_semantic_inquiry.py publish-triage`, then use the returned `triage_id` as the plan's `--head-triage-id`.

Do not hand-edit published records or claims. Choosing work is never itself evidence of defeat. A same-binding disposition must follow an earlier frontier-valid action selecting that assessment and must bind a validated calibration-record value; staleness must bind the complete exact input delta. Terminal prerequisite dispositions unlock scheduling dependencies, while `RETAINED` keeps or reopens a criticism. Exclusive v1 triage remains read-only historical evidence and cannot enter, start, or extend this active lineage.
