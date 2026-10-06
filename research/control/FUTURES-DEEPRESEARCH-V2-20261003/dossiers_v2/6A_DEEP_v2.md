# 6A_DEEP_v2 — Australian Dollar Futures (CME 6A) Deep Descriptive Research, 2020-01 → 2026-10

> **Task** FUTURES-DEEPRESEARCH-V2-20261003, lane **DEEP-6A**. Prep-class deep
> descriptive research: NO PnL evaluation, NO signal selection, NO conditional
> mean-return event tables (dispatch law: anything PnL-linked = NOT_RUN pending
> a registered budget/freeze). All thresholds strict-past/rolling; ex-post
> labels descriptive only.

- Generated_utc: 2026-10-03 (lane local; web access dates marked where used)
- Worktree/branch: `prep/futures-behavior-10syms-20261002` @ `26d96eb4` (base)
- Supersedes (does not delete): `FUTURES-BEHAVIOR-10SYMS-PREP-20261002/dossiers/6A_DOSSIER.md` (v1)
  sha256 `85956ee67f977ee266d50cfd29cf861631db92b0acbf0f75b820afb353cd0408`
- Owner framework: `owner_framework/6A_RESEARCH_FRAMEWORK.md` sha256
  `6f1e14133d6d5e30ee05f88e5966081c7389d8fc25a1f6b5c7aaf6c29a3cbf82`
- Dispatch: `dispatch/DISPATCH_MANIFEST.json` sha256
  `c2ecffa82f0cb715dab1ded82d21e8b55d66b30c702d9e621e224597cfe237ed`

**Data (all read-only):**

- Price: `/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim/parquet/`
  6A ohlcv-1m union of `AV1B-O1M-6A-BACKFILL2` (2020-01-01→2022-01-01, landed by
  lane FX-BACKFILL 2026-10-03), `AV1R-O1M-6A-BACKFILL` (2022→2026-04),
  `AV1T-O1M-6A` (2026-04→2026-10-01). 2,876,268 raw rows; 2,703,211 outright
  bars on 86 contracts (32 quarterly HMUZ + 54 serial) after excluding 1,584
  vendor-contaminant bars (symbol `6BU5`, a 6B-family symbol riding inside the
  6A parent request — see §7) [ERRATUM MINOR-2: was "2,704,795 … after
  excluding 1,584" — 2,704,795 is the PRE-exclusion count; post-exclusion is
  2,703,211, matching the lane's own `6A_build_cache.py` build_report.json
  and the A7-6A recompute]; 171,473 calendar-spread instrument bars kept
  strictly separate (§3.4). First bar 2020-01-01 23:00 UTC = 17:00 CT open of
  trade date 2020-01-02; last bar 2026-09-30 23:59 UTC (trade date 2026-10-01
  present only through its first 2h — partial tail disclosed; all full-session
  stats end 2026-09-30).
- Definitions+statistics `AV1T-*-ALL10` (2023-10+ only; OI 2023+): identity
  cross-check (0 mismatches) and OI migration (§3.3).
