from __future__ import annotations

import copy
import unittest
from pathlib import Path

from creib.canonical import domain_digest
from creib.errors import AnchorMismatch, PolicyViolation, RecordError
from creib.models import (
    validate_anchor,
    validate_choice_registry,
    validate_declaration,
    validate_manifest,
)
from creib.strict_json import load_strict
from creib.verify import _enforce_pilot_policy, _validate_bridge_graph
from creib.verify import verify_bundle


ROOT = Path(__file__).resolve().parents[1]


class RecordSeparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = validate_manifest(load_strict(ROOT / "authority" / "source_manifest.json"))
        anchor_set = load_strict(ROOT / "authority" / "source_anchors.json")
        cls.raw_anchors = anchor_set["anchors"]
        cls.choice_registry = validate_choice_registry(
            load_strict(ROOT / "bridge" / "choices" / "interpretation-choices.json")
        )

    def anchor_map(self) -> dict[str, dict]:
        return {
            record["anchor_digest"]: validate_anchor(record, self.manifest)
            for record in self.raw_anchors
        }

    def test_anchor_mutation_without_new_identity_fails(self) -> None:
        record = copy.deepcopy(self.raw_anchors[0])
        record["payload"]["locator"]["tight_bbox_millipoints"][2] += 1
        with self.assertRaisesRegex(RecordError, "anchor digest mismatch"):
            validate_anchor(record, self.manifest)

    def test_new_anchor_identity_breaks_old_declaration_reference(self) -> None:
        record = copy.deepcopy(self.raw_anchors[0])
        record["payload"]["locator"]["tight_bbox_millipoints"][2] += 1
        record["anchor_digest"] = domain_digest("CR-EIB/source-anchor/v1", record["payload"])
        payload = validate_anchor(record, self.manifest)
        declaration = load_strict(ROOT / "bridge" / "declarations" / "EIB-DF10-CANDIDATE.json")
        with self.assertRaisesRegex(PolicyViolation, "unresolved anchor"):
            validate_declaration(
                declaration,
                {record["anchor_digest"]: payload},
                self.choice_registry,
            )

    def test_known_wrong_th3_locator_fails_even_if_rehashed(self) -> None:
        records = copy.deepcopy(self.raw_anchors)
        th3 = records[1]
        th3["payload"]["locator"]["physical_pdf_page"] = 229
        th3["payload"]["locator"]["pdf_page_index_zero_based"] = 228
        th3["payload"]["locator"]["printed_footer_page"] = 228
        th3["anchor_digest"] = domain_digest("CR-EIB/source-anchor/v1", th3["payload"])
        anchors = {
            record["payload"]["authoritative_id"]: validate_anchor(record, self.manifest)
            for record in records
        }
        with self.assertRaises(AnchorMismatch):
            _enforce_pilot_policy(self.manifest, anchors)

    def test_invented_source_metadata_fails_even_if_rehashed(self) -> None:
        mutations = {
            "title": lambda payload: payload.__setitem__("title_raw", "invented title"),
            "section": lambda payload: payload["locator"].__setitem__("section_raw", "invented section"),
            "source tag": lambda payload: payload["source_status"].__setitem__(
                "source_tags", ["S-FAKE1"]
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                records = copy.deepcopy(self.raw_anchors)
                mutate(records[0]["payload"])
                records[0]["anchor_digest"] = domain_digest(
                    "CR-EIB/source-anchor/v1", records[0]["payload"]
                )
                anchors = {
                    record["payload"]["authoritative_id"]: validate_anchor(record, self.manifest)
                    for record in records
                }
                with self.assertRaises(AnchorMismatch):
                    _enforce_pilot_policy(self.manifest, anchors)

    def test_source_inferential_status_cannot_be_invented(self) -> None:
        record = copy.deepcopy(self.raw_anchors[0])
        record["payload"]["source_inferential_status"] = "DEF"
        record["anchor_digest"] = domain_digest("CR-EIB/source-anchor/v1", record["payload"])
        with self.assertRaises(PolicyViolation):
            validate_anchor(record, self.manifest)

    def test_hidden_formal_parameter_is_rejected(self) -> None:
        anchor_map = {
            record["anchor_digest"]: validate_anchor(record, self.manifest)
            for record in self.raw_anchors
        }
        declaration = load_strict(ROOT / "bridge" / "declarations" / "EIB-DF10-CANDIDATE.json")
        declaration["parameters"][0]["binding"] = "implicit"
        with self.assertRaises(PolicyViolation):
            validate_declaration(declaration, anchor_map, self.choice_registry)

    def test_declaration_typed_body_path_rejects_traversal(self) -> None:
        declaration = copy.deepcopy(
            load_strict(ROOT / "bridge" / "declarations" / "EIB-DF10-CANDIDATE.json")
        )
        declaration["typed_body"]["path"] = "../formal/CREIB/Bridge/DF10Candidate.lean"
        with self.assertRaisesRegex(RecordError, "normalized repository-relative path"):
            validate_declaration(declaration, self.anchor_map(), self.choice_registry)

    def test_declaration_typed_body_path_rejects_absolute_path(self) -> None:
        declaration = copy.deepcopy(
            load_strict(ROOT / "bridge" / "declarations" / "EIB-DF10-CANDIDATE.json")
        )
        declaration["typed_body"]["path"] = "/tmp/DF10Candidate.lean"
        with self.assertRaisesRegex(RecordError, "normalized repository-relative path"):
            validate_declaration(declaration, self.anchor_map(), self.choice_registry)

    def test_declaration_typed_body_path_rejects_non_normalized_forms(self) -> None:
        for path in (
            "./formal/CREIB/Bridge/DF10Candidate.lean",
            "formal//CREIB/Bridge/DF10Candidate.lean",
            "formal/./CREIB/Bridge/DF10Candidate.lean",
        ):
            declaration = copy.deepcopy(
                load_strict(ROOT / "bridge" / "declarations" / "EIB-DF10-CANDIDATE.json")
            )
            declaration["typed_body"]["path"] = path
            with self.subTest(path=path), self.assertRaisesRegex(
                RecordError, "normalized repository-relative path"
            ):
                validate_declaration(declaration, self.anchor_map(), self.choice_registry)

    def test_v1_declaration_remains_compatible_without_choice_registry(self) -> None:
        declaration = load_strict(ROOT / "bridge" / "declarations" / "EIB-TH3A-PILOT.json")
        validated = validate_declaration(declaration, self.anchor_map())
        self.assertEqual(validated["schema_version"], "cr-eib.bridge-declaration.v1")

    def test_v2_declaration_requires_validated_choice_registry(self) -> None:
        declaration = load_strict(
            ROOT / "bridge" / "declarations" / "EIB-DF10-REFINED-CANDIDATE.json"
        )
        with self.assertRaisesRegex(PolicyViolation, "require a validated interpretation choice registry"):
            validate_declaration(declaration, self.anchor_map())
        validated = validate_declaration(declaration, self.anchor_map(), self.choice_registry)
        self.assertEqual(validated["schema_version"], "cr-eib.bridge-declaration.v2")

    def test_v2_binder_order_must_match_parameter_order(self) -> None:
        declaration = copy.deepcopy(
            load_strict(ROOT / "bridge" / "declarations" / "EIB-DF10-REFINED-CANDIDATE.json")
        )
        declaration["binder_semantics"]["order"][3:5] = ["x", "s"]
        with self.assertRaisesRegex(PolicyViolation, "binder order"):
            validate_declaration(declaration, self.anchor_map(), self.choice_registry)

    def test_v2_choice_references_fail_closed(self) -> None:
        declaration = copy.deepcopy(
            load_strict(ROOT / "bridge" / "declarations" / "EIB-DF10-REFINED-CANDIDATE.json")
        )
        declaration["interpretation"]["choice_ids"][0] = "EIB-C-TY99"
        with self.assertRaisesRegex(PolicyViolation, "unresolved interpretation choice"):
            validate_declaration(declaration, self.anchor_map(), self.choice_registry)

    def test_v2_interpretation_metadata_ids_are_unique(self) -> None:
        declaration = copy.deepcopy(
            load_strict(ROOT / "bridge" / "declarations" / "EIB-DF10-REFINED-CANDIDATE.json")
        )
        declaration["interpretation"]["loses"][0]["loss_id"] = declaration[
            "interpretation"
        ]["preserves"][0]["preservation_id"]
        with self.assertRaisesRegex(RecordError, "duplicate interpretation metadata identifier"):
            validate_declaration(declaration, self.anchor_map(), self.choice_registry)

    def test_v2_mapping_acceptance_requires_separate_review_acceptance(self) -> None:
        declaration = copy.deepcopy(
            load_strict(ROOT / "bridge" / "declarations" / "EIB-DF10-REFINED-CANDIDATE.json")
        )
        declaration["mapping_status"] = "accepted"
        with self.assertRaisesRegex(PolicyViolation, "accepted mapping requires"):
            validate_declaration(declaration, self.anchor_map(), self.choice_registry)

    def test_v2_accepted_mapping_requires_equivalence_capable_class(self) -> None:
        base = copy.deepcopy(
            load_strict(
                ROOT / "bridge" / "declarations" / "EIB-DF10-REFINED-CANDIDATE.json"
            )
        )
        base["mapping_status"] = "accepted"
        base["interpretation"]["bridge_status"] = "accepted"
        base["interpretation"]["review_status"] = "accepted"
        base["interpretation"]["coverage"]["status"] = "exact"
        base["interpretation"]["coverage"]["excluded"] = []
        base["interpretation"]["loses"] = []
        accepted_choices = {
            choice_id: {"bridge_status": "accepted"}
            for choice_id in base["interpretation"]["choice_ids"]
        }
        for interpretation_class in ("refinement", "assumption"):
            declaration = copy.deepcopy(base)
            declaration["interpretation"]["class"] = interpretation_class
            with self.subTest(interpretation_class=interpretation_class), self.assertRaisesRegex(
                PolicyViolation, "equivalence-capable"
            ):
                validate_declaration(declaration, self.anchor_map(), accepted_choices)

    def test_v2_accepted_mapping_requires_exact_lossless_coverage(self) -> None:
        declaration = copy.deepcopy(
            load_strict(
                ROOT / "bridge" / "declarations" / "EIB-DF10-REFINED-CANDIDATE.json"
            )
        )
        declaration["mapping_status"] = "accepted"
        declaration["interpretation"]["bridge_status"] = "accepted"
        declaration["interpretation"]["review_status"] = "accepted"
        accepted_choices = {
            choice_id: {"bridge_status": "accepted"}
            for choice_id in declaration["interpretation"]["choice_ids"]
        }
        with self.assertRaisesRegex(PolicyViolation, "exact exclusion-free coverage"):
            validate_declaration(declaration, self.anchor_map(), accepted_choices)

        declaration["interpretation"]["coverage"]["status"] = "exact"
        with self.assertRaisesRegex(PolicyViolation, "may not declare exclusions"):
            validate_declaration(declaration, self.anchor_map(), accepted_choices)

        declaration["interpretation"]["coverage"]["excluded"] = []
        with self.assertRaisesRegex(PolicyViolation, "semantic losses"):
            validate_declaration(declaration, self.anchor_map(), accepted_choices)

        declaration["interpretation"]["loses"] = []
        declaration["interpretation"]["class"] = "abbreviation"
        validated = validate_declaration(declaration, self.anchor_map(), accepted_choices)
        self.assertEqual(validated["mapping_status"], "accepted")

    def test_v2_verified_obligation_requires_verified_artifact(self) -> None:
        declaration = copy.deepcopy(
            load_strict(ROOT / "bridge" / "declarations" / "EIB-DF10-REFINED-CANDIDATE.json")
        )
        declaration["proof_obligations"][0]["artifact"] = None
        with self.assertRaisesRegex(RecordError, "must be an object"):
            validate_declaration(declaration, self.anchor_map(), self.choice_registry)

    def test_der_requires_closed_proposition_and_empty_axiom_list(self) -> None:
        mutations = {
            "open proposition": lambda declaration: declaration["typed_body"].__setitem__(
                "closed_proposition", False
            ),
            "declared axiom": lambda declaration: declaration["replay"].__setitem__(
                "expected_axioms", ["Classical.choice"]
            ),
        }
        for label, mutate in mutations.items():
            declaration = copy.deepcopy(
                load_strict(ROOT / "bridge" / "declarations" / "EIB-TH3A-PILOT.json")
            )
            mutate(declaration)
            with self.subTest(label=label), self.assertRaisesRegex(
                PolicyViolation, "proposed DER requires"
            ):
                validate_declaration(declaration, self.anchor_map())

    def test_choice_registry_cannot_promote_choices_to_source_facts(self) -> None:
        registry = copy.deepcopy(
            load_strict(ROOT / "bridge" / "choices" / "interpretation-choices.json")
        )
        registry["choices"][0]["authority_status"] = "source-fact"
        with self.assertRaises(PolicyViolation):
            validate_choice_registry(registry)

    def test_repository_policy_pins_declared_lean_symbols(self) -> None:
        report = verify_bundle(ROOT)
        self.assertEqual(report["declarations_valid"], [
            "EIB-DF10-CANDIDATE",
            "EIB-DF10-REFINED-CANDIDATE",
            "EIB-TH3A-PILOT",
            "EIB-TH3B-PILOT",
        ])

    def test_bridge_dependencies_must_resolve_and_be_acyclic(self) -> None:
        unresolved = {"EIB-A": {"dependencies": {"bridge": ["EIB-B"]}}}
        with self.assertRaisesRegex(PolicyViolation, "unresolved bridge dependency"):
            _validate_bridge_graph(unresolved)

        cyclic = {
            "EIB-A": {"dependencies": {"bridge": ["EIB-B"]}},
            "EIB-B": {"dependencies": {"bridge": ["EIB-A"]}},
        }
        with self.assertRaisesRegex(PolicyViolation, "dependency cycle"):
            _validate_bridge_graph(cyclic)


if __name__ == "__main__":
    unittest.main()
