from __future__ import annotations

import copy
from pathlib import Path
import tempfile
import unittest

from creib.canonical import canonical_bytes
from creib.errors import PolicyViolation, RecordError
from creib.forge.generic_inquiry import (
    AdapterRegistry,
    AuthorityBinding,
    BindingKind,
    ComponentBinding,
    GENERIC_RECORD_ADAPTER_ID,
    GenericInquiryInputAdapter,
    LEGACY_CALIBRATION_ADAPTER_ID,
    LegacyCalibrationAdapter,
    ObservationDomain,
    ResearchBasis,
    available_attack_targets,
    build_generic_inquiry_plan,
    build_inquiry_input_record,
    compute_inquiry_input_id,
    compute_next_action_id,
    default_adapter_registry,
    legacy_calibration_binding_projection,
    make_locus_assessment,
    make_next_action,
    validate_generic_inquiry_plan,
)
from creib.strict_json import load_strict


ROOT = Path(__file__).resolve().parents[1]
RUN_PATH = ROOT / "forge/runs/SMF-CALIBRATION-CR-1-0-001.4219efce.json"
PLAN_PATH = ROOT / "forge/plans/SMF-AIP-1210e0fa.no-triage.json"


class GenericInquiryFoundationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.v2_plan = load_strict(PLAN_PATH)
        cls.ledger_binding = cls.v2_plan["bindings"]["research_ledger"]
        cls.legacy_case = default_adapter_registry().adapt_path(
            LEGACY_CALIBRATION_ADAPTER_ID,
            RUN_PATH,
            repo_root=ROOT,
            research_ledger_binding=cls.ledger_binding,
        )
        cls.basis = cls.legacy_case.research_basis
        if cls.basis is None:
            raise AssertionError("legacy fixture must contain a research basis")

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.temp_root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    @staticmethod
    def authorities() -> tuple[AuthorityBinding, ...]:
        return (
            AuthorityBinding("SEMANTIC_AUTHORITY", "CR-1.0", "a" * 64),
        )

    @staticmethod
    def components() -> tuple[ComponentBinding, ...]:
        values = (
            ComponentBinding(
                "OBLIGATION_GRAPH",
                "TOG-001",
                BindingKind.CANONICAL_RECORD,
                "b" * 64,
            ),
            ComponentBinding(
                "TRANSLATION_CANDIDATE",
                "TC-001",
                BindingKind.CONTRACT,
                "c" * 64,
            ),
        )
        return tuple(sorted(values, key=lambda item: canonical_bytes(item.to_dict())))

    def input_record(
        self,
        origin: ObservationDomain,
        *,
        selected_value: object | None = None,
        research_basis: ResearchBasis | None = None,
        components: tuple[ComponentBinding, ...] | None = None,
    ) -> dict[str, object]:
        return build_inquiry_input_record(
            producer_contract_sha256="d" * 64,
            authority_bindings=self.authorities(),
            component_bindings=components or self.components(),
            observation_domain=origin,
            selected_value=(
                {"mechanical_observation": "ONE_UNMAPPED_OBLIGATION"}
                if selected_value is None
                else selected_value
            ),
            research_basis=research_basis,
        )

    def adapt_record(self, record: dict[str, object]):
        path = self.temp_root / "input.json"
        path.write_bytes(canonical_bytes(record) + b"\n")
        return default_adapter_registry().adapt_path(
            GENERIC_RECORD_ADAPTER_ID,
            path,
            repo_root=ROOT,
            research_ledger_binding=self.ledger_binding,
        )

    @staticmethod
    def harness_assessment() -> dict[str, object]:
        return make_locus_assessment(
            loci=("AUXILIARY", "TEST"),
            mechanism="The adapter may have omitted an obligation before triage.",
            relevance="A missing obligation can change the bounded translation.",
            discriminator="Replay the exact source obligation through the adapter.",
            scope="The exact stage-neutral inquiry input only.",
            uncertainty_location="INTERNAL_HARNESS_SPECIFICATION",
        )

    @staticmethod
    def external_assessment() -> dict[str, object]:
        return make_locus_assessment(
            loci=("CANDIDATE",),
            mechanism="Two live interpretations require an external discriminator.",
            relevance="The discriminator can criticize either bounded rival.",
            discriminator="Inspect the exact rival-falsifier target.",
            scope="The exact research basis only.",
            uncertainty_location="EXTERNAL_CRITICAL_INSTRUMENT",
        )

    def test_legacy_adapter_projection_is_byte_equivalent_to_v2_binding(self) -> None:
        projected = legacy_calibration_binding_projection(self.legacy_case)
        self.assertEqual(projected, self.v2_plan["bindings"])
        self.assertEqual(
            canonical_bytes(projected),
            canonical_bytes(self.v2_plan["bindings"]),
        )

    def test_legacy_adapter_preserves_exact_observation_pointer_and_digest(self) -> None:
        binding = self.v2_plan["bindings"]
        observation = self.legacy_case.observation
        self.assertEqual(observation.selected_value_pointer, binding["observation_pointer"])
        self.assertEqual(observation.selected_value_sha256, binding["observation_sha256"])
        self.assertEqual(observation.source_snapshot["run_id"], binding["run_id"])

    def test_registry_requires_explicit_known_adapter(self) -> None:
        with self.assertRaisesRegex(RecordError, "unknown inquiry input adapter"):
            default_adapter_registry().adapt_path(
                "SMF-ADAPTER-UNKNOWN",
                RUN_PATH,
                repo_root=ROOT,
                research_ledger_binding=self.ledger_binding,
            )

    def test_registry_rejects_duplicate_adapter_identity(self) -> None:
        with self.assertRaisesRegex(RecordError, "duplicate inquiry input adapter"):
            AdapterRegistry((LegacyCalibrationAdapter(), LegacyCalibrationAdapter()))

    def test_case_binding_rejects_conflicting_logical_duplicates(self) -> None:
        duplicate_authorities = tuple(
            sorted(
                (
                    AuthorityBinding("SEMANTIC_AUTHORITY", "CR-1.0", "a" * 64),
                    AuthorityBinding("SEMANTIC_AUTHORITY", "Other", "b" * 64),
                ),
                key=lambda item: canonical_bytes(item.to_dict()),
            )
        )
        with self.assertRaisesRegex(PolicyViolation, "singleton authority role"):
            build_inquiry_input_record(
                producer_contract_sha256="d" * 64,
                authority_bindings=duplicate_authorities,
                component_bindings=self.components(),
                observation_domain=ObservationDomain.SOURCE_TRANSLATION,
                selected_value={"mechanical_observation": "CONFLICT"},
                research_basis=None,
            )

        duplicate_components = tuple(
            sorted(
                (
                    ComponentBinding(
                        "OBLIGATION_GRAPH",
                        "TOG-OTHER",
                        BindingKind.CANONICAL_RECORD,
                        "a" * 64,
                    ),
                    ComponentBinding(
                        "OBLIGATION_GRAPH",
                        "TOG-001",
                        BindingKind.CONTRACT,
                        "b" * 64,
                    ),
                ),
                key=lambda item: canonical_bytes(item.to_dict()),
            )
        )
        with self.assertRaisesRegex(PolicyViolation, "singleton component role"):
            build_inquiry_input_record(
                producer_contract_sha256="d" * 64,
                authority_bindings=self.authorities(),
                component_bindings=duplicate_components,
                observation_domain=ObservationDomain.SOURCE_TRANSLATION,
                selected_value={"mechanical_observation": "CONFLICT"},
                research_basis=None,
            )

    def test_wrong_explicit_adapter_does_not_guess_from_record(self) -> None:
        with self.assertRaises(RecordError):
            AdapterRegistry((GenericInquiryInputAdapter(),)).adapt_path(
                GENERIC_RECORD_ADAPTER_ID,
                RUN_PATH,
                repo_root=ROOT,
                research_ledger_binding=self.ledger_binding,
            )

    def test_all_origins_wait_for_human_triage(self) -> None:
        routes = set()
        for origin in ObservationDomain:
            with self.subTest(origin=origin.value):
                case = self.adapt_record(self.input_record(origin))
                plan = build_generic_inquiry_plan(case)
                routes.add(plan["route"])
                self.assertFalse(plan["origin_can_select_locus_or_route"])
                self.assertFalse(plan["publication_authority"])
                self.assertIsNone(plan["semantic_verdict"])
        self.assertEqual(routes, {"AWAITING_HUMAN_TRIAGE"})

    def test_origin_cannot_change_same_human_selected_route(self) -> None:
        routes = set()
        for origin in ObservationDomain:
            case = self.adapt_record(self.input_record(origin))
            assessment = self.harness_assessment()
            action = make_next_action(
                case,
                selected_assessment_ids=(str(assessment["assessment_id"]),),
                route_intent="INTERNAL_HARNESS_WORK",
                action="Replay the adapter against the exact obligation.",
                selection_basis="INDEPENDENT_HUMAN_PRIORITY",
                reason="This schedules work and makes no semantic ranking.",
            )
            routes.add(
                build_generic_inquiry_plan(
                    case,
                    locus_assessments=(assessment,),
                    next_action=action,
                )["route"]
            )
        self.assertEqual(routes, {"INTERNAL_HARNESS_WORK"})

    def test_observation_without_action_waits_after_plural_assessment(self) -> None:
        case = self.adapt_record(self.input_record(ObservationDomain.SOURCE_TRANSLATION))
        assessment = self.harness_assessment()
        plan = build_generic_inquiry_plan(case, locus_assessments=(assessment,))
        self.assertEqual(plan["route"], "AWAITING_HUMAN_ACTION_SELECTION")

    def test_action_cannot_precede_human_assessment(self) -> None:
        case = self.adapt_record(self.input_record(ObservationDomain.HARNESS_TEST))
        assessment = self.harness_assessment()
        action = make_next_action(
            case,
            selected_assessment_ids=(str(assessment["assessment_id"]),),
            route_intent="INTERNAL_HARNESS_WORK",
            action="Run the exact internal check.",
            selection_basis="INDEPENDENT_HUMAN_PRIORITY",
            reason="Scheduling only.",
        )
        with self.assertRaisesRegex(PolicyViolation, "cannot precede"):
            build_generic_inquiry_plan(case, next_action=action)

    def test_external_action_requires_research_basis(self) -> None:
        case = self.adapt_record(self.input_record(ObservationDomain.SOURCE_TRANSLATION))
        assessment = self.external_assessment()
        with self.assertRaisesRegex(PolicyViolation, "exact research basis"):
            make_next_action(
                case,
                selected_assessment_ids=(str(assessment["assessment_id"]),),
                route_intent="EXTERNAL_RESEARCH_REQUIRED",
                action="Seek the exact discriminator.",
                selection_basis="INDEPENDENT_HUMAN_PRIORITY",
                reason="Scheduling only.",
                attack_target_ids=("AT:" + "0" * 64,),
            )

    def test_external_action_requires_nonempty_exact_target_subset(self) -> None:
        case = self.adapt_record(
            self.input_record(
                ObservationDomain.SOURCE_TRANSLATION,
                research_basis=self.basis,
            )
        )
        assessment = self.external_assessment()
        with self.assertRaisesRegex(PolicyViolation, "attack-target subset"):
            make_next_action(
                case,
                selected_assessment_ids=(str(assessment["assessment_id"]),),
                route_intent="EXTERNAL_RESEARCH_REQUIRED",
                action="Seek the exact discriminator.",
                selection_basis="INDEPENDENT_HUMAN_PRIORITY",
                reason="Scheduling only.",
            )

    def test_exact_external_basis_and_target_route_research(self) -> None:
        case = self.adapt_record(
            self.input_record(
                ObservationDomain.SEMANTIC_MODEL,
                research_basis=self.basis,
            )
        )
        assessment = self.external_assessment()
        target_id = str(available_attack_targets(case)[0]["attack_target_id"])
        action = make_next_action(
            case,
            selected_assessment_ids=(str(assessment["assessment_id"]),),
            route_intent="EXTERNAL_RESEARCH_REQUIRED",
            action="Seek the exact rival falsifier.",
            selection_basis="INDEPENDENT_HUMAN_PRIORITY",
            reason="The human selected this bounded external work.",
            attack_target_ids=(target_id,),
        )
        plan = build_generic_inquiry_plan(
            case,
            locus_assessments=(assessment,),
            next_action=action,
        )
        self.assertEqual(plan["route"], "EXTERNAL_RESEARCH_REQUIRED")
        self.assertEqual(
            plan["next_action"]["research_target"]["case_binding_id"],
            case.case_binding_id,
        )
        self.assertEqual(
            plan["next_action"]["research_target"]["attack_target_ids"],
            [target_id],
        )
        validate_generic_inquiry_plan(plan)

    def test_external_action_rejects_changed_case_binding(self) -> None:
        case = self.adapt_record(
            self.input_record(
                ObservationDomain.SEMANTIC_MODEL,
                research_basis=self.basis,
            )
        )
        assessment = self.external_assessment()
        target_id = str(available_attack_targets(case)[0]["attack_target_id"])
        action = make_next_action(
            case,
            selected_assessment_ids=(str(assessment["assessment_id"]),),
            route_intent="EXTERNAL_RESEARCH_REQUIRED",
            action="Seek the exact rival falsifier.",
            selection_basis="INDEPENDENT_HUMAN_PRIORITY",
            reason="Scheduling only.",
            attack_target_ids=(target_id,),
        )
        action["research_target"]["case_binding_id"] = "CB:" + "0" * 64
        action["action_id"] = compute_next_action_id(action)
        with self.assertRaisesRegex(PolicyViolation, "exact research basis"):
            build_generic_inquiry_plan(
                case,
                locus_assessments=(assessment,),
                next_action=action,
            )

    def test_unavailable_attack_target_is_rejected(self) -> None:
        case = self.adapt_record(
            self.input_record(
                ObservationDomain.SOURCE_TRANSLATION,
                research_basis=self.basis,
            )
        )
        assessment = self.external_assessment()
        action = make_next_action(
            case,
            selected_assessment_ids=(str(assessment["assessment_id"]),),
            route_intent="EXTERNAL_RESEARCH_REQUIRED",
            action="Seek a target.",
            selection_basis="INDEPENDENT_HUMAN_PRIORITY",
            reason="Scheduling only.",
            attack_target_ids=("AT:" + "0" * 64,),
        )
        with self.assertRaisesRegex(PolicyViolation, "unavailable attack targets"):
            build_generic_inquiry_plan(
                case,
                locus_assessments=(assessment,),
                next_action=action,
            )

    def test_selected_value_change_changes_observation_and_case_identity(self) -> None:
        first = self.adapt_record(
            self.input_record(
                ObservationDomain.SOURCE_TRANSLATION,
                selected_value={"unmapped": "A"},
            )
        )
        second = self.adapt_record(
            self.input_record(
                ObservationDomain.SOURCE_TRANSLATION,
                selected_value={"unmapped": "B"},
            )
        )
        self.assertNotEqual(first.observation.observation_id, second.observation.observation_id)
        self.assertNotEqual(first.case_binding_id, second.case_binding_id)

    def test_component_change_changes_case_but_not_observation_selection(self) -> None:
        first = self.adapt_record(self.input_record(ObservationDomain.HARNESS_TEST))
        changed_components = tuple(
            sorted(
                (
                    *self.components()[:-1],
                    ComponentBinding(
                        "TRANSLATION_CANDIDATE",
                        "TC-001",
                        BindingKind.CONTRACT,
                        "e" * 64,
                    ),
                ),
                key=lambda item: canonical_bytes(item.to_dict()),
            )
        )
        second = self.adapt_record(
            self.input_record(
                ObservationDomain.HARNESS_TEST,
                components=changed_components,
            )
        )
        self.assertEqual(
            first.observation.selected_value_sha256,
            second.observation.selected_value_sha256,
        )
        self.assertNotEqual(first.case_binding_id, second.case_binding_id)

    def test_input_id_tamper_fails_closed(self) -> None:
        record = self.input_record(ObservationDomain.ROUND_TRIP)
        record["input_id"] = "II:" + "0" * 64
        with self.assertRaisesRegex(RecordError, "content-addressed ID mismatch"):
            self.adapt_record(record)

    def test_noncanonical_binding_order_fails_closed(self) -> None:
        record = self.input_record(ObservationDomain.SOURCE_TRANSLATION)
        record["component_bindings"] = list(reversed(record["component_bindings"]))
        record["input_id"] = compute_inquiry_input_id(record)
        with self.assertRaisesRegex(RecordError, "canonical order"):
            self.adapt_record(record)

    def test_float_observation_is_outside_canonical_profile(self) -> None:
        with self.assertRaises(RecordError):
            build_inquiry_input_record(
                producer_contract_sha256="d" * 64,
                authority_bindings=self.authorities(),
                component_bindings=self.components(),
                observation_domain=ObservationDomain.HARNESS_TEST,
                selected_value={"score": 0.9},
                research_basis=None,
            )

    def test_plan_route_tamper_fails_regeneration(self) -> None:
        case = self.adapt_record(self.input_record(ObservationDomain.SEMANTIC_MODEL))
        plan = build_generic_inquiry_plan(case)
        forged = copy.deepcopy(plan)
        forged["route"] = "AUTHORITY_REVIEW"
        with self.assertRaises((PolicyViolation, RecordError)):
            validate_generic_inquiry_plan(forged)

    def test_foundation_plan_is_never_publication_authority(self) -> None:
        case = self.adapt_record(self.input_record(ObservationDomain.MATHEMATICAL_EXTRACTION))
        plan = build_generic_inquiry_plan(case)
        self.assertFalse(plan["publication_authority"])
        self.assertEqual(plan["epistemic_status"], "UNRESOLVED")
        self.assertEqual(plan["epistemic_effect"], "WORKFLOW_ROUTING_ONLY")


if __name__ == "__main__":
    unittest.main()
