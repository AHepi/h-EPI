from __future__ import annotations

import copy
import errno
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from creib.canonical import bytes_digest, canonical_bytes, domain_digest
from creib.errors import PolicyViolation, RecordError
from creib.forge.inquiry import (
    EVENT_SCHEMA,
    LEGACY_EVENT_SCHEMA,
    InquiryError,
    InquiryRoute,
    QuestionState,
    build_adaptive_inquiry_plan,
    build_inquiry_event,
    compute_adaptive_inquiry_plan_id,
    compute_assessment_disposition_id,
    compute_evidence_binding_id,
    compute_event_id,
    compute_human_triage_id,
    compute_locus_assessment_id,
    compute_next_action_id,
    compute_question_id,
    dumps_adaptive_inquiry_plan,
    inquiry_question_digest,
    load_research_ledger_binding,
    loads_adaptive_inquiry_plan,
    publish_human_triage_against_inputs,
    publish_inquiry_event,
    validate_adaptive_inquiry_plan,
    validate_adaptive_inquiry_plan_against_inputs,
    validate_human_triage,
    validate_inquiry_event,
    validate_inquiry_question_against_plan,
    verify_human_triage_chain,
    verify_inquiry_chain,
    verify_issue_warrant_binding,
)
from creib.forge.models import parse_issue, parse_research_warrant
from creib.forge.research import parse_research_ledger
from creib.strict_json import load_strict


ROOT = Path(__file__).resolve().parents[1]
RUN_PATH = (
    ROOT
    / "forge"
    / "runs"
    / "SMF-CALIBRATION-CR-1-0-001.4219efce.json"
)
LEDGER_PATH = ROOT / "forge" / "research" / "SMF-RESEARCH-2026-09-03.json"
SCHEMA_PATH = ROOT / "forge" / "schema" / "adaptive-inquiry-v2.schema.json"
EVENT_SCHEMA_PATH = ROOT / "forge" / "schema" / "inquiry-event-v2.schema.json"
LEGACY_SCHEMA_PATH = ROOT / "forge" / "schema" / "adaptive-inquiry.schema.json"
LEGACY_EVENT_SCHEMA_PATH = ROOT / "forge" / "schema" / "inquiry-event.schema.json"


def rehash_research_ledger_after_entry_change(record: dict[str, object]) -> None:
    entries = record.get("entries")
    if type(entries) is not list:
        raise TypeError("test ledger entries must be a list")
    entry_hashes: dict[object, object] = {}
    for entry in entries:
        if type(entry) is not dict:
            raise TypeError("test ledger entry must be an object")
        unsigned = {key: value for key, value in entry.items() if key != "entry_sha256"}
        entry["entry_sha256"] = domain_digest(
            "creib.semantic-forge.external-source-entry.v2",
            unsigned,
        ).removeprefix("sha256:")
        entry_hashes[entry["entry_id"]] = entry["entry_sha256"]

    proposals = record.get("project_use_proposals")
    if type(proposals) is not list:
        raise TypeError("test ledger proposals must be a list")
    for proposal in proposals:
        if type(proposal) is not dict:
            raise TypeError("test ledger proposal must be an object")
        proposal["source_entry_sha256"] = entry_hashes[proposal["source_entry_id"]]
        unsigned = {
            key: value
            for key, value in proposal.items()
            if key != "proposal_sha256"
        }
        proposal["proposal_sha256"] = domain_digest(
            "creib.semantic-forge.project-use-proposal.v1",
            unsigned,
        ).removeprefix("sha256:")

    unsigned_ledger = {
        key: value for key, value in record.items() if key != "ledger_sha256"
    }
    record["ledger_sha256"] = domain_digest(
        "creib.semantic-forge.external-research-ledger.v2",
        unsigned_ledger,
    ).removeprefix("sha256:")


class SemanticForgeAdaptiveInquiryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = load_strict(RUN_PATH)
        cls.run_raw = RUN_PATH.read_bytes()
        cls.ledger, cls.ledger_binding = load_research_ledger_binding(LEDGER_PATH)

    def setUp(self) -> None:
        self._temporary_root = tempfile.TemporaryDirectory()
        self._test_root = Path(self._temporary_root.name)
        self._triage_counter = 0
        self._plan_context_by_case: dict[str, tuple[Path, str | None]] = {}
        self._latest_attack_targets: tuple[dict[str, object], ...] = ()

    def tearDown(self) -> None:
        self._temporary_root.cleanup()

    def new_triage_dir(self) -> Path:
        self._triage_counter += 1
        directory = self._test_root / f"triage-{self._triage_counter:03d}"
        directory.mkdir()
        return directory

    def no_triage_plan(self, triage_dir: Path | None = None) -> dict[str, object]:
        directory = triage_dir if triage_dir is not None else self.new_triage_dir()
        plan = build_adaptive_inquiry_plan(
            repo_root=ROOT,
            run_record_path=RUN_PATH,
            research_ledger_path=LEDGER_PATH,
            triage_dir=directory,
        )
        self._latest_attack_targets = tuple(plan["available_attack_targets"])  # type: ignore[arg-type]
        return plan

    def build_plan(
        self,
        *,
        triage: dict[str, object] | None = None,
        triage_dir: Path | None = None,
        head_triage_id: str | None = None,
        events_dir: Path | None = None,
        head: str | None = None,
    ) -> dict[str, object]:
        directory = triage_dir if triage_dir is not None else self.new_triage_dir()
        if triage is not None:
            if head_triage_id is None:
                head_triage_id = str(triage["triage_id"])
            output_path = directory / f"{str(triage['triage_id']).replace(':', '-')}.json"
            if not output_path.exists():
                if not self._latest_attack_targets:
                    self.no_triage_plan()
                publish_human_triage_against_inputs(
                    directory,
                    triage,
                    expected_head_triage_id=triage.get("previous_triage_id"),  # type: ignore[arg-type]
                    repo_root=ROOT,
                    run_record_path=RUN_PATH,
                    research_ledger_path=LEDGER_PATH,
                )
        plan = build_adaptive_inquiry_plan(
            repo_root=ROOT,
            run_record_path=RUN_PATH,
            research_ledger_path=LEDGER_PATH,
            triage_dir=directory,
            head_triage_id=head_triage_id,
            triage=triage,
            events_dir=events_dir,
            head_event_id=head,
        )
        self._latest_attack_targets = tuple(plan["available_attack_targets"])  # type: ignore[arg-type]
        self._plan_context_by_case[str(plan["case_sha256"])] = (
            directory,
            head_triage_id,
        )
        return plan

    def locus_assessment(
        self,
        *,
        loci: tuple[str, ...] = ("CANDIDATE",),
        location: str = "EXTERNAL_CRITICAL_INSTRUMENT",
        mechanism: str = "The candidate admits a rival realization of the tested role.",
        relevance: str = "Resolving this criticism can change the next bounded work item.",
        discriminator: str = "Construct a same-reduct rival or defeat that construction.",
        scope: str = "The finite typed-role projection and its declared contracts only.",
        dependencies: tuple[str, ...] = (),
    ) -> dict[str, object]:
        assessment: dict[str, object] = {
            "assessment_id": "LA:" + "0" * 64,
            "status": "LIVE",
            "loci": sorted(loci),
            "mechanism": mechanism,
            "relevance": relevance,
            "discriminator": discriminator,
            "uncertainty_location": location,
            "scope": scope,
            "depends_on_assessment_ids": sorted(dependencies),
            "epistemic_effect": "CRITICISM_ONLY",
            "can_establish_unique_cause": False,
        }
        assessment["assessment_id"] = compute_locus_assessment_id(assessment)
        return assessment

    def next_action(
        self,
        bindings: dict[str, object],
        assessments: list[dict[str, object]],
        *,
        selected_assessment_ids: tuple[str, ...] | None = None,
        route_intent: str = "EXTERNAL_RESEARCH_REQUIRED",
        action: str = "Seek the exact bounded discriminator for the selected criticism.",
        selection_basis: str | None = None,
        attack_target_ids: tuple[str, ...] | None = None,
    ) -> dict[str, object]:
        selected = sorted(
            selected_assessment_ids
            if selected_assessment_ids is not None
            else (str(assessments[0]["assessment_id"]),)
        )
        if selection_basis is None:
            selection_basis = (
                "SHARED_ACTION_FOR_MULTIPLE_LOCI"
                if len(selected) > 1
                else "INDEPENDENT_HUMAN_PRIORITY"
            )
        research_target: dict[str, object] | None = None
        if route_intent == "EXTERNAL_RESEARCH_REQUIRED":
            if attack_target_ids is None:
                if not self._latest_attack_targets:
                    self.no_triage_plan()
                attack_target_ids = tuple(
                    str(item["attack_target_id"])
                    for item in self._latest_attack_targets
                )
            research_target = {
                "issue_id": bindings["issue_id"],
                "issue_sha256": bindings["issue_sha256"],
                "warrant_id": bindings["warrant_id"],
                "warrant_sha256": bindings["warrant_sha256"],
                "attack_target_ids": sorted(attack_target_ids),
            }
        record: dict[str, object] = {
            "action_id": "NA:" + "0" * 64,
            "selected_assessment_ids": selected,
            "route_intent": route_intent,
            "action": action,
            "selection_basis": selection_basis,
            "reason": "This is a human scheduling choice, not a ranking of truth.",
            "research_target": research_target,
            "epistemic_effect": "SCHEDULING_ONLY",
            "can_rank_semantic_truth": False,
        }
        record["action_id"] = compute_next_action_id(record)
        return record

    def disposition_evidence(
        self,
        snapshot: dict[str, object],
        *,
        evidence_kind: str = "TYPED_EVIDENCE_RECORD",
        record_id_pointer: str = "/record_id",
        selected_value_pointer: str = "",
        bearing: str = "This exact record bears on the declared discriminator.",
    ) -> dict[str, object]:
        selected: object = snapshot
        if selected_value_pointer:
            for token in selected_value_pointer[1:].split("/"):
                selected = selected[token]  # type: ignore[index]
        record: dict[str, object] = {
            "evidence_binding_id": "EB:" + "0" * 64,
            "evidence_kind": evidence_kind,
            "record_id": snapshot[record_id_pointer.removeprefix("/")],
            "record_id_pointer": record_id_pointer,
            "record_snapshot": copy.deepcopy(snapshot),
            "record_sha256": domain_digest(
                "creib.semantic-forge.disposition-evidence-record.v1",
                snapshot,
            ),
            "selected_value_pointer": selected_value_pointer,
            "selected_value_sha256": domain_digest(
                "creib.semantic-forge.disposition-evidence-selection.v1",
                selected,
            ),
            "bearing": bearing,
        }
        record["evidence_binding_id"] = compute_evidence_binding_id(record)
        return record

    def calibration_disposition_evidence(self) -> dict[str, object]:
        return self.disposition_evidence(
            copy.deepcopy(self.report),
            evidence_kind="CALIBRATION_RUN",
            record_id_pointer="/run_id",
            selected_value_pointer=(
                "/fixture_evaluations/weak_typed_role_projection"
            ),
            bearing=(
                "This exact bound calibration observation bears on the declared "
                "discriminator without confirming the model."
            ),
        )

    def assessment_disposition(
        self,
        assessment: dict[str, object],
        *,
        assessment_origin_triage_id: str,
        bindings: dict[str, object],
        disposition: str,
        evidence_bindings: list[dict[str, object]],
        created_on: str = "2026-09-03",
        decision_sequence: int = 1,
        previous_disposition_id: str | None = None,
        superseded_bindings: dict[str, object] | None = None,
        changed_binding_pointers: tuple[str, ...] = (),
    ) -> dict[str, object]:
        record: dict[str, object] = {
            "schema_version": "creib.semantic-forge.assessment-disposition.v1",
            "record_type": "assessment_disposition",
            "disposition_id": "AD:" + "0" * 64,
            "assessment_id": assessment["assessment_id"],
            "assessment_origin_triage_id": assessment_origin_triage_id,
            "decision_sequence": decision_sequence,
            "previous_disposition_id": previous_disposition_id,
            "created_on": created_on,
            "bindings": copy.deepcopy(bindings),
            "disposition": disposition,
            "declared_discriminator": assessment["discriminator"],
            "evidence_bindings": sorted(
                copy.deepcopy(evidence_bindings),
                key=lambda item: str(item["evidence_binding_id"]),
            ),
            "reason": "A fallible human disposition of this exact criticism only.",
            "superseded_bindings": copy.deepcopy(superseded_bindings),
            "changed_binding_pointers": sorted(changed_binding_pointers),
            "reviewer_kind": "HUMAN",
            "machine_generated": False,
            "epistemic_effect": "ASSESSMENT_WORKFLOW_ONLY",
            "can_establish_unique_cause": False,
            "can_promote_model": False,
            "can_confirm_target_semantics": False,
            "not_found_can_dispose": False,
            "source_count_can_decide": False,
            "provider_agreement_can_decide": False,
            "semantic_verdict": None,
        }
        record["disposition_id"] = compute_assessment_disposition_id(record)
        return record

    def human_triage(
        self,
        bindings: dict[str, object],
        *,
        assessments: list[dict[str, object]] | None = None,
        assessment_dispositions: list[dict[str, object]] | None = None,
        include_action: bool = True,
        selected_assessment_ids: tuple[str, ...] | None = None,
        route_intent: str = "EXTERNAL_RESEARCH_REQUIRED",
        action: str = "Seek the exact bounded discriminator for the selected criticism.",
        selection_basis: str | None = None,
        attack_target_ids: tuple[str, ...] | None = None,
        created_on: str = "2026-09-03",
        sequence: int = 1,
        previous_triage_id: str | None = None,
        transition_kind: str = "GENESIS",
        transition_reason: str = (
            "Start one fallible, additive human criticism lineage."
        ),
    ) -> dict[str, object]:
        if assessments is None:
            assessments = [self.locus_assessment()]
        ordered_assessments = sorted(
            copy.deepcopy(assessments),
            key=lambda item: str(item["assessment_id"]),
        )
        ordered_dispositions = sorted(
            copy.deepcopy(assessment_dispositions or []),
            key=lambda item: str(item["disposition_id"]),
        )
        action = (
            self.next_action(
                bindings,
                ordered_assessments,
                selected_assessment_ids=selected_assessment_ids,
                route_intent=route_intent,
                action=action,
                selection_basis=selection_basis,
                attack_target_ids=attack_target_ids,
            )
            if include_action
            else None
        )
        record: dict[str, object] = {
            "$schema": "../schema/adaptive-inquiry-v2.schema.json",
            "schema_version": "creib.semantic-forge.human-failure-triage.v2",
            "record_type": "human_failure_triage",
            "triage_id": "HT:" + "0" * 64,
            "sequence": sequence,
            "previous_triage_id": previous_triage_id,
            "transition_kind": transition_kind,
            "transition_reason": transition_reason,
            "created_on": created_on,
            "bindings": copy.deepcopy(bindings),
            "overall_status": "UNRESOLVED",
            "locus_assessments": ordered_assessments,
            "assessment_dispositions": ordered_dispositions,
            "next_action": action,
            "reviewer_kind": "HUMAN",
            "machine_generated": False,
            "epistemic_effect": "WORKFLOW_ROUTING_ONLY",
            "can_promote_model": False,
            "semantic_verdict": None,
        }
        record["triage_id"] = compute_human_triage_id(record)
        return record

    def external_plan(self) -> dict[str, object]:
        blocked = self.build_plan()
        return self.build_plan(triage=self.human_triage(blocked["bindings"]))  # type: ignore[arg-type]

    def write_unchecked_triage_lineage(
        self,
        directory: Path,
        triages: list[dict[str, object]],
    ) -> None:
        """Write adversarial replay fixtures without using the guarded publisher."""

        for triage in triages:
            payload = canonical_bytes(triage) + b"\n"
            triage_id = str(triage["triage_id"])
            (directory / f"{triage_id.replace(':', '-')}.json").write_bytes(payload)
            previous = triage["previous_triage_id"]
            parent = "GENESIS" if previous is None else str(previous).removeprefix("HT:")
            (directory / f"NEXT-{parent}.claim").write_bytes(payload)

    def standalone_source_report(
        self,
        question: dict[str, object],
        *,
        seed_index: int = 0,
        suffix: str = "001",
    ) -> dict[str, object]:
        entry = copy.deepcopy(self.ledger.entries[seed_index].to_dict())
        entry["entry_id"] = f"SMF-RES-INQUIRY-{suffix}"
        entry["attacked_harness_question"] = question["query"]
        entry["falsifier"] = question["falsifier_condition"]
        unsigned = copy.deepcopy(entry)
        unsigned.pop("entry_sha256")
        entry["entry_sha256"] = domain_digest(
            "creib.semantic-forge.external-source-entry.v2",
            unsigned,
        ).removeprefix("sha256:")
        return entry

    def question_binding(
        self,
        question: dict[str, object],
    ) -> dict[str, object]:
        return {
            "question_id": question["question_id"],
            "case_sha256": question["case_sha256"],
            "triage_id": question["triage_id"],
            "action_id": question["action_id"],
            "attack_target_id": question["attack_target_id"],
        }

    def standalone_entry(
        self,
        question: dict[str, object],
        *,
        seed_index: int = 0,
        suffix: str = "001",
    ) -> dict[str, object]:
        return {
            "schema_version": "creib.semantic-forge.event-research-entry.v2",
            "question_binding": self.question_binding(question),
            "source_report": self.standalone_source_report(
                question,
                seed_index=seed_index,
                suffix=suffix,
            ),
        }

    def append(
        self,
        directory: Path,
        question: dict[str, object],
        *,
        head: str | None,
        event_type: str,
        actor: str,
        occurred_on: str = "2026-09-03",
        research_entry: dict[str, object] | None = None,
    ) -> dict[str, object]:
        triage_dir, head_triage_id = self._plan_context_by_case[
            str(question["case_sha256"])
        ]
        plan = self.build_plan(
            triage_dir=triage_dir,
            head_triage_id=head_triage_id,
            events_dir=directory,
            head=head,
        )
        state = verify_inquiry_chain(
            directory,
            head,
            research_ledger=self.ledger,
            research_binding=self.ledger_binding,
        )
        current = state.question_states.get(question["question_id"])
        event = build_inquiry_event(
            sequence=len(state.events) + 1,
            previous_event_id=head,
            event_type=event_type,
            occurred_on=occurred_on,
            actor_kind=actor,
            question=question,
            from_state=None if current is None else current.value,
            reason_code=event_type,
            reason=f"Test transition {event_type}; no semantic promotion.",
            research_ledger=self.ledger,
            research_ledger_binding=self.ledger_binding,
            research_entry=research_entry,
        )
        publish_inquiry_event(
            directory,
            event,
            expected_head_event_id=head,
            plan=plan,
            repo_root=ROOT,
            run_record_path=RUN_PATH,
            research_ledger_path=LEDGER_PATH,
            triage_dir=triage_dir,
            research_ledger=self.ledger,
            research_binding=self.ledger_binding,
        )
        return event

    def legacy_question_and_event(
        self,
        current_question: dict[str, object],
        *,
        sequence: int = 1,
        previous_event_id: str | None = None,
    ) -> tuple[dict[str, object], dict[str, object]]:
        """Build an intrinsically valid immutable-v1 replay fixture."""

        legacy_question = {
            key: copy.deepcopy(value)
            for key, value in current_question.items()
            if key
            not in {
                "triage_id",
                "action_id",
                "selected_assessment_ids",
                "selected_locus_assessments",
                "selected_action",
                "selection_reason",
                "attack_target",
            }
        }
        legacy_question["schema_version"] = (
            "creib.semantic-forge.critical-question.v1"
        )
        legacy_question["question_id"] = compute_question_id(legacy_question)
        legacy_event: dict[str, object] = {
            "$schema": "../schema/inquiry-event.schema.json",
            "schema_version": LEGACY_EVENT_SCHEMA,
            "event_id": "IE:" + "0" * 64,
            "ledger_id": "SMF-INQUIRY-CR-1-0",
            "sequence": sequence,
            "previous_event_id": previous_event_id,
            "event_type": "QUESTION_PROPOSED",
            "occurred_on": "2026-09-03",
            "actor_kind": "MACHINE",
            "question": legacy_question,
            "from_state": None,
            "to_state": "PROPOSED",
            "reason_code": "HISTORICAL_V1",
            "reason": "Historical v1 event retained only for replay.",
            "research_ledger": copy.deepcopy(self.ledger_binding),
            "research_entry": None,
            "research_entry_sha256": None,
            "semantic_verdict": None,
            "epistemic_effect": "MAY_CRITICIZE_OR_ROUTE_WORK_ONLY",
        }
        legacy_event["event_id"] = compute_event_id(legacy_event)
        return legacy_question, legacy_event

    def write_unchecked_event_lineage(
        self,
        directory: Path,
        events: list[dict[str, object]],
    ) -> None:
        """Write adversarial event fixtures without the guarded publisher."""

        for event in events:
            payload = canonical_bytes(event) + b"\n"
            event_id = str(event["event_id"])
            (directory / f"{event_id.replace(':', '-')}.json").write_bytes(payload)
            previous = event["previous_event_id"]
            parent = "GENESIS" if previous is None else str(previous).removeprefix("IE:")
            (directory / f"NEXT-{parent}.claim").write_bytes(payload)

    def test_new_schemas_are_strict_and_registered_offline(self) -> None:
        adaptive = load_strict(SCHEMA_PATH)
        event = load_strict(EVENT_SCHEMA_PATH)
        legacy_adaptive = load_strict(LEGACY_SCHEMA_PATH)
        legacy_event = load_strict(LEGACY_EVENT_SCHEMA_PATH)
        for schema in (adaptive, event, legacy_adaptive, legacy_event):
            self.assertEqual(
                schema["$schema"],
                "https://json-schema.org/draft/2020-12/schema",
            )
        self.assertFalse(event["additionalProperties"])
        self.assertFalse(legacy_event["additionalProperties"])
        for schema in (adaptive, legacy_adaptive):
            for definition in (
                "human_failure_triage",
                "critical_question",
                "inquiry_plan",
            ):
                self.assertFalse(schema["$defs"][definition]["additionalProperties"])
        result = subprocess.run(
            [sys.executable, "tools/validate_semantic_forge.py"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("adaptive-inquiry-v2.schema.json", result.stdout)
        self.assertIn("adaptive-inquiry.schema.json", result.stdout)
        self.assertIn("inquiry-event-v2.schema.json", result.stdout)
        self.assertIn("inquiry-event.schema.json", result.stdout)

    def test_plan_cli_rejects_schema_invalid_research_url_casing(self) -> None:
        source = load_strict(LEDGER_PATH)
        if type(source) is not dict:
            self.fail("research ledger fixture must be an object")
        cases = (
            ("uppercase-scheme", "HTTPS://alphaxiv.org/"),
            ("uppercase-host", "https://ALPHAXIV.ORG/"),
        )
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for label, prefix in cases:
                changed = copy.deepcopy(source)
                alphaxiv = next(
                    entry
                    for entry in changed["entries"]
                    if entry["discovery"]["provider"] == "AlphaXiv"
                )
                locator = alphaxiv["discovery"]["route_locator"]
                suffix = locator.split("/", 3)[3]
                alphaxiv["discovery"]["route_locator"] = prefix + suffix
                rehash_research_ledger_after_entry_change(changed)
                ledger_path = directory / f"{label}.json"
                ledger_path.write_text(
                    json.dumps(
                        changed,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                    + "\n",
                    encoding="utf-8",
                )
                result = subprocess.run(
                    [
                        sys.executable,
                        "tools/run_semantic_inquiry.py",
                        "plan",
                        "--run-record",
                        str(RUN_PATH),
                        "--research-ledger",
                        str(ledger_path),
                    ],
                    cwd=ROOT,
                    check=False,
                    capture_output=True,
                    text=True,
                )
                with self.subTest(case=label):
                    self.assertNotEqual(result.returncode, 0)
                    output = json.loads(result.stdout)
                    self.assertEqual(
                        output["error_code"],
                        "INQUIRY_RESEARCH_LEDGER_INVALID",
                    )
                    self.assertIsNone(output["semantic_verdict"])

    def test_current_run_without_human_triage_fails_closed(self) -> None:
        plan = self.build_plan()
        self.assertEqual(plan["route"], InquiryRoute.AWAITING_HUMAN_TRIAGE.value)
        self.assertEqual(plan["proposed_questions"], [])
        self.assertIsNone(plan["semantic_verdict"])
        self.assertEqual(plan["epistemic_status"], "UNRESOLVED")
        self.assertIsNone(plan["triage"])
        self.assertIsNone(plan["state_head_triage_id"])
        self.assertGreater(len(plan["available_attack_targets"]), 0)
        self.assertEqual(plan["live_locus_assessment_ids"], [])
        self.assertIsNone(plan["selected_action_id"])

    def test_plan_binds_exact_model_failure_issue_warrant_and_ledger(self) -> None:
        plan = self.build_plan()
        bindings = plan["bindings"]
        for field in (
            "run_record_file_sha256",
            "run_contract_sha256",
            "authority_sha256",
            "candidate_contract_sha256",
            "challenge_contract_sha256",
            "fixture_contract_sha256",
            "evaluator_contract_sha256",
            "observation_sha256",
            "issue_sha256",
            "warrant_sha256",
            "research_ledger",
        ):
            with self.subTest(field=field):
                self.assertIn(field, bindings)
        self.assertEqual(
            bindings["observation_kind"],
            "CRITICISM_CANDIDATE_NOT_SEMANTIC_VERDICT",
        )
        self.assertEqual(
            bindings["research_ledger"]["as_of_date"],
            self.ledger.as_of_date,
        )
        self.assertEqual(
            bindings["research_ledger"]["created_on"],
            self.ledger.created_on,
        )

    def test_issue_to_warrant_binding_is_complete_not_id_only(self) -> None:
        issue = parse_issue(self.report["corpus_trace"]["selected_external_issue"])
        warrant_record = copy.deepcopy(
            self.report["research_routing"]["external_role_warrant"]
        )
        warrant = parse_research_warrant(warrant_record)
        verify_issue_warrant_binding(issue, warrant)

        warrant_record["question"] += " Altered while retaining the same identifiers."
        altered = parse_research_warrant(warrant_record)
        with self.assertRaisesRegex(PolicyViolation, "exact deterministic projection"):
            verify_issue_warrant_binding(issue, altered)

    def test_human_triage_is_content_addressed_and_exactly_bound(self) -> None:
        blocked = self.build_plan()
        triage = self.human_triage(blocked["bindings"])
        validate_human_triage(triage, expected_bindings=blocked["bindings"])

        assessment = triage["locus_assessments"][0]
        action = triage["next_action"]
        self.assertEqual(
            assessment["assessment_id"],
            compute_locus_assessment_id(assessment),
        )
        self.assertEqual(action["action_id"], compute_next_action_id(action))

        changed = copy.deepcopy(triage)
        changed["bindings"]["candidate_id"] = "SAME-ID-LAUNDERING-ATTEMPT"
        changed["triage_id"] = compute_human_triage_id(changed)
        with self.assertRaisesRegex(PolicyViolation, "exact current inquiry inputs"):
            validate_human_triage(changed, expected_bindings=blocked["bindings"])

        mutations = (
            ("assessment mechanism", ("locus_assessments", 0, "mechanism")),
            ("assessment discriminator", ("locus_assessments", 0, "discriminator")),
            ("selected action", ("next_action", "reason")),
        )
        for label, path in mutations:
            stale_id = copy.deepcopy(triage)
            target: object = stale_id
            for component in path[:-1]:
                target = target[component]  # type: ignore[index]
            target[path[-1]] += " changed"  # type: ignore[index,operator]
            with self.subTest(mutation=label), self.assertRaisesRegex(
                RecordError,
                "content-addressed ID mismatch",
            ):
                validate_human_triage(
                    stale_id,
                    expected_bindings=blocked["bindings"],
                )

        stale_assessment = copy.deepcopy(triage)
        stale_assessment["locus_assessments"][0]["mechanism"] += " changed"
        stale_assessment["triage_id"] = compute_human_triage_id(stale_assessment)
        with self.assertRaisesRegex(
            RecordError,
            "locus assessment content-addressed ID mismatch",
        ):
            validate_human_triage(
                stale_assessment,
                expected_bindings=blocked["bindings"],
            )

        stale_action = copy.deepcopy(triage)
        stale_action["next_action"]["reason"] += " changed"
        stale_action["triage_id"] = compute_human_triage_id(stale_action)
        with self.assertRaisesRegex(
            RecordError,
            "next action content-addressed ID mismatch",
        ):
            validate_human_triage(
                stale_action,
                expected_bindings=blocked["bindings"],
            )

    def test_human_triage_cannot_predate_bound_research_snapshot(self) -> None:
        blocked = self.build_plan()
        backdated = self.human_triage(
            blocked["bindings"],  # type: ignore[arg-type]
            created_on="2026-09-02",
        )
        with self.assertRaisesRegex(
            PolicyViolation,
            "precedes the bound research ledger artifact",
        ):
            validate_human_triage(
                backdated,
                expected_bindings=blocked["bindings"],  # type: ignore[arg-type]
            )
        with self.assertRaisesRegex(
            PolicyViolation,
            "precedes the bound research ledger artifact",
        ):
            self.build_plan(triage=backdated)

        intrinsically_rehashed = self.external_plan()
        intrinsically_rehashed["triage"]["created_on"] = "2026-09-02"
        intrinsically_rehashed["triage"]["triage_id"] = compute_human_triage_id(
            intrinsically_rehashed["triage"]
        )
        intrinsically_rehashed["plan_id"] = compute_adaptive_inquiry_plan_id(
            intrinsically_rehashed
        )
        with self.assertRaisesRegex(
            PolicyViolation,
            "precedes the bound research ledger artifact",
        ):
            validate_adaptive_inquiry_plan(intrinsically_rehashed)

        impossible_bindings = copy.deepcopy(blocked["bindings"])
        impossible_bindings["research_ledger"]["as_of_date"] = "2026-09-04"
        impossible = self.human_triage(
            impossible_bindings,
            created_on="2026-09-04",
        )
        with self.assertRaisesRegex(
            RecordError,
            "as_of_date cannot be after .*created_on",
        ):
            validate_human_triage(
                impossible,
                expected_bindings=impossible_bindings,
            )

    def test_external_triage_generates_exact_content_addressed_attacks(self) -> None:
        plan = self.external_plan()
        self.assertEqual(plan["route"], InquiryRoute.EXTERNAL_RESEARCH_REQUIRED.value)
        action = plan["triage"]["next_action"]
        self.assertEqual(plan["selected_action_id"], action["action_id"])
        self.assertEqual(
            action["research_target"],
            {
                "issue_id": plan["bindings"]["issue_id"],
                "issue_sha256": plan["bindings"]["issue_sha256"],
                "warrant_id": plan["bindings"]["warrant_id"],
                "warrant_sha256": plan["bindings"]["warrant_sha256"],
                "attack_target_ids": [
                    target["attack_target_id"]
                    for target in plan["available_attack_targets"]
                ],
            },
        )
        questions = plan["proposed_questions"]
        self.assertEqual(len(questions), 4)
        self.assertEqual(len({item["question_id"] for item in questions}), 4)
        self.assertEqual(len({item["attack_target_id"] for item in questions}), 4)
        for question in questions:
            with self.subTest(question=question["question_id"]):
                self.assertEqual(question["question_id"], compute_question_id(question))
                self.assertEqual(
                    question["triage_created_on"],
                    plan["triage"]["created_on"],
                )
                self.assertEqual(question["triage_id"], plan["triage"]["triage_id"])
                self.assertEqual(question["action_id"], action["action_id"])
                self.assertEqual(
                    question["selected_assessment_ids"],
                    action["selected_assessment_ids"],
                )
                selected = {
                    item["assessment_id"]: item
                    for item in plan["triage"]["locus_assessments"]
                }
                self.assertEqual(
                    question["selected_locus_assessments"],
                    [
                        selected[assessment_id]
                        for assessment_id in action["selected_assessment_ids"]
                    ],
                )
                self.assertEqual(question["selected_action"], action["action"])
                self.assertEqual(question["selection_reason"], action["reason"])
                target = next(
                    item
                    for item in plan["available_attack_targets"]
                    if item["attack_target_id"] == question["attack_target_id"]
                )
                self.assertEqual(question["attack_target"], target)
                self.assertEqual(question["rival_id"], target["rival_id"])
                self.assertEqual(question["rival_claim"], target["rival_claim"])
                self.assertEqual(
                    question["falsifier_condition"],
                    target["falsifier_condition"],
                )
                self.assertTrue(inquiry_question_digest(question).startswith("sha256:"))
                self.assertFalse(question["can_confirm_target_semantics"])
                self.assertFalse(question["source_count_can_promote"])
                self.assertFalse(question["provider_agreement_can_promote"])
                self.assertEqual(
                    question["search_protocol"]["default_contemporary_discovery_channel"],
                    "AlphaXiv",
                )
                self.assertIn("absence supplies no support", question["query"])
        validate_adaptive_inquiry_plan(plan)

    def test_attack_target_menu_is_exact_canonical_and_non_authorizing(self) -> None:
        plan = self.build_plan()
        targets = plan["available_attack_targets"]
        target_ids = [target["attack_target_id"] for target in targets]
        self.assertEqual(target_ids, sorted(target_ids))
        self.assertEqual(len(target_ids), len(set(target_ids)))
        self.assertGreater(len(target_ids), 0)
        for target in targets:
            body = {
                key: value
                for key, value in target.items()
                if key != "attack_target_id"
            }
            expected = "AT:" + domain_digest(
                "creib.semantic-forge.attack-target.v1",
                body,
            ).removeprefix("sha256:")
            self.assertEqual(target["attack_target_id"], expected)
            self.assertEqual(
                target["issue_sha256"],
                plan["bindings"]["issue_sha256"],
            )
            self.assertEqual(
                target["warrant_sha256"],
                plan["bindings"]["warrant_sha256"],
            )
        self.assertEqual(plan["proposed_questions"], [])
        self.assertEqual(plan["route"], InquiryRoute.AWAITING_HUMAN_TRIAGE.value)

    def test_external_action_selects_only_a_known_nonempty_target_subset(self) -> None:
        blocked = self.build_plan()
        target_ids = tuple(
            str(item["attack_target_id"])
            for item in blocked["available_attack_targets"][:2]
        )
        triage = self.human_triage(
            blocked["bindings"],  # type: ignore[arg-type]
            attack_target_ids=target_ids,
        )
        plan = self.build_plan(triage=triage)
        self.assertEqual(
            [item["attack_target_id"] for item in plan["proposed_questions"]],
            sorted(target_ids),
        )
        self.assertEqual(len(plan["proposed_questions"]), len(target_ids))

        for attack_target_ids in ((), ("AT:" + "f" * 64,)):
            invalid = self.human_triage(
                blocked["bindings"],  # type: ignore[arg-type]
                attack_target_ids=attack_target_ids,
            )
            directory = self.new_triage_dir()
            before = list(directory.iterdir())
            with self.subTest(attack_target_ids=attack_target_ids), self.assertRaises(
                (RecordError, PolicyViolation)
            ):
                publish_human_triage_against_inputs(
                    directory,
                    invalid,
                    expected_head_triage_id=None,
                    repo_root=ROOT,
                    run_record_path=RUN_PATH,
                    research_ledger_path=LEDGER_PATH,
                )
            self.assertEqual(list(directory.iterdir()), before)

        noncanonical = copy.deepcopy(triage)
        noncanonical["next_action"]["research_target"]["attack_target_ids"].reverse()
        noncanonical["next_action"]["action_id"] = compute_next_action_id(
            noncanonical["next_action"]
        )
        noncanonical["triage_id"] = compute_human_triage_id(noncanonical)
        with self.assertRaisesRegex(RecordError, "canonical lexical order"):
            validate_human_triage(
                noncanonical,
                expected_bindings=blocked["bindings"],  # type: ignore[arg-type]
            )

    def test_selected_assessment_and_action_text_materially_shape_the_query(self) -> None:
        blocked = self.build_plan()
        target_id = str(blocked["available_attack_targets"][0]["attack_target_id"])
        original_assessment = self.locus_assessment(
            discriminator="Try discriminator alpha against the same exact target."
        )
        original = self.build_plan(
            triage=self.human_triage(
                blocked["bindings"],  # type: ignore[arg-type]
                assessments=[original_assessment],
                attack_target_ids=(target_id,),
                action="Run attack protocol alpha.",
            )
        )
        changed_assessment = self.locus_assessment(
            discriminator="Try discriminator beta against the same exact target."
        )
        changed_discriminator = self.build_plan(
            triage=self.human_triage(
                blocked["bindings"],  # type: ignore[arg-type]
                assessments=[changed_assessment],
                attack_target_ids=(target_id,),
                action="Run attack protocol alpha.",
            )
        )
        changed_action = self.build_plan(
            triage=self.human_triage(
                blocked["bindings"],  # type: ignore[arg-type]
                assessments=[original_assessment],
                attack_target_ids=(target_id,),
                action="Run attack protocol gamma.",
            )
        )
        original_query = original["proposed_questions"][0]["query"]
        discriminator_query = changed_discriminator["proposed_questions"][0]["query"]
        action_query = changed_action["proposed_questions"][0]["query"]
        self.assertNotEqual(original_query, discriminator_query)
        self.assertNotEqual(original_query, action_query)
        self.assertIn("discriminator alpha", original_query)
        self.assertIn("discriminator beta", discriminator_query)
        self.assertIn("attack protocol gamma", action_query)

    def test_question_tampering_breaks_content_address_and_schema_is_closed(self) -> None:
        plan = self.external_plan()
        changed = copy.deepcopy(plan)
        changed["proposed_questions"][0]["falsifier_condition"] += " altered"
        with self.assertRaisesRegex(RecordError, "content-addressed ID mismatch"):
            validate_adaptive_inquiry_plan(changed)

        illicit = copy.deepcopy(plan)
        illicit["proposed_questions"][0]["source_count"] = 1000
        with self.assertRaises(RecordError):
            validate_adaptive_inquiry_plan(illicit)

        rebound = copy.deepcopy(plan)
        rebound["proposed_questions"][0]["issue_sha256"] = "sha256:" + "1" * 64
        rebound["proposed_questions"][0]["question_id"] = compute_question_id(
            rebound["proposed_questions"][0]
        )
        rebound["plan_id"] = compute_adaptive_inquiry_plan_id(rebound)
        with self.assertRaisesRegex(
            PolicyViolation,
            "full or flattened attack target",
        ):
            validate_adaptive_inquiry_plan(rebound)

    def test_inquiry_event_cannot_predate_its_exact_plan_triage(self) -> None:
        question = self.external_plan()["proposed_questions"][0]
        with self.assertRaises(InquiryError) as construction_failure:
            build_inquiry_event(
                sequence=1,
                previous_event_id=None,
                event_type="QUESTION_PROPOSED",
                occurred_on="2026-09-02",
                actor_kind="MACHINE",
                question=question,
                from_state=None,
                reason_code="BACKDATED_TRIAGE",
                reason="A deliberately pre-triage proposal.",
                research_ledger=self.ledger,
                research_ledger_binding=self.ledger_binding,
            )
        self.assertEqual(
            construction_failure.exception.error_code,
            "INQUIRY_EVENT_PRECEDES_TRIAGE",
        )

        valid = build_inquiry_event(
            sequence=1,
            previous_event_id=None,
            event_type="QUESTION_PROPOSED",
            occurred_on="2026-09-03",
            actor_kind="MACHINE",
            question=question,
            from_state=None,
            reason_code="CURRENT_TRIAGE",
            reason="A proposal on the exact triage date.",
            research_ledger=self.ledger,
            research_ledger_binding=self.ledger_binding,
        )
        self_rehashed = copy.deepcopy(valid)
        self_rehashed["occurred_on"] = "2026-09-02"
        self_rehashed["event_id"] = compute_event_id(self_rehashed)
        with self.assertRaises(InquiryError) as validation_failure:
            validate_inquiry_event(
                self_rehashed,
                research_ledger=self.ledger,
                expected_research_binding=self.ledger_binding,
            )
        self.assertEqual(
            validation_failure.exception.error_code,
            "INQUIRY_EVENT_PRECEDES_TRIAGE",
        )

    def test_standalone_event_enforces_bound_ledger_chronology(self) -> None:
        question = self.external_plan()["proposed_questions"][0]
        valid = build_inquiry_event(
            sequence=1,
            previous_event_id=None,
            event_type="QUESTION_PROPOSED",
            occurred_on="2026-09-03",
            actor_kind="MACHINE",
            question=question,
            from_state=None,
            reason_code="LEDGER_CHRONOLOGY",
            reason="A proposal on the bound ledger creation date.",
            research_ledger=self.ledger,
            research_ledger_binding=self.ledger_binding,
        )

        impossible_binding = copy.deepcopy(self.ledger_binding)
        impossible_binding["as_of_date"] = "2026-09-04"
        impossible_event = copy.deepcopy(valid)
        impossible_event["research_ledger"] = impossible_binding
        impossible_event["event_id"] = compute_event_id(impossible_event)
        with self.assertRaisesRegex(
            RecordError,
            "as_of_date cannot be after .*created_on",
        ):
            validate_inquiry_event(
                impossible_event,
                research_ledger=self.ledger,
                expected_research_binding=impossible_binding,
            )

        early_triage = copy.deepcopy(valid)
        early_triage["question"]["triage_created_on"] = "2026-09-02"
        early_triage["question"]["question_id"] = compute_question_id(
            early_triage["question"]
        )
        early_triage["event_id"] = compute_event_id(early_triage)
        with self.assertRaises(InquiryError) as triage_failure:
            validate_inquiry_event(
                early_triage,
                research_ledger=self.ledger,
                expected_research_binding=self.ledger_binding,
            )
        self.assertEqual(
            triage_failure.exception.error_code,
            "INQUIRY_TRIAGE_PRECEDES_RESEARCH_LEDGER",
        )
        with self.assertRaises(InquiryError) as construction_failure:
            build_inquiry_event(
                sequence=1,
                previous_event_id=None,
                event_type="QUESTION_PROPOSED",
                occurred_on="2026-09-03",
                actor_kind="MACHINE",
                question=early_triage["question"],
                from_state=None,
                reason_code="EARLY_TRIAGE",
                reason="Attempt to bind a question predating the ledger.",
                research_ledger=self.ledger,
                research_ledger_binding=self.ledger_binding,
            )
        self.assertEqual(
            construction_failure.exception.error_code,
            "INQUIRY_TRIAGE_PRECEDES_RESEARCH_LEDGER",
        )

        early_event = copy.deepcopy(valid)
        early_event["question"]["triage_created_on"] = "2026-09-01"
        early_event["question"]["question_id"] = compute_question_id(
            early_event["question"]
        )
        early_event["occurred_on"] = "2026-09-02"
        early_event["event_id"] = compute_event_id(early_event)
        with self.assertRaises(InquiryError) as event_failure:
            validate_inquiry_event(
                early_event,
                research_ledger=self.ledger,
                expected_research_binding=self.ledger_binding,
            )
        self.assertEqual(
            event_failure.exception.error_code,
            "INQUIRY_EVENT_PRECEDES_RESEARCH_LEDGER",
        )

    def test_low_level_event_and_chain_apis_bind_the_exact_ledger_object(self) -> None:
        ledger_record = load_strict(LEDGER_PATH)
        if type(ledger_record) is not dict:
            self.fail("research ledger fixture must be an object")
        ledger_record["provider_policy"][
            "default_contemporary_discovery_provider"
        ] = "ModernIndex"
        for entry in ledger_record["entries"]:
            if entry["discovery"]["route_kind"] == "default_contemporary_discovery":
                entry["discovery"]["provider"] = "ModernIndex"
                entry["discovery"]["route_locator"] = (
                    "https://modern-index.example/discovery/" + entry["entry_id"]
                )
        rehash_research_ledger_after_entry_change(ledger_record)
        different_ledger = parse_research_ledger(ledger_record)

        question = self.external_plan()["proposed_questions"][0]
        with self.assertRaisesRegex(
            PolicyViolation,
            "record_sha256 does not match the supplied ResearchLedger",
        ):
            build_inquiry_event(
                sequence=1,
                previous_event_id=None,
                event_type="QUESTION_PROPOSED",
                occurred_on="2026-09-03",
                actor_kind="MACHINE",
                question=question,
                from_state=None,
                reason_code="MISMATCHED_LEDGER",
                reason="A different policy ledger paired with the original binding.",
                research_ledger=different_ledger,
                research_ledger_binding=self.ledger_binding,
            )

        valid = build_inquiry_event(
            sequence=1,
            previous_event_id=None,
            event_type="QUESTION_PROPOSED",
            occurred_on="2026-09-03",
            actor_kind="MACHINE",
            question=question,
            from_state=None,
            reason_code="MATCHED_LEDGER",
            reason="The exact policy ledger and binding agree.",
            research_ledger=self.ledger,
            research_ledger_binding=self.ledger_binding,
        )
        with self.assertRaisesRegex(
            PolicyViolation,
            "record_sha256 does not match the supplied ResearchLedger",
        ):
            validate_inquiry_event(
                valid,
                research_ledger=different_ledger,
                expected_research_binding=self.ledger_binding,
            )
        with self.assertRaisesRegex(
            PolicyViolation,
            "record_sha256 does not match the supplied ResearchLedger",
        ):
            verify_inquiry_chain(
                ROOT,
                None,
                research_ledger=different_ledger,
                research_binding=self.ledger_binding,
            )

    def test_self_rehashed_route_cannot_launder_absent_triage(self) -> None:
        plan = self.build_plan()
        changed = copy.deepcopy(plan)
        changed["route"] = InquiryRoute.INTERNAL_MODEL_WORK.value
        changed["route_reason"] = (
            "The selected human action schedules internal model work without "
            "dismissing other live loci."
        )
        changed["plan_id"] = compute_adaptive_inquiry_plan_id(changed)
        with self.assertRaises((RecordError, PolicyViolation)):
            validate_adaptive_inquiry_plan(changed)

    def test_plural_loci_coexist_and_scope_never_short_circuits(self) -> None:
        blocked = self.build_plan()
        bindings = blocked["bindings"]
        assessments = [
            self.locus_assessment(
                loci=("CANDIDATE",),
                mechanism="The candidate permits an unwanted same-reduct rival.",
            ),
            self.locus_assessment(
                loci=("AUXILIARY",),
                location="INTERNAL_HARNESS_SPECIFICATION",
                mechanism="A held-fixed auxiliary may be too weak.",
            ),
            self.locus_assessment(
                loci=("TEST",),
                location="INTERNAL_DEDUCTION_OR_MODEL_FINDING",
                mechanism="The current oracle may fail to expose a role swap.",
            ),
            self.locus_assessment(
                loci=("SCOPE",),
                location="CR_AUTHORITY_INTERPRETATION",
                mechanism="The declared case boundary may omit a relevant authority span.",
            ),
        ]
        selected = next(
            item["assessment_id"]
            for item in assessments
            if item["loci"] == ["CANDIDATE"]
        )
        triage = self.human_triage(
            bindings,  # type: ignore[arg-type]
            assessments=assessments,
            selected_assessment_ids=(str(selected),),
        )
        plan = self.build_plan(triage=triage)

        self.assertEqual(plan["route"], InquiryRoute.EXTERNAL_RESEARCH_REQUIRED.value)
        self.assertNotEqual(plan["route"], InquiryRoute.OUT_OF_SCOPE.value)
        self.assertEqual(triage["overall_status"], "UNRESOLVED")
        self.assertIsNone(triage["semantic_verdict"])
        self.assertNotIn("disposition", triage)
        self.assertEqual(
            {
                locus
                for item in triage["locus_assessments"]
                for locus in item["loci"]
            },
            {"CANDIDATE", "AUXILIARY", "TEST", "SCOPE"},
        )
        self.assertEqual(
            plan["live_locus_assessment_ids"],
            [item["assessment_id"] for item in triage["locus_assessments"]],
        )
        self.assertEqual(plan["epistemic_status"], "UNRESOLVED")
        self.assertIsNone(plan["semantic_verdict"])

    def test_joint_locus_assessment_is_allowed_but_must_be_canonical(self) -> None:
        blocked = self.build_plan()
        joint = self.locus_assessment(loci=("SCOPE", "CANDIDATE"))
        triage = self.human_triage(
            blocked["bindings"],  # type: ignore[arg-type]
            assessments=[joint],
        )
        validate_human_triage(triage, expected_bindings=blocked["bindings"])
        self.assertEqual(triage["locus_assessments"][0]["loci"], ["CANDIDATE", "SCOPE"])

        noncanonical = copy.deepcopy(triage)
        assessment = noncanonical["locus_assessments"][0]
        assessment["loci"] = ["SCOPE", "CANDIDATE"]
        assessment["assessment_id"] = compute_locus_assessment_id(assessment)
        noncanonical["next_action"]["selected_assessment_ids"] = [
            assessment["assessment_id"]
        ]
        noncanonical["next_action"]["action_id"] = compute_next_action_id(
            noncanonical["next_action"]
        )
        noncanonical["triage_id"] = compute_human_triage_id(noncanonical)
        with self.assertRaisesRegex(RecordError, "canonical lexical order"):
            validate_human_triage(
                noncanonical,
                expected_bindings=blocked["bindings"],
            )

    def test_no_action_preserves_all_loci_and_waits_for_human_selection(self) -> None:
        blocked = self.build_plan()
        assessments = [
            self.locus_assessment(
                loci=("AUXILIARY",),
                location="INTERNAL_HARNESS_SPECIFICATION",
                mechanism="One independent harness criticism remains live.",
            ),
            self.locus_assessment(
                loci=("CANDIDATE",),
                mechanism="One independent candidate criticism remains live.",
            ),
        ]
        triage = self.human_triage(
            blocked["bindings"],  # type: ignore[arg-type]
            assessments=assessments,
            include_action=False,
        )
        plan = self.build_plan(triage=triage)
        self.assertEqual(
            plan["route"],
            InquiryRoute.AWAITING_HUMAN_ACTION_SELECTION.value,
        )
        self.assertEqual(plan["proposed_questions"], [])
        self.assertEqual(plan["question_state"], {})
        self.assertIsNone(plan["selected_action_id"])
        self.assertEqual(len(plan["live_locus_assessment_ids"]), 2)

    def test_route_is_selected_by_action_not_locus_name_or_array_position(self) -> None:
        blocked = self.build_plan()
        bindings = blocked["bindings"]
        cases = (
            (
                ("CANDIDATE",),
                "INTERNAL_HARNESS_SPECIFICATION",
                InquiryRoute.INTERNAL_HARNESS_WORK,
            ),
            (
                ("TEST",),
                "INTERNAL_DEDUCTION_OR_MODEL_FINDING",
                InquiryRoute.INTERNAL_MODEL_WORK,
            ),
            (
                ("SCOPE",),
                "CR_AUTHORITY_INTERPRETATION",
                InquiryRoute.AUTHORITY_REVIEW,
            ),
            (
                ("AUXILIARY",),
                "EXTERNAL_CRITICAL_INSTRUMENT",
                InquiryRoute.EXTERNAL_RESEARCH_REQUIRED,
            ),
        )
        for loci, location, expected in cases:
            assessment = self.locus_assessment(loci=loci, location=location)
            triage = self.human_triage(
                bindings,  # type: ignore[arg-type]
                assessments=[assessment],
                route_intent=expected.value,
            )
            with self.subTest(loci=loci, location=location):
                plan = self.build_plan(triage=triage)
                self.assertEqual(plan["route"], expected.value)
                if expected is not InquiryRoute.EXTERNAL_RESEARCH_REQUIRED:
                    self.assertEqual(plan["proposed_questions"], [])

    def test_independent_frontier_requires_explicit_human_choice(self) -> None:
        blocked = self.build_plan()
        bindings = blocked["bindings"]
        first = self.locus_assessment(
            mechanism="Independent external criticism alpha."
        )
        second = self.locus_assessment(
            loci=("AUXILIARY",),
            mechanism="Independent external criticism beta.",
        )
        assessments = [first, second]
        waiting = self.human_triage(
            bindings,  # type: ignore[arg-type]
            assessments=assessments,
            include_action=False,
        )
        self.assertEqual(
            self.build_plan(triage=waiting)["route"],
            InquiryRoute.AWAITING_HUMAN_ACTION_SELECTION.value,
        )

        plans = []
        for selected in (first["assessment_id"], second["assessment_id"]):
            triage = self.human_triage(
                bindings,  # type: ignore[arg-type]
                assessments=assessments,
                selected_assessment_ids=(str(selected),),
            )
            plans.append(self.build_plan(triage=triage))
        self.assertTrue(
            all(
                plan["route"] == InquiryRoute.EXTERNAL_RESEARCH_REQUIRED.value
                for plan in plans
            )
        )
        self.assertNotEqual(plans[0]["selected_action_id"], plans[1]["selected_action_id"])
        self.assertNotEqual(plans[0]["case_sha256"], plans[1]["case_sha256"])

    def test_dependency_frontier_and_graph_integrity_fail_closed(self) -> None:
        blocked = self.build_plan()
        bindings = blocked["bindings"]
        prerequisite = self.locus_assessment(
            loci=("AUXILIARY",),
            mechanism="The auxiliary must be criticized before its dependent candidate.",
        )
        dependent = self.locus_assessment(
            mechanism="The candidate criticism depends on the auxiliary criticism.",
            dependencies=(str(prerequisite["assessment_id"]),),
        )
        assessments = [prerequisite, dependent]
        valid = self.human_triage(
            bindings,  # type: ignore[arg-type]
            assessments=assessments,
            selected_assessment_ids=(str(prerequisite["assessment_id"]),),
            selection_basis="UPSTREAM_DEPENDENCY",
        )
        validate_human_triage(valid, expected_bindings=bindings)  # type: ignore[arg-type]

        blocked_selection = self.human_triage(
            bindings,  # type: ignore[arg-type]
            assessments=assessments,
            selected_assessment_ids=(str(dependent["assessment_id"]),),
        )
        with self.assertRaisesRegex(PolicyViolation, "unresolved dependencies"):
            validate_human_triage(
                blocked_selection,
                expected_bindings=bindings,  # type: ignore[arg-type]
            )

        evidence = self.calibration_disposition_evidence()
        unscheduled = self.human_triage(
            bindings,  # type: ignore[arg-type]
            assessments=assessments,
            include_action=False,
        )
        unauthorized_disposition = self.assessment_disposition(
            prerequisite,
            assessment_origin_triage_id=str(unscheduled["triage_id"]),
            bindings=bindings,  # type: ignore[arg-type]
            disposition="DEFEATED",
            evidence_bindings=[evidence],
        )
        unauthorized_successor = self.human_triage(
            bindings,  # type: ignore[arg-type]
            assessments=assessments,
            assessment_dispositions=[unauthorized_disposition],
            include_action=False,
            sequence=2,
            previous_triage_id=str(unscheduled["triage_id"]),
            transition_kind="SAME_BINDINGS",
        )
        unauthorized_directory = self.new_triage_dir()
        self.write_unchecked_triage_lineage(
            unauthorized_directory,
            [unscheduled, unauthorized_successor],
        )
        with self.assertRaisesRegex(
            PolicyViolation,
            "previously authorized dependency-frontier action",
        ):
            verify_human_triage_chain(
                unauthorized_directory,
                str(unauthorized_successor["triage_id"]),
                expected_bindings=bindings,  # type: ignore[arg-type]
            )

        fake_run_evidence = self.disposition_evidence(
            {
                "run_id": self.report["run_id"],
                "result": "No sources were found.",
            },
            evidence_kind="CALIBRATION_RUN",
            record_id_pointer="/run_id",
            selected_value_pointer="/result",
        )
        fake_disposition = self.assessment_disposition(
            prerequisite,
            assessment_origin_triage_id=str(valid["triage_id"]),
            bindings=bindings,  # type: ignore[arg-type]
            disposition="DEFEATED",
            evidence_bindings=[fake_run_evidence],
        )
        fake_successor = self.human_triage(
            bindings,  # type: ignore[arg-type]
            assessments=assessments,
            assessment_dispositions=[fake_disposition],
            include_action=False,
            sequence=2,
            previous_triage_id=str(valid["triage_id"]),
            transition_kind="SAME_BINDINGS",
        )
        with self.assertRaisesRegex(
            RecordError,
            "adaptive-inquiry-v2.schema.json|calibration-run.schema.json",
        ):
            validate_human_triage(
                fake_successor,
                expected_bindings=bindings,  # type: ignore[arg-type]
            )

        defeated = self.assessment_disposition(
            prerequisite,
            assessment_origin_triage_id=str(valid["triage_id"]),
            bindings=bindings,  # type: ignore[arg-type]
            disposition="DEFEATED",
            evidence_bindings=[evidence],
        )
        successor = self.human_triage(
            bindings,  # type: ignore[arg-type]
            assessments=assessments,
            assessment_dispositions=[defeated],
            selected_assessment_ids=(str(dependent["assessment_id"]),),
            sequence=2,
            previous_triage_id=str(valid["triage_id"]),
            transition_kind="SAME_BINDINGS",
            transition_reason=(
                "Record the exact prerequisite disposition and advance the frontier."
            ),
        )
        directory = self.new_triage_dir()
        first_plan = self.build_plan(triage=valid, triage_dir=directory)
        advanced = self.build_plan(
            triage=successor,
            triage_dir=directory,
            head_triage_id=str(successor["triage_id"]),
        )
        self.assertIn(
            prerequisite["assessment_id"],
            first_plan["live_locus_assessment_ids"],
        )
        self.assertNotIn(
            prerequisite["assessment_id"],
            advanced["live_locus_assessment_ids"],
        )
        self.assertIn(
            dependent["assessment_id"],
            advanced["live_locus_assessment_ids"],
        )
        self.assertEqual(
            advanced["selected_action_id"],
            successor["next_action"]["action_id"],
        )
        round_trip = loads_adaptive_inquiry_plan(
            dumps_adaptive_inquiry_plan(advanced)
        )
        self.assertEqual(round_trip, advanced)
        for question in advanced["proposed_questions"]:
            self.assertEqual(
                question["selected_assessment_ids"],
                [dependent["assessment_id"]],
            )
            self.assertEqual(
                question["selected_locus_assessments"][0][
                    "depends_on_assessment_ids"
                ],
                [prerequisite["assessment_id"]],
            )

        retained = self.assessment_disposition(
            prerequisite,
            assessment_origin_triage_id=str(valid["triage_id"]),
            bindings=bindings,  # type: ignore[arg-type]
            disposition="RETAINED",
            evidence_bindings=[evidence],
        )
        still_blocked = self.human_triage(
            bindings,  # type: ignore[arg-type]
            assessments=assessments,
            assessment_dispositions=[retained],
            selected_assessment_ids=(str(dependent["assessment_id"]),),
            sequence=2,
            previous_triage_id=str(valid["triage_id"]),
            transition_kind="SAME_BINDINGS",
        )
        with self.assertRaisesRegex(PolicyViolation, "unresolved dependencies"):
            validate_human_triage(
                still_blocked,
                expected_bindings=bindings,  # type: ignore[arg-type]
            )

        unknown = self.locus_assessment(
            dependencies=("LA:" + "f" * 64,),
            mechanism="An assessment with a missing prerequisite.",
        )
        unknown_triage = self.human_triage(
            bindings,  # type: ignore[arg-type]
            assessments=[unknown],
            include_action=False,
        )
        with self.assertRaisesRegex(PolicyViolation, "absent from this triage"):
            validate_human_triage(
                unknown_triage,
                expected_bindings=bindings,  # type: ignore[arg-type]
            )

        duplicate_edge = self.locus_assessment(
            dependencies=(
                str(prerequisite["assessment_id"]),
                str(prerequisite["assessment_id"]),
            ),
            mechanism="An assessment with a duplicate prerequisite edge.",
        )
        duplicate_triage = self.human_triage(
            bindings,  # type: ignore[arg-type]
            assessments=[prerequisite, duplicate_edge],
            include_action=False,
        )
        with self.assertRaises(RecordError):
            validate_human_triage(
                duplicate_triage,
                expected_bindings=bindings,  # type: ignore[arg-type]
            )

        self_reference = self.locus_assessment(
            dependencies=("LA:" + "0" * 64,),
            mechanism="A self-referential dependency attempt.",
        )
        self_reference["depends_on_assessment_ids"] = [
            self_reference["assessment_id"]
        ]
        self_ref_triage = self.human_triage(
            bindings,  # type: ignore[arg-type]
            assessments=[self_reference],
            include_action=False,
        )
        self_ref_triage["triage_id"] = compute_human_triage_id(self_ref_triage)
        with self.assertRaises((RecordError, PolicyViolation)):
            validate_human_triage(
                self_ref_triage,
                expected_bindings=bindings,  # type: ignore[arg-type]
            )

        cycle_left = self.locus_assessment(mechanism="Cycle endpoint left.")
        cycle_right = self.locus_assessment(
            mechanism="Cycle endpoint right.",
            dependencies=(str(cycle_left["assessment_id"]),),
        )
        cycle_left["depends_on_assessment_ids"] = [cycle_right["assessment_id"]]
        cycle_triage = self.human_triage(
            bindings,  # type: ignore[arg-type]
            assessments=[cycle_left, cycle_right],
            include_action=False,
        )
        cycle_triage["triage_id"] = compute_human_triage_id(cycle_triage)
        with self.assertRaises((RecordError, PolicyViolation)):
            validate_human_triage(
                cycle_triage,
                expected_bindings=bindings,  # type: ignore[arg-type]
            )

    def test_full_calibration_evidence_cannot_select_run_id_as_bearing_value(
        self,
    ) -> None:
        blocked = self.build_plan()
        bindings = blocked["bindings"]
        assessment = self.locus_assessment()
        genesis = self.human_triage(
            bindings,  # type: ignore[arg-type]
            assessments=[assessment],
        )
        wrong_pointer = self.disposition_evidence(
            copy.deepcopy(self.report),
            evidence_kind="CALIBRATION_RUN",
            record_id_pointer="/run_id",
            selected_value_pointer="/run_id",
            bearing=(
                "A run identifier cannot stand in for the exact bound "
                "calibration observation."
            ),
        )
        disposition = self.assessment_disposition(
            assessment,
            assessment_origin_triage_id=str(genesis["triage_id"]),
            bindings=bindings,  # type: ignore[arg-type]
            disposition="DEFEATED",
            evidence_bindings=[wrong_pointer],
        )
        successor = self.human_triage(
            bindings,  # type: ignore[arg-type]
            assessments=[assessment],
            assessment_dispositions=[disposition],
            include_action=False,
            sequence=2,
            previous_triage_id=str(genesis["triage_id"]),
            transition_kind="SAME_BINDINGS",
        )

        self.assertEqual(
            wrong_pointer["evidence_binding_id"],
            compute_evidence_binding_id(wrong_pointer),
        )
        self.assertEqual(
            disposition["disposition_id"],
            compute_assessment_disposition_id(disposition),
        )
        self.assertEqual(successor["triage_id"], compute_human_triage_id(successor))
        with self.assertRaisesRegex(
            (RecordError, PolicyViolation),
            "selected_value_pointer|exact bound observation",
        ):
            validate_human_triage(
                successor,
                expected_bindings=bindings,  # type: ignore[arg-type]
            )

    def test_action_route_and_external_target_are_exactly_bound(self) -> None:
        blocked = self.build_plan()
        bindings = blocked["bindings"]
        internal = self.locus_assessment(
            location="INTERNAL_HARNESS_SPECIFICATION"
        )
        incompatible = self.human_triage(
            bindings,  # type: ignore[arg-type]
            assessments=[internal],
            route_intent="EXTERNAL_RESEARCH_REQUIRED",
        )
        with self.assertRaisesRegex(PolicyViolation, "route_intent contradicts"):
            validate_human_triage(
                incompatible,
                expected_bindings=bindings,  # type: ignore[arg-type]
            )

        external = self.human_triage(bindings)  # type: ignore[arg-type]
        external["next_action"]["research_target"]["issue_sha256"] = (
            "sha256:" + "1" * 64
        )
        external["next_action"]["action_id"] = compute_next_action_id(
            external["next_action"]
        )
        external["triage_id"] = compute_human_triage_id(external)
        with self.assertRaisesRegex(PolicyViolation, "exact issue and warrant"):
            validate_human_triage(
                external,
                expected_bindings=bindings,  # type: ignore[arg-type]
            )

    def test_unresolved_is_overall_only_and_local_fields_are_concrete(self) -> None:
        blocked = self.build_plan()
        bindings = blocked["bindings"]
        triage = self.human_triage(bindings)  # type: ignore[arg-type]
        assessment = triage["locus_assessments"][0]
        self.assertEqual(triage["overall_status"], "UNRESOLVED")
        for field in ("mechanism", "relevance", "discriminator", "scope"):
            self.assertTrue(assessment[field])
        self.assertEqual(assessment["status"], "LIVE")
        self.assertNotIn("UNRESOLVED", assessment["loci"])

        invalid_local = copy.deepcopy(triage)
        invalid_assessment = invalid_local["locus_assessments"][0]
        invalid_assessment["loci"] = ["UNRESOLVED"]
        invalid_assessment["assessment_id"] = compute_locus_assessment_id(
            invalid_assessment
        )
        invalid_local["next_action"]["selected_assessment_ids"] = [
            invalid_assessment["assessment_id"]
        ]
        invalid_local["next_action"]["action_id"] = compute_next_action_id(
            invalid_local["next_action"]
        )
        invalid_local["triage_id"] = compute_human_triage_id(invalid_local)
        with self.assertRaises(RecordError):
            validate_human_triage(
                invalid_local,
                expected_bindings=bindings,  # type: ignore[arg-type]
            )

        invalid_status = copy.deepcopy(triage)
        invalid_status["locus_assessments"][0]["status"] = "UNRESOLVED"
        invalid_status["locus_assessments"][0]["assessment_id"] = (
            compute_locus_assessment_id(invalid_status["locus_assessments"][0])
        )
        invalid_status["next_action"]["selected_assessment_ids"] = [
            invalid_status["locus_assessments"][0]["assessment_id"]
        ]
        invalid_status["next_action"]["action_id"] = compute_next_action_id(
            invalid_status["next_action"]
        )
        invalid_status["triage_id"] = compute_human_triage_id(invalid_status)
        with self.assertRaises(RecordError):
            validate_human_triage(
                invalid_status,
                expected_bindings=bindings,  # type: ignore[arg-type]
            )

    def test_set_like_triage_arrays_require_canonical_unique_order(self) -> None:
        blocked = self.build_plan()
        bindings = blocked["bindings"]
        first = self.locus_assessment(mechanism="Canonical assessment alpha.")
        second = self.locus_assessment(
            loci=("AUXILIARY",),
            mechanism="Canonical assessment beta.",
        )
        triage = self.human_triage(
            bindings,  # type: ignore[arg-type]
            assessments=[first, second],
            selected_assessment_ids=(
                str(first["assessment_id"]),
                str(second["assessment_id"]),
            ),
        )
        validate_human_triage(triage, expected_bindings=bindings)  # type: ignore[arg-type]

        reversed_assessments = copy.deepcopy(triage)
        reversed_assessments["locus_assessments"].reverse()
        reversed_assessments["triage_id"] = compute_human_triage_id(
            reversed_assessments
        )
        with self.assertRaisesRegex(RecordError, "canonical assessment_id order"):
            validate_human_triage(
                reversed_assessments,
                expected_bindings=bindings,  # type: ignore[arg-type]
            )

        reversed_selection = copy.deepcopy(triage)
        reversed_selection["next_action"]["selected_assessment_ids"].reverse()
        reversed_selection["next_action"]["action_id"] = compute_next_action_id(
            reversed_selection["next_action"]
        )
        reversed_selection["triage_id"] = compute_human_triage_id(
            reversed_selection
        )
        with self.assertRaisesRegex(RecordError, "canonical lexical order"):
            validate_human_triage(
                reversed_selection,
                expected_bindings=bindings,  # type: ignore[arg-type]
            )

        duplicate_assessment = copy.deepcopy(triage)
        duplicate_assessment["locus_assessments"] = [
            duplicate_assessment["locus_assessments"][0],
            duplicate_assessment["locus_assessments"][0],
        ]
        duplicate_assessment["next_action"] = None
        duplicate_assessment["triage_id"] = compute_human_triage_id(
            duplicate_assessment
        )
        with self.assertRaises(RecordError):
            validate_human_triage(
                duplicate_assessment,
                expected_bindings=bindings,  # type: ignore[arg-type]
            )

    def test_published_triage_genesis_is_canonical_unique_and_terminal(self) -> None:
        blocked = self.build_plan()
        bindings = blocked["bindings"]
        directory = self.new_triage_dir()
        empty = verify_human_triage_chain(
            directory,
            None,
            expected_bindings=bindings,  # type: ignore[arg-type]
        )
        self.assertIsNone(empty.head_triage_id)
        self.assertEqual(empty.triages, ())

        triage = self.human_triage(
            bindings,  # type: ignore[arg-type]
            include_action=False,
        )
        output = publish_human_triage_against_inputs(
            directory,
            triage,
            expected_head_triage_id=None,
            repo_root=ROOT,
            run_record_path=RUN_PATH,
            research_ledger_path=LEDGER_PATH,
        )
        payload = canonical_bytes(triage) + b"\n"
        expected_record = f"{str(triage['triage_id']).replace(':', '-')}.json"
        self.assertEqual(output.name, expected_record)
        self.assertEqual(
            {path.name for path in directory.iterdir()},
            {expected_record, "NEXT-GENESIS.claim"},
        )
        self.assertEqual(output.read_bytes(), payload)
        self.assertEqual((directory / "NEXT-GENESIS.claim").read_bytes(), payload)
        state = verify_human_triage_chain(
            directory,
            str(triage["triage_id"]),
            expected_bindings=bindings,  # type: ignore[arg-type]
        )
        self.assertEqual(state.triages, (triage,))
        with self.assertRaises(InquiryError):
            verify_human_triage_chain(
                directory,
                None,
                expected_bindings=bindings,  # type: ignore[arg-type]
            )

        free_directory = self.new_triage_dir()
        with self.assertRaisesRegex(
            PolicyViolation,
            "embedded human triage does not equal",
        ):
            build_adaptive_inquiry_plan(
                repo_root=ROOT,
                run_record_path=RUN_PATH,
                research_ledger_path=LEDGER_PATH,
                triage_dir=free_directory,
                triage=triage,
            )
        self.assertEqual(list(free_directory.iterdir()), [])

    def test_triage_publication_recovers_exact_claim_only_reservation(self) -> None:
        blocked = self.build_plan()
        bindings = blocked["bindings"]
        directory = self.new_triage_dir()
        triage = self.human_triage(
            bindings,  # type: ignore[arg-type]
            include_action=False,
        )
        payload = canonical_bytes(triage) + b"\n"
        output = directory / f"{str(triage['triage_id']).replace(':', '-')}.json"
        claim = directory / "NEXT-GENESIS.claim"
        real_link = os.link
        link_calls = 0

        def fail_record_link(source: object, target: object) -> None:
            nonlocal link_calls
            link_calls += 1
            if link_calls == 2:
                raise OSError(errno.EIO, "simulated record-link interruption")
            real_link(source, target)  # type: ignore[arg-type]

        with mock.patch(
            "creib.forge.inquiry.os.link",
            side_effect=fail_record_link,
        ), self.assertRaises(InquiryError) as interrupted:
            publish_human_triage_against_inputs(
                directory,
                triage,
                expected_head_triage_id=None,
                repo_root=ROOT,
                run_record_path=RUN_PATH,
                research_ledger_path=LEDGER_PATH,
            )
        self.assertEqual(interrupted.exception.error_code, "INQUIRY_TRIAGE_WRITE_FAILED")
        self.assertEqual(claim.read_bytes(), payload)
        self.assertFalse(output.exists())
        self.assertEqual(list(directory.glob(".human-triage-*.tmp")), [])
        with self.assertRaises(InquiryError):
            verify_human_triage_chain(
                directory,
                None,
                expected_bindings=bindings,  # type: ignore[arg-type]
            )

        recovered = publish_human_triage_against_inputs(
            directory,
            triage,
            expected_head_triage_id=None,
            repo_root=ROOT,
            run_record_path=RUN_PATH,
            research_ledger_path=LEDGER_PATH,
        )
        self.assertEqual(recovered, output)
        self.assertTrue(os.path.samefile(claim, output))
        self.assertEqual(
            publish_human_triage_against_inputs(
                directory,
                triage,
                expected_head_triage_id=None,
                repo_root=ROOT,
                run_record_path=RUN_PATH,
                research_ledger_path=LEDGER_PATH,
            ),
            output,
        )

        sibling = self.human_triage(
            bindings,  # type: ignore[arg-type]
            assessments=[
                self.locus_assessment(
                    mechanism="A different successor cannot replace a durable reservation."
                )
            ],
            include_action=False,
        )
        with self.assertRaises(InquiryError) as stale:
            publish_human_triage_against_inputs(
                directory,
                sibling,
                expected_head_triage_id=None,
                repo_root=ROOT,
                run_record_path=RUN_PATH,
                research_ledger_path=LEDGER_PATH,
            )
        self.assertEqual(stale.exception.error_code, "INQUIRY_TRIAGE_STALE_HEAD")
        self.assertEqual(claim.read_bytes(), payload)

    def test_triage_retry_resyncs_complete_pair_without_relinking(self) -> None:
        blocked = self.build_plan()
        bindings = blocked["bindings"]
        directory = self.new_triage_dir()
        triage = self.human_triage(
            bindings,  # type: ignore[arg-type]
            include_action=False,
        )
        output = directory / f"{str(triage['triage_id']).replace(':', '-')}.json"
        claim = directory / "NEXT-GENESIS.claim"
        fsync_calls = 0

        def fail_second_directory_fsync(_directory: Path) -> None:
            nonlocal fsync_calls
            fsync_calls += 1
            if fsync_calls == 2:
                raise OSError(errno.EIO, "simulated post-link directory fsync failure")

        with mock.patch(
            "creib.forge.inquiry._fsync_directory",
            side_effect=fail_second_directory_fsync,
        ), self.assertRaises(InquiryError) as interrupted:
            publish_human_triage_against_inputs(
                directory,
                triage,
                expected_head_triage_id=None,
                repo_root=ROOT,
                run_record_path=RUN_PATH,
                research_ledger_path=LEDGER_PATH,
            )
        self.assertEqual(fsync_calls, 2)
        self.assertEqual(interrupted.exception.error_code, "INQUIRY_TRIAGE_WRITE_FAILED")
        self.assertTrue(output.exists())
        self.assertTrue(os.path.samefile(claim, output))
        before = {path.name: path.read_bytes() for path in directory.iterdir()}

        with mock.patch(
            "creib.forge.inquiry.os.link",
            side_effect=AssertionError("a complete retry must not relink"),
        ) as link_mock, mock.patch(
            "creib.forge.inquiry._fsync_directory"
        ) as retry_fsync:
            recovered = publish_human_triage_against_inputs(
                directory,
                triage,
                expected_head_triage_id=None,
                repo_root=ROOT,
                run_record_path=RUN_PATH,
                research_ledger_path=LEDGER_PATH,
            )
        self.assertEqual(recovered, output)
        link_mock.assert_not_called()
        retry_fsync.assert_called_once_with(directory)
        self.assertEqual(
            {path.name: path.read_bytes() for path in directory.iterdir()},
            before,
        )

    def test_non_genesis_triage_claim_only_retry_rolls_forward(self) -> None:
        blocked = self.build_plan()
        bindings = blocked["bindings"]
        directory = self.new_triage_dir()
        first_assessment = self.locus_assessment(
            mechanism="A parent criticism remains live during child recovery."
        )
        genesis = self.human_triage(
            bindings,  # type: ignore[arg-type]
            assessments=[first_assessment],
            include_action=False,
        )
        publish_human_triage_against_inputs(
            directory,
            genesis,
            expected_head_triage_id=None,
            repo_root=ROOT,
            run_record_path=RUN_PATH,
            research_ledger_path=LEDGER_PATH,
        )
        added_assessment = self.locus_assessment(
            mechanism="An additive child criticism survives interrupted publication."
        )
        successor = self.human_triage(
            bindings,  # type: ignore[arg-type]
            assessments=[first_assessment, added_assessment],
            include_action=False,
            sequence=2,
            previous_triage_id=str(genesis["triage_id"]),
            transition_kind="SAME_BINDINGS",
            transition_reason="Add one criticism without dropping the parent record.",
        )
        output = directory / f"{str(successor['triage_id']).replace(':', '-')}.json"
        claim = directory / (
            f"NEXT-{str(genesis['triage_id']).removeprefix('HT:')}.claim"
        )
        real_link = os.link
        link_calls = 0

        def fail_record_link(source: object, target: object) -> None:
            nonlocal link_calls
            link_calls += 1
            if link_calls == 2:
                raise OSError(errno.EIO, "simulated child record-link interruption")
            real_link(source, target)  # type: ignore[arg-type]

        with mock.patch(
            "creib.forge.inquiry.os.link",
            side_effect=fail_record_link,
        ), self.assertRaises(InquiryError) as interrupted:
            publish_human_triage_against_inputs(
                directory,
                successor,
                expected_head_triage_id=str(genesis["triage_id"]),
                repo_root=ROOT,
                run_record_path=RUN_PATH,
                research_ledger_path=LEDGER_PATH,
            )
        self.assertEqual(interrupted.exception.error_code, "INQUIRY_TRIAGE_WRITE_FAILED")
        self.assertTrue(claim.exists())
        self.assertFalse(output.exists())

        recovered = publish_human_triage_against_inputs(
            directory,
            successor,
            expected_head_triage_id=str(genesis["triage_id"]),
            repo_root=ROOT,
            run_record_path=RUN_PATH,
            research_ledger_path=LEDGER_PATH,
        )
        self.assertEqual(recovered, output)
        verified = verify_human_triage_chain(
            directory,
            str(successor["triage_id"]),
            expected_bindings=bindings,  # type: ignore[arg-type]
        )
        self.assertEqual(verified.triages, (genesis, successor))

    def test_pending_recovery_exception_is_scoped_to_the_exact_parent(self) -> None:
        bindings = self.build_plan()["bindings"]
        triage_dir = self.new_triage_dir()
        triage_claim = triage_dir / f"NEXT-{'f' * 64}.claim"
        triage_claim.write_bytes(b"not a successor for the selected parent\n")
        with self.assertRaises(InquiryError) as bad_triage_claim:
            verify_human_triage_chain(
                triage_dir,
                None,
                expected_bindings=bindings,  # type: ignore[arg-type]
                _pending_successor_claim=(
                    triage_claim.name,
                    triage_claim.read_bytes(),
                ),
            )
        self.assertEqual(
            bad_triage_claim.exception.error_code,
            "INQUIRY_TRIAGE_PENDING_CLAIM_INVALID",
        )

        event_dir = self._test_root / "wrong-parent-event-recovery"
        event_dir.mkdir()
        event_claim = event_dir / f"NEXT-{'f' * 64}.claim"
        event_claim.write_bytes(b"not a successor for the selected parent\n")
        with self.assertRaises(InquiryError) as bad_event_claim:
            verify_inquiry_chain(
                event_dir,
                None,
                research_ledger=self.ledger,
                research_binding=self.ledger_binding,
                required_schema_version=EVENT_SCHEMA,
                _pending_successor_claim=(
                    event_claim.name,
                    event_claim.read_bytes(),
                ),
            )
        self.assertEqual(
            bad_event_claim.exception.error_code,
            "INQUIRY_EVENT_PENDING_CLAIM_INVALID",
        )

    def test_pending_recovery_rejects_malformed_payload_and_extra_inventory(
        self,
    ) -> None:
        blocked = self.build_plan()
        bindings = blocked["bindings"]
        triage = self.human_triage(
            bindings,  # type: ignore[arg-type]
            include_action=False,
        )
        plan = self.external_plan()
        question = plan["proposed_questions"][0]
        event = build_inquiry_event(
            sequence=1,
            previous_event_id=None,
            event_type="QUESTION_PROPOSED",
            occurred_on="2026-09-03",
            actor_kind="MACHINE",
            question=question,
            from_state=None,
            reason_code="PENDING_PAYLOAD",
            reason="Supply a valid pending event payload for inventory checks.",
            research_ledger=self.ledger,
            research_ledger_binding=self.ledger_binding,
        )

        malformed_triage_dir = self.new_triage_dir()
        malformed_triage_claim = malformed_triage_dir / "NEXT-GENESIS.claim"
        malformed_triage_claim.write_bytes(b"{\n")
        with self.assertRaises((InquiryError, RecordError)):
            verify_human_triage_chain(
                malformed_triage_dir,
                None,
                expected_bindings=bindings,  # type: ignore[arg-type]
                _pending_successor_claim=(
                    malformed_triage_claim.name,
                    malformed_triage_claim.read_bytes(),
                ),
            )

        malformed_event_dir = self._test_root / "malformed-event-recovery"
        malformed_event_dir.mkdir()
        malformed_event_claim = malformed_event_dir / "NEXT-GENESIS.claim"
        malformed_event_claim.write_bytes(b"{\n")
        with self.assertRaises((InquiryError, RecordError)):
            verify_inquiry_chain(
                malformed_event_dir,
                None,
                research_ledger=self.ledger,
                research_binding=self.ledger_binding,
                required_schema_version=EVENT_SCHEMA,
                _pending_successor_claim=(
                    malformed_event_claim.name,
                    malformed_event_claim.read_bytes(),
                ),
            )

        extra_triage_dir = self.new_triage_dir()
        triage_payload = canonical_bytes(triage) + b"\n"
        (extra_triage_dir / "NEXT-GENESIS.claim").write_bytes(triage_payload)
        (extra_triage_dir / f"NEXT-{'f' * 64}.claim").write_bytes(b"unrelated\n")
        (extra_triage_dir / f"HT-{'f' * 64}.json").write_bytes(b"{}\n")
        with self.assertRaises(InquiryError) as extra_triage:
            verify_human_triage_chain(
                extra_triage_dir,
                None,
                expected_bindings=bindings,  # type: ignore[arg-type]
                _pending_successor_claim=("NEXT-GENESIS.claim", triage_payload),
            )
        self.assertEqual(
            extra_triage.exception.error_code,
            "INQUIRY_TRIAGE_HEAD_REQUIRED",
        )

        extra_event_dir = self._test_root / "extra-event-recovery-inventory"
        extra_event_dir.mkdir()
        event_payload = canonical_bytes(event) + b"\n"
        (extra_event_dir / "NEXT-GENESIS.claim").write_bytes(event_payload)
        (extra_event_dir / f"NEXT-{'f' * 64}.claim").write_bytes(b"unrelated\n")
        (extra_event_dir / f"IE-{'f' * 64}.json").write_bytes(b"{}\n")
        with self.assertRaises(InquiryError) as extra_event:
            verify_inquiry_chain(
                extra_event_dir,
                None,
                research_ledger=self.ledger,
                research_binding=self.ledger_binding,
                required_schema_version=EVENT_SCHEMA,
                _pending_successor_claim=("NEXT-GENESIS.claim", event_payload),
            )
        self.assertEqual(
            extra_event.exception.error_code,
            "INQUIRY_EVENT_HEAD_REQUIRED",
        )

    def test_triage_successor_cannot_drop_or_rewrite_any_live_criticism(self) -> None:
        blocked = self.build_plan()
        bindings = blocked["bindings"]
        assessments = [
            self.locus_assessment(
                loci=(locus,),
                location=location,
                mechanism=f"Independent live {locus.lower()} criticism.",
            )
            for locus, location in (
                ("CANDIDATE", "EXTERNAL_CRITICAL_INSTRUMENT"),
                ("AUXILIARY", "INTERNAL_HARNESS_SPECIFICATION"),
                ("TEST", "INTERNAL_DEDUCTION_OR_MODEL_FINDING"),
                ("SCOPE", "CR_AUTHORITY_INTERPRETATION"),
            )
        ]
        genesis = self.human_triage(
            bindings,  # type: ignore[arg-type]
            assessments=assessments,
            include_action=False,
        )
        directory = self.new_triage_dir()
        publish_human_triage_against_inputs(
            directory,
            genesis,
            expected_head_triage_id=None,
            repo_root=ROOT,
            run_record_path=RUN_PATH,
            research_ledger_path=LEDGER_PATH,
        )

        dropped = self.human_triage(
            bindings,  # type: ignore[arg-type]
            assessments=[assessments[0]],
            include_action=False,
            sequence=2,
            previous_triage_id=str(genesis["triage_id"]),
            transition_kind="SAME_BINDINGS",
            transition_reason="Attempt to erase three still-live criticisms.",
        )
        rewritten_assessments = copy.deepcopy(assessments)
        rewritten_assessments[0]["mechanism"] += " Silently rewritten."
        rewritten_assessments[0]["assessment_id"] = compute_locus_assessment_id(
            rewritten_assessments[0]
        )
        rewritten = self.human_triage(
            bindings,  # type: ignore[arg-type]
            assessments=rewritten_assessments,
            include_action=False,
            sequence=2,
            previous_triage_id=str(genesis["triage_id"]),
            transition_kind="SAME_BINDINGS",
            transition_reason="Attempt to replace a criticism under a new ID.",
        )
        before = {
            path.name: path.read_bytes()
            for path in directory.iterdir()
        }
        for label, successor in (("drop", dropped), ("rewrite", rewritten)):
            with self.subTest(label=label), self.assertRaisesRegex(
                PolicyViolation,
                "dropped live locus assessments",
            ):
                publish_human_triage_against_inputs(
                    directory,
                    successor,
                    expected_head_triage_id=str(genesis["triage_id"]),
                    repo_root=ROOT,
                    run_record_path=RUN_PATH,
                    research_ledger_path=LEDGER_PATH,
                )
            self.assertEqual(
                {path.name: path.read_bytes() for path in directory.iterdir()},
                before,
            )

    def test_additive_triage_successor_may_add_and_reprioritize_only(self) -> None:
        blocked = self.build_plan()
        bindings = blocked["bindings"]
        first = self.locus_assessment(mechanism="Live criticism alpha.")
        second = self.locus_assessment(mechanism="Live criticism beta.")
        genesis = self.human_triage(
            bindings,  # type: ignore[arg-type]
            assessments=[first, second],
            selected_assessment_ids=(str(first["assessment_id"]),),
            attack_target_ids=(
                str(blocked["available_attack_targets"][0]["attack_target_id"]),
            ),
        )
        directory = self.new_triage_dir()
        publish_human_triage_against_inputs(
            directory,
            genesis,
            expected_head_triage_id=None,
            repo_root=ROOT,
            run_record_path=RUN_PATH,
            research_ledger_path=LEDGER_PATH,
        )
        added = self.locus_assessment(mechanism="Newly articulated criticism gamma.")
        successor = self.human_triage(
            bindings,  # type: ignore[arg-type]
            assessments=[first, second, added],
            selected_assessment_ids=(str(second["assessment_id"]),),
            attack_target_ids=(
                str(blocked["available_attack_targets"][1]["attack_target_id"]),
            ),
            sequence=2,
            previous_triage_id=str(genesis["triage_id"]),
            transition_kind="SAME_BINDINGS",
            transition_reason=(
                "Preserve all criticisms, add one, and schedule a different attack."
            ),
        )
        publish_human_triage_against_inputs(
            directory,
            successor,
            expected_head_triage_id=str(genesis["triage_id"]),
            repo_root=ROOT,
            run_record_path=RUN_PATH,
            research_ledger_path=LEDGER_PATH,
        )
        state = verify_human_triage_chain(
            directory,
            str(successor["triage_id"]),
            expected_bindings=bindings,  # type: ignore[arg-type]
        )
        self.assertEqual(state.triages, (genesis, successor))
        self.assertTrue(
            {
                item["assessment_id"]
                for item in genesis["locus_assessments"]
            }.issubset(
                {
                    item["assessment_id"]
                    for item in successor["locus_assessments"]
                }
            )
        )
        self.assertNotEqual(
            genesis["next_action"]["action_id"],
            successor["next_action"]["action_id"],
        )
        with self.assertRaises(InquiryError):
            verify_human_triage_chain(
                directory,
                str(genesis["triage_id"]),
                expected_bindings=bindings,  # type: ignore[arg-type]
            )

    def test_binding_change_transition_preserves_lineage_and_clears_action(self) -> None:
        blocked = self.build_plan()
        bindings = blocked["bindings"]
        first = self.locus_assessment(
            mechanism="Criticism alpha survives input change."
        )
        second = self.locus_assessment(
            mechanism="Criticism beta depends on alpha under each exact binding.",
            dependencies=(str(first["assessment_id"]),),
        )
        assessments = [first, second]
        genesis = self.human_triage(
            bindings,  # type: ignore[arg-type]
            assessments=assessments,
            selected_assessment_ids=(str(first["assessment_id"]),),
            selection_basis="UPSTREAM_DEPENDENCY",
        )
        changed_bindings = copy.deepcopy(bindings)
        changed_bindings["run_record_file_sha256"] = "a" * 64
        changed_bindings["run_contract_sha256"] = "b" * 64
        successor = self.human_triage(
            changed_bindings,
            assessments=assessments,
            include_action=False,
            sequence=2,
            previous_triage_id=str(genesis["triage_id"]),
            transition_kind="INPUT_BINDING_CHANGED",
            transition_reason=(
                "Inputs changed; carry every criticism and require fresh scheduling."
            ),
        )
        directory = self.new_triage_dir()
        self.write_unchecked_triage_lineage(directory, [genesis, successor])
        state = verify_human_triage_chain(
            directory,
            str(successor["triage_id"]),
            expected_bindings=changed_bindings,
        )
        self.assertEqual(state.triages[-1]["next_action"], None)
        self.assertEqual(
            state.triages[-1]["locus_assessments"],
            state.triages[0]["locus_assessments"],
        )
        self.assertEqual(
            state.triages[-1]["bindings"]["authority_sha256"],
            state.triages[0]["bindings"]["authority_sha256"],
        )
        self.assertEqual(
            state.triages[-1]["bindings"]["research_ledger"]["ledger_id"],
            state.triages[0]["bindings"]["research_ledger"]["ledger_id"],
        )

        defeated_before_change = self.assessment_disposition(
            first,
            assessment_origin_triage_id=str(genesis["triage_id"]),
            bindings=bindings,  # type: ignore[arg-type]
            disposition="DEFEATED",
            evidence_bindings=[self.calibration_disposition_evidence()],
        )
        disposed_before_change = self.human_triage(
            bindings,  # type: ignore[arg-type]
            assessments=assessments,
            assessment_dispositions=[defeated_before_change],
            include_action=False,
            sequence=2,
            previous_triage_id=str(genesis["triage_id"]),
            transition_kind="SAME_BINDINGS",
            transition_reason="Treat the scheduled prerequisite for the old binding.",
        )
        rolled = self.human_triage(
            changed_bindings,
            assessments=assessments,
            assessment_dispositions=[defeated_before_change],
            include_action=False,
            sequence=3,
            previous_triage_id=str(disposed_before_change["triage_id"]),
            transition_kind="INPUT_BINDING_CHANGED",
            transition_reason=(
                "Preserve the old disposition but make it ineffective after rollover."
            ),
        )
        reselected = self.human_triage(
            changed_bindings,
            assessments=assessments,
            assessment_dispositions=[defeated_before_change],
            selected_assessment_ids=(str(first["assessment_id"]),),
            selection_basis="UPSTREAM_DEPENDENCY",
            sequence=4,
            previous_triage_id=str(rolled["triage_id"]),
            transition_kind="SAME_BINDINGS",
            transition_reason=(
                "Reselect the prerequisite because its old-binding disposition is inactive."
            ),
        )
        rollover_directory = self.new_triage_dir()
        self.write_unchecked_triage_lineage(
            rollover_directory,
            [genesis, disposed_before_change, rolled, reselected],
        )
        rollover_state = verify_human_triage_chain(
            rollover_directory,
            str(reselected["triage_id"]),
            expected_bindings=changed_bindings,
        )
        self.assertEqual(
            rollover_state.triages[-1]["next_action"]["selected_assessment_ids"],
            [first["assessment_id"]],
        )

        variants: list[tuple[str, dict[str, object], str]] = []
        wrong_kind = copy.deepcopy(successor)
        wrong_kind["transition_kind"] = "SAME_BINDINGS"
        wrong_kind["triage_id"] = compute_human_triage_id(wrong_kind)
        variants.append(("transition", wrong_kind, "INPUT_BINDING_CHANGED"))

        dropped = copy.deepcopy(successor)
        dropped["locus_assessments"] = [
            item
            for item in dropped["locus_assessments"]
            if item["assessment_id"] == first["assessment_id"]
        ]
        dropped["triage_id"] = compute_human_triage_id(dropped)
        variants.append(("dropped", dropped, "dropped live locus assessments"))

        scheduled = copy.deepcopy(successor)
        scheduled["next_action"] = self.next_action(
            changed_bindings,
            assessments,
            attack_target_ids=(
                str(blocked["available_attack_targets"][0]["attack_target_id"]),
            ),
        )
        scheduled["triage_id"] = compute_human_triage_id(scheduled)
        variants.append(("action", scheduled, "next_action null"))

        changed_authority = copy.deepcopy(successor)
        changed_authority["bindings"]["authority_sha256"] = "c" * 64
        changed_authority["triage_id"] = compute_human_triage_id(changed_authority)
        variants.append(("authority", changed_authority, "preserve authority"))

        changed_ledger = copy.deepcopy(successor)
        changed_ledger["bindings"]["research_ledger"]["ledger_id"] = (
            "SMF-RESEARCH-UNRELATED"
        )
        changed_ledger["triage_id"] = compute_human_triage_id(changed_ledger)
        variants.append(("ledger", changed_ledger, "research-ledger identity"))

        for label, invalid, message in variants:
            bad_directory = self.new_triage_dir()
            self.write_unchecked_triage_lineage(bad_directory, [genesis, invalid])
            with self.subTest(label=label), self.assertRaisesRegex(
                PolicyViolation,
                message,
            ):
                verify_human_triage_chain(
                    bad_directory,
                    str(invalid["triage_id"]),
                    expected_bindings=invalid["bindings"],  # type: ignore[arg-type]
                )

        changed_pointers = (
            "/run_contract_sha256",
            "/run_record_file_sha256",
        )
        delta = {
            "record_id": "TRIAGE-BINDING-DELTA",
            "previous_bindings": copy.deepcopy(bindings),
            "current_bindings": copy.deepcopy(changed_bindings),
            "changed_binding_pointers": list(changed_pointers),
        }
        stale_evidence = self.disposition_evidence(
            delta,
            evidence_kind="INPUT_BINDING_DELTA",
            record_id_pointer="/record_id",
        )
        stale = self.assessment_disposition(
            assessments[0],
            assessment_origin_triage_id=str(genesis["triage_id"]),
            bindings=changed_bindings,
            disposition="STALE_BY_BINDING_CHANGE",
            evidence_bindings=[stale_evidence],
            superseded_bindings=bindings,  # type: ignore[arg-type]
            changed_binding_pointers=changed_pointers,
        )
        stale_successor = self.human_triage(
            changed_bindings,
            assessments=assessments,
            assessment_dispositions=[stale],
            include_action=False,
            sequence=2,
            previous_triage_id=str(genesis["triage_id"]),
            transition_kind="INPUT_BINDING_CHANGED",
            transition_reason=(
                "Carry every criticism and record one exact input-bound staleness judgment."
            ),
        )
        stale_directory = self.new_triage_dir()
        self.write_unchecked_triage_lineage(
            stale_directory,
            [genesis, stale_successor],
        )
        stale_state = verify_human_triage_chain(
            stale_directory,
            str(stale_successor["triage_id"]),
            expected_bindings=changed_bindings,
        )
        self.assertEqual(
            stale_state.triages[-1]["assessment_dispositions"],
            [stale],
        )

        incomplete_stale = copy.deepcopy(stale_successor)
        incomplete_stale["assessment_dispositions"][0][
            "changed_binding_pointers"
        ] = ["/run_contract_sha256"]
        incomplete_stale["assessment_dispositions"][0]["disposition_id"] = (
            compute_assessment_disposition_id(
                incomplete_stale["assessment_dispositions"][0]
            )
        )
        incomplete_stale["triage_id"] = compute_human_triage_id(incomplete_stale)
        incomplete_directory = self.new_triage_dir()
        self.write_unchecked_triage_lineage(
            incomplete_directory,
            [genesis, incomplete_stale],
        )
        with self.assertRaisesRegex(PolicyViolation, "exact binding delta"):
            verify_human_triage_chain(
                incomplete_directory,
                str(incomplete_stale["triage_id"]),
                expected_bindings=changed_bindings,
            )

    def test_disposed_set_awaits_reassessment_and_retained_reopens_without_confirmation(
        self,
    ) -> None:
        blocked = self.build_plan()
        bindings = blocked["bindings"]
        assessment = self.locus_assessment(
            mechanism="One exact criticism can be dispositioned and later reopened."
        )
        genesis = self.human_triage(
            bindings,  # type: ignore[arg-type]
            assessments=[assessment],
            include_action=True,
        )
        directory = self.new_triage_dir()
        self.build_plan(triage=genesis, triage_dir=directory)
        evidence = self.calibration_disposition_evidence()
        defeated = self.assessment_disposition(
            assessment,
            assessment_origin_triage_id=str(genesis["triage_id"]),
            bindings=bindings,  # type: ignore[arg-type]
            disposition="DEFEATED",
            evidence_bindings=[evidence],
        )
        disposed = self.human_triage(
            bindings,  # type: ignore[arg-type]
            assessments=[assessment],
            assessment_dispositions=[defeated],
            include_action=False,
            sequence=2,
            previous_triage_id=str(genesis["triage_id"]),
            transition_kind="SAME_BINDINGS",
            transition_reason="Record a scoped defeat without promoting the model.",
        )
        disposed_plan = self.build_plan(
            triage=disposed,
            triage_dir=directory,
            head_triage_id=str(disposed["triage_id"]),
        )
        self.assertEqual(
            disposed_plan["route"],
            InquiryRoute.AWAITING_HUMAN_REASSESSMENT.value,
        )
        self.assertEqual(disposed_plan["live_locus_assessment_ids"], [])
        self.assertIsNone(disposed_plan["semantic_verdict"])
        self.assertEqual(disposed_plan["epistemic_status"], "UNRESOLVED")

        dropped_history = self.human_triage(
            bindings,  # type: ignore[arg-type]
            assessments=[assessment],
            assessment_dispositions=[],
            include_action=False,
            sequence=3,
            previous_triage_id=str(disposed["triage_id"]),
            transition_kind="SAME_BINDINGS",
            transition_reason="An invalid attempt to erase disposition history.",
        )
        dropped_directory = self.new_triage_dir()
        self.write_unchecked_triage_lineage(
            dropped_directory,
            [genesis, disposed, dropped_history],
        )
        with self.assertRaisesRegex(
            PolicyViolation,
            "dropped assessment dispositions",
        ):
            verify_human_triage_chain(
                dropped_directory,
                str(dropped_history["triage_id"]),
                expected_bindings=bindings,  # type: ignore[arg-type]
            )

        reopened_evidence = self.calibration_disposition_evidence()
        retained = self.assessment_disposition(
            assessment,
            assessment_origin_triage_id=str(genesis["triage_id"]),
            bindings=bindings,  # type: ignore[arg-type]
            disposition="RETAINED",
            evidence_bindings=[reopened_evidence],
            decision_sequence=2,
            previous_disposition_id=str(defeated["disposition_id"]),
        )
        reopened = self.human_triage(
            bindings,  # type: ignore[arg-type]
            assessments=[assessment],
            assessment_dispositions=[defeated, retained],
            include_action=False,
            sequence=3,
            previous_triage_id=str(disposed["triage_id"]),
            transition_kind="SAME_BINDINGS",
            transition_reason="Reopen the exact criticism without rewriting its record.",
        )
        reopened_plan = self.build_plan(
            triage=reopened,
            triage_dir=directory,
            head_triage_id=str(reopened["triage_id"]),
        )
        self.assertEqual(
            reopened_plan["route"],
            InquiryRoute.AWAITING_HUMAN_ACTION_SELECTION.value,
        )
        self.assertEqual(
            reopened_plan["live_locus_assessment_ids"],
            [assessment["assessment_id"]],
        )
        self.assertIsNone(reopened_plan["semantic_verdict"])

    def test_legacy_triage_validates_only_as_history_not_as_an_active_plan(self) -> None:
        blocked = self.build_plan()
        bindings = blocked["bindings"]
        legacy: dict[str, object] = {
            "$schema": "../schema/adaptive-inquiry.schema.json",
            "schema_version": "creib.semantic-forge.human-failure-triage.v1",
            "record_type": "human_failure_triage",
            "triage_id": "HT:" + "0" * 64,
            "created_on": "2026-09-03",
            "bindings": copy.deepcopy(bindings),
            "disposition": "UNRESOLVED",
            "uncertainty_location": "EXTERNAL_CRITICAL_INSTRUMENT",
            "reason": "Historical exclusive triage retained only for replay.",
            "scope": "The historical v1 record boundary.",
            "reviewer_kind": "HUMAN",
            "machine_generated": False,
            "epistemic_effect": "WORKFLOW_ROUTING_ONLY",
            "can_promote_model": False,
            "semantic_verdict": None,
        }
        legacy["triage_id"] = compute_human_triage_id(legacy)
        validate_human_triage(legacy, expected_bindings=bindings)  # type: ignore[arg-type]
        with self.assertRaisesRegex(PolicyViolation, "only human triage v2"):
            self.build_plan(triage=legacy)
        directory = self.new_triage_dir()
        with self.assertRaisesRegex(PolicyViolation, "only human triage v2"):
            publish_human_triage_against_inputs(
                directory,
                legacy,
                expected_head_triage_id=None,
                repo_root=ROOT,
                run_record_path=RUN_PATH,
                research_ledger_path=LEDGER_PATH,
            )
        self.assertEqual(list(directory.iterdir()), [])

    def test_legacy_events_replay_but_cannot_be_published_or_extended(self) -> None:
        plan = self.external_plan()
        current_question = plan["proposed_questions"][0]
        _legacy_question, legacy_event = self.legacy_question_and_event(
            current_question
        )
        validate_inquiry_event(
            legacy_event,
            research_ledger=self.ledger,
            expected_research_binding=self.ledger_binding,
        )
        triage_dir, head_triage_id = self._plan_context_by_case[
            str(plan["case_sha256"])
        ]

        fresh_events = self._test_root / "legacy-publication"
        fresh_events.mkdir()
        with self.assertRaisesRegex(PolicyViolation, "legacy inquiry events"):
            publish_inquiry_event(
                fresh_events,
                legacy_event,
                expected_head_event_id=None,
                plan=plan,
                repo_root=ROOT,
                run_record_path=RUN_PATH,
                research_ledger_path=LEDGER_PATH,
                triage_dir=triage_dir,
                research_ledger=self.ledger,
                research_binding=self.ledger_binding,
            )
        self.assertEqual(list(fresh_events.iterdir()), [])

        history = self._test_root / "legacy-replay"
        history.mkdir()
        self.write_unchecked_event_lineage(history, [legacy_event])
        replayed = verify_inquiry_chain(
            history,
            str(legacy_event["event_id"]),
            research_ledger=self.ledger,
            research_binding=self.ledger_binding,
        )
        self.assertEqual(replayed.events, (legacy_event,))
        replayed_v1 = verify_inquiry_chain(
            history,
            str(legacy_event["event_id"]),
            research_ledger=self.ledger,
            research_binding=self.ledger_binding,
            required_schema_version=LEGACY_EVENT_SCHEMA,
        )
        self.assertEqual(replayed_v1.events, (legacy_event,))

        before = {path.name: path.read_bytes() for path in history.iterdir()}
        with self.assertRaises(InquiryError) as active_replay:
            verify_inquiry_chain(
                history,
                str(legacy_event["event_id"]),
                research_ledger=self.ledger,
                research_binding=self.ledger_binding,
                required_schema_version=EVENT_SCHEMA,
            )
        self.assertEqual(
            active_replay.exception.error_code,
            "INQUIRY_EVENT_LINEAGE_VERSION_MISMATCH",
        )
        with self.assertRaises(InquiryError) as active_plan:
            self.build_plan(
                triage_dir=triage_dir,
                head_triage_id=head_triage_id,
                events_dir=history,
                head=str(legacy_event["event_id"]),
            )
        self.assertEqual(
            active_plan.exception.error_code,
            "INQUIRY_EVENT_LINEAGE_VERSION_MISMATCH",
        )
        self.assertEqual(
            {path.name: path.read_bytes() for path in history.iterdir()},
            before,
        )

    def test_forged_self_hashed_question_and_plan_cannot_claim_genesis(self) -> None:
        plan = self.external_plan()
        forged = copy.deepcopy(plan["proposed_questions"][0])
        forged["query"] += " Forged but internally rehashed instruction."
        forged["question_id"] = compute_question_id(forged)
        self.assertEqual(forged["case_sha256"], plan["case_sha256"])
        with self.assertRaisesRegex(
            PolicyViolation,
            "absent from the exact plan inventory",
        ):
            validate_inquiry_question_against_plan(forged, plan)

        forged_plan = copy.deepcopy(plan)
        forged_plan["proposed_questions"][0] = forged
        forged_plan["plan_id"] = compute_adaptive_inquiry_plan_id(forged_plan)
        validate_adaptive_inquiry_plan(forged_plan)
        forged_event = build_inquiry_event(
            sequence=1,
            previous_event_id=None,
            event_type="QUESTION_PROPOSED",
            occurred_on="2026-09-03",
            actor_kind="MACHINE",
            question=forged,
            from_state=None,
            reason_code="FORGED_CURRENT_QUESTION",
            reason="Attempt to claim genesis with an invented current-case question.",
            research_ledger=self.ledger,
            research_ledger_binding=self.ledger_binding,
        )
        triage_dir, _head_triage_id = self._plan_context_by_case[
            str(plan["case_sha256"])
        ]
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            with self.assertRaisesRegex(
                PolicyViolation,
                "differs from exact deterministic regeneration",
            ):
                publish_inquiry_event(
                    directory,
                    forged_event,
                    expected_head_event_id=None,
                    plan=forged_plan,
                    repo_root=ROOT,
                    run_record_path=RUN_PATH,
                    research_ledger_path=LEDGER_PATH,
                    triage_dir=triage_dir,
                    research_ledger=self.ledger,
                    research_binding=self.ledger_binding,
                )
            self.assertEqual(list(directory.iterdir()), [])

            exact = self.append(
                directory,
                plan["proposed_questions"][0],
                head=None,
                event_type="QUESTION_PROPOSED",
                actor="MACHINE",
            )
            self.assertTrue(
                (directory / f"{str(exact['event_id']).replace(':', '-')}.json").is_file()
            )
            self.assertTrue((directory / "NEXT-GENESIS.claim").is_file())

    def test_historical_case_question_survives_later_triage_rollover(self) -> None:
        blocked = self.build_plan()
        old_triage = self.human_triage(
            blocked["bindings"],  # type: ignore[arg-type]
            created_on="2026-09-03",
        )
        old_plan = self.build_plan(triage=old_triage)
        old_question = old_plan["proposed_questions"][0]
        triage_dir, old_head = self._plan_context_by_case[
            str(old_plan["case_sha256"])
        ]

        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            event = self.append(
                directory,
                old_question,
                head=None,
                event_type="QUESTION_PROPOSED",
                actor="MACHINE",
                occurred_on="2026-09-03",
            )
            new_triage = self.human_triage(
                blocked["bindings"],  # type: ignore[arg-type]
                assessments=old_triage["locus_assessments"],  # type: ignore[arg-type]
                created_on="2026-09-04",
                sequence=2,
                previous_triage_id=old_head,
                transition_kind="SAME_BINDINGS",
                transition_reason=(
                    "Keep the criticism and revise only the scheduled work instruction."
                ),
                action="Seek the same discriminator under a newly selected work instruction.",
            )
            current = self.build_plan(
                triage=new_triage,
                triage_dir=triage_dir,
                head_triage_id=str(new_triage["triage_id"]),
                events_dir=directory,
                head=event["event_id"],
            )
            self.assertNotEqual(old_plan["case_sha256"], current["case_sha256"])
            self.assertEqual(
                current["route"],
                InquiryRoute.EXTERNAL_RESEARCH_REQUIRED.value,
            )
            self.assertEqual(current["question_state"], {})
            self.assertEqual(len(current["proposed_questions"]), 4)
            self.assertNotEqual(
                {item["question_id"] for item in old_plan["proposed_questions"]},
                {item["question_id"] for item in current["proposed_questions"]},
            )

            current_question = current["proposed_questions"][0]
            current_event = self.append(
                directory,
                current_question,
                head=event["event_id"],
                event_type="QUESTION_PROPOSED",
                actor="MACHINE",
                occurred_on="2026-09-04",
            )
            live = self.build_plan(
                triage=new_triage,
                triage_dir=triage_dir,
                head_triage_id=str(new_triage["triage_id"]),
                events_dir=directory,
                head=current_event["event_id"],
            )
            self.assertEqual(live["route"], InquiryRoute.RESEARCH_IN_PROGRESS.value)
            self.assertIn(current_question["question_id"], live["question_state"])
            self.assertNotIn(old_question["question_id"], live["question_state"])

            plan_path = directory / "live-plan.json"
            plan_path.write_text(
                dumps_adaptive_inquiry_plan(live) + "\n",
                encoding="utf-8",
            )
            before = {path.name for path in directory.iterdir()}
            attempted = subprocess.run(
                [
                    sys.executable,
                    "tools/run_semantic_inquiry.py",
                    "append",
                    "--run-record",
                    str(RUN_PATH),
                    "--research-ledger",
                    str(LEDGER_PATH),
                    "--triage-dir",
                    str(triage_dir),
                    "--events-dir",
                    str(directory),
                    "--expected-head-event-id",
                    str(current_event["event_id"]),
                    "--plan",
                    str(plan_path),
                    "--question-id",
                    str(old_question["question_id"]),
                    "--event-type",
                    "QUESTION_ACTIVATED",
                    "--actor-kind",
                    "HUMAN",
                    "--occurred-on",
                    "2026-09-04",
                    "--reason-code",
                    "HISTORICAL_CASE",
                    "--reason",
                    "Attempt to reactivate a question from an earlier case.",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(attempted.returncode, 0)
            self.assertEqual(
                json.loads(attempted.stdout)["error_code"],
                "INQUIRY_QUESTION_NOT_ACTIONABLE",
            )
            self.assertEqual(before, {path.name for path in directory.iterdir()})

    def test_cli_route_gate_stops_other_questions_after_block_or_integration(
        self,
    ) -> None:
        plan = self.external_plan()
        first, second = plan["proposed_questions"][:2]
        triage_dir, head_triage_id = self._plan_context_by_case[
            str(plan["case_sha256"])
        ]

        def rejected_proposal(
            directory: Path,
            routed: dict[str, object],
            head: str,
            suffix: str,
        ) -> None:
            plan_path = directory / f"{suffix}-plan.json"
            plan_path.write_text(
                dumps_adaptive_inquiry_plan(routed) + "\n",
                encoding="utf-8",
            )
            before = {path.name for path in directory.iterdir()}
            attempted = subprocess.run(
                [
                    sys.executable,
                    "tools/run_semantic_inquiry.py",
                    "append",
                    "--run-record",
                    str(RUN_PATH),
                    "--research-ledger",
                    str(LEDGER_PATH),
                    "--triage-dir",
                    str(triage_dir),
                    "--events-dir",
                    str(directory),
                    "--expected-head-event-id",
                    head,
                    "--plan",
                    str(plan_path),
                    "--question-id",
                    str(second["question_id"]),
                    "--event-type",
                    "QUESTION_PROPOSED",
                    "--actor-kind",
                    "MACHINE",
                    "--occurred-on",
                    "2026-09-03",
                    "--reason-code",
                    suffix.upper(),
                    "--reason",
                    "Attempt to propose another question despite the exact route.",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(attempted.returncode, 0)
            self.assertEqual(
                json.loads(attempted.stdout)["error_code"],
                "INQUIRY_ROUTE_NOT_ACTIONABLE",
            )
            self.assertEqual(before, {path.name for path in directory.iterdir()})

        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            first_proposed = self.append(
                directory,
                first,
                head=None,
                event_type="QUESTION_PROPOSED",
                actor="MACHINE",
            )
            stale = self.append(
                directory,
                first,
                head=first_proposed["event_id"],
                event_type="MODEL_CHANGED",
                actor="MACHINE",
            )
            blocked = self.build_plan(
                triage_dir=triage_dir,
                head_triage_id=head_triage_id,
                events_dir=directory,
                head=stale["event_id"],
            )
            self.assertEqual(blocked["route"], InquiryRoute.POLICY_BLOCKED.value)
            rejected_proposal(
                directory,
                blocked,
                str(stale["event_id"]),
                "policy-blocked",
            )

        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            first_proposed = self.append(
                directory,
                first,
                head=None,
                event_type="QUESTION_PROPOSED",
                actor="MACHINE",
            )
            active = self.append(
                directory,
                first,
                head=first_proposed["event_id"],
                event_type="QUESTION_ACTIVATED",
                actor="HUMAN",
            )
            report = self.append(
                directory,
                first,
                head=active["event_id"],
                event_type="RESEARCH_CANDIDATE_RECORDED",
                actor="OPERATOR",
                research_entry=self.standalone_entry(first),
            )
            retained = self.append(
                directory,
                first,
                head=report["event_id"],
                event_type="HUMAN_CRITICISM_RETAINED",
                actor="HUMAN",
            )
            integration = self.build_plan(
                triage_dir=triage_dir,
                head_triage_id=head_triage_id,
                events_dir=directory,
                head=retained["event_id"],
            )
            self.assertEqual(
                integration["route"],
                InquiryRoute.INTERNAL_INTEGRATION_REQUIRED.value,
            )
            rejected_proposal(
                directory,
                integration,
                str(retained["event_id"]),
                "integration-required",
            )

    def test_event_chain_requires_a_head_for_any_published_inventory(self) -> None:
        unrelated = self._test_root / "event-inventory-unrelated"
        unrelated.mkdir()
        (unrelated / "README.md").write_text("operator notes\n", encoding="utf-8")
        empty = verify_inquiry_chain(
            unrelated,
            None,
            research_ledger=self.ledger,
            research_binding=self.ledger_binding,
            required_schema_version=EVENT_SCHEMA,
        )
        self.assertEqual(empty.events, ())

        for label, filename in (
            ("record", f"IE-{'a' * 64}.json"),
            ("claim", "NEXT-GENESIS.claim"),
        ):
            directory = self._test_root / f"event-inventory-{label}"
            directory.mkdir()
            (directory / filename).write_bytes(b"{}\n")
            with self.subTest(label=label), self.assertRaises(
                InquiryError
            ) as failure:
                verify_inquiry_chain(
                    directory,
                    None,
                    research_ledger=self.ledger,
                    research_binding=self.ledger_binding,
                    required_schema_version=EVENT_SCHEMA,
                )
            self.assertEqual(
                failure.exception.error_code,
                "INQUIRY_EVENT_HEAD_REQUIRED",
            )

        missing = self._test_root / "event-inventory-missing"
        with self.assertRaises(InquiryError) as missing_failure:
            verify_inquiry_chain(
                missing,
                None,
                research_ledger=self.ledger,
                research_binding=self.ledger_binding,
                required_schema_version=EVENT_SCHEMA,
            )
        self.assertEqual(
            missing_failure.exception.error_code,
            "INQUIRY_EVENT_PARENT_MISSING",
        )

    def test_event_chain_rejects_mixed_v1_v2_ancestry_in_both_orders(self) -> None:
        current_question = self.external_plan()["proposed_questions"][0]
        _legacy_question, legacy_genesis = self.legacy_question_and_event(
            current_question
        )
        v2_after_v1 = build_inquiry_event(
            sequence=2,
            previous_event_id=str(legacy_genesis["event_id"]),
            event_type="QUESTION_PROPOSED",
            occurred_on="2026-09-03",
            actor_kind="MACHINE",
            question=current_question,
            from_state=None,
            reason_code="MIXED_V2_AFTER_V1",
            reason="A v2 event must not extend a v1 historical lineage.",
            research_ledger=self.ledger,
            research_ledger_binding=self.ledger_binding,
        )

        v2_genesis = build_inquiry_event(
            sequence=1,
            previous_event_id=None,
            event_type="QUESTION_PROPOSED",
            occurred_on="2026-09-03",
            actor_kind="MACHINE",
            question=current_question,
            from_state=None,
            reason_code="MIXED_V2_GENESIS",
            reason="A v2 genesis used only to test forbidden mixed ancestry.",
            research_ledger=self.ledger,
            research_ledger_binding=self.ledger_binding,
        )
        _legacy_question, v1_after_v2 = self.legacy_question_and_event(
            current_question,
            sequence=2,
            previous_event_id=str(v2_genesis["event_id"]),
        )

        for label, events, head in (
            ("v1-then-v2", [legacy_genesis, v2_after_v1], v2_after_v1),
            ("v2-then-v1", [v2_genesis, v1_after_v2], v1_after_v2),
        ):
            directory = self._test_root / f"mixed-events-{label}"
            directory.mkdir()
            self.write_unchecked_event_lineage(directory, events)
            with self.subTest(label=label), self.assertRaises(
                InquiryError
            ) as failure:
                verify_inquiry_chain(
                    directory,
                    str(head["event_id"]),
                    research_ledger=self.ledger,
                    research_binding=self.ledger_binding,
                )
            self.assertEqual(
                failure.exception.error_code,
                "INQUIRY_EVENT_MIXED_VERSION_LINEAGE",
            )

    def test_event_chain_requires_complete_records_and_exact_successor_claims(
        self,
    ) -> None:
        question = self.external_plan()["proposed_questions"][0]
        proposed = build_inquiry_event(
            sequence=1,
            previous_event_id=None,
            event_type="QUESTION_PROPOSED",
            occurred_on="2026-09-03",
            actor_kind="MACHINE",
            question=question,
            from_state=None,
            reason_code="INVENTORY_PROPOSED",
            reason="Establish a complete v2 event lineage for inventory attacks.",
            research_ledger=self.ledger,
            research_ledger_binding=self.ledger_binding,
        )
        activated = build_inquiry_event(
            sequence=2,
            previous_event_id=str(proposed["event_id"]),
            event_type="QUESTION_ACTIVATED",
            occurred_on="2026-09-03",
            actor_kind="HUMAN",
            question=question,
            from_state="PROPOSED",
            reason_code="INVENTORY_ACTIVATED",
            reason="Activate the exact question without changing its record.",
            research_ledger=self.ledger,
            research_ledger_binding=self.ledger_binding,
        )
        sibling = build_inquiry_event(
            sequence=2,
            previous_event_id=str(proposed["event_id"]),
            event_type="QUESTION_ACTIVATED",
            occurred_on="2026-09-03",
            actor_kind="HUMAN",
            question=question,
            from_state="PROPOSED",
            reason_code="INVENTORY_FORK",
            reason="A competing successor that must remain an invalid fork.",
            research_ledger=self.ledger,
            research_ledger_binding=self.ledger_binding,
        )

        valid_dir = self._test_root / "complete-event-lineage"
        valid_dir.mkdir()
        self.write_unchecked_event_lineage(valid_dir, [proposed, activated])
        verified = verify_inquiry_chain(
            valid_dir,
            str(activated["event_id"]),
            research_ledger=self.ledger,
            research_binding=self.ledger_binding,
            required_schema_version=EVENT_SCHEMA,
        )
        self.assertEqual(verified.events, (proposed, activated))
        with self.assertRaises(InquiryError) as nonterminal:
            verify_inquiry_chain(
                valid_dir,
                str(proposed["event_id"]),
                research_ledger=self.ledger,
                research_binding=self.ledger_binding,
                required_schema_version=EVENT_SCHEMA,
            )
        self.assertEqual(
            nonterminal.exception.error_code,
            "INQUIRY_EVENT_ORPHAN_RECORD",
        )

        fork_dir = self._test_root / "forked-event-lineage"
        fork_dir.mkdir()
        self.write_unchecked_event_lineage(fork_dir, [proposed, activated])
        sibling_payload = canonical_bytes(sibling) + b"\n"
        sibling_path = fork_dir / f"{str(sibling['event_id']).replace(':', '-')}.json"
        sibling_path.write_bytes(sibling_payload)
        with self.assertRaises(InquiryError) as orphan:
            verify_inquiry_chain(
                fork_dir,
                str(activated["event_id"]),
                research_ledger=self.ledger,
                research_binding=self.ledger_binding,
                required_schema_version=EVENT_SCHEMA,
            )
        self.assertEqual(
            orphan.exception.error_code,
            "INQUIRY_EVENT_ORPHAN_RECORD",
        )

        claim_name = f"NEXT-{str(proposed['event_id']).removeprefix('IE:')}.claim"
        variants = (
            ("missing", "INQUIRY_EVENT_CLAIM_READ_FAILED"),
            ("changed", "INQUIRY_EVENT_CLAIM_MISMATCH"),
            ("extra", "INQUIRY_EVENT_NONTERMINAL_HEAD"),
        )
        for label, expected_code in variants:
            directory = self._test_root / f"event-claim-{label}"
            directory.mkdir()
            self.write_unchecked_event_lineage(directory, [proposed, activated])
            if label == "missing":
                (directory / claim_name).unlink()
            elif label == "changed":
                (directory / claim_name).write_bytes(sibling_payload)
            else:
                (directory / f"NEXT-{'f' * 64}.claim").write_bytes(
                    canonical_bytes(activated) + b"\n"
                )
            with self.subTest(label=label), self.assertRaises(
                InquiryError
            ) as failure:
                verify_inquiry_chain(
                    directory,
                    str(activated["event_id"]),
                    research_ledger=self.ledger,
                    research_binding=self.ledger_binding,
                    required_schema_version=EVENT_SCHEMA,
                )
            self.assertEqual(failure.exception.error_code, expected_code)

    def test_legal_question_lifecycle_replays_from_explicit_head(self) -> None:
        plan = self.external_plan()
        question = plan["proposed_questions"][0]
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            proposed = self.append(
                directory,
                question,
                head=None,
                event_type="QUESTION_PROPOSED",
                actor="MACHINE",
            )
            activated = self.append(
                directory,
                question,
                head=proposed["event_id"],
                event_type="QUESTION_ACTIVATED",
                actor="HUMAN",
            )
            state = verify_inquiry_chain(
                directory,
                activated["event_id"],
                research_ledger=self.ledger,
                research_binding=self.ledger_binding,
                required_schema_version=EVENT_SCHEMA,
            )
            self.assertEqual(len(state.events), 2)
            self.assertIs(
                state.question_states[question["question_id"]],
                QuestionState.ACTIVE,
            )

    def test_illegal_lifecycle_or_machine_human_disposition_fails(self) -> None:
        question = self.external_plan()["proposed_questions"][0]
        for sequence, previous in (
            (2, None),
            (1, "IE:" + "1" * 64),
        ):
            with self.subTest(sequence=sequence, previous=previous), self.assertRaises(
                PolicyViolation
            ):
                build_inquiry_event(
                    sequence=sequence,
                    previous_event_id=previous,
                    event_type="QUESTION_PROPOSED",
                    occurred_on="2026-09-03",
                    actor_kind="MACHINE",
                    question=question,
                    from_state=None,
                    reason_code="BAD_SEQUENCE_LINK",
                    reason="Sequence one and a null parent must occur together.",
                    research_ledger=self.ledger,
                    research_ledger_binding=self.ledger_binding,
                )
        with self.assertRaises(PolicyViolation):
            build_inquiry_event(
                sequence=1,
                previous_event_id=None,
                event_type="QUESTION_ACTIVATED",
                occurred_on="2026-09-03",
                actor_kind="HUMAN",
                question=question,
                from_state=None,
                reason_code="BAD_TRANSITION",
                reason="No proposal exists.",
                research_ledger=self.ledger,
                research_ledger_binding=self.ledger_binding,
            )
        with self.assertRaisesRegex(PolicyViolation, "requires actor_kind HUMAN"):
            build_inquiry_event(
                sequence=2,
                previous_event_id="IE:" + "1" * 64,
                event_type="HUMAN_MISFRAMED",
                occurred_on="2026-09-03",
                actor_kind="MACHINE",
                question=question,
                from_state="PROPOSED",
                reason_code="MACHINE_CANNOT_ADJUDICATE",
                reason="A machine cannot supply the human disposition.",
                research_ledger=self.ledger,
                research_ledger_binding=self.ledger_binding,
            )

    def test_hash_chain_detects_event_tampering(self) -> None:
        question = self.external_plan()["proposed_questions"][0]
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            event = self.append(
                directory,
                question,
                head=None,
                event_type="QUESTION_PROPOSED",
                actor="MACHINE",
            )
            event_path = directory / (event["event_id"].replace(":", "-") + ".json")
            tampered = json.loads(event_path.read_text(encoding="utf-8"))
            tampered["reason"] += " tampered"
            event_path.write_text(
                json.dumps(tampered, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(RecordError, "content-addressed ID mismatch"):
                verify_inquiry_chain(
                    directory,
                    event["event_id"],
                    research_ledger=self.ledger,
                    research_binding=self.ledger_binding,
                )

    def test_no_clobber_publication_reserves_each_parent_head_once(self) -> None:
        plan = self.external_plan()
        question = plan["proposed_questions"][0]
        triage_dir, head_triage_id = self._plan_context_by_case[
            str(plan["case_sha256"])
        ]
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            exact_plan = self.build_plan(
                triage_dir=triage_dir,
                head_triage_id=head_triage_id,
                events_dir=directory,
            )
            event = build_inquiry_event(
                sequence=1,
                previous_event_id=None,
                event_type="QUESTION_PROPOSED",
                occurred_on="2026-09-03",
                actor_kind="MACHINE",
                question=question,
                from_state=None,
                reason_code="FIRST_PUBLICATION",
                reason="Publish this exact planned question once.",
                research_ledger=self.ledger,
                research_ledger_binding=self.ledger_binding,
            )
            self.assertEqual(event["event_id"], compute_event_id(event))
            publish_inquiry_event(
                directory,
                event,
                expected_head_event_id=None,
                plan=exact_plan,
                repo_root=ROOT,
                run_record_path=RUN_PATH,
                research_ledger_path=LEDGER_PATH,
                triage_dir=triage_dir,
                research_ledger=self.ledger,
                research_binding=self.ledger_binding,
            )
            before = {
                path.name: path.read_bytes()
                for path in directory.iterdir()
            }
            repeated = publish_inquiry_event(
                directory,
                event,
                expected_head_event_id=None,
                plan=exact_plan,
                repo_root=ROOT,
                run_record_path=RUN_PATH,
                research_ledger_path=LEDGER_PATH,
                triage_dir=triage_dir,
                research_ledger=self.ledger,
                research_binding=self.ledger_binding,
            )
            self.assertEqual(repeated, directory / f"{str(event['event_id']).replace(':', '-')}.json")
            self.assertEqual(
                {
                    path.name: path.read_bytes()
                    for path in directory.iterdir()
                },
                before,
            )

    def test_event_publication_recovers_exact_claim_only_reservation(self) -> None:
        plan = self.external_plan()
        question = plan["proposed_questions"][0]
        triage_dir, head_triage_id = self._plan_context_by_case[
            str(plan["case_sha256"])
        ]
        directory = self._test_root / "event-claim-recovery"
        directory.mkdir()
        exact_plan = self.build_plan(
            triage_dir=triage_dir,
            head_triage_id=head_triage_id,
            events_dir=directory,
        )
        event = build_inquiry_event(
            sequence=1,
            previous_event_id=None,
            event_type="QUESTION_PROPOSED",
            occurred_on="2026-09-03",
            actor_kind="MACHINE",
            question=question,
            from_state=None,
            reason_code="RECOVER_RESERVED_EVENT",
            reason="Recover only this exact successor after an interrupted publication.",
            research_ledger=self.ledger,
            research_ledger_binding=self.ledger_binding,
        )
        payload = canonical_bytes(event) + b"\n"
        output = directory / f"{str(event['event_id']).replace(':', '-')}.json"
        claim = directory / "NEXT-GENESIS.claim"

        def publish(candidate: dict[str, object]) -> Path:
            return publish_inquiry_event(
                directory,
                candidate,
                expected_head_event_id=None,
                plan=exact_plan,
                repo_root=ROOT,
                run_record_path=RUN_PATH,
                research_ledger_path=LEDGER_PATH,
                triage_dir=triage_dir,
                research_ledger=self.ledger,
                research_binding=self.ledger_binding,
            )

        real_link = os.link
        link_calls = 0

        def fail_record_link(source: object, target: object) -> None:
            nonlocal link_calls
            link_calls += 1
            if link_calls == 2:
                raise OSError(errno.EIO, "simulated record-link interruption")
            real_link(source, target)  # type: ignore[arg-type]

        with mock.patch(
            "creib.forge.inquiry.os.link",
            side_effect=fail_record_link,
        ), self.assertRaises(InquiryError) as interrupted:
            publish(event)
        self.assertEqual(interrupted.exception.error_code, "INQUIRY_EVENT_WRITE_FAILED")
        self.assertEqual(claim.read_bytes(), payload)
        self.assertFalse(output.exists())
        self.assertEqual(list(directory.glob(".inquiry-event-*.tmp")), [])
        with self.assertRaises(InquiryError) as incomplete:
            verify_inquiry_chain(
                directory,
                None,
                research_ledger=self.ledger,
                research_binding=self.ledger_binding,
                required_schema_version=EVENT_SCHEMA,
            )
        self.assertEqual(incomplete.exception.error_code, "INQUIRY_EVENT_HEAD_REQUIRED")

        recovered = publish(event)
        self.assertEqual(recovered, output)
        self.assertTrue(os.path.samefile(claim, output))
        self.assertEqual(publish(event), output)

        sibling = build_inquiry_event(
            sequence=1,
            previous_event_id=None,
            event_type="QUESTION_PROPOSED",
            occurred_on="2026-09-03",
            actor_kind="MACHINE",
            question=question,
            from_state=None,
            reason_code="COMPETING_RESERVED_EVENT",
            reason="A different successor cannot replace the durable reservation.",
            research_ledger=self.ledger,
            research_ledger_binding=self.ledger_binding,
        )
        before = {path.name: path.read_bytes() for path in directory.iterdir()}
        with self.assertRaises(InquiryError) as stale:
            publish(sibling)
        self.assertEqual(stale.exception.error_code, "INQUIRY_EVENT_STALE_HEAD")
        self.assertEqual(
            {path.name: path.read_bytes() for path in directory.iterdir()},
            before,
        )

    def test_committed_event_retry_rechecks_original_parent_context(self) -> None:
        plan = self.external_plan()
        question = plan["proposed_questions"][0]
        triage_dir, head_triage_id = self._plan_context_by_case[
            str(plan["case_sha256"])
        ]
        directory = self._test_root / "committed-event-context"
        directory.mkdir()
        exact_plan = self.build_plan(
            triage_dir=triage_dir,
            head_triage_id=head_triage_id,
            events_dir=directory,
        )
        event = build_inquiry_event(
            sequence=1,
            previous_event_id=None,
            event_type="QUESTION_PROPOSED",
            occurred_on="2026-09-03",
            actor_kind="MACHINE",
            question=question,
            from_state=None,
            reason_code="COMMITTED_CONTEXT",
            reason="A committed successor still requires its original authorization.",
            research_ledger=self.ledger,
            research_ledger_binding=self.ledger_binding,
        )
        output = publish_inquiry_event(
            directory,
            event,
            expected_head_event_id=None,
            plan=exact_plan,
            repo_root=ROOT,
            run_record_path=RUN_PATH,
            research_ledger_path=LEDGER_PATH,
            triage_dir=triage_dir,
            research_ledger=self.ledger,
            research_binding=self.ledger_binding,
        )
        self.assertTrue(output.exists())
        before = {path.name: path.read_bytes() for path in directory.iterdir()}

        truncated_plan = copy.deepcopy(exact_plan)
        del truncated_plan["bindings"]
        wrong_plan = self.build_plan()
        missing = self._test_root / "nonexistent-event-context"
        attempts = (
            (
                "truncated-plan",
                truncated_plan,
                ROOT,
                RUN_PATH,
                LEDGER_PATH,
                triage_dir,
            ),
            (
                "wrong-plan",
                wrong_plan,
                ROOT,
                RUN_PATH,
                LEDGER_PATH,
                triage_dir,
            ),
            (
                "missing-repository",
                exact_plan,
                missing,
                RUN_PATH,
                LEDGER_PATH,
                triage_dir,
            ),
            (
                "missing-run",
                exact_plan,
                ROOT,
                missing / "run.json",
                LEDGER_PATH,
                triage_dir,
            ),
            (
                "missing-ledger",
                exact_plan,
                ROOT,
                RUN_PATH,
                missing / "ledger.json",
                triage_dir,
            ),
            (
                "missing-triage",
                exact_plan,
                ROOT,
                RUN_PATH,
                LEDGER_PATH,
                missing / "triage",
            ),
        )
        for label, candidate_plan, repo, run, ledger, candidate_triage in attempts:
            with self.subTest(label=label), mock.patch(
                "creib.forge.inquiry._fsync_directory"
            ) as retry_fsync, self.assertRaises(
                (InquiryError, PolicyViolation, RecordError)
            ):
                publish_inquiry_event(
                    directory,
                    event,
                    expected_head_event_id=None,
                    plan=candidate_plan,
                    repo_root=repo,
                    run_record_path=run,
                    research_ledger_path=ledger,
                    triage_dir=candidate_triage,
                    research_ledger=self.ledger,
                    research_binding=self.ledger_binding,
                )
            retry_fsync.assert_not_called()
            self.assertEqual(
                {path.name: path.read_bytes() for path in directory.iterdir()},
                before,
            )

    def test_event_retry_resyncs_complete_pair_without_relinking(self) -> None:
        plan = self.external_plan()
        question = plan["proposed_questions"][0]
        triage_dir, head_triage_id = self._plan_context_by_case[
            str(plan["case_sha256"])
        ]
        directory = self._test_root / "event-post-link-fsync"
        directory.mkdir()
        exact_plan = self.build_plan(
            triage_dir=triage_dir,
            head_triage_id=head_triage_id,
            events_dir=directory,
        )
        event = build_inquiry_event(
            sequence=1,
            previous_event_id=None,
            event_type="QUESTION_PROPOSED",
            occurred_on="2026-09-03",
            actor_kind="MACHINE",
            question=question,
            from_state=None,
            reason_code="POST_LINK_FSYNC",
            reason="Retry an exact pair whose final directory sync was interrupted.",
            research_ledger=self.ledger,
            research_ledger_binding=self.ledger_binding,
        )
        output = directory / f"{str(event['event_id']).replace(':', '-')}.json"
        claim = directory / "NEXT-GENESIS.claim"
        fsync_calls = 0

        def fail_second_directory_fsync(_directory: Path) -> None:
            nonlocal fsync_calls
            fsync_calls += 1
            if fsync_calls == 2:
                raise OSError(errno.EIO, "simulated post-link directory fsync failure")

        with mock.patch(
            "creib.forge.inquiry._fsync_directory",
            side_effect=fail_second_directory_fsync,
        ), self.assertRaises(InquiryError) as interrupted:
            publish_inquiry_event(
                directory,
                event,
                expected_head_event_id=None,
                plan=exact_plan,
                repo_root=ROOT,
                run_record_path=RUN_PATH,
                research_ledger_path=LEDGER_PATH,
                triage_dir=triage_dir,
                research_ledger=self.ledger,
                research_binding=self.ledger_binding,
            )
        self.assertEqual(fsync_calls, 2)
        self.assertEqual(interrupted.exception.error_code, "INQUIRY_EVENT_WRITE_FAILED")
        self.assertTrue(output.exists())
        self.assertTrue(os.path.samefile(claim, output))
        before = {path.name: path.read_bytes() for path in directory.iterdir()}

        with mock.patch(
            "creib.forge.inquiry.os.link",
            side_effect=AssertionError("a complete retry must not relink"),
        ) as link_mock, mock.patch(
            "creib.forge.inquiry._fsync_directory"
        ) as retry_fsync:
            recovered = publish_inquiry_event(
                directory,
                event,
                expected_head_event_id=None,
                plan=exact_plan,
                repo_root=ROOT,
                run_record_path=RUN_PATH,
                research_ledger_path=LEDGER_PATH,
                triage_dir=triage_dir,
                research_ledger=self.ledger,
                research_binding=self.ledger_binding,
            )
        self.assertEqual(recovered, output)
        link_mock.assert_not_called()
        retry_fsync.assert_called_once_with(directory)
        self.assertEqual(
            {path.name: path.read_bytes() for path in directory.iterdir()},
            before,
        )

    def test_non_genesis_event_claim_only_retry_rolls_forward(self) -> None:
        plan = self.external_plan()
        question = plan["proposed_questions"][0]
        triage_dir, head_triage_id = self._plan_context_by_case[
            str(plan["case_sha256"])
        ]
        directory = self._test_root / "non-genesis-event-recovery"
        directory.mkdir()
        genesis_plan = self.build_plan(
            triage_dir=triage_dir,
            head_triage_id=head_triage_id,
            events_dir=directory,
        )
        proposed = build_inquiry_event(
            sequence=1,
            previous_event_id=None,
            event_type="QUESTION_PROPOSED",
            occurred_on="2026-09-03",
            actor_kind="MACHINE",
            question=question,
            from_state=None,
            reason_code="PARENT_PROPOSAL",
            reason="Publish a valid parent before interrupting its child.",
            research_ledger=self.ledger,
            research_ledger_binding=self.ledger_binding,
        )
        publish_inquiry_event(
            directory,
            proposed,
            expected_head_event_id=None,
            plan=genesis_plan,
            repo_root=ROOT,
            run_record_path=RUN_PATH,
            research_ledger_path=LEDGER_PATH,
            triage_dir=triage_dir,
            research_ledger=self.ledger,
            research_binding=self.ledger_binding,
        )
        child_plan = self.build_plan(
            triage_dir=triage_dir,
            head_triage_id=head_triage_id,
            events_dir=directory,
            head=str(proposed["event_id"]),
        )
        activated = build_inquiry_event(
            sequence=2,
            previous_event_id=str(proposed["event_id"]),
            event_type="QUESTION_ACTIVATED",
            occurred_on="2026-09-03",
            actor_kind="HUMAN",
            question=question,
            from_state="PROPOSED",
            reason_code="CHILD_ACTIVATION",
            reason="Recover an exact non-genesis activation after claim reservation.",
            research_ledger=self.ledger,
            research_ledger_binding=self.ledger_binding,
        )
        output = directory / f"{str(activated['event_id']).replace(':', '-')}.json"
        claim = directory / (
            f"NEXT-{str(proposed['event_id']).removeprefix('IE:')}.claim"
        )
        real_link = os.link
        link_calls = 0

        def fail_record_link(source: object, target: object) -> None:
            nonlocal link_calls
            link_calls += 1
            if link_calls == 2:
                raise OSError(errno.EIO, "simulated child record-link interruption")
            real_link(source, target)  # type: ignore[arg-type]

        with mock.patch(
            "creib.forge.inquiry.os.link",
            side_effect=fail_record_link,
        ), self.assertRaises(InquiryError) as interrupted:
            publish_inquiry_event(
                directory,
                activated,
                expected_head_event_id=str(proposed["event_id"]),
                plan=child_plan,
                repo_root=ROOT,
                run_record_path=RUN_PATH,
                research_ledger_path=LEDGER_PATH,
                triage_dir=triage_dir,
                research_ledger=self.ledger,
                research_binding=self.ledger_binding,
            )
        self.assertEqual(interrupted.exception.error_code, "INQUIRY_EVENT_WRITE_FAILED")
        self.assertTrue(claim.exists())
        self.assertFalse(output.exists())

        recovered = publish_inquiry_event(
            directory,
            activated,
            expected_head_event_id=str(proposed["event_id"]),
            plan=child_plan,
            repo_root=ROOT,
            run_record_path=RUN_PATH,
            research_ledger_path=LEDGER_PATH,
            triage_dir=triage_dir,
            research_ledger=self.ledger,
            research_binding=self.ledger_binding,
        )
        self.assertEqual(recovered, output)
        verified = verify_inquiry_chain(
            directory,
            str(activated["event_id"]),
            research_ledger=self.ledger,
            research_binding=self.ledger_binding,
            required_schema_version=EVENT_SCHEMA,
        )
        self.assertEqual(verified.events, (proposed, activated))
        self.assertIs(
            verified.question_states[question["question_id"]],
            QuestionState.ACTIVE,
        )

    def test_event_publication_rejects_exact_question_state_mismatch(self) -> None:
        plan = self.external_plan()
        question = plan["proposed_questions"][0]
        triage_dir, head_triage_id = self._plan_context_by_case[
            str(plan["case_sha256"])
        ]
        directory = self._test_root / "event-state-mismatch"
        directory.mkdir()
        proposed = self.append(
            directory,
            question,
            head=None,
            event_type="QUESTION_PROPOSED",
            actor="MACHINE",
        )
        exact_plan = self.build_plan(
            triage_dir=triage_dir,
            head_triage_id=head_triage_id,
            events_dir=directory,
            head=str(proposed["event_id"]),
        )
        mismatched = build_inquiry_event(
            sequence=2,
            previous_event_id=str(proposed["event_id"]),
            event_type="HUMAN_MISFRAMED",
            occurred_on="2026-09-03",
            actor_kind="HUMAN",
            question=question,
            from_state="ACTIVE",
            reason_code="WRONG_EXACT_QUESTION_STATE",
            reason="This transition is legal in general but not from the replayed state.",
            research_ledger=self.ledger,
            research_ledger_binding=self.ledger_binding,
        )
        before = {path.name: path.read_bytes() for path in directory.iterdir()}
        with self.assertRaises(InquiryError) as failure:
            publish_inquiry_event(
                directory,
                mismatched,
                expected_head_event_id=str(proposed["event_id"]),
                plan=exact_plan,
                repo_root=ROOT,
                run_record_path=RUN_PATH,
                research_ledger_path=LEDGER_PATH,
                triage_dir=triage_dir,
                research_ledger=self.ledger,
                research_binding=self.ledger_binding,
            )
        self.assertEqual(failure.exception.error_code, "INQUIRY_EVENT_STATE_MISMATCH")
        self.assertEqual(
            {path.name: path.read_bytes() for path in directory.iterdir()},
            before,
        )

    def test_one_concrete_report_routes_to_human_not_confirmation(self) -> None:
        plan = self.external_plan()
        question = plan["proposed_questions"][0]
        entry = self.standalone_entry(question)
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            proposed = self.append(
                directory,
                question,
                head=None,
                event_type="QUESTION_PROPOSED",
                actor="MACHINE",
            )
            active = self.append(
                directory,
                question,
                head=proposed["event_id"],
                event_type="QUESTION_ACTIVATED",
                actor="HUMAN",
            )
            report = self.append(
                directory,
                question,
                head=active["event_id"],
                event_type="RESEARCH_CANDIDATE_RECORDED",
                actor="OPERATOR",
                research_entry=entry,
            )
            routed = self.build_plan(
                triage=plan["triage"],  # type: ignore[arg-type]
                events_dir=directory,
                head=report["event_id"],
            )
            self.assertEqual(routed["route"], InquiryRoute.AWAITING_HUMAN_REVIEW.value)
            self.assertIsNone(routed["semantic_verdict"])
            self.assertEqual(routed["epistemic_status"], "UNRESOLVED")

    def test_agreeing_reports_cannot_advance_beyond_awaiting_human_review(self) -> None:
        plan = self.external_plan()
        questions = plan["proposed_questions"][:2]
        routes: list[str] = []
        verdicts: list[object] = []
        for index, question in enumerate(questions):
            temporary = tempfile.TemporaryDirectory()
            self.addCleanup(temporary.cleanup)
            directory = Path(temporary.name)
            proposed = self.append(
                directory,
                question,
                head=None,
                event_type="QUESTION_PROPOSED",
                actor="MACHINE",
            )
            active = self.append(
                directory,
                question,
                head=proposed["event_id"],
                event_type="QUESTION_ACTIVATED",
                actor="HUMAN",
            )
            report = self.append(
                directory,
                question,
                head=active["event_id"],
                event_type="RESEARCH_CANDIDATE_RECORDED",
                actor="OPERATOR",
                research_entry=self.standalone_entry(
                    question,
                    seed_index=index,
                    suffix=f"AGREE-{index + 1:03d}",
                ),
            )
            triage_dir, head_triage_id = self._plan_context_by_case[
                str(plan["case_sha256"])
            ]
            routed = self.build_plan(
                triage_dir=triage_dir,
                head_triage_id=head_triage_id,
                events_dir=directory,
                head=report["event_id"],
            )
            routes.append(str(routed["route"]))
            verdicts.append(routed["semantic_verdict"])

        self.assertEqual(
            routes,
            [InquiryRoute.AWAITING_HUMAN_REVIEW.value] * len(questions),
        )
        self.assertEqual(verdicts, [None] * len(questions))

    def test_unattested_protocol_exhaustion_cannot_retire_a_question(self) -> None:
        plan = self.external_plan()
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            question = plan["proposed_questions"][0]
            proposed = self.append(
                directory,
                question,
                head=None,
                event_type="QUESTION_PROPOSED",
                actor="MACHINE",
            )
            active = self.append(
                directory,
                question,
                head=proposed["event_id"],
                event_type="QUESTION_ACTIVATED",
                actor="HUMAN",
            )
            with self.assertRaisesRegex(ValueError, "unknown inquiry event type"):
                self.append(
                    directory,
                    question,
                    head=active["event_id"],
                    event_type="PROTOCOL_EXHAUSTED",
                    actor="OPERATOR",
                )
            routed = self.build_plan(
                triage=plan["triage"],  # type: ignore[arg-type]
                events_dir=directory,
                head=active["event_id"],
            )
            self.assertEqual(
                routed["route"],
                InquiryRoute.RESEARCH_IN_PROGRESS.value,
            )
            self.assertEqual(routed["epistemic_status"], "UNRESOLVED")
            self.assertIsNone(routed["semantic_verdict"])

    def test_human_terminal_dispositions_can_end_the_current_question_set(self) -> None:
        plan = self.external_plan()
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            head: str | None = None
            for question in plan["proposed_questions"]:
                proposed = self.append(
                    directory,
                    question,
                    head=head,
                    event_type="QUESTION_PROPOSED",
                    actor="MACHINE",
                )
                retired = self.append(
                    directory,
                    question,
                    head=proposed["event_id"],
                    event_type="HUMAN_MISFRAMED",
                    actor="HUMAN",
                )
                head = retired["event_id"]
            routed = self.build_plan(
                triage=plan["triage"],  # type: ignore[arg-type]
                events_dir=directory,
                head=head,
            )
            self.assertEqual(
                routed["route"],
                InquiryRoute.NO_NEW_RESEARCH_UNDER_CURRENT_PROTOCOL.value,
            )
            self.assertEqual(routed["epistemic_status"], "UNRESOLVED")
            self.assertIsNone(routed["semantic_verdict"])
            self.assertIn("no support", routed["route_reason"])

    def test_research_entry_must_target_the_exact_active_question(self) -> None:
        question = self.external_plan()["proposed_questions"][0]
        unrelated = {
            "schema_version": "creib.semantic-forge.event-research-entry.v2",
            "question_binding": self.question_binding(question),
            "source_report": self.ledger.entries[0].to_dict(),
        }
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            proposed = self.append(
                directory,
                question,
                head=None,
                event_type="QUESTION_PROPOSED",
                actor="MACHINE",
            )
            active = self.append(
                directory,
                question,
                head=proposed["event_id"],
                event_type="QUESTION_ACTIVATED",
                actor="HUMAN",
            )
            with self.assertRaisesRegex(PolicyViolation, "exact active question"):
                self.append(
                    directory,
                    question,
                    head=active["event_id"],
                    event_type="RESEARCH_CANDIDATE_RECORDED",
                    actor="OPERATOR",
                    research_entry=unrelated,
                )

    def test_event_research_entry_cannot_cross_bind_same_text_question(self) -> None:
        question = self.external_plan()["proposed_questions"][0]
        other_question = copy.deepcopy(question)
        other_question["case_sha256"] = "sha256:" + "0" * 64
        other_question["question_id"] = compute_question_id(other_question)
        self.assertNotEqual(other_question["question_id"], question["question_id"])
        self.assertEqual(other_question["query"], question["query"])
        self.assertEqual(
            other_question["falsifier_condition"],
            question["falsifier_condition"],
        )

        with self.assertRaisesRegex(PolicyViolation, "exact v2 question binding"):
            build_inquiry_event(
                sequence=3,
                previous_event_id="IE:" + "1" * 64,
                event_type="RESEARCH_CANDIDATE_RECORDED",
                occurred_on="2026-09-03",
                actor_kind="OPERATOR",
                question=other_question,
                from_state="ACTIVE",
                reason_code="CROSS_BOUND_REPORT",
                reason="A report bound to a textually identical other question.",
                research_ledger=self.ledger,
                research_ledger_binding=self.ledger_binding,
                research_entry=self.standalone_entry(question),
            )

    def test_event_source_entry_ids_share_the_bound_ledger_namespace(self) -> None:
        question = self.external_plan()["proposed_questions"][0]
        bound_entry = self.ledger.entries[0].to_dict()
        collision = self.standalone_entry(question, suffix="BOUND-ID-COLLISION")
        collision_report = collision["source_report"]
        collision_report["entry_id"] = bound_entry["entry_id"]
        unsigned_collision = copy.deepcopy(collision_report)
        unsigned_collision.pop("entry_sha256")
        collision_report["entry_sha256"] = domain_digest(
            "creib.semantic-forge.external-source-entry.v2",
            unsigned_collision,
        ).removeprefix("sha256:")
        with self.assertRaisesRegex(
            PolicyViolation,
            "bound research-ledger entry ID for different content",
        ):
            build_inquiry_event(
                sequence=3,
                previous_event_id="IE:" + "1" * 64,
                event_type="RESEARCH_CANDIDATE_RECORDED",
                occurred_on="2026-09-03",
                actor_kind="OPERATOR",
                question=question,
                from_state="ACTIVE",
                reason_code="BOUND_ENTRY_ID_COLLISION",
                reason="Attempt to reuse a bound entry ID for a different report.",
                research_ledger=self.ledger,
                research_ledger_binding=self.ledger_binding,
                research_entry=collision,
            )

        custom_record = load_strict(LEDGER_PATH)
        exact_report = copy.deepcopy(collision_report)
        custom_record["entries"][0] = exact_report
        rehash_research_ledger_after_entry_change(custom_record)
        custom_ledger = parse_research_ledger(custom_record)
        custom_raw = canonical_bytes(custom_record) + b"\n"
        custom_binding = {
            "ledger_id": custom_ledger.ledger_id,
            "created_on": custom_ledger.created_on,
            "as_of_date": custom_ledger.as_of_date,
            "file_sha256": bytes_digest(custom_raw),
            "record_sha256": domain_digest(
                custom_ledger.schema_version,
                custom_ledger.to_dict(),
            ),
        }
        exact_envelope = {
            "schema_version": "creib.semantic-forge.event-research-entry.v2",
            "question_binding": self.question_binding(question),
            "source_report": custom_ledger.entries[0].to_dict(),
        }
        accepted = build_inquiry_event(
            sequence=3,
            previous_event_id="IE:" + "1" * 64,
            event_type="RESEARCH_CANDIDATE_RECORDED",
            occurred_on="2026-09-03",
            actor_kind="OPERATOR",
            question=question,
            from_state="ACTIVE",
            reason_code="EXACT_BOUND_ENTRY_REUSE",
            reason="Reuse the exact bound report under the same entry ID.",
            research_ledger=custom_ledger,
            research_ledger_binding=custom_binding,
            research_entry=exact_envelope,
        )
        self.assertEqual(
            accepted["research_entry"]["source_report"],
            custom_ledger.entries[0].to_dict(),
        )

    def test_event_research_entry_requires_every_exact_question_binding(self) -> None:
        question = self.external_plan()["proposed_questions"][0]
        replacements = {
            "question_id": "IQ:" + "0" * 64,
            "case_sha256": "sha256:" + "0" * 64,
            "triage_id": "HT:" + "0" * 64,
            "action_id": "NA:" + "0" * 64,
            "attack_target_id": "AT:" + "0" * 64,
        }
        for field, replacement in replacements.items():
            entry = self.standalone_entry(
                question,
                suffix=f"BAD-{field.upper().replace('_', '-')}",
            )
            self.assertNotEqual(entry["question_binding"][field], replacement)
            entry["question_binding"][field] = replacement
            with self.subTest(field=field), self.assertRaisesRegex(
                PolicyViolation,
                "exact v2 question binding",
            ):
                build_inquiry_event(
                    sequence=3,
                    previous_event_id="IE:" + "1" * 64,
                    event_type="RESEARCH_CANDIDATE_RECORDED",
                    occurred_on="2026-09-03",
                    actor_kind="OPERATOR",
                    question=question,
                    from_state="ACTIVE",
                    reason_code="MISMATCHED_BINDING",
                    reason=f"The event entry changes its {field} binding.",
                    research_ledger=self.ledger,
                    research_ledger_binding=self.ledger_binding,
                    research_entry=entry,
                )

    def test_event_entry_digest_binds_same_report_to_exact_question(self) -> None:
        question = self.external_plan()["proposed_questions"][0]
        other_question = copy.deepcopy(question)
        other_question["case_sha256"] = "sha256:" + "0" * 64
        other_question["question_id"] = compute_question_id(other_question)
        first_entry = self.standalone_entry(question, suffix="SHARED-REPORT")
        second_entry = copy.deepcopy(first_entry)
        second_entry["question_binding"] = self.question_binding(other_question)

        events = []
        for bound_question, entry in (
            (question, first_entry),
            (other_question, second_entry),
        ):
            events.append(
                build_inquiry_event(
                    sequence=3,
                    previous_event_id="IE:" + "1" * 64,
                    event_type="RESEARCH_CANDIDATE_RECORDED",
                    occurred_on="2026-09-03",
                    actor_kind="OPERATOR",
                    question=bound_question,
                    from_state="ACTIVE",
                    reason_code="EXACT_REPORT_BINDING",
                    reason="Bind one source report to this exact question.",
                    research_ledger=self.ledger,
                    research_ledger_binding=self.ledger_binding,
                    research_entry=entry,
                )
            )
        self.assertEqual(
            events[0]["research_entry"]["source_report"],
            events[1]["research_entry"]["source_report"],
        )
        self.assertNotEqual(
            events[0]["research_entry_sha256"],
            events[1]["research_entry_sha256"],
        )

    def test_v2_research_event_schema_requires_strict_entry_envelope(self) -> None:
        question = self.external_plan()["proposed_questions"][0]
        valid = build_inquiry_event(
            sequence=3,
            previous_event_id="IE:" + "1" * 64,
            event_type="RESEARCH_CANDIDATE_RECORDED",
            occurred_on="2026-09-03",
            actor_kind="OPERATOR",
            question=question,
            from_state="ACTIVE",
            reason_code="STRICT_ENVELOPE",
            reason="Exercise the strict event-time entry envelope.",
            research_ledger=self.ledger,
            research_ledger_binding=self.ledger_binding,
            research_entry=self.standalone_entry(question),
        )
        malformed: list[dict[str, object]] = []

        raw_report = copy.deepcopy(valid)
        raw_report["research_entry"] = raw_report["research_entry"]["source_report"]
        malformed.append(raw_report)

        missing_binding = copy.deepcopy(valid)
        missing_binding["research_entry"]["question_binding"].pop("case_sha256")
        malformed.append(missing_binding)

        extra_binding = copy.deepcopy(valid)
        extra_binding["research_entry"]["question_binding"]["confidence"] = 1
        malformed.append(extra_binding)

        absent_entry = copy.deepcopy(valid)
        absent_entry["research_entry"] = None
        absent_entry["research_entry_sha256"] = None
        malformed.append(absent_entry)

        proposal = build_inquiry_event(
            sequence=1,
            previous_event_id=None,
            event_type="QUESTION_PROPOSED",
            occurred_on="2026-09-03",
            actor_kind="MACHINE",
            question=question,
            from_state=None,
            reason_code="NO_REPORT_ON_PROPOSAL",
            reason="A non-research event cannot carry an entry envelope.",
            research_ledger=self.ledger,
            research_ledger_binding=self.ledger_binding,
        )
        entry_on_proposal = copy.deepcopy(proposal)
        entry_on_proposal["research_entry"] = self.standalone_entry(question)
        entry_on_proposal["research_entry_sha256"] = valid[
            "research_entry_sha256"
        ]
        malformed.append(entry_on_proposal)

        for index, event in enumerate(malformed):
            event["event_id"] = compute_event_id(event)
            with self.subTest(case=index), self.assertRaises(RecordError):
                validate_inquiry_event(
                    event,
                    research_ledger=self.ledger,
                    expected_research_binding=self.ledger_binding,
                )

    def test_v2_research_event_rejects_raw_legacy_source_report(self) -> None:
        question = self.external_plan()["proposed_questions"][0]
        with self.assertRaisesRegex(RecordError, "envelope|schema_version"):
            build_inquiry_event(
                sequence=3,
                previous_event_id="IE:" + "1" * 64,
                event_type="RESEARCH_CANDIDATE_RECORDED",
                occurred_on="2026-09-03",
                actor_kind="OPERATOR",
                question=question,
                from_state="ACTIVE",
                reason_code="RAW_REPORT",
                reason="A v2 event cannot use the legacy raw report shape.",
                research_ledger=self.ledger,
                research_ledger_binding=self.ledger_binding,
                research_entry=self.standalone_source_report(question),
            )

    def test_v1_raw_research_entry_still_validates_and_replays(self) -> None:
        question = self.external_plan()["proposed_questions"][0]
        legacy_question, proposed = self.legacy_question_and_event(question)

        active = copy.deepcopy(proposed)
        active.update(
            {
                "sequence": 2,
                "previous_event_id": proposed["event_id"],
                "event_type": "QUESTION_ACTIVATED",
                "actor_kind": "HUMAN",
                "from_state": "PROPOSED",
                "to_state": "ACTIVE",
                "reason_code": "HISTORICAL_V1_ACTIVATED",
                "reason": "Historical v1 question activation retained for replay.",
            }
        )
        active["event_id"] = compute_event_id(active)

        source_report = self.standalone_source_report(
            legacy_question,
            suffix="LEGACY-V1",
        )
        research = copy.deepcopy(active)
        research.update(
            {
                "sequence": 3,
                "previous_event_id": active["event_id"],
                "event_type": "RESEARCH_CANDIDATE_RECORDED",
                "actor_kind": "OPERATOR",
                "from_state": "ACTIVE",
                "to_state": "AWAITING_HUMAN_REVIEW",
                "reason_code": "HISTORICAL_V1_REPORT",
                "reason": "Historical v1 raw source report retained for replay.",
                "research_entry": source_report,
                "research_entry_sha256": domain_digest(
                    "creib.semantic-forge.inquiry-event-entry-binding.v1",
                    source_report,
                ),
            }
        )
        research["event_id"] = compute_event_id(research)

        for event in (proposed, active, research):
            validate_inquiry_event(
                event,
                research_ledger=self.ledger,
                expected_research_binding=self.ledger_binding,
            )
        history = self._test_root / "legacy-v1-research-replay"
        history.mkdir()
        self.write_unchecked_event_lineage(history, [proposed, active, research])
        replayed = verify_inquiry_chain(
            history,
            str(research["event_id"]),
            research_ledger=self.ledger,
            research_binding=self.ledger_binding,
        )
        self.assertEqual(replayed.events, (proposed, active, research))
        self.assertEqual(
            replayed.question_states[legacy_question["question_id"]],
            QuestionState.AWAITING_HUMAN_REVIEW,
        )

    def test_standalone_entry_must_pass_its_own_content_digest(self) -> None:
        question = self.external_plan()["proposed_questions"][0]
        changed = self.standalone_entry(question)
        changed["source_report"]["title"] += " altered after hashing"
        with self.assertRaisesRegex(RecordError, "entry.entry_sha256 mismatch"):
            build_inquiry_event(
                sequence=3,
                previous_event_id="IE:" + "1" * 64,
                event_type="RESEARCH_CANDIDATE_RECORDED",
                occurred_on="2026-09-03",
                actor_kind="OPERATOR",
                question=question,
                from_state="ACTIVE",
                reason_code="ALTERED_REPORT",
                reason="Attempt to attach a report changed after hashing.",
                research_ledger=self.ledger,
                research_ledger_binding=self.ledger_binding,
                research_entry=changed,
            )

    def test_standalone_entry_inherits_bound_provider_policy(self) -> None:
        question = self.external_plan()["proposed_questions"][0]
        seed_index = next(
            index
            for index, item in enumerate(self.ledger.entries)
            if item.discovery.route_kind.value == "default_contemporary_discovery"
        )
        changed = self.standalone_entry(
            question,
            seed_index=seed_index,
            suffix="WRONG-PROVIDER",
        )
        source_report = changed["source_report"]
        source_report["discovery"]["provider"] = "ModernIndex"
        source_report["discovery"]["route_locator"] = (
            "https://modern-index.example/result"
        )
        unsigned = copy.deepcopy(source_report)
        unsigned.pop("entry_sha256")
        source_report["entry_sha256"] = domain_digest(
            "creib.semantic-forge.external-source-entry.v2",
            unsigned,
        ).removeprefix("sha256:")
        with self.assertRaisesRegex(PolicyViolation, "configured provider"):
            build_inquiry_event(
                sequence=3,
                previous_event_id="IE:" + "1" * 64,
                event_type="RESEARCH_CANDIDATE_RECORDED",
                occurred_on="2026-09-03",
                actor_kind="OPERATOR",
                question=question,
                from_state="ACTIVE",
                reason_code="WRONG_PROVIDER",
                reason="A source snapshot using a different default provider.",
                research_ledger=self.ledger,
                research_ledger_binding=self.ledger_binding,
                research_entry=changed,
            )

    def test_event_date_cannot_move_backwards(self) -> None:
        initial_plan = self.external_plan()
        question = initial_plan["proposed_questions"][0]
        triage_dir, head_triage_id = self._plan_context_by_case[
            str(initial_plan["case_sha256"])
        ]
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            proposed = self.append(
                directory,
                question,
                head=None,
                event_type="QUESTION_PROPOSED",
                actor="MACHINE",
                occurred_on="2026-09-04",
            )
            state = verify_inquiry_chain(
                directory,
                proposed["event_id"],
                research_ledger=self.ledger,
                research_binding=self.ledger_binding,
            )
            regressed = build_inquiry_event(
                sequence=len(state.events) + 1,
                previous_event_id=proposed["event_id"],
                event_type="QUESTION_ACTIVATED",
                occurred_on="2026-09-03",
                actor_kind="HUMAN",
                question=question,
                from_state="PROPOSED",
                reason_code="BACKDATED",
                reason="A deliberately backdated transition.",
                research_ledger=self.ledger,
                research_ledger_binding=self.ledger_binding,
            )
            current_plan = self.build_plan(
                triage_dir=triage_dir,
                head_triage_id=head_triage_id,
                events_dir=directory,
                head=str(proposed["event_id"]),
            )
            with self.assertRaisesRegex(InquiryError, "precedes its selected parent"):
                publish_inquiry_event(
                    directory,
                    regressed,
                    expected_head_event_id=proposed["event_id"],
                    plan=current_plan,
                    repo_root=ROOT,
                    run_record_path=RUN_PATH,
                    research_ledger_path=LEDGER_PATH,
                    triage_dir=triage_dir,
                    research_ledger=self.ledger,
                    research_binding=self.ledger_binding,
                )

    def test_serialization_round_trips_without_floats(self) -> None:
        plan = self.external_plan()
        serialized = dumps_adaptive_inquiry_plan(plan)
        self.assertEqual(loads_adaptive_inquiry_plan(serialized), plan)

        def walk(value: object) -> None:
            self.assertNotIsInstance(value, float)
            if isinstance(value, dict):
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)

        walk(plan)

    def test_generic_plan_validator_reports_intrinsic_scope_only(self) -> None:
        plan = self.external_plan()
        with tempfile.TemporaryDirectory() as temporary:
            plan_path = Path(temporary) / "plan.json"
            plan_path.write_text(
                dumps_adaptive_inquiry_plan(plan) + "\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    "tools/validate_semantic_forge.py",
                    "--instance",
                    str(plan_path),
                    "--schema",
                    "adaptive-inquiry-v2.schema.json",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        output = json.loads(result.stdout)
        self.assertEqual(
            output["validation_status"],
            "SCHEMA_AND_INTRINSIC_RUNTIME_VALID",
        )
        self.assertEqual(output["runtime_contract_scope"], "INTRINSIC_RECORD_ONLY")

    def test_event_derived_plan_state_and_history_block_require_a_head(self) -> None:
        plan = self.external_plan()
        question = plan["proposed_questions"][0]

        active_without_head = copy.deepcopy(plan)
        active_without_head["route"] = InquiryRoute.RESEARCH_IN_PROGRESS.value
        active_without_head["route_reason"] = (
            "At least one exact current attack question is already proposed or active."
        )
        active_without_head["state_head_event_id"] = None
        active_without_head["proposed_questions"] = []
        active_without_head["question_state"] = {
            question["question_id"]: QuestionState.ACTIVE.value
        }
        active_without_head["plan_id"] = compute_adaptive_inquiry_plan_id(
            active_without_head
        )
        with self.assertRaisesRegex(
            (RecordError, PolicyViolation),
            "state_head_event_id|event-derived question state|schema",
        ):
            validate_adaptive_inquiry_plan(active_without_head)
        with self.assertRaisesRegex(
            (RecordError, PolicyViolation),
            "state_head_event_id|event-derived question state|schema",
        ):
            validate_inquiry_question_against_plan(
                question,
                active_without_head,
            )

        blocked_without_head = copy.deepcopy(plan)
        blocked_without_head["route"] = InquiryRoute.POLICY_BLOCKED.value
        blocked_without_head["route_reason"] = (
            "Event history changed a bound question."
        )
        blocked_without_head["state_head_event_id"] = None
        blocked_without_head["proposed_questions"] = []
        blocked_without_head["question_state"] = {}
        blocked_without_head["plan_id"] = compute_adaptive_inquiry_plan_id(
            blocked_without_head
        )
        with self.assertRaisesRegex(
            (RecordError, PolicyViolation),
            "state_head_event_id|event-history integrity block|schema",
        ):
            validate_adaptive_inquiry_plan(blocked_without_head)

    def test_fake_plan_event_head_is_only_an_intrinsic_reference(self) -> None:
        plan = self.external_plan()
        question = plan["proposed_questions"][0]
        forged = copy.deepcopy(plan)
        forged["route"] = InquiryRoute.RESEARCH_IN_PROGRESS.value
        forged["route_reason"] = (
            "At least one exact current attack question is already proposed or active."
        )
        forged["state_head_event_id"] = "IE:" + "f" * 64
        forged["proposed_questions"] = []
        forged["question_state"] = {
            question["question_id"]: QuestionState.ACTIVE.value
        }
        forged["plan_id"] = compute_adaptive_inquiry_plan_id(forged)

        validate_adaptive_inquiry_plan(forged)
        validate_inquiry_question_against_plan(question, forged)
        triage_dir, _head_triage_id = self._plan_context_by_case[
            str(plan["case_sha256"])
        ]
        empty_events = self._test_root / "empty-events-for-fake-head"
        empty_events.mkdir()
        with self.assertRaises(InquiryError):
            validate_adaptive_inquiry_plan_against_inputs(
                forged,
                repo_root=ROOT,
                run_record_path=RUN_PATH,
                research_ledger_path=LEDGER_PATH,
                triage_dir=triage_dir,
                events_dir=empty_events,
            )

    def test_real_replayed_plan_with_event_head_validates_contextually(self) -> None:
        plan = self.external_plan()
        question = plan["proposed_questions"][0]
        proposed = build_inquiry_event(
            sequence=1,
            previous_event_id=None,
            event_type="QUESTION_PROPOSED",
            occurred_on="2026-09-03",
            actor_kind="MACHINE",
            question=question,
            from_state=None,
            reason_code="REAL_REPLAY_HEAD",
            reason="Create an exact event head for contextual plan regeneration.",
            research_ledger=self.ledger,
            research_ledger_binding=self.ledger_binding,
        )
        events_dir = self._test_root / "real-replay-head"
        events_dir.mkdir()
        self.write_unchecked_event_lineage(events_dir, [proposed])
        triage_dir, head_triage_id = self._plan_context_by_case[
            str(plan["case_sha256"])
        ]
        replayed = self.build_plan(
            triage_dir=triage_dir,
            head_triage_id=head_triage_id,
            events_dir=events_dir,
            head=str(proposed["event_id"]),
        )

        self.assertEqual(replayed["state_head_event_id"], proposed["event_id"])
        validate_adaptive_inquiry_plan(replayed)
        validate_inquiry_question_against_plan(question, replayed)
        validate_adaptive_inquiry_plan_against_inputs(
            replayed,
            repo_root=ROOT,
            run_record_path=RUN_PATH,
            research_ledger_path=LEDGER_PATH,
            triage_dir=triage_dir,
            events_dir=events_dir,
        )

    def test_append_cli_rejects_stale_plan_and_accepts_regenerated_plan(self) -> None:
        plan = self.external_plan()
        question_id = plan["proposed_questions"][0]["question_id"]
        triage_dir, head_triage_id = self._plan_context_by_case[
            str(plan["case_sha256"])
        ]
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            plan_path = directory / "plan.json"
            plan_path.write_text(
                dumps_adaptive_inquiry_plan(plan) + "\n",
                encoding="utf-8",
            )
            common = [
                sys.executable,
                "tools/run_semantic_inquiry.py",
                "append",
                "--run-record",
                str(RUN_PATH),
                "--research-ledger",
                str(LEDGER_PATH),
                "--triage-dir",
                str(triage_dir),
                "--events-dir",
                str(directory),
                "--plan",
                str(plan_path),
                "--question-id",
                str(question_id),
                "--occurred-on",
                "2026-09-03",
            ]
            backdated = subprocess.run(
                common[:-1]
                + [
                    "2026-09-02",
                    "--event-type",
                    "QUESTION_PROPOSED",
                    "--actor-kind",
                    "MACHINE",
                    "--reason-code",
                    "BACKDATED_TRIAGE",
                    "--reason",
                    "Attempt to propose before exact plan triage.",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(backdated.returncode, 0)
            self.assertEqual(
                json.loads(backdated.stdout)["error_code"],
                "INQUIRY_EVENT_PRECEDES_TRIAGE",
            )
            self.assertEqual(list(directory.glob("IE-*.json")), [])
            self.assertEqual(list(directory.glob("NEXT-*.claim")), [])

            proposed = subprocess.run(
                common
                + [
                    "--event-type",
                    "QUESTION_PROPOSED",
                    "--actor-kind",
                    "MACHINE",
                    "--reason-code",
                    "TEST_PROPOSED",
                    "--reason",
                    "Propose the exact current question.",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                proposed.returncode,
                0,
                proposed.stdout + proposed.stderr,
            )
            head = json.loads(proposed.stdout)["event"]["event_id"]
            stale = subprocess.run(
                common
                + [
                    "--expected-head-event-id",
                    head,
                    "--event-type",
                    "QUESTION_ACTIVATED",
                    "--actor-kind",
                    "HUMAN",
                    "--reason-code",
                    "TEST_ACTIVATED",
                    "--reason",
                    "Activate the exact current question.",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(stale.returncode, 0)
            self.assertEqual(
                json.loads(stale.stdout)["error_code"],
                "INQUIRY_PLAN_STALE_HEAD",
            )

            current_plan = self.build_plan(
                triage=plan["triage"],  # type: ignore[arg-type]
                triage_dir=triage_dir,
                head_triage_id=head_triage_id,
                events_dir=directory,
                head=head,
            )
            current_path = directory / "current-plan.json"
            current_path.write_text(
                dumps_adaptive_inquiry_plan(current_plan) + "\n",
                encoding="utf-8",
            )
            activated = subprocess.run(
                [
                    sys.executable,
                    "tools/run_semantic_inquiry.py",
                    "append",
                    "--run-record",
                    str(RUN_PATH),
                    "--research-ledger",
                    str(LEDGER_PATH),
                    "--triage-dir",
                    str(triage_dir),
                    "--events-dir",
                    str(directory),
                    "--expected-head-event-id",
                    head,
                    "--plan",
                    str(current_path),
                    "--question-id",
                    str(question_id),
                    "--event-type",
                    "QUESTION_ACTIVATED",
                    "--actor-kind",
                    "HUMAN",
                    "--occurred-on",
                    "2026-09-03",
                    "--reason-code",
                    "TEST_ACTIVATED",
                    "--reason",
                    "Activate the exact current question.",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                activated.returncode,
                0,
                activated.stdout + activated.stderr,
            )

    def test_optimized_python_preserves_fail_closed_no_triage_route(self) -> None:
        program = (
            "from pathlib import Path; import tempfile; "
            "from creib.forge.inquiry import build_adaptive_inquiry_plan; "
            f"root=Path(r'{ROOT}'); run=Path(r'{RUN_PATH}'); ledger=Path(r'{LEDGER_PATH}'); "
            "triage_dir=Path(tempfile.mkdtemp()); "
            "plan=build_adaptive_inquiry_plan(repo_root=root,run_record_path=run,research_ledger_path=ledger,triage_dir=triage_dir); "
            "print(plan['route'],plan['semantic_verdict'])"
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
        self.assertEqual(results[0], "AWAITING_HUMAN_TRIAGE None")
        self.assertEqual(results[0], results[1])

    def test_normal_and_optimized_cli_emit_identical_plural_plans(self) -> None:
        blocked = self.build_plan()
        triage = self.human_triage(blocked["bindings"])
        with tempfile.TemporaryDirectory() as temporary:
            triage_dir = Path(temporary) / "triage-lineage"
            triage_dir.mkdir()
            publish_human_triage_against_inputs(
                triage_dir,
                triage,
                expected_head_triage_id=None,
                repo_root=ROOT,
                run_record_path=RUN_PATH,
                research_ledger_path=LEDGER_PATH,
            )
            outputs = []
            for flags in ([], ["-O"]):
                result = subprocess.run(
                    [
                        sys.executable,
                        *flags,
                        "tools/run_semantic_inquiry.py",
                        "plan",
                        "--run-record",
                        str(RUN_PATH),
                        "--research-ledger",
                        str(LEDGER_PATH),
                        "--triage-dir",
                        str(triage_dir),
                        "--head-triage-id",
                        str(triage["triage_id"]),
                    ],
                    cwd=ROOT,
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                outputs.append(result.stdout)
        self.assertEqual(outputs[0], outputs[1])
        plan = json.loads(outputs[0])
        self.assertEqual(plan["route"], InquiryRoute.EXTERNAL_RESEARCH_REQUIRED.value)
        self.assertEqual(plan["triage"]["overall_status"], "UNRESOLVED")
        self.assertIsNone(plan["semantic_verdict"])

    def test_normal_and_optimized_cli_emit_valid_dependent_frontier_plan(self) -> None:
        blocked = self.build_plan()
        bindings = blocked["bindings"]
        prerequisite = self.locus_assessment(
            loci=("AUXILIARY",),
            mechanism="A scheduled auxiliary criticism precedes external work.",
        )
        dependent = self.locus_assessment(
            mechanism="The external criticism depends on the auxiliary review.",
            dependencies=(str(prerequisite["assessment_id"]),),
        )
        assessments = [prerequisite, dependent]
        genesis = self.human_triage(
            bindings,  # type: ignore[arg-type]
            assessments=assessments,
            selected_assessment_ids=(str(prerequisite["assessment_id"]),),
            selection_basis="UPSTREAM_DEPENDENCY",
        )
        disposition = self.assessment_disposition(
            prerequisite,
            assessment_origin_triage_id=str(genesis["triage_id"]),
            bindings=bindings,  # type: ignore[arg-type]
            disposition="DEFEATED",
            evidence_bindings=[self.calibration_disposition_evidence()],
        )
        successor = self.human_triage(
            bindings,  # type: ignore[arg-type]
            assessments=assessments,
            assessment_dispositions=[disposition],
            selected_assessment_ids=(str(dependent["assessment_id"]),),
            sequence=2,
            previous_triage_id=str(genesis["triage_id"]),
            transition_kind="SAME_BINDINGS",
            transition_reason=(
                "Record the prerequisite disposition and schedule the newly open frontier."
            ),
        )
        with tempfile.TemporaryDirectory() as temporary:
            triage_dir = Path(temporary) / "triage-lineage"
            triage_dir.mkdir()
            publish_human_triage_against_inputs(
                triage_dir,
                genesis,
                expected_head_triage_id=None,
                repo_root=ROOT,
                run_record_path=RUN_PATH,
                research_ledger_path=LEDGER_PATH,
            )
            publish_human_triage_against_inputs(
                triage_dir,
                successor,
                expected_head_triage_id=str(genesis["triage_id"]),
                repo_root=ROOT,
                run_record_path=RUN_PATH,
                research_ledger_path=LEDGER_PATH,
            )
            outputs = []
            for flags in ([], ["-O"]):
                result = subprocess.run(
                    [
                        sys.executable,
                        *flags,
                        "tools/run_semantic_inquiry.py",
                        "plan",
                        "--run-record",
                        str(RUN_PATH),
                        "--research-ledger",
                        str(LEDGER_PATH),
                        "--triage-dir",
                        str(triage_dir),
                        "--head-triage-id",
                        str(successor["triage_id"]),
                    ],
                    cwd=ROOT,
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                outputs.append(result.stdout)

        self.assertEqual(outputs[0], outputs[1])
        plan = loads_adaptive_inquiry_plan(outputs[0])
        self.assertEqual(plan["route"], InquiryRoute.EXTERNAL_RESEARCH_REQUIRED.value)
        self.assertTrue(plan["proposed_questions"])
        for question in plan["proposed_questions"]:
            self.assertEqual(
                question["selected_assessment_ids"],
                [dependent["assessment_id"]],
            )

    def test_normal_and_optimized_cli_reject_same_blocked_action(self) -> None:
        blocked = self.build_plan()
        bindings = blocked["bindings"]
        prerequisite = self.locus_assessment(
            loci=("AUXILIARY",),
            mechanism="Optimized-mode prerequisite.",
        )
        dependent = self.locus_assessment(
            mechanism="Optimized-mode dependent.",
            dependencies=(str(prerequisite["assessment_id"]),),
        )
        invalid = self.human_triage(
            bindings,  # type: ignore[arg-type]
            assessments=[prerequisite, dependent],
            selected_assessment_ids=(str(dependent["assessment_id"]),),
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            triage_path = root / "blocked-triage.json"
            triage_path.write_text(
                json.dumps(
                    invalid,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n",
                encoding="utf-8",
            )
            failures = []
            for index, flags in enumerate(([], ["-O"])):
                triage_dir = root / f"lineage-{index}"
                triage_dir.mkdir()
                result = subprocess.run(
                    [
                        sys.executable,
                        *flags,
                        "tools/run_semantic_inquiry.py",
                        "publish-triage",
                        "--run-record",
                        str(RUN_PATH),
                        "--research-ledger",
                        str(LEDGER_PATH),
                        "--triage-dir",
                        str(triage_dir),
                        "--triage",
                        str(triage_path),
                    ],
                    cwd=ROOT,
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertNotEqual(result.returncode, 0)
                failures.append(json.loads(result.stdout))
                self.assertEqual(list(triage_dir.iterdir()), [])
        self.assertEqual(failures[0], failures[1])
        self.assertIsNone(failures[0]["semantic_verdict"])
        self.assertIn("dependency-frontier", failures[0]["error"])

    def test_normal_and_optimized_cli_emit_identical_disposition_plan(self) -> None:
        blocked = self.build_plan()
        bindings = blocked["bindings"]
        assessment = self.locus_assessment(
            mechanism="One scheduled criticism receives exact run-bound treatment."
        )
        genesis = self.human_triage(
            bindings,  # type: ignore[arg-type]
            assessments=[assessment],
        )
        directory = self.new_triage_dir()
        self.build_plan(triage=genesis, triage_dir=directory)
        disposition = self.assessment_disposition(
            assessment,
            assessment_origin_triage_id=str(genesis["triage_id"]),
            bindings=bindings,  # type: ignore[arg-type]
            disposition="DEFEATED",
            evidence_bindings=[self.calibration_disposition_evidence()],
        )
        successor = self.human_triage(
            bindings,  # type: ignore[arg-type]
            assessments=[assessment],
            assessment_dispositions=[disposition],
            include_action=False,
            sequence=2,
            previous_triage_id=str(genesis["triage_id"]),
            transition_kind="SAME_BINDINGS",
            transition_reason="Record one scoped workflow disposition.",
        )
        expected = self.build_plan(
            triage=successor,
            triage_dir=directory,
            head_triage_id=str(successor["triage_id"]),
        )
        command = [
            "tools/run_semantic_inquiry.py",
            "plan",
            "--run-record",
            str(RUN_PATH),
            "--research-ledger",
            str(LEDGER_PATH),
            "--triage-dir",
            str(directory),
            "--head-triage-id",
            str(successor["triage_id"]),
        ]
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(ROOT / "src")
        outputs: list[str] = []
        for flags in ([], ["-O"]):
            result = subprocess.run(
                [sys.executable, *flags, *command],
                cwd=ROOT,
                env=environment,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            outputs.append(result.stdout)
        self.assertEqual(outputs[0], outputs[1])
        self.assertEqual(json.loads(outputs[0]), expected)
        self.assertEqual(
            expected["route"],
            InquiryRoute.AWAITING_HUMAN_REASSESSMENT.value,
        )
        self.assertIsNone(expected["semantic_verdict"])


if __name__ == "__main__":
    unittest.main()
