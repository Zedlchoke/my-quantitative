# TB_LABELS_EXECUTION_PREP — registration-ready execution spec for the TB-LABELS offline producer (HN-6)

Status: **PREP / NOT RUN.** This document registers the execution law of the
TB-LABELS offline producer (analysis-only; labels for forensics; **NO claim,
NO PnL, NO scored row, NO eligibility change**) before any line of it runs.
Companion skeleton: `producer_skeleton.py` (same directory) — imports,
CLI and signatures only; every compute path is `NOT_IMPLEMENTED`.

Authorities (read order):

- `research/control/PORTFOLIO-COMPOSITE-12ASSETS-100K-V1/triple_barrier/INVENTORY_AND_DESIGN.md`
  — the frozen TB design (cited below as **TBD §…/lines**; verified at
  worktree `orca/portfolio-composite-12assets-100k-v1-integration @ a812e73…`).
- `research/control/successor_design_2026-10-02/HYPOTHESIS_REGISTER.md`
  (HN-6, B-H-G2, A-H5, B-H-G1) — cited as **HR**.
- `research/control/successor_design_2026-10-02/SAMPLE_FEASIBILITY_MATRIX.md`
  (INF/ECO floor-causality law) — cited as **SFM**.
- `research/control/successor_design_2026-10-02/SUCCESSOR_PROTOCOL_DRAFT.md`
  (two-freeze law, Track-1, exposure lineage) — cited as **SPD**.
- `research/control/PORTFOLIO-COMPOSITE-12ASSETS-100K-V1/journal/FILL_ACCOUNTING_SPEC.md`
  — cited as **FAS**.
- `research/control/PORTFOLIO-COMPOSITE-12ASSETS-100K-V1/poolB/data_audit/audit_summary.json`
  (panel inventory) — cited as **AUD**.
- Engine citations (`leg_rules.py`, `legs.py`, `panels.py`,
  `calendar_service.py`, `legs_config/*.json`) are at the verified HEAD in
  `.worktrees/portfolio-composite-12assets-100k-v1/integration/research/pc12a/`.

---

## 1. RATIONALE + SCOPE

**What this producer is.** HN-6 (HR lines 332–343): an offline labeling run
over the committed M1 panels for exactly the 3 journaled symbols
(EURUSD/GBPUSD/USDJPY), TRAIN-side plus already-exposed folds labeled
EXPOSED, feeding forensics only. SPD §5 Track-1 item 1 names it the single
highest-leverage analysis unlock; SPD §2 stage (3) places "HN-6 TB-LABELS
TRAIN-side" in IMPLEMENTATION. Every exit-geometry question below is `[NR]`
without it (HR DP-path table, path 2).

**Questions it feeds (all analysis-only):**

| question | hypothesis | what the label supplies |
|---|---|---|
| Did EURUSD-S013's 2.8σ SL fire before the SMA20 TP (stop-before-target ordering)? | B-MEANREV forensics (HR matrix row 3 core leg) | barrier_order + hit_ts per filled trade |
| GBPUSD-S017's 15/28 ≤1-minute stop-outs and 20SL:6TP geometry (HR B-H-G1, lines 130–137) | SU-RS-G1 retire prior | entry-bar touch flags + exit_class distribution |
| GBPUSD-S002 ±2-pip stop vs a ±3-pip alternative path (HR B-H-G2, lines 146–149: "barrier-touch ordering [NR]") | B-H-G2 (DATA-BLOCKED overlay node) | same-entry dual-geometry labels (±2 implemented; ±3 tagged HYPOTHESIS-ONLY) |
| MAE/MFE winner/loser separation | successor engine's MAE/MFE fields (SPD §5) | MAE, MFE per trade within holding |
| A-H5 churn re-entry: "TB-LABELS shows friction-dominance persisting AND a decision-time reformulation" (HR lines 95–99) | A-H5 (benched) | friction-dominance descriptives |

