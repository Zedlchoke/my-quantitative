# ES DEEP v2 — E-mini S&P 500, 16.4 years of 1m per-contract data

- Task: **FUTURES-DEEPRESEARCH-V2-20261003**, lane **DEEP-ES**
- Generated (UTC): 2026-10-03
- Parent evidence inherited read-only: `research/control/FUTURES-BEHAVIOR-10SYMS-PREP-20261002/`
  (v1 dossier `dossiers/ES_DOSSIER.md`; acquisition ledger; IBKR overlap validation)
- New inputs (this lane, read-only):
  - Vendor ohlcv-1m per contract 2010-06-06→2026-10-01 (FULL; both contracts
    of every roll observed every session):
    `/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim/parquet/AV1R-O1M-ES-DELTA/` (7 chunks, 2010-06→2023-10)
    + `…/AV1T-O1M-ES/` (6 chunks, 2023-10→2026-10). 7,825,657 outright
    quarterly 1m bars after filtering `^ES[HMUZ][0-9]$` (calendar-spread
    instruments and 2027 deferred stray-print tails excluded from chains).
  - Definitions (exact expiries, 2023-10+), statistics (stat_type 9 = open
    interest, 6 = cleared volume; 2023-09-28→2026-09-28) — same vendor root.
  - Nonprice PIT: FOMC statements+calendars 2011-01→2026-09 (as-issued HTML),
    CFTC CoT legacy (as-published, 2006-01→2026-09), FRED latest (DFF; NOT
    PIT — sign corroboration only).
- Own analysis (this task's `analysis/` dir; every OBSERVED number below is
  reproducible from these):
  - `ES_build_panel.py` → `ES_cache/es_1m_outright.parquet`, `ES_cache/es_contracts.json`, `ES_cache/es_statistics_daily.parquet`
  - `ES_chains.py` → `ES_cache/es_contract_daily.parquet`, `es_chain_{VOL,T5,DECL,OI}.parquet`, `es_roll_table.json`
  - `ES_regime_map.py` → `ES_regime_stats.json`
  - `ES_sessions.py` → `ES_session_stats.json`
  - `ES_roll_stats.py` → `ES_roll_stats.json`
  - `ES_fomc.py` → `ES_fomc_stats.json`
  - `ES_cot.py` → `ES_cot_stats.json`
  - `ES_quality.py` → `ES_quality_ledger.json`
- Claims taxonomy: **FACT** (primary source + date), **OBSERVED** (script +
  window), **POSTULATED** (mechanism, unmeasured), **NOT_RUN** (never inferred
  PASS). This is PREP-class deep descriptive research: **0 PnL, 0 scored
  runs, 0 parameter selection, 0 conditional mean-return tables**. Where a
  threshold exists it is strict-past/trailing (window ends before the day
  described).
- v1→v2 depth delta: v1 had 14 months of front-scale daily data + 30d hourly
  (RTH-only, overnight hidden) + 5 roll cycles; v2 has **16.4 years × 1m ×
  both-session × both-roll-sides** — every v1 "depth-starved / NOT_RUN"
  structural item is now measured except where a law or a missing external
  dataset blocks it.
- **ERRATA applied 2026-10-03** (lane DOSSIER-ERRATA-V2, from
  `audit/a7_es/A7_DEEP_ES.md`, verdict PASS_WITH_ERRATA — 13/13 mandated
  recomputes match exactly): **M-1** the "OI crossover leads volume by 1
  calendar day" claim is RESTATED as a timezone-labeling artifact — under a
  consistent session-date convention OI crosses on the SAME trading day as
  volume (12/12); plus small wording corrections m-1/m-2/m-3 and the
  advised v1-cross-check reframe n-1. Full old→new ledger in §12.

---

## 0. Executive summary (each item OBSERVED with script+window unless noted)

