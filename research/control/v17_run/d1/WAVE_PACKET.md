# CRYPTO-V17 D1 WAVE PACKET (frozen at the wave SHA)

You are a BLIND proposal lane. You receive this packet and NOTHING about any
outcome. You never see scored results, PnL, gate verdicts, or other lanes'
proposals. You write exactly TWO proposals and a signed outcome-blind
attestation, then one clean commit on your lane branch.

## 1. Mission (your axis)

- Lane A4 (axis 1, MANDATORY): intraday reaction structure — H1/H4-class
  displacement / imbalance / reaction books that are NEW mechanisms on
  BTCUSDT+ETHUSDT from the published UTC-H1 panel. V16's dead forms
  re-clocked to H1/H4 are RESCUE and are vetoed by definition.
- Lane A5 (axis 2): universe extension — NEW daily-or-slower mechanisms on the
  3-symbol panel (BTCUSDT+ETHUSDT+SOLUSDT; SOL is a structurally different
  high-beta attention alt). V16-dead forms on SOL remain vetoed.
- Lane A6 (axis 3, open): any literature-backed mechanism on the authorized
  keyless Binance data in the non-forbidden space, any sanctioned clock.

Exactly TWO proposals per lane. Exactly three arms per proposal: anchor,
neighbour (same mechanism, different frozen parameters), control (placebo or
causal — the CONVENIENT EXPLANATION that must NOT reproduce the anchor).

## 2. Data contract (the ONLY data you may design against)

Published UTC-H1 panel, sha-pinned in `research/control/v17_run/staging/panel_manifest_v17_published.json`
(manifest sha256 761190a52e6504a74e12748efdb232dba03b40fa3065d35820b025283122e08b
— verify). Window S0 2025-08-22..2026-08-21 (365 days; 2025-08-22 row-filtered).
Per symbol, 8,760 hourly rows (BTCUSDT, ETHUSDT, SOLUSDT), columns:

    symbol, hour_utc, day_utc, n_trades, buy_count, sell_count,
    buy_qty, sell_qty, buy_quote, sell_quote, quote_total, qty_total, vwap,
    first_price, last_price, high_price, low_price, max_trade_quote,
    sum_qty_squared, n_price_moves, sum_squared_log_ret, gap_sum_s, gap_count,
    entry_gap_s, run_close_dir, run_close_len, run_switch_count,
    max_run_buy, max_run_sell, first_ts_ms, last_ts_ms

Daily aggregates derivable from H1 rows reconcile EXACTLY against the V16
sha-pinned daily panel (P0 mandatory self-audit RECONCILE_PASS). Any
observable you use MUST be computable from these columns (post-extraction
derivations allowed: H4 buckets, day aggregates, session flags, rolling
ratios). NO new data source without an owner plan; lane 3 may additionally
use keyless Binance klines/funding/premium endpoints already authorized in
prior crypto cycles (data.binance.vision + fapi public), same license law.

## 3. Frozen invariants (binding; from p3_invariants_v17.json)

- Rule order #1: after-cost expectancy first; gates in frozen order:
  G1 expectancy>0; G2 PF>=1.10; G3 folds>=2/3; G4 largest-fold-positive-share<=0.50;
  G5 MDD<=0.20; G10 neighbour supports; G11 control does not reproduce
  (reproduced = same sign AND |control exp| >= 0.5x|anchor exp| — if it
  reproduces, the family DIES, falsification-by-control cluster);
  G12 novelty pooled |rho|<=0.20.
- Costs: taker charged EXACTLY ONCE PER FILL (schedule: fee 5.0 bps baseline,
  tier multipliers x1.0/x1.5/x2.0 with slip floors 1/1/2 ticks; TIER 2.0 IS
  THE PRIMARY BOOK). Stress multipliers apply to BOOKED PnL.
- Folds: 3 chronological folds over S0 with the 1-day-purge contract
  (+/-1 full UTC day around each internal fold boundary).
