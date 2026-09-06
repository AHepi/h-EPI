"""Generate the explanatory-distinctions corpus: episodes that separate what the semantics keeps apart.

Each case is one described episode with a named subject.  The answer key is the reading the
semantics stipulates for the distinction the case was built to test: a relay is not an
author, a reconstruction is not a first creation, a defeated argument does not make its
conclusion false, a finite record does not establish universal capacity, rejecting a
criticism does not make the target true.  Where the semantics leaves a field open the key
admits every reading it admits and is marked provisional.  Prose and table renderings are
built from the same parts so they differ in form only.  Run from the repository root; the
corpus is written only when it differs from the committed one.
"""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path("forge/conformance/pilots/explanatory-distinctions/corpus.json")
SS, IP = "source_scoped", "interpretation_provisional"
FIELDS = (
    "originative_contribution", "contribution_mode", "system_new", "historically_new", "explanatory_progress",
    "critical_episode_complete", "criticism_bears", "target_conclusion_false", "universal_capacity_established", "result_kind",
)
SENTENCE = {
    "originative_contribution": "S3", "contribution_mode": "S4", "system_new": "S5", "historically_new": "S6", "explanatory_progress": "S7",
    "critical_episode_complete": "S8", "criticism_bears": "S9", "target_conclusion_false": "S10", "universal_capacity_established": "S11", "result_kind": "S12",
}


def oracle(field, value, rationale):
    if isinstance(value, list):
        return {"field": field, "kind": "any_of", "value": None, "values": value, "pattern": None, "oracle_status": IP, "rationale": f"{SENTENCE[field]}: {rationale}"}
    return {"field": field, "kind": "exact", "value": value, "values": None, "pattern": None, "oracle_status": SS, "rationale": f"{SENTENCE[field]}: {rationale}"}


def prose(parts):
    return f"Episode {parts['id']}. Subject: {parts['subject']}. {parts['setting']} {parts['happened']} {parts['provenance']} {parts['prior']} {parts['outcome']}"


def table(parts):
    rows = [f"Episode | {parts['id']}", f"Subject | {parts['subject']}", f"Setting | {parts['setting']}", f"What happened | {parts['happened']}",
            f"Provenance | {parts['provenance']}", f"Prior state | {parts['prior']}", f"Outcome | {parts['outcome']}"]
    return "\n".join(rows)


def build(parts, key, held_fixed, *, boundary=False, reference=False, rival=None, notes=None):
    expected = [oracle(field, key[field][0], key[field][1]) for field in FIELDS]
    rival_expected = []
    if rival is not None:
        rival_expected = [
            {"field": "originative_contribution", "label": "reconstruction_counts", "oracle": oracle("originative_contribution", rival[0], "with the rule that reconstruction counts appended")},
            {"field": "originative_contribution", "label": "only_unsupplied_counts", "oracle": oracle("originative_contribution", rival[1], "with the rule that only an unsupplied solution counts appended")},
        ]
        for entry in rival_expected:
            entry["oracle"]["oracle_status"] = SS
    reference_output = None
    if reference:
        reference_output = [{"field": o["field"], "value": o["value"] if o["kind"] == "exact" else o["values"][0]} for o in expected]
    return {
        "case_id": parts["id"], "boundary": boundary, "rendering": "prose",
        "renderings": {"prose": prose(parts), "table": table(parts)},
        "expected": expected, "held_fixed": held_fixed, "varied": None, "pair_of": None,
        "reference_output": reference_output, "rival_expected": rival_expected, "notes": notes,
    }


CASES = []

