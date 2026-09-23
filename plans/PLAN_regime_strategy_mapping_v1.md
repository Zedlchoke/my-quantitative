# PLAN REGIME-STRATEGY-MAPPING-V1 — regime-specialist mapping + switching-cost attrition reduction

> Status: `PLANNED_NOT_STARTED`. Owner instruction 2026-09-23 (successor cycle after
> JEV-REGIME-ROUTER-V2 closed TERMINAL `JEV_NO_INCREMENTAL_VALUE`).
> S0 discovery research ONLY. This is NOT a JEV-V2 rescue: no Jev API call is
> made in this cycle, no V2 artifact is mutated, no Jev label / prompt /
> confidence / persistence / regime threshold is changed after the fact.
> No paper/live/orders. S1 `SEALED_UNTOUCHED`.

## 0. Cycle identity

```text
cycle_id     REGIME-STRATEGY-MAPPING-V1
class        S0 DISCOVERY (outcome-observed corpus; see §7 contamination law)
question     Does a per-regime SPECIALIST strategy mapping — chosen by a frozen
             nested walk-forward law from a bounded (≤2/regime) economically
             motivated library, executed under a frozen anti-churn turnover
             law — beat (a) simple always-on baselines and (b) the original V2
             mapping, after costs, on the already-observed V2 corpus? And how
             much of V2's loss was mechanism (strategy) vs attrition
             (costs/churn)?
inputs       V2 frozen corpus, read-only: cached Jev decisions
             (runtime/replay/{cell}/decisions_*.jsonl in the V2 worktree),
             V2 trade ledgers (runtime/scored/...), V2 freeze contracts, and
             the same frozen data snapshots (BTCUSDT 15m catalog parquet
             sha256 81d4f147…; SPY snapshot sha256 3fd229f9…).
jev_calls    ZERO. Effective/persisted regime timelines are RECOMPUTED
             deterministically from the cached decisions by the V2 frozen
             safety/persistence code (0.50/0.20/confirm 2/dwell 6/cooldown 3),
             never re-asked.
budget       21 scored cells = 3 cells (BTC_H1, BTC_H4, SPY_D1) x 7 arm
             instances (A1, A2, B, C, D, E, F; §4). FLAT and buy-and-hold are
             reference metrics, not scored arms. Phase-1 attribution and
             Phase-2 feasibility are diagnostic, NOT scored trials.
s1           SEALED_UNTOUCHED (every asset)
orders       NONE (no broker/paper/testnet/live surface)
go_phrase    GO REGIME STRATEGY MAPPING V1 DISCOVERY BACKTEST   (STOP-1 gate)
predecessor  JEV-REGIME-ROUTER-V2 TERMINAL `JEV_NO_INCREMENTAL_VALUE`
             (commit authority 0c277a94 on orca/jev-regime-router-v2-integration;
             A7 terminal `TERMINAL_VERDICT_AUTHORIZED_JEV_NO_INCREMENTAL_VALUE`,
             0 HIGH/CRITICAL). V2 artifacts are append-only evidence: read-only.
forbidden    research/control/SANDBOX-OVERFIT-3ASSETS/ (never read); Jev API of
             any kind; S1; mutating any V2 artifact; parameter choice on the
             full history presented as validation; unlimited strategy search;
             large strategy grids; BTC H1-vs-H4 selection by PnL; using SPY
             ALWAYS_ON_TREND +19,813 as evidence of edge (concentration 0.69 >
             0.50 kill — it stays a posterior baseline); EURUSD (remains
             BLOCKED_SOURCE_LICENSE).
```

## 1. Predecessor intake law (re-measured before this plan freezes anything)

All anchors re-measured on disk 2026-09-23 and must hold at every phase gate;
any drift ⇒ STOP and disclose before proceeding:

1. Registry: `JEV-REGIME-ROUTER-V2` lifecycle TERMINAL, head `0c277a94`,
   branch `orca/jev-regime-router-v2-integration`, clean tree.
2. Terminal verdict `JEV_NO_INCREMENTAL_VALUE`; A7 terminal verdict
   `TERMINAL_VERDICT_AUTHORIZED_JEV_NO_INCREMENTAL_VALUE`; 0 unresolved
   HIGH/CRITICAL (3 LOW + 4 INFO, none blocking).
