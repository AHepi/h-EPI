import CREIB.Pilot.TH3Refinement

set_option autoImplicit false
set_option warningAsError true

namespace CREIB

-- These typed aliases fail compilation if a declared symbol's proposition drifts.
example :
    ∀ (M : CRModel)
      (_s : M.Sys)
      (_x : M.Content)
      (_p : M.Problem)
      (_b : M.Background)
      (_h : M.Hist)
      (_ctx : IntervalContext M),
      Prop :=
  EIB_DF10_CANDIDATE

example
    (M : CRModel)
    (s : M.Sys)
    (x : M.Content)
    (p : M.Problem)
    (b : M.Background)
    (h : M.Hist)
    (ctx : IntervalContext M) :
    EIB_DF10_CANDIDATE M s x p b h ctx ↔
      M.CCPResult s x p b h ctx.interval ∧
        M.K_E x p b h ctx.endTime ∧
        M.Retained s x h ctx.endTime :=
  EIB_DF10_fold_unfold M s x p b h ctx

example :
    ∀ (M : CRModel)
      (s : M.Sys)
      (x : M.Content)
      (p : M.Problem)
      (b : M.Background)
      (h : M.Hist)
      (ctx : IntervalContext M),
      EIB_DF10_CANDIDATE M s x p b h ctx →
        M.CCPResult s x p b h ctx.interval ∧
          M.K_E x p b h ctx.endTime ∧
          M.Retained s x h ctx.endTime :=
  EIB_TH3a_unfold

example :
    ¬ (∀ (M : CRModel)
        (s : M.Sys)
        (x : M.Content)
        (p : M.Problem)
        (b : M.Background)
        (h : M.Hist)
        (ctx : IntervalContext M),
        (M.CCPResult s x p b h ctx.interval ∧
          M.Retained s x h ctx.endTime) →
          EIB_DF10_CANDIDATE M s x p b h ctx) :=
  EIB_TH3b_relative_non_sufficiency

-- The role index refines Content additively; it does not replace legacy CRModel.
example (M : CRModel) : ContentRoleRefinement M :=
  ContentRoleRefinement.unrestricted M

example
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
  EIB_DF10_refined_fold_unfold
    M roles ports s x p b h interval endpoint

example
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
  EIB_DF10_refined_projection M roles ports s x p b h interval endpoint

example
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
  EIB_DF10_refined_legacy_transport
    M roles transport s x p b h ctx

example
    (M : CRModel)
    (roles : ContentRoleRefinement M)
    (base : DF10OpaquePorts M roles) :
    (canonicalDF10EKCExpansion M roles base).base = base :=
  EIB_DF10_canonical_reduct M roles base

example
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
            EIB_DF10_REFINED M roles base s x p b h interval endpoint :=
  EIB_DF10_canonical_model_expansion_exists M roles base

example :
    ∃ (M : CRModel)
      (roles : ContentRoleRefinement M)
      (ports : DF10OpaquePorts M roles)
      (s : M.Sys)
      (x : M.Content)
      (p : ProblemContent M roles)
      (b : M.Background)
      (h : M.Hist)
      (interval : M.Interval)
      (endpoint : EndTimeWitness M interval),
      ports.CCPResult s x p b h interval ∧
        ports.Retained s x h endpoint.1 ∧
        ¬ ports.K_E x p b h endpoint.1 ∧
        ¬ EIB_DF10_REFINED
          M roles ports s x p b h interval endpoint :=
  EIB_TH3b_refined_countermodel_exists

example :
    ¬ (∀ (M : CRModel)
        (roles : ContentRoleRefinement M)
        (ports : DF10OpaquePorts M roles)
        (s : M.Sys)
        (x : M.Content)
        (p : ProblemContent M roles)
        (b : M.Background)
        (h : M.Hist)
        (interval : M.Interval)
        (endpoint : EndTimeWitness M interval),
        (ports.CCPResult s x p b h interval ∧
          ports.Retained s x h endpoint.1) →
          EIB_DF10_REFINED
            M roles ports s x p b h interval endpoint) :=
  EIB_TH3b_refined_relative_non_sufficiency

end CREIB
