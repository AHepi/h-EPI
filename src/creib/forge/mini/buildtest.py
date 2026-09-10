"""BUILD-TEST-1: does a proposer that must reconstruct produce what one that may relay does not?

The protocol is ``docs/mini/BUILD_TEST.md``, pre-registered before any arm ran. This module is
its machinery and decides nothing: it asks, it executes, it records.

*Explanatory Construction Semantics 2.0* §6.3 defines an originative act as
``Origin ⟺ Attempt ∧ New ∧ Build``. ``New`` is unestablishable for a model whose repertoire
before the event cannot be inspected (§6.2, the incomplete-archive case), so nothing here can
establish ``Origin`` and nothing here claims to. ``Build`` — "a nontrivial binding construction,
not a composition of content-preserving transfers" — is what two arms are separated on, by
§6.2's own phrase: learner reconstruction counts, relay does not.

Arm **R** is shown the checks' documented rules and no code. Arm **L** is shown the rules and the
complete source. Everything else is identical, the grid of MINI-USE-TEST-1 is gone (§8.3
condition 3), and no defect is seeded: a contradiction here is a place where this repository's
documentation and its behaviour disagree.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping, Sequence

from creib.errors import RecordError
from creib.strict_json import loads_strict

from .common import MiniError
from .usetest import KERNEL_IDS, load_subject, rules_text, run_kernel, subject_source

BUILD_TEST_ID = "build-test-1"

#: The method version. A change to a prompt, an arm, a measure or a path is a new version and a
#: new block, and blocks are never compared arm for arm across versions.
METHOD_VERSION = 1

ARM_RECONSTRUCT = "R"
ARM_RELAY = "L"
ARMS: tuple[str, ...] = (ARM_RECONSTRUCT, ARM_RELAY)

#: The checks a proposal may name. The three that read a whole reply; the grounding pair takes a
#: structured input and is not enumerable from a free-form text (MINI-USE-TEST-1's NON_ENUMERABLE).
OPEN_KERNELS: tuple[str, ...] = ("recovery", "recovered-from-prose", "response-verdict", "refusal-phrase")

PROPOSAL_FIELDS: tuple[str, ...] = ("kernel", "expect", "input", "rewritten", "reading")

PROPOSAL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": list(PROPOSAL_FIELDS),
    "properties": {
        "kernel": {"type": "string", "enum": list(OPEN_KERNELS)},
        "expect": {"type": "string", "enum": ["moves", "unchanged"]},
        "input": {"type": "string"},
        "rewritten": {"type": "string"},
        "reading": {"type": "string"},
    },
}

_TASK = (
    "You are testing one check that reads a model's reply and reports what it found in it.\n\n"
    "Build TWO texts. \"input\" is any reply text you like. \"rewritten\" is a second text, "
    "different from the first — change it however you judge most informative. Then say what the "
    "RULE AS WRITTEN says the check's answer ought to do between the two texts: \"moves\" if the "
    "rule says the answer should differ, \"unchanged\" if the rule says it should stay the same.\n\n"
    "Your expectation must come from the rule's words. Quote the words you read it from in "
    "\"reading\", and name which answer the rule gives for each text.\n\n"
    "Choose the pair that would be most informative about whether the check does what its "
    "description says. A pair whose answer is obvious teaches nothing.\n\n"
    "Write real line breaks in the texts, never the two characters backslash and n. Return JSON "
    "only, one object with exactly these string fields: "
    + ", ".join(f'"{name}"' for name in PROPOSAL_FIELDS)
    + '. "kernel" is one of '
    + ", ".join(OPEN_KERNELS)
    + '. "expect" is "moves" or "unchanged". Write nothing outside the JSON object.'
)

_SHOWN_RULES = (
    "You are shown the checks' documented rules — every definition's signature and its "
    "description — and none of their code. "
)
_SHOWN_SOURCE = (
    "You are shown the checks' documented rules and their complete source. "
)


def brief(arm: str, source: str) -> tuple[str, str]:
    """The system prompt and the user text one arm is given. They differ in one clause and one section."""

    if arm not in ARMS:
        raise MiniError("MINI_BUILDTEST_ARM_UNKNOWN", f"{arm!r} is not an arm; those are {', '.join(ARMS)}")
    system = (_SHOWN_RULES if arm == ARM_RECONSTRUCT else _SHOWN_SOURCE) + _TASK
    user = "## The documented rules of the checks\n\n" + rules_text(source)
    if arm == ARM_RELAY:
        user += "\n\n## The source of the checks\n\n" + source
    return system, user


@dataclass(frozen=True)
class Proposal:
    """One reply, read into the shape the task asked for."""

    kernel: str
    expect: str
    input: str
    rewritten: str
    reading: str

    def to_dict(self) -> dict[str, str]:
        return {name: getattr(self, name) for name in PROPOSAL_FIELDS}


def read_proposal(reply: str) -> Proposal | None:
    """A reply as a proposal, or nothing. A reply that cannot be read is recorded, never repaired."""

    try:
        parsed = loads_strict(reply)
    except RecordError:
        try:
            parsed = loads_strict(reply, control_characters=True)
        except RecordError:
            return None
    if type(parsed) is not dict:
        return None
    values = {name: parsed.get(name) for name in PROPOSAL_FIELDS}
    if any(type(value) is not str for value in values.values()):
        return None
    if values["kernel"] not in OPEN_KERNELS or values["expect"] not in ("moves", "unchanged"):
        return None
    return Proposal(**values)  # type: ignore[arg-type]


#: The one boundary this repository already knows about, as a predicate over a pair rather than a
#: string match: a fence holding a sentence beside its object, scored on a bare object after it.
def reproduces_h43(subject: ModuleType, text: str) -> bool:
    """Does this text exhibit H43 — a fence holding prose and an object, with a bare object after?"""

    if "```" not in text:
        return False
    head, _, tail = text.rpartition("```")
    if not tail.strip() or not tail.strip().startswith("{"):
        return False
    inside = head.split("```")
    if len(inside) < 2:
        return False
    fenced = inside[-1]
    has_prose = any(line.strip() and not line.strip().startswith(("{", "[")) for line in fenced.splitlines())
    has_object = "{" in fenced
    return bool(has_prose and has_object)


@dataclass
class Execution:
    """What the machine did with one proposal. Nothing here is a verdict."""

    proposal: Proposal
    executed: str
    before: str = ""
    after: str = ""
    detail: str = ""

    @property
    def contradicted(self) -> bool:
        if self.executed not in ("moved", "unchanged"):
            return False
        return (self.executed == "moved") != (self.proposal.expect == "moves")

    @property
    def behaviour(self) -> tuple[str, str, str]:
        return (self.proposal.kernel, self.before, self.after)

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.proposal.to_dict(),
            "executed": self.executed,
            "before": self.before,
            "after": self.after,
            "detail": self.detail,
            "contradicted": self.contradicted,
        }


def execute(subject: ModuleType, proposal: Proposal) -> Execution:
    """Run the named check on both texts. A degenerate pair is recorded as such, never scored."""

    if proposal.input == proposal.rewritten:
        return Execution(proposal, "degenerate", detail="the two texts are the same text")
    if not proposal.input.strip() or not proposal.rewritten.strip():
        return Execution(proposal, "degenerate", detail="one of the texts is empty")
    try:
        before = run_kernel(subject, proposal.kernel, proposal.input)
        after = run_kernel(subject, proposal.kernel, proposal.rewritten)
    except MiniError as error:
        return Execution(proposal, "unrunnable", detail=str(error))
    return Execution(proposal, "moved" if before != after else "unchanged", before=before, after=after)


# --- the two paths a call may take, and the one place each key is read ---

#: Where the vendor key is read from, as a path to a file. The key is never a value in a manifest,
#: a record, a log or an exception; it is read at call time and nowhere else.
DEEPSEEK_KEY_FILE_ENV = "DEEPSEEK_KEY_FILE"
OLLAMA_KEY_ENV = "OLLAMA_API_KEY"

PATH_OLLAMA = "ollama.com"
PATH_DEEPSEEK = "api.deepseek.com"
PATHS: tuple[str, ...] = (PATH_OLLAMA, PATH_DEEPSEEK)


@dataclass(frozen=True)
class Endpoint:
    """What a call is sent to, and what the record says it was sent to.

    ``quantised`` is declared, not detected: ``api.deepseek.com`` serves the vendor's own weights
    and ``ollama.com`` may serve quantised ones, which makes one model on both paths a
    quantisation comparison at fixed prompt. Nothing here verifies the claim; it records which
    path was used so a reader can.
    """

    path: str
    model: str
    think: bool | str | None
    timeout_seconds: int = 900
    max_tokens: int | None = None

    @property
    def quantisation(self) -> str:
        return "vendor weights, unquantised" if self.path == PATH_DEEPSEEK else "unknown, may be quantised"

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "model": self.model,
            "think": self.think,
            "timeout_seconds": self.timeout_seconds,
            "max_tokens": self.max_tokens,
            "quantisation": self.quantisation,
        }


@dataclass
class Reply:
    """One call's outcome, whether or not it produced anything readable."""

    text: str
    completion_tokens: int
    prompt_tokens: int
    elapsed_s: int
    ok: bool
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "completion_tokens": self.completion_tokens,
            "prompt_tokens": self.prompt_tokens,
            "elapsed_s": self.elapsed_s,
            "ok": self.ok,
            "detail": self.detail,
        }


