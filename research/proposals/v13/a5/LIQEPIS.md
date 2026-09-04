# A13-V13-A5-LIQEPIS — Liquidity episodicity (volume-time concentration of supply)

Lane: a5 | Cycle: CRYPTO-V13 Phase D1 | Outcome-blind proposal (no computation performed)
Status: NEW mechanism, conditioning space = liquidity provision / depth-turnover structure
(mission Q2). Shadow-region posture: voluntarily front-door compliant (section 12 below);
confirmatory only if A1/A7-N classify it into the shadow region.

## 1. Hypothesis ID and mechanism

Hypothesis ID: `A13-V13-A5-LIQEPIS`

Resting liquidity in a perpetual market is the standing capacity to transfer risk from
positional traders to short-horizon participants. That capacity has a temporal SHAPE: in some
names trading flow is smooth (spread evenly across the 24/7 grid); in others it is episodic
(concentrated in a small fraction of time, thin in between). The mechanism conditions on this
shape: episodicity `H_i(T) = sum_b (q_b / Q)^2`, the Herfindahl of 15-minute dollar-volume
shares over the trailing 28 days (2688 completed bars; q_b = close x volume; uniform baseline
1/2688).

Economic counterparty: the liquidity provider facing bursty flow, and the positional holder
whose risk-transfer needs do not coincide with the bursts. Admati & Pfleiderer (1988) show
trading clusters endogenously because discretionary liquidity traders bunch where depth is
thick, and that clustering patterns persist — the shape is a stable name-level characteristic,
not noise. Crypto-specific structure strengthens this: 24/7 trading with pronounced algorithmic
periodicity (quarter-hour cycles documented on Binance USDT-M perps; inverted-U intraday
volume/volatility patterns), so between-burst periods are genuinely thin rather than merely
off-session.

Why the edge exists: when supply is episodic, providers face bursty inventory and
adverse-selection risk and quote wider effective spreads around bursts, while standing depth
between bursts is thin. A weekly holder entering at a fixed clock (Monday 00:15Z fill) whose
exit need not coincide with the bursts systematically transacts against worse effective
liquidity, and burst-driven prints are more often information- than inventory-driven
(adverse-selection dominated). The market prices this fragility by attention (bursts attract
chasing flow) rather than by standing-liquidity quality, so names with smooth turnover are
systematically underpriced relative to the liquidity service they provide a holder.

Expected sign: cross-sectionally, LOW episodicity (smooth turnover; standing liquidity reliably
available) outperforms HIGH episodicity over the next week. The arm is long the bottom tercile
of H, short the top tercile. The signal contains NO return term, NO OI term, NO funding term,
NO shock threshold, and NO price-impact term.

## 2. Falsifiable prediction

Falsifiable prediction: after base costs, the LIQEPIS-28D anchor earns positive BTC-beta-
adjusted weekly excess in at least 2 of the 3 frozen chronological folds, its 56d neighbour
supports the same sign, and the sign-inverted control does NOT pass the same gate. The
hypothesis is FALSIFIED if any of: (a) the anchor's beta-context excess is not positive in
>= 2/3 folds; (b) the sign-inverted control (long HIGH episodicity) ALSO passes the incremental
gate — then the smooth-vs-episodic ordering carries no directional liquidity information and the
anchor's result is a generic tilt artifact; the anchor is rejected and the control is never
promotable; (c) the neighbour flips sign (shape is formation-window fragile, i.e. not the
persistent characteristic the Admati-Pfleiderer persistence argument requires); (d) the anchor
passes base but fails stress, meaning the measured effect is a spread/slippage execution
artifact rather than a liquidity-structure premium.

## 3. Literature (queries + retrieval UTC + accept/reject; transfer caveats)

Log (all retrieved 2026-09-04, UTC):

