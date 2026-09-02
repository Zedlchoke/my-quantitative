# A3 Family 1 — PIT index-reconstitution forced-flow drift

- **family_id**: `EQ_S2_A3_F1_PIT_RECON_FLOW`
- **proposer**: A3 lane (data / security master / point-in-time universe), branch `orca/stocks-s2-prop-a3`
- **machine-readable twin**: `research/proposals/stocks/a3_family1.json`
- **status**: outcome-blind proposal. No scored PnL, PF, Sharpe or ranking was computed in this lane, and no other proposal lane's files were read.

## Why this proposal comes from the data/PIT lane

Index membership is the canonical dataset that naive backtesting silently fakes: a
"current members" table projected backwards fabricates a history that no investor
could have observed. The shipped factory makes the honest version the *only*
version — `MembershipTable` structurally bans backfill (membership rows require
`effective_from`; the only read API is `members_as_of`), and the security master
resolves identity `as_of` with effective-dated ticker history. The mechanism below
is expressible **only** on such effective-dated membership plus PIT announcement
timestamps. That is the A3 lens: the edge lives in point-in-time universe
construction and PIT membership reconstitution, where sloppy data handling does
not merely add noise — it makes the object under study unmeasurable.

## 1. Economic mechanism and counterparty

When a major cap-weighted benchmark announces an addition or deletion effective at
a future date, every fund tracking that benchmark must trade the change at/near
the effective close to avoid tracking error. That demand is mandate-driven and
price-inelastic: it does not respond to price, only to the membership fact. The
classical price-pressure literature documents exactly this slope in demand curves
around index changes (Shleifer 1986; Harris & Gurel 1986), its anticipation once
the game became known (Beneish & Whaley 1996), its partial but incomplete
arbitrage (Wurgler & Zhuravskaya 2002; Greenwood 2005), and its identification in
a rule-based recon setting (Chang, Hong & Liskovich 2015).

**Expected counterparty**: index-tracking funds and benchmark-constrained active
managers. They persist structurally because their objective function is tracking
error against a benchmarked mandate, not expected profit (Baker, Bradley & Wurgler
2011 — benchmarks as limits to arbitrage). Every year produces new adds/deletes
and the passive complex keeps growing, so the counterparty does not disappear;
front-running by recon traders competes the effect down but cannot remove the
forced flow itself, because somebody must end up holding the name at the
effective close in the proportion the index dictates.

## 2. PIT fields and source authority

**Factory-expressible today (synthetic fixtures)**

- stable `security_id` + `ticker_as_of(security_id, as_of)` — `SecurityMaster`;
- effective-dated membership rows via `MembershipTable` (only `members_as_of`;
  structural no-backfill ban);
- announcement/effective event stream through `BarLoader` event rows with
  `ts_exchange`/`ts_ingest` (tz-aware, ingest >= exchange enforced);
- daily OHLCV, checksum-verified, gap-fail-closed;
- ACCEPTED/REJECTED rebalance rows with mandatory reasons and canonical digest.

**UNAVAILABLE_PENDING_ENTITLEMENT today**

- authoritative PIT index announcement records (`announce_ts`, `effective_ts`,
  `event_type`, `universe_id`, `security_id`) from the index provider's
  maintenance history;
- authoritative non-backfilled membership history for the benchmark **and** the
  control index;
- per-index tracking-AUM estimates (PIT, annual) to rank flow intensity;
- PIT sector (GICS as-of) assignments;
- PIT borrow availability/fee for every short (A5 gate);
- >= 8y real daily history with delistings retained (PLAN §7 floors).

**Authority policy**: per `research/assets/stocks/provider.py`, every adapter
defaults to `NO_ENTITLEMENT_FAIL_CLOSED`; authority requires a verified
`EntitlementRecord` covering `REQUIRED_LICENSE_SCOPE`
(PIT_SECURITY_MASTER, DELISTINGS, CORPORATE_ACTIONS, HISTORY_WITH_ADJUSTMENTS)
on an authority-capable source class. Free-convenience data is
`DIAGNOSTIC_ONLY` and can never satisfy authority — including for announcement
timestamps, which are precisely where a free-feed shortcut would fake this family.

**Data readiness**: implementable against the synthetic-fixture factory now;
real-data readiness BLOCKED pending owner-authorized entitlement
(`NO_ENTITLEMENT_FAIL_CLOSED`).

## 3. Universe, neutralization, benchmark

US-listed common stocks via `build_rebalance_snapshot` (ACCEPTED and REJECTED
rows both retained with reasons; >= 30 eligible liquid names per decision; S0
floors enforced). Signal book is **sector-neutral, dollar-neutral**: long
announced additions, short announced deletions, matched within PIT sector buckets
(sector as-of formation). Benchmarks: flat and SPY total return, evaluated inside
the declared sector-neutral/dollar-neutral context per PLAN §10.

## 4. Formation, holding, execution clocks

- **Decision**: an announcement may be used only at the first regular-session
  close strictly after its `ts_ingest` (PIT discipline; a signal may execute only
  on a later observable event — one-event entry delay, A5 helpers).
- **Formation**: next-close after the announcement is observable.
- **Entry**: next regular-session close (declared close-event fill; no fill on
  halt / closed session / missing quote). Early closes honoured via the calendar.
- **Holding**: to the session close 20 sessions after the effective date — a
  fixed ex-ante constant of the order of the documented pressure window, not a
  tuned parameter.
- **Execution events**: session-close events; VWAP-style execution over the
  entry/exit session is expressible via loader intraday bars and becomes the fill
  path when the intraday entitlement and the >= 3y intraday floor exist.