- Nonprice `/Users/hoangminhlong/.my-quantitative-data/futures-nonprice-10syms/`:
  RBA cash-rate gate HTML (full as-published decision table 1990→2026-09),
  fed/statements (147 archived FOMC statements 2011-01→2026-09),
  `normalized/cftc_legacy_tidy.parquet` (COT_LEGACY_6A "AUSTRALIAN DOLLAR -
  CME", 2006-01→2026-09-22, as_published_no_revision),
  `fred_alfred/latest/DFF_latest.csv` (latest vintage; ALFRED vintages are
  year-end-only in this corpus — CIP caveat §3.2).

**Analysis artifacts (this lane, `analysis/`):** `6A_deep_lib.py`,
`6A_build_cache.py` → `6A_cache/{outright_1m, spreads_1m, registry,
session_contract, chain_daily}.parquet` + `build_report.json`;
`6A_a1_regimes.py/.json`; `6A_a2_sessions.py/.json`; `6A_a3_term.py/.json`;
`6A_a4_events.py/.json`; `6A_a5_cot.py/.json`; `6A_a6_hypo_quality.py/.json`.

**Taxonomy used throughout:** FACT (sourced+date) / OBSERVED (script+window) /
POSTULATED (mechanism, unmeasured) / NOT_RUN (never inferred PASS).

**Chain construction (no vendor stitching anywhere):** held chain = v1 declared
calendar rule with quarterly adaptation — hold the nearest HMUZ contract until
the last session before day-1 of its delivery month, roll at that close.
1,746 sessions, 27 rolls, 2020-01-02→2026-09-30. Registry identity by vendor
instrument_id (definitions 2023-10+ authoritative: 0 mismatches; earlier by
3rd-Wednesday delivery-frame containment). Returns in two variants:
*within-contract* (v1 convention, no stitched jump) and *rolled* (roll gap
included — mark-to-market of a held position, NOT a strategy PnL).

---

## 0. Headline findings (all OBSERVED unless marked)

1. **v1's RTH-blindness is fixed and re-frames the contract**: US RTH core
   (08:30-15:00 CT) carries only **38-43%** of 6A volume; the Sydney day
   (07:00-17:00 Australia/Sydney) carries **26%**, London window ~51%,
   Tokyo ~19%. v1's IBKR corpus could see none of the home session (§2).
2. **RBA decision-minute anatomy measured for the first time** (67 meetings
   2020-2026): ±5 min around 14:30 Sydney = **9.0× baseline volume, 4.8×
   baseline |1m-return|**; change-days (n=23) run median 59-tick session range
   vs 29 on hold-days vs 19 non-event. NO conditional mean-return tables
   computed (law) (§4).
3. **H5 floor dissolved — CIP sign verified on 27 rolls**: roll-gap sign
   matches sign(US rate − AUD rate) on **100% of the 16 rolls with material
   differential (|Δ|≥25bp)** and 74% overall (mismatches concentrate in the
   2021 ZIRP-era noise). v1 had only 4 rolls; the "mild 2026 backwardation"
   is the CIP-consistent expression of RBA 4.35% > DFF 3.63% (§3.2).
4. **Regime map**: annualized vol 12.1% (2020) → 8.9% (2021) → **13.4% (2022
   USD shock)** → 10.8% → 8.4% → 9.5% → 8.4% (2026); worst drawdown is NOT
   COVID (−18.0%, trough 2020-03-19) but the **2021-02→2025-04 USD-cycle
   decline (−25.2%)**; COVID week 2020-03-09..13 = −6.83% with front volume
   exploding ~1k→147k lots/day as the roll and the crash compounded (§1).
5. **Trend persistence is a coin-flip in every year 2020-2026** (47.1-51.9%
   sign-match vs prior-50-session mean; 48.9% overall) — v1's 13.5-month
   49.4% finding now holds across 6.8 years (§1.3).
6. **v1's serial-executability defect is 96% dissolved**: 52 of 54 in-window
   serial months print bars (only 6AK0/6AQ0 2020 never trade); the literal
   next-listed chain is constructible from 2020-06 onward, and its serial
   books run a **median 51.5 lots/day** — three orders of magnitude below
   the quarterly front (~75-95k) (§3.5, §6 H3).
7. **Liquidity migration timing completed**: at every roll the NEW quarterly
   takes 4-12 days (median 8) to reach 10k lots/day and the volume
   crossover lands 9-15 days AFTER the declared calendar roll date — but
   **OI crosses first by 2-3 sessions** (2023-12→2026-09 measured on GLBX
   statistics) (§3.3).
8. **CoT: a historic 2026 positioning flip** — specs were persistently net
   SHORT AUD 2021-2025 (mean −33k…−66k contracts; crowding −0.19…−0.36) then
   flipped net LONG in 2026 (mean +16k, max +85.6k) with OI ~278k vs 138k in
   2020. Positioning extremes do NOT map to subsequent-vol gradients in the
   2020-2026 overlap (mid-positioning weeks precede slightly HIGHER vol than
   extremes — descriptive only) (§5).
9. **Data-quality**: 0 negative prices on outrights across all 6.8y (law
   held); negative prices exist ONLY on calendar-spread instruments —
   32,694 of 171,473 spread bars (the dispatch's "5,067" is exactly the
   2020-2021 backfill-era subset); 1 break-window bar in 2.7M; 0 weekend
   anomalies; front sessions 1,321-1,380 bars/day with **0.0% zero-volume
   minutes** — a strikingly complete panel (§7).

---

## 1. Strict-past regime map 2020-2026 [OBSERVED: `6A_a1_regimes.py`, window 2020-01-02→2026-09-30, held quarterly chain, full-session closes]

### 1.1 Volatility regimes

| Year | σ ann (rolled) | σ ann (RTH-only) | cum ret | worst day | median front vol/day |
|---|---|---|---|---|---|
| 2020 | 12.1% | — | −1.4% (H1 COVID +11.5% H2) | −3.86% (Mar 12) | ~80-92k |
| 2021 | 8.9% | — | −5.5% | — | ~80-100k |
| 2022 | **13.4%** | — | −6.0% | −2.39% (Dec 15) | ~70-105k |
| 2023 | 10.8% | — | −0.2% | — | — |
| 2024 | 8.4% | — | −9.3% | — | — |
| 2025 | 9.5% | — | +7.8% | **−4.55% (Apr 4, tariff week)** | ~43-73k |
| 2026 Jan-Sep | 8.4% | 7.7% | +3.9% | — | ~55-125k |

- Half-year granularity: vol peaked 14.8% (2020H1) and 14.7% (2022H2 — Fed
  hiking + USD shock), bottomed 6.1% (2026H2). Rolling-63d vol range
  6.7%→16.3% annualized (median 9.3%). [OBSERVED]
- **v1 reconciliation**: 2025-09-10→2026-10-01 full-session σ 7.85% ann vs
  RTH-only σ 7.70% vs v1's IBKR-RTH 7.45% — v1's number was biased low by
  settlement-derived deep bars, not by the RTH window itself. [OBSERVED]
- Strict-past vol-regime tags (rolling-63d vol quintile within its prior-2y
  distribution) split sessions into usable regimes (q0…q4 with mean |r|
  monotonically rising) — tags exist for regime-conditioned descriptive
  splits only, never selection. [OBSERVED]
- Large-move days (|r| > q95 of prior-126 |r|, strict past): 85 events,
  clustering in 2022Q2 (10), **2026Q1 (10)**, 2021Q1 (5), 2025Q2 (6). Top:
  2025-04-04 −4.55% (tariff shock), 2025-04-09 +3.33%, 2022-11-10 +2.91%,
  2022-11-04 +2.90%. [OBSERVED]

### 1.2 Drawdowns (rolled held-chain close vs running max — mark-to-market of a long, NOT PnL)

| Peak | Trough | Depth | Note |
|---|---|---|---|
| 2021-02-24 [ERRATUM MINOR-3: was 2021-02-25 — fresh running-max close is 02-24; depth/trough unchanged] | **2025-04-08** | **−25.2%** | the multi-year USD/commodity cycle — NOT yet recovered at window end |
| 2020-01-02 | 2020-03-19 | −18.0% | COVID crash leg |
| 2020-08-31 | 2020-10-29 | −4.7% | |
| 2021-01-06 | 2021-02-04 | −2.7% | |

COVID week anatomy (2020-03-02→03-27): week of Mar 9 cum **−6.83%**; daily
moves −1.14 (Mar 10), −3.86 (Mar 12), −3.70 (Mar 18); ranges up to 908 ticks
(Mar 19); held-contract volume 1.1k→147.5k lots/day between Mar 2 and Mar 13
(chain rolled onto 6AM0 on Mar 2 — the explosion is roll-migration × COVID
panic compounding; all-contract market volume March 2020 = 2.70M contracts,
the highest month in the corpus vs ~2.0M typical). Biggest 63-session moves:
**+19.9% ending 2020-06-17** (COVID recovery/commodity rally), −12.9% ending
2020-04-03. [OBSERVED]

### 1.3 Trend persistence (strict past)

Share of sessions whose return sign matches the prior-50-session mean sign:
**48.9% overall**; by year 2020 50.5 / 2021 47.5 / 2022 51.9 / 2023 47.7 /
2024 47.1 / 2025 47.7 / 2026 50.8 — coin-flip in every single year; by
strict-past vol quintile 44.0-50.5% (no regime rescue). v1's "no exploitable
daily trend persistence" (49.4% on 13.5 months) is confirmed as a structural
property across 6.8 years including two full macro cycles. [OBSERVED,
description-only]

### 1.4 Distribution / gaps

Rolled daily returns by era: skew −0.64 (2020-21), +0.11 (2022-23), −0.54
(2024-26); lag-1 |r| autocorr 0.095 / 0.034 / 0.111 — weak vol clustering,
unlike equity index futures. Overnight gap (full-session open vs prior RTH
close): median ≈ 0.0% in all eras, q05/q95 ≈ ∓0.12-0.17% — v1's "hidden
session is near-flat drift on median, fat tails on macro mornings" carries
over 2020-2026. [OBSERVED]

---

## 2. Session / intraday structure — the v1 RTH-blindness fix [OBSERVED: `6A_a2_sessions.py`, held-chain front bars 2020-01→2026-09, DST-correct via zoneinfo (America/Chicago, Australia/Sydney, Asia/Tokyo, Asia/Shanghai, Europe/London)]

### 2.1 Where 6A volume actually lives (volume share of held-front 1m bars)

| Window (local clock) | 2020-21 | 2022-23 | 2024-26 |
|---|---|---|---|
| Sydney day 07:00-17:00 | 27.7% | 26.2% | 26.3% |
| Tokyo 09:00-15:00 | 20.4% | 19.3% | 18.5% |
| London 08:00-16:30 | 51.0% | 52.8% | 50.6% |
| US data block 07:00-08:30 CT | 9.8% | 12.1% | 11.5% |
| **US RTH core 08:30-15:00 CT** | **38.0%** | **39.5%** | **42.7%** |
| Shanghai data 09:30-10:00 (30min) | 2.3% | 2.3% | 2.2% |
| Evening reopen 17:00-20:00 CT | 9.2% | 8.2% | 8.6% |
| Overnight 00:00-06:00 CT | 25.2% | 23.0% | 20.5% |

(Windows overlap in real time by design; shares do not sum to 100%.)

- **v1 reconciliation**: median front daily volume full-session 73,624 vs
  RTH-only 31,626 (RTH share 44.0%) on 2025-09-10→2026-10-01 — v1's IBKR
  corpus recorded under half the day, and every AU/China event it had to
  infer from the opening gap is now directly measurable. [OBSERVED]
- Intraday vol U-curve (mean |1m ret| by CT hour, 2024-26): primary peak
  09:00 CT (1.68bp), secondary peak 19:00-20:00 CT (1.19-1.27bp =
  **Sydney/Tokyo morning 10:00-11:00 local**), minimum 15:00 CT (0.68bp).
  6A is bimodal — a genuinely two-hemisphere book. [OBSERVED]
- Sydney morning profile (Sydney clock, share of day): 09:00 0.60 → 10:00
  1.78 → 11:00 1.81 → **11:30 2.35** (the Sydney-morning modal peak —
  ~1.1× the average half-hour (2.08%) and ~1.3× the median (1.77%); ~3.9×
  only vs the quiet 09:00 Sydney-open slot (0.60%) [ERRATUM MINOR-1: was
  "~4× the average half-hour intensity on all days" — the 2.35% share and
  the all-days time-of-day computation are exact; the multiplier was wrong])
  → London open (17:00-18:30 Syd)
  1.75-2.01. [OBSERVED]
- Sydney-open 30m (09:45-10:15 Syd): 1.4-1.5% of daily volume (3× the
  preceding 30m) with mean 1m range 1.8-2.4 ticks — modest but real open
  effect; nothing like an equity open. [OBSERVED]
- China-data window visibility: 09:30-10:00 Shanghai prints 2.2-2.3% of
  daily volume (≈3× average 30-min intensity) with the highest mean 1m
  range of any hub window (2.36 ticks) — the Caixin/NBS release slot is now
  OBSERVED as a structure, but release-day event splits remain NOT_RUN (no
  China calendar in corpus, §4). [OBSERVED + NOT_RUN]

---

## 3. Term structure + rolls [OBSERVED: `6A_a3_term.py`]

### 3.1 The 27 quarterly rolls 2020-2026 (declared calendar rule, quarterly adaptation)

Median roll gap **+0.41% annualized**; only 4 of 27 rolls negative
(14.8%); range −1.87% to +1.82%. Roll-session adjacent-contract close gap
(new−old): e.g. 2020-03-02 +28 ticks; 2022-12-01 **+61 ticks (+$305, +1.82%
ann)** — the Fed-peak contango; 2026 rolls −15/−27/−22 ticks (−0.42/−0.75/
−1.87% ann) — the v1 "mild 2026 backwardation", now measured as the deepest
of the corpus. Full per-roll table in `6A_a3_term.json` (`quarterly_rolls`).
Gaps are adjacent-contract close differences — NOT tradable costs. [OBSERVED]

Migration at every roll (old-side decay now VISIBLE — v1's truncation is
gone): the old quarterly still prints 61-154k median volume over its last 10
post-roll sessions; the new quarterly reaches the 10k/day front scale in
**4-12 days (median 8)** and overtakes the old in total volume **9-15 days
after the declared roll date (median 11)** (e.g. roll 2025-12-01 → volume
crossover 2025-12-12). The calendar rule therefore rolls ~1-2 weeks EARLY
relative to where liquidity actually migrates — a structural, rule-choice
fact (execution consequence POSTULATED, cost NOT_COMPUTED). [OBSERVED +
POSTULATED]

### 3.2 Roll gap vs RBA-Fed differential (v1 H5 — floor dissolved) [OBSERVED + disclosed caveat]

Rate series: RBA cash-rate target (as-published gate-HTML table — every
decision 1990→2026-09; 23 changes 2020-2026: COVID cuts to 0.10, 2022-23
hike cycle to 4.35, 2025 cuts to 3.60, **2026 hikes Feb/Mar/May/Sep to
4.60**) minus US effective Fed funds (FRED DFF, latest vintage — ALFRED
vintages in this corpus are year-end-only, so this is a latest-vintage CIP
check, not strict-PIT vintages; overnight rates as tenor proxy).

CIP direction for a USD-per-AUD quote: r_AUD > r_USD ⇒ deferred cheaper
(backwardation, negative gap). Measured: **sign agreement on 16/16 rolls
with |differential| ≥ 25bp** (100%); 20/27 overall (74%; every mismatch sits
in the 2021-era ~0.0-0.1pp differential where the sign is noise). Largest
confirmations: 2022-12-01 gap +1.82% ann vs diff −0.98pp; 2023-03-01 +1.53%
vs −1.23pp; 2026-09-01 −1.87% vs +0.72pp. **v1's H5 floor (≥8 rolls, had 4)
is dissolved; the structural relation holds with the correct quote-convention
sign.** v1's original spec had the naive sign expectation; the v2 spec
records the corrected convention. [OBSERVED; mechanism FACT-CIP; vintage
caveat disclosed]

### 3.3 OI-availability note (2023-10+) [OBSERVED]

GLBX statistics OI (stat_type 9) is available only 2023-10+, but for the 12
completed rolls since then it dates the migration precisely: **OI crossover
leads volume crossover by 2-3 sessions at every roll** (e.g. 2025-12-09 vs
2025-12-12; 2026-09-09 vs 2026-09-11). One 2024 outlier (U4→Z4 OI cross
2024-04-03, months early) flagged for the audit lane. OI-based roll rules
are now MEASURABLE on 2023-10+ but not back-testable pre-2023 in-corpus.
[OBSERVED]

### 3.4 Calendar-spread negative-price anatomy (SEPARATE — spread instruments never enter any price-behavior stat) [OBSERVED]

- Negative-price bars: **32,694 of 171,473** spread-instrument bars across
  2020-2026 (by era: 2020-21 = **5,067** — exactly the dispatch's figure,
  which was scoped to the backfill2 chunk; 2022-23 = 45; 2024-25 = 757;
  2026Q1 = 11,836; 2026Q2-09 = 14,989). **Outright negative bars: 0 in every
  era** — the dispatch law held under re-measurement. [OBSERVED]
- Negative spread closes are the CURVE SIGN itself: deferred-minus-near
  spreads print negative when the far leg is cheaper (backwardation). The
  densest negative clusters are 2026 spreads vs the Mar-27 leg (e.g.
  `6AH7-6AZ6` 100% negative, median −0.00084, Aug-Sep 2026) — i.e. the 2026
  backwardation visible in outright roll gaps (§3.1) is directly quoted in
  the spread board. [OBSERVED]
- Consistency: spread-instrument session closes track (leg1 − leg2) outright
  closes with median |diff| 0.0002-0.0008 USD (4-16 ticks) across the six
  most-printed symbols (last 90 days) — spread marks are curve information,
  not an independent price source. [OBSERVED]
- Curve snapshots (front-to-farthest quarterly, close prices): 2020-03-13
  −0.47%; 2021-06-01 +0.18%; 2022-04-29 +0.54%; **2023-01-03 +2.19%** (peak
  contango, Fed 4.25-4.50 vs RBA 3.10); 2024-01-02 +0.65%; 2026-01-02
  −0.25% (6AH6 0.66955 / 6AM6 0.66845 / 6AU6 0.66790). [OBSERVED]

### 3.5 Serial vs quarterly books on the vendor panel (v1 H3 re-measure)

52 of 54 in-window serial months (2020-2026) print bars — only 6AK0_2020
(May) and 6AQ0_2020 (Aug) never trade. Serial-month TOTAL volumes run
8-12k contracts per lifetime (e.g. 6AX0_2020 12.0k) vs quarterly totals in
the millions; on the 44 sessions where the literal next-listed rule holds a
serial book, its median volume is **51.5 lots/day (p90 233, max 593)** vs
the quarterly front's ~75-95k. v1's "serials are dead books" is confirmed
on 6.8 years of full-session data; the literal chain is constructible from
2020-06 onward (truncates at 6AK0_2020 in May 2020). [OBSERVED]

---

## 4. Event-day anatomy [OBSERVED: `6A_a4_events.py`; LAWS: volume/volatility/range timing only — NO conditional mean-return tables computed; no surprise classification (none in corpus)]

### 4.1 RBA cash-rate decisions (67 meetings 2020-01→2026-09; 23 changes, 44 holds)

Source: RBA cash-rate table (nonprice gate HTML, as-published). Anchor =
14:30 Sydney on effective_date − 1 AU business day; only off-Tuesday case is
the 2020-03-19 COVID emergency cut (announced Thu 19 Mar, effective Fri 20
Mar — the −1-BD rule still lands correctly). 2026 remaining meetings per v1
FACT: Nov 3, Dec 8. [FACT in-corpus + OBSERVED]

Release-anchored medians across all 67 events vs same-Sydney-clock windows
on non-event sessions:

| Window (min around 14:30 Syd) | Volume | mean abs 1m ret |
|---|---|---|
| −60…−5 | 1,530 vs 1,518 (**1.0×**) | 0.97 vs 0.96bp (1.0×) |
| **−5…+5** | **2,199 vs 245 (9.0×)** | **4.35 vs 0.91bp (4.8×)** |
| +5…+15 | 915 vs 225 (4.1×) | 3.05 vs 0.85bp (3.6×) |
| +15…+60 | 2,320 vs 1,228 (1.9×) | 1.56 vs 0.90bp (1.7×) |
| +60…+240 | 11,401 vs 8,214 (1.4×) | 1.67 vs 1.18bp (1.4×) |

Event-day sessions: median volume 83.8k vs 79.4k non-event; median session
range **38 vs 19 ticks (2.0×)**; Sydney-share of daily volume 30.4% vs
26.2% (activity migrates into the home session on decision days). Split:
**change-days (n=23): 93.0k volume, 59-tick range; hold-days (n=44): 77.7k,
29 ticks** — the decision-surprise channel is visible in volume/range
without any return conditioning. [OBSERVED]

### 4.2 FOMC statement days (59 statements 2020-01→2026-09; time from the statement's own "For release at" line where present, 13:00 CT convention otherwise — flagged)

±5 min around release: volume **8.2×** baseline, |1m ret| **6.2×**
(5.67 vs 0.92bp); +15-60min 4.3-4.4×; the FOMC reaction is LARGER and
LONGER than RBA's (US rates are the bigger common factor for AUD/USD), and
it lands inside RTH (13:00 CT) — the one family v1 could partially see.
Event-day sessions: 96.8k volume (+23% vs non-event), range 53.5 vs 19.0
ticks (2.8×). [OBSERVED]

### 4.3 ABS CPI / Labour Force — NOT_RUN (erratum)

The dispatch packet lists an "ABS release calendar (CPI/Labour Force
dates+times)" in nonprice; the corpus contains **no ABS family** (only the
RBA gate HTML and the items listed in the header). abs.gov.au listing pages
do not expose historical release dates (future-release time 11:30 AEDT
verified on the Labour Force landing page, access 2026-10-03, WebFetch).
The 11:30-Sydney window itself is measurably hot on ALL days (§2.1: 2.35%
of daily volume in that half-hour — the Sydney-morning modal peak, ~1.1×
the average half-hour and ~3.9× the quiet 09:00 Sydney-open slot [ERRATUM
MINOR-1: was "~4× average intensity"]) — but CPI/LF
event-day splits are **NOT_RUN** until historical release dates are added
(owner acquisition decision). [NOT_RUN + FACT-landing-page]

