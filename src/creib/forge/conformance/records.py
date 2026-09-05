"""Content-addressed observation and run records, published no-clobber.

An observation binds one variant, one request digest, one raw response, its
scoring, and its routing.  A run binds the header that was fixed before any
model was called (pilot, plan, model, endpoint, executor, families, limit,
timestamp) and the ordered observation identifiers produced under it.

Identifiers replay from content; loaders fail closed when bytes are not the
canonical serialisation or when a recomputed identifier differs.  ``created_on``
is supplied by the caller so records stay replayable.  No record carries a
key, a header, or a score; the run status is always ``UNRESOLVED`` and the
route is always human triage.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from creib.canonical import canonical_bytes
from creib.errors import PolicyViolation, RecordError
from creib.forge.models import NON_INDUCTIVE_LIMIT
from creib.strict_json import loads_strict

from .common import (
    OBSERVATION_SCHEMA_NAME,
    OBSERVATION_SCHEMA_VERSION,
    OVERALL_STATUS_UNRESOLVED,
    ROUTE_AWAITING_HUMAN_TRIAGE,
    RUN_SCHEMA_NAME,
    RUN_SCHEMA_VERSION,
    SCOPE_REFUTED,
    SCOPE_UNREFUTED,
    array_value,
    content_id,
    decode_utf8,
    hex_digest,
    identifier,
    integer,
    model_id,
    object_value,
    optional_boolean,
    optional_integer,
    optional_text,
    publish_no_clobber,
    rfc3339,
    text,
    validate_instance,
)
from .executor import ChatResponse, response_from_dict
from .families import Family, Variant, variant_from_dict
from .oracle import Scoring, scoring_from_dict
from .routing import Routing, routing_from_dict
from .spec import Binding, Endpoint, endpoint_from_dict


OBSERVATION_DOMAIN = "creib.conformance-pilot.observation.v1"
RUN_HEADER_DOMAIN = "creib.conformance-pilot.run-header.v1"
RUN_CONTENT_DOMAIN = "creib.conformance-pilot.run-content.v1"
EXECUTOR_KINDS: tuple[str, ...] = ("ollama-chat", "fake", "replay", "canned")
_SCHEMA_SHORT_NAMES: Mapping[str, tuple[str, str, str]] = {
    OBSERVATION_SCHEMA_VERSION: ("observation", "observation_id", OBSERVATION_SCHEMA_NAME),
    RUN_SCHEMA_VERSION: ("run", "run_id", RUN_SCHEMA_NAME),
}


def _bindings_from(raw: Any, where: str) -> tuple[Binding, ...]:
    bindings = tuple(
        Binding(
            path=text(object_value(item, f"{where}[{index}]")["path"], f"{where}[{index}].path"),
            sha256=hex_digest(object_value(item, f"{where}[{index}]")["sha256"], f"{where}[{index}].sha256"),
        )
        for index, item in enumerate(array_value(raw, where))
    )
    if not bindings:
        raise RecordError(f"{where} must not be empty")
    return bindings


@dataclass(frozen=True)
class ObservationRecord:
    observation_id: str
    run_id: str
    pilot_id: str
    plan_id: str
    planned_variant_id: str
    spec_bindings: tuple[Binding, ...]
    model: str
    variant: Variant
    request_digest: str | None
    response: ChatResponse | None
    scoring: Scoring
    routing: Routing
    baseline_observation_id: str | None
    created_on: str

    def body(self) -> dict[str, object]:
        return {
            "schema_version": OBSERVATION_SCHEMA_VERSION,
            "run_id": self.run_id,
            "pilot_id": self.pilot_id,
            "plan_id": self.plan_id,
            "planned_variant_id": self.planned_variant_id,
            "spec_bindings": [binding.to_dict() for binding in self.spec_bindings],
            "model": self.model,
            "variant": self.variant.to_dict(),
            "request_digest": self.request_digest,
            "response": None if self.response is None else self.response.to_dict(),
            "scoring": self.scoring.to_dict(),
            "routing": self.routing.to_dict(),
            "baseline_observation_id": self.baseline_observation_id,
            "created_on": self.created_on,
        }

    def to_dict(self) -> dict[str, object]:
        record = self.body()
        record["observation_id"] = self.observation_id
        return record


def build_observation(**fields: Any) -> ObservationRecord:
    draft = ObservationRecord(observation_id="0" * 64, **fields)
    return ObservationRecord(observation_id=content_id(OBSERVATION_DOMAIN, draft.body()), **fields)


def observation_from_dict(raw: Any) -> ObservationRecord:
    """Rebuild an observation, re-validating the schema and replaying its id."""

    record = object_value(raw, "observation")
    validate_instance(record, OBSERVATION_SCHEMA_NAME)
    request_digest = optional_text(record["request_digest"], "observation.request_digest")
    response = None if record["response"] is None else response_from_dict(record["response"], "observation.response")
    rebuilt = build_observation(
        run_id=hex_digest(record["run_id"], "observation.run_id"),
        pilot_id=identifier(record["pilot_id"], "observation.pilot_id"),
        plan_id=hex_digest(record["plan_id"], "observation.plan_id"),
        planned_variant_id=hex_digest(record["planned_variant_id"], "observation.planned_variant_id"),
        spec_bindings=_bindings_from(record["spec_bindings"], "observation.spec_bindings"),
        model=model_id(record["model"], "observation.model"),
        variant=variant_from_dict(record["variant"]),
        request_digest=request_digest,
        response=response,
        scoring=scoring_from_dict(record["scoring"], "observation.scoring"),
        routing=routing_from_dict(record["routing"], "observation.routing"),
        baseline_observation_id=None if record["baseline_observation_id"] is None else hex_digest(record["baseline_observation_id"], "observation.baseline_observation_id"),
        created_on=rfc3339(record["created_on"], "observation.created_on"),
    )
    if rebuilt.observation_id != hex_digest(record["observation_id"], "observation.observation_id"):
        raise RecordError("observation_id does not replay from the record content")
    if (request_digest is None) != (response is None):
        raise RecordError("observation must carry a request digest exactly when it carries a response")
    if rebuilt.variant.model_call == (response is None):
        raise RecordError("observation response presence disagrees with the variant's model_call flag")
    return rebuilt


@dataclass(frozen=True)
class RunRecord:
    run_id: str
    content_digest: str
    pilot_id: str
    plan_id: str
    model: str
    endpoint: Endpoint
    executor_kind: str
    spec_bindings: tuple[Binding, ...]
    created_on: str
    selected_families: tuple[str, ...]
    variant_limit: int | None
    observation_ids: tuple[str, ...]
    family_counts: tuple[tuple[str, int], ...]
    response_verdict_counts: tuple[tuple[str, int], ...]
    field_verdict_counts: tuple[tuple[str, int], ...]
    live_locus_counts: tuple[tuple[str, int], ...]
    observations_with_live_loci: int
    model_call_count: int
    transport_error_count: int
    scope_label: str
    format_enforced_by_server: bool | None
    overall_status: str = OVERALL_STATUS_UNRESOLVED
    route: str = ROUTE_AWAITING_HUMAN_TRIAGE
    epistemic_limit: str = NON_INDUCTIVE_LIMIT

    def __post_init__(self) -> None:
        if self.overall_status != OVERALL_STATUS_UNRESOLVED:
            raise PolicyViolation("a conformance run record cannot express any status but UNRESOLVED")
        if self.route != ROUTE_AWAITING_HUMAN_TRIAGE:
            raise PolicyViolation("a conformance run record must route to human triage")
        if self.epistemic_limit != NON_INDUCTIVE_LIMIT:
            raise PolicyViolation("run record weakens the non-inductive limit")
        if self.scope_label not in (SCOPE_REFUTED, SCOPE_UNREFUTED):
            raise PolicyViolation("run record scope label is outside the allowed vocabulary")
        if self.executor_kind not in EXECUTOR_KINDS:
            raise RecordError("run record executor_kind is unknown")

    def header(self) -> dict[str, object]:
        return {
            "schema_version": RUN_SCHEMA_VERSION,
            "pilot_id": self.pilot_id,
            "plan_id": self.plan_id,
            "model": self.model,
            "endpoint": self.endpoint.to_dict(),
            "executor_kind": self.executor_kind,
            "spec_bindings": [binding.to_dict() for binding in self.spec_bindings],
            "created_on": self.created_on,
            "selected_families": list(self.selected_families),
            "variant_limit": self.variant_limit,
        }

    def body(self) -> dict[str, object]:
        record = self.header()
        record.update(
            {
                "run_id": self.run_id,
                "observation_ids": list(self.observation_ids),
                "family_counts": [{"family": family, "count": count} for family, count in self.family_counts],
                "response_verdict_counts": [{"verdict": verdict, "count": count} for verdict, count in self.response_verdict_counts],
                "field_verdict_counts": [{"verdict": verdict, "count": count} for verdict, count in self.field_verdict_counts],
                "live_locus_counts": [{"locus": locus, "count": count} for locus, count in self.live_locus_counts],
                "observations_with_live_loci": self.observations_with_live_loci,
                "model_call_count": self.model_call_count,
                "transport_error_count": self.transport_error_count,
                "scope_label": self.scope_label,
                "overall_status": self.overall_status,
                "route": self.route,
                "epistemic_limit": self.epistemic_limit,
                "format_enforced_by_server": self.format_enforced_by_server,
            }
        )
        return record

    def to_dict(self) -> dict[str, object]:
        record = self.body()
        record["content_digest"] = self.content_digest
        return record


def compute_run_id(header: Mapping[str, Any]) -> str:
    return content_id(RUN_HEADER_DOMAIN, dict(header))


def build_run_record(**fields: Any) -> RunRecord:
    """Assign the header-derived run_id and the whole-record content digest."""

    draft = RunRecord(run_id="0" * 64, content_digest="0" * 64, **fields)
    run_id = compute_run_id(draft.header())
    if fields.get("run_id_expected") is not None:
        raise RecordError("run_id is derived, not supplied")
    with_id = RunRecord(run_id=run_id, content_digest="0" * 64, **fields)
    return RunRecord(run_id=run_id, content_digest=content_id(RUN_CONTENT_DOMAIN, with_id.body()), **fields)


def _count_pairs(raw: Any, where: str, key: str) -> tuple[tuple[str, int], ...]:
    pairs = tuple(
        (
            text(object_value(item, f"{where}[{index}]")[key], f"{where}[{index}].{key}"),
            integer(object_value(item, f"{where}[{index}]")["count"], f"{where}[{index}].count"),
        )
        for index, item in enumerate(array_value(raw, where))
    )
    if len({name for name, _ in pairs}) != len(pairs):
        raise RecordError(f"{where} repeats a key")
    return pairs


def run_from_dict(raw: Any) -> RunRecord:
    record = object_value(raw, "run")
    validate_instance(record, RUN_SCHEMA_NAME)
    families = tuple(text(item, "run.selected_families") for item in array_value(record["selected_families"], "run.selected_families"))
    for family in families:
        try:
            Family(family)
        except ValueError as exc:
            raise RecordError(f"run.selected_families has unknown family {family!r}") from exc
    rebuilt = build_run_record(
        pilot_id=identifier(record["pilot_id"], "run.pilot_id"),
        plan_id=hex_digest(record["plan_id"], "run.plan_id"),
        model=model_id(record["model"], "run.model"),
        endpoint=endpoint_from_dict(record["endpoint"]),
        executor_kind=text(record["executor_kind"], "run.executor_kind"),
        spec_bindings=_bindings_from(record["spec_bindings"], "run.spec_bindings"),
        created_on=rfc3339(record["created_on"], "run.created_on"),
        selected_families=families,
        variant_limit=optional_integer(record["variant_limit"], "run.variant_limit", minimum=1),
        observation_ids=tuple(hex_digest(item, "run.observation_ids") for item in array_value(record["observation_ids"], "run.observation_ids")),
        family_counts=_count_pairs(record["family_counts"], "run.family_counts", "family"),
        response_verdict_counts=_count_pairs(record["response_verdict_counts"], "run.response_verdict_counts", "verdict"),
        field_verdict_counts=_count_pairs(record["field_verdict_counts"], "run.field_verdict_counts", "verdict"),
        live_locus_counts=_count_pairs(record["live_locus_counts"], "run.live_locus_counts", "locus"),
        observations_with_live_loci=integer(record["observations_with_live_loci"], "run.observations_with_live_loci"),
        model_call_count=integer(record["model_call_count"], "run.model_call_count"),
        transport_error_count=integer(record["transport_error_count"], "run.transport_error_count"),
        scope_label=text(record["scope_label"], "run.scope_label"),
        format_enforced_by_server=optional_boolean(record["format_enforced_by_server"], "run.format_enforced_by_server"),
        overall_status=text(record["overall_status"], "run.overall_status"),
        route=text(record["route"], "run.route"),
        epistemic_limit=text(record["epistemic_limit"], "run.epistemic_limit"),
    )
    if rebuilt.run_id != hex_digest(record["run_id"], "run.run_id"):
        raise RecordError("run_id does not replay from the run header")
    if rebuilt.content_digest != hex_digest(record["content_digest"], "run.content_digest"):
        raise RecordError("run content_digest does not replay from the record content")
    return rebuilt


def record_filename(record: Mapping[str, Any]) -> str:
    schema_version = record.get("schema_version")
    try:
        short, id_key, _ = _SCHEMA_SHORT_NAMES[str(schema_version)]
    except KeyError as exc:
        raise RecordError(f"unknown conformance record schema_version {schema_version!r}") from exc
    return f"{short}.{hex_digest(record[id_key], id_key)[:16]}.json"


def publish_record(record: ObservationRecord | RunRecord | Mapping[str, Any], directory: Path) -> Path:
    """Validate, canonicalise, and publish one record without ever overwriting."""

    if not isinstance(directory, Path):
        raise TypeError("directory must be pathlib.Path")
    data = record.to_dict() if isinstance(record, (ObservationRecord, RunRecord)) else dict(record)
    schema_version = str(data.get("schema_version"))
    if schema_version not in _SCHEMA_SHORT_NAMES:
        raise RecordError(f"unknown conformance record schema_version {schema_version!r}")
    validate_instance(data, _SCHEMA_SHORT_NAMES[schema_version][2])
    if isinstance(record, Mapping):
        if schema_version == OBSERVATION_SCHEMA_VERSION:
            observation_from_dict(data)
        else:
            run_from_dict(data)
    payload = canonical_bytes(data) + b"\n"
    path = directory / record_filename(data)
    if path.exists():
        raise RecordError(f"record path exists: {path}")
    return publish_no_clobber(path, payload)


def _load_canonical(path: Path) -> dict[str, Any]:
    if not isinstance(path, Path):
        raise TypeError("path must be pathlib.Path")
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise RecordError(f"cannot read record {path}: {exc}") from exc
    value = loads_strict(decode_utf8(raw, str(path)))
    record = object_value(value, str(path))
    if raw != canonical_bytes(record) + b"\n":
        raise RecordError(f"record {path} is not canonical JSON plus one newline")
    return record


def load_observation(path: Path) -> ObservationRecord:
    record = _load_canonical(path)
    if record.get("schema_version") != OBSERVATION_SCHEMA_VERSION:
        raise RecordError(f"{path} is not a conformance observation record")
    return observation_from_dict(record)


def load_run(path: Path) -> RunRecord:
    record = _load_canonical(path)
    if record.get("schema_version") != RUN_SCHEMA_VERSION:
        raise RecordError(f"{path} is not a conformance run record")
    return run_from_dict(record)


def load_observation_directory(directory: Path) -> list[ObservationRecord]:
    if not isinstance(directory, Path):
        raise TypeError("directory must be pathlib.Path")
    if not directory.is_dir():
        raise RecordError(f"observation directory does not exist: {directory}")
    return [load_observation(path) for path in sorted(directory.glob("observation.*.json"))]
