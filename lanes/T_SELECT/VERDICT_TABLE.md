# VERDICT TABLE — NBA-PLAYERFEAT-SCORED-V1 · TRAIN-INTERNAL SELECTION

Sign convention: ΔLL = LL(arm) − LL(B1*); Δ < 0 favors the arm. CI: tip-date-clustered bootstrap 95%, 10,000 resamples, seed 20261005. Slope band [0.85, 1.15].

| # | arm / config | φ | pooled LL (folds 2018–21) | ΔLL vs B1* [95% CI] | slope | twin | verdict |
|---|---|---|---|---|---|---|---|
| 1 | B0 (per-fold refit) | — | see ledger | see ledger | n/a (constant p) | — | REFERENCE_FLOOR |
| 2 | B1* (K=32 HCA=100 γ=0.75) | — | 0.638327 | 0 [0, 0] | 0.7801 | — | REFERENCE_BASELINE |
| 3 | PF-A `PF-A|phi=-50` | -50 | 0.659481 | +0.021155 [+0.014419, +0.027971] | 0.6031 | — | GRID_EVALUATED |
| 4 | PF-A `PF-A|phi=-25` | -25 | 0.643365 | +0.005038 [+0.001710, +0.008375] | 0.7243 | — | GRID_EVALUATED |
| 5 | PF-A `PF-A|phi=0` | 0 | 0.638327 | +0.000000 [+0.000000, +0.000000] | 0.7801 | 0.638327 (clean) | DESIGNED_NULL_OK |
| 6 | PF-A `PF-A|phi=25` | 25 | 0.644783 | +0.006456 [+0.003114, +0.009766] | 0.7302 | — | GRID_EVALUATED |
| 7 | PF-A `PF-A|phi=50` | 50 | 0.662523 | +0.024197 [+0.017473, +0.030917] | 0.6050 | — | GRID_EVALUATED |
| 8 | PF-B `PF-B|phi=-50` | -50 | 0.655316 | +0.016989 [+0.011249, +0.022679] | 0.6500 | — | GRID_EVALUATED |
| 9 | PF-B `PF-B|phi=-25` | -25 | 0.642612 | +0.004286 [+0.001423, +0.007103] | 0.7476 | — | GRID_EVALUATED |
| 10 | PF-B `PF-B|phi=0` | 0 | 0.638327 | +0.000000 [+0.000000, +0.000000] | 0.7801 | 0.638327 (clean) | DESIGNED_NULL_OK |
| 11 | PF-B `PF-B|phi=25` | 25 | 0.642574 | +0.004247 [+0.001480, +0.007118] | 0.7331 | — | GRID_EVALUATED |
| 12 | PF-B `PF-B|phi=50` | 50 | 0.655107 | +0.016781 [+0.011183, +0.022539] | 0.6336 | — | GRID_EVALUATED |
| 13 | PF-C `PF-C|phi=-50` | -50 | 0.659247 | +0.020920 [+0.013877, +0.028283] | 0.5934 | — | GRID_EVALUATED |
| 14 | PF-C `PF-C|phi=-25` | -25 | 0.643030 | +0.004704 [+0.001262, +0.008302] | 0.7156 | — | GRID_EVALUATED |
| 15 | PF-C `PF-C|phi=0` | 0 | 0.638327 | +0.000000 [+0.000000, +0.000000] | 0.7801 | 0.638327 (clean) | DESIGNED_NULL_OK |
| 16 | PF-C `PF-C|phi=25` | 25 | 0.648295 | +0.009969 [+0.006028, +0.013881] | 0.7136 | — | GRID_EVALUATED |
| 17 | PF-C `PF-C|phi=50` | 50 | 0.671904 | +0.033578 [+0.025107, +0.042222] | 0.5590 | — | GRID_EVALUATED |
| 18 | B1-HCA0 (diagnostic) | — | 0.642816 | ΔLL(B1*,B1-HCA0)=+0.004490 [-0.003291, +0.012047] | — | — | DIAGNOSTIC_ABLATION |

**Frozen φ per ADMITTED arm:** NONE — no arm admitted