- Budget: max 6 cells per cycle; unused slots never reassigned.
- S1 SEALED_UNTOUCHED — your designs never touch any S1 window.

## 4. Forbidden ancestry (measured veto at D2: pooled |rho| > 0.20 vs ANY of
these, measured on CONDITIONING EXPOSURES — not argued)

All prior crypto families and measured shadows, INCLUDING at any clock or
universe: funding carry (1/3/7d) + reverse; funding/price divergence;
cross-sectional reversal; time-series momentum; dollar-volume shock;
aggressor absorption (M01); residual-MAX lottery (LOT); Amihud ILLIQ;
OI-leverage quintiles; OILEV-V2 + inverted-OI shadow; betting-against-beta;
OI term-structure (OITD); liquidity episodicity (LIQEPIS); basis/premium
fade (PREMFADE); OI-cycle (OICYC, confirmatory-closed); elite-size asymmetry
fade; taker-saturation fade; elite-LEVEL shadow; day-boundary close-vs-VWAP
DISPLACEMENT FADE (V16 CLOSE-DISPLACE-FADE — dead at ANY clock);
same-side run PERSISTENCE (V16 RUNPERSIST — dead at ANY clock); run-imbalance
corroborating shadow; plus the pre-factory sprint forms (funding-crowding MR,
vol-compression breakout, cross-sectional momentum, frozen-rule mean-reversion
transfer, Wyckoff markdown-breakdown, 24h sprint matrix). Re-labels by
timeframe, threshold, symbol set, fee, sign-flip or session-subset are rescue.
A mechanism is NEW only if information source AND causal story AND control
class are new.

## 5. Proposal template (both proposals, JSON, exact fields)

    hypothesis_id        "V17-{LANE}-P{1|2}-{SHORTNAME}"
    lane                 "a4" | "a5" | "a6"
    mechanism_name
    mechanism_story      who is forced to buy/sell or slow to react; WHY the
                         effect exists; the observable that measures it; WHEN
                         it must fail (the market condition that kills it)
    universe             symbols used
    clock                decision clock (H1 / H4 / daily-or-slower)
    warmup               lookback actually consumed, in decisions
    features_and_lags    every input column (section 2 names) + lag spec;
                         availability law: decision at bucket t may use rows
                         with close_ts <= t (NO same-bucket close peeking
                         unless the fill is explicitly next-bucket-open)
    entry_exit_fills     entry rule, exit/holding rule, force-flat at fold
                         edges; fill timing (next-bucket VWAP/close default)
    costs                state the once-per-fill acknowledgment + tier 2.0 primary
    anchor               exact book definition
    neighbour            same mechanism, different frozen parameters
    control              placebo/causal class fitting the mechanism:
                         session-conditioned -> randomized session-boundary
                         sham; characteristic book -> exposure-form control
                         (characteristic replaced by its raw level);
                         arrival-structure -> reshuffled-interval placebo
    exposure_series_spec how D2 measures your conditioning exposure series
                         from the panel (exact formula) - REQUIRED
    falsification_rule   the pre-registered condition that kills the family
                         (control reproduces; anchor negative; etc.)
    expected_failure_interpretation  what a REJECT means for the mechanism
    expected_failure_mode            MUST be cost domination (named risk of
                                     this frontier), with your turnover
                                     estimate per decision

## 6. Deliverables (your lane dir ONLY: research/control/v17_run/d1/{lane}/)

    proposal_P1.json, proposal_P2.json,
    attestation.json {"lane": ..., "wave_sha": "<wave sha>",
                      "outcome_blind": true, "no_scored_artifacts_seen": true,
                      "proposals": ["proposal_P1.json","proposal_P2.json"],
                      "attested_by": "A{4|5|6} blind lane", "utc": ...}

Then ONE clean commit on your lane branch (git add by exact path only) and a
handoff message listing changed files + attestation sha256. Do NOT touch
anything else. Do NOT read results/, ledgers, terminals, or other lanes' dirs.