**Applicability — labels are NOT the overlay, and the overlay exclusions do
not bind labels.** TBD §5 ("WHERE THE OVERLAY MAY NOT APPLY", lines 402–433)
excludes A-TREND by owner warning (line 423) and VOLPROF because the class
IS a triple-barrier implementation (line 430) **from overlay-arm creation
only**. TBD §2a (lines 232–239) defines labels "for every FILLED trade in a
journal" with **no family restriction**, and TBD §7 item 5 (lines 498–500)
restates TB-LABELS as analysis-only with the §2a firewall and no family
scope. **Confirmed: trend and VOLPROF legs MAY and SHOULD be labeled for
forensics** (the VOLPROF labels double as a quoted-side touch-basis
cross-check of the engine, T-QUOTE `legs.py:413-417`); they are merely
barred from becoming overlay arms.

**Out of scope:** any PnL, any re-trade, any barrier parameter chosen after
seeing labels (that is a TBD §3 prohibition, lines 357–361), any TEST-fold
label informing a rule (STOP-3, HR HN-6 refutation clause), any write
outside the label output directory (TBD §2a firewall bullet 1–2).

## 2. FEATURE-LABEL SEPARATION LAW

**Construction.** A TB label is a function of the POST-ENTRY future path;
its information time is the hit timestamp, strictly after entry. Under the
campaign §1 PIT clock law and GROUPING_PROPOSAL §3 (no feature may carry
`available_time` > decision time), **labels can NEVER be features,
eligibility inputs, policy inputs, sizing inputs, or arm-selection inputs —
by construction, not by convention** (TBD §2a "Leak law", lines 252–257,
verbatim carry-over).

**Firewall clauses (TBD §2a "Firewall (exact)", lines 240–262, binding):**

1. Label outputs live under `research/control/…/triple_barrier/labels/`
   (schema `tb_label@1`: journal order_id, fold_id, leg ids, entry ts/price,
   direction, barriers, label, hit_ts, ambiguous_flag) — NEVER under the
   engine tree. This prep additionally scopes the successor-cycle run's
   outputs under this cycle's control tree with the same never-engine law
   (registration pins the final path).
2. **No engine import**: `legs.py`, `leg_rules.py`, `policy.py`,
   `run_dry.py`, `journal.py`, `cost_kernel.py` carry zero references to
   `triple_barrier/` — verifiable by grep at any freeze; the producer only
   READS committed journals/panels and WRITES label files. Engine code is
   not modified.
3. **Fold discipline**: TRAIN-fold labels during Stage-A/B analysis;
   TEST-fold labels only inside Stage-C reporting after the scored runs
   they describe exist; sealed tail untouched (TBD §2a lines 258–260).
   Successor-carry-over: TRAIN-side + already-exposed folds labeled
   EXPOSED, forensics-only (HR HN-6 "Action", lines 339–341).
4. **Eligibility**: labels change no eligibility state, add no ledger row
   type beyond their own analysis file, and never feed any PASS-bar input
   (TBD §2a lines 261–262).
5. **Consumption law** (this prep, from HR A-H5 + SFM INF): labels are
   consumed ONLY by (i) loss/forensics analysis and (ii) exit-hypothesis
   PREREGISTRATION input — any rule shaped with their help is a
   POST_OUTCOME_HYPOTHESIS that must be reformulated at decision time and
   re-learned on fresh LEARN before it can run (HR HN-1 law analogy). A
   test-fold label informing a rule before LEARN is a **STOP-3 integrity
   kill** (HR HN-6, line 342). Like INF-layer outputs (SFM lines 70–76),
   labels never enter the order path.

## 3. BARRIER DEFINITIONS PER LEG (leg-own replay table)

Two labeling geometries, both entry-information-only (TBD §3, lines
316–327: barriers are functions of information available AT ENTRY only,
frozen at the entry fill):

