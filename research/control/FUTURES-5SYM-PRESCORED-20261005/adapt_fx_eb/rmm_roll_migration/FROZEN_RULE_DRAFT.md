# FROZEN_RULE_DRAFT — RMM Roll-Migration Mode (Role-A MACHINERY-ONLY; Role-B owner-gated)

- Round **FUTURES-5SYM-PRESCORED-20261005**, wave-3, lane **ADAPT-FXEB**, 2026-10-05.
- **STATUS: PROPOSED / CONDITIONAL-ON-PB2-LIFT. Role-A = construction ledger, 0 IDs,
  machinery-only in this lane (the ledger itself is CLOSED — k6gate D-1). Role-B =
  NEEDS_EVIDENCE + owner-gated.** PB2 HOLD stands; outcome-blind; synthetic fixtures only.
- Parents: `../../hypo/CENSUS_5SYM.md` RMM dossier (§1-§13) ·
  `../../fx_eb/IDENTITY_BUDGET_6E_6B.md` §4/§5 item 5/§6 (DC §1.3) ·
  `../../fx_eb/CALENDAR_PIT_POLICY_6E_6B.md` §2 · `../../fx_ja/rmm_mode_ledger.json`
  (mode ledger 6E 22/5, 6B 23/4 abrupt/gradual — DERIVED, Role-A CLOSED) ·
  `../../exec/symbol_contracts.json` 6E/6B rows.
- Mechanism [HYPOTHESIS, Role-B INFERENCE-grade]: when quarterly FX migration is
  COMPRESSED (cease-guard-triggered switch), the receiving contract's post-switch window
  may carry a mode-dependent pressure signature (M-COMPRESS-REV vs M-COMPRESS-CONT) that
  gradual (crossover-triggered) rolls do not show. **The mode × post-switch-drift
  interaction has never been measured — that measurement IS the family.**

## 1. What the adapter implements (machinery only)

- **Role-A construction ledger helpers** (0 identities): deterministic mode-split
  counting over an injected mode-label table; per-symbol cited ledger constants
  (6E 22/5, 6B 23/4); switch-session classification for the exclusion law
  (event-stacking, holiday-adjacency).
- **Role-B refusal**: `request_rmm_role_b_identity(sym, k)` raises
  `RefusedPendingOwnerDecision("P5-FXEB-OD5")` — the owner DC §1.3 boundary ruling is
  required before any Role-B registration; the detail also records that the interaction
  measurement is NOT_RUN and PB2 HOLD stands. `signal()` always refuses
  (`ROLE_A_CONSTRUCTION_ONLY` / no entries).
- **Role-B law sketch (recorded, NOT implemented as a signal)**: signal day = switch
  session t; entry = open of the first 1m bar after t close; delay variants +1 bar/+30m;
  direction = the two arms both tails; TP 2×SL / SL 1.0×ATR(20 same-window); time exit
  switch+K (K=5 sessions [PROVISIONAL]); C1 = mode-BLOCK-shuffle placebo (≥100 seeds,
  iid forbidden — sits OUTSIDE the +4 IDs pending the placebo ruling P5-FXEB-OD4);
  family negative = the gradual-mode rolls themselves.

## 2. Switch-session exclusion law (implemented for the ledger)

| code | law |
|---|---|
| `EVENT_STACKING_EXCLUDED` | switch sessions overlapping central-bank decision windows (FOMC/ECB/MPC day-sets) excluded — flagged stratum, never base |
| `HOLIDAY_ADJACENT_SWITCH_EXCLUDED_6B` | 6B holiday-adjacent switches EXCLUDED fail-closed (grid 0/42 posture applied conservatively at the switch) |
| `QUARTER_NOT_OBTAINED_ROLL_ANCHOR` | quarters with no official expiry cell carry no roll anchor (D12) |
| mode-label PIT law | the mode label is a strict-past classification decided at close t, effective t+1 (DC §1.3 timing law) |

## 3. Identity enumeration (exact DRAFT IDs, quoted from IDENTITY_BUDGET_6E_6B.md §4)

Role-A = **0 identities** (construction). Role-B = `FXRMM-<SYM>-RB1..RB4` (+4/leg,
DC §1.3-gated; FX-C only). Mints refuse while P5-FXEB-OD5 is unsigned.

## 4. Cost / power honesty (carried)

MODELED / UNDER REVIEW; shared FX tier table; at pooled n≈108 FX events MDE ≈ 12.5
bp-class vs RT 3.6–6.3 (6E) / 6.3–11.2 (6B) — power-marginal by construction; a null at
this n is the pre-registered K2 death, NOT evidence of absence. K1 block-shuffle
reproduction, K3 gradual≈abrupt, K4 delay flip, K5 era concentration, K7 DC §1.3
gap-level/differential leakage are the standing kill set (census RMM field 7).

— End FROZEN_RULE_DRAFT (PROPOSED). Nothing herein freezes, registers, scores, or ratifies.
