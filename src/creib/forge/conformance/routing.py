"""Plural failure routing: every criticism names the loci that could be at fault.

The routing table below maps a trigger (a response verdict, a field verdict,
or a comparison outcome) to a set of live loci from the C/A/T/S vocabulary:

    CANDIDATE  the model under test
    AUXILIARY  prompt, format plumbing, instruction wording, harness settings
    TEST       the oracle, the corruption template, the probe design
    SCOPE      whether the case or endpoint is inside the declared scope

Table (trigger -> loci; family restrictions in brackets):

    TRANSPORT_ERROR            -> AUXILIARY, SCOPE
    EMPTY_RESPONSE             -> CANDIDATE, AUXILIARY
    TRUNCATED                  -> CANDIDATE, AUXILIARY
    INVALID_JSON               -> CANDIDATE, AUXILIARY
    NOT_AN_OBJECT              -> CANDIDATE, AUXILIARY
    REFUSAL_SUSPECTED          -> CANDIDATE, AUXILIARY, TEST
    PREREQUISITE_UNAVAILABLE   -> AUXILIARY, TEST
    EXTRA_FIELD                -> CANDIDATE, AUXILIARY
    MISSING_REQUIRED           -> CANDIDATE, AUXILIARY
    FORMAT_NOT_ENFORCED        -> TEST
    MISMATCH and constraint violations:
        default                -> CANDIDATE, TEST
        [RIVAL_SUBSTITUTION]   -> CANDIDATE, AUXILIARY, TEST
        [SEMANTIC_ROLE_TWIN]   -> CANDIDATE, TEST
        [SUBSTRATE_SWAP]       -> CANDIDATE, SCOPE, TEST
        [BOUNDARY_SHIFT]       -> CANDIDATE, TEST, SCOPE
        [ROUND_TRIP]           -> CANDIDATE, AUXILIARY, TEST
    IDENTICAL_TO_BASELINE [NEGATION]        -> CANDIDATE, AUXILIARY, SCOPE
        (subsumes the field-level mismatch triggers of the same observation)
    CONTROL_ACCEPTED [NON_VACUITY]          -> TEST, AUXILIARY
    CONTROL_REJECTED [NON_VACUITY]          -> TEST
    DEPENDENCE_CHANGED [IMPORT_DEPENDENCY]  -> AUXILIARY, SCOPE
    DEPENDENCE_UNCHANGED [IMPORT_DEPENDENCY]-> AUXILIARY, TEST, SCOPE

A model-involved variant never routes to a single locus.  The only empty set
is a variant whose declared expectation was met everywhere; that is recorded
as ``unrefuted_for_variant`` and is not confirmation of anything.  The route
is always ``AWAITING_HUMAN_TRIAGE``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from creib.errors import PolicyViolation, RecordError

from .common import (
    LOCUS_VALUES,
    ROUTE_AWAITING_HUMAN_TRIAGE,
    array_value,
    boolean,
    object_value,
    optional_boolean,
    text,
)
from .families import ExpectationKind, Family, Variant
from .oracle import Scoring


_CRITICISM_FIELD_VERDICTS = frozenset(
    {"MISMATCH", "TYPE_VIOLATION", "PATTERN_VIOLATION", "ENUM_VIOLATION", "LENGTH_VIOLATION", "UNEXPECTED_PRESENT", "SCHEMA_INVALID"}
)
_STRUCTURAL_FIELD_VERDICTS = frozenset({"EXTRA_FIELD", "MISSING_REQUIRED"})
TRIGGERS: tuple[str, ...] = (
    "TRANSPORT_ERROR",
    "EMPTY_RESPONSE",
    "TRUNCATED",
    "INVALID_JSON",
    "NOT_AN_OBJECT",
    "REFUSAL_SUSPECTED",
    "PREREQUISITE_UNAVAILABLE",
    "MISMATCH",
    "MISSING_REQUIRED",
    "EXTRA_FIELD",
    "TYPE_VIOLATION",
    "PATTERN_VIOLATION",
    "ENUM_VIOLATION",
    "LENGTH_VIOLATION",
    "UNEXPECTED_PRESENT",
    "SCHEMA_INVALID",
    "IDENTICAL_TO_BASELINE",
    "CONTROL_ACCEPTED",
    "CONTROL_REJECTED",
    "DEPENDENCE_CHANGED",
    "DEPENDENCE_UNCHANGED",
    "FORMAT_NOT_ENFORCED",
)


@dataclass(frozen=True)
class LiveLocus:
    locus: str
    reason: str

    def to_dict(self) -> dict[str, object]:
        return {"locus": self.locus, "reason": self.reason}


@dataclass(frozen=True)
class RoutingRule:
    trigger: str
    families: frozenset[Family] | None
    loci: tuple[tuple[str, str], ...]

    def applies(self, trigger: str, family: Family) -> bool:
        return trigger == self.trigger and (self.families is None or family in self.families)


def _rule(trigger: str, loci: tuple[tuple[str, str], ...], families: tuple[Family, ...] | None = None) -> RoutingRule:
    return RoutingRule(trigger=trigger, families=None if families is None else frozenset(families), loci=loci)


_CANDIDATE_MISMATCH = ("CANDIDATE", "The output does not meet the declared expectation for at least one field.")
_TEST_ORACLE = ("TEST", "The oracle is a non-final proposal and may misread the case or the form.")
_MISMATCH_TRIGGERS = ("MISMATCH", "TYPE_VIOLATION", "PATTERN_VIOLATION", "ENUM_VIOLATION", "LENGTH_VIOLATION", "UNEXPECTED_PRESENT", "SCHEMA_INVALID")
_MISMATCH_FAMILY_LOCI: dict[Family, tuple[tuple[str, str], ...]] = {
    Family.RIVAL_SUBSTITUTION: (
        ("CANDIDATE", "The output did not match the oracle for the appended rival rule; ignoring or overriding the rule is one reading of this."),
        ("AUXILIARY", "The appended rival sentence may be phrased so that the model cannot apply it."),
        _TEST_ORACLE,
    ),
    Family.SEMANTIC_ROLE_TWIN: (
        ("CANDIDATE", "At least one value did not match its swapped label; following position rather than label is one reading of this."),
        ("TEST", "The position swap may itself alter how the labels read; the probe may be confounded."),
    ),
    Family.SUBSTRATE_SWAP: (
        ("CANDIDATE", "On this substrate at least one field missed its oracle; sensitivity to the rendering is one reading of this."),
        ("SCOPE", "The alternative substrate may fall outside the declared input scope."),
        _TEST_ORACLE,
    ),
    Family.BOUNDARY_SHIFT: (
        ("CANDIDATE", "The boundary case was not filled as the oracle expects."),
        ("TEST", "The oracle may be wrong on this edge case; its status is recorded per field."),
        ("SCOPE", "The boundary case may lie outside what the form and instructions can express."),
    ),
    Family.ROUND_TRIP: (
        ("CANDIDATE", "The model's output is not stable under a re-rendering of its own output."),
        ("AUXILIARY", "The fixed prose rendering template may lose or distort information."),
        ("TEST", "The round-trip expectation is derived from the model's own output and is provisional."),
    ),
}

ROUTING_TABLE: tuple[RoutingRule, ...] = (
    _rule(
        "TRANSPORT_ERROR",
        (
            ("AUXILIARY", "The executor, network, or endpoint failed before any model output was observed."),
            ("SCOPE", "The endpoint or model may be outside the declared scope (unavailable, renamed, or rate-limited)."),
        ),
    ),
    _rule(
        "EMPTY_RESPONSE",
        (
            ("CANDIDATE", "The model returned no content."),
            ("AUXILIARY", "The request plumbing (format, think, options) may have suppressed output."),
        ),
    ),
    _rule(
        "TRUNCATED",
        (
            ("CANDIDATE", "The model did not finish within the output budget."),
            ("AUXILIARY", "The output length limit is a harness setting."),
        ),
    ),
    _rule(
        "INVALID_JSON",
        (
            ("CANDIDATE", "The model did not return parseable JSON."),
            ("AUXILIARY", "The prompt or the server-side format constraint may not have been applied."),
        ),
    ),
    _rule(
        "NOT_AN_OBJECT",
        (
            ("CANDIDATE", "The model returned JSON that is not an object."),
            ("AUXILIARY", "The prompt or the server-side format constraint may not have been applied."),
        ),
    ),
    _rule(
        "REFUSAL_SUSPECTED",
        (
            ("CANDIDATE", "The model appears to have declined the task."),
            ("AUXILIARY", "The prompt framing may have provoked a refusal."),
            ("TEST", "The refusal phrase list is a heuristic import and may misclassify prose."),
        ),
    ),
    _rule(
        "PREREQUISITE_UNAVAILABLE",
        (
            ("AUXILIARY", "A prerequisite observation (the baseline output) was unusable, so the chain could not proceed."),
            ("TEST", "The chained test could not be constructed as designed."),
        ),
    ),
    _rule(
        "EXTRA_FIELD",
        (
            ("CANDIDATE", "The model emitted a key the form schema does not define."),
            ("AUXILIARY", "The format constraint or prompt did not prevent extra keys."),
        ),
    ),
    _rule(
        "MISSING_REQUIRED",
        (
            ("CANDIDATE", "The model omitted a required key."),
            ("AUXILIARY", "The format constraint or prompt did not enforce the required list."),
        ),
    ),
    _rule(
        "FORMAT_NOT_ENFORCED",
        (("TEST", "The test assumed server-side schema enforcement; this observation shows it was not applied."),),
    ),
    *[
        _rule(trigger, loci, (family,))
        for family, loci in _MISMATCH_FAMILY_LOCI.items()
        for trigger in _MISMATCH_TRIGGERS
    ],
    *[
        _rule(
            trigger,
            (_CANDIDATE_MISMATCH, _TEST_ORACLE),
            tuple(family for family in Family if family not in _MISMATCH_FAMILY_LOCI),
        )
        for trigger in _MISMATCH_TRIGGERS
    ],
    _rule(
        "IDENTICAL_TO_BASELINE",
        (
            ("CANDIDATE", "The output did not change when the formatting instruction was inverted; the instruction may be ignored."),
            ("AUXILIARY", "The schema pattern or prompt plumbing may dominate the instruction sentence."),
            ("SCOPE", "Formatting instruction-following may be outside what this model can be asked to do."),
        ),
        (Family.NEGATION,),
    ),
    _rule(
        "CONTROL_ACCEPTED",
        (
            ("TEST", "The oracle accepted a deliberately corrupted output; the check is vacuous for this corruption."),
            ("AUXILIARY", "The corruption template or the reference output may be misconfigured."),
        ),
        (Family.NON_VACUITY,),
    ),
    _rule(
        "CONTROL_REJECTED",
        (("TEST", "The oracle rejected the uncorrupted reference output; the oracle or the reference is wrong."),),
        (Family.NON_VACUITY,),
    ),
    _rule(
        "DEPENDENCE_CHANGED",
        (
            ("AUXILIARY", "The output depends on the removed sentence as declared; whether that dependence is wanted is a question about the instruction, not a refutation of the model."),
            ("SCOPE", "Declaring a sentence load-bearing is a scope decision about the instructions."),
        ),
        (Family.IMPORT_DEPENDENCY,),
    ),
    _rule(
        "DEPENDENCE_UNCHANGED",
        (
            ("AUXILIARY", "The sentence declared load-bearing had no observable effect on this case."),
            ("TEST", "The removal probe may be confounded by the schema or by other sentences."),
            ("SCOPE", "This case may not exercise the removed sentence at all."),
        ),
        (Family.IMPORT_DEPENDENCY,),
    ),
)


@dataclass(frozen=True)
class Routing:
    live_loci: tuple[LiveLocus, ...]
    route: str
    unrefuted_for_variant: bool
    triggers: tuple[str, ...]
    format_enforced_by_server: bool | None

    def to_dict(self) -> dict[str, object]:
        return {
            "live_loci": [locus.to_dict() for locus in self.live_loci],
            "route": self.route,
            "unrefuted_for_variant": self.unrefuted_for_variant,
            "triggers": list(self.triggers),
            "format_enforced_by_server": self.format_enforced_by_server,
        }

    @property
    def loci(self) -> tuple[str, ...]:
        return tuple(locus.locus for locus in self.live_loci)


def routing_from_dict(raw: Any, where: str = "routing") -> Routing:
    record = object_value(raw, where)
    loci: list[LiveLocus] = []
    for index, item in enumerate(array_value(record["live_loci"], f"{where}.live_loci")):
        entry = object_value(item, f"{where}.live_loci[{index}]")
        locus = text(entry["locus"], f"{where}.live_loci[{index}].locus")
        if locus not in LOCUS_VALUES:
            raise RecordError(f"{where}.live_loci[{index}].locus is not a known locus")
        loci.append(LiveLocus(locus=locus, reason=text(entry["reason"], f"{where}.live_loci[{index}].reason")))
    route = text(record["route"], f"{where}.route")
    if route != ROUTE_AWAITING_HUMAN_TRIAGE:
        raise PolicyViolation("routing route must be AWAITING_HUMAN_TRIAGE")
    triggers = tuple(text(item, f"{where}.triggers[{index}]") for index, item in enumerate(array_value(record["triggers"], f"{where}.triggers")))
    for trigger in triggers:
        if trigger not in TRIGGERS:
            raise RecordError(f"{where}.triggers has unknown trigger {trigger!r}")
    return Routing(
        live_loci=tuple(loci),
        route=route,
        unrefuted_for_variant=boolean(record["unrefuted_for_variant"], f"{where}.unrefuted_for_variant"),
        triggers=triggers,
        format_enforced_by_server=optional_boolean(record["format_enforced_by_server"], f"{where}.format_enforced_by_server"),
    )


def derive_triggers(variant: Variant, scoring: Scoring, *, format_sent: bool) -> tuple[str, ...]:
    """List the criticism triggers raised by one scoring, in a fixed order."""

    triggers: list[str] = []
    kind = variant.expectation_kind
    if scoring.response_verdict not in ("JSON_OBJECT", "NO_MODEL_CALL"):
        triggers.append(scoring.response_verdict)
        return tuple(triggers)
    if kind in (ExpectationKind.CONTROL_REJECT, ExpectationKind.CONTROL_ACCEPT):
        if kind is ExpectationKind.CONTROL_REJECT and scoring.all_match:
            triggers.append("CONTROL_ACCEPTED")
        if kind is ExpectationKind.CONTROL_ACCEPT and not scoring.all_match:
            triggers.append("CONTROL_REJECTED")
        return tuple(triggers)
    if kind is ExpectationKind.RECORD_DEPENDENCE:
        if scoring.changed_vs_baseline is None:
            triggers.append("PREREQUISITE_UNAVAILABLE")
        elif scoring.changed_vs_baseline:
            triggers.append("DEPENDENCE_CHANGED")
        else:
            triggers.append("DEPENDENCE_UNCHANGED")
        return tuple(triggers)
    field_triggers = list(scoring.verdict_kinds())
    if scoring.schema_valid is False and not any(t in _CRITICISM_FIELD_VERDICTS | _STRUCTURAL_FIELD_VERDICTS for t in field_triggers):
        field_triggers.append("SCHEMA_INVALID")
    triggers.extend(field_triggers)
    if format_sent and variant.model_call and any(t in _STRUCTURAL_FIELD_VERDICTS or t == "UNEXPECTED_PRESENT" for t in field_triggers):
        triggers.append("FORMAT_NOT_ENFORCED")
    if variant.family is Family.NEGATION and scoring.changed_vs_baseline is False:
        triggers.append("IDENTICAL_TO_BASELINE")
    if variant.family is Family.NEGATION and scoring.changed_vs_baseline is None:
        triggers.append("PREREQUISITE_UNAVAILABLE")
    return tuple(triggers)


def route(variant: Variant, scoring: Scoring, *, format_sent: bool = True) -> Routing:
    """Route one scoring to its plural live loci; never to a verdict about the model."""

    triggers = derive_triggers(variant, scoring, format_sent=format_sent)
    # An output identical to the baseline explains every field-level mismatch
    # of a NEGATION variant; the oracle (TEST) is then not a live locus.
    subsumed = frozenset(_MISMATCH_TRIGGERS) if "IDENTICAL_TO_BASELINE" in triggers else frozenset()
    reasons: dict[str, str] = {}
    for trigger in triggers:
        if trigger in subsumed:
            continue
        matched = False
        for rule in ROUTING_TABLE:
            if rule.applies(trigger, variant.family):
                matched = True
                for locus, reason in rule.loci:
                    reasons.setdefault(locus, reason)
        if not matched:
            raise RecordError(f"routing table has no rule for trigger {trigger!r} in family {variant.family.value}")
    live = tuple(LiveLocus(locus=locus, reason=reasons[locus]) for locus in LOCUS_VALUES if locus in reasons)
    if variant.model_call and len(live) == 1:
        raise PolicyViolation(
            f"model-involved variant {variant.variant_id} routed to a single locus {live[0].locus}"
        )
    format_enforced: bool | None = None
    if "FORMAT_NOT_ENFORCED" in triggers:
        format_enforced = False
    return Routing(
        live_loci=live,
        route=ROUTE_AWAITING_HUMAN_TRIAGE,
        unrefuted_for_variant=not triggers,
        triggers=triggers,
        format_enforced_by_server=format_enforced,
    )
