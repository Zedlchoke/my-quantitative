# FUTURES-DATA-10SYMS-V1 — intake (2026-10-02)

Owner instruction 2026-10-02 (verbatim task header preserved in
`dispatch/OWNER_DIRECTIVE_2026-10-02.md`): independent DATA LANE — check and
collect futures data for exactly 10 symbols NQ, ES, CL, NG, GC, SI, 6E, 6J,
6B, 6A. NOT a strategy GO. No scored cells.

## Hard non-goals (owner's)

No PnL/backtest numbers, no scored cells, no S1, no paper/live orders, no
subscription/paid-package activation, no data purchase, no push/merge, no
paywall/CAPTCHA/network-filter circumvention, no ETF/spot substitution for
futures prices, no unexplained CONTFUT-as-chain claims. 6J is quoted JPY/USD
(notation must be recorded, never silently inverted).

## Re-measured intake (2026-10-02, this session)

- Root checkout `/Users/hoangminhlong/my-quantitative`, branch `main`,
  HEAD `6770d790863d25c77a13b66967964433110a80fd`.
- Dirty tree (owner's, preserved untouched, not staged, not committed):
  modified `research/control/DATA-FOUNDATION-SIXSOURCE-V1/ibkr_fx/sessions_index.jsonl`;
  untracked `sanitized_fix_window_*.json`, `sanitized_rollover_window_*.json`,
  `research/control/SANDBOX-OVERFIT-3ASSETS/{data,out}/`, `research/control/SLEEVE-FX5-100K-V1/`.
- Cycle registry: 85 cycles; no live futures-data cycle; FX-FUTURES-FRONTIER-V1
  TERMINAL `FX_FUTURES_FRONTIER_V1_BLOCKED_TRANSPORT` (CME direct estate
  SNI-keyed sinkholed — evidence `research/control/fx_futures_frontier_v1/`);
  DAYTRADER-100-V1 and PORTFOLIO-COMPOSITE-12ASSETS-100K-V1 TERMINAL, their
  probe dirs are immutable evidence. None reopened.
- Heavy lock: `FREE_PROVEN` (no holder, no flock) at intake.
- Disk: 23 GiB free of 228 GiB (root volume). Session byte ceiling
  published BEFORE any download: **2.0 GiB hard cap on new raw bytes;
  abort-on-breach in code; ≥20 GiB free floor preserved** (3 GiB headroom).
- TWS paper socket `127.0.0.1:7497`: TCP OPEN (nc probe this session).
- Python: `.venv/bin/python`, ib_insync 0.9.86, ibapi 10.45.1, pandas 3.0.5.
- Neighbors live at intake (ACTIVE_LIGHT): PROSPECTIVE-SHADOW-V1,
  LIVE-DATA-GATEWAY-V1, CRYPTO-HISTORICAL-REPLICATION-3F-V1,
  FX-RANGEFADE-2M-SHADOW-V1, ILLIQ-LOSS-MECH-V1, SHADOW-PAPER-REVIEW-V1,
  ECONOMIC-ROBUSTNESS-PROGRAM-V1, EVENT-MECHANISMS-V1, REGIME-GATED-COMBO-V1,
  DAILY-EXPLORATORY-V1. None of their surfaces written.

## Registration status (disclosure — SIXSOURCE precedent)

**No cycle registered in `plans/CYCLE_REGISTRY.json` for this session** —
bounded read-only data reconnaissance under the owner's direct instruction
(authority order #1), no scored surface, no GO phrase, no budget to account,
registry files not touched. Precedent: `DATA-FOUNDATION-SIXSOURCE-V1`
(2026-09-28) and standalone probe control dirs. Nothing here flips any
lifecycle or ledger row. One API worker at a time (single client id, no
heavy lock acquisition — downloads are network-bound, not CPU-heavy; the
machine-wide heavy lock is left free for real heavy jobs).

## Past evidence carried (re-measured this session, never assumed)

1. CME direct transport: SNI-keyed in-path block, resolver sinkhole
   (FX-FUTURES-FRONTIER-V1 A2 lane). Re-measured: `cme_check/`.
2. IBKR TWS paper 7497 works read-only (PC12A probe 2026-09-30).
3. CONTFUT daily TRADES "6 Y" for CL/NG/BRENT = continuous series with
   41–63% flat-OHLC zero-volume bars pre-2025, front-conId identity, no roll
   rule — NOT a tradable chain (PC12A F-1). Not used as contract data here.
4. Expired FUT resolution: quarterly months < ~1y back errored 200 in that
   session (oldest resolvable 202512 then); must re-measure per symbol with
   includeExpired=True + explicit month.
5. Quote entitlement ≠ history entitlement: CL delayed error 10168, NG 354/
   10167 measured; historical HMDS probes separately.
6. IB API footguns: error 10372 (timestamp echoed into contract month — use
   conId+exchange for history), error 10339 (CONTFUT history forbids end
   time), pacing (≥15s identical request, ~60 hist req/10min ceiling).

## Lane plan (single controller, sequential stages, checkpointed)

- S1 `identity`: per symbol — active FUT chain via reqContractDetails;
  expired walk-back with includeExpired until 3 consecutive misses; record
  conId/localSymbol/expiry/multiplier/minTick/currency/tradingHours/
  timeZoneId per contract. Client id 9210, readonly=True.
- S2 `quotes`: per front contract — live snapshot (type 1) vs delayed
  (type 3), error codes recorded; separate from S3.
- S3 `histprobe`: per symbol front — reqHeadTimeStamp + 1-bar probes:
  daily TRADES, hourly, 1-min, daily BID/ASK, with whatUse recorded.
- S4 `sample` + `bulk`: bounded samples then checkpointed batch (daily full
  life per resolvable contract first, then hourly, then 1-min bounded
  window), pacing 3s between requests, raw JSON+gzip under governed root,
  manifest with sha256/params/UTC timestamps/row counts/date ranges.
- S5 `validate`: coverage per contract/month, interior gaps, duplicates,
  forming-bar detection, volume=0 synthetic detection, timezone/DST audit,
  roll calendar from expiry info only (no lookahead), settlement vs trade
  separation, cost table per symbol (IBKR public schedule fetched+hashed;
  CME official pages expected BLOCKED_TRANSPORT — recorded, not bypassed).
- S6: independent verification (subagent re-derives identity/coverage/roll
  from raw files) + FINAL_REPORT.md + HANDOFF (zcode_orch_v3_handoff@1).

Governed raw root (outside git, never committed):
`/Users/hoangminhlong/.my-quantitative-data/futures-10syms-v1/raw/`

## Boundary summary

Read-only TWS API (`ib.connect(readonly=True)`); unique client ids 921x;
no account ids in artifacts (redaction filter on logs; account endpoints
never called); no orders; no subscriptions; single download worker.
