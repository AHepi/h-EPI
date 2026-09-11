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


def resolve_any_kernel(kernel_id: str) -> Kernel:
    """The registry first, then import. A registered id never changes meaning because of this file."""

    if is_open_kernel_id(kernel_id):
        return resolve_open_kernel(kernel_id)
    return resolve_kernel(kernel_id)


def _execute_pairs_open(context: MachineContext) -> str:
    return execute_pairs_with(context, resolve_any_kernel, PAIR_EXECUTION_OPEN_KIND)


PAIR_EXECUTION_OPEN_SEAT = register_machine_seat(
    MachineSeat(
        PAIR_EXECUTION_OPEN_KIND,
        "Runs pair proposals whose kernel may be any function of one string named by import path.",
        _execute_pairs_open,
    )
)
