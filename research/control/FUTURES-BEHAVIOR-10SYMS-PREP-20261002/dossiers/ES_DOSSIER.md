# ES DOSSIER — E-mini S&P 500 Futures

- Symbol: **ES** (CME, trading class ES; Globex code ES)
- Exchange: **CME** (CME Group), Globex electronic
- Generated (UTC): 2026-10-02
- Author lane: **SYMBOL-DOSSIER-ES** (task FUTURES-BEHAVIOR-10SYMS-PREP-20261002)
- Inputs:
  - `owner_framework/ES_RESEARCH_FRAMEWORK.md` sha256
    `92e9d51087492d55270080cb442c2b1cd3e5e9abf58b4b1dc90aee71c41e2acf`
    (from `owner_framework/SHA256SUMS.txt`)
  - `owner_framework/00_MASTER_FRAMEWORK.md` sha256
    `a75571b8017b13b5ff6552755d1334b03db640ebc26a6b4c9ad4323ca16d3c74`
  - `research/control/FUTURES-DATA-10SYMS-V1/FINAL_REPORT.md` (+ HANDOFF.json,
    S9_INDEPENDENT_VERIFY.md, S1_IDENTITY.json, S6_FRONT_SPREADS.json,
    costs/IBKR_futures_commissions_2026-10-02.json,
    costs/SPECS_MARGINS_PUBLIC_2026-10-02.md) — untracked snapshot 2026-10-02, read-only
  - Raw data (read-only): `~/.my-quantitative-data/futures-10syms-v1/raw/ES_*`
    (65 files: 10 contracts × TRADES daily-6Y / hourly-30D / 1min-2D / BID+ASK
    daily-1Y, plus front/next/expired 3D probes). All bars `useRTH=true`
    (US regular trading hours) — see §1/§3 for consequences.
  - Own analysis: `analysis/ES_analysis.py` → `analysis/ES_stats.json`
    (every OBSERVED number below is reproducible from these).
- Claims taxonomy used throughout: **FACT** (primary source + URL + access
  date), **OBSERVED** (computed from raw data; script + window), **POSTULATED**
  (mechanism reasoning, unmeasured), **NOT_RUN** (not measured — never inferred
  PASS). This dossier is PREP: 0 PnL, 0 scored runs, 0 parameter selection.

---

## 1. Mechanics

- **Underlying exposure** [FACT]: $50 × S&P 500 Index; cash-settled
  ("Financially settled"), no delivery. NinjaTrader spec mirror
  https://www.ninjatrader.com/futures/futures-contracts/equity-index/e-mini-s-p-500/
  (accessed 2026-10-02 via costs/SPECS_MARGINS_PUBLIC_2026-10-02.md);
  corroborated TradingCharts https://futures.tradingcharts.com/chart/ES/ and CME
  pages via search snippet (CME direct fetch blocked this session — see below).
- **Economic role / participants** [POSTULATED, standard index-futures
  structure; participant identity itself is NOT_RUN on our data]: asset
  managers hedging/neutralizing equity beta, CTA/macro funds, dealers hedging
  options books, index arbitrageurs holding futures-vs-cash basis, HFT market
  makers. Positioning composition per participant type: NOT_RUN (no CoT pull in
  this session; CoT covers reportable categories only — see §2/§4).
- **Tick / multiplier / quote convention** [FACT, machine-verified]:
  multiplier "50", minTick 0.25 (=$12.50/tick), currency USD, on **every**
  resolved ES contract in S1_IDENTITY.json (uniform across all resolved
  contracts; S9 caveat: multiplier/minTick not re-derivable from raw bars —
  identity authority is S1). Quote = index points (no 6J-style inversion risk).
- **Sessions and DST** [FACT, machine-verified from S1 `tradingHours` /
  `liquidHours` for ESZ6, fetched 2026-10-02]: Globex 17:00 CT → 16:00 CT next
  day (23h, 60-min maintenance break 16:00–17:00 CT; Sunday open 17:00 CT);
  RTH ("liquid") session 08:30–16:00 CT. Timezone `US/Central`; S9 verified
  raw intraday offsets are DST-correct at each bar's own date (-05:00 CDT /
  -06:00 CST). CME states Globex hours as "Sunday 6:00 p.m. – Friday 5:00 p.m.
  ET with a daily 60-minute break" (cmegroup.com ES pages via search snippet,
  accessed 2026-10-02; CME direct fetch HTTP-403/timeout — consistent with
  FUTURES-DATA-10SYMS-V1 `cme_check/`). **All raw daily/hourly/1-min bars in
  this snapshot are `useRTH=true`** [OBSERVED, raw metadata]: daily bars are
  RTH-day bars (open 08:30 CT, close 16:00 CT); the Globex overnight session is
  NOT present in any intraday file — overnight-session behavior is therefore
  NOT_RUN on this snapshot (only the overnight→RTH-open *gap* is measurable at
  daily resolution; §3).
