# GC_DOSSIER — Gold Futures (COMEX GC)

- Symbol: GC (COMEX division of CME Group; tradingClass `GC` — NOT the 1000oz SIL class, and
  not to be confused with micro MGC)
- Exchange: COMEX (via CME Globex); vendor endpoint IB TWS API, timezone US/Eastern
- Generated_utc: 2026-10-02 (lane local; all web access dates below are 2026-10-02)
- Author lane: SYMBOL-DOSSIER-GC, task FUTURES-BEHAVIOR-10SYMS-PREP-20261002 (PREP ONLY —
  no scored runs, no PnL/event-studies/sweeps, no GO)
- Inputs:
  - owner_framework/GC_RESEARCH_FRAMEWORK.md sha256
    `be444f2368c5f324be2bcfcc0f1d4999a586b05e631fde4039aa050a5c581bb9`
    (owner_framework/SHA256SUMS.txt); 00_MASTER_FRAMEWORK.md sha256
    `a75571b8017b13b5ff6552755d1334b03db640ebc26a6b4c9ad4323ca16d3c74`
  - research/control/FUTURES-DATA-10SYMS-V1/FINAL_REPORT.md sha256
    `9722d3a123da7e3bc1546293705c241aab7eb938fed38a08f2f07600926e4260` (untracked snapshot,
    read-only) + S1_IDENTITY.json sha256 `d217ab9dcd865765e1bcae8f8131dee2f7f200cd90c07403280134da32b05822`,
    S6_VALIDATION.json, S6_FRONT_SPREADS.json, S9_INDEPENDENT_VERIFY.md,
    costs/SPECS_MARGINS_PUBLIC_2026-10-02.md, costs/IBKR_futures_commissions_2026-10-02.json
  - Raw (read-only): ~/.my-quantitative-data/futures-10syms-v1/raw/ files `GC_*`
    (22 contracts × 5 job types = 110 files)
  - Analysis: analysis/GC_descriptives.py → analysis/GC_descriptives.json (this lane,
    descriptive only, strict past/rolling windows)
- Claims taxonomy used everywhere below: FACT (sourced) / OBSERVED (raw+script+window) /
  POSTULATED (mechanism, unmeasured) / NOT_RUN (default; never inferred PASS).

## 1. Mechanics

- Underlying exposure: 100 troy oz of refined gold, USD/oz quotation, physically delivered at
  expiry. [FACT-primary-partial: official CME product page (cmegroup.com/markets/metals/
  precious/gold.contractSpecs.html, accessed 2026-10-02 via web-reader fallback; direct
  WebFetch times out) confirms physical settlement and nearly-24-hour electronic access, but
  the numeric spec table is JS-driven and did NOT render] [FACT-secondary for the numbers:
  NinjaTrader mirror of CME spec, fetched by data lane 2026-10-02,
  costs/SPECS_MARGINS_PUBLIC_2026-10-02.md] [OBSERVED corroboration: S1_IDENTITY.json GC —
  multiplier "100", minTick 0.1, currency USD, longName "Gold", validExchanges
  COMEX,QBALGO, uniform on all 22 resolved contracts]
- Tick/multiplier/quote convention: minTick 0.1 USD/oz → tick value 10 USD/contract
  (100 oz × $0.10). Quote is USD per troy ounce; raw closes 2023-11→2026-10 span
  $1,570.5–$5,718.2/oz (min is the 2020 settlement era; max is the 2026-01 spike top) —
  scale-consistent with USD/oz, no 6J-style inversion. [OBSERVED: analysis/GC_descriptives.json
  `quote_convention_check`; S1 broker secdef]
- Participants: hedgers = miners (sell-side forward hedging), jewelers/fabricators, bullion
  banks (delivery/carry arbitrage, EFP vs spot London); speculators = macro funds, CTAs,
  ETF-like index flow; central-bank-related flows (official sector buying is reported monthly
  by IMF/WGC, not real-time); market makers/arbitrageurs link GC to XAU spot, lease rate and
  forwards. [POSTULATED: participant map per owner framework §core; not measured here]
- Sessions & DST: COMEX Globex session 18:00 ET (day-1) → 17:00 ET (day-2), Sun open / Fri
  close; liquid (RTH) window 09:30–17:00 ET per broker secdef `liquidHours`.
  [OBSERVED: S1_IDENTITY.json tradingHours/liquidHours strings, e.g.
  "20260930:1800-20261001:1700"; bar timestamps carry ISO offsets and DST was verified
  correct at bar date by S9 (50/50 files across NQ/CL/6J, method applicable; GC files carry
  US/Eastern)] Raw daily files are stamped US/Eastern; hourly files are useRTH=True →
  09:30–16:00 labels only, so Asia/London overnight behavior is NOT in the intraday files.
  [OBSERVED: raw metadata; analysis `intraday_hourly_rth_only.caveat`]
- Holidays: exchange holidays absent from raw calendar — e.g. 2025-11-27 (US Thanksgiving)
  and 2026-01-19 (MLK Day) have no bars on GCZ5/GCG6 respectively; S1 tradingHours marks
  2026-10-03/04 CLOSED (weekend). [OBSERVED: raw daily panel; S1]
