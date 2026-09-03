from __future__ import annotations

import json
import unittest
from dataclasses import FrozenInstanceError

from creib.errors import PolicyViolation, RecordError
from creib.forge import (
    NON_INDUCTIVE_LIMIT,
    REQUIRED_PRESERVATION_DIMENSIONS,
    DefectType,
    FormalizationReadiness,
    HardeningStatus,
    Issue,
    JustificationBasis,
    OracleStatus,
    PreservationDimension,
    ReadinessStatus,
    ResearchWarrant,
    Rival,
    UnknownKind,
    assess_formalization_readiness,
    assess_revision,
    dumps_record,
    generate_challenge_template,
    generate_challenge_templates,
    generate_research_warrant,
    loads_formalization_readiness,
    loads_hardening_assessment,
    loads_issue,
    loads_minimal_pair_challenge,
    loads_research_warrant,
    parse_hardening_assessment,
    parse_issue,
    parse_minimal_pair_challenge,
    parse_research_warrant,
    parse_rival,
    to_jsonable,
)


def rival(name: str, *, falsifiable: bool = True) -> Rival:
    conditions = (f"A source passage contradicts {name}.",) if falsifiable else ()
    return Rival(name, f"The semantic role follows reading {name}.", conditions)


def issue(
    *,
    issue_id: str = "ISSUE-1",
    unknown_kind: UnknownKind = UnknownKind.EXTERNAL,
    relevant: bool = True,
    rivals: tuple[Rival, ...] | None = None,
) -> Issue:
    return Issue(
        issue_id=issue_id,
        question="Which reading fixes the role boundary?",
        unknown_kind=unknown_kind,
        decision="Choose the role boundary in model version two.",
        decision_relevance=(
            "The answer admits one countermodel and excludes the other."
            if relevant
            else None
        ),
        rivals=rivals if rivals is not None else (rival("R1"), rival("R2")),
        expected_discriminator="A named finding makes the rivals classify one case differently.",
        admissible_source_scope=("Primary sources and explicit critical rivals.",),
        stop_condition="Stop after the declared scope is inspected or the question is shown defective.",
    )


ALL_PRESERVED = tuple(REQUIRED_PRESERVATION_DIMENSIONS)


class StrictRecordTests(unittest.TestCase):
    def test_issue_and_rival_round_trip_through_json(self) -> None:
        original = issue()
        encoded = dumps_record(original)
        decoded = loads_issue(encoded)
        self.assertEqual(decoded, original)
        self.assertEqual(parse_issue(to_jsonable(original)), original)
        self.assertEqual(parse_rival(original.rivals[0].to_dict()), original.rivals[0])

    def test_records_are_frozen(self) -> None:
        original = issue()
        with self.assertRaises(FrozenInstanceError):
            original.question = "changed"  # type: ignore[misc]

    def test_issue_rejects_duplicate_rival_identity_and_claim(self) -> None:
        first = rival("R1")
        duplicate_id = Rival("R1", "A distinct claim.", ("A counterexample.",))
        duplicate_claim = Rival("R2", first.claim, ("A different counterexample.",))
        with self.assertRaisesRegex(ValueError, "unique rival_id"):
            issue(rivals=(first, duplicate_id))
        with self.assertRaisesRegex(ValueError, "distinct claims"):
            issue(rivals=(first, duplicate_claim))

    def test_direct_construction_requires_typed_immutable_collections(self) -> None:
        with self.assertRaisesRegex(ValueError, "must be a tuple"):
            Rival("R1", "A claim.", ["A falsifier."])  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "must be UnknownKind"):
            Issue("I1", "Question?", "external", "Decision.", "Impact.", ())  # type: ignore[arg-type]

    def test_parser_rejects_missing_extra_and_wrong_container_fields(self) -> None:
        record = issue().to_dict()
        for mutation in ("missing", "extra", "wrong-container"):
            candidate = dict(record)
            if mutation == "missing":
                del candidate["decision"]
            elif mutation == "extra":
                candidate["confidence"] = 0
            else:
                candidate["rivals"] = {}
            with self.subTest(mutation=mutation), self.assertRaises(RecordError):
                parse_issue(candidate)

    def test_parser_rejects_unknown_schema_and_enum(self) -> None:
        record = issue().to_dict()
        record["schema_version"] = "creib.semantic-forge.issue.v999"
        with self.assertRaisesRegex(RecordError, "schema version"):
            parse_issue(record)
        record = issue().to_dict()
        record["unknown_kind"] = "expert_vote"
        with self.assertRaisesRegex(RecordError, "must be one of"):
            parse_issue(record)

    def test_strict_json_rejects_duplicate_keys(self) -> None:
        source = dumps_record(issue())
        duplicate = source.replace(
            '"issue_id":"ISSUE-1"',
            '"issue_id":"ISSUE-1","issue_id":"ISSUE-2"',
        )
        with self.assertRaisesRegex(RecordError, "duplicate JSON key"):
            loads_issue(duplicate)

    def test_serialized_reports_use_only_json_primitives(self) -> None:
        records = (
            issue(),
            generate_research_warrant(issue()),
            generate_challenge_template(DefectType.ROLE_RELABELING),
            assess_formalization_readiness(report_id="READY-1", candidate_id="CANDIDATE-1"),
        )
        for record in records:
            with self.subTest(record=type(record).__name__):
                projected = to_jsonable(record)  # type: ignore[arg-type]
                self.assertEqual(json.loads(json.dumps(projected)), projected)


