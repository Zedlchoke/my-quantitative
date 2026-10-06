# ES_DEEPFOUR_V3_ADDENDUM — E-mini S&P 500 deep-four research v3 addendum

- Task: **FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003**, lane **B1-DEEP-ESNQ**
  (ES document; NQ sibling in `NQ_DEEPFOUR_V3_ADDENDUM.md`).
- Generated (UTC): 2026-10-03. Worktree
  `/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/prep` @
  `7149425df83b7c47f34848fc83d36e450b802bc5`, branch
  `prep/futures-behavior-10syms-20261002` (re-measured at dispatch; no drift).
- Class: PREP deep-research addendum. **0 PnL, 0 scored runs, 0 signal
  selection, 0 conditional mean-return tables.** ES cycle scope is UNCHANGED:
  SPEC_PB1_ES r3 (freeze-ready, 24 identities) is REFERENCED, never modified.
- Evidence base (read-only): `FUTURES-DEEPRESEARCH-V2-20261003/dossiers_v2/
  ES_DEEP_v2.md` (errata applied, incl. M-1/m-1/m-2/m-3/n-1) + its
  `analysis/ES_*.json`; `FUTURES-DATACONTRACT-QUAL-V1/DATACONTRACT_
  QUALIFICATION.md` + `PLAYBOOKS_DRAFT.md` (r5) + `SUMMARY_QUAL_ACTIONS.md`
  (r6); `FUTURES-ES-V1-PACKET/SPEC_PB1_ES.md` (r3) + `PLAN_futures_es_v1.md`;
  `research/wayfinder/{MAP,HYPOTHESIS_LEDGER,SURVIVORS}.md` (ancestry).
- Taxonomy on every claim: **FACT** (primary source + date/URL) / **OBSERVED**
  (script + window) / **POSTULATED** (mechanism, unmeasured) / **NOT_RUN**
  (missing evidence is never PASS). Sibling-lane outputs (A1-CMECAL-NQES,
  A4-FEES, A5-EVENTS-BBO-COVERAGE) are in-flight at write time: this document
  records their REQUIREMENTS, never their results.

---

## 1. Identity & registry

- Contract: E-mini S&P 500, CME Globex. Multiplier **50** USD/index-pt;
  minimum tick **0.25** index pts = **$12.50/tick** [FACT, DATACONTRACT §1.1
  row ES; corroborated SPEC_PB1_ES §1]. Quote orientation: plain index points.
- Registry: **71 outright quarterly contracts ESH0-2010 → ESZ7-2027**, keyed by
  vendor `instrument_id` (immune to decade-repeated symbols); 7,825,657 1m bars
  after filtering `^ES[HMUZ][0-9]$` [OBSERVED, `dossiers_v2/ES_DEEP_v2.md §1`;
  `ES_build_panel.py`, window 2010-06-06→2026-10-01].
- Calendar-spread instruments (dash symbols) and 2027 deferred stray-print
  tails (ESU7/ESZ7) are excluded from chains by the deterministic ≥100k-volume
  floor [OBSERVED, ES_DEEP_v2 §1; binding rule DATACONTRACT §1.6].
- Expiry law: 3rd Friday of delivery month, with the **Juneteenth shift** —
  ESM6 last traded **2026-06-18 (Thu)** observed in bars + vendor definitions;
  ESM7 **2027-06-17** from definitions (Jun-19-2027 Sat → observed Fri Jun-18
  → expiry Thu Jun-17); no other June displacement 2010-2025 [OBSERVED,
  ES_DEEP_v2 §1; `es_contracts.json`; encoded in SPEC_PB1_ES §1 with ERRATUM
  A7-SPEC-M2: June-2021 NOT shifted despite federal observance].
- Definitions cross-check 2023-10+: 0 mismatches (D5; `SUMMARY_QUAL_ACTIONS.md`
  row D5: instrument_id 1:1 vs definitions; absolute tick grid on outright
  0/478,951 off-grid) [OBSERVED].
- IBKR daily closes are settlement marks (D5: 96/96 tick-exact vs CME
  settlement), NEVER fill prices [OBSERVED, SUMMARY_QUAL_ACTIONS D5].

## 2. PIT inventory (what is point-in-time-evidenced vs NOT_RUN)