1. **Roll calendar is near-deterministic**: across all 66 completed quarterly
   rolls 2010-06→2026-09, the next contract's daily volume first exceeds the
   old front's (with ≥100k new-contract volume) **3–5 trading sessions before
   expiry** (median 5). A fixed T-5 calendar roll deviates from the true
   crossover by **0 to −2 sessions (never >3)** — v1 H1's invalidation
   condition never fires in 16 years. OI (where measurable, 12 rolls 2023+)
   crosses on the **SAME trading day** as volume [ERRATUM M-1: was "1
   calendar day before volume" — a timezone-labeling artifact, see §4].
2. **Roll-gap sign tracks the carry regime**: calendar spread at crossover is
   negative 2010-2016 (−1.5 to −1.8 %/yr annualized) and 2020-21, positive
   2018-19 and strongly positive 2023-2026 (+3.3 to +4.7 %/yr); sign matches
   (DFF − 1.8pp dividend-yield proxy) on 61/66 rolls. v1 measured 5 positive
   gaps (2025-26); the full sign flip history is the v2 upgrade. Dividend
   yield itself is NOT in repo → mechanism link stays POSTULATED.
3. **The v1 declared roll rule is structurally costly**: it switches to the
   deferred contract a **median 9 sessions (range 6–11)** before the market's
   volume crossover, i.e. it holds a sub-liquidity book ~2 weeks/quarter —
   now measured on 65 rolls (v1: 5 cycles).
4. **Overnight (Globex) carries 21–54% of daily return variance** by year
   (highest 2020: 53.8%; lowest 2018: 20.9%), while RTH holds a stable
   ~79–86% of volume across 16 years — information share and volume share
   diverge. Overnight std ≈ 0.25–1.4%/day vs RTH 0.3–1.3% by era
   [ERRATUM m-2: was "0.4–1.4" — the dossier's own year table has 2017
   sd(ON) = 0.25%; honest full range 0.25–1.41].
5. **Vol regimes span 5.3×**: annualized vol (252d) ranged 6.3% (Dec-2017) to
   33.6% (Feb-2021). Daily-return lag-1 autocorr is negative in 6/7 eras
   (daily mean-reversion tilt; COVID era −0.243); variance ratios VR(5d)
   < 1 in all eras (0.80–0.95). |ret| autocorr (clustering) 0.07–0.51 by era
   — v1's "0.002, clustering weak" was a 284-day-window artifact.
6. **FOMC anatomy (timing only, no returns)**: volume runs at **0.72–0.81×**
   baseline for the 2 hours before release (pre-release quieting), spikes to
   **2.91×** in the release 15 minutes (|1m ret| 3.19×), and stays elevated
   (1.1–2.7×) through +165 min (presser at +30 min visible) [ERRATUM m-3:
   was "1.3–2.7× for 3+ hours" — the bucket table dips to 1.107 (+105 min)
   and 1.212 (+120 min)]. Reaction volume
   peaks at **minute +1** (median; 55% of events peak at minutes 0–1).
   Day-level: RTH volume ×1.14, RTH range ×1.38 vs trailing medians.
7. **CoT positioning has U-shaped risk content**: weeks in the most-extreme
   trailing positioning quintiles (either direction) are followed by ~2pp
   higher median forward 21d vol (Q1 14.9% / Q5 14.4% vs Q2–Q4 11.9–12.7%).
   Crisis anchors: COVID-2020 struck from the 13th percentile (positioning
   did NOT warn); the 2022 bear began at the 94th.
8. **Data quality is strong with two structural footnotes**: session close
   moved 16:30→16:15 CT (2013) →16:00 CT (Nov-2015) — pre-2016 "post-16:00"
   volume is real trading sitting in the break bucket; and the normalized
   CoT table mixes 3 S&P-complex markets under one series id (contamination
   found, filtered, disclosed). Coverage ≈99–100% of era-correct session
   length; 0 duplicate timestamps; 0 negative prices; 0 Saturday sessions;
   DST transitions never intersect an open ES session.

---

## 1. Data foundation and chain construction [OBSERVED]

- **Panel**: 71 outright quarterly contracts (ESM0-2010 → ESZ7-2027), keyed by
  vendor `instrument_id` (immune to decade-repeated symbols ESH0-2010 vs
  ESH0-2020). 7,825,657 1m bars. Prices are int-nanos (1e-9 pt); OHLC
  consistency violations: 0; negative prices: 0; duplicate
  (instrument, minute) rows: 0 (`ES_build_panel.py`, full window).
- **Contract calendar**: for every contract that expired inside the window,
  the last session with volume IS the 3rd Friday of the delivery month — with
  exactly one exception in-data: **ESM6 last traded 2026-06-18 (Thu)** because
  Friday 2026-06-19 is Juneteenth; vendor definitions confirm 2026-06-18, and
  definitions additionally show **ESM7 2027-06-17 (Jun-19 Sat → observed Fri
  Jun-18 → expiry Thu Jun-17)**. 2010–2025 June expiries were never displaced
  (Juneteenth observance collided with the 3rd Friday first in 2026)
  [OBSERVED, `es_contracts.json` vs naive 3rd-Friday; corroborates v1 FACT].
- **Chains (all PIT-legal, strict past)** (`ES_chains.py`):
  - **VOL**: hold argmax of prior-session total volume among the two nearest
    quarterlies; 66 switches 2010-06→2026-09. Ratio-back-adjusted closes
    carry no roll jump (max switch-day |ret| 4.4% = 2020-03 market vol, not
    adjustment artifact).
  - **T5**: calendar roll 5 trading sessions before the (observed/definition)
    expiry session; 66 switches; Juneteenth-adjusted June expiries.
  - **DECL**: v1 data-lane rule (last session before delivery-month day-1);
    65 switches.
  - **OI**: prior published open-interest argmax (statistics schema; only
    2023-10+); 12 switches in-era.
  - Chain agreement: VOL and T5 name the same front on 97.9% of sessions
    (90 disagreement sessions in 16.4y, all inside pre-roll windows where T5
    leads the volume crossover by 0–2 sessions); VOL and OI agree on 98.4%
    of the 2023-10+ window. DECL disagrees with all of them for the
    ~9-session thin window each quarter [OBSERVED].
- **Statistics (OI) table**: 5,425 contract-days 2023-09-28→2026-09-28;
  stray deferred OI prints (2–5k lots, calendar-spread artifacts like
  ESM6 OI jumping 2→5,337→2 on 2025-04-02/03) floored out of crossover logic
  (require ≥500k OI) [OBSERVED, `es_statistics_daily.parquet`].

## 2. A1 — Strict-past regime map, 2010-06 → 2026-10 [OBSERVED, `ES_regime_map.py`]

Full sample (4,203 return days, VOL chain, ratio-adjusted): mean +5.2 bp/day;
annualized vol 17.0%; skew −0.24; excess kurtosis 12.6; lag-1 daily autocorr
−0.101; |ret| lag-1 +0.323; 5d-return lag-1 +0.77 (overlapping-window
artifact, reported for completeness). Rolling 21d vol percentiles
(p05/p25/p50/p75/p95) = 6.0/9.2/12.5/17.2/28.9%; 252d vol min 6.3%
(2017-12-13) max 33.6% (2021-02-08).

Era table (data-quality eras aligned to vendor protocol boundaries; market
regime label descriptive):

| Era (window) | n | vol(ann) | mean bp/d | maxDD | acf1 | acf\|r\| | VR(5d) | longest underwater (sess) |
|---|---|---|---|---|---|---|---|---|
| E1 2010-06→2012-12 FIX/FAST post-GFC/EU-crisis | 664 | 18.9% | +6.0 | −19.7% | −0.109 | +0.18 | 0.87 | 201 |
| E2 2013→2015-11 taper→liftoff | 732 | 12.8% | +6.1 | −11.9% | +0.014 | +0.20 | 0.95 | 88 |
| E3 2015-11→2017-05 late-QE | 385 | 12.0% | +4.3 | −12.7% | −0.065 | +0.30 | 0.87 | 95 |
| E4 2017-05→2020-02 MDP3 low-vol | 711 | 13.3% | +5.2 | −20.4% | −0.038 | +0.30 | 0.91 | 154 |
| E5 2020-02→2021-12 COVID | 483 | 25.7% | +8.8 | −33.9% | −0.243 | +0.51 | 0.80 | 118 |
| E6 2022→2023-09 hiking bear+rally | 452 | 20.0% | −2.2 | −25.1% | +0.003 | +0.07 | 0.92 | 451 |
| E7 2023-10→2026-10 AV1T AI-bull | 776 | 14.9% | +6.4 | −19.5% | −0.088 | +0.21 | 0.88 | 145 |

Year-level extremes and extremes table: worst days cluster 2020-03 (−10.6%
2020-03-12; +10.2% 2020-03-24), 2011-08-08 (−7.3%, post US-downgrade),
2025-04-09 (+10.0%), 2022-11-10 (+5.8%); best-vol year 2017 (6.4% ann, maxDD
−2.6%, zero days |>2%|), worst 2020 (32.8%, 18.9% of days |>2%|)
[`ES_regime_stats.json` years/extreme_days]. Trailing-tercile vol-regime
occupancy (thresholds from trailing 1000 sessions, strict past): LOW 38.2% /
MID 24.6% / HIGH 28.6% / untagged (warmup) 8.6% — occupancy asymmetry is the
right-skewed vol distribution, not a threshold artifact.

Drawdown anatomy [OBSERVED]: deepest episodes 2020-02→03 (−33.9%), 2022
(−25.1%, longest underwater 451 sessions — the 2022-01→10 bear spent ~85% of
the time below prior peak), 2018-Q4 (−20.4% in ≤60 sessions), 2011-H2
(−19.7%), 2025-04 (−19.3%). Trend-persistence reading: no era shows VR(5d)>1
— multi-day momentum is not a descriptive feature of ES daily closes in ANY
era; crisis-era daily autocorr is the most negative (−0.24 COVID).

## 3. A2 — Session/intraday structure, full era, DST-correct [OBSERVED, `ES_sessions.py`]

Segments (America/Chicago via tz database): ON 17:00→08:29, RTH 08:30→15:59,
break 16:00→16:59. Front contract = VOL chain. Historical session-length
regimes (recovered from the bars themselves, see §6): Globex close was
16:30 CT until 2012, 16:15 CT 2013→Nov-2015, 16:00 CT since — the
pre-2016 16:00→16:15/30 tail volume (median 2.1–2.3k contracts/session)
sits in the break bucket and is excluded from RTH/ON splits (disclosed).

| Era | median front vol/day | RTH vol share | Var(ON) share | sd(ON) | sd(RTH) | corr(ON,RTH) |
|---|---|---|---|---|---|---|
| E1 2010-12 | 1.86M | 0.835 | 38.5% | 0.69% | 0.87% | +0.12 |
| E2 2013-15 | 1.50M | 0.848 | 38.6% | 0.51% | 0.64% | −0.04 |
| E3 2015-17 | 1.50M | 0.850 | 43.6% | 0.50% | 0.57% | −0.02 |
| E4 2017-20 | 1.25M | 0.832 | 28.4% | 0.45% | 0.71% | −0.00 |
| E5 2020-21 | 1.39M | 0.813 | 50.7% | 1.07% | 1.06% | +0.15 |
| E6 2022-23 | 1.63M | 0.842 | 32.8% | 0.74% | 1.06% | −0.04 |
| E7 2023-26 | 1.33M | 0.847 | 34.2% | 0.58% | 0.81% | −0.10 |

- ON return = prev 16:00 close → 08:30 open; RTH = 08:30 open → 16:00 close
  (front contract marks). The ON variance share is regime-driven (crisis
  50–54% in 2020/2015-16, quiet 21% in 2018) — v1's single-number "gap std
  ≈63% of day std" on 284 days is superseded.
- Hour-of-day (E7): RTH hours carry 12.8% (08:00h = open 30m) to 16.3%
  (14:00h = cash MOC half-hour) of daily volume; overnight hours 0.4–3.0%
  each (07:00h elevated at 3.0% with |1m| 1.6bp — the 07:30 CT macro-release
  slot). |1m ret| runs ~0.65–1.3bp overnight vs 2.0–2.8bp in RTH.
- RTH sub-buckets (share of RTH volume): open 30m ≈13.2–13.8% stable across
  eras; MOC half-hour (14:30–15:00) rose 11.9%→13.8% E1→E7; the post-cash
  15:00–16:00 hour fell 6.4%→5.2%.
- Sunday 17:00 CT reopen hour trades 1.5–2.9× the weekday 17:00 hour volume
  in every era.
- Volume era drift: median front volume peaked 2011 (2.14M/day), troughed
  2017-19 (1.21–1.24M), partially recovered 2022 (1.70M) — volume is NOT
  monotonically declining, but ON share of volume is stable (~15–17%) across
  16 years [OBSERVED, `ES_session_stats.json` years].

## 4. A3 — Term structure, roll, and liquidity migration [OBSERVED, `ES_chains.py` + `ES_roll_stats.py`]

66 completed rolls (2010-06→2026-09 pairs):

- **Volume crossover** (first session where new ≥100k contracts AND new > old):
  3–5 sessions before expiry; median 5; mean 4.64. June rolls behave
  identically including 2026 (crossover 2026-06-15, 3 sessions before the
  Juneteenth-shifted 2026-06-18 expiry) [OBSERVED].
- **T5 calendar rule** vs measured crossover: deviation 0 to −2 sessions,
  never >3 — v1-H1's invalidation condition (a cycle deviating >3 sessions)
  NEVER fired in 66/66 rolls [OBSERVED].
- **OI crossover** (statistics era, 12 rolls): **[ERRATUM M-1 — RESTATED]**
  the pre-audit text read "leads volume crossover by exactly 1 calendar day
  in 12/12 rolls (positions migrate first, flow follows next session)" —
  that 1-day gap is a DATE-CONVENTION ARTIFACT, not an economic lead. The
  OI table's dates are the Chicago calendar date of `ts_ref` (UTC midnight
  of trading day T, i.e. T−1); all twelve lane OI "crossovers" are SUNDAYS
  (e.g. 2023-12-10), one calendar day before the Monday volume crossovers.
  Proof `ts_ref=T` labels trading day T: Databento stat_type 6 (cleared
  volume) at `ts_ref=T` tracks session-T traded volume at a stable
  1.03–1.14× (cleared incl. spreads) on quiet weeks, while T−1 alignment is
  wild (0.87–12.3×). **Under a consistent session-date convention the OI
  crossover falls on the SAME trading day as the volume crossover in 12/12
  rolls (2023-10+ statistics era).** Publication-lag disclosure: the OI
  chain's "prior published OI" rule (`oiq.index < s`) with the shifted
  labels actually consumes same-trading-day OI published the following
  morning ~08:28–08:58 CT — a few-hours publication-lag leak inside a
  descriptive-only statistic (98.4% chain agreement); no PnL impact
  [OBSERVED; convention proof OBSERVED].