**(a) GENERIC form (frozen, uniform, every filled trade)** — TBD §2a lines
231–239 verbatim basis: `U = e + k_U × ATR20_entry`, `L = e − k_L ×
ATR20_entry` (mirrored for shorts), with **k_U = k_L = 1.0** and **H = the
trade's own realized holding time**; ATR20_entry = ATR(20) on the leg's own
decision clock (D1 legs ATR20(D1); H1/H4 legs ATR(20) of the aggregate
clock; M1 session legs ATR(60 M1)). Labels describe the realized path; they
do not re-trade it.

**(b) LEG-OWN barrier replay (forensics mode, per leg)** — the implemented
leg's own TP/SL/TIME levels, frozen at entry, walked on the M1 exit-side
quoted path from fill to the trade's actual close. Sources: TBD §1 rows
(file:line) + frozen configs. **Where corpus intent and implementation
diverge, labels replay the FROZEN IMPLEMENTATION** (the thing that traded),
with the divergence carried as a row note (TBD §1.8 divergences).

| leg | clock / window | TP | SL | TIME / SIG | basis (TBD §1) |
|---|---|---|---|---|---|
| **EURUSD-S013** | H4 bars, no time bound | SMA20 (BB20 mid), close-basis | m ± 2.8σ (σ = (BB_up − m)/2, BB(20, 2.0), ADX(14)<20 gate) | none | C-M1, `leg_rules.py:1662-1689`, config `bb_zscore_fade` |
| **GBPUSD-S017** | M1, **window 15:30–18:30 London; exit eval ONLY inside the window** (`leg_rules.py:2415-2416` early return; bars outside the window are NOT evaluated — the label path applies the same mask) | session VWAP (vol-weighted mid, n≥30) | entry bar close ∓ 1σ of the session distribution (config note "stop +1 sigma"; `leg_rules.py:2434-2440`) | window end (residual carries O/N) | C-M1, `leg_rules.py:2413-2440` |
| **GBPUSD-S002** | M1 session day; entry 09:30 London | none | London 07:00–09:00 range edge ∓ 2 pip (`stop=lo−2pip / hi+2pip`, `leg_rules.py:2009-2012`) | **16:00 London flat** (`LONDON_1600_EXIT`, `leg_rules.py:2005`) | C-M1, `leg_rules.py:1981-2017`, INTRADAY-FLAT |
| **USDJPY-S026** | H1 bars, London ∪ NY session | TP ratchet 1×ATR(D1) extension | 0.5×ATR(H1) inside (`stop_mode: atr_half`) | none (session union; O/N possible) | C-M1, `leg_rules.py:1838-1909` |
| **VC2-LVNFAIL × 3 pairs** | M1 intraday | POC (M1 mid-close crossing) | 1×ATR60 beyond node, **T-QUOTE** (`bid_low ≤ stop / ask_high ≥ stop`, `legs.py:413-417`) | tmax 240 min + 19:55 UTC hard flat (`tmax_min: 240`) | TP C-M1 / SL T-QUOTE, `legs.py:402-423` |
| **USDJPY-S014** | H4 bars, ~8 bars | none | 1×ATR(H4) (`stop_atr_mult: 1.0`) | SIG (RSI2→50) + TIME (8 H4 bars, `exit_bars: 8`) | C-M1, `leg_rules.py:1703-1759` |
| **EURUSD-S009** | D1 bars, multi-week | — | — | SIG only (MACD-H dual divergence) | C-D1, `legs.py:715-789`; SIGNAL-EXIT-ONLY (TBD §1.1 row) |

**S009 and SIGNAL-EXIT-ONLY legs — what the design says.** TBD §2a defines
labels for **every** filled trade using the generic form; §5's exclusions
are overlay-scoped only (§1 above). Therefore S009 (and the other 17
signal-only legs) receive **generic-geometry labels of their would-be
barrier paths**: U/L = fill ± 1.0 × ATR20(D1), H = realized holding, walked
on the M1 sub-path (available for the 3 staged pairs even for D1-clock
legs, TBD §0 lines 33–36). The leg-own replay columns are empty for such
legs by construction (they have no barriers); the label answers "which
synthetic ±1×ATR20 barrier did the realized path touch first before the
signal exit". No overlay arm is created for them (TBD §5).

