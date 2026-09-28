"""Lane E — scored execution module (EVENT-MECHANISMS-V1).

CLEARLY SEPARATED from the frozen book builder (engine/emv1/): this package
CONSUMES the frozen decision-record books read-only and computes the
GO-authorized scored aggregates (the first PnL-domain computation of the
cycle, post owner GO 2026-09-28).

Laws honored here:
- R2-1 raw prices only (records already carry raw entry/exit);
- cost law exactly once per fill: entry fill + exit fill per round trip,
  stress powers read from the FROZEN engine constants (emv1.config);
- no parameter variation: exactly the 3 GO-authorized cells
  (EMV1-A1 anchor H=5, N1 H=10, N2 S2-monitored H=5) + registered
  control/baseline re-evaluations;
- outcomes computed once, recorded honestly, never re-run with tweaks.
"""
