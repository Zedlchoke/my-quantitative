# FROZEN_RULE_DRAFT — FX-F6 Crowded-Positioning Overlay (MACHINERY-ONLY, NEEDS_EVIDENCE)

- Round **FUTURES-5SYM-PRESCORED-20261005**, wave-3, lane **ADAPT-FXEB**, 2026-10-05.
- **STATUS: PROPOSED / CONDITIONAL-ON-PB2-LIFT / NEEDS_EVIDENCE / MACHINERY-ONLY.**
  FX-F6 has **0 standalone identities**; it exists ONLY as a percentile SPLIT (≥80 /
  ≤20, mid = negative stratum) on ONE chosen **6E** host leg. **6B is the measured
  falsifier, not a second leg** (corr(|z|, fwd vol20) = −0.074, n=326). PB2 HOLD stands.
- Parents: `../../hypo/CENSUS_5SYM.md` FX-F6 dossier · `../../fx_eb/IDENTITY_BUDGET_6E_6B.md`
  §2 · `../../meas_fx/meas_fx_m2_transfer_harness.py` (strict_past_percentile /
  assign_strata / transfer_statistic — REFERENCED, never duplicated).
- Mechanism (two-sided): crowded CoT positioning changes the book's volatility response;
  the committed fwd-21d-vol fact (≥80th pctile 6.52% vs ≤20th 7.68%, n=347 joined,
  release-safe obs+3, strict-past percentiles) transferring to the intraday horizon IS
  the hypothesis — and that transfer measurement is **NOT_RUN**.

## 1. What the adapter implements (machinery only)

- **stratum split**: pctile ≥ 80 → HIGH, pctile ≤ 20 → LOW, else MID_NEGATIVE — on the
  host's evaluable days; strict-past 3y-rolling percentiles, release-safe obs+3 (the
  CoT PIT structure Tue-observe / Fri-15:30 release is consumed as carried data).
- **no own signal / no own cost**: `signal()` always NO_TRADE (`OVERLAY_NO_OWN_SIGNAL`);
  host cost floors apply with √2 MDE inflation disclosed; the mid-pctile (20–80)
  stratum is the built-in negative.

## 2. Evidence gate (fail-closed, raises)

`require_f6_evidence()` raises `RefusedPendingEvidence("F6_INTRADAY_TRANSFER_NOT_RUN")`
naming the harness. The 0-ID transfer measurement is a PREP-legal item owned by the
meas_fx harness — this adapter duplicates nothing.

## 3. Standing ancestry fence

Rows 107–109 (COMMNG1-A4-P2 ×3 arms, CONTROL_OUT_EARNS_RELEASE_CLOCK): the bare
release-clock control out-earned every positioning book; the positioning frontier is
measured-closed on that substrate. **Any F6 scored future must carry the release-clock
control, and any drift toward standalone or release-clock constructions is void** —
the adapter structurally emits no standalone signal.

## 4. Slots / folds

Host's OD1..OD11 posture and fold/warmup law apply unchanged.

— End FROZEN_RULE_DRAFT (PROPOSED, MACHINERY-ONLY). Nothing herein freezes, registers,
scores, or ratifies.
