# HYPOTHESES_FXJA_R3 — round-3 outcome-blind hypothesis search, 6J (JPY) + 6A (AUD) CME FX futures (lane FXJA)

- Task: **FUTURES-TEN-HYPO-PREP-20261004**, lane **FXJA**. Generated 2026-10-04
  UTC. Worktree `/Users/hoangminhlong/my-quantitative/.worktrees/futures-ten-hypo/prep`
  @ HEAD **`a4a882658e09092b5b282b666b30a3cfc5ac3418`** (measured via the one
  permitted `git rev-parse HEAD` at lane start; == dispatch base_sha), branch
  `prep/futures-ten-hypo-20261004`. Companion artifacts: `CARRIED_STATUS.md`,
  `hypotheses_fxja_r3.json`, `fetch_log.jsonl`, `captures/` + `SHA256SUMS_lane.txt`,
  `dispatch/handoff_FXJA.json`.
- Class: PREP hypothesis dossier. **0 PnL, 0 returns, 0 scored runs, 0 sweeps,
  0 selection by any return statistic. Outcome-blind. No conditional-on-signal
  measurement of any kind was performed or is proposed as done. Missing
  evidence is NOT_RUN, never PASS.** Every parameter **[PROVISIONAL]**.
  **No cycle registration, no trial creation. NO_GO_REGISTER / NO_GO_SCORE /
  NO_GO_ORDER stand.**
- Standing rulings restated, never reopened: **PB3 PARK (6A)** — 0 budget,
  contingency bookkeeping only; **6J no cap defined** (owner ceiling required
  before any 6J registration); 6A tick era law ($10.00/tick ≤2020-11-20 /
  $5.00/tick ≥2020-11-23; era-1 = 231 sessions descriptive-only); 6J
  orientation PROVEN (USD-per-JPY, up = yen strong); 6J volume 0.455× law
  (shares/ratios only); **BoJ intraday decision stamps NOT_IN_CORPUS** (owner
  decision pending); ABS/China calendars NOT_RUN (AF3 K4 alive); cease-guard
  exemplars 6J 2022-09-20 / 6A 2024-12-17 + 2026-06-16 (descriptive-only
  stratum n=3); fees MODELED / VERIFIED_VS_ACCOUNT=NOT_RUN / UNDER REVIEW
  (D2); BBO NOT_RUN (D5); D1-D12 all open; **DC §1.3: construction ≠ alpha**.
- Taxonomy: **FACT** (primary source + date) / **OBSERVED** (script + window
  on committed artifacts, cited `file:field`) / **MECHANISM_HYPOTHESIS** /
  **INFERENCE** / **DERIVED** / **NOT_RUN** / **NOT_OBTAINED** /
  **NOT_IN_CORPUS**. Forbidden words: "measured cost", "complete cost",
  "edge" claims of any kind.

---

## 0. Evidence base consumed before writing (read-only; in-worktree unless noted)

1. `research/control/FUTURES-OVERNIGHT-PREP-20261003/hypo/6j_6a/JPY_AUD_HYPOTHESES.md`
   (711 lines, in full — JF1-3 / AF1-3 11-field specs, PB3 park law, K0
   thin-n kill, shared cost table, NOT_RUN register) + `hypo/6j_6a/
   RANKING_INPUT.md` (3-axis scores + trial census).
2. `research/control/FUTURES-OVERNIGHT-PREP-20261003/hypo/cross/RANKING_FRAMEWORK.md`
   (the 5-dim D1-D5 0-3 program rubric, aggregation + tie-break law, worked
   example, §3 consolidated ranking, §4 diagnostics class) — the anchor set
   for this lane's §6.
3. `research/control/FUTURES-SIX-ADOPT-PREP-20261004/hypo/HYPOTHESES_R2.md`
   (format exemplar; R2-F1 RMM, R2-F2 AF4, W1/W2/W3 wall taxonomy, ancestry
   table, 5-dim scores) + `packet/CYCLE_LAUNCH_DRAFT.md` §1-§3, §8 (chains of
   record, PIT laws, cost contract incl. D8 era law, budget surfaces, D1-D12).
4. `research/control/FUTURES-SIX-READINESS-20261004/fx_ja/`:
   `DATA_READINESS_6J.md`, `DATA_READINESS_6A.md`, `6a_roll_measured.json`
   (27 rolls; triggers 21 cease-guard / 6 crossover; variant delta
   2024-12-17 + 2026-06-16), `6a_tick_adjudication.json` (era grids),
   `6j_identity.json` (tick 5e-7 unique; GCD 500 int-nano all eras),
   `6j_orientation_recheck.json`, `6j_cease_guard_2022.json`,
   `ja_event_pit.json` (BoJ 156 statements dates-only / RBA 395 decisions
   dates-only / MOF 386 ops / DFF vintages), `session_holes_2023.json`,
   `fx_ja_readiness.json`. Cited as fields; nothing recomputed.
5. `research/wayfinder/FAMILY_FAILURES.jsonl` — **all 173 rows scanned this
   lane** (crypto 78 / forex 41 / stocks 36 / vol 6 / sprint 6 / rates 3 /
   commodities 3), classes SCIENTIFIC_REJECTION, SELECTION_REJECTION,
   ANCESTRY_RHO_BLOCK, VARIANT_SAME_FAMILY, COST_VETO_PRE_PNL,
   DATA_BLOCK, HOLDOUT_FAILURE, SCORED_REJECTION, NOVELTY_VETO_PRE_PNL,
   INCREMENTAL_ALPHA_NEGATIVE, NOT_RUN_THIN_AGGREGATE.
