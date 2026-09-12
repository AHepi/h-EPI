"""DECIDE-TEST-1: the states a decision is put in, the six briefs, and how a choice is scored.

`docs/mini/DECIDE_TEST_1.md` is the pre-registration and this module is what it describes. Everything
here is offline: it builds briefs, enumerates options, and scores a choice against a grid of runs. It
calls nothing. `tools/mini_decide.py` runs the grid and the decisions.

The point of the block is that nothing larger than the model under test decides anything. A choice is
scored against what the grid actually yielded, and the campaign comparison is against a function of six
numbers. There is no adjudicator anywhere in it.
"""

from __future__ import annotations

import importlib
import inspect
import json
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from creib.forge.mini.common import MiniError

#: The three checks whose documented rules ``creib.forge.mini.rule_readings`` implements, so every
#: outcome in this block is adjudicated by machine rather than taken from a model's prose.
WORKING_SET: tuple[str, ...] = (
    "creib.forge.conformance.oracle.recover_json_object",
    "creib.forge.conformance.oracle.refusal_phrase_in",
    "creib.forge.conformance.oracle._plain_quotes",
)

#: The option a decision may take. A ``move`` option carries the check it moves to.
STAY = "stay"
STOP = "stop"
MOVE = "move-to-"

#: The six briefs. ``plain`` is the canonical stacking; the rest change one thing each.
PLAIN = "plain"
REPEAT = "repeat"
REORDERED = "reordered"
RELABELLED = "relabelled"
CONTRAST = "contrast"
ABLATED = "ablated"
BRIEFS: tuple[str, ...] = (PLAIN, REPEAT, REORDERED, RELABELLED, CONTRAST, ABLATED)

#: Which briefs change only the form of the state and which change what it says. A decider must be
#: insensitive to the first and sensitive to the second; the pre-registration turns each into a
#: conjecture that this block's records can refute.
FORM_BRIEFS: tuple[str, ...] = (REORDERED, RELABELLED)
CONTENT_BRIEFS: tuple[str, ...] = (CONTRAST, ABLATED)

#: The neutral names ``relabelled`` gives the checks, in a fixed order, so the recoding preserves
#: content exactly and is the same every time it is built. They are valid identifiers because the
#: recoding renames the function INSIDE the source as well: a brief that renamed only the labels while
#: the source still said ``def recover_json_object`` would leave the model its memory of the name, and
#: then a choice that did not move under relabelling would show nothing about form.
NEUTRAL_NAMES: tuple[str, ...] = ("check_one", "check_two", "check_three")


@dataclass(frozen=True)
class Tally:
    """What has been spent on one check and what came back."""

    check: str
    segments: int
    finds: int
    real_classes: int

    @property
    def name(self) -> str:
        return self.check.rsplit(".", 1)[-1]


@dataclass(frozen=True)
class State:
    """One decision point: the check being worked and the figures for all three."""

    point_id: str
    current: str
    tallies: tuple[Tally, ...]

    def __post_init__(self) -> None:
        names = [tally.check for tally in self.tallies]
        if len(set(names)) != len(names):
            raise MiniError("MINI_COLLAPSE_CLASS_INVALID",
                            f"{self.point_id}: a state carries one tally per check, got {names}")
        if self.current not in names:
            raise MiniError("MINI_COLLAPSE_CLASS_INVALID",
                            f"{self.point_id}: the check being worked, {self.current!r}, has no tally")

    def tally_of(self, check: str) -> Tally:
        for tally in self.tallies:
            if tally.check == check:
                return tally
        raise MiniError("MINI_COLLAPSE_CLASS_INVALID", f"{self.point_id}: no tally for {check!r}")

    @property
    def others(self) -> tuple[str, ...]:
        return tuple(tally.check for tally in self.tallies if tally.check != self.current)


def move_option(check: str) -> str:
    """The option id for moving to one check."""

    return MOVE + check.rsplit(".", 1)[-1]


def options_of(state: State) -> tuple[str, ...]:
    """The options the machine enumerates at one point, in a fixed order."""

    return (STAY,) + tuple(move_option(check) for check in state.others) + (STOP,)


def check_of_option(state: State, option: str) -> str | None:
    """Which check an option works, or ``None`` for ``stop``."""

    if option == STAY:
        return state.current
    if option == STOP:
        return None
    for check in state.others:
        if move_option(check) == option:
            return check
    raise MiniError("MINI_COLLAPSE_CLASS_INVALID",
                    f"{state.point_id}: {option!r} is not one of {options_of(state)}")


