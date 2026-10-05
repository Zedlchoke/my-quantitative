# VERDICT TABLE — A7_NEGVERIFY · NBA-PLAYERFEAT-SCORED-V1 · independent verification of the NEGATIVE

All numbers recomputed by A7-OWN code from raw bytes (see A7_VERIFICATION_REPORT.md and
`verify/*.json`). Sign convention as in the lane: ΔLL = LL(arm) − LL(B1*); Δ < 0 favors the arm.

| # | verification task | lane claim | A7 own recompute | result |
|---|---|---|---|---|
| 1 | B1* pooled fold LL (n=4599) | 0.6383266072624096 | 0.6383266072624096 (err 0.0, req ≤1e-9) | MATCH |
| 2 | B1* calibration slope | 0.780102170044627 | 0.780102170044627 (err 0.0) | MATCH |
| 3 | PF-A φ=−25 ΔLL point | +0.0050383739170385316 | +0.005038373917038531 (err 8.7e-19) | MATCH |
| 4 | PF-A φ=−25 ΔLL 95% CI | [+0.00170997, +0.00837455] | [+0.00170997, +0.00837455] own indep. bootstrap (err ≤8.7e-19; tol 5e-4) | MATCH |
| 5 | PF-B φ=+25 ΔLL point | +0.004247277631594099 | +0.004247277631594098 (err 8.7e-19) | MATCH |
| 6 | PF-B φ=+25 ΔLL 95% CI | [+0.00147987, +0.00711801] | [+0.00147987, +0.00711801] own indep. bootstrap (err ≤8.7e-19) | MATCH |
| 7 | full 3×5 grid pooled LL vs ledger | 15 rows | all match; max abs err 1.1102e-16 | MATCH |
| 8 | grid minimum per arm | φ=0 for all 3 arms | φ=0 for all 3 (ledger AND own recompute) | CONFIRMED |
| 9 | every non-zero φ raises pooled LL vs B1* | claimed | true for all 12 non-zero configs | CONFIRMED |
| 10 | designed null φ=0 ≡ B1*, real fold rows | max\|Δp\|=0.0 | max\|Δp\|=0.0 (PF-A/PF-B/PF-C, own code) | PASS |
| 11 | designed null on A7-OWN synthetic streams | (lane: 3 own streams) | max\|Δp\|=0.0 on 3 A7 streams (seeds 101/202/303) | PASS |
| 12 | season cap code + behavior | doctored 2022 aborts | SEASON_MAX_REAL=2021 (harness.py:72); own tmp doctored probe ABORTS SEASON_CAP_VIOLATION; healthy copy max season 2021 | PASS |
| 13 | evaluate-oos real-data refusal | refuses without GO | exit 1, OOS_REFUSED_NO_GO_TOKEN, raised pre-read; GO token absent | PASS |
| 14 | ledger completeness | 18 rows | 18 = 15 grid + B0 + B1* + B1-HCA0; no unexpected rows; no un-counted fits | PASS |
| 15 | grid constants in code == dispatch | no tampering | PHI_GRID/arms/K/HCA/γ/μ/seed/10k/band/group columns all equal dispatch | PASS |
| 16 | honesty: twins-winning disclosed | disclosed as machinery/noise | report Diagnostics + ledger twin_wins:true + handoff limitations | PASS |
| 17 | honesty: B1* slope 0.7801 disclosed | disclosed | report + verdict table + arm reasons | PASS |
| 18 | determinism corroboration | ledger sha 0ede824f… | lane == data-dir copy == claim; VERDICT_TABLE 72b6a4e8… == claim | PASS |

## A7 VERDICT: **NEGATIVE_VERIFIED**

The clean negative stands: no PF arm carries a train-internal gain at any pre-registered φ;
each arm's best config is its φ=0 designed null (= B1*); the feature direction is uniformly
harmful (ΔLL > 0, CIs entirely > 0 at |φ| ≥ 25); machinery is disclosed and does not rescue
any config. No defect named.

**Frozen φ per arm: NONE — slot release confirmed by independent verification.**
