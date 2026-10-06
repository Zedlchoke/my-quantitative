# 6J_DOSSIER — Japanese Yen Futures (CME 6J)

- Symbol: 6J (CME; tradingClass `6J`, broker symbol field "JPY")
- Exchange: CME (Globex); vendor endpoint IB TWS API, contract timeZoneId US/Central
- Generated_utc: 2026-10-02 (lane local; all web access dates below are 2026-10-02)
- Author lane: SYMBOL-DOSSIER-6J, task FUTURES-BEHAVIOR-10SYMS-PREP-20261002 (PREP ONLY —
  no scored runs, no PnL/event-studies/sweeps, no GO)
- Inputs:
  - owner_framework/6J_RESEARCH_FRAMEWORK.md sha256
    `bc3ad5a3d38a72f1de96ab8749854ce46241e033a7682ee94b5e3b8e2cd16217`;
    00_MASTER_FRAMEWORK.md sha256
    `a75571b8017b13b5ff6552755d1334b03db640ebc26a6b4c9ad4323ca16d3c74`
    (owner_framework/SHA256SUMS.txt)
  - research/control/FUTURES-DATA-10SYMS-V1/FINAL_REPORT.md sha256
    `9722d3a123da7e3bc1546293705c241aab7eb938fed38a08f2f07600926e4260` (untracked snapshot,
    read-only) + S1_IDENTITY.json sha256 `d217ab9dcd865765e1bcae8f8131dee2f7f200cd90c07403280134da32b05822`,
    S9_INDEPENDENT_VERIFY.md, S6_FRONT_SPREADS.json,
    costs/SPECS_MARGINS_PUBLIC_2026-10-02.md, costs/IBKR_futures_commissions_2026-10-02.json
  - Raw (read-only): ~/.my-quantitative-data/futures-10syms-v1/raw/ files `6J_*`
    (20 contracts × 5 job types = 100 files + 5 front/expired 3D probes)
  - Analysis: analysis/6J_descriptives.py → analysis/6J_descriptives.json (this lane,
    descriptive only, strict past/rolling windows)
- Claims taxonomy used everywhere below: FACT (sourced; primary source + access date) /
  OBSERVED (raw + script + window) / POSTULATED (mechanism, unmeasured) / NOT_RUN
  (default; never inferred PASS).

## 1. Mechanics

