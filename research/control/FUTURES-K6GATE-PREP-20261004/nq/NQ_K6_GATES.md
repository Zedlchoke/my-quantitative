# NQ_K6_GATES — lane NQ-K6, round FUTURES-K6GATE-PREP-20261004

Lane: NQ-K6. Worktree `.worktrees/futures-k6gate/prep`, branch
`prep/futures-k6gate-20261004`, base/actual_start HEAD
`05e5493971116eec8db5ea49e30c06930e8cc6bc` (verified at lane start via a single
`git rev-parse HEAD`; `git status --porcelain` clean except this control dir).
Data: cache_v3 ONLY —
`research/control/FUTURES-SIX-READINESS-20261004/nq/cache_v3/`
(`nq_outright_1m_v3.parquet` 6,780,608 rows; `nq_annotated_1m_v3.parquet`
6,780,608 rows; `nq_sessions_v3.parquet` 11,715 rows;
`held_volume_k5_v3.parquet` 4,219 rows). Chain law: cache_v3 only; the D9
candidate is pending and never treated as canonical; pre-v3 caches never
touched. Zero-fetch lane: NO network was used; every input is an in-repo
committed artifact or the read-only root data plane already committed to the
repo's evidence index. Zero PnL: every statistic below is an unconditional
descriptive anatomy statistic (volume counts, |1m log return| dispersion, bar
counts, range aggregates). No PnL, no expectancy, no conditional-on-signal
measurement, no parameter selection, no family change. A gate result never
changes family/parameters — it only adjudicates the pre-declared gate
condition.

Shas of cited committed artifacts (computed by this lane at start,
sha256/first 8):
- `NQ_a4_events.json` = 5a09aff9 (matches ESNQ_HYPOTHESES field 11 citation)
- `NQ_a1_regimes.json` = 66efedc7 (matches NQ-F3 field 11 citation)
- `NQ_a2_sessions.json` = ce326ea4
- `ES_fomc_stats.json` = 228fe2d4 (matches ES-F1 field 11 citation)
- `nq_cal_coverage.json` = ad7f4b3a (FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/cme_cal/nq_es/)
- `bls_dates.json` = ad41d2a7 (matches ES-F2 field 3 citation)
- `COST_FREEZE_ERRATUM.md` = cf83bc2d
(No fee/number appears in any gate statistic below; this lane is
cost-irrelevant — anatomy only. The erratum citation is recorded for
completeness because the dispatch cost-law clause applies to any fee citation;
none is made.)

---

## §0 PREDECLARATION (written and committed to disk BEFORE any compute)

Every statistic below was declared here first; the compute ran only after this
section was saved. Where the owning family doc leaves a threshold implicit,
the operationalization is marked **[OPERATIONALIZED]**.

### §0.1 M1 — NQ-F1 K6 anatomy reproduction pre-gate

Owning doc: `research/control/FUTURES-OVERNIGHT-PREP-20261003/hypo/es_nq/ESNQ_HYPOTHESES.md`,
family NQ-F1 `FOMC-ERA`, field (7) states: "**K6 anatomy reproduction
pre-gate.**" — which invokes the shared F1-K6 definition in the same file
(shared refutation block, first family section), quoted verbatim:

> "**F1-K6 anatomy reproduction gate (pre-scoring)**: re-measured on the
> era-correct session mapping, the release bucket must again show ≥2×
> volume and pre-release ≤0.85× suppression; if the committed anatomy fails
> to reproduce, family never enters scoring [construction gate]."

Committed anatomy being reproduced (NQ_a4_events.json 5a09aff9,
`fomc_2pm_release_windows`): m60_0 vol_ratio_median **0.683×**, h0_30
**2.256×**, h30_60 **2.637×**, release-minute **3.53×**; era table
2016-19/2020-22/2023-26 h0_30 vol 2.99→2.25→1.46, m60_0 0.80→0.79→0.59.

Exact statistics re-measured on cache_v3 (mirroring the committed a4 recipe
verbatim, `NQ_a4_events.py` sha-recorded in that directory):
- Event set: FOMC statements with primary-source 'For release at 2:00 p.m.
  ET' proof (read from the committed read-only statements archive the a4
  script used: `~/.my-quantitative-data/futures-nonprice-10syms/fed/statements/monetary*.html`,
  147 files), session present in the held k=5 chain
  (held_volume_k5_v3), session `rth_coverage ≥ 0.6` (the family's standard
  clean-session threshold). 14:00 ET ≡ 13:00 CT release minute = minute-of-day 780.
- Windows (CT minute-of-day, [start, end)): pre-release m60_0 = [720, 780);
  release bucket h0_30 = [780, 810); h30_60 = [810, 840); release minute = 780 exactly.
