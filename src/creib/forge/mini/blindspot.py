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
from .formats import loads_admitting_control
from .machines import MachineContext, MachineSeat, register_machine_seat

PROPOSAL_KIND = "mini.proposal.v1"
EXECUTION_KIND = "mini.execution.v1"
#: A proposal that carries its own rewrite: {kernel, input, rewritten, expect}. No transform
#: registry stands between the proposer and the check, so a rewrite nobody registered can be
#: proposed; the executor runs the kernel on both texts.
PAIR_PROPOSAL_KIND = "mini.pair-proposal.v1"
#: Any kind whose id begins so is a pair proposal: a template may declare several, one per
#: target, each with its own instruction, and the executor reads them all.
PAIR_PROPOSAL_PREFIX = "mini.pair-proposal."
PAIR_EXECUTION_KIND = "mini.pair-execution.v1"
EXPECTATIONS: tuple[str, ...] = ("moves", "unchanged")
#: A prediction is a second reading of a pair: a seat that read something other than what the
#: proposer read (the code where the proposer read the rule, or the reverse) commits, for one
#: proposal, what it expects the executed answer to do. Its kind id carries this prefix and its
#: commitments are JSON ``{"proposal": <id prefix>, "expect": "moves" | "unchanged"}``.
PAIR_PREDICTION_PREFIX = "mini.pair-prediction."
READING_ABSENT = "no prediction"
READING_AGREE = "expectation and prediction both held"
READING_RULE_DIVERGES = "expectation failed, prediction held"
READING_CODE_MISREAD = "expectation held, prediction failed"
READING_NEITHER = "expectation and prediction both failed"
READING_UNREADABLE = "prediction unreadable"
READINGS: tuple[str, ...] = (READING_ABSENT, READING_AGREE, READING_RULE_DIVERGES, READING_CODE_MISREAD, READING_NEITHER, READING_UNREADABLE)
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
    #: The verdict this kernel gives when it cannot read its input at all; an execution on
    #: which either side is this verdict is ``unrunnable``, not a move (mini register M11).
    unreadable: str | None = None


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


#: What a catalogue row says: whether the kernel's verdict moved under the transform, and the
#: input that was checked, when the row names one. A row without an input is a claim about the
#: pair alone and cannot be told from a row about some other input.
CatalogueRow = dict[str, Any]


def catalogue_from(state: Any, blobs: Any) -> dict[tuple[str, str], CatalogueRow]:
    """Read the catalogue out of a run's own evidence, never off the disk."""

    listed: dict[tuple[str, str], CatalogueRow] = {}
    for block in state.blocks:
        if block.get("source_id") != CATALOGUE_SOURCE:
            continue
        window = blobs.get(str(block["source_ref"]))[int(block["span_start"]) : int(block["span_end"])]
        try:
            parsed = loads_strict(window.decode("utf-8"))
        except (RecordError, UnicodeDecodeError):
            continue
        for point in (parsed or {}).get("points", []) if type(parsed) is dict else []:
            source = point.get("input")
            listed[(str(point.get("kernel")), str(point.get("transform")))] = {
                "moves": bool(point.get("moves")),
                "input": source if type(source) is str else None,
            }
    return listed


def catalogue_from_blocks(context: MachineContext) -> dict[tuple[str, str], CatalogueRow]:
    return catalogue_from(context.state, context.blobs)


def registry_text(prefix: str = "") -> str:
    """The registered kernels and transforms as a proposer is shown them: one per paragraph.

    A proposer asked for registered ids and shown none invents them (the first live run of the
    blind-spot template, mini register M5); a JSON registry cut at blank lines is one block and
    the legend shows only its first line (M6). A text registry, one entry per paragraph, is a
    source the legend can show whole.
    """

    lines = [f"kernel {kernel.kernel_id}: {kernel.description}" for kernel in registered_kernels() if kernel.kernel_id.startswith(prefix)]
    lines += [f"transform {transform.transform_id}: {transform.description}" for transform in registered_transforms() if transform.transform_id.startswith(prefix)]
    return "\n\n".join(lines) + "\n"


def _proposal_of(context: MachineContext, record: Mapping[str, Any]) -> dict[str, Any] | None:
    """The commitments of one artifact, read as the format layer read them.

    A raw line break a model wrote inside the string is admitted here as it is there
    (`formats.loads_admitting_control`); a seat that refused what the format accepted would
    mark its own run's proposals unreadable, which is what mini register M13 records.
    """

    try:
        parsed, _recovered = loads_admitting_control(context.commitments(record))
    except RecordError:
        parsed = {}
    fields = dict(parsed) if type(parsed) is dict else {}
    # A kind may carry the long fields as its own optional fields instead of nesting them in
    # the commitments string, where they would need a second level of escaping (M13). They are
    # read here as if they had been written there, and they win where both are present.
    fields.update({name: value for name, value in dict(record.get("extra") or {}).items() if type(value) is str})
    return fields or None


