"""Fail-closed orchestration for the generic semantic-translation harness.

This module composes existing validators.  Its output is a runtime report, not
a new record family, and therefore has no content ID or ``schema_version``.
Passing a stage establishes only the narrow operational claim named by that
stage.  It never establishes source meaning, model truth, or mapping fidelity.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from creib.canonical import domain_digest
from creib.errors import PolicyViolation, RecordError
from creib.strict_json import load_strict

from .generic_inquiry import validate_generic_inquiry_plan
from .hardening import (
    resolve_hardening_comparison,
    validate_hardening_comparison,
    validate_hardening_resolution,
)
from .qualification import (
    ALL_REPRODUCED,
    freeze_translation_snapshot,
    qualify_exposure_report,
    validate_freeze_record,
)
from .translation import (
    TranslationValidationResult,
    load_translation_inventory,
    translation_record_digest,
    validate_translation_snapshot,
)
from .source_replay import replay_translation_sources
from .translation_review import (
    REVIEW_SCHEMA,
    translation_review_bindings,
    translation_review_surface,
    verify_translation_review_chain,
)
from .translation_tests import (
    synthesize_translation_tests,
    validate_translation_test_synthesis,
)


NOT_SUPPLIED = "NOT_SUPPLIED"
INVALID = "INVALID"
BLOCKED = "BLOCKED"
UNRESOLVED = "UNRESOLVED"
STRUCTURALLY_VALID = "STRUCTURALLY_VALID"
READY = "READY"

STAGE_STATUSES = frozenset(
    {NOT_SUPPLIED, INVALID, BLOCKED, UNRESOLVED, STRUCTURALLY_VALID, READY}
)

STAGE_ORDER = (
    "translation_integrity",
    "source_identity",
    "charter",
    "obligation_graph",
    "interpretation_rivals",
    "neutral_model",
    "two_way_bridge",
    "interpretation_review",
    "dynamic_test_synthesis",
    "research_routing_readiness",
    "iteration_lineage",
    "hardening",
    "qualification",
)

REPORT_LIMIT = (
    "This runtime report establishes only the stated structural, workflow, "
    "test-synthesis, routing, hardening, and qualification conditions. It "
    "cannot confirm source meaning, mapping fidelity, model truth, or a unique "
    "failure locus."
)

_REVIEW_READY = frozenset({"SCOPED_USE_AUTHORIZED"})
_REVIEW_BLOCKED = frozenset({"REJECTED_FOR_SCOPE"})
_ACTIONABLE_ROUTES = frozenset(
    {
        "INTERNAL_HARNESS_WORK",
        "INTERNAL_MODEL_WORK",
        "AUTHORITY_REVIEW",
        "EXTERNAL_RESEARCH_REQUIRED",
    }
)
_ASSESSMENT_ROUTES = {
    "INTERNAL_HARNESS_SPECIFICATION": "INTERNAL_HARNESS_WORK",
    "INTERNAL_DEDUCTION_OR_MODEL_FINDING": "INTERNAL_MODEL_WORK",
    "CR_AUTHORITY_INTERPRETATION": "AUTHORITY_REVIEW",
    "EXTERNAL_CRITICAL_INSTRUMENT": "EXTERNAL_RESEARCH_REQUIRED",
    "APPLICATION_EMPIRICAL": "EXTERNAL_RESEARCH_REQUIRED",
}


def _load_object(path: Path, where: str) -> dict[str, Any]:
    if not isinstance(path, Path):
        raise TypeError(f"{where} path must be pathlib.Path")
    value = load_strict(path)
    if type(value) is not dict:
        raise RecordError(f"{where} must contain a JSON object")
    return value


def _error(exc: Exception) -> dict[str, str]:
    return {"error_type": type(exc).__name__, "error": str(exc)}


def _stage(
    status: str,
    claim: str,
    *,
    details: Mapping[str, Any] | None = None,
    next_actions: Sequence[str] = (),
    error: Exception | None = None,
) -> dict[str, Any]:
    if status not in STAGE_STATUSES:
        raise ValueError(f"unsupported pipeline stage status: {status}")
    result: dict[str, Any] = {
        "status": status,
        "claim": claim,
        "details": dict(details or {}),
        "next_actions": list(next_actions),
        "semantic_verdict": None,
        "mapping_fidelity": "UNREVIEWED",
    }
    if error is not None:
        result["error"] = _error(error)
    return result


def _blocked_stage(prerequisite: str) -> dict[str, Any]:
    return _stage(
        BLOCKED,
        "This stage was not evaluated because a required prior binding failed.",
        details={"blocked_by": prerequisite},
        next_actions=(f"Resolve {prerequisite} and rerun this stage.",),
    )


def _selected_record_ids(snapshot: Mapping[str, Any]) -> dict[str, set[str]]:
    """Group unresolved IDs without interpreting what their failure means."""

    return {
        "source_identity": set(snapshot["document_ids"]) | set(snapshot["span_ids"]),
        "charter": {str(snapshot["charter_id"])},
        "neutral_model": {
            str(snapshot["signature_id"]),
            str(snapshot["model_id"]),
            *snapshot["import_ids"],
        },
        "two_way_bridge": {str(snapshot["bridge_id"])},
    }


def _translation_stages(
    snapshot: dict[str, Any],
    records: Mapping[str, Mapping[str, Any]],
    validation: TranslationValidationResult,
    source_documents: Mapping[str, Path],
    transcription_root: Path,
) -> dict[str, dict[str, Any]]:
    unresolved = set(validation.unresolved_record_ids)
    grouped = _selected_record_ids(snapshot)
    graph = records[str(snapshot["graph_id"])]
    interpretations = [
        records[str(record_id)] for record_id in snapshot["interpretation_set_ids"]
    ]
    grouped["obligation_graph"] = {str(snapshot["graph_id"])}
    for obligation in graph["obligations"]:
        grouped["obligation_graph"].update(
            {
                str(obligation["obligation_id"]),
                str(obligation["source_claim"]["claim_id"]),
                str(obligation["translation_duty"]["duty_id"]),
                *(
                    str(feature["feature_id"])
                    for feature in obligation["translation_duty"]["protected_features"]
                ),
            }
        )
    grouped["obligation_graph"].update(
        str(edge["edge_id"]) for edge in graph["edges"]
    )
    grouped["interpretation_rivals"] = set(snapshot["interpretation_set_ids"]) | {
        str(branch["interpretation_id"])
        for record in interpretations
        for branch in record["branches"]
    }
    model = records[str(snapshot["model_id"])]
    grouped["neutral_model"].update(
        str(member["member_id"])
        for member in records[str(snapshot["signature_id"])]["members"]
    )
    grouped["neutral_model"].update(
        str(clause["clause_id"]) for clause in model["clauses"]
    )
    grouped["neutral_model"].update(
        str(port["port_id"]) for port in model["open_ports"]
    )
    bridge = records[str(snapshot["bridge_id"])]
    grouped["two_way_bridge"].update(
        str(mapping["mapping_id"])
        for mapping in (*bridge["forward_mappings"], *bridge["reverse_mappings"])
    )
    grouped["two_way_bridge"].update(
        str(delta["delta_id"]) for delta in bridge["translation_deltas"]
    )

    integrity_status = UNRESOLVED if unresolved else STRUCTURALLY_VALID
    stages: dict[str, dict[str, Any]] = {
        "translation_integrity": _stage(
            integrity_status,
            "The selected record closure and its cross-record references are structurally valid.",
            details={
                "snapshot_id": validation.snapshot_id,
                "record_count": validation.record_count,
                "unresolved_record_ids": list(validation.unresolved_record_ids),
            },
            next_actions=(
                "Resolve or explicitly preserve every unresolved record before downstream use.",
            )
            if unresolved
            else (),
        )
    }

    component_claims = {
        "charter": "The translation charter record and its snapshot binding are structurally valid.",
        "obligation_graph": "The obligation graph is structurally valid and bound to the selected charter and spans.",
        "interpretation_rivals": "The rival interpretation sets are structurally valid and remain unranked.",
        "neutral_model": "The neutral signature, model, and declared imports are structurally valid.",
        "two_way_bridge": "The two-way bridge has complete structural forward and reverse coverage.",
    }
    for name, claim in component_claims.items():
        open_ids = sorted(unresolved.intersection(grouped[name]))
        stages[name] = _stage(
            UNRESOLVED if open_ids else STRUCTURALLY_VALID,
            claim,
            details={"unresolved_ids": open_ids},
            next_actions=(
                f"Review the unresolved {name.replace('_', ' ')} IDs: {', '.join(open_ids)}.",
            )
            if open_ids
            else (),
        )

    selected_documents = tuple(str(item) for item in snapshot["document_ids"])
    unknown_bindings = sorted(set(source_documents).difference(selected_documents))
    missing_bindings = sorted(set(selected_documents).difference(source_documents))
    source_open = sorted(unresolved.intersection(grouped["source_identity"]))
    if unknown_bindings:
        stages["source_identity"] = _stage(
            INVALID,
            "A supplied source-byte binding names a document outside the selected snapshot.",
            details={
                "unknown_document_ids": unknown_bindings,
                "selected_document_ids": list(selected_documents),
            },
            next_actions=("Remove or correct every unknown source-document binding.",),
        )
    elif not source_documents:
        stages["source_identity"] = _stage(
            UNRESOLVED,
            "Source-document records are structurally bound, but external source bytes were not supplied for replay.",
            details={
                "source_bytes_input": NOT_SUPPLIED,
                "selected_document_ids": list(selected_documents),
                "unresolved_ids": source_open,
            },
            next_actions=(
                "Supply the exact byte artifact for every selected document ID and rerun source identity.",
            ),
        )
    elif missing_bindings:
        stages["source_identity"] = _stage(
            BLOCKED,
            "Only part of the selected source-byte inventory was supplied.",
            details={
                "supplied_document_ids": sorted(
                    set(selected_documents).intersection(source_documents)
                ),
                "missing_document_ids": missing_bindings,
            },
            next_actions=(
                "Supply one exact source-byte path for each missing document ID.",
            ),
        )
    else:
        try:
            replay = replay_translation_sources(
                snapshot=snapshot,
                validation=validation,
                records=records,
                source_documents=source_documents,
                transcription_root=transcription_root,
            )
        except Exception as exc:
            stages["source_identity"] = _stage(
                INVALID,
                "A supplied source artifact, locator, literal snapshot, transcription, or verbatim claim failed exact replay.",
                details={"selected_document_ids": list(selected_documents)},
                next_actions=(
                    "Restore the exact bound material or create new superseding source records; do not repair an immutable record in place.",
                ),
                error=exc,
            )
        else:
            replay_details = replay.details()
            replay_details["unresolved_ids"] = source_open
            complete = replay.complete and not source_open
            stages["source_identity"] = _stage(
                STRUCTURALLY_VALID if complete else UNRESOLVED,
                (
                    "Every selected source byte binding, locator, literal snapshot, optional transcription, and verbatim claim text replays exactly."
                    if complete
                    else "Source replay remains incomplete; no listed unresolved claim is mechanically grounded."
                ),
                details=replay_details,
                next_actions=()
                if complete
                else (
                    "Resolve every listed replay limitation with an executable, version-bound profile and rerun source identity.",
                ),
            )
    return stages


def _review_stage(
    *,
    review_dir: Path | None,
    review_head_id: str | None,
    snapshot: dict[str, Any] | None,
    records: Mapping[str, Mapping[str, Any]] | None,
) -> dict[str, Any]:
    if review_dir is None and review_head_id is None:
        return _stage(
            NOT_SUPPLIED,
            "No append-only human interpretation-review lineage was supplied.",
            next_actions=(
                "Create a review surface and record human dispositions without treating selection as confirmation.",
            ),
        )
    if review_dir is None:
        return _stage(
            BLOCKED,
            "A review head was supplied without its append-only review directory.",
            next_actions=("Supply the review directory containing the selected lineage.",),
        )
    if snapshot is None or records is None:
        return _blocked_stage("translation_integrity")
    try:
        interpretation_sets = tuple(
            records[str(record_id)] for record_id in snapshot["interpretation_set_ids"]
        )
        bindings = translation_review_bindings(snapshot)
        surface = translation_review_surface(snapshot, interpretation_sets)
        state = verify_translation_review_chain(
            review_dir,
            review_head_id,
            expected_bindings=bindings if review_head_id is not None else None,
            expected_surface=surface if review_head_id is not None else None,
        )
        if state.workflow_status in _REVIEW_READY and (
            state.current_scope_binding is None or not state.authorized_variants
        ):
            raise PolicyViolation(
                "an authorized review state requires an exact scope and model variant"
            )
        if state.current_scope_binding is not None:
            charter = records[str(snapshot["charter_id"])]
            scope = state.current_scope_binding
            if (
                scope["charter_id"] != snapshot["charter_id"]
                or scope["purpose"] != charter["purpose"]
                or scope["system_boundary"] != charter["system_boundary"]
                or not set(scope["in_scope"]).issubset(set(charter["in_scope"]))
            ):
                raise PolicyViolation(
                    "review scope does not reproduce the current charter purpose, "
                    "boundary, and an exact nonempty in-scope subset"
                )
        if state.authorized_variants:
            if len(state.authorized_variants) != 1:
                raise PolicyViolation(
                    "one translation snapshot can authorize exactly one current "
                    "model projection"
                )
            selected_interpretations = {
                str(selection["interpretation_id"])
                for selection in state.authorized_variants[0]["selections"]
            }
            model_interpretations = set(
                records[str(snapshot["model_id"])]["interpretation_ids"]
            )
            if selected_interpretations != model_interpretations:
                raise PolicyViolation(
                    "authorized review branches do not exactly equal the current "
                    "neutral model interpretation bases"
                )
    except Exception as exc:
        return _stage(
            INVALID,
            "The supplied interpretation-review lineage failed integrity or current-snapshot binding checks.",
            next_actions=("Repair by appending a correctly bound successor; do not overwrite prior review bytes.",),
            error=exc,
        )

    workflow_status = state.workflow_status
    if workflow_status in _REVIEW_READY:
        status = READY
        actions = (
            "Use only the explicitly authorized variants and declared scope; keep rival and uncertainty records live.",
        )
    elif workflow_status in _REVIEW_BLOCKED:
        status = BLOCKED
        actions = (
            "Revise the translation candidate or reframe the scope before requesting another human review.",
        )
    elif workflow_status == "SCOPED_USE_SELECTED_AUTHENTICATION_REQUIRED":
        status = UNRESOLVED
        actions = (
            "Attach a separately authenticated approval event before treating the scoped selection as authorized.",
        )
    else:
        status = UNRESOLVED
        actions = (
            "Record the next human review decision or preserve the suspension as unresolved.",
        )
    return _stage(
        status,
        "The review lineage is internally valid; its workflow state grants no semantic verdict.",
        details={
            "head_review_id": state.head_review_id,
            "review_count": len(state.reviews),
            "workflow_status": workflow_status,
            "current_decision_id": state.current_decision_id,
            "effective_branch_states": state.effective_branch_states,
            "reviewer_authentication": state.reviewer_authentication,
            "current_scope_binding": state.current_scope_binding,
            "authorized_variants": list(state.authorized_variants),
            "head_review_sha256": (
                None
                if not state.reviews
                else domain_digest(
                    f"{REVIEW_SCHEMA}.complete-record", state.reviews[-1]
                )
            ),
        },
        next_actions=actions,
    )


def _dynamic_test_stage(
    *,
    old_snapshot_path: Path | None,
    delta_path: Path | None,
    snapshot: dict[str, Any] | None,
) -> dict[str, Any]:
    if old_snapshot_path is None and delta_path is None:
        return _stage(
            NOT_SUPPLIED,
            "No predecessor snapshot and exact translation delta were supplied for dynamic test synthesis.",
            next_actions=(
                "Supply a content-addressed predecessor snapshot and its exact delta to synthesize all test families.",
            ),
        )
    missing = [
        name
        for name, value in (
            ("old_snapshot", old_snapshot_path),
            ("translation_delta", delta_path),
        )
        if value is None
    ]
    if missing:
        return _stage(
            BLOCKED,
            "Dynamic test synthesis requires both sides of the translation change.",
            details={"missing_inputs": missing},
            next_actions=(f"Supply the missing inputs: {', '.join(missing)}.",),
        )
    if snapshot is None:
        return _blocked_stage("translation_integrity")
    try:
        old_snapshot = _load_object(old_snapshot_path, "old translation snapshot")  # type: ignore[arg-type]
        delta = _load_object(delta_path, "translation delta")  # type: ignore[arg-type]
        if snapshot.get("predecessor_snapshot_id") != old_snapshot.get("snapshot_id"):
            raise PolicyViolation(
                "new translation snapshot does not name the supplied old snapshot as its predecessor"
            )
        synthesis = synthesize_translation_tests(old_snapshot, snapshot, delta)
        validate_translation_test_synthesis(
            synthesis,
            old_snapshot=old_snapshot,
            new_snapshot=snapshot,
            delta=delta,
        )
    except Exception as exc:
        return _stage(
            INVALID,
            "The supplied snapshots or delta could not produce a valid deterministic test synthesis.",
            next_actions=("Repair the exact snapshot/delta bindings and regenerate the synthesis.",),
            error=exc,
        )

    rows = synthesis["coverage"]
    missing_rows = [row for row in rows if row["missing_semantic_bindings"]]
    actions = tuple(
        "Bind "
        + str(row["family"])
        + " with: "
        + ", ".join(row["missing_semantic_bindings"])
        + "; then record a typed human-authored expectation."
        for row in missing_rows
    )
    return _stage(
        UNRESOLVED if missing_rows else READY,
        "All deterministic test families were synthesized; missing semantic bindings remain explicit rather than guessed.",
        details={
            "synthesis_id": synthesis["synthesis_id"],
            "overall_status": synthesis["overall_status"],
            "family_coverage": [
                {
                    "family": row["family"],
                    "coverage_status": row["coverage_status"],
                    "missing_semantic_bindings": row["missing_semantic_bindings"],
                }
                for row in rows
            ],
            "research_authorized": False,
        },
        next_actions=actions
        or (
            "Execute the bound tests and route every criticism without inferring a unique failure locus.",
        ),
    )


def _research_stage(
    plan_paths: Sequence[Path], snapshot: Mapping[str, Any] | None
) -> dict[str, Any]:
    if not plan_paths:
        return _stage(
            NOT_SUPPLIED,
            "No stage-neutral inquiry plan was supplied for criticism routing.",
            next_actions=(
                "Create one inquiry plan per bound observation, then record human locus assessments and actions.",
            ),
        )
    if snapshot is None:
        return _blocked_stage("translation_integrity")
    expected_snapshot_binding = {
        "role": "TRANSLATION_SNAPSHOT",
        "subject_id": snapshot["snapshot_id"],
        "binding_kind": "CANONICAL_RECORD",
        "sha256": translation_record_digest(snapshot).removeprefix("sha256:"),
    }
    items: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for path in plan_paths:
        try:
            plan = _load_object(path, "generic inquiry plan")
            validate_generic_inquiry_plan(plan)
            component_bindings = plan["case_binding"]["component_bindings"]
            binding_keys = [
                (item["role"], item["subject_id"]) for item in component_bindings
            ]
            if len(binding_keys) != len(set(binding_keys)):
                raise PolicyViolation(
                    "inquiry plan repeats a semantic component-binding key"
                )
            if expected_snapshot_binding not in component_bindings:
                raise PolicyViolation(
                    "inquiry plan is not exactly bound to the current translation snapshot"
                )
            next_action = plan["next_action"]
            selected_assessment_ids = set(
                ()
                if next_action is None
                else next_action["selected_assessment_ids"]
            )
            assessments_by_id = {
                str(assessment["assessment_id"]): assessment
                for assessment in plan["locus_assessments"]
            }
            applicable_routes: list[dict[str, Any]] = []
            for assessment_id in plan["live_locus_assessment_ids"]:
                assessment = assessments_by_id[str(assessment_id)]
                route = _ASSESSMENT_ROUTES.get(
                    str(assessment["uncertainty_location"])
                )
                selected = str(assessment_id) in selected_assessment_ids
                if selected:
                    readiness = "SELECTED_FOR_ACTION"
                elif assessment["depends_on_assessment_ids"]:
                    readiness = "DEPENDENCY_BLOCKED"
                elif route is None:
                    readiness = "LOCATION_UNRESOLVED"
                else:
                    readiness = "FRONTIER_UNSELECTED"
                applicable_routes.append(
                    {
                        "assessment_id": str(assessment_id),
                        "route": route,
                        "readiness": readiness,
                        "selected": selected,
                    }
                )
            items.append(
                {
                    "path": str(path),
                    "plan_id": plan["plan_id"],
                    "selected_action_route": plan["route"],
                    "live_locus_assessment_ids": plan[
                        "live_locus_assessment_ids"
                    ],
                    "selected_action_id": plan["selected_action_id"],
                    "applicable_routes": applicable_routes,
                    "research_target": (
                        None
                        if next_action is None
                        else next_action["research_target"]
                    ),
                }
            )
        except Exception as exc:
            errors.append({"path": str(path), **_error(exc)})
    if errors:
        return _stage(
            INVALID,
            "At least one supplied inquiry plan failed exact deterministic validation.",
            details={"valid_plans": items, "invalid_plans": errors},
            next_actions=tuple(
                f"Repair or supersede the invalid inquiry plan at {item['path']}."
                for item in errors
            ),
        )

    waiting = [
        item
        for item in items
        if item["selected_action_route"] not in _ACTIONABLE_ROUTES
    ]
    if waiting:
        actions: list[str] = []
        for item in waiting:
            if item["selected_action_route"] == "AWAITING_HUMAN_TRIAGE":
                actions.append(
                    f"Add human locus assessments to plan {item['plan_id']}; origin cannot select the locus."
                )
            else:
                actions.append(
                    f"Select explicit work actions for plan {item['plan_id']}; keep incompatible routes separate."
                )
        status = UNRESOLVED
    else:
        status = UNRESOLVED
        actions = [
            "Publish a separately authorized action for every selected route before execution; do not rank or collapse applicable routes."
        ]
    return _stage(
        status,
        "Each valid plan is a non-publishing route preview bound to this snapshot; no score or input order selects among routes.",
        details={
            "plans": items,
            "applicable_routes": [
                {"plan_id": item["plan_id"], **route}
                for item in items
                for route in item["applicable_routes"]
            ],
            "selected_route": None,
            "selection_policy": "HUMAN_BOUND_ACTIONS_NO_AUTOMATIC_RANKING",
            "publication_authority": False,
            "preview_only": True,
        },
        next_actions=actions,
    )


def _iteration_lineage_stage() -> dict[str, Any]:
    """Expose the still-open closed-loop lineage as a first-class gate."""

    return _stage(
        UNRESOLVED,
        "The harness does not yet bind one observed test failure through inquiry, research disposition, revision, delta replay, and hardening as a single append-only lineage.",
        details={
            "closure_status": "NOT_IMPLEMENTED_V1",
            "required_edges": [
                "TEST_EXECUTION_TO_OBSERVATION",
                "OBSERVATION_TO_INQUIRY",
                "INQUIRY_TO_RESEARCH_DISPOSITION",
                "RESEARCH_DISPOSITION_TO_SUCCESSOR_SNAPSHOT",
                "SUCCESSOR_TO_DERIVED_DELTA_REPLAY",
                "DELTA_REPLAY_TO_HARDENING_COMPARISON",
            ],
            "publication_authority": False,
        },
        next_actions=(
            "Implement content-addressed, append-only records for every required edge before treating the controller as a closed iterative repair loop.",
        ),
    )


def _hardening_stage(
    *,
    comparison_path: Path | None,
    evidence_paths: Sequence[Path],
    decision_paths: Sequence[Path],
    resolution_path: Path | None,
    snapshot: Mapping[str, Any] | None,
    records: Mapping[str, Mapping[str, Any]] | None,
    review_head_id: str | None,
    review_stage_status: str,
    review_head_sha256: str | None,
) -> dict[str, Any]:
    extras_present = bool(evidence_paths or decision_paths or resolution_path is not None)
    if comparison_path is None and not extras_present:
        return _stage(
            NOT_SUPPLIED,
            "No bounded hardening comparison was supplied.",
            next_actions=(
                "Define an exact candidate/baseline comparison, protected features, gains, imports, and live criticisms.",
            ),
        )
    if comparison_path is None:
        return _stage(
            BLOCKED,
            "Hardening evidence, decisions, or a resolution were supplied without their comparison.",
            next_actions=("Supply the exact hardening comparison record.",),
        )
    if snapshot is None or records is None:
        return _blocked_stage("translation_integrity")
    if review_head_id is None or review_stage_status != READY:
        return _blocked_stage("interpretation_review")
    try:
        comparison = validate_hardening_comparison(
            _load_object(comparison_path, "hardening comparison")
        )
        successor = comparison["successor"]
        model = records[str(snapshot["model_id"])]
        signature = records[str(snapshot["signature_id"])]
        exact_refs = (
            (
                successor["snapshot_ref"],
                snapshot["snapshot_id"],
                "creib.semantic-forge.translation-snapshot.v1",
                translation_record_digest(snapshot),
            ),
            (
                successor["model_ref"],
                snapshot["model_id"],
                "creib.semantic-forge.translation-neutral-model.v1",
                translation_record_digest(model),
            ),
            (
                successor["signature_ref"],
                snapshot["signature_id"],
                "creib.semantic-forge.translation-neutral-signature.v1",
                translation_record_digest(signature),
            ),
        )
        for ref, record_id, schema_version, digest in exact_refs:
            if ref != {
                "record_id": record_id,
                "schema_version": schema_version,
                "record_sha256": digest,
            }:
                raise PolicyViolation(
                    "hardening successor is not exactly bound to the current translation snapshot"
                )
        if successor["review_head_ref"] != {
            "record_id": review_head_id,
            "schema_version": REVIEW_SCHEMA,
            "record_sha256": review_head_sha256,
        }:
            raise PolicyViolation(
                "hardening successor is not bound to the current interpretation-review head"
            )
        projection = model["theory_projection"]
        closure = model["semantic_dependency_closure"]
        if (
            successor["theory_record_sha256"] != projection["theory_record_sha256"]
            or successor["dependency_closure_sha256"] != closure["closure_sha256"]
            or comparison["execution_semantics"] != projection["execution_semantics"]
        ):
            raise PolicyViolation(
                "hardening execution or theory binding differs from the current neutral model"
            )
        evidence = [
            _load_object(path, "hardening evidence") for path in evidence_paths
        ]
        decisions = [
            _load_object(path, "hardening decision") for path in decision_paths
        ]
        derived = resolve_hardening_comparison(comparison, evidence, decisions)
        if resolution_path is not None:
            supplied = validate_hardening_resolution(
                _load_object(resolution_path, "hardening resolution"),
                comparison,
                evidence,
                decisions,
            )
            if supplied != derived:
                raise RecordError(
                    "supplied hardening resolution differs from deterministic replay"
                )
    except Exception as exc:
        return _stage(
            INVALID,
            "The hardening comparison or its evidence/decision closure failed deterministic validation.",
            next_actions=("Repair the exact hardening records and replay the non-scalar conjunction.",),
            error=exc,
        )

    outcome = str(derived["status"])
    if outcome == "HARDENING_UNREFUTED":
        status = READY
        actions = (
            "Treat hardening as scoped and presently unrefuted only; keep the criticism register open.",
        )
    elif outcome == "NO_HARDENING":
        status = BLOCKED
        actions = (
            "Address the recorded counterwitness or defeating human decision before making a hardening claim.",
        )
    else:
        status = UNRESOLVED
        actions = (
            "Supply missing evidence and human decisions without collapsing the obligations into a score.",
        )
    return _stage(
        status,
        "The hardening outcome is limited to the exact declared comparison and remains non-final.",
        details={
            "comparison_id": comparison["comparison_id"],
            "resolution_id": derived["resolution_id"],
            "hardening_status": outcome,
            "reason_codes": derived["reason_codes"],
            "effective_live_criticism_ids": derived[
                "effective_live_criticism_ids"
            ],
            "obligations": derived["obligations"],
            "human_requirements": derived["human_requirements"],
            "supplied_resolution_verified": resolution_path is not None,
        },
        next_actions=actions,
    )


def _qualification_stage(
    *,
    report_path: Path | None,
    report_freeze_path: Path | None,
    candidate_freeze_path: Path | None,
    repository_root: Path,
    snapshot: Mapping[str, Any] | None,
    snapshot_path: Path,
    records_dir: Path,
) -> dict[str, Any]:
    if (
        report_path is None
        and report_freeze_path is None
        and candidate_freeze_path is None
    ):
        return _stage(
            NOT_SUPPLIED,
            "No frozen HRC-1 declared-exposure report was supplied for qualification replay.",
            next_actions=(
                "Freeze a blind candidate report before controller disclosure, then supply the report and freeze.",
            ),
        )
    missing = [
        name
        for name, value in (
            ("qualification_report", report_path),
            ("qualification_report_freeze", report_freeze_path),
            ("qualification_candidate_freeze", candidate_freeze_path),
        )
        if value is None
    ]
    if missing:
        return _stage(
            BLOCKED,
            "Qualification replay requires a report and its pre-controller freeze.",
            details={"missing_inputs": missing},
            next_actions=(f"Supply the missing inputs: {', '.join(missing)}.",),
        )
    if snapshot is None:
        return _blocked_stage("translation_integrity")
    try:
        report_freeze = validate_freeze_record(
            _load_object(report_freeze_path, "qualification report freeze")  # type: ignore[arg-type]
        )
        candidate_freeze = validate_freeze_record(
            _load_object(candidate_freeze_path, "candidate snapshot freeze")  # type: ignore[arg-type]
        )
        if candidate_freeze["content_id"] != snapshot.get("snapshot_id"):
            raise PolicyViolation(
                "qualification candidate freeze is not bound to the initially "
                "validated translation snapshot"
            )
        if candidate_freeze["record_closure_sha256"] != snapshot.get(
            "record_closure_sha256"
        ):
            raise PolicyViolation(
                "qualification candidate freeze is not bound to the initially "
                "validated translation record closure"
            )
        _current_snapshot, expected_candidate_freeze = freeze_translation_snapshot(
            snapshot_path, records_dir
        )
        if candidate_freeze != expected_candidate_freeze:
            raise PolicyViolation(
                "qualification candidate freeze is not the current translation snapshot"
            )
        result = qualify_exposure_report(
            report_path=report_path,  # type: ignore[arg-type]
            report_freeze=report_freeze,
            repository_root=repository_root,
            candidate_snapshot_freeze=candidate_freeze,
            candidate_snapshot_path=snapshot_path,
            candidate_records_dir=records_dir,
        )
    except Exception as exc:
        return _stage(
            INVALID,
            "The qualification inputs or HRC-1 controller bindings failed validation.",
            next_actions=("Repair the frozen report bindings and rerun the controller replay.",),
            error=exc,
        )

    declarations_match = result["qualification_status"] == ALL_REPRODUCED
    return _stage(
        UNRESOLVED,
        "The result compares declared exposure tokens with HRC-1; no mutation execution or detection evidence was verified.",
        details={
            "qualification_id": result["qualification_id"],
            "qualification_status": result["qualification_status"],
            "case_counts": result["case_counts"],
            "missed_case_ids": result["missed_case_ids"],
            "false_positive_case_ids": result["false_positive_case_ids"],
            "blindness_verdict": result["blindness_verdict"],
            "controller_declaration_match": declarations_match,
            "mutation_execution_verified": result["mutation_execution_verified"],
            "execution_evidence_verified": result["execution_evidence_verified"],
        },
        next_actions=(
            "Preserve the scoped result and seek new counterexamples; do not promote it to translation fidelity.",
        )
        if declarations_match
        else (
            "Treat every missed or false-positive exposure as a live harness criticism and route it separately.",
        ),
    )


def _overall_status(stages: Mapping[str, Mapping[str, Any]]) -> str:
    statuses = {str(stage["status"]) for stage in stages.values()}
    if INVALID in statuses:
        return INVALID
    if BLOCKED in statuses:
        return BLOCKED
    if UNRESOLVED in statuses or NOT_SUPPLIED in statuses:
        return UNRESOLVED
    return READY


def run_translation_pipeline(
    *,
    records_dir: Path,
    snapshot_path: Path,
    source_documents: Mapping[str, Path] | None = None,
    review_dir: Path | None = None,
    review_head_id: str | None = None,
    old_snapshot_path: Path | None = None,
    delta_path: Path | None = None,
    inquiry_plan_paths: Sequence[Path] | None = None,
    hardening_comparison_path: Path | None = None,
    hardening_evidence_paths: Sequence[Path] | None = None,
    hardening_decision_paths: Sequence[Path] | None = None,
    hardening_resolution_path: Path | None = None,
    qualification_report_path: Path | None = None,
    qualification_report_freeze_path: Path | None = None,
    qualification_candidate_freeze_path: Path | None = None,
    qualification_repository_root: Path | None = None,
) -> dict[str, Any]:
    """Validate every supplied stage and expose all remaining work.

    Optional inputs are nullable so a partial run is still useful.  A partial
    run cannot become ``READY``: omitted stages stay visible as
    ``NOT_SUPPLIED`` and make the conjunctive pipeline ``UNRESOLVED``.
    """

    plans = tuple(inquiry_plan_paths or ())
    evidence_paths = tuple(hardening_evidence_paths or ())
    decision_paths = tuple(hardening_decision_paths or ())
    sources = dict(source_documents or {})
    qualification_root = qualification_repository_root or Path.cwd()

    snapshot: dict[str, Any] | None = None
    records: Mapping[str, Mapping[str, Any]] | None = None
    stages: dict[str, dict[str, Any]] = {}
    try:
        records = load_translation_inventory(records_dir)
        snapshot = _load_object(snapshot_path, "translation snapshot")
        validation = validate_translation_snapshot(snapshot, records)
        stages.update(
            _translation_stages(
                snapshot,
                records,
                validation,
                sources,
                records_dir,
            )
        )
    except Exception as exc:
        stages["translation_integrity"] = _stage(
            INVALID,
            "The selected translation inventory or snapshot failed structural validation.",
            next_actions=("Repair or supersede the invalid translation records, then rerun the snapshot validator.",),
            error=exc,
        )
        for name in (
            "source_identity",
            "charter",
            "obligation_graph",
            "interpretation_rivals",
            "neutral_model",
            "two_way_bridge",
        ):
            stages[name] = _blocked_stage("translation_integrity")
        snapshot = None
        records = None

    stages["interpretation_review"] = _review_stage(
        review_dir=review_dir,
        review_head_id=review_head_id,
        snapshot=snapshot,
        records=records,
    )
    stages["dynamic_test_synthesis"] = _dynamic_test_stage(
        old_snapshot_path=old_snapshot_path,
        delta_path=delta_path,
        snapshot=snapshot,
    )
    stages["research_routing_readiness"] = _research_stage(plans, snapshot)
    stages["iteration_lineage"] = _iteration_lineage_stage()
    stages["hardening"] = _hardening_stage(
        comparison_path=hardening_comparison_path,
        evidence_paths=evidence_paths,
        decision_paths=decision_paths,
        resolution_path=hardening_resolution_path,
        snapshot=snapshot,
        records=records,
        review_head_id=review_head_id,
        review_stage_status=stages["interpretation_review"]["status"],
        review_head_sha256=stages["interpretation_review"]["details"].get(
            "head_review_sha256"
        ),
    )
    stages["qualification"] = _qualification_stage(
        report_path=qualification_report_path,
        report_freeze_path=qualification_report_freeze_path,
        candidate_freeze_path=qualification_candidate_freeze_path,
        repository_root=qualification_root,
        snapshot=snapshot,
        snapshot_path=snapshot_path,
        records_dir=records_dir,
    )

    # Keep presentation deterministic, but explicitly deny priority meaning.
    stages = {name: stages[name] for name in STAGE_ORDER}
    next_actions = [
        {"stage": name, "action": action}
        for name, stage in stages.items()
        for action in stage["next_actions"]
    ]
    if not next_actions:
        next_actions = [
            {
                "stage": "human_semantic_review",
                "action": (
                    "Decide whether any scoped downstream use is warranted; "
                    "do not convert operational readiness into semantic confirmation."
                ),
            }
        ]
    route_details = stages["research_routing_readiness"]["details"]
    applicable_routes = route_details.get("applicable_routes", [])
    return {
        "report_type": "translation_harness_runtime_report",
        "overall_status": _overall_status(stages),
        "snapshot_id": None if snapshot is None else snapshot.get("snapshot_id"),
        "stages": stages,
        "applicable_routes": applicable_routes,
        "selected_route": None,
        "route_selection_policy": "NO_AUTOMATIC_RANKING_OR_EXCLUSIVE_SELECTION",
        "stage_aggregation_policy": "CONJUNCTIVE_FAIL_CLOSED_NO_SCORING",
        "next_actions": next_actions,
        "next_action_ordering": "STAGE_PRESENTATION_ONLY_NOT_PRIORITY",
        "automatic_semantic_effect": "NONE",
        "semantic_verdict": None,
        "mapping_fidelity": "UNREVIEWED",
        "epistemic_limit": REPORT_LIMIT,
    }


__all__ = [
    "BLOCKED",
    "INVALID",
    "NOT_SUPPLIED",
    "READY",
    "STAGE_ORDER",
    "STAGE_STATUSES",
    "STRUCTURALLY_VALID",
    "UNRESOLVED",
    "run_translation_pipeline",
]
