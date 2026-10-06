# 6E DEEP DOSSIER v2 — Euro FX Futures, 2020-2026.8

- Symbol: **6E** (CME Globex; EUR 125,000 vs USD; USD-per-EUR; minTick
  5e-05 = $6.25/tick) — carried from v1 [FACT/OBSERVED, 6E_DOSSIER.md §1].
- Task: FUTURES-DEEPRESEARCH-V2-20261003, lane **DEEP-6E**. Generated
  2026-10-02 (UTC). PREP class: 0 PnL, 0 scored runs, 0 parameter
  selection; every threshold strict-past/rolling; event content is
  release-anchored descriptive anatomy only — anything PnL-linked
  selection = NOT_RUN.
- Data window: **2020-01-01 → 2026-09-30 (6.75y, 1,746 held-chain
  sessions)** on Databento GLBX.MDP3 ohlcv-1m per-contract bars
  (vendor parquet under `~/.my-quantitative-data/futures-databento-av1trim/`,
  read-only), stitched into three eras (§1). v1 depth was 13.5 months of
  RTH-only IBKR daily bars with a 247-day true-volume window; v2 has
  23h-session 1m bars for the whole span — v1's two structural
  limitations (depth, RTH-blindness) are both dissolved.
- Inputs (this lane, all under
  `research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/`):
  - `6E_deep_lib.py` + `6E_build_cache.py` → `6E_cache/`
    (annotated 1m panel 3,054,311 outright bars; contract registry 90
    contracts; session table 11,705 contract-sessions; 3 held-contract maps)
  - `6E_a1_regime.py` → `6E_a1_regimes.json` (regime map)
  - `6E_a2_sessions.py` → `6E_a2_sessions.json` (session structure)
  - `6E_a3_term.py` → `6E_a3_term.json` (term structure, 27 rolls, CIP)
  - `6E_a4_events.py` → `6E_a4_events.json` (ECB/FOMC/8:30 anatomy)
  - `6E_a5_cot.py` → `6E_a5_cot.json` (CoT 2006-2026)
  - `6E_a6_dq.py` → `6E_a6_dq.json` (per-era data-quality ledger)
- Parent evidence (read-only): v1 `dossiers/6E_DOSSIER.md`,
  `owner_framework/6E_RESEARCH_FRAMEWORK.md` (sha256
  `db5fbaff…e1aedcd`), acquisition ledgers (COMPLETION_LEDGER.json,
  BACKFILL_LEDGER.json), nonprice normalized data
  (`~/.my-quantitative-data/futures-nonprice-10syms/`).
- Claims taxonomy: **FACT** (primary source + date), **OBSERVED**
  (script + window), **POSTULATED** (mechanism, unmeasured), **NOT_RUN**.
- **ERRATA applied 2026-10-03** (lane DOSSIER-ERRATA-V2, from
  `audit/a7_6e/A7_DEEP_6E.md`, verdict PASS WITH ERRATA — 12/12 headline
  recomputes match): **MAJOR-1** the "GLBX venue OI = 2.000× CFTC OI
  convention" claim is RETRACTED (publication-duplication artifact in a5's
  raw-row sum; deduped venue OI reconciles 1:1 with CFTC); **MAJOR-2** the
  CIP r=0.91 headline is vintage-fragile (PIT-as-of reconstruction from
  on-disk ALFRED vintages gives r=−0.107) — H2 downgraded to
  "sign 26/27 PIT-robust, magnitude vintage-dependent"; plus five MINOR
  text/label corrections. Full old→new ledger in §11.

---

## 1. Data plane and quality ledger (per era)

Three delivery eras combine into a continuous 2020-2026.9 panel
[OBSERVED, `6E_a6_dq.json`; vendor provenance in COMPLETION_LEDGER.json
(lane ACQ-DOWNLOAD) and BACKFILL_LEDGER.json (lane FX-BACKFILL, job
GLBX-20261002-94UVSCXK6G, sha256 c3fd0a88…, $3.47, no-overlap butt at
2022-01-01)]:

| era | files | bars | sessions | median bars/sess | median sess vol | price range |
|---|---|---|---|---|---|---|
| AV1B backfill2 2020-01→2021-12 | 1 | 886,127 | 518 | 1,600 | 161,634 | 1.0648–1.2429 |
| AV1R backfill 2022-01→2025-12 | 2 | 1,823,090 | 1,033 | 1,633 | 179,300 | 0.9552–1.21495 |
| AV1T original 2026-01→2026-09 | 2 | 345,094 | 195 | 1,653 | 150,359 | 1.1323–1.2253 |

- **Quality is uniform and clean across eras** [OBSERVED, `6E_a6_dq.json`
  `eras`]: 0 stale flat zero-volume bars, 0 duplicate (contract, minute)
  bars, 0 negative prices, 0 close-price tick-multiple violations
  (1e-9 fixed point vs 5e-05 tick), 0 weekend-anomaly bars, 1 single
  maintenance-break bar (16:00–17:00 CT, AV1B era) removed from session
  aggregation. Median session prints 1,600+ 1m bars ≈ full 23h Globex
  coverage (1,320 tradable minutes + multi-print minutes); p05 1,450+.
