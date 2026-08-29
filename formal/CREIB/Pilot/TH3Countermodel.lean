import CREIB.Pilot.TH3

set_option autoImplicit false
set_option warningAsError true

namespace CREIB
namespace TH3Countermodel

-- Separate singleton carriers preserve the source-level sort distinctions.
inductive Sys where
  | only

inductive Content where
  | only

inductive Problem where
  | only

inductive Background where
  | only

inductive Hist where
  | only

inductive Time where
  | only

inductive Interval where
  | only

/-- An explicit interpretation; `K_E` is false, not absent or unknown. -/
def model : CRModel where
  Sys := Sys
  Content := Content
  Problem := Problem
  Background := Background
  Hist := Hist
  Time := Time
  Interval := Interval
  Endpoint := fun _ _ => True
  CCPResult := fun _ _ _ _ _ _ => True
  K_E := fun _ _ _ _ _ => False
  Retained := fun _ _ _ _ => True

def context : IntervalContext model where
  interval := Interval.only
  endTime := Time.only
  endpointProof := True.intro

theorem concreteWitness :
    model.CCPResult
        Sys.only Content.only Problem.only Background.only Hist.only
        context.interval ∧
      model.Retained Sys.only Content.only Hist.only context.endTime ∧
      ¬ model.K_E Content.only Problem.only Background.only Hist.only context.endTime ∧
      ¬ EIB_DF10_CANDIDATE
        model Sys.only Content.only Problem.only Background.only Hist.only
        context := by
  constructor
  · exact True.intro
  constructor
  · exact True.intro
  constructor
  · intro hKE
    exact hKE
  · intro hEKC
    exact hEKC.2.1

end TH3Countermodel

/-- A concrete typed model witnessing the pilot's relative non-sufficiency. -/
theorem EIB_TH3b_countermodel_exists :
    ∃ (M : CRModel)
      (s : M.Sys)
      (x : M.Content)
      (p : M.Problem)
      (b : M.Background)
      (h : M.Hist)
      (ctx : IntervalContext M),
      M.CCPResult s x p b h ctx.interval ∧
        M.Retained s x h ctx.endTime ∧
        ¬ M.K_E x p b h ctx.endTime ∧
        ¬ EIB_DF10_CANDIDATE M s x p b h ctx := by
  exact
    ⟨TH3Countermodel.model,
     TH3Countermodel.Sys.only,
     TH3Countermodel.Content.only,
     TH3Countermodel.Problem.only,
     TH3Countermodel.Background.only,
     TH3Countermodel.Hist.only,
     TH3Countermodel.context,
     TH3Countermodel.concreteWitness⟩

/--
EIB-TH3B-PILOT: CCPResult and Retained do not uniformly entail the candidate
EKC predicate over the minimal unconstrained port signature.
-/
theorem EIB_TH3b_relative_non_sufficiency :
    ¬ (∀ (M : CRModel)
        (s : M.Sys)
        (x : M.Content)
        (p : M.Problem)
        (b : M.Background)
        (h : M.Hist)
        (ctx : IntervalContext M),
        (M.CCPResult s x p b h ctx.interval ∧
          M.Retained s x h ctx.endTime) →
          EIB_DF10_CANDIDATE M s x p b h ctx) := by
  intro hAll
  have hw := TH3Countermodel.concreteWitness
  have hEKC :=
    hAll
      TH3Countermodel.model
      TH3Countermodel.Sys.only
      TH3Countermodel.Content.only
      TH3Countermodel.Problem.only
      TH3Countermodel.Background.only
      TH3Countermodel.Hist.only
      TH3Countermodel.context
      ⟨hw.1, hw.2.1⟩
  exact hw.2.2.2 hEKC

end CREIB
