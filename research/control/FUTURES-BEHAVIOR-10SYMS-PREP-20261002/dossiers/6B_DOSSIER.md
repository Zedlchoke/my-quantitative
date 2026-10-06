# 6B_DOSSIER — British Pound Futures (CME 6B)

- Symbol: 6B (CME British Pound futures, tradingClass `6B`; symbol field GBP in secdef; not
  to be confused with mini 6B ("BPM") or options)
- Exchange: CME (via CME Globex); vendor endpoint IB TWS API, timezone US/Central
- Generated_utc: 2026-10-02 (lane local; all web access dates below are 2026-10-02)
- Author lane: SYMBOL-DOSSIER-6B, task FUTURES-BEHAVIOR-10SYMS-PREP-20261002 (PREP ONLY —
  no scored runs, no PnL/event-studies/sweeps, no GO)
- Inputs:
  - owner_framework/6B_RESEARCH_FRAMEWORK.md sha256
    `510032d400273c16b2feef03dd05e6e8670e2026d75e411cba8b914949fd40ed`
    (owner_framework/SHA256SUMS.txt); 00_MASTER_FRAMEWORK.md sha256
    `a75571b8017b13b5ff6552755d1334b03db640ebc26a6b4c9ad4323ca16d3c74`
    (owner research document — every claim inside is a HYPOTHESIS here)
  - research/control/FUTURES-DATA-10SYMS-V1/ (untracked snapshot, read-only):
    FINAL_REPORT.md sha256 `9722d3a123da7e3bc1546293705c241aab7eb938fed38a08f2f07600926e4260`,
    S1_IDENTITY.json `d217ab9dcd865765e1bcae8f8131dee2f7f200cd90c07403280134da32b05822`,
    S9_INDEPENDENT_VERIFY.md `cb5c916992f9f45971d1cac4b1863e1482d464d8b7412745520ee4c22a678e00`,
    HANDOFF.json `4d79f0424b3a7467d2fb5c9a22f3f8298560993018b55206bff019a6866a55f6`,
    S6_VALIDATION.json `0dd3e76b649cd6f403cebeaa4fe5bca5c5922823c70f199bbe064b0e38a700c`,
    S6_FRONT_SPREADS.json `3724a6333bef26cff265cae7ee0c2e544803554f812990a397df1b18bbe59511`,
    costs/SPECS_MARGINS_PUBLIC_2026-10-02.md
    `e8174857f463821e85d0352335c06368939ab65b1784509956cd6339952330a3`,
    costs/IBKR_futures_commissions_2026-10-02.json
    `44829cbdab8e4d747257aa7bc427db68a10ec031c95a1ed8a36d8c22b4b4950f`
  - Raw (read-only): ~/.my-quantitative-data/futures-10syms-v1/raw/ files `6B_*`
    (115 files = 20 contracts × 5 series + 3 probe contracts [front 6BV6 / next 6BX6 /
    nearest-expired 6BU6] × 5; plus `6E_*`/`ES_*` daily files read-only for cross-asset
    descriptives)
  - Analysis (this lane): analysis/6B_descriptives.py → analysis/6B_descriptives.json
    (descriptive only, strict past/rolling windows, no back-adjustment)
- Claims taxonomy used everywhere below: FACT (sourced) / OBSERVED (raw+script+window) /
  POSTULATED (mechanism, unmeasured) / NOT_RUN (default; never inferred PASS).

## 1. Mechanics

- Underlying exposure: GBP/USD exchange rate; long 6B = long GBP vs USD. Contract unit
  62,500 British pounds. [FACT-secondary: TK Futures + AMP spec mirrors fetched by data lane
  2026-10-02, costs/SPECS_MARGINS_PUBLIC_2026-10-02.md §1] [OBSERVED corroboration: S1_IDENTITY
  6B — multiplier "62500" uniform on every resolved contract, currency USD, longName
  "British pound", validExchanges CME,QBALGO]
- Quote convention: USD per 1 GBP (same direction as spot GBP/USD; NOT inverted — unlike 6J).
  Snapshot recent closes 1.3102–1.3266 [FACT-secondary: TradingCharts quoted-units "US $ per
  British Pound", costs file §2] [OBSERVED: FINAL_REPORT 6B row; analysis panel real-volume
  closes span 1.2147 (6BZ5, 2020-era prints) – 1.3794 (6BH6, 2026); quarterly chain closed
  1.3191 on 2026-10-01].
- Tick/multiplier: S1 minTick 0.0001 ($6.25/contract at 62,500 GBP) — CONFLICTED in public
  broker tables: AMP "0.0001/$6.25" vs TK "regular 0.0002=$12.50, calendar spread
  0.0001=$6.25" (likely outright-vs-spread minimums and/or tick redesign history; CME
  rulebook unreachable — CME_BLOCKED_TRANSPORT, costs file §1). This dossier reports tick
  counts on the 0.0001 basis and flags the conflict wherever USD values depend on it.
  [FACT-secondary for both numbers; OBSERVED for S1 value; official adjudication NOT_RUN]
- Participants: banks/corporates (trade + FX-hedge flow), asset managers, macro funds, CTAs,
  market makers; natural hedgers = UK-trade corporates and GBP-asset holders; arbitrageurs
  bind 6B to GBP spot/forwards (CIP) and to the 6E cross. [POSTULATED: owner framework
  header; not measured here]