**B-H-G2's ±3-pip alternative**: the producer may emit a second, separate
label set for GBPUSD-S002 entries with SL widened to ±3 pips, tagged
`geometry=HYPOTHESIS_BHG2_ONLY`; these are forensics inputs to a future
overlay node registration, never a claim (HR B-H-G2 DATA-BLOCKED: needs
HN-6 + fresh calendar).

## 4. AMBIGUOUS_ORDER LAW (the co-owner's named hazard)

**Definition (TBD §4, lines 367–371, adapted to labels).** M1 panels are
per-minute two-sided OHLC (record `(sec_offset, open, close, low, high,
volume_f32)`, Dukascopy order `t_o_c_l_h`, 1440 records/day/side —
`panels.py:8-21`; the dispatch's `b_o/b_h/b_l/b_c` + ask side maps to these
fields). The intrabar path inside one M1 bar is UNKNOWN. If on an
evaluation bar BOTH barrier levels lie inside the bar's quoted-side range
(long: `bid_low ≤ SL < TP ≤ bid_high`; shorts mirrored on ask) then the
touch order is undetermined: the label MUST be **`AMBIGUOUS_ORDER`**
(`ambiguous_flag = true`), never a guessed order.

**Tie-break policy — CONSERVATIVE, with the design's SL-first law quoted
where it applies.** The frozen design's pessimistic default (TBD §4 lines
373–379, the "SL-first ambiguous law" named by the co-owner in
`terminal_review_2026-10-01/DECISION_PACKET.md` line 171; campaign
precedent `BTC-COMBO6-SCORED-V1/DATA_COST_FREEZE.md` line 31 "same-bar
TP+SL → SL first") states: ALL ambiguous bars of a RUN resolve SL-first
(the adverse order), applied uniformly — no per-run, per-leg choice — with
the ambiguous-bar fraction reported per arm and a run with >20% ambiguous
bars typed `NOT_RUN_TOUCH_RESOLUTION`. **For LABELS the order of authority
is:**

1. The label row records `barrier_order = "AMBIGUOUS_ORDER"` +
   `ambiguous_flag = true`. No guessed TP-first or SL-first order is ever
   written as the label.
