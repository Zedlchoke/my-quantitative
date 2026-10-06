# FROZEN_RULE_DRAFT — 6J-JF3 TOKYO-MORNING SESSION STRUCTURE (PROPOSED — never an approved freeze)

- Round **FUTURES-5SYM-PRESCORED-20261005**, wave-3, lane **ADAPT-FXJA**, 2026-10-05.
- **STATUS: PROPOSED / DRAFT-PENDING-OWNER.** Rule TEXT AS CODE ENFORCES IT for
  the synthetic-sandbox adapter `adapter.py`. NOT an approved freeze; no scored
  run, no real-data execution, no registration. Outcome-blind.
- Parents: `../../fx_ja/SPEC_6J.md` §2/§3/§4/§7/§8 ·
  `../../fx_ja/CALENDAR_PIT_POLICY_6J_6A.md` §2/§3/§5 ·
  `../../fx_ja/COST_CONTRACT_6J_6A.md` §1/§4 · `../../fx_ja/IDENTITY_BUDGET_6J.md` §2 ·
  `../../hypo/CENSUS_5SYM.md` JF3 dossier.
- Family: **JF3 Tokyo-Morning Session Structure** — home-session discovery vs
  fade; n≈1,600 non-excluded sessions needs a window-move scale well above
  ~10 bp (K2 power honesty stated). **Dead-adjacency carried in full
  (census §11): FOREX-FREE-V2-A4-P1 (row 34) "Tokyo-range compression →
  London-morning expansion" is EXPECTANCY_NONPOSITIVE dead on SPOT — JF3 is
  6J futures, single-symbol, range-break trigger, different window pair; the
  full clock/sham placebo set binds this family's scored future.**

## 1. Observables and their timestamp-availability law (PIT)

| observable | definition as coded | knowable at (PIT) |
|---|---|---|
| Tokyo-morning range | high/max + low/min of the 09:00–11:30 JST 1m bars (Asia/Tokyo zoneinfo bucketing — DST-correct clock law, SPEC_6J §3); complete only at the window close | 11:30 JST |
| window coverage | minutes-with-bar share of the nominal 150-bar window | 11:30 JST |
| break trigger | first 1m CLOSE strictly outside the range, scanning bars with start ≥ 11:30 JST; tail = break side (6J price terms) | trigger-bar close (start + 1 min) = decision time |
| daily ATR(20) | mean daily range of the prior 20 held sessions, strict past, held-contract-only aggregates | after the 20th prior session closes |
| BoJ MPM dates / MOF disclosure dates | injected calendar facts (day-granularity) used as EXCLUDES only | calendar knowledge precedes the session |

**QUOTE-DIRECTION LAW:** 6J UP = yen STRONG (orientation proof `6j_orientation_
recheck.json` sha `6ca0baeb…`: 2024-07-11 6JU4 +1.73% while USDJPY 160.04 →
157.32). Break tail UP = close ABOVE range high in 6J price terms.

## 2. Signal definition

- **Universe (base)**: non-excluded sessions (BoJ MPM days and MOF disclosure
  days base-EXCLUDED — census JF3 §6).
- **Coverage rule**: Tokyo window ≥ 80% of nominal bars else the session is
  EXCLUDED (`H_WINDOW_COVERAGE_LT_080`, fail-closed).
- **tail**: UP (close > range_hi) / DN (close < range_lo); no break ⇒ NO-TRADE.
- **arms**: `CONT` = follow the break into the London/NY books; `FADE` = trade
  opposite. Both tails registered simultaneously.
- **controls**: `PLA` C1 clock-only shadow (seed 20261002, single-seed/
  single-delay); `ALW` C2 always-in; `CLK` C3 weekday-matched non-event clock
  (MPM/MOF days removed — the family negative vs JF1). Views (0 IDs): C3″
  DST-mismatch falsifier (a ±1h-class shift of the Tokyo anchor = clock bug ⇒
  family kill; the fixture probes it by CT-bucketing the same bars and
  requiring a different/no trigger), and the coverage EXCLUDE list.