- **Holidays** [OBSERVED, S1 machine windows]: `20261003:CLOSED` (Sat) and
  Sunday shown CLOSED until 17:00 CT open; **June expiry shifted off the 3rd
  Friday when Juneteenth observance interferes** [OBSERVED, computed from S1
  `lastTradeDateOrContractMonth` across 26 resolved contracts]: all H/M/U/Z
  last-trade dates are 3rd Fridays **except** ESM6 2026-06-18 (Fri 2026-06-19
  = Juneteenth) and ESM7 2027-06-17 (Juneteenth observed Fri 2026→2027-06-18).
  A naive "3rd Friday" roll/expiry rule is wrong for June [OBSERVED].
- **Delivery / first-notice / expiry / price limits**:
  - Cash-settled; no delivery/first-notice mechanics [FACT, NT/TradingCharts].
  - Final trading until 08:30 CT on expiry morning [FACT: S1 `lastTradeTime`
    "08:30:00" on every contract carrying it; CME E-mini FAQ via search
    snippet, accessed 2026-10-02].
  - Price limits: 7% / 13% / 20% circuit levels coordinated with securities
    market-wide circuit breakers (7%/13% halts; 20% closes for the session)
    [FACT, secondary channel — cmegroup.com "S&P 500 Price Limits FAQ" and
    "US-Based Equity Index Futures Price Limits FAQ" via search snippets,
    accessed 2026-10-02; CME direct fetch blocked; exact Rule 582 text
    NOT_RUN-unverified].
- **Listed months & liquid maturities** [FACT + OBSERVED]: quarterly H/M/U/Z,
  "nine quarters out and three additional December contracts" (NT spec);
  S1 active chain resolves ESZ6 (2026-12) through ESH1 (2031-03) with extra
  Decembers (ESZ9/ESZ0/ESZ1) — matches the 9Q+3Dec listing rule [OBSERVED,
  S1]. Liquid maturity: **front quarterly only** — deferred quarterlies print
  at most 2k–13k contracts/RTH-day (median ≤5) vs front ~1.0–1.3M
  [OBSERVED, ES_stats.json `contract_panel`].
- **Liquidity migration front→next** [OBSERVED, `ES_stats.json`
  `liquidity_migration` + `first_front_scale_date`]: in all 5 roll cycles
  2025-06→2026-09 the *next* quarterly first reaches front-scale volume
  (≥100k/RTH-day; 500k/1M within 1–2 more sessions) exactly in **roll week**,
  4–5 sessions before the old contract's expiry: 2025-09-15, 2025-12-12,
  2026-03-13, 2026-06-11, 2026-09-14. At the data lane's declared roll date
  (last session before day-1 of expiry month) the old front still carried
  0.98–1.34M contracts/day (one 300k half-session) while the next contract had
  ~0.5–2k — i.e., the declared rule rolls ~2 weeks **before** the market's
  liquidity migration, and the declared-rule "front" is a thin deferred
  contract for ~8–9 sessions each quarter (thin windows: 2025-09-02..12,
  2025-12-01..11, 2026-03-02..12, 2026-06-01..10, 2026-09-01..11) [OBSERVED].
  The exact old-vs-new volume **crossover is NOT observable** in this dataset
  because each expired contract's raw file ends at its declared roll date
  (fetch `endDateTime` = day-1 of expiry month) [OBSERVED, file windows].
- **PIT contract selection + roll rule (baseline + alternatives)**:
  - Baseline (data lane declared, used by engine unless changed): hold until
    last session before day-1 of expiry month; roll to next listed quarterly
    at that close; no back-adjustment; listing calendar is published years
    ahead so the decision is PIT-legal [FACT, FINAL_REPORT §Roll rule].
  - **Roll cost / gap** [OBSERVED, `declared_rule_rolls`]: adjacent-contract
    close gaps at the 5 declared rolls were **positive every time**:
    +55.75, +58.75, +52.5, +61.75, +67.75 pts (≈0.76–0.86% of level per
    quarter ≈ ~3.3%/yr; $2,625–$3,388/contract). Sign consistent with
    cost-of-carry contango (short rates > S&P dividend yield) [POSTULATED for
    the mechanism; the gap magnitudes themselves are OBSERVED]. An
    unadjusted continuous series therefore embeds ~+0.8%/quarter artificial
    jumps at roll dates — back-adjustment is mandatory for any level/trend
    work (construction decision, not alpha) [POSTULATED→engine spec].
  - Alternatives to baseline (for engine A/B): (a) volume roll (roll when
    next-quarterly daily volume ≥ trailing fraction of front volume — exact
    crossover unmeasurable in this snapshot, NOT_RUN); (b) calendar roll at
    T-5 sessions before 3rd-Friday expiry ("roll week", matches all 5 OBSERVED
    ramp dates; note June Juneteenth shift); (c) OI roll — NOT_RUN (raw files
    carry no open-interest field).
- **Identity cross-check** [FACT/OBSERVED]: 10 ES conIds in raw set match S1
  identity on conId/localSymbol/expiry (S9 Check 2 PASS; front ESZ6 515416632,
  S1 mult 50, minTick 0.25). Raw `expiry_month` field carries full
  lastTradeDate (e.g. ESZ6 → 20261218) [OBSERVED].

