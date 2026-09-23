# PROPOSALS — cell BTC_H1 (lane L1, cycle PHASE-STRATEGY-V1)

At most ONE strategy per data-sufficient phase (plan §6), chosen by economic
mechanism before any dry-run counts were seen. Machine-readable twin with
arm digests: `proposals.json`; cost/turnover arithmetic: `feasibility/ceiling.json`.

> PIT disclosure and INCIDENT XCHECK-FAIL: see `census/CENSUS.md` — they
> apply verbatim to every proposal below.

## Phase slots

| phase | slot |
|---|---|
| ACCUMULATION | FROZEN: `PSV1-BTC_H1-ACC-FLOOR_PROVISION` |
| UPTREND | FROZEN: `PSV1-BTC_H1-UPTREND-BREAKOUT_CONT` |
| DISTRIBUTION | **NO_ELIGIBLE_PROPOSAL** (strict default) |
| DOWNTREND | FROZEN: `PSV1-BTC_H1-DOWNTREND-BREAKDOWN_CONT` |
| TRANSITION_UNKNOWN | **NOT_RUN_THIN_PHASE — slot FLAT** (3 episodes; margin −17) |

DISTRIBUTION strict default applies: post-advance tops are where late longs
get handed inventory; no explicit, evidenced forced-counterparty mechanism is
expressible from OHLCV-only observables (no positioning/borrow data), so the
phase defaults FLAT. Naked-shorting tops additionally carries negative-carry
risk into strength with no evidenced forced counterparty to pay for it.

## PSV1-BTC_H1-UPTREND-BREAKOUT_CONT (long only)

- **Mechanism** — BTC markup legs force two buyer classes into thin books:
  stopped-out shorts must cover and late momentum chasers must lift offers.
  Continuation after a fresh 20-day-high breakout is supplied by these
  forced flows; episodes are sparse (10.2 round trips/yr measured) and
  multi-day (median hold 4.6 d), so 12–24 bps cost loads are structurally
  small vs the episode anatomy.
- **Observable** — close vs prior 480-bar max of highs (Donchian-20d), gated
  by the cell's frozen UPTREND state; decision at close, fill next open.
- **Exits** — STOP: close < prior 240-bar min of lows (risk override, may
  fire pre-min-hold); gate-off: state leaves UPTREND after min-hold 24 bars;
  fold-end force-flat. Stop-window law: prior-bar windows only.
- **Sizing** — fraction 1.0; direction long only (BTC perp).
- **Churn law** — min-dwell 24 bars == phase-rule transition buffer;
  sub-buffer label noise produces zero fills (engine-structurally enforced;
  golden test). Switches = 68 vs 505 phase-label transitions (13.5%).
  unnecessary_close_reopen = 0 structurally.
- **Turnover/costs** — 68 entries over 6.65 y; per-fold 16/13/22/17; median
  hold 110 bars. Cost load incl. adverse funding allowance: 13.9 / 20.8 /
  27.8 bps at 1.0x/1.5x/2.0x. Argued gross edge ≥ 200 bps/episode (stated
  assumption: an episode failing to move +2% over multi-day dwell would not
  satisfy ADX≥22 persistence + fresh-20d-high anatomy) → margins ≥ 14.4x /
  9.6x / 7.2x → ceiling PASS at all tiers.
- **Control (frozen now)** — phase-shuffled matched control: episode-block
  permutation within fold, seed 20260923, 100 draws, identical rule under
  shuffled gate; VALID only if entry-time 24h realized-move distribution
  matches the candidate (KS ≤ 0.15, checked in the scored run); control
  out-earning ⇒ kill (G6).
- **Failure interpretation (preregistered)** — continuation already
  arbitraged (mechanism-dead) or cost-eaten at 1.5x; single-fold
  concentration in one expansion era is the secondary kill signature.
- **Ancestry** — NOT `UP_TREND_SLOW_LONG` (a continuously-held regime
  long): this is an event-conditional breakout book with a structure stop.
  Not a §7.2 dead class (no reversal/imbalance/illiquidity/OI/vol-shock/
  pair input). Measured |rho| ≤ 0.076 vs all reconstructible shadows.

## PSV1-BTC_H1-ACC-FLOOR_PROVISION (long only)

- **Mechanism** — at range floors after declines, forced sellers
  (margin-stressed longs, redemption flows, impatient holders) sell into
  thin books; patient inventory is acquired there and held through the
  range until markup. Entries are sparse deep-in-range events (7.8/yr);
  the book is designed to RIDE the ACC→UPTREND transition (hold gate
  {ACCUMULATION, UPTREND}), so the strategy monetizes the markup its
  accumulation precedes. Median hold 4.9 d, max 444 bars.
