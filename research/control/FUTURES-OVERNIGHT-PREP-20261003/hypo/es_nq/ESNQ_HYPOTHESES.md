# ESNQ_HYPOTHESES — Competing-hypothesis families for ES and NQ (beyond the OVN pair)

- Task: **FUTURES-OVERNIGHT-PREP-20261003**, lane **P1-ESNQ**. Generated UTC
  2026-10-04. Worktree
  `/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/prep` @
  `72c9bc5b1d94b812044a9bd21768c53b4d378436` (re-measured via `git -C` before
  writing; no tracked drift), branch `prep/futures-behavior-10syms-20261002`.
- Class: PREP competing-hypothesis specification. **0 PnL, 0 scored runs, 0
  signal selection by any return statistic; every parameter [PROVISIONAL];
  outcome-blind.** No committed file modified; SPEC_PB1_ES r3 untouched.
- Evidence base (read fully first, per dispatch): parent v3 addenda
  `FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/deep/es_nq/{ES,NQ}_DEEPFOUR_
  V3_ADDENDUM.md` + `evidence_index.json` (the registered H-A/H-B OVN pair
  with K1-K5 lives there); this round's batch-1 facts committed at 72c9bc5b:
  `fees_erratum/source/FEES_CORRECTED.md`, `cme_cal_gap/equity/
  EQ_GAPFILL_EVIDENCE.md`, `bls_vintage/BLS_VINTAGE_INVESTIGATION.md`; plus
  parent-round artifacts `events_bbo_coverage/bls_dates.json` (A5) and
  `cme_cal/nq_es/nq_cal_coverage.json` (A1). Every number below re-verified
  against the committed JSON at 72c9bc5b (spot-check exit codes in handoff).
- Labels on every substantive claim: **OBSERVED** (artifact + field) /
  **MECHANISM_HYPOTHESIS** (unmeasured causal story) / **INFERENCE**
  (argument from evidence, flagged) / **NOT_RUN** (missing evidence is never
  PASS). **No new web numerics were fetched this lane** — all numerics are
  repo artifacts; therefore no new captures/log (disclosed in handoff).
- Cross-symbol designs belong to sibling P1-CROSS; everything here is
  single-symbol.

---

## 0. Standing context all families inherit (cite-once block)

### 0.1 Corrected cost law (batch-1, commit 72c9bc5b)

- Corrected tier-1/Fixed all-in FEES ES and NQ = **2.24 USD/side**
  (0.85 commission + 1.38 exchange + 0.01 reg; glued-superscript erratum;
  tiered T2-T4 ES/NQ = 2.04/1.84/1.64) [OBSERVED,
  `FEES_CORRECTED.md` §2, sha256 006d6372…]. All **MODELED COST**,
  SOURCE=PUBLIC_REFERENCE, **VERIFIED_VS_ACCOUNT=NOT_RUN**; **fee values
  UNDER REVIEW until a new A7 re-audits** [OBSERVED, FEES_CORRECTED §6].
- Per-side MODELED totals used by every family below (composition follows
  SPEC_PB1_ES §5 law: fees + spread half-turn proxy + slippage tier):
  - **ES**: S1 2.24+6.25+12.50 = **20.99** · S2 = **33.49** · S3 = **45.99**
    (spread half-turn proxy 6.25 from 1.0-tick close-proxy full spread,
    high-biased; slippage 1/2/3 ticks × $12.50 = assumption D1).
  - **NQ**: S1 2.24+16.25+5.00 = **23.49** · S2 = **28.49** · S3 = **33.49**
    (spread half-turn proxy 16.25 from 6.5-tick close proxy, high-biased,
    particularly so for NQ; slippage 1/2/3 ticks × $5.00 = assumption D1).
  - The words "measured"/"complete" applied to cost are FORBIDDEN; BBO true
    spread NOT_RUN; account verification NOT_RUN.

### 0.2 Calendar authority (batch-1 + parent A1)

- ES expirations **68/68 quarters** (was 63/68; 5 gap quarters closed with
  dual archived product-calendar captures) [OBSERVED,
  `EQ_GAPFILL_EVIDENCE.md` Gap 1, sha256 8ee5fc23…]. NQ expirations **68/68**
  (36 product + 32 family; zero divergence cross-checks); NQ holidays 17/17
  years authority-backed [OBSERVED, `nq_cal_coverage.json`, sha256
  ad7f4b3a…].
- **ES/NQ-specific 2026 Globex holiday session times: NOT_OBTAINED**
  (widget-only; full blocked-transport trail saved) [OBSERVED,
  EQ_GAPFILL_EVIDENCE Gaps 2-3]. NQ product-level early-close times 2011 and
  2021-2025 NOT_TRANSCRIBED [OBSERVED, nq_cal_coverage limits].
- Binding exclude-days law (unchanged): any day whose session calendar is
  uncertain ⇒ **EXCLUDE/NOT_RUN**, never inferred-pass. Concretely: every
  2026 dubious Globex day is excluded fail-closed until the widget class is
  unlocked.

### 0.3 BLS vintage law (batch-1) and the PIT upgrade

- CPI/EMPSIT calendars are now **PASS_EVIDENCED_CALENDAR**: 17/17 years
  2010-2026, 204 CPI + 204 EMPSIT scheduled dates, all printed "08:30 AM"
  Eastern (= 07:30 CT), per-year wayback snapshot as as-of verifier
  [OBSERVED, `bls_dates.json` sha256 ad41d2a7… + `BLS_PIT_EVIDENCE.md`].
  This **supersedes** the v3 addenda's "CPI/NFP calendars NOT_RUN" (the NQ
  a4 `cpa_nfp_status.status: "NOT_RUN"` block is stale on this point — it
  predates A5's landing; both citations recorded here).
- **Vintage law** [OBSERVED, `BLS_VINTAGE_INVESTIGATION.md` sha256
  2b18f6ce…]: for decision date D the correct expected-release calendar is
  the schedule vintage as known at D, pinned by dated capture. 2025 lapse in
  appropriations: CPI Oct-ref Nov-13 and EMPSIT Oct-ref Nov-7 **canceled**;
  CPI Sep-ref Oct-15→24, Nov-ref Dec-10→18; EMPSIT Sep-ref Oct-3→Nov-20,
  Nov-ref Dec-5→16; 2025 actual prints **11 CPI / 10 EMPSIT**. Recurrence in
  2026 (CPI Jan-26 Feb-11→13; EMPSIT Jan-26 Feb-6→11). Actual-publish
  latency and any surprise/consensus content: **NOT_RUN** (calendars only).