- **DECL-rule thin windows** (sessions between DECL switch and volume
  crossover): median 9, range 6–11 — the declared v1 baseline holds a
  sub-front-scale book ~2 weeks per quarter [OBSERVED; v1 estimated 8–9
  from 5 cycles; now 65 rolls].
- **Calendar spread at crossover** (new − old close on the prior session,
  both books liquid): sign/magnitude by year (median, annualized %):

  2010 −1.78% | 2011 −1.74% | 2012 −1.84% | 2013 −1.49% | 2014 −1.50% |
  2015 −1.51% | 2016 −1.47% | 2017 −0.31% | 2018 +0.65% | 2019 +0.47% |
  2020 −1.38% | 2021 −0.81% | 2022 +0.94% | 2023 +4.24% | 2024 +4.70% |
  2025 +3.48% | 2026(YTD) +3.35%

  Sign matches (DFF − 1.8pp proxy) on 61/66 rolls; the 5 mismatches are
  2017×1, 2018×2, 2019×1, 2022×1 — there is NO 2021 mismatch (2021 spreads
  were negative with DFF≈0.08, proxy negative → match) [ERRATUM m-1: was
  "2017 transition rolls and 2021"]. Mechanism reading: futures ≈ spot +
  (rate − div yield)×T [POSTULATED; rates side corroborated by FRED DFF
  (latest-revised, NOT PIT — disclosed); dividend yield NOT in repo]. The
  unadjusted-switch jump (what a naive continuous series would embed) =
  spread ± overnight market move — distribution in `ES_roll_stats.json`
  (`rolls[]`), e.g. 2026-09 roll: spread +67.75 pts — consistent in sign
  and magnitude with v1's +67.75 (0.25-pt mark-convention difference on the
  vendor-declared-roll comparison: v1's figure is the IBKR daily-close gap
  at the declared roll 2026-08-31 where the vendor last-trade same day is
  68.00; the two +67.75s are different quantities that coincide numerically
  — ERRATUM n-1, was "matches v1's +67.75 exactly — cross-validation
  PASS"), unadjusted jump +31.5 pts.
