# FX2-A5-P1 — PIT rate-differential carry with explicit financing/cost accounting

Lane: A5 (cost / rollover / accounting perspective) — F2 outcome-blind proposal.
Status: scientific hypothesis. No returns, no PnL, no backtest were computed for
this proposal and no other lane's output or scored ledger was read.

## Mechanism in one paragraph

Uncovered interest parity fails: high-yield currencies do not depreciate by the
full interest differential (Fama 1984). A dollar-neutral basket long the top
yielders and short the bottom yielders against USD therefore earns an average
excess return that the literature reads as compensation for crash risk
(Lustig-Roussanov-Verdelhan 2011; Brunnermeier-Nagel-Pedersen 2008). For this
lane the essential point is that the *financing economics are the mechanism*:
the surplus is rate accrual minus the dealer's rollover/swap wedge (long/short
asymmetry, Wednesday triple-roll) minus spread and commission. The proposal is
viable only if accrual clears that total drag; cost drag is an economic
variable, not an afterthought.

## Contract fields (narrative mirror of proposal_1.json — JSON is authoritative)

- **Economic mechanism**: UIP deviation / forward-premium puzzle; tradeable
  object is spot's persistent failure to move by the differential, paid as a
  risk premium; net surplus = (r_i − r_USD)·dt + E[spot] − swap wedge −
  spread − commission.
- **Expected counterparty**: leveraged carry investors unwinding in risk-off
  (we sell them crash insurance), corporate/real-money hedgers persistently
  selling high-yield forward, central-bank flow at rate-cycle extremes.
- **Signal fields and publication clock**: PIT 3M interbank/term rates for the
  8 currencies with fix timestamps and vintage history; signal = PIT
  differential; usable only one common trading hour after both legs' fix is
  stamped; vol estimate strictly pre-formation. PIT rates are UNAVAILABLE in
  the repo — stated plainly; family is feasibility-blocked without them.
- **Formation / holding / rebalance**: weekly formation at first common
  trading hour; hold one week; weekly re-rank with hysteresis band; 8% vol
  target from pre-formation EWMA vol; close at executable bid/ask.
- **Pair universe and neutralization**: the seven frozen USD pairs;
  dollar-neutral top-half vs bottom-half sleeves in equal-risk weights;
  residual currency exposure capped and reported by underlying currency.
- **Expected spread / rollover / turnover**: ≤ 12 pair-sides per week;
  spread measured per pair/session from real bid/ask (no global pip); rollover
  is the dominant financing term with triple-roll Wednesday modeled explicitly;
  anchor scored only net of everything against the A5 canonical USD identity.
- **Anchor / neighbour / negative control**:
  - *Anchor*: 3M PIT differential HML-FX, net of full costs.
  - *Neighbour*: same construction on 1M PIT differential — same theoretical
    premium, different financing tenor; validates if rank-correlated and
    same-signed; divergence forces a term-structure explanation.
  - *Causal negative controls*: (a) sign-flip at every formation — must
    destroy (reverse) net performance if the premium is the UIP deviation;
    (b) fixed-seed rank-scramble of differentials across currencies — severs
    the currency-rate causal link while preserving turnover and cost profile;
    must return ≈ 0 net of costs.
- **Expected regimes and falsification**: positive drift risk-on; violent
  negative-skew crashes in risk-off; dead in compressed-differential regimes.
  Falsified if anchor ≤ 0 net of costs, if either control fails, if PnL is
  sensitive to non-PIT rates, or if performance survives only under midpoint /
  constant-spread scoring.
- **Macro/session external-validity risks**: LIBOR→term-rate benchmark
  transition splits the sample; silent backfill of rates is a look-ahead
  channel; crash clustering makes Sharpe unstable; holiday/DST timing of the
  weekly formation; rollover boundary moves with DST; zero-rate regimes
  compress differentials; one dealer feed is not the global market.
- **Exact trial count**: 4 (anchor, neighbour, sign-flip control, scramble
  control). No post-score replacement, addition or re-windowing.
- **Required PIT fields and availability** (graded against measured repo facts):
  bid/ask 1h history — UNAVAILABLE (0 of 7 pairs, fail-closed); PIT 3M/1M rate
  vintages — UNAVAILABLE (no source in repo); rollover/swap schedule authority —
  UNAVAILABLE; holiday tables — SYNTHETIC_TEST_ONLY; session/DST clocks —
  implemented (zoneinfo DST real; wall-time session labels SYNTHETIC_TEST_ONLY
  defaults); accounting/conversion contracts — implemented but inert without
  the data above.
- **Prohibited shortcut check**: none apply (no indicator grids; no volume
  used; carry never from today's rates applied historically — PIT source is
  required and honestly marked UNAVAILABLE; no session filter; no midpoint
  labeled executable).
- **Ancestry statement**: first-cycle proposal; not a rescue of any previously
  rejected family; no other lane read. Adjacent to crypto funding-premium
  families by analogy only — instrument, signal source, financing schedule,
  calendar and cost structure are FX-native and new to this repo.

## Feasibility statement

Feasibility-blocked at selection as things stand: PIT rate vintages, real
bid/ask history and a swap-schedule authority are all UNAVAILABLE. Proceeds
only if the owner explicitly authorizes those sources. This proposal never
claims or implies the data exists.
