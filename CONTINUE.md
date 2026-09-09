# CONTINUE.md — program checkpoint (Lead-synced 2026-09-09 morning)

Read the LIVE plan of the cycle you serve (highest version per asset in
`plans/`); the canonical registry (`plans/CYCLE_REGISTRY.json` via
`researchctl cycle list`) is the router authority. Measured 2026-09-09
~10:20 VN: **three asset cycles moving.** CRYPTO-V17 post-remediation
(selection re-frozen v2 WKNDLIQ + ATTN-PHASE at `6da1d76`; Q re-run in
flight; next: A7 fresh-context re-audit, then owner GO). STOCKS-FREE-V13
substrate crawl (~2,400/345,152 Form-4 docs, ETA ~Sunday; D2 blocked on
partial substrate). FOREX-FREE-V8 scored-complete
`REJECT_ALL` (falsification-by-control #14, budget 3/6, `07e1b95`);
close chain in flight (twin reproduction → A7 terminal → Lead sync:
forex 42/42, program 236/239, registry TERMINAL). **FOREX-FREE-V9**
(`plans/PLAN_forex_v9.md`, owner-requested 2026-09-09 — the
PPP-deviation frontier) is written and PLANNED_NOT_STARTED: bootstrap is
BLOCKED until the V8 close chain lands (plan §0). GO phrases V17/V13
registered-unconsumed; V8's was consumed at its gate (`720decb`) and is
dead; V9's registers with its plan. This file is a derived checkpoint,
not an authority. Machine: heavy phases queue under the machine-wide
lock (NOT_RUN_RESOURCE_CONFLICT, never contention; V13's SEC
silence-window yielding is the standing pattern); root commits are
atomic single-purpose pathspec only (P-10).

## Measured program state

- CLOSED 2026-09-07 evening: `FOREX_FREE_V7_REJECT_ALL` (terminal
  `f59ea0c`; cross-economy spillover sham-reproduction, cluster #12 —
  with V6 this closes the whole reaction-direction class) and
  `STOCKS_FREE_V11_REJECT_ALL` (terminal `9d3a061`; amendment
  cadence-latency falsified by shuffled-chain control, cluster #13;
  mandatory filing-event lane died measured at D2, novelty 0.219 vs
  momentum_63s). Both A7-confirmed from bytes, reproduced byte-identical.
- CLOSED 2026-09-08 07:45 VN: `V16_REJECT_ALL` (terminal `46db31d` +
  canonical close `9d62d5c`; first governance-native cycle — gate + lock
  + registry exercised end-to-end; aggTrades frontier measured-exhausted
  at the daily clock on BTC/ETH; sub-daily untested).
- Program totals (ledger authority, P-9): **233 published / 236 observed,
  0 survivors; S1 SEALED everywhere** (crypto 155/158, stocks 39/39,
  forex 39/39). Failure registry 55 entries --verify PASS.
- CRYPTO-V16 A7T ADDENDUM (2026-09-08 08:12 VN): the terminal A7 audit
  ran 27 min after canonical close → `V16_TERMINAL_APPROVED_0_FAIL`
  (`2762cd7`, a7_terminal_v16.json; anchors' gates recomputed
  exact-to-r12; the margins-misattribution defect adjudicated
  verdict-neutral). The V16 close chain is now A7-terminal-complete.
- RUNNING (ACTIVE_LIGHT): CRYPTO-V17 (A1 bootstrap `ff33929`; first
  report GO for P0; no scored cell — A7 prelaunch NOT_RUN, owner GO
  absent per P-8) and STOCKS-V12 (A1 bootstrap `02b4ac2`, first report
  `e0dcb0f` GO for P0, census-only P0 lane dispatched `ac06951`; both
  lanes pre-checked fundable; GO phrase registered, unconsumed). Still
  awaiting owner dispatch: forex `PLAN_forex_v8.md` (real-rate frontier
  under the FRED key).

## Owner-keyed doors (Lead-measured current state)

- 2026-09-07 ~18:05 VN: **FRED_API_KEY PRESENT in `.env`** (owner placed
  it; length 32, value never read into repo/chat). Functional probe by
  Lead: one public GET to api.stlouisfed.org (series DFF, limit 1) ->
  HTTP 200, observation (2026-09-03, 3.63). Frozen plans keep their
  as-measured-at-freeze wording (handbook §3.1); this file carries
  current state. Effect: the FRED real-rate lane is preregistered by
  `plans/PLAN_forex_v8.md` (mandatory lane 1, full license/PIT/vintage
  audit in P0 before any proposal). Key presence is not data authority.

## Standing owner items

- F-A7-T-1 kernel debt (gate-equality quirk, verdict-neutral, carried
  from forex V6 close).
- EODHD $19.99/mo: keep active — STOCKS-V12 is dispatched and running.
- Dashboard: BUILT, merged to main (`effbe42` + logo), pushed; app opens
  via `LabDashboard.command`; registry `plans/ACTIVE_CYCLES.json`
  regenerates on each collector run (worktree-existence semantics —
  closed-cycle wording is the known follow-up).
