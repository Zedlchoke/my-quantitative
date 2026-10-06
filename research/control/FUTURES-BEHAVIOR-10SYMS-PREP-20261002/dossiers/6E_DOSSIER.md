# 6E DOSSIER — Euro FX Futures

- Symbol: **6E** (CME, trading class 6E, product symbol EUR in IB; marketName 6E)
- Exchange: **CME** (CME Group), Globex electronic
- Generated (UTC): 2026-10-02
- Author lane: **SYMBOL-DOSSIER-6E** (task FUTURES-BEHAVIOR-10SYMS-PREP-20261002)
- Inputs:
  - `owner_framework/6E_RESEARCH_FRAMEWORK.md` sha256
    `db5fbaff7d16994ddb7a7fc60c04d3198b3f601e9118babab68e2cd0de1aedcd`
    (from `owner_framework/SHA256SUMS.txt`)
  - `owner_framework/00_MASTER_FRAMEWORK.md` sha256
    `a75571b8017b13b5ff6552755d1334b03db640ebc26a6b4c9ad4323ca16d3c74`
  - `research/control/FUTURES-DATA-10SYMS-V1/FINAL_REPORT.md` (+ HANDOFF.json,
    S9_INDEPENDENT_VERIFY.md, S1_IDENTITY.json, S6_FRONT_SPREADS.json,
    costs/IBKR_futures_commissions_2026-10-02.json,
    costs/SPECS_MARGINS_PUBLIC_2026-10-02.md) — untracked snapshot 2026-10-02, read-only
  - Raw data (read-only): `~/.my-quantitative-data/futures-10syms-v1/raw/6E_*`
    (20 contracts × TRADES daily-6Y / hourly-30D / 1min-2D / BID+ASK daily-1Y,
    plus front/next/expired 3D probes). All bars `useRTH=true` (IB "liquid hours"
    08:30–16:00 US/Central) — see §1/§3 for the FX-specific consequences, which are
    more severe than for equity-index futures.
  - Own analysis: `analysis/6E_descriptives.py` → `analysis/6E_descriptives.json`
    (every OBSERVED number below is reproducible from these).
  - Sibling evidence in same task: `dossiers/ES_DOSSIER.md` (methodology baseline
    for roll-gap measurement, shared macro calendars fetched 2026-10-02).
- Claims taxonomy used throughout: **FACT** (primary source + URL + access
  date), **OBSERVED** (computed from raw data; script + window), **POSTULATED**
  (mechanism reasoning, unmeasured), **NOT_RUN** (not measured — never inferred
  PASS). This dossier is PREP: 0 PnL, 0 scored runs, 0 parameter selection.

---

## 1. Mechanics

- **Underlying exposure** [FACT]: EUR 125,000 vs USD per contract, quoted in
  **USD per 1 EUR** (same family convention as 6B/6A; 6J is USD-per-JPY).
  Contract unit "125,000 euro" per NinjaTrader spec mirror
  https://www.ninjatrader.com/futures/futures-contracts/currency/euro-forex and
  AMP https://www.ampfutures.com/trading-info/contract-specifications/ (both
  accessed 2026-10-02 via costs/SPECS_MARGINS_PUBLIC_2026-10-02.md). CME's own
  product page title "Euro FX **EUR/USD** Overview" fetched 2026-10-02 via web
  reader (https://www.cmegroup.com/markets/fx/g10/euro-fx.html — CME direct
  HTTP-403 to non-browser clients, same transport wall as
  FUTURES-DATA-10SYMS-V1 `cme_check/`; web reader renders page shell). Quote
  scale machine-checked: all 6E closes in this snapshot are 1.0109–1.3001
  (front-scale era 1.1268–1.2005) — USD-per-EUR, no 6J-style inversion risk
  [OBSERVED, 6E_descriptives.json `contract_panel`].
