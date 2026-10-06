# ES_K6_GATES — round FUTURES-K6GATE-PREP-20261004, lane ES-K6

- Task: **FUTURES-K6GATE-PREP-20261004**, lane **ES-K6** (0-cost pre-registered
  anatomy gates, K6-class, on committed data). Written 2026-10-04 UTC.
- Worktree `/Users/hoangminhlong/my-quantitative/.worktrees/futures-k6gate/prep`,
  branch `prep/futures-k6gate-20261004`, HEAD measured
  **`05e5493971116eec8db5ea49e30c06930e8cc6bc`** (== dispatch base_sha; the one
  permitted `git -C … rev-parse HEAD` + `git status --porcelain` at start/end;
  no other git, never commit/stage/push).
- Class: **UNCONDITIONAL descriptive statistics only.** 0 PnL, 0 expectancy,
  0 conditional-on-signal measurement, 0 parameter/family changes, 0 network
  fetches (zero attempts made). Gate measures adjudicate ONLY their
  pre-declared gate condition. Cap 24 FROZEN untouched (no identity touched,
  no trial created, no registry/ledger write). Fees per COST_FREEZE_ERRATUM
  dual-variant table (A 2.25/21.00-33.50-46.00; B 2.24/20.99-33.49-45.99;
  1.386 forbidden) — no cost number is used by any gate below (0-cost gates).
- **§0 PREDECLARATION below was written BEFORE any computation** (§0-§0.7
  existed on disk before the first compute pass; the file was subsequently
  amended by §0.8 — also before any verdict was written — and appended
  with results, so the current file mtime no longer proves the ordering;
  the ordering is vouched by this narrative and by the lane handoff).
  The compute script `es_k6_compute.py` is committed alongside and
  contains no statistic not declared here or in the §0.8 amendment.

---

## §0 PREDECLARATION (written before compute)

### §0.1 Shared data basis and session law (all gates)

- Panel: `research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/
  ES_cache/es_1m_outright.parquet` (in-git; 7,825,657 rows re-counted from
  parquet metadata; columns instrument_id/raw_symbol/ts_event/open/high/low/
  close/volume; `ts_event` = bar START, fixed-point 1e-9 per D5 schema).
  Path + row count cited from `FUTURES-SIX-READINESS-20261004/es/
  es_readiness.json` dim 1/2 and `DATA_READINESS_ES.md` §"What this lane
  independently re-verified" item 6. Single-shot read, aggregate, release.
- Session mapping [OPERATIONALIZED — mechanical rule, applied identically to
  every gate]: `ts_event` → America/Chicago wall time; a bar belongs to
  trade-date D where D = bar's calendar date if time-of-day < 17:00, else
  next calendar day (Sunday-evening bars → Monday; no Saturday sessions).
- Era-correct session-close law (binding construction, quoted from
  `FUTURES-ES-V1-PACKET/SPEC_PB1_ES.md` §1: "Session clock **era-correct**
  (đo): close 16:30 CT (→2012) → 16:15 CT (2013→2015-11) → 16:00 CT (từ
  2015-11/2016); break-tail pre-2016 tách riêng."; corroborated by
  `FUTURES-SIX-READINESS-20261004/es/es_session_holiday.json`
  `weekly_template_by_era`). Close-eras: **CA 16:30** = trade-date ≤
  2012-12-31; **CB 16:15** = 2013-01-01..2015-11-19; **CC 16:00** =
  ≥ 2015-11-20. RTH settlement close (secondary view only): 15:15 CT
  through 2013-04, 15:00 CT after (same artifact, weekly_template_by_era).
- Quality eras (annotation only; `FUTURES-DEEPRESEARCH-V2-20261003/analysis/
  ES_quality_ledger.json` eras): E1 2010-06..2012-12, E2 2013-01..2015-11-19,
  E3 2015-11-20..2017-05-20, E4 2017-05-21..2020-02-19, E5 2020-02-20..
  2021-12-31, E6 2022-01-01..2023-09-30, E7 2023-10-01..2026-10-01.
  Tri-eras (regime views, quoted from `FUTURES-OVERNIGHT-PREP-20261003/hypo/
  es_nq/ESNQ_HYPOTHESES.md` §0.4: "Era splits used by every family's regime
  field: 2010-16 / 2017-21 / 2022-26"): **T1** ≤ 2016-12-31, **T2**
  2017-01-01..2021-12-31, **T3** ≥ 2022-01-01.
- RTH-core coverage law (binding, quoted from `SPEC_PB1_ES.md` §2 [ERRATUM
  A7-SPEC-M4]): "RTH-core … = tỷ lệ phút 08:30–15:00 CT có bar (close
  era-correct) <60% ⇒ EXCLUDE". RTH-core window = 08:30–15:00 CT. Sessions
  with coverage < 0.60 are EXCLUDED (half-day/holiday); never imputed,
  never padded. [Expected-minutes count amended 420→390 in §0.8 — an
  arithmetic slip in this §0.1 sentence, corrected before any gate was
  adjudicated; the window itself is unchanged.]