- **Observable** — close within the lower quartile of the trailing 720-bar
  (30d) close range while state == ACCUMULATION.
- **Exits** — state leaves {ACC, UP} after min-hold 24 bars; STOP: close
  below the 30d range low observed at the entry bar (new 30d low = structure
  break); fold-end force-flat. 52 entries; per-fold 5/15/16/16; switches
  10.3% of label transitions; unnecessary_close_reopen = 0.
- **Turnover/costs** — load 14.0 / 21.0 / 28.1 bps at 1.0x/1.5x/2.0x.
  Argued gross edge ≥ 500 bps/episode (stated assumption: the mechanism's
  minimum DEFINED capture is the range-floor→midpoint span, ≥25% of a 30d
  range height; a sub-5% BTC 30d range is extraordinarily dead) → margins
  ≥ 35.6x / 23.8x / 17.8x → ceiling PASS at all tiers.
- **Control (frozen now)** — clock-only control: identical structure entry
  WITHOUT the phase gate, thinned deterministically (keep every k-th event)
  to the candidate's entry count (k frozen from the candidate dry-run
  count), exits on a frozen 720-bar clock instead of the hold gate; control
  out-earning ⇒ kill (G6).
- **Failure interpretation (preregistered)** — ranges resolve DOWN more
  often than UP in contraction eras (falling-knife capture), or floor
  provision is low-volatility beta that the frozen baselines beat.
- **Ancestry** — NOT `ACC_RANGE_MR` (two-sided excursion-fading, mean-target
  exits, high trade count): this is one-sided liquidity provision with a
  structure stop and markup-ride exit. NOT `ACC_FLAT_BREAKOUT_WAIT` (no
  breakout entries in ACC). Measured |rho| ≤ 0.066 vs all shadows.

## PSV1-BTC_H1-DOWNTREND-BREAKDOWN_CONT (short only)

- **Mechanism** — deleveraging cascades are persistent: margin calls, stop
  cascades and redemption flows beget forced selling, while unlevered
  holders exit late and market makers reprice thin books slowly. Breakdown
  continuation after a fresh 20-day-low break monetizes that persistence;
  funding in contraction typically rebates shorts. Sparse (7.1/yr), median
  hold 4.9 d.
- **Observable** — close vs prior 480-bar min of lows, gated by frozen
  DOWNTREND state; decision at close, fill next open.
- **Exits** — STOP: close > prior 240-bar max of highs; gate-off after
  min-hold; fold-end force-flat. 47 entries; per-fold 4/16/14/13; switches
  9.3% of label transitions; unnecessary_close_reopen = 0.
- **Turnover/costs** — load 14.0 / 21.0 / 28.1 bps. Argued gross edge ≥
  200 bps/episode (mirror of the UPTREND anatomy assumption) → margins
  ≥ 14.3x / 9.5x / 7.1x → ceiling PASS at all tiers.
- **Control (frozen now)** — phase-shuffled matched control, identical
  semantics to the UPTREND candidate (seed 20260923, 100 draws, KS ≤ 0.15
  movement validation).
- **Failure interpretation (preregistered)** — breakdown entries cluster at
  local lows that mean-revert (stop churn), or the effect is
  indistinguishable from simple stress-avoidance baselines.
- **Ancestry** — NOT `DOWN_SHORT_BTC` (a continuously-held regime short):
  event-conditional breakdown entry with structure stop. Not a rev-style
  reversal: entries require a NEW 20d low under ADX≥22 structure, not a
  fade. Measured |rho| ≤ 0.082 vs all shadows.

## Common contract (all three)

Execution: decision at bar close, fill at NEXT bar open, no mid-bar fills.
Sizing fraction 1.0 (V2 accounting). No age-based staleness/force-flat law
exists (the plan §10 defect class is absent; the only forced flat is the
fold boundary). Identity: `family_id PSV1-<CELL>-<PHASE>-<MECH>` +
`arm_config_digest` in `proposals.json`; data manifest digest in
`data/manifest.json`; code freeze = this commit.

## Honest disclosures carried by every proposal

1. INCIDENT XCHECK-FAIL — the 15m-catalog identity assurance FAILED
   (forensics in `data/manifest.json`); scored data is the Vision series,
   integrity PASS; A1 adjudicates.
2. ACC and DOWN proposals have thin first-fold entry counts (5 and 4
   entries in F1) — the phase FLOORS pass on episode/decision counts, but
   fold-level trade robustness (G4) is at risk in the scored run; disclosed.
3. Per-episode edge assumptions (200/500/200 bps) are stated, mechanism-
   grounded assumptions frozen pre-scoring — the scored run adjudicates
   them; they are NOT measured returns.
4. All dry-run numbers are counts/durations only; no PnL exists in this lane.
