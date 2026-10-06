# NG_DOSSIER — Henry Hub Natural Gas Futures (NG, NYMEX)

- Symbol: NG (tradingClass `NG`) · Exchange: NYMEX (CME Group DCM) · Quote: USD per MMBtu
- Generated (UTC): 2026-10-02 · Author lane: SYMBOL-DOSSIER-NG of FUTURES-BEHAVIOR-10SYMS-PREP-20261002 (PREP ONLY; no GO, no PnL/event-study/rule-sweep, no scored run)
- Inputs:
  - `owner_framework/NG_RESEARCH_FRAMEWORK.md` sha256 `285d010f833fdf8eef09a52ce0a766d69ed9443f01280bf843aa528ecbad9ae8`; `owner_framework/00_MASTER_FRAMEWORK.md` sha256 `a75571b8017b13b5ff6552755d1334b03db640ebc26a6b4c9ad4323ca16d3c74` (from `owner_framework/SHA256SUMS.txt`). Framework = HYPOTHESES, never facts/PASS.
  - `research/control/FUTURES-DATA-10SYMS-V1/FINAL_REPORT.md` + `S1_IDENTITY.json`, `S6_FRONT_SPREADS.json`, `S7_DEPTH_ACTIVE.json`, `S9_INDEPENDENT_VERIFY.md`, `costs/SPECS_MARGINS_PUBLIC_2026-10-02.md` (untracked snapshot, read-only; fetched 2026-10-02).
  - Raw (legal, read-only): `~/.my-quantitative-data/futures-10syms-v1/raw/` — 160 NG files: 29 contracts × (TRADES daily 6Y + H1 30D + M1 2D + BID/ASK daily 1Y) + 3D probes.
  - Own analysis: `analysis/NG_descriptives.py` → `analysis/NG_descriptives.json` (all OBSERVED numbers below come from there unless stated).
- Claims taxonomy used throughout: FACT (primary source + access date) / OBSERVED (script + window) / POSTULATED / NOT_RUN.

## 1. Mechanics

**Underlying exposure.** Physically delivered natural gas at the Henry Hub interconnect in Louisiana; EIA (primary): "Prices are based on delivery at the Henry Hub in Louisiana" and NG futures are "Official daily closing prices at 2:30 p.m. from the trading floor of the New York Mercantile Exchange (NYMEX)" (eia.gov/dnav/ng/ng_pri_fut_s1_d.htm, accessed 2026-10-02) — FACT. Contract unit 10,000 MMBtu; tick 0.001 USD/MMBtu = $10/contract — OBSERVED (S1_IDENTITY: multiplier "10000", minTick 0.001 uniform on every resolved NG contract; corroborated by NinjaTrader/AMP secondary tables fetched by the data lane 2026-10-02, `costs/SPECS_MARGINS_PUBLIC_2026-10-02.md`). CME-official spec page: NOT_RUN_CME_BLOCKED_TRANSPORT (cmegroup.com timed out/403 to non-browser clients both in the data-lane session and this session; web-reader fallback rate-limited).

**Participant map.** Producers, LDCs/utilities, power generators, LNG exporters, physical traders, commodity index funds, CTAs, calendar-spread traders — taxonomy per owner framework (POSTULATED; not measured). Margins context (broker-class, data lane 2026-10-02): NG maintenance ~$2,815-3,234/contract, day margin $1,000 (NinjaTrader 2026-08-31) / $3,234 (AMP 2026-10-02) — vendor-sourced FACT-class for the broker, CME SPAN NOT_RUN_CME_BLOCKED.

**Sessions, timezone, DST.** IB contract metadata (OBSERVED, S1): timeZoneId `US/Eastern`; tradingHours pattern `D 18:00 → D+1 17:00` (23h electronic session, implied 17:00-18:00 ET daily maintenance break); IB liquidHours `09:30–17:00 ET`; lastTradeTime `14:30` ET. Bar offsets in the raw are ISO-8601 with correct DST (-04:00 in summer, -05:00 in winter; S9 verified DST-correct offsets on 1-min files) — OBSERVED. CME-official session text and holiday calendar: NOT_RUN_CME_BLOCKED_TRANSPORT. Holiday effect on data: visible only as bar-date gaps; no official calendar cross-check — NOT_RUN.

