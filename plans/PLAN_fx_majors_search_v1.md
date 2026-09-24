# PLAN FX-MAJORS-SEARCH-V1 — transfer the EURUSD search design to GBPUSD + USDJPY

> Registered 2026-09-24 by A1 under the owner instruction "okay mở cycle
> tiếp theo dành cho GBPUSD và USDJPY". S0 exploration ONLY. The instruction
> opens the cycle; it is NOT a scoring GO (P-8).

## 0. Cycle identity

```text
cycle_id     FX-MAJORS-SEARCH-V1
class        STRATEGY SEARCH (exploratory S0; after-cost PnL permitted only
             after the per-pair data gate passes)
asset        forex (GBPUSD + USDJPY; two instruments, ONE cycle, separate
             per-pair verdicts)
budget       12 families × 4 configs × 2 pairs = 96 planned = 96 MAX
S1           SEALED_UNTOUCHED
orders       NONE
go_phrase    GO FX MAJORS SEARCH V1 SCORED (typed only at this cycle's own
             gate after A7 prelaunch; the opening instruction is NOT a GO)
forbidden    editing any terminal verdict; other cycles' surfaces; any
             order/paper/live surface
```

## 1. Design (transferred from EURUSD-OPEN-SEARCH-V2, same laws)

- `D2 = OWNER_WAIVED_EXPLORATORY` (campaign class the owner has run since
  the 2026-09-23 directive; never recorded as PASS).
- Windows frozen NOW: dev 2021-01-01..2025-12-31; **holdout 2026-01-01..
  2026-06-30 — untouched by ANY search on these two pairs**. Disclosed
  cross-pair contamination: the researcher knows FX2-RANGEEXP succeeded on
  EURUSD in the same window; that is inherent to a generalization test.
- Folds F1–F6 identical to V2; G3 = ≥4/6 folds net>0.
- Gates: G1 net>0 @k=1.0; **G2 PF ≥ 1.20**; G3; G4 net>0 @k=1.5; G5 trades
  ≥ 30. Selection per pair: eligible ranked by net@1.5, freeze ≤ 2 per pair.
- Holdout SUCCESS (preregistered per pair): net>0 @1.0 AND @1.5; ONE look;
  failure final, no rescue.
- Force-flat law: no swap data ⇒ every position flat before rollover —
  day-close = the 19:00 H1 bar (close 20:00 UTC), no fills ≥ 19:00, weekend
  flat. Identical for both pairs (rollover is 21:00 UTC for both).
- Leak guards physical: per-pair dev runner loads only bars < 2026-01-01;
  holdout runner only ≥; run-count logged.

## 2. Data authority (per pair)

Dukascopy public M1 BID/ASK day candles 2021-01..2026-06 for GBPUSD and
USDJPY (~4,014 files per pair). Same OWNER_DIRECTIVE_SOURCE_AUTHORIZATION /
TCU_RISK_DISCLOSED posture as V1/V2; no account, no ToS acceptance, no
purchase; raw bytes machine-local, only SHA manifests commit.

Per-pair gates before any outcome: bi5 layout probe against tick ground
truth for each pair (price scale differs: GBPUSD 1e-5 points like EURUSD;
**USDJPY is expected at 1e-3 points — verified by probe, never assumed**);
census BUILD_PASS (tradable-minute share > 0.90, non-positive-spread
minutes ≈ 0); pip size fixed per pair (GBPUSD pip = 0.0001, USDJPY pip =
0.01) and all PnL reported in pips per pair's own pip.

## 3. Families (the V2 census, pip-normalized configs)

Same 12 families as V2 (FX2-GAP, PDHLOC, DOW, ASIAFADE, SESSMA, H1TSMOM,
H1DONCH, DAYMOM, RANGEEXP, STOCH, ROUNDNUM, HOURREV), same 4 configs each.
Threshold-type parameters are expressed in **pips and converted per pair**
(e.g., GAP th 10 pips = 0.0010 GBPUSD = 0.10 USDJPY; ROUNDNUM grid 50 pips
= 0.0050 / 0.50). Unit-free parameters (lookbacks, z-thresholds, sessions)
unchanged. Ancestry: this is a generalization test of the V2 census —
disclosed, D2-waived, and the EURUSD knowledge is recorded (see §1).

## 4. Governance

Engine semantics v1 with pip-size parametrization (default 1e4 keeps the
EURUSD fixtures byte-compatible; the 7+4 existing fixture suites must PASS
unchanged plus new JPY-scale fixtures before any outcome). Selection freeze
committed BEFORE the campaign. A7 fresh-context prelaunch before the
holdout opens. Per-pair terminal verdict enums:
`CANDIDATE_PENDING_PROSPECTIVE_VERIFICATION` | `NO_CANDIDATE_NO_VALUE` |
`BLOCKED_SOURCE_LICENSE` | `BLOCKED_COST_AUTHORITY` | `TECHABORT` (one per
pair; the cycle closes when both are recorded). No paper/live/order
surfaces. Program ledger: exploratory trials count per pair analogous to
V2 (tier-folded).
