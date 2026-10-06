# SI DOSSIER — COMEX Silver 5,000 oz Futures

- Symbol: **SI** (COMEX, trading class SI — the 5,000 oz contract, **NOT** the
  1,000 oz SIL class; symbol "SI" on COMEX resolves both classes and the data
  session selected `tradingClass="SI"` explicitly)
- Exchange: **COMEX** (division of CME Group), Globex electronic
- Generated (UTC): 2026-10-02
- Author lane: **SYMBOL-DOSSIER-SI** (task FUTURES-BEHAVIOR-10SYMS-PREP-20261002)
- Inputs:
  - `owner_framework/SI_RESEARCH_FRAMEWORK.md` sha256
    `d0349504fdbf2d6c3a400b486aa4920058a65caa75d5a5077ebfb12071e96cee`
  - `owner_framework/00_MASTER_FRAMEWORK.md` sha256
    `a75571b8017b13b5ff6552755d1334b03db640ebc26a6b4c9ad4323ca16d3c74`
    (both from `owner_framework/SHA256SUMS.txt`)
  - `research/control/FUTURES-DATA-10SYMS-V1/FINAL_REPORT.md` (+ HANDOFF.json,
    S9_INDEPENDENT_VERIFY.md, S1_IDENTITY.json, S6_FRONT_SPREADS.json,
    costs/IBKR_futures_commissions_2026-10-02.json,
    costs/SPECS_MARGINS_PUBLIC_2026-10-02.md) — untracked snapshot 2026-10-02,
    read-only
  - Raw data (read-only): `~/.my-quantitative-data/futures-10syms-v1/raw/SI_*`
    (125 files: 22 contracts × TRADES daily-6Y / hourly-30D / 1min-2D /
    BID+ASK daily-1Y, plus front/next/nearest_expired 3D probes). All bars
    `useRTH=true` (US/Eastern regular hours) — see §1/§3 for consequences.
  - Own analysis: `analysis/SI_behavior_stats.py` →
    `analysis/SI_behavior_stats.json` (every OBSERVED number below is
    reproducible from these).
- Claims taxonomy used throughout: **FACT** (primary source + URL + access
  date), **OBSERVED** (computed from raw data; script + window), **POSTULATED**
  (mechanism reasoning, unmeasured), **NOT_RUN** (not measured — never inferred
  PASS). This dossier is PREP: 0 PnL, 0 scored runs, 0 parameter selection.
- Methodology cross-check vs ES lane (ES_DOSSIER.md, read for consistency only):
  roll-gap measured the same way (adjacent-contract close gap at declared roll
  date, both legs observed same day); same RTH-only caveat (all raw bars
  `useRTH=true`); same strict-past/trailing-window discipline. SI-specific
  divergence: the declared "next listed contract" roll target is interpreted on
  the **measured liquid cycle** (H/K/N/U/Z), because literal next-calendar-month
  steps into dead serial contracts (§1) — a hazard ES does not have.

---

## 1. Mechanics

- **Underlying exposure** [FACT, spec mirrors + S1]: 5,000 troy ounces of
  refined silver, **physically delivered**, USD-quoted per troy ounce. Contract
  unit and deliverability per AMP and NinjaTrader spec mirrors (fetched
  2026-10-02, recorded in `costs/SPECS_MARGINS_PUBLIC_2026-10-02.md`);
  CME/COMEX official spec page unreachable this cycle (HTTP 403/timeout,
  consistent with `cme_check/`) — COMEX-official text NOT_RUN-unverified.
  Machine-verified identity: multiplier "5000", minTick 0.005, currency USD,
  `tradingClass "SI"`, uniform on **every** resolved SI contract in
  S1_IDENTITY.json (S9 Check 2: multiplier/minTick not re-derivable from raw
  bars; S1 is the identity authority; front SIV6 conId 760200581).
- **Economic role / participants** [POSTULATED, per SI framework §1; participant
  identity NOT_RUN on our data]: miners and smelters hedging forward production;
  industrial users (electronics/solar chain) hedging input costs; bullion
  banks/traders arbitrating COMEX vs London (LBMA) loco; macro/commodity funds
  taking precious-metals beta; **retail/speculative participants (disproportionate
  vs GC — measured squeeze episode §3)**; market makers. Per-participant
  positioning split NOT_RUN (no CoT pull this session).
- **Tick / multiplier / quote convention** [FACT, machine-verified]: tick
  $0.005/oz = **$25.00/contract** (5,000 oz × $0.005); quote = US$/troy oz
  (~$61 in Oct 2026); no 6J-style inversion risk. Corroborated by AMP/NT
  mirrors ("$0.005 / $25.00", costs file, 2026-10-02).
- **Sessions and DST** [FACT/OBSERVED, machine-verified from S1
  `tradingHours`/`liquidHours` for SI contracts, fetched 2026-10-02]: Globex
  **18:00 ET → 17:00 ET next day** (23h, 60-min maintenance break 17:00–18:00
  ET; Sunday open 18:00 ET); "liquid"/RTH session **09:30–17:00 ET**. Timezone
  `US/Eastern`. Hourly raw bars carry `-04:00` offsets on all Sep–Oct 2026
  timestamps (EDT, DST-correct; S9 verified the same convention across
  symbols). **All raw bars in this snapshot are `useRTH=true`**
  [OBSERVED, raw metadata]: daily bars are 09:30–17:00 ET RTH-day bars; the
  ~17h Globex overnight session is absent from every intraday file —
  overnight-session behavior NOT_RUN (only the overnight→RTH-open *gap* is
  measurable at daily resolution; §3).
- **Holidays** [OBSERVED, S1 windows]: `20261003:CLOSED` (Sat) and Sunday
  CLOSED until the 18:00 ET open; nothing SI-specific in the resolved window.
  Holiday shifts of last-trade dates matter at the 1-day level (third-last
  *business* day rule below).