**Delivery / expiry.** Monthly delivery; final trade = third-last business day of the month BEFORE the delivery month (NinjaTrader secondary source; OBSERVED conformance in raw: NGX26 [Nov-2026 delivery] lastTradeDate 2026-10-28; NGV25 [Oct-2025] final bar 2025-08-29; NGZ25 [Dec-2025] final 2025-10-31). Month-code convention: localSymbol letter = delivery month; raw field `expiry_month` actually holds lastTradeDate (one month earlier for NG) — S9 caveat C3, do not misread. Physical delivery (EIA + secondary sources); first-notice / delivery-mechanics detail beyond final trade: NOT_RUN (CME rulebook blocked). Price limits: NOT_RUN_CME_BLOCKED_TRANSPORT.

**Listed months & liquid maturities.** All 12 months, listed "current year + next 12 calendar years" (NinjaTrader secondary). In-snapshot universe: 29 monthly contracts, deliveries 2025-10…2028-02, contiguous — OBSERVED. Liquidity is concentrated in the front year: OBSERVED lifetime total volume by delivery: NGV26 3.11M, NGH26 2.89M, NGJ26 2.45M lots vs NGZ27 47k, NGG28 18k lots (deferred tails thin).

**Liquidity migration front→next (OBSERVED, `roll_table_matured_pairs`).** 13 matured pairs (deliveries 2025-10…2026-10). Volume crossover (first day next-delivery volume > outgoing, both >0, search capped at 90 days before the outgoing final session): 8/13 pairs crossed ≥84 days before final (values at/near the 90d cap — next/winter contract already dominated at window start); 5/13 no crossover within 90d (nearest month stayed dominant to the end); the latest cycle NGV26→NGX26 crossed only 6 days before final. Read: NG's most-active-by-volume contract is often a winter month months before the calendar front expires — calendar-nearest ≠ volume-max. OI-based migration: NOT_RUN (no open-interest field anywhere in raw).

**PIT contract selection + roll rule — CANONICAL BASIS (audit M2 fix, 2026-10-02).** The declared baseline reads "hold until the last session before day-1 of the expiry month, roll to the next listed contract at that close", where **expiry month = the month of the contract's LAST-TRADE date — the raw `expiry_month` header field (caveat C3); this is the single canonical basis adopted across `code/futbt/roll.py`, BACKTEST_LAUNCH_DRAFT.md §0 and INTEGRATION_SUMMARY.md.** [ERRATUM: this paragraph's original text read "expiry month" as the DELIVERY month and declared the rule "INFEASIBLE for NG as written". That reading is retired, not forked: an NG front's final trade (3rd-last business day of the month before delivery) precedes the last session of that month, so under a delivery-month reading the scheduled roll would bind at the front's own final session — the same rule's boundary consequence when applied to the other field.] On the canonical last-trade-month basis NG is feasible exactly like CL: the roll session (last session before day-1 of the LTD month) precedes the front's final session by ~4 weeks — e.g. NGX26: LTD 2026-10-28 → canonical roll 2026-09-30. OBSERVED reconciliation with this lane's implemented chain (nearest-listed delivery pick capped by each contract's data end; effective rolls = first chain day after each outgoing final bar: 2025-09-02, 2025-10-01, …, 2026-09-30): every expired NG file in the snapshot is cut exactly AT the canonical roll session (NGV25 → 2025-08-29, NGX25 → 2025-09-30, NGZ25 → 2025-10-31, NGU26 → 2026-07-31, …), so the chain's matured effective rolls reproduce the canonical roll sessions one session later and the §3 stats stand unchanged under the canonical basis. Residual divergences, disclosed: (i) NGV26 — the most-recently-expired contract — was fetched through its true final session (2026-09-29; LTD 2026-09-28) instead of being cut at the canonical boundary (2026-08-31), so the last matured roll (~2026-09-29/30) executed ~4 weeks later than canonical; (ii) the live front NGX26: this lane's chain holds it until its final session (~2026-10-28) whereas the canonical baseline rolled NGX26→NGZ26 at 2026-09-30 — ~1 month more front exposure on the live leg only. Any backtest arm (futbt engine) uses the canonical basis. Alternatives to test later: volume-crossover roll (would sometimes jump months early — changes exposure seasonally, see above), OI roll (NOT_RUN, no OI). No back-adjustment performed; continuous construction is for causal/descriptive use only.

## 2. Causal driver map