## 2. Causal driver map

Master-framework buckets relevant to ES: Macro, Cross-asset, Positioning,
Term structure, Microstructure, Event-driven. (Fundamental/physical bucket is
N/A for a cash-settled equity index future except via earnings/dividends —
covered under Macro/growth.)

| # | Driver | Source → mechanism | Predicted sign / horizon | Regime dependency | Confounders | Falsification test | PIT data source (primary, access date) | Evidence class |
|---|--------|-------------------|--------------------------|-------------------|-------------|--------------------|----------------------------------------|----------------|
| 1 | Fed policy / real+nominal rates (FOMC path) | Fed communications → discount-rate & risk-premium channel → equity beta repricing | Hawkish surprise → down; easing → up; horizon minutes–days | Strongest in tight/vol regimes; weakest mid-cycle drift | Growth news released same window; OPEC-style supply shocks | Event-window ES move vs surprise-measured rate repricing (e.g., 2y yield change) on FOMC days, flat otherwise | FOMC calendar + statements: federalreserve.gov (2026-10-02); rate repricing: CME/Treasury mkt data — NOT in repo | Calendar FACT; effect NOT_RUN |
| 2 | Inflation surprises (CPI, PCE) | CPI ≫ consensus → higher implied path → discount-rate channel dominates (recent regime) vs inflation-is-growth older regime | Regime-dependent sign; minutes | Sign flipped historically across Fed regimes | Growth connotation of same print; oil shocks | CPI-day ES return conditional on signed CPI surprise vs non-CPI days | Release schedule BLS https://www.bls.gov/schedule/news_release/cpi.htm (2026-10-02) FACT; surprise data NOT in repo (vendor consensus) | Calendar FACT; effect NOT_RUN |
| 3 | Labor market (NFP/Employment Situation) | Payroll/unemployment surprise → growth-vs-rates tension → two-sided | Surprise-dependent; minutes–hours | Bad-news-is-bad-news vs bad-news-is-good regime flip | Benchmark revisions; simultaneous releases (8:30 ET block) | NFP-day conditional returns split by surprise sign across regimes | Schedule BLS https://www.bls.gov/schedule/news_release/empsit.htm (2026-10-02) FACT; actuals+consensus NOT in repo | Calendar FACT; effect NOT_RUN |
| 4 | Growth/earnings expectations (ISM, GDP, earnings) | Macro data → earnings-path expectations → beta | Pro-growth → up; days | Cycle-dependent | Inflation composition | ISM/GDP-day conditional returns vs matched non-event days | ISM/GDP schedules NOT fetched this session (NOT_RUN calendar for these two) | NOT_RUN |
| 5 | Volatility regime (VIX/VX, dealer hedging) | Dealer gamma/vega inventory → intraday suppression/amplification of moves; vol clustering → trend/mr regime switch | VIX level predicts ES vol (not sign); horizon days–weeks | Core regime variable itself | Vol index construction; VX–ES basis | Rolling correlation of VIX level vs forward ES |ret| — data NOT in repo (no VIX/VX file) | POSTULATED (mechanism); measurement NOT_RUN |
| 6 | USD / global liquidity (DXY, 6E) | Dollar strength → multinational earnings + foreign flows | Strong USD → mild ES headwind; days | Global-risk regimes | Commodity/oil co-moves | Rolling ES–DXY beta sign stability — DXY data NOT in repo (6E raw exists as cross-check) | 6E raw in snapshot; DXY NOT in repo | Cross-asset descriptives NOT_RUN this session |
| 7 | Positioning (CFTC CoT, OI) | Crowded net length → squeeze/convexity risk on shocks | Extreme positioning → larger adverse moves on surprise; weekly horizon | Crisis vs normal | CoT aggregates reportables only; release ≠ position date (see §4) | CoT-extreme weeks vs subsequent ES vol/returns | Release schedule cftc.gov https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm (2026-10-02) FACT; historical CoT values NOT pulled this session | Calendar FACT; effect NOT_RUN |
| 8 | Term structure / carry (calendar spread, roll gap) | Futures fair value = spot + (rates − divs)×T; spread absorbs rate/div expectations | Roll gap ≈ carry; sign positive while rates > div yield; per-quarter | Flips when div yield > rates | Dividend-cycle seasonality (Q1 heavy) | Roll-gap sign/level vs (SOFR-like rate − S&P div yield) each quarter; 5/5 gaps measured positive 2025-26 [OBSERVED] | Rates/divs NOT in repo; gaps measured from raw | Gaps OBSERVED; driver link POSTULATED |
| 9 | Microstructure: roll-window liquidity | Declared-rule roll lands on thin deferred book ~2 weeks before market migration (§1) | Execution-cost spike + sparse prints in thin windows; quarterly | Any; mechanical | Holiday half-sessions (e.g. 2025-11-28 300k) | Compare per-trade cost proxies / flatness inside vs outside thin windows | Raw files (measured) + future BBO depth (NOT in repo) | OBSERVED (volume side); cost side NOT_RUN |
| 10 | Index/options flows (OpEx, rebalance) | Quarterly OpEx (3rd Friday) + dealer gamma unwind → pinning/vol around expiry; index rebalance flows Q1/Q4 | Local vol/flow anomalies; expiry-day horizon | High-dealer-inventory regimes | Overlaps roll week | Expiry-week vs non-expiry-week |ret|/volume profile — needs intraday depth | OpEx dates derivable from S1 lastTradeDate [FACT]; flow data NOT in repo | Calendar FACT; effect NOT_RUN |
| 11 | Overnight info transfer (Asia/Europe → US open) | Globex accumulates foreign-session news → RTH open gap; partial reversion or continuation | Gap ≈ 60%+ of daily variance (§3); sign conditional | Vol regimes; crisis discontinuities | Daily open = RTH open only (no true 24h marks in data) | Gap-vs-day decomposition across vol regimes (needs ≥2y front-scale days for power) | Raw daily (measured, §3) | OBSERVED (descriptive); hypothesis NOT_RUN |

