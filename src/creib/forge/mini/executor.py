"""The responder a stage is asked through.

Two ship. The scripted one calls nothing: it returns prepared replies in a
fixed order per stage, so a run of the same plan against the same script writes
the same record twice, and no test in this package needs a network or a key.
It is the only responder the suite uses.

The live one exists so a run can be driven by a real model. It does not speak
HTTP itself: it builds a request and hands it to the conformance harness's own
``OllamaChatExecutor``, which reads the key from ``OLLAMA_API_KEY`` at call
time, sends no auth material into any record, and redacts the key from any
error text. Reusing that executor rather than writing a second HTTP client is
deliberate: there is one place in this repository where a key is touched.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence

import dataclasses
import os

from creib.errors import RecordError
from creib.forge.conformance.executor import API_KEY_ENV, ChatRequest, OllamaChatExecutor
from creib.forge.conformance.spec import Endpoint, endpoint_from_dict, think_setting

from .common import MiniError

#: The endpoint a manifest that declares none is run against: the conformance harness's own
#: shape, read by its own reader. The key is read from OLLAMA_API_KEY at call time inside
#: OllamaChatExecutor and nowhere else; ``auth: none`` sends no key, for a local Ollama.
DEFAULT_ENDPOINT: Endpoint = endpoint_from_dict(
    {
        "kind": "ollama-chat",
        "base_url": "https://ollama.com",
        "timeout_seconds": 180,
        "options": {"temperature": 0, "seed": 7},
        "think": None,
    }
)


def endpoint_from_manifest(raw: Any) -> Endpoint:
    """Read a manifest's endpoint with the conformance harness's reader, refusing as a mini refusal."""

    try:
        return endpoint_from_dict(raw)
    except (RecordError, KeyError, TypeError) as error:
        raise MiniError("MINI_ENDPOINT_INVALID", f"endpoint: {error}") from error


def endpoint_with_overrides(endpoint: Endpoint, think: str | None = None, timeout_seconds: int | None = None) -> Endpoint:
    """A run-time override of the reasoning setting or the call timeout, as the conformance runner takes them.

    The plan is unchanged; the run's record carries what was sent.
    """

    if think is not None:
        raw_think = {"true": True, "false": False, "none": None, "null": None}.get(think.lower(), think)
        try:
            endpoint = dataclasses.replace(endpoint, think=think_setting(raw_think, "--think"))
        except RecordError as error:
            raise MiniError("MINI_ENDPOINT_INVALID", str(error)) from error
    if timeout_seconds is not None:
        if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 3600:
            raise MiniError("MINI_ENDPOINT_INVALID", "--timeout-seconds must be a whole number of seconds from 1 to 3600")
        endpoint = dataclasses.replace(endpoint, timeout_seconds=timeout_seconds)
    return endpoint


@dataclass(frozen=True)
class Request:
    """What a stage asks for, at one coordinate of the run."""

    stage_id: str
    kind_id: str
    attempt: int
    brief: str
    cycle: int = 0
    phase: str = "body"


@dataclass(frozen=True)
class Reply:
    """What came back, with deterministic token counts."""

    text: str
    prompt_tokens: int
    completion_tokens: int


class Responder(Protocol):
    """Anything a stage can be asked through."""

    def reply(self, request: Request) -> Reply: ...


class ScriptedResponder:
    """Prepared replies, in one of two forms, told apart by shape.

    ORDERED — a stage's value is a list, consumed in order. The shorter thing to
    write when a stage runs once and nothing re-orders it.

    BY COORDINATE — a stage's value is an object keyed by cycle, each holding a
    list indexed by attempt. A stage then gets the same reply wherever the cycle
    puts it, so one script drives the same manifest with attention off and on
    and the two runs can be set side by side.

    Both forms may appear in one script, so stages migrate one at a time. A
    phase other than the body reads from the same place: ``<stage>@commitments``
    if the script names it, else the same entry, so a one-call script keeps
    working under the two-call shape.
    """

    def __init__(self, script: Mapping[str, Any]) -> None:
        self._script = {stage: replies for stage, replies in script.items()}
        self._used: dict[str, int] = {}

    @property
    def used(self) -> Mapping[str, int]:
        return dict(self._used)

    def _entry(self, request: Request) -> tuple[Any, str]:
        keyed = f"{request.stage_id}@{request.phase}"
        if keyed in self._script:
            return self._script[keyed], keyed
        # No entry for this phase: the stage's own replies serve it, consumed
        # independently per phase, so one reply carrying both fields drives both
        # calls of the two-call shape.
        return self._script.get(request.stage_id), f"{request.stage_id}#{request.phase}"

    def reply(self, request: Request) -> Reply:
        entry, key = self._entry(request)
        if isinstance(entry, Mapping):
            replies = entry.get(str(request.cycle))
            position = request.attempt
            where = f"stage {request.stage_id!r} at cycle {request.cycle}, attempt {request.attempt}"
        else:
            replies = entry
            position = self._used.get(key, 0)
            where = f"stage {request.stage_id!r}"
        if replies is None or position >= len(replies):
            raise MiniError("MINI_SCRIPT_EXHAUSTED", f"the script has no reply for {where}")
        if not isinstance(entry, Mapping):
            self._used[key] = position + 1
        body = replies[position]
        return Reply(text=body, prompt_tokens=len(request.brief.split()), completion_tokens=len(body.split()))


#: What a live model is asked to return: the template's own fields, and nothing
#: a kind must add. A kind's further optional fields are not offered here.
WIRE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["body", "commitments"],
    "properties": {
        "body": {"type": "string"},
        "commitments": {"type": "string"},
        "citations": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["block", "quote"],
                "properties": {
                    "block": {"type": "string", "minLength": 1},
                    "quote": {"type": "string", "minLength": 1},
                },
            },
        },
        "about": {"type": "array", "items": {"type": "string"}},
        "answers": {"type": "array", "items": {"type": "string"}},
    },
}

SYSTEM = (
    "You fill one artifact. Return JSON only, carrying \"body\" and \"commitments\", "
    "both strings. \"body\" is what you have to say. \"commitments\" is what you are "
    "committing to if it is taken up. If evidence blocks are listed, you may add "
    "\"citations\": each names a block id and quotes that block's own words exactly."
)

SYSTEM_BODY = (
    "You write the BODY of one artifact. Return JSON only, carrying \"body\", a string: "
    "what you have to say. If evidence blocks are listed, you may add \"citations\": "
    "each names a block id and quotes that block's own words exactly. Do not return "
    "commitments; you will be asked for those separately."
)

SYSTEM_COMMITMENTS = (
    "You write the COMMITMENTS of one artifact. Return JSON only, carrying "
    "\"commitments\", a string: what is being committed to if the writing below is "
    "taken up. Return nothing else."
)

#: The wire contract for one phase. A brief that asks for one field and a schema
#: that requires two are contradictory instructions, and a model asked for both
#: at once can only guess which to obey (audit F4).
BODY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["body"],
    "properties": {
        "body": WIRE_SCHEMA["properties"]["body"],
        "citations": WIRE_SCHEMA["properties"]["citations"],
        "about": WIRE_SCHEMA["properties"]["about"],
        "answers": WIRE_SCHEMA["properties"]["answers"],
    },
}

COMMITMENTS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["commitments"],
    "additionalProperties": False,
    "properties": {"commitments": {"type": "string"}},
}

_CONTRACTS: Mapping[str, tuple[str, dict[str, Any]]] = {
    "both": (SYSTEM, WIRE_SCHEMA),
    "body": (SYSTEM_BODY, BODY_SCHEMA),
    "commitments": (SYSTEM_COMMITMENTS, COMMITMENTS_SCHEMA),
}


def contract_for(phase: str) -> tuple[str, dict[str, Any]]:
    """The system instruction and response schema one phase is entitled to."""

    try:
        return _CONTRACTS[phase]
    except KeyError as error:
        raise MiniError(
            "MINI_LIVE_CALL_FAILED",
            f"no live contract for the phase {phase!r}; known: {sorted(_CONTRACTS)}",
        ) from error


class LiveResponder:
    """One model call per attempt, through the harness's own Ollama executor.

    The endpoint is the conformance harness's ``Endpoint``: base URL, timeout, temperature,
    seed, reasoning setting, and auth. The executor built from it is the one place in this
    repository that touches the key. When this responder builds its own executor and the
    endpoint's auth is bearer, an absent key is refused here, before any record is written,
    rather than at the first call with a run already open.
    """

    def __init__(
        self,
        model: str,
        executor: Any | None = None,
        *,
        endpoint: Endpoint = DEFAULT_ENDPOINT,
        retries: int = 0,
    ) -> None:
        self.model = model
        self.endpoint = endpoint
        if executor is None:
            if endpoint.auth == "bearer" and not os.environ.get(API_KEY_ENV):
                raise MiniError(
                    "MINI_LIVE_KEY_MISSING",
                    f"the endpoint's auth is bearer and {API_KEY_ENV} is not set; export it for this process, or set the manifest endpoint's auth to none for a local Ollama",
                )
            executor = OllamaChatExecutor(
                base_url=endpoint.base_url,
                timeout_seconds=endpoint.timeout_seconds,
                retries=retries,
                auth=endpoint.auth,
            )
        self._executor = executor
        self._calls = 0

    @property
    def calls(self) -> int:
        return self._calls

    def reply(self, request: Request) -> Reply:
        self._calls += 1
        system, schema = contract_for(request.phase)
        response = self._executor.complete(
            ChatRequest(
                model=self.model,
                system=system,
                user=request.brief,
                format_schema=schema,
                options={"temperature": self.endpoint.temperature, "seed": self.endpoint.seed},
                think=self.endpoint.think,
            )
        )
        if not response.usable:
            raise MiniError(
                "MINI_LIVE_CALL_FAILED",
                f"the call for stage {request.stage_id!r} did not complete: "
                f"{response.transport_error or response.done_reason or 'no content'}",
            )
        return Reply(
            text=response.content,
            prompt_tokens=response.prompt_eval_count or 0,
            completion_tokens=response.eval_count or 0,
        )
