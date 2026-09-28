# REGIME-GATED-COMBO-V1 — G3 FREEZE (pre-PnL)

- frozen_utc: 2026-09-28, BEFORE any combo PnL (fixtures 4/4, dry-run pending)
- legs: G1 leg-inheritance audit PASSED (dt100 package copied byte-match; 6 anchor
  configs identical to DT100 arms.py)
- gate law: state for week W = data strictly before W Monday 00:00 UTC (fixture-pinned)
- tercile cuts: computed on WARMUP distributions only (crypto 2020-09-01..2021-03-31,
  FX 2021-01-01..2021-03-31), machine-written to GATE_TABLE.json — not hand-set,
  not outcome-informed
- allocation table (mechanism-first): FUNDCONTRA∝G1-tercile, CORRBREAK∝G2c-vol,
  PDHLSWEEPFX∝G2f-vol, ASIANRANGE/LONDONMOM∝(4−G2f) calm-tilt, WEEKEND constant 2;
  cap 0.5/leg; G3 trend + G4 corr computed-and-logged but UNUSED (anti-knob law)
- switching: weekly only; cost = Σ|Δw|×RT_leg exactly once per boundary; RT crypto
  12 bps frozen; RT fx = 2× warmup-median Dukascopy spread (machine-frozen)
- baselines (all must be beaten): ALWAYS_ON_6 / RANDOM-gate (seed 20260928, same
  switch discipline) / BEST_LEG (CORRBREAK w=1) / CLOCK-shadow (13-week block
  permutation, seed+1)
- folds: GĐ1 2021-04-01..2022-06-30 · GĐ2 2022-07-01..2023-09-30 · GĐ3 2023-10-01..
  2024-12-31 · GĐ4 2025-01-01..2026-08-31; weeks W-MON 2021-04-05..2026-08-31
- budget 3 cells: anchor (this table) + N1 widened + N2 tightened terciles
- verdict law: PASS_ALL_BASELINES + ≥3/4 folds beat ALWAYS_ON else
  REGIME_COMBO_NO_INCREMENTAL_VALUE (class closes 6th and final)