- Day-class hygiene for every event-class gate (family stand-aside law):
  RTH-core <60% ⇒ EXCLUDE (above); FOMC statement-day stacking (ES-F1's own
  day set) disclosed; unproven-early-close days fail closed via the coverage
  law (SPEC §2-E1: 2011-2025 unproven ES-specific days EXCLUDE fail-closed —
  they manifest mechanically as sub-60% RTH-core coverage here).
- |1m ret| definition [OPERATIONALIZED]: |log(close_t / close_{t-1})| on
  consecutive 1m bars of the same session, computed within each reported
  window; the FIRST bar of a window uses the prior bar (previous window)
  only when both bars sit in the same session. No sign is ever reported.

### §0.2 M1 — ESNQ-F5 `EXPWITCH` ES-leg F5-K6

Owning-family definition, quoted verbatim from
`research/control/FUTURES-TEN-HYPO-PREP-20261004/es_nq/HYPOTHESES_ESNQ_R3.md`
§2 field 7 (lines "**F5-K6 anatomy pre-gate …**"):

> "**F5-K6 anatomy pre-gate (construction gate, 0 identities,
> PREP-legal)**: before any scoring is ever proposed, (i) the
> witching-Friday session anatomy must be measured on the era-correct
> mapping and show elevated close-window volume/activity vs matched
> ordinary Fridays **in the modern eras**; (ii) held-chain session
> integrity on expiry Fridays must pass (no phantom gaps; switch-day
> audit law NEW-4 inherited for the NQ leg). Failure ⇒ the family
> never enters scoring."

Day classes:
- **W (witching)** = the quarterly expiry Fridays of the committed 68/68
  calendar `FUTURES-SIX-READINESS-20261004/es/es_expiry_recheck.json`
  (`date_machine_checks.per_quarter[].expiry`, 68 quarters 2010-03..2026-12;
  in-panel: 66 dates 2010-06-18..2026-09-18; 2010-03-19 and 2026-12-18 lie
  outside the panel span and are NOT_RUN rows, never inferred).
- **O (matched ordinary Fridays)** = Fridays of months-position 2nd/4th/5th
  within the same month, in-panel, per the family's own placebo convention
  (field 6 C1/NC-1: "weekday-matched ordinary Fridays (months-position
  matched 2nd/4th/5th Fridays)"). 3rd Fridays that are NOT quarterly
  expiries (monthly opex) are NOT in either class (NC-2 declared NOT_RUN in
  the family doc; never assumed).
- Excludes applied to BOTH classes (family field 5 stand-aside law, counts
  disclosed): RTH-core coverage <60% ⇒ EXCLUDE; W-days stacking a scheduled
  08:30 CT BLS print (CPI∪EMPSIT set per §0.4) ⇒ EXCLUDED in the main gate
  set, disclosed; W-days that are FOMC statement days (ES-F1 set) ⇒
  EXCLUDED, disclosed; calendar-uncertain days ⇒ fail-closed via coverage
  law. A disclosed sensitivity re-run of the primary statistic INCLUDES the
  macro-stacked W-days (anti-cherry-pick; gate adjudicates on the
  family-law set).

Statistics (unconditional, per class × view):
- Bar counts: sessions per class per era; per-session total bars and
  RTH-core bars (medians).
- Session volume distribution: per-minute mean volume by clock-hour block
  (2-hour blocks 17:00→close, plus RTH 08:30-15:00 split into
  08:30-10:29 / 10:30-12:29 / 12:30-14:29 / close-window), per class per
  close-era; share of full-session volume.
