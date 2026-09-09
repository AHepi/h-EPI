"""The one artifact template, and the kind records that fill it in (R4, R6, R7).

There is no conjecturer type here and no critic type. There is a template —
declared input ports, one output port, two required submission fields — and a
kind record that says what a particular seat is shown and what it produces.
Conjecturer and critic are two such records. A third kind is a third record.

A submission carries ``body`` and ``commitments`` and nothing else it must:
``citations``, ``about`` and ``answers`` belong to the template and are always
optional, and a kind may name further optional fields of its own.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Mapping

from creib.errors import RecordError
from creib.strict_json import loads_strict

from .common import (
    MiniError,
    REQUIRED_SUBMISSION_FIELDS,
    TEMPLATE_SUBMISSION_FIELDS,
    array_value,
    object_value,
    text,
)
from .failures import FailurePolicy, failure_policy_from_dict
from .formats import CompiledFormat
from .windows import ALL, Window, window_from_dict


@dataclass(frozen=True)
class InputPort:
    port_id: str
    port_type: str
    params: Mapping[str, Any] = field(default_factory=dict)
    window: Window = ALL

    def to_dict(self) -> dict[str, object]:
        return {
            "port_id": self.port_id,
            "port_type": self.port_type,
            "params": dict(self.params),
            **self.window.to_dict(),
        }


@dataclass(frozen=True)
class OutputPort:
    port_id: str
    produces_kind: str

    def to_dict(self) -> dict[str, object]:
        return {"port_id": self.port_id, "produces_kind": self.produces_kind}


@dataclass(frozen=True)
class ArtifactKind:
    """One registered kind: the template with its slots filled."""

    kind_id: str
    title: str
    input_ports: tuple[InputPort, ...]
    output_port: OutputPort
    optional_fields: tuple[str, ...]
    format_spec: Mapping[str, Any] | None
    failure_policy: FailurePolicy

    def port(self, port_id: str) -> InputPort:
        for item in self.input_ports:
            if item.port_id == port_id:
                return item
        raise MiniError("MINI_PORT_UNKNOWN", f"kind {self.kind_id!r} declares no port {port_id!r}")

    def to_dict(self) -> dict[str, object]:
        return {
            "kind_id": self.kind_id,
            "title": self.title,
            "input_ports": [item.to_dict() for item in self.input_ports],
            "output_port": self.output_port.to_dict(),
            "optional_fields": list(self.optional_fields),
            "failure_policy": self.failure_policy.to_dict(),
        }


def kind_from_dict(raw: Any, where: str) -> ArtifactKind:
    """Read one kind record. The output port must produce the kind's own id."""

    entry = object_value(raw, where)
    kind_id = text(entry.get("kind_id"), f"{where}.kind_id")
    ports = array_value(entry.get("input_ports"), f"{where}.input_ports")
    input_ports: list[InputPort] = []
    seen: set[str] = set()
    for index, item in enumerate(ports):
        port_entry = object_value(item, f"{where}.input_ports[{index}]")
        port_id = text(port_entry.get("port_id"), f"{where}.input_ports[{index}].port_id")
        if port_id in seen:
            raise MiniError("MINI_KIND_PORT_DUPLICATE", f"kind {kind_id!r} declares the port {port_id!r} twice")
        seen.add(port_id)
        input_ports.append(
            InputPort(
                port_id=port_id,
                port_type=text(port_entry.get("port_type"), f"{where}.input_ports[{index}].port_type"),
                params=object_value(port_entry.get("params") or {}, f"{where}.input_ports[{index}].params"),
                window=window_from_dict(port_entry.get("window"), f"{where}.input_ports[{index}].window"),
            )
        )
    output_raw = object_value(entry.get("output_port"), f"{where}.output_port")
    output = OutputPort(
        port_id=text(output_raw.get("port_id"), f"{where}.output_port.port_id"),
        produces_kind=text(output_raw.get("produces_kind"), f"{where}.output_port.produces_kind"),
    )
    if output.produces_kind != kind_id:
        raise MiniError(
            "MINI_KIND_OUTPUT_MISMATCH",
            f"kind {kind_id!r} has an output port producing {output.produces_kind!r}: a kind produces its own kind",
        )
    optional_raw = entry.get("optional_fields") or []
    optional = tuple(
        text(item, f"{where}.optional_fields[{index}]")
        for index, item in enumerate(array_value(optional_raw, f"{where}.optional_fields"))
    )
    reserved = set(REQUIRED_SUBMISSION_FIELDS) | set(TEMPLATE_SUBMISSION_FIELDS)
    clash = sorted(set(optional) & reserved)
    if clash:
        raise MiniError("MINI_SUBMISSION_UNKNOWN_FIELD", f"kind {kind_id!r} redeclares template fields {clash}")
    return ArtifactKind(
        kind_id=kind_id,
        title=text(entry.get("title"), f"{where}.title"),
        input_ports=tuple(input_ports),
        output_port=output,
        optional_fields=optional,
        format_spec=entry.get("format"),
        failure_policy=failure_policy_from_dict(entry.get("failure_policy"), f"{where}.failure_policy"),
    )


