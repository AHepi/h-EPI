"""Generic, formalism-independent semantic translation records.

The records in this module describe a proposed path from exact source bytes to
a neutral semantic model.  They deliberately contain no Lean, SMT, proof, or
truth status.  Validation establishes record integrity and traceability only;
it never establishes that a proposed interpretation is faithful.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from functools import cache
import re
import unicodedata
from pathlib import Path
from typing import Any, Iterable, Mapping

from creib.canonical import bytes_digest, canonical_bytes, domain_digest
from creib.errors import PolicyViolation, RecordError
from creib.strict_json import loads_strict


TRANSLATION_SCHEMA_TO_ID: Mapping[str, tuple[str, str]] = {
    "creib.semantic-forge.translation-source-document.v1": ("TDOC", "document_id"),
    "creib.semantic-forge.translation-source-span.v1": ("TSPAN", "span_id"),
    "creib.semantic-forge.translation-charter.v1": ("TCHAR", "charter_id"),
    "creib.semantic-forge.translation-obligation-graph.v1": ("TOG", "graph_id"),
    "creib.semantic-forge.translation-interpretation-set.v1": (
        "TIS",
        "interpretation_set_id",
    ),
    "creib.semantic-forge.translation-neutral-signature.v1": (
        "TNS",
        "signature_id",
    ),
    "creib.semantic-forge.translation-neutral-model.v1": ("TNM", "model_id"),
    "creib.semantic-forge.translation-project-import.v1": ("TIMP", "import_id"),
    "creib.semantic-forge.translation-two-way-bridge.v1": ("TBR", "bridge_id"),
    "creib.semantic-forge.translation-snapshot.v1": ("TSN", "snapshot_id"),
}

TRANSLATION_SCHEMA_TO_FILE: Mapping[str, str] = {
    schema: name
    for schema, name in {
        "creib.semantic-forge.translation-source-document.v1": "translation-source-document.schema.json",
        "creib.semantic-forge.translation-source-span.v1": "translation-source-span.schema.json",
        "creib.semantic-forge.translation-charter.v1": "translation-charter.schema.json",
        "creib.semantic-forge.translation-obligation-graph.v1": "translation-obligation-graph.schema.json",
        "creib.semantic-forge.translation-interpretation-set.v1": "translation-interpretation-set.schema.json",
        "creib.semantic-forge.translation-neutral-signature.v1": "translation-neutral-signature.schema.json",
        "creib.semantic-forge.translation-neutral-model.v1": "translation-neutral-model.schema.json",
        "creib.semantic-forge.translation-project-import.v1": "translation-project-import.schema.json",
        "creib.semantic-forge.translation-two-way-bridge.v1": "translation-two-way-bridge.schema.json",
        "creib.semantic-forge.translation-snapshot.v1": "translation-snapshot.schema.json",
    }.items()
}


@cache
def _translation_schema_catalog():
    """Return the checked local schema catalog without creating an import cycle."""

    from .schema_validation import load_local_schema_catalog

    return load_local_schema_catalog()


def _validate_translation_schema_shape(record: Mapping[str, Any]) -> None:
    """Apply the closed JSON Schema before any cross-record reasoning.

    ``validate_translation_record`` intentionally implements the intrinsic
    invariants that JSON Schema cannot express.  Entry points which accept
    external records call this companion check as well, so an otherwise
    content-addressed record cannot smuggle in an extra claim or enum value.
    """

    schema = record.get("schema_version")
    if type(schema) is not str or schema not in TRANSLATION_SCHEMA_TO_FILE:
        raise RecordError("unknown generic translation schema version")
    _translation_schema_catalog().validate(
        dict(record), TRANSLATION_SCHEMA_TO_FILE[schema]
    )

TRANSLATION_COMPONENT_ID_SPECS: Mapping[str, tuple[str, str, str]] = {
    "protected_distinction": (
        "TPD",
        "creib.semantic-forge.translation-protected-distinction.v1",
        "distinction_id",
    ),
    "source_claim": (
        "TSC",
        "creib.semantic-forge.translation-source-claim.v1",
        "claim_id",
    ),
    "protected_feature": (
        "TPF",
        "creib.semantic-forge.translation-protected-feature.v1",
        "feature_id",
    ),
    "translation_duty": (
        "TDUT",
        "creib.semantic-forge.translation-duty.v1",
        "duty_id",
    ),
    "obligation": (
        "TO",
        "creib.semantic-forge.translation-obligation.v1",
        "obligation_id",
    ),
    "obligation_edge": (
        "TOE",
        "creib.semantic-forge.translation-obligation-edge.v1",
        "edge_id",
    ),
    "interpretation": (
        "TI",
        "creib.semantic-forge.translation-interpretation.v1",
        "interpretation_id",
    ),
    "signature_member": (
        "TNSM",
        "creib.semantic-forge.translation-signature-member.v1",
        "member_id",
    ),
    "model_clause": (
        "TNMC",
        "creib.semantic-forge.translation-model-clause.v1",
        "clause_id",
    ),
    "model_open_port": (
        "TNMP",
        "creib.semantic-forge.translation-model-open-port.v1",
        "port_id",
    ),
    "forward_mapping": (
        "TFM",
        "creib.semantic-forge.translation-forward-mapping.v1",
        "mapping_id",
    ),
    "reverse_mapping": (
        "TRM",
        "creib.semantic-forge.translation-reverse-mapping.v1",
        "mapping_id",
    ),
    "translation_delta": (
        "TDL",
        "creib.semantic-forge.translation-mapping-delta.v1",
        "delta_id",
    ),
}

SEMANTIC_DEPENDENCY_CLOSURE_DOMAIN = (
    "creib.semantic-forge.translation-semantic-dependency-closure.v1"
)
THEORY_RECORD_DOMAIN = "creib.semantic-forge.translation-theory-record.v1"

NON_INDUCTIVE_TRANSLATION_LIMIT = (
    "Operational integrity and recorded review do not confirm a translation; "
    "every interpretation remains open to criticism."
)

_HEX = re.compile(r"^[0-9a-f]{64}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_DOMAIN_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
_RFC3339_TIMESTAMP = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]+)?(?:Z|[+-][0-9]{2}:[0-9]{2})$"
)
_STABLE_ID = re.compile(r"^[A-Za-z][A-Za-z0-9._:-]{0,127}$")

_FIXED_POLICIES: Mapping[str, object] = {
    "formalism_can_override_valid_prose": False,
    "test_survival_effect": "UNREFUTED_ONLY",
    "research_role": "CRITICISM_DISCOVERY_ONLY",
    "ambiguity_policy": "PRESERVE_RIVALS",
    "missing_mapping_policy": "OPEN_LOSS",
    "conflict_policy": "PRESERVE_CONFLICT_FOR_REVIEW",
    "human_semantic_decision_required": True,
}

_FORBIDDEN_SEMANTIC_KEYS = frozenset(
    {
        "confidence",
        "probability",
        "support_score",
        "confirmation_score",
        "consensus_score",
        "truth_score",
    }
)


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
    if unicodedata.normalize("NFC", value) != value:
        raise RecordError(f"{where} must be NFC-normalized")
    if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
        raise RecordError(f"{where} contains a Unicode surrogate")
    return value


def _nullable_string(value: Any, where: str) -> str | None:
    if value is None:
        return None
    return _string(value, where)


def _nullable_nfc_text(value: Any, where: str) -> str | None:
    if value is None:
        return None
    if type(value) is not str:
        raise RecordError(f"{where} must be a string or null")
    if unicodedata.normalize("NFC", value) != value:
        raise RecordError(f"{where} must be NFC-normalized")
    if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
        raise RecordError(f"{where} contains a Unicode surrogate")
    return value


def _integer(value: Any, where: str, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise RecordError(f"{where} must be an integer >= {minimum}")
    return value


def _stable_identifier(value: Any, where: str) -> str:
    text = _string(value, where)
    if not _STABLE_ID.fullmatch(text):
        raise RecordError(f"{where} must be a stable identifier")
    return text


def _string_set(value: Any, where: str, *, nonempty: bool = False) -> tuple[str, ...]:
    items = tuple(_string(item, f"{where}[{index}]") for index, item in enumerate(_array(value, where)))
    if nonempty and not items:
        raise RecordError(f"{where} must not be empty")
    if len(items) != len(set(items)):
        raise RecordError(f"{where} must not contain duplicates")
    if items != tuple(sorted(items)):
        raise RecordError(f"{where} must be in canonical lexical order")
    return items


def _canonical_branch_sets(value: Any, where: str) -> tuple[tuple[str, ...], ...]:
    raw_sets = _array(value, where)
    combinations = tuple(
        _string_set(raw, f"{where}[{index}]", nonempty=True)
        for index, raw in enumerate(raw_sets)
    )
    encoded = tuple(canonical_bytes(list(item)) for item in combinations)
    if len(encoded) != len(set(encoded)):
        raise RecordError(f"{where} must not contain duplicate branch sets")
    if encoded != tuple(sorted(encoded)):
        raise RecordError(f"{where} must use canonical branch-set order")
    return combinations


def _reject_forbidden_keys(value: Any, where: str = "$") -> None:
    if type(value) is dict:
        present = sorted(_FORBIDDEN_SEMANTIC_KEYS.intersection(value))
        if present:
            raise PolicyViolation(
                f"{where} contains forbidden semantic scoring field(s): "
                + ", ".join(present)
            )
        for key, item in value.items():
            _string(key, f"{where} key")
            _reject_forbidden_keys(item, f"{where}.{key}")
    elif type(value) is list:
        for index, item in enumerate(value):
            _reject_forbidden_keys(item, f"{where}[{index}]")
    elif type(value) is str:
        _string(value, where)


def _without(record: Mapping[str, Any], key: str) -> dict[str, Any]:
    return {name: value for name, value in record.items() if name != key}


def compute_translation_record_id(record: Mapping[str, Any]) -> str:
    """Compute the domain-separated ID for one top-level translation record."""

    if not isinstance(record, Mapping):
        raise TypeError("record must be a mapping")
    schema = record.get("schema_version")
    if type(schema) is not str or schema not in TRANSLATION_SCHEMA_TO_ID:
        raise RecordError("unknown generic translation schema version")
    prefix, id_field = TRANSLATION_SCHEMA_TO_ID[schema]
    digest = domain_digest(f"{schema}.record-id", _without(record, id_field))
    return f"{prefix}:{digest.removeprefix('sha256:')}"


def translation_record_digest(record: Mapping[str, Any]) -> str:
    """Digest a complete record for exact closure binding."""

    schema = record.get("schema_version")
    if type(schema) is not str or schema not in TRANSLATION_SCHEMA_TO_ID:
        raise RecordError("unknown generic translation schema version")
    return domain_digest(f"{schema}.complete-record", dict(record))


def compute_translation_component_id(
    prefix: str,
    domain: str,
    value: Mapping[str, Any],
    *,
    id_field: str,
) -> str:
    """Compute an ID for a nested immutable component."""

    if not prefix.isalpha() or prefix.upper() != prefix:
        raise ValueError("component prefix must be uppercase ASCII letters")
    _string(domain, "component domain")
    digest = domain_digest(domain, _without(value, id_field))
    return f"{prefix}:{digest.removeprefix('sha256:')}"


def compute_named_translation_component_id(
    component_kind: str,
    value: Mapping[str, Any],
) -> str:
    """Compute the canonical content ID for a named nested component."""

    try:
        prefix, domain, id_field = TRANSLATION_COMPONENT_ID_SPECS[component_kind]
    except KeyError as exc:
        raise RecordError(f"unknown translation component kind: {component_kind}") from exc
    return compute_translation_component_id(
        prefix,
        domain,
        value,
        id_field=id_field,
    )


def compute_semantic_dependency_closure_sha256(
    closure: Mapping[str, Any],
) -> str:
    """Digest a neutral model dependency closure without its digest field."""

    if not isinstance(closure, Mapping):
        raise TypeError("closure must be a mapping")
    return domain_digest(
        SEMANTIC_DEPENDENCY_CLOSURE_DOMAIN,
        _without(closure, "closure_sha256"),
    )


def compute_theory_record_sha256(projection: Mapping[str, Any]) -> str:
    """Digest the declared, non-executable theory projection."""

    if not isinstance(projection, Mapping):
        raise TypeError("projection must be a mapping")
    return domain_digest(
        THEORY_RECORD_DOMAIN,
        _without(projection, "theory_record_sha256"),
    )


def _validate_component_id(component_kind: str, value: Mapping[str, Any]) -> str:
    try:
        prefix, _domain, id_field = TRANSLATION_COMPONENT_ID_SPECS[component_kind]
    except KeyError as exc:
        raise RecordError(f"unknown translation component kind: {component_kind}") from exc
    actual = _string(value.get(id_field), f"{component_kind}.{id_field}")
    if not re.fullmatch(rf"{prefix}:[0-9a-f]{{64}}", actual):
        raise RecordError(
            f"{component_kind}.{id_field} must use the {prefix}: content-addressed namespace"
        )
    expected = compute_named_translation_component_id(component_kind, value)
    if actual != expected:
        raise RecordError(f"{component_kind}.{id_field} content-addressed ID mismatch")
    return actual


def validate_translation_record_id(record: Mapping[str, Any]) -> str:
    schema = record.get("schema_version")
    if type(schema) is not str or schema not in TRANSLATION_SCHEMA_TO_ID:
        raise RecordError("unknown generic translation schema version")
    prefix, id_field = TRANSLATION_SCHEMA_TO_ID[schema]
    actual = _string(record.get(id_field), id_field)
    if not re.fullmatch(rf"{prefix}:[0-9a-f]{{64}}", actual):
        raise RecordError(f"{id_field} must use the {prefix}: content-addressed namespace")
    expected = compute_translation_record_id(record)
    if actual != expected:
        raise RecordError(f"{id_field} does not match the canonical record content")
    return actual


def _content_id(value: Any, prefix: str, where: str) -> str:
    text = _string(value, where)
    if not re.fullmatch(rf"{prefix}:[0-9a-f]{{64}}", text):
        raise RecordError(f"{where} must use the {prefix}: content-addressed namespace")
    return text


def _sorted_objects(
    value: Any,
    where: str,
    *,
    key: str,
    nonempty: bool = False,
) -> list[dict[str, Any]]:
    raw_items = _array(value, where)
    if nonempty and not raw_items:
        raise RecordError(f"{where} must not be empty")
    items = [_object(item, f"{where}[{index}]") for index, item in enumerate(raw_items)]
    keys = tuple(_string(item.get(key), f"{where}[{index}].{key}") for index, item in enumerate(items))
    if len(keys) != len(set(keys)):
        raise RecordError(f"{where} must not repeat {key}")
    if keys != tuple(sorted(keys)):
        raise RecordError(f"{where} must be ordered by {key}")
    return items


def _validate_provenance(record: Mapping[str, Any]) -> None:
    provenance = _object(record.get("provenance"), "provenance")
    kind = provenance.get("producer_kind")
    if kind not in {"HUMAN", "TOOL", "LLM"}:
        raise RecordError("provenance.producer_kind is unsupported")
    _string(provenance.get("producer_id"), "provenance.producer_id")
    created_at = _string(provenance.get("created_at"), "provenance.created_at")
    if not _RFC3339_TIMESTAMP.fullmatch(created_at):
        raise RecordError("provenance.created_at must be an RFC 3339 timestamp")
    try:
        normalized_created_at = (
            created_at.removesuffix("Z") + "+00:00"
            if created_at.endswith("Z")
            else created_at
        )
        datetime.fromisoformat(normalized_created_at)
    except ValueError as exc:
        raise RecordError("provenance.created_at must be an RFC 3339 timestamp") from exc
    generation_ids = _string_set(
        provenance.get("generation_record_ids"),
        "provenance.generation_record_ids",
        nonempty=kind == "LLM",
    )
    for index, record_id in enumerate(generation_ids):
        if not re.fullmatch(r"[A-Z][A-Z0-9]*:[0-9a-f]{64}", record_id):
            raise RecordError(
                f"provenance.generation_record_ids[{index}] is not a content ID"
            )


def _validate_legacy_refs(record: Mapping[str, Any]) -> None:
    refs = _array(record.get("legacy_refs"), "legacy_refs")
    keys: list[tuple[str, str]] = []
    for index, raw in enumerate(refs):
        ref = _object(raw, f"legacy_refs[{index}]")
        keys.append(
            (
                _string(ref.get("namespace"), f"legacy_refs[{index}].namespace"),
                _string(ref.get("record_id"), f"legacy_refs[{index}].record_id"),
            )
        )
    if len(keys) != len(set(keys)) or keys != sorted(keys):
        raise RecordError("legacy_refs must be unique and canonically ordered")


def _validate_document(record: dict[str, Any]) -> None:
    _stable_identifier(record.get("document_key"), "source document document_key")
    _string(record.get("title"), "source document title")
    artifact = _object(record.get("artifact"), "source document artifact")
    _string(artifact.get("supplied_filename"), "source document artifact.supplied_filename")
    media_type = artifact.get("media_type")
    if media_type not in {
        "application/pdf",
        "text/plain",
        "text/markdown",
        "text/html",
    }:
        raise RecordError("source document artifact.media_type is unsupported")
    digest = _string(artifact.get("sha256"), "source document artifact.sha256")
    if not _SHA256.fullmatch(digest):
        raise RecordError("source document artifact.sha256 must be a SHA-256 hex digest")
    _integer(artifact.get("byte_length"), "source document artifact.byte_length", minimum=1)
    structure = _object(record.get("structure"), "source document structure")
    kind = structure.get("kind")
    if kind not in {"PDF", "UTF8_TEXT"}:
        raise RecordError("source document structure.kind must be PDF or UTF8_TEXT")
    if kind == "PDF":
        _integer(structure.get("page_count"), "source document structure.page_count", minimum=1)
        if structure.get("encoding") is not None:
            raise RecordError("PDF source documents must have null structure.encoding")
        if media_type != "application/pdf":
            raise RecordError("PDF structure requires application/pdf media type")
    else:
        if structure.get("page_count") is not None:
            raise RecordError("UTF8_TEXT source documents must have null page_count")
        if structure.get("encoding") != "UTF-8":
            raise RecordError("UTF8_TEXT source documents require UTF-8 encoding")
        if media_type == "application/pdf":
            raise RecordError("application/pdf media type requires PDF structure")
    _validate_legacy_refs(record)


def _validate_span(record: dict[str, Any]) -> None:
    _content_id(record.get("document_id"), "TDOC", "source span document_id")
    _stable_identifier(record.get("span_key"), "source span span_key")
    segments = _array(record.get("segments"), "source span segments")
    if not segments:
        raise RecordError("source span segments must not be empty")
    locator_kind: str | None = None
    previous_text_end: int | None = None
    for index, raw in enumerate(segments, start=1):
        segment = _object(raw, f"source span segments[{index - 1}]")
        if segment.get("ordinal") != index:
            raise RecordError("source span segment ordinals must be consecutive from one")
        locator = _object(segment.get("locator"), f"source span segment {index} locator")
        kind = locator.get("kind")
        if kind not in {"PDF_REGION", "UTF8_BYTE_RANGE"}:
            raise RecordError("source span locator kind is unsupported")
        if locator_kind is None:
            locator_kind = kind
        elif kind != locator_kind:
            raise RecordError(
                "source span segments must use one locator kind for their single document"
            )
        if kind == "PDF_REGION":
            if index > 1:
                raise RecordError(
                    "multi-region PDF source spans are unsupported until a "
                    "deterministic region-composition order is bound"
                )
            page = _integer(locator.get("physical_page"), "PDF physical page", minimum=1)
            zero = _integer(locator.get("page_index_zero_based"), "PDF zero-based page")
            if zero != page - 1:
                raise RecordError("PDF page index must equal physical page minus one")
            _nullable_nfc_text(locator.get("printed_label"), "PDF printed_label")
            _nullable_nfc_text(locator.get("section_raw"), "PDF section_raw")
            page_size = _array(locator.get("page_size_millipoints"), "PDF page size")
            if len(page_size) != 2 or any(type(item) is not int or item < 1 for item in page_size):
                raise RecordError("PDF page size must contain two positive integers")
            if locator.get("page_rotation_degrees") not in {0, 90, 180, 270}:
                raise RecordError("PDF page rotation must be 0, 90, 180, or 270 degrees")
            bbox = _array(locator.get("bbox_millipoints"), "PDF bbox")
            if len(bbox) != 4 or any(type(item) is not int or item < 0 for item in bbox):
                raise RecordError("PDF bbox must contain four nonnegative integers")
            if bbox[0] >= bbox[2] or bbox[1] >= bbox[3]:
                raise RecordError("PDF bbox must have positive area")
            if bbox[2] > page_size[0] or bbox[3] > page_size[1]:
                raise RecordError("PDF bbox must fall inside the declared page size")
        elif kind == "UTF8_BYTE_RANGE":
            start = _integer(locator.get("start_byte"), "text range start")
            end = _integer(locator.get("end_byte_exclusive"), "text range end", minimum=1)
            if end <= start:
                raise RecordError("UTF-8 byte range must be nonempty")
            if previous_text_end is not None and start < previous_text_end:
                raise RecordError(
                    "UTF-8 byte ranges must be strictly increasing and "
                    "non-overlapping; adjacent ranges are permitted"
                )
            previous_text_end = end
            if locator.get("encoding") != "UTF-8":
                raise RecordError("text range locator encoding must be UTF-8")
        literal = _object(segment.get("literal_snapshot"), "source span literal_snapshot")
        for field in ("algorithm", "tool", "tool_version", "selection_rule", "digest_domain"):
            _string(literal.get(field), f"literal snapshot {field}")
        snapshot_digest = _string(literal.get("sha256"), "literal snapshot sha256")
        if not _SHA256.fullmatch(snapshot_digest):
            raise RecordError("literal snapshot sha256 must be a SHA-256 hex digest")
        _integer(literal.get("item_count"), "literal snapshot item_count", minimum=1)
        transcription = segment.get("reviewed_transcription")
        if transcription is not None:
            reviewed = _object(transcription, "source span reviewed_transcription")
            _string(reviewed.get("path"), "reviewed transcription path")
            reviewed_digest = _string(reviewed.get("sha256"), "reviewed transcription sha256")
            if not _SHA256.fullmatch(reviewed_digest):
                raise RecordError("reviewed transcription sha256 must be a SHA-256 hex digest")
            if (
                reviewed.get("encoding") != "UTF-8"
                or reviewed.get("unicode_normalization") != "NFC"
                or reviewed.get("eol") != "LF"
                or type(reviewed.get("final_newline")) is not bool
            ):
                raise RecordError("reviewed transcription normalization profile is invalid")
            _string_set(
                reviewed.get("declared_transformations"),
                "reviewed transcription declared_transformations",
            )
    _string_set(record.get("context_span_ids"), "source span context_span_ids")
    _validate_legacy_refs(record)
    if record.get("source_inferential_status") is not None:
        raise PolicyViolation("source span source_inferential_status must remain null")


def _validate_charter(record: dict[str, Any]) -> None:
    for field in ("title", "problem_statement", "purpose", "system_boundary"):
        _string(record.get(field), f"translation charter {field}")
    bindings = _array(record.get("authority_bindings"), "charter authority_bindings")
    if not bindings:
        raise RecordError("charter authority_bindings must not be empty")
    roles: list[str] = []
    document_ids: list[str] = []
    for index, raw in enumerate(bindings):
        binding = _object(raw, f"charter authority_bindings[{index}]")
        document_ids.append(_content_id(binding.get("document_id"), "TDOC", "authority document_id"))
        role = _string(binding.get("role"), "authority role")
        if role not in {
            "SOLE_SEMANTIC_AUTHORITY",
            "CO_SEMANTIC_AUTHORITY",
            "CONTEXT_ONLY",
            "ADVISORY",
        }:
            raise RecordError("charter authority role is unsupported")
        roles.append(role)
    if len(document_ids) != len(set(document_ids)) or document_ids != sorted(document_ids):
        raise RecordError("charter authority bindings must be unique and ordered by document_id")
    sole_count = roles.count("SOLE_SEMANTIC_AUTHORITY")
    co_count = roles.count("CO_SEMANTIC_AUTHORITY")
    if sole_count == 1 and co_count == 0:
        pass
    elif sole_count == 0 and co_count >= 1:
        pass
    else:
        raise PolicyViolation("charter requires exactly one sole authority or one-or-more co-authorities")
    if record.get("output_kind") != "NEUTRAL_SEMANTIC_MODEL":
        raise PolicyViolation("translation charter output_kind must remain neutral semantic model")
    if record.get("success_claim") != "SCOPED_FIT_ONLY":
        raise PolicyViolation("translation charter success_claim must remain SCOPED_FIT_ONLY")
    if record.get("proposal_status") != "PROPOSED":
        raise PolicyViolation("translation charter is a proposal until separate human review")
    policies = _object(record.get("policies"), "translation charter policies")
    if policies != dict(_FIXED_POLICIES):
        raise PolicyViolation("translation charter policies do not match the fail-closed constitution")
    in_scope = set(
        _string_set(
            record.get("in_scope"),
            "translation charter in_scope",
            nonempty=True,
        )
    )
    out_of_scope = set(
        _string_set(
            record.get("out_of_scope"),
            "translation charter out_of_scope",
            nonempty=True,
        )
    )
    overlap = sorted(in_scope.intersection(out_of_scope))
    if overlap:
        raise PolicyViolation(
            "translation charter cannot put the same item in and out of scope: "
            + ", ".join(overlap)
        )
    distinctions = _sorted_objects(
        record.get("protected_distinctions"),
        "translation charter protected_distinctions",
        key="distinction_id",
        nonempty=True,
    )
    for distinction in distinctions:
        _string(distinction.get("statement"), "protected distinction statement")
        _validate_component_id("protected_distinction", distinction)


def _assert_acyclic(nodes: Iterable[str], edges: Iterable[tuple[str, str]], where: str) -> None:
    ordered_nodes = tuple(nodes)
    graph: dict[str, set[str]] = {node: set() for node in ordered_nodes}
    for source, target in edges:
        if source not in graph or target not in graph:
            raise RecordError(f"{where} edge references an unknown node")
        graph[source].add(target)
    state: dict[str, int] = {}

    def visit(node: str) -> None:
        mark = state.get(node, 0)
        if mark == 1:
            raise RecordError(f"{where} contains a dependency cycle")
        if mark == 2:
            return
        state[node] = 1
        for dependency in sorted(graph[node]):
            visit(dependency)
        state[node] = 2

    for node in sorted(graph):
        visit(node)


def _validate_graph(record: dict[str, Any]) -> None:
    _content_id(record.get("charter_id"), "TCHAR", "obligation graph charter_id")
    bindings = _array(record.get("span_bindings"), "obligation graph span_bindings")
    if not bindings:
        raise RecordError("obligation graph span_bindings must not be empty")
    bound_ids: list[str] = []
    target_ids: set[str] = set()
    for index, raw in enumerate(bindings):
        binding = _object(raw, f"obligation graph span_bindings[{index}]")
        span_id = _content_id(binding.get("span_id"), "TSPAN", "span binding span_id")
        bound_ids.append(span_id)
        role = binding.get("role")
        if role not in {"TARGET", "CONTEXT"}:
            raise RecordError("span binding role must be TARGET or CONTEXT")
        if role == "TARGET":
            target_ids.add(span_id)
    if bound_ids != sorted(bound_ids) or len(bound_ids) != len(set(bound_ids)):
        raise RecordError("obligation graph span bindings must be unique and ordered")
    if not target_ids:
        raise RecordError("obligation graph requires at least one TARGET span")
    obligations = _array(record.get("obligations"), "obligation graph obligations")
    if not obligations:
        raise RecordError("obligation graph obligations must not be empty")
    obligation_ids: list[str] = []
    covered_targets: set[str] = set()
    dependency_edges: list[tuple[str, str]] = []
    feature_ids: set[str] = set()
    source_claim_ids: set[str] = set()
    duty_ids: set[str] = set()
    for index, raw in enumerate(obligations):
        obligation = _object(raw, f"obligation graph obligations[{index}]")
        obligation_id = _validate_component_id("obligation", obligation)
        obligation_ids.append(obligation_id)
        source_claim = _object(obligation.get("source_claim"), "obligation source_claim")
        claim_id = _validate_component_id("source_claim", source_claim)
        if claim_id in source_claim_ids:
            raise RecordError("source claim IDs must be unique across the graph")
        source_claim_ids.add(claim_id)
        if source_claim.get("claim_kind") != "SOURCE_AUTHORITY":
            raise PolicyViolation("obligation source claim must remain SOURCE_AUTHORITY")
        if source_claim.get("expression_mode") != "VERBATIM_TRANSCRIPTION":
            raise PolicyViolation(
                "SOURCE_AUTHORITY claims must be verbatim transcriptions; "
                "paraphrase belongs in the SOURCE_INTERPRETATION duty"
            )
        _string(source_claim.get("statement"), "source claim statement")
        spans = set(_string_set(source_claim.get("source_span_ids"), "source claim span ids", nonempty=True))
        if not spans.issubset(set(bound_ids)):
            raise RecordError("source claim references a span outside the graph")
        covered_targets.update(spans.intersection(target_ids))
        _string_set(source_claim.get("source_marks_raw"), "source claim source_marks_raw")
        duty = _object(obligation.get("translation_duty"), "obligation translation_duty")
        duty_id = _validate_component_id("translation_duty", duty)
        if duty_id in duty_ids:
            raise RecordError("translation duty IDs must be unique across the graph")
        duty_ids.add(duty_id)
        if duty.get("claim_kind") != "SOURCE_INTERPRETATION":
            raise PolicyViolation("translation duty must remain SOURCE_INTERPRETATION")
        if duty.get("duty_kind") not in {
            "CLAIM",
            "DEFINITION",
            "DISTINCTION",
            "PROHIBITION",
            "QUALIFICATION",
            "MODALITY",
            "BOUNDARY",
            "EXAMPLE",
            "EXCEPTION",
            "OPEN_RESIDUE",
        }:
            raise RecordError("translation duty kind is unsupported")
        _string(duty.get("statement"), "translation duty statement")
        features = _sorted_objects(
            duty.get("protected_features"),
            "translation duty protected_features",
            key="feature_id",
        )
        for feature in features:
            feature_id = _validate_component_id("protected_feature", feature)
            if feature_id in feature_ids:
                raise RecordError("protected feature IDs must be unique across the graph")
            feature_ids.add(feature_id)
            if feature.get("kind") not in {
                "TERM",
                "RELATION",
                "DISTINCTION",
                "IDENTITY",
                "QUANTIFIER",
                "NEGATION",
                "MODALITY",
                "SCOPE",
                "DEPENDENCY",
                "QUALIFICATION",
                "EXAMPLE",
                "EXCEPTION",
            }:
                raise RecordError("protected feature kind is unsupported")
            _string(feature.get("statement"), "protected feature statement")
            distinction_ids = _string_set(
                feature.get("charter_distinction_ids"),
                "protected feature charter_distinction_ids",
            )
            for distinction_id in distinction_ids:
                _content_id(
                    distinction_id,
                    "TPD",
                    "protected feature charter distinction",
                )
        dependencies = _string_set(
            obligation.get("depends_on_obligation_ids"),
            "obligation dependencies",
        )
        dependency_edges.extend((obligation_id, dependency) for dependency in dependencies)
    if obligation_ids != sorted(obligation_ids) or len(obligation_ids) != len(set(obligation_ids)):
        raise RecordError("obligations must be unique and ordered by obligation_id")
    if covered_targets != target_ids:
        missing = sorted(target_ids - covered_targets)
        raise RecordError(f"target source spans lack an obligation or open residue: {missing}")
    _assert_acyclic(obligation_ids, dependency_edges, "source obligation graph")
    edges = _sorted_objects(
        record.get("edges"),
        "obligation graph edges",
        key="edge_id",
    )
    declared_dependencies: set[tuple[str, str]] = set()
    declared_dependency_count = 0
    for edge in edges:
        _validate_component_id("obligation_edge", edge)
        source = _content_id(edge.get("from_obligation_id"), "TO", "edge from_obligation_id")
        target = _content_id(edge.get("to_obligation_id"), "TO", "edge to_obligation_id")
        kind = edge.get("kind")
        if kind not in {
            "DEPENDS_ON",
            "QUALIFIES",
            "EXCLUDES",
            "CONTRASTS_WITH",
            "EXAMPLE_OF",
            "EXCEPTION_TO",
            "SCOPES",
        }:
            raise RecordError("obligation graph edge kind is unsupported")
        _string(edge.get("statement"), "obligation graph edge statement")
        if source not in obligation_ids or target not in obligation_ids:
            raise RecordError("obligation graph edge references an unknown obligation")
        if source == target:
            raise RecordError("obligation graph edges must not be self-loops")
        if kind == "DEPENDS_ON":
            declared_dependency_count += 1
            declared_dependencies.add((source, target))
    if declared_dependency_count != len(declared_dependencies):
        raise RecordError("logical DEPENDS_ON edges must be unique")
    if declared_dependencies != set(dependency_edges):
        raise RecordError(
            "DEPENDS_ON edges must exactly mirror depends_on_obligation_ids"
        )
    if record.get("proposal_status") != "PROPOSED":
        raise PolicyViolation("obligation graph must remain proposed until review")


def _validate_interpretation_set(record: dict[str, Any]) -> None:
    _content_id(record.get("charter_id"), "TCHAR", "interpretation charter_id")
    _content_id(record.get("graph_id"), "TOG", "interpretation graph_id")
    _string(record.get("question"), "interpretation question")
    source_span_ids = set(
        _string_set(record.get("source_span_ids"), "interpretation source spans", nonempty=True)
    )
    obligation_ids = set(
        _string_set(record.get("obligation_ids"), "interpretation obligations", nonempty=True)
    )
    relation = record.get("rival_relation")
    if relation not in {
        "EXCLUSIVE",
        "OVERLAPPING",
        "PARTIALLY_COMPATIBLE",
    }:
        raise RecordError("interpretation rival_relation is unsupported")
    branches = _array(record.get("branches"), "interpretation branches")
    if len(branches) < 2:
        raise RecordError("an interpretation set requires at least two rival branches")
    branch_ids: list[str] = []
    statements: list[str] = []
    for index, raw in enumerate(branches):
        branch = _object(raw, f"interpretation branches[{index}]")
        branch_ids.append(_validate_component_id("interpretation", branch))
        statements.append(_string(branch.get("statement"), "interpretation statement"))
        if branch.get("claim_kind") != "SOURCE_INTERPRETATION":
            raise PolicyViolation("interpretation branch claim_kind must remain SOURCE_INTERPRETATION")
        if branch.get("proposal_status") != "PROPOSED":
            raise PolicyViolation("interpretation branches remain proposed until review")
        branch_spans = set(
            _string_set(branch.get("source_span_ids"), "branch source spans", nonempty=True)
        )
        branch_obligations = set(
            _string_set(branch.get("interpreted_obligation_ids"), "branch obligations", nonempty=True)
        )
        if not branch_spans.issubset(source_span_ids):
            raise RecordError("interpretation branch cites a span outside its set")
        if not branch_obligations.issubset(obligation_ids):
            raise RecordError("interpretation branch cites an obligation outside its set")
        _string_set(branch.get("preserved_feature_ids"), "branch preserved features")
        _string_set(
            branch.get("discriminating_consequences"),
            "branch discriminating consequences",
            nonempty=True,
        )
        _string_set(branch.get("falsifier_conditions"), "branch falsifiers", nonempty=True)
        _string_set(branch.get("known_loss_risks"), "branch loss risks")
        effect = _object(branch.get("model_effect"), "branch model_effect")
        if effect.get("status") not in {"DECLARED", "UNPROJECTED"}:
            raise RecordError("branch model_effect status must be DECLARED or UNPROJECTED")
        affected = _string_set(effect.get("affected_element_keys"), "branch affected elements")
        _string(effect.get("effect_statement"), "branch model effect statement")
        if effect.get("status") == "DECLARED" and not affected:
            raise RecordError("a declared branch model effect must name affected elements")
        if effect.get("status") == "UNPROJECTED" and affected:
            raise RecordError("an unprojected branch cannot name affected elements")
    if branch_ids != sorted(branch_ids) or len(branch_ids) != len(set(branch_ids)):
        raise RecordError("interpretation branches must be unique and ordered by ID")
    admissible = _canonical_branch_sets(
        record.get("admissible_branch_sets"),
        "interpretation admissible_branch_sets",
    )
    branch_id_set = set(branch_ids)
    if any(not set(combination).issubset(branch_id_set) for combination in admissible):
        raise RecordError("an admissible branch set cites an unknown interpretation")
    singleton_sets = {(branch_id,) for branch_id in branch_ids}
    if not singleton_sets.issubset(set(admissible)):
        raise PolicyViolation(
            "every interpretation branch must remain independently admissible"
        )
    full_set = tuple(branch_ids)
    if relation == "EXCLUSIVE" and set(admissible) != singleton_sets:
        raise PolicyViolation(
            "EXCLUSIVE rivals permit exactly the singleton branch sets"
        )
    if relation == "OVERLAPPING" and full_set not in admissible:
        raise PolicyViolation(
            "OVERLAPPING rivals must explicitly admit the full branch set"
        )
    if relation == "PARTIALLY_COMPATIBLE":
        plural_sets = [item for item in admissible if len(item) > 1]
        if len(branch_ids) < 3 or not plural_sets or full_set in admissible:
            raise PolicyViolation(
                "PARTIALLY_COMPATIBLE rivals require at least three branches, "
                "an explicit plural subset, and no full-set combination"
            )
    if len(statements) != len(set(statements)):
        raise RecordError("interpretation branches must state distinct readings")
    if record.get("proposal_status") != "PROPOSED":
        raise PolicyViolation("interpretation set must remain proposed until review")


def _basis(
    value: Any,
    where: str,
    *,
    allow_structural: bool = True,
) -> tuple[str, tuple[str, ...]]:
    basis = _object(value, where)
    kind = _string(basis.get("premise_kind"), f"{where}.premise_kind")
    allowed = {"SOURCE_INTERPRETATION", "PROJECT_IMPORT"}
    if allow_structural:
        allowed.add("STRUCTURAL_SCAFFOLD")
    if kind not in allowed:
        raise PolicyViolation(f"{where}.premise_kind is not an allowed semantic basis")
    ids = _string_set(basis.get("record_ids"), f"{where}.record_ids")
    if kind == "STRUCTURAL_SCAFFOLD" and ids:
        raise RecordError("structural-scaffold basis cannot cite semantic records")
    if kind != "STRUCTURAL_SCAFFOLD" and not ids:
        raise RecordError("meaning-bearing basis must cite at least one record")
    prefix = {
        "SOURCE_INTERPRETATION": "TI",
        "PROJECT_IMPORT": "TIMP",
    }.get(kind)
    if prefix is not None:
        for index, record_id in enumerate(ids):
            _content_id(record_id, prefix, f"{where}.record_ids[{index}]")
    return kind, ids


def _validate_signature(record: dict[str, Any]) -> None:
    _content_id(record.get("charter_id"), "TCHAR", "neutral signature charter_id")
    members = _array(record.get("members"), "neutral signature members")
    if not members:
        raise RecordError("neutral signature must contain at least one member")
    ids: list[str] = []
    keys: list[str] = []
    for index, raw in enumerate(members):
        member = _object(raw, f"neutral signature members[{index}]")
        ids.append(_validate_component_id("signature_member", member))
        keys.append(_stable_identifier(member.get("element_key"), "signature element_key"))
        if member.get("kind") not in {
            "SORT",
            "ENTITY",
            "ROLE",
            "RELATION",
            "PROPERTY",
            "EVENT",
            "PROCESS",
            "MODALITY",
            "BOUNDARY",
            "IDENTITY_CONDITION",
        }:
            raise RecordError("neutral signature member kind is unsupported")
        _string(member.get("statement"), "signature member statement")
        roles = _array(member.get("argument_roles"), "signature member argument_roles")
        role_keys: list[tuple[str, str, str]] = []
        role_names: set[str] = set()
        for role_index, raw_role in enumerate(roles):
            role = _object(raw_role, f"signature member argument_roles[{role_index}]")
            name = _stable_identifier(role.get("name"), "signature argument role name")
            if name in role_names:
                raise RecordError("signature argument role names must be unique per member")
            role_names.add(name)
            target = _content_id(
                role.get("target_member_id"),
                "TNSM",
                "signature argument role target_member_id",
            )
            multiplicity = _string(role.get("multiplicity"), "signature argument role multiplicity")
            if multiplicity not in {"ONE", "OPTIONAL", "MANY"}:
                raise RecordError("signature argument role multiplicity is unsupported")
            role_keys.append((name, target, multiplicity))
        if role_keys != sorted(role_keys) or len(role_keys) != len(set(role_keys)):
            raise RecordError("signature argument roles must be unique and canonically ordered")
        for field in ("identity_conditions", "variation_conditions", "scope_conditions"):
            _string_set(member.get(field), f"signature member {field}")
        effect = member.get("semantic_effect")
        kind, _ids = _basis(member.get("basis"), "signature member basis")
        if effect not in {"MEANING_BEARING", "NONE"}:
            raise RecordError("signature member semantic_effect is unsupported")
        if effect == "MEANING_BEARING" and kind == "STRUCTURAL_SCAFFOLD":
            raise PolicyViolation("meaning-bearing signature members need an interpretation or import basis")
        if effect == "NONE" and kind != "STRUCTURAL_SCAFFOLD":
            raise PolicyViolation("structural signature members must not claim semantic basis")
    if ids != sorted(ids) or len(ids) != len(set(ids)):
        raise RecordError("signature members must be unique and ordered by member_id")
    if len(keys) != len(set(keys)):
        raise RecordError("neutral signature element_key values must be unique")
    known_member_ids = set(ids)
    for raw in members:
        member = _object(raw, "neutral signature member")
        for raw_role in _array(member.get("argument_roles"), "signature member argument_roles"):
            role = _object(raw_role, "signature argument role")
            if role["target_member_id"] not in known_member_ids:
                raise RecordError("signature argument role targets an unknown member")
    if record.get("proposal_status") != "PROPOSED":
        raise PolicyViolation("neutral signature must remain proposed until review")


def _validate_model(record: dict[str, Any]) -> None:
    _content_id(record.get("charter_id"), "TCHAR", "neutral model charter_id")
    _content_id(record.get("signature_id"), "TNS", "neutral model signature_id")
    _string_set(record.get("interpretation_ids"), "model interpretation_ids", nonempty=True)
    _string_set(record.get("import_ids"), "model import_ids")
    clauses = _array(record.get("clauses"), "neutral model clauses")
    if not clauses:
        raise RecordError("neutral model clauses must not be empty")
    clause_ids: list[str] = []
    clause_keys: list[str] = []
    edges: list[tuple[str, str]] = []
    for index, raw in enumerate(clauses):
        clause = _object(raw, f"neutral model clauses[{index}]")
        clause_id = _validate_component_id("model_clause", clause)
        clause_ids.append(clause_id)
        clause_keys.append(_stable_identifier(clause.get("element_key"), "model clause element_key"))
        if clause.get("kind") not in {
            "PRIMITIVE_CONDITION",
            "DEFINITION",
            "CONSTRAINT",
            "DISTINCTION",
            "SCOPE_CONDITION",
            "MODAL_CONDITION",
            "IDENTITY_CONDITION",
        }:
            raise RecordError("neutral model clause kind is unsupported")
        _string(clause.get("operative_prose"), "model clause operative_prose")
        _string_set(clause.get("uses_member_ids"), "model clause member IDs", nonempty=True)
        dependencies = _string_set(clause.get("depends_on_clause_ids"), "model clause dependencies")
        edges.extend((clause_id, dependency) for dependency in dependencies)
        _basis(clause.get("basis"), "model clause basis", allow_structural=False)
    if clause_ids != sorted(clause_ids) or len(clause_ids) != len(set(clause_ids)):
        raise RecordError("model clauses must be unique and ordered by clause_id")
    if len(clause_keys) != len(set(clause_keys)):
        raise RecordError("neutral model clause element_key values must be unique")
    _assert_acyclic(clause_ids, edges, "neutral model clause graph")
    ports = _sorted_objects(
        record.get("open_ports"),
        "neutral model open_ports",
        key="port_id",
    )
    for port in ports:
        _validate_component_id("model_open_port", port)
        _string(port.get("question"), "neutral model open port question")
        affected_member_ids = _string_set(
            port.get("affected_member_ids"),
            "open port affected_member_ids",
        )
        affected_clause_ids = _string_set(
            port.get("affected_clause_ids"),
            "open port affected_clause_ids",
        )
        if not affected_member_ids and not affected_clause_ids:
            raise RecordError(
                "a neutral model open port must name at least one affected member or clause"
            )
        _string_set(
            port.get("interpretation_set_ids"),
            "open port interpretation_set_ids",
            nonempty=True,
        )
    closure = _object(
        record.get("semantic_dependency_closure"),
        "semantic dependency closure",
    )
    closure_members = _array(closure.get("members"), "semantic dependency closure members")
    if not closure_members:
        raise RecordError("semantic dependency closure members must not be empty")
    closure_ids: list[str] = []
    for index, raw in enumerate(closure_members):
        member = _object(raw, f"semantic dependency closure[{index}]")
        premise_kind = _string(member.get("premise_kind"), "closure premise_kind")
        prefix = {
            "SOURCE_AUTHORITY": "TSC",
            "SOURCE_INTERPRETATION": "TI",
            "PROJECT_IMPORT": "TIMP",
        }.get(premise_kind)
        if prefix is None:
            raise RecordError("semantic dependency closure premise_kind is unsupported")
        closure_ids.append(_content_id(member.get("record_id"), prefix, "closure record_id"))
        if member.get("role") not in {"DIRECT", "TRANSITIVE"}:
            raise RecordError("semantic dependency closure role is unsupported")
    if closure_ids != sorted(closure_ids) or len(closure_ids) != len(set(closure_ids)):
        raise RecordError("semantic dependency closure must be unique and ordered")
    closure_digest = _string(closure.get("closure_sha256"), "semantic dependency closure sha256")
    if not _DOMAIN_SHA256.fullmatch(closure_digest):
        raise RecordError("semantic closure digest must be domain-separated SHA-256")
    if closure_digest != compute_semantic_dependency_closure_sha256(closure):
        raise RecordError("semantic dependency closure digest does not match its members")
    projection = _object(record.get("theory_projection"), "neutral model theory_projection")
    if projection.get("execution_semantics") != "NONE_V1":
        raise PolicyViolation("neutral semantic model v1 has no executable semantics")
    _string_set(projection.get("member_ids"), "theory projection member_ids", nonempty=True)
    _string_set(projection.get("clause_ids"), "theory projection clause_ids", nonempty=True)
    theory_digest = _string(projection.get("theory_record_sha256"), "theory projection digest")
    if not _DOMAIN_SHA256.fullmatch(theory_digest):
        raise RecordError("theory projection digest must be domain-separated SHA-256")
    if theory_digest != compute_theory_record_sha256(projection):
        raise RecordError("theory projection digest does not match its declaration")
    if record.get("proposal_status") != "PROPOSED" or record.get("semantic_verdict") is not None:
        raise PolicyViolation("neutral semantic model must remain a verdict-free proposal")


def _validate_import(record: dict[str, Any]) -> None:
    _content_id(record.get("charter_id"), "TCHAR", "project import charter_id")
    _stable_identifier(record.get("import_key"), "project import import_key")
    for field in ("statement", "scope", "motivation"):
        _string(record.get(field), f"project import {field}")
    if record.get("claim_kind") != "PROJECT_IMPORT":
        raise PolicyViolation("translation imports must remain PROJECT_IMPORT claims")
    if record.get("source_entitlement") != "NONE_CLAIMED":
        raise PolicyViolation("a project import cannot claim source entitlement")
    if record.get("category") not in {
        "SEMANTIC",
        "CAUSAL",
        "EPISTEMIC",
        "METHODOLOGICAL",
        "PHYSICAL",
    }:
        raise RecordError("project import category is unsupported")
    for field in ("independence_claim", "necessity_claim"):
        claim = _object(record.get(field), f"project import {field}")
        _string(claim.get("statement"), f"project import {field}.statement")
        if claim.get("status") != "PROPOSED":
            raise PolicyViolation(f"project import {field} must remain proposed")
        _string(claim.get("discriminator"), f"project import {field}.discriminator")
        _string_set(
            claim.get("evidence_record_ids"),
            f"project import {field}.evidence_record_ids",
        )
    alternatives = _array(record.get("alternatives"), "project import alternatives")
    if not alternatives:
        raise RecordError("project import must state at least one alternative")
    _string_set(record.get("alternatives"), "project import alternatives", nonempty=True)
    deletion_test = _object(record.get("deletion_test"), "project import deletion_test")
    _string(deletion_test.get("prediction"), "project import deletion test prediction")
    _string_set(deletion_test.get("test_record_ids"), "project import deletion test records")
    _string_set(record.get("affected_element_keys"), "project import affected elements", nonempty=True)
    if record.get("proposal_status") != "PROPOSED":
        raise PolicyViolation("project import must remain proposed until separate review")


def _validate_bridge(record: dict[str, Any]) -> None:
    for field, prefix in (
        ("charter_id", "TCHAR"),
        ("graph_id", "TOG"),
        ("signature_id", "TNS"),
        ("model_id", "TNM"),
    ):
        _content_id(record.get(field), prefix, f"two-way bridge {field}")
    if record.get("mapping_status") != "PROPOSED" or record.get("semantic_verdict") is not None:
        raise PolicyViolation("two-way bridge must remain a verdict-free proposal")
    _string_set(record.get("interpretation_set_ids"), "bridge interpretation_set_ids", nonempty=True)
    _string_set(record.get("import_ids"), "bridge import_ids")
    forward = _sorted_objects(
        record.get("forward_mappings"),
        "bridge forward_mappings",
        key="mapping_id",
        nonempty=True,
    )
    reverse = _sorted_objects(
        record.get("reverse_mappings"),
        "bridge reverse_mappings",
        key="mapping_id",
        nonempty=True,
    )
    deltas = _sorted_objects(
        record.get("translation_deltas"),
        "bridge translation_deltas",
        key="delta_id",
    )
    delta_ids = {_validate_component_id("translation_delta", item) for item in deltas}
    for raw in deltas:
        delta = _object(raw, "translation delta")
        if delta.get("status") != "OPEN":
            raise PolicyViolation("translation deltas remain open until separate review")
        if delta.get("kind") not in {
            "OMISSION",
            "ADDITION",
            "STRENGTHENING",
            "WEAKENING",
            "COLLAPSED_DISTINCTION",
            "SPLIT_DISTINCTION",
            "MODAL_SHIFT",
            "SCOPE_SHIFT",
            "IDENTITY_SHIFT",
            "DEPENDENCY_SHIFT",
            "UNRESOLVED",
        }:
            raise RecordError("translation delta kind is unsupported")
        source_ids = _string_set(
            delta.get("source_obligation_ids"),
            "translation delta source_obligation_ids",
        )
        element_ids = _string_set(
            delta.get("model_element_ids"),
            "translation delta model_element_ids",
        )
        if not source_ids and not element_ids:
            raise RecordError("translation delta must name a source or model element")
        _string(delta.get("statement"), "translation delta statement")
        _string(delta.get("consequence"), "translation delta consequence")
    referenced_delta_ids: set[str] = set()
    for raw in forward:
        mapping = _object(raw, "forward mapping")
        _validate_component_id("forward_mapping", mapping)
        _content_id(mapping.get("obligation_id"), "TO", "forward mapping obligation_id")
        _string_set(mapping.get("model_element_ids"), "forward mapping model_element_ids")
        _string_set(mapping.get("interpretation_ids"), "forward mapping interpretation_ids")
        _string(mapping.get("transformation_statement"), "forward mapping transformation_statement")
        _string(mapping.get("back_translation"), "forward mapping back_translation")
        coverage = mapping.get("coverage_claim")
        comparison = mapping.get("comparison")
        attached = set(_string_set(mapping.get("delta_ids"), "forward mapping delta_ids"))
        referenced_delta_ids.update(attached)
        if not attached.issubset(delta_ids):
            raise RecordError("forward mapping references an unknown translation delta")
        needs_delta = coverage in {"PARTIAL", "UNREPRESENTED", "DISPUTED"} or comparison in {
            "WEAKER",
            "STRONGER",
            "DIFFERENT",
            "UNRESOLVED",
        }
        if needs_delta and not attached:
            raise RecordError("non-exact forward mapping must expose at least one open delta")
        if coverage == "CLAIMED_EXACT" and comparison == "EQUIVALENT_CANDIDATE" and attached:
            raise RecordError("claimed-exact candidate mapping cannot hide an attached delta")
        if coverage == "CLAIMED_EXACT" and (
            comparison != "EQUIVALENT_CANDIDATE"
            or not mapping["model_element_ids"]
            or not mapping["interpretation_ids"]
        ):
            raise RecordError("claimed-exact forward mappings require projected rival trace")
        if coverage != "CLAIMED_EXACT" and not attached:
            raise RecordError("non-exact forward mappings require an open delta")
    if referenced_delta_ids != delta_ids:
        raise RecordError("every translation delta must be attached to a forward mapping")
    for mapping in reverse:
        _validate_component_id("reverse_mapping", mapping)
        element_id = _string(mapping.get("model_element_id"), "reverse mapping model_element_id")
        if not re.fullmatch(r"(?:TNSM|TNMC):[0-9a-f]{64}", element_id):
            raise RecordError("reverse mapping model_element_id has an invalid namespace")
        basis_kind = _string(mapping.get("basis_kind"), "reverse mapping basis_kind")
        basis_ids = _string_set(mapping.get("basis_ids"), "reverse mapping basis_ids")
        source_ids = _string_set(
            mapping.get("source_obligation_ids"),
            "reverse mapping source_obligation_ids",
        )
        effect = mapping.get("semantic_effect")
        _string(mapping.get("back_translation"), "reverse mapping back_translation")
        expected_prefix = {
            "SOURCE_INTERPRETATION": "TI",
            "PROJECT_IMPORT": "TIMP",
        }.get(basis_kind)
        if basis_kind == "STRUCTURAL_SCAFFOLD":
            if basis_ids or source_ids or effect != "NONE":
                raise PolicyViolation("structural reverse mappings cannot claim semantic basis")
        elif expected_prefix is None:
            raise RecordError("reverse mapping basis_kind is unsupported")
        else:
            if not basis_ids or effect != "MEANING_BEARING":
                raise PolicyViolation("meaning-bearing reverse mappings require an explicit basis")
            for index, basis_id in enumerate(basis_ids):
                _content_id(basis_id, expected_prefix, f"reverse mapping basis_ids[{index}]")
            if basis_kind == "SOURCE_INTERPRETATION" and not source_ids:
                raise RecordError("source-derived reverse mappings require source obligations")
            if basis_kind == "PROJECT_IMPORT" and source_ids:
                raise PolicyViolation("project-import reverse mappings cannot claim source obligations")


def _validate_snapshot(record: dict[str, Any]) -> None:
    array_fields = (
        ("document_ids", "TDOC", True),
        ("span_ids", "TSPAN", True),
        ("interpretation_set_ids", "TIS", True),
        ("import_ids", "TIMP", False),
    )
    for field, prefix, nonempty in array_fields:
        ids = _string_set(
            record.get(field),
            f"translation snapshot {field}",
            nonempty=nonempty,
        )
        for index, record_id in enumerate(ids):
            _content_id(record_id, prefix, f"translation snapshot {field}[{index}]")
    unresolved = _string_set(
        record.get("unresolved_record_ids"),
        "translation snapshot unresolved_record_ids",
    )
    for index, record_id in enumerate(unresolved):
        if not re.fullmatch(r"[A-Z][A-Z0-9]*:[0-9a-f]{64}", record_id):
            raise RecordError(
                f"translation snapshot unresolved_record_ids[{index}] is not a content ID"
            )
    for field, prefix in (
        ("charter_id", "TCHAR"),
        ("graph_id", "TOG"),
        ("signature_id", "TNS"),
        ("model_id", "TNM"),
        ("bridge_id", "TBR"),
    ):
        _content_id(record.get(field), prefix, f"translation snapshot {field}")
    digest = _string(record.get("record_closure_sha256"), "translation snapshot record_closure_sha256")
    if not _DOMAIN_SHA256.fullmatch(digest):
        raise RecordError("translation snapshot closure must be a domain-separated SHA-256")


def validate_translation_record(record: Mapping[str, Any]) -> str:
    """Validate context-free invariants and return the record ID."""

    checked = _object(record, "translation record")
    # canonical_bytes also rejects floats and unsupported Python values.
    canonical_bytes(checked)
    _reject_forbidden_keys(checked)
    record_id = validate_translation_record_id(checked)
    schema = checked["schema_version"]
    if not schema.endswith("translation-snapshot.v1"):
        _validate_provenance(checked)
    if schema.endswith("translation-source-document.v1"):
        _validate_document(checked)
    elif schema.endswith("translation-source-span.v1"):
        _validate_span(checked)
    elif schema.endswith("translation-charter.v1"):
        _validate_charter(checked)
    elif schema.endswith("translation-obligation-graph.v1"):
        _validate_graph(checked)
    elif schema.endswith("translation-interpretation-set.v1"):
        _validate_interpretation_set(checked)
    elif schema.endswith("translation-neutral-signature.v1"):
        _validate_signature(checked)
    elif schema.endswith("translation-neutral-model.v1"):
        _validate_model(checked)
    elif schema.endswith("translation-project-import.v1"):
        _validate_import(checked)
    elif schema.endswith("translation-two-way-bridge.v1"):
        _validate_bridge(checked)
    elif schema.endswith("translation-snapshot.v1"):
        _validate_snapshot(checked)
    return record_id


@dataclass(frozen=True)
class TranslationValidationResult:
    snapshot_id: str
    record_count: int
    unresolved_record_ids: tuple[str, ...]
    operational_status: str = "TRANSLATION_INTEGRITY_VALID"
    mapping_fidelity: str = "UNREVIEWED"
    semantic_verdict: None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "snapshot_id": self.snapshot_id,
            "record_count": self.record_count,
            "unresolved_record_ids": list(self.unresolved_record_ids),
            "operational_status": self.operational_status,
            "mapping_fidelity": self.mapping_fidelity,
            "semantic_verdict": self.semantic_verdict,
            "epistemic_limit": NON_INDUCTIVE_TRANSLATION_LIMIT,
        }


def _record_id(record: Mapping[str, Any]) -> str:
    schema = record.get("schema_version")
    if type(schema) is not str or schema not in TRANSLATION_SCHEMA_TO_ID:
        raise RecordError("unknown translation record schema")
    return _string(record.get(TRANSLATION_SCHEMA_TO_ID[schema][1]), "translation record ID")


def _resolve(records: Mapping[str, Mapping[str, Any]], record_id: str, schema: str) -> Mapping[str, Any]:
    try:
        record = records[record_id]
    except KeyError as exc:
        raise RecordError(f"unresolved translation record reference: {record_id}") from exc
    if record.get("schema_version") != schema:
        raise RecordError(f"translation reference {record_id} has the wrong record kind")
    return record


def compute_record_closure_sha256(records: Iterable[Mapping[str, Any]]) -> str:
    refs = [
        {
            "record_id": _record_id(record),
            "schema_version": record["schema_version"],
            "record_sha256": translation_record_digest(record),
        }
        for record in records
    ]
    refs.sort(key=lambda item: item["record_id"])
    if len(refs) != len({item["record_id"] for item in refs}):
        raise RecordError("translation closure contains duplicate record IDs")
    return domain_digest("creib.semantic-forge.translation-record-closure.v1", refs)


def validate_translation_snapshot(
    snapshot: Mapping[str, Any],
    records: Mapping[str, Mapping[str, Any]],
) -> TranslationValidationResult:
    """Validate a complete selected translation snapshot against frozen records."""

    _validate_translation_schema_shape(snapshot)
    snapshot_id = validate_translation_record(snapshot)
    if snapshot.get("schema_version") != "creib.semantic-forge.translation-snapshot.v1":
        raise RecordError("selected record is not a translation snapshot")
    checked_records: dict[str, Mapping[str, Any]] = {}
    for key, value in records.items():
        _validate_translation_schema_shape(value)
        actual = validate_translation_record(value)
        if key != actual:
            raise RecordError("translation inventory key does not match record ID")
        if actual in checked_records and checked_records[actual] != value:
            raise RecordError(f"translation content-ID collision: {actual}")
        checked_records[actual] = value

    selected_ids: list[str] = []
    typed_selections = (
        ("document_ids", "creib.semantic-forge.translation-source-document.v1"),
        ("span_ids", "creib.semantic-forge.translation-source-span.v1"),
        ("interpretation_set_ids", "creib.semantic-forge.translation-interpretation-set.v1"),
        ("import_ids", "creib.semantic-forge.translation-project-import.v1"),
    )
    for field, schema in typed_selections:
        for record_id in _string_set(snapshot.get(field), f"snapshot {field}"):
            _resolve(checked_records, record_id, schema)
            selected_ids.append(record_id)
    singleton_selections = (
        ("charter_id", "creib.semantic-forge.translation-charter.v1"),
        ("graph_id", "creib.semantic-forge.translation-obligation-graph.v1"),
        ("signature_id", "creib.semantic-forge.translation-neutral-signature.v1"),
        ("model_id", "creib.semantic-forge.translation-neutral-model.v1"),
        ("bridge_id", "creib.semantic-forge.translation-two-way-bridge.v1"),
    )
    for field, schema in singleton_selections:
        record_id = _string(snapshot.get(field), f"snapshot {field}")
        _resolve(checked_records, record_id, schema)
        selected_ids.append(record_id)
    if len(selected_ids) != len(set(selected_ids)):
        raise RecordError("snapshot selections contain a record in more than one role")

    documents = {record_id: checked_records[record_id] for record_id in snapshot["document_ids"]}
    spans = {record_id: checked_records[record_id] for record_id in snapshot["span_ids"]}
    charter = checked_records[snapshot["charter_id"]]
    graph = checked_records[snapshot["graph_id"]]
    interpretation_sets = {
        record_id: checked_records[record_id] for record_id in snapshot["interpretation_set_ids"]
    }
    imports = {record_id: checked_records[record_id] for record_id in snapshot["import_ids"]}
    signature = checked_records[snapshot["signature_id"]]
    model = checked_records[snapshot["model_id"]]
    bridge = checked_records[snapshot["bridge_id"]]

    for span in spans.values():
        if span["document_id"] not in documents:
            raise RecordError("source span document is not selected in the snapshot")
        missing_context = set(span["context_span_ids"]) - set(spans)
        if missing_context:
            raise RecordError(f"source span context is not selected: {sorted(missing_context)}")

    authority_roles = {
        item["document_id"]: item["role"] for item in charter["authority_bindings"]
    }
    if set(authority_roles) != set(documents):
        raise RecordError(
            "selected source documents must exactly equal the charter's role-bound documents"
        )
    semantic_authority_documents = {
        document_id
        for document_id, role in authority_roles.items()
        if role in {"SOLE_SEMANTIC_AUTHORITY", "CO_SEMANTIC_AUTHORITY"}
    }
    if graph["charter_id"] != snapshot["charter_id"]:
        raise RecordError("obligation graph is bound to another charter")
    graph_spans = {item["span_id"] for item in graph["span_bindings"]}
    if not graph_spans.issubset(spans):
        raise RecordError("obligation graph references an unselected source span")
    if graph_spans != set(spans):
        raise RecordError(
            "every selected source span must have exactly one TARGET or CONTEXT "
            "obligation-graph binding"
        )
    target_spans = {
        item["span_id"] for item in graph["span_bindings"] if item["role"] == "TARGET"
    }
    claim_span_ids = {
        span_id
        for obligation in graph["obligations"]
        for span_id in obligation["source_claim"]["source_span_ids"]
    }
    if not claim_span_ids.issubset(target_spans):
        raise PolicyViolation(
            "SOURCE_AUTHORITY claims may cite TARGET spans only, never CONTEXT spans"
        )
    claim_document_ids = {spans[span_id]["document_id"] for span_id in claim_span_ids}
    if not claim_document_ids.issubset(semantic_authority_documents):
        raise PolicyViolation(
            "SOURCE_AUTHORITY claims may cite only SOLE or CO semantic-authority documents"
        )
    if claim_document_ids != semantic_authority_documents:
        raise PolicyViolation(
            "every SOLE or CO semantic-authority document must ground at least one source claim"
        )
    obligations_by_id = {
        item["obligation_id"]: item for item in graph["obligations"]
    }
    obligation_ids = set(obligations_by_id)
    source_claim_by_obligation = {
        item["obligation_id"]: item["source_claim"]["claim_id"]
        for item in graph["obligations"]
    }
    graph_feature_ids = {
        feature["feature_id"]
        for item in graph["obligations"]
        for feature in item["translation_duty"]["protected_features"]
    }
    charter_distinction_ids = {
        distinction["distinction_id"]
        for distinction in charter["protected_distinctions"]
    }
    feature_rows = {
        feature["feature_id"]: feature
        for obligation in graph["obligations"]
        for feature in obligation["translation_duty"]["protected_features"]
    }
    linked_distinction_ids = {
        distinction_id
        for feature in feature_rows.values()
        for distinction_id in feature["charter_distinction_ids"]
    }
    if not linked_distinction_ids.issubset(charter_distinction_ids):
        raise RecordError("protected feature links an unknown charter distinction")
    if linked_distinction_ids != charter_distinction_ids:
        raise PolicyViolation(
            "every protected charter distinction must link to a graph feature"
        )

    branch_ids: set[str] = set()
    branches: dict[str, Mapping[str, Any]] = {}
    unprojected_interpretation_set_ids: set[str] = set()
    for interpretation_set_id, interpretation in interpretation_sets.items():
        if interpretation["charter_id"] != snapshot["charter_id"] or interpretation["graph_id"] != snapshot["graph_id"]:
            raise RecordError("interpretation set is bound to another charter or graph")
        if not set(interpretation["source_span_ids"]).issubset(spans):
            raise RecordError("interpretation set references an unselected source span")
        if not set(interpretation["obligation_ids"]).issubset(obligation_ids):
            raise RecordError("interpretation set references an unknown source obligation")
        for branch in interpretation["branches"]:
            branch_id = branch["interpretation_id"]
            if branch_id in branch_ids:
                raise RecordError("interpretation branch IDs must be unique across the snapshot")
            branch_ids.add(branch_id)
            branches[branch_id] = branch
            if not set(branch["source_span_ids"]).issubset(interpretation["source_span_ids"]):
                raise RecordError("interpretation branch cites a span outside its set")
            branch_obligation_ids = set(branch["interpreted_obligation_ids"])
            if not branch_obligation_ids.issubset(interpretation["obligation_ids"]):
                raise RecordError("interpretation branch cites an obligation outside its set")
            obligation_span_ids = {
                span_id
                for obligation_id in branch_obligation_ids
                for span_id in obligations_by_id[obligation_id]["source_claim"][
                    "source_span_ids"
                ]
            }
            if not obligation_span_ids.issubset(branch["source_span_ids"]):
                raise RecordError(
                    "interpretation branch source spans do not cover its "
                    "interpreted obligations"
                )
            preserved_feature_ids = set(branch["preserved_feature_ids"])
            if not preserved_feature_ids.issubset(graph_feature_ids):
                raise RecordError("interpretation branch preserves an unknown source feature")
            obligation_feature_ids = {
                feature["feature_id"]
                for obligation_id in branch_obligation_ids
                for feature in obligations_by_id[obligation_id]["translation_duty"][
                    "protected_features"
                ]
            }
            if not preserved_feature_ids.issubset(obligation_feature_ids):
                raise RecordError(
                    "interpretation branch preserves a feature outside its "
                    "interpreted obligations"
                )
            if branch["model_effect"]["status"] == "UNPROJECTED":
                unprojected_interpretation_set_ids.add(interpretation_set_id)

    for project_import in imports.values():
        if project_import["charter_id"] != snapshot["charter_id"]:
            raise RecordError("project import is bound to another charter")

    if signature["charter_id"] != snapshot["charter_id"]:
        raise RecordError("neutral signature is bound to another charter")
    if model["charter_id"] != snapshot["charter_id"] or model["signature_id"] != snapshot["signature_id"]:
        raise RecordError("neutral model is bound to another charter or signature")
    if set(model["interpretation_ids"]) - branch_ids:
        raise RecordError("neutral model cites an unselected interpretation branch")
    if set(model["import_ids"]) != set(imports):
        raise RecordError("neutral model import closure differs from the selected imports")

    members = {item["member_id"]: item for item in signature["members"]}
    clauses = {item["clause_id"]: item for item in model["clauses"]}
    member_element_keys = {item["element_key"] for item in members.values()}
    clause_element_keys = {item["element_key"] for item in clauses.values()}
    if member_element_keys.intersection(clause_element_keys):
        raise RecordError(
            "signature member and model clause element_key values must be "
            "globally disjoint"
        )
    for member in members.values():
        basis_kind, basis_ids = _basis(member["basis"], "signature member basis")
        if basis_kind == "SOURCE_INTERPRETATION" and not set(basis_ids).issubset(branch_ids):
            raise RecordError("signature member cites an unselected interpretation branch")
        if basis_kind == "PROJECT_IMPORT" and not set(basis_ids).issubset(imports):
            raise RecordError("signature member cites an unselected project import")
        for role in member["argument_roles"]:
            if role["target_member_id"] not in members:
                raise RecordError("signature argument role targets an unknown member")
    for clause in clauses.values():
        if not set(clause["uses_member_ids"]).issubset(members):
            raise RecordError("model clause uses an unknown signature member")
        basis_kind, basis_ids = _basis(
            clause["basis"],
            "model clause basis",
            allow_structural=False,
        )
        if basis_kind == "SOURCE_INTERPRETATION" and not set(basis_ids).issubset(branch_ids):
            raise RecordError("model clause cites an unselected interpretation branch")
        if basis_kind == "PROJECT_IMPORT" and not set(basis_ids).issubset(imports):
            raise RecordError("model clause cites an unselected project import")
    ported_interpretation_set_ids: set[str] = set()
    for port in model["open_ports"]:
        if not set(port["affected_member_ids"]).issubset(members):
            raise RecordError("model open port references an unknown signature member")
        if not set(port["affected_clause_ids"]).issubset(clauses):
            raise RecordError("model open port references an unknown clause")
        if not set(port["interpretation_set_ids"]).issubset(interpretation_sets):
            raise RecordError("model open port references an unselected interpretation set")
        ported_interpretation_set_ids.update(port["interpretation_set_ids"])
    if not unprojected_interpretation_set_ids.issubset(
        ported_interpretation_set_ids
    ):
        raise PolicyViolation(
            "every UNPROJECTED interpretation branch must have an open port "
            "covering its interpretation set"
        )
    model_elements = tuple(members.values()) + tuple(clauses.values())
    direct_interpretations: set[str] = set()
    direct_imports: set[str] = set()
    for element in model_elements:
        basis_kind, basis_ids = _basis(element["basis"], "model element basis")
        if basis_kind == "SOURCE_INTERPRETATION":
            direct_interpretations.update(basis_ids)
        elif basis_kind == "PROJECT_IMPORT":
            direct_imports.update(basis_ids)
    if set(model["interpretation_ids"]) != direct_interpretations:
        raise RecordError("neutral model interpretation_ids do not equal its direct bases")
    if set(model["import_ids"]) != direct_imports:
        raise RecordError("neutral model import_ids do not equal its direct bases")
    for import_id, project_import in imports.items():
        affected_keys = {
            element["element_key"]
            for element in model_elements
            if element["basis"]["premise_kind"] == "PROJECT_IMPORT"
            and import_id in element["basis"]["record_ids"]
        }
        if set(project_import["affected_element_keys"]) != affected_keys:
            raise PolicyViolation(
                "project import affected_element_keys do not exactly match "
                "its direct model bases"
            )
    for branch_id, branch in branches.items():
        affected_keys = {
            element["element_key"]
            for element in model_elements
            if element["basis"]["premise_kind"] == "SOURCE_INTERPRETATION"
            and branch_id in element["basis"]["record_ids"]
        }
        declared_effect = branch["model_effect"]
        if declared_effect["status"] == "UNPROJECTED":
            if affected_keys:
                raise PolicyViolation(
                    "an UNPROJECTED interpretation is nevertheless used by the neutral model"
                )
        elif set(declared_effect["affected_element_keys"]) != affected_keys:
            raise PolicyViolation(
                "a DECLARED interpretation model effect does not exactly match its model bases"
            )
    modeled_interpretations = set(model["interpretation_ids"])
    for interpretation_set in interpretation_sets.values():
        modeled_in_set = modeled_interpretations.intersection(
            branch["interpretation_id"]
            for branch in interpretation_set["branches"]
        )
        modeled_combination = tuple(sorted(modeled_in_set))
        admissible = {
            tuple(combination)
            for combination in interpretation_set["admissible_branch_sets"]
        }
        if modeled_combination and modeled_combination not in admissible:
            raise PolicyViolation(
                "neutral model interpretation bases are not an explicitly "
                "admissible branch set"
            )
    for distinction_id in charter_distinction_ids:
        linked_features = {
            feature_id
            for feature_id, feature in feature_rows.items()
            if distinction_id in feature["charter_distinction_ids"]
        }
        if not any(
            branch_id in modeled_interpretations
            and bool(linked_features.intersection(branch["preserved_feature_ids"]))
            for branch_id, branch in branches.items()
        ):
            raise PolicyViolation(
                "a protected charter distinction has no modeled interpretation coverage"
            )

    closure_members = model["semantic_dependency_closure"]["members"]
    actual_closure_members = {
        item["record_id"]: (item["premise_kind"], item["role"])
        for item in closure_members
    }
    source_claim_ids = {
        source_claim_by_obligation[obligation_id]
        for branch_id in direct_interpretations
        for obligation_id in branches[branch_id]["interpreted_obligation_ids"]
    }
    expected_closure_members = {
        **{
            record_id: ("SOURCE_AUTHORITY", "TRANSITIVE")
            for record_id in source_claim_ids
        },
        **{
            record_id: ("SOURCE_INTERPRETATION", "DIRECT")
            for record_id in direct_interpretations
        },
        **{
            record_id: ("PROJECT_IMPORT", "DIRECT")
            for record_id in direct_imports
        },
    }
    if actual_closure_members != expected_closure_members:
        raise RecordError(
            "semantic dependency closure does not exactly expose direct and transitive premises"
        )
    projection = model["theory_projection"]
    if projection["signature_id"] != snapshot["signature_id"]:
        raise RecordError("theory projection names another signature")
    if set(projection["member_ids"]) != set(members) or set(projection["clause_ids"]) != set(clauses):
        raise RecordError("theory projection is not complete")

    if (
        bridge["charter_id"] != snapshot["charter_id"]
        or bridge["graph_id"] != snapshot["graph_id"]
        or bridge["signature_id"] != snapshot["signature_id"]
        or bridge["model_id"] != snapshot["model_id"]
    ):
        raise RecordError("two-way bridge is bound to another translation surface")
    if set(bridge["interpretation_set_ids"]) != set(interpretation_sets):
        raise RecordError("bridge interpretation-set closure is incomplete")
    if set(bridge["import_ids"]) != set(imports):
        raise RecordError("bridge import closure is incomplete")

    delta_ids = {item["delta_id"] for item in bridge["translation_deltas"]}
    for delta in bridge["translation_deltas"]:
        if not set(delta["source_obligation_ids"]).issubset(obligation_ids):
            raise RecordError("translation delta references an unknown source obligation")
        if not set(delta["model_element_ids"]).issubset(set(members).union(clauses)):
            raise RecordError("translation delta references an unknown model element")
    for mapping in bridge["forward_mappings"]:
        if mapping["obligation_id"] not in obligation_ids:
            raise RecordError("forward mapping references an unknown source obligation")
        if not set(mapping["model_element_ids"]).issubset(set(members).union(clauses)):
            raise RecordError("forward mapping references an unknown model element")
        if not set(mapping["interpretation_ids"]).issubset(model["interpretation_ids"]):
            raise RecordError("forward mapping references an unmodeled interpretation")
        if not set(mapping["delta_ids"]).issubset(delta_ids):
            raise RecordError("forward mapping references an unknown translation delta")

    forward_obligations = [mapping["obligation_id"] for mapping in bridge["forward_mappings"]]
    if len(forward_obligations) != len(set(forward_obligations)) or set(forward_obligations) != obligation_ids:
        raise RecordError("every source obligation must have exactly one forward mapping")
    model_element_ids = set(members).union(clauses)
    reverse_elements = [mapping["model_element_id"] for mapping in bridge["reverse_mappings"]]
    if len(reverse_elements) != len(set(reverse_elements)) or set(reverse_elements) != model_element_ids:
        raise RecordError("every model element must have exactly one reverse mapping")

    for mapping in bridge["reverse_mappings"]:
        element_id = mapping["model_element_id"]
        element = members.get(element_id, clauses.get(element_id))
        if element is None:
            raise RecordError("reverse mapping references an unknown model element")
        basis_kind, basis_ids = _basis(element["basis"], "model element basis")
        reverse_kind = mapping["basis_kind"]
        reverse_ids = tuple(mapping["basis_ids"])
        if reverse_kind != basis_kind or reverse_ids != basis_ids:
            raise RecordError("reverse mapping basis disagrees with the model element basis")
        if basis_kind == "SOURCE_INTERPRETATION" and not set(basis_ids).issubset(branch_ids):
            raise RecordError("model element cites an unknown interpretation branch")
        if basis_kind == "PROJECT_IMPORT" and not set(basis_ids).issubset(imports):
            raise RecordError("model element cites an unknown project import")
        allowed_source_obligations: set[str] = set()
        if basis_kind == "SOURCE_INTERPRETATION":
            allowed_source_obligations = {
                obligation_id
                for branch_id in basis_ids
                for obligation_id in branches[branch_id]["interpreted_obligation_ids"]
            }
        mapped_source_obligations = set(mapping["source_obligation_ids"])
        if basis_kind == "SOURCE_INTERPRETATION" and (
            not mapped_source_obligations
            or not mapped_source_obligations.issubset(allowed_source_obligations)
        ):
            raise RecordError(
                "reverse mapping source obligations must be a nonempty subset "
                "of its exact interpretation basis"
            )

    reverse_by_element = {
        mapping["model_element_id"]: mapping for mapping in bridge["reverse_mappings"]
    }
    deltas_by_id = {
        delta["delta_id"]: delta for delta in bridge["translation_deltas"]
    }
    for mapping in bridge["forward_mappings"]:
        obligation_id = mapping["obligation_id"]
        source_basis_ids: set[str] = set()
        for element_id in mapping["model_element_ids"]:
            reverse = reverse_by_element[element_id]
            if reverse["basis_kind"] == "PROJECT_IMPORT":
                raise PolicyViolation(
                    "a source-obligation forward mapping cannot rely on a project-import element"
                )
            if reverse["basis_kind"] == "SOURCE_INTERPRETATION":
                if obligation_id not in reverse["source_obligation_ids"]:
                    raise PolicyViolation(
                        "forward and reverse mappings disagree on source-obligation incidence"
                    )
                source_basis_ids.update(reverse["basis_ids"])
        if set(mapping["interpretation_ids"]) != source_basis_ids:
            raise PolicyViolation(
                "forward mapping interpretation_ids do not equal its elements' source bases"
            )
        for delta_id in mapping["delta_ids"]:
            delta = deltas_by_id[delta_id]
            if (
                obligation_id not in delta["source_obligation_ids"]
                and not set(mapping["model_element_ids"]).intersection(
                    delta["model_element_ids"]
                )
            ):
                raise PolicyViolation(
                    "forward mapping attaches an unrelated translation delta"
                )
        if mapping["coverage_claim"] == "CLAIMED_EXACT":
            protected = {
                feature["feature_id"]
                for feature in obligations_by_id[obligation_id]["translation_duty"][
                    "protected_features"
                ]
            }
            preserved = {
                feature_id
                for branch_id in mapping["interpretation_ids"]
                for feature_id in branches[branch_id]["preserved_feature_ids"]
            }
            if not protected.issubset(preserved):
                raise PolicyViolation(
                    "CLAIMED_EXACT mapping does not preserve every protected feature"
                )

    forward_incidence: dict[str, set[str]] = {
        element_id: set() for element_id in model_element_ids
    }
    forward_by_obligation = {
        mapping["obligation_id"]: mapping
        for mapping in bridge["forward_mappings"]
    }
    for obligation_id, mapping in forward_by_obligation.items():
        for element_id in mapping["model_element_ids"]:
            forward_incidence[element_id].add(obligation_id)
    for element_id, mapping in reverse_by_element.items():
        if set(mapping["source_obligation_ids"]) != forward_incidence[element_id]:
            raise RecordError(
                "reverse mapping source obligations do not exactly equal "
                "direct forward element incidence"
            )

    clause_dependencies = {
        clause_id: set(clause["depends_on_clause_ids"])
        for clause_id, clause in clauses.items()
    }

    def reaches_prerequisite(dependent: str, prerequisite: str) -> bool:
        """Return positive-length TNMC depends-on reachability only."""

        if dependent not in clause_dependencies or prerequisite not in clause_dependencies:
            return False
        pending = list(clause_dependencies[dependent])
        visited: set[str] = set()
        while pending:
            current = pending.pop()
            if current == prerequisite:
                return True
            if current not in visited:
                visited.add(current)
                pending.extend(clause_dependencies[current] - visited)
        return False

    source_dependency_pairs = {
        (obligation_id, prerequisite_id)
        for obligation_id, obligation in obligations_by_id.items()
        for prerequisite_id in obligation["depends_on_obligation_ids"]
    }
    dependency_shifts = {
        delta_id: delta
        for delta_id, delta in deltas_by_id.items()
        if delta["kind"] == "DEPENDENCY_SHIFT"
    }
    shifted_pairs: set[tuple[str, str]] = set()
    for delta_id, delta in dependency_shifts.items():
        matching_pairs = []
        for dependent_id, prerequisite_id in source_dependency_pairs:
            dependent_mapping = forward_by_obligation[dependent_id]
            prerequisite_mapping = forward_by_obligation[prerequisite_id]
            exact_model_footprint = set(dependent_mapping["model_element_ids"]).union(
                prerequisite_mapping["model_element_ids"]
            )
            if (
                set(delta["source_obligation_ids"])
                == {dependent_id, prerequisite_id}
                and set(delta["model_element_ids"]) == exact_model_footprint
                and delta_id in dependent_mapping["delta_ids"]
                and all(
                    delta_id not in other_mapping["delta_ids"]
                    for other_id, other_mapping in forward_by_obligation.items()
                    if other_id != dependent_id
                )
            ):
                matching_pairs.append((dependent_id, prerequisite_id))
        if len(matching_pairs) != 1:
            raise PolicyViolation(
                "a DEPENDENCY_SHIFT must bind exactly one declared source "
                "dependency, its complete mapped-element footprint, and the "
                "dependent obligation's forward mapping only; v1 does not infer "
                "direction from unordered delta sets or prose"
            )
        matched_pair = matching_pairs[0]
        if matched_pair in shifted_pairs:
            raise PolicyViolation(
                "a declared source dependency may have at most one exact "
                "DEPENDENCY_SHIFT"
            )
        shifted_pairs.add(matched_pair)

    for dependent_id, prerequisite_id in source_dependency_pairs:
        dependent_elements = set(
            forward_by_obligation[dependent_id]["model_element_ids"]
        )
        prerequisite_elements = set(
            forward_by_obligation[prerequisite_id]["model_element_ids"]
        )
        forward_witness = any(
            reaches_prerequisite(dependent, prerequisite)
            for dependent in dependent_elements
            for prerequisite in prerequisite_elements
        )
        reverse_witness = any(
            reaches_prerequisite(prerequisite, dependent)
            for dependent in dependent_elements
            for prerequisite in prerequisite_elements
        )
        if not (forward_witness and not reverse_witness) and (
            dependent_id,
            prerequisite_id,
        ) not in shifted_pairs:
            raise PolicyViolation(
                "source obligation dependency lacks an exclusively correctly "
                "directed positive-length TNMC dependency path or an exact "
                "open DEPENDENCY_SHIFT; v1 does not infer direction from "
                "unordered delta sets or prose"
            )

    selected_records = [checked_records[record_id] for record_id in selected_ids]
    actual_closure = compute_record_closure_sha256(selected_records)
    if snapshot["record_closure_sha256"] != actual_closure:
        raise RecordError("translation snapshot record closure digest does not match selected records")
    unresolved = _string_set(snapshot["unresolved_record_ids"], "snapshot unresolved_record_ids")
    nested_ids = {
        distinction["distinction_id"]
        for distinction in charter["protected_distinctions"]
    }
    nested_ids.update(obligation_ids)
    nested_ids.update(source_claim_by_obligation.values())
    nested_ids.update(
        item["translation_duty"]["duty_id"] for item in graph["obligations"]
    )
    nested_ids.update(graph_feature_ids)
    nested_ids.update(item["edge_id"] for item in graph["edges"])
    nested_ids.update(branch_ids)
    nested_ids.update(members)
    nested_ids.update(clauses)
    nested_ids.update(item["port_id"] for item in model["open_ports"])
    nested_ids.update(item["mapping_id"] for item in bridge["forward_mappings"])
    nested_ids.update(item["mapping_id"] for item in bridge["reverse_mappings"])
    nested_ids.update(delta_ids)
    unresolved_generation_ids = {
        generation_id
        for record in selected_records
        for generation_id in record.get("provenance", {}).get(
            "generation_record_ids", []
        )
    }
    nested_ids.update(unresolved_generation_ids)
    allowed_unresolved = set(selected_ids).union(nested_ids)
    unresolved_set = set(unresolved)
    if not unresolved_set.issubset(allowed_unresolved):
        raise RecordError("snapshot unresolved_record_ids contains an unknown record")
    required_unresolved = {
        project_import["import_id"] for project_import in imports.values()
    }
    required_unresolved.update(branch_ids - set(model["interpretation_ids"]))
    required_unresolved.update(port["port_id"] for port in model["open_ports"])
    required_unresolved.update(delta_ids)
    required_unresolved.update(unresolved_generation_ids)
    required_unresolved.update(
        obligation["obligation_id"]
        for obligation in graph["obligations"]
        if obligation["translation_duty"]["duty_kind"] == "OPEN_RESIDUE"
    )
    missing_unresolved = sorted(required_unresolved - unresolved_set)
    if missing_unresolved:
        raise PolicyViolation(
            "snapshot omits mechanically open records from unresolved_record_ids: "
            + ", ".join(missing_unresolved)
        )

    return TranslationValidationResult(
        snapshot_id=snapshot_id,
        record_count=len(selected_ids) + 1,
        unresolved_record_ids=unresolved,
    )


def load_translation_inventory(directory: Path) -> dict[str, Mapping[str, Any]]:
    """Load one unambiguous, canonical file for every inventory record."""

    if not isinstance(directory, Path):
        raise TypeError("directory must be pathlib.Path")
    if not directory.is_dir():
        raise RecordError(f"translation inventory directory does not exist: {directory}")
    result: dict[str, Mapping[str, Any]] = {}
    for path in sorted(directory.rglob("*.json")):
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise RecordError(f"cannot read {path}: {exc}") from exc
        try:
            source = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise RecordError(f"JSON is not UTF-8: {path}") from exc
        record = loads_strict(source)
        if raw != canonical_bytes(record) + b"\n":
            raise RecordError(
                "translation inventory record is not canonical JSON with exactly "
                f"one trailing newline: {path}"
            )
        if type(record) is not dict or record.get("schema_version") not in TRANSLATION_SCHEMA_TO_ID:
            raise RecordError(f"unrecognized translation record in inventory: {path}")
        _validate_translation_schema_shape(record)
        record_id = validate_translation_record(record)
        if record_id in result:
            raise RecordError(f"duplicate translation record ID: {record_id}")
        result[record_id] = record
    return result


def loads_translation_record(source: str) -> dict[str, Any]:
    record = _object(loads_strict(source), "translation record")
    _validate_translation_schema_shape(record)
    validate_translation_record(record)
    return record


def verify_source_document_bytes(record: Mapping[str, Any], path: Path) -> None:
    """Verify external source bytes without granting semantic authority."""

    _validate_translation_schema_shape(record)
    validate_translation_record(record)
    if record.get("schema_version") != "creib.semantic-forge.translation-source-document.v1":
        raise RecordError("byte verification requires a source-document record")
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise RecordError(f"cannot read source document: {exc}") from exc
    artifact = record["artifact"]
    if len(raw) != artifact["byte_length"] or bytes_digest(raw) != artifact["sha256"]:
        raise RecordError("source document bytes do not match the bound artifact")
    if record["structure"]["kind"] == "UTF8_TEXT":
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise RecordError("bound UTF8_TEXT artifact is not valid UTF-8") from exc
