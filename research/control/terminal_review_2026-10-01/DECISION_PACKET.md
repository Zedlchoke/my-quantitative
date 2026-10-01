# DECISION_PACKET v2 — terminal review of PC12A & EOSV2 (2026-10-01, revision of fc26adf1)

Prepared by A1, preparation-only. No new GO, no scored runs, no S1, no
paper/live/orders, no registration, no registry hand-edits, no reuse of
closed-cycle budgets. Both TERMINAL cycles preserved (verified below).
v2 revises v1 (commit `fc26adf1`) per the owner's six-gap follow-up; §7
lists every correction. Evidence markers: **[M]** = measured from
committed artifacts (path cited); **[H]** = hypothesis, not evidence;
**[NR]** = NOT_RUN / not established.

## 1. Monitoring snapshot (measured this session)

Root `main @ cbd39395…` (v1 packet at `fc26adf1` on top); dirty tree =
owner files only (SIXSOURCE ibkr_fx ×3, SANDBOX ×2, SLEEVE-FX5) —
untouched. Heavy lock FREE_PROVEN; scored/diag workers 0. Registry vs
measured worktree HEADs: PC12A `c93123db…` match; EOSV2 `857af951…`
match; both TERMINAL, S1 SEALED_UNTOUCHED, GO phrases DEAD (P-8).
Hygiene (disclosed): PC12A's 2 dirty REPRO-scratch files restored to the
committed snapshot (P-10); root evidence copy retains the investigation
state, explained in TERMINAL_DECISION C-2.

## 2. PC12A — verdict `POLICY_NO_INCREMENTAL_VALUE`, harm quantified [M]

Source artifacts: `…/PORTFOLIO-COMPOSITE-12ASSETS-100K-V1/diagnostics/stagec/ARMS/{POLICY,B1_ALWAYS_ON}/{metrics.json,journal.jsonl}`
(root evidence landing; identical bytes in worktree branch).

### 2.1 Per-fold (8 pooled test folds, tier ×1.0) [M]

| fold | window | POLICY net | B1 net | harm | POLICY DD | B1 DD | POLICY fills | B1 fills |
|---|---|---|---|---|---|---|---|---|
| 0 | 2022-01→07 | +541,483.96 | +541,483.96 | **0.00 (identical)** | 64,855 | 64,855 | 390 | 390 |
| 1 | 2022-07→12 | −149,566.12 | −66,163.14 | −83,402.98 | 350,066 | 248,114 | 299 | 311 |
| 2 | 2023-01→06 | +21,675.53 | +230,503.03 | −208,827.50 | 119,138 | 26,081 | 298 | 273 |
| 3 | 2023-07→12 | −78,294.18 | −75,194.21 | −3,099.97 | 139,346 | 201,355 | 301 | 271 |
| 4 | 2024-01→06 | +210,424.95 | +98,896.82 | +111,528.13 | 183,020 | 202,507 | 294 | 288 |
| 5 | 2024-07→12 | +73,626.69 | −100,565.72 | +174,192.41 | 136,979 | 172,694 | 271 | 298 |
| 6 | 2025-01→06 | −231,109.36 | −151,850.06 | −79,259.30 | 306,777 | 186,610 | 290 | 294 |
| 7 | 2025-07→12 | +215,099.14 | +211,493.34 | +3,605.80 | 63,388 | 20,139 | 293 | 238 |
| **Σ** | | **+603,340.60** | **+688,604.03** | **−85,263.43** | 418,228 | 397,157 | 2,436 | 2,363 |

Fold arithmetic reconciles to the pooled numbers to the cent. Harm is
concentrated in folds 1, 2, 6; the policy HELPED in folds 4–5; fold-0
outcome records are identical (net/DD/fills/cost bill; identical 389
NET_ORDER rows; the journals differ only in SWAP-row bookkeeping and
header) — the policy was effectively always-on there.

### 2.2 By asset [M: metrics.json `per_symbol_fold_records`]

| symbol | POLICY net | B1 net | harm | POLICY costs | B1 costs |
|---|---|---|---|---|---|
| USDJPY | +600,082.92 | +687,284.31 | **−87,201.39** | 128,073 | 106,651 |
| EURUSD | +2,315.24 | +600.97 | +1,714.26 | 826 | 1,390 |
| GBPUSD | +942.44 | +718.75 | +223.70 | 591 | 615 |

