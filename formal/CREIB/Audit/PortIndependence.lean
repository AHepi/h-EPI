import CREIB.Pilot.TH3Countermodel

set_option autoImplicit false
set_option warningAsError true

namespace CREIB
namespace Audit

/--
Audit-only negative control for the legacy TH-3B pilot. If `K_E` is identified
with `Retained` at every typed argument tuple, then `CCPResult ∧ Retained`
entails the candidate DF-10 body. The relative countermodel requires permitting
`Retained` without `K_E`; this conflation would rule that out. This is not a
source mapping or a release declaration.
-/
theorem keRetainedConflationEntailsCandidate
    (M : CRModel)
    (hConflated :
      ∀ (s : M.Sys)
        (x : M.Content)
        (p : M.Problem)
        (b : M.Background)
        (history : M.Hist)
        (time : M.Time),
        M.K_E x p b history time ↔ M.Retained s x history time) :
    ∀ (s : M.Sys)
      (x : M.Content)
      (p : M.Problem)
      (b : M.Background)
      (history : M.Hist)
      (ctx : IntervalContext M),
      (M.CCPResult s x p b history ctx.interval ∧
        M.Retained s x history ctx.endTime) →
        EIB_DF10_CANDIDATE M s x p b history ctx := by
  intro s x p b history ctx premises
  exact
    ⟨premises.1,
     (hConflated s x p b history ctx.endTime).2 premises.2,
     premises.2⟩

end Audit
end CREIB
