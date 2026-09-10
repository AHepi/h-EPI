"""The blind-spot template: hunting places a check does not see (R26).

The question it asks is this prototype's own: for each of its checks, is there a
rewrite of the input under which the check's verdict ought to move and does not,
or moves where nobody had written it down?

Three registries and one committed document:

- a KERNEL is a deterministic verdict of this prototype's own machinery over one
  piece of text;
- a TRANSFORM is a deterministic rewrite of one piece of text;
- the CATALOGUE lists the kernel and transform pairs already known, and whether
  each is known to move. It is supplied as an ordinary run source, so it is cut
  into blocks and a critic can cite it like any other evidence.

A proposal names a kernel, a transform and an input. The machine EXECUTOR runs
the kernel before and after the transform and records whether the verdict moved.
The machine VERDICT sets each execution against the catalogue and commits a
standing. Nothing in the loop promotes anything: a verdict is an artifact, it
mints no standing anywhere else, and a person turns the last one into boundary
points or does not.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Callable, Mapping

from creib.errors import RecordError
from creib.strict_json import loads_strict

from .common import MiniError
from .evidence import cut_source, folded
from .machines import MachineContext, MachineSeat, register_machine_seat

PROPOSAL_KIND = "mini.proposal.v1"
EXECUTION_KIND = "mini.execution.v1"
CRITICISM_KIND = "mini.criticism.v1"
VERDICT_KIND = "mini.verdict.v1"
CATALOGUE_SOURCE = "catalogue"

STANDING_CANDIDATE = "candidate point"
STANDING_DEFECT = "defect"
STANDING_REJECTED = "rejected"
STANDINGS: tuple[str, ...] = (STANDING_CANDIDATE, STANDING_DEFECT, STANDING_REJECTED)


@dataclass(frozen=True)
class Kernel:
    kernel_id: str
    description: str
    verdict: Callable[[str], str]


@dataclass(frozen=True)
class Transform:
    transform_id: str
    description: str
    rewrite: Callable[[str], str]


_KERNELS: dict[str, Kernel] = {}
_TRANSFORMS: dict[str, Transform] = {}


def register_kernel(kernel: Kernel) -> Kernel:
    if kernel.kernel_id in _KERNELS:
        raise MiniError("MINI_KERNEL_DUPLICATE", f"kernel {kernel.kernel_id!r} is already registered")
    _KERNELS[kernel.kernel_id] = kernel
    return kernel


def register_transform(transform: Transform) -> Transform:
    if transform.transform_id in _TRANSFORMS:
        raise MiniError("MINI_TRANSFORM_DUPLICATE", f"transform {transform.transform_id!r} is already registered")
    _TRANSFORMS[transform.transform_id] = transform
    return transform


def resolve_kernel(kernel_id: str) -> Kernel:
    try:
        return _KERNELS[kernel_id]
    except KeyError as error:
        raise MiniError("MINI_KERNEL_UNKNOWN", f"no kernel {kernel_id!r}; known: {sorted(_KERNELS)}") from error


def resolve_transform(transform_id: str) -> Transform:
    try:
        return _TRANSFORMS[transform_id]
    except KeyError as error:
        raise MiniError("MINI_TRANSFORM_UNKNOWN", f"no transform {transform_id!r}; known: {sorted(_TRANSFORMS)}") from error


def registered_kernels() -> tuple[Kernel, ...]:
    return tuple(_KERNELS[name] for name in sorted(_KERNELS))


def registered_transforms() -> tuple[Transform, ...]:
    return tuple(_TRANSFORMS[name] for name in sorted(_TRANSFORMS))


# --- the kernels: this prototype's own checks, each as a verdict over one text ---


def _cut_count(text: str) -> str:
    return str(len(cut_source("probe", text.encode("utf-8"), "evidence")))


def _folded_text(text: str) -> str:
    return folded(text)


def _json_readable(text: str) -> str:
    try:
        loads_strict(text)
    except RecordError:
        return "no"
    return "yes"


def _carries_because(text: str) -> str:
    return "yes" if "BECAUSE" in text else "no"


register_kernel(Kernel("mini.kernel.cut-count", "How many blocks the cutter makes of this text.", _cut_count))
register_kernel(Kernel("mini.kernel.folded", "The text with its whitespace folded, as the quote check folds it.", _folded_text))
register_kernel(Kernel("mini.kernel.json-readable", "Whether the reader can read this text as JSON.", _json_readable))
register_kernel(Kernel("mini.kernel.carries-because", "Whether a keyword format check would pass on this text.", _carries_because))


# --- the transforms ---


def _fold_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _upper_case(text: str) -> str:
    return text.upper()


def _wrap_in_code_fence(text: str) -> str:
    return f"```json\n{text}\n```"


def _reorder_paragraphs(text: str) -> str:
    return "\n\n".join(reversed(text.split("\n\n")))


def _append_blank_line(text: str) -> str:
    return text + "\n"


register_transform(Transform("mini.transform.fold-whitespace", "Collapse every run of whitespace.", _fold_whitespace))
register_transform(Transform("mini.transform.upper-case", "Put the text in capitals.", _upper_case))
register_transform(Transform("mini.transform.wrap-in-code-fence", "Wrap the text in a markdown code fence.", _wrap_in_code_fence))
register_transform(Transform("mini.transform.reorder-paragraphs", "Reverse the order of the paragraphs.", _reorder_paragraphs))
register_transform(Transform("mini.transform.append-blank-line", "Add a newline at the end.", _append_blank_line))


# --- the catalogue ---


def catalogue_from(state: Any, blobs: Any) -> dict[tuple[str, str], bool]:
    """Read the catalogue out of a run's own evidence, never off the disk."""

    listed: dict[tuple[str, str], bool] = {}
    for block in state.blocks:
        if block.get("source_id") != CATALOGUE_SOURCE:
            continue
        window = blobs.get(str(block["source_ref"]))[int(block["span_start"]) : int(block["span_end"])]
        try:
            parsed = loads_strict(window.decode("utf-8"))
        except (RecordError, UnicodeDecodeError):
            continue
        for point in (parsed or {}).get("points", []) if type(parsed) is dict else []:
            listed[(str(point.get("kernel")), str(point.get("transform")))] = bool(point.get("moves"))
    return listed


