# Agent todos

Agents write deferred work here as one Markdown file per item. The **todo-to-issue** automation turns these into GitHub issues. Do not put secrets in these files.

## File name

`YYYYMMDD-<kebab-slug>.md` (example: `20260907-alias-collision-handling.md`)

## Frontmatter

```yaml
---
type: agent-todo
title: Short imperative title
priority: medium # low | medium | high
source: <agent-or-pr-or-skill>
status: open # open | filed | cancelled
---
```

## Body

1. **What** — one sentence outcome.
2. **Why** — why it was deferred (out of scope, blocked, follow-up).
3. **Acceptance** — bullets that make the issue done.
4. **Questions** — anything a human must decide before work starts. If this section is non-empty, the issue gets `needs-human` instead of `agent-ready`.
5. **Context** — paths, related PRs, links (optional).

After an issue is filed, set `status: filed` and `filed_issue: <url>` when you can do it on an already-open related PR. Never open a new PR just for that status change. If no such PR exists, leave the file; duplicate issue search prevents re-filing, and the issue-worker updates or deletes the source todo in the implementation PR.