# ------------------------------------------------------------------------------------------------
# The grid, and what it says the right answer is
# ------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Grid:
    """Per check, how many NEW real collapse classes each of its segments produced, in order.

    A number is new classes and not classes, so summing a tail is the yield still to come. The grid is
    the whole of the ground truth in this block: nothing about a right answer is taken from an earlier
    block, which only says what to expect.
    """

    new_real_classes: Mapping[str, tuple[int, ...]]

    def __post_init__(self) -> None:
        for check, row in self.new_real_classes.items():
            if any(count < 0 for count in row):
                raise MiniError("MINI_COLLAPSE_CLASS_INVALID",
                                f"{check}: a grid row counts new classes and cannot go negative: {row}")

    def segments(self, check: str) -> int:
        return len(self.row(check))

    def row(self, check: str) -> tuple[int, ...]:
        if check not in self.new_real_classes:
            raise MiniError("MINI_COLLAPSE_CLASS_INVALID", f"the grid has no row for {check!r}")
        return tuple(self.new_real_classes[check])

    def remaining(self, check: str, spent: int) -> int:
        """New real classes the grid found on this check after its first ``spent`` segments."""

        return sum(self.row(check)[spent:])


def remaining_yield(grid: Grid, state: State, option: str) -> int:
    """What the grid says one option still had to give at this point. ``stop`` gives nothing."""

    check = check_of_option(state, option)
    if check is None:
        return 0
    return grid.remaining(check, state.tally_of(check).segments)


def right_options(grid: Grid, state: State) -> frozenset[str]:
    """Every option with the most remaining yield. ``stop`` is right only when nothing is left."""

    scores = {option: remaining_yield(grid, state, option) for option in options_of(state)}
    best = max(scores.values())
    if best == 0:
        return frozenset({STOP})
    return frozenset(option for option, score in scores.items() if score == best)


def random_hit_rate(grid: Grid, states: Sequence[State]) -> float:
    """The expected hit rate of choosing uniformly among the enumerated options."""

    if not states:
        raise MiniError("MINI_COLLAPSE_CLASS_INVALID", "a baseline over no state says nothing")
    total = 0.0
    for state in states:
        options = options_of(state)
        total += len(right_options(grid, state) & set(options)) / len(options)
    return total / len(states)


def fixed_hit_rate(grid: Grid, states: Sequence[State], option: str) -> float:
    """The hit rate of always choosing one option, where it is available."""

    if not states:
        raise MiniError("MINI_COLLAPSE_CLASS_INVALID", "a baseline over no state says nothing")
    return sum(1 for state in states
               if option in options_of(state) and option in right_options(grid, state)) / len(states)


# ------------------------------------------------------------------------------------------------
# The briefs
# ------------------------------------------------------------------------------------------------


def source_of(check: str) -> str:
    """One check's own source, docstring included, as the model is shown it."""

    module_name, _, function_name = check.rpartition(".")
    try:
        function = getattr(importlib.import_module(module_name), function_name)
        return inspect.getsource(function)
    except (ImportError, AttributeError, OSError, TypeError) as error:
        raise MiniError("MINI_COLLAPSE_CLASS_INVALID",
                        f"the source of {check} could not be read: {error}") from error


TASK = (
    "You are running a search. The thing being looked for is a pair of reply texts that one of the "
    "checks below answers the SAME on, where the check's own documented rule requires it to answer "
    "differently. When that happens nothing downstream can recover the difference, because the "
    "difference is not in the check's answer at all.\n\n"
    "You are not being asked to find one now. You are being asked what the search should do next."
)

#: The reply shape. The option id is the whole of ``body`` and the reason is the whole of
#: ``commitments``, with nothing nested inside either. Asking for a JSON object INSIDE the commitments
#: string is what broke 12 of block 2's 16 escaped readings, and there is no reason to repeat it when
#: the answer is one word (ERRATA C21).
INSTRUCTION = (
    "Choose exactly one of the options you are shown and say in one sentence why.\n\n"
    "Your reply is one JSON object and nothing else. Its \"body\" is the option id, copied exactly "
    "from the list and by itself with no other words. Its \"commitments\" is your one sentence. "
    "Nothing is nested inside either: they are plain strings.\n\n"
    "In full, a well formed reply looks exactly like this:\n\n"
    '{"body": "stop", "commitments": "Nothing has been found on any of them in the segments run so '
    'far."}\n\n'
    "An id that is not on the list is not a choice, and a body holding more than one of the ids names "
    "none of them."
)


