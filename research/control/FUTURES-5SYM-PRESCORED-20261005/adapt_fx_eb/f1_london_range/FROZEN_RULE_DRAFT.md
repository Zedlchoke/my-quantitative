# FROZEN_RULE_DRAFT — FX-F1 London-Range Absorption (PROPOSED — never an approved freeze)

- Round **FUTURES-5SYM-PRESCORED-20261005**, wave-3, lane **ADAPT-FXEB**, 2026-10-05.
- **STATUS: PROPOSED / CONDITIONAL-ON-PB2-LIFT. PB2 HOLD stands** (PLAYBOOKS_DRAFT r5 §2;
  PB2_ANCESTRY_COURT_DRAFT §d; `PB2_HOLD_RESTATE.md` sha256 `88386aa3…5a75b`). This is the
  rule TEXT AS CODE ENFORCES IT for the synthetic-sandbox adapter `adapter.py` in this
  directory. It is NOT an approved freeze; no scored run, no real-data execution, no
  registration is authorized or implied. Outcome-blind: signals/order-intent on synthetic
  fixtures only.
- Parents: `../../fx_eb/SPEC_6E.md` §2/§3/§4/§5/§7/§9 · `../../fx_eb/SPEC_6B.md` §2/§3/§4/§5/§7/§9 ·
  `../../fx_eb/CALENDAR_PIT_POLICY_6E_6B.md` §2/§3/§4/§5 · `../../fx_eb/COST_CONTRACT_6E_6B.md` ·
  `../../fx_eb/IDENTITY_BUDGET_6E_6B.md` §2/§4.1/§4.2/§6 · `../../hypo/CENSUS_5SYM.md` FX-F1 rows ·
  `../../exec/symbol_contracts.json` rows 6E/6B.
- Family: **FX-F1 London-Range Absorption** — London-morning discovery, US-arrival
  continuation (H-C) vs absorption/fade (H-D). Census gate ≥500 triggers/symbol:
  **6E PASS 1,362 / 6B PASS 1,342** [MEASURED, `FUTURES-K6GATE-PREP-20261004/fx_eb/
  fx_f1_f4_census.json`; gate definition `FXF1_census@1`: trigger = first 1m close
  strictly outside R_lon in 11:00–15:30 London, cap 1 trigger/session first-touch].
  Census gate closes the measurement precondition ONLY; **court §b1.1 1m trigger-time
  anatomy remains NOT_RUN and gates any scored F1 spec** (P5-FXEB-OD11).

## 1. Observables and their timestamp-availability law (PIT)

| observable | definition as coded | knowable at (PIT) |
|---|---|---|
| London range R_lon | (min low, max high) of 1m bars whose London-local wall time (Europe/London, zoneinfo, DST-correct) lies in **[08:00, 11:00)** on the session date | at the close of the last range-window bar (11:00 London) |
| London coverage | minutes-with-bar share of the same [08:00,11:00) London window | same |
| trigger | **first** 1m close strictly outside R_lon with London-local time in **[11:00, 15:30)**; cap 1 trigger/session (first-touch) | close of the trigger bar |
| trigger sign | `UP` if trigger close > R_lon high, `DN` if < R_lon low; exactly on the boundary is not outside ⇒ no trigger | close of the trigger bar |
| ATR(20) | mean daily range of the prior 20 held sessions, strict past, held-contract-only (`fx_common.atr20_points`) | after the 19th prior session closes; consumed at decision time |
| F2 event day-sets | injected calendar rows with vintage provenance: 6E = FOMC ∪ ECB GC; 6B = MPC ∪ FOMC (`fx_common.f2_event_day_set`; CALENDAR_PIT_POLICY §4 vintage law — current-calendar inference FORBIDDEN) | day level, 00:00 CT |
| holiday / quarter posture | 6E fail-closed lists (`fx_common.holiday_exclusion_flags`, incl. hard-coded evidence-based 2023-11-24 + injected neighborhood cells); 6B = `HOL_GRID_ABSENT_0OF42_DECLARED` on every session (declaration, NOT exclusion); NOT_OBTAINED quarters excluded per-quarter (D12) | day level |