- **Delivery / first-notice / expiry / price limits**:
  - Physical delivery [FACT, NT mirror]. First-notice-day mechanics and
    delivery instrument detail: NOT_RUN (CME blocked; mirrors not detailed).
  - Last trading: **13:25 ET on the third-last business day of the contract
    month** [FACT, doubly corroborated: NT mirror text "Trading ceases at 1:25
    pm ET on the third last business day of the contract month" (costs file,
    2026-10-02) AND S1 machine-verified `lastTradeTime "13:25:00"` on every
    contract]. Dates machine-check: SIV6 2026-10-28, SIZ6 2026-12-29, SIH7
    2027-03-29 — each is exactly the third-last business day of its month
    [OBSERVED, computed from S1 lastTradeDate set].
  - Price limits: COMEX metals daily price limits — NOT_RUN (no reachable
    primary source this session; CME blocked). The measured −31.4% close-to-close
    day (§3) is at least consistent with no binding limit that day, but the
    limit schedule itself is unverified.
- **Listed months & liquid maturities** [FACT + OBSERVED — a core SI finding]:
  - Listing rule [FACT, NT mirror]: monthly contracts for 3 consecutive months
    + any Jan/Mar/May/Sep within the nearest 23 months + any Jul/Dec within 60
    months. AMP lists the "active cycle" as F,H,K,N,U,Z (costs file).
  - **Measured liquid cycle = H/K/N/U/Z (Mar/May/Jul/Sep/Dec) only**
    [OBSERVED, `contract_panel`/`panel_summary`, all 22 raw files]: the 10
    serial contracts (V6, X6, F7, G7, J7, M7, Q7, V7, X7, F8) print at most
    **944 lots/RTH-day (SIV6 — the current S1 "front"!) vs 26k–178k on cycle
    months**; SIQ7/SIV7/SIX7 have zero volume in their entire files. Even Jan
    (F7, inside AMP's "active" list) is dead: max 53 lots. Deferred cycle
    months are also dead until they approach front (SIK7 max 41, SIN7 38, SIU7
    6, SIZ7 20, SIH7 797 lots) — liquidity lives on the **first 1–2 cycle
    contracts only**.
  - Consequence: **S1's "front" = nearest-expiry contract (SIV6, Oct-2026
    serial) is NOT the liquidity front** (SIZ6, Dec-2026, is — median 16.9k
    lots/day in Sep 2026 vs SIV6's dead book) [OBSERVED]. Any front/roll logic
    keyed to nearest-expiry is wrong for SI.
- **Liquidity migration front→next** [OBSERVED, `volume_migration` + roll-gaps
  table]: in all 6 roll cycles 2025-08→2026-08, the next cycle contract first
  reached 10,000 lots/day **2–7 calendar days before the declared roll date**
  (Z5: 7d, H6: 3d, K6: 2d, N6: 2d, U6: 6d, Z6: 4d), while the old contract's
  volume at the roll date had collapsed to **22–376 lots/day** (old-leg
  `v` on roll dates). I.e. COMEX silver migrates in the last few sessions
  before month-end, and the declared rule (roll at last session before day-1 of
  delivery month) is **well-aligned with migration** (within days), unlike the
  ES lane's finding of ~2-week misalignment. Exact old/new crossover *within*
  those days is NOT observable: expired contracts' raw files end at their roll
  date, and volume on the old leg is nearly zero by then [OBSERVED, file
  windows: SIU5..SIU6 files all end exactly at declared roll — verified 6/6 in
  `verify_files_end_at_declared_roll`].
- **PIT contract selection + roll rule (baseline + alternatives)**:
  - Baseline (data-lane declared, FINAL_REPORT §Roll rule): hold until the last
    session before day-1 of the delivery month; roll to the next listed
    contract at that close; listing calendar published years ahead → PIT-legal;
    no back-adjustment performed by the data lane.
  - **SI-specific hazard [OBSERVED]**: "next listed contract" interpreted as
    next *calendar* month steps into dead serial books (Sep→Oct 2026 would hold
    SIV6 at ≤944 lots/day vs SIZ6's 17k). The raw dataset itself only supports
    the **cycle chain** U5→Z5→H6→K6→N6→U6→Z6(→H7 …), because the expired-walk
    fetched cycle months only (Oct/Nov-2025 serials absent entirely). The
    engine baseline for SI must therefore be: **declared timing, cycle-month
    target** [construction decision, not alpha].
  - **Roll gap / cost** [OBSERVED, `roll_gaps`]: adjacent-contract close gaps at
    the 6 completed rolls were **positive 6/6**: +0.525, +0.725, +0.605,
    +0.495, +0.445, +0.770 $/oz (median +0.565 $/oz = 113 ticks =
    $2,825/contract; mean **+0.97% per roll** ≈ +5.2%/yr at the observed
    ~5.4 rolls/yr). Consistent with a persistent **contango** (deferred above
    nearby) throughout the measured window [gaps OBSERVED; carry mechanism
    POSTULATED — see driver 8]. Caveat: the old leg's roll-date close prints on
    a nearly-dead book (22–376 lots), so the gap embeds both carry and
    tail-book staleness [OBSERVED]. An unadjusted continuous series embeds
    ~+1%/2-months artificial jumps at rolls — back-adjustment mandatory for
    level/trend work (construction, not alpha) [POSTULATED→engine spec].
  - Alternatives (engine A/B): (a) volume-crossover roll (next cycle contract
    daily volume ≥ 10k — measured to occur 2–7 days before declared roll);
    (b) OI roll — NOT_RUN (raw files carry no open-interest field);
    (c) calendar T-N variants — measurable but add no observed benefit over
    the declared date given the 2–7-day alignment.
- **Identity cross-check** [FACT/OBSERVED]: 22 SI conIds in raw set match S1
  identity on conId/localSymbol/expiry (S9 Check 2 PASS incl. SI). Raw
  `expiry_month` field carries the full lastTradeDate (SIV6 → 20261028); for
  SI the month code == delivery month == last-trade month (no CL/NG-style
  one-month offset — S9 C3 does not apply to SI).

## 2. Causal driver map

Master-framework buckets relevant to SI: Macro, Fundamental/physical,
Cross-asset, Positioning, Term structure, Microstructure, Event-driven.
(SI is the only symbol in this 10-symbol corpus whose framework explicitly
assigns BOTH monetary and industrial driver buckets.)

| # | Driver | Source → mechanism | Predicted sign / horizon | Regime dependency | Confounders | Falsification test | PIT data source (primary, access date) | Evidence class |
|---|--------|-------------------|--------------------------|-------------------|-------------|--------------------|----------------------------------------|----------------|
| 1 | Gold direction (GC) — monetary premium beta | GC repricing → silver shares the monetary/store-of-value factor with higher amp (smaller mkt, retail leverage) | SI same sign as GC, amplified ~2x in %; horizon = GC shock horizon (min–days) | Amp largest in precious-metals momentum/squeeze regimes; weakest when industrial demand shocks dominate SI alone | SI-specific squeezes (measured Jan-2026: ratio crashed to 44 while GC rose — driver decoupled); USD/rates co-moves | Rolling %-beta stability; regime split of beta vs vol | GC raw in snapshot (measured §3); LBMA Silver Price auction 12:00 London (lbma.org.uk / ICE developer portal, 2026-10-02) for cash-leg | Correlation OBSERVED (0.83 full-sample); amplification/convexity POSTULATED (needs regime split) |
| 2 | Real rates / Fed policy (FOMC, CPI) | Real-yield ↑ → zero-carry store-of-value discount-rate channel → SI down; silver's retail flow amplifies | Hawkish surprise → down; easing → up; minutes–days | Strongest in tight-vol regimes; weakest mid-cycle | Same-window growth news; USD channel (driver 3) opposite sign possible | FOMC/CPI-window SI return vs rate repricing, flat otherwise | FOMC calendar federalreserve.gov/monetarypolicy/fomccalendars.htm (2026-10-02); CPI schedule bls.gov/schedule/news_release/cpi.htm (2026-10-02); surprise data NOT in repo | Calendar FACT; effect NOT_RUN |
| 3 | USD (DXY/FX) | USD ↑ → $-priced metal cheaper globally → SI down; days | Inverse; days | Global-risk and rates regimes | Non-USD supply/demand; other metals co-move | Rolling SI–DXY beta sign stability | DXY NOT in repo (6E/6B/6J/6A raw exist as FX cross-checks); DXY source NOT fetched | NOT_RUN (measurement) |
| 4 | Industrial growth expectations (solar/electronics demand; HG confirmation) | PMI/ISM/industrial cycle → silver's ~50%+ industrial demand leg → SI deviates from GC | Pro-growth → SI outperforms GC (ratio falls? direction regime-dependent); weeks–months | Only distinguishable when monetary factor quiet | Gold beta dominates short horizon (driver 1); substitution/THRIFT in electronics | SI/GC ratio response to industrial surprises vs GC-controlled | ISM schedule NOT fetched; HG copper NOT in 10-symbol snapshot | NOT_RUN |
| 5 | Mine supply / physical premia (COMEX-LBMA basis, EFP, lease rates) | Refinery/coin/bar demand → physical premium → front vs London dislocation (2020-style EFP squeeze) | Scarcity premium → front over London, curve backwardation; event-scale | Crisis/logistics regimes only | Rates/carry (driver 8); warehouse inventory policy | EFP/lease-rate extremes vs subsequent front-curve slope | LBMA lease/forward data login/paid; NOT in repo; COMEX vault stocks (cmegroup.com) BLOCKED_HTTP | NOT_RUN |
| 6 | Risk appetite / retail positioning (squeeze risk) | Retail/leverage flows into the small silver market → self-reinforcing momentum then violent unwind (measured Jan-2026: +14% day, then −31.4% day; §3) | Fat both-way tails clustered in squeeze windows; event horizon | High-vol / momentum regimes; absent in quiet regimes | Macro shocks landing same window; margin-hike mechanics (exchange notices) | Tail-day clustering conditional on trailing vol/positioning | CoT (driver 7) + vol measures from raw (measured); margin-notice archive NOT in repo | Episode OBSERVED (descriptive); mechanism POSTULATED |
| 7 | Positioning (CFTC CoT, OI) | Crowded net spec length → squeeze/convexity risk on shocks; dealer inventory constraints | Extremes → larger adverse tails; weekly horizon | Crisis vs normal | CoT aggregates reportables only; release ≠ position date (Fri release, Tue positions — verified below) | CoT-extreme weeks vs subsequent SI vol/tails | Release schedule cftc.gov MarketReports/CommitmentsofTraders (2026-10-02): "generally published each Friday at 3:30 pm ET", positions "as of the close of business of Tuesday"; historical values NOT pulled | Calendar FACT; effect NOT_RUN |
| 8 | Term structure / carry (roll gap = contango) | Futures = spot + (rates + storage − convenience/lease)×T; measured contango ≈ +0.97%/roll | Gap > 0 while carry positive; flips to backwardation in physical-squeeze regimes (2020 precedent) | Rates regime + physical scarcity | Tail-book staleness inflates measured gap (old leg 22–376 lots at roll); demand pressure premium | Gap sign vs (SOFR-like rate − silver lease/storage) each cycle | Gaps OBSERVED (6/6 positive); SOFR free on FRED (not yet pulled); lease rates paid | Gaps OBSERVED; carry link POSTULATED |
| 9 | Microstructure: roll-window + serial-month books | Liquidity migrates in last 2–7 days before month-end (measured); serial books ≤944 lots are quote-rot traps (S6 spread measured on one of them) | Execution-cost spike if rolled too early/late; thin-book marks unreliable | Always (mechanical); worse in stress | Holiday half-sessions; S1-front mislabeling (nearest ≠ liquid front) | Cost proxies inside vs outside roll week; serial vs cycle spread | Raw files (measured §3); BBO depth NOT in repo | OBSERVED (volume/spread side); depth side NOT_RUN |
| 10 | Event calendar (FOMC/CPI/CoT/COMEX roll/LBMA fix) | Scheduled catalysts concentrate repricing; LBMA 12:00 London auction sets cash-leg reference inside Globex hours | Event-window vol clustering; minutes | High-vol regimes amplify | Overlapping events; post-squeeze regime (2026) | Event vs non-event vol/return distribution | Calendars: Fed/BLS/CFTC (2026-10-02, §4); LBMA auction 12:00 London via lbma.org.uk FAQ + ICE developer portal (search-index access 2026-10-02; LBMA page itself bot-blocked) | Calendar FACT; effects NOT_RUN |

## 3. Behavior (measured where legal)

All computed by `analysis/SI_behavior_stats.py` → `analysis/SI_behavior_stats.json`
from raw per-contract daily TRADES (RTH bars, useRTH=true), declared-rule
unadjusted **cycle chain** (U5→Z5→H6→K6→N6→U6→Z6), thresholds only via
strict past/trailing windows. Chain window **2025-07-01→2026-10-01, 316
days** (chain cannot start earlier: previous liquid fronts SIN5-/GCQ5- are
behind the expired-secdef wall; deeper per-contract history exists only as
deferred-contract settlement marks, e.g. SIZ5 file from 2020-12-31 — reference
price only, never a front chain). Front-scale era (chain daily volume ≥10k
lots, sustained ≥80% of a 20-day window): starts at the chain start
2025-07-01 (289/316 days ≥10k; ≥20k sustained only from 2025-08-27, 159 days)
[OBSERVED].

- **Session/volume behavior**:
  - Liquid-front median daily volume by cycle era [OBSERVED, `volume_migration`
    + panel]: Jul–Aug 2025 (SIU5) 16–25k; Sep–Nov 2025 (SIZ5) 25–49k; Dec
    2025–Feb 2026 (SIH6) 19–66k; Mar–Apr 2026 (SIK6) 13–18k; May–Jun (SIN6)
    14–18k; Jul–Aug (SIU6) 13–14k; Sep 2026 (SIZ6) ~17k.
  - RTH hourly volume profile (front SIZ6, 2026-08-20→2026-10-01, 30 days,
    RTH-only): 09:30–10:00 12.9%, 10:00-hour 22.2%, 11:00-hour 16.6%, 12:00
    14.3%, 13:00 13.5%, 14:00 10.1%, 15:00 7.5%, 16:00–17:00 close bar 3.0% —
    **front-loaded** (first 90 min ≈ 35% of RTH volume), NOT the ES-style
    U-shape; prior front SIU6 (Jul 21–Aug 31 window) agrees (first 2.5h ≈ 54%)
    [OBSERVED, 30-day windows only — not structural constants].
  - Overnight Globex session: NOT_RUN (useRTH=true; absent from snapshot).
  - Serial/deferred books: never tradable at size (max 944 lots/day serial;
    deferred cycle ≤797 until ~2 months to front) [OBSERVED, panel].
  - Top volume days all cluster in the Dec-2025–Jan-2026 squeeze: 178,488
    (2026-01-26), 173,244 (01-30), 113,794 (2025-12-12), 107,549 (2025-10-09,
    SIZ5), 100,742 (2026-01-14) [OBSERVED].
- **Volatility behavior** (n=309 daily returns; 6 roll-morning returns
  excluded; front-scale era = full window):
  - Mean +0.217%/day, std **3.79%/day** (annualized 60.2%), min **−31.37%**
    (2026-01-30), max **+13.99%** (2026-01-26), q05..q95 −5.68%..+6.07%,
    skew −1.81, excess kurtosis **+15.2** [OBSERVED].
  - **The sample is one squeeze-and-crash regime**: level 36.4 (2025-07-01) →
    **115.505 close peak (2026-01-26, +217%)** → 61.175 (2026-10-01);
    crash day 2026-01-30 printed o=98.355, l=74.000, c=78.530 on 173,244 lots
    / 123,771 trades [OBSERVED, raw SIH6 bars — verified against file
    directly]. Any statistic from this window carries single-regime caveat.
  - Rolling 63-day vol: min 1.41% (2025 Q3), median 3.25%, max 6.67%
    (post-squeeze), last 2.28% (2026-10-01) — 4.7× range [OBSERVED].
  - |ret| lag-1 autocorr 0.089 — weak daily vol clustering [OBSERVED,
    short-window caveat].
- **Trend behavior**: descriptive only — mean +0.22%/day with strongly
  negative skew and fat tails over a +68% 15-month net move; no trend/MR test
  run (would be rule evaluation — NOT_RUN by task classification).
- **Event behavior**: FOMC/CPI/CoT-day conditional behavior NOT_RUN (needs
  event alignment + longer sample; no surprise/consensus dataset in repo).
  The one measured "event-like" cluster is the squeeze itself (ex-post
  description, not a scheduled event): 8 of the top-10 |daily moves| fall in
  2025-12-20→2026-02-12 [OBSERVED].
- **Curve behavior**: all 6 measured roll gaps positive (median +0.565 $/oz =
  +0.97% mean per roll ≈ +5.2%/yr) — persistent contango through the squeeze
  [OBSERVED]. Calendar-spread behavior beyond roll dates NOT_RUN (deferred
  marks stale/rot; front-filter needed).
- **Seasonality (descriptive, single pass of the year, squeeze-dominated)**:
  by-month mean daily return: Jan +1.01%, Feb +1.01%, Nov +0.86%, Dec +0.96%
  vs Jun −1.10%, Mar −0.07%; by-month vol: Jan 9.0%, Feb 5.2%, Dec 4.7% vs
  Jul–Aug 1.8–2.0%. By weekday: Thu mean −0.63% (crash-day Friday skew −3.6;
  the −31% day was a Friday), Mon/Wed +0.68/+0.70% [OBSERVED — n≈19–42 per
  bucket, one year; NOT seasonal-alpha claims].
- **Overnight→RTH-open gap** (RTH open vs prior RTH close; normalized by
  trailing-20d mean|ret| ending prior day, strict past): n=289, mean +0.25%,
  std **3.24%** (≈86% of the full-day return std — a larger overnight-transfer
  share than ES's 63%), q05..q95 −5.05%..+5.47%, extremes −14.05% (2026-01-30)
  and +13.30% (2026-02-03); |gap| ≥ 2× trailing mean|ret| on **9% of days**
  [OBSERVED]. Top gaps: −14.05% (2.68×), +13.30% (2.08×), −11.88% (2026-03-19,
  3.75×).
- **Cross-asset: GC/SI ratio and beta** (both legs = own unadjusted declared-
  rule liquid chains, 2025-07-01→2026-10-01, n=316; 25 days adjacent to either
  leg's roll flagged) [OBSERVED]:
  - Gold/silver ratio: mean 70.9, std 11.5, **min 44.00 on 2026-01-26 (squeeze
    peak) vs max 92.79 on 2025-07-01**, current 68.69 (69.8th percentile of
    trailing 63d, strict past) — the ratio traversed a 2.1× range in 7 months
    and mean-reverted past its median.
  - SI-vs-GC same-day return correlation 0.828 full-sample; rolling 63d
    correlation 0.654–0.91 (never near zero); $-beta 0.010–0.057 (median
    0.028) → %-elasticity ≈ beta × (GC/SI price) ≈ **~1.9% SI per 1% GC at the
    median** (amplification ~2x, consistent with framework §15's convex-beta
    hypothesis; convexity itself untested — regime split NOT_RUN).
  - Caveats: unadjusted legs embed roll-gap jumps at both calendars' rolls;
    descriptive only — no reversion rule tested.
- **Spread/cost observables** (published ≠ measured user costs):
  - **Liquid-era front close-proxy BID/ASK spread** (each cycle contract's own
    BID/ASK 1Y file restricted to its liquid era; close-to-close proxy, NOT
    executable): SIU5 (Jul–Aug 25) 2 ticks=$50; SIZ5 2 ticks=$50; SIH6 (Dec
    25–Feb 26, squeeze era) 5 ticks=$125 (p90 23 ticks); SIK6 8 ticks=$200;
    SIN6 5 ticks=$125; SIU6 4 ticks=$100; SIZ6 (Sep 26+) 3 ticks=$75. Pooled
    median-of-medians **4 ticks = $100/contract**; 0 crossed days in all
    liquid windows [OBSERVED]. Spread roughly doubled across the sample
    (2→4–8 ticks) with price level and vol.
  - The data lane's S6 front-spread number for SI (median 4.5 ticks = $112.5,
    p90 $147.5) was measured on **SIV6 — the dead Oct serial "front"**
    [OBSERVED, S6_FRONT_SPREADS.json front=SIV6]; that book's full-1Y median is
    20 ticks ($500) with p90 $6.46/oz and the dataset's **only crossed close
    day (2026-05-21)** — quote rot on a serial book, not a liquid-front
    property. Use the liquid-era numbers above for SI cost baselines.
  - Commission [FACT, document-class]: IBKR US standard futures $0.85/side +
    exchange + regulatory (costs/IBKR_futures_commissions_2026-10-02.json,
    fetched 2026-10-02); **SI-specific exchange fee NOT_FETCHED** (JS tables
    did not render; only the ES worked example $2.24 all-in exists). Slippage:
    NOT_RUN_NO_DECLARED_VALUE.
  - Margin [FACT, broker-class public; CME SPAN blocked]: NinjaTrader
    maintenance $33,498 / initial $36,847.80 (as of 2026-08-31); AMP
    maintenance $35,641 (2026-10-02) — <7% apart (costs/
    SPECS_MARGINS_PUBLIC_2026-10-02.md).
  - Roll cost: gaps measured (above, 6/6 positive, median $2,825/contract);
    as an executed two-book crossing cost NOT_RUN (thin-book side
    unmeasurable).
- **Intraday beyond RTH**: 1-min files are 2 days/contract (SIZ6: 900 bars);
  M1/H1 multi-year depth NOT_RUN in snapshot (FINAL_REPORT wall ~10 months,
  RTH-only) — no intraday statistics computed beyond the 30-day hourly
  profiles above.

## 4. Event calendar

All times: release time (source-stated) + exchange tz (US/Eastern, ET; RTH
09:30–17:00; Globex 18:00→17:00 ET).

| Event | Actual release time (UTC / ET) | Vintage & PIT properties | Effective vs available vs retrieved | Evidence class |
|---|---|---|---|---|
| FOMC decisions 2026 | Meetings Jan 27-28, Mar 17-18*, Apr 28-29, Jun 16-17*, Jul 28-29, Sep 15-16*, Oct 27-28, Dec 8-9* (* = SEP). Statement day-2 ~14:00 ET (19:00 UTC) — statement time POSTULATED, not fetched | Statements final at release; SEP projections revised each SEP meeting | Effective = statement timestamp; available same minute on federalreserve.gov; retrieved in repo: NO (schedule collection only) | Calendar FACT (federalreserve.gov/monetarypolicy/fomccalendars.htm, 2026-10-02); statement-time POSTULATED |
| CPI (BLS) | 8:30 AM ET (12:30/13:30 UTC winter/summer); 2026: Jan 13, Feb 13, Mar 11, Apr 10, May 12, Jun 10, Jul 14, Aug 12, Sep 11, Oct 14, Nov 10, Dec 10 (reference month M-1) | Index rarely revised; seasonal factors revised annually (policy text not fetched) | Effective = 8:30 ET release; retrieved: NO | Schedule FACT (bls.gov/schedule/news_release/cpi.htm, 2026-10-02) |
| CFTC CoT (Financial Futures, incl. silver complex) | "generally published each Friday at 3:30 pm ET" (19:30/20:30 UTC); positions "as of the close of business of Tuesday" of the same week; ~3-day processing lag; holidays shift schedule | Position date (Tue) ≠ release (Fri) — PIT lag ≥ 3 days; only 13 most recent months kept on site | Earliest legal observation = Fri 15:30 ET; using Tuesday-dated positions earlier = look-ahead; retrieved: NO | FACT (cftc.gov/MarketReports/CommitmentsofTraders/index.htm, 2026-10-02) |
| COMEX roll / roll week (cycle chain) | Last session before day-1 of delivery month: 2026-11-30 (SIZ6→SIH7 next); next-cycle ≥10k-lot ramp measured 2–7 days prior | Determinable from published listing calendar years ahead (fully PIT-safe); ramp date needs same-day volume | Ex-post measured here; forward rule = calendar (deterministic) | OBSERVED (6 cycles) + FACT (calendar) |
| LBMA Silver Price auction (cash-leg benchmark) | 12:00 noon London time (07:00 ET in EDT / 08:00 ET in EST; 11:00/12:00 UTC) each LBMA business day; administered by ICE Benchmark Administration; participants input in 25k/100k oz lots | Published once, final; benchmark methodology governed by IBA | Effective = auction close; retrievable free with delay; retrieved: NO | FACT (lbma.org.uk Silver Price FAQ + ICE developer portal developer.ice.com, accessed 2026-10-02 via search index — LBMA page itself bot-blocked) |
| NFP/Employment Situation, PCE, ISM, GDP | NOT fetched this session (BLS CPI + Fed calendars only) | — | — | NOT_RUN (calendar) |

Consensus/surprise datasets: none in repo; any surprise-adjusted design is
blocked until a PIT consensus archive is sourced (owner decision).

## 5. Hypotheses (ranked by testability × causal plausibility — NOT by PnL)

Corpus-1200 reuse: none checked — corpus not provided to this lane. No
FX→futures transfer claimed; all hypotheses below are native to this futures
corpus or from `SI_RESEARCH_FRAMEWORK.md` §15 (flagged per row).

**H1 — Cycle-chain construction + roll-calendar alignment (mechanics-level,
testable NOW; foundation for every other SI test).**
- PIT condition (observable): calendar-only: hold the nearest **H/K/N/U/Z**
  delivery-month contract; roll at the last session before day-1 of its
  delivery month; never hold serial months (measured dead: max 944 lots vs
  26k–178k cycle).
- Prediction: declared timing is within 2–7 days of the measured ≥10k-lot
  migration (6/6 cycles); a nearest-expiry "front" (SIV6-style) would sit in a
  ≤944-lot book with 20-tick median spread and the dataset's only crossed day.
- Mechanism: COMEX silver's delivery-cycle convention concentrates hedge and
  roll flow on cycle months; serial listings exist for tail hedging only.
- Entry/exit (construction rule, not a trade): switch continuous reference at
  declared roll close; TP/SL/direction N/A.
- Universe/roll: SI H/K/N/U/Z, ~5.4 rolls/yr; sizing N/A; cost model: roll gap
  measured (median +0.565 $/oz = $2,825/contract unadjusted jump).
- Invalidation: a cycle where the ≥10k ramp deviates >10 days from the declared
  date, or a serial month trading >10k lots/day.
- Counter-hypothesis: migration is volume/OI-driven, not calendar (OI roll
  untestable now — no OI field).
- Failure conditions: engine using nearest-expiry front or vendor continuous
  with unknown stitching; treating the roll gap as PnL.
- Data: ALREADY met by raw files (this dossier §1/§3). Floor: none. Budget: 0.

**H2 — Gold/silver ratio extremes forecast relative-value reversion
(framework §15, idea 2).**
- PIT condition: GC/SI ratio (own liquid chains) crosses a trailing
  percentile band of itself (strict past window, e.g. 63d — descriptive
  current read: 68.69 at the 69.8th percentile).
- Prediction: after extreme ratio readings, the spread (long cheap leg / short
  rich leg) reverts toward its trailing median over weeks; mechanism: silver's
  dual identity (monetary premium vs industrial valuation) plus retail-flow
  overshoot — measured anchors: ratio range 44.0→92.8 in 7 months with
  reversion through the median.
- Strongest regime: post-squeeze/high-vol (amplification unwinding); weakest:
  structural industrial-demand shifts (framework §16 failure mode — silver
  becoming "more industrial" would break mean reversion toward old levels).
- Entry/exit/TP/SL/time: PARAM-GAP — band width, holding horizon and exit
  percentile cannot be set without a look-ahead-free selection protocol; must
  be pre-declared before any run. Direction: long SI/short GC when ratio rich
  (SI cheap), reverse when ratio cheap.
- Universe/roll: both legs' cycle fronts, H1 rolls both chains (SI HKNUZ ~5.4/yr,
  GC GJMQVZ ~6/yr). Sizing: ratio-neutral 1:delta (declared formula before
  run). Cost model: both legs ~4–5 ticks liquid-era close-proxy + $0.85+exch
  (SI exch fee NOT_FETCHED) × two legs × ~11 rolls/yr combined.
- Invalidation: sign instability across the (few) regime episodes; reversion
  edge < 2-leg costs at 1.5× stress (master §6).
- Counter-hypothesis: ratio is a one-way structural trend (industrial silver
  scarcity) — 15-month window cannot distinguish.
- Failure conditions: roll-gap jumps treated as reversion (unadjusted legs —
  exclude ±1 roll days, 25 flagged); using settlement-era marks as fills.
- Data: 15 months both legs in snapshot → LOW power (≈1 full episode); floor
  ≥100 extreme-episodes needs ≥10y two-leg daily history → vendor purchase
  (owner decision) or prospective accumulation. Budget: vendor bundle.

**H3 — Contango roll-gap sign tracks carry (rates + storage − convenience
yield).**
- PIT condition: at each roll, adjacent-contract close gap (measured) vs
  contemporaneous short-rate proxy (e.g., 3M SOFR) and silver lease/storage
  cost proxies.
- Prediction: gap > 0 while carry positive — measured 6/6 positive, mean
  +0.97%/roll ≈ +5.2%/yr through a 60%-vol squeeze; sign should flip toward
  backwardation in physical-scarcity regimes (2020 EFP episode precedent,
  POSTULATED).
- Mechanism: cost-of-carry fair value anchored by bullion-bank inventory
  arbitrage (COMEX↔London).
- Strongest regime: normal inventories/positive rates; weakest: scarcity
  (premium inverts curve) or zero-rate policy.
- Entry/exit/TP/SL/direction: N/A (structural relation; informs continuous-
  series drift, calendar-spread designs, and ratio-trade roll accounting).
- Universe/roll: adjacent cycle pairs. Sizing N/A. Cost model: spread legs
  (front-filtered quotes only — serial/deferred books are rot).
- Invalidation: positive gaps persisting while measured carry is deeply
  negative (would imply demand-pressure premium dominates).
- Counter-hypothesis: gap is mostly tail-book staleness (old leg trades 22–376
  lots at roll) — testable by comparing to a T-5 or volume-roll gap variant.
- Failure conditions: treating settlement-derived deferred closes as tradable;
  ignoring the thin-old-leg caveat.
- Data: gaps OBSERVED; rates free via FRED (not yet pulled); lease rates
  paid (LBMA/IBA). PARAM-GAP until rate/lease series sourced. Floor: ≥8
  rolls for a sign statement (have 6 measured + more accumulating
  prospectively ~5.4/yr).

**H4 — Convex beta of SI to GC in precious-metals momentum regimes
(framework §15, idea 1).**
- PIT condition: GC return shock (or GC-momentum regime label from trailing
  window, strict past); SI response measured on the cycle front.
- Prediction: SI %-response per 1% GC > 1 and increasing in momentum/high-vol
  regimes (measured linear elasticity ~1.9 median, corr 0.83, never below
  0.65 on rolling 63d — the *convexity* (nonlinearity) is POSTULATED and
  unmeasured).
- Mechanism: smaller market cap metal + retail leverage + dealer inventory
  limits amplify the common monetary factor.
- Strongest regime: precious-metals momentum (measured squeeze window);
  weakest: industrial-shock windows where SI moves alone (2026-01-26 showed
  full decoupling: ratio −44 while GC rose).
- Entry/exit/TP/SL/time: PARAM-GAP (no thresholds may be set without a
  selection protocol). Direction: same sign as GC shock.
- Universe/roll: SI cycle front (H1); GC cycle front. Sizing: beta-scaled
  (declared formula). Cost model: SI 4 ticks + GC 5 ticks (liquid-era
  close-proxy medians) + commissions both legs.
- Invalidation: elasticity < 1 persistently, or convexity absent (linear beta
  suffices) across ≥2 regimes.
- Counter-hypothesis: apparent amplification is a volatility-scaling artifact
  (framework §4's explicit question) — must normalize by vol before claiming
  convexity.
- Failure conditions: single-episode attribution (the Jan-2026 squeeze IS one
  event); roll-boundary contamination; RTH-only gaps understating overnight
  co-movement.
- Data: 15 months two-leg daily = LOW power; needs multi-year two-leg daily
  (vendor) for regime splits. Budget: vendor bundle.

**H5 — Overnight-gap tail clustering conditional on trailing vol regime
(squeeze-risk descriptor; framework §16 "retail-driven squeezes").**
- PIT condition: RTH-open gap vs prior close; regime label from trailing-63d
  vol and/or squeeze markers (all strict past).
- Prediction: |gap| ≥ 2× trailing-20d mean|ret| days cluster in high-trailing-
  vol states (measured: 9% of days overall; extremes −14.0%/+13.3%/−11.9% all
  in the squeeze aftermath); gap std is 86% of daily std — most variance
  arrives overnight→open, where our data is blind inside the session.
- Mechanism: leveraged positions unwound into thin books; margin-hike cascade
  (POSTULATED).
- Strongest regime: post-squeeze high-vol; weakest: quiet regimes.
- Entry/exit/TP/SL/time: PARAM-GAP (and intraday execution assumptions
  unusable: RTH-only bars, 2-day M1). Direction: two-sided tails — as a risk
  filter, not a direction trade.
- Universe/roll: cycle front, H1. Sizing: vol-targeted (declared formula).
  Cost model: gap-crossing slippage NOT_RUN_NO_DECLARED_VALUE (honest floor:
  the 14% gap day implies limit-style execution risk no tick model covers).
- Invalidation: tail clustering absent once conditioned correctly (poisson-like
  arrival independent of trailing vol).
- Counter-hypothesis: gaps are pure information arrival (macro nights), no
  risk premium.
- Failure conditions: treating 15-month single-regime tail estimates as
  stationary; using settlement-era marks pre-2025-07.
- Data: legal daily data sufficient for a *descriptive* first pass (done);
  hypothesis-grade test needs ≥2y front-scale + overnight session data
  (vendor M1 with non-RTH bars). Budget: vendor bundle.

## 6. Missing data table

| Need | Have | Source (primary first) | Period | Schema | PIT properties | License/cost | Blocker | Next action |
|---|---|---|---|---|---|---|---|---|
| Multi-year true-volume front chain, daily (H2/H4/H5 power) | 15 months (2025-07→2026-10) cycle chain; deeper = deferred settlement marks only | Databento / CME DataMine (CME-licensed vendor) | 2010→now | per-contract OHLCV (+OI) | Volume as-published (no revision) | Paid (owner decision; FINAL_REPORT option (a)) | Purchase decision | Owner decision; DATA lane spec |
| Intraday M1/H1 depth incl. overnight session (H5; microstructure) | 30D hourly RTH-only + 2D M1 per contract (~10-month wall) | Databento / CME DataMine | 2019→now | ohlcv-1m + definitions per expiry (SI framework §10) | Raw bars immutable; tz policy to verify | Paid | Same purchase | Bundle with daily |
| Open interest per contract (roll studies; CoT cross) | NONE (raw files carry no OI field) | CME daily OI via vendor; CFTC CoT weekly (free) | 2019→now | date, conId, OI | As-published next morning; CoT Fri-release/Tue-positions | CoT free; vendor OI paid | OI absent from IBKR bars | Free CoT pull can start now (owner gate); vendor OI in bundle |
| CFTC CoT history incl. silver (driver 7) | Release schedule verified (FACT §4); no historical values | cftc.gov (primary, free) | 2006→now | weekly report CSV (legacy futures-only + TFF) | Fri 15:30 ET release, Tue positions; only 13 months on site → use archived historical datasets | Free | Not pulled (PREP, no purchases but pulls allowed only with owner gate on new pipelines) | Schedule with engine-prep |
| HG copper daily (framework §13 confirmation variable) | NOT in 10-symbol snapshot | Vendor (CME-licensed) | 2019→now | per-contract OHLCV | As-published | Paid | Absent from corpus | Add to vendor bundle |
| Short-rate + lease-rate series (H3 carry driver) | NONE in repo (gap measurements only) | FRED (SOFR/T-bill, free, vintage-aware); silver lease rates LBMA/IBA (paid) | 2019→now | daily rate series | FRED vintage-aware; lease delayed/paid | FRED free; lease paid | Not sourced | FRED pull free — schedule for engine-prep |
| PIT macro consensus/surprise archive (H-`event` designs) | Release schedules only (§4 FACT) | Primary actuals BLS/Fed (free); consensus = vendor archive | 2015→now | event, datetime_utc, survey_median, actual, vintage | Consensus as-known-before-release | Actuals free; consensus paid | No PIT consensus in repo | Owner: pick vendor or restrict to date-based designs |
| BBO depth / synchronous quotes (measured costs) | 1Y daily BID/ASK closes per contract (non-synchronous; close proxy only) | Vendor bbo-1m/1s | 2019→now | bid/ask/size ts | As-captured | Paid | Same purchase | Bundle; validate measured vs published after |

Priority for top-3 causal drivers (GC beta, rates/Fed, positioning/CoT): rows
1, 4, 6 (CoT row is free). This dossier does not condition on the wishlist.

## 7. Framework coverage

**Master §1 (10 questions):**
1. Underlying exposure: 5,000 oz physical silver; hybrid monetary/industrial
   metal with ~2x amplification to GC [FACT unit; amplification OBSERVED §3].
2. Participants: miners, industrial users, bullion traders/banks, macro funds,
   retail (disproportionate), MMs [POSTULATED; per-participant measurement
   NOT_RUN].
3. Exchange/sessions: COMEX Globex 18:00→17:00 ET (60-min break); RTH
   09:30–17:00 ET; DST-correct [FACT/OBSERVED S1+bars]; **raw bars RTH-only**
   [OBSERVED].
4. Size/tick/currency/margin/settlement: 5,000 oz; $0.005=$25/tick; USD;
   physical delivery; margins $33.5k–36.8k class [FACT/OBSERVED §1/§3].
5. Listed months / liquid expiries: 3 consecutive + Jan/Mar/May/Sep ≤23m +
   Jul/Dec ≤60m [FACT]; **liquid = H/K/N/U/Z measured; serials dead**
   [OBSERVED].
6. Liquidity migration: ≥10k-lot ramp 2–7 days before declared roll, 6/6
   cycles; old book ≤376 lots at roll [OBSERVED].
7. Dominant behavior: macro/monetary (GC beta 0.83 corr) + carry (6/6
   positive roll gaps) + squeeze/positioning episodes; cash-arb via
   COMEX-LBMA basis POSTULATED unmeasured [OBSERVED/POSTULATED].
8. Which session matters: cannot rank Asia/Europe/overnight vs US (overnight
   absent from data) [NOT_RUN]; within RTH, first 90 min carry ~35% of volume
   (30-day windows) [OBSERVED].
9. Tradeable contract per timestamp (PIT): nearest H/K/N/U/Z contract until
   its declared roll; never serial/deferred [OBSERVED-informed rule].
10. Vendor symbols ↔ expiries + reproducible continuous: localSymbol→conId in
    S1 (SIV6=760200581 etc.); cycle-chain + roll table (6 gaps) built here;
    back-adjustment delegated to engine (gaps measured) [FACT/OBSERVED].

**SI framework checklist (§1–§17) — status:**
- §1 Foundation (what contract represents / hedgers vs specs / fair value vs
  cash / liquid expiries / delivery distortion / session / minimal PIT data):
  answered above and §1; fair-value-vs-cash specifics (COMEX-LBMA basis)
  NOT_RUN.
- §2 Market structure (volume by session/expiry; roll speed; spread widening
  overnight/near-expiry; opening/settlement effects; stable selection rule;
  back-adjustment impact): volume by expiry + roll speed OBSERVED; spread
  near-expiry/era OBSERVED (close-proxy); spread overnight/event widening
  NOT_RUN (non-synchronous BID/ASK, RTH-only); opening/settlement effects
  NOT_RUN; selection-rule stability: calendar-cycle measured stable 6/6,
  volume variant measured ramp, OI NOT_RUN; back-adjustment impact on trend
  signals NOT_RUN (delegated to engine; gap sizes measured).
- §3 Causal driver table: §2 above, each row tagged.
- §4 Regime map: ONE regime measured (squeeze-bull-crash, 60% ann. vol, skew
  −1.8, exkurt 15); full regime taxonomy NOT_RUN (needs multi-year + macro
  series).
- §5 Event-study framework: calendars FACT (§4); 1m/5m/…/3d measurements
  NOT_RUN (intraday depth; no surprise data).
- §6 Term-structure/roll: raw panel built; cycle front chain built; roll
  gaps measured (6/6 +); calendar vs volume roll timing compared (2–7d); OI
  roll NOT_RUN; back-adjusted vs unadjusted NOT_RUN (engine); no vendor
  stitching exists to audit (CONTFUT unused by data lane) [OBSERVED].
- §7 Cross-asset: GC measured (corr 0.83, elasticity ~1.9, ratio 44–93);
  HG/DXY/real yields/equity-risk/solar proxies NOT in snapshot or NOT_RUN.
- §8/§15 Candidate signals: 5 hypotheses specified (§5) with mechanism +
  falsification; NO backtests run (PREP). Framework §15's four ideas map to
  H4 (convex beta), H2 (ratio reversion), H4-industrial variant (HG
  confirmation — blocked, no HG data), breakout-persistence idea NOT
  specified (would need range-break labels — rule-evaluation territory, NOT_RUN).
- §9 Backtest protocol: inputs prepared (per-contract panel, cycle chain,
  roll table, cost observables); protocol execution NOT_RUN (task
  classification).
- §10 Data checklist (Databento phase-1 ohlcv-1m/definition/statistics):
  mapped in §6.
- §11/§16 Failure modes: higher slippage than GC — consistent (SI liquid-era
  spread 4 ticks=$100 vs GC 5 ticks=$50/contract per S6/GC liquid measures —
  SI ~2x in $/contract) [OBSERVED]; retail-driven squeeze — LITERALLY MEASURED
  in-window (Jan-2026 +14%/−31% days) [OBSERVED]; unstable gold beta — rolling
  corr 0.65–0.91, elasticity untested [OBSERVED partial]; structural
  industrial-demand change — unmeasurable in-window [NOT_RUN].
- §12 Deliverables: items 1–8, 10 partial (this dossier); 9 (backtest
  report) and rejection log NOT_RUN.
- §13 Contract-specific driver map: 7 primary drivers covered in §2 (gold,
  industrial growth, USD/real rates, solar demand, mine supply, risk
  appetite, positioning); confirmation variables: GC measured, HG/DXY/yields
  NOT_RUN.
- §14 Contract-specific questions (precious vs industrial regimes; GC-beta
  stability; copper confirmation; liquidity penalty vs GC): beta stability
  partially measured (corr band, elasticity point); precious-vs-industrial
  regime split NOT_RUN; HG confirmation NOT_RUN (no data); executable-edge
  penalty vs GC: spread ~2x in $/contract, slippage NOT_RUN [OBSERVED
  partial].
- §17 First research sprint: items 1–3 done at legal depth (panel, roll/
  liquidity diagnostics, daily/session stats); 4–6 blocked on data (§6); 7
  (rejection) pending engine era.

**Open questions (carried to handoff):** (1) exact old/new volume crossover
day within the 2–7-day pre-roll window (needs overlapping both-contract
volume or prospective collection); (2) whether SI serial months (Oct/Nov)
were ever liquid pre-2025 (deferred marks only — unverifiable in snapshot);
(3) SI exchange fee (IBKR tables JS-hidden; CME blocked) — cost model gap;
(4) COMEX price-limit schedule unverified (CME blocked) — matters after the
measured −31% day; (5) LBMA lease-rate sourcing for H3 carry test.