def relabelling(state: State) -> dict[str, str]:
    """Check to neutral name, in the fixed order of the state's own tallies."""

    if len(state.tallies) > len(NEUTRAL_NAMES):
        raise MiniError("MINI_COLLAPSE_CLASS_INVALID",
                        f"{state.point_id}: {len(state.tallies)} checks and only "
                        f"{len(NEUTRAL_NAMES)} neutral names are declared")
    return {tally.check: NEUTRAL_NAMES[index] for index, tally in enumerate(state.tallies)}


def contrast_of(state: State) -> State:
    """The same state with the figures rewritten so a different option is the indicated one.

    The check being worked is given the figures of the other check that has been worked most, and that
    check is given the current one's. Nothing else moves: the same checks, the same sources, the same
    options, the same total spend. So a choice that follows the figures must move, and a choice that
    does not follow them cannot.
    """

    others = sorted(state.others, key=lambda check: (-state.tally_of(check).segments, check))
    if not others:
        raise MiniError("MINI_COLLAPSE_CLASS_INVALID",
                        f"{state.point_id}: a contrast needs a second check to swap with")
    partner = others[0]
    here, there = state.tally_of(state.current), state.tally_of(partner)
    swapped: list[Tally] = []
    for tally in state.tallies:
        if tally.check == state.current:
            swapped.append(Tally(tally.check, there.segments, there.finds, there.real_classes))
        elif tally.check == partner:
            swapped.append(Tally(tally.check, here.segments, here.finds, here.real_classes))
        else:
            swapped.append(tally)
    return State(point_id=state.point_id + ".contrast", current=state.current, tallies=tuple(swapped))


def _figures_block(state: State, names: Mapping[str, str]) -> str:
    lines = ["## What has been spent and what came back", "",
             "The figures are segments run, pairs found, and distinct ways of breaking the check "
             "those pairs represent. Two pairs that break a check the same way are one way.", ""]
    for tally in state.tallies:
        here = " (this is the check being worked now)" if tally.check == state.current else ""
        lines.append(f"- {names[tally.check]}: {tally.segments} segment(s) run, {tally.finds} pair(s) "
                     f"found, {tally.real_classes} distinct way(s) of breaking it{here}")
    return "\n".join(lines)


def recode(text: str, names: Mapping[str, str]) -> str:
    """Rename every check consistently throughout a text, longest name first.

    Longest first because one check's name can be a part of another's, and a shorter replacement made
    first would cut the longer one in half. The three names of the working set do not overlap, and the
    ordering is here so that a fourth which did would not quietly corrupt the recoding.
    """

    recoded = text
    for check in sorted(names, key=lambda name: -len(name.rsplit(".", 1)[-1])):
        recoded = recoded.replace(check.rsplit(".", 1)[-1], names[check])
    return recoded


def _sources_block(state: State, names: Mapping[str, str]) -> str:
    parts = ["## The checks, in full", ""]
    for tally in state.tallies:
        parts.append(f"### {names[tally.check]}")
        parts.append("")
        parts.append(recode(source_of(tally.check), names))
        parts.append("")
    return "\n".join(parts).rstrip()


def _options_block(state: State, names: Mapping[str, str]) -> str:
    lines = ["## The options, and there are no others", ""]
    for option in options_of(state):
        check = check_of_option(state, option)
        if option == STAY:
            lines.append(f"- `{option}` -- run another segment on {names[state.current]}")
        elif option == STOP:
            lines.append(f"- `{option}` -- stop: there is nothing further to find on any of these")
        else:
            lines.append(f"- `{option}` -- leave {names[state.current]} and run a segment on "
                         f"{names[check]}")
    return "\n".join(lines)


def option_ids(state: State, variant: str) -> dict[str, str]:
    """The id shown for each underlying option under one brief, so a reply can be read back.

    Only ``relabelled`` changes an id, and it changes it because the check's name is part of it. Every
    other brief shows the canonical ids, so a choice can be compared across briefs directly.
    """

    if variant != RELABELLED:
        return {option: option for option in options_of(state)}
    names = relabelling(state)
    shown: dict[str, str] = {}
    for option in options_of(state):
        check = check_of_option(state, option)
        shown[option] = option if check is None or option == STAY else MOVE + names[check]
    return shown


def brief(state: State, variant: str) -> str:
    """One decision point, put one of six ways."""

    if variant not in BRIEFS:
        raise MiniError("MINI_COLLAPSE_CLASS_INVALID",
                        f"unknown brief: {variant!r}; the briefs are {BRIEFS}")
    shown = state
    names = {tally.check: tally.name for tally in state.tallies}
    if variant == CONTRAST:
        shown = contrast_of(state)
    if variant == RELABELLED:
        names = relabelling(state)
    figures = _figures_block(shown, names)
    sources = _sources_block(shown, names)
    if variant == RELABELLED:
        options = "\n".join(
            line.replace(f"`{option}`", f"`{option_ids(state, variant)[option]}`")
            for option, line in zip(options_of(state), _options_block(shown, names).splitlines()[2:]))
        options = "## The options, and there are no others\n\n" + options
    else:
        options = _options_block(shown, names)
    blocks = [TASK, sources, figures, options, INSTRUCTION]
    if variant == ABLATED:
        blocks = [TASK, sources, options, INSTRUCTION]
    if variant == REORDERED:
        blocks = [options, figures, sources, TASK, INSTRUCTION]
    return "\n\n".join(blocks) + "\n"


