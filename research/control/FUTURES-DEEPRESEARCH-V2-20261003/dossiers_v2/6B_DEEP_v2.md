# 6B_DEEP_v2 — British Pound Futures Deep Dossier v2 (2020-2026)

- Symbol: 6B (CME British Pound futures, 62,500 GBP, USD per GBP; see v1 §1 for
  mechanics — unchanged and incorporated by reference)
- Lane: DEEP-6B, task FUTURES-DEEPRESEARCH-V2-20261003 (prep-class deep
  descriptive research; NO scored runs, NO PnL evaluation, NO signal selection,
  NO conditional mean-return tables — those are NOT_RUN by law)
- Generated_utc: 2026-10-02 (all web fetches this session dated 2026-10-02)
- Supersedes (does not delete): FUTURES-BEHAVIOR-10SYMS-PREP-20261002
  dossiers/6B_DOSSIER.md (v1, 13.5-month IBKR real-volume era + settlement
  marks). v1 claims remain authoritative where this dossier says nothing new.
- Owner framework: owner_framework/6B_RESEARCH_FRAMEWORK.md (sha in v1 header).

## 0. Inputs and provenance

Primary price data — Databento GLBX.MDP3 ohlcv-1m, 6B, outright contracts only
(calendar-spread instruments excluded by symbol filter; serials excluded from
chains by design — both counted in §7):

| File | Window | sha256 (first 16) |
|---|---|---|
| .../parquet/AV1B-O1M-6B-BACKFILL2/...2020-01-01_2022-01-01.parquet | 2020-01→2022-01 (FX-BACKFILL lane) | c354cfb704c63f7c |
| .../parquet/AV1R-O1M-6B-BACKFILL/...2022-01-01_2024-01-01.parquet | 2022-01→2024-01 | 17857809913fa770 |
| .../parquet/AV1R-O1M-6B-BACKFILL/...2024-01-01_2026-01-01.parquet | 2024-01→2026-01 | 64423ad861917a19 |
| .../parquet/AV1R-O1M-6B-BACKFILL/...2026-01-01_2026-04-01.parquet | 2026-01→2026-04 | 996aa88ef3f5042a |
| .../parquet/AV1T-O1M-6B/...2026-04-01_2026-10-01.parquet | 2026-04→2026-10 | e5338f48ee274bb9 |

(full 64-hex shas in handoff_DEEP-6B.json outputs; ledger authority:
acquisition_download/COMPLETION_LEDGER.json + backfill_20261003/BACKFILL_LEDGER.json,
vendor job ids + vendor sha recorded there — [FACT]. NOTE: dispatch names the
dataset path ~/.my-quantitative-data/futures-databento-av1trim/; the delivered
bytes physically sit at /Users/hoangminhlong/my-quantitative-data/
futures-databento-av1trim/ (no leading dot) — verified this session [OBSERVED:
ls + shasum]; nonprice sits at the dot path as dispatched.)

Non-price inputs (all read-only):
- BoE Official Bank Rate decisions 2000→2025-12-18,
  normalized/boe_bank_rate_tidy.parquet (79789ea5112d8e1d, provenance sha in
  file, official_history_latest vintage) [FACT].
- BoE MPC announcement calendars 2020→2027 assembled this session from
  bankofengland.co.uk (news pages "MPC dates for YYYY" + upcoming-mpc-dates;
  2020-03-11 moved meeting + 2020-03-19 emergency added from the Bank-Rate
  table; rate-change subset == local parquet exactly) [FACT: fetched
  2026-10-02; cross-check OBSERVED].
- FOMC statements 2008→2026 from archived federalreserve.gov HTML
  (fed/statements/monetary*.html, 147 files = 132 `a`-statements + 15
  `b`/`c` implementation notes; 2020-2026 window: **59 statements, ALL 59
  carry in-document release-time proof; 53 at 14:00 ET; 58 dates in panel**
  [ERRATUM M4: was "58 in panel; 53 carry in-document 'For release at 2:00
  p.m. ET' proof" — the 53 is the 14:00-count, not the proof-count; the
  proof-count is 59/59]) [FACT + OBSERVED parse].
- CFTC legacy futures-only CoT, CME POUND STERLING → series COT_LEGACY_6B,
  2006-01-03→2026-09-22, n=1082 weeks, as-published
  (normalized/cftc_legacy_tidy.parquet, f7a2719e745c2f6f — canonical FIXED
  tidy, INTEGRATION-FIX-V2 2026-10-03 [ERRATUM M6: was 4f9cd78944ee79dc,
  the pre-fix tidy now preserved as `.bak_prefix_mixed_20261003`; the fix
  only stripped `market_name` trailing whitespace on 470 rows for 6B —
  numeric columns identical, verified row-for-row by A7-6B §4; no §5 number
  changes]) [FACT; POUND→6B
  mapping verified in nonprice_acquisition].
- FRED latest: FRED_DFEDTARU (fed funds target upper) — vintage_flag latest,
  NOT vintage-true PIT (ALFRED year-end vintages only) — used only for
  descriptive policy-differential mapping [FACT levels; vintage caveat].
- BoE gilt nominal daily curve (boe/glcnominalddata.zip, 312d4a0efaf93f5e,
  "GLC Nominal daily data_2016 to 2024.xlsx" updated 2025-01-21 → coverage
  ends 2024) [FACT; DECLARED_LAG caveat throughout §6].
- GLBX statistics (settlement/cleared-volume/OI) ALL10 2023-10→2026-10 and
  definitions ALL10 2023-10→2026-10 [FACT, in vendor package].