- Delivery/first-notice/expiry/last trade: physical delivery; last trade "ceases 13:30 ET on
  the third-last business day of the contract month" [FACT-secondary: NinjaTrader mirror;
  OBSERVED corroboration: S1 `lastTradeTime` 13:30 for every GC contract; per-contract
  lastTradeDate present, e.g. GCV6 20261028, GCZ6 20261229]. First-notice-day and delivery
  mechanics detail: NOT_RUN (no primary source fetched; CME page blocked). Price limits:
  NOT_RUN (no primary/secondary source fetched this session — do not assume "none").
- Listed months & liquid maturities: active cycle G,J,M,Q,V,Z (Feb/Apr/Jun/Aug/Oct/Dec)
  [OBSERVED: the 22-contract dataset is exactly the GJMQVZ chain 2025-10→2028-01 + monthly
  serials from 2026-10 onward; S6 `contract_months_available` shows near-monthly listings
  2025-10→2028-01 plus Jun/Dec out to 2032-12 — 40 listings]. Liquid maturity = the nearest
  active cycle month; serial months trade but thin. [POSTULATED for "serials thin";
  OBSERVED for dataset serial volumes: GCX6 total recorded volume 5,224 lots over its life
  vs GCZ5 8.57M — see volume caveat below]
- Liquidity migration front→next [OBSERVED on the thick-volume contracts,
  analysis `volume_migration`]: at every 2025-11→2026-07 cycle roll the old contract's
  volume collapses and the new contract's volume crosses over **1–2 sessions before** the
  declared roll session (flip offsets: GCZ5→GCG6 −2 (2025-11-25), GCG6→GCJ6 −2 (2026-01-28),
  GCJ6→GCM6 −2 (2026-03-27), GCM6→GCQ6 −2 (2026-05-27), GCQ6→GCV6 −1 (2026-07-30)).
  Example (2026-03-27): GCJ6 8,201 vs GCM6 82,091; two sessions later GCJ6 580 vs GCM6 77,044.
- **Volume-scale caveat (important)** [OBSERVED, analysis `roll_analysis.volume_scale_caveat`]:
  vendor-recorded daily volume is full scale (~30k–260k lots/day) for G/J/M/Q/Z-month
  contracts during their front windows, but 1–2 orders thinner for the V-month contracts
  (GCV5 front Aug–Sep 2025 median ≈ 3.0k; GCV6 front Aug–Sep 2026 median ≈ 3.2k) and for all
  deferred months. Hourly sums match dailies where checked (GCV6 2026-08-20: 6,068 = 6,068),
  so this is per-contract vendor recording, not aggregation error. Volume is therefore usable
  only for *relative* migration timing, never for absolute liquidity or capacity claims.
- PIT contract selection + roll rule: baseline = data lane's declared rule — hold until the
  last session BEFORE day-1 of the delivery month, roll to the next listed contract at that
  close (months listed years ahead → PIT-legal, no lookahead) [FACT: FINAL_REPORT §roll rule].
  **Executability defect found by this lane** [OBSERVED, analysis `serial_gaps`]: the raw set
  contains NO serial months for 2025-11…2026-09 (GCX5, GCF6, GCH6, GCK6, GCN6, GCU6 missing),
  so the declared "roll to next listed" is NOT executable on this dataset for the entire
  2025-09→2026-09 span; the executable approximation rolls cycle→cycle (a 1-month skip; each
  contract held ~2 months). Alternatives: (a) volume/OI roll — blocked: OI not in raw, and
  volume flip is only 1–2 sessions earlier than the declared date; (b) fetch the missing
  serials (cheapest fix, same entitlement, reqContractDetails already resolves that window).
  Roll cost: observable as adjacent-contract close gap but NOT_COMPUTED as a tradable cost
  here; measured raw gaps at the real-era cycle rolls: +32.4, +37.3, +31.2, +31.0, +32.5,
  +27.5 USD/oz across the first six, plus a SEVENTH completed inside the snapshot —
  GCV6→GCZ6 at 2026-09-30, gap +31.1 USD/oz, old leg 245 lots real volume [m2 fix
  2026-10-02, audit R5: the original text said "six" and omitted the 2026-09-30 roll that
  this dossier's own event calendar (§4) already recorded; the 7th gap sits inside the
  +27.5…+37.3 range and is consistent with the contango conclusion] (always positive —
  see §3 curve). [OBSERVED: analysis `roll_analysis.rolls`]

## 2. Causal driver map

Master-framework buckets covered for GC: Macro, Fundamental/physical (limited — monetary
metal, no inventory report of CL/NG type), Cross-asset, Positioning, Term structure,
Microstructure, Event-driven. Evidence class marks the *measurement* status in this prep.