def name_choice(body: str, shown: Mapping[str, str]) -> str:
    """Which of the shown option ids a body names, in canonical ids; empty when it names none.

    Two readings, in order, both pre-registered: the body IS one id, after whitespace and backticks
    come off; or exactly one id occurs somewhere in the body and no other does. A body holding two ids
    names neither, because nothing here is going to guess which one was meant.
    """

    text = body.strip().strip("`").strip()
    for canonical, displayed in shown.items():
        if text == displayed:
            return canonical
    inside = [canonical for canonical, displayed in shown.items() if displayed in text]
    # ``stay`` is a part of no other id and ``stop`` of none either, but a longer id can hold a
    # shorter one in another option set, so a body matching two names neither.
    return inside[0] if len(inside) == 1 else ""


def read_choice(body: str, state: State, variant: str) -> str:
    """Which option a decision's body chose, in canonical ids."""

    return name_choice(body, option_ids(state, variant))


def agreement(first: Mapping[str, str], second: Mapping[str, str]) -> tuple[int, int]:
    """How many points two briefs chose the same option on, and how many both answered at all."""

    both = [key for key in first if key in second and first[key] and second[key]]
    return (sum(1 for key in both if first[key] == second[key]), len(both))


def states_from_grid(grid: Grid, cuts: Iterable[int] = (1, 2, 4, 6),
                     finds: Mapping[str, tuple[int, ...]] | None = None) -> tuple[State, ...]:
    """The decision points: each check cut at each of ``cuts``, with the other checks as at that time.

    The three grids are read as if run in the declared order of :data:`WORKING_SET`, one segment each
    in turn, so a point's figures for the other checks are what had been run by then rather than
    anything invented. ``finds`` carries each check's per-segment find counts when they are known, so
    the figures a model is shown are the real ones and not only the class counts.
    """

    checks = [check for check in WORKING_SET if check in grid.new_real_classes]
    if not checks:
        raise MiniError("MINI_COLLAPSE_CLASS_INVALID", "the grid holds no check of the working set")
    built: list[State] = []
    for current in checks:
        for cut in cuts:
            if cut > grid.segments(current):
                continue
            tallies: list[Tally] = []
            for check in checks:
                # Round-robin: by the time this check has run ``cut`` segments, a check earlier in the
                # order has run ``cut`` and a later one ``cut - 1``.
                spent = cut if checks.index(check) <= checks.index(current) else max(cut - 1, 0)
                spent = min(spent, grid.segments(check))
                rows = grid.row(check)[:spent]
                found = sum((finds or {}).get(check, ())[:spent]) if finds else sum(rows)
                tallies.append(Tally(check, spent, found, sum(rows)))
            built.append(State(point_id=f"{current.rsplit('.', 1)[-1]}.s{cut}", current=current,
                               tallies=tuple(tallies)))
    return tuple(built)


def contrast_indicates(grid: Grid, state: State) -> frozenset[str]:
    """What the CONTRAST brief's figures indicate, read as if they were the real ones.

    The contrast swaps two checks' figures, so the indicated option is what those figures point at,
    computed from them and not from the grid's own tail. A contrast that indicates the same option as
    the plain brief tests nothing: the figures moved and what they say did not.
    """

    swapped = contrast_of(state)
    scores = {option: (0 if check_of_option(swapped, option) is None
                       else swapped.tally_of(check_of_option(swapped, option)).real_classes)
              for option in options_of(swapped)}
    best = max(scores.values())
    if best == 0:
        return frozenset({STOP})
    return frozenset(option for option, score in scores.items() if score == best)


def plain_indicates(state: State) -> frozenset[str]:
    """What the plain brief's own figures indicate, by the same reading, for the comparison above."""

    scores = {option: (0 if check_of_option(state, option) is None
                       else state.tally_of(check_of_option(state, option)).real_classes)
              for option in options_of(state)}
    best = max(scores.values())
    if best == 0:
        return frozenset({STOP})
    return frozenset(option for option, score in scores.items() if score == best)


