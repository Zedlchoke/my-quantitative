# GUARD_AND_SESSION_FORENSICS — successor_design_2026-10-02 / TRADE-FORENSICS lane

**STATUS HEADER.** ANALYSIS ONLY: journal-row counting/arithmetic over the
COMMITTED PC12A Stage-C journals
(`research/control/PORTFOLIO-COMPOSITE-12ASSETS-100K-V1/diagnostics/stagec/ARMS/{POLICY,B1_ALWAYS_ON}/journal.jsonl`).
No engine run, no PnL replay (no excursion reconstruction), no sealed/S1
bytes, no network. Every PnL number in §3 is CITED from the 2026-10-01
dockets and labeled **ATTRIBUTION-on-exposed-path** — none is a marginal-PnL
or counterfactual claim. Machine evidence (this dir, produced by
`forensics_build.py`): `guard_spend_band_histogram.json`,
`session_dst_alignment.json`, `verification_checks.json`. Companion brief:
`TRADE_FORENSICS_BRIEF.md` (inventory, reconciliation, one quantified docket
A defect: swap added with the wrong sign — §2.3 there).

---

## 1. GUARD SPEND-BAND HISTOGRAM and J3 grid-node feasibility counts

This is the counting exercise the register demanded before J3 registration
(HYPOTHESIS_REGISTER A-H1/SU-RS-J3: "commit the guard SPEND-BAND HISTOGRAM
from the exposed journals (lawful counting exercise) so node feasibility is
computed"; SAMPLE_FEASIBILITY_MATRIX row 5 typed m∈{1.5,2.0} "NOT ESTIMABLE
from committed evidence — no artifact holds the spend distribution between
cap and m×cap").

### 1.1 Parse verification `[M]`

- All **331** POLICY DEFER rows and all **296** B1 DEFER rows carry
  `blocked_reason_detail` = "L6 cost guard: trailing 28d spend X >= cap Y";
  regex parse succeeds on **100%** of rows, and X/Y agree with the
  structured `guard.{trailing_spend_usd, cap_usd}` field on every row
  (string is the 4-decimal rounding of the structure).
- **Cap is constant $2,836.97 on every DEFER row in BOTH arms** (verified;
  matches the citations in docket A H1 and the register). Window = 28 days
  everywhere.
- Defer votes (POLICY): 130 rows `direction_vote=+1`, 201 rows vote 0, none
  −1 (B1: 99 / 187 / 10). The guard defers flatten-votes too — admission of
  a deferred row can mean a longer-held position, not only a new entry.

### 1.2 Ratio r = X/Y distribution of FIRED defers `[M]`

| stat | POLICY (n=331) | B1 (n=296) |
|---|---:|---:|
| min | 1.00 | 1.00 |
| q25 | 1.02 | 1.02 |
| **median** | **1.03** | **1.06** |
| mean | 1.04 | 1.09 |
| q75 | 1.07 | 1.10 |
| q90 | 1.07 | 1.22 |
| q95 | 1.11 | 1.41 |
| **max** | **1.20** | **1.41** |
| share ≥ 1.1× | 5% | 27% |
| share ≥ 1.2× | 0% (0 rows; max 1.20) | 15% |
| share ≥ 1.5× | **0%** | **0%** |
| share ≥ 2.0× | **0%** | **0%** |

The fired-defer mass sits in a thin band **just above the cap**: the guard
bind serially while spend hovers at cap+ε (deferring adds no spend, so it
stays pinned until the 28d window rolls off). **No fired defer ever reached
1.5× cap in either arm.**

### 1.3 Grid-node feasibility counts (m ∈ {1.5, 2.0, ∞}) `[M: static counts]`

Under node m (cap × m), a fired defer with X ≥ m·Y would STILL defer (TRUE
defer); X < m·Y would have been ADMITTED.

| arm | node m | TRUE defer | admitted | folds with admitted ≥3 | per-fold admitted (f0..f7) |
|---|---|---:|---:|---:|---|
| POLICY | 1.5 | **0** | **331** | 8/8 | 15/62/57/30/25/79/47/16 |
| POLICY | 2.0 | **0** | **331** | 8/8 | same |
| POLICY | ∞ (off) | 0 | 331 | 8/8 | same |
| B1 | 1.5 | 0 | 296 | 8/8 | 15/62/12/64/30/62/39/12 |
| B1 | 2.0 | 0 | 296 | 8/8 | same |
| B1 | ∞ (off) | 0 | 296 | 8/8 | same |

**These are counts of DECISION ROWS under a counterfactual threshold — NOT
marginal PnL.** The admitted-set PnL is measurable only by full-path replay
(netting path-dependence: re-admitted fills change later netting, sizing and
the spend path itself). Two hard caveats:

1. **Endogeneity.** Under a real cap ×1.5 the trailing-28d spend path
   evolves differently (admitted fills add spend), so the guard could re-bind
   at 1.5×cap later and generate defers NOT in the observed set. The static
   count is an ordering tool, not a simulation.
2. **Selection.** The histogram observes only FIRED defers. Decisions with
   spend < cap were already admitted and carry no `guard` field in the
   journal — the unconditional spend distribution at all 3,467 decision
   points is NOT on file (adapter spec #5, §4).

**Reading for the register (resolves the NOT ESTIMABLE flag):** on this
window's fired-defer corpus the nodes m=1.5, m=2.0 and ∞ are **identical in
static count** — 100% of fired defers sit in [1.00, 1.20]×cap (POLICY;
B1 max 1.41), so the "spend distribution between cap and m×cap" flagged as
missing is in fact ALL of the mass, and the feared per-fold thinness
("per-fold <3 = 30%, VAL <20 = 32%") does not materialize statically: every
fold would admit ≥12 (POLICY ≥15) and the window admits 331/296 against a
floor of ≥20. The grid {1.5, 2.0, ∞} therefore contains effectively ONE
static node (∞) on this corpus; a grid intended to differentiate must place
nodes inside [1.00, 1.41] (e.g. m=1.1 keeps ~5% POLICY / ~27% B1 of fired
defers deferred; m=1.2 keeps ~0% / ~15%). LEARN-window re-binding remains a
live risk and keeps the register's pre-typing caution.

Closest PnL proxy on file (cited, NOT a node count): 29 of the 331 POLICY
defers were actually filled by B1 at the identical (leg, ts) and netted
**+274,572 (16W/13L)**, one trade 46% of the total; removing them WORSENS
B1's USDJPY maxDD −378,482 → −501,493 (docket A §6 ON-RULE) — the guard
deferred trades that were drawdown-REDUCING on B1's path. Overfit risk HIGH
(n=29); POST_OUTCOME_HYPOTHESIS per the register.

---

## 2. SESSION / DST ALIGNMENT (descriptive composition of the two negative buckets)

Units: **DECISION rows**, not trades/excursions — the docket buckets (91/74
NY excursions; 57/59 suppressed trades) are entry-side reconstructions and
are NOT comparable counts; nobody should read 172 against 91. B1's DECISION
stream is the corpus superset (3,467 vs POLICY 3,124, census
`decision_dedup`); both are shown.

### 2.1 USDJPY NY-long bucket (vote=+1, UTC hour ∈ [16,21))

**Composition by DST phase × UTC hour `[M]`** (Europe/London: BST from last
Sunday of March 01:00 UTC to last Sunday of October 01:00 UTC; date-level
classification is exact for hours ≥12 UTC):

| phase \ hour | 16 | 17 | 18 | 19 | 20 | total |
|---|---:|---:|---:|---:|---:|---:|
| GMT (winter) POLICY | 27 | 8 | 4 | 12 | 16 | **67** |
| BST (summer) POLICY | 36 | 23 | 16 | 8 | 22 | **105** |
| GMT B1 | 27 | 8 | 4 | 12 | 16 | 67 |
| BST B1 | 36 | 23 | 17 | 8 | 22 | 106 |

Annual totals (POLICY): 2022: 54 · 2023: 38 · 2024: 42 (February zero) ·
2025: 38 — the bucket is present in BOTH phases in every year. Full 47-month
× hour matrix: `session_dst_alignment.json`.

**London-close drift overlay** (the bucket's meaning shifts by phase):

| phase | London 16:00 close in UTC | bucket [16,21) offset from close | NY-local span of bucket | NYSE open in UTC |
|---|---|---|---|---|
| GMT (winter) | 15:00 | +1 … +5 h | 11:00–16:00 EST | 14:30 |
| BST (summer) | 14:00 | +2 … +6 h | 12:00–17:00 EDT | 13:30 |

The fixed UTC bucket starts 1h after London close in winter but 2h after in
summer and spans a different NY-local window — any succession rule keyed to
this bucket (A-H2 / SU-RS-J1) must be declared in UTC-with-DST-phase or
local-clock terms, never bare UTC.

**Descriptive flag (counts only):** 61% of the bucket's decision mass falls
in BST months vs a 7/12 ≈ 58% calendar expectation — **no concentration in
one DST phase beyond calendar share**. Whether the bucket's PnL (docket:
POLICY −281,460 / B1 −83,684 on excursions) concentrates in one phase is
**NOT_RUN** under this lane (PnL-by-DST-phase needs per-excursion
reconstruction = replay; adapter #4).

### 2.2 EURUSD hours {12, 16} (nonzero-vote decisions)

| phase \ hour | 12 | 16 | total | vote split (short/long) |
|---|---:|---:|---:|---|
| GMT POLICY | 8 | 19 | 27 | h12 4/4 · h16 10/9 |
| BST POLICY | 5 | 28 | 33 | h12 3/2 · h16 15/13 |
| GMT B1 | 8 | 21 | 29 | h12 4/4 · h16 11/10 |
| BST B1 | 5 | 28 | 33 | h12 3/2 · h16 15/13 |

Annual totals (POLICY): 2022: 19 · 2023: 14 · 2024: 18 · 2025: 9; grand 60
(B1 62). Hour 16 dominates (47/60 POLICY). BST share 55% — if anything
slightly UNDER calendar expectation; votes are near-symmetric short/long in
every phase-hour cell. Same DST-phase caveat as §2.1 (hour 16 = 17:00 London
summer vs 16:00 London winter; hour 12 = 13:00/12:00 London). PnL-by-phase:
NOT_RUN.

---

## 3. TWO-SIDED descriptive tables (from the dockets, cited; ATTRIBUTION-on-exposed-path — NOT marginal PnL)

### 3.1 USDJPY NY-session long block (docket A §6 OFF-RULE; A-H2 basis)

| side | n | $ (par journal units) |
|---|---:|---:|
| losers avoided | 50 | −795,805.74 |
| winners suppressed | 38 | +514,369.07 |
| **net attribution effect** | 91 removed | **+281,460.12** |
| maxDD after (weekly reconstruction) | | −412,208.31 → −359,621.76 |
| folds touched | all 8 (13/5/9/12/9/15/15/13) | sign-stable |

Both-arm agreement: POLICY −281,460.12 (n=91) and B1 −83,683.91 (n=74) — the
only tested off-rule PnL- AND DD-consistent in both arms and all folds;
pooled long×NY −384,746.52 vs London longs +972,340.40. Long-only split is
POST_OUTCOME (docket A §7 H2). DST composition of the underlying decision
stream: §2.1 above.

### 3.2 EURUSD entry-hour gate 12:00/16:00 UTC (docket B R-E2; H-E2 basis)

| arm | suppressed n | suppressed net $ | winners cut (missed) | losers cut (avoided) | maxDD all → rule |
|---|---:|---:|---|---|---|
| POLICY | 57 | −495.9 | 17 / −901.4 | 40 / +1,397.3 | 878 → 387 |
| B1 | 59 | −1,037.1 | 21 / −1,440.7 | 38 / +2,477.7 | 2,277 → 977 |

Positive on both arms (6/8 folds negative-suppression each) — the honest
costs are the positive-suppression folds (POLICY f0–f1; B1 f5/f7). Note: the
"17W/40L" shorthand attached to this gate in the dispatch packet describes
the POLICY arm only; B1 is 21W/38L. Mechanism named (S013's H4 votes inside
the London/NY handover + NY-open spread widening), cost-visible in docket B
§5 session-spread medians.

### 3.3 E1 floor: saves vs costs per leg (docket B R-E1/R-E3; docket A §6 E-floor OFF; dossier §2)

| side of the floor | leg(s) | $ | citation |
|---|---|---:|---|
| floor SAVED (avoided loss) | EURUSD-S009 missed set (49 B1 trades POLICY never took) | −504.0 avoided (B1 S009 book −587.8/50) | docket B R-E1 |
| floor COST (missed profit) | EURUSD VC2 strictly-blocked subset (13 trades) | +227.4 missed (B1 VC2 book +653.0/26) | docket B R-E3 |
| floor REMOVED (USDJPY, paper) | S003 +225,631.11 · S023 +230,099.40 · S002 −24,268.70 · VC2-JPY −2,804.70 = **+428,657.11 four-leg paper sum** (the "+428.7k" citation includes VC2's −2.8k) | | docket A §6 |
| floor REMOVED (USDJPY, realized entries) | B1 excursions entered by blocked legs | +187,084.33 (n=13) | docket A §6 |
| floor BENEFICIAL (JPY) | USDJPY-S002: solo always-on −248,990 vs POLICY floored book +137,883 (34 fills) | | dossier §1; census |

Paper ≠ realizable: solo-leg paper ignores netting (realized ≪ paper is the
expected failure mode, H3); every row above is an attribution on the exposed
path under a named law.

---

## 4. NOT_RUN_INPUT_MISSING + adapter specs (what the successor journal must record)

Analyses this lane could NOT run, the missing field, and the 5-line adapter
spec for each (successor engine `journal_row@2` proposals; all are
emit-at-time fields, none require offline path reconstruction):

1. **MAE/MFE per excursion** — missing: no excursion-path fields exist
   (journals record fills and nightly swap only; TB-LABELS not run).
   Adapter: on each NET_ORDER, emit `excursion_ref` + running
   `mfe_usd`/`mae_usd` (and pips) vs the excursion's entry mid, computed by
   the engine per M1 bar while the position is open; also final values on
   the flattening fill. Consumed by: exit-law forensics (did SIG-ENTRY
   losers give back open profit), H5 churn filter, TB-EXIT-OVERLAY design.
2. **Per-fill quoted spread at the entry/decision bar** — missing: journals
   carry the charged model outputs (`spread_once_usd`, C-cell tag) but not
   the market quote (C1–C3 are DECLARED bands; NY-bucket "spread-victim"
   story untestable). Adapter: on DECISION and NET_ORDER rows, emit
   `quoted_spread_pips`, `quoted_bid`, `quoted_ask` from the M1 panel at the
   decision bar and at fill time. Consumed by: session-bucket cost
   attribution, cost-authority upgrade evidence.
3. **Realized vol / trend state at entry** — missing: `feature_pit_snapshot`
   carries value digests only (no numeric features). Adapter: on DECISION
   rows, emit the leg's own feature vector numerically (e.g. realized vol,
   ADX, z-score) alongside the digest. Consumed by: W/L feature separation
   beyond dct's null (δ=0.028), regime tagging of the NY/EUR hour buckets.
4. **Per-excursion machine sidecar (for DST-phase PnL and any bucket-PnL
   split)** — missing: no committed per-excursion artifact exists (only
   aggregate docket tables), so PnL by DST phase / session / hour is
   NOT_RUN without replay. Adapter: emit one row per closed excursion:
   `excursion_id, symbol, entry_ts_utc, exit_ts_utc, direction, max_units,
   n_fills, net_usd, gross_usd, friction_usd, exit_class, fold_id, force_flat_flag`.
   Consumed by: descriptive bucket PnL splits (this packet §2), guard-node
   diagnostics, successor rule forensics — all without engine re-runs.
5. **Unconditional guard telemetry** — missing: `guard.{trailing_spend_usd,
   cap_usd}` appears ONLY on DEFER rows, so the spend distribution at
   non-fired decisions is unknown and dynamic node re-binding cannot be
   counted. Adapter: on every DECISION row with a nonzero vote, emit
   `guard.trailing_spend_usd` and `guard.cap_usd` regardless of whether the
   guard fires. Consumed by: J3 node feasibility on LEARN/VAL (dynamic, not
   static), grid placement inside [1.0, 1.41]×cap.

Also NOT_RUN and NOT adapter-fixable here: intrabar stop/target ordering
(needs the TB-LABELS lane over the committed M1 panels) and any
portfolio-minus-one-leg counterfactual (needs the successor battery's
leave-one-leg arms; solo ≠ minus-one).

— end forensics —
