# FROZEN_RULE_DRAFT — FX-F4 Globex Reopen Gap (PROPOSED — never an approved freeze)

- Round **FUTURES-5SYM-PRESCORED-20261005**, wave-3, lane **ADAPT-FXEB**, 2026-10-05.
- **STATUS: PROPOSED / CONDITIONAL-ON-PB2-LIFT. PB2 HOLD stands** (`PB2_HOLD_RESTATE.md`
  sha256 `88386aa3…5a75b`). Rule TEXT AS CODE ENFORCES IT for `adapter.py`; NOT an
  approved freeze. Outcome-blind; synthetic fixtures only.
- Parents: `../../fx_eb/SPEC_6E.md` §9 (F4 power) · `../../fx_eb/SPEC_6B.md` §8 (F4 two
  standing gates) · `../../fx_eb/CALENDAR_PIT_POLICY_6E_6B.md` §2/§3/§5 ·
  `../../fx_eb/COST_CONTRACT_6E_6B.md` §2/§3/§4 · `../../fx_eb/IDENTITY_BUDGET_6E_6B.md`
  §4.1/§4.2/§6 · `../../hypo/CENSUS_5SYM.md` FX-F4 dossier · **M2c erratum (BINDING on
  any future freeze)**: `../../fx_eb/FXEB_K6_GATES.md` finding 1 — the family-doc
  baseline "reopen-gap std 0.3778%" (ratio 0.805, n=1,739) was generated as the **08:30-CT
  RTH-open gap**, not the 17:00-CT reopen; true 17:00 reopen gaps are **2.3–5× smaller**
  (ratio ≈ 0.16); recorded append-only, nothing overwritten — every FX-F4 consumption
  uses the corrected interpretation.
- Family: **FX-F4 Globex Reopen Gap** — 17:00-CT reopen vs 16:00-CT prior close, after
  the 60-minute maintenance break. Census: weekday reopen gaps n=1,282 (6E, std
  0.0304%) / n=1,283 (6B, std 0.0400%); Sunday stratum 317/317; 6B weekday dispersion
  0.0486→0.0306% by era [MEASURED, `fx_f1_f4_census.json`]. 6E borderline cost
  viability; **6B cost-weakest in the portfolio (RT 6.3–11.2 bp) with the holiday
  stand-aside BLOCKED on the 0/42 grid**.

## 1. The two windows (distinct, labeled — M2c erratum implemented)

| window | definition as coded | status |
|---|---|---|
| `WINDOW_A_REOPEN_1700_PRIMARY` | gap_A = open(17:00-CT session-opening bar) − prior held-session 16:00-CT close, same held chain | **PRIMARY — the only signal source** |
| `WINDOW_B_RTH_OPEN_0830_ERRATUM_BASELINE` | gap_B = open(08:30-CT bar) − prior held-session 16:00-CT close | **ERRATUM BASELINE — measurement/diagnostic ONLY; never a signal source**; every observables payload carries both gaps + their ratio so the corrected premise scale (gap_A ≪ gap_B class) is auditable |

## 2. Observables and PIT law

| observable | knowable at (PIT) |
|---|---|
| prior held-session 16:00-CT close | at/after that session's close (session aggregate; held-contract-only) |
| 17:00-CT reopen print (session-opening bar open) | at the reopen print |
| 08:30-CT RTH-open print | at that bar's open |
| gap_A / gap_B / ratio | after the 08:30 bar opens (for signal purposes only gap_A matters and it is knowable at 17:00) |
| ATR(20) | strict past (prior-20 held sessions) |

## 3. Signal / entry / exit / horizon

- **threshold law**: signal = sign(gap_A) **beyond a minimum-gap threshold**. The exact
  threshold value is a registered-cycle decision, never tuned in PREP (SPEC NOT_RUN
  item 9) ⇒ the adapter REQUIRES an explicit `min_gap_threshold` argument; `None` ⇒
  NO-TRADE with `THRESHOLD_NOT_REGISTERED`. Fixture thresholds are synthetic parameters,
  labeled SYNTHETIC-PARAMETER-NOT-REGISTERED in the manifests — they exercise machinery,
  they register nothing.
- **tails**: `UP`/`DN` from sign(gap_A) when |gap_A| > threshold; else
  `GAP_BELOW_THRESHOLD` (the zero/minimum-gap-day placebo class).
- **arms**: `GC` = continuation into the Asia leg; `GD` = revert once primary liquidity
  arrives. Both registered.
- **fill**: T+5m law — **D0 = open of the 17:05-CT bar** (the 17:00 auction minute is
  excluded; five full minutes after the print); D1B = 17:06; D30M = 17:35. Conservative
  next-bar-open; BBO NOT_RUN — and the $18.75 close-proxy spread is likely MOST
  biased-low exactly here (17:00 CT thin window, p05 session volume 7,904 contracts;
  COST_CONTRACT §2 hazard) — disclosed on every intent.