### 4.4 US CPI / NFP, Caixin/NBS China data — NOT_RUN

BLS gate empty in nonprice corpus; China release calendars never fetched.
The clock windows are now visible (§2.1) but event-day anatomy requires
calendars NOT in corpus. [NOT_RUN]

---

## 5. CoT AUD positioning 2006-2026 [OBSERVED: `6A_a5_cot.py`; CFTC legacy futures-only, as-published, Tue as-of/Fri 15:30 ET release (release rule FACT, cftc.gov, v1 verification)]

- Series 2006-01→2026-09-22 (1,082 weeks; release≈obs+3 business days,
  median gap verified). Net noncommercial range −107.5k (2024-03-19) to
  +103.4k (2012-12-11). [OBSERVED]
- Regime history: 2008-2013 net-long carry era (+22k to +49k means);
  2021-2025 **persistent net-short** (yearly means −33.1k/−51.6k/−52.4k/
  −38.2k/−66.1k; crowding −0.19…−0.36 of OI); **2026 flip to net-long**
  (mean +16.0k, max +85.6k) — the RBA hiking cycle (4.35→4.60) with OI
  doubling from ~138k (2020) to ~278k (2026 mean). [OBSERVED]
- Strict-past extremes vs subsequent risk (overlap era 2020+ only; tag =
  percentile vs trailing 3y, forward window starts at CoT release):
  weeks >p90 (n=49): median fwd-13w vol 8.74% ann / max-DD −4.62%;
  mid-band (n=158): 10.17% / −4.27%; weeks <p10 (n=42): 8.97% / −3.93%.
  **No monotone positioning→vol gradient** — mid-positioning weeks precede
  slightly higher vol than extremes in this window. Year-end pairing:
  2021-12-28 net −81.7k (3.8th pctile, crowded short) → 2022 vol 13.4%
  (the highest overlap year); 2019 year-end −38k → 2020 12.1%. Descriptive
  only — NOT a signal table. [OBSERVED]