6. `research/control/FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/deep/6e_6b/
   PB2_ANCESTRY_COURT_DRAFT.md` (court method: §a dead-corpus facts incl.
   "no central-bank event conditioning capability" + forced-flat/no-calendar
   law; §b three-part veto test; §c placebo/POWER method; transplant warning)
   and `deep/es_nq/NQ_DEEPFOUR_V3_ADDENDUM.md` §10 (program-level warning as
   cited in R2).
7. Root checkout READ-ONLY: `research/control/FUTURES-DATA-10SYMS-V1/
   FINAL_REPORT.md` ("root main d8cf8eca"; 6J spread 25 / 6A 20; quote
   scales verified; roll rule declared PIT-legal).
8. New primary-source captures made by this lane (2 of 5 fetch attempts, both
   200; log `fetch_log.jsonl`): **RBA Monetary Policy Minutes page**
   (rba.gov.au/monetary-policy/rba-board-minutes/, sha256 e52e10ea…) — text:
   minutes published **two weeks after each meeting**; meetings held **eight
   times each year**; no intraday release stamp on page. **MOF JGB auction
   hub page** (mof.go.jp/english/policy/jgbs/auction/index.html, sha256
   28cae2fc…) — documents the auction calendar/results as public; no
   intraday stamp on page. Three 404s (wrong paths) logged, bodies deleted.

---

## 1. Search result and closure — the honest headline

**0 NEW hypothesis families are proposed.** The search generated and
adjudicated **16 candidates** across every design space the dispatch named
plus this lane's own probes; every one died against a wall that is already
committed law, committed dead evidence, or a committed NOT_RUN. Quality over
quantity is not a stylistic preference here — it is the outcome: the
occupied inventory (JF1-JF3, AF1-AF3, AF4, RMM) already covers the
session-structure, scheduled-uncertainty, official-flow-regime, roll-
migration and microstructure-era classes on these two symbols, and the dead
corpus covers the calendar-flow, release-window, fix-window, open-window and
yield-exposure classes across assets **including the same pairs**.

The four recurring walls (following R2's W1-W3 taxonomy, extended):

- **W1 — Ancestry veto (dead-class rename).** The dead corpus is not merely
  FX-spot London sessions: it contains calendar-anchored flow classes
  (month-end fix drift, turn-of-month, post-options-expiry, pre-release
  avoidance with a SHAM-CALENDAR control that OUT-EARNED its anchor), a
  day-of-week geometry kill, release-order/reaction-direction families, a
  holdout-failed open class, and yield-exposure controls that out-earned
  their anchors. Any calendar-seasonality, release-window, fix-window or
  expiry-window family on 6J/6A is a symbol/era tweak of a rejected class —
  court §b fails because the mechanism (scheduled-flow reaction in the
  quoted hours) is fully representable on spot, and the dead corpus already
  ran it on USDJPY and AUDUSD.
- **W2 — Occupancy (window-space / family-space duplication).** 6J/6A
  session and event space is already partitioned by carried families:
  Tokyo-morning (JF3), BoJ decision window (JF1), MOF regime (JF2), RBA
  minute (AF1), bimodal session skeleton (AF3), differential regime (AF2),
  tick-era conditioning (AF4), roll migration (RMM). A candidate whose
  anchor lands inside one of these windows or whose day-set is a subset of
  one of these day-sets is a re-parameterization, not a family.
- **W3 — Standing law (out-of-law classes).** Roll/curve/carry =
  construction (DC §1.3); MOF same-day signals = PIT lag-law violation;
  cross-venue comovement = out of scope (P1-CROSS owns); 6A anything = PB3
  PARK surface anyway.
- **W4 — Data absence (NOT_RUN, never designed around).** ABS historical
  release dates NOT_RUN; China calendars NOT_RUN; BoJ operation/statement
  intraday stamps NOT_IN_CORPUS; FX holiday session times 2024-25
  NOT_OBTAINED; BBO NOT_RUN. None may be assumed away.

The valuable deliverable this round is therefore the **veto record itself**
(§3: every candidate with its specific wall and its cited dead rows) plus the
**provisional 5-dim program scores for the carried families** (§6 — the
RANKING_FRAMEWORK explicitly lists the 6J6A rows as PENDING for the synthesis
lane). **An honest "zero NEW" is the declared result.**

---

## 2. Candidate adjudications (16; each: proposed mechanism → nearest dead
entries / occupied space → the specific wall → verdict)

Field 1-11 format is reserved for NEW families; none survived, so each
candidate carries the load-bearing subset (mechanism, PIT posture, bindings
conflicts, ancestry, wall) instead. All candidates are recorded whether they
died on one wall or four.

### C-01 `FYJ-SEAS` — Japan fiscal year-end (March) / September half-year importer-exporter hedging seasonality (6J)
- Proposed mechanism [MECHANISM_HYPOTHESIS, rejected]: scheduled Japanese
  corporate hedging around fiscal year-end (Mar) and half-year (Sep) creates
  persistent USD/JPY flow pressure visible as drift in the days around the
  turn.
