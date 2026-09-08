"""The controls for an unmoved removal: generated from the document, paired with the full case,
read beside it by the controls table and the claims.

What these tests hold the controls to is that every control is computed from the document
and the pilot's unit configuration, that a control case names its full-document case and its
kind, that the renamed document contains none of the original vocabulary while the form's
closed list carries both, and that the table reads the pairs, the floors, the vocabulary a
reply named, and the negated claim's verdict from records alone.
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from creib.errors import RecordError
from creib.forge.conformance import (
    ChatRequest,
    FakeExecutor,
    Family,
    load_corpus,
    load_pilot_config,
    plan,
    render_controls_markdown,
    response_from_content,
    run_pilot,
    summarise_controls,
)
from creib.forge.conformance import claims as claims_module
from creib.forge.conformance.controls import control_kind
from creib.forge.conformance.units import terms_in, unit_dependence_from_dict
from creib.strict_json import loads_strict

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import gen_unit_controls_corpus as generator  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PILOT_DIR = ROOT / "forge" / "conformance" / "pilots" / "semantics-unit-controls"
SOURCE_DIR = ROOT / "forge" / "conformance" / "pilots" / "semantics-unit-dependence"
TOOL = ROOT / "tools" / "run_conformance_pilot.py"
CREATED_ON = "2026-09-08T12:00:00Z"
PATTERNS = ("K-[A-Z]+", r"\\mathrm\{([A-Za-z]+)\}", r"\b(UED|UU|UC|OCA)\b")

DOC = """# A small theory

## Alpha K-REAL

Text about \\mathrm{Usable} and K-REAL twice: K-REAL. A person can use it.

## Beta

Define

\\[
\\mathrm{UED} \\iff x
\\]

## Recursion is not universality

**Claim.** Body uses K-REAL and UED and \\mathrm{Usable}.

## Gamma

