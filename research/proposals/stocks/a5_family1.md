# A5-S2 Family 1 — Lending-Constraint (Borrow-Fee) Short Premium

- lane: A5 (accounting / borrow / execution), sprint S2
- family_id: `A5-S2-F1-LENDING-CONSTRAINT-PREMIUM`
- arms: `anchor`, `neighbour`, `negative_control` — exactly 3 cells
- retrieval note: literature is cited from **MODEL_INTERNAL_UNVERIFIED** memory (no network this sprint). No DOIs, no verbatim quotes.
- outcome-blind: no scored PnL/PF/Sharpe/ranking computed or read anywhere in this proposal; the cost-drag arithmetic below is analytic, derived from the frozen cost models (`research/assets/stocks/execution.py`, `research/assets/stocks/accounting.py`) and published magnitudes only.

## 1. Economic mechanism and expected counterparty

Where the securities-lending market is scarce — low lendable supply relative to short demand, expressed economically as a high point-in-time borrow fee and high lending utilization — optimists set the marginal price while would-be short sellers cannot arb the overpricing away (Miller 1977, *Journal of Finance*). The constrained tail therefore has abnormally low forward returns (D'Avolio 2002, *JFE* 66; Nagel 2005, *Journal of Finance*; Stambaugh, Yu & Yuan 2012, *JFE*). Kaplan, Moskowitz & Sensoy (2013, *Journal of Finance*) show causally that adding lending supply raises prices, and Blocher, Reed & Van Wesep (2013, *JFE*) connect lending supply to price effects through vote retention.

The harvested object is a **sector/size-neutral long-short spread**: short the lending-constrained tail **only where the locate is actually available at a PIT rate**, fund with lending-rich general-collateral names in the same bucket. The family's defining property is that the edge and the cost are the same object: the fee that ranks the names is the fee the canonical identity charges (`short_borrow_fees`), and the dividends the long leg collects reappear on the short leg as `short_dividend_liability`. Engines that book shorts at zero borrow and ignore the liability inflate this spread by roughly the full fee plus dividend yield of the short notional; the honest ledger keeps only the documented shorting-premium residue (Drechsler & Drechsler, "The shorting premium", working paper — venue unverified).

Expected counterparties:

1. **securities-lending desks** (beneficial owners / prime brokers) — they are paid the fee our short leg pays, and they control recalls;
2. **sentiment-driven retail longs** in the constrained names — providers of the overpricing;
3. **institutions with ample lendable supply** in the long-leg names — the other side of the lending income transfer.

## 2. PIT fields and source authority

| Field | Authority | Status |
|---|---|---|
| locate availability + annual borrow rate, daily, per symbol | prime-broker / securities-finance aggregator | **UNAVAILABLE_PENDING_ENTITLEMENT** |
| lending utilization (loans / lendable) | same feed | **UNAVAILABLE_PENDING_ENTITLEMENT** |
| biweekly short interest | FINRA consolidated | **UNAVAILABLE_PENDING_ENTITLEMENT** (corroborating observable only) |
| price, NBBO quotes, ADV, halted/session flags | US equities OHLCV + quotes provider | synthetic fixture **now**; real **UNAVAILABLE_PENDING_ENTITLEMENT** |
| PIT GICS sector, size bucket, listing/delisting | security master (A3) | synthetic fixture **now**; real **UNAVAILABLE_PENDING_ENTITLEMENT** |
| splits/dividends with ex/effective timestamps | corporate-actions master (A4) | synthetic fixture **now**; real **UNAVAILABLE_PENDING_ENTITLEMENT** |
| earnings timestamps, PIT, B/A classified | earnings calendar provider | **UNAVAILABLE_PENDING_ENTITLEMENT** |
| borrow recall events | prime-broker feed | **UNAVAILABLE_PENDING_ENTITLEMENT** — declared caveat, never silently modeled |

Factory bindings: `BorrowLocate`, `SharedCapitalReplay.submit_intent` locate gate, `compute_borrow_fee` (360-day basis), `DividendEvent` buckets, `EquityExecutionModel.attempt_fill` fail-closed inputs.

## 3. Universe, neutralization, benchmark

- Universe: PIT population of US-listed common stocks, price >= 5 USD, ADV floor, primary US listing; membership decided **only at formation**; delisted names retained to their last valid event.
- Neutralization: dollar-neutral long/short **within PIT sector bucket**, matched into size buckets; no current-membership backfill.
- Benchmarks: flat, SPY total return, and the declared factor-neutral context (sector + size bucket neutral long/short; the portfolio is its own factor context).

## 4. Formation, holding and execution clocks

- **Formation**: month-end regular-session close; rank by PIT borrow-fee percentile (anchor) within sector/size bucket.
- **Holding**: until the next month-end signal (~21 sessions). Borrow fee accrues daily at `rate * days / 360` while the short is held (`accrue_borrow_fee`); daily PIT locate re-check gates **new opens only**; missing/unavailable locate is a zero-cost rejection record — a short is never filled for free (factory-native).
- **Execution**: entries at the first executable regular-session event strictly after the formation close (one-event delay, `next_executable_event_index`); exits at the executable event after the next signal. Every order passes `attempt_fill`, whose HALTED -> SESSION_CLOSED -> MISSING_QUOTE -> MISSING_ADV -> PARTICIPATION_CAP order fails closed: a halted or unquoted name is skipped with rejection evidence and never priced off a stale print. Terminal valuation on the last observable executable event.

All three clocks are directly expressible in the existing factory; no new machinery is required.

## 5. Expected turnover, capacity and cost-drag reasoning

- Turnover: monthly two-sided rebalance with leg overlap rho ~ 0.6-0.8 gives roughly 2*(1-rho)*12 ~ 500-1000%/yr two-sided turnover of per-leg notional — slow by design.
- Friction per side per rebalance (frozen model): commission ~0.3-1 bps; half-spread from quotes when entitled, else the declared conservative proxy — of order 3-10 bps on the liquid long names and 10-25 bps on the deliberately illiquid constrained short names; declared slippage bps; sqrt impact at <= 2% participation with a hard cap (orders above the cap do not fill).
- **Dominant drag — short-leg carry**: special-name fees of order 3-10%/yr (D'Avolio 2002 fee distribution) over near-full-year exposure give ~3-10%/yr on short notional, plus short dividend liability of order 1-2%/yr on short notional. The honest bar: the gross sector-neutral spread must exceed roughly **5-12%/yr on short notional plus trading friction**. Published gross overpricing spreads of order 5-15%/yr (Nagel 2005; Stambaugh-Yu-Yuan 2012) shrink to the shorting-premium residue once this is paid. A zero-borrow replay of the identical ranking is expected to "earn" several points/yr more than the honest ledger — that delta is this family's built-in falsification diagnostic.
- Capacity: bounded by the short leg — constrained names are by definition low-lendable, typically mid/small; realistic capacity is low single-digit percent of short-leg ADV, order 10-100M USD strategy-wide, and shrinks when specialness is concentrated.

## 6. Anchor, neighbour, causal negative control (3 cells)

1. **anchor** — sector/size-neutral long lending-rich vs short lending-constrained tail, ranked by PIT borrow-fee percentile, locate-gated, honest borrow + dividend-liability accounting.
2. **neighbour** — identical construction with the ranking replaced by PIT lending utilization. Justified: fee and utilization are the price and quantity of the same lending market (D'Avolio 2002; Geczy, Musto & Reed 2002, *JFE* 66), so the mechanism predicts the same sign; sign disagreement would indicate a fee-data artifact rather than lending scarcity.
3. **negative_control** — identical machinery, universe, buckets and clocks executed entirely among general-collateral names (top lending-supply tercile), with the same fee-rank placebo ordering inside that bucket. The constraint cause is absent there, so the mechanism predicts a spread indistinguishable from zero after costs; a full-magnitude spread would falsify the mechanism as an unidentified ranking artifact.

## 7. Corporate actions, earnings, borrow, dividends

- **Corporate actions**: splits applied at PIT ex/effective events with position continuity; names with a split inside the entry window deferred one formation; terminal valuation only on executable events.
- **Earnings**: entry skipped for a name whose PIT earnings timestamp falls on the entry session (zero-cost rejection evidence); positions otherwise deliberately held through earnings — the documented unwind is over weeks, so avoiding all earnings would gut the mechanism.
- **Borrow (special duty)**: locate per name per formation, re-checked daily; missing/unavailable locate rejects the short with zero cost, no fill (never overridden); daily fee accrual at `rate*days/360`; recalls are UNAVAILABLE_PENDING_ENTITLEMENT and declared as an explicit external-validity caveat rather than silently modeled. Feasibility conditional: a constrained name is traded only if the expected fee over the holding period does not exceed its expected overpricing contribution — the ledger never books a short whose carry the mechanism cannot afford.
- **Dividends**: long leg books `cash_dividends` at ex-date; short leg books the same event as `short_dividend_liability`. No adjusted/total-return series is used for fills or short-leg carry, so the liability cannot hide inside an adjustment factor — this is precisely where naive accounting silently fakes or destroys the effect.

## 8. Falsification rule and external-validity caveats

Falsify the family if ANY of:

1. anchor's honest sector-neutral spread (net of borrow fee, short dividend liability, all four execution-cost buckets and rejections) is not positive in S0 folds;
2. the negative-control arm's spread is not materially weaker than the anchor's;
3. the utilization-ranked neighbour disagrees in sign with the anchor;
4. an accounting-only counterfactual shows the anchor's gross spread smaller than its short-leg carry drag — i.e., the published edge exists only under zero-borrow accounting.

All four conditions are preregistered here before any scored cell exists.

Caveats: lending-data entitlement is the binding dependency; securities-finance snapshots are prone to backfill/survivorship (A3/A4 PIT ingest discipline is load-bearing); recall/squeeze episodes (2008, 2021) can erase months of premium in days and are not modeled; the shorting premium is crowding-sensitive; post-2003 and post-RegSHO regime changes are structural breaks.

## 9. Maximum trial count

**Exactly 3 cells** (anchor, neighbour, negative_control). No lookback/threshold grid exists anywhere in the family.

## Eligibility and novelty

- Not an indicator/lookback/threshold grid: one mechanism, three theory-linked arms.
- Not a rescue of the rejected crypto families (M01 aggressor-flow absorption, funding-carry, weekly reversal): distinct **observable** (PIT securities-lending fee/utilization, not perp funding or flow absorption), distinct **counterparty** (lending desks + sentiment longs, not crypto perp counterparties), distinct **clock** (monthly formation, month-long holds, not intraday/weekly reversal), distinct **causal control** (GC-placebo arm removing the constraint channel — none of the banned families had a lending-supply control).

## Data readiness

- Synthetic-fixture factory: **IMPLEMENTABLE NOW** (locate/fee records, dividends, quotes, halts, ADV are first-class fixture inputs).
- Real data: **BLOCKED pending owner-authorized entitlement** (securities-finance feed, FINRA short interest, PIT earnings calendar). This proposal authorizes no purchase.