### 0.4 Session/roll bindings (era-correct, frozen construction law)

- ES closes: 16:30 CT →2012; 16:15 CT 2013→Nov-2015; 16:00 CT since
  Nov-2015; pre-2016 break-tails separated [OBSERVED, ES addendum §3].
- NQ closes: Mon-Thu 16:15 CT →2015-09-18; 16:00 CT since 2015-09-21;
  Friday 15:15 CT through Oct-2012 (126 era-A sessions) [OBSERVED, NQ
  addendum §3].
- Roll: ES **T-5** (66/66; deviation 0..−2 sessions; Juneteenth shift
  2026-06-18, 2027-06-17; June-2021 NOT shifted); NQ **k=5 volume-crossover
  + cease-guard** (66 rolls; daily-crossover DTE median 7, n=62) [OBSERVED,
  ES_roll_stats.json / NQ_a3_term.json].
- Era splits used by every family's regime field: **2010-16 / 2017-21 /
  2022-26** (the OVN-share/K1 convention) plus, where the artifact measured
  it so, FOMC data-eras 2016-19 / 2020-22 / 2023-26.

### 0.5 The registered parent pair (NOT re-specified here)

The PB1-linked OVN pair — **M-A/M-B (ES)** and **M-A′/M-B′ (NQ)**:
q80-strict-past OVN tail, CONT vs REV, both tails, K1-K5 + NEW-1..NEW-4 —
remains exactly as specified in the v3 addenda §8-§11. **Anti-multi-trial
rulings by this lane** (OBSERVED reasoning, standing):
1. **OVN-variance-share regime conditioning is NOT a new family** — it is
   already K1/NEW-1 evaluation views on the existing pair; registering it
   separately would be a disguised re-parameterization of the same m.
2. **Roll-window microstructure is NOT a standalone ES family** — ES roll
   rule is a validated construction constant (T-5 66/66); the carry-era
   spread-sign flip (39 neg / 27 pos; 61/66 sign match vs DFF−1.8pp proxy,
   proxy NOT PIT) is an **era-break field** for existing families, not a
   mechanism about session behavior [OBSERVED, ES_roll_stats.json].
3. For NQ the roll theme partially survives as family **NQ-F4** below,
   because there the evidence (corr 0.999, phantom drift) is about chain
   construction itself, and NEW-4 is binding.

Family IDs: **ES-F1/F2/F3/F4** and **NQ-F1/F2/F3/F4**. Census and ranking in
`RANKING_INPUT.md` (same directory).

---

# PART I — ES families

## ES-F1 `FOMC-RES` — FOMC scheduled-uncertainty resolution vs pre-positioning unwind

**(1) Mechanism + microstructure.**
- **M-RES (continuation arm) [MECHANISM_HYPOTHESIS]**: FOMC statement
  releases resolve scheduled uncertainty at a *known minute*. Heterogeneous
  interpretations diffuse through the book gradually (headline first,
  rates-path implications repriced over minutes-to-hours, presser at +30m
  re-ignites processing), so the immediate release-window move *persists*
  into the RTH close.
- **M-UNW (reversal arm) [MECHANISM_HYPOTHESIS]**: the same suppression
  evidence shows the crowd deliberately stands aside pre-release and a
  thin, one-sided book sets the first prints; the release-minute spike is
  over-extension that the returning RTH liquidity fades.
- Constraining anatomy [all OBSERVED, `ES_fomc_stats.json` sha256
  228fe2d4…]: release 15-min bucket **2.906× volume / 3.188× |1m ret|**;
  pre-release −120→−15 min **0.724-0.805× flat suppression**; **+30m
  2.653×** (presser onset) and +45m 2.506× — a *second* processing wave
  M-RES predicts and M-UNW must explain away; reaction peak **median +1
  min** (55% at minutes 0-1, 76% ≤5 min, n=91); day-level RTH volume ×1.14,
  range ×1.38 (131 in-data statements). Both arms registered together,
  falsification-by-competitor (D-law), mirroring the parent pair.

**(2) Expected direction IF true (falsifiable sign, no PnL claim).**
- M-RES: sign(RTH 13:01→close) agrees with sign(release-window move
  13:00→13:30) more often than the weekday-matched non-event clock placebo,
  stable across the three FOMC data-eras, surviving S2 modeled cost.
- M-UNW: the opposite sign statement (retrace). If BOTH arms fail K2-class
  floor at S1, family dead. [MECHANISM_HYPOTHESIS, pre-registered]

**(3) PIT feature availability.**
- 92 timed statements 2016-01-27+ (85 @14:00 ET; 7 irregular, listed) from
  as-issued HTML; day-level only for 40 statements 2011-2015 [OBSERVED,
  ES_fomc_stats.json header; ES addendum §5]. Minute-anchored arms scored
  **2016+ only**; 2011-15 day-level descriptive views only. 2010 meetings
  absent from the archive [OBSERVED]. Surprise/decision-content
  conditioning: **NOT_RUN** (no consensus archive). Statement text itself
  not needed for this family.

**(4) Contract/unit/session/timezone/expiry/roll bindings.**
- ES, mult 50, tick 0.25 ($12.50/tick), quotes in index pts, America/
  Chicago. Release minute mapped 14:00 ET → **13:00 CT** (DST exact
  2010-2026; no session ever clock-distorted [OBSERVED, ES addendum §3]).
- Entry anchors: **D0 = first 1m bar ≥13:01 CT; D30 = first 1m bar ≥13:30
  CT** (presser onset; the +30m bucket is measured at 2.653×). Irregular
  times (e.g. 2020-03-15 17:00 Sun) enter at their own release+1min;
  Sunday/holiday sessions ⇒ EXCLUDE per era law.
- Exit: era-correct RTH close (§0.4); expiry law incl. Juneteenth
  2026-06-18; chain per T-5; flat before roll-session close.

**(5) Entry/stand-aside/exit [PROVISIONAL] (PB1 discipline).**
- Fill = **open of NEXT 1m bar** after the anchor (conservative fill law;
  no limit/queue claims). Delay pair {+1m, +30m} = **two scored
  identities** (K4-class delay adjudication). TP 2.0×SL; SL = 1.0× median
  prior-20 RTH session ranges (strict past, era-correct marks, short/
  flagged sessions excluded); same-bar touch of both ⇒ **SL priority**;
  mandatory time-exit at era-correct RTH close; warmup 252 sessions.
