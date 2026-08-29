# Lean pilot

This package checks a deliberately narrow, non-authoritative interpretation of CR-1.0 clauses DF-10 and TH-3. It proves fold/unfold and a finite typed countermodel relative to an unconstrained port signature. It does not prove or refute the authoritative PDF theorem until the complete dependency mappings are accepted.

The countermodel assigns `K_E` explicit falsity. Missing or unavailable evidence is not represented as falsity.

Run:

```sh
cd formal
lake build
```

The root module imports the axiom audit. The expected axiom list for every pilot result is empty.
