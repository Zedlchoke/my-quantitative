# A9-F2 — OI-Positioning RE-AUDIT (post-staging)

- Role: D2b-A9-F | Branch: `orca/v11d2b-a9f-oireaudit` | HEAD at audit: `0c0ea9c8cff4440b879566335c66e9693a65bb8c`
- Completes the single open item of prior audit `bc4bd4c` (D2-A9-F): "staged snapshot has NO OI → OI group UNAVAILABLE".
- Scope: schedule-only. **No PnL, no scored return series, no forward returns anywhere.** Budget 0/12 untouched. Audit-only — no repairs proposed.

## Verdict: **PASS** for the OI-positioning family (weekly book; canonical candidate `a8_prop2`)

**Canonical frozen-spec delta verified:** `a8_prop2` (A8-V11-OILEVER-DELEV) = weekly Monday 00:00Z decisions; feature = 28d log OI-growth from daily-last-snapshot OI (last strictly-before anchor, ≤48h staleness); **with cross-sectional momentum-orthogonalisation as a frozen spec element** (per-stamp cross-sectional OLS of OI-growth on trailing-28d return; residual = traded signal). Mandated by the A1 rho addendum: OI_GROWTH28|MOM28 pooled rho 0.5651 > 0.5 (FAIL); DEF/LOT/ILLIQ/funding pairs all PASS.

Prior audit's sole OI blocker (zero OI coverage) is removed. The a6 monthly OI variant stays breadth-blocked exactly as before (min-6-names/leg unsatisfiable on 9 eligible) — carried forward, not re-litigated.

## Task 1 — Independent raw-zip spot verification (staging report NOT trusted)

Symbols: BTCUSDT (large), AVAXUSDT (mid), ONGUSDT (small). Recomputed from `oi_data/metrics_daily` zips:

| symbol | files | days present | internal gaps | rows/day (min/med/max) | nulls | nonpositive OI | parquet last-row = raw last-row |
|---|---|---|---|---|---|---|---|
| BTCUSDT | 417 | 417/417 | 0 | 285/288/288 | 0 | 10 | 417/417 |
| AVAXUSDT | 417 | 417/417 | 0 | 285/288/288 | 0 | 10 | 417/417 |
| ONGUSDT | 417 | 417/417 | 0 | 285/288/288 | 0 | 12 | 417/417 |

**CONFIRMED.** All nonpositive raw rows sit in a 2025-07-21 16:20–16:25 UTC source outage window, are mid-day (never a day's last row), leaked 0 into the parquets, and precede the earliest feature anchor (2025-07-28) — zero contamination. Full 20/20 consolidated census: 417 rows each, strictly increasing, 0 nulls, 0 nonpositive, SHA-256 matches `oi_staging_manifest.json` 20/20.

## Task 2 — PIT semantics of `create_time`

Empirics: day files run 00:00…23:55 in 5m steps; 364/417 BTC days start at 00:00; no 24:00-label rows; chain is seamless D:23:55 → D+1:00:00 → `create_time` is the **snapshot instant (bucket-START label)**. Residual end-label ambiguity cannot be 100% excluded from file shape alone.

**PIT rule (robust to either reading):** at a decision stamp T, use the **last completed row with `create_time` strictly before T** (never a same-instant row). For Monday 00:00Z stamps that is Sunday's final snapshot (median 23:55; max observed staleness 8.083h, all ≤48h). Bars side: last completed 15m bar with `ts_event` strictly before T; gate fills are first completed bars strictly after the decision (cost inputs only).

## Task 3 — Feature feasibility at the weekly stamps

Spec verified: `ln(OI[T]/OI[T-28d])` at Monday 00:00Z stamps 2025-08-25 … 2026-08-17 (52 stamps), then per-stamp cross-sectional regression of OI-growth on trailing-28d return; residual = signal.

- **Per-stamp eligible counts: 20 / 20 / 20 (min/median/max) — 20 of 20 symbols at every one of the 52 stamps (1040/1040 symbol-stamps feature-complete).**
- Orthogonalisation computable at every stamp; cross-sectional R²(OI-growth~MOM28) range 0.0–0.8088 (construction diagnostic only), consistent with A1's pooled rho 0.5651 — the orthogonalisation is load-bearing, not cosmetic.

## Task 4 — Schedule-only floors (frozen gate reused, not forked)

Weekly quintile proxy identical to the prior audit (same pseudo-characteristic, DV-above-median eligible set, 60d history, terminal forced-flat; schedule SHA `68e54a10…` byte-identical to the prior `a8_prop2_scheduleonly` counterfactual). Only delta: signal availability now supplied from measured OI-feature existence (fraction 1.0). Gate: `research/v11/cost_feasibility.py::evaluate_schedule_cost_feasibility` via import.

| floor | threshold | observed | status |
|---|---|---|---|
| decisions per 365d | ≤60 | 52.576 | PASS |
| median intended holding days | ≥3 | 21.0 | PASS |
| base cost drag / gross (annualised) | ≤8% | 2.475% | PASS |
| stressed cost drag / gross | ≤12% | 4.180% | PASS |
| max per-symbol turnover share | ≤25% | 16.67% (SOLUSDT-PERP) | PASS |

Verdict **PASS** with **zero** unavailable metrics.

## Task 5 — Compute estimate (full-window OI-growth build)

Consolidated path (20 OI parquets + 20×15m bars, 52 stamps, orthogonalisation): **wall 1.52 s, peak RSS 248 MB** of 8 GiB. Worst-case full raw-zip rebuild (8340 zips): ~8.6 s extrapolated. Trivial; no stronger machine needed.

## Blockers

None.

## Carried flags

- HIGH (carried; not a floor fail): quintile book trades 1 name/leg on the 9-symbol DV-above-median set — Stage-A concentration gates are the binding downstream risk.
- MEDIUM (spec-freeze obligation): the traded feature uses the daily last-snapshot OI series; frozen spec must pin the strictly-before lookup, the ≤48h staleness gate and the momentum-orthogonalisation step.
- LOW (carried): instrument defs are a single end-of-window static snapshot; acceptable since declared cost floors equal staged values.
- LOW (new, informational): 2025-07-21 16:20–16:25 UTC zero-OI outage rows exist in raw feeds; excluded from parquets and outside every feature anchor.

## Assumptions

Candidate window 2025-08-22..2026-08-21 (unchanged); snapshot-instant label reading (verdict invariant to it); trailing returns used only as declared feature inputs; raw recomputation spot-checked on 3/20 symbols plus full 20/20 consolidated census with SHA verification.

Scratch evidence: `research/audits/v11p/a9f2_scratch/` (spot_verify_raw, pit_semantics, feature_feasibility, schedule_gate_oi, compute_estimate, all20_census, run_oi_schedule_gate.py).