| # | Driver (bucket) | Source variable → mechanism | Predicted sign / horizon | Regime dependency | Confounders | Falsification test | PIT data source (primary, access date) | Class |
|---|---|---|---|---|---|---|---|---|
| 1 | US real yields (Macro) | 10y TIPS yield ↑ → opportunity cost of zero-coupon metal ↑ → de-positioning | Negative for GC / days-weeks | Dominant outside acute crisis; can flip in stress | nominal rates vs breakeven decomposition; USD co-move | Real-yield shock days with no GC down-move drift | Treasury/CME TIPS yields, vintage-clean (treasury.gov; FRED ALFRED vintages) — NOT fetched this session | POSTULATED (mechanism), measurement NOT_RUN |
| 2 | USD / DXY (Macro, cross-asset) | USD ↑ → gold priced in USD cheaper for non-USD buyers → demand ↓ | Negative / days-weeks | Weaker when non-US (CB) demand dominates | US rates move with USD; safe-haven bid | Persistent GC-USD same-direction weeks | 6E futures in raw (own corpus, PIT) + DXY (ICE, official NOT fetched) | Mechanism POSTULATED; 6E data OBSERVED available |
| 3 | Fed policy expectations / FOMC (Macro, event) | Hawkish surprise → real-rate path ↑ → GC ↓ (and vice versa) | Event-day, minutes-hours | Easing cycles strengthen effect | statement vs pre-positioning; press conference drift | Post-FOMC 1-60min GC move vs rate-futures-implied surprise | FOMC calendar FACT (federalreserve.gov, 2026-10-02); surprise measure NOT_RUN (no PIT consensus in corpus) | Calendar FACT; response NOT_RUN |
| 4 | Inflation expectations / CPI·PCE (Macro, event) | Surprise ↑ → breakevens ↑ but also nominal-rate ↑; net = real-rate sign | Ambiguous ex-ante / minutes-days | 1970s-style vs real-rate-led regimes differ | headline vs core; energy pass-through | Post-CPI GC response sign vs *real* (not headline) surprise | BLS CPI schedule FACT (bls.gov, 2026-10-02); BEA PCE partial FACT (bea.gov, 2026-10-02, Oct-Dec dates); surprise/consensus data MISSING | Calendar FACT; response NOT_RUN |
| 5 | Risk aversion / geopolitical stress (Macro/event) | Stress → safe-haven bid | Positive intraday-to-weeks | Strongest in crisis; can reverse once rates respond | USD also bids in stress (offset); VIX co-jumps | Stress days where GC fails to rally vs USD-adjusted | VIX/GVZ not in corpus; NOT_RUN | POSTULATED, NOT_RUN |
| 6 | Central-bank demand (Fundamental) | Official-sector buying → structural bid, less rate-sensitive | Positive / months | Only in high-reserve-diversification regimes | monthly-reported, lagged, revised | CB-reported buying months with no price support | IMF IFS/COFER, WGC — official but lagged; NOT fetched | POSTULATED, NOT_RUN |
| 7 | ETF/fund flows (Positioning) | GLD-type creations → immediate gold purchase | Positive / days | Mirrors risk appetite; endogenous to price | flows are price-reactive (reverse causality) | Flow-predictive vs flow-lagging split | GLD shares/outstanding daily (official ETF pages) — NOT fetched | POSTULATED, NOT_RUN |
| 8 | CoT positioning (Positioning) | Money-manager net extreme → squeeze/crowding risk | Contrarian at extremes / weeks | Works in trending regimes, fails in crisis extension | CoT = Tue positions, Fri 15:30 ET release (≠ trade date) | Extremes with no reversal | CFTC CoT: weekly, Fri 15:30 ET, as-of prior Tuesday, not revised [FACT: cftc.gov, 2026-10-02]; series NOT fetched | Release rule FACT; use NOT_RUN |
| 9 | Term structure / carry (Term structure) | Contango ≈ full-carry financing; flat/backwardation = convenience/stress bid | Roll yield positive in contango for longs' *cost* | Widens with rates, compresses in stress | settlement-derived deep bars | — (measured) | own raw panel | OBSERVED (§3) |
| 10 | Roll-window microstructure (Microstructure) | Liquidity migrates before expiry → calendar spread noise around roll | Spread/execution effect | Always; amplified at month-end | vendor volume artifact (V-month thinness) | — (measured) | own raw panel | OBSERVED (§1, §3) |
| 11 | Related markets: SI, Treasuries, VIX, BTC, miners (Cross-asset) | Gold/silver ratio = risk beta within metals; miners = equity leverage | Correlative / days | Regime-dependent sign flips | common USD/rates driver | rolling beta instability | SI in raw (OBSERVED available); others NOT in corpus | Mechanism POSTULATED; SI data OBSERVED available |

## 3. Behavior (measured where legal)

All statistics: analysis/GC_descriptives.py → GC_descriptives.json, computed from the raw
GC_* files; returns are within-contract daily log returns (roll-date return belongs to the
OLD contract; no stitched jumps); thresholds use strictly-prior rolling windows; ex-post
labels are description-only. No PnL/performance metrics anywhere.

- **What window is actually measurable**: continuous per-date panel of 22 contracts spans
  2019-12→2026-10, but per-contract depth is settlement-derived (v=0, O=H=L=C) for most of
  history [OBSERVED: flat share 37–99% per contract, S6 reconciled]; real-volume bars are
  continuous on the executable chain only from **2025-01-15** → 2026-10-01 (424 return obs).
  The single-contract Dec-series (GCZ5 full life 2019-12→2025-11, GCZ6 2020-12→2026-10)
  give clean long-horizon *reference* stats without stitching, settlement-derived.
  [OBSERVED: `real_volume_chain_start`, `long_horizon_single_contract_refs`]