- **Economic role / participants** [POSTULATED, framework §"Key participant
  groups"; participant identity itself NOT_RUN on our data]: banks/corporates
  hedging EUR-USD receivables/payables, asset managers and macro funds taking
  policy-differential views, CTAs, central-bank-adjacent reserve managers
  (POSTULATED), market makers, and cash-futures arbitrageurs anchoring the
  futures basis to CIP fair value (see roll-gap row in §2). Positioning
  composition per participant: NOT_RUN (no CoT pull this session).
- **Tick / multiplier / quote convention** [FACT, machine-verified]: multiplier
  "125000", minTick 5e-05, currency USD, timeZoneId US/Central on **every**
  resolved 6E contract in S1_IDENTITY.json (36 active-chain + 4 expired =
  uniform; S9 caveat: multiplier/minTick not re-derivable from raw bars —
  identity authority is S1). minTick 5e-05 USD/EUR × 125,000 = **$6.25/tick**.
  Public conflict noted in costs dossier (NinjaTrader/AMP half-tick $6.25 vs
  legacy TradingCharts/Wikipedia full-tick $12.50; official CME adjudication
  CME_BLOCKED_TRANSPORT) — for THIS entitlement the machine value 5e-05 governs.
- **Sessions and DST** [FACT, machine-verified from S1 `tradingHours` /
  `liquidHours` for 6EV6, fetched 2026-10-02]: Globex 17:00 CT → 16:00 CT next
  day (23h, 60-min maintenance break 16:00–17:00 CT; Sunday open 17:00 CT);
  CME page text "Nearly 24-hour access" (fetched 2026-10-02, web reader).
  IB "liquid" (RTH) window **08:30–16:00 CT**. S9 verified raw intraday offsets
  DST-correct at each bar's own date (-05:00 CDT observed in the files).
  **All raw daily/hourly/1-min bars are `useRTH=true`** [OBSERVED, raw
  metadata]: every bar covers only 08:30–16:00 CT. For 6E this means the
  captured window **excludes the Asian session, the entire London morning
  (≈02:00–08:00 CT), ECB decisions (≈14:15 CET ≈ 07:15 CT) and the 08:30 ET
  (07:30 CT) US data block** — the parts of the FX day that carry most EUR/USD
  information. Only FOMC (14:00 ET = 13:00 CT) and the London afternoon fall
  inside the captured window. Everything before 08:30 CT is measurable only as
  the open-vs-prior-close gap (§3). Session-behavior claims beyond this slice:
  NOT_RUN.
- **Holidays** [OBSERVED, S1 machine windows]: `20261003:CLOSED` (Saturday) and
  Sunday CLOSED until 17:00 CT open — same weekly pattern as ES. **IMM expiry
  dates shift when US holidays fall inside the 2-business-day window**
  [OBSERVED, computed across all 20 contracts, 6E_descriptives.json
  `expiry_rule_check`]: 17/20 last-trade dates match naive Mon–Fri
  "2 business days before 3rd Wednesday"; the 3 exceptions are explained by
  MLK Day / Presidents' Day: 6EF7 → 2027-01-15 (MLK Mon 2027-01-18), 6EG7 →
  2027-02-12 (Presidents' Day Mon 2027-02-15), 6EF8 → 2028-01-14 (MLK
  2028-01-17). With holidays modeled: **20/20 match** "2nd exchange business
  day before the 3rd Wednesday of the delivery month". Naive weekday
  arithmetic in roll/expiry code is wrong for Jan/Feb FX contracts in some
  years.
- **Delivery / first-notice / expiry / price limits**:
  - Physically delivered (EUR 125,000 vs USD) at expiry, value the 3rd
    Wednesday of the delivery month [FACT, NinjaTrader spec "Deliverable" +
    Wikipedia https://en.wikipedia.org/wiki/Currency_future, accessed
    2026-10-02 via costs dossier]. No first-notice-day mechanic for FX
    (settlement by delivery, not warehouse receipt) [POSTULATED — CME
    rulebook text CME_BLOCKED_TRANSPORT].
  - Last trading **09:16 CT (10:16 ET)** on the last-trade date [FACT, S1
    `lastTradeTime` "09:16:00" on every contract carrying it; corroborates NT
    spec "10:16 am ET"].
  - Price limits / position limits: NOT_RUN (CME rulebook unreachable this
    session; no public mirror fetched).
- **Listed months & liquid maturities** [FACT + OBSERVED]: S1 active chain
  resolves **monthly (serial) contracts through ~Sep 2028, then quarterly
  HMUZ through Mar 2031** (36 contracts; e.g. all 12 months of 2027 listed;
  2028 has F,G,H,J,K,M,N,Q,U,Z — no V8/X8 — then Z8, H9…) [OBSERVED, S1].
  CME page: "convenient monthly and quarterly futures" [FACT, fetched
  2026-10-02]; NinjaTrader text "Quarterly contracts (Mar, Jun, Sept, Dec)
  listed for 20 consecutive quarters" + Wikipedia "+3 serial months" [FACT
  via costs dossier — under-describes the observed monthly listing depth].
  **Liquid maturity = front quarterly ONLY**: front quarterlies print median
  56k–76k contracts/RTH-day near expiry (max 208k), deferred quarterlies
  median 1–60/day, and **serial (non-HMUZ) months median 0–115/day (max 659)**
  [OBSERVED, `quarterly_vs_serial` + `contract_panel`]. Serial months are
  real listed contracts (38–67% flat bars per FINAL_REPORT) but never become
  the liquidity vehicle.
- **Liquidity migration front→next** [OBSERVED, `liquidity_migration_quarterly`]:
  migration is **quarterly→next-quarterly and happens in the expiry (IMM) week
  itself**: the next quarterly first reached ≥50k contracts/RTH-day on
  2025-12-12, 2026-03-13, 2026-06-11, 2026-09-11 — i.e. 1–2 sessions (2–4
  calendar days) before each old quarterly's last trade date (2025-12-15,
  2026-03-16, 2026-06-15, 2026-09-14). The serial month that is "next listed" in between is **skipped
  entirely**: in Sep-2026 the serial 6EV6 (nearest expiry, IB S1 "front")
  traded median 214/day (max 659) while 6EZ6 traded median 71,234/day the same
  21 sessions — a ~333:1 volume ratio [OBSERVED, `literal_rule_serial_front_windows`].
  Exact old-vs-new volume crossover NOT observable (each expired contract's
  raw file ends at its fetch window = day-1 of expiry month).
- **PIT contract selection + roll rule (baseline + measured adaptations)**:
  - Baseline (data lane declared): hold until last session BEFORE day-1 of
    expiry month, roll to next listed at that close; listing calendar known
    years ahead → PIT-legal [FACT, FINAL_REPORT §Roll rule].
  - **Literal application to 6E is broken** [OBSERVED]: "next listed" after a
    quarterly is a serial month (e.g. 6EU6 → 6EV6 on 2026-08-31): the literal
    chain then holds a 100–600-lot book for ~21 sessions while the quarterly
    carries 70–210k. Also the declared timing rolls ~2 weeks early: at all 4
    measured declared rolls the old quarterly still traded 23k–88k/day while
    the next quarterly had 530–1,365 (thin windows <10k on the chain:
    2025-12-01..09, 2026-03-02..05, 2026-06-01..04 (+06-08), 2026-09-01..08)
    [OBSERVED].
  - **Quarterly-only adaptation (used for all §3 stats)**: same declared
    timing, but roll target = next HMUZ. Still 4–7 sessions of thin book per
    quarter; the market's own migration completes 2–3 sessions before expiry —
    so an expiry-week calendar roll (e.g. roll at the last session of the week
    before IMM week, or T-2 sessions before old expiry) matches observed
    migration better than the declared date. CME's own product page links an
    "FX Quarterly Roll Analyzer Tool" [FACT, fetched 2026-10-02] — quarterly
    roll is the exchange-recognized convention for this complex.
  - **Roll cost / gap** [OBSERVED, `declared_rule_rolls_quarterly_chain`]:
    adjacent-quarterly close gaps at the 4 declared rolls were **positive
    every time**: +106, +102, +86, +82 ticks = +0.456%, +0.431%, +0.368%,
    +0.353% of level per quarter (annualized +1.83%, +1.73%, +1.48%, +1.42%;
    $662.50, $637.50, $537.50, $512.50 per contract). Mechanism: covered-interest
    parity — deferred EUR/USD futures sit above near expiry while USD short
    rates exceed EUR rates [POSTULATED; no rate series in repo to verify].
    Unadjusted continuous series therefore embed ~+0.35–0.46% artificial jumps
    at rolls (observed unadjusted boundary next-session returns: +0.51%,
    −0.49%, +0.07%, +0.13% — the sign flips when the true market move offsets
    the gap) — back-adjustment is mandatory for level/trend work, and
    roll-boundary returns must be excluded [POSTULATED→engine spec].
  - Alternatives for engine A/B: (a) volume roll (crossover unmeasurable
    here, NOT_RUN); (b) OI roll — NOT_RUN (no OI field in raw); (c) calendar
    expiry-week roll (deterministic, matches measured migration; must apply
    the IMM holiday shift above).
  - **Symbol-mapping trap** [OBSERVED]: IB's expiry-nearest "front" (S1 front
    = 6EV6 serial on 2026-10-02) is NOT the liquid front (6EZ6). Any engine
    keyed on nearest-expiry or IB front will price/cost a dead book: even the
    measured spread differs — last-20-day median BID/ASK close-proxy spread
    3.0 ticks ($18.75) on 6EV6 vs 1.0 tick ($6.25) on 6EZ6 [OBSERVED;
    reconciles S6_FRONT_SPREADS 6E $18.75, which used the expiry front].

