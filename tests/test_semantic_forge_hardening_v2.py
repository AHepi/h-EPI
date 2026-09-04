from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from creib.canonical import canonical_bytes, domain_digest
from creib.errors import PolicyViolation, RecordError
from creib.forge.hardening import (
    COMPARISON_SCHEMA,
    DECISION_SCHEMA,
    EVIDENCE_SCHEMA,
    GAIN_DOMAIN,
    NON_INDUCTIVE_LIMIT,
    PROTECTION_DOMAIN,
    RESOLUTION_SCHEMA,
    TARGET_ROLE_DOMAIN,
    build_hardening_decision,
    build_hardening_evidence,
    compute_evidence_id,
    compute_resolution_id,
    derive_hardening_obligations,
    derive_human_decision_requirements,
    publish_content_addressed_record,
    resolve_hardening_comparison,
    seal_hardening_comparison,
    validate_hardening_comparison,
    validate_hardening_evidence,
    validate_hardening_resolution,
)
from creib.strict_json import load_strict


ROOT = Path(__file__).resolve().parents[1]
DIGEST_A = "sha256:" + "a" * 64
DIGEST_B = "sha256:" + "b" * 64
DIGEST_C = "sha256:" + "c" * 64


def ref(record_id: str, digest: str = DIGEST_A) -> dict[str, str]:
    return {
        "record_id": record_id,
        "schema_version": "example.record.v1",
        "record_sha256": digest,
    }


def theory(prefix: str, digest: str) -> dict[str, object]:
    return {
        "snapshot_ref": ref(f"{prefix}-SNAPSHOT", digest),
        "review_head_ref": ref(f"{prefix}-TR", digest),
        "model_ref": ref(f"{prefix}-MODEL", digest),
        "signature_ref": ref(f"{prefix}-SIGNATURE", digest),
        "theory_record_sha256": digest,
        "dependency_closure_sha256": digest,
    }


def comparison(*, execution_semantics: str = "FINITE_EXHAUSTIVE_V1", live: tuple[str, ...] = ()) -> dict[str, object]:
    target_symbols = [
        {"symbol": "Role", "kind": "RELATION", "argument_roles": ["node"]}
    ]
    domain = (
        {"mode": "FINITE_EXHAUSTIVE", "domain_ref": ref("FINITE-DOMAIN", DIGEST_C)}
        if execution_semantics == "FINITE_EXHAUSTIVE_V1"
        else {"mode": "NONEXHAUSTIVE_SEARCH", "domain_ref": None}
    )
    body = {
        "schema_version": COMPARISON_SCHEMA,
        "record_type": "hardening_comparison",
        "declared_purpose": "Remove one role assignment without losing the retained case.",
        "baseline": theory("BASELINE", DIGEST_A),
        "successor": theory("SUCCESSOR", DIGEST_B),
        "translation_delta_ref": ref("TRANSLATION-DELTA", DIGEST_B),
        "criticism_state": {
            "snapshot_ref": ref("CRITICISM-SNAPSHOT", DIGEST_A),
            "effective_live_criticism_ids": list(live),
        },
        "target_roles": {
            "registry_id": "TARGET-ROLES-1",
            "registry_sha256": domain_digest(
                TARGET_ROLE_DOMAIN,
                {"registry_id": "TARGET-ROLES-1", "symbols": target_symbols},
            ),
            "symbols": target_symbols,
        },
        "signatures": {
            "candidate_symbols": ["Base", "Role", "Visible"],
            "old_result_symbols": ["Visible"],
            "control_symbols": ["Base", "Visible"],
            "preservation_scope_symbols": ["Base", "Visible"],
        },
        "role_view": {"kind": "GLOBAL", "localization_ref": None},
        "model_domain": domain,
        "gain": {
            "axis": "ROLE_NARROWING",
            "bad_old_result_id": None,
            "control_base_id": "CONTROL-1",
            "bad_assignment_id": "BAD-ROLE",
            "keep_assignment_id": "KEEP-ROLE",
        },
        "protections": {
            "positives": [ref("P-KEEP-1", DIGEST_A)],
            "exclusions": [],
            "consequences": [],
        },
        "necessary_clauses": [
            {
                "clause_ref": ref("CLAUSE-1", DIGEST_B),
                "defect_witness_ref": ref("DEFECT-1", DIGEST_A),
            }
        ],
        "imports": [ref("IMPORT-1", DIGEST_A)],
        "change_inventory": [
            {
                "change_id": "CHANGE-ADD",
                "disposition": "ADDED",
                "premise_kind": "PROJECT_IMPORT",
                "baseline_ref": None,
                "successor_ref": ref("IMPORT-1", DIGEST_A),
                "transport_refs": [],
            },
            {
                "change_id": "CHANGE-KEEP",
                "disposition": "RETAINED",
                "premise_kind": "SOURCE_INTERPRETATION",
                "baseline_ref": ref("SHARED-CLAIM", DIGEST_A),
                "successor_ref": ref("SHARED-CLAIM", DIGEST_A),
                "transport_refs": [],
            },
        ],
        "execution_semantics": execution_semantics,
        "semantic_verdict": None,
        "epistemic_limit": NON_INDUCTIVE_LIMIT,
    }
    return seal_hardening_comparison(body)


