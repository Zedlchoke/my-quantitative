# FROZEN_RULE_DRAFT — FX-F2 Policy-Decision Resolution (PROPOSED — never an approved freeze)

- Round **FUTURES-5SYM-PRESCORED-20261005**, wave-3, lane **ADAPT-FXEB**, 2026-10-05.
- **STATUS: PROPOSED / CONDITIONAL-ON-PB2-LIFT. PB2 HOLD stands** (PLAYBOOKS_DRAFT r5 §2;
  PB2_ANCESTRY_COURT_DRAFT §d; `PB2_HOLD_RESTATE.md` sha256 `88386aa3…5a75b`). Rule TEXT AS
  CODE ENFORCES IT for `adapter.py` in this directory; NOT an approved freeze; no scored
  run, no real-data execution, no registration. Outcome-blind: synthetic fixtures only.
- Parents: `../../fx_eb/SPEC_6E.md` §5/§7/§8/§9 · `../../fx_eb/SPEC_6B.md` §5/§7/§8/§9 ·
  `../../fx_eb/CALENDAR_PIT_POLICY_6E_6B.md` §4 · `../../fx_eb/COST_CONTRACT_6E_6B.md` ·
  `../../fx_eb/IDENTITY_BUDGET_6E_6B.md` §2/§4.1/§4.2/§6 · `../../hypo/CENSUS_5SYM.md`
  FX-F2 dossier · BoE MPC 2026 official capture: `../../cal_cost/captures/boe_mpc_live.html`
  (CAL_COST_REPORT EV-1: 2026 dates Feb-05, Mar-19, Apr-30, Jun-18, Jul-30, Sep-17,
  **Nov-05, Dec-17**; "Next due: 5 November 2026", Bank Rate 3.75% — forward-scheduled
  dates are never decisions) · `../../exec/symbol_contracts.json` rows 6E/6B.
- Family: **FX-F2 Policy-Decision Resolution** — ONE family, two legs with mutually
  exclusive day-sets per symbol (IDENTITY_BUDGET §2): **6E FOMC anchor leg** (13:00 CT,
  minute 780; first-5m ×17.24 vs control Wednesdays; re-amplification ×8.81 @13:40) and
  **6B MPC anchor leg** (12:00 Europe/London, minute 720, DST-proven across 8 UK/US
  mismatch dates; first-5m ×18.7). These are FX-F1's excluded day-sets (the competing
  structure). Power honesty: MDE ≈ 17.0 bp (6E, n=58 FOMC) / ≈ 20.6 bp (6B, n=56 MPC)
  vs RT 3.6–6.3 / 6.3–11.2 bp — detectable only at tail-event scale; **a null at this n
  is the pre-registered power death, NOT evidence of absence** (court §c3).

## 1. Observables and their timestamp-availability law (PIT)

| observable | definition as coded | knowable at (PIT) |
|---|---|---|
| FOMC stamps (6E anchor leg; 6B secondary) | injected `calendar.fomc_statements[]` = `{date, time_ct, kind, vintage_asof, provenance}` mirroring the committed archive inventory (30 rate-decision statements 2023→2026-09; 58 in-panel 2020–2026 with in-file release-time proof, 53 at 13:00 CT; 2020 emergency timings EXCLUDED from any base) | day level, 00:00 CT |
| MPC stamps (6B anchor leg) | injected `calendar.mpc_dates[]` = `{date, kind: change|hold, vintage_asof}`; 30 in-panel decisions 2023–2026 (11 rate-changes 5/2/4/0 by year, cross-checked vs `normalized/boe_bank_rate_tidy.parquet`); the cal_cost official 2026 capture upgrades the assembly to official provenance; 2026-11-05 / 2026-12-17 forward-scheduled rows are NEVER decisions | day level |
| ECB stamps (6E secondary stratum) | injected `calendar.ecb_dates[]`; 55/55 meetings 2020–2026.9, decision 14:15 CET/CEST (decision-minute ×1.73 — the weak-intensity family negative) | day level |
| anchor bar | 6E: the **13:00 CT** bar (minute 780) of the event session. 6B: the bar whose **Europe/London wall time == 12:00** (minute 720) — resolved via zoneinfo per session date (DST-correct by construction; the CT clock time varies 06:00↔07:00 across UK/US DST-mismatch weeks — that variation is the DST-proof, never hardcoded) | the anchor bar is consumed only AFTER it closes (decision time = anchor + 1 min) |
| first-5m window | bars anchor+1..anchor+5 (CT minutes); `sign(close(anchor+5) − close(anchor))` | close of the anchor+5 bar |
| spike ratio | anchor-bar volume / median volume of the 6 prior bars — DESCRIPTIVE label only (×17.24 / ×18.7 class), never a gate | after the anchor bar closes |
| ATR(20) | prior-20 held-session ranges, strict past (`fx_common.atr20_points`) | at decision time |