- Sessions & DST: Globex session 17:00 US/Central (day-1) → 16:00 CT (day-2) with a daily
  16:00–17:00 CT maintenance break; Sunday open 17:00 CT; liquid hours (RTH) 08:30–16:00 CT
  Mon–Fri. [OBSERVED: S1_IDENTITY 6B tradingHours/liquidHours strings, e.g.
  "20260930:1700-20261001:1600", "20261003:CLOSED", liquidHours "20261001:0830-...-1600",
  fetched 2026-10-02; timeZoneId US/Central on all active contracts] DST handling verified at
  bar level: 6B H1 bars carry correct ISO offsets across the 2025-11-02 DST flip (e.g.
  6BZ5 hourly 2025-10-17 bar −05:00 CDT, 2025-11-28 bar −06:00 CST). [OBSERVED: raw 6B files;
  S6_VALIDATION 6B series windows; S9 method note (50-file DST check covered NQ/CL/6J, method
  applicable)]
- Holidays: CME holiday calendar NOT fetchable (cmegroup.com HTTP 403 to non-browser
  clients; web-reader fallback rate-limited this session) → official holiday list NOT_RUN.
  Observable proxy: weekends CLOSED in S1 strings; 7 contracts' zero-volume gaps around US
  holidays visible in raw. Expiry-date anomalies below (§1 expiry) are consistent with US
  holidays in the business-day count. [OBSERVED for weekends; POSTULATED for holiday
  explanation]
- Delivery/first-notice/expiry: physically delivered FX (delivery on third Wednesday of the
  delivery month); trading ceases on the second business day immediately preceding the third
  Wednesday, at 09:16 CT (lastTradeTime in S1; TK spec "LTD (9:16a.m.) GLBX").
  [FACT-secondary: TK/Cannon via costs file §1] [OBSERVED: S1 lastTradeDate per contract +
  lastTradeTime 09:16 on all 37 resolved contracts; raw expiry_month = lastTradeDate
  yyyymmdd]. Rule check vs a Mon–Fri business-day approximation: 17/20 snapshot contracts
  match exactly; 3 differ by −3 days (6BF7 2027-01-15, 6BG7 2027-02-12, 6BF8 2028-01-14 —
  each a Monday whose preceding Friday was the naive answer), consistent with US holidays
  (MLK Day / Presidents' Day) inside the 2-business-day count. [OBSERVED: analysis
  `expiry_rule_check`; holiday explanation POSTULATED — CME calendar NOT_RUN]
- Price limits: none found in reachable sources; FX futures are not limit-priced in the
  broker spec mirrors reviewed. [NOT_RUN — CME rulebook unreachable; not asserted]
- Listed months: monthly serials + quarterlies. [OBSERVED: S1 active_chain 2026-10-02 —
  24 consecutive monthly listings 2026-10..2028-09, then quarterly cycle 2028-12..2031-12
  (H/M/U/Z); corroborated by TK "Six months in the March quarterly Cycle" being an
  under-statement of the current chain] Listing calendar known years ahead → roll decisions
  on it are PIT-legal. [OBSERVED]
- Liquid maturities: essentially ONLY the quarterly (H/M/U/Z) contracts. Measured RTH
  volume by contract type, 2025-09→2026-10: quarterlies ≥99.87% of volume every month
  (busiest quarterly ≥99.5% of month volume); serial months printed 140–862 contracts per
  MONTH (≤0.13%) vs quarterly fronts 33k–77k contracts per DAY; the by-expiry "front"
  6BV6 (Oct-2026 serial) peaked at 237 contracts/day while the December quarterly 6BZ6
  printed 40k–62k/day the same month. Deferred serials (2027-04..2028-01) are all-volume-0;
  6BF7/6BG7 have exactly one 16-contract print (2026-07-01). [OBSERVED: analysis
  `monthly_volume_by_contract_type`, `contract_panel`, `quarterly_vs_serial`]
- Liquidity migration front→next (master Q6): at each of the 4 measured quarterly rolls the
  OLD quarterly still printed 17.6k–58.4k contracts on the declared roll session while the
  NEXT quarterly printed only 28–572; the next quarterly first reached front-scale (≥10k/day)
  8–9 sessions AFTER the declared roll date (2025-12-10, 2026-03-11, 2026-06-10, 2026-09-09),
  i.e. ~5 days before the old contract's last trade. The old contract's bars are cut at the
  fetch boundary (endDateTime = day-1 of expiry month), so old-side volume inside its expiry
  month is NOT observable → exact crossover date NOT_RUN. [OBSERVED: analysis
  `liquidity_migration_quarterly`, window 2025-09..2026-10; limitation explicit]
- PIT contract selection + roll rule: baseline = data lane's declared rule — hold until the
  last session BEFORE day-1 of the expiry month, roll to the next listed contract at that
  close. [FACT: FINAL_REPORT §"Quy tắc roll khai báo"] For 6B this project measures TWO
  applications:
  - (a) LITERAL next-listed (includes serials): NOT executable as a liquidity chain — the
    serial legs it would hold are 2–3 orders of magnitude thin (e.g. holding 6BV6 through
    Sep-2026: median 21 contracts/day vs 37,052/day on the quarterly chain same window).
    [OBSERVED: analysis `literal_rule_serial_front_windows`] Additionally NOT
    reconstructable historically on this snapshot: it contains ZERO expired serial
    contracts (Jan/Feb/Apr/May/Jul/Aug-2026 delivery all absent — S1 expired_walk stepped
    quarterly only), so the literal rule's serial targets for the 2025-12..2026-09 rolls do
    not exist in-dataset. [OBSERVED: analysis `snapshot_hole_serial_months`; listing of
    those serials in 2025-26 is POSTULATED from the current listing pattern]
  - (b) QUARTERLY-ONLY adaptation (roll HMUZ→next HMUZ at the same declared timing): matches
    measured liquidity; this is the chain all §3 descriptives below use. [OBSERVED]
    Alternatives: volume-crossover roll (constructible PIT from the new contract's own past
    RTH volume, but only 4 real-era rolls exist to describe it), OI roll (OI NOT in raw →
    NOT_RUN). [NOT_RUN]
