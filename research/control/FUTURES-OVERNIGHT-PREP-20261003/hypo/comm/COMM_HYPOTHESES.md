# COMM_HYPOTHESES — Competing-hypothesis families for CL, NG, GC, SI

- Task: **FUTURES-OVERNIGHT-PREP-20261003**, lane **P1-COMM**. Generated UTC
  2026-10-04. Worktree
  `/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/prep` @
  `72c9bc5b1d94b812044a9bd21768c53b4d378436` (re-measured via `git -C`
  immediately before writing; no tracked drift), branch
  `prep/futures-behavior-10syms-20261002`.
- Class: PREP competing-hypothesis specification. **0 PnL, 0 scored runs, 0
  selection by any return statistic; every parameter [PROVISIONAL];
  outcome-blind.** No committed file modified.
- **SCOPE LAW (measured this lane, not assumed):** the vendor root
  `/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim/`
  contains **O1M price data for 6A/6B/6E/6J/ES/NQ ONLY** (dir listing:
  AV1B/AV1R-O1M-{6A,6B,6E,6J}, AV1R-O1M-{ES,NQ}); for CL/NG/GC/SI it holds
  only `AV1T-definition-ALL10` + `AV1T-statistics-ALL10` (metadata; the
  definition manifest's symbol list includes CL.FUT/NG.FUT/GC.FUT/SI.FUT,
  quarterly chunks 2023-10 onward — sha256 d431a38d…). Price history for the
  four commodity codes = **14–22 months IBKR legacy daily/H1-RTH/M1-2D** +
  settlement-derived deferred marks only. **Every family below is
  PROVISIONAL design + free-source testability plan; anything requiring
  intraday history is NOT_RUN_DATA_ABSENT today. NO qualification upgrade is
  claimed: CL/NG/GC/SI remain NOT_QUALIFIED_V2
  (DATACONTRACT_QUALIFICATION §2, sha256 df175a2d…).**
- Labels on every substantive claim: **OBSERVED** (artifact + field/section)
  / **MECHANISM_HYPOTHESIS** (unmeasured causal story) / **INFERENCE**
  (flagged argument) / **NOT_RUN** (missing evidence is never PASS).
- All 24 cited artifacts hashed this lane in `captures/source_sha256.tsv`
  (sha256 per FACT in §7). **No new web fetches this lane** — all numerics
  are local artifacts re-measured with python/grep this session (log:
  `fetch_log.jsonl`); URLs cited from the dossiers/evidence files carry
  their original access dates (2026-10-02/03).

---

## 0. Standing context all families inherit (cite-once block)

### 0.1 Corrected cost law (batch-1, commit 72c9bc5b) — MODELED COST ONLY

- Corrected tier-1/Fixed all-in fees: **CL 2.36 · NG 2.46 · GC 2.51 · SI
  2.51 USD/side** (commission 0.85 + exchange 1.50/1.60/1.65/1.65 + reg
  0.01; glued-superscript erratum upheld by P0-VERIFY) [OBSERVED,
  `FEES_CORRECTED.md` §2, sha256 006d6372…]. Tiered T2–T4: CL
  2.16/1.96/1.76 · NG 2.26/2.06/1.86 · GC/SI 2.31/2.11/1.91. All
  **MODELED COST**, SOURCE=PUBLIC_REFERENCE,
  **VERIFIED_VS_ACCOUNT=NOT_RUN**; fee values **UNDER REVIEW** until a new
  A7 re-audit [OBSERVED, FEES_CORRECTED §6].
- Per-side MODELED totals (fees + spread half-turn proxy + slippage tier).
  Spread proxies are v1-dossier close-proxy **full** spreads halved
  (high-biased, non-synchronous; BBO NOT_RUN); slippage {1,2,3 ticks}/side =
  research assumption (D1 precedent). Tick values: CL $10 (0.01×1000 bbl) ·
  NG $10 (0.001×10,000 MMBtu) · GC $10 (0.1×100 oz) · SI $25
  (0.005×5,000 oz).

| symbol | fees | half-spread proxy (source) | S1 | S2 | S3 |
|---|---|---|---|---|---|
| CL | 2.36 | 15.00 (3.0-tick $30 front-20d median, CL_DOSSIER §3) | **27.36** | **37.36** | **47.36** |
| NG | 2.46 | 10.00 (2-tick $20 front median, NG_DOSSIER §3) | **22.46** | **32.46** | **42.46** |
| GC | 2.51 | 25.00 (5-tick $50 front-20d median, GC_DOSSIER §3) | **37.51** | **47.51** | **57.51** |
| SI | 2.51 | 50.00 (4-tick $100 liquid-era pooled median, SI_DOSSIER §3) | **77.51** | **102.51** | **127.51** |

  The words "measured" or "complete" applied to cost are FORBIDDEN; a
  daily-close
  round-trip event window pays 2 sides (×2 the table).

### 0.2 Calendar + expiry authority (all ARCHIVED_OFFICIAL; zero extrapolation)

[OBSERVED, `COMM_CALENDAR_EVIDENCE.md` §2 table rows, sha256 adcd3b54… +
`FXCOMM_GAPFILL_EVIDENCE.md` §3, sha256 0de05fa5…]

- **CL** last-trade dates **Apr 2010 → Feb 2027** (183 months; two chained
  captures 20100310023046 + 20180228030442, rule-reconciled); termination
  rule verbatim ×2 eras: "third business day prior to the 25th calendar day
  of the month preceding the delivery month" + weekend-shift sub-rule ("if
  the 25th is a non-business day, trading ceases 3 bd prior to the last
  business day preceding the 25th" ≡ 2020-era "4 bd prior to the 25th" —
  semantically equivalent, both validated against official dates).
- **NG** last-trade dates **Jun 2010 → Feb 2027** (240 months; captures
  20100430195312 + 20170220105945); rule 3rd-last business day of the month
  prior to delivery month — 2021 text == v1 dossier wording verbatim;
  canonical **last-trade-month** roll basis confirmed (NG_DOSSIER §1 audit
  M2).
- **GC** dates Aug 2013 → Jun 2019 (parent) **extended to Dec 2023**
  (FXCOMM: capture 20180227093156 embedded JSON rows incl. GCM23 28 Jun
  2023, GCZ23 27 Dec 2023); **2024–2026 NOT_OBTAINED**. Last trade 12:30 CT
  third-last business day of contract month (2 eras verbatim; = 13:30 ET of
  v1 dossier).
- **SI** dates Mar 2015 → Dec 2019 (parent) **extended to Dec 2022**
  (FXCOMM: capture 20180227093206, SIZ22 28 Dec 2022); **2023–2026
  NOT_OBTAINED**. Last trade **12:25 CT** third-last business day (vs GC
  12:30 CT — the offset is official, 2 eras); 5,000 oz class confirmed.
- Energy/metals holiday Globex times: **2011–2015 = 43/45 cells** verbatim
  PDFs (gaps: 2014-MLK NOT_TRANSCRIBED, 2014/2015-Veterans NOT_OBTAINED) +
  **2017–2023 bonus grid** (FXCOMM §2b/bonus; Monday-halt regime shifts
  2011-12 → 2013-15 → 2018-21 12:00 CT → 2022 13:30 CT). **Binding
  exclude-days law: any day whose session calendar is uncertain ⇒
  EXCLUDE/NOT_RUN, never inferred-pass.**

### 0.3 The 14-month era law (the standing limitation, declared once)

Every futures-price statistic available to these four symbols comes from a
single contiguous window: CL true-volume front 2025-08-21→2026-10-01 (280
days), NG 2025-08-01→2026-10-01 (281 returns), GC real-volume chain
2025-01-15→2026-10-01 (424 returns), SI cycle chain 2025-07-01→2026-10-01
(316 days) [OBSERVED, respective dossiers §3]. One regime per symbol (CL/NG
high-vol; GC 30.7% ann-vol regime; SI squeeze-and-crash). **No family below
can claim regime breadth; every era-stability kill is unanswerable until
deeper data lands (owner purchase decision).** Deep per-contract bars
before these windows are settlement-derived (v=0, O=H=L=C) — reference
only, never fills [OBSERVED, dossiers §3].

### 0.4 Nonprice inventory re-verified THIS lane (the free legs)

[All OBSERVED 2026-10-04, python/grep on
`~/.my-quantitative-data/futures-nonprice-10syms/`; hashes §7]