class ResearchWarrantTests(unittest.TestCase):
    def test_valid_external_decision_gap_generates_warrant(self) -> None:
        source_issue = issue()
        warrant = generate_research_warrant(source_issue)
        self.assertIsInstance(warrant, ResearchWarrant)
        self.assertEqual(warrant.issue_id, source_issue.issue_id)
        self.assertEqual(warrant.discovery_channels, ("AlphaXiv",))
        self.assertEqual(warrant.epistemic_limit, NON_INDUCTIVE_LIMIT)
        self.assertEqual(loads_research_warrant(dumps_record(warrant)), warrant)

    def test_discovery_provider_is_pluggable_and_preserves_priority(self) -> None:
        warrant = generate_research_warrant(
            issue(),
            discovery_channels=("Primary archive", "AlphaXiv", "Consensus"),
        )
        self.assertEqual(
            warrant.discovery_channels,
            ("Primary archive", "AlphaXiv", "Consensus"),
        )

    def test_maximum_issue_id_produces_bounded_content_derived_warrant_id(self) -> None:
        maximum_id = "I" + ("x" * 127)
        first = generate_research_warrant(issue(issue_id=maximum_id))
        repeated = generate_research_warrant(issue(issue_id=maximum_id))
        changed = issue(issue_id=maximum_id)
        changed = Issue(
            issue_id=changed.issue_id,
            question="Which changed question fixes the role boundary?",
            unknown_kind=changed.unknown_kind,
            decision=changed.decision,
            decision_relevance=changed.decision_relevance,
            rivals=changed.rivals,
            expected_discriminator=changed.expected_discriminator,
            admissible_source_scope=changed.admissible_source_scope,
            stop_condition=changed.stop_condition,
        )
        changed_warrant = generate_research_warrant(changed)

        self.assertIsNotNone(first)
        self.assertIsNotNone(repeated)
        self.assertIsNotNone(changed_warrant)
        assert first is not None and repeated is not None and changed_warrant is not None
        self.assertEqual(first.warrant_id, repeated.warrant_id)
        self.assertNotEqual(first.warrant_id, changed_warrant.warrant_id)
        self.assertLessEqual(len(first.warrant_id), 128)
        self.assertRegex(first.warrant_id, r"^RW:[0-9a-f]{64}$")

        with self.assertRaisesRegex(ValueError, "stable identifier"):
            issue(issue_id="I" + ("x" * 128))

    def test_internal_gap_cannot_generate_external_research(self) -> None:
        self.assertIsNone(
            generate_research_warrant(issue(unknown_kind=UnknownKind.INTERNAL))
        )

    def test_decision_irrelevant_gap_cannot_generate_research(self) -> None:
        self.assertIsNone(generate_research_warrant(issue(relevant=False)))

    def test_fewer_than_two_distinct_rivals_cannot_generate_research(self) -> None:
        self.assertIsNone(generate_research_warrant(issue(rivals=(rival("R1"),))))
        self.assertIsNone(generate_research_warrant(issue(rivals=())))

    def test_every_rival_requires_a_possible_falsifier(self) -> None:
        incomplete = issue(rivals=(rival("R1"), rival("R2", falsifiable=False)))
        self.assertIsNone(generate_research_warrant(incomplete))

    def test_warrant_cannot_be_constructed_for_internal_unknown(self) -> None:
        source_issue = issue()
        with self.assertRaisesRegex(ValueError, "external unknown"):
            ResearchWarrant(
                warrant_id="RW:I1",
                issue_id=source_issue.issue_id,
                question=source_issue.question,
                unknown_kind=UnknownKind.INTERNAL,
                decision=source_issue.decision,
                decision_relevance=source_issue.decision_relevance or "impact",
                rivals=source_issue.rivals,
                expected_discriminator=source_issue.expected_discriminator or "discriminator",
                admissible_source_scope=source_issue.admissible_source_scope,
                stop_condition=source_issue.stop_condition or "stop",
                discovery_channels=("AlphaXiv",),
            )

    def test_warrant_parser_rejects_weakened_epistemic_limit(self) -> None:
        warrant = generate_research_warrant(issue())
        record = warrant.to_dict()
        record["epistemic_limit"] = "Many passes confirm the preferred rival."
        with self.assertRaisesRegex(PolicyViolation, "non-inductive"):
            parse_research_warrant(record)

    def test_missing_discriminator_scope_or_stop_condition_blocks_research(self) -> None:
        complete = issue()
        mutations = (
            {"expected_discriminator": None},
            {"admissible_source_scope": ()},
            {"stop_condition": None},
        )
        for mutation in mutations:
            values = {
                "issue_id": complete.issue_id,
                "question": complete.question,
                "unknown_kind": complete.unknown_kind,
                "decision": complete.decision,
                "decision_relevance": complete.decision_relevance,
                "rivals": complete.rivals,
                "expected_discriminator": complete.expected_discriminator,
                "admissible_source_scope": complete.admissible_source_scope,
                "stop_condition": complete.stop_condition,
            }
            values.update(mutation)
            with self.subTest(mutation=mutation):
                self.assertIsNone(generate_research_warrant(Issue(**values)))

    def test_empty_or_duplicate_provider_labels_fail(self) -> None:
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            generate_research_warrant(issue(), discovery_channels=())
        with self.assertRaisesRegex(ValueError, "duplicates"):
            generate_research_warrant(
                issue(),
                discovery_channels=("AlphaXiv", "AlphaXiv"),
            )


