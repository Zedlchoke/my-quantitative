# M1 — NQ session-σ dispersion proxy re-derivation on cache_v3 (G11) — MEAS-NQ, wave 3

- Round **FUTURES-5SYM-PRESCORED-20261005**, lane **MEAS-NQ**, 2026-10-05. PREP-only, **descriptive only**
  (no conditional-on-signal returns, no PnL, no gate adjudication).
- Worktree `/Users/hoangminhlong/my-quantitative/.worktrees/futures-5sym-prescored/prep`, branch
  `prep/futures-5sym-prescored-20261005`, HEAD `b2d086ca50996c628ec0373c4a3e8c2f2387c742`. No commits by this lane.
- Reads: committed cache_v3 (`FUTURES-SIX-READINESS-20261004/nq/cache_v3/`) in the same read posture as the
  k6gate NQ lane — **ADOPT-D9 UNSIGNED ⇒ cache_v3 stays canonical-CANDIDATE**; consumption is per-cycle cited
  (`D8_D9_DECISION_SHEET.md`), never treated as ratified. FREEZE consumption: **NOT_RUN** (out of scope for this lane).
- Locks: `researchctl.py locks inspect` = **FREE_PROVEN** immediately before and after each panel scan; the
  single-shot annotated-panel read ran **16.9 s wall** (< 2 min ⇒ canonical heavy lock not required, per lane law).
- Generator: `m1_rederive_dispersion.py` (this dir). Outputs: `m1_session_sigma_v3.json`,
  `m1_per_session_rederived.parquet` (4,219 rows).

## 1. The pre-recovery defect G11 discloses (read from the citation chain)

`HYPO_GAPS.md` G11: *"NQ dispersion proxy defect — session-σ re-derivation on the recovered v3 series
(pre-recovery defect disclosed) … feeds any NQ MDE refresh (NQ-F2/NQ-F3 inherit)"*.

The disclosed defect lives in the census power-honesty print
(`FUTURES-TEN-HYPO-PREP-20261004/es_nq/HYPOTHESES_ESNQ_R3.md` §7, F5-K2; restated in `SPEC_NQ.md` §7):

> "**NQ** median ann vol **17.83%** ⇒ session σ ≈ **112.3 bp** [OBSERVED, NQ_a1_regimes
> yearly[].vol_ann_pct median; **pre-recovery-series defect disclosed**] ⇒ **MDE ≈ 38.7 bp**"

The proxy's source, `FUTURES-DEEPRESEARCH-V2-20261003/analysis/NQ_a1_regimes.json` (schema `NQ_a1_regimes@1`),
was built on the **pre-recovery series**, where:

- the **2020-03-23..2020-05-29 vendor hole** left the hole sessions NaN/thin: panel
  `depleted_sessions = 77` (51 of them in 2020 alone) — year-2020 `vol_ann_pct = 33.5434%` was computed on a
  depleted year, i.e. **the highest-vol window of the era was structurally under-weighted**;
- the v2 chain carried the **wrong 2020-06-01 roll** (`NQH0_2020` dead-held **49 sessions**, dte −73), so the
  daily series feeding the annualized vol regime was built across a dead handoff
  (`before_after_2020.json`, sha256 `83753151…2302`, cited).

The v3 repair (alias view + true 2020-03-19 crossover) restores the hole as real sessions and retires the
dead handoff; the corrected full-era aggregate tables are `nq_f3_rebuild_a1a2.json` (k6gate M4,
`depleted_sessions 77 → 27`, 2020 max-DD 32.28% → 34.12%).

## 2. What this lane re-derived (independent implementation, verbatim recipe law)

Recipe (mirrored from the committed k6gate M3, `k6_compute.py` §M3, inputs swapped to nothing — same cache_v3,
independent code): single-shot read of `nq_annotated_1m_v3.parquet` (7 columns); sort `(contract, dt)`;
`r1 = log-close diff within contract`, first bar of each contract NaN **on the full panel, restricted to the
held chain afterwards** (order load-bearing — see §5); held-chain restriction = inner merge on
`(contract, session_date)` with `held_volume_k5_v3.parquet` (4,219 sessions / 66 rolls); per held session:
`absret_mean/median/sd_bp` (full session), `rth_absret_median_bp` (`in_rth` flag — the cache's era-correct
annotation, 08:30 CT → era close 16:15 CT through 2015-09-18 then 16:00 CT), `rth_5min_sd_bp` (5-min
non-overlapping RTH closes, `minute_of_day // 5` buckets, ×√78 dailyization). DST fall-back absolute-24h quirk
**PRESERVED AS MEASURED** — session boundaries consumed from the cache annotation, never re-derived here.

**Input integrity:** 4/4 files read re-hash **match** `adopt/cache_v3_hashes.json` pins
(`nq_annotated_1m_v3` `e233da66…`, `nq_held_daily_v3` `b7bd830a…`, `nq_sessions_v3` `30bc1ec3…`,
`held_volume_k5_v3` `99ff1ca1…`).

## 3. Diff old (committed k6gate artifact) vs new (this re-derivation)

Old = `FUTURES-K6GATE-PREP-20261004/nq/session_dispersion_v3.json` + `…_per_session.parquet` (committed
evidence, cited, never overwritten). New = this lane's independent re-derivation from the same committed parquets.

