---
type: agent-todo
title: Point scheduled scanners at the Python application code
priority: high
source: scan-vulnerabilities automation
status: open
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

1. Should `process_data` be merged into `main`, should `process_data` become the GitHub default branch, or should only the Cursor automations change their base branch to `process_data`?

## Context

- Scanned empty `main` at `7a9d6c11003f7f97aab9d359f6a9e9a6995dd6c2`.
- Application tree is on `origin/process_data`.
- Related follow-ups (do not implement until the code is on the scan branch): `20260907-restore-or-skip-alias-csv-build.md`, `20260907-scope-non-derivation-starters-write.md`.
