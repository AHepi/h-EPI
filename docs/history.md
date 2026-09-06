# History

This repository began as `h-EPI`, an implementation workspace for a formal creativity semantic model (CR-1.0): a fail-closed executable interpretation bridge with Lean proofs, a content-pinned authority manifest, a bootstrap package, and the Semantic Model Forge, a criticism-first method for translating a source into a model without confirming it. Most of that work was carried out by a Codex orchestrator across several tranches, each recorded in a handover document, with external audits by other models.

In September 2026 the form-filling conformance harness was built as a pilot of the same method on a second problem, and the maintainer then chose to keep only the harness. Everything else was removed from the working tree in one commit.

## Recovering the earlier project

The complete tree immediately before the removal is kept on a branch (the remote refuses tags, so a branch is the durable pointer; a local tag `cr-eib-0.6-full` marks the same commit, `e3faadb`):

```sh
git fetch origin archive/cr-eib-0.6-full
git switch --detach origin/archive/cr-eib-0.6-full
```

That branch holds the CR-1.0 bridge (`bridge/`, `formal/`, `baseline/`, `authority/`), the forge runtimes and their 28 record schemas (`src/creib/forge/*.py`, `forge/schema/`), the calibration record and inquiry plan, the four orchestrator handovers (`docs/handoff/`), the external audit transcripts (`docs/audits/`), the pinned Docker replay image (`.devcontainer/`), the Lean and container CI jobs, and the 1,053 incident-form observation records from the nine-model run. Its `CLAUDE.md` and `docs/handoff/STATUS.md` describe the state of that project as it was left. Those observation and run records are `v1`; the record schemas on `main` became `v2` when grounding was added, so read them with the branch's own `fills` and `report`, or with a raw JSON scan. `docs/failure-modes.md` cites them by observation id.

## What was kept, and why

- `src/creib/canonical.py`, `strict_json.py`, `errors.py`: the byte-level discipline every record depends on.
- `src/creib/forge/schema_validation.py`: the offline schema loader, rewritten without the CR-1.0 record dispatch and with the content-keyed cache folded in.
- `src/creib/forge/conformance/`, its schemas, the two pilot configurations, the template's live records, the CLI, the tests, `tools/check.py`, the CI workflow, the SessionStart hook, and the publish skill.

Nothing about the earlier project's status was changed by the removal. Its mapping fidelity was `UNREVIEWED` and its bridge conformance `BLOCKED` when it was set aside, and no source-level theorem had been proved or refuted.
