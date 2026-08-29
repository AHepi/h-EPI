# Lean pilot

This package checks a deliberately narrow, non-authoritative interpretation of CR-1.0 clauses DF-10 and TH-3. It proves fold/unfold and a finite typed countermodel relative to an unconstrained port signature. It does not prove or refute the authoritative PDF theorem until the complete dependency mappings are accepted.

The countermodel assigns `K_E` explicit falsity. Missing or unavailable evidence is not represented as falsity.

The additive refinement layer keeps the legacy pilot intact while introducing
overlapping Content role sorts through `RoleEligible`. Eligibility is only a
bridge typing judgment; it is not context-free semantic role satisfaction. An
`EndTimeWitness` packages a selected endpoint without assuming that all
intervals have one or that endpoints are unique.

`EIB_DF10_REFINED` projects definitionally to a source-shaped conjunction on
the explicit endpoint-witness coverage. The canonical EKC expansion theorem is
relative to a fixed role-refined opaque-port base and checks that its reduct is
unchanged. It is not a conservativity claim for migrating the legacy
independent `Problem` carrier, which requires an explicit transport, and it is
not acceptance of the CR-1.0 mapping.

The lifted singleton witness also yields
`EIB_TH3b_refined_relative_non_sufficiency`, a refined `¬ ∀` theorem matching
the logical shape of the legacy pilot. It remains relative to unconstrained
opaque ports and does not adjudicate source TH-3.

Run:

```sh
cd formal
lake build
```

The root module imports the axiom audit. The expected axiom list for every pilot result is empty.
