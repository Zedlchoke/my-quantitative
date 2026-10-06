# NQ_DEEP_v2 — E-mini Nasdaq-100 futures: 16-year deep descriptive dossier

- **Task:** FUTURES-DEEPRESEARCH-V2-20261003, lane DEEP-NQ (prep-class deep research; NOT a scored cycle)
- **Worktree:** `/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/prep` @ `26d96eb4`, branch `prep/futures-behavior-10syms-20261002`
- **Generated (UTC):** 2026-10-03
- **Mission:** the deepest honest descriptive study of NQ structure/behavior the 16-year vendor dataset allows; supersedes the depth-starved v1 dossier (`FUTURES-BEHAVIOR-10SYMS-PREP-20261002/dossiers/NQ_DOSSIER.md`, whose true-volume window was 14-16 months).
- **Claims taxonomy (every tagged claim):** FACT (primary official source + location) / OBSERVED (script + window on this data) / POSTULATED (mechanism reasoning, unmeasured) / NOT_RUN (default; missing evidence is never PASS).
- **Laws honored:** no PnL evaluation, no conditional mean-return signal tables, no ranking/selection of strategies; thresholds strict-past/rolling; ex-post labels descriptive only; raw vendor data read-only.
- **ERRATA applied 2026-10-03** (lane DOSSIER-ERRATA-V2, from the independent audit `audit/a7_nq/A7_DEEP_NQ.md`, verdict PASS_WITH_ERRATA): **F1** the "2020 vendor hole" is RECLASSIFIED as a vendor SYMBOLOGY ALIAS (data present and recoverable at $0); **F2** §5 CoT source re-pointed to the `__ALT__` Consolidated series — every §5 number unchanged; **F3** §1 "16.9% (volume rule)" corrected to 20.1% (comparison direction reverses); **F4** ACF/VR prose refreshed to delivered-artifact values; **F5** FOMC provenance counts corrected (132/92/85); **F6** window typo + Friday-close count fixed. Full old→new ledger in §10.

**Inputs (all under `research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/` unless noted):**

| artifact | role |
|---|---|
| `NQ_deep_lib.py` | loaders + session/segment/contract-identity logic (era-aware, DST-correct) |
| `NQ_build_cache.py` → `NQ_cache/` | outright 1m panel, contract registry (111 clusters incl. 4 strays), per-(contract,session) table, PIT held-contract maps |
| `NQ_a1_regimes.py` → `NQ_a1_regimes.json` | regime map |
| `NQ_a2_sessions.py` → `NQ_a2_sessions.json` | session/intraday structure |
| `NQ_a3_term.py` → `NQ_a3_term.json` | term structure + roll |
| `NQ_a4_events.py` → `NQ_a4_events.json` | FOMC event anatomy |
| `NQ_a5_cot.py` → `NQ_a5_cot.json` | CoT positioning |
| `NQ_a7_quality.py` → `NQ_a7_quality.json` | data-quality ledger |
| vendor data (read-only) | `~/.my-quantitative-data/futures-databento-av1trim/parquet/` NQ ohlcv-1m 2010-06-06→2026-09-30 (AV1R delta 2010-2023 + AV1T 2023-2026), GLBX statistics 2023-10+, definitions 2023-10+ |
| nonprice (read-only) | `~/.my-quantitative-data/futures-nonprice-10syms/`: CFTC legacy CoT as-published, Fed FOMC statements 2011-2026 (147 archived HTML), FRED latest CSVs, ALFRED annual vintage snapshots |

**Held-contract construction (used by A1/A2/A4; no vendor stitching anywhere).**
OBSERVED panel: 6,688,533 outright ohlcv-1m bars (calendar-spread instruments excluded: 641,787 spread rows dropped from 7,330,320 parent rows), 2010-06-06 22:00Z → 2026-09-30 23:59Z; 4,219 held sessions 2010-06-07 → 2026-10-01. Primary rule = **PIT volume-crossover k=5**: at each session close t, trailing-5-session mean volume of the next quarterly vs current; switch decided on data through t, new contract held from t+1 (66 rolls). v1's declared calendar rule retained as sensitivity (§3 shows why it is unfit). The held series is **hole-aware**: the 2020 alias-window sessions carry NaN closes, never synthetic jump returns (§7; reclassified by ERRATUM F1 in §10).

---

## 1. Regime map 2010-2026 (A1)

All OBSERVED (script `NQ_a1_regimes.py`, window 2010-06-07..2026-10-01, held-contract daily log returns; hole sessions NaN; min_periods 75% of window).

**Realized volatility, multi-horizon (annualized, trailing windows).**

| horizon | min | p5 | p25 | median | p75 | p95 | max (date) |
|---|---|---|---|---|---|---|---|
| 5d | — | — | — | — | — | — | see JSON |
| 20d | 4.5% | 7.9% | 12.0% | **16.1%** | 22.1% | 33.5% | 92.4% (2020-03-27) |
| 60d | 6.4% | 9.9% | 13.6% | **16.7%** | 21.9% | 33.2% | 57.1% (2020-04-13) |

(rvol20 minimum 4.5% at 2016-09-02.) Vol clustering: rolling-252d ACF(1) of |ret| median 0.168 — daily vol persistence is modest; the vol regime itself mean-reverts (2022 94% of sessions in high-vol tercile → 2023-2024 ~0-5%).