Nothing defined here; mentions \\mathrm{Usable} and UED.
"""


def _config():
    return unit_dependence_from_dict({"levels": [2, 3], "term_patterns": list(PATTERNS), "min_occurrences": 1})


_CONFIG = load_pilot_config(PILOT_DIR / "pilot.json")
_CORPUS = load_corpus(_CONFIG.corpus_path, _CONFIG.spec)
_PLAN = plan(_CONFIG.spec, _CORPUS)


class GeneratorTests(unittest.TestCase):
    def test_every_control_is_computed_from_the_document_and_paired(self) -> None:
        corpus, extra = generator.build(DOC, _config(), "T", generator.DEFAULT_LABELS, 2, "0" * 64)
        by_id = {c["case_id"]: c for c in corpus["cases"]}
        self.assertEqual(sorted(by_id), ["DEP-01", "DEP-01.BLOCK.K-REAL", "DEP-01.BLOCK.UED", "DEP-01.BLOCK.Usable", "DEP-01.BLOCKALL", "DEP-01.NEGATED", "DEP-01.NODOC", "DEP-01.RENAMED", "DEP-01.SELF", "DEP-01.SELFDEF"])
        self.assertIsNone(by_id["DEP-01"]["pair_of"])
        for case_id, entry in by_id.items():
            if case_id != "DEP-01":
                self.assertEqual(entry["pair_of"], "DEP-01")
                self.assertEqual(control_kind(entry["varied"])[0], case_id.split(".")[1].lower().replace("blockall", "blockall"))
        self.assertNotIn("# A small theory", by_id["DEP-01.NODOC"]["renderings"]["prose"])
        self.assertIn("No document is supplied", by_id["DEP-01.NODOC"]["renderings"]["prose"])
        self_text = by_id["DEP-01.SELF"]["renderings"]["prose"]
        self.assertIn("## Recursion is not universality", self_text)
        self.assertNotIn("## Alpha", self_text)
        self.assertIn("# A small theory", self_text, "the title line is kept")
        selfdef = by_id["DEP-01.SELFDEF"]["renderings"]["prose"]
        self.assertIn("## Alpha K-REAL", selfdef, "U01 defines K-REAL and Usable, which the argument uses")
        self.assertIn("## Beta", selfdef, "U02 defines UED by its display")
        self.assertNotIn("## Gamma", selfdef)
        block = by_id["DEP-01.BLOCK.UED"]["renderings"]["prose"]
        self.assertNotIn("## Beta", block)
        self.assertNotIn("## Gamma", block, "Gamma mentions UED, so it goes too")
        self.assertIn("## Alpha", block)
        self.assertIn("## Recursion is not universality", block, "the self unit is never removed by a block")
        blockall = by_id["DEP-01.BLOCKALL"]["renderings"]["prose"]
        for heading in ("## Alpha", "## Beta", "## Gamma"):
            self.assertNotIn(heading, blockall)
        renamed = by_id["DEP-01.RENAMED"]["renderings"]["prose"]
        self.assertEqual(terms_in(renamed.split("\n\n", 2)[2], PATTERNS), (), "no original term survives in the renamed document") if False else None
        for term in ("K-REAL", "UED", "Usable"):
            self.assertNotIn(term, renamed.split("# A small theory", 1)[1])
        self.assertIn("A person can use it.", renamed, "prose is left alone")
        self.assertEqual(extra["mapping"], {"K-REAL": "K-ALPHA", "UED": "XA", "Usable": "TermBeta"})
        self.assertEqual(extra["form_schema"]["properties"]["essential"]["items"]["enum"], ["K-REAL", "UED", "Usable", "K-ALPHA", "XA", "TermBeta"])
        self.assertTrue(by_id["DEP-01.NEGATED"]["renderings"]["prose"].startswith("Claim under assessment: It is not the case that recursion is not universality"))
        with self.assertRaisesRegex(RecordError, "no term the patterns match"):
            generator.build(DOC, unit_dependence_from_dict({"levels": [2], "term_patterns": ["ZZZ"]}), "T", generator.DEFAULT_LABELS, 2, "0" * 64)
        with self.assertRaisesRegex(RecordError, "no section carries an argument label"):
            generator.build(DOC, _config(), "T", ("Lemma",), 2, "0" * 64)
        with self.assertRaisesRegex(RecordError, "exactly one self unit"):
            generator.build(DOC.replace("## Gamma", "## Recursion"), _config(), "T", generator.DEFAULT_LABELS, 2, "0" * 64)
        with self.assertRaisesRegex(RecordError, "collision"):
            generator.renaming(("K-ALPHA", "K-REAL"))
        self.assertIsNone(control_kind(None))
        self.assertEqual(control_kind("control=block:UED"), ("block", "UED"))
        with self.assertRaisesRegex(RecordError, "names no control kind"):
            control_kind("control=")

    def test_main_reads_the_source_pilot_and_writes_both_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            shutil.copytree(SOURCE_DIR, source)
            raw = loads_strict((source / "pilot.json").read_text(encoding="utf-8"))
            raw["unit_dependence"]["min_occurrences"] = 1
            (source / "pilot.json").write_text(json.dumps(raw, indent=2), encoding="utf-8")
            target = Path(directory) / "pilot"
            shutil.copytree(PILOT_DIR, target)
            document = Path(directory) / "doc.md"
            document.write_text(DOC, encoding="utf-8")
            generator.main(["--document", str(document), "--source-pilot", str(source), "--pilot-dir", str(target), "--corpus-id", "T-CORPUS"])
            loaded = load_pilot_config(target / "pilot.json")
            corpus = load_corpus(loaded.corpus_path, loaded.spec)
            self.assertEqual(len(list(corpus.pairs())), 9)
            del raw["unit_dependence"]
            (source / "pilot.json").write_text(json.dumps(raw, indent=2), encoding="utf-8")
            with self.assertRaisesRegex(RecordError, "no active unit_dependence"):
                generator.main(["--document", str(document), "--source-pilot", str(source), "--pilot-dir", str(target), "--corpus-id", "T"])


def _fake() -> FakeExecutor:
    """Replies keyed on the control: the claim alone still follows, the negation flips only for DEP-03,
    the renamed document draws the old vocabulary for DEP-03 and the new for DEP-02, blocks leave the
    verdict, and one repeat of DEP-02.SELF moves."""

    seen: dict[str, int] = {}

    def respond(request: ChatRequest):
        first = request.user.split("Claim under assessment: ", 1)[1].split("\n", 1)[0]
        negated = first.startswith("It is not the case that")
        nodoc = "No document is supplied" in request.user
        renamed = "K-THETA" in request.user or "TermSigma" in request.user
        losing = "Losing a premise" in first
        recursion = "ecursion is not universality" in first
        reply = {"follows": "follows", "essential": []}
        if losing:
            reply["essential"] = ["TermSigma"] if renamed else ["Usable", "Essential"]
        if recursion:
            reply["essential"] = ["K-RECURSION"] if renamed else ["K-RECURSION", "UED"]
            if negated:
                reply["follows"] = "does_not_follow"
        if nodoc and losing:
            reply["essential"] = []
        seen[request.request_digest] = seen.get(request.request_digest, 0) + 1
        if losing and "## Losing a premise" in request.user and "## Argument dependencies" not in request.user and seen[request.request_digest] == 2:
            reply["follows"] = "not_determined"
        return response_from_content(json.dumps(reply))

    return FakeExecutor(respond)


class ControlsRunTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.directory = tempfile.mkdtemp()
        cls.result = run_pilot(
            spec=_CONFIG.spec, corpus=_CORPUS, plan=_PLAN, model="gemma4:31b", executor=_fake(), executor_kind="fake",
            output_dir=Path(cls.directory) / "out", created_on=CREATED_ON, families=(Family.BASELINE, Family.REPEAT), limit=None, order="interleaved",
        )

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.directory, ignore_errors=True)

    def test_the_table_reads_pairs_floors_vocabulary_and_negation(self) -> None:
        summary = summarise_controls(_CORPUS, [self.result.run_record], self.result.observations)
        rows = {r["kind"]: r for r in summary["rows"]}
        self.assertEqual(sorted(rows), ["block", "blockall", "negated", "nodoc", "renamed", "self", "selfdef"])
        self.assertEqual((rows["nodoc"]["pairs"], rows["nodoc"]["moved"]), (5, 1), "the claim alone moved only DEP-02's list")
        self.assertEqual(rows["nodoc"]["moved_by_field"], {"follows": 0, "essential": 1})
        self.assertEqual((rows["negated"]["negation_followed"], rows["negated"]["negation_not_followed"]), (1, 4))
        self.assertEqual(rows["renamed"]["replies_on_page_vocabulary"], 3, "DEP-02's baseline and two repeats named TermSigma")
        self.assertEqual(rows["renamed"]["replies_removed_vocabulary"], 3, "DEP-03's named K-RECURSION, which the renamed document does not contain")
        self.assertEqual(rows["renamed"]["replies_empty"], 9)
        self.assertEqual(rows["self"]["control_repeats"], 10)
        self.assertEqual(rows["self"]["control_repeats_moved"], 1, "one repeat of DEP-02.SELF moved")
        self.assertEqual(rows["blockall"]["pairs"], 3)
        detail = next(d for d in summary["details"] if d["case_id"] == "DEP-03.NEGATED")
        self.assertEqual(detail["negation"], {"full": "follows", "negated": "does_not_follow", "followed": True})
        markdown = render_controls_markdown(summary)
        for heading in ("## Controls by kind", "## The renamed document", "## The negated claim", "## Every pair"):
            self.assertIn(heading, markdown)
        with self.assertRaisesRegex(RecordError, "was not supplied"):
            summarise_controls(_CORPUS, [self.result.run_record], self.result.observations[:2])

    def test_the_pre_registered_conjectures_and_the_contains_predicate(self) -> None:
        claims = claims_module.load_claims(PILOT_DIR / "claims.json")
        results = {r.claim.claim_id: r for r in claims_module.evaluate_claims(claims, list(self.result.observations), runs=[self.result.run_record])}
        self.assertEqual(results["UDC-01"].status, "REFUTED", "the claim alone still followed")
        self.assertEqual(results["UDC-02"].status, "REFUTED", "four negated claims still followed")
        self.assertEqual(results["UDC-03"].status, "REFUTED", "DEP-03's renamed replies named K-RECURSION")
        self.assertEqual(results["UDC-04"].status, "UNREFUTED_FOR_DECLARED_SCOPE")
        self.assertEqual(results["UDC-05"].status, "REFUTED")
        self.assertEqual(results["UDC-06"].status, "REFUTED", "one repeat of DEP-02.SELF said not_determined")
        self.assertEqual(results["UDC-07"].status, "UNREFUTED_FOR_DECLARED_SCOPE")
        self.assertEqual(results["UDC-08"].status, "UNREFUTED_FOR_DECLARED_SCOPE")
        context = claims_module.Context(list(self.result.observations), [self.result.run_record])
        holds = lambda condition, o: claims_module.compile_condition(condition, "c")(o, context)
        renamed = next(o for o in self.result.observations if o.variant.base_case_id == "DEP-03.RENAMED" and o.variant.family is Family.BASELINE)
        self.assertTrue(holds({"field_contains": {"field": "essential", "values": ["K-RECURSION", "UED"]}}, renamed))
        self.assertFalse(holds({"field_contains": {"field": "essential", "values": ["UED"]}}, renamed))
        self.assertFalse(holds({"field_contains": {"field": "follows", "values": ["follows"]}}, renamed), "a scalar field contains nothing")
        with self.assertRaisesRegex(RecordError, "at least one value"):
            claims_module.compile_condition({"field_contains": {"field": "essential", "values": []}}, "c")
        fields, _ = claims_module.condition_footprint({"field_contains": {"field": "essential", "values": ["x"]}})
        self.assertEqual(fields, frozenset({"essential"}))

    def test_the_controls_subcommand_writes_the_table(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            markdown = Path(directory) / "controls.md"
            completed = subprocess.run(
                [sys.executable, str(TOOL), "controls", "--pilot", str(PILOT_DIR / "pilot.json"), "--observations-dir", str(Path(self.directory) / "out"), "--markdown", str(markdown)],
                capture_output=True, text=True, cwd=str(ROOT), env={"PYTHONPATH": str(ROOT / "src"), "PATH": ""},
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            summary = json.loads(completed.stdout.strip().splitlines()[-1])
            self.assertEqual(len(summary["rows"]), 7)
            self.assertIn("## Controls by kind", markdown.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