def contrast_flips(grid: Grid, state: State) -> bool:
    """Whether the contrast changes what the figures indicate. DEC-4 is measured only where it does."""

    return contrast_indicates(grid, state) != plain_indicates(state)


# ------------------------------------------------------------------------------------------------
# The campaign comparison: a function of six numbers, and the model asked to compute it
# ------------------------------------------------------------------------------------------------


#: The campaign's option set: its five rules, and running the shape again unchanged. The ids are the
#: rules' own ``rule_id`` values, so a reply can be compared with what ``campaign.decide`` returns
#: without a translation table in between.
UNCHANGED = "run-again-unchanged"


@dataclass(frozen=True)
class CampaignState:
    """The six numbers a campaign round decides on, and the three facts about the manifest it reads."""

    state_id: str
    format_failures: int
    drops: int
    ran: int
    escaped_breaks: int
    multi_part_pairs: int
    cells_in_grid: int
    cells_executed: int
    duplicates: int
    stop_reason: str
    in_fields_form: bool
    carries_break_instruction: bool
    carries_one_change_instruction: bool

    def __post_init__(self) -> None:
        if self.cells_executed > self.cells_in_grid:
            raise MiniError("MINI_COLLAPSE_CLASS_INVALID",
                            f"{self.state_id}: {self.cells_executed} cells run of "
                            f"{self.cells_in_grid} in the grid")
        if self.escaped_breaks > self.ran or self.multi_part_pairs > self.ran:
            raise MiniError("MINI_COLLAPSE_CLASS_INVALID",
                            f"{self.state_id}: more rows described than the {self.ran} the kernel ran")


def _reading_of(state: CampaignState) -> Any:
    """A real ``RunReading`` carrying these numbers, so the rules see the type they were written for."""

    from creib.forge.mini.report import ExecutionRow, RunReading

    rows: list[ExecutionRow] = []
    for index in range(state.ran):
        escaped = index < state.escaped_breaks
        multi = index < state.multi_part_pairs
        source = "a\\nb" if escaped else ("a\nb\nc\nd" if multi else "a")
        rewritten = "a\\nz" if escaped else ("z\ny\nx\nw" if multi else "z")
        rows.append(ExecutionRow(cycle=1, proposal=f"p{index}", kernel="open:m.f", transform="pair",
                                 executed="unchanged", before="a", after="a", expect="moves",
                                 as_expected=False, detail="", cell=f"c{index}", source=source,
                                 rewritten=rewritten))
    grid = tuple(f"c{index}" for index in range(state.cells_in_grid))
    return RunReading(
        root="", run_id="", manifest_id="", responder_id="", ended=True, cycles_completed=1,
        stop_reason=state.stop_reason, proposals=state.ran, calls_refused=0, drops=state.drops,
        format_failures=state.format_failures,
        executed={"unchanged": state.ran, "duplicate": state.duplicates},
        standings={}, columns={}, readings={}, executions=tuple(rows), verdicts=(),
        cells_in_grid=grid, cells_assigned=grid, cells_attempted=grid,
        cells_executed=grid[:state.cells_executed])


def _manifest_of(state: CampaignState) -> dict[str, Any]:
    """A manifest carrying only what the rules read of one: its form and the sentences it holds."""

    from creib.forge.mini.campaign import _ONE_CHANGE, _REAL_BREAKS

    instructions: list[str] = []
    if state.carries_break_instruction:
        instructions.append(_REAL_BREAKS)
    if state.carries_one_change_instruction:
        instructions.append(_ONE_CHANGE)
    kinds: list[dict[str, Any]] = [{
        "kind_id": "mini.pair-proposal.reading.v1", "title": "Proposal",
        "instruction": "propose a pair." + "".join(instructions),
        "input_ports": [], "output_port": {"port_id": "out", "produces_kind": "mini.pair-proposal.reading.v1"},
    }]
    if state.in_fields_form:
        from creib.forge.mini.campaign import LONG_FIELDS

        kinds[0]["optional_fields"] = list(LONG_FIELDS)
    return {"manifest_id": "mini.campaign.state", "kinds": kinds,
            "stages": [{"stage_id": "propose", "kind_id": "mini.pair-proposal.reading.v1", "ports": []},
                       {"stage_id": "end", "end": True}],
            "cycles": {"max_cycles": 1}}


def rule_that_fires(state: CampaignState) -> str:
    """The first rule the campaign fires on these numbers, or :data:`UNCHANGED` when none does.

    This calls ``creib.forge.mini.campaign.decide`` rather than restating its rules, so the key of the
    comparison is the machine's own answer and cannot drift from it.
    """

    from creib.forge.mini.campaign import decide

    decision = decide("shape", _reading_of(state), _manifest_of(state))
    return decision.rules_fired[0] if decision.rules_fired else UNCHANGED


