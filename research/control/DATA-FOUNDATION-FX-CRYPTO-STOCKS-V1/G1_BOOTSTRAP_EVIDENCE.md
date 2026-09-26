# G1 bootstrap evidence — DATA-FOUNDATION-FX-CRYPTO-STOCKS-V1

Measured 2026-09-26 (this session), per plan §14 F1/F4/F7.

## Registry (F4)
- Registered via `researchctl cycle register` → ACTIVE_LIGHT, 0/0, shared,
  plan `plans/PLAN_data_foundation_fx_crypto_stocks_v1.md`, branch
  `orca/data-foundation-v1-integration`, head `189c6d23ab…def92820`.
- Registry commit (root main): `64c87239f8d2b46c703cbfad1f9fec1976f1e3bc`
  (registry + events journal + regenerated projection, incl. the prior
  PWS-BNBUSDT projection sync).

## Worktrees (F1)
Base/dispatch SHA for all lanes: `189c6d23ab2a6f50475819cf6df2e2e4def92820`.
All six verified `git worktree list` + per-worktree `rev-parse HEAD` = base,
branch correct, porcelain clean at spawn.

| worktree | branch | du |
|---|---|---|
| .worktrees/data-foundation-v1/integration | orca/data-foundation-v1-integration | 148M |
| .worktrees/data-foundation-v1/lane-fx | orca/dfv1-lane-fx | 148M |
| .worktrees/data-foundation-v1/lane-cx | orca/dfv1-lane-cx | 148M |
| .worktrees/data-foundation-v1/lane-st | orca/dfv1-lane-st | 148M |
| .worktrees/data-foundation-v1/lane-pit | orca/dfv1-lane-pit | 148M |
| .worktrees/data-foundation-v1/lane-cost | orca/dfv1-lane-cost | 148M |

Disk ledger: 7.7 GiB free before integration worktree → 7.6 → … → **6.8 GiB
free after all six** (worktree footprint 888 MB, within the 2.0 GB total cap;
floor 5.0 GiB not approached; abort line 6.0 GiB never crossed). `df`
re-measured before each `git worktree add`. L-A7 worktree will add ~148 MB
later (planned inside the same cap).

## Neighbors (F7 — measured from live registry, not plan §2)
Foreign ACTIVE_LIGHT at G1 (9): PROSPECTIVE-SHADOW-V1, LIVE-DATA-GATEWAY-V1,
CRYPTO-HISTORICAL-REPLICATION-3F-V1, FX-RANGEFADE-2M-SHADOW-V1,
ILLIQ-LOSS-MECH-V1, SHADOW-PAPER-REVIEW-V1, ETHUSDT-OPEN-SEARCH-V2,
ECONOMIC-ROBUSTNESS-PROGRAM-V1, PWS-CX-BNBUSDT-C1.
(Plan §2's "10" counted EDGE-SCANNER-TOOLING-V1, measured ACTIVE at intake
but no longer ACTIVE_LIGHT at G1 — drift recorded, Q-8.)
Live-owner rule (F5) therefore binds: PWS-CX-BNBUSDT-C1, LIVE-DATA-GATEWAY-V1,
FX-RANGEFADE-2M-SHADOW-V1, PROSPECTIVE-SHADOW-V1, CRYPTO-HISTORICAL-
REPLICATION-3F-V1 (+ ILLIQ-LOSS-MECH-V1, ETHUSDT-OPEN-SEARCH-V2 by
heartbeat-recency preference).

## Packets
COMMON + 5 lane packets committed at root main `af7b1c3c…`
(`research/control/DATA-FOUNDATION-FX-CRYPTO-STOCKS-V1/dispatch/`).

## Heavy lock
FREE_PROVEN at dispatch time; lanes are offline surveys with the F10
measure-and-abort rule; no heavy job registered.
