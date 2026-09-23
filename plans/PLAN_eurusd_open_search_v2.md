# PLAN EURUSD-OPEN-SEARCH-V2 — different families / coarser horizon on the proven data plane

> Registered 2026-09-23 by A1 under the owner's option **(a)** (reply "A" to
> the V1 terminal report): open a NEW campaign with different strategy
> families and a coarser execution horizon on the V1 data plane. S0
> exploration ONLY. The owner's "A" is NOT a scoring GO.

## 0. Cycle identity

```text
cycle_id     EURUSD-OPEN-SEARCH-V2
class        STRATEGY SEARCH (exploratory S0, after-cost PnL permitted only
             after the §2 data-extension gate passes)
asset        forex (EURUSD only)
budget       12 families × 4 configs = 48 planned, 96 MAX observed trials
S1           SEALED_UNTOUCHED
orders       NONE
go_phrase    GO EURUSD OPEN SEARCH V2 EXPLORATORY SCORED (typed only at
             this cycle's own gate after A7 prelaunch; "A" is NOT the GO)
forbidden    V1's SEALED-holdout reuse as holdout (see §3); editing any
             terminal cycle verdict; SANDBOX-OVERFIT-3ASSETS/;
             d2_curiosity_v1_sources/; other cycles' surfaces
```

## 1. Relation to V1 (ancestry, disclosed — D2 owner-waived exploratory)

`D2 = OWNER_WAIVED_EXPLORATORY` again (per the campaign shape the owner
picked; never recorded as PASS). Ancestry discipline despite the waiver:
V2 does NOT re-run V1's 12 families re-parameterized at the same horizon.
8/12 V2 families are NEW mechanisms; 2 are V1 mechanisms at a COARSER
horizon (H1) — the owner's chosen option explicitly includes "horizon khác";
2 are inverted forms of V1 mechanisms, disclosed in the freeze. Every V1
dev-positive arm is treated as dead unless V2 re-discovers it under V2's
own stronger gates.

V1 lessons frozen into V2's design:

- 15m granularity: costs (~0.3 pip/round-trip leg) ate 43/48 strategies.
  V2 executes at **H1** (holds of hours, same-day) where moves amortize
  costs.
- V1's dev gate PF≥1.10 let a false positive through (dev 1.14 → holdout
  0.98). **V2 G2 = PF ≥ 1.20 on dev** (preregistered BEFORE outcomes,
  rationale = V1's observed OOS decay).
- One-look holdout law stands: failure is final, no rescue.

## 2. Data authority (extension of the proven plane)

Base: V1's sha-pinned Dukascopy M1 bid/ask corpus 2021-01-01..2025-12-31
(3,652/3,652 files, PROBE_PASS layout, BUILD_PASS census) — copied
byte-identical into this cycle's `data_local/` (verify-on-read against the
V1 manifest), then EXTENDED with exactly 2026-01-01..2026-06-30.

- Extension gate: same decoder + census law (BUILD_PASS or the cycle falls
  back to BLOCKED_*). Boundary continuity check: no overlap/gap at the
  2025-12-31 → 2026-01-01 seam beyond the regular weekend closure.
- Same OWNER_DIRECTIVE_SOURCE_AUTHORIZATION / TCU_RISK_DISCLOSED posture as
  V1 amendment A1; no account, no ToS acceptance, no purchase.
- Same measured-cost law: spreads from bid/ask at decision and fill times;
  no invented spread; **no swap data ⇒ every position force-flat before
  rollover** — on the H1 plane the last tradable bar of a day is the
  19:00-UTC bar (close at 20:00, one full hour of margin before 21:00); no
  fills on it; weekend flat by construction.

## 3. Windows (frozen NOW, before any outcome)

```text
development : 2021-01-01 .. 2025-12-31 UTC  (all of V1's data; V1's old
              holdout 2023-07..2025-12 is DEMOTED to dev — it was seen once
              by one V1 candidate check and is disclosed as process-
              contaminated: V1 baselines revealed a long bias there)
holdout     : 2026-01-01 .. 2026-06-30 UTC  (never touched by any EURUSD
              search; downloaded only after the dev freeze, before A7)
```

Walk-forward folds on dev (H1 bars): F1 2022-07..2022-12, F2 2023-01..2023-06,
F3 2023-07..2023-12, F4 2024-01..2024-06, F5 2024-07..2024-12,
F6 2025-01..2025-06; warmup/training residue: 2021-01..2022-06 + each fold's
past. G3 becomes "≥ 4/6 folds net>0".

## 4. Gates and selection (all preregistered)

- G1 net_pips > 0 @k=1.0; **G2 PF ≥ 1.20 @k=1.0**; G3 ≥ 4/6 folds net>0;
  G4 net_pips > 0 @k=1.5; G5 trades ≥ 30.
- Selection: eligible = all gates; rank by net_pips @k=1.5; freeze ≤ 2;
  tiebreak net@1.0 then fewer trades.
- Holdout SUCCESS criteria (preregistered in the candidate-freeze artifact
  before the holdout opens): net > 0 @k=1.0 AND @k=1.5. One look only.
- Leak guards identical to V1: the dev runner physically loads only bars
  < 2026-01-01; the holdout runner only ≥ 2026-01-01; run-count logged.

## 5. Family census (12 × 4 configs; ancestry noted)

```text
FX2-GAP      overnight-gap follow/fade, intraday exec     NEW
FX2-PDHLOC   prior-day high/low breakout, intraday        NEW
FX2-DOW      day-of-week trailing-stats conditioning      NEW
FX2-ASIAFADE Asian-range fade during London morning       NEW
FX2-SESSMA   session-anchored MA deviation fade           NEW
FX2-H1TSMOM  time-series momentum at H1 (+time stop)      horizon-change of V1 FXOS-03
FX2-H1DONCH  Donchian at H1                               horizon-change of V1 FXOS-02
FX2-DAYMOM   prior-N-day sign -> intraday continuation    NEW
FX2-RANGEEXP prior-day range percentile -> expansion mode NEW
FX2-STOCH    stochastic %K/%D fade/follow at H1           NEW
FX2-ROUNDNUM round-number grid reject/magnet              NEW
FX2-HOURREV  hour-of-day reversal (inverted V1 form)      inverted V1 FXOS-24
```

Families NOT run (disclosed): everything else, including V1's survivors'
near-relatives at 15m — cap discipline; V1's near-miss FXOS-10-C3 stays dead.

## 6. Governance

Engine semantics v1 unchanged (opposite-side fills with stress multiplier,
force-flat law, pips = 1e4, PIT-only signals); new family functions get the
same truncation-invariance fixtures before any outcome; selection_freeze.json
committed BEFORE the campaign runs; A7 fresh-context prelaunch before the
holdout opens; heavy-lock law respected (download is probe-sized, ~5 MB).
Terminal verdict enum: `CANDIDATE_PENDING_PROSPECTIVE_VERIFICATION` |
`NO_CANDIDATE_NO_VALUE` | `BLOCKED_SOURCE_LICENSE` | `BLOCKED_COST_AUTHORITY`
| `TECHABORT`. No paper/live/order surfaces. This cycle's "A" instruction is
recorded as the campaign opener, NOT as a verbatim GO (P-8).
