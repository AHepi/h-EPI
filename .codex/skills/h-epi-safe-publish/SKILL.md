---
name: h-epi-safe-publish
description: Safely stage, commit, push a working branch, and open a pull request for authorized changes to AHepi/h-EPI when the user explicitly asks to commit, publish, or push; never pushes to main directly.
---

# h-EPI safe publish

Use this skill only after the user explicitly authorizes an external Git mutation such as committing, pushing, or opening a pull request. Do not trigger it for inspection, diagnosis, review, or planning alone.

## Fixed boundary

The only allowed destination is GitHub repository `AHepi/h-EPI`. Accept an `origin` URL only when its parsed host, owner, and repository equal that destination. Never print a remote URL that contains user information or credentials; report only the canonical repository slug.

`main` is the publication target, never the working branch. Publication is a pull request from a working branch; merging is a separate human action. Never push to `main`, never map any `HEAD` onto `refs/heads/main`, never merge, never enable auto-merge.

Do not invent an author identity, alter global Git configuration, print tokens, place credentials in a URL, create or delete tags, delete branches, rewrite history, force-push, reset, clean, or rebase. If the Git CLI lacks a credential, stop and report; there is no fallback that manufactures commits through another channel.

## Preflight

1. Resolve the repository root with `git rev-parse --show-toplevel` and confirm the work is inside it.
2. Parse `remote.origin.url` without echoing secrets and confirm the canonical destination is exactly `AHepi/h-EPI` on `github.com`.
3. Require the current branch to be a working branch, not `main`. Agent-platform branch names such as `claude/*` and `codex/*` are the expected working branches; a human-chosen name is also fine. Stop if the current branch is `main`; do not create or rename branches to work around this.
4. Fetch `origin` without changing the worktree. If `origin/<branch>` exists, calculate ahead/behind counts and stop if local history is behind or diverged; do not merge or rebase. If `origin/main` has moved since the branch was cut, say so; the pull request will show the merge state.
5. Inspect `git status --short`, including untracked files. Preserve unrelated user changes.
6. Confirm an existing Git author name and email are available. If either is absent, stop and ask the user; do not choose one.

## Stage and verify

Stage only explicit reviewed paths. Never use `git add -A`, `git add .`, a broad unresolved glob, or a workspace root.

Review `git diff --cached --name-status`, `git diff --cached --stat`, and the substantive staged diff. Run `git diff --cached --check`; document any intentional immutable-byte exception and verify it against its pinned digest. Scan staged filenames and content for credential, private-key, environment-file, database, authority-PDF, archive, and generated-build artifacts. Never reveal a detected secret in output.

Run the checks through the single entry point so this skill, CI, README, and CLAUDE.md agree. From a Python 3.12 environment with the pinned dependencies (`python tools/check.py bootstrap` creates one):

```sh
python tools/check.py lint
python tools/check.py test
python tools/check.py verify
python tools/check.py verify-lean   # only if lean/lake are installed
```

`test-fast` is acceptable for an intermediate commit; the complete `test` target must pass before a pull request is opened or updated. If `lean`, `lake`, `pdftotext`, or Docker are absent, record that tier as `UNAVAILABLE` in the report; never simulate a result. The PDF replay is optional because the authority file is deliberately untracked; if a lawful local copy is present, run `python tools/verify_bridge.py --pdf <local-path> --lean` without staging or printing the file.

Some implementation files are pinned by the committed calibration record's execution contract (`_IMPLEMENTATION_CODE_PATHS` in `src/creib/forge/calibration.py`, plus every `forge/schema/*.schema.json`). A change to any of them makes the calibration replay tests fail until the maintainer regenerates the record with the authority PDF. State this explicitly in the pull request when it applies; do not "fix" it by editing the record or the tests.

## Commit and publish

Create a focused commit whose message describes only the staged change. Recheck status immediately after committing. Push the working branch to its own upstream: `git push -u origin HEAD`. Never add `--force` or `--force-with-lease`; never use a `HEAD:main` refspec.

After a successful push, read the local `HEAD` SHA and the remote `refs/heads/<branch>` SHA and require exact equality. Do not claim publication succeeded until they match.

Open a pull request against `main` for the pushed branch, using the `gh` CLI or the authenticated GitHub connector's create-pull-request operation. If neither is available, report the branch and stop; the human opens the pull request. The body must list the checks run and their results, any `UNAVAILABLE` tiers, whether pinned files changed, and the handover document for the tranche. Do not merge, approve, or enable auto-merge.

Report the canonical repository, branch, commit SHA, pull request URL, checks run, and any remaining uncommitted paths.
