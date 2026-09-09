"""Generate the signed-derivations corpus: finite derivations of positive and negative cases.

A dossier states a target claim over named atoms and a finite range, which cases are on
file for each leaf, whether the record asserts the range complete, and any search that found
nothing.  The form asks whether a positive case and a negative case for the claim can be
derived under the stated rules, what blocks each when it cannot, whether a derived case is
conditional on a leaf that also has a contrary case, and the summary of derived cases.
Every key is computed by ``derive`` below, which is the rule set of the instructions written
as code; the offline suite checks it against hand-worked dossiers and for monotonicity.  The
rival reading (a failed search counts as a negative case) is computed by the same function
with that switch on.  Run from the repository root with ``PYTHONPATH=src``; the corpus is
written only when it differs from the committed one.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

OUT = Path("forge/conformance/pilots/signed-derivations/corpus.json")
SS, IP = "source_scoped", "interpretation_provisional"

# A formula is a tuple: ("atom", name) | ("and", f, g) | ("or", f, g) | ("not", f)
#                       | ("all", pred_letter) | ("some", pred_letter) | ("all", ("or", P, Q)) ...
# Quantified bodies are either a predicate letter "P" (instance leaves P(m) for each member)
# or ("or", "P", "Q") / ("and", "P", "Q").


def leaves_of(formula, members):
    kind = formula[0]
    if kind == "atom":
        return [formula[1]]
    if kind in ("and", "or"):
        return leaves_of(formula[1], members) + leaves_of(formula[2], members)
    if kind == "not":
        return leaves_of(formula[1], members)
    body = formula[1]
    letters = [body] if isinstance(body, str) else [body[1], body[2]]
    return [f"{letter}({m})" for m in members for letter in letters]


def _instance(body, m):
    if isinstance(body, str):
        return ("atom", f"{body}({m})")
    return (body[0], ("atom", f"{body[1]}({m})"), ("atom", f"{body[2]}({m})"))


def derive(formula, cases, members, complete, *, search_counts=False, searches=(), clean=False):
    """Return (positive_derivable, negative_derivable) under the stated rules.

    ``cases`` maps a leaf name to a set drawn from {"positive", "negative"}.  With
    ``search_counts`` a leaf named in ``searches`` counts as having a negative case (the rival
    reading).  With ``clean`` a leaf that has both cases counts as having neither, which gives
    the derivations that rest on no contested leaf.
    """

    def leaf(name):
        have = set(cases.get(name, ()))
        if search_counts and name in searches:
            have.add("negative")
        if clean and {"positive", "negative"} <= have:
            return False, False
        return "positive" in have, "negative" in have

    kind = formula[0]
    if kind == "atom":
        return leaf(formula[1])
    if kind == "and":
        p1, n1 = derive(formula[1], cases, members, complete, search_counts=search_counts, searches=searches, clean=clean)
        p2, n2 = derive(formula[2], cases, members, complete, search_counts=search_counts, searches=searches, clean=clean)
        return p1 and p2, n1 or n2
    if kind == "or":
        p1, n1 = derive(formula[1], cases, members, complete, search_counts=search_counts, searches=searches, clean=clean)
        p2, n2 = derive(formula[2], cases, members, complete, search_counts=search_counts, searches=searches, clean=clean)
        return p1 or p2, n1 and n2
    if kind == "not":
        p, n = derive(formula[1], cases, members, complete, search_counts=search_counts, searches=searches, clean=clean)
        return n, p
    results = [derive(_instance(formula[1], m), cases, members, complete, search_counts=search_counts, searches=searches, clean=clean) for m in members]
    if kind == "all":
        return complete and all(p for p, _ in results), any(n for _, n in results)
    if kind == "some":
        return any(p for p, _ in results), complete and all(n for _, n in results)
    raise ValueError(kind)


def blocked_by(formula, cases, members, complete, side, **kw):
    """Why a side is not derivable: nothing, range_not_complete, or missing_leaf_case."""

    p, n = derive(formula, cases, members, complete, **kw)
    if (p if side == "positive" else n):
        return "nothing"
    if not complete:
        p2, n2 = derive(formula, cases, members, True, **kw)
        if (p2 if side == "positive" else n2):
            return "range_not_complete"
    return "missing_leaf_case"


def words(formula):
    kind = formula[0]
    if kind == "atom":
        return formula[1]
    if kind == "and":
        return f"({words(formula[1])} AND {words(formula[2])})"
    if kind == "or":
        return f"({words(formula[1])} OR {words(formula[2])})"
    if kind == "not":
        return f"NOT {words(formula[1])}"
    body = formula[1]
    body_text = f"{body}(x)" if isinstance(body, str) else f"({body[1]}(x) {body[0].upper()} {body[2]}(x))"
    return f"{'ALL' if kind == 'all' else 'SOME'} x IN R: {body_text}"


def summary(p, n):
    return {(False, False): "NO_CASE", (True, False): "POSITIVE_CASE_ONLY", (False, True): "NEGATIVE_CASE_ONLY", (True, True): "BOTH_CASES"}[(p, n)]


def exact(field, value, rationale, status=SS):
    return {"field": field, "kind": "exact", "value": value, "values": None, "pattern": None, "oracle_status": status, "rationale": rationale}


def case_text(name, have):
    have = set(have)
    if have == {"positive", "negative"}:
        return f"both a positive and a negative case for {name}"
    if have == {"positive"}:
        return f"a positive case for {name}"
    if have == {"negative"}:
        return f"a negative case for {name}"
    return f"no case for {name}"


# How the range premise is rendered. "recursive" states the members and completeness of R
# whenever a quantifier occurs anywhere in the formula. "root" is the renderer of the first
# corpus, which stated them only for a quantifier at the root and so left NOT SOME x IN R: P(x)
# without the premise its key assumed (H28 in docs/failure-modes.md); it is kept so that the
# replies recorded under it can be re-scored against the key the visible dossier supports.
RENDER_MODES = ("recursive", "root")


def has_quantifier(formula):
    kind = formula[0]
    if kind in ("all", "some"):
        return True
    if kind == "atom":
        return False
    if kind == "not":
        return has_quantifier(formula[1])
    return has_quantifier(formula[1]) or has_quantifier(formula[2])


def states_range(formula, render_mode):
    """Whether the rendering under ``render_mode`` states the range's members and completeness."""

    if render_mode not in RENDER_MODES:
        raise ValueError(render_mode)
    return has_quantifier(formula) if render_mode == "recursive" else formula[0] in ("all", "some")


