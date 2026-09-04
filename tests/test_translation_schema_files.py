from __future__ import annotations

import copy
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from creib.errors import RecordError
from creib.forge.schema_validation import load_local_schema_catalog


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "forge" / "schema"

TRANSLATION_SCHEMAS = {
    "translation-source-document.schema.json": (
        "https://ahepi.example/smf/0.4/translation-source-document.schema.json"
    ),
    "translation-source-span.schema.json": (
        "https://ahepi.example/smf/0.4/translation-source-span.schema.json"
    ),
    "translation-charter.schema.json": (
        "https://ahepi.example/smf/0.4/translation-charter.schema.json"
    ),
    "translation-obligation-graph.schema.json": (
        "https://ahepi.example/smf/0.4/translation-obligation-graph.schema.json"
    ),
    "translation-interpretation-set.schema.json": (
        "https://ahepi.example/smf/0.4/translation-interpretation-set.schema.json"
    ),
    "translation-neutral-signature.schema.json": (
        "https://ahepi.example/smf/0.4/translation-neutral-signature.schema.json"
    ),
    "translation-neutral-model.schema.json": (
        "https://ahepi.example/smf/0.4/translation-neutral-model.schema.json"
    ),
    "translation-project-import.schema.json": (
        "https://ahepi.example/smf/0.4/translation-project-import.schema.json"
    ),
    "translation-two-way-bridge.schema.json": (
        "https://ahepi.example/smf/0.4/translation-two-way-bridge.schema.json"
    ),
    "translation-snapshot.schema.json": (
        "https://ahepi.example/smf/0.4/translation-snapshot.schema.json"
    ),
}


def _id(prefix: str, digit: str) -> str:
    return f"{prefix}:{digit * 64}"


def _sha(digit: str = "a") -> str:
    return digit * 64


def _domain_sha(digit: str = "a") -> str:
    return "sha256:" + _sha(digit)


def _provenance() -> dict[str, object]:
    return {
        "producer_kind": "HUMAN",
        "producer_id": "reviewer",
        "created_at": "2026-09-03T00:00:00Z",
        "generation_record_ids": [],
    }