- Stand-aside: (i) irregular-time statements on half/weekend days ⇒
  EXCLUDE unless the session is a normal RTH day; (ii) calendar-uncertain
  days ⇒ EXCLUDE/NOT_RUN (§0.2); (iii) RTH-core coverage <60% ⇒ EXCLUDE;
  (iv) days where the release minute falls in a data gap ⇒ EXCLUDE that
  event (count disclosed). **Zero overlap with PB1**: PB1 base-EXCLUDEs all
  132 FOMC statement days; this family scores exactly that excluded set —
  complementary partition, not a re-trial [OBSERVED partition argument].

**(6) Baselines/placebo/negative controls.**
- C1-C4 pattern (C1 seeded clock placebo seed 20261002-class with a *new*
  disclosed seed; C2 always-in-RTH on event days; C3 flat anchor; C4
  dose-response in release-window |move|).
- **Family-specific negative control NC-1**: weekday-matched non-FOMC days,
  same 13:00/13:30 CT clock, same entry/exit machinery — if the clock alone
  (lunch-hour microstructure) produces the pattern, the mechanism is fake.
  Must show NOTHING beyond C2 baseline.
- Era views 2016-19/2020-22/2023-26 + tri-era 2010-16/2017-21/2022-26
  (day-level only for the latter's 2011-15 leg).

**(7) Refutation conditions (mechanism kills first).**
- **F1-K1 era instability**: surviving arm's sign flips across the three
  data-eras ⇒ participation-era artifact, kill family.
- **F1-K2 both arms below Stage-A floor at S1 (1-tick, 20.99/side modeled)
  ⇒ dead; re-tparameterization FORBIDDEN.**
- **F1-K3 concentration**: ≥80% of contribution from 2020-03..04 ⇒ kill.
- **F1-K4 delay flip**: sign flips between +1m and +30m entries ⇒
  presser-onset artifact, downgrade to descriptive.
- **F1-K5 placebo reproduction**: NC-1 clock control reproduces the
  pattern ⇒ mechanism not specific to information release, kill.
- **F1-K6 anatomy reproduction gate (pre-scoring)**: re-measured on the
  era-correct session mapping, the release bucket must again show ≥2×
  volume and pre-release ≤0.85× suppression; if the committed anatomy fails
  to reproduce, family never enters scoring [construction gate].
- Cost survival statement: whatever survives must survive **S2 (33.49/
  side)** with S1/S3 flanks reported; fee values UNDER REVIEW (§0.1).

**(8) Cost/spread/slippage sensitivity.** MODELED COST only: ES S1 20.99 /
S2 33.49 / S3 45.99 per side (composition §0.1); spread proxy high-biased;
slippage assumption D1; event-minute entries plausibly face worse-than-
median fills but **no slippage claim beyond the {1,2,3}-tick tier triple is
legal** (double-stress forbidden).

**(9) Regime/era breaks.** Data-eras above; tri-era views; carry-era
roll-spread sign (§0.5-2) as a covariate view only. 2011-15 day-level leg
analyzed separately, never pooled with minute-anchored results.

**(10) Coverage/hole proof.** 16.4y panel 2010-06-06→2026-10-01, 4,204
sessions, 0 OHLC violations [OBSERVED, ES addendum §6]. Event n: 92 timed
(91 with 1m data) + 40 day-level; armed-sample arithmetic for the
minute-anchored arms ≈ 91 events × tail-split — **thin per-cell n is a
published power limitation** (per-cell 1σ dominates; single-seed placebo
limitation inherited). Deferred tails/calendar-spreads excluded by
construction. Family needs nothing unavailable beyond §3's declared
NOT_RUNs.

**(11) Sources.** ES_fomc_stats.json (sha256 228fe2d4…); ES addendum §5
(sha256 d18d5422…); federalreserve.gov archive (counts as cited there);
FEES_CORRECTED.md; EQ_GAPFILL_EVIDENCE.md. Full sha256 table in
`esnq_hypotheses.json`.

## ES-F2 `MACRO-0730` — scheduled CPI/NFP-day 07:30 CT spike conditioning

**(1) Mechanism + microstructure.**
- **M-MS-CONT [MECHANISM_HYPOTHESIS]**: the scheduled 08:30 ET macro print
  discharges accumulated overnight uncertainty into the thinnest part of
  the Globex day; the 07:30 move is genuine information that the RTH book
  only slowly incorporates ⇒ the sign of the 07:30-window move persists
  into RTH.
- **M-MS-REV [MECHANISM_HYPOTHESIS]**: the same spike is thin-book
  over-extension (pre-RTH, minimal dealer inventory); RTH liquidity fades
  it — the event-morning analog of M-B.
- Constraining anatomy [OBSERVED]: E7 (2023-10..2026-10) hour profile
  07:00h CT = **3.0% of daily volume (0.0302) and |1m| 1.61 bp** — the most
  active pre-RTH hour [`ES_session_stats.json` hour_profiles, sha256
  f4e24ce3…]; three of ES's ten >2% 1m jumps sit exactly at 07:30 CPI
  minutes (2022-09-13, 2022-10-13, 2022-11-10) [ES addendum §5]. 07:30
  spike anatomy **per-era** (2010-16, 2017-21): **NOT_RUN** — must be
  measured before any scoring era is extended (see F2-K6).

**(2) Expected direction IF true.** M-MS-CONT: sign(RTH 08:30→close) agrees
with sign(07:29→08:29 reaction window) on scheduled-release days more than
on weekday-matched non-release days, stable across eras *in which the 07:30
anatomy reproduces*, surviving S2. M-MS-REV: opposite. If the
scheduled-vs-non-release contrast is null for both arms ⇒ the calendar
carries no conditioning information (G7-class verdict) [MECHANISM_
HYPOTHESIS, pre-registered].

**(3) PIT feature availability.**
- Scheduled-release calendars: **PASS_EVIDENCED_CALENDAR** — CPI 204 +
- EMPSIT 204 dates 2010-2026, all 08:30 ET, per-year snapshot verifiers
  [OBSERVED, bls_dates.json sha256 ad41d2a7…] **with the vintage law**
  (§0.3): decision-date-keyed vintage; 2025 has 11 CPI / 10 EMPSIT actual
  prints; canceled-but-expected days (2025-11-13 CPI, 2025-11-07 EMPSIT)
  are themselves information and form a falsification subset (below).
- Surprise/direction-of-print conditioning: **NOT_RUN** (no PIT consensus
  archive; H3 blocker) ⇒ arms are **price-measured only** (sign of the
  07:30-window move, strict past). Actual-publish latency NOT_RUN ⇒ the
  reaction window is defined on schedule-time ± band, not on feed-latency
  claims.

**(4) Bindings.** ES units/timezone per §0.4. Reaction window r = log(px
08:29 / px 07:29) CT (both minutes inside the Globex day; era-correct close
marks for C_prev contexts). Entry anchors: **D0 = first 1m bar ≥08:30 CT;
D30 = ≥09:00 CT** (delay pair = two scored identities). Expiry/Juneteenth/
T-5 per §0.4. Release-day DST check: 08:30 ET↔07:30 CT conversion exact
(all transitions weekend-internal) [OBSERVED, ES addendum §3].

**(5) Entry/stand-aside/exit [PROVISIONAL].** PB1 discipline identical to
ES-F1 (fill = next-bar open; TP 2.0×SL; SL 1.0×ATR(20d RTH); SL priority;
era-correct RTH-close time exit; warmup 252d). Stand-aside: (i) release
days that are also FOMC days ⇒ EXCLUDE (event-stacking contamination,
disclosed); (ii) **vintage-law days**: for every decision date the
release-day set is the as-known vintage; expected-but-canceled 2025 days
are scored ONLY in the falsification subset, never in the main arms;
(iii) 2026 Globex-uncertain days ⇒ EXCLUDE (§0.2); (iv) RTH-core coverage
<60% ⇒ EXCLUDE. **Overlap ruling**: PB1 does NOT exclude CPI/NFP days;
this family conditions on a *different signal* (07:30-window sign vs OVN
17:00→08:30 tail) — overlap with PB1 armed days exists and is **disclosed**;
the two families' identities remain distinct constructions (different m,
different entry clock). Multi-trial accounting: all ES-F2 identities are
new and additive ⇒ census marks them BLOCKED_TRIAL_BUDGET (see RANKING_
INPUT).

