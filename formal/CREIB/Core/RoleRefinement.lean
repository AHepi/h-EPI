import CREIB.Core.Model

set_option autoImplicit false
set_option genInjectivity false
set_option warningAsError true

namespace CREIB

/--
Bridge-level names for the four Content roles described by CR-1.0.  These are
role indices, not disjoint replacement carriers.
-/
inductive ContentRole where
  | problem
  | attemptedExplanation
  | criticism
  | standard
deriving DecidableEq, Repr

/--
An additive refinement of a legacy `CRModel.Content` carrier by bridge sort
eligibility.  `RoleEligible x r` means only that `x` may inhabit the bridge
sort indexed by `r`.  It does not assert that `x` satisfies that semantic role
in every episode, history, problem situation, or other context.

No disjointness, exhaustiveness, or inhabitance condition is imposed.
-/
structure ContentRoleRefinement (M : CRModel) where
  RoleEligible : M.Content → ContentRole → Prop

/-- A Content value paired with bridge sort-eligibility evidence for `role`. -/
abbrev RoleContent
    (M : CRModel)
    (roles : ContentRoleRefinement M)
    (role : ContentRole) : Type :=
  { x : M.Content // roles.RoleEligible x role }

abbrev ProblemContent (M : CRModel) (roles : ContentRoleRefinement M) : Type :=
  RoleContent M roles .problem

abbrev AttemptExplanationContent
    (M : CRModel)
    (roles : ContentRoleRefinement M) : Type :=
  RoleContent M roles .attemptedExplanation

abbrev CriticismContent (M : CRModel) (roles : ContentRoleRefinement M) : Type :=
  RoleContent M roles .criticism

abbrev StandardContent (M : CRModel) (roles : ContentRoleRefinement M) : Type :=
  RoleContent M roles .standard

namespace ContentRoleRefinement

/--
The freely available refinement in which every legacy Content is eligible for
every bridge sort.  This witnesses additive extensibility only; it is not a
source-fidelity claim about which roles any Content semantically satisfies.
-/
def unrestricted (M : CRModel) : ContentRoleRefinement M where
  RoleEligible := fun _ _ => True

end ContentRoleRefinement

/-- The unrestricted refinement permits one Content to inhabit several roles. -/
theorem unrestricted_role_overlap
    (M : CRModel)
    (x : M.Content) :
    ∃ (asProblem : ProblemContent M (ContentRoleRefinement.unrestricted M))
      (asCriticism : CriticismContent M (ContentRoleRefinement.unrestricted M)),
      asProblem.1 = asCriticism.1 := by
  exact ⟨⟨x, True.intro⟩, ⟨x, True.intro⟩, rfl⟩

/--
A selected endpoint time together with evidence that it is an endpoint of the
given interval.  This dependent alias neither chooses an endpoint for every
interval nor says that an endpoint is unique.
-/
abbrev EndTimeWitness (M : CRModel) (interval : M.Interval) : Type :=
  { endTime : M.Time // M.Endpoint interval endTime }

namespace IntervalContext

/-- Recover the dependent endpoint witness already carried by a context. -/
def endTimeWitness
    {M : CRModel}
    (ctx : IntervalContext M) : EndTimeWitness M ctx.interval :=
  ⟨ctx.endTime, ctx.endpointProof⟩

/-- Build an interval context from an explicitly supplied endpoint witness. -/
def ofEndTimeWitness
    {M : CRModel}
    (interval : M.Interval)
    (witness : EndTimeWitness M interval) : IntervalContext M where
  interval := interval
  endTime := witness.1
  endpointProof := witness.2

theorem ofEndTimeWitness_endTime
    {M : CRModel}
    (interval : M.Interval)
    (witness : EndTimeWitness M interval) :
    (ofEndTimeWitness interval witness).endTime = witness.1 :=
  rfl

end IntervalContext

end CREIB