| Asset | Measured this lane | Verdict |
|---|---|---|
| EIA WNGSR issues | 1,205 HTML files 2001-05-07 → 2026-01-22 (`eia/wngsr/issues/`); tidy `eia_wngsr_vintages_tidy.parquet` 1,205×26 with per-issue `provenance_sha256`, `working_gas_total_bcf`, `net_change_bcf`+`net_change_direction` | as-published PIT-grade, in hand |
| The Desk survey (NG consensus, free) | "the desk" text present in **393/1,205** raw issues, earliest **2017-05-11** (grep); tidy `survey_median_bcf` non-null **369 rows, 2018-05-03 → 2026-01-22**; `survey_direction` = {injections 247, withdrawals 87, **NaN 35**}; **ALL 369 medians stored as positive magnitudes** (sign lives only in the direction words) | genuine free consensus, **unsigned ⇒ r-1 blocker stands (§1 F1)** |
| EIA WPSR | 790 issues 2011-08-03 → 2026-09-30 + tables (ttable1/3/4 ×790 each, ttable13.pdf ×750); **Cushing line present 790/790 ttable4** (byte-level check; earlier shell-grep 745 was a glob artifact, superseded); tidy `eia_wpsr_vintages_tidy.parquet` 790×5 `crude_mmbbl`+`cushing_mmbbl` per vintage | as-published PIT-grade, in hand |
| WPSR analyst survey | grep of wpsr_2026_09_30.html: **no analyst-consensus text** (only website-survey JS + EIA-914 "survey-based production" boilerplate) | **no free CL consensus exists ⇒ naive-surprise proxy required (declared §2 F1)** |
| NOAA CPC 6-10d | `610temp/` 4,459 daily zips 2012-09-11 → 2025-06-30 + `610temp_recent_weekly/` 65 weekly 2025-07-07 → 2026-09-28 + `814temp_pilot/` 31 files (8-14d, Sep–Oct 2026); inventory parquet 4,555 rows, `valid_window="issue+6..10d"`, `vintage_flag="issued_forecast_as_published"`, per-file sha256; zip-internal file times 15:02 (e.g. 610temp_20250630.zip) | issued-vintage archive PIT-grade, in hand; issuance-time evidence = file clock only (official issuance schedule NOT verified) |
| Observed HDD/CDD | `noaa_observed_popweighted_hddcdd.parquet` 1,319 **monthly** periods (1895-01 →), `observed_official_weights_predeclared` | **MONTHLY cadence ⇒ 6-10d verification leg NOT_RUN_DATA_ABSENT** (daily observed temps not owned) |
| FRED ALFRED | year-end as-of snapshots only (e.g. DFII10_asof_2024-12-31.csv); per DATACONTRACT §1.4: **NOT PIT-strict** | descriptive/CIP use with sensitivity only |

### 0.5 Free/official daily testability verdicts (summary; detail per family)

- **NG = FREE_MEASURABLE_DAILY (blocked only by r-1 + price-history depth)**:
  surprise leg 100% free in corpus (vintages + The Desk medians); price leg
  = IBKR 14m in corpus + free EIA daily NG futures settle page
  (eia.gov/dnav/ng/ng_pri_fut_s1_d.htm — URL per NG_DOSSIER §1, accessed
  2026-10-02; NOT fetched this lane) for pre-2025 extension.
- **CL = PARTIAL_FREE**: vintages + Cushing free; consensus NOT free
  (naive proxy declared); price leg same shape as NG (EIA WTI spot page as
  conditioning-measurement candidate, not fills).
- **GC = PARTIAL_FREE**: free/official daily legs = Treasury 10y TIPS real
  yield (treasury.gov daily real-yield curve; FRED DFII10 latest-vintage;
  corpus year-end snapshots) + CFTC CoT (free, Fri-15:30 as-published) +
  LBMA Gold Price PM auction (free with delay; lbma.org.uk / ICE — per
  GC/SI dossiers §4, accessed 2026-10-02). Curve legs beyond 22 months =
  vendor decision.
- **SI = PARTIAL_FREE**: free/official daily legs = LBMA Silver Price
  auction (12:00 London, administered by ICE; free with delay) + CFTC CoT;
  GC co-leg free as above. Two-leg depth beyond 15 months = vendor
  decision.
- **All four = NOT_RUN_DATA_ABSENT intraday** (H1 RTH ~14m + M1 2D only;
  no 10:30-release-window, no overnight session, no BBO).

---

## 1. NG — Henry Hub natural gas (2 competing families + 1 construction law)

### NG-F1 — WNGSR storage-surprise resolution (The-Desk free consensus)

**Field 1 — Mechanism.** MECHANISM_HYPOTHESIS: at the WNGSR Thursday
10:30 ET release, the front NG contract reprices in the direction of the
storage surprise (actual net-change minus The-Desk survey median) over
minutes-to-days, because working-gas inventory is the binding state
variable of a storable commodity and the print resolves the week's
storage uncertainty. OBSERVED anatomy: (a) release schedule FACT —
standard Thursdays 10:30 ET, holiday moves Fri 10:30 / Wed 12:00 (NG_DOSSIER
§4, ir.eia.gov/ngs/ngs.html + /schedule.html, accessed 2026-10-02); (b)
Thursday 10:00–11:00 ET bucket carries **25.3% of RTH volume vs 16.1–18.0%
other weekdays** and the highest mean |hour-ret| 0.49% [OBSERVED,
NG_DOSSIER §3 session behavior — adjacent anatomy, NOT an event study]; (c)
the consensus is inside the release itself: verbatim 2025-10-30 issue —
"estimates of the weekly net change … ranged from net injections of 70 Bcf
to 88 Bcf, with a median estimate of 81 Bcf" vs actual "net injections
totaled 74 Bcf" [OBSERVED, corpus issue file, sha256 ff544642…]. The
event-conditioned reaction itself: **NOT_RUN** (prep prohibition + no
release-time intraday).

**PRE-REGISTERED BLOCKER r-1 (confirmed at column level this lane):** the
survey values are **unsigned** — all 369 tidy medians are positive
magnitudes; sign lives only in `survey_direction` words ("injections"/
"withdrawals"), which is **NaN on 35 rows**; the actual side likewise
splits `net_change_bcf`/`net_change_direction`. **A signed-surprise rule
(direction→sign mapping, zero-change and NaN-direction edge cases,
withdrawal-season sign convention) must be written, tested, and frozen
BEFORE any NG-F1 math. Until then NG-F1 arithmetic = NOT_RUN_BLOCKED_R1.**
[OBSERVED, eia_wngsr_vintages_tidy.parquet, sha256 3914729f…]

**Field 2 — Expected direction (falsifiable).** Signed surprise S
(= signed_actual − signed_consensus) > 0 (smaller build / larger draw than
expected) ⇒ front NG daily returns measured close-to-close through the
release window are conditionally positive (and symmetric for S<0);
equivalently E[r | S>0] − E[r | S<0] > 2×(round-trip cost) at the daily
horizon. Competing sign prediction lives in NG-F2 (reaction is a
weather-revision proxy, surprise adds nothing).

**Field 3 — PIT feature availability.** Release clock: FACT (schedule
page, holiday moves enumerated; 2026 examples: Nov 13 → Fri, Nov 25 → Wed
12:00). Vintages: every issue file is the as-published release with
per-issue sha256 in the tidy parquet [OBSERVED]; weekly estimates are
preliminary — **treat vintages, never revised history** (NG_DOSSIER §4
law). Consensus: The-Desk text inside the release document itself ⇒
zero-lag, zero-extra-source consensus (survey of analysts taken before
release; published simultaneously with the actual) — the only free,
release-embedded consensus among all four symbols. Coverage: medians
2018-05-03→2026-01-22 (369 events; raw text earliest 2017-05-11, not
adjudicated pre-2018 by the nonprice lane's round-4 "2018+ genuine"
verdict). Gaps: tidy chain ends 2026-01-22 (issues beyond = current_week
live page, not archived in corpus); intraday release-window prices NOT_RUN.

**Field 4 — Bindings.** NG (NYMEX): 10,000 MMBtu, USD/MMBtu, tick 0.001 =
$10; physical delivery Henry Hub; Globex 18:00→17:00 ET (60-min break),
RTH 09:30–17:00 ET, all bars RTH-only; **negative-CL law adopted
symbol-wide** (simple returns, no log assumption — NG_DOSSIER §3
convention); monthly, 12 months listed; last trade = **3rd-last business
day of month before delivery** (official dates Jun 2010→Feb 2027 in hand,
§0.2); roll baseline = canonical **last-trade-month** rule (last session
before day-1 of the LTD month; NGX26 roll 2026-09-30 observed) with
volume-crossover alternative declared (8/13 winter-dominated pairs —
NG_DOSSIER §1); month code = delivery month, raw `expiry_month` field
holds lastTradeDate (S9 C3 mislabel hazard). No overnight/Asia/Europe bars.

