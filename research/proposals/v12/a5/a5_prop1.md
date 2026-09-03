# A5 proposal 1 — V12-A5-P1-BAB-LOWBETA (leverage-constraint beta pricing)

Lane A5, outcome-blind. This narrative accompanies `a5_prop1.json`; the JSON is the
machine-checkable record. No returns, PnL, PF, Sharpe, ranking or backtest was computed in
this lane; all floor verification belongs to the schedule-only gate.

## Mechanism in one line

A weekly (Monday 00:00:00Z), beta-neutral long/short quintile book over the 19 non-BTC
Binance USD-M perpetuals: long the lowest trailing 90-day daily BTC-beta quintile, short the
highest, with the sign prediction that leverage-constrained demand for high-beta names
depresses their risk-adjusted returns (Frazzini & Pedersen 2014).

## Primary-source claim and crypto transfer

- S1 (Frazzini & Pedersen 2014, JFE 111(1), DOI 10.1016/j.jfineco.2013.10.005): constrained
  investors tilt toward high-beta assets, bidding down their risk-adjusted returns; the
  betting-against-beta factor earns positive risk-adjusted returns across asset classes.
- Crypto transfer: S4 (Seabe et al. 2024, Mathematics 12(9), DOI 10.3390/math12091351) shows
  BAB-type factor construction transplants to crypto factor investing; S5 (Pyo & Jang 2026,
  FRL, DOI 10.1016/j.frl.2026.109851) documents the low-risk anomaly persisting in the crypto
  cross-section. These are habitat claims, not imported magnitudes.
- Transfer caveats (full list in JSON): cheap perp leverage weakens the equity friction;
  BTC-vs-market benchmark distortion; stale-price lookalikes of low beta guarded by the
  coverage/data-quality eligibility gate; high-beta alt shorts often coincide with positive
  funding, so a carry-confound probe is a falsification condition, not an afterthought;
  published BAB premia are implementation-sensitive (Novy-Marx & Velikov 2018, working-paper
  caveat only), hence sign-and-identity falsification rather than magnitude pre-registration.

## Economic counterparty and expected sign

Leverage-constrained / convexity-seeking perpetual traders overweight high-beta alts;
mandate-constrained investors under-lever low-beta names. Anchor sign: long lowest-beta
quintile / short highest-beta quintile, beta-neutralized, positive expected unit-gross spread
vs the flat hard gate. The sign-flipped book is predicted NOT to earn it.

## PIT discipline

Feature: OLS beta of daily log returns vs BTCUSDT over the trailing 90-day daily block,
from completed 15m bars only (ts_event at-or-before the Monday 00:00Z stamp; the 90d warmup
is the data contract's declared binding horizon and its satisfiability is checkable from
pre-window history via `data_contract.warmup_report`). Execution: one declared lag — fill at
the first completed 15m bar strictly after the stamp (00:15Z close), strict-later
`FILLED_NEXT_EVENT`; stress adds +1 event delay. Funding settlements apply to a holding span
only when inside `[ts_opened, ts_closed]`. BTCUSDT is never a position.

## Schedule

19-name universe (20 minus BTC). Eligibility per stamp: covered 90d block, >= 60 valid paired
daily observations, >= 9 eligible names overall (else carry prior book forward). Formation:
beta quintiles. Holding: intended 28d with two-stamp hysteresis both directions and a 28d
per-symbol re-entry cooldown. Rebalance: weekly Mondays, terminal FORCE_FLAT at the frozen
boundary. 52 discretionary decisions/365d by construction (floor 60).

## Target book and risk neutralisation

Long/short quintile book. Equal within leg, leg gross 0.5 each: `w_i = ±min(0.30, 0.5/n_leg)`
so `max|w| <= 0.30` for every leg size >= 2 by construction; a single-member leg clips at
0.30; after the beta-neutral leg tilt the whole book is uniformly shrunk by
`min(1, 0.30/max|w|)`. Neutrality: long-leg gross scaled by the ratio of mean short-leg beta
to mean long-leg beta so the beta-weighted sum vs BTC is exactly zero. Median intended
holding 28d (floor 3d); turnover guards as specified; magnitudes deferred to the gate.

## Anchor, neighbour, causal control (3 scored cells — the family maximum)

- Anchor: 90d-beta quintile L/S, beta-neutral.
- Justified neighbour: betting-against-correlation — sort on trailing 90d downside
  correlation to BTC (BTC-down days), same skeleton. Justified by Asness, Frazzini, Gormsen &
  Pedersen 2020 (JFE 135(3), DOI 10.1016/j.jfineco.2019.07.003): the correlation channel is
  the low-risk effect's distinguishing component, so this is a theory-mandated alternative
  estimator of the same mechanism, not an anchor parameterization.
- Causal negative control: sign-flipped anchor (sign-destroying). If the flipped book earns
  the anchor's spread, beta pricing is not the driver and the family is falsified.

## Costs, funding, stress

Repo tier-0 taker fee floor + declared adverse-tick slippage using schema tick sizes
(1e-7..1e-2), all transitions through the adapter's frozen cost primitive; native funding
while held under `LONG_PAYS_POSITIVE_RATE` with PIT span applicability; frozen stress cells
(fee x1.5, +2 ticks, +1 event delay) plus the derived drop-one-symbol / drop-one-fold matrix.
No maker-rebate assumption; no fee reduction anywhere.

## Falsification

(1) Anchor fails the pre-registered gate vs the flat hard gate AND the sign-flipped control
passes; (2) anchor and sign-flip indistinguishable; (3) carry-confound probe — earnings
concentrate only where short legs coincide with positive funding; (4) momentum-confound
probe — beta ranks ≈ trailing-return ranks persistently, collapsing the mechanism into
V4-XSECT-MOM territory; the family is withdrawn rather than re-signed or re-windowed.

## Ancestry and why this is not a rescue

Mechanism-level mapping against `forbidden_family_inventory.json`: distinct from ordinary
momentum (second-moment signal, no return ranking), funding carry (no funding input; explicit
confound probe), LOT/MAX/skew (no return-distribution statistic; different counterparty),
Amihud/illiquidity (no impact statistic; prices only), OILEV (no OI input), aggressor
absorption (no signed flow), vol-compression breakout (no vol-regime timing), weekly reversal
(no past-return ranking; the sign-flip control exposes any hidden reversal content), and
DATA-GATED (schema-only inputs). Why not a rescue: the 90-day window is the data contract's
frozen warmup, not a retuned rejected lookback; fees are the declared floors; the full
eligible universe is binned mechanically (no winning-symbol selection); the 0.30 cap is
respected by construction with no post-score renormalisation; and no rejected baseline's
substance (past returns, funding, OI, volume shocks, signed flow) appears anywhere in the
formation.
