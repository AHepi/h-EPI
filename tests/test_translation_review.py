from __future__ import annotations

import copy
import errno
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from creib.canonical import canonical_bytes, domain_digest
from creib.errors import PolicyViolation, RecordError
from creib.forge.translation_review import (
    BRANCH_DISPOSITION_SCHEMA,
    INTERPRETATION_DOMAIN,
    INTERPRETATION_SET_SCHEMA,
    MODEL_EFFECT_DOMAIN,
    REVIEW_SCHEMA,
    REVIEW_SCHEMA_REF,
    SNAPSHOT_SCHEMA,
    TRANSLATION_DECISION_SCHEMA,
    TranslationReviewError,
    compute_branch_disposition_id,
    compute_interpretation_id,
    compute_interpretation_set_id,
    compute_translation_decision_id,
    compute_translation_review_id,
    compute_translation_scope_id,
    compute_translation_snapshot_id,
    compute_translation_variant_id,
    publish_translation_review,
    translation_review_bindings,
    translation_review_surface,
    validate_translation_review,
    verify_translation_review_chain,
)


def content_id(prefix: str, seed: str) -> str:
    return f"{prefix}:" + domain_digest("test.translation-review", seed).removeprefix(
        "sha256:"
    )


class TranslationReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.review_dir = self.root / "reviews"
        self.review_dir.mkdir()

        self.span_ids = sorted(
            [content_id("TSPAN", "target"), content_id("TSPAN", "context")]
        )
        self.obligation_id = content_id("TO", "obligation")
        self.charter_id = content_id("TCHAR", "charter")
        self.graph_id = content_id("TOG", "graph")
        first = self.branch("endpoint is content", "EndpointContent")
        second = self.branch("endpoint is a problem situation", "EndpointProblem")
        self.interpretation_set = {
            "schema_version": INTERPRETATION_SET_SCHEMA,
            "interpretation_set_id": "TIS:" + "0" * 64,
            "supersedes_interpretation_set_id": None,
            "charter_id": self.charter_id,
            "graph_id": self.graph_id,
            "question": "What role does the source assign to the endpoint?",
            "source_span_ids": self.span_ids,
            "obligation_ids": [self.obligation_id],
            "rival_relation": "EXCLUSIVE",
            "admissible_branch_sets": sorted(
                [[first["interpretation_id"]], [second["interpretation_id"]]],
                key=canonical_bytes,
            ),
            "branches": sorted(
                [first, second], key=lambda item: str(item["interpretation_id"])
            ),
            "proposal_status": "PROPOSED",
            "provenance": {
                "producer_kind": "HUMAN",
                "producer_id": "test-author",
                "created_at": "2026-09-03T00:00:00Z",
                "generation_record_ids": [],
            },
        }
        self.interpretation_set[
            "interpretation_set_id"
        ] = compute_interpretation_set_id(self.interpretation_set)
        self.snapshot = self.make_snapshot(
            [str(self.interpretation_set["interpretation_set_id"])]
        )
        self.sets = (self.interpretation_set,)
        self.bindings = translation_review_bindings(self.snapshot)
        self.surface = translation_review_surface(self.snapshot, self.sets)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def branch(
        self, statement: str, affected: str, *, projected: bool = True
    ) -> dict[str, object]:
        branch: dict[str, object] = {
            "interpretation_id": "TI:" + "0" * 64,
            "claim_kind": "SOURCE_INTERPRETATION",
            "statement": statement,
            "source_span_ids": self.span_ids,
            "interpreted_obligation_ids": [self.obligation_id],
            "preserved_feature_ids": [],
            "model_effect": {
                "status": "DECLARED" if projected else "UNPROJECTED",
                "effect_statement": f"Use {affected} in the neutral model.",
                "affected_element_keys": [affected] if projected else [],
            },
            "discriminating_consequences": [
                f"The model must distinguish the {affected} role."
            ],
            "falsifier_conditions": [
                f"A bound passage excludes the {affected} reading."
            ],
            "known_loss_risks": [],
            "proposal_status": "PROPOSED",
        }
        branch["interpretation_id"] = compute_interpretation_id(branch)
        return branch

    def make_snapshot(
        self,
        set_ids: list[str],
        *,
        model_seed: str = "model",
        predecessor_snapshot_id: str | None = None,
    ) -> dict[str, object]:
        snapshot: dict[str, object] = {
            "schema_version": SNAPSHOT_SCHEMA,
            "snapshot_id": "TSN:" + "0" * 64,
            "predecessor_snapshot_id": predecessor_snapshot_id,
            "document_ids": [content_id("TDOC", "document")],
            "span_ids": self.span_ids,
            "charter_id": self.charter_id,
            "graph_id": self.graph_id,
            "interpretation_set_ids": sorted(set_ids),
            "signature_id": content_id("TNS", "signature"),
            "model_id": content_id("TNM", model_seed),
            "import_ids": [],
            "bridge_id": content_id("TBR", "bridge"),
            "unresolved_record_ids": [],
            "record_closure_sha256": domain_digest(
                "test.translation-closure", model_seed
            ),
        }
        snapshot["snapshot_id"] = compute_translation_snapshot_id(snapshot)
        return snapshot

    def make_interpretation_context(
        self,
        rival_relation: str,
        *,
        branches: list[dict[str, object]] | None = None,
    ) -> tuple[
        dict[str, object],
        dict[str, object],
        dict[str, object],
        dict[str, object],
    ]:
        interpretation_set = copy.deepcopy(self.interpretation_set)
        interpretation_set["rival_relation"] = rival_relation
        if branches is not None:
            interpretation_set["branches"] = sorted(
                copy.deepcopy(branches),
                key=lambda item: str(item["interpretation_id"]),
            )
        elif rival_relation == "PARTIALLY_COMPATIBLE":
            interpretation_set["branches"] = sorted(
                [
                    *interpretation_set["branches"],
                    self.branch("endpoint is an activity", "EndpointActivity"),
                ],
                key=lambda item: str(item["interpretation_id"]),
            )
        branch_ids = [
            str(item["interpretation_id"])
            for item in interpretation_set["branches"]
        ]
        admissible = [[branch_id] for branch_id in branch_ids]
        if rival_relation == "OVERLAPPING":
            admissible.append(branch_ids)
        elif rival_relation == "PARTIALLY_COMPATIBLE":
            admissible.append(sorted(branch_ids[:2]))
        interpretation_set["admissible_branch_sets"] = sorted(
            admissible,
            key=canonical_bytes,
        )
        interpretation_set["interpretation_set_id"] = compute_interpretation_set_id(
            interpretation_set
        )
        snapshot = self.make_snapshot(
            [str(interpretation_set["interpretation_set_id"])],
            model_seed=f"model-{rival_relation}-{len(interpretation_set['branches'])}",
        )
        bindings = translation_review_bindings(snapshot)
        surface = translation_review_surface(snapshot, [interpretation_set])
        return interpretation_set, snapshot, bindings, surface

    def prose(self, reason: str = "This is a fallible scoped review.") -> dict[str, object]:
        return {
            "plain_language_reading": "The source leaves rival endpoint roles to review.",
            "reason": reason,
            "model_effect_assessment": "The alternatives change the endpoint carrier.",
            "remaining_uncertainty": "The wider source context may reopen this decision.",
        }

    def review_scope(
        self,
        *,
        charter_id: str | None = None,
        purpose: str = "Evaluate the endpoint-role translation for downstream comparison.",
        system_boundary: str = "The selected neutral model and its declared bridge only.",
        in_scope: list[str] | None = None,
    ) -> dict[str, object]:
        scope: dict[str, object] = {
            "scope_id": "TRS:" + "0" * 64,
            "charter_id": charter_id or self.charter_id,
            "purpose": purpose,
            "system_boundary": system_boundary,
            "in_scope": sorted(in_scope or ["Endpoint-role interpretation"]),
        }
        scope["scope_id"] = compute_translation_scope_id(scope)
        return scope

    def review(
        self,
        *,
        sequence: int = 1,
        previous: str | None = None,
        transition: str = "GENESIS",
        bindings: dict[str, object] | None = None,
        surface: dict[str, object] | None = None,
        dispositions: list[dict[str, object]] | None = None,
        decisions: list[dict[str, object]] | None = None,
    ) -> dict[str, object]:
        record: dict[str, object] = {
            "$schema": REVIEW_SCHEMA_REF,
            "schema_version": REVIEW_SCHEMA,
            "record_type": "translation_review",
            "review_id": "TR:" + "0" * 64,
            "sequence": sequence,
            "previous_review_id": previous,
            "transition_kind": transition,
            "transition_reason": "Preserve an exact human review step.",
            "created_on": "2026-09-03",
            "bindings": copy.deepcopy(bindings or self.bindings),
            "review_surface": copy.deepcopy(surface or self.surface),
            "branch_dispositions": sorted(
                copy.deepcopy(dispositions or []),
                key=lambda item: str(item["disposition_id"]),
            ),
            "translation_decisions": sorted(
                copy.deepcopy(decisions or []),
                key=lambda item: str(item["decision_id"]),
            ),
            "reviewer_kind": "HUMAN",
            "reviewer_authentication": "NOT_ESTABLISHED_BY_RECORD",
            "machine_generated": False,
            "epistemic_status": "UNRESOLVED",
            "epistemic_effect": "TRANSLATION_REVIEW_WORKFLOW_ONLY",
            "can_confirm_source_meaning": False,
            "can_promote_model": False,
            "semantic_verdict": None,
        }
        record["review_id"] = compute_translation_review_id(record)
        return record

    def branch_disposition(
        self,
        *,
        disposition: str = "EXCLUDED_FOR_SCOPE",
        sequence: int = 1,
        previous: str | None = None,
        bindings: dict[str, object] | None = None,
        surface: dict[str, object] | None = None,
        set_index: int = 0,
        interpretation_index: int = 0,
        superseded: dict[str, object] | None = None,
        changed: list[str] | None = None,
    ) -> dict[str, object]:
        chosen_surface = surface or self.surface
        set_surface = chosen_surface["interpretation_sets"][set_index]
        branch_surface = set_surface["interpretations"][interpretation_index]
        record: dict[str, object] = {
            "schema_version": BRANCH_DISPOSITION_SCHEMA,
            "record_type": "translation_branch_disposition",
            "disposition_id": "BD:" + "0" * 64,
            "interpretation_set_id": set_surface["interpretation_set_id"],
            "interpretation_id": branch_surface["interpretation_id"],
            "decision_sequence": sequence,
            "previous_disposition_id": previous,
            "created_on": "2026-09-03",
            "bindings": copy.deepcopy(bindings or self.bindings),
            "disposition": disposition,
            "reviewed_source_span_ids": list(set_surface["source_span_ids"]),
            "considered_interpretation_ids": [
                item["interpretation_id"] for item in set_surface["interpretations"]
            ],
            "reviewed_model_effect_sha256": branch_surface[
                "model_effect_sha256"
            ],
            "reviewer_prose": self.prose(),
            "superseded_bindings": copy.deepcopy(superseded),
            "changed_binding_pointers": list(changed or []),
            "reviewer_kind": "HUMAN",
            "reviewer_authentication": "NOT_ESTABLISHED_BY_RECORD",
            "machine_generated": False,
            "epistemic_effect": "BRANCH_WORKFLOW_ONLY",
            "can_authorize_translation": False,
            "can_confirm_source_meaning": False,
            "semantic_verdict": None,
        }
        record["disposition_id"] = compute_branch_disposition_id(record)
        return record

    def stale_dispositions(
        self,
        *,
        predecessor_surface: dict[str, object],
        predecessor_bindings: dict[str, object],
        successor_bindings: dict[str, object],
        previous_dispositions: list[dict[str, object]] | None = None,
    ) -> list[dict[str, object]]:
        previous_heads: dict[str, dict[str, object]] = {}
        for item in previous_dispositions or []:
            branch_id = str(item["interpretation_id"])
            current = previous_heads.get(branch_id)
            if current is None or int(item["decision_sequence"]) > int(
                current["decision_sequence"]
            ):
                previous_heads[branch_id] = item
        changed_pointers = sorted(
            f"/{key}"
            for key in predecessor_bindings
            if predecessor_bindings[key] != successor_bindings[key]
        )
        stale: list[dict[str, object]] = []
        for set_index, set_surface in enumerate(
            predecessor_surface["interpretation_sets"]
        ):
            for interpretation_index, interpretation in enumerate(
                set_surface["interpretations"]
            ):
                branch_id = str(interpretation["interpretation_id"])
                previous = previous_heads.get(branch_id)
                stale.append(
                    self.branch_disposition(
                        disposition="STALE_BY_BINDING_CHANGE",
                        sequence=(
                            1
                            if previous is None
                            else int(previous["decision_sequence"]) + 1
                        ),
                        previous=(
                            None
                            if previous is None
                            else str(previous["disposition_id"])
                        ),
                        bindings=successor_bindings,
                        surface=predecessor_surface,
                        set_index=set_index,
                        interpretation_index=interpretation_index,
                        superseded=predecessor_bindings,
                        changed=changed_pointers,
                    )
                )
        return stale

    def decision(
        self,
        *,
        disposition: str = "AUTHORIZE_SCOPED_USE",
        sequence: int = 1,
        previous: str | None = None,
        bindings: dict[str, object] | None = None,
        surface: dict[str, object] | None = None,
        selected_branches: list[tuple[str, str]] | None = None,
        scope_binding: dict[str, object] | None = None,
    ) -> dict[str, object]:
        chosen_surface = surface or self.surface
        all_interpretations = [
            interpretation
            for interpretation_set in chosen_surface["interpretation_sets"]
            for interpretation in interpretation_set["interpretations"]
        ]
        interpretation_index = {
            str(interpretation["interpretation_id"]): interpretation
            for interpretation in all_interpretations
        }
        if selected_branches is None:
            first_set = chosen_surface["interpretation_sets"][0]
            selected = first_set["interpretations"][1]
            selected_branches = [
                (
                    str(first_set["interpretation_set_id"]),
                    str(selected["interpretation_id"]),
                )
            ]
        selections = sorted(
            [
                {
                    "interpretation_set_id": set_id,
                    "interpretation_id": branch_id,
                }
                for set_id, branch_id in selected_branches
            ],
            key=lambda item: (
                str(item["interpretation_set_id"]),
                str(item["interpretation_id"]),
            ),
        )
        selected_effects = sorted(
            {
                str(interpretation_index[branch_id]["model_effect_sha256"])
                for _set_id, branch_id in selected_branches
                if branch_id in interpretation_index
            }
        )
        variant: dict[str, object] = {
            "variant_id": "TV:" + "0" * 64,
            "model_id": chosen_surface["model_id"],
            "selections": selections,
            "model_effect_sha256s": selected_effects,
            "reason": "Carry one explicit rival as the scoped translation variant.",
        }
        variant["variant_id"] = compute_translation_variant_id(variant)
        record: dict[str, object] = {
            "schema_version": TRANSLATION_DECISION_SCHEMA,
            "record_type": "translation_decision",
            "decision_id": "TD:" + "0" * 64,
            "decision_sequence": sequence,
            "previous_decision_id": previous,
            "created_on": "2026-09-03",
            "bindings": copy.deepcopy(bindings or self.bindings),
            "scope_binding": copy.deepcopy(
                scope_binding or self.review_scope()
            ),
            "disposition": disposition,
            "reviewed_source_span_ids": list(chosen_surface["source_span_ids"]),
            "considered_interpretation_ids": sorted(
                str(item["interpretation_id"]) for item in all_interpretations
            ),
            "reviewed_model_effects": sorted(
                [
                    {
                        "interpretation_id": item["interpretation_id"],
                        "model_effect_sha256": item["model_effect_sha256"],
                    }
                    for item in all_interpretations
                ],
                key=lambda item: str(item["interpretation_id"]),
            ),
            "authorized_variants": [variant]
            if disposition == "AUTHORIZE_SCOPED_USE"
            else [],
            "reviewer_prose": self.prose(),
            "reviewer_kind": "HUMAN",
            "reviewer_authentication": "NOT_ESTABLISHED_BY_RECORD",
            "machine_generated": False,
            "epistemic_effect": "SCOPED_WORKFLOW_DECISION_ONLY",
            "can_confirm_unique_reading": False,
            "can_accept_project_import": False,
            "source_count_can_decide": False,
            "provider_agreement_can_decide": False,
            "source_truth_verdict": None,
            "semantic_verdict": None,
        }
        record["decision_id"] = compute_translation_decision_id(record)
        return record

    def publish(self, review: dict[str, object], expected: str | None) -> Path:
        return publish_translation_review(
            self.review_dir,
            review,
            expected_head_review_id=expected,
            snapshot=self.snapshot,
            interpretation_sets=self.sets,
        )

    def write_unchecked_lineage(
        self,
        directory: Path,
        reviews: list[dict[str, object]],
    ) -> None:
        directory.mkdir()
        for review in reviews:
            payload = canonical_bytes(review) + b"\n"
            record_name = f"{str(review['review_id']).replace(':', '-')}.json"
            previous = review["previous_review_id"]
            claim_token = (
                "GENESIS"
                if previous is None
                else str(previous).removeprefix("TR:")
            )
            (directory / record_name).write_bytes(payload)
            (directory / f"NEXT-{claim_token}.claim").write_bytes(payload)

    def test_review_surface_binds_every_rival_span_and_model_effect(self) -> None:
        self.assertEqual(self.surface["source_span_ids"], self.span_ids)
        set_surface = self.surface["interpretation_sets"][0]
        self.assertEqual(set_surface["question"], self.interpretation_set["question"])
        self.assertEqual(set_surface["rival_relation"], "EXCLUSIVE")
        self.assertEqual(len(set_surface["interpretations"]), 2)
        for source_branch, interpretation in zip(
            self.interpretation_set["branches"], set_surface["interpretations"]
        ):
            review_material = copy.deepcopy(interpretation)
            effect_digest = review_material.pop("model_effect_sha256")
            self.assertEqual(review_material, source_branch)
            self.assertEqual(interpretation["model_effect"]["status"], "DECLARED")
            self.assertTrue(str(effect_digest).startswith("sha256:"))

        review = self.review()
        validate_translation_review(
            review,
            expected_bindings=self.bindings,
            expected_surface=self.surface,
        )
        changed = copy.deepcopy(review)
        changed["review_surface"]["source_span_ids"].pop()
        changed["review_id"] = compute_translation_review_id(changed)
        with self.assertRaisesRegex(PolicyViolation, "omitted or changed"):
            validate_translation_review(
                changed,
                expected_bindings=self.bindings,
                expected_surface=self.surface,
            )

        reworded = copy.deepcopy(review)
        reworded_branch = reworded["review_surface"]["interpretation_sets"][0][
            "interpretations"
        ][0]
        reworded_branch["statement"] += " (silently changed)"
        reworded["review_id"] = compute_translation_review_id(reworded)
        with self.assertRaisesRegex(RecordError, "branch material"):
            validate_translation_review(
                reworded,
                expected_bindings=self.bindings,
                expected_surface=reworded["review_surface"],
            )

    def test_exclusive_variant_requires_exactly_one_branch(self) -> None:
        set_surface = self.surface["interpretation_sets"][0]
        selected = [
            (
                str(set_surface["interpretation_set_id"]),
                str(branch["interpretation_id"]),
            )
            for branch in set_surface["interpretations"]
        ]
        decision = self.decision(selected_branches=selected)
        review = self.review(
            sequence=2,
            previous=content_id("TR", "plural-exclusive-parent"),
            transition="SAME_BINDINGS",
            decisions=[decision],
        )
        with self.assertRaisesRegex(PolicyViolation, "not explicitly declared admissible"):
            validate_translation_review(
                review,
                expected_bindings=self.bindings,
                expected_surface=self.surface,
            )

    def test_overlapping_relation_allows_plural_branch_subset(self) -> None:
        _interpretation_set, _snapshot, bindings, surface = (
            self.make_interpretation_context("OVERLAPPING")
        )
        set_surface = surface["interpretation_sets"][0]
        selected = [
            (
                str(set_surface["interpretation_set_id"]),
                str(branch["interpretation_id"]),
            )
            for branch in set_surface["interpretations"]
        ]
        decision = self.decision(
            bindings=bindings,
            surface=surface,
            selected_branches=selected,
        )
        review = self.review(
            sequence=2,
            previous=content_id("TR", "plural-overlapping-parent"),
            transition="SAME_BINDINGS",
            bindings=bindings,
            surface=surface,
            decisions=[decision],
        )
        validate_translation_review(
            review,
            expected_bindings=bindings,
            expected_surface=surface,
        )

    def test_partially_compatible_allows_only_explicit_combinations(
        self,
    ) -> None:
        _interpretation_set, _snapshot, bindings, surface = (
            self.make_interpretation_context("PARTIALLY_COMPATIBLE")
        )
        set_surface = surface["interpretation_sets"][0]
        all_branches = [
            (
                str(set_surface["interpretation_set_id"]),
                str(branch["interpretation_id"]),
            )
            for branch in set_surface["interpretations"]
        ]
        singleton = self.decision(
            bindings=bindings,
            surface=surface,
            selected_branches=[all_branches[0]],
        )
        validate_translation_review(
            self.review(
                sequence=2,
                previous=content_id("TR", "partial-singleton-parent"),
                transition="SAME_BINDINGS",
                bindings=bindings,
                surface=surface,
                decisions=[singleton],
            ),
            expected_bindings=bindings,
            expected_surface=surface,
        )

        admitted_ids = next(
            combination
            for combination in set_surface["admissible_branch_sets"]
            if len(combination) > 1
        )
        admitted = self.decision(
            bindings=bindings,
            surface=surface,
            selected_branches=[
                (str(set_surface["interpretation_set_id"]), str(branch_id))
                for branch_id in admitted_ids
            ],
        )
        validate_translation_review(
            self.review(
                sequence=2,
                previous=content_id("TR", "partial-admitted-parent"),
                transition="SAME_BINDINGS",
                bindings=bindings,
                surface=surface,
                decisions=[admitted],
            ),
            expected_bindings=bindings,
            expected_surface=surface,
        )

        full_set = self.decision(
            bindings=bindings,
            surface=surface,
            selected_branches=all_branches,
        )
        with self.assertRaisesRegex(PolicyViolation, "not explicitly declared admissible"):
            validate_translation_review(
                self.review(
                    sequence=2,
                    previous=content_id("TR", "partial-plural-parent"),
                    transition="SAME_BINDINGS",
                    bindings=bindings,
                    surface=surface,
                    decisions=[full_set],
                ),
                expected_bindings=bindings,
                expected_surface=surface,
            )

    def test_variant_rejects_duplicate_or_absent_branches(self) -> None:
        set_surface = self.surface["interpretation_sets"][0]
        selection = (
            str(set_surface["interpretation_set_id"]),
            str(set_surface["interpretations"][1]["interpretation_id"]),
        )
        duplicate = self.decision(selected_branches=[selection, selection])
        with self.assertRaises(RecordError):
            validate_translation_review(
                self.review(
                    sequence=2,
                    previous=content_id("TR", "duplicate-parent"),
                    transition="SAME_BINDINGS",
                    decisions=[duplicate],
                ),
                expected_bindings=self.bindings,
                expected_surface=self.surface,
            )

        absent = self.decision()
        variant = absent["authorized_variants"][0]
        variant["selections"][0]["interpretation_id"] = content_id(
            "TI", "absent-branch"
        )
        variant["variant_id"] = compute_translation_variant_id(variant)
        absent["decision_id"] = compute_translation_decision_id(absent)
        with self.assertRaisesRegex(PolicyViolation, "absent rival"):
            validate_translation_review(
                self.review(
                    sequence=2,
                    previous=content_id("TR", "absent-parent"),
                    transition="SAME_BINDINGS",
                    decisions=[absent],
                ),
                expected_bindings=self.bindings,
                expected_surface=self.surface,
            )

    def test_variant_rejects_unprojected_branch(self) -> None:
        branches = [
            self.branch("endpoint is content", "EndpointContent", projected=False),
            self.branch("endpoint is a problem situation", "EndpointProblem"),
        ]
        _interpretation_set, _snapshot, bindings, surface = (
            self.make_interpretation_context("OVERLAPPING", branches=branches)
        )
        set_surface = surface["interpretation_sets"][0]
        unprojected = next(
            branch
            for branch in set_surface["interpretations"]
            if branch["model_effect"]["status"] == "UNPROJECTED"
        )
        decision = self.decision(
            bindings=bindings,
            surface=surface,
            selected_branches=[
                (
                    str(set_surface["interpretation_set_id"]),
                    str(unprojected["interpretation_id"]),
                )
            ],
        )
        with self.assertRaisesRegex(PolicyViolation, "unprojected"):
            validate_translation_review(
                self.review(
                    sequence=2,
                    previous=content_id("TR", "unprojected-parent"),
                    transition="SAME_BINDINGS",
                    bindings=bindings,
                    surface=surface,
                    decisions=[decision],
                ),
                expected_bindings=bindings,
                expected_surface=surface,
            )

    def test_authorization_binds_exact_scope_and_current_model(self) -> None:
        decision = self.decision()
        scope = decision["scope_binding"]
        self.assertEqual(scope["charter_id"], self.charter_id)
        self.assertTrue(scope["in_scope"])

        changed_scope = copy.deepcopy(decision)
        changed_scope["scope_binding"]["purpose"] += " Changed after review."
        changed_scope["decision_id"] = compute_translation_decision_id(changed_scope)
        with self.assertRaisesRegex(RecordError, "scope content-addressed ID"):
            validate_translation_review(
                self.review(
                    sequence=2,
                    previous=content_id("TR", "changed-scope-parent"),
                    transition="SAME_BINDINGS",
                    decisions=[changed_scope],
                ),
                expected_bindings=self.bindings,
                expected_surface=self.surface,
            )

        changed_model = copy.deepcopy(decision)
        variant = changed_model["authorized_variants"][0]
        variant["model_id"] = content_id("TNM", "other-model")
        variant["variant_id"] = compute_translation_variant_id(variant)
        changed_model["decision_id"] = compute_translation_decision_id(changed_model)
        with self.assertRaisesRegex(PolicyViolation, "current neutral model"):
            validate_translation_review(
                self.review(
                    sequence=2,
                    previous=content_id("TR", "changed-model-parent"),
                    transition="SAME_BINDINGS",
                    decisions=[changed_model],
                ),
                expected_bindings=self.bindings,
                expected_surface=self.surface,
            )

    def test_plural_variant_binds_exact_selected_effect_closure(self) -> None:
        _interpretation_set, _snapshot, bindings, surface = (
            self.make_interpretation_context("OVERLAPPING")
        )
        set_surface = surface["interpretation_sets"][0]
        selected = [
            (
                str(set_surface["interpretation_set_id"]),
                str(branch["interpretation_id"]),
            )
            for branch in set_surface["interpretations"]
        ]
        decision = self.decision(
            bindings=bindings,
            surface=surface,
            selected_branches=selected,
        )
        variant = decision["authorized_variants"][0]
        variant["model_effect_sha256s"].pop()
        variant["variant_id"] = compute_translation_variant_id(variant)
        decision["decision_id"] = compute_translation_decision_id(decision)
        with self.assertRaisesRegex(PolicyViolation, "exact selected model-effect"):
            validate_translation_review(
                self.review(
                    sequence=2,
                    previous=content_id("TR", "effect-closure-parent"),
                    transition="SAME_BINDINGS",
                    bindings=bindings,
                    surface=surface,
                    decisions=[decision],
                ),
                expected_bindings=bindings,
                expected_surface=surface,
            )

    def test_genesis_is_no_clobber_and_requires_explicit_head(self) -> None:
        genesis = self.review()
        path = self.publish(genesis, None)
        payload = canonical_bytes(genesis) + b"\n"
        self.assertEqual(path.read_bytes(), payload)
        self.assertEqual((self.review_dir / "NEXT-GENESIS.claim").read_bytes(), payload)
        self.assertTrue(os.path.samefile(path, self.review_dir / "NEXT-GENESIS.claim"))
        state = verify_translation_review_chain(
            self.review_dir,
            str(genesis["review_id"]),
            expected_bindings=self.bindings,
            expected_surface=self.surface,
        )
        self.assertEqual(state.workflow_status, "AWAITING_HUMAN_REVIEW")
        with self.assertRaises(TranslationReviewError):
            verify_translation_review_chain(self.review_dir, None)

    def test_only_explicit_case_decision_authorizes_scoped_use(self) -> None:
        genesis = self.review()
        self.publish(genesis, None)
        excluded = self.branch_disposition()
        without_decision = self.review(
            sequence=2,
            previous=str(genesis["review_id"]),
            transition="SAME_BINDINGS",
            dispositions=[excluded],
        )
        self.publish(without_decision, str(genesis["review_id"]))
        state = verify_translation_review_chain(
            self.review_dir, str(without_decision["review_id"])
        )
        self.assertEqual(state.workflow_status, "AWAITING_HUMAN_REVIEW")

        selected = self.decision()
        authorized = self.review(
            sequence=3,
            previous=str(without_decision["review_id"]),
            transition="SAME_BINDINGS",
            dispositions=[excluded],
            decisions=[selected],
        )
        self.publish(authorized, str(without_decision["review_id"]))
        state = verify_translation_review_chain(
            self.review_dir, str(authorized["review_id"])
        )
        self.assertEqual(
            state.workflow_status,
            "SCOPED_USE_SELECTED_AUTHENTICATION_REQUIRED",
        )
        self.assertEqual(state.current_decision_id, selected["decision_id"])
        self.assertEqual(
            state.reviewer_authentication,
            "NOT_ESTABLISHED_BY_RECORD",
        )
        self.assertEqual(state.current_scope_binding, selected["scope_binding"])
        self.assertEqual(state.authorized_variants, tuple(selected["authorized_variants"]))

    def test_decision_cannot_omit_a_rival_or_model_effect(self) -> None:
        genesis = self.review()
        self.publish(genesis, None)
        decision = self.decision(disposition="SUSPEND_UNRESOLVED")
        decision["considered_interpretation_ids"].pop()
        decision["decision_id"] = compute_translation_decision_id(decision)
        successor = self.review(
            sequence=2,
            previous=str(genesis["review_id"]),
            transition="SAME_BINDINGS",
            decisions=[decision],
        )
        with self.assertRaisesRegex(PolicyViolation, "omitted or changed an alternative"):
            self.publish(successor, str(genesis["review_id"]))

    def test_human_prose_and_actor_boundary_are_content_addressed(self) -> None:
        decision = self.decision(disposition="SUSPEND_UNRESOLVED")
        original_id = decision["decision_id"]
        decision["reviewer_prose"]["reason"] = "A different human reason."
        with self.assertRaisesRegex(RecordError, "content-addressed ID mismatch"):
            validate_translation_review(
                self.review(
                    sequence=2,
                    previous=content_id("TR", "parent"),
                    transition="SAME_BINDINGS",
                    decisions=[decision],
                ),
                expected_bindings=self.bindings,
                expected_surface=self.surface,
            )
        self.assertEqual(decision["decision_id"], original_id)

        machine = self.decision(disposition="SUSPEND_UNRESOLVED")
        machine["reviewer_kind"] = "MACHINE"
        machine["machine_generated"] = True
        machine["decision_id"] = compute_translation_decision_id(machine)
        with self.assertRaises(RecordError):
            validate_translation_review(
                self.review(
                    sequence=2,
                    previous=content_id("TR", "parent-2"),
                    transition="SAME_BINDINGS",
                    decisions=[machine],
                ),
                expected_bindings=self.bindings,
                expected_surface=self.surface,
            )

        self_asserted_authentication = self.review()
        self_asserted_authentication["reviewer_authentication"] = "AUTHENTICATED"
        self_asserted_authentication["review_id"] = compute_translation_review_id(
            self_asserted_authentication
        )
        with self.assertRaises(RecordError):
            validate_translation_review(
                self_asserted_authentication,
                expected_bindings=self.bindings,
                expected_surface=self.surface,
            )

    def test_successor_cannot_drop_history(self) -> None:
        genesis = self.review()
        self.publish(genesis, None)
        decision = self.decision(disposition="SUSPEND_UNRESOLVED")
        second = self.review(
            sequence=2,
            previous=str(genesis["review_id"]),
            transition="SAME_BINDINGS",
            decisions=[decision],
        )
        self.publish(second, str(genesis["review_id"]))
        dropped = self.review(
            sequence=3,
            previous=str(second["review_id"]),
            transition="SAME_BINDINGS",
        )
        with self.assertRaisesRegex(PolicyViolation, "dropped or changed"):
            self.publish(dropped, str(second["review_id"]))

    def test_changed_snapshot_resets_old_authorization(self) -> None:
        genesis = self.review()
        self.publish(genesis, None)
        excluded = self.branch_disposition()
        decision = self.decision()
        authorized = self.review(
            sequence=2,
            previous=str(genesis["review_id"]),
            transition="SAME_BINDINGS",
            dispositions=[excluded],
            decisions=[decision],
        )
        self.publish(authorized, str(genesis["review_id"]))

        replacement = self.make_snapshot(
            [str(self.interpretation_set["interpretation_set_id"])],
            model_seed="replacement-model",
            predecessor_snapshot_id=str(self.snapshot["snapshot_id"]),
        )
        replacement_bindings = translation_review_bindings(replacement)
        replacement_surface = translation_review_surface(replacement, self.sets)
        stale_dispositions = self.stale_dispositions(
            predecessor_surface=self.surface,
            predecessor_bindings=self.bindings,
            successor_bindings=replacement_bindings,
            previous_dispositions=[excluded],
        )

        zero_stale = self.review(
            sequence=3,
            previous=str(authorized["review_id"]),
            transition="INPUT_BINDING_CHANGED",
            bindings=replacement_bindings,
            surface=replacement_surface,
            dispositions=[excluded],
            decisions=[decision],
        )
        with self.assertRaisesRegex(
            PolicyViolation, "exact staleness disposition coverage"
        ):
            publish_translation_review(
                self.review_dir,
                zero_stale,
                expected_head_review_id=str(authorized["review_id"]),
                snapshot=replacement,
                interpretation_sets=self.sets,
            )

        partial_stale = self.review(
            sequence=3,
            previous=str(authorized["review_id"]),
            transition="INPUT_BINDING_CHANGED",
            bindings=replacement_bindings,
            surface=replacement_surface,
            dispositions=[excluded, stale_dispositions[0]],
            decisions=[decision],
        )
        with self.assertRaisesRegex(
            PolicyViolation, "exact staleness disposition coverage"
        ):
            publish_translation_review(
                self.review_dir,
                partial_stale,
                expected_head_review_id=str(authorized["review_id"]),
                snapshot=replacement,
                interpretation_sets=self.sets,
            )

        rollover = self.review(
            sequence=3,
            previous=str(authorized["review_id"]),
            transition="INPUT_BINDING_CHANGED",
            bindings=replacement_bindings,
            surface=replacement_surface,
            dispositions=[excluded, *stale_dispositions],
            decisions=[decision],
        )
        publish_translation_review(
            self.review_dir,
            rollover,
            expected_head_review_id=str(authorized["review_id"]),
            snapshot=replacement,
            interpretation_sets=self.sets,
        )
        state = verify_translation_review_chain(
            self.review_dir,
            str(rollover["review_id"]),
            expected_bindings=replacement_bindings,
            expected_surface=replacement_surface,
        )
        self.assertEqual(state.workflow_status, "AWAITING_HUMAN_REVIEW")
        self.assertIsNone(state.current_decision_id)
        self.assertEqual(
            set(state.effective_branch_states.values()),
            {"STALE_BY_BINDING_CHANGE"},
        )

        immediate = self.review(
            sequence=4,
            previous=str(rollover["review_id"]),
            transition="INPUT_BINDING_CHANGED",
            bindings=self.bindings,
            surface=self.surface,
            dispositions=[excluded, *stale_dispositions],
            decisions=[decision, self.decision(sequence=2, previous=str(decision["decision_id"]))],
        )
        with self.assertRaises(PolicyViolation):
            publish_translation_review(
                self.review_dir,
                immediate,
                expected_head_review_id=str(rollover["review_id"]),
                snapshot=self.snapshot,
                interpretation_sets=self.sets,
            )

    def test_stale_branch_requires_retained_open_before_authorization(self) -> None:
        genesis = self.review()
        self.publish(genesis, None)
        replacement = self.make_snapshot(
            [str(self.interpretation_set["interpretation_set_id"])],
            model_seed="stale-authorization-model",
            predecessor_snapshot_id=str(self.snapshot["snapshot_id"]),
        )
        replacement_bindings = translation_review_bindings(replacement)
        replacement_surface = translation_review_surface(replacement, self.sets)
        stale_dispositions = self.stale_dispositions(
            predecessor_surface=self.surface,
            predecessor_bindings=self.bindings,
            successor_bindings=replacement_bindings,
        )
        rollover = self.review(
            sequence=2,
            previous=str(genesis["review_id"]),
            transition="INPUT_BINDING_CHANGED",
            bindings=replacement_bindings,
            surface=replacement_surface,
            dispositions=stale_dispositions,
        )
        publish_translation_review(
            self.review_dir,
            rollover,
            expected_head_review_id=str(genesis["review_id"]),
            snapshot=replacement,
            interpretation_sets=self.sets,
        )

        decision = self.decision(
            bindings=replacement_bindings,
            surface=replacement_surface,
        )
        direct_authorization = self.review(
            sequence=3,
            previous=str(rollover["review_id"]),
            transition="SAME_BINDINGS",
            bindings=replacement_bindings,
            surface=replacement_surface,
            dispositions=stale_dispositions,
            decisions=[decision],
        )
        with self.assertRaisesRegex(
            PolicyViolation, "stale branch.*RETAINED_OPEN"
        ):
            publish_translation_review(
                self.review_dir,
                direct_authorization,
                expected_head_review_id=str(rollover["review_id"]),
                snapshot=replacement,
                interpretation_sets=self.sets,
            )

        reopened = self.branch_disposition(
            disposition="RETAINED_OPEN",
            sequence=2,
            previous=str(stale_dispositions[1]["disposition_id"]),
            bindings=replacement_bindings,
            surface=replacement_surface,
            interpretation_index=1,
        )
        reopened_authorization = self.review(
            sequence=3,
            previous=str(rollover["review_id"]),
            transition="SAME_BINDINGS",
            bindings=replacement_bindings,
            surface=replacement_surface,
            dispositions=[*stale_dispositions, reopened],
            decisions=[decision],
        )
        publish_translation_review(
            self.review_dir,
            reopened_authorization,
            expected_head_review_id=str(rollover["review_id"]),
            snapshot=replacement,
            interpretation_sets=self.sets,
        )
        state = verify_translation_review_chain(
            self.review_dir,
            str(reopened_authorization["review_id"]),
            expected_bindings=replacement_bindings,
            expected_surface=replacement_surface,
        )
        self.assertEqual(
            state.workflow_status,
            "SCOPED_USE_SELECTED_AUTHENTICATION_REQUIRED",
        )

    def test_changed_binding_requires_immediate_snapshot_and_set_lineage(
        self,
    ) -> None:
        genesis = self.review()
        self.publish(genesis, None)

        def revised_set(supersedes: str | None) -> dict[str, object]:
            interpretation_set = copy.deepcopy(self.interpretation_set)
            interpretation_set["question"] = (
                "What revised role does the source assign to the endpoint?"
            )
            interpretation_set["supersedes_interpretation_set_id"] = supersedes
            interpretation_set["interpretation_set_id"] = (
                compute_interpretation_set_id(interpretation_set)
            )
            return interpretation_set

        def rollover_for(
            interpretation_set: dict[str, object],
            *,
            predecessor_snapshot_id: str | None,
            model_seed: str,
        ) -> tuple[
            dict[str, object],
            dict[str, object],
            dict[str, object],
            dict[str, object],
        ]:
            snapshot = self.make_snapshot(
                [str(interpretation_set["interpretation_set_id"])],
                model_seed=model_seed,
                predecessor_snapshot_id=predecessor_snapshot_id,
            )
            bindings = translation_review_bindings(snapshot)
            surface = translation_review_surface(snapshot, [interpretation_set])
            dispositions = self.stale_dispositions(
                predecessor_surface=self.surface,
                predecessor_bindings=self.bindings,
                successor_bindings=bindings,
            )
            rollover = self.review(
                sequence=2,
                previous=str(genesis["review_id"]),
                transition="INPUT_BINDING_CHANGED",
                bindings=bindings,
                surface=surface,
                dispositions=dispositions,
            )
            return rollover, snapshot, bindings, surface

        missing_snapshot_link = rollover_for(
            self.interpretation_set,
            predecessor_snapshot_id=None,
            model_seed="missing-snapshot-link",
        )
        with self.assertRaisesRegex(
            PolicyViolation, "immediate predecessor"
        ):
            publish_translation_review(
                self.review_dir,
                missing_snapshot_link[0],
                expected_head_review_id=str(genesis["review_id"]),
                snapshot=missing_snapshot_link[1],
                interpretation_sets=self.sets,
            )

        missing_set_link = revised_set(None)
        missing_set_rollover = rollover_for(
            missing_set_link,
            predecessor_snapshot_id=str(self.snapshot["snapshot_id"]),
            model_seed="missing-set-link",
        )
        with self.assertRaisesRegex(
            PolicyViolation, "supersede every removed predecessor"
        ):
            publish_translation_review(
                self.review_dir,
                missing_set_rollover[0],
                expected_head_review_id=str(genesis["review_id"]),
                snapshot=missing_set_rollover[1],
                interpretation_sets=[missing_set_link],
            )

        foreign_set_link = revised_set(content_id("TIS", "foreign-set"))
        foreign_set_rollover = rollover_for(
            foreign_set_link,
            predecessor_snapshot_id=str(self.snapshot["snapshot_id"]),
            model_seed="foreign-set-link",
        )
        with self.assertRaisesRegex(
            PolicyViolation, "immediately removed predecessor"
        ):
            publish_translation_review(
                self.review_dir,
                foreign_set_rollover[0],
                expected_head_review_id=str(genesis["review_id"]),
                snapshot=foreign_set_rollover[1],
                interpretation_sets=[foreign_set_link],
            )

        replacement_set = revised_set(
            str(self.interpretation_set["interpretation_set_id"])
        )
        accepted = rollover_for(
            replacement_set,
            predecessor_snapshot_id=str(self.snapshot["snapshot_id"]),
            model_seed="valid-set-link",
        )
        publish_translation_review(
            self.review_dir,
            accepted[0],
            expected_head_review_id=str(genesis["review_id"]),
            snapshot=accepted[1],
            interpretation_sets=[replacement_set],
        )
        state = verify_translation_review_chain(
            self.review_dir,
            str(accepted[0]["review_id"]),
            expected_bindings=accepted[2],
            expected_surface=accepted[3],
        )
        old_set_id = str(self.interpretation_set["interpretation_set_id"])
        self.assertTrue(state.effective_branch_states)
        self.assertTrue(
            all(
                key.startswith(f"{old_set_id}/")
                for key in state.effective_branch_states
            )
        )

        wrong_snapshot_link = copy.deepcopy(accepted[0])
        wrong_predecessor_id = content_id("TSN", "wrong-predecessor")
        wrong_snapshot_link["bindings"]["predecessor_snapshot_id"] = (
            wrong_predecessor_id
        )
        for disposition in wrong_snapshot_link["branch_dispositions"]:
            disposition["bindings"]["predecessor_snapshot_id"] = (
                wrong_predecessor_id
            )
            disposition["disposition_id"] = compute_branch_disposition_id(
                disposition
            )
        wrong_snapshot_link["branch_dispositions"] = sorted(
            wrong_snapshot_link["branch_dispositions"],
            key=lambda item: str(item["disposition_id"]),
        )
        wrong_snapshot_link["review_id"] = compute_translation_review_id(
            wrong_snapshot_link
        )
        wrong_snapshot_dir = self.root / "wrong-snapshot-replay"
        self.write_unchecked_lineage(
            wrong_snapshot_dir, [genesis, wrong_snapshot_link]
        )
        with self.assertRaisesRegex(PolicyViolation, "immediate predecessor"):
            verify_translation_review_chain(
                wrong_snapshot_dir,
                str(wrong_snapshot_link["review_id"]),
                expected_bindings=wrong_snapshot_link["bindings"],
                expected_surface=wrong_snapshot_link["review_surface"],
            )

        missing_set_replay = copy.deepcopy(accepted[0])
        missing_set_replay["review_surface"]["interpretation_sets"][0][
            "supersedes_interpretation_set_id"
        ] = None
        missing_set_replay["review_id"] = compute_translation_review_id(
            missing_set_replay
        )
        missing_set_dir = self.root / "missing-set-replay"
        self.write_unchecked_lineage(
            missing_set_dir, [genesis, missing_set_replay]
        )
        with self.assertRaisesRegex(
            PolicyViolation, "supersede every removed predecessor"
        ):
            verify_translation_review_chain(
                missing_set_dir,
                str(missing_set_replay["review_id"]),
                expected_bindings=missing_set_replay["bindings"],
                expected_surface=missing_set_replay["review_surface"],
            )

        replacement_decision = self.decision(
            bindings=accepted[2],
            surface=accepted[3],
        )
        authorized_replacement = self.review(
            sequence=3,
            previous=str(accepted[0]["review_id"]),
            transition="SAME_BINDINGS",
            bindings=accepted[2],
            surface=accepted[3],
            dispositions=list(accepted[0]["branch_dispositions"]),
            decisions=[replacement_decision],
        )
        with self.assertRaisesRegex(
            PolicyViolation, "stale branch.*RETAINED_OPEN"
        ):
            publish_translation_review(
                self.review_dir,
                authorized_replacement,
                expected_head_review_id=str(accepted[0]["review_id"]),
                snapshot=accepted[1],
                interpretation_sets=[replacement_set],
            )

        selected_branch_id = str(
            replacement_decision["authorized_variants"][0]["selections"][0][
                "interpretation_id"
            ]
        )
        stale_head = next(
            item
            for item in accepted[0]["branch_dispositions"]
            if item["interpretation_id"] == selected_branch_id
        )
        selected_index = next(
            index
            for index, item in enumerate(
                accepted[3]["interpretation_sets"][0]["interpretations"]
            )
            if item["interpretation_id"] == selected_branch_id
        )
        reopened = self.branch_disposition(
            disposition="RETAINED_OPEN",
            sequence=int(stale_head["decision_sequence"]) + 1,
            previous=str(stale_head["disposition_id"]),
            bindings=accepted[2],
            surface=accepted[3],
            interpretation_index=selected_index,
        )
        reopened_authorization = self.review(
            sequence=3,
            previous=str(accepted[0]["review_id"]),
            transition="SAME_BINDINGS",
            bindings=accepted[2],
            surface=accepted[3],
            dispositions=[*accepted[0]["branch_dispositions"], reopened],
            decisions=[replacement_decision],
        )
        publish_translation_review(
            self.review_dir,
            reopened_authorization,
            expected_head_review_id=str(accepted[0]["review_id"]),
            snapshot=accepted[1],
            interpretation_sets=[replacement_set],
        )

        second_snapshot = self.make_snapshot(
            [str(replacement_set["interpretation_set_id"])],
            model_seed="valid-second-hop",
            predecessor_snapshot_id=str(accepted[1]["snapshot_id"]),
        )
        second_bindings = translation_review_bindings(second_snapshot)
        second_surface = translation_review_surface(
            second_snapshot, [replacement_set]
        )
        second_stale = self.stale_dispositions(
            predecessor_surface=accepted[3],
            predecessor_bindings=accepted[2],
            successor_bindings=second_bindings,
            previous_dispositions=list(
                reopened_authorization["branch_dispositions"]
            ),
        )
        second_rollover = self.review(
            sequence=4,
            previous=str(reopened_authorization["review_id"]),
            transition="INPUT_BINDING_CHANGED",
            bindings=second_bindings,
            surface=second_surface,
            dispositions=[
                *reopened_authorization["branch_dispositions"],
                *second_stale,
            ],
            decisions=[replacement_decision],
        )
        publish_translation_review(
            self.review_dir,
            second_rollover,
            expected_head_review_id=str(reopened_authorization["review_id"]),
            snapshot=second_snapshot,
            interpretation_sets=[replacement_set],
        )
        second_state = verify_translation_review_chain(
            self.review_dir,
            str(second_rollover["review_id"]),
            expected_bindings=second_bindings,
            expected_surface=second_surface,
        )
        self.assertEqual(second_state.workflow_status, "AWAITING_HUMAN_REVIEW")
        self.assertEqual(
            set(second_state.effective_branch_states.values()),
            {"STALE_BY_BINDING_CHANGE"},
        )

    def test_claim_only_interruption_rolls_forward_exact_candidate(self) -> None:
        genesis = self.review()
        real_link = os.link
        calls = 0

        def fail_second_link(source: object, target: object) -> None:
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError(errno.EIO, "simulated interrupted publication")
            real_link(source, target)  # type: ignore[arg-type]

        with mock.patch(
            "creib.forge.translation_review.os.link", side_effect=fail_second_link
        ), self.assertRaises(TranslationReviewError) as interrupted:
            self.publish(genesis, None)
        self.assertEqual(
            interrupted.exception.error_code, "TRANSLATION_REVIEW_WRITE_FAILED"
        )
        claim = self.review_dir / "NEXT-GENESIS.claim"
        output = self.review_dir / f"{str(genesis['review_id']).replace(':', '-')}.json"
        self.assertTrue(claim.exists())
        self.assertFalse(output.exists())

        recovered = self.publish(genesis, None)
        self.assertEqual(recovered, output)
        self.assertTrue(os.path.samefile(claim, output))

        sibling = self.review()
        sibling["transition_reason"] = "A sibling must not replace the reservation."
        sibling["review_id"] = compute_translation_review_id(sibling)
        with self.assertRaises(TranslationReviewError) as stale:
            self.publish(sibling, None)
        self.assertEqual(stale.exception.error_code, "TRANSLATION_REVIEW_STALE_HEAD")

    def test_complete_pair_retry_is_idempotent_without_relink(self) -> None:
        genesis = self.review()
        output = self.publish(genesis, None)
        with mock.patch(
            "creib.forge.translation_review.os.link",
            side_effect=AssertionError("complete retry must not relink"),
        ) as link_mock, mock.patch(
            "creib.forge.translation_review._fsync_directory"
        ) as fsync_mock:
            self.assertEqual(self.publish(genesis, None), output)
        link_mock.assert_not_called()
        fsync_mock.assert_called_once_with(self.review_dir)

    def test_record_without_claim_and_extra_lineage_fail_closed(self) -> None:
        genesis = self.review()
        record = self.review_dir / f"{str(genesis['review_id']).replace(':', '-')}.json"
        record.write_bytes(canonical_bytes(genesis) + b"\n")
        with self.assertRaises(TranslationReviewError):
            verify_translation_review_chain(self.review_dir, str(genesis["review_id"]))


if __name__ == "__main__":
    unittest.main()
