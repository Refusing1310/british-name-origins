# Cursor automations (agent issue loop)

Cloud automations keep deferred agent work and scanner findings moving, with a human stop whenever something is unclear.

```text
.cursor/agent-todos/*.md
        │
        ▼
 todo-to-issue  ──ambiguity──►  issue + needs-human  ──human answers──┐
        │                                                             │
        └──clear──►  issue + agent-ready  ◄───────────────────────────┘
                            │
 find-critical-bugs ────────┤
 scan-vulnerabilities ──────┤
                            ▼
                      issue-worker ──► PR into main
                            │
                     mid-work question
                            ▼
                      needs-human (stop)
```

Scanners only discover and file issues. They do not open PRs or implement fixes. `todo-to-issue` may set todo status to `filed`, but only by pushing onto an already-open related PR — never a new PR just for status. `issue-worker` implements anything labeled `agent-ready`, updates or deletes the source todo in that same PR, and drops `agent-ready` / `agent-todo` when it starts.

## Activate (required)

1. Create labels (commands in `todo-to-issue.md`).
2. Add Cloud Agent secret `GH_TOKEN` (fine-grained PAT, Issues read/write on this repo) at [Cloud Agents secrets](https://cursor.com/dashboard?tab=cloud-agents).
3. Open [cursor.com/automations](https://cursor.com/automations) and create new automations from:
   - [`todo-to-issue.md`](./todo-to-issue.md)
   - [`issue-worker.md`](./issue-worker.md)
   - [`find-critical-bugs.md`](./find-critical-bugs.md) — PR creation off
   - [`scan-vulnerabilities.md`](./scan-vulnerabilities.md) — PR creation off
4. Repo for every automation: `Refusing1310/british-name-origins`, base branch `main`.

## Human involvement

- Todos with a **Questions** section → `needs-human` (no auto-work).
- Scanner findings with unclear Acceptance / secrets / destructive data choices → `needs-human`.
- Worker hits ambiguity mid-run → comments questions, sets `needs-human`, stops.
- Resume by answering on the issue, then add `agent-ready` and remove `needs-human`.
