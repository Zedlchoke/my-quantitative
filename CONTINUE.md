# CONTINUE.md — STOCKS-FREE-V5 TERMINAL (REJECT_ALL) ENTRY STATE

Read `PLAN_stocks_v5.md` completely. It is the fresh-context Stocks
authority for any next stocks cycle; `PLAN_stocks.md` (V2/V2R/V3) and
`PLAN_stocks_v4.md` are closed historical authorities and are not rewritten.

## Verdict lineage (must agree with `research/wayfinder/MAP.md`)

- V2 effective verdict: `STOCKS_FREE_V1_REJECT_ALL` (W1
  `1063782`), V3: `STOCKS_FREE_V3_REJECT_ALL` (W1 `586f9fe`),
  V4: `STOCKS_FREE_V4_REJECT_ALL` (A7T CONFIRMED, W1 `dfa099a`).
- V5 terminal verdict: `STOCKS_FREE_V5_REJECT_ALL` (A7T
  `STOCKS_FREE_V5_REJECT_ALL_CONFIRMED`, audit head `bc5827e`;
  `STOCKS_FREE_V5_W1 = 0ecca232caf6cee21a84d78579681e336b616388`);
  statistical denominator 21 observed / 21 published (V2 6 + V3 6 + V4 6
  + V5 3). S1 SEALED_UNTOUCHED. No paper/live/orders. Workers zero.

## What V5 established

- Data Fusion V1 core adopted into the stocks tree pre-freeze
  (c6a0576 byte-identical); canonical PIT bridge
  `research/assets/stocks/pit_conditioning.py` (owner adjudication after a
  two-controller concurrency incident — see event_log
  V5_CONCURRENCY_INCIDENT_RECORDED / V5_OWNER_ADJUDICATION; lesson L8:
  one cycle = one A1 thread).
- SEC EDGAR conditioning authority built and audited (410-filer panel,
  3.82M instant records, A1-A8 PIT audit PASS); FRED/ALFRED + FINRA +
  Alpha Vantage remain BLOCKED pending owner key/signup decisions.
- F1 root cause (unremediated by design): the bridge's single-vintage
  semantics collapse per-tick sector coverage — all four SEC-conditioned
  proposals died pre-selection. A vintage-age-bounded aggregation variant
  is a candidate preregistration for a FUTURE owner plan.
- Section 1.1 shadow front door is now MEASURED CLOSED for vol-level
  re-entry as preregistered (shape-gate rho 0.319 > 0.20).
- SFV5-A6-H2-CROSS-SECTOR-COUPLING: FAMILY_REJECT — anchor fails 10/15
  Stage-A gates; the nominal-price placebo control outperforms the anchor
  on the identifying metric (preregistered falsification fires).

## Entry conditions for the next thread

1. Read `PLAN_stocks_v5.md` (closed authority for V5) and the cumulative
   forbidden inventory `research/control/stocks_free_v5_run/forbidden_family_inventory.json`.
2. Append V5 families to `research/wayfinder/HYPOTHESIS_LEDGER.md` at the
   start of the next cycle (Lead Engineer index).
3. Any new cycle needs a fresh owner plan (V6 or a Data-Fusion remediation
   plan preregistering vintage-age-bounded aggregation before any scoring).
4. Heavy cap 1 on the 8 GB host; full pytest runs alone.
