---
type: agent-todo
title: Restore alias CSV generation or stop calling the stub
priority: medium
source: scan-vulnerabilities automation
status: open
---

## What

Stop `import_and_process_data` from calling a no-op `build_aliases_csv` that never writes `data/processed/aliases.csv`.

## Why

On `process_data`, `main.py` calls `build_aliases_csv` when `aliases.csv` is missing, but `data_processing/produce_aliases.py` is entirely commented out and returns `None`. `etymology/place_name_parser.py` is supposed to use aliases later. Out of scope for the security scan (no attacker path), but it is a real pipeline hole.

## Acceptance

- Either `build_aliases_csv` writes a real `aliases.csv` from `elements_df`, or `main.py` no longer calls it until that logic exists.
- `pytest` still passes for the existing processing tests.

## Questions

1. Should aliases be generated now, and if so with what rules (the commented stub used `{element}_alias_{n}` placeholders), or should the call site be removed until the etymology algorithm is designed?

## Context

- Primary location: `data_processing/produce_aliases.py` (call site `main.py`).
- Code lands on `main` via the process_data merge; implement against `main` after that merge.