- **Caveat on the "front" chain**: because serial months 2025-11…2026-09 are missing from
  the raw set (§1), the constructed chain tracks a *deferred* contract for part of the
  window (e.g. 2024 tracks GCV5, the Oct-25 delivery, ~11 months out). All "chain" stats
  below therefore describe gold price behavior at a movable curve point (0–11 months out),
  not strictly the front month; the two are near-identical in level-vol terms here (GCZ5
  single-contract vol by year ≈ chain vol by year: 2024 14.32 vs 14.77%, 2025 20.39 vs
  20.53%) but roll/curve statements are the only front-precise ones. [OBSERVED]
- **Volatility (regime shift)**: annualized daily vol by year (chain, settlement-derived
  pre-2025): 2023 ~15.0% (n=20), 2024 14.8%, 2025 20.5%, 2026 (Jan–Sep) **30.7%**.
  Single-contract GCZ5 confirms 2020 20.6% → 2023 11.4% → 2025 20.4%; GCZ6 2026 30.6%.
  Rolling 21-session realized vol on the real-volume era: mean 23.9%, max **56.7%**,
  latest (2026-09-30) 20.7% annualized. Worst day −12.07% on **2026-01-30** (crash off the
  2026-01 spike top ~5,718–5,730 across contracts; GCZ6 ranged 5,729→5,280 intraday
  2026-01-29); best day +5.89% on 2026-02-03. [OBSERVED]
- **Distribution / day skew**: real-volume era n=424: mean +0.085%/day, σ=1.61%/day,
  q05/q50/q95 = −2.67/+0.16/+2.63%, positive days 54.5%; lag-1 return autocorr **−0.11**
  (mild daily mean-reversion), |r| lag-1 autocorr +0.11, lag-5 +0.12 (mild vol clustering).
  [OBSERVED]
- **Trend persistence**: share of days whose return sign matches the prior-50-session mean
  sign = 50.8% (real era, n=374); GCZ5 long series prior-200-session version = 51.8%
  (n=1,264). ≈ coin-flip: no strong daily trend persistence at these horizons.
  [OBSERVED, description-only]
- **Large-move frequency (strict past threshold)**: days with |r| above the 95th percentile
  of the *prior 126 sessions'* |r|: 16 of 298 evaluated (5.37%), clustered in
  2025-10/11, 2025-12/2026-01, 2026-02/03 and 2026-09-28 — i.e. vol comes in bursts.
  [OBSERVED, description-only]
- **Seasonality (description-only, tiny buckets)**: mean |r| by calendar month (real era):
  highest Oct 1.64% (n=22), Jan 1.39%, Apr 1.32%; lowest Jul 0.88%, Sep 0.89%, Dec 0.86%.
  Weekday: Mon 1.32% > Fri 1.22% > Tue–Thu 1.04–1.08%. n≈20–44 per bucket — NOT a signal.
  [OBSERVED]
- **Curve / term structure (settlement-derived, descriptive)**: near-below-far (contango)
  on **99.8–100%** of overlapping sessions for every pair measured; median 2-month spread
  ≈ −19 to −24 USD/oz (near minus far), 12-month ≈ −39 to −42; 2026-10-01 deferred-curve
  snapshot shows +15.2…+19.5 USD/oz per month out to Jan-2028 (~4.5%/yr carry).
  Backwardation essentially absent in this data. [OBSERVED; deep bars settlement-derived]
- **Roll-window behavior**: old-contract volume collapse + new-contract crossover 1–2
  sessions before the declared roll session (§1); roll-session adjacent-contract close gaps
  +27.5…+37.3 USD/oz across the SEVEN real-era cycle rolls completed in the snapshot
  (six reported originally + GCV6→GCZ6 2026-09-30 at +31.1 — audit m2 fix 2026-10-02;
  consistent with the contango level, i.e. gap ≈ 2 months × ~16 USD/oz/month — NOT an
  extra "roll penalty" signal). [OBSERVED, gap ≠ tradable cost]
- **Intraday session profile — US RTH only**: pooled hourly bars (22 contracts, 30-D
  windows ending at each contract's fetch/expiry, 4,001 bars, 211 sessions, labels 09:30
  stub + 10:00–16:00 ET): volume share peaks in the **10:00 ET hour (24.0%)**, then decays
  monotonically to 16:00 (3.9%); median bar range% declines 0.40% (10:00) → 0.09% (16:00).
  The 09:30 opening stub carries 13.9% of volume with 0.32% median range. [OBSERVED]
  **Asia/London/COMEX-open (18:00 ET) behavior: NOT_RUN** — useRTH=True files contain no
  overnight bars, so no statement about which *global* session leads price discovery can be
  measured from this corpus (owner-framework question, answer: NOT_RUN).
- **1-minute behavior: NOT_RUN** — 1-min files are 2-day snapshots per contract (900 bars
  active / 660 expired); unsuitable for any distributional statement.