## 2. Causal driver map

Master-framework buckets relevant to 6E: Macro, Cross-asset, Positioning, Term
structure, Microstructure, Event-driven. Fundamental/physical applies only via
energy terms-of-trade (euro-area energy imports). Framework §13 primary drivers
covered by rows 1–7.

| # | Driver | Source → mechanism | Predicted sign / horizon | Regime dependency | Confounders | Falsification test | PIT data source (primary, access date) | Evidence class |
|---|--------|-------------------|--------------------------|-------------------|-------------|--------------------|----------------------------------------|----------------|
| 1 | Fed–ECB policy differential (level & change) | FOMC/ECB communications → relative discount rates + carry-attraction flows → EUR/USD repricing | Wider USD-over-EUR rate gap → EUR down; horizon days–months | Strongest when policy paths diverge actively; weakest when priced-in | Growth/inflation news same window; risk sentiment | Rate-differential changes vs subsequent 1M/3M 6E direction, split by divergence regime | FOMC calendar federalreserve.gov (fetched 2026-10-02); ECB GC calendar ecb.europa.eu (fetched 2026-10-02); rate series NOT in repo (FRED free, un-sourced) | Calendars FACT; differential effect NOT_RUN |
| 2 | US macro surprises (CPI, NFP) | 8:30 ET surprises → USD repricing → 6E moves opposite USD | Hot US print → 6E down; minutes–days | Fed-reaction-function regimes flip sign (growth-vs-rates connotation) | Same-block releases; EUR-area news same day | Release-day 6E returns conditional on signed surprise vs non-event days | BLS schedules bls.gov (fetched 2026-10-02, sibling-lane verified); consensus/surprise archive NOT in repo | Calendar FACT; effect NOT_RUN |
| 3 | Euro-area surprises (HICP, PMI, ECB) | EA data → ECB path repricing → EUR | Hot EA print → 6E up; minutes–days | ECB reaction regime | US news same window | EA-surprise-conditional returns vs non-event days | Eurostat/PMI calendars NOT fetched this session | Calendar NOT_RUN; effect NOT_RUN |
| 4 | Energy terms of trade (framework §13/§15) | Energy price shocks worsen euro-area (importer) trade balance & real income → EUR down disproportionately in stress | Up energy → EUR down; weeks | Energy-stress regimes only | Global risk-off co-moves (USD bid); US energy exposure differs | EUR response to CL/NG shocks split by energy-stress regime | CL/NG raw in snapshot (cross descriptives NOT_RUN this session — lane scope 6E) | Mechanism POSTULATED; measurement NOT_RUN |
| 5 | Risk sentiment / USD liquidity | Global risk-off → USD bid (funding/safe-haven) → 6E down | Risk-off → 6E down; days | Crisis vs normal | USD policy simultaneity | 6E vs ES/risk-asset co-movement conditional on vol regime | ES raw in snapshot (NOT_RUN this session); DXY/liquidity series NOT in repo | POSTULATED |
| 6 | European political/fiscal risk | Sovereign-spread/political shocks → EUR risk premium | Risk event → 6E down; event horizon | Stress regimes | Global USD moves | Event-window decomposition vs DXY-style control | No political-event dataset sourced | POSTULATED; NOT_RUN |
| 7 | Positioning (CFTC CoT, OI) | Crowded EUR net length → squeeze/convexity on shocks | Extremes → larger adverse moves on surprise; weekly horizon | Crisis vs normal | CoT aggregates reportables; release ≠ position date (§4) | CoT-extreme weeks vs subsequent 6E vol/returns | Release schedule cftc.gov (fetched 2026-10-02); historical values NOT pulled | Calendar FACT; effect NOT_RUN |
| 8 | Term structure / CIP carry (roll gap) | Futures fair value = spot × (r_USD−r_EUR)×t → calendar spread absorbs rate differential | Roll gap >0 while r_USD>r_EUR (4/4 measured positive, +82..106 ticks ≈ +1.4–1.8%/yr) | Flips if EUR rates exceed USD | Rate-path expectations vs realized; delivery-month microstructure | Gap sign/level vs contemporaneous USD−EUR short rates each quarter | Gaps OBSERVED from raw; rate series NOT in repo | Gaps OBSERVED; CIP link POSTULATED |
| 9 | Microstructure: serial/quarterly liquidity cliff + roll timing | Declared rule (i) lands on serial books if applied literally, (ii) rolls 2 weeks before migration even quarterly-only | Execution-cost spike + sparse prints in thin windows; quarterly | Any; mechanical | Holiday sessions; serials' stale quotes | Compare volume/flatness inside vs outside thin windows; serial vs quarterly same-day volume ratio | Raw files (measured §1/§3) | OBSERVED |
| 10 | Session information timing (Asia/London vs US RTH) | Most EUR/USD information lands before 08:30 CT (ECB ~07:15 CT, US 8:30 ET = 07:30 CT, London morning) — all outside captured bars; arrives in-snapshot only as the RTH-open gap (std 0.26% = ~79% of RTH-day ret std) | Gap carries majority of measured-day variance; sign conditional | Vol/crisis regimes | Daily open = RTH open only (no 24h marks in data) | Gap-vs-day decomposition across vol regimes (needs multi-year front-scale data) | Raw daily (measured §3) | OBSERVED (descriptive); hypothesis NOT_RUN |

