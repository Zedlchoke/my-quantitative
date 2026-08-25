# V7 catalog novelty check — H-XSECT-FUNDING-PRICE-DIVERGENCE-v1

Author: A6 (hypothesis owner). Drafted at H00–H00:30 of PLAN §4, blind to all
results. Frozen with the V7 spec per PLAN §16.1 ("A catalog novelty check must
be frozen with the V7 spec; a material duplicate blocks V7") and gate V7-A03.

Question under test: is the cross-sectional score

    percentile_rank(price_return) - percentile_rank(funding)

(long top-2 score / short bottom-2 score on the S0-seven universe) materially
distinct from every existing catalog specification?

Catalog scanned: `ls research/hypotheses/` → H-XSECT-MOM-v1,
H-XSECT-REVERSAL-v1, H-VOLCOMP-BRKOUT-v1, H-FUNDCROWD-MR-v1, H-FUNDCROWD-MR-v2
(candidate/status/hypothesis files skimmed), plus the same-sprint V6 sibling
H-XSECT-FUNDING-CARRY-v1 for completeness.

## Per-entry comparison

| Catalog entry | State | Signal construction | Verdict vs V7 divergence score | One-line justification |
|---|---|---|---|---|
| H-XSECT-MOM-v1 | SPEC_LOCKED (scored family) | `cumulative_log_return_rank`, lookbacks 3/7/14d, long top-2 / short bottom-2 | **DISTINCT** | Price-only rank with no funding leg; V7 requires the funding term to offset price rank, so it can short strong-but-crowded names MOM would long. |
| H-XSECT-REVERSAL-v1 | IDEA / DRAFT-ONLY, zero trials, DATA_INCOMPLETE | Sketch: trailing 7d return rank, long losers / short winners quintiles, weekly | **DISTINCT** | Sign-flipped price-only rank with no funding term; V7's long side buys relative strength (opposite sign) and its shorts are conditioned on rich carry, not raw weakness. |
| H-VOLCOMP-BRKOUT-v1 | REJECTED | Single-symbol long-only squeeze→Donchian breakout + volume burst on 15m bars | **DISTINCT** | No cross-sectional ranking at all; entry-timing pattern on one symbol vs V7's daily two-leg market-neutral cross-sectional spread. |
| H-FUNDCROWD-MR-v1 | SPEC_DRAFT, superseded, never scored | Funding-rate percentile used as a SKIP-gate on frozen reclaim-MR entries (15m bars) | **DISTINCT** | Funding enters as a binary entry filter on an unrelated MR base signal, never as a cross-sectional spread term; no price-return rank anywhere in the gate. |
| H-FUNDCROWD-MR-v2 | REJECTED (scored) | Same gate structure: `percentile_asof(decision_ts, 30d)` blocks crowded-side entries on reclaim-MR base | **DISTINCT** | Identical objection: funding percentile gates individual entries rather than ranking symbols against each other; V7 constructs a portfolio from the signed difference of TWO cross-sectional percentile ranks. |
| H-XSECT-FUNDING-CARRY-v1 (V6 sibling, this sprint) | SPEC_DRAFT, zero trials | Rank by trailing mean funding alone; long bottom-2 / short top-2 | **DISTINCT** | Carry-only ordering with no price leg; V7's exact research question (§16.1) is whether ADDING the price-confirmation term improves on this baseline — same universe/mechanics, materially different score and falsifiable claim. |

## Duplicate-risk analysis

The nearest neighbors are H-XSECT-MOM-v1 (shares price-rank mechanics) and
H-XSECT-FUNDING-CARRY-v1 (shares funding-rank mechanics). V7 is not a rerun or
rename of either:

1. vs MOM: the funding term can flip signs relative to a pure price rank
   (e.g., longs require LOW funding percentile while momentum longs buy HIGH
   return percentile only when it coincides with cheap carry); the negative
   control and FG3-V7 both-leg requirements make the difference measurable.
2. vs CARRY: the price term can flip signs relative to pure carry (longs need
   relative STRENGTH, not just cheapness); §17.2 explicitly decomposes price
   vs funding PnL and marks one-leg dominance as mechanism-inconclusive.
3. vs FUNDCROWD: gate-vs-spread is a categorical construction difference, and
   the base strategy (reclaim-MR, 15m) is absent from V7.
4. Shared scaffolding (universe, clocks, folds, risk caps, budgets) is common
   protocol per PLAN §8/§16, not signal duplication.

## Final verdict

```text
NOVEL_MATERIAL_DISTINCT
```

No catalog entry is a material duplicate; V7 is not blocked. This memo must be
hashed together with `candidate.yaml` before the first V6 scored launch
(gate V7-A03) and must show no post-V6-result diff (gate V7-A04).