## 3. Behavior (measured where legal)

All computed by `analysis/ES_analysis.py` → `analysis/ES_stats.json` from raw
per-contract daily TRADES (RTH bars, useRTH=true), declared-rule unadjusted
front chain, thresholds only via strict past/trailing windows. Full sample for
chain stats: 2021-06-07→2026-10-01; **front-scale era** (front daily volume
≥100k, robustness: 500k gives −7 days, 1M −57 days of the same era) defined
descriptively: 2025-06-13→2026-10-01, 284 days.

- **Session/volume behavior**:
  - Front quarterly median RTH-day volume 1,091,761 contracts; ≥1M on 185/284
    days; ≥500k on 277/284 [OBSERVED, front-scale era].
  - RTH hourly volume profile (front ESZ6, 2026-08-20→2026-10-01, 30 days,
    RTH-only bars): 08:00-hour 10.5%, 09:00 18.4%, 14:00 19.7% (largest),
    15:00 half-hour 4.2% — U-shape with heavy PM (MOC-flow) tilt; first+last
    full hours ≈ 30% of RTH volume [OBSERVED, 30-day window only — NOT a
    structural constant].
  - Overnight Globex session: NOT_RUN (useRTH=true files; overnight data not
    in snapshot).
  - Deferred contracts: median ≤5 contracts/day, max 13k — never tradable at
    size [OBSERVED, panel].
- **Volatility behavior**:
  - Front-scale era daily simple returns: n=284 (roll-boundary returns
    excluded), mean +9.0bp/day, std 0.77%, min −2.71%, max +2.86%, skew −0.07,
    q05..q95 = −1.24%..+1.40%; annualized-vol descriptor 12.2% [OBSERVED].
    Single-regime caveat: this window is one persistent rally (~+27% level
    move) — no crisis regime in sample.
  - Full unadjusted chain 2021-06→2026-10 (mostly settlement-derived marks):
    std 1.03%/day, min −5.98%, max +9.45% (max = 2025-04-09-type reversal
    cluster), roll-boundary-inclusive vs exclusive nearly identical (1.0345%
    vs 1.0359%) [OBSERVED, settlement-derived caveat per FINAL_REPORT].
  - Rolling 63-day vol: min 0.52%, median 0.84%, max 2.04% (daily units) —
    4× vol range across the sample [OBSERVED, full chain].
  - |ret| lag-1 autocorr: 0.152 full chain (settlement-mark era included) vs
    **0.002 front-scale era** — daily vol clustering is weak in the recent
    284-day regime [OBSERVED; short-window caveat].
- **Trend behavior**: descriptive only — front-scale era mean +9bp/day with
  positive skew≈0; no trend/mr test run (would be rule evaluation — NOT_RUN by
  classification of this task).
- **Event behavior**: macro-release-day conditional behavior NOT_RUN (requires
  event-day alignment + intraday depth or at minimum multi-year daily sample;
  also no surprise/consensus dataset in repo).
- **Curve behavior**: all 5 observed roll gaps positive (+52.5..+67.75 pts ≈
  0.76–0.86%/quarter) [OBSERVED]; deferred-quarterly quotes exist but are
  stale/rotten (front-only BID/ASK filter needed; see spread note) — calendar
  spread behavior beyond roll dates NOT_RUN.
- **Seasonality (descriptive, full chain incl. settlement-derived era)**:
  - By month (mean daily ret / daily vol): all months |mean| ≤ 18bp; Sep the
    only negative-mean month (−9bp); Apr the highest-vol month (1.66%/day vs
    0.82–1.23% others — April-2022/2024/2025 shock cluster); n≈96–132/month.
  - By weekday: Mon vol 0.91% vs Wed–Fri 1.06–1.11%; means +12bp (Mon) …
    −2bp (Thu) [OBSERVED, whole-chain caveat — NOT a seasonal-alpha claim].
