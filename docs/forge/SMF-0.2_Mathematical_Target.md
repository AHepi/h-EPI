# SMF-0.2 mathematical target: semantic-role determination

## Status and authority boundary

This note fixes a mathematical target for criticizing candidate formalizations of semantic roles before further Lean work. It is a non-authoritative forge artifact. It neither amends Model CR-1.0 nor asserts that the proposed neutral vocabulary is the vocabulary intended by its author.

The sole semantic and formal authority remains `Creativity as Explanatory Self-Correction`, Model CR-1.0, SHA-256 `08ff81e848fea976b558345402d85723173be8f40f1041fb00d6267f1e026b8b`. Every source transcription, interpretation, and project addition used below must remain separately typed. A model-theoretic result is a `FORMAL_CONSEQUENCE` of its named premises; it cannot promote any premise to source authority.

The target contains no evidential probability, instance-to-law induction, confirmation rule, or convergence rule. Agreement, consensus, source-search rank, repeated test survival, and proof success confer no semantic authority. A countermodel defeats a stated formal entailment. Failure to find a countermodel has no positive semantic force, and a proof establishes only a consequence of its typed premises; semantic applicability remains independently reviewable.

## The exact question

Let a target-neutral base structure be fixed, including its declared history or history family. For a history-local test, conservatively extend both the candidate and control signatures by a fresh constant \(c_h:\mathsf{History}\) and use a pointed structure \((A,h)\), meaning the expansion with \(c_h^A=h\); the candidate sentences otherwise remain unchanged. Every reduct, rival, fiber, and intended-base coverage claim for that test uses this pointed control signature. For a family-level test, omit \(c_h\) and declare that the entire structure \(A\) is held fixed. Do the candidate constraints determine the extensions of the registered target-role symbols, including `Problem`, `Attempt`, `CritOf`, `UsesReason`, `Authors`, and `K_E` (and any separately registered unary role tags), or can the same declared base receive two incompatible role assignments?

A pointed base alone does not localize a role whose extension ranges across several histories. Each test therefore also declares a scope \(\tau\). For a family-level test, \(\tau=*\). For a history-local test, \(\tau=(c_h,L)\), where every tested role \(R\) has a versioned, digest-bound, target-neutral localization formula \(L_R(\bar x,c_h)\) over the control signature. If \(R\) has a history coordinate, \(L_R\) may simply require that coordinate to equal \(c_h\). A role without one requires an explicit incidence map connecting its tuples to the distinguished history. That map is a separately typed `SOURCE_INTERPRETATION` or `PROJECT_IMPORT` dependency; it is not supplied by the role's name. A missing, role-dependent, or unreviewed localization blocks a history-local claim.

For any model \(M\), define its declared role view

\[
\operatorname{RView}_{\tau}^{M}(Q_{role})=
\begin{cases}
(R^M)_{R\in Q_{role}}, & \tau=*,\\
\bigl(\{\bar a\in R^M\mid M\models L_R(\bar a,c_h)\}\bigr)_{R\in Q_{role}},
  & \tau=(c_h,L).
\end{cases}
\]

All role disagreements and role assignments below mean disagreement or assignment within this declared view. Thus a local test at \(h_0\) is not defeated merely because two models differ only at another history \(h_1\).

The desired test is therefore not whether a structure containing appropriately named predicates is satisfiable. It is whether those predicates are *implicitly determined* by declared non-role structure and any explicitly held-fixed auxiliaries.

## Provisional target-neutral signature

For SMF-0.2, the proposed neutral signature is the relational signature \(\Sigma_0\) with sorts

\[
\mathsf{System},\ \mathsf{History},\ \mathsf{Time},\ \mathsf{Node},\ \mathsf{Intervention}
\]

and symbols

\[
\begin{aligned}
&\prec\;\subseteq\mathsf{Time}^2,\\
&\mathsf{Event},\mathsf{State},\mathsf{Token},\mathsf{Operation},\mathsf{Agent},
  \mathsf{Resource}\;\subseteq\mathsf{Node},\\
&\mathsf{Occurs}\;\subseteq\mathsf{Node}\times\mathsf{History}\times\mathsf{Time},\\
&\mathsf{Inside}\;\subseteq\mathsf{System}\times\mathsf{Node}\times
  \mathsf{History}\times\mathsf{Time},\\
&\mathsf{Causal}\;\subseteq\mathsf{History}\times\mathsf{Node}^2,\\
&\mathsf{Available}\;\subseteq\mathsf{System}\times\mathsf{Node}\times
  \mathsf{History}\times\mathsf{Time},\\
&\mathsf{Variant}\;\subseteq\mathsf{Intervention}\times\mathsf{History}^2,\\
&\mathsf{HeldFixed}\;\subseteq\mathsf{Intervention}\times\mathsf{Node}.
\end{aligned}
\]

`Node` is deliberately uncommitted: a node may later be interpreted as a token, state, operation, content carrier, response, standard, or participant. The unary tags are not presumed disjoint. `Causal` records a declared causal edge but assigns no epistemic role to either endpoint. `Variant` and `HeldFixed` record an intervention design but do not say which variation is meaning-preserving or defect-relevant.

