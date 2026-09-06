# Appraisal labelling: completion instructions

Read the dossier and complete the form.

1. Output a single JSON object containing exactly the keys defined by the form schema, and no other text.
2. The dossier describes six arguments, A1 to A6, each with a readiness of PASS, FAIL, or UNKNOWN, the arguments it depends on essentially, and the arguments it attacks.
3. An argument is in when its readiness is PASS, every argument it depends on is in, and every argument that attacks it is out.
4. An argument is out when its readiness is FAIL, or an argument it depends on is out, or an argument that attacks it is in.
5. Labels are found by applying sentences 3 and 4 together, over and over, starting with no argument in and no argument out, until nothing changes; an argument that is then neither in nor out is undecided.
6. `label_a1` is the label of A1: in, out, or undecided.
7. `label_a2` is the label of A2: in, out, or undecided.
8. `label_a3` is the label of A3: in, out, or undecided.
9. `label_a4` is the label of A4: in, out, or undecided.
10. `label_a5` is the label of A5: in, out, or undecided.
11. `label_a6` is the label of A6: in, out, or undecided.
12. `usable_count` is the number of the six arguments whose label is in, as an integer.
13. `raw_summary` is NO_CASE when no case is attached to any argument, POSITIVE_CASE_ONLY when every attached case is positive, NEGATIVE_CASE_ONLY when every attached case is negative, and BOTH_CASES when positive and negative cases are both attached.
14. `usable_summary` is the same description restricted to the cases attached to arguments whose label is in.