- Roll cost (observable, causal construction, description only — NOT a tradable cost):
  adjacent-contract close gaps at the 4 real-era quarterly roll sessions, both closes on
  real-volume bars: −2 / +5 / −3 / +3 ticks (−12.50 / +31.25 / −18.75 / +18.75 USD per
  contract at $6.25/tick) = −0.015% / +0.037% / −0.022% / +0.022% of level; annualized
  −0.06% / +0.15% / −0.09% / +0.09%. Sign MIXED → no persistent contango/backwardation
  drift in this window; per-roll magnitude ≈ half a typical spread-day's range. [OBSERVED:
  analysis `declared_rule_rolls_quarterly_chain`, rolls 2025-11-28, 2026-02-27, 2026-05-29,
  2026-08-31] (GC dossier found same-style raw gaps; NOT back-adjusted, no stitching jump
  treated as alpha.)
- Forward roll calendar (quarterly chain, from listing dates + session calendar):
  6BZ6→6BH7 declared roll 2026-11-30 (if a session), 6BH7→6BM7 2027-02-26, 6BM7→6BU7
  2027-05-28. [OBSERVED: S1 dates + rule; session-day confirmation NOT_RUN (holiday
  calendar)]

## 2. Causal driver map

Buckets per 00_MASTER_FRAMEWORK §3 relevant to 6B; each row: source → mechanism → predicted
sign/horizon → regime dependency → confounders → falsification test → PIT data source
(primary official + access date). Evidence class marked per row.

| # | Driver (bucket) | Source → mechanism → prediction | Regime | Confounders | Falsification | PIT source (primary) | Class |
|---|---|---|---|---|---|---|---|
| 1 | BoE-Fed policy differential (Macro) | MPC/FOMC decisions & guidance → relative short-rate path → CIP-motivated GBP/USD repricing → GBP up on hawkish-relative surprise; horizon minutes–weeks | Strengthens when policy paths diverge; weak when both on hold | Global risk tone moving both legs; USD liquidity | Relative surprise (BoE vs Fed) fails to predict next-day direction ≥55% in walk-forward | BoE MPC calendar/minutes (bankofengland.co.uk, acc. 2026-10-02) + Fed FOMC (federalreserve.gov, acc. 2026-10-02); market-implied expectations NOT in corpus | Mechanism POSTULATED; calendar FACT; surprise data NOT_RUN |
| 2 | UK inflation/wages (Macro) | ONS CPI/average-earnings → BoE reaction function → rate-path repricing; persistent when "inflation persistence" high (framework §15) | High-persistence regimes → persistent drift; low → mean-reversion | Simultaneous US data; revisions | UK surprise sign does NOT condition 3-day drift sign | ONS release calendar + first prints (ons.gov.uk — NOT fetchable this session: 2×404 → NOT_RUN; 07:00-London time POSTULATED) | POSTULATED; PIT source NOT_RUN |
| 3 | UK growth/PMIs (Macro) | S&P Global PMIs, ONS GDP → relative-growth FX channel → GBP up on beat; horizon days | Risk-on amplifies | USD cycle dominance | Beats fail to add explanatory power beyond US data | S&P Global PMI release page (NOT fetched — NOT_RUN); ONS (NOT_RUN) | POSTULATED; NOT_RUN |
| 4 | Fiscal policy / gilt stress (Macro, UK-specific) | Fiscal-credibility shocks → gilt yields ↑ + GBP ↓ (2022 mini-budget archetype) → underperformance vs EUR (framework §15) | Dominates when UK fiscal credibility is the marginal story; rare | Global risk-off lifting USD broadly (6E falls too) | GBP/6E ratio does NOT widen on UK-specific fiscal events | HM Treasury budget calendar (GOV.UK — NOT fetched this session); DMO auction calendar | POSTULATED; UK-fiscal events calendar NOT_RUN |
| 5 | Risk sentiment / USD cycle (Macro/Cross-asset) | Global risk appetite → GBP beta ≈ risk currency; USD-strength factor → GBP down; horizon intraday–days | Crisis: co-moves with EUR, decouples on UK idiosyncratic news | GBP-specific news during global moves | GBP beta to ES is unstable/sign-flipping (measured rolling corr already spans −0.02..0.65) | ES in corpus (OBSERVED available); VIX NOT in corpus | Mechanism POSTULATED; 6B↔ES corr OBSERVED 0.31 front-scale era |
| 6 | Energy/import terms of trade (Fundamental) | UK net-energy-importer: energy ↑ → GBP trade balance/GDP headwind → GBP down; horizon weeks | Matters in large oil moves | USD also strengthens on energy shocks (confounds sign) | Oil-price changes fail to predict GBP vs EUR differentially | EIA spot CL (public, PIT daily) — in DATA lane notes; NOT in this raw corpus | POSTULATED; NOT_RUN |
| 7 | 6E / EUR-GBP cross (Cross-asset) | EUR share of GBP variance; relative-value carrier for UK-vs-eurozone idiosyncrasy | Relation stable in calm, breaks in Brexit-style shocks | Common USD driver (remove by ratio) | Rolling 63d corr leaves <25% idiosyncratic residual | 6E in corpus (OBSERVED available) | OBSERVED: 6B↔6E corr 0.837 front-scale era (rolling 0.75–0.91) |
| 8 | CoT positioning (Positioning) | Spec net-long extremes → crowded-position unwinds amplify reversals | Matters at extremes | Release Fri ≠ position Tue; futures-only (not cash FX) | Extremes do NOT precede elevated |r| | CFTC CoT (cftc.gov, weekly Fri 15:30 ET — schedule NOT fetched this session → NOT_RUN) | POSTULATED; data NOT_RUN |
| 9 | Term structure / calendar spread (Term structure) | Front-vs-next quarterly spread ≈ USD-GBP rate differential + basis; small measured gaps ±2–5 ticks/roll | Widens when policy divergence widens | Thin serial quotes distort any non-quarterly spread | Spread sign does NOT track rate-differential changes | Own raw panel (OBSERVED); rate data NOT in corpus | OBSERVED (§1 roll gaps); carry mapping POSTULATED |
| 10 | Roll-window microstructure (Microstructure) | Liquidity flips old→next quarterly ~8–9 sessions AFTER declared roll date; declared-date roll trades a 100x-thinner new contract | Stable quarter-cycle pattern in 4/4 measured rolls (min sample) | Old-side volume hidden by fetch cut (NOT_RUN) | A crossover-timing rule is unstable (>±5 sessions) across future rolls | Own raw panel RTH volume (OBSERVED) | OBSERVED (§1 migration) |
| 11 | Session effects (Microstructure) | London is GBP's prime session; Asia thin; US-data window 07:30–08:30 CT | BoE (London noon) and ONS (07:00 London) land OUTSIDE RTH bars | RTH-only bars hide all of it | (not testable on this snapshot) | Needs Globex-hours intraday (Databento-class) — NOT in corpus | NOT_RUN (bars are RTH-only; hidden-gap proxy OBSERVED §3) |
| 12 | Scheduled macro releases (Event-driven) | US CPI/NFP 08:30 ET, FOMC 14:00 ET, BoE MPC London noon, ONS 07:00 London → vol clusters at fixed times | High-beta in hawkish/dovish pivot regimes | Time-of-day conventions unverified for BoE/ONS this session | Event-time vol does NOT exceed matched non-event times | BLS CPI schedule + 08:30 release FACT (bls.gov/schedule/news_release/cpi.htm, acc. 2026-10-02); FOMC dates FACT; BoE dates FACT; NFP dates NOT_RUN; ONS NOT_RUN | Calendar FACT; reaction measurement NOT_RUN (event studies out of scope for PREP) |