The ENTIRE net harm is USDJPY, and the policy also paid $21.4k MORE costs
there while trading a different size path. Per-LEG PnL on test folds is
**[NR]**: legs are netted per-asset (L4), so per-leg PnL separation
requires an attribution assumption — only per-leg ACTIVITY is measured:
decisions USDJPY-S026 1,891 · GBPUSD-S002 490 · USDJPY-S014 288 ·
EURUSD-S013 238 · EURUSD-S046 94 · GBPUSD-S017 56 · VC2-LVNFAIL-EUR 30 ·
VC2-LVNFAIL-JPY 20 · USDJPY-S003 10 · USDJPY-S002 4 · EURUSD-S009 3.

### 2.3 Measured harm mechanisms (representative journal events) [M]

Loss-reason typing status first: the JOURNAL_SCHEMA §3 LOSS_* taxonomy
tags were **[NR]** — never computed in the scored run. The examples below
use the journals' own outcome rows; no reason is guessed.

- **(a) Cost-guard deferral observed — rows verbatim; at this citation
  the outcome is NOT a missed profit.** Week ending 2023-05-19 (fold 2):
  `USDJPY-S026` DEFER ×4, e.g. 2023-05-16T16:00Z, eligibility ON,
  `blocked_reason_detail: "L6 cost guard: trailing 28d spend 2852.3954 >=
  cap 2836.97"`, PIT-at-entry feature `decision_count_trailing: 503`
  (POLICY journal DEFER rows). Skeptic F-1 correction: B1's corresponding
  05-16 17:00→18:00 round trip closed **−$2,190.70** and POLICY itself
  took B1's 05-18/05-19 fills — the guard deferred a round trip that
  LOST in B1 at this citation; the week's −$49.9k divergence (inside the
  fold-2 −$208.8k gap) is dominated by the size/path divergence of (b),
  not by the guard. (Docket A measures the guard's full-window effect
  separately: the 29 cost-guard defers B1 actually filled netted
  +$274,572 — the guard's deferrals were net HARMFUL across the window;
  see symbol_docket/USDJPY_DOCKET.md §6.) No counterfactual on any
  single deferral is claimed.
- **(b) Netting/size divergence, not gating — MEASURED.** Worst single
  week (ending 2024-11-08, divergence −$114,238): the trading legs were
  all-ON (9× S026 ON, 4× S014 ON, no BLOCK/DEFER on either); 5 BLOCK rows
  on dormant legs (S002/S003/VC2-EUR) contributed −$113.14 of the week's
  −$114,238; positions differed in
  SIZE (policy −19,384/+10,000 units vs B1's −4,684/−10,000/+22,591
  mixes). The supermajority-netting/caps layer produced a different size
  path than always-on vote aggregation on the same votes.
- **(c) Drawdown deepening — MEASURED.** Policy DD exceeded B1 by
  +$102.0k (fold 1) and +$120.2k (fold 6) on the same USDJPY path
  (pooled per-fold DDs, §2.1), and fold-7 DD $63.4k vs $20.1k.

**Measured vs conjectured:** (a)–(c) are measured mechanisms. NOT
established anywhere in this packet: that any different on/off pattern
would have improved the result — no counterfactual policy search was run
and none may be (no tuning, folds are burned). The B4 battery already
measured that 128/128 duty-matched random eligibility patterns beat the
frozen policy's objective [M: B4_BATTERY.json].

## 3. EOSV2 — verdict `NO_INCREMENTAL_VALUE` [M]

STOP-1 8/8 cells; G3 wall fails 4/4 (best B2 +403,801.90 vs
BASE_ALWAYS_ON_LONG +1,653,470.33; margin −1,249,668.43); G10 fails 4/4
(all below TREND_LF +472,864.82); G5 fails B1/B2/B4; references
reproduce V1 terminal numbers **28/28 values to the cent, every tier and
fold** [M: scored/scored_summary.json vs V1 terminal] — so the death is
attributable to the mechanism, not measurement. G8 repro twin ALL_MATCH
(sole divergence `built_utc`, root-caused); G9 A7 terminal
CONFIRM_WITH_CONDITIONS 0C/0H — the r1 remediation adjudicated lawful
(pure crash-guard `g.get('all_pass')`, zero outcome exposure proven
structurally + by the lock-history FAILED-release stderr). Residual
disclosure: state.json `phase` still reads P4 (cosmetic; close
authorities correct).