def _post(url: str, body: dict[str, Any], key: str, timeout: int) -> tuple[int, bytes]:
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + key},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return int(response.status), response.read()
    except urllib.error.HTTPError as error:
        try:
            raw = error.read()
        except (OSError, ValueError):
            raw = b""
        return int(error.code), raw


def ask(endpoint: Endpoint, system: str, user: str) -> Reply:
    """One call on the declared path. The key is read here and appears in nothing this returns."""

    started = time.monotonic()
    if endpoint.path == PATH_OLLAMA:
        key = os.environ.get(OLLAMA_KEY_ENV, "")
        if not key:
            raise MiniError("MINI_BUILDTEST_KEY_MISSING", f"{OLLAMA_KEY_ENV} is not set, so no call can be made")
        options: dict[str, int] = {"temperature": 0, "seed": 7}
        if endpoint.max_tokens is not None:
            options["num_predict"] = endpoint.max_tokens
        body: dict[str, Any] = {
            "model": endpoint.model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "stream": False,
            "options": options,
            "format": PROPOSAL_SCHEMA,
        }
        if endpoint.think is not None:
            body["think"] = endpoint.think
        status, raw = _post("https://ollama.com/api/chat", body, key, endpoint.timeout_seconds)
    elif endpoint.path == PATH_DEEPSEEK:
        where = os.environ.get(DEEPSEEK_KEY_FILE_ENV, "")
        if not where or not Path(where).is_file():
            raise MiniError("MINI_BUILDTEST_KEY_MISSING", f"{DEEPSEEK_KEY_FILE_ENV} names no readable file")
        key = Path(where).read_text(encoding="utf-8").strip()
        body = {
            "model": endpoint.model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "stream": False,
        }
        if endpoint.max_tokens is not None:
            body["max_tokens"] = endpoint.max_tokens
        status, raw = _post("https://api.deepseek.com/chat/completions", body, key, endpoint.timeout_seconds)
    else:
        raise MiniError("MINI_BUILDTEST_PATH_UNKNOWN", f"{endpoint.path!r} is not a path; those are {', '.join(PATHS)}")

    elapsed = int(time.monotonic() - started)
    redacted = raw.decode("utf-8", errors="replace").replace(key, "<redacted>")
    if status != 200:
        return Reply("", 0, 0, elapsed, False, f"HTTP {status}: {redacted[:300]}")
    try:
        parsed = json.loads(redacted)
    except ValueError as error:
        return Reply("", 0, 0, elapsed, False, f"the body is not JSON: {error}")
    if endpoint.path == PATH_OLLAMA:
        message = parsed.get("message") or {}
        text = str(message.get("content") or "")
        return Reply(text, int(parsed.get("eval_count") or 0), int(parsed.get("prompt_eval_count") or 0),
                     elapsed, bool(text.strip()), "" if text.strip() else "the reply carried no content")
    choice = (parsed.get("choices") or [{}])[0]
    text = str(((choice.get("message") or {}).get("content")) or "")
    usage = parsed.get("usage") or {}
    return Reply(text, int(usage.get("completion_tokens") or 0), int(usage.get("prompt_tokens") or 0),
                 elapsed, bool(text.strip()), "" if text.strip() else "the reply carried no content")