## 3. Behavior (measured where legal)

All computed by `analysis/6E_descriptives.py` → `analysis/6E_descriptives.json`
from raw per-contract daily TRADES (RTH bars 08:30–16:00 CT, useRTH=true),
quarterly-only front chain (declared roll timing, HMUZ targets), unadjusted,
thresholds only via strict past/trailing windows. Two samples used throughout:
(a) **full unadjusted quarterly chain** 2020-12-15→2026-10-01 (n=1475; mostly
settlement-derived marks pre-2025 — official exchange marks usable as
reference/signal prices, NOT fills, per FINAL_REPORT); (b) **front-scale era**
= chain front ≥10k contracts/RTH-day: **2025-09-09→2026-10-01, n=247** (robustness:
≥25k from 2025-09-10, n=236; ≥50k from 2025-09-16, n=191). The era starts at
the Sep-2025 IMM roll — before that, the true market fronts (6EU5 etc.) are
beyond the expired-secdef wall and the chain holds deferred marks.

- **Session/volume behavior**:
  - Front-scale era: median front volume 65,869 contracts/RTH-day; ≥25k on
    236/247 days (95.5%), ≥50k on 191/247 (77.3%); max 208,059 (2026-10-01)
    [OBSERVED].
  - RTH hourly profile (front 6EZ6, 2026-08-20→2026-10-01, 30 days):
    09:00 21.4%, 10:00 17.7%, 13:00 15.2%, 12:00 10.6%, 08:30-half-hour 9.1%,
    fading to 3.4% in the 15:00 hour — morning-heavy (late-London overlap +
    US morning), NOT the ES-style U-shape; last two hours only ~12% [OBSERVED,
    30-day window — not a structural constant].
  - **Asian session, London morning, ECB window, 8:30-ET block: NOT_RUN**
    (useRTH=true files; the prime EUR/USD sessions are absent — §1). CME
    states "Nearly 24-hour access" [FACT] — the data does not contain it.
  - Serial months: median 0–115/day, max 659; deferred quarterlies median
    1–60/day — never tradable at size [OBSERVED, panel].
- **Volatility behavior**:
  - Front-scale era daily simple returns (n=247, roll boundaries excluded):
    mean −1.6bp/day, std **0.333%**, min −0.87%, max +0.99%, skew +0.31,
    q05..q95 −0.59%..+0.57%; annualized-vol descriptor **5.3%** [OBSERVED].
    Single-regime caveat: one ~13-month window, EUR drifting 1.20→1.13; no
    crisis sample.
  - Full unadjusted chain (settlement-derived era incl.): std 0.446%/day, min
    −1.81%, max +2.30%; roll-boundary exclusion changes nothing material
    (0.4466% vs 0.4464%) because boundary returns land on the next session
    [OBSERVED, caveat per FINAL_REPORT].
  - Rolling 63-day vol (full chain): min 0.25%, median 0.39%, max 0.82%
    (daily units) — ~3.3× vol range across the deeper (settlement-mark)
    sample [OBSERVED].
  - |ret| lag-1 autocorr: **0.136** front-scale era vs 0.171 full chain —
    mild daily vol clustering, stronger in the deeper sample [OBSERVED].
- **Trend behavior**: descriptive only — front-scale era mean −1.6bp/day over
  a ~−6.1% level drift (1.2005→1.1268 range within era); no trend/mr test run
  (rule evaluation = NOT_RUN by task classification).
- **Event behavior**: FOMC/ECB/CPI/NFP-day conditional behavior NOT_RUN
  (needs event alignment + intraday depth or multi-year daily; no
  consensus/surprise dataset in repo — §4).
- **Curve behavior**: 4/4 measured quarterly roll gaps positive (+82..+106
  ticks, +0.35..+0.46%/quarter, ann. +1.4–1.8%) [OBSERVED]; deferred-quarterly
  quotes exist but stale (median 1–60 vol) — calendar-spread behavior beyond
  roll dates NOT_RUN. Deep (settlement-mark) era carries the same CIP upward
  slope in marks [POSTULATED identification; marks OBSERVED].
- **Seasonality (descriptive)**:
  - Full chain by month: all |means| ≤ 6.3bp (Sep most negative −6.3bp, n=127);
    highest vol months Mar 0.55%/day, Nov 0.54% (settlement-mark era included)
    [OBSERVED, deep-era caveat].
  - Front-scale era by weekday (n≈49–56/weekday): Mon/Tue means +2.1/+2.3bp,
    Wed −7.0bp, Thu −3.9bp, Fri −3.5bp; vol Tue 0.34% > Fri 0.29% — window too
    short for anything but description [OBSERVED].
