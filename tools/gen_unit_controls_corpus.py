"""Generate the controls that read an unmoved removal: redundant, unread, or answered from the claim.

A single-unit removal that moves nothing is consistent with three things: the document
carries the unit's content elsewhere, the model answers the claim without the document,
or the model does not read the unit. This corpus puts each probe of the unit-dependence
pilot beside controls that separate them, all computed from the document:

- ``full``      the probe as the unit-dependence pilot sends it;
- ``nodoc``     the claim alone, no document;
- ``self``      the claim with only the section carrying the document's own argument;
- ``selfdef``   that section and the units defining the terms it uses;
- ``block``     the full document minus every other unit that mentions one term the
                argument uses, one case per term, and ``blockall`` minus every other
                unit that mentions any of them;
- ``renamed``   the full document with every term consistently renamed, the form's
                closed list carrying both vocabularies, so a reply that names the old
                vocabulary names what is not on the page;
- ``negated``   the full document with the claim negated in the preamble.

Each control case names the ``full`` case as its pair and says which control it is in
``varied``. No key is written. The pilot directory must hold a ``pilot.json``; the unit
configuration (heading levels, term patterns) is read from ``--source-pilot``, the
unit-dependence pilot, so that the two pilots share one reading of the document.

    python tools/gen_unit_controls_corpus.py --document doc.md \\
        --source-pilot forge/conformance/pilots/semantics-unit-dependence \\
        --pilot-dir forge/conformance/pilots/semantics-unit-controls --corpus-id ID
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from creib.errors import RecordError  # noqa: E402
from creib.forge.conformance.units import (  # noqa: E402
    Unit,
    document_terms,
    preamble_text,
    relate_units,
    split_units,
    unit_dependence_from_dict,
    unit_text,
)
from creib.strict_json import loads_strict  # noqa: E402

DEFAULT_LABELS = ("Claim", "Counterexample", "Derivation", "Construction", "Consequence")
CONTROL_KINDS = ("nodoc", "self", "selfdef", "block", "blockall", "renamed", "negated")
PREAMBLE = (
    "Claim under assessment: {title}\n\n"
    "The document below is to be read as written. Decide whether the claim under assessment "
    "follows from the document's commitments and definitions, and name the commitments and "
    "defined terms it depends on. The document begins at its title."
)
# When the probes are given explicitly (--probes-file), the claim is a statement and the section it is
# drawn from is named, so that the section is the probe's self unit exactly as a heading-claim would be.
PREAMBLE_STATED = (
    "Claim under assessment: {claim}\n\n"
    "The claim is drawn from the section titled \"{title}\".\n\n"
    "The document below is to be read as written. Decide whether the claim under assessment "
    "follows from the document's commitments and definitions, and name the commitments and "
    "defined terms it depends on. The document begins at its title."
)
PREAMBLE_NODOC = (
    "Claim under assessment: {title}\n\n"
    "No document is supplied. Decide whether the claim under assessment follows, and name the "
    "commitments and defined terms it depends on, from the claim alone."
)
GREEK = ("ALPHA", "BETA", "GAMMA", "DELTA", "EPSILON", "ZETA", "ETA", "THETA", "IOTA", "KAPPA", "LAMBDA", "MU", "NU", "XI", "OMICRON", "PI", "RHO", "SIGMA", "TAU", "UPSILON", "PHI", "CHI", "PSI", "OMEGA")


def oracle(field: str) -> dict:
    return {
        "field": field,
        "kind": "unknown",
        "value": None,
        "values": None,
        "pattern": None,
        "oracle_status": "interpretation_provisional",
        "rationale": "no key: the reply is compared with the same model's reply on the full document, never with an answer",
    }


def form_schema(terms: tuple[str, ...]) -> dict:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Unit dependence controls",
        "description": "Whether a claim follows from a document as written, and which of the document's named commitments and defined terms it depends on; the closed list carries the document's vocabulary and the renamed vocabulary of the renamed control.",
        "type": "object",
        "additionalProperties": False,
        "required": ["follows", "essential"],
        "properties": {
            "follows": {
                "type": "string",
                "description": "Whether the claim under assessment follows from the document as written.",
                "enum": ["follows", "does_not_follow", "not_determined"],
            },
            "essential": {
                "type": "array",
                "description": "The named commitments and defined terms the claim depends on essentially; may be empty.",
                "uniqueItems": True,
                "items": {"type": "string", "enum": list(terms)},
            },
        },
    }


def renaming(terms: tuple[str, ...]) -> dict[str, str]:
    """A fixed, collision-free map from each term to a name of the same shape."""

    mapping: dict[str, str] = {}
    k_index = 0
    word_index = 0

    def greek(index: int) -> str:
        # Past the twenty-four letters the name takes a numeral, so any vocabulary size renames.
        return GREEK[index % len(GREEK)] + (str(index // len(GREEK) + 1) if index >= len(GREEK) else "")

    for term in terms:
        if term.startswith("K-"):
            mapping[term] = "K-" + greek(k_index)
            k_index += 1
        elif term.isupper():
            mapping[term] = "X" + chr(ord("A") + word_index % 26) + (str(word_index // 26 + 1) if word_index >= 26 else "")
            word_index += 1
        else:
            mapping[term] = "Term" + greek(word_index).title()
            word_index += 1
    if len(set(mapping.values())) != len(mapping) or set(mapping.values()) & set(terms):
        raise RecordError("renaming produced a collision")
    return mapping


def rename(text_value: str, patterns: tuple[str, ...], mapping: dict[str, str]) -> str:
    """Rename every term occurrence the patterns find, longest spans first, leaving prose alone."""

    spans: dict[tuple[int, int], str] = {}
    for pattern in patterns:
        compiled = re.compile(pattern)
        for match in compiled.finditer(text_value):
            group = 1 if compiled.groups else 0
            spans[match.span(group)] = match.group(group)
    out = []
    last = 0
    for (start, end), term in sorted(spans.items()):
        if start < last:
            continue
        out.append(text_value[last:start])
        out.append(mapping.get(term, term))
        last = end
    out.append(text_value[last:])
    return "".join(out)


def probes(document: str, levels: tuple[int, ...], labels: tuple[str, ...], probe_level: int, stated: list | None = None) -> list:
    """(unit, claim) pairs, as in gen_unit_dependence_corpus: argued sections with their headings, or the stated probes."""

    if stated is not None:
        by_title = {unit.title: unit for unit in split_units(document, levels)}
        found = []
        for index, item in enumerate(stated):
            if item["section"] not in by_title:
                raise RecordError(f"probes[{index}] names a section that is not a unit heading: {item['section']!r}")
            found.append((by_title[item["section"]], item["claim"]))
        return found
    return [(unit, unit.title) for unit in _labelled_probes(document, levels, labels, probe_level)]


def _labelled_probes(document: str, levels: tuple[int, ...], labels: tuple[str, ...], probe_level: int) -> list[Unit]:
    found = []
    for unit in split_units(document, levels):
        if unit.level == probe_level and any(f"**{label}.**" in unit_text(document, unit) for label in labels):
            found.append(unit)
    return found


def _document_without(document: str, units: tuple[Unit, ...], drop: set[str]) -> str:
    lines = document.split("\n")
    keep = [True] * len(lines)
    for unit in units:
        if unit.unit_id in drop:
            for index in range(unit.start, unit.end):
                keep[index] = False
    return "\n".join(line for line, kept in zip(lines, keep) if kept)


def _document_only(document: str, units: tuple[Unit, ...], keep_ids: list[str]) -> str:
    """The document's title line and the named units, in document order."""

    lines = document.split("\n")
    title = lines[0] if lines and lines[0].startswith("#") else ""
    parts = [title] if title else []
    for unit in units:
        if unit.unit_id in keep_ids:
            parts.append("\n".join(lines[unit.start:unit.end]).rstrip("\n"))
    return "\n\n".join(parts) + "\n"


