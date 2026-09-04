# A9-F Feasibility Audit — FOREX-FREE-V3, Phase V3-D2

- Auditor: A9-F (independent; audit only, no repairs)
- Date: 2026-09-04 (machine_date_u)
- Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v3/d2-a9-feasibility`
- Branch: `orca/forex-free-v3-d2-a9-feasibility`, HEAD `ac83dc80dce6664e92e09f30ec4b4be100cc7608` (matches required prefix `ac83dc8`), porcelain empty at start
- Machine-readable companion: `a9_feasibility.json` (same directory)
- Scope: PLAN_forex_v3.md section 8 A9-F. **No PnL computed** — schedule counts and cost arithmetic only.

## 0. Snapshot replay (STEP 0)

Authorized snapshot copied read-only from
`/Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v2/e-exec-1/data_raw/forex_free_v1/`
into `data_raw/forex_free_v1/` (gitignored; verified nothing under `data_raw/` staged or committed).

Manifest: `forex-free-v2/integration/research/control/forex_free_v1_run/staged_data_manifest.json`,
section `digests_exec2`. The 156 entries decompose as 152 price files under
`data_raw/forex_free_v1/` plus 4 control files under `research/control/forex_free_v1_run/`
(`w1_freeze.json`, `data_probe/{request_manifest,data_quality_final,canonical_manifest_final}.json`).

**Replay verdict: PASS — 156/156 matched, 0 mismatched, 0 missing.**

Measured H1 coverage: 2020-01-29/30 .. 2026-09-02 00:00Z for all 7 pairs.

## 1. Measured schedule facts (real snapshot)

Decision bar = completed H1 bar at 16:00 America/New_York wall time, Mon-Fri only
(session gate Sun 21:00 -> Fri 16:00 NY). DST stamps verified on data: 16:00-NY bars
stamp only at 20Z (EDT) / 21Z (EST).

| Metric (per pair) | EURUSD | GBPUSD | AUDUSD | NZDUSD | USDJPY | USDCHF | USDCAD |
|---|---|---|---|---|---|---|---|
| Weekday 16:00-NY bars, full window | 1652 | 1657 | 1656 | 1656 | 1653 | 1655 | 1654 |
| F1 (2020-03-01..2022-05-01) | 551 | 551 | 549 | 551 | 549 | 549 | 549 |
| F2 (2022-05-01..2024-07-01) | 519 | 521 | 521 | 519 | 519 | 521 | 519 |
| F3 (2024-07-01..2026-09-02) | 560 | 563 | 563 | 563 | 562 | 562 | 563 |
| Bars strictly before 2020-03-01 | 22 | 22 | 23 | 23 | 23 | 23 | 23 |

- Panel-complete (all-7-pairs) weekday decision dates: **1,650** (F1 549 / F2 519 / F3 560; 22 before F0).
- Warmup activations measured (weekday decision-bar series): 10 sessions -> 2020-02-10..13
  (pre-fold; A4-P1 supported); 63 bars -> 2020-04-27..29 (A5-P1, inside F1); 126 bars ->
  2020-07-23..27 (A5-P2, inside F1); 220 NY-days -> 2020-12-02..04 (A6-P1, inside F1).
- A4-P2 Wednesdays: full window 337-342/pair; scored with 26-week warmup (first 2020-08-05):
  **311-315/pair** (F1 91 / F2 111-113 / F3 109-111); with 52-week warmup (first 2021-02-03):
  285-289/pair (F1 65).
- Data quality: provider weekend-stamped 16:00-NY bars exist (EURUSD 34 Sat / 172 Sun wall-16:00)
  — outside the session gate, excluded from all counts above; 63-68 missing weekday 16:00 bars
  per pair over F1-F3, concentrated on Fridays (~58-59, provider stretches e.g. Fridays
  2021-07-09..2021-10-01); 17-24 NY-days per pair carry internal H1 hour gaps (A6-P1
  day-validity, fail-closed).

Cost basis (frozen invariant ladder, 10,000 USD-unit notional): base RT 3.0 bps = 3.00 USD;
tier-1.5 RT 4.5 bps; tier-2.0 RT 6.0 bps. Gross-edge band assumption: daily-or-slower FX
per-trade gross dispersion ~20-200 bps for 5-21 session holds; documented predictive
components ~2-10 bps per trade; carry accrual at in-window policy differentials tens of bps
per multi-week hold.

Macro quorum: 4 of 6 proposals condition on adopted macro series (>= 3 required) — MET.

## 2. Verdicts

| hypothesis_id | Verdict | Decisions measured (schedule) |
|---|---|---|
| FXFV3-A4-P1 | FEASIBILITY_PASS (conditional on P3 macro gate) | NOT_MEASURABLE_LOCALLY (BIS event-driven; price-side warmup/fills PASS; proposal band ~120-180 pair-events plausible, unverified) |
| FXFV3-A4-P2 | FEASIBILITY_PASS | 311-315 scored Wednesdays/pair (~2,180 anchor decisions panel; F1 91 / F2 111-113 / F3 109-111) |
| FXFV3-A5-P1 | FEASIBILITY_PASS | ~1,589/pair from 2020-04-28 activation (~11,100 panel) |
| FXFV3-A5-P2 | FEASIBILITY_PASS | 1,650 panel-complete dates; ~1,524 post-warmup evaluations (~10,668 pair-day) |
| FXFV3-A6-P1 | FEASIBILITY_PASS | ~1,590/pair from 2020-12-03 activation (~11,000 panel) |
| FXFV3-A6-P2 | FEASIBILITY_PASS | ~1,652/pair (~11,400 panel; ~1,900 trades est., matches claim) |

All 40/arm invariant floors cleared by 40x+ where locally countable; no fold has zero
decisions on any locally countable schedule.

## 3. Findings by severity

**HIGH (1)**
- A4P1-F1 — FXFV3-A4-P1's event-driven decision count and per-fold event breadth cannot be
  verified on the authorized data on hand (no macro snapshot exists;
  `NOT_PROVEN_ON_LIVE_FETCH` per `data_authority_v3.json`). Feasibility is conditional on the
  P3 freeze / Q data-hash macro gate; the proposal declares the BLOCKED_DATA_OR_SELECTION
  fallback. No audit stop: price-side coverage, schedule mechanics and cost arithmetic pass.

**MEDIUM (6)**
- A4P1-F2 / A4P2-F2 — A4 lane cost-labeling error: "3.00 USD (6 bps of notional)" — 3.00 USD
  on the 10k unit is **3.0 bps** RT (the invariant base ladder); 6 bps is the tier-2.0 RT.
  USD figure correct; error conservative (overstates break-even).
- A4P1-F3 — tier-2.0 (6.0 bps RT) attainable only in the upper half of A4-P1's own predicted
  5-30 bps gross band.
- A4P2-F1 — internal turnover contradiction: cadence argument says 2-5 flips/pair-year
  (=> 14-35 RT/year panel) but the turnover line claims ~25 flips/pair-year (~175 RT/year).
  Stated turnover overstated; effect conservative (actual drag lower).
- A6P1-F1 — trade band low edge (3 RT/pair-year => ~130 aggregate) falls below the proposal's
  own 140 aggregate trade floor (declared INDETERMINATE handling).
- A6P2-F1 — thinnest break-even headroom of the six: base RT 3.0 bps per 5-day trade vs a
  plausible 2-7 bps daily lead-lag band (clears at/above mid-band; tier-2.0 at band top).
  Not INFEASIBLE_COST_HEADROOM — base-tier clearing at plausible edges is possible and the
  break-even diagnostic is mandated — but cost-dominance is the family's most likely failure
  mode (disclosed ex ante).
- A6P2-F2 — direction degeneracy: leave-one-out means share 5/6 components, so all 7 pairs
  trade the same sign nearly every day; the inherited `usd_corr_abs_ceiling` 0.3 and the
  >=25% long/short balance check are likely to bind (disclosed ex ante).

**LOW (5)**
- A4P2-F3 — F1 "~65 weekly decisions" claim matches the 52-week neighbour window; the anchor
  26-week window measures F1=91.
- A4P2-F4 — trade-flip cadence macro-dependent; F1 trade population could fall below
  fold_populated_min_trades 30 at the band's low end (INDETERMINATE by declared rule).
- A5P1-F1 / A5P2-F1 — expected-decision estimates under-count measured schedules
  (conservative direction).
- A6P1-F2 — activation measured 2020-12-02..04 (claimed ~2020-11); F1 residual ~1.4y, not
  ">1.5y". No floor impact.
- DATA — provider weekend-stamped 16:00-NY bars and Friday-weighted 16:00-bar gaps
  (63-68/pair) plus 17-24 internal-gap NY-days require exact session-gate and fail-closed
  handling at implementation.

## 4. Blockers

None. Snapshot replay 156/156 PASS; HEAD verified; no data stop.

## 5. Handoff

A1 receives this audit for D2 selection under the frozen rubric (novelty/rescue, data
authority, control identifiability, feasibility, source-to-test trace, implementation risk,
lexicographic tie-break; max 2 families / 6 scored cells). Implementation risk highlights
per proposal are in `a9_feasibility.json` (`proposals[].checks.8_implementation_risks`).
