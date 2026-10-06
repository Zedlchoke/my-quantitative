# FROZEN_RULE_DRAFT — 6A-AF1 RBA DECISION-MINUTE REACTION (PROPOSED — never an approved freeze; CONTINGENCY-PB3-PARK)

> **CONTINGENCY-ONLY BANNER (binding).** 6A is PB3 PARK — 0 budget, 0
> identities, 0 scheduled work. This draft activates ONLY after the owner
> chain **PB3 lift → ADOPT-D8 → ADOPT-D9 → D2 → ABS/China calendar**
> (namespaced slot **P5-FXJA-D5**). The frozen 26-ID contingency table
> (below) is carried VERBATIM and MUST NOT be expanded. 0 PnL, 0 scored runs,
> outcome-blind; `NO_GO_REGISTER / NO_GO_SCORE / NO_GO_ORDER` in force.

- Round **FUTURES-5SYM-PRESCORED-20261005**, wave-3, lane **ADAPT-FXJA**, 2026-10-05.
- Parents: `../../fx_ja/SPEC_6A_CONTINGENCY.md` §1-2/§4/§6 ·
  `../../fx_ja/CALENDAR_PIT_POLICY_6J_6A.md` §4 ·
  `../../fx_ja/COST_CONTRACT_6J_6A.md` §2-3 ·
  `../../hypo/CENSUS_5SYM.md` AF1 dossier ·
  `FUTURES-SIX-SCORED-GATE-PREP-20261004/budget/identity_tables.json`
  (sha256 `1a96b8eafcc80c9ec549a34e06cb704db4a240af80bb6488ab2bbc46e6e9246a`).
