# FROZEN_RULE_DRAFT — 6A-AF3 BIMODAL US+SYDNEY SESSION STRUCTURE (PROPOSED — never an approved freeze; CONTINGENCY-PB3-PARK)

> **CONTINGENCY-ONLY BANNER (binding).** 6A is PB3 PARK — 0 budget, 0
> identities, 0 scheduled work. Activates ONLY after the owner chain **PB3
> lift → D8 → D9 → D2 → ABS/China calendar** (slot **P5-FXJA-D5**; the China
> acquisition itself is **P5-HYPO-OD3** class). Frozen 26-ID table carried
> VERBATIM (sha `1a96b8ea…`), never expanded. 0 PnL, outcome-blind.

- Round **FUTURES-5SYM-PRESCORED-20261005**, wave-3, lane **ADAPT-FXJA**, 2026-10-05.
- Parents: `../../fx_ja/SPEC_6A_CONTINGENCY.md` §1-3/§5/§7 ·
  `../../fx_ja/CALENDAR_PIT_POLICY_6J_6A.md` §4/§5 ·
  `../../fx_ja/COST_CONTRACT_6J_6A.md` §2-3 · `../../hypo/CENSUS_5SYM.md` AF3 dossier.
- Family: **AF3 Bimodal US+Sydney Session Structure** — does a Sydney-morning
  range break (09:30–11:30 Syd) rotate into the deep US book (**ROT**) or get
  absorbed (**ABS**)? Committed anatomy: bimodal U-curve (primary peak 09:00
  CT, secondary 19:00–20:00 CT, minimum 15:00 CT); Sydney 11:30 modal
  half-hour 2.35% of daily volume; Shanghai-data window carries the highest
  mean 1m range (2.36 ticks) — hence K4.

## 1. Observables and their timestamp-availability law (PIT)

| observable | definition as coded | knowable at (PIT) |
|---|---|---|
| Sydney-morning range | high/low of the 09:30–11:30 Sydney bars (Australia/Sydney zoneinfo — DST-correct; the opposite-DST-month clock falsifier C3″ is the standing kill) | window close 11:30 Syd |
| window coverage | minutes-with-bar share of the nominal 120-bar window | 11:30 Syd |
| break trigger | first 1m CLOSE strictly outside the range, scanning from 11:30 Syd; tail = break side (6A price terms) | trigger-bar close = decision time |
| **K4 China-window boundary** | a trigger whose Asia/Shanghai local time falls in **09:30–10:00 CST** is a contamination boundary ⇒ fail-closed NO-TRADE; an ORDER INTENT on such a session raises `REFUSED_CHINA_CALENDAR_NOT_RUN` (China splits NOT_RUN) | at the trigger |
| daily ATR(20) | mean daily range, prior 20 held sessions, strict past | after the 20th prior session |
| era label | measured 2020-11-20/23 grid break (era-1 $10/tick vs era-2 $5/tick) | deterministic |

## 2. Signal definition

tail UP/DN; arms `ROT` (follow the break) / `ABS` (fade it), both tails;
controls `PLA`/`ALW`/`CLK` (C3 weekday-matched non-event clock, RBA+FOMC
removed). C3″ opposite-DST-month clock falsifier = the program's cleanest
clock-law kill (evaluation view, 0 IDs). **K4 kills the base spec if triggers
cluster in the China window** — the adapter refuses rather than trades an
unclassifiable event.

## 3. Entry / exit / holding horizon

D1 = first 1m bar after the trigger; D30M = +30 min; conservative fill; TP
2×SL / SL 1.0×daily-ATR(20); same-bar TP/SL → SL priority; time exit 16:00 CT
(the scan stops at the CT afternoon close; mandatory flat). Sydney-morning
entry fills carry the +1-tick thinner-book session floor (PROVISIONAL).

## 4. Session / event / calendar exclusions (fail-closed; ANY flag ⇒ NO-TRADE)

`X_RBA_DAY` + `X_FOMC_DAY` (AF3 base excludes) · `H_WINDOW_COVERAGE_LT_080`
(< 80% of 120 nominal bars) · `H_QUARTER_UNPROVEN` (6A 2023Q1/Q2) ·
`H_HOLIDAY_TIMES_NOT_OBTAINED` · `H_PARTIAL_TAIL` · `ATR_WARMUP_INSUFFICIENT`
· `NO_BREAK_UPTO_ASOF` · `CHINA_WINDOW_CONTAMINATION_K4` (plus the intent-level
`REFUSED_CHINA_CALENDAR_NOT_RUN`).

## 5. Roll / cease-guard handling

6A law identical to AF1 draft §5 (baseline k=5 with 2 violations ⇒ explicit
cease-guard variant MANDATORY, law-pending ADOPT-D9; machinery in
`fx_common.build_roll_chain`; exercised by the RMM-6A family tests).

## 6. Tick / multiplier / cost binding points (ERA-AWARE)

Era-2 RT T1/1-tick $54.92 = 8.2019 bp; era-1 $104.92 = 15.1794 bp; the fee
layer is tick-invariant (×1.85-not-×2 law). NO-BACK-CAST: era-1 trade intent
refuses (`REFUSED_ERA1_DESCRIPTIVE_ONLY`). K2 honesty: Sydney trigger scale
~1.2–1.5 bp/min needs multi-minute accumulation to clear 8.2 bp. Labels:
MODELED COST / UNDER REVIEW / VERIFIED_VS_ACCOUNT=NOT_RUN.

## 7. Identity enumeration (CONTINGENCY-PB3-PARK shapes; frozen 26-count table verbatim)

AF3 = 8 + 3 = 11 of the frozen 26 (AF1 11 + AF2 0 + AF3 11 + AF4 0 + RMM 4;
total today **0** until PB3 lift + D8). C6A0 strings are PROPOSED shapes:

```
C6A0-CONT-AF3-ROT-UP-D1-S2  C6A0-CONT-AF3-ROT-UP-D30M-S2  C6A0-CONT-AF3-ROT-DN-D1-S2  C6A0-CONT-AF3-ROT-DN-D30M-S2
C6A0-CONT-AF3-ABS-UP-D1-S2  C6A0-CONT-AF3-ABS-UP-D30M-S2  C6A0-CONT-AF3-ABS-DN-D1-S2  C6A0-CONT-AF3-ABS-DN-D30M-S2
C6A0-CONT-PLA-AF3           C6A0-CONT-ALW-AF3             C6A0-CONT-CLK-AF3
```

## 8. Fold / warmup law

Host folds (SPEC_6J §8 map) + 252-session warmup; daily ATR(20) warmup gate;
K4 clusters and C3″ opposite-DST months are evaluation views (0 IDs).

## 9. Owner-pending law — namespaced slots + fail-closed refusal

| slot | law | refusal behavior |
|---|---|---|
| `P5-FXJA-D5` | 6A activation chain | real-data + freeze gates refuse (`BLOCKED_PB3_PARK`) |
| `P5-HYPO-OD3` | ABS + China release-calendar acquisition | `RefusedChinaCalendarNotRun` on any K4-window trigger intent |
| era-1 law | no-back-cast | era-1 intent raises `RefusedEra1NoTradeIntent` |

Real-data adapter execution: **NOT_RUN**. CONTINGENCY machinery — never
activated.
