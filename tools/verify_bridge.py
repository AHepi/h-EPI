#!/usr/bin/env python3
"""Repository-local launcher for the CR-EIB verifier."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from creib.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main(["--repo-root", str(ROOT), *sys.argv[1:]]))
