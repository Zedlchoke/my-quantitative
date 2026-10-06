# FROZEN_RULE_DRAFT — FX-F5 CIP / Rate-Differential Overlay (MACHINERY-ONLY, NEEDS_EVIDENCE)

- Round **FUTURES-5SYM-PRESCORED-20261005**, wave-3, lane **ADAPT-FXEB**, 2026-10-05.
- **STATUS: PROPOSED / CONDITIONAL-ON-PB2-LIFT / NEEDS_EVIDENCE / MACHINERY-ONLY.**
  FX-F5 has **0 standalone identities** (IDENTITY_BUDGET §2: overlays carry NO
  option-total cells); it exists ONLY as a regime SPLIT (×2 strata) on ONE chosen host
  leg (F1/F4) as a declared contingency. PB2 HOLD stands; the named missing evidence is
  NOT_RUN. Outcome-blind; synthetic fixtures only.
- Parents: `../../fx_eb/SPEC_6E.md` §10 item 10 · `../../hypo/CENSUS_5SYM.md` FX-F5
  dossier (6B-primary, 6E fragile) · `../../fx_eb/IDENTITY_BUDGET_6E_6B.md` §2 ·
  `../../meas_fx/meas_fx_m1_m3_cip_vintage.py` (the measurement harness — REFERENCED,
  never duplicated here).
- Mechanism (two-sided, declared UNKNOWN a priori): the US-minus-foreign policy
  differential regime plausibly modulates a host family's liquidity-absorption effect.
  Committed descriptive basis: 6B corr(roll-gap ticks, DFEDTARU − Bank Rate) = +0.8423 /
  Spearman +0.7445 (n=27 rolls); 6E sign agreement 27/27 but **vintage-fragile:
  r = +0.9097 latest-vintage vs r = −0.107 PIT-as-of** (ERRATUM MAJOR-2 class).

## 1. What the adapter implements (machinery only)

- **stratum split**: `diff > 0 → HIGH`, `diff ≤ 0 → LOW` on the host's evaluable days —
  as-of the decision date (vintage law). The host spec is otherwise UNCHANGED; an
  immaterial |Δ| band, where a host defines one, is the host's own noise exclusion.
- **vintage bookkeeping**: every series row carries its vintage stamp; the split
  consumes as-of values only. The latest-vintage vs PIT-as-of flip is the family's
  declared falsifier (K2-class).
- **no own signal / no own cost**: `signal()` always returns NO_TRADE with
  `OVERLAY_NO_OWN_SIGNAL`; zero own cost (host floors apply with **√2 MDE inflation**
  disclosed — halving the host n per stratum).

## 2. Evidence gate (fail-closed, raises)

`require_f5_evidence()` raises `RefusedPendingEvidence` with item
`F5_CIP_VINTAGE_QUANTIFICATION_NOT_RUN`: the vintage-sensitivity quantification has not
been executed, **and** the owner real-time SOFR source decision (court §d row 7) is
mandatory BEFORE any F5-conditioned registration. The measurement harness lives at
`meas_fx/meas_fx_m1_m3_cip_vintage.py` (run_m1/run_m3, K2 flip counter) — this adapter
references it and does not duplicate it.

## 3. Exclusions / folds / slots

Host's universe and exclusions apply unchanged; `apply_exclusions` delegates to the
host family's pass. Fold/warmup and the OD1..OD11 slot table are the host's (binding
behavior identical to the F1 draft §8/§9). Per-symbol notes: 6B differential =
DFEDTARU − Bank Rate (Bank Rate revision-free); the 2025-26 zero-differential window on
6B (four consecutive rolls at 0.00pp) is the built-in negative; 6E's differential is
vintage-fragile and carries no independent conditioning claim.

## 4. Ancestry fence (restated, binding)

Near-miss cluster: rows 56 (FXFV8-A5-P1), 64/65 (FXFV9-A5-P1/P2 PPP), 83
(FXNG1-A4-P2 — "the DGS10-level shadow remains the most lethal control in the forex
program"). FX-F5 is lawful ONLY as an overlay; **any standalone differential entry is
OUT-OF-LAW (DC §1.3 + H-G) and void** — the adapter structurally cannot produce one
(0 standalone IDs; signal always NO_TRADE).

— End FROZEN_RULE_DRAFT (PROPOSED, MACHINERY-ONLY). Nothing herein freezes, registers,
scores, or ratifies.
