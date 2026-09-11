"""FOREX-NG1 I-phase cell runners (task forex-ng1-i-runners).

Cell runner for the two frozen families of the FOREX-NG1 selection freeze
(research/control/forex_ng1_run/selection_freeze.json):

- FXNG1-A5-P1  release-order opening-follower print drift (own pair)
- FXNG1-A4-P2  trailing-YoY extrapolation CPI deviation (acceleration)

LAWS ENCODED (frozen; this lane implements, never invents):

- every arm parameter comes from the committed frozen proposals
  (research/control/forex_ng1_run/d1/proposals/proposal_A5_P1.json /
  proposal_A4_P2.json) and the selection freeze -- nothing here retunes a
  threshold, horizon, clock, or seed (P-15);
- decision grid = daily 16:00 America/New_York on the pinned staged spot
  calendars (V9 frozen representation, inherited from
  research.assets.forex_ng1.spot_series);
- signals are vintaged as-of reads (P-1..P-6 chain); the A5 order state is
  interval-strict-before on evidenced publication instants (fail-closed);
- dual-book accounting with the frozen cost ladder 1.5 bps/side x
  {1.0, 1.5, 2.0}, tier 2.0 PRIMARY, charged exactly ONCE per fill (entry
  and exit are separate fills -- V8 kernel law inherited);
- folds frozen 2018-04..2020-06 / 2020-07..2022-10 / 2022-11..2025-04,
  force-flat at each boundary;
- DRY-RUN ONLY in this lane: decision records carry identity, timing,
  direction, units, fold and cost-contract constants -- never prices, PnL,
  PF, expectancy, stress or breakeven at any depth (the leak scanner in
  ``scanner`` enforces this recursively).  Outcome computation is gated
  behind an explicit scored mode that this lane never enables.
- the Stage-A R1-R6 evaluator (``evaluator``) is a pure fail-closed
  function over metric inputs; at this lane it is exercised ONLY by
  synthetic fixtures, never on real outcomes.
"""
