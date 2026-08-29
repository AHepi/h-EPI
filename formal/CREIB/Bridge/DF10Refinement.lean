import CREIB.Bridge.DF10Candidate
import CREIB.Core.RoleRefinement

set_option autoImplicit false
set_option warningAsError true

namespace CREIB

/--
The three opaque ports needed by the role-refined DF-10 bridge.  In contrast to
the legacy pilot signature, the problem argument is a Content carrying
problem-sort eligibility evidence.  The fields remain uninterpreted semantic
ports; this structure adds no source axioms.
-/
structure DF10OpaquePorts
    (M : CRModel)
    (roles : ContentRoleRefinement M) where
  CCPResult :
    M.Sys → M.Content → ProblemContent M roles → M.Background → M.Hist →
      M.Interval → Prop
  K_E :
    M.Content → ProblemContent M roles → M.Background → M.Hist → M.Time → Prop
  Retained : M.Sys → M.Content → M.Hist → M.Time → Prop

/--
An explicit, user-supplied transport from the refined problem sort to the
legacy pilot's independent `Problem` carrier.  Such a transport is not
derivable from `CRModel`, so no conservativity or source-fidelity claim is made
for it.
-/
structure LegacyProblemTransport
    (M : CRModel)
    (roles : ContentRoleRefinement M) where
  toLegacyProblem : ProblemContent M roles → M.Problem

namespace DF10OpaquePorts

/-- Lift the legacy opaque ports along an explicitly supplied problem map. -/
def fromLegacy
    (M : CRModel)
    (roles : ContentRoleRefinement M)
    (transport : LegacyProblemTransport M roles) : DF10OpaquePorts M roles where
  CCPResult :=
    fun s x p b h interval =>
      M.CCPResult s x (transport.toLegacyProblem p) b h interval
  K_E :=
    fun x p b h time =>
      M.K_E x (transport.toLegacyProblem p) b h time
  Retained := M.Retained

end DF10OpaquePorts

/--
The source-shaped conjunction at a selected interval and time, relative to the
refined opaque ports.  This surface form alone does not assert that `endTime`
is an endpoint; the witnessed form below supplies that coverage explicitly.
-/
def EIB_DF10_REFINED_SURFACE
    (M : CRModel)
    (roles : ContentRoleRefinement M)
    (ports : DF10OpaquePorts M roles)
    (s : M.Sys)
    (x : M.Content)
    (p : ProblemContent M roles)
    (b : M.Background)
    (h : M.Hist)
    (interval : M.Interval)
    (endTime : M.Time) : Prop :=
  ports.CCPResult s x p b h interval ∧
    ports.K_E x p b h endTime ∧
    ports.Retained s x h endTime

/--
Role-refined DF-10 candidate over an interval with an explicitly witnessed
endpoint.  This remains definition-relative to opaque ports and does not by
itself establish acceptance of the source mapping.
-/
def EIB_DF10_REFINED
    (M : CRModel)
    (roles : ContentRoleRefinement M)
    (ports : DF10OpaquePorts M roles)
    (s : M.Sys)
    (x : M.Content)
    (p : ProblemContent M roles)
    (b : M.Background)
    (h : M.Hist)
    (interval : M.Interval)
    (endpoint : EndTimeWitness M interval) : Prop :=
  EIB_DF10_REFINED_SURFACE
    M roles ports s x p b h interval endpoint.1

theorem EIB_DF10_refined_fold_unfold
    (M : CRModel)
    (roles : ContentRoleRefinement M)
    (ports : DF10OpaquePorts M roles)
    (s : M.Sys)
    (x : M.Content)
    (p : ProblemContent M roles)
    (b : M.Background)
    (h : M.Hist)
    (interval : M.Interval)
    (endpoint : EndTimeWitness M interval) :
    EIB_DF10_REFINED M roles ports s x p b h interval endpoint ↔
      ports.CCPResult s x p b h interval ∧
        ports.K_E x p b h endpoint.1 ∧
        ports.Retained s x h endpoint.1 :=
  Iff.rfl

