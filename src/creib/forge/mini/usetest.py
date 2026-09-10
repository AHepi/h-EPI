"""MINI-USE-TEST-1: the machinery for a comparison in which mini is allowed to lose.

The audit of 10 September asked for a decisive comparison and this repository owed it one. The
protocol (``docs/mini/USE_TEST.md``) puts five arms on the same hidden condition: a direct
audit, a tool-assisted adversary that may execute what it likes, mini's small core, full mini
with attention off, and full mini with attention on. Nothing here favours any of them.

Three pieces live here.

**A subject.** The code under test is a copy of the conformance harness's own reply-reading
functions, generated from their real source, so a seeded defect never touches this tree and the
functions are the ones the harness actually runs. A subject is a file; a mutation is a string
substitution in that file, recorded in a manifest a seat never sees.

**A frozen grammar with validators.** A cell of the recovery grid is a shape written in a
notation, and its validator compiles to predicates over the concrete text a seat built: one
fenced region, this much prose inside it, a distinct object after it. A cell counts as covered
only when a validator proves the executed text satisfies it — an assignment is a reservation
and an instantiation is a claim (the audit's F-A, its anti-cheating rule, and mini register
M12).

**A neutral packet.** Every arm ends in the same eight fields, with nothing in them that says
which arm or model produced it, so the adjudication can be blind.

Nothing in this module decides whether a claim is a defect. The sealed manifest is the truth
criterion for a seeded stratum, and it is opened after the packets are written.
"""

from __future__ import annotations

import ast
import importlib.util
import inspect
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Mapping, Sequence

from creib.errors import RecordError
from creib.forge.conformance import oracle
from creib.strict_json import loads_strict

from .common import MiniError

USE_TEST_ID = "mini-use-test-1"
#: The method version. The protocol forbids editing prompts, grids, validators or special cases
#: inside a registered block: a change makes a new method version and starts a new block.
#: Version 1 threw away a fenced packet, let a mini arm spend past the shared ceiling, and told a
#: proposer to remove a part from cells that have only one, so its first cells could not be
#: instantiated at all. Version 2 trusted the proposal's echo of the cell it had been given, so a
#: seat that copied the rendered port text instead of the cell failed validation for the
#: rendering's fault; version 3 takes the assigned cell from the assignment. Every break is
#: recorded in ``docs/mini/USE_TEST.md``.
METHOD_VERSION = 3

#: The harness functions a subject is built around. Everything they reach is copied with them:
#: the closure is computed from the source rather than listed, so a subject cannot go stale
#: against the code it is a copy of.
SUBJECT_SEEDS: tuple[str, ...] = (
    "recover_json_object",
    "_loads_last_wins",
    "_plain_quotes",
    "refusal_phrase_in",
    "parse_content",
    "_normalise_whitespace",
    "_span_occurs",
)