**(6) Baselines/placebo/negative controls.** C1-C4 pattern + **NC-2
weekday-matched non-release-day 07:30 clock** (same machinery, no
scheduled print ⇒ must show NOTHING beyond C2); **NC-2b canceled-day
falsifier**: 2025-11-13 / 2025-11-07 expected-but-canceled days — if
"scheduled-day" conditioning fires on days the print never arrived, the
mechanism is calendar artifact, not information [family-specific,
vintage-law-enabled].

**(7) Refutation conditions.** F2-K1 era instability (across eras where
anatomy reproduced); F2-K2 both arms below S1 floor ⇒ dead; F2-K3 2020-03..
04 concentration ≥80% ⇒ kill; F2-K4 delay flip 08:30 vs 09:00 ⇒
cash-open-push artifact; F2-K5 NC-2/NC-2b reproduction ⇒ kill; **F2-K6
anatomy pre-gate**: 07:30-vs-neighbor minute-volume spike must reproduce in
each scoring era (else that era is descriptive-only — the spike is a
participation-era feature on NQ evidence, and ES pre-2016 is unmeasured)
[construction gate]. Cost: survive S2 33.49/side with S1/S3 flanks; fees
UNDER REVIEW.

**(8) Cost/spread/slippage.** §0.1 ES tiers; no claim beyond the tier
triple; 07:30 fills occur in the thinnest pre-RTH hour — the {1,2,3}-tick
tiers are the ONLY sensitivity axis (no ad-hoc event-day surcharge may be
invented; that would be double-stress).

**(9) Regime/era breaks.** Tri-era mandatory; separate views for
pre-2016/modern session-close eras; carry-era covariate view; 2025
vintage-break treated as a structural annotation, not an era.

**(10) Coverage/hole proof.** Panel §ES-F1(10). Event n: ~204 CPI + ~204
EMPSIT scheduled days 2010-2026 minus FOMC-stacked/uncertain excludes;
2025 uses 11/10 actual prints per vintage law. Armed-day thinness per
cell disclosed at census time. Everything else needed is available;
surprise conditioning remains NOT_RUN and is NOT invented.

**(11) Sources.** bls_dates.json + BLS_PIT_EVIDENCE.md (sha256 ad41d2a7… /
8f616615…); BLS_VINTAGE_INVESTIGATION.md (2b18f6ce…); ES_session_stats.json
hour_profiles (f4e24ce3…); ES addendum §5/§7; FEES_CORRECTED.md.

## ES-F3 `COT-CROWD` — positioning-extreme regime conditioning (vol-first, direction gated)

**(1) Mechanism + microstructure.**
- **M-CROWD-VOL [MECHANISM_HYPOTHESIS]**: at extremes of noncommercial net
  positioning, the marginal trader is crowded; subsequent adverse moves
  trigger cascading stops/unwinds ⇒ forward realized volatility is
  elevated at BOTH tails — measured, U-shaped.
- **M-CROWD-DIR (gated, INFERENCE)**: if crowd-unwind risk is real, OVN
  moves *against* the crowded side on extreme weeks should extend further
  (stop-cascade continuation) rather than mean-revert — a directional
  asymmetry claim the v2 evidence does NOT yet support (vol only);
  registered as gated second stage only.
- Constraining anatomy [OBSERVED, `ES_cot_stats.json` sha256 51fa8964…]:
  fwd-21d rv medians by net-position quintile **Q1 14.85 / Q2 11.86 / Q3
  12.72 / Q4 12.39 / Q5 14.36** (n=922 usable releases 2009-01→2026-08);
  extreme deciles 16.75 (most-short) / 15.95 (most-long); fwd-dd21 deeper
  at both tails (−3.66/−3.23 vs −2.58/−2.62 mid). PIT convention:
  positions as-of Tuesday, released Friday 15:30 ET, as-published
  no-revision, forward windows start next session [FACT cftc.gov; OBSERVED
  ES addendum §2]. NQ contrast: consolidated line era sign-flips = honest
  null ⇒ **no NQ analogue registered** [OBSERVED, NQ addendum §12-6].

**(2) Expected direction IF true.** Vol leg (primary, no PnL): conditional
next-session range/|ret| on Q1∪Q5 weeks exceeds Q3 weeks, strict-past
conditioning, stable sign across tri-eras. Directional leg (gated): the
crowd-against OVN-tail continuation-vs-reversal differential is signed
against the crowded side. If the vol leg fails at session granularity, the
directional leg is never scored [pre-registered gate].