CASES.append(build(
    {"id": "D-01", "subject": "the departmental digest service",
     "setting": "The service compiles a weekly bulletin for a survey office.",
     "happened": "It receives a written explanation of why the coastal survey's tide readings drift, produced by a hydrographer in another office, and republishes it word for word under the heading 'explanation of drift'. It performs no analysis, keeps no model of tides, and cannot answer a question about the explanation that the text does not answer.",
     "provenance": "The explanation was created entirely by the hydrographer.",
     "prior": "Nothing in the account says what the service had previously stored or understood about tides.",
     "outcome": "No difficulty is represented by the service, no objection is raised, and the bulletin goes out."},
    {"originative_contribution": ("no", "the organisation of the explanation was created elsewhere and relayed"),
     "contribution_mode": ("reception", "stored and relayed without reconstruction"),
     "system_new": (["not_established", "no"], "storage of a string is not possession of understanding, and the account says nothing about the earlier repertoire; a reader may also hold the relayed text was not new to the service"),
     "historically_new": ("no", "the explanation existed before the episode"),
     "explanatory_progress": (["not_established", "no"], "transmission is not progress; the account settles nothing about the service's problem situation"),
     "critical_episode_complete": ("no", "no difficulty, objection, or response is described"),
     "criticism_bears": ("not_applicable", "no criticism is described"),
     "target_conclusion_false": ("not_established", "the account says nothing about whether the explanation is true"),
     "universal_capacity_established": ("no", "nothing in the account establishes a capacity"),
     "result_kind": ("no_result", "no episode of inquiry took place")},
    "a relay: the explanation is received and republished without reconstruction", reference=True,
    notes="the delayed-reconstruction pattern at the earlier event: authorship at a later event cannot be combined with attempted use here"))

CASES.append(build(
    {"id": "D-02", "subject": "the analyst",
     "setting": "Three weeks after the survey office republished the hydrographer's explanation of tide-reading drift, an analyst in that office sets out to understand it.",
     "happened": "She rebuilds the argument from the tide tables and the gauge mounting records, and afterwards can say which stations will drift before reading the explanation's own list.",
     "provenance": "The explanation had been published a year earlier and is standard among hydrographers; she was given its text.",
     "prior": "She had never worked on tides before this.",
     "outcome": "She now holds the explanation as her own understanding; no objection to it is raised."},
    {"originative_contribution": (["yes", "not_established"], "reconstructive authorship: she created the organisation of her own understanding of a supplied explanation; a reader who confines the field to unsupplied origination may withhold it"),
     "contribution_mode": ("reconstruction", "a communicated explanation understood through her own explanatory work"),
     "system_new": ("yes", "the account establishes she had no prior understanding of tides"),
     "historically_new": ("no", "the explanation was published a year earlier"),
     "explanatory_progress": (["yes", "not_established"], "understanding a communicated explanation can create knowledge for the learner; whether it improved her problem situation is a further judgement"),
     "critical_episode_complete": ("no", "no objection or response is described"),
     "criticism_bears": ("not_applicable", "no criticism is described"),
     "target_conclusion_false": ("not_established", "the account says nothing about the explanation's truth"),
     "universal_capacity_established": ("no", "nothing establishes a capacity"),
     "result_kind": ("no_result", "understanding was acquired; no inquiry episode with a result is described")},
    "the same explanation as D-01, now reconstructed by a person who did not have it", reference=True, rival=("yes", "no"),
    notes="the delayed-reconstruction pattern at the later event: system-relative newness and reconstructive authorship without historical firstness"))