- **Era boundaries butt cleanly** [OBSERVED]: 2021-12-31→2022-01-03 and
  2025-12-31→2026-01-02 held-contract (6EH2_2022 / 6EH6_2026) closes
  continue without gap (1.13875→1.1314; 1.17855→1.17585); 0 held-chain
  sessions without front bars.
- **Symbol-plane contamination, filtered and disclosed** [OBSERVED,
  `6E_a3_term.json` `stray_symbol_rows`]: the 6E parent-symbol downloads
  contain non-6E outright rows — `6JZ7` 4,831 bars (AV1B file),
  `SIJ5` 1,869 bars (AV1R file) — plus calendar-spread instruments
  (`6EG0-6EF0`-style, 60,429/256,918/58,375 rows per era = 6.4%/12.4%/14.5%
  of rows). The OUTRIGHT_RE filter `^6E[A-Z]\d$` (all months) keeps 6E
  outrights only; spread instruments are NOT part of price panels but
  their **rising row share (6%→14%)** is itself a microstructure fact:
  roll/calendar execution increasingly migrates into dedicated spread
  books [OBSERVED row counts; interpretation POSTULATED].
- **Definitions dataset not used for identity**: 2023-10+ only; contract
  identity was built from bars + IMM expiry rule validated below. The
  `instrument_id` per symbol is stable within the window (registry
  `instrument_ids` lists) [OBSERVED].
- **Statistics dataset (settlement/cleared volume/OI) is 2023-10+ only** —
  every OI-dependent statement below is era-limited and tagged.
- **Venue-OI vs CFTC OI — "2.000× convention" RETRACTED** [ERRATUM
  MAJOR-1; evidence A7-DEEP-6E §2]: the pre-audit text claimed GLBX
  statistics OI summed over listed 6E outrights = **2.000×** CFTC legacy
  futures-only OI (156 overlap weeks; median ratio 2.0003) and called it an
  "engine-critical systematic convention difference (double-counting
  convention)". **That is a publication-duplication artifact, not a
  convention.** The GLBX statistics dataset publishes MULTIPLE rows per
  (contract, ref_date) for stat_type 9 (7,615 pairs ×2, 107 ×3, 8 ×4,
  107 ×1) — duplicate publication events, usually identical quantity; a5's
  RAW-ROW SUM doubled everything (and tripled it on 3-publication days:
  "ratio" 3.000× on 2023-11-21, 2023-10-24, 2023-11-07, 2024-02-27,
  2024-07-30 — a genuine convention difference can never triple). **Dedup
  to latest publication per contract-day: median ratio 1.0000 vs CFTC CoT
  OI** (p05 1.0000, p95 1.00005; 150/156 weeks within ±0.2%; probe week
  2024-06-04: venue sum 671,736 == CoT OI 671,736 exactly). The 3 residual
  weeks (2025-06-17 ×1.31, 2026-03-17 ×1.27, 2025-09-16 ×1.18) are
  roll/expiry weeks where the venue statistic still carries the
  just-expired contract (e.g. 6EM5 232,435 on 2025-06-17) that CFTC
  zeroes. Adjudication: NO contract-unit or convention difference exists —
  GLBX stat_type-9 OI and CFTC legacy futures-only OI are the same
  single-sided measure after deduplicating publications. Internal
  inconsistency that confirmed the artifact: this lane's own a3
  OI-crossover analysis used a DEDUPED table
  (`groupby(...).agg(last)`) while a5 summed raw rows; only the a5 side
  was published as a "convention". The OI-vs-volume crossover finding
  (§5) used the deduped table and is UNAFFECTED. Hygiene rule that
  survives: dedupe publications before any venue-OI join (the old
  "never mix / scale-normalize" warning was harmless but addressed a
  nonexistent scaling).
- **What v1's data could not see, quantified** [OBSERVED,
  `6E_a6_dq.json` `rth_only_view_would_miss`]: 55.3% of front-contract
  volume (1,504,002 of 2,252,088 front bars) trades OUTSIDE the IBKR
  "liquid hours" 08:30–16:00 CT that v1's bars were limited to. Every
  session-structure claim in v1 §3 was drawn from the 44.7% RTH slice.

## 2. Mechanics deltas vs v1

- **Expiry rule extended — two holidays v1's model missed** [OBSERVED,
  `6E_cache/expiry_rule_check.json`]: last trade = 2nd exchange business
  day before the 3rd Wednesday of the delivery month. v1's holiday set
  (MLK, Presidents) validates 20/20 on its sample, but the deeper data
  adds: **Juneteenth** (6EM3 last session 2023-06-16, rule-without-holiday
  said 2023-06-19) and **Columbus Day** (Oct serials 6EV4 2024-10-11,
  6EV5 2025-10-10). Final model — holidays {MLK, Presidents, Juneteenth
  (2022+), Columbus Day, Good Friday, Veterans Day, weekend-observed
  shifts}: **80/80 expired contracts match the last observed trading
  session exactly** (quarterlies AND serials, 2020-2026). Quarterly
  expiries are Mondays (32/33; the exception is Friday 2023-06-16).