| # | Query | Retrieved (UTC) | Source | Verdict + reason |
|---|-------|-----------------|--------|------------------|
| L1 | Admati Pfleiderer theory of intraday patterns volume price variability liquidity trading | 11:15 | Admati & Pfleiderer 1988, Review of Financial Studies 1(1), 3-40 | ACCEPT (primary): endogenous, persistent concentration of discretionary liquidity trading; grounds both the persistence of the shape and the provider-facing mechanism. |
| L2 | trading volume concentration burstiness cross-section expected returns turnover Herfindahl | 11:16 | MDPI JRFM 17(8) 2024 Gini-based volume concentration across S&P 500 with concentration-driven portfolios; RePEc IJEFR 2021 volume concentration and returns | PARTIAL ACCEPT: direct precedent for concentration measures in cross-sectional return work; caveats — equity daily aggregation, journal tier, mixed evidence; used only as precedent that the variable is studied, not as sign evidence. |
| L3 | cryptocurrency perpetual futures intraday volume seasonality liquidity provision pattern empirical | 11:17 | Jasiak 2024, International Review of Economics and Finance (intraday/intraweek crypto volume-volatility patterns); Su et al. 2022 (inverted-U intraday volume/volatility/liquidity); arXiv 2607.09426 quarter-hour effect on Binance USDT-M perps | ACCEPT (primary for the crypto transfer): crypto volume has persistent temporal structure on exactly the venue and asset class studied; supports computing a 24/7 shape measure rather than an equity-session one. |
| L4 | Datar Naik Radcliffe liquidity stock returns alternative test turnover 1998 | 11:16 | Datar, Naik & Radcliffe 1998, Journal of Financial Markets 1(2), 203-219 | ACCEPT only as lineage contrast: DNR turnover = volume/shares outstanding is a LEVEL ratio (no price term) and is the reason turnover-family variables are distinct from Amihud price-impact ratios; NOT used as the anchor basis — this proposal's variable is a temporal DISPERSION SHAPE, not a turnover level, and the mechanism (standing-liquidity reliability) differs from the DNR liquidity premium. |
| L5 | perpetual futures liquidity provision market making funding rate intraday | 11:17 | arXiv 2605.06405 funding-aware optimal market making in perps | ACCEPT as mechanism context: perp liquidity provision is explicitly patterned and provider decisions are state-dependent; supports between-burst thinness being a real supply decision. No design element taken. |

Primary-source claims carried into the design: (i) volume-time concentration is endogenous and
persistent (L1); (ii) crypto/perp volume seasonality is strong and venue-specific (L3); (iii)
concentration-style variables have prior art in cross-sectional work (L2, precedent only).

Transfer caveats (equity/commodity -> Binance USD-M perps):
- Admati-Pfleiderer is an equity session theory; crypto trades 24/7 with quarter-hour
  algorithmic periodicity, so the 28d shape here aggregates across all hours including
  traditionally quiet ones — the measured shape mixes a periodic component and a burst
  component by design; the neighbour window (56d) tests persistence of the mixture.
- Herfindahl over 2688 bins is sensitive to venue downtime: any missing 15m slot refuses the
  stamp (fail-closed) so gaps can never masquerade as thinness; refusal counts are reported.
- Dollar-volume proxies (LAST close x base volume) conflate taker/maker and carry intra-bar
  drift noise, identical across arms.
- The prior equity concentration evidence is mixed and daily-aggregated; the a priori sign here
  is declared from the provider/holder mechanism, not from L2 — if the sign comes out opposite,
  the mechanism is falsified per section 2 (no post-hoc reinterpretation).
- Burstiness correlates with event-driven attention; part of the effect may be captured by
  volatility-level characteristics (forbidden LOT/MAX/skew family) — the ancestry defense is
  that H uses NO return moments whatsoever; only volume shares across time.

## 4. PIT observable (fusion-record availability semantics)

Decision instant T = Monday 00:00:00Z. A decision at T reads ONLY rows with
`available_time_utc <= T`; retrieval time never substitutes for availability
(research/data_fusion/crypto_compat.py; research/data_fusion/pit.py vintage selection).

- Bars: dataset `crypto_bars`, 15m completed bars, available at bar close (a bar is completed at
  instant t iff t >= its close boundary ts_event). At T the formation window is the trailing
  2688 (anchor) / 5376 (neighbour) completed-bar slots; EVERY slot must be present and
  available; one missing slot refuses the symbol at that stamp (fail-closed; no back-fill).
- q_b = bar close x bar volume; H = sum over bars of (q_b / Q)^2, Q = total.
- BTCUSDT bars: benchmark only (buy-and-hold + 90d beta context), never in the ranking.
- Funding: dataset `crypto_funding`; native cost on held legs only; never a signal.

## 5. Universe, warmup, clock, holding, execution

- Universe: the 20 staged REQUIRED_SYMBOLS minus BTCUSDT (benchmark only) = 19 tradable names.
  Eligibility at T: full completed-bar coverage of the formation window (fail-closed) plus the
  binding 90-day beta warmup.
- Warmup: binding maximum 90 days (beta context); anchor shape 28d; neighbour shape 56d — all
  from the frozen warmup table (28/56/90).
- Decision clock: weekly, every Monday 00:00:00Z (52 discretionary decisions/365d <= 60 floor).
- Holding: intended 7 days (median 7d >= 3d floor); force-flat at fold boundaries.
- Execution lag (ONE, declared): fills at the close of the first completed 15m bar strictly
  after T (Monday 00:15:00Z bar close), generic adapter costs on fills; stress adds +1 event
  delay (fill at Monday 00:30:00Z close).
