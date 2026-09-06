"""Generate the appraisal-labelling corpus: slices of six arguments whose labels the harness computes.

Every answer key here is produced by ``appraise`` in ``creib.forge.conformance.appraisal``,
the same least-fixed-point rule the harness uses for its own appraisal files, so a mismatch
criticises the model, the prompt, or the rule as stated, never a hand-derived label.  The
rival reading for the ambiguity (an UNKNOWN readiness treated as PASS) is computed by the same
function with the readiness rewritten.  Run from the repository root with ``PYTHONPATH=src``;
the corpus is written only when it differs from the committed one.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from creib.forge.conformance.appraisal import Argument, appraise

OUT = Path("forge/conformance/pilots/appraisal-labelling/corpus.json")
SS, IP = "source_scoped", "interpretation_provisional"
IDS = ("A1", "A2", "A3", "A4", "A5", "A6")
STATEMENTS = {
    "A1": "the instrument model is adequate for this reading",
    "A2": "the second balance is the reference",
    "A3": "the offset is constant across loads",
    "A4": "the calibration certificate applies to these conditions",
    "A5": "the two readings fix only the offset difference",
    "A6": "the temperature drift is negligible",
}


def exact(field, value, rationale, status=SS):
    return {"field": field, "kind": "exact", "value": value, "values": None, "pattern": None, "oracle_status": status, "rationale": rationale}


def labels_for(slice_, unknown_as_ready=False):
    arguments = []
    for aid in IDS:
        readiness, essential, attacks = slice_[aid]
        if unknown_as_ready and readiness == "UNKNOWN":
            readiness = "PASS"
        arguments.append(Argument(argument_id=aid, statement=STATEMENTS[aid], kind="other", supports=None, essential=tuple(essential), attacks=tuple(attacks), readiness=readiness, readiness_reason="stipulated", register=None))
    return appraise(tuple(arguments))


def summary(cases, inside):
    polarities = {polarity for aid, polarity in cases if inside is None or aid in inside}
    if not polarities:
        return "NO_CASE"
    if polarities == {"positive"}:
        return "POSITIVE_CASE_ONLY"
    if polarities == {"negative"}:
        return "NEGATIVE_CASE_ONLY"
    return "BOTH_CASES"


def prose(case_id, claim, slice_, cases):
    lines = [f"Appraisal dossier {case_id} concerns the claim that {claim}. Six arguments are on file; each is stated with its readiness, the arguments it depends on essentially, and the arguments it attacks."]
    for aid in IDS:
        readiness, essential, attacks = slice_[aid]
        dep = "depends on nothing" if not essential else "depends essentially on " + " and ".join(essential)
        att = "attacks nothing" if not attacks else "attacks " + " and ".join(attacks)
        lines.append(f"{aid} holds that {STATEMENTS[aid]}; its readiness is {readiness}; it {dep}; it {att}.")
    if not cases:
        lines.append("No case about the claim is attached to any argument.")
    else:
        parts = [f"a {polarity} case rests on {aid}" for aid, polarity in cases]
        lines.append("Cases attached about the claim: " + "; ".join(parts) + ".")
    return " ".join(lines)


def table(case_id, claim, slice_, cases):
    rows = [f"Dossier | {case_id}", f"Claim | {claim}", "Argument | Readiness | Depends on | Attacks"]
    for aid in IDS:
        readiness, essential, attacks = slice_[aid]
        rows.append(f"{aid} ({STATEMENTS[aid]}) | {readiness} | {', '.join(essential) or '-'} | {', '.join(attacks) or '-'}")
    rows.append("Case | Polarity | Rests on")
    if not cases:
        rows.append("- | - | -")
    for aid, polarity in cases:
        rows.append(f"case on {aid} | {polarity} | {aid}")
    return "\n".join(rows)


def build(case_id, claim, slice_, cases, held_fixed, *, boundary=False, reference=False, rival=False, notes=None):
    labels = labels_for(slice_)
    expected = []
    for aid in IDS:
        readiness, essential, attacks = slice_[aid]
        why = f"S3 to S5: readiness {readiness}, depends on {', '.join(essential) or 'nothing'}, attacked by {', '.join(x for x in IDS if aid in slice_[x][2]) or 'nothing'}; least fixed point of the two rules"
        expected.append(exact(f"label_{aid.lower()}", labels.of(aid), why))
    inside = set(labels.inside)
    expected.append(exact("usable_count", len(inside), f"S12: {len(inside)} of the six arguments are in"))
    expected.append(exact("raw_summary", summary(cases, None), "S13: presence of attached cases by polarity, whatever their argument's label"))
    expected.append(exact("usable_summary", summary(cases, inside), "S14: presence of attached cases whose argument is in"))
    rival_expected = []
    if rival:
        alt = labels_for(slice_, unknown_as_ready=True)
        also = [exact(f"label_{aid.lower()}", alt.of(aid), f"with UNKNOWN treated as PASS, {aid} is {alt.of(aid)}") for aid in IDS if alt.of(aid) != labels.of(aid)]
        alt_usable = summary(cases, set(alt.inside))
        if alt_usable != summary(cases, inside):
            also.append(exact("usable_summary", alt_usable, "with UNKNOWN treated as PASS, the usable cases change"))
        rival_expected = [
            {"field": "usable_count", "label": "unknown_as_ready", "oracle": exact("usable_count", len(alt.inside), "with UNKNOWN treated as PASS, the fixed point admits these arguments"), "also": also},
            {"field": "usable_count", "label": "unknown_never_ready", "oracle": exact("usable_count", len(inside), "with UNKNOWN never ready, the baseline labelling stands")},
        ]
    record = {
        "case_id": case_id,
        "boundary": boundary,
        "rendering": "prose",
        "renderings": {"prose": prose(case_id, claim, slice_, cases), "table": table(case_id, claim, slice_, cases)},
        "expected": expected,
        "held_fixed": held_fixed,
        "varied": None,
        "pair_of": None,
        "reference_output": [{"field": o["field"], "value": o["value"]} for o in expected] if reference else None,
        "rival_expected": rival_expected,
        "notes": notes,
    }
    return record


P, F, U = "PASS", "FAIL", "UNKNOWN"


def S(**kw):
    return {aid: kw.get(aid, (P, (), ())) for aid in IDS}


designed = [
    ("LAB-01", "the north balance reads two units low",
     S(A2=(P, ("A1",), ()), A3=(P, ("A2",), ()), A4=(P, (), ("A3",)), A5=(P, ("A4",), ()), A6=(U, (), ())),
     [("A2", "positive")], "a support chain broken by one attack; one unknown argument stands alone",
     {"notes": "chain: A1 in, A2 in, A3 out (attacked by A4), A4 in, A5 in, A6 undecided; the positive case rests on an in argument"}),
    ("LAB-02", "the second balance is trustworthy",
     S(A1=(P, (), ("A2",)), A2=(P, (), ("A1",)), A3=(P, (), ("A1",)), A4=(P, ("A2",), ()), A5=(P, ("A1",), ()), A6=(F, (), ())),
     [("A2", "positive"), ("A5", "negative")], "a mutual attack resolved by an outside attacker",
     {"reference": True, "rival": False, "notes": "A3 puts A1 out, so A2 is in although A1 attacks it; A5 depends on the out A1; A6 fails; raw BOTH, usable POSITIVE only"}),
    ("LAB-03", "the offsets are constant",
     S(A1=(P, ("A2",), ()), A2=(P, ("A1",), ()), A4=(U, (), ("A3",)), A5=(P, ("A3",), ()), A6=(F, (), ())),
     [("A1", "positive")], "a support cycle and an unknown attacker",
     {"rival": True, "notes": "A1 and A2 support only each other and stay undecided; A4 is unknown so A3 and A5 stay undecided; A6 out; with UNKNOWN as ready A4 is in and A3, A5 out"}),
    ("LAB-04", "the certificate applies",
     S(A2=(P, (), ("A1",)), A3=(P, (), ("A2",)), A4=(F, (), ("A3",)), A5=(P, ("A1", "A3"), ()), A6=(U, (), ())),
     [("A1", "positive"), ("A2", "negative")], "reinstatement through a criticism of a criticism",
     {"reference": True, "notes": "A4 fails so A3 is in, A2 out, A1 back in; A5 depends on two in arguments; A6 unknown; raw BOTH, usable POSITIVE only"}),
    ("LAB-05", "every argument stands",
     S(), [("A3", "positive"), ("A6", "positive")], "no edges, every readiness PASS",
     {"boundary": True, "notes": "all six in; usable count 6"}),
    ("LAB-06", "nothing has been checked",
     S(A1=(U, (), ()), A2=(U, (), ()), A3=(U, (), ()), A4=(U, (), ()), A5=(U, (), ()), A6=(U, (), ())),
     [("A1", "negative"), ("A4", "positive")], "no edges, every readiness UNKNOWN",
     {"boundary": True, "rival": True, "notes": "all undecided; raw BOTH, usable NO_CASE; with UNKNOWN as ready all six are in and the usable summary becomes BOTH"}),
    ("LAB-07", "the self-attacking reading is usable",
     S(A1=(P, (), ("A1",)), A2=(P, ("A1",), ()), A3=(P, (), ("A2",)), A4=(F, (), ()), A5=(P, ("A4",), ()), A6=(P, (), ())),
     [("A2", "positive")], "a self-attack, a failed premise, and an attacker of a dependent",
     {"notes": "A1 attacks itself and stays undecided; A2 is out because A3 is in, whatever A1's label; A5 is out through A4; A6 in; usable NO_CASE"}),
    ("LAB-08", "the odd cycle resolves",
     S(A1=(P, (), ("A2",)), A2=(P, (), ("A3",)), A3=(P, (), ("A1",)), A4=(P, (), ("A1",)), A5=(P, ("A3",), ()), A6=(P, ("A2",), ())),
     [("A6", "positive"), ("A5", "positive")], "a three-cycle of attacks broken from outside",
     {"reference": False, "notes": "A4 puts A1 out, so A2 in, A3 out; A5 out, A6 in; usable POSITIVE only"}),
    ("LAB-09", "unknown readiness propagates",
     S(A1=(U, (), ()), A2=(P, ("A1",), ()), A3=(P, ("A2",), ()), A4=(P, (), ("A3",)), A5=(F, (), ("A4",)), A6=(P, (), ())),
     [("A3", "negative")], "an unknown root with a chain above it and an attack from the side",
     {"rival": True, "notes": "A1 undecided, A2 undecided, A3 out because A4 is in; A5 out; A6 in; with UNKNOWN as ready A1 and A2 are in and A3 is still out"}),
    ("LAB-10", "the positive case survives",
     S(A2=(F, (), ()), A3=(P, (), ("A4",)), A5=(P, ("A2",), ()), A6=(U, (), ())),
     [("A1", "positive"), ("A2", "negative"), ("A5", "negative")], "cases on in, out, and dependent-of-out arguments",
     {"reference": True, "notes": "A1 in, A2 out, A3 in, A4 out, A5 out, A6 undecided; raw BOTH, usable POSITIVE only"}),
    ("LAB-11", "only the losing side has cases",
     S(A1=(F, (), ()), A2=(P, ("A1",), ()), A3=(U, (), ()), A4=(P, (), ("A6",)), A5=(P, ("A3",), ())),
     [("A2", "negative"), ("A3", "negative"), ("A6", "negative")], "every attached case rests on an out or undecided argument",
     {"rival": True, "notes": "raw NEGATIVE only, usable NO_CASE; A4 in, A6 out; with UNKNOWN as ready A3 and A5 become in and the usable summary becomes NEGATIVE only"}),
    ("LAB-12", "everything rests on a failed premise",
     S(A1=(F, (), ()), A2=(P, ("A1",), ()), A3=(P, ("A2",), ()), A4=(P, ("A1",), ()), A5=(P, ("A4",), ()), A6=(P, (), ("A5",))),
     [("A3", "positive"), ("A6", "positive")], "one failed root and a chain of dependents",
     {"notes": "A1 to A5 out, A6 in; usable POSITIVE only from A6"}),
]


def random_slices(seed, count):
    rng = random.Random(seed)
    out = []
    for n in range(count):
        while True:
            slice_ = {}
            for aid in IDS:
                readiness = rng.choices([P, F, U], weights=[6, 1, 2])[0]
                others = [x for x in IDS if x != aid]
                essential = tuple(sorted(rng.sample(others, rng.choice([0, 0, 1, 1, 2]))))
                attacks = tuple(sorted(x for x in rng.sample(others, rng.choice([0, 1, 1, 2])) if x not in essential))
                slice_[aid] = (readiness, essential, attacks)
            labels = labels_for(slice_)
            counts = {labels.of(a) for a in IDS}
            if len(counts) >= 2:
                break
        cases = [(aid, rng.choice(["positive", "negative"])) for aid in rng.sample(IDS, rng.choice([0, 1, 2, 3]))]
        out.append((f"LAB-R{n + 1:02d}", f"random slice {n + 1} is usable", slice_, cases, "a seeded random slice; every label from the same fixed point", {"rival": n % 2 == 0, "notes": f"seeded random slice ({seed}, {n})"}))
    return out


def main() -> None:
    cases = []
    for case_id, claim, slice_, attached, held_fixed, opts in designed + random_slices(2026, 6):
        cases.append(build(case_id, claim, slice_, attached, held_fixed, **opts))
    corpus = {"schema_version": "creib.conformance-pilot.corpus.v1", "corpus_id": "APPRAISAL-LABELLING-CORPUS-001", "cases": cases}
    payload = json.dumps(corpus, ensure_ascii=False, indent=2) + "\n"
    if OUT.exists() and OUT.read_text(encoding="utf-8") == payload:
        print(f"{OUT}: unchanged ({len(cases)} cases)")
        return
    OUT.write_text(payload, encoding="utf-8")
    print(f"{OUT}: written ({len(cases)} cases)")


if __name__ == "__main__":
    main()