- **Sessions** [OBSERVED, bars]: 17:00 CT → 16:00 CT (23h, break
  16:00–17:00 CT), Sunday-evening open present on 348/1,746 sessions
  (all Mondays; 1.9% of front volume). DST handling corrected in this
  lane's code: wall-clock session-date arithmetic (absolute timedelta
  addition lands on the wrong date on DST-transition evenings — 2,712
  bars were mislabeled before the fix; final panel has zero
  Sat/Sun-dated sessions).
- **Serials are dead books across the FULL 6.8y** [OBSERVED,
  `6E_a3_term.json` `serial_vs_quarterly`]: 57 serial contracts vs 33
  quarterlies; serials carry 1.06M contracts total = **0.34% of outright
  volume** (quarterly 309.8M), median daily volume when active 140
  contracts, max single day 9,019, zero serials with median ≥1k. v1's
  333:1 same-window ratio generalizes: the liquid vehicle is exclusively
  the front quarterly, all years, no exceptions.

## 3. Regime map 2020-2026 [OBSERVED, `6E_a1_regimes.json`]

Quarterly-only chain, declared calendar roll, within-contract (gap-free)
daily returns, n=1,746 sessions / 1,745 returns [ERRATUM MINOR-3a: was
"n=1,751" — artifacts say 1,746 sessions / 1,745 returns].

- **Daily returns**: mean −0.44 bp/day, std **0.463%** (annualized
  7.36%), min −2.07% (2020-03-19), max +2.29% (2025-04-10), skew +0.19,
  excess kurtosis +1.83, q05..q95 −0.75%..+0.74%. v1's front-scale-era
  std was 0.333% — the v1 window was unusually calm (below).
- **Multi-horizon vol**: ann. vol from 1d/5d/21d/63d horizons =
  7.36% / 7.31% / 6.95% / 7.18% — term structure of vol is FLAT (no
  strong horizon amplification/damping beyond noise).
- **Rolling 63d ann vol**: min **3.56%** (2026-01-16 [ERRATUM MINOR-3b:
  was "2026-01-14"; artifact + fresh recompute say 2026-01-16]) … median
  6.59% … max **13.07%** (2022-12-01) — a 3.7× vol range. Regime shares:
  55.5% of sessions below 7%, 28.4% in 7–10%, 12.5% above 10%, 0% above
  15%.
- **Annual regimes** (drift / ann vol / close range):
  2020 +9.0%/7.5% (1.0734–1.2320); 2021 −7.2%/5.6% (1.1205–1.2345);
  **2022 −5.0%/9.97% (0.9651–1.1469) — the EUR-crisis year: vol 1.77×
  2021's, parity broken 2022-07 (week of the 2022-07-21 ECB +50 hike);
  front-chain min close 0.96505 (2022-09), the era's absolute 1m-close
  minimum across all listed contracts 0.9552**
  [OBSERVED; driver attribution POSTULATED: energy terms-of-trade +
  Fed-ECB differential]; 2023 +4.5%/7.5%; 2024 −5.3%/5.9%;
  2025 **+14.4%/7.9%** (largest annual drift, 1.0274→1.1929);
  2026 YTD −3.4%/5.7% (to 2026-09-30, close 1.1361).
- **Where v1's window sits** [OBSERVED, `v1_window_placement`]: the v1
  247-day window (2025-09-09→2026-10-01 in v1's IBKR data; 277 sessions
  here to 2026-09-30) has ann vol 5.41% = **6.8th percentile** of all
  same-length rolling windows 2020-2026 (rolling p05 5.66 / p50 7.19 /
  p95 9.94 [ERRATUM MINOR-3c: p05 was "5.65"; artifact 5.6601]); its −5.5% drift is 25.8th percentile. v1's "single-regime,
  no-crisis-sample" caveat is now quantified: **v1 sat at the bottom
  decile of the 6.8-year vol distribution** — any v1-calibrated
  volatility/cost parameter (spread, slippage, vol-scaling) is
  calibrated on a quiet-regime draw.
- **Drawdown anatomy** (ratio-adjusted level, gap-free returns): max
  drawdown **−23.6%**, start 2021-01-07, trough 2022-09-27, 446 sessions,
  NOT recovered by 2026-09-30 (2025 rally high 1.2253 < Jan-2021 peak
  region 1.2345). Second: COVID 2020-03-09→03-20 **−6.6%** in 9 sessions,
  recovered 2020-07-21 (95 sessions). Five further drawdowns ≤4%.
  Top-5 |daily moves|: 2025-04-10 +2.29% (tariff-pause day, largest
  single-day move of the whole sample), 2022-11-04 +2.20%, 2020-03-19
  −2.07%, 2022-11-10 +1.96%, 2024-11-06 +1.84% (US election+Fed week).
- **Trend persistence** [OBSERVED, `trend_persistence`]: daily return
  autocorrelations ≈ 0 (lag1 +0.005 … lag21 −0.028); variance ratios
  VR(10)=0.927, VR(21)=0.887, VR(63)=0.950 — **mild mean-reversion at
  2–4 week horizons**, no daily momentum; |ret| lag-1 autocorr 0.139 /
  lag-5 0.125 — vol clustering similar to v1 (0.136-0.171) and stable
  across the deeper sample.