# --- a condition, its run, and the measures the protocol fixed before any of it ran ---


@dataclass(frozen=True)
class Condition:
    """One cell of the design: an arm, an endpoint, and how many proposals to ask for."""

    arm: str
    endpoint: Endpoint
    proposals: int = 10
    grid_cells: tuple[str, ...] = ()

    @property
    def condition_id(self) -> str:
        grid = "grid" if self.grid_cells else "nogrid"
        think = {True: "think-on", False: "think-off", None: "think-default"}.get(self.endpoint.think, str(self.endpoint.think))
        return f"{self.endpoint.path}/{self.endpoint.model}/arm-{self.arm}/{think}/{grid}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "condition_id": self.condition_id,
            "arm": self.arm,
            "endpoint": self.endpoint.to_dict(),
            "proposals_requested": self.proposals,
            "grid_cells": list(self.grid_cells),
        }


def run_condition(condition: Condition, subject: ModuleType, source: str) -> dict[str, Any]:
    """Ask, execute, record. Each proposal is one call; nothing is retried and nothing is repaired."""

    system, user = brief(condition.arm, source)
    executions: list[Execution] = []
    calls: list[dict[str, Any]] = []
    seen: list[str] = []
    for index in range(condition.proposals):
        shown = user
        if condition.grid_cells:
            shown += "\n\n## The shape to build\n\n" + condition.grid_cells[index % len(condition.grid_cells)]
        if seen:
            # A proposer that repeats itself measures nothing twice (mini register M10), so the
            # pairs already built are shown back. This is the run's own history, never a hint.
            shown += "\n\n## Pairs you have already built, which you may not repeat\n\n" + "\n\n".join(seen[-8:])
        reply = ask(condition.endpoint, system, shown)
        calls.append({"index": index, **reply.to_dict()})
        if not reply.ok:
            continue
        proposal = read_proposal(reply.text)
        if proposal is None:
            calls[-1]["detail"] = calls[-1]["detail"] or "the reply could not be read as a proposal"
            continue
        seen.append(f"{proposal.kernel}: {proposal.input[:160]!r} -> {proposal.rewritten[:160]!r}")
        executions.append(execute(subject, proposal))
    return {
        "condition": condition.to_dict(),
        "method_version": METHOD_VERSION,
        "calls": calls,
        "executions": [item.to_dict() for item in executions],
        "measures": measures(executions, subject),
    }


