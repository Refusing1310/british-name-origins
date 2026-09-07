# Automation: todo → issue

Paste this into [cursor.com/automations](https://cursor.com/automations) (or use `/automate` locally). Repo: `Refusing1310/british-name-origins`, branch `main`.

## Triggers

- **Schedule:** every hour (or every 6 hours if quieter)
- **Push to branch `main`:** only when paths under `.cursor/agent-todos/` change (if the UI supports path filters; otherwise rely on schedule + manual run)
- **Manual** run for testing

## Tools

- Repository access (this repo)
- Pull request creation: off (this agent only files issues)
- Memories: optional (dedupe notes across runs)

## Required secrets (Cloud Agent / automation)

- `GH_TOKEN` — fine-grained PAT with **Issues: Read and write** on this repo (Cloud Agent GitHub App token cannot create issues)

## Labels (create once)

| Label           | Color    | Meaning                   |
| --------------- | -------- | ------------------------- |
| `agent-ready`   | `0E8A16` | Clear enough to implement |
| `needs-human`   | `D93F0B` | Blocked on human answers  |
| `agent-working` | `1D76DB` | Worker is in progress     |

```bash
gh label create agent-ready --color 0E8A16 --description "Ready for agent to implement"
gh label create needs-human --color D93F0B --description "Agent blocked; human input required"
gh label create agent-working --color 1D76DB --description "Agent is actively working this issue"
```

## Prompt

```text
You convert agent todos into GitHub issues for Refusing1310/british-name-origins.

Follow skill `.cursor/skills/workspace-agent-todo/SKILL.md` and the format in `.cursor/agent-todos/README.md`.

Steps:
1. List files under `.cursor/agent-todos/` (ignore README.md and anything under filed/ if present).
2. For each todo with status open (or missing status):
   a. Read the full file.
   b. Search existing open issues for duplicates (title/keywords / `Source todo:` path). If found, skip create.
   c. Build an issue title from frontmatter `title` (or the first heading).
   d. Build the issue body: What, Why, Acceptance, Context, plus a footer `Source todo: .cursor/agent-todos/<file>`.
   e. If the Questions section has any real content, or acceptance criteria are vague:
      - `gh issue create` with label `needs-human`
      - Comment with the questions numbered, asking a human to answer then add `agent-ready` and remove `needs-human`
   f. Else:
      - `gh issue create` with label `agent-ready`
3. Status updates are allowed (`status: filed`, `filed_issue: <url>`). Put them on an already-open PR that already carries this todo or related work — push to that branch. Never open a new PR whose only change is todo status. If no such PR exists, leave the file for the issue-worker to update in the implementation PR (duplicate issue search prevents re-filing).

Rules:
- Auth for issues: use `GH_TOKEN` / `gh`. If issue create fails with 403, stop and report that `GH_TOKEN` with Issues write is missing — do not invent a workaround.
- Never start implementation. Never guess product or research methodology decisions.
- Never open a PR specifically to change todo status; fold status into an existing PR when one exists.
- One issue per todo file. Skip empty or cancelled todos.
- Be concise in issue bodies.
```
