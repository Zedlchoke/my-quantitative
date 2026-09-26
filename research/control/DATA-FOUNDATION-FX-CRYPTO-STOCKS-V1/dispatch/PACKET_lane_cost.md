# PACKET — L-COST (cost/execution authority — census #4, measurable vs owner-action)

ROLE: A3-class cost-authority lane. WORKTREE:
`/Users/hoangminhlong/my-quantitative/.worktrees/data-foundation-v1/lane-cost`
BRANCH: `orca/dfv1-lane-cost`. Allowed writes: `research/control/DATA-FOUNDATION-FX-CRYPTO-STOCKS-V1/cost_execution/` only. COMMON.md applies in full.

## Objective
One consolidated COST_AUTHORITY_TABLE (per asset × cost component):
component, current evidence class (MEASURED_FROM_BYTES / DECLARED /
STATED_VENDOR / UNMEASURED), value or range, source artifact path, what is
missing, owner action that would make it measured. This is the machine-half
of deliverable D3/D4 — you produce the table + evidence, NOT the runbook
prose (A1 writes that).

## Inputs to consolidate (read-only)
1. DATA-EDGE-UNLOCK-V1 Lane F dossier (third cost census; ten components;
   stress 2.0 frozen): `.worktrees/data-edge-unlock-v1/lane-f/` or
   `research/control/data_edge_unlock_v1/`.
2. FOREX-NG6 P0-F4 + FOREX-NG7 P0-F4 rulings (no citable financing band;
   TD vendor not broker): `.worktrees/forex-ng6|ng7/research/control/`.
3. ERP1 measured cost floors: stressed RT 3.6/4.4 pips partition
   (`research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/forex_program/`),
   P3-A 0.9–1.0 pip measured crossings vs 0.41 threshold (cohort-2).
4. Measured FX spread curves: Dukascopy session/rollover censuses
   (EURUSD p50 0.3 pips; GBPUSD 0.8; USDJPY 0.5; FOREX-SEARCH-V1 staging).
5. Crypto: funding measured 11.798%/yr BTC (EDGE-SEARCH), 11.81/13.96 ETH/BTC
   (SRLV), fees 5bps+1tick DECLARED (SRLV), SOL spread census p50 0.469 bps,
   BNB census (PWS-BNB — ACTIVE, metadata only), mark/premiumIndex measured
   (LIVE-DATA-GATEWAY amendment: 11.5 calls/min, funding parse — metadata
   only).
6. Stocks: EODHD EOD has no execution cost basis; Q-2 conditional-cost law;
   AMIHUD X1 fill-feasibility law (L-SAMV1-3).
7. Prior probe artifacts: `research/control/forex_mt5_cost_probe_2026-09/`,
   `research/control/xauusd_ibkr_probe_2026-09/` — what was measured, what
   stayed NOT_RUN (IBKR gateway unauthenticated timeout).
8. Environment: does `/Users/hoangminhlong/Jts/` (IBKR TWS) and
   `/Users/hoangminhlong/ntws/` exist? `ls` only (directory names, no file
   content reads beyond install markers like a version file name listing).
   This decides whether the runbook's "owner starts TWS" path is one click
   away.

## Ten-component checklist (from DEU-V1 Lane F — verify and restate)
spread, commission, minimum size, tick size, swap/financing per pair,
triple-swap day, margin, slippage/latency, currency conversion, API fees.
For each × asset: current class + what a measured value requires.

## Hard rules
- NO credentials, NO account logins, NO gateway connections — this lane is
  consolidation + `ls`-level presence checks only.
- Every number cites its artifact path; DECLARED/STATED classes must never
  be silently upgraded (Q-8).