- Per event: vol_ratio_w = (event-day window volume sum) / (median over
  control sessions of same-window volume sum). Controls: same weekday within
  ±21 calendar days, non-FOMC-day, held, coverage ≥ 0.6 (identical to the
  committed control string "same weekday within +-21d, non-event, clean
  sessions").
- Headline statistic: MEDIAN of per-event ratios per window (full-era, all
  qualifying events pooled), plus the same per data-era (2016-19, 2020-22,
  2023-26) as descriptive reference rows.
- |1m ret| and range ratios computed identically (absr_ratio = mean |1m log
  close-to-close ret| in window / median over control sessions of per-session
  mean |1m ret|; rng_ratio = window high−low / median control) and reported,
  but the GATE binds on the volume ratios only (the gate sentence names
  volume and suppression, both volume-based).

**GATE condition (pre-declared):** PASS iff full-era
`vol_ratio_median(h0_30) ≥ 2.0` AND `vol_ratio_median(m60_0) ≤ 0.85`; else
FAIL. [OPERATIONALIZED]: "release bucket" = h0_30 (0..+30 min), the committed
2.256× row; "pre-release" = m60_0 (−60..0), the committed 0.683× row the doc
calls "deepest measured window". The gate is adjudicated on the full-era
pooled median (the gate sentence is a single reproduction statement); per-era
rows are reported but do not each have to pass (the era table is the
pre-registered K1 reference, not the K6 binding). NOT_RUN if < 20 qualifying
events (power floor declared here; committed n=84).

### §0.2 M2 — ESNQ-F5 EXPWITCH F5-K6 anatomy pre-gate (NQ leg)

Owning doc: `research/control/FUTURES-TEN-HYPO-PREP-20261004/es_nq/HYPOTHESES_ESNQ_R3.md`,
§2 ESNQ-F5 `EXPWITCH`, field 7, quoted verbatim:

> "**F5-K6 anatomy pre-gate (construction gate, 0 identities,
> PREP-legal)**: before any scoring is ever proposed, (i) the
> witching-Friday session anatomy must be measured on the era-correct
> mapping and show elevated close-window volume/activity vs matched
> ordinary Fridays **in the modern eras**; (ii) held-chain session
> integrity on expiry Fridays must pass (no phantom gaps; switch-day
> audit law NEW-4 inherited for the NQ leg). Failure ⇒ the family
> never enters scoring."

Day-classes (pre-declared):
- W (witching) = the 68/68 NQ quarterly expiration Fridays from
  `nq_cal_coverage.json` `expirations.per_year` (36 product-specific + 32
  family-level, cross-check "zero divergence", verdict
  PASS_WITH_COVERAGE_68_OF_68_QUARTERS). Calendar reuse declared as-is; no
  derivation.
- O (ordinary) = all other held Fridays in the same tri-era, EXCLUDING
  Fridays that are FOMC statement days (132-statement date set from the same
  archive the a4 loader reads) or CPI/EMPSIT scheduled-release days
  (bls_dates.json) — declared exclusion, mirroring the family's law that
  "FOMC/macro clocks are excluded by law" and NC-1's "matched ordinary
  Fridays" (a matched clock must not carry another family's event).
- Tri-eras (family field 9): 2010-16 / 2017-21 / 2022-26 ("modern eras" =
  2017-21 and 2022-26 [OPERATIONALIZED — the doc does not define "modern";
  the two most recent tri-eras are the only reading consistent with a
  participation-era mechanism]).

Statistics (unconditional anatomy, per class × era, on held-chain sessions,
clean coverage ≥ 0.6 for share statistics; integrity stats use all held
sessions):
1. Session volume distribution: median, p25, p75, n of held-session total
   volume; plus era-normalized median (class median / era O median).
2. |1m log ret| dispersion (bp): per-session mean of |1m close-to-close|
   (contract-internal diff; first bar of each contract NaN), aggregated as
   median across sessions; full session and close window.
3. Close-window anatomy: close window = the last 60 tradable minutes of the
   session's own era-correct close span (close minute per the measured era
   law: 16:15 CT through 2015-09-18, 16:00 CT from 2015-09-21; era-A
   Friday-15:15 sessions handled per-session by their own measured last
   minute) — volume share of session and |1m ret| median. [OPERATIONALIZED]
4. Per-segment bar counts: session n_bars and rth_bars distributions
   (median, p10, n) by class × era.