3. JEV_ONLY net-negative on BTC_H1 (−88,140) / BTC_H4 (−85,274) / SPY_D1
   (−51,623); fold nets negative 11/12 (only SPY fold-2 positive, +4,985);
   loses to ALWAYS_ON_MEAN_REVERSION on all three cells.
4. SPY ALWAYS_ON_TREND +19,813 is a BASELINE with concentration 0.6876 >
   0.50 kill — reported, never promoted, never citable as edge.
5. V2 RANDOM_MATCHED null `null_invalid` on all 9 cell×tier combos (Q-11);
   conclusions there never rested on it alone; this cycle's shuffled control
   must not repeat that weakness silently (§4.F).
6. S1 sealed; no V2 paper/live/order anywhere.
7. V2 usage law (unchanged): the only permitted use of V1/V2 observations is
   naming failure classes and justifying THIS design change. No V1/V2
   threshold, prompt, bin or mapping may be tuned against labels.

## 2. Phases

```text
P0   plan -> researchctl register -> integration worktree/branch
     (.worktrees/regime-strategy-mapping-v1/integration,
      orca/regime-strategy-mapping-v1-integration). Root checkout is never
      the implementation lane.
P1   MECHANISM ATTRIBUTION AUDIT (diagnostic, outcome-observed, no candidate
     selection) — §3. Reads V2 ledgers + recomputed regime timelines only.
P2   REGIME SAMPLE FEASIBILITY (no PnL at all) — §4.0 sample floors.
P3   SPECIALIST LIBRARY FREEZE (≤2/regime, economic rationale) + nested
     selection law freeze — §5.
P4   ARMS + CONTROLS FREEZE (A1,A2,B,C,D,E,F) — §4.
P5   TURNOVER LAW FREEZE — §6.
P6   CONTAMINATION LAW — §7 (no new computation; disclosure baked into every
     artifact).
P7   A7 PRE-OUTCOME AUDIT (fresh-context) — §10.1.
STOP-1 OWNER GATE — §11. WAIT for exact phrase
     `GO REGIME STRATEGY MAPPING V1 DISCOVERY BACKTEST`.
P8   scored discovery run under heavy lock, full denominator, reproduction,
     A7 terminal fresh-context, verdict — §12/§13.
```

Freeze order law: P3–P5 freeze files land BEFORE any candidate PnL is
computed by this cycle. P1 (V2 PnL already observed) and P2 (no PnL) precede
them by design: P1 locates the failure mechanism, P2 sizes the sample; the
specialist library is justified by economic reasoning + P1 mechanism findings
(not by scanning candidate strategies' PnL on this history — that is what the
nested law in §5 exists to prevent).

## 3. Phase 1 — V2 mechanism attribution audit (diagnostic only)

Outcome-observed diagnostic on the V2 corpus; NOT a scored validation; its
counterfactuals locate the failure mechanism and NOTHING chosen here is
"validated". For each cell BTC_H1 / BTC_H4 / SPY_D1, from the V2 tier-1
trade ledgers and the recomputed effective/persisted regime timeline:

1. Gross PnL before costs; fee, slippage and funding separately; net PnL.
2. PnL inside stable-regime windows vs windows around regime transitions
   (±1/2/3 regime bars around each persisted switch).
3. PnL by persisted regime (bar-level equity-delta attribution; trades
   attributed to the regime active at entry; both reported).
4. Counts: entries, exits, reversals (direction-flip fills), no-op target
   updates (label changed, target direction unchanged).
5. Turnover and holding time (per trade and per regime).
6. Cost attribution, each fill tagged with exactly one cause:
   `strategy_native` (specialist's own signal), `regime_switch` (position
   changed because the persisted label changed), `fold_force_flat`,
   `unnecessary_close_reopen` (closed and reopened the SAME direction with no
   strategy-native reason).
