"""A reading of the finds: which shape difference through a check each one exercises.

The block-2 arms were compared on how many finds each produced. A find is a pair of reply texts
the check answers the same on where the documented rule requires it to answer differently. Counted
that way the block produced 164 finds, and nothing in that number says whether they are 164 facts
about the code or one fact restated 164 times.

This module partitions the finds. Each side of a pair is described by the shape distinctions the
checks under test actually make -- whether the text opens a fenced block, whether the fence carries
a tag the check's own pattern matches, how many brace groups sit inside the fence and how many
outside, whether a brace group sits inside a quoted string -- and a *collapse class* is the check
together with the two descriptions. Two finds in the same class differ in the same way; a count of
classes is a count of distinct ways the check was made to collapse, not of distinct texts.

The word route is not used for this: ``routing.py`` already means by it which stage runs next.

This reading was written after the records existed. It is a description of them, not a conjecture
they were run to test, and the document that reports it says so.

WHAT THE READING CANNOT SEE. Two texts with the same description can still take different paths
through the function: the description does not say which brace group parses as JSON, only how many
there are. Two texts with different descriptions can take the same path: the counts are capped, so
four brace groups and five are described alike. A class count is therefore neither an upper nor a
lower bound on the number of distinct paths through the check. It is the number of cells in a
partition by a stated shape, and the shape is stated here so a reader can disagree with it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from creib.forge.mini.common import MiniError

#: The tags the conformance oracle's own fence pattern matches, spelled as that pattern spells them.
#: The pattern is ``(?:json|JSON)?``, so it admits an empty tag, ``json``, and ``JSON``, and nothing
#: else -- ``Json`` included. A fence carrying anything else is not seen by that pattern as a fence at
#: all, which is the single most-exercised route in block 2. Comparing case-insensitively here would
#: make the reading blind to the very distinction that produced the finds, so the comparison is exact.
MATCHED_FENCE_TAGS: frozenset[str] = frozenset({"", "json", "JSON"})

#: Brace groups are counted up to this many and no further. Four and five are described alike, and
#: the module docstring says what that costs.
BRACE_CAP = 3

_FENCE_TAG = re.compile(r"```([A-Za-z0-9_]*)")
_FENCED_REGION = re.compile(r"```[A-Za-z0-9_]*\s*(.*?)```", re.DOTALL)
_BRACE_GROUP = re.compile(r"\{[^{}]*\}")
_QUOTED_BRACE = re.compile(r'"\s*\{')

#: The executor's words for a claim it ran. Anything else is a claim it could not run, and an
#: unrunnable claim has no pair to describe.
RAN = frozenset({"moved", "unchanged"})


@dataclass(frozen=True)
class Shape:
    """How one reply text looks to the distinctions the checks under test make."""

    fence: str
    braced_inside: int
    braced_outside: int
    braced_in_quotes: bool

    def as_row(self) -> tuple[str, int, int, bool]:
        return (self.fence, self.braced_inside, self.braced_outside, self.braced_in_quotes)


@dataclass(frozen=True)
class CollapseClass:
    """A check together with the shapes of the two texts that made it answer the same."""

    kernel: str
    before: Shape
    after: Shape

    def as_row(self) -> tuple[str, tuple[str, int, int, bool], tuple[str, int, int, bool]]:
        return (self.kernel, self.before.as_row(), self.after.as_row())

    @property
    def check(self) -> str:
        """The bare function name, with the open prefix and the module path dropped."""

        return self.kernel.rsplit(".", 1)[-1]


def shape_of(text: str) -> Shape:
    """Describe one reply text. A text that is not a string is an input failure, not a shape."""

    if not isinstance(text, str):
        raise MiniError("MINI_COLLAPSE_CLASS_INVALID",
                        f"a reply text must be a string to be described, not {type(text).__name__}")
    tags = _FENCE_TAG.findall(text)
    if not tags:
        fence = "absent"
    elif all(tag in MATCHED_FENCE_TAGS for tag in tags):
        fence = "json_or_bare"
    else:
        fence = "other_tag"
    region = _FENCED_REGION.search(text)
    inside = len(_BRACE_GROUP.findall(region.group(1))) if region else 0
    outside = len(_BRACE_GROUP.findall(_FENCED_REGION.sub("", text)))
    return Shape(fence=fence, braced_inside=min(inside, BRACE_CAP),
                 braced_outside=min(outside, BRACE_CAP),
                 braced_in_quotes=_QUOTED_BRACE.search(text) is not None)


def is_find(row: Mapping[str, Any]) -> bool:
    """Whether one executor row is a find: the rule required a move and the check did not move."""

    return str(row.get("expect")) == "moves" and row.get("executed") == "unchanged"


def ran(row: Mapping[str, Any]) -> bool:
    """Whether the executor ran the claim at all."""

    return str(row.get("executed")) in RAN


def class_of(row: Mapping[str, Any]) -> CollapseClass:
    """The class one find falls in. A row that is not a find has no class and is refused."""

    if not is_find(row):
        raise MiniError("MINI_COLLAPSE_CLASS_INVALID", "only a find has a collapse class: this row is "
                        f"expect={row.get('expect')!r} executed={row.get('executed')!r}")
    kernel = row.get("kernel")
    if not isinstance(kernel, str) or not kernel:
        raise MiniError("MINI_COLLAPSE_CLASS_INVALID", "a find must name the check it is about")
    return CollapseClass(kernel=kernel, before=shape_of(str(row.get("input"))),
                 after=shape_of(str(row.get("rewritten"))))


def classes_of(rows: Iterable[Mapping[str, Any]]) -> list[CollapseClass]:
    """Every find's class, in the order the finds were recorded. Non-finds are passed over."""

    return [class_of(row) for row in rows if is_find(row)]