def case(case_id: str, prose: str, *, pair_of: str | None, varied: str | None, held_fixed: str, notes: str) -> dict:
    return {
        "case_id": case_id, "boundary": False, "rendering": "prose", "renderings": {"prose": prose},
        "expected": [oracle("follows"), oracle("essential")],
        "held_fixed": held_fixed, "varied": varied, "pair_of": pair_of, "reference_output": None, "rival_expected": [], "notes": notes,
    }


def build(document: str, config, corpus_id: str, labels: tuple[str, ...], probe_level: int, digest: str, stated: list | None = None) -> tuple[dict, dict]:
    terms = document_terms(document, config)
    if not terms:
        raise RecordError("the document has no term the patterns match")
    mapping = renaming(terms)
    units = split_units(document, config.levels)
    renamed_document = rename(document, config.term_patterns, mapping)
    cases = []
    summary = []
    for index, (unit, claim) in enumerate(probes(document, config.levels, labels, probe_level, stated), start=1):
        base_id = f"DEP-{index:02d}"
        heading_claim = claim == unit.title
        preamble = PREAMBLE.format(title=unit.title) if heading_claim else PREAMBLE_STATED.format(claim=claim, title=unit.title)
        negated = "It is not the case that " + claim[0].lower() + claim[1:]
        nodoc = PREAMBLE_NODOC.format(title=claim)
        negated_preamble = PREAMBLE.format(title=negated) if heading_claim else PREAMBLE_STATED.format(claim=negated, title=unit.title)
        full_text = preamble + "\n\n" + document
        relations = relate_units(full_text, config)
        # relate_units works on the case text, whose units are offset by the preamble; map back by title.
        by_title = {u.title: u for u in units}
        selves = [by_title[r.unit.title] for r in relations if r.relation == "self"]
        declared = [by_title[r.unit.title] for r in relations if r.relation == "declared"]
        if len(selves) != 1:
            raise RecordError(f"{base_id}: expected exactly one self unit for {unit.title!r}, found {[u.unit_id for u in selves]}")
        self_unit = selves[0]
        used_terms = tuple(sorted(set(_terms(preamble + "\n" + unit_text(document, self_unit), config.term_patterns))))
        common = f"probe of section {unit.title!r}; document sha256 {digest}; self {self_unit.unit_id}; declared {', '.join(u.unit_id for u in declared) or 'none'}; terms used {', '.join(used_terms) or 'none'}"
        cases.append(case(base_id, full_text, pair_of=None, varied=None, held_fixed="the whole document as written; the claim is the section's own heading", notes=common + "; no key"))
        cases.append(case(f"{base_id}.NODOC", nodoc, pair_of=base_id, varied="control=nodoc", held_fixed="the claim", notes=common + "; control: no document"))
        cases.append(case(f"{base_id}.SELF", preamble + "\n\n" + _document_only(document, units, [self_unit.unit_id]), pair_of=base_id, varied="control=self", held_fixed="the claim and the document's own argument for it", notes=common + "; control: the self unit only"))
        cases.append(case(f"{base_id}.SELFDEF", preamble + "\n\n" + _document_only(document, units, [u.unit_id for u in units if u.unit_id == self_unit.unit_id or u in declared]), pair_of=base_id, varied="control=selfdef", held_fixed="the claim, its own argument, and the definitions that argument uses", notes=common + "; control: the self unit and the declared units"))
        all_carriers: set[str] = set()
        for term in used_terms:
            carriers = [u.unit_id for u in units if u.unit_id != self_unit.unit_id and term in _terms(unit_text(document, u), config.term_patterns)]
            all_carriers.update(carriers)
            if not carriers:
                continue
            cases.append(case(f"{base_id}.BLOCK.{_slug(term)}", preamble + "\n\n" + _document_without(document, units, set(carriers)), pair_of=base_id, varied=f"control=block:{term}", held_fixed="the claim, its own argument, and every unit that does not mention the term", notes=common + f"; control: every other unit mentioning {term} removed ({', '.join(carriers)})"))
        if all_carriers:
            cases.append(case(f"{base_id}.BLOCKALL", preamble + "\n\n" + _document_without(document, units, all_carriers), pair_of=base_id, varied="control=blockall", held_fixed="the claim, its own argument, and every unit that mentions none of the terms the argument uses", notes=common + f"; control: every other unit mentioning any used term removed ({', '.join(sorted(all_carriers))})"))
        cases.append(case(f"{base_id}.RENAMED", preamble + "\n\n" + renamed_document, pair_of=base_id, varied="control=renamed", held_fixed="the whole document, every term consistently renamed", notes=common + "; control: renamed vocabulary; map " + ", ".join(f"{k}->{v}" for k, v in mapping.items() if k in used_terms or not used_terms)))
        cases.append(case(f"{base_id}.NEGATED", negated_preamble + "\n\n" + document, pair_of=base_id, varied="control=negated", held_fixed="the whole document; the claim negated", notes=common + "; control: the claim negated"))
        summary.append((base_id, unit.title, self_unit.unit_id, [u.unit_id for u in declared], used_terms, sorted(all_carriers)))
    if not cases:
        raise RecordError("no section carries an argument label; nothing to probe")
    corpus = {"schema_version": "creib.conformance-pilot.corpus.v1", "corpus_id": corpus_id, "cases": cases}
    return corpus, {"form_schema": form_schema(terms + tuple(mapping[t] for t in terms)), "mapping": mapping, "summary": summary, "terms": terms}