# --- the machine seats ---


def _executed_before(context: MachineContext, execution_kind: str, keys: tuple[str, ...]) -> set[tuple[str, ...]]:
    """The keys every earlier execution of this kind in the run already ran, so a repeat is named, not re-run."""

    seen: set[tuple[str, ...]] = set()
    for record in context.artifacts_of_kind(execution_kind):
        if int(record.get("cycle", 0)) >= context.cycle:
            continue
        parsed = _proposal_of(context, record) or {}
        for entry in parsed.get("executions", []):
            if all(key in entry for key in keys):
                seen.add(tuple(str(entry[key]) for key in keys))
    return seen


def _execute(context: MachineContext) -> str:
    """Run every proposal of this cycle through its kernel, before and after.

    A triple the run already executed, in an earlier cycle or earlier in this one, is marked
    ``duplicate`` and not run again (mini register M10): the record says the proposer repeated
    itself, and the verdict rejects the repeat.
    """

    executions: list[dict[str, Any]] = []
    lines: list[str] = []
    seen = _executed_before(context, EXECUTION_KIND, ("kernel", "transform", "input"))
    for record in context.artifacts_of_kind(PROPOSAL_KIND, cycle=context.cycle):
        proposal = _proposal_of(context, record)
        entry: dict[str, Any] = {"proposal": str(record["artifact_id"])[:16]}
        if proposal is None:
            entry.update({"executed": "unreadable", "detail": "the proposal's commitments are not readable as JSON"})
            executions.append(entry)
            lines.append(f"{entry['proposal']}: unreadable")
            continue
        kernel_id, transform_id = str(proposal.get("kernel")), str(proposal.get("transform"))
        triple = (kernel_id, transform_id, str(proposal.get("input", "")))
        if triple in seen:
            entry.update({"executed": "duplicate", "kernel": kernel_id, "transform": transform_id, "input": triple[2], "detail": "this run already executed this kernel, transform and input"})
            executions.append(entry)
            lines.append(f"{entry['proposal']}: duplicate")
            continue
        seen.add(triple)
        try:
            kernel, transform = resolve_kernel(kernel_id), resolve_transform(transform_id)
        except MiniError as error:
            entry.update({"executed": "unrunnable", "detail": str(error), "kernel": kernel_id, "transform": transform_id})
            executions.append(entry)
            lines.append(f"{entry['proposal']}: unrunnable")
            continue
        source = str(proposal.get("input", ""))
        before, after = kernel.verdict(source), kernel.verdict(transform.rewrite(source))
        entry.update({"kernel": kernel_id, "transform": transform_id, "input": source, "before": before, "after": after})
        if kernel.unreadable is not None and kernel.unreadable in (before, after):
            entry.update({"executed": "unrunnable", "detail": _unreadable_detail(kernel, before, after)})
        else:
            entry["executed"] = "moved" if before != after else "unchanged"
        executions.append(entry)
        lines.append(f"{entry['proposal']}: {kernel_id} under {transform_id} -> {entry['executed']}")
    return json.dumps(
        {
            "body": "Executed this cycle's proposals.\n" + ("\n".join(lines) or "(no proposal to run)"),
            "commitments": json.dumps({"executions": executions}, ensure_ascii=False, sort_keys=True),
        },
        ensure_ascii=False,
    )


COLUMN_MOVES = "moves"
COLUMN_UNCHANGED = "unchanged"
COLUMNS: tuple[str, ...] = (COLUMN_MOVES, COLUMN_UNCHANGED)