/--
Projection from the witness-indexed target back to the source-shaped surface
on the declared coverage: a caller has supplied an admitted endpoint witness.
-/
theorem EIB_DF10_refined_projection
    (M : CRModel)
    (roles : ContentRoleRefinement M)
    (ports : DF10OpaquePorts M roles)
    (s : M.Sys)
    (x : M.Content)
    (p : ProblemContent M roles)
    (b : M.Background)
    (h : M.Hist)
    (interval : M.Interval)
    (endpoint : EndTimeWitness M interval) :
    EIB_DF10_REFINED M roles ports s x p b h interval endpoint ↔
      EIB_DF10_REFINED_SURFACE
        M roles ports s x p b h interval endpoint.1 :=
  Iff.rfl

/--
Compatibility with the legacy candidate after, and only after, an explicit
problem-carrier transport has been supplied.
-/
theorem EIB_DF10_refined_legacy_transport
    (M : CRModel)
    (roles : ContentRoleRefinement M)
    (transport : LegacyProblemTransport M roles)
    (s : M.Sys)
    (x : M.Content)
    (p : ProblemContent M roles)
    (b : M.Background)
    (h : M.Hist)
    (ctx : IntervalContext M) :
    EIB_DF10_REFINED
        M roles (DF10OpaquePorts.fromLegacy M roles transport)
        s x p b h ctx.interval ctx.endTimeWitness ↔
      EIB_DF10_CANDIDATE
        M s x (transport.toLegacyProblem p) b h ctx :=
  Iff.rfl

/--
An expansion of a fixed role-refined opaque-port base by a new EKC predicate
and its defining equation.  The base is retained as a field so reduct identity
can be stated and kernel-checked explicitly.
-/
structure DF10EKCExpansion
    (M : CRModel)
    (roles : ContentRoleRefinement M) where
  base : DF10OpaquePorts M roles
  EKC :
    (s : M.Sys) →
    (x : M.Content) →
    ProblemContent M roles →
    M.Background →
    M.Hist →
    (interval : M.Interval) →
    EndTimeWitness M interval → Prop
  definingEquation :
    ∀ (s : M.Sys)
      (x : M.Content)
      (p : ProblemContent M roles)
      (b : M.Background)
      (h : M.Hist)
      (interval : M.Interval)
      (endpoint : EndTimeWitness M interval),
      EKC s x p b h interval endpoint ↔
        EIB_DF10_REFINED M roles base s x p b h interval endpoint

/-- The definitional EKC expansion of any fixed refined opaque-port base. -/
def canonicalDF10EKCExpansion
    (M : CRModel)
    (roles : ContentRoleRefinement M)
    (base : DF10OpaquePorts M roles) : DF10EKCExpansion M roles where
  base := base
  EKC := EIB_DF10_REFINED M roles base
  definingEquation := by
    intro s x p b h interval endpoint
    exact Iff.rfl

/-- The canonical expansion has exactly the supplied old-vocabulary reduct. -/
theorem EIB_DF10_canonical_reduct
    (M : CRModel)
    (roles : ContentRoleRefinement M)
    (base : DF10OpaquePorts M roles) :
    (canonicalDF10EKCExpansion M roles base).base = base :=
  rfl

/--
Relative model-expansion obligation for the new EKC definition: every fixed
role-refined opaque-port base has an expansion satisfying the equation while
its old-vocabulary reduct is unchanged.
-/
theorem EIB_DF10_canonical_model_expansion_exists
    (M : CRModel)
    (roles : ContentRoleRefinement M)
    (base : DF10OpaquePorts M roles) :
    ∃ expanded : DF10EKCExpansion M roles,
      expanded.base = base ∧
        ∀ (s : M.Sys)
          (x : M.Content)
          (p : ProblemContent M roles)
          (b : M.Background)
          (h : M.Hist)
          (interval : M.Interval)
          (endpoint : EndTimeWitness M interval),
          expanded.EKC s x p b h interval endpoint ↔
            EIB_DF10_REFINED M roles base s x p b h interval endpoint := by
  exact ⟨canonicalDF10EKCExpansion M roles base, rfl, by
    intro s x p b h interval endpoint
    exact Iff.rfl⟩

end CREIB
