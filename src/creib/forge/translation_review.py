"""Append-only human review for generic source-to-model translations.

The immutable translation snapshot is the object presented for review.  Review
records can authorize bounded downstream use, but they cannot turn an
interpretation into source text, accept project imports, or confirm a model.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import errno
import os
from pathlib import Path
import tempfile
import unicodedata
from typing import Any, Iterable

from creib.canonical import canonical_bytes, domain_digest
from creib.errors import PolicyViolation, RecordError
from creib.strict_json import load_strict, loads_strict

from .schema_catalog_cache import cached_local_schema_catalog
from .translation import (
    compute_translation_component_id,
    compute_translation_record_id,
    validate_translation_record,
)


REVIEW_SCHEMA = "creib.semantic-forge.translation-review.v1"
BRANCH_DISPOSITION_SCHEMA = (
    "creib.semantic-forge.translation-branch-disposition.v1"
)
TRANSLATION_DECISION_SCHEMA = "creib.semantic-forge.translation-decision.v1"
TRANSLATION_VARIANT_DOMAIN = "creib.semantic-forge.translation-variant.v1"
TRANSLATION_SCOPE_DOMAIN = "creib.semantic-forge.translation-review-scope.v1"
INTERPRETATION_DOMAIN = "creib.semantic-forge.translation-interpretation.v1"
MODEL_EFFECT_DOMAIN = "creib.semantic-forge.translation-model-effect.v1"
SNAPSHOT_BINDING_DOMAIN = "creib.semantic-forge.translation-snapshot-binding.v1"

REVIEW_SCHEMA_REF = "../../schema/translation-review-v1.schema.json"
SNAPSHOT_SCHEMA = "creib.semantic-forge.translation-snapshot.v1"
INTERPRETATION_SET_SCHEMA = (
    "creib.semantic-forge.translation-interpretation-set.v1"
)


class TranslationReviewError(RecordError):
    """Stable machine-classifiable translation-review failure."""

    def __init__(self, error_code: str, message: str) -> None:
        super().__init__(message)
        self.error_code = error_code


@dataclass(frozen=True)
class TranslationReviewState:
    """Verified state derived from one explicitly selected review head."""

    head_review_id: str | None
    reviews: tuple[dict[str, object], ...]
    workflow_status: str
    current_decision_id: str | None
    effective_branch_states: dict[str, str]
    reviewer_authentication: str | None
    current_scope_binding: dict[str, object] | None
    authorized_variants: tuple[dict[str, object], ...]


def _object(value: Any, where: str) -> dict[str, object]:
    if type(value) is not dict:
        raise RecordError(f"{where} must be an object")
    return value


def _string(value: Any, where: str) -> str:
    if type(value) is not str or not value:
        raise RecordError(f"{where} must be a non-empty string")
    return value


def _without(record: dict[str, Any], key: str) -> dict[str, object]:
    return {name: value for name, value in record.items() if name != key}


def _hex_digest(domain: str, value: object) -> str:
    return domain_digest(domain, value).removeprefix("sha256:")


def _record_id(prefix: str, domain: str, record: dict[str, object], key: str) -> str:
    return f"{prefix}:{_hex_digest(domain, _without(record, key))}"


def compute_translation_snapshot_id(record: dict[str, object]) -> str:
    return compute_translation_record_id(record)


def compute_interpretation_set_id(record: dict[str, object]) -> str:
    return compute_translation_record_id(record)


def compute_interpretation_id(record: dict[str, object]) -> str:
    return compute_translation_component_id(
        "TI", INTERPRETATION_DOMAIN, record, id_field="interpretation_id"
    )


def compute_branch_disposition_id(record: dict[str, object]) -> str:
    return _record_id(
        "BD", BRANCH_DISPOSITION_SCHEMA, record, "disposition_id"
    )


def compute_translation_variant_id(record: dict[str, object]) -> str:
    return _record_id("TV", TRANSLATION_VARIANT_DOMAIN, record, "variant_id")


def compute_translation_scope_id(record: dict[str, object]) -> str:
    return _record_id("TRS", TRANSLATION_SCOPE_DOMAIN, record, "scope_id")


def compute_translation_decision_id(record: dict[str, object]) -> str:
    return _record_id("TD", TRANSLATION_DECISION_SCHEMA, record, "decision_id")


def compute_translation_review_id(record: dict[str, object]) -> str:
    # Match the top-level translation-record convention without registering
    # the review layer as one of the pre-review translation inputs.
    return _record_id("TR", f"{REVIEW_SCHEMA}.record-id", record, "review_id")


def _content_id(value: Any, prefix: str, where: str) -> str:
    text = _string(value, where)
    if len(text) != len(prefix) + 65 or not text.startswith(prefix + ":"):
        raise RecordError(f"{where} has an invalid {prefix} content-ID shape")
    suffix = text.removeprefix(prefix + ":")
    if any(character not in "0123456789abcdef" for character in suffix):
        raise RecordError(f"{where} has a non-hexadecimal content ID")
    return text


def _iso_date(value: Any, where: str) -> str:
    text = _string(value, where)
    try:
        parsed = date.fromisoformat(text)
    except ValueError as exc:
        raise RecordError(f"{where} must be a valid ISO date") from exc
    if parsed.isoformat() != text:
        raise RecordError(f"{where} must use canonical YYYY-MM-DD form")
    return text


def _canonical_strings(
    value: Any, where: str, *, nonempty: bool = False
) -> tuple[str, ...]:
    if type(value) is not list or (nonempty and not value):
        suffix = " non-empty" if nonempty else ""
        raise RecordError(f"{where} must be a{suffix} array")
    result = tuple(_string(item, f"{where}[{index}]") for index, item in enumerate(value))
    if len(result) != len(set(result)):
        raise RecordError(f"{where} must contain unique values")
    if result != tuple(sorted(result)):
        raise RecordError(f"{where} must use canonical lexical order")
    return result


def _canonical_branch_sets(value: Any, where: str) -> tuple[tuple[str, ...], ...]:
    if type(value) is not list:
        raise RecordError(f"{where} must be an array")
    combinations = tuple(
        _canonical_strings(item, f"{where}[{index}]", nonempty=True)
        for index, item in enumerate(value)
    )
    encoded = tuple(canonical_bytes(list(item)) for item in combinations)
    if len(encoded) != len(set(encoded)):
        raise RecordError(f"{where} must contain unique branch sets")
    if encoded != tuple(sorted(encoded)):
        raise RecordError(f"{where} must use canonical branch-set order")
    return combinations


def _nfc_prose(value: Any, where: str) -> None:
    prose = _object(value, where)
    for key in (
        "plain_language_reading",
        "reason",
        "model_effect_assessment",
        "remaining_uncertainty",
    ):
        text = _string(prose.get(key), f"{where}.{key}")
        if unicodedata.normalize("NFC", text) != text:
            raise RecordError(f"{where}.{key} must already be Unicode NFC")


def _changed_pointers(previous: Any, current: Any, pointer: str = "") -> tuple[str, ...]:
    if previous == current:
        return ()
    if type(previous) is dict and type(current) is dict:
        changed: list[str] = []
        for key in sorted(set(previous).union(current)):
            token = str(key).replace("~", "~0").replace("/", "~1")
            child = f"{pointer}/{token}"
            if key not in previous or key not in current:
                changed.append(child)
            else:
                changed.extend(_changed_pointers(previous[key], current[key], child))
        return tuple(changed)
    return (pointer,)


def _validate_translation_inputs(
    snapshot: dict[str, object],
    interpretation_sets: Iterable[dict[str, object]],
) -> tuple[dict[str, object], tuple[dict[str, object], ...]]:
    catalog = cached_local_schema_catalog()
    catalog.validate(snapshot, "translation-snapshot.schema.json")
    if snapshot.get("schema_version") != SNAPSHOT_SCHEMA:
        raise RecordError("translation snapshot has an unsupported schema version")
    validate_translation_record(snapshot)

    for field in (
        "document_ids",
        "span_ids",
        "interpretation_set_ids",
        "import_ids",
        "unresolved_record_ids",
    ):
        _canonical_strings(
            snapshot.get(field),
            f"translation snapshot.{field}",
            nonempty=field in {"document_ids", "span_ids", "interpretation_set_ids"},
        )

    checked: list[dict[str, object]] = []
    all_interpretation_ids: set[str] = set()
    for index, item in enumerate(interpretation_sets):
        record = _object(item, f"interpretation_sets[{index}]")
        catalog.validate(record, "translation-interpretation-set.schema.json")
        if record.get("schema_version") != INTERPRETATION_SET_SCHEMA:
            raise RecordError("interpretation set has an unsupported schema version")
        validate_translation_record(record)
        if record.get("charter_id") != snapshot.get("charter_id"):
            raise PolicyViolation("interpretation set changed the snapshot charter")
        if record.get("graph_id") != snapshot.get("graph_id"):
            raise PolicyViolation("interpretation set changed the snapshot obligation graph")
        source_ids = _canonical_strings(
            record.get("source_span_ids"),
            "interpretation set.source_span_ids",
            nonempty=True,
        )
        if not set(source_ids).issubset(set(snapshot["span_ids"])):  # type: ignore[arg-type]
            raise PolicyViolation("interpretation set cites a span outside the snapshot")
        _canonical_strings(
            record.get("obligation_ids"),
            "interpretation set.obligation_ids",
            nonempty=True,
        )
        branches = record.get("branches")
        if type(branches) is not list or len(branches) < 2:
            raise RecordError("interpretation set requires at least two rival branches")
        branch_ids: list[str] = []
        for branch_index, raw_branch in enumerate(branches):
            branch = _object(raw_branch, f"interpretation set.branches[{branch_index}]")
            if branch.get("interpretation_id") != compute_interpretation_id(branch):
                raise RecordError("interpretation branch content-addressed ID mismatch")
            branch_id = _content_id(
                branch.get("interpretation_id"), "TI", "interpretation_id"
            )
            if branch_id in all_interpretation_ids:
                raise RecordError("interpretation IDs must be globally unique in a snapshot")
            all_interpretation_ids.add(branch_id)
            branch_ids.append(branch_id)
            branch_spans = _canonical_strings(
                branch.get("source_span_ids"),
                f"interpretation branch {branch_id}.source_span_ids",
                nonempty=True,
            )
            if not set(branch_spans).issubset(set(source_ids)):
                raise PolicyViolation("interpretation branch cites a span outside its set")
            branch_obligations = _canonical_strings(
                branch.get("interpreted_obligation_ids"),
                f"interpretation branch {branch_id}.interpreted_obligation_ids",
                nonempty=True,
            )
            if not set(branch_obligations).issubset(set(record["obligation_ids"])):  # type: ignore[arg-type]
                raise PolicyViolation("interpretation branch cites an obligation outside its set")
            effect = _object(branch.get("model_effect"), "interpretation branch.model_effect")
            _canonical_strings(
                effect.get("affected_element_keys"),
                "interpretation branch.model_effect.affected_element_keys",
            )
        if tuple(branch_ids) != tuple(sorted(branch_ids)):
            raise RecordError("interpretation branches must use canonical ID order")
        checked.append(record)

    set_ids = tuple(str(item["interpretation_set_id"]) for item in checked)
    if len(set_ids) != len(set(set_ids)) or set_ids != tuple(sorted(set_ids)):
        raise RecordError("interpretation sets must be unique and canonically ordered")
    if set_ids != tuple(snapshot["interpretation_set_ids"]):  # type: ignore[arg-type]
        raise PolicyViolation(
            "supplied interpretation-set inventory differs from the snapshot"
        )
    return snapshot, tuple(checked)


def translation_review_bindings(snapshot: dict[str, object]) -> dict[str, object]:
    """Return the exact immutable snapshot binding used by review records."""

    return {
        "snapshot_id": snapshot["snapshot_id"],
        "predecessor_snapshot_id": snapshot["predecessor_snapshot_id"],
        "snapshot_sha256": domain_digest(SNAPSHOT_BINDING_DOMAIN, snapshot),
        "record_closure_sha256": snapshot["record_closure_sha256"],
    }


def translation_review_surface(
    snapshot: dict[str, object],
    interpretation_sets: Iterable[dict[str, object]],
) -> dict[str, object]:
    """Derive the complete span, rival, and model-effect surface shown to a reviewer."""

    snapshot, sets = _validate_translation_inputs(snapshot, interpretation_sets)
    set_surfaces: list[dict[str, object]] = []
    for interpretation_set in sets:
        interpretations: list[dict[str, object]] = []
        for branch in interpretation_set["branches"]:  # type: ignore[index]
            effect = _object(branch["model_effect"], "interpretation model effect")
            interpretations.append(
                {
                    "interpretation_id": branch["interpretation_id"],
                    "claim_kind": branch["claim_kind"],
                    "statement": branch["statement"],
                    "source_span_ids": list(branch["source_span_ids"]),
                    "interpreted_obligation_ids": list(
                        branch["interpreted_obligation_ids"]
                    ),
                    "preserved_feature_ids": list(branch["preserved_feature_ids"]),
                    "model_effect": {
                        "status": effect["status"],
                        "effect_statement": effect["effect_statement"],
                        "affected_element_keys": list(effect["affected_element_keys"]),
                    },
                    "model_effect_sha256": domain_digest(MODEL_EFFECT_DOMAIN, effect),
                    "discriminating_consequences": list(
                        branch["discriminating_consequences"]
                    ),
                    "falsifier_conditions": list(branch["falsifier_conditions"]),
                    "known_loss_risks": list(branch["known_loss_risks"]),
                    "proposal_status": branch["proposal_status"],
                }
            )
        set_surfaces.append(
            {
                "interpretation_set_id": interpretation_set["interpretation_set_id"],
                "supersedes_interpretation_set_id": interpretation_set[
                    "supersedes_interpretation_set_id"
                ],
                "question": interpretation_set["question"],
                "source_span_ids": list(interpretation_set["source_span_ids"]),
                "obligation_ids": list(interpretation_set["obligation_ids"]),
                "rival_relation": interpretation_set["rival_relation"],
                "admissible_branch_sets": [
                    list(combination)
                    for combination in interpretation_set[
                        "admissible_branch_sets"
                    ]
                ],
                "interpretations": interpretations,
            }
        )
    return {
        "document_ids": list(snapshot["document_ids"]),
        "source_span_ids": list(snapshot["span_ids"]),
        "charter_id": snapshot["charter_id"],
        "graph_id": snapshot["graph_id"],
        "interpretation_sets": set_surfaces,
        "signature_id": snapshot["signature_id"],
        "model_id": snapshot["model_id"],
        "import_ids": list(snapshot["import_ids"]),
        "bridge_id": snapshot["bridge_id"],
        "unresolved_record_ids": list(snapshot["unresolved_record_ids"]),
    }


def _surface_index(
    surface: dict[str, object],
) -> tuple[
    dict[str, dict[str, object]],
    dict[str, tuple[str, dict[str, object]]],
]:
    sets: dict[str, dict[str, object]] = {}
    interpretations: dict[str, tuple[str, dict[str, object]]] = {}
    ordered_set_ids: list[str] = []
    for raw_set in surface["interpretation_sets"]:  # type: ignore[index]
        item = _object(raw_set, "review_surface.interpretation_sets[]")
        set_id = _content_id(
            item.get("interpretation_set_id"), "TIS", "interpretation_set_id"
        )
        if set_id in sets:
            raise RecordError("review surface repeats an interpretation set")
        ordered_set_ids.append(set_id)
        sets[set_id] = item
        ordered_branch_ids: list[str] = []
        for raw_interpretation in item["interpretations"]:  # type: ignore[index]
            branch = _object(raw_interpretation, "review surface interpretation")
            branch_id = _content_id(
                branch.get("interpretation_id"), "TI", "interpretation_id"
            )
            if branch_id in interpretations:
                raise RecordError("review surface repeats an interpretation")
            ordered_branch_ids.append(branch_id)
            branch_material = {
                key: value
                for key, value in branch.items()
                if key != "model_effect_sha256"
            }
            if compute_interpretation_id(branch_material) != branch_id:
                raise RecordError(
                    "review surface branch material does not match its interpretation ID"
                )
            effect = _object(branch.get("model_effect"), "review surface model effect")
            if branch.get("model_effect_sha256") != domain_digest(
                MODEL_EFFECT_DOMAIN, effect
            ):
                raise RecordError(
                    "review surface model effect does not match its exact digest"
                )
            interpretations[branch_id] = (set_id, branch)
        if ordered_branch_ids != sorted(ordered_branch_ids):
            raise RecordError(
                "review surface interpretations must use canonical branch order"
            )
        admissible = _canonical_branch_sets(
            item.get("admissible_branch_sets"),
            "review surface admissible_branch_sets",
        )
        if any(
            not set(combination).issubset(set(ordered_branch_ids))
            for combination in admissible
        ):
            raise PolicyViolation(
                "review surface admissible branch set cites an absent interpretation"
            )
    if ordered_set_ids != sorted(ordered_set_ids):
        raise RecordError("review surface sets must use canonical interpretation-set order")
    return sets, interpretations


def _validate_branch_disposition(
    value: Any,
    *,
    surface: dict[str, object] | None,
) -> dict[str, object]:
    record = _object(value, "translation branch disposition")
    if record.get("disposition_id") != compute_branch_disposition_id(record):
        raise RecordError("branch disposition content-addressed ID mismatch")
    _iso_date(record.get("created_on"), "branch disposition.created_on")
    _nfc_prose(record.get("reviewer_prose"), "branch disposition.reviewer_prose")
    _canonical_strings(
        record.get("reviewed_source_span_ids"),
        "branch disposition.reviewed_source_span_ids",
        nonempty=True,
    )
    _canonical_strings(
        record.get("considered_interpretation_ids"),
        "branch disposition.considered_interpretation_ids",
        nonempty=True,
    )
    _canonical_strings(
        record.get("changed_binding_pointers"),
        "branch disposition.changed_binding_pointers",
    )
    if surface is not None:
        sets, interpretations = _surface_index(surface)
        set_id = _content_id(
            record.get("interpretation_set_id"), "TIS", "interpretation_set_id"
        )
        branch_id = _content_id(
            record.get("interpretation_id"), "TI", "interpretation_id"
        )
        if set_id not in sets or branch_id not in interpretations:
            raise PolicyViolation("branch disposition targets an absent interpretation")
        actual_set_id, branch = interpretations[branch_id]
        if actual_set_id != set_id:
            raise PolicyViolation("branch disposition changed interpretation-set membership")
        expected_considered = [
            item["interpretation_id"]
            for item in sets[set_id]["interpretations"]  # type: ignore[index]
        ]
        if record.get("considered_interpretation_ids") != expected_considered:
            raise PolicyViolation("branch disposition omitted or changed a rival interpretation")
        if record.get("reviewed_source_span_ids") != sets[set_id]["source_span_ids"]:
            raise PolicyViolation("branch disposition omitted or changed a required source span")
        if record.get("reviewed_model_effect_sha256") != branch["model_effect_sha256"]:
            raise PolicyViolation("branch disposition changed the reviewed model effect")
    return record


def _expected_reviewed_model_effects(
    surface: dict[str, object],
) -> list[dict[str, object]]:
    _sets, interpretations = _surface_index(surface)
    return [
        {
            "interpretation_id": branch_id,
            "model_effect_sha256": interpretations[branch_id][1][
                "model_effect_sha256"
            ],
        }
        for branch_id in sorted(interpretations)
    ]


def _validate_scope_binding(
    value: Any,
    *,
    surface: dict[str, object] | None,
) -> dict[str, object]:
    scope = _object(value, "translation decision.scope_binding")
    if scope.get("scope_id") != compute_translation_scope_id(scope):
        raise RecordError("translation review scope content-addressed ID mismatch")
    _content_id(scope.get("charter_id"), "TCHAR", "scope_binding.charter_id")
    for field in ("purpose", "system_boundary"):
        text = _string(scope.get(field), f"scope_binding.{field}")
        if unicodedata.normalize("NFC", text) != text:
            raise RecordError(f"scope_binding.{field} must already be Unicode NFC")
    _canonical_strings(
        scope.get("in_scope"),
        "scope_binding.in_scope",
        nonempty=True,
    )
    if surface is not None and scope.get("charter_id") != surface.get("charter_id"):
        raise PolicyViolation(
            "translation review scope is not bound to the current charter"
        )
    return scope


def _validate_translation_decision(
    value: Any,
    *,
    surface: dict[str, object] | None,
) -> dict[str, object]:
    record = _object(value, "translation decision")
    if record.get("decision_id") != compute_translation_decision_id(record):
        raise RecordError("translation decision content-addressed ID mismatch")
    _iso_date(record.get("created_on"), "translation decision.created_on")
    _nfc_prose(record.get("reviewer_prose"), "translation decision.reviewer_prose")
    _validate_scope_binding(record.get("scope_binding"), surface=surface)
    _canonical_strings(
        record.get("reviewed_source_span_ids"),
        "translation decision.reviewed_source_span_ids",
        nonempty=True,
    )
    _canonical_strings(
        record.get("considered_interpretation_ids"),
        "translation decision.considered_interpretation_ids",
        nonempty=True,
    )
    reviewed_effects = record.get("reviewed_model_effects")
    if type(reviewed_effects) is not list:
        raise RecordError("translation decision.reviewed_model_effects must be an array")
    effect_ids = tuple(
        _content_id(
            _object(item, "reviewed model effect").get("interpretation_id"),
            "TI",
            "reviewed model effect.interpretation_id",
        )
        for item in reviewed_effects
    )
    if len(effect_ids) != len(set(effect_ids)) or effect_ids != tuple(sorted(effect_ids)):
        raise RecordError("reviewed model effects must use unique canonical interpretation order")

    variants = record.get("authorized_variants")
    if type(variants) is not list:
        raise RecordError("translation decision.authorized_variants must be an array")
    variant_ids: list[str] = []
    for raw_variant in variants:
        variant = _object(raw_variant, "authorized translation variant")
        if variant.get("variant_id") != compute_translation_variant_id(variant):
            raise RecordError("translation variant content-addressed ID mismatch")
        variant_ids.append(_content_id(variant["variant_id"], "TV", "variant_id"))
        _content_id(variant.get("model_id"), "TNM", "translation variant.model_id")
        selections = variant.get("selections")
        if type(selections) is not list:
            raise RecordError("translation variant selections must be an array")
        selection_keys: list[tuple[str, str]] = []
        for raw_selection in selections:
            selection = _object(raw_selection, "translation variant selection")
            set_id = _content_id(
                selection.get("interpretation_set_id"),
                "TIS",
                "variant selection.interpretation_set_id",
            )
            branch_id = _content_id(
                selection.get("interpretation_id"),
                "TI",
                "variant selection.interpretation_id",
            )
            selection_keys.append((set_id, branch_id))
        if len(selection_keys) != len(set(selection_keys)) or tuple(
            selection_keys
        ) != tuple(sorted(selection_keys)):
            raise RecordError(
                "variant selections must use unique canonical set-and-branch order"
            )
        _canonical_strings(
            variant.get("model_effect_sha256s"),
            "translation variant.model_effect_sha256s",
            nonempty=True,
        )
    if len(variant_ids) != len(set(variant_ids)) or tuple(variant_ids) != tuple(
        sorted(variant_ids)
    ):
        raise RecordError("authorized variants must use unique canonical variant order")

    if surface is not None:
        sets, interpretations = _surface_index(surface)
        all_branch_ids = sorted(interpretations)
        if record.get("reviewed_source_span_ids") != surface["source_span_ids"]:
            raise PolicyViolation("translation decision omitted or changed a source span")
        if record.get("considered_interpretation_ids") != all_branch_ids:
            raise PolicyViolation("translation decision omitted or changed an alternative")
        if record.get("reviewed_model_effects") != _expected_reviewed_model_effects(surface):
            raise PolicyViolation("translation decision omitted or changed a model effect")
        for variant in variants:
            if variant.get("model_id") != surface.get("model_id"):
                raise PolicyViolation(
                    "translation variant is not bound to the current neutral model"
                )
            selected_effects: set[str] = set()
            selections_by_set: dict[str, list[str]] = {}
            for raw_selection in variant["selections"]:
                selection = _object(raw_selection, "translation variant selection")
                set_id = str(selection["interpretation_set_id"])
                branch_id = str(selection["interpretation_id"])
                found = interpretations.get(branch_id)
                if found is None or found[0] != set_id:
                    raise PolicyViolation("translation variant selects an absent rival")
                branch = found[1]
                effect = _object(branch["model_effect"], "selected branch model effect")
                if effect["status"] != "DECLARED":
                    raise PolicyViolation(
                        "an unprojected model effect cannot be authorized for use"
                    )
                selections_by_set.setdefault(set_id, []).append(branch_id)
                selected_effects.add(str(branch["model_effect_sha256"]))
            if set(selections_by_set) != set(sets):
                raise PolicyViolation(
                    "each authorized variant must select a nonempty branch subset from every set"
                )
            for set_id, set_surface in sets.items():
                selected_set = tuple(sorted(selections_by_set[set_id]))
                admissible_sets = {
                    tuple(combination)
                    for combination in set_surface["admissible_branch_sets"]
                }
                if selected_set not in admissible_sets:
                    raise PolicyViolation(
                        "translation variant selects a branch set not explicitly "
                        "declared admissible"
                    )
            if variant["model_effect_sha256s"] != sorted(selected_effects):
                raise PolicyViolation(
                    "translation variant changed its exact selected model-effect closure"
                )
    return record


def _validate_subrecord_chains(
    review: dict[str, object],
    surfaces: dict[str, dict[str, object]],
) -> None:
    dispositions = review.get("branch_dispositions")
    decisions = review.get("translation_decisions")
    if type(dispositions) is not list or type(decisions) is not list:
        raise RecordError("translation review requires disposition and decision arrays")

    disposition_ids: list[str] = []
    by_branch: dict[str, list[dict[str, object]]] = {}
    for raw in dispositions:
        item = _object(raw, "translation branch disposition")
        binding = _object(item.get("bindings"), "branch disposition.bindings")
        # A staleness disposition is created under the replacement binding but
        # describes the superseded branch.  Its old-surface fidelity is checked
        # by the transition validator, not against the replacement surface.
        surface = (
            None
            if item.get("disposition") == "STALE_BY_BINDING_CHANGE"
            else surfaces.get(str(binding.get("snapshot_id")))
        )
        checked = _validate_branch_disposition(item, surface=surface)
        disposition_id = str(checked["disposition_id"])
        disposition_ids.append(disposition_id)
        # An interpretation is content-addressed independently of the set that
        # currently presents it.  A replacement set may therefore carry the
        # same branch ID.  Its disposition chain must follow that branch across
        # the set boundary instead of silently starting a fresh chain.
        branch_id = str(checked["interpretation_id"])
        by_branch.setdefault(branch_id, []).append(checked)
    if len(disposition_ids) != len(set(disposition_ids)) or tuple(disposition_ids) != tuple(
        sorted(disposition_ids)
    ):
        raise RecordError("branch dispositions must use unique canonical ID order")
    for chain in by_branch.values():
        ordered = sorted(chain, key=lambda item: int(item["decision_sequence"]))
        for index, item in enumerate(ordered, start=1):
            if item["decision_sequence"] != index:
                raise PolicyViolation("branch disposition chain has a sequence gap or fork")
            expected = None if index == 1 else ordered[index - 2]["disposition_id"]
            if item["previous_disposition_id"] != expected:
                raise PolicyViolation("branch disposition chain has an inconsistent predecessor")
            if index > 1 and item["created_on"] < ordered[index - 2]["created_on"]:
                raise PolicyViolation("branch disposition chronology moves backwards")

    decision_ids: list[str] = []
    checked_decisions: list[dict[str, object]] = []
    for raw in decisions:
        item = _object(raw, "translation decision")
        binding = _object(item.get("bindings"), "translation decision.bindings")
        surface = surfaces.get(str(binding.get("snapshot_id")))
        checked_decisions.append(_validate_translation_decision(item, surface=surface))
        decision_ids.append(str(item["decision_id"]))
    if len(decision_ids) != len(set(decision_ids)) or tuple(decision_ids) != tuple(
        sorted(decision_ids)
    ):
        raise RecordError("translation decisions must use unique canonical ID order")
    ordered_decisions = sorted(
        checked_decisions, key=lambda item: int(item["decision_sequence"])
    )
    for index, item in enumerate(ordered_decisions, start=1):
        if item["decision_sequence"] != index:
            raise PolicyViolation("translation decision chain has a sequence gap or fork")
        expected = None if index == 1 else ordered_decisions[index - 2]["decision_id"]
        if item["previous_decision_id"] != expected:
            raise PolicyViolation("translation decision chain has an inconsistent predecessor")
        if index > 1 and item["created_on"] < ordered_decisions[index - 2]["created_on"]:
            raise PolicyViolation("translation decision chronology moves backwards")
    _validate_current_authorization_branch_states(review)


def validate_translation_review(
    review: dict[str, object],
    *,
    expected_bindings: dict[str, object],
    expected_surface: dict[str, object],
) -> dict[str, object]:
    """Validate one review head against the exact current translation snapshot."""

    cached_local_schema_catalog().validate(review, "translation-review-v1.schema.json")
    if review.get("review_id") != compute_translation_review_id(review):
        raise RecordError("translation review content-addressed ID mismatch")
    _surface_index(_object(review.get("review_surface"), "translation review surface"))
    if review.get("bindings") != expected_bindings:
        raise PolicyViolation("translation review is not bound to the exact snapshot")
    if review.get("review_surface") != expected_surface:
        raise PolicyViolation(
            "translation review omitted or changed source spans, alternatives, or model effects"
        )
    _iso_date(review.get("created_on"), "translation review.created_on")
    sequence = review.get("sequence")
    previous = review.get("previous_review_id")
    transition = review.get("transition_kind")
    if sequence == 1:
        if previous is not None or transition != "GENESIS":
            raise PolicyViolation("review genesis must have sequence one and no predecessor")
    elif type(sequence) is not int or sequence < 2 or previous is None or transition == "GENESIS":
        raise PolicyViolation("review successor must link a predecessor")
    _validate_subrecord_chains(
        review,
        {str(expected_bindings["snapshot_id"]): expected_surface},
    )
    return review


def _review_filename(review_id: str) -> str:
    return _content_id(review_id, "TR", "review_id").replace(":", "-") + ".json"


def _claim_filename(parent_review_id: str | None) -> str:
    token = (
        "GENESIS"
        if parent_review_id is None
        else _content_id(parent_review_id, "TR", "parent_review_id").removeprefix("TR:")
    )
    return f"NEXT-{token}.claim"


def _inventory(directory: Path) -> tuple[set[str], set[str]]:
    if not directory.is_dir():
        raise TranslationReviewError(
            "TRANSLATION_REVIEW_PARENT_MISSING",
            f"translation review directory does not exist: {directory}",
        )
    records: set[str] = set()
    claims: set[str] = set()
    for entry in directory.iterdir():
        if not entry.is_file():
            continue
        if entry.name.startswith("TR-") and entry.name.endswith(".json"):
            records.add(entry.name)
        elif entry.name.startswith("NEXT-") and entry.name.endswith(".claim"):
            claims.add(entry.name)
    return records, claims


def _load_review_file(path: Path) -> dict[str, object]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise TranslationReviewError(
            "TRANSLATION_REVIEW_READ_FAILED", f"cannot read review: {exc}"
        ) from exc
    try:
        value = loads_strict(raw.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise RecordError("translation review is not UTF-8") from exc
    review = _object(value, "translation review")
    cached_local_schema_catalog().validate(review, "translation-review-v1.schema.json")
    if review.get("review_id") != compute_translation_review_id(review):
        raise RecordError("translation review content-addressed ID mismatch")
    _surface_index(_object(review.get("review_surface"), "translation review surface"))
    if raw != canonical_bytes(review) + b"\n":
        raise RecordError("translation review file is not canonical JSON plus one newline")
    if path.name != _review_filename(str(review["review_id"])):
        raise RecordError("translation review filename does not match its ID")
    return review


def _items_by_id(review: dict[str, object], field: str, id_field: str) -> dict[str, dict[str, object]]:
    values = review.get(field)
    if type(values) is not list:
        raise RecordError(f"translation review.{field} must be an array")
    return {
        str(_object(item, f"translation review.{field}[]")[id_field]): _object(
            item, f"translation review.{field}[]"
        )
        for item in values
    }


def _branch_heads(review: dict[str, object]) -> dict[str, dict[str, object]]:
    """Return disposition heads keyed by content-addressed branch identity."""

    heads: dict[str, dict[str, object]] = {}
    for item in _items_by_id(review, "branch_dispositions", "disposition_id").values():
        branch_id = str(item["interpretation_id"])
        current = heads.get(branch_id)
        if current is None or int(item["decision_sequence"]) > int(current["decision_sequence"]):
            heads[branch_id] = item
    return heads


def _decision_head(review: dict[str, object]) -> dict[str, object] | None:
    decisions = list(
        _items_by_id(review, "translation_decisions", "decision_id").values()
    )
    return max(decisions, key=lambda item: int(item["decision_sequence"]), default=None)


def _validate_current_authorization_branch_states(
    review: dict[str, object],
) -> None:
    bindings = _object(review["bindings"], "translation review.bindings")
    current_decisions = [
        item
        for item in _items_by_id(
            review, "translation_decisions", "decision_id"
        ).values()
        if item.get("bindings") == bindings
    ]
    decision = max(
        current_decisions,
        key=lambda item: int(item["decision_sequence"]),
        default=None,
    )
    if decision is None or decision.get("disposition") != "AUTHORIZE_SCOPED_USE":
        return
    selected_branch_ids = {
        str(selection["interpretation_id"])
        for variant in decision["authorized_variants"]
        for selection in variant["selections"]
    }
    current_branch_heads = _branch_heads(review)
    stale = {
        branch_id
        for branch_id, item in current_branch_heads.items()
        if item.get("bindings") == bindings
        and item.get("disposition") == "STALE_BY_BINDING_CHANGE"
    }
    if selected_branch_ids.intersection(stale):
        raise PolicyViolation(
            "translation decision selects a stale branch without a later "
            "RETAINED_OPEN disposition"
        )
    excluded = {
        branch_id
        for branch_id, item in current_branch_heads.items()
        if item.get("bindings") == bindings
        and item.get("disposition") == "EXCLUDED_FOR_SCOPE"
    }
    if selected_branch_ids.intersection(excluded):
        raise PolicyViolation("translation decision selects an excluded branch")


def _validate_successor_input_lineage(
    predecessor: dict[str, object],
    successor: dict[str, object],
) -> None:
    """Validate immediate input lineage from facts persisted in review records."""

    if successor.get("transition_kind") != "INPUT_BINDING_CHANGED":
        return

    predecessor_bindings = _object(
        predecessor["bindings"], "predecessor.bindings"
    )
    successor_bindings = _object(successor["bindings"], "successor.bindings")
    predecessor_snapshot_id = str(predecessor_bindings["snapshot_id"])
    if (
        successor_bindings.get("predecessor_snapshot_id")
        != predecessor_snapshot_id
    ):
        raise PolicyViolation(
            "a changed snapshot must name the predecessor review snapshot "
            "as its immediate predecessor"
        )

    predecessor_surface = _object(
        predecessor["review_surface"], "predecessor.review_surface"
    )
    predecessor_sets, _predecessor_interpretations = _surface_index(
        predecessor_surface
    )
    predecessor_set_ids = set(predecessor_sets)
    successor_surface = _object(
        successor["review_surface"], "successor.review_surface"
    )
    successor_sets, _successor_interpretations = _surface_index(successor_surface)
    successor_set_ids = set(successor_sets)
    removed_set_ids = predecessor_set_ids.difference(successor_set_ids)
    added_set_ids = successor_set_ids.difference(predecessor_set_ids)

    replacement_targets: list[str] = []
    for set_id in added_set_ids:
        target = successor_sets[set_id].get("supersedes_interpretation_set_id")
        if target is not None:
            replacement_targets.append(str(target))
    if any(target not in removed_set_ids for target in replacement_targets):
        raise PolicyViolation(
            "a new interpretation set may supersede only an immediately removed "
            "predecessor interpretation set"
        )
    if (
        set(replacement_targets) != removed_set_ids
        or len(replacement_targets) != len(set(replacement_targets))
    ):
        raise PolicyViolation(
            "a changed-set successor must supersede every removed predecessor "
            "interpretation set exactly once"
        )


def _validate_successor(predecessor: dict[str, object], successor: dict[str, object]) -> None:
    if successor.get("sequence") != int(predecessor["sequence"]) + 1:
        raise TranslationReviewError(
            "TRANSLATION_REVIEW_SEQUENCE_MISMATCH",
            "translation review sequence does not extend the selected head",
        )
    if successor.get("previous_review_id") != predecessor.get("review_id"):
        raise TranslationReviewError(
            "TRANSLATION_REVIEW_STALE_HEAD",
            "translation review previous link differs from the selected head",
        )
    if successor.get("created_on") < predecessor.get("created_on"):
        raise PolicyViolation("translation review chronology moves backwards")

    old_dispositions = _items_by_id(
        predecessor, "branch_dispositions", "disposition_id"
    )
    new_dispositions_all = _items_by_id(
        successor, "branch_dispositions", "disposition_id"
    )
    old_decisions = _items_by_id(predecessor, "translation_decisions", "decision_id")
    new_decisions_all = _items_by_id(successor, "translation_decisions", "decision_id")
    for label, old, new in (
        ("branch disposition", old_dispositions, new_dispositions_all),
        ("translation decision", old_decisions, new_decisions_all),
    ):
        missing = set(old).difference(new)
        changed = {key for key in old if key in new and old[key] != new[key]}
        if missing or changed:
            raise PolicyViolation(f"review successor dropped or changed a prior {label}")

    added_dispositions = [
        value for key, value in new_dispositions_all.items() if key not in old_dispositions
    ]
    added_decisions = [
        value for key, value in new_decisions_all.items() if key not in old_decisions
    ]
    targets = [
        (str(item["interpretation_set_id"]), str(item["interpretation_id"]))
        for item in added_dispositions
    ]
    if len(targets) != len(set(targets)):
        raise PolicyViolation("a successor may add at most one disposition per branch")
    if len(added_decisions) > 1:
        raise PolicyViolation("a successor may add at most one translation decision")

    old_bindings = _object(predecessor["bindings"], "predecessor.bindings")
    new_bindings = _object(successor["bindings"], "successor.bindings")
    same_bindings = old_bindings == new_bindings
    if same_bindings:
        if successor.get("transition_kind") != "SAME_BINDINGS":
            raise PolicyViolation("same-binding review successor must declare SAME_BINDINGS")
        if successor.get("review_surface") != predecessor.get("review_surface"):
            raise PolicyViolation("same-binding review changed its review surface")
    else:
        if successor.get("transition_kind") != "INPUT_BINDING_CHANGED":
            raise PolicyViolation("changed-binding review must declare INPUT_BINDING_CHANGED")
        old_surface = _object(predecessor["review_surface"], "predecessor.review_surface")
        new_surface = _object(successor["review_surface"], "successor.review_surface")
        for key in ("document_ids", "charter_id", "graph_id"):
            if old_surface.get(key) != new_surface.get(key):
                raise PolicyViolation(
                    "a different authority or review subject requires a new lineage"
                )
        if added_decisions:
            raise PolicyViolation(
                "a changed snapshot must survive one review head before a decision"
            )
        _validate_successor_input_lineage(predecessor, successor)
        _old_sets, old_interpretations = _surface_index(old_surface)
        expected_stale_targets = {
            (set_id, branch_id)
            for branch_id, (set_id, _branch) in old_interpretations.items()
        }
        if set(targets) != expected_stale_targets:
            raise PolicyViolation(
                "a changed-binding successor must add exact staleness disposition "
                "coverage for every predecessor branch"
            )

    predecessor_branch_heads = _branch_heads(predecessor)
    for item in added_dispositions:
        branch_id = str(item["interpretation_id"])
        previous = predecessor_branch_heads.get(branch_id)
        expected_id = None if previous is None else previous["disposition_id"]
        expected_sequence = 1 if previous is None else int(previous["decision_sequence"]) + 1
        if item["previous_disposition_id"] != expected_id or item["decision_sequence"] != expected_sequence:
            raise PolicyViolation("new branch disposition does not extend its selected head")
        if item["created_on"] != successor["created_on"]:
            raise PolicyViolation("new branch disposition date differs from its review head")
        if item["bindings"] != new_bindings:
            raise PolicyViolation("new branch disposition has stale bindings")
        if same_bindings:
            if item["disposition"] == "STALE_BY_BINDING_CHANGE":
                raise PolicyViolation("same-binding review cannot mark a branch stale")
            _validate_branch_disposition(
                item, surface=_object(successor["review_surface"], "review surface")
            )
            if previous is not None and previous["bindings"] == old_bindings and previous[
                "disposition"
            ] in {"EXCLUDED_FOR_SCOPE", "STALE_BY_BINDING_CHANGE"} and item[
                "disposition"
            ] != "RETAINED_OPEN":
                raise PolicyViolation("a terminal branch can only be reopened explicitly")
        else:
            if item["disposition"] != "STALE_BY_BINDING_CHANGE":
                raise PolicyViolation(
                    "a changed-binding successor may add only staleness dispositions"
                )
            if item["superseded_bindings"] != old_bindings:
                raise PolicyViolation("stale branch does not bind the predecessor inputs")
            expected_changed = list(_changed_pointers(old_bindings, new_bindings))
            if item["changed_binding_pointers"] != expected_changed:
                raise PolicyViolation("stale branch changed or omitted the exact binding delta")
            _validate_branch_disposition(
                item, surface=_object(predecessor["review_surface"], "old review surface")
            )

    old_decision_head = _decision_head(predecessor)
    for item in added_decisions:
        expected_id = None if old_decision_head is None else old_decision_head["decision_id"]
        expected_sequence = 1 if old_decision_head is None else int(
            old_decision_head["decision_sequence"]
        ) + 1
        if item["previous_decision_id"] != expected_id or item["decision_sequence"] != expected_sequence:
            raise PolicyViolation("new translation decision does not extend its selected head")
        if item["created_on"] != successor["created_on"] or item["bindings"] != new_bindings:
            raise PolicyViolation("new translation decision has stale date or bindings")

    _validate_current_authorization_branch_states(successor)


def _state_from_reviews(
    reviews: tuple[dict[str, object], ...],
) -> TranslationReviewState:
    if not reviews:
        return TranslationReviewState(
            None,
            (),
            "AWAITING_HUMAN_REVIEW",
            None,
            {},
            None,
            None,
            (),
        )
    head = reviews[-1]
    bindings = head["bindings"]
    states: dict[str, str] = {}
    for branch_id, item in _branch_heads(head).items():
        if item.get("bindings") == bindings:
            set_id = str(item["interpretation_set_id"])
            states[f"{set_id}/{branch_id}"] = str(item["disposition"])
    current_decisions = [
        item
        for item in _items_by_id(head, "translation_decisions", "decision_id").values()
        if item.get("bindings") == bindings
    ]
    decision = max(
        current_decisions,
        key=lambda item: int(item["decision_sequence"]),
        default=None,
    )
    if decision is None:
        status = "AWAITING_HUMAN_REVIEW"
        decision_id = None
        scope_binding = None
        authorized_variants: tuple[dict[str, object], ...] = ()
    else:
        status = {
            "AUTHORIZE_SCOPED_USE": "SCOPED_USE_SELECTED_AUTHENTICATION_REQUIRED",
            "REJECT_CURRENT_SET_FOR_SCOPE": "REJECTED_FOR_SCOPE",
            "SUSPEND_UNRESOLVED": "SUSPENDED_UNRESOLVED",
            "REFRAME_REVIEW_PROBLEM": "REFRAME_REQUIRED",
        }[str(decision["disposition"])]
        decision_id = str(decision["decision_id"])
        scope_binding = _object(
            decision["scope_binding"], "translation decision.scope_binding"
        )
        variants = decision["authorized_variants"]
        if type(variants) is not list:
            raise RecordError("translation decision.authorized_variants must be an array")
        authorized_variants = tuple(
            _object(item, "translation decision.authorized_variants[]")
            for item in variants
        )
    return TranslationReviewState(
        str(head["review_id"]),
        reviews,
        status,
        decision_id,
        dict(sorted(states.items())),
        str(head["reviewer_authentication"]),
        scope_binding,
        authorized_variants,
    )


def verify_translation_review_chain(
    review_dir: Path,
    head_review_id: str | None,
    *,
    expected_bindings: dict[str, object] | None = None,
    expected_surface: dict[str, object] | None = None,
    _pending_successor_claim: tuple[str, bytes] | None = None,
) -> TranslationReviewState:
    """Verify complete inventory and one explicitly selected terminal lineage."""

    record_names, claim_names = _inventory(review_dir)
    pending_name: str | None = None
    pending_review: dict[str, object] | None = None
    if _pending_successor_claim is not None:
        pending_name, payload = _pending_successor_claim
        if pending_name != _claim_filename(head_review_id) or pending_name not in claim_names:
            raise TranslationReviewError(
                "TRANSLATION_REVIEW_PENDING_CLAIM_INVALID",
                "pending recovery claim does not identify the selected parent",
            )
        if (review_dir / pending_name).read_bytes() != payload:
            raise TranslationReviewError(
                "TRANSLATION_REVIEW_PENDING_CLAIM_INVALID",
                "pending recovery claim changed content",
            )
        try:
            parsed = loads_strict(payload.decode("utf-8"))
        except UnicodeDecodeError as exc:
            raise RecordError("pending translation review is not UTF-8") from exc
        pending_review = _object(parsed, "pending translation review")
        cached_local_schema_catalog().validate(
            pending_review, "translation-review-v1.schema.json"
        )
        if canonical_bytes(pending_review) + b"\n" != payload:
            raise RecordError("pending translation review is not canonical")
        if pending_review.get("review_id") != compute_translation_review_id(pending_review):
            raise RecordError("pending translation review content-addressed ID mismatch")
        _surface_index(
            _object(
                pending_review.get("review_surface"),
                "pending translation review surface",
            )
        )
        if pending_review.get("previous_review_id") != head_review_id:
            raise TranslationReviewError(
                "TRANSLATION_REVIEW_PENDING_CLAIM_INVALID",
                "pending translation review does not extend the selected parent",
            )

    if head_review_id is None:
        allowed_claims = set() if pending_name is None else {pending_name}
        if record_names or claim_names != allowed_claims:
            raise TranslationReviewError(
                "TRANSLATION_REVIEW_HEAD_REQUIRED",
                "a missing review head is valid only for an empty lineage",
            )
        reviews: tuple[dict[str, object], ...] = ()
    else:
        _content_id(head_review_id, "TR", "head_review_id")
        reverse: list[dict[str, object]] = []
        seen: set[str] = set()
        current: str | None = head_review_id
        while current is not None:
            if current in seen:
                raise RecordError("translation review chain contains a cycle")
            seen.add(current)
            review = _load_review_file(review_dir / _review_filename(current))
            if review.get("review_id") != current:
                raise RecordError("translation review chain resolved the wrong record")
            reverse.append(review)
            previous = review.get("previous_review_id")
            current = previous if type(previous) is str else None
        reviews = tuple(reversed(reverse))

    surfaces: dict[str, dict[str, object]] = {}
    for index, review in enumerate(reviews, start=1):
        if review.get("sequence") != index:
            raise RecordError("translation review sequence is not contiguous from one")
        expected_previous = None if index == 1 else reviews[index - 2]["review_id"]
        if review.get("previous_review_id") != expected_previous:
            raise RecordError("translation review previous link is inconsistent")
        binding = _object(review["bindings"], "translation review.bindings")
        snapshot_id = str(binding["snapshot_id"])
        surface = _object(review["review_surface"], "translation review.review_surface")
        old_surface = surfaces.setdefault(snapshot_id, surface)
        if old_surface != surface:
            raise PolicyViolation("one snapshot ID resolved to different review surfaces")
        if index > 1:
            _validate_successor(reviews[index - 2], review)

    for review in reviews:
        _validate_subrecord_chains(review, surfaces)

    expected_records = {_review_filename(str(item["review_id"])) for item in reviews}
    if record_names != expected_records:
        raise TranslationReviewError(
            "TRANSLATION_REVIEW_ORPHAN_RECORD",
            "review directory contains a record outside the selected lineage",
        )
    expected_claims = {
        _claim_filename(
            item["previous_review_id"] if type(item["previous_review_id"]) is str else None
        )
        for item in reviews
    }
    if pending_name is not None:
        expected_claims.add(pending_name)
    if claim_names != expected_claims:
        raise TranslationReviewError(
            "TRANSLATION_REVIEW_CLAIM_INVENTORY_MISMATCH",
            "review successor-claim inventory differs from the selected lineage",
        )
    for review in reviews:
        claim = review_dir / _claim_filename(
            review["previous_review_id"]
            if type(review["previous_review_id"]) is str
            else None
        )
        if claim.read_bytes() != canonical_bytes(review) + b"\n":
            raise RecordError("translation review claim differs from its record")

    if reviews and expected_bindings is not None:
        if reviews[-1]["bindings"] != expected_bindings:
            raise PolicyViolation("selected review head is not bound to the current snapshot")
        if expected_surface is not None and reviews[-1]["review_surface"] != expected_surface:
            raise PolicyViolation("selected review head changed the current review surface")
    if pending_review is not None:
        if not reviews:
            if pending_review.get("sequence") != 1 or pending_review.get("transition_kind") != "GENESIS":
                raise PolicyViolation("first pending translation review must be genesis")
        else:
            _validate_successor(reviews[-1], pending_review)
    return _state_from_reviews(reviews)


def _fsync_directory(directory: Path) -> None:
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def publish_translation_review(
    review_dir: Path,
    review: dict[str, object],
    *,
    expected_head_review_id: str | None,
    snapshot: dict[str, object],
    interpretation_sets: Iterable[dict[str, object]],
) -> Path:
    """Contextually publish one no-clobber review successor."""

    snapshot, sets = _validate_translation_inputs(snapshot, interpretation_sets)
    bindings = translation_review_bindings(snapshot)
    surface = translation_review_surface(snapshot, sets)
    validate_translation_review(
        review, expected_bindings=bindings, expected_surface=surface
    )
    payload = canonical_bytes(review) + b"\n"
    review_id = str(review["review_id"])
    output_path = review_dir / _review_filename(review_id)
    claim_path = review_dir / _claim_filename(expected_head_review_id)

    pending: tuple[str, bytes] | None = None
    if claim_path.exists():
        existing_claim = claim_path.read_bytes()
        if existing_claim != payload:
            raise TranslationReviewError(
                "TRANSLATION_REVIEW_STALE_HEAD",
                "the selected review head already has a different successor claim",
            )
        if output_path.exists():
            if output_path.read_bytes() != payload:
                raise RecordError("translation review record differs from its claim")
            verify_translation_review_chain(
                review_dir,
                review_id,
                expected_bindings=bindings,
                expected_surface=surface,
            )
            _fsync_directory(review_dir)
            return output_path
        pending = (claim_path.name, payload)

    state = verify_translation_review_chain(
        review_dir,
        expected_head_review_id,
        _pending_successor_claim=pending,
    )
    if review.get("sequence") != len(state.reviews) + 1:
        raise TranslationReviewError(
            "TRANSLATION_REVIEW_SEQUENCE_MISMATCH",
            "translation review sequence does not extend the selected head",
        )
    if state.reviews:
        _validate_successor(state.reviews[-1], review)
    elif review.get("transition_kind") != "GENESIS":
        raise PolicyViolation("first published translation review must be genesis")

    temporary_path: Path | None = None
    try:
        if pending is None:
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=".translation-review-", suffix=".tmp", dir=review_dir
            )
            temporary_path = Path(temporary_name)
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            try:
                os.link(temporary_path, claim_path)
            except FileExistsError as exc:
                if claim_path.read_bytes() != payload:
                    raise TranslationReviewError(
                        "TRANSLATION_REVIEW_STALE_HEAD",
                        "the selected review head acquired a sibling successor",
                    ) from exc
            _fsync_directory(review_dir)
        try:
            os.link(claim_path, output_path)
        except FileExistsError as exc:
            if output_path.read_bytes() != payload:
                raise TranslationReviewError(
                    "TRANSLATION_REVIEW_EXISTS",
                    "different content exists at the review ID path",
                ) from exc
        _fsync_directory(review_dir)
    except OSError as exc:
        code = (
            "TRANSLATION_REVIEW_PARENT_MISSING"
            if exc.errno == errno.ENOENT
            else "TRANSLATION_REVIEW_WRITE_FAILED"
        )
        raise TranslationReviewError(code, f"cannot publish translation review: {exc}") from exc
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass
    verify_translation_review_chain(
        review_dir,
        review_id,
        expected_bindings=bindings,
        expected_surface=surface,
    )
    return output_path


def load_translation_inputs(
    snapshot_path: Path,
    interpretation_set_paths: Iterable[Path],
) -> tuple[dict[str, object], tuple[dict[str, object], ...]]:
    """Strict-load canonical translation inputs for the review CLI."""

    snapshot = _object(load_strict(snapshot_path), "translation snapshot")
    if snapshot_path.read_bytes() != canonical_bytes(snapshot) + b"\n":
        raise RecordError("translation snapshot file is not canonical JSON plus one newline")
    sets: list[dict[str, object]] = []
    for path in interpretation_set_paths:
        item = _object(load_strict(path), f"interpretation set {path}")
        if path.read_bytes() != canonical_bytes(item) + b"\n":
            raise RecordError("interpretation set file is not canonical JSON plus one newline")
        sets.append(item)
    return _validate_translation_inputs(snapshot, sets)


def load_translation_review(path: Path) -> dict[str, object]:
    """Strict-load a human-authored draft; publication canonicalizes it."""

    return _object(load_strict(path), "translation review")