def measures(executions: Sequence[Execution], subject: ModuleType) -> dict[str, Any]:
    """The six measures the protocol fixed. None is a score and no arm is ranked by them."""

    ran = [item for item in executions if item.executed in ("moved", "unchanged")]
    contradicted = [item for item in ran if item.contradicted]
    behaviours = sorted({item.behaviour for item in ran})
    return {
        "proposals": len(executions),
        "executed": len(ran),
        "degenerate": sum(1 for item in executions if item.executed == "degenerate"),
        "unrunnable": sum(1 for item in executions if item.executed == "unrunnable"),
        "contradicted": len(contradicted),
        "distinct_behaviours": len(behaviours),
        "behaviours": [list(item) for item in behaviours],
        "reproduces_h43": sum(1 for item in contradicted if reproduces_h43(subject, item.proposal.input)),
        "contradictions": [item.to_dict() for item in contradicted],
    }


def unique_to_arm(this: Mapping[str, Any], other: Mapping[str, Any]) -> list[list[str]]:
    """Behaviour triples this condition produced that the other did not. §6.2's measure."""

    mine = {tuple(item) for item in this["measures"]["behaviours"]}
    theirs = {tuple(item) for item in other["measures"]["behaviours"]}
    return [list(item) for item in sorted(mine - theirs)]
