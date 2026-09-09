"""Generate a unit-dependence corpus from a markdown document: one probe per argued section, no key.

The document is split into units at the heading levels the pilot names. A section is a
probe when its body carries the document's own argument markup (a bold label such as
``**Claim.**`` or ``**Counterexample.**``); the claim under assessment is the section's
heading, restated in a short preamble before the whole document. No answer is written: both
form fields carry the ``unknown`` oracle, so a reply is compared only with the same model's
reply on the full document, never with a key. The form's array field lists the terms the
document uses, found by the pilot's patterns, so that a model can name what it takes the
claim to depend on in the document's own vocabulary.

Run from the repository root with the pilot directory's ``pilot.json`` already in place; the
generator reads the ``unit_dependence`` block from it so that the corpus and the plan share
one configuration. It prints the model-free unit table: every unit, the terms it is taken to
define, and each probe's self and declared units.

    python tools/gen_unit_dependence_corpus.py --document path/to/document.md \\
        --pilot-dir forge/conformance/pilots/<pilot> --corpus-id <ID>
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from creib.errors import RecordError  # noqa: E402
from creib.forge.conformance.units import (  # noqa: E402
    document_terms,
    relate_units,
    split_units,
    unit_dependence_from_dict,
    unit_table_markdown,
    unit_text,
)
from creib.strict_json import loads_strict  # noqa: E402

DEFAULT_LABELS = ("Claim", "Counterexample", "Derivation", "Construction", "Consequence")
PREAMBLE = (
    "Claim under assessment: {title}\n\n"
    "The document below is to be read as written. Decide whether the claim under assessment "
    "follows from the document's commitments and definitions, and name the commitments and "
    "defined terms it depends on. The document begins at its title."
)


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
        "title": "Unit dependence probe",
        "description": "Whether a claim follows from a document as written, and which of the document's named commitments and defined terms it depends on.",
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


def probes(document: str, levels: tuple[int, ...], labels: tuple[str, ...], probe_level: int) -> list:
    found = []
    for unit in split_units(document, levels):
        if unit.level != probe_level:
            continue
        body = unit_text(document, unit)
        if any(f"**{label}.**" in body for label in labels):
            found.append(unit)
    return found


def build(document: str, config, corpus_id: str, labels: tuple[str, ...], probe_level: int, digest: str) -> tuple[dict, dict]:
    terms = document_terms(document, config)
    if not terms:
        raise RecordError("the document has no term the patterns match")
    cases = []
    relations_by_probe: dict[str, tuple] = {}
    for index, unit in enumerate(probes(document, config.levels, labels, probe_level), start=1):
        case_id = f"DEP-{index:02d}"
        preamble = PREAMBLE.format(title=unit.title)
        text_value = preamble + "\n\n" + document
        relations = relate_units(text_value, config)
        selves = [r.unit.unit_id for r in relations if r.relation == "self"]
        if len(selves) != 1:
            raise RecordError(f"{case_id}: expected exactly one self unit for {unit.title!r}, found {selves}")
        declared = [r.unit.unit_id for r in relations if r.relation == "declared"]
        others = sum(1 for r in relations if r.relation == "other")
        relations_by_probe[case_id] = relations
        cases.append({
            "case_id": case_id,
            "boundary": False,
            "rendering": "prose",
            "renderings": {"prose": text_value},
            "expected": [oracle("follows"), oracle("essential")],
            "held_fixed": "the whole document as written; the claim is the section's own heading",
            "varied": None,
            "pair_of": None,
            "reference_output": None,
            "rival_expected": [],
            "notes": (
                f"probe of section {unit.title!r} (document lines {unit.start + 1}-{unit.end}); document sha256 {digest}; "
                f"self {selves[0]}; declared {', '.join(declared) or 'none'}; other {others} units; no key"
            ),
        })
    if not cases:
        raise RecordError("no section carries an argument label; nothing to probe")
    corpus = {"schema_version": "creib.conformance-pilot.corpus.v1", "corpus_id": corpus_id, "cases": cases}
    table = unit_table_markdown(document, config, relations_by_probe)
    return corpus, {"form_schema": form_schema(terms), "table": table, "terms": terms}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--document", type=Path, required=True, help="the markdown document under test")
    parser.add_argument("--pilot-dir", type=Path, required=True, help="directory holding pilot.json; form.schema.json and corpus.json are written here")
    parser.add_argument("--corpus-id", required=True)
    parser.add_argument("--labels", nargs="+", default=list(DEFAULT_LABELS), help="bold labels that mark a section as argued, and so as a probe")
    parser.add_argument("--probe-level", type=int, default=2, help="heading level of the sections that can be probes")
    parser.add_argument("--units-markdown", type=Path, default=None, help="also write the unit table here")
    args = parser.parse_args(argv)
    raw_pilot = loads_strict((args.pilot_dir / "pilot.json").read_text(encoding="utf-8"))
    config = unit_dependence_from_dict(raw_pilot.get("unit_dependence"))
    if not config.active:
        raise RecordError("pilot.json has no active unit_dependence block")
    document_bytes = args.document.read_bytes()
    document = document_bytes.decode("utf-8")
    digest = hashlib.sha256(document_bytes).hexdigest()
    corpus, extra = build(document, config, args.corpus_id, tuple(args.labels), args.probe_level, digest)
    (args.pilot_dir / "corpus.json").write_text(json.dumps(corpus, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (args.pilot_dir / "form.schema.json").write_text(json.dumps(extra["form_schema"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    table = f"# Units of {args.document.name} (sha256 {digest})\n\n{len(corpus['cases'])} probes; {len(extra['terms'])} terms.\n\n" + extra["table"]
    if args.units_markdown is not None:
        args.units_markdown.write_text(table, encoding="utf-8")
    print(table)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
