"""How far back a port looks (R23).

A port declaration may carry a window, and what it draws is filtered by the
cycle coordinate the record already carries. The default is ``all``, so a
manifest that says nothing behaves as it did before cycles existed.

Supplied sources are batched before the first cycle and carry cycle 0, so
``this_cycle`` on an evidence port draws only what the run itself generated.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .common import MiniError, object_value

WINDOW_ALL = "all"
WINDOW_THIS_CYCLE = "this_cycle"
WINDOW_PREVIOUS_CYCLE = "previous_cycle"
WINDOW_NAMES: tuple[str, ...] = (WINDOW_ALL, WINDOW_THIS_CYCLE, WINDOW_PREVIOUS_CYCLE)
_INVALID = "MINI_WINDOW_INVALID"


@dataclass(frozen=True)
class Window:
    """One port's reach back through the cycles."""

    name: str
    last_n: int | None = None

    def admits(self, produced_in: int, current_cycle: int) -> bool:
        if self.name == WINDOW_ALL:
            return True
        if self.name == WINDOW_THIS_CYCLE:
            return produced_in == current_cycle
        if self.name == WINDOW_PREVIOUS_CYCLE:
            return produced_in == current_cycle - 1
        return produced_in > current_cycle - int(self.last_n or 0)

    def to_dict(self) -> dict[str, object]:
        return {"window": self.name} if self.last_n is None else {"window": self.name, "last_n": self.last_n}


ALL = Window(WINDOW_ALL)


def window_from_dict(raw: Any, where: str) -> Window:
    """Read one port's window. Absent is ``all``."""

    if raw is None:
        return ALL
    if type(raw) is str:
        if raw not in WINDOW_NAMES:
            raise MiniError(_INVALID, f"{where} must be one of {list(WINDOW_NAMES)} or a last_n object, got {raw!r}")
        return Window(raw)
    entry = object_value(raw, where, _INVALID)
    if set(entry) != {"last_n"}:
        raise MiniError(_INVALID, f"{where} as an object must carry only last_n")
    value = entry["last_n"]
    if type(value) is not int or value < 1:
        raise MiniError(_INVALID, f"{where}.last_n must be a whole number of cycles, at least 1")
    return Window("last_n", value)