Vintage law (CALENDAR_PIT_POLICY §4): event calendars keyed to vintage as-of decision
date; **current-calendar inference FORBIDDEN**; surprise/consensus vintages NOT_RUN —
F2 conditions on event membership + realized first-5m sign ONLY.

PIT enforcement: every read via `fx_common.bars_upto` / `session_bars(..., upto)`;
pytest proof truncates the panel at the fill instant and requires identical
decision-instant outputs.

## 2. Signal definition

- **Universe (base)**: 6E = FOMC decision days with the 13:00-CT stamp class;
  6B = MPC days (change and hold POOLED in base; strata reported descriptively).
  Mutually exclusive vs FX-F1's base by construction (F1 excludes exactly these
  day-sets).
- **tail**: `UP` / `DN` from the first-5m sign; 0 move ⇒ NO-TRADE (`TRIGGER_FLAT`).
- **arms**: `RC` = enter in the window-move direction (resolution-drift/continuation);
  `RD` = enter opposite (spike-reversal). Both registered simultaneously.
- **controls**: `C1-SHADOW` same-anchor-minute non-event weekday placebo
  (single-seed/single-delay, seed 20261002-class, reading (a) default);
  `C2-ALW` always-in at the anchor (does SIGN carry information or just the day?);
  `C3-ANCHOR` FLAT-class floor. Family-specific negatives: 6E ECB stratum / 6B FOMC
  stratum — the ×17.24 > ×9.5 > ×1.73 (6E) and ×18.7 > ×9.5 (6B) intensity orderings
  are themselves part of the falsifiable claim.
- **strata (descriptive, never base-pool splits)**: `MPC_CHANGE` / `MPC_HOLD` (6B);
  `EMERGENCY_TIMING` (non-13:00 stamps — base-excluded, sensitivity only);
  `DOUBLE_EVENT` (6B MPC∩FOMC days — disclosed stratum, base-excluded).

## 3. Entry / exit / holding horizon

- **fill law**: entry assumes ≥ 1 minute post-release (T+60s law). **D0 = open of the
  anchor+6 bar** (the first-5m signal window completes at anchor+5); **D1B = open of
  anchor+7**; **D30M = open of anchor+36** (D0 + 30 minutes — the spike-decay detector
  per FX_HYPOTHESES §2.5; slots are the P5-FXEB-OD3 draft default {D0, D1B}, D30M =
  full-grid extension).
- **exit (whichever first)**: TP = entry ± 2 × SL_distance; SL = entry ∓ 1.0 × ATR(20);
  same-bar TP/SL ⇒ **SL-priority**; else mandatory flat at the **16:00 CT close**
  (6E ≈3h holding window from the anchor; 6B ≈9h window). Intraday, same session.
- Conservative fills: next-bar-open entry, no limit/queue/BBO claims (BBO NOT_RUN D5);
  slippage is first-order inside the decaying spike — tier sensitivity disclosed
  (COST_CONTRACT §2 hazard).

## 4. Session / event / calendar exclusions (fail-closed)

| code | law |
|---|---|
| `EMERGENCY_TIMING` | 6E/6B FOMC stamps not in the 13:00-CT class (2020 emergency timings) — base-EXCLUDED, sensitivity stratum only |
| `ECB_STRATUM_NO_BASE_TRADE` (6E) | ECB GC days — the weak-intensity negative; no base trade on the FOMC-anchor leg |
| `FOMC_STRATUM_NO_BASE_TRADE` (6B) | FOMC-only days on 6B — the secondary stratum; no base trade on the MPC-anchor leg |
| `DOUBLE_EVENT_EXCLUDED` | MPC∩FOMC days (6B disclosed stratum) — base-excluded |
| `NOT_AN_EVENT_DAY` | no injected decision stamp for this symbol's anchor leg ⇒ NO-TRADE |
| `ANCHOR_BAR_ABSENT` / `WINDOW_INCOMPLETE` / `TRIGGER_FLAT` | structural NO-TRADEs |
| `H6E_*` / `HOL_GRID_ABSENT_0OF42_DECLARED` / `QUARTER_NOT_OBTAINED_ROLL_ANCHOR` | shared holiday/quarter posture as FX-F1 (§4 of the F1 draft; 6B declaration never blocks) |
| `ATR_WARMUP_INSUFFICIENT` | <20 prior held sessions ⇒ NO-TRADE |