- Pre-2020 price-side reads: NOT_RUN (no 6A price in corpus before
  2020-01). [NOT_RUN]

---

## 6. Hypothesis refinement vs v1 (6A-H1…H5) [OBSERVED/NOT_RUN statuses; full machine-readable version in `6A_a6_hypo_quality.json` `refined_hypotheses_v2`]

**6A-H1 v2 (RBA decision reaction) — UPGRADED, measurement floor MET.**
v1 measured only next-RTH-open gaps (RTH-blind). v2: the 14:30-Sydney
minute itself is measured (9× volume, 4.8× vol ±5min; §4.1). PARAM-GAP
6A-H1-P2 ("needs Globex data at 22:30 CT") **DISSOLVED**. PARAM-GAP
6A-H1-P1 (hawkish/dovish surprise classification) **STILL OPEN** — no
consensus/market-pricing series in corpus; the change-vs-hold split (59 vs
29-tick ranges) is the available weak proxy, labeled as such. Any trade
version = registered cycle + surprise source (owner budget). NO
mean-return conditioning computed (law). [OBSERVED + OPEN PARAM]

**6A-H2 v2 (commodity/China confirmation) — UNCHANGED-GATED.** HG copper
re-verified **NOT_IN_CORPUS** (definitions ALL10 carry no HG symbol; no HG
ohlcv line — A6 block 1); iron-ore still licensed/paid. China-data windows
now VISIBLE (§2.1) but China release calendars/surprises NOT in corpus.
The ToT-confirmation idea remains vendor/paid-gated exactly as v1's
ERRATUM left it. [NOT_IN_CORPUS + NOT_RUN]