## 4. The seven-deaths statement — exact ancestry [M]

v1's "seventh consecutive death of the gating/overlay/coordination
pattern" is correct ONLY with this exact enumeration (each a measured
terminal on its own evidence): 1. JEV-REGIME-ROUTER-V2
(`JEV_NO_INCREMENTAL_VALUE`); 2. REGIME-STRATEGY-MAPPING-V1
(`NO_REGIME_STRATEGY_INCREMENTAL_VALUE`); 3. PHASE-STRATEGY-V1
(`PHASE_STRATEGY_V1_NO_INCREMENTAL_VALUE`); 4.
PORTFOLIO-ROUTER-12ASSETS-100K-V1 (`ROUTER_STATES_THIN` — pre-PnL state
kill); 5. BTC-COMBO6-SCORED-V1 (`COMBO6_NO_INCREMENTAL_VALUE` — fixed
6-leg combo); 6. PC12A (`POLICY_NO_INCREMENTAL_VALUE` — risk-only policy
over diagnostic legs); 7. EOSV2 (`NO_INCREMENTAL_VALUE` — breadth
gates). REGIME-GATED-COMBO-V1 is EXCLUDED (not terminal; owner a/b
pending). Narrower wording: "seven measured terminals across four
router/gating attempts, one fixed combo, one risk-policy and one
breadth-gate program on this workspace's calendars."

## 5. Ranked lawful next-research paths from the existing corpus

Calendar law first: the 5-pair M1/H1 calendar is **BURNED** for new
scored claims (8 test folds' outcomes seen; sealed 26w tail = 1 fold <
the 6-fold floor); ONLY genuinely fresh data opens new validation.

| rank | path | mechanism hypothesis [H] | blockers | budget (draft) | baselines | validation calendar | scoreable now? |
|---|---|---|---|---|---|---|---|
| 1 | **Daily-cohort cycle** on the 4 probe pairs (NZDUSD, USDCHF, XAUUSD, XAGUSD; identity frozen, 7 named candidates §6) | the 7 candidates' corpus mechanisms at daily clock on never-scored panels | (i) HMDS daily **PIT-lag measurement** (currently ASSUMED next-business-day); (ii) plan amendment; (iii) XAU basis thresholds frozen; (iv) commission/swap still DECLARED | ~24–32 cells | B0/B1 always-on wall/B2/B3/B4 battery + the seven-deaths prior priced in | FRESH: 2020-10→2026-09 daily panels, own 8×fold split, untouched | NO — blocked on (i)–(iii); everything else is staged (IDENTITY_FREEZE_2026-09-30.json) |
| 2 | **TB-LABELS** (analysis-only) on existing TRAIN data | none claimed — labels for loss forensics | none (TRAIN-side, no test-fold use, firewall per design §2a) | 0 scored cells (not a claim) | n/a | TRAIN only | YES as diagnostics; makes NO claim |
| 3 | **TB-EXIT-OVERLAY** as new identity | barrier exits beat signal-exits on mean-rev/session families | FRESH calendar required (rank-1 data or future-accumulated M1); on the burned calendar it is unlawful | 57 rows already registered in the TB design | original-exit control + B-family | fresh panels only | NO — no lawful folds exist today |
| 4 | EOSV2 tranche V3 | new tuples attack the ALWAYS_ON wall's regime dependence | owner must NAME the new data/tuples; walls are structural (G3 margins ~−1.25M) | per new cycle | V1/V2 reference walls | depends on owner's data | NO |
| 5 | "Always-on carry book" as its own question | [H] the P1-B0/B1 positive is carry, persists on new data | NOT evidence today (see §7-corr-1); would be tested INSIDE rank-1's baseline battery, not its own cycle | inside rank 1 | rank-1 battery | rank-1 calendar | NO |

## 6. The 7 daily candidates — exact rows and status [M]

Source: `…/ibkr_capability_probe_2026-09-30/LEG_RESOLUTION_MATRIX.tsv`
(columns gid, symbol, family, horizon, tier, label, class, probe_assets,
note; rows quoted verbatim) + IDENTITY_FREEZE_2026-09-30.json + Lane DV
verification (all 131 raw hashes, spans, spreads reproduced).

