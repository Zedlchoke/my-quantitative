# DATAGATE_REPORT — ERP1-TRACKA-COHORT-1 — tracka1-datagate lane

Lane: DATA-GATE IMPLEMENTER (implement + download + census ONLY — no PnL,
no signal/target computation, no backtest of any arm; scored cells
FORBIDDEN, GO-2 not given).
Worktree: `.worktrees/erp1-tracka-cohort-1/integration`, branch
`orca/erp1-tracka-cohort-1-integration`.
Base: `460d2acdf9c4dc3970a6dddbbdc36b08178f02a3` (after `git merge --ff-only main`).
Python: `/Users/hoangminhlong/my-quantitative/.venv/bin/python` (root checkout).

## Verdict line (per pair) — DATA GATE GREEN

| Pair | Probe | Census verdict | Gates (all true) | Key margins |
|---|---|---|---|---|
| AUDUSD | PROBE_PASS | **BUILD_PASS** | midweek-share / nonpos-spread / bars15 / dup-ts / reconcile | share 0.98611 (margin **+0.08611** over 0.90); nonpos minutes **0** (margin +0.01000); bars15 130,160 (**+30,160** over 100k); dup 0; reconcile max diff **0.0** pip |
| USDCAD | PROBE_PASS | **BUILD_PASS** | same five | share 0.98607 (**+0.08607**); nonpos **0**; bars15 130,102 (**+30,102**); dup 0; reconcile **0.0** pip |

Session-spread census (OPEN spread p50, pips): AUDUSD asia 1.0, london 1.0,
ny_overlap 1.0, ny_late 1.0, rollover 2.0, late_22_24 1.3, friday_20_23 1.1,
sunday_open 4.6; overall p50 1.0 / p99 4.1. USDCAD: asia 1.3, london 1.2,
ny_overlap 1.2, ny_late 1.2, rollover 2.3, late 1.7, friday 1.3,
sunday_open 6.8; overall p50 1.2 / p99 6.2. CLOSE-spread quantiles persisted
alongside (census JSONs). All 8 buckets well above the low-sample floor
(min n = 312, AUDUSD sunday_open); `LOW_SAMPLE_BUCKET` fired on no bucket.

## 1. Blocking port defect fix (plan §5.2) — CONFIRMED FIXED

Ancestor code (`EURUSD-RANGEEXP-SCORED-V1/scripts/`, read-only lineage at
`.worktrees/fx-rangefade-2m-shadow-v1`) hard-codes: `duka_lib.py`
`PRICE_SCALE=1e5` + EURUSD-only URLs; `build_bars.py` `PIP=1e-4`,
`o / 1e5`, band `0.80 < bid < 1.35`; `engine.py` `PIP=1e4`. Copied
verbatim these fail-close every non-EURUSD pair. This lane ports all
three into `scripts/` with every per-pair constant in a probe-proven
`PairConfig` (`scripts/pair_config.py`, `scripts/pair_configs.json`):

- `duka_lib.py` — symbol in every path; decoders take `price_scale`;
  keep-alive polite fetcher preserved verbatim (one HTTPS connection,
  0.15–0.35 s pacing, exponential backoff + connection rebuild on
  429/500/502/503 and network errors, stable-404 → None). The 24-byte M1
  layout invariant (`len % 24`) and the 20-byte tick layout (`len % 20`)
  are asserted in the decoders, and the shared-LZMA-container trap
  (payloads divisible by BOTH 20 and 24 → layout asserts alone cannot
  catch a cross-decode) is documented AND covered by a fixture test
  (`tests/test_duka_lib.py::test_layout_trap_240_bytes_passes_both_asserts`)
  plus content-level cross-checks in the probe.
- `engine.py` — `PIP=1e4` replaced by `Plane.pip_mult` (EURUSD-style 1e4,
  USDJPY-style 100, cohort pairs from probe); fill/force-flat semantics
  byte-compatible with the ancestor. FAMILIES table NOT ported (scored
  machinery is out of data-gate scope — a later lane ports it under its
  own GO). No PnL was computed anywhere in this lane.
- `build_bars.py` — per-pair pip/scale/band; hardened census schema (§5).
- `pair_configs.json` is written ONLY by `probe_pair.py` after
  PROBE_PASS; every consumer fail-closes on a missing/unproven config
  (`load_pair_config` raises `SystemExit("FAIL_CLOSED ...")`).

## 2. Pre-gate registry check (§5.2 item 1) — PASS

Filename-level check (no outcome/report content read): no prior program
cycle built an AUDUSD or USDCAD data corpus. Evidence (both return
nothing outside this lane):

```
find research/control -name "m1_manifest*" -o -name "census*.json" | xargs grep -l "AUDUSD\|USDCAD"   # empty
find research/control -type d -name "AUDUSD" -o -type d -name "USDCAD"                                # only this lane's dirs
```

Plan-level symbol mentions are candidate-universe listings in other
cycles (forex_search_v1, ng2/ng3/ng7 plans, MT5 cost-probe contract
lists) — no Dukascopy corpus, manifest or census predates this lane.
AUDUSD/USDCAD are searched HERE for the first time.

