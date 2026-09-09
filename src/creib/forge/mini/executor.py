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

from creib.forge.conformance.executor import ChatRequest, OllamaChatExecutor

from .common import MiniError


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


class LiveResponder:
    """One model call per attempt, through the harness's own Ollama executor."""

    def __init__(
        self,
        model: str,
        executor: Any | None = None,
        *,
        seed: int = 7,
        timeout_seconds: int = 180,
        retries: int = 0,
    ) -> None:
        self.model = model
        self._executor = (
            executor
            if executor is not None
            else OllamaChatExecutor(timeout_seconds=timeout_seconds, retries=retries)
        )
        self._seed = seed
        self._calls = 0

    @property
    def calls(self) -> int:
        return self._calls

    def reply(self, request: Request) -> Reply:
        self._calls += 1
        response = self._executor.complete(
            ChatRequest(
                model=self.model,
                system=SYSTEM,
                user=request.brief,
                format_schema=WIRE_SCHEMA,
                options={"temperature": 0, "seed": self._seed},
                think=None,
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
