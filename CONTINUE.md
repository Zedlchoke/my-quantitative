# CONTINUE.md — program checkpoint (Lead-synced 2026-09-08 morning)

Read the LIVE plan of the cycle you serve (highest version per asset in
`plans/`): crypto `PLAN_crypto_v16.md` (RUNNING — scored execution),
stocks `PLAN_stocks_v12.md` (awaiting owner dispatch), forex
`PLAN_forex_v8.md` (awaiting owner dispatch). This file is a derived
checkpoint, not an authority.

## Measured program state

- CLOSED 2026-09-07 evening: `FOREX_FREE_V7_REJECT_ALL` (terminal
  `f59ea0c`; cross-economy spillover sham-reproduction, cluster #12 —
  with V6 this closes the whole reaction-direction class) and
  `STOCKS_FREE_V11_REJECT_ALL` (terminal `9d3a061`; amendment
  cadence-latency falsified by shuffled-chain control, cluster #13;
  mandatory filing-event lane died measured at D2, novelty 0.219 vs
  momentum_63s). Both A7-confirmed from bytes, reproduced byte-identical.
- Program totals (ledger authority, P-9): **227 published / 230 observed,
  0 survivors; S1 SEALED everywhere** (crypto 149/152, stocks 39/39,
  forex 39/39). Failure registry 53 entries --verify PASS.
- RUNNING: crypto V16 — two-key complete 2026-09-08 07:35 VN (A7
  `CRYPTO_V16_S0_LAUNCH_AUTHORIZED` + owner exact GO; an earlier
  form-failing attempt was correctly refused); scored cells execute
  serially under the machine-wide heavy lock.

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
- EODHD $19.99/mo: keep active while stocks cycles run; cancel when
  stocks idle (currently idle until V12 dispatch — owner decision point
  before dispatching V12).
- Dashboard build agent: plan approved (`plans/PLAN_dashboard.md`),
  worktree `.worktrees/governance/lab-dashboard` @ `orca/lab-dashboard`
  ready, NOT started — owner dispatches with the prompt they hold.
