# SUCCESSOR_PLAN_DRAFT — ONOFF-SUCCESSOR-V1 (preparation, 2026-10-01)

**Status: DRAFT, NOT REGISTERED.** Builds on DECISION_PACKET v2.1
(`615f43f4`), the 3 symbol dockets, GATING_VS_SIZING.md and RULE_SLATE.md
(this dir). The 8 PC12A test folds are EXPOSED — hypothesis-generation
only, never validation (owner law). S1 sealed tail untouched.
   Historical ATTRIBUTION ≠ causal ABLATION — cite M1_OPERATIVE_UPDATE §2. Nothing in
this draft is a GO.

## 0. Question

Can a SMALL slate of per-symbol, decision-time ON/OFF rules — learned
from the PC12A trade forensics, thresholds fitted ONLY on a fresh
calendar's earliest window — raise net PnL after all costs AND lower
drawdown versus always-on same-legs, on a genuinely non-overlapping
validation calendar? (PASS = PASS_BARS_V2 AND-semantics + P-MW/P-FA.)

## 1. Rule slate (from RULE_SLATE.md §2; eligibility-only semantics)

| rule | symbol | scope | trigger (decision-time, PIT-clean) | action |
|---|---|---|---|---|
| SU-RS-J1 | USDJPY | all legs' entries | entry-hour UTC ∈ NY window (frozen bounds from LEARN) AND direction_vote=+1 | OFF entry |
| SU-RS-J2 | USDJPY | meanrev family (S014 class) | family_id match at decision | retire (OFF always) |
| SU-RS-J3 | USDJPY | USDJPY-S026 only | L6 guard: cap-multiplier grid {1.5, 2.0, removed} learned on LEARN (per RULE_SLATE §2/§4) | guard relaxation |
| SU-RS-E1 | EURUSD | all legs' entries | entry-hour UTC ∈ {12,16} [HIGH-RISK: shaped on exposed folds — grid re-learned on LEARN to honest ±adjacent hours] | OFF entry |
| SU-RS-E2 | EURUSD (SIG-exit-only class; today EURUSD-S009) | signal-exit-only legs | onoff_features.decision_count_trailing < 3 in trailing 26w (constants frozen) | OFF (codified PC12A E1 floor) |
| SU-RS-G1 | GBPUSD | S017 | family/leg id at decision (1-min stop-out signature) | retire |

Anti-hypotheses (refutation conditions, frozen): per RULE_SLATE §2 —
where this table's paraphrases differ in any particular from RULE_SLATE
§2's frozen REFUTED/floor clauses, the slate text is binding —
e.g. SU-RS-J1 refuted if on fresh folds suppressed-winner net ≥
avoided-loser net in ≥3 folds or DD worsens; SU-RS-J3 refuted if guard-
relaxed book DD exceeds guard-active book DD on ≥3 fresh folds.

## 2. Measured basis (why these rules)

GATING_VS_SIZING §9: harm is a PARTICIPATION phenomenon (skipped trades
−$385.5k vs sizing −$7.3k/2%); **L6 guard = largest single harm** (dollar split is marking-convention-dependent per
  DECOMP §8.3 — independent rebuild gives GATE −$449.6k/SIZE −$18.5k;
  signs, ordering and the identity are stable);
(−$352,959, 91.4% of USDJPY gate harm, folds 1–2); E1 floor net
+$17.3k; E-degradation/W-rules never fired; netting ties $0. Dockets A/B
supply the per-symbol feature contrasts (NY-long bucket sign-consistent
both arms; S017 1-minute stop-outs; S014 negative both arms).

## 3. Protocol (frozen at registration; nothing before)

1. **Hypothesis IDs** SU-H1..H6 = the 6 slate rules + their anti-
   hypotheses; registered BEFORE any fresh data touch.
2. **Thresholds/grids**: one frozen default per rule + ≤3-node grid,
   learned ONLY on the LEARN window; no exposure to validation folds.
   LEARN window per OPERATIVE track (aligned with §3.4): M1-track (N1,
   no-unseal — owner decision M1-CAL): the unsealed never-scored M1
   2026-06-27→2026-09-23 extended by accumulation to 2026-12-26 (the S1
   sealed tail 2026-01-02→2026-06-26 stays SEALED — never a LEARN or
   validation input). DAILY-track: the first 20% of the admitted daily
   panels' calendar (2020-10-02→).