**Field 5 — Entry/stand-aside/exit [PROVISIONAL] (daily design; intraday
variant NOT_RUN_DATA_ABSENT).** Event day = Thursday with scheduled 10:30
ET release (holiday-shifted dates from schedule page). State: S computed
from release (after r-1 rule frozen). Entry: release-day RTH close (first
settle observable after release in a daily-bar world) in sign(S); variant
delay-pair: t+1 close (both pre-registered; the daily pair is the only
legal delay axis — the intraday 10:31-entry variant of NG_DOSSIER H1 is
**NOT_RUN_DATA_ABSENT**). Exit: t+3 close or opposite-signed release,
whichever first [PROVISIONAL horizon]. Stand-aside: (i) holiday-shifted
releases (Fri/Wed-noon) flagged, reported split not pooled; (ii) NaN/
zero-direction survey rows EXCLUDED until r-1 rule covers them; (iii)
roll-session days ±1 EXCLUDE (stitch contamination); (iv) uncertain
calendar days EXCLUDE/NOT_RUN (§0.2 law).

**Field 6 — Baselines/placebo/negative controls.** (a) Weekday-matched
non-event placebo: same entry/exit clock on Tuesdays (non-release days)
with random sign — a scored placebo path (C1-class); (b) always-in-window
baseline Tue–Thu (C2-class); (c) **seasonal placebo for the weather
confound**: same design keyed to CPC-forecast-revision sign instead of S
(NG-F2 cross-adjudication — the two families are each other's negative
control); (d) sign-flipped-S placebo (S with random sign) — mechanism must
die under (a)/(d) if fake.

**Field 7 — Refutation conditions.** Mechanism-level first: (i)
conditional effect ≤ 0 after r-1 rule applied, or sign instability across
injection/withdrawal seasons (single-season window = declared
unanswerable, §0.3); (ii) effect fully absorbed by same-week CPC revision
state (NG-F2 wins); (iii) placebo (a)/(d) reproduces the "effect" ⇒ kill;
(iv) effect lives only in the 35 NaN-direction or quarantined rows ⇒
parser artifact, kill. Cost-level: corrected all-ins §0.1 (NG S2 32.46/
side; round trip 64.92) + NG spread proxy 2 ticks (reconciled to S6,
NG_DOSSIER §3) + slippage tiers; family dies if median |conditional daily
move| ≤ round-trip cost at S1 and sign weakens monotonically with tier.
**r-1 blocker pre-registered above — no NG-F1 math before it is cleared.**

**Field 8 — Cost sensitivity.** MODELED COST ONLY: fees 2.46 UNDER REVIEW
(§0.1); tiers S1/S2/S3 per side 22.46/32.46/42.46; measured/complete
FORBIDDEN. Fee-schedule era caveat: multi-year backtests must declare
per-year schedule or current-as-approximation (PLAYBOOKS §4.4 law) —
pre-2018 fee schedules NOT sourced.

**Field 9 — Regime/era breaks.** The 14-month window is the limitation
itself: one seasonal cycle, one high-vol regime (NG ann. vol ~49%),
2025-26 winter concentration measured once (Jan |r| 4.98% vs Apr 1.48%,
single cycle [OBSERVED §3]). 369 free surprise events span 2018-2026
(≈7 seasonal cycles) but price legs for 2018-2024 are settlement-derived
or not owned ⇒ the free-source testability plan (Field 11) is the only
route to era breadth. Injection/withdrawal season split is mandatory
(storage percentile conditioning declared NOT_RUN until Cushing-style
level series is computed from vintages — feasible free).

**Field 10 — Coverage/hole proof.** HAVE: 1,205 WNGSR vintages (per-issue
sha256), 369 survey medians, 790-item roll-adjacent NG daily IBKR true
volume, NG front BID/ASK 1Y close-proxy, official expiry dates 2010-2027,
holiday times 2011-15/2017-23. HOLE (nothing exists): release-window
intraday (any year), overnight-session bars, BBO/depth, OI, pre-2018
survey adjudication (2017-05..2018-04 text present, tidy parse absent),
post-2026-01-22 archived issues, daily observed temps for 6-10d
verification (NG-F2 hole), PIT-strict consensus beyond the release-embedded
text. **Intraday: NOTHING exists — full stop.**

**Field 11 — Sources per FACT.** (1) WNGSR schedule + release law:
https://www.eia.gov/naturalgas/storage/ (ir.eia.gov/ngs/ngs.html +
/ngs/schedule.html), accessed 2026-10-02 by the NG dossier lane [FACT].
(2) Corpus issues + tidy: local paths §7, sha256 3914729f… (tidy),
ff544642… (2025-10-30 issue), 408e8ef7… (2017-05-11 earliest-Desk issue).
(3) The-Desk-2018+-genuine adjudication: nonprice lane round-4 verdict
(dispatch KEY FACTS; re-measured text presence this lane, count 393).
(4) Price legs: `~/.my-quantitative-data/futures-10syms-v1/raw/NG_*` (160
files, sha256 9d7755d2… exemplar); free extension candidate URL (NOT
fetched this lane): https://www.eia.gov/dnav/ng/ng_pri_fut_s1_d.htm
("Official daily closing prices at 2:30 p.m. … NYMEX" — quoted in
NG_DOSSIER §1, accessed 2026-10-02).

### NG-F2 — CPC 6-10d forecast-REVISION momentum (weather-revision flow) — the direct competitor

**Field 1 — Mechanism.** MECHANISM_HYPOTHESIS: consecutive issued vintages
of the CPC 6-10d temperature outlook revise the expected HDD/CDD demand
path; traders reprice the NG balance as forecasts rev, and because the
physical system mean-reverts while revisions cluster, front NG drifts in
the revision direction over 1-5 days — i.e., the same Thursday-week price
action NG-F1 attributes to storage is driven by weather-information flow.
OBSERVED anatomy: (a) issued-vintage archive in hand — 4,559 daily zips
2012-09-11→2025-06-30 + 65 weekly to 2026-09-28, each an immutable
shapefile vintage with per-file sha256 and `valid_window=issue+6..10d`
[OBSERVED, inventory parquet sha256 2d8f68c5…]; (b) winter/summer |r|
split 3.09% vs 1.82% (~1.7×) and curve seasonality sign flip
[OBSERVED, NG_DOSSIER §3 — adjacent, weather-consistent, not
revision-specific]. The revision-conditioned drift: **NOT_RUN**. **Honest
re-scope of the dispatch's "forecast-error regime" framing: the
ERROR-REGIME variant (issued vs realized) is NOT_RUN_DATA_ABSENT — the
corpus's observed HDD/CDD leg is MONTHLY (1,319 monthly periods), which
cannot verify a 6-10d window; only the REVISION leg (vintage t vs t-1 for
the same valid window) is computable today.**

**Field 2 — Expected direction (falsifiable).** Define R(t) = revision of
the 6-10d population-weighted temperature outlook for window W between the
two most recent issued vintages (colder-revision = positive demand shock).
Prediction: E[front-NG return over the 1-5 sessions after vintage t] has
the same sign as the demand revision, conditionally on storage-ample
regimes being weaker/reversed; and — the competition — R(t) subsumes the
NG-F1 surprise state (regression coefficient on S → 0 once R included).

**Field 3 — PIT feature availability.** Issued vintages: as-published,
immutable, per-file sha256 — the archive IS the vintage law. Issuance
cadence: daily (business days) 2012-2025, then weekly recent window
— **a cadence break measured in the corpus itself** (daily zips end
2025-06-30; weekly thereafter) that any long design must declare.
Issuance TIME evidence: zip-internal file clock 15:02 local [OBSERVED,
unzip listing] — file-clock only; official publication-time schedule
NOT_RUN (NOAA CPC page not fetched this lane). Latency to NG-relevant
usability NOT measured. Realized-weather leg: monthly only (§0.4) ⇒
verification designs blocked; realized weather as a PIT feature is
forbidden anyway (NG_DOSSIER §4 law: FORECAST VINTAGES ONLY).