- **Spread/cost observations**: daily BID/ASK closes (non-synchronous → NOT executable):
  front GCV6 1Y median 9 ticks ($0.9/oz) with last-20-session median **5 ticks ($50/contract)**
  — reconciles with S6_FRONT_SPREADS GC (5.0 ticks, $50, n=20); deferred GCX6 1Y median 42
  ticks collapsing to 5 once it became front; crossed days: 0 on GC except GCX7 (1 day).
  Commission: IBKR $0.85/side + exchange fee **NOT_FETCHED** (only ES 1.38 example exists);
  slippage NOT_RUN_NO_DECLARED_VALUE; margins (public broker pages, 2026-10-02): initial
  ~$24.6k, maintenance ~$22.4k/contract (NT) vs $24.2k (AMP) — broker-class, not CME SPAN
  official (CME blocked). [OBSERVED + FACT-secondary per costs/ artifacts]

## 4. Event calendar

Scheduled events relevant to GC, with UTC/ET timing. Release calendars are FACT (official
sources, access date 2026-10-02). Response measurement of GC to any of these: NOT_RUN
(prohibited/insufficient intraday depth; no surprise/consensus data in corpus).

| Event | 2026 remaining dates | Release time (exchange tz = America/New_York ET) | UTC | PIT properties | Source (access 2026-10-02) |
|---|---|---|---|---|---|
| FOMC decision | Oct 27–28; Dec 8–9 (2026 meetings: Jan 27-28, Mar 17-18, Apr 28-29, Jun 16-17, Jul 28-29, Sep 15-16, Oct 27-28, Dec 8-9; SEP at *) | Statement day-2; exact release time not stated on calendar page (conventionally 14:00 ET — NOT confirmed on page) | ~19:00 UTC (unconfirmed) | Minutes +3 weeks; SEP quarterly; no vintage revision of decision itself | federalreserve.gov/monetarypolicy/fomccalendars.htm |
| CPI (BLS) | Oct 14, Nov 10, Dec 10 (earlier 2026: Jan 13, Feb 13, Mar 11, Apr 10, May 12, Jun 10, Jul 14, Aug 12, Sep 11) | 08:30 ET | 12:30/13:30 UTC (DST) | Seasonally-adjusted series revised; first print is the tradeable vintage; reference month = prior month | bls.gov/schedule/news_release/cpi.htm |
| Employment Situation / NFP (BLS) | Oct 2, Nov 6, Dec 4 (2026: Jan 9, Feb 11, Mar 6, Apr 3, May 8, Jun 5, Jul 2, Aug 7, Sep 4) | 08:30 ET | 12:30/13:30 UTC | Payrolls revised twice after first print (vintage-sensitive); benchmark annual revision | bls.gov/schedule/news_release/empsit.htm |
| PCE (BEA, personal income & outlays) | Oct 29, Nov 25, Dec 23 | 08:30 ET | 12:30/13:30 UTC | Heavily revised (multiple vintages); Jan–Sep 2026 dates not on the fetched schedule page (NOT_FETCHED) | bea.gov/news/schedule |
| CFTC CoT (financial futures, incl. GC) | weekly, Fridays 15:30 ET | 15:30 ET | 19:30/20:30 UTC | Positions as-of PRIOR Tuesday; not revised; release ≠ position date; holiday shifts | cftc.gov/MarketReports/CommitmentsofTraders/index.htm (+ FAQ) |
| COMEX GC roll/expiry (contract events) | declared-roll sessions still ahead: 2026-10-30 (GCX6, Nov delivery), 2026-11-27 (GCZ6, Dec delivery), 2026-12-30 (GCF7, Jan-2027 delivery) — last session before each delivery month (GCV6's roll already occurred 2026-09-30); last-trade dates from S1 chain (GCV6 2026-10-28, GCX6 2026-11-25, GCZ6 2026-12-29) | 13:30 ET cessation on last-trade day | — | Listing calendar known years ahead (PIT-legal roll decisions) | OBSERVED: S1_IDENTITY.json chain + raw bars |
| Treasury auctions / yield "shocks" | NOT_RUN (no primary schedule fetched) | — | — | — | — |
| Geopolitical shocks | unscheduled — NOT_RUN by construction | — | — | — | — |

Effective vs available vs retrieved (general PIT rule for this dossier): exchange/official
release timestamps above are the *available* times; nothing has been *retrieved* into a PIT
store this cycle; any hypothesis using macro series must store vintage/first-release values
(FRED ALFRED or source vintages), else treat as unsuitable for strict PIT tests.

## 5. Hypotheses (3–5, ranked by testability × causal plausibility — NOT by PnL)

Reuse disclosure: corpus-1200 is outside this lane's read scope — idea-line/ID mapping
**NOT_RUN**. Where an idea mirrors a generic FX/macro pattern (H1/H2 USD-dependence), the
FX→futures transfer is flagged: futures differ by basis, roll (contango ~16 USD/oz/month
OBSERVED), tick costs, and margin — an FX finding never transfers as "already valid".

**H1 — Roll-timing microstructure (rank 1: fully measurable on data in hand).**
When the front GC contract approaches its declared roll session (last session before its
delivery month), liquidity migrates to the next listed contract 1–2 sessions earlier
[already OBSERVED, §1]. Hypothesis: a roll rule switching at the *volume-crossover* session
instead of the calendar session reduces calendar-spread crossing costs and avoids the
post-crossover thin old-contract book, with no material change in exposure.
- PIT condition: within-session cumulative relative volume old vs next (strict same-session
  past data), or prior-session daily volumes.
- Predicted effect: lower effective spread paid at switch; exposure drift ≈ 0 (contracts
  co-move; gap ≈ contango).
- Mechanism: liquidity providers widen the dying contract's book; takers pay the calendar
  spread plus wide book.
- Strongest regime: high-vol month-ends (2026-01-30 roll inside the −12% crash week);
  weakest: quiet months where both books stay tight.
- Rules: entry/exit = the roll switch itself; no TP/SL (not a directional trade);
  holding = position lifetime; direction = none (execution choice); universe = GC front→next
  pair; roll = this IS the roll rule; sizing = 1 contract baseline; cost model = observed
  bid/ask medians (front 5 ticks = $50; deferred months wide — PARAM-GAP for serial months
  not in raw); invalidation = if old-contract book (spread/volume) does not deteriorate
  pre-roll in ≥ half of rolls; counter-hypothesis = calendar rule already equals volume
  rule (it is 1–2 sessions late — OBSERVED against); failure = serial-contract volumes are
  vendor-artifact-thin (V-month caveat §1) making crossover undetectable; data floor =
  daily BID/ASK + volume per contract (HAVE, 2025-08→2026-10), serial months MISSING
  (6 contracts), 1-min roll-window detail NOT_RUN; budget = re-fetch 6 serial contracts,
  minutes of API time, $0.

**H2 — Post-CPI real-rate sign vs headline sign (rank 2: mechanism-falsifiable, data-gated).**
When CPI prints at 08:30 ET, GC's same-day move should follow the *real-rate* implication
(breakeven path vs nominal path), not the headline inflation sign: an upside surprise that
raises breakevens more than nominals (rates “capped”) can be GC-positive despite hot
headline. [Framework §15 hypothesis 3.]
- PIT condition: CPI first print + same-morning nominal yield & breakeven moves (all
  timestamped 08:30 ET releases).
- Predicted move: sign(r_GC, 1d) ≈ −sign(Δreal-yield proxy, 08:30→close); horizon minutes→1d.
- Mechanism: gold = duration-like zero-coupon real asset.
- Strongest regime: tight-Fed/real-rate-led (2026-type 30% vol regime); weakest: crisis
  bid weeks (safe-haven overrides, e.g. 2026-01).
- Rules: entry 08:30:05 ET (PARAM-GAP: no M1 depth before ~2025-12 — event-entry realism
  NOT_RUN until deeper M1); exit same close; no TP/SL in test-0 (measurement first);
  direction conditional; universe = GC front; roll = declared rule (serials caveat);
  sizing = 1; cost = spread 5 ticks + commission (exchange fee NOT_FETCHED);
  invalidation = real-rate-sign model classifies ≤ coin-flip of GC same-day signs over ≥24
  events; counter-hypothesis = headline-sign traders dominate the first minutes;
  failure = surprise/consensus PIT data unavailable (consensus is vendor-licensed);
  data floor: timestamped CPI + TIPS yields + consensus (MISSING), M1 around 08:30
  (partial ~10 months); budget: consensus history is a paid decision (owner) —PARAM-GAP.

**H3 — Contango-curve stress signal (rank 3: measured structure, mechanism forward).**
GC's near-vs-far spread is contango ~100% of days (OBSERVED §3). Hypothesis: compression of
the 2-month spread toward/below ~half its trailing median (strict past window) precedes
stress episodes, because spot-adjacent urgency bid (physical/EFP squeeze) is the only force
that flattens a full-carry curve. Predicted: GC outperforms forwards over days-weeks after
compression; strongest in high-vol regimes (2026), weakest when rates simply fall (carry
compresses mechanically with no stress).
- Entry: spread < rolling-median(126 sessions)×0.5 (strict past); exit: spread back above
  median, or 10 sessions; direction: long front/short next (calendar spread — description
  first, no PnL yet); universe = GC 1st/2nd cycle months; roll = n/a (spread position);
  sizing 1:1; cost = 2 legs × spread; invalidation = compression days with no subsequent
  front outperformance; counter = compression is pure rate move (control: Δ2y yield);
  failure = settlement-derived deep bars misstate curve before 2025 (real-volume curve
  only 2025-01→2026-10, ~40 weekly obs); data floor: HAVE raw curve (settlement-derived),
  NEED real-volume curve ≥ 2y; budget: vendor data decision (owner).

**H4 — GC/SI ratio regime behavior (rank 4).** Framework §15 hypothesis 4. GC/SI ratio
(both COMEX, same sessions) mean-reverts differently across risk regimes: risk-on → SI
outperforms (ratio falls); stress → ratio rises. Testable on daily closes already in raw
(SI_ files, 2020-12→2026-10 settlement-derived + 2025+ real-volume). Entry/exit/holding:
PARAM-GAP until regime tagging rule is fixed a priori (vol quantile + trend sign, strict
past windows) — deliberately not specified here to avoid ex-post tuning; direction
conditional; universe GC/SI fronts; roll = declared (serials caveat both symbols);
invalidation = regime-conditional ratio behavior is unstable year-by-year; counter =
ratio driven by SI's idiosyncratic industrial demand, not risk appetite; data floor: HAVE
daily closes; budget $0.

**H5 — Real-yield level driver (rank 5: most causal-plausible, least testable now).**
Framework §15 hypothesis 1: real-yield shocks dominate GC direction outside acute crisis.
Cannot be specified as a trade rule yet: no PIT yield/expectation series in corpus
(PARAM-GAP). Required: 10y TIPS yield vintages + a crisis dummy defined ex-ante. Everything
directional/mechanical per driver-map row 1; explicitly NOT_RUN beyond mechanism.

## 6. Missing data table

| Need | Have | Source (primary first) | Period | Schema | PIT properties | License / cost | Blocker | Next action |
|---|---|---|---|---|---|---|---|---|
| Real-volume daily per-contract ≥ 24 months incl. SERIAL months (GCX5, GCF6, GCH6, GCK6, GCN6, GCU6 missing entirely) | 2025-01-15→2026-10-01 real-volume on cycle months only | current IB entitlement (or Databento/CME DataMine — owner decision) | 2019→present | per-contract OHLCV daily | timestamps ET, already PIT | existing entitlement $0 / vendor $ owner decision | expired-secdef ~1y wall + serials never fetched | re-fetch 6 serial contracts now (resolvable window); vendor purchase is owner decision |
| 10y TIPS / real-yield + breakeven, vintage-clean | none | treasury.gov, FRED ALFRED vintages | 2019→ | daily yield + release/vintage stamps | first-release values required | free / FRED terms | not fetched (out of prep scope) | fetch + store vintages in a PIT store before H2/H5 |
| CPI/NFP/PCE surprise (consensus vs first print) | release CALENDAR only (FACT) | BLS/BEA official releases + consensus vendor | 2019→ | event time, consensus, actual, prior, revision flags | first print is the vintage | consensus is licensed ($) | no consensus source; owner purchase decision | decide budget for consensus history; until then H2 stays PARAM-GAP |
| Intraday M1/H1 depth (multi-year, full 23h session incl. Asia/London) | 30-D RTH-only hourly, 2-D M1 per contract | vendor (Databento glbx.mdxp3 style) | 2019→ | 1-min OHLCV full session | timestamps UTC/ET | $ owner decision | entitlement vintage wall ~10 months | owner vendor decision (DATA-PIT-ACQUISITION-PREP lane spec) |
| CFTC CoT disaggregated (money managers vs swap dealers) for GC | none (release rule known, FACT) | cftc.gov legacy futures-only + TFF | 2019→ | weekly Tue positions, Fri 15:30 ET release | not revised; release≠position date | free | not fetched | fetch once hypotheses H2–H5 enter measurement |
| Open interest per contract (roll by OI, capacity) | none in raw | vendor/CME | 2019→ | daily OI per contract | T+1 publication | vendor terms | not in entitlement snapshot | add to vendor data spec |

Priority = top-3 causal drivers (real yields, macro surprises, full-session intraday) +
the two $0 fixes already possible under the current entitlement (serial contracts re-fetch;
CoT fetch). This dossier does NOT condition on the full wishlist.

## 7. Framework coverage

Master framework §1 (10 questions):

1. Underlying economic exposure → 100 oz refined gold, USD/oz, monetary/duration-like real
   asset, physically delivered. [FACT-secondary + OBSERVED S1; §1]
2. Natural hedgers/speculators/MMs/arbitrageurs → miners/jewelers/bullion banks; macro
   funds/CTAs/ETFs; MMs & EFP/carry arbitrage vs London spot. [POSTULATED]
3. Exchange & hours → COMEX (CME Group), Globex 18:00→17:00 ET, RTH 09:30–17:00 ET,
   DST verified in bars. [OBSERVED S1/S9; §1]
4. Size/tick/currency/margin/settlement → 100 oz; $0.10/oz = $10/tick; USD; margin ~$22–24k
   maintenance/initial (broker-class public, CME SPAN blocked); physical delivery.
   [OBSERVED + FACT-secondary; §1, §3]
5. Listed months & normally liquid expiries → near-monthly (3 consecutive + cycle months;
   Jun/Dec out 6y in S1 chain); liquid = nearest GJMQVZ cycle month. [OBSERVED chain;
   serial thinness POSTULATED + volume-caveat OBSERVED]
6. When does liquidity migrate → volume crossover 1–2 sessions before declared roll session
   (5/6 real-era rolls; 1 at roll). [OBSERVED; §1]
7. Dominant price behavior → macro expectations (real rates/USD) + stress premium; carry
   contango ~100% of days; NOT storage/commodity-cycle driven. [POSTULATED for macro
   dominance; OBSERVED for curve]
8. Which session matters → measurable only for US RTH (10:00 ET hour = 24% of RTH volume,
   morning-heavy). Asia/London/COMEX-open: NOT_RUN (no overnight bars). [OBSERVED/NOT_RUN;
   §3]
9. "Tradeable" contract per timestamp (PIT volume/OI) → declared calendar rule executable
   with serial caveat; OI unavailable; volume rule measurable but only 1–2 sessions earlier.
   [OBSERVED; §1]
10. Vendor symbols ↔ expiries, reproducible continuous reconstruction → localSymbol
    G?{monthcode}{yeardigit} (GCV6=Oct-2026 …), conId per contract in S1/raw filenames; raw
    individual contracts stored; roll tables derivable (gaps measured); back-adjustment
    NOT performed (description only). [OBSERVED]

GC framework's own checklist (foundation/market-structure/§14 questions):

- What the contract represents / fair value vs spot → duration-like claim on gold; fair
  value = spot × carry (contango ~4.5%/yr OBSERVED on curve); EFP vs London NOT_RUN.
  [POSTULATED + OBSERVED curve]
- Who must trade / who speculates → §1 participants [POSTULATED].
- Liquid expiries & migration timing → answered [OBSERVED; Q5/Q6].
- Settlement/delivery distortions of the front → physical delivery + 13:30 ET cessation;
  front distortion NOT measured (no expiry-week microstructure) [FACT-secondary; NOT_RUN].
- Session information/liquidity → RTH only measured; global session question NOT_RUN.
  [OBSERVED/NOT_RUN]
- Minimum data to reconstruct a PIT series → per-contract daily TRADES+BID/ASK (HAVE,
  22-months real-volume on cycle months) + missing serials list (§6) [OBSERVED].
- Volume by session/expiry, roll speed, spread widening (overnight/releases/expiry),
  opening/settlement effects, contract-selection-rule stability, back-adjustment impact on
  trend → volume-by-expiry OBSERVED (with vendor-scale caveat); roll speed OBSERVED
  (1–2 sessions); spread near expiry NOT_RUN (no synchronized quotes); opening/settlement
  intraday effects NOT_RUN; selection-rule comparison NOT_RUN (OI missing); back-adjustment
  effect NOT_RUN (no adjusted series built — description-only mandate). [OBSERVED/NOT_RUN]
- §14 regime questions (gold vs nominal/real/USD/stress; safe-haven vs real-yield;
  CB-demand proxy; session leadership) → all POSTULATED/NOT_RUN (no external PIT series
  in corpus this cycle).

---

### Defects / caveats register (this lane)

1. [OBSERVED] Serial months 2025-11…2026-09 absent from raw → declared roll rule not
   executable for that span; all chain stats use a cycle-skip approximation (disclosed).
2. [OBSERVED] Vendor volume thin 1–2 orders for GCV5/GCV6 (front V-windows) and all
   deferred months vs G/J/M/Q/Z contracts; hourly-vs-daily consistency checked on one day
   (GCV6 2026-08-20 equal); do not use vendor volume as absolute liquidity.
3. [OBSERVED] Deep daily bars are settlement-derived (37–99% flat per contract) — usable
   as reference/curve only, never fill prices.
4. [NOT_RUN] CME official numeric spec/fee/SPAN tables not retrievable (direct WebFetch
   times out; web-reader fallback renders the page but the spec/fee tables are JS-driven
   and empty — re-tested 2026-10-02) — specs rest on broker secdef (OBSERVED) + vendor
   mirrors (secondary) + CME page marketing-level facts (physical delivery, ~24h access).
5. [NOT_RUN] Intraday = RTH-only 30-D windows; 1-min = 2-D snapshots; no overnight data.
6. [OBSERVED] GCV5 raw bars end 2025-09-30 although lastTradeDate is 2025-10-29 — dataset
   ends one month before the contract's legal last-trade day (vendor snapshot boundary,
   aligned with the declared roll date).