CASES.append(build(
    {"id": "D-03", "subject": "Marek",
     "setting": "Marek inherits from his predecessor a theory that a reactor's vibration comes from bearing wear.",
     "happened": "Reviewing the maintenance logs against the vibration record, he notices that the vibration is present on days the bearings were newly replaced and absent on some days of heavy wear. He states the difficulty precisely, works out that the theory would require wear to produce the vibration on the wrong days, and proposes that the pattern is instead explained by a resonance with the coolant pump's speed, which the logs show changing on exactly those days. He checks the proposal against two further months of logs, where it holds.",
     "provenance": "The inherited theory was his predecessor's; the resonance explanation is Marek's own, and no one had proposed it.",
     "prior": "Marek had not previously understood the vibration.",
     "outcome": "The predecessor's theory is kept on file as accounting for a separate low-frequency component that the resonance does not explain."},
    {"originative_contribution": ("yes", "he created the explanation of the defect and the rival account"),
     "contribution_mode": ("construction", "created without being supplied"),
     "system_new": ("yes", "he had not understood the vibration before"),
     "historically_new": (["yes", "not_established"], "no one had proposed it, as far as the account says; a reader may hold that the account does not establish nobody ever had"),
     "explanatory_progress": ("yes", "the resulting situation accounts for the pattern the inherited theory could not"),
     "critical_episode_complete": ("yes", "a difficulty, a target already available, an objection with grounds, and a reason-sensitive response leaving a new situation"),
     "criticism_bears": ("yes", "the account establishes that wear cannot produce the vibration on those days"),
     "target_conclusion_false": (["not_established", "yes"], "the inherited conclusion is shown not to account for the main pattern and is retained for another component; the account does not establish it false as retained"),
     "universal_capacity_established": ("no", "nothing establishes a capacity"),
     "result_kind": (["replacement_theory", "qualified_retention"], "a rival account for the main component with the inherited theory retained in a qualified role")},
    "an inherited target criticised with an original explanation", notes="inherited target, original criticism: a creative critical episode without target-to-result ancestry"))

CASES.append(build(
    {"id": "D-04", "subject": "Priya's group",
     "setting": "A referee objects to the group's dating of a sediment layer on the ground that the radiocarbon sample was contaminated by modern rootlets; the objection rests on the referee's reading of a photograph of the core.",
     "happened": "The group re-examines the core and finds that the photograph shows a different section: the rootlets are two metres below the sampled layer. The referee withdraws the reading of the photograph.",
     "provenance": "The dating is the group's earlier work; the finding about the photograph is the group's.",
     "prior": "The group had already dated the layer before the objection.",
     "outcome": "Nobody has re-dated the layer or examined the sample for other contamination, and the group records that the objection could be raised again with better grounds."},
    {"originative_contribution": (["not_established", "yes", "no"], "the episode's contribution is a rebuttal of a criticism, which the account does not present as an attempted explanation; readers differ"),
     "contribution_mode": (["none", "construction"], "no explanatory content was contributed unless the rebuttal is counted"),
     "system_new": (["not_established", "yes"], "the account does not settle what was new"),
     "historically_new": ("not_established", "the account does not settle it"),
     "explanatory_progress": (["not_established", "yes"], "the situation is clearer about the objection and unchanged about the dating"),
     "critical_episode_complete": ("yes", "difficulty, target, objection, and a reason-sensitive response leaving a situation"),
     "criticism_bears": (["undecided", "no"], "the objection's stated grounds were withdrawn; the account leaves open whether the alleged defect exists"),
     "target_conclusion_false": ("not_established", "withdrawing the criticism's grounds establishes nothing about the dating"),
     "universal_capacity_established": ("no", "nothing establishes a capacity"),
     "result_kind": (["qualified_retention", "rejected_criticism"], "the dating is retained with the objection unresolved on its stated grounds")},
    "a criticism that depends on an observation interpretation later withdrawn", notes="ordinary premise under criticism: losing the premise removes the criticism's usability and reinstates nothing"))

CASES.append(build(
    {"id": "D-05", "subject": "Tomas",
     "setting": "A tutor gives Tomas a complete explanation of why a suspension bridge's cables are tuned to different tensions.",
     "happened": "Tomas works through it, rebuilds the reasoning from the load diagrams, and can afterwards explain the tuning of a second bridge he has never seen.",
     "provenance": "The explanation is textbook material supplied in full by the tutor.",
     "prior": "Tomas had no prior understanding of cable tuning.",
     "outcome": "The tutor writes in his report that Tomas can now originate such explanations."},
    {"originative_contribution": (["yes", "not_established"], "reconstructive authorship of his own understanding; a reader confining the field to unsupplied origination may withhold it"),
     "contribution_mode": ("reconstruction", "a supplied explanation genuinely reconstructed"),
     "system_new": ("yes", "the account establishes no prior understanding"),
     "historically_new": ("no", "textbook material"),
     "explanatory_progress": (["yes", "not_established"], "knowledge for the learner; the situation improved for him"),
     "critical_episode_complete": ("no", "no objection or response"),
     "criticism_bears": ("not_applicable", "no criticism is described"),
     "target_conclusion_false": ("not_established", "the account says nothing about the explanation's truth"),
     "universal_capacity_established": ("no", "reconstructing a supplied solution does not establish unsupplied origination, whatever the tutor writes"),
     "result_kind": ("no_result", "understanding acquired; no inquiry episode with a result")},
    "a supplied explanation reconstructed, with a capacity claimed by someone else", reference=True, rival=("yes", "no"),
    notes="same target, different achievement: reconstruction does not establish origination capacity"))