**Field 4 — Bindings.** Identical to NG-F1 Field 4 (same contract, roll,
session, negative-CL law). Feature clock: CPC issuance days mapped to NG
trading days via next-RTH-close (a daily-bar design; the 10:00-ET
pre-release entry variant of NG_DOSSIER H2 is NOT_RUN_DATA_ABSENT for lack
of issuance-time + intraday evidence).

**Field 5 — Entry/stand-aside/exit [PROVISIONAL] (daily).** State: R(t)
from consecutive vintages for the same valid window (sign convention:
colder = demand-positive). Entry: first NG RTH close after vintage t
became available (file-clock + conservative 1-session lag [PROVISIONAL]);
direction with the demand revision. Exit: 5 sessions or offsetting
revision [PROVISIONAL]. Stand-aside: (i) Thursdays EXCLUDE from entry
samples and reported separately (release-day contamination — the F1/F2
separation requires clean non-release entries); (ii) weekly-cadence era
post-2025-06 split-flagged; (iii) roll ±1 days EXCLUDE; (iv) seasonal
placebo windows (Field 6).

**Field 6 — Baselines/placebo/negative controls.** (a) **Seasonal placebo
(mandatory for weather families)**: same design with R replaced by the
same-calendar-month mean revision of trailing years (pure seasonality must
show nothing if the mechanism is information-flow, not calendar); (b)
weekday-matched random-vintage placebo (C1-class); (c) storage-percentile
split (ample vs tight) — the mechanism predicts attenuation in ample
regimes; (d) NG-F1 cross-adjudication (Field 2).

**Field 7 — Refutation conditions.** Mechanism-level: (i) sign
instability across seasons beyond placebo (Field 6a reproduces the effect
Ⓢ mechanism is calendar, kill); (ii) symmetric fade of revisions (entry-
delay sensitivity at daily granularity: effect gone at t+1 entry ⇒
same-day absorption, kill the drift claim); (iii) revision state adds
nothing beyond seasonality in a pre-registered two-regressor comparison;
(iv) effect confined to the weekly-cadence era ⇒ cadence artifact. Cost-
level: §0.1 NG tiers; a 1-5-day hold pays one round trip ⇒ dies if median
conditional |move| ≤ 64.92 (S2 round trip). r-1 not binding here (no
survey math) but the storage-percentile control uses vintages (sign
convention shared with r-1 rule — declared dependency).

**Field 8 — Cost sensitivity.** Same MODELED-COST law as NG-F1 (22.46/
32.46/42.46 per side); no measured statements. Horizon note: multi-day
holds make the fee share smaller but add weekend/gap risk priced by SI-
style overnight-gap blind spot (no overnight bars — §0.3).

**Field 9 — Regime/era breaks.** 14-month price window (single winter);
feature window 2012-2026 (13+ years of vintages) — **asymmetry declared**:
features are long, prices are short; the honest design tests 2025-2026
only until the free price extension (EIA daily settle page) is fetched
(capture-timestamped, then 2018-2026 overlap becomes testable).
CPC-archive cadence break 2025-06 (daily→weekly) declared. Era-stability
kills unanswerable pre-extension.

**Field 10 — Coverage/hole proof.** HAVE: 4,555 issued vintages with
sha256 + valid windows; monthly pop-weighted observed HDD/CDD (official
weights); NG price/roll/curve 14m; seasonal anatomy. HOLE: DAILY observed
temperatures (blocks error-regime variant — NOT_RUN_DATA_ABSENT), official
issuance-time schedule, pre-2025-07 price front (except settlement-derived
curve legs), intraday anything, HDD/CDD **forecast** aggregates (the zips
are probability-of-above/below shapefiles — the population-weighted
degree-day AGGREGATION rule (which weights, which stations) is NOT in the
corpus and must be built + frozen a priori [PROVISIONAL derivation task];
the monthly observed series' "official weights predeclared" flag covers
only the observed leg).

**Field 11 — Sources per FACT.** (1) Corpus zips + inventory parquet:
local paths §7 (sha256 2d8f68c5… inventory; 2c54c854… observed monthly).
(2) CPC product page (URL from SI/NG dossier lineage, NOT fetched this
lane): https://www.cpc.ncep.noaa.gov/products/predictions/6_10day/ —
candidate for issuance-schedule evidence; archive-timestamp required when
fetched. (3) Weather-driver row of NG_DOSSIER §2 (NOMADS keyed by run
date+cycle, accessed 2026-10-02) as the GFS-vintage alternative path. No
purchases, no signups anywhere in this plan.

### NG-F3 — CONSTRUCTION LAW (not a hypothesis): seasonal-flip roll structure

Declared per owner law (PLAYBOOKS §0 H-G precedent): the measured m1−m2
seasonal flip (autumn/spring contango medians −0.44/−0.30/−0.28 vs
mid-winter backwardation +0.55/+0.34, single cycle [OBSERVED, NG_DOSSIER
§3]) and the 8/13 winter-dominated volume-crossover heterogeneity
[OBSERVED, §1] are **curve construction / roll-selection inputs — they are
NOT alpha**. Any future NG family must state its roll convention (canonical
last-trade-month baseline; volume-crossover alternative), exclude roll ±1
days, and never register "seasonal flip" as a signal. Back-adjustment
NOT_RUN in prep (deferred to engine).

---

## 2. CL — WTI crude oil (2 competing families + 1 cost-law declaration)

### CL-F1 — WPSR Wednesday inventory-surprise resolution (naive-surprise proxy)

**Field 1 — Mechanism.** MECHANISM_HYPOTHESIS: the WPSR Wednesday 10:30 ET
release resolves weekly crude/Cushing inventory uncertainty; the front CL
reprices in the surprise direction over minutes-to-days, strongest when
Cushing (the deliverable hub) contradicts the national headline (CL_DOSSIER
§2 driver 1 + 9, §5 H2/H3 — POSTULATED there, unmeasured). OBSERVED
anatomy: (a) 790 as-published WPSR vintages 2011-08-03→2026-09-30 with
crude + Cushing per issue [OBSERVED, tidy sha256 ba439c60…; Cushing line
790/790 ttable4, byte-checked]; (b) release schedule FACT (Wed 10:30 ET,
holiday shifts Thu 12:00 / NY-Thu 11:00 / Christmas-Mon 17:00 — CL_DOSSIER
§4, eia.gov schedule page accessed 2026-10-02); (c) adjacent on-symbol
anatomy only: Wednesday |ret| 2.25% ≈ Tuesday 2.24% (n≈56, descriptive,
corrected within-contract values) [OBSERVED, CL_DOSSIER §3 erratum block].
Event-conditioned reaction: **NOT_RUN**. **Free-consensus blocker declared
(measured this lane): WPSR issues contain NO analyst-survey text — the CL
consensus (Bloomberg/Reuters-style) is vendor-licensed. Surprise must be
defined as a NAIVE proxy [PROVISIONAL]: signed_actual − expectation, with
expectation ∈ {5-year-average same-storage-week change, prior-week change},
chosen a priori and frozen before any math; a true-consensus variant stays
NOT_RUN_DATA_ABSENT (paid).**

**Field 2 — Expected direction (falsifiable).** Naive surprise N > 0
(larger draw / smaller build than the frozen naive expectation) ⇒
conditionally positive CL daily returns through the release window;
Cushing-leg surprise N_C predicts the front better than the national leg
when the two disagree (delivered-hub primacy). Competing sign prediction
lives in CL-F2 (conflict ⇒ reversal).

**Field 3 — PIT feature availability.** Release clock FACT (schedule page
+ enumerated holiday moves); vintages as-published with per-issue sha256;
weekly data preliminary (crude-imports table flagged preliminary; errata
page exists) — treat vintages, never revised history (CL_DOSSIER §4).
Consensus: absent free (measured); naive-expectation inputs (5-year
seasonal means) computable from the same vintages strictly trailing
(release-t-1 information only). Coverage: 790 issues ≈ 15 years of
surprise states once the proxy is frozen.

**Field 4 — Bindings.** CL (NYMEX): 1,000 bbl, USD & cents/bbl, tick 0.01
= $10; physical delivery Cushing; Globex Sun 18:00→Fri 17:00 ET (60-min
break), RTH bars only; **negative-price law mandatory** (Apr-2020
neighborhood; dataset itself has 0 negative bars but the convention is
binding — CL_DOSSIER §3); monthly, all 12; last trade = **3rd business day
prior to the 25th of the month prior to delivery + weekend-shift
sub-rule** (official dates Apr 2010→Feb 2027 in hand, §0.2); roll baseline
= declared calendar rule (last session before day-1 of LTD month, ~21
calendar days pre-LTD, old book still 3-7× next — CL_DOSSIER §1) with
volume-switch alternative NOT_RUN for 13/14 rolls (data past boundary
absent); month code = delivery month; raw `expiry_month` holds
lastTradeDate (S9 C3). Dynamic price limits (secondary source, ~15%):
no limit-hit in window [OBSERVED no-hit only].