PIT enforcement in code: every read goes through `fx_common.bars_upto` / `session_bars(...,
upto)`; the pytest PIT proof feeds truncated panels (rows > fill time removed) and requires
identical outputs.

## 2. Signal definition

- **Universe (base)**: sessions with a London trigger, EXCLUDING the FX-F2 day-sets
  (mutually-exclusive day-set relation per IDENTITY_BUDGET §2: F1's base excludes exactly
  F2's universe), coverage <80% sessions, holiday/quarter fail-closed classes, and the
  ATR-warmup-insufficient head.
- **tails**: `UP` / `DN` from the trigger sign; no trigger ⇒ NO-TRADE (`NO_TRIGGER`).
- **arms**: `HC` = enter in the trigger-move direction (continuation);
  `HD` = enter opposite (fade). Both registered simultaneously
  (falsification-by-competitor). Identity arms per IDENTITY_BUDGET §4: `{HC,HD}`.
- **controls** (same machinery): `C1-SHADOW` clock-only shadow (single-seed/single-delay
  default per P5-FXEB-OD4; ≥100-seed expansion = separate owner ruling), `C2-ALW`
  always-in-London-window, `C3-ANCHOR` FLAT-class accounting floor. 6E/6B trigger
  co-occurrence + the 6B London-share-drift split (28.7→23.7%) are declared
  falsifier/diagnostic views (CENSUS FX-F1 §7), not identities.

## 3. Entry / exit / holding horizon

- **delay slots** [DRAFT, P5-FXEB-OD3]: D0 = open of the first 1m bar AFTER the trigger bar
  (conservative next-bar-open fill; no limit/queue/BBO claims — BBO NOT_RUN D5);
  D1B = one bar later; D30M = D0 bar + 30 minutes (full-grid extension only).
- **exit (whichever first)**: TP = entry ± 2 × SL_distance; SL = entry ∓ 1.0 × ATR(20);
  same-bar TP/SL ⇒ **SL-priority**; otherwise mandatory flat at the **16:00 CT session
  close** (time exit; exit fill = close of the 16:00 CT bar). Intraday, same session —
  no overnight holding. SL/TP rounded to the symbol tick grid; ATR numeric levels are
  computed at freeze, never before (SPEC_6E §10 item 12 posture) — the adapter computes
  them only on synthetic fixture inputs.

## 4. Session / event / calendar exclusions (fail-closed; `apply_exclusions`)

| code | law |
|---|---|
| `FXF2_EVENT_DAY_STANDING_OUTSIDE` | every F2 day-set session (6E FOMC∪ECB / 6B MPC∪FOMC) EXCLUDED from the F1 base — the competing structure's day-set |
| `LONDON_COVERAGE_LT_080` | London-morning coverage < 0.80 ⇒ EXCLUDE (census base filter, K6GATE diagnostics `sessions_coverage_lt_80pct`) |
| `H6E_EVIDENCE_BASED_DEVIATION` | 6E 2023-11-24 early close (the single committed id-58 deviation exclusion) |
| `H6E_NEIGHBORHOOD_FAIL_CLOSED` / `H6E_AGED_OUT_NEIGHBORHOOD` | 93 cells / 37 windows (29 OBTAINED + 8 aged-out; deviant-session identification NOT_RUN ⇒ neighborhood excluded, never counted clean); aged-out zero-grids never evidence of normal hours |
| `HOL_GRID_ABSENT_0OF42_DECLARED` | **6B only — DECLARATION, NOT an exclusion**: no holiday-adjacent exclusion is implementable (grid 0/42 structural NOT_OBTAINED); holiday-adjacent 6B sessions are neither excluded nor certified clean and every 6B result carries the hole declared |
| `QUARTER_NOT_OBTAINED_ROLL_ANCHOR` | 6E 2026-Q3/Q4 (ECU26/ECZ26); 6B 2023Q1–2024Q2 (BPH23..BPM24) — no official roll anchor ⇒ per-quarter exclusion (D12 posture) |
| `ATR_WARMUP_INSUFFICIENT` | fewer than 20 prior held sessions ⇒ NO-TRADE |
| `NO_TRIGGER` | no out-of-range close in the trigger window ⇒ NO-TRADE |

DST: all London-local anchoring via zoneinfo (Europe/London); `session_date` consumed as
carried panel data, never re-derived from `ts`. A DST-mismatch sign flip = clock-law bug
(K4-analog; K5 view).

## 5. Roll / cease-guard handling (chain law)

- All fills consume the **held contract only** (SPEC_6E §2 / SPEC_6B §2: 1,282,448 / 469,545
  shared-timestamp rows excluded from any dispersion/fill computation). Fixtures are
  single-contract per session by construction.
- Roll law: **27 measured switches / 28 contracts / 1,746 sessions each**; leads 13–19d (6E
  where cells obtained) / 17d (6B 2024Q4→2026Q3), 14d into 2026Q4 [MEASURED,
  `cost_roll_events_fxeb.json` sha256 `a99a6983…40052`]. The PIT **k=5 + cease-guard**
  rule is law-pending (D9-extension; 6B thin-window 1,069..13,222 contracts/day measured):
  the adapter performs NO chain construction and never exercises the cease-guard branch;
  F1 does not additionally exclude roll-week sessions (a trigger may fall in a roll week);
  NOT_OBTAINED quarters are excluded per-quarter above.

## 6. Tick / multiplier / cost binding points

- Bound from `exec/symbol_contracts.json` via `fx_common.load_fx_contract(sym)`:
  **6E tick 0.00005 = $6.25 @ EUR 125,000; 6B tick 0.0001 = $6.25 @ GBP 62,500**;
  long_base_sign +1 (USD per EUR / per GBP). The rows' `session_mask_spec.rth
  "07:20-14:00"` is a PLACEHOLDER-PENDING field (CONTRACTS handoff finding F2) —
  disclosed, never consumed; the measured Globex 17:00→16:00 CT template is the law of
  record. Tick constancy CONSTANT across the 2020-11-23 boundary both symbols
  (K6GATE §4).
- Costs (`fx_common.cost_ladder_usd`): fee all-in B 2.46 / A-derived 2.47 USD/side
  (Variant-A DERIVED, not tabulated in A7 §8 for FX) + $18.75 spread half-turn
  (high-biased close-proxy) + slippage {S1 6.25, S2 12.50, S3 18.75}/side ⇒
  RT S1/S2/S3 = 54.92 / 67.42 / 79.92 USD ⇒ **6E 3.6–6.3 bp / 6B 6.3–11.2 bp** bands.
  F1 power honesty: MDE-at-n ≈ 3.5 bp (6E, n=1,362) vs RT floor — power floor ≈ cost
  floor; **6B MDE 4.2 bp sits BELOW its own S1 cost floor** (court §c3: a null at
  program-feasible n is the pre-registered death, NOT evidence of absence).
  **`fx_common.consumable_rt_cost` refuses while P5-FXEB-OD6 unsigned** — no cost gate
  may consume either basis. Labels MODELED COST / UNDER REVIEW /
  VERIFIED_VS_ACCOUNT=NOT_RUN on every surface; "measured cost" forbidden.

## 7. Identity enumeration (exact DRAFT IDs, quoted from IDENTITY_BUDGET_6E_6B.md §4.1/§4.2)

Grammar `FXF<n>-<SYM>-<ARM>-<TAIL>-<DELAY>-<TIER>[-<STRATUM>]`. FX-F1 = 8 core + 3
controls = **11 per leg** (CONV-D; census-native CONV-C 36/leg full-grid disclosed, never
summed). Draft delay slots {D0, D1B} (P5-FXEB-OD3):

```
FXF1-6E-HC-UP-D0-S2  FXF1-6E-HC-UP-D1B-S2  FXF1-6E-HC-DN-D0-S2  FXF1-6E-HC-DN-D1B-S2
FXF1-6E-HD-UP-D0-S2  FXF1-6E-HD-UP-D1B-S2  FXF1-6E-HD-DN-D0-S2  FXF1-6E-HD-DN-D1B-S2
FXF1-6E-C1-SHADOW    FXF1-6E-C2-ALW        FXF1-6E-C3-ANCHOR
FXF1-6B-HC-UP-D0-S2  FXF1-6B-HC-UP-D1B-S2  FXF1-6B-HC-DN-D0-S2  FXF1-6B-HC-DN-D1B-S2
FXF1-6B-HD-UP-D0-S2  FXF1-6B-HD-UP-D1B-S2  FXF1-6B-HD-DN-D0-S2  FXF1-6B-HD-DN-D1B-S2
FXF1-6B-C1-SHADOW    FXF1-6B-C2-ALW        FXF1-6B-C3-ANCHOR
```

Binding any OPTION (FX-A/B/C) raises `RefusedPendingOwnerDecision("P5-FXEB-OD2")` while
the FX ceiling + clock-shadow reading are unsigned. `request_f1_scored_spec` refuses
(`P5-FXEB-OD11`) — court §b1.1 anatomy NOT_RUN.

## 8. Fold / warmup application (two competing laws — P5-FXEB-OD10)

Folds (SPEC_6E §7 / SPEC_6B §7, DRAFT): F1 2020-01..2021-12 · F2 2022-01..2023-12 ·
F3 2024-01..2025-06 · F4 2025-07..2026-09; re-fixed at any registration freeze. Warmup
switchable: `FAMILY_60` (60 held sessions — FX_HYPOTHESES §1.5 family law; DRAFT DEFAULT)
vs `ES_252` (252-session ES precedent). `scoreable_sessions(..., warmup_mode=...)`
implements BOTH; `bind_warmup_law` refuses (`P5-FXEB-OD10`) while unsigned — the default
is the recorded draft, never binding. Folds multiply evaluation views only; identity count
invariant across folds. S1 = SEALED_UNTOUCHED.

## 9. Owner-pending law — namespaced decision slots (fail-closed while unsigned)

| slot | law it gates | adapter behavior while unsigned |
|---|---|---|
| `P5-FXEB-OD1` | PB2 lift for 6E/6B (P5-OD1; consumption order dependencies→censuses→courts→spec) | `require_synthetic()` raises on any non-SYNTHETIC panel; real-data execution NOT_RUN |
| `P5-FXEB-OD2` | FX ceiling + option (FX-A/B/C) + clock-shadow reading | `bind_option()` raises |
| `P5-FXEB-OD3` | CONV-D core delay-slot assignment | `bind_delay_slots()` raises; draft {D0,D1B} used for enumeration only |
| `P5-FXEB-OD4` | placebo budget (single-seed C1 default) | C1 shadow machinery stays single-seed; no ≥100-seed path exists |
| `P5-FXEB-OD6` | FX reg basis (consumes D3/e.4) | `consumable_rt_cost()` raises |
| `P5-FXEB-OD7` | e.1 FX fee alias corroboration | fee layer stays PARTIAL/UNDER REVIEW (co-blocker of the cost gate) |
| `P5-FXEB-OD9` | D12 residual-cell posture | `override_d12_posture()` always refuses; fail-closed exclusions stand |
| `P5-FXEB-OD10` | fold/warmup law freeze | `bind_warmup_law()` raises; both laws switchable, none binding |
| `P5-FXEB-OD11` | court §b1.1 anatomy commissioning | `request_f1_scored_spec()` always refuses |

(OD5/OD8 are consulted by the RMM package and the shared fill law respectively.)

## 10. K-views / era conditioning (evaluation labels, never identity splits)

Every intent carries `k_views`: era split 2020-22 vs 2023-26 (K5); DST-mismatch-week split
(K4 clock-bug detector); 6B London-share-drift split (built-in falsifier); 6E/6B trigger
co-occurrence diagnostic. Era conditioning shapes evaluation strata at a future freeze; it
never gates an individual signal in this adapter.

— End FROZEN_RULE_DRAFT (PROPOSED). Nothing herein freezes, registers, scores, or ratifies.