7. Counterfactuals (ledger-level replays, diagnostic only):
   a. hold-position-when-target-direction-unchanged (no-op law);
   b. transition buffer of 1/2/3 regime bars before honoring a switch;
   c. minimum hold of 2/4/8 regime bars;
   d. JEV risk-off veto only (base always-on, flat in DISTRIBUTION/DOWNTREND).
   None of (a)–(d) may be selected as "the winner" from this phase; they only
   quantify attrition mechanisms for the P3–P5 freezes.

Deliverables: `MECHANISM_ATTRIBUTION_REPORT.md` + machine-readable JSON +
exact reconciliation to the V2 ledgers (per-arm gross/fee/slip/funding/net
and trade counts must equal V2 `runtime/scored/{cell}/{arm}/tier_1.json`
totals to <1e-6; every check PASS/FAIL/NOT_RUN).

## 4. Phase 2 + arms — sample floors, arms, controls

### 4.0 Sample feasibility (measured BEFORE any specialist PnL; no PnL here)

Per cell × persisted regime (ACCUMULATION / UPTREND / DISTRIBUTION /
DOWNTREND / TRANSITION_UNKNOWN):

- decision count; independent episode count (maximal contiguous persisted
  runs); episode duration distribution (min/median/max/quartiles); episodes
  per outer fold; transition count; eligible entries (episodes long enough
  to admit an entry under the specialist's frozen min conditions); market
  time in bars; margin-to-sample-floor (min over floors).

Preregistered sample floors (owner-proposed; A7 may adjust BEFORE outcome
with rationale recorded in the freeze):

- ≥ 20 independent episodes/regime/cell (total);
- ≥ 3 episodes/regime/outer-fold;
- ≥ 100 eligible decisions/regime/outer-fold;
- below floor ⇒ that regime×cell scores `NOT_RUN_THIN_REGIME` and its
  specialist selection defaults to FLAT (the router still runs; the thin
  regime contributes no specialist risk);
- BTC_H1, BTC_H4 and SPY_D1 are NEVER pooled to fake sample size.

### Arms (frozen before any candidate PnL; 21 scored cells)

| ID | Arm | Role |
|---|---|---|
| A1 | ALWAYS_ON_SIMPLE_BASELINE (mean-reversion) | reference: no regime info |
| A2 | ALWAYS_ON_SIMPLE_BASELINE (trend-long) | reference: no regime info |
| B | ORIGINAL_V2_MAPPING_REFERENCE | V2 frozen mapping on cached regimes, V2 mechanics (engine-equivalence: must reconcile to V2 JEV_ONLY tier-1 within <1e-6 before any C outcome) |
| C | REGIME_SPECIALIST_ROUTER | THE candidate: cached persisted regime → nested-law-selected specialist (§5) under the turnover law (§6) |
| D | SPARSE_JEV_RISK_OFF_VETO | control: always-on base (BTC: A1; SPY: A2 — economically motivated, disclosed as aligned with V2's per-cell stronger always-on; controls may be outcome-informed, candidates never), flat while persisted regime ∈ {DISTRIBUTION, DOWNTREND}, turnover law active |
| E | DETERMINISTIC_PROPOSAL_PLUS_JEV_VETO | control: V2 deterministic law proposes; Jev effective regime may only veto (disagree → flat); turnover law active (isolates churn-law value on the V2 CONFIRM design) |
| F | EPISODE_SHUFFLED_MATCHED_CONTROL | null: 21 seeded segment-permutations matched to arm C's occupancy (±2pp) / switches (±10%) / dwell (±10%) / invested (±2pp); Q-11 movement validation MANDATORY; invalid ⇒ `NOT_RUN_CONTROL_MATCHING` — never conclude from a broken null |

Mandatory for every arm: same occupancy/switching control where applicable
(arm F); cost tiers 1.0x/1.5x/2.0x; fold force-flat; trade/fill/PnL
reconciliation identity; no-lookahead mutation tests; regime lag ≥ 1
executable bar (decision at bar close, fill next executable open); no
strategy change between bars after outcome becomes visible.

### Cells and folds

Identical to the V2 frozen fold contract (4 contiguous folds per cell, same
boundaries, same warmup 192 regime bars, same floors; BTC_H1 and BTC_H4
INDEPENDENT cells; no H1-vs-H4 selection by PnL; SPY_D1 long-only).

### Costs

Identical to the V2 frozen contract: BTC taker 5 bps/side + slippage 1
bps/side (6 bps/side; 12 round-trip), funding 1.377e-5/8h signed; SPY
10 bps/fill long-only; stress 2.0x; sweep 1.0/1.5/2.0. Zero-cost variants
are computed for diagnosis only and can never support a PASS.

## 5. Phase 3 — frozen specialist library + nested selection law

Bounded library, ≤ 2 specialists per regime, chosen for ECONOMIC reasons
(who is forced to act / react in each phase), never from scanning PnL.
No 2^4 mapping grid: the selection law picks per regime independently.

| Regime | Specialist (frozen ID) | Economic rationale (short) |
|---|---|---|
| ACCUMULATION | `ACC_RANGE_MR` — slow range mean-reversion long/flat | post-decline base: liquidity providers fade deviations inside the range; slow cadence to keep turnover low |
| ACCUMULATION | `ACC_FLAT_BREAKOUT_WAIT` — FLAT until the regime itself confirms a breakout (transition to UPTREND handled by routing, not by this specialist) | accumulation is only knowable in retrospect; standing aside costs nothing when ranges chop |
| UPTREND | `UP_TREND_SLOW_LONG` — slow trend-long | late/forced sellers + FOMO demand push drift; slow entries avoid paying the churn tax |
| UPTREND | `UP_LONG_RISKOFF_EXIT` — long baseline with risk-off exit (defensive exit to flat on frozen risk triggers) | same drift, but tail-risk-aware: exits early when the trend's precondition breaks |
| DISTRIBUTION | `DIST_FLAT` — FLAT | distribution tops are where longs get handed to late buyers; SPY default FLAT (no naked-short authority) |
| DISTRIBUTION | `DIST_SHORT_BTC` — BTC-only slow short / defensive exit | post-advance markdown risk in BTC is tradeable short; SPY stays FLAT |
| DOWNTREND | `DOWN_SHORT_BTC` — BTC-only slow trend-short | forced liquidations cascade; slow short harvests the cascade without fighting squeezes |
| DOWNTREND | `DOWN_FLAT_RISKOFF` — FLAT / risk-off (SPY default) | equity downside is not shorted without authority; capital preservation stance |
| TRANSITION_UNKNOWN | `UNK_FLAT` — FLAT (not selectable; fixed) | no-information state |

Counter-trend specialists: NOT included — no separate economic hypothesis
was registered for one, and excluding them keeps the library bounded. Adding
one later requires a new plan.

Every specialist freezes: entry/exit rules with exact indicator parameters
and clocks; sizing (fraction 1.0, same as V2); stop; maximum holding;
minimum holding; transition delay; next-bar execution; transaction costs
(§4); funding; no-op target behavior (same direction ⇒ no fill); asset
eligibility (BTC-only shorts; SPY long/flat only); expected failure mode.
Freeze file: `freezes/specialist_library_freeze.json`.

### Nested selection law (frozen before any candidate PnL)

For each cell, each outer fold k ∈ {1..4} (V2 fold boundaries), each regime R
with eligible specialists on that asset:

- inner-train set = folds 1..k−1 (expanding window; walk-forward);
- fold 1 has empty inner ⇒ FLAT for every selectable regime (the law's own
  insufficient-evidence default);
- inner floors (pooled over inner folds): ≥ 5 episodes AND ≥ 150 eligible
  decisions for R; below ⇒ FLAT for R in fold k;
- if exactly one specialist is asset-eligible for R: take it iff inner
  floors met, else FLAT;
- if two are eligible: compute each specialist's inner pooled NET PnL (base
  tier costs) inside R-windows only; pick the higher NET iff (i) strictly
  higher (> 1e-9) and (ii) stable — higher on every inner fold where both
  have ≥ 1 episode when inner folds ≤ 2, else on ≥ 2/3 of such folds; any
  tie, instability, or floor failure ⇒ FLAT;
- tie-break: FLAT > BTC-only-short > long-capable (never needed except on
  exact numeric ties; recorded);
- selection is per regime, per fold, per cell — recomputed only from inner
  folds; the OUTER fold is scored once, never retuned;
- the selection law, these tie-breaks and the §4.0 floors freeze BEFORE any
  candidate PnL exists; A7 may adjust floors pre-outcome only.

## 6. Phase 5 — turnover law (frozen; applies to arms C, D, E)

1. Regime confirmation: the persisted-regime machine (confirm 2 / dwell 6 /
   cooldown 3) is already the first gate — unchanged.
2. Transition buffer: a persisted-regime switch changes the TARGET only
   after 1 further regime bar of confirmation (frozen k=1; the 2/3-bar
   buffers are Phase-1 diagnostics, not selectable here).
3. Minimum dwell of target state: inherited from the persistence machine
   (min_dwell 6); a specialist may impose a LONGER frozen min-hold, never
   shorter.
4. No-op law: target direction == current position direction ⇒ NO fill, even
   if the regime label or specialist identity changed. Specialist parameter
   changes mid-position are forbidden (a specialist switch takes effect only
   at flat or at a direction change).
5. Long→short and short→long: explicit close + open, both costs charged.
6. No close/reopen merely because a label changed while target
   strategy/direction is unchanged (counted as `unnecessary_close_reopen` if
   it ever fires — it must not).
7. Reporting: regime switches and actual position switches are reported
   SEPARATELY in every artifact.
8. Turnover rejection law (frozen before scoring): arm C FAILS the cell if
   its position-switch count ≥ V2 JEV_ONLY trade count on that cell (churn
   law not binding ⇒ the mechanism is not what it claims); and any candidate
   that only survives with zero/absurd costs is FAIL (real costs at 1.0x are
   the minimum gate; §13).

## 7. Phase 6 — contamination law (disclosure, no computation)

The entire V2 history — every price, every cached Jev decision, every V2
outcome — is outcome-observed. Therefore:

- this cycle is S0 discovery; nested walk-forward reduces overfitting but
  does NOT convert observed history into untouched validation;
- the strongest verdict any result can earn is
  `DISCOVERY_CANDIDATE_FOR_PROSPECTIVE_VALIDATION`;
- no promotion to shadow, paper, live or orders — ever, from this cycle;
- the successor validation must be a NEW cycle on prospective/future data or
  a genuinely never-observed time extension;
- S1 remains `SEALED_UNTOUCHED`.

## 8. Data (re-verified, no re-pull)

Same frozen inputs as V2, digests re-verified at freeze: BTCUSDT 15m catalog
parquet sha256 `81d4f147…` (35,039 bars; H1 = 8,759 complete hours; H4 =
2,189 complete buckets, 16 aligned 15m bars each); SPY snapshot sha256
`3fd229f9…` (2,943 sessions, disclosed snapshot semantics). The cached Jev
decisions are consumed read-only from the V2 worktree with per-file sha256
manifests; BTC decisions jsonl + digests recorded in
`freezes/decision_cache_manifest.json`. EURUSD: NOT_RUN
(BLOCKED_SOURCE_LICENSE; separate extension cycle only after a licensed
bid/ask source and EURUSD_DATA_QUALIFIED).

## 9. Implementation + tests

Namespace `rsmv1` under `research/control/regime_strategy_mapping_v1/` in the
cycle worktree. The V2 engine modules (jrv2, at V2 commit `0c277a94`) are
forked read-only as the starting point; all modifications live in rsmv1 and
are covered by tests. Mandatory tests (hand-computed fixtures):

- all V2 golden tests that still apply (no-lookahead mutation; PIT; digest
  echo; sequential replay determinism; fold partition contiguity +
  reconciliation identity + no-span; next-bar fill; cost-once; funding
  signed; S1 denial; broker-surface scan; freeze-digest assertions);
- regime-timeline recomputation determinism (recomputed persisted timeline
  byte-equals the V2-builtin timeline used in V2 metrics: switches 90/31/34,
  occupancy shares, max UNKNOWN runs 6/7/14);
- engine-equivalence: arms A1/A2/B reproduce V2 ALWAYS_ON / JEV_ONLY tier-1
  totals to <1e-6 BEFORE any C outcome is computed;
- no-op law fixture (label change, same direction ⇒ zero fills);
- turnover rejection-law counter; separate regime-switch vs position-switch
  counters;
- nested selection law on synthetic fixtures (inner selection, floors,
  stability, tie → FLAT; fold-1 FLAT);
- sample-floor calculator fixtures; thin-regime → FLAT routing;
- shuffled-control matching + Q-11 movement checks (valid + invalid cases);
- counterfactual replay fixtures for §3.7 (buffer 1/2/3, min-hold, veto);
- cost-tier sweep exactness (1.0/1.5/2.0 multiplication points).

## 10. Gates

### 10.1 A7 pre-outcome (fresh-context, before STOP-1)

Audits: predecessor verdict recorded `JEV_NO_INCREMENTAL_VALUE`; V2 not
mutated (tree + digests); cached labels/decision manifests correct identity;
sample floors sensible; specialist library bounded (≤2/regime, economic
justification present); no combinatorial search; nested selection law as
frozen; contamination disclosure; transaction-cost authority (V2 frozen
costs, tiers); turnover law; trial accounting (21 cells); no-lookahead;
controls (F movement validation; D/E roles); S1 sealed; no broker/order
surface. Verdicts: `AUTHORIZED_FOR_DISCOVERY_STOP` or
`REMEDIATION_REQUIRED`. Zero unresolved HIGH/CRITICAL to reach STOP-1.

### 10.2 STOP-1 (mandatory owner gate)

After plan + freezes + tests + A7-1: STOP. Owner report answers (plain
language): why V2 failed; how much loss was strategy vs costs/churn; which
regimes have sample; which are thin; which specialists froze; total scored
cells/trials; why this cycle is not "JEV rescue"; the exact GO phrase.
Proposed phrase (never self-consumed):
`GO REGIME STRATEGY MAPPING V1 DISCOVERY BACKTEST`.

### 10.3 Scored run (Phase 8, only after valid GO)

One atomic process under the machine-wide heavy lock; full denominator (all
21 cells, all three cells even if early results look bad); no mid-run
stopping on ugly numbers; no mapping/threshold edits after PnL is visible;
independent reproduction (byte-compare tier files); A7 terminal
fresh-context; verdict exactly one of:

```text
DISCOVERY_CANDIDATE_FOR_PROSPECTIVE_VALIDATION
NO_REGIME_STRATEGY_INCREMENTAL_VALUE
BLOCKED_THIN_REGIME_SAMPLE
BLOCKED_COST_OR_CONTROL_AUTHORITY
TECHABORT
```

## 11. Candidate gates (arm C, per cell and overall)

1. net-positive after base (1.0x) costs;
2. not collapsing at 1.5x (net still positive or within a frozen tolerance —
   strictly: net at 1.5x > 0);
3. beats the better of A1/A2 on that cell (net, base tier);
4. beats arm B (original V2 mapping) on that cell;
5. no single-fold dependency (positive in ≥ 3/4 outer folds, or fold nets
   with the best fold removed still > 0);
6. not merely "trades less": beats D (sparse veto) and the F null where F is
   valid — if F invalid (`NOT_RUN_CONTROL_MATCHING`), say so and rest on
   A/B/D/E only;
7. reproduction match (byte-identical tier files);
8. A7 terminal clean (zero unresolved HIGH/CRITICAL).

Even ALL-PASS ⇒ still only `DISCOVERY_CANDIDATE_FOR_PROSPECTIVE_VALIDATION`.
No live-ready/profitable language anywhere. The only forward path proposed
is a prospective-validation successor cycle.

## 12. Boundaries

No push, no merge to main, registry only via researchctl, one heavy worker
machine-wide, never kill foreign processes, S1 sealed, no orders, no
credential leakage, V2/V1 artifacts byte-untouched, root checkout is
bootstrap/owner space; worktrees `.worktrees/regime-strategy-mapping-v1/*`.
Turn-scope law: pre-GO turns may implement, test, run P1/P2 diagnostics and
freezes, and audit — they may NOT run the scored discovery backtest.