class MinimalPairTemplateTests(unittest.TestCase):
    def test_every_defect_type_has_one_well_formed_template(self) -> None:
        templates = generate_challenge_templates()
        self.assertEqual(
            {item.defect_type for item in templates},
            {item.value for item in DefectType},
        )
        self.assertEqual(len(templates), len(DefectType))
        for template in templates:
            with self.subTest(defect_type=template.defect_type):
                self.assertNotEqual(template.intended_case, template.lookalike_case)
                self.assertTrue(template.controlled_difference)
                self.assertTrue(template.oracle)
                self.assertTrue(template.falsifies_if)
                self.assertEqual(
                    loads_minimal_pair_challenge(dumps_record(template)),
                    template,
                )

    def test_generation_is_permutation_invariant(self) -> None:
        types = (
            DefectType.SCOPE_ESCAPE,
            DefectType.INDUCTIVE_WARRANT,
            DefectType.ROLE_RELABELING,
        )
        forward = generate_challenge_templates(types)
        reverse = generate_challenge_templates(reversed(types))
        self.assertEqual(forward, reverse)

    def test_unknown_defect_type_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown defect type"):
            generate_challenge_template("confirmation_score")

    def test_runtime_challenge_can_name_a_new_defect_family(self) -> None:
        record = generate_challenge_template(DefectType.ROLE_RELABELING).to_dict()
        record["defect_type"] = "newly_witnessed_defect"
        parsed = parse_minimal_pair_challenge(record)
        self.assertEqual(parsed.defect_type, "newly_witnessed_defect")
        self.assertIs(parsed.oracle_status, OracleStatus.PROJECT_IMPORT_PROVISIONAL)

    def test_dynamic_challenge_oracle_requires_a_typed_nonfinal_status(self) -> None:
        record = generate_challenge_template(DefectType.ROLE_RELABELING).to_dict()
        for oracle in (
            "A free-text oracle with no boundary.",
            "status=confirmed; a machine verdict",
            "status=project_import_provisional;   ",
            "status=project_import_provisional;\nA multiline rationale",
        ):
            candidate = dict(record)
            candidate["oracle"] = oracle
            with self.subTest(oracle=oracle), self.assertRaisesRegex(
                RecordError, "oracle"
            ):
                parse_minimal_pair_challenge(candidate)

    def test_duplicate_requested_defect_fails(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicates"):
            generate_challenge_templates(
                (DefectType.ROLE_RELABELING, DefectType.ROLE_RELABELING)
            )

    def test_custom_identifier_is_supported_but_strict(self) -> None:
        challenge = generate_challenge_template(
            DefectType.REPAIR_PROVENANCE,
            challenge_id="MP-CUSTOM-1",
        )
        self.assertEqual(challenge.challenge_id, "MP-CUSTOM-1")
        with self.assertRaisesRegex(ValueError, "stable identifier"):
            generate_challenge_template(
                DefectType.REPAIR_PROVENANCE,
                challenge_id="contains spaces",
            )

    def test_parser_rejects_unknown_field_and_changed_limit(self) -> None:
        record = generate_challenge_template(DefectType.INDUCTIVE_WARRANT).to_dict()
        record["pass_count"] = 10
        with self.assertRaises(RecordError):
            parse_minimal_pair_challenge(record)
        record = generate_challenge_template(DefectType.INDUCTIVE_WARRANT).to_dict()
        record["epistemic_limit"] = "Ten passes make the model probable."
        with self.assertRaises(PolicyViolation):
            parse_minimal_pair_challenge(record)


class HardeningAssessmentTests(unittest.TestCase):
    def assessment(self, **changes: object):
        arguments: dict[str, object] = {
            "assessment_id": "HA-1",
            "baseline_id": "MODEL-1",
            "revision_id": "MODEL-2",
            "preserved_dimensions": ALL_PRESERVED,
            "gain_witness_refs": ("WITNESS-1",),
            "preservation_review_refs": ("PRESERVATION-REVIEW-1",),
            "human_decision_refs": ("DECISION-1",),
            "justification_bases": (JustificationBasis.COUNTEREXAMPLE,),
        }
        arguments.update(changes)
        return assess_revision(**arguments)  # type: ignore[arg-type]

    def test_plain_reference_strings_cannot_authorize_hardening(self) -> None:
        assessment = self.assessment(
            excluded_countermodels=("CM-role-swap",),
            gain_witness_refs=("BOGUS-WITNESS-REF",),
            preservation_review_refs=("BOGUS-REVIEW-REF",),
            human_decision_refs=("BOGUS-DECISION-REF",),
        )
        self.assertEqual(assessment.status, HardeningStatus.UNRESOLVED)
        self.assertIn("unrefuted", assessment.epistemic_limit.lower())
        self.assertNotIn("score", assessment.to_dict())

    def test_plain_reference_strings_cannot_authorize_resolved_ambiguity(self) -> None:
        assessment = self.assessment(resolved_ambiguities=("role-boundary",))
        self.assertEqual(assessment.status, HardeningStatus.UNRESOLVED)

    def test_no_strict_gain_is_no_hardening(self) -> None:
        self.assertEqual(self.assessment().status, HardeningStatus.NO_HARDENING)

    def test_each_known_regression_defeats_hardening(self) -> None:
        regressions = {
            "new_countermodels": ("CM-new",),
            "lost_intended_cases": ("artistic-creation",),
            "weakened_claims": ("necessity became possibility",),
            "collapsed_distinctions": ("conjecture versus criticism",),
        }
        for field, value in regressions.items():
            with self.subTest(field=field):
                assessment = self.assessment(
                    excluded_countermodels=("CM-old",),
                    **{field: value},
                )
                self.assertEqual(assessment.status, HardeningStatus.NO_HARDENING)

    def test_external_decision_gap_remains_unresolved_before_human_triage(self) -> None:
        assessment = self.assessment(
            excluded_countermodels=("CM-old",),
            research_issues=(issue(),),
            discovery_channels=("Primary archive", "AlphaXiv"),
        )
        self.assertEqual(
            assessment.status,
            HardeningStatus.UNRESOLVED,
        )
        self.assertEqual(len(assessment.research_warrants), 1)
        self.assertEqual(
            assessment.research_warrants[0].discovery_channels,
            ("Primary archive", "AlphaXiv"),
        )

    def test_known_regression_dominates_research_warrant(self) -> None:
        assessment = self.assessment(
            excluded_countermodels=("CM-old",),
            lost_intended_cases=("science",),
            research_issues=(issue(),),
        )
        self.assertEqual(assessment.status, HardeningStatus.NO_HARDENING)

    def test_internal_or_incomplete_issue_is_unresolved_not_research(self) -> None:
        cases = (
            issue(unknown_kind=UnknownKind.INTERNAL),
            issue(rivals=(rival("R1"),)),
            issue(relevant=False),
        )
        for source_issue in cases:
            with self.subTest(issue=source_issue):
                assessment = self.assessment(
                    excluded_countermodels=("CM-old",),
                    research_issues=(source_issue,),
                )
                self.assertEqual(assessment.status, HardeningStatus.UNRESOLVED)
                self.assertFalse(assessment.research_warrants)

    def test_missing_preservation_or_open_criticism_is_unresolved(self) -> None:
        missing = self.assessment(
            excluded_countermodels=("CM-old",),
            preserved_dimensions=(PreservationDimension.INTENDED_REACH_PRESERVED,),
        )
        open_criticism = self.assessment(
            excluded_countermodels=("CM-old",),
            unresolved_criticisms=("The scope boundary still moves.",),
        )
        self.assertEqual(missing.status, HardeningStatus.UNRESOLVED)
        self.assertEqual(open_criticism.status, HardeningStatus.UNRESOLVED)

    def test_unreviewed_gain_cannot_report_hardening(self) -> None:
        for missing in (
            "gain_witness_refs",
            "preservation_review_refs",
            "human_decision_refs",
            "justification_bases",
        ):
            with self.subTest(missing=missing):
                assessment = self.assessment(
                    excluded_countermodels=("CM-old",),
                    **{missing: ()},
                )
                self.assertEqual(assessment.status, HardeningStatus.UNRESOLVED)

    def test_pass_count_consensus_and_confidence_are_forbidden_bases(self) -> None:
        for basis in (
            JustificationBasis.PASS_COUNT,
            JustificationBasis.CONSENSUS,
            JustificationBasis.CONFIDENCE,
        ):
            with self.subTest(basis=basis), self.assertRaisesRegex(
                PolicyViolation,
                "cannot justify",
            ):
                self.assessment(
                    excluded_countermodels=("CM-old",),
                    justification_bases=(basis,),
                )

    def test_allowed_critical_bases_do_not_promote_without_a_strict_gain(self) -> None:
        assessment = self.assessment(
            justification_bases=(
                JustificationBasis.COUNTEREXAMPLE,
                JustificationBasis.DEDUCTIVE_CONSEQUENCE,
            )
        )
        self.assertEqual(assessment.status, HardeningStatus.NO_HARDENING)

    def test_repeated_or_permuted_named_inputs_do_not_become_a_score(self) -> None:
        forward = self.assessment(
            excluded_countermodels=("CM-b", "CM-a"),
            resolved_ambiguities=("B", "A"),
        )
        reverse = self.assessment(
            excluded_countermodels=("CM-a", "CM-b"),
            resolved_ambiguities=("A", "B"),
        )
        self.assertEqual(forward, reverse)
        with self.assertRaisesRegex(ValueError, "duplicates"):
            self.assessment(excluded_countermodels=("CM-a", "CM-a"))

    def test_assessment_has_no_truth_coercion(self) -> None:
        with self.assertRaisesRegex(TypeError, "no truth coercion"):
            bool(self.assessment(excluded_countermodels=("CM-old",)))

    def test_legacy_research_required_status_is_not_in_the_model_vocabulary(self) -> None:
        record = self.assessment(excluded_countermodels=("CM-old",)).to_dict()
        record["status"] = "SEMANTIC_REVISION_RESEARCH_REQUIRED"
        with self.assertRaisesRegex(RecordError, "hardening.status"):
            parse_hardening_assessment(record)

    def test_round_trip_recomputes_and_rejects_laundered_status(self) -> None:
        assessment = self.assessment(excluded_countermodels=("CM-old",))
        self.assertEqual(loads_hardening_assessment(dumps_record(assessment)), assessment)
        record = assessment.to_dict()
        record["status"] = HardeningStatus.HARDENING_UNREFUTED.value
        with self.assertRaisesRegex(PolicyViolation, "inconsistent"):
            parse_hardening_assessment(record)

    def test_unknown_scalar_evidence_fields_are_rejected(self) -> None:
        record = self.assessment(excluded_countermodels=("CM-old",)).to_dict()
        for field, value in (
            ("score", 1),
            ("pass_count", 1000),
            ("confidence", 99),
            ("consensus_votes", 20),
        ):
            candidate = dict(record)
            candidate[field] = value
            with self.subTest(field=field), self.assertRaises(RecordError):
                parse_hardening_assessment(candidate)

    def test_no_status_can_claim_confirmation_probability_or_truth(self) -> None:
        forbidden = ("CONFIRMED", "PROBABLE", "SUPPORTED", "TRUE")
        for status in HardeningStatus:
            for word in forbidden:
                self.assertNotIn(word, status.value)


class FormalizationReadinessTests(unittest.TestCase):
    def test_omitted_review_evidence_defaults_to_blocked(self) -> None:
        report = assess_formalization_readiness(
            report_id="FR-1",
            candidate_id="MODEL-2",
        )
        self.assertEqual(report.status, ReadinessStatus.BLOCKED)
        self.assertTrue(report.advisory)
        self.assertFalse(report.final)
        self.assertEqual(loads_formalization_readiness(dumps_record(report)), report)

    def test_plain_review_reference_cannot_authorize_readiness(self) -> None:
        report = assess_formalization_readiness(
            report_id="FR-1",
            candidate_id="MODEL-2",
            review_record_refs=("BOGUS-UNRESOLVED-REFERENCE",),
        )
        self.assertEqual(report.status, ReadinessStatus.BLOCKED)
        self.assertTrue(report.advisory)
        self.assertFalse(report.final)

        laundered = report.to_dict()
        laundered["status"] = ReadinessStatus.PROVISIONALLY_READY.value
        with self.assertRaisesRegex(PolicyViolation, "inconsistent"):
            loads_formalization_readiness(json.dumps(laundered))

    def test_each_required_semantic_gap_blocks_formalization(self) -> None:
        blockers = {
            "unresolved_semantic_roles": ("criticism target role",),
            "missing_positive_witnesses": ("scientific inquiry",),
            "missing_negative_witnesses": ("lookup table",),
            "ungrounded_primitives": ("Problem",),
            "undecided_source_forks": ("corroboration reading A versus B",),
        }
        for field, value in blockers.items():
            with self.subTest(field=field):
                report = assess_formalization_readiness(
                    report_id="FR-1",
                    candidate_id="MODEL-2",
                    **{field: value},
                )
                self.assertEqual(report.status, ReadinessStatus.BLOCKED)

    def test_readiness_cannot_be_final_or_truth_coerced(self) -> None:
        with self.assertRaisesRegex(PolicyViolation, "advisory"):
            FormalizationReadiness(
                report_id="FR-1",
                candidate_id="MODEL-2",
                status=ReadinessStatus.PROVISIONALLY_READY,
                unresolved_semantic_roles=(),
                missing_positive_witnesses=(),
                missing_negative_witnesses=(),
                ungrounded_primitives=(),
                undecided_source_forks=(),
                review_record_refs=("SEMANTIC-REVIEW-1",),
                final=True,
            )
        with self.assertRaisesRegex(TypeError, "advisory"):
            bool(
                assess_formalization_readiness(
                    report_id="FR-1",
                    candidate_id="MODEL-2",
                )
            )

    def test_parser_rejects_false_ready_status_with_blocker(self) -> None:
        report = assess_formalization_readiness(
            report_id="FR-1",
            candidate_id="MODEL-2",
            ungrounded_primitives=("Knowledge",),
        )
        record = report.to_dict()
        record["status"] = ReadinessStatus.PROVISIONALLY_READY.value
        with self.assertRaisesRegex(PolicyViolation, "inconsistent"):
            loads_formalization_readiness(json.dumps(record))

    def test_parser_rejects_non_boolean_advisory_marker(self) -> None:
        record = assess_formalization_readiness(
            report_id="FR-1",
            candidate_id="MODEL-2",
        ).to_dict()
        record["advisory"] = 1
        with self.assertRaisesRegex(RecordError, "Booleans"):
            loads_formalization_readiness(json.dumps(record))


if __name__ == "__main__":
    unittest.main()
