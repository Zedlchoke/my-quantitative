# DATA MANIFEST — Lane B (NFL_B_dataset) — NFL-WINPROB-PREP-V1

Cycle: NFL-WINPROB-PREP-V1 · Role: quant-explorer · Measured: 2026-10-04 (UTC)
Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/nfl-winprob-prep-v1/integration`
Branch HEAD at start (`orca/nfl-winprob-prep-v1-integration`):
`8deb036d9ebb74e24de99e8c3461e7cea9b9dc43` (measured via ref-file read; no git
commands run per lane scope).

## Source authority

- Owner directive 2026-10-04 + prior annex audit: nflverse-data releases are
  CC BY 4.0 (verified). All bytes came from
  `github.com/nflverse/nflverse-data` release download URLs only.

## Release metadata measured 2026-10-04 (GitHub API)

- `/releases/latest` resolves to tag **`pbp`** (published_at
  2022-01-28T02:12:09Z, 164 assets; asset churn continuous since).
- `games.csv` lives in release tag **`schedules`** (published_at
  2025-10-01T11:19:34Z); asset `games.csv` updated_at 2026-10-04T12:16:32Z.
  Note: `releases/latest/download/games.csv` would 404 — the correct path is
  `releases/download/schedules/games.csv`. (There is no `games` tag.)
- as-of markers (timestamp.json): schedules `{"last_updated":"2026-10-04
  08:16:30 EDT"}`; pbp `{"last_updated":"2026-10-04 05:03:18 EDT"}`.

## Downloaded files

Location: `~/.my-quantitative-data/nfl-nflverse-v1/raw/`
Per-file URL / tag / asset updated_at / bytes / sha256 / pull time UTC:
see `ATTRIBUTION.md` in that directory (single table, 8 files,
104,417,685 bytes total). All local byte sizes matched GitHub API asset
metadata exactly.

| file | role |
|---|---|
| games.csv | schedules/games census source (Lee Sharpe) |
| timestamp_schedules.json | as-of marker for games.csv |
| timestamp_pbp.json | as-of marker for pbp release |
| play_by_play_{2021..2025}.parquet | 5 most recent COMPLETE-season pbp (2026 skipped, in progress; 102.1 MB total — no cut vs 600 MB cap) |

Provenance proven during census: every parquet's distinct game_id set joins
100% into games.csv; seasons inside each parquet are exactly the labeled year.

## Lane artifacts (this directory)

- `DATA_MANIFEST.md` — this file.
- `DATASET_AUDIT.md` — full census results + freeze proposal.
- `audit_script.py` — reproducible census (reads raw dir only, writes nothing;
  run: `/Users/hoangminhlong/my-quantitative/.venv/bin/python audit_script.py`).
- `handoff_B.json` — structured handoff `zcode_orch_v3_handoff@1`.

## Environment measured

- Python 3.12.14 (workspace .venv); pyarrow 25.0.1, pandas 3.0.5, numpy 2.5.2
  (all present — parquet row counts RUN, not NOT_RUN).
- No installs performed.

## External outputs

- `~/.my-quantitative-data/nfl-nflverse-v1/raw/` (8 data files + ATTRIBUTION.md)

## NOT_RUN / corrections vs dispatch expectations

- Dispatch expected games.csv seasons "1920s..2026": **measured 1999..2026** —
  the nflverse-data schedules release starts at season 1999. No 1920s-1998
  coverage exists in this source.
- Strike seasons 1982/1987: **NOT_IN_RELEASE** (out of range).
- `releases/latest/download/timestamp.json` succeeded (latest = pbp), but the
  as-of marker for games.csv is the **schedules** release marker — both
  recorded.
- Dispatch expected rename "STL→LA 2016": verified, abbrev is `LA` (not LAR).