| source | PIT status | evidence |
|---|---|---|
| FOMC statements 2011-01→2026-09 | **PASS_EVIDENCED minute-level for 92/132 statements (2016-01-27+; 85 @14:00 ET + 7 irregular)** — "For release at" clock text in as-issued HTML; **day-level only for 40 statements 2011-2015** (artifact lacks times → minute anatomy NOT_RUN there) | FACT (federalreserve.gov archived HTML, `nonprice/fed/statements/`); counts OBSERVED `ES_fomc.py` / `ES_fomc_stats.json` (132/131-in-data/91-timed-with-1m) |
| CFTC CoT legacy "E-MINI S&P 500" | PASS_EVIDENCED: positions as-of Tuesday, released Friday 15:30 ET, as-published no-revision; forward windows start next session | FACT (cftc.gov schedule); 1,082 weekly rows 2006-01→2026-09-22, exact-name filter restored after 3-market contamination incident [OBSERVED, ES_DEEP_v2 §6] |
| FRED DFF | **NOT PIT** — latest-revised; sign-corroboration only | FACT (FRED); ES_DEEP_v2 §0/§4 disclosure |
| US CPI/NFP calendars | **NOT_RUN** — `bls_gate/` empty; FRED `released_at=null`; fabricating dates forbidden | OBSERVED (absence); NQ_DEEP_v2 §4 documents the program-wide gate; lane A5-EVENTS-BBO-COVERAGE is working this blocker (results NOT_RUN at write time) |
| PIT consensus/surprise archive | **NOT_RUN** — never acquired (H3 blocking item since v1) | ES_DEEP_v2 §8-H3 |
| Pit dividend yield (for roll-gap identity) | **NOT_RUN** — not in repo; 1.8pp proxy is a declared constant | ES_DEEP_v2 §4 [ERRATUM-era disclosure] |
| Vendor price/OI statistics feed | Statistics (stat_type 6/9) 2023-09-28→2026-09-28 with publication-lag disclosure (next-morning ~08:28-08:58 CT) | OBSERVED, ES_DEEP_v2 §4 [ERRATUM M-1] |
| BBO quotes/depth | **NOT_RUN** — never purchased; bbo-1m also insufficient for fill/queue proof (D5) | DATACONTRACT §1.7; PLAYBOOKS §4.8 |

## 3. Session by era / DST

- Era close-marks (recovered from the bars themselves, not assumed): Globex
  day close **16:30 CT through 2012 → 16:15 CT 2013→Nov-2015 → 16:00 CT since
  Nov-2015** [OBSERVED, ES_DEEP_v2 §3/§7; `ES_quality_ledger.json`
  `session_structure_history_OBSERVED`].
- Break-tail handling: pre-2016 16:00→16:15/16:30 tail volume (median
  2.1-2.3k contracts/session; 24,653 break bars total, confined to ≤2015)
  sits in the break bucket and is EXCLUDED from RTH/ON splits — disclosed,
  deterministic [OBSERVED, ES_DEEP_v2 §3; DATACONTRACT §1.2].
- DST proof: both US transitions (Sun 02:00 local) fall inside the weekend
  closure (Fri 16:00 → Sun 17:00 CT) — **no ES session is ever
  clock-distorted**; America/Chicago conversion exact 2010-2026 [OBSERVED,
  ES_DEEP_v2 §7 `dst_note`]. (Program-level 32/32 modal-hour proof measured on
  NQ — see NQ addendum §3.)
- Design consequence (binding on PB1): C_prev must use the era-correct actual
  prior-session close (16:30/16:15/16:00 CT), never a hard-coded 16:00;
  pre-2016 break-tails are separated, not merged [PLAYBOOKS_DRAFT §1 signal
  row; SPEC_PB1_ES §1].
- Session volume anatomy per era: RTH volume share stable **0.813-0.850**;
  ON variance share by year **20.9% (2018) … 53.8% (2020)** — verified from
  `ES_session_stats.json` `years[].var_on_pct` [OBSERVED].

## 4. Roll & calendar

- **Roll rule (frozen construction rule, not alpha): T-5 calendar** — switch
  at close of the 5th trading session before the expiry session, expiry =
  publicly-computable 3rd-Friday + Juneteenth shift (2026-06-18, 2027-06-17
  only; June-2021 NOT shifted — SPEC ERRATUM A7-SPEC-M2). Evidence: **66/66
  completed quarterly rolls**, T-5 deviation from measured volume crossover
  **0 to −2 sessions, never >3** (`abs_t5_dev_gt3_sessions: 0`; median 0,
  p10 −1) — v1-H1 invalidation never fired [OBSERVED,
  `analysis/ES_roll_stats.json` `t5_minus_crossover_sessions`; ES_DEEP_v2 §4].
- Volume crossover distribution: median 5 / mean 4.64 / min 3 / max 5
  sessions before expiry (n=66) [OBSERVED, `ES_roll_stats.json`].
- OI crossover (statistics era, 12 rolls): falls on the **SAME trading day**
  as volume crossover 12/12 under consistent session-date convention
  [OBSERVED, ERRATUM M-1 — pre-audit text "leads by 1 calendar day" was a
  timezone-labeling artifact]; OI-rule only legal 2023-10+.
- DECL (v1-declared) rule is dominated: holds a sub-liquidity book a median
  **9 sessions (range 6-11)** per quarter (n=65) [OBSERVED,
  `ES_roll_stats.json` `decl_thin_window_sessions`].