## 3. Behavior (measured where legal)

All numbers below: [OBSERVED: analysis/6B_descriptives.py → 6B_descriptives.json; sample =
20 6B contracts, daily TRADES 6Y files, useRTH=true (bars cover 08:30–16:00 US/Central only
— Asia + London + the 08:30 ET US-data block are NOT inside daily or hourly bars; only the
open-vs-prior-close gap sees them); settlement-derived bars (v=0, o=h=l=c) separated, never
silently mixed]. "Front-scale era" = quarterly-chain front RTH volume ≥10,000 contracts/day:
2025-09-11 → 2026-10-01, 239 trading days, median front volume 33,900/day (n≥25k: 199 days;
n≥50k: 39). Before 2025-09-11 the per-contract files are settlement-derived or sporadic tiny
prints (e.g. 6BZ5 median 28 contracts across its 178 scattered print-days 2024-08..2025-09) —
the real-volume quarterly chain is only
~13.5 months, consistent with the FINAL_REPORT "~14 months" wall (6B precise start
2025-09-11, not the generic 2025-08).

- Session behavior: NOT measurable where it matters most. GBP's prime session (London
  morning; ONS 07:00 London and BoE 12:00 London events) is entirely outside useRTH bars;
  Asia session likewise. [NOT_RUN — data window; the hourly files are 08:30–16:00 CT only,
  20 files, 11 with any real volume; the 5 liquid quarterlies provide ~30-day patches each:
  6BZ5 2025-10-17..11-28, 6BH6 2026-01-15..02-27, 6BM6 2026-04-17..05-29, 6BU6
  2026-07-21..08-31, 6BZ6 2026-08-20..10-01; no continuous multi-year intraday]. What IS
  measurable (RTH internal distribution, 6BZ6 30-day patch, 2026-08-20..10-01): volume
  concentrates 09:00–11:00 CT (09:00 22.3%, 10:00 18.6%, 11:00 12.0%), a 13:00–14:00 CT
  shoulder (15.5%/8.0% — the FOMC 13:00 CT statement window), thin first (08:30, 10.0%) and
  last (15:00, 3.4%) hours. [OBSERVED: `hourly_rth_profile_30d`; single-contract 30-day
  sample, not a stable claim]
- Hidden-session (overnight+London) gap: RTH open vs prior RTH close on the quarterly chain,
  normalized by trailing-20d mean |daily ret| (strict past, window ends prior session).
  Front-scale era (n=239): median −1 pip (0.0001), std 0.301%, q05..q95 −0.54%..+0.47%,
  skew +0.33; across the full chain 11.9% of days gap ≥2× trailing mean. Biggest all-era
  gaps cluster Sep–Nov 2022: −5.02% (2022-09-23), +2.76% (2022-10-13), +2.74% (2022-10-17),
  +2.58% (2022-11-10) — all on settlement-derived marks (rv=0, magnitude unreliable), and
  the dates coincide with the UK "mini-budget"/gilt-intervention episode (event context
  POSTULATED — not independently sourced this session; the measurable claim is only the
  mark-to-mark gap). [OBSERVED: `overnight_hidden_session_gap`]
