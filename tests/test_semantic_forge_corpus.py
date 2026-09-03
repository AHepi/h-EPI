from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from creib.errors import RecordError
from creib.forge import (
    DefectType,
    generate_challenge_templates,
    parse_issue,
    parse_minimal_pair_challenge,
)
from creib.forge.schema_validation import (
    load_local_schema_catalog,
    validate_semantic_forge_file,
    validate_semantic_forge_instance,
)
from creib.forge.calibration import (
    ANNOTATION_PROSE_SEMANTIC_EFFECT,
    ANNOTATION_PROSE_STATUS,
    load_calibration_corpus,
)
from creib.strict_json import load_strict


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "forge" / "schema"
CORPUS_PATH = ROOT / "forge" / "corpus" / "cr-1.0-seed.json"


class SemanticForgeCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = load_local_schema_catalog(SCHEMA_DIR)
        cls.schemas = cls.catalog.schemas
        cls.corpus = load_strict(CORPUS_PATH)

    def test_schemas_are_valid_draft_2020_12(self) -> None:
        self.assertEqual(
            set(self.catalog.schema_names),
            {path.name for path in SCHEMA_DIR.glob("*.schema.json")},
        )
        self.assertTrue(
            {
                "adaptive-inquiry-v2.schema.json",
                "adaptive-inquiry.schema.json",
                "challenge.schema.json",
                "corpus.schema.json",
                "inquiry-event-v2.schema.json",
                "inquiry-event.schema.json",
                "research-issue.schema.json",
            }.issubset(self.schemas)
        )
        for schema_name, schema in self.schemas.items():
            with self.subTest(schema=schema["$id"]):
                Draft202012Validator.check_schema(schema)
                if schema_name in {
                    "challenge.schema.json",
                    "corpus.schema.json",
                    "inquiry-event-v2.schema.json",
                    "inquiry-event.schema.json",
                    "research-issue.schema.json",
                }:
                    self.assertFalse(schema["additionalProperties"])

    def test_seed_validates_and_runtime_parses_every_record(self) -> None:
        validated = validate_semantic_forge_file(
            CORPUS_PATH,
            schema_dir=SCHEMA_DIR,
        )
        self.assertEqual(validated, self.corpus)
        self.assertIs(
            validate_semantic_forge_instance(
                self.corpus,
                catalog=self.catalog,
            ),
            self.corpus,
        )
        challenges = [
            parse_minimal_pair_challenge(record)
            for record in self.corpus["challenges"]
        ]
        issues = [parse_issue(record) for record in self.corpus["research_issues"]]
        self.assertEqual(len(challenges), 10)
        self.assertEqual(len(issues), 10)

    def test_runtime_generated_templates_satisfy_published_challenge_schema(self) -> None:
        validator = self.catalog.validator("challenge.schema.json")
        templates = generate_challenge_templates()
        self.assertEqual(
            {item.defect_type for item in templates},
            {item.value for item in DefectType},
        )
        for template in templates:
            with self.subTest(defect_type=template.defect_type):
                validator.validate(template.to_dict())
        for oracle in (
            "A free-text oracle with no typed claim boundary.",
            "status=project_import_provisional;\nA multiline rationale",
        ):
            invalid = templates[0].to_dict()
            invalid["oracle"] = oracle
            with self.subTest(oracle=oracle), self.assertRaises(ValidationError):
                validator.validate(invalid)

    def test_annotation_coverage_is_exact_and_project_imports_are_not_source_claims(self) -> None:
        challenge_ids = {record["challenge_id"] for record in self.corpus["challenges"]}
        challenge_annotation_ids = {
            record["record_id"] for record in self.corpus["challenge_annotations"]
        }
        issue_ids = {record["issue_id"] for record in self.corpus["research_issues"]}
        issue_annotation_ids = {
            record["record_id"]
            for record in self.corpus["research_issue_annotations"]
        }
        self.assertEqual(challenge_ids, challenge_annotation_ids)
        self.assertEqual(issue_ids, issue_annotation_ids)
        self.assertEqual(
            len(self.corpus["challenges"]),
            len(self.corpus["challenge_annotations"]),
        )
        self.assertEqual(
            len(self.corpus["research_issues"]),
            len(self.corpus["research_issue_annotations"]),
        )
        for collection in ("challenge_annotations", "research_issue_annotations"):
            for annotation in self.corpus[collection]:
                self.assertEqual(annotation["construction_kind"], "project_import")
                if annotation["basis_kind"] == "project_import":
                    self.assertEqual(
                        annotation["source_basis"]["authoritative_refs"],
                        [],
                    )

    def test_annotation_free_prose_has_an_explicit_inert_boundary(self) -> None:
        for collection in ("challenge_annotations", "research_issue_annotations"):
            for annotation in self.corpus[collection]:
                with self.subTest(
                    collection=collection,
                    record_id=annotation["record_id"],
                ):
                    self.assertEqual(
                        annotation["annotation_prose_status"],
                        ANNOTATION_PROSE_STATUS,
                    )
                    self.assertEqual(
                        annotation["annotation_prose_semantic_effect"],
                        ANNOTATION_PROSE_SEMANTIC_EFFECT,
                    )

        changed_prose = copy.deepcopy(self.corpus)
        changed_prose["challenge_annotations"][0]["title"] = (
            "Editorial assertion carrying no typed semantic force"
        )
        changed_prose["challenge_annotations"][0]["source_basis"][
            "boundary_note"
        ] = "Unreviewed prose cannot alter a claim kind or oracle status."
        self.catalog.validate(changed_prose, "corpus.schema.json")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "corpus.json"
            path.write_text(json.dumps(changed_prose), encoding="utf-8")
            loaded = load_calibration_corpus(path)
        parsed = loaded.challenge_annotations[0]
        self.assertEqual(parsed.annotation_prose_status, ANNOTATION_PROSE_STATUS)
        self.assertEqual(
            parsed.annotation_prose_semantic_effect,
            ANNOTATION_PROSE_SEMANTIC_EFFECT,
        )

        promoted_status = copy.deepcopy(self.corpus)
        promoted_status["challenge_annotations"][0][
            "annotation_prose_status"
        ] = "reviewed_authoritative"
        with self.assertRaises(RecordError):
            self.catalog.validate(promoted_status, "corpus.schema.json")

        promoted_effect = copy.deepcopy(self.corpus)
        promoted_effect["research_issue_annotations"][0][
            "annotation_prose_semantic_effect"
        ] = "establishes_source_authority"
        with self.assertRaises(RecordError):
            self.catalog.validate(promoted_effect, "corpus.schema.json")

        missing_boundary = copy.deepcopy(self.corpus)
        del missing_boundary["challenge_annotations"][0][
            "annotation_prose_semantic_effect"
        ]
        with self.assertRaises(RecordError):
            self.catalog.validate(missing_boundary, "corpus.schema.json")

    def test_authority_references_are_exact_subject_bound_contracts(self) -> None:
        references = [
            reference
            for collection in ("challenge_annotations", "research_issue_annotations")
            for annotation in self.corpus[collection]
            for field in ("authoritative_refs", "related_authority_refs")
            for reference in annotation["source_basis"][field]
        ]
        self.assertEqual(len(references), 23)
        self.assertEqual(
            len({reference["reference_id"] for reference in references}),
            len(references),
        )
        registered_schema_ids = set(
            self.schemas["corpus.schema.json"]["$defs"]["authority_ref"][
                "properties"
            ]["reference_id"]["enum"]
        )
        self.assertEqual(
            {reference["reference_id"] for reference in references},
            registered_schema_ids,
        )
        self.catalog.validate(self.corpus, "corpus.schema.json")

        laundered = copy.deepcopy(self.corpus)
        annotation = laundered["challenge_annotations"][1]
        annotation["basis_kind"] = "source_authority"
        annotation["oracle_status"] = "source_scoped"
        annotation["source_basis"]["authoritative_refs"] = [
            {
                "reference_id": (
                    "CR1REF:SMF-CH-CONJECTURE-BEFORE-CRITICISM-001:"
                    "AUTHORITATIVE:99"
                ),
                "source_record_ids": ["DP-2"],
                "locator": "MADE-UP-AUTHORITY",
                "physical_pdf_pages": [226],
                "use": "Machine confirmed this project import as CR-1.0 semantics.",
            }
        ]
        with self.assertRaises(RecordError):
            self.catalog.validate(laundered, "corpus.schema.json")

        altered_use = copy.deepcopy(self.corpus)
        altered_use["challenge_annotations"][0]["source_basis"][
            "authoritative_refs"
        ][0]["use"] = "A provider declared this source meaning confirmed."
        with self.assertRaisesRegex(RecordError, "registered immutable reference"):
            self.catalog.validate(altered_use, "corpus.schema.json")

        altered_source_id = copy.deepcopy(self.corpus)
        altered_source_id["challenge_annotations"][0]["source_basis"][
            "authoritative_refs"
        ][0]["source_record_ids"] = ["DP-4"]
        with self.assertRaisesRegex(RecordError, "registered immutable reference"):
            self.catalog.validate(altered_source_id, "corpus.schema.json")

        altered_page = copy.deepcopy(self.corpus)
        altered_page["challenge_annotations"][0]["source_basis"][
            "authoritative_refs"
        ][0]["physical_pdf_pages"] = [225]
        with self.assertRaisesRegex(RecordError, "registered immutable reference"):
            self.catalog.validate(altered_page, "corpus.schema.json")

        borrowed_reference_id = copy.deepcopy(self.corpus)
        borrowed_reference_id["challenge_annotations"][0]["source_basis"][
            "authoritative_refs"
        ][0]["reference_id"] = (
            "CR1REF:SMF-RI-EXPLANATION-INTERPRETATION-001:AUTHORITATIVE:01"
        )
        with self.assertRaisesRegex(RecordError, "different subject"):
            self.catalog.validate(borrowed_reference_id, "corpus.schema.json")

        altered_subject = copy.deepcopy(self.corpus)
        altered_subject["challenges"][0]["oracle"] += " Provider-confirmed."
        with self.assertRaisesRegex(RecordError, "subject content differs"):
            self.catalog.validate(altered_subject, "corpus.schema.json")

        promoted_interpretation = copy.deepcopy(self.corpus)
        issue_annotation = promoted_interpretation["research_issue_annotations"][4]
        self.assertEqual(issue_annotation["basis_kind"], "source_interpretation")
        issue_annotation["basis_kind"] = "source_authority"
        with self.assertRaisesRegex(RecordError, "claim-kind boundary"):
            self.catalog.validate(promoted_interpretation, "corpus.schema.json")

    def test_unresolved_issues_stay_unresolved_and_do_not_acquire_an_oracle(self) -> None:
        for annotation in self.corpus["research_issue_annotations"]:
            with self.subTest(record_id=annotation["record_id"]):
                self.assertEqual(annotation["status"], "unresolved")
                self.assertIsNone(annotation["resolution"])

    def test_challenge_oracles_preserve_their_claim_boundary(self) -> None:
        expected_status = {
            "source_authority": "source_scoped",
            "source_interpretation": "interpretation_provisional",
            "project_import": "project_import_provisional",
        }
        challenges = {
            challenge["challenge_id"]: challenge
            for challenge in self.corpus["challenges"]
        }
        for annotation in self.corpus["challenge_annotations"]:
            with self.subTest(record_id=annotation["record_id"]):
                self.assertEqual(
                    annotation["oracle_status"],
                    expected_status[annotation["basis_kind"]],
                )
                self.assertTrue(
                    challenges[annotation["record_id"]]["oracle"].startswith(
                        f"status={annotation['oracle_status']};"
                    )
                )
        self.assertNotIn(
            "formal_relative",
            {
                annotation["oracle_status"]
                for annotation in self.corpus["challenge_annotations"]
            },
        )

        contradictory = copy.deepcopy(self.corpus)
        contradictory["challenges"][0]["oracle"] = contradictory["challenges"][
            0
        ]["oracle"].replace(
            "status=interpretation_provisional;",
            "status=source_scoped;",
            1,
        )
        with self.assertRaisesRegex(RecordError, "oracle status contradicts"):
            self.catalog.validate(contradictory, "corpus.schema.json")

    def test_seed_annotations_use_only_representable_provenance_shapes(self) -> None:
        representable = {
            "source_authority",
            "source_interpretation",
            "project_import",
        }
        for collection in (
            "challenge_annotations",
            "research_issue_annotations",
        ):
            for annotation in self.corpus[collection]:
                with self.subTest(
                    collection=collection,
                    record_id=annotation["record_id"],
                ):
                    self.assertIn(annotation["basis_kind"], representable)
        challenge_annotations = {
            annotation["record_id"]: annotation
            for annotation in self.corpus["challenge_annotations"]
        }
        for record_id in (
            "SMF-CH-FINITE-HISTORY-DISPOSITION-001",
            "SMF-CH-SEMANTIC-PHYSICAL-MAPPING-001",
        ):
            self.assertEqual(
                challenge_annotations[record_id]["basis_kind"],
                "source_interpretation",
            )
        self.assertNotIn(
            "source_authority",
            {
                annotation["basis_kind"]
                for collection in (
                    "challenge_annotations",
                    "research_issue_annotations",
                )
                for annotation in self.corpus[collection]
            },
        )

        unrepresentable = copy.deepcopy(self.corpus)
        unrepresentable["challenge_annotations"][0][
            "basis_kind"
        ] = "formal_consequence"
        unrepresentable["challenge_annotations"][0][
            "oracle_status"
        ] = "formal_relative"
        with self.assertRaises(RecordError):
            self.catalog.validate(unrepresentable, "corpus.schema.json")

    def test_source_locators_use_physical_pdf_pages(self) -> None:
        actual: dict[tuple[str, str], tuple[int, ...]] = {}
        for collection in (
            "challenge_annotations",
            "research_issue_annotations",
        ):
            for annotation in self.corpus[collection]:
                for kind in ("authoritative_refs", "related_authority_refs"):
                    for reference in annotation["source_basis"][kind]:
                        actual[(annotation["record_id"], reference["locator"])] = tuple(
                            reference["physical_pdf_pages"]
                        )
        expected = {
            ("SMF-CH-ANTI-INDUCTION-001", "DP-2"): (226,),
            (
                "SMF-CH-CRITICISM-VS-SCORE-001",
                "SC-3, DF-5, DF-6 and DP-5",
            ): (222, 223, 226),
            ("SMF-CH-AUTHORSHIP-VS-OUTPUT-001", "SC-4 and DP-3"): (
                222,
                226,
            ),
            (
                "SMF-CH-SEMANTIC-PHYSICAL-MAPPING-001",
                "TY-3, SC-6, BR-1 to BR-8, DF-22, DF-23 and TH-14",
            ): (221, 222, 228, 229, 232),
            ("SMF-RI-AUTHORSHIP-CREDIT-001", "MS-4, SC-4 and DP-3"): (
                222,
                226,
            ),
            (
                "SMF-RI-SEMANTIC-PHYSICAL-BRIDGE-001",
                "BR-1 to BR-8 and TH-14",
            ): (228, 229, 232),
            ("SMF-RI-ANTIINDUCTIVE-PRIORITY-001", "DP-2 and DP-4"): (226,),
            (
                "SMF-RI-EXPLANATION-INTERPRETATION-001",
                "MS-5, SC-5 and DP-1",
            ): (222, 226),
        }
        for key, pages in expected.items():
            with self.subTest(record_id=key[0], locator=key[1]):
                self.assertEqual(actual[key], pages)

    def test_claim_kind_meanings_are_frozen_policy_not_free_prose(self) -> None:
        changed = copy.deepcopy(self.corpus)
        changed["epistemic_policy"]["claim_kind_meanings"][
            "source_authority"
        ] += " Altered."
        with self.assertRaises(RecordError):
            self.catalog.validate(changed, "corpus.schema.json")

    def test_whitespace_only_text_and_overlong_keys_are_rejected(self) -> None:
        blank = copy.deepcopy(self.corpus)
        blank["challenges"][0]["oracle"] = " \t\n"
        with self.assertRaises(RecordError):
            self.catalog.validate(blank, "corpus.schema.json")

        overlong = copy.deepcopy(self.corpus)
        overlong["challenges"][0]["defect_type"] = "a" * 129
        with self.assertRaises(RecordError):
            self.catalog.validate(overlong, "corpus.schema.json")

    def test_schema_level_collections_reject_exact_duplicates(self) -> None:
        duplicate_channel = copy.deepcopy(self.corpus)
        duplicate_channel["research_policy"]["preferred_discovery_channels"].append(
            "AlphaXiv"
        )
        with self.assertRaises(RecordError):
            self.catalog.validate(duplicate_channel, "corpus.schema.json")

        duplicate_falsifier = copy.deepcopy(self.corpus)
        falsifiers = duplicate_falsifier["research_issues"][0]["rivals"][0][
            "falsifier_conditions"
        ]
        falsifiers.append(falsifiers[0])
        with self.assertRaises(RecordError):
            self.catalog.validate(duplicate_falsifier, "corpus.schema.json")

    def test_catalog_fails_closed_on_an_unregistered_reference(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            schema_dir = Path(directory)
            broken = {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": "https://ahepi.example/test/broken.schema.json",
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "value": {
                        "$ref": "https://unregistered.invalid/remote.schema.json"
                    }
                },
            }
            (schema_dir / "broken.schema.json").write_text(
                json.dumps(broken),
                encoding="utf-8",
            )
            with self.assertRaises(RecordError):
                load_local_schema_catalog(schema_dir)

    def test_catalog_ignores_reference_shaped_literal_data(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            schema_dir = Path(directory)
            literal = {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": "https://ahepi.example/test/literal.schema.json",
                "const": {"$ref": "ordinary-data-not-a-schema-reference"},
            }
            (schema_dir / "literal.schema.json").write_text(
                json.dumps(literal),
                encoding="utf-8",
            )
            catalog = load_local_schema_catalog(schema_dir)
            catalog.validate(
                {"$ref": "ordinary-data-not-a-schema-reference"},
                "literal.schema.json",
            )

    def test_catalog_schema_snapshots_cannot_mutate_future_validation(self) -> None:
        schema_name = "research-ledger.schema.json"
        if schema_name not in self.catalog.schema_names:
            self.skipTest("research-ledger schema is not present")
        snapshot = self.catalog.schemas
        snapshot[schema_name]["required"].clear()
        snapshot[schema_name]["additionalProperties"] = True
        with self.assertRaises(RecordError):
            self.catalog.validate({}, schema_name)

    def test_catalog_rejects_nested_resource_identifiers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            schema_dir = Path(directory)
            nested_id = {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": "https://ahepi.example/test/root.schema.json",
                "$defs": {
                    "ambiguous": {
                        "$id": "https://ahepi.example/test/shared.schema.json",
                        "type": "string",
                    }
                },
            }
            (schema_dir / "nested.schema.json").write_text(
                json.dumps(nested_id),
                encoding="utf-8",
            )
            with self.assertRaises(RecordError):
                load_local_schema_catalog(schema_dir)

    def test_catalog_rejects_ambiguous_anchor_mechanisms(self) -> None:
        for keyword in ("$anchor", "$dynamicAnchor", "$dynamicRef"):
            with self.subTest(keyword=keyword), tempfile.TemporaryDirectory() as directory:
                schema_dir = Path(directory)
                ambiguous = {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "$id": "https://ahepi.example/test/root.schema.json",
                    "$defs": {
                        "ambiguous": {
                            keyword: "shared" if keyword != "$dynamicRef" else "#shared",
                            "type": "string",
                        }
                    },
                }
                (schema_dir / "ambiguous.schema.json").write_text(
                    json.dumps(ambiguous),
                    encoding="utf-8",
                )
                with self.assertRaises(RecordError):
                    load_local_schema_catalog(schema_dir)

    def test_recursive_schema_failure_is_typed_and_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            schema_dir = Path(directory)
            recursive = {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": "https://ahepi.example/test/loop.schema.json",
                "$ref": "#",
            }
            (schema_dir / "loop.schema.json").write_text(
                json.dumps(recursive),
                encoding="utf-8",
            )
            catalog = load_local_schema_catalog(schema_dir)
            with self.assertRaises(RecordError):
                catalog.validate({}, "loop.schema.json")

    def test_runtime_only_corpus_invariants_fail_closed(self) -> None:
        identical_pair = copy.deepcopy(self.corpus)
        identical_pair["challenges"][0]["lookalike_case"] = identical_pair[
            "challenges"
        ][0]["intended_case"]
        with self.assertRaises(RecordError):
            self.catalog.validate(identical_pair, "corpus.schema.json")

        duplicate_rival_id = copy.deepcopy(self.corpus)
        duplicate_rival_id["research_issues"][0]["rivals"][1][
            "rival_id"
        ] = duplicate_rival_id["research_issues"][0]["rivals"][0]["rival_id"]
        with self.assertRaises(RecordError):
            self.catalog.validate(duplicate_rival_id, "corpus.schema.json")

        duplicate_challenge_id = copy.deepcopy(self.corpus)
        repeated = copy.deepcopy(duplicate_challenge_id["challenges"][0])
        repeated["oracle"] += " Distinct record body."
        duplicate_challenge_id["challenges"].append(repeated)
        with self.assertRaises(RecordError):
            self.catalog.validate(duplicate_challenge_id, "corpus.schema.json")

        broken_coverage = copy.deepcopy(self.corpus)
        broken_coverage["challenge_annotations"][0][
            "record_id"
        ] = "SMF-CH-NOT-IN-CORPUS-001"
        with self.assertRaises(RecordError):
            self.catalog.validate(broken_coverage, "corpus.schema.json")

    def test_research_channel_is_default_not_semantic_authority(self) -> None:
        policy = self.corpus["research_policy"]
        self.assertEqual(policy["preferred_discovery_channels"][0], "AlphaXiv")
        self.assertTrue(policy["provider_replaceable"])
        self.assertFalse(policy["provider_output_is_oracle"])

        reversioned = copy.deepcopy(self.corpus)
        reversioned["corpus_id"] = "SMF-CORPUS-REPLACEABLE-DISCOVERY"
        reversioned["research_policy"]["preferred_discovery_channels"] = [
            "FutureDiscoveryIndex"
        ]
        self.catalog.validate(reversioned, "corpus.schema.json")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "corpus.json"
            path.write_text(json.dumps(reversioned), encoding="utf-8")
            loaded = load_calibration_corpus(path)
        self.assertEqual(loaded.discovery_channels, ("FutureDiscoveryIndex",))

    def test_corpus_does_not_force_research_when_no_external_issue_is_live(self) -> None:
        no_research = copy.deepcopy(self.corpus)
        no_research["corpus_id"] = "SMF-CORPUS-NO-EXTERNAL-ISSUE"
        no_research["research_issues"] = []
        no_research["research_issue_annotations"] = []
        self.catalog.validate(no_research, "corpus.schema.json")


if __name__ == "__main__":
    unittest.main()