def catalogue_from_blocks(context: MachineContext) -> dict[tuple[str, str], bool]:
    return catalogue_from(context.state, context.blobs)


def _proposal_of(context: MachineContext, record: Mapping[str, Any]) -> dict[str, Any] | None:
    try:
        parsed = loads_strict(context.commitments(record))
    except RecordError:
        return None
    return parsed if type(parsed) is dict else None


# --- the machine seats ---


def _execute(context: MachineContext) -> str:
    """Run every proposal of this cycle through its kernel, before and after."""

    executions: list[dict[str, Any]] = []
    lines: list[str] = []
    for record in context.artifacts_of_kind(PROPOSAL_KIND, cycle=context.cycle):
        proposal = _proposal_of(context, record)
        entry: dict[str, Any] = {"proposal": str(record["artifact_id"])[:16]}
        if proposal is None:
            entry.update({"executed": "unreadable", "detail": "the proposal's commitments are not readable as JSON"})
            executions.append(entry)
            lines.append(f"{entry['proposal']}: unreadable")
            continue
        kernel_id, transform_id = str(proposal.get("kernel")), str(proposal.get("transform"))
        try:
            kernel, transform = resolve_kernel(kernel_id), resolve_transform(transform_id)
        except MiniError as error:
            entry.update({"executed": "unrunnable", "detail": str(error), "kernel": kernel_id, "transform": transform_id})
            executions.append(entry)
            lines.append(f"{entry['proposal']}: unrunnable")
            continue
        source = str(proposal.get("input", ""))
        before, after = kernel.verdict(source), kernel.verdict(transform.rewrite(source))
        entry.update(
            {
                "kernel": kernel_id,
                "transform": transform_id,
                "before": before,
                "after": after,
                "executed": "moved" if before != after else "unchanged",
            }
        )
        executions.append(entry)
        lines.append(f"{entry['proposal']}: {kernel_id} under {transform_id} -> {entry['executed']}")
    return json.dumps(
        {
            "body": "Executed this cycle's proposals.\n" + ("\n".join(lines) or "(no proposal to run)"),
            "commitments": json.dumps({"executions": executions}, ensure_ascii=False, sort_keys=True),
        },
        ensure_ascii=False,
    )


