# SYNTHESIS_K6 — FUTURES-K6GATE-PREP-20261004 per-symbol PREP-gate status (controller)

- Round: **FUTURES-K6GATE-PREP-20261004** over lanes NQ-K6 / ES-K6 /
  FXEB-K6 / FXJA-K6 (wave-1). Outcome-blind by law: **0 PnL, 0
  conditional-on-signal measurements, 0 scored trials, 0 registrations,
  0 parameter/family changes.** Every gate verdict below adjudicates
  ONLY its §0-PREDECLARED condition (anti-cherry-pick: the two
  EXPWITCH FAILs are reported, not re-tuned; F4-K6 was correctly
  withheld as conditional-on-signal and is NOT_RUN).
- Standing state unchanged: D3 unsigned (CYCLE-1 BLOCKED_COST_FREEZE per
  COST_FREEZE_ERRATUM — correction of record), no typed GO, ES cap 24
  FROZEN, PB2 HOLD, PB3 PARK, D8/D9 unratified, NO_GO all.

## 1. Gate verdict table (this round's measures)

| Symbol | Family / gate | Verdict | Decisive numbers (artifact) |
|---|---|---|---|
| NQ | NQ-F1 K6 FOMC anatomy | **PASS** | release 2.230× (≥2.0), pre 0.686× (≤0.85), n=85; repaired chain admits exactly 1 extra event (2020-04-29); era rows reproduce committed table bit-identically (`nq/m1_fomc_anatomy_v3.json`) |
| NQ | NQ-F2 K6 07:30-by-era | **PASS** | scoring-era spike 4.51× (≥2.0 [OPERATIONALIZED]); 2010-16 cell now measured 4.39×; canceled-day falsifier clean (no spike) (`nq/m5_0730_era_v3.json`) |
| NQ | NQ-F3 rebuild precondition (a1/a2 aggregates) | **DONE (descriptive)** | rebuilt ret series == nq_held_daily_v3 (max diff 0.0, 4,218 rets); 2020 DD 32.28%→34.12% == addendum figure; depleted sessions 77→27 (`nq/nq_f3_rebuild_a1a2.json`) |
| NQ | EXPWITCH-NQ F5-K6 | **FAIL** | part (i) PASS (ratios 1.271/1.184, 1.142/1.159 >1.0); part (ii) FAIL: 35/66 expiry Fridays carry 15-min RTH gaps (era-generic vendor granularity: ordinary Fridays 46/80 — post-hoc diagnostic, disclosed, non-adjudicating) (`nq/m2_expwitch_anatomy_v3.json`) |
| ES | EXPWITCH-ES F5-K6 | **FAIL** | part (i) FAIL: T3 1.220 < 1.25 (margin −0.030; T1 1.192/T2 1.269); part (ii) PASS (61/61 sessions clean; 08:30 ratios in band). AND-law ⇒ ES leg never enters scoring; margin table published for owner re-adjudication — NOT re-tuned post-hoc (`es/es_k6_gates.json`) |
| ES | ES-F1 F1-K6 FOMC-RES | **PASS** | 2.646× ≥2.0; pre-release 0.828 ≤0.85; n=91 timed events; era views non-adjudicating (`es/ES_K6_GATES.md`) |
| ES | ES-F2 F2-K6 MACRO-0730 | **PASS all 3 eras** | 3.416/2.504/2.955 ≥2.0; canceled-day falsifiers 0.843/0.918 (no spike); n=369 release days (`es/`) |
| ES | ES-F4 F4-K6 | **NOT_RUN** | conditions on price-derived signal — forbidden this round; disposition written §0.5 BEFORE compute |
| 6E/6B | FX-F1 court census | **PASS both** | 6E 1,362 / 6B 1,342 base triggers (≥500); court thinness NOT triggered; MDE-at-n ≈3.5bp/4.2bp (`fx_eb/fx_f1_f4_census.json`) |
| 6E/6B | FX-F4 census + 6B gap-std | **MEASURED** | weekday gaps n=1,282/1,283, std 0.0304%/0.0400%; Sunday stratum 317/317; 6B weekday dispersion 0.0486→0.0306% by era; no numeric threshold existed → none invented; 0/42 holiday hole stands (fail-closed unchanged) |
| 6E/6B | tick constancy @2020-11-23 | **CONSTANT both** | GCD 50,000 (6E) / 100,000 (6B) int-nano in all 5 sampled windows; closes R2 D-2 step (iii); proves the grid change is 6A-specific (`fx_eb/tick_constancy_6e6b.json`) |
| 6J | JF1-K3 anchor robustness | **DELIVERED** | label ANCHOR_INSENSITIVE_AT_45MIN over the 54 MPM days; all 7 shifted-anchor variants reported (`fx_ja/jf1_k3_anchor.json`; verifier re-checks label-vs-number consistency) |
| 6E/6B/6J | RMM D-1 mode ledger | **CLOSED (was NOT_RUN)** | abrupt/gradual: 6E 22/5, 6B 23/4, 6J 19/8 (derived; 6J exact 27/27; 6E/6B declared-calendar divergence itemized per K6(c), never normalized); 6A 21/6 reproduced; CEASE-SYNC: 18/24 abrupt weeks all-4-symbol ±1w (descriptive; block-shuffle placebo stays scored-side NOT_RUN) (`fx_ja/rmm_mode_ledger.json`) |
| 6A | D-2 tick-era audit (i+ii) | **DELIVERED** | era-1 RT 1-tick $104.92 = 15.18bp vs era-2 $54.92/8.20bp (MODELED); step test 6A ×0.50 USD/tick vs 6J ×1.00 same dates — era-2 cost models may NOT back-cast into era-1 (`fx_ja/aud_d2_tickera.json`) |
| all | session dispersion refreshes | **DELIVERED** | NQ 4,219 sessions incl. 2020 hole (49 sessions, 3.60bp); ES 4,204 (== census); 6J bar-identical to prior a2; 6A era split 231/1,515; prior committed tables reproduce everywhere except repaired windows (deltas shown, nothing overwritten) |

