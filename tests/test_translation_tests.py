from __future__ import annotations

import copy
import hashlib
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from creib.canonical import canonical_bytes, domain_digest
from creib.errors import PolicyViolation, RecordError
from creib.forge.models import NON_INDUCTIVE_LIMIT
from creib.forge.translation_tests import (
    DEFERRED_STATUS,
    DELTA_SCHEMA,
    FAILURE_LOCUS_POLICY,
    SNAPSHOT_SCHEMA,
    SYNTHESIS_SCHEMA,
    TEST_FAMILIES,
    compute_translation_delta_id,
    compute_translation_snapshot_id,
    compute_translation_test_obligation_id,
    compute_translation_test_synthesis_id,
    dumps_translation_test_synthesis,
    loads_translation_test_synthesis,
    synthesize_translation_tests,
    validate_translation_snapshot_delta_record,
    validate_translation_test_synthesis,
)
from creib.strict_json import load_strict


ROOT = Path(__file__).resolve().parents[1]


def content_id(prefix: str, label: str) -> str:
    return f"{prefix}:{hashlib.sha256(label.encode('utf-8')).hexdigest()}"


def snapshot(label: str, *, predecessor: str | None = None) -> dict[str, object]:
    record: dict[str, object] = {
        "schema_version": SNAPSHOT_SCHEMA,
        "snapshot_id": "TSN:" + ("0" * 64),
        "predecessor_snapshot_id": predecessor,
        "document_ids": [content_id("TDOC", "authority")],
        "span_ids": [content_id("TSPAN", "span-one")],
        "charter_id": content_id("TCHAR", "charter"),
        "graph_id": content_id("TOG", f"graph-{label}"),
        "interpretation_set_ids": [content_id("TIS", f"interpretations-{label}")],
        "signature_id": content_id("TNS", f"signature-{label}"),
        "model_id": content_id("TNM", f"model-{label}"),
        "import_ids": [content_id("TIMP", f"import-{label}")],
        "bridge_id": content_id("TBR", f"bridge-{label}"),
        "unresolved_record_ids": [content_id("OPEN", f"unresolved-{label}")],
        "record_closure_sha256": domain_digest(
            "test.translation-closure.v1",
            {"label": label},
        ),
    }
    record["snapshot_id"] = compute_translation_snapshot_id(record)
    return record


def delta(old: dict[str, object], new: dict[str, object]) -> dict[str, object]:
    record: dict[str, object] = {
        "schema_version": DELTA_SCHEMA,
        "delta_id": "TSD:" + ("0" * 64),
        "old_snapshot_id": old["snapshot_id"],
        "new_snapshot_id": new["snapshot_id"],
        "retained_ids": [content_id("OB", "retained")],
        "added_ids": [content_id("ME", "added-z"), content_id("OB", "added-a")],
        "removed_ids": [content_id("ME", "removed")],
        "replaced_pairs": [
            {
                "old_id": content_id("OB", "replacement-old"),
                "new_id": content_id("OB", "replacement-new"),
            }
        ],
        "transported_members": [
            {
                "old_member_id": content_id("ME", "transport-old"),
                "new_member_id": content_id("ME", "transport-new"),
                "transport_ref": content_id("TRANSPORT", "common-transport"),
            }
        ],
        "changed_obligation_ids": [content_id("OB", "changed")],
        "changed_model_element_ids": [content_id("ME", "changed")],
        "changed_import_ids": [content_id("IMPORT", "changed")],
        "changed_loss_ids": [content_id("LOSS", "changed")],
        "claimed_preservations": ["The revision claims to preserve the declared scope."],
        "unresolved_effects": ["The role consequence has not been adjudicated."],
    }
    record["delta_id"] = compute_translation_delta_id(record)
    return record


