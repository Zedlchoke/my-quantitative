# CYCLE VERDICT — FX-MAJORS-SEARCH-V1 (TERMINAL, 2026-09-24)

- Branch: `orca/fx-majors-search-v1-integration` @ terminal anchor; plan
  `plans/PLAN_fx_majors_search_v1.md`; owner instruction opened the cycle
  (NOT a GO); no scored execution occurred (exploratory campaign class,
  same as V2).
- Data: per-pair Dukascopy M1 bid/ask 2021-01..2026-06 — 4,014 files/pair,
  0 missing; probe ALL_PROBE_PASS (USDJPY 1e-3 scale PROVEN against ticks);
  census BUILD_PASS per pair (GBPUSD 131,488 15m bars, spread p50 0.8 pips;
  USDJPY 131,676 bars, 0.5 pips; 0 non-positive-spread minutes).

## VERDICTS (per pair, one enum each)

### GBPUSD: `CANDIDATE_PENDING_PROSPECTIVE_VERIFICATION` — with conviction

FX2-RANGEEXP (wide-prior-day-range fade) **generalizes to the second pair**,
and the holdout half-year was choppy (both naive direction baselines lost):

| window | C3 | C4 |
|---|---|---|
| dev 2021–2025 | +8,525.2 pips, PF 1.642, 6/6 folds + | +7,852.1, PF 1.578, 6/6 folds + |
| **holdout 2026-H1 (ONE look)** | **+164.2 @1.0 (PF 1.12), +105.3 @1.5, +46.4 @2.0** | **+234.9 @1.0 (PF 1.18), +175.7 @1.5, +116.5 @2.0** |

Baselines all negative on the same window: LONG −132.9, SHORT −47.1,
RANDOM −1,546.9. The mechanism earned in both directions in a directionless
half-year — the strongest evidence in the program so far that this is an
effect, not a drift bet. Still S0: pending prospective verification.

### USDJPY: `CANDIDATE_PENDING_PROSPECTIVE_VERIFICATION` — thin, drift-flagged for the successor

Preregistered SUCCESS met (net>0 @1.0 AND @1.5) by both frozen candidates,
but with full honesty:

| window | PDHLOC-C2 | RANGEEXP-C3 |
|---|---|---|
| dev 2021–2025 | +3,573.6 @1.0, PF 1.306 | +3,128.1 @1.0, PF 1.355 |
| **holdout 2026-H1** | **+35.4 @1.0 (PF 1.03), +3.6 @1.5, −28.1 @2.0** | **+30.6 @1.0 (PF 1.04), +2.5 @1.5, −25.6 @2.0** |

**LONG_ALWAYS +532.5 @1.0 on the same window** — USDJPY rallied hard
(carry-driven yen weakness) and the naive long beat both candidates ~10–17×
on absolute net; both candidates DIE at 2× stress. The pass is technically
valid and mechanically real (PF>1 both), but the window cannot separate
edge from long-beta. **The paper-forward successor MUST carry the JPY
long/carry-beta control alongside the short-beta control from the EURUSD
scored cycle.**

## Campaign accounting

- 96/96 trials observed (12 families × 4 configs × 2 pairs), D2 =
  OWNER_WAIVED_EXPLORATORY in every record.
- Positive after cost @1.0: GBPUSD 7/48, USDJPY 12/48; @1.5: 5/48 and 9/48.
- USDJPY freeze deviation disclosed pre-holdout: mechanical rank-2
  (PDHLOC-C4) was an outcome-identical duplicate of rank-1 (opposite_exit
  never fired in 5y — positions are day-flat before a full-range cross);
  freeze took rank-1 + the distinct-mechanism rank-3 (RANGEEXP-C3).
- RUN-1 of this campaign was the only run; no voids; deterministic.

## Governance state

- A7 prelaunch: **AUTHORIZED** 0 blocking (independent byte-exact re-run of
  all four frozen books; USDJPY duplicate deviation substantiated; 32+ raw
  files sha-verified per pair; leak guards hold) — `audits/a7_prelaunch_audit.*`.
- F1 (uncommitted fxm_build manifest-key fix) committed before the holdout;
  tree clean at execution; run_count = 1.
- S1 SEALED_UNTOUCHED; no orders/paper/live; GO phrase
  `GO FX MAJORS SEARCH V1 SCORED` never consumed → extinguished UNCONSUMED
  at close (no scored-execution set exists).
- Cross-cycle note: program ledger denominators are being advanced
  concurrently by other Lead sessions; this cycle's stamp records its own
  delta (+96/+96 exploratory trials, forex) and per-cycle forex totals;
  program-total reconciliation follows the registry-conflict union law.
- Next authorized path (owner decision): extend the paper-forward program —
  GBPUSD-RANGEEXP (strong), EURUSD-RANGEEXP (strong + scored), USDJPY
  (thin; carry-beta control mandatory).
