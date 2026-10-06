# RANKING_INPUT — 6E/6B hypothesis families, outcome-blind prioritization input (P1-6E6B)

- Task `FUTURES-OVERNIGHT-PREP-20261003`, lane **P1-6E6B**, 2026-10-04 UTC.
- **Rubric: evidence-coverage × mechanism-specificity × falsifiability.**
  Mechanical: each axis scored 0-3 against pre-stated anchors; score = product
  (0-27). **No return statistics, no PnL, no expectancy, no hit-rate, no
  variance-of-any-signed-return enter any score — nothing has been run.**
  Scores describe the QUALITY OF THE PRE-REGISTRATION PACKAGE ONLY.
- Families are defined in `FX_HYPOTHESES.md` (11 fields each) /
  `fx_hypotheses.json`. PB2 HOLD: FX-F1 is scored for completeness but is
  **not eligible for any scheduling action** while HOLD stands.

## Axis anchors (fixed before scoring)

**Evidence-coverage (EC)** — measured evidence available NOW:
- 3 = trigger-window anatomy measured on this venue + PIT calendar
  PASS_EVIDENCED + coverage/hole proof for the family's day-set.
- 2 = anatomy measured at adjacent windows, or PIT partial (calendar passes
  but a declared dependency/latency hole remains, or anatomy NOT_RUN on one
  symbol leg).
- 1 = mechanism-level analogies/conditioning basis only.
- 0 = nothing measured.

**Mechanism-specificity (MS)** — could the dead FOREX-FREE-V1/V2 corpus have
represented this claim (court §b)?
- 3 = mechanism class the dead corpus could NOT represent (event conditioning
  impossible by their law; venue-specific microstructure claim) AND distinct
  information source.
- 2 = partially overlapping with a dead family's signal class — distinction
  must be measured (court's honest category).
- 1 = same signal-family claim as a dead ancestor.
- 0 = unspecified mechanism.

**Falsifiability (FA)** — can a future registered cycle refute it sharply?
- 3 = pre-freezable descriptive gates (census/anatomy) + power floor
  reachable at realistic n (MDE ≤ modeled-cost scale).
- 2 = refutable but power-limited (MDE at/above cost scale at realistic n, or
  required descriptive gate still NOT_RUN).
- 1 = heavily power-starved (MDE ≥ ~3× cost), or blocked on an owner-gated
  dependency.
- 0 = unfalsifiable.

## Scores

| family | symbol leg | EC | MS | FA | product | one-line basis (all facts OBSERVED/DERIVED in FX_HYPOTHESES.md) |
|---|---|---|---|---|---|---|
| FX-F1 | 6E | 3 | 2 | 2 | **12** | full anatomy + DST proof + court package; ancestry overlap V2-A4-P2; census NOT_RUN + MDE≈cost at n≈300-900 |
| FX-F1 | 6B | 3 | 2 | 2 | **12** | same + London-drift built-in falsifier; cost 2.1-3.7× dead floor |
| FX-F3 | 6E | 2 | 3 | 2 | **12** | ×1.95 anatomy + RV-share; CPI/EMPSIT PASS but type-census/latency NOT_RUN; n≈165 → MDE ≈ 10 bp > cost |
| FX-F3 | 6B | 2 | 3 | 2 | **12** | same; drift split mandatory |
| FX-F2 | 6E (FOMC) | 3 | 3 | 1 | **9** | ×17.2 anatomy + 58/58 PIT perfect; n=58 → MDE ≈ 17 bp ≈ 3-5× cost |
| FX-F2 | 6B (MPC) | 3 | 3 | 1 | **9** | 18.7× + minute-720 DST-stable; n=56 → MDE ≈ 21 bp |
| FX-F4 | 6E | 2 | 2 | 2 | **8** | gap-std measured 0.378% + DST experiment; no trigger census; MS overlaps dead session-momentum class |
| FX-F4 | 6B | 1 | 2 | 2 | **4** | **gap anatomy NOT_RUN on 6B (gate)** + cost-viability doubt 6.3-11.2 bp RT |
| FX-F5 | overlay | 2 | 3 | 1 | **6** | 6B corr +0.84 measured; vintage-fragile 6E; owner-gated → FA 1 |
| FX-F6 | 6E overlay | 3 | 2 | 1 | **6** | 1,082wk + vol-descriptive measured; intraday transfer NOT_RUN |

Tie-break (mechanical, pre-stated): (1) product; (2) EC desc; (3) FA desc;
(4) MS desc; (5) family id asc.

## Resulting order (per symbol, eligible set; F5/F6 overlays listed separately)

- **6E: FX-F1 (12) = FX-F3 (12) > FX-F2 (9) > FX-F4 (8)** — tie F1/F3 broken
  by EC (3 vs 2): F1 first. Overlays: F6 (6) eligible on 6E hosts; F5 (6)
  blocked pending owner decision.
- **6B: FX-F1 (12) = FX-F3 (12) > FX-F2 (9) > FX-F4 (4)** — same tie-break.
  F5 measured basis strongest on 6B (+0.84) but registration-blocked.

**Top-3 (both symbols, outcome-blind): 1) FX-F1 London-Range Absorption
(H-C/H-D); 2) FX-F3 US-8:30 Spillover; 3) FX-F2 Policy-Decision Resolution.**

Caveats stated plainly: (i) FX-F1's rank is CONTINGENT on PB2 HOLD — first
schedulable action for F1 is the court's descriptive census (≥500-trigger
gate), not any scored cell; (ii) FX-F3 overtakes F1 on mechanism-specificity
if the Co-Owner values dead-corpus distinguishability over anatomy
completeness — the rubric's EC-first tie-break is a stated choice, not a
fact; (iii) FX-F4-6B is ranked last not by preference but by a measured gate
(gap anatomy NOT_RUN) plus the court's own cost finding.

— End RANKING_INPUT. No outcome data existed to be blind to; none was used.