- **Overnight→RTH-open gap** (RTH open vs prior RTH close; normalized by
  trailing-20d mean |ret| ending prior day, strict past window):
  - Front-scale era (n=284): mean +9bp, std 0.48%, q05..q95 −0.72%..+0.82%,
    max +2.60%/min −1.48% — gap std is ~63% of full-day return std, i.e., a
    majority share of daily variance arrives at/through the overnight→open
    transfer [OBSERVED, 284-day window].
  - Whole chain (n=1336, settlement-era inflates): std 0.92%; |gap| ≥ 2×
    trailing-20d mean|ret| on 10.25% of days [OBSERVED].
- **Spread/cost observables** (published ≠ measured user costs):
  - Front close-proxy BID/ASK spread (declared-rule front days, n=284):
    median 1.0 tick = $12.50, p90 2.0 ticks = $25.00, 0 crossed days;
    whole 513-day front-chain sample median 2 ticks / p90 $2,512 (deferred
    quote-rot visible when front filter relaxed) [OBSERVED, close-to-close
    proxy — not an executable spread; S6 20-day median $12.50 concordant].
  - Commission [FACT, document-class]: IBKR $0.85/side + exchange + reg;
    official worked example ES all-in **$2.24/side** (IBKR 0.85 + exchange
    1.38 + clearing 0.00 + reg 0.00–0.01), fetched 2026-10-02
    (costs/IBKR_futures_commissions_2026-10-02.json). Exchange fee per CME
    schedule: NOT_FETCHED (CME blocked). Slippage: NOT_RUN_NO_DECLARED_VALUE.
  - Margin [FACT, broker-class public; CME SPAN blocked]: NinjaTrader
    maintenance $26,028.77 / initial $28,631.65 (as of 2026-08-31,
    ninjatrader.com/pricing/margins); AMP maintenance $28,813 (2026-10-02,
    ampfutures.com) — <11% apart incl. AMP retail +10% adjustment.
  - Roll cost: gap observable & measured (above); as an executed cost
    (crossing two books) NOT_RUN — thin-book side unmeasurable.

## 4. Event calendar

All times below: release time (source-stated) + exchange tz (US/Central,
CT=America/Chicago; RTH 08:30–16:00 CT; Globex 17:00 CT→16:00 CT).

| Event | Actual release time (UTC / CT) | Vintage & PIT properties | Effective vs available vs retrieved | Evidence class |
|---|---|---|---|---|
| FOMC decisions 2026 | Meetings Jan 27-28, Mar 17-18*, Apr 28-29, Jun 16-17*, Jul 28-29, Sep 15-16*, Oct 27-28, Dec 8-9* (* = SEP). Statement day-2 ~14:00 ET (19:00 UTC) — statement time POSTULATED, not fetched; minutes ~3 weeks later | Statements are final at release (no revision); SEP projections revised each SEP meeting | Effective = statement timestamp; available = same minute on Fed site; retrieved in our repo: NO (must schedule) | Calendar FACT (federalreserve.gov, 2026-10-02); statement-time POSTULATED |
| CPI (BLS) | 8:30 AM ET (12:30/13:30 UTC winter/summer) = 07:30 CT; 2026 releases: Jan 13, Feb 13, Mar 11, Apr 10, May 12, Jun 10, Jul 14, Aug 12, Sep 11, Oct 14, Nov 10, Dec 10 (reference month M-1) | Index not typically revised (seasonal factors revised annually) — revision policy NOT fetched this session | Effective = 8:30 ET release; seasonal-revision vintage PIT note applies only to SA series | Schedule FACT (bls.gov/schedule/news_release/cpi.htm, 2026-10-02) |
| Employment Situation / NFP (BLS) | 8:30 AM ET; mostly first Friday (2026: Jan 9, Feb 11, Mar 6, Apr 3, May 8, Jun 5, Jul 2, Aug 7, Sep 4, Oct 2, Nov 6, Dec 4) | Prior-two-month payroll revisions standard (revision policy text not fetched); reference week (week incl. 12th) not stated on fetched page | Effective = 8:30 ET; revised vintages mean backcast must use ALP/vintage files for strict PIT | Schedule FACT (bls.gov/schedule/news_release/empsit.htm, 2026-10-02) |
| CFTC CoT (Financial Futures, incl. ES complex) | "generally published each Friday at 3:30 pm ET" (14:30 CT / 19:30/20:30 UTC); positions as of the **prior Tuesday** close ("three days to process") | Position date (Tue) ≠ release (Fri) — PIT lag ≥ 3 days; holiday shifts per CFTC release-schedule page | Earliest legal observation = Fri 15:30 ET; using Tuesday-dated positions earlier = look-ahead | FACT (cftc.gov/MarketReports/CommitmentsofTraders/index.htm, 2026-10-02) |
| ES quarterly OpEx / expiry | 3rd Friday H/M/U/Z, final trading to 08:30 CT; **June shifted for Juneteenth** (2026-06-18, 2027-06-17) | Contract calendar published years ahead (S1 resolves to 2031) | Fully knowable in advance (no PIT issue) | FACT/OBSERVED (S1 lastTradeDate set, computed) |
| Roll week (volume migration) | Starts ~5 sessions before old-contract expiry (measured: 2025-09-15, 2025-12-12, 2026-03-13, 2026-06-11, 2026-09-14) | Determinable PIT only with same-day volume data (front/next), or pre-declared calendar proxy (T-5) | Measured ex-post here; as a forward rule use T-5 calendar (deterministic) | OBSERVED (5 cycles) |
| ISM, PCE, GDP, Treasury auctions | NOT fetched this session | — | — | NOT_RUN (calendar) |

