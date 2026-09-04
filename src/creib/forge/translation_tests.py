"""Deterministic test obligations for exact translation/model deltas.

The synthesizer is deliberately weaker than a semantic judge.  It produces a
complete family-indexed attack surface from two content-addressed translation
snapshots and their exact delta.  In this first contract, semantic fixtures,
comparators, executable theory projections, and expectations are not inputs,
so every family is retained as a deferred obligation.  Nothing in this module
can invent an oracle, choose a failure locus, authorize research, or schedule
an action.
"""

from __future__ import annotations

import json
from functools import lru_cache
import re
from typing import Any

from creib.canonical import canonical_bytes, domain_digest
from creib.errors import PolicyViolation, RecordError

from .models import NON_INDUCTIVE_LIMIT


SNAPSHOT_SCHEMA = "creib.semantic-forge.translation-snapshot.v1"
DELTA_SCHEMA = "creib.semantic-forge.translation-snapshot-delta.v1"
SYNTHESIS_SCHEMA = "creib.semantic-forge.translation-test-synthesis.v1"
OBLIGATION_DOMAIN = "creib.semantic-forge.translation-test-obligation.v1"
FAMILY_CONTRACT = "creib.semantic-forge.translation-test-families.v1"

DEFERRED_STATUS = "DEFERRED_MISSING_SEMANTIC_BINDINGS"
OVERALL_STATUS = "AWAITING_SEMANTIC_BINDINGS"
EPISTEMIC_EFFECT = "CRITICISM_ONLY"
FAILURE_LOCUS_POLICY = (
    "A generated or observed test cannot select a unique CANDIDATE, "
    "AUXILIARY, TEST, or SCOPE cause."
)

TEST_FAMILIES = (
    "DELETION",
    "NEGATION",
    "RIVAL_SUBSTITUTION",
    "SEMANTIC_ROLE_TWIN",
    "SUBSTRATE_SWAP",
    "BOUNDARY_SHIFT",
    "IMPORT_DEPENDENCY",
    "NON_VACUITY",
    "ROUND_TRIP",
)

_CONTENT_ID = re.compile(r"^[A-Za-z][A-Za-z0-9._-]*:[0-9a-f]{64}$")
_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")

_SNAPSHOT_KEYS = {
    "schema_version",
    "snapshot_id",
    "predecessor_snapshot_id",
    "document_ids",
    "span_ids",
    "charter_id",
    "graph_id",
    "interpretation_set_ids",
    "signature_id",
    "model_id",
    "import_ids",
    "bridge_id",
    "unresolved_record_ids",
    "record_closure_sha256",
}

_DELTA_KEYS = {
    "schema_version",
    "delta_id",
    "old_snapshot_id",
    "new_snapshot_id",
    "retained_ids",
    "added_ids",
    "removed_ids",
    "replaced_pairs",
    "transported_members",
    "changed_obligation_ids",
    "changed_model_element_ids",
    "changed_import_ids",
    "changed_loss_ids",
    "claimed_preservations",
    "unresolved_effects",
}

_SYNTHESIS_KEYS = {
    "schema_version",
    "synthesis_id",
    "family_contract",
    "old_snapshot_binding",
    "new_snapshot_binding",
    "delta_binding",
    "coverage",
    "overall_status",
    "semantic_verdict",
    "next_action",
    "research_authorized",
    "failure_locus_policy",
    "epistemic_effect",
    "epistemic_limit",
}

_COVERAGE_KEYS = {
    "obligation_id",
    "family",
    "old_snapshot_id",
    "new_snapshot_id",
    "delta_id",
    "target_ids",
    "question",
    "coverage_status",
    "required_semantic_bindings",
    "missing_semantic_bindings",
    "semantic_expectation",
    "semantic_verdict",
    "next_action",
    "research_authorized",
    "epistemic_effect",
    "epistemic_limit",
}