Let \(P_0=\{\rho_j\}_j\) be the versioned, digest-bound premise records that constitute the neutral base theory. Each \(\rho_j\) contains an immutable \((id,version,digest)\) reference, a digest-bound signature reference, a well-formed formula \(\varphi_j\), claim kind, and direct immutable dependency references. Write \(T_0=\{\varphi_j\}_j\) after applying the reviewed common-signature transports defined below. Every member of \(P_0\) is a `PROJECT_IMPORT`, not background logic and not source authority. In this proposal, those premises say only that \(\prec\) is irreflexive and transitive, that every first argument of `Occurs` is tagged `Event`, and that the endpoints of a `Causal` edge occur in its stated history. They add no total order, unique boundary, unique event time, role disjointness, semantic equivalence, authorship, criticism, success, or physical-realization axiom. Additional neutral structure requires a versioned signature revision and a new import dependency.

This choice of \(\Sigma_0\), including the decision to reify heterogeneous source carriers as `Node`, is also a `PROJECT_IMPORT`. Any claim that it faithfully projects CR-1.0 additionally requires a reviewed `SOURCE_INTERPRETATION` mapping. Target neutrality is a constraint on this experiment, not a fact obtained from the source by naming it so. A review of a theorem or countermodel must therefore include the identifiers, versions, digests, and dispositions of every premise in \(P_0\); calling them “neutral” does not remove them from review.

## Role expansion and theory slices

The first role signature \(\Sigma_R\) adds the unary role predicates

\[
\mathsf{ProblemRole},\ \mathsf{AttemptRole},\ \mathsf{CriticismRole},\
\mathsf{StandardRole}\subseteq\mathsf{Node}
\]

and the relations

\[
\begin{aligned}
&\mathsf{Problem}(s,p,b,t),\qquad
  \mathsf{Attempt}(s,x,p,b,t),\\
&\mathsf{CritOf}(c,x,p,b,k),\qquad
  \mathsf{UsesReason}(s,c,a),\\
&\mathsf{Authors}(s,x,p),\qquad
  \mathsf{K_E}(x,p,b,h,t).
\end{aligned}
\]

Here \(s,h,t\) have sorts `System`, `History`, and `Time`; every other displayed argument has sort `Node`. This is only the first diagnostic surface. `Rep`, `Purports`, `Explains`, `BearsOn`, `Prov`, `CLine`, content equivalence, retention, and the remaining CR-1.0 vocabulary enter a full candidate as separately declared auxiliary symbols. They must not be silently compiled into one of the relations above. For one comparison, write \(\Sigma=\Sigma_0\cup\Sigma_R\cup\Sigma_{aux}\) for the declared common candidate signature, including the pointed-history constant when that test uses one.

Each formula-bearing premise is stored as a record

\[
\rho=(r,\sigma_{ref},\varphi,kind,deps),
\qquad r=(id,version,digest),
\]

where \(\varphi\) is a well-formed sentence in the digest-bound declared signature \(\sigma_{ref}\), \(deps\) is a finite set of immutable \((id,version,digest)\) dependency references, and

\[
kind\in\{\mathsf{SOURCE\_AUTHORITY},\mathsf{SOURCE\_INTERPRETATION},
\mathsf{PROJECT\_IMPORT}\}.
\]

`SOURCE_AUTHORITY` is reserved for a digest-bound, locator-bound proposition or exact formula stated in CR-1.0. A carrier choice, disambiguation, formal paraphrase, or source-to-signature map is a `SOURCE_INTERPRETATION`. An independently added grounding, causal, modal, episode, or realization condition is a `PROJECT_IMPORT`. A premise has exactly one kind. `EXTERNAL_SOURCE_REPORT` records may occur in the evidence dependency graph, but their prose is not a target-language premise; it can enter the formula theory only through an explicit `SOURCE_INTERPRETATION` or `PROJECT_IMPORT` bridge. `FORMAL_CONSEQUENCE` is an output kind, not a premise kind.

Before records can form one theory, each declared signature must either be the common candidate signature \(\Sigma\) or have a reviewed, digest-bound transport \(\iota_\rho:\sigma_{ref}\to\Sigma\). The transport record is itself typed as `SOURCE_INTERPRETATION` or `PROJECT_IMPORT` as appropriate and appears in \(deps\); it never inherits `SOURCE_AUTHORITY` from the transported claim. A missing or ambiguous transport blocks theory formation. Transports must also preserve co-reference: records with the same digest-bound source signature use one common transport, and transports from overlapping signatures must agree on every shared sort, constant, function, and relation symbol. Incompatible maps cannot be combined in one theory slice; they define separate interpretation branches that may be compared only as inter-interpretation rivals after a common target-language comparison map is reviewed.

Let \(S\), \(I\), and \(P\) be sets of formula-bearing premise records for the source-authority slice, reviewed interpretation choices, and further project imports, respectively. Let \(\operatorname{DepCl}(U)\) be the least set of records containing \(U\) and the unique record matching every immutable reference reached transitively through a member's \(deps\). If a reference is absent, resolves to more than one record, or fails its digest, \(\operatorname{DepCl}(U)\) is undefined and the result is blocked rather than computed from a partial closure. Evidence, locator, signature, and mapping records may belong to a successful closure without thereby becoming formulas. For any dependency-closed record set \(D\), define its common-signature formula projection

\[
\Phi_{\Sigma}(D)=
\{\iota_\rho(\varphi_\rho)\mid
  \rho\in D\text{ is a formula-bearing premise record}\},
\]

where \(\iota_\rho\) is the identity when \(\sigma_{ref}=\Sigma\). Thus \(\Phi_\Sigma(D)\) is a well-typed set of \(\Sigma\)-sentences, not a union of formulas from unrelated languages.

The complete dependency-record set and its formula theory are then

