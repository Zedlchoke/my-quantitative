# COST AUTHORITY TABLE — DFV1 L-COST (cost/execution census #4, 2026-09-26)

Companion of `cost_authority_table.json` (machine-readable, authoritative for
values). Lineage: FOREX-NG6 P0-F4 + FOREX-NG7 F4 (censuses #1–2) → DEU-V1
Lane F ten-component dossier (census #3, stress 2.0 frozen) → **this table
(census #4)**, which adds the 2026-09-26 IBKR TWS SIM probe, the ERP1
measured cost floors, and the crypto measured books. Classes:
`MEASURED_FROM_BYTES / DECLARED / STATED_VENDOR / UNMEASURED` (+ qualifiers
`SINGLE_SAMPLE`, `CONSERVATIVE_DEFAULT_NOT_MEASURED`, `FROZEN`,
`NOT_SUBSCRIBED`, `REPORT_ONLY`). No class was upgraded anywhere.

## Asset verdicts

| Asset | Verdict | What is actually measured |
|---|---|---|
| FX majors (EUR/GBP/USDJPY/AUD/NZD/USDCAD) | `BLOCKED_BROKER_COST_AUTHORITY` (A7 F-C1: components 3,4,5,6 need account-bound bytes; none exist) | vendor-book spread censuses (Dukascopy M1 bid/ask corpora) + **tick = 0.5 pip MEASURED account-bound (IBKR SIM, all 5 pairs, 2026-09-26)** + stressed RT floor 3.6/4.4 pips (AUDUSD/USDCAD) |
| XAUUSD | `PROBE_PAUSED` (NOT_RUN_TWS_UNAVAILABLE at freeze; not retried 2026-09-26 per lane law) | tick 0.01 USD/oz (measured, beat stated 10x); single-sample spread 0.923 bps (connectivity proof only); commission/storage/borrow STATED_VENDOR (official pages) |
| Crypto perps (BTC/ETH/SOL/BNB) | `PARTIAL_MEASURED` | funding per pair MEASURED (BTC 11.798%/yr; ETH 7,305 settlements; SOL fapi conflict-excluded; BNB n=7,261 PASS-WITH-CAVEATS); SOL spread census MEASURED (n=13.8M, p50 0.469 bps); commission DECLARED 5 bps + 1 tick; keyless API = 0 fee |
| Stocks (EODHD EOD) | `BLOCKED_ACCOUNT` for execution cost — EOD channel has **no** bid/ask/fill/spread fields | nothing cost-bearing; Q-2 conditional-cost law + L-SAMV1-3 X1/X2 fill-feasibility law are the binding execution contract |

## Ten-component checklist × asset (condensed; full detail in JSON)

| # | Component | FX majors | XAUUSD | Crypto | Stocks |
|---|---|---|---|---|---|
| 1 | spread | MEASURED (vendor book: EURUSD p50 0.3 / GBPUSD 0.8 / USDJPY 0.5 pips; AUD 0.9 cond / USDCAD 1.1 cond; rollover p99 7.8–16.7; Sunday 3.0–6.8). Broker side: NOT_SUBSCRIBED (bid/ask = −1 ×5 pairs) | MEASURED single sample 0.40 USD/oz = 0.923 bps (proof only) | MEASURED SOL p50 0.469 bps (n=13.8M); BTC/ETH/BNB NOT_RUN | UNMEASURED (channel cannot carry it; Q-2: cost must condition on vol/price/liquidity — open ran 3.33×/3.35× midday) |
| 2 | commission | UNMEASURED (zero account-bound bytes; NG6 F4) | STATED_VENDOR (tiered official page) | DECLARED 5 bps + 1 adverse tick (frozen CHR3F; not fill-validated, Q-8) | UNMEASURED (per-share fee = tax on low prices, Q-2) |
| 3 | minimum size | UNMEASURED (contractDetails minSize = null ×5, measured attempt) | STATED_VENDOR (Campus lesson, Jan 2022, indicative) | UNMEASURED (exchangeInfo filters not pulled) | UNMEASURED |
| 4 | tick size | **MEASURED 0.00005 = 0.5 pip ×5** (IDEALPRO CASH, 2 runs) ⇒ min crossing ≥0.5 pip ⇒ ≥1.0 pip @k=2.0 = **2.4× the frozen 0.41 threshold** | **MEASURED 0.01 USD/oz** (vs stated 0.001 — 10x conflict, measured wins) | UNMEASURED (PRICE_FILTER not pulled; implied by convention) | UNMEASURED |
| 5 | swap/financing per pair | UNMEASURED — **binding PASS-minimum**; NG7 F4: no citable financing band exists anywhere authorized | STATED_VENDOR (storage 0.10%/yr; borrow tiers) | **MEASURED**: BTC 11.798%/yr (85.89% positive; constant 1.508% underestimates 7.8×), ETH floor-exact 7,305, SOL conflict-excluded, BNB n=7,261 | UNMEASURED (borrow; FINRA NMS ToU INCOMPATIBLE = terminal) |
| 6 | triple-swap day | UNMEASURED — binding PASS-minimum; CONSERVATIVE-DEFAULT-NOT-MEASURED 3× weekday carried | UNMEASURED (same conservative default) | MEASURED natively (8h funding carries interval changes, e.g. FTX week) | UNMEASURED |
| 7 | margin | UNMEASURED, REPORT-ONLY (whatIf forbidden) | UNMEASURED (page not retrievable) | UNMEASURED (leverage brackets not pulled) | UNMEASURED |
| 8 | slippage/latency | UNMEASURED — `DECLARED_UNMEASURED` erosion-only line; FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK | UNMEASURED (paper fills = zero evidential weight, RULE) | UNMEASURED (owner directive: no order-book/flow inference from candles) | UNMEASURED — **L-SAMV1-3 X1/X2 law: volume=0 bars unfillable; notional ≤ participation fraction; unfillable skipped AND counted** |
| 9 | currency conversion | UNMEASURED (fee); pip↔bps factors measured (mid 0.66864 / 1.35137) | UNMEASURED | UNMEASURED (USDT-quoted) | UNMEASURED |
| 10 | API fees | UNMEASURED (no account-attached schedule; free FX delayed not enabled) | STATED_VENDOR (same official page) | DECLARED 0 (keyless posture) + rate-limit headroom MEASURED (11.5 calls/min live-verified vs soft 1200 weight) | DECLARED (EODHD owner entitlement; earnings channel 403 dead) |
| + | stress multiplier | **FROZEN 2.0** pre-outcome (census #3 component 10) | FROZEN 2.0 (same) | n/a (funding-path stress measured: 24.7% settlements negative in downtrend) | n/a |

## Stats (components by class per asset)

| Asset | MEASURED_FROM_BYTES | DECLARED | STATED_VENDOR | UNMEASURED | extras |
|---|---|---|---|---|---|
| FX majors | 2 (spread-vendor-book, tick) | 0 | 0 | 8 | 2 FROZEN (stress 2.0; P3-A 0.41 threshold) |
| XAUUSD | 2 (spread single-sample, tick) | 0 | 3 | 5 | — |
| Crypto | 3 (+1 metadata-only extra) | 2 | 0 | 5 | — |
| Stocks | 0 | 1 | 0 | 9 | — |

## The two frozen numbers every future proposal must clear

1. **ERP1 measured cost floor (vendor book):** AUDUSD conditional crossing
   p50 0.9 pips (last-6m) / 1.0 (whole dev); USDCAD 1.1 / 1.2 → **×2.0
   stressed RT = 3.6 (AUDUSD) / 4.4 (USDCAD) pips ≈ 5.5 / 3.7 bps**. A
   declared gross band must exceed these to produce a positive ceiling, and
   clear ~2× (≈7–9 pips intraday) to be non-fragile. Across all 38 forex
   failure entries, NO honest measured gross intraday premium ever reached
   that line.
2. **P3-A frozen threshold:** conditional crossing ≤ **0.41 pips @k=2.0**.
   Measured 0.9–1.0 (p25 0.8) → `CEILING_NEGATIVE_VETO` pre-PnL; and the
   IBKR tick measurement (min spread ≥ 0.5 pip ⇒ crossing ≥ 1.0 pip @k=2.0)
   makes the condition **arithmetically unattainable at IDEALPRO** — P3-A is
   measured-dead at this venue by tick geometry, no rescue.

## IBKR / TWS presence finding (ls-level only; no content read)

- `/Users/hoangminhlong/Jts/` EXISTS — the live TWS estate: `jts.ini`,
  extension dir containing `tws.20260926.105853.ibgzenc` +
  `audit.20260926.105906.ibgzenc` (TWS ran **today** ~10:58–10:59),
  `launcher.log` mtime 2026-09-26 21:40.
- `/Users/hoangminhlong/ntws/` EXISTS — a second TWS install (`jts.ini`,
  extension dir with `tws.20260916.135943.ibgzenc`, `Settings/`),
  last used 2026-09-16.
- Consequence: the runbook's "owner starts TWS" path is **one click away**,
  and the 2026-09-26 probe already proved socket 7497 + **Read-Only API
  active server-side** (order-channel reads rejected 321). The binding
  constraints are NOT installation: (a) the SIM account lacks two-sided FX
  market data, (b) no Activity/Flex statement has ever been exported.

## What a Read-Only API session unlocks (exactly, per VERDICT_session2 §owner-documents + Lane F option A)

1. `contractDetails.minTick` → component 4 (already measured ×5).
2. `reqMktData` streaming bid/ask → component 1 **only after** the owner
   enables free FX delayed (Manage Data Subscriptions) — today it returns
   BID/ASK = −1 (NOT_SUBSCRIBED).
3. `contractDetails.minSize` → component 3 **but CASH returns null** — the
   statement/fill granularity is the real source.
4. Activity/Flex (or XML) statement with FX trades + a Wed–Sun overnight
   window: Trade+Commission rows → 2; Interest Accruals per position → 5
   (LONG/SHORT); dated Wednesday 3× rows → 6; accrual timestamps + statement
   timezone (17:00 ET roll) → rollover clock; fills → 8 (report-only);
   Account Summary InitMarginReq/MaintMarginReq → 7 (REPORT-ONLY;
   whatIf/order channels stay forbidden).
5. One TWS restart before re-probing (session-slot stalls after ~20 probe
   sessions were the measured failure mode).

## Cheapest single owner action per asset

- **FX majors:** Option A of census #3, now partially executed — export ONE
  Activity/Flex statement (any IBKR account, window with FX trades +
  overnight positions) and enable free FX delayed market data. The probe is
  one command; templates frozen in `xauusd_ibkr_probe_2026-09/` and reused
  verbatim 2026-09-26. This alone converts components 2/3/5/6/7/8 from
  UNMEASURED to measured and satisfies the FOREX-NG7 reopening condition
  class.
- **XAUUSD:** resume the preregistered probe once TWS API is up (handshake
  diagnosis needs new preregistration per plan §3) — spreads distribution +
  margin lines from an account the owner demonstrably runs.
- **Crypto:** nothing owner-gated for the measured pairs; the only open
  technical items (BTC/ETH/BNB spread census, exchangeInfo filters, BNB
  Vision cross-check) are keyless and belong to the cycles that own those
  corpora. Commission tier stays DECLARED until an account channel exists.
- **Stocks:** no lawful free path to execution cost (FINRA terminal;
  EOD-channel cannot carry it) — the cheapest honest action is an owner
  broker-statement export IF the owner holds any equities account; otherwise
  stocks stay `BLOCKED_ACCOUNT` for execution cost, and any equities family
  is restricted to illiquidity-proxy designs under the X1/X2 law.
