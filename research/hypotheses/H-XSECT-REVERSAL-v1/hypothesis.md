# H-XSECT-REVERSAL-v1 — Cross-sectional weekly rank reversal (DRAFT-ONLY)

**Family:** `cross_sectional_reversal` · **State:** `IDEA` · **Owner:** A4 ·
**Blocked on data:** `DATA_INCOMPLETE` · **No implementation.**

## Why drafted at all

PLAN §7 family priority 4 lists cross-sectional momentum/reversal. External
evidence cited in NOTES §15.1 (Zaremba et al. 2021; Wen et al. 2022) supports
liquidity-conditioned reversal among less liquid coins vs daily momentum in
large caps. It is recorded as an IDEA so the next iteration inherits a
pre-registered direction instead of re-deriving it.

## Hard blockers (why NO scored run and no code)

1. **Common intersection ~1y** (contracts/README.md H0 limitation). Weekly rank
   reversal needs longer common history: quintile ranks on 7 symbols are
   unstable, and fold counts would be too small for the ≥20-trade gate.
2. **Portfolio engine gap.** Cross-sectional baskets need shared-capital,
   multi-leg concurrent execution; the current matrix runner is per-symbol
   cells only.
3. Trial budget: 0 combinations declared; nothing is scored from this draft.

## Promotion criteria (for a future iteration)

- Common 15m intersection ≥ 2y across the universe, or weekly bars ≥ 2y.
- Portfolio replay support in the runner (G5-style shared capital).
- Pre-register `candidate_version` grid BEFORE any scored run; then implement.

## Explicit labels

Any result resembling this idea that appears incidentally elsewhere must stay
labeled **EXPLORATORY**; scan near-winners (NEAR reclaim, BOME pullback, ADA
markdown, SOL reclaim) are 4-of-58 survivors under multiple testing and are not
evidence of edge.