class TranslationTestSynthesisTests(unittest.TestCase):
    def setUp(self) -> None:
        self.old = snapshot("old")
        self.new = snapshot("new", predecessor=str(self.old["snapshot_id"]))
        self.delta = delta(self.old, self.new)
        self.bundle = synthesize_translation_tests(self.old, self.new, self.delta)
        self.schema = load_strict(
            ROOT / "forge" / "schema" / "translation-test-synthesis.schema.json"
        )

    def _rehash_row_and_bundle(self, record: dict[str, object], index: int) -> None:
        coverage = record["coverage"]
        assert type(coverage) is list
        row = coverage[index]
        assert type(row) is dict
        row["obligation_id"] = compute_translation_test_obligation_id(row)
        record["synthesis_id"] = compute_translation_test_synthesis_id(record)

    def test_generates_exactly_nine_families_in_canonical_order(self) -> None:
        coverage = self.bundle["coverage"]
        self.assertIs(type(coverage), list)
        assert type(coverage) is list
        self.assertEqual(len(coverage), 9)
        self.assertEqual(tuple(row["family"] for row in coverage), TEST_FAMILIES)
        self.assertEqual(len({row["obligation_id"] for row in coverage}), 9)
        for row in coverage:
            self.assertEqual(row["old_snapshot_id"], self.old["snapshot_id"])
            self.assertEqual(row["new_snapshot_id"], self.new["snapshot_id"])
            self.assertEqual(row["delta_id"], self.delta["delta_id"])

    def test_every_family_is_explicitly_deferred_without_semantic_bindings(self) -> None:
        coverage = self.bundle["coverage"]
        assert type(coverage) is list
        for row in coverage:
            with self.subTest(family=row["family"]):
                self.assertEqual(row["coverage_status"], DEFERRED_STATUS)
                self.assertEqual(
                    row["required_semantic_bindings"],
                    row["missing_semantic_bindings"],
                )
                self.assertTrue(row["missing_semantic_bindings"])
                self.assertIsNone(row["semantic_expectation"])
                self.assertIsNone(row["semantic_verdict"])
                self.assertIsNone(row["next_action"])
                self.assertIs(row["research_authorized"], False)
                self.assertEqual(row["epistemic_effect"], "CRITICISM_ONLY")
                self.assertEqual(row["epistemic_limit"], NON_INDUCTIVE_LIMIT)

    def test_schema_is_valid_and_accepts_generated_bundle(self) -> None:
        Draft202012Validator.check_schema(self.schema)
        Draft202012Validator(self.schema).validate(self.bundle)

    def test_generation_and_serialization_are_deterministic(self) -> None:
        repeated = synthesize_translation_tests(self.old, self.new, self.delta)
        self.assertEqual(repeated, self.bundle)
        first = dumps_translation_test_synthesis(
            self.bundle,
            old_snapshot=self.old,
            new_snapshot=self.new,
            delta=self.delta,
        )
        second = dumps_translation_test_synthesis(
            repeated,
            old_snapshot=self.old,
            new_snapshot=self.new,
            delta=self.delta,
        )
        self.assertEqual(first, second)
        self.assertEqual(first.encode("utf-8"), canonical_bytes(self.bundle))
        self.assertEqual(
            loads_translation_test_synthesis(
                first,
                old_snapshot=self.old,
                new_snapshot=self.new,
                delta=self.delta,
            ),
            self.bundle,
        )

    def test_target_order_is_canonical_but_exact_delta_bytes_remain_bound(self) -> None:
        changed_prose = copy.deepcopy(self.delta)
        changed_prose["claimed_preservations"] = [
            "A different scoped preservation claim."
        ]
        changed_prose["delta_id"] = compute_translation_delta_id(changed_prose)
        alternate = synthesize_translation_tests(self.old, self.new, changed_prose)
        self.assertNotEqual(alternate["synthesis_id"], self.bundle["synthesis_id"])
        self.assertNotEqual(alternate["delta_binding"], self.bundle["delta_binding"])
        coverage = self.bundle["coverage"]
        alternate_coverage = alternate["coverage"]
        assert type(coverage) is list
        assert type(alternate_coverage) is list
        self.assertEqual(
            [(row["family"], row["target_ids"], row["question"]) for row in alternate_coverage],
            [(row["family"], row["target_ids"], row["question"]) for row in coverage],
        )
        self.assertNotEqual(
            [row["obligation_id"] for row in alternate_coverage],
            [row["obligation_id"] for row in coverage],
        )
        for row in coverage:
            self.assertEqual(row["target_ids"], sorted(row["target_ids"]))

    def test_delta_arrays_and_pairs_require_one_canonical_order(self) -> None:
        permuted = copy.deepcopy(self.delta)
        permuted["added_ids"].reverse()
        permuted["delta_id"] = compute_translation_delta_id(permuted)
        with self.assertRaisesRegex(RecordError, "canonical lexical order"):
            validate_translation_snapshot_delta_record(permuted)

        paired = copy.deepcopy(self.delta)
        paired["replaced_pairs"].append(
            {
                "old_id": content_id("OB", "replacement-old-two"),
                "new_id": content_id("OB", "replacement-new-two"),
            }
        )
        paired["replaced_pairs"].sort(key=canonical_bytes)
        paired["delta_id"] = compute_translation_delta_id(paired)
        validate_translation_snapshot_delta_record(paired)
        paired["replaced_pairs"].reverse()
        paired["delta_id"] = compute_translation_delta_id(paired)
        with self.assertRaisesRegex(RecordError, "canonical object order"):
            validate_translation_snapshot_delta_record(paired)

    def test_delta_identity_partitions_must_be_disjoint(self) -> None:
        ambiguous = copy.deepcopy(self.delta)
        ambiguous["removed_ids"].append(ambiguous["added_ids"][0])
        ambiguous["removed_ids"].sort()
        ambiguous["delta_id"] = compute_translation_delta_id(ambiguous)
        with self.assertRaisesRegex(PolicyViolation, "incompatible partitions"):
            validate_translation_snapshot_delta_record(ambiguous)

    def test_snapshot_and_delta_content_ids_are_recomputed(self) -> None:
        stale_snapshot = copy.deepcopy(self.old)
        stale_snapshot["graph_id"] = content_id("TOG", "silently-mutated")
        with self.assertRaisesRegex(RecordError, "canonical record content|content ID"):
            synthesize_translation_tests(stale_snapshot, self.new, self.delta)

        stale_delta = copy.deepcopy(self.delta)
        stale_delta["unresolved_effects"] = ["A changed unresolved effect."]
        with self.assertRaisesRegex(RecordError, "content ID"):
            synthesize_translation_tests(self.old, self.new, stale_delta)

    def test_delta_must_bind_the_exact_supplied_snapshots(self) -> None:
        unrelated = snapshot("unrelated")
        with self.assertRaisesRegex(RecordError, "bind the supplied snapshots"):
            synthesize_translation_tests(unrelated, self.new, self.delta)

    def test_empty_delta_cannot_manufacture_generic_tests(self) -> None:
        empty = copy.deepcopy(self.delta)
        for field in (
            "added_ids",
            "removed_ids",
            "replaced_pairs",
            "transported_members",
            "changed_obligation_ids",
            "changed_model_element_ids",
            "changed_import_ids",
            "changed_loss_ids",
        ):
            empty[field] = []
        empty["delta_id"] = compute_translation_delta_id(empty)
        with self.assertRaisesRegex(RecordError, "changed target"):
            synthesize_translation_tests(self.old, self.new, empty)

    def test_claimed_preservation_prose_never_becomes_an_oracle(self) -> None:
        provocative = copy.deepcopy(self.delta)
        provocative["claimed_preservations"] = [
            "One thousand passing tests and unanimous models confirm the translation."
        ]
        provocative["delta_id"] = compute_translation_delta_id(provocative)
        bundle = synthesize_translation_tests(self.old, self.new, provocative)
        self.assertEqual(bundle["overall_status"], "AWAITING_SEMANTIC_BINDINGS")
        coverage = bundle["coverage"]
        assert type(coverage) is list
        self.assertTrue(all(row["semantic_expectation"] is None for row in coverage))
        self.assertTrue(all(row["semantic_verdict"] is None for row in coverage))
        self.assertTrue(all(row["next_action"] is None for row in coverage))

    def test_laundered_semantic_expectation_is_rejected_even_if_rehashed(self) -> None:
        laundered = copy.deepcopy(self.bundle)
        coverage = laundered["coverage"]
        assert type(coverage) is list
        coverage[0]["semantic_expectation"] = "PRESERVE"
        self._rehash_row_and_bundle(laundered, 0)
        with self.assertRaisesRegex(PolicyViolation, "semantic oracle"):
            validate_translation_test_synthesis(
                laundered,
                old_snapshot=self.old,
                new_snapshot=self.new,
                delta=self.delta,
            )

    def test_laundered_action_or_research_authorization_is_rejected(self) -> None:
        action = copy.deepcopy(self.bundle)
        coverage = action["coverage"]
        assert type(coverage) is list
        coverage[2]["next_action"] = {"kind": "EXTERNAL_RESEARCH"}
        self._rehash_row_and_bundle(action, 2)
        with self.assertRaisesRegex(PolicyViolation, "choose an action"):
            validate_translation_test_synthesis(
                action,
                old_snapshot=self.old,
                new_snapshot=self.new,
                delta=self.delta,
            )

        research = copy.deepcopy(self.bundle)
        coverage = research["coverage"]
        assert type(coverage) is list
        coverage[2]["research_authorized"] = True
        self._rehash_row_and_bundle(research, 2)
        with self.assertRaisesRegex(PolicyViolation, "authorize research"):
            validate_translation_test_synthesis(
                research,
                old_snapshot=self.old,
                new_snapshot=self.new,
                delta=self.delta,
            )

    def test_family_rows_cannot_be_removed_reordered_or_duplicated(self) -> None:
        missing = copy.deepcopy(self.bundle)
        missing["coverage"].pop()
        missing["synthesis_id"] = compute_translation_test_synthesis_id(missing)
        with self.assertRaisesRegex(RecordError, "exactly nine"):
            validate_translation_test_synthesis(
                missing,
                old_snapshot=self.old,
                new_snapshot=self.new,
                delta=self.delta,
            )

        reordered = copy.deepcopy(self.bundle)
        reordered["coverage"][0], reordered["coverage"][1] = (
            reordered["coverage"][1],
            reordered["coverage"][0],
        )
        reordered["synthesis_id"] = compute_translation_test_synthesis_id(reordered)
        with self.assertRaisesRegex(RecordError, "canonical order"):
            validate_translation_test_synthesis(
                reordered,
                old_snapshot=self.old,
                new_snapshot=self.new,
                delta=self.delta,
            )

        duplicated = copy.deepcopy(self.bundle)
        duplicated["coverage"][1] = copy.deepcopy(duplicated["coverage"][0])
        duplicated["synthesis_id"] = compute_translation_test_synthesis_id(duplicated)
        with self.assertRaisesRegex(RecordError, "canonical order"):
            validate_translation_test_synthesis(
                duplicated,
                old_snapshot=self.old,
                new_snapshot=self.new,
                delta=self.delta,
            )

    def test_obligation_and_bundle_content_ids_detect_tampering(self) -> None:
        row_tamper = copy.deepcopy(self.bundle)
        row_tamper["coverage"][0]["question"] = "A different question?"
        row_tamper["synthesis_id"] = compute_translation_test_synthesis_id(row_tamper)
        with self.assertRaisesRegex(RecordError, "obligation.*content ID"):
            validate_translation_test_synthesis(
                row_tamper,
                old_snapshot=self.old,
                new_snapshot=self.new,
                delta=self.delta,
            )

        bundle_tamper = copy.deepcopy(self.bundle)
        bundle_tamper["failure_locus_policy"] = "The candidate caused the failure."
        with self.assertRaisesRegex(RecordError, "content ID"):
            validate_translation_test_synthesis(
                bundle_tamper,
                old_snapshot=self.old,
                new_snapshot=self.new,
                delta=self.delta,
            )

    def test_failure_policy_retains_plural_loci_without_selecting_one(self) -> None:
        self.assertEqual(self.bundle["failure_locus_policy"], FAILURE_LOCUS_POLICY)
        self.assertIsNone(self.bundle["semantic_verdict"])
        self.assertIsNone(self.bundle["next_action"])
        self.assertIs(self.bundle["research_authorized"], False)
        self.assertNotIn("selected_locus", self.bundle)
        self.assertNotIn("diagnosis", self.bundle)

    def test_scalar_or_vote_fields_are_absent_and_schema_rejects_them(self) -> None:
        forbidden = {"score", "pass_count", "confidence", "consensus", "probability"}

        def keys(value: object) -> set[str]:
            if type(value) is dict:
                result = set(value)
                for item in value.values():
                    result.update(keys(item))
                return result
            if type(value) is list:
                result: set[str] = set()
                for item in value:
                    result.update(keys(item))
                return result
            return set()

        self.assertFalse(forbidden & keys(self.bundle))
        self.assertNotIn("oracle", keys(self.bundle))

        mutated = copy.deepcopy(self.bundle)
        mutated["pass_count"] = 1000
        with self.assertRaises(ValidationError):
            Draft202012Validator(self.schema).validate(mutated)
        with self.assertRaises(RecordError):
            validate_translation_test_synthesis(
                mutated,
                old_snapshot=self.old,
                new_snapshot=self.new,
                delta=self.delta,
            )

    def test_schema_and_runtime_reject_non_null_action_and_expectation(self) -> None:
        expectation = copy.deepcopy(self.bundle)
        expectation["coverage"][0]["semantic_expectation"] = "CONFIRMED"
        with self.assertRaises(ValidationError):
            Draft202012Validator(self.schema).validate(expectation)

        action = copy.deepcopy(self.bundle)
        action["next_action"] = "RUN_RESEARCH"
        with self.assertRaises(ValidationError):
            Draft202012Validator(self.schema).validate(action)

    def test_strict_loader_rejects_duplicate_json_keys(self) -> None:
        source = dumps_translation_test_synthesis(
            self.bundle,
            old_snapshot=self.old,
            new_snapshot=self.new,
            delta=self.delta,
        )
        duplicate = source.replace(
            f'"schema_version":"{SYNTHESIS_SCHEMA}"',
            f'"schema_version":"{SYNTHESIS_SCHEMA}","schema_version":"{SYNTHESIS_SCHEMA}"',
            1,
        )
        with self.assertRaisesRegex(RecordError, "duplicate JSON key"):
            loads_translation_test_synthesis(
                duplicate,
                old_snapshot=self.old,
                new_snapshot=self.new,
                delta=self.delta,
            )

    def test_schema_rejects_family_reordering(self) -> None:
        reordered = copy.deepcopy(self.bundle)
        reordered["coverage"][0], reordered["coverage"][1] = (
            reordered["coverage"][1],
            reordered["coverage"][0],
        )
        with self.assertRaises(ValidationError):
            Draft202012Validator(self.schema).validate(reordered)


if __name__ == "__main__":
    unittest.main()