_FAMILY_QUESTIONS: dict[str, str] = {
    "DELETION": (
        "What declared consequence changes when each delta target is removed "
        "while an exact held-fixed contract is preserved?"
    ),
    "NEGATION": (
        "What declared consequence changes under a typed root negation of each "
        "eligible delta target over the same signature and scope?"
    ),
    "RIVAL_SUBSTITUTION": (
        "What differs when an explicitly registered rival replaces the changed "
        "reading under one common comparison transport?"
    ),
    "SEMANTIC_ROLE_TWIN": (
        "Can two models of the same encoded theory share the exact control "
        "reduct while differing only in a declared target-role view?"
    ),
    "SUBSTRATE_SWAP": (
        "Does an explicitly registered substrate replacement preserve the "
        "features named by a separately bound invariance claim?"
    ),
    "BOUNDARY_SHIFT": (
        "How does the result change under a pre-registered boundary alternative "
        "while every declared non-boundary fact remains fixed?"
    ),
    "IMPORT_DEPENDENCY": (
        "Which consequences and mappings depend on each exact changed import, "
        "and does every dependency cross claim kinds through an explicit bridge?"
    ),
    "NON_VACUITY": (
        "Does the successor have an executable model, activate each material "
        "changed condition, and expand every registered intended base?"
    ),
    "ROUND_TRIP": (
        "Does every source obligation map forward or to an explicit loss, and "
        "does every model element map back to source, interpretation, or import?"
    ),
}

_REQUIRED_BINDINGS: dict[str, tuple[str, ...]] = {
    "DELETION": (
        "DELETION_SEMANTICS",
        "HELD_FIXED_CONTRACT",
        "OBSERVABLE_CONTRACT",
        "TYPED_EXPECTATION",
    ),
    "NEGATION": (
        "NEGATABLE_FORM",
        "SATISFIABILITY_CHECKER",
        "OBSERVABLE_CONTRACT",
        "TYPED_EXPECTATION",
    ),
    "RIVAL_SUBSTITUTION": (
        "EXPLICIT_RIVAL_BRANCH",
        "COMMON_COMPARISON_TRANSPORT",
        "TYPED_EXPECTATION",
    ),
    "SEMANTIC_ROLE_TWIN": (
        "EXECUTABLE_THEORY_PROJECTION",
        "CONTROL_SIGNATURE",
        "ROLE_VIEW_SCOPE",
        "MODEL_CHECKER",
    ),
    "SUBSTRATE_SWAP": (
        "SUBSTRATE_INVARIANCE_CLAIM",
        "REALIZATION_TRANSFORM",
        "HELD_FIXED_CONTRACT",
        "TYPED_EXPECTATION",
    ),
    "BOUNDARY_SHIFT": (
        "PREREGISTERED_BOUNDARY_ALTERNATIVES",
        "MEMBERSHIP_FIXTURES",
        "HELD_FIXED_CONTRACT",
        "TYPED_EXPECTATION",
    ),
    "IMPORT_DEPENDENCY": (
        "EXECUTABLE_DEPENDENCY_GRAPH",
        "CLAIM_KIND_BRIDGES",
        "CONSEQUENCE_OBSERVABLES",
    ),
    "NON_VACUITY": (
        "EXECUTABLE_THEORY_PROJECTION",
        "NON_VACUITY_CHECKER",
        "INTENDED_BASE_REGISTRY",
    ),
    "ROUND_TRIP": (
        "FORWARD_TRANSLATOR",
        "BACK_TRANSLATOR",
        "TYPED_COMPARATOR",
    ),
}


@lru_cache(maxsize=1)
def _translation_schema_catalog() -> Any:
    """Load the immutable in-repository schema catalog once per process."""

    from .schema_validation import load_local_schema_catalog

    return load_local_schema_catalog()


def _record_id(prefix: str, domain: str, body: dict[str, object]) -> str:
    digest = domain_digest(domain, body)
    if not _SHA256.fullmatch(digest):
        raise RecordError("internal domain digest has an unexpected shape")
    return f"{prefix}:{digest.removeprefix('sha256:')}"


def _without(record: dict[str, Any], key: str) -> dict[str, object]:
    return {name: value for name, value in record.items() if name != key}