- **Regime-map answers for owner framework §4**: vol regimes span
  3.6–13.1%; trend regimes: 2022 one-way crisis slide, 2025 one-way
  rally (+14.4%), 2023/2024/2026 ranges; monetary regime (POSTULATED
  labels, rates data on disk): Fed hiking 2022 → both easing 2024-2025 →
  differential compression (§5 roll gaps track this). Invariance: none
  tested conditionally (selection = NOT_RUN).

## 4. Session / intraday structure — v1's RTH blindness dissolved
[OBSERVED, `6E_a2_sessions.json`; 2,252,088 front-quarterly 1m bars,
1,746 sessions; DST-correct via America/Chicago + Europe/London zoneinfo]

- **Volume by CT hour (full session)**: the day is **double-humped with a
  US-morning peak**: h+07..h+10 CT (08:00–11:00 CT, late-London/NY
  overlap) = 40.5% of volume (h+09 alone 12.2%); London morning
  02:00–05:00 CT = 17.1%; ECB+US-data block 06:30–08:00 CT = 12.5%;
  Asia (19:00–02:00 CT) = 12.2%; quietest session hours (excluding the
  16:00 CT break hour): **17:00–18:00 CT (1.004%) and 23:00–24:00 CT
  (1.015%)** [ERRATUM MINOR-3d: was "~01:00 CT (1.0%) and 18:00 CT
  (1.0%)" — session-hour labels (h−07, h−01) were misread as clock
  times; 01:00 CT actually carries 3.99%]; 16:00 CT (close+break) ≈ 0.
- **Information (realized-variance) shares differ from volume shares**:
  by 1m realized variance, **ECB/US-data window 06:30–08:00 CT carries
  15.6% of full-session variance with only 12.5% of volume** — the
  highest information-per-contract segment of the 6E day; London morning
  16.6% of RV; US morning 15.5%. Median per-session RV shares: London
  morning 17.6% (top), ECB/US-data 10.6%, US-morning-late 15.1%.
- **London flow follows London local time (DST-correctness proof)**
  [OBSERVED, `dst_mismatch_effect`]: in US/EU DST-mismatch weeks
  (~March, late Oct–early Nov; 159,982 front bars), the CT-hour volume
  profile shifts by exactly one CT hour: h+02 share falls 6.79%→4.71%
  while h+03 rises 5.64%→6.80%, h+04 4.70%→5.71%, h+05 4.33%→5.03%
  (Oct/Nov case: London on GMT while Chicago still on CDT, so London
  08:00 local = 03:00 CT). London-local 08:00–12:00 = 21.6% of volume
  vs 17.1% for the fixed CT 02:00–05:00 window. **Any session-bucketed
  engine feature must bucket by Europe/London local time, not CT.**
- **US 8:30 ET data block** [OBSERVED, `us_830et_block`]: the 07:30 CT
  minute shows a clean daily release spike: median volume 277 vs 142 the
  minute before (**×1.95**), median 1m range 3.0 ticks vs 2.0 (**×1.5**),
  present on 1,732/1,746 sessions. This block is on EVERY weekday —
  event-type decomposition (CPI vs NFP vs other) NOT_RUN (no PIT release
  calendar on disk).
- **v1's hidden-gap estimate re-measured on true 24h data**
  [OBSERVED, `v1_gap_remeasure`]: RTH-open gap (08:30 CT first bar vs
  prior session close) std 0.378% vs full-day return std 0.470% =
  **80.4% ratio — v1's RTH-only estimate (79%) was accurate**. But v2
  decomposes WHERE that variance lives: Asia 15.2% of RV, London morning
  16.6%, ECB/US-data 15.6%, pre-RTH 4.5%, RTH+afternoon 38.5% (volume
  split: 44.7% inside vs 55.3% outside IBKR liquid hours) — the
  "gap" is not one blob; it is two named sessions plus two release
  blocks, each now directly measurable at 1m.
- **Weekday**: volume Thu 21.3% > Wed 20.9% ≈ Fri 20.9% > Tue 19.4% >
  Mon 17.6% (Monday carries the Sunday-open thin evening).
- **Session coverage**: median 1,356 front bars/session (≥ full
  tradable minute count — 1m bars can multi-print); p05 volume 7,904
  contracts (thin half-days exist but rare; no zero-volume held sessions).

## 5. Term structure, rolls, and CIP — v1's 4-roll sample → 27 measured
[OBSERVED, `6E_a3_term.json`]

- **Roll events**: 27 quarterly rolls measured under the declared
  calendar rule (2020-03→2026-09), each with: roll session, days to
  expiry, gap, CIP prediction, volume/OI crossover (JSON `rolls`).
