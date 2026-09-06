# Conformance harness — agent entry point

Read this file first, then `README.md`, then `agent.md` (how to use the harness, use by use, command by command), then `docs/how-it-works.md`; `docs/failure-modes.md` is the register of what has been observed to go wrong, with record ids. `AGENTS.md` is a symlink to this file so Codex reads the same rules; `agent.md` is the operating guide, not a rules file. The `h-epi-safe-publish` skill (under `.codex/skills/`, symlinked into `.claude/skills/`) governs publishing.

## What this repository is

A criticism-first harness that checks how a language model fills a form from a document. The machine is `src/creib/forge/conformance/`; its configurations live under `forge/conformance/pilots/`; its records under `forge/conformance/runs/`. The earlier CR-1.0 semantic-model project that this grew out of was removed from the tree and is preserved on the branch `archive/cr-eib-0.6-full` (see `docs/history.md`).

## Never promote

- Passing tests, schema validity, agreement between models, or green CI never confirm a model. The strongest run label is `UNREFUTED_FOR_DECLARED_SCOPE`; a run with any unscored field or any transport error is `INCONCLUSIVE_NO_SCORED_OUTPUT`; a run with the model as a live suspect anywhere is `REFUTED_CASES_PRESENT`.
- A failed expectation criticises the tested conjunction. Live loci are a subset of CANDIDATE (the model), AUXILIARY (prompt, executor, format plumbing), TEST (the oracle), SCOPE (the task as framed); never a single locus after a model call; empty only when every field matched.
- Never hand-edit a published record. Records are content-addressed and published no-clobber; a changed oracle means a re-score through `run --replay-dir <observations>` (the `ReplayExecutor`, matched by request digest), which writes new records, not an edited file.
- A records directory is read by enumeration: every entry is an observation record, a run record, or an error that names it, and a record file's name must carry the prefix of the id it holds. Nothing is passed over.
- The report never ranks models, computes scores, or uses words like best, worst, pass, or accuracy.
- A general claim about language models is stated as a conjecture in a pilot's `claims.json` and tested with `claims`; a claim is `REFUTED` by one record or `UNREFUTED_FOR_DECLARED_SCOPE`, never confirmed, and a document that makes such a claim cites the claim id and the records.
- A refutation rests on readings of the key and the matcher. The readings that have been argued about, the criticisms of them, and a readiness a person decided (`PASS`, `FAIL`, `UNKNOWN`, with the reason) live in the pilot's `appraisal.json`; `claims --appraisal` labels them `in`, `out`, or `undecided` by a fixed least-fixed-point rule and classes each refutation `usable`, `contested`, or `defeated`. Readiness is never inferred from records, and a reading nobody has argued about is usable, which is absence of argument, not endorsement.
- An unrefuted claim says whether its refuting condition held on any supplied record outside its scope; a survival whose condition held nowhere has not been shown able to fail and is never cited as a survival without saying so. A control whose corruption leaves the reference output unchanged is refused when the plan is built.
- Conjectures for a run are committed with the pilot change, before the run's records exist. A conjecture written after the records is a description of them, and the document that reports it says so.

## Environment

- Python 3.12. In a Claude Code web session the SessionStart hook creates `.venv` and exports `PATH` and `PYTHONPATH`. Elsewhere run `python3.12 tools/check.py bootstrap`.
- `PYTHONPATH=src` for every invocation; the package is not installed.
- Dependencies are the hash-locked set in `requirements-container.txt` (jsonschema and its stack). Nothing else.
- The model API key is read only from `OLLAMA_API_KEY` at call time. It must never appear in a file, a record, a log, or an exception message. A model reply that echoes the key is redacted. A local Ollama needs no key: set `"auth": "none"` in the pilot's endpoint and no Authorization header is sent.

## Verification

| Target | What | Time |
|---|---|---|
| `python tools/check.py lint` | compileall, shipped-code assert guard, whitespace | seconds |
| `python tools/check.py test` | complete offline suite | ~10 s |
| `python tools/check.py pilots` | validate and plan every pilot configuration | seconds |
| `python tools/check.py all` | all three | seconds |

Run `all` before every commit. No model is called by any check. Do not add `assert` to `src/` or `tools/`; use explicit `raise`.

## Changing the machine

- Adding a schema keyword, oracle kind, verdict, trigger, or scope label means changing the code, the matching schema under `forge/conformance/schema/`, and a test, together. The observation and corpus schemas each carry their own copy of the oracle-kind list; the observation schema and `routing.py` each carry the trigger list; grounding verdicts live in `oracle.py`, `routing.py`, `report.py`, and both record schemas.
- A change to the shape of an observation or run record is a version change: bump `OBSERVATION_SCHEMA_VERSION` or `RUN_SCHEMA_VERSION` in `common.py`, the matching `_DOMAIN` constants in `records.py`, and the `const` in the schema, together. Records written under the earlier version stay as they are and are read by the code that wrote them.
- Grounding spans and abstention are configuration (`grounding` in `pilot.json`), never code. Mode `none` must leave every existing pilot byte-for-byte unchanged; a test asserts it. The same holds for `span_relaxations` (default empty) and `repeats` (default 0): anything that adds model calls or loosens a check is off unless a pilot asks for it, and an absent or default value is written to no record body, so earlier variant ids keep replaying.
- The pilot configuration is a source binding of the plan, so any edit to `pilot.json` moves the plan id even when no variant changes. Cite plan ids from run records, not from memory.
- A live run that shows a new failure mode gets an entry in `docs/failure-modes.md` with observation ids taken from `evidence`, never from memory. Absence of a mode on the cases run is recorded too.
- Adding a claim predicate means changing `claims.py`, `conformance-claims.schema.json`, and a test together; adding an argument kind, readiness value, or label means changing `appraisal.py`, `conformance-appraisal.schema.json`, and a test together. Both vocabularies fail closed on anything unknown.
- A new form is a new directory under `forge/conformance/pilots/`, never a code change. If a form cannot be expressed, extend the form profile in `spec.py` and say so in `docs/how-it-works.md`.
- Live model runs are deliberate: they cost money and produce records that get committed. Use `--family BASELINE` for plain fills, `--limit` while developing, and a scratch `--output-dir` for anything you are not ready to commit.

## Publishing

- Work on a branch (`claude/*`, `codex/*`, or a human-chosen name). Never commit on or push to `main`; publication is a pull request and merging is a human action.
- Push only to the branch's own upstream: `git push -u origin HEAD`. Never `--force`, never `HEAD:main`, never rebase, reset, amend, or rewrite published history. `.claude/settings.json` denies these commands.
- Stage explicit paths. Run `git diff --cached --check`. Never stage `.venv`, key material, or source documents you are not licensed to share.

## Style

- LF line endings, no trailing whitespace, strict JSON (no duplicate keys, no floats), canonical bytes for records.
- Type-annotated Python with `from __future__ import annotations`, frozen dataclasses, `RecordError` for input failures, no `print` in library code.
- Explain results to a person by leading with what happened, translating every label the first time it appears, and keeping every live suspect visible.
