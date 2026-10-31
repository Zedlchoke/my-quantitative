# PaperDesk and options research

Current owner direction (2026-10-31): preserve PaperDesk, archive unrelated
research, and investigate Python options strategies for a USD 1,000 account.
Paper/demo comes first. US equity, crypto and FX options are in scope.

## PaperDesk

The app is under `apps/paperdesk`. Its backend uses the root Python environment,
`research/papertrade_exec`, pinned sports/forecasting worktrees, governance and
external data. These are retained. Do not delete a worktree merely because its
name does not contain PaperDesk. Existing paper laws and permissions still apply.

## New project: data feasibility before strategy selection

Read `plans/PLAN_options_data_feasibility_v1_DRAFT.txt` in full. It records the
source dossier, candidate hypotheses, data gaps, risk decisions and five batches.
This is an unregistered bootstrap proposal, not a scored research cycle.
No sustainable strategy has been established. No strategy engine, continuous
collector, AI integration or paper executor is active for the new project.

A bounded public-data diagnostic is available:

```bash
.venv/bin/python scripts/options_data_probe.py --output-dir /absolute/path/to/a/new-probe-directory
```

Choose a new output directory outside this repository. The diagnostic requests
ETH option metadata, one book, seven days of hourly option candles and thirty
days of hourly underlying candles. It writes raw responses, receipt times,
SHA-256 hashes and a summary. It requires `curl`; no account or API key is used.
It has no order endpoint, scoring loop or background service. A received sample
is not proof of streaming reliability, historical executable quotes or an edge.

## Archive and recovery

The pre-cleanup repository archive and manifests are outside this checkout:
`/Users/hoangminhlong/my-quantitative-archives/20261031-paperdesk-options/`.
Read `BACKUP_MANIFEST.json`, `TARGET_VERIFICATION.json`, `RESTORE_CHECK.json` and
`RESTORE_INSTRUCTIONS.txt` there. Historical non-PaperDesk projects are paused
for owner-directed archival, not relabelled as scientific failures or successes.
Their plans, ledger history and Git branches remain evidence; removed local
artifacts are resolved through the archive. External data is untouched.

## Operating contract

`AGENTS.md`, `CLAUDE.md` and `HOW_TO_BE_A_LEAD_ENGINEER.md` retain the evidence,
worktree, lock, S1 and owner-authority boundaries. The canonical cycle registry
remains `plans/CYCLE_REGISTRY.json`; all writes use `researchctl`.