- **Roll gaps: 27/27 positive** [+36..+138 ticks, median **+91 ticks**
  (+0.455% of level ≈ +$568.75/contract)], annualized +0.80% (2021) to
  +2.20% (2022) per year, median +1.73%/yr. **Sign agreement with the
  SOFR−€STR differential: 27/27 (latest-vintage rates); correlation gap vs
  CIP-predicted gap r = 0.91; median residual gap−CIP = +6.2 ticks** —
  all three reproduce exactly on the lane's LATEST-VINTAGE basis. **[ERRATUM
  MAJOR-2 — vintage-sensitivity disclosure; evidence A7-DEEP-6E §3]**
  Rebuilding the rate series PIT-AS-OF each roll from the ALFRED year-end
  SOFR vintages that exist on disk (2019-12-31…2024-12-31 + 2026-09-30;
  **no 2025-12-31 vintage exists**) gives **r = −0.107, sign agreement
  26/27, median residual +3.77 ticks** — the headline correlation does not
  hold on the only vintage data available for a PIT reconstruction. Two
  readings, both now on the record: (a) year-end vintages are too stale
  (up to 12 months; up to ~21 months for 2025-26 rolls with no 2025
  vintage) to test CIP, and real-time SOFR (knowable daily, essentially
  unrevised) would have matched — r=0.91 defensible but currently
  UNVERIFIABLE from disk; or (b) the correlation is a latest-vintage
  artifact. €STR is latest-only (ECB SDW), no vintage set on disk.
  **PIT-robust across both bases: sign agreement (26/27) and the
  one-sided positive residual; vintage-dependent: the r=0.91 magnitude.**
  (~+0.12%/yr excess — small but one-sided; candidate
  microstructure/hedging-flow premium [POSTULATED]). Rates: FRED SOFR
  (latest vintage) + ECB €STR (SDW latest); €STR essentially unrevised,
  SOFR revisions negligible per NY Fed methodology [stated, not
  independently verified here]. v1's H2 PARAM-GAP (rate series absent) is
  **dissolved**.
- **What an unadjusted continuous chain would embed**: +0.80%..+2.18%
  per year of artificial upward drift (sum of roll gaps: 2020 +1.09%,
  2021 +0.80%, 2022 +2.18%, 2023 +1.93%, 2024 +1.60%, 2025 +2.10%,
  2026 +1.16% through Sep) — back-adjustment remains mandatory; the
  embedded drift is LARGEST exactly in the high-differential years
  (2022, 2025) where trend signals would be most contaminated
  [OBSERVED; contamination-of-signals claim POSTULATED→engine spec].
- **Liquidity migration, n=27** [OBSERVED, `migration_median_new_volume_share`]:
  median new-contract share of (new+old) volume by calendar days to old
  expiry: d−7 9.5% → d−5 19.6% → d−4 (Thursday) 30.7% → **d−3 (Friday)
  87.1%** → d−0 (Monday expiry) 98.8%. Quarterly expiries are Mondays
  (32/33), so **the spot volume crossover lands on the Friday before
  expiry week — 1 trading session before the old contract's last
  session** (v1's 4/4 "1–2 sessions before expiry" confirmed and
  generalized to 27/27).
- **Declared-rule thin windows: DISSOLVED** [OBSERVED,
  `declared_rule_thin_windows`]: across all 27 rolls, the final 14
  sessions before delivery-month day-1 contain **0 sessions below 10k
  contracts and 0 below 25k** on the held front. v1's "4–7 thin sessions
  per quarter" was an artifact of its expired-secdef wall (chain held
  deferred settlement marks), not a market property. The v1 baseline
  roll rule is executable at size in this data; the residual question is
  only gap-optimization, not liquidity.
- **OI vs volume crossover (2023-10+ only, n=12 rolls)** [OBSERVED,
  `oi_vs_vol_crossover`]: OI crossover (GLBX statistics, next-morning
  publication) leads the k=5 trailing-volume rule crossover by a
  consistent **5–6 days in 7/12 rolls** (the other 5 show 217–540-day
  artifacts from stale early OI prints in deferred books — disclosed,
  excluded from the pattern statement). A PIT OI-triggered roll must
  consume the statistic with its publication lag (adapter law).
- **Roll execution microstructure**: calendar-spread instrument row
  share rising 6.4%→14.5% of the symbol plane (§1) suggests rolls
  increasingly execute as spreads rather than two outrights
  [POSTULATED; instrument-level volume not summed here — row counts
  OBSERVED].

## 6. Event-day anatomy — ECB GC + FOMC + 8:30 ET [OBSERVED, `6E_a4_events.json`]
Descriptive release-anchored timing only; **no conditional mean-return
tables** (PnL-linked selection = NOT_RUN by task law).

- **Event sets**: ECB GC monetary-policy decision dates 2020-2026: 55 in
  window (incl. both March-2020 emergency meetings), of which **10
  machine-verified by direct fetch of the ECB press-release URL** (HTTP
  200 + date + title match; URL scheme `ecb.mpYYMMDD~hash` prevents full
  enumeration; ECB archive pages JS-rendered; Wayback offline at access
  time). Assembly source: ECB monetary-policy decisions archive
  (ecb.europa.eu, accessed 2026-10-02) — dates beyond the 10 verified
  are FACT-with-assembly-method disclosed. Release time FACT: decision
  press release **14:15 CET/CEST, press conference 14:45** (ECB pages,
  fetched 2026-10-02) = 07:15 CT in 49/55 cases, 08:15 CT in the 6
  spring DST-mismatch meetings (computed per-date, Europe/Berlin →
  America/Chicago). FOMC: 58 statements 2020-2026, **all 58 with
  primary-source time proof** ("For release at …" parsed from archived
  federalreserve.gov HTML on disk); 53 at 13:00 CT, the rest are 2020
  emergency-timing meetings (11:00 ET, 07:00 CT, 08:15 CT…).