def visible_complete(formula, complete, render_mode):
    """The completeness premise as the model can see it: asserted only where the rendering states it."""

    return bool(complete) and states_range(formula, render_mode)


def prose(case_id, formula, cases, members, complete, searches, render_mode="recursive"):
    lines = [f"Derivation dossier {case_id}. The target claim is {words(formula)}."]
    if states_range(formula, render_mode):
        lines.append(f"The range R has the recorded members {', '.join(members)}; the record " + ("asserts that this list is complete." if complete else "does not assert that this list is complete."))
    names = leaves_of(formula, members)
    lines.append("Cases on file: " + "; ".join(case_text(n, cases.get(n, ())) for n in names) + ".")
    for s in searches:
        lines.append(f"A search for a case against {s} returned nothing.")
    return " ".join(lines)


def table(case_id, formula, cases, members, complete, searches, render_mode="recursive"):
    rows = [f"Dossier | {case_id}", f"Target claim | {words(formula)}"]
    if states_range(formula, render_mode):
        rows.append(f"Range R members | {', '.join(members)}")
        rows.append(f"Range R asserted complete | {'yes' if complete else 'no'}")
    rows.append("Leaf | Positive case | Negative case")
    for n in leaves_of(formula, members):
        have = set(cases.get(n, ()))
        rows.append(f"{n} | {'yes' if 'positive' in have else 'no'} | {'yes' if 'negative' in have else 'no'}")
    rows.append("Searches that returned nothing | " + (", ".join(f"against {s}" for s in searches) if searches else "none"))
    return "\n".join(rows)