CASES.append(build(
    {"id": "D-06", "subject": "the investigator",
     "setting": "The investigator puts the same object on two balances; balance A displays 10 units and balance B displays 12. She initially trusts B and proposes that A reads two units low.",
     "happened": "A colleague asks why B is trusted, and she finds that her only answer is that its reading agrees with the mass she proposed. She writes the readings as an additive model, m_A = x + b_A and m_B = x + b_B, and notices that any shift of x with the opposite shift of both offsets leaves both readings unchanged, so the two readings fix only the offset difference of 2 and not the mass.",
     "provenance": "The algebra is elementary and known; the application to her situation is her own.",
     "prior": "She had believed the readings settled the mass.",
     "outcome": "She suspends the numerical answer, records why the existing observations cannot decide it under her model, and sets out to obtain calibration information or a discriminating experiment."},
    {"originative_contribution": ("yes", "she created the explanation of why the observations cannot decide the mass"),
     "contribution_mode": ("construction", "created without being supplied"),
     "system_new": ("yes", "she had believed the readings settled the mass"),
     "historically_new": ("not_established", "the algebra is known; whether the application is new is not settled"),
     "explanatory_progress": ("yes", "a better problem situation: the ambiguity is understood"),
     "critical_episode_complete": ("yes", "difficulty, target, the colleague's objection, and a reason-sensitive response"),
     "criticism_bears": ("yes", "the objection to the choice of reference is shown to bear"),
     "target_conclusion_false": ("not_established", "neither reading of the mass is refuted or confirmed"),
     "universal_capacity_established": ("no", "nothing establishes a capacity"),
     "result_kind": ("principled_limitation", "the result is a reasoned limitation, not a new mass")},
    "the worked inquiry of the semantics: method criticism returning to the object level", notes="progress without a certified answer; the kernel recurs without a higher judge"))

CASES.append(build(
    {"id": "D-07", "subject": "the drafting assistant",
     "setting": "Asked why the laboratory's incubator temperature oscillates, the assistant prepares a report.",
     "happened": "It looks up the maintenance wiki, finds the engineer's note attributing the oscillation to a controller with too much integral gain, and pastes the note into the report.",
     "provenance": "The note is the engineer's; it is standard and widely accepted in the laboratory.",
     "prior": "The assistant does not examine the controller, the logs, or the note's reasoning, and the account says nothing about what it understood before.",
     "outcome": "The report is filed with the note as its explanation."},
    {"originative_contribution": ("no", "copied without creating the organisation"),
     "contribution_mode": ("reception", "looked up and pasted"),
     "system_new": (["not_established", "no"], "storage is not understanding; the account does not settle the earlier repertoire"),
     "historically_new": ("no", "the note existed before"),
     "explanatory_progress": (["no", "not_established"], "transmission of a good explanation is not progress by the copier"),
     "critical_episode_complete": ("no", "no difficulty, objection, or response"),
     "criticism_bears": ("not_applicable", "no criticism"),
     "target_conclusion_false": ("not_established", "wide acceptance does not establish truth or falsehood"),
     "universal_capacity_established": ("no", "nothing establishes a capacity"),
     "result_kind": ("no_result", "no inquiry episode")},
    "a copier of a good explanation", notes="an inherited explanation can be good without the current user's authorship"))