def _instances() -> dict[str, dict[str, object]]:
    document_id = _id("TDOC", "a")
    span_id = _id("TSPAN", "b")
    charter_id = _id("TCHAR", "c")
    graph_id = _id("TOG", "d")
    obligation_id = _id("TO", "e")
    source_claim_id = _id("TSC", "f")
    duty_id = _id("TDUT", "1")
    feature_id = _id("TPF", "2")
    distinction_id = _id("TPD", "3")
    interpretation_set_id = _id("TIS", "3")
    interpretation_one = _id("TI", "4")
    interpretation_two = _id("TI", "5")
    signature_id = _id("TNS", "6")
    signature_member_id = _id("TNSM", "7")
    model_id = _id("TNM", "8")
    clause_id = _id("TNMC", "9")
    port_id = _id("TNMP", "a")
    import_id = _id("TIMP", "b")
    bridge_id = _id("TBR", "c")
    forward_mapping_id = _id("TFM", "d")
    reverse_mapping_id = _id("TRM", "e")
    snapshot_id = _id("TSN", "f")

    source_document = {
        "schema_version": "creib.semantic-forge.translation-source-document.v1",
        "document_id": document_id,
        "supersedes_document_id": None,
        "document_key": "CR-1.0",
        "title": "Pinned source",
        "artifact": {
            "supplied_filename": "source.pdf",
            "media_type": "application/pdf",
            "sha256": _sha("1"),
            "byte_length": 100,
        },
        "structure": {"kind": "PDF", "page_count": 2, "encoding": None},
        "legacy_refs": [],
        "provenance": _provenance(),
    }
    source_span = {
        "schema_version": "creib.semantic-forge.translation-source-span.v1",
        "span_id": span_id,
        "supersedes_span_id": None,
        "document_id": document_id,
        "span_key": "CLAUSE-1",
        "segments": [
            {
                "ordinal": 1,
                "locator": {
                    "kind": "PDF_REGION",
                    "physical_page": 1,
                    "page_index_zero_based": 0,
                    "printed_label": "1",
                    "section_raw": "Section",
                    "page_size_millipoints": [612000, 792000],
                    "page_rotation_degrees": 0,
                    "bbox_millipoints": [1000, 1000, 2000, 2000],
                },
                "literal_snapshot": {
                    "algorithm": "word-snapshot-v1",
                    "tool": "extractor",
                    "tool_version": "1.0",
                    "selection_rule": "inside region",
                    "item_count": 4,
                    "digest_domain": "translation-test/literal/v1",
                    "sha256": _sha("2"),
                },
                "reviewed_transcription": None,
            }
        ],
        "context_span_ids": [],
        "legacy_refs": [],
        "source_inferential_status": None,
        "provenance": _provenance(),
    }
    charter = {
        "schema_version": "creib.semantic-forge.translation-charter.v1",
        "charter_id": charter_id,
        "supersedes_charter_id": None,
        "title": "Translation charter",
        "problem_statement": "Represent the source without hiding ambiguity.",
        "purpose": "Construct a bounded neutral semantic model.",
        "output_kind": "NEUTRAL_SEMANTIC_MODEL",
        "authority_bindings": [
            {"document_id": document_id, "role": "SOLE_SEMANTIC_AUTHORITY"}
        ],
        "in_scope": ["One source clause"],
        "out_of_scope": ["Mathematical extraction"],
        "system_boundary": "The selected source clause only.",
        "protected_distinctions": [
            {
                "distinction_id": distinction_id,
                "statement": "A role is not a surface label.",
            }
        ],
        "success_claim": "SCOPED_FIT_ONLY",
        "policies": {
            "formalism_can_override_valid_prose": False,
            "test_survival_effect": "UNREFUTED_ONLY",
            "research_role": "CRITICISM_DISCOVERY_ONLY",
            "ambiguity_policy": "PRESERVE_RIVALS",
            "missing_mapping_policy": "OPEN_LOSS",
            "conflict_policy": "PRESERVE_CONFLICT_FOR_REVIEW",
            "human_semantic_decision_required": True,
        },
        "proposal_status": "PROPOSED",
        "provenance": _provenance(),
    }
    obligation_graph = {
        "schema_version": "creib.semantic-forge.translation-obligation-graph.v1",
        "graph_id": graph_id,
        "supersedes_graph_id": None,
        "charter_id": charter_id,
        "span_bindings": [{"span_id": span_id, "role": "TARGET"}],
        "obligations": [
            {
                "obligation_id": obligation_id,
                "source_claim": {
                    "claim_id": source_claim_id,
                    "claim_kind": "SOURCE_AUTHORITY",
                    "expression_mode": "VERBATIM_TRANSCRIPTION",
                    "statement": "The source distinguishes role from label.",
                    "source_span_ids": [span_id],
                    "source_marks_raw": [],
                },
                "translation_duty": {
                    "duty_id": duty_id,
                    "claim_kind": "SOURCE_INTERPRETATION",
                    "duty_kind": "DISTINCTION",
                    "statement": "Preserve the role-label distinction.",
                    "protected_features": [
                        {
                            "feature_id": feature_id,
                            "kind": "DISTINCTION",
                            "statement": "Role and label can vary independently.",
                            "charter_distinction_ids": [distinction_id],
                        }
                    ],
                },
                "depends_on_obligation_ids": [],
            }
        ],
        "edges": [],
        "proposal_status": "PROPOSED",
        "provenance": _provenance(),
    }
    interpretation_set = {
        "schema_version": "creib.semantic-forge.translation-interpretation-set.v1",
        "interpretation_set_id": interpretation_set_id,
        "supersedes_interpretation_set_id": None,
        "charter_id": charter_id,
        "graph_id": graph_id,
        "question": "Is the distinction causal or merely nominal?",
        "source_span_ids": [span_id],
        "obligation_ids": [obligation_id],
        "rival_relation": "EXCLUSIVE",
        "admissible_branch_sets": [[interpretation_one], [interpretation_two]],
        "branches": [
            {
                "interpretation_id": interpretation_one,
                "claim_kind": "SOURCE_INTERPRETATION",
                "statement": "The role requires a causal difference.",
                "source_span_ids": [span_id],
                "interpreted_obligation_ids": [obligation_id],
                "preserved_feature_ids": [feature_id],
                "model_effect": {
                    "status": "DECLARED",
                    "effect_statement": "Introduce causal use.",
                    "affected_element_keys": ["CausalUse"],
                },
                "discriminating_consequences": ["Relabeling alone does not suffice."],
                "falsifier_conditions": ["A source-backed labels-only case is sufficient."],
                "known_loss_risks": [],
                "proposal_status": "PROPOSED",
            },
            {
                "interpretation_id": interpretation_two,
                "claim_kind": "SOURCE_INTERPRETATION",
                "statement": "The role is exhausted by the label.",
                "source_span_ids": [span_id],
                "interpreted_obligation_ids": [obligation_id],
                "preserved_feature_ids": [],
                "model_effect": {
                    "status": "UNPROJECTED",
                    "effect_statement": "No model projection has been supplied.",
                    "affected_element_keys": [],
                },
                "discriminating_consequences": ["Relabeling changes the classification."],
                "falsifier_conditions": ["A same-label case has distinct causal use."],
                "known_loss_risks": ["The role-label distinction may collapse."],
                "proposal_status": "PROPOSED",
            },
        ],
        "proposal_status": "PROPOSED",
        "provenance": _provenance(),
    }
    neutral_signature = {
        "schema_version": "creib.semantic-forge.translation-neutral-signature.v1",
        "signature_id": signature_id,
        "supersedes_signature_id": None,
        "charter_id": charter_id,
        "members": [
            {
                "member_id": signature_member_id,
                "element_key": "CausalUse",
                "kind": "RELATION",
                "statement": "One item is causally used by another.",
                "argument_roles": [],
                "identity_conditions": [],
                "variation_conditions": ["Labels may vary independently."],
                "scope_conditions": ["Inside the declared system boundary."],
                "semantic_effect": "MEANING_BEARING",
                "basis": {
                    "premise_kind": "SOURCE_INTERPRETATION",
                    "record_ids": [interpretation_one],
                },
            }
        ],
        "proposal_status": "PROPOSED",
        "provenance": _provenance(),
    }
    project_import = {
        "schema_version": "creib.semantic-forge.translation-project-import.v1",
        "import_id": import_id,
        "supersedes_import_id": None,
        "charter_id": charter_id,
        "import_key": "SystemBoundary",
        "statement": "A case supplies an explicit system boundary.",
        "claim_kind": "PROJECT_IMPORT",
        "category": "METHODOLOGICAL",
        "scope": "This translation only.",
        "source_entitlement": "NONE_CLAIMED",
        "motivation": "Causal use is boundary-relative.",
        "independence_claim": {
            "statement": "The boundary is not asserted by the source span.",
            "status": "PROPOSED",
            "discriminator": "Find an explicit source boundary.",
            "evidence_record_ids": [],
        },
        "necessity_claim": {
            "statement": "The boundary is needed to evaluate causal use.",
            "status": "PROPOSED",
            "discriminator": "Delete it and compare admissible cases.",
            "evidence_record_ids": [],
        },
        "alternatives": ["Treat the boundary as an unresolved port."],
        "deletion_test": {
            "prediction": "Deletion makes causal use underdetermined.",
            "test_record_ids": [],
        },
        "affected_element_keys": ["CausalUse"],
        "proposal_status": "PROPOSED",
        "provenance": _provenance(),
    }
    neutral_model = {
        "schema_version": "creib.semantic-forge.translation-neutral-model.v1",
        "model_id": model_id,
        "supersedes_model_id": None,
        "charter_id": charter_id,
        "signature_id": signature_id,
        "interpretation_ids": [interpretation_one],
        "import_ids": [import_id],
        "clauses": [
            {
                "clause_id": clause_id,
                "element_key": "CausalUseRequired",
                "kind": "PRIMITIVE_CONDITION",
                "operative_prose": "The classified role requires causal use.",
                "uses_member_ids": [signature_member_id],
                "depends_on_clause_ids": [],
                "basis": {
                    "premise_kind": "SOURCE_INTERPRETATION",
                    "record_ids": [interpretation_one],
                },
            }
        ],
        "open_ports": [
            {
                "port_id": port_id,
                "question": "Could the labels-only reading be projected?",
                "affected_member_ids": [signature_member_id],
                "affected_clause_ids": [clause_id],
                "interpretation_set_ids": [interpretation_set_id],
            }
        ],
        "semantic_dependency_closure": {
            "members": [
                {
                    "record_id": source_claim_id,
                    "premise_kind": "SOURCE_AUTHORITY",
                    "role": "TRANSITIVE",
                },
                {
                    "record_id": interpretation_one,
                    "premise_kind": "SOURCE_INTERPRETATION",
                    "role": "DIRECT",
                },
                {
                    "record_id": import_id,
                    "premise_kind": "PROJECT_IMPORT",
                    "role": "DIRECT",
                },
            ],
            "closure_sha256": _domain_sha("4"),
        },
        "theory_projection": {
            "signature_id": signature_id,
            "member_ids": [signature_member_id],
            "clause_ids": [clause_id],
            "theory_record_sha256": _domain_sha("5"),
            "execution_semantics": "NONE_V1",
        },
        "proposal_status": "PROPOSED",
        "semantic_verdict": None,
        "provenance": _provenance(),
    }
    two_way_bridge = {
        "schema_version": "creib.semantic-forge.translation-two-way-bridge.v1",
        "bridge_id": bridge_id,
        "supersedes_bridge_id": None,
        "charter_id": charter_id,
        "graph_id": graph_id,
        "signature_id": signature_id,
        "model_id": model_id,
        "interpretation_set_ids": [interpretation_set_id],
        "import_ids": [import_id],
        "forward_mappings": [
            {
                "mapping_id": forward_mapping_id,
                "obligation_id": obligation_id,
                "model_element_ids": [clause_id],
                "interpretation_ids": [interpretation_one],
                "coverage_claim": "CLAIMED_EXACT",
                "transformation_statement": "Render the distinction as causal use.",
                "back_translation": "The role requires causal use, not a label.",
                "comparison": "EQUIVALENT_CANDIDATE",
                "delta_ids": [],
            }
        ],
        "reverse_mappings": [
            {
                "mapping_id": reverse_mapping_id,
                "model_element_id": signature_member_id,
                "basis_kind": "SOURCE_INTERPRETATION",
                "basis_ids": [interpretation_one],
                "source_obligation_ids": [obligation_id],
                "back_translation": "Causal use distinguishes the role.",
                "semantic_effect": "MEANING_BEARING",
            }
        ],
        "translation_deltas": [],
        "mapping_status": "PROPOSED",
        "semantic_verdict": None,
        "provenance": _provenance(),
    }
    snapshot = {
        "schema_version": "creib.semantic-forge.translation-snapshot.v1",
        "snapshot_id": snapshot_id,
        "predecessor_snapshot_id": None,
        "document_ids": [document_id],
        "span_ids": [span_id],
        "charter_id": charter_id,
        "graph_id": graph_id,
        "interpretation_set_ids": [interpretation_set_id],
        "signature_id": signature_id,
        "model_id": model_id,
        "import_ids": [import_id],
        "bridge_id": bridge_id,
        "unresolved_record_ids": [interpretation_two],
        "record_closure_sha256": _domain_sha("6"),
    }
    return {
        "translation-source-document.schema.json": source_document,
        "translation-source-span.schema.json": source_span,
        "translation-charter.schema.json": charter,
        "translation-obligation-graph.schema.json": obligation_graph,
        "translation-interpretation-set.schema.json": interpretation_set,
        "translation-neutral-signature.schema.json": neutral_signature,
        "translation-neutral-model.schema.json": neutral_model,
        "translation-project-import.schema.json": project_import,
        "translation-two-way-bridge.schema.json": two_way_bridge,
        "translation-snapshot.schema.json": snapshot,
    }


class TranslationSchemaFileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = load_local_schema_catalog(SCHEMA_DIR)
        cls.instances = _instances()

    def _validate_schema_only(self, instance: object, schema_name: str) -> None:
        """Exercise representation rules without claiming runtime identity.

        These fixtures deliberately use readable placeholder content IDs.  The
        separate runtime suite recomputes and checks real content identities.
        """

        try:
            self.catalog.validator(schema_name).validate(instance)
        except ValidationError as exc:
            raise RecordError(str(exc)) from exc

    def test_catalog_registers_all_translation_schemas_offline(self) -> None:
        self.assertTrue(set(TRANSLATION_SCHEMAS).issubset(self.catalog.schema_names))
        for schema_name, expected_id in TRANSLATION_SCHEMAS.items():
            with self.subTest(schema=schema_name):
                schema = self.catalog.schemas[schema_name]
                self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
                self.assertEqual(schema["$id"], expected_id)
                self.assertFalse(schema["additionalProperties"])
                Draft202012Validator.check_schema(schema)

    def test_minimal_generic_vertical_slice_is_schema_valid(self) -> None:
        for schema_name, instance in self.instances.items():
            with self.subTest(schema=schema_name):
                self._validate_schema_only(instance, schema_name)

    def test_every_root_record_is_closed_to_extra_fields(self) -> None:
        for schema_name, instance in self.instances.items():
            changed = copy.deepcopy(instance)
            changed["unreviewed_extra"] = True
            with self.subTest(schema=schema_name), self.assertRaises(RecordError):
                self._validate_schema_only(changed, schema_name)

    def test_exact_top_level_content_id_prefixes_are_required(self) -> None:
        id_fields = {
            "translation-source-document.schema.json": "document_id",
            "translation-source-span.schema.json": "span_id",
            "translation-charter.schema.json": "charter_id",
            "translation-obligation-graph.schema.json": "graph_id",
            "translation-interpretation-set.schema.json": "interpretation_set_id",
            "translation-neutral-signature.schema.json": "signature_id",
            "translation-neutral-model.schema.json": "model_id",
            "translation-project-import.schema.json": "import_id",
            "translation-two-way-bridge.schema.json": "bridge_id",
            "translation-snapshot.schema.json": "snapshot_id",
        }
        for schema_name, id_field in id_fields.items():
            changed = copy.deepcopy(self.instances[schema_name])
            changed[id_field] = _id("BAD", "a")
            with self.subTest(schema=schema_name), self.assertRaises(RecordError):
                self._validate_schema_only(changed, schema_name)

    def test_adjacent_utf8_multi_segment_source_span_is_representable(self) -> None:
        span = copy.deepcopy(self.instances["translation-source-span.schema.json"])
        literal = span["segments"][0]["literal_snapshot"]
        span["segments"] = [
            {
                "ordinal": 1,
                "locator": {
                    "kind": "UTF8_BYTE_RANGE",
                    "start_byte": 0,
                    "end_byte_exclusive": 4,
                    "encoding": "UTF-8",
                },
                "literal_snapshot": copy.deepcopy(literal),
                "reviewed_transcription": None,
            },
            {
                "ordinal": 2,
                "locator": {
                    "kind": "UTF8_BYTE_RANGE",
                    "start_byte": 4,
                    "end_byte_exclusive": 8,
                    "encoding": "UTF-8",
                },
                "literal_snapshot": copy.deepcopy(literal),
                "reviewed_transcription": None,
            },
        ]
        self._validate_schema_only(span, "translation-source-span.schema.json")

    def test_charter_cannot_let_formalism_override_prose(self) -> None:
        charter = copy.deepcopy(self.instances["translation-charter.schema.json"])
        charter["policies"]["formalism_can_override_valid_prose"] = True
        with self.assertRaises(RecordError):
            self._validate_schema_only(charter, "translation-charter.schema.json")

    def test_charter_requires_a_coherent_semantic_authority_mode(self) -> None:
        charter = copy.deepcopy(self.instances["translation-charter.schema.json"])
        charter["authority_bindings"][0]["role"] = "CONTEXT_ONLY"
        with self.assertRaises(RecordError):
            self._validate_schema_only(charter, "translation-charter.schema.json")

        charter = copy.deepcopy(self.instances["translation-charter.schema.json"])
        charter["authority_bindings"].append(
            {"document_id": _id("TDOC", "b"), "role": "CO_SEMANTIC_AUTHORITY"}
        )
        with self.assertRaises(RecordError):
            self._validate_schema_only(charter, "translation-charter.schema.json")

    def test_document_media_type_and_structure_must_agree(self) -> None:
        document = copy.deepcopy(
            self.instances["translation-source-document.schema.json"]
        )
        document["structure"] = {
            "kind": "UTF8_TEXT",
            "page_count": None,
            "encoding": "UTF-8",
        }
        with self.assertRaises(RecordError):
            self._validate_schema_only(document, "translation-source-document.schema.json")

    def test_interpretation_set_requires_rivals_and_does_not_project_an_unknown(self) -> None:
        interpretation_set = copy.deepcopy(
            self.instances["translation-interpretation-set.schema.json"]
        )
        interpretation_set["branches"] = interpretation_set["branches"][:1]
        with self.assertRaises(RecordError):
            self._validate_schema_only(
                interpretation_set, "translation-interpretation-set.schema.json"
            )

        interpretation_set = copy.deepcopy(
            self.instances["translation-interpretation-set.schema.json"]
        )
        interpretation_set["branches"][1]["model_effect"]["affected_element_keys"] = [
            "IllicitProjection"
        ]
        with self.assertRaises(RecordError):
            self._validate_schema_only(
                interpretation_set, "translation-interpretation-set.schema.json"
            )

    def test_neutral_records_reject_formal_language_payloads(self) -> None:
        signature = copy.deepcopy(
            self.instances["translation-neutral-signature.schema.json"]
        )
        signature["members"][0]["lean_symbol"] = "CREIB.CausalUse"
        with self.assertRaises(RecordError):
            self._validate_schema_only(signature, "translation-neutral-signature.schema.json")

        model = copy.deepcopy(self.instances["translation-neutral-model.schema.json"])
        model["clauses"][0]["typed_body"] = {"language": "Lean4"}
        with self.assertRaises(RecordError):
            self._validate_schema_only(model, "translation-neutral-model.schema.json")

    def test_structural_scaffolding_cannot_claim_semantic_effect(self) -> None:
        signature = copy.deepcopy(
            self.instances["translation-neutral-signature.schema.json"]
        )
        signature["members"][0]["basis"] = {
            "premise_kind": "STRUCTURAL_SCAFFOLD",
            "record_ids": [],
        }
        with self.assertRaises(RecordError):
            self._validate_schema_only(signature, "translation-neutral-signature.schema.json")

    def test_import_cannot_claim_source_entitlement(self) -> None:
        project_import = copy.deepcopy(
            self.instances["translation-project-import.schema.json"]
        )
        project_import["source_entitlement"] = "SOURCE_AUTHORITY"
        with self.assertRaises(RecordError):
            self._validate_schema_only(project_import, "translation-project-import.schema.json")

    def test_claimed_exact_bridge_cannot_carry_an_open_delta(self) -> None:
        bridge = copy.deepcopy(
            self.instances["translation-two-way-bridge.schema.json"]
        )
        delta_id = _id("TDL", "1")
        bridge["forward_mappings"][0]["delta_ids"] = [delta_id]
        bridge["translation_deltas"] = [
            {
                "delta_id": delta_id,
                "kind": "WEAKENING",
                "source_obligation_ids": [_id("TO", "e")],
                "model_element_ids": [_id("TNMC", "9")],
                "statement": "A condition was weakened.",
                "consequence": "A new case may be admitted.",
                "status": "OPEN",
            }
        ]
        with self.assertRaises(RecordError):
            self._validate_schema_only(bridge, "translation-two-way-bridge.schema.json")

    def test_snapshot_closure_digest_is_domain_prefixed(self) -> None:
        snapshot = copy.deepcopy(self.instances["translation-snapshot.schema.json"])
        snapshot["record_closure_sha256"] = _sha("6")
        with self.assertRaises(RecordError):
            self._validate_schema_only(snapshot, "translation-snapshot.schema.json")

    def test_llm_provenance_requires_a_generation_record(self) -> None:
        document = copy.deepcopy(
            self.instances["translation-source-document.schema.json"]
        )
        document["provenance"]["producer_kind"] = "LLM"
        with self.assertRaises(RecordError):
            self._validate_schema_only(document, "translation-source-document.schema.json")


if __name__ == "__main__":
    unittest.main()
