from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from creib.errors import PolicyViolation, RecordError
from creib.forge.generic_inquiry import (
    AuthorityBinding,
    BindingKind,
    CaseBinding,
    ComponentBinding,
    InputObservation,
    ObservationDomain,
    ResearchLedgerBinding,
    build_generic_inquiry_plan,
)
from creib.forge.schema_validation import load_local_schema_catalog
from creib.forge.translation import compute_translation_record_id


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "forge" / "schema"

TRANSLATION_SCHEMA_NAMES = (
    "translation-source-document.schema.json",
    "translation-source-span.schema.json",
    "translation-charter.schema.json",
    "translation-obligation-graph.schema.json",
    "translation-interpretation-set.schema.json",
    "translation-neutral-signature.schema.json",
    "translation-neutral-model.schema.json",
    "translation-project-import.schema.json",
    "translation-two-way-bridge.schema.json",
    "translation-snapshot.schema.json",
)

CONTEXT_FREE_SCHEMA_NAMES = (
    *TRANSLATION_SCHEMA_NAMES,
    "translation-snapshot-delta.schema.json",
    "adaptive-inquiry-v3.schema.json",
    "hardening-comparison.schema.json",
)

CONTEXT_REQUIRED_SCHEMA_NAMES = (
    "inquiry-input-v1.schema.json",
    "translation-review-v1.schema.json",
    "translation-test-synthesis.schema.json",
    "hardening-evidence.schema.json",
    "hardening-decision.schema.json",
    "hardening-resolution.schema.json",
)


def _source_document() -> dict[str, object]:
    record: dict[str, object] = {
        "schema_version": "creib.semantic-forge.translation-source-document.v1",
        "document_id": "TDOC:" + "0" * 64,
        "supersedes_document_id": None,
        "document_key": "TEST-SOURCE-1",
        "title": "Exact test source",
        "artifact": {
            "supplied_filename": "source.txt",
            "media_type": "text/plain",
            "sha256": "a" * 64,
            "byte_length": 12,
        },
        "structure": {
            "kind": "UTF8_TEXT",
            "page_count": None,
            "encoding": "UTF-8",
        },
        "legacy_refs": [],
        "provenance": {
            "producer_kind": "HUMAN",
            "producer_id": "runtime-dispatch-test",
            "created_at": "2026-09-03T00:00:00Z",
            "generation_record_ids": [],
        },
    }
    record["document_id"] = compute_translation_record_id(record)
    return record


def _generic_plan() -> dict[str, object]:
    observation = InputObservation(
        observation_domain=ObservationDomain.SEMANTIC_MODEL,
        adapter_id="TEST-ADAPTER-1",
        adapter_contract_sha256="a" * 64,
        source_record_id="SOURCE-RECORD-1",
        source_schema_version="example.source.v1",
        source_record_id_pointer="/record_id",
        source_file_sha256="b" * 64,
        source_contract_sha256="c" * 64,
        selected_value_pointer="/observation",
        selected_value_digest_domain="example.observation.v1",
        selected_value_sha256="sha256:" + "d" * 64,
    )
    case = CaseBinding(
        authority_bindings=(
            AuthorityBinding("SEMANTIC_AUTHORITY", "SOURCE-1", "e" * 64),
        ),
        component_bindings=(
            ComponentBinding(
                "MODEL",
                "MODEL-1",
                BindingKind.CANONICAL_RECORD,
                "f" * 64,
            ),
        ),
        observation=observation,
        research_basis=None,
        research_ledger=ResearchLedgerBinding(
            ledger_id="LEDGER-1",
            created_on="2026-09-03",
            as_of_date="2026-09-03",
            file_sha256="1" * 64,
            record_sha256="sha256:" + "2" * 64,
        ),
    )
    return build_generic_inquiry_plan(case)


class NewSchemaRuntimeDispatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = load_local_schema_catalog(SCHEMA_DIR)

    def test_every_context_free_new_record_has_runtime_dispatch(self) -> None:
        for schema_name in CONTEXT_FREE_SCHEMA_NAMES:
            with self.subTest(schema=schema_name):
                self.assertTrue(
                    self.catalog.has_full_record_runtime_contract(schema_name)
                )

    def test_context_dependent_new_records_remain_explicitly_schema_only(self) -> None:
        for schema_name in CONTEXT_REQUIRED_SCHEMA_NAMES:
            with self.subTest(schema=schema_name):
                self.assertFalse(
                    self.catalog.has_full_record_runtime_contract(schema_name)
                )

    def test_translation_content_tamper_is_not_schema_only_success(self) -> None:
        record = _source_document()
        self.catalog.validate(record, "translation-source-document.schema.json")
        changed = copy.deepcopy(record)
        changed["title"] = "Changed without changing the content ID"
        with self.assertRaisesRegex(RecordError, "canonical record content"):
            self.catalog.validate(
                changed,
                "translation-source-document.schema.json",
            )

    def test_generic_plan_route_tamper_reaches_deterministic_runtime_check(self) -> None:
        plan = _generic_plan()
        self.catalog.validate(plan, "adaptive-inquiry-v3.schema.json")
        changed = copy.deepcopy(plan)
        changed["route"] = "AUTHORITY_REVIEW"
        with self.assertRaises(PolicyViolation):
            self.catalog.validate(changed, "adaptive-inquiry-v3.schema.json")

    def test_canonical_filename_with_custom_identity_does_not_trigger_runtime(self) -> None:
        custom_schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "https://example.test/not-the-canonical-runtime-contract.json",
            "type": "object",
        }
        with tempfile.TemporaryDirectory() as directory:
            schema_dir = Path(directory)
            schema_name = "translation-source-document.schema.json"
            (schema_dir / schema_name).write_text(
                json.dumps(custom_schema, sort_keys=True, separators=(",", ":"))
                + "\n",
                encoding="utf-8",
            )
            catalog = load_local_schema_catalog(schema_dir)
            self.assertFalse(catalog.has_full_record_runtime_contract(schema_name))
            catalog.validate({}, schema_name)


if __name__ == "__main__":
    unittest.main()