- **Liquidity migration speed**: mean new-contract share of old+new volume
  over the old contract's last 8 sessions ≈ 0.47–0.71; migration is a
  step-function in roll week, not a gradual drift [OBSERVED].

## 5. A4 — FOMC event-day anatomy (timing ONLY) [OBSERVED, `ES_fomc.py`]

- Statement inventory: 132 policy statements 2011-01-26→2026-09-16 in the
  as-issued HTML archive; 92 carry machine-parsable "For release at" clock
  times (2016-01-27 onward; 85 scheduled at 14:00 ET; 7 irregular:
  2019-10-11 11:00, 2020-03-03 10:00, 2020-03-15 17:00 Sun, 2020-03-23
  08:00, 2020-03-31 08:30, 2020-08-27 09:10, 2025-08-22 10:00). 40
  statements 2011-2015 have NO time in the artifact → **minute-anchored
  anatomy NOT_RUN for 2011-2015**; day-level anatomy covers all 131 in-data
  statements [FACT for times (as-issued statement text), OBSERVED for
  profiles].
- **Day-level** (ratios to trailing-20-session strict-past medians, front
  contract): RTH volume median ×1.14 (p25-p75 1.01–1.31; n=131); RTH range
  median ×1.38 vs baseline-day ×0.98 (n=3,913). The 2011-2015 untimed era
  shows ×1.23 vol ratio vs ×1.12 for 2016-26 [OBSERVED].