Analysis artifacts (this lane, all under
research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/):
6B_deep_lib.py, 6B_build_cache.py (+6B_build_report.json),
6B_a1_regimes.{py,json}, 6B_a2_sessions.{py,json}, 6B_a3_term.{py,json},
6B_a4_events.{py,json}, 6B_a5_cot.{py,json}, 6B_a6_gilts.{py,json},
6B_a7_quality.{py,json}; derived caches under 6B_cache/ (parquet).

Claims taxonomy: FACT (sourced) / OBSERVED (script+window) / POSTULATED
(mechanism, unmeasured) / NOT_RUN (never inferred PASS).

## 0.1 Panel construction (everything downstream depends on this)

- Outright 6B ohlcv-1m panel: 2,549,633 rows, 2020-01-01 23:00 UTC →
  2026-09-30 23:58 UTC; prices fixed-9 (×1e-9 → USD); session = 17:00 CT (D-1)
  → 16:00 CT (D), trade date D; maintenance break 16:00-17:00 CT: exactly ONE
  1m bar observed inside the break in 6.8y, 0 weekend bars — session clock is
  clean [OBSERVED: 6B_build_cache.py; 6B_a7_quality.py].
- Contract registry: 48 registry rows resolve to 32 distinct quarterly (HMUZ)
  contract keys (multi-cluster contracts = early deferred micro-prints;
  disambiguation: one-digit-year symbols split on 45-day gaps + expiry-window
  match; LTD rule = 2 business days before 3rd Wednesday, Mon-Fri
  approximation — Monday-holiday LTD shifts visible in data, e.g. 6BM3 last
  bar 2023-06-16 for Juneteenth week, tolerated by window). Of these, 28
  front-scale quarterlies 6BH0_2020→6BZ6_2026 carry the real market (>1M
  contracts lifetime volume each, 85k-99k 1m bars); 59 stray clusters
  quarantined (§7) [OBSERVED: 6B_deep_lib.build_contract_registry].
- DST correctness: session bar-counts on US spring-forward sessions (e.g.
  2021-03-15: 1294 bars) vs fall-back (2021-11-08: 1300) behave as 23h/25h CT
  wall-clock days; city-clock segment labels (Europe/London, Asia/Tokyo,
  America/Chicago via zoneinfo tz_convert) keep the BoE 12:00 London anchor at
  minute 720 London across BOTH UK/US DST mismatch weeks (e.g. 2022-10-06:
  12:00 London = 06:00 CT; 2022-03-17: = 07:00 CT) — DST-correct anchoring is
  demonstrated, not assumed [OBSERVED: 6B_a2_sessions.py `boe_1200_london_
  in_ct_clock`, `dst_transition_sessions`].
- Held-contract chains (no vendor stitching, ever): (a) calendar rule (v1
  declared rule: roll at last close before delivery-month day-1) — 1746
  sessions; (b) volume-crossover rule (PIT: switch when next quarterly's
  trailing-5-session mean volume > held's, decided at close, effective next
  session). Rules agree 1458/1746 sessions (83.5%); disagreements = 288
  sessions ≈ 44/year ≈ 11 per roll — the migration lag (§3) [OBSERVED:
  6B_build_cache.py]. Daily-return correlation between the two chains: 0.9998;
  both exclude roll-boundary returns from all statistics (no stitching jumps
  treated as alpha; raw gaps reported separately §3).

## 1. Strict-past regime map 2020-2026 [6B_a1_regimes.py]

Chain = calendar-rule quarterly chain, roll-boundary returns excluded,
truncated final session (2026-10-01) excluded; n=1630 daily returns.

Full-sample: mean −1.8e-05/day, std 0.549% (ann 8.71%), skew −0.28, kurt 4.4,
q05..q95 −0.89%..+0.81%, worst −3.82% (2022-09-23), best +3.17% [OBSERVED].

By year (era drift) [OBSERVED, `by_year`]:

| year | ann vol % | worst day % | mean day volume (contracts) |
|---|---|---|---|
| 2020 | 11.01 | −3.58 (COVID, 03-18/19 era) | 85,917 |
| 2021 | 6.63 | −1.36 | 77,642 |
| 2022 | 12.62 | −3.82 (2022-09-23 mini-budget) | 98,014 |
| 2023 | 8.28 | −1.60 | 83,619 |
| 2024 | 6.27 | −1.25 | 86,198 |
| 2025 | 7.13 | −1.58 | 74,309 |
| 2026 (to 09-30) | 6.50 | −0.98 | 72,342 |

Rolling-63d realized vol (min_periods 40 — see caveat below): min 4.72%
(window ending 2024-07-29) → median 7.25% → max 20.08% (window ending
2022-12-15, i.e. the Sep-Dec 2022 mini-budget aftermath), q25..q75
6.41..8.78%. ALL of the top-8 stress windows end between 2022-11-28 and
2022-12-20 (19.6-20.1% annualized): the LDI/fiscal crisis is THE vol regime
of record in 6.8 years [OBSERVED: `rv63`, `rv63_top8`]. CAVEAT [OBSERVED,
script note]: a naive rolling(63).std() would require all 63 values non-NaN
and — with 116 roll-boundary/thin-session NaNs scattered through the chain —
leaves only ~5 usable windows; min_periods=40 keeps ~1,630 valid windows and
every regime claim above uses that. Vol-regime labels (trailing-1y
percentile of rv63, strict past): high-regime day-share by year — 2021 1.5%,
2022 66%, 2023 8.5%, 2024 25%, 2025 50%, 2026 28% (2020 mid/low split
60/39); the regime map is genuinely time-varying, not one persistent state
[OBSERVED, `vol_regime_share_by_year`].