- **Hidden-session (overnight→RTH-open) gap** — for 6E this gap spans Asia +
  full London morning + ECB + 8:30-ET US releases (everything outside
  08:30–16:00 CT): front-scale era (n=247): mean −0.6bp, std **0.265%**
    (≈79% of the RTH-day return std), median −1.5 pips, q05..q95
    −0.39%..+0.44%, max +1.12%; |gap| ≥ 2× trailing-20d mean|ret| on 11.3% of
    all days (n=1474, settlement era incl.) [OBSERVED, strict past
    normalization]. Biggest 5 gaps (settlement-era, all pre-front-scale):
    2025-04-03 +231.5 pips (US tariff-shock window), 2022-10-04 +210.5,
    2022-07-05 −197.0, 2022-03-09 +190.5, 2022-09-23 −188.0 [OBSERVED].
- **Spread/cost observables** (published ≠ measured user costs):
  - Front (quarterly chain) BID/ASK close-proxy spread, front-scale days
    (n=247): **median 1.0 tick = $6.25, p90 2.0 ticks = $12.50, 0 crossed
    days**; all 465 chain days with quotes (incl. deferred-mark era): median
    2 ticks, p90 4 ticks ($50) [OBSERVED, close-to-close proxy — not an
    executable spread]. Serial/expiry front instead: 3.0 ticks = $18.75 median
    over the last 20 days on 6EV6 vs 1.0 tick on 6EZ6 — reconciles
    S6_FRONT_SPREADS' $18.75 (expiry-front convention) [OBSERVED].

> **ERRATUM (2026-10-02, round co-owner-review-fix-1, lane HANDOFF-RESEARCH)
> — tick/USD consistency in the spread bullet above.** "p90 4 ticks ($50)"
> mixes tick conventions: at this dossier's machine-verified tick value
> (**$6.25/tick** = minTick 5e-05 × 125,000), **$50.00 = 8 ticks**, while
> 4 ticks = **$25.00**. The authoritative number is the JSON value
> `bid_ask_1y.p90_spread_usd_all` = $50.0 (analysis/6E_descriptives.json),
> so the correct statement is **"p90 ≈ 8 ticks ($50)"**; a "4 ticks = $50"
> reading holds only under the rejected legacy full-tick ($12.50) convention
> (§1 conflict note). Superseded wording preserved verbatim above.
> **Explicit units for the roll-gap figures cited in this dossier** (§1, §2
> row 8, §3, §5 H1/H2): **+82..+106 are TICK COUNTS** — price increments of
> 0.00005 USD/EUR, i.e. a raw price difference of +0.0041..+0.0053 USD/EUR —
> NOT dollar amounts; the per-contract cash equivalents are
> **+$512.50..+$662.50** (ticks × $6.25), as already correctly stated in §1.
> Front-scale spread medians (1 tick = $6.25; p90 2 ticks = $12.50) and the
> serial-front 3-tick = $18.75 figure are correct as written.
  - Commission [FACT, document-class]: IBKR $0.85/side standard futures
    (tier ≤1000) + exchange + regulatory pass-through; 6E-specific exchange
    fee NOT_FETCHED (JS tables did not render; CME blocked); the only worked
    all-in example on the page is ES $2.24 (costs/IBKR_futures_commissions_
    2026-10-02.json, fetched 2026-10-02). Slippage:
    NOT_RUN_NO_DECLARED_VALUE.
  - Margin [FACT, broker-class public; CME SPAN blocked]: NinjaTrader
    maintenance $2,400 / initial $2,640 (as of 2026-08-31,
    ninjatrader.com/pricing/margins); AMP maintenance $2,310 (2026-10-02) —
    <4% apart.
  - Roll cost: gaps measured above; as an executed two-book cost NOT_RUN
    (thin-book side unmeasurable in snapshot).

## 4. Event calendar

All times: release time (source-stated or tagged) + exchange tz (US/Central,
CT = America/Chicago; captured bars 08:30–16:00 CT only — see the collision
notes, which are PIT/execution-critical for THIS snapshot).

| Event | Actual release time (UTC / CT) | Vintage & PIT properties | Effective vs available vs retrieved | Evidence class |
|---|---|---|---|---|
| FOMC decisions 2026 | Meetings Jan 27-28, Mar 17-18*, Apr 28-29, Jun 16-17*, Jul 28-29, Sep 15-16*, Oct 27-28, Dec 8-9* (* = SEP); decision day-2, statement ~14:00 ET (19:00 UTC) = 13:00 CT — statement time POSTULATED (calendar page does not state it); minutes +3 weeks [page-verified] | Statement final at release; SEP projections revised each SEP meeting | Effective = statement timestamp; available same minute on federalreserve.gov; retrieved in repo: NO | Calendar FACT (federalreserve.gov/monetarypolicy/fomccalendars.htm, fetched 2026-10-02); statement time POSTULATED |
| ECB Governing Council monetary policy meetings | 2026 remaining: Oct 28-29 (press conference Oct 29), Dec 16-17 (pc Dec 17); latest past MPC press conference 2026-09-10; decision ~14:15 CET / pc 14:45 CET ≈ 07:15/07:45 CT — time-of-day NOT on fetched pages (POSTULATED) | Decisions final at release; staff projections quarterly | Effective = decision/pc timestamps; available on ecb.europa.eu same minute; retrieved: NO | Calendar FACT (ecb.europa.eu/press/calendars/mgcgc/html/index.en.html + press index, fetched 2026-10-02); announcement time POSTULATED |
| CPI (BLS, US) | 8:30 AM ET = 12:30/13:30 UTC = **07:30 CT — BEFORE the captured 08:30 CT bar window**; 2026: Jan 13, Feb 13, Mar 11, Apr 10, May 12, Jun 10, Jul 14, Aug 12, Sep 11, Oct 14, Nov 10, Dec 10 | Index not typically revised; seasonal factors revised annually (policy text not re-fetched) | Effective 8:30 ET; seasonal-vintage note for SA series | Schedule FACT (bls.gov/schedule/news_release/cpi.htm, verified 2026-10-02) |
| Employment Situation / NFP (BLS) | 8:30 AM ET = 07:30 CT (pre-window); 2026: Jan 9, Feb 11, Mar 6, Apr 3, May 8, Jun 5, Jul 2, Aug 7, Sep 4, Oct 2, Nov 6, Dec 4 | Prior-two-month payroll revisions standard — strict PIT needs vintage/ALFRED | Effective 8:30 ET | Schedule FACT (bls.gov/schedule/news_release/empsit.htm, verified 2026-10-02) |
| Eurostat HICP flash / PMIs (EA) | NOT fetched this session — | — | — | Calendar NOT_RUN |
| CFTC CoT (Financial Futures, incl. EUR) | "generally published each Friday at 3:30 pm ET" (14:30 CT); positions as of **prior Tuesday** close | Position date (Tue) ≠ release (Fri) — PIT lag ≥ 3 days; holiday shifts per CFTC | Earliest legal observation Fri 15:30 ET | FACT (cftc.gov/MarketReports/CommitmentsofTraders/index.htm, fetched 2026-10-02) |
| 6E expiry (IMM) | Last trade 09:16 CT, 2nd exchange-business-day before 3rd Wednesday of delivery month (holiday-shifted: 2027-01-15, 2027-02-12, 2028-01-14) | Contract calendar published years ahead (S1 resolves to 2031) | Fully knowable in advance | FACT (S1 lastTradeTime) + OBSERVED (holiday shift computed 20/20) |
| Quarterly roll week (market migration) | Next quarterly ≥50k on 2025-12-12, 2026-03-13, 2026-06-11, 2026-09-11 (1–2 sessions before old expiry) | Determinable PIT only with same-day volume; pre-declared calendar proxy = expiry-week | Measured ex-post here; forward rule = deterministic IMM-week calendar | OBSERVED (4 cycles) |