- Roll-gap structure: spread sign negative 2010-2016 (−1.5 to −1.8 %/yr ann.)
  and 2020-21, positive 2018-19 and strongly positive 2023-2026 (+3.3 to
  +4.7 %/yr); sign matches (DFF − 1.8pp proxy) on **61/66**; mismatches
  2017×1, 2018×2, 2019×1, 2022×1 [OBSERVED, ES_DEEP_v2 §4; ERRATUM m-1].
  Mechanism (futures ≈ spot + (rate − div)×T) remains POSTULATED — dividend
  yield PIT series NOT in repo.
- **CALENDAR AUTHORITY STATUS (current gaps per DATACONTRACT §1.2/§3; ES row
  of §2 matrix)**: holidays + early-closes **17/17 years 2010-2026
  authority-backed** (D3-CMECAL r6: 2026 LIVE_OFFICIAL trading-hours.html
  fetched 2026-10-03; 2010 ARCHIVED_OFFICIAL 38-page PDF; 2011-2025
  ARCHIVED_OFFICIAL verbatim tables; evidence
  `FUTURES-DATACONTRACT-QUAL-V1/analysis/d3_cmecalendar/ES_CALENDAR_EVIDENCE.md`).
  STILL OPEN: **expirations only 36/68 quarters ARCHIVED_OFFICIAL**
  (2012-2018 + 2025 + parts of 2010/2011/2024; **NOT_OBTAINED 2019-2023 +
  2026**); **ES-specific 2026 Globex early-close times NOT_OBTAINED** (behind
  page widget); 5 other CME symbols not yet extracted. Binding law: uncertain
  day ⇒ EXCLUDE/NOT_RUN, no inferred-pass (SPEC §2 E1-E3).
