# PLAN EURUSD-RANGEEXP-SCORED-V1 — formal scored confirmation + short-beta decomposition of the V2 candidate

> Registered 2026-09-24 by A1 under the owner's option **1** ("Scored trên
> dữ liệu đã có", reply to the V2 terminal report). S0 scored cycle. The
> owner's "1" selects the path; it is NOT the verbatim GO (P-8).

## 0. Cycle identity

```text
cycle_id     EURUSD-RANGEEXP-SCORED-V1
class        SCORED CONFIRMATION + SHORT-BETA DECOMPOSITION (no new data,
             no new selection, no parameter changes)
asset        forex (EURUSD only)
budget       6 scored cells MAX (S1..S6 below; every computed cell counts
             in the observed denominator)
S1           n/a (no S1 surface exists in this cycle)
orders       NONE
go_phrase    GO EURUSD RANGEEXP SCORED V1
             (typed verbatim by the owner at this cycle's own gate after
             A7 prelaunch; nothing runs scored before it)
forbidden    editing any terminal verdict; new signal code (engine v1 +
             v2_lib are frozen, sha-verified); touching other cycles'
             surfaces; any order/paper/live surface
```

## 1. Inherited frozen state (verify-on-read, zero drift allowed)

- Engine: `engine.py` sha `cc868402e63d…` (V1/V2 frozen semantics v1:
  opposite-side fills, stress multiplier, force-flat, pips=1e4).
- Candidates: `outcomes/candidates_frozen_v2.json` (FX2-RANGEEXP-C3 config
  digest `020e645dbfec2cdc`, C4 `548bb8606af4beae`) — configs are IMMUTABLE.
- Data: Dukascopy M1 bid/ask 2021-01..2026-06 (manifest-verified copies);
  planes: dev 2021-01..2025-12-31, holdout 2026-01-01..2026-06-30.
- Disclosure: the holdout was UNSEALED once by V2's single candidate check;
  this cycle performs NO selection on it — only decomposition of the
  already-fixed book.

## 2. Scored cells (all preregistered)

```text
S1  reproduction gate: recompute C3 and C4 books on dev (k=1.0/1.5/2.0)
    and holdout (k=1.0/1.5/2.0) under the frozen engine; every metric MUST
    reconcile byte-exact (to the recorded rounding) with V2's committed
    campaign_dev_v2.jsonl + holdout_check_v2.json. Any mismatch = blocker
    (challenges V2's results), never silently accepted.
S2  C3 leg decomposition on dev: long-leg vs short-leg net pips, trades,
    hit, PF; leg symmetry ratio = short_leg_net / total_net.
S3  C3 leg decomposition on holdout (same metrics).
S4  C4 leg decomposition on dev.
S5  C4 leg decomposition on holdout.
S6  drift-flag cell (mechanical, preregistered): for each candidate x
    window, flag DRIFT_DEPENDED when (short_leg_net > 0) AND
    (|short_leg_net| >= 0.5 * total_net) AND (SHORT_ALWAYS_net > 0 on the
    same window). Otherwise NO_DRIFT_FLAG. The flag feeds the paper-forward
    successor's mandatory short-beta control gate; it does not retroactively
    alter the V2 verdict.
```

Baselines recomputed identically per cell window: CASH, LONG_ALWAYS,
SHORT_ALWAYS, RANDOM_MATCHED(seed 20260923).

## 3. Verdict enum (exactly one at close)

`SCORED_RECONCILED_NO_DRIFT_FLAG` | `SCORED_RECONCILED_DRIFT_FLAG` |
`TECHABORT` | `BLOCKED_DATA` | `BLOCKED_AUTHORITY`.

## 4. Governance

- Two-key launch: A7 fresh-context prelaunch (freeze chain, byte-exact
  reproduction dry-run at scored=false, ledger seed) THEN the owner types
  `GO EURUSD RANGEEXP SCORED V1` at this gate. Then cells run, independent
  reproduction + A7 terminal follow, then two-half close.
- Heavy-lock law respected: the scored compute is seconds of vectorized
  work on an existing plane (light), never contending a foreign worker.
- Program accounting: this cycle's ledger row reports reproduction-class
  deltas separately from genuinely new computations (S2–S6 are new scored
  observables; S1 is a reproduction gate and counts as reproduction, not a
  new trial — per the BTC-H4-CONTINUATION-V2 precedent).
- No order/paper/live surface; no secret; S1 boundary untouched.
```