Consensus/surprise datasets: none in repo; surprise-adjusted designs blocked
until a PIT consensus archive is sourced (owner decision). Timing collision
summary for this snapshot: ECB (~07:15 CT) and US 8:30-ET block (07:30 CT)
release **before** the first captured bar each day; FOMC (13:00 CT) is inside
the captured window — event studies at M1 depth would see the ECB/US-data
reaction only as the 08:30 CT open gap [OBSERVED window arithmetic from §1].

## 5. Hypotheses (ranked by testability × causal plausibility — NOT by PnL)

Corpus-1200 reuse: none checked — corpus not provided to this lane. FX-spot
ideas referenced below are **POSTULATED transfers** (futures differ in basis =
CIP carry, roll cost measured +0.35–0.46%/quarter, and tick/commission cost
structure) — never "already valid".

**H1 — Quarterly-only contract selection + expiry-week roll alignment
(mechanics-level, testable NOW).**
- PIT condition (observable): calendar-only — front = nearest **HMUZ**
  contract; roll at the last session of the week before IMM expiry week (or
  T-2 sessions before old last-trade date), with the IMM holiday shift
  (MLK/Presidents) applied.
- Prediction: avoids (i) serial-month books (median 214 vs 71,234 same window,
  333:1) and (ii) 4–7 declared-rule thin sessions per quarter; matches the 4/4
  measured migration ramps (1–2 sessions before old expiry).
