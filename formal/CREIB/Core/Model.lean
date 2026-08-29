set_option autoImplicit false
set_option warningAsError true

namespace CREIB

/--
The minimal typed port signature used by the pilot. Predicate fields are supplied
by a model; this file does not assert their CR-1.0 meanings.
-/
structure CRModel where
  Sys : Type
  Content : Type
  Problem : Type
  Background : Type
  Hist : Type
  Time : Type
  Interval : Type

  /-- Relational so the bridge assumes neither endpoint totality nor uniqueness. -/
  Endpoint : Interval → Time → Prop

  CCPResult :
    Sys → Content → Problem → Background → Hist → Interval → Prop
  K_E :
    Content → Problem → Background → Hist → Time → Prop
  Retained :
    Sys → Content → Hist → Time → Prop

/-- An explicit interval, endpoint time, and witness connecting the two. -/
structure IntervalContext (M : CRModel) where
  interval : M.Interval
  endTime : M.Time
  endpointProof : M.Endpoint interval endTime

end CREIB