Consensus/surprise datasets: none in repo; any "surprise-adjusted" design is
blocked until a PIT consensus archive is sourced (vendor decision = owner).

## 5. Hypotheses (ranked by testability × causal plausibility — NOT by PnL)

Corpus-1200 reuse: none checked — corpus not provided to this lane. No
FX→futures transfer claimed; ES/NQ ideas are native to this futures corpus.

**H1 — Roll-calendar liquidity alignment (mechanics-level, testable NOW).**
- PIT condition (observable): calendar-only: old-quarterly age reaches
  expiry−5 sessions (T-5, e.g. Thu/Fri of roll week), with Juneteenth June
  shift applied.
- Prediction: declared-rule baseline (roll at last session before expiry
  month) holds a book with <1% of front volume for ~8–9 sessions/quarter;
  T-5 roll aligns with measured migration ramps (5/5 cycles).
- Mechanism: quarterly OpEx economics (options/roll programs concentrate in
  roll week) migrates lendable liquidity front→next; calendar-only rule is
  deterministic and PIT-safe.
- Entry/exit (as a *construction rule*, not a trade): switch continuous
  reference contract at T-5 close; exit N/A; TP/SL N/A; direction N/A.
- Universe/roll: ES HMUZ; sizing N/A; cost model: roll gap (measured
  +52.5..+67.75 pts) + two-sided execution in roll week.
- Invalidation: a cycle where next-contract volume ramp deviates >3 sessions
  from T-5 (watch Dec cycles / holiday compression).
- Counter-hypothesis: migration is volume-driven not calendar-driven
  (crossover unmeasurable in this snapshot — prospective collector can test).
- Failure conditions: June expiry handling bug (Juneteenth); using vendor
  continuous instead of own chain.
- Data requirements: ALREADY met by raw daily files (this dossier, §1/§3).
  Floor: none. Budget: 0.

**H2 — Roll-gap carry sign tracks (short rate − dividend yield).**
- PIT condition: at each quarterly roll, spread between adjacent closes
  (observed) vs contemporaneous ~3M USD rate and S&P forward dividend yield.
- Prediction: gap > 0 while rate > div yield (5/5 measured positive,
  2025-06→2026-09); sign should flip when div yield exceeds rates.
- Mechanism: cost-of-carry fair value (index arbitrage anchors futures =
  spot + carry).
- Entry/exit/TP/SL: N/A (structural relation, not a standalone trade; informs
  continuous-construction drift and calendar-spread ideas).
- Direction: N/A; universe: adjacent HMUZ pairs; sizing N/A; cost model: spread
  legs (measured spread median 1 tick front).
- Invalidation: positive gap persisting while rate < div yield (would indicate
  rebalancing demand premium).
- Counter-hypothesis: gaps are demand/supply pressure (hedging flows), not
  carry.
- Failure conditions: using settlement-derived deferred closes as tradable
  prices (they are marks, not fills).
- Data: gaps OBSERVED; rate/dividend series NOT in repo → FRED (free) for
  rates; dividend yield needs index-provider or SPX options data (paid) —
  PARAM-GAP until sourced (owner decision). Floor: ≥8 quarters for a sign
  statement (we have 5 measured + deeper deferred marks NOT tradable).

**H3 — Post-macro-release persistence after surprise-adjusted releases.**
- PIT condition: 8:30 ET CPI/NFP or 14:00 ET FOMC, surprise measured vs
  PIT consensus archive (NOT in repo).
- Prediction: 30-min post-release drift continues surprise-implied direction;
  effect strongest in high-vol/tight-Fed regimes, weakest mid-cycle.
- Mechanism: slow diffusion of repricing across investor horizons + dealer
  inventory smoothing (POSTULATED).
- Entry: e.g. M1 close 5 min after release; exit: +X hrs / session close;
  TP/SL/time: must be pre-declared before any run (PARAM-GAP — thresholds
  cannot be set without look-ahead-free selection protocol); direction:
  surprise-sign; universe: front quarterly (T-5 roll per H1); sizing: vol-
  scaled (declared formula before run); cost model: $2.24/side + 1–2 ticks.
- Invalidation: edge disappears with 5-min entry delay or 2× costs (master §6).
- Counter-hypothesis: full adjustment within first minute (macro efficiency).
- Failure conditions: same-bar execution assumption at 8:30; revised (non-
  vintage) macro data; consensus snooping.