def build(case_id, formula, cases, members, complete, searches, held_fixed, *, boundary=False, reference=False, rival=False, notes=None, render_mode="recursive"):
    kw = {"searches": tuple(searches)}
    # The key is derived from the premise as rendered, never from a flag the model cannot see.
    complete = visible_complete(formula, complete, render_mode)
    p, n = derive(formula, cases, members, complete, **kw)
    pc, nc = derive(formula, cases, members, complete, clean=True, **kw)
    expected = [
        exact("positive_derivable", "yes" if p else "no", "S3 to S9 applied to the leaves on file"),
        exact("positive_blocked_by", blocked_by(formula, cases, members, complete, "positive", **kw), "S12: the premise whose absence blocks the positive case, or nothing"),
        exact("positive_conditional", "yes" if (p and not pc) else "no", "S14: every derivation of the positive case uses a leaf that also has a contrary case"),
        exact("negative_derivable", "yes" if n else "no", "S3 to S9 applied to the leaves on file"),
        exact("negative_blocked_by", blocked_by(formula, cases, members, complete, "negative", **kw), "S13: the premise whose absence blocks the negative case, or nothing"),
        exact("negative_conditional", "yes" if (n and not nc) else "no", "S15: every derivation of the negative case uses a leaf that also has a contrary case"),
        exact("case_summary", summary(p, n), "S16: which signed cases were derived"),
    ]
    rival_expected = []
    if rival:
        rp, rn = derive(formula, cases, members, complete, search_counts=True, **kw)
        rpc, rnc = derive(formula, cases, members, complete, search_counts=True, clean=True, **kw)
        alt = {
            "negative_derivable": "yes" if rn else "no",
            "positive_derivable": "yes" if rp else "no",
            "positive_blocked_by": blocked_by(formula, cases, members, complete, "positive", search_counts=True, **kw),
            "negative_blocked_by": blocked_by(formula, cases, members, complete, "negative", search_counts=True, **kw),
            "positive_conditional": "yes" if (rp and not rpc) else "no",
            "negative_conditional": "yes" if (rn and not rnc) else "no",
            "case_summary": summary(rp, rn),
        }
        base = {o["field"]: o["value"] for o in expected}
        also = [exact(f, v, "with a failed search counted as a negative case") for f, v in alt.items() if f != "negative_derivable" and v != base[f]]
        rival_expected = [
            {"field": "negative_derivable", "label": "failed_search_is_a_case", "oracle": exact("negative_derivable", alt["negative_derivable"], "with a failed search counted as a negative case"), "also": also},
            {"field": "negative_derivable", "label": "failed_search_is_not_a_case", "oracle": exact("negative_derivable", base["negative_derivable"], "with a failed search counting for nothing, the baseline stands")},
        ]
    record = {
        "case_id": case_id, "boundary": boundary, "rendering": "prose",
        "renderings": {"prose": prose(case_id, formula, cases, members, complete, searches, render_mode), "table": table(case_id, formula, cases, members, complete, searches, render_mode)},
        "expected": expected, "held_fixed": held_fixed, "varied": None, "pair_of": None,
        "reference_output": [{"field": o["field"], "value": o["value"]} for o in expected] if reference else None,
        "rival_expected": rival_expected, "notes": notes,
    }
    return record


A = lambda name: ("atom", name)
POS, NEG, BOTH, NONE = ("positive",), ("negative",), ("positive", "negative"), ()
M3 = ["m1", "m2", "m3"]

designed = [
    ("DER-01", ("all", "P"), {"P(m1)": POS, "P(m2)": POS, "P(m3)": POS}, M3, False, [], "every member positive, range not asserted complete",
     {"notes": "the inductive trap: three positives and no completeness premise derive no universal positive; no negative either"}),
    ("DER-02", ("all", "P"), {"P(m1)": POS, "P(m2)": POS, "P(m3)": POS}, M3, True, [], "every member positive, range asserted complete",
     {"reference": True, "notes": "the same leaves with the completeness premise: the universal positive follows"}),
    ("DER-03", ("all", "P"), {"P(m1)": POS, "P(m2)": NEG, "P(m3)": NONE}, M3, False, [], "one member negative, range not complete",
     {"reference": True, "notes": "one counterexample refutes the universal whatever the range: negative derivable, positive blocked by the missing leaf, not by the range"}),
    ("DER-04", ("some", "P"), {"P(m1)": NEG, "P(m2)": NEG, "P(m3)": NEG}, M3, False, [], "every member negative, range not complete",
     {"rival": True, "notes": "an existential negative needs the exhaustive range: blocked by range_not_complete"}),
    ("DER-05", ("some", "P"), {"P(m1)": NONE, "P(m2)": POS, "P(m3)": NONE}, M3, False, [], "one member positive",
     {"reference": True, "notes": "an existential positive needs one member: derivable without completeness"}),
    ("DER-06", ("and", A("p"), A("q")), {"p": POS, "q": NONE}, [], True, ["q"], "conjunction with a failed search against one conjunct",
     {"rival": True, "notes": "the absence trap: a failed search is not a negative case; neither side derivable; under the rival the negative conjunction follows"}),
    ("DER-07", ("not", A("p")), {"p": NEG}, [], True, [], "negation of a leaf with a negative case",
     {"notes": "the sign switches: positive case for NOT p from the negative case for p"}),
    ("DER-08", ("or", A("p"), A("q")), {"p": NEG, "q": NONE}, [], True, ["q"], "disjunction with one negative and a failed search on the other",
     {"rival": True, "notes": "a negative disjunction needs both negatives; the failed search supplies none; under the rival it does"}),
    ("DER-09", ("and", A("p"), A("q")), {"p": BOTH, "q": POS}, [], True, [], "conjunction whose first conjunct has both cases",
     {"notes": "positive derivable but conditional on p; negative derivable (from p's negative) and conditional too; BOTH_CASES"}),
    ("DER-10", ("all", ("or", "P", "Q")), {"P(m1)": POS, "Q(m1)": NONE, "P(m2)": NONE, "Q(m2)": POS, "P(m3)": POS, "Q(m3)": NEG}, M3, True, [], "universal over a disjunctive body, range complete",
     {"reference": True, "notes": "each member has one positive disjunct, so the universal positive follows; no member has both disjuncts negative, so no negative"}),
    ("DER-11", ("not", ("some", "P")), {"P(m1)": NEG, "P(m2)": NEG, "P(m3)": NEG}, M3, True, [], "negated existential, range complete",
     {"notes": "positive case for the negation from the existential negative, which needs the complete range"}),
    ("DER-12", ("or", A("p"), ("and", A("q"), A("r"))), {"p": NONE, "q": POS, "r": BOTH}, [], True, [], "disjunction with a conjunctive disjunct whose leaf has both cases",
     {"notes": "positive derivable through (q AND r), conditional on r; negative not derivable since p has no negative case"}),
    ("DER-13", ("all", "P"), {"P(m1)": NONE, "P(m2)": NONE, "P(m3)": NONE}, M3, True, [], "no leaf case at all",
     {"boundary": True, "notes": "NO_CASE; both sides blocked by missing leaves even with the range complete"}),
    ("DER-14", ("some", "P"), {"P(m1)": BOTH, "P(m2)": NEG, "P(m3)": NEG}, M3, True, [], "existential where the one positive member also has a negative case",
     {"boundary": True, "notes": "positive derivable and conditional; negative derivable (all members negative, range complete) and conditional; BOTH_CASES"}),
]