- **ECB decision minute (07:15/08:15 CT)**: median volume ×**1.73** vs
  control Thursdays at the same minute; press-conference minute +30m
  ×1.46; pre-release minutes are QUIETER than control (×0.88–0.94) —
  the book goes still, then reprices. On event days the peak-volume
  minute within 06:00–09:00 CT clusters at the release/presser minutes
  (435–446) and the 07:30 US-data collision (450), while control
  Thursdays peak scattered across the early-morning hours. 93.6% of
  06:00–10:00 CT volume arrives after 06:45 on event days vs 90.2%
  control (modest skew: ECB days are also US-data days).
- **FOMC statement minute (13:00 CT)**: median volume ×**17.2** vs
  control Wednesdays at 13:00 CT; +5m ×9.96; +10m ×5.61; +20m ×3.21;
  re-amplifies at 13:40 CT (×8.8, press-conference rhythm). Peak volume
  minute: 24/58 events peak at exactly 13:00 CT (control-Wednesday peak
  minutes: **mode 13:59 CT — 162 of ~340 control Wednesdays — with
  12:00–12:02 CT a secondary cluster (26 sessions)** [ERRATUM MINOR-4:
  was "peak at 12:00–12:07 CT"; the recurring-midday-flow narrative was
  built on the secondary cluster; the FOMC ×17.2 headline is unaffected]).
  88.9% of 12:00–16:00 CT volume arrives after 13:00 on event days vs
  68.8% control. **FOMC is the single largest scheduled 1m-volume event
  in the 6E day; ECB is a 1.7× blip against a busy morning block.**
- **8:30 ET block**: ×1.95 volume / ×1.5 range spike at 07:30 CT on all
  weekdays (§4) — the highest-frequency scheduled release anchor
  available without a consensus dataset.

## 7. CoT positioning — EURO FX, 2006-2026 [OBSERVED, `6E_a5_cot.json`]

- Coverage: 1,082 weeks (2006-01-03→2026-09-22), as-published
  no-revision, Tuesday as-of / Friday-15:30-ET release (PIT honored:
  forward descriptives start at obs+3 sessions; labels ex-post
  descriptive only).
- **History**: net non-commercial extremes at **−226,560 (2015-03-31)**
  and **+211,752 (2020-08-25)**; latest (2026-09-22) **−52,334 (9th
  percentile of the rolling-3y percentile incl. current week [ERRATUM
  MINOR-5: was labeled "strict-past 3y" — a5's rolling min/max window
  includes the current observation; a truly strict variant gives identical
  bucket means (6.52/7.68) and the same latest percentile (9.08)])** — EUR
  long-cover unwind into the 2026
  slide. Era means flip from +36k (2006-09) to −44k/−40k (2010-14 /
  2015-19 euro-debt/QE short eras) to **+62k/+72k (2020-22 / 2023-26
  long-bias eras)**; OI nearly quadrupled 173k→754k mean contracts.
- **2022 crisis path**: net started ~flat (−1.5k Jan-2022), slid to
  **−47.7k by 2022-08-30** (positioning capitulation at parity), then
  flipped to **+146k by year-end** — specs rode the collapse AND the
  0.95→1.09 rebound, while OI expanded 678k→773k (crisis = position
  growth, not exit).
- **Positioning extremes vs subsequent realized vol (2020-2026 overlap,
  n=347 weeks)**: crowded-long weeks (rolling 3y percentile incl. current
  week, ≥80, n=54) → next-21d ann vol mean 6.5%; crowded-short weeks (≤20, n=36) →
  **7.7%** (median 7.6% vs 6.4%); mid 7.0%. The crowded-short tail is
  vol-heavier — driven by Feb/Mar-2020 (short extreme → 16% forward
  vol) and 2026 samples [OBSERVED, descriptive; asymmetric-vol-after-
  positioning-squeeze mechanism POSTULATED]. No return conditioning run
  (NOT_RUN by law).
- CoT OI vs venue OI: **RETRACTED** — the previously reported "2.000×
  convention gap" was a publication-duplication artifact in a5's raw-row
  sum; deduped venue OI reconciles 1:1 with CFTC OI (§1 ERRATUM MAJOR-1).
  Cross-venue OI joins remain fine WITHOUT scale normalization provided
  publications are deduplicated per (contract, ref_date).

## 8. Hypothesis refinement vs v1 (specs refined, NO PnL evaluation)