- Close-window volume/activity: **W-60-full** = [close−60min, close) with
  close = era-correct full-session close (16:30/16:15/16:00 CT) [the
  family's own exit mark, field 4/5]; secondary **W-60-rth** = final 60
  minutes before the RTH settlement close (15:15/15:00 CT). Per close-era:
  per-minute mean volume ratio W/O, per-minute median |1m ret| ratio W/O
  (activity co-evidence), n per class.
- **Gate-adjudicating statistic [OPERATIONALIZED]**: per-minute mean volume
  ratio W/O in W-60-full, per close-era. "Elevated … in the modern eras"
  is operationalized as ratio ≥ 1.25 in BOTH modern tri-eras T2 (2017-21)
  and T3 (2022-26) evaluated on the close-eras that intersect them (CB for
  T2, CC for T3; T1 2010-16 = the old-regime view, reported not
  adjudicated — the family's own K1 pre-registration expects old-regime
  inflation, so T1 is descriptive only). The 1.25 threshold is a declared
  operationalization (the doc names no number); the raw per-era ratios are
  reported alongside so the adjudication is transparent.
- (ii) held-chain integrity on W-days, on the held chain (the panel is the
  outright chain; ES T-5 roll ⇒ on expiry Friday the held contract is the
  NEXT quarterly, not the terminating one — family field 4): (a) missing
  RTH-core minutes per W session (must be 0; also reported for O);
  (b) OHLC violations (high<max(o,c), low>min(o,c), high<low) per W
  session (must be 0); (c) the 08:30 CT termination minute (expiring
  contract terminates 9:30 a.m. ET = 08:30 CT, coincident with the RTH
  cash open): W-vs-O ratio of per-minute median volume and per-minute
  median |1m ret| at minute 08:30 [phantom threshold OPERATIONALIZED:
  ratios within [0.5, 3.0] and zero missing/OHLC defects ⇒ integrity
  PASS; any breach ⇒ FAIL].

Verdict rule (pre-declared): F5-K6 (ES leg) PASS iff (i) elevated per the
1.25× rule in both modern tri-eras AND (ii) integrity PASS. Otherwise FAIL
(⇒ the ES leg never enters scoring). All component values reported either
way. This gate adjudicates nothing else (no sign, no return statistic).

### §0.3 M2 — ES-F1 `FOMC-RES` F1-K6

Owning-family definition, quoted verbatim from
`research/control/FUTURES-OVERNIGHT-PREP-20261003/hypo/es_nq/
ESNQ_HYPOTHESES.md`, PART I, ES-F1 field 7:

> "**F1-K6 anatomy reproduction gate (pre-scoring)**: re-measured on the
> era-correct session mapping, the release bucket must again show ≥2×
> volume and pre-release ≤0.85× suppression; if the committed anatomy fails
> to reproduce, family never enters scoring [construction gate]."

Committed reference anatomy being reproduced (same doc, ES-F1 field 1,
[OBSERVED, `ES_fomc_stats.json` sha256 228fe2d4…]): "release 15-min bucket
**2.906× volume / 3.188× |1m ret|**; pre-release −120→−15 min **0.724-0.805×
flat suppression**".

Event class: the 132-statement committed artifact `FUTURES-DEEPRESEARCH-
V2-20261003/analysis/ES_fomc_stats.json` (`n_statements_total` = 132;
`per_event_day_level` = 131 in-data dates; `release_time_note` = 85 @14:00
ET + 7 irregular: 2019-10-11 11:00, 2020-03-03 10:00, 2020-03-15 17:00 Sun,
2020-03-23 08:00, 2020-03-31 08:30, 2020-08-27 09:10, 2025-08-22 10:00).
Minute-anchored anatomy = the `timed: true` statements with in-panel data
(expected n=91; 2011-15 statements are day-level only — their minute
anatomy is NOT_RUN per the artifact and is never inferred). Sunday
2020-03-15 EXCLUDE (family field 4: "Sunday/holiday sessions ⇒ EXCLUDE per
era law"); other irregulars enter at their own release minute. Release
minute = 14:00 ET → 13:00 CT for the scheduled 85 (family field 4 law).
RTH-core coverage <60% event days ⇒ EXCLUDE, disclosed.

Statistics (mirroring the committed bucket method; baseline re-declared):
- Buckets: 15-minute buckets at offsets −120..+165 min from the release
  minute, per event day; per bucket median volume and median |1m ret|.
- Baseline [same convention as the committed artifact's `baseline_wed13`]:
  the same clock buckets on non-FOMC Wednesdays (all eras pooled), n
  disclosed. Secondary era views [OPERATIONALIZED]: same buckets on
  non-FOMC Wednesdays restricted to each FOMC data-era (2016-19 / 2020-22
  / 2023-26, family field 6) and each tri-era — reported, not adjudicated.
- Reproduction check vs committed values: event bucket-0 vol ratio,
  bucket-0 |1m ret| ratio, pre-release bucket ratios (−120..−15).
- **Gate-adjudicating condition (verbatim thresholds from the quote)**:
  bucket-0 volume ratio ≥ 2.0 AND max(pre-release bucket −120..−15 volume
  ratio) ≤ 0.85. |1m ret| multiples reported as co-evidence (the gate text
  names volume and suppression only). Era-level values reported as views
  (era instability is F1-K1's job, not K6's).

Verdict rule (pre-declared): F1-K6 PASS iff the pooled 2016+ timed-sample
re-measurement meets both thresholds on the era-correct mapping. Failure ⇒
the family never enters scoring. Nothing else is adjudicated.

### §0.4 M3a — ES-F2 `MACRO-0730` F2-K6

Owning-family definition, quoted verbatim from `ESNQ_HYPOTHESES.md`, PART I,
ES-F2 field 7:

> "**F2-K6 anatomy pre-gate**: 07:30-vs-neighbor minute-volume spike must
> reproduce in each scoring era (else that era is descriptive-only — the
> spike is a participation-era feature on NQ evidence, and ES pre-2016 is
> unmeasured) [construction gate]."

Committed reference anatomy (same doc, ES-F2 field 1, [OBSERVED]):
"E7 (2023-10..2026-10) hour profile 07:00h CT = **3.0% of daily volume
(0.0302) and |1m| 1.61 bp** — the most active pre-RTH hour
[`ES_session_stats.json` hour_profiles, sha256 f4e24ce3…]; three of ES's
ten >2% 1m jumps sit exactly at 07:30 CPI minutes (2022-09-13, 2022-10-13,
2022-11-10)".

Event class (vintage law, family field 3/5 + §0.3 of the baseline doc):
scheduled CPI + EMPSIT dates from `FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/
events_bbo_coverage/bls_dates.json` (204 + 204, all 08:30 ET = 07:30 CT;
2016-04 double-entry anomaly handled per that artifact: monthly grid uses
2016-05-17). Vintage-law corrections (quoted law: "for decision date D the
correct expected-release calendar is the schedule vintage as known at D";
"2025 actual prints 11 CPI / 10 EMPSIT"; canceled-but-expected days
"2025-11-13 CPI, 2025-11-07 EMPSIT"): main anatomy set 2025 = the days a
print physically landed — CPI scheduled {…Sep 11} ∪ {Oct 24, Dec 18} (Oct
15, Nov 13 out), EMPSIT scheduled {…Sep 5} ∪ {Nov 20, Dec 16} (Oct 3, Nov
7 out); the two expected-but-canceled days form the NC-2b falsification
sub-view only (reported separately, never pooled). 2026 uses the
bls_dates.json 2026 lists (current vintage fetched 2026-10-03, which
already encodes the Feb-2026 shifts). [OPERATIONALIZED note]: the
artifact's "10 EMPSIT" headline count does not itemize which 10; my
vintage-corrected construction yields 11 EMPSIT 2025 print days; the
headline-vs-construction discrepancy is recorded as a residual in §6, not
smoothed. Union = CPI ∪ EMPSIT (dedup). Excludes: FOMC-stacked release
days ⇒ EXCLUDE (family field 5 stand-aside (i)), count disclosed;
RTH-core <60% ⇒ EXCLUDE, disclosed.

Statistics per tri-era (T1/T2/T3 = the doc's own "scoring eras" axis, field
7 "(else that era is descriptive-only)") and per close-era (CA/CB/CC,
reported as views):
- Spike window [OPERATIONALIZED]: minutes 07:25–07:34 CT (the 07:30 print
  minute ±4); neighbor window [OPERATIONALIZED]: 06:45–07:24 ∪ 07:36–08:15
  CT, same days (symmetric ±25–45 min, pre-RTH).
- Primary gate statistic: per-minute mean volume, spike/neighbor, on
  release days, per tri-era.
- Co-evidence / reference-matching views (reported, not adjudicated):
  (a) hour-07 volume share of full-session volume on release days per era
  vs the committed E7 3.0% reference; (b) release-day spike-window
  per-minute volume ÷ weekday-matched non-release-day same-clock
  per-minute volume per era (match = nearest same-weekday non-release,
  non-FOMC day within ±30 days); (c) spike-window median |1m ret| ratio
  release vs matched non-release days.
- **Gate-adjudicating condition [OPERATIONALIZED]**: "spike must reproduce
  in each scoring era" = primary gate statistic ≥ 2.0 in each of T1, T2,
  T3 (the ≥2× threshold is borrowed from the F1-K6 release-bucket
  convention and is here declared; the doc names no number for F2-K6).

Verdict rule (pre-declared): per-era PASS/FAIL reported; family-level
F2-K6 PASS iff ALL THREE tri-eras pass. An era that fails is
descriptive-only (verbatim consequence); family-level failure bars any
scoring-era extension beyond passing eras. Nothing else adjudicated.

### §0.5 M3b — ES-F4 `RUN-REV` F4-K6

Owning-family definition, quoted verbatim from `ESNQ_HYPOTHESES.md`, PART I,
ES-F4 field 7:

> "**F4-K6 anatomy pre-gate**: intraday placement of run-reversal (open vs
> close) must be measured descriptively before scoring — if reversal is
> purely an overnight-close phenomenon the RTH-session family is
> mis-specified and dies pre-registration."

Disposition decided BEFORE compute (recorded here, not after): the gate's
measured object — "placement of **run-reversal**" — conditions on a
price-derived signal (k consecutive same-sign sessions, strict past).
This round's law is UNCONDITIONAL descriptive statistics only, with
conditional-on-signal measurement explicitly forbidden ("that measurement
IS the family's scored trial" per the family's own zero-PnL law in
HYPOTHESES_ESNQ_R3 header). F4-K6 is therefore **NOT_RUN** this round with
the named gap: it is not unconditional anatomy; it is a conditional
measurement reserved for scored authorization. The unconditional inputs
F4-K6 would consume (per-session RTH-core dispersion, bar counts, segment
structure) ARE delivered by M4. Recorded in the NOT_RUN register and in
the considered-and-not-run table (§5) — never inferred PASS.

### §0.6 M4 — Session dispersion table refresh (unconditional)

- Population: every session of the full panel (trade-date keyed), all
  eras. Per session: total bars; RTH-core bars (08:30–15:00 CT, 420
  expected); RTH-core coverage; RTH-core |1m ret| median / p75 / p90 /
  sd (bp); full-session volume sum; era labels (close-era, quality era,
  tri-era). Exclusions by the committed bar-count law only: RTH-core
  coverage < 0.60 ⇒ flagged `excluded: true` with reason (half-day /
  holiday-class short session), never imputed, never dropped from the
  JSON (kept and flagged so the exclusion is auditable).
- Aggregates reported: per-year medians and full-panel/full-era summaries
  (compact md table + `session_dispersion_es.json`). This is the D5 /
  power-honesty input table refresh; it adjudicates nothing.

### §0.7 Anti-cherry-pick commitment

Every statistic computed by `es_k6_compute.py` appears in §1-§4 results —
including nulls and failures. No additional statistic was computed. The
considered-and-not-run register (§5) lists every candidate measurement
contemplated and dropped, with reasons.

### §0.8 IMPLEMENTATION DISCOVERY & AMENDMENT (written after first compute
### pass, BEFORE any result was adjudicated or any verdict written)

Two implementation defects were found in the first compute pass; both are
fixed before any gate is adjudicated. Neither fix is outcome-driven; the
gate conditions of §0.2-§0.4 are unchanged.

1. **RTH-core expected minutes: 390, not 420.** §0.1 declared the RTH-core
   window 08:30–15:00 CT (the SPEC [ERRATUM A7-SPEC-M4] span, unchanged)
   but wrote "420 expected minutes" — an arithmetic slip (08:30→15:00 is
   6.5 h = 390 minute-BARS, bar-starts 08:30..14:59). First-pass coverage
   was uniformly 390/420 = 0.9286 across all 4,204 sessions, which is the
   signature of the denominator error, not of data holes (spot sessions
   re-probed: 390/390 minutes present). AMENDED: expected RTH-core minutes
   = 390; coverage = distinct held-chain minute-starts in [08:30,15:00) /
   390. The <60% EXCLUDE law is unchanged.
2. **The panel is the multi-contract outright panel; |1m ret| runs on the
   held chain.** `es_1m_outright.parquet` carries all co-trading outright
   contracts per minute (e.g., 2024-06-21 contains ESM4 expiring + ESU4
   held + far-tail prints in the same minutes). First-pass |1m ret| was
   computed bar-to-bar over the interleaved panel, which mixes contracts
   inside a minute (|log(close_next/close_expiring)| = roll-basis noise)
   — materially contaminating exactly the expiry-adjacent minutes the
   gates examine. AMENDED (dictated by the family's own construction law,
   ESNQ-F5 field 4: "on expiry Friday the held chain holds the NEXT
   quarterly", and by the T-5 chain law): each session's HELD contract =
   the maximum-session-volume outright symbol in that session; **|1m ret|
   is computed only on the held contract's consecutive bars within the
   session**; held-chain RTH-core bar counts and missing-minute integrity
   use held-chain minutes. **Volume statistics remain complex-summed**
   (sum over all contracts per minute = total ES complex volume), which is
   the convention comparable to the committed reference anatomy
   (`ES_fomc_stats.json`, `ES_session_stats.json`). Alignment views added,
   reported regardless of outcome and never gate-adjudicating: M2
   held-chain-only bucket volume ratios alongside the complex-summed
   ratios; M1 held-chain close-window |1m ret| ratios (replacing the
   contaminated first-pass values, which are discarded, not reported as
   results).

Consequence for §0.6: `session_dispersion_es.json` dispersion columns are
held-chain; volume/bar-count columns carry both conventions (complex and
held-chain), each labeled.

---

# RESULTS (all outcomes reported; computed per §0 as amended by §0.8)

Raw machine numbers: `es_k6_gates_results.json` (same directory). Compute
script: `es_k6_compute.py` (single-shot parquet read; zero network).

## §1 M1 — ESNQ-F5 `EXPWITCH` ES-leg F5-K6

Class sizes (n per class per era). W = committed 68/68 expiry calendar ∩
panel (66 in-panel: 65 Fridays + **2026-06-18 Thursday**, the Juneteenth-
shifted ESM6 — calendar date is the authority, weekday disclosed). O =
2nd/4th/5th-Friday matched ordinary set.

| class | CA_1630 | CB_1615 | CC_1600 | T1 | T2 | T3 |
|---|---|---|---|---|---|---|
| W main | 8 | 10 | 43 | 22 | 20 | 19 |
| W sensitivity (stacked incl.) | 11 | 11 | 44 | 27 | 20 | 19 |
| O | 68 | 77 | 287 | 173 | 131 | 128 |

W excludes (family field-5 law, disclosed): BLS-stacked 5 — 2010-09-17,
2011-12-16, 2012-03-16, 2013-03-15, 2016-09-16; FOMC-stacked 0; RTH-core
coverage failures 0 (W) / 16 (O — day-after-Thanksgiving short Fridays
2010-11-26..2025-11-28, mechanically caught by the coverage law). Out-of-
panel calendar rows NOT_RUN, never inferred: 2010-03-19, 2026-12-18.

Primary adjudicating statistic — W-60-full per-minute mean complex volume
ratio W/O (§0.2; threshold ≥1.25 in BOTH modern tri-eras):

| view | CA_1630 | CB_1615 | CC_1600 | T1 (2010-16) | T2 (2017-21) | T3 (2022-26) |
|---|---|---|---|---|---|---|
| vol ratio W/O | 1.417 | 1.595 | 1.212 | 1.192 | **1.269** | **1.220** |
| \|1m ret\| median ratio (held) | 0.991 | 1.035 | 1.169 | 1.031 | 1.127 | 1.405 |
| n_W / n_O | 8/68 | 10/77 | 43/287 | 22/173 | 20/131 | 19/128 |

Sensitivity (BLS/FOMC-stacked W days included — all stacked days are
2010-2016): T2 1.269, T3 1.220 unchanged; T1 1.144. Close-window volume
level (CC): W 1666 vs O 1375 per-minute (W-60-full [15:00,16:00) — the
post-RTH-settle Globex window carries the elevation); W-60-rth
[14:00,15:00): W 4919 vs O 4721 (ratio 1.042). Session volume
distribution (CC, per-minute mean complex volume): RTH-open 4507 (W) vs
4332 (O); midday 2346/2342; afternoon 2087/2273; 14:30-15:00 7365/6821;
overnight 482/407; evening 137/155. Bar counts (CC): median complex bars
2405 (W) vs 1729 (O) — co-trading-contract inflation on expiry
mornings, disclosed; held-chain RTH-core bars median 390/390.

(ii) Held-chain integrity on W days: 61/61 sessions — 0 missing RTH-core
held minutes (panel-complete 390/390), 0 OHLC violations (O: 432/432
clean too). 08:30 CT termination minute (expiring contract SOQ coincides
with the cash open): median held volume W 24,897 vs O 11,880.5 → ratio
2.096 ∈ [0.5,3.0]; median held \|1m ret\| W 3.857 bp vs O 3.800 bp →
ratio 1.015 ∈ [0.5,3.0]. No phantom-gap signature. **(ii) PASS.**

### F5-K6 verdict (ES leg): **FAIL**

Component (i) FAILS the pre-declared rule: T2 1.269 ≥ 1.25 but **T3
1.220 < 1.25** (margin −0.030). Component (ii) PASSES. Per the
pre-declared rule (PASS iff (i) AND (ii)) and the family's own
consequence ("Failure ⇒ the family never enters scoring"), the ES leg
does not enter scoring. Honest margin note, for the owner only: the miss
is threshold-marginal and directionally consistent (elevation present in
every view: 1.19-1.60 by close-era, 1.19/1.27/1.22 by tri-era, with
held-chain \|1m ret\| co-elevation 1.13-1.41 in T2/T3); the threshold
1.25 was this lane's declared operationalization of the doc's
unquantified "elevated", and it is NOT re-tuned post-hoc. Re-adjudication
of the operationalization is an owner decision, not a lane decision.
First-pass (contaminated pre-§0.8) |ret| values were discarded, not
reported.

## §2 M2 — ES-F1 `FOMC-RES` F1-K6

Event class: 92 timed statements in `ES_fomc_stats.json`
(`per_event_day_level` `timed: true`; 85 @14:00 ET → 13:00 CT + 7
irregular at own minute); 2020-03-15 (Sunday) EXCLUDED per family field
4; n measured = **91**; coverage failures 0; baseline = 719 non-FOMC
Wednesdays (RTH-core-complete), 15-min buckets −120..+165.

Gate statistics (complex-summed volume per §0.3; held-chain §0.8
alignment alongside):

| statistic | measured (n=91) | committed reference | gate |
|---|---|---|---|
| release bucket (0) volume ratio | **2.646** | 2.906× | ≥2.0 ✓ |
| pre-release (−120..−15) max volume ratio | **0.828** (range 0.739-0.828) | 0.724-0.805× | ≤0.85 ✓ |
| held-only alignment: bucket-0 / pre-max | 2.625 / 0.793 | — | views |
| \|1m ret\| bucket-0 ratio (held-chain, per-event bucket-median convention) | 2.231 | 3.188× (artifact's own convention, not itemized) | co-evidence |
| \|1m ret\| pre-release range (held) | 0.684-0.799 | — | co-evidence |
| +30 / +45 bucket volume ratios | 2.665 / 2.465 | 2.653× / 2.506× | reproduction ✓ |

The committed anatomy REPRODUCES: release-bucket ≥2× volume ✓, pre-
release ≤0.85× suppression ✓, and the second processing wave (+30/+45)
matches the committed 2.653×/2.506× almost exactly.

Era views (non-adjudicating per §0.3; era instability is F1-K1's kill,
not K6's): bucket-0 vol ratio / pre-release max — 2016-19: 2.769 / 0.900;
2020-22: 2.367 / 0.885; 2023-26: 2.896 / 0.806 (n_ev 33/27/31, baselines
173/134/162). Per-era pre-max readings 0.885-0.900 sit above the 0.85
line in two data-eras — reported, not adjudicated here.

### F1-K6 verdict: **PASS**

## §3 M3a — ES-F2 `MACRO-0730` F2-K6

Event class: vintage-law main set (§0.4): union in-panel 381 → FOMC-
stacked excluded 12 (2013-10-30 … 2025-12-10, list in results JSON) →
RTH-core coverage failures excluded 7 (Good-Friday/July-3 short sessions:
2012-04-06, 2014-07-03, 2015-04-03, 2021-04-02, 2023-04-07, 2025-07-03,
2026-04-03) → **n=369** release days; matched non-release comparators
n=369/369 filled (nearest same-weekday ±30d, non-release non-FOMC).

Gate statistic — release-day 07:25-07:34 vs same-day neighbor
(06:45-07:24 ∪ 07:36-08:15) per-minute complex volume ratio; threshold
≥2.0 in EACH tri-era:

| era | gate stat | ≥2.0? | release-vs-matched spike ratio | \|1m ret\| spike (held, bp) rel/matched | 07:00h share rel/matched |
|---|---|---|---|---|---|
| T1 2010-16 | **3.416** | ✓ | 3.253 | 2.39 / 1.75 | 6.54% / 3.19% |
| T2 2017-21 | **2.504** | ✓ | 3.021 | 1.75 / 1.25 | 4.93% / 2.61% |
| T3 2022-26 | **2.955** | ✓ | 3.854 | 2.59 / 1.50 | 6.54% / 2.76% |

Close-era views (non-adjudicating): CA 3.735, CB 3.479, CC 2.712.
Reference-matching: committed E7 hour-07 share 3.0% (all-day profile) —
this lane's release-day 07:00h share in the 2023-26 window is 6.54%
(release days) vs 2.76% (matched non-release) — consistent.

**NC-2b falsification sub-view** (expected-but-canceled 2025 days,
disclosed, never pooled): 2025-11-07 EMPSIT spike/neighbor = 0.918,
2025-11-13 CPI = 0.843 — NO spike on days the print never arrived, i.e.
the anatomy is information-arrival-linked, not calendar-artifact-linked.

### F2-K6 verdict: **PASS — spike reproduces in all three scoring eras**

## §3b M3b — ES-F4 `RUN-REV` F4-K6

**NOT_RUN** (disposition pre-declared in §0.5 before compute): the gate
measures placement of run-reversal CONDITIONED on a price-derived signal
(k consecutive same-sign sessions); this round's law forbids
conditional-on-signal measurement. Unconditional inputs F4-K6 would
consume are delivered by §4. Never inferred PASS.

## §4 M4 — Session dispersion table refresh (unconditional)

`session_dispersion_es.json`: 4,204 sessions (matches the committed
census exactly), held-chain dispersion columns + complex volume columns,
full per-session rows kept (excluded sessions flagged, never dropped).
RTH-core expected 390 minutes (§0.8); median coverage 1.000.

| close-era | sessions | excluded (<60%) | median of session median \|1m ret\| (bp) |
|---|---|---|---|
| CA_1630 (2010-06..2012-12) | 665 | 22 | 1.94 |
| CB_1615 (2013-01..2015-11-19) | 732 | 16 | 1.48 |
| CC_1600 (2015-11-20..2026-10) | 2,807 | 101 | 1.69 |

Year medians (compact; full table in JSON): 2010 2.23 · 2011 1.98 · 2012
1.82 · 2013 1.53 · 2014 1.33 · 2015 2.10 · 2016 1.20 · 2017 1.03 · 2018
1.83 · 2019 1.67 · 2020 2.25 · 2021 1.39 · 2022 3.15 · 2023 1.80 · 2024
1.49 · 2025 1.65 · 2026 1.44 bp. Excluded sessions: 139 (3-11/yr
half-day/holiday-class short sessions + full-holiday Globex stubs;
per-year excluded counts 3-11 in JSON; list in JSON `excluded_dates`;
exclusion by the committed bar-count law only — SPEC_PB1_ES §2 [ERRATUM
A7-SPEC-M4] — never imputed).

## §5 Gate verdict table + considered-and-not-run register

| gate | family / doc | verdict | decisive numbers |
|---|---|---|---|
| F5-K6 (i) close-window elevation | ESNQ-F5 EXPWITCH, HYPOTHESES_ESNQ_R3.md §2 field 7 | **FAIL** | T3 vol ratio 1.220 < 1.25 declared (T2 1.269 ✓) |
| F5-K6 (ii) held-chain integrity | same | **PASS** | 0 missing minutes, 0 OHLC, 08:30-min ratios 2.10/1.01 in band |
| **F5-K6 overall (ES leg)** | same | **FAIL** | (i) AND (ii) required; family never enters scoring (ES leg) |
| F1-K6 anatomy reproduction | ES-F1 FOMC-RES, ESNQ_HYPOTHESES.md field 7 | **PASS** | 2.646 ≥2.0; 0.828 ≤0.85; +30/+45 wave reproduces |
| F2-K6 07:30 spike per era | ES-F2 MACRO-0730, ESNQ_HYPOTHESES.md field 7 | **PASS (all eras)** | 3.416 / 2.504 / 2.955 ≥2.0; NC-2b shows no spike |
| F4-K6 run-reversal placement | ES-F4 RUN-REV, ESNQ_HYPOTHESES.md field 7 | **NOT_RUN** | conditional-on-signal (§0.5) |

Considered and NOT run (anti-cherry-pick; each with reason):

1. F4-K6 execution (run-conditioned OVN/RTH placement decomposition) —
   conditional-on-signal measurement, forbidden this round (§0.5).
2. Monthly-opex (non-quarterly 3rd Fridays) as the graded dose stratum
   between W and O — options-side calendar NOT_OBTAINED (family NC-2
   declared NOT_RUN; arithmetic derivation forbidden).
3. Any directional/sign statistic (W1 sign, close-window direction,
   07:30-window sign, run-day or expiry-day signed returns) — these ARE
   the families' scored trials; zero-PnL law forbids.
4. F5-K6 NQ leg — out of this lane (NQ-K6 lane owns it).
5. Session-close era-change "liquidity redistribution" as a family —
   CONSTRUCTION-ONLY per R3 §3; only era views are measured here.
6. W×PB1-armed-day overlap census — PB1 territory; belongs to a
   scored-census round, not this anatomy round.
7. Re-derivation of committed calendars (68/68 expiry, 132 FOMC,
   204+204 BLS, era templates) — used as committed; re-verification is
   the owning lanes' closed work.
8. Unconditional OVN-vs-RTH signed-return placement table (an F4-K6
   adjacent view without the run condition) — considered and dropped:
   it is a signed-return aggregate beyond this round's
   magnitude-only law and would not adjudicate F4-K6 anyway.

## §6 Residuals, contradictions, NOT_RUN register, zero-PnL statement

Residuals / contradictions (reported, not smoothed):

1. **EMPSIT 2025 count**: artifact headline "2025 actual prints 11 CPI /
   10 EMPSIT" vs this lane's vintage-corrected construction = 11 EMPSIT
   print days ({Jan..Sep 5} ∪ {Nov 20, Dec 16}; Oct 3 moved + Nov 7
   canceled excluded). The artifact does not itemize its "10". Recorded;
   main-set construction disclosed in §0.4; the 1-day difference affects
   2 session-days of the 369-day M3 class at most.
2. **FOMC \|1m ret\| reference convention**: committed 3.188×
   (ES_fomc_stats.json) vs this lane 2.231× — per-bucket |ret| statistic
   convention is not itemized in the artifact (likely mean/max/pooled vs
   this lane's per-event bucket-median); the VOLUME gate statistic
   reproduces at 2.646 vs 2.906 (same region; baselines differ: this
   lane n=719 non-FOMC Wednesdays vs the artifact's `baseline_wed13`
   n≈1489 — also not fully itemized). Gate thresholds are absolute on
   this lane's declared statistics; both sets reported.
3. **W weekday fact**: the "quarterly expiry Fridays" conditioner
   contains one Thursday, 2026-06-18 (Juneteenth shift) — included by
   calendar authority, disclosed (65 Fri + 1 Thu in panel).
4. Inherited, unchanged: 8/23 Q5 2026 deviation captures missing from
   disk (SIX-READINESS disclosure; not touched here); 2011-2025
   unproven ES-specific early-close days excluded fail-closed via the
   coverage law; BBO/account-fee verification NOT_RUN (no cost number
   used — 0-cost gates).
5. First-pass compute defects (420-min denominator; multi-contract
   \|1m ret\| contamination) — found, disclosed, fixed via §0.8 BEFORE
   any verdict; contaminated first-pass |ret| values discarded.

NOT_RUN register (this lane): F4-K6 (§3b); monthly-opex dose stratum;
NQ leg; W×PB1 overlap census; out-of-panel calendar rows (2010-03-19,
2026-12-18); surprise/consensus conditioning (never acquired, H3);
publish latency; 2011-15 FOMC minute anatomy (day-level only, per
committed artifact). Nothing missing was inferred PASS.

**Zero-PnL statement**: every number in this document and its companion
JSONs is an unconditional descriptive statistic (volume counts, |1m ret|
magnitudes, bar counts, coverage). No PnL, no expectancy, no
conditional-on-signal measurement, no sign/return-direction statistic,
no parameter or family change, no scored cell, no trial creation, no
registry/ledger write, no network fetch (0 attempts), cap 24 FROZEN
untouched (identity table never read for modification). Gate measures
adjudicate only their pre-declared gate conditions. Fees: no cost number
is consumed by any gate above (0-cost gates); the COST_FREEZE_ERRATUM
dual-variant table (A 2.25/21.00-33.50-46.00; B 2.24/20.99-33.49-45.99;
1.386 forbidden) is acknowledged as the correction of record.

— End ES_K6_GATES.md results. Machine mirror: `es_k6_gates.json`.
