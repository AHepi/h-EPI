from __future__ import annotations

import copy
from pathlib import Path
import tempfile
import unittest

from creib.canonical import bytes_digest, canonical_bytes
from creib.errors import PolicyViolation, RecordError
from creib.forge.schema_validation import load_local_schema_catalog
from creib.forge.translation import (
    NON_INDUCTIVE_TRANSLATION_LIMIT,
    TRANSLATION_COMPONENT_ID_SPECS,
    TRANSLATION_SCHEMA_TO_FILE,
    TRANSLATION_SCHEMA_TO_ID,
    compute_named_translation_component_id,
    compute_record_closure_sha256,
    compute_semantic_dependency_closure_sha256,
    compute_theory_record_sha256,
    compute_translation_record_id,
    load_translation_inventory,
    validate_translation_record,
    validate_translation_snapshot,
    verify_source_document_bytes,
)


ROOT = Path(__file__).resolve().parents[1]


def _provenance() -> dict[str, object]:
    return {
        "producer_kind": "HUMAN",
        "producer_id": "translation-runtime-test",
        "created_at": "2026-09-03T00:00:00Z",
        "generation_record_ids": [],
    }


def _seal_record(record: dict[str, object]) -> dict[str, object]:
    id_field = {
        "creib.semantic-forge.translation-source-document.v1": "document_id",
        "creib.semantic-forge.translation-source-span.v1": "span_id",
        "creib.semantic-forge.translation-charter.v1": "charter_id",
        "creib.semantic-forge.translation-obligation-graph.v1": "graph_id",
        "creib.semantic-forge.translation-interpretation-set.v1": "interpretation_set_id",
        "creib.semantic-forge.translation-neutral-signature.v1": "signature_id",
        "creib.semantic-forge.translation-neutral-model.v1": "model_id",
        "creib.semantic-forge.translation-project-import.v1": "import_id",
        "creib.semantic-forge.translation-two-way-bridge.v1": "bridge_id",
        "creib.semantic-forge.translation-snapshot.v1": "snapshot_id",
    }[str(record["schema_version"])]
    record[id_field] = compute_translation_record_id(record)
    return record


def _seal_component(kind: str, value: dict[str, object]) -> dict[str, object]:
    id_field = TRANSLATION_COMPONENT_ID_SPECS[kind][2]
    value[id_field] = compute_named_translation_component_id(kind, value)
    return value


