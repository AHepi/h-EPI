"""Offline JSON Schema validation for semantic-forge records.

The schemas use absolute identifiers so relative ``$ref`` values have stable
resolution semantics.  This module registers every local schema before it
checks references or instances and supplies a retrieval function that always
fails.  Validation therefore cannot silently fetch a schema from the network.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping
from urllib.parse import urljoin, urlsplit

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError
from referencing import Registry, Resource
from referencing.exceptions import (
    CannotDetermineSpecification,
    InvalidAnchor,
    NoSuchAnchor,
    NoSuchResource,
    PointerToNowhere,
    Unresolvable,
    Unretrievable,
)

from creib.canonical import bytes_digest, canonical_bytes
from creib.errors import RecordError
from creib.strict_json import load_strict, loads_strict

from .models import parse_issue, parse_minimal_pair_challenge


DEFAULT_SCHEMA_DIR = Path(__file__).resolve().parents[3] / "forge" / "schema"
_DRAFT_2020_12 = "https://json-schema.org/draft/2020-12/schema"
_CHALLENGE_SCHEMA_ID = "https://ahepi.example/smf/0.1/challenge.schema.json"
_CORPUS_SCHEMA_ID = "https://ahepi.example/smf/0.1/corpus.schema.json"
_RESEARCH_ISSUE_SCHEMA_ID = (
    "https://ahepi.example/smf/0.1/research-issue.schema.json"
)
_RESEARCH_LEDGER_SCHEMA_ID = (
    "https://ahepi.example/smf/0.2/research-ledger.schema.json"
)
_FULL_RECORD_RUNTIME_SCHEMA_IDS = frozenset(
    {
        _CHALLENGE_SCHEMA_ID,
        _CORPUS_SCHEMA_ID,
        _RESEARCH_ISSUE_SCHEMA_ID,
        _RESEARCH_LEDGER_SCHEMA_ID,
    }
)
_ANNOTATION_PROSE_STATUS = "unreviewed_non_authoritative"
_ANNOTATION_PROSE_SEMANTIC_EFFECT = "none"
_PINNED_IDENTIFIER_INVENTORY_SHA256 = (
    "25c6ebdf2f4da088c47b7d8856638773c1094584b53a3c3f745a764108318c92"
)
_IDENTIFIER_INVENTORY_PATH = (
    DEFAULT_SCHEMA_DIR.parents[1]
    / "baseline/cr-1.0/bootstrap-v0.1/authority/identifier_inventory.yaml"
)


@dataclass(frozen=True)
class _AuthorityReferenceContract:
    subject_id: str
    subject_sha256: str
    basis_kind: str
    relationship: str
    reference_sha256: str


# These identifiers and page sets are transcribed from the digest-pinned CR-1.0
# identifier inventory above.  A reference may select only pages belonging to
# its named records; the complete reference object is separately digest-bound.
_CR1_SOURCE_RECORD_PAGES: Mapping[str, tuple[int, ...]] = MappingProxyType({
    "LANGUAGE-1.1": (221,), "TY-3": (221,), "MS-4": (222,), "MS-5": (222,),
    "SC-2": (222,), "SC-3": (222,), "SC-4": (222,), "SC-5": (222,),
    "SC-6": (222,), "SC-8": (223,), "DF-1": (223,), "DF-5": (223,),
    "DF-6": (223,), "DF-7": (224,), "DF-7a": (223, 224),
    "DF-11": (224,), "DF-12": (224,), "DF-13": (224,), "DF-22": (229,),
    "DF-23": (229,), "DP-1": (226,), "DP-2": (226,), "DP-3": (226,),
    "DP-4": (226,), "DP-5": (226,), "BR-1": (228,), "BR-2": (228,),
    "BR-3": (228,), "BR-4": (228,), "BR-5": (228,), "BR-6": (229,),
    "BR-7": (229,), "BR-8": (229,), "TH-7": (230, 231), "TH-9": (231,),
    "TH-12": (232,), "TH-14": (232,),
})


def _authority_contract(
    subject_id: str,
    subject_sha256: str,
    basis_kind: str,
    relationship: str,
    reference_sha256: str,
) -> _AuthorityReferenceContract:
    return _AuthorityReferenceContract(
        subject_id, subject_sha256, basis_kind, relationship, reference_sha256
    )


_AUTHORITY_REFERENCE_CONTRACTS: Mapping[str, _AuthorityReferenceContract] = MappingProxyType({
    "CR1REF:SMF-CH-ANTI-INDUCTION-001:AUTHORITATIVE:01": _authority_contract("SMF-CH-ANTI-INDUCTION-001", "622159653f66c255eb2c728b58266ffdd4e120300bb8dfb2771e163736577b06", "source_interpretation", "authoritative", "fdd1a5c0041bc663d06ea19718bfcfe9f4f59250b22aab22462821b4e93b21d7"),
    "CR1REF:SMF-CH-CONJECTURE-BEFORE-CRITICISM-001:RELATED:01": _authority_contract("SMF-CH-CONJECTURE-BEFORE-CRITICISM-001", "75c3a08802ca847037ade129cdd551e9c5c3718d58e0ecac20f9c0c278f46370", "project_import", "related", "3a544d18552d79c56d621abe5b6e4c8378fcc2964e67d897278eebfcfa5c6d79"),
    "CR1REF:SMF-CH-CRITICISM-VS-SCORE-001:AUTHORITATIVE:01": _authority_contract("SMF-CH-CRITICISM-VS-SCORE-001", "594c59e440b04e72f45382da8d7557d885f9bedc823f2a5256a234bd8a52e6a3", "source_interpretation", "authoritative", "9e51eb267fb6f62b62b5fce175f100a8bda8bf990434e581ba3e55213e76caa9"),
    "CR1REF:SMF-CH-CRITICISM-VS-SCORE-001:RELATED:01": _authority_contract("SMF-CH-CRITICISM-VS-SCORE-001", "594c59e440b04e72f45382da8d7557d885f9bedc823f2a5256a234bd8a52e6a3", "source_interpretation", "related", "11a7a7e671e8a52a61543095964111ee370c50dd18018f4c8c4bbf4d50b93f3d"),
    "CR1REF:SMF-CH-PROBLEM-ATTENTION-VALUE-001:RELATED:01": _authority_contract("SMF-CH-PROBLEM-ATTENTION-VALUE-001", "3dec79588ae9f5aad74d1a0fab8f074e8623b39dd6403ae328591a87f8ba81dd", "project_import", "related", "957cbbf8ac1f11fa123fadf0d44f219424696eee4824908637d0412a20f7fc10"),
    "CR1REF:SMF-CH-AUTHORSHIP-VS-OUTPUT-001:AUTHORITATIVE:01": _authority_contract("SMF-CH-AUTHORSHIP-VS-OUTPUT-001", "4a7092d45a3f6255111120b8ad950bffa51898f65b44b2afd62692202017ff87", "source_interpretation", "authoritative", "af05f107b3c318eb144c2438c7f9358f5c56ba6f422f08c776bb44706efe7df8"),
    "CR1REF:SMF-CH-AUTHORSHIP-VS-OUTPUT-001:RELATED:01": _authority_contract("SMF-CH-AUTHORSHIP-VS-OUTPUT-001", "4a7092d45a3f6255111120b8ad950bffa51898f65b44b2afd62692202017ff87", "source_interpretation", "related", "58abec8b4650f9cce466ee695f39ed4f39c1ce8bf47b78cdc240b4e4d82cf3ac"),
    "CR1REF:SMF-CH-SUSPEND-UNRESOLVED-001:RELATED:01": _authority_contract("SMF-CH-SUSPEND-UNRESOLVED-001", "6d7f84bd283eea4af28b436aaf1855f51037a737f88bae47756441e6176d9fd5", "project_import", "related", "39ec21d5643cba0d4f03f4164e9cb456f37fbfd5e4aed3b081afc1b15c157ba1"),
    "CR1REF:SMF-CH-OVERLAPPING-EPISODES-001:RELATED:01": _authority_contract("SMF-CH-OVERLAPPING-EPISODES-001", "0416e2788b89255b40a2045d5ba3bb166a15ad9f9ac3f43aec29d032bfa51559", "project_import", "related", "8230e26efe5156304263069a11835690593660af660a132be2e1e66b63cbfc98"),
    "CR1REF:SMF-CH-FINITE-HISTORY-DISPOSITION-001:AUTHORITATIVE:01": _authority_contract("SMF-CH-FINITE-HISTORY-DISPOSITION-001", "4d8c6124bd9ce357c842416995bbfe43476b212eec923a88b48802a22e88a435", "source_interpretation", "authoritative", "c2f1b003c8d9d543c09df9b410602416a6d8f0515a6c528b00f0faf4fdff93f6"),
    "CR1REF:SMF-CH-FINITE-HISTORY-DISPOSITION-001:RELATED:01": _authority_contract("SMF-CH-FINITE-HISTORY-DISPOSITION-001", "4d8c6124bd9ce357c842416995bbfe43476b212eec923a88b48802a22e88a435", "source_interpretation", "related", "4fda06f4692e386c2d28509a198538acfbf4be5f1ca08ce551c75492561d210d"),
    "CR1REF:SMF-CH-ROLE-RELABEL-TWIN-001:AUTHORITATIVE:01": _authority_contract("SMF-CH-ROLE-RELABEL-TWIN-001", "da831c05dff819983d64e065947c9ec71d931e2df9b24fb677690b597e0c7abe", "source_interpretation", "authoritative", "b59d43f3b6fef15a5c9034cf5049d16eac7c8c21947d727ac0820acf06706458"),
    "CR1REF:SMF-CH-SEMANTIC-PHYSICAL-MAPPING-001:AUTHORITATIVE:01": _authority_contract("SMF-CH-SEMANTIC-PHYSICAL-MAPPING-001", "7fe2c1f1f4cbfaf244a569c8f347b47d4f5df9979def4409d6fb1c300d7da283", "source_interpretation", "authoritative", "6feb1455396fa44817576574e655c5454199bf77254ae11a03e8c7ffb061ad1a"),
    "CR1REF:SMF-RI-ATTENTION-REALIZATION-001:RELATED:01": _authority_contract("SMF-RI-ATTENTION-REALIZATION-001", "25eac71b07f8084f851b4c0f41ea02be96c72dd3b28a3fd4463c1a1aa5ccfff1", "project_import", "related", "1e87a1f6324a0a8db80fcaab6111b5ac742f94842bc4df2edcd2bffb26685f3e"),
    "CR1REF:SMF-RI-CONJECTURE-PRECEDENCE-001:RELATED:01": _authority_contract("SMF-RI-CONJECTURE-PRECEDENCE-001", "96e177834cd30a187953b096cb789f74f1cbce42afb389481164b7b0a2d7e31c", "project_import", "related", "27b845d94d5b7f9b9fdc13ff4a2ae0bbd31ec6c610aafac11f58ed77923070ff"),
    "CR1REF:SMF-RI-SUSPENSION-STATE-001:RELATED:01": _authority_contract("SMF-RI-SUSPENSION-STATE-001", "2e11288a31b27b989007b83ba4ff0a8aae395b56aeb572de5b07ea7128d14870", "project_import", "related", "a6476938d25bf57393e7f10613ee838265f57ad80747b1af20ccb67a02aeb128"),
    "CR1REF:SMF-RI-EPISODE-OVERLAP-001:RELATED:01": _authority_contract("SMF-RI-EPISODE-OVERLAP-001", "562e65462f898fb8acf66933d01224c2776ce1684d757e2f5971949cc3fb705b", "project_import", "related", "246e110cc6d9601f559f8e964a37388b44d690702d46385d1578978679865948"),
    "CR1REF:SMF-RI-AUTHORSHIP-CREDIT-001:AUTHORITATIVE:01": _authority_contract("SMF-RI-AUTHORSHIP-CREDIT-001", "b92d2ac0e54003da0d22ecb4dbddd55ad041fdbe4ced40faaea521179cfa5f21", "source_interpretation", "authoritative", "6162f99ee649f7946b2cd80fa47746c2a36d76392284584b5d4b6b732cb8843d"),
    "CR1REF:SMF-RI-DISPOSITION-EVIDENCE-001:AUTHORITATIVE:01": _authority_contract("SMF-RI-DISPOSITION-EVIDENCE-001", "ffba4b5694d2f7040245605e6949655a090ec6a941a87d59b824dbf3d16af22b", "source_interpretation", "authoritative", "2b0693e1126202cf76d03be0ed94aa6cd1726e0a174670e32a1808379e224227"),
    "CR1REF:SMF-RI-ROLE-REALIZATION-001:AUTHORITATIVE:01": _authority_contract("SMF-RI-ROLE-REALIZATION-001", "c46df690442239b388e6374204534fa0db9b0bc1104bee948e22fd5270fd4760", "source_interpretation", "authoritative", "a6e14f8342ace2c3428411d969e0178bd1e1db520ecf60ee9c6de49857ac377d"),
    "CR1REF:SMF-RI-SEMANTIC-PHYSICAL-BRIDGE-001:AUTHORITATIVE:01": _authority_contract("SMF-RI-SEMANTIC-PHYSICAL-BRIDGE-001", "4bd6325dfac2499c6b9903d835d4698ebda828611e2d3814356bc19ddae500ba", "source_interpretation", "authoritative", "e8afe1dba6d335f3e3e91e3761738b5e2f9a2ec18ca3a6be5e836758f989fca6"),
    "CR1REF:SMF-RI-ANTIINDUCTIVE-PRIORITY-001:RELATED:01": _authority_contract("SMF-RI-ANTIINDUCTIVE-PRIORITY-001", "cd625de9fa899171ad49913fdb97d323ac6e8d6970d05485265f269b06f5a71e", "project_import", "related", "82cf39ce787774d8888e1b1996de7850f1ade1260334e4ffab6de9713fa9968b"),
    "CR1REF:SMF-RI-EXPLANATION-INTERPRETATION-001:AUTHORITATIVE:01": _authority_contract("SMF-RI-EXPLANATION-INTERPRETATION-001", "3077e47baeaed56d9fbedd32d109753881654bacb1031f9b8344d4a21cbf1bd3", "source_interpretation", "authoritative", "fb83d0f0d67a42ce9a8a2bcca567b3d333297d81f722635782eda51f9116ae2e"),
})
_REFERENCE_KEYS = frozenset({"$ref"})
_FORBIDDEN_RESOURCE_KEYS = frozenset({"$anchor", "$dynamicAnchor", "$dynamicRef"})
_SINGLE_SCHEMA_KEYWORDS = frozenset(
    {
        "additionalProperties",
        "contains",
        "contentSchema",
        "else",
        "if",
        "items",
        "not",
        "propertyNames",
        "then",
        "unevaluatedItems",
        "unevaluatedProperties",
    }
)
_SCHEMA_ARRAY_KEYWORDS = frozenset({"allOf", "anyOf", "oneOf", "prefixItems"})
_SCHEMA_MAP_KEYWORDS = frozenset(
    {"$defs", "dependentSchemas", "patternProperties", "properties"}
)


def _registry_from_schemas(
    schemas: Mapping[str, Mapping[str, Any]],
) -> Registry[Any]:
    registry: Registry[Any] = Registry(retrieve=_deny_retrieval)
    for schema in schemas.values():
        registry = registry.with_resource(
            schema["$id"],
            Resource.from_contents(schema),
        )
    return registry.crawl()


def _deny_retrieval(uri: str) -> Resource[Any]:
    """Make the local-only policy explicit even if library defaults change."""

    raise NoSuchResource(ref=uri)


def _stable_path(parts: object) -> str:
    encoded: list[str] = []
    for part in parts:  # type: ignore[union-attr]
        token = str(part).replace("~", "~0").replace("/", "~1")
        encoded.append(token)
    return "/" + "/".join(encoded) if encoded else "/"


def _schema_references(
    node: Any,
    base_uri: str,
    *,
    root: bool = True,
) -> list[tuple[str, str]]:
    """Return references from schema-valued positions, never literal data."""

    found: list[tuple[str, str]] = []
    if type(node) is bool:
        return found
    if type(node) is not dict:
        return found
    forbidden = sorted(_FORBIDDEN_RESOURCE_KEYS.intersection(node))
    if forbidden:
        raise RecordError(
            "the local v0.1 schema registry forbids " + ", ".join(forbidden)
        )
    if not root and "$id" in node:
        raise RecordError(
            "nested $id is forbidden in the local v0.1 schema registry; "
            "declare a separate schema file instead"
        )
    for key in _REFERENCE_KEYS:
        if key in node:
            value = node[key]
            if type(value) is not str or not value:
                raise RecordError(f"schema {key} must be a non-empty string")
            found.append((base_uri, value))
    for key in _SINGLE_SCHEMA_KEYWORDS:
        if key in node:
            found.extend(_schema_references(node[key], base_uri, root=False))
    for key in _SCHEMA_ARRAY_KEYWORDS:
        values = node.get(key)
        if type(values) is list:
            for value in values:
                found.extend(_schema_references(value, base_uri, root=False))
    for key in _SCHEMA_MAP_KEYWORDS:
        values = node.get(key)
        if type(values) is dict:
            for value in values.values():
                found.extend(_schema_references(value, base_uri, root=False))
    return found


def _unique_ids(values: list[str], where: str) -> None:
    if len(values) != len(set(values)):
        raise RecordError(f"{where} identifiers must be unique")


def _record_array(instance: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = instance.get(key)
    if type(value) is not list:
        raise RecordError(f"semantic-forge corpus {key} must be an array")
    checked: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if type(item) is not dict:
            raise RecordError(
                f"semantic-forge corpus {key}[{index}] must be an object"
            )
        checked.append(item)
    return checked


def _validate_annotation_prose_boundaries(
    *annotation_collections: tuple[str, list[dict[str, Any]]],
) -> None:
    """Keep editorial titles and boundary notes mechanically non-authoritative."""

    for collection_name, annotations in annotation_collections:
        for index, annotation in enumerate(annotations):
            where = f"semantic-forge corpus {collection_name}[{index}]"
            if annotation.get("annotation_prose_status") != _ANNOTATION_PROSE_STATUS:
                raise RecordError(
                    f"{where} annotation prose must remain unreviewed and "
                    "non-authoritative"
                )
            if (
                annotation.get("annotation_prose_semantic_effect")
                != _ANNOTATION_PROSE_SEMANTIC_EFFECT
            ):
                raise RecordError(
                    f"{where} annotation prose must have no semantic effect"
                )


def _validate_authority_references(
    *,
    challenges: list[dict[str, Any]],
    issues: list[dict[str, Any]],
    challenge_annotations: list[dict[str, Any]],
    issue_annotations: list[dict[str, Any]],
) -> None:
    """Resolve every typed source reference against immutable local contracts."""

    try:
        inventory_bytes = _IDENTIFIER_INVENTORY_PATH.read_bytes()
    except OSError as exc:
        raise RecordError(
            f"cannot read the CR-1.0 identifier inventory: {exc}"
        ) from exc
    if bytes_digest(inventory_bytes) != _PINNED_IDENTIFIER_INVENTORY_SHA256:
        raise RecordError("the CR-1.0 identifier inventory digest changed")

    subjects: dict[str, dict[str, Any]] = {}
    for record, id_field in (
        *((record, "challenge_id") for record in challenges),
        *((record, "issue_id") for record in issues),
    ):
        record_id = record.get(id_field)
        if type(record_id) is not str:
            raise RecordError(f"corpus subject requires string {id_field}")
        subjects[record_id] = record

    seen_reference_ids: list[str] = []
    for collection_name, annotations in (
        ("challenge_annotations", challenge_annotations),
        ("research_issue_annotations", issue_annotations),
    ):
        for annotation_index, annotation in enumerate(annotations):
            where = f"semantic-forge corpus {collection_name}[{annotation_index}]"
            subject_id = annotation.get("record_id")
            if type(subject_id) is not str or subject_id not in subjects:
                raise RecordError(f"{where} has no exact runtime subject")
            subject_sha256 = bytes_digest(canonical_bytes(subjects[subject_id]))
            basis_kind = annotation.get("basis_kind")
            source_basis = annotation.get("source_basis")
            if type(source_basis) is not dict:
                raise RecordError(f"{where}.source_basis must be an object")
            for field, relationship in (
                ("authoritative_refs", "authoritative"),
                ("related_authority_refs", "related"),
            ):
                references = source_basis.get(field)
                if type(references) is not list:
                    raise RecordError(f"{where}.source_basis.{field} must be an array")
                for reference_index, reference in enumerate(references):
                    reference_where = (
                        f"{where}.source_basis.{field}[{reference_index}]"
                    )
                    if type(reference) is not dict:
                        raise RecordError(f"{reference_where} must be an object")
                    reference_id = reference.get("reference_id")
                    if type(reference_id) is not str:
                        raise RecordError(f"{reference_where}.reference_id must be a string")
                    try:
                        contract = _AUTHORITY_REFERENCE_CONTRACTS[reference_id]
                    except KeyError as exc:
                        raise RecordError(
                            f"{reference_where} uses an unregistered authority reference ID"
                        ) from exc
                    if contract.subject_id != subject_id:
                        raise RecordError(
                            f"{reference_where} is registered to a different subject"
                        )
                    if contract.subject_sha256 != subject_sha256:
                        raise RecordError(
                            f"{reference_where} subject content differs from its registered contract"
                        )
                    if contract.basis_kind != basis_kind:
                        raise RecordError(
                            f"{reference_where} cannot change its registered claim-kind boundary"
                        )
                    if contract.relationship != relationship:
                        raise RecordError(
                            f"{reference_where} cannot change its registered reference relationship"
                        )
                    if bytes_digest(canonical_bytes(reference)) != contract.reference_sha256:
                        raise RecordError(
                            f"{reference_where} locator, pages, source IDs, or use differ "
                            "from the registered immutable reference"
                        )

                    source_record_ids = reference.get("source_record_ids")
                    pages = reference.get("physical_pdf_pages")
                    if type(source_record_ids) is not list or type(pages) is not list:
                        raise RecordError(f"{reference_where} has invalid source resolution fields")
                    for source_record_id in source_record_ids:
                        try:
                            record_pages = _CR1_SOURCE_RECORD_PAGES[source_record_id]
                        except (KeyError, TypeError) as exc:
                            raise RecordError(
                                f"{reference_where} names an unregistered CR-1.0 source record"
                            ) from exc
                        if not set(pages).intersection(record_pages):
                            raise RecordError(
                                f"{reference_where} does not cite a page for source record "
                                f"{source_record_id}"
                            )
                    allowed_pages = {
                        page
                        for source_record_id in source_record_ids
                        for page in _CR1_SOURCE_RECORD_PAGES[source_record_id]
                    }
                    if any(page not in allowed_pages for page in pages):
                        raise RecordError(
                            f"{reference_where} cites a page outside its source records"
                        )
                    seen_reference_ids.append(reference_id)
    _unique_ids(seen_reference_ids, "corpus authority reference")


def _validate_corpus_runtime_contract(instance: Any) -> None:
    """Enforce parser and cross-record invariants JSON Schema cannot express."""

    if type(instance) is not dict:
        raise RecordError("semantic-forge corpus must be an object")
    challenges = _record_array(instance, "challenges")
    issues = _record_array(instance, "research_issues")
    challenge_annotations = _record_array(instance, "challenge_annotations")
    issue_annotations = _record_array(instance, "research_issue_annotations")
    _validate_annotation_prose_boundaries(
        ("challenge_annotations", challenge_annotations),
        ("research_issue_annotations", issue_annotations),
    )
    parsed_challenges = [parse_minimal_pair_challenge(item) for item in challenges]
    parsed_issues = [parse_issue(item) for item in issues]
    challenge_ids = [item.challenge_id for item in parsed_challenges]
    issue_ids = [item.issue_id for item in parsed_issues]
    challenge_annotation_ids = [
        item.get("record_id") for item in challenge_annotations
    ]
    issue_annotation_ids = [
        item.get("record_id") for item in issue_annotations
    ]
    if any(type(value) is not str for value in challenge_annotation_ids):
        raise RecordError("corpus challenge annotations require string record_id")
    if any(type(value) is not str for value in issue_annotation_ids):
        raise RecordError("corpus research-issue annotations require string record_id")
    _unique_ids(challenge_ids, "corpus challenge")
    _unique_ids(issue_ids, "corpus research issue")
    _unique_ids(challenge_annotation_ids, "corpus challenge annotation")
    _unique_ids(issue_annotation_ids, "corpus research-issue annotation")
    if set(challenge_ids) != set(challenge_annotation_ids):
        raise RecordError("corpus challenge annotation coverage must be one-to-one")
    if set(issue_ids) != set(issue_annotation_ids):
        raise RecordError("corpus research-issue annotation coverage must be one-to-one")
    annotation_by_id = {
        annotation["record_id"]: annotation for annotation in challenge_annotations
    }
    for challenge in challenges:
        challenge_id = challenge["challenge_id"]
        oracle = challenge.get("oracle")
        if type(oracle) is not str or not oracle.startswith("status=") or ";" not in oracle:
            raise RecordError(
                f"corpus challenge {challenge_id} oracle lacks an explicit status prefix"
            )
        embedded_status = oracle.removeprefix("status=").split(";", 1)[0]
        annotation_status = annotation_by_id[challenge_id].get("oracle_status")
        if embedded_status != annotation_status:
            raise RecordError(
                f"corpus challenge {challenge_id} oracle status contradicts its annotation"
            )
    _validate_authority_references(
        challenges=challenges,
        issues=issues,
        challenge_annotations=challenge_annotations,
        issue_annotations=issue_annotations,
    )


@dataclass(frozen=True)
class LocalSchemaCatalog:
    """A checked, immutable view of a fail-closed local schema registry."""

    schema_dir: Path
    _schema_sources: Mapping[str, str]

    @property
    def schemas(self) -> Mapping[str, Mapping[str, Any]]:
        """Return a disposable snapshot; mutations cannot alter the catalog."""

        return MappingProxyType(
            {
                name: loads_strict(source)
                for name, source in self._schema_sources.items()
            }
        )

    @property
    def registry(self) -> Registry[Any]:
        """Return a fresh registry whose mutable contents are not retained."""

        return _registry_from_schemas(self.schemas)

    @property
    def schema_names(self) -> tuple[str, ...]:
        return tuple(self._schema_sources)

    def validator(self, schema_name: str) -> Draft202012Validator:
        if type(schema_name) is not str or not schema_name:
            raise RecordError("schema_name must be a non-empty string")
        schemas = self.schemas
        try:
            schema = schemas[schema_name]
        except KeyError as exc:
            raise RecordError(f"unregistered local schema: {schema_name!r}") from exc
        return Draft202012Validator(
            schema,
            registry=_registry_from_schemas(schemas),
            format_checker=Draft202012Validator.FORMAT_CHECKER,
        )

    def has_full_record_runtime_contract(self, schema_name: str) -> bool:
        """Report whether ``validate`` dispatches a full-record parser.

        Runtime dispatch is keyed by the selected schema's canonical ``$id``,
        not by its local filename.  Keeping this query beside the dispatch
        logic prevents callers from overstating coverage for lookalike custom
        schemas that reuse a canonical filename.
        """

        schemas = self.schemas
        try:
            schema = schemas[schema_name]
        except KeyError as exc:
            raise RecordError(f"unregistered local schema: {schema_name!r}") from exc
        return schema["$id"] in _FULL_RECORD_RUNTIME_SCHEMA_IDS

    def validate(self, instance: Any, schema_name: str) -> None:
        """Validate an in-memory instance and report deterministic locations."""

        try:
            errors = sorted(
                self.validator(schema_name).iter_errors(instance),
                key=lambda error: (
                    _stable_path(error.absolute_path),
                    _stable_path(error.absolute_schema_path),
                    error.message,
                ),
            )
        except RecursionError as exc:
            raise RecordError(
                f"{schema_name} validation exceeded the supported schema recursion"
            ) from exc
        if errors:
            shown = errors[:10]
            details = "; ".join(
                f"{_stable_path(error.absolute_path)}: {error.message}"
                for error in shown
            )
            omitted = len(errors) - len(shown)
            if omitted:
                details += f"; ... {omitted} additional validation error(s)"
            raise RecordError(
                f"{schema_name} rejected the JSON instance with "
                f"{len(errors)} error(s): {details}"
            )
        schema_id = self.schemas[schema_name]["$id"]
        if schema_id == _CHALLENGE_SCHEMA_ID:
            parse_minimal_pair_challenge(instance)
        elif schema_id == _RESEARCH_ISSUE_SCHEMA_ID:
            parse_issue(instance)
        elif schema_id == _CORPUS_SCHEMA_ID:
            _validate_corpus_runtime_contract(instance)
        elif schema_id == _RESEARCH_LEDGER_SCHEMA_ID:
            # Imported lazily so the general offline registry does not acquire
            # a module-level dependency on every record family it validates.
            # The research module does not import this module, so this path is
            # cycle-free and enforces the hashes and cross-record invariants
            # that JSON Schema alone cannot express.
            from .research import parse_research_ledger

            parse_research_ledger(instance)


def load_local_schema_catalog(
    schema_dir: Path = DEFAULT_SCHEMA_DIR,
) -> LocalSchemaCatalog:
    """Strict-load and check every ``*.schema.json`` file in one directory."""

    if not isinstance(schema_dir, Path):
        raise TypeError("schema_dir must be pathlib.Path")
    paths = tuple(sorted(schema_dir.glob("*.schema.json")))
    if not paths:
        raise RecordError(f"no local JSON schemas found in {schema_dir}")

    mutable: dict[str, dict[str, Any]] = {}
    schema_ids: set[str] = set()
    resources: list[tuple[str, Resource[Any]]] = []
    for path in paths:
        raw = load_strict(path)
        if type(raw) is not dict:
            raise RecordError(f"schema must be a JSON object: {path}")
        if raw.get("$schema") != _DRAFT_2020_12:
            raise RecordError(f"schema must declare JSON Schema 2020-12: {path}")
        schema_id = raw.get("$id")
        if type(schema_id) is not str or not schema_id:
            raise RecordError(f"schema must declare a non-empty $id: {path}")
        try:
            parsed_id = urlsplit(schema_id)
        except ValueError as exc:
            raise RecordError(f"invalid schema $id URI: {path}") from exc
        if not parsed_id.scheme or parsed_id.fragment:
            raise RecordError(f"schema $id must be absolute and fragment-free: {path}")
        if schema_id in schema_ids:
            raise RecordError(f"duplicate schema $id: {schema_id}")
        try:
            Draft202012Validator.check_schema(raw)
            resource = Resource.from_contents(raw)
        except (SchemaError, CannotDetermineSpecification) as exc:
            raise RecordError(f"invalid JSON Schema {path}: {exc}") from exc
        mutable[path.name] = raw
        schema_ids.add(schema_id)
        resources.append((schema_id, resource))

    registry: Registry[Any] = Registry(retrieve=_deny_retrieval)
    for schema_id, resource in resources:
        registry = registry.with_resource(schema_id, resource)
    registry = registry.crawl()

    reference_errors = (
        InvalidAnchor,
        NoSuchAnchor,
        NoSuchResource,
        PointerToNowhere,
        Unresolvable,
        Unretrievable,
        ValueError,
    )
    for schema_name, schema in mutable.items():
        root_id = schema["$id"]
        for base_uri, reference in _schema_references(schema, root_id):
            try:
                registry.resolver(base_uri).lookup(reference)
            except reference_errors as exc:
                try:
                    resolved = urljoin(base_uri, reference)
                except ValueError:
                    resolved = reference
                raise RecordError(
                    f"schema {schema_name} has an unregistered or invalid local "
                    f"reference {resolved!r}"
                ) from exc

    frozen = MappingProxyType(
        {
            name: json.dumps(
                schema,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            for name, schema in sorted(mutable.items())
        }
    )
    return LocalSchemaCatalog(
        schema_dir=schema_dir,
        _schema_sources=frozen,
    )


def validate_semantic_forge_file(
    instance_path: Path,
    *,
    schema_name: str = "corpus.schema.json",
    schema_dir: Path = DEFAULT_SCHEMA_DIR,
) -> Any:
    """Strict-load a JSON file and validate it using only registered schemas."""

    if not isinstance(instance_path, Path):
        raise TypeError("instance_path must be pathlib.Path")
    instance = load_strict(instance_path)
    return validate_semantic_forge_instance(
        instance,
        schema_name=schema_name,
        schema_dir=schema_dir,
    )


def validate_semantic_forge_instance(
    instance: Any,
    *,
    schema_name: str = "corpus.schema.json",
    schema_dir: Path = DEFAULT_SCHEMA_DIR,
    catalog: LocalSchemaCatalog | None = None,
) -> Any:
    """Validate an already parsed value, preserving a caller's byte snapshot."""

    active_catalog = catalog or load_local_schema_catalog(schema_dir)
    active_catalog.validate(instance, schema_name)
    return instance
