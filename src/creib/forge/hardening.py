"""Digest-bound, non-scalar hardening comparisons.

The protocol in this module is deliberately narrower than a theorem prover.
It binds one comparison, derives every required obligation, replays the finite
checker that this version actually implements, and combines that mechanical
record with separate human decisions.  It never turns test frequency, source
agreement, or a human decision into missing mechanical evidence.

Neutral semantic-model records whose execution semantics are ``NONE_V1`` stay
unresolved.  The finite checker exists to qualify the protocol and to support
genuinely finite, exhaustively declared model classes; it is not a surrogate
for executable semantics of a prose model.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date
import os
from pathlib import Path
import re
from typing import Any, Iterable, Mapping, Sequence

from creib.canonical import bytes_digest, canonical_bytes, domain_digest, file_digest
from creib.errors import PolicyViolation, RecordError


COMPARISON_SCHEMA = "creib.semantic-forge.hardening-comparison.v1"
EVIDENCE_SCHEMA = "creib.semantic-forge.hardening-evidence.v1"
DECISION_SCHEMA = "creib.semantic-forge.hardening-decision.v1"
RESOLUTION_SCHEMA = "creib.semantic-forge.hardening-resolution.v1"

OBLIGATION_DOMAIN = "creib.semantic-forge.hardening-obligation.v1"
DECISION_REQUIREMENT_DOMAIN = "creib.semantic-forge.hardening-decision-requirement.v1"
TARGET_ROLE_DOMAIN = "creib.semantic-forge.target-role-registry.v1"
SCOPE_DOMAIN = "creib.semantic-forge.hardening-scope.v1"
PROTECTION_DOMAIN = "creib.semantic-forge.hardening-protection-registry.v1"
GAIN_DOMAIN = "creib.semantic-forge.hardening-gain.v1"
DELTA_DOMAIN = "creib.semantic-forge.hardening-delta.v1"
IMPORT_DOMAIN = "creib.semantic-forge.hardening-import-set.v1"
EVIDENCE_INVENTORY_DOMAIN = "creib.semantic-forge.hardening-evidence-inventory.v1"
DECISION_INVENTORY_DOMAIN = "creib.semantic-forge.hardening-decision-inventory.v1"

NON_INDUCTIVE_LIMIT = (
    "Survival of criticism leaves a claim unrefuted; pass counts, consensus, "
    "and confidence do not justify it."
)

HARDENING_STATUSES = frozenset(
    {"HARDENING_UNREFUTED", "NO_HARDENING", "UNRESOLVED"}
)
EVIDENCE_OUTCOMES = frozenset(
    {"WITNESSED", "COUNTERWITNESSED", "INCONCLUSIVE"}
)
DECISION_DISPOSITIONS = frozenset(
    {
        "ACCEPT_FOR_DECLARED_SCOPE",
        "SUSPEND",
        "COMPARISON_DEFECT",
        "DEFEATS_HARDENING",
    }
)
EXECUTION_SEMANTICS = frozenset(
    {"NONE_V1", "FINITE_EXHAUSTIVE_V1", "PROOF_CERTIFIED_V1"}
)
MODEL_DOMAIN_MODES = frozenset(
    {"NONEXHAUSTIVE_SEARCH", "FINITE_EXHAUSTIVE", "PROOF_DEFINED"}
)

COMMON_OBLIGATION_KINDS = (
    "OLD_RESULT_NON_BROADENING",
    "ROLE_FIBER_NON_BROADENING",
    "SUCCESSOR_NON_VACUITY",
    "SCOPE_PRESERVATION",
    "TYPE_DEPENDENCY_PRESERVATION",
)
ITEM_OBLIGATION_KINDS = frozenset(
    {
        "TARGETED_GAIN_OLD_RESULT",
        "TARGETED_GAIN_ROLE_FIBER",
        "POSITIVE_PRESERVATION",
        "EXCLUSION_PRESERVATION",
        "CONSEQUENCE_PRESERVATION",
        "CLAUSE_INDEPENDENCE",
    }
)
OBLIGATION_KINDS = frozenset(COMMON_OBLIGATION_KINDS) | ITEM_OBLIGATION_KINDS

DECISION_KINDS = (
    "GAIN_RELEVANCE_FOR_SCOPE",
    "PROTECTION_REGISTRY_FOR_SCOPE",
    "SCOPE_USE_FOR_COMPARISON",
    "TYPE_AND_DELTA_CLASSIFICATION",
)
IMPORT_DECISION_KIND = "IMPORT_USE_FOR_SCOPE"

_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9._:-]{0,255}$")
_CONTENT_ID = re.compile(r"^(HC|HO|HE|HD|HR|HRQ):[0-9a-f]{64}$")
_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")


def _object(value: Any, where: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise RecordError(f"{where} must be an object")
    return value


def _array(value: Any, where: str) -> list[Any]:
    if type(value) is not list:
        raise RecordError(f"{where} must be an array")
    return value


def _string(value: Any, where: str) -> str:
    if type(value) is not str or not value.strip():
        raise RecordError(f"{where} must be a non-empty string")
    if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
        raise RecordError(f"{where} contains a Unicode surrogate")
    return value


def _identifier(value: Any, where: str) -> str:
    text = _string(value, where)
    if not _IDENTIFIER.fullmatch(text):
        raise RecordError(f"{where} must be a stable identifier")
    return text


def _content_id(value: Any, prefix: str, where: str) -> str:
    text = _string(value, where)
    if not text.startswith(prefix + ":") or not _CONTENT_ID.fullmatch(text):
        raise RecordError(f"{where} must be a {prefix}: content identifier")
    return text


def _digest(value: Any, where: str) -> str:
    text = _string(value, where)
    if not _SHA256.fullmatch(text):
        raise RecordError(f"{where} must be a sha256: lowercase digest")
    return text


def _exact_keys(value: Mapping[str, Any], expected: set[str], where: str) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise RecordError(f"{where} has unexpected keys; missing={missing}, extra={extra}")


def _without(record: Mapping[str, Any], key: str) -> dict[str, Any]:
    return {name: value for name, value in record.items() if name != key}


def _record_id(prefix: str, domain: str, body: Mapping[str, Any]) -> str:
    return f"{prefix}:{domain_digest(domain, dict(body)).removeprefix('sha256:')}"


def _canonical_strings(
    value: Any,
    where: str,
    *,
    nonempty: bool = False,
    identifiers: bool = False,
) -> tuple[str, ...]:
    values = _array(value, where)
    checked = tuple(
        (_identifier(item, f"{where}[{index}]") if identifiers else _string(item, f"{where}[{index}]"))
        for index, item in enumerate(values)
    )
    if nonempty and not checked:
        raise RecordError(f"{where} must not be empty")
    if checked != tuple(sorted(set(checked))):
        raise RecordError(f"{where} must be unique and use canonical lexical order")
    return checked


def _record_ref(value: Any, where: str) -> dict[str, str]:
    ref = _object(value, where)
    _exact_keys(ref, {"record_id", "schema_version", "record_sha256"}, where)
    return {
        "record_id": _identifier(ref["record_id"], f"{where}.record_id"),
        "schema_version": _identifier(ref["schema_version"], f"{where}.schema_version"),
        "record_sha256": _digest(ref["record_sha256"], f"{where}.record_sha256"),
    }


def _optional_record_ref(value: Any, where: str) -> dict[str, str] | None:
    if value is None:
        return None
    return _record_ref(value, where)


def _canonical_refs(value: Any, where: str, *, nonempty: bool = False) -> tuple[dict[str, str], ...]:
    refs = tuple(
        _record_ref(item, f"{where}[{index}]")
        for index, item in enumerate(_array(value, where))
    )
    if nonempty and not refs:
        raise RecordError(f"{where} must not be empty")
    keys = tuple(ref["record_id"] for ref in refs)
    if keys != tuple(sorted(set(keys))):
        raise RecordError(f"{where} must have unique record IDs in lexical order")
    return refs


def _ref_identity(ref: Mapping[str, str]) -> tuple[str, str, str]:
    return (ref["record_id"], ref["schema_version"], ref["record_sha256"])


def _assert_global_reference_coherence(value: Any) -> None:
    """Reject one record ID being rebound to different schema or bytes."""

    registry: dict[str, tuple[str, str]] = {}

    def visit(node: Any) -> None:
        if type(node) is dict:
            if set(node) == {"record_id", "schema_version", "record_sha256"}:
                ref = _record_ref(node, "comparison record reference")
                identity = (ref["schema_version"], ref["record_sha256"])
                prior = registry.setdefault(ref["record_id"], identity)
                if prior != identity:
                    raise PolicyViolation(
                        "one hardening record ID is rebound to conflicting bytes"
                    )
                return
            for item in node.values():
                visit(item)
        elif type(node) is list:
            for item in node:
                visit(item)

    visit(value)


def compute_comparison_id(record: Mapping[str, Any]) -> str:
    return _record_id("HC", COMPARISON_SCHEMA, _without(record, "comparison_id"))


def compute_evidence_id(record: Mapping[str, Any]) -> str:
    return _record_id("HE", EVIDENCE_SCHEMA, _without(record, "evidence_id"))


def compute_decision_id(record: Mapping[str, Any]) -> str:
    return _record_id("HD", DECISION_SCHEMA, _without(record, "decision_id"))


def compute_resolution_id(record: Mapping[str, Any]) -> str:
    return _record_id("HR", RESOLUTION_SCHEMA, _without(record, "resolution_id"))


def _validate_theory_binding(value: Any, where: str) -> dict[str, Any]:
    binding = _object(value, where)
    _exact_keys(
        binding,
        {
            "snapshot_ref",
            "review_head_ref",
            "model_ref",
            "signature_ref",
            "theory_record_sha256",
            "dependency_closure_sha256",
        },
        where,
    )
    for field in ("snapshot_ref", "review_head_ref", "model_ref", "signature_ref"):
        _record_ref(binding[field], f"{where}.{field}")
    _digest(binding["theory_record_sha256"], f"{where}.theory_record_sha256")
    _digest(binding["dependency_closure_sha256"], f"{where}.dependency_closure_sha256")
    return binding


def _validate_target_roles(value: Any) -> dict[str, Any]:
    roles = _object(value, "comparison.target_roles")
    _exact_keys(roles, {"registry_id", "registry_sha256", "symbols"}, "comparison.target_roles")
    _identifier(roles["registry_id"], "comparison.target_roles.registry_id")
    symbols = _array(roles["symbols"], "comparison.target_roles.symbols")
    if not symbols:
        raise RecordError("comparison.target_roles.symbols must not be empty")
    names: list[str] = []
    for index, raw in enumerate(symbols):
        where = f"comparison.target_roles.symbols[{index}]"
        symbol = _object(raw, where)
        _exact_keys(symbol, {"symbol", "kind", "argument_roles"}, where)
        names.append(_identifier(symbol["symbol"], f"{where}.symbol"))
        if symbol["kind"] not in {"RELATION", "FUNCTION", "CONSTANT"}:
            raise RecordError(f"{where}.kind is unsupported")
        _canonical_strings(symbol["argument_roles"], f"{where}.argument_roles", identifiers=True)
    if tuple(names) != tuple(sorted(set(names))):
        raise RecordError("comparison.target_roles.symbols must be unique and lexically ordered")
    expected = domain_digest(
        TARGET_ROLE_DOMAIN,
        {"registry_id": roles["registry_id"], "symbols": symbols},
    )
    if roles["registry_sha256"] != expected:
        raise RecordError("comparison target-role registry digest mismatch")
    return roles


def _validate_signatures(value: Any, target_names: set[str]) -> dict[str, Any]:
    signatures = _object(value, "comparison.signatures")
    _exact_keys(
        signatures,
        {
            "candidate_symbols",
            "old_result_symbols",
            "control_symbols",
            "preservation_scope_symbols",
        },
        "comparison.signatures",
    )
    candidate = set(
        _canonical_strings(
            signatures["candidate_symbols"],
            "comparison.signatures.candidate_symbols",
            nonempty=True,
            identifiers=True,
        )
    )
    old = set(
        _canonical_strings(
            signatures["old_result_symbols"],
            "comparison.signatures.old_result_symbols",
            identifiers=True,
        )
    )
    control = set(
        _canonical_strings(
            signatures["control_symbols"],
            "comparison.signatures.control_symbols",
            identifiers=True,
        )
    )
    scope = set(
        _canonical_strings(
            signatures["preservation_scope_symbols"],
            "comparison.signatures.preservation_scope_symbols",
            identifiers=True,
        )
    )
    if not target_names <= candidate:
        raise PolicyViolation("target roles must belong to the declared candidate signature")
    if not old <= scope or not control <= scope:
        raise PolicyViolation("old-result and control signatures must be within preservation scope")
    if not scope <= candidate:
        raise PolicyViolation("preservation scope must be within the candidate signature")
    if target_names & (old | control | scope):
        raise PolicyViolation("target roles must be excluded from old, control, and preservation signatures")
    return signatures


def _validate_gain(value: Any) -> dict[str, Any]:
    gain = _object(value, "comparison.gain")
    _exact_keys(
        gain,
        {
            "axis",
            "bad_old_result_id",
            "control_base_id",
            "bad_assignment_id",
            "keep_assignment_id",
        },
        "comparison.gain",
    )
    axis = gain["axis"]
    if axis == "OLD_RESULT_RESTRICTION":
        _identifier(gain["bad_old_result_id"], "comparison.gain.bad_old_result_id")
        if any(gain[field] is not None for field in ("control_base_id", "bad_assignment_id", "keep_assignment_id")):
            raise RecordError("old-result gain must not carry role-fiber targets")
    elif axis == "ROLE_NARROWING":
        if gain["bad_old_result_id"] is not None:
            raise RecordError("role-narrowing gain must not carry an old-result target")
        for field in ("control_base_id", "bad_assignment_id", "keep_assignment_id"):
            _identifier(gain[field], f"comparison.gain.{field}")
        if gain["bad_assignment_id"] == gain["keep_assignment_id"]:
            raise RecordError("role-narrowing bad and retained assignments must differ")
    else:
        raise RecordError("comparison.gain.axis is unsupported")
    return gain


def _validate_change_inventory(value: Any) -> tuple[dict[str, Any], ...]:
    changes = _array(value, "comparison.change_inventory")
    if not changes:
        raise RecordError("comparison.change_inventory must not be empty")
    checked: list[dict[str, Any]] = []
    identifiers: list[str] = []
    for index, raw in enumerate(changes):
        where = f"comparison.change_inventory[{index}]"
        change = _object(raw, where)
        _exact_keys(
            change,
            {
                "change_id",
                "disposition",
                "premise_kind",
                "baseline_ref",
                "successor_ref",
                "transport_refs",
            },
            where,
        )
        identifiers.append(_identifier(change["change_id"], f"{where}.change_id"))
        disposition = change["disposition"]
        if disposition not in {"RETAINED", "ADDED", "REMOVED", "REPLACED", "TRANSPORTED"}:
            raise RecordError(f"{where}.disposition is unsupported")
        if change["premise_kind"] not in {
            "SOURCE_AUTHORITY",
            "SOURCE_INTERPRETATION",
            "PROJECT_IMPORT",
        }:
            raise RecordError(f"{where}.premise_kind is unsupported")
        baseline = _optional_record_ref(change["baseline_ref"], f"{where}.baseline_ref")
        successor = _optional_record_ref(change["successor_ref"], f"{where}.successor_ref")
        transports = _canonical_refs(change["transport_refs"], f"{where}.transport_refs")
        if disposition == "RETAINED":
            if baseline is None or successor is None or _ref_identity(baseline) != _ref_identity(successor):
                raise RecordError("retained change requires one unchanged record on both sides")
        elif disposition == "ADDED":
            if baseline is not None or successor is None:
                raise RecordError("added change requires only a successor record")
        elif disposition == "REMOVED":
            if baseline is None or successor is not None:
                raise RecordError("removed change requires only a baseline record")
        else:
            if baseline is None or successor is None:
                raise RecordError(f"{disposition.lower()} change requires records on both sides")
        if disposition == "TRANSPORTED" and not transports:
            raise RecordError("transported change requires an explicit transport record")
        if disposition != "TRANSPORTED" and transports:
            raise RecordError("only a transported change may carry transport records")
        checked.append(change)
    if tuple(identifiers) != tuple(sorted(set(identifiers))):
        raise RecordError("comparison.change_inventory must use unique lexical change IDs")
    return tuple(checked)


def validate_hardening_comparison(value: Any) -> dict[str, Any]:
    comparison = _object(value, "comparison")
    _exact_keys(
        comparison,
        {
            "schema_version",
            "record_type",
            "comparison_id",
            "declared_purpose",
            "baseline",
            "successor",
            "translation_delta_ref",
            "criticism_state",
            "target_roles",
            "signatures",
            "role_view",
            "model_domain",
            "gain",
            "protections",
            "necessary_clauses",
            "imports",
            "change_inventory",
            "execution_semantics",
            "semantic_verdict",
            "epistemic_limit",
        },
        "comparison",
    )
    if comparison["schema_version"] != COMPARISON_SCHEMA:
        raise RecordError("unsupported hardening comparison schema")
    if comparison["record_type"] != "hardening_comparison":
        raise RecordError("hardening comparison changed record_type")
    if comparison["comparison_id"] != compute_comparison_id(comparison):
        raise RecordError("hardening comparison content-addressed ID mismatch")
    _string(comparison["declared_purpose"], "comparison.declared_purpose")
    baseline = _validate_theory_binding(comparison["baseline"], "comparison.baseline")
    successor = _validate_theory_binding(comparison["successor"], "comparison.successor")
    if baseline["snapshot_ref"]["record_id"] == successor["snapshot_ref"]["record_id"]:
        raise RecordError("hardening baseline and successor snapshots must differ")
    if baseline["model_ref"]["record_id"] == successor["model_ref"]["record_id"]:
        raise RecordError("hardening baseline and successor models must differ")
    _record_ref(comparison["translation_delta_ref"], "comparison.translation_delta_ref")

    criticism = _object(comparison["criticism_state"], "comparison.criticism_state")
    _exact_keys(criticism, {"snapshot_ref", "effective_live_criticism_ids"}, "comparison.criticism_state")
    _record_ref(criticism["snapshot_ref"], "comparison.criticism_state.snapshot_ref")
    _canonical_strings(
        criticism["effective_live_criticism_ids"],
        "comparison.criticism_state.effective_live_criticism_ids",
        identifiers=True,
    )

    roles = _validate_target_roles(comparison["target_roles"])
    target_names = {item["symbol"] for item in roles["symbols"]}
    _validate_signatures(comparison["signatures"], target_names)

    role_view = _object(comparison["role_view"], "comparison.role_view")
    _exact_keys(role_view, {"kind", "localization_ref"}, "comparison.role_view")
    if role_view["kind"] == "GLOBAL":
        if role_view["localization_ref"] is not None:
            raise RecordError("global role view must not carry a localization record")
    elif role_view["kind"] == "HISTORY_LOCAL":
        _record_ref(role_view["localization_ref"], "comparison.role_view.localization_ref")
    else:
        raise RecordError("comparison.role_view.kind is unsupported")

    domain = _object(comparison["model_domain"], "comparison.model_domain")
    _exact_keys(domain, {"mode", "domain_ref"}, "comparison.model_domain")
    if domain["mode"] not in MODEL_DOMAIN_MODES:
        raise RecordError("comparison.model_domain.mode is unsupported")
    domain_ref = _optional_record_ref(domain["domain_ref"], "comparison.model_domain.domain_ref")
    if domain["mode"] in {"FINITE_EXHAUSTIVE", "PROOF_DEFINED"} and domain_ref is None:
        raise RecordError("exhaustive and proof-defined domains require a record reference")

    semantics = comparison["execution_semantics"]
    if semantics not in EXECUTION_SEMANTICS:
        raise RecordError("comparison.execution_semantics is unsupported")
    expected_mode = {
        "NONE_V1": "NONEXHAUSTIVE_SEARCH",
        "FINITE_EXHAUSTIVE_V1": "FINITE_EXHAUSTIVE",
        "PROOF_CERTIFIED_V1": "PROOF_DEFINED",
    }[semantics]
    if domain["mode"] != expected_mode:
        raise PolicyViolation("execution semantics and model-domain mode do not agree")

    _validate_gain(comparison["gain"])
    protections = _object(comparison["protections"], "comparison.protections")
    _exact_keys(protections, {"positives", "exclusions", "consequences"}, "comparison.protections")
    positive = _canonical_refs(protections["positives"], "comparison.protections.positives", nonempty=True)
    exclusions = _canonical_refs(protections["exclusions"], "comparison.protections.exclusions")
    consequences = _canonical_refs(protections["consequences"], "comparison.protections.consequences")
    protection_ids = [ref["record_id"] for ref in (*positive, *exclusions, *consequences)]
    if len(protection_ids) != len(set(protection_ids)):
        raise RecordError("one protection record cannot occupy more than one protection class")

    clauses = _array(comparison["necessary_clauses"], "comparison.necessary_clauses")
    clause_ids: list[str] = []
    for index, raw in enumerate(clauses):
        where = f"comparison.necessary_clauses[{index}]"
        clause = _object(raw, where)
        _exact_keys(clause, {"clause_ref", "defect_witness_ref"}, where)
        clause_ref = _record_ref(clause["clause_ref"], f"{where}.clause_ref")
        _record_ref(clause["defect_witness_ref"], f"{where}.defect_witness_ref")
        clause_ids.append(clause_ref["record_id"])
    if tuple(clause_ids) != tuple(sorted(set(clause_ids))):
        raise RecordError("comparison.necessary_clauses must use unique lexical clause IDs")

    _canonical_refs(comparison["imports"], "comparison.imports")
    _validate_change_inventory(comparison["change_inventory"])
    if comparison["semantic_verdict"] is not None:
        raise PolicyViolation("hardening comparison cannot carry a semantic verdict")
    if comparison["epistemic_limit"] != NON_INDUCTIVE_LIMIT:
        raise PolicyViolation("hardening comparison weakens the non-inductive limit")
    _assert_global_reference_coherence(comparison)
    return comparison


def seal_hardening_comparison(body: Mapping[str, Any]) -> dict[str, Any]:
    if "comparison_id" in body:
        raise ValueError("comparison body must not already contain comparison_id")
    record = dict(body)
    record["comparison_id"] = compute_comparison_id(record)
    return validate_hardening_comparison(record)


def _obligation(comparison_id: str, kind: str, subject: Any) -> dict[str, Any]:
    body = {"comparison_id": comparison_id, "kind": kind, "subject": subject}
    return {"obligation_id": _record_id("HO", OBLIGATION_DOMAIN, body), **body}


def derive_hardening_obligations(comparison: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    checked = validate_hardening_comparison(comparison)
    comparison_id = checked["comparison_id"]
    obligations = [
        _obligation(comparison_id, kind, None)
        for kind in COMMON_OBLIGATION_KINDS
    ]
    gain_kind = (
        "TARGETED_GAIN_OLD_RESULT"
        if checked["gain"]["axis"] == "OLD_RESULT_RESTRICTION"
        else "TARGETED_GAIN_ROLE_FIBER"
    )
    obligations.append(_obligation(comparison_id, gain_kind, checked["gain"]))
    for collection, kind in (
        (checked["protections"]["positives"], "POSITIVE_PRESERVATION"),
        (checked["protections"]["exclusions"], "EXCLUSION_PRESERVATION"),
        (checked["protections"]["consequences"], "CONSEQUENCE_PRESERVATION"),
    ):
        obligations.extend(
            _obligation(comparison_id, kind, item) for item in collection
        )
    obligations.extend(
        _obligation(comparison_id, "CLAUSE_INDEPENDENCE", item)
        for item in checked["necessary_clauses"]
    )
    return tuple(sorted(obligations, key=lambda item: item["obligation_id"]))


def _decision_requirement(kind: str, subject_sha256: str) -> dict[str, str]:
    body = {"decision_kind": kind, "subject_sha256": subject_sha256}
    return {
        "requirement_id": _record_id("HRQ", DECISION_REQUIREMENT_DOMAIN, body),
        **body,
    }


def derive_human_decision_requirements(
    comparison: Mapping[str, Any],
) -> tuple[dict[str, str], ...]:
    checked = validate_hardening_comparison(comparison)
    scope = {
        "declared_purpose": checked["declared_purpose"],
        "signatures": checked["signatures"],
        "role_view": checked["role_view"],
        "model_domain": checked["model_domain"],
    }
    values = {
        "SCOPE_USE_FOR_COMPARISON": domain_digest(SCOPE_DOMAIN, scope),
        "PROTECTION_REGISTRY_FOR_SCOPE": domain_digest(
            PROTECTION_DOMAIN, checked["protections"]
        ),
        "GAIN_RELEVANCE_FOR_SCOPE": domain_digest(GAIN_DOMAIN, checked["gain"]),
        "TYPE_AND_DELTA_CLASSIFICATION": domain_digest(
            DELTA_DOMAIN,
            {
                "translation_delta_ref": checked["translation_delta_ref"],
                "change_inventory": checked["change_inventory"],
            },
        ),
    }
    requirements = [
        _decision_requirement(kind, values[kind]) for kind in DECISION_KINDS
    ]
    if checked["imports"]:
        requirements.append(
            _decision_requirement(
                IMPORT_DECISION_KIND,
                domain_digest(
                    IMPORT_DOMAIN,
                    {
                        "declared_purpose": checked["declared_purpose"],
                        "imports": checked["imports"],
                    },
                ),
            )
        )
    return tuple(sorted(requirements, key=lambda item: item["requirement_id"]))


def _obligation_map(comparison: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        item["obligation_id"]: item
        for item in derive_hardening_obligations(comparison)
    }


def _find_ref(comparison: Mapping[str, Any], record_id: str) -> dict[str, str]:
    candidates: list[dict[str, str]] = []
    for side in ("baseline", "successor"):
        for field in ("snapshot_ref", "review_head_ref", "model_ref", "signature_ref"):
            candidates.append(comparison[side][field])  # type: ignore[index]
    candidates.append(comparison["translation_delta_ref"])  # type: ignore[arg-type]
    candidates.append(comparison["criticism_state"]["snapshot_ref"])  # type: ignore[index]
    domain_ref = comparison["model_domain"]["domain_ref"]  # type: ignore[index]
    if domain_ref is not None:
        candidates.append(domain_ref)
    for field in ("positives", "exclusions", "consequences"):
        candidates.extend(comparison["protections"][field])  # type: ignore[index]
    candidates.extend(comparison["imports"])  # type: ignore[arg-type]
    for item in comparison["necessary_clauses"]:  # type: ignore[assignment]
        candidates.extend((item["clause_ref"], item["defect_witness_ref"]))
    for item in comparison["change_inventory"]:  # type: ignore[assignment]
        for field in ("baseline_ref", "successor_ref"):
            if item[field] is not None:
                candidates.append(item[field])
        candidates.extend(item["transport_refs"])
    matches = [ref for ref in candidates if ref["record_id"] == record_id]
    identities = {_ref_identity(ref) for ref in matches}
    if len(identities) != 1:
        raise RecordError(f"record ID {record_id!r} is absent or resolves ambiguously")
    return matches[0]


def _expected_input_refs(
    comparison: Mapping[str, Any], obligation: Mapping[str, Any]
) -> tuple[dict[str, str], ...]:
    refs: list[dict[str, str]] = [
        comparison["baseline"]["model_ref"],  # type: ignore[index]
        comparison["successor"]["model_ref"],  # type: ignore[index]
    ]
    domain_ref = comparison["model_domain"]["domain_ref"]  # type: ignore[index]
    if domain_ref is not None:
        refs.append(domain_ref)
    kind = obligation["kind"]
    subject = obligation["subject"]
    if kind in {
        "POSITIVE_PRESERVATION",
        "EXCLUSION_PRESERVATION",
        "CONSEQUENCE_PRESERVATION",
    }:
        refs.append(_find_ref(comparison, subject["record_id"]))
    elif kind == "CLAUSE_INDEPENDENCE":
        refs.extend((subject["clause_ref"], subject["defect_witness_ref"]))
    elif kind == "TYPE_DEPENDENCY_PRESERVATION":
        refs.append(comparison["translation_delta_ref"])  # type: ignore[arg-type]
        refs.extend(comparison["imports"])  # type: ignore[arg-type]
    unique = {_ref_identity(ref): ref for ref in refs}
    return tuple(sorted(unique.values(), key=lambda item: item["record_id"]))


def _checker_binding() -> dict[str, str]:
    return {
        "checker_id": "SMF-HARDENING-DECLARATION-PARSER-V1",
        "checker_version": "1",
        "implementation_sha256": "sha256:" + file_digest(Path(__file__)),
    }


def _fiber_map(value: Any, where: str) -> dict[str, set[str]]:
    fibers = _array(value, where)
    result: dict[str, set[str]] = {}
    control_ids: list[str] = []
    for index, raw in enumerate(fibers):
        child = f"{where}[{index}]"
        fiber = _object(raw, child)
        _exact_keys(fiber, {"control_id", "assignments"}, child)
        control = _identifier(fiber["control_id"], f"{child}.control_id")
        assignments = set(
            _canonical_strings(
                fiber["assignments"], f"{child}.assignments", identifiers=True
            )
        )
        control_ids.append(control)
        result[control] = assignments
    if tuple(control_ids) != tuple(sorted(set(control_ids))):
        raise RecordError(f"{where} must use unique lexical control IDs")
    return result


def _scope_pairs(value: Any, where: str, *, nonempty: bool = True) -> bool:
    pairs = _array(value, where)
    if nonempty and not pairs:
        raise RecordError(f"{where} must not be empty")
    subjects: list[str] = []
    equal = True
    for index, raw in enumerate(pairs):
        child = f"{where}[{index}]"
        pair = _object(raw, child)
        _exact_keys(pair, {"subject_id", "baseline_sha256", "successor_sha256"}, child)
        subjects.append(_identifier(pair["subject_id"], f"{child}.subject_id"))
        before = _digest(pair["baseline_sha256"], f"{child}.baseline_sha256")
        after = _digest(pair["successor_sha256"], f"{child}.successor_sha256")
        equal = equal and before == after
    if tuple(subjects) != tuple(sorted(set(subjects))):
        raise RecordError(f"{where} must use unique lexical subject IDs")
    return equal


def _derive_finite_outcome(
    comparison: Mapping[str, Any], obligation: Mapping[str, Any], payload: Any
) -> str:
    body = _object(payload, "evidence.payload")
    def scoped(condition: bool) -> str:
        # V1 parses a caller declaration but has no artifact resolver or model
        # executor. Even a self-described finite domain therefore cannot
        # become mechanical evidence. Evaluate ``condition`` so every payload
        # branch is checked, but never promote the declaration.
        _ = condition
        return "INCONCLUSIVE"

    kind = obligation["kind"]
    expected_payload_type = {
        "OLD_RESULT_NON_BROADENING": "OLD_RESULT_SETS",
        "ROLE_FIBER_NON_BROADENING": "ROLE_FIBERS",
        "TARGETED_GAIN_OLD_RESULT": "OLD_RESULT_SETS",
        "TARGETED_GAIN_ROLE_FIBER": "ROLE_FIBERS",
        "SUCCESSOR_NON_VACUITY": "SUCCESSOR_MODELS",
        "POSITIVE_PRESERVATION": "POSITIVE_PAIR",
        "EXCLUSION_PRESERVATION": "EXCLUSION_PAIR",
        "CONSEQUENCE_PRESERVATION": "CONSEQUENCE_PAIR",
        "SCOPE_PRESERVATION": "SCOPE_PAIRS",
        "CLAUSE_INDEPENDENCE": "CLAUSE_DELETION",
        "TYPE_DEPENDENCY_PRESERVATION": "TYPE_DEPENDENCY_CHECKS",
    }[kind]
    if body.get("payload_type") != expected_payload_type:
        raise RecordError(
            f"{kind} requires payload_type {expected_payload_type}"
        )
    if expected_payload_type == "OLD_RESULT_SETS":
        _exact_keys(body, {"payload_type", "coverage", "baseline_values", "successor_values"}, "evidence.payload")
        if body["coverage"] != "FINITE_EXHAUSTIVE":
            return "INCONCLUSIVE"
        baseline = set(_canonical_strings(body["baseline_values"], "evidence.payload.baseline_values", identifiers=True))
        successor = set(_canonical_strings(body["successor_values"], "evidence.payload.successor_values", identifiers=True))
        if kind == "OLD_RESULT_NON_BROADENING":
            return scoped(successor <= baseline)
        bad = comparison["gain"]["bad_old_result_id"]  # type: ignore[index]
        return scoped(bad in baseline and bad not in successor and successor < baseline)
    if expected_payload_type == "ROLE_FIBERS":
        _exact_keys(body, {"payload_type", "coverage", "baseline_fibers", "successor_fibers"}, "evidence.payload")
        if body["coverage"] != "FINITE_EXHAUSTIVE":
            return "INCONCLUSIVE"
        baseline = _fiber_map(body["baseline_fibers"], "evidence.payload.baseline_fibers")
        successor = _fiber_map(body["successor_fibers"], "evidence.payload.successor_fibers")
        if kind == "ROLE_FIBER_NON_BROADENING":
            controls = set(baseline) | set(successor)
            return scoped(
                all(
                    successor.get(control, set()) <= baseline.get(control, set())
                    for control in controls
                )
            )
        gain = comparison["gain"]  # type: ignore[assignment]
        control = gain["control_base_id"]
        before = baseline.get(control, set())
        after = successor.get(control, set())
        bad = gain["bad_assignment_id"]
        keep = gain["keep_assignment_id"]
        return scoped(
            bad in before
            and keep in before
            and bool(after)
            and after < before
            and bad not in after
            and keep in after
        )
    if expected_payload_type == "SUCCESSOR_MODELS":
        _exact_keys(body, {"payload_type", "successor_model_ids", "retained_positive_ids"}, "evidence.payload")
        models = _canonical_strings(body["successor_model_ids"], "evidence.payload.successor_model_ids", identifiers=True)
        retained = set(_canonical_strings(body["retained_positive_ids"], "evidence.payload.retained_positive_ids", identifiers=True))
        positive_ids = {item["record_id"] for item in comparison["protections"]["positives"]}  # type: ignore[index]
        return scoped(bool(models) and bool(retained & positive_ids))
    if expected_payload_type == "POSITIVE_PAIR":
        _exact_keys(
            body,
            {
                "payload_type",
                "protection_id",
                "baseline_model_id",
                "successor_model_id",
                "baseline_scope_sha256",
                "successor_scope_sha256",
                "baseline_classification_sha256",
                "successor_classification_sha256",
            },
            "evidence.payload",
        )
        subject = obligation["subject"]["record_id"]
        valid = (
            _identifier(body["protection_id"], "evidence.payload.protection_id") == subject
            and bool(_identifier(body["baseline_model_id"], "evidence.payload.baseline_model_id"))
            and bool(_identifier(body["successor_model_id"], "evidence.payload.successor_model_id"))
            and _digest(body["baseline_scope_sha256"], "evidence.payload.baseline_scope_sha256")
            == _digest(body["successor_scope_sha256"], "evidence.payload.successor_scope_sha256")
            and _digest(body["baseline_classification_sha256"], "evidence.payload.baseline_classification_sha256")
            == _digest(body["successor_classification_sha256"], "evidence.payload.successor_classification_sha256")
        )
        return scoped(valid)
    if expected_payload_type == "EXCLUSION_PAIR":
        _exact_keys(
            body,
            {
                "payload_type",
                "protection_id",
                "baseline_context_live",
                "successor_context_live",
                "baseline_excluded",
                "successor_excluded",
                "baseline_scope_sha256",
                "successor_scope_sha256",
            },
            "evidence.payload",
        )
        subject = obligation["subject"]["record_id"]
        valid = (
            _identifier(body["protection_id"], "evidence.payload.protection_id") == subject
            and all(type(body[field]) is bool and body[field] for field in ("baseline_context_live", "successor_context_live", "baseline_excluded", "successor_excluded"))
            and _digest(body["baseline_scope_sha256"], "evidence.payload.baseline_scope_sha256")
            == _digest(body["successor_scope_sha256"], "evidence.payload.successor_scope_sha256")
        )
        return scoped(valid)
    if expected_payload_type == "CONSEQUENCE_PAIR":
        _exact_keys(
            body,
            {
                "payload_type",
                "protection_id",
                "baseline_entailed",
                "successor_entailed",
                "baseline_closure_sha256",
                "successor_closure_sha256",
                "formula_sha256",
            },
            "evidence.payload",
        )
        subject = obligation["subject"]["record_id"]
        valid = (
            _identifier(body["protection_id"], "evidence.payload.protection_id") == subject
            and body["baseline_entailed"] is True
            and body["successor_entailed"] is True
        )
        for field in ("baseline_closure_sha256", "successor_closure_sha256", "formula_sha256"):
            _digest(body[field], f"evidence.payload.{field}")
        return scoped(valid)
    if expected_payload_type == "SCOPE_PAIRS":
        _exact_keys(body, {"payload_type", "scope_pairs"}, "evidence.payload")
        return scoped(_scope_pairs(body["scope_pairs"], "evidence.payload.scope_pairs"))
    if expected_payload_type == "CLAUSE_DELETION":
        _exact_keys(
            body,
            {
                "payload_type",
                "clause_id",
                "defect_witness_id",
                "full_successor_excludes_defect",
                "deleted_clause_readmits_defect",
                "full_scope_sha256",
                "deleted_scope_sha256",
            },
            "evidence.payload",
        )
        subject = obligation["subject"]
        valid = (
            _identifier(body["clause_id"], "evidence.payload.clause_id")
            == subject["clause_ref"]["record_id"]
            and _identifier(body["defect_witness_id"], "evidence.payload.defect_witness_id")
            == subject["defect_witness_ref"]["record_id"]
            and body["full_successor_excludes_defect"] is True
            and body["deleted_clause_readmits_defect"] is True
            and _digest(body["full_scope_sha256"], "evidence.payload.full_scope_sha256")
            == _digest(body["deleted_scope_sha256"], "evidence.payload.deleted_scope_sha256")
        )
        return scoped(valid)
    if expected_payload_type == "TYPE_DEPENDENCY_CHECKS":
        _exact_keys(
            body,
            {
                "payload_type",
                "delta_complete",
                "types_preserved",
                "dependencies_closed",
                "transports_explicit",
            },
            "evidence.payload",
        )
        fields = ("delta_complete", "types_preserved", "dependencies_closed", "transports_explicit")
        if any(type(body[field]) is not bool for field in fields):
            raise RecordError("type/dependency checks must be booleans")
        return scoped(all(body[field] for field in fields))
    raise AssertionError("unreachable evidence payload branch")


def build_hardening_evidence(
    comparison: Mapping[str, Any],
    obligation_id: str,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    checked = validate_hardening_comparison(comparison)
    obligations = _obligation_map(checked)
    _content_id(obligation_id, "HO", "obligation_id")
    if obligation_id not in obligations:
        raise RecordError("evidence targets an obligation outside the comparison")
    obligation = obligations[obligation_id]
    outcome = _derive_finite_outcome(checked, obligation, payload)
    record: dict[str, Any] = {
        "schema_version": EVIDENCE_SCHEMA,
        "record_type": "hardening_evidence",
        "comparison_id": checked["comparison_id"],
        "comparison_sha256": domain_digest(COMPARISON_SCHEMA, checked),
        "obligation_id": obligation_id,
        "evidence_kind": obligation["kind"],
        "checker": _checker_binding(),
        "input_refs": list(_expected_input_refs(checked, obligation)),
        "payload": dict(payload),
        "payload_sha256": domain_digest(
            f"{EVIDENCE_SCHEMA}.payload.{obligation['kind']}", dict(payload)
        ),
        "outcome": outcome,
        "epistemic_effect": "DECLARED_PAYLOAD_ONLY",
        "semantic_verdict": None,
        "epistemic_limit": NON_INDUCTIVE_LIMIT,
    }
    record["evidence_id"] = compute_evidence_id(record)
    return validate_hardening_evidence(record, checked)


def validate_hardening_evidence(
    value: Any, comparison: Mapping[str, Any]
) -> dict[str, Any]:
    evidence = _object(value, "evidence")
    _exact_keys(
        evidence,
        {
            "schema_version",
            "record_type",
            "evidence_id",
            "comparison_id",
            "comparison_sha256",
            "obligation_id",
            "evidence_kind",
            "checker",
            "input_refs",
            "payload",
            "payload_sha256",
            "outcome",
            "epistemic_effect",
            "semantic_verdict",
            "epistemic_limit",
        },
        "evidence",
    )
    checked = validate_hardening_comparison(comparison)
    if evidence["schema_version"] != EVIDENCE_SCHEMA or evidence["record_type"] != "hardening_evidence":
        raise RecordError("unsupported hardening evidence record")
    if evidence["evidence_id"] != compute_evidence_id(evidence):
        raise RecordError("hardening evidence content-addressed ID mismatch")
    if evidence["comparison_id"] != checked["comparison_id"] or evidence["comparison_sha256"] != domain_digest(COMPARISON_SCHEMA, checked):
        raise PolicyViolation("hardening evidence changed its comparison binding")
    obligations = _obligation_map(checked)
    obligation_id = _content_id(evidence["obligation_id"], "HO", "evidence.obligation_id")
    if obligation_id not in obligations:
        raise PolicyViolation("hardening evidence targets an unknown obligation")
    obligation = obligations[obligation_id]
    if evidence["evidence_kind"] != obligation["kind"]:
        raise PolicyViolation("hardening evidence kind does not match its obligation")
    checker = _object(evidence["checker"], "evidence.checker")
    _exact_keys(checker, {"checker_id", "checker_version", "implementation_sha256"}, "evidence.checker")
    if checker != _checker_binding():
        raise PolicyViolation("hardening evidence checker is unavailable or has changed")
    refs = _canonical_refs(evidence["input_refs"], "evidence.input_refs", nonempty=True)
    if tuple(_ref_identity(item) for item in refs) != tuple(
        _ref_identity(item) for item in _expected_input_refs(checked, obligation)
    ):
        raise PolicyViolation("hardening evidence input bindings are incomplete or changed")
    payload = _object(evidence["payload"], "evidence.payload")
    expected_payload_digest = domain_digest(
        f"{EVIDENCE_SCHEMA}.payload.{obligation['kind']}", payload
    )
    if evidence["payload_sha256"] != expected_payload_digest:
        raise RecordError("hardening evidence payload digest mismatch")
    outcome = _derive_finite_outcome(checked, obligation, payload)
    if evidence["outcome"] != outcome or outcome not in EVIDENCE_OUTCOMES:
        raise PolicyViolation("hardening evidence outcome does not replay")
    if (
        evidence["epistemic_effect"] != "DECLARED_PAYLOAD_ONLY"
        or evidence["semantic_verdict"] is not None
    ):
        raise PolicyViolation("declared hardening payload claimed a semantic effect")
    if evidence["epistemic_limit"] != NON_INDUCTIVE_LIMIT:
        raise PolicyViolation("hardening evidence weakens the non-inductive limit")
    return evidence


def build_hardening_decision(
    comparison: Mapping[str, Any],
    requirement_id: str,
    *,
    disposition: str,
    reason: str,
    created_on: str,
    decision_sequence: int = 1,
    previous_decision_id: str | None = None,
    considered_evidence: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    checked = validate_hardening_comparison(comparison)
    requirements = {
        item["requirement_id"]: item
        for item in derive_human_decision_requirements(checked)
    }
    _content_id(requirement_id, "HRQ", "requirement_id")
    if requirement_id not in requirements:
        raise RecordError("decision targets a requirement outside the comparison")
    evidence_refs = []
    for item in considered_evidence:
        evidence = validate_hardening_evidence(item, checked)
        evidence_refs.append(
            {
                "evidence_id": evidence["evidence_id"],
                "evidence_sha256": domain_digest(EVIDENCE_SCHEMA, evidence),
            }
        )
    evidence_refs.sort(key=lambda item: item["evidence_id"])
    requirement = requirements[requirement_id]
    record: dict[str, Any] = {
        "schema_version": DECISION_SCHEMA,
        "record_type": "hardening_human_decision",
        "comparison_id": checked["comparison_id"],
        "comparison_sha256": domain_digest(COMPARISON_SCHEMA, checked),
        "requirement_id": requirement_id,
        "decision_kind": requirement["decision_kind"],
        "subject_sha256": requirement["subject_sha256"],
        "decision_sequence": decision_sequence,
        "previous_decision_id": previous_decision_id,
        "disposition": disposition,
        "considered_evidence": evidence_refs,
        "reason": reason,
        "created_on": created_on,
        "human_judgment_is_fallible": True,
        "reviewer_authentication": "NOT_ESTABLISHED_BY_RECORD",
        "can_supply_mechanical_evidence": False,
        "can_promote_source_authority": False,
        "semantic_verdict": None,
        "epistemic_limit": NON_INDUCTIVE_LIMIT,
    }
    record["decision_id"] = compute_decision_id(record)
    return validate_hardening_decision(record, checked, considered_evidence)


def validate_hardening_decision(
    value: Any,
    comparison: Mapping[str, Any],
    evidence_records: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    decision = _object(value, "decision")
    _exact_keys(
        decision,
        {
            "schema_version",
            "record_type",
            "decision_id",
            "comparison_id",
            "comparison_sha256",
            "requirement_id",
            "decision_kind",
            "subject_sha256",
            "decision_sequence",
            "previous_decision_id",
            "disposition",
            "considered_evidence",
            "reason",
            "created_on",
            "human_judgment_is_fallible",
            "reviewer_authentication",
            "can_supply_mechanical_evidence",
            "can_promote_source_authority",
            "semantic_verdict",
            "epistemic_limit",
        },
        "decision",
    )
    checked = validate_hardening_comparison(comparison)
    if decision["schema_version"] != DECISION_SCHEMA or decision["record_type"] != "hardening_human_decision":
        raise RecordError("unsupported hardening decision record")
    if decision["decision_id"] != compute_decision_id(decision):
        raise RecordError("hardening decision content-addressed ID mismatch")
    if decision["comparison_id"] != checked["comparison_id"] or decision["comparison_sha256"] != domain_digest(COMPARISON_SCHEMA, checked):
        raise PolicyViolation("hardening decision changed its comparison binding")
    requirements = {
        item["requirement_id"]: item
        for item in derive_human_decision_requirements(checked)
    }
    requirement_id = _content_id(decision["requirement_id"], "HRQ", "decision.requirement_id")
    requirement = requirements.get(requirement_id)
    if requirement is None:
        raise PolicyViolation("hardening decision targets an unknown requirement")
    if decision["decision_kind"] != requirement["decision_kind"] or decision["subject_sha256"] != requirement["subject_sha256"]:
        raise PolicyViolation("hardening decision changed its derived question or subject")
    sequence = decision["decision_sequence"]
    if type(sequence) is not int or sequence < 1:
        raise RecordError("hardening decision sequence must be a positive integer")
    previous = decision["previous_decision_id"]
    if previous is not None:
        _content_id(previous, "HD", "decision.previous_decision_id")
    if (sequence == 1) != (previous is None):
        raise RecordError("hardening decision genesis/predecessor shape is inconsistent")
    if decision["disposition"] not in DECISION_DISPOSITIONS:
        raise RecordError("hardening decision disposition is unsupported")
    _string(decision["reason"], "decision.reason")
    try:
        parsed_date = date.fromisoformat(_string(decision["created_on"], "decision.created_on"))
    except ValueError as exc:
        raise RecordError("decision.created_on must use canonical YYYY-MM-DD form") from exc
    if parsed_date.isoformat() != decision["created_on"]:
        raise RecordError("decision.created_on must use canonical YYYY-MM-DD form")

    known_evidence: dict[str, Mapping[str, Any]] = {}
    for item in evidence_records:
        evidence = validate_hardening_evidence(item, checked)
        if evidence["evidence_id"] in known_evidence:
            raise RecordError("duplicate hardening evidence ID")
        known_evidence[evidence["evidence_id"]] = evidence
    refs = _array(decision["considered_evidence"], "decision.considered_evidence")
    ref_ids: list[str] = []
    for index, raw in enumerate(refs):
        where = f"decision.considered_evidence[{index}]"
        ref = _object(raw, where)
        _exact_keys(ref, {"evidence_id", "evidence_sha256"}, where)
        evidence_id = _content_id(ref["evidence_id"], "HE", f"{where}.evidence_id")
        _digest(ref["evidence_sha256"], f"{where}.evidence_sha256")
        if evidence_id not in known_evidence:
            raise PolicyViolation("decision considered evidence absent from the supplied inventory")
        if ref["evidence_sha256"] != domain_digest(EVIDENCE_SCHEMA, known_evidence[evidence_id]):
            raise PolicyViolation("decision considered evidence with changed bytes")
        ref_ids.append(evidence_id)
    if tuple(ref_ids) != tuple(sorted(set(ref_ids))):
        raise RecordError("decision.considered_evidence must use unique lexical evidence IDs")
    if (
        decision["human_judgment_is_fallible"] is not True
        or decision["reviewer_authentication"] != "NOT_ESTABLISHED_BY_RECORD"
        or decision["can_supply_mechanical_evidence"] is not False
        or decision["can_promote_source_authority"] is not False
        or decision["semantic_verdict"] is not None
    ):
        raise PolicyViolation("hardening human decision changed its authority boundary")
    if decision["epistemic_limit"] != NON_INDUCTIVE_LIMIT:
        raise PolicyViolation("hardening decision weakens the non-inductive limit")
    return decision


def _terminal_decisions(
    comparison: Mapping[str, Any],
    decisions: Sequence[Mapping[str, Any]],
    evidence: Sequence[Mapping[str, Any]],
) -> dict[str, Mapping[str, Any]]:
    requirements = {
        item["requirement_id"]: item
        for item in derive_human_decision_requirements(comparison)
    }
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    seen: set[str] = set()
    for raw in decisions:
        decision = validate_hardening_decision(raw, comparison, evidence)
        decision_id = decision["decision_id"]
        if decision_id in seen:
            raise RecordError("duplicate hardening decision ID")
        seen.add(decision_id)
        grouped[decision["requirement_id"]].append(decision)
    terminals: dict[str, Mapping[str, Any]] = {}
    for requirement_id, records in grouped.items():
        if requirement_id not in requirements:
            raise PolicyViolation("decision lineage targets an unknown requirement")
        ordered = sorted(records, key=lambda item: item["decision_sequence"])
        for index, current in enumerate(ordered):
            expected_sequence = index + 1
            expected_previous = None if index == 0 else ordered[index - 1]["decision_id"]
            if current["decision_sequence"] != expected_sequence or current["previous_decision_id"] != expected_previous:
                raise PolicyViolation("hardening decision lineage is forked, gapped, or mislinked")
        terminals[requirement_id] = ordered[-1]
    return terminals


def resolve_hardening_comparison(
    comparison: Mapping[str, Any],
    evidence_records: Sequence[Mapping[str, Any]],
    decision_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    checked = validate_hardening_comparison(comparison)
    obligations = derive_hardening_obligations(checked)
    evidence_by_obligation: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    seen_evidence: set[str] = set()
    validated_evidence: list[Mapping[str, Any]] = []
    for raw in evidence_records:
        evidence = validate_hardening_evidence(raw, checked)
        evidence_id = evidence["evidence_id"]
        if evidence_id in seen_evidence:
            raise RecordError("duplicate hardening evidence ID")
        seen_evidence.add(evidence_id)
        validated_evidence.append(evidence)
        evidence_by_obligation[evidence["obligation_id"]].append(evidence)

    obligation_states: list[dict[str, Any]] = []
    has_counterwitness = False
    has_unresolved_obligation = False
    for obligation in obligations:
        records = evidence_by_obligation.get(obligation["obligation_id"], [])
        outcomes = {item["outcome"] for item in records}
        if "COUNTERWITNESSED" in outcomes:
            state = "COUNTERWITNESSED"
            has_counterwitness = True
        elif "WITNESSED" in outcomes:
            state = "WITNESSED"
        elif records:
            state = "INCONCLUSIVE"
            has_unresolved_obligation = True
        else:
            state = "MISSING"
            has_unresolved_obligation = True
        obligation_states.append(
            {
                "obligation_id": obligation["obligation_id"],
                "kind": obligation["kind"],
                "state": state,
                "evidence_ids": sorted(item["evidence_id"] for item in records),
            }
        )

    terminals = _terminal_decisions(checked, decision_records, validated_evidence)
    requirements = derive_human_decision_requirements(checked)
    decision_states: list[dict[str, Any]] = []
    has_defeat_decision = False
    has_unresolved_decision = False
    for requirement in requirements:
        terminal = terminals.get(requirement["requirement_id"])
        if terminal is None:
            state = "MISSING"
            decision_id = None
            has_unresolved_decision = True
        else:
            state = terminal["disposition"]
            decision_id = terminal["decision_id"]
            if state == "DEFEATS_HARDENING":
                has_defeat_decision = True
            elif state != "ACCEPT_FOR_DECLARED_SCOPE":
                has_unresolved_decision = True
        decision_states.append(
            {
                "requirement_id": requirement["requirement_id"],
                "decision_kind": requirement["decision_kind"],
                "state": state,
                "decision_id": decision_id,
            }
        )

    live = list(checked["criticism_state"]["effective_live_criticism_ids"])
    reason_codes: set[str] = set()
    if has_counterwitness:
        reason_codes.add("MECHANICAL_COUNTERWITNESS")
    if has_defeat_decision:
        reason_codes.add("HUMAN_RECORDED_DEFEAT")
    if has_unresolved_obligation:
        reason_codes.add("MECHANICAL_OBLIGATION_OPEN")
    if has_unresolved_decision:
        reason_codes.add("HUMAN_DECISION_OPEN")
    if live:
        reason_codes.add("EFFECTIVE_LIVE_CRITICISM")
    if checked["execution_semantics"] == "NONE_V1":
        reason_codes.add("EXECUTION_SEMANTICS_UNAVAILABLE")
    if checked["execution_semantics"] == "PROOF_CERTIFIED_V1":
        reason_codes.add("PROOF_CHECKER_UNAVAILABLE_V1")
    if checked["execution_semantics"] == "FINITE_EXHAUSTIVE_V1":
        reason_codes.add("BOUND_ARTIFACT_REPLAY_UNAVAILABLE_V1")

    if has_counterwitness or has_defeat_decision:
        status = "NO_HARDENING"
    elif has_unresolved_obligation or has_unresolved_decision or live:
        status = "UNRESOLVED"
    else:
        status = "HARDENING_UNREFUTED"
    if status not in HARDENING_STATUSES:
        raise AssertionError("unreachable hardening status")

    evidence_inventory = sorted(validated_evidence, key=lambda item: item["evidence_id"])
    decision_inventory = sorted(
        (validate_hardening_decision(item, checked, validated_evidence) for item in decision_records),
        key=lambda item: item["decision_id"],
    )
    record: dict[str, Any] = {
        "schema_version": RESOLUTION_SCHEMA,
        "record_type": "hardening_resolution",
        "comparison_id": checked["comparison_id"],
        "comparison_sha256": domain_digest(COMPARISON_SCHEMA, checked),
        "status": status,
        "obligations": obligation_states,
        "human_requirements": decision_states,
        "effective_live_criticism_ids": live,
        "reason_codes": sorted(reason_codes),
        "evidence_inventory_sha256": domain_digest(
            EVIDENCE_INVENTORY_DOMAIN, evidence_inventory
        ),
        "decision_inventory_sha256": domain_digest(
            DECISION_INVENTORY_DOMAIN, decision_inventory
        ),
        "result_scope": "DECLARED_COMPARISON_ONLY",
        "final": False,
        "semantic_verdict": None,
        "epistemic_limit": NON_INDUCTIVE_LIMIT,
    }
    record["resolution_id"] = compute_resolution_id(record)
    return _validate_hardening_resolution_intrinsic(record, checked)


def _validate_hardening_resolution_intrinsic(
    value: Any, comparison: Mapping[str, Any]
) -> dict[str, Any]:
    resolution = _object(value, "resolution")
    _exact_keys(
        resolution,
        {
            "schema_version",
            "record_type",
            "resolution_id",
            "comparison_id",
            "comparison_sha256",
            "status",
            "obligations",
            "human_requirements",
            "effective_live_criticism_ids",
            "reason_codes",
            "evidence_inventory_sha256",
            "decision_inventory_sha256",
            "result_scope",
            "final",
            "semantic_verdict",
            "epistemic_limit",
        },
        "resolution",
    )
    checked = validate_hardening_comparison(comparison)
    if resolution["schema_version"] != RESOLUTION_SCHEMA or resolution["record_type"] != "hardening_resolution":
        raise RecordError("unsupported hardening resolution record")
    if resolution["resolution_id"] != compute_resolution_id(resolution):
        raise RecordError("hardening resolution content-addressed ID mismatch")
    if resolution["comparison_id"] != checked["comparison_id"] or resolution["comparison_sha256"] != domain_digest(COMPARISON_SCHEMA, checked):
        raise PolicyViolation("hardening resolution changed its comparison binding")
    if resolution["status"] not in HARDENING_STATUSES:
        raise RecordError("hardening resolution status is unsupported")
    obligation_rows = _array(resolution["obligations"], "resolution.obligations")
    expected_obligations = derive_hardening_obligations(checked)
    if [row.get("obligation_id") for row in obligation_rows if type(row) is dict] != [item["obligation_id"] for item in expected_obligations]:
        raise PolicyViolation("hardening resolution changed its obligation inventory")
    for index, raw in enumerate(obligation_rows):
        where = f"resolution.obligations[{index}]"
        row = _object(raw, where)
        _exact_keys(row, {"obligation_id", "kind", "state", "evidence_ids"}, where)
        if row["kind"] != expected_obligations[index]["kind"]:
            raise PolicyViolation("hardening resolution changed an obligation kind")
        if row["state"] not in EVIDENCE_OUTCOMES | {"MISSING"}:
            raise RecordError(f"{where}.state is unsupported")
        _canonical_strings(row["evidence_ids"], f"{where}.evidence_ids")
    human_rows = _array(resolution["human_requirements"], "resolution.human_requirements")
    expected_requirements = derive_human_decision_requirements(checked)
    if [row.get("requirement_id") for row in human_rows if type(row) is dict] != [item["requirement_id"] for item in expected_requirements]:
        raise PolicyViolation("hardening resolution changed its decision inventory")
    for index, raw in enumerate(human_rows):
        where = f"resolution.human_requirements[{index}]"
        row = _object(raw, where)
        _exact_keys(row, {"requirement_id", "decision_kind", "state", "decision_id"}, where)
        if row["decision_kind"] != expected_requirements[index]["decision_kind"]:
            raise PolicyViolation("hardening resolution changed a decision kind")
        if row["state"] not in DECISION_DISPOSITIONS | {"MISSING"}:
            raise RecordError(f"{where}.state is unsupported")
        if row["decision_id"] is not None:
            _content_id(row["decision_id"], "HD", f"{where}.decision_id")
    _canonical_strings(
        resolution["effective_live_criticism_ids"],
        "resolution.effective_live_criticism_ids",
        identifiers=True,
    )
    _canonical_strings(resolution["reason_codes"], "resolution.reason_codes", identifiers=True)
    _digest(resolution["evidence_inventory_sha256"], "resolution.evidence_inventory_sha256")
    _digest(resolution["decision_inventory_sha256"], "resolution.decision_inventory_sha256")
    if (
        resolution["result_scope"] != "DECLARED_COMPARISON_ONLY"
        or resolution["final"] is not False
        or resolution["semantic_verdict"] is not None
    ):
        raise PolicyViolation("hardening resolution exceeded its declared scope")
    if resolution["epistemic_limit"] != NON_INDUCTIVE_LIMIT:
        raise PolicyViolation("hardening resolution weakens the non-inductive limit")
    return resolution


def validate_hardening_resolution(
    value: Any,
    comparison: Mapping[str, Any],
    evidence_records: Sequence[Mapping[str, Any]],
    decision_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Validate a resolution only by replaying its exact input inventories.

    A content-addressed resolution is still merely an assertion unless its row
    states, terminal human decisions, inventory digests and reason codes are
    deterministically re-derived.  Callers therefore cannot validate a
    resolution in isolation.
    """

    checked = _validate_hardening_resolution_intrinsic(value, comparison)
    derived = resolve_hardening_comparison(
        comparison,
        evidence_records,
        decision_records,
    )
    if checked != derived:
        raise PolicyViolation(
            "hardening resolution differs from exact evidence and decision replay"
        )
    return checked


def publish_content_addressed_record(record: Mapping[str, Any], destination: Path) -> Path:
    """Publish canonical JSON plus one newline without replacing prior bytes."""

    if not isinstance(destination, Path):
        raise TypeError("destination must be pathlib.Path")
    payload = canonical_bytes(dict(record)) + b"\n"
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError:
        try:
            existing = destination.read_bytes()
        except OSError as exc:
            raise RecordError(f"cannot inspect existing hardening record: {exc}") from exc
        if existing != payload:
            raise RecordError("hardening record path already contains different bytes")
        return destination
    try:
        descriptor = os.open(destination.parent, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    except OSError as exc:
        raise RecordError(f"cannot durably publish hardening record: {exc}") from exc
    return destination


def load_canonical_record(path: Path) -> dict[str, Any]:
    """Strict-load one canonical hardening record without schema dispatch."""

    from creib.strict_json import loads_strict

    try:
        raw = path.read_bytes()
        value = loads_strict(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, RecordError) as exc:
        raise RecordError(f"cannot load hardening record {path}: {exc}") from exc
    record = _object(value, str(path))
    if raw != canonical_bytes(record) + b"\n":
        raise RecordError(f"hardening record {path} is not canonical JSON plus one newline")
    return record
