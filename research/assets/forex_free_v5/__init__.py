"""FOREX-FREE-V5 family-module package.

Implements the SELECTED, FROZEN proposal of the cycle (selection_freeze.json,
``selected.family_id = FXFV5-A6-P1``) against the inherited V3 kernel
architecture (family API contract of
:mod:`research.assets.forex_free_v3.scored_runner`):

* ``family_a6p1`` -- FXFV5-A6-P1 pre-release position-avoidance window
  (research/control/forex_free_v5_run/i1_inputs/PROPOSAL_FXFV5-A6-P1.json,
  materialized from git object c82403d8c6f39a9d31c276db4d8510b70313c6cd).

Exactly three scored arms (selection_freeze.json ``selected.arms`` +
the I1 directive):

* ``anchor``    -- counter-trend daily 16:00-NY trade (minus sign of the
  trailing 10-NY-day return sum) whose holding window [F, X] spans the
  evidenced CPI release instant a (F < a < X mechanically enforced) and
  holds NO post-release session.
* ``neighbour`` -- sham-calendar causal control: identical reversal law
  anchored to +7-calendar-day-shifted availability stamps whose windows
  contain no evidenced release of ANY evidenced economy (invalid anchors
  dropped fail-closed, counted as ``sham_dropped``).
* ``control``   -- stale-calendar proximity isolation: identical law
  anchored to each economy's PREVIOUS evidenced clock (c_prev); first
  clock per economy has no predecessor and is skipped (counted).
* ``benchmark_treatment`` is additionally exposed per the KERNEL contract
  (``scored_runner.BENCHMARK_ARM``: booked inside a scored anchor cell for
  the incremental alpha, never a scored cell); its schedule IS the frozen
  stale-calendar (c_prev) law -- the packet's
  ``incremental_test.bench_schedule_id`` = FXFV5-A6-P1-bench.

Factory-only namespace mirroring the inherited V3/V4 family-module
discovery pattern: families are registered as ``family_id=module.path``
and expose ``run_arm(arm, data_paths, macro_reader, freeze_token)``.  No
frozen kernel file is modified; the V3 kernel
(research/assets/forex_free_v3/{accounting.py,scored_runner.py}) is
imported READ-ONLY for booking/validation.

Factory-only lanes: synthetic fixtures in tests, no scored PnL on real
data, no network, no new data authority.
"""