def standing_for(executed: str, catalogued: bool, catalogue_moves: bool | None = None) -> str:
    """The rule, stated once: read by the machine seat and by the tests.

    A defect is the catalogue and the execution DISAGREEING — the catalogue
    claiming a movement that did not happen, or denying one that did. A
    catalogued pair whose execution agrees with the catalogue is neither a
    defect nor a discovery. Only an uncatalogued movement is a candidate point;
    an uncatalogued non-movement is an invariance and belongs in the ledger
    `compare` prints, not in a standing.
    """

    if catalogued:
        return STANDING_DEFECT if (executed == "moved") != bool(catalogue_moves) else STANDING_REJECTED
    return STANDING_CANDIDATE if executed == "moved" else STANDING_REJECTED


def _verdict(context: MachineContext) -> str:
    """Set this cycle's executions against the catalogue, and commit a standing."""

    catalogue = catalogue_from_blocks(context)
    verdicts: list[dict[str, Any]] = []
    for record in context.artifacts_of_kind(EXECUTION_KIND, cycle=context.cycle):
        parsed = _proposal_of(context, record) or {}
        for entry in parsed.get("executions", []):
            executed = str(entry.get("executed"))
            key = (str(entry.get("kernel")), str(entry.get("transform")))
            catalogued = key in catalogue
            claims = catalogue.get(key)
            verdicts.append(
                {
                    "proposal": str(entry.get("proposal")),
                    "kernel": key[0],
                    "transform": key[1],
                    "executed": executed,
                    "catalogued": catalogued,
                    "catalogue_moves": bool(claims),
                    "standing": standing_for(executed, catalogued, claims),
                }
            )
    lines = [
        f"{item['proposal']}: {item['kernel']} under {item['transform']} {item['executed']}, "
        f"{'catalogue says it ' + ('moves' if item['catalogue_moves'] else 'does not move') if item['catalogued'] else 'not catalogued'}"
        f" -> {item['standing']}"
        for item in verdicts
    ]
    return json.dumps(
        {
            "body": "Verdict on this cycle's executions.\n" + ("\n".join(lines) or "(nothing executed)"),
            "commitments": json.dumps({"verdicts": verdicts}, ensure_ascii=False, sort_keys=True),
        },
        ensure_ascii=False,
    )


EXECUTOR_SEAT = register_machine_seat(
    MachineSeat(EXECUTION_KIND, "Runs this cycle's proposals through their kernels.", _execute)
)
VERDICT_SEAT = register_machine_seat(
    MachineSeat(VERDICT_KIND, "Sets this cycle's executions against the catalogue.", _verdict)
)

#: The schema a verdict's commitments must fit, whichever kind of seat fills it.
VERDICT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["verdicts"],
    "properties": {
        "verdicts": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["proposal", "executed", "catalogued", "standing"],
                "properties": {
                    "proposal": {"type": "string"},
                    "kernel": {"type": "string"},
                    "transform": {"type": "string"},
                    "executed": {"type": "string"},
                    "catalogued": {"type": "boolean"},
                    "standing": {"enum": list(STANDINGS)},
                },
            },
        }
    },
}