**Field 5 — Entry/stand-aside/exit [PROVISIONAL] (daily; intraday variant
NOT_RUN_DATA_ABSENT).** Event day = scheduled WPSR Wednesday (holiday
shifts flagged). State: N (and N_C) from release vs frozen naive
expectation. Entry: release-day RTH close in sign(N) — first post-release
observable on daily bars; delay-pair: t+1 close. The 10:31-ET first-bar
entry of CL_DOSSIER H2 is NOT_RUN_DATA_ABSENT. Exit: t+3 close or
opposite-sign release [PROVISIONAL]. Stand-aside: holiday-shifted releases
split-reported; OPEC-meeting days EXCLUDE if a dated OPEC calendar is
ever pinned (currently NOT_RUN — opec.org 403, CL_DOSSIER §4); roll ±1
EXCLUDE; uncertain calendar days EXCLUDE/NOT_RUN.

**Field 6 — Baselines/placebo/negative controls.** (a) Weekday-matched
non-event placebo: Tuesdays/Thursdays same clock random-sign (scored C1);
(b) always-in Tue–Thu baseline (C2); (c) **national-vs-Cushing sign-
conflict subset** = the CL-F2 adjudication leg (reported split, not
pooled); (d) API-Tuesday pre-information row (CL_DOSSIER §2 driver 2):
Tuesday conditioning must show NOTHING if the WPSR mechanism is real
(negative control; API timing detail NOT_RUN, day-level FACT only).

**Field 7 — Refutation conditions.** Mechanism-level: (i) conditional
effect ≤ 0 or sign-unstable across the 15-year free feature window (once
price legs extended); (ii) naive-proxy choice flips the sign of the
conclusion ⇒ proxy fragility kill (both pre-declared proxies must agree in
sign for survival — a pre-registered double-proxy robustness rule); (iii)
Cushing leg does not beat national leg where they conflict ⇒ delivered-hub
primacy dead; (iv) Tuesday negative control (d) shows equal "effect" ⇒
weekday artifact kill. Cost-level: §0.1 CL tiers (S2 37.36/side, round
trip 74.72) + 3-tick spread proxy; dies if median conditional |move| ≤
round trip at S1. No r-1 analogue (no survey), but the naive-expectation
freeze plays the same role — no math before freeze.

**Field 8 — Cost sensitivity.** MODELED COST ONLY; fees 2.36 UNDER
REVIEW; tiers 27.36/37.36/47.36 per side; per-year fee schedules for
2011-2024 NOT sourced (declare current-as-approximation if ever
backtested long). Slippage tiers {1,2,3}×$10 assumption.

**Field 9 — Regime/era breaks.** Price window 14 months, **100%
backwardation (280/280 days)** [OBSERVED, CL_DOSSIER §3] — zero contango
regime observed ⇒ regime breadth NOT_RUN until depth lands; feature
window 15 years (asymmetry declared, as NG-F2). Vol regime: 38-42% ann.
current vs p10 ~20% (rolling median). Era-stability kills unanswerable
today.

**Field 10 — Coverage/hole proof.** HAVE: 790 WPSR vintages (+ Cushing
790/790), official CL expiry dates 2010-2027, holiday times 2011-15/
2017-23, 280-day true-volume front + curve, BID/ASK 1Y close-proxy,
29-contract deferred settlement marks. HOLE: intraday anything (release
window, overnight), OI, API historical prints (vendor), consensus
(vendor), product futures RB/HO (H3 conflict-definition data absent —
PARAM-GAP), OPEC decision record (403), volume past roll boundary (13/14
rolls). **Intraday: NOTHING exists.**

**Field 11 — Sources per FACT.** (1) WPSR schedule:
https://www.eia.gov/petroleum/supply/weekly/schedule.php (accessed
2026-10-02, CL_DOSSIER §4) [FACT]. (2) Corpus vintages/tables: §7 sha256
ba439c60… / d579fd86… / 4b4f3963… (2011-08-03 ttable4 Cushing exemplar).
(3) No-consensus measurement: grep wpsr_2026_09_30.html (sha256
8de87d99…) this lane. (4) Price legs: `CL_*` 160 files (exemplar sha256
f0b47fef…); free extension candidate (NOT fetched): EIA WTI spot page
https://www.eia.gov/dnav/petroleum/pet_pri_spt_s1_d.htm (conditioning-
measurement leg only, never fills). (5) Rule verbatim ×2 eras +
183-month table: COMM_CALENDAR_EVIDENCE.md §1 (sha256 adcd3b54…).

### CL-F2 — Post-WPSR reversal on headline-vs-Cushing conflict (the competitor)

**Field 1 — Mechanism.** MECHANISM_HYPOTHESIS (from CL_DOSSIER §5 H3,
re-grounded): the first post-release move trades the national headline;
when the Cushing detail contradicts it, fundamentals reprice and the
first move partially REVERTS next session — i.e., where CL-F1 predicts
continuation in surprise direction, CL-F2 predicts that the conflict
subset reverses. OBSERVED anatomy: same 790-vintage Cushing-vs-national
panel as CL-F1 (measured inputs); the conflict-conditional path itself
NOT_RUN. No product (RB/HO) leg exists in corpus — the H3
headline-vs-products variant stays PARAM-GAP; the Cushing variant is
testable free.

**Field 2 — Expected direction (falsifiable).** On Wednesdays where
sign(N_national) ≠ sign(N_Cushing) (both vs frozen naive expectations),
the t+1 CL return is conditionally OPPOSITE to the release-day (t) move,
beyond costs; on agreeing-sign Wednesdays continuation (CL-F1) holds.
The two families are adjudicated on the SAME registered event set —
pre-registered conflict-split, no post-hoc tail choice.

**Fields 3-4 — PIT + bindings.** Identical to CL-F1 (same vintages, same
clock, same contract/roll/session bindings; conflict state uses only
release-t information).

**Field 5 — Entry/stand-aside/exit [PROVISIONAL] (daily).** Condition on
conflict Wednesdays; entry at t+1 open/close OPPOSITE the day-t signed
move [PROVISIONAL close variant primary]; exit t+3 [PROVISIONAL].
Stand-aside: as CL-F1 plus non-conflict Wednesdays excluded from this
arm (they belong to CL-F1's continuation arm).

**Field 6 — Baselines/placebo.** (a) same-day random-sign placebo on the
same conflict subset (scored); (b) agreeing-sign subset as the built-in
contrast; (c) weekday-matched Tuesday placebo; (d) seasonal placebo on
Cushing's own seasonal path (maintenance-season conflict clusters must
not carry the effect).

**Field 7 — Refutation conditions.** Mechanism: conflict subset shows
continuation, not reversal ⇒ CL-F2 dead (CL-F1 strengthened); reversal
absent AND continuation absent ⇒ both dead, event-day conditioning
itself killed; reversal survives but is explained by naive-proxy
fragility (proxy double-agreement rule of CL-F1 Field 7ii) ⇒ parser
artifact kill. Cost: same §0.1 CL tiers — reversal must exceed round
trip 74.72 at S2 median.

**Field 8 — Cost sensitivity.** Identical MODELED-COST law to CL-F1.

**Field 9 — Regime/era breaks.** Same 14-month law (§0.3) + 15-year
feature asymmetry; conflict frequency itself is seasonally clustered
(refinery maintenance) — season-split mandatory, single-regime caveat
declared.

**Field 10 — Coverage/hole proof.** Same as CL-F1; additionally the
products-leg (gasoline/distillate detail tables 3/4 exist in corpus as
CSVs — the CRUDE-vs-CUSHING conflict is computable; the
headline-vs-PRODUCTS conflict is computable too from ttable1/3 — noted
as a free extension, NOT_RUN here).

**Field 11 — Sources.** Identical to CL-F1 (§2 F11), plus conflict-leg
inputs = ttable1 (national) + ttable4 (Cushing) per vintage.

### CL cost-law declaration (not a family)

