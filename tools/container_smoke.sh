#!/usr/bin/env bash
set -euo pipefail

umask 022

if [[ -n "${LD_PRELOAD:-}" ]]; then
  echo "LD_PRELOAD must be absent from the replay environment" >&2
  exit 1
fi
if [[ -n "${LEAN_FIXED_APP_PATH:-}" ]]; then
  echo "LEAN_FIXED_APP_PATH must be absent from the replay environment" >&2
  exit 1
fi
if [[ "$(uname -m)" != "x86_64" ]]; then
  echo "the reviewed replay environment is scoped to linux/amd64" >&2
  exit 1
fi

pdftotext -v 2>&1 | grep --fixed-strings --line-regexp 'pdftotext version 24.02.0'
pdfinfo -v 2>&1 | grep --fixed-strings --line-regexp 'pdfinfo version 26.05.0'
lean --version \
  | grep --fixed-strings 'Lean (version 4.33.1,' \
  | grep --fixed-strings 'commit 819816b2e0a3bf405af45ae5c7af2491d8f5bee6'
python3 --version 2>&1 | grep --extended-regexp '^Python 3\.12\.'

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repository_root}"
export PYTHONPATH="${repository_root}/src"

if (( $# > 1 )); then
  echo "usage: $0 [authority-pdf]" >&2
  exit 2
fi

verify_arguments=(--lean)
expected_operational_status=PARTIAL
expected_authority_pdf_checked=false
if (( $# == 1 )); then
  verify_arguments=(--pdf "$1" --lean)
  expected_operational_status=PASS
  expected_authority_pdf_checked=true
fi

python3 baseline/cr-1.0/bootstrap-v0.1/tools/validate_bootstrap.py
# One complete Python pass. The former second pass under `python -O` is
# replaced by the shipped-code assert guard in tools/check.py (lint), which
# CI runs on the same commit; with no `assert` in src/ or tools/ the -O pass
# could not exercise anything this pass does not.
python3 -m unittest discover -s tests -v
sha256sum --check --strict formal/formal-package.sha256

formal_replay_directory="$(mktemp -d -t cr-eib-container-formal-XXXXXXXX)"
actual_axiom_transcript="$(mktemp -t cr-eib-container-axioms-XXXXXXXX.txt)"
cleanup() {
  rm -rf -- "${formal_replay_directory}"
  rm -f -- "${actual_axiom_transcript}"
}
trap cleanup EXIT

while read -r _ repository_path; do
  relative_path="${repository_path#formal/}"
  if [[ "${relative_path}" == "${repository_path}" \
      || -z "${relative_path}" \
      || "${relative_path}" == /* \
      || "${relative_path}" == ./* \
      || "${relative_path}" == */./* \
      || "${relative_path}" == */. \
      || "${relative_path}" == .. \
      || "${relative_path}" == ../* \
      || "${relative_path}" == */../* \
      || "${relative_path}" == */.. \
      || "${relative_path}" == *//* ]]; then
    echo "formal package manifest path escapes formal/: ${repository_path}" >&2
    exit 1
  fi
  canonical_source_path="$(realpath --canonicalize-existing -- "${repository_path}")"
  if [[ "${canonical_source_path}" != "${repository_root}/formal/"* ]]; then
    echo "formal package source escapes formal/: ${repository_path}" >&2
    exit 1
  fi
  target_path="${formal_replay_directory}/${relative_path}"
  canonical_target_path="$(realpath --canonicalize-missing -- "${target_path}")"
  if [[ "${canonical_target_path}" != "${formal_replay_directory}/"* ]]; then
    echo "formal replay target escapes temporary directory: ${repository_path}" >&2
    exit 1
  fi
  mkdir -p "$(dirname "${target_path}")"
  cp -- "${repository_path}" "${target_path}"
done < formal/formal-package.sha256

(
  cd "${formal_replay_directory}"
  lake build >build.log 2>&1
  lake env lean CREIB/Audit/Axioms.lean >"${actual_axiom_transcript}" 2>&1
)

python3 - \
  docs/audits/CR-EIB-0.2_Release_Axiom_Transcript.txt \
  "${actual_axiom_transcript}" <<'PY'
from pathlib import Path
import sys

expected_path = Path(sys.argv[1])
actual_path = Path(sys.argv[2])
expected = expected_path.read_bytes()
actual = actual_path.read_bytes()
if len(actual.splitlines()) != 14:
    raise SystemExit(
        f"release axiom transcript has {len(actual.splitlines())} lines instead of 14"
    )
if actual != expected:
    raise SystemExit(
        "release axiom transcript byte mismatch\n"
        f"expected={expected.decode('utf-8', errors='replace')!r}\n"
        f"actual={actual.decode('utf-8', errors='replace')!r}"
    )
PY

replay_report="$(python3 tools/verify_bridge.py "${verify_arguments[@]}")"
printf '%s\n' "${replay_report}"
printf '%s\n' "${replay_report}" | python3 -c '
import json
import sys

report = json.load(sys.stdin)
expected = {
    "operational_status": sys.argv[1],
    "mapping_fidelity_status": "UNREVIEWED",
    "bridge_conformance_status": "BLOCKED",
    "record_status": "PASS",
    "schema_status": "PASS",
    "formal_package_status": "PASS",
    "authority_pdf_checked": sys.argv[2] == "true",
    "formal_replay_checked": True,
}
actual = {key: report.get(key) for key in expected}
if actual != expected:
    raise SystemExit(f"container smoke status mismatch: expected {expected!r}, got {actual!r}")
' "${expected_operational_status}" "${expected_authority_pdf_checked}"