| # | gid | row (verbatim fields) | unlocks | PIT/price/cost status |
|---|---|---|---|---|
| 1 | AUDUSD-S081 | AUDUSD · T3_PARK · PRIOR_NOT_SCORED · NEW-DAILY-CANDIDATE | NZDUSD | daily BID/ASK span PASS (2020-10-02→2026-09-30, 0 holes >5d); interior gaps NOT_RUN; M1 NOT_RUN_SIZE_CAP; costs: spreads daily p50 0.88bps measured, commission/swap DECLARED-unmeasured |
| 2 | USDJPY-S063 | USDJPY · G-XASSET · T3_PARK · PRIOR_NOT_SCORED · NEW-DAILY-CANDIDATE | XAUUSD | note: "gold D1 + VIX (evidenced) + USDJPY D1; gold was the unevidenced series" — now daily-evidenced; XAU basis vs archive measured (abs p50 3.25bps) but acceptance thresholds UNFROZEN; PIT lag ASSUMED |
| 3 | AUDUSD-S100 | AUDUSD · J-REGIME_OPT · T3_PARK · FAMILY_HISTORY_NEGATIVE · NEW-DAILY-CANDIDATE | XAUUSD | note: crisis-alpha switch, VIX(>30) already evidenced; same XAU status as #2 |
| 4 | USDJPY-S083 | USDJPY · T3_PARK · FAMILY_HISTORY_NEGATIVE · NEW-DAILY-CANDIDATE | NZDUSD; USDCHF | as #1; USDCHF spreads p50 4.51bps |
| 5 | EURUSD-S006 | EURUSD · T3_PARK · FAMILY_HISTORY_NEGATIVE · NEW-DAILY-CANDIDATE | USDCHF;NZDUSD | as #1 |
| 6 | EURUSD-S061 | EURUSD · T3_PARK · FAMILY_HISTORY_NEGATIVE · NEW-DAILY-CANDIDATE | USDCHF;NZDUSD | as #1 |
| 7 | EURUSD-S085 | EURUSD · T3_PARK · FAMILY_HISTORY_NEGATIVE · NEW-DAILY-CANDIDATE | USDCHF;NZDUSD | as #1 |

XAGUSD: identity frozen, **zero candidates**. All 7 remain **BLOCKED
pending plan amendment** — daily price existence raises nothing
automatically. TB design (path 3): `…/PORTFOLIO-COMPOSITE-12ASSETS-100K-V1/triple_barrier/INVENTORY_AND_DESIGN.md`
— inventory 76 configs (exit classes + check bases cited file:line
within), TB-LABELS firewall §2a, overlay grid 18 nodes/family, 57-row
budget, SL-first ambiguous law, applicability exclusions (trend/VOLPROF).

## 7. Corrections to v1 (self-audit, owner-directed)

- **corr-1 (P1-B0 overclaim).** v1: "the legs' raw carry was real".
  Corrected: P1-B0 PASS means **positive pooled net under
  DECLARED-pessimistic costs for THIS selected set on these 8 folds** —
  it is NOT proof of real edge: (a) commission/swap/slippage are
  unmeasured (PROVISIONAL_PENDING_COST_AUTHORITY; every pair carries
  NET_DEFAULT_COST); (b) the 150→62→12 selection pipeline overlapped the
  same corpus and the deflated view REJECTS it (DSR 0.0002, P5a); (c) it
  is a baseline sub-bar, not an edge claim. Status: [M] number, [H] any
  persistence claim.
- **corr-2 (adjudication overclaim).** v1: "the 1,200-idea program is
  now fully adjudicated". Corrected: the AMENDED question was answered
  for the cohorts that could lawfully run — 294 screened, 150
  triage-runnable, 62 diagnosed, 12 scored. The **128 STILL-NOT_RUN +
  9 FUTURES-BLOCKED + ceiling/PIT-blocked cohorts remain UNADJUDICATED**
  pending data unblocks; the corpus is not "closed" beyond what ran.
- **corr-3 (P8 wording).** TERMINAL_DECISION.md (and SESSION_REPORT): "7/12 leave-one-leg removals break".
  Corrected: P8 was IMPLEMENTED as single-leg isolation pairs (A7 H-1,
  `run_scoredc.py:384-385`); **7/12 ISOLATION re-runs fail P1-semantics;
  the without-leg-i complement reading was never run** [NR]. Both
  readings yield FAIL with the same close code; the verdict is
  unchanged either way (P1 types the close regardless).
