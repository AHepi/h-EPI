from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from creib.canonical import domain_digest
from creib.errors import PolicyViolation, RecordError
from creib.forge.inquiry import (
    InquiryError,
    InquiryRoute,
    QuestionState,
    build_adaptive_inquiry_plan,
    build_inquiry_event,
    compute_adaptive_inquiry_plan_id,
    compute_event_id,
    compute_human_triage_id,
    compute_question_id,
    dumps_adaptive_inquiry_plan,
    inquiry_question_digest,
    load_research_ledger_binding,
    loads_adaptive_inquiry_plan,
    publish_inquiry_event,
    validate_adaptive_inquiry_plan,
    validate_human_triage,
    validate_inquiry_event,
    validate_inquiry_question_against_plan,
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
SCHEMA_PATH = ROOT / "forge" / "schema" / "adaptive-inquiry.schema.json"
EVENT_SCHEMA_PATH = ROOT / "forge" / "schema" / "inquiry-event.schema.json"


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

    def build_plan(
        self,
        *,
        triage: dict[str, object] | None = None,
        events_dir: Path | None = None,
        head: str | None = None,
    ) -> dict[str, object]:
        return build_adaptive_inquiry_plan(
            repo_root=ROOT,
            run_record_path=RUN_PATH,
            research_ledger_path=LEDGER_PATH,
            triage=triage,
            events_dir=events_dir,
            head_event_id=head,
        )

    def human_triage(
        self,
        bindings: dict[str, object],
        *,
        disposition: str = "UNRESOLVED",
        location: str = "EXTERNAL_CRITICAL_INSTRUMENT",
        created_on: str = "2026-09-03",
    ) -> dict[str, object]:
        record: dict[str, object] = {
            "$schema": "../schema/adaptive-inquiry.schema.json",
            "schema_version": "creib.semantic-forge.human-failure-triage.v1",
            "record_type": "human_failure_triage",
            "triage_id": "HT:" + "0" * 64,
            "created_on": created_on,
            "bindings": copy.deepcopy(bindings),
            "disposition": disposition,
            "uncertainty_location": location,
            "reason": "A fallible human workflow triage for an exact criticism candidate.",
            "scope": "The finite typed-role projection and its declared contracts only.",
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

    def standalone_entry(
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
            research_ledger=self.ledger,
            research_binding=self.ledger_binding,
        )
        return event

    def test_new_schemas_are_strict_and_registered_offline(self) -> None:
        adaptive = load_strict(SCHEMA_PATH)
        event = load_strict(EVENT_SCHEMA_PATH)
        self.assertEqual(adaptive["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertFalse(event["additionalProperties"])
        result = subprocess.run(
            [sys.executable, "tools/validate_semantic_forge.py"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("adaptive-inquiry.schema.json", result.stdout)
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

        changed = copy.deepcopy(triage)
        changed["bindings"]["candidate_id"] = "SAME-ID-LAUNDERING-ATTEMPT"
        changed["triage_id"] = compute_human_triage_id(changed)
        with self.assertRaisesRegex(PolicyViolation, "exact current inquiry inputs"):
            validate_human_triage(changed, expected_bindings=blocked["bindings"])

        stale_id = copy.deepcopy(triage)
        stale_id["reason"] += " changed"
        with self.assertRaisesRegex(RecordError, "content-addressed ID mismatch"):
            validate_human_triage(stale_id, expected_bindings=blocked["bindings"])

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
        with self.assertRaisesRegex(PolicyViolation, "bound issue digest"):
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
        changed["route"] = InquiryRoute.OUT_OF_SCOPE.value
        changed["route_reason"] = "The supplied human triage marks the case out of scope."
        changed["plan_id"] = compute_adaptive_inquiry_plan_id(changed)
        with self.assertRaisesRegex(PolicyViolation, "untriaged observation"):
            validate_adaptive_inquiry_plan(changed)

    def test_route_matrix_keeps_internal_authority_and_external_work_distinct(self) -> None:
        blocked = self.build_plan()
        cases = (
            (
                "TEST_DEFECT",
                "INTERNAL_HARNESS_SPECIFICATION",
                InquiryRoute.INTERNAL_HARNESS_WORK,
            ),
            (
                "CANDIDATE_DEFECT",
                "INTERNAL_DEDUCTION_OR_MODEL_FINDING",
                InquiryRoute.INTERNAL_MODEL_WORK,
            ),
            (
                "UNRESOLVED",
                "CR_AUTHORITY_INTERPRETATION",
                InquiryRoute.AUTHORITY_REVIEW,
            ),
            ("OUT_OF_SCOPE", "UNLOCATED", InquiryRoute.OUT_OF_SCOPE),
            ("UNRESOLVED", "UNLOCATED", InquiryRoute.AWAITING_HUMAN_TRIAGE),
        )
        for disposition, location, expected in cases:
            triage = self.human_triage(
                blocked["bindings"],  # type: ignore[arg-type]
                disposition=disposition,
                location=location,
            )
            with self.subTest(disposition=disposition, location=location):
                plan = self.build_plan(triage=triage)
                self.assertEqual(plan["route"], expected.value)
                self.assertEqual(plan["proposed_questions"], [])

    def test_current_case_forged_chain_question_blocks_route_and_cli_action(self) -> None:
        plan = self.external_plan()
        forged = copy.deepcopy(plan["proposed_questions"][0])
        forged["rival_claim"] += " Forged current-case variant."
        forged["question_id"] = compute_question_id(forged)
        self.assertEqual(forged["case_sha256"], plan["case_sha256"])
        self.assertNotIn(
            forged["question_id"],
            {item["question_id"] for item in plan["proposed_questions"]},
        )
        with self.assertRaisesRegex(
            PolicyViolation,
            "absent from the exact plan inventory",
        ):
            validate_inquiry_question_against_plan(forged, plan)

        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            event = self.append(
                directory,
                forged,
                head=None,
                event_type="QUESTION_PROPOSED",
                actor="MACHINE",
            )
            blocked = self.build_plan(
                triage=plan["triage"],  # type: ignore[arg-type]
                events_dir=directory,
                head=event["event_id"],
            )
            self.assertEqual(blocked["route"], InquiryRoute.POLICY_BLOCKED.value)
            self.assertEqual(
                blocked["route_reason"],
                "Event history changed a bound question.",
            )
            self.assertEqual(blocked["question_state"], {})

            plan_path = directory / "blocked-plan.json"
            plan_path.write_text(
                dumps_adaptive_inquiry_plan(blocked) + "\n",
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
                    "--events-dir",
                    str(directory),
                    "--expected-head-event-id",
                    str(event["event_id"]),
                    "--plan",
                    str(plan_path),
                    "--question-id",
                    str(forged["question_id"]),
                    "--event-type",
                    "QUESTION_ACTIVATED",
                    "--actor-kind",
                    "HUMAN",
                    "--occurred-on",
                    "2026-09-03",
                    "--reason-code",
                    "FORGED_CURRENT_QUESTION",
                    "--reason",
                    "Attempt to action a forged current-case question.",
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

    def test_historical_case_question_survives_later_triage_rollover(self) -> None:
        blocked = self.build_plan()
        old_triage = self.human_triage(
            blocked["bindings"],  # type: ignore[arg-type]
            created_on="2026-09-03",
        )
        old_plan = self.build_plan(triage=old_triage)
        old_question = old_plan["proposed_questions"][0]

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
                created_on="2026-09-04",
            )
            current = self.build_plan(
                triage=new_triage,
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

        def rejected_activation(
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
                    "--events-dir",
                    str(directory),
                    "--expected-head-event-id",
                    head,
                    "--plan",
                    str(plan_path),
                    "--question-id",
                    str(second["question_id"]),
                    "--event-type",
                    "QUESTION_ACTIVATED",
                    "--actor-kind",
                    "HUMAN",
                    "--occurred-on",
                    "2026-09-03",
                    "--reason-code",
                    suffix.upper(),
                    "--reason",
                    "Attempt to continue another question despite the exact route.",
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
            second_proposed = self.append(
                directory,
                second,
                head=first_proposed["event_id"],
                event_type="QUESTION_PROPOSED",
                actor="MACHINE",
            )
            stale = self.append(
                directory,
                first,
                head=second_proposed["event_id"],
                event_type="MODEL_CHANGED",
                actor="MACHINE",
            )
            blocked = self.build_plan(
                triage=plan["triage"],  # type: ignore[arg-type]
                events_dir=directory,
                head=stale["event_id"],
            )
            self.assertEqual(blocked["route"], InquiryRoute.POLICY_BLOCKED.value)
            self.assertEqual(
                blocked["question_state"][second["question_id"]],
                QuestionState.PROPOSED.value,
            )
            rejected_activation(
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
            second_proposed = self.append(
                directory,
                second,
                head=first_proposed["event_id"],
                event_type="QUESTION_PROPOSED",
                actor="MACHINE",
            )
            active = self.append(
                directory,
                first,
                head=second_proposed["event_id"],
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
                triage=plan["triage"],  # type: ignore[arg-type]
                events_dir=directory,
                head=retained["event_id"],
            )
            self.assertEqual(
                integration["route"],
                InquiryRoute.INTERNAL_INTEGRATION_REQUIRED.value,
            )
            self.assertEqual(
                integration["question_state"][second["question_id"]],
                QuestionState.PROPOSED.value,
            )
            rejected_activation(
                directory,
                integration,
                str(retained["event_id"]),
                "integration-required",
            )

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
            )
            self.assertEqual(len(state.events), 2)
            self.assertIs(
                state.question_states[question["question_id"]],
                QuestionState.ACTIVE,
            )

    def test_illegal_lifecycle_or_machine_human_disposition_fails(self) -> None:
        question = self.external_plan()["proposed_questions"][0]
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
            self.assertEqual(event["event_id"], compute_event_id(event))
            with self.assertRaises(InquiryError) as failure:
                publish_inquiry_event(
                    directory,
                    event,
                    expected_head_event_id=None,
                    research_ledger=self.ledger,
                    research_binding=self.ledger_binding,
                )
            self.assertIn(
                failure.exception.error_code,
                {"INQUIRY_EVENT_EXISTS", "INQUIRY_EVENT_STALE_HEAD"},
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

        def chain(report_count: int) -> str:
            temporary = tempfile.TemporaryDirectory()
            self.addCleanup(temporary.cleanup)
            directory = Path(temporary.name)
            head: str | None = None
            for index, question in enumerate(questions[:report_count]):
                proposed = self.append(
                    directory,
                    question,
                    head=head,
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
                head = report["event_id"]
            routed = self.build_plan(
                triage=plan["triage"],  # type: ignore[arg-type]
                events_dir=directory,
                head=head,
            )
            return routed["route"]  # type: ignore[return-value]

        self.assertEqual(chain(1), InquiryRoute.AWAITING_HUMAN_REVIEW.value)
        self.assertEqual(chain(2), InquiryRoute.AWAITING_HUMAN_REVIEW.value)

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
        unrelated = self.ledger.entries[0].to_dict()
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

    def test_standalone_entry_must_pass_its_own_content_digest(self) -> None:
        question = self.external_plan()["proposed_questions"][0]
        changed = self.standalone_entry(question)
        changed["title"] += " altered after hashing"
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
        changed["discovery"]["provider"] = "ModernIndex"
        changed["discovery"]["route_locator"] = "https://modern-index.example/result"
        unsigned = copy.deepcopy(changed)
        unsigned.pop("entry_sha256")
        changed["entry_sha256"] = domain_digest(
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
        question = self.external_plan()["proposed_questions"][0]
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
            with self.assertRaisesRegex(InquiryError, "precedes its selected parent"):
                publish_inquiry_event(
                    directory,
                    regressed,
                    expected_head_event_id=proposed["event_id"],
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
                    "adaptive-inquiry.schema.json",
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

    def test_append_cli_rejects_stale_plan_and_accepts_regenerated_plan(self) -> None:
        plan = self.external_plan()
        question_id = plan["proposed_questions"][0]["question_id"]
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
            "from pathlib import Path; "
            "from creib.forge.inquiry import build_adaptive_inquiry_plan; "
            f"root=Path(r'{ROOT}'); run=Path(r'{RUN_PATH}'); ledger=Path(r'{LEDGER_PATH}'); "
            "plan=build_adaptive_inquiry_plan(repo_root=root,run_record_path=run,research_ledger_path=ledger); "
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


if __name__ == "__main__":
    unittest.main()