def _execute_pairs(context: MachineContext) -> str:
    """Run every pair proposal of this cycle: the kernel on the input and on the proposer's own rewrite."""

    executions: list[dict[str, Any]] = []
    lines: list[str] = []
    seen = _executed_before(context, PAIR_EXECUTION_KIND, ("kernel", "input", "rewritten"))
    proposals = [
        context.state.artifacts[key]
        for key in context.state.artifact_order
        if str(context.state.artifacts[key]["kind_id"]).startswith(PAIR_PROPOSAL_PREFIX)
        and int(context.state.artifacts[key].get("cycle", 0)) == context.cycle
    ]
    for record in proposals:
        proposal = _proposal_of(context, record)
        entry: dict[str, Any] = {"proposal": str(record["artifact_id"])[:16]}
        if proposal is None:
            entry.update({"executed": "unreadable", "detail": "the proposal's commitments are not readable as JSON"})
            executions.append(entry)
            lines.append(f"{entry['proposal']}: unreadable")
            continue
        kernel_id = str(proposal.get("kernel"))
        source, rewritten = str(proposal.get("input", "")), str(proposal.get("rewritten", ""))
        expect = str(proposal.get("expect", ""))
        entry.update({"kernel": kernel_id, "input": source, "rewritten": rewritten, "expect": expect, "rewrite": str(proposal.get("rewrite", ""))})
        if expect not in EXPECTATIONS:
            entry.update({"executed": "unrunnable", "detail": f"expect must be one of {list(EXPECTATIONS)}"})
            executions.append(entry)
            lines.append(f"{entry['proposal']}: unrunnable")
            continue
        try:
            kernel = resolve_kernel(kernel_id)
        except MiniError as error:
            entry.update({"executed": "unrunnable", "detail": str(error)})
            executions.append(entry)
            lines.append(f"{entry['proposal']}: unrunnable")
            continue
        if (kernel_id, source, rewritten) in seen:
            entry.update({"executed": "duplicate", "detail": "this run already executed this kernel on this pair"})
            executions.append(entry)
            lines.append(f"{entry['proposal']}: duplicate")
            continue
        if source == rewritten:
            entry.update({"executed": "unrunnable", "detail": "the rewritten text is the input unchanged"})
            executions.append(entry)
            lines.append(f"{entry['proposal']}: unrunnable")
            continue
        seen.add((kernel_id, source, rewritten))
        before, after = kernel.verdict(source), kernel.verdict(rewritten)
        entry.update({"before": before, "after": after})
        if kernel.unreadable is not None and kernel.unreadable in (before, after):
            entry.update({"executed": "unrunnable", "detail": _unreadable_detail(kernel, before, after)})
            executions.append(entry)
            lines.append(f"{entry['proposal']}: unrunnable")
            continue
        executed = "moved" if before != after else "unchanged"
        entry.update({"executed": executed, "as_expected": (executed == "moved") == (expect == "moves")})
        executions.append(entry)
        lines.append(f"{entry['proposal']}: {kernel_id} -> {executed}, expected {expect}")
    return json.dumps(
        {
            "body": "Executed this cycle's pair proposals.\n" + ("\n".join(lines) or "(no proposal to run)"),
            "commitments": json.dumps({"executions": executions}, ensure_ascii=False, sort_keys=True),
        },
        ensure_ascii=False,
    )


def _unreadable_detail(kernel: Kernel, before: str, after: str) -> str:
    sides = [name for name, verdict in (("the input", before), ("the rewritten text", after)) if verdict == kernel.unreadable]
    return f"{kernel.kernel_id} could not read {' and '.join(sides)} ({kernel.unreadable}); a move to or from that verdict is not a move"


def predictions_of(context: MachineContext) -> dict[str, str]:
    """This cycle's predictions by the proposal id prefix they name: the expectation, or ``?`` when unreadable."""

    found: dict[str, str] = {}
    for key in context.state.artifact_order:
        record = context.state.artifacts[key]
        if not str(record["kind_id"]).startswith(PAIR_PREDICTION_PREFIX) or int(record.get("cycle", 0)) != context.cycle:
            continue
        parsed = _proposal_of(context, record)
        if parsed is None:
            continue
        proposal, expect = str(parsed.get("proposal", "")), str(parsed.get("expect", ""))
        found[proposal[:16]] = expect if expect in EXPECTATIONS else "?"
    return found


def reading_for(executed: str, expect: str, predicted: str | None) -> str:
    """How the two readings of a pair fared against the machine: nothing is decided, the pairing is named."""

    if predicted is None:
        return READING_ABSENT
    if predicted not in EXPECTATIONS or executed not in ("moved", "unchanged") or expect not in EXPECTATIONS:
        return READING_UNREADABLE
    held = (executed == "moved") == (expect == "moves")
    predicted_held = (executed == "moved") == (predicted == "moves")
    if held and predicted_held:
        return READING_AGREE
    if held:
        return READING_CODE_MISREAD
    return READING_RULE_DIVERGES if predicted_held else READING_NEITHER


NEXT_CELL_KIND = "mini.next-cell.v1"
GRID_SOURCE = "grid"