**(3) PIT availability.** CoT legacy "E-MINI S&P 500" exact-name line,
1,082 weekly rows 2006→2026-09-22 as-published [OBSERVED, ES addendum §2];
quintile thresholds must be computed **strict-past** (trailing window,
no full-sample quantiles — full-sample quintiles in the committed table are
descriptive, not PIT). TFF/disaggregated: NOT_RUN (100% null). Everything
needed is in-repo.

**(4) Bindings.** ES per §0.4; conditioning day = first session after the
Friday 15:30 ET release (weekend information discharge — Sunday reopen
1.5-2.9× weekday 17:00 volume [OBSERVED, ES_session_stats sunday_open]);
T-5 chain; era-correct closes; Juneteenth law.

**(5) Entry/stand-aside/exit [PROVISIONAL].** Stage 1 (descriptive, 0
scored identities): session-granularity vol contrast Q1∪Q5 vs Q3, strict-
past quintiles. Stage 2 (gated): arms {crowd-fade, crowd-continue} × tails
{OVN move against crowd, with crowd}, D0 entry 08:30 CT only, tier S2,
PB1 exit/TP/SL discipline verbatim. Stand-aside: FOMC-day EXCLUDE base
(day-level 132 statements); calendar-uncertain EXCLUDE; warmup 252d.

**(6) Baselines/placebo/negative controls.** C1-C4 pattern; **NC-3
Q3-mid-quintile placebo**: same machinery on positioning-neutral weeks ⇒
must show nothing; **NC-3b dose control**: monotone Q2/Q4 intermediates
should sit between Q3 and tails if the mechanism is graded crowding
(non-monotone ⇒ artifact suspicion).

**(7) Refutation conditions.** F3-K1: vol U-shape fails to reproduce at
session granularity strict-past ⇒ family never enters scoring (kills the
gated leg by construction); F3-K2 both directional arms below S1 floor ⇒
dead; F3-K3 era instability; F3-K4 2020-03..04 concentration; F3-K5
NC-3/NC-3b reproduction (including a flat dose profile). Cost: survive S2
with flanks; fees UNDER REVIEW.

**(8) Cost/spread/slippage.** §0.1 ES tiers apply to the gated leg only;
the vol leg costs nothing and claims nothing.

**(9) Regime/era breaks.** Tri-era; net-position regime level shifts
disclosed via the by-year table (2006-2026 medians committed); the CoT
contamination incident (fixed, exact-name filter) is inherited as a
construction note [OBSERVED, ES addendum §12-6].

**(10) Coverage/hole proof.** n=922 usable releases; weekly cadence ⇒
armed weeks thin per tail (≈2×~185 per tail quintile pre-excludes);
session-granularity analysis uses the same 16.4y panel. No unavailable
input beyond declared NOT_RUNs (TFF).

**(11) Sources.** ES_cot_stats.json (51fa8964…); cftc.gov schedule
convention per ES addendum §2; ES_session_stats sunday_open; FEES_
CORRECTED.md.

## ES-F4 `RUN-REV` — multi-day run reversal vs continuation (RTH session mapping)

**(1) Mechanism + microstructure.**
- **M-RR [MECHANISM_HYPOTHESIS]**: ES daily closes exhibit horizon-dependent
  mean reversion; after k consecutive same-sign sessions (or a large
  cumulative k-session move), the next RTH session fades the run
  (overreaction correction / inventory normalization at the cash open).
- **M-RG [MECHANISM_HYPOTHESIS]**: competing — momentum-carry regime: runs
  continue within trending regimes; the reversion is a crisis-only
  artifact (concentrated in E5-type episodes).
- Constraining anatomy [OBSERVED, `ES_regime_stats.json` sha256
  623ef90e…]: acf1_daily per era **−0.1091 / +0.0144 / −0.0652 / −0.038 /
  −0.2432 / +0.0034 / −0.0885** (negative 5/7 eras; the dossier §0.5 "6/7"
  prose is a disclosed inconsistency, JSON is authority); VR_q5 **0.795-0.955
  (<1 in ALL 7 eras)**. NOTE honestly: these are daily-close statistics;
  the *session-level* mapping (fade at 08:30 vs fade through the day) is
  unmeasured ⇒ anatomy-to-verify pre-gate required (F4-K6).

**(2) Expected direction IF true.** M-RR: conditional on a k=5-session run
(strict past, era-correct closes), sign(RTH session return) opposes the run
more often than the seeded random-sign placebo and more than no-run days
(dose), stable across tri-eras, surviving S2. M-RG: sign agrees
(continuation). Both fail ⇒ no conditioning information in runs (G7-class).

**(3) PIT availability.** Fully in-repo: run length from the VOL chain
closes (strict past); no external feature. Nothing NOT_RUN.

**(4) Bindings.** ES per §0.4; run defined on era-correct closes (16:30/
16:15/16:00 CT) — a hard-coded 16:00 close would corrupt pre-2016 runs
[construction note]; `prev_short` sessions excluded from run counting
(flagged, sensitivity view); T-5 chain; Juneteenth law.

**(5) Entry/stand-aside/exit [PROVISIONAL].** Arms {FADE, GO} × tails
{run-up, run-dn}; k=5 primary (k=3 sensitivity view, NOT a separate
identity grid without budget); D0 entry 08:30 CT only; PB1 fill/TP/SL/exit
discipline verbatim; warmup 252d; FOMC-day EXCLUDE base; calendar-uncertain
EXCLUDE.

**(6) Baselines/placebo/negative controls.** C1-C4 pattern; **NC-4 no-run
days control** (|5-session cumulative move| below its trailing median,
same clock): if FADE fires equally on no-run days, the run carries no
information; **NC-4b sign-shuffled run labels** (seed disclosed).

**(7) Refutation conditions.** F4-K1 era instability (esp. M-RG predicts
E5-concentration — F4-K3 drops window ≥80% from 2020-03..04); F4-K2 both
arms below S1 floor; F4-K4 delay flip if a D30 view is ever added;
F4-K5 NC-4/NC-4b reproduction; **F4-K6 anatomy pre-gate**: intraday
placement of run-reversal (open vs close) must be measured descriptively
before scoring — if reversal is purely an overnight-close phenomenon the
RTH-session family is mis-specified and dies pre-registration. Cost: S2
survival with flanks; fees UNDER REVIEW.

