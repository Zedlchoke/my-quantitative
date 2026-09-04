"""A13-V13-A5-LIQEPIS -- liquidity episodicity family (V13 Phase I, lane i-family-2).

Frozen mechanism (selection_freeze_v13.json + research/proposals/v13/a5/
LIQEPIS.{md,json}, implemented faithfully -- no redesign):

* signal = normalized Herfindahl ``H_i(T) = sum_b (q_b / Q)^2`` of 15m
  dollar-volume shares (``q_b = close x volume``) over the trailing 2688
  completed-bar slots (28d anchor) / 5376 slots (56d neighbour), uniform
  baseline ``1/2688``; every slot must be present AND available
  (fail-closed; one missing slot refuses the symbol at that stamp);
* book = long the bottom tercile (lowest H, smooth turnover) / short the
  top tercile (highest H, bursty), 6 symbols per side, equal weight 1/12,
  gross 1.0, ties broken by symbol id ascending, middle tercile flat;
* arms: ``LIQEPIS-28D`` (anchor) / ``LIQEPIS-56D`` (neighbour) /
  ``LIQEPIS-SIGN-INV`` (causal negative control: the sign-inverted book);
  preregistered falsification: if the inversion passes the incremental gate
  while the anchor passes, the anchor is a tilt artifact and the family is
  falsified (see :mod:`research.v13.families.liqepis.gate_runner`);
* clock = weekly Monday 00:00:00Z decisions; ONE declared execution lag:
  fills at the close of the first completed 15m bar strictly after the
  decision stamp (Monday 00:15Z close; the +1-delay stress fills at the
  00:30Z close); holding 7 days, force-flat at fold boundaries;
* folds = frozen chronological F0/F1/F2 over the blind-S0 window
  2025-08-22..2026-08-21 with the 1-day purge (the measured V13 convention:
  exactly one stamp, 2026-04-20, falls inside the F1 purge zone, leaving 51
  effective Mondays -- A9-F feasibility audit; selection_freeze_v13).

BARS-ONLY family (A9-F implementation risk LOW): no OI, mark-price or
funding-rate field enters any signal; funding settles natively on held legs
as a COST only, identical across arms.

SCOPE BOUNDARY: nothing in this package computes PnL, returns or any scored
metric; real data are READ-ONLY workspace files
(``/Users/hoangminhlong/my-quantitative/catalog_live_crypto/data/``).
"""