**6A-H3 v2 (roll execution vs thin serials) — MEASURED END-TO-END with one
caveat.** Serial coverage 52/54 in-window months (2 never-trade 2020
serials); literal chain constructible from 2020-06; serial books median
51.5 lots/day vs quarterly ~75-95k (§3.5); migration fully mapped incl
old-side decay and OI-lead (§3.1/§3.3). The v1 executability defect is
96% dissolved and its economic content (never hold serials at size) is
re-confirmed on 6.8y of full-session data. [OBSERVED]

**6A-H4 v2 (AUD equity-beta regime dependence) — MEASUREMENT READY, spec
frozen.** 6A-vs-ES daily within-contract returns (ES = sibling DEEP-ES
declared-chain cache, read-only): yearly corr 0.43-0.63, OLS beta 0.18-0.43;
by ex-ante ES-vol regime (trailing-63d vol vs prior-252d median, strict
past): corr 0.487 risk-on vs 0.533 risk-off, **beta 0.351 risk-on vs 0.247
risk-off** — beta is HIGHER in risk-on, direction consistent with the v1
mechanism (long-risk carry currency), measured descriptively with no
signal/PnL attached. Regime-tag definition **frozen a priori here** for any
future registered run (this kills param-gap 6A-H4-P1's tuning risk; the
USD-beta control via 6E remains NOT_RUN in this lane). [OBSERVED + POSTULATED mechanism]