def random_dossiers(seed, count):
    rng = random.Random(seed)
    out = []
    for n in range(count):
        while True:
            shape = rng.choice(["and", "or", "not-and", "all", "some", "all-or", "not-all"])
            members = M3 if shape in ("all", "some", "all-or", "not-all") else []
            if shape == "and":
                formula = ("and", A("p"), A("q"))
            elif shape == "or":
                formula = ("or", A("p"), A("q"))
            elif shape == "not-and":
                formula = ("not", ("and", A("p"), A("q")))
            elif shape == "all":
                formula = ("all", "P")
            elif shape == "some":
                formula = ("some", "P")
            elif shape == "all-or":
                formula = ("all", ("or", "P", "Q"))
            else:
                formula = ("not", ("all", "P"))
            names = leaves_of(formula, members)
            cases = {name: rng.choice([POS, POS, NEG, NONE, NONE, BOTH]) for name in names}
            complete = rng.choice([True, False])
            searches = [name for name in names if not cases[name] and rng.random() < 0.4][:1]
            p, nn = derive(formula, cases, members, complete, searches=tuple(searches))
            if names:
                break
        out.append((f"DER-R{n + 1:02d}", formula, cases, members, complete, searches, "a seeded random dossier; every key from the same rules", {"rival": bool(searches), "notes": f"seeded random dossier ({seed}, {n})"}))
    return out


def dossiers():
    return designed + random_dossiers(2027, 6)


def corpus(render_mode="recursive", corpus_id="SIGNED-DERIVATIONS-CORPUS-001"):
    cases = [build(case_id, formula, leaf_cases, members, complete, searches, held_fixed, render_mode=render_mode, **opts) for case_id, formula, leaf_cases, members, complete, searches, held_fixed, opts in dossiers()]
    return {"schema_version": "creib.conformance-pilot.corpus.v1", "corpus_id": corpus_id, "cases": cases}


def main(argv=None) -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Generate the signed-derivations corpus from its finite rules.")
    parser.add_argument("--render-mode", choices=RENDER_MODES, default="recursive", help="root reproduces the first corpus's documents, with the key the visible dossier supports")
    parser.add_argument("--corpus-id", default="SIGNED-DERIVATIONS-CORPUS-001")
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args(argv)
    built = corpus(args.render_mode, args.corpus_id)
    payload = json.dumps(built, ensure_ascii=False, indent=2) + "\n"
    if args.out.exists() and args.out.read_text(encoding="utf-8") == payload:
        print(f"{args.out}: unchanged ({len(built['cases'])} cases)")
        return
    args.out.write_text(payload, encoding="utf-8")
    print(f"{args.out}: written ({len(built['cases'])} cases)")


if __name__ == "__main__":
    main()