## 2. Per-symbol scored-readiness after this round (trial scored = 0)

| Symbol | PREP gates now | Still blocking scored (owner side) |
|---|---|---|
| ES | F1/F2 K6 PASS; F4 NOT_RUN (lawful); EXPWITCH-ES leg dead at gate (per family law); dispersion refreshed | **D3 cost-freeze signature (BLOCKED_COST_FREEZE)** → registration → prelaunch A7 → typed GO. Cap 24 unchanged (PB1-only slate unaffected by EXPWITCH result — it was never registered) |
| NQ | F1/F2 K6 PASS; F3 rebuild precondition DONE; EXPWITCH-NQ leg dead at gate (vendor-gap resolution = owner data-plane decision, NOT a re-tunable parameter) | D9 ratification + NQ ceiling + registration + A7 + GO (fee A7 executed clean earlier) |
| 6E/6B | FX-F1 census PASS (court thinness off); 6B gap-std MEASURED; tick constancy CONSTANT; anatomy/dispersion refreshed | **PB2 lift** + FX ceiling + registration + A7 + GO |
| 6J | JF1-K3 delivered; RMM mode ledger closed; dispersion refreshed | 6J ceiling + BBO/cost gates + registration + GO |
| 6A | D-2 audit delivered (era-1 cost table + step test); dispersion era-split | **PB3 lift + D8** (contingency annex unchanged) |

## 3. New findings recorded (append-only; nothing overwritten)

1. **FX_HYP §4.1 baseline-provenance defect** (FXEB M2c): the family
   doc's cited "reopen-gap" baseline (0.3778%, ratio 0.805, n=1,739) is
   generated as the 08:30-CT RTH-open gap, not the 17:00-CT reopen
   (true reopen gaps are 2.3-5× smaller, ratio 0.16). Recorded in
   `fx_eb/FXEB_K6_GATES.md`; the family doc stands as committed; any
   future FX-F4 freeze must consume the corrected interpretation.
2. **NQ 2020 dispersion now measured** (was hole): 49 sessions at 3.60bp
   mean |1m ret| — the D5/power tables for NQ families may now use the
   repaired window (post-freeze arithmetic, not this round's).
3. **EXPWITCH outcome** (both legs dead at their pre-declared F5-K6):
   the ten-hypo census hypothetical numbers stand as published (43/67
   arithmetic unaffected — nothing was registered); per the anti-
   cherry-pick law the threshold miss (−0.030 on T3) is NOT re-tuned;
   the owner may re-adjudicate the threshold at a future registration
   only as an explicit, disclosed amendment.
4. **ES-K6 material compute disclosures** (self-caught pre-adjudication,
   §0.8): RTH-core expected minutes corrected to 390; multi-contract
   contamination fixed by the family's own held-chain law (first-pass
   values discarded, not reported). One Thursday (2026-06-18 Juneteenth
   shift) present in the expiry calendar per the calendar authority.

## 4. NOT_RUN register (this round, by law not by omission)

ES-F4 K6 (conditional-on-signal); FX-F4 6B holiday-grid cells (0/42
NOT_OBTAINED stands); RMM block-shuffle placebo + JF1 K3 kill (both
scored-side by law); EXPWITCH monthly-opex dose stratum; BoJ/ABS/China
stamps and calendars (inherited NOT_RUN); BBO everywhere. Missing
evidence is NOT_RUN, never PASS.

— End SYNTHESIS_K6. Trial scored = 0; no family or parameter was changed
by any result in this document.
