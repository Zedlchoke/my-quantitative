# ADAPTER_MAP_6E_6B — per-family per-symbol adapter machinery map (PROPOSED)

- Round **FUTURES-5SYM-PRESCORED-20261005**, wave-3, lane **ADAPT-FXEB**, 2026-10-05.
- **STATUS: PROPOSED / CONDITIONAL-ON-PB2-LIFT machinery for owner review — never an
  approved freeze. Real-data execution NOT_RUN. Outcome-blind: signals/order-intent on
  synthetic fixtures only.** PB2 HOLD stands (P5-FXEB-OD1 gate in code).
- Test suite: `cd adapt_fx_eb && /Users/hoangminhlong/my-quantitative/.venv/bin/python
  -m pytest . -q` → **86 passed** (F1 19, F2 15, F3 18, F4 13, F5 6, F6 6, RMM 9).
  Shared machinery: `fx_common.py` (session/fold/cost/identity/slot/exclusion law);
  import pattern mirrors `adapt_nq/` (conftest on sys.path, per-family packages,
  `build_observables` / `signal` / `order_intent` / `apply_exclusions` pure functions).

## Map (candidate → SPEC → rule draft → adapter → fixtures → tests → blockers)

| family × symbol | SPEC section | rule draft | adapter | fixtures | tests | blockers (all fail-closed) |
|---|---|---|---|---|---|---|
| FX-F1 6E | `fx_eb/SPEC_6E.md` §2/§3/§4/§5/§7/§9 | `f1_london_range/FROZEN_RULE_DRAFT.md` | `f1_london_range/adapter.py` | `f1_london_range/fixtures/panel_6E.json` (+6B, EXPECTED_MANIFEST) | `test_adapter_f1.py` | OD1 (PB2), OD2, OD3, OD11 (court §b1.1 anatomy NOT_RUN), OD6/OD7 (cost gate), §b1.1 census PASS is measurement-only |
| FX-F1 6B | `fx_eb/SPEC_6B.md` §2/§3/§4/§5/§7/§9 (+ London-drift falsifier) | same draft (6B parameterization table) | same adapter (`sym="6B"`) | `panel_6B.json` | same | + holiday grid 0/42 declared (never an exclusion); MDE 4.2 bp < own cost floor |
| FX-F2 6E (FOMC leg) | `SPEC_6E.md` §5/§8/§9 | `f2_policy_decision/FROZEN_RULE_DRAFT.md` | `f2_policy_decision/adapter.py` | `f2_policy_decision/fixtures/panel_6E.json` (+6B) | `test_adapter_f2.py` | OD1/OD2/OD3/OD6/OD7; owner power acceptance (MDE ≈17.0 bp vs RT 3.6–6.3) |
| FX-F2 6B (MPC leg) | `SPEC_6B.md` §5/§8/§9 + cal_cost EV-1 BoE 2026 capture | same draft | same (London minute-720 anchor, DST-proof tested) | `panel_6B.json` | same | + MDE ≈20.6 bp vs RT 6.3–11.2 (cost-weakest); change/hold pooled strata |
| FX-F3 6E | `SPEC_6E.md` §5 (BLS vintage) | `f3_us0830/FROZEN_RULE_DRAFT.md` | `f3_us0830/adapter.py` | `f3_us0830/fixtures/panel_6E.json` (+6B) | `test_adapter_f3.py` | OD1/OD2/OD3/OD6/OD7; latency NOT_RUN; release-type census NOT_RUN; MDE ≈10.1 bp |
| FX-F3 6B | `SPEC_6B.md` §5 | same draft | same | `panel_6B.json` | same | + MDE ≈12.0 bp; 6B thin-k coverage law carried |
| FX-F4 6E | `SPEC_6E.md` §9 (F4) + M2c erratum | `f4_reopen_gap/FROZEN_RULE_DRAFT.md` (dual-window law) | `f4_reopen_gap/adapter.py` | `f4_reopen_gap/fixtures/panel_6E.json` (+6B) | `test_adapter_f4.py` | OD1/OD2/OD3/OD6/OD7; threshold NOT_RUN (registered-cycle decision); borderline cost viability |
| FX-F4 6B | `SPEC_6B.md` §8 (two standing gates) | same draft | same | `panel_6B.json` | same | + holiday stand-aside BLOCKED on 0/42 grid; cost-weakest leg (2.1–3.7× dead-spot proxy) |
| FX-F5 overlay (6B-primary; 6E fragile) | `CENSUS_5SYM.md` FX-F5 dossier | `f5_cip_overlay/FROZEN_RULE_DRAFT.md` | `f5_cip_overlay/adapter.py` (MACHINERY-ONLY) | `series_6E/6B.json` | `test_adapter_f5.py` | **NEEDS_EVIDENCE**: CIP-vintage quantification NOT_RUN + owner real-time SOFR decision (court §d row 7); 0 standalone IDs; harness `meas_fx/meas_fx_m1_m3_cip_vintage.py` referenced |
| FX-F6 overlay (6E host; 6B = falsifier) | `CENSUS_5SYM.md` FX-F6 dossier | `f6_cot_overlay/FROZEN_RULE_DRAFT.md` | `f6_cot_overlay/adapter.py` (MACHINERY-ONLY) | `series_6E/6B.json` | `test_adapter_f6.py` | **NEEDS_EVIDENCE**: intraday-transfer NOT_RUN (the transfer IS the hypothesis); harness `meas_fx/meas_fx_m2_transfer_harness.py` referenced; rows 107–109 release-clock-control law |
| RMM 6E | `CENSUS_5SYM.md` RMM §1-§13; mode ledger 22/5 | `rmm_roll_migration/FROZEN_RULE_DRAFT.md` | `rmm_roll_migration/adapter.py` (Role-A MACHINERY-ONLY) | `switch_table_6E/6B.json` | `test_adapter_rmm.py` | **Role-B gated**: P5-FXEB-OD5 (owner DC §1.3), interaction NOT_RUN, OD4 placebo ruling, PB2 |
| RMM 6B | same; mode ledger 23/4 | same | same | `switch_table_6B.json` | same | + holiday-adjacent switches EXCLUDE fail-closed |