3. **Trial budget**: ≤24 scored identities (battery: slate book, B1S
   always-on, leave-one-rule ×6, random dwell battery [1 identity,
   ≤128 seeds own line], clock-shadow, ×1.5 governing / ×2.0 reporting,
   inverted/lagged if headroom); ≤120 ledger rows (84 scored + 18 LEARN
   grids + margin). STOP at cap.
4. **Validation calendar (NO-UNSEAL OPERATIVE)**. ≥6×26w folds + 1-week
   embargo, non-overlapping with the 2021-01-08→2025-12-26 EXPOSED window,
   the S1 sealed tail (2026-01-02→2026-06-26 — stays SEALED; no unseal is
   authorized), and the LEARN window. LEARN (no-unseal) = the unsealed
   never-scored M1 segment 2026-06-27→2026-09-23 (88 d on file) extended
   by lawful live accumulation to 26 weeks: LEARN 2026-06-27→2026-12-26
   (the 7-day accumulation hole 2026-09-24→2026-09-30 is typed and
   disclosed unless lawfully backfilled; any backfill channel must not
   touch 2026-01-02→2026-06-26). Fold 1 starts 2027-01-02 (LEARN end +
   7 d), readable 2027-07-03; earliest complete 6×26w evaluation
   **2029-12-29** (2030-01-05 if 182 full data days are required without
   backfill). This supersedes RULE_SLATE §4.5's fallback dates and the
   unseal variants (DEAD by owner directive). USDCAD/AUDUSD: **NOT_RUN**
   (no lawful H1/M1 calendar on file; §6 decision packet in
   M1_OPERATIVE_UPDATE.md). Daily-cohort track unchanged (≈10 folds
   feasible today conditional on data-lane gates + owner D-1..D-7).
   "Mid-2027" remains unattainable on every lawful variant.

5. **PIT/cost authority**: panel clock PIT (proven engine); spreads
   measured C1–C3; commission/swap/slippage DECLARED bands with
   PROVISIONAL labels; IBKR statement remains the measured unlock;
   stress ×1.5 governing.
6. **Engine/journal**: PC12A engine lineage (append-only journal_row@1,
   every trade AND blocked signal; add MAE/MFE + per-trade attribution
   — the docket [NR] items; QUOTE-CCY ledger accounting per
   FILL_ACCOUNTING_SPEC §4 as a REQUIRED item — see the currency-convention
   erratum in DECISION_PACKET §13); determinism + truncation replay + leak law
   inherited.
7. **Freeze → A7 → GO**: code/data/selection/cost freeze; fresh-context
   A7 prelaunch; owner GO at the scored gate (phrase registered at
   registration, not consumable from this draft).
7b. **Quote-CCY accounting (REQUIRED, implemented before freeze)**: all
   PnL and DD computed in quote-CCY then converted at ONE frozen
   convention — per-fill realization rate for cash events, equity marks
   at the same bar's conversion rate; USDJPY/USDCHF legs carry an explicit
   JPY/CHF→USD conversion row per fill (closing the PC12A at-par defect —
   DECISION_PACKET §13); reconciliation test: per-symbol quote-CCY books
   must satisfy the §6 identity to 1e-9 AND cross-check against a par-
   convention replay with the disclosed divergence bound.
8. **PASS bars**: PASS_BARS_V2 wholesale (net ↑ AND DD ↓ vs B1S etc.)
   + **P-MW** (OFF rules: avoided-loser net must EXCEED suppressed-
   winner net pooled, Δ(rule)>0; winner column mandatory) + **P-FA**
   (ON rules: admitted set net >0, concentration disclosed).

## 4. Expansion path to 12 assets

EUR/GBP/JPY: this slate at the M1-track calendar (2029+). USDCAD/
AUDUSD: need an H1/M1 collector decision (owner) — else permanently
NOT_RUN for inference. NZD/CHF/XAU/XAG (+BRENT/WTI/NATGAS per the data
lane's EIA dailies): join via a DAILY-TRACK successor cohort once the
data lane's gates pass + owner D-decisions land; each symbol enters
with its own rules under the same PASS bars; no forced cross-symbol
regime.

## 5. Stop conditions

Any anti-hypothesis fires → rule dies (ledger row, no rescue). Ledger
overflow, calendar shortfall, PIT/cost gate failure → typed NOT_RUN.
Negative close is first-class (seventh-death prior stands).