- **exit (whichever first)**: TP = entry ± 2 × SL_distance; SL = entry ∓ 1.0 × ATR(20);
  same-bar SL-priority; else **time exit at the 09:00-CT bar close** [PROVISIONAL —
  before the London/US information blocks]. Intraday.

## 4. Session / event / calendar exclusions (fail-closed)

| code | law |
|---|---|
| `ROLL_SESSION` / `SESSION_AFTER_ROLL` | roll sessions + the session after a roll EXCLUDED (chain-construction artifact law); roll law itself law-pending (k=5 + cease-guard, D9-extension; 27 measured switches, leads 13–19d/17d) |
| `SUNDAY_REOPEN_STRATUM` | Sunday-evening opens (session opening on a Sunday 17:00 CT) are a SEPARATE stratum (317/317; 1.9% of front volume) — never the base; `-SUN` = declared contingency, not in the 11 |
| `H6E_EVIDENCE_BASED_DEVIATION` / `H6E_NEIGHBORHOOD_FAIL_CLOSED` / `H6E_AGED_OUT_NEIGHBORHOOD` | 6E holiday fail-closed classes (CALENDAR_PIT_POLICY §3.1; 2022 Monday-halt regime change handled year-aware, pre-2022 Monday sessions never silently pooled) |
| `HOL_GRID_ABSENT_0OF42_DECLARED` | 6B — DECLARATION, not exclusion: holiday-adjacent 6B sessions neither excluded nor certified clean; **the 6B F4 holiday stand-aside stays BLOCKED on the grid** |
| `QUARTER_NOT_OBTAINED_ROLL_ANCHOR` | 6E 2026-Q3/Q4; 6B 2023Q1–2024Q2 (D12 posture) |
| `PRIOR_SESSION_CLOSE_ABSENT` / `ATR_WARMUP_INSUFFICIENT` / `ANCHOR_BAR_ABSENT` / `THRESHOLD_NOT_REGISTERED` / `GAP_BELOW_THRESHOLD` | structural NO-TRADEs |

## 5. Tick / multiplier / cost binding

As F1 draft §6. F4-specific cost honesty: the corrected premise scale (ratio ≈ 0.16)
lowers the effect-size prior materially versus the family-doc text — the r = RT/MDE
arithmetic must be re-derived at any freeze (`meas_fx/meas_fx_m4_f4_rt_mde.py` owns the
MDE arithmetic; this adapter duplicates nothing). 6E borderline; 6B carries the explicit
cost-viability doubt.

## 6. Identity enumeration (exact DRAFT IDs, quoted from IDENTITY_BUDGET_6E_6B.md §4.1/§4.2)

FX-F4 = 8 core + 3 controls = **11 per leg** (CONV-D; Sunday stratum +36 = contingency;
RMM `FXRMM-<SYM>-RB1..RB4` +4 are the RMM package's, DC §1.3-gated):

```
FXF4-6E-GC-UP-D0-S2  FXF4-6E-GC-UP-D1B-S2  FXF4-6E-GC-DN-D0-S2  FXF4-6E-GC-DN-D1B-S2
FXF4-6E-GD-UP-D0-S2  FXF4-6E-GD-UP-D1B-S2  FXF4-6E-GD-DN-D0-S2  FXF4-6E-GD-DN-D1B-S2
FXF4-6E-C1-SHADOW    FXF4-6E-C2-ALW        FXF4-6E-C3-ANCHOR
FXF4-6B-GC-UP-D0-S2  FXF4-6B-GC-UP-D1B-S2  FXF4-6B-GC-DN-D0-S2  FXF4-6B-GD-DN-D1B-S2
FXF4-6B-GD-UP-D0-S2  FXF4-6B-GD-UP-D1B-S2  FXF4-6B-GD-DN-D0-S2  FXF4-6B-GD-DN-D1B-S2
FXF4-6B-C1-SHADOW    FXF4-6B-C2-ALW        FXF4-6B-C3-ANCHOR
```

## 7. Fold / warmup / slots / K-views

Folds + the switchable 60/252 warmup as F1 draft §8 (binding on P5-FXEB-OD10). Slots
OD1..OD11 as F1 draft §9. K-views: era split (6B dispersion FELL a third across eras —
0.0486→0.0306% — anatomy only); DST-mismatch split (K4 clock bug); zero/minimum-gap-day
placebo (below-threshold days); roll-adjacency stratum.

— End FROZEN_RULE_DRAFT (PROPOSED). Nothing herein freezes, registers, scores, or ratifies.
