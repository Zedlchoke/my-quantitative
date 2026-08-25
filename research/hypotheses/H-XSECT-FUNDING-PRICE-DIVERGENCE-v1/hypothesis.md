# H-XSECT-FUNDING-PRICE-DIVERGENCE-v1 — V7 hypothesis specification (A6 blind draft)

State: SPEC_DRAFT — PENDING_V6P_AUTHORIZATION
Owner: A6 (hypothesis owner)
Drafted at: H00–H00:30 block of PLAN §4 (V6P), BEFORE any V6 or V6P result
exists. Machine contract: `candidate.yaml` (verbatim PLAN §16.2). Status
sidecar: `status.yaml`. Per PLAN §17.1 gate V7-A03, this spec and its novelty
check (`research/audits/v6p/v7_catalog_novelty_check.md`) are hashed BEFORE the
first V6 scored launch; authorization to run comes only via the twelve §17.1
gates.

## 1. Mechanism

V6 carry alone buys cheap-funding names and sells expensive-funding names. V7
asks a different, narrower question (PLAN §16.1): does that market-neutral
portfolio improve when funding cheapness must be CONFIRMED by relative price
behavior — longs only where low funding coincides with relative price strength,
shorts only where high funding coincides with relative price weakness?

Construction: at each daily_00_00_utc signal, compute for each of the seven
traded symbols a cross-sectional divergence score

    percentile_rank(price_return) - percentile_rank(funding)

where `price_return` is the trailing close-to-close return on completed bars
only (declared price lookback; the single candidate dimension is
{1D, 3D, 7D}) and `funding` is the trailing mean of published settled funding
(fixed 3D lookback). LONG top-2 score / SHORT bottom-2 score, rebalance 24h,
chronological 3-fold with 24h purge/embargo, same risk caps as V6.

Economic intuition: assets where price strength coexists with cheap funding are
the least crowded strong names (longs not yet paying to be long); assets where
weakness coexists with rich funding are crowded weak names (paying shorts to
stay short into deterioration). The score demands BOTH legs agree before
exposure.

## 2. Economic prior vs edge claim

**This is an economic prior, not an established edge** (PLAN §16.1). It can
fail because carry and price continuation may not coexist, trading costs may
dominate, or the signal may collapse into repackaged momentum or repackaged
carry. Per §17.2, a result dominated by only one leg (pure momentum or pure
carry) is recorded as mechanism-inconclusive, never relabeled as a new edge.
No confirmed-edge claim may follow from drafting or locking.

## 3. Frozen pre-registration contract (summary)

Machine contract `candidate.yaml`, field-for-field PLAN §16.2:

- Family `cross_sectional_funding_price_divergence`, stage S0_EXPLORATORY.
- Same universe/benchmark/clock/folds/purge/risk caps/trial budget as V6.
- Funding feature fixed at 3D trailing mean of published settled funding;
  price feature {1D, 3D, 7D} = exactly three directional candidates plus one
  negative control (`reverse_score_sides_at_price_lookback_3d`) = four
  launches, no fifth (PLAN §16.3).
- Score/leg rules: long top_2_score, short bottom_2_score; rebalance 24h.
- `TO_FREEZE_AT_AUTHORIZATION` placeholders in `candidate.yaml` mirror the V6
  freeze list (PLAN §16.2 requires the same data, accounting, execution,
  latency, terminal, risk, metric, fold, DSR, cost, and artifact contracts).

The ONLY candidate dimension is the declared price lookback. No OI,
volatility, regime, liquidity, trend, symbol-specific, or threshold filter may
be added (PLAN §16.2).

## 4. Mechanism invalidation conditions (from PLAN §17.2 FG3-V7, summarized)

FG0/FG1/FG2/FG4–FG7 reuse V6 without relaxation; FG3 is replaced by FG3-V7.
Reject/mechanism-fail if ANY of:

1. After-cost total PnL <= 0.
2. Position PF < 1.10.
3. Net funding cashflow <= 0 OR future price PnL <= 0 (both legs must pay).
4. Fewer than 2/3 folds positive on total PnL.
5. Fewer than 2/3 folds positive on funding contribution.
6. Median continuous-capital fold return <= 0.
7. Fewer than 90 scored daily rebalances or 100 closed/terminal legs.
8. Top fold > 50% or top symbol > 40% of positive PnL.
9. No two adjacent price lookbacks positive.
10. Reverse control beats the best directional candidate.
11. Any required stress loses positive total PnL, positive funding, risk
   limits, or valid accounting.
12. Result dominated by only price momentum or only funding carry =>
   mechanism-INCONCLUSIVE (never PASS).
13. Any inherited V6 FG hard-gate failure (data/PIT/accounting/integrity/
   reproduction/audit) blocks V7 entirely per §17.1.

## 5. Forbidden post-lock changes

After A1 hashes/locks this spec (pre-V6-launch hash per V7-A03):

- Any frozen parameter value (universe, funding lookback fixed at 3D, the
  declared price lookback set, leg rules, rebalance, folds, purge/embargo,
  risk caps, trial budget, negative control).
- Adding OI, volatility, regime, liquidity, trend, symbol-specific, or
  threshold filters in v1.
- Any post-V6-result spec diff (gate V7-A04 fails on diff); verdicts and
  metadata go to `status.yaml` only.
- Window or universe changes after results; silent skip/replacement.
- Relabeling a mechanism-inconclusive or duplicate outcome as a new edge.