5. (ii) integrity: for every expiry-Friday held session — (a) phantom-gap
   check inside the RTH span 08:30 CT→era close: largest run of missing
   consecutive minutes; [OPERATIONALIZED threshold: pass requires gap ≤ 5
   minutes and rth_bars ≥ 0.8 × span] ; (b) NEW-4-class switch-day
   descriptive: |overnight gap| (log held close(t−1)→close(t) across the
   maintenance break, i.e. session-to-session close diff on the held daily
   series) on roll switch days vs non-switch days — median, p90, n (66
   rolls). "Indistinguishable" operationalized descriptively: switch-day
   median within 2× non-switch median ⇒ no flag raised; the standing NEW-4
   law remains binding on any future run regardless.

**GATE condition (pre-declared):** part (i) PASS iff, in BOTH modern tri-eras
(2017-21, 2022-26), W/O ratio > 1.0 for close-window volume share AND > 1.0
for close-window |1m ret| median. [OPERATIONALIZED: "elevated" = ratio > 1.0
on both activity measures; the doc states no numeric threshold.] Part (ii)
PASS iff no expiry-Friday held session fails the phantom-gap check (switch-day
descriptive reported, flag noted, not a pass/fail leg — the doc binds (ii) on
phantom gaps and invokes the NEW-4 law for runs). Failure of (i) or (ii) ⇒
gate FAIL (family never enters scoring — recorded, never acted on here).

### §0.3 M3 — session dispersion re-derivation on cache_v3 (descriptive rebuild, no gate)

Declared statistic set (mirrors what NQ families' D5/power honesty consumes,
re-derived on v3 for the full era): per held session (4,219):
- `n_bars_rth` (consecutive-minute RTH bars), `n_bars_session`;
- `absret_median_bp` = median |1m close-to-close log ret| (bp) over
  contract-internal consecutive minutes (first bar of each contract NaN),
  full session and RTH-only;
- `absret_sd_bp`, `absret_mean_bp`;
- `rth_close_series_sd_bp` = sd of 5-minute non-overlapping RTH close log
  returns ×√(78) dailyization proxy — declared as the per-session RTH
  dispersion measure comparable to committed `sd_rth_pct` family tables.
Aggregates: per calendar year and full era — n sessions, median/p25/p75 of
each per-session measure; plus dedicated reporting of the 2020-03-23..
2020-05-29 vendor-hole window now covered by the repaired chain.
Comparison artifact (cite, do NOT overwrite):
`NQ_a2_sessions.json` (ce326ea4) `era_segments`/`minute_profiles`/`rth_hourly`
— built on the pre-recovery series with the hole SKIPPED (era split
2017-01_2020-02 | 2020-06_2022-12); deltas shown per era where comparable.
No gate condition — descriptive rebuild only.

### §0.4 M4 — NQ-F3 a1/a2 aggregate rebuild on cache_v3 (descriptive rebuild, no gate)

Owning doc: ESNQ_HYPOTHESES.md NQ-F3 field (1) honest disclosure + field (2)
"**NQ-F3-K6 anatomy pre-gate = the full-era rebuild itself** plus the
intraday-placement measurement"; NOT_RUN register item 7: "NQ full-era rebuild
on alias-recovered series: outstanding — hard precondition for NQ-F3,
inherited by NQ-F2/F4 aggregates." The a1/a2 tables are defined by
`NQ_DEEPFOUR_V3_ADDENDUM.md` (§ panel: "a1" = `NQ_a1_regimes.json` held-chain
daily aggregates, NaN-aware, 4,219 held sessions; "a2" =
`NQ_a2_sessions.json` session-structure aggregates, 4,016 clean RTH sessions
of 4,170 at coverage ≥ 0.6).

Rebuild scope (recipes mirrored VERBATIM from the committed generator scripts
`NQ_a1_regimes.py` / `NQ_a2_sessions.py`, inputs swapped to cache_v3):
- a1 on v3: held daily series (right-merge keeps hole sessions as NaN closes
  — diff yields NaN, never a synthetic jump); realized_vol_summary
  rvol_{5,10,20,60,120,252}d (min/p5/p25/median/p75/p95/max/argmin/argmax/last);
  vol_clustering (acf1_abs_ret_252d_median, vol20_of_vol20); trend_persistence
  (acf1_ret_full, rolling-252 median + p10/p90, variance_ratios_full
  VR5/20/60 = mean of last 252 rolling values, VR20 median + p10/p90);
  drawdowns ≥ 10%; yearly anatomy; strict-past vol-tercile and 120d-t
  trend-regime labels; v1_window_context. `calendar_rule_sensitivity` needs
  the calendar-rule held chain which cache_v3 does not ship as a parquet —
  rebuilt from `contract_registry_v3.json` if feasible, else declared
  NOT_RUN with reason.