def payload_for(obligation: dict[str, object], record: dict[str, object]) -> dict[str, object]:
    kind = obligation["kind"]
    same = DIGEST_A
    if kind == "OLD_RESULT_NON_BROADENING":
        return {
            "payload_type": "OLD_RESULT_SETS",
            "coverage": "FINITE_EXHAUSTIVE",
            "baseline_values": ["BAD-OLD", "KEEP-OLD"],
            "successor_values": ["KEEP-OLD"],
        }
    if kind in {"ROLE_FIBER_NON_BROADENING", "TARGETED_GAIN_ROLE_FIBER"}:
        return {
            "payload_type": "ROLE_FIBERS",
            "coverage": "FINITE_EXHAUSTIVE",
            "baseline_fibers": [
                {"control_id": "CONTROL-1", "assignments": ["BAD-ROLE", "KEEP-ROLE"]}
            ],
            "successor_fibers": [
                {"control_id": "CONTROL-1", "assignments": ["KEEP-ROLE"]}
            ],
        }
    if kind == "SUCCESSOR_NON_VACUITY":
        return {
            "payload_type": "SUCCESSOR_MODELS",
            "successor_model_ids": ["SUCCESSOR-WITNESS-1"],
            "retained_positive_ids": ["P-KEEP-1"],
        }
    if kind == "POSITIVE_PRESERVATION":
        return {
            "payload_type": "POSITIVE_PAIR",
            "protection_id": obligation["subject"]["record_id"],  # type: ignore[index]
            "baseline_model_id": "BASELINE-WITNESS-1",
            "successor_model_id": "SUCCESSOR-WITNESS-1",
            "baseline_scope_sha256": same,
            "successor_scope_sha256": same,
            "baseline_classification_sha256": DIGEST_B,
            "successor_classification_sha256": DIGEST_B,
        }
    if kind == "SCOPE_PRESERVATION":
        return {
            "payload_type": "SCOPE_PAIRS",
            "scope_pairs": [
                {
                    "subject_id": "P-KEEP-1",
                    "baseline_sha256": same,
                    "successor_sha256": same,
                }
            ],
        }
    if kind == "CLAUSE_INDEPENDENCE":
        return {
            "payload_type": "CLAUSE_DELETION",
            "clause_id": obligation["subject"]["clause_ref"]["record_id"],  # type: ignore[index]
            "defect_witness_id": obligation["subject"]["defect_witness_ref"]["record_id"],  # type: ignore[index]
            "full_successor_excludes_defect": True,
            "deleted_clause_readmits_defect": True,
            "full_scope_sha256": same,
            "deleted_scope_sha256": same,
        }
    if kind == "TYPE_DEPENDENCY_PRESERVATION":
        return {
            "payload_type": "TYPE_DEPENDENCY_CHECKS",
            "delta_complete": True,
            "types_preserved": True,
            "dependencies_closed": True,
            "transports_explicit": True,
        }
    raise AssertionError(f"missing test payload for {kind}")