Columns: driver → mechanism → predicted sign/horizon → regime dependency → confounders → falsification test → PIT data source (primary, access date) → evidence class (for the driver's NG relevance being measured; the MECHANISM itself is POSTULATED unless noted).

| Driver | Mechanism | Sign / horizon | Regime dependency | Confounders | Falsification test | PIT source (primary + access date) | Class |
|---|---|---|---|---|---|---|---|
| Weather forecast revisions (GFS/GEFS/EPS vintages) | Expected HDD/CDD demand shifts → balance repricing before realization | Colder revision → up; hours–days | Winter >> shoulder; tight storage amplifies | Same-week EIA print, LNG outages, production changes | Symmetric response to offsetting revisions; response vanishes when storage ample | NOAA NOMADS archive keyed by run date + cycle hour 00/06/12/18 UTC (nomads.ncep.noaa.gov, accessed 2026-10-02, cycle dirs observed) | mechanism POSTULATED; source FACT; impact NOT_RUN |
| EIA weekly storage surprise (WNGSR) | Inventory vs consensus → scarcity repricing | Build surprise → down; minutes–days | Amplified at low storage percentile & in withdrawal season | Weather moving same week, positioning pre-report | No conditional response when storage surplus large; response decays with entry delay ≥5 min to noise | EIA WNGSR: standard release "10:30 a.m. eastern time on Thursdays", "All times are eastern"; stocks "as of Friday" (ir.eia.gov/ngs/ngs.html + /ngs/schedule.html, accessed 2026-10-02) | schedule FACT; impact NOT_RUN |
| Dry-gas production | Supply growth offsets demand → price down at given demand | Down; days–weeks | Freeze-offs/hurricanes flip sign short-term | Demand shocks, pipeline constraints | Production surprises fail to move price when storage buffered | EIA-914 monthly (primary, not fetched); vendor daily estimates (not fetched) | POSTULATED; NOT_RUN |
| LNG feedgas demand | Export pull tightens domestic balance → up | Up; days | High vs low LNG utilization; outage regime | Domestic weather, international (TTF) prices | Feedgas drops w/o price response when storage ample | EIA NG Weekly Update LNG tables (eia.gov, not fetched this lane) | POSTULATED; NOT_RUN |
| Power burn / HDD-CDD realization | Weather-driven demand converts to withdrawals | Up in cold; seasonal | Summer burn vs winter heat | Renewable output, gas-vs-coal switching | Realized weather beta ≈ 0 after forecast revision absorbed | Derived from weather + power data (not in corpus) | POSTULATED; NOT_RUN |
| Pipeline constraints / freeze-offs / hurricane | Physical supply loss → localized then hub repricing | Up; hours–weeks | Event-driven | Demand destruction, storage flexibility | Constraint events with no basis response | EIA/NOAA/PHMSA notices (not fetched) | POSTULATED; NOT_RUN |
| Seasonal storage trajectory (injection/withdrawal path) | Storage percentile sets scarcity premium | Level/risk premium; weeks–months | End-winter vs end-summer stocks | LNG, production growth | Premium unexplained by percentile in regressions | EIA WNGSR weekly (same as above) | POSTULATED; NOT_RUN |
| Term structure (m1−m2 contango/backwardation) | Storage/convenience-yield arbitrage prices carry | Slope ↔ expected spot path; days–weeks | Withdrawal vs injection season | Winter premium seasonality | Slope has no info on subsequent returns after costs | Computable from THIS corpus (OBSERVED curve stats §3) | curve stats OBSERVED; predictiveness NOT_RUN |
| Cross-asset: TTF/EU gas, CL, power, USD/rates | Relative fuel economics, macro risk channels | Varies; days | Risk-on/off, inflation regime | Common energy factor | Relation unstable sign or dies at costs | Not in corpus (NOT_RUN) | POSTULATED; NOT_RUN |
| Positioning (CFTC CoT, OI) | Crowding/forced-rolls amplify moves | Varies; weekly | Extremes only | Price-wealth endogeneity | Positioning adds nothing beyond fundamentals | CFTC CoT: "generally published each Friday at 3:30 pm Eastern Time", data as-of Tuesday (cftc.gov, accessed 2026-10-02) | schedule FACT; impact NOT_RUN |

Master-framework taxonomy buckets covered: Fundamental/physical (rows 1-7), Term structure (8), Cross-asset (9), Positioning (10), Event-driven (§4). Macro bucket: relevant via USD/rates/risk channels — POSTULATED, NOT_RUN (no macro series in corpus). Microstructure: §3 session/roll findings.

## 3. Behavior (measured where legal)

**Declared measurement windows (all OBSERVED from `analysis/NG_descriptives.json`, raw fetched 2026-10-02).**
- Per-contract daily TRADES: 29 contracts, bars 2019-09-03…2026-10-01. STRUCTURAL CAVEAT: contracts in the snapshot have deliveries 2025-10…2028-02, so 2019–2024 bars belong to then-DEFERRED strip legs, most of them settlement-derived close-only (v=0, O=H=L=C) or thin prints (median 3–30 lots/day pre-2024). The contemporaneous 2019–2024 front month does NOT exist in this corpus (expired-secdef wall ~12 months). Deep history = curve proxy, not tradable front.
- Front-true chain (selected contract delivery within 2 calendar months): 2025-08-01…2026-10-01, n=281 daily returns (within-contract; roll-day returns skipped). Note the first ~4 weeks the chain leg is at most the 2nd listed month (earliest delivery in corpus is 2025-10).
- Intraday H1 (IB useRTH=True → 09:30–17:00 ET ONLY; full Globex session NOT captured): per-contract last ~30 days; pooled 2025-07-21…2026-10-01, 291 distinct days, all bars v>0 (coverage_by_contract in JSON).
- Intraday M1: 2-day windows at each contract's final session: 2025-08-28…2026-10-01 (plus last 2 days for actives). IB M1 retention probe (S7, data lane): intraday requestable ~2.2y back for NG — capability, not corpus content.
- BID/ASK daily 1Y per contract (non-synchronous closes; NOT an executable spread).

**Session behavior (RTH window only).** Volume share by ET hour bucket: 09(09:30-10:00, half-hour) 10.0%, 10 19.3%, 11 15.7%, 12 13.4%, 13 13.8%, 14 20.1%, 15 4.9%, 16(16:00-17:00) 2.7% — activity concentrates late morning and 13:30-15:30, decays into 17:00. Mean |log ret| ×100 by hour: 10:00 bucket 0.49% vs ~0.35% midday and ~0.20% in 15/16 buckets; the 10:00-11:00 bucket contains the EIA 10:30 release. Weekday cut of the 10:00 bucket's share of day volume: Thu 25.3% vs Mon-Fri(ex-Thu) 16.1-18.0% — Thursday concentration consistent with the storage release timing (time-of-day/weekday descriptive profile, NOT an event study). M1 (2-day windows): first 30 min holds 11.7% of RTH day volume; last 30 min only 1.3%. Overnight/Asia/Europe sessions: NOT_RUN (RTH-only capture).

**Volatility.** Front-true era: daily log-ret std 3.10% → 49.2% annualized (iid convention); 26.7% of days |r|>3%, 8.2% >5%, max |r| 18.1% (2026); trailing-20d annualized vol at snapshot 48.7% (era median 40.1%, p10-p90 8.1%-43.9% on the long nearest-listed chain). Regime observation: on the nearest-listed (curve-proxy) chain, 2025-2026 vol (47-51% ann) is 2-4× the 2020-2024 level (13-21%) — the current sample sits in a HIGH-vol regime; do not extrapolate 2025-26 vol as typical. Winter vs summer |r| (front era): 3.09% vs 1.82% (~1.7×, single seasonal cycle).

**Trend fingerprint.** Lag-1 autocorrelation of front-era daily returns +0.0995 (nearest-listed chain +0.0291) — mild positive serial correlation, descriptive only; no rule built. Momentum/trend-statistics beyond this: NOT_RUN.

**Seasonality.** Front-era mean |r| by calendar month peaks Jan 4.98%, Dec 3.61% (winter) vs Apr 1.48%, Jul 1.58%; single seasonal cycle (2025-08→2026-10) — descriptive, one observation per month. Curve seasonality (m1−m2 same-day spread, front era): median by delivery-context month: Sep −0.44, Oct −0.30, Aug −0.28, Apr −0.29 (autumn/spring contango = winter premium in deferred) vs Dec +0.55, Nov +0.34 (mid-winter backwardation) — OBSERVED, single cycle.

**Curve behavior.** Front era m1−m2: median −0.112 USD/MMBtu, 75.2% of days negative (contango-shaped: near at a discount to the next delivery — a deferred winter premium; [m1 fix 2026-10-02: an earlier revision of this line called the negative medians "backwardated", contradicting the seasonality bullet below where negative medians = autumn/spring contango and positive mid-winter medians = backwardation]); p10 −0.375, p90 +0.345. On the long nearest-listed chain (curve proxy) the nearest-vs-second spread was negative 95.9% of days (median −0.186) — persistent discount of nearest leg through the deferred-print era; interpret as strip structure, not tradable front/next.

**Event behavior.** NOT_RUN — no return-based event studies performed (prohibited in PREP) and no consensus/surprise data in corpus.

**Roll behavior.** 13 matured rolls: same-day calendar spread (next − outgoing close at outgoing final session) median +0.028, min −0.556, max +0.577 USD/MMBtu, 30.8% negative; roll-day gap (next's next-session close − outgoing final close, stale-carry definition) median +0.055, min −1.181, max +0.755. These are curve gaps, NOT executable roll costs (settlement closes; no simultaneous quotes). Volume-crossover heterogeneity as in §1.

**Liquidity & costs (descriptive).** Front-era front-contract volume median 32,981 lots/day (p10 15,022, p90 78,588); aggregate all-contract volume median 79,938 lots/day. Front close-bid/close-ask proxy (294 days, 2025-08-01…2026-10-01): median 0.002 (= 2 ticks = $20), p90 0.003 ($30), max 0.02; NGX26 last-20-day median 0.002 — exactly reconciles with data-lane S6_FRONT_SPREADS (median 2 ticks/$20, p90 $30) — OBSERVED. Commission: IBKR $0.85/side + exchange + regulatory (document-class, `costs/IBKR_futures_commissions_2026-10-02.json`); NG exchange fee NOT_FETCHED; slippage NOT_RUN_NO_DECLARED_VALUE; PUBLISHED schedules ≠ MEASURED user costs.

**Price levels.** Front era: min 2.634, max 4.869, median 3.096, last 2.967 USD/MMBtu (2026-10-01). EIA Henry Hub spot late Sep-2026 $2.90-3.21 (eia.gov, accessed 2026-10-02) — corroborates level. Long nearest-listed chain (curve proxy): 2.298-4.896.

**Continuous adjustment.** None applied; all series unadjusted per-contract closes; roll-day returns excluded. Any back-adjustment effect on signals: NOT_RUN (deliberately deferred).

## 4. Event calendar

| Event | Actual release time (UTC unless noted) | Exchange tz context | Effective vs available vs retrieved | Vintage/revision/consensus PIT notes | Class |
|---|---|---|---|---|---|
| EIA Weekly Natural Gas Storage Report (WNGSR) | Standard: Thursdays 10:30 a.m. ET = 14:30 UTC (EDT) / 15:30 UTC (EST); holiday moves: → Friday 10:30 a.m. or → Wednesday 12:00 p.m. (e.g., 2026: Nov 13 → Fri, Nov 25 → Wed 12:00) | 09:30-17:00 ET RTH window; 10:30 falls in the 10:00-11:00 H1 bucket; falls INSIDE the trading day (no session gap) | Effective: stocks "as of Friday" prior week (report page wording); precise intraday survey cutoff NOT verified → NOT_RUN detail. Available: 10:30 a.m. ET release (primary, accessed 2026-10-02). Retrieved: NOT_RUN — no EIA pull in this session (futures raw only) | Weekly estimates; consensus needed for surprise (vendor); weekly-vs-annual revision policy NOT verified — treat vintages, never revised history as PIT | schedule FACT; everything else NOT_RUN |
| EIA WNGSR Supplement (new 2026 product) | "published every Thursday afternoon" (launched Jan 29, 2026 on EIA Beta) | — | same-day availability; exact time NOT_RUN | NOT_RUN | FACT (existence); NOT_RUN (timing) |
| CFTC Commitments of Traders | Fridays 3:30 p.m. ET = 19:30/20:30 UTC; holidays shift (published schedule) | after RTH close | Release ≠ position date: data as of PRIOR Tuesday close — 3-day staleness mandatory in any PIT use | Friday file = one Tuesday snapshot/week; use release-timestamped files, not revised history | FACT (cftc.gov, accessed 2026-10-02); usage NOT_RUN |
| Weather model runs (GFS and peers) | Cycles 00/06/12/18 UTC; NOMADS archive keyed by date + cycle dir (observed "00" for 2026-10-02 at fetch) | — | Availability latency per cycle NOT measured → NOT_RUN; vintage = run timestamp; FORECAST VINTAGES ONLY — never realized weather as a PIT feature | Each cycle is an immutable vintage; re-downloads must pin run date+hour | archive structure FACT (accessed 2026-10-02); latency NOT_RUN |
| Monthly roll / final session | Per contract: 3rd-last business day of month before delivery (~14:30 ET last trade); NGX26 final ~2026-10-28. Canonical-basis rolls (audit M2 fix): NGX26→NGZ26 already executed 2026-09-30 (last session before NGX26's LTD month Oct-2026); next canonical roll = out of NGZ26 at 2026-10-30 (last session before NGZ26's LTD month Nov-2026) | inside RTH | Roll decision uses only listed-calendar info (exchange-published months) — PIT-safe | — | FACT (rule, secondary source) + OBSERVED (dates in corpus) |
| Unscheduled physical events (hurricanes, freeze-offs, LNG outages) | Not scheduled | — | Exchange/official notices needed | NOT_RUN_CME_BLOCKED for exchange notices | POSTULATED taxonomy |

Macro releases (FOMC/CPI/NFP) matter only via the macro channel for NG — no NG-specific timing claims made here (NOT_RUN). Earnings/ETF timing: N/A for NG.

## 5. Hypotheses (ranked by testability × causal plausibility — NOT by PnL)

Standing constraints for all: PREP — none is run; each is a falsifiable design only. Corpus-1200 reuse: NOT_CHECKED (corpus-1200 not within this lane's read set); no FX→futures transfer claimed. Common cost model: median spread $20/side + commission $0.85 + exchange fee (NOT_FETCHED, use ES-documented $2.24 all-in style as placeholder class, NOT a measured NG cost) + slippage NOT_RUN_NO_DECLARED_VALUE. Common universe: NG monthly, canonical last-trade-month roll baseline (§1; this lane's matured chain rolls coincide with the canonical sessions — see the §1 reconciliation; live-front divergence disclosed there); sizing: vol-targeted off trailing-20d realized vol (PARAM-GAP: target vol, risk budget).

**H1 (rank 1) — Storage-surprise response conditioned on inventory percentile and season.** When the WNGSR print at 10:30:00 ET Thursday deviates from consensus by more than X Bcf (PARAM-GAP: X has no measured basis yet), the front contract should move in the surprise direction over minutes-to-hours, because inventory is the binding state variable of a storable commodity; strongest at low storage percentile and in withdrawal season, weakest (possibly reversed) at high percentile/injection season. Entry: first bar ≥ 10:31 ET in surprise direction; exit: time-stop same session or 1-3 days (PARAM-GAP); direction: with the surprise; TP/SL: none pre-registered (PARAM-GAP until post-release vol is measured); invalidation: median post-event move ≤ costs at 1.5×; counter-hypothesis: reaction is a weather-revision proxy (control: same-week forecast deltas); failure: edge only on delayed (≥5 min) entries disappearing, or only in one winter. Data requirements: EIA WNGSR vintages (free), consensus archive (vendor), M1 futures ≥5y around 10:30 (vendor; current corpus has only 2-day M1 windows) — floors: ≥100 events; budget: data cost decision is owner's. Class: design POSTULATED; all inputs NOT_RUN.

**H2 (rank 2) — Forecast-revision drift when storage is tight** (framework line "Weather-forecast revisions predict returns only when storage is tight"). When the day-over-day change in population-weighted HDD/CDF forecast from consecutive GFS vintages (00Z vs prior 00Z) exceeds k degree-days (PARAM-GAP), front NG should drift in the demand direction over 1-5 days, because traders reprice the balance as forecasts rev — but only when the storage buffer is thin; in ample-storage regimes the response should be muted/reversed (failure regime). Entry: 10:00 ET after vintage availability (latency must be measured first); exit: 1-5 days or offsetting revision; direction: with revision; sizing: vol-scaled; invalidation: symmetric fade, or disappears at 2× costs; counter-hypothesis: revisions are already priced intraday (test entry-delay sensitivity); failure: sign flips by season without percentile control. Data: NOMADS vintages (free, FACT archive), storage percentile (EIA, free), daily futures (have 14m true-volume + deeper settlement reference). Class: POSTULATED; NOT_RUN.

**H3 (rank 3) — Curve steepening/flattening forecasts near-term reversion vs trend** (framework line "Curve steepening/flattening…"). When the front-era m1−m2 spread steepens (more backwardation) by more than s USD/MMBtu over 5 sessions (PARAM-GAP), near-term daily returns should [direction unresolved a priori — two-sided test], because the spread prices storage scarcity and expected spot path; regime: withdrawal season vs injection season must be split (the §3 monthly medians flip sign across seasons). Entry/exit: daily closes, 5-20 day horizon; direction: two-sided pre-registration; invalidation: no conditional structure beyond unconditional winter vol; counter-hypothesis: it is only a seasonality proxy (control: month dummies); failure: result depends on roll convention (test alternative roll) or on the settlement-derived era. Testability NOW is highest (computable from legal corpus incl. deep per-contract closes, declared settlement-derived) but causal plausibility is medium (spread is endogenous to weather). Class: inputs OBSERVED (curve stats); hypothesis NOT_RUN.

**H4 (rank 4) — Extreme weather-premium mean reversion on forecast normalization** (framework "Extreme weather premium mean-reverts when subsequent forecasts normalize"). When the front's k-day return is extreme AND driven by a cold-forecast spike that then normalizes in the next vintage, price should retrace a fraction over 1-3 days, because risk premium unwinds faster than fundamentals justify; strongest in winter, weakest when normalization confirms a physical shock (freeze-off). Direction: against the spike; entry: after normalizing vintage; invalidation: retrace ≤ costs; counter-hypothesis: drift continues (underreaction). Requires weather vintages + ≥3y daily true-volume. Class: POSTULATED; NOT_RUN.

**H5 (rank 5) — Execution-timing descriptivum (not a signal).** The Thursday 10:00-11:00 ET bucket carries 25.3% of RTH volume (vs 16-18% other weekdays) and the highest mean |hour-ret| (0.49%); any NG execution design must declare its stance toward the 10:30 release (avoid trading 10:29-10:35, or explicitly event-trade per H1). This is a measured microstructure fact (OBSERVED) to be embedded as an execution constraint in later backtests, not an alpha claim.

PARAM-GAP register: all thresholds (X Bcf, k degree-days, s USD, horizons, TP/SL, sizing parameters) lack measured bases and are left unspecified on purpose — never invented.

## 6. Missing data table

| Need | Have | Source (primary first) | Period | Schema | PIT properties | License / cost | Blocker | Next action |
|---|---|---|---|---|---|---|---|---|
| Deep per-contract daily TRADES (true volume) | 14m front chain + settlement-derived 2019-24 reference | Databento / CME DataMine (owner decides; FINAL_REPORT option a) | 2010→now | per-contract OHLCV + OI | exchange feed, no revisions | paid (owner decision) | purchase moratorium in PREP | owner decision + DATA_ACQUISITION_SPEC |
| Intraday M1/H1 multi-year | H1 pooled ~14m RTH; M1 2-day windows | same vendors | 2010→now | 1-min OHLCV | same | paid | same | same |
| EIA WNGSR historical vintages + consensus | nothing pulled | ir.eia.gov (free) + consensus vendor | 1994→now | week, region Bcf, released-at | release-timestamped; weekly estimates revised | free + vendor cost | not fetched this lane | fetch in data lane next cycle |
| Weather forecast vintages (GFS/GEFS/EPS) | nothing pulled | NOMADS (free), ECMWF open data | 2004→now | run-date+cycle GRIB2 | immutable vintages | free | build effort; latency unmeasured | collector spec in DATA_ACQUISITION_SPEC |
| Open interest (daily per contract) | none in raw | vendor (CME via license) | — | OI per contract | daily, minor revision | paid | purchase moratorium | bundle with futures vendor buy |
| LNG feedgas / production daily | none | EIA weekly tables; vendor dailies | — | Bcf/d | release-timestamped | free/vendor | not fetched | fetch spec |
| CFTC CoT NG history | none pulled | cftc.gov (free) | 2006→now | futures-only positions | Friday release, Tuesday as-of | free | not fetched | fetch spec |

Top-3 by causal priority (per §2): weather vintages, WNGSR+consensus, deep true-volume futures (the last is the binding gate for any backtest beyond description — FINAL_REPORT: DAILY_BT/INTRADAY_BT BLOCKED ×10).

## 7. Framework coverage

Master framework §1 (10 questions):
1. Underlying economic exposure: physical HH gas, USD/MMBtu, 10,000 MMBtu — FACT (EIA) + OBSERVED (S1).
2. Participants: taxonomy POSTULATED (framework), no measurement.
3. Exchange & hours: NYMEX; IB session 18:00→17:00 ET OBSERVED (S1); CME-official text NOT_RUN_CME_BLOCKED.
4. Size/tick/currency/settlement: 10,000 MMBtu; 0.001=$10; USD; physically delivered — OBSERVED (S1) + FACT (EIA delivery point); margin mechanics broker-class only (vendor), SPAN NOT_RUN.
5. Listed months & liquid expiries: all 12, ~13y depth (secondary FACT); liquid = front + winter strip — OBSERVED.
6. Liquidity migration timing: OBSERVED — heterogeneous (8/13 pairs months-early winter dominance, 5/13 front-dominant to end, latest 6 days).
7. Dominant behavior driver: seasonality/storage/weather framework — POSTULATED; measured: high vol + winter concentration + curve seasonality OBSERVED; causal attribution NOT_RUN.
8. Which session matters: RTH only measured (10:00 & 14:00 buckets heaviest; Thu 10:00 bucket 25.3%) OBSERVED; overnight/Asia/EU NOT_RUN (RTH-only capture).
9. Tradeable contract per timestamp: calendar-nearest feasible PIT rule (OBSERVED roll dates); volume-max rule deviates seasonally (OBSERVED); OI rule NOT_RUN.
10. Vendor symbols ↔ expiries + reproducible continuous reconstruction: localSymbol month-code = delivery month (FACT convention + OBSERVED); raw `expiry_month` field mislabel risk (S9 C3) — documented; chain construction reproducible via `analysis/NG_descriptives.py` OBSERVED.

NG symbol-framework checklist (§1/§2/§14 of NG_RESEARCH_FRAMEWORK.md):
- What the contract represents / fair value vs cash: FACT (EIA HH) / storage-carry POSTULATED.
- Who must hedge: POSTULATED. Fair value vs spot basis: NOT_RUN (no spot series pulled).
- Volume by session and expiry: OBSERVED (§3; RTH-only). Volume/OI shift speed at roll: OBSERVED (volume only; OI NOT_RUN).
- Spread behavior overnight/near release/near expiry: overnight NOT_RUN; near-release weekday profile OBSERVED (volume only); near-expiry spread NOT_RUN (non-synchronous quotes).
- Opening/settlement/roll effects: first-30-min share 11.7% OBSERVED; settlement timing NOT_RUN_CME_BLOCKED; roll gaps OBSERVED (curve gaps only).
- Most stable contract-selection rule: calendar vs volume vs hybrid — OPEN; measured heterogeneity says test both (OBSERVED inputs; conclusion NOT_RUN).
- Back-adjustment impact on trend signals: NOT_RUN (no adjustment applied).
- Which weather vintage was available at each timestamp: NOT_RUN (latency unmeasured; archive structure FACT).
- Storage percentile × temperature-shock interaction: NOT_RUN (no EIA/weather series).
- LNG-flow dominance vs weather: NOT_RUN. Winter vs shoulder mechanics: descriptive vol/curve seasonality OBSERVED (single cycle), causal NOT_RUN.

Databento phase-1 checklist (framework §10): NOT_RUN — data acquisition is a separate lane (DATA-PIT-ACQUISITION-PREP) and any purchase is the owner's decision; this dossier only supplies requirements (§6).

— End of dossier. Every unlisted item is NOT_RUN by default; nothing here is a PASS, a GO, or a measured edge.

---

### CoT revision-policy verification note (added 2026-10-02, round co-owner-review-fix-1, lane HANDOFF-RESEARCH)

The CoT "not revised" wording in §2 positioning row and §4 CoT calendar row (this dossier's §4 already prescribes release-timestamped files over revised history — now primary-verified) was re-verified against primary CFTC
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
"cftc.gov legacy + TFF" is cited as a future source (the positioning rows). Shared note in
RESEARCH_MATRIX.md §CoT.