**H1 (contract selection + roll timing) — PARAM-GAPs DISSOLVED, spec
tightened.** v1 proposed quarterly-only + expiry-week roll; measured
migration (Friday crossover, 27/27) and holiday-extended expiry rule
(80/80) now pin the calendar precisely. Refined spec: hold nearest HMUZ;
roll at the close of the **Friday of expiry week** (= the session 1
trading day before the Monday last-trade; equivalently last session of
the week containing the 2-business-days-before-3rd-Wednesday date, with
the full holiday set). Liquidity floor previously feared missing
(<10k sessions) — none exist (§5). Alternatives now measurable: volume
crossover k=5 (triggers ~expiry Monday+1, i.e., 1 session late vs
market), OI-crossover (leads volume by ~6 days per the a3 deduped table
but next-morning publication lag + deferred-book noise artifacts). **Floor:
n=27 rolls
measured; a sign/timing statement is now supported; selection A/B for
execution = NOT_RUN (needs registered cycle).**

**H2 (roll gap tracks USD−EUR differential) — sign result PIT-robust;
magnitude/correlation vintage-dependent [ERRATUM MAJOR-2 — downgraded
from "CONFIRMED descriptively"].** Latest-vintage basis: 27/27 sign
agreement, r=0.91 vs CIP prediction, median +91 ticks vs CIP ~85 ticks,
residual +6 ticks. PIT-as-of basis (on-disk ALFRED year-end vintages):
**sign 26/27, r=−0.107, residual +3.77 ticks** (§5). The H2 registration
spec MUST carry this quantified sensitivity, not a one-line vintage
caveat. Refined falsifiable
spec for the registered cycle: gap_ann(t) = α + β·(SOFR−€STR)(t) + ε;
invalidation |β−1|>0.35 or sign flip while differential > 150bp; plus a
mandatory vintage-robustness leg (real-time/vintage SOFR source decision
by the owner — the year-end-only ALFRED set on disk cannot settle it).
The 2025-2026 gap compression (+2.10%→+1.16% ann) as the differential
compressed is visible in the roll table [OBSERVED].

**H3 (post-FOMC persistence) — data-ready, still NOT_RUN by law.** All
58 FOMC events 2020-2026 are in-window at 1m with primary-source
timestamps; ×17 volume concentration at 13:00 CT measured. The v1
blocker (M1 depth + timestamps) is dissolved; the blocker now is purely
the task-class law (no conditional mean-return / selection in PREP) and
the absence of a PIT consensus archive for surprise conditioning.

**H4 (US-vs-EA surprise differential) — still PARAM-GAP** (consensus
archive absent; unchanged), but the ECB/US release-time anatomy (§6)
now provides the correct release-anchored windows for a future
registered design (07:15/08:15 CT ECB, 07:30 CT US, DST-correct).

**H5 (FX-spot corpus session transfer) — partially UNBLOCKED, transfer
still POSTULATED.** The London/NY overlap is now measurable in futures
(§4): overlap hours carry the volume peak and the London morning the
top per-session RV share; DST-mismatch weeks prove London-local
bucketing is required. But the corpus-1200 ideas themselves were never
provided to this lane; transfer differences remain: CIP basis/roll
(+0.8–2.2%/yr embedded drift measured), tick/commission granularity,
and quote-orientation equivalence (USD-per-EUR — same as spot EUR/USD
convention, no 6J-style inversion). Any corpus idea re-use must be
re-registered and re-measured on THIS data (v1 caveat stands).

**New measured facts that refine the framework's §15 priors**:
(i) ECB decision minutes are a ×1.7 volume event, NOT a ×17 FOMC-class
event — EUR/USD event asymmetry is real in the futures book; (ii) the
8:30 ET block is the most reliable daily anchor (×1.95 every weekday);
(iii) v1's 247-day window was 6.8th-percentile vol — all v1 magnitudes
shift up with the fuller distribution (daily std 0.463% vs 0.333%).

## 9. NOT_RUN register (explicit)

- Any conditional mean-return table, signal ranking, or PnL evaluation
  (task law — prep class).
- PIT consensus/surprise conditioning (no archive sourced).
- US 8:30-ET release-type decomposition (CPI/NFP/other) — no PIT US
  release calendar on disk.
- Spread-instrument (6Ex-6Ey) volume/microstructure quantification —
  rows counted, volumes not aggregated (candidate follow-up: roll-cost
  arbitrage between outright pairs and spread books).
