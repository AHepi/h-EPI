#!/bin/bash
# SessionStart hook for Claude Code on the web.
#
# A fresh remote container defaults to a Python the project forbids (3.11 <
# 3.12) and has none of the pinned dependencies, so the test suite fails on
# import. This hook creates the project virtual environment, installs ONLY the
# hash-locked wheel set the replay image uses, and exports PATH/PYTHONPATH for
# the session. It is synchronous and idempotent: re-running it is cheap.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

root="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)}"
venv="${root}/.venv"

interpreter=""
for candidate in python3.12 /usr/bin/python3.12 /usr/local/bin/python3.12; do
  if command -v "${candidate}" >/dev/null 2>&1; then
    interpreter="$(command -v "${candidate}")"
    break
  fi
done
if [ -z "${interpreter}" ]; then
  echo "session-start: python3.12 not found; the project requires Python >= 3.12" >&2
  exit 1
fi

if [ ! -x "${venv}/bin/python" ]; then
  "${interpreter}" -m venv "${venv}"
fi
"${venv}/bin/python" --version

# Hash-locked install: identical wheel set to the reviewed replay image.
"${venv}/bin/python" -m pip install --quiet --disable-pip-version-check \
  --no-deps --only-binary=:all: --require-hashes \
  --requirement "${root}/requirements-container.txt"

if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  {
    echo "export PATH=\"${venv}/bin:\${PATH}\""
    echo "export PYTHONPATH=\"${root}/src\""
    echo "export PIP_DISABLE_PIP_VERSION_CHECK=1"
  } >> "${CLAUDE_ENV_FILE}"
fi

# Smoke: one fast module proves the interpreter, dependencies, and PYTHONPATH.
PYTHONPATH="${root}/src" "${venv}/bin/python" -m unittest tests.test_strict_json -q
echo "session-start: environment ready (${venv}/bin/python, PYTHONPATH=${root}/src)"
