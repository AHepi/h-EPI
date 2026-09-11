"""Kernels a proposer names rather than a person registers (mini register M24).

A ``Kernel`` is a registered callable, so until now the boundary points a proposer could name were
exactly the ones somebody had written a ``register_kernel`` call for: ten at runtime. The space of
boundary points is not ten wide. This module lets a proposal name a function by its dotted path and
have it run, so what may be probed is bounded by an import rule that is written down rather than by
a list somebody curated.

Three bounds, declared rather than hidden:

- **The module allowlist.** Only the reading surface of the conformance harness. ``runner`` drives
  runs, ``executor`` calls an endpoint, ``common`` creates directories; a kernel is supposed to be a
  question about a reply, not an action, and this is the crudest honest way to say so. It is a
  bound, not a proof of purity: a function inside the allowlist may still do something surprising.
- **One argument.** ``Kernel.verdict`` is ``Callable[[str], str]``. A function of a variant, a key,
  two replies or a run's history cannot be reached this way, and that exclusion is the same one
  ``conformance_kernels`` already names.
- **A raise is unreadable, never a move.** Most of these functions raise on most inputs. Scoring an
  exception as an answer would make every crash look like a boundary point, and at this width there
  would be thousands. ``unreadable`` is what M11 already says to do with a verdict the check could
  not produce, and an execution with it on either side is ``unrunnable``.
"""

from __future__ import annotations

import importlib
import inspect
from typing import Any, Callable

from .blindspot import Kernel, PAIR_EXECUTION_PREFIX, execute_pairs_with, resolve_kernel
from .common import MiniError
from .machines import MachineContext, MachineSeat, register_machine_seat

#: The one prefix a proposal writes to mean "resolve this by import, not from the registry".
OPEN_PREFIX = "open:"

#: The package every open kernel must live under.
OPEN_PACKAGE = "creib.forge.conformance."

#: The reading surface. Modules that run a pilot, call an endpoint or touch the filesystem are out.
OPEN_MODULES: tuple[str, ...] = (
    "appraisal", "claims", "compare", "controls", "corpus", "cycles", "dependence",
    "families", "oracle", "prompt", "records", "report", "routing", "spec", "units",
)

#: The verdict for a call that raised. Never equal to any answer a function returns, because no
#: ``repr`` starts with a space.
RAISED = " raised"

OPEN_MALFORMED = "MINI_OPEN_KERNEL_MALFORMED"
OPEN_MODULE_REFUSED = "MINI_OPEN_KERNEL_MODULE_REFUSED"
OPEN_NOT_FOUND = "MINI_OPEN_KERNEL_NOT_FOUND"
OPEN_NOT_CALLABLE = "MINI_OPEN_KERNEL_NOT_CALLABLE"
OPEN_ARITY = "MINI_OPEN_KERNEL_ARITY"


def is_open_kernel_id(kernel_id: str) -> bool:
    """Whether this id asks for import resolution. Anything else is the registry's business."""

    return kernel_id.startswith(OPEN_PREFIX)


def _answer(function: Callable[..., Any]) -> Callable[[str], str]:
    def verdict(text: str) -> str:
        try:
            return repr(function(text))
        except Exception:  # noqa: BLE001 - any raise is one verdict: the check could not answer
            return RAISED

    return verdict


def resolve_open_kernel(kernel_id: str) -> Kernel:
    """Build a kernel from ``open:creib.forge.conformance.<module>.<function>``.

    Every refusal below is a refusal the proposer can provoke by writing a path, so each is a
    ``MiniError`` with its own code rather than a crash inside the seat.
    """

    if not is_open_kernel_id(kernel_id):
        raise MiniError(OPEN_MALFORMED, f"an open kernel id begins {OPEN_PREFIX!r}; got {kernel_id!r}")
    path = kernel_id[len(OPEN_PREFIX):]
    if not path.startswith(OPEN_PACKAGE) or path.count(".") < OPEN_PACKAGE.count("."):
        raise MiniError(
            OPEN_MALFORMED,
            f"an open kernel path is {OPEN_PACKAGE}<module>.<function>; got {path!r}",
        )
    rest = path[len(OPEN_PACKAGE):]
    module_name, _, function_name = rest.partition(".")
    if not function_name or "." in function_name:
        raise MiniError(
            OPEN_MALFORMED,
            f"an open kernel path names one module and one function; got {rest!r}",
        )
    if module_name not in OPEN_MODULES:
        raise MiniError(
            OPEN_MODULE_REFUSED,
            f"module {module_name!r} is not on the open list; allowed: {list(OPEN_MODULES)}",
        )
    module = importlib.import_module(f"{OPEN_PACKAGE}{module_name}")
    try:
        function = getattr(module, function_name)
    except AttributeError as error:
        raise MiniError(
            OPEN_NOT_FOUND,
            f"{module_name!r} has no {function_name!r}",
        ) from error
    if not inspect.isfunction(function):
        raise MiniError(OPEN_NOT_CALLABLE, f"{rest!r} is not a function")
    # No guard on ``signature`` raising: ``isfunction`` has already excluded the builtins and C
    # callables it raises for, so a guard here would be a refusal site no test could reach, which
    # the deletion sweep would rightly name.
    signature = inspect.signature(function)
    required = [
        parameter
        for parameter in signature.parameters.values()
        if parameter.default is inspect.Parameter.empty
        and parameter.kind in (parameter.POSITIONAL_ONLY, parameter.POSITIONAL_OR_KEYWORD)
    ]
    if len(required) != 1:
        raise MiniError(
            OPEN_ARITY,
            f"{rest!r} takes {len(required)} required arguments; a kernel takes one string",
        )
    return Kernel(
        kernel_id=kernel_id,
        description=f"{rest}, resolved by import",
        verdict=_answer(function),
        unreadable=RAISED,
    )


