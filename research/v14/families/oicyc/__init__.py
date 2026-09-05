"""A14-V14-A8-OICYC -- positioning-cycle-beta family (V14 Phase I, lane i-family-2).

Frozen mechanism (selection_freeze_v14.json family ``A14-V14-A8-OICYC`` +
``research/proposals/v14/a8/OICYC.md``, implemented faithfully -- no
redesign):

* signal = ``CYC_s(T)`` -- the trailing OLS slope of the symbol's daily log
  open-interest change on the contemporaneous LEAVE-ONE-OUT aggregate of
  the other 18 tradeable symbols' daily log OI changes, over the 28 most
  recent paired daily changes whose end-row stamps are <= T (anchor
  ``CYC-28D``, a 29-row window; neighbour ``CYC-14D`` over 14 changes, a
  15-row window); long the lowest-cycle-beta tercile, short the highest;
* causal negative control ``CTL-OISHARE`` = rank on ``SH_s(T)`` -- the mean
  own share of the staged-universe aggregate OI over the 28 most recent
  daily rows <= T -- long lowest-share / short highest-share (descending
  rank presentation); it contains no differencing, no regression and no
  OI-flow direction and is preregistered to be refuted;
* book = median-exit hysteresis terciles: long-entry = lowest ``n//3``
  ranks, short-entry = highest ``n//3``, middle = buffer; a flat symbol
  enters its entry zone's side; a HELD side exits only when its rank
  crosses beyond the median (exit = flip); equal weight per side
  ``min(0.5/n_side, 0.30)``, gross <= 1.0, side membership < 4 skips the
  rebalance and holds the previous book (fail-closed);
* clock = weekly Monday 00:00:00Z discretionary decisions (52 scheduled,
  51 effective after the frozen 1-day calendar-zone purge -- exactly the
  2026-04-20 stamp -- leaving 17/17/17 per fold) with DAILY conditioning
  refreshed from the daily staged-OI path (availability = the row's own
  ``create_time``, read per row); warmup 55 daily rows at the first stamp
  2025-08-25T00:00Z; ONE declared execution lag (slot-open fill at T+15m);
  force-flat at fold boundaries;
* window = blind-S0 screen window 2025-08-22..2026-08-21, folds F0/F1/F2
  per the pinned V12 fold calendar.

DATA AUTHORITY: archived staged OI ``v11_oi_staging_v1``
(``/Users/hoangminhlong/my-quantitative/oi_data/consolidated``, 20 symbols
x 417 daily rows, per-file SHA-256 pinned in
``research/control/v11_run/oi_staging_manifest.json``).  Every real-data
load SHA-256-verifies against the manifest and FAILS CLOSED on mismatch
(``audits.load_oi_by_symbol_verified``).  Bars enter execution/pricing
only; funding is COST ONLY, never in any signal.

STATUS: preregistered CONFIRMATORY (plan Section 1.1 shadow-region entry;
the sign was observed in the V12 ``OILEV-V2-28D-FLOW-W-INV`` control arm).
The status is carried by every payload, by :meth:`OicycPlugin.status_
metadata` and by every gate-runner verdict so the V14 driver records it in
the verdict record and in the observed/published denominator accounting.
All Stage-A gates apply unrelaxed.

SCOPE BOUNDARY: nothing in this package computes PnL, returns or any
scored metric; the plugin plugs into ``research/adapter_v10/`` exactly like
the V13 families (cost_model, decision stamps, folds, universe, one book
per arm, preflight digests) for the V14 driver adapted from
``research/control/v13_run/tools/run_v13_cell.py``.
"""
