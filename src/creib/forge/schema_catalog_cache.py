"""Content-keyed memoisation of the checked local schema catalog.

``creib.forge.schema_validation.load_local_schema_catalog`` strict-loads every
``*.schema.json`` file in a directory, runs the metaschema check on each, and
crawls a retrieval-disabled registry.  That is the right behaviour for one
call and the wrong cost model for thousands of calls against unchanged bytes.

This module wraps the loader without modifying it.  The cache key is the
directory path together with the SHA-256 of every schema file's bytes, so a
hit requires byte-identical schema files.  Any change to any schema misses
the cache and repeats the complete check.  Caching removes repeated work; it
never skips a check that a changed input would need, and it never changes
what the loader would have returned.

The loader itself is part of the pinned implementation contract of the
committed calibration record, so it is deliberately left untouched here.
Callers that are not pinned may use this accessor instead.
"""

from __future__ import annotations

from pathlib import Path
import threading

from creib.canonical import bytes_digest
from creib.errors import RecordError

from .schema_validation import DEFAULT_SCHEMA_DIR, LocalSchemaCatalog, load_local_schema_catalog

_CacheKey = tuple[str, tuple[tuple[str, str], ...]]
_CACHE: dict[_CacheKey, LocalSchemaCatalog] = {}
_LOCK = threading.Lock()
_LIMIT = 64


def clear_schema_catalog_cache() -> None:
    """Drop every memoised catalog; the next call re-checks from bytes."""

    with _LOCK:
        _CACHE.clear()


def _cache_key(schema_dir: Path) -> _CacheKey:
    if not isinstance(schema_dir, Path):
        raise TypeError("schema_dir must be pathlib.Path")
    paths = tuple(sorted(schema_dir.glob("*.schema.json")))
    if not paths:
        raise RecordError(f"no local JSON schemas found in {schema_dir}")
    digests: list[tuple[str, str]] = []
    for path in paths:
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise RecordError(f"cannot read {path}: {exc}") from exc
        digests.append((path.name, bytes_digest(raw)))
    return (str(schema_dir), tuple(digests))


def cached_local_schema_catalog(
    schema_dir: Path = DEFAULT_SCHEMA_DIR,
) -> LocalSchemaCatalog:
    """Return the checked catalog for byte-identical schema files, else reload."""

    key = _cache_key(schema_dir)
    with _LOCK:
        hit = _CACHE.get(key)
    if hit is not None:
        return hit
    catalog = load_local_schema_catalog(schema_dir)
    with _LOCK:
        if len(_CACHE) >= _LIMIT:
            _CACHE.clear()
        return _CACHE.setdefault(key, catalog)