**(8) Cost/spread/slippage.** §0.1 ES tiers; nothing beyond the tier
triple.

**(9) Regime/era breaks.** Tri-era mandatory; VR/acf1 per-era table is the
pre-registered instability reference; carry-era covariate view.

**(10) Coverage/hole proof.** 16.4y; armed-day count ≈ runs of length ≥5
occurrence rate (disclosed at census; daily-horizon conditioning gives far
fewer armed days than PB1 — thin-power warning pre-registered). Deferred
tails excluded; break-tails never enter run counting.

**(11) Sources.** ES_regime_stats.json (623ef90e…); ES addendum §2/§8
(5/7-vs-6/7 disclosure); FEES_CORRECTED.md.

---

# PART II — NQ families (contingent register: census is contingency only)

Standing precondition for ALL NQ families [OBSERVED, NQ addendum §9]: NQ
enters a registered cycle only after (i) cost gate — now unblocked-in-
principle by the corrected 2.24/side MODELED fee but **UNDER REVIEW until
A7 re-audit**; (ii) trial-ceiling arithmetic; (iii) calendar authority +
exclude-list (17/17 holidays + 68/68 expirations landed; 2026 Globex times
NOT_OBTAINED; early-close times 2011/2021-25 NOT_TRANSCRIBED); (iv)
**full-era rebuild on the alias-recovered series** (only 2020 aggregates
re-measured; §1 distribution rows still hole-era) — F4-style families that
lean on a1/a2 aggregates carry this as an explicit precondition.

## NQ-F1 `FOMC-ERA` — same-information/thinner-book FOMC release conditioning

**(1) Mechanism + microstructure.**
- **M-NQ-CONT [MECHANISM_HYPOTHESIS]**: information ratio at release is
  era-STABLE (|ret| ratio 2.24-2.44× across eras) while the volume spike
  diluted 2.99→1.46× — the same news now spreads through a book whose
  participation sits ~1/5 overnight; processing is slower ⇒ post-release
  persistence into the close should be era-strengthening.
- **M-NQ-UNW [MECHANISM_HYPOTHESIS]**: the release minute itself prints
  3.53× volume in the thinnest context — first-print over-extension that
  reverts; the NQ reaction peak sits in the SECOND 30 min (30-60m 2.637× >
  0-30m 2.256×) vs ES's +1-min peak, i.e. NQ's immediate print is
  relatively less informed ⇒ revert.
- Constraining anatomy [all OBSERVED, `NQ_a4_events.json` sha256
  5a09aff9…]: lull −60..0 **0.683×** (deepest measured window); 0-30m
  **2.256×**; 30-60m **2.637×**; release-minute **3.53×**; era table
  2016-19/2020-22/2023-26: lull 0.80→0.79→**0.59**, h0-30 vol 2.99→2.25→
  **1.46**, h0-30 |ret| 2.25→2.44→**2.24**; day-level n=128: volume ×1.06,
  RTH vol ×1.11, range ×1.12.

**(2) Expected direction IF true.** M-NQ-CONT: sign(13:01→close) follows
sign(13:00→13:30) with the contrast vs placebo WEAKENING in volume terms
but PERSISTING in sign, era-stable, surviving S2 (28.49/side). M-NQ-UNW:
retrace, and (its distinguishing prediction) the reversal fraction should
be largest where the immediate spike ratio is largest. Both null ⇒ dead.

**(3) PIT availability.** Identical FOMC archive basis as ES (132
statements; 92 timed; 84 clean 14:00-ET events with release windows;
2011-15 day-level) [OBSERVED, NQ_a4_events]. Surprise conditioning NOT_RUN.

**(4) Bindings.** NQ units (mult 20, tick 0.25 = $5.00); k=5+cease-guard
chain; era-correct NQ closes (§0.4 incl. Friday-15:15 era-A rule and the
disclosed phantom-session 2020-11-01 cache artifact — rebuild note);
release 14:00 ET → 13:00 CT; Juneteenth 2026-06-18 expiry law shared with
ES family.

