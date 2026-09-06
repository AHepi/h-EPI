"""SMF-0.5 task-conformance pilot: criticism-first checks of form filling by LLMs.

The package points the repository's method (content-bound sources, per-field
obligations, rival readings, adversarial test families, plural C/A/T/S
failure routing, human triage, no confirmation) at a configurable task: an
LLM must fill a form from a case document.  A different form, instruction
set, corpus, or model list is a configuration change.

Nothing exported here confirms a model.  Run records are always
``UNRESOLVED`` and routed to human triage; a variant with no live loci is
merely unrefuted for that variant.
"""

from __future__ import annotations

from .common import CONFORMANCE_SCHEMA_DIR, LOCUS_VALUES, conformance_catalog
from .corpus import Case, Corpus, Oracle, load_corpus, parse_corpus
from .executor import (
    CannedExecutor,
    ChatRequest,
    ChatResponse,
    FakeExecutor,
    ModelExecutor,
    OllamaChatExecutor,
    ReplayExecutor,
    response_from_content,
)
from .families import (
    FAMILY_GENERATORS,
    TEST_FAMILIES,
    ExpectationKind,
    Family,
    Plan,
    Variant,
    materialize_round_trip,
    plan,
    render_round_trip_document,
)
from .oracle import FieldVerdict, Scoring, score
from .prompt import build_chat_request
from .records import (
    ObservationRecord,
    RunRecord,
    load_observation,
    load_observation_directory,
    load_run,
    publish_record,
)
from .report import build_report, render_markdown
from .routing import ROUTING_TABLE, LiveLocus, Routing, route
from .runner import RunResult, run_pilot, select_variants
from .spec import Obligation, PilotConfig, TaskSpec, load_pilot_config

__all__ = [
    "CONFORMANCE_SCHEMA_DIR",
    "LOCUS_VALUES",
    "conformance_catalog",
    "Case",
    "Corpus",
    "Oracle",
    "load_corpus",
    "parse_corpus",
    "CannedExecutor",
    "ChatRequest",
    "ChatResponse",
    "FakeExecutor",
    "ModelExecutor",
    "OllamaChatExecutor",
    "ReplayExecutor",
    "response_from_content",
    "FAMILY_GENERATORS",
    "TEST_FAMILIES",
    "ExpectationKind",
    "Family",
    "Plan",
    "Variant",
    "materialize_round_trip",
    "plan",
    "render_round_trip_document",
    "FieldVerdict",
    "Scoring",
    "score",
    "build_chat_request",
    "ObservationRecord",
    "RunRecord",
    "load_observation",
    "load_observation_directory",
    "load_run",
    "publish_record",
    "build_report",
    "render_markdown",
    "ROUTING_TABLE",
    "LiveLocus",
    "Routing",
    "route",
    "RunResult",
    "run_pilot",
    "select_variants",
    "Obligation",
    "PilotConfig",
    "TaskSpec",
    "load_pilot_config",
]