- Data: BLOCKED — M1 depth ~10 months & 2D per contract (useRTH even there);
  need M1 from ≥2019 + PIT consensus. Floors: ≥40 events per class. Budget:
  vendor historical (owner decision per FINAL_REPORT §"Cần thêm").

**H4 — ES/NQ relative-value response on FOMC/CPI days.**
- PIT condition: known release timestamps (FACT §4); long-history daily data
  both symbols (raw snapshot has NQ equivalents).
- Prediction: rate-surprise days widen ES−NQ spread (growth/duration
  composition differs); horizon = 1–3 sessions.
- Mechanism: NQ's higher duration/beta reprices differently under discount-
  rate shocks (POSTULATED).
- Entry/exit: spread at prior close → exit +1/+3 sessions; TP/SL: pre-declared
  PARAM-GAP (no sweep); direction: rate-shock-sign; universe: both fronts,
  T-5 rolls; sizing: beta-neutral 1:delta (declared formula); cost model:
  both legs $2.24 + 1–2 ticks each.
- Invalidation: no spread-variance difference event vs non-event days.
- Counter-hypothesis: both legs are one beta factor → spread unresponsive.
- Failure conditions: roll-boundary contamination (unadjusted chains);
  event-window overlapping both legs' roll weeks.
- Data: daily raw exists (testable at daily resolution, ~14 months front-scale
  both symbols → LOW power; multi-year needs vendor history). Floor: ≥100
  events. PARAM-GAP on surprise measure (use event dates only as v1).

**H5 — Overnight-gap behavior conditioned on trailing vol regime.**
- PIT condition: RTH-open gap vs prior RTH close; vol regime from trailing-63d
  vol (strict past).
- Prediction (framework §15): negative-gap continuation or reversion
  conditional on regime — direction declared before run; gap already measured
  at 0.48% std (front-scale era).
- Mechanism: overnight liquidity thinness + dealer inventory at open
  (POSTULATED).
- Entry/exit: open→close RTH; TP/SL/time: PARAM-GAP; direction: declared per
  regime table before run; universe: front chain; sizing: vol-scaled;
  costs: $2.24 + gap-crossing slippage (unmeasured — NOT_RUN floor).
- Invalidation: sign instability across the (few) vol regimes in window.
- Counter-hypothesis: gaps are pure information (no reversion premium).
- Failure conditions: settlement-derived bars treated as tradable opens
  (pre-2025-06 chain unusable — open≡close flat marks); 284-day single-regime
  sample.
- Data: legal daily data sufficient for a *descriptive* first pass; ≥2y
  front-scale recommended → currently 14 months → LOW power; floor not met →
  NOT_RUN until depth acquired.

## 6. Missing data table

| Need | Have | Source (primary first) | Period | Schema | PIT properties | License/cost | Blocker | Next action |
|---|---|---|---|---|---|---|---|---|
| Intraday M1/H1 per-contract depth (H1–H5 event/microstructure) | ~30D hourly (RTH-only) + 2D M1 per contract, ~10-month wall | Databento / CME DataMine (CME-licensed vendor) | 2019→now | ohlcv-1m + definitions per expiry | Raw ticks/bars immutable; vendor timestamp policy to verify | Paid (owner decision; FINAL_REPORT option (a)) | Purchase decision + budget | Owner decision; spec drafted by DATA lane |
| Multi-year true-volume front chain (daily) | 14 months front-scale (2025-06→2026-10); deeper = settlement-derived marks only | Vendor daily per-contract TRADES + OI | 2010→now | per-contract OHLCV+OI+settlement | Volume/OI as-published (no revision) | Paid (same vendors) | Same purchase | Bundle with M1 acquisition |
| PIT macro consensus/surprise archive | Release schedules only (FACT §4); no consensus | Primary actuals BLS/Fed (free); consensus = vendor (e.g., paid archives) | 2015→now | event, datetime_utc, survey_median, actual, vintage | Consensus as-known-before-release; actuals at release timestamp | Free actuals; consensus paid | No PIT consensus in repo | Owner: pick vendor or restrict to date-based (non-surprise) designs |
| Open interest per contract (roll/OI studies, CoT cross) | NONE (raw files carry no OI field) | CME daily OI via vendor or CFTC CoT (weekly) | 2019→now | date, conId, OI | As-published next morning; CoT Friday-release (Tue positions) | Free (CoT) / vendor | OI absent from IBKR bars | Add CoT pull (free) + vendor OI with M1 bundle |
| VIX/VX + rates/dividend series (H2, driver 5) | NONE in repo | CFE VX (vendor); FRED rates (free); dividend yield (index provider) | 2019→now | daily close series | VIX real-time/index revision policy to verify; FRED vintage aware | FRED free; VX paid | Not sourced | FRED pull is free — schedule for engine-prep; VX into vendor bundle |
| BBO depth / synchronous quotes | 1Y daily BID/ASK closes (non-synchronous; close proxy only) | Vendor bbo-1m/1s | 2019→now | bid/ask/size ts | As-captured | Paid | Same purchase | Bundle; validate measured vs published costs after |