def all_evidence(record: dict[str, object]) -> list[dict[str, object]]:
    return [
        build_hardening_evidence(
            record, item["obligation_id"], payload_for(item, record)
        )
        for item in derive_hardening_obligations(record)
    ]


def all_accepts(
    record: dict[str, object], evidence: list[dict[str, object]]
) -> list[dict[str, object]]:
    return [
        build_hardening_decision(
            record,
            item["requirement_id"],
            disposition="ACCEPT_FOR_DECLARED_SCOPE",
            reason=f"Accept {item['decision_kind']} only for this declared comparison.",
            created_on="2026-09-03",
            considered_evidence=evidence,
        )
        for item in derive_human_decision_requirements(record)
    ]


class GenericHardeningProtocolTests(unittest.TestCase):
    def test_four_schemas_are_strict_and_accept_generated_records(self) -> None:
        record = comparison()
        evidence = all_evidence(record)
        decisions = all_accepts(record, evidence)
        resolution = resolve_hardening_comparison(record, evidence, decisions)
        cases = (
            ("hardening-comparison.schema.json", record),
            ("hardening-evidence.schema.json", evidence[0]),
            ("hardening-decision.schema.json", decisions[0]),
            ("hardening-resolution.schema.json", resolution),
        )
        for filename, instance in cases:
            with self.subTest(schema=filename):
                schema = load_strict(ROOT / "forge" / "schema" / filename)
                self.assertFalse(schema["additionalProperties"])
                Draft202012Validator.check_schema(schema)
                Draft202012Validator(schema).validate(instance)

    def test_declared_finite_payload_cannot_claim_executed_hardening(self) -> None:
        record = comparison()
        evidence = all_evidence(record)
        decisions = all_accepts(record, evidence)
        resolution = resolve_hardening_comparison(record, evidence, decisions)
        self.assertEqual(resolution["status"], "UNRESOLVED")
        self.assertTrue(all(row["state"] == "INCONCLUSIVE" for row in resolution["obligations"]))
        self.assertTrue(
            all(
                row["state"] == "ACCEPT_FOR_DECLARED_SCOPE"
                for row in resolution["human_requirements"]
            )
        )
        self.assertIsNone(resolution["semantic_verdict"])
        self.assertFalse(resolution["final"])
        self.assertEqual(resolution["result_scope"], "DECLARED_COMPARISON_ONLY")
        self.assertIn(
            "BOUND_ARTIFACT_REPLAY_UNAVAILABLE_V1", resolution["reason_codes"]
        )

    def test_resolution_cannot_validate_without_exact_inventory_replay(self) -> None:
        record = comparison()
        evidence = all_evidence(record)
        decisions = all_accepts(record, evidence)
        fabricated = copy.deepcopy(
            resolve_hardening_comparison(record, evidence, decisions)
        )
        fabricated["obligations"][0]["state"] = "WITNESSED"
        fabricated["resolution_id"] = compute_resolution_id(fabricated)

        with self.assertRaisesRegex(PolicyViolation, "exact evidence and decision"):
            validate_hardening_resolution(
                fabricated,
                record,
                evidence,
                decisions,
            )

    def test_caller_declared_counterexample_remains_inconclusive(self) -> None:
        record = comparison()
        evidence = all_evidence(record)
        old = next(
            item
            for item in derive_hardening_obligations(record)
            if item["kind"] == "OLD_RESULT_NON_BROADENING"
        )
        counter = build_hardening_evidence(
            record,
            old["obligation_id"],
            {
                "payload_type": "OLD_RESULT_SETS",
                "coverage": "FINITE_EXHAUSTIVE",
                "baseline_values": ["KEEP-OLD"],
                "successor_values": ["KEEP-OLD", "NEW-OLD"],
            },
        )
        self.assertEqual(counter["outcome"], "INCONCLUSIVE")
        evidence.append(counter)
        resolution = resolve_hardening_comparison(
            record, evidence, all_accepts(record, evidence)
        )
        self.assertEqual(resolution["status"], "UNRESOLVED")
        self.assertNotIn("MECHANICAL_COUNTERWITNESS", resolution["reason_codes"])

    def test_none_v1_semantics_cannot_be_promoted_by_human_acceptance(self) -> None:
        record = comparison(execution_semantics="NONE_V1")
        evidence = all_evidence(record)
        self.assertTrue(all(item["outcome"] == "INCONCLUSIVE" for item in evidence))
        resolution = resolve_hardening_comparison(
            record, evidence, all_accepts(record, evidence)
        )
        self.assertEqual(resolution["status"], "UNRESOLVED")
        self.assertIn("EXECUTION_SEMANTICS_UNAVAILABLE", resolution["reason_codes"])

    def test_nonexhaustive_search_cannot_witness_a_universal(self) -> None:
        record = comparison()
        old = next(
            item
            for item in derive_hardening_obligations(record)
            if item["kind"] == "OLD_RESULT_NON_BROADENING"
        )
        evidence = build_hardening_evidence(
            record,
            old["obligation_id"],
            {
                "payload_type": "OLD_RESULT_SETS",
                "coverage": "NONEXHAUSTIVE_SEARCH",
                "baseline_values": ["KEEP-OLD"],
                "successor_values": ["KEEP-OLD"],
            },
        )
        self.assertEqual(evidence["outcome"], "INCONCLUSIVE")

    def test_missing_evidence_and_live_criticism_stay_unresolved(self) -> None:
        base = comparison()
        self.assertEqual(
            resolve_hardening_comparison(base, [], all_accepts(base, []))["status"],
            "UNRESOLVED",
        )
        live = comparison(live=("CRITICISM-1",))
        evidence = all_evidence(live)
        resolution = resolve_hardening_comparison(
            live, evidence, all_accepts(live, evidence)
        )
        self.assertEqual(resolution["status"], "UNRESOLVED")
        self.assertIn("EFFECTIVE_LIVE_CRITICISM", resolution["reason_codes"])

    def test_human_defeat_is_no_hardening_but_suspension_is_unresolved(self) -> None:
        record = comparison()
        evidence = all_evidence(record)
        requirements = derive_human_decision_requirements(record)
        accepts = all_accepts(record, evidence)
        target = requirements[0]
        for disposition, expected in (
            ("SUSPEND", "UNRESOLVED"),
            ("COMPARISON_DEFECT", "UNRESOLVED"),
            ("DEFEATS_HARDENING", "NO_HARDENING"),
        ):
            with self.subTest(disposition=disposition):
                replacement = build_hardening_decision(
                    record,
                    target["requirement_id"],
                    disposition=disposition,
                    reason="This exact scoped requirement remains criticized.",
                    created_on="2026-09-03",
                    considered_evidence=evidence,
                )
                decisions = [
                    replacement if item["requirement_id"] == target["requirement_id"] else item
                    for item in accepts
                ]
                self.assertEqual(
                    resolve_hardening_comparison(record, evidence, decisions)["status"],
                    expected,
                )

    def test_fabricated_outcome_and_changed_checker_are_rejected(self) -> None:
        record = comparison()
        evidence = all_evidence(record)[0]
        fabricated = copy.deepcopy(evidence)
        fabricated["outcome"] = (
            "COUNTERWITNESSED"
            if evidence["outcome"] == "WITNESSED"
            else "WITNESSED"
        )
        fabricated["evidence_id"] = compute_evidence_id(fabricated)
        with self.assertRaisesRegex(PolicyViolation, "does not replay"):
            validate_hardening_evidence(fabricated, record)
        changed = copy.deepcopy(evidence)
        changed["checker"]["implementation_sha256"] = DIGEST_C
        changed["evidence_id"] = compute_evidence_id(changed)
        with self.assertRaisesRegex(PolicyViolation, "checker"):
            validate_hardening_evidence(changed, record)

    def test_signature_and_target_role_constraints_are_enforced(self) -> None:
        record = comparison()
        for mutation in ("target-in-scope", "old-outside-scope"):
            body = copy.deepcopy(record)
            body.pop("comparison_id")
            if mutation == "target-in-scope":
                body["signatures"]["preservation_scope_symbols"].append("Role")
                body["signatures"]["preservation_scope_symbols"].sort()
            else:
                body["signatures"]["old_result_symbols"] = ["Base", "Visible"]
                body["signatures"]["preservation_scope_symbols"] = ["Visible"]
            with self.subTest(mutation=mutation), self.assertRaises(PolicyViolation):
                seal_hardening_comparison(body)

    def test_plain_reference_or_scalar_fields_cannot_be_laundered_in(self) -> None:
        record = comparison()
        body = copy.deepcopy(record)
        body.pop("comparison_id")
        body["score"] = 99
        with self.assertRaises(RecordError):
            seal_hardening_comparison(body)
        evidence = all_evidence(record)[0]
        evidence["pass_count"] = 1000
        evidence["evidence_id"] = compute_evidence_id(evidence)
        with self.assertRaises(RecordError):
            validate_hardening_evidence(evidence, record)

    def test_decision_lineage_fork_or_gap_fails_closed(self) -> None:
        record = comparison()
        evidence = all_evidence(record)
        requirement = derive_human_decision_requirements(record)[0]
        genesis = build_hardening_decision(
            record,
            requirement["requirement_id"],
            disposition="SUSPEND",
            reason="Awaiting exact review.",
            created_on="2026-09-03",
            considered_evidence=evidence,
        )
        successor = build_hardening_decision(
            record,
            requirement["requirement_id"],
            disposition="ACCEPT_FOR_DECLARED_SCOPE",
            reason="Scoped review supplied.",
            created_on="2026-09-04",
            decision_sequence=2,
            previous_decision_id=genesis["decision_id"],
            considered_evidence=evidence,
        )
        remaining = [
            item
            for item in all_accepts(record, evidence)
            if item["requirement_id"] != requirement["requirement_id"]
        ]
        resolution = resolve_hardening_comparison(
            record, evidence, [genesis, successor, *remaining]
        )
        self.assertEqual(resolution["status"], "UNRESOLVED")
        broken = copy.deepcopy(successor)
        broken["previous_decision_id"] = "HD:" + "f" * 64
        from creib.forge.hardening import compute_decision_id

        broken["decision_id"] = compute_decision_id(broken)
        with self.assertRaisesRegex(PolicyViolation, "forked, gapped, or mislinked"):
            resolve_hardening_comparison(
                record, evidence, [genesis, broken, *remaining]
            )

    def test_content_addressed_publication_is_idempotent_not_clobbering(self) -> None:
        record = comparison()
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / f"{record['comparison_id']}.json"
            publish_content_addressed_record(record, path)
            publish_content_addressed_record(record, path)
            self.assertEqual(path.read_bytes(), canonical_bytes(record) + b"\n")
            path.write_bytes(b"different\n")
            with self.assertRaisesRegex(RecordError, "different bytes"):
                publish_content_addressed_record(record, path)

    def test_record_ids_bind_every_change(self) -> None:
        first = comparison()
        body = copy.deepcopy(first)
        body.pop("comparison_id")
        body["declared_purpose"] = "A changed bounded purpose."
        second = seal_hardening_comparison(body)
        self.assertNotEqual(first["comparison_id"], second["comparison_id"])
        self.assertNotEqual(
            derive_hardening_obligations(first)[0]["obligation_id"],
            derive_hardening_obligations(second)[0]["obligation_id"],
        )

    def test_protocol_vocabulary_has_no_truth_or_probability_status(self) -> None:
        statuses = {
            "HARDENING_UNREFUTED",
            "NO_HARDENING",
            "UNRESOLVED",
            "WITNESSED",
            "COUNTERWITNESSED",
            "INCONCLUSIVE",
        }
        for status in statuses:
            for forbidden in ("CONFIRMED", "PROBABLE", "SUPPORTED", "TRUE"):
                self.assertNotIn(forbidden, status)


if __name__ == "__main__":
    unittest.main()
