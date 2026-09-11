"""Loud alarms for the failure modes this repository has actually paid for.

Named ``alarms`` and not ``signals``: ``signals.py`` is mini's attention and stop-condition layer,
which steers a run from inside it. These are about the run's machinery being unfit to measure
anything, which is a different thing and belongs in a different file. (The first draft of this module
was written straight over ``signals.py`` without looking at it first.)

Every defect in ``docs/mini/ERRATA.md`` was found after runs had been spent on it: a seat the tool
did not register cost thirty-six runs and then three more; a criticism reading nothing but refusals
cost two whole blocks of a null that meant nothing; a translator writing an artifact id where a
function path belonged cost nine executions of eleven. In each case the record said so at the first
segment and nobody was looking.

So each known mode gets a named signal computed from one segment's record, with a severity that says
whether an arm should stop. A signal is a measurement, never a verdict about the subject: it says the
machinery is not in a state to measure anything, which is a different claim from the subject being
uninteresting, and conflating those is what produced the withdrawn conclusions in the errata.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

#: An artifact id rendered beside an artifact, which a seat asked for "an id" may hand back instead
#: of the thing actually wanted. Cost nine of eleven executions in CREATIVITY-ARMS-1 v1.
_ARTIFACT_ID = re.compile(r"^[0-9a-f]{12,64}$")

FATAL, WARN = "fatal", "warn"


@dataclass(frozen=True)
class Alarm:
    """One named thing that is wrong with the machinery, not with the subject."""

    name: str
    severity: str
    detail: str

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.name}: {self.detail}"


def _executions(records: Sequence[Any], blobs: Any, kind_prefix: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for record in records:
        if not str(record["kind_id"]).startswith(kind_prefix):
            continue
        try:
            out.extend(json.loads(blobs.get(str(record["commitments_ref"])).decode("utf-8")).get("executions", []))
        except (ValueError, TypeError):
            continue
    return out


def alarms_for(root: Path, previous_brief: str | None = None, brief: str | None = None) -> list[Alarm]:
    """Every signal one finished segment raises. Cheap: it reads the record and calls no model."""

    from .blindspot import CRITICISM_KIND_PREFIX, PAIR_EXECUTION_PREFIX
    from .common import RUN_HEADER_DOMAIN, content_id
    from .log import BlobStore, replay
    from creib.strict_json import load_strict

    found: list[Alarm] = []
    log = root / "log.jsonl"
    if not log.is_file():
        return [Alarm("SEGMENT_NEVER_STARTED", FATAL, f"{root} has no log")]
    if "RUN_ENDED" not in log.read_text(encoding="utf-8"):
        # The runner used to step over this in silence, so F/s01 produced nothing and F/s02's carry
        # held only s00: the arm whose whole point is accumulation did not accumulate.
        return [Alarm("SEGMENT_DIED", FATAL, f"{root.name} never reached RUN_ENDED")]

    state = replay(log, content_id(RUN_HEADER_DOMAIN, load_strict(root / "run-header.json")))
    blobs = BlobStore(root / "blobs")
    records = [state.artifacts[key] for key in state.artifact_order]
    rows = _executions(records, blobs, PAIR_EXECUTION_PREFIX)

    for entry in rows:
        kernel = str(entry.get("kernel", ""))
        if _ARTIFACT_ID.match(kernel):
            found.append(Alarm("ID_WHERE_A_NAME_BELONGS", FATAL,
                                f"a proposal's kernel field is {kernel[:16]!r}, which is an artifact id, "
                                "not a function; the field's name is ambiguous in its own context"))
            break

    if rows:
        ran = [e for e in rows if e.get("executed") in ("moved", "unchanged")]
        if len(ran) * 2 < len(rows):
            found.append(Alarm("LOOP_STARVED", FATAL,
                                f"{len(rows) - len(ran)} of {len(rows)} executions did not run, so a critic "
                                "reads refusals rather than results and any comparison downstream measures "
                                "the machinery"))
    else:
        found.append(Alarm("NOTHING_EXECUTED", FATAL, "the segment ran no pair at all"))

    refused = sum(1 for line in (root / "log.jsonl").read_text(encoding="utf-8").splitlines()
                  if '"FORMAT_FAILURE"' in line)
    submitted = sum(1 for line in (root / "log.jsonl").read_text(encoding="utf-8").splitlines()
                    if '"ARTIFACT_SUBMITTED"' in line)
    if refused and refused >= submitted:
        # CON-FORMAT-KILLS-RUN: a stricter form and a shorter run are one knob with two effects, so
        # an arm dying young looks worse for a reason that is not what it was testing.
        found.append(Alarm("FORMAT_FAILURES_RISING", FATAL,
                           f"{refused} submissions refused against {submitted} accepted; a run this "
                           "close to its failure tolerance ends on the form rather than on the subject"))
    elif refused:
        found.append(Alarm("FORMAT_FAILURES_RISING", WARN,
                           f"{refused} submissions refused against {submitted} accepted"))

    criticisms = [r for r in records if str(r["kind_id"]).startswith(CRITICISM_KIND_PREFIX)]
    unparsed = 0
    for record in criticisms:
        try:
            parsed = json.loads(blobs.get(str(record["commitments_ref"])).decode("utf-8"))
        except (ValueError, TypeError):
            parsed = None
        if not isinstance(parsed, dict):
            unparsed += 1
    if criticisms and unparsed == len(criticisms):
        found.append(Alarm("COMMITMENTS_ARE_PROSE", WARN,
                            f"all {len(criticisms)} criticism commitments failed to parse; a commitment "
                            "asked for in prose and not enforced by a format check is usually prose"))

    if previous_brief is not None and brief is not None and previous_brief == brief and previous_brief:
        found.append(Alarm("CARRY_STALLED", WARN,
                            "this segment's brief is byte-identical to the previous one's, so the "
                            "install map carried nothing new"))
    return found


def preflight(manifest: Path, repo_root: Path) -> list[Alarm]:
    """Everything checkable before a single model call is paid for.

    The seat check runs in a FRESH interpreter, because registration is a process-global side effect
    and asking in this one answers a question about what this process imported (M26).
    """

    import subprocess
    import sys

    probe = (
        "import importlib.util, json, sys\n"
        "from pathlib import Path\n"
        "root = Path(sys.argv[1]); sys.path.insert(0, str(root / 'src'))\n"
        "spec = importlib.util.spec_from_file_location('rm', root / 'tools' / 'run_mini.py')\n"
        "m = importlib.util.module_from_spec(spec); sys.modules['rm'] = m; spec.loader.exec_module(m)\n"
        "from creib.forge.mini.machines import registered_machine_seats\n"
        "print(json.dumps(sorted(s.kind_id for s in registered_machine_seats())))\n"
    )
    finished = subprocess.run([sys.executable, "-c", probe, str(repo_root)],
                              capture_output=True, text=True)
    if finished.returncode != 0:
        return [Alarm("TOOL_WILL_NOT_IMPORT", FATAL, finished.stderr.strip()[-300:])]
    registered = set(json.loads(finished.stdout.strip().splitlines()[-1]))

    body = json.loads(manifest.read_text(encoding="utf-8"))
    wanted = {str(stage.get("kind_id")) for stage in body.get("stages", [])
              if stage.get("seat") == "machine" and stage.get("kind_id")}
    missing = sorted(wanted - registered)
    if missing:
        return [Alarm("SEAT_NOT_REGISTERED_BY_THE_TOOL", FATAL,
                       f"{manifest} names {missing}, which the command line does not register; the "
                       "tests may import it and the tool does not (M25, M26)")]
    return []