- PIT posture: NO scheduled anchor exists — no primary source (MOF, BoJ, any
  ministry) publishes a hedging calendar; the flow is diffuse OTC
  spot/forward dealing through banks. A family without a scheduled anchor
  degenerates to a day-of-month/quarter-turn calendar effect.
- Ancestry (specific dead rows): **DTPFX1-A1-MEFIX-VARIANT** (forex,
  SELECTION_REJECTION / VARIANT_SAME_FAMILY — "Owner-named month-end London
  WMR fix rebalancing drift (enter the final pre-fix window on month-end
  days…)": the month-end calendar-flow drift family is already dead AS A
  CLASS); **FXFV5-A6-P1-pre-release-avoidance** (forex, SCIENTIFIC_REJECTION
  / CONTROL_OUTEARNED_ANCHOR — the +7-day SHAM-CALENDAR neighbour out-earned
  the anchor: the calendar itself carried nothing); **FXNG4-A4-P1/P2/A5-P1/P2**
  (forex, SELECTION_REJECTION / ANCESTRY_RHO_BLOCK vs `generic_dow_tue` —
  33/37 event-days on one weekday: calendar stacks collapse to day-of-week
  geometry); **SFV3-A6-TOM-SETTLE** (stocks, PF_BELOW_THRESHOLD — turn-of-
  month); **CNG1-A5-P2** (crypto, ANCESTRY_RHO_BLOCK — monthly
  post-options-expiry unwind). Five assets, one class, all dead.