def open_kernel_brief() -> str:
    """What a proposer is told: the rule for forming a path, and the modules. Never the functions."""

    modules = "\n".join(f"- {OPEN_PACKAGE}{name}" for name in OPEN_MODULES)
    return (
        "A kernel id may instead be written "
        f"{OPEN_PREFIX}{OPEN_PACKAGE}<module>.<function>, naming any function of one string in one "
        "of these modules of the harness under test. No list of functions is given: read the source "
        "and choose. A function that raises on a text has not answered, and a pair on which either "
        "side raised is not a move.\n\n"
        f"{modules}\n"
    )


#: The seat a manifest names to get open kernels. The registry seat, ``mini.pair-execution.v1``, is
#: untouched, so every manifest written before this module is byte-for-byte unaffected and an open
#: answer space is something a run asks for rather than something it inherits.
PAIR_EXECUTION_OPEN_KIND = f"{PAIR_EXECUTION_PREFIX}open.v1"


#: Configuration a two-argument check takes in this codebase. A kernel is a function of one string,
#: so a check whose second argument is a fixed table is unreachable without this: CREATIVITY-ARMS-1
#: found the loop starved because every conjecture about such a check came back unrunnable, and a
#: criticism stage fed refusals is criticising the machinery rather than the subject.
SECOND_ARGUMENT: dict[str, str] = {
    "refusal_phrase_in": "creib.forge.mini.conformance_kernels.REFUSAL_PHRASES",
}


def _with_second_argument(function: Any, name: str) -> Callable[[str], str] | None:
    """A one-string view of a two-argument check, when its second argument is declared above."""

    target = SECOND_ARGUMENT.get(name)
    if target is None:
        return None
    holder, _, attribute = target.rpartition(".")
    value = getattr(importlib.import_module(holder), attribute)
    return lambda text: function(text, value)


def _candidate(path: str) -> Kernel | None:
    """One resolution attempt: the path as given, then with its declared second argument bound."""

    try:
        return resolve_open_kernel(path)
    except MiniError as error:
        if error.code != OPEN_ARITY:
            return None
    inner = path[len(OPEN_PREFIX):]
    module_name, _, function_name = inner.rpartition(".")
    function = getattr(importlib.import_module(module_name), function_name, None)
    bound = _with_second_argument(function, function_name) if function is not None else None
    if bound is None:
        return None
    return Kernel(kernel_id=path, description=f"{inner}, second argument declared",
                  verdict=_answer_of(bound), unreadable=RAISED)


def relocate(kernel_id: str) -> str | None:
    """The same function name under another open module, when its stated module does not hold it.

    A conjecture that names the right function in the wrong file is misfiled, not false, and
    refusing it teaches a criticism stage nothing about the subject. A candidate that needs its
    second argument bound counts as found: the two widenings have to compose, and the first version
    of this function rejected exactly the case both were written for.
    """

    if not is_open_kernel_id(kernel_id):
        return None
    name = kernel_id.rpartition(".")[2]
    for module_name in OPEN_MODULES:
        candidate = f"{OPEN_PREFIX}{OPEN_PACKAGE}{module_name}.{name}"
        if candidate != kernel_id and _candidate(candidate) is not None:
            return candidate
    return None


def resolve_any_kernel(kernel_id: str) -> Kernel:
    """The registry first, then import, then a declared second argument, then another module.

    The widenings after the first are ones CREATIVITY-ARMS-1 measured the need for: they turn a
    claim the executor would have refused into a result the loop can read. Applied to every arm
    equally, and an unknown name is still refused.
    """

    if not is_open_kernel_id(kernel_id):
        return resolve_kernel(kernel_id)
    direct = _candidate(kernel_id)
    if direct is not None:
        return direct
    elsewhere = relocate(kernel_id)
    if elsewhere is not None:
        moved = _candidate(elsewhere)
        if moved is not None:
            return moved
    return resolve_open_kernel(kernel_id)


def _answer_of(call: Callable[[str], Any]) -> Callable[[str], str]:
    def verdict(text: str) -> str:
        try:
            return repr(call(text))
        except Exception:  # noqa: BLE001 - any raise is one verdict: the check could not answer
            return RAISED

    return verdict


def _execute_pairs_open(context: MachineContext) -> str:
    return execute_pairs_with(context, resolve_any_kernel, PAIR_EXECUTION_OPEN_KIND)


PAIR_EXECUTION_OPEN_SEAT = register_machine_seat(
    MachineSeat(
        PAIR_EXECUTION_OPEN_KIND,
        "Runs pair proposals whose kernel may be any function of one string named by import path.",
        _execute_pairs_open,
    )
)
