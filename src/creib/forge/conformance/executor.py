"""Model executors: a real Ollama chat client, a fake, a canned filler, a replayer.

The API key is read from ``OLLAMA_API_KEY`` at call time only.  It is never
stored on an executor, never placed in a request record, and every transport
error message is redacted before it is recorded.  A request digest covers
exactly what is sent to the model (model, prompts, format schema, options,
think) and nothing about authentication.

An executor returns what the endpoint returned.  It does not judge, retry
silently, or normalise content; a retry, when configured, is recorded as a
separate prior attempt inside the final response.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import http.client
import json
import os
from pathlib import Path
import re
from typing import Any, Callable, Mapping, Protocol
import urllib.error
import urllib.request

from creib.canonical import bytes_digest, domain_digest
from creib.errors import RecordError

from .common import (
    any_string,
    array_value,
    boolean,
    hex_digest,
    integer,
    object_value,
    optional_integer,
    optional_text,
    text,
)


REQUEST_DOMAIN = "creib.conformance-pilot.chat-request.v1"
API_KEY_ENV = "OLLAMA_API_KEY"
_BEARER = re.compile(r"(?i)bearer\s+\S+")
_AUTHORIZATION = re.compile(r"(?i)authorization")


def redact_content(content: str, secret: str | None) -> str:
    """Remove only the key value from model output; ordinary words are left intact."""

    return content.replace(secret, "[REDACTED]") if secret else content


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key in response: {key!r}")
        result[key] = value
    return result


def redact(message: str, secret: str | None) -> str:
    """Remove the key value and any bearer/authorization tokens from free text."""

    cleaned = message
    if secret:
        cleaned = cleaned.replace(secret, "[REDACTED]")
    cleaned = _BEARER.sub("[REDACTED_AUTH]", cleaned)
    cleaned = _AUTHORIZATION.sub("[REDACTED_HEADER]", cleaned)
    return cleaned


def _duration_int(value: Any, where: str) -> int | None:
    """Ollama reports nanoseconds and token counts as integers.

    If a float ever arrives it is truncated toward zero; whole-number floats
    are therefore preserved exactly and fractional nanoseconds are dropped.
    """

    if value is None:
        return None
    if type(value) is bool:
        return None
    if type(value) is int:
        return value
    if type(value) is float:
        return int(value)
    return None


@dataclass(frozen=True)
class ChatRequest:
    model: str
    system: str
    user: str
    format_schema: dict[str, Any] | None
    options: dict[str, int]
    think: bool | None

    def to_dict(self) -> dict[str, object]:
        return {
            "model": self.model,
            "system": self.system,
            "user": self.user,
            "format_schema": self.format_schema,
            "options": dict(self.options),
            "think": self.think,
        }

    @property
    def request_digest(self) -> str:
        return domain_digest(REQUEST_DOMAIN, self.to_dict())

    def body(self) -> dict[str, object]:
        """The exact JSON body posted to ``/api/chat``; no auth material."""

        payload: dict[str, object] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system},
                {"role": "user", "content": self.user},
            ],
            "stream": False,
            "options": dict(self.options),
        }
        if self.format_schema is not None:
            payload["format"] = self.format_schema
        if self.think is not None:
            payload["think"] = self.think
        return payload


@dataclass(frozen=True)
class ChatResponse:
    content: str
    thinking_present: bool
    done: bool
    done_reason: str | None
    prompt_eval_count: int | None
    eval_count: int | None
    total_duration_ns: int | None
    http_status: int | None
    transport_error: str | None
    response_digest: str
    attempt: int = 1
    prior_attempts: tuple["ChatResponse", ...] = field(default=())

    def _attempt_dict(self) -> dict[str, object]:
        return {
            "content": self.content,
            "thinking_present": self.thinking_present,
            "done": self.done,
            "done_reason": self.done_reason,
            "prompt_eval_count": self.prompt_eval_count,
            "eval_count": self.eval_count,
            "total_duration_ns": self.total_duration_ns,
            "http_status": self.http_status,
            "transport_error": self.transport_error,
            "response_digest": self.response_digest,
            "attempt": self.attempt,
        }

    def to_dict(self) -> dict[str, object]:
        record = self._attempt_dict()
        record["prior_attempts"] = [prior._attempt_dict() for prior in self.prior_attempts]
        return record

    @property
    def usable(self) -> bool:
        return self.transport_error is None and self.http_status in (None, 200)


def _response_from_attempt(raw: Any, where: str) -> ChatResponse:
    record = object_value(raw, where)
    return ChatResponse(
        content=any_string(record["content"], f"{where}.content"),
        thinking_present=boolean(record["thinking_present"], f"{where}.thinking_present"),
        done=boolean(record["done"], f"{where}.done"),
        done_reason=optional_text(record["done_reason"], f"{where}.done_reason"),
        prompt_eval_count=optional_integer(record["prompt_eval_count"], f"{where}.prompt_eval_count"),
        eval_count=optional_integer(record["eval_count"], f"{where}.eval_count"),
        total_duration_ns=optional_integer(record["total_duration_ns"], f"{where}.total_duration_ns"),
        http_status=optional_integer(record["http_status"], f"{where}.http_status", minimum=100),
        transport_error=optional_text(record["transport_error"], f"{where}.transport_error"),
        response_digest=hex_digest(record["response_digest"], f"{where}.response_digest"),
        attempt=integer(record["attempt"], f"{where}.attempt", minimum=1),
    )


def response_from_dict(raw: Any, where: str = "response") -> ChatResponse:
    record = object_value(raw, where)
    final = _response_from_attempt(record, where)
    priors = tuple(
        _response_from_attempt(item, f"{where}.prior_attempts[{index}]")
        for index, item in enumerate(array_value(record["prior_attempts"], f"{where}.prior_attempts"))
    )
    return ChatResponse(**{**final.__dict__, "prior_attempts": priors})


class ModelExecutor(Protocol):
    def complete(self, request: ChatRequest) -> ChatResponse: ...


def _error_response(message: str, *, http_status: int | None, body: bytes | None, attempt: int) -> ChatResponse:
    digest_source = body if body is not None else message.encode("utf-8")
    return ChatResponse(
        content="",
        thinking_present=False,
        done=False,
        done_reason=None,
        prompt_eval_count=None,
        eval_count=None,
        total_duration_ns=None,
        http_status=http_status,
        transport_error=message,
        response_digest=bytes_digest(digest_source),
        attempt=attempt,
    )


def parse_chat_body(body: bytes, *, http_status: int, attempt: int, secret: str | None) -> ChatResponse:
    """Turn a raw ``/api/chat`` body into a float-free response record."""

    digest = bytes_digest(body)
    try:
        parsed = json.loads(body.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys)
    except (UnicodeDecodeError, ValueError) as exc:
        return _error_response(
            "ResponseParseError: " + redact(str(exc), secret),
            http_status=http_status,
            body=body,
            attempt=attempt,
        )
    if type(parsed) is not dict:
        return _error_response(
            "ResponseParseError: body is not a JSON object",
            http_status=http_status,
            body=body,
            attempt=attempt,
        )
    message = parsed.get("message")
    if type(message) is not dict:
        detail = parsed.get("error")
        return _error_response(
            "ResponseShapeError: " + redact(str(detail) if detail is not None else "no message object", secret),
            http_status=http_status,
            body=body,
            attempt=attempt,
        )
    content = message.get("content")
    if type(content) is not str:
        content = ""
    thinking = message.get("thinking")
    done_reason = parsed.get("done_reason")
    return ChatResponse(
        content=redact_content(content, secret),
        thinking_present=type(thinking) is str and bool(thinking.strip()),
        done=parsed.get("done") is True,
        done_reason=done_reason if type(done_reason) is str and done_reason.strip() else None,
        prompt_eval_count=_duration_int(parsed.get("prompt_eval_count"), "prompt_eval_count"),
        eval_count=_duration_int(parsed.get("eval_count"), "eval_count"),
        total_duration_ns=_duration_int(parsed.get("total_duration"), "total_duration"),
        http_status=http_status,
        transport_error=None,
        response_digest=digest,
        attempt=attempt,
    )


class OllamaChatExecutor:
    """POST to ``{base_url}/api/chat`` with the key from the environment only."""

    def __init__(self, base_url: str = "https://ollama.com", timeout_seconds: int = 180, retries: int = 0) -> None:
        if type(timeout_seconds) is not int or timeout_seconds < 1:
            raise RecordError("timeout_seconds must be a positive integer")
        if type(retries) is not int or retries < 0:
            raise RecordError("retries must be a non-negative integer")
        self.base_url = text(base_url, "base_url").rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.retries = retries

    def __repr__(self) -> str:
        return f"OllamaChatExecutor(base_url={self.base_url!r}, timeout_seconds={self.timeout_seconds}, retries={self.retries})"

    def _attempt(self, request: ChatRequest, attempt: int) -> ChatResponse:
        secret = os.environ.get(API_KEY_ENV)
        if not secret:
            raise RecordError("OLLAMA_API_KEY is not set")
        payload = json.dumps(request.body(), ensure_ascii=False, allow_nan=False).encode("utf-8")
        http_request = urllib.request.Request(
            self.base_url + "/api/chat",
            data=payload,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": "Bearer " + secret,
            },
        )
        try:
            with urllib.request.urlopen(http_request, timeout=self.timeout_seconds) as response:
                status = int(response.status)
                body = response.read()
        except urllib.error.HTTPError as exc:
            try:
                body = exc.read()
            except (OSError, ValueError, http.client.HTTPException):
                body = b""
            snippet = redact(body.decode("utf-8", errors="replace")[:500], secret)
            return _error_response(
                f"HTTPError: status {exc.code}: {snippet}",
                http_status=int(exc.code),
                body=body,
                attempt=attempt,
            )
        except (urllib.error.URLError, OSError, ValueError, http.client.HTTPException) as exc:
            return _error_response(
                f"{type(exc).__name__}: {redact(str(exc), secret)}",
                http_status=None,
                body=None,
                attempt=attempt,
            )
        return parse_chat_body(body, http_status=status, attempt=attempt, secret=secret)

    def complete(self, request: ChatRequest) -> ChatResponse:
        priors: list[ChatResponse] = []
        final: ChatResponse | None = None
        for attempt in range(1, self.retries + 2):
            final = self._attempt(request, attempt)
            if final.usable or attempt == self.retries + 1:
                break
            priors.append(final)
        if final is None:
            raise RecordError("executor produced no attempt")
        if priors:
            return ChatResponse(**{**final.__dict__, "prior_attempts": tuple(priors)})
        return final


class FakeExecutor:
    """Deterministic responses for tests: by request digest or by callable."""

    def __init__(self, responses: Mapping[str, ChatResponse] | Callable[[ChatRequest], ChatResponse]) -> None:
        self._responses = responses
        self.requests: list[ChatRequest] = []

    def complete(self, request: ChatRequest) -> ChatResponse:
        self.requests.append(request)
        if callable(self._responses):
            return self._responses(request)
        try:
            return self._responses[request.request_digest]
        except KeyError as exc:
            raise RecordError(f"FakeExecutor has no response for request {request.request_digest}") from exc


def executor_failure_response(exc: BaseException) -> ChatResponse:
    """Record an executor that raised instead of returning; only the type is kept.

    The exception message is deliberately not recorded: it could carry request
    or environment text. The type name is enough to route the observation to
    AUXILIARY and SCOPE and to make the failure visible in the run counts.
    """

    return _error_response(
        f"ExecutorException: {type(exc).__name__}",
        http_status=None,
        body=None,
        attempt=1,
    )


def response_from_content(content: str, *, done_reason: str | None = "stop", thinking_present: bool = False) -> ChatResponse:
    """A synthetic successful response carrying ``content``; for fakes and tests."""

    return ChatResponse(
        content=content,
        thinking_present=thinking_present,
        done=True,
        done_reason=done_reason,
        prompt_eval_count=None,
        eval_count=None,
        total_duration_ns=None,
        http_status=None,
        transport_error=None,
        response_digest=bytes_digest(content.encode("utf-8")),
    )


def canned_value(property_schema: Mapping[str, Any]) -> Any:
    """Schema-derived placeholder for one field; a smoke filler, not a model."""

    if "enum" in property_schema:
        return property_schema["enum"][0]
    json_type = property_schema.get("type")
    if json_type == "boolean":
        return False
    if json_type == "integer":
        return 0
    pattern = property_schema.get("pattern", "")
    if "[0-9]{4}-[0-9]{2}-[0-9]{2}" in pattern:
        return "2025-01-01"
    if "\\+61" in pattern:
        return "+61400000000"
    if "[0-9]{2}:[0-9]{2}" in pattern:
        return "09:00"
    return "placeholder"


class CannedExecutor:
    """Fills every schema property with a fixed placeholder; used by ``--dry-run``."""

    def complete(self, request: ChatRequest) -> ChatResponse:
        schema = request.format_schema or {}
        properties = schema.get("properties", {})
        output = {name: canned_value(property_schema) for name, property_schema in properties.items()}
        return response_from_content(json.dumps(output, ensure_ascii=False, allow_nan=False))


class ReplayExecutor:
    """Replay recorded responses by request digest; never contacts a network."""

    def __init__(self, observation_records_dir: Path) -> None:
        from .records import load_observation_directory

        if not isinstance(observation_records_dir, Path):
            raise TypeError("observation_records_dir must be pathlib.Path")
        self._responses: dict[str, ChatResponse] = {}
        for record in load_observation_directory(observation_records_dir):
            if record.request_digest is None or record.response is None:
                continue
            existing = self._responses.get(record.request_digest)
            if existing is not None and existing != record.response:
                raise RecordError(
                    f"replay directory holds conflicting responses for request {record.request_digest}"
                )
            self._responses[record.request_digest] = record.response

    def complete(self, request: ChatRequest) -> ChatResponse:
        try:
            return self._responses[request.request_digest]
        except KeyError as exc:
            raise RecordError(f"no recorded response for request {request.request_digest}") from exc
