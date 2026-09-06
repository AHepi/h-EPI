"""Offline, fail-closed JSON Schema validation for the conformance harness.

Every schema in one directory is strict-loaded, checked against the JSON
Schema 2020-12 metaschema, and registered in a registry whose retrieval
function always fails, so validation can never fetch a schema over the
network. Local references must resolve inside that registry.

The checked catalog is memoised per process under a key made of the
directory path and the SHA-256 of every schema file's bytes. A cache hit
requires byte-identical schema files; any change misses the cache and
repeats the complete check. Caching removes repeated work; it never skips a
check that a changed input would need.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import threading
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

from creib.canonical import bytes_digest
from creib.errors import RecordError
from creib.strict_json import loads_strict


DEFAULT_SCHEMA_DIR = Path(__file__).resolve().parents[3] / "forge" / "conformance" / "schema"
_DRAFT_2020_12 = "https://json-schema.org/draft/2020-12/schema"
_FORBIDDEN_RESOURCE_KEYS = frozenset({"$anchor", "$dynamicAnchor", "$dynamicRef"})
_SINGLE_SCHEMA_KEYWORDS = frozenset(
    {"additionalProperties", "contains", "else", "if", "items", "not", "propertyNames", "then", "unevaluatedItems", "unevaluatedProperties"}
)
_SCHEMA_ARRAY_KEYWORDS = frozenset({"allOf", "anyOf", "oneOf", "prefixItems"})
_SCHEMA_MAP_KEYWORDS = frozenset({"$defs", "dependentSchemas", "patternProperties", "properties"})


def _deny_retrieval(uri: str) -> Resource[Any]:
    raise RecordError(f"schema retrieval is disabled; unregistered reference {uri!r}")


def _registry_from_schemas(schemas: Mapping[str, Mapping[str, Any]]) -> Registry[Any]:
    registry: Registry[Any] = Registry(retrieve=_deny_retrieval)
    for schema in schemas.values():
        registry = registry.with_resource(schema["$id"], Resource.from_contents(schema))
    return registry.crawl()


def _schema_references(node: Any, base_uri: str, path: str = "$"):
    """Yield (base_uri, reference) pairs for every ``$ref`` in a schema tree."""

    if isinstance(node, dict):
        forbidden = _FORBIDDEN_RESOURCE_KEYS & set(node)
        if forbidden:
            raise RecordError(f"schema uses unsupported keyword(s) {sorted(forbidden)} at {path}")
        if "$id" in node and path != "$":
            raise RecordError(f"nested $id is not supported at {path}")
        if "$ref" in node:
            if type(node["$ref"]) is not str:
                raise RecordError(f"$ref must be a string at {path}")
            yield base_uri, node["$ref"]
        for key, value in node.items():
            if key in _SINGLE_SCHEMA_KEYWORDS:
                yield from _schema_references(value, base_uri, f"{path}.{key}")
            elif key in _SCHEMA_ARRAY_KEYWORDS and isinstance(value, list):
                for index, item in enumerate(value):
                    yield from _schema_references(item, base_uri, f"{path}.{key}[{index}]")
            elif key in _SCHEMA_MAP_KEYWORDS and isinstance(value, dict):
                for name, item in value.items():
                    yield from _schema_references(item, base_uri, f"{path}.{key}.{name}")


def _stable_path(parts: Any) -> str:
    return "/" + "/".join(str(part) for part in parts)


@dataclass(frozen=True)
class LocalSchemaCatalog:
    """A checked, immutable view of a fail-closed local schema registry."""

    schema_dir: Path
    _schema_sources: Mapping[str, str]
    _checked_schemas: Mapping[str, Mapping[str, Any]]
    _checked_registry: Registry[Any]

    @property
    def schemas(self) -> Mapping[str, Mapping[str, Any]]:
        """Return a disposable snapshot; mutations cannot alter the catalog."""

        return MappingProxyType({name: loads_strict(source) for name, source in self._schema_sources.items()})

    @property
    def schema_names(self) -> tuple[str, ...]:
        return tuple(self._schema_sources)

    @property
    def registry(self) -> Registry[Any]:
        """The checked, retrieval-disabled registry; ``referencing`` registries are immutable."""

        return self._checked_registry

    def validator(self, schema_name: str) -> Draft202012Validator:
        if type(schema_name) is not str or not schema_name:
            raise RecordError("schema_name must be a non-empty string")
        try:
            schema = self._checked_schemas[schema_name]
        except KeyError as exc:
            raise RecordError(f"unregistered local schema: {schema_name!r}") from exc
        return Draft202012Validator(
            schema,
            registry=self._checked_registry,
            format_checker=Draft202012Validator.FORMAT_CHECKER,
        )

    def validate(self, instance: Any, schema_name: str) -> None:
        """Validate an in-memory instance and report deterministic locations."""

        try:
            errors = sorted(
                self.validator(schema_name).iter_errors(instance),
                key=lambda error: (_stable_path(error.absolute_path), _stable_path(error.absolute_schema_path), error.message),
            )
        except RecursionError as exc:
            raise RecordError(f"{schema_name} validation exceeded the supported schema recursion") from exc
        if errors:
            shown = errors[:10]
            details = "; ".join(f"{_stable_path(error.absolute_path)}: {error.message}" for error in shown)
            omitted = len(errors) - len(shown)
            if omitted:
                details += f"; ... {omitted} additional validation error(s)"
            raise RecordError(f"{schema_name} rejected the JSON instance with {len(errors)} error(s): {details}")


_CacheKey = tuple[str, tuple[tuple[str, str], ...]]
_CATALOG_CACHE: dict[_CacheKey, LocalSchemaCatalog] = {}
_CATALOG_CACHE_LOCK = threading.Lock()
_CATALOG_CACHE_LIMIT = 64


def clear_schema_catalog_cache() -> None:
    """Drop every memoised catalog; the next load re-checks from bytes."""

    with _CATALOG_CACHE_LOCK:
        _CATALOG_CACHE.clear()


def _read_schema_files(schema_dir: Path) -> tuple[tuple[Path, bytes], ...]:
    if not isinstance(schema_dir, Path):
        raise TypeError("schema_dir must be pathlib.Path")
    paths = tuple(sorted(schema_dir.glob("*.schema.json")))
    if not paths:
        raise RecordError(f"no local JSON schemas found in {schema_dir}")
    sources = []
    for path in paths:
        try:
            sources.append((path, path.read_bytes()))
        except OSError as exc:
            raise RecordError(f"cannot read {path}: {exc}") from exc
    return tuple(sources)


def load_local_schema_catalog(schema_dir: Path = DEFAULT_SCHEMA_DIR) -> LocalSchemaCatalog:
    """Strict-load and check every ``*.schema.json`` file in one directory."""

    sources = _read_schema_files(schema_dir)
    cache_key: _CacheKey = (str(schema_dir), tuple((path.name, bytes_digest(raw)) for path, raw in sources))
    with _CATALOG_CACHE_LOCK:
        cached = _CATALOG_CACHE.get(cache_key)
    if cached is not None:
        return cached

    parsed: dict[str, dict[str, Any]] = {}
    schema_ids: set[str] = set()
    for path, raw_bytes in sources:
        try:
            source = raw_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise RecordError(f"JSON is not UTF-8: {path}") from exc
        raw = loads_strict(source)
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
        except SchemaError as exc:
            raise RecordError(f"invalid JSON Schema {path}: {exc}") from exc
        parsed[path.name] = raw
        schema_ids.add(schema_id)

    try:
        registry = _registry_from_schemas(parsed)
    except CannotDetermineSpecification as exc:
        raise RecordError(f"schema registry could not be built: {exc}") from exc
    reference_errors = (InvalidAnchor, NoSuchAnchor, NoSuchResource, PointerToNowhere, Unresolvable, Unretrievable, ValueError)
    for schema_name, schema in parsed.items():
        root_id = schema["$id"]
        for base_uri, reference in _schema_references(schema, root_id):
            try:
                registry.resolver(base_uri).lookup(reference)
            except reference_errors as exc:
                try:
                    resolved = urljoin(base_uri, reference)
                except ValueError:
                    resolved = reference
                raise RecordError(f"schema {schema_name} has an unregistered or invalid local reference {resolved!r}") from exc

    catalog = LocalSchemaCatalog(
        schema_dir=schema_dir,
        _schema_sources=MappingProxyType(
            {name: json.dumps(schema, ensure_ascii=False, sort_keys=True, separators=(",", ":")) for name, schema in sorted(parsed.items())}
        ),
        _checked_schemas=MappingProxyType({name: parsed[name] for name in sorted(parsed)}),
        _checked_registry=registry,
    )
    with _CATALOG_CACHE_LOCK:
        if len(_CATALOG_CACHE) >= _CATALOG_CACHE_LIMIT:
            _CATALOG_CACHE.clear()
        return _CATALOG_CACHE.setdefault(cache_key, catalog)
