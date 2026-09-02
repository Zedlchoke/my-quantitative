# A3 Family 2 — Listing-age overpricing of young listings

- **family_id**: `EQ_S2_A3_F2_LISTING_AGE`
- **proposer**: A3 lane (data / security master / point-in-time universe), branch `orca/stocks-s2-prop-a3`
- **machine-readable twin**: `research/proposals/stocks/a3_family2.json`
- **status**: outcome-blind proposal. No scored PnL, PF, Sharpe or ranking was computed in this lane, and no other proposal lane's files were read.

## Why this proposal comes from the data/PIT lane

This is the one equity family whose anchor signal **is** a security-master field:
`listed_age = decision_date - listed_date`, straight off the PIT
`SecurityMaster`. It is also the family most easily faked by the exact data
pathologies A3's gates exist to catch:

- **survivorship bias**: sampling only names still listed today overweights the
  young cohorts that lived, silently inflating "avoid young" strategies;
- **delisting bias**: dropping final prints of performance delists removes the
  worst outcomes of young names (Shumway 1997; Shumway & Warther 1999) —
  precisely what `evaluate_delisting_retention` forbids;
- **ticker-inception proxies**: using "first bar seen in the database" or a
  ticker's first appearance instead of the true listing date mis-measures age by
  exactly the years that matter.

The shipped factory makes the honest construction the only construction
(effective-dated ticker history, listing/delisting dates, `last_valid_event`,
delisting retention gate, `history_days` on `EligibilityInput`).

## 1. Economic mechanism and counterparty

Young listings concentrate optimistic, disagreement-prone ownership against
binding short-sale constraints and a thin, partly locked float. Divergence of
opinion under short-sale constraints prices in the optimists' view (Miller
1977); the new-issues literature documents the resulting multi-year
underperformance of new listings versus matched seasoned peers (Ritter 1991;
Loughran & Ritter 1995). The demand side is reinforced by lottery-type
preferences concentrated in young, low-price shares (Kumar 2009) and the episode
literature shows its extreme form in young internet shares (Ofek & Richardson
2003). The supply side — lockup expiries releasing insider shares — adds
pressure exactly where the mechanism predicts (Field & Hanka 2001).

**Expected counterparty**: constrained optimists — lottery-preference and
attention-driven flow plus momentum chasers — buying from insiders/underwriters
distributing a thin float. They persist because they are not price-elastic, and
short-side arbitrage is structurally expensive: young names are frequently
unborrowable or borrow at penalty fees (Nagel 2005), spreads are wide, and
ownership is concentrated in scheduled sellers.

## 2. PIT fields and source authority

**Factory-expressible today (synthetic fixtures)**

- `listed_date`, `delisted_date`, `last_valid_event`, `primary_exchange`,
  effective-dated `ticker_history` — `SecurityMaster`;
- `history_days` on `EligibilityInput` (age rules expressible as selection
  logic in `build_rebalance_snapshot`);
- delisting-retention gate `evaluate_delisting_retention`;
- ACCEPTED/REJECTED snapshot rows with reasons and canonical digest;
- daily OHLCV with `ts_exchange`/`ts_ingest` via `BarLoader`; next-open /
  next-close events via the US equity session calendar; one-event entry delay
  helpers (A5).

**UNAVAILABLE_PENDING_ENTITLEMENT today**

- authoritative PIT security master (true list dates, exchange identity, full
  ticker history);
- delist reason/compensation codes for Shumway-style delisting-return treatment;
- PIT sector (GICS as-of) assignments;
- PIT borrow availability/fee for every short;
- lockup-expiry / follow-on-offering records (attribution context only);
- >= 8y real daily history including delisted names through final valid event.

**Authority policy**: per `research/assets/stocks/provider.py`, authority
requires a verified `EntitlementRecord` covering `REQUIRED_LICENSE_SCOPE`
(PIT_SECURITY_MASTER, DELISTINGS, CORPORATE_ACTIONS, HISTORY_WITH_ADJUSTMENTS);
free-convenience endpoints are `DIAGNOSTIC_ONLY`. A free "first bar seen" proxy
for list date is precisely the failure mode this family forbids.

**Data readiness**: implementable against the synthetic-fixture factory now;
real-data readiness BLOCKED pending owner-authorized entitlement
(`NO_ENTITLEMENT_FAIL_CLOSED`).

## 3. Universe, neutralization, benchmark

US-listed common stocks via `build_rebalance_snapshot` with PLAN floors (>= 30
eligible liquid names per decision; both ACCEPTED and REJECTED rows retained
with reasons; delisted members retained through final valid event). Book is
**sector-neutral, dollar-neutral**, formed monthly: within each PIT sector
bucket, equal-weight **long seasoned** (listed_age >= 5 years) against **short
young** (listed_age <= 12 months) in-sector peers; zero net sector and dollar
exposure. Benchmarks: flat and SPY total return inside the declared
sector-neutral context per PLAN §10.

## 4. Formation, holding, execution clocks

- **Formation**: monthly, first regular-session close of the calendar month
  (declared schedule on the official US equity calendar; never a manufactured
  calendar). All inputs PIT as of that close.
- **Entry**: next regular-session **open** (one-event entry delay is inherent;
  no fill on halt / closed session / missing quote).
- **Holding**: one month; the book rolls at the next formation's entry.
- **Execution events**: next-open entries/exits; VWAP-style execution across the
  session expressible via loader intraday bars when the intraday entitlement and
  the >= 3y intraday floor exist.
- **Grid prohibition**: exactly one young band (<= 12 months) and one seasoned
  threshold (>= 5 years), both ex-ante mechanism constants (float-unlock
  horizon ~1y; multi-year history needed for a seasoned comparator). No age,
  lookback or threshold sweep in any arm.

