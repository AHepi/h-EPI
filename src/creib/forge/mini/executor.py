"""The responder a stage is asked through.

Only one is shipped and it calls nothing: a scripted responder that returns
prepared replies in a fixed order per stage. It is deterministic, so a run of
the same plan against the same script writes the same record twice, and no test
in this package needs a network or a key.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from .common import MiniError


@dataclass(frozen=True)
class Request:
    """What a stage asks for."""

    stage_id: str
    kind_id: str
    attempt: int
    brief: str


@dataclass(frozen=True)
class Reply:
    """What came back, with deterministic token counts."""

    text: str
    prompt_tokens: int
    completion_tokens: int


class ScriptedResponder:
    """A prepared reply per stage, consumed in order.

    Retries consume the next reply for that stage, so a script can answer badly
    first and well second and the run exercises the retry road exactly.
    """

    def __init__(self, script: Mapping[str, Sequence[str]]) -> None:
        self._script = {stage: list(replies) for stage, replies in script.items()}
        self._used: dict[str, int] = {}

    @property
    def used(self) -> Mapping[str, int]:
        return dict(self._used)

    def reply(self, request: Request) -> Reply:
        replies = self._script.get(request.stage_id)
        position = self._used.get(request.stage_id, 0)
        if replies is None or position >= len(replies):
            raise MiniError(
                "MINI_SCRIPT_EXHAUSTED",
                f"the script has no further reply for the stage {request.stage_id!r}",
            )
        self._used[request.stage_id] = position + 1
        body = replies[position]
        return Reply(text=body, prompt_tokens=len(request.brief.split()), completion_tokens=len(body.split()))