**6A-H5 v2 (roll-gap vs rate differential) — FLOOR DISSOLVED, RELATION
MEASURED.** 27 rolls vs v1's 4 (floor was ≥8): CIP sign agreement 100% on
material differentials (§3.2), with the corrected quote-convention sign
(v1's naive expectation was sign-flipped). Caveats: DFF latest-vintage
(year-end-only ALFRED vintages), overnight-tenor proxy. The relation is a
structural input (curve/carry description), not a signal. [OBSERVED]

**New v2 candidate (NOT a v1 hypothesis; descriptive observation only):**
the **OI-leads-volume migration** (2-3 sessions, §3.3) and the
**RBA-change-day range doubling** (§4.1) are the two cleanest
newly-measurable structures; both are recorded as observations for future
hypothesis design — deliberately NOT specified as signals here (no PnL
evaluation law). [OBSERVED]

---

## 7. Data-quality ledger per era [OBSERVED: `6A_build_cache.py`→`build_report.json`, `6A_a6_hypo_quality.py`]

Eras by acquisition line: BF2 = 2020-2021 backfill2; BF1A = 2022-2023;
BF1B = 2024-2025; BF1C = 2026Q1; TRIM = 2026Q2-Q3.

| Check | BF2 2020-21 | BF1A 2022-23 | BF1B 2024-25 | BF1C 2026Q1 | TRIM 2026Q2-09 |
|---|---|---|---|---|---|
| front sessions | 518 | 516 | 517 | 63 | 132 |
| front bars/session (min/med/max) | 157/1343/1380 | 122/1361/1380 | 115/1350/1380 | 371/1364/1379 | 99/1321/1372 |
| zero-volume minutes (front) | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| max calendar gap between sessions | 4d | 4d | 4d | 3d | 3d |

Global: 1,746 sessions; **1** break-window bar in 2,703,211 [ERRATUM
MINOR-2: was 2,704,795 — pre-exclusion count; see header] (single
16:00-17:00 CT violation, recorded in build_report); **0** weekend
anomalies; DST-transition-day front bar counts median 1,351 (consistent
with the ±60min clock shift — no DST data loss); registry 86 contracts, 0
definition mismatches, 1 instrument (id 7084 `6AM5`) with pre-activation
stray clusters (914 bars Jan-May 2020 before its 2020-06-15 activation —
negligible volume, recorded, excluded from frame stats); 1,584
`6BU5`-contaminant bars excluded (§header); negative prices: 0 outright /
32,694 spread bars (§3.4). Session template verified empirically:
17:00 CT Sunday open → 16:00 CT Friday close, 60-min maintenance break
honored 2020-2026. Volume cross-check: vendor full-session 2026-09-15
front 59,451 vs v1 IBKR RTH 46,592 same day (RTH ≈ 78% — consistent scales,
no per-symbol vendor scaling artifact). [OBSERVED]

**Vendor/request caveats:** 2020-2021 identity rests on instrument_id +
DBN-prelude (definitions begin 2023-10) — validated by 0-mismatch
cross-check where definitions exist and by delivery-frame containment
elsewhere; raw_symbols are decade-ambiguous by vendor convention (handled
by the registry). Statistics (settlement/cleared-volume/OI) exist only
2023-10+. [OBSERVED + disclosed]

---

## 8. Remaining NOT_RUNs (explicit)

1. ABS CPI/Labour Force event anatomy — no historical release dates in
   corpus (§4.3; dispatch-packet erratum). NOT_RUN.
2. US CPI/NFP and Caixin/NBS China event-day splits — no calendars in
   corpus (§4.4). NOT_RUN.
3. Any conditional mean-return event table / PnL-linked selection —
   prohibited by dispatch law pending registered budget/freeze. NOT_RUN.
4. HG copper / iron-ore ToT legs (6A-H2) — NOT_IN_CORPUS / licensed. NOT_RUN.
5. Surprise classification for RBA days (market pricing at 14:30) — no
   source in corpus (weak proxy change-vs-hold measured instead). NOT_RUN.
6. Pre-2020 price-side CoT reads; OI-based rules pre-2023-10. NOT_RUN.
7. 6E USD-beta control for H4 (sibling cache reuse limited to ES by
   discipline). NOT_RUN.
8. Tradeable roll-cost computation (crossing both legs) — gaps reported as
   adjacent-close differences only. NOT_COMPUTED.

---

### ERRATA applied 2026-10-03 (lane DOSSIER-ERRATA-V2)

Source of record: `audit/a7_6a/A7_DEEP_6A.md` — verdict PASS_WITH_FINDINGS
(0 BLOCKER / 0 MAJOR / 3 MINOR / 4 NOTE; all 9 recomputed headline families
match). Each item is applied in place above and marked `[ERRATUM …]` at the
correction site; nothing was silently rewritten. The 4 NOTEs required no
dossier change (NOTE-1: the §3.3 "2024 outlier" was the lane's unanchored
first-crossover scan — roll-anchored OI cross 2024-09-11, lead 2 days,
disclosure was honest; NOTE-2: RBA baseline rounding only; NOTE-3: CoT fix
row-identical for COT_LEGACY_6A (0/1082 mismatches), dossier valid on the
fixed tidy; NOTE-4: DFF 3.63 is the Sep-1 roll-date value, correct in context).

| id | severity | was (old) | now (new) | site |
|---|---|---|---|---|
| MINOR-1 | MINOR | 11:30-Sydney slot "~4× the average half-hour intensity" | 2.35% share exact; ~1.1× the mean half-hour (2.08%), ~1.3× the median (1.77%); ~3.9× only vs the quiet 09:00 slot (0.60%) | §2.1; §4.3 |
| MINOR-2 | MINOR | "2,704,795 outright bars … after excluding 1,584" (header and §7) | 2,704,795 is PRE-exclusion; post-exclusion **2,703,211** (= build_report.json) | header; §7 |
| MINOR-3 | MINOR | USD-cycle DD peak 2021-02-25 | peak **2021-02-24** (fresh running-max close; depth −25.2%, trough 2025-04-08 unchanged) | §1.2 |

INCIDENT (lane DOSSIER-ERRATA-V2, 2026-10-03): a power outage killed the
errata session mid-run; 6A's errata (untouched in the partial state) were
applied in full on resume.

---

### Defects / caveats register (this lane)

1. [OBSERVED] Vendor contamination: 1,584 `6BU5` bars inside the 6A parent
   request (2020-05→08) — excluded from every stat, recorded in
   build_report.json.
2. [OBSERVED] Pre-activation stray clusters on instrument 7084 (`6AM5`):
   914 bars Jan-May 2020 before activation 2020-06-15 — excluded from
   contract-frame stats.
3. [OBSERVED] 2 serial months never traded (6AK0/6AQ0 2020) → literal chain
   truncates May-2020; constructible from 2020-06.
4. [DISCLOSED] CIP check uses DFF latest-vintage (ALFRED year-end-only) and
   overnight tenor; RBA table as-published. Not strict-PIT vintages.
5. [DISCLOSED] Trade date 2026-10-01 present only through ~18:59 CT of
   Sep-30 (2h); all full-session stats end 2026-09-30.
6. [DISCLOSED] ES beta block reuses sibling lane DEEP-ES's chain cache
   (read-only, their declared-rule chain) — cross-lane reuse disclosed,
   no writes.
7. [ERRATUM vs dispatch] "ABS release calendar in nonprice" — not present
   in corpus; and the "5,067 negative bars" figure is the 2020-21
   backfill-era subset of the 32,694-bar full-corpus count (§3.4).
8. [NOT_RUN] CME official fee/SPAN pages still transport-blocked (v1 §4
   note carries forward); tick-size 0.00005-vs-0.0001 legacy conflict
   remains unadjudicated (vendor min_price_increment 5e-05 used throughout
   = $5.00/tick).
