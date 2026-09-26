# FALSIFIER BATTERY REPORT — ERP1-TRACKB-COHORT-1 (GO-1 scope, pre-PnL, terminal outcome)

- Verdict line: **F-1 one-shot ancestry rho = KILL_ANCESTRY_RHO. M1 (the only
  admitted mechanism) is dead pre-PnL. Cohort closes with 0 scored cells.**
- Measured: 2026-09-26. Freeze: TRIAL_FREEZE_v1.json (+FN-1) @ branch
  `orca/erp1-trackb-cohort-1-integration`. Skeptic lane computed the rho on
  the frozen representation (representation law honored).

## 1. Ordering law honored

Data gate (staging v1, manifest f6028626…) → F-0 (class court + DTX
precondition, ruling 310fe03e…) → F-2 PIT fixtures → F-3/F-6 construction +
feasibility → **F-1 one-shot rho (skeptic)** — all BEFORE any PnL-bearing
computation. Zero PnL was computed anywhere in this cycle. Observed scored
cells: 0/7.

## 2. F-1 one-shot ancestry rho (authority: SKEPTIC_F1_RHO_VERDICT.md)

| Dead reconstruction | Pooled |rho| binary | Pooled |rho| continuous | Faithful? |
|---|---|---|---|
| CARRY-BAB funding proxy (V16 razor ref) | **0.5308** | **1.0000** | YES — identity |
| BASISLV-PREMFADE-28D basis axis | **0.3337** | 0.7331 | YES |
| CARRY-7D (V6) | 0.0795 | 0.5101 | partial (binary under, continuous over) |
| CARRY-1D / CARRY-3D | 0.174 / 0.097 | — | partial |
| FUNDCROWD-MR-v2 percentile | 0.1901 | — | partial (under by 0.0099) |

The kill is structural, not marginal: FN-1's expected-carry estimator IS
the trailing-90d mean of settled funding — the same observable the dead
carry class consumed in window (V6), change (V17 FUNDJUMP 0.2439) and
percentile (FUNDCROWD) forms. The continuous rho vs the CARRY-BAB proxy is
1.0000 by construction. The skeptic's pre-registered warning ("any class
whose entry is monotone in funding level should expect > 0.20") was the
correct prior. Bar 0.20 immovable; no rescue by re-gating (§6).

## 3. PIT battery F-2 (all PASS — the law is PIT-clean as executed)

- M-1 independent-impl equivalence PASS (naive loop == bisect form, 270-settlement window).
- M-2 one-epoch delay moves 6.03% of epochs (non-vacuous); state series non-constant. PASS.
- M-3 panel-truncation replay **318/318 epochs byte-identical** (P-18 law holds: settled-only consumption).
- M-4 stamps/headers normalized (spot zips headerless, perp zips headered; 1h open-time grid verified; channels separated). PASS.
- M-5 single-poison future-settlement probe: 0/50 state changes (22 epochs have a settlement exactly at T — legally consumable per frozen law). PASS.

## 4. F-3 / F-6 corrected facts (full dev grid 2020-07-24..2026-08-21, 318 epochs)

- Occupancy 221/318 = 69.5% (persistent gate); threshold sensitivity fires
  at C*=45/50/60: 221/201/166.
- Non-overlapping 35d holds: **42 ≥ 40 floor** — G5 population reachable
  (the earlier 34<40 was a truncation artifact, see incidents).
- Last-6m: **2 edge fires only** (2026-08-14 ec 47.9; 2026-08-21 ec 49.4
  bps; plus 2026-02-06 ec 46.3 just outside the 6m slice) — recent-window
  expected carry sits at/below the ×2.0 bill: the F-5 knife-edge picture
  (COSTEXEC §4) is confirmed by the gate's own behavior.
- F-3 permutation control: constructible; Jaccard distance 0.471 vs chance
  0.467 — the frozen ≥90%-differ predicate (sparse-firing template) is
  structurally inapplicable to a persistent gate: DISCLOSED, never waived.
  Moot under the F-1 kill.

## 5. Incidents (all recorded, none silently repaired)

- **I-1** staging attempt-1 mkdir defect (zero exposure, lock released; fixed + re-run).
- **I-2** spot 2025+ vision zips use MICROSECOND open_time; the loader's ms
  guard silently truncated the epoch grid at 2024-12-27 — caught by the
  skeptic lane's independent count; loader now normalizes scale; series
  regenerated (318 epochs); corrected numbers govern everywhere.
- **I-3** fixture v1 design defects (M-2 drop-last-settlement probe; M-5
  multi-poison cross-contamination) — both re-derived to the frozen
  semantics before any verdict was relied upon; v1 verdicts void, v2 governs.
- **I-4** my prose "0 fires last 6m / 34<40 holds" was wrong (truncation
  artifact); corrected to 2 edge fires / 42 holds per I-2 fix.

## 6. Consequence (frozen law, mechanical)

- M1-ANCHOR/N1/N2/CAUSAL/INVERTED/BASELINE + DIAG-DTX: `NOT_SCORED_FALSIFIED`
  / `NOT_RUN_HOST_KILLED` (ledger rows appended; DTX BC-2/BC-4 stand).
- Slots 2–3 were already EMPTY (F-0 court). The cohort's terminal label
  (umbrella §9 vocabulary): **REJECT_ALL** (the admitted mechanism class was
  killed by its own preregistered falsifier before scoring; 0/7 cells).
- Future-cohort conditions (skeptic, binding): a NON-funding-level PIT axis
  (OI / liquidation tape — both BLOCKED today) or a dated measured
  cost-regime break. No re-window, re-gate, re-threshold, or re-cadence on
  this surface can revive it (no-rescue law, owner list verbatim).