---

### CoT revision-policy verification note (added 2026-10-02, round co-owner-review-fix-1, lane HANDOFF-RESEARCH)

The CoT "not revised" wording in §2 driver-map row 8, §4 CoT calendar row and §6 missing-data CoT row (this dossier) was re-verified against primary CFTC
documentation on 2026-10-02:

1. Release rule CONFIRMED (FACT stands): "The COT Report is generally
   published each Friday at 3:30 pm Eastern Time (US)"; the reports
   "provide a breakdown of each Tuesday's open interest"; "Generally, the
   data in the COT reports is from Tuesday and released Friday."
   https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm
   (accessed 2026-10-02).
2. No-revision property CONFIRMED for the AS-PUBLISHED weekly reports —
   the FACT stands with scope = as-published weekly files. CFTC FAQ answer,
   verbatim: "No, historical data is not updated once published."
   (same URL, accessed 2026-10-02).
3. SCOPE QUALIFICATION for the TFF supplement: TFF HISTORICAL compressed
   files are NOT vintage-stable — "the CFTC does not maintain a history of
   large-trader classifications, so, recent classifications had to be used
   to classify the historical positions of each reportable trader" (Form 40
   refreshed "every 2 years or more often"; classification shifts restated
   into history). Traders in Financial Futures Explanatory Notes,
   https://www.cftc.gov/sites/default/files/idc/groups/public/@commitmentsoftraders/documents/file/tfmexplanatorynotes.pdf
   (accessed 2026-10-02). Strict PIT use must pin release-dated weekly
   files, never the current compressed history.

Verdict: no class downgrade for the release rule or the as-published
no-revision claim; the blanket "not revised" is scope-qualified wherever
"cftc.gov legacy + TFF" is cited as a future source (§6 here). Shared note in
RESEARCH_MATRIX.md §CoT.
