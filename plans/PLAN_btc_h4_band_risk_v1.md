# PLAN BTC-H4-BAND-RISK-V1 — exit-side risk overlays on the ES1 band book: can the near-miss that beats every baseline survive G5?

> Status: `PLANNED_NOT_STARTED`. Owner directive 2026-09-23: "Lên cycle mới
> tìm kiếm từ sai lầm này đi, khỏi A7 lúc này" — successor to ES1's
> near-miss of record (C3 band-3% beats ALL baselines under BOTH funding
> laws but fails G5 fold-concentration 0.71–0.73; F3 +733,552 measured,
> F2 −75,569). Class POSTHOC S0 DISCOVERY (ceiling
> `POSTHOC_DISCOVERY_CANDIDATE_FOR_PROSPECTIVE_VALIDATION`; no dev/holdout
> possible — outcome-observed window). S1 `SEALED_UNTOUCHED`. No
> paper/live/orders.

## 0. Cycle identity

```text
cycle_id     BTC-H4-BAND-RISK-V1
asset        crypto (cell BTC_H4)
question     The band book's losses live in drawdown folds (F2) while its
             profit lives in trend folds (F3). EXIT-SIDE risk overlays —
             trailing stop from position peak / catastrophic stop from
             entry, with band-law re-entry — are an EXIT-LAW change, NOT
             entry timing (the G6-killed class). Can any overlay cell pass
             the FULL preregistered gate set INCLUDING G5 (fold
             concentration <= 0.50) while keeping G3 (beats ALL four
             baselines under BOTH funding laws)? A NO is the expected valid
             terminal.
inputs       SAME engine + panel + measured funding series inherited from
             ES1 (engine identity gate RECONCILED 9e-10 vs PSV1 ledger;
             9/9 fixtures). Base SHA = ES1 terminal 09159aaa.
folds/costs  FROZEN identical to ES1 (F1..F4 era edges; 6bps/side; tiers
             1.0/1.5/2.0; funding laws constant 1.377e-5 + measured
             Vision series; capital 100k; fraction <= 1.0; force-flat at
             fold ends).
budget       max 8 scored cells (R1..R8 below). Baselines + G6 control +
             DIAG census are reference computations.
s1           SEALED_UNTOUCHED
orders       NONE
go_phrase    GO BTC H4 BAND RISK V1 SCORED EXECUTION (STOP-1, §4;
             the dispatching prompt is NOT a GO)
a7           WAIVED THIS CYCLE by explicit owner instruction 2026-09-23
             ("khỏi A7 lúc này" — recorded verbatim). NOT waived: data/PIT
             authority, measured costs, trial accounting, reproduction
             (mandatory twin, byte-compare), owner GO, S1 seal, heavy-lock
             law. Compensating controls: inherited RECONCILED engine +
             full fixture regression re-run + full-distribution reporting.
forbidden    entry-timing families; regime routers (TRV1/RSM/JEV/PSV1
             reopening law); post-hoc gate relaxation (G5 stays 0.50);
             leverage; choosing ladder rungs by fold PnL (ladder frozen
             below); mid-run stop on ugly numbers; git add -A.
```

## 1. Overlay law (frozen BEFORE any PnL)

Base book: the ES1 band law — long enters when close > SMA200×(1+b), exits
when close < SMA200×(1−b). Overlay (exit-only, evaluated at H4 close on
bars while the band state is long):

```text
TRAIL(t):  track peak_close = max(close over bars since this position's
           entry fill). If close[t] < peak_close×(1−trail) → exit decision
           at t (fill t+1). Re-entry ONLY via the band law (close >
           SMA200×(1+b) again). peak resets at each new entry fill.
CAT(t):    if close[t] < entry_ref_close×(1−cat) → exit decision at t.
           entry_ref_close = close at the bar whose decision opened the
           position.
COOLDOWN(k): after ANY overlay exit, the band entry is blocked for k bars
           (churn law on stop-outs).
```

Cells (round ladder, frozen):

```text
R1 C3 base + TRAIL 10%          R5 C1 base (b=0.005) + TRAIL 15%
R2 C3 base + TRAIL 15%          R6 C3 base + CAT 15%
R3 C3 base + TRAIL 20%          R7 C3 base + TRAIL 15% + COOLDOWN 12
R4 C3 base + TRAIL 25%          R8 C3 base + TRAIL 30% (far-stop control:
                                   must nearly reproduce C3 — ablation
                                   identity within 2% of C3 net, else
                                   TECHABORT on the overlay machinery)
```

G6 control: block-shuffle(30 bars, seed 20260923) of R2's overlay-trigger
series (the exit decision series it adds on top of C3), re-priced on the
same base book; control out-earning R2 ⇒ kill.

## 2. Gates (identical to ES1 §4, unchanged, G5 NOT relaxed)

G1 net>0 @1.0x both laws · G2 net>0 @1.5x both laws · G3 beats ALL FOUR
baselines @1.0x BOTH laws · G4 >=3/4 positive folds OR best-fold-removed>0
· G5 fold concentration <= 0.50 (THE wall this cycle attacks) · G6 control
not out-earning · G7 turnover ceiling + no zero-length trades · G10 vs
BASE_TREND_LF: combined net increases AND no fold flips positive→negative.
ALL-PASS ⇒ ceiling verdict `..._POSTHOC_DISCOVERY_CANDIDATE_FOR_
PROSPECTIVE_VALIDATION`; else `BTC_H4_BAND_RISK_V1_NO_INCREMENTAL_VALUE`
(or BLOCKED_DATA_OR_SELECTION / TECHABORT).

DIAG (reference, no budget): fold-concentration census of ALL baselines +
COMPARATOR + every ES1 C-cell — establishes whether ANY long book on this
window can pass G5 at all; reported as a program finding, never a gate
change.

## 3. Cycle phases

```text
P0  intake; registry hygiene.
P1  overlay implementation in the inherited engine namespace + hand-
    computed fixtures (trail golden: synthetic path where the stop fires
    exactly one bar after peak-break; cat golden; cooldown golden; peak
    reset at re-entry; fold-end precedence) + full regression (9+ fixtures)
    + sanitized dry-run counts (no PnL).
STOP-1 OWNER GATE: report + wait for the owner to type verbatim
    GO BTC H4 BAND RISK V1 SCORED EXECUTION
P2  scored run (full denominator; same §9 light-exemption measurement
    discipline with the foreign-lock disclosure if the lock is still held)
P3  reproduction twin (mandatory, byte-compare) + two-half close.
```

## 4. Trial identity

family_id BANDRISK-<CELL>; arm_config_digest; data digests inherited;
funding_law recorded per computation; observed denominator counts every
cell×tier×law (24 minimum) + references; budget 8.

## 5. Boundaries

Worktree `.worktrees/btc-h4-band-risk-v1/integration`, branch
`orca/btc-h4-band-risk-v1-integration`, base = ES1 terminal 09159aaa
(RECONCILED engine inherited verbatim). No push from lanes; registry only
via researchctl; S1 sealed; no orders; raw bytes gitignored. Turn-scope:
pre-GO turns implement/test/census/freeze — no scored run.

## 6. Amendments log

None yet.
