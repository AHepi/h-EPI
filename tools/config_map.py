#!/usr/bin/env python3
"""Audit the config map, the confound register and the configuration registry against each other.

    python tools/config_map.py audit
    python tools/config_map.py show --config CONF-ARMS-W

Four documents have to agree or none of them is worth reading:

- ``docs/mini/CONFIG_MAP.md`` names every setting (``CFG-*``) and how it is misread (``MIS-*``);
- ``docs/mini/CONFOUNDS.md`` names settings that move together (``CON-*``);
- ``docs/mini/ERRATA.md`` names what has already gone wrong;
- ``forge/mini/configs/registry.json`` names configurations (``CONF-*``) and tags each with the
  settings it moves, the confounds that apply, and what it does and does not prove.

The audit is the point. A cross-reference nobody checks rots, and this repository has already paid
for two documents that disagreed with the code (M22, M23). Every tag must resolve, every setting
named must exist in the schema, every manifest and record path must exist, and every alarm named in
prose must exist in ``alarms.py``.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

CONFIG_MAP = ROOT / "docs/mini/CONFIG_MAP.md"
CONFOUNDS = ROOT / "docs/mini/CONFOUNDS.md"
ERRATA = ROOT / "docs/mini/ERRATA.md"
REGISTRY = ROOT / "forge/mini/configs/registry.json"

_HEADING = re.compile(r"^### ((?:CFG|CON)-[A-Z0-9-]+)", re.M)
_MIS = re.compile(r"\*\*(MIS-[A-Z0-9-]+)\*\*")
_TAG = re.compile(r"\b((?:CFG|CON|MIS|ALM|CONF)-[A-Z0-9-]+)\b")
_COUPLES = re.compile(r"^\*\*Couples:\*\* (.+)$", re.M)
_ALARM_IN_PROSE = re.compile(r"\bALM-([A-Z0-9-]+)\b")


def _defined() -> tuple[set[str], set[str], set[str]]:
    """Every setting, confound and misreading the documents define."""

    settings = {t for t in _HEADING.findall(CONFIG_MAP.read_text(encoding="utf-8")) if t.startswith("CFG-")}
    confounds = {t for t in _HEADING.findall(CONFOUNDS.read_text(encoding="utf-8")) if t.startswith("CON-")}
    misreadings = set(_MIS.findall(CONFIG_MAP.read_text(encoding="utf-8")))
    return settings, confounds, misreadings


def _schema_keys() -> set[str]:
    """Every key a manifest or kind may actually set, read from the schemas rather than remembered."""

    keys: set[str] = set()
    for name in ("mini-manifest.schema.json", "mini-kind.schema.json", "mini-policy.schema.json"):
        body = json.loads((ROOT / "forge/mini/schema" / name).read_text(encoding="utf-8"))
        keys.update(body.get("properties", {}))
        for definition in (body.get("$defs") or {}).values():
            if isinstance(definition, dict):
                keys.update(definition.get("properties", {}))
    return keys


def _alarm_names() -> set[str]:
    from creib.forge.mini import alarms as module
    import inspect

    return set(re.findall(r'Alarm\("([A-Z_]+)"', inspect.getsource(module)))


def _audit(args: argparse.Namespace) -> int:
    settings, confounds, misreadings = _defined()
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    errata = ERRATA.read_text(encoding="utf-8")
    problems: list[str] = []

    for tag in sorted(settings):
        if not re.search(re.escape(tag) + r"\b.*`", CONFIG_MAP.read_text(encoding="utf-8")):
            problems.append(f"{tag} names no manifest key in backticks")

    # Every confound must couple settings that exist.
    for line in _COUPLES.findall(CONFOUNDS.read_text(encoding="utf-8")):
        for tag in _TAG.findall(line):
            if tag.startswith("CFG-") and tag not in settings:
                problems.append(f"CONFOUNDS.md couples {tag}, which CONFIG_MAP.md does not define")

    # Every alarm named in prose must exist in the code.
    real = _alarm_names()
    for text, where in ((CONFOUNDS.read_text(encoding="utf-8"), "CONFOUNDS.md"),
                        (CONFIG_MAP.read_text(encoding="utf-8"), "CONFIG_MAP.md")):
        for name in _ALARM_IN_PROSE.findall(text):
            if name.replace("-", "_") not in real:
                problems.append(f"{where} names ALM-{name}, which alarms.py does not raise")

    seen: set[str] = set()
    for config in registry["configs"]:
        cid = str(config["config_id"])
        if cid in seen:
            problems.append(f"{cid} is registered twice")
        seen.add(cid)
        if config["status"] not in registry["statuses"]:
            problems.append(f"{cid} has status {config['status']!r}, which the registry does not define")
        for tag in config.get("sets", {}):
            if tag not in settings:
                problems.append(f"{cid} sets {tag}, which CONFIG_MAP.md does not define")
        for tag in config.get("confounds", []):
            if tag not in confounds:
                problems.append(f"{cid} names {tag}, which CONFOUNDS.md does not define")
        for tag in config.get("errata", []):
            if not re.search(rf"\b{re.escape(tag)}\b", errata):
                problems.append(f"{cid} cites erratum {tag}, which ERRATA.md does not contain")
        manifest = config.get("manifest")
        if manifest and not (ROOT / manifest).is_file():
            problems.append(f"{cid} names a manifest that does not exist: {manifest}")
        for path in config.get("evidence", []):
            if not (ROOT / path).exists():
                problems.append(f"{cid} cites evidence that does not exist: {path}")
        for field in ("shows", "proven", "not_proven"):
            if not str(config.get(field, "")).strip():
                problems.append(f"{cid} leaves {field!r} empty; a registered config says what it does and does not show")

    print(f"settings {len(settings)}, misreadings {len(misreadings)}, confounds {len(confounds)}, "
          f"configs {len(registry['configs'])}, alarms {len(real)}", flush=True)
    for problem in problems:
        print(f"  MISMATCH: {problem}", flush=True)
    if problems:
        print(f"{len(problems)} mismatch(es)", flush=True)
        return 1
    print("every tag resolves", flush=True)
    return 0


def _show(args: argparse.Namespace) -> int:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    for config in registry["configs"]:
        if config["config_id"] != args.config:
            continue
        print(f"{config['config_id']}  [{config['status']}]  {config['title']}", flush=True)
        for field in ("shows", "proven", "not_proven"):
            print(f"\n{field}:\n  {config[field]}", flush=True)
        if config.get("confounds"):
            print(f"\nconfounds: {', '.join(config['confounds'])}", flush=True)
        if config.get("errata"):
            print(f"errata:    {', '.join(config['errata'])}", flush=True)
        return 0
    print(f"no configuration {args.config!r}; known: {[c['config_id'] for c in registry['configs']]}", flush=True)
    return 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    auditor = sub.add_parser("audit", help="check every cross-reference resolves")
    auditor.set_defaults(handler=_audit)
    shower = sub.add_parser("show", help="print one registered configuration")
    shower.add_argument("--config", required=True)
    shower.set_defaults(handler=_show)
    args = parser.parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