- Family: **AF1 RBA Decision-Minute Reaction** — does the ±5' move at the RBA
  decision persist (DRIFT) or overshoot-and-revert (REV) through the Sydney
  afternoon? **K0 thin-n kill PRE-REGISTERED** (n=67 meetings; change-vs-hold
  strata fragment folds below the ≥5 floor — single-stratum cell or pooled
  eras only); **K2 expected** (±5' signal scale 4.35 bp < one era-2 RT 8.2 bp).

## 1. Observables and their timestamp-availability law (PIT)

| observable | definition as coded | knowable at (PIT) |
|---|---|---|
| RBA decision dates | injected `calendar.rba_decision_dates[]` (date granularity; effective_date − 1 AU business day rule; the 2020-03-19 off-Tuesday special flagged) | calendar knowledge precedes the session |
| RBA decision TIME | **NOT carried by the source table.** Consuming a claimed minute-stamp refuses (`RefusedRbaTimeNotCarried`); the **14:30 Sydney anchor stays a DECLARED convention** (6A_DEEP §4.1) | never verified |
| ±5' window | 14:30–14:35 Sydney bar starts, Asia/Sydney zoneinfo (DST-correct); window move = close(14:34) − open(14:30), 6A price terms (6A UP = AUD stronger) | window close 14:35 = decision time |
| window ATR(20) | mean ±5'-window range over the prior 20 RBA dates, strict past | after the 20th prior event |
| era label | deterministic from the MEASURED 2020-11-20/23 grid break (data-side PROVISIONAL pending D8): era-1 tick 1e-04 = $10.00/tick; era-2 5e-05 = $5.00/tick | deterministic per session date |

## 2. Signal definition

tail UP/DN from the ±5' signed move; arms `DRIFT`/`REV` both tails; controls
`PLA` (C1 clock-only shadow, seed 20261002) / `ALW` (C2 always-in on event
days) / `CLK` (C3 Tuesday-matched non-event clock — RBA days are Tuesdays).
Surprise classification **NOT_RUN** (weak change-vs-hold proxy 59 vs 29
ticks — labeled as such, never a signal input).

## 3. Entry / exit / holding horizon

D1 entry = 14:35 Syd bar open; D30M = 15:05 Syd bar open; conservative fill
law (next-bar open; no limit/queue/BBO). TP = entry ± 2 × SL_distance;
SL = entry ∓ 1.0 × window-ATR(20); same-bar TP/SL → SL priority; time exit
17:00 Sydney [PROVISIONAL] (scan stops there; mandatory flat).

## 4. Session / event / calendar exclusions (fail-closed; ANY flag ⇒ NO-TRADE)

`X_FOMC_DAY` + `X_FOMC_SPILLOVER_NEXT_DAY` (AF1 base excludes — the US
common factor is LARGER than RBA's on 6A: ±5' 8.2×) · `H_QUARTER_UNPROVEN`
(6A 2023Q1/Q2 NOT_OBTAINED; derivation FORBIDDEN) ·
`H_HOLIDAY_TIMES_NOT_OBTAINED` · `H_PARTIAL_TAIL` (2026-10-01) ·
`ATR_WARMUP_INSUFFICIENT` · `TRIGGER_FLAT`.

## 5. Roll / cease-guard handling

6A measured chain: 27 rolls, span 2020-03-17..2026-09-14; baseline-code k=5
has **2 cease-guard violations (2024-12-17, 2026-06-16 — the exact 6J
2022-09-20 pathology, twice)** ⇒ the explicit cease-guard variant is the
MANDATORY chain-builder (27 rolls, 0 violations; law-pending ADOPT-D9:
measure and disclose violations first). Chain machinery lives in
`fx_common.build_roll_chain` / `measure_and_disclose_guard_violations` and is
exercised by the RMM-6A family tests.

## 6. Tick / multiplier / cost binding points (ERA-AWARE — the load-bearing 6A law)

- Multiplier 100,000 AUD; quote USD per AUD; 6A UP = AUD stronger.
- **Era law (D8-pending, data-side adjudicated)**: era-1 = 2020-01-02..
  2020-11-20 (231 sessions) grid 1e-04 = **$10.00/tick**; era-2 from
  2020-11-23 grid 5e-05 = **$5.00/tick**; break sits in the 11-20→11-23
  weekend; zero odd 5e-05-multiple closes in 327k+ era-1 closes.
- **NO-BACK-CAST LAW**: era-2 cost models may NOT back-cast into era-1
  windows; the adapter REFUSES trade intent on era-1 windows
  (`REFUSED_ERA1_DESCRIPTIVE_ONLY` — refusal CODE, not a warning).
- Costs: era-2 RT T1/1-tick **$54.92 = 8.2019 bp** @ $66,960 notional;
  era-1 RT T1/1-tick **$104.92 = 15.1794 bp** @ $69,120 (×1.85 not ×2 — the
  fee layer 2.46/side is tick-invariant). Sydney-window entry fills carry
  the +1-tick session floor (PROVISIONAL). Labels: MODELED COST / UNDER
  REVIEW / VERIFIED_VS_ACCOUNT=NOT_RUN everywhere.

## 7. Identity enumeration (CONTINGENCY-PB3-PARK shapes; frozen table carried VERBATIM)

The FROZEN object is the 26-ID table (`identity_tables.json` sha `1a96b8ea…`,
symbol `6A`, carried verbatim in `SPEC_6A_CONTINGENCY.md §6`): **AF1
minimal_core 8 + controls 3 = 11; AF2 0; AF3 11; AF4 0; RMM_6A 4 = 26 if
ever lifted; total today 0.** The C6A0 ID strings below are PROPOSED shapes —
they freeze only post-lift and are never a scored denominator.

```
C6A0-CONT-AF1-DRIFT-UP-D1-S2  C6A0-CONT-AF1-DRIFT-UP-D30M-S2  C6A0-CONT-AF1-DRIFT-DN-D1-S2  C6A0-CONT-AF1-DRIFT-DN-D30M-S2
C6A0-CONT-AF1-REV-UP-D1-S2    C6A0-CONT-AF1-REV-UP-D30M-S2    C6A0-CONT-AF1-REV-DN-D1-S2    C6A0-CONT-AF1-REV-DN-D30M-S2
C6A0-CONT-PLA-AF1             C6A0-CONT-ALW-AF1               C6A0-CONT-CLK-AF1
```

## 8. Fold / warmup law

Host folds (SPEC_6J §8 map) with the 252-session warmup; **K0: the change-vs-
hold strata (23/44 of n=67) fragment any fold structure below the ≥5-per-fold
floor** (`fc.fold_floor_check(23, 8)` fails — pre-registered) ⇒ the family
may only ever be scored as a single-stratum cell or pooled eras.

## 9. Owner-pending law — namespaced slots + fail-closed refusal

| slot | law | refusal behavior |
|---|---|---|
| `P5-FXJA-D5` | 6A activation chain: PB3 lift → D8 → D9 → D2 → ABS/China calendar | `require_synthetic(6A)` refuses real panels (`BLOCKED_PB3_PARK` / `BLOCKED_D8_UNRATIFIED`); `af1_freeze_check()` refuses; the 26-ID table stays at total 0 |
| era-1 law | no-back-cast | era-1 trade intent raises `RefusedEra1NoTradeIntent` (code `REFUSED_ERA1_DESCRIPTIVE_ONLY`) |
| RBA time | date-granularity only | `consume_rba_decision_stamp()` always refuses |

Real-data adapter execution: **NOT_RUN**. This adapter is CONTINGENCY
machinery — **never activated**.
