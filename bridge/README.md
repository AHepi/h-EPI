# Executable interpretation bridge

CR-EIB is a versioned, non-authoritative interpretation layer. It cannot modify what the CR-1.0 PDF says.

The current pilot contains four candidate declarations. Declaration formats
are intentionally mixed-version: the legacy DF-10 record and the two TH-3
pilot records remain v1, while the separately identified role-refined DF-10
record uses v2 so interpretation choices and fidelity obligations are
machine-visible. The refined record is a parallel candidate, not a mutation or
silent replacement of the legacy declaration.

| Bridge declaration | Source anchor | What is checked |
|---|---|---|
| `EIB-DF10-CANDIDATE` | `DF-10` | The preserved legacy conjunction over the independent `Problem` carrier |
| `EIB-DF10-REFINED-CANDIDATE` | `DF-10` | A role-refined conjunction with an explicit interval-endpoint witness, surface projection, and relative model-expansion certificate |
| `EIB-TH3A-PILOT` | `TH-3` | Definitional unfolding of the legacy `EIB-DF10-CANDIDATE` body |
| `EIB-TH3B-PILOT` | `TH-3` | A finite typed countermodel to uniform sufficiency for the legacy candidate |

All source inferential statuses remain `null`. `DEF` and `DER` are proposed
bridge statuses only. Every formal parameter is explicit. The v2 refined DF-10
record preserves dependent binder order and resolves every referenced bridge
choice through `bridge/choices/interpretation-choices.json`.

The role-refined DF-10 ports are explicit fields of `DF10OpaquePorts`; the
endpoint relation remains an explicit `CRModel` field. `ProblemContent`
membership is only bridge sort eligibility. It does not establish contextual
problemhood, representation, or system-level causal use. The projection keeps
both `I` and the selected `t_I` with endpoint evidence. It assumes neither a
total endpoint function nor endpoint uniqueness.

The model-expansion certificate applies only to adding `EKC` over a fixed
role-refined opaque-port base. It is not a conservativity certificate for
turning the legacy independent `Problem` carrier into a Content subtype.

Both TH-3 declaration records depend on the legacy identity
`EIB-DF10-CANDIDATE`, matching their unchanged Lean bodies. They do not silently
retarget to `EIB-DF10-REFINED-CANDIDATE`. The refined countermodel lift is an
auxiliary checked result until a separately identified refined TH-3 declaration
is designed and recorded.

The TH-3b logical witness uses an explicit false interpretation for `K_E`;
separately, application evidence must contain an accepted explicit negative
before the evidence resolver supports a witness. Unavailable evidence resolves
to `blocked`, never false.

The Lean replay is valid relative to the declared unconstrained ports. It
establishes formal validity of the recorded bridge propositions, not semantic
fidelity of the translation. The refined DF-10 mapping remains a candidate with
partial coverage, blocked bridge status, and unreviewed fidelity. CR-EIB
conformance remains blocked until the source meanings, mapping review, and
dependency closure are complete and accepted.

The Draft 2020-12 schemas enforce record shape. `creib.verify` additionally
enforces cross-record identity, exact pilot metadata, choice resolution,
artifact hashes, obligation kinds, dependency resolution, acyclicity, and
evidence policy. Its report keeps operational replay, mapping fidelity, and
bridge conformance separate; tests validate every committed instance through
both layers.