## 5. Expected turnover and capacity

Monthly full roll implies ~12 round trips per position per year (~24 one-side
turnovers/year). Capacity is bounded by the young short leg: small ADV, tens of
bps spreads, frequent borrow unavailability. With the A5 square-root impact
model, hard order-size caps at declared ADV participation, and the >= 30-name
eligibility floor, order-of-magnitude capacity is **low tens of millions USD**
AUM. The seasoned long leg is liquid; the young short leg binds first.

## 6. Anchor, neighbour, negative control

| arm | id | statement |
|---|---|---|
| anchor | `EQ_S2_A3_F2_ANCHOR` | Monthly sector-neutral young-vs-seasoned book per PIT `listed_date`; next-open entry; one-month roll; borrow-gated shorts; delisting-safe accounting. |
| neighbour | `EQ_S2_A3_F2_NEIGH_CONSTRAINT_GRADIENT` | Same book/clocks, young short leg restricted to names with an available PIT borrow quote at a fee above a declared floor (constraints demonstrably binding). The mechanism predicts the drift concentrates where constraints bind (Nagel 2005; Ofek & Richardson 2003) — the neighbour must support the anchor. |
| negative control | `EQ_S2_A3_F2_CTRL_AGED_ENTRY` | Same securities, same sector book, same clocks, but the short leg's entry clock is delayed until each name's listed_age exceeds the seasoned threshold (the identical cohort re-entered only once no longer young). If the mechanism is real, the control's edge must be destroyed (~0 after costs). If the drift persists in the control, the effect is a persistent junk-characteristic confound, not listing-age overpricing — family falsified. |

The control is genuinely causal and expressible today: it severs "youngness"
via the age clock (`EligibilityInput.history_days`) while keeping the securities,
sectors and schedule identical — a size/growth confound that would survive a
simple exclusion test cannot survive the cohort clock shift, and if it does, the
anchor is dead.

## 7. Corporate actions, earnings, borrow, dividends

Splits and dividends applied exactly once at ex/effective timestamps (A4);
declared RAW fill path vs TOTAL_RETURN research path with reconciliation. A young
name delisting inside the window is exited at its final valid event with
Shumway-style delisting-return treatment (performance delists carry their
negative return; merger delists exit at the deal print) — exactly what the
delisting-retention gate enforces. The first post-listing earnings cycles are
part of the mechanism's resolution window; positions are held through them;
PIT BTO/AMC timestamps (UNKNOWN fails closed) used for attribution only. Every
short requires locate plus a PIT borrow fee; unavailable borrow => the short is
rejected with a reason (never a free fill), coverage reported per rebalance.
Dividend receipt on longs and short dividend liability on shorts per the A5
identity.

## 8. Falsification rule and external validity

The family dies if any of:

1. the aged-entry control retains materially the anchor's after-cost edge
   (characteristic confound);
2. the neighbour fails to concentrate the drift where constraints bind;
3. the edge exists only when delisted names are dropped or final prints
   truncated — the honest delisting-retained construction shows no edge while a
   survivorship-only variant does (declared a data artifact);
4. the edge vanishes under x1.5 costs, impact at declared ADV caps, or borrow
   x2/unavailable stress;
5. any Stage-A gate (PLAN §13) fails.

**External validity caveats**: the effect is episode- and vintage-concentrated
(documented especially around 1999-2000) — report by cohort vintage and
sub-period, never pooled. Listing technology changes (direct listings, spin-offs,
de-SPAC) alter float/lockup structure; the declared scope is common-stock
listings from the PIT security master, and structures outside that class are out
of scope. Borrow economics are the binding limit; without PIT equity-loan data
the family must be declared borrow-infeasible rather than run on free shorts.

## 9. Maximum trial count

Exactly **3** computed cells: anchor, neighbour, negative control.

## Ineligibility attestation

Not an indicator/lookback grid: age bands are single ex-ante mechanism
constants, one monthly clock, one neutralization, nothing swept. Not a
transplanted crypto family: versus rejected M01 aggressor-flow absorption the
observable (PIT listed_age vs order-book imbalance), counterparty (constrained
optimists vs momentum aggressors), clock (monthly next-open vs intraday) and
causal control (aged-entry cohort shift) all differ; no funding-carry term
anywhere (the borrow fee is a cost constraint, not a signal); not a weekly
reversal clock and the young short leg is not conditioned on past returns.

## Literature (MODEL_INTERNAL_UNVERIFIED)

Attributions from internal knowledge of published literature; network
verification unavailable; no DOIs asserted; no direct quotes; exact volume/page
details deliberately omitted.

- Miller, E. (1977). Risk, Uncertainty, and Divergence of Opinion. *Journal of
  Finance*.
- Ritter, J. (1991). The Long-Run Performance of Initial Public Offerings.
  *Journal of Finance*.
- Loughran, T. & Ritter, J. (1995). The New Issues Puzzle. *Journal of Finance*.
- Shumway, T. (1997). The Delisting Bias in CRSP Data. *Journal of Finance*.
- Shumway, T. & Warther, V. (1999). The Delisting Bias in CRSP's Nasdaq Data.
  *Journal of Finance*.
- Field, L. & Hanka, G. (2001). The Expiration of IPO Share Lockups. *Journal of
  Finance*.
- Ofek, E. & Richardson, M. (2003). DotCom Mania: The Rise and Fall of Internet
  Stock Prices. *Journal of Finance*.
- Nagel, S. (2005). Short Sales: Institutional Investors and the Equity Loan
  Market. *Journal of Financial Economics*.
- Kumar, A. (2009). Who Gambles in the Stock Market? *Journal of Finance*.
- Hong, H. & Stein, J. (2007). Disagreement and the Stock Market. *Journal of
  Economic Perspectives*.