- **corr-4 (seven-deaths).** Now stated with exact ancestry (§4) and
  narrower wording; RGC-V1 excluded.

## 8. Decision menu (each ONE owner action; nothing runs before it)

- **D-A EOSV2 §8**: A1-recommended END (two structural walls, cent-exact
  reproduction) / V3 with owner-named tuples / redirection.
- **D-B PC12A axis (REVISED by owner steering 2026-10-01 — supersedes
  v1/v2's "accept-and-close as the only next step")**: the desired path
  is deep historical-trade study per symbol → falsifiable on/off
  hypotheses → a preregistered successor cycle validated on a genuinely
  fresh future calendar. Section 11 (SYMBOL RESEARCH DOCKET) and §12
  (successor protocol sketch) implement this; the v1 "accept/close"
  option survives only as the null action if the owner rejects every
  docket hypothesis.
- **D-C cross-cutting**: RGC-V1 a/b (recommend close (a) at 0 cells);
  stale heartbeats EVENT-MECHANISMS-V1 (hb 2026-09-27) and
  CRYPTO-HISTORICAL-REPLICATION-3F-V1 (hb 2026-09-23) — resume-and-check
  or formal pause; IBKR statement (optional, upgrades DECLARED→measured);
  SLEEVE-FX5 D1/D2 packet.

## 9. Why a root-main commit of this review conforms to AGENTS.md

AGENTS.md: "Root checkout = bootstrap/owner space" and "A1 is the sole
integration, merge, central-ledger and publication authority"
(CLAUDE.md §Repository invariants). This packet is A1 integration output
in the owner space — the same surface where every cycle's session
reports, close artifacts and registry control-plane commits land by A1
(precedents on main: PR12A closes, BTC-COMBO6 two-half close (root half `659f76e2`, lane half `6f9dfd52`),
this week's PC12A/EOSV2 closes, v1 of this packet `fc26adf1`). Lane
research code never touches main; nothing here is pushed (push is
forbidden workspace-wide); staging is pathspec-only and the owner's
dirty tree is untouched. No further repo writes occur after this commit
until the owner verifies (this session's only write is this file).

## 10. Boundaries held

Preparation only: 0 scored cells, 0 S1 reads, 0 orders/paper/live, 0
registrations, 0 registry hand-edits, no reuse of either cycle's
dead budget. GO phrases DEAD. Single file-level actions: the disclosed
REPRO-scratch restore (§1) and this file.

## 11. SYMBOL RESEARCH DOCKET (owner steering 2026-10-01; all analysis of EXISTING backtests only — hypothesis-generating, never fresh validation)

Three fresh-context lanes reconstructed trades from the committed scored
journals (POLICY + B1) and TRAIN diagnostics; every file carries
hypothesis-generating-only headers and fold provenance.

### 11.0 Inference capability across the 12 assets [M: docket C]

**3 of 12 support trade-level inference today** (EURUSD, GBPUSD, USDJPY —
all 12 scored legs sit there). USDCAD/AUDUSD: TRAIN-only
hypothesis-generating (all 9 diagnosed H1 legs died COST_DOMINATED at
×2.0 fold 7 — zero floor kills; at ×1.0 only USDCAD-S011 +$111.72 and
S091 +$313.61 were net-positive, both flipping at ×2.0; C2 structural
absence + Sunday-deferral asymmetry: AUDUSD defers 87/286 Fridays at
2.2× USDCAD's rate). The 7 blocked assets (NZDUSD, USDCHF, XAUUSD,
XAGUSD, BRENT, WTI, NATGAS): no admissible panel; every unlock action is
OWNER-ONLY (statement export / PIT declaration+threshold freeze /
futures chain-source naming); XAU's overlap is measured (1,531 days, abs
basis p50 3.25bps) but PIT lag remains ASSUMED.

### 11.1 USDJPY (docket A — the whole −$87.2k harm) [M]

703 flat-to-flat excursions reconstructed (POLICY 393, B1 310) with exact
reconciliation (Σnet = journal symbol nets to the cent; friction =
metrics cost bill; 4/5 force-flats identified). Findings: losers
outnumber winners every fold (387 vs 292 beyond ±$239.54 friction) but
winner gross is 1.34× loser gross; winners hold 24h vs losers 7h; S026
is the workhorse (+825k/+822k attributed), S014 meanrev persistently
negative (−222k/−320k; RSI2_MID_CROSS family −470k); decision-density
does NOT separate winners/losers (δ=0.028 — honest null); **NY-session
long entries are the only sign-consistent negative bucket in BOTH arms**
(POLICY −281k n=91 across all 8 folds; B1 −84k n=74). Rule tests both
sides: blocking NY longs is the ONLY PnL- and DD-consistent off-rule
(+281k avoided, DD −412k→−360k); the cost guard's 29 defers B1 filled
netted +$274.6k (guard HARMFUL window-wide — correcting packet §2.3(a));
E-floor blocked legs were worth +$428.7k paper/+187.1k realized in B1.

### 11.2 EURUSD + GBPUSD (docket B) [M]

Reconciled to ≤$1 on all 32 arm×symbol×fold cells. EURUSD: harm +$1.7k ≈
neutral — the E1 activity floor SUPPRESSED the bleeding S009
(always-on −$587.8, floor avoided ~$504) while B1's fold-6 long-carry
through the 2025 rally cost −1,696 vs −134; swap dominates costs (65%).
GBPUSD: S017 bleeds (20 SL : 6 TP; 15/28 stop out within 1 minute —
retire candidate); S002's entire edge is "survive to 16:00" (TIME exits
+$3,853 vs ±2-pip stops −$2,865 at 27% stop rate).

### 11.3 The falsifiable on/off hypotheses (12 total across dockets, ranked by MECHANISTIC plausibility not exposed PnL)

Top-ranked per docket (full trigger/rationale/predicted-benefit/failure-
condition/sample-floor text in the docket files):
1. **H-J1 block USDJPY NY-session long entries** (docket A) — the only
   rule consistent on both arms and both quantities; mechanism: Tokyo-fix
   cycle timing vs NY liquidity.
2. **H-E1 codify the E1 activity floor for signal-exit-only legs**
   (docket B) — the floor was the policy's one measured WIN (S009).
3. **H-G1 retire/admit-gate GBPUSD-S017** (1-minute stop-out signature).
4. **H-E2 EURUSD 12:00/16:00 entry gate** (suppressed net-negative on
   both arms, halves pair DD).
5. **H-J2 re-tune-or-remove the L6 cost guard** (its deferrals were
   window-wise harmful, +$274.6k foregone).
6. **H-J3 USDJPY meanrev family off-switch** (S014 class negative on
   both arms).
Plus 6 further hypotheses (dockets A/B/C) including H1-pair
spread-cell/swap-drag/deferral-asymmetry tests gated on future panel
upgrades. NO hypothesis is validated by these numbers — they only
justify preregistration.

## 12. Successor protocol sketch (for the owner packet; nothing runs without a new cycle + GO)

1. **Preregistration**: hypotheses + thresholds-grid (bounded, e.g.
   ≤24 nodes total) + trial budget (e.g. ≤40 rows) + controls (dwell-
   matched random, clock-shadow, sign-inversion) frozen BEFORE any
   testing; ranked by mechanistic plausibility, never by exposed PnL.
2. **Threshold learning**: earlier TRAIN folds only (fold k trains on
   < fold-k start − embargo); no test-fold contact.
3. **Validation calendar**: genuinely NEW, non-overlapping with
   2021-01→2025-12 (fresh daily-cohort panels and/or future-accumulated
   M1 from the live collectors); ≥6×26w folds or NOT_RUN. The exposed
   folds can never be relabeled as validation.
4. **Costs**: measured where owned (spreads C1-C3), DECLARED bands
   elsewhere with PROVISIONAL labels; IBKR statement remains the
   measured-cost unlock. **Journaling**: every trade and blocked signal
   per journal_row@1 (already proven); MAE/MFE + per-leg attribution
   added to the successor engine (docket [NR] items).
5. **Symbol-specific rules + cross-symbol caps**: per-asset on/off maps
   (no single regime rule); L4/L5 netting+cluster caps retained from
   PC12A's architecture; conflicts resolved by the frozen netting law.
6. **Acceptance**: PASS_BARS_V2 AND-semantics (net ↑ AND DD ↓ vs the
   named baselines incl. always-on) on the fresh calendar only.