- Volatility/trend: front-scale-era daily returns (roll-boundary days excluded; within-
  contract close-to-close, no stitched jumps): n=239, mean −8.1e-05, std 0.3892%
  (annualized 6.18%), q05..q95 −0.70%..+0.65%, min −0.99%, max +1.15%, skew +0.07 —
  near-symmetric, no fat-tail catastrophe inside the window. Rolling 63d realized vol (full
  quarterly chain, mixed-quality eras): min 0.286%, median 0.438%, max 1.346% daily — the
  max windows sit in the 2022 settlement-marks era, treat as upper-bound-ish descriptive.
  Volatility clustering mild: |ret| lag-1 autocorr 0.113 front-scale era (0.253 full chain),
  return lag-1 autocorr 0.039 (no daily mean-reversion/momentum signature). [OBSERVED:
  `front_chain_quarterly_stats`]
- Event behavior: NOT_RUN by scope (no return-based event studies in PREP) and NOT measurable
  intraday (~10-month patchy H1). The only event-adjacent descriptive: the 2022 gap cluster
  above.
- Curve/term structure: quarterly-to-quarterly roll gaps mixed-sign ±2–5 ticks over the 4
  real-era rolls (§1); annualized ±0.06–0.15% — no persistent carry direction in-window.
  Calendar-spread levels (front-minus-next-quarterly continuous series): NOT_COMPUTED beyond
  the roll-date gaps (deferred-contract quotes before their liquid window are
  settlement-derived; a full daily spread series would mostly measure the vendor's
  settlement marks, not a tradeable spread). [OBSERVED for roll gaps; NOT_RUN for daily
  spread series]
- Seasonality: NOT_RUN as a claim. Front-scale era is 13.5 months (every calendar month n≤2);
  full-chain by-month stats are settlement-era contaminated. Weekday cells (front-scale era,
  descriptive only): Mon–Fri mean daily ret −0.082%..+0.083%, vol 0.32%..0.46% — no day
  dominates. [OBSERVED cells; no seasonal claim]
- Cross-asset: daily returns of 6B vs 6E quarterly chains: corr 0.837 front-scale era (n=239;
  rolling-63d 0.752–0.910, n=176 windows); 6B vs ES 0.308 (rolling −0.022..0.650) — EUR is
  the dominant co-mover (shared USD factor), ES beta unstable (risk channel present but
  regime-dependent). Description only, unadjusted chains. [OBSERVED:
  `cross_asset_returns`]