- Walls: W1 (five cited classes across assets); W4 (no scheduled-flow
  primary source exists — "needs primary source on scheduled visible flow"
  resolves to NOT_OBTAINABLE, not un-fetched); mechanism locus = spot
  fixing/importer dealing (court §b: representable in the dead corpus, which
  traded USDJPY); window occupancy (Mar/Sep turns are ordinary sessions
  inside JF3's host + JF1/JF2 exclusions).
- **Verdict: VETO — ancestry (calendar-flow class dead ×5) + no PIT schedule
  + spot-representable mechanism + occupied window space.**

### C-02 `AF1-MIN` — RBA minutes-vs-decision differentiation (6A)
- Proposed mechanism: minutes (T+2 weeks, 8/year) carry board-debate detail
  that re-prices the path at a known Sydney hour.
- PIT posture: cadence now FACT-pinned by this lane's capture
  (`rba_board_minutes.html`: "two weeks after each meeting… eight times each
  year"); dates derivable from decision dates; **release time-of-day NOT
  evidenced on the page** — a minute-anchored window would lean on an
  unverified convention (the same defect class as AF1's own 14:30 anchor,
  but with zero measured anatomy of its own).
- Occupancy: same venue, same anchor hour convention, same mechanism class
  (scheduled RBA communication resolution) as **AF1**; weaker payload —
  AF1's measured intensity gradient is change-vs-hold (59 vs 29 ticks), and
  minutes have no change/hold split by construction.
- n honesty: minutes days in the 2020-2026 panel ≈ the meeting count
  (≈63-67; 2024+ = 8/year per the capture and `ja_event_pit.json:rba`
  decisions_by_year) — inherits AF1's pre-registered **K0 thin-n kill**.
- Walls: W2 (AF1 re-parameterization; the occupancy rule says do not
  duplicate); W4 (no primary minute-stamp); W3 (PB3 PARK surface); K0.
- **Verdict: DUPLICATE-VETO — AF1 space; sub-K0 n; no stamp.**

### C-03 `JGB-AUCT` — MOF JGB auction-date flow (6J)
- Proposed mechanism: auction results (public calendar, PIT-legal —
  capture `mof_jgb_auction_en.html` documents the calendar/results as
  public) create dealer funding/JPY-demand flow at auction times.
- PIT posture: schedule published in advance — capturable; **result
  release time-of-day not stated on the captured page** (declared
  convention would be required, as for JF1).
- Walls: W2 (results land 09:45 JST-convention inside **JF3's** occupied
  Tokyo-morning host; as a day-set it would reproduce AF3's K4
  contamination kill in reverse; the event CLASS — scheduled Japan-side
  official announcement — is JF1's); mechanism is second-order to JPY
  (first-order effect is JGB yields — a different instrument) and no
  primary source documents a JPY-visible scheduled flow at auction times;
  no 6J anatomy measured at auction minutes anywhere in the committed
  corpus; dead-class adjacency: scheduled-announcement reaction classes are
  dead (FXNG1-A5-P1 EXPECTANCY_NONPOSITIVE release-order; FXFV6-A4-P1
  own-economy reaction-direction PF razor-fail; FXFV3-A6-P1 STRESS_TIER_FAIL
  at 47/159 evidencing).
- Honesty note: this is the strongest of the capturable-data candidates —
  it dies on mechanism/occupancy/anatomy, NOT on transport.
- **Verdict: VETO — occupied window + second-order undocumented mechanism +
  no anatomy + dead release-window class.**

### C-04 `BOJ-RMPG` — BoJ Outlook Report / RMPG dates as a distinct event set (6J)
- The Outlook Report publishes on day-2 of scheduled MPMs (Jan/Apr/Jul/Oct)
  — **a subset of JF1's 54-day set**; off-cycle interim assessments are rare
  and, if ever acquired, would extend JF1's day-set under its existing
  window convention and K3 anchor-robustness law — an extension of a
  carried family, not a family. The dispatch's own prior ("likely JF1
  territory") is confirmed.
- Walls: W2 (subset of JF1's day-set; same class).
- **Verdict: NOT_NEW — SUBSUMED by JF1 (day-set subset).**

### C-05 `AU-REL` — ABS employment/CPI release windows (6A)
- Proposed mechanism: AU own-economy release resolution at 11:30 Sydney.
- Walls: W4 first — **ABS historical release dates NOT_RUN** (owner
  acquisition decision; DATA_READINESS_6A Dim 5): the day-set is
  unbuildable, so the family is DATA-BLOCKED regardless of merit. W1: the
  class is dead in spot (FXNG1 / FXFV6 / FXFV5) and occupied on FX futures
  by FX-F3 (6E/6B US-8:30 legs). W2: the 11:30 Sydney slot is **AF3's
  measured modal peak** (2.35% of daily volume in that half-hour) —
  ABS-day splits are AF3's own declared NOT_RUN extension, not a new
  family. Timezone PIT honesty: the 11:30 landing time is verified only on
  the CURRENT ABS page (6A_DEEP §4.3); historical release-time schedules
  (incl. any AU analogue of the BLS 2025-vintage revisions, BLSV §1-§3)
  are NOT evidenced.
- **Verdict: DATA-BLOCKED + DUPLICATE (FX-F3 class / AF3 window space).**

### C-06 `CN-REL` — China data windows (6A)
- Walls: W4 — China Caixin/NBS calendars NOT_RUN (standing). W2 — the
  09:30-10:00 Shanghai window is **AF3's** observed structure (highest mean
  1m range 2.36 ticks) whose own kill law (K4) says a trigger cluster there
  IS the missing-calendar family; building it requires the calendar that is
  NOT_RUN. Any capturable-primary route is an owner acquisition decision,
  not a lane action.
- **Verdict: DATA-BLOCKED (AF3 K4 alive; occupied window).**

### C-07 `FOMC-6JA` — FOMC decision-window legs on 6J/6A
- Measured fact: on 6A the FOMC ±5' common factor is LARGER than RBA's
  (8.2× volume / 6.2× |ret| vs RBA 9.0×/4.8× — comparable volume, larger
  ret) [OBSERVED, `6A_a4_events.json:fomc`; AF1 field 3]. Tempting — and
  already occupied: ES-F1/NQ-F1 own the FOMC-resolution class (registered
  parent); FX-F2 owns policy-decision legs on FX futures (6E/6B); AF1/AF3
  carry FOMC as measured-and-EXCLUDED common factor (C3″/K1). New symbol
  legs = extension of occupied classes, and the exclusion structure of the
  carried 6J/6A families already encodes the effect as a control.
- Walls: W2 (occupied class ×2 + measured-and-excluded inside AF1); the
  measured common-factor anatomy is the C3″ control's evidence, not a
  family.
- **Verdict: NOT_NEW — occupied class (ES-F1 parent / FX-F2 FX-legs); the
  effect lives in carried families as exclusions.**

### C-08 `JP-0850` — Japan 08:50 JST own-economy release windows (6J: GDP/labor/trade/CPI)
- Proposed mechanism: own-economy scheduled release spillover in the home
  morning; trade balance is a named flow channel.
- Walls: W2 — 08:50 JST sits inside **JF3's** Tokyo-morning host (window
  occupied); the class is FX-F3's (own-economy release spillover on FX
  futures, occupied 6E/6B). W1 — release-window classes dead in spot
  (FXNG1 opening-follower release-order EXPECTANCY_NONPOSITIVE; FXFV6 CPI
  reaction-direction PF 1.0979 razor-fail; FXFV5 pre-release avoidance
  CONTROL_OUTEARNED_ANCHOR); the trade-balance flow channel is
  spot-representable (court §b fails). W4 — no 6J anatomy committed at
  08:50 (JF3's aggregates are adjacent-window evidence only); Japan release
  calendar NOT_IN_CORPUS.
- **Verdict: VETO — window occupied + class occupied + dead release-window
  corpus + no anatomy.**

### C-09 `GAP-6JA` — weekend/reopen-gap legs on 6J/6A
- FX-F4 Reopen-Gap owns the class (6E/6B legs; 6B gap anatomy itself
  NOT_RUN/declared gate). A 6J/6A leg is a symbol-leg extension of a
  carried family; the adjacent dead open-class (FXOS-04 holdout failure;
  FXFV1-A3 London-open) plus the program-level "session/open — must NOT be
  transplanted without evidence" warning caps any independent variant.
- Walls: W2 (FX-F4 class). **Verdict: NOT_NEW — FX-F4 symbol-leg extension;
  anatomy gates NOT_RUN.**

### C-10 `TOKYO-FIX` — Tokyo fixing (9:55/10:00 JST) window on 6J
- Fix-participant/fix-window classes dead twice: **DTPFX1-A1-MEFIX-VARIANT**
  (VARIANT_SAME_FAMILY — month-end WMR-fix skeleton strip leaves the dead
  decision law intact) and **TRACKA2-P4A-FIXCERT-01** (SELECTION_REJECTION /
  DECLARED_BAND_BELOW_MEASURED_COST — fix-participant payer died on the
  cost band alone). Mechanism = spot-fixing rebalancing flow
  (spot-representable, court §b fails); 09:55 JST is inside JF3's window
  (W2); BBO NOT_RUN keeps any fill story conservative-law only.
- **Verdict: VETO — ancestry ×2 + spot-representable + occupied window.**

### C-11 `MOF-INTRA` — intraday intervention detection / op-hour window (6J)
- OUT-OF-LAW by construction: MOF lag law — op amounts publish ~1 month
  (monthly) / quarterly (daily detail) after the fact; same-day signals are
  FORBIDDEN (DC §1.4; JF2 fields 1-2). The 2026-07-30 window is price-
  anatomy-only (NOT MOF-verified) and stays inside JF2 as an ex-post
  label. Any same-day family is a PIT violation, not a hypothesis.
- **Verdict: OUT-OF-LAW — PIT lag law; JF2 territory ex-post only.**

### C-12 `OPXE-6JA` — options-expiry / pin windows (6A/6J)
- Post-options-expiry unwind class dead: **CNG1-A5-P2** (crypto, ANCESTRY_
  RHO_BLOCK vs oi_level). Monthly/quarterly CME FX option expiry is a
  scheduled calendar-flow class (W1); the delta-hedging mechanism is
  generic expiry-flow, representable outside futures (court §b fails); no
  options anatomy committed on 6J/6A (W4); expiry-date cells for 2023+
  quarters are themselves NOT_OBTAINED with derivation forbidden.
- **Verdict: VETO — dead expiry-flow class + spot-representable + no
  anatomy.**

### C-13 `GLOBEX-OPEN` — 17:00 CT daily open / session-open structure (6J/6A)
- Dead open-class (FXOS-04 Bollinger fade at opens, HOLDOUT_NET_NEGATIVE;
  FXFV1-A3 London-open continuation) + program warning "FX-spot
  session/open — must NOT be transplanted without evidence" (court §a/§b;
  NQ addendum §10). AF3/JF3 own the session-structure space on these
  symbols with measured, era-stable anatomy; a fresh open-window family
  would be the exact transplant the warning forbids.
- **Verdict: VETO — dead open-class transplant + occupied session space.**

### C-14 `JGB-BOJ-OPS` — BoJ JGB-purchase operation announcement windows (6J)
- Operation results/timestamps NOT_IN_CORPUS (`ja_event_pit.json:boj`
  carries statements dates-only; operations never captured — same owner
  decision class as the MPM stamps). Event class = JF1's
  scheduled-BoJ-communication class (W2). The mechanism is a persistent
  YCC-era regime, not an event-window flow; the event-window version would
  need minute stamps that do not exist (W4).
- **Verdict: DUPLICATE-VETO (JF1 class) + DATA (stamps NOT_IN_CORPUS).**

### C-15 `YIELD-CND` — JGB-US yield-spread regime conditioning (6J analogue of AF2)
- AF2 owns the differential-conditioning class (H-F/H-G law; overlay, 0
  identities). A 6J analogue inherits a strictly worse PIT hole: the corpus
  has NO JGB PIT series at all (FRED side = DFF vintages only, year-end,
  no 2025). Dead-corpus warning is explicit: yield-exposure-form controls
  OUT-EARNED their anchors (FXFV8-A5-P1 DGS10 control +19.77/trade = 4.01×
  anchor; FXNG1-A4-P2 CTL-DGS10LEVEL +4.13 vs −6.63) — the class reduces
  to its rates factor.
- **Verdict: DUPLICATE-VETO (AF2 class) + DATA (no PIT JGB series) + dead
  exposure-control precedent.**

### C-16 `COT-6JA` — CoT positioning standalone family (6J/6A)
- FX-F6 CoT-Conditioning owns the overlay class (6E leg; 1,082-wk
  as-published series). JF2 field 3 already carries CoT as companion
  context on 6J. Dead precedent: COMMNG1-A4-P2 (commodities) — all three
  CoT arms killed by **CONTROL_OUT_EARNS_RELEASE_CLOCK** (the bare
  release-clock book beat every anchor). A standalone 6J/6A CoT family is
  a class extension with a dead falsification precedent.
- **Verdict: NOT_NEW — FX-F6 overlay class + JF2 companion + dead
  control-clock precedent.**

---

## 3. Ancestry-check table (law: every candidate vs nearest dead entries + verdict)

Scan basis: all **173** FAMILY_FAILURES.jsonl rows (this lane read the full
file; 41 forex rows enumerated individually); dead FX-spot session corpus =
PB2_ANCESTRY_COURT_DRAFT §a (FOREX-FREE-V1/V2 six cells 12/12
EXPECTANCY_NONPOSITIVE, forced-flat/no-calendar law, "no central-bank event
conditioning capability") + court §b three-part veto test; program warning
(NQ addendum §10 as cited in R2).

| candidate | nearest dead entries (asset, family_id, verdict_class / primary code) | distinguishability | verdict |
|---|---|---|---|
| C-01 FYJ-SEAS | DTPFX1-A1-MEFIX-VARIANT (forex, VARIANT_SAME_FAMILY); FXFV5-A6-P1 (forex, CONTROL_OUTEARNED_ANCHOR — sham-calendar beat anchor); FXNG4-A4-P1/P2+A5-P1/P2 (forex, ANCESTRY_RHO_BLOCK — dow geometry); SFV3-A6-TOM-SETTLE (stocks, PF_BELOW_THRESHOLD); CNG1-A5-P2 (crypto, ANCESTRY_RHO_BLOCK) | NONE — calendar-anchored flow drift is the dead class itself on the same pairs; no scheduled-flow anchor exists to distinguish (court §b fails: representable in spot, already run on USDJPY/AUDUSD) | **VETO** |
| C-02 AF1-MIN | (no dead row needed — blocks on CARRIED AF1, occupancy law) | none offered: same class/hour/venue as AF1 with weaker payload; n≈63-67 inherits K0 | **DUPLICATE-VETO** |
| C-03 JGB-AUCT | FXNG1-A5-P1 (forex, EXPECTANCY_NONPOSITIVE); FXFV6-A4-P1 (forex, PF_BELOW_THRESHOLD razor); FXFV3-A6-P1 (forex, STRESS_TIER_FAIL 47/159 evidenced) | partial: auction dates ARE capturable/PIT — but mechanism to JPY second-order and undocumented in primary sources; window inside JF3; zero committed 6J anatomy at auction minutes | **VETO** |
| C-04 BOJ-RMPG | (blocks on CARRIED JF1 — day-set subset) | none: Outlook dates ⊂ MPM day-2 set | **NOT_NEW (SUBSUMED)** |
| C-05 AU-REL | FXNG1/FXFV6/FXFV5 (forex release-window class); FX-F3 = occupied program class | blocked first on DATA (ABS dates NOT_RUN); window = AF3's modal slot | **DATA-BLOCKED + DUPLICATE** |
| C-06 CN-REL | (no dead row — blocks on AF3 K4 + missing calendar) | none available without the NOT_RUN calendar | **DATA-BLOCKED** |
| C-07 FOMC-6JA | (blocks on occupied classes ES-F1 / FX-F2 + AF1 exclusion) | the measured 6A FOMC anatomy is already AF1's C3″ control evidence | **NOT_NEW** |
| C-08 JP-0850 | FXNG1-A5-P1; FXFV6-A4-P1; FXFV5-A6-P1 (release-window class, forex) | none: 08:50 JST inside JF3; class = FX-F3; flow channel spot-representable | **VETO** |
| C-09 GAP-6JA | FXOS-04 (HOLDOUT_FAILURE_NO_RESCUE); FXFV1-A3-P1 (session/open class) | FX-F4 owns the class; symbol-leg only | **NOT_NEW** |
| C-10 TOKYO-FIX | DTPFX1-A1-MEFIX-VARIANT; TRACKA2-P4A-FIXCERT-01 (DECLARED_BAND_BELOW_MEASURED_COST) | none: fix-window flow is the dead class; 09:55 JST inside JF3 | **VETO** |
| C-11 MOF-INTRA | (out-of-law — no dead row needed) | PIT lag law forbids same-day; JF2 owns ex-post | **OUT-OF-LAW** |
| C-12 OPXE-6JA | CNG1-A5-P2 (ANCESTRY_RHO_BLOCK) | generic expiry-flow representable outside futures; no options anatomy; 2023+ expiry cells NOT_OBTAINED | **VETO** |
| C-13 GLOBEX-OPEN | FXOS-04; FXFV1-A3-P1/P2; program session/open transplant warning | none: exact transplant the warning forbids; AF3/JF3 own session space | **VETO** |
| C-14 JGB-BOJ-OPS | (blocks on JF1 class + stamps NOT_IN_CORPUS) | regime-not-flow mechanism; no stamps | **DUPLICATE-VETO + DATA** |
| C-15 YIELD-CND | FXFV8-A5-P1 (CONTROL_OUTEARNED_ANCHOR — DGS10 exposure control 4.01× anchor); FXNG1-A4-P2 (CONTROL_OUTEARNED_ANCHOR — DGS10LEVEL) | AF2 owns the overlay class; no JGB PIT series; exposure class = the dead corpus's own killer-controls | **DUPLICATE-VETO + DATA** |
| C-16 COT-6JA | COMMNG1-A4-P2 ×3 arms (CONTROL_OUT_EARNS_RELEASE_CLOCK) | FX-F6 owns overlay class; JF2 carries CoT as context | **NOT_NEW** |

Anti-transplant ruling applied throughout (court §b + dispatch law):
session-window momentum/fade transplants from the dead spot corpus are VETO
unless the futures-specific mechanism is unrepresentable there. **No
candidate this round passed that test** — the two R2 families that did
(RMM: contract migration has no spot analog; AF4: venue grid event) remain
the only futures-native mechanisms on these symbols, and both are carried.

---

## 4. Veto-wall summary (the specific wall per rejected candidate)

| # | candidate | primary wall | secondary walls |
|---|---|---|---|
| 1 | FYJ-SEAS | ancestry: calendar-flow class dead ×5 (cited rows) | no PIT schedule; spot-representable; occupied window |
| 2 | AF1-MIN | occupancy: AF1 re-parameterization | K0-class thin n; no release stamp; PB3 PARK |
| 3 | JGB-AUCT | mechanism second-order/undocumented + window occupied (JF3) | no 6J anatomy; dead release class |
| 4 | BOJ-RMPG | occupancy: JF1 day-set subset | — |
| 5 | AU-REL | DATA: ABS dates NOT_RUN | dead release class; AF3 slot occupied |
| 6 | CN-REL | DATA: China calendars NOT_RUN | AF3 K4; occupied window |
| 7 | FOMC-6JA | occupancy: ES-F1/FX-F2 classes; AF1 exclusion | — |
| 8 | JP-0850 | occupancy: JF3 window + FX-F3 class | dead release corpus; no anatomy |
| 9 | GAP-6JA | occupancy: FX-F4 class | dead open-class adjacency |
| 10 | TOKYO-FIX | ancestry: fix class dead ×2 | spot-representable; JF3 window |
| 11 | MOF-INTRA | OUT-OF-LAW: PIT lag law | JF2 ex-post ownership |
| 12 | OPXE-6JA | ancestry: expiry-flow class dead | no anatomy; expiry cells NOT_OBTAINED |
| 13 | GLOBEX-OPEN | ancestry: open-class dead ×2 + program warning | AF3/JF3 session space |
| 14 | JGB-BOJ-OPS | DATA: stamps NOT_IN_CORPUS + JF1 class | regime-not-flow mechanism |
| 15 | YIELD-CND | occupancy: AF2 class + no PIT JGB series | dead exposure-control precedent |
| 16 | COT-6JA | occupancy: FX-F6 overlay class | dead control-clock precedent (COMMNG1) |

---

## 5. Trial-identity estimates (0 consumed, 0 added)

- **This round consumes 0 identities and adds 0.** No NEW family exists to
  enumerate; nothing is registered, scheduled, or budgeted.
- Carried census unchanged (CARRIED_STATUS.md restates it): 6J minimal
  ≈ 29-36 (JF1 11 + JF2 7/host + JF3 11; full-grid 96) — **no 6J cap
  defined; owner ceiling required before any registration**; RMM Role B
  would add 4/leg IF the owner rules the DC §1.3 boundary (6J leg ⇒ +4);
  6A is PB3 PARK ⇒ 0 budget (AF1 11 + AF3 11 minimal and AF4 0 are
  contingency-only census lines; RMM-6A leg 4 IDs same status). Program
  delta from R2 (if everything were someday legalized): +12 IDs (RMM Role B
  8 FX + 4 6J) + 4 contingency-only 6A. This round changes that delta by 0.
- Controls: NOT counted as trial identities (court §c4 convention).

---

## 6. Provisional D1-D5 program scores — carried 6J/6A families (RANKING_FRAMEWORK anchors, applied mechanically; synthesis-lane input)

The RANKING_FRAMEWORK §3 lists the 6J6A rows as **PENDING** for the synthesis
lane; the baseline 3-axis scores (RANKING_INPUT.md) predate the 5-dim rubric.
The scores below are **PROVISIONAL** (synthesis lane owns consolidation),
purely mechanical against the committed anchors, and contain no return
statistic. D5 uses the rubric's r = RT(S2-mid)/MDE(n) floor: where the
committed artifacts state an MDE number, r is derived from it; where they do
not, MDE is NOT_RUN and the anchor is 1 (never inferred).

| family | leg | D1 | D2 | D3 | D4 | D5 | total | mechanical basis (artifacts only) |
|---|---|---|---|---|---|---|---|---|
| JF3 Tokyo-morning | 6J | 3 | **2** | 2 | 3 | 1 | **11** | D1: extrema/shares/depth measured on-symbol, 3 eras. **D2=2, not 3: the dead-corpus clause** — Tokyo-session continuation/fade partially overlaps dead FXFV2-A4-P1's spot signal class (Tokyo-state→London-expansion, 7-pair incl. USDJPY/AUDUSD); court §b category is the honest anchor (same category that cost FX-F1 its D2=2). D3: kills complete, MDE at/above RT. D4: pure in-repo session structure. D5: floor computed (RT 8.45 bp class), court-MDE NOT_RUN. |
| JF1 BoJ MPM window | 6J | 3 | 2 | 2 | 2 | **2** | **11** | D1: 54-day ×1.87/1.27× + 34-vs-53 depth multi-era. D2: actors inferred + window-convention anchor (stamps NOT_IN_CORPUS); no dead overlap (dead corpus had NO central-bank event capability — court §a FACT). D3: kills complete; MDE ≈13-19 bp stated ≥ RT 8.5-14.7. D4: dates FACT; intraday stamps + surprise NOT_RUN. **D5=2: r = 8.45/13-19 ≈ 0.44-0.65 ≤ 1 (MDE number committed).** |
| AF3 bimodal session | 6A | 3 | **2** | 2 | 3 | 1 | **11** | D1: bimodal U-curve + hub shares, 3 eras. **D2=2, not 3: Sydney-morning→US rotation overlaps dead FXFV2-A4-P1's session-state class** (disclosed — the baseline 3-axis MS=3 divergence is this clause, mechanical, not a re-litigation). D3: kills complete incl. K4 Shanghai. D4: pure session structure + DST falsifier. D5: MDE NOT_RUN. |
| AF1 RBA decision minute | 6A | 3 | 2 | 2 | 2 | 1 | **10** | D1: ±5' 9.0×/4.8× + 59/29 measured, n=67. D2: actors inferred; weak surprise proxy; no dead overlap (no CB-event capability in dead corpus). D3: kills complete; K0 pre-registered; per-event scale 4.35 bp < RT. D4: dates PASS at date granularity; decision TIME not carried; surprise NOT_RUN. D5: floor computed; MDE number NOT_RUN in committed artifacts. |
| JF2 MOF regime | 6J | 2 | 3 | 2 | 2 | 1 | **10** | D1: 10-op anatomy + 4/14 leg decomposition; conditioning gradients NOT_RUN. D2=3: named official-flow actor, disclosure-lag law, shuffled-label + null-era controls; **class unrepresentable in dead corpus** (no official-flow conditioning capability — court §b pass). D3: kills complete; n=10 power-marginal. D4: lag-law labels PIT; same-day detection impossible (disclosed). D5: overlay host floor; MDE NOT_RUN. |
| AF2 differential overlay | 6A | 2 | **2** | 2 | **1** | 1 | **8** | D1: 16/16 material-roll sign law; gradients NOT_RUN. **D2=2, not 3: the dead corpus's own killer-CONTROLS were yield-exposure-form books (FXFV8-A5-P1, FXNG1-A4-P2) — partial signal-class overlap, disclosed.** D3: kills complete incl. K2 vintage-flip test runnable. D4=1: DFF latest-vintage conditioning (NOT PIT-strict — the rubric's explicit anchor). D5: overlay host floor. |
| (carried, scored in R2 — unchanged) AF4 TRC | 6A | 2 | 3 | 2 | 2 | 1 | **10** | R2 table stands. |
| (carried, scored in R2 — unchanged) RMM | 4 FX legs | 2 | 3 | 2 | 3 | 1 | **11** | R2 table stands. |

Disclosure (load-bearing, for the synthesis lane): the 5-dim rubric scores
JF3/AF3 at 11 where the baseline 3-axis product gave 18 — the entire
difference is the D2 dead-corpus clause ("or partially overlapping a dead
family's signal class" ⇒ 2), which the 6J6A-lane 3-axis rubric did not
encode. This is the same anchor choice that cost FX-F1 its D2=2 in the
program table (RANKING_FRAMEWORK §3 footnote), applied consistently here.
The rubric's D5 anchors also re-rank JF1 (D5=2, the only 6J/6A family with a
committed MDE number) above the power-starved session families. Both effects
are mechanical consequences of the committed anchors, not judgment calls.

---

## 7. NOT_RUN / NOT_OBTAINED register (this lane)

1. All 16 candidate adjudications are desk adjudications on committed
   evidence; **no anatomy was measured this lane** (Zero-PnL law: no
   conditional-on-signal measurement exists or is disclosed as existing).
2. ABS historical release dates; China Caixin/NBS calendars — NOT_RUN
   (standing; keep C-05/C-06 blocked and AF3 K4 alive).
3. BoJ statement AND operation intraday stamps — NOT_IN_CORPUS (owner
   decision pending; keeps JF1's window convention and blocks C-14).
4. RBA minutes release time-of-day; MOF JGB auction result release
   time-of-day — **NOT evidenced by this lane's captures** (both pages
   state cadence/schedule, neither states a clock time; declared
   conventions would be required for any minute-anchored use — blocks
   C-02/C-03 independent of their other walls).
5. Japan scheduled-release calendar (C-08); any importer/exporter hedging
   schedule (C-01) — NOT_IN_CORPUS; C-01 additionally NOT_OBTAINABLE (no
   such primary schedule exists — absence disclosed, not assumed).
6. BBO / true spread / fill / queue both symbols — NOT_RUN (D5); fees
   MODELED / UNDER REVIEW until A7 (D2) — inherited, unchanged.
7. Owner rulings declared, not self-ratified: 6J ceiling (pre-registration);
   PB3 PARK continuation; D8 era-law ratification; D2 fee A7; D9 cease-guard
   standing law. D1-D12 all open.

---

## 8. Sources

- Local committed artifacts (paths in §0; cited as `file:field` throughout):
  JPY_AUD_HYPOTHESES.md, RANKING_INPUT.md, RANKING_FRAMEWORK.md,
  HYPOTHESES_R2.md, CYCLE_LAUNCH_DRAFT.md, DATA_READINESS_6J/6A.md,
  `6a_roll_measured.json`, `6a_tick_adjudication.json`, `6j_identity.json`,
  `6j_orientation_recheck.json`, `6j_cease_guard_2022.json`,
  `ja_event_pit.json`, `session_holes_2023.json`, FAMILY_FAILURES.jsonl
  (173 rows), PB2_ANCESTRY_COURT_DRAFT.md, NQ_DEEPFOUR_V3_ADDENDUM §10,
  root FUTURES-DATA-10SYMS-V1/FINAL_REPORT.md ("root main d8cf8eca",
  read-only).
- New web captures (2, both 200; sha256 in `SHA256SUMS_lane.txt`; log in
  `fetch_log.jsonl`; ≤2 attempts per URL, 5 fetches total, all GET):
  rba.gov.au/monetary-policy/rba-board-minutes/ (2026-10-04);
  mof.go.jp/english/policy/jgbs/auction/index.html (2026-10-04). Three 404
  attempts (wrong paths) logged, bodies deleted. cmegroup.com not contacted
  (standing BLOCKED_HTTP_403; no capture required this round).

— End HYPOTHESES_FXJA_R3.md. Zero PnL/returns entered any cell; 0 NEW
families proposed; 16 candidates adjudicated with cited walls; carried
census unchanged; missing evidence is NOT_RUN, never PASS. No registration,
no trial creation — proposals on paper only.