**(5) Entry/stand-aside/exit [PROVISIONAL].** Same PB1 discipline as
ES-F1 with NQ anchors (D0 13:01 CT / D30 13:30 CT — D30 deliberately
coincides with NQ's measured 30-60m peak window); TP 2.0×SL; SL 1.0×
median prior-20 NQ RTH ranges; SL priority; era-correct NQ close time
exit; warmup 252d; stand-aside identical to ES-F1 + the NQ calendar gate
(2026 Globex-uncertain EXCLUDE; NOT_TRANSCRIBED early-close days treated
as calendar-uncertain until transcribed ⇒ EXCLUDE fail-closed).

**(6) Baselines/placebo/negative controls.** C1-C4 pattern with own seeds;
**NC-5 weekday-matched non-FOMC 13:00 CT NQ clock** (must show nothing);
era views per the measured table.

**(7) Refutation conditions.** NQ-F1-K1 era instability (measured era
table is the pre-registered reference); K2 both arms below S1 floor
(23.49/side — note NQ S1 is NOT cheap: 6.5-tick spread proxy dominates);
K3 2020-03..04 concentration; K4 delay flip; K5 placebo reproduction;
K6 anatomy reproduction pre-gate. Cost: survive S2 28.49 with flanks;
fees UNDER REVIEW; **K5-symbol note**: opposite sign vs ES-F1 outcome
would be a symbol-specific downgrade under the parent K5 law (cross-
symbol comparison belongs to the ES cycle's report; recorded here as
contingency).

**(8) Cost/spread/slippage.** §0.1 NQ tiers (23.49/28.49/33.49); spread
proxy 16.25 high-biased particularly for NQ; nothing beyond the tier
triple; margin cap ≤1 ct @100k noted for sizing-sensitive metrics.

**(9) Regime/era breaks.** Data-eras 2016-19/2020-22/2023-26 (as
measured) + tri-era; OVN-share level shift ~2018-19 (10.2%→23.8%
trajectory) is the participation covariate behind the mechanism —
pre-registered interpretation, not a rescue.

**(10) Coverage/hole proof.** NQ panel 6,688,533 outright bars, 4,219
held sessions 2010-06-07→2026-10-01, 0 integrity violations [OBSERVED, NQ
addendum §6]; alias window recovered via id-16908 rule; deferred stray
clusters excluded; minute-anchored arms 2016+ only (n=84 clean 14:00-ET);
2020 window fully measured post-recovery. Full-era rebuild precondition
applies to any aggregate re-used.

**(11) Sources.** NQ_a4_events.json (5a09aff9…); NQ addendum §5 (e78548a6…);
FEES_CORRECTED.md; nq_cal_coverage.json; BLS/PIT not needed here.

## NQ-F2 `MACRO-0730-NQ` — era-gated macro spike-day conditioning

**(1) Mechanism + microstructure.**
- **M-NQ-MS [MECHANISM_HYPOTHESIS]**: on NQ the 07:30 concentration is a
  *participation-era feature* (2023-26 spike present; 2017-20 absent) —
  macro information now arrives when ~1/5 of daily volume is already
  overnight; arms CONT (spike extends into RTH) vs REV (thin-book spike
  fades), scored only in eras where the anatomy reproduces.
- Constraining anatomy [OBSERVED, `NQ_a4_events.json`
  cpa_nfp_status.calendar_free_evidence_0730ct]: 2023-26 minute-volume
  share **0.00185 at 07:30 vs 0.00041 at 07:25** (≈4.5× neighbor);
  |1m ret| 0.077% approaching the cash-open minute's 0.086%; the quiet
  2017-20 era showed NO such spike (0.088% share, |ret| 0.031%) [OBSERVED,
  NQ addendum §5]. The NQ-specific calendar-free block is now *joined* by
  the PIT calendar (§0.3) — the family is specified on calendar-day
  conditioning, direction-agnostic or price-sign based only.

**(2) Expected direction IF true.** Within scoring eras (anatomy-gated),
sign(RTH) follows (CONT) or opposes (REV) the 07:29→08:29 window sign,
vs NC-6 non-release clock; effect confined to spike-eras while absent in
2017-20 would itself CONFIRM the participation mechanism (pre-registered
interpretation — a null in non-spike eras is mechanism-consistent, not a
failure); must survive S2.

**(3) PIT availability.** Same BLS calendars + vintage law as ES-F2
(PASS_EVIDENCED_CALENDAR 204+204; surprise NOT_RUN; latency NOT_RUN).
NQ-side per-era spike anatomy 2010-16: NOT_RUN (must be measured; only
2017-20 vs 2023-26 contrast committed).

**(4) Bindings.** NQ units/closes/roll per §0.4 and NQ-F1; 07:30 CT
anchors; FOMC-stacked days EXCLUDE; vintage law incl. canceled-day
falsifier subset.

**(5) Entry/stand-aside/exit [PROVISIONAL].** D0 08:30 CT / D30 09:00 CT
delay pair; PB1 discipline verbatim; era gate: scoring eras = those
passing the F2-K6-style anatomy pre-gate (on committed evidence: 2023-26
only ⇒ ~3.7-4y scoring window, thin-power pre-registered; 2017-20 and
2010-16 as mechanism-contrast descriptive views, never pooled).

**(6) Baselines/placebo/negative controls.** C1-C4 pattern; **NC-6
weekday-matched non-release 07:30 NQ clock**; **NC-6b canceled-day
falsifier** (2025 vintage subset, identical to ES-F2's NC-2b); plus the
**era-contrast control**: the 2017-20 null era is itself the
family-specific negative control — if the effect appears equally in the
no-spike era, the mechanism is not macro-spillover but generic clock.

**(7) Refutation conditions.** K1 era instability *within* scoring eras;
K2 both below S1 floor; K3 2020-03..04 concentration; K4 delay flip;
K5 NC-6/6b reproduction; K6 anatomy gate (07:30 spike reproduction per
scoring era); additionally **K7 thin-era kill**: if effect appears ONLY in
the anatomy-absent eras, family dead (inverted mechanism). Cost: survive
S2 28.49 with flanks; fees UNDER REVIEW.

**(8) Cost/spread/slippage.** §0.1 NQ tiers; NQ needs a proportionally
larger per-trade move to clear identical tick costs vs ES at half the
per-tick dollar value — structural, quantified only in a registered cycle
[INFERENCE, parent §7 framing].

**(9) Regime/era breaks.** Scoring era gated by anatomy (2023-26 on
committed evidence); OVN-share shift 2018-19 is the covariate; 2025
vintage break annotated.

**(10) Coverage/hole proof.** NQ panel per NQ-F1(10); scoring window thin
(~3.7y × ~22 CPI+NFP days/yr ≈ ~160 event days pre-excludes — armed-cell
power limitation pre-registered; census contingency only). Full-era
rebuild precondition inherited.

**(11) Sources.** NQ_a4_events.json cpa_nfp_status (5a09aff9…); bls_dates
+ BLS vintage docs (§0.3); NQ addendum §5; FEES_CORRECTED.md;
nq_cal_coverage.json.

## NQ-F3 `RUN-REV-NQ` — multi-day run reversal on the strongest reversion substrate

**(1) Mechanism + microstructure.**
- **M-NQ-RR [MECHANISM_HYPOTHESIS]**: NQ exhibits the strongest multi-day
  mean reversion in the 10-symbol set — VR(5/20/60) = **0.808/0.711/0.669**
  (VR(20) p10-p90 0.522-0.850), acf1 full-era **−0.076** (rolling-252
  median −0.042, p10-p90 −0.134..+0.071) [OBSERVED, `NQ_a1_regimes.json`
  trend_persistence, sha256 66efedc7…] — after k-session runs, the next
  RTH session fades; competitor M-NQ-RG (trend regime) mirrors ES-F4.
- Honest disclosure [OBSERVED, NQ addendum §6/§12-4]: these aggregates are
  computed on the pre-recovery series; the alias window (2018-08→2020-05)
  contributes contaminated thin sessions that never won k=5, but the
  full-era rows have NOT been re-measured on the recovered series —
  **full-era rebuild is a hard precondition** for this family.

**(2)-(5)** Mirror ES-F4 fields with NQ bindings (units, k=5+cease-guard
chain, era-correct NQ closes incl. Friday-15:15 era-A exclusion from run
counting, D0 08:30 CT entry, PB1 discipline verbatim, FOMC-day EXCLUDE,
calendar gate per NQ-F1). Distinctive pre-gate: **NQ-F3-K6 anatomy
pre-gate = the full-era rebuild itself** plus the intraday-placement
measurement (F4-K6 analog).

**(6) Controls.** NC-4/NC-4b analogs with own seeds; **NC-7
ES-contrast view** (descriptive, cross-symbol comparison only in reports —
NQ VR depth vs ES's shallower 0.80-0.95 VR(5) is the pre-registered
substrate contrast; no cross-symbol identity is registered here).

**(7) Refutation.** K1 era instability; K2 both below S1 (23.49); K3
2020-03..04 concentration — especially binding here because the recovered
2020 episode (−34.12% DD, worst day −11.15%) will dominate any reversion
statistic [OBSERVED, NQ2020_ADDENDUM]; K4 delay (if D30 added); K5
placebo; K6 rebuild+placement gates. Cost: S2 28.49 survival with flanks;
fees UNDER REVIEW.

**(8)-(10)** §0.1 NQ tiers; tri-era breaks with the OVN-share shift as
covariate; coverage = NQ panel with 4,219 held sessions, armed-day
thinness pre-registered; deferred tails + stray clusters excluded;
NEW-4-style chain audit mandatory before any scoring (see NQ-F4).

**(11) Sources.** NQ_a1_regimes.json (66efedc7…); NQ2020_ADDENDUM.md +
nq2020_remeasure.json (per parent evidence index); NQ addendum §6/§8;
FEES_CORRECTED.md.

## NQ-F4 `ROLLWK` — roll-week liquidity-migration conditioning + binding chain-integrity check

**(1) Mechanism + microstructure.**
- **Role A (binding construction check — inherits and hardens NEW-4)**
  [OBSERVED hazard]: corr(roll-day gap, trailing spread level) = **0.999**;
  unadjusted-chain embedding **+723/+1,014/+907/+810 pts/yr 2023-26**
  (~4-5%/yr phantom drift) vs −5..−31 pts/yr 2010-16 [OBSERVED,
  `NQ_a3_term.json` sha256 07dde36e…]. Any NQ evaluation must pass a
  switch-day jump audit (post-adjustment switch-day |return| distribution
  indistinguishable from non-switch days) or the RUN is killed
  (construction failure, not hypothesis failure).
- **Role B (family, INFERENCE-grade) [MECHANISM_HYPOTHESIS]**: during the
  k=5 migration window the two books' liquidity splits (S-curve D−5 2% →
  D−1 81% → D0 87%; calendar-rule holds traded at median 1.4% of front
  volume [OBSERVED, NQ_a3_term/NQ_DEEP_v2 §3]) ⇒ OVN sessions inside roll
  weeks are thinner than matched non-roll OVN sessions ⇒ over-extension
  (REV-type) behavior is amplified in roll weeks. **The roll-week ×
  session-type interaction itself is NOT_RUN — it was never measured**;
  this family therefore carries an explicit anatomy-to-verify list and is
  ranked lowest (see RANKING_INPUT).
- ES analogue explicitly NOT registered (§0.5-2).

**(2) Expected direction IF true.** Descriptive primary: roll-week OVN
session |move|/range exceeds weekday-matched non-roll weeks (strict-past
roll calendar from k=5 rule). Gated secondary: OVN-tail REV-vs-CONT
differential is more REV in roll weeks than non-roll weeks. Both are
pre-registered sign statements without PnL claims.

**(3) PIT availability.** Fully in-repo: roll dates from the k=5 rule
(decide t−1, hold t); spread/gap series committed; no external input;
nothing NOT_RUN except the interaction measurement itself.

**(4)-(5)** NQ bindings per NQ-F1; conditioning window = the 5 sessions
straddling each of 66 rolls; PB1 discipline for the gated leg (D0 08:30 CT,
era-correct exit); FOMC EXCLUDE; calendar gate.

**(6) Controls.** C1-C4 pattern; **NC-8 mid-quarter matched clock**
(sessions ≥10 days from any roll): must show nothing; **NC-8b roll-week
day-of-week balance check** (roll dates cluster on specific weekdays —
weekday matching is mandatory to avoid a disguised weekday effect).

**(7) Refutation.** K1 era instability (carry-era sign flip of the
calendar premium −0.8%→+5.0%/yr makes pre-2022 vs post-2022 roll weeks
structurally different [OBSERVED]); K2 both below S1; K5 placebo; **K6
anatomy gate = the NOT_RUN interaction must first be measured
descriptively — failure kills Role B pre-registration**; Role A audit
failure kills any NQ run regardless of family (standing law).

**(8)-(10)** §0.1 NQ tiers (gated leg only); era breaks = carry eras
(ZIRP-negative vs 2023-26-positive premium); coverage 66 rolls × ~5
sessions ≈ 330 conditioned sessions — very thin, pre-registered;
census contingency only.

**(11) Sources.** NQ_a3_term.json (07dde36e…); NQ addendum §4/§11-NEW-4;
DATACONTRACT §1.3 row NQ; FEES_CORRECTED.md.

---

## Cross-cutting NOT_RUN register (family-blocking or scope-limiting)

1. Surprise/consensus conditioning (all macro families): NOT_RUN — no PIT
   consensus archive (H3, unchanged); direction-agnostic or price-sign
   designs only.
2. Actual-publish latency (BLS feeds): NOT_RUN — reaction windows defined
   on schedule time; no latency claim anywhere.
3. BBO true spreads / fills: NOT_RUN — close-proxy spreads only,
   high-biased; fill = next-bar open law.
4. Account fee verification: NOT_RUN; fee values UNDER REVIEW pending new
   A7 audit (FEES_CORRECTED §6).
5. ES/NQ-specific 2026 Globex holiday session times: NOT_OBTAINED ⇒ 2026
   dubious days excluded fail-closed in every family.
6. NQ product early-close times 2011, 2021-2025: NOT_TRANSCRIBED ⇒ those
   days calendar-uncertain ⇒ EXCLUDE until transcribed.
7. NQ full-era rebuild on alias-recovered series: outstanding — hard
   precondition for NQ-F3, inherited by NQ-F2/F4 aggregates.
8. FOMC minute anatomy 2011-2015: absent ⇒ day-level views only.
9. NQ TFF/disaggregated CoT: NOT_RUN (100% null) — no NQ positioning
   family registered.
10. OVN-variance-share regime split and roll-window ES conditioning:
    ruled evaluation-views/construction constants (§0.5), NOT families.

— End of ESNQ_HYPOTHESES.md. No PnL computed, no selection performed, no
PASS claimed without evidence; SPEC_PB1_ES r3 untouched; all parameters
[PROVISIONAL]; outcome-blind throughout.
