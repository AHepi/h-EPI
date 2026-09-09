"""Isolated reproductions for review of AHepi/h-EPI commit 0cba0b8.

This is NOT a checkout or execution of the repository's complete test suite.
The rendering and derivation functions below transcribe the relevant operations
from tools/gen_signed_derivations_corpus.py. The labelled response is transcribed
from observation.dcc7033bffce6cd0.json. No network or model calls are made.
"""
from __future__ import annotations
import json
from pathlib import Path

COMMIT = "0cba0b8bb2efe2570b850ef2b7c0655e5ad88a06"

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

def instance(body, m):
    if isinstance(body, str):
        return ("atom", f"{body}({m})")
    return (body[0], ("atom", f"{body[1]}({m})"), ("atom", f"{body[2]}({m})"))

def derive(formula, cases, members, complete):
    kind = formula[0]
    if kind == "atom":
        have = set(cases.get(formula[1], ()))
        return "positive" in have, "negative" in have
    if kind in ("and", "or"):
        p1, n1 = derive(formula[1], cases, members, complete)
        p2, n2 = derive(formula[2], cases, members, complete)
        return (p1 and p2, n1 or n2) if kind == "and" else (p1 or p2, n1 and n2)
    if kind == "not":
        p, n = derive(formula[1], cases, members, complete)
        return n, p
    results = [derive(instance(formula[1], m), cases, members, complete) for m in members]
    if kind == "all":
        return complete and all(p for p, _ in results), any(n for _, n in results)
    if kind == "some":
        return any(p for p, _ in results), complete and all(n for _, n in results)
    raise ValueError(kind)

def words(formula):
    kind = formula[0]
    if kind == "atom":
        return formula[1]
    if kind in ("and", "or"):
        return f"({words(formula[1])} {kind.upper()} {words(formula[2])})"
    if kind == "not":
        return f"NOT {words(formula[1])}"
    body = formula[1]
    body_text = f"{body}(x)" if isinstance(body, str) else f"({body[1]}(x) {body[0].upper()} {body[2]}(x))"
    return f"{'ALL' if kind == 'all' else 'SOME'} x IN R: {body_text}"

def case_text(name, have):
    have = set(have)
    if have == {"positive", "negative"}:
        return f"both a positive and a negative case for {name}"
    if have == {"positive"}:
        return f"a positive case for {name}"
    if have == {"negative"}:
        return f"a negative case for {name}"
    return f"no case for {name}"

def prose(case_id, formula, cases, members, complete):
    lines = [f"Derivation dossier {case_id}. The target claim is {words(formula)}."]
    # Same root-only quantifier check as the reviewed code.
    if any(f[0] in ("all", "some") for f in [formula]):
        lines.append(f"The range R has the recorded members {', '.join(members)}; the record " + ("asserts that this list is complete." if complete else "does not assert that this list is complete."))
    names = leaves_of(formula, members)
    lines.append("Cases on file: " + "; ".join(case_text(n, cases.get(n, ())) for n in names) + ".")
    return " ".join(lines)

def main():
    formula = ("not", ("some", "P"))
    members = ["m1", "m2", "m3"]
    cases = {f"P({m})": ("negative",) for m in members}
    complete_text = prose("DER-11", formula, cases, members, True)
    incomplete_text = prose("DER-11", formula, cases, members, False)
    complete_key = derive(formula, cases, members, True)
    incomplete_key = derive(formula, cases, members, False)
    if complete_text != incomplete_text or complete_key == incomplete_key:
        raise RuntimeError("The expected information-loss witness did not reproduce.")
    # The exact seven relevant output fields of the recorded LAB-07 response.
    output = {"label_a1":"undecided", "label_a2":"undecided", "label_a3":"undecided", "label_a4":"out", "label_a5":"out", "label_a6":"in", "usable_count":1}
    own_count = sum(output[f"label_a{i}"] == "in" for i in range(1, 7))
    oracle_count = 2
    if own_count != output["usable_count"] or output["usable_count"] == oracle_count:
        raise RuntimeError("The expected predicate-mismatch witness did not reproduce.")
    result = {
        "reviewed_commit": COMMIT,
        "execution_scope": "isolated source-operation reproduction; no repository suite or model calls",
        "renderer_information_loss": {
            "rendered_input_identical": complete_text == incomplete_text,
            "rendered_input": complete_text,
            "key_with_complete_range": list(complete_key),
            "key_without_complete_range": list(incomplete_key),
            "interpretation": "Positive/negative derivability differs although the visible dossier is identical."
        },
        "lab11_predicate_mismatch": {
            "source_observation": "dcc7033bffce6cd0",
            "model": "gpt-oss:20b",
            "output": output,
            "count_of_own_in_labels": own_count,
            "oracle_count": oracle_count,
            "internal_count_consistent": output["usable_count"] == own_count,
            "proxy_matches_oracle": output["usable_count"] == oracle_count,
            "interpretation": "The record violates the proxy but not the stated internal-consistency claim."
        }
    }
    path = Path(__file__).with_name("isolated_witnesses_results.json")
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