- **REQUIREMENTS lane A1-CMECAL-NQES is filling right now** (in-flight at this
  document's write time; results NOT_RUN here, do not assume PASS): (R1) ES
  quarterly expirations 2019-2023 + 2026 from official/archived-official
  sources to close the 36/68 gap (each recovered quarter converts
  authority-less rule-validation quarters into authority-checked ones; any
  mismatch ⇒ EXCLUDE whole quarter per SPEC §2-E2); (R2) ES-specific 2026
  Globex holiday/early-close TIMES (currently every dubious-2026 day is
  excluded fail-closed); (R3) NQ holidays/early-closes + expirations
  2010-2026 (currently NOT_RUN official — inferred only; gates the NQ
  sibling, see NQ addendum §4); (R4) all extracted with source URL + capture
  date + verbatim-vs-derived flag, ≤2 attempts/URL/method, no inference
  gap-fill [FACT — lane scope, `dispatch/DISPATCH_MANIFEST.json`
  lanes.A1-CMECAL-NQES].

## 5. Events

- FOMC inventory: **132 statements 2011-01-26→2026-09-16**; 92 carry
  machine-parsable release times (2016-01-27+; **85 @14:00 ET**, 7 irregular:
  2019-10-11 11:00, 2020-03-03 10:00, 2020-03-15 17:00 Sun, 2020-03-23 08:00,
  2020-03-31 08:30, 2020-08-27 09:10, 2025-08-22 10:00); 40 untimed
  2011-2015; 131 in-data; **91 timed sessions with 1m data** [FACT for times
  (as-issued HTML) + OBSERVED counts, `ES_fomc_stats.json` header fields].
- Release-anchored 15-min bucket ratios (medians, vs same-weekday non-FOMC
  baseline anchored 13:00 CT; verified from JSON): pre-release −120→−15 min
  **0.724-0.805 flat** (quieting); release bucket **2.906×** volume
  (|1m ret| **3.188×**); +15m 1.792×; +30m 2.653× (presser onset); +45m
  2.506×; +60m 2.054×; +90m 1.623×; dips 1.107× @+105 and 1.212× @+120;
  still 1.29-1.61× at +135→+165 (RTH tail 15:00-15:45 CT) [OBSERVED,
  `ES_fomc_stats.json` `minute_profile_15min_buckets.ratio_vol`/`ratio_absret`].
- Reaction timing: minute of max volume in [0,+30]: **median +1 min; 55% peak
  at minutes 0-1; 76% within 5** [OBSERVED, `reaction_timing`, n=91].
- Day-level (all 131 in-data): RTH volume ×1.14 median (p25-p75 1.01-1.31);
  RTH range ×1.38 vs baseline-day ×0.98; untimed 2011-2015 era ×1.23 vs
  ×1.12 for 2016-26 [OBSERVED, `ES_fomc_stats.json` `day_level`].
- **Minute-anchored anatomy NOT_RUN for 2011-2015** (no times in artifacts) —
  day-level only there [OBSERVED constraint, ES_DEEP_v2 §5].
- Non-FOMC macro: 07:30 CT slot visible in hour profiles (E7 07:00h = 3.0% of
  daily volume, |1m| 1.61bp — the most active pre-RTH hour) and in the 10
  extreme >2% 1m jumps (2022-09-13/10-13/11-10 all AT the 07:30 CPI minute)
  [OBSERVED, `ES_session_stats.json` hour_profiles E7; ES_DEEP_v2 §7].
  **CPI/NFP calendars NOT_RUN** (BLS gate empty) — see §2.
- LAW: no mean returns computed or compared anywhere above; volume/range
  timing only; nothing ranks or selects.

## 6. Coverage & data quality

- Window: **16.4 years** (2010-06-06→2026-10-01; 4,204 sessions; 4,203 return
  days on the VOL chain) [OBSERVED, `ES_regime_stats.json` `window`/
  `n_sessions`/`full_sample`].
- Integrity: 0 OHLC-consistency violations, 0 negative prices, 0 duplicate
  (instrument, minute) rows, 0 Saturday sessions; zero-volume bars ≈0% in all
  eras (Databento emits traded minutes only) [OBSERVED, `ES_build_panel.py` /
  ES_DEEP_v2 §1/§7].
- Coverage per era: ~97% (E1) → ~98% (E2-E3) → ~99% (E4-E5) → 100% (E6-E7) of
  era-correct session length; flat-OHLC 10.0% (E1) declining to low in
  modern eras; 1m gaps 0.9%→0.0%; |1m ret|>1%: 6/3/0/2/30/8/15 per era
  [OBSERVED, `ES_quality_ledger.json` `eras`].
- DST: never intersects an open ES session (§3); timestamp-precision caveat
  moot at 1m granularity (minute-stamped bars) [OBSERVED, ES_DEEP_v2 §7].
- ES-vs-IBKR overlap: 273 liquid days 2023-10→2026-10; vendor 16:00 CT close
  vs IBKR daily close median |diff| 15 ticks; 15:00 CT close 4 ticks —
  settlement-vs-last-trade convention gap, not an error; IBKR closes remain
  unusable as tradable marks [OBSERVED, `ES_quality_ledger.json`
  `ibkr_overlap_ES`].
- Early-close RTH sessions 3-10/yr 2010-2026 (from
  `early_close_rth_sessions_by_year`) — these feed the PB1 `prev_short`
  flag/SPEC §2-E1 machinery [OBSERVED].
- NQ 2020 alias episode: resolved program-side (recovered at $0; see NQ
  addendum §6); no ES analogue — ES panel had no hole.

## 7. Spread / cost (all MODELED COST — cost-as-measurement claims forbidden)

- Close-proxy spread: **full-spread median 1.0 tick = $12.50** (same-session
  BID/ASK close convention, reproduce exact r6) → **half-turn $6.25** used in
  the spec. This is a **high-biased proxy**, not BBO [OBSERVED-proxy,
  SUMMARY_QUAL_ACTIONS D5; SPEC_PB1_ES §5].
- MODELED COST per side (SPEC_PB1_ES §5, binding): commission IBKR Fixed
  **0.85** [FACT: IBKR public pricing page, LIVE_OFFICIAL fetch 2026-10-03 —
  conservative row of the public plan/tier table]; exchange CME **1.386**
  [FACT: IBKR CME.php offset table, LIVE_OFFICIAL; current-as-approximation
  for all historical years]; regulatory NFA **0.02** default, **0.01** for
  2014-10-01→2017-12-31 [FACT: official NFA timeline; single-source rule —
  IBKR 0.011 NOT added]; slippage tiers **S1/S2/S3 = $12.50/25.00/37.50**
  (1/2/3 ticks × $12.50) = **research assumption D1, not a measurement**;
  all-in per side **S1 21.006 · S2 33.506 · S3 46.006** (default NFA 0.02).
- **Account verification: NOT_RUN** (owner requested redacted statement;
  plan/tier of the actual account unknown; $2.247 all-in doc example carries
  label DOC_EXAMPLE_NOT_ACCOUNT_VERIFIED) [FACT(status), SUMMARY_QUAL_ACTIONS
  D2]. Historical per-year fee schedules: NOT_OBTAINABLE ⇒
  CURRENT_SCHEDULE_AS_APPROXIMATION with disclosure.
- BBO true spread: **NOT_RUN** (never purchased; D5 law: even bbo-1m cannot
  prove intrabar fill/queue) [DATACONTRACT §1.7].
- Stress law: ×1.0/×1.5/×2.0 on (spread + slippage-declared) is FORBIDDEN as
  double-stress; the {S1,S2,S3} tier triple is the only slippage sensitivity
  axis [PLAYBOOKS §4.4].
- Lane A4-FEES is currently fetching public schedules for NQ/FX/comm symbols
  (ES already done r6) — results NOT_RUN at this write time; nothing in this
  document depends on them.

## 8. Economic mechanism (POSTULATED — both directions registered together)

Both mechanisms are POSTULATED and mutually exclusive as dominant
explanations; the pair is registered simultaneously as falsification-by-
competitor (D-law). Each is CONSTRAINED by observed anatomy:

- **M-A Overnight information accumulation (→ CONT arm)**: Asian/European
  news and the 07:30 CT macro slot accumulate while the book is thin; RTH
  liquidity providers open their books slowly, so the OVN move continues into
  RTH. Constraining observations: OVN carries **21-54% of daily return
  variance by year** (2018 low 20.9%, 2020 high 53.8%) while holding only
  ~15-17% of volume — information share ≫ volume share [OBSERVED,
  `ES_session_stats.json` years]; the 07:30 CT macro slot is the most active
  pre-RTH hour in E7 (3.0% daily volume, |1m| 1.61bp) and produced three of
  the ten >2% 1m jumps exactly at CPI minutes [OBSERVED, §5]; Sunday reopen
  hour trades 1.5-2.9× weekday 17:00 volume [OBSERVED, ES_DEEP_v2 §3] —
  weekend information does discharge at the open.
- **M-B Thin-book over-extension (→ REV arm)**: the OVN tail is an
  over-extension by a thin crowd that RTH liquidity fades back. Constraining
  observations: daily lag-1 autocorr **negative in 5/7 data-quality eras**
  (E1 −0.109, E3 −0.065, E4 −0.038, E5 −0.243, E7 −0.089; positive only E2
  +0.014, E6 +0.003 — both ≈0) — NOTE: dossier §0.5 prose says "6/7" but its
  own §2 era table and `ES_regime_stats.json` give **5/7**; internal
  inconsistency disclosed here, JSON is the authority [OBSERVED + disclosed
  discrepancy]; VR(5d) < 1 in ALL eras (0.80-0.95) — multi-day momentum is
  not a descriptive feature of ES daily closes in any era [OBSERVED,
  ES_DEEP_v2 §2]; corr(ON,RTH) ranges +0.15→−0.10 by era, i.e. no stable
  positive coupling [OBSERVED, ES_DEEP_v2 §3].
- The two mechanisms cannot both survive the same data — that is the design's
  falsification engine. Which observations FAVOR NEITHER: FOMC release-minute
  volume 2.9×/|ret| 3.2× with pre-release suppression 0.72-0.81× shows event
  windows are a distinct information regime (hence base-EXCLUDE in PB1), not
  evidence for either arm [OBSERVED, §5].

## 9. Hypothesis + counter-hypothesis pair [PROVISIONAL] — PB1-ES field table

**This section REFERENCES SPEC_PB1_ES r3 (freeze-ready, A7-SPEC
FREEZE_READY_WITH_ERRATA applied) — it does NOT modify it.** The 24-identity
A-r4 scope STANDS. Any delta below is a [PROVISIONAL] recommendation for a
possible future owner amendment — explicitly NOT applied.

Test question: does a large overnight move (17:00 CT→08:30 CT open,
strict-past tail threshold) systematically continue or reverse inside RTH
after modeled costs? Arms **PB1-CONT** (direction sign(m)) and **PB1-REV**
(−sign(m)) registered simultaneously, both tails {UP, DN}; no post-hoc
tail/direction selection.

| field | specification [PROVISIONAL] | authority reference |
|---|---|---|
| Universe | **ES only** (E-mini S&P 500, mult 50, tick 0.25); held chain per contract §1.3 **T-5 rule + Juneteenth expiry law** (publicly computable, no lookahead; bars only VALIDATE) | SPEC_PB1_ES §1; DATACONTRACT §1.3 |
| Signal | m = log(open_0830 / C_prev); **C_prev = actual close of the immediately-prior session at its era-correct mark** (16:30 CT →2012; 16:15 CT 2013→2015-11; 16:00 CT since); prior-session short/holiday ⇒ C_prev = actual last print, current session flagged `prev_short` (era/Friday sensitivity view, not EXCLUDE); prior-session calendar uncertain ⇒ **EXCLUDE/NOT_RUN**; condition \|m\| ≥ q80(\|m\|, trailing-252d, strict-past) — q80 from anatomy, not tuned | SPEC §1/§3; PLAYBOOKS §1 |
| Entry | first 1m bar at 08:30 CT (D0) or 09:00 CT (D30) in arm direction; **fill = open of NEXT 1m bar** (conservative fill law D5; no limit/queue claims) | SPEC §4 |
| Delay pair | **{0, +30m} are TWO mandatory scored identities** (not reporting-only) — K4 consumes their pair directly | SPEC §4/§6; PLAYBOOKS §1 |
| Stand-aside | (i) FOMC statement days base-EXCLUDE at DAY level (all 132 statements incl. 40 untimed 2011-2015 — day-level dates are public); FOMCIN arm = INCLUDE sensitivity (4 identities); (ii) uncertain calendar days ⇒ EXCLUDE/NOT_RUN (E1-E5 machinery, D3 authority); (iii) RTH-core coverage (minutes 08:30-15:00 CT with a bar, era-correct close) < 60% ⇒ EXCLUDE; (iv) warmup 252 sessions | SPEC §3 [ERRATUM A7-SPEC-M3/M4] |
| Session | RTH close era-correct per §3 above; pre-2016 break-tails separated | SPEC §1; this addendum §3 |
| TP / SL | TP = 2.0 × SL-distance; SL = 1.0 × median of prior-20 RTH session ranges (strict past, era-correct close marks, short/flagged sessions excluded) — frozen a priori, R=2 | SPEC §4 [ERRATUM A7-SPEC-M5] |
| Same-bar TP/SL | one 1m bar touching both ⇒ **SL priority** (worse price), deterministic, no OHLC-order favoritism | SPEC §4; PLAYBOOKS §1 |
| Time exit | era-correct RTH close, mandatory flat — daytrade; no roll-carry exposure | SPEC §4 |
| Roll | §1.3 T-5; position flat before roll-session close; roll only affects the reference chain; quarter mismarking rule ⇒ EXCLUDE WHOLE QUARTER | SPEC §1/§2-E2 |
| Sizing | 1-2 contracts (margin ~$29k/ct public, 2 sources <2% apart; 4× coverage ⇒ ≤2 @100k); risk 0.5%/trade [freeze at GO] | SPEC §4; DATACONTRACT §1.7 |
| Cost | MODELED COST per §7 above: all-in/side S1 21.006 · S2 33.506 · S3 46.006 (NFA 0.01 window −0.01); describing these costs as measured/verified figures is FORBIDDEN | SPEC §5 |
| Identities | **A-r4 exactly 24**: P-A {CONT,REV}×{UP,DN}×{D0,D30}×S2 = 8; P-B {CONT,REV}×{UP,DN}×D0×{S1,S3} = 8; FOMCIN {CONT,REV}×{UP,DN}×D0×S2 = 4; C1 placebo (seed 20261002, D0/S2) + C2 always-in-RTH + C3 flat anchor + C4 dose-response = 4. Full design D1=52/D2=53 remain BLOCKED_TRIAL_BUDGET | SPEC §6 |
| Folds/gates | 4 sequential folds F1 2010-06..2012-12 / F2 2013..2017-12 / F3 2018..2021-12 / F4 2022..2026-09; G1-G9 stage-A gates; S1 SEALED_UNTOUCHED | SPEC §7-§8 |
| Terminal | pre-declared outcomes incl. `FUTURES_ES_V1_REJECT_ALL` | SPEC §9 |

**Evidence-driven deltas observed by this addendum (ALL [PROVISIONAL],
NOT applied — SPEC_PB1_ES stays r3 untouched; any change requires an owner
amendment + ceiling re-check):**
1. *(observation only)* The 5/7-vs-6/7 acf1 discrepancy (§8 above) does not
   touch any spec parameter; if a future amendment cites "acf1 negative 6/7
   eras" as mechanism support, it must cite 5/7 per
   `ES_regime_stats.json` instead. [OBSERVED discrepancy; no action]
2. *(recommendation candidate)* None required for calendar: SPEC §2 already
   fail-closes every D3 gap; when lane A1-CMECAL-NQES lands, the only legal
   integration path is regenerating the deterministic exclude-list at freeze
   (SPEC §2), not editing this addendum or the SPEC. [POSTULATED process]

## 10. Ancestry & placebo

**Ancestry verdict (honest search of `research/wayfinder/{MAP,
HYPOTHESIS_LEDGER,SURVIVORS}.md` + control/ directory):**
- **No prior scored ancestor for equity-index futures exists in this
  program** — searches for e-mini/emini/equity-index/S&P-500-futures families
  across the wayfinder registry return zero scored families; the futures
  program to date is FX-futures (DTP-FX-MECHCOURT-V1, fx_futures_frontier)
  and this 10-symbol prep. Status: **NOT_RUN/none-locatable** — PB1-ES is a
  first-generation family on this substrate, so no in-family kin-claim can be
  made against it (which cuts both ways: no dead ancestor vetoes it, and no
  live ancestor supports it).
- Nearest dead families (cross-asset, must NOT be transplanted without
  evidence — different microstructure, different session architecture, FX
  has no cash-equity open):
  - **FOREX-FREE-V1 `FXFV1-A3-P1` London-open session continuation** — REJECT:
    anchor expectancy −2.35/trade, PF 0.849, all 3 folds negative, 11,459
    trades, 7 pairs [OBSERVED registry, HYPOTHESIS_LEDGER row Free-V1]. This
    is the closest MECHANISM cousin of M-A (session-open continuation).
  - **FOREX-FREE-V2 `FXFV2-A4-P1` Tokyo-range compression → London expansion
    and `FXFV2-A4-P2` London-AM range break + retest** — REJECT: all arms
    EXPECTANCY_NONPOSITIVE (−3.804/−3.093 per trade); P2's placebo
    reproduced the behavior (mechanism not specific) [OBSERVED registry].
  - Cumulative-evidence line: "Session/open FX momentum/fade on free G10
    data: rejected at high trade counts (cost-dominated)"
    [HYPOTHESIS_LEDGER §F]. DAYTRADER-100-V1: FX session books cost-marginal,
    die at ×2.0 stress [OBSERVED registry row].
  - **Discriminating claim for PB1-ES vs these corpses**: FX-spot deaths were
    cost-dominated at high trade counts on ~free data with no variance-share
    asymmetry of the OVN kind; ES has (a) a measured OVN information-share
    ≫ volume-share asymmetry (21-54% variance at 15-17% volume), (b) 1-tick
    close-proxy spread at $12.50 vs $50 multiplier, (c) a cash-open
    microstructure at 08:30 CT that FX lacks. These are POSTULATED
    distinctions — the ancestry court has NOT adjudicated them (that is
    B2-DEEP-6E6B's mandate for PB2; PB1-ES proceeds as first-generation).
- Placebo/controls C1-C4 (per SPEC §6 / PLAYBOOKS §1): **C1** clock/random-sign
  seeded placebo (seed 20261002, D0/S2, own PnL path, scored identity);
  **C2** always-in-RTH baseline (D0/S2, scored); **C3** flat anchor (0 trades,
  ledger only); **C4** OVN-direction-unconditional dose-response (sign(m)
  every day, D0/S2, scored — replaces the ±21d trading convention; C5
  ±21d non-event stats remain non-PnL descriptive).
- **POWER discussion [POSTULATED]**: expected session n after warmup/wedges ≈
  4,204 − 252 (warmup) − ~131 FOMC day-excludes − EXCLUDE-list (calendar-
  uncertain days, low-coverage; order tens/yr in pre-authority years) ≈
  **~3,700-3,800 eligible sessions**, of which the q80 tail gives ~20%
  ≈ **740-760 armed sessions per tail-pooled arm** (~370-380 per
  tail×arm cell at D0; halved again per delay cell family). With C1 placebo
  single draw and C2 baseline as the reference, the design distinguishes
  effects of order **≥ the placebo spread** — a single-seed placebo anchors
  only the sign/random-assignment null, NOT the permutation distribution:
  **A-r4's single-seed C1 (20261002, single delay) is a published
  limitation — no permutation-robustness claim is legal** (PLAYBOOKS r5
  arithmetic: full designs D1=52/D2=53 both BLOCKED_TRIAL_BUDGET vs the
  24 ceiling). Thin-power warnings: (i) per-cell n at D0×tail×arm ~370
  gives ±~1 σ ≈ 5-6 bp/session on after-cost expectancy at ES vol ~17%
  ann (~107 bp/day σ) — only effects ≳0.05σ/day/trade are distinguishable
  from noise at 1σ; (ii) K3's 2020-03..04 window is ~40 sessions — a
  single-month regime can dominate a cell (that is why K3 exists); (iii)
  G3's 2/4-folds-positive gate has weak power at per-fold n ~900-1,000
  armed-pooled.

## 11. Refutation tests (mechanism-level falsifiers)

Pre-registered K-series (SPEC §8 / PLAYBOOKS kill rules; each names its
observable + the artifact that would contain the evidence):

- **K1 era sign-stability**: split by the three OVN-share eras
  2010-16 / 2017-21 / 2022-26 (evaluation VIEWS on existing PnL paths —
  SPEC §7; zero new identities). Kill: per-era sign/expectancy of the
  surviving arm unstable across the three ⇒ participation artifact, kill the
  whole family. Observable: per-era expectancy table in the cycle's
  evaluation report; constraining anatomy = ES `var_on_pct` by year
  (2010-16 ≈ 30-46%, 2017-21 spans 20.9→53.8%, 2022-26 ≈ 29-45%)
  [OBSERVED basis; kill logic pre-registered].
- **K2 both-arms-below-floor**: CONT and REV both below Stage-A floor at
  S1 (1-tick) tier ⇒ family dead; re-tparameterization FORBIDDEN
  [pre-registered; observable: stage-A gate table at S1].
- **K3 drop-window**: ≥80% of contribution from 2020-03..04 ⇒ drop-window
  sensitivity fail [pre-registered; observable: contribution decomposition
  by calendar month on existing paths].
- **K4 delay sign-flip**: sign of after-cost expectancy flips between D0 and
  D30 (same arm/tail/tier) ⇒ open-microstructure artifact — adjudicated
  DIRECTLY on the two scored delay identities, neither may be dropped
  [pre-registered; observable: the P-A pair's two cells].
- **K5 NQ-vs-ES divergence**: when NQ enters (post cost gate), NQ sign
  opposite to ES ⇒ symbol-specific downgrade, no family claim
  [pre-registered; observable: cross-symbol comparison in the NQ sibling
  cycle's report].
- **NEW-1 OVN-variance-share participation artifact [POSTULATED]**: if the
  surviving arm's effect exists ONLY in high-OVN-share regimes (e.g.
  2020-21 crisis where ON share 50.7-53.8%), the "information accumulation"
  mechanism is really a crisis-participation proxy. Observable/prediction:
  conditioning the primary cells on trailing-year var_on_pct median-split
  (strict-past) should show the effect in BOTH halves if M-A/M-B is a
  structural session mechanism, only the top half if it is participation.
  Falsification: effect confined to the top OVN-share half ⇒ reclassify as
  vol-regime effect, require vol-tercile registration (new cycle, new
  budget) — NOT a rescue. Evidence container: era/views tables on existing
  paths + `ES_session_stats.json` years (no new identities needed for the
  descriptive split; a scored vol-conditioned variant would be a new
  registration).
- **NEW-2 FOMC-exclusion information-source test [POSTULATED]**: the base
  EXCLUDE removes 132 day-level statement days. If M-A (information
  accumulation) is the true mechanism, the FOMCIN sensitivity arm should
  show LARGER armed-day effects on OVN tails that include scheduled
  macro-morning adjacency (07:30 CT slot), while M-B (over-extension) should
  be insensitive to information source. Observable: FOMCIN 4 identities vs
  base arm contrast, plus the 07:30-slot day subset (calendar NOT_RUN until
  A5 lands — descriptive split only after PIT calendars exist).
  Falsification: effect flips sign or vanishes on FOMCIN ⇒ the base arm was
  harvesting event-avoidance, not session structure — downgrade and record.
- **NEW-3 volume-conditioned split (dose-response gradient) [POSTULATED]**:
  C4 (unconditional sign(m)) provides the dose-response control; mechanism
  M-A predicts monotone conditioning value in |m| (bigger tail ⇒ bigger
  continuation), M-B predicts the opposite gradient. Observable: C4 vs
  primary q80 cells' expectancy gap. Falsification: C4 ≥ primary ⇒ the q80
  threshold carries no conditioning information (G7 already encodes this vs
  C2/C1; C4 extends it to dose) — "no conditioning information" verdict.
  Evidence container: identity table + G7 gate results.

## 12. Limitations & open questions

1. All §8-§11 mechanism/power statements are POSTULATED or arithmetic
   projections from descriptives — nothing here is evidence of edge; the
   conditional-return question remains NOT_RUN until a registered cycle.
2. Calendar authority partial: expirations 2019-2023+2026 and ES-2026
   Globex times await lane A1; every uncertain day excludes fail-closed
   (reduces armed n, biases sample toward authority-covered years —
   disclosed, accepted by law).
3. Cost authority: MODELED COST only; account verification NOT_RUN;
   historical per-year fee schedules NOT_OBTAINABLE (current-as-
   approximation); slippage {1,2,3} ticks is assumption D1; BBO NOT_RUN.
4. FOMC minute anatomy absent 2011-2015 (day-level only); CPI/NFP calendars
   NOT_RUN pending A5; PIT consensus archive NOT_RUN (blocks any surprise-
   conditioned design).
5. Single-seed placebo limitation stands (A-r4, 24-identity ceiling);
   permutation robustness unclaimable.
6. CoT contamination incident (fixed, filtered) and the nonprice-root
   emptiness incident I-1 are owner-ledger items; this addendum inherits the
   corrected artifacts only.
7. Dossier §0.5 "acf1 negative 6/7 eras" vs JSON/§2-table 5/7 — recorded
   here as a disclosed internal inconsistency; errata authority belongs to
   the DOSSIER-ERRATA lane, not this addendum.
8. Dividend-yield PIT series absent ⇒ roll-gap sign identity stays
   POSTULATED on the rates side only (61/66 sign match).
9. Open questions for the owner: (a) GO/no-GO for FUTURES-ES-V1 after A1
   lands + exclude-list regeneration; (b) whether NEW-1/NEW-2 descriptive
   splits should be added as evaluation views (0 new identities) at
   registration; (c) NQ cost-gate decision ordering (A4-FEES first).

— End of ES_DEEPFOUR_V3_ADDENDUM. No PnL computed, no selection performed,
no PASS claimed without evidence; SPEC_PB1_ES r3 untouched.