- a2 on v3: held/clean/excluded counts at coverage ≥ 0.6; era_segments on
  the SAME five committed era windows (for before/after comparability) PLUS
  the hole window 2020-03-01..2020-05-31 as its own new row; yearly_overnight_share;
  minute_profiles (vol_share_by_minute + absret_by_minute) per era, with the
  hole window included in an era view that the pre-v3 table could not
  produce (2020-03..05 profile); rth_hourly; friday_early_close_eraA;
  holiday_short_sessions.
This is descriptive aggregation of daily/session/1m anatomy. NOT the
family's run-reversal signal computation: no k-run conditioning, no RR
signal, no PnL anywhere.

### §0.5 M5 — NQ-F2 07:30-by-era check (K6 anatomy gate)

Owning doc: ESNQ_HYPOTHESES.md NQ-F2 `MACRO-0730-NQ`, field (7): "**K6
anatomy gate (07:30 spike reproduction per scoring era)**"; field (3):
"NQ-side per-era spike anatomy 2010-16: NOT_RUN (must be measured; only
2017-20 vs 2023-26 contrast committed)"; field (9): "Scoring era gated by
anatomy (2023-26 on committed evidence)". Committed evidence
(NQ_a4_events.json `cpa_nfp_status.calendar_free_evidence_0730ct`,
calendar-free, 2023-26 era): share_0730 **0.00185** vs share_0725
**0.00041** (≈4.5× neighbor); quiet 2017-20 era share 0.088%, |ret| 0.031%.

Anchor note (declared): the dispatch packet says "07:30 ET window"; the
family's committed anchor is **07:30 CT** (= 08:30 ET release slot,
`calendar_free_evidence_0730ct` note verbatim). This lane uses the family's
07:30 CT anchor (minute-of-day 450); reading the packet as 07:30 ET = 06:30
CT would contradict the committed evidence table and is rejected.