- OI-based analyses before 2023-10 (statistics dataset start). ~~OI
  convention (2×) unresolved against CFTC definition~~ [RESOLVED by
  ERRATUM MAJOR-1: no convention difference exists — dedupe publication
  rows; a5's `cot_oi_vs_venue_oi` block is superseded].
- Cross-asset confirmation matrix (6B/6J/ES/DXY) — lane scope 6E.
- Definitions-dataset identity cross-check (2023-10+ only; bars +
  registry used instead).
- ECB GC dates beyond the 10 direct-verified: assembly-method FACT, not
  per-date machine verification (disclosure in §6).

## 10. Open questions carried to the registered cycle

1. Roll A/B at execution level: declared calendar vs Friday-of-expiry-
   week vs volume k=5 vs OI(+lag) — costs now measurable including the
   spread books (needs spread-instrument volume aggregation).
2. The +6-tick median CIP residual: hedging-flow premium vs
   stale-quote artifacts at 16:00 CT closes — testable with bbo-1m data
   (framework §10 phase-2).
3. Positioning-asymmetric vol (crowded shorts → higher fwd vol) on a
   3-currency FX panel (6B/6J lanes) — descriptive robustness before
   any conditional design.
4. Does the Wednesday control-day volume peak — **mode 13:59 CT (162 of
   ~340 control Wednesdays), secondary cluster 12:00–12:02 CT** [ERRATUM
   MINOR-4: was "12:00–12:07 CT"] (settlement/closing flow?) — interact
   with FOMC-week liquidity?
5. ~~Vendor OI 2× convention adjudication against CME-published OI~~
   **RESOLVED/RETRACTED by ERRATUM MAJOR-1** (A7-DEEP-6E adjudicated it
   from the delivered data: deduped GLBX stat_type-9 OI reconciles 1:1
   with CFTC legacy futures-only OI, 150/156 weeks within ±0.2%; residual
   weeks are just-expired-contract timing). Replacement item if desired:
   pin the GLBX statistics publication stamp (ts_event) timing for
   adapter PIT use.

---

## 11. ERRATA ledger (applied 2026-10-03, lane DOSSIER-ERRATA-V2; authority `audit/a7_6e/A7_DEEP_6E.md`, verdict PASS WITH ERRATA — 12/12 headline recomputes match, 5/5 ECB dates verified, 20/20 rate-change meetings machine-checked)

Applied in place above and marked `[ERRATUM …]` at each correction site;
nothing silently rewritten.

| id | severity | where | old → new | evidence |
|---|---|---|---|---|
| MAJOR-1 | MAJOR | §1 venue-OI bullet, §7 last bullet, §9 NOT_RUN register, §10 q5 | "GLBX venue OI = 2.000× CFTC OI (engine-critical double-counting convention); never mix / scale-normalize" → **RETRACTED as publication-duplication artifact**: stat_type 9 publishes 2 rows per (contract, ref_date) in 7,615 pairs (107×3, 8×4, 107×1); a5's raw-row sum doubled (3-publication days → "3.000×"); deduped-to-latest median ratio **1.0000** (150/156 weeks ±0.2%; 2024-06-04 venue 671,736 == CFTC 671,736); 3 residual weeks = just-expired-contract timing. a5-vs-a3 method inconsistency reconciled (a3 deduped all along; §5 crossover finding unaffected) | A7-6E MAJOR-1/§2 |
| MAJOR-2 | MAJOR | §5 CIP bullet, §8-H2 | "r = 0.91 … vintage caveat: not point-in-time" + H2 "CONFIRMED descriptively" → quantified sensitivity: latest-vintage r=0.9097/sign 27/27/residual +6.18t (reproduces) vs **PIT-as-of r=−0.107/sign 26/27/residual +3.77t** (ALFRED year-end vintages 2019…2024 + 2026-09-30; no 2025 vintage); H2 downgraded to "sign 26/27 PIT-robust, magnitude vintage-dependent"; H2 spec must carry the sensitivity + a real-time-SOFR source decision | A7-6E MAJOR-2/§3 |
| MINOR-3a | MINOR | §3 chain n | "n=1,751" → **1,746 sessions / 1,745 returns** | A7-6E MINOR-3(a) |
| MINOR-3b | MINOR | §3 rolling-63 min date | "2026-01-14" → **2026-01-16** | A7-6E MINOR-3(b) |
| MINOR-3c | MINOR | §3 v1-window percentiles | "rolling p05 5.65" → **5.66** | A7-6E MINOR-3(c) |
| MINOR-3d | MINOR | §4 quiet hours | "~01:00 CT (1.0%) and 18:00 CT (1.0%)" → **17:00–18:00 CT (1.004%) and 23:00–24:00 CT (1.015%)**; 01:00 CT carries 3.99% (session-hour labels h−07/h−01 misread as clock times) | A7-6E MINOR-3(d) |
| MINOR-4 | MINOR | §6 + §10 q4 | control-Wednesday peak "12:00–12:07 CT" → **mode 13:59 CT (162 of ~340); 12:00–12:02 secondary (26)**; midday-flow narrative re-attributed to the secondary cluster; FOMC ×17.2 unaffected | A7-6E MINOR-4 |
| MINOR-5 | MINOR | §7 labels | "strict-past 3y percentile" → **"rolling 3y percentile incl. current week"** (strict variant: identical bucket means 6.52/7.68, same latest pct 9.08) | A7-6E MINOR-5 |
| NOTE-6 | NOTE (disclosed) | §6 | 14:45 CET press-conference FACT rests solely on the lane's 2026-10-02 fetch (ECB index page silent on it); 14:15 CET decision FACT re-verified verbatim | A7-6E NOTE 6 |
| NOTE-7 | NOTE (disclosed) | header | "→2026-09-30" includes one final partial session dated 2026-10-01 (Tue 2026-09-30 17:00+ CT evening); 1,746 sessions either way | A7-6E NOTE 7 |

Out-of-dossier item flagged for the owner (NOT edited by this lane): `analysis/6E_a5_cot.json` block `cot_oi_vs_venue_oi` (median_ratio 2.0003) is superseded by MAJOR-1 — regenerate with publication dedupe when the a5 script is next run; the JSON as shipped still carries the artifact numbers with the ratio computed raw-sum.

— End of ERRATA ledger.
