---
name: workspace-agent-todo
description: >
  Write deferred agent work into `.cursor/agent-todos/` and follow the human-gate
  protocol for GitHub issues. Use when an agent finishes a task with leftover work,
  when converting agent todos into issues, when working an agent-ready issue, or
  whenever the agent is unsure and must ask a human before continuing.
---

# Agent todos and human gates

## When to write a todo (do not invent work)

Only when the current task leaves real follow-up that is out of scope, blocked, or explicitly deferred. One file per item under `.cursor/agent-todos/` using the format in that folder's README. Skip cosmetic cleanup and speculative ideas.

## Filing issues (todo-to-issue agent)

1. Read open todos (`status: open` or missing `status`).
2. Skip duplicates already tracked by an open GitHub issue (search title/keywords / `Source todo:` path).
3. If **Questions** is non-empty or acceptance criteria are ambiguous: create the issue with label `needs-human`, comment the questions, do **not** add `agent-ready`.
4. If the work is clear: create the issue with label `agent-ready`.
5. You may set `status: filed` and `filed_issue: <url>`. Commit that only on an already-open related PR — never open a new PR just for the status change. If no such PR exists, leave the file; the issue-worker updates it in the implementation PR (duplicate search prevents re-filing).
6. Never invent research methodology or product decisions. Prefer `needs-human` over guessing.

## Working issues (issue-worker agent)

Trigger: issue has `agent-ready` and does not have `needs-human`.

1. Add `agent-working`, remove `agent-ready` and `agent-todo`.
2. Branch from `main` as `cursor/issue-<number>-<kebab-slug-from-title>` (plus any required cloud suffix). Name it after the GitHub issue, never after the automation (`issue-worker-…`) or an opaque UUID.
3. Implement only what the issue asks. Prefer existing modules; call library functions instead of interactive `main.py`.
4. If the issue names a `Source todo:` path, update that todo in the same implementation PR (`filed`/`cancelled` or delete). Never open a separate PR just for status.
5. Run `pytest` (or the narrowest covering tests). Open a draft PR into `main` that closes the issue (`Fixes #N`). Before marking it ready for review, `git fetch origin main`, merge `origin/main` into the branch, push, then mark ready. Do not mark ready while behind `origin/main`.
6. On any open question (missing design, conflicting requirements, secret/env you lack, destructive choice, unclear acceptance):
   - Stop coding (or revert unfinished speculative work).
   - Comment on the issue with numbered questions.
   - Replace `agent-working` / `agent-ready` with `needs-human`.
   - Do not open a PR until answers land.
7. Resume only when a human clears the ambiguity (comment answers and/or removes `needs-human` and adds `agent-ready`).

## Human gate rules (hard)

- Ambiguity → ask. Do not assume.
- Prefer one blocking comment with all questions over drip questions.
- Do not merge. Humans merge.
- Do not close `needs-human` issues yourself.