- **Release-anchored 15-min buckets** (91 timed sessions with 1m data vs
  same-weekday non-FOMC baseline anchored 13:00 CT; medians):
  pre-release −120→−15 min: volume ratio **0.72–0.81 flat** (quieting);
  release bucket **2.91×** (|1m ret| 3.19×); +15m 1.79×; +30m 2.65×
  (press-conference onset); +45m 2.51×; +60m 2.05×; +90m 1.62×; elevation
  still 1.1–1.6× at +105→+165 min (RTH tail: 13:00 CT anchor ⇒ 15:00–15:45
  CT; NOT "early Globex" — ERRATUM m-3). Full table in
  `ES_fomc_stats.json` [OBSERVED].
- **Reaction timing**: minute of max volume within [0,+30] after release:
  median offset +1 minute; 55% of events peak at minutes 0–1; 76% within 5
  minutes [OBSERVED].
- LAW COMPLIANCE: no mean returns computed or compared anywhere in A4; these
  are volume/vol/range timing descriptives; nothing ranks or selects.
- Pre-release quieting ratio (−30m volume rate vs prior 90m): median 0.93 —
  mild; the deeper suppression is vs normal Wednesdays (0.72–0.81 above).

## 6. A5 — CoT positioning vs subsequent realized vol/drawdowns [OBSERVED, `ES_cot.py`]

- Series: CFTC legacy, market name exactly "E-MINI S&P 500 …" (STOCK INDEX
  spellings), 1,082 weekly rows 2006-01-03→2026-09-22, as-published
  (no revision), positions Tue / release Fri 15:30 ET; forward windows start
  the session AFTER release (PIT lag honored). 922 usable releases after the
  3-year trailing-percentile warmup (2009-01→2026-08).