- Mechanism: quarterly IMM expiries concentrate options/roll/swap-related
  flow (CME's own "FX Quarterly Roll Analyzer" institutionalizes this);
  serials never attract the migration.
- Entry/exit (construction rule, not a trade): switch reference contract at
  declared calendar time; TP/SL/direction N/A.
- Universe/roll: 6E HMUZ; sizing N/A; cost model: measured roll gap
  (+82..+106 ticks) + roll-week two-book execution (thin-side cost NOT_RUN).
- Invalidation: a cycle where next-quarterly ramp deviates >3 sessions from
  IMM week; or serial-month volume exceeding next-quarterly during any
  migration window.
- Counter-hypothesis: migration is volume/OM-driven, not calendar (exact
  crossover unmeasurable here — prospective collector can test).
- Failure conditions: nearest-expiry or IB-"front" symbol mapping (lands on
  serials); naive Mon–Fri expiry arithmetic (Jan/Feb holiday shift); vendor
  continuous instead of own chain.
- Data requirements: ALREADY MET by raw daily files (§1/§3). Floor: none.
  Budget: 0.

**H2 — Roll-gap (CIP) sign tracks USD−EUR short-rate differential.**
- PIT condition: at each quarterly roll, adjacent-close gap (measured) vs
  contemporaneous ~3M USD and EUR short rates.
- Prediction: gap > 0 while r_USD > r_EUR (4/4 measured positive 2025-11→
  2026-08, +1.4–1.8%/yr); sign flips if EUR rates rise above USD.
- Mechanism: covered-interest parity anchors deferred futures vs spot
  (cash-futures arbitrage row, §2 #8).
- Entry/exit/TP/SL: N/A (structural relation; informs continuous-construction
  drift + calendar-spread ideas).
- Direction: N/A; universe: adjacent HMUZ pairs; sizing N/A; cost model:
  spread legs (front median 1 tick).
- Invalidation: persistent positive gap while r_USD < r_EUR (would indicate
  hedging-flow premium over CIP).
- Counter-hypothesis: gaps driven by roll-flow pressure, not rates.
- Failure conditions: using settlement-derived deferred closes as tradable
  (marks, not fills); roll-boundary returns left in unadjusted series.
- Data: gaps OBSERVED; rate series NOT in repo → FRED (free) pull needed —
  PARAM-GAP until sourced. Floor: ≥8 quarters for a sign statement (4
  measured; deeper gaps exist in settlement marks but are not tradable).

**H3 — Post-release persistence on FOMC days (in-window releases only).**
- PIT condition: FOMC decision timestamps 13:00 CT (inside captured RTH
  window, unlike ECB/8:30-ET events which are pre-window); surprise measure
  needs a PIT consensus archive (NOT in repo).
- Prediction: 30–60-min post-decision drift continues repricing direction;
  strongest in active-divergence regimes, weakest when priced-in.
- Mechanism: slow diffusion across participant horizons + dealer inventory
  smoothing [POSTULATED].
- Entry: M1 close ≥5 min after statement; exit: +X hours / session close;
  TP/SL/time: pre-declared before any run (PARAM-GAP — thresholds cannot be
  set without a look-ahead-free selection protocol); direction:
  surprise-sign; universe: front HMUZ (H1 rule); sizing: vol-scaled declared
  formula; cost model: $0.85+exch/side + 1–2 ticks ($6.25–12.50 measured
  median/p90).
- Invalidation: edge disappears with 5-min entry delay or 2× costs (master
  §6 stop conditions).
- Counter-hypothesis: full adjustment within first minutes (macro efficiency).
- Failure conditions: same-bar execution at 13:00; using ECB/8:30-ET events
  as M1 in-window events (they are pre-window in this snapshot); revised
  (non-vintage) macro data.
- Data: BLOCKED — M1 depth = 2D/contract + ~10 months hourly; need M1 from
  ≥2019 + PIT consensus. Floors: ≥40 events/class. Budget: vendor history
  (owner decision).

**H4 — US-vs-EA macro-surprise differential (framework §14/§15).**
- PIT condition: signed US surprise minus signed EA surprise (CPI/NFP/PMI),
  same-day or next-session 6E response.
- Prediction: differential predicts 6E direction better than US surprise
  alone; strongest when both central banks reaction-function-sensitive.
- Mechanism: relative-policy-path repricing [POSTULATED].
- Entry/exit: prior close → +1/+3 sessions; TP/SL: pre-declared PARAM-GAP;
  direction: differential-sign; universe: front HMUZ; sizing: vol-scaled;
  costs: $0.85+exch + 1–2 ticks + roll gaps per quarter.
- Invalidation: differential adds no explanatory power over US-only in
  OOS splits.
- Counter-hypothesis: global USD factor dominates (EA surprises redundant).
- Failure conditions: mixing 07:30 CT releases into same-bar event windows;
  consensus snooping; unadjusted roll boundaries.
- Data: BLOCKED — needs PIT consensus archive for both regions + multi-year
  front chain (14 months available). PARAM-GAP.

**H5 — FX-spot-corpus session behavior transferred to 6E (POSTULATED
transfer — explicitly NOT validated).**
- PIT condition (if data existed): London/NY-overlap breakout behavior
  observed on EUR/USD spot in the FX corpus (corpus-1200 ideas were NOT
  provided to this lane; any specific line/ID reuse must be re-registered
  before testing).
- Prediction as framed by owner framework §15: London/NY overlap breakouts
  have regime-dependent continuation.
- Mechanism: liquidity/information concentration in the overlap [POSTULATED].
- Status: **NOT_RUN and structurally blocked on this snapshot** — the London
  morning (02:00–08:00 CT) and the 8:30-ET block are OUTSIDE the RTH-only
  bars; only the 13:00–16:00 CT tail of the overlap exists in-file. Any test
  would measure a different object than the spot-corpus idea.
- Transfer caveats (basis/roll/cost): futures embed CIP carry (roll gap
  +0.35–0.46%/quarter measured vs spot's swap points), delivery/roll
  mechanics, exchange fees + $6.25 tick granularity vs spot pips.
- Failure conditions: claiming spot-corpus validity for futures without
  re-registration and re-measurement; testing with RTH-only data and calling
  it the overlap.
- Data requirements: M1 depth ≥2019 covering full 23h Globex (owner/vendor
  decision) + corpus idea re-registration. Floor: ≥2y. Budget: vendor.

## 6. Missing data table

| Need | Have | Source (primary first) | Period | Schema | PIT properties | License/cost | Blocker | Next action |
|---|---|---|---|---|---|---|---|---|
| Full-session (Globex 23h) M1/H1 per-contract depth (H3/H5; session behavior) | 30D hourly RTH-only + 2D M1 per contract (~10-month wall), no Asia/London | Databento / CME DataMine (CME-licensed) | 2019→now | ohlcv-1m + definitions per expiry, full session | Raw bars immutable; vendor timestamp policy to verify | Paid (owner decision) | Purchase decision + budget | Owner decision; spec by DATA lane |
| Multi-year true-volume quarterly front chain (daily) | 247 front-scale days (2025-09-09→2026-10-01); deeper = settlement marks | Vendor daily per-contract TRADES + OI | 2010→now | per-contract OHLCV+OI+settlement | As-published | Paid | Same purchase | Bundle with M1 |
| USD + EUR short-rate / OIS series (H2 CIP test) | NONE (roll gaps measured, rates absent) | FRED (SOFR/€STR, free, primary-adjacent) + ECB SDW (€STR) | 2019→now | daily rate series | Vintage-aware (ALFRED for revisions) | Free | Not sourced | Free pull in engine-prep; ≥8 quarters floor |
| PIT macro consensus/surprise archive (H3/H4) | Release schedules only (FACT §4) | BLS/Fed/ECB actuals free; consensus = vendor archive | 2015→now | event, ts_utc, survey_median, actual, vintage | Consensus as-known-before-release | Actuals free; consensus paid | No consensus in repo | Owner: vendor or date-based v1 design |
| Open interest per contract (volume/OI roll A/B, CoT cross) | NONE (raw files carry no OI) | CFTC CoT weekly (free); vendor daily OI | 2019→now | date, conId, OI | CoT Friday-release/Tuesday-positions | Free/paid | OI absent from IBKR bars | Free CoT pull now; vendor OI with bundle |
| Cross-asset series for confirmation variables (6B/6J raw exist; DXY, Bund/UST yields, EA equities) | 6B/6J/ES/CL/NG raw in snapshot (daily, same limits) | FRED/DXA vendors; CME complex via bundle | 2019→now | daily closes | Vendor revision policy | Mixed | Not sourced / lane scope | Cross-asset matrix deferred to post-dossier stage |

Priority for top-3 causal drivers (policy differential, macro surprises, CIP
carry): rows 3, 4, 1. This dossier does not condition on the full wishlist.

## 7. Framework coverage

**Master §1 (10 questions):**
1. Underlying exposure: EUR 125,000 vs USD, USD-per-EUR quote; Fed-ECB
   differential / growth / inflation / USD-cycle driven [FACT + framework
   POSTULATED].
2. Participants: banks, corporates, asset managers, macro funds, CTAs,
   CB-related hedgers, MMs [POSTULATED per framework; measurement NOT_RUN].
3. Exchange/sessions: CME Globex 17:00→16:00 CT (23h, break 16:00–17:00);
   IB RTH 08:30–16:00 CT; DST-correct [FACT/OBSERVED S1+S9]; **raw bars are
   RTH-only — prime FX sessions absent** [OBSERVED].
4. Size/tick/currency/margin/settlement: 125k ×, 0.00005 = $6.25, USD,
   physical delivery at IMM; margins $2.31–2.64k maintenance class
   [FACT/OBSERVED §1/§3].
5. Listed months / liquid expiries: monthly ~2y out + quarterly to 2031
   [OBSERVED S1]; **only front quarterly liquid** [OBSERVED].
6. Liquidity migration: quarterly→quarterly in IMM expiry week, 1–2 sessions
   before old last-trade (4/4 cycles); serials skipped (333:1 volume);
   exact crossover NOT_RUN [OBSERVED].
7. Behavior dominated by: macro/policy expectations + CIP carry (4/4 positive
   gaps) + microstructure roll effects; cash-arb channel = CIP anchoring
   [OBSERVED gaps; dominance attribution POSTULATED].
8. Which session matters: cannot rank Asia/London/US — Asia+London absent
   from data [NOT_RUN]; within captured RTH, 09:00–11:00 CT carry most volume
   (39% over 30 days) [OBSERVED]; hidden-session gap carries ~79% of measured
   RTH-day return std [OBSERVED].
9. Tradeable contract per timestamp (PIT): front HMUZ until expiry-week roll
   (H1 rule); nearest-expiry/serial is a trap (IB "front" = 214-lot book
   Sep-2026) [OBSERVED-informed design].
10. Vendor symbols ↔ expiries + reproducible continuous: localSymbol→conId in
    S1 (6EZ6=532281583 etc., 20 raw contracts); quarterly-only unadjusted
    chain built here; back-adjustment delegated to engine (4 gaps measured)
    [FACT/OBSERVED].

**6E framework checklist (§1–§17) — status:**
- §1 Foundation: answered (§1) [FACT/OBSERVED where stated].
- §2 Market structure: volume by hour/expiry OBSERVED (30d/panel); roll speed
  (IMM-week ramp) OBSERVED; spread widening near events/expiry NOT_RUN
  (non-synchronous BID/ASK; serial-vs-quarterly spread difference OBSERVED);
  opening/settlement effects NOT_RUN (RTH-only bars); contract-selection-rule
  stability: calendar vs volume vs OI — quarterly-calendar measured, volume/
  OI alternatives NOT_RUN.
- §3 Causal-driver table: §2 above [each row tagged].
- §4 Regime map: one regime in front-scale sample (EUR drift 1.20→1.13, 5.3%
  ann-vol descriptor); regime taxonomy NOT_RUN (needs multi-year + macro
  series).
- §5 Event-study framework: calendars FACT (§4); 1m/5m/… measurements NOT_RUN
  (intraday depth + pre-window timing collision).
- §6 Term-structure/roll: raw panel built; quarterly front chain built; 4
  roll gaps measured; calendar-vs-volume-vs-OI roll comparison NOT_RUN (no
  OI); back-adjusted vs unadjusted delegated to engine (gap sizes measured);
  no vendor stitching present (self-built chain — no vendor jump risk).
- §7 Cross-asset (6B/6J/ES/DXY/Bund/EA equities): 6B/6J/ES raw exist in
  snapshot — cross descriptives NOT_RUN this session (lane scope 6E); DXY/
  Bund/EA-equity data absent.
- §8/§15 Candidate signals: 5 hypotheses specified (§5) with mechanism +
  falsification; H1/H2 testable now/at low cost; no backtests run (PREP).
- §9 Backtest protocol: inputs prepared (panel, roll table, gaps, costs);
  execution NOT_RUN (task classification).
- §10 Data checklist (Databento phase-1 ohlcv-1m/definition/statistics;
  bbo-1m later): mapped in §6.
- §11 Failure modes: single-regime sample flagged; limit-move handling
  NOT_RUN (no price-limit source); same-bar execution risk flagged in H3;
  basis/roll-convention creation of signal flagged (H2/unadjusted chains).
- §12 Deliverables: items 1–8, 10 partially covered; 9 (backtest report) and
  rejection log NOT_RUN.
- §13 Contract-specific driver map: covered in §2 rows 1–7 (all seven
  framework primaries); confirmation variables NOT_RUN.
- §14 Foundation questions (level-vs-change of differential; energy-shock
  sensitivity; London-vs-NY persistence; surprise differentials): all
  POSTULATED/NOT_RUN — measurement blocked on data (§6 rows 1/3/4); session
  question additionally blocked by RTH-only window.
- §16 Contract-specific failure modes: cash-vs-futures orientation handled
  (USD-per-EUR verified); policy-priced-in risk flagged in H3; political-gap
  risk NOT_RUN; time-zone/release-timestamp errors quantified (§4 timing
  collision).
- §17 First sprint: items 1–3 done at legal depth (PIT panel from S1+
  definitions, roll/liquidity diagnostics, baseline daily stats); 4–6
  blocked on data (§6); 7 pending.

**Open questions (carried to handoff):** (1) exact quarterly volume crossover
per cycle (needs both-contract overlapping volume — vendor history or
prospective collection); (2) does the Jan/Feb IMM holiday shift alter roll-week
timing in Q1 cycles (only one Q1 boundary in sample, none in front-scale era
beyond Mar-2026)? (3) CIP gap vs actual USD−EUR rates once FRED/€STR pulled;
(4) consensus archive choice for H3/H4; (5) whether 6B/6A/6J show the same
serial-skip structure (shared FX-family hypothesis, sibling lanes to confirm).