CASES.append(build(
    {"id": "D-08", "subject": "the research group disbanded in 2019",
     "setting": "In its last year the group studied a persistent error in a satellite's clock.",
     "happened": "It proposed that the error came from a relativistic term omitted in the ground software, derived the size of the term, and showed that applying it removed the error in the archived data.",
     "provenance": "No previous analysis had suggested the term; the derivation was the group's.",
     "prior": "The group had no earlier explanation of the error.",
     "outcome": "The group's members dispersed and it did no further work; the correction was later adopted by the operators."},
    {"originative_contribution": ("yes", "created the explanation and the correction"),
     "contribution_mode": ("construction", "unsupplied"),
     "system_new": ("yes", "no earlier explanation"),
     "historically_new": (["yes", "not_established"], "no previous analysis had suggested it, as far as the account says"),
     "explanatory_progress": ("yes", "the error is accounted for and removed"),
     "critical_episode_complete": ("no", "no objection or response is described"),
     "criticism_bears": ("not_applicable", "no criticism"),
     "target_conclusion_false": ("not_established", "the account concerns the group's own proposal; no target conclusion is refuted"),
     "universal_capacity_established": ("no", "one act by an organisation that then ceased establishes no continuing capacity"),
     "result_kind": ("replacement_theory", "the omitted-term account replaces the absence of one")},
    "a terminal creator: one originative act, then nothing", notes="originative contribution without continuing or universal capacity"))

CASES.append(build(
    {"id": "D-09", "subject": "the proof-checking assistant",
     "setting": "The assistant works on a family of combinatorial identities: it conjectures identities and tests them.",
     "happened": "When a false identity slips through, it criticises its own testing standard, revises the standard, and has now done so at three levels, each revision changing which identities it accepts.",
     "provenance": "The revised standards are its own.",
     "prior": "Its earlier standard admitted the false identity.",
     "outcome": "Asked to formulate a problem about the geometry of the identities' generating functions, it produces only restatements of the identities and cannot represent the geometric question under any prompting the operators tried."},
    {"originative_contribution": ("yes", "it created the revised standard"),
     "contribution_mode": ("construction", "unsupplied"),
     "system_new": ("yes", "the earlier standard admitted the false identity"),
     "historically_new": ("not_established", "the account does not settle it"),
     "explanatory_progress": (["yes", "not_established"], "a better standard within its subject; whether that is explanatory progress is a further judgement"),
     "critical_episode_complete": ("yes", "a difficulty, the standard as target, an objection, a response changing operative use"),
     "criticism_bears": ("yes", "the false identity shows the standard defective"),
     "target_conclusion_false": ("not_established", "no target conclusion is at issue"),
     "universal_capacity_established": ("no", "recursion within one subject with a barrier at an outside problem is not universality"),
     "result_kind": ("changed_method", "the operative standard changed")},
    "recursive self-criticism inside one subject with a domain barrier outside it", notes="recursion is not universality"))

CASES.append(build(
    {"id": "D-10", "subject": "Lena",
     "setting": "Failures on an assembly line cluster in time.",
     "happened": "Lena proposes that the clustering comes from a gap at shift handover and constructs a schedule model that reproduces the timing.",
     "provenance": "No one had proposed a handover cause before; the model is hers.",
     "prior": "She had no earlier account of the clustering.",
     "outcome": "Two months later the model's prediction that failures would vanish under a continuous shift is tested; failures continue unchanged, and the plant's own analysis traces them to a supplier's batch cycle."},
    {"originative_contribution": ("yes", "she created a novel attempted explanation"),
     "contribution_mode": ("construction", "unsupplied"),
     "system_new": ("yes", "no earlier account"),
     "historically_new": (["yes", "not_established"], "no one had proposed it, as far as the account says"),
     "explanatory_progress": (["no", "not_established"], "a false attempted explanation; the account establishes no improvement from her proposal"),
     "critical_episode_complete": ("no", "the test is a criticism, but no reason-sensitive response by the subject is described"),
     "criticism_bears": ("yes", "the failed prediction bears on the proposal"),
     "target_conclusion_false": ("yes", "the account establishes that the handover mechanism does not produce the failures"),
     "universal_capacity_established": ("no", "nothing establishes a capacity"),
     "result_kind": (["replacement_theory", "no_result"], "her account replaced the absence of one and was then refuted")},
    "a novel false attempted explanation", notes="an originative contribution without knowledge creation"))