def _object(value: Any, where: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise RecordError(f"{where} must be an object")
    return value


def _exact_keys(record: dict[str, Any], expected: set[str], where: str) -> None:
    actual = set(record)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise RecordError(f"{where} has missing keys {missing} and extra keys {extra}")


def _text(value: Any, where: str) -> str:
    if type(value) is not str or not value.strip():
        raise RecordError(f"{where} must be a non-empty string")
    if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
        raise RecordError(f"{where} contains a Unicode surrogate")
    return value


def _content_id(value: Any, where: str, *, prefix: str | None = None) -> str:
    checked = _text(value, where)
    if not _CONTENT_ID.fullmatch(checked):
        raise RecordError(f"{where} must be a content-addressed identifier")
    if prefix is not None and not checked.startswith(f"{prefix}:"):
        raise RecordError(f"{where} must use the {prefix}: namespace")
    return checked


def _text_array(value: Any, where: str) -> tuple[str, ...]:
    if type(value) is not list:
        raise RecordError(f"{where} must be an array")
    checked = tuple(_text(item, f"{where}[{index}]") for index, item in enumerate(value))
    if len(checked) != len(set(checked)):
        raise RecordError(f"{where} must not contain duplicates")
    if checked != tuple(sorted(checked)):
        raise RecordError(f"{where} must use canonical lexical order")
    return checked


def _content_id_array(value: Any, where: str) -> tuple[str, ...]:
    items = _text_array(value, where)
    for index, item in enumerate(items):
        _content_id(item, f"{where}[{index}]")
    return items


def compute_translation_snapshot_id(record: dict[str, object]) -> str:
    checked = _object(record, "translation snapshot")
    if checked.get("schema_version") != SNAPSHOT_SCHEMA:
        raise RecordError("translation snapshot has an unsupported schema_version")
    # Keep one identity rule for the translation graph and every downstream
    # consumer.  A locally plausible TSN: value must not become a parallel
    # snapshot namespace merely because test synthesis can hash it.
    from .translation import compute_translation_record_id

    return compute_translation_record_id(checked)


def compute_translation_delta_id(record: dict[str, object]) -> str:
    checked = _object(record, "translation delta")
    if checked.get("schema_version") != DELTA_SCHEMA:
        raise RecordError("translation delta has an unsupported schema_version")
    return _record_id(
        "TSD",
        f"{DELTA_SCHEMA}.record-id",
        _without(checked, "delta_id"),
    )


def compute_translation_test_obligation_id(record: dict[str, object]) -> str:
    checked = _object(record, "translation test obligation")
    if checked.get("family") not in TEST_FAMILIES:
        raise RecordError("translation test obligation has an unsupported family")
    return _record_id(
        "TTO",
        f"{OBLIGATION_DOMAIN}.record-id",
        _without(checked, "obligation_id"),
    )


def compute_translation_test_synthesis_id(record: dict[str, object]) -> str:
    checked = _object(record, "translation test synthesis")
    if checked.get("schema_version") != SYNTHESIS_SCHEMA:
        raise RecordError("translation test synthesis has an unsupported schema_version")
    return _record_id(
        "TTS",
        f"{SYNTHESIS_SCHEMA}.record-id",
        _without(checked, "synthesis_id"),
    )


def _validate_snapshot(value: Any, where: str) -> dict[str, Any]:
    record = _object(value, where)
    _exact_keys(record, _SNAPSHOT_KEYS, where)
    if record["schema_version"] != SNAPSHOT_SCHEMA:
        raise RecordError(f"{where} has an unsupported schema_version")
    # Schema validation supplies the exact TDOC/TSPAN/TCHAR/... namespaces;
    # the runtime validator supplies canonical ordering and the shared
    # content-ID rule.  Both are required before a snapshot can seed tests.
    from .translation import validate_translation_record

    _translation_schema_catalog().validate(
        record,
        "translation-snapshot.schema.json",
    )
    validate_translation_record(record)
    snapshot_id = _content_id(record["snapshot_id"], f"{where}.snapshot_id", prefix="TSN")
    predecessor = record["predecessor_snapshot_id"]
    if predecessor is not None:
        _content_id(predecessor, f"{where}.predecessor_snapshot_id", prefix="TSN")
        if predecessor == snapshot_id:
            raise RecordError(f"{where} cannot name itself as predecessor")
    for field in (
        "document_ids",
        "span_ids",
        "interpretation_set_ids",
        "import_ids",
        "unresolved_record_ids",
    ):
        _content_id_array(record[field], f"{where}.{field}")
    for field in ("charter_id", "graph_id", "signature_id", "model_id", "bridge_id"):
        _content_id(record[field], f"{where}.{field}")
    closure = _text(record["record_closure_sha256"], f"{where}.record_closure_sha256")
    if not _SHA256.fullmatch(closure):
        raise RecordError(f"{where}.record_closure_sha256 must be a sha256 digest")
    if snapshot_id != compute_translation_snapshot_id(record):
        raise RecordError(f"{where}.snapshot_id is not the content ID of the snapshot")
    return record


def _validate_pair_array(
    value: Any,
    where: str,
    fields: tuple[str, ...],
) -> tuple[dict[str, str], ...]:
    if type(value) is not list:
        raise RecordError(f"{where} must be an array")
    checked: list[dict[str, str]] = []
    seen: set[bytes] = set()
    for index, item in enumerate(value):
        pair = _object(item, f"{where}[{index}]")
        _exact_keys(pair, set(fields), f"{where}[{index}]")
        normalized: dict[str, str] = {}
        for field in fields:
            normalized[field] = _content_id(
                pair[field],
                f"{where}[{index}].{field}",
            )
        encoded = canonical_bytes(normalized)
        if encoded in seen:
            raise RecordError(f"{where} must not contain duplicates")
        seen.add(encoded)
        checked.append(normalized)
    if tuple(canonical_bytes(item) for item in checked) != tuple(
        sorted(canonical_bytes(item) for item in checked)
    ):
        raise RecordError(f"{where} must use canonical object order")
    return tuple(checked)


def validate_translation_snapshot_delta_record(value: Any) -> dict[str, Any]:
    """Validate one standalone old/new snapshot delta intrinsically."""

    record = _object(value, "translation snapshot delta")
    _exact_keys(record, _DELTA_KEYS, "translation snapshot delta")
    if record["schema_version"] != DELTA_SCHEMA:
        raise RecordError("translation snapshot delta has an unsupported schema_version")
    delta_id = _content_id(
        record["delta_id"], "translation snapshot delta.delta_id", prefix="TSD"
    )
    old_id = _content_id(
        record["old_snapshot_id"],
        "translation snapshot delta.old_snapshot_id",
        prefix="TSN",
    )
    new_id = _content_id(
        record["new_snapshot_id"],
        "translation snapshot delta.new_snapshot_id",
        prefix="TSN",
    )
    if old_id == new_id:
        raise RecordError("translation snapshot delta must bind distinct snapshots")

    for field in (
        "retained_ids",
        "added_ids",
        "removed_ids",
        "changed_obligation_ids",
        "changed_model_element_ids",
        "changed_import_ids",
        "changed_loss_ids",
    ):
        _content_id_array(record[field], f"translation snapshot delta.{field}")
    replacement_pairs = _validate_pair_array(
        record["replaced_pairs"],
        "translation snapshot delta.replaced_pairs",
        ("old_id", "new_id"),
    )
    if any(item["old_id"] == item["new_id"] for item in replacement_pairs):
        raise RecordError("translation snapshot delta replacement must change identity")
    partition_groups = {
        "retained": set(record["retained_ids"]),
        "added": set(record["added_ids"]),
        "removed": set(record["removed_ids"]),
        "replacement-old": {item["old_id"] for item in replacement_pairs},
        "replacement-new": {item["new_id"] for item in replacement_pairs},
    }
    seen_partition_ids: dict[str, str] = {}
    for group, identifiers in partition_groups.items():
        for identifier in identifiers:
            previous = seen_partition_ids.setdefault(identifier, group)
            if previous != group:
                raise PolicyViolation(
                    "translation snapshot delta identity appears in incompatible "
                    f"partitions: {previous} and {group}"
                )
    transported_members = _validate_pair_array(
        record["transported_members"],
        "translation snapshot delta.transported_members",
        ("old_member_id", "new_member_id", "transport_ref"),
    )
    if any(
        item["old_member_id"] == item["new_member_id"]
        for item in transported_members
    ):
        raise RecordError("translation snapshot delta transport must change member identity")
    _text_array(
        record["claimed_preservations"],
        "translation snapshot delta.claimed_preservations",
    )
    _text_array(
        record["unresolved_effects"],
        "translation snapshot delta.unresolved_effects",
    )

    if not _delta_target_ids(record):
        raise RecordError("translation snapshot delta must identify a changed target")
    if delta_id != compute_translation_delta_id(record):
        raise RecordError("translation snapshot delta.delta_id is not its content ID")
    return record


def _validate_delta(
    value: Any,
    old_snapshot: dict[str, Any],
    new_snapshot: dict[str, Any],
) -> dict[str, Any]:
    record = validate_translation_snapshot_delta_record(value)
    old_id = record["old_snapshot_id"]
    new_id = record["new_snapshot_id"]
    if old_id != old_snapshot["snapshot_id"] or new_id != new_snapshot["snapshot_id"]:
        raise RecordError("translation snapshot delta does not bind the supplied snapshots")
    if new_snapshot.get("predecessor_snapshot_id") != old_id:
        raise PolicyViolation(
            "new translation snapshot does not name the old snapshot as predecessor"
        )
    return record


def _delta_target_ids(delta: dict[str, Any]) -> tuple[str, ...]:
    targets: set[str] = set()
    for field in (
        "added_ids",
        "removed_ids",
        "changed_obligation_ids",
        "changed_model_element_ids",
        "changed_import_ids",
        "changed_loss_ids",
    ):
        value = delta.get(field, [])
        if type(value) is list:
            targets.update(item for item in value if type(item) is str)
    for item in delta.get("replaced_pairs", []):
        if type(item) is dict:
            targets.update(
                value for key, value in item.items() if key in {"old_id", "new_id"} and type(value) is str
            )
    for item in delta.get("transported_members", []):
        if type(item) is dict:
            targets.update(
                value
                for key, value in item.items()
                if key in {"old_member_id", "new_member_id", "transport_ref"}
                and type(value) is str
            )
    return tuple(sorted(targets))


def _input_binding(record: dict[str, Any], id_field: str) -> dict[str, str]:
    return {
        "record_id": _text(record[id_field], f"input.{id_field}"),
        "record_digest": domain_digest(
            f"{record['schema_version']}.complete-record",
            record,
        ),
    }


def _obligation(
    family: str,
    target_ids: tuple[str, ...],
    *,
    old_snapshot_id: str,
    new_snapshot_id: str,
    delta_id: str,
) -> dict[str, object]:
    required = list(_REQUIRED_BINDINGS[family])
    body: dict[str, object] = {
        "family": family,
        "old_snapshot_id": old_snapshot_id,
        "new_snapshot_id": new_snapshot_id,
        "delta_id": delta_id,
        "target_ids": list(target_ids),
        "question": _FAMILY_QUESTIONS[family],
        "coverage_status": DEFERRED_STATUS,
        "required_semantic_bindings": required,
        "missing_semantic_bindings": list(required),
        "semantic_expectation": None,
        "semantic_verdict": None,
        "next_action": None,
        "research_authorized": False,
        "epistemic_effect": EPISTEMIC_EFFECT,
        "epistemic_limit": NON_INDUCTIVE_LIMIT,
    }
    return {
        "obligation_id": _record_id(
            "TTO",
            f"{OBLIGATION_DOMAIN}.record-id",
            body,
        ),
        **body,
    }


def synthesize_translation_tests(
    old_snapshot: dict[str, object],
    new_snapshot: dict[str, object],
    delta: dict[str, object],
) -> dict[str, object]:
    """Return the exact nine-family, non-authorizing synthesis bundle.

    Snapshot and delta identities are recomputed before use.  The v1 input
    surface contains no executable semantic projection or typed expectation,
    so the family rows are obligations awaiting those bindings rather than
    fabricated tests with guessed answers.
    """

    old = _validate_snapshot(old_snapshot, "old translation snapshot")
    new = _validate_snapshot(new_snapshot, "new translation snapshot")
    checked_delta = _validate_delta(delta, old, new)
    targets = _delta_target_ids(checked_delta)
    coverage = [
        _obligation(
            family,
            targets,
            old_snapshot_id=str(old["snapshot_id"]),
            new_snapshot_id=str(new["snapshot_id"]),
            delta_id=str(checked_delta["delta_id"]),
        )
        for family in TEST_FAMILIES
    ]
    body: dict[str, object] = {
        "schema_version": SYNTHESIS_SCHEMA,
        "family_contract": FAMILY_CONTRACT,
        "old_snapshot_binding": _input_binding(old, "snapshot_id"),
        "new_snapshot_binding": _input_binding(new, "snapshot_id"),
        "delta_binding": _input_binding(checked_delta, "delta_id"),
        "coverage": coverage,
        "overall_status": OVERALL_STATUS,
        "semantic_verdict": None,
        "next_action": None,
        "research_authorized": False,
        "failure_locus_policy": FAILURE_LOCUS_POLICY,
        "epistemic_effect": EPISTEMIC_EFFECT,
        "epistemic_limit": NON_INDUCTIVE_LIMIT,
    }
    return {
        "synthesis_id": _record_id(
            "TTS",
            f"{SYNTHESIS_SCHEMA}.record-id",
            body,
        ),
        **body,
    }


def validate_translation_test_synthesis(
    value: Any,
    *,
    old_snapshot: dict[str, object],
    new_snapshot: dict[str, object],
    delta: dict[str, object],
) -> dict[str, object]:
    """Validate a bundle by exact deterministic regeneration."""

    record = _object(value, "translation test synthesis")
    _exact_keys(record, _SYNTHESIS_KEYS, "translation test synthesis")
    if record.get("schema_version") != SYNTHESIS_SCHEMA:
        raise RecordError("translation test synthesis has an unsupported schema_version")
    _content_id(record.get("synthesis_id"), "translation test synthesis.synthesis_id", prefix="TTS")
    coverage = record.get("coverage")
    if type(coverage) is not list:
        raise RecordError("translation test synthesis.coverage must be an array")
    if len(coverage) != len(TEST_FAMILIES):
        raise RecordError("translation test synthesis must contain exactly nine family rows")
    for index, (item, expected_family) in enumerate(zip(coverage, TEST_FAMILIES, strict=True)):
        row = _object(item, f"translation test synthesis.coverage[{index}]")
        _exact_keys(row, _COVERAGE_KEYS, f"translation test synthesis.coverage[{index}]")
        if row.get("family") != expected_family:
            raise RecordError("translation test synthesis family rows are not in canonical order")
        _content_id(
            row.get("obligation_id"),
            f"translation test synthesis.coverage[{index}].obligation_id",
            prefix="TTO",
        )
        if row.get("obligation_id") != compute_translation_test_obligation_id(row):
            raise RecordError("translation test obligation has an inconsistent content ID")
        if row.get("semantic_expectation") is not None or row.get("semantic_verdict") is not None:
            raise PolicyViolation("translation test synthesis cannot invent a semantic oracle")
        if row.get("next_action") is not None or row.get("research_authorized") is not False:
            raise PolicyViolation("translation test synthesis cannot choose an action or authorize research")

    if record.get("semantic_verdict") is not None:
        raise PolicyViolation("translation test synthesis cannot assign a semantic verdict")
    if record.get("next_action") is not None or record.get("research_authorized") is not False:
        raise PolicyViolation("translation test synthesis cannot choose an action or authorize research")
    if record.get("epistemic_limit") != NON_INDUCTIVE_LIMIT:
        raise PolicyViolation("translation test synthesis weakens the non-inductive limit")
    if record.get("synthesis_id") != compute_translation_test_synthesis_id(record):
        raise RecordError("translation test synthesis has an inconsistent content ID")

    expected = synthesize_translation_tests(old_snapshot, new_snapshot, delta)
    if record != expected:
        raise RecordError("translation test synthesis does not exactly regenerate from its inputs")
    return record


def dumps_translation_test_synthesis(
    record: dict[str, object],
    *,
    old_snapshot: dict[str, object],
    new_snapshot: dict[str, object],
    delta: dict[str, object],
) -> str:
    """Return deterministic compact JSON after contextual validation."""

    checked = validate_translation_test_synthesis(
        record,
        old_snapshot=old_snapshot,
        new_snapshot=new_snapshot,
        delta=delta,
    )
    return canonical_bytes(checked).decode("utf-8")


def loads_translation_test_synthesis(
    source: str,
    *,
    old_snapshot: dict[str, object],
    new_snapshot: dict[str, object],
    delta: dict[str, object],
) -> dict[str, object]:
    """Parse duplicate-key-safe JSON and contextually validate it."""

    if type(source) is not str:
        raise TypeError("source must be a string")

    def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, item in pairs:
            if key in result:
                raise RecordError(f"duplicate JSON key: {key}")
            result[key] = item
        return result

    try:
        value = json.loads(
            source,
            object_pairs_hook=no_duplicates,
            parse_constant=lambda item: (_ for _ in ()).throw(
                RecordError(f"non-finite JSON number: {item}")
            ),
        )
    except RecordError:
        raise
    except (TypeError, ValueError, RecursionError) as exc:
        raise RecordError(f"invalid translation test synthesis JSON: {exc}") from exc
    return validate_translation_test_synthesis(
        value,
        old_snapshot=old_snapshot,
        new_snapshot=new_snapshot,
        delta=delta,
    )
