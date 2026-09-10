"""The conformance harness's own checks as mini kernels, and rewrites of a reply as transforms.

The blind-spot template asks a proposer for a kernel, a transform and an input,
runs the kernel before and after the transform by machine, and sets the result
against a catalogue of pairs already written down. This module points that loop
at the checks under ``src/creib/forge/conformance/`` rather than at mini's own:
every kernel here is one of the harness's functions read over one reply text,
and every transform is a rewrite of a reply of the kind the kernel table in
``docs/kernel.md`` describes (P-01 to P-08, R-01, R-02). Nothing in the
conformance package is changed or wrapped; the functions are called as they are.

A kernel is a function of one string, so only the checks that read a reply on
its own are here: JSON recovery, the parse verdict, whether recovery happened
from prose, and the refusal phrase. The grounding matcher reads a value beside a
span and is not a function of one string; it is not represented.

Importing this module registers the kernels and transforms. The registry is
listed, one entry per paragraph, in ``forge/mini/manifests/conformance-blind-spot/registry.txt``,
and a test refuses drift between that file and this module.
"""

from __future__ import annotations

import re

import hashlib
import inspect
import json

from creib.canonical import canonical_bytes
from creib.errors import RecordError
from creib.forge.conformance import oracle
from creib.forge.conformance.oracle import _normalise_whitespace, _span_occurs, parse_content, recover_json_object, refusal_phrase_in
from creib.strict_json import loads_strict

from .blindspot import Kernel, Transform, register_kernel, register_transform
from .machines import MachineContext, MachineSeat, register_machine_seat

#: The refusal phrases the kernels read with: the travel-claim pilot's list, fixed here so
#: that a kernel is a function of the text alone.
REFUSAL_PHRASES: tuple[str, ...] = ("I cannot", "I can't", "I'm sorry", "I am unable", "as an AI", "cannot assist")

KERNEL_RECOVERY = "conformance.kernel.recovery"
KERNEL_RECOVERED_FROM_PROSE = "conformance.kernel.recovered-from-prose"
KERNEL_RESPONSE_VERDICT = "conformance.kernel.response-verdict"
KERNEL_REFUSAL_PHRASE = "conformance.kernel.refusal-phrase"

NO_OBJECT = "NO_OBJECT"
NO_PHRASE = "NONE"


def _recovery(text: str) -> str:
    try:
        value, _duplicates = recover_json_object(text)
    except RecordError:
        return NO_OBJECT
    return canonical_bytes(value).decode("utf-8")


def _recovered_from_prose(text: str) -> str:
    return "yes" if parse_content(text, REFUSAL_PHRASES)[3] else "no"


def _response_verdict(text: str) -> str:
    return parse_content(text, REFUSAL_PHRASES)[1]


def _refusal_phrase(text: str) -> str:
    return refusal_phrase_in(text, REFUSAL_PHRASES) or NO_PHRASE


KERNEL_SPAN_OCCURS = "conformance.kernel.span-occurs"
KERNEL_GROUNDING = "conformance.kernel.grounding"
UNREADABLE = "UNREADABLE_INPUT"


def _fields(text: str, *names: str) -> dict[str, str] | None:
    """A grounding kernel's input is one JSON object carrying the named string fields."""

    try:
        parsed = loads_strict(text)
    except RecordError:
        return None
    if type(parsed) is not dict or any(type(parsed.get(name)) is not str for name in names):
        return None
    return {name: str(parsed[name]) for name in names}


def _span_occurs_kernel(text: str) -> str:
    fields = _fields(text, "span", "document")
    if fields is None:
        return UNREADABLE
    matched = _span_occurs(fields["span"], fields["document"], ())
    return "NOT_IN_DOCUMENT" if matched is None else matched


def _grounding_kernel(text: str) -> str:
    """The grounding verdict as the harness gives it, with no relaxation and the value-in-span check on.

    The three lines are the harness's own (``_grounding_verdict`` in ``oracle.py``), read here
    over one JSON object rather than over a variant and its output.
    """

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


KERNELS: tuple[Kernel, ...] = (
    Kernel(KERNEL_RECOVERY, "The object the harness recovers from the reply, as canonical JSON, or NO_OBJECT.", _recovery),
    Kernel(KERNEL_RECOVERED_FROM_PROSE, "Whether the harness had to recover the object from prose or a fence (yes) or read it as strict JSON (no).", _recovered_from_prose),
    Kernel(KERNEL_RESPONSE_VERDICT, "The harness's response verdict for the reply: JSON_OBJECT, INVALID_JSON, REFUSAL_SUSPECTED, or another of its verdicts.", _response_verdict),
    Kernel(KERNEL_REFUSAL_PHRASE, "The first listed refusal phrase the reply contains, typographic apostrophes read as straight, or NONE.", _refusal_phrase),
    Kernel(KERNEL_SPAN_OCCURS, "Whether a cited span occurs in a document, whitespace-normalised, no relaxation: the input is one JSON object {\"span\", \"document\"}; verbatim or NOT_IN_DOCUMENT.", _span_occurs_kernel),
    Kernel(KERNEL_GROUNDING, "The harness's grounding verdict for a value, its cited span and the document, no relaxation, value-in-span checked: the input is one JSON object {\"value\", \"span\", \"document\"}; GROUNDED, SPAN_MISSING, SPAN_NOT_IN_DOCUMENT or VALUE_NOT_IN_SPAN.", _grounding_kernel),
)

