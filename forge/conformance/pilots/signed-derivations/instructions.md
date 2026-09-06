# Signed derivations: completion instructions

Read the dossier and complete the form.

1. Output a single JSON object containing exactly the keys defined by the form schema, and no other text.
2. The dossier states a target claim built from leaves with AND, OR, NOT, and the quantifiers ALL and SOME over the recorded members of a range R; a leaf may have a positive case on file, a negative case, both, or neither, and a case is on file only when the dossier says so.
3. A positive case for a conjunction needs a positive case for both conjuncts, and a negative case for a conjunction needs a negative case for at least one conjunct.
4. A positive case for a disjunction needs a positive case for at least one disjunct, and a negative case for a disjunction needs a negative case for both disjuncts.
5. A positive case for NOT F is a negative case for F, and a negative case for NOT F is a positive case for F.
6. A positive case for SOME x IN R needs one recorded member with a positive case for its instance, and a negative case for SOME x IN R needs the record to assert that the list of members is complete and a negative case for every member's instance.
7. A positive case for ALL x IN R needs the record to assert that the list of members is complete and a positive case for every member's instance, and a negative case for ALL x IN R needs one recorded member with a negative case for its instance.
8. A search that returned nothing supplies no case of either sign, and a leaf with no case on file supplies none.
9. Cases are derived only by sentences 3 to 7 from the cases on file; nothing else counts as a case.
10. `positive_derivable` is yes when a positive case for the target claim follows by those sentences and no otherwise.
11. `negative_derivable` is yes when a negative case for the target claim follows by those sentences and no otherwise.
12. `positive_blocked_by` is nothing when the positive case follows, range_not_complete when it would follow if the record asserted the list of members complete, and missing_leaf_case otherwise.
13. `negative_blocked_by` is nothing when the negative case follows, range_not_complete when it would follow if the record asserted the list of members complete, and missing_leaf_case otherwise.
14. `positive_conditional` is yes when the positive case follows and every way of deriving it uses a leaf that has both a positive and a negative case on file, and no otherwise.
15. `negative_conditional` is yes when the negative case follows and every way of deriving it uses a leaf that has both a positive and a negative case on file, and no otherwise.
16. `case_summary` is NO_CASE when neither case follows, POSITIVE_CASE_ONLY when only the positive case follows, NEGATIVE_CASE_ONLY when only the negative case follows, and BOTH_CASES when both follow.
