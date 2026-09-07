---
type: agent-todo
title: Write non-derivation starters under the kepn output folder
priority: medium
source: scan-vulnerabilities automation
status: open
---

## What

Make `parse_elements` read and write `non_derivation_starters.csv` relative to the kepn output folder (or an explicit path), not a hardcoded process-cwd path.

## Why

`process_kepn_data` takes `output_folder` and writes `ground_truth.csv` / `elements.csv` there, but `parse_elements` always uses `Path("data/processed/non_derivation_starters.csv")`. Tests already `chdir` into a temp dir to contain that write. Out of scope for the security scan (the operator already controls cwd), but it is an unbounded relative write.

## Acceptance

- `parse_elements` (or `process_kepn_data`) takes an output directory or file path and uses it for the starters CSV.
- No remaining hardcoded `data/processed/non_derivation_starters.csv` inside `parse_elements`.
- Existing `tests/test_process_data.py` parser tests pass without relying on a surprise cwd write outside the provided output folder.

## Questions

## Context

- Primary location: `data_processing/process_csvs.py`.
- Code lands on `main` via the process_data merge; implement against `main` after that merge.
- Tests: `tests/test_process_data.py` fixture `isolated_parser_env`.