- Book: long bottom tercile (lowest H), short top tercile (highest H), 6 symbols per side,
  equal weight 1/12 per held symbol, gross 1.0; max |weight| = 1/12 <= 0.30 by construction;
  ties broken by symbol id ascending (declared a priori); middle tercile flat.
- Folds: frozen V12 chronological F0/F1/F2 over the blind-S0 window 2025-08-22..2026-08-21 with
  1-day purge, imported unchanged.

## 6. Arms (exactly 3): anchor + neighbour + causal negative control

- ANCHOR — `LIQEPIS-28D`: H over trailing 2688 completed bars (28d); long bottom tercile /
  short top tercile as in section 5.
- NEIGHBOUR — `LIQEPIS-56D`: same mechanism and book, shape window 5376 bars (56d).
  Justification: the Admati-Pfleiderer persistence claim implies the shape is a slow
  characteristic; 56d tests that the mechanism does not depend on one month's flow realization;
  56d is in the frozen warmup table and is the pre-declared sibling of the 28d anchor.
- CAUSAL NEGATIVE CONTROL — `LIQEPIS-SIGN-INV`: identical construction and book with the sign
  inverted (long HIGH episodicity / short LOW). This is the factory-standard causal negative
  control (same pattern as the frozen OILEV-V2 inverted control): it separates the declared
  mechanism sign from a generic long/short tilt.
- Preregistered control rule: the control MUST NOT reproduce the anchor — if
  `LIQEPIS-SIGN-INV` passes the same incremental gate (BTC-beta-context excess positive in
  >= 2/3 folds), the episodic-liquidity mechanism is falsified (the ordering carries no
  directional liquidity information; any anchor result is a tilt/cost artifact), the anchor
  FAILS and the family is rejected. The control is never promotable to a family regardless of
  its own result.
- Beta/funding separation (all arms): identical universe, identical fills and identical native
  funding costs; funding is a cost, never a signal; the incremental gate is BTC-beta-adjusted;
  any anchor-minus-control difference is sign-direction liquidity information, not funding
  carry or beta.

## 7. Incremental test vs buy-and-hold and BTC-beta context

- Benchmark: BTCUSDT buy-and-hold over the same stamps (same clock, same fold boundaries).
- Beta context: weekly arm excess adjusted by beta from trailing 90d of completed daily bars
  (frozen convention).
- Binding gate (Stage-A, unrelaxed): anchor BTC-beta-context excess positive in >= 2/3 folds;
  raw excess vs buy-and-hold also positive in >= 2/3 folds for the family to advance; neighbour
  same sign; control must fail per section 6.

## 8. Costs, floors, concentration, drop-one

- Costs: frozen generic adapter fee/slippage schedule (base) and stress = fee x1.5, +2 adverse
  ticks, +1 event delay. Native funding on held legs, counted once, cost only. Feasibility
  (base drag <= 8%/yr of gross; stressed <= 12%/yr) is evaluated by A9-F from schedule
  artifacts only — no cost number is computed in this proposal.
- Floors: <= 60 discretionary decisions/365d (52 weekly); median intended holding 7d >= 3d;
  >= 52 weekly decisions per arm in the screen window; >= 15 per fold; zero-position arms
  refused at publication (inherited minimum-activity rule).
- Concentration: no symbol > 25% of turnover (equal tercile book; checked by A9-F); largest
  symbol positive-PnL share <= 0.70 gate inherited; max |weight| <= 0.30 at every stamp by
  construction (1/12).
- Drop-one design (non-vacuous): identify the fold-stamp with the largest held |weight|; drop
  the single symbol attaining that maximum among held positions (by construction a held
  max-|weight| symbol); renormalize to 5 symbols per side (1/10) and re-run. The family
  survives only if the anchor's fold-sign pattern and the control rule's outcome are unchanged;
  otherwise the edge is symbol-specific and the family is rejected.

## 9. Failure interpretation

- Anchor fails incremental gate in all folds: no after-cost edge; smooth-liquidity service is
  not rewarded at weekly horizon (or episodicity is priced away by attention flows); family
  rejected (no parameter search).
- Anchor positive but sign-inverted control also positive: no directional liquidity information
  in the ordering; anchor result is a tilt/cost artifact; family rejected; control never
  promotable.
- Anchor positive, neighbour negative or sign-flipped: shape is formation-window fragile — not
  the persistent characteristic the mechanism requires; family rejected.
- Anchor passes base but fails stress: measured effect is a spread/slippage execution artifact;
  family rejected.
- Fold-concentration failure (one fold carries > 50% of positives): regime-driven (e.g. one
  burst-dominated quarter); not a persistent mechanism; family rejected.
- Symbol-concentration failure (largest symbol > 0.70 of positive PnL): single-name artifact;
  family rejected.