Steep backwardation 280/280 days (median −$0.58/bbl, deepest −$8.65;
roll gaps median −$0.51, max −$8.22) [OBSERVED, CL_DOSSIER §3] is a
**COST/carry conditioning input, not alpha** (owner law; H-G precedent):
any future CL family must declare its carry state as a control/split, and
roll-gap magnitudes enter cost accounting for multi-session holds. Term-
structure-momentum (CL_DOSSIER H1) is NOT registered here — it requires
regime breadth (zero contango observed) ⇒ NOT_RUN_DATA_ABSENT depth.

---

## 3. GC — gold (2 families; evidence thin — 22-month true-volume era)

### GC-F1 — Contango-compression stress signal (curve anatomy)

**Field 1 — Mechanism.** MECHANISM_HYPOTHESIS: GC's near-vs-far spread is
full-carry contango on ~100% of sessions [OBSERVED, GC_DOSSIER §3:
99.8-100% every pair; median 2m spread ≈ −19..−24 USD/oz near-minus-far;
12m ≈ −39..−42; 7 roll gaps +27.5..+37.3 ≈ 2 months × ~16 USD/oz/month,
incl. audit-m2 7th roll +31.1 on 2026-09-30]. The only force that
flattens a full-carry curve is spot-adjacent urgency (physical/EFP
squeeze premium); therefore compression of the 2m spread below a strict-
past fraction of its trailing median should precede front outperformance
over days-weeks (GC_DOSSIER §5 H3, re-grounded on the committed anatomy).
The conditional outperformance: NOT_RUN (real-volume curve only
2025-01→2026-10, ~40 weekly observations — power NOT_RUN).

**Field 2 — Expected direction (falsifiable).** After compression days
(spread < 0.5 × trailing-126-session median, strict past), front-GC
outperforms the deferred leg over a pre-declared 10-session window; the
built-in competitor — **rate-mechanical compression** — predicts NO front
outperformance conditional on the compression being explained by Δ(real
yield/short rate).

**Field 3 — PIT feature availability.** Curve legs: own per-contract
closes (IBKR, in corpus; deep bars settlement-derived — reference only).
Rates control: FRED DFII10 (10y TIPS) **latest-vintage + corpus year-end
snapshots only ⇒ NOT PIT-strict** (DATACONTRACT §1.4 law; corpus file
DFII10_asof_2024-12-31.csv sha256 f56d598e…) — free daily real-yield
curve exists at treasury.gov (URL per GC_DOSSIER §6, not fetched this
lane); PIT-strict rate vintages = ALFRED year-ends only, sensitivity-
mandatory. No release-clock dependency (continuous feature).

**Field 4 — Bindings.** GC (COMEX): 100 oz, USD/oz, tick 0.1 = $10;
physical delivery; Globex 18:00→17:00 ET; last trade **12:30 CT third-
last business day of contract month**; official dates Aug 2013→Dec 2023
(2024-26 NOT_OBTAINED — §0.2); active cycle G/J/M/Q/V/Z; roll baseline =
last session before delivery-month day-1 with the **serial-months defect
declared** (6 serial contracts missing 2025-11→2026-09 ⇒ declared rule
not executable that span; cycle-skip approximation disclosed —
GC_DOSSIER §1) — a $0 re-fetch of 6 serials under existing entitlement
is the named unblock (NOT_RUN this lane). Unadjusted chains only;
back-adjustment NOT_RUN.

**Field 5 — Entry/stand-aside/exit [PROVISIONAL] (daily).** Condition:
compression state at close (strict past windows). Design frame:
calendar-spread DESCRIPTION FIRST (front-vs-next relative move, no PnL);
any outright directional variant is a second stage gated on stage-1
structure. Entry/exit: spread state at close t; exit at spread recovery
or 10 sessions [PROVISIONAL]. Stand-aside: roll weeks ±1 EXCLUDE (7-gap
anatomy contaminates spread levels); serial-gap span 2025-11→2026-09
flagged; holiday-uncertain days EXCLUDE.

**Field 6 — Baselines/placebo/negative controls.** (a) random-day placebo
with matched compression frequency (scored); (b) **rate-control leg**:
compression days explained by |ΔDFII10| beyond a trailing threshold
EXCLUDED — if the effect lives only there, rate-mechanical kill; (c)
seasonal placebo (month dummies — GC_DOSSIER H3 counter); (d) inverted
threshold (spread > 1.5× median) as the anti-state.

**Field 7 — Refutation conditions.** Mechanism: compression days with no
subsequent front outperformance (stage-1 descriptive kill); effect only
in the rate-explained subset (Field 6b kill); settlement-derived deep
bars misstate the curve pre-2025 (construction kill — restrict to
real-volume era, accept power NOT_RUN). Cost: 2 legs × §0.1 GC tiers —
a spread round trip pays 2 × 2 × (tier); stage-1 is descriptive so cost
kills apply only at the directional stage.

**Field 8 — Cost sensitivity.** MODELED COST ONLY; fees 2.51 UNDER
REVIEW; GC tiers 37.51/47.51/57.51 per side per leg.

**Field 9 — Regime/era breaks.** 22-month real-volume era inside a
30.7%-ann-vol regime (2026) — vol by year 2023 ~15% → 2026 30.7%
[OBSERVED §3]; settlement-derived long refs (GCZ5 2019-2026) usable for
level-vol description only. Era breadth NOT_RUN; the stress mechanism's
crisis-dependence explicitly declared unanswerable in-window.

**Field 10 — Coverage/hole proof.** HAVE: 22-contract panel (110 files),
real-volume chain 2025-01→2026-10, 7 roll gaps, BID/ASK 1Y proxies,
official dates 2013-2023, holiday times. HOLE: serial months (6
contracts), OI, intraday/overnight, BBO, EFP/lease rates (LBMA paid),
2024-26 official expiry dates, PIT-strict rate vintages (beyond year-ends).
**Intraday: NOTHING.**

**Field 11 — Sources per FACT.** Corpus `GC_*` 125 files (exemplar
sha256 c95a6db2…); treasury.gov real-yield curve URL (GC_DOSSIER §6, not
fetched); FRED DFII10 corpus snapshot sha256 f56d598e…; LBMA Gold Price
(free delayed, administered by IBA — per GC/SI dossier §4 lineage,
lbma.org.uk, accessed 2026-10-02, page bot-blocked then; NO purchases,
NO signups — delayed-free only). Curve anatomy: GC_DOSSIER §3 (sha256
3231d3a0…).

### GC-F2 — Roll-window liquidity-migration execution family

