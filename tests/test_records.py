from __future__ import annotations

import copy
import unittest
from pathlib import Path

from creib.canonical import domain_digest
from creib.errors import AnchorMismatch, PolicyViolation, RecordError
from creib.models import validate_anchor, validate_declaration, validate_manifest
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
            validate_declaration(declaration, {record["anchor_digest"]: payload})

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
            validate_declaration(declaration, anchor_map)

    def test_repository_policy_pins_declared_lean_symbols(self) -> None:
        report = verify_bundle(ROOT)
        self.assertEqual(report["declarations_valid"], [
            "EIB-DF10-CANDIDATE",
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