**Trend persistence (descriptive; not a signal).** Variance ratios (252d rolling variance basis): VR(5)=0.81, VR(20)=0.71, VR(60)=0.67 — q-day variance is materially BELOW q×1-day variance at all measured horizons: **multi-day mean reversion, not momentum, dominates NQ daily returns across the full era** (VR(20) 10-90p range 0.522-0.85 [ERRATUM F4]). ACF(1) of returns: full-era -0.076; rolling-252d median -0.042 (p10-p90 -0.134..+0.071) [ERRATUM F4: stale pre-DST-fix prose corrected to the delivered JSON values]. OBSERVED. This resolves v1's deliberately-unmeasured "trend behavior" cell and *cautions against* naive multi-day momentum designs on daily NQ.

**Drawdown anatomy (≥10% episodes, top 8).**

| start | trough | end | depth | fall (sess) | recovery (sess) |
|---|---|---|---|---|---|
| 2022-01-20 | 2022-11-03 | 2023-12-13 | **-43.6%** | 204 | 289 |
| 2020-02-27 | 2020-03-16 | 2020-06-05 | -32.3% | **12** | 58* |
| 2018-10-24 | 2018-12-24 | 2019-04-17 | -26.5% | 44 | 80 |
| 2025-03-10 | 2025-04-08 | 2025-06-24 | -25.5% | 21 | 54 |
| 2016-01-08 | 2016-02-09 | 2016-07-28 | -17.9% | 22 | 121 |
| 2011-08-05 | 2011-08-08 | 2012-01-19 | -17.4% | 1 | 117 |
| 2024-07-30 | 2024-08-07 | 2024-11-06 | -15.7% | 6 | 66 |
| 2015-08-21 | 2015-08-24 | 2015-11-02 | -15.5% | 1 | 51 |

*COVID recovery spans the 2020 vendor hole (§7). OBSERVED.

**Year-by-year (selected; full table in JSON).** 2020: +13.2% (hole-adjusted sum of log rets; sessions with data), vol 33.5% ann, worst day -11.15% (2020-03-16, real), best +8.85%, DD -32.3%. 2022: **-39.1%**, vol 31.9%, DD -43.0%, worst -5.83%. 2023: +43.2%, vol 17.7%. 2024: +22.2%, vol 18.2%. 2025: +18.1%, vol 23.2%, DD -25.5% (Apr-2025), skew +1.12, ex-kurt 16.2 (one +11.6% day, 2025-04-09 cohort). 2026 YTD (to 09-30): +19.2%, vol 20.8%, high-vol-tercile share 67%. Average daily held-contract volume: 215-278k (2010-2014) → 415-536k (2018-2020) → peak 634k (2022), ~527-596k (2023-2026) — a doubling over the era.

**Strict-past regime labels (ex-post descriptive labels; thresholds trailing-only).**
- Vol terciles vs own trailing-756d distribution: high-vol sessions concentrate in 2011 (50), 2015-16, 2018-20, 2022 (231), 2025-26; 2013, 2017, 2023-24 are almost entirely low/med. Counts: low 1,355 / med 1,066 / high 1,454.
- Trend label (|t|>1 on trailing-120d drift): range 2,549 / trend-up 1,555 / trend-down 64 sessions. Trend-down label appears almost only in 2022 (56 of 64). OBSERVED.

**v1's single-regime caveat — now resolved (the core v1→v2 upgrade).**
v1's W2 (2025-05-30..2026-10-01, 332 returns) rvol20 median 17.1% sits at the **57th percentile** of the 2010-2024 distribution (whose p10-p90 is 9.1%-28.9%); its observed range 7.8%-35.2%; its max drawdown 12.8% vs the era's 43.6%. **OBSERVED conclusion: v1 sampled a neutral, mid-distribution volatility regime and structurally could not see the era's tails; its W1/W2 vol/skew/kurtosis figures are representative of "normal NQ", not of NQ's crisis behavior.** Any strategy validation performed on 2025-26 data alone is a mid-regime test (this is the honest scope statement v1 lacked the data to make).