#: The harness functions the kernels call, whose source a proposer may be shown whole.
SOURCE_FUNCTIONS = tuple(
    function
    for function in (
        getattr(oracle, name, None)
        for name in ("recover_json_object", "_top_level_objects", "_loads_last_wins", "parse_content", "refusal_phrase_in", "_plain_quotes", "_normalise_whitespace", "_span_occurs")
    )
    if function is not None
) + (_grounding_kernel,)
KERNEL_SOURCE_KIND = "mini.kernel-source.v1"


def kernel_source_text() -> str:
    """The source of the harness functions behind the kernels, as a seat is shown it."""

    parts = [f"_FENCE = re.compile({oracle._FENCE.pattern!r}, re.DOTALL)", f"REFUSAL_PHRASES = {list(REFUSAL_PHRASES)!r}"]
    parts.extend(inspect.getsource(function).rstrip() for function in SOURCE_FUNCTIONS)
    return "\n\n".join(parts) + "\n"


def _kernel_source(context: MachineContext) -> str:
    """A machine seat whose artifact is the source itself, so a proposer reads the check it attacks.

    Evidence reaches a seat as a legend of excerpts; an artifact reaches it whole. The body is
    the source and the commitments name its digest, so the record says which code was shown.
    """

    text = kernel_source_text()
    return json.dumps(
        {"body": text, "commitments": f"The source of the harness functions behind the kernels, sha256 {hashlib.sha256(text.encode('utf-8')).hexdigest()}."},
        ensure_ascii=False,
    )


KERNEL_SOURCE_SEAT = register_machine_seat(MachineSeat(KERNEL_SOURCE_KIND, "Emits the kernels' source code as an artifact.", _kernel_source))

_WHITESPACE = re.compile(r"\s+")


def _fence(text: str) -> str:
    return f"```json\n{text}\n```"


def _fence_with_prose(text: str) -> str:
    return f"```json\nthe form:\n{text}\n```"


def _fence_then_bare_after(text: str) -> str:
    return f"```json\n{text}\n``` then {{\"later\": 1}}"


def _prose_before(text: str) -> str:
    return "Here is the form:\n" + text


def _prose_after(text: str) -> str:
    return text + "\nThat is the completed form."


def _refusal_prose_before(text: str) -> str:
    return "I cannot stress how clear this document is:\n" + text


def _draft_before(text: str) -> str:
    return '{"draft": 1} then ' + text


def _bare_after(text: str) -> str:
    return text + ' then {"later": 1}'


def _float_after(text: str) -> str:
    return text + ' final {"a": 1.5}'


def _upper_case(text: str) -> str:
    return text.upper()


def _typographic_quotes(text: str) -> str:
    return text.replace("'", "’")


def _indent(text: str) -> str:
    return "\n\n  " + text.replace("\n", "\n  ") + "\n"


def _fold_whitespace(text: str) -> str:
    return _WHITESPACE.sub(" ", text).strip()


TRANSFORMS: tuple[Transform, ...] = (
    Transform("conformance.transform.fence", "Wrap the whole reply in a ```json code fence.", _fence),
    Transform("conformance.transform.fence-with-prose", "Wrap the reply in a ```json fence that also holds a sentence before it.", _fence_with_prose),
    Transform("conformance.transform.fence-then-bare-after", "Wrap the reply in a fence and add a bare object {\"later\": 1} after the fence.", _fence_then_bare_after),
    Transform("conformance.transform.prose-before", "Put the sentence 'Here is the form:' on a line before the reply.", _prose_before),
    Transform("conformance.transform.prose-after", "Put the sentence 'That is the completed form.' on a line after the reply.", _prose_after),
    Transform("conformance.transform.refusal-prose-before", "Put the sentence 'I cannot stress how clear this document is:' before the reply; it holds a listed refusal phrase.", _refusal_prose_before),
    Transform("conformance.transform.draft-before", "Put a bare object {\"draft\": 1} and the word 'then' before the reply.", _draft_before),
    Transform("conformance.transform.bare-after", "Put the word 'then' and a bare object {\"later\": 1} after the reply.", _bare_after),
    Transform("conformance.transform.float-after", "Put the word 'final' and an object holding a float, {\"a\": 1.5}, after the reply.", _float_after),
    Transform("conformance.transform.upper-case", "Put the whole reply in capitals.", _upper_case),
    Transform("conformance.transform.typographic-quotes", "Replace every straight apostrophe with a typographic one.", _typographic_quotes),
    Transform("conformance.transform.indent", "Add blank lines before the reply and two spaces of indentation to every line.", _indent),
    Transform("conformance.transform.fold-whitespace", "Collapse every run of whitespace to one space and strip the ends.", _fold_whitespace),
)

for _kernel in KERNELS:
    register_kernel(_kernel)
for _transform in TRANSFORMS:
    register_transform(_transform)


def registry_text() -> str:
    """The conformance registry as a proposer is shown it: one kernel or transform per paragraph."""

    from .blindspot import registry_text as _registry_text

    return _registry_text("conformance.")


__all__ = [
    "KERNELS",
    "KERNEL_GROUNDING",
    "KERNEL_SOURCE_KIND",
    "KERNEL_SPAN_OCCURS",
    "kernel_source_text",
    "KERNEL_RECOVERED_FROM_PROSE",
    "KERNEL_RECOVERY",
    "KERNEL_REFUSAL_PHRASE",
    "KERNEL_RESPONSE_VERDICT",
    "NO_OBJECT",
    "NO_PHRASE",
    "REFUSAL_PHRASES",
    "TRANSFORMS",
    "registry_text",
]