| axis | comparisons | result |
|---|---|---|
| JSON blocks: per_year × 17 years × 5 measures × {median,p25,p75} = 255, full_era = 15, hole_window = 15 | **285** | **285 MEASUREMENT_IDENTICAL** (bit-exact float equality, 0 deltas ≠ 0.0), 0 DEFECT_CORRECTED |
| per-session parquet, all 7 measures × 4,219 sessions | 4,219 rows | **max abs delta = 0.0** on every measure; 0 rows differ |

Classification law: `MEASUREMENT_IDENTICAL` = bit-exact (delta 0.0, rel tol 1e-9); `DEFECT_CORRECTED` = value
changed by the v3 repair; `NEW_MEASUREMENT` = no prior committed value. Headline reproduced values (now
independently confirmed): full-era |1m ret| mean **1.706 bp**, median **1.088 bp**, sd **1.986 bp**; RTH-only
median **2.109 bp**; RTH 5-min dailyized sd **71.122 bp**; hole window 2020-03-23..05-29 = **49 sessions**,
|1m ret| mean median **3.605 bp** (vs 1.71 full era — the window the pre-v3 aggregates skipped).

## 4. The σ proxy itself — old (pre-recovery) vs new (v3)

Law (census): `σ_bp = median_over_years( std(daily held log rets, year) × √252 ) × 100`.

| quantity | pre-recovery (`NQ_a1_regimes.json`) | v3 re-derivation (`nq_held_daily_v3.parquet`) | delta | classification |
|---|---|---|---|---|
| median year vol_ann | 17.8268% (2015) | 17.8268% (2015) | 0.0 | **MEASUREMENT_IDENTICAL** |
| **σ proxy** | **112.2984 bp** | **112.2984 bp** | **0.0 bp** | **MEASUREMENT_IDENTICAL (median-invariant)** |
| year-2020 vol_ann | 33.5434% (51 depleted sessions) | **34.8153%** (hole restored) | **+1.2719 pct-pts** | **DEFECT_CORRECTED** |
| all other 16 years | — | — | 0.0 (bit-exact) | MEASUREMENT_IDENTICAL |

**M1 finding (the G11 answer):** the census σ proxy is **defect-invariant at the median**: the defect moved the
2020 tail (+1.27 annualized pct-pts; the depleted 51 sessions were the crash-recovery window) but the
median-across-years lands on 2015 in both the pre-recovery and v3 builds, so **σ ≈ 112.30 bp survives the v3
repair unchanged** — the disclosed defect is real and is corrected in the per-year table, but it does **not**
move the number the census consumed. Any NQ MDE refresh that consumes the median-year σ therefore inherits
**no delta**; any refresh that consumes a 2020-inclusive stratum (e.g. era K-V4 COVID view) inherits the
corrected 34.82% (σ_2020 = 219.2 bp dailyized) instead of 33.54%.

## 5. NEW measurement — per-session-class decomposition (SPEC_NQ session law)

No prior committed value exists for these ⇒ all rows `NEW_MEASUREMENT` (descriptive; median/p25/p75 of
per-session |1m ret| stats across the 4,219 held sessions):

| class (SPEC_NQ §1/§3 law) | sessions with obs | absret mean bp (med/p25/p75) | absret median bp | absret sd bp |
|---|---|---|---|---|
| **RTH** (`in_rth`; 08:30 CT → era close 16:15/16:00 CT) | 4,193 (99.4%) | 2.754 / 2.057 / 3.854 | 2.109 | 2.548 |
| **Globex** (17:00 CT prev-day open → 08:30 CT, outside break) | 4,219 (100%) | 1.256 / 0.944 / 1.733 | 0.939 | 1.379 |
| **maintenance boundary** (`in_break`; 16:00/16:15 → 17:00 CT window) | 532 (12.6%) | 1.156 / 0.770 / 1.669 | 1.067 | 1.073 |

RTH dispersion runs ≈ 2.2× the Globex class at the per-session mean — the session-σ proxy (a whole-session
daily σ) blends both classes; a per-class σ law for any future NQ family parameterization is now measurable
from `m1_per_session_rederived.parquet` but is **not** invented here (parameter law is owner territory).

## 6. Recipe-order note (why one intermediate run differed, then was corrected)

An intermediate implementation restricted to the held chain **before** computing `r1`; that yields first-held-bar
NaNs where the committed recipe (diff on the full panel, then restrict) carries the contract-internal diff into
the first held bar — 4 cells shifted by ≤ 7.2e-4 bp. The committed order was adopted verbatim and all 285
comparisons went bit-identical. The intermediate run is disclosed here for reproduction honesty; no artifact of
it is consumed downstream.

## 7. Limitations

- Descriptive re-derivation of a dispersion **proxy**; not a per-family MDE table (those stay post-freeze
  arithmetic — `SPEC_NQ.md` §7). The MDE refresh arithmetic that consumes this file is `m3_mde_refresh.md`.
- cache_v3 is consumed as canonical-CANDIDATE (D9 UNSIGNED); if D9 ever fails, these numbers keep their k6gate
  citation chain but lose their starting-point status.
- The maintenance-boundary class has bars in only 532/4,219 sessions (era-dependent: the break window is
  bar-less most of the era) — per-session class stats on that class are computed over few observations for
  early-era sessions; medians across sessions are still well-defined.
- Session-class decomposition uses the cache's own `in_rth` / `in_break` / `session_date` annotations
  (v3 measured construction, incl. the DST preserved-quirk rows); no independent re-derivation of session
  boundaries was performed (that would be a new chain build — out of lane scope).

— End M1. Descriptive only; nothing herein gates, scores, or ratifies anything.