- Underlying exposure: 12,500,000 Japanese yen vs US dollars, quoted in **USD per JPY**
  (JPY/USD convention; 6J price = 1 / USDJPY spot, NOT inverted in this data), physically
  delivered at expiry (delivery obligates exchange of ¥12.5M for USD at the settlement
  price). [FACT-secondary: NinjaTrader/AMP mirrors of CME spec, fetched by data lane
  2026-10-02, costs/SPECS_MARGINS_PUBLIC_2026-10-02.md, incl. NT FAQ "exchange ¥12,500,000
  for USD"] [FACT-primary-marketing: CME product page "Japanese Yen Futures JPY/USD"
  (cmegroup.com/markets/fx/g10/japanese-yen.contractSpecs.html, accessed 2026-10-02 via
  web-reader fallback; page title confirms JPY/USD quotation framing and names "monthly
  and quarterly futures"; the numeric spec table is JS-driven and did NOT render)]
  [OBSERVED corroboration: S1_IDENTITY.json 6J — multiplier "12500000", minTick 5e-07,
  currency USD, uniform on all 42 resolved contracts incl. expired walk (S9 check 2)]
- Quote convention verified on raw closes: min 0.006127 / max 0.010176 USD per JPY
  (implied USDJPY band 98.3–163.2), zero closes ≥1.0 across 9,136 daily bars, and **every
  close lies exactly on the 5e-7 tick grid** (max deviation 0.0). Yen appreciation = 6J
  price UP; a long 6J is long JPY/short USD. [OBSERVED: analysis `quote_convention_check`;
  S9 check 6 PASS]
- Tick/multiplier/tick value: minTick 0.0000005 USD/JPY × ¥12,500,000 = **$6.25/tick**;
  notional at 0.00633 ≈ $79,100/contract. Note legacy-source conflict ($0.000001/$12.50
  legacy JY tick on TradingCharts) — adjudication requires the CME rulebook, which is
  transport-blocked; broker secdef + raw tick-grid agreement support 5e-7/$6.25.
  [FACT-secondary + OBSERVED; official CME numeric NOT_RUN]
- Participants: natural hedgers = Japanese exporters/importers and corporates (CME page
  cites >$250bn US–Japan goods/services trade), banks/bullion-style FX dealers, asset
  managers hedging JPY exposure; speculators = macro funds, CTAs, carry traders,
  retail-size leverage accounts (margin ~$3k vs ~$79k notional ≈ 26×); arbitrageurs/MMs
  link 6J to USDJPY spot/forwards, cross-listed yen futures and FX Link; official-sector
  (MOF) intervention operates in the underlying spot market, not on 6J, but repriced it
  violently in 2026 (§3). [POSTULATED: participant map per owner framework + CME framing;
  not measured]
- Sessions & DST: Globex session 17:00 CT (day-1) → 16:00 CT (day-2), Sun open / Fri
  close; broker `liquidHours` window 08:30–16:00 CT (09:30–17:00 ET). [OBSERVED: S1
  tradingHours/liquidHours strings] Bar timestamps carry ISO offsets; DST verified correct
  at each bar's own date across all 11 non-empty 6J 1-min files (e.g. 6JH6 2026-02 bars
  −06:00 CST, 2026-09/10 bars −05:00 CDT). [OBSERVED: S9 check 5]
- Holidays: exchange holidays absent from raw calendar — verified absent on 6JZ6 bars:
  2026-09-07 (Labor Day), 2026-07-03 (observed Independence Day), 2026-12-25, 2026-01-01;
  S1 marks 2026-10-03/04 CLOSED (weekend). [OBSERVED: raw daily panel]
- Delivery/first-notice/last trade: physically delivered; last trade "ceases 10:16 am ET
  two business days prior to the third Wednesday of the contract month" per NT mirror —
  consistent with S1 `lastTradeTime` 09:16 CT = 10:16 ET on every contract. Per-contract
  last-trade dates from S1 chain: 6JV6 2026-10-19, 6JX6 2026-11-16, 6JZ6 2026-12-14,
  6JH7 2027-03-15… Price limits: NOT_RUN (no primary/secondary source fetched; do not
  assume "none" — FX futures historically no limits, but unverified). First-notice-day
  mechanics: NOT_RUN (not applicable/documented for deliverable FX — unverified).
- Listed months & liquid maturities: **~24 consecutive monthly contracts + HMUZ
  quarterlies out ~5 years** (S1 active chain 2026-10-02: every month 2026-10→2028-09,
  then quarterly 6JZ8…6JU1 through Sep-2031 = 36 contracts) [OBSERVED: S1 chain;
  FACT-primary-marketing: CME "convenient monthly and quarterly futures"]. NT mirror
  describes only "quarterly contracts listed for 20 consecutive quarters" — superseded
  by the resolved chain. **Liquid maturity = the nearest HMUZ quarterly only**:
  quarterlies 6JZ5/H6/M6/U6/Z6 traded 1.38M–3.82M lots over their lives (last front-window
  sessions 40k–135k lots/day), while the serials present in raw are dead: 6JV6 total
  3,511 lots (max 139/day), 6JX6 775 lots (13–76/day recent), and all 2027+ serials
  (6JF7…6JF8) have zero real volume so far (flat settlement-derived bars only).
  [OBSERVED: analysis `panel`, `serial_coverage`]
- Liquidity migration front→next [OBSERVED, analysis `volume_migration` +
  `roll_analysis.u6_to_z6_liquidity_skip`]: liquidity migrates **quarterly → next
  quarterly**, NOT calendar-month-to-month. The old quarterly remains the dominant
  contract through its final pre-delivery session (declared roll session), e.g. 6JU6
  79,185 lots on 2026-08-31 vs 752 on incoming 6JZ6; the new quarterly then ramps over
  ~2 weeks (6JZ6: 1,295 lots Sep-1 → 20,821 Sep-8 → 132,774 Sep-14, 2026). **No
  pre-roll volume crossover exists within ±10 sessions of any 2025-26 roll** (unlike GC,
  where the flip led the roll by 1–2 sessions). In Sep-2026 the quarterly 6JZ6 carried
  **99.73%** of all recorded U6/V6/X6/Z6 volume; the calendar front serials 6JV6+6JX6
  together carried ~0.2%.
- **Roll-rule executability defects found by this lane (explicit check, as GC did):**
  1. [OBSERVED, analysis `serial_coverage.missing_serial_delivery_months`] The raw set
     contains **NO serial months with delivery 2025-10…2026-08** (missing: 6JV5, 6JX5,
     6JF6, 6JG6, 6JJ6, 6JK6, 6JN6, 6JQ6). The data lane's declared rule ("roll to the
     next listed contract at the last session before the delivery month") is therefore
     **NOT executable on this dataset for every roll in 2025-09→2026-08** — those next
     listed serials were listed by CME but never fetched and are now unresolvable
     (expired-secdef wall ~1y). The executable approximation used in analysis rolls
     quarterly→next quarterly (3-month skip), which happens to coincide with where the
     liquidity actually was.
  2. [OBSERVED] From 2026-08-31 onward the declared next-listed contracts ARE in the raw
     set, but they are near-dead serials: the literal declared rule routes U6→6JV6 at
     2026-08-31 (V6 ≈ 0.1% of that day's U6+V6+Z6 volume) and V6→6JX6 at 2026-09-30
     (X6 26 lots vs 6JZ6 118,886 lots on 2026-10-01). Executable on paper at 1-lot size;
     economically non-viable. **Baseline roll rule for any future backtest must be
     restated as "next HMUZ quarterly"** (or volume/OI-gated), with the calendar-serial
     rule treated as a known defect, not a baseline.
- Roll cost: observable as adjacent-contract close gaps at roll sessions (raw, NOT_COMPUTED
  as a tradable cost): quarterly→quarterly 3-month skips measured +109/+100/+92 ticks
  ($681.25/$625.00/$575.00 per contract) at 2025-11-28,
  2026-02-27, 2026-05-29; 1-month gaps +34 ticks ($212.50, U6→V6 2026-08-31) and +28
  ticks ($175, V6→X6 2026-09-30). Sign always positive (far above near — see §3 curve).
  [OBSERVED: analysis `roll_analysis.rolls`]

## 2. Causal driver map

Master-framework buckets covered for 6J: Macro, Fundamental (Japan-specific macro),
Cross-asset, Positioning, Term structure, Microstructure, Event-driven. "Class" marks the
measurement status in this prep.

| # | Driver (bucket) | Source variable → mechanism | Predicted sign / horizon | Regime dependency | Confounders | Falsification test | PIT data source (primary, access date) | Class |
|---|---|---|---|---|---|---|---|---|
| 1 | US–JPY short-rate differential (Macro) | US rates > JPY rates → covered-parity forward premium on USD → 6J deferreds ABOVE nears (measured §3) → long-JPY futures bleed roll; yield-diff widening = JPY weakness spot-side | 6J down / diff up, days–months | Dominant outside intervention/BoJ-shock weeks; fails near MOF thresholds (H5) | rate expectations vs realized; term premia; intervention offset | diff-widening weeks with no 6J underperformance vs curve-implied drift | USD OIS/T-bill + TONA/¥LIBOR-successor series with vintages (BOJ/official — NOT fetched) | Curve consequence OBSERVED (§3); yield series NOT_RUN |
| 2 | BoJ policy / YCC stance (Macro, event) | Tightening surprise → JPY up (6J up); regime changes break historical rate relations | 6J up on hawkish surprise / minutes–days; regime breaks | Strongest at regime changes (YCC exit-type); weak at unchanged meetings | simultaneous MOF/US news; guidance vs action gap | MPM-day 6J move sign vs statement classification | BoJ MPM calendar + statements FACT (boj.or.jp, 2026-10-02); surprise measure NOT_RUN | Calendar FACT; response NOT_RUN (§3 has day-level description only) |
| 3 | MOF intervention risk / operations (Event, FX-specific) | Yen-buying ops → immediate 6J up-jump + option-implied skew repricing; verbal intervention dampens drift | 6J up sharply on op days (+2.5–2.8% measured); partial next-day retracement (−0.25…−0.4% measured) | Only near multi-decade yen-weak levels (~USDJPY 160+ in 2026 data); absent elsewhere | BoJ meeting coincidence (Jul 30-31, 2026); month-end flows | op days without up-moves, or up-moves without subsequently disclosed ops | MOF quarterly/monthly FX intervention pages FACT (mof.go.jp, 2026-10-02); same-day PIT signal NOT available (amounts published with ~1-month/quarter lag) | Ops FACT + day reaction OBSERVED; same-day tradability NOT_RUN |
| 4 | Global risk-off / carry unwind (Macro, cross-asset) | Risk-off → carry shorts unwind → JPY repatriation bid → 6J up; strength depends on starting carry positioning | 6J up in stress / hours–weeks | Strongest from crowded-short-yen + high-vol starts; weak when BoJ normalizing | USD bid-in-stress offset; US rates move | high-VIX days with no 6J bid conditional on positioning | VIX/ES in own corpus (ES raw present); positioning needs CoT | Mechanism POSTULATED; 2026 co-moves NOT_RUN |
| 5 | Japanese inflation / wages (Macro, fundamental) | Inflation above target → BoJ tightening expectations → JPY up | 6J up / days–weeks | Only when BoJ reaction function credibly inflation-linked | energy import pass-through (row 6); base effects | CPI/wage surprises with no rate-expectation or JPY response | Japan CPI (Statistics Bureau) schedule NOT_FETCHED (stat.go.jp URLs 404 — NOT_RUN); vintage properties unknown | POSTULATED, NOT_RUN |
| 6 | Energy import costs (Fundamental) | Japan energy imports priced in USD → oil up = JPY terms-of-trade hit → 6J down | 6J down / days | Weaker post-2011 (energy mix); yen-weak feedback loop into import inflation | CL moves driven by JPY-safe-haven flows (reverse causality) | CL-shock days with no 6J down-move | CL in own corpus (OBSERVED available) | Mechanism POSTULATED; measurement NOT_RUN |
| 7 | Global carry appetite / positioning (Positioning) | Crowded short-JPY carry → squeeze risk when vol rises; CoT extremes mark fragility | Contrarian at extremes / weeks | Only with high-vol trigger | CoT = Tue positions, Fri 15:30 ET release (≠ trade date) | positioning-extreme weeks with no conditional vol-response | CFTC CoT weekly, Fri 15:30 ET, as-of prior Tuesday, not revised [FACT: cftc.gov via costs/GC lane sourcing, 2026-10-02]; series NOT fetched | Release rule FACT; use NOT_RUN |
| 8 | Term structure / roll carry (Term structure) | Deferreds above nears ~100% of sessions (measured) = USD-JPY differential embedded; long-JPY pays ~2.2–2.7%/yr to roll; short-JPY earns it | Roll-yield drag constant sign / per-roll | Compresses if JPY rates converge with USD rates | settlement-derived deep bars pre-2025 | curve days near/below flat while diff positive | own raw panel | OBSERVED (§3) |
| 9 | Roll-window microstructure (Microstructure) | Liquidity migrates quarterly→quarterly with a ~2-week post-roll ramp; calendar-serial rule lands in dead books | Execution effect around roll / days | Always; worst when calendar front = serial (2 of every 3 months) | vendor volume scale differences; expired-file clipping at delivery-month start | serial-front months where spread/depth do not blow out | own raw panel + daily BID/ASK | OBSERVED (§1, §3) |
| 10 | Cross-asset: USTs, Nikkei, ES/VIX, 6E, DXY, gold (Cross-asset) | USD-wide moves dominate 6E/6B/6A/6J jointly; Nikkei↔JPY inverse (repatriation); gold-USD co-moves | Correlative / days | Sign flips in stress vs carry regimes | common USD driver; BoJ idiosyncrasy | rolling-beta instability across regimes | 6E/6B/6A/ES/GC in own corpus (OBSERVED available); Nikkei/VIX/DXY NOT in corpus | Mechanism POSTULATED; data availability OBSERVED |
| 11 | Session/fix microstructure (Microstructure) | Tokyo fix/London fix/Wall-Street-RTH volume waves; BoJ releases hit overnight (US hours) | Intraday concentration | RTH-only files cannot see Asia session | useRTH=True clipping | — | own raw hourly (RTH only) | PARTIAL OBSERVED (§3); overnight NOT_RUN |

## 3. Behavior (measured where legal)

All statistics: analysis/6J_descriptives.py → 6J_descriptives.json, computed from the raw
6J_* files. Returns are within-contract daily log returns on the **quarterly (HMUZ)
liquidity chain** (old contract keeps the roll-date return; no stitched jumps); the
data-lane calendar rule is non-executable/defective for this symbol (§1) and its literal
serial-routing is not used for statistics. Thresholds use strictly-prior rolling windows;
ex-post labels are description-only. No PnL/performance metrics anywhere.

- **What window is actually measurable**: per-contract daily depth spans 2020-12→2026-10
  but is settlement-derived (v=0, O=H=L=C) for most of history (flat share 81–99% per
  contract); the quarterly chain has real vendor volume continuously from
  **2025-05-20 → 2026-10-01** (342 return obs). Long-horizon *reference* stats come from
  single contracts without stitching: 6JZ5 full life 2020-12→2025-11 (n=1,263) and 6JZ6
  2021-12→2026-10 (n=1,219), settlement-derived deep era included. NOTE: before Sep-2025
  the "quarterly chain" actually holds 6JZ5 as a deferred contract (the nearer serials
  and 6JU5 are missing from raw), so 2021–mid-2025 chain stats describe a curve point
  ~5→0 months out — near-identical to front behavior in level-vol for FX (curve vol
  nearly flat: 6JZ5 vs 6JZ6 by-year vol differ by ≤0.4pp) but disclosed.
  [OBSERVED: `quarterly_chain`, `long_horizon_single_contract_refs`]
- **Volatility**: annualized daily vol by year (quarterly-chain, full depth incl.
  settlement-derived): 2021 4.8%, 2022 **10.8%** (BoJ YCC-shock year; both single-contract
  series' extreme days are 2022: min −2.17% on 2022-06-17, max **+3.9% on 2022-12-20**,
  the historic YCC-widening day), 2023 8.4%, 2024 9.8%, 2025 9.8%, 2026 (Jan–Sep) 8.7%.
  Real-volume era 2025-05→2026-10: σ=0.55%/day (8.7% ann); rolling 21-session realized
  vol mean 8.4%, max **12.4%**, latest (2026-10-01) 12.1% — i.e. 2026 Q3 intervention
  period is the vol peak of the measurable era. [OBSERVED]
- **Drift / regime (description-only)**: real-era mean −0.037%/day, median −0.08%/day,
  only **37.7% positive days** — a persistent yen-depreciation regime taking 6J from
  ~0.0069 (USDJPY ~145) to the 0.006127 low (implied USDJPY **163.2**) reached in the
  pre-intervention weak extreme; sign-matches-trailing-50d-mean share 56.2% (mild
  trending bias within the depreciation era). Lag-1 return autocorr −0.055 (very mild
  daily mean reversion); |r| lag-1 autocorr +0.109 (mild vol clustering). [OBSERVED]
- **Intervention-day behavior (measured description, NOT an event study)**: the two
  largest up-moves of the real era are MOF yen-buying operation days verified from
  primary MOF pages: **2026-04-30 +2.48%** (¥6,278.7bn op; volume 107,535) and
  **2026-07-30 +2.75%** (start of the record late-Jul/Aug window; volume **490,134 ≈ 10×
  normal**) [m5 fix 2026-10-02, audit R6: these two are SIMPLE returns; on this section's
  declared log-return convention they are +2.44% and +2.71%]; 2026-05-06 +0.94% (¥4,675.9bn op). Day-after sessions partially retraced
  (−0.39%, −0.25%). The 2026-07-30/31 BoJ MPM coincides with the intervention window
  (2026-07-31 close unchanged 0.006314 after +2.75% simple). BoJ MPM day-2 dates also show in
  the big-move list: 2026-01-23 +1.61%, 2026-03-19 +1.29%. MOF amounts are published
  with ~1-month (monthly) / quarterly lag — these day reactions are *descriptions* of
  disclosed operations, not a same-day PIT signal. [OBSERVED: `intervention_day_description`,
  `top10_abs_moves_realera`; ops FACT mof.go.jp 2026-10-02]
- **Large-move frequency (strict past threshold)**: days with |r| above the 95th
  percentile of prior-126-session |r|: 12/216 (5.6%), clustered Dec-2025–Jan-2026,
  Mar-2026, 2026-04-30, Jul-30→Aug, Sep-2026 — bursts, not Poisson scatter.
  [OBSERVED, description-only]
- **Seasonality (tiny buckets, description-only)**: mean |r| by month (real era): highest
  Oct 0.48%, Sep 0.45%, Mar 0.45%; lowest Jun 0.32%, May 0.33%. Weekday: Thu 0.46% >
  Mon/Tue 0.38–0.39% > Fri 0.38% > Wed 0.35%. n=19–44/month. NOT a signal. [OBSERVED]
- **Curve / term structure (settlement-derived deep era included, description-only)**:
  near **below far on 100.0% of overlapping sessions for every pair measured** (1,000+
  sessions per quarterly pair): median quarterly (3m) spread −6.1…−6.3e-5 USD/JPY
  (−122…−126 ticks ≈ −$763…−788/contract); 1-month serial spreads −28 ticks (V6–X6, X6–Z6);
  6m −249 ticks; 12m −338 ticks. ≈ −28…−42 ticks/month ≈ **−0.22…−0.33%/month ≈ −2.6%/yr
  roll drag for long-JPY** (short-JPY earns it) — consistent in sign and size with
  USD-over-JPY short-rate differentials across 2021–2026. Backwardation absent in this
  data. [OBSERVED]
- **Roll-window behavior**: old quarterly dominant through its final pre-delivery session
  (no pre-roll crossover; new quarterly ramps over ~2 weeks post-roll — §1). Roll-session
  adjacent-contract close gaps always positive ≈ curve carry (quarterly roll gap ≈ 3 ×
  monthly gap) — gap ≈ carry, NOT an extra penalty signal. [OBSERVED; gap ≠ tradable cost]
- **Intraday session profile — US RTH only**: pooled hourly bars (quarterly front windows
  + current actives, 30-D windows, 2,148 bars, 142 sessions, labels CT): volume share
  peaks in the **09:00 CT hour = 10:00 ET (25.1%)**, then 10:00 CT/11:00 ET (16.3%),
  13:00 CT/14:00 ET secondary bump (14.1%), decay to 4.4% by 15:00 CT; the 08:30 CT
  (09:30 ET) opening stub carries 12.1%. Median bar range declines 0.12% (09:00 CT)
  → 0.03% (15:00 CT). **Asia session (where USDJPY and BoJ releases actually trade) and
  London: NOT_RUN** — useRTH=True files contain no overnight bars; no statement about
  global session leadership can be measured from this corpus. BoJ MPM decisions are
  announced "in the afternoon JST" on day-2 [FACT: boj.or.jp calendar page, 2026-10-02]
  = US overnight, outside all RTH files. [OBSERVED + NOT_RUN]
- **1-minute behavior: NOT_RUN** — 1-min files are 2-day snapshots per contract.
- **Spread/cost observations**: daily BID/ASK closes (non-synchronous → NOT an executable
  spread): quarterlies tight — 6JU6 1Y median 4 ticks, last-20 **1 tick ($6.25)**;
  6JZ6 1Y median 5 ticks, last-20 2 ticks ($12.50); current calendar-front serial 6JV6
  5 ticks median (last-20 4 ticks) reconciling with S6_FRONT_SPREADS 6J (4.0 ticks, $25,
  n=20) — quotes can be tight on dead serials while depth is ~nil (V6 volume ≤139
  lots/day). Deferred/dead serials wide: 6JF7/G7/J7/K7 264–342 ticks; 6JX6 1Y median 264
  ticks collapsing to 4 once at front; crossed days: 0 on all 6J contracts. Commission:
  IBKR $0.85/side + exchange fee NOT_FETCHED (only ES example exists); slippage
  NOT_RUN_NO_DECLARED_VALUE; margins (public broker pages, 2026-10-02): initial ~$3,080,
  maintenance ~$2,800 (NT/AMP; day-margin $500–770) — broker-class, CME SPAN official
  BLOCKED_HTTP. [OBSERVED + FACT-secondary per costs/ artifacts]

## 4. Event calendar

Scheduled events relevant to 6J, exchange tz = America/Chicago (CT). Calendars are FACT
(primary sources, access 2026-10-02). Response measurement of 6J to any of these: NOT_RUN
(no same-day surprise data; intraday depth ~10 months RTH-only; overnight releases
invisible in RTH files).

| Event | 2026 remaining dates (2027 known dates) | Release time | UTC | PIT properties | Source (access 2026-10-02) |
|---|---|---|---|---|---|
| BoJ Monetary Policy Meetings | Oct 29–30, Dec 17–18 (2026: Jan 22-23✓, Mar 18-19✓, Apr 27-28✓, Jun 15-16✓, Jul 30-31✓, Sep 17-18✓; 2027: Jan 21-22, Mar 17-18, Apr 27-28, Jun 10-11, Jul 21-22, Sep 21-22, Oct 28-29, Dec 16-17) | decision "in the afternoon" (JST) on day-2; Outlook Report at Jan/Apr/Jul/Oct MPMs; Minutes ~10 business days later | afternoon JST = ~02:00–05:00 UTC ≈ overnight CT (outside RTH bars) | statements not revised; Minutes lagged; no vintage issue on the decision itself | boj.or.jp/en/mopo/mpmsche_minu/index.htm (calendar) + mpmdeci/mpr_2026/index.htm (decisions) |
| BoJ policy changes 2026 (context) | "Change in the Guideline for Money Market Operations" at Jun 16 and Sep 18 MPMs (other 2026 MPMs: plain statements) | as above | — | rate/guideline levels themselves NOT verified (PDFs unfetchable this session) — NOT_RUN | boj.or.jp/en/mopo/mpmdeci/mpr_2026/index.htm (titles/dates FACT; levels NOT_RUN) |
| MOF FX intervention (disclosure events) | monthly releases ~end of following month; quarterly with daily detail (Q2-2026 released Aug 7; Q3-2026 page not yet published at access). Verified: Q1-2026 ¥0; Q2-2026 ¥11,734.9bn (Apr 30 ¥6,278.7bn; May 4 ¥780.2bn; May 6 ¥4,675.9bn — all USD-sold/JPY-bought); Aug 27–Sep 28 ¥0 | ~JST daytime | — | amounts knowable only ~1 month/quarter AFTER the ops (no same-day PIT); press-cited record ¥15.4T window Jul 30–Aug 26 2026 pending Q3 page | mof.go.jp/english/policy/international_policy/reference/feio/ (quarter + monthly pages) |
| Japan CPI (Statistics Bureau) | schedule NOT_FETCHED (stat.go.jp URLs 404) — NOT_RUN; convention "~08:30 JST, 19th–25th of following month" is POSTULATED, not sourced | POSTULATED 08:30 JST | — | revised once (following-month release incl. preliminary → final); verify before use | NOT_RUN |
| FOMC / US CPI / US NFP | Oct 27–28, Dec 8–9 (FOMC); Oct 14, Nov 10, Dec 10 (CPI); Oct 2, Nov 6, Dec 4 (NFP) | 14:00 ET FOMC statement (convention, unconfirmed on page); 08:30 ET CPI/NFP | 18:00/19:00; 12:30/13:30 | US-side drivers of row 1/2; NFP heavily revised (vintage-sensitive) | federalreserve.gov, bls.gov — fetched 2026-10-02 by sibling lane GC (same task); re-verify before scoring use |
| CFTC CoT (financial futures incl. 6J) | weekly, Fridays 15:30 ET | 15:30 ET | 19:30/20:30 | positions as-of PRIOR Tuesday; not revised; holiday shifts | cftc.gov (via costs artifacts; release rule FACT) |
| 6J contract events (rolls/expiry) | declared roll sessions ahead (calendar rule — defective, §1): 2026-10-30 (X6, into 6JZ6), 2026-11-27 (Z6, into 6JF7-serial-trap), 2026-12-30; liquid-relevant quarterly roll 2026-11-27 (Z6→6JH7). Last trade: 6JV6 2026-10-19, 6JX6 2026-11-16, 6JZ6 2026-12-14 | 09:16 CT cessation | — | listing calendar known years ahead (PIT-legal roll decisions); quarterly-cycle timing itself is the liquidity fact | OBSERVED: S1 chain + raw bars |

Effective vs available vs retrieved (general PIT rule): release timestamps above are the
*available* times; nothing has been retrieved into a PIT store this cycle. Any hypothesis
using BoJ/MOF/Japan-macro series must store first-release vintages (MOF ops lag ~1 month;
BoJ decisions immediate-but-overnight-CT; Japan CPI revised once) or treat as unsuitable
for strict PIT tests.

## 5. Hypotheses (3–5, ranked by testability × causal plausibility — NOT by PnL)

Reuse disclosure: corpus-1200 is outside this lane's read scope — idea-line/ID mapping
NOT_RUN. Any FX-spot-corpus idea (incl. JPY carry themes) transfers to 6J futures only as
a HYPOTHESIS: futures differ by (a) quote orientation (6J = 1/USDJPY — a USDJPY-long
idea is a 6J SHORT), (b) roll basis (−0.22…−0.33%/month measured — spot carry PnL is NOT
futures carry PnL), (c) costs/spread ($6.25/tick, 1–4 tick front spreads vs spot-dealer
pricing), (d) margin/financing. Never "already valid".

**H1 — Quarterly-chain roll rule vs calendar rule (rank 1: fully measured already).**
When the calendar front is a serial month (2 of every 3 months), the liquid vehicle is
the nearest HMUZ quarterly (measured: serial fronts carry ≤0.3% of volume; 99.73% on Z6
in Sep-2026). Hypothesis: a roll/selection rule restricted to the HMUZ chain (roll at
the declared session = last session before the held quarterly's delivery month) is the
only executable baseline; the literal next-listed rule is a defect.
- PIT condition: exchange listing calendar (known years ahead) + contract delivery
  months; no lookahead. Entry/exit = the roll switch itself; holding = quarterly
  (~3 months); direction = none (execution/construction choice); universe = 6J HMUZ
  chain; sizing = 1 contract baseline; cost model = measured front spreads (1–5 ticks)
  + roll-gap ≈ curve carry (+28…+126 ticks/roll depending on skip) + $0.85+exchange
  commission (exchange fee NOT_FETCHED); invalidation = any future sample where a serial
  month carries >20% of the concurrent quarterly's volume over a full front window;
  counter-hypothesis = serials someday liquid (CME incentives change); failure = vendor
  volume scale unreliable for levels (it is fine for relative shares — §1); data floor =
  HAVE daily per-contract TRADES+BID/ASK (2020-12→, real-volume era 2025-05→2026-10);
  budget = $0. PARAM-GAP: none for the rule itself.

**H2 — Post-intervention reversion/drift conditioning (rank 2: mechanism measured at
day level, tradability gated).** When a MOF yen-buying operation day produces a ≥2σ
(strict past window) 6J up-move, the next 1–5 sessions show partial retracement
(measured: −0.39%/−0.25% after +2.48%/+2.75%) but the 4–8 week path retained a
meaningful share of the jump in 2026 (Sep closes ~0.0063+ vs pre-op 0.00615).
Mechanism: intervention debt-repaying flows fade while the rate differential persists;
intervention-risk premium keeps a floor. Strongest when ops are large relative to
history (2026 record regime); weakest/reversed when coordinated with BoJ turns.
- Entry (test-0, description-only): day after a >2σ(prior-126d) up-move; exit +5
  sessions; no TP/SL in test-0; direction = conditional (fade vs follow comparison);
  universe = quarterly chain; roll = H1 rule; sizing = 1; cost = 1–4 tick spread +
  commission; invalidation = day-after reversion share unstable across the 2026 episode
  set (n≈3 primary ops + 2022 history not in real-volume era — sample tiny, disclose);
  counter-hypothesis = moves are BoJ-driven, not MOF (Jul 30-31 coincidence);
  failure = cannot define the condition same-day PIT (MOF amounts lag ~1 month; a
  price-only "≥2σ up-day" proxy is testable but is a different hypothesis — use that);
  data floor: HAVE daily; deeper M1 NOT available for entry timing → PARAM-GAP on
  intraday entry; budget $0 for daily version.

**H3 — Carry/curve constant: roll-drag hurdle for any JPY directional idea (rank 3:
measured structure, immediate use).** The 6J curve embeds a −0.22…−0.33%/month roll drag
for longs (100% of sessions near<far). Hypothesis (cost-model, not alpha): any
FX-spot-derived long-JPY signal must clear ~2.2–2.7%/yr + spread/commission in futures,
and conversely short-JPY signals receive that tailwind; spot-corpus PnL does not
transfer. Strongest/weakest regime: drag magnitude tracks the US–JPY differential level
(2026 Fed-vs-BoJ gap), so the hurdle is regime-dependent; falsified if the measured
monthly gap departs the interest-differential band once proper rate series are added.
- Entry/exit/holding: n/a (hurdle model applied to any H); direction = both;
  universe = HMUZ chain; roll = H1; sizing = 1; cost = the measured gap itself;
  invalidation = gap sign flips while diff stays positive; counter = curve moves are
  expectations-driven, not covered-parity; failure = settlement-derived bars misstate
  the curve pre-2025 (real-volume curve agrees 2025+); data floor = HAVE curve;
  need USD/JPY rate series (vintaged) to close the loop — PARAM-GAP.

**H4 — BoJ MPM-day conditional behavior (rank 4: calendar FACT, response NOT_RUN).**
Framework §15 hypothesis 3: BoJ surprises create multi-session momentum when the policy
regime changes (2026 had exactly two "Change in the Guideline" MPMs: Jun 16, Sep 18 —
FACT titles; levels NOT_RUN). Measured day-level context: MPM day-2 dates 2026-01-23
(+1.61%) and 2026-03-19 (+1.29%) are top-10 real-era moves; Jun/Sep MPM days coincide
with the largest Sep volume day (151,991 on 2026-09-18) — but attribution to BoJ vs
other drivers is NOT_RUN without surprise classification and overnight data.
- Entry: PARAM-GAP (decisions hit ~02:00–05:00 UTC; RTH files cannot time them; M1
  depth ~10 months and RTH-only); exit/TP/SL: PARAM-GAP; direction = conditional on
  surprise sign; universe = quarterly chain; roll = H1; sizing = 1; cost = spread +
  overnight-gap risk; invalidation = MPM-day moves indistinguishable from unconditional
  distribution once 2022–2026 sample is tested; counter = moves are US-driven (FOMC/US
  CPI adjacency); failure = no PIT surprise/consensus source for BoJ (in-house
  statement classification needed — buildable from boj.or.jp archives, $0);
  data floor: daily HAVE; intraday around JST afternoon NOT available → measurement
  limited to session-close granularity until deeper data.

**H5 — Intervention-threshold regime break (rank 5: most 6J-specific, least testable
now).** Framework §15 hypothesis 2: yield-differential/trend signals fail near
intervention thresholds. The 2026 weak extreme (implied USDJPY 163.2 = raw min
0.006127) + record ops define the zone; hypothesis: trend-following short-JPY signals
degrade as price approaches the historically-acted zone, and realized skew flips
(measured hint: two largest up-moves of the era = ops).
- Entry/exit: PARAM-GAP (threshold definition must be fixed a priori from MOF action
  history, not tuned: e.g. "implied USDJPY ≥ highest level at which MOF has previously
  acted, per MOF releases"); direction = long 6J near zone; universe = quarterly chain;
  roll = H1; sizing = 1; cost = H3 hurdle applies against longs; invalidation =
  threshold approach with no conditional behavior change across episodes; counter =
  zone is a round-number artifact; failure = needs MOF action-history series (buildable
  $0 from mof.go.jp archives) + longer real-volume 6J history (only 2025-05→2026-10
  available); data floor: partial HAVE.

## 6. Missing data table

| Need | Have | Source (primary first) | Period | Schema | PIT properties | License / cost | Blocker | Next action |
|---|---|---|---|---|---|---|---|---|
| Serial contracts 2025-10…2026-08 (6JV5/6JX5/6JF6/6JG6/6JJ6/6JK6/6JN6/6JQ6) for literal-rule replay | nothing (8 contracts absent) | (expired ~1y wall makes IB re-fetch impossible) | 2024–2026 | per-contract daily OHLCV | n/a | vendor history (owner decision) | secdef resolves only ~1y back | accept quarterly-chain baseline (H1) or buy vendor history; do NOT fake serial legs |
| MOF intervention full daily history + BoJ surprise classification | 2026 Q1/Q2 + Sep-2020 verified; rest NOT_RUN | mof.go.jp feio archives; boj.or.jp statements | 2020→ | op date, JPY amt, direction / statement text + timestamp | ops lag ~1 month; statements immediate | free | not fetched (web budget) | script the mof.go.jp quarterly archive + boj.or.jp statement index ($0) before H2/H4/H5 |
| US–JPY short-rate / yield-diff series (vintaged) | none | BOJ TONA + Fed/FRED ALFRED vintages | 2019→ | daily yield + release stamps | first-release values | free | not fetched | fetch into PIT store before H3 closure/H5 |
| Japan CPI schedule + first prints | none | stat.go.jp / e-Stat | 2019→ | release date, vintage | revised once | free | URLs 404 this session | retry via e-Stat portal |
| Intraday M1/H1 multi-year, FULL 23h session (Asia/London + BoJ afternoon-JST releases) | 30-D RTH-only hourly, 2-D M1 | vendor (Databento glbx.mdxp3 style) | 2019→ | 1-min OHLCV full session | UTC/CT stamps | $ owner decision | entitlement vintage wall ~10 months | owner vendor decision (DATA-PIT-ACQUISITION-PREP lane) |
| CFTC CoT CME-currency futures positioning | release rule known only | cftc.gov legacy + TFF | 2019→ | weekly Tue positions, Fri 15:30 ET | not revised; release≠position date | free | not fetched | fetch once H4/H5 enter measurement |
| Open interest per contract (OI-based roll alternative, capacity) | none in raw | vendor/CME | 2019→ | daily OI per contract | T+1 | vendor terms | not in entitlement snapshot | add to vendor spec |
| CME official numeric specs/fees/SPAN margin | broker secdef + NT/AMP mirrors | cmegroup.com | current | spec table | — | free | BLOCKED_HTTP (JS tables; re-confirmed 2026-10-02) | live with broker-class numbers; re-try when transport changes |

Priority = top-3 causal drivers (BoJ/intervention event record, rate-differential
series, full-session intraday) + the two $0 fixes (MOF/BoJ archive scripting; CoT
fetch). This dossier does NOT condition on the full wishlist.

## 7. Framework coverage

Master framework §1 (10 questions):

1. Underlying economic exposure → ¥12.5M vs USD, USD-per-JPY quote (1/USDJPY), long =
   long JPY; physically delivered; ~$79k notional, $6.25/tick. [FACT-secondary +
   OBSERVED S1/raw; §1]
2. Natural hedgers/speculators/MMs/arbitrageurs → exporters/importers (CME cites >$250bn
   US–JP trade), banks/asset managers; macro funds/CTAs/carry; MMs arbitrage vs USDJPY
   spot/forwards + FX Link; MOF acts in the underlying. [POSTULATED]
3. Exchange & hours → CME Globex 17:00→16:00 CT Sun–Fri; RTH/liquid 08:30–16:00 CT;
   DST verified in bars. [OBSERVED S1/S9; §1]
4. Size/tick/currency/margin/settlement → ¥12.5M; 5e-7 = $6.25/tick; USD; margin
   ~$2.8–3.1k (broker-class; CME SPAN blocked); physical delivery. [OBSERVED +
   FACT-secondary; §1, §3]
5. Listed months & normally liquid expiries → ~24 consecutive monthlies + quarterlies
   to Sep-2031 (36 resolved); liquid = nearest HMUZ quarterly ONLY (measured volumes).
   [OBSERVED; §1]
6. When does liquidity migrate → quarterly→next quarterly at the delivery-month
   boundary, with a ~2-week post-roll ramp and NO pre-roll crossover; serial fronts
   never liquid in sample. [OBSERVED; §1]
7. Dominant price behavior → macro expectations (US–JPY rate differential, BoJ, MOF
   intervention) + carry/positioning; curve dominated by covered-parity carry (100%
   near<far); NOT storage/seasonal-commodity driven. [OBSERVED for curve; POSTULATED
   for macro dominance; §2, §3]
8. Which session matters → measurable only for US RTH (10:00 ET hour = 25% of RTH
   volume); Asia/London (where BoJ trades) NOT_RUN — no overnight bars. [OBSERVED/NOT_RUN;
   §3]
9. "Tradeable" contract per timestamp (PIT volume/OI) → HMUZ-quarterly restriction rule
   (H1); OI unavailable; calendar-next-listed rule measured as defective (serial trap).
   [OBSERVED; §1]
10. Vendor symbols ↔ expiries, reproducible continuous reconstruction → localSymbol
    6J{month}{yeardigit} (6JV6 = Oct-2026…), conId per contract; raw individual
    contracts stored; roll tables derivable (gaps measured); back-adjustment NOT
    performed (description only). [OBSERVED]

6J framework's own checklist (§1 foundation, §2 market-structure, §14 questions):

- What the contract represents / fair value vs spot → deliverable JPY/USD claim; fair
  value = spot × covered-parity carry (curve measures −0.22…−0.33%/month; basis vs
  Tokyo spot NOT measured — no spot data in corpus). [OBSERVED curve; basis NOT_RUN]
- Who must trade / who speculates → §1 participants. [POSTULATED]
- Liquid expiries & migration timing → answered (quarterlies; post-roll ramp).
  [OBSERVED]
- Settlement/delivery distortion of the front → physical delivery, 09:16 CT cessation
  2 business days before 3rd Wednesday (lastTradeTime consistent across chain);
  front-week distortion itself NOT measured (no expiry-week microstructure beyond the
  2026-10 V6 tail). [FACT-secondary + NOT_RUN]
- Session with most information/liquidity → RTH 10:00 ET hour measured; Asia question
  NOT_RUN (RTH-only files). [OBSERVED/NOT_RUN]
- Minimum data for PIT reconstruction → per-contract daily TRADES+BID/ASK (HAVE;
  real-volume era 2025-05→2026-10) + HMUZ rule; missing serials listed (§6).
  [OBSERVED]
- Volume by session/expiry; roll speed; spread widening overnight/near releases/near
  expiry; opening/settlement effects; selection-rule stability; back-adjustment impact
  → volume-by-expiry OBSERVED (serials dead); roll speed OBSERVED (ramp ~2 weeks,
  no pre-flip); spread near expiry partially OBSERVED (V6 4–5 ticks into delivery
  month vs U6 last-20 1 tick — narrowing not widening in quotes, depth unmeasured);
  overnight spread behavior NOT_RUN (no overnight data); selection-rule comparison:
  calendar vs quarterly measured (H1), OI variant NOT_RUN; back-adjustment effect
  NOT_RUN (no adjusted series built — description-only mandate). [OBSERVED/NOT_RUN]
- §14 questions: orientation transform (6J = 1/USDJPY — OBSERVED + FACT framing);
  intervention-dominance conditions (measured 2026 episode days OBSERVED; threshold
  model H5 NOT_RUN); risk-off×carry interaction (POSTULATED, NOT_RUN); BoJ regime
  breaks breaking relations (POSTULATED; two 2026 guideline changes FACT-titled,
  effects NOT_RUN).

---

### Defects / caveats register (this lane)

1. [OBSERVED] 8 serial months (delivery 2025-10…2026-08) absent from raw → data lane's
   declared calendar roll rule NOT executable on this dataset for 2025-09…2026-08 rolls;
   approximation rolls quarterly→quarterly (coincides with liquid reality).
2. [OBSERVED] From 2026-08-31 the literal next-listed rule routes into near-dead serials
   (2026-10-01: 6JX6 26 lots vs 6JZ6 118,886) — declared rule defective for 6J even when
   executable; future backtests must use the HMUZ rule (H1).
3. [OBSERVED] Deep daily bars settlement-derived (81–99% flat per contract) — reference
   and curve use only, never fill prices.
4. [OBSERVED] Expired-contract files are clipped at the delivery-month start
   (endDateTime construction), so residual old-contract trading after the declared roll
   session (e.g. 6JU6 Sep-01→14-2026) is invisible in raw.
5. [NOT_RUN] Intraday = RTH-only 30-D windows; 1-min = 2-day snapshots; no Asia/London
   data — the sessions where BoJ decisions and Tokyo fixes actually trade.
6. [NOT_RUN] CME official numeric spec/fee/SPAN tables transport-blocked (re-confirmed
   2026-10-02 via web-reader fallback: page renders, JS tables empty); specs rest on
   broker secdef (OBSERVED) + vendor mirrors (secondary).
7. [NOT_RUN] BoJ 2026 policy-rate levels not verified (statement PDFs unfetchable);
   only decision titles/dates are FACT.
8. [OBSERVED] Vendor volume scale: quarterly contracts full-scale (40k–135k
   lots/day front), serials effectively untraded — use volume shares, not levels.
9. [NOT_RUN] Japan CPI schedule (stat.go.jp 404×3), press-cited record Q3-2026
   intervention total pending MOF quarterly page — both flagged for $0 re-fetch.

---

### CoT revision-policy verification note (added 2026-10-02, round co-owner-review-fix-1, lane HANDOFF-RESEARCH)

The CoT "not revised" wording in §2 driver-map row 7, §4 CoT calendar row and §6 missing-data CoT row (this dossier) was re-verified against primary CFTC
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
