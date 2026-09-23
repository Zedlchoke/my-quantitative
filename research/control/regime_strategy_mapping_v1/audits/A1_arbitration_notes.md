# A1 arbitration notes — REGIME-STRATEGY-MAPPING-V1 integration

A1 records every cross-lane arbitration here. Lanes never edit this file.

## 2026-09-23 — A5 findings

- **A5-F1 (MEDIUM, BUY_HOLD docstring vs behavior)**: ACCEPTED as proven.
  Arbitration: correct the FORK'S DOCSTRING to describe implemented
  behavior (strategy_exit/stop exits occur mid-fold under BUY_HOLD targets;
  re-arm only at next fold start). Behavior NOT changed: the fork must stay
  byte-equivalent to V2 (proven by the engine-equivalence gate,
  `evidence/engine_equivalence.json`), and buy-hold is a REFERENCE metric
  that is never a scored arm in this cycle. Disclosure consequence: any
  buy-hold reference number quoted from V2 or this cycle follows this
  behavior and must be labeled "trend-exit buy-hold reference", not pure
  hold-to-end.
- **A5-O1 (LOW, ATR fallback at i==13)**: NOTED, no code change. The
  fallback `atr14[i]` when `atr14[i-1]` is NaN can only trigger at the
  first finite-ATR bar (i==13) — unreachable under warmup 192 (all cells)
  and immaterial to every arm. Recorded for the audit trail.

## 2026-09-23 — A6 arbitration points (from the A6 handoff)

1. **V2 reference pins**: arm B's engine-equivalence pins are the V2 stored
   tier-1 totals of JEV_ONLY_ROUTER / ALWAYS_ON_MEAN_REVERSION /
   ALWAYS_ON_TREND per cell, read from the TERMINAL V2 ledgers (read-only)
   and cross-checked against the V2 A7 terminal audit. The V2 "trade
   count" pin (978/1060/343) counts COMPLETED TRADE CYCLES (round trips,
   one per position open→close). `position_switch_count` in this cycle is
   defined identically: the number of COMPLETED TRADE RECORDS (position
   opens) in the arm's ledger — mapping recorded pre-outcome as required.
2. **F matcher invested fraction**: CONFIRMED — the shuffled matcher's
   `invested` tolerance applies to the ROUTED TARGET series per fold (the
   arm's own targets), not to a global label set. The forked matcher
   (`rsmv1/arms.py::random_matched_paths`) matches on the label path and
   tolerance-checks occupancy/switches/dwell/invested on the derived
   target path; A6's freeze language is the authority.
3. **Specialist library freeze ordering**: CONFIRMED — the specialist
   library freeze (A4 proposal -> A1 freeze) lands BEFORE any arm C
   execution; cmd_scored refuses without the GO token regardless.