## 3. Probes (§5.2 item 2) — PROBE_PASS both pairs

Window `2024-10-26..2024-11-06` (11 days): EU DST end (Sun 2024-10-27),
US DST end (Sun 2024-11-03), two weekend rollovers, one bounded window.
Per pair: 24 M1 day candle files (BID+ASK) + 288 tick hour files, all
sha256 digests in `data_local/derived/probe_{SYMBOL}.json` (committed;
probe raw bytes one-shot, not persisted).

| Derivation | AUDUSD | USDCAD | Method |
|---|---|---|---|
| price_scale | 1e5 | 1e5 | unique candidate s ∈ {1e3,1e4,1e5,1e6} placing median(raw/s) inside the registered guard band (AUDUSD 0.55–0.85, USDCAD 1.20–1.50); median price 0.65765 / 1.39101 |
| point | 1e-5 | 1e-5 | 1/price_scale |
| pip | 1e-4 | 1e-4 | 10 × point (byte-derived; USDJPY precedent 10×1e-3 = 0.01) |
| band | [0.5209, 0.85] | [1.1057, 1.6751] | union(probe min×0.80 floor-to-pip, probe max×1.20 ceil-to-pip, registered guard) |
| probe prices in band | yes | yes | min/max tick mids recorded (0.65125–0.664505 / 1.3821–1.3959-ish; exact in reports) |
| median tick spread | 1.0 pip | 1.2 pip | scale-free check (median raw spread / 10) |

Invariants (all clean, both pairs): 0 layout violations (len%24 / len%20);
0 M1 OHLC invariant violations (34,560 candles/pair); tick-vs-candle
content cross-check **0 mismatches** (11,613 minutes/side/pair), 0
"candle tradable with zero tick" cases.

DST seam visible in probe bytes (first tick of each transition Sunday,
UTC): AUDUSD 2024-10-27 **21:02:30** → 2024-11-03 **22:00:04**; USDCAD
2024-10-27 **21:01:11** → 2024-11-03 **22:00:03** — the FX Sunday open
tracks US DST (≈21:00 UTC before the US fall-back, ≈22:00 UTC after).
Rollover widening visible per hour (AUDUSD medians: 0.9 pip @12h →
1.3 @21h → 1.5 @22h).

Metadata-only correction: the DST annotation strings in both probe
reports were regenerated from `probe_pair.dst_note` after a wording fix;
the observed `first_tick_utc` DATA was untouched; report sha256 in
`pair_configs.json` refreshed post-patch (config digest test enforces it).

## 4. Full download (§5.2 item 3) — COMPLETE, 0 missing days

2021-01-01..2026-06-30 M1 BID+ASK day bi5 files into
`data_local/duka/M1/{BID,ASK}/{SYMBOL}/` (machine-local, gitignored);
sha256 of every file in `data_local/duka/m1_manifest_{SYMBOL}.json`
(COMMITTED). Machine-wide heavy lock via root
`research/governance.heavy_lock`, heartbeat 30 s, release in `finally`
with FINISHED/FAILED+note; 40-min soft budget per acquisition with
idempotent sha-verified resume (yield + re-acquire instead of holding).

| Pair | Files | Days missing (404) | Compressed bytes | Manifest sha256 (head) | Lock acquisitions |
|---|---|---|---|---|---|
| AUDUSD | 4,014 (2,007 days × BID+ASK) | **0** | 34,336,187 (34.3 MB) | `f869cfa32210194c…` | 3 (chunk 1 killed externally at ~62 min — see §7.2) |
| USDCAD | 4,014 (2,007 days × BID+ASK) | **0** | 34,748,361 (34.7 MB) | `0f9a7df78bcaf481…` | 5 (one SSL-outage FAILED release, recovered by resume — §7.3) |

4,014 files/pair and 0 missing exactly matches the GBPUSD/USDJPY
precedent recorded in plan §5.1. Observed throughput ≈ 1.7–2.3 s/file
(server-latency bound at the polite pacing). Wall clock ≈ 2.0 h AUDUSD,
≈ 2.8 h USDCAD (incl. the two incident pauses).

## 5. Census (§5.2 item 4, §6 hardened schema) — BUILD_PASS both pairs

`scripts/build_bars.py --symbol S` → `data_local/derived/bars15_{S}.parquet`,
`bars1h_{S}.parquet` (machine-local), `census_{S}.json` (COMMITTED,
schema `tracka_census@2`). Panel: first_ts 2021-01-03T22:00Z, last_ts
2026-06-30T23:59Z, 2,007 days, 0 short-record days, days with zero
tradable minutes = 288 weekend + 1 weekday (2021-01-01 holiday) per pair.

Gates + margins (per pair, both true sets identical in shape):

| Gate | AUDUSD | USDCAD |
|---|---|---|
| midweek_tradable_share_gt_0.90 | 0.98611, margin +0.08611 | 0.98607, margin +0.08607 |
| nonpos_spread_share_lt_1pct | 0 minutes, margin +0.01000 | 0 minutes, margin +0.01000 |
| bars15_gt_100k | 130,160, margin +30,160 | 130,102, margin +30,102 |
| duplicate_15m_ts_eq_0 | 0 dup, fail-closed | 0 dup, fail-closed |
| reconcile_p50_within_rounding | max diff 0.0 ≤ 5e-4 | max diff 0.0 ≤ 5e-4 |