def campaign_options() -> tuple[str, ...]:
    """Every option a campaign decision may take, in the order the rules are tried."""

    from creib.forge.mini.campaign import RULES

    return tuple(rule.rule_id for rule in RULES) + (UNCHANGED,)


CAMPAIGN_TASK = (
    "A loop has just finished a round. It proposed pairs of texts, a translator turned each into "
    "something a machine could run, and the machine ran what it could. You are deciding what the NEXT "
    "round should change -- one thing, or nothing.\n\n"
    "These are the only things that can be changed, and each is worth doing only when the numbers say "
    "so. If more than one looks warranted, choose the one that is most pressing."
)


def _campaign_figures(state: CampaignState) -> str:
    return "\n".join([
        "## What the round did", "",
        f"- the machine ran {state.ran} pair(s)",
        f"- {state.format_failures} reply/replies were refused for not carrying the shape asked for",
        f"- {state.drops} reply/replies were dropped before anything could read them",
        f"- {state.escaped_breaks} of the pairs it ran carried the two characters backslash and n "
        "where a line break belonged",
        f"- {state.multi_part_pairs} of the pairs it ran differed in more than one line",
        f"- the round had {state.cells_in_grid} cell(s) of its grid to cover and reached "
        f"{state.cells_executed} of them",
        f"- the machine was handed {state.duplicates} pair(s) it had already run",
        f"- the round ended because: {state.stop_reason}",
        "",
        "## How the round is set up now", "",
        f"- the long texts are {'separate fields of the reply' if state.in_fields_form else 'nested inside one string of the reply'}",
        f"- the proposer {'has' if state.carries_break_instruction else 'has not'} been told to write real line breaks",
        f"- the proposer {'has' if state.carries_one_change_instruction else 'has not'} been told to change one thing per pair",
    ])


CAMPAIGN_OPTION_TEXT: dict[str, str] = {
    "fields-form": "move the long texts out of the nested string and make them separate fields of the reply",
    "real-line-breaks": "tell the proposer to write real line breaks instead of the two characters backslash and n",
    "one-change-per-pair": "tell the proposer to change exactly one thing between the two texts of a pair",
    "cover-the-grid": "raise the number of cycles so the cells the round never reached can be reached",
    "space-exhausted": "stop this shape: it has nothing left to run",
    UNCHANGED: "change nothing and run the same round again",
}


def campaign_brief(state: CampaignState, variant: str) -> str:
    """One campaign state, put one of the same six ways."""

    if variant not in BRIEFS:
        raise MiniError("MINI_COLLAPSE_CLASS_INVALID",
                        f"unknown brief: {variant!r}; the briefs are {BRIEFS}")
    options = ["## The options, and there are no others", ""]
    for option in campaign_options():
        options.append(f"- `{option}` -- {CAMPAIGN_OPTION_TEXT[option]}")
    option_block = "\n".join(options)
    figures = _campaign_figures(state)
    if variant == CONTRAST:
        figures = _campaign_figures(campaign_contrast_of(state))
    blocks = [CAMPAIGN_TASK, figures, option_block, INSTRUCTION]
    if variant == ABLATED:
        blocks = [CAMPAIGN_TASK, option_block, INSTRUCTION]
    if variant == REORDERED:
        blocks = [option_block, figures, CAMPAIGN_TASK, INSTRUCTION]
    if variant == RELABELLED:
        # There is nothing to rename here: the options are the changes themselves and the figures are
        # numbers. Renaming would have to change the words that say what an option does, which is
        # content. The brief is therefore the plain one, and the pairing is recorded as unavailable.
        blocks = [CAMPAIGN_TASK, figures, option_block, INSTRUCTION]
    return "\n\n".join(blocks) + "\n"


def campaign_contrast_of(state: CampaignState) -> CampaignState:
    """The same brief with another declared state's numbers in it: the next one, in order, wrapping.

    Flipping every knob at once was the first version of this and it made seven of the eight contrasts
    fire the same rule, so a model that always named that rule would have looked sensitive to content. A
    rotation through the declared states spreads the key by construction: the contrast of the state that
    fires rule *n* fires whatever the next state fires, and the options and their wording do not move.
    """

    declared = campaign_states()
    for index, candidate in enumerate(declared):
        if candidate.state_id == state.state_id:
            partner = declared[(index + 1) % len(declared)]
            return CampaignState(
                state_id=state.state_id + ".contrast",
                format_failures=partner.format_failures, drops=partner.drops, ran=partner.ran,
                escaped_breaks=partner.escaped_breaks, multi_part_pairs=partner.multi_part_pairs,
                cells_in_grid=partner.cells_in_grid, cells_executed=partner.cells_executed,
                duplicates=partner.duplicates, stop_reason=partner.stop_reason,
                in_fields_form=partner.in_fields_form,
                carries_break_instruction=partner.carries_break_instruction,
                carries_one_change_instruction=partner.carries_one_change_instruction)
    raise MiniError("MINI_COLLAPSE_CLASS_INVALID",
                    f"{state.state_id} is not one of the declared campaign states, so it has no "
                    "contrast; the contrast is a rotation through the declared set")