**Calendar-rule sensitivity (v1's roll rule).** Rebuilding the same daily series under v1's declared calendar rule: 4,155 sessions, ann vol 19.6% vs **20.1%** (volume rule; n=4,168 returns on the delivered hole-aware series) [ERRATUM F3: the pre-audit text read "16.9%" and claimed the calendar rule "inflates vol" — that figure is not reproducible from the delivered cache by any variant (excl-2020, excl-hole-adjacent, clean-only, ddof=0), appears to be a stale pre-DST-fix number, and the stated comparison direction reverses on current artifacts (19.6% < 20.1%)]. The calendar rule's unfitness rests on §3's measured thinness (1.4% of market-front volume), NOT on this vol comparison. OBSERVED.

---

## 2. Session / intraday structure, full era (A2)

All OBSERVED (`NQ_a2_sessions.py`; held-contract clean sessions only — RTH-core coverage ≥0.6, n=4,016 of 4,170; DST-correct America/Chicago; segments clock-based; era-aware close: **measured schedule changes**: Mon-Thu close 16:15 CT through 2015-09-18 → 16:00 CT from 2015-09-21; **Friday close 15:15 CT through 2012-10** (last full month; mixed Nov-2012; none from Dec-2012)).

**The overnight/Globex share v1 could not see (IBKR RTH-only).** Share of total session volume traded in the full overnight (17:00→08:30 CT): **2010: 10.2% → 2016: 15.8% → 2019: 22.5% → 2023-26: 19-24% (2026: 23.8%)**. The Globex session roughly DOUBLED its weight over the era, with a level-shift around 2018-2019. Consequences: (a) any RTH-only execution design now leaves ~1/5 of daily volume and its information flow unmodeled; (b) v1's session claims were ~80%-complete-era-typical for RTH shape but blind to this level shift.

**RTH internal shape (stable across eras — U-shape is an invariant so far).** First 30 min (08:30-09:00 CT) = **16.2% (2010-12) / 17.2% (2013-16) / 17.1% (2017-20) / 16.0% (2020-22) / 15.6% (2023-26) of RTH volume** — v1's 16.5% estimate was typical, not special. Hourly RTH shares (2010-12 vs 2023-26): 09:00-10:00 18.1%→16.4% (peak), 11:00-12:00 8.7%→8.7%, 12:00-13:00 7.7%→8.0% (trough), 14:00-15:00 14.5%→11.5% (secondary), 15:00-16:00 3.8%→3.1%. Per-minute |1m log ret| at 08:30 = 2.1-2.6× the 12:00 lunch trough (2.29× / 2.11× / 2.55× in the three big eras). OBSERVED.

**The 07:30 CT (08:30 ET) macro-release slot.** Calendar-free evidence (minute-volume share vs neighbors): 2023-26 era share at 07:30 = 0.185% vs 0.041% at 07:25 and 0.089% at 07:35 — a 2-4× minute-volume spike at exactly the CPI/NFP release time, with |1m ret| (0.077%) approaching the cash-open minute (0.086%). In the quiet 2017-20 era the same slot showed no such spike (0.088% share, |ret| 0.031%). OBSERVED — macro-morning concentration is a recent-era feature, consistent with the macro-vol regime, not a fixed microstructure constant.

**Holiday-shorted days.** 119 inferred short sessions (last trade ≥45 min before scheduled close, coverage otherwise real; method disclosed, not exchange-asserted): Thanksgiving/Black Friday, Dec 24, MLK/Presidents-Day-adjacent, Jul 3 etc., ~3-10/year growing over time (CME added early closes). Volume on those days = 16.8% of same-year median. Separately: 126 era-A Friday-early-close sessions (15:15 CT Fridays 2010-06→2012-11) [ERRATUM F6: was "123"; `NQ_a2_sessions.json` says 126]. OBSERVED.

**FIX/FAST caveat (carried from dispatch):** pre-2017 GLBX data originates from the legacy feed conventions; cross-era LEVEL comparisons of per-minute volume are tagged with this caveat (shape comparisons above are ratio-based to mitigate).

---

## 3. Term structure + roll (A3)

All OBSERVED (`NQ_a3_term.py`; per-contract session closes, adjacent-quarter spreads, 66 roll events under the PIT k=5 volume rule).

**The calendar curve is a rate-era animal — the sign FLIPS across the 16 years.** Median adjacent-quarter spread on liquid observations, annualized (new-over-old ÷ price × 365/91):

| era | ann. premium | era | ann. premium |
|---|---|---|---|
| 2010 | -0.40% | 2018 | +1.50% |
| 2011 | -0.63% | 2019 | +1.23% |
| 2012 | -0.83% | 2020 | -0.46% |
| 2013 | -0.75% | 2021 | -0.26% |
| 2014 | -0.71% | 2022 | +1.13% |
| 2015 | -0.65% | 2023 | **+5.00%** |
| 2016 | -0.33% | 2024 | **+4.99%** |
| 2017 | +0.53% | 2025 | +4.09%, 2026: +3.81% |

v1 saw only 2025-26 (~4%/yr premium) and POSTULATED "financing minus dividends"; the full curve shows the premium was NEGATIVE for most of 2010-2021 (ZIRP: dividends ≥ financing) and only became large-positive in the 2022+ rate regime. The financing-minus-dividend mechanism now has 16 years of sign/level variation consistent with it (still POSTULATED — not decomposed against rate/dividend data).

**Roll mechanics (66 rolls).** Roll-day gap (new close − old close): median −0.8 pts, p10 −8.5, p90 +238.9, min −14.0 (2015), max +302 (2024); 49.2% of rolls positive. Corr(roll-day gap, trailing-10-session spread level) = **0.999** — the roll gap IS the calendar spread (no independent roll noise). **What an unadjusted chain would embed per year (sum of gaps a holder realizes):** 2010-2016: −5 to −31 pts/yr (index 1.8-5k); 2018-2019: +95 to +110 pts; **2023: +723, 2024: +1,014, 2025: +907, 2026 YTD: +810 pts/yr (~4-5% of price per year)** — an unadjusted NQ "price series" is dominated by this drift in the modern era; any backtest on unadjusted chains would manufacture a ~4%/yr phantom trend (2023-26) that was ~−0.5%/yr in 2011-2016. OBSERVED; this is the single largest back-adjustment hazard the deep data exposes.

**Liquidity migration across rolls.** New-contract share of two-contract volume around the k=5 roll session: D−5 2%, D−4 8%, D−3 42%, D−2 71%, D−1 81%, D0 87%, D+2 98%, D+3 ~100% (n=66, mean path in JSON). **Daily-volume crossover (persistent, new>old for 3 consecutive sessions) occurs median 7 days before the old contract's 3rd-Friday expiry (p10 4, p90 7, min 3, max 7; n=62 valid)** — the market handoff completes in the week BEFORE expiry week, essentially never inside DTE<3. OBSERVED. (k=5 smoothing rolls ~2-3 sessions later than the daily crossover; both disclosed.)

**OI crossover (GLBX statistics, 2023-10+ only, 12 roll pairs, publication lag next-morning disclosed).** OI(new) > OI(old) precedes the volume-crossover roll session by 2-3 days in the 8 artifact-free events (range −3..−2). Small n; tag OBSERVED-2023+, not era-general.

**The v1 calendar roll rule is quantitatively unfit (v1 caveat → v2 measurement).** On the first 10 sessions of each calendar-rule hold window (n=650 sessions 2010-2026): held-contract volume = **median 1.4% of the market front's volume** (p10 0.3%); 78% of those sessions below 50%. The v1 rule holds near-dead contracts for ~2 weeks per quarter; the PIT volume rule (or the measured market convention, daily-crossover DTE≈7) is the only defensible baseline. OBSERVED.

---

## 4. Event-day anatomy (A4) — descriptive, PIT-honest

All OBSERVED (`NQ_a4_events.py`; held-contract 1m bars; control = same weekday ±21d, non-event, clean sessions; **volume / |1m ret| / range only — no conditional mean-return tables by law**).

**FOMC day-level (147 archived files = 132 `a`-statements + 15 `b`/`c` implementation-note files; the analysis ingests the 132 statements, 2011-01-26→2026-09-16, federalreserve.gov HTML archived under `nonprice/fed/statements/`; 128 matched to clean sessions).** [ERRATUM F5: was "147 archived statements".] FOMC sessions vs control: session volume ×1.06 (median ratio), RTH volume ×1.11, true range ×1.12; 60% of days above-control volume, 62% above-control range.

**Release-window anatomy (only the 92 statements whose own HTML carries "For release at H:MM p.m. E[SD]T" — a primary-source release-time proof; 84 clean 2:00 p.m. ET events 2016-2026; 85 of 92 are 2pm, specials listed below).** [ERRATUM F5: was "106 statements … 98 of 106" — 106 counts all 147 files (92 `a`-statements + 14 `b`/`c` notes carrying clock text), not statements.] Release = 13:00 CT.

| window (rel. to 14:00 ET) | volume ratio | |1m ret| ratio | range ratio |
|---|---|---|---|
| −120..−60 min | 0.80 | 0.85 | 0.84 |
| −60..0 min | **0.68** | 0.85 | 0.84 |
| 0..+30 min | **2.26** | 2.28 | 2.62 |
| +30..+60 min | **2.64** | 2.54 | 2.80 |
| +60..+120 min | 1.44 | 1.66 | 1.75 |
| +120..+180 min | 1.34 | 1.48 | 1.60 |
| release minute itself | ×3.5 volume | — | — |

The **pre-FOMC lull** (hour before release at 0.68× control volume) and the **release-hour burst** (2.3-2.8×, peaking in the second 30 minutes, decaying over the following 2 hours but never below control) are the anatomy. Era shifts (2016-19 vs 2023-26): the lull deepened (0.80→0.59×) and the volume spike diluted (2.99→1.46×) while the **information ratio (|1m ret| ×) stayed stable at 2.2-2.4×** — the same news, spread over a market whose volume is now distributed differently (bigger OVN share, §2). OBSERVED.

Special-time statements (release-time proofs, listed for the record; NOT aggregated): 2019-10-11 11:00, 2020-03-03 10:00, 2020-03-15 17:00 (Sunday emergency cut), 2020-03-23 08:00, 2020-03-31 08:30, 2020-08-27 09:10, 2025-08-22 10:00 ET, plus others in JSON.

**CPI / NFP: NOT_RUN.** No historical CPI/NFP release calendar exists in the nonprice tree (`bls_gate/` empty; FRED series carry `released_at=null`); fabricating dates from memory is forbidden. The only calendar-free evidence is §2's 07:30 CT minute spike. Acquiring the BLS schedule archive is the single cheapest unlock for completing this section.

---

## 5. Positioning — CFTC CoT as-published (A5)

**Data discipline first (OBSERVED; [ERRATUM F2 — source pointer corrected, numbers unchanged]):** the analysis line is the NASDAQ-100 **Consolidated** market (850 weekly rows, 2010-06-15→2026-09-22). After the 2026-10-03 INTEGRATION-FIX-V2 exact-name fix to `cftc_normalize.py`, that line lives in `cftc_legacy_tidy.parquet` as its own series id `COT_LEGACY_NQ__ALT__NASDAQ_100_CONSOLIDATED_CHICAGO_MERCANTILE_EXCHANGE`, while canonical `COT_LEGACY_NQ` is now the single E-mini NASDAQ-100 line (1,082 rows, 2006-01-2026). Pre-fix, all three lines (Consolidated + "Micro E-mini NASDAQ-100", 306 rows, 2020-08+ + "Nasdaq Mini", 242 rows, 2022-02+) sat mixed under `COT_LEGACY_NQ` on duplicate dates, and A5 isolated the Consolidated line with a local `startswith("NASDAQ-100 Consolidated")` filter — i.e. the same 850 rows either way. **Every §5 number was re-verified unchanged on the fixed tidy (A7-NQ r5, exact reproduction).** The `NQ_a5_cot.py` loader was re-pointed to the `__ALT__` id by lane DOSSIER-ERRATA-V2 (as written it selected ZERO rows on the fixed tidy — a silent-empty re-run hazard). Vintage = as-published, unrevised; positions as-of Tuesday, released Friday 15:30 ET (FACT, cftc.gov schedule; manifest_sources.json). Forward windows start after the release (release-honest alignment). **TFF/disaggregated: NOT_RUN — the normalized TFF table carries position values that are 100% null (metadata only) and the annual compressed archives are classification-backcast, not vintage-stable (documented vendor caveat).** Owner decision-record addendum (A7-NQ r5 part C): restated on the canonical E-mini line, the §5 headline conclusion still holds (extreme-short 18.39% vs mid 17.13% fwd-10 vol — still the max bucket; same era sign-flip), but context numbers differ materially (OI 359k 2010 → 284k 2026 vs consolidated 95k → 302k; net-noncomm %OI 6.8% → 3.1% vs 8.7% → 2.0%).

**Descriptive result (strict-past trailing-3y percentile of net non-commercial position → forward 10-session outcomes, ex-post descriptive labels).**

| bucket | n | fwd 10-session realized vol (ann, median) | fwd Σ|ret| (median) |
|---|---|---|---|
| extreme short (pct<10) | 105 | **18.5%** | 9.2% |
| low 10-40 | 195 | 14.0% | 7.0% |
| mid 40-60 | 123 | 15.3% | 7.6% |
| high 60-90 | 170 | 15.5% | 7.2% |
| extreme long (pct≥90) | 91 | 15.3% | 7.5% |

Forward 10-session max-drawdown medians: extreme-short −2.3%, mid −2.4%, extreme-long −1.9%. **Era stability: the extreme-vs-mid vol gap flips sign across eras** (2013-16: 14.4% vs 14.9%; 2017-20: 17.0% vs 14.4%; 2021-26: 17.2% vs 19.4%). **Honest conclusion: on the legacy net-noncommercial series there is NO stable descriptive association between positioning extremes and subsequent NQ volatility/drawdowns** — the only persistent cell is extreme-SHORT positioning preceding somewhat higher forward vol (18.5% vs 15.3% mid), driven by the 2015/2018/2020 stress episodes. No return-signaling claim is made or implied. NOT_RUN: direction-conditional tables (prohibited), TFF dealer/asset-manager splits (values missing).

**Context series (OBSERVED):** consolidated OI median 95k (2010) → 77k (2014) → 49k (2018) → **302k (2026)** — the line's composition changed when Micro E-mini (2019+) entered the consolidated aggregate; cross-era OI level comparisons carry this caveat. Net-noncomm as % of OI: 8.7% (2010) → 2.0% (2026). Extreme-long episodes cluster in 2016-2017; extreme-short episodes in 2016/2018 (top-5 lists in JSON).

---

## 6. Hypothesis refinement — v1 §5 H1..H5 revisited (A6)

No PnL evaluation has been run for any hypothesis (law). Status changes vs v1:

**H1 real-yield shock → NQ underperforms ES.** v1 FLOOR "needs ≥2y vendor history": **DISSOLVED — NQ 16.3y per-contract data in hand; ES delta exists in the same acquisition (AV1R-O1M-ES-DELTA 2010-2023 + 2023-26)** (cross-symbol execution is DEEP-ES lane's to verify). Rate data: DFII10 latest covers 2003→2026-09-30 (OBSERVED, file) but is the REVISED vintage (`latest_revised_NOT_PIT`); ALFRED annual snapshots (2010-2026) exist for revision-sensitivity checks; **full daily-vintage PIT real-yield series: NOT_RUN (missing)**. Refined spec (unchanged mechanics, now testable window): entry next RTH open after a trailing-252d 90th-percentile DFII10 1-day change; exit 5 sessions; NQ−ES relative; year-by-year sign stability + 1.5× cost stress; invalidation if the effect lives only in 2022-2026 (the only high-premium era, §3 — a regime-concentration failure mode now visible and mandatory to test).

**H2 CoT extremes → conditional vol/asymmetry.** v1 called it "cheapest fully-PIT-testable". **Downgraded by evidence:** the descriptive precondition (stable distributional difference) is NOT met on legacy net-noncomm (§5: gap flips sign across eras; only extreme-short shows a mild persistent vol elevation). Refined specification if still pursued: restrict to the extreme-SHORT cell; outcome = forward 10-session realized vol (not returns); invalidation = the 18.5%-vs-15.3% gap vanishes outside 2015/2018/2020 stress windows. TFF-based variants remain NOT_RUN (values null). PARAM-GAP unchanged (percentile + holding period must be pre-registered).

**H3 macro surprise × rate response.** Still **BLOCKED on consensus archive** (nothing acquired; BLS gate empty). New since v1: FOMC-side release-time proofs (92 primary-source statement timestamps [ERRATUM F5: was 106]) now exist, so the FOMC leg of the event framework is fully timestamped; CPI/NFP legs remain NOT_RUN without calendars. Deep-intraday release-window fills are now measurable (16y of 1m Globex) once surprises exist.

**H4 overnight→RTH continuation.** v1 was BLOCKED on Globex data; **the data floor is now EXCEEDED (16.3y full-session 1m incl. all Globex segments, DST-correct)**. The evaluation itself remains **NOT_RUN (return-conditioned; prep-prohibited)**. Refined pre-registered spec: overnight move = 17:00→08:30 CT log return; condition = trailing-252d 80th percentile of |overnight| (strict past); entry 08:30 CT next session, exit 16:00 CT; mandatory 30-min delayed-entry variant; counter-hypothesis from §1's VR(20)<1 evidence — overnight-extension may be exactly the mean-reverting component (test both tails); failure condition: continuation sign unstable across the §2 OVN-share eras (10%→24% overnight weight is a participation-regime shift, not noise).

**H5 roll-window/term-structure effects.** v1 was BLOCKED on ≥2y real-volume curve: **DISSOLVED and largely REPLACED by measurement (§3)**: curve level measured 16y, roll gaps ≈ curve (corr 0.999), migration S-curve measured, unadjusted-chain embedding quantified (+4-5%/yr phantom drift 2023-26). Remaining NOT_RUN: spread-change vs rate-reprint event alignment (needs PIT rates), and any tradable spread rule (prep-prohibited). New hypothesis generated by the data (POSTULATED, untested): calendar-premium LEVEL as a rate-expectation proxy — its 2023-24 →2025-26 decline (+5.0%→+3.8-4.1%) coincides with the easing cycle; a falsifiable spec is drafted in JSON-adjacent notes but NOT evaluated.

**New NOT_RUN inventory (blocking a registered cycle):** consensus archive (H3), daily-vintage PIT yields (H1 strict form), synchronous BBO quotes (all execution-cost work), TFF position values (H2 variant), CPI/NFP calendars (event completion), 2020 alias-window re-measurement (§7 ERRATUM F1: data present; aggregates must be recomputed at $0 before any registered cycle).

---

## 7. Data-quality ledger (A7)

All OBSERVED (`NQ_a7_quality.py` + build diagnostics, window 2010-06-06→2026-09-30).

**Panel integrity.** 6,688,533 outright 1m bars; duplicates (symbol,minute): **0**; non-monotonic contract streams: **0**; negative prices: 0; high<low: 0; close outside [low,high]: 0; zero-volume bars: 0; price range 1,699.25 → 31,454.75 pts. Parent-symbol rows included 641,787 calendar-spread bars (excluded from all analysis; disclosed). One-digit-year symbol epochs resolved by time-cluster matching (111 clusters; e.g. NQZ0 = Dec-2010 and Dec-2020); 4 stray single-print clusters excluded (NQZ6 2023-10-25, NQZ7 2025-05-30, NQZ7 2025-09-15, NQZ9 2025-02-14 — deferred-year prints outside any live contract window).

**DST correctness (evidence, not assumption).** Modal UTC hour of the 17:00 CT session open flips 22Z↔23Z in **32 of 32 expected March/November transitions 2010-2026, zero unexpected flips**. A fall-back session-date arithmetic bug (timedelta vs wall-clock day) was found and fixed during this study (35 affected Sunday-evening clusters); disclosure: the fix is in `NQ_deep_lib.py` (Day offset), caches rebuilt, A1/A2 re-run post-fix.

**THE 2020 "VENDOR HOLE" — RECLASSIFIED as vendor SYMBOLOGY ALIAS [ERRATUM F1, MAJOR; evidence A7-DEEP-NQ F1 + INTEGRATION-FIX-V2 probe `analysis/integration/nq2020_hole_probe.*`, adjudication `A_ALIAS_NOT_ABSENCE`, verified against the raw delivered parquet].** What the pre-audit text called a 10-week front-contract absence is a dash-symbol ALIAS invisible to the dash-excluding outright filter: `instrument_id 16908` carries raw_symbol `NQU8-NQM9` for 2018-08-15→2020-05-31 (92,075 bars, 24,686,121 contracts) and `NQM0` for 2020-06-01→06-19 (19,406 bars, 5,159,596; last bar 2020-06-19 13:29Z, the Jun-19 expiry week). Through the alleged hole (2020-03-23..05-29) id 16908 printed **58 trading dates, 0 weekday gaps except Good Friday 2020-04-10, 21,824,572 contracts — 625,650 on Mar-23 alone (daily range 6,838..690,803)**. Delivered-window reconciliation (2020-03-01..06-30, both chunks): 169,992 rows total == the live-vendor parent quote; 100,034 on id 16908 (80,628 alias + 19,406 relabeled) == the live-vendor `NQM0` quote; per-symbol counts NQH0 17,932 / NQU0 30,204 / NQZ0 971 all match. `NQU8-NQM9` is the only dash symbol with lifetime volume > 5M (24.7M; next 0.97M). **Recovery rule (deterministic, $0): view `instrument_id==16908 AND date<2020-06-01 → 'NQM0'`.** Two supporting-narrative corrections: (i) "front degrades from 2020-03-16 (505k→85k by 03-19)" — that fade was **NQH0 expiring 2020-03-20**; the true front (id 16908) traded 350,956 / 478,420 / 475,836 / 478,254 / 540,580 contracts on 03-16..03-20 — no degradation; (ii) "only the deferred NQU0 trickle (~100-1,200 contracts/day) prints" — under the alias view the actual front printed 6.8k-690k contracts/day through the window. **Consequences:** handling stays as-is (hole-window sessions carry NaN closes; no synthetic jumps) and all §1/§2/§3 numbers computed on the NaN series remain internally valid *as computed*; but the 2020 aggregates (e.g. "+13.2%", "worst day −11.15%", "2020 ann-vol 33.5% is a lower bound") are recomputable at $0 and MUST be re-measured before any registered cycle uses them. The pre-audit recommendation to backfill this window is CANCELLED (§9).

**Session-era changes (measured schedule facts, not assumptions).** (i) Mon-Thu close 16:15 CT through 2015-09-18; (ii) all-days close 16:00 CT from 2015-09-21; (iii) Friday close 15:15 CT through 2012-10, abolished Nov/Dec-2012; (iv) maintenance-break stragglers: 5,266 bars inside the (era-correct) break window 2010-2015 — median 4 lots, ~10 bars/session, predominantly deferred contracts (negligible; excluded from session aggregates); era-B violations: 37 bars total.

**Per-era densities.** Yearly bars 204k (2010 partial) → 466k (2024); clean held sessions/year 145 (2010 partial) → 247-251 typical; 2020 = 202 clean sessions (hole); 2026 = 187 (through Sep). Holiday shorts: 119 inferred (method disclosed, exchange-calendar NOT_RUN).

**Coverage statement per analysis (the window each claim rests on).** A1: 4,219 sessions (NaN-aware), drawdowns incl. hole-flagged COVID episode. A2: 4,016 clean sessions; era tables 643-931 sessions each. A3: 66 rolls (62 valid for daily-crossover DTE), spread levels 2010-2026 with liquidity filter (deferred leg ≥500 contracts). A4: FOMC 2011-2026 day-level (128), release-window 2016-2026 (84 events). A5: 850 weekly CoT obs on the consolidated line only. Statistics-based OI: 2023-10+ only.

---

## 8. What upgraded vs v1 — summary

| v1 limitation | v2 resolution |
|---|---|
| 14-16 months true volume; single-regime caveat | 16.3 years; v1 window placed at 57th pct of era vol (neutral regime, never saw 43.6% DD / 92% rvol) |
| Trend behavior NOT_RUN | VR(5/20/60)=0.81/0.71/0.67 — multi-day mean reversion measured |
| Overnight NOT_RUN (RTH-only IBKR) | OVN share 10.2%→23.8% measured; release-slot 07:30 CT spike measured |
| Curve ≈ 1 year, premium "≈ financing−dividends" guess | 16y curve with SIGN FLIPS (−0.8%/yr ZIRP eras → +5.0% 2023-24); unadjusted-chain phantom drift quantified (+1,014 pts in 2024) |
| Roll handoff NOT observable (data cut at declared roll) | 66 rolls: daily-crossover DTE median 7 days; migration S-curve; v1 calendar rule measured at 1.4% of market-front volume — unfit |
| Event behavior NOT_RUN | FOMC anatomy measured (lull 0.68×, burst 2.3-2.8×, era-stable information ratio); CPI/NFP still NOT_RUN (calendars) |
| CoT not acquired | 850-week as-published series analyzed; extreme-positioning→vol link found UNSTABLE (honest null) |
| Data quality undocumented | Full ledger incl. the 2020 hole, DST proof, schedule-era changes, integrity checks |

## 9. Remaining NOT_RUNs (priority order for the owner)

1. ~~2020-03-20..2026-05-29 NQ front backfill~~ **CANCELLED by ERRATUM F1** (the window end typo "2026-05-29" is also corrected to 2020-05-29 — ERRATUM F6): the 2020 window is NOT absent — it sits under the `instrument_id 16908` symbology alias and is recoverable at $0 via the view rule in §7 (the recorded vendor backfill quote of $0.62 was NOT executed). Replacement top priority: **re-measure all 2020 aggregates (yearly return/vol/DD, rvol windows spanning Mar-May 2020) on the alias-recovered series before any registered cycle.**
2. CPI/NFP historical release calendars (BLS archive; unlocks event-section completion).
3. Consensus archive (H3 remains blocked; commercial license decision).
4. Daily-vintage PIT yields (ALFRED daily real-time; H1 strict form).
5. Synchronous BBO (execution-cost realism for any future registered cycle).
6. TFF position values (current normalized table is metadata-only).
7. Any return-conditioned hypothesis evaluation (requires a registered, budgeted, frozen cycle — by law, not by data).

---

## 10. ERRATA ledger (applied 2026-10-03, lane DOSSIER-ERRATA-V2; authority `audit/a7_nq/A7_DEEP_NQ.md`, verdict PASS_WITH_ERRATA — 13/13 headline recomputes MATCH)

Every item below is applied in place above and marked `[ERRATUM …]` at the correction site. Nothing was silently rewritten.

| id | severity | where | old → new | evidence |
|---|---|---|---|---|
| F1 | MAJOR | §7 heading-paragraph, §6 NOT_RUN inventory, §9 item 1, §0 held-series note | "THE 2020 VENDOR HOLE … entirely absent … top backfill candidate" → reclassified as vendor SYMBOLOGY ALIAS on `instrument_id 16908` (`NQU8-NQM9` 2018-08-15→2020-05-31; 58 trading dates and 21.82M contracts inside the "hole" window; view rule `instrument_id==16908 AND date<2020-06-01 → 'NQM0'`); "degraded from 03-16" struck (that was NQH0 expiry; true front 350,956-540,580 contracts/day 03-16..20); "NQU0 trickle" struck (actual front 6.8k-690k/day); §9 backfill CANCELLED ($0.62 quote recorded, not executed); 2020 aggregates MUST be re-measured at $0 before any registered cycle | A7-NQ F1 / r6; INTEGRATION-FIX-V2 `A_ALIAS_NOT_ABSENCE` |
| F2 | MAJOR | §5 data-discipline paragraph; `analysis/NQ_a5_cot.py` + `NQ_deep_lib.py` loader | §5 source pointer: pre-fix mixed-tidy description → fixed-tidy series `COT_LEGACY_NQ__ALT__NASDAQ_100_CONSOLIDATED_CHICAGO_MERCANTILE_EXCHANGE` (canonical `COT_LEGACY_NQ` = E-mini line 2006-2026). **No §5 number changes** (exact reproduction on the fixed tidy, incl. 850 rows / buckets 105-18.5%, 195-14.0%, 123-15.3%, 170-15.5%, 91-15.3%; OI 94,852→302,385; %OI 8.66→1.98). Loader fix: `NQ_a5_cot.py` selected 0 of 1,082 canonical rows on the fixed tidy (silent-empty); re-pointed to the `__ALT__` id with a hard guard. Canonical-line addendum recorded for the owner (extreme-short 18.39% vs mid 17.13%; OI 359k→284k; %OI 6.8→3.1) | A7-NQ F2 / r5 |
| F3 | MAJOR | §1 calendar-rule sensitivity | "ann vol 19.6% vs **16.9%** (volume rule) — inflated by…" → 19.6% vs **20.1%** (n=4,168 returns); 16.9% not reproducible from any delivered variant; comparison direction as previously written reverses; unfitness argument re-anchored to §3 thinness evidence | A7-NQ F3 |
| F4 | MINOR | §1 trend-persistence prose | ACF(1) −0.056 → **−0.076**; rolling-252d median −0.045 → **−0.042**; p10-p90 +0.069 → **+0.071**; VR(20) p10 0.53 → **0.522** | A7-NQ F4 |
| F5 | MINOR | §4 FOMC provenance, §6-H3 | "147 archived statements" → **132 statements + 15 b/c note files** (147 files); "106 statements with 'For release at'" → **92 statements** (106 = all files incl. 14 b/c with clock text); "98 of 106 are 2pm" → **85 of 92**; H3 "106 timestamps" → 92. Matched counts (128 day-level; 84 clean 2pm) and all ratios unchanged | A7-NQ F5 |
| F6 | MINOR | §9 item 1 window end, §2 holiday shorts | "2020-03-20..**2026**-05-29" → 2020-05-29 (same typo lives in `NQ_a7_quality.json` — flagged for regeneration, not hand-edited); "123 era-A Friday-early-close sessions" → **126** | A7-NQ F6 |
| N1 | NOTE | §2 (disclosed, no number change) | Yearly overnight share named as **mean of per-session shares** (a2's statistic); aggregate-volume variant differs ≤0.5pp (2010: 10.2 vs 9.8; 2026: 23.8 vs 23.7); doubling claim robust to the choice | A7-NQ N1 |
| N2 | NOTE | §5 (disclosed) | A5's rvol and mdd forward tables use slightly different row sets (mid n=123 vs n=126 — mdd table lacks the all-NaN guard); unified row set gives mid mdd −2.58% vs published −2.4% | A7-NQ N2 |
| N3 | NOTE | §4 (disclosed) | ±21d control pool includes sessions after the event — descriptive control, not a signal threshold; disclosed as acceptable prep practice | A7-NQ N3 |
| N4 | NOTE | folded into F2 | `NQ_deep_lib.load_cot_nq()` docstring / §5 wording describing the "three mixed lines" was accurate pre-fix and is retained as historical description; current tidy state stated in the F2 text | A7-NQ N4 |

Out-of-dossier items flagged for the owner (NOT edited by this lane): `analysis/NQ_a7_quality.json` `vendor_hole_2020` block (incl. `contracts_with_any_data` omitting NQM0_2020 for alias reasons, and the "2026-05-29" typo) requires regeneration from the corrected narrative, not hand-editing; `dispatch/handoff_DEEP-NQ.json` known_limitations[0] (hole framing), [2] (106/147 counts), [4] (three-mixed-lines wording) and recommended_next_action(1) (backfill) are superseded by F1/F5/F2 — that handoff remains the DEEP-NQ lane's record; this ledger supersedes it for dossier content.

— End of dossier. Every number above is reproducible from the listed scripts against the read-only vendor/nonprice trees; nothing here is a PASS/GO claim.