- Overlapping event books aggregate; per-name caps; no re-entry per
  (security_id, announcement).

## 5. Expected turnover and capacity

One round trip per announced name with ~25-session holding implies each traded
name turns ~8-10x per year while held; at book level, order 10-40 announced
changes/year plus one large annual reconstitution gives effective turnover of
order 4-10x/year of average one-side notional. Capacity is bounded by the A5
impact model (square-root law, hard order-size caps at declared ADV
participation; oversized orders do not fill) and by event concentration: a single
reconstitution must clear through closing-auction liquidity, so per-name order
size must stay a small fraction of effective-date volume. Order-of-magnitude
capacity: tens of millions to low hundreds of millions USD AUM; deletions
(wide-spread, deteriorating names) bind first.

## 6. Anchor, neighbour, negative control

| arm | id | statement |
|---|---|---|
| anchor | `EQ_S2_A3_F1_ANCHOR` | Long announced adds / short announced deletes of the primary benchmark; sector-neutral dollar-neutral; next-close formation, next-close entry, exit effective+20 sessions; borrow-gated shorts. |
| neighbour | `EQ_S2_A3_F1_NEIGH_RULE_BASED_RECON` | Same mechanism, rule-based identification: threshold-split (Russell-style) reconstitution where adds/deletes are pure rule, not committee discretion; same clocks and gates. If forced benchmark flow is real, the neighbour must support the anchor (Chang, Hong & Liskovich 2015). |
| negative control | `EQ_S2_A3_F1_CTRL_NOFLOW_INDEX` | Identical observable, clock and neutralization applied to membership changes of a matched index with economically negligible tracking assets (no investable tracking products). If the mechanism is real, the control's after-cost edge must be destroyed (≈ 0). If the control shows the same drift, the anchor is a characteristic confound and the family is falsified. |

The control is genuinely causal: it severs forced inelastic flow while keeping
everything else identical — including the "index change" observable itself, so it
cannot be satisfied by a momentum/size story that would also move the anchor.

## 7. Corporate actions, earnings, borrow, dividends

Splits and cash dividends applied exactly once at ex/effective timestamps (A4);
declared RAW fill path vs TOTAL_RETURN research path with reconciliation;
delisted names retained through their final valid event and a deletion position
exited at its delisting event (never silently dropped). Earnings inside the
window are not signals; positions are held through them; PIT BTO/AMC
classification (UNKNOWN fails closed) used only for attribution. Every short
requires locate plus a PIT borrow fee; unavailable borrow => the short is
rejected with a reason and the book re-normalizes; coverage is reported per
event. Dividend receipt on longs, short dividend liability on shorts, per the A5
accounting identity.

## 8. Falsification rule and external validity

The family dies if any of:

1. the negative control retains materially the anchor's after-cost edge
   (confound, not forced flow);
2. the neighbour contradicts the anchor;
3. the edge vanishes under one-event entry delay, x1.5 costs, impact at declared
   ADV caps, or borrow x2/unavailable stress;
4. the edge exists only with backfilled current membership rather than
   `members_as_of` effective rows (pure data artifact);
5. any Stage-A gate (PLAN §13) fails.

**External validity caveats**: inclusion effects are documented to have decayed
as the passive complex grew and recon trading industrialised (anticipation was
already measurable in the 1990s); announcement-to-effective windows changed by
era, so window constants must be declared per announcement-era from PIT records;
the neighbour's identification depends on band/assignment rules that themselves
changed over time. Results must be reported by sub-period and by flow-intensity
bucket, never as a single pooled average.

## 9. Maximum trial count

Exactly **3** computed cells: anchor, neighbour, negative control.

## Ineligibility attestation

Not an indicator/lookback grid: one event type, one declared window constant set,
one neutralization, nothing tuned against outcomes. Not a transplanted crypto
family: versus rejected M01 aggressor-flow absorption the observable (PIT
effective-dated membership + scheduled announcements vs order-book aggressor
imbalance), counterparty (mandate-forced index funds vs momentum aggressors),
clock (multi-week announcement-to-effective schedule vs intraday) and causal
control (no-tracking-AUM index) all differ; no funding-carry term; not a periodic
reversal clock.

## Literature (MODEL_INTERNAL_UNVERIFIED)

Attributions from internal knowledge of published literature; network
verification unavailable; no DOIs asserted; no direct quotes; exact
volume/page details deliberately omitted.

- Shleifer, A. (1986). Do Demand Curves for Stocks Slope Down? *Journal of Finance*.
- Harris, L. & Gurel, E. (1986). Price and Volume Effects Associated with Changes
  in the S&P 500 List. *Journal of Finance*.
- Beneish, M. & Whaley, R. (1996). An Anatomy of the "S&P Game": The Effects of
  Changing the Rules. *Journal of Finance* (year/journal detail UNVERIFIED).
- Wurgler, J. & Zhuravskaya, E. (2002). Does Arbitrage Flatten Demand Curves for
  Stocks? *Journal of Economic Perspectives*.
- Greenwood, R. (2005). Short- and Long-Term Demand Curves for Stocks. *Journal
  of Financial Economics*.
- Barberis, N., Shleifer, A. & Wurgler, J. (2005). Comovement. *Journal of
  Financial Economics*.
- Chang, Y.-C., Hong, H. & Liskovich, I. (2015). Regression Discontinuity and the
  Price Effects of Stock Index Inclusion. *Journal of Financial Economics*.
- Baker, M., Bradley, B. & Wurgler, J. (2011). Benchmarks as Limits to Arbitrage.
  *Financial Analysts Journal*.