\[
D_{CR}^{I,P_0,P}=\operatorname{DepCl}(P_0\cup S\cup I\cup P),
\qquad
T_{CR}^{I,P_0,P}=\Phi_{\Sigma}\!\left(D_{CR}^{I,P_0,P}\right).
\]

Here \(S\) contains only `SOURCE_AUTHORITY` records admitted to the slice. A judgment \(T_{CR}^{I,P_0,P}\models\varphi\) is recorded as `FORMAL_CONSEQUENCE` with the complete record-ID, kind, version, and digest closure \(D_{CR}^{I,P_0,P}\), including every `PROJECT_IMPORT` record used to form \(T_0\). The formula set and its dependency records are never conflated. The judgment is not restated as something CR-1.0 says. Missing review or traceability for even one dependency record blocks promotion of the result beyond an unreviewed formal artifact.

## Rival expansions

Each rival test declares a nonempty target-role set \(\varnothing\ne Q_{role}\subseteq\Sigma_R\) and a control signature \(\Gamma\) with

\[
\Sigma_0\subseteq\Gamma\subseteq(\Sigma_0\cup\Sigma_R\cup\Sigma_{aux})\setminus Q_{role}.
\]

For a family-level broad test take \(\Gamma=\Sigma_0\). A diagnostic test for one role normally holds every non-target symbol fixed by taking \(\Gamma=\Sigma\setminus Q_{role}\). In a history-local test, \(\Gamma\) includes \(c_h\) and every symbol used by the registered localization formulas. This prevents a supposed relabelling result from being purchased by changing the distinguished history, a localizer, or an unrelated auxiliary.

For a fixed \(\Gamma\)-structure \(B\), define

\[
\operatorname{Exp}^{\Gamma}_{I,P_0,P}(B)=
\{M\mid M\models T_{CR}^{I,P_0,P}\ \text{and}\ M\!\upharpoonright_{\Gamma}=B\}.
\]

Thus a history-local expansion class is indexed by a pointed control reduct, not merely by its unpointed \(\Sigma_0\)-reduct. Two uses of “rival” must remain distinct.

An *intra-candidate rival pair* consists of \(M,N\in\operatorname{Exp}^{\Gamma}_{I,P_0,P}(B)\) whose declared target-role views disagree. Such a pair refutes role determination from the declared \(\Gamma\)-reduct by that one candidate theory for the declared scope \(\tau\). A pair constructed for the broad \(\Gamma=\Sigma_0\) test does not refute a stronger diagnostic claim that additionally holds an auxiliary fixed unless it is also a pair over that stronger control reduct.

An *inter-interpretation rival pair* consists of

\[
M\in\operatorname{Exp}^{\Gamma}_{I_1,P_{0,1},P_1}(B),\qquad
N\in\operatorname{Exp}^{\Gamma}_{I_2,P_{0,2},P_2}(B)
\]

with a disagreement in the declared role view. It exposes a live source-interpretation or project-import fork. It does not by itself refute either rival theory, because the two structures do not satisfy the same premise set. If the branches do not share the exact digest-bound \(\Gamma\), scope, and base \(B\), a reviewed transport into a common comparison signature is required before such a rival claim is well typed.

## Role-relabel twin countermodel

Let \(T\) be one fixed candidate theory and \(Q_{role}\) its tested role symbols. A \((Q_{role},\Gamma,\tau)\)-role-relabel twin is a pair \((M,N)\) such that

\[
M\models T,\quad N\models T,\quad
M\!\upharpoonright_\Gamma=N\!\upharpoonright_\Gamma,
\quad\text{and}\quad
\operatorname{RView}_{\tau}^{M}(Q_{role})
\ne\operatorname{RView}_{\tau}^{N}(Q_{role}).
\]

Equality of reducts means that the carrier sets and every symbol in \(\Gamma\), including \(c_h\) and every symbol used by a localization formula in a history-local test, are literally fixed; an isomorphic presentation may be transported onto one fixed carrier before comparison. The role difference must be exhibited by a tuple \(\bar a\) and role \(R\in Q_{role}\) that lies in the declared view and for which

\[
M\models R(\bar a)\quad\text{and}\quad N\models\neg R(\bar a).
\]

For \(\tau=(c_h,L)\), membership in the declared view additionally requires \(M\models L_R(\bar a,c_h)\), equivalently \(N\models L_R(\bar a,c_h)\) because the localization structure is held fixed.

A pure name permutation is permitted only between relations with the same sorted arity. Otherwise the twin changes extensions tuple-by-tuple. In either case, it may not alter a time, event, boundary, causal edge, intervention, held-fixed condition, or any other symbol in \(\Gamma\).

This is stronger than showing that two different histories receive the same classifier output. It demands incompatible semantic expansions of one declared control reduct (or of one pointed history when the test is explicitly history-local).

## Implicit determination criterion

The target roles \(Q_{role}\) are implicitly determined by \(\Gamma\) in \(T\) at declared scope \(\tau\) exactly when

\[
\operatorname{ID}_T(Q_{role}\mid\Gamma;\tau)\;:\Longleftrightarrow\;
\forall M,N\models T,
\bigl(M\!\upharpoonright_\Gamma=N\!\upharpoonright_\Gamma
\Rightarrow
\operatorname{RView}_{\tau}^{M}(Q_{role})
=\operatorname{RView}_{\tau}^{N}(Q_{role})\bigr).
\]