**Field 1 — Mechanism.** MECHANISM_HYPOTHESIS: liquidity providers widen
the dying contract's book before the delivery-month boundary; takers
rolling on the declared calendar date pay the calendar spread plus a
deteriorated old-contract book — a volume-crossover roll (switch at the
session the next contract's volume crosses, strict same-day-past data)
reduces effective crossing cost with no material exposure change.
OBSERVED anatomy [GC_DOSSIER §1/§3]: volume crossover **1-2 sessions
before the declared roll** at 5/6 real-era rolls (6th at roll; offsets
−2,−2,−2,−2,−1; e.g. 2026-03-27 GCJ6 8,201 vs GCM6 82,091); V-month
volume-scale vendor caveat declared (relative timing only, never absolute
liquidity). Predictive cost claim: NOT_RUN (no synchronous spread book).

**Field 2 — Expected direction (falsifiable).** Effective spread/roll
cost under volume-switch timing < calendar timing in ≥ half of future
rolls; exposure drift ≈ 0 (legs co-move; gap ≈ contango). Competitor:
the measured roll gaps are pure carry (gap ≈ 2m × 16 USD/oz) with
execution timing irrelevant — if timing difference ≤ noise, the family
dies as an execution improvement and remains a construction note.

**Field 3 — PIT availability.** Volume state: same-session cumulative
relative volume (strict past within session) or prior-session dailies —
computable from IBKR dailies in corpus; deeper OI-based rule NOT_RUN (no
OI field). No external clock.

**Field 4 — Bindings.** As GC-F1 (contract, 12:30 CT cessation, cycle
months, declared-roll baseline; serial defect declared). This family IS
a roll-rule comparison — per owner law the roll rule is CONSTRUCTION,
so this family can never be registered as alpha; it is an
execution-cost study feeding the cost model (H-G class).

**Field 5 — Entry/stand-aside/exit [PROVISIONAL].** No directional
trade: switch-date comparison designs (calendar T vs volume-crossover)
on the 7+3 measured/prospective rolls; measurement legs = close-proxy
BID/ASK medians per contract. Stand-aside: none (execution study);
holiday-adjacent rolls flagged.

**Field 6 — Baselines/placebo.** (a) T-5 and T+5 calendar variants
(timing placebo band); (b) quiet vs stressed month-ends split (2026-01-30
crash-week roll vs quiet rolls — regime leg); (c) SI-side same design as
cross-symbol corroboration (NOT registration).

**Field 7 — Refutation conditions.** Mechanism: old-book (spread/volume)
does not deteriorate pre-roll in ≥ half of rolls ⇒ LP-withdrawal story
dead; calendar ≡ volume rule (offsets collapse to 0) ⇒ nothing to
improve, family retires to construction note. Cost: any claimed
improvement must exceed the measured half-spread differences (close-proxy,
high-biased) — no measured-BBO statements permitted.

**Field 8 — Cost sensitivity.** MODELED only; this family PRODUCES cost
inputs rather than consuming them (declared).

**Field 9 — Regime/era.** 7 measured rolls in one vol regime; vendor
volume-scale defect (V-months) — declared; prospective accumulation
~6 rolls/yr.

**Field 10 — Coverage/holes.** HAVE: dailies + BID/ASK proxies + 7 gaps.
HOLE: serial months, synchronous BBO, OI, intraday roll-window detail
(NOT_RUN_DATA_ABSENT), pre-2025 rolls.

**Field 11 — Sources.** GC_DOSSIER §1 roll anatomy (sha256 3231d3a0…);
corpus `GC_*` files; FXCOMM §3 for the GC date law (sha256 0de05fa5…).

---

## 4. SI — silver 5,000 oz (2 families + 1 construction law)

### SI-F1 — GC-beta convexity in precious-metals momentum regimes

**Field 1 — Mechanism.** MECHANISM_HYPOTHESIS: SI shares the monetary
factor with GC with amplification ~2× (smaller market + retail leverage +
dealer inventory limits); in momentum/high-vol regimes the %-elasticity
is CONVEX (rises with |GC move|). OBSERVED anatomy [SI_DOSSIER §3]:
same-day corr **0.828** (rolling 63d 0.654–0.91, never near zero);
$-beta 0.010-0.057 (median 0.028) ⇒ elasticity ≈ **1.9% SI per 1% GC**;
GC/SI ratio traversed **44.00 → 92.79** in 7 months and mean-reverted
past median; 2026-01-26 full decoupling measured (ratio −44 while GC
rose) — the industrial-idiosyncrasy competitor instantiated once.
Convexity itself: **NOT_RUN** (regime split unmeasured; single squeeze
regime).

**Field 2 — Expected direction (falsifiable).** Conditional elasticity
increases in trailing-momentum states (strict past labels); after
normalizing by each leg's vol, SI's residual beta > 1 persists — the
built-in competitor (**vol-scaling artifact**, SI_DOSSIER §5 H4 counter)
predicts the apparent amplification vanishes under vol normalization.

**Field 3 — PIT availability.** Both legs = own per-contract dailies
(strict-past labels only); no external clock. Free corroboration legs:
LBMA Silver Price 12:00 London auction + LBMA Gold Price PM (free
delayed; ICE-administered — FACT per SI_DOSSIER §4 lineage, accessed
2026-10-02 via search index; LBMA page bot-blocked) — cash-leg
references inside Globex hours, usable as free daily confirmation, NOT
as fills.

**Field 4 — Bindings.** SI (COMEX): **5,000 oz class** (NOT 1,000 oz
SIL); USD/oz; tick 0.005 = **$25**; physical delivery; last trade
**12:25 CT** third-last business day of contract month (vs GC 12:30 —
official offset); official dates Mar 2015→Dec 2022 (2023-26
NOT_OBTAINED); **liquid cycle = H/K/N/U/Z measured** (serials dead: max
944 lots/RTH-day vs 26k-178k cycle; S1 nearest-expiry "front" (SIV6) is
NOT the liquidity front — SIZ6 was, 16.9k median lots) [OBSERVED,
SI_DOSSIER §1]; roll baseline = declared timing on cycle target; ~5.4
rolls/yr; unadjusted chains embed ~+0.97%/roll jumps — ±1-roll-day
exclusions mandatory; 6/6 measured migration ramps 2-7 days pre-roll.

**Field 5 — Entry/stand-aside/exit [PROVISIONAL] (daily).** This is a
cross-leg CONDITIONING family first: stage-1 = vol-normalized elasticity
by trailing regime (descriptive, 0 scored identities); stage-2
directional variant (long SI beta-scaled on GC-shock days) only if
stage-1 convexity survives, entry next close after GC shock label, exit
t+1..t+3 [PROVISIONAL]. Stand-aside: roll ±1 either leg EXCLUDE (25
flagged days in the measured window); squeeze-week outliers (8 of top-10
|moves| in 2025-12-20→2026-02-12) split-reported, never silently
dropped.

**Field 6 — Baselines/placebo.** (a) vol-normalization control (the
competitor's test — mechanical); (b) random-GC-day placebo same clock
(scored); (c) ratio-extreme anti-state (long SI/short GC at ratio rich —
H2 of the dossier, NOT registered, listed as the competing family
variant); (d) always-in beta-1 baseline.

**Field 7 — Refutation conditions.** Mechanism: elasticity < 1
persistently, or convexity absent across ≥2 regimes (needs depth —
NOT_RUN today, declared); vol-normalized residual beta ≈ 1 ⇒ artifact
kill; single-episode attribution (the Jan-2026 squeeze IS one event) —
any stage-2 claim from this window is auto-killed by the
single-regime law (§0.3). Cost: SI tiers are the binding element —
77.51/102.51/127.51 per side (4-tick $100 spread proxy, ~2× GC in
$/contract, OBSERVED §3) — a beta trade pays 2 legs; dies if the
conditional move ≤ 2×S2 round trips.

**Field 8 — Cost sensitivity.** MODELED COST ONLY; fees 2.51 UNDER
REVIEW; SI tiers above; slippage tiers {1,2,3}×$25 assumption — the
measured −14%/+13% overnight gaps imply execution risk no tick model
covers (honest floor, SI_DOSSIER §5 H5).

**Field 9 — Regime/era.** 15-month window IS one squeeze-bull-crash
regime (60.2% ann vol; skew −1.81; exkurt +15.2) — every statistic
carries the single-regime caveat [OBSERVED §3]. Regime split
NOT_RUN_DATA_ABSENT depth.

**Field 10 — Coverage/holes.** HAVE: 125-file panel, cycle chain 316
days, 6 roll gaps, ratio/beta table, liquid-era spread proxies, CPC/
LBMA clocks. HOLE: HG copper (industrial confirmation leg — vendor),
DXY (free FRED latest-vintage only), OI, intraday/overnight (gap std is
86% of daily std yet the session inside is invisible), 2023-26 official
expiry dates. **Intraday: NOTHING.**

**Field 11 — Sources.** SI_DOSSIER §3 cross-asset block (sha256
a15e5e23…); corpus `SI_*` 125 files (exemplar 5a594f7d…); LBMA Silver
Price clock: lbma.org.uk FAQ + ICE developer portal (accessed 2026-10-02,
SI_DOSSIER §4) — free-with-delay, no purchases/signups.

### SI-F2 — Curve-flip scarcity signal (contango → backwardation)

**Field 1 — Mechanism.** MECHANISM_HYPOTHESIS: SI's persistent contango
(measured 6/6 positive roll gaps, median +0.565 $/oz = 113 ticks =
$2,825/contract, mean +0.97%/roll ≈ +5.2%/yr — OBSERVED, SI_DOSSIER §1/
§3) inverts to backwardation only under physical scarcity (2020 EFP
episode precedent — POSTULATED, outside corpus); therefore a flip of the
adjacent-cycle spread to discount, or a compression below the carry-
implied level (rates + storage − lease), is a scarcity-stress signal
preceding front strength. The conditional content: NOT_RUN (6 rolls; the
flip itself never observed in-window). **Competitor built in: measured
gaps embed tail-book staleness (old leg 22-376 lots at roll) — the
staleness explanation predicts the gap is NOT informative.**

**Field 2 — Expected direction (falsifiable).** Spread ≤ carry-implied
floor (pre-declared from FRED short-rate proxy + storage assumption
[PROVISIONAL]) ⇒ front SI outperforms next over days-weeks; staleness
competitor predicts nothing after excluding thin-old-leg roll marks.

**Field 3 — PIT availability.** Curve: own dailies (corpus). Rates: FRED
SOFR/short-rate **latest-vintage, NOT PIT-strict** (DATACONTRACT law;
free). Lease rates: LBMA/IBA **paid** ⇒ NOT_RUN; the carry floor is
therefore a proxy floor [PROVISIONAL] — declared defect.

**Field 4 — Bindings.** As SI-F1 (cycle chain, 12:25 CT, ±1-roll-day
exclusions, back-adjustment mandatory for any level work —
unadjusted ~+1%/2-months jumps measured).

**Field 5 — Entry/stand-aside/exit [PROVISIONAL] (daily).** Stage-1
descriptive: gap-vs-carry-floor panel (0 identities). Stage-2
conditional variant only if a flip/compression is ever observed:
long front/short next, exit on spread normalization or 10 sessions.
Stand-aside: thin-old-leg marks (volume < threshold strict-past)
EXCLUDE — the staleness control is mandatory, not optional.

**Field 6 — Baselines/placebo.** (a) T-5/T+5 gap variants (staleness
control — SI_DOSSIER H3 counter-hypothesis); (b) carry-floor band
placebo (spread within normal band, random days); (c) GC-side same-
state corroboration (monetary-vs-industrial split).

**Field 7 — Refutation conditions.** Mechanism: gaps stay positive while
carry proxy is deeply negative ⇒ demand-pressure premium dominates, carry
story dead; flip never occurs through a full cycle of prospective
accumulation ⇒ unmeasurable, family retires to construction note; effect
vanishes under thin-leg exclusion ⇒ staleness kill. Cost: 2 legs × SI
tiers (§0.1); dies at S2 round trip × 2 legs.

**Field 8 — Cost sensitivity.** MODELED only; SI tiers; lease-rate hole
means the floor itself is an assumption — flagged as a second
sensitivity layer (floor ± bands).

**Field 9 — Regime/era.** One squeeze regime; 6 rolls; 2023-26 dates
NOT_OBTAINED (prospective roll dating relies on the third-last-BD rule
pending official captures — declared, no extrapolation into scored use).

**Field 10 — Coverage/holes.** HAVE: 6 gaps + cycle dailies + rates
(latest-vintage). HOLE: lease rates (paid), OI, intraday, pre-2025
front-scale curve (settlement marks only), official 2023-26 dates.

**Field 11 — Sources.** SI_DOSSIER §1/§3 (sha256 a15e5e23…); FRED SOFR
URL lineage (SI_DOSSIER §6 — free, not fetched this lane); corpus `SI_*`.

### SI-F3 — CONSTRUCTION LAW (not a hypothesis): cycle chain + serial exclusion + S1-front hazard

Declared: nearest-H/K/N/U/Z holding with declared-roll timing is the
binding universe rule (serials measured dead; S1 "front" ≠ liquidity
front); back-adjustment mandatory for level/trend work; the +0.97%/roll
gap is carry, not PnL. Any future SI family inherits these laws
(SI_DOSSIER H1, owner construction-rule law).

---

## 5. Per-symbol summary (outcome-blind)

| symbol | families | headline mechanism | status today |
|---|---|---|---|
| NG | **2 competing** (F1 storage-surprise vs F2 forecast-revision) + F3 construction | release-embedded free consensus (The Desk) vs weather-information flow | designs PROVISIONAL; **F1 math blocked by r-1 (unsigned survey — confirmed column-level)**; F2 revision-leg computable, error-leg NOT_RUN_DATA_ABSENT; both price-gated to 14m/extension |
| CL | **2 competing** (F1 WPSR surprise-resolution vs F2 conflict-reversal) + cost-law | naive-surprise continuation vs headline-vs-Cushing reversal on one event set | designs PROVISIONAL; no free consensus (measured) ⇒ naive-proxy freeze required; intraday variants NOT_RUN_DATA_ABSENT |
| GC | 2 (F1 curve-compression stress; F2 roll-migration execution) | full-carry flattening = urgency bid; LP book withdrawal at roll | evidence-thin class: anatomy committed single-era; F1 power NOT_RUN (~40 weekly obs); F2 is construction/cost input, never alpha |
| SI | 2 (F1 beta convexity; F2 curve-flip scarcity) + F3 construction | 2× monetary amplification (vs vol artifact); contango flip = scarcity | evidence-thin class: single squeeze regime; convexity/flip NOT_RUN; serial/cycle laws binding |

**No family is registered, enumerated for scoring, or scheduled. No
qualification upgrade claimed. NOT_QUALIFIED_V2 stands for all four
symbols.**

---

## 6. Cross-family adjudication map (registered competitors)

- NG: F1 vs F2 share the Thursday-week event space — F1's Field 6c =
  F2's state and vice versa; both must be registered together in any
  future cycle (falsification-by-competitor).
- CL: F1 continuation vs F2 conflict-reversal adjudicated on ONE frozen
  event set with pre-registered conflict split.
- GC: F1's rate-mechanical competitor uses the same DFII10 series as
  F2's cost inputs — one rates dependency, declared once.
- SI: F1's vol-artifact control and F2's staleness control are the
  registered negative controls; both feed the same two-leg cost table.

## 7. Source register (all sha256 = sha256, this lane, `captures/source_sha256.tsv`)

| # | artifact | sha256 (first 8) | role |
|---|---|---|---|
| 1 | dossiers/{CL,NG,GC,SI}_DOSSIER.md | d85927f3 / cabb5716 / 3231d3a0 / a15e5e23 | 14-month anatomy, cost proxies, bindings |
| 2 | PLAYBOOKS_DRAFT.md / DATACONTRACT_QUALIFICATION.md | 7610ed3c / df175a2d | NOT_QUALIFIED_V2 verdict, H-G construction law, cost law |
| 3 | FEES_CORRECTED.md | 006d6372 | corrected all-ins (under review) |
| 4 | FXCOMM_GAPFILL_EVIDENCE.md | 0de05fa5 | GC/SI dates to 2023/2022, holiday times 2011-23 |
| 5 | COMM_CALENDAR_EVIDENCE.md | adcd3b54 | CL/NG rules verbatim + 183/240-month tables |
| 6 | eia_wngsr_vintages_tidy.parquet | 3914729f | 1,205 vintages + survey cols (r-1 evidence) |
| 7 | eia_wpsr_vintages_tidy.parquet | ba439c60 | 790 crude+Cushing vintages |
| 8 | eia_wpsr_tables_tidy.parquet | d579fd86 | tables normalization |
| 9 | noaa_cpc_issued_forecast_inventory.parquet | 2d8f68c5 | 4,555 issued vintages |
| 10 | noaa_observed_popweighted_hddcdd.parquet | 2c54c854 | monthly observed (error-leg blocker) |
| 11 | wngsr/issues/2025_10_30.html | ff544642 | The-Desk verbatim sample |
| 12 | wngsr/issues/2017_05_11.html | 408e8ef7 | earliest Desk mention |
| 13 | wpsr/issues/wpsr_2026_09_30.html | 8de87d99 | no-consensus measurement |
| 14 | wpsr/tables/2011_08_03_ttable4.csv | 4b4f3963 | Cushing-line exemplar |
| 15 | DFII10_asof_2024-12-31.csv | f56d598e | rates control (year-end vintage, not PIT-strict) |
| 16 | AV1T-definition-ALL10 …metadata.json | d431a38d | vendor scope law (metadata-only for comm) |
| 17 | IBKR raw exemplars CL/NG/GC/SI TRADES_1day_6Y | f0b47fef / 9d7755d2 / c95a6db2 / 5a594f7d | 14-22m price legs |

URLs (all accessed 2026-10-02/03 by their original lanes; none fetched
this lane — re-fetch with archive timestamps when used):
eia.gov/naturalgas/storage/ + /petroleum/supply/weekly/schedule.php ·
eia.gov/dnav/ng/ng_pri_fut_s1_d.htm · eia.gov/dnav/petroleum/pet_pri_spt_s1_d.htm ·
cpc.ncep.noaa.gov/products/predictions/6_10day/ · federalreserve.gov/monetarypolicy/fomccalendars.htm ·
bls.gov/schedule/news_release/cpi.htm · cftc.gov/MarketReports/CommitmentsofTraders/ ·
lbma.org.uk (Gold/Silver Price, free delayed) · developer.ice.com (IBA) ·
home.treasury.gov real-yield curve · fred.stlouisfed.org (DFII10/SOFR).

— End of COMM_HYPOTHESES.md. Outcome-blind; no return statistic was
computed or used; missing evidence is NOT_RUN everywhere.
