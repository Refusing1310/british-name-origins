---
type: agent-todo
title: Point scheduled scanners at the Python application code
priority: high
source: scan-vulnerabilities automation
status: cancelled
---

## What

Make `scan-vulnerabilities`, `find-critical-bugs`, `todo-to-issue`, and `issue-worker` review and implement against the actual pipeline (`main.py`, `data_processing/`, `database/`, `etymology/`), not the empty default branch.

## Why

A scheduled security scan of this repo's default branch `main` has only README, LICENSE, and `.gitignore`. The Python data project lives on `process_data` (commit `2ff83d7c7446a9db3c6a68e78823bce3b94d22fc`). Automations are documented as targeting `main`, so scans will keep reporting "no findings" even when later bugs land on `process_data`.

## Acceptance

- Default scan/implement base includes `main.py` and `data_processing/`.
- `.cursor/automations/*.md` match the chosen default branch.
- A follow-up scan of that branch can actually see the pipeline entry points.

## Questions

## Context

- Resolved by merging `process_data` into `main` (decision: merge into default branch rather than retargeting automations).
- Automations already document base branch `main`; after merge they will see `main.py` and `data_processing/`.
- Related follow-ups remain open: `20260907-restore-or-skip-alias-csv-build.md`, `20260907-scope-non-derivation-starters-write.md`.