def campaign_states() -> tuple[CampaignState, ...]:
    """Eight states: one that fires each of the five rules, one where none fires, two where two do."""

    def state(state_id: str, **changes: Any) -> CampaignState:
        base: dict[str, Any] = {"format_failures": 0, "drops": 0, "ran": 8, "escaped_breaks": 0,
                                "multi_part_pairs": 0, "cells_in_grid": 4, "cells_executed": 4,
                                "duplicates": 0, "stop_reason": "completed", "in_fields_form": True,
                                "carries_break_instruction": True,
                                "carries_one_change_instruction": True}
        base.update(changes)
        return CampaignState(state_id=state_id, **base)

    return (
        state("none-fires"),
        state("fields-form", ran=2, format_failures=3, drops=1, in_fields_form=False),
        state("real-line-breaks", escaped_breaks=3, carries_break_instruction=False),
        state("one-change-per-pair", multi_part_pairs=6, carries_one_change_instruction=False),
        state("cover-the-grid", cells_executed=1, stop_reason="cycle_cap"),
        state("space-exhausted", duplicates=3),
        state("breaks-and-one-change", escaped_breaks=3, multi_part_pairs=6,
              carries_break_instruction=False, carries_one_change_instruction=False),
        state("fields-and-breaks", ran=2, format_failures=3, escaped_breaks=2, in_fields_form=False,
              carries_break_instruction=False),
    )


# ------------------------------------------------------------------------------------------------
# What to add: asked, and not scored, for the reason the pre-registration gives
# ------------------------------------------------------------------------------------------------


#: The three steps block 2's arms took from the plain loop, in the order it took them, each with what it
#: does and what it adds to a segment's call count. The description is the content of the option; the id
#: is its form, so the ``relabelled`` brief can replace the id and leave the description word for word.
#:
#: The first step is two changes at once, and says so. That is not a simplification here: block 2's
#: ``F`` arm added the attacking seat and the carried brief together, so no run separates them, and a
#: brief that presented them as one tidy change would be describing an experiment nobody ran.
ADDITIONS: tuple[tuple[str, str, int], ...] = (
    ("the-attacking-seat-and-the-carried-brief",
     "a second seat that attacks the conjecture after the machine has run it, and a brief that tells "
     "the next segment what has already been run and not to repeat it (two changes, made together)",
     2),
    ("the-readings-port",
     "the attacking seat also being shown the second seat's own rendering of the conjecture, and not "
     "only the conjecture itself",
     0),
    ("the-warrant-schema",
     "the attacking seat naming, in a fixed shape, which artifact it attacks and on what ground, with "
     "what its attacks settle computed and shown to the next segment",
     0),
)

ADD_NOTHING = "add-nothing"


def _describes() -> dict[str, str]:
    return {name: description for name, description, _ in ADDITIONS}


def _costs() -> dict[str, int]:
    return {name: extra for name, _, extra in ADDITIONS}


@dataclass(frozen=True)
class AddState:
    """A loop as it stands: what is in it, what it costs a segment, and what it has produced."""

    state_id: str
    present: tuple[str, ...]
    segments: int
    finds: int
    real_classes: int
    calls_per_segment: int

    def __post_init__(self) -> None:
        declared = {name for name, _, _ in ADDITIONS}
        unknown = [name for name in self.present if name not in declared]
        if unknown:
            raise MiniError("MINI_COLLAPSE_CLASS_INVALID",
                            f"{self.state_id}: {unknown} is not one of the declared additions "
                            f"{sorted(declared)}")

    @property
    def absent(self) -> tuple[str, ...]:
        return tuple(name for name, _, _ in ADDITIONS if name not in self.present)


def add_options(state: AddState) -> tuple[str, ...]:
    """Adding nothing, and adding each thing the loop does not already have."""

    return (ADD_NOTHING,) + tuple(f"add-{name}" for name in state.absent)