def grid_cells(state: Any, blobs: Any) -> tuple[str, ...]:
    """The cells of the grid, one per paragraph of the ``grid`` source, read out of the run's own evidence."""

    cells: list[str] = []
    for block in state.blocks:
        if block.get("source_id") != GRID_SOURCE:
            continue
        window = blobs.get(str(block["source_ref"]))[int(block["span_start"]) : int(block["span_end"])]
        text = " ".join(window.decode("utf-8", errors="replace").split())
        if text:
            cells.append(text)
    return tuple(cells)


def cells_named(context: MachineContext) -> dict[str, int]:
    """How many times each cell has been named in any artifact's commitments so far, its own kind's included."""

    counts: dict[str, int] = {}
    for key in context.state.artifact_order:
        parsed = _proposal_of(context, context.state.artifacts[key])
        if parsed is None or type(parsed.get("cell")) is not str:
            continue
        cell = " ".join(parsed["cell"].split())
        counts[cell] = counts.get(cell, 0) + 1
    return counts


def _next_cell(context: MachineContext) -> str:
    """A machine seat that names the cell of the grid to cover next: the first named least often.

    The grid is enumerated by machine and instantiated by the model, so which cells get covered
    is not the proposer's choice. A proposer that names a cell in its commitments counts as
    covering it; so does this seat's own earlier output, so three seats in one cycle name three
    cells. When every cell has been named the count starts again from the least named, and the
    executor names the repeats.
    """

    cells = grid_cells(context.state, context.blobs)
    if not cells:
        return json.dumps({"body": "The grid source holds no cell.", "commitments": json.dumps({"cell": ""})})
    counts = cells_named(context)
    cell = min(cells, key=lambda item: (counts.get(item, 0), cells.index(item)))
    named = sum(1 for item in cells if counts.get(item, 0))
    return json.dumps(
        {
            "body": f"The cell to cover: {cell}\n({named} of {len(cells)} cells named so far.)",
            "commitments": json.dumps({"cell": cell}, ensure_ascii=False),
        },
        ensure_ascii=False,
    )


NEXT_CELL_SEAT = register_machine_seat(MachineSeat(NEXT_CELL_KIND, "Names the cell of the grid source named least often so far.", _next_cell))
#: A port window is counted in cycles, so a proposer that must see one cell and not its
#: neighbours' draws a kind of its own: the same seat under a numbered kind id, one per proposer
#: stage of a cycle.
NEXT_CELL_KINDS: tuple[str, ...] = tuple(f"mini.next-cell.{index}.v1" for index in (1, 2, 3))
for _kind_id in NEXT_CELL_KINDS:
    register_machine_seat(MachineSeat(_kind_id, "Names the cell of the grid source named least often so far, for one proposer stage.", _next_cell))


def standing_for_pair(executed: str, expect: str) -> str:
    """The rule for a proposer's own rewrite, where no catalogue row applies.

    The proposer said what it expected. A rewrite it expected to move the verdict that did
    not is a candidate point for the unchanged column: a rewrite the proposer judged material
    that the check cannot see. A rewrite it expected to leave the verdict alone that moved it
    is a candidate for the moves column: a sensitivity nobody asked for. Agreement adds no
    row, and a pair that could not run or was a repeat is rejected.
    """

    if executed not in ("moved", "unchanged") or expect not in EXPECTATIONS:
        return STANDING_REJECTED
    return STANDING_REJECTED if (executed == "moved") == (expect == "moves") else STANDING_CANDIDATE


def standing_for(
    executed: str,
    catalogued: bool,
    catalogue_moves: bool | None = None,
    same_input: bool | None = None,
) -> str:
    """The rule, stated once: read by the machine seat and by the tests.

    A kernel point in this repository has two columns, what the verdict moves
    under and what it does not, and each is shown on one input. The rule reads
    a catalogue row the same way:

    - A row that says the pair does NOT move is an invariance claim over every
      input of the class; one execution that moves refutes it, and that is a
      DEFECT in the catalogue. An execution that does not move agrees.
    - A row that says the pair MOVES is a sensitivity shown on the row's own
      input. An execution that moves agrees. One that does not move on the same
      input is a DEFECT, the row's own example being wrong; on another input
      it is a CANDIDATE POINT for the unchanged column, an input on which the
      check is blind to a rewrite it sees elsewhere.
    - An uncatalogued pair is a CANDIDATE POINT either way: for the moves
      column if it moved, for the unchanged column if it did not. The second
      is the blind spot nobody wrote down, which is what the loop is for.
    - A proposal that could not be run is REJECTED, and so is an agreement:
      neither adds a row.

    Until 10 September an uncatalogued non-movement was rejected and a
    catalogued pair was compared without regard to its input, so a proposal on
    a different input read as a defect where the catalogue and the code agree
    (the first live run of the conformance template).
    """

    if executed not in ("moved", "unchanged"):
        return STANDING_REJECTED
    moved = executed == "moved"
    if not catalogued:
        return STANDING_CANDIDATE
    if not bool(catalogue_moves):
        return STANDING_DEFECT if moved else STANDING_REJECTED
    if moved:
        return STANDING_REJECTED
    return STANDING_DEFECT if same_input else STANDING_CANDIDATE


