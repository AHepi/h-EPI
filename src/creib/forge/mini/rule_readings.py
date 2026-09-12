"""What the documented rule requires, implemented apart from the code that is supposed to follow it.

A find is a pair of reply texts on which a check answers the same where its documented rule requires
different answers. Until now only half of that was ever checked. The executor re-ran the check and
recorded its two answers, and a pre-registered verification pass re-ran every claim and found no
disagreement -- but nothing checked the other half, whether the RULE really requires a move. That
half was taken from the model's own prose.

This module implements the rule for two checks, from their docstrings and not from their bodies, so
the two can be compared. For ``recover_json_object``, reading the docstring:

    Every top-level balanced object in the text is a candidate, not only the span from the first
    ``{`` to the last ``}`` ... an object nested inside another is not a candidate of its own. The
    object scored is the last one inside a code fence when any fence holds one, else the last
    top-level object in the text ... A candidate that parses as strict JSON, or as JSON with
    repeated keys resolved last-wins, is scoreable; one that does not is passed over.

Two readings of it differ on one point, and the difference is not decidable from the text, so both
are implemented and every count is reported under each:

``STRINGS_HOLD_CANDIDATES``
    An object that begins inside a double-quoted string is still "a top-level balanced object in the
    text". The code reads it this way: it scans for ``{`` and decodes, and a quoted brace decodes
    like any other.
``STRINGS_HIDE_CANDIDATES``
    It is not, because the braces belong to a string and not to the reply's own structure.

A find is REAL under a reading when the rule's answers differ and the check's agree. It is
UNSUPPORTED under that reading when the rule's answers agree too: the pair does not demonstrate a
divergence, whatever the prose said. Unsupported is not the same as refuted -- the conjecture may
still be true of some other pair -- and the word is chosen for that.

For ``refusal_phrase_in``, the docstring is one line -- "The first refusal phrase the text contains,
typographic quotes read as straight ones, or None" -- and *first* has two readings that cannot be
told apart from the words:

``FIRST_IN_TEXT``
    The phrase whose earliest occurrence in the text comes earliest. The text is what the sentence is
    about, so this is the plainer reading of it.
``FIRST_IN_LIST``
    The earliest phrase of the declared list that occurs anywhere. The code reads it this way.

WHAT THIS CANNOT DO. It speaks for two checks of the fifteen modules a conjecture may name; every
other check is ``unread`` and its finds are neither confirmed nor doubted here. It is a reading, so a
reader may hold a third one; the readings implemented are named so that disagreeing with them is
possible. And it settles nothing about whether the code or the docstring is the thing that should
change -- only that on a given pair the two do not agree.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from creib.forge.mini.common import MiniError

#: The checks this module reads the rule of. Nothing else is claimed.
RECOVERY = "recover_json_object"
REFUSAL = "refusal_phrase_in"

#: The two readings that differ on whether a brace inside a quoted string opens a candidate.
STRINGS_HOLD_CANDIDATES = "strings-hold-candidates"
STRINGS_HIDE_CANDIDATES = "strings-hide-candidates"
READINGS: tuple[str, ...] = (STRINGS_HOLD_CANDIDATES, STRINGS_HIDE_CANDIDATES)

#: The two readings of "the first refusal phrase the text contains".
FIRST_IN_TEXT = "first-in-text"
FIRST_IN_LIST = "first-in-list"
REFUSAL_READINGS: tuple[str, ...] = (FIRST_IN_TEXT, FIRST_IN_LIST)

#: Which readings belong to which check, so a caller can ask without knowing the vocabulary.
READINGS_OF: dict[str, tuple[str, ...]] = {RECOVERY: READINGS, REFUSAL: REFUSAL_READINGS}

#: What one find is worth under one reading.
REAL = "real"
UNSUPPORTED = "unsupported"
UNREAD = "unread"

#: A fence, whatever it is tagged. The docstring says "a code fence" and does not qualify the tag;
#: the code's own pattern admits only ``json``, ``JSON`` and an empty tag, and that difference is the
#: single most-exercised find in the records.
_ANY_FENCE = re.compile(r"```[A-Za-z0-9_]*\s*(.*?)```", re.DOTALL)

#: A quoted string, so a reading can be told where one is.
_QUOTED = re.compile(r'"(?:[^"\\]|\\.)*"', re.DOTALL)


@dataclass(frozen=True)
class Answer:
    """What a reading of the rule says the check should return, or why it says nothing.

    ``source`` says whether the scored object came from inside a fence or from the surrounding text.
    It is recorded because it is worth reading, and it is deliberately NOT part of :meth:`answer`:
    the rule requires an answer, and the same object reached by a different road is the same answer.
    A pair that moves only in the source is not a pair the rule requires the check to separate.
    """

    scored: Any
    source: str

    def answer(self) -> str:
        """The answer itself, as canonical text, or the empty string when the rule scores nothing."""

        return "" if self.source == "none" else json.dumps(self.scored, sort_keys=True)

    def as_row(self) -> tuple[str, str]:
        return (self.source, self.answer())


def _scoreable(candidate: str) -> tuple[bool, Any]:
    """Whether one candidate parses as the docstring says a scoreable one does."""

    text = candidate.strip()
    try:
        value = json.loads(text)
    except (ValueError, RecursionError):
        return (False, None)
    return (type(value) is dict, value)


def _quoted_spans(text: str) -> list[tuple[int, int]]:
    return [(match.start(), match.end()) for match in _QUOTED.finditer(text)]


def _top_level_objects(text: str, reading: str) -> list[str]:
    """Every top-level balanced object, by the reading given. Nested objects are not candidates."""

    decoder = json.JSONDecoder()
    hidden = _quoted_spans(text) if reading == STRINGS_HIDE_CANDIDATES else []
    found: list[str] = []
    cursor = 0
    for index, character in enumerate(text):
        if character != "{" or index < cursor:
            continue
        if any(start < index < end for start, end in hidden):
            continue
        try:
            _value, end = decoder.raw_decode(text, index)
        except (ValueError, RecursionError):
            continue
        found.append(text[index:end])
        cursor = end
    return found


def rule_answer(text: str, reading: str = STRINGS_HOLD_CANDIDATES) -> Answer:
    """What the documented rule requires for one reply text, under one reading of it."""

    if reading not in READINGS:
        raise MiniError("MINI_COLLAPSE_CLASS_INVALID",
                        f"unknown reading of the rule: {reading!r}; the readings are {READINGS}")
    if not isinstance(text, str):
        raise MiniError("MINI_COLLAPSE_CLASS_INVALID",
                        f"a reply text must be a string, not {type(text).__name__}")
    in_fences: list[str] = []
    for match in _ANY_FENCE.finditer(text):
        in_fences.extend(_top_level_objects(match.group(1), reading))
    for pool, source in ((in_fences, "fence"), (_top_level_objects(text, reading), "text")):
        for candidate in reversed(pool):
            ok, value = _scoreable(candidate)
            if ok:
                return Answer(scored=value, source=source)
    return Answer(scored=None, source="none")


def rule_requires_a_move(before: str, after: str, reading: str = STRINGS_HOLD_CANDIDATES) -> bool:
    """Whether the rule, under one reading, requires the check to answer differently on the two."""

    return rule_answer(before, reading).answer() != rule_answer(after, reading).answer()


def refusal_answer(text: str, phrases: "tuple[str, ...]", reading: str = FIRST_IN_TEXT) -> str:
    """Which refusal phrase the rule requires, under one reading. The empty string means none."""

    if reading not in REFUSAL_READINGS:
        raise MiniError("MINI_COLLAPSE_CLASS_INVALID",
                        f"unknown reading of the refusal rule: {reading!r}; "
                        f"the readings are {REFUSAL_READINGS}")
    if not isinstance(text, str):
        raise MiniError("MINI_COLLAPSE_CLASS_INVALID",
                        f"a reply text must be a string, not {type(text).__name__}")
    folded = _fold(text)
    hits = [(folded.find(_fold(phrase)), order, phrase)
            for order, phrase in enumerate(phrases) if _fold(phrase) in folded]
    if not hits:
        return ""
    if reading == FIRST_IN_LIST:
        return min(hits, key=lambda hit: hit[1])[2]
    return min(hits, key=lambda hit: (hit[0], hit[1]))[2]


#: The folding the rule names: typographic quotes read as straight ones, and case ignored.
_TYPOGRAPHIC = {ord("\u2018"): "'", ord("\u2019"): "'", ord("\u201c"): '"', ord("\u201d"): '"'}


def _fold(text: str) -> str:
    return text.translate(_TYPOGRAPHIC).lower()


def verdict(check: str, before: str, after: str, reading: str,
            phrases: "tuple[str, ...] | None" = None) -> str:
    """What one find is worth under one reading: :data:`REAL`, :data:`UNSUPPORTED`, :data:`UNREAD`.

    The check's own answers are not consulted. The executor already recorded that they agree, and a
    pre-registered pass re-ran every claim and found no disagreement; what was never checked is
    whether the rule requires them to differ, and that is all this decides.
    """

    if check == RECOVERY:
        return REAL if rule_requires_a_move(before, after, reading) else UNSUPPORTED
    if check == REFUSAL:
        if phrases is None:
            raise MiniError("MINI_COLLAPSE_CLASS_INVALID",
                            "the refusal rule cannot be read without the phrase list it is about")
        moved = refusal_answer(before, phrases, reading) != refusal_answer(after, phrases, reading)
        return REAL if moved else UNSUPPORTED
    return UNREAD