- Liquidity/spread: quarterly-front BID/ASK daily closes (non-synchronous, close-to-close
  proxy — NOT an executable spread), matched to the quarterly chain, 465 days 2024-11-29 →
  2026-10-01, 0 crossed: median 2 ticks = $12.50/contract, p90 $12.50 on front-scale days
  ($37.50 all-days incl. deferred-quote rot). Data lane's 20-day front probe (S6, front =
  the thin 6BV6): median 3 ticks = $18.75. PUBLISHED/daily-proxy costs ≠ MEASURED execution
  costs. [OBSERVED: `bid_ask_1y`; S6_FRONT_SPREADS] Broker margins (public, broker-class,
  2026-10-02): NinjaTrader day $500 / maintenance $2,000 / initial $2,200; AMP overnight
  maintenance $1,870 / day $467.50. IBKR commission standard futures $0.85/side + exchange
  + regulatory; 6B exchange fee NOT_FETCHED (JS table didn't render; CME blocked).
  [FACT-secondary: costs file §3 + IBKR commissions JSON, acc. 2026-10-02]

## 4. Event calendar

All times: exchange tz = US/Central (CT); UTC conversions shown; "effective vs available"
notes what a strategy could have known when. Access date for all fetched pages: 2026-10-02.

| Event | Schedule (verified) | Time | CT / UTC | PIT properties | Source | Class |
|---|---|---|---|---|---|---|
| BoE MPC announcements 2026 | Feb 5, Mar 19, Apr 30, Jun 18, Jul 30, Sep 17, **Nov 5**, Dec 17 | 12:00 London convention (page does NOT state a time — POSTULATED) | 06:00 CT / 11:00–12:00 UTC (BST/GMT) | Decision + summary + minutes simultaneous on release; MPR in Feb/Apr/Jul/Nov; archive of decisions is a stable URL per meeting | bankofengland.co.uk/monetary-policy/upcoming-mpc-dates (fetched) | Dates FACT; time POSTULATED |
| BoE MPC 2027 | Feb 4, Mar 18, Apr 29, Jun 17, Jul 29, Sep 16, Nov 4, Dec 16 | (as above) | (as above) | (as above) | same page | FACT |
| FOMC 2026 (USD leg of the differential) | Jan 27-28, Mar 17-18*, Apr 28-29, Jun 16-17*, Jul 28-29, Sep 15-16*, **Oct 27-28**, Dec 8-9* (*=SEP) | 14:00 ET statement convention (page does NOT state — POSTULATED) | 13:00 CT / 18:00–19:00 UTC | Statement + SEP simultaneous; minutes +3w | federalreserve.gov/monetarypolicy/fomccalendars.htm (fetched) | Dates FACT; time POSTULATED |
| FOMC 2027 | Jan 26-27, Mar 16-17*, Apr 27-28, Jun 8-9*, Jul 27-28, Sep 14-15*, Oct 26-27, Dec 7-8* | (as above) | (as above) | (as above) | same page | FACT |
| US CPI (BLS) 2026 | Jan 13, Feb 13, Mar 11, Apr 10, May 12, Jun 10, Jul 14, Aug 12, Sep 11, **Oct 14**, Nov 10, Dec 10 | 08:30 (page lists "08:30 AM" on every entry; ET per BLS convention) | 07:30 CT / 12:30–13:30 UTC | First print revised; SA indexes re-seasonalized annually — vintage-sensitive for strict PIT | bls.gov/schedule/news_release/cpi.htm (fetched) | FACT |
| US NFP / Employment Situation (BLS) | NOT fetched this lane (URL attempt 404) | 08:30 ET convention (POSTULATED) | 07:30 CT | Payrolls revised twice + annual benchmark — highly vintage-sensitive | bls.gov/schedule/news_release/empsit.htm (NOT_FETCHED) | Dates NOT_RUN; time POSTULATED |
| UK CPI / wages / GDP / PMIs (ONS & S&P Global) | NOT fetchable this session (ons.gov.uk 2 attempts → 404) | 07:00 London convention (POSTULATED) | 01:00–02:00 CT | ONS publishes first estimates then revises (vintages matter); release calendar is the PIT anchor | ons.gov.uk/releasecalendars (NOT_RUN this session) | NOT_RUN |
| UK fiscal statements (Budget / Autumn Statement) | NOT fetched | — | — | GBP-specific tail-risk events; scheduled ~6-monthly by HM Treasury | GOV.UK (NOT_RUN this session) | NOT_RUN |
| CFTC CoT (GBP futures) | Weekly, Fri 15:30 ET convention (schedule NOT fetched) | 15:30 ET POSTULATED | 14:30 CT | Release ≠ position date (data as of prior Tue) — a 3-day lag by construction | cftc.gov (NOT_RUN) | NOT_RUN |
| 6B contract events | Quarterly-chain declared rolls ahead: 6BZ6→6BH7 2026-11-30(±holiday), 6BH7→6BM7 2027-02-26, 6BM7→6BU7 2027-05-28; last trades: 6BZ6 2026-12-14, 6BH7 2027-03-15; serial expiries 6BV6 2026-10-19, 6BX6 2026-11-16 (thin — market ignores them) | last trade ceases 09:16 CT | — | Listing calendar known years ahead → roll decisions PIT-legal | S1_IDENTITY.json chain + raw bars | OBSERVED |

## 5. Hypotheses (ranked by testability × causal plausibility — NOT by PnL)

All hypotheses below are PREP-stage proposals; none has been run, scored or validated.
FX-spot→6B-futures transfer is flagged where relevant: futures differ from spot by CIP
basis, quarterly roll (measured ±2–5 ticks/roll) and commissions/spread ($12.50/contract
median daily-proxy spread + $0.85 + unfetched exchange fee) — an FX-spot corpus idea is
never "already valid" on 6B. Corpus-1200 line/ID mapping for framework §15 items: NOT_PROVIDED
in dispatch; framework file sha256 recorded in header.

**H1 — Roll-timing / contract-selection microstructure (rank 1: measured on data in hand).**
When the 6B quarterly front approaches its declared roll session (last session before day-1
of its delivery month), the next quarterly is still 2–3 orders of magnitude thinner at that
session (28–572 contracts vs 17.6k–58.4k) and only reaches front-scale ~8–9 sessions later;
therefore a roll rule that switches at the *volume-crossover* (new contract's own trailing
volume, PIT-legal) should track true liquidity better than the calendar rule, over
horizon = one quarter per decision.
- Observable PIT condition: new quarterly's trailing-5d RTH volume ≥ x% of old's trailing-5d
  (x: PARAM-GAP — only 4 real-era rolls exist to calibrate; do not invent).
- Predicted effect: crossover occurs inside the old contract's expiry month (~2nd week);
  holding-old until crossover captures more liquid sessions. Economic mechanism: liquidity
  network effects — MM quotes concentrate where open interest sits; hedgers follow; the
  calendar rule is an artifact of the data lane's generic rule, not of 6B's microstructure.
- Entry/exit/holding: decision daily at close; switch old→next-quarterly at the first close
  satisfying the condition; TP/SL: none (rule, not a trade); time: max-hold to old's last
  trade minus 1 session (forced exit).
- Direction: long/short agnostic (execution-quality hypothesis).
- Universe/roll: quarterly HMUZ chain only (serials excluded — measured 2–3 OOM thinner);
  sizing: 1 contract unit (descriptive); cost model: measured spread $12.50 + roll gap ±2–5
  ticks per roll; invalidation: crossover date varies >±5 sessions across future rolls, or
  old-side volume (unobservable here — files cut at day-1 of expiry month) shows the flip
  happened before the declared date.
- Counter-hypothesis: liquidity flips exactly at month-end (calendar) and the measured
  "8–9 sessions late" is a fetch-window artifact of the NEW contract's early-September
  volume ramp.
- Data requirements: daily per-contract RTH volume ≥24 months (have ~13.5 front-scale
  months; 4 rolls measured); floor: ≥12 quarterly rolls before any stability claim.
  Failure conditions: only-4-rolls sample; settlement-derived old bars.

**H2 — Relative BoE-vs-Fed repricing (framework §15 #4; rank 2: calendar verified, data
missing).** When a UK-vs-US macro-surprise differential (BoE hawkish-relative surprise, or
UK CPI/wages above consensus while US data at/below) occurs, GBP/6B should drift up over
1–5 days (rate-differential channel), strongest in high-inflation-persistence regimes,
weakest/reversed in risk-off (USD bid swamps idiosyncrasy).
- Observable PIT condition: standardized relative surprise (needs consensus + actual with
  release timestamps). Entry: next-bar/session close after release; exit: 1–5 sessions;
  TP/SL: none at hypothesis stage; direction: long GBP on positive relative surprise;
  universe/roll: quarterly chain; sizing: vol-scaled (rolling-20d, strict past); cost model:
  $12.50 spread + $0.85+fee per side + 1 roll per quarter avg.
- Invalidation: sign consistency ≤50% in walk-forward; counter-hypothesis: BoE surprises are
  priced within the London session (not measurable on RTH-only bars — H2 requires Globex
  intraday or at minimum daily bars with London coverage).
- Data requirements (floor): PIT consensus/actual for BoE + UK CPI/wages + US CPI/NFP ≥3y
  with release timestamps (NOT in corpus); daily true-volume chain ≥24 months (have 13.5);
  M1 for first-reaction work (blocked). Failure: revised data used as-known-then (ONS
  vintages).

**H3 — UK fiscal-credibility shock → GBP underperforms EUR (framework §15 #2; rank 3).**
When a UK-specific fiscal/gilt event occurs (Budget risk events, gilt yield spike with no US
counterpart), 6B should fall more than 6E (6B/6E ratio down) over days–weeks; mechanism:
fiscal-dominance premium priced into UK rates → GBP discount; strongest when BoE credibility
questioned, weakest in global risk-off (both fall).
- Observable PIT condition: event flag from HM Treasury calendar + gilt-yield jump filter;
  relative-value expression: short 6B / long 6E (delta-neutral-ish USD leg: not exact —
  multipliers differ: 62,500 GBP vs 125,000 EUR; ratio ≈ 2:1 contracts).
- Entry/exit: at next close after event flag; hold to fixed horizon or ratio reversion;
  TP/SL: PARAM-GAP (no measured event sample); sizing: 2×6B vs 1×6E per unit; cost model:
  2 spreads on 6B + 1 on 6E + 2 rolls/quarter total.
- Invalidation: 6B/6E idiosyncratic residual (1−corr² ≈ 30% of front-scale variance, rolling
  corr 0.75–0.91 measured) is NOT elevated on UK fiscal dates; counter-hypothesis: EUR
  gilts-linked flows dominate the cross during EU stress, flipping the relative story.
- Data requirements: UK fiscal event calendar (NOT_RUN to fetch), gilt yields PIT (NOT in
  corpus), 6E chain (HAVE, read-only measured).

**H4 — London-session breakout by macro regime (framework §15 #3; rank 4: NOT measurable on
this snapshot).** GBP range breaks during the London morning (02:00–08:00 CT) should
continue into the US session when the monetary regime is directional (BoE/Fed cycle moving),
and fade in on-hold regimes. NOT_RUN now: the London session is entirely outside useRTH
bars (hidden-gap proxy is the only trace). Entry/exit/TP/SL/time: PARAM-GAP pending
Globex-hours intraday data (Databento-class ohlcv-1m per framework §10); universe: quarterly
chain; costs as above; invalidation: breakout follow-through does not survive entry-delay
+1–5 minutes. Data floor: ≥2y M1 with full Globex hours + regime tags.

**H5 — US-macro-window hidden-gap reaction (rank 5: partial proxy measurable, event studies
out of PREP scope).** On BLS 08:30 ET CPI days (12 of 2026's dates verified), the 6B RTH
open-vs-prior-close gap (which embeds the 07:30 CT release minute) should be larger in
magnitude than non-release days; descriptive |gap| distributions conditioned on the VERIFIED
release calendar are computable on the front-scale era (~13 months, ~12 CPI dates) as a
PREP-legal descriptive (no PnL, no strategy). Mechanism: pre-positioning + release
repricing. NOT an executable signal without intraday (entry timing inside the gap is
unknowable). Invalidation: gap distribution on release days ≈ non-release days. Status:
design ready, measurement NOT_RUN this cycle (kept descriptive-only).

## 6. Missing data table

| Need | Have | Source | Period | Schema | PIT properties | License/cost | Blocker | Next action |
|---|---|---|---|---|---|---|---|---|
| Multi-year per-contract intraday (M1/H1, full Globex hours) — top drivers #1 (BoE/Fed differential) & #4 (London session) | ~30-day RTH-only patches per liquid quarterly (5 patches, 2025-10→2026-10); London/Asia absent | Databento ohlcv-1m + definition (framework §10) or CME DataMine | 2010-06+ per framework; ≥5y minimum | ts, raw_symbol, instrument_id, expiry, OHLCV, OI | exchange feed = release time; no revision | PAID — owner decision (no purchases in PREP) | entitlement wall (~10 months M1) | Owner decision on vendor; until then NOT_RUN |
| BoE/Fed/UK-US surprise vintages (consensus, actual, release ts) | Verified release CALENDARS only (BoE, Fed, BLS-CPI); no consensus/actual data | BoE/Fed/BLS primary + a consensus archive (e.g. Refinitiv/consensus panels — TBD, license) | ≥5y | event, ts_utc, consensus, actual, revised | first-print vintage required; revision trail | mixed free/PAID | consensus data not in corpus | Owner picks a licensed surprise source; ONS calendar re-fetch (404 this session) |
| True-volume daily front chain ≥24 months (DAILY_BT floor per FINAL_REPORT) | 13.5 months (2025-09-11→2026-10-01) | same vendors or prospective accumulation | 2019→present | per-contract daily TRADES w/ real volume | volume is of the day (usable next open) | as above | expired-secdef wall ~1y | vendor purchase or accumulate prospectively |
| OI per contract (OI-based roll alternative; CoT corroboration) | NOT in raw (no OI field) | CME/Databento statistics schema | ≥5y | date, conId, OI | daily release, revision-free mostly | with vendor package | not fetched | include in vendor spec |
| Gilts/FTSE/DXY/VIX PIT series (driver #4/#5 confirmation) | 6E + ES only (measured, read-only); cross-asset table otherwise NOT_RUN | official/ licensed sources TBD | ≥5y | daily OHLC + release ts | index revision policy varies | mixed | not in corpus | owner prioritizes after top-3 |
| 6B exchange fee + official tick adjudication | IBKR $0.85/side known; CME exchange fee NOT_FETCHED; tick 0.0001 (S1) vs 0.0002 (TK) unresolved | CME fee schedule + rulebook (cmegroup.com) | current | fee table; rulebook text | n/a | free (transport-blocked) | CME HTTP 403 to non-browser clients; web-reader rate-limited | retry via browser-class fetch next cycle, else keep flagged |

Top-3 causal-driver priority (per instruction): (1) BoE-Fed differential (needs surprise
vintages + intraday), (2) UK inflation/wages (needs ONS calendar + vintages), (3) fiscal
credibility/gilt stress (needs gilt yields + event calendar). The dossier is NOT conditional
on the full wishlist — H1/H5 partial descriptives run on data in hand.

## 7. Framework coverage

Master framework §1 ten questions (answer + class; NOT_RUN where unmeasured):

| # | Question | Answer | Class |
|---|---|---|---|
| 1 | Underlying economic exposure | USD per 62,500 GBP; long GBP/USD | FACT (spec) / OBSERVED (S1) |
| 2 | Hedgers/speculators/MMs/arbitrageurs | Corporates/banks hedge; macro funds/CTAs speculate; MMs quote; arbitrage binds to spot/forwards via CIP | POSTULATED (not measured) |
| 3 | Exchange, listing, hours | CME Globex 17:00→16:00 CT, Sun–Fri, 1h break; RTH 08:30–16:00 CT | OBSERVED (S1 strings) |
| 4 | Size/tick/currency/margin/settlement | 62,500 GBP; minTick 0.0001 ($6.25, public conflict 0.0002 flagged); USD-denominated; margins $500/$2,000/$2,200 (NT) — broker-class; physically delivered third Wednesday | FACT-secondary + OBSERVED (S1); official tick/fee NOT_RUN |
| 5 | Listed months; liquid expiries | Monthly ~2y + quarterly to 2031; ONLY quarterlies liquid (serials ≤0.13% of volume) | OBSERVED |
| 6 | Liquidity migration timing | Next quarterly reaches front-scale ~8–9 sessions AFTER declared roll date; old still 17k–58k at roll session; old-side inside expiry month unobservable | OBSERVED (4 rolls) + NOT_RUN (crossover exact date) |
| 7 | Dominant price behavior | Cash-arbitrage (CIP) + macro expectations dominate; storage/seasonality absent | POSTULATED (mechanism) |
| 8 | Which session matters most | London (by mechanism) — NOT measurable (RTH-only bars); within RTH: 09:00–11:00 CT | POSTULATED + OBSERVED (RTH patch only) |
| 9 | Tradeable contract per timestamp (PIT) | Quarterly HMUZ chain by trailing volume (serials excluded, measured); selection rule PIT-legal from own volume | OBSERVED |
| 10 | Vendor symbols → continuous reconstruction | localSymbol 6B{M}{Y} (20 in raw); reconstruction = quarterly chain with declared-roll timing, raw gaps recorded, NO back-adjustment; expired serials missing → literal next-listed rule NOT reconstructable pre-2026-10 | OBSERVED |

6B framework checklists (§1 foundation / §2 market-structure / §14 questions / §16 failure
modes → status):

- Fair value vs spot: CIP forward ≈ spot × rate differential; measured roll gaps ±2–5
  ticks/roll consistent with tiny carry — mapping POSTULATED, rate data NOT in corpus.
- Volume by session/expiry: by expiry OBSERVED (§3); by session NOT_RUN (RTH-only).
- Roll speed: old→next quarterly flip spans ~2 weeks around month boundary (4-roll sample)
  — OBSERVED (with old-side cut limitation).
- Spread widening overnight/near releases/near expiry: NOT_RUN (no synchronous quotes;
  daily BID/ASK proxy only).
- Opening/settlement/roll recurring effects: roll-date gaps measured (§1); settlement
  effects NOT_RUN.
- Most stable contract-selection rule: calendar-quarterly (matches measured liquidity);
  volume/OI roll comparison NOT_RUN (no OI) — OBSERVED-partial.
- Back-adjustment impact on trend signals: NOT_RUN (no back-adjustment performed by
  design; raw gaps small, ±0.02–0.04%).
- §14 UK-fiscal-dominance vs USD-factor, BoE-shock persistence, European-vs-risk-currency
  behavior, persistent-vs-mean-reverting UK releases: all NOT_RUN (need event data +
  longer windows; only 2022 gap cluster as circumstantial marks).
- §16 failure modes: Brexit-era breaks (outside data window — settlement marks only);
  fiscal jumps (2022 cluster settlement-marked); thin Asian-session liquidity (NOT
  measurable); cash/futures basis & roll (measured small, mixed sign).

**Status summary for downstream lanes:** 6B is SIGNAL_RESEARCH_READY per data lane (10/10);
this dossier adds: (a) liquidity is quarterly-only — any engine must implement the
HMUZ-chain adaptation, not the literal next-listed rule, and must treat the missing expired
serials as a snapshot hole; (b) declared roll timing precedes measured liquidity migration
by ~8–9 sessions (roll executability caveat, 4-roll sample); (c) real-volume daily chain is
13.5 months (2025-09-11 start) — DAILY_BT/INTRADAY_BT remain BLOCKED per FINAL_REPORT; (d)
all London-session behavior is NOT_RUN on this snapshot.