- High refusal rate (formation windows with missing slots): BLOCKED_DATA verdict, not a
  mechanism rejection.

## 10. Source-to-test map

| Input field (dataset) | Exact test use |
|---|---|
| 15m bar close x volume (`crypto_bars`, avail = bar close) | q_b per bar; Herfindahl H over 2688 (anchor) / 5376 (neighbour) completed slots; tercile ranking; fail-closed gap refusal |
| Completed-bar coverage / gaps | warmup satisfiability (90d binding), formation-window completeness, fold boundaries |
| BTCUSDT 15m bars | weekly buy-and-hold benchmark; 90d beta context (benchmark only, never ranked) |
| Funding settlements (`crypto_funding`, avail = settlement stamp) | native cost on held legs in ALL arms identically; never in signals or gates |
| Instrument tick size (`crypto_perpetual` metadata) | +2-tick stress slippage unit |
| (explicitly NOT used) OI snapshots, mark price, funding rate | no OI, mark or funding field enters any signal — declared to bound the conditioning space |

## 11. Ancestry map vs the forbidden inventory

- V9 dollar-volume shock continuation: different variable and different claim. V9 conditioned on
  dollar-volume SHOCK LEVELS and claimed continuation (buy the spike). LIQEPIS uses the
  within-window temporal DISPERSION of volume shares (a shape, no threshold, no level), and its
  a priori sign is SHORT the concentrated side — declared before any outcome from the provider
  mechanism, not as an inversion of V9: no parameter rescue, no universe carve-out, no renaming.
- V1-VOLCOMP (volatility-compression breakout): no volatility conditioning, no breakout, no
  continuation; volume shape only.
- V11-ILLIQ-AMIHUD / V12-ILLIQ-REPLICATION: no |return|/volume price-impact term anywhere; the
  shape is volume-share dispersion, not price impact; the frozen ILLIQ brief is untouched.
- V11-LOTTERY-MAX-SKEW: H uses NO return moments (no MAX, no skew, no lottery characteristics);
  only volume shares across time.
- V12-OILEV-V2: no OI data enters any signal (declared in section 10); no OI differencing,
  level or flow.
- V6/V1-CARRY-FUNDING: funding only as an identical native cost across arms; never a signal.
- V4-XSECT-MOM / V8R-XSECT-REVERSAL / V9-TS-TREND / WEEKLY-REVERSAL: no return term enters any
  signal.
- V10-M01-AGGRESSOR-ABSORPTION: no aggressor/order-flow panels; 15m LAST bars only.
- V12-BAB-LOWBETA: no beta-sorted book; beta only as identical context adjustment.

## 12. Shadow-region determination and front-door disclosures (voluntary, pre-staged)

Determination: the mechanism is a liquidity-supply STRUCTURE story (standing-liquidity
reliability), not a liquidity-provision premium harvested against providers and not a
crowding-premium rescue. No prior control arm measured volume-time concentration: the recorded
shadow observations (inverted OI-flow +0.758 in the V12 OILEV-V2-28D-FLOW-W-INV control; V11
LOT inversion; stocks-program vol-level sorting) involve different variables and no observed
sign exists for this mechanism. The proposal therefore declares itself OUTSIDE the shadow
region, with no prior-sign disclosure to make beyond the inventory's own recorded observations.
In the alternative — if A1/A7-N classify any liquidity-provision conditioning as inside the
shadow region — the front door is pre-staged and accepted:
1. Mechanism stated in its own words above (sections 1-2), never as "the inverted anchor".
2. Disclosure: the sign of THIS mechanism was never observed in any V12/V11 control arm; the
   recorded shadow observations are the inventory's own (listed above) and none is a
   volume-time-concentration result. If shadow-classified, this family is preregistered
   CONFIRMATORY and its confirmatory status recorded in the verdict and denominator.
3. Own causal negative control (section 6) separating the mechanism from any rejected ancestor
   (sign-inverted arm isolates the directional claim; no OI or funding variable exists in the
   signal to confound with carry) and from beta/funding carry (identical costs/funding across
   arms; BTC-beta-adjusted gate).
4. The binding A7-N rank-correlation check |rho| <= 0.20 against the frozen OILEV-V2 anchor AND
   its inverted control on the common window is accepted as an eligibility condition;
   failure renders this proposal INELIGIBLE.
5. Stage-A gates apply with no relaxation.

## 13. Outcome-blind attestation

```
OUTCOME-BLIND ATTESTATION
lane: a5  proposal: A13-V13-A5-LIQEPIS
I wrote this mechanism and its falsification conditions before computing any
return, metric or ranking, and without access to any scored artifact or
outcome file.
utc: 2026-09-04T11:19:42Z  agent: a5
```