For a substantive positive result, let \(\mathcal B_{int}\subseteq\operatorname{Str}(\Gamma)\) be a declared, versioned, digest-bound registry of intended control bases, and require \(\mathcal B_{int}\ne\varnothing\). In a history-local test, \(\Gamma\) here is the pointed control signature containing \(c_h\), so each member fixes the distinguished history rather than merely the surrounding unpointed structure. For each \(R\in Q_{role}\) of sorted arity \((s_1,\ldots,s_n)\), define the localization domain

\[
\operatorname{Loc}_{R}(B)=
\{\bar a\in B_{s_1}\times\cdots\times B_{s_n}
  \mid B\models L_R(\bar a,c_h)\}.
\]

Every history-local pair \((B,R)\in\mathcal B_{int}\times Q_{role}\) must have either a digest-bound witness that \(\operatorname{Loc}_{R}(B)\ne\varnothing\), or a distinct, digest-bound human disposition declaring the empty localization domain intended and explaining its scope. The latter makes the uniqueness statement vacuous or not applicable for that pair and cannot count as evidence of substantive role determination. A positive determination claim over all registered bases and roles may be called substantive only when every such localization domain is witnessed nonempty.

The definition of \(\operatorname{ID}\) is a uniqueness condition only: it holds vacuously if \(T\) has no models and says nothing about an intended \(B\in\mathcal B_{int}\) that has no \(T\)-expansion. A substantive positive determination result must therefore also prove \(\operatorname{Mod}(T)\ne\varnothing\) and

\[
\forall B\in\mathcal B_{int},\qquad
\exists M\models T\ \text{with}\ M\!\upharpoonright_\Gamma=B,
\]

so that a \(T\)-expansion is exhibited for every registered base. One valid role-relabel twin proves

\[
\neg\operatorname{ID}_T(Q_{role}\mid\Gamma;\tau).
\]

A bounded search that returns no twin does not establish \(\operatorname{ID}\). Discharging the positive direction requires the uniqueness proof, non-vacuity, and registered intended-base coverage over the declared model class. The theorem still concerns the encoded theory and its typed premises, including every base import in \(P_0\); semantic fidelity remains a separate review question.

## What the current calibration establishes

The executable calibration defines two finite cases, \(g\) and \(\ell\), and four Boolean features:

\[
\begin{array}{c|cccc}
 & \mathsf{TypedEvents} & \mathsf{TypedRoles} & \mathsf{CausalUse} &
 \mathsf{MatchedCF}\\ \hline
g & \top & \top & \top & \top\\
\ell & \top & \top & \bot & \bot
\end{array}
\]

Its deliberately weak projection is

\[
W(z):=\mathsf{TypedEvents}(z)\land\mathsf{TypedRoles}(z).
\]

Therefore

\[
W(g)=W(\ell)=\top,
\]

even though the recorded causal and matched-counterfactual features differ. Mechanics establish only this equality and the recorded feature differences. Calling the pair an in-scope failure or calling \(W\) under-discriminating is conditional on a human accepting the proposed oracle, held-fixed conditions, and applicability of the fixture. The null semantic verdict licenses neither diagnosis. The run does not construct a same-reduct role twin, and it does not refute CR-1.0. In particular, \(W\) deliberately omits the system-level causal-use and counterfactual conditions stated in SC-2 and SC-3. Whether a faithful, complete formalization of those and the other CR-1.0 constraints implicitly determines the roles is open.

## Existential erasure and non-vacuity

Begin with a baseline theory \(T_b\) over \(\Sigma_b\). If every tested target role is already in \(\Sigma_b\), put \(\Sigma=\Sigma_b\) and \(T=T_b\). If a set \(Q_{new}\) of tested roles is new, form the common signature \(\Sigma=\Sigma_b\cup Q_{new}\) and the conservative language lift

\[
T=T_b^{\uparrow\Sigma}:=T_b,
\]

where the same baseline sentences are now read in \(\Sigma\); consequently every well-sorted interpretation of \(Q_{new}\) over a model of \(T_b\) is permitted. All notation below uses this common signature, so the tested roles satisfy \(Q_{role}\subseteq\Sigma\) and \(Q_{role}^{M}\) is defined for both baseline and successor models.

A comparison must declare, version, and digest-bind an *old-result signature* \(\Lambda_{old}\) and a control signature \(\Gamma\) such that

\[
\Sigma_0\subseteq\Lambda_{old}\subseteq\Sigma\setminus Q_{role},
\qquad
\Sigma_0\subseteq\Gamma\subseteq\Sigma\setminus Q_{role}.
\]

Thus \(\Lambda_{old}\) contains exactly the target-neutral histories, observable classifications, or other non-target results whose admission is being compared, while \(\Gamma\) holds fixed the non-target structure needed by the role test. The signatures may contain different non-target auxiliaries; neither is silently projected into the other. Excluding \(Q_{role}\) from \(\Lambda_{old}\) is what keeps strict old-result restriction distinct from strict role-assignment narrowing. If a comparison instead retains a target role in its projected language, it must say so and may not claim that the two strict gain notions are independent for that role.