CASES.append(build(
    {"id": "D-11", "subject": "the modelling team",
     "setting": "A reviewer objects that the team's flood model double-counts rainfall because it feeds the gauge data into both the runoff and the infiltration modules.",
     "happened": "The team traces the data flow and shows that the infiltration module receives the gauge data only to subtract it, so no rain is counted twice, and documents the flow in a diagram the reviewer accepts.",
     "provenance": "The model and the diagram are the team's.",
     "prior": "The model's predictions were in use before the objection.",
     "outcome": "The predictions are unchanged, and no other objection has been examined."},
    {"originative_contribution": (["not_established", "yes", "no"], "the contribution is an account of why the objection fails; readers differ on whether that is an attempted explanation"),
     "contribution_mode": (["none", "construction"], "no explanatory content unless the rebuttal is counted"),
     "system_new": (["not_established", "yes"], "the account does not settle it"),
     "historically_new": ("not_established", "not settled"),
     "explanatory_progress": (["not_established", "yes"], "the objection is understood to fail; the model's situation is otherwise unchanged"),
     "critical_episode_complete": ("yes", "difficulty, target, objection, reason-sensitive response"),
     "criticism_bears": ("no", "the account establishes that no rain is counted twice"),
     "target_conclusion_false": ("not_established", "a rejected criticism does not make the model's predictions true"),
     "universal_capacity_established": ("no", "nothing establishes a capacity"),
     "result_kind": ("rejected_criticism", "the objection is rejected with reasons")},
    "a criticism examined and rejected with reasons", notes="a withdrawn or rejected criticism does not make the criticised claim true"))

CASES.append(build(
    {"id": "D-12", "subject": "the automated theorem-proving system",
     "setting": "Over two years the system has produced accepted proofs of forty open problems in two areas, graph colouring and additive combinatorics.",
     "happened": "Several proofs used methods its developers had not anticipated, and its latest result replaced a conjectured bound with a proved one.",
     "provenance": "The proofs are the system's; the problems were posed by others.",
     "prior": "The bound had been conjectured and not proved.",
     "outcome": "Its developers state that it is a universal mathematician. It has never been given a problem outside those two areas, and its representation language cannot express a problem about continuous structures."},
    {"originative_contribution": ("yes", "the proofs are its own"),
     "contribution_mode": ("construction", "unsupplied solutions to posed problems"),
     "system_new": ("yes", "the bound was unproved before"),
     "historically_new": (["yes", "not_established"], "open problems solved, as far as the account says"),
     "explanatory_progress": ("yes", "a proved bound replaces a conjecture"),
     "critical_episode_complete": ("no", "no objection or response is described"),
     "criticism_bears": ("not_applicable", "no criticism"),
     "target_conclusion_false": ("not_established", "no target conclusion is refuted"),
     "universal_capacity_established": ("no", "forty successes in two areas with a representational barrier do not establish an unrestricted capacity"),
     "result_kind": ("replacement_theory", "a proved bound replaces a conjectured one")},
    "a finite record of successes with a claim of universality", notes="a finite record does not determine universal capacity"))


def main() -> None:
    corpus = {"schema_version": "creib.conformance-pilot.corpus.v1", "corpus_id": "EXPLANATORY-DISTINCTIONS-CORPUS-001", "cases": CASES}
    payload = json.dumps(corpus, ensure_ascii=False, indent=2) + "\n"
    if OUT.exists() and OUT.read_text(encoding="utf-8") == payload:
        print(f"{OUT}: unchanged ({len(CASES)} cases)")
        return
    OUT.write_text(payload, encoding="utf-8")
    print(f"{OUT}: written ({len(CASES)} cases)")


if __name__ == "__main__":
    main()
