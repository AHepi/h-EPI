---
name: h-epi-safe-publish
description: Safely stage, commit, and push authorized changes to AHepi/h-EPI with the Git CLI when the user explicitly asks to commit, publish, or push; no pull request or gh CLI is required.
---

# h-EPI safe publish

Use this skill only after the user explicitly authorizes an external Git mutation such as committing or pushing. Do not trigger it for inspection, diagnosis, review, or planning alone.

## Fixed boundary

The only allowed destination is GitHub repository `AHepi/h-EPI`. Accept an `origin` URL only when its parsed host, owner, and repository equal that destination. Never print a remote URL that contains user information or credentials; report only the canonical repository slug.

Do not invent an author identity, alter global Git configuration, print tokens, place credentials in a URL, create or delete tags, delete branches, rewrite history, force-push, reset, clean, or rebase protected history. Stop on an authentication failure, non-fast-forward rejection, ambiguous target, unexpected remote, or missing identity.

## Preflight

1. Resolve the repository root with `git rev-parse --show-toplevel` and confirm the work is inside it.
2. Parse `remote.origin.url` without echoing secrets and confirm the canonical destination is exactly `AHepi/h-EPI` on `github.com`.
3. Require the current branch to be exactly `main`, then check its upstream. Stop on any other branch; never map a feature-branch `HEAD` onto remote `main`. Fetch `origin` without changing the worktree.
4. If `origin/main` exists, calculate ahead/behind counts. Stop if local history is behind or diverged; do not silently merge or rebase.
5. Inspect `git status --short`, including untracked files. Preserve unrelated user changes.
6. Confirm an existing Git author name and email are available. If either is absent, stop and ask the user; do not choose one.

## Stage and verify

Stage only explicit reviewed paths. Never use `git add -A`, `git add .`, a broad unresolved glob, or a workspace root.

Review `git diff --cached --name-status`, `git diff --cached --stat`, and the substantive staged diff. Run `git diff --cached --check`; document any intentional immutable-byte exception and verify it against its pinned digest. Scan staged filenames and content for credential, private-key, environment-file, database, authority-PDF, archive, and generated-build artifacts. Never reveal a detected secret in output.

Run the checks relevant to the staged change. For the current h-EPI stack, the full safe set is:

```sh
python -m pip install -r requirements-ci.txt -r requirements-bridge-ci.txt
python baseline/cr-1.0/bootstrap-v0.1/tools/validate_bootstrap.py
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -O -m unittest discover -s tests
python tools/verify_bridge.py
python tools/verify_bridge.py --lean
```

The PDF replay is optional because the authority file is deliberately untracked. If a lawful local copy is present, run `python tools/verify_bridge.py --pdf <local-path> --lean` without staging or printing the file.

## Commit and publish

Create a focused commit whose message describes only the staged change. Recheck status immediately after committing. Push normally with `git push origin HEAD:main`; use `-u` only when establishing the first upstream. Never add `--force` or `--force-with-lease`.

After a successful push, read the local `HEAD` SHA and the remote `refs/heads/main` SHA and require exact equality. Report the canonical repository, branch, commit SHA, checks run, and any remaining uncommitted paths. Do not claim publication succeeded until the remote SHA matches.
