"""Strict structural validation for CR-EIB pilot records."""

from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Any

from .canonical import domain_digest
from .errors import PolicyViolation, RecordError

HEX64 = re.compile(r"^[0-9a-f]{64}$")
SOURCE_ID = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Za-z0-9]+)+$")


def _object(value: Any, where: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise RecordError(f"{where} must be an object")
    return value


def _exact_keys(value: dict[str, Any], keys: set[str], where: str) -> None:
    actual = set(value)
    if actual != keys:
        missing = sorted(keys - actual)
        extra = sorted(actual - keys)
        raise RecordError(f"{where} keys differ; missing={missing}, extra={extra}")


def _string(value: Any, where: str, *, nonempty: bool = True) -> str:
    if type(value) is not str or (nonempty and not value):
        raise RecordError(f"{where} must be a{' non-empty' if nonempty else ''} string")
    return value


def _integer(value: Any, where: str, *, minimum: int | None = None) -> int:
    if type(value) is not int:
        raise RecordError(f"{where} must be an integer")
    if minimum is not None and value < minimum:
        raise RecordError(f"{where} must be at least {minimum}")
    return value


def _boolean(value: Any, where: str) -> bool:
    if type(value) is not bool:
        raise RecordError(f"{where} must be a Boolean")
    return value


def _list(value: Any, where: str) -> list[Any]:
    if type(value) is not list:
        raise RecordError(f"{where} must be an array")
    return value


def _digest(value: Any, where: str, *, prefixed: bool = False) -> str:
    text = _string(value, where)
    candidate = text.removeprefix("sha256:") if prefixed else text
    if not HEX64.fullmatch(candidate):
        raise RecordError(f"{where} must be a lowercase SHA-256 digest")
    if prefixed and not text.startswith("sha256:"):
        raise RecordError(f"{where} must start with 'sha256:'")
    return text


def _source_id(value: Any, where: str) -> str:
    text = _string(value, where)
    if not SOURCE_ID.fullmatch(text):
        raise RecordError(f"{where} is not one explicit declaration identifier: {text!r}")
    return text


def _safe_relative(value: Any, where: str) -> str:
    text = _string(value, where)
    path = PurePosixPath(text)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise RecordError(f"{where} must be a normalized repository-relative path")
    return text


def _bbox(value: Any, where: str, page_size: list[int]) -> list[int]:
    coords = _list(value, where)
    if len(coords) != 4:
        raise RecordError(f"{where} must contain four coordinates")
    x0, y0, x1, y1 = (_integer(item, f"{where}[{index}]", minimum=0) for index, item in enumerate(coords))
    if not (x0 < x1 <= page_size[0] and y0 < y1 <= page_size[1]):
        raise RecordError(f"{where} is outside the page or is not ordered")
    return coords


def validate_manifest(value: Any) -> dict[str, Any]:
    manifest = _object(value, "manifest")
    _exact_keys(
        manifest,
        {
            "schema_version",
            "document_id",
            "semantic_authority",
            "supplied_filename",
            "sha256",
            "byte_length",
            "page_count",
            "page_size_millipoints",
            "active_span",
            "authority_file_committed",
        },
        "manifest",
    )
    if manifest["schema_version"] != "cr-eib.source-manifest.v1":
        raise RecordError("unknown source-manifest schema version")
    _string(manifest["document_id"], "manifest.document_id")
    if _boolean(manifest["semantic_authority"], "manifest.semantic_authority") is not True:
        raise PolicyViolation("the pilot manifest must identify the PDF as semantic authority")
    _string(manifest["supplied_filename"], "manifest.supplied_filename")
    _digest(manifest["sha256"], "manifest.sha256")
    _integer(manifest["byte_length"], "manifest.byte_length", minimum=1)
    _integer(manifest["page_count"], "manifest.page_count", minimum=1)
    page_size = _list(manifest["page_size_millipoints"], "manifest.page_size_millipoints")
    if len(page_size) != 2:
        raise RecordError("manifest.page_size_millipoints must contain width and height")
    for index, coordinate in enumerate(page_size):
        _integer(coordinate, f"manifest.page_size_millipoints[{index}]", minimum=1)
    span = _object(manifest["active_span"], "manifest.active_span")
    _exact_keys(span, {"physical_pdf_pages", "printed_folios"}, "manifest.active_span")
    for name in ("physical_pdf_pages", "printed_folios"):
        pair = _list(span[name], f"manifest.active_span.{name}")
        if len(pair) != 2 or any(type(item) is not int for item in pair) or pair[0] > pair[1]:
            raise RecordError(f"manifest.active_span.{name} must be an ordered integer pair")
    if _boolean(manifest["authority_file_committed"], "manifest.authority_file_committed") is not False:
        raise PolicyViolation("the authority PDF must not be committed by this pilot")
    return manifest


def validate_anchor(value: Any, manifest: dict[str, Any]) -> dict[str, Any]:
    record = _object(value, "anchor")
    _exact_keys(record, {"anchor_digest", "payload"}, "anchor")
    _digest(record["anchor_digest"], "anchor.anchor_digest", prefixed=True)
    payload = _object(record["payload"], "anchor.payload")
    _exact_keys(
        payload,
        {
            "schema_version",
            "record_version",
            "supersedes",
            "authority",
            "source_namespace",
            "authoritative_id",
            "proxy_ids",
            "clause_family",
            "title_raw",
            "locator",
            "transcription",
            "source_status",
            "dependencies",
            "source_inferential_status",
            "provenance",
        },
        "anchor.payload",
    )
    if payload["schema_version"] != "cr-eib.source-anchor.v1":
        raise RecordError("unknown source-anchor schema version")
    _integer(payload["record_version"], "anchor.payload.record_version", minimum=1)
    if payload["supersedes"] is not None:
        _digest(payload["supersedes"], "anchor.payload.supersedes", prefixed=True)

    authority = _object(payload["authority"], "anchor.payload.authority")
    authority_keys = {
        "document_id",
        "supplied_filename",
        "sha256",
        "byte_length",
        "page_count",
        "page_size_millipoints",
    }
    _exact_keys(authority, authority_keys, "anchor.payload.authority")
    for key in authority_keys:
        if authority[key] != manifest[key]:
            raise RecordError(f"anchor authority field does not match manifest: {key}")

    if payload["source_namespace"] != manifest["document_id"]:
        raise RecordError("anchor source namespace does not match manifest document_id")
    authoritative_id = _source_id(payload["authoritative_id"], "anchor.payload.authoritative_id")
    proxy_ids = _list(payload["proxy_ids"], "anchor.payload.proxy_ids")
    for index, proxy_id in enumerate(proxy_ids):
        _source_id(proxy_id, f"anchor.payload.proxy_ids[{index}]")
    if len(proxy_ids) != len(set(proxy_ids)):
        raise RecordError("anchor proxy identifiers must be unique")
    if payload["clause_family"] not in {"definition", "theorem"}:
        raise RecordError("anchor.payload.clause_family must be definition or theorem")
    _string(payload["title_raw"], "anchor.payload.title_raw")

    locator = _object(payload["locator"], "anchor.payload.locator")
    _exact_keys(
        locator,
        {
            "physical_pdf_page",
            "pdf_page_index_zero_based",
            "printed_footer_page",
            "section_raw",
            "coordinate_system",
            "page_rotation_degrees",
            "tight_bbox_millipoints",
            "regions",
        },
        "anchor.payload.locator",
    )
    physical = _integer(locator["physical_pdf_page"], "anchor.payload.locator.physical_pdf_page", minimum=1)
    index = _integer(locator["pdf_page_index_zero_based"], "anchor.payload.locator.pdf_page_index_zero_based", minimum=0)
    if physical != index + 1:
        raise RecordError("physical page and zero-based page index disagree")
    _integer(locator["printed_footer_page"], "anchor.payload.locator.printed_footer_page", minimum=1)
    if locator["section_raw"] is not None:
        _string(locator["section_raw"], "anchor.payload.locator.section_raw")
    if locator["coordinate_system"] != "top-left CropBox millipoints":
        raise RecordError("unsupported anchor coordinate system")
    if locator["page_rotation_degrees"] != 0:
        raise RecordError("the CR-1.0 pilot pages must have zero rotation")
    page_size = manifest["page_size_millipoints"]
    tight_bbox = _bbox(locator["tight_bbox_millipoints"], "anchor.payload.locator.tight_bbox_millipoints", page_size)
    regions = _list(locator["regions"], "anchor.payload.locator.regions")
    if not regions:
        raise RecordError("anchor must contain at least one named region")
    region_names: set[str] = set()
    for region_index, region_value in enumerate(regions):
        region = _object(region_value, f"anchor.payload.locator.regions[{region_index}]")
        _exact_keys(region, {"name", "bbox_millipoints"}, f"anchor.payload.locator.regions[{region_index}]")
        name = _string(region["name"], f"anchor.payload.locator.regions[{region_index}].name")
        if name in region_names:
            raise RecordError("anchor region names must be unique")
        region_names.add(name)
        box = _bbox(region["bbox_millipoints"], f"anchor.payload.locator.regions[{region_index}].bbox_millipoints", page_size)
        if box[0] < tight_bbox[0] or box[1] < tight_bbox[1] or box[2] > tight_bbox[2] or box[3] > tight_bbox[3]:
            raise RecordError("anchor region lies outside the tight clause bbox")

    transcription = _object(payload["transcription"], "anchor.payload.transcription")
    _exact_keys(transcription, {"literal_word_snapshot", "reviewed_reading", "declared_transformations"}, "anchor.payload.transcription")
    snapshot = _object(transcription["literal_word_snapshot"], "anchor.payload.transcription.literal_word_snapshot")
    _exact_keys(snapshot, {"algorithm", "extractor", "extractor_version", "selection_rule", "word_count", "sha256"}, "anchor.payload.transcription.literal_word_snapshot")
    if snapshot["algorithm"] != "CR-EIB/pdftotext-word-snapshot/v1":
        raise RecordError("unsupported word-snapshot algorithm")
    if snapshot["extractor"] != "pdftotext -bbox":
        raise RecordError("unsupported anchor extractor")
    _string(snapshot["extractor_version"], "anchor snapshot extractor_version")
    if snapshot["selection_rule"] != "word-center-in-tight-bbox; XML document order; round points to millipoints":
        raise RecordError("unsupported word-snapshot selection rule")
    _integer(snapshot["word_count"], "anchor snapshot word_count", minimum=1)
    _digest(snapshot["sha256"], "anchor snapshot sha256")
    reading = _object(transcription["reviewed_reading"], "anchor.payload.transcription.reviewed_reading")
    _exact_keys(reading, {"path", "sha256", "encoding", "unicode_normalization", "eol", "final_newline"}, "anchor.payload.transcription.reviewed_reading")
    _safe_relative(reading["path"], "anchor reviewed-reading path")
    _digest(reading["sha256"], "anchor reviewed-reading sha256")
    if reading["encoding"] != "UTF-8" or reading["unicode_normalization"] != "NFC" or reading["eol"] != "LF":
        raise RecordError("reviewed reading must be UTF-8 NFC with LF line endings")
    if _boolean(reading["final_newline"], "anchor reviewed-reading final_newline") is not True:
        raise RecordError("reviewed reading must declare its final newline")
    transformations = _list(transcription["declared_transformations"], "anchor.payload.transcription.declared_transformations")
    for transformation_index, transformation in enumerate(transformations):
        _string(transformation, f"anchor transformation[{transformation_index}]")

    source_status = _object(payload["source_status"], "anchor.payload.source_status")
    _exact_keys(source_status, {"raw", "assertions", "source_tags"}, "anchor.payload.source_status")
    _string(source_status["raw"], "anchor.payload.source_status.raw")
    assertions = _list(source_status["assertions"], "anchor.payload.source_status.assertions")
    if not assertions:
        raise RecordError("anchor source status must retain at least one assertion")
    for assertion_index, assertion_value in enumerate(assertions):
        assertion = _object(assertion_value, f"anchor source assertion[{assertion_index}]")
        _exact_keys(assertion, {"mark", "scheme", "scope_raw", "parse_status"}, f"anchor source assertion[{assertion_index}]")
        if assertion["mark"] != "R" or assertion["scheme"] != "CR-1.0/source-status":
            raise PolicyViolation("source mark R must remain in the CR-1.0 source-status namespace")
        _string(assertion["scope_raw"], f"anchor source assertion[{assertion_index}].scope_raw")
        if assertion["parse_status"] not in {"parsed", "scope-limited"}:
            raise RecordError("unknown source-mark parse status")
    tags = _list(source_status["source_tags"], "anchor.payload.source_status.source_tags")
    for tag_index, tag in enumerate(tags):
        _source_id(tag, f"anchor source tag[{tag_index}]")
    if len(tags) != len(set(tags)):
        raise RecordError("source tags must be unique and source ordered")

    dependencies = _object(payload["dependencies"], "anchor.payload.dependencies")
    _exact_keys(dependencies, {"source_declared"}, "anchor.payload.dependencies")
    declared = _object(dependencies["source_declared"], "anchor source-declared dependencies")
    _exact_keys(declared, {"raw", "exact_ids", "declared_exhaustive"}, "anchor source-declared dependencies")
    if declared["raw"] is not None:
        _string(declared["raw"], "anchor source-declared dependency text")
    exact_ids = _list(declared["exact_ids"], "anchor source-declared dependency ids")
    for dependency_index, dependency in enumerate(exact_ids):
        _source_id(dependency, f"anchor source dependency[{dependency_index}]")
    if len(exact_ids) != len(set(exact_ids)):
        raise RecordError("source-declared dependencies must be explicit and unique")
    exhaustive = _boolean(declared["declared_exhaustive"], "anchor source-declared exhaustive flag")
    if exhaustive and declared["raw"] is None:
        raise RecordError("an exhaustive source dependency list requires preserved raw text")

    if payload["source_inferential_status"] is not None:
        raise PolicyViolation("source_inferential_status must remain null")
    provenance = _object(payload["provenance"], "anchor.payload.provenance")
    _exact_keys(provenance, {"input_artifact_hashes", "tool_versions"}, "anchor.payload.provenance")
    input_hashes = _list(provenance["input_artifact_hashes"], "anchor provenance input hashes")
    for hash_index, input_hash in enumerate(input_hashes):
        _digest(input_hash, f"anchor provenance input hash[{hash_index}]")
    tools = _object(provenance["tool_versions"], "anchor provenance tool versions")
    for name, version in tools.items():
        _string(name, "anchor provenance tool name")
        _string(version, f"anchor provenance tool {name}")

    expected = domain_digest("CR-EIB/source-anchor/v1", payload)
    if record["anchor_digest"] != expected:
        raise RecordError(f"anchor digest mismatch for {authoritative_id}: expected {expected}")
    return payload


def validate_declaration(value: Any, anchors: dict[str, dict[str, Any]]) -> dict[str, Any]:
    declaration = _object(value, "declaration")
    _exact_keys(
        declaration,
        {
            "schema_version",
            "declaration_id",
            "authoritative_id",
            "source_anchor_digest",
            "mapping_status",
            "source_inferential_status",
            "proposed_inferential_status",
            "parameters",
            "opaque_ports",
            "dependencies",
            "claim_scope",
            "typed_body",
            "evidence_policy",
            "replay",
        },
        "declaration",
    )
    if declaration["schema_version"] != "cr-eib.bridge-declaration.v1":
        raise RecordError("unknown bridge-declaration schema version")
    _source_id(declaration["declaration_id"], "declaration.declaration_id")
    authoritative_id = _source_id(declaration["authoritative_id"], "declaration.authoritative_id")
    anchor_digest = _digest(declaration["source_anchor_digest"], "declaration.source_anchor_digest", prefixed=True)
    if anchor_digest not in anchors:
        raise PolicyViolation(f"declaration references an unresolved anchor: {anchor_digest}")
    anchor = anchors[anchor_digest]
    if anchor["authoritative_id"] != authoritative_id:
        raise PolicyViolation("declaration authoritative_id disagrees with its anchor")
    if declaration["mapping_status"] not in {"candidate", "accepted", "rejected", "blocked"}:
        raise RecordError("unknown declaration mapping status")
    if declaration["source_inferential_status"] is not None:
        raise PolicyViolation("bridge records may not invent a source inferential status")
    proposed = declaration["proposed_inferential_status"]
    if proposed not in {None, "DEF", "IMP", "DER"}:
        raise RecordError("invalid proposed inferential status")

    parameters = _list(declaration["parameters"], "declaration.parameters")
    parameter_names: set[str] = set()
    for parameter_index, parameter_value in enumerate(parameters):
        parameter = _object(parameter_value, f"declaration.parameters[{parameter_index}]")
        _exact_keys(parameter, {"name", "sort", "binding"}, f"declaration.parameters[{parameter_index}]")
        name = _string(parameter["name"], f"declaration.parameters[{parameter_index}].name")
        _string(parameter["sort"], f"declaration.parameters[{parameter_index}].sort")
        if parameter["binding"] != "explicit":
            raise PolicyViolation("all formal parameters must be explicitly bound")
        if name in parameter_names:
            raise RecordError("formal parameter names must be unique")
        parameter_names.add(name)

    opaque_ports = _list(declaration["opaque_ports"], "declaration.opaque_ports")
    opaque_names: set[str] = set()
    for port_index, port_value in enumerate(opaque_ports):
        port = _object(port_value, f"declaration.opaque_ports[{port_index}]")
        _exact_keys(port, {"name", "signature", "binding"}, f"declaration.opaque_ports[{port_index}]")
        name = _string(port["name"], f"declaration.opaque_ports[{port_index}].name")
        _string(port["signature"], f"declaration.opaque_ports[{port_index}].signature")
        if port["binding"] != "model-field":
            raise PolicyViolation("opaque semantic ports must be explicit CRModel fields")
        if name in opaque_names:
            raise RecordError("opaque semantic port names must be unique")
        opaque_names.add(name)

    dependencies = _object(declaration["dependencies"], "declaration.dependencies")
    _exact_keys(dependencies, {"source_declared", "reconstructed_source", "bridge"}, "declaration.dependencies")
    for name in ("source_declared", "reconstructed_source", "bridge"):
        dep_list = _list(dependencies[name], f"declaration.dependencies.{name}")
        for dep_index, dependency in enumerate(dep_list):
            _source_id(dependency, f"declaration.dependencies.{name}[{dep_index}]")
        if len(dep_list) != len(set(dep_list)):
            raise RecordError(f"declaration.dependencies.{name} must be unique")
    if dependencies["source_declared"] != anchor["dependencies"]["source_declared"]["exact_ids"]:
        raise PolicyViolation("declaration source dependencies do not exactly mirror its anchor")
    _string(declaration["claim_scope"], "declaration.claim_scope")

    body = _object(declaration["typed_body"], "declaration.typed_body")
    _exact_keys(body, {"language", "symbol", "path", "sha256", "closed_proposition"}, "declaration.typed_body")
    if body["language"] != "Lean4":
        raise RecordError("the pilot typed body must target Lean4")
    _string(body["symbol"], "declaration.typed_body.symbol")
    _safe_relative(body["path"], "declaration.typed_body.path")
    _digest(body["sha256"], "declaration.typed_body.sha256")
    closed = _boolean(body["closed_proposition"], "declaration.typed_body.closed_proposition")

    policy = _object(declaration["evidence_policy"], "declaration.evidence_policy")
    _exact_keys(policy, {"missing_is_false", "explicit_negative_required_for_countermodel"}, "declaration.evidence_policy")
    if _boolean(policy["missing_is_false"], "declaration evidence missing_is_false") is not False:
        raise PolicyViolation("missing evidence must never be treated as false")
    _boolean(policy["explicit_negative_required_for_countermodel"], "declaration evidence explicit-negative flag")

    replay = _object(declaration["replay"], "declaration.replay")
    _exact_keys(replay, {"status", "tool", "toolchain", "command", "expected_axioms"}, "declaration.replay")
    if replay["status"] not in {"pending-ci", "verified"}:
        raise RecordError("unknown replay status")
    if replay["tool"] != "Lean4" or replay["toolchain"] != "leanprover/lean4:v4.33.1":
        raise PolicyViolation("Lean replay tool and toolchain must remain pinned")
    _string(replay["command"], "declaration.replay.command")
    axioms = _list(replay["expected_axioms"], "declaration.replay.expected_axioms")
    for axiom_index, axiom in enumerate(axioms):
        _string(axiom, f"declaration.replay.expected_axioms[{axiom_index}]")
    if proposed == "DER" and (not closed or axioms):
        raise PolicyViolation("a proposed DER requires a closed proposition and an empty expected-axiom list")
    return declaration