RECOVERED_FENCE = "fence"
RECOVERED_PROSE = "prose"

#: A bracketed block id prefix, then a quotation. Deliberately narrow: it
#: recovers the shape the record has actually seen a model use, and finds
#: nothing in prose that carries no block id.
_PROSE_CITATION = re.compile(r"\[([0-9a-f]{8,64})\]\s*[\"\u201c]([^\"\u201d]{1,512})[\"\u201d]")
_FENCE = re.compile(r"\A\s*```[A-Za-z0-9_-]*\s*\n(.*?)\n?\s*```\s*\Z", re.DOTALL)


def strip_fence(reply: str) -> tuple[str, bool]:
    """Return the reply with a markdown code fence removed, and whether one was."""

    match = _FENCE.match(reply)
    return (match.group(1), True) if match else (reply, False)


def recover_prose_citations(body: str) -> tuple[dict[str, Any], ...]:
    """Bracketed id-and-quote pairs a seat wrote into its prose."""

    return tuple(
        {"block": block, "quote": quote, "recovered": RECOVERED_PROSE}
        for block, quote in _PROSE_CITATION.findall(body)
    )


@dataclass(frozen=True)
class Submission:
    """One well-formed submission, before its format is checked."""

    body: str
    commitments: str
    citations: tuple[Mapping[str, Any], ...]
    about: tuple[str, ...]
    answers: tuple[str, ...]
    extra: Mapping[str, str]
    recovered: tuple[str, ...] = ()

    def as_fields(self) -> dict[str, Any]:
        return {"body": self.body, "commitments": self.commitments}


def _string_array(raw: Any, where: str) -> tuple[str, ...]:
    items = array_value(raw, where, "MINI_SUBMISSION_FIELD_TYPE")
    return tuple(text(item, f"{where}[{index}]", "MINI_SUBMISSION_FIELD_TYPE") for index, item in enumerate(items))


def read_submission(reply: str, kind: ArtifactKind) -> Submission:
    """Read a reply into a submission, or refuse it with a typed reason.

    Only ``body`` and ``commitments`` are required, whatever the kind (R7).
    """

    unfenced, fenced = strip_fence(reply)
    try:
        parsed = loads_strict(unfenced)
    except RecordError as error:
        raise MiniError("MINI_SUBMISSION_NOT_JSON", f"the reply is not readable as JSON: {error}") from error
    if type(parsed) is not dict:
        raise MiniError("MINI_SUBMISSION_NOT_JSON", "the reply is not a JSON object")
    for name in REQUIRED_SUBMISSION_FIELDS:
        if name not in parsed:
            raise MiniError("MINI_SUBMISSION_MISSING_FIELD", f"the submission carries no {name!r}")
        if type(parsed[name]) is not str:
            raise MiniError("MINI_SUBMISSION_FIELD_TYPE", f"{name!r} must be a string")
    admitted = set(REQUIRED_SUBMISSION_FIELDS) | set(TEMPLATE_SUBMISSION_FIELDS) | set(kind.optional_fields)
    unknown = sorted(set(parsed) - admitted)
    if unknown:
        raise MiniError(
            "MINI_SUBMISSION_UNKNOWN_FIELD",
            f"the submission carries fields kind {kind.kind_id!r} does not declare: {unknown}",
        )
    citations_raw = array_value(parsed.get("citations") or [], "submission.citations", "MINI_SUBMISSION_FIELD_TYPE")
    declared: list[Mapping[str, Any]] = []
    for index, item in enumerate(citations_raw):
        entry = object_value(item, f"submission.citations[{index}]", "MINI_SUBMISSION_FIELD_TYPE")
        # An empty pair is a badly shaped submission, not an unknown block: it
        # says nothing about the evidence, only about the reply (FAILURE_MODES M2).
        for name in ("block", "quote"):
            value = entry.get(name)
            if type(value) is not str or not value.strip():
                raise MiniError(
                    "MINI_SUBMISSION_FIELD_TYPE",
                    f"submission.citations[{index}].{name} must be a non-empty string",
                )
        declared.append({**entry, "recovered": None})
    recovered_citations = recover_prose_citations(parsed["body"])
    citations = tuple(declared) + recovered_citations
    extra: dict[str, str] = {}
    for name in kind.optional_fields:
        if name in parsed:
            extra[name] = text(parsed[name], f"submission.{name}", "MINI_SUBMISSION_FIELD_TYPE")
    return Submission(
        body=parsed["body"],
        commitments=parsed["commitments"],
        citations=citations,
        about=_string_array(parsed.get("about") or [], "submission.about"),
        answers=_string_array(parsed.get("answers") or [], "submission.answers"),
        extra=extra,
        recovered=tuple(
            [RECOVERED_FENCE] if fenced else []
        ) + ((RECOVERED_PROSE,) if recovered_citations else ()),
    )
