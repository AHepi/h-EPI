import CREIB.Pilot.TH3Countermodel

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

end CREIB