Trend persistence [OBSERVED, `persistence`]: return autocorr lag-1 +0.045
(daily, full sample) — no 1-day momentum/reversal signature; |ret| autocorr
lag-1 +0.252 → clear vol clustering; variance ratios VR(q): q2 1.13, q5 0.99,
q10 1.17, q21 0.73, q63 0.60 — MULTI-WEEK MEAN REVERSION dominates: 21- and
63-day horizons realize ~27%/40% LESS variance than iid, stable across years
(VR21 < 1 in 7/7 years, min 0.53 in 2026). POSTULATED mechanism: FX
mean-reversion of GBP idiosyncratic shocks absent UK-fiscal-stress regimes
(2022 VR21 0.98 — reversion suspended exactly in the crisis year, consistent
with §6's coupling).

Drawdown anatomy (roll-gap-excluded cumulative index) [OBSERVED,
`drawdown_episodes_below_3pct`, `max_drawdown`]:
- COVID: 2020-03-10→trough 2020-03-19, −14.52% (8 sessions), recovered by
  2020-11-10.
- 2021 wobble set: five −3.1..−3.9% episodes May-Sep 2021 (GBP peak 1.4164
  close 2021-05-27 era).
- THE BIG ONE (still open at data end): opens 2021-09-16, trough −22.48% on
  2022-09-26, never recovered through 2026-09-30 (close 1.3268 2026-09-30 vs
  cycle peak close 1.4205 on 2021-05-27; −24.7% close-to-close, −26.8%
  peak-close-to-trough-low 1.0392) [OBSERVED].

2022 GBP turmoil — first settlement-free 1m anatomy (v1 saw only
settlement-era daily marks) [OBSERVED: `turmoil_2022_daily`,
`turmoil_2022_summary`; window 2022-08-25→2022-10-21]:
- 2022-09-23 (mini-budget Friday): −3.82% close-to-close, range 1.1298→1.0840
  (4.1% intraday), 244,110 contracts.
- 2022-09-26 (Monday): low 1.0392 — the all-data low; 374,255 contracts = the
  highest-volume session in 6.8 years (4.5× the median day).
- 2022-09-28 (BoE gilt-market intervention): +1.40% with gilts rallying −38bp
  10y/−25bp 2y (§6).
- Episode stats (37 sessions): ann vol 18.86% (2.4× the 6.8y median),
  worst −3.82%, best +2.16% (2022-09-29).
- Event attribution of the crash days (fiscal announcement 2022-09-23, BoE
  intervention 2022-09-28) is context [FACT: public record via BoE/news,
  fetched by v1+this lane's gilt data]; the measured marks above are
  OBSERVED regardless of attribution.

## 2. Session/intraday structure — London morning + Asia now visible [6B_a2_sessions.py]

(v1 was RTH-blind: its bars covered 08:30-16:00 CT only. All numbers below are
DST-correct city-clock statistics on the held chain, 2020-01→2026-09,
truncated final session excluded.)

Volume by London clock hour (share of session volume) [OBSERVED,
`volume_share_by_london_hour`]:
- The modal hour is 15:00 London (= 09:00-10:00 CT London/US-overlap US-data
  window): 12.1-12.8% of volume in every era — the single most liquid hour.
- London morning 07:00-12:00: 28.7% (2020-21) → 27.5% (2022) → 27.5%
  (2023-24) → 23.7% (2025-26). DRIFT: London-morning share fell ~5pp over
  6.8 years, with the 08:00 London hour falling hardest (7.7%→5.7%);
  redistribution goes to the 12:00-17:00 London block (44.6%→45.5-46.5%) and
  the 17:00-24:00 London evening (17.9%→21.8%) — volume is migrating toward
  US hours, not away from GBP [OBSERVED; mechanism POSTULATED: US-macro
  dominance of the rate-differential regime 2022-2026].
- Asia overnight (00:00-07:00 London): stable 7.7-9.3% across eras — GBP's
  Asian session is small but persistent, no drift [OBSERVED].

Per-minute realized vol by segment (annualized from 1m log rets) [OBSERVED,
`per_minute_vol_by_segment_pct_ann_by_year`; caveat: thin segments
overstate vol via sparse-print jumps — asia_early especially]:
- lon_pre_boe (08:00-12:00 London): 13.8% (2020), 8.8% (2021), 14.7% (2022),
  9.8% (2023), 7.0% (2024), 8.3% (2025), 7.6% (2026) — tracks the annual
  vol map §1.
- us_rth: 13.1/8.1/14.1/10.2/7.8/8.5/7.9 — London-morning per-minute vol was
  slightly ABOVE US-RTH vol in 2020-2022 and slightly BELOW it every year
  2023-2026 — the two sessions are near-parity (GBP is a two-session market)
  with a mild late-sample tilt to the US window, consistent with the volume
  drift above [OBSERVED].

BoE release-minute verification (v1 upgrade: POSTULATED → OBSERVED): across
56 in-panel MPC days, mean volume by London minute spikes at exactly minute
720 (12:00): 3,451 contracts/min vs 1,392 (12:01) and 1,074 (12:02) — the
12:00 London announcement convention is now measured, matching the official
convention [OBSERVED: a2 `mpc_day_top5_minutes`; a4
`release_minute_empirical`].

## 3. Term structure + roll — 27 quarterly rolls [6B_a3_term.py]

(v1 had 4 rolls and could not see the old contract inside its delivery month.
Now: all 27 quarterly rolls 2020-02→2026-09 with full two-sided 1m data.)

Roll-gap distribution (next-minus-old close at the declared roll session,
both closes on real-volume bars) [OBSERVED, `roll_gap_dist_ticks`]:
- n=27, mean +6.5 ticks, median +5.0, std 8.6, q05..q95 −3.7..+22.7, min −5,
  max +30 ticks; 20 positive / 7 negative / 0 zero.
- In % of level: mean +0.052%, |gap| mean 0.062%, ≈ +0.21%/yr at 4 rolls/yr
  when positive.

v1 RE-TESTED AND OVERTURNED — the "mixed-sign ±2-5 ticks, no persistent
direction" finding was a zero-differential-window artifact: v1's four rolls
(2025-11→2026-08) all sat at a roll-date differential of **exactly 0.00pp**
(BoE 4.00/3.75 = Fed upper on all four dates; v1's own gaps −3..+5 ticks, v2's
re-measured full-session gaps on those dates −4..+1) [ERRATUM M2: was
"(diff −0.25..0.00pp → gaps −2..+3 ticks)" — wrong on both ends: −0.25 is an
era-path minimum not a roll-date value (80 of 395 days in 2025-09→2026-09
were nonzero), and the gap range matched neither v1's nor v2's numbers.
OVERTURN CONFIRMED by A7-6B: the zero-diff rolls show small mixed-sign gaps
−5..+13, exactly what v1 measured]. Across 27 rolls the gap SIGN AND SIZE
track the BoE-Fed policy differential on the roll date [OBSERVED,
`gap_vs_policy_diff`]:
- Pearson corr(gap ticks, Fed-target-upper − Bank Rate) = +0.84; rank corr
  (Spearman) = +0.744 [ERRATUM M1: was "rank corr = +0.84" — `6B_a3_term.json`
  `spearman_corr` = 0.7445; Pearson +0.84 is correct]; corr(realized gap
  ticks, CIP-predicted ticks) = 0.83.
- Mean gap when diff>0: +9.4 ticks (n=19); when diff<0: −3.0 ticks (n=1,
  the 2022-02-28 roll with BoE 0.50 vs Fed 0.25); the other 7 rolls sat at
  diff exactly 0 (2022-05, 2024-11, 2025-02, 2025-11, 2026-02, 2026-05,
  2026-08 — synchronized-policy windows) with gaps −5..+13 ticks; the +13
  outlier (2022-05-31) sits 2 days before the 2022-06-01 QT start and ~2
  weeks before the next scheduled FOMC (2022-06-15, archive
  `monetary20220615a.html`) [ERRATUM M3: was "one week before a scheduled
  Fed hike" — the nearest scheduled Fed event was the Jun-1 QT start (2
  days), not a hike] — the gap
  loads on the FORWARD differential, not only the spot one (mechanism
  POSTULATED from CIP; forward-rate data not in corpus).
- CIP magnitude: regression slope 0.186% per pp of differential vs theory
  0.253% per pp (91-day quarter, ACT/360) — realized carry ≈ 73% of textbook
  CIP; mean realized +6.5 ticks vs CIP-predicted +8.6 ticks. The roll gap IS
  the rate-differential carry, not noise. [OBSERVED; mechanism FACT-CIP
  textbook; rate inputs FACT with vintage caveats: BoE revision-free levels;
  Fed DFEDTARU = FRED latest, not vintage-true — benign for same-day-known
  policy targets, disclosed.]
- Calendar-spread series corroborates at daily granularity (front−next
  quarterly on two-sided-active days, n=851 days 2020-01→2026-09): median
  spread by year +8.0 (2020), +3.0 (2021), +19.5 (2022), +8.0 (2023), +4.0
  (2024), +1.0 (2025), −1.0 (2026) ticks — the term structure sign walks with
  the differential through the whole hiking/unwinding cycle [OBSERVED,
  `calendar_spread_median_ticks_by_year`].

Liquidity migration (v1 NOT_RUN dissolved — old side fully observable now):
- At EVERY declared roll session the old quarterly still trades 66k-172k
  contracts while the next prints 0.3-4.3k — median ratio old:new = 129:1
  [OBSERVED, `migration`].
- Volume crossover (next's trailing-5d mean > old's) occurs a median 11
  sessions AFTER the declared roll (min 9, q25 10, q75 11, max 13) —
  27/27 crossovers INSIDE the old contract's delivery month, i.e. ~1-2 weeks
  before its LTD. v1's 4-roll estimate "~8-9 sessions after" was close but
  low [OBSERVED].
- Old contract keeps a median 824,460 contracts of volume inside its
  delivery month — the month is not dead; it is the liquid month [OBSERVED].
- OI-based roll (GLBX statistics, 2023-12→2026-09, 11 rolls): OI crossover
  LEADS volume crossover by 5-7 days (median −6) — open interest migrates
  first, volume follows [OBSERVED, `oi_vs_volume_crossover`].
- Practical consequence measured on the chains: the calendar rule holds the
  thin new contract for ~11 sessions post-roll (e.g. held-contract volume
  **1,069..13,222 contracts/day (median ~3.1k; only 03-11/03-12 reach ~13k)**
  in 2024-03-01..12 vs 100k+ on the old [ERRATUM M7: was "13-16k/day" —
  understated the thinness; the qualitative point (calendar rule holds a
  thin contract post-roll) stands and is STRONGER as corrected]), and
  114/1746 held-chain
  sessions have <600 printed 1m bars — almost all inside those windows
  [OBSERVED: a7 `sessions_below_600_bars` 33+71+10].

## 4. Event-day anatomy — BoE MPC + FOMC [6B_a4_events.py]

Release-anchored volume/vol/range descriptives ONLY (no conditional
mean-return tables: those are PnL-linked selection = NOT_RUN by law).

BoE MPC days (n=56 in panel 2020-01→2026-09: 22 rate-change, 34 hold;
calendar FACT per §0; controls = non-MPC Thursdays n=295, and all non-event
days n=1687) [OBSERVED, `boe`]:
- ±30m around 12:00 London: median 17,454 contracts vs 3,371 (non-MPC
  Thursday) = 5.2×; median summed |1m ret| 0.0126 vs 0.0051 = 2.5×; median
  window range 26.1 pip vs 6.3 pip = 4.1×.
- First 5 minutes (12:00-12:05): median 7,091 contracts vs 380 = 18.7×;
  median |ret| sum 0.0040 vs 0.00053 = 7.6×.
- Whole-day: median 117,908 contracts vs 78,189 (Thursdays) = 1.51×; median
  day range 1.02% vs 0.68% = 1.51×.
- Change vs hold days: day volume ~equal (117.9k vs 118.3k — the calendar,
  not the decision, drives attendance); first-5m volume higher on change
  days (median 8,985 vs 6,435) and first-5m |move| larger (0.0048 vs
  0.0027) — the decision content shows up in the reaction window
  [OBSERVED].
- Release-minute spike at 12:00 London exactly (§2) [OBSERVED].

FOMC days (n=58 dates with panel bars of the 59 statements in the
2020-2026 window — ALL 59 with in-document release-time proof; 53 at 14:00
ET = the 13:00 CT anchor; 6 statements at other times: 08:00/08:30/09:10/
10:00×2/17:00 ET, five the 2020 COVID intermeeting moves plus 2025-08-22
10:00 ET [ERRATUM M4: was "53 with in-document 14:00 ET proof" — conflated
the proof-count (59/59) with the 14:00-count (53)] ; control = non-FOMC
Wednesdays n=295-299)
[OBSERVED, `fomc`]:
- First 5 min after 13:00 CT: median 2,266 contracts vs 239 = 9.5×; median
  |ret| sum 0.0031 vs 0.00037 = 8.4×.
- ±30m: median 6,772 vs 2,609 = 2.6× (FOMC is a USD-leg event for 6B —
  real but half the BoE intensity).
- Whole-day volume: 91,641 vs 82,047 = 1.12× only — FOMC concentrates into
  the release window rather than lifting the day [OBSERVED].
- 2020-03-19 (08:00 ET special, coordinated swap-line day): day range 2.83%,
  158k contracts [OBSERVED].

Top 1m volume bars sanity: 2020-10-01 13:05 UTC (US presidential COVID
diagnosis), 2020-11-11 (vaccine Monday), 2022-02-03 12:00 UTC (BoE
double-hike day = in BoE window), 2024-08-23 (Jackson Hole) — the bar-level
event sensitivity is real and correctly timestamped [OBSERVED].

## 5. CoT POUND STERLING positioning 2006-2026 [6B_a5_cot.py]

(CFTC legacy futures-only, as-published, obs Tuesday → release Friday 15:30
ET — release lag median 3 days, min 2, max 4 [OBSERVED]. Forward outcomes
measured on the calendar-rule chain from 2020 (chain start); z = strict-past
156-week rolling z of net-noncomm/OI. n=326 joint obs 2020-01→2026-09.
Forward drawdown is LOCAL to the 20-session forward window — the secular
2021-22 decline must not masquerade as "drawdown following positioning".)

- Net-noncomm range 2006-2026: median −12k, q05..q95 −76.7k..+57.0k
  contracts, min −107,844 (obs 2017-03-21, record spec SHORT — Brexit
  aftermath), max +142,183 (obs 2024-07-23, record spec LONG) [OBSERVED,
  `net_noncomm_stats_2006_2026`].
- v1 driver-#8 falsification test answered DESCRIPTIVELY: positioning
  extremes do NOT precede elevated forward risk. corr(|z|, forward-20-session
  realized vol) = −0.07 (signed z: −0.08); bucket medians of forward vol:
  z<−1.5 → 6.17%, |z|<0.5 → 7.99%, z>1.5 → 6.85%; forward window-local
  max-drawdown medians −1.6%..−2.3% across buckets with extremes carrying
  mildly deeper medians, within noise (z>1.5 median −2.27% vs neutral
  −1.64%; p05 −4.83% vs −4.31%; z<−1.5 p05 −4.88% vs −4.31%) [ERRATUM M5:
  was "extremes no worse than neutral" — contradicted by the same table's
  drawdown leg (the quoted numbers were already in the text); the vol-bucket
  flatness and the corr −0.07 null result stand unchanged]
  [OBSERVED, `forward_20s_outcomes_by_z_bucket`]. The crowded-positioning-
  unwind amplification story has NO descriptive support at weekly frequency
  on 6B in 2020-2026 — and the 2022 crash arrived from SHORT positioning
  (Aug-2022 snapshot: z −0.4..−1.26, net spec −28k..−56k contracts — specs
  were positioned FOR the slide, not against it) [OBSERVED,
  `turmoil_2022_positioning`].
- OI structural level: median OI by era 2006-09: 104k; 2010-13: 145k;
  2014-17: 212k; 2018-21: 190k; 2022-26: 228k — contract relevance grew
  through the sample [OBSERVED, `oi_median_by_era`].
- Spec positioning is a persistent-crowd variable (net spec and net comm are
  strongly mirror-image: hedgers supply the other side) — descriptive only;
  NO positioning-conditioned return tables run (NOT_RUN by law).

## 6. Gilt-curve coupling (DECLARED_LAG caveat) [6B_a6_gilts.py]

Source: BoE GLC nominal spot curve, local copy ends 2024 (§0). Gilt data is
published with a declared lag → contemporaneous associations below are
descriptive; PIT use requires ≥1 business-day lag. 2025-2026 gilt coupling:
NOT_RUN (no local data).

- Full-sample (2020-2024, n=1171): corr(6B daily ret, Δ10y gilt) = −0.13 —
  weak average coupling [OBSERVED, `full_corr_ret_dg10`].
- Era drift: 2020 −0.14, 2021 +0.17, 2022 −0.23, 2023 −0.06, 2024 −0.10 —
  the SIGN is regime-dependent (risk-on/risk-off vs fiscal-stress regimes
  flip it) [OBSERVED, `era_corr_6b_vs_gilts`].
- Rolling-63d corr(6B ret, Δgilt10): min −0.57 at 2022-10-17 — the LDI
  crisis is the most negative coupling window in the sample; max +0.55 at
  2020-12-23 (Brexit-deal-breakdown window: gilts and GBP fell together =
  UK-idiosyncratic risk pricing) [OBSERVED, `rolling63_corr_ret_dg10`].
- Mini-budget episode (2022-09-20→10-17 daily table in JSON): 09-23 6B −3.82%
  with 2y +45bp/10y +29bp; 09-26 −1.46% with 2y +44bp (2y level 4.53% on
  09-27 = crisis peak); 09-28 +1.40% with 10y −38bp on BoE intervention;
  4-day window corr −0.68 [OBSERVED, `mini_budget_episode`].
- Gilt-stress days (2022, |Δ10y| > 2σ): median |6B ret| 1.40% vs calm days
  0.32% = 4.4× (n=9 stress days incl. 09-23/26/27/28, 10-10/13/17/24)
  [OBSERVED, `gilt_stress_days_2022`].
- v1 H3 (fiscal-credibility → 6B underperforms) now has measured UK-specific
  stress covariates; the relative-value leg (6B vs 6E) remains NOT_RUN this
  lane (6E panel is another lane's data; cross-asset RV deferred).

## 7. Data-quality ledger per era [6B_a7_quality.py]

| check | backfill 2020-01→2022-01 | main 2022-01→2026-04 | recent 2026-04→2026-10 |
|---|---|---|---|
| outright rows | 754,609 | 1,615,234 | 179,790 |
| spread-instrument rows excluded | 37,943 | 135,537 | 15,559 |
| OHLC violations | 0 | 0 | 0 |
| zero-volume outright bars | 0 | 0 | 0 |
| duplicate (instrument_id, ts_event) | 0 | 0 | 0 |
| held-chain sessions / weekday-days expected | 518/522 | 1096/1107 | 132/132 |
| missing weekday sessions | 4 (Good Friday 2020/2021? observed: 2020-04-10, 2020-12-25, 2021-01-01, 2021-12-24) | 11 (all holidays: 2022-04-15, 2022-12-26, 2023-01-02, 2023-12-25, 2024-01-01, 2024-03-29, ...) | 0 |
| median 1m bars/session (held chain) | 1284 | 1281 | 1222 |

- Butt joints: 2022-01-01 and 2026-04-01 — ZERO duplicate keys across the
  seams; front-contract close→open continuity across each seam 0.00% and
  +0.074% (a normal weekend gap) — the three delivery chunks butt cleanly
  with no double-billing artifacts [OBSERVED, `butt_joints`].
- Weekend bars: 0. Bars inside 16:00-17:00 CT break: 1 (single stray minute).
  DST-transition sessions present with full bar counts (§0.1) [OBSERVED].
- Stray inventory (quarantined from all analyses, 59 clusters, 85,731 bars,
  413,468 volume): 57 serial-month clusters (F/G/J/K/N/Q/V/X — dead by
  design, 0.256% of outright volume — corroborates v1's "serials dead" on
  6.8y); 1 non-6B symbol `GCQ4` (gold Aug-2024 prints inside the 6B
  response — vendor parent-mapping leak, 2,139 bars 2020-07→2020-11);
  1 quarterly `6BM5` early cluster (1,392 bars 2020-01→2020-05 on the
  Jun-2025 symbol ~5y before plausible listing — either very-long-dated
  deferred prints or vendor mapping artifact; unresolved here) [OBSERVED,
  `stray_clusters`].
- min_price_increment from GLBX definitions (19,183 6B quarterly definition
  rows 2023-10→2026-10): uniformly 0.0001 USD — PRIMARY-SOURCE ADJUDICATION
  of v1's AMP(0.0001)/TK(0.0002) conflict in favor of 0.0001 ($6.25/contract)
  [FACT: vendor definition records; v1's spread-tick USD figures stand].
- Truncated final session 2026-10-01 (fetch cut 2026-09-30 23:58 UTC):
  excluded from all statistics that need full sessions [OBSERVED].

## 8. Hypothesis refinement vs v1 (NO PnL evaluation — specs only)

v1 hypotheses H1-H5 re-ranked by the new evidence. Every spec stays
descriptive/unpriced; PARAM-GAPs either dissolved by measurement or restated.

**H1' (v1 H1) — Roll-timing/contract-selection microstructure — ESSENTIALLY
MEASURED NOW.** v1's PARAM-GAP ("only 4 rolls; x% crossover threshold
un.calibratable") is DISSOLVED: 27 rolls, crossover median 11 sessions after
declared roll (9-13 range, all inside delivery month), OI crossover leads
volume crossover by 5-7 days. Refined PIT rule (no free parameters left):
switch at first close where next-quarterly trailing-5d mean volume > held's
(strict past). Remaining gaps: (a) execution-cost difference between holding
old-in-delivery-month vs new-thin is NOT measured (needs intraday spread data
— bbo-1m NOT in package); (b) OI-informed rule (switch 5-7d earlier than
volume crossover) measurable only 2023-10+ (statistics window). Floor for
any stability claim (≥12 rolls): MET (27). Invalidation condition updated:
crossover drift >±5 sessions across future rolls (measured spread 9-13
supports stability). [OBSERVED for the anatomy; PnL comparison NOT_RUN]

**H2' (v1 H2) — BoE-vs-Fed repricing.** Upgrade: the release machinery is
now measured (12:00 London spike, 18.7× first-5m volume, MPC-day range
1.02% vs 0.68%). The differential channel itself is CONFIRMED structurally
in the term structure (roll gap = CIP carry, corr 0.84 §3) — the SAME
macro variable the hypothesis trades. What remains NOT_RUN: consensus
surprise vintages (no licensed surprise source in corpus — unchanged from
v1); any conditional mean-return test (law). Refined floor: event-window
execution must assume entry ≥1 minute post-12:00:00 London (volume spike
makes same-minute fills optimistic — descriptive evidence §4).
[mechanism partially OBSERVED; signal NOT_RUN]

**H3' (v1 H3) — UK fiscal-credibility shocks → GBP underperforms EUR.**
Upgrade: 2022 episode now fully measured on both legs available locally
(6B 1m + gilt curve daily): −22.5% drawdown anatomy, −0.68 4-day coupling,
stress-day |ret| 4.4×. Gilt conditioning usable PIT only with ≥1bd lag
(DECLARED_LAG). Remaining NOT_RUN: the 6E relative-value leg (cross-lane
data), HM Treasury fiscal-event calendar (still unfetched), 2025-2026 gilt
coupling (local gilt data ends 2024). Floor: n=1 crisis in window —
hypothesis remains a single-episode story; pre-2020 fiscal episodes
(2016 Brexit not in 1m window) NOT_RUN. [episode OBSERVED; RV test NOT_RUN]

**H4' (v1 H4) — London-session breakout by regime.** Upgrade: London
morning is now measurable (28.7%→23.7% share, per-minute vol parity with
US RTH, BoE window anatomy). The hypothesis's core variable (London
morning range break → US-session continuation) is now testable in
principle on this panel; NOT tested here (conditional mean-return = law
violation). PARAM-GAP restated: breakout definition (range window
07:00-11:00 London? level h≥ prior N-day k-range?) still owner-choice;
entry-delay +1-5m test now feasible. Era-drift caveat NEW from §2: London
share is falling — any session-structure hypothesis must be
rolling-window, not full-sample. [structure OBSERVED; signal NOT_RUN]

**H5' (v1 H5) — US-macro-window gap reaction.** DISSOLVED AS FRAMED: v1's
"hidden-gap proxy" (RTH open vs prior close) is obsolete — the 08:30 CT
release minute is directly in the 1m panel now. Event-window vol anatomy
(FOMC first-5m 9.5× §4) supersedes it. Remaining NOT_RUN: BLS CPI/NFP
release-calendar fetch (v1 404s; not re-attempted this lane — BLS gate
dataset exists in nonprice `bls_gate/`, NOT parsed here), any conditional
return table. [anatomy OBSERVED for FOMC; CPI-day anatomy NOT_RUN]

**NEW H6 — Roll-carry aware chain selection (spec, unpriced).** Since the
roll gap is CIP carry (corr 0.84, slope 73% of theory), the choice of roll
DATE inside the delivery month carries/loses ≈ differential × days
remaining: rolling EARLY (calendar rule) vs at volume crossover differs by
~11 sessions × (Fed−BoE) × level/360 — in 2022-23 that is ±2-3 ticks of
pure carry per roll, in 2025-26 ≈ 0. A chain-selection rule that rolls at
crossover both tracks liquidity (H1') and holds the carry leg to its
converging maturity. All components measured; the SELECTION between rules
by PnL = NOT_RUN (law). [components OBSERVED; rule evaluation NOT_RUN]

**NEW H7 — Session-migration drift (spec, unpriced).** London-morning share
fell 28.7%→23.7% while 15:00-London hour rose to 12.8% (§2). If execution
capacity matters, scheduling assumptions built on 2020-22 liquidity maps
are stale by ~5pp. Descriptive drift only; no trade. [OBSERVED]

**CoT driver (v1 #8) — DOWNGRADED.** Positioning extremes do NOT precede
forward vol elevation (corr −0.07, flat bucket medians §5); the
crowded-unwind amplification mechanism has no descriptive support on 6B
weekly data. Keep CoT as a context variable, drop from the driver
short-list. [OBSERVED negative result]

## 9. Missing data / remaining NOT_RUN

| item | status |
|---|---|
| Conditional mean-return / event-reaction drift tables (any event) | NOT_RUN by law (PnL-linked selection; needs registered cycle) |
| 6B↔6E relative-value (H3' leg), 6B↔ES beta on 6.8y | NOT_RUN this lane (cross-symbol panels are other lanes' outputs; defer to A7-DEEP-AUDIT or registered cycle) |
| bbo-1m / spread behavior around events + rolls | NOT_RUN (schema not purchased) |
| OI pre-2023-10 | NOT_RUN (statistics window starts 2023-10) |
| Gilt curve 2025-2026 | NOT_RUN (local copy ends 2024; DECLARED_LAG caveat throughout §6) |
| Consensus surprise vintages (BoE/CPI/NFP) | NOT_RUN (no licensed source — unchanged since v1) |
| ONS calendar + UK-data event anatomy | NOT_RUN (ons.gov.uk fetch not re-attempted; calendar NOT in nonprice corpus) |
| BLS CPI/NFP day anatomy | NOT_RUN (calendar unfetched; bls_gate/ raw present but un-parsed this lane) |
| Official CME holiday calendar | NOT_RUN (transport-blocked; holiday gaps inferred from data only, §7) |
| 6B exchange fee schedule | NOT_RUN (CME 403; IBKR $0.85/side known from v1) |
| 6BM5 early-cluster + GCQ4 strays adjudication | NOT_RUN (vendor-side; quarantined + documented §7) |

## 10. Framework coverage deltas vs v1

- §4 regime map: DONE descriptively (vol/trend/monetary/USD-adjacent) for
  2020-2026 [OBSERVED]. Crisis-vs-calm relationship flips: gilt coupling
  sign flips by regime (§6); VR21 mean-reversion suspends in 2022 (§1).
- §5 event-study framework: release anchoring + spread/volume response
  DONE for BoE/FOMC (descriptive); returns-at-horizons NOT_RUN (law).
- §6 term structure: roll table 27 rolls, calendar-spread series, CIP
  mapping, OI-vs-volume roll comparison DONE [OBSERVED]. Back-adjustment
  impact on trend signals: still NOT_RUN (no back-adjustment by design;
  raw gaps now known to be CIP-carry, ±0.05% mean).
- §7 cross-asset: NOT_RUN (deferred, see §9).
- §13 driver map: differential channel UP (CIP-confirmed), fiscal channel
  UP (episode measured), positioning channel DOWN (negative result),
  BoE-vs-ONS intraday timing RESOLVED for BoE (12:00 London measured).
- §16 failure modes: fiscal-event jumps — now measured (2022 anatomy);
  thin Asia liquidity — measured as 8-9% share, stable; cash/futures
  basis & roll — measured as CIP carry with vintage caveats;
  Brexit-era breaks — still outside 1m window (NOT_RUN).

**Bottom line for downstream lanes:** 6B on the new panel is a
6.8-year, 2.55M-bar, DST-clean, two-sided-roll-observable market whose
roll gaps are rate-differential carry (corr 0.84), whose events fire on
the minute (BoE 12:00 London 18.7× first-5m; FOMC 13:00 CT 9.5×), whose
London morning is drifting down ~5pp, whose weekly positioning shows no
forward-risk content, and whose one regime break (2022 fiscal crisis) is
now fully reconstructed at 1m resolution. All PnL-linked questions
remain NOT_RUN pending a registered cycle.

---

## 11. ERRATA ledger (applied 2026-10-03, lane DOSSIER-ERRATA-V2)

Source of record: `audit/a7_6b/A7_DEEP_6B.md` — verdict PASS_WITH_MINOR_ERRATA
(0 BLOCKER / 0 MAJOR / 7 MINOR / 5 NOTE; ~36 headline numbers recomputed fresh
with an independent implementation — every numeric claim reproduces exactly;
the v1-overturn headline is CONFIRMED). Each item below is applied in place
above and marked `[ERRATUM …]` at the correction site; nothing was silently
rewritten. The 5 NOTEs required no dossier change (N1: §1 "low 1.0392" is the
held-chain low — panel-wide low 1.0293 on a 6BU3 deferred 2-lot print same
day; N2: "4.5× median day" approximation fine; N3: auditor's own first-pass
DST bug corroborates the lane's DST correctness; N4: a5 CoT predates the tidy
fix by 45 min — verified numerically identical; N5: DFEDTARU latest-not-vintage
disclosed).

| id | severity | was (old) | now (new) | site |
|---|---|---|---|---|
| M1 | MINOR | "rank corr = +0.84" | Spearman **+0.744** (`6B_a3_term.json` 0.7445); Pearson +0.84 correct | §3 |
| M2 | MINOR | v1-overturn parenthetical "(diff −0.25..0.00pp → gaps −2..+3 ticks)" | roll-date differential **exactly 0.00** on all four v1 dates; v1 gaps −3..+5; v2 re-measured −4..+1. Overturn claim itself CONFIRMED (cleaner than stated) | §3 |
| M3 | MINOR | "+13 outlier (2022-05-31) one week before a scheduled Fed hike" | 2 days before the 2022-06-01 QT start; next scheduled FOMC 2022-06-15 (~2 weeks) | §3 |
| M4 | MINOR | "58 in panel; 53 carry in-document proof" / "n=58 statements; 53 with in-document 14:00 ET proof" | **59 statements 2020-2026, ALL 59 with proof; 53 at 14:00 ET; 58 dates with panel bars**; 6 non-14:00 statements (5 COVID 2020 + 2025-08-22) | §0; §4 |
| M5 | MINOR | "extremes no worse than neutral" | "mildly deeper medians at extremes, within noise" (z>1.5 −2.27% vs −1.64%; p05 −4.83/−4.88 vs −4.31); vol flatness + corr −0.07 stand | §5 |
| M6 | MINOR | CoT provenance sha `4f9cd78944ee79dc` (pre-fix tidy, now `.bak`) | canonical fixed-tidy sha `f7a2719e745c2f6f`; fix = whitespace-only for 6B, numbers unchanged | §0 |
| M7 | MINOR | "held-contract volume 13-16k/day in 2024-03-01..12" | **1,069..13,222/day (median ~3.1k; only 03-11/12 reach ~13k)** — understated thinness; point stronger | §3 |

INCIDENT (lane DOSSIER-ERRATA-V2, 2026-10-03): a power outage killed the
errata session mid-run after the other five dossiers were partially
errata'd; 6B was untouched in the partial state (0 erratum mentions) and
was applied in full on resume.