Cells (pre-declared): eras **2010-16 / 2017-20 / 2023-26** (mirrors the
committed contrast; 2010-16 is the must-measure cell) × day-classes:
- calendar-free: all held sessions with coverage ≥ 0.6 in the era
  (direct reproduction of the committed table's class);
- release-day: CPI ∪ EMPSIT scheduled dates from `bls_dates.json`
  (204 + 204, all 08:30 ET, vintage-law decision-date-keyed; canceled-but-
  expected 2025 days reported separately, never pooled into the main cell);
  control = same weekday within ±21d non-release held sessions.
Statistics per cell: minute-volume share at 07:25/07:30/07:31 CT
(share = era-minute volume / era total, or session-level share then median
for release cells), spike ratio share_0730/share_0725, |1m ret| at 07:30
(mean, bp), release/control ratio of 07:30 volume share. n per cell reported.

**GATE condition (pre-declared):** PASS iff the scoring era 2023-26 shows a
reproduced spike on the calendar-free class: `share_0730/share_0725 ≥ 2.0`
[OPERATIONALIZED: "spike" threshold 2× neighbor, anchored on the committed
≈4.5× and the family's own "≈4.5× neighbor" framing; 2× is the minimal
reproduction reading]. The 2010-16 and 2017-20 cells are the declared
mechanism-contrast descriptive views (a null there is mechanism-consistent
per field (2) and never fails the gate). Release-day cells are reported per
the dispatch but are secondary to the gate (the committed evidence class is
calendar-free). NOT_RUN for any era the committed BLS calendar cannot fill
(expected: none — years_covered 17 for both series).

### §0.6 Anti-cherry-pick register — measurements considered and NOT run

Declared before compute; nothing below was measured in this lane:
1. Any ES-side leg of F5-K6 (ES quota; this lane is NQ only).
2. FOMC minute anatomy 2011-2015 (statements carry no release-time line;
   day-level only — committed NOT_RUN, respected).
3. Monthly-opex dose stratum of EXPWITCH (options-side calendar
   NOT_OBTAINED/BLOCKED_TRANSPORT — derivation forbidden).
4. Surprise/consensus or release-direction conditioning anywhere (no PIT
   consensus archive; H3 blocker).
5. Any signed-return, conditional-on-signal, delay-pair, placebo-clock or
   PnL statistic (the scored identities of all five families) — zero-PnL
   law; only the anatomy tables above.
6. ES-side 07:30 anatomy (ES lane's scope).
7. Roll-week × session-type interaction (NQ-F4 Role B NOT_RUN) — not this
   lane's gate; only the NEW-4-class switch-day descriptive inside M2(ii).
8. 2026 Globex-uncertain days: excluded fail-closed everywhere (committed
   NOT_OBTAINED law); NQ early-close-untranscribed days enter only through
   per-session measured coverage, never as asserted sessions.
9. calendar_rule_sensitivity a1 row IF the calendar chain cannot be rebuilt
   from cache_v3 alone (will be declared in §4 with the actual outcome).
10. Any comparison of cache_v3 vs the D9 candidate (not canonical; never
    touched).

---
(COMPUTE RESULTS APPENDED BELOW IN §1-§6 — nothing above this line was
modified after compute began.)

---

## §1 M1 result — NQ-F1 K6 anatomy reproduction pre-gate: **PASS**

Artifact: `m1_fomc_anatomy_v3.json` (recipe mirror of NQ_a4_events.py on cache_v3).

n = 85 qualifying 2:00 p.m.-ET events (of 85 timed-14:00 statements; committed
n was 84 — the repaired chain admits exactly one additional event,
2020-04-29, whose held session NQM0_2020 has coverage 1.0 on v3 and had no
front-contract bars pre-repair; ≥ 20 power floor).

Full-era window medians (rebuild vs committed 5a09aff9):

| window | vol_ratio | absr_ratio | rng_ratio | committed vol | committed absr |
|---|---|---|---|---|---|
| m120_60 | 0.802 | 0.849 | 0.837 | 0.799 | 0.853 |
| **m60_0 (pre-release)** | **0.686** | 0.850 | 0.816 | **0.683** | 0.853 |
| **h0_30 (release bucket)** | **2.230** | 2.240 | 2.618 | **2.256** | 2.278 |
| h30_60 | 2.614 | 2.529 | 2.753 | 2.637 | 2.544 |
| h60_120 | 1.440 | 1.659 | 1.752 | 1.445 | 1.659 |
| h120_180 | 1.339 | 1.498 | 1.620 | 1.336 | 1.477 |
| release minute | 3.506 | — | — | 3.527 | — |

Era table (rebuild vs committed):

| era | n | h0_30 vol | h0_30 absr | m60_0 vol | committed (n, vol, absr, m60_0) |
|---|---|---|---|---|---|
| 2016-19 | 32 | 2.987 | 2.253 | 0.802 | 32, 2.987, 2.253, 0.802 (identical) |
| 2020-22 | 23 | 2.222 | 2.257 | 0.788 | 22, 2.253, 2.439, 0.786 |
| 2023-26 | 30 | 1.456 | 2.236 | 0.593 | 30, 1.456, 2.236, 0.593 (identical) |

2016-19 and 2023-26 rows are bit-identical to the committed table (inputs
unaffected by the alias repair); the 2020-22 row shifts by the one recovered
event and the relabelled 2018-08..2020-05 sessions.

**GATE adjudication (§0.1):** h0_30 vol_ratio_median = 2.230 ≥ 2.0 AND
m60_0 vol_ratio_median = 0.686 ≤ 0.85 ⇒ **PASS**. The committed FOMC anatomy
reproduces on the era-correct (cache_v3) session mapping. This adjudicates
only the K6 gate; it says nothing about any scored arm.

## §2 M2 result — ESNQ-F5 EXPWITCH F5-K6 (NQ leg): **FAIL** (part (ii); part (i) PASS)

Artifact: `m2_expwitch_anatomy_v3.json`.

Classes: W = NQ quarterly expiry Fridays (68/68 calendar ad7f4b3a; 66 have
held sessions — 2010-03-19 predates panel start 2010-06-07, 2026-12-18
postdates data end 2026-10-01); O = other held Fridays in era excluding FOMC
and CPI/EMPSIT dates. Tri-eras per family field 9.

**(i) close-window anatomy (clean sessions):**

| era | W n (held/clean) | O n (held/clean) | vol ratio W/O | close-window vol-share ratio | close-window absret ratio | full absret ratio |
|---|---|---|---|---|---|---|
| 2010-16 | 27/27 | 215/206 | 1.139 | 1.142 | 1.225 | 1.027 |
| 2017-21 | 20/20 | 164/158 | 0.988 | **1.271** | **1.184** | 0.915 |
| 2022-26 | 18/18 | 167/160 | 1.026 | **1.142** | **1.159** | 0.978 |

Part (i) pre-declared condition: close-window volume-share ratio > 1.0 AND
close-window |1m ret| ratio > 1.0 in BOTH modern eras ⇒ 1.271/1.184 (2017-21)
and 1.142/1.159 (2022-26) ⇒ **part (i) PASS**. (Total-session volume is NOT
elevated — vol ratio ≈ 1.0 and full-session |ret| ratio < 1 — the elevation
is close-window concentrated, which is what the gate names.)

**(ii) held-chain session integrity on expiry Fridays:**

- 66/66 in-window expiry Fridays have held sessions (coverage complete for
  the observable window).
- Phantom-gap check (pre-declared [OPERATIONALIZED]: any session with an
  RTH-span gap > 5 min or present < 0.8 × span fails): **35/66 FAIL**.
  Failure years: 2012(1), 2013-2020(4 each), 2021(2); gap sizes 15 min
  (34) / 14 min (1).
- Post-hoc diagnostic (declared here as diagnostic, NOT a gate leg; same
  statistic, seed-20261004 sample of 80 non-expiry held Fridays): **46/80
  fail** — a HIGHER failure rate than expiry Fridays (53.0% vs 57.5%). The
  15-minute gap signature is a panel-wide property of the committed 1m data
  from 2013 through 2021 (the FIX/FAST-era vendor convention caveat committed
  in the a2 header), present equally on ordinary days. It is NOT an
  expiry-specific or held-chain artifact, and cache_v3's repair scope
  (alias window 2018-08..2020-05) never targeted it.
- NEW-4-class switch-day descriptive: |overnight close-to-close gap|
  switch vs non-switch = median 76.8 bp vs 62.4 bp (ratio 1.23×, p90 223 vs
  200 bp, n 66/4152) ⇒ below the pre-declared 2× flag threshold, no flag.

**GATE adjudication (§0.2):** the pre-declared part (ii) condition is "no
expiry-Friday held session fails the phantom-gap check". 35 fail ⇒ **part
(ii) FAIL** ⇒ **F5-K6 (NQ leg) = FAIL** under the condition as declared.
Recorded interpretation for the owner (this lane changes nothing): the
failing signature is era-generic committed-data granularity (2013-2021), not
witching-day anatomy; resolving it is a data-plane decision outside this
lane's authority. Until then the gate stands as measured: FAIL — the family
never enters scoring on the NQ leg per the owning doc's own consequence
clause.

## §3 M3 result — session dispersion re-derivation on cache_v3 (descriptive, no gate)

Artifacts: `session_dispersion_v3.json` + `session_dispersion_v3_per_session.parquet`
(4,219 held sessions, 2010-06-07..2026-10-01).

Full-era per-session medians: |1m ret| mean 1.71 bp / median 1.09 bp / sd
1.99 bp; RTH-only median 2.11 bp; RTH 5-min dailyized sd 71.1 bp.
Per-year tables in the JSON (e.g. 2020: mean 2.47 bp, RTH 5-min sd 103.2 bp,
n=260 — the first year-row to include March-May 2020).

**The repaired window**: 2020-03-23..2020-05-29 (the pre-v3 vendor hole) now
has 49 measured sessions — |1m ret| mean 3.60 bp (p25-p75 2.83-5.20), median
2.62 bp, sd 3.76 bp. Under pre-v3 aggregates this window did not exist.

Comparison vs the committed pre-v3-derived table (NQ_a2_sessions.json
ce326ea4; cited, NOT overwritten):

| row | committed (pre-v3) | cache_v3 rebuild | delta |
|---|---|---|---|
| held sessions | 4,170 | 4,219 | +49 (hole sessions real) |
| clean sessions (cov ≥ 0.6) | 4,016 | 4,065 | +49 |
| era 2017-01_2020-02 n / ovn_share / avg vol | 781 / 0.18624 / 387,501.9 | 781 / 0.18624 / 387,502 | identical |
| era 2020-06_2022-12 n / ovn_share / avg vol | 649 / 0.21207 / 565,906.9 | 649 / 0.21207 / 565,931 | avg vol +24 (≈0.004%): relabel-affected 2020-06-01..05 cutover sessions |
| era 2020-03..05 | not present (hole skipped) | 63 clean sessions, ovn_share 0.267, avg vol 520,068 | NEW row |
| yearly ovn 2019 | 0.22451 | 0.22451 | identical |
| yearly ovn 2020 | 0.23841 (hole excluded) | 0.24374 (hole included) | +0.0053 — the hole weeks were higher-ovn |
| committed "quiet era" 07:30 share 2017-01_2020-02 | 0.000883 (share_450) | 0.000883 | identical |

Everything outside the repair window reproduces the committed table to
reported precision; the only deltas are the recovered window itself.

## §4 M4 result — NQ-F3 a1/a2 full-era rebuild on cache_v3 (descriptive, no gate)

Artifact: `nq_f3_rebuild_a1a2.json` (schema nq_f3_rebuild_a1a2_v3@1; recipes
mirrored verbatim from NQ_a1_regimes.py / NQ_a2_sessions.py; inputs swapped
to cache_v3; right-merge keeps hole sessions as NaN closes so diffs never
bridge the hole synthetically). Row counts: held daily series 4,219 rows
(4,218 non-NaN rets), 66 rolls; per-session 1m anatomy 4,219 rows.

**Independent cross-check**: the rebuild's daily ret series matches the
readiness lane's `nq_held_daily_v3.parquet` with **max |diff| = 0.0 over all
4,218 overlapping non-NaN rets** — two independent implementations of the
chain → identical series.

Reconciliation vs the documented pre-v3 hole-era values (committed
NQ_a1_regimes.json 66efedc7):

| statistic | committed (pre-v3) | cache_v3 full-era rebuild | note |
|---|---|---|---|
| panel n_sessions / rolls | 4,219 / 66 | 4,219 / 66 | same frame, different closes in hole window |
| depleted_sessions | 77 | **27** | 50 hole-window sessions no longer NaN/thin |
| acf1_ret_full | −0.0758 | **−0.0857** | mean-reversion substrate STRONGER after repair |
| acf1 rolling-252 median (p10-p90) | −0.0418 (−0.134..+0.071) | −0.0459 (−0.174..+0.069) | |
| VR(5/20/60) full | 0.8080/0.7113/0.6688 | 0.8080/0.7113/0.6688 | identical (last-252d mean = 2025-26, outside repair window) |
| VR20 median (p10-p90) | 0.6915 (0.522..0.850) | 0.6998 (0.531..0.849) | |
| rvol20 max (argmax) | 0.9241 (2020-03-27) | 0.8865 (2020-03-30) | hole no longer distorts the vol peak |
| worst 2020 day | −11.15% | −11.15% | identical |
| 2020 max DD | 32.28% | **34.12%** | now EQUALS the NQ2020_ADDENDUM recovered-episode figure (−34.12% DD, worst day −11.15%) cited in NQ-F3(7) — the addendum number and the full-era rebuild reconcile |
| 2020 vol_ann / ret_pct | (hole-year) | 34.82% / +38.43% | |
| calendar-rule sensitivity vol_ann | 19.62% (n=4,155) | 19.84% (n=4,219) | v1-rule chain rebuilt from contract_registry_v3 (109 usable registry rows; 4 dropped for missing expiry, 4 for missing contract — disclosed) |
| regime_trend counts (range/up/down) | 2549/1555/64 | 2564/1590/64 | |
| a2 clean sessions | 4,016 | 4,065 | +49 |
| era segments (unaffected eras) | — | identical to committed | see §3 table |
| hole-window era_segments row | absent | 2020-03_2020-05: 63 clean sessions | NEW |

F3 hard-precondition status: the "full-era rebuild on the alias-recovered
series" (NOT_RUN register item 7) is now executed and committed as
descriptive aggregates. No RR signal, no run conditioning, no PnL was
computed — the family's scored measurement remains untouched and pending its
own gates.

## §5 M5 result — NQ-F2 07:30-by-era anatomy: **PASS** (scoring era 2023-26)

Artifact: `m5_0730_era_v3.json`. Anchor 07:30 CT = 08:30 ET (family anchor;
dispatch wording discrepancy resolved per §0.5). Eras mirror the committed
contrast windows (2010-06-07..2016-09-30 / 2017-01-01..2020-02-21 /
2023-01-01..2026-10-01).

Calendar-free era cells (exact mirror of the committed evidence class,
minute-volume share of era total):

| era | share 07:25 | share 07:30 | spike ratio | absret 07:30 | committed reference |
|---|---|---|---|---|---|
| 2010-16 (must-measure; was NOT_RUN) | 0.000344 | 0.001512 | **4.39×** | 5.2 bp | none — first measurement |
| 2017-20 (contrast) | 0.000404 | 0.000883 | **2.18×** | 3.1 bp | committed 0.00088 / 0.031% — reproduced |
| 2023-26 (scoring era) | 0.000411 | 0.001853 | **4.51×** | 7.7 bp | committed 0.00041 / 0.00185 / ≈4.5× / 0.077% — reproduced |

Coverage ≥ 0.6 variant of each cell differs by ≤ 0.03× on the spike ratio
(both variants in the JSON).

Release-day cells (CPI ∪ EMPSIT actual-print dates, bls_dates.json
ad41d2a7, vintage-law; canceled-but-expected 2025-11-13 / 2025-11-07 kept
SEPARATE per §0.5 — the first pooled computation was superseded in the JSON,
correction disclosed):

| era | n release (held) | share 07:30 release median | share 07:30 control median | ratio | absret 07:30 release (pooled row, incl. 2 canceled days) |
|---|---|---|---|---|---|
| 2010-16 | 148 | 0.003651 | 0.000489 | 7.47× | 17.6 bp |
| 2017-20 | 74 | 0.003203 | 0.000451 | 7.11× | 12.4 bp |
| 2023-26 | 85 | 0.006166 | 0.000716 | 8.61× | 35.1 bp |
| 2023-26 canceled-day subset (n=2) | — | 0.000477 | — | ≈ control level, no spike | — |

The canceled-day subset showing control-level 07:30 share is exactly the
vintage-law falsifier direction (no print ⇒ no spike) — descriptive only.

**GATE adjudication (§0.5):** scoring era 2023-26 calendar-free
share_0730/share_0725 = 4.51 ≥ 2.0 ⇒ **PASS**; the committed anatomy
reproduces to reported precision. The 2017-20 mechanism-contrast cell (2.18×)
and the newly measured 2010-16 cell (4.39×) are descriptive rows: a null
there would have been mechanism-consistent (field 2), and their measured
values are recorded without any scoring implication.

## §6 Gate verdict table, NOT_RUN register, zero-PnL statement

| mission | gate | pre-declared condition | result | verdict | n |
|---|---|---|---|---|---|
| M1 | NQ-F1-K6 | h0_30 vol ≥ 2.0× AND m60_0 vol ≤ 0.85×, full-era median | 2.230× / 0.686× | **PASS** | 85 events |
| M2 | ESNQ-F5 F5-K6 (i) | close-window vol-share & absret ratios > 1.0 in both modern tri-eras | 1.271/1.184 and 1.142/1.159 | **(i) PASS** | 20+18 W, 158+160 O clean |
| M2 | ESNQ-F5 F5-K6 (ii) | no expiry-Friday held session fails the ≤5min/0.8 phantom-gap check | 35/66 fail (15-min gaps, 2013-2021 era-generic; ordinary-Friday diagnostic fails 46/80) | **FAIL** ⇒ F5-K6 **FAIL** | 66 sessions |
| M3 | (none — descriptive rebuild) | — | hole window now measured (49 sessions) | — | 4,219 sessions |
| M4 | NQ-F3-K6 precondition = full-era rebuild | executed as descriptive aggregation; ret series cross-check vs readiness lane exact | max diff 0.0 (n=4,218) | **DONE** (precondition discharged as descriptive; no RR signal computed) | 4,219 rows |
| M5 | NQ-F2-K6 | share_0730/share_0725 ≥ 2.0 in scoring era 2023-26 (calendar-free class) | 4.51× | **PASS** | 3 era cells + release cells |

NOT_RUN register (final state):
1. M2 ES leg of F5-K6 — not this lane (ES quota; ES-K6 lane's scope).
2. M2 monthly-opex dose stratum — calendar NOT_OBTAINED (pre-declared).
3. M2 expiry dates 2010-03-19 / 2026-12-18 — outside the observable data
   window (structural, not a measurement failure).
4. M4 calendar_rule_sensitivity — completed on the 3rd attempt after two
   code defects (registry rows lacking `expiry`, then lacking `contract`;
   the merge-step defect had never executed before). Attempts disclosed;
   final value 19.84%/4,219 sessions.
5. M1 FOMC minute anatomy 2011-2015 — respected as committed NOT_RUN
   (statements carry no release-time line); day-level only, not re-measured.
6. M5 surprise/direction conditioning — committed NOT_RUN (no PIT consensus).
7. Everything in §0.6 (anti-cherry-pick register) — none of it was measured.

Deviations/corrections during execution (all disclosed in-artifact):
- M3 groupby tuple-key crash → fixed and rerun (M1/M2/M5 artifacts untouched).
- M5 release cells: first computation pooled the 2 canceled-but-expected
  2025 days, violating §0.5; superseded in JSON by
  `class_release_vs_control_v2_separate`; adjudication uses the separate
  block.
- M2 integrity `fails` list first written truncated to 20; recomputed in
  full and patched (count 35 unchanged).

**Zero-PnL statement**: every number in this file and its JSON artifacts is
an unconditional descriptive statistic of committed data (volume counts and
shares, |1m log return| dispersions, bar/minute counts, range aggregates,
variance ratios and autocorrelations of the held daily close series). No
PnL, no expectancy, no conditional-on-signal measurement, no parameter
selection, no family or parameter change, no registration action, no network
fetch (zero-fetch lane: all inputs are in-repo committed artifacts plus the
read-only root data plane already covered by the repo's evidence index), no
fee number cited (cost-irrelevant lane; COST_FREEZE_ERRATUM cf83bc2d recorded
unconsumed). Gate verdicts adjudicate only their pre-declared conditions;
they never promote, demote, or re-parameterize a family.
