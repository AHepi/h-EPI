from __future__ import annotations

import hashlib
import json
import unittest
from collections import Counter
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
QUALIFICATION = ROOT / "forge" / "translation" / "qualification"
CONTROLLER = QUALIFICATION / "controller"

AUTHORITY_REL = "forge/translation/qualification/HRC-1.authority.txt"
BLIND_PACKET_REL = "forge/translation/qualification/HRC-1.blind-packet.json"
CHARTER_REL = "forge/translation/qualification/HRC-1.translation-charter.json"
COMMITMENT_REL = (
    "forge/translation/qualification/HRC-1.construction-key.commitment.json"
)
KEY_REL = "forge/translation/qualification/controller/HRC-1.construction-key.json"
OBLIGATIONS_REL = (
    "forge/translation/qualification/controller/HRC-1.source-obligations.json"
)
MUTATIONS_REL = (
    "forge/translation/qualification/controller/HRC-1.mutation-ledger.json"
)
CONTROLS_REL = (
    "forge/translation/qualification/controller/HRC-1.benign-controls.json"
)


def _load(relative: str) -> dict[str, object]:
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    if type(value) is not dict:
        raise TypeError(f"{relative} must contain a JSON object")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class TranslationQualificationFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = _load(
            "forge/translation/qualification/HRC-1.manifest.json"
        )
        cls.blind_packet = _load(BLIND_PACKET_REL)
        cls.charter = _load(CHARTER_REL)
        cls.commitment = _load(COMMITMENT_REL)
        cls.key = _load(KEY_REL)
        cls.obligation_record = _load(OBLIGATIONS_REL)
        cls.mutation_ledger = _load(MUTATIONS_REL)
        cls.control_record = _load(CONTROLS_REL)
        cls.obligations = cls.obligation_record["obligations"]
        cls.obligation_ids = {
            item["obligation_id"] for item in cls.obligations  # type: ignore[index]
        }

    def test_manifest_binds_the_exact_fixture_artifacts(self) -> None:
        expected_paths = {
            AUTHORITY_REL,
            BLIND_PACKET_REL,
            CHARTER_REL,
            COMMITMENT_REL,
            KEY_REL,
            OBLIGATIONS_REL,
            MUTATIONS_REL,
            CONTROLS_REL,
        }
        inventory = self.manifest["artifact_inventory"]
        self.assertIs(type(inventory), list)
        paths = [item["path"] for item in inventory]  # type: ignore[index]
        self.assertEqual(paths, sorted(paths))
        self.assertEqual(set(paths), expected_paths)
        self.assertEqual(len(paths), len(set(paths)))

        for item in inventory:  # type: ignore[assignment]
            path = ROOT / item["path"]
            self.assertTrue(path.is_file(), item["path"])
            self.assertEqual(len(path.read_bytes()), item["byte_length"])
            self.assertEqual(_sha256(path), item["sha256"])

    def test_blind_packet_is_closed_and_excludes_every_controller_path(self) -> None:
        allowed = self.blind_packet["translator_allowed_paths"]
        self.assertIs(type(allowed), list)
        paths = [item["path"] for item in allowed]  # type: ignore[index]
        self.assertEqual(
            paths,
            [AUTHORITY_REL, COMMITMENT_REL, CHARTER_REL],
        )
        self.assertTrue(self.blind_packet["path_set_is_closed"])
        excluded_prefix = self.blind_packet["controller_excluded_prefix"]
        self.assertEqual(
            excluded_prefix,
            "forge/translation/qualification/controller/",
        )
        self.assertFalse(any(path.startswith(excluded_prefix) for path in paths))
        self.assertNotIn(KEY_REL, paths)
        self.assertNotIn(OBLIGATIONS_REL, paths)
        self.assertNotIn(MUTATIONS_REL, paths)
        self.assertNotIn(CONTROLS_REL, paths)

        for item in allowed:  # type: ignore[assignment]
            pure = PurePosixPath(item["path"])
            self.assertFalse(pure.is_absolute())
            self.assertNotIn("..", pure.parts)
            path = ROOT / pure
            self.assertEqual(len(path.read_bytes()), item["byte_length"])
            self.assertEqual(_sha256(path), item["sha256"])

    def test_construction_key_commitment_matches_withheld_bytes(self) -> None:
        committed = self.commitment["committed_artifact"]
        self.assertEqual(committed["path"], KEY_REL)  # type: ignore[index]
        key_path = ROOT / KEY_REL
        self.assertEqual(len(key_path.read_bytes()), committed["byte_length"])  # type: ignore[index]
        self.assertEqual(_sha256(key_path), committed["sha256"])  # type: ignore[index]
        self.assertEqual(
            self.manifest["construction_key_commitment_sha256"],
            committed["sha256"],  # type: ignore[index]
        )
        self.assertEqual(
            self.commitment["translator_access"],
            "BLIND_PACKET",
        )
        self.assertEqual(
            self.commitment["disclosure_phase"],
            "AFTER_TRANSLATION_OUTPUTS_ARE_FROZEN",
        )

    def test_source_is_exact_utf8_with_fourteen_numbered_clauses(self) -> None:
        source = (ROOT / AUTHORITY_REL).read_bytes()
        self.assertTrue(source.endswith(b"\n"))
        decoded = source.decode("utf-8")
        headings = [
            line
            for line in decoded.splitlines()
            if any(line.startswith(f"{number}. ") for number in range(1, 15))
        ]
        self.assertEqual(len(headings), 14)
        self.assertIn("¹", decoded)
        self.assertIn("Byte-identical", decoded)
        self.assertIn("Example only:", decoded)
        self.assertEqual(
            _sha256(ROOT / AUTHORITY_REL),
            self.obligation_record["source_file_sha256"],
        )

    def test_every_source_span_digest_replays_from_exact_line_bytes(self) -> None:
        source_lines = (ROOT / AUTHORITY_REL).read_bytes().splitlines(keepends=True)
        self.assertEqual(len(self.obligations), 17)
        seen_ids: set[str] = set()
        for obligation in self.obligations:  # type: ignore[assignment]
            obligation_id = obligation["obligation_id"]
            self.assertNotIn(obligation_id, seen_ids)
            seen_ids.add(obligation_id)
            self.assertTrue(obligation["facets"])
            self.assertTrue(obligation["protected_distinctions"])
            self.assertTrue(obligation["source_spans"])
            for span in obligation["source_spans"]:
                first = span["first_line"]
                last = span["last_line"]
                self.assertIs(type(first), int)
                self.assertIs(type(last), int)
                self.assertGreaterEqual(first, 1)
                self.assertGreaterEqual(last, first)
                self.assertLessEqual(last, len(source_lines))
                raw = b"".join(source_lines[first - 1 : last])
                self.assertEqual(hashlib.sha256(raw).hexdigest(), span["sha256"])
        self.assertEqual(seen_ids, self.obligation_ids)

    def test_obligation_dependencies_are_known_acyclic_and_not_self_edges(self) -> None:
        dependencies = {
            item["obligation_id"]: tuple(item["dependencies"])
            for item in self.obligations  # type: ignore[index]
        }
        for obligation_id, parents in dependencies.items():
            self.assertEqual(len(parents), len(set(parents)))
            self.assertNotIn(obligation_id, parents)
            self.assertTrue(set(parents) <= self.obligation_ids)

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(obligation_id: str) -> None:
            if obligation_id in visited:
                return
            self.assertNotIn(obligation_id, visiting, "obligation dependency cycle")
            visiting.add(obligation_id)
            for parent in dependencies[obligation_id]:
                visit(parent)
            visiting.remove(obligation_id)
            visited.add(obligation_id)

        for obligation_id in sorted(self.obligation_ids):
            visit(obligation_id)
        self.assertEqual(visited, self.obligation_ids)

    def test_construction_key_binds_obligations_and_required_discriminators(self) -> None:
        self.assertEqual(
            self.key["source_file_sha256"],
            _sha256(ROOT / AUTHORITY_REL),
        )
        self.assertEqual(
            self.key["obligation_record_sha256"],
            _sha256(ROOT / OBLIGATIONS_REL),
        )
        ground_truth = self.key["construction_ground_truth"]
        self.assertEqual(ground_truth["declared_source_obligation_count"], 17)  # type: ignore[index]
        discriminators = ground_truth["required_discriminator_families"]  # type: ignore[index]
        self.assertEqual(len(discriminators), 13)
        discriminator_ids = [item["discriminator_id"] for item in discriminators]
        self.assertEqual(len(discriminator_ids), len(set(discriminator_ids)))
        for item in discriminators:
            self.assertTrue(item["must_distinguish"])
            self.assertTrue(set(item["obligation_ids"]) <= self.obligation_ids)

        ambiguities = ground_truth["intentional_ambiguities"]  # type: ignore[index]
        self.assertEqual(len(ambiguities), 1)
        self.assertEqual(
            ambiguities[0]["allowed_reading_ids"],
            ["HRC-R-REFERENCE-CHALLENGE", "HRC-R-REFERENCE-SEAL"],
        )

    def test_mutation_ledger_is_complete_isolated_and_obligation_bound(self) -> None:
        mutations = self.mutation_ledger["mutations"]
        self.assertEqual(len(mutations), 34)
        mutation_ids = [item["mutation_id"] for item in mutations]
        self.assertEqual(len(mutation_ids), len(set(mutation_ids)))
        self.assertTrue(all(item.startswith("HRC-M-") for item in mutation_ids))
        self.assertEqual(
            Counter(item["run_kind"] for item in mutations),
            Counter({"SINGLE": 31, "COMPOUND": 3}),
        )
        self.assertEqual(
            Counter(item["category"] for item in mutations),
            Counter(
                {
                    "SEMANTIC_MODEL": 10,
                    "HARDENING": 6,
                    "SOURCE_CAPTURE": 5,
                    "OBLIGATION_GRAPH": 3,
                    "COMPOUND": 3,
                    "DECISION_BOUNDARY": 2,
                    "INTERPRETATION_FOREST": 1,
                    "BRIDGE": 1,
                    "FORMAL_EXTRACTION": 1,
                    "RESEARCH_ROUTING": 1,
                    "TEST_CONTRACT": 1,
                }
            ),
        )
        for item in mutations:
            self.assertTrue(item["injection"])
            self.assertTrue(item["expected_exposures"])
            self.assertEqual(
                len(item["expected_exposures"]),
                len(set(item["expected_exposures"])),
            )
            self.assertTrue(set(item["affected_obligation_ids"]) <= self.obligation_ids)

        all_exposures = {
            exposure
            for item in mutations
            for exposure in item["expected_exposures"]
        }
        self.assertTrue(
            {
                "AUTHORITY_IDENTITY_INVALIDATED",
                "ALTERNATIVE_READING_DROPPED",
                "CLAIM_STRENGTH_DELTA",
                "CONTEXT_INDEX_LOSS",
                "FORMAL_DEPENDENCY_GAP",
                "MODALITY_COLLAPSE",
                "NONINDUCTIVE_PROMOTION_REJECTED",
                "PLURAL_CRITICISMS_PRESERVED",
                "SCOPE_ESCAPE",
                "WRONG_EXTERNAL_RESEARCH_ROUTE",
            }
            <= all_exposures
        )

    def test_benign_controls_change_identity_without_silent_equivalence(self) -> None:
        controls = self.control_record["controls"]
        self.assertEqual(len(controls), 6)
        control_ids = [item["control_id"] for item in controls]
        self.assertEqual(len(control_ids), len(set(control_ids)))
        for item in controls:
            self.assertTrue(item["transformation"])
            self.assertTrue(item["expected_exposures"])
            self.assertTrue(set(item["affected_obligation_ids"]) <= self.obligation_ids)
        exposures = {
            exposure
            for item in controls
            for exposure in item["expected_exposures"]
        }
        self.assertIn("NO_SILENT_IDENTITY_REUSE", exposures)
        self.assertIn("HUMAN_REVIEW_REQUIRED_BEFORE_BRANCH_RETIREMENT", exposures)
        self.assertIn("NO_HARDENING_CLAIM", exposures)

    def test_fixture_records_forbid_semantic_promotion(self) -> None:
        forbidden = set(self.charter["forbidden_outputs"])
        self.assertEqual(
            forbidden,
            {
                "CONFIRMED",
                "PROVED_SEMANTICS",
                "SEMANTICALLY_TRUE",
                "TRANSLATION_CORRECT",
            },
        )
        self.assertFalse(self.charter["claim_boundary"]["semantic_truth_claimed"])
        self.assertFalse(
            self.charter["claim_boundary"]["formal_success_can_promote_fidelity"]
        )
        self.assertEqual(
            self.charter["research_policy"]["external_semantic_research_route"],
            "PROHIBITED_FOR_SYNTHETIC_SOURCE",
        )
        self.assertIsNone(self.blind_packet["semantic_verdict"])
        self.assertIsNone(self.obligation_record["semantic_verdict"])
        self.assertIsNone(self.key["epistemic_boundary"]["semantic_verdict"])
        self.assertIsNone(
            self.mutation_ledger["required_terminal_fields"]["semantic_verdict"]
        )
        self.assertIsNone(
            self.control_record["required_terminal_fields"]["semantic_verdict"]
        )
        boundary = self.manifest["qualification_claim_boundary"]
        self.assertFalse(boundary["asserts_semantic_truth"])
        self.assertFalse(boundary["asserts_translation_fidelity"])
        self.assertIsNone(boundary["semantic_verdict"])
        self.assertEqual(
            boundary["allowed_mechanical_result"],
            "ALL_DECLARED_EXPOSURES_REPRODUCED",
        )

    def test_manifest_counts_match_controller_records(self) -> None:
        counts = self.manifest["construction_counts"]
        ground_truth = self.key["construction_ground_truth"]
        self.assertEqual(counts["source_obligations"], len(self.obligations))
        self.assertEqual(counts["mutations"], len(self.mutation_ledger["mutations"]))
        self.assertEqual(counts["benign_controls"], len(self.control_record["controls"]))
        self.assertEqual(
            counts["required_discriminator_families"],
            len(ground_truth["required_discriminator_families"]),
        )


if __name__ == "__main__":
    unittest.main()
