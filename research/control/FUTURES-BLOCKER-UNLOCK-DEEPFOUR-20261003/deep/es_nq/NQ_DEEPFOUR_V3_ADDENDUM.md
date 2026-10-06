# NQ_DEEPFOUR_V3_ADDENDUM — E-mini Nasdaq-100 deep-four research v3 addendum

- Task: **FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003**, lane **B1-DEEP-ESNQ**
  (NQ document; ES sibling in `ES_DEEPFOUR_V3_ADDENDUM.md`).
- Generated (UTC): 2026-10-03. Worktree
  `/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/prep` @
  `7149425df83b7c47f34848fc83d36e450b802bc5`, branch
  `prep/futures-behavior-10syms-20261002` (re-measured at dispatch; no drift).
- Class: PREP deep-research addendum. **0 PnL, 0 scored runs, 0 signal
  selection, 0 conditional mean-return tables.** NQ is a **sibling design
  CONTINGENT on the cost gate** (exchange fee NOT_FETCHED); it is NOT part of
  any current cycle scope and enters only after the gate opens and the
  24-identity ES ceiling arithmetic is re-checked (PLAYBOOKS §1: "NQ sibling:
  chỉ tính thêm khi trần còn và cost gate D2 mở").
- Evidence base (read-only): `FUTURES-DEEPRESEARCH-V2-20261003/dossiers_v2/
  NQ_DEEP_v2.md` (errata F1-F6 applied) + `analysis/NQ_a*.json`;
  `FUTURES-DATACONTRACT-QUAL-V1/` (DATACONTRACT_QUALIFICATION §1/§2/§3,
  PLAYBOOKS_DRAFT r5, SUMMARY_QUAL_ACTIONS r6) incl.
  `analysis/nq2020_remeasure/NQ2020_ADDENDUM.md` (alias-recovered 2020
  re-measurement, erratum A7-DC-F2 applied); `FUTURES-ES-V1-PACKET/`
  (referenced for the sibling structure only — NOT NQ scope);
  `research/wayfinder/{MAP,HYPOTHESIS_LEDGER,SURVIVORS}.md` (ancestry).
- Taxonomy on every claim: **FACT** / **OBSERVED** (script + window) /
  **POSTULATED** / **NOT_RUN**. Sibling-lane outputs (A1-CMECAL-NQES,
  A4-FEES, A5-EVENTS-BBO-COVERAGE) in-flight at write time: REQUIREMENTS
  recorded, results never fabricated.

---

## 1. Identity & registry

- Contract: E-mini Nasdaq-100, CME Globex. Multiplier **20** USD/index-pt;
  minimum tick **0.25** index pts = **$5.00/tick**; quotes plain index points
  [FACT, DATACONTRACT §1.1 row NQ].
- Registry: **111 one-digit-year symbol time-clusters (4 stray single-print
  clusters excluded: NQZ6 2023-10-25, NQZ7 2025-05-30, NQZ7 2025-09-15,
  NQZ9 2025-02-14 — deferred-year prints outside any live contract window)**;
  decade-repeat symbols resolved by time-cluster matching (e.g. NQZ0 =
  Dec-2010 and Dec-2020) [OBSERVED, NQ_DEEP_v2 §7; `NQ_build_cache.py`].
- **ALIAS-VIEW RULE (binding, id-16908)**: `instrument_id==16908 AND date <
  2020-06-01 → raw_symbol 'NQM0'` — the 2020 "vendor hole" is a vendor
  SYMBOLOGY ALIAS (raw_symbol `NQU8-NQM9` 2018-08-15→2020-05-31: 92,075
  bars, 24,686,121 contracts; relabeled `NQM0` 2020-06-01→06-19: 19,406
  bars). Through the alleged hole id 16908 printed **58 trading dates,
  21,824,572 contracts** [OBSERVED, ERRATUM F1 / A7-NQ F1; adjudication
  `A_ALIAS_NOT_ABSENCE`; DATACONTRACT §1.1]. Panel integrity under the rule:
  0 duplicates, 0 high<low, 0 negative, 0 close-outside-range
  (NQ2020_ADDENDUM §5).
- Exclusions (binding, DATACONTRACT §1.6): calendar-spread instruments
  (641,787 rows dropped from 7,330,320 parent rows), stray clusters (above),
  maintenance-break bars, 2026-10-01 partial tail, roll-final depleted
  sessions.

## 2. PIT inventory (what is point-in-time-evidenced vs NOT_RUN)

| source | PIT status | evidence |
|---|---|---|
| FOMC statements | **PASS_EVIDENCED**: 132 statements 2011-01-26→2026-09-16 (archive = 147 files = 132 a-statements + 15 b/c notes [ERRATUM F5]); **92 carry "For release at" times (85 @14:00 ET, 7 irregular)**; 40 untimed 2011-2015 ⇒ day-level only there | FACT (federalreserve.gov archived HTML `nonprice/fed/statements/`); counts OBSERVED `NQ_a4_events.json` |
| CFTC CoT legacy | PASS_EVIDENCED as-published, Tuesday→Friday 15:30 ET release; analysis line = **NASDAQ-100 Consolidated `__ALT__` series, 850 rows 2010-06-15→2026-09-22** (post INTEGRATION-FIX-V2; loader re-pointed by ERRATUM F2 with hard guard — it silently selected 0 rows on the fixed tidy otherwise); canonical E-mini line 1,082 rows kept for owner context | FACT (cftc.gov); OBSERVED `NQ_a5_cot.json` |
| TFF / disaggregated CoT | **NOT_RUN** — normalized TFF values 100% null (metadata only); annual archives classification-backcast, not vintage-stable | NQ_DEEP_v2 §5 |
| US CPI/NFP calendars | **NOT_RUN** — `bls_gate/` empty, FRED `released_at=null`; only calendar-free 07:30 CT minute-spike evidence exists (§5); lane A5-EVENTS-BBO-COVERAGE in flight | OBSERVED absence; `NQ_a4_events.json` `cpa_nfp_status` |
| PIT consensus/surprise archive | **NOT_RUN** — H3 blocking item, unchanged | NQ_DEEP_v2 §6-H3 |
| Rates (DFII10/DFF) | latest-revised vintages only (NOT PIT-strict); ALFRED annual snapshots exist for sensitivity; daily-vintage PIT NOT_RUN | NQ_DEEP_v2 §6-H1 |
| GLBX statistics (OI) | 2023-10+ only, publication lag next-morning disclosed | OBSERVED, NQ_DEEP_v2 §3 |
| BBO quotes/depth | **NOT_RUN** — never purchased; bbo-1m insufficient for fill/queue proof (D5) | DATACONTRACT §1.7 |

## 3. Session by era / DST

- Era close-marks (measured from bars): **Mon-Thu close 16:15 CT through
  2015-09-18 → 16:00 CT from 2015-09-21; Friday close 15:15 CT through
  2012-10** (last full month; mixed Nov-2012; none from Dec-2012; **126
  era-A Friday-early-close sessions** [ERRATUM F6: was 123]) [OBSERVED,
  NQ_DEEP_v2 §2/§7; `NQ_a2_sessions.json` `friday_early_close_eraA`].
- DST proof: **32/32 expected March/November transitions show the correct
  modal UTC hour flip (22Z↔23Z), 0 unexpected flips** 2010-2026 [OBSERVED,
  `NQ_a7_quality.json` `dst_evidence`]. A fall-back session-date arithmetic
  bug (timedelta vs wall-clock) was found AND fixed during the v2 study
  (35 affected Sunday-evening clusters; lib fix + caches rebuilt + A1/A2
  re-run) — disclosed incident, not latent [OBSERVED, NQ_DEEP_v2 §7].
- Break-tail handling: 5,266 maintenance-break straggler bars inside the
  era-correct break window 2010-2015 (median 4 lots, ~10 bars/session,
  predominantly deferred contracts) — excluded from session aggregates;
  era-B violations: 37 bars total [OBSERVED, NQ_DEEP_v2 §7].
- Cache artifact disclosed: the delivered v2 cache contains a **phantom
  session 2020-11-01** (DST fall-back Sunday-open chunk assigned to Sunday;
  current lib code assigns it to Monday 11-02) — 260 vs 259 session rows,
  +0.08pp on 2020 ann vol, return sum unaffected [OBSERVED,
  NQ2020_ADDENDUM §1/§4-3]. Flagged for the full-era rebuild.
- Overnight weight (the headline NQ structure): full-overnight volume share
  **10.2% (2010) → 15.8% (2016) → 22.5% (2019) → 19-24% (2023-26; 2023-26
  endpoint 23.8% in 2026)** — the Globex session roughly DOUBLED its weight,
  with a level-shift ~2018-2019 [OBSERVED, `NQ_a2_sessions.json`
  `yearly_overnight_share`; ERRATUM-era note N1: mean-of-per-session shares;
  aggregate-volume variant differs ≤0.5pp]. Design consequence: an RTH-only
  NQ design leaves ~1/5 of daily volume and its information flow unmodeled.

## 4. Roll & calendar

- **Roll rule (frozen construction rule, not alpha): PIT k=5
  volume-crossover + cease-guard** — at each session close t, compare
  trailing-5-session mean volume of next quarterly vs current; decide on
  data through t, hold new from t+1; **cease-guard**: if the held contract
  stops trading (<25% bars or volume≈0 for the session) before the rule
  switches, force-switch to the next quarterly at that close (6J-lesson
  guard, applied program-wide to volume-rule symbols) [OBSERVED rule;
  DATACONTRACT §1.3 row NQ].
- Roll evidence: **66 rolls**; daily-volume crossover (persistent new>old for
  3 consecutive sessions) occurs **median 7 days before the old contract's
  3rd-Friday expiry (p10 4, p90 7, min 3, max 7; n=62 valid** — rolls with
  dte>45d excluded as 2020 alias artifacts) [OBSERVED,
  `NQ_a3_term.json` `daily_volume_crossover_dte`]; k=5 smoothing rolls
  ~2-3 sessions later than the daily crossover (disclosed).
- Migration S-curve: new-contract share of two-contract volume around roll:
  D−5 2% → D−3 42% → D−1 81% → D0 87% → D+3 ~100% [OBSERVED, NQ_DEEP_v2 §3].
- **v1-declared calendar rule measured UNFIT**: on the first 10 sessions of
  each calendar-rule hold window (n=650), held-contract volume = **median
  1.4% of market-front volume (p10 0.3%; 78% of sessions below 50%)** — it
  holds near-dead books ~2 weeks/quarter [OBSERVED, NQ_DEEP_v2 §3]. The
  vol-comparison formerly used against it is re-anchored: 19.6% (calendar
  rule) vs **20.1%** (volume rule, n=4,168 returns) [ERRATUM F3 — pre-audit
  "16.9%" not reproducible; direction reverses].
- Roll-gap structure: corr(roll-day gap, trailing-10-session spread level) =
  **0.999** — the roll gap IS the calendar spread. **Unadjusted-chain
  embedding per year: 2023 +723 pts, 2024 +1,014, 2025 +907, 2026-YTD +810
  (~4-5% of price/yr)** vs −5 to −31 pts/yr in 2010-2016 — any backtest on
  unadjusted NQ chains manufactures a ~4%/yr phantom trend in the modern era
  [OBSERVED, NQ_DEEP_v2 §3]. Calendar premium sign flips by rate era
  (−0.8%/yr ZIRP era → +5.0% 2023-24; financing−dividend mechanism
  POSTULATED, not decomposed).
- OI crossover: precedes volume-crossover roll by 2-3 days in the 8
  artifact-free events (2023-10+, range −3..−2, small n, publication lag
  disclosed) — OBSERVED-2023+, not era-general [NQ_DEEP_v2 §3].
- **CALENDAR AUTHORITY STATUS (current gaps)**: NQ holidays/early-closes are
  **NOT_RUN official** — the v2 holiday evidence is inferred (119 short
  sessions by last-trade-gap method, "disclosed, not exchange-asserted";
  plus the 126 measured era-A Friday closes) [OBSERVED-inferred,
  `NQ_a2_sessions.json` `holiday_short_sessions`]. NQ expirations have no
  authority extraction yet (3rd-Friday rule is bar-validated by the 62-roll
  DTE analysis, not exchange-calendar-proven).
- **REQUIREMENTS lane A1-CMECAL-NQES is filling (in-flight; results NOT_RUN
  here)**: (R3) **NQ holidays + early-closes 2010-2026 and NQ quarterly
  expirations** from official/archived-official sources (same evidence class
  as the ES D3 r6 extraction: source URL + capture date + verbatim-vs-derived
  flag; ≤2 attempts/URL/method; no inference gap-fill). Integration law once
  it lands: every NQ day not proven at day-level ⇒ EXCLUDE/NOT_RUN for a
  future NQ cycle (mirroring SPEC_PB1_ES §2-E1); the 119 inferred short
  sessions become cross-checks, not authority [FACT — lane scope,
  `dispatch/DISPATCH_MANIFEST.json` lanes.A1-CMECAL-NQES].

## 5. Events

- FOMC day-level: **128 matched clean sessions** (of 132 statements) vs
  same-weekday ±21d non-event control: session volume ×1.06, RTH volume
  ×1.11, true range ×1.12; 60%/62% of days above-control volume/range
  [OBSERVED, `NQ_a4_events.json` `fomc_day_level`; control pool includes
  sessions after the event — descriptive convention, disclosed A7-NQ N3].
- Release-window anatomy (84 clean 14:00-ET events 2016-2026; medians):
  pre-release −120..−60 **0.799×**; −60..0 **0.683×** (the pre-FOMC lull);
  0..+30 **2.256×**; +30..+60 **2.637×** (peak in the second 30 min);
  +60..+120 1.445×; +120..+180 1.344×; **release minute itself ×3.5
  volume** [OBSERVED, `NQ_a4_events.json` `fomc_2pm_release_windows` +
  NQ_DEEP_v2 §4].
- Era shift (2016-19 vs 2023-26): lull deepened 0.80→0.59×; volume spike
  diluted 2.99→1.46×; **information ratio (|1m ret| ×) stable 2.2-2.4×** —
  same news spread over a market whose volume now sits more overnight
  [OBSERVED, `fomc_release_hour_by_era`].
- Special-time statements (release-time proofs, listed, never aggregated):
  2019-10-11 11:00, 2020-03-03 10:00, 2020-03-15 17:00 (Sun emergency),
  2020-03-23 08:00, 2020-03-31 08:30, 2020-08-27 09:10, 2025-08-22 10:00 ET
  [FACT from as-issued HTML; OBSERVED list].
- **CPI/NFP: NOT_RUN** (no calendar; fabrication forbidden). Calendar-free
  07:30 CT evidence: 2023-26 minute-volume share **0.185% at 07:30 vs
  0.041% at 07:25** (2-4× neighbor spike; |1m ret| 0.077% approaching the
  cash-open minute 0.086%); the quiet 2017-20 era showed NO such spike
  (0.088% share, |ret| 0.031%) — macro-morning concentration is a
  recent-era feature, not a fixed constant [OBSERVED,
  `cpa_nfp_status.calendar_free_evidence_0730ct`; NQ_DEEP_v2 §2].
- LAW: volume/|ret|/range timing only; no mean-return tables, no ranking.

## 6. Coverage & data quality

- Window: 16.3-16.4y — panel 2010-06-06 22:00Z → 2026-09-30 23:59Z; **4,219
  held sessions 2010-06-07→2026-10-01** (a1, NaN-aware); 4,016 clean RTH
  sessions of 4,170 (a2, coverage ≥0.6; 154 excluded low-coverage)
  [OBSERVED, `NQ_a1_regimes.json` `panel`; `NQ_a2_sessions.json`].
- Panel: **6,688,533 outright 1m bars**; 0 duplicates (symbol, minute), 0
  non-monotonic streams, 0 negative prices, 0 high<low, 0 close-outside,
  0 zero-volume bars; price range 1,699.25→31,454.75 pts [OBSERVED,
  NQ_DEEP_v2 §7].
- **2020 alias episode RESOLVED**: recovered at $0 via the id-16908 view
  rule; the v2 dossier's hole-aware numbers are SUPERSEDED for 2020 by the
  NQ2020_ADDENDUM re-measurement: **2020 yearly log-ret +38.43% (was
  +13.20%), ann vol 34.88% (was 33.54% "lower bound"), max DD −34.12% (was
  −32.28%), COVID episode 02-27→trough 2020-03-20 (close 6,920.25)→06-05,
  fall 16 / recovery 54 sessions (all real); worst day −11.15% @2020-03-12
  (dossier prose date 03-16 was wrong — minor erratum recorded), best +8.85%
  @2020-03-13; rvol20 max 88.65% @2020-03-30; rvol60 max 60.24% @2020-05-18.
  Decomposition: +32.65pp recovered hole returns − 7.42pp roll-week
  restatement** [OBSERVED, `nq2020_remeasure.py`/`.json`; DATACONTRACT §1.6-6
  and §3-5 mark this DONE]. March-2020 roll verification: k=5 fires at close
  **2020-03-19** (trail5 NQM0 428,574 > NQH0 229,267 [ERRATUM A7-DC-F2 —
  the "~357k" figure did not reproduce; date unaffected]); the old series'
  03-20 return (+3.39%) was stale-print contaminated (dying NQH0 last print
  7,453.50 vs liquid front 6,920.25, +7.7% same-index discrepancy) and is
  replaced by −3.75% [OBSERVED, NQ2020_ADDENDUM §4-2].
- Deferred tails excluded: the 4 stray clusters (§1) never enter chains;
  alias-window thin relabeled NQM0 H2-2019 sessions (~40 bars/day) never win
  the k=5 comparison and are never held [OBSERVED, NQ2020_ADDENDUM §4-5].
- Full-era §1 distribution rows (percentiles/ACF/VR) NOT re-measured on the
  recovered series — only the flagged 2020 aggregates and rvol 20/60 maxima;
  flagged for a full-era rebuild before any registered NQ cycle
  [OBSERVED-disclosure, NQ2020_ADDENDUM §6].

## 7. Spread / cost (all MODELED COST; NQ cost statement BLOCKED)

- Close-proxy spread: **median full spread 6.5 ticks = $32.50** → half-turn
  $16.25 — a **high-biased proxy, particularly so for NQ** (6.5 ticks vs ES
  1.0 tick); no BBO ⇒ no true-spread claim [OBSERVED-proxy, DATACONTRACT
  §1.7 row NQ].
- **MODELED COST status — cost-gate OPEN**: commission IBKR public $0.85/side
  [FACT, IBKR public pricing, LIVE_OFFICIAL 2026-10-03]; **exchange fee
  NOT_FETCHED ⇒ no all-in figure may be quoted for NQ; the cost statement is
  BLOCKED** [FACT(status), DATACONTRACT §1.7/§3-1]. NFA regulatory 0.02
  (0.01 for 2014-10-01→2017-12-31) per the official NFA timeline [FACT];
  slippage tiers {1,2,3} ticks = **$5/$10/$15 per side** — **research
  assumption D1, not a measurement**.
- Margin: initial/maint **42-46k/contract** (2 public sources, <2% apart)
  [FACT-public, DATACONTRACT §1.7]. BBO true spread: NOT_RUN.
- Lane A4-FEES is currently fetching the public NQ schedule (IBKR plan/tier
  + CME exchange + NFA, URL + effective date each) — results NOT_RUN at this
  write time; when it lands, NQ all-in becomes quotable as MODELED COST
  (never "measured/complete"), and the sibling decision gate can be
  adjudicated.
- Structural cost asymmetry vs ES (design-relevant): proxy half-turn $16.25
  vs ES $6.25 at HALF the per-tick risk granularity — the same 1-tick
  slippage tier is $5 vs $12.50 per side, but the per-point multiplier (20 vs
  50) means SL distances in index units translate to ~2.5× smaller dollar
  risk per point. Net: NQ needs a proportionally LARGER per-trade move to
  clear identical tick costs — quantified only inside a registered cycle
  (no PnL here) [POSTULATED arithmetic framing].

## 8. Economic mechanism (POSTULATED — both directions registered together)

Mirrors the ES pair (falsification-by-competitor), with NQ-specific anatomy
as constraints:

- **M-A′ Overnight information accumulation (→ CONT)**: Globex information
  (Asian/European sessions + the 07:30 CT macro slot) accumulates in a book
  that now carries ~1/5 of daily volume, and RTH pricing catches up slowly.
  Constraining observations: **OVN volume share doubled 10.2%→23.8% with a
  level shift ~2018-19** [OBSERVED, §3]; 07:30 CT minute-volume spike 2-4×
  neighbors in 2023-26 with |1m ret| near the cash-open magnitude
  [OBSERVED, §5]; FOMC information ratio stable while volume spikes diluted
  — news is processed at the same rate in a thinner-volume profile
  [OBSERVED, §5].
- **M-B′ Thin-book over-extension (→ REV)**: the OVN tail is an
  over-extension of a thin crowd that the RTH book fades. Constraining
  observations: **VR(5)=0.81, VR(20)=0.71, VR(60)=0.67** — q-day variance
  materially below q×1-day variance at ALL measured horizons: multi-day
  mean reversion, not momentum, dominates NQ daily returns across the full
  era (VR(20) 10-90p range 0.522-0.850) [OBSERVED, `NQ_a1_regimes.json`
  `trend_persistence` (ERRATUM F4 values)]; ACF(1) full-era **−0.076**
  (rolling-252d median −0.042, p10-p90 −0.134..+0.071) [OBSERVED].
- NQ-specific tension the design must carry: the VR evidence (M-B′ support)
  is measured on DAILY closes, while the OVN-share doubling (M-A′ support)
  is a participation-regime shift — the H4 refined-spec failure condition
  already encodes this: continuation sign unstable across the OVN-share eras
  ⇒ participation artifact, not signal [POSTULATED; NQ_DEEP_v2 §6-H4].
- The 2023-26 **unadjusted-chain phantom drift (+4-5%/yr)** is a
  construction hazard, not a mechanism: it must be eliminated by roll
  adjustment before ANY conditional evaluation, else both arms are
  contaminated [OBSERVED hazard, §4].

## 9. Hypothesis + counter-hypothesis pair [PROVISIONAL] — NQ sibling field table

**Status: SIBLING, CONTINGENT on the cost gate.** Structure mirrors
PB1-ES / SPEC_PB1_ES r3; nothing here is registered, frozen, or scheduled.
Entry into any cycle additionally requires: (i) A4-FEES NQ schedule landed
(MODELED COST quotable), (ii) trial-ceiling arithmetic re-checked (ES cycle
consumes 24; NQ identities are additive and need their own budget), (iii)
A1 calendar authority + exclude-list, (iv) full-era rebuild on the
alias-recovered series (§6).

Test question (same as PB1): does a large overnight move (17:00 CT→08:30 CT
open, strict-past q80 tail) systematically continue or reverse inside RTH
after modeled costs? Arms **NQ-CONT** (sign(m)) and **NQ-REV** (−sign(m))
registered simultaneously, both tails.

| field | specification [PROVISIONAL — sibling] | delta vs SPEC_PB1_ES r3 |
|---|---|---|
| Universe | NQ only; held chain per contract §1.3: **k=5 PIT volume-crossover + cease-guard** (not T-5) | roll rule |
| Signal | m = log(open_0830 / C_prev); C_prev = actual prior-session close at **NQ era-correct marks: Mon-Thu 16:15 CT →2015-09-18, 16:00 CT since 2015-09-21; Friday 15:15 CT through 2012-10/Nov-2012**; `prev_short` flag on prior short/Friday-early sessions (sensitivity view); uncertain prior calendar ⇒ EXCLUDE/NOT_RUN; \|m\| ≥ q80(\|m\|, trailing-252d, strict-past) | C_prev era table (NQ's Friday-15:15 era is NQ-specific) |
| Entry | first 1m bar 08:30 CT (D0) / 09:00 CT (D30); fill = open of NEXT 1m bar | same |
| Delay pair | {0, +30m} = two mandatory scored identities (K4 pair) | same |
| Stand-aside | FOMC day-level base-EXCLUDE (132 statements incl. untimed) / FOMCIN sensitivity; calendar-uncertain days EXCLUDE/NOT_RUN (NQ official calendar NOT_RUN until A1 lands — until then a NQ cycle is BLOCKED, not inferred-pass); RTH-core coverage <60% EXCLUDE; warmup 252d; **2020 alias window INCLUDED only after the full-era rebuild lands** | calendar gate stricter |
| Session | era-correct RTH close per §3; break stragglers excluded | same law, NQ era dates |
| TP/SL | TP 2.0×SL-distance; SL 1.0× median prior-20 RTH session ranges (strict past, era-correct marks, flagged sessions excluded) | same |
| Same-bar TP/SL | SL priority, deterministic | same |
| Time exit | era-correct RTH close, mandatory flat | same |
| Roll | §1.3 k=5 + cease-guard; flat before roll close; roll affects reference chain only; **switch-day returns must be spread-adjusted** (corr 0.999 — an unadjusted chain embeds ±4-5%/yr phantom drift, §4) | adjustment emphasis |
| Sizing | risk 0.5%/trade; margin cap: ~$42-46k/ct ⇒ ≤1 @100k at 4× coverage — **tighter than ES** | margin row |
| Cost | MODELED COST; commission 0.85 + NFA 0.02/0.01 known; **exchange NOT_FETCHED ⇒ all-in BLOCKED** (§7); slippage {5,10,15}/side = assumption D1; spread half-turn proxy $16.25 (high-biased) | cost gate open |
| Identities | NOT enumerated — enumeration belongs to a future NQ packet after the gate; any grid must mirror the ES A-r4 discipline (explicit identity table, controls C1-C4 scored, ceiling arithmetic, no hidden cells) | deferred |
| Counter-hypothesis | CONT vs REV registered together; C1 seeded clock placebo (own seed, disclosed single-seed limitation), C2 always-in-RTH, C3 flat, C4 dose-response unconditional | same class |

**K5 note (binding)**: if NQ and ES results have OPPOSITE sign (same
arm/tail/tier), the verdict is **symbol-specific downgrade — no family
claim** (PLAYBOOKS K5; SPEC §8 notes K5 not applicable to ES-only cycle;
it activates exactly when this sibling runs). Rationale from anatomy: NQ's
VR/ACF reversion profile and OVN-share trajectory differ measurably from ES
(§8), so sign divergence is a live possibility, not a formality
[POSTULATED].

## 10. Ancestry & placebo

**Ancestry verdict (same honest search as ES)**:
- **No prior scored ancestor for equity-index futures exists in this
  program** (wayfinder MAP/HYPOTHESIS_LEDGER/SURVIVORS searches for
  e-mini/Nasdaq/equity-index futures families return zero scored families)
  ⇒ **NOT_RUN/none-locatable in-family**. The v1 NQ dossier was prep-class
  descriptive only (14-16 months true volume; no scored runs); its W2
  window is now placed at the **57th percentile** of the 2010-2024 rvol20
  distribution — a neutral mid-regime sample that never saw the era's tails
  (43.6% DD / 92% rvol) [OBSERVED, `NQ_a1_regimes.json`
  `v1_window_context`].
- Nearest dead families (FX-spot session/open — must NOT be transplanted
  without evidence): **FOREX-FREE-V1 `FXFV1-A3-P1` London-open continuation**
  REJECT (−2.35/trade, PF 0.849, 3/3 folds negative, 11,459 trades);
  **FOREX-FREE-V2 Tokyo-range→London expansion / London-AM break+retest**
  REJECT (EXPECTANCY_NONPOSITIVE; placebo reproduced behavior);
  program-level "session/open FX momentum/fade rejected at high trade
  counts (cost-dominated)"; DAYTRADER-100-V1 FX session books cost-marginal,
  die at ×2.0 [OBSERVED registry rows]. NQ-relevant twist: NQ's cost hurdle
  is HARSHER than those corpses' venue (proxy spread 6.5 ticks; fee
  NOT_FETCHED) — the FX cost-domination lesson transfers as a warning, not
  as a veto [POSTULATED transfer argument, explicitly flagged].
- Placebo/controls C1-C4 (class identical to ES §10; when a NQ packet is
  drafted): C1 seeded clock/random-sign placebo (own PnL path, scored;
  single-seed single-delay limitation disclosed — no permutation-robustness
  claim); C2 always-in-RTH baseline (scored); C3 flat anchor (ledger); C4
  OVN-direction-unconditional dose-response (scored).
- **POWER discussion [POSTULATED]**: clean-session base 4,016 (a2) − 252
  warmup − ~131 FOMC day-excludes − calendar-uncertain excludes (NQ starts
  with ZERO authority days until A1 lands; post-A1 the E1-class excludes
  should be tens/yr) ≈ **~3,500-3,600 eligible sessions**, ~700-740 armed
  q80-tail sessions pooled per arm (~350-370 per tail×arm at D0). NQ daily
  σ ≈ 126 bp at 20.1% ann vol ⇒ per-cell 1σ ≈ 6-7 bp/session — only
  effects ≳0.05σ/day distinguishable at 1σ; slightly WEAKER power than ES
  per session at the same cell count, and the K3 window (2020-03..04) is
  now measured (not hole-bridged) with a DEEPER DD (−34.1%) — expect the
  COVID fold to dominate variance, which is precisely what K3 guards.
  Thin-power warnings: era-fold n as low as ~600-800 armed sessions per
  2-3y fold; single-seed C1 anchors the null assignment only; NQ margin cap
  (≤1 ct @100k) adds discretization noise to any sizing-sensitive metric.

## 11. Refutation tests (mechanism-level falsifiers)

K-series inherited from the PB1 framework (pre-registered class; each names
its observable + evidence container):

- **K1 era sign-stability across OVN-share eras 2010-16 / 2017-21 / 2022-26**
  (evaluation views, 0 new identities). Kill: sign/expectancy unstable ⇒
  participation artifact — for NQ this is the PRIMARY test because the OVN
  share doubled across exactly these eras (10.2%→23.8%) [OBSERVED basis;
  kill logic pre-registered; container: per-era views on existing paths].
- **K2 both arms below floor at S1 (1-tick) tier** ⇒ family dead; re-tparam
  forbidden [pre-registered; container: stage-A gate table]. NQ-specific
  caution: S1 dollar-cost $5/side slippage + $16.25 spread proxy — the S1
  tier is NOT "cheap" relative to NQ point value; still the floor tier.
- **K3 ≥80% contribution from 2020-03..04** ⇒ drop-window fail [container:
  monthly contribution decomposition]. NQ note: the window is now fully
  measured post-alias-recovery (§6) — the test is honest here in a way it
  could not be on the hole-aware series.
- **K4 delay 0 vs +30m sign flip** ⇒ open-microstructure artifact,
  adjudicated directly on the two delay identities [container: the delay
  pair cells].
- **K5 NQ-vs-ES divergence** (activates when this sibling runs): opposite
  sign vs ES ⇒ symbol-specific downgrade, no family claim (§9 K5 note)
  [container: cross-symbol comparison report].
- **NEW-1 OVN-participation artifact split [POSTULATED]**: condition the
  primary cells on trailing-year OVN volume-share median-split (strict
  past; shares from `NQ_a2_sessions.json` yearly series). Prediction: a
  structural session mechanism (M-A′/M-B′) shows the effect in BOTH halves;
  if it lives only in the high-share (post-2018) half, the effect is a
  participation-regime artifact and must be re-registered as such (new
  cycle, new budget), not rescued. Falsification: effect confined to
  high-OVN-share half ⇒ participation artifact verdict.
- **NEW-2 FOMC-exclusion information-source test [POSTULATED]**: contrast
  base-EXCLUDE vs FOMCIN arms; M-A′ predicts sensitivity to scheduled
  information proximity (07:30-slot days once A5 calendars land), M-B′
  predicts insensitivity to information source. Falsification: effect
  appears/vanishes/flips with FOMC inclusion ⇒ base arm was harvesting
  event-avoidance, downgrade and record [container: FOMCIN identities +
  07:30-slot descriptive split — the split is NOT_RUN until PIT CPI/NFP
  calendars exist].
- **NEW-3 dose-response gradient via C4 [POSTULATED]**: M-A′ predicts
  monotone conditioning value in |m|; M-B′ predicts the opposite gradient.
  Falsification: C4 (unconditional sign(m)) ≥ q80 primary ⇒ threshold
  carries no conditioning information ("no conditioning information"
  verdict, G7-class) [container: identity table + gate results].
- **NEW-4 roll-adjustment integrity check [POSTULATED, NQ-specific]**:
  because corr(roll gap, spread)=0.999 and the unadjusted drift is 4-5%/yr
  in 2023-26, any evaluated NQ series must pass a switch-day jump audit:
  post-adjustment switch-day |return| distribution must be statistically
  indistinguishable from non-switch days (else the adjustment failed and
  both arms are drift-contaminated). Falsification: switch-day return
  distribution shift ⇒ construction failure — kill the RUN (not the
  hypothesis), fix chain, re-run only with owner budget amendment
  [container: chain QA table in the future packet; basis: §4 OBSERVED].

## 12. Limitations & open questions

1. Everything §8-§11 mechanism/power is POSTULATED or arithmetic projection;
   the conditional-return question is NOT_RUN; NQ enters nothing until the
   cost gate + ceiling arithmetic + calendar authority + full-era rebuild
   are all closed.
2. Cost gate: exchange fee NOT_FETCHED (A4-FEES in flight); no all-in NQ
   figure exists or is quoted here; slippage is assumption D1; BBO NOT_RUN.
3. Calendar authority: zero official NQ holiday/early-close/expiry days at
   write time (A1-CMECAL-NQES in flight); inferred flags are cross-checks,
   never authority.
4. Full-era rebuild outstanding: §1 distribution rows (percentiles, ACF/VR)
   still computed on the hole-aware series; only 2020 aggregates + rvol
   maxima were re-measured (NQ2020_ADDENDUM §6). Also pending: regenerate
   `NQ_a7_quality.json`'s stale `vendor_hole_2020` block (typo + framing
   flagged by ERRATUM F6/F1 for regeneration, not hand-editing).
5. FOMC minute anatomy absent 2011-2015 (day-level only); CPI/NFP calendars
   NOT_RUN pending A5; PIT consensus NOT_RUN.
6. CoT conclusions are an honest null on the consolidated line (era
   sign-flips; only extreme-short shows mild persistent vol elevation) —
   positioning carries no design weight here [OBSERVED, NQ_DEEP_v2 §5].
7. Single-seed placebo limitation (class-wide); no permutation robustness.
8. Open questions for the owner: (a) priority of A4 NQ fee fetch vs ES cycle
   GO sequencing; (b) whether the full-era alias-recovered rebuild should be
   commissioned as its own prep task before any NQ packet is drafted;
   (c) whether NEW-4 (roll-adjustment audit) should be promoted to a
   binding pre-registration element for ALL future futures cycles.

— End of NQ_DEEPFOUR_V3_ADDENDUM. No PnL computed, no selection performed,
no PASS claimed without evidence; NQ remains sibling-after-cost-gate.