def add_relabelling(state: AddState) -> dict[str, str]:
    """Addition to a neutral name, in the declared order. Descriptions are never touched."""

    if len(ADDITIONS) > len(NEUTRAL_NAMES):
        raise MiniError("MINI_COLLAPSE_CLASS_INVALID",
                        f"{len(ADDITIONS)} additions and only {len(NEUTRAL_NAMES)} neutral names")
    return {name: NEUTRAL_NAMES[index].replace("check", "part")
            for index, (name, _, _) in enumerate(ADDITIONS)}


def add_option_ids(state: AddState, variant: str) -> dict[str, str]:
    """The id shown for each option under one brief, so a reply can be read back."""

    if variant != RELABELLED:
        return {option: option for option in add_options(state)}
    names = add_relabelling(state)
    shown = {ADD_NOTHING: ADD_NOTHING}
    for name in state.absent:
        shown[f"add-{name}"] = f"add-{names[name]}"
    return shown


def add_contrast_of(state: AddState) -> AddState:
    """The same loop with what it has produced turned around, and nothing else moved.

    A loop that is finding something is a reason to leave it alone; a loop that has found nothing in
    the same number of segments is a reason to change something. So this is the content the decision is
    about, and the spend, the parts present and the wording of every option stay exactly as they were.
    """

    barren = state.real_classes > 0
    return AddState(state_id=state.state_id + ".contrast", present=state.present,
                    segments=state.segments,
                    finds=0 if barren else state.segments,
                    real_classes=0 if barren else state.segments,
                    calls_per_segment=state.calls_per_segment)


ADD_TASK = (
    "A loop is running the search described below. It writes a conjecture in prose, a second seat "
    "renders it as something a machine can run, and the machine runs it. What it is looking for is a "
    "pair of reply texts that a check answers the SAME on, where the check's own documented rule "
    "requires it to answer differently.\n\n"
    "You are deciding whether to add one thing to that loop, or nothing. Every call costs money, so "
    "adding something is worth doing only if it will find more than the calls it spends."
)


def _add_figures(state: AddState, names: Mapping[str, str]) -> str:
    lines = ["## The loop as it stands", ""]
    if state.present:
        for name in state.present:
            lines.append(f"- it already has {names.get(name, name)}: "
                         + _describes()[name])
    else:
        lines.append("- it has none of the things below: it writes a conjecture, renders it, runs it")
    lines.extend([
        f"- it costs {state.calls_per_segment} model call(s) per segment",
        f"- in {state.segments} segment(s) it has found {state.finds} pair(s), which are "
        f"{state.real_classes} distinct way(s) of breaking a check",
    ])
    return "\n".join(lines)


def _add_options_block(state: AddState, variant: str) -> str:
    shown = add_option_ids(state, variant)
    lines = ["## The options, and there are no others", "",
             f"- `{shown[ADD_NOTHING]}` -- leave the loop as it is and run another segment"]
    for name in state.absent:
        extra = _costs()[name]
        cost = (f" This adds {extra} model call(s) to every segment." if extra
                else " This adds no model call to a segment.")
        lines.append(f"- `{shown['add-' + name]}` -- {_describes()[name]}.{cost}")
    return "\n".join(lines)


def add_brief(state: AddState, variant: str) -> str:
    """One what-to-add decision, put one of the same six ways."""

    if variant not in BRIEFS:
        raise MiniError("MINI_COLLAPSE_CLASS_INVALID",
                        f"unknown brief: {variant!r}; the briefs are {BRIEFS}")
    shown = add_contrast_of(state) if variant == CONTRAST else state
    names = (add_relabelling(state) if variant == RELABELLED
             else {name: name for name, _, _ in ADDITIONS})
    figures = _add_figures(shown, names)
    options = _add_options_block(state, variant)
    blocks = [ADD_TASK, figures, options, INSTRUCTION]
    if variant == ABLATED:
        blocks = [ADD_TASK, options, INSTRUCTION]
    if variant == REORDERED:
        blocks = [options, figures, ADD_TASK, INSTRUCTION]
    return "\n\n".join(blocks) + "\n"


def add_states(segments: int = 6, finds: int = 5, real_classes: int = 3) -> tuple[AddState, ...]:
    """One state per amount already added, with the plain loop's own figures from the grid.

    The loop with everything already in it is left out: its only option is to add nothing, and a
    decision with one option is not a decision.
    """

    ladder = [(), (ADDITIONS[0][0],), (ADDITIONS[0][0], ADDITIONS[1][0])]
    return tuple(
        AddState(state_id=f"loop-with-{len(present)}" if present else "plain-loop", present=present,
                 segments=segments, finds=finds, real_classes=real_classes,
                 calls_per_segment=3 + sum(_costs()[name] for name in present))
        for present in ladder)