def column_for(executed: str, standing: str) -> str | None:
    """Which column of a kernel point a candidate would fill; nothing for any other standing."""

    if standing != STANDING_CANDIDATE:
        return None
    return COLUMN_MOVES if executed == "moved" else COLUMN_UNCHANGED


def _verdict(context: MachineContext) -> str:
    """Set this cycle's executions against the catalogue, and commit a standing."""

    catalogue = catalogue_from_blocks(context)
    verdicts: list[dict[str, Any]] = []
    for record in context.artifacts_of_kind(EXECUTION_KIND, cycle=context.cycle):
        parsed = _proposal_of(context, record) or {}
        for entry in parsed.get("executions", []):
            executed = str(entry.get("executed"))
            key = (str(entry.get("kernel")), str(entry.get("transform")))
            row = catalogue.get(key)
            catalogued = row is not None
            claims = None if row is None else bool(row["moves"])
            row_input = None if row is None else row["input"]
            same_input = None if row_input is None or "input" not in entry else str(entry["input"]) == row_input
            standing = standing_for(executed, catalogued, claims, same_input)
            verdicts.append(
                {
                    "proposal": str(entry.get("proposal")),
                    "kernel": key[0],
                    "transform": key[1],
                    "executed": executed,
                    "catalogued": catalogued,
                    "catalogue_moves": bool(claims),
                    "same_input": same_input,
                    "standing": standing,
                    "column": column_for(executed, standing),
                }
            )
    lines = [
        f"{item['proposal']}: {item['kernel']} under {item['transform']} {item['executed']}, "
        f"{'catalogue says it ' + ('moves' if item['catalogue_moves'] else 'does not move') + ('' if item['same_input'] is None else (' on this input' if item['same_input'] else ' on another input')) if item['catalogued'] else 'not catalogued'}"
        f" -> {item['standing']}{'' if item['column'] is None else ' (' + item['column'] + ')'}"
        for item in verdicts
    ]
    predictions = predictions_of(context)
    for record in context.artifacts_of_kind(PAIR_EXECUTION_KIND, cycle=context.cycle):
        parsed = _proposal_of(context, record) or {}
        for entry in parsed.get("executions", []):
            executed, expect = str(entry.get("executed")), str(entry.get("expect", ""))
            standing = standing_for_pair(executed, expect)
            proposal = str(entry.get("proposal"))
            predicted = predictions.get(proposal[:16])
            item = {
                "proposal": proposal,
                "kernel": str(entry.get("kernel")),
                "transform": "proposer's own rewrite: " + str(entry.get("rewrite", ""))[:120],
                "executed": executed,
                "expected": expect,
                "predicted": predicted,
                "reading": reading_for(executed, expect, predicted),
                "catalogued": False,
                "catalogue_moves": False,
                "same_input": None,
                "standing": standing,
                "column": column_for(executed, standing),
            }
            verdicts.append(item)
            lines.append(
                f"{item['proposal']}: {item['kernel']} under {item['transform']} {executed}, expected {expect or 'nothing'}"
                f"{'' if predicted is None else ', predicted ' + predicted}"
                f" -> {standing}{'' if item['column'] is None else ' (' + item['column'] + ')'}; {item['reading']}"
            )
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
PAIR_EXECUTOR_SEAT = register_machine_seat(
    MachineSeat(PAIR_EXECUTION_KIND, "Runs this cycle's pair proposals: the kernel on the input and on the proposer's own rewrite.", _execute_pairs)
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
                    "predicted": {"enum": [*EXPECTATIONS, "?", None]},
                    "reading": {"enum": list(READINGS)},
                    "catalogued": {"type": "boolean"},
                    "standing": {"enum": list(STANDINGS)},
                    "column": {"enum": [*COLUMNS, None]},
                    "expected": {"type": "string"},
                },
            },
        }
    },
}
