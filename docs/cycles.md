# Cycles: what a further pass changes, read beside the repeat floor

*Written after the five-model cycles run on the travel-claim pilot. Every observation id below is the file `observation.<id>.json` under `forge/conformance/runs/travel-claim-cycles/`; every conjecture id is in the pilot's `claims.json`, committed as `bda06bf` before any cycle record existed.*

## The question, and the form it can be put in

Whether giving a model more cycles improves its answers is a general, positive claim about models, and this harness cannot make one: its report never computes accuracy and no finite set of records confirms anything. What it can do is put the question as conjectures that one record breaks, run them, and say what survived, beside the one thing any cycle experiment has to clear first: the run's own repeat floor, the moves a byte-identical request makes with nothing asked to change.

The CYCLE family (`docs/how-it-works.md`, "Cycles, beside the repeat floor") asks the question in two forms:

- **Self-revision** (criticism `none`). The model is shown its previous answer after the document and asked to check it against the instructions, the schema, and the document, and to return the complete form again. Nothing else is added. This is the model as its own critic, the design the reviews under `docs/reviews/` call a self-confirming check.
- **External criticism** (criticism `external`). The same, with the failed checks of the previous answer listed by field: a missing required key, an extra key, a type, pattern, enum, or length violation, a span that is missing, absent from the document, or not containing its value. These come from the form schema and the document alone. `MISMATCH` and `UNEXPECTED_PRESENT` come from the answer key and are excluded in code, in the record schema, and by a test. Where no such check failed, the cycle says so.

Three cycles follow each of the nine ordinary cases per source, so a chain is baseline, cycle 1, cycle 2, cycle 3; each cycle is scored against the case's own oracle and compared with the step it follows. The same run repeats each baseline twice (REPEAT), which is the floor.

## Conjectures written before the run

| Id | Says, in the never form | Floor |
|---|---|---|
| CYC-01 | A cycle never turns a matched field into a miss when no criticism named it | CYC-09 |
| CYC-02 | Self-revision never turns a missed field into a match | CYC-10 |
| CYC-03 | External criticism never turns a missed field into a match | CYC-10 |
| CYC-04 | Self-revision never changes the answer | STAB-01 |
| CYC-05 | Told nothing failed, the model never changes the answer | |
| CYC-06 | A field the criticism named is never left unchanged | |
| CYC-07 | A named schema check never fails on the same field afterwards | |
| CYC-08 | A named grounding check never fails on the same field afterwards | |
| CYC-09 | A repeat never turns a matched field into a miss | the floor |
| CYC-10 | A repeat never turns a missed field into a match | the floor |
| CYC-11 | A later cycle never changes an answer the cycle before left unchanged | |
| CYC-12 | A cycle never returns something other than a JSON object | |
| CYC-13 | A cycle never withdraws a stated return date to null | |
| CYC-14 | Self-revision never moves the claimed total onto the key | CYC-10 |

CYC-09 and CYC-10 were already refuted by the round-three records when the file was committed (four and eight refuting repeats): the floor predicate fires on records that exist, which is what a pre-registered floor is for.

## What the run showed

The five-model run was still completing when this design section was committed; the results, the cycles table beside the repeat floor, and the conjectures' outcomes follow in the commit that carries the run's records.
