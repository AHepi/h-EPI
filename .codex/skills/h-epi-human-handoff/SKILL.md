---
name: h-epi-human-handoff
description: Explain h-EPI semantic-model findings, choices, research gates, status, and next steps in plain language while preserving plural criticism, unresolved status, and non-inductive limits.
---

# h-EPI human handoff

Use this skill when explaining h-EPI/CR-EIB work to a person: especially a test failure, a choice among failure loci, a research decision, a status report, or a next-step handoff. Use the formal project records for exact facts; this skill governs their explanation, not their truth.

## Preserve the important distinction

A failed expected result criticizes the tested conjunction. If the observation and the inference to failure are retained, the conjunction cannot remain intact; that still does not identify exactly one culprit. When candidate semantics, auxiliaries, tests, and scope can all remain live:

- present them as compatible criticisms, not an exclusive menu;
- say what each criticism would mean in ordinary language;
- distinguish the live diagnosis set from the one work action selected now;
- explain that choosing an action schedules work and neither defeats the other criticisms nor ranks semantic truth.

Use exclusive wording only when a separately reviewed, evidence-bound human judgment records a scoped exclusion; still describe that judgment as fallible.

When an assessment has a disposition, translate it precisely:

- `DEFEATED` means the reviewer records that evidence answers the exact criticism for the exact bound inputs and scope; it does not confirm the model or clear another criticism;
- `STALE_BY_BINDING_CHANGE` means the reviewer records that an exact input change made that criticism inapplicable in the new case; it was not refuted;
- `RETAINED` means the reviewer records that the criticism remains live, including when later evidence reopens an earlier disposition.

Mention the exact bound calibration observation at its declared observation pointer, or the exact input-binding delta, that bears on the discriminator. A disposition is a fallible human workflow judgment: its content-addressed envelope proves which bytes and pointer were cited, but it does not prove the reviewer's statement about what that evidence means. It never follows automatically from a pass, source count, agreement, or failed search; a relevant test result can be evidence only with an explicit human statement of how it bears on the discriminator. If no assessment is effective-live because each has a current-binding terminal `DEFEATED` or `STALE_BY_BINDING_CHANGE` disposition, say “the present criticism set needs human reassessment,” never “the model is confirmed.”

Keep question events distinct from assessment dispositions. `HUMAN_CRITICISM_RETAINED` retires one research question into internal integration; assessment `RETAINED` keeps or reopens a criticism. Question `STALE_BY_MODEL_CHANGE` closes one old question; assessment `STALE_BY_BINDING_CHANGE` is a separate human judgment about one criticism.

## Explain decisions from the reader's point of view

Lead with the practical outcome. Then supply only the reasoning needed to evaluate it:

1. What changed or what remains blocked.
2. Why that follows, using concrete nouns and the smallest faithful logical statement.
3. What action is authorized now, why it comes first, and which alternatives remain live.
4. What observation would change the decision.

Translate a formal label the first time it matters. Prefer “the test may be asking the wrong question” followed by `(TEST)` over an unexplained code. Do not make the reader reconstruct a conclusion from hashes, filenames, or tool output; place those details after the human meaning when they are needed for verification.

## Make the research gate explicit

When research is considered, state:

- the exact unresolved question;
- whether it can be attacked internally, in the CR authority, or only with an external critical instrument;
- the specific rival or falsifier to seek;
- what a result could criticize;
- that no result, repeated agreement, source count, or failure to find a result confirms the model.

Before authorization, describe AlphaXiv only as the user's preferred contingent route if external research becomes warranted. Once an exact external target is authorized, it may be described as the active contemporary discovery route. Treat discovery output as a route to inspectable primary material, never as an oracle.

## Give usable next steps

Use a short ordered list when order matters. When recommending or explaining an order, give an explicit operational reason such as an upstream dependency, shared work across several criticisms, reversibility, or the user's stated priority; distinguish your recommendation from the human action actually published. A dependency is work order, not evidential support: it becomes traversable only after every prerequisite has an exact, current-binding terminal human disposition. Keep every unaddressed live criticism visible. State blockers and deliberate limitations directly.

For publication handoffs, report the branch and commit, the meaningful verification outcome, what remains unresolved, and the next human decision. Do not equate passing tests, formal consistency, or successful publication with semantic confirmation.

Explain publication integrity without implementation jargon unless it matters: a durable claim reserves one exact append-only successor, an interrupted claim-only write may be retried only for that byte-identical candidate after contextual revalidation, and conflicting or record-only states fail closed. Distinguish intrinsic checks from contextual assurance. Intrinsic plan validation can require a syntactically compatible event-head reference; only contextual regeneration proves that the head exists and that the complete event lineage replays to it. If a source report appears both in an event and in the bound research ledger, explain that both surfaces share the `entry_id` namespace: the same ID must mean the exact same complete report.