## Shared-law consumption per family (what differs per symbol — never shared silently)

| law | 6E | 6B |
|---|---|---|
| tick / value / multiplier | 0.00005 / $6.25 / 125,000 | 0.0001 / $6.25 / 62,500 |
| fixed-point tick | 50,000 int-nano | 100,000 int-nano |
| FX-F2 anchor | 13:00 CT (minute 780), FOMC | 12:00 Europe/London (minute 720), MPC — DST-proven, tested |
| FX-F2 day-sets (F1-excluded) | FOMC ∪ ECB | MPC ∪ FOMC |
| holiday posture | 34/42; fail-closed lists (evidence-based 2023-11-24 + 93-cell neighborhoods + 8 aged-out) | 0/42 NOT_OBTAINED structural — DECLARED, never an exclusion |
| NOT_OBTAINED quarters (D12) | 2026-Q3/Q4 (ECU26/ECZ26) | 2023Q1–2024Q2 (BPH23..BPM24) |
| modeled RT band | 3.6–6.3 bp | 6.3–11.2 bp (2.1–3.7× dead-spot 3.0 bp) |
| F1 census / MDE | 1,362 triggers / ≈3.5 bp | 1,342 / ≈4.2 bp (below own cost floor) |
| F2 n / MDE | 58 FOMC / ≈17.0 bp | 56 MPC / ≈20.6 bp |
| F4 weekday reopen std | 0.0304% (n=1,282) | 0.0400% (n=1,283; era fall 0.0486→0.0306%) |
| RMM mode ledger (Role-A CLOSED) | 22 abrupt / 5 gradual | 23 / 4 |
| roll leads (measured) | 13–19 d where cells obtained | 17 d (2024Q4→2026Q3); 14 d into 2026Q4 |

## Owner-pending slots (namespaced P5-FXEB-OD1..OD11 — every one fail-closed in code)

| slot | gates | code surface |
|---|---|---|
| P5-FXEB-OD1 | PB2 lift (P5-OD1) | `require_synthetic()` — every adapter entry |
| P5-FXEB-OD2 | FX ceiling + option + clock-shadow reading | `bind_option()` |
| P5-FXEB-OD3 | CONV-D core delay slots {D0,D1B} vs {D0,D30M} | `bind_delay_slots()`; draft default used for enumeration only |
| P5-FXEB-OD4 | placebo budget | consulted by C1 machinery (single-seed default; no ≥100-seed path) |
| P5-FXEB-OD5 | RMM Role-B DC §1.3 | `request_rmm_role_b_identity()` |
| P5-FXEB-OD6 | FX reg basis (consumes D3/e.4) | `consumable_rt_cost()` |
| P5-FXEB-OD7 | e.1 FX fee alias corroboration | co-blocker of the cost gate |
| P5-FXEB-OD8 | BBO reaffirm (D5) | fill-law constants; no bypass exists |
| P5-FXEB-OD9 | D12 residual posture | `override_d12_posture()` always refuses |
| P5-FXEB-OD10 | fold/warmup law (60 vs 252) | `scoreable_sessions()` switchable; `bind_warmup_law()` refuses |
| P5-FXEB-OD11 | court §b1.1 anatomy commissioning | `request_f1_scored_spec()` always refuses |

— End ADAPTER_MAP_6E_6B (PROPOSED). Nothing herein freezes, registers, scores, or ratifies.
