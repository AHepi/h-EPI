from __future__ import annotations

import copy
from dataclasses import FrozenInstanceError
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from creib.canonical import domain_digest
from creib.errors import PolicyViolation, RecordError
from creib.forge.research import (
    DiscoveryRouteKind,
    HumanAdjudicationStatus,
    dumps_research_ledger,
    load_research_ledger,
    loads_research_ledger,
    parse_research_ledger,
    report_sha256,
)
from creib.strict_json import load_strict


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "forge" / "schema" / "research-ledger.schema.json"
LEDGER_PATH = ROOT / "forge" / "research" / "SMF-RESEARCH-2026-09-03.json"

EXPECTED_SOURCE_IDENTIFIERS = {
    "doi:10.1007/10722167_15",
    "doi:10.1007/978-3-031-47262-6_3",
    "arXiv:2412.13688",
    "doi:10.1007/978-3-031-77792-9_8",
    "doi:10.1109/TSE.2016.2532875",
    "doi:10.1109/TSE.2014.2372785",
    "arXiv:2605.03936",
    "arXiv:2607.27359",
}


def rehash_ledger_record(record: dict[str, object]) -> None:
    entries = record["entries"]
    assert isinstance(entries, list)
    entry_hashes = {}
    for entry in entries:
        assert isinstance(entry, dict)
        entry["report_sha256"] = report_sha256(entry["bounded_source_report"])
        unsigned = {key: value for key, value in entry.items() if key != "entry_sha256"}
        entry["entry_sha256"] = domain_digest(
            "creib.semantic-forge.external-source-entry.v2", unsigned
        ).removeprefix("sha256:")
        entry_hashes[entry["entry_id"]] = entry["entry_sha256"]
    proposals = record["project_use_proposals"]
    assert isinstance(proposals, list)
    for proposal in proposals:
        assert isinstance(proposal, dict)
        proposal["source_entry_sha256"] = entry_hashes[proposal["source_entry_id"]]
        unsigned = {
            key: value for key, value in proposal.items() if key != "proposal_sha256"
        }
        proposal["proposal_sha256"] = domain_digest(
            "creib.semantic-forge.project-use-proposal.v1", unsigned
        ).removeprefix("sha256:")
    unsigned_ledger = {
        key: value for key, value in record.items() if key != "ledger_sha256"
    }
    record["ledger_sha256"] = domain_digest(
        "creib.semantic-forge.external-research-ledger.v2", unsigned_ledger
    ).removeprefix("sha256:")


class SemanticForgeResearchLedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = load_strict(SCHEMA_PATH)
        cls.instance = load_strict(LEDGER_PATH)
        cls.validator = Draft202012Validator(cls.schema)

    def fresh_instance(self) -> dict[str, object]:
        return copy.deepcopy(self.instance)

    def test_schema_is_valid_and_every_complete_object_is_closed(self) -> None:
        Draft202012Validator.check_schema(self.schema)
        self.assertFalse(self.schema["additionalProperties"])
        for key in (
            "authority_boundary",
            "provider_policy",
            "epistemic_policy",
            "canonical_source",
            "primary_inspection",
            "discovery",
            "research_entry",
            "project_use_proposal",
            "engineering_decision",
        ):
            with self.subTest(object=key):
                self.assertFalse(self.schema["$defs"][key]["additionalProperties"])

    def test_seed_validates_and_strict_runtime_parser_loads_it(self) -> None:
        self.validator.validate(self.instance)
        ledger = load_research_ledger(LEDGER_PATH)
        self.assertEqual(ledger.to_dict(), self.instance)
        self.assertEqual(ledger.ledger_id, "SMF-RESEARCH-2026-09-03")
        self.assertEqual(len(ledger.entries), 8)
        self.assertEqual(len(ledger.project_use_proposals), 8)
        self.assertFalse(ledger.engineering_decisions)

    def test_ledger_creation_may_equal_or_follow_the_data_cutoff(self) -> None:
        for created_on in ("2026-09-03", "2026-09-04"):
            changed = self.fresh_instance()
            changed["created_on"] = created_on
            rehash_ledger_record(changed)
            with self.subTest(created_on=created_on):
                ledger = parse_research_ledger(changed)
                self.assertEqual(ledger.created_on, created_on)
                self.assertEqual(ledger.as_of_date, "2026-09-03")

    def test_ledger_creation_cannot_precede_the_data_cutoff(self) -> None:
        changed = self.fresh_instance()
        changed["created_on"] = "2026-09-02"
        rehash_ledger_record(changed)
        with self.assertRaisesRegex(
            RecordError,
            "ledger.created_on cannot precede as_of_date",
        ):
            parse_research_ledger(changed)

    def test_ledger_contains_only_the_bounded_source_set(self) -> None:
        ledger = load_research_ledger(LEDGER_PATH)
        actual = {
            entry.canonical_source.canonical_identifier for entry in ledger.entries
        }
        self.assertEqual(actual, EXPECTED_SOURCE_IDENTIFIERS)

    def test_reports_are_exactly_hashed_and_non_authoritative(self) -> None:
        ledger = load_research_ledger(LEDGER_PATH)
        self.assertFalse(ledger.authority_boundary.external_research_semantic_authority)
        self.assertFalse(ledger.authority_boundary.external_reports_are_target_semantics)
        self.assertFalse(ledger.provider_policy.provider_output_is_oracle)
        self.assertFalse(ledger.epistemic_policy.passing_reports_confirm_model)
        self.assertFalse(ledger.epistemic_policy.frequency_or_citation_count_can_promote)
        self.assertFalse(ledger.epistemic_policy.provider_agreement_can_promote)
        self.assertFalse(ledger.epistemic_policy.inductive_promotion_permitted)
        self.assertFalse(ledger.epistemic_policy.research_can_close_semantic_question)
        for entry in ledger.entries:
            with self.subTest(entry=entry.entry_id):
                self.assertEqual(
                    entry.report_sha256,
                    report_sha256(entry.bounded_source_report),
                )
                self.assertEqual(entry.claim_kind, "external_source_report")
                self.assertEqual(entry.report_author, "SMF_PROJECT")
                self.assertEqual(
                    entry.epistemic_effect,
                    "may_criticize_or_guide_engineering_only",
                )
                self.assertFalse(entry.semantic_authority)
                self.assertFalse(entry.provider_output_is_oracle)
                self.assertFalse(entry.can_confirm_target_semantics)
                self.assertIs(
                    entry.human_adjudication_status,
                    HumanAdjudicationStatus.UNREVIEWED,
                )
                self.assertTrue(entry.attacked_harness_question.strip())
                self.assertTrue(entry.falsifier.strip())
                self.assertTrue(entry.limitations)
                self.assertNotIn("SMF adopts", entry.bounded_source_report)
        for proposal in ledger.project_use_proposals:
            with self.subTest(proposal=proposal.proposal_id):
                self.assertEqual(proposal.proposal_status.value, "PROPOSED")
                self.assertFalse(proposal.semantic_authority)
                self.assertFalse(proposal.can_promote_hardening)

    def test_source_identity_version_and_dates_are_distinct_from_discovery(self) -> None:
        ledger = load_research_ledger(LEDGER_PATH)
        for entry in ledger.entries:
            with self.subTest(entry=entry.entry_id):
                source = entry.canonical_source
                self.assertTrue(source.canonical_identifier)
                self.assertTrue(source.canonical_url.startswith("https://"))
                self.assertTrue(source.version)
                self.assertTrue(source.versioned_url.startswith("https://"))
                self.assertEqual(source.as_of_date, ledger.as_of_date)
                self.assertLessEqual(source.retrieved_on, source.as_of_date)
                self.assertTrue(entry.discovery.route_locator)
                self.assertEqual(entry.primary_inspection.locator, source.versioned_url)
                self.assertEqual(entry.primary_inspection.version, source.version)
                self.assertTrue(entry.primary_inspection.primary_source_inspected)
                self.assertIsNone(entry.primary_inspection.source_artifact_sha256)
                if source.canonical_identifier.startswith("doi:"):
                    self.assertEqual(
                        source.canonical_url,
                        "https://doi.org/" + source.canonical_identifier.removeprefix("doi:"),
                    )
                else:
                    self.assertEqual(
                        source.canonical_url,
                        "https://arxiv.org/abs/"
                        + source.canonical_identifier.removeprefix("arXiv:"),
                    )
                    self.assertEqual(
                        source.versioned_url,
                        source.canonical_url + source.version,
                    )

    def test_alphaxiv_is_a_replaceable_non_oracular_discovery_default(self) -> None:
        ledger = load_research_ledger(LEDGER_PATH)
        policy = ledger.provider_policy
        self.assertEqual(policy.default_contemporary_discovery_provider, "AlphaXiv")
        self.assertEqual(policy.contemporary_from_year, 2024)
        self.assertEqual(policy.consensus_role, "optional_independent_cross_check")
        self.assertTrue(policy.providers_replaceable)
        self.assertTrue(policy.direct_primary_source_required)
        self.assertTrue(any(entry.discovery.provider == "AlphaXiv" for entry in ledger.entries))
        for entry in ledger.entries:
            contemporary = entry.canonical_source.publication_year >= 2024
            with self.subTest(entry=entry.entry_id):
                self.assertIs(entry.discovery.contemporary, contemporary)
                if entry.discovery.route_kind is DiscoveryRouteKind.DEFAULT_CONTEMPORARY:
                    self.assertTrue(contemporary)
                    self.assertEqual(entry.discovery.provider, policy.default_contemporary_discovery_provider)
                    self.assertIs(
                        entry.discovery.route_kind,
                        DiscoveryRouteKind.DEFAULT_CONTEMPORARY,
                    )
                if entry.discovery.provider == "AlphaXiv":
                    self.assertIn("alphaxiv.org", entry.discovery.route_locator)

    def test_records_are_immutable_at_every_parsed_layer(self) -> None:
        ledger = load_research_ledger(LEDGER_PATH)
        with self.assertRaises(FrozenInstanceError):
            ledger.title = "changed"  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            ledger.entries[0].title = "changed"  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            ledger.entries[0].canonical_source.version = "changed"  # type: ignore[misc]

    def test_unknown_fields_are_rejected_at_top_and_nested_levels(self) -> None:
        for label, path in (
            ("root", ("confidence_score",)),
            ("authority", ("authority_boundary", "research_vote")),
            ("source", ("entries", 0, "canonical_source", "abstract")),
            ("entry", ("entries", 0, "semantic_score")),
        ):
            changed = self.fresh_instance()
            target: object = changed
            for part in path[:-1]:
                target = target[part]  # type: ignore[index]
            target[path[-1]] = 1  # type: ignore[index]
            with self.subTest(layer=label):
                with self.assertRaises(RecordError):
                    parse_research_ledger(changed)
                with self.assertRaises(ValidationError):
                    self.validator.validate(changed)

    def test_missing_fields_are_rejected_at_top_and_nested_levels(self) -> None:
        for label, path in (
            ("root", ("as_of_date",)),
            ("policy", ("epistemic_policy", "research_can_close_semantic_question")),
            ("source", ("entries", 0, "canonical_source", "retrieved_on")),
            ("entry", ("entries", 0, "falsifier")),
        ):
            changed = self.fresh_instance()
            target: object = changed
            for part in path[:-1]:
                target = target[part]  # type: ignore[index]
            del target[path[-1]]  # type: ignore[index]
            with self.subTest(layer=label):
                with self.assertRaises(RecordError):
                    parse_research_ledger(changed)
                with self.assertRaises(ValidationError):
                    self.validator.validate(changed)

    def test_duplicate_json_keys_fail_before_semantic_parsing(self) -> None:
        raw = LEDGER_PATH.read_text(encoding="utf-8")
        original = (
            '  "title": "Semantic Model Forge bounded external-research reports",'
        )
        duplicated = original + '\n  "title": "duplicate",'
        self.assertIn(original, raw)
        with self.assertRaisesRegex(RecordError, "duplicate JSON key"):
            loads_research_ledger(raw.replace(original, duplicated, 1))

    def test_duplicate_entry_ids_and_source_ids_are_rejected(self) -> None:
        duplicate_entry = self.fresh_instance()
        duplicate_entry["entries"].append(  # type: ignore[union-attr]
            copy.deepcopy(duplicate_entry["entries"][0])  # type: ignore[index]
        )
        with self.assertRaisesRegex(RecordError, "entry IDs must be unique"):
            parse_research_ledger(duplicate_entry)

        duplicate_source = self.fresh_instance()
        copied = copy.deepcopy(duplicate_source["entries"][0])  # type: ignore[index]
        copied["entry_id"] = "SMF-RES-DUPLICATE-SOURCE"
        duplicate_source["entries"].append(copied)  # type: ignore[union-attr]
        with self.assertRaisesRegex(RecordError, "source identifiers must be unique|entry_sha256"):
            parse_research_ledger(duplicate_source)

        doi_alias = self.fresh_instance()
        original = next(
            entry
            for entry in doi_alias["entries"]  # type: ignore[union-attr]
            if "TSE" in entry["canonical_source"]["canonical_identifier"]
        )
        copied_alias = copy.deepcopy(original)
        copied_alias["entry_id"] = "SMF-RES-DUPLICATE-DOI-CASE-ALIAS"
        copied_alias["canonical_source"]["canonical_identifier"] = (
            copied_alias["canonical_source"]["canonical_identifier"].lower()
        )
        copied_alias["canonical_source"]["canonical_url"] = (
            copied_alias["canonical_source"]["canonical_url"].lower()
        )
        doi_alias["entries"].append(copied_alias)  # type: ignore[union-attr]
        with self.assertRaisesRegex(
            RecordError,
            "source identifiers must be unique|entry_sha256|versioned URL",
        ):
            parse_research_ledger(doi_alias)

    def test_report_text_tampering_requires_a_new_hash(self) -> None:
        changed = self.fresh_instance()
        changed["entries"][0]["bounded_source_report"] += " Altered."  # type: ignore[index,operator]
        with self.assertRaisesRegex(RecordError, "report_sha256 mismatch"):
            parse_research_ledger(changed)

    def test_recomputed_report_hash_cannot_hide_entry_rewrite(self) -> None:
        changed = self.fresh_instance()
        entry = changed["entries"][0]  # type: ignore[index]
        entry["bounded_source_report"] = "A replacement source report."
        entry["report_sha256"] = report_sha256(entry["bounded_source_report"])
        with self.assertRaisesRegex(RecordError, "entry_sha256 mismatch"):
            parse_research_ledger(changed)

    def test_entry_digest_is_bound_into_separate_project_use_proposal(self) -> None:
        changed = self.fresh_instance()
        entry = changed["entries"][0]  # type: ignore[index]
        entry["attacked_harness_question"] = "A replacement question."
        unsigned = {key: value for key, value in entry.items() if key != "entry_sha256"}
        entry["entry_sha256"] = domain_digest(
            "creib.semantic-forge.external-source-entry.v2", unsigned
        ).removeprefix("sha256:")
        with self.assertRaisesRegex(RecordError, "source-entry digest mismatch"):
            parse_research_ledger(changed)

    def test_complete_ledger_digest_detects_unversioned_snapshot_rewrite(self) -> None:
        changed = self.fresh_instance()
        changed["title"] += " rewritten"  # type: ignore[operator]
        with self.assertRaisesRegex(RecordError, "ledger_sha256 mismatch"):
            parse_research_ledger(changed)

    def test_source_reports_and_project_use_have_distinct_typed_scopes(self) -> None:
        ledger = load_research_ledger(LEDGER_PATH)
        self.assertTrue(ledger.project_use_proposals)
        self.assertFalse(ledger.engineering_decisions)
        for entry in ledger.entries:
            self.assertEqual(entry.report_scope, "source_claims_only")
            self.assertNotIn("SMF adopts", entry.bounded_source_report)
        for proposal in ledger.project_use_proposals:
            self.assertEqual(proposal.proposal_status.value, "PROPOSED")
            self.assertFalse(proposal.semantic_authority)
            self.assertFalse(proposal.can_promote_hardening)

    def test_project_use_cannot_self_adopt_or_promote_hardening(self) -> None:
        for field, value in (
            ("proposal_status", "ADOPTED"),
            ("semantic_authority", True),
            ("can_promote_hardening", True),
        ):
            changed = self.fresh_instance()
            changed["project_use_proposals"][0][field] = value  # type: ignore[index]
            with self.subTest(field=field):
                with self.assertRaises((PolicyViolation, RecordError)):
                    parse_research_ledger(changed)
                with self.assertRaises(ValidationError):
                    self.validator.validate(changed)

    def test_v2_rejects_unauthenticated_engineering_decisions(self) -> None:
        changed = self.fresh_instance()
        proposal = changed["project_use_proposals"][0]  # type: ignore[index]
        changed["engineering_decisions"].append(  # type: ignore[union-attr]
            {
                "schema_version": "creib.semantic-forge.engineering-decision.v1",
                "decision_id": "SMF-DEC-CEGAR-TRIAGE-001",
                "proposal_id": proposal["proposal_id"],
                "proposal_sha256": proposal["proposal_sha256"],
                "disposition": "ADOPT",
                "rationale": "Adopt as a revisable harness-engineering control only.",
                "decided_on": "2026-09-03",
                "decision_maker_role": "HUMAN_REVIEWER",
                "decision_scope": "HARNESS_ENGINEERING_ONLY",
                "semantic_authority": False,
                "can_promote_hardening": False,
            }
        )
        rehash_ledger_record(changed)
        with self.assertRaisesRegex(
            PolicyViolation,
            "cannot authenticate human engineering decisions",
        ):
            parse_research_ledger(changed)
        with self.assertRaises(ValidationError):
            self.validator.validate(changed)

    def test_runtime_rejects_empty_project_use_proposals_like_schema(self) -> None:
        changed = self.fresh_instance()
        changed["project_use_proposals"] = []
        rehash_ledger_record(changed)
        with self.assertRaisesRegex(RecordError, "non-empty tuple"):
            parse_research_ledger(changed)
        with self.assertRaises(ValidationError):
            self.validator.validate(changed)

    def test_retrieval_cannot_predate_source_publication(self) -> None:
        changed = self.fresh_instance()
        entry = next(
            item
            for item in changed["entries"]  # type: ignore[union-attr]
            if item["canonical_source"]["source_kind"] == "arxiv"
        )
        entry["canonical_source"]["retrieved_on"] = "1900-01-01"
        entry["primary_inspection"]["retrieved_on"] = "1900-01-01"
        entry["discovery"]["discovered_on"] = "1900-01-01"
        rehash_ledger_record(changed)
        with self.assertRaisesRegex(RecordError, "cannot predate publication_year"):
            parse_research_ledger(changed)

    def test_discovery_cannot_predate_source_publication(self) -> None:
        changed = self.fresh_instance()
        entry = next(
            item
            for item in changed["entries"]  # type: ignore[union-attr]
            if item["canonical_source"]["source_kind"] == "arxiv"
        )
        entry["discovery"]["discovered_on"] = "1900-01-01"
        rehash_ledger_record(changed)
        with self.assertRaisesRegex(
            RecordError,
            "discovery.discovered_on cannot predate publication_year",
        ):
            parse_research_ledger(changed)

    def test_every_inductive_promotion_switch_fails_closed(self) -> None:
        cases = (
            ("authority semantic authority", "authority_boundary", "external_research_semantic_authority"),
            ("reports become semantics", "authority_boundary", "external_reports_are_target_semantics"),
            ("passing confirms", "epistemic_policy", "passing_reports_confirm_model"),
            ("frequency promotes", "epistemic_policy", "frequency_or_citation_count_can_promote"),
            ("agreement promotes", "epistemic_policy", "provider_agreement_can_promote"),
            ("induction permitted", "epistemic_policy", "inductive_promotion_permitted"),
            ("research closes", "epistemic_policy", "research_can_close_semantic_question"),
        )
        for label, group, field in cases:
            changed = self.fresh_instance()
            changed[group][field] = True  # type: ignore[index]
            with self.subTest(case=label):
                with self.assertRaises(PolicyViolation):
                    parse_research_ledger(changed)
                with self.assertRaises(ValidationError):
                    self.validator.validate(changed)

    def test_entry_level_oracle_authority_and_confirmation_are_forbidden(self) -> None:
        for field in (
            "semantic_authority",
            "provider_output_is_oracle",
            "can_confirm_target_semantics",
        ):
            changed = self.fresh_instance()
            changed["entries"][0][field] = True  # type: ignore[index]
            with self.subTest(field=field):
                with self.assertRaises(PolicyViolation):
                    parse_research_ledger(changed)
                with self.assertRaises(ValidationError):
                    self.validator.validate(changed)

        changed_effect = self.fresh_instance()
        changed_effect["entries"][0]["epistemic_effect"] = "confirms_target_semantics"  # type: ignore[index]
        with self.assertRaises(PolicyViolation):
            parse_research_ledger(changed_effect)

        changed_review = self.fresh_instance()
        changed_review["entries"][0]["human_adjudication_status"] = "APPROVED"  # type: ignore[index]
        with self.assertRaises(RecordError):
            parse_research_ledger(changed_review)

    def test_provider_output_cannot_be_promoted_to_an_oracle(self) -> None:
        global_oracle = self.fresh_instance()
        global_oracle["provider_policy"]["provider_output_is_oracle"] = True  # type: ignore[index]
        with self.assertRaises(PolicyViolation):
            parse_research_ledger(global_oracle)
        with self.assertRaises(ValidationError):
            self.validator.validate(global_oracle)

        route_oracle = self.fresh_instance()
        route_oracle["entries"][0]["discovery"]["provider_output_is_oracle"] = True  # type: ignore[index]
        with self.assertRaises(PolicyViolation):
            parse_research_ledger(route_oracle)
        with self.assertRaises(ValidationError):
            self.validator.validate(route_oracle)

    def test_provider_policy_cannot_drift(self) -> None:
        cases = (
            ("consensus_role", "coequal_discovery_provider"),
            ("providers_replaceable", False),
            ("direct_primary_source_required", False),
        )
        for field, value in cases:
            changed = self.fresh_instance()
            changed["provider_policy"][field] = value  # type: ignore[index]
            with self.subTest(field=field):
                with self.assertRaises(PolicyViolation):
                    parse_research_ledger(changed)
                with self.assertRaises(ValidationError):
                    self.validator.validate(changed)

    def test_default_discovery_provider_is_actually_replaceable(self) -> None:
        changed = self.fresh_instance()
        changed["provider_policy"]["default_contemporary_discovery_provider"] = "ModernIndex"  # type: ignore[index]
        for entry in changed["entries"]:  # type: ignore[union-attr]
            if entry["discovery"]["route_kind"] == "default_contemporary_discovery":
                entry["discovery"]["provider"] = "ModernIndex"
                entry["discovery"]["route_locator"] = (
                    "https://modern-index.example/discovery/" + entry["entry_id"]
                )
        rehash_ledger_record(changed)
        ledger = parse_research_ledger(changed)
        self.assertEqual(
            ledger.provider_policy.default_contemporary_discovery_provider,
            "ModernIndex",
        )

    def test_default_contemporary_route_rejects_noncontemporary_source(self) -> None:
        changed = self.fresh_instance()
        old_entry = next(
            entry
            for entry in changed["entries"]  # type: ignore[union-attr]
            if entry["canonical_source"]["publication_year"] < 2024
        )
        old_entry["discovery"]["route_kind"] = "default_contemporary_discovery"
        old_entry["discovery"]["provider"] = "AlphaXiv"
        old_entry["discovery"]["route_locator"] = (
            "https://alphaxiv.org/abs/noncontemporary-test"
        )
        rehash_ledger_record(changed)
        with self.assertRaisesRegex(PolicyViolation, "contemporary source"):
            parse_research_ledger(changed)

    def test_source_report_kind_and_project_authorship_cannot_drift(self) -> None:
        cases = (
            (("epistemic_policy", "claim_kind"), "source_authority"),
            (("entries", 0, "claim_kind"), "source_authority"),
            (("entries", 0, "report_scope"), "project_adoption"),
            (("entries", 0, "report_author"), "AlphaXiv"),
        )
        for path, value in cases:
            changed = self.fresh_instance()
            target: object = changed
            for part in path[:-1]:
                target = target[part]  # type: ignore[index]
            target[path[-1]] = value  # type: ignore[index]
            with self.subTest(path=path):
                with self.assertRaises(PolicyViolation):
                    parse_research_ledger(changed)
                with self.assertRaises(ValidationError):
                    self.validator.validate(changed)

    def test_alphaxiv_locator_cannot_be_forged(self) -> None:
        changed = self.fresh_instance()
        alphaxiv = next(
            entry
            for entry in changed["entries"]  # type: ignore[union-attr]
            if entry["discovery"]["provider"] == "AlphaXiv"
        )
        alphaxiv["discovery"]["route_locator"] = "https://example.com/not-alphaxiv"
        rehash_ledger_record(changed)
        with self.assertRaises(PolicyViolation):
            parse_research_ledger(changed)
        with self.assertRaises(ValidationError):
            self.validator.validate(changed)

    def test_url_casing_matches_the_schema_contract(self) -> None:
        cases = (
            ("uppercase scheme", lambda value: value.replace("https://", "HTTPS://", 1)),
            (
                "uppercase AlphaXiv host",
                lambda value: value.replace("alphaxiv.org", "ALPHAXIV.ORG", 1),
            ),
        )
        for label, mutate in cases:
            changed = self.fresh_instance()
            alphaxiv = next(
                entry
                for entry in changed["entries"]  # type: ignore[union-attr]
                if entry["discovery"]["provider"] == "AlphaXiv"
            )
            locator = alphaxiv["discovery"]["route_locator"]
            alphaxiv["discovery"]["route_locator"] = mutate(locator)
            rehash_ledger_record(changed)
            with self.subTest(case=label):
                with self.assertRaises((RecordError, PolicyViolation)):
                    parse_research_ledger(changed)
                with self.assertRaises(ValidationError):
                    self.validator.validate(changed)

    def test_contemporary_marker_must_match_configured_boundary(self) -> None:
        changed = self.fresh_instance()
        contemporary = next(
            entry
            for entry in changed["entries"]  # type: ignore[union-attr]
            if entry["canonical_source"]["publication_year"] >= 2024
        )
        contemporary["discovery"]["contemporary"] = False
        rehash_ledger_record(changed)
        with self.assertRaises(PolicyViolation):
            parse_research_ledger(changed)

    def test_contemporary_primary_source_may_bypass_default_discovery(self) -> None:
        ledger = load_research_ledger(LEDGER_PATH)
        direct = [
            entry
            for entry in ledger.entries
            if entry.canonical_source.publication_year >= 2024
            and entry.discovery.route_kind is DiscoveryRouteKind.DIRECT_PRIMARY_SOURCE
        ]
        self.assertTrue(direct)

    def test_canonical_identifier_and_url_must_agree(self) -> None:
        changed = self.fresh_instance()
        changed["entries"][0]["canonical_source"]["canonical_url"] = (  # type: ignore[index]
            "https://doi.org/10.1007/not-the-record"
        )
        with self.assertRaisesRegex(RecordError, "identifier and canonical URL disagree"):
            parse_research_ledger(changed)

    def test_arxiv_identifier_and_publication_year_must_agree(self) -> None:
        changed = self.fresh_instance()
        arxiv_entry = next(
            entry
            for entry in changed["entries"]  # type: ignore[union-attr]
            if entry["canonical_source"]["source_kind"] == "arxiv"
        )
        arxiv_entry["canonical_source"]["publication_year"] += 1
        with self.assertRaisesRegex(RecordError, "publication year disagree"):
            parse_research_ledger(changed)

    def test_deterministic_serialization_round_trips(self) -> None:
        ledger = load_research_ledger(LEDGER_PATH)
        serialized = dumps_research_ledger(ledger)
        self.assertEqual(loads_research_ledger(serialized), ledger)
        self.assertEqual(dumps_research_ledger(loads_research_ledger(serialized)), serialized)
        self.assertEqual(
            hashlib.sha256(serialized.encode("utf-8")).hexdigest(),
            hashlib.sha256(dumps_research_ledger(ledger).encode("utf-8")).hexdigest(),
        )

    def test_optimized_python_cannot_disable_ledger_guards(self) -> None:
        program = (
            "from pathlib import Path; import hashlib; "
            "from creib.forge.research import load_research_ledger,dumps_research_ledger; "
            "p=Path(r'" + str(LEDGER_PATH) + "'); "
            "s=dumps_research_ledger(load_research_ledger(p)); "
            "print(hashlib.sha256(s.encode('utf-8')).hexdigest())"
        )
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(ROOT / "src")
        results = []
        for flags in ([], ["-O"]):
            result = subprocess.run(
                [sys.executable, *flags, "-c", program],
                cwd=ROOT,
                env=environment,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            results.append(result.stdout.strip())
        self.assertEqual(results[0], results[1])

    def test_serialized_ledger_contains_no_floating_point_values(self) -> None:
        serialized = dumps_research_ledger(load_research_ledger(LEDGER_PATH))
        decoded = json.loads(serialized)

        def walk(value: object) -> None:
            self.assertNotIsInstance(value, float)
            if isinstance(value, dict):
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)

        walk(decoded)


if __name__ == "__main__":
    unittest.main()