def subject_closure() -> tuple[str, ...]:
    """Every module-level name in ``oracle`` the seeds reach, in an order that defines before use."""

    tree = ast.parse(inspect.getsource(oracle))
    functions = {node.name: node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
    assignments = {
        target.id: node
        for node in tree.body
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    order: list[str] = []
    seen: set[str] = set()

    def visit(name: str) -> None:
        if name in seen:
            return
        seen.add(name)
        node = functions.get(name) or assignments.get(name)
        if node is None:
            return
        for inner in ast.walk(node):
            if isinstance(inner, ast.Name) and inner.id != name and (inner.id in functions or inner.id in assignments):
                visit(inner.id)
        order.append(name)

    for seed in SUBJECT_SEEDS:
        visit(seed)
    return tuple(order)


def _source_of(name: str) -> str:
    """One module-level name's source: a function whole, an assignment as it is written."""

    tree = ast.parse(inspect.getsource(oracle))
    lines = inspect.getsource(oracle).splitlines()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name == name:
            return inspect.getsource(getattr(oracle, name)).rstrip()
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return "\n".join(lines[node.lineno - 1 : node.end_lineno]).rstrip()
    raise MiniError("MINI_USETEST_SUBJECT_UNREADABLE", f"the oracle has no module-level {name!r} to copy")

#: The refusal phrases a subject reads with: the travel-claim pilot's list, fixed here so a
#: kernel is a function of the text alone.
REFUSAL_PHRASES: tuple[str, ...] = ("I cannot", "I can't", "I'm sorry", "I am unable", "as an AI", "cannot assist")

_SUBJECT_TAIL = '''

# --- the kernels: each a function of one text, as every arm sees them ---

NO_OBJECT = "NO_OBJECT"
NO_PHRASE = "NONE"
UNREADABLE = "UNREADABLE_INPUT"


def k_recovery(text):
    """The object recovered from the reply, as canonical JSON text, or NO_OBJECT."""

    try:
        value, _duplicates = recover_json_object(text)
    except RecordError:
        return NO_OBJECT
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def k_recovered_from_prose(text):
    """Whether the object had to be recovered from prose or a fence (yes) or read strictly (no)."""

    return "yes" if parse_content(text, REFUSAL_PHRASES)[3] else "no"


def k_response_verdict(text):
    """The response verdict for the reply."""

    return parse_content(text, REFUSAL_PHRASES)[1]


def k_refusal_phrase(text):
    """The first listed refusal phrase the reply contains, or NONE."""

    return refusal_phrase_in(text, REFUSAL_PHRASES) or NO_PHRASE


def _fields(text, *names):
    try:
        parsed = loads_strict(text)
    except RecordError:
        try:
            parsed = loads_strict(text, control_characters=True)
        except RecordError:
            return None
    if type(parsed) is not dict or any(type(parsed.get(name)) is not str for name in names):
        return None
    return {name: str(parsed[name]) for name in names}


def k_span_occurs(text):
    """Whether a cited span occurs in a document: the input is one JSON object {span, document}."""

    fields = _fields(text, "span", "document")
    if fields is None:
        return UNREADABLE
    matched = _span_occurs(fields["span"], fields["document"], ())
    return "NOT_IN_DOCUMENT" if matched is None else matched


def k_grounding(text):
    """The grounding verdict: the input is one JSON object {value, span, document}."""

    fields = _fields(text, "value", "span", "document")
    if fields is None:
        return UNREADABLE
    if not fields["span"].strip():
        return "SPAN_MISSING"
    if _span_occurs(fields["span"], fields["document"], ()) is None:
        return "SPAN_NOT_IN_DOCUMENT"
    if _normalise_whitespace(fields["value"]).casefold() not in _normalise_whitespace(fields["span"]).casefold():
        return "VALUE_NOT_IN_SPAN"
    return "GROUNDED"


KERNELS = {
    "recovery": k_recovery,
    "recovered-from-prose": k_recovered_from_prose,
    "response-verdict": k_response_verdict,
    "refusal-phrase": k_refusal_phrase,
    "span-occurs": k_span_occurs,
    "grounding": k_grounding,
}
'''

KERNEL_IDS: tuple[str, ...] = (
    "recovery",
    "recovered-from-prose",
    "response-verdict",
    "refusal-phrase",
    "span-occurs",
    "grounding",
)


def subject_source() -> str:
    """The subject module's text: the harness's own functions, copied, with kernels over them."""

    head = "\n".join(
        [
            '"""The code under test. Generated from the conformance harness\'s own source."""',
            "",
            "from __future__ import annotations",
            "",
            "import json",
            "import re",
            "from typing import Any",
            "",
            "from creib.errors import RecordError",
            "from creib.strict_json import loads_strict",
            "",
            f"REFUSAL_PHRASES = {list(REFUSAL_PHRASES)!r}",
            "",
            "",
        ]
    )
    bodies = [_source_of(name) for name in subject_closure()]
    return head + "\n\n\n".join(bodies) + _SUBJECT_TAIL


@dataclass(frozen=True)
class Mutation:
    """One hidden condition: a substitution in the subject, and the truth about it.

    ``find`` must occur exactly once in the clean subject, so that a mutation is a single
    determinate edit. ``reproducer`` is the minimal input whose kernel answer the edit changes,
    and ``clean`` and ``mutated`` are what that kernel returns either side of it. A stratum of
    ``S6`` carries no edit at all.
    """

    mutation_id: str
    stratum: str
    kernel: str
    find: str
    replace: str
    reproducer: str
    consequence: str
    dimensions: tuple[str, ...] = ()

    @property
    def seeded(self) -> bool:
        return bool(self.find)


CLEAN = Mutation("clean", "S6", "", "", "", "", "no edit: the subject is the harness's own code")

#: The corpus, frozen before any mutation is drawn. S1 changes one path; S2 preserves every
#: one-dimensional behaviour and breaks a conjunction of two.
CORPUS: tuple[Mutation, ...] = (
    Mutation(
        "s1-whitespace-strip",
        "S1",
        "span-occurs",
        'return " ".join(value.split())',
        "return value.strip()",
        json.dumps({"span": "five  days", "document": "Amara was away for five days."}),
        "the occurrence check no longer folds a run of spaces inside the span",
        ("whitespace",),
    ),
    Mutation(
        "s1-refusal-last-wins",
        "S1",
        "refusal-phrase",
        "    for phrase in refusal_phrases:\n        if _plain_quotes(phrase).lower() in lowered:\n            return phrase\n    return None",
        "    found = [phrase for phrase in refusal_phrases if _plain_quotes(phrase).lower() in lowered]\n    return found[-1] if found else None",
        "I cannot help with that, as an AI.",
        "the phrase reported is the list's last match rather than its first",
        ("two phrases",),
    ),
    Mutation(
        "s1-quotes-not-folded",
        "S1",
        "refusal-phrase",
        "    return text.translate(_TYPOGRAPHIC_QUOTES)",
        "    return text",
        "I\u2019m sorry, that is not possible.",
        "a typographic apostrophe is no longer folded, so a phrase written with one is missed",
        ("apostrophe",),
    ),
    Mutation(
        "s2-fence-single-only",
        "S2",
        "recovery",
        "    for pool in (fenced, top_level):",
        "    for pool in ((fenced if len(fenced) == 1 else []), top_level):",
        '```json\n{"a": 1}\n```\n```json\n{"b": 2}\n```\n{"z": 9}',
        "a fenced object is preferred only when the reply holds exactly one fence, so two fences fall through to the last top-level object",
        ("two fences", "a bare object after them"),
    ),
    Mutation(
        "s2-duplicates-outside-fence-only",
        "S2",
        "recovery",
        "                parsed = _loads_last_wins(candidate.strip())",
        "                parsed = None if pool is fenced else _loads_last_wins(candidate.strip())",
        '```json\n{"a": 1, "a": 2}\n```\n{"z": 9}',
        "a repeated key is resolved last-wins only outside a fence, so a fenced object carrying one is passed over for whatever follows",
        ("inside a fence", "a repeated key", "an object after the fence"),
    ),
    Mutation(
        "s2-span-normalised-one-side",
        "S2",
        "span-occurs",
        "    normal_span, normal_document = _normalise_whitespace(span), _normalise_whitespace(document)",
        "    normal_span, normal_document = span, _normalise_whitespace(document)",
        json.dumps({"span": "five  days", "document": "Amara was away for five days."}),
        "the document is whitespace-normalised and the span is not, so only a span with irregular spacing fails",
        ("irregular span", "regular document"),
    ),
)

CORPUS_BY_ID: Mapping[str, Mutation] = {item.mutation_id: item for item in CORPUS}


def apply_mutation(source: str, mutation: Mutation) -> str:
    """Apply one mutation to a clean subject, refusing anything that is not a single edit."""

    if not mutation.seeded:
        return source
    found = source.count(mutation.find)
    if found != 1:
        raise MiniError(
            "MINI_USETEST_MUTATION_UNPLACED",
            f"{mutation.mutation_id}: its text occurs {found} times in the subject, and a mutation is one edit",
        )
    return source.replace(mutation.find, mutation.replace, 1)


def load_subject(path: Path) -> ModuleType:
    """Import a subject file by path, without putting it on the import path."""

    spec = importlib.util.spec_from_file_location(f"creib_usetest_subject_{abs(hash(str(path)))}", path)
    if spec is None or spec.loader is None:
        raise MiniError("MINI_USETEST_SUBJECT_UNREADABLE", f"{path} cannot be imported as a subject")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_kernel(subject: ModuleType, kernel_id: str, text: str) -> str:
    """One kernel of one subject on one text. Any refusal inside the subject is its answer."""

    kernels = getattr(subject, "KERNELS", {})
    if kernel_id not in kernels:
        raise MiniError("MINI_USETEST_UNKNOWN_KERNEL", f"no kernel {kernel_id!r}; known: {sorted(kernels)}")
    try:
        return str(kernels[kernel_id](text))
    except (RecordError, ValueError, RecursionError, TypeError) as error:
        return f"RAISED:{type(error).__name__}"


# --- the frozen grammar, and the validator that decides whether a text is the cell it claims ---

#: A token of a cell: one prose sentence, or an object named by a letter. Two letters name two
#: objects that must differ; the same letter twice names the same object written twice.
_OBJECT_TOKENS: tuple[str, ...] = ("A", "B", "C")
_PROSE_TOKEN = "S"

_FENCE_LINE = re.compile(r"^\s*```")


@dataclass(frozen=True)
class Cell:
    """One cell of a frozen grammar: what a fence holds, and what follows it."""

    cell_id: str
    inside: tuple[str, ...]
    after: tuple[str, ...]

    @property
    def notation(self) -> str:
        held = " ".join(self.inside)
        tail = " ".join(f"fence[ {token[6:-1]} ]" if token.startswith("fence[") else token for token in self.after)
        return f"fence[ {held} ]" + (f" {tail}" if tail else "")


def parse_cell(notation: str) -> Cell:
    """Read a cell written in the notation the grids use, refusing anything else."""

    text = " ".join(notation.split())
    match = re.fullmatch(r"fence\[ (?P<inside>[^\]]*) \](?P<after>.*)", text)
    if match is None:
        raise MiniError("MINI_USETEST_CELL_UNREADABLE", f"{notation!r} is not a cell of this grammar")
    inside = tuple(token for token in match.group("inside").split() if token)
    rest = match.group("after").strip()
    after: list[str] = []
    while rest:
        second = re.match(r"fence\[ ([^\]]*) \]", rest)
        if second is not None:
            after.append(f"fence[{second.group(1).strip()}]")
            rest = rest[second.end() :].strip()
            continue
        token, _, rest = rest.partition(" ")
        after.append(token.strip())
        rest = rest.strip()
    for token in inside + tuple(after):
        bare = token[6:-1] if token.startswith("fence[") else token
        if bare not in _OBJECT_TOKENS + (_PROSE_TOKEN,):
            raise MiniError("MINI_USETEST_CELL_UNREADABLE", f"{notation!r} names {token!r}, which the grammar does not hold")
    return Cell(text, inside, tuple(after))


def _classify(line: str) -> tuple[str, str] | None:
    """One line of a built reply: an object, a sentence, or nothing at all."""

    stripped = line.strip()
    if not stripped:
        return None
    try:
        value = json.loads(stripped)
    except (ValueError, RecursionError):
        return ("prose", stripped)
    return ("object", json.dumps(value, sort_keys=True, separators=(",", ":"))) if type(value) is dict else ("prose", stripped)


def _regions(text: str) -> tuple[list[list[str]], list[tuple[str, str]]]:
    """The fenced regions of a text, and everything outside them, line by line."""

    fenced: list[list[str]] = []
    outside: list[tuple[str, str]] = []
    current: list[str] | None = None
    for line in text.split("\n"):
        if _FENCE_LINE.match(line):
            if current is None:
                current = []
            else:
                fenced.append(current)
                current = None
            outside.append(("fence", ""))
            continue
        if current is not None:
            current.append(line)
            continue
        classified = _classify(line)
        if classified is not None:
            outside.append(classified)
    if current is not None:
        fenced.append(current)
    return fenced, outside


def validate_cell(notation: str, text: str) -> str | None:
    """Prove that a built reply is the cell it claims to be, or say why it is not.

    This is the anti-cheating rule of the protocol: a cell is covered when a validator shows the
    text that actually ran satisfies its predicates, never when a seat was handed the cell or
    said it had built it. Everything checked here is syntactic — how many fenced regions there
    are, what each holds line by line, which objects are equal — so the validator never decides
    what any kernel should answer.
    """

    cell = parse_cell(notation)
    fenced, outside = _regions(text)
    wanted_fences = 1 + sum(1 for token in cell.after if token.startswith("fence["))
    if len(fenced) != wanted_fences:
        return f"the cell wants {wanted_fences} fenced region(s) and the text has {len(fenced)}"

    def shape(lines: Sequence[str]) -> tuple[list[str], list[str]]:
        kinds: list[str] = []
        values: list[str] = []
        for line in lines:
            classified = _classify(line)
            if classified is None:
                continue
            kinds.append(classified[0])
            values.append(classified[1])
        return kinds, values

    bindings: dict[str, str] = {}

    def bind(token: str, kind: str, value: str) -> str | None:
        if token == _PROSE_TOKEN:
            return None if kind == "prose" else f"the cell wants a sentence where the text has {kind}"
        if kind != "object":
            return f"the cell wants object {token} where the text has {kind}"
        if token in bindings and bindings[token] != value:
            return f"object {token} is written twice with different content"
        if token not in bindings and value in bindings.values():
            return f"object {token} is the same as another object the cell names apart"
        bindings[token] = value
        return None

    inside_kinds, inside_values = shape(fenced[0])
    if len(inside_kinds) != len(cell.inside):
        return f"the fence should hold {len(cell.inside)} part(s) and holds {len(inside_kinds)}"
    for token, kind, value in zip(cell.inside, inside_kinds, inside_values):
        reason = bind(token, kind, value)
        if reason is not None:
            return reason

    tail = [item for item in outside if item[0] != "fence"]
    expected_tail = [token for token in cell.after if not token.startswith("fence[")]
    if len(tail) != len(expected_tail):
        return f"the cell wants {len(expected_tail)} part(s) after the fence and the text has {len(tail)}"
    for token, (kind, value) in zip(expected_tail, tail):
        reason = bind(token, kind, value)
        if reason is not None:
            return reason

    second_fences = [token[6:-1] for token in cell.after if token.startswith("fence[")]
    for index, token in enumerate(second_fences, start=1):
        kinds, values = shape(fenced[index])
        if len(kinds) != 1:
            return f"the second fence should hold one part and holds {len(kinds)}"
        reason = bind(token, kinds[0], values[0])
        if reason is not None:
            return reason
    return None


#: The frozen recovery grid: what a fence holds by what follows it. Written before any mutation
#: was drawn, and every cell of it has a validator by construction.
RECOVERY_GRID: tuple[str, ...] = tuple(
    f"fence[ {held} ]" + (f" {tail}" if tail else "")
    for held in ("A", "S A", "A S", "A B")
    for tail in ("", "S", "C" if held == "A B" else "B", "A", "fence[ C ]" if held == "A B" else "fence[ B ]")
)

def cell_of(text: str, grid: Sequence[str] = ()) -> str | None:
    """Which cell of the grammar a text is, if any: the rewrite lands in a different cell.

    A pair removes one part, so the rewritten text cannot be the cell the input was; it must
    still be a shape the grammar holds, or nobody can say what was run.
    """

    for cell in grid or RECOVERY_GRID:
        if validate_cell(cell, text) is None:
            return cell
    return None


#: Families whose space cannot be enumerated with a validator that does not decide the question
#: the kernel is there to answer. A span occurs in a document or it does not, and checking that
#: a cell is instantiated *is* the occurrence check; the protocol's rule is to mark the family
#: non-enumerable rather than to pretend (MINI-USE-TEST-1, "Construction validation").
NON_ENUMERABLE: Mapping[str, str] = {
    "span-occurs": "whether a span stands in a given relation to a document is the question the kernel answers",
    "grounding": "the same, with the value's containment added",
}


# --- the neutral packet every arm ends in, and the dispositions an adjudicator may give ---

#: The eight fields, in the order the protocol lists them. Nothing here names an arm or a model.
PACKET_FIELDS: tuple[str, ...] = (
    "claim",
    "expected",
    "observed",
    "reproducer",
    "source_basis",
    "execution_evidence",
    "scope",
    "uncertainty",
)

#: What an adjudicator may say about one packet, and nothing else.
DISPOSITIONS: tuple[str, ...] = (
    "TRUE_DEFECT",
    "TRUE_BOUNDARY",
    "AMBIGUOUS_SPEC",
    "INVALID_TEST",
    "ALREADY_DOCUMENTED",
    "FALSE_POSITIVE",
    "NO_FINDING",
    "OUT_OF_DOMAIN",
)

PACKET_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": list(PACKET_FIELDS),
    "properties": {name: {"type": "string"} for name in PACKET_FIELDS},
}

#: Words that would tell a blinded adjudicator which arm wrote a packet. A packet carrying one
#: is not silently cleaned: it is reported, because a leak is a fact about the run.
_FINGERPRINTS: tuple[str, ...] = (
    "mini",
    "arm ",
    "kernel",
    "cell",
    "grid",
    "manifest",
    "gemma",
    "qwen",
    "mistral",
    "nemotron",
    "proposal",
    "verdict",
    "cycle",
)


@dataclass(frozen=True)
class Packet:
    """One candidate, as every arm must end."""

    fields: Mapping[str, str]
    instance_id: str
    arm: str
    model: str

    def neutral(self) -> dict[str, str]:
        """The eight fields alone, in order, with nothing that says who wrote them."""

        return {name: str(self.fields.get(name, "")) for name in PACKET_FIELDS}

    def leaks(self) -> tuple[str, ...]:
        """Words in the packet that would tell an adjudicator which arm produced it."""

        text = " ".join(self.neutral().values()).lower()
        return tuple(word for word in _FINGERPRINTS if word in text)


def packet_from(raw: Any, instance_id: str, arm: str, model: str) -> Packet | None:
    """Read a packet out of whatever an arm returned, or nothing if it did not write one.

    A model that wraps its JSON in a code fence has written a packet, and version 1 of this
    machinery threw it away: an arm that had found something was recorded as having found
    nothing, which would have biased the comparison in favour of whichever arm happened to
    fence less. The fence is stripped as mini strips it everywhere else.
    """

    if type(raw) is str:
        from .kinds import strip_fence

        unfenced, _fenced = strip_fence(raw)
        for candidate in (unfenced, raw):
            for lenient in (False, True):
                try:
                    raw = loads_strict(candidate, control_characters=lenient)
                except RecordError:
                    continue
                break
            else:
                continue
            break
        else:
            return None
    if type(raw) is not dict:
        return None
    if not any(type(raw.get(name)) is str and raw[name].strip() for name in ("claim", "observed")):
        return None
    return Packet({name: str(raw.get(name, "")) for name in PACKET_FIELDS}, instance_id, arm, model)


@dataclass
class Ceiling:
    """The resource ceiling every arm shares on one hidden instance.

    The protocol's primary causal comparison is at a common ceiling, so the ceiling is counted
    here rather than trusted to a prompt: an arm that has spent its invocations or its
    completion tokens is not asked again.
    """

    invocations: int = 8
    completion_tokens: int = 12_000
    used_invocations: int = 0
    used_prompt_tokens: int = 0
    used_completion_tokens: int = 0
    machine_executions: int = 0

    @property
    def spent(self) -> bool:
        return self.used_invocations >= self.invocations or self.used_completion_tokens >= self.completion_tokens

    def charge(self, prompt_tokens: int, completion_tokens: int) -> None:
        self.used_invocations += 1
        self.used_prompt_tokens += max(0, prompt_tokens)
        self.used_completion_tokens += max(0, completion_tokens)

    def as_dict(self) -> dict[str, int]:
        return {
            "invocations_allowed": self.invocations,
            "completion_tokens_allowed": self.completion_tokens,
            "invocations": self.used_invocations,
            "prompt_tokens": self.used_prompt_tokens,
            "completion_tokens": self.used_completion_tokens,
            "machine_executions": self.machine_executions,
        }


# --- the arms that do not use mini: a direct audit, and an adversary that may execute ---

_PACKET_INSTRUCTION = (
    "Return JSON only, one object carrying exactly these string fields: "
    + ", ".join(f'"{name}"' for name in PACKET_FIELDS)
    + '. "claim" is what is wrong, "expected" the behaviour the supplied rule justifies, "observed" what the code '
    'actually does, "reproducer" one exact input, "source_basis" the words of the rule you read it from, '
    '"execution_evidence" a machine result or the words "none: no executable oracle", "scope" the smallest class of '
    'inputs the claim covers, "uncertainty" any reading you could not settle. If you have found nothing, say so in '
    '"claim" and leave the rest empty. Write nothing outside the JSON object.'
)

ARM_A = "A"
ARM_B = "B"
ARM_C = "C"
ARM_D = "D"
ARM_E = "E"
ARMS: tuple[str, ...] = (ARM_A, ARM_B, ARM_C, ARM_D, ARM_E)

_ARM_A_SYSTEM = (
    "You are auditing one module for defects. You are given its documented rules and its complete source. "
    "You cannot run anything: reason from the text. Find the strongest single defect you can justify — a place where "
    "the code does not do what its documentation says — and report exactly one candidate. " + _PACKET_INSTRUCTION
)

_ARM_B_SYSTEM = (
    "You are auditing one module for defects and you may run it. You are given its documented rules and its complete "
    "source. Reply with JSON only: an object carrying \"tests\", an array of at most six objects, each "
    '{"kernel": "<one of the kernel names listed>", "input": "<the exact text to run>", "expected": "<what the rule '
    'says the answer should be>"}. The harness will run each and return what the code actually answered. When you are '
    "ready to report, reply instead with the candidate object described here: " + _PACKET_INSTRUCTION
)


def _ask(executor: Any, model: str, system: str, user: str, ceiling: Ceiling, schema: dict[str, Any] | None = None) -> str:
    """One model call, charged against the shared ceiling. The key is read inside the executor."""

    from creib.forge.conformance.executor import ChatRequest

    response = executor.complete(
        ChatRequest(model=model, system=system, user=user, format_schema=schema, options={"temperature": 0, "seed": 7}, think=None)
    )
    ceiling.charge(response.prompt_eval_count or 0, response.eval_count or 0)
    if not response.usable:
        raise MiniError(
            "MINI_USETEST_CALL_FAILED",
            f"the call did not complete: {response.transport_error or response.done_reason or 'no content'}",
        )
    return response.content


def _brief(subject_path: Path, rules_only: bool) -> str:
    """What an arm is shown: the documented rules, and the code unless the arm is a rule reader."""

    source = subject_path.read_text(encoding="utf-8")
    rules = rules_text(source)
    if rules_only:
        return "## The documented rules of the checks\n\n" + rules
    return "## The documented rules of the checks\n\n" + rules + "\n\n## The source of the checks\n\n" + source


def rules_text(source: str) -> str:
    """A subject's documented rules: every definition's signature and docstring, and no code.

    This is what a rule reader is shown. It is derived from the subject itself, so a mutation
    that changes behaviour without changing a docstring leaves the rules exactly as they were,
    which is the point: the reader must not be able to see the defect in what it is given.
    """

    tree = ast.parse(source)
    parts: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "REFUSAL_PHRASES":
                    parts.append(ast.unparse(node))
        if not isinstance(node, ast.FunctionDef):
            continue
        doc = ast.get_docstring(node)
        signature = f"def {node.name}({', '.join(ast.unparse(argument) for argument in node.args.args)}):"
        body = doc if doc else "(no docstring)"
        parts.append(signature + "\n" + "\n".join(("    " + line).rstrip() for line in body.split("\n")))
    return "\n\n".join(parts)


def run_arm_a(executor: Any, model: str, subject_path: Path, ceiling: Ceiling) -> tuple[Packet | None, list[dict[str, Any]]]:
    """Arm A: rules and code, no execution, one candidate."""

    transcript: list[dict[str, Any]] = []
    reply = _ask(executor, model, _ARM_A_SYSTEM, _brief(subject_path, rules_only=False), ceiling, PACKET_SCHEMA)
    transcript.append({"phase": "report", "reply": reply})
    return packet_from(reply, "", ARM_A, model), transcript


def run_arm_b(
    executor: Any,
    model: str,
    subject_path: Path,
    ceiling: Ceiling,
    rounds: int = 4,
) -> tuple[Packet | None, list[dict[str, Any]]]:
    """Arm B: rules, code, and as many machine-run tests as the ceiling allows.

    The strongest simple baseline, and the one that matters: it may design any test it likes and
    is told exactly what the code answered. It gets no grid, no critic, no cycles and no seats.
    """

    subject = load_subject(subject_path)
    transcript: list[dict[str, Any]] = []
    conversation = _brief(subject_path, rules_only=False) + (
        "\n\n## The kernels you may run\n\n" + ", ".join(sorted(getattr(subject, "KERNELS", {})))
    )
    for _round in range(rounds):
        if ceiling.spent:
            break
        reply = _ask(executor, model, _ARM_B_SYSTEM, conversation, ceiling)
        candidate = packet_from(reply, "", ARM_B, model)
        if candidate is not None:
            transcript.append({"phase": "report", "reply": reply})
            return candidate, transcript
        try:
            asked = loads_strict(reply)
        except RecordError:
            try:
                asked = loads_strict(reply, control_characters=True)
            except RecordError:
                asked = None
        tests = asked.get("tests") if type(asked) is dict else None
        if not isinstance(tests, list) or not tests:
            transcript.append({"phase": "unreadable", "reply": reply})
            conversation += "\n\n## Your last reply could not be read as either shape. Return one of the two."
            continue
        results: list[dict[str, str]] = []
        for item in tests[:6]:
            if type(item) is not dict:
                continue
            kernel_id, text = str(item.get("kernel", "")), str(item.get("input", ""))
            if kernel_id not in getattr(subject, "KERNELS", {}):
                results.append({"kernel": kernel_id, "input": text, "answer": "NO SUCH KERNEL"})
                continue
            ceiling.machine_executions += 1
            results.append({"kernel": kernel_id, "input": text, "expected": str(item.get("expected", "")), "answer": run_kernel(subject, kernel_id, text)})
        transcript.append({"phase": "tests", "reply": reply, "results": results})
        conversation += "\n\n## What the code answered on the tests you asked for\n\n" + json.dumps(results, ensure_ascii=False, indent=2)
    if ceiling.spent:
        return None, transcript
    reply = _ask(executor, model, _ARM_A_SYSTEM.replace("You cannot run anything: reason from the text. ", ""), conversation, ceiling, PACKET_SCHEMA)
    transcript.append({"phase": "report", "reply": reply})
    return packet_from(reply, "", ARM_B, model), transcript


# --- the seats the mini arms use: the subject's rules, and execution with construction validated ---

#: Where a seat finds the subject it is testing. The path is not written into any brief: a seat
#: that could read the subject's path could read the subject, and the rule readers must not.
#: The instance record binds the subject's bytes to the run by digest.
SUBJECT_ENV = "MINI_USETEST_SUBJECT"

RULES_KIND = "mini.usetest-rules.v1"
EXECUTION_KIND = "mini.usetest-execution.v1"
PROPOSAL_PREFIX = "mini.pair-proposal."


def bound_subject() -> Path:
    """The subject this process is testing, or a refusal that names what is missing."""

    import os

    where = os.environ.get(SUBJECT_ENV, "")
    if not where.strip():
        raise MiniError("MINI_USETEST_SUBJECT_UNBOUND", f"{SUBJECT_ENV} names no subject, so nothing can be executed")
    path = Path(where)
    if not path.is_file():
        raise MiniError("MINI_USETEST_SUBJECT_UNBOUND", f"{SUBJECT_ENV} names {where!r}, which is not a file")
    return path


def _rules_seat(context: Any) -> str:
    """A machine seat whose artifact is the subject's documented rules, and none of its code."""

    import hashlib

    source = bound_subject().read_text(encoding="utf-8")
    text = rules_text(source)
    return json.dumps(
        {
            "body": text,
            "commitments": f"The documented rules of the subject under test, without its code, sha256 {hashlib.sha256(text.encode('utf-8')).hexdigest()}.",
        },
        ensure_ascii=False,
    )


def _execution_seat(context: Any) -> str:
    """Validate each pair proposal against the cell it claims, then run it against the subject.

    Three states, and only the third is coverage: a cell was assigned, a seat claimed to have
    built it, and a validator proved the text that ran satisfies it. A text that fails the
    validator is ``INVALID_INSTANTIATION``: it is not a candidate and it covers nothing.
    """

    from .blindspot import proposal_fields

    subject = load_subject(bound_subject())
    executions: list[dict[str, Any]] = []
    lines: list[str] = []
    # The cell under test is the one the machine handed out this cycle, read from the assignment
    # itself. A proposal's echo of it is recorded and never trusted: a seat that copies the
    # rendered port text instead of the cell would otherwise fail validation for the rendering's
    # fault, which is what version 2 did (USE_TEST break 5, and the audit's F-A in miniature).
    assigned = ""
    for key in context.state.artifact_order:
        record = context.state.artifacts[key]
        if str(record["kind_id"]).startswith("mini.next-cell.") and int(record.get("cycle", 0)) == context.cycle:
            from .blindspot import proposal_fields as _fields_of

            named = (_fields_of(context.commitments(record), record.get("extra")) or {}).get("cell")
            if type(named) is str and named.strip():
                assigned = " ".join(named.split())
    for key in context.state.artifact_order:
        record = context.state.artifacts[key]
        kind_id = str(record["kind_id"])
        if not kind_id.startswith(PROPOSAL_PREFIX) or int(record.get("cycle", 0)) != context.cycle:
            continue
        parsed = proposal_fields(context.commitments(record), record.get("extra")) or {}
        entry: dict[str, Any] = {
            "proposal": str(record["artifact_id"])[:16],
            "cell": assigned or " ".join(str(parsed.get("cell", "")).split()),
            "cell_echoed": str(parsed.get("cell", ""))[:200],
            "cell_assigned": assigned,
        }
        kernel_id = str(parsed.get("kernel", ""))
        source_text, rewritten = str(parsed.get("input", "")), str(parsed.get("rewritten", ""))
        expect = str(parsed.get("expect", ""))
        entry.update({"kernel": kernel_id, "input": source_text, "rewritten": rewritten, "expect": expect, "rewrite": str(parsed.get("rewrite", ""))})
        if expect not in ("moves", "unchanged"):
            entry.update({"executed": "unrunnable", "detail": "expect must be moves or unchanged"})
            executions.append(entry)
            lines.append(f"{entry['proposal']}: unrunnable")
            continue
        reason = None
        try:
            found = validate_cell(entry["cell"], source_text)
        except MiniError as error:
            found = str(error)
        if found is not None:
            reason = f"the input is not the cell it names: {found}"
        else:
            # The rewrite removes one part, so it is a different cell of the same grammar; it
            # must still be one, or what ran cannot be said.
            landed = cell_of(rewritten)
            entry["rewritten_cell"] = landed or ""
            if landed is None:
                reason = "the rewritten text is no cell of the grammar"
        if reason is not None:
            entry.update({"executed": "INVALID_INSTANTIATION", "detail": reason})
            executions.append(entry)
            lines.append(f"{entry['proposal']}: INVALID_INSTANTIATION")
            continue
        before, after = run_kernel(subject, kernel_id, source_text), run_kernel(subject, kernel_id, rewritten)
        executed = "moved" if before != after else "unchanged"
        entry.update({"before": before, "after": after, "executed": executed, "as_expected": (executed == "moved") == (expect == "moves")})
        executions.append(entry)
        lines.append(f"{entry['proposal']}: {kernel_id} {executed}, expected {expect}")
    return json.dumps(
        {
            "body": "Executed this cycle's pairs against the subject, after validating each against its cell.\n"
            + ("\n".join(lines) or "(nothing to run)"),
            "commitments": json.dumps({"executions": executions}, ensure_ascii=False, sort_keys=True),
        },
        ensure_ascii=False,
    )


def register_seats() -> None:
    """Register the two use-test seats, once."""

    from .machines import MachineSeat, register_machine_seat, resolve_machine_seat

    for kind_id, description, function in (
        (RULES_KIND, "Emits the subject's documented rules, without its code.", _rules_seat),
        (EXECUTION_KIND, "Validates each pair against its cell and runs it against the subject.", _execution_seat),
    ):
        try:
            resolve_machine_seat(kind_id)
        except Exception:
            register_machine_seat(MachineSeat(kind_id, description, function))


register_seats()


# --- the manifests the mini arms run, generated per instance from the frozen grid ---

_PROPOSER_INSTRUCTION = (
    "You are shown the documented rules of the checks under test, not their code, and ONE cell of a frozen grid under "
    "'The cell to cover'. The notation: fence[ ... ] is a code fence, a line of three backticks before and after, "
    "holding one part per line in the order given; S is one plain sentence such as 'Here is the result:'; A, B and C "
    "are small JSON objects different from each other, such as {\"a\": 1}, {\"b\": 2}, {\"c\": 3}; anything after the "
    "closing bracket comes after the closing fence line, one part per line. Build the input exactly from the cell, "
    "each part on its own line and written out in full, and nothing added: a validator will check it against the cell "
    "before anything is run, and an input that is not the cell is thrown away. The rewritten text is the same reply "
    "with exactly ONE part added or removed, and it must itself be another cell of the same grammar — a fence must "
    "still hold at least one part, so a reply whose fence holds one object is changed by adding after the fence rather "
    "than by emptying it. Write real line breaks, never the two "
    "characters backslash and n. Say what the rule, read as written, says the check's answer ought to do between the "
    "two texts: move ('moves') or stay ('unchanged'), naming in the body the words of the rule you read it from and "
    "which answer the rule gives for each text. Your kernel is one of recovery, recovered-from-prose, "
    "response-verdict. The commitments are a STRING whose content is JSON of the form "
    '{"kernel": "<id>", "expect": "moves" or "unchanged"} and nothing else; this artifact carries "input", '
    '"rewritten", "rewrite" and "cell" as fields of its own, each a plain string, and the cell exactly as it was named.'
)

_CRITIC_INSTRUCTION = (
    "Do not propose. Read this cycle's executions beside the proposals: say which expectations held, which failed, "
    "which inputs the validator threw away and why, and what a proposer should build next. Cite nothing you were not "
    "shown."
)

_LONG_FIELDS = ("input", "rewritten", "rewrite", "cell")


def _proposal_kind(kind_id: str, cell_port: str) -> dict[str, Any]:
    return {
        "kind_id": kind_id,
        "title": "Proposal",
        "optional_fields": list(_LONG_FIELDS),
        "commitment_call": "single",
        "input_ports": [
            {"port_id": "problem", "port_type": "problem", "window": "all"},
            {"port_id": "rules", "port_type": "usetest_rules", "window": "this_cycle"},
            {"port_id": "cell", "port_type": cell_port, "window": "this_cycle"},
        ],
        "output_port": {"port_id": "out", "produces_kind": kind_id},
        "instruction": _PROPOSER_INSTRUCTION,
        "format": {
            "commitments": {
                "all_of": [
                    {
                        "check": "json_schema",
                        "schema": {
                            "type": "object",
                            "required": ["kernel", "expect"],
                            "properties": {
                                "kernel": {"type": "string", "pattern": "^(recovery|recovered-from-prose|response-verdict)$"},
                                "expect": {"enum": ["moves", "unchanged"]},
                            },
                        },
                    }
                ]
            }
        },
    }


PROBLEM = (
    "The checks under test read a model's reply and say what they found in it. You are shown their documented rules "
    "and never their code. The question is whether there is a reply, and a single edit of it, on which a check's "
    "answer does something the rule as written does not allow. A machine builds nothing and reads no rule: it "
    "validates that what you built is the shape you were given, runs the check on both texts, and records what came "
    "back. Nothing here decides that anything is a defect."
)


def arm_manifest(arm: str, instance_id: str, cycles: int, max_calls: int) -> dict[str, Any]:
    """The manifest one mini arm runs on one instance: core, full, or full with attention on."""

    if arm not in (ARM_C, ARM_D, ARM_E):
        raise MiniError("MINI_USETEST_PLAN_INVALID", f"{arm!r} is not a mini arm; those are {ARM_C}, {ARM_D}, {ARM_E}")
    proposal_kind = "mini.pair-proposal.usetest.v1"
    cell_kind = "mini.next-cell.1.v1"
    port_types = [
        {"port_type": "usetest_rules", "draws_from": {"artifact_kinds": [RULES_KIND]}, "render": {"rule": "list_bodies", "header": "The documented rules of the checks"}},
        {"port_type": "cell_1", "draws_from": {"artifact_kinds": [cell_kind]}, "render": {"rule": "list_bodies", "header": "The cell to cover"}},
        {"port_type": "proposals", "draws_from": {"artifact_kinds": [proposal_kind]}, "render": {"rule": "list_bodies_and_commitments", "header": "Proposals so far"}},
        {"port_type": "executions", "draws_from": {"artifact_kinds": [EXECUTION_KIND]}, "render": {"rule": "list_bodies_and_commitments", "header": "Executions"}},
        {"port_type": "criticisms", "draws_from": {"artifact_kinds": ["mini.criticism.v1"]}, "render": {"rule": "list_bodies", "header": "Criticisms"}},
    ]
    kinds: list[dict[str, Any]] = [
        {"kind_id": RULES_KIND, "title": "Rules", "input_ports": [], "output_port": {"port_id": "out", "produces_kind": RULES_KIND}},
        {"kind_id": cell_kind, "title": "Next cell", "input_ports": [], "output_port": {"port_id": "out", "produces_kind": cell_kind}},
        _proposal_kind(proposal_kind, "cell_1"),
        {"kind_id": EXECUTION_KIND, "title": "Execution", "input_ports": [{"port_id": "proposals", "port_type": "proposals", "window": "this_cycle"}], "output_port": {"port_id": "out", "produces_kind": EXECUTION_KIND}},
        {"kind_id": "mini.verdict.v1", "title": "Verdict", "input_ports": [{"port_id": "executions", "port_type": "executions", "window": "this_cycle"}], "output_port": {"port_id": "out", "produces_kind": "mini.verdict.v1"}},
    ]
    stages: list[dict[str, Any]] = [
        {"stage_id": "rules", "kind_id": RULES_KIND, "seat": "machine", "ports": []},
        {"stage_id": "cell", "kind_id": cell_kind, "seat": "machine", "ports": []},
        {"stage_id": "propose", "kind_id": proposal_kind, "ports": ["problem", "rules", "cell"]},
        {"stage_id": "execute", "kind_id": EXECUTION_KIND, "seat": "machine", "ports": ["proposals"]},
        {"stage_id": "verdict", "kind_id": "mini.verdict.v1", "seat": "machine", "ports": ["executions"]},
        {"stage_id": "end", "end": True},
    ]
    if arm in (ARM_D, ARM_E):
        # Full mini: the proposer is fed what the run has done, and a critic reads each cycle.
        proposal = next(kind for kind in kinds if kind["kind_id"] == proposal_kind)
        proposal["input_ports"].extend(
            [
                {"port_id": "earlier", "port_type": "proposals", "window": "all"},
                {"port_id": "executions", "port_type": "executions", "window": "all"},
                {"port_id": "criticisms", "port_type": "criticisms", "window": "previous_cycle"},
            ]
        )
        next(stage for stage in stages if stage["stage_id"] == "propose")["ports"] = [
            "problem",
            "rules",
            "cell",
            "earlier",
            "executions",
            "criticisms",
        ]
        kinds.append(
            {
                "kind_id": "mini.criticism.v1",
                "title": "Criticism",
                "input_ports": [
                    {"port_id": "problem", "port_type": "problem", "window": "all"},
                    {"port_id": "rules", "port_type": "usetest_rules", "window": "this_cycle"},
                    {"port_id": "proposals", "port_type": "proposals", "window": "this_cycle"},
                    {"port_id": "executions", "port_type": "executions", "window": "this_cycle"},
                ],
                "output_port": {"port_id": "out", "produces_kind": "mini.criticism.v1"},
                "instruction": _CRITIC_INSTRUCTION,
            }
        )
        stages.insert(4, {"stage_id": "criticise", "kind_id": "mini.criticism.v1", "ports": ["problem", "rules", "proposals", "executions"]})
    manifest: dict[str, Any] = {
        "schema_version": "creib.mini.manifest.v1",
        "manifest_id": f"mini.usetest.{instance_id}.arm-{arm.lower()}",
        "problem": PROBLEM,
        "cycles": {"max_cycles": cycles, "max_calls": max_calls},
        "port_types": port_types,
        "kinds": kinds,
        "stages": stages,
        "sources": [{"source_id": "grid", "text": "\n\n".join(RECOVERY_GRID) + "\n"}],
    }
    if arm == ARM_E:
        manifest["attention"] = {"policy": "mini.attention.most-unanswered-criticisms"}
    return manifest