## 3. Entry / exit / holding horizon

- **D1 entry**: OPEN of the first 1m bar after the trigger bar; **D30M**: bar
  starting 30 minutes after the trigger close-minute. Conservative fill law
  (fill = next-bar open; non-conservative requests refuse `P5-FXJA-D3`).
- **exit (whichever first)**: TP = entry ± 2 × SL_distance; SL = entry ∓ 1.0 ×
  daily ATR(20); same-bar TP/SL → SL priority; time exit = 16:00 CT session
  close (measured last bar — the position crosses into the deep US book by
  construction); no overnight hold.
- SL/TP rounded to the 5e-07 grid.

## 4. Session / event / calendar exclusions (fail-closed; ANY flag ⇒ NO-TRADE)

`X_BOJ_MPM_DAY` · `X_MOF_DISCLOSURE_DAY` (JF3 base excludes) ·
`X_MOF_OP_DAY` · `X_ROLL_CEASE_GUARD` (2022-09-20 law case, SPEC_6J §5) ·
`H_QUARTER_UNPROVEN` (6J 2023Q1–Q4 + 2 unidentified cells; derivation
FORBIDDEN) · `H_HOLIDAY_TIMES_NOT_OBTAINED` (2024–25 NOT_OBTAINED) ·
`H_PARTIAL_TAIL` (2026-10-01) · `H_WINDOW_COVERAGE_LT_080` (< 80% nominal) ·
`ATR_WARMUP_INSUFFICIENT` · `NO_BREAK_UPTO_ASOF` / `RANGE_NOT_COMPLETE_UPTO_ASOF`.

## 5. Roll / cease-guard handling

Same law as JF1 (rule draft §5): the adapter consumes carried masks; the chain
machinery (`fc.build_roll_chain`, `measure_and_disclose_guard_violations`) is
exercised in the RMM-6J family; flagged days are NO-TRADE here.

## 6. Tick / multiplier / cost binding points

- Bound identity: tick 5e-07 = $6.25 · multiplier 12,500,000 JPY · quote USD
  per JPY (`fc.load_fx_contract("6J")`, drift refuses).
- Costs per COST_CONTRACT §1 with the **Tokyo-fill session floor** (+1 tick
  entry-side, PROVISIONAL, JF3-8): RT T1/S1 = $67.42 = 8.4499 bp gate number;
  stress ×1.5/×2.0 on (spread + slippage) only. Labels: MODELED COST /
  UNDER REVIEW / VERIFIED_VS_ACCOUNT=NOT_RUN everywhere.

## 7. Identity enumeration (exact DRAFT IDs, quoted from IDENTITY_BUDGET_6J.md §2 / .json)

JF3 = 8 core + 3 controls = **minimal 11** (CONV-B; full grid 24):

```
FB6J1-JF3-CONT-UP-D1-S2   FB6J1-JF3-CONT-UP-D30M-S2   FB6J1-JF3-CONT-DN-D1-S2   FB6J1-JF3-CONT-DN-D30M-S2
FB6J1-JF3-FADE-UP-D1-S2   FB6J1-JF3-FADE-UP-D30M-S2   FB6J1-JF3-FADE-DN-D1-S2   FB6J1-JF3-FADE-DN-D30M-S2
FB6J1-PLA-JF3             FB6J1-ALW-JF3               FB6J1-CLK-JF3
```

## 8. Fold / warmup law

SPEC_6J §8 folds F1–F4 with the 252-session fold-head warmup
(`fc.scoreable_sessions`); folds multiply evaluation, never identities. Daily
ATR(20) is the warmup gate (20 prior held sessions strict past).

## 9. Owner-pending law — namespaced slots + fail-closed refusal

`P5-FXJA-D1` (real-data gate + option binding, `BLOCKED_NO_CEILING`) ·
`P5-FXJA-D3` (fill law) · `P5-FXJA-D4` (cost labels) · `P5-HYPO-OD2` (BoJ
stamps — window/coverage law stands). Real-data adapter execution: **NOT_RUN**.