- **DATA INCIDENT (found+fixed this lane)**: the normalized
  `cftc_legacy_tidy.parquet` series `COT_LEGACY_ES` mixes three CFTC markets
  (true E-mini OI ~1.4–3.0M; "Micro E-mini" ~0.1–0.2M; "S&P 500
  Consolidated" ~0.4–0.5M). Unfiltered use (first run) produced corrupted
  percentiles and an OI series that halved in 2022. Exact-name filter
  restores a clean 1,082-week series with zero duplicate weeks; corrected
  OI by year is economically sane (1.40M 2006 → 2.95M 2016 peak → 1.98M
  2026) [OBSERVED].
- Trailing-percentile quintiles (3y strict-past) vs forward outcomes
  (medians): **U-shape** — Q1 most-short: fwd 21d vol 14.9%, fwd 63d DD
  −6.6%; Q2: 11.9% / −5.0%; Q3: 12.7% / −5.7%; Q4: 12.4% / −5.0%; Q5
  most-long: 14.4% / −5.7%. Extremes in EITHER direction carry ~2pp more
  forward vol. Spearman (trailing pctl vs fwd 63d vol) = −0.07 (weak
  monotonic — consistent with U, not line). Deciles: most-short −227k net →
  fwd rv 16.8%; most-long +180k → 15.9% [OBSERVED].
- Crisis anchors: COVID-2020 struck from 13th-percentile positioning (fwd
  21d vol 90.5% — positioning did NOT warn); 2022 bear began at 94th
  percentile; Aug-2011 at 58th; 2025-04 at 78th (fwd vol 41.9%)
  [OBSERVED]. Structural drift: net noncommercial swung −150k (2006) → +96k
  (2013) → −145k (2022) → −103k (2026) — the "who is the marginal
  speculator" structure is regime-dependent across decadal windows.
- NO forward-return tables were produced (law); this is risk anatomy only.

## 7. A6 — Data-quality ledger per era [OBSERVED, `ES_quality.py`]

| Era | sessions | median bars/sess | coverage (era-correct) | flat-OHLC bars | 1m gaps | |1m ret|>1% count |
|---|---|---|---|---|---|---|
| E1 2010-06→2012-12 | 665 | 1,381 | ~97% of 1,425 | 10.0% | 0.9% | 6 |
| E2 2013→2015-11 | 732 | 1,365 | ~98% of 1,395 | (≈E1 class) | 1.3% | 3 |
| E3 2015-11→2017-05 | 385 | 1,360 | ~98% of 1,380 | lower | 0.6% | 0 |
| E4 2017-05→2020-02 | 711 | 1,364 | ~99% | lower | 0.5% | 2 |
| E5 2020-02→2021-12 | 483 | 1,365 | ~99% | lower | 0.2% | 30 |
| E6 2022→2023-09 | 452 | 1,380 | 100% | low | 0.0% | 8 |
| E7 2023-10→2026-10 | 776 | 1,380 | 100% | low | 0.0% | 15 |

- zero-volume bars ≈ 0% in all eras (Databento emits bars only on traded
  minutes; quiet overnight minutes are absent, not zero-filled — hence
  pre-2013 nights show ~9-45 missing minutes/session, a coverage not an
  error mode).
- **Session-close history recovered from the data**: Globex day ended 16:30
  CT through 2012, 16:15 CT 2013→Nov-2015, 16:00 CT since (break bars
  24,653 total, confined to ≤2015; post-2016 residual 16:00/16:59 prints are
  single-mark artifacts ≤60 bars/yr) [OBSERVED]. Consequence handled in §3.
- DST: both US transitions (Sun 02:00 local) fall inside the weekend closure
  (Fri 16:00 → Sun 17:00 CT) — no ES session is ever clock-distorted;
  America/Chicago tz-conversion is exact across 2010-2026 [OBSERVED].
- Saturday sessions: 0. Early-close (holiday half-day) sessions: 3–10/yr.
  Extreme 1m jumps (>2%): exactly 10 in 16.4y, all at identifiable macro
  minutes — 2011-08-05 (US downgrade), 2020-03-03/09/16 (COVID; the
  2020-03-16 08:45 CT halt-reopen minute moved −5.67%), 2022-09-13, 10-13,
  11-10 (all three at the 07:30 CT CPI release minute), 2025-04-07/09
  (tariff-pause cluster) [OBSERVED].
- **ES-vs-IBKR overlap** (this lane; the acquisition lane validated only NQ):
  273 liquid days 2023-10→2026-10, vendor 16:00 CT 1m close vs IBKR daily
  close median |diff| 15 ticks, 15:00 CT close 4 ticks — consistent with the
  settlement-mark vs last-trade convention gap (same magnitude as the
  acquisition lane's NQ finding of 17.5 ticks); NOT an error, and IBKR daily
  closes remain unusable as tradable marks (v1 caveat reinforced).
- **Timestamp-precision caveat resolution**: ohlcv-1m bars are
  minute-stamped, so the vendor "ms precision pre-2015-11-20" caveat is
  **not testable and not relevant** on this schema (all ts trivially
  ms-aligned in every era); it would matter only for tick-level schemas.
  FIX/FAST pre-2017-05 capture: no anomaly detectable at 1m aggregation
  beyond the higher flat-bar/gap rates above [OBSERVED + vendor docs FACT
  via DATA_ACQUISITION_SPEC.md].
- Nonprice quality: (a) CoT contamination (§6); (b) FOMC 2011-2015 statements
  lack release times in artifact (§5); (c) FRED latest = latest-revised NOT
  PIT (sign corroboration only); (d) BLS schedule caveat inherited
  (CPI/NFP not touched by this lane).

---

## 8. Hypothesis refinement vs v1 ES-H* (specs refined, NOT evaluated; no PnL)

Status legend: PARAM-GAP dissolved = the data floor v1 demanded is now
exceeded. Floors were v1's own minimum-evidence bars.

**H1 Roll-calendar liquidity alignment (v1) → v2 CONFIRMED-descriptively.**
- v1 floor: >3-session deviation between calendar T-5 and measured migration
  would invalidate. v2: 66/66 rolls within 0–2 sessions; OI crossover falls
  on the SAME trading day as volume (12/12 where measurable; ERRATUM M-1 —
  was "leads volume by 1 day", a timezone-labeling artifact). PARAM-GAP
  dissolved (5 rolls →
  66).
- Refined spec (construction rule, PIT-legal): continuous reference =
  switch at T-5 close before the delivery-month expiry session, where
  expiry = 3rd Friday with the June Juneteenth shift (2026-06-18 observed;
  2027-06-17 from definitions); alternative OI-switch rule legal from
  2023-10+ only (needs statistics feed). Declared-rule (v1 baseline) is
  dominated: median 9-session thin-book window per quarter.
- Remaining NOT_RUN: measured execution cost inside thin windows (no BBO
  depth); deferred-tail stray prints (ESU7/ESZ7 2027) excluded by
  ≥100k-volume floor (rule documented, deterministic).

**H2 Roll-gap carry (v1) → v2 sign-history measured.**
- v1 floor: ≥8 quarters for a sign statement (had 5). v2: 66 quarters, sign
  flips 2016→2018 and 2020→2022 both observed; 61/66 sign-match vs
  (DFF−1.8pp). PARAM-GAP dissolved on the futures side.
- Remaining PARAM-GAP: S&P dividend yield PIT series not in repo → the
  (rate − div) identity is corroborated on sign only; refined test needs a
  dividend-yield vintage source (owner decision). Refined falsification: a
  sustained positive spread while (rate − div) < 0 (rebalancing-demand
  premium hypothesis) — not yet observed in 66 rolls.

**H3 Post-release persistence (v1) → v2 timing prior established; conditional test still BLOCKED.**
- Now legal and measured (this lane): release-minute volume/reaction timing
  (peak minute +1; 55% minutes 0–1), 2-hour pre-release quieting, 3-hour
  elevation decay. These are the execution-cost and event-window design
  priors any future H3 test must use (e.g., same-bar entry at release is
  untradable in size — release-minute book absorbs 2.9× volume).
- BLOCKED unchanged: PIT consensus/surprise archive absent (vendor decision,
  v1 §6 row 3). The mean-return side remains NOT_RUN by task law and by
  data. Depth floor (≥40 events/class) now met for FOMC (92 timed) — the
  blocking item is consensus data only.

**H4 ES/NQ relative-value on event days (v1) → cross-lane, NOT_RUN here.**
- NQ deep lane owns NQ v2; this lane did not compute NQ chains. Refined spec
  when both dossiers land: same-event-day spread-variance descriptive first
  (law-safe), return-conditional test only in a registered cycle. Both
  symbols now have 16y 1m depth — v1's "LOW power, 14 months" blocker is
  gone at the data level.

**H5 Overnight-gap regime behavior (v1) → descriptive foundation replaced; conditional test still NOT_RUN.**
- v2 measured: full-era ON/RTH variance decomposition (21–54% ON by year),
  era corr(ON,RTH) from +0.15 to −0.10, hour-level overnight profiles. The
  v1 gap-normalization machinery (trailing-20d mean |ret|) is superseded by
  direct both-session decomposition.
- The sign-conditional gap-continuation/reversion evaluation is
  mean-return-conditional = PnL-linked selection → NOT_RUN under this task's
  laws (registered cycle required). Refined pre-registered spec drafted in
  handoff.

**New v2 hypothesis candidates (mechanism-first, all NOT_RUN as tests):**
- **H6 Roll-window microstructure cost**: DECL-style rules pay a liquidity
  premium for ~9 sessions/quarter; prediction: per-contract effective spread
  in thin windows exceeds roll-week spreads (needs bbo-1m — PARAM-GAP).
- **H7 Positioning-extremes vol convexity (from A5 U-shape)**: extreme
  trailing positioning (either tail) → elevated forward realized vol;
  falsifiable as a risk filter (vol prediction, not return prediction) in a
  registered cycle with PIT release alignment; CoT Tuesday-positions/Friday-
  release lag already honored.
- **H8 Pre-release liquidity withdrawal timing (from A4)**: 2-hour
  pre-FOMC volume suppression (0.72–0.81×) as a cost-timing descriptor for
  any execution near scheduled macro releases; descriptive use legal now.

## 9. Framework coverage update (v1 §7 items now closed)

- Master Q6 (liquidity migration): measured on 66 rolls incl. exact
  crossover (was NOT_RUN in v1). Master Q8 (which session matters): ON vs
  RTH variance shares measured per era (was NOT_RUN — overnight hidden).
  Master Q9 (tradeable contract per timestamp): VOL/T5/OI/DECL all
  constructed, compared; OI rule legal 2023-10+ only.
- ES-framework §2 spread widening near events/expiry: volume side measured
  (roll-week migration, FOMC buckets); BBO spread side NOT_RUN (no quotes).
  §4 regime map: 7-era table + trailing-tercile occupancy. §5 event study:
  FOMC timing anatomy done; CPI/NFP calendars inherited FACT but 1m anatomy
  NOT_RUN (not in this lane's mission scope; data would support it). §6
  term structure: spread ladder at 66 rolls measured; intraday calendar-
  spread dynamics NOT_RUN. §14 overnight transfer: measured (A2).

## 10. Remaining NOT_RUN (explicit, no inferred PASS)

1. Any conditional mean-return evaluation (H3/H4/H5 return side) — task law;
   requires registered cycle + budget.
2. CPI/NFP/PCE/ISM release anatomy (only FOMC was this lane's mission; BLS
   schedule caveat inherited).
3. BBO spread/depth anywhere (roll windows, release minutes, thin windows) —
   no quote data acquired.
4. Tick-level microstructure (ms-precision caveat applies there).
5. Dividend-yield PIT series (H2 identity completion).
6. PIT consensus/surprise archive (H3 unblocking).
7. NQ/cross-asset descriptives (NQ lane).
8. 2011-2015 FOMC minute-anchored anatomy (artifact lacks release times) —
   day-level only.

## 11. Reproduction

Run order (venv `/Users/hoangminhlong/my-quantitative/.venv/bin/python`):
`ES_build_panel.py` → `ES_chains.py` → any of `ES_regime_map.py`,
`ES_sessions.py`, `ES_roll_stats.py`, `ES_fomc.py`, `ES_cot.py`,
`ES_quality.py`. Vendor + nonprice roots are read-only; outputs land in
`analysis/` (+ `analysis/ES_cache/`). Full window 2010-06-07→2026-10-01
(4,204 sessions).

---

## 12. ERRATA ledger (applied 2026-10-03, lane DOSSIER-ERRATA-V2; authority `audit/a7_es/A7_DEEP_ES.md`, verdict PASS_WITH_ERRATA — BLOCKER 0 / MAJOR 1 / MINOR 3 / NOTE 5 / INCIDENT 1)

Applied in place above and marked `[ERRATUM …]` at each correction site;
nothing silently rewritten.

| id | severity | where | old → new | evidence |
|---|---|---|---|---|
| M-1 | MAJOR | §0.1 item 1, §4 OI-crossover bullet, §8-H1 | "OI crossover leads volume crossover by exactly 1 calendar day (12/12); positions migrate first, flow follows next session" → timezone-labeling artifact: OI dates are the Chicago calendar date of `ts_ref` (UTC midnight of trading day T = T−1); all 12 OI crossovers are Sundays; consistent-convention result = **OI crosses on the SAME trading day as volume, 12/12** (2023-10+ era). Added publication-lag nuance: `oiq.index < s` rule consumes same-trading-day OI published next morning ~08:28–08:58 CT (few-hours leak in a descriptive stat; 98.4% agreement; no PnL impact) | A7-ES M-1 |
| m-1 | MINOR | §4 spread sign-match attribution | "the 5 mismatches are 2017 transition rolls and 2021" → **2017×1, 2018×2, 2019×1, 2022×1; no 2021 mismatch** (count 61/66 itself exact) | A7-ES m-1 |
| m-2 | MINOR | §0.4 | "sd(ON) ≈ 0.4–1.4%/day" → **0.25–1.41** (own year table: 2017 sd(ON)=0.25%) | A7-ES m-2 |
| m-3 | MINOR | §0.6 and §5 elevation wording | "stays elevated (1.3–2.7×) for 3+ hours" → **1.1–2.7× through +165 min** (table dips 1.107 @+105, 1.212 @+120); "+135→+165 min (early Globex)" → **+105→+165 min, RTH tail 15:00–15:45 CT** (13:00 CT anchor) | A7-ES m-3 |
| n-1 | NOTE (applied, advised) | §4 2026-09 v1 cross-check | "matches v1's +67.75 exactly — cross-validation PASS" → "consistent in sign and magnitude (0.25-pt mark-convention difference…); different quantities that coincide numerically" (v2 = vendor close spread at 2026-09-11; v1 = IBKR daily-close gap at declared roll 2026-08-31, vendor last-trade 68.00) | A7-ES n-1 |
| n-2 | NOTE (disclosed, not applied) | §7 2011-08-05 attribution | The 07:30 CT +2.10% minute precedes the S&P downgrade announcement (post-close Aug 5); it is the 07:30 macro (payrolls) slot — same cluster-day, wording loose | A7-ES n-2 |
| n-3 | NOTE (disclosed) | `ES_regime_map.py` docstring | "tag on day t uses returns up to t−1" — the tagged vol63 includes day t's own return (thresholds themselves ARE strict-past); occupancy stat descriptive only | A7-ES n-3 |
| n-4 | NOTE (disclosed) | §1 statistics window | "2023-09-28→2026-09-28" is the Chicago-date rendering; UTC dates are 2023-09-29→2026-09-29; count 5,425 exact | A7-ES n-4 |
| I-1 | INCIDENT (environment, owner) | §11 reproduction | During the A7-ES audit the local nonprice root `~/.my-quantitative-data/futures-nonprice-10syms/` was EMPTIED (raw subdirs + normalized/ incl. the fixed tidy); the audit reconstructed everything from the iCloud mirror + vendor roots. Status at errata time (2026-10-03, this lane): the root is again POPULATED (normalized/ incl. fixed `cftc_legacy_tidy.parquet` sha256 f7a2719e745c2f6f… verified present). Root-emptiness events touch "raw immutable; no deletions" — owner ledger action, not an ES-lane defect | A7-ES I-1 |

Owner-facing note: `DISPATCH_MANIFEST.json`'s "53/58" statement-inventory figure could not be reproduced by the audit; the dossier's own counts (132 statements / 92 timed / 85@14:00+7 irregular / 40 untimed 2011-15 / 131 in-data / 91 timed-with-data) all verify exactly and stand (A7-ES §5).

— End of ERRATA ledger.