2. `resolved_order = "SL_FIRST"` is emitted as a SEPARATE, clearly-derived
   field (constant, uniform, never conditioned on anything) so that
   PnL-bearing or aggregate consumers may apply the frozen §4 default —
   but every such consumer must disclose the ambiguous fraction alongside
   (§4's >20% law gates comparability; the labels analog is stated below).
3. No other resolution exists. Deeper recursion is impossible by data
   (M1 is the finest panel; TBD §4 lines 380–388 — for the 3 staged pairs
   the ambiguous fraction collapses to same-M1-bar double-touches only,
   after walking M1 bars inside any coarser evaluation bar).

**Ambiguity counting is a first-class output stat (no data may be touched
to estimate it now — this prep runs over nothing).** The producer's run
manifest MUST report, per symbol × leg and pooled: `ambiguous_trades`,
`ambiguous_fraction_of_labeled_trades`, `ambiguous_bars /
evaluated_bars` (§4's own denominator), and the same stats restricted to
entry-bar touches (the S017 hazard class). The first real run's ambiguity
report is a gating artifact: downstream forensic reads of any leg whose
ambiguous fraction exceeds 20% must carry that leg's
`NOT_RUN_TOUCH_RESOLUTION`-analog qualifier (the §4 law transposed from
overlay PnL to label consumers — recorded, never silently accepted).

## 5. QUOTE-SIDE + SPREAD + FILL-LAG

**Quote side.** Barriers are evaluated on the QUOTED side you exit into —
long exits at BID, short exits at ASK — per TBD §2b's four touch cases
(lines 277–287: long TP `bid_high ≥ TP`; long SL `bid_low ≤ SL`; short TP
`ask_low ≤ TP`; short SL `ask_high ≥ SL`) and §2a's label basis ("first
barrier touched on the exit-side quoted series", lines 235–237). Spread is
taken from the SAME bar's two-sided quotes (mid = same-bar bid/ask mid,
FAS §1.1; mixing sides is an integrity trip). The §2b touch-fill price law
("fills execute at the touch bar's quoted side … never at the barrier
price"; gap-through → fx6 worst-fill grade, worst of the touch bar's
open/close on the quoted side — TBD §2b lines 289–295, §6 lines 439–453,
FAS §1.5) is recorded as the exit's `cost_label`, not re-priced here.

**Fill lag — which campaign law applies to which exit class (FAS §1.3,
lines 36–48):**

- **Decision-basis exits (SIG, TIME classes)**: the decision at T fills at
  the **NEXT bar open** (bar spanning [T, T+1min)); buys at `ask_open +
  slip`, sells at `bid_open − slip` (FAS §1.3). Label `exit_ts` = the fill
  bar; `cost_label = NEXT_BAR_OPEN`.
- **Touch-basis barrier exits (TP/SL/TRAIL on quoted side)**: exit AT the
  touch bar's quoted side under the spread-once kernel (TBD §2b/§6); no
  next-minute lag. `cost_label = TOUCH_BAR_QUOTED_SIDE`; gap-through bars
  get `cost_label = FX6_WORST_FILL` (worst of touch-bar open/close on the
  quoted side; never the barrier price).
- **Rollover/Sunday-reopen touch bars** (21:00–22:00 UTC window; reopen
  first 15 min): `cost_label = C2C3_CELL` (FAS §3, corrected Mon–Thu cells
  govern). Sunday-reopen spreads measured up to ~9–24 pips p90 per pair
  (AUD spread §C3) — a quoted-side touch at reopen is often spread-made,
  not price-made; the label keeps it, the cost_label flags it.

**Entry bar evaluation (S017's 15/28 ≤1-minute stop-outs, HR B-H-G1).**
Because the entry fill is at the fill bar's OPEN (FAS §1.3), the entire
fill bar [T, T+1min) is post-entry: **the entry bar IS evaluated for
barrier touches.** Rules: (i) a touch inside the fill bar → `exit_class`
per the touch side, `hit_ts` = the fill bar, `entry_bar_touch = true`
(intra-bar resolution is bar-level only — the ≤1-minute stop-out class is
exactly this row population); (ii) both barriers inside the fill bar's
quoted range → `AMBIGUOUS_ORDER` per §4 above; (iii) the fill bar's OPEN
already beyond the SL (born-through-barrier) → order IS determinable (the
open is the bar's first price): `exit_class = SL`, tag
`BORN_THROUGH_BARRIER`, gap-through priced per fx6; (iv) censoring — an
entry-bar touch never looks past the trade's own window mask (S017's
window law §3) or session flat; a trade touched-and-closed inside the
entry bar has MAE/MFE computed from entry fill to that bar's extremes
only (§7).

## 6. TIMEZONE / DST

Sessions are defined by named IANA tzdata zones via `zoneinfo`, never
hardcoded UTC offsets — the engine's own frozen law: session windows
rebuilt from IANA tzdata (Europe/London, America/New_York), **no hardcoded
DST offsets** (`calendar_service.py:8-12`, authority CLASS_SPEC_VOLPROF_M1
§4; `_TZ_LONDON = ZoneInfo("Europe/London")`, `calendar_service.py:33`;
every leg config carries the `TZDATA_SESSIONS` pit-join). The producer
MUST reuse the engine's zone objects/laws byte-for-byte (read-only import
of the frozen constants, or a copy carrying the same authority citation),
and MUST pin the tzdata version in the run manifest.

**The S002 16:00 London exit shifts in UTC across DST** — 16:00 Europe/London
= 16:00 UTC in GMT winter, 15:00 UTC in BST summer; the label path derives
the flat minute per-day from the zone, exactly as the engine does
(`tz_minutes(ctx.ts, "Europe/London")`, `leg_rules.py:1988,2005`). Same law
for S017's 15:30–18:30 window and S026's London∪NY session union.

**Calendar dependency (named sources).** Primary: IANA tzdata via
`zoneinfo` + the engine's `calendar_service.py` session marks. Holiday
calendar: the DAILY cycle's frozen precedent
`DECLARED-PANEL-CALENDAR@1` (`.worktrees/pc12a-daily-exploratory-prep/
research/daily_exploratory/datainputs.py:152-155`: "weekend-skip PLUS each
panel's own recorded session calendar — holidays are whatever the frozen
panel itself did/did not record; nothing is inferred") — a minute is valid
iff `vol>0, ask≥bid>0` (sanity-banded), the same validity rule as
`D1_SESSION_1700ET@1` (`datainputs.py:24-27`: a D1 session T spans
[17:00 ET (T-1), 17:00 ET T), ET = `ZoneInfo("America/New_York")` —
DST-aware; that is what DAILY used and it is the named precedent for
panel-calendar truth). **`exchange_calendars` is NOT used by any frozen
campaign on this checkout; introducing it would be a new calendar source
requiring registration. Do not.**

## 7. CENSORING

- **MAE/MFE** are measured entry→exit ONLY within the trade's holding and
  its own window/session masks (S017 window, S002 day, VC2 19:55), on the
  exit-side quoted path: MAE = max adverse quoted excursion vs entry fill
  (pips, SL-side), MFE = max favorable excursion (TP-side). Bars outside
  the mask never contribute (S017's early-return law, §3).
- **Force-flat / fold-edge exits right-censor**: `censoring =
  "CENSORED_FF"` — the label's TIME/timeout reading is the flat law, not a
  barrier verdict; MAE/MFE remain valid up to the flat bar (TBD §2b line
  271-274 fold-edge force-flat is a venue fact; PASS_BARS E-Law 2
  referenced there).
- **Trades open at panel end (2026-09-23)**: `censoring =
  "CENSORED_PANEL_END"` — right-censored at the last tradable bar; no
  label class beyond the censor tag is asserted.
- **Swap-charged nights do not affect path labels** but are journaled
  (count of 22:00 UTC accrual boundaries crossed while held, Wed ×3 — FAS
  §2 swap calendar): a `swap_nights` field on the row, information only.
  Path labels are price-path facts; swap is a book fact.

## 8. BUDGET + IDENTITY

- **Identity: analysis-only.** 0 scored rows; no PASS-bar input; no
  eligibility change; outputs carry an explicit NOT-a-claim header on
  EVERY file: `TB-LABELS ANALYSIS-ONLY — POST_OUTCOME BY CONSTRUCTION —
  NOT A FEATURE, NOT AN ELIGIBILITY/POLICY/SIZING/ARM INPUT — NO CLAIM`
  (plus run id, spec sha, window class, panel manifest hashes, tzdata
  version, engine HEAD).
- **Compute budget**: producer runs over 3 symbols × committed panels
  (2,092 day-files/side × 2 sides × 3 pairs, 1,440 M1 records/file — AUD
  panels inventory; ~2.13M tradable minutes/side/pair). Labeling cost is
  O(filled trades × holding minutes); panel decode is the fixed floor.
  Single machine; if run as a batch job it takes the machine-wide heavy
  lock per workspace law; every run is one ledger row (owner amendment
  2026-09-29 §2: every exploratory computation is a ledger row — TBD
  header lines 9-11).
- **Outputs**: per symbol × leg, `labels_<SYM>_<LEG>.jsonl` (+ parquet
  mirror) under the control-tree labels directory (§2 clause 1), schema
  `tb_label_v2@DRAFT` = frozen `tb_label@1` fields (journal order_id,
  fold_id, leg ids, entry ts/price, direction, barriers, label, hit_ts,
  ambiguous_flag) PLUS the fields this prep requires: `trade_id, leg,
  entry_ts, exit_ts, exit_class, barrier_order, resolved_order,
  ambiguous_flag, MAE, MFE, censoring, cost_label, window_class,
  entry_bar_touch, geometry, swap_nights`. One `run_manifest.json` with
  the §4 ambiguity stats, input hashes, and the NOT-a-claim header.
  Registration pins the final schema name.
- **Execution gating**: this producer may run over EXPOSED/TRAIN windows
  ONLY after this prep is owner-reviewed; default window allowlist =
  campaign window 2021-01-08 → 2026-06-26 (`calendar_service.py`
  CAMPAIGN_START/END), every row tagged `window_class ∈ {TRAIN, EXPOSED}`
  (the whole window is statistically exposed — SPD §1.1 lineage: tail
  dates read by DAILY, PROVEN-EXPOSED / permission NOT_RUN_UNPROVEN, two
  axes never merged). Dates in (2026-06-26, 2026-09-23] are PC12A
  sealed-tail class: the producer REFUSES them (`SEALED_TAIL_REFUSED`)
  until a registered cycle + owner says otherwise. TEST-fold labels of a
  future successor calendar are produced only inside that cycle's Stage-C
  reporting (§2 clause 3).

## 9. DEFECTS / RISKS (named, honestly)

1. **Same-bar ambiguity rate is UNKNOWN until the first run** — no number
   exists today (this prep ran over nothing). The producer's ambiguity
   report (§4) is a gating artifact and must precede any downstream use;
   legs over 20% ambiguous carry the NOT_RUN_TOUCH_RESOLUTION-analog
   qualifier on every forensic read.
2. **Corpus-vs-implementation stop divergence** (e.g. S017's short-side
   `stop = c − σ` code vs the corpus "+1σ stop" wording; 13 strong D1
   divergences TBD §1.8). Labels replay the implementation; any reader
   wanting corpus intent must re-derive — the row carries the divergence
   note. Misreading corpus intent as the barrier law is the top
   misinterpretation risk.
3. **DST / tzdata drift**: 16:00 London and 15:30–18:30 window bounds move
   in UTC; a tzdata version change between engine run and label run would
   silently shift TIME exits. Mitigation: pinned tzdata version in the
   manifest + reuse of the engine's frozen zone law (§6).
4. **Quoted-side spread artifacts**: reopen/roll spreads reach 9–24 pips
   p90 (AUD §C3) — quoted-side touches near 21:00–22:00 UTC / Sunday
   reopen can be spread-made; weekend flat-carry bars (vol=0, stale
   prices) must be excluded by the tradable-minute mask or they
   phantom-extend paths. `cost_label` flags the affected rows.
5. **ANC H1 reference panels lack ask-high/low** (H1 columns are for
   reference only — AUD format_and_volume): irrelevant here — all barrier
   walking for the 3 symbols is on the two-sided M1 panels; it would bind
   only if a future leg needed H1 ask-side extremes (named, so nobody
   "fixes" it silently).
6. **The TD-archive XAU overlap is irrelevant here**: XAUUSD is one of the
   7 blocked daily-only assets; TBD §4 lines 391-398 makes within-day TB
   resolution IMPOSSIBLE for it — no labels are produced for blocked
   assets, full stop.
7. **Window permission axis**: the panel extends to 2026-09-23 but the
   sealed-tail slice (post 2026-06-26) is refusal-locked (§8); the
   exposed-but-unratified tail question (SPD §1.1) is an OWNER action,
   not a producer decision.

— end prep —
