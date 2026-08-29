import CREIB.Core.Model

set_option autoImplicit false
set_option warningAsError true

namespace CREIB

/--
EIB-DF10-CANDIDATE. This is exact only relative to the three uninterpreted
semantic ports in `CRModel`; it is not yet an accepted transcription of DF-10.
-/
def EIB_DF10_CANDIDATE
    (M : CRModel)
    (s : M.Sys)
    (x : M.Content)
    (p : M.Problem)
    (b : M.Background)
    (h : M.Hist)
    (ctx : IntervalContext M) : Prop :=
  M.CCPResult s x p b h ctx.interval ∧
    M.K_E x p b h ctx.endTime ∧
    M.Retained s x h ctx.endTime

theorem EIB_DF10_fold_unfold
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
  Iff.rfl

end CREIB