Priority for top-3 causal drivers (rates/Fed, inflation, positioning): rows
1, 3, 4 above. This dossier explicitly does NOT condition on the full wishlist.

## 7. Framework coverage

**Master §1 (10 questions):**
1. Underlying exposure: $50 × S&P 500, US large-cap beta + risk appetite [FACT].
2. Participants: hedgers (asset managers), speculators (CTA/macro), MMs, index
   arbitrageurs [POSTULATED; per-participant measurement NOT_RUN].
3. Exchange/sessions: CME Globex 17:00→16:00 CT + RTH 08:30–16:00 CT, DST-
   correct [FACT/OBSERVED S1+S9]; **raw bars are RTH-only** [OBSERVED].
4. Size/tick/currency/margin/settlement: 50×, 0.25=$12.50, USD, cash-settled;
   margins $26.0k–28.8k maint class [FACT/OBSERVED §1/§3].
5. Listed months / liquid expiries: HMUZ, 9Q+3Dec (ESZ6→ESH1 + Dec 2029-31);
   only front quarterly liquid [FACT/OBSERVED].
6. Liquidity migration: roll-week ramp T-4/5 before expiry, 5/5 cycles
   measured; exact crossover NOT_RUN (data window) [OBSERVED §1].
7. Behavior dominated by: macro expectations + carry (5/5 positive roll gaps)
   + microstructure roll effects; cash-arb channel via fair-value carry
   [OBSERVED gaps; dominance attribution POSTULATED].
8. Which session matters: cannot rank Asia/Europe/overnight vs US — overnight
   absent from data [NOT_RUN]; within RTH, 09:00 & 14:00 CT hours carry most
   volume (30-day window) [OBSERVED].
9. Tradeable contract per timestamp (PIT): front quarterly until T-5, then
   next (H1 rule); volume-based selection needs OI/both-side volume
   [OBSERVED-informed design; crossover NOT_RUN].
10. Vendor symbols ↔ expiries + reproducible continuous: localSymbol→conId
    mapped in S1 (ESZ6=515416632 etc.); declared-rule unadjusted chain built
    here; back-adjustment delegated to engine (gaps measured) [FACT/OBSERVED].

**ES framework checklist (§1–§17) — status:**
- §1 Foundation: answered (above + §1) [FACT/OBSERVED where stated].
- §2 Market structure (session/expiry volume distribution, roll speed, spread
  widening): volume by hour & roll windows OBSERVED (30d/5 cycles); spread
  widening near events/expiry NOT_RUN (non-synchronous BID/ASK); opening/
  settlement effects NOT_RUN (RTH-only bars); contract-selection stability
  (calendar vs volume vs OI) partially — calendar T-5 vs declared measured,
  volume/OI alternatives NOT_RUN.
- §3 Causal driver table: §2 above [each row tagged].
- §4 Regime map: one regime in front-scale sample (rally, 12% vol); regime
  taxonomy NOT_RUN (needs multi-year + macro series).
- §5 Event-study framework: calendar FACT; 1m/5m/… measurements NOT_RUN
  (intraday depth).
- §6 Term-structure/roll: raw panel built; front chain built; roll gaps
  measured; calendar-vs-volume-vs-OI roll comparison NOT_RUN (no OI);
  back-adjusted vs unadjusted comparison delegated to engine (gap sizes
  measured) [OBSERVED].
- §7 Cross-asset (NQ/ZN/VIX/DXY/credit/SPX): NQ raw exists in snapshot —
  cross descriptives NOT_RUN this session (lane scope ES); others absent.
- §8/§15 Candidate signals: 5 hypotheses specified (§5), each with mechanism
  + falsification; no backtests run (PREP).
- §9 Backtest protocol: inputs prepared (per-contract panel, roll table,
  costs); protocol execution NOT_RUN (task classification).
- §10 Data checklist (Databento phase-1 etc.): mapped in §6.
- §11/§16 Failure modes: crisis discontinuity absent from sample (single-
  regime caveat); limit-move handling [FACT limits, §1]; options-expiry
  distortion flagged (§2 driver 10); basis effects = roll-gap carry (§2
  driver 8) — all else NOT_RUN until depth.
- §12 Deliverables: this dossier covers items 1-8, 10 partially; 9 (backtest
  report), rejection log NOT_RUN.
- §13 Contract-specific driver map: covered in §2 (7 primary + confirmations;
  confirmation-variable measurement NOT_RUN).
- §14 Index-arb vs discovery, overnight transfer, dealer-hedging dominance,
  basis separation: overnight transfer measured at daily gap level
  [OBSERVED §3]; others POSTULATED/NOT_RUN.
- §17 First sprint: items 1-3 done at legal depth (panel, roll/liquidity
  diagnostics, daily/session stats); 4-6 blocked on data (§6); 7 pending.

**Open questions (carried to handoff):** (1) exact volume crossover date per
roll (needs both-contract overlapping volume or prospective collection);
(2) whether June Juneteenth shift also moves roll-week patterns; (3) measured
(tick-level) vs published costs; (4) consensus archive choice.
