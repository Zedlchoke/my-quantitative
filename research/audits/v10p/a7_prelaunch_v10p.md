# A7 prelaunch audit — V10P-R

- producer: A7 (independent recompute, all evidence self-generated)
- worktree: `/Users/hoangminhlong/my-quantitative-v10-wt/a7-v10p-prelaunch`
- freeze audited: `2c13d03410c3f8db6a8f9ac2dba0ecd1a37dd79d`; W2: `d61a483669b692b786938ba06c6826d183536e73`
- bootstrap: `5bb1a90551c8f7823773af713316a45e0ca070cd`
- generated_at_measured: `2026-08-27T15:00:03Z`; deadline `2026-08-27T16:55:00Z`

## Verdict: `NO_GO_BLOCKED_PRELAUNCH`

All ten specified prelaunch gates PASS on my own measurements. One HIGH code/data
defect outside those literal criteria blocks launch, plus two environmental blockers.

## Gate results

| Gate | Verdict | Evidence (self-generated) |
|---|---|---|
| G05 ETH loader | PASS | 2 parts, raw 70079 rows, 34954 in window, **0 duplicates**, 0 internal gaps, no `DataIntegrityError` |
| G05 coverage | **FAIL / HIGH** | see below |
| Window/folds | PASS | `hyp_a8_m01.py:122-123` window pin; `:978-1017` purge (`purge_days=WARMUP_DAYS_REQUIRED=1`); `:208` `FORCE_FLAT_REASON` |
| BG1-BG6 | PASS | `pytest ... -q` → **87 passed**, exit 0; adapter grep `M01\|A8-V10\|hyp_a8` outside `m01_plugin.py` = **0 hits** |
| G15 funding | PASS | hand-derived `-250 / +500 / net +250 / margin 0.05`; confirmed by direct `accrue_span` call |
| F2 cache | PASS | raw_reads 2 (cached) vs 6 (uncached); wall 0.870s vs 2.043s; digests equal; thresholds preregistered |
| G17 resource cap | PASS | measured now **1.9831 GB** < 2.0 reserve → safe_cap 0 → `final_cap=0`; facade rejects any `final > measured` |
| H08 12-20 | PASS | 9 explicit cases, 0 pre-filled statuses, 23 test functions, all executed |
| W2/R1b/R2b | PASS | R1b==R2b at `d61a483` detached+clean; diff vs freeze is control-JSON only; 2 data files sha-identical; old R1/R2 intact at `79fc883` |
| Budget purity | PASS | `results/registry/experiments.jsonl` absent → 0 CELL_RESULT, budget 0 |
| Full suite | PASS | **1275 passed, 1 skipped**, exit 0, 72.21s |

## HIGH — staged data does not reach the preregistered scored window end

Measured, not inferred:

- last staged bar `2026-08-20T02:29:59.999Z`
- declared window end `2026-08-21T00:00:00Z`
- shortfall **86 bars = 21.5 hours** (99.7545% coverage)
- `build_daily_closes` emits a close for the terminal boundary `2026-08-21T00:00:00Z`
  sourced from that 21.5 h-stale bar, rather than omitting it or failing closed
- `coverage_report()` returns only a count (`34954`) and raises nothing
- no artifact under `research/control/v10p_run/` or `research/control/v10_discovery_run/`
  acknowledges the shortfall

Root cause: the catalog part was staged `2026-08-20T02:34:14Z` as a rolling 1-year
slice, so it ends ~21.5 h before the preregistered window end. The final scored day's
close is not PIT-real and the force-flat at the window boundary is computed from
stale data.

Remediation is owner-level: either re-stage bars through `2026-08-21T00:00:00Z`, or
re-declare the window end to the actual staged snapshot. Changing a preregistered
constant is not within A7's allowlist.

## Other blockers

- **BLK-2** — scored launch window already closed. Event log records
  `scored_launch_window_closed` at `14:55:00Z` (PLAN §14: `<120 minutes -> no new
  scored cell`). At audit time ~115 min remained.
- **BLK-3** — `final_cap=0` today: no local scored launch on this host regardless of
  schedule. This is correct fail-closed behaviour, not a defect.

## Honestly unavailable / method notes

- No gate was left `UNAVAILABLE_PARTIAL`.
- F2 was verified by reading the measure script and the recorded decision artifact
  (full staged slice + ranks, `rows_last_pass=761` both arms, byte-parity, wall-pair,
  preregistered thresholds) — **not** by a fresh `--probe-cache` re-run, which would
  also have perturbed the G17 RAM reading.
- My first BG1-BG6 invocation silently no-op'd: I passed `/Users/hoangminhlong/.venv/bin/python`
  which does not exist. Re-ran with `/Users/hoangminhlong/my-quantitative/.venv/bin/python`.
  The failed attempt produced no results and is not counted anywhere.
- G15 was not run as a standalone captured-exit-code invocation; the file is included
  in both the 87-test and 1275-test runs, and I re-derived the arithmetic by hand and
  re-executed it directly.

## Scope

Wrote only `research/audits/v10p/a7_prelaunch_v10p.json` and this file. No production
or control source touched, no G1/G2/G3 artifact overwritten, nothing pushed, no scored
run launched, S1 not read.