def _selected_records(
    snapshot: dict[str, object],
    records: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    ids = [
        *snapshot["document_ids"],
        *snapshot["span_ids"],
        snapshot["charter_id"],
        snapshot["graph_id"],
        *snapshot["interpretation_set_ids"],
        snapshot["signature_id"],
        snapshot["model_id"],
        *snapshot["import_ids"],
        snapshot["bridge_id"],
    ]
    return [records[str(record_id)] for record_id in ids]


def _bundle(
    *,
    labels_use_unrelated_span: bool = False,
    labels_preserve_uninterpreted_feature: bool = False,
    project_import_affected_element_keys: tuple[str, ...] | None = None,
    open_port_has_affected_elements: bool = True,
    include_open_port: bool = True,
    causal_clause_element_key: str = "CausalUseRequired",
    dependency_mode: str = "FORWARD",
    include_dependency_shift: bool = False,
    exact_dependency_shift_footprint: bool = True,
) -> dict[str, object]:
    source_bytes = b"%PDF-translation-runtime-fixture\n"
    document = _seal_record(
        {
            "schema_version": "creib.semantic-forge.translation-source-document.v1",
            "document_id": "",
            "supersedes_document_id": None,
            "document_key": "FixtureAuthority",
            "title": "Translation runtime fixture authority",
            "artifact": {
                "supplied_filename": "fixture.pdf",
                "media_type": "application/pdf",
                "sha256": bytes_digest(source_bytes),
                "byte_length": len(source_bytes),
            },
            "structure": {"kind": "PDF", "page_count": 1, "encoding": None},
            "legacy_refs": [],
            "provenance": _provenance(),
        }
    )
    span = _seal_record(
        {
            "schema_version": "creib.semantic-forge.translation-source-span.v1",
            "span_id": "",
            "supersedes_span_id": None,
            "document_id": document["document_id"],
            "span_key": "role-distinction",
            "segments": [
                {
                    "ordinal": 1,
                    "locator": {
                        "kind": "PDF_REGION",
                        "physical_page": 1,
                        "page_index_zero_based": 0,
                        "printed_label": "1",
                        "section_raw": "Fixture clause",
                        "page_size_millipoints": [612000, 792000],
                        "page_rotation_degrees": 0,
                        "bbox_millipoints": [1000, 1000, 400000, 700000],
                    },
                    "literal_snapshot": {
                        "algorithm": "fixture-word-snapshot-v1",
                        "tool": "translation-runtime-test",
                        "tool_version": "1",
                        "selection_rule": "tokens intersecting the declared region",
                        "item_count": 4,
                        "digest_domain": "translation-runtime-test/literal/v1",
                        "sha256": "1" * 64,
                    },
                    "reviewed_transcription": None,
                }
            ],
            "context_span_ids": [],
            "legacy_refs": [],
            "source_inferential_status": None,
            "provenance": _provenance(),
        }
    )
    selected_spans = [span]
    labels_source_span_ids = [span["span_id"]]
    if labels_use_unrelated_span:
        unrelated_span = copy.deepcopy(span)
        unrelated_span["span_id"] = ""
        unrelated_span["span_key"] = "unrelated-reading"
        _seal_record(unrelated_span)
        selected_spans.append(unrelated_span)
        labels_source_span_ids = [unrelated_span["span_id"]]
    distinction = _seal_component(
        "protected_distinction",
        {
            "distinction_id": "",
            "statement": "A semantic role is not merely its surface label.",
        },
    )
    charter = _seal_record(
        {
            "schema_version": "creib.semantic-forge.translation-charter.v1",
            "charter_id": "",
            "supersedes_charter_id": None,
            "title": "Bounded neutral translation",
            "problem_statement": "Represent the selected source without hiding rivals.",
            "purpose": "Construct a criticism-ready neutral semantic proposal.",
            "output_kind": "NEUTRAL_SEMANTIC_MODEL",
            "authority_bindings": [
                {
                    "document_id": document["document_id"],
                    "role": "SOLE_SEMANTIC_AUTHORITY",
                }
            ],
            "in_scope": ["The selected role-label distinction."],
            "out_of_scope": ["Any claim that test survival confirms the translation."],
            "system_boundary": "The selected source span and declared project imports.",
            "protected_distinctions": [distinction],
            "success_claim": "SCOPED_FIT_ONLY",
            "policies": {
                "formalism_can_override_valid_prose": False,
                "test_survival_effect": "UNREFUTED_ONLY",
                "research_role": "CRITICISM_DISCOVERY_ONLY",
                "ambiguity_policy": "PRESERVE_RIVALS",
                "missing_mapping_policy": "OPEN_LOSS",
                "conflict_policy": "PRESERVE_CONFLICT_FOR_REVIEW",
                "human_semantic_decision_required": True,
            },
            "proposal_status": "PROPOSED",
            "provenance": _provenance(),
        }
    )

    feature_one = _seal_component(
        "protected_feature",
        {
            "feature_id": "",
            "kind": "DISTINCTION",
            "statement": "Role and label can vary independently.",
            "charter_distinction_ids": [distinction["distinction_id"]],
        },
    )
    claim_one = _seal_component(
        "source_claim",
        {
            "claim_id": "",
            "claim_kind": "SOURCE_AUTHORITY",
            "expression_mode": "VERBATIM_TRANSCRIPTION",
            "statement": "The source distinguishes semantic role from label.",
            "source_span_ids": [span["span_id"]],
            "source_marks_raw": [],
        },
    )
    duty_one = _seal_component(
        "translation_duty",
        {
            "duty_id": "",
            "claim_kind": "SOURCE_INTERPRETATION",
            "duty_kind": "DISTINCTION",
            "statement": "Preserve the role-label distinction.",
            "protected_features": [feature_one],
        },
    )
    obligation_one = _seal_component(
        "obligation",
        {
            "obligation_id": "",
            "source_claim": claim_one,
            "translation_duty": duty_one,
            "depends_on_obligation_ids": [],
        },
    )
    feature_two = _seal_component(
        "protected_feature",
        {
            "feature_id": "",
            "kind": "RELATION",
            "statement": "The proposed causal reading has a discriminating consequence.",
            "charter_distinction_ids": [],
        },
    )
    claim_two = _seal_component(
        "source_claim",
        {
            "claim_id": "",
            "claim_kind": "SOURCE_AUTHORITY",
            "expression_mode": "VERBATIM_TRANSCRIPTION",
            "statement": "The distinction may constrain classification consequences.",
            "source_span_ids": [span["span_id"]],
            "source_marks_raw": [],
        },
    )
    duty_two = _seal_component(
        "translation_duty",
        {
            "duty_id": "",
            "claim_kind": "SOURCE_INTERPRETATION",
            "duty_kind": "CLAIM",
            "statement": "State a consequence that could discriminate rival readings.",
            "protected_features": [feature_two],
        },
    )
    obligation_two = _seal_component(
        "obligation",
        {
            "obligation_id": "",
            "source_claim": claim_two,
            "translation_duty": duty_two,
            "depends_on_obligation_ids": [obligation_one["obligation_id"]],
        },
    )
    edge = _seal_component(
        "obligation_edge",
        {
            "edge_id": "",
            "from_obligation_id": obligation_two["obligation_id"],
            "to_obligation_id": obligation_one["obligation_id"],
            "kind": "DEPENDS_ON",
            "statement": "The consequence depends on preserving the distinction.",
        },
    )
    obligations = sorted(
        [obligation_one, obligation_two], key=lambda item: str(item["obligation_id"])
    )
    graph = _seal_record(
        {
            "schema_version": "creib.semantic-forge.translation-obligation-graph.v1",
            "graph_id": "",
            "supersedes_graph_id": None,
            "charter_id": charter["charter_id"],
            "span_bindings": sorted(
                [
                    {"span_id": span["span_id"], "role": "TARGET"},
                    *(
                        [
                            {
                                "span_id": selected_spans[1]["span_id"],
                                "role": "CONTEXT",
                            }
                        ]
                        if labels_use_unrelated_span
                        else []
                    ),
                ],
                key=lambda item: item["span_id"],
            ),
            "obligations": obligations,
            "edges": [edge],
            "proposal_status": "PROPOSED",
            "provenance": _provenance(),
        }
    )

    obligation_ids = sorted(
        [obligation_one["obligation_id"], obligation_two["obligation_id"]]
    )
    feature_ids = sorted([feature_one["feature_id"], feature_two["feature_id"]])
    causal_branch = _seal_component(
        "interpretation",
        {
            "interpretation_id": "",
            "claim_kind": "SOURCE_INTERPRETATION",
            "statement": "The role requires a causal difference, not a label change alone.",
            "source_span_ids": [span["span_id"]],
            "interpreted_obligation_ids": obligation_ids,
            "preserved_feature_ids": feature_ids,
            "model_effect": {
                "status": "DECLARED",
                "effect_statement": "Introduce a causal-use relation.",
                "affected_element_keys": sorted(
                    {
                        "CausalUse",
                        "RoleDistinctionRequired",
                        causal_clause_element_key,
                    }
                ),
            },
            "discriminating_consequences": ["Relabeling alone leaves the role unchanged."],
            "falsifier_conditions": ["A source-backed labels-only case is sufficient."],
            "known_loss_risks": [],
            "proposal_status": "PROPOSED",
        },
    )
    labels_branch = _seal_component(
        "interpretation",
        {
            "interpretation_id": "",
            "claim_kind": "SOURCE_INTERPRETATION",
            "statement": "The role is exhausted by its surface label.",
            "source_span_ids": labels_source_span_ids,
            "interpreted_obligation_ids": (
                [obligation_one["obligation_id"]]
                if labels_preserve_uninterpreted_feature
                else obligation_ids
            ),
            "preserved_feature_ids": (
                [feature_two["feature_id"]]
                if labels_preserve_uninterpreted_feature
                else []
            ),
            "model_effect": {
                "status": "UNPROJECTED",
                "effect_statement": "No neutral model projection has been supplied.",
                "affected_element_keys": [],
            },
            "discriminating_consequences": ["Relabeling changes the classification."],
            "falsifier_conditions": ["A same-label case has distinct causal use."],
            "known_loss_risks": ["The role-label distinction may collapse."],
            "proposal_status": "PROPOSED",
        },
    )
    interpretation = _seal_record(
        {
            "schema_version": "creib.semantic-forge.translation-interpretation-set.v1",
            "interpretation_set_id": "",
            "supersedes_interpretation_set_id": None,
            "charter_id": charter["charter_id"],
            "graph_id": graph["graph_id"],
            "question": "Does the distinction require causal use or only a label?",
            "source_span_ids": sorted(
                selected_span["span_id"] for selected_span in selected_spans
            ),
            "obligation_ids": obligation_ids,
            "rival_relation": "EXCLUSIVE",
            "admissible_branch_sets": sorted(
                [
                    [causal_branch["interpretation_id"]],
                    [labels_branch["interpretation_id"]],
                ],
                key=canonical_bytes,
            ),
            "branches": sorted(
                [causal_branch, labels_branch],
                key=lambda item: str(item["interpretation_id"]),
            ),
            "proposal_status": "PROPOSED",
            "provenance": _provenance(),
        }
    )

    project_import = _seal_record(
        {
            "schema_version": "creib.semantic-forge.translation-project-import.v1",
            "import_id": "",
            "supersedes_import_id": None,
            "charter_id": charter["charter_id"],
            "import_key": "SystemBoundary",
            "statement": "Each evaluated case supplies an explicit system boundary.",
            "claim_kind": "PROJECT_IMPORT",
            "category": "METHODOLOGICAL",
            "scope": "This translation proposal only.",
            "source_entitlement": "NONE_CLAIMED",
            "motivation": "Causal use is boundary-relative.",
            "independence_claim": {
                "statement": "The selected source span does not state this boundary.",
                "status": "PROPOSED",
                "discriminator": "Locate an explicit source boundary.",
                "evidence_record_ids": [],
            },
            "necessity_claim": {
                "statement": "The boundary is needed to evaluate causal use.",
                "status": "PROPOSED",
                "discriminator": "Delete it and compare admissible cases.",
                "evidence_record_ids": [],
            },
            "alternatives": ["Represent the boundary only as an unresolved port."],
            "deletion_test": {
                "prediction": "Deletion makes causal use underdetermined.",
                "test_record_ids": [],
            },
            "affected_element_keys": list(
                project_import_affected_element_keys
                if project_import_affected_element_keys is not None
                else ("BoundaryRequired", "SystemBoundary")
            ),
            "proposal_status": "PROPOSED",
            "provenance": _provenance(),
        }
    )

    case_member = _seal_component(
        "signature_member",
        {
            "member_id": "",
            "element_key": "Case",
            "kind": "ENTITY",
            "statement": "An item classified by the proposal.",
            "argument_roles": [],
            "identity_conditions": [],
            "variation_conditions": [],
            "scope_conditions": ["Inside the declared translation boundary."],
            "semantic_effect": "NONE",
            "basis": {"premise_kind": "STRUCTURAL_SCAFFOLD", "record_ids": []},
        },
    )
    causal_member = _seal_component(
        "signature_member",
        {
            "member_id": "",
            "element_key": "CausalUse",
            "kind": "RELATION",
            "statement": "One case causally uses another.",
            "argument_roles": [
                {
                    "name": "used_case",
                    "target_member_id": case_member["member_id"],
                    "multiplicity": "ONE",
                }
            ],
            "identity_conditions": [],
            "variation_conditions": ["Labels may vary independently."],
            "scope_conditions": ["Inside the declared translation boundary."],
            "semantic_effect": "MEANING_BEARING",
            "basis": {
                "premise_kind": "SOURCE_INTERPRETATION",
                "record_ids": [causal_branch["interpretation_id"]],
            },
        },
    )
    boundary_member = _seal_component(
        "signature_member",
        {
            "member_id": "",
            "element_key": "SystemBoundary",
            "kind": "BOUNDARY",
            "statement": "The explicit boundary used to evaluate a case.",
            "argument_roles": [],
            "identity_conditions": [],
            "variation_conditions": [],
            "scope_conditions": ["This translation proposal only."],
            "semantic_effect": "MEANING_BEARING",
            "basis": {
                "premise_kind": "PROJECT_IMPORT",
                "record_ids": [project_import["import_id"]],
            },
        },
    )
    signature = _seal_record(
        {
            "schema_version": "creib.semantic-forge.translation-neutral-signature.v1",
            "signature_id": "",
            "supersedes_signature_id": None,
            "charter_id": charter["charter_id"],
            "members": sorted(
                [case_member, causal_member, boundary_member],
                key=lambda item: str(item["member_id"]),
            ),
            "proposal_status": "PROPOSED",
            "provenance": _provenance(),
        }
    )

    boundary_clause = _seal_component(
        "model_clause",
        {
            "clause_id": "",
            "element_key": "BoundaryRequired",
            "kind": "SCOPE_CONDITION",
            "operative_prose": "Evaluation requires an explicit system boundary.",
            "uses_member_ids": [boundary_member["member_id"]],
            "depends_on_clause_ids": [],
            "basis": {
                "premise_kind": "PROJECT_IMPORT",
                "record_ids": [project_import["import_id"]],
            },
        },
    )

    def make_role_clause(dependency_ids: list[str]) -> dict[str, object]:
        return _seal_component(
            "model_clause",
            {
                "clause_id": "",
                "element_key": "RoleDistinctionRequired",
                "kind": "DISTINCTION",
                "operative_prose": "Semantic role is not exhausted by its label.",
                "uses_member_ids": [causal_member["member_id"]],
                "depends_on_clause_ids": dependency_ids,
                "basis": {
                    "premise_kind": "SOURCE_INTERPRETATION",
                    "record_ids": [causal_branch["interpretation_id"]],
                },
            },
        )

    def make_causal_clause(dependency_ids: list[str]) -> dict[str, object]:
        return _seal_component(
            "model_clause",
            {
                "clause_id": "",
                "element_key": causal_clause_element_key,
                "kind": "PRIMITIVE_CONDITION",
                "operative_prose": "The classified role requires causal use.",
                "uses_member_ids": [causal_member["member_id"]],
                "depends_on_clause_ids": dependency_ids,
                "basis": {
                    "premise_kind": "SOURCE_INTERPRETATION",
                    "record_ids": [causal_branch["interpretation_id"]],
                },
            },
        )

    if dependency_mode == "FORWARD":
        role_clause = make_role_clause([boundary_clause["clause_id"]])
        causal_clause = make_causal_clause([role_clause["clause_id"]])
    elif dependency_mode == "REVERSED":
        causal_clause = make_causal_clause([boundary_clause["clause_id"]])
        role_clause = make_role_clause([causal_clause["clause_id"]])
    elif dependency_mode == "NONE":
        role_clause = make_role_clause([boundary_clause["clause_id"]])
        causal_clause = make_causal_clause([boundary_clause["clause_id"]])
    else:
        raise ValueError(f"unsupported dependency_mode: {dependency_mode}")

    clauses = sorted(
        [boundary_clause, role_clause, causal_clause],
        key=lambda item: str(item["clause_id"]),
    )
    open_port = _seal_component(
        "model_open_port",
        {
            "port_id": "",
            "question": "Can the labels-only rival be projected without collapsing the distinction?",
            "affected_member_ids": (
                [causal_member["member_id"]]
                if open_port_has_affected_elements
                else []
            ),
            "affected_clause_ids": (
                [causal_clause["clause_id"]]
                if open_port_has_affected_elements
                else []
            ),
            "interpretation_set_ids": [interpretation["interpretation_set_id"]],
        },
    )
    closure = {
        "members": sorted(
            [
                {
                    "record_id": claim_one["claim_id"],
                    "premise_kind": "SOURCE_AUTHORITY",
                    "role": "TRANSITIVE",
                },
                {
                    "record_id": claim_two["claim_id"],
                    "premise_kind": "SOURCE_AUTHORITY",
                    "role": "TRANSITIVE",
                },
                {
                    "record_id": causal_branch["interpretation_id"],
                    "premise_kind": "SOURCE_INTERPRETATION",
                    "role": "DIRECT",
                },
                {
                    "record_id": project_import["import_id"],
                    "premise_kind": "PROJECT_IMPORT",
                    "role": "DIRECT",
                },
            ],
            key=lambda item: str(item["record_id"]),
        ),
        "closure_sha256": "",
    }
    closure["closure_sha256"] = compute_semantic_dependency_closure_sha256(closure)
    projection = {
        "signature_id": signature["signature_id"],
        "member_ids": sorted(
            [
                case_member["member_id"],
                causal_member["member_id"],
                boundary_member["member_id"],
            ]
        ),
        "clause_ids": sorted(
            [
                boundary_clause["clause_id"],
                role_clause["clause_id"],
                causal_clause["clause_id"],
            ]
        ),
        "theory_record_sha256": "",
        "execution_semantics": "NONE_V1",
    }
    projection["theory_record_sha256"] = compute_theory_record_sha256(projection)
    model = _seal_record(
        {
            "schema_version": "creib.semantic-forge.translation-neutral-model.v1",
            "model_id": "",
            "supersedes_model_id": None,
            "charter_id": charter["charter_id"],
            "signature_id": signature["signature_id"],
            "interpretation_ids": [causal_branch["interpretation_id"]],
            "import_ids": [project_import["import_id"]],
            "clauses": clauses,
            "open_ports": [open_port] if include_open_port else [],
            "semantic_dependency_closure": closure,
            "theory_projection": projection,
            "proposal_status": "PROPOSED",
            "semantic_verdict": None,
            "provenance": _provenance(),
        }
    )

    delta = _seal_component(
        "translation_delta",
        {
            "delta_id": "",
            "kind": "UNRESOLVED",
            "source_obligation_ids": [obligation_two["obligation_id"]],
            "model_element_ids": [causal_clause["clause_id"]],
            "statement": "The consequence mapping remains disputed.",
            "consequence": "The model may understate or overstate the source consequence.",
            "status": "OPEN",
        },
    )
    dependency_shift: dict[str, object] | None = None
    if include_dependency_shift:
        dependency_shift = _seal_component(
            "translation_delta",
            {
                "delta_id": "",
                "kind": "DEPENDENCY_SHIFT",
                "source_obligation_ids": sorted(
                    [
                        obligation_one["obligation_id"],
                        obligation_two["obligation_id"],
                    ]
                ),
                "model_element_ids": sorted(
                    [
                        *(
                            [causal_member["member_id"]]
                            if exact_dependency_shift_footprint
                            else []
                        ),
                        role_clause["clause_id"],
                        causal_clause["clause_id"],
                    ]
                ),
                "statement": "The source dependency lacks an exclusively directed model path.",
                "consequence": "Dependency direction remains explicitly open.",
                "status": "OPEN",
            },
        )
    forward_one = _seal_component(
        "forward_mapping",
        {
            "mapping_id": "",
            "obligation_id": obligation_one["obligation_id"],
            "model_element_ids": sorted(
                [causal_member["member_id"], role_clause["clause_id"]]
            ),
            "interpretation_ids": [causal_branch["interpretation_id"]],
            "coverage_claim": "CLAIMED_EXACT",
            "transformation_statement": "Represent the distinction as causal use.",
            "back_translation": "The role requires causal use, not a label alone.",
            "comparison": "EQUIVALENT_CANDIDATE",
            "delta_ids": [],
        },
    )
    forward_two = _seal_component(
        "forward_mapping",
        {
            "mapping_id": "",
            "obligation_id": obligation_two["obligation_id"],
            "model_element_ids": [causal_clause["clause_id"]],
            "interpretation_ids": [causal_branch["interpretation_id"]],
            "coverage_claim": "DISPUTED",
            "transformation_statement": "Propose a discriminating causal consequence.",
            "back_translation": "A consequence discriminates the causal reading.",
            "comparison": "UNRESOLVED",
            "delta_ids": sorted(
                [
                    delta["delta_id"],
                    *(
                        [dependency_shift["delta_id"]]
                        if dependency_shift is not None
                        else []
                    ),
                ]
            ),
        },
    )

    def reverse(
        element: dict[str, object],
        back_translation: str,
        source_obligation_ids: tuple[str, ...] = (),
    ) -> dict[str, object]:
        basis = element["basis"]
        basis_kind = basis["premise_kind"]
        return _seal_component(
            "reverse_mapping",
            {
                "mapping_id": "",
                "model_element_id": element.get("member_id", element.get("clause_id")),
                "basis_kind": basis_kind,
                "basis_ids": list(basis["record_ids"]),
                "source_obligation_ids": list(source_obligation_ids),
                "back_translation": back_translation,
                "semantic_effect": (
                    "NONE" if basis_kind == "STRUCTURAL_SCAFFOLD" else "MEANING_BEARING"
                ),
            },
        )

    reverse_mappings = sorted(
        [
            reverse(case_member, "A structurally identified case."),
            reverse(
                causal_member,
                "The role requires causal use.",
                (obligation_one["obligation_id"],),
            ),
            reverse(boundary_member, "The project supplies a boundary not claimed by the source."),
            reverse(boundary_clause, "Evaluation uses the project-supplied boundary."),
            reverse(
                role_clause,
                "Semantic role is not exhausted by its label.",
                (obligation_one["obligation_id"],),
            ),
            reverse(
                causal_clause,
                "The classified role requires causal use.",
                (obligation_two["obligation_id"],),
            ),
        ],
        key=lambda item: str(item["mapping_id"]),
    )
    bridge = _seal_record(
        {
            "schema_version": "creib.semantic-forge.translation-two-way-bridge.v1",
            "bridge_id": "",
            "supersedes_bridge_id": None,
            "charter_id": charter["charter_id"],
            "graph_id": graph["graph_id"],
            "signature_id": signature["signature_id"],
            "model_id": model["model_id"],
            "interpretation_set_ids": [interpretation["interpretation_set_id"]],
            "import_ids": [project_import["import_id"]],
            "forward_mappings": sorted(
                [forward_one, forward_two], key=lambda item: str(item["mapping_id"])
            ),
            "reverse_mappings": reverse_mappings,
            "translation_deltas": sorted(
                [delta, *([dependency_shift] if dependency_shift is not None else [])],
                key=lambda item: item["delta_id"],
            ),
            "mapping_status": "PROPOSED",
            "semantic_verdict": None,
            "provenance": _provenance(),
        }
    )

    top_records = [
        document,
        *selected_spans,
        charter,
        graph,
        interpretation,
        signature,
        model,
        project_import,
        bridge,
    ]
    records = {
        str(
            record[
                {
                    "creib.semantic-forge.translation-source-document.v1": "document_id",
                    "creib.semantic-forge.translation-source-span.v1": "span_id",
                    "creib.semantic-forge.translation-charter.v1": "charter_id",
                    "creib.semantic-forge.translation-obligation-graph.v1": "graph_id",
                    "creib.semantic-forge.translation-interpretation-set.v1": "interpretation_set_id",
                    "creib.semantic-forge.translation-neutral-signature.v1": "signature_id",
                    "creib.semantic-forge.translation-neutral-model.v1": "model_id",
                    "creib.semantic-forge.translation-project-import.v1": "import_id",
                    "creib.semantic-forge.translation-two-way-bridge.v1": "bridge_id",
                }[str(record["schema_version"])]
            ]
        ): record
        for record in top_records
    }
    snapshot = {
        "schema_version": "creib.semantic-forge.translation-snapshot.v1",
        "snapshot_id": "",
        "predecessor_snapshot_id": None,
        "document_ids": [document["document_id"]],
        "span_ids": sorted(
            selected_span["span_id"] for selected_span in selected_spans
        ),
        "charter_id": charter["charter_id"],
        "graph_id": graph["graph_id"],
        "interpretation_set_ids": [interpretation["interpretation_set_id"]],
        "signature_id": signature["signature_id"],
        "model_id": model["model_id"],
        "import_ids": [project_import["import_id"]],
        "bridge_id": bridge["bridge_id"],
        "unresolved_record_ids": sorted(
            [
                labels_branch["interpretation_id"],
                project_import["import_id"],
                *([open_port["port_id"]] if include_open_port else []),
                delta["delta_id"],
                *(
                    [dependency_shift["delta_id"]]
                    if dependency_shift is not None
                    else []
                ),
            ]
        ),
        "record_closure_sha256": "",
    }
    snapshot["record_closure_sha256"] = compute_record_closure_sha256(top_records)
    _seal_record(snapshot)
    return {
        "snapshot": snapshot,
        "records": records,
        "source_bytes": source_bytes,
        "names": {
            "document": document,
            "span": span,
            "charter": charter,
            "graph": graph,
            "interpretation": interpretation,
            "signature": signature,
            "model": model,
            "project_import": project_import,
            "bridge": bridge,
            "causal_branch": causal_branch,
            "labels_branch": labels_branch,
            "open_port": open_port,
            "delta": delta,
            "dependency_shift": dependency_shift,
            "role_clause": role_clause,
        },
    }


def _replace_bridge(bundle: dict[str, object], changed: dict[str, object]) -> None:
    snapshot = bundle["snapshot"]
    records = bundle["records"]
    old_id = snapshot["bridge_id"]
    _seal_record(changed)
    del records[old_id]
    records[changed["bridge_id"]] = changed
    snapshot["bridge_id"] = changed["bridge_id"]
    snapshot["record_closure_sha256"] = compute_record_closure_sha256(
        _selected_records(snapshot, records)
    )
    _seal_record(snapshot)


def _replace_model(bundle: dict[str, object], changed: dict[str, object]) -> None:
    snapshot = bundle["snapshot"]
    records = bundle["records"]
    old_model_id = snapshot["model_id"]
    old_bridge_id = snapshot["bridge_id"]
    _seal_record(changed)
    del records[old_model_id]
    records[changed["model_id"]] = changed
    snapshot["model_id"] = changed["model_id"]
    bridge = copy.deepcopy(records[old_bridge_id])
    bridge["model_id"] = changed["model_id"]
    _seal_record(bridge)
    del records[old_bridge_id]
    records[bridge["bridge_id"]] = bridge
    snapshot["bridge_id"] = bridge["bridge_id"]
    snapshot["record_closure_sha256"] = compute_record_closure_sha256(
        _selected_records(snapshot, records)
    )
    _seal_record(snapshot)


class TranslationRecordRuntimeTests(unittest.TestCase):
    def test_inventory_accepts_exactly_one_canonical_file_per_record(self) -> None:
        document = _bundle()["names"]["document"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "document.json"
            path.write_bytes(canonical_bytes(document) + b"\n")

            inventory = load_translation_inventory(Path(directory))

        self.assertEqual(inventory, {document["document_id"]: document})

    def test_inventory_rejects_noncanonical_file_bytes(self) -> None:
        document = _bundle()["names"]["document"]
        canonical = canonical_bytes(document)
        cases = {
            "missing-newline": canonical,
            "leading-space": b" " + canonical + b"\n",
            "extra-newline": canonical + b"\n\n",
        }
        for name, payload in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                (Path(directory) / "document.json").write_bytes(payload)
                with self.assertRaisesRegex(RecordError, "not canonical JSON"):
                    load_translation_inventory(Path(directory))

    def test_inventory_rejects_duplicate_record_ids_even_when_equal(self) -> None:
        document = _bundle()["names"]["document"]
        payload = canonical_bytes(document) + b"\n"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "a.json").write_bytes(payload)
            (root / "nested").mkdir()
            (root / "nested" / "b.json").write_bytes(payload)

            with self.assertRaisesRegex(RecordError, "duplicate translation record ID"):
                load_translation_inventory(root)

    def test_full_slice_is_schema_valid_and_operationally_valid(self) -> None:
        bundle = _bundle()
        catalog = load_local_schema_catalog(ROOT / "forge" / "schema")
        for record in bundle["records"].values():
            schema_file = TRANSLATION_SCHEMA_TO_FILE[record["schema_version"]]
            with self.subTest(schema=schema_file):
                catalog.validate(record, schema_file)
                id_field = TRANSLATION_SCHEMA_TO_ID[record["schema_version"]][1]
                self.assertEqual(validate_translation_record(record), record[id_field])
        snapshot = bundle["snapshot"]
        catalog.validate(snapshot, "translation-snapshot.schema.json")
        result = validate_translation_snapshot(snapshot, bundle["records"])
        self.assertEqual(result.operational_status, "TRANSLATION_INTEGRITY_VALID")
        self.assertEqual(result.mapping_fidelity, "UNREVIEWED")
        self.assertIsNone(result.semantic_verdict)
        self.assertIn("do not confirm", NON_INDUCTIVE_TRANSLATION_LIMIT)
        self.assertEqual(result.record_count, 10)

    def test_branch_source_spans_must_cover_interpreted_obligations(self) -> None:
        bundle = _bundle(labels_use_unrelated_span=True)

        with self.assertRaisesRegex(
            RecordError,
            "source spans do not cover its interpreted obligations",
        ):
            validate_translation_snapshot(bundle["snapshot"], bundle["records"])

    def test_every_selected_span_requires_an_obligation_graph_role(self) -> None:
        bundle = _bundle()
        snapshot = bundle["snapshot"]
        records = bundle["records"]
        extra_span = copy.deepcopy(bundle["names"]["span"])
        extra_span["span_id"] = ""
        extra_span["span_key"] = "selected-but-unclassified"
        _seal_record(extra_span)
        records[extra_span["span_id"]] = extra_span
        snapshot["span_ids"] = sorted(
            [*snapshot["span_ids"], extra_span["span_id"]]
        )
        snapshot["record_closure_sha256"] = compute_record_closure_sha256(
            _selected_records(snapshot, records)
        )
        _seal_record(snapshot)

        with self.assertRaisesRegex(
            RecordError,
            "every selected source span must have exactly one TARGET or CONTEXT",
        ):
            validate_translation_snapshot(snapshot, records)

    def test_branch_can_preserve_features_only_from_interpreted_obligations(
        self,
    ) -> None:
        bundle = _bundle(labels_preserve_uninterpreted_feature=True)

        with self.assertRaisesRegex(
            RecordError,
            "preserves a feature outside its interpreted obligations",
        ):
            validate_translation_snapshot(bundle["snapshot"], bundle["records"])

    def test_project_import_affected_keys_must_equal_direct_model_bases(
        self,
    ) -> None:
        cases = {
            "missing-key": ("SystemBoundary",),
            "extra-key": (
                "BoundaryRequired",
                "GhostElement",
                "SystemBoundary",
            ),
        }
        for name, affected_element_keys in cases.items():
            with self.subTest(name=name):
                bundle = _bundle(
                    project_import_affected_element_keys=affected_element_keys,
                )
                with self.assertRaisesRegex(
                    PolicyViolation,
                    "affected_element_keys do not exactly match its direct model bases",
                ):
                    validate_translation_snapshot(
                        bundle["snapshot"],
                        bundle["records"],
                    )

    def test_open_port_must_name_an_affected_model_element(self) -> None:
        model = _bundle(open_port_has_affected_elements=False)["names"]["model"]

        with self.assertRaisesRegex(
            RecordError,
            "must name at least one affected member or clause",
        ):
            validate_translation_record(model)

    def test_unprojected_branch_requires_a_port_for_its_interpretation_set(
        self,
    ) -> None:
        bundle = _bundle(include_open_port=False)

        with self.assertRaisesRegex(
            PolicyViolation,
            "UNPROJECTED interpretation branch.*open port",
        ):
            validate_translation_snapshot(bundle["snapshot"], bundle["records"])

    def test_member_and_clause_element_keys_must_be_globally_disjoint(
        self,
    ) -> None:
        bundle = _bundle(causal_clause_element_key="CausalUse")

        with self.assertRaisesRegex(
            RecordError,
            "element_key values must be globally disjoint",
        ):
            validate_translation_snapshot(bundle["snapshot"], bundle["records"])

    def test_flat_model_cannot_conjoin_exclusive_rival_branches(self) -> None:
        bundle = _bundle()
        snapshot = bundle["snapshot"]
        records = bundle["records"]
        names = bundle["names"]

        labels_branch = copy.deepcopy(names["labels_branch"])
        labels_branch["model_effect"] = {
            "status": "DECLARED",
            "effect_statement": "Represent classification as label-exhaustion.",
            "affected_element_keys": ["LabelExhaustive"],
        }
        _seal_component("interpretation", labels_branch)
        interpretation = copy.deepcopy(names["interpretation"])
        old_interpretation_id = interpretation["interpretation_set_id"]
        interpretation["branches"] = sorted(
            [names["causal_branch"], labels_branch],
            key=lambda item: item["interpretation_id"],
        )
        interpretation["admissible_branch_sets"] = sorted(
            [
                [branch["interpretation_id"]]
                for branch in interpretation["branches"]
            ],
            key=canonical_bytes,
        )
        _seal_record(interpretation)
        del records[old_interpretation_id]
        records[interpretation["interpretation_set_id"]] = interpretation
        snapshot["interpretation_set_ids"] = [
            interpretation["interpretation_set_id"]
        ]

        label_member = _seal_component(
            "signature_member",
            {
                "member_id": "",
                "element_key": "LabelExhaustive",
                "kind": "PROPERTY",
                "statement": "The role is exhausted by its surface label.",
                "argument_roles": [],
                "identity_conditions": [],
                "variation_conditions": [],
                "scope_conditions": ["Inside the declared translation boundary."],
                "semantic_effect": "MEANING_BEARING",
                "basis": {
                    "premise_kind": "SOURCE_INTERPRETATION",
                    "record_ids": [labels_branch["interpretation_id"]],
                },
            },
        )
        signature = copy.deepcopy(names["signature"])
        old_signature_id = signature["signature_id"]
        signature["members"].append(label_member)
        signature["members"].sort(key=lambda item: item["member_id"])
        _seal_record(signature)
        del records[old_signature_id]
        records[signature["signature_id"]] = signature
        snapshot["signature_id"] = signature["signature_id"]

        model = copy.deepcopy(names["model"])
        old_model_id = model["model_id"]
        model["signature_id"] = signature["signature_id"]
        model["interpretation_ids"] = sorted(
            [
                names["causal_branch"]["interpretation_id"],
                labels_branch["interpretation_id"],
            ]
        )
        model["open_ports"] = []
        model["semantic_dependency_closure"]["members"].append(
            {
                "record_id": labels_branch["interpretation_id"],
                "premise_kind": "SOURCE_INTERPRETATION",
                "role": "DIRECT",
            }
        )
        model["semantic_dependency_closure"]["members"].sort(
            key=lambda item: item["record_id"]
        )
        model["semantic_dependency_closure"]["closure_sha256"] = (
            compute_semantic_dependency_closure_sha256(
                model["semantic_dependency_closure"]
            )
        )
        model["theory_projection"]["signature_id"] = signature["signature_id"]
        model["theory_projection"]["member_ids"].append(label_member["member_id"])
        model["theory_projection"]["member_ids"].sort()
        model["theory_projection"]["theory_record_sha256"] = (
            compute_theory_record_sha256(model["theory_projection"])
        )
        _seal_record(model)
        del records[old_model_id]
        records[model["model_id"]] = model
        snapshot["model_id"] = model["model_id"]

        reverse_mapping = _seal_component(
            "reverse_mapping",
            {
                "mapping_id": "",
                "model_element_id": label_member["member_id"],
                "basis_kind": "SOURCE_INTERPRETATION",
                "basis_ids": [labels_branch["interpretation_id"]],
                "source_obligation_ids": sorted(
                    obligation["obligation_id"]
                    for obligation in names["graph"]["obligations"]
                ),
                "back_translation": "The role is exhausted by its surface label.",
                "semantic_effect": "MEANING_BEARING",
            },
        )
        bridge = copy.deepcopy(names["bridge"])
        old_bridge_id = bridge["bridge_id"]
        bridge["interpretation_set_ids"] = [
            interpretation["interpretation_set_id"]
        ]
        bridge["signature_id"] = signature["signature_id"]
        bridge["model_id"] = model["model_id"]
        bridge["reverse_mappings"].append(reverse_mapping)
        bridge["reverse_mappings"].sort(key=lambda item: item["mapping_id"])
        _seal_record(bridge)
        del records[old_bridge_id]
        records[bridge["bridge_id"]] = bridge
        snapshot["bridge_id"] = bridge["bridge_id"]

        snapshot["unresolved_record_ids"] = sorted(
            record_id
            for record_id in snapshot["unresolved_record_ids"]
            if record_id
            not in {
                names["labels_branch"]["interpretation_id"],
                names["open_port"]["port_id"],
            }
        )
        snapshot["record_closure_sha256"] = compute_record_closure_sha256(
            _selected_records(snapshot, records)
        )
        _seal_record(snapshot)

        with self.assertRaisesRegex(PolicyViolation, "explicitly admissible branch set"):
            validate_translation_snapshot(snapshot, records)

    def test_rival_relations_require_explicit_admissible_branch_sets(self) -> None:
        overlapping = copy.deepcopy(_bundle()["names"]["interpretation"])
        overlapping["rival_relation"] = "OVERLAPPING"
        _seal_record(overlapping)
        with self.assertRaisesRegex(PolicyViolation, "full branch set"):
            validate_translation_record(overlapping)

        branch_ids = [
            branch["interpretation_id"] for branch in overlapping["branches"]
        ]
        overlapping["admissible_branch_sets"] = sorted(
            [*overlapping["admissible_branch_sets"], branch_ids],
            key=canonical_bytes,
        )
        _seal_record(overlapping)
        validate_translation_record(overlapping)

        partial = copy.deepcopy(overlapping)
        partial["rival_relation"] = "PARTIALLY_COMPATIBLE"
        _seal_record(partial)
        with self.assertRaisesRegex(PolicyViolation, "at least three branches"):
            validate_translation_record(partial)

    def test_every_nested_component_id_is_recomputed(self) -> None:
        names = _bundle()["names"]
        components: list[tuple[str, dict[str, object]]] = []
        charter = names["charter"]
        components.append(("protected_distinction", charter["protected_distinctions"][0]))
        graph = names["graph"]
        for obligation in graph["obligations"]:
            components.extend(
                [
                    ("obligation", obligation),
                    ("source_claim", obligation["source_claim"]),
                    ("translation_duty", obligation["translation_duty"]),
                ]
            )
            components.extend(
                ("protected_feature", feature)
                for feature in obligation["translation_duty"]["protected_features"]
            )
        components.extend(("obligation_edge", edge) for edge in graph["edges"])
        interpretation = names["interpretation"]
        components.extend(("interpretation", branch) for branch in interpretation["branches"])
        signature = names["signature"]
        components.extend(("signature_member", member) for member in signature["members"])
        model = names["model"]
        components.extend(("model_clause", clause) for clause in model["clauses"])
        components.extend(("model_open_port", port) for port in model["open_ports"])
        bridge = names["bridge"]
        components.extend(("forward_mapping", item) for item in bridge["forward_mappings"])
        components.extend(("reverse_mapping", item) for item in bridge["reverse_mappings"])
        components.extend(("translation_delta", item) for item in bridge["translation_deltas"])
        self.assertEqual({kind for kind, _item in components}, set(TRANSLATION_COMPONENT_ID_SPECS))
        for kind, component in components:
            id_field = TRANSLATION_COMPONENT_ID_SPECS[kind][2]
            with self.subTest(kind=kind, identifier=component[id_field]):
                self.assertEqual(
                    component[id_field],
                    compute_named_translation_component_id(kind, component),
                )

    def test_nested_id_tampering_is_rejected_even_when_parent_is_resealed(self) -> None:
        bundle = _bundle()
        charter = copy.deepcopy(bundle["names"]["charter"])
        charter["protected_distinctions"][0]["statement"] += " Changed."
        _seal_record(charter)
        with self.assertRaisesRegex(RecordError, "protected_distinction"):
            validate_translation_record(charter)

        graph = copy.deepcopy(bundle["names"]["graph"])
        obligation = graph["obligations"][0]
        obligation["translation_duty"]["protected_features"][0]["statement"] += " Changed."
        _seal_component("translation_duty", obligation["translation_duty"])
        _seal_component("obligation", obligation)
        graph["obligations"].sort(key=lambda item: item["obligation_id"])
        _seal_record(graph)
        with self.assertRaisesRegex(RecordError, "protected_feature"):
            validate_translation_record(graph)

        graph_cases = (
            ("source_claim", "source_claim", "statement"),
            ("translation_duty", "translation_duty", "statement"),
        )
        for kind, child_key, field in graph_cases:
            changed = copy.deepcopy(bundle["names"]["graph"])
            changed_obligation = changed["obligations"][0]
            changed_obligation[child_key][field] += " Changed."
            _seal_component("obligation", changed_obligation)
            changed["obligations"].sort(key=lambda item: item["obligation_id"])
            _seal_record(changed)
            with self.subTest(kind=kind), self.assertRaisesRegex(RecordError, kind):
                validate_translation_record(changed)

        graph = copy.deepcopy(bundle["names"]["graph"])
        target_obligation = graph["obligations"][0]
        target_obligation["depends_on_obligation_ids"] = (
            []
            if target_obligation["depends_on_obligation_ids"]
            else [graph["obligations"][1]["obligation_id"]]
        )
        _seal_record(graph)
        with self.assertRaisesRegex(RecordError, "obligation"):
            validate_translation_record(graph)

        graph = copy.deepcopy(bundle["names"]["graph"])
        graph["edges"][0]["statement"] += " Changed."
        _seal_record(graph)
        with self.assertRaisesRegex(RecordError, "obligation_edge"):
            validate_translation_record(graph)

        direct_cases = (
            ("interpretation", "branches", "interpretation", "statement"),
            ("signature", "members", "signature_member", "statement"),
            ("model", "clauses", "model_clause", "operative_prose"),
            ("model", "open_ports", "model_open_port", "question"),
            ("bridge", "forward_mappings", "forward_mapping", "back_translation"),
            ("bridge", "reverse_mappings", "reverse_mapping", "back_translation"),
            ("bridge", "translation_deltas", "translation_delta", "statement"),
        )
        for record_name, collection, kind, field in direct_cases:
            changed = copy.deepcopy(bundle["names"][record_name])
            changed[collection][0][field] += " Changed."
            _seal_record(changed)
            with self.subTest(kind=kind), self.assertRaisesRegex(RecordError, kind):
                validate_translation_record(changed)

    def test_wrong_pdf_index_is_rejected_under_a_fresh_record_id(self) -> None:
        span = copy.deepcopy(_bundle()["names"]["span"])
        span["segments"][0]["locator"]["page_index_zero_based"] = 1
        _seal_record(span)
        with self.assertRaisesRegex(RecordError, "page index"):
            validate_translation_record(span)

    def test_provenance_timestamp_is_runtime_checked_as_rfc3339(self) -> None:
        document = copy.deepcopy(_bundle()["names"]["document"])
        document["provenance"]["created_at"] = "not-a-date"
        _seal_record(document)
        with self.assertRaisesRegex(RecordError, "RFC 3339"):
            validate_translation_record(document)

    def test_unresolved_generation_provenance_cannot_disappear(self) -> None:
        bundle = _bundle()
        generation_id = "GEN:" + "a" * 64
        model = copy.deepcopy(bundle["names"]["model"])
        model["provenance"] = {
            "producer_kind": "LLM",
            "producer_id": "fixture-generator",
            "created_at": "2026-09-03T00:00:00Z",
            "generation_record_ids": [generation_id],
        }
        _replace_model(bundle, model)

        with self.assertRaisesRegex(PolicyViolation, "mechanically open"):
            validate_translation_snapshot(bundle["snapshot"], bundle["records"])

        snapshot = bundle["snapshot"]
        snapshot["unresolved_record_ids"] = sorted(
            [*snapshot["unresolved_record_ids"], generation_id]
        )
        _seal_record(snapshot)
        result = validate_translation_snapshot(snapshot, bundle["records"])
        self.assertIn(generation_id, result.unresolved_record_ids)

    def test_model_digests_are_not_decorative(self) -> None:
        model = copy.deepcopy(_bundle()["names"]["model"])
        model["semantic_dependency_closure"]["closure_sha256"] = "sha256:" + "0" * 64
        _seal_record(model)
        with self.assertRaisesRegex(RecordError, "closure digest"):
            validate_translation_record(model)

        model = copy.deepcopy(_bundle()["names"]["model"])
        model["theory_projection"]["theory_record_sha256"] = "sha256:" + "0" * 64
        _seal_record(model)
        with self.assertRaisesRegex(RecordError, "theory projection digest"):
            validate_translation_record(model)

    def test_cross_record_dependency_closure_must_be_exact(self) -> None:
        bundle = _bundle()
        model = copy.deepcopy(bundle["names"]["model"])
        source_member = next(
            item
            for item in model["semantic_dependency_closure"]["members"]
            if item["premise_kind"] == "SOURCE_AUTHORITY"
        )
        source_member["role"] = "DIRECT"
        model["semantic_dependency_closure"]["closure_sha256"] = (
            compute_semantic_dependency_closure_sha256(
                model["semantic_dependency_closure"]
            )
        )
        _replace_model(bundle, model)
        with self.assertRaisesRegex(RecordError, "dependency closure"):
            validate_translation_snapshot(bundle["snapshot"], bundle["records"])

    def test_two_way_bridge_must_be_total_in_both_directions(self) -> None:
        bundle = _bundle()
        bridge = copy.deepcopy(bundle["names"]["bridge"])
        bridge["reverse_mappings"] = bridge["reverse_mappings"][1:]
        _replace_bridge(bundle, bridge)
        with self.assertRaisesRegex(RecordError, "every model element"):
            validate_translation_snapshot(bundle["snapshot"], bundle["records"])

    def test_reverse_source_trace_must_equal_direct_element_incidence(self) -> None:
        bundle = _bundle()
        bridge = copy.deepcopy(bundle["names"]["bridge"])
        mapping = next(
            item
            for item in bridge["reverse_mappings"]
            if item["basis_kind"] == "SOURCE_INTERPRETATION"
        )
        all_obligation_ids = {
            obligation["obligation_id"]
            for obligation in bundle["names"]["graph"]["obligations"]
        }
        mapping["source_obligation_ids"] = sorted(
            all_obligation_ids.union(mapping["source_obligation_ids"])
        )
        _seal_component("reverse_mapping", mapping)
        bridge["reverse_mappings"].sort(key=lambda item: item["mapping_id"])
        _replace_bridge(bundle, bridge)
        with self.assertRaisesRegex(
            RecordError,
            "direct forward element incidence",
        ):
            validate_translation_snapshot(bundle["snapshot"], bundle["records"])

    def test_source_dependency_requires_correctly_directed_clause_path(self) -> None:
        forward = _bundle(dependency_mode="FORWARD")
        validate_translation_snapshot(
            forward["snapshot"],
            forward["records"],
        )

        for mode in ("NONE", "REVERSED"):
            bundle = _bundle(dependency_mode=mode)
            with self.subTest(mode=mode), self.assertRaisesRegex(
                PolicyViolation,
                "exclusively correctly directed positive-length TNMC dependency path",
            ):
                validate_translation_snapshot(
                    bundle["snapshot"],
                    bundle["records"],
                )

    def test_logical_source_dependency_edges_cannot_be_duplicated(self) -> None:
        graph = copy.deepcopy(_bundle()["names"]["graph"])
        duplicate = copy.deepcopy(graph["edges"][0])
        duplicate["statement"] += " Duplicate wording."
        _seal_component("obligation_edge", duplicate)
        graph["edges"].append(duplicate)
        graph["edges"].sort(key=lambda item: item["edge_id"])
        _seal_record(graph)

        with self.assertRaisesRegex(RecordError, "logical DEPENDS_ON edges"):
            validate_translation_record(graph)

    def test_exact_open_dependency_shift_exposes_v1_direction_limit(self) -> None:
        bundle = _bundle(
            dependency_mode="REVERSED",
            include_dependency_shift=True,
        )

        result = validate_translation_snapshot(
            bundle["snapshot"],
            bundle["records"],
        )

        self.assertEqual(result.operational_status, "TRANSLATION_INTEGRITY_VALID")
        self.assertIn(
            bundle["names"]["dependency_shift"]["delta_id"],
            result.unresolved_record_ids,
        )

        malformed = _bundle(
            dependency_mode="REVERSED",
            include_dependency_shift=True,
            exact_dependency_shift_footprint=False,
        )
        with self.assertRaisesRegex(
            PolicyViolation,
            "complete mapped-element footprint",
        ):
            validate_translation_snapshot(
                malformed["snapshot"],
                malformed["records"],
            )

    def test_semantic_scoring_fields_are_rejected(self) -> None:
        project_import = copy.deepcopy(_bundle()["names"]["project_import"])
        project_import["confidence"] = 99
        _seal_record(project_import)
        with self.assertRaises(PolicyViolation):
            validate_translation_record(project_import)

    def test_charter_cannot_place_the_same_item_in_and_out_of_scope(self) -> None:
        charter = copy.deepcopy(_bundle()["names"]["charter"])
        charter["out_of_scope"] = [charter["in_scope"][0]]
        _seal_record(charter)
        with self.assertRaisesRegex(PolicyViolation, "in and out of scope"):
            validate_translation_record(charter)

    def test_source_byte_check_proves_identity_not_meaning(self) -> None:
        bundle = _bundle()
        document = bundle["names"]["document"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "authority.pdf"
            path.write_bytes(bundle["source_bytes"])
            verify_source_document_bytes(document, path)
            path.write_bytes(bundle["source_bytes"] + b"mutation")
            with self.assertRaisesRegex(RecordError, "do not match"):
                verify_source_document_bytes(document, path)


if __name__ == "__main__":
    unittest.main()
