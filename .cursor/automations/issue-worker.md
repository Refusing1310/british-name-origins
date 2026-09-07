# Automation: issue worker

Paste this into [cursor.com/automations](https://cursor.com/automations) (or use `/automate` locally). Repo: `Refusing1310/british-name-origins`, base branch `main`.

## Triggers

1. **Issue label changed** — label `agent-ready` **added**
2. **Issue comment** — on issues that still have `needs-human` (so a human answer can resume work): when commenting, the agent checks whether answers are sufficient; if yes, it may remove `needs-human` and add `agent-ready` only when the human explicitly says to proceed or answers every question. Prefer: human removes `needs-human` and adds `agent-ready` themselves.

## Tools

- Repository access (this repo)
- Pull request creation: **on**
- Computer use: off (this is a Python data pipeline, not a web UI)

## Required secrets

- `GH_TOKEN` — fine-grained PAT with **Issues: Read and write** (for labels/comments). Git push/PR can use the built-in Cursor GitHub App token.

## Prompt

```text
You implement GitHub issues labeled agent-ready for Refusing1310/british-name-origins.

Follow `.cursor/skills/workspace-agent-todo/SKILL.md`. Human gate is mandatory.
Default branch is `main`. This is a Python place-name / geospatial data project (pandas, geopandas, pytest) — not a web app.

On start:
1. Read the triggering issue (number, title, body, labels, recent comments).
2. If the issue has `needs-human`, or lacks `agent-ready`, stop (unless a human just answered every open question and asked you to continue — then remove `needs-human`, add `agent-ready`, and proceed).
3. Add label `agent-working` and remove `agent-ready` and `agent-todo`.
4. If anything is still ambiguous (methodology, data source licensing, env/secret, acceptance, destructive choice over raw/processed data): do not code. Comment numbered questions, set `needs-human`, remove `agent-working`/`agent-ready`, stop.

When clear:
5. Branch from `main` named after the issue, not the automation. Pattern: `cursor/issue-<number>-<kebab-slug-from-title>` (keep any required cloud suffix). Example: issue #3 "Fix Ordnance Survey header join" → `cursor/issue-3-fix-os-header-join-…`. Do **not** use `cursor/issue-worker-…`, opaque `cursor/bc-<uuid>-…`, or other cloud-default names that omit the issue number and title.
6. Implement the smallest change that satisfies Acceptance. Prefer existing modules under `data_processing/`, `etymology/`, `graph_creation/`, and `constants/`. Do not drive interactive `main.py` prompts in automation — call library functions instead.
7. If the issue body names a `Source todo: .cursor/agent-todos/…` file, update its status in this same implementation PR (set `filed`/`cancelled` or delete the file). Do not open a new PR just for that status change.
8. Run `pytest` (or the narrowest tests that cover the change) and fix failures you caused.
9. Open a draft PR into `main` with `Fixes #<number>`, a humanized summary, and test evidence.
10. Before marking the PR ready for review: `git fetch origin main`, merge `origin/main` into the branch (prefer merge over rebase), push, then mark ready. Do not mark ready while behind `origin/main`.
11. Comment on the issue with the PR URL. Remove `agent-working` when the PR is open (or when marked ready).

Never merge. Never invent unanswered requirements. Prefer stopping with `needs-human` over a speculative PR. Todo status changes belong in the implementation PR — never a PR opened only for that. Never commit giant raw OS dumps or regenerable processed CSVs unless the issue explicitly requires it and `.gitignore` changes are intentional.
```