## 5. Roll / cease-guard handling

Held-contract-only fills (SPEC_6E §2 / SPEC_6B §2). Roll law law-pending (k=5 +
cease-guard, D9-extension; 27 measured switches, leads 13–19d / 17d —
`cost_roll_events_fxeb.json`); the adapter performs no chain construction. A decision
day may fall in a roll week; no additional roll exclusion on this family.

## 6. Tick / multiplier / cost binding

Identical binding points to the F1 draft §6 (`fx_common.load_fx_contract`; 6E
0.00005/$6.25/125k; 6B 0.0001/$6.25/62.5k; PLACEHOLDER session-mask disclosed-not-
consumed). Costs: same modeled ladder; 6B RT 6.3–11.2 bp is the cost-weakest leg in the
FX portfolio; consumable cost gate refuses while P5-FXEB-OD6/OD7 unsigned. The dead-spot
3.0 bp ancestry fence binds (court §b4): 6E 1.2–2.1×, 6B 2.1–3.7×.

## 7. Identity enumeration (exact DRAFT IDs, quoted from IDENTITY_BUDGET_6E_6B.md §4.1/§4.2)

FX-F2 = 8 core + 3 controls = **11 per leg** (CONV-D; the 6E ECB-day stratum (+8
core-class cells at S2-D0/D1B in full-grid) is a declared contingency, NOT in the 11):

```
FXF2-6E-RC-UP-D0-S2  FXF2-6E-RC-UP-D1B-S2  FXF2-6E-RC-DN-D0-S2  FXF2-6E-RC-DN-D1B-S2
FXF2-6E-RD-UP-D0-S2  FXF2-6E-RD-UP-D1B-S2  FXF2-6E-RD-DN-D0-S2  FXF2-6E-RD-DN-D1B-S2
FXF2-6E-C1-SHADOW    FXF2-6E-C2-ALW        FXF2-6E-C3-ANCHOR
FXF2-6B-RC-UP-D0-S2  FXF2-6B-RC-UP-D1B-S2  FXF2-6B-RC-DN-D0-S2  FXF2-6B-RC-DN-D1B-S2
FXF2-6B-RD-UP-D0-S2  FXF2-6B-RD-UP-D1B-S2  FXF2-6B-RD-DN-D0-S2  FXF2-6B-RD-DN-D1B-S2
FXF2-6B-C1-SHADOW    FXF2-6B-C2-ALW        FXF2-6B-C3-ANCHOR
```

Binding any OPTION raises on P5-FXEB-OD2; delay-slot binding on P5-FXEB-OD3.

## 8. Fold / warmup application

As F1 draft §8 (shared fold boundaries; warmup switchable FAMILY_60 default vs ES_252;
`bind_warmup_law` refuses on P5-FXEB-OD10 while unsigned). Folds multiply evaluation
only. n=58/56 event-day bases are tiny — fold splitting multiplies evaluation, never
power.

## 9. Owner-pending law — namespaced decision slots

Same slot table as the F1 draft §9 (all of OD1..OD11 consulted or inherited); F2-specific
notes: the owner **power acceptance** question (MDE ≈17.0/20.6 bp vs cost floors) is an
owner-owned pre-condition recorded in IDENTITY_BUDGET §6 — the adapter refuses scored
consumption via the same OD1/OD2 gates and carries the honesty labels on every intent.

## 10. K-views

Era split 2020-22 vs 2023-26; DST-mismatch split (6B anchor minute-720 stability is the
K4-analog clock law — a CT-clock-anchored implementation is a REFUSAL-class bug, tested);
BLS vintage regime 2025 (F3's law, inherited where day-sets touch); fee epoch windows
(none measured for FX inside 2020+).

— End FROZEN_RULE_DRAFT (PROPOSED). Nothing herein freezes, registers, scores, or ratifies.
