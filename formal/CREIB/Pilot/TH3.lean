import CREIB.Bridge.DF10Candidate

set_option autoImplicit false
set_option warningAsError true

namespace CREIB

/--
EIB-TH3A-PILOT: direct unfolding of the candidate DF-10 body. This result is
relative to the pilot signature and does not adjudicate source theorem TH-3.
-/
theorem EIB_TH3a_unfold
    (M : CRModel)
    (s : M.Sys)
    (x : M.Content)
    (p : M.Problem)
    (b : M.Background)
    (h : M.Hist)
    (ctx : IntervalContext M)
    (hEKC : EIB_DF10_CANDIDATE M s x p b h ctx) :
    M.CCPResult s x p b h ctx.interval ∧
      M.K_E x p b h ctx.endTime ∧
      M.Retained s x h ctx.endTime :=
  hEKC

end CREIB
