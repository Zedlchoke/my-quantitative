# VERDICT TABLE — lane T_SELECT · WNBA-PLAYERFEAT-SCORED-V1 (TRAIN-INTERNAL)

| slot | arm | frozen config | verdict | basis |
|---|---|---|---|---|
| baseline | B0 constant | p_home=0.603755 | REFERENCE | train-window rate, frozen |
| baseline | B1-WNBA fresh own-Elo | K=32, HCA=50, γ=0.65 (warm-up 1997–2001) | FROZEN (kill test passed) | ΔLL vs B0 -0.054386 [-0.070150,-0.038275]; slope 0.9530 |
| feature | WF-A | none (no free scalar) | MACHINERY_SUSPECT | ΔLL +0.000420 [-0.002750,0.003621]; slope 0.9845; twin -0.000968 |
| feature | WF-B | φ=+0 | RELEASE | ΔLL +0.000000 [0.000000,0.000000]; slope 0.9047; twin +0.000000 |
| feature | WF-C | φ=+0 | RELEASE | ΔLL +0.000000 [0.000000,0.000000]; slope 0.9047; twin +0.000000 |

Verdict vocabulary: FROZEN = selected + train-internal kill test passed; ADMIT = G-ENTRY passed (point<0, slope in [0.85,1.15], twin clean) — pending post-GO OOS; INCONCLUSIVE = admitted but CI includes 0; RELEASE = slot released; KILL = falsified train-internally; MACHINERY_SUSPECT = twin beat its own parent (arm UN-SCORED). No OOS season was read.

Notes. (1) WF-B/WF-C: every NONZERO φ in the immutable grid was worse than the designed null on the pooled folds, so the selection returned φ=0 ≡ parent exactly (ΔLL = +0.000000 by byte identity) — the honest statement is that neither load/concentration nor form/absence adds train-internal signal at any pre-registered strength; slots RELEASED. (2) WF-A MACHINERY_SUSPECT: twin ΔLL -0.000968 vs own parent on the shuffled corpus, with the parent's real-data fold slope 0.9047 INSIDE [0.85,1.15] — the adjudication refinement's miscalibrated-parent exemption does NOT apply; arm UN-SCORED, machinery audit owed before any re-proposal. (3) Parent reference: B1-WNBA fold slope 0.9047; effects < ~0.003 ΔLL are INCONCLUSIVE at this capacity.