def _slug(term: str) -> str:
    """A term as a case-id segment: characters outside the identifier alphabet become their code point."""

    return re.sub(r"[^A-Za-z0-9._:-]", lambda m: f"u{ord(m.group(0)):04x}", term)


def _terms(text_value: str, patterns: tuple[str, ...]) -> tuple[str, ...]:
    from creib.forge.conformance.units import terms_in
    return terms_in(text_value, patterns)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--document", type=Path, required=True)
    parser.add_argument("--source-pilot", type=Path, required=True, help="directory of the unit-dependence pilot whose unit_dependence block is reused")
    parser.add_argument("--pilot-dir", type=Path, required=True, help="directory holding this pilot's pilot.json; corpus.json and form.schema.json are written here")
    parser.add_argument("--corpus-id", required=True)
    parser.add_argument("--labels", nargs="+", default=list(DEFAULT_LABELS))
    parser.add_argument("--probes-file", type=Path, default=None, help="JSON list of {section, claim}: the claims to assess, each drawn from the named section heading; replaces label detection")
    parser.add_argument("--probe-level", type=int, default=2)
    args = parser.parse_args(argv)
    source = loads_strict((args.source_pilot / "pilot.json").read_text(encoding="utf-8"))
    config = unit_dependence_from_dict(source.get("unit_dependence"))
    if not config.active:
        raise RecordError("the source pilot has no active unit_dependence block")
    document_bytes = args.document.read_bytes()
    document = document_bytes.decode("utf-8")
    digest = hashlib.sha256(document_bytes).hexdigest()
    stated = None if args.probes_file is None else loads_strict(args.probes_file.read_text(encoding="utf-8"))
    corpus, extra = build(document, config, args.corpus_id, tuple(args.labels), args.probe_level, digest, stated)
    (args.pilot_dir / "corpus.json").write_text(json.dumps(corpus, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (args.pilot_dir / "form.schema.json").write_text(json.dumps(extra["form_schema"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(corpus['cases'])} cases; {len(extra['terms'])} terms renamed")
    for base_id, title, self_id, declared, used, carriers in extra["summary"]:
        print(f"{base_id} {title!r}: self {self_id}; declared {declared}; terms {list(used)}; other carriers {carriers}")
    print("map:", ", ".join(f"{k}->{v}" for k, v in extra["mapping"].items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