Let \(T'\) be an arbitrary proposed successor over

\[
\Sigma'=\Sigma\cup H_{repair},
\]

where \(H_{repair}\cap\Sigma=\varnothing\) is fresh repair vocabulary and may be empty. A purely additive extension \(T'=T\cup\Delta\) is one special case; replacement or removal of a premise is also representable and must be reported as such. The common-signature lift above ensures that fresh repair symbols and newly introduced tested roles are not conflated.

The baseline and successor old-result shadows are

\[
\begin{aligned}
\operatorname{Old}_{\Lambda_{old}}(T)
  &=\{A\in\operatorname{Str}(\Lambda_{old})\mid
      \text{some }\Sigma\text{-expansion }M\text{ of }A\text{ satisfies }T\},\\
\operatorname{Old}_{\Lambda_{old}}(T')
  &=\{A\in\operatorname{Str}(\Lambda_{old})\mid
      \text{some }\Sigma'\text{-expansion }M'\text{ of }A\text{ satisfies }T'\}.
\end{aligned}
\]

These projections existentially erase the fresh repair vocabulary and every baseline symbol deliberately excluded from the declared old-result signature; nothing may be omitted silently. They supply one strength axis: *old-result restriction*. Every hardening comparison first requires non-broadening,

\[
\operatorname{Old}_{\Lambda_{old}}(T')
\subseteq
\operatorname{Old}_{\Lambda_{old}}(T),
\]

and a gain on this axis requires the inclusion to be strict. Because \(T'\) need not be an additive extension, even the non-strict subset condition is substantive: a successor that admits a new \(\Lambda_{old}\)-reduct has broadened the baseline and is not a hardening on this comparison.

A second axis asks whether the successor narrows target-role assignments over a fixed control reduct. For a \(\Gamma\)-structure \(B\), define the *projected target-role fibers*

\[
\begin{aligned}
\operatorname{RFib}_{T,\tau}(B)
  &=\{\operatorname{RView}_{\tau}^{M}(Q_{role})
      \mid M\models T\ \text{and}\ M\!\upharpoonright_\Gamma=B\},\\
\operatorname{RFib}_{T',\tau}(B)
  &=\{\operatorname{RView}_{\tau}^{M'}(Q_{role})
      \mid M'\models T'\ \text{and}\ M'\!\upharpoonright_\Gamma=B\}.
\end{aligned}
\]

The projection forgets fresh repair symbols and any non-control auxiliaries while retaining exactly the family-level or localized target-role view selected by \(\tau\). Every hardening comparison also requires global role-assignment non-broadening over the declared control signature and scope,

\[
\forall C\in\operatorname{Str}(\Gamma),\qquad
\operatorname{RFib}_{T',\tau}(C)\subseteq\operatorname{RFib}_{T,\tau}(C).
\]

A witnessed role-narrowing gain additionally names a retained control reduct \(B\) and distinct assignments \(E_{bad},E_{keep}\) such that

\[
\begin{gathered}
E_{bad},E_{keep}\in\operatorname{RFib}_{T,\tau}(B),\qquad
\varnothing\ne\operatorname{RFib}_{T',\tau}(B)
  \subsetneq\operatorname{RFib}_{T,\tau}(B),\\
E_{bad}\notin\operatorname{RFib}_{T',\tau}(B),
\qquad E_{keep}\in\operatorname{RFib}_{T',\tau}(B).
\end{gathered}
\]

Thus the allegedly removed assignment must have been a live baseline rival over the same control reduct, the intended assignment must survive, and the successor may not purchase that local gain by admitting a novel target-role assignment over some other control reduct. Uniqueness,

\[
\operatorname{RFib}_{T',\tau}(B)=\{E_{keep}\},
\]

is the strongest local determination result for that registered \(B\). A proposal may preserve every old-result reduct while uniquely determining its target roles over a registered base. That can harden an ambiguity on the role axis without excluding an old-result history or classification on the first axis. It will generally exclude full \(\Sigma\)-models carrying the removed target-role assignment, which is why \(\Lambda_{old}\), \(\Gamma\), and \(Q_{role}\) must not be conflated. Conversely, excluding an old-result reduct need not determine the roles of the reducts that survive. Neither axis substitutes for the other.

The following cases must therefore not be conflated:

\[
\begin{array}{ll}
\operatorname{Old}_{\Lambda_{old}}(T')=
  \operatorname{Old}_{\Lambda_{old}}(T)
  \text{ and a registered }B\text{ has a witnessed strict role-fiber narrowing}
  & \text{no old-result restriction; possible ambiguity hardening};\\
\operatorname{Old}_{\Lambda_{old}}(T')=
  \operatorname{Old}_{\Lambda_{old}}(T)
  \text{ and no strict role-fiber narrowing is witnessed}
  & \text{no demonstrated gain on either axis};\\
\operatorname{Old}_{\Lambda_{old}}(T')
  \subsetneq\operatorname{Old}_{\Lambda_{old}}(T)
  & \text{old-result restriction requiring preservation review}.
\end{array}
\]

All three rows presuppose both non-broadening conditions above. The third row makes no claim about whether a role-fiber gain also occurs. If either non-broadening condition fails, the proposal is not a hardening under this registry; any deliberate tradeoff must instead be recorded as a semantic revision for human review.

An old-result exclusion witness is an explicit \(\Lambda_{old}\)-structure \(B_{bad}\) such that

\[
B_{bad}\in\operatorname{Old}_{\Lambda_{old}}(T)
\quad\text{and}\quad
B_{bad}\notin\operatorname{Old}_{\Lambda_{old}}(T').
\]

That witness establishes strict restriction only; it does not establish that the successor is non-vacuous. The inconsistent successor \(T'=\{\bot\}\), for example, excludes every baseline old-result reduct. Every positive hardening assessment must independently require \(\operatorname{Mod}(T')\ne\varnothing\) and at least one named retained intended expansion. Adding a predicate name whose value never constrains admission and leaves rival role assignments untouched fails both axes. A unique role assignment may do substantive determination work even when it excludes no old-result reduct; whether that work resolves the intended ambiguity remains a typed, human-reviewed claim rather than a consequence of uniqueness alone.

## Non-scalar hardening obligations

Hardening is assessed relative to a versioned, digest-bound obligation registry

\[
\mathcal O=(r_T,r_{T'},\widehat Q_{role},G_{bad},P_{keep},X_{keep},C_{keep},
\Lambda_{old},\Gamma,\tau,\Sigma_{scope}),
\]

where \(r_T=(id_T,version_T,digest_T)\) and
\(r_{T'}=(id_{T'},version_{T'},digest_{T'})\) bind the complete baseline and
successor theory records, their signatures, and their dependency closures,
denoted \(D_T\) and \(D_{T'}\), with
\(T=\Phi_{\Sigma}(D_T)\) and \(T'=\Phi_{\Sigma'}(D_{T'})\). The target-role registry is

\[
\widehat Q_{role}=
(r_Q,\langle(R,(s_1^R,\ldots,s_{n_R}^R))\rangle_{R\in Q_{role}}),
\qquad \varnothing\ne Q_{role},
\]

where \(r_Q=(id_Q,version_Q,digest_Q)\) binds a canonical ordering of every target symbol and its sorted arity. Every role view, fiber, localization record, and gain witness in \(\mathcal O\) uses this exact registry. A
change to either theory or closure creates a different comparison; witnesses
and reviews cannot be transplanted by reusing an identifier. The component
\(G_{bad}\) is one typed, immutable-reference-bound gain obligation of either form

\[
(r_g,\mathsf{OLD\_RESTRICTION},B_{bad})
\quad\text{or}\quad
(r_g,\mathsf{ROLE\_NARROWING},B_{\Gamma},E_{bad},E_{keep}),
\]

with \(r_g=(id_g,version_g,digest_g)\). The first names an old-result structure to exclude. The second names one fixed control reduct \(B_{\Gamma}\), a distinct baseline target-role assignment \(E_{bad}\) to remove, and an intended baseline target-role assignment \(E_{keep}\) to retain under the exact pre/post fiber conditions above.

Each protected positive record has the form

\[
p=(r_p,M_p,\kappa_p)\in P_{keep},
\]

where \(r_p\) is immutable, \(M_p\models T\) is a digest-bound baseline model certificate, and \(\kappa_p\) is the exact protected classification or target-role diagram true in \(M_p\) under the same declared scope \(\tau\). Each protected exclusion record has the form

\[
x=(r_x,\Delta_x,\chi_x,U_x,D_x,M_x,proof_x)\in X_{keep},
\]

where \(\Delta_x\) is a digest-bound \(\Sigma_{scope}\)-diagram, \(\chi_x\) is the forbidden classification sentence, \(U_x\subseteq D_T\) is a named seed set, and \(D_x=\operatorname{DepCl}(U_x)\subseteq D_T\) is an immutable dependency-closed set whose formula-bearing records are active in \(T\). The digest-bound model certificate \(M_x\models T\cup\Delta_x\) proves that the protected baseline context is live; the digest-bound \(proof_x\) establishes

\[
\operatorname{Mod}\!\left(
\Phi_{\Sigma}(D_x)\cup\Delta_x\cup\{\chi_x\}
\right)=\varnothing.
\]

Each protected-consequence record has the form

\[
c=(r_c,\varphi_c,U_c,D_c,proof_c)\in C_{keep},
\]

where \(U_c\subseteq D_T\) is a named seed set, \(D_c=\operatorname{DepCl}(U_c)\subseteq D_T\) is its exact immutable dependency closure with every formula-bearing record active in \(T\), and \(proof_c\) is a digest-bound certificate of \(\Phi_\Sigma(D_c)\models\varphi_c\). The registries contain records, not bare formulas or reference strings. The remaining components declare the old-result signature, control signature, role-view scope and localization, and preservation-scope signature, including every fixed boundary, history, modality, intervention, resource, and other control symbol, with

\[
\Lambda_{old}\cup\Gamma\subseteq\Sigma_{scope}
\subseteq\Sigma\setminus Q_{role}.
\]

Allowing \(\Sigma_{scope}\) to include non-target auxiliaries is necessary when the diagnostic determination claim holds them fixed. Every signature and diagram above is versioned and digest-bound; a missing transport into the common comparison language blocks the assessment.

A proposed \(T'\) may receive `HARDENING_UNREFUTED` only after all of the following distinct obligations are discharged:

| Obligation | Exact condition |
|---|---|
| Old-result non-broadening | Prove \(\operatorname{Old}_{\Lambda_{old}}(T')\subseteq\operatorname{Old}_{\Lambda_{old}}(T)\) for the declared, versioned, digest-bound projection signature. |
| Role-assignment non-broadening | Prove \(\operatorname{RFib}_{T',\tau}(C)\subseteq\operatorname{RFib}_{T,\tau}(C)\) for every \(\Gamma\)-structure \(C\); a local repair may not introduce a new rival elsewhere within the same declared role view. |
| Targeted gain | Discharge the registered \(G_{bad}\): either \(B_{bad}\in\operatorname{Old}_{\Lambda_{old}}(T)\setminus\operatorname{Old}_{\Lambda_{old}}(T')\), or \(E_{bad},E_{keep}\in\operatorname{RFib}_{T,\tau}(B_{\Gamma})\), the nonempty successor fiber is a strict subset of the baseline fiber, \(E_{bad}\) is absent, and \(E_{keep}\) remains. The axis, scope, and every witness are explicit. |
| Successor non-vacuity | Prove \(\operatorname{Mod}(T')\ne\varnothing\); the retained intended witness below must exhibit at least one such model rather than allowing inconsistency to count as maximal restriction. |
| Positive preservation | \(P_{keep}\ne\varnothing\), and for every \((r_p,M_p,\kappa_p)\in P_{keep}\), exhibit \(M'_p\models T'\) with \(M'_p\!\upharpoonright_{\Sigma_{scope}}=M_p\!\upharpoonright_{\Sigma_{scope}}\) and \(M'_p\models\kappa_p\). |
| Exclusion preservation | For every \((r_x,\Delta_x,\chi_x,U_x,D_x,M_x,proof_x)\in X_{keep}\), verify \(M_x\models T\cup\Delta_x\) and the baseline exclusion certificate. Exhibit a successor context model \(M'_x\models T'\cup\Delta_x\), then name \(U'_x\subseteq D_{T'}\), compute \(D'_x=\operatorname{DepCl}(U'_x)\subseteq D_{T'}\), and prove with a digest-bound successor certificate that \(\operatorname{Mod}(\Phi_{\Sigma'}(D'_x)\cup\Delta_x\cup\{\chi_x\})=\varnothing\). Thus neither an impossible context nor deletion of the whole context can manufacture preservation; a renamed or weakened forbidden classification is not the same exclusion. |
| Consequence preservation | For every \((r_c,\varphi_c,U_c,D_c,proof_c)\in C_{keep}\), verify \(D_c=\operatorname{DepCl}(U_c)\subseteq D_T\), verify that its formula-bearing records remain active in \(T\), and replay \(proof_c:\Phi_\Sigma(D_c)\models\varphi_c\). Then name \(U'_c\subseteq D_{T'}\), compute \(D'_c=\operatorname{DepCl}(U'_c)\subseteq D_{T'}\), and prove \(\Phi_{\Sigma'}(D'_c)\models\varphi_c^{\uparrow\Sigma'}\) with a digest-bound successor certificate. Because \(T'=\Phi_{\Sigma'}(D_{T'})\), this also proves \(T'\models\varphi_c^{\uparrow\Sigma'}\). Reusing \(D_c\) requires every referenced record and formula to remain unchanged and active in \(D_{T'}\); any different closure is a new, separately typed consequence claim requiring review, not automatic preservation. |
| Scope preservation | The paired positive models and paired baseline/successor exclusion-context models preserve the registered interpretations of \(\Sigma_{scope}\), including pointed or quantified histories and intervention families. |
| Clause independence | For each successor clause claimed necessary, deleting that clause from \(T'\) re-admits a named defect witness while the complete successor excludes it. |
| Type and dependency preservation | No `EXTERNAL_SOURCE_REPORT`, `SOURCE_INTERPRETATION`, or `PROJECT_IMPORT` is reported as `SOURCE_AUTHORITY`; every retained, added, removed, replaced, or transported member of the baseline closure \(D_T\), including \(P_0\), \(S\), \(I\), \(P\), signature maps, and localization records, is explicit and receives a typed disposition; every new consequence retains its complete dependency-record closure rather than projecting evidence prose into the formula theory. |

The obligations are conjunctive and non-compensatory for either strength axis. Expansion narrowing cannot offset loss of one protected intended case; extra excluded counterfeits cannot offset a changed modality; a shorter proof cannot offset a hidden import. Status precedence is explicit. A known regression, protected loss, weakened claim, or collapsed distinction yields `NO_HARDENING`. A generated warrant for a structurally eligible external decision fork is only a route candidate; before exact human failure-locus triage it leaves the hardening assessment `UNRESOLVED`. An unresolved criticism, incomplete preservation set, or missing necessary semantic disposition likewise yields `UNRESOLVED` when a gain is claimed. If no targeted gain is recorded, the result is `NO_HARDENING` without asserting unreviewed preservation. A recorded gain remains `UNRESOLVED` under the current fail-closed rule below.

The warrant and planner-derived attack-target menu are non-authorizing. External criticism work begins only after an additive v2 triage is published, its terminal head is explicitly selected, and its `next_action` names both the external route and a nonempty exact subset of attack-target IDs. This scheduling still supplies no evidence for the selected assessment or against the others.

Promotion to `HARDENING_UNREFUTED` fails closed in the current implementation. Its runtime record does not yet encode digest-bound baseline and successor theory records and dependency closures, the nonempty sorted target-role registry, the declared old-result and control signatures, role-view scope and nonvacuous localization coverage, either global non-broadening relation, the typed gain axis, the exact pre/post fiber relation, successor non-vacuity, or all of the preservation obligations above, and it has no resolver for typed, digest-bound gain-witness, preservation-review, and human-decision records. Plain reference strings, even when nonempty, cannot trigger the positive status. A future promotion remains blocked pending both schema evolution and ledger-backed resolution, followed by discharge of every conjunctive obligation.

These statuses are scoped criticism records. None asserts truth, probability, confirmation, convergence, or finality.

## First theorem and countermodel obligations

| ID | Exact obligation | Present state |
|---|---|---|
| `SMF-CAL-CM-01` | Exhibit \(g,\ell\) with \(W(g)=W(\ell)=\top\), \(\mathsf{CausalUse}(g)\ne\mathsf{CausalUse}(\ell)\), and \(\mathsf{MatchedCF}(g)\ne\mathsf{MatchedCF}(\ell)\). | Mechanically witnessed by the finite calibration; this concerns \(W\) only and is not a Lean result. |
| `SMF-SIG-MAP-01` | Supply a reviewed, digest-bound transport from each source carrier and source symbol used in the first slice to the common \(\Sigma=\Sigma_0\cup\Sigma_R\cup\Sigma_{aux}\), with every reification, role overlap, arity choice, and loss typed as source authority, interpretation, or import. | Open prerequisite. |
| `SMF-CR-CM-01` | For one fixed, dependency-closed \(T_{CR}^{I,P_0,P}\), construct \(M,N\models T_{CR}^{I,P_0,P}\) and a tuple \(\bar a\) such that their declared control reducts are equal and their declared \(\tau\)-role views disagree; for a local test, the witness tuple must satisfy its reviewed \(L_R(\bar a,c_h)\). | Open. A witness would refute implicit determination for that encoded slice and declared scope only. |
| `SMF-CR-SAT-01` | Establish \(\varnothing\ne\mathcal B_{int}\subseteq\operatorname{Str}(\Gamma)\), exhibit a model of the same dependency-closed \(T_{CR}^{I,P_0,P}\), and exhibit a model over every registered intended base; a history-local \(\Gamma\) includes the fixed constant \(c_h\), and every registered \((B,R)\) has a nonempty localization-domain witness or a separately reviewed empty-domain disposition. | Open prerequisite for any substantive positive determination claim; inconsistency, an empty intended-base registry, unpointed coverage, or an unacknowledged empty localizer may not discharge it. |
| `SMF-CR-ID-01` | Alternatively prove \(\operatorname{ID}_{T_{CR}^{I,P_0,P}}(Q_{role}\mid\Gamma;\tau)\) for the same fixed slice, nonempty sorted target-role registry, control signature, and role view, with every \(P_0\) and localization premise in the dependency report and `SMF-CR-SAT-01` discharged. | Open. Finite search exhaustion cannot discharge it; a reviewed-empty localization pair remains explicitly vacuous rather than substantive. |
| `SMF-REV-CM-01` | For a proposed successor \(T'\), prove old-result non-broadening, exhibit \(B_{bad}\in\operatorname{Old}_{\Lambda_{old}}(T)\setminus\operatorname{Old}_{\Lambda_{old}}(T')\), exhibit a model of \(T'\), and retain at least one named intended witness. | Blocked until a reviewed successor, projection signature, defect witness, and intended witness exist. |
| `SMF-REV-FIBER-01` | For a proposed successor \(T'\), prove global role-assignment non-broadening for the same \(\tau\), then exhibit one fixed \(B_{\Gamma}\), distinct \(E_{bad},E_{keep}\in\operatorname{RFib}_{T,\tau}(B_{\Gamma})\), strict nonempty successor-fiber narrowing, removal of \(E_{bad}\), and retention of \(E_{keep}\); if uniqueness is claimed, prove \(\operatorname{RFib}_{T',\tau}(B_{\Gamma})=\{E_{keep}\}\). | Blocked until a reviewed localization, ambiguity witness, intended assignment, and successor exist. |
| `SMF-REV-PRES-01` | Prove both global non-broadening conditions, construct the required \(T'\)-model for every typed \(P_{keep}\) record, realize each typed \(X_{keep}\) context on both sides and replay its exclusion from named seed subclosures, replay every baseline \(C_{keep}\) certificate, prove each protected consequence from a named successor seed subclosure of \(D_{T'}\), and preserve each registered \(\Sigma_{scope}\)-reduct, including protected non-target auxiliaries. | Blocked until the protected registry receives human disposition. |
| `SMF-REV-INDEP-01` | For each allegedly necessary successor clause \(\delta\), exhibit a named defect model admitted by \(T'\setminus\{\delta\}\) and excluded by \(T'\). | Blocked until a reviewed successor exists. |
| `SMF-REV-RELABEL-01` | Prove the repaired theory's declared role-determination statement, or preserve a countermodel showing that it still fails. | Blocked by the preceding mapping, non-vacuity, and preservation obligations. |

`SMF-CR-CM-01` and `SMF-CR-ID-01` are rival outcomes for the same fixed formal target; they are not both expected to succeed. If neither is discharged, the correct result is open.

## Readiness decision

The current calibration mechanically establishes \(W(g)=W(\ell)\) and invariance of the fixture's declared old-result classification under erasure of `RoleGrounded`. It does not evaluate the global role-fiber condition above. Diagnosing \(W\) as under-discriminating, `RoleGrounded` as semantically disconnected, or the proposal as rejected remains conditional on the proposed oracle and a human disposition, both of which are unresolved. This is calibration of the forge mechanism, not a result about the full source model class.

The full CR role-determination result remains open. The target still lacks a reviewed source-to-neutral mapping, an adjudicated choice between local operational discrimination and distributed network-role readings, a protected tacit/inexplicit positive witness, reviewed \(P_0\) base imports, and an executable substantive repair. Lean readiness for this target is therefore `BLOCKED`. The implementation also fails closed on `PROVISIONALLY_READY`: its schema does not yet encode every obligation required here and it has no typed, digest-bound review-record resolver, so neither an empty blocker list nor plain review-reference strings can trigger that promotion. A future promotion remains blocked pending schema evolution and ledger-backed resolution of all relevant witness, mapping, import, review, and decision records, followed by discharge of every obligation. Further Lean declarations would presently freeze unresolved interpretation choices rather than discharge them.

The supporting engineering discipline and diagnostic frontier are recorded in [SMF-0.1 Architecture](./SMF-0.1_Architecture.md) and [SMF-0.1 Underspecification Atlas](./SMF-0.1_Underspecification_Atlas.md).
