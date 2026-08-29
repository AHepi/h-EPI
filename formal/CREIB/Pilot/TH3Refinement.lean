import CREIB.Bridge.DF10Refinement
import CREIB.Pilot.TH3Countermodel

set_option autoImplicit false
set_option warningAsError true

namespace CREIB
namespace TH3RefinedCountermodel

def roles : ContentRoleRefinement TH3Countermodel.model :=
  ContentRoleRefinement.unrestricted TH3Countermodel.model

def problem : ProblemContent TH3Countermodel.model roles :=
  ⟨TH3Countermodel.Content.only, True.intro⟩

def legacyProblemTransport :
    LegacyProblemTransport TH3Countermodel.model roles where
  toLegacyProblem := fun _ => TH3Countermodel.Problem.only

def ports : DF10OpaquePorts TH3Countermodel.model roles :=
  DF10OpaquePorts.fromLegacy
    TH3Countermodel.model roles legacyProblemTransport

def endpoint :
    EndTimeWitness TH3Countermodel.model TH3Countermodel.context.interval :=
  TH3Countermodel.context.endTimeWitness

/--
The existing singleton countermodel lifted through the explicit problem-sort
transport.  This is a compatibility witness, not a claim that the legacy
independent carrier already encoded CR-1.0's role semantics.
-/
theorem concreteWitness :
    ports.CCPResult
        TH3Countermodel.Sys.only TH3Countermodel.Content.only problem
        TH3Countermodel.Background.only TH3Countermodel.Hist.only
        TH3Countermodel.context.interval ∧
      ports.Retained
        TH3Countermodel.Sys.only TH3Countermodel.Content.only
        TH3Countermodel.Hist.only endpoint.1 ∧
      ¬ ports.K_E
        TH3Countermodel.Content.only problem TH3Countermodel.Background.only
        TH3Countermodel.Hist.only endpoint.1 ∧
      ¬ EIB_DF10_REFINED
        TH3Countermodel.model roles ports
        TH3Countermodel.Sys.only TH3Countermodel.Content.only problem
        TH3Countermodel.Background.only TH3Countermodel.Hist.only
        TH3Countermodel.context.interval endpoint := by
  constructor
  · exact True.intro
  constructor
  · exact True.intro
  constructor
  · intro hKE
    exact hKE
  · intro hEKC
    exact hEKC.2.1

end TH3RefinedCountermodel

/-- A role-refined lift of the pilot's concrete relative countermodel. -/
theorem EIB_TH3b_refined_countermodel_exists :
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
          M roles ports s x p b h interval endpoint := by
  exact
    ⟨TH3Countermodel.model,
     TH3RefinedCountermodel.roles,
     TH3RefinedCountermodel.ports,
     TH3Countermodel.Sys.only,
     TH3Countermodel.Content.only,
     TH3RefinedCountermodel.problem,
     TH3Countermodel.Background.only,
     TH3Countermodel.Hist.only,
     TH3Countermodel.context.interval,
     TH3RefinedCountermodel.endpoint,
     TH3RefinedCountermodel.concreteWitness⟩

/--
CCPResult and Retained do not uniformly entail the role-refined DF-10
candidate over the unconstrained refined opaque-port signature.  This is the
same relative `¬ ∀` shape as the legacy pilot; it does not adjudicate source
TH-3 or any missing dependency mapping.
-/
theorem EIB_TH3b_refined_relative_non_sufficiency :
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
            M roles ports s x p b h interval endpoint) := by
  intro hAll
  have hw := TH3RefinedCountermodel.concreteWitness
  have hEKC :=
    hAll
      TH3Countermodel.model
      TH3RefinedCountermodel.roles
      TH3RefinedCountermodel.ports
      TH3Countermodel.Sys.only
      TH3Countermodel.Content.only
      TH3RefinedCountermodel.problem
      TH3Countermodel.Background.only
      TH3Countermodel.Hist.only
      TH3Countermodel.context.interval
      TH3RefinedCountermodel.endpoint
      ⟨hw.1, hw.2.1⟩
  exact hw.2.2.2 hEKC

end CREIB