Hardened-schema elements verified in both censuses: per-bucket COUNT +
OPEN and CLOSE quantiles (p50/p75/p90/p95/p99, PIPS) for all 8 fixed-UTC
buckets (asia_00_07, london_07_12, ny_overlap_12_16, ny_late_16_21,
rollover_21_22, late_22_24, friday_20_23_open, sunday_open_21_22); no
bucket below the n=100 floor ⇒ no `LOW_SAMPLE_BUCKET` fired; H1 bars
valid iff exactly 4 consecutive 15m bars, H1 `s_open = a_o−b_o`,
`s_close = a_c−b_c` (30,420 / 30,386 valid H1 bars); reconcile recomputed
per-bar medians from the PERSISTED parquet per session — identical to
census p50.

Gap census: interior micro-gaps 6,051 (AUDUSD) / 5,930 (USDCAD) slots
over the panel (~3/day, by-hour histogram + capped entries persisted);
weekday span slots p50 = first 0 (00:00) → last 95 (23:45); Friday→next
open boundaries 286 per pair, gap p50 48.5 h, max 73.25 h / 73.0 h (long
weekends), min 47.25 h / 47.5 h (DST-shifted short weekends). DST-shift
dates visible: 22 in-panel transition Sundays tabulated per pair with
observed first-Sunday-bar UTC hour (22↔21 across the DST regime; both
pairs same pattern — vendor Sunday-open convention recorded, not
assumed). Fixture asserts build-failing and green: rollover bucket n =
3,497 / 3,680 > 0; Sunday-open cell present (n = 312 / 321); synthetic
DST force-flat tests in `tests/test_engine.py` (Sunday opens 21/22/23
UTC shapes).

`price_range_violations` (minutes outside the derived band): **0** for
both pairs — the probe-derived bands hold across the full 2021–2026
panel.

## 6. Tests run (exact commands, final)

```
cd <worktree>/research/control/ERP1-TRACKA-COHORT-1
/Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest tests/ -q
# 20 passed in 0.9s
```

Suites: `test_duka_lib.py` (bi5 layouts, 20-vs-24 trap, symbol paths),
`test_engine.py` (pip parametrization incl. USDJPY-style template;
force-flat day-close across synthetic DST Sunday shapes 21/22/23 UTC;
zero-target smoke — no signal, no PnL), `test_pair_configs.py`
(probe-proven configs, guard coverage, digest consistency,
no-outcome-fields), `test_build_bars_synthetic.py` (H1 grouping law,
micro-gap enumeration, weekend boundary + DST table, reconcile
machinery). The synthetic census suite caught and fixed one real bug
pre-data (§7.4).

## 7. Incident log

1. **LINEAGE-NOTE-1** (observation, recorded, not "fixed" in the
   ancestor): ancestor `build_bars.py` built 15m high/low from the CLOSE
   column (`bb[:,2].max()`/`bb[:,3].min()` under its verified
   open,close,low,high decode order). This port uses the true high/low
   columns. Later parity lanes must not treat the ancestor quirk as law.
2. **External kill of AUDUSD download chunk 1** (~62 min into an 80-min
   budget): the platform stopped the background process without running
   its `finally`, leaving a stale RUNNING lock row (dead pid). Next
   `heavy_lock.acquire` archived the PROVEN-stale row automatically
   (round-2 discipline; no manual surgery) and work resumed idempotently.
   Chunk budgets were reduced to 40 min afterward. No data loss (sha
   resume re-fetched at most the last checkpoint window).
3. **USDCAD chunk 3 SSL outage**: `SSLEOFError` exhausted the fetcher's
   8-retry exponential backoff mid-chunk; process released the lock with
   FAILED + note and exited. Resume (chunk 4/5) completed the corpus with
   0 missing days. No manual retry outside the governance flow.
4. **Synthetic test caught a real census bug pre-data** (`gap_census`
   crashed on year extraction: set-wrapping a list) — fixed and covered;
   also redefined micro-gaps as INTERIOR holes (within a day's traded
   span) so market-closed hours are not counted as gaps; span stats
   reported separately.
5. Probe metadata patch (§3) — annotation strings only, digests refreshed.

## 8. Wording/class compliance

No outcome, no PnL, no signal, no backtest exists in this lane; nothing
here is evidence about any arm. No maker/queue claims, no "earning the
spread", no live-readiness wording. Download posture:
`OWNER_DIRECTIVE_SOURCE_AUTHORIZATION` with `TCU_RISK_DISCLOSED`
(plan §5.1); no accounts, no terms accepted; public datafeed endpoints
only; no license/paywall prompt appeared (would have stopped the lane).
Every artifact carries the data-gate class: raw bytes machine-local +
committed sha manifests; derived planes machine-local + committed census
JSONs; `SINGLE_SOURCE_PANEL` applies to the corpus by construction.
