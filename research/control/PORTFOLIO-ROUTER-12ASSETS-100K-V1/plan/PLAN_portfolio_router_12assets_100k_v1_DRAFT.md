# PLAN_portfolio_router_12assets_100k_v1 — DRAFT FOR OWNER (2026-09-28)

**Cycle ID (proposed):** PORTFOLIO-ROUTER-12ASSETS-100K-V1 · **Status: DRAFT,
NOT REGISTERED.** This plan exists pre-GO per owner directive 2026-09-28. The
owner's directive is explicitly NOT a GO phrase for registration, scored
execution or S1. Nothing runs until the owner grants registration and, later, a
fresh typed GO at the cycle's own gate (two-key: A7 first, then owner — P-8).

## 0. Question and honest prior

**Question:** does ONE portfolio coordination policy — macro-state router over
gated sleeves — add after-cost value over a fixed baseline battery on a
simulated $100,000 account trading at most 12 assets (EURUSD GBPUSD USDCAD
USDJPY AUDUSD NZDUSD USDCHF XAUUSD XAGUSD BRENT WTI NATGAS)?

**Honest prior: NEGATIVE.** Four router-class ancestors died on this exact
question shape (JEV-REGIME-ROUTER-V2 `JEV_NO_INCREMENTAL_VALUE`;
REGIME-STRATEGY-MAPPING-V1 `NO_REGIME_STRATEGY_INCREMENTAL_VALUE`;
PHASE-STRATEGY-V1 `PHASE_STRATEGY_V1_NO_INCREMENTAL_VALUE`; REGIME-GATED-COMBO-V1
exposed reading awaiting owner). This cycle earns the right to ask again only
through changed mechanism axes: exogenous published macro PIT states (not LLM
labels, not the traded tape), a 12-asset FX+metals+energy universe with cluster
risk architecture, sleeve-level falsification BEFORE router assembly, and
switching economics as a first-class measurement. If those axes carry nothing,
the expected close is a typed negative at low cost — which is a successful
cycle (Q-16).

## 1. Scope and deliverables mapping (owner's 5 steps)

| Owner step | Artifact (this control dir) | Status |
|---|---|---|
| 1. Census 1.200 + sort + verdicts | `census/CENSUS_1200.tsv` (1,200 rows), `CENSUS_SUMMARY.md`, `shortlist.tsv`, `CENSUS_PROTOCOL.md` (rubric frozen pre-PnL) | DONE (pre-GO) |
| 2. 12-symbol data/cost matrix, vehicle truth, PIT rules | `datacost/DATA_COST_MATRIX.md` (+ `_DRAFT.md`, `PIT_SOURCE_TABLE.md`), `cost/COST_ACCOUNTING_SPEC.md` | DONE (pre-GO) |
| 3. ONE policy: sleeves + state engine + ON/OFF/FLAT + allocation + kill-switches | `router/ROUTER_POLICY_DESIGN_DRAFT.md` (A1-endorsed) | DONE (pre-GO) |
| 4. Router value check design: baselines, nested walk-forward, attribution, DSR/PBO | `router/EVALUATION_PROTOCOL_DRAFT.md` (A1-endorsed) | DONE (design) |
| 5. Plan, outcome-exposure map, trial budget, A7 prereview | this file + `OUTCOME_EXPOSURE_MAP.md` + `TRIAL_BUDGET_FREEZE_DRAFT.md` + `skeptic/A7_PREREVIEW.md` | DONE (pre-GO) |

Post-GO stages (NOT authorized by this plan alone): registration → data/PIT
remediation lanes (owner-gated data decisions) → implementation lanes →
code/data freeze → sanitized dry-run → independent A7 prelaunch → owner GO →
scored cells under heavy lock → reproduction twin → terminal A7 → two-half
close.

## 2. Why we do NOT score 1,200 ideas (owner asked for the reason, in the plan)

1. **Multiple-testing arithmetic:** 1,200 scored configurations at α=0.05
   manufacture ~60 false "edges" before any real one; DSR/PBO over that ledger
   would price every survivor to zero. The trial budget (§6) exists precisely
   so the program's first number is also its most defensible one.
2. **Ancestry law:** 548/1,200 rows (45.7%) are mechanism-class variants of
   already-dead families; scoring them re-runs known deaths under new names —
   forbidden by handbook §14.3 and P-27's F-0 court.
3. **Data law:** only 5/12 symbols have repo price history and only one macro
   series (SOFR/EFFR) has evidenced PIT; 433 PIT_UNPROVEN + 121 BLOCKED_DATA
   rows cannot produce honest books today. Scoring them would require
   fabricating exactly the favorable assumptions the mission bans.
4. **The question is portfolio-level:** the cycle tests the ROUTER's increment
   over baselines, not 1,200 individual PnLs. Sleeves enter only through the
   admission battery (≤10 sleeves initially; `ROUTER_POLICY_DESIGN_DRAFT` §2),
   each backed by census exemplars.

## 3. Data, vehicle and cost authority (binding references)

- Eligibility: `datacost/DATA_COST_MATRIX.md` — **initial executable universe
  = 5 FX pairs; 7/12 symbols FLAT by data authority** (NZDUSD/USDCHF/XAGUSD/
  BRENT/WTI/NATGAS FLAT_BLOCKED_DATA; XAUUSD FLAT_PIT_UNPROVEN). Activation of
  a FLAT column = its named owner data decision + PIT/cost gates, as a plan
  amendment — never a silent assumption.
- Vehicles: FX spot only at registration (6E alternative is a separate
  identity); no PnL mixing across vehicles; prospective data never history.
- Costs: `cost/COST_ACCOUNTING_SPEC.md` — conditional cost kernel, GROSS/NET
  dual books, 18-item UNMEASURED register with pessimistic defaults, stress
  tiers 1.0/1.5/2.0×, owner statement as the unblock.
- PIT: `datacost/PIT_SOURCE_TABLE.md` per-source rules. State variables:
  V1=EFFR Δ63bd (EVIDENCED), V2=VIX 252d percentile (PIT gate via ALFRED
  vintages REQUIRED), V3=Brent−WTI spread percentile (PIT gate REQUIRED). V2/V3
  gate failure ⇒ state engine NOT_RUN — no substitution post-hoc.

## 4. Policy summary (full spec: `router/ROUTER_POLICY_DESIGN_DRAFT.md`)

- Sleeves (≤2 families/cluster, ≤10 total; FLAT default; J-family excluded):
  admission = census DISTINCT/exemplar → F-0 mechanism court → PIT battery →
  measured ×2.0 after-cost bill on TRAIN → sample floors. Losing sleeves are
  never rescued by loss-segment gates (structural: router thresholds are
  functions of macro series only).
- State engine: 3 PIT variables (V1/V2/V3), 4 states via frozen priority
  ladder (WAR_ENERGY > RISK_STRESS > TIGHTENING > EASING) + ABSTAIN ⇒ FLAT.
  Weekly clock Friday 17:00 ET, T−1 publication lock, staleness fail-closed,
  min-dwell 2w, episode-merge 4w, floors F1≥10/F2≥2/F3≥26 (weekly-clock
  adaptation of the 20/3/100 triplet, shortfall-to-20 disclosed and bound by
  ×1.5 cost survival).
- ON/OFF/FLAT table state×cluster (macro-conditioned rows governed; E-SESSION/
  I-STATARB/NATGAS always-eligible class runs on its own sleeve gates; ABSTAIN
  and UNSEEN ⇒ macro rows FLAT).
- Allocation on $100k: per-trade 0.375% (0.25–0.5% preregistered), cluster cap
  2% one-way (USD-bloc = ONE exposure), NATGAS ≤1% tail-sized, portfolio cap
  6%, margin ≤30% utilization, no PnL-feedback sizing.
- Kill-switches KS1–KS6 typed (carry-unwind, cluster DD>4%, whipsaw, stale/
  unseen, account DD>10%, intervention — the last lives inside sleeves only).

## 5. Evaluation summary (full spec: `router/EVALUATION_PROTOCOL_DRAFT.md`)

Nested walk-forward (26-week test folds, expanding train, 1-week embargo,
52-week warmup, ≥6-fold calendar floor else `NOT_RUN_INSUFFICIENT_CALENDAR`);
trial ledger counts EVERY try (grid ≤54 state-engine nodes, TRAIN-only);
pre-PnL battery order: state census floors → representation-rho ≤0.20 vs dead
ancestors → P-20 arm-distinctness → sleeve admissions → null-validity (Q-11)
→ inverted-router kill. Baselines B0–B8 (FLAT, ALWAYS_ON, BEST_LEG-train-only,
ABSTAIN-ONLY, RANDOM_GATE 100 seeds duty+turnover matched, CLOCK_GATE,
INVERTED, LAGGED, ORACLE-non-governing). Robustness: ×1.5/×2 costs, switching
ladder, leave-one-asset/cluster, fold-concentration ≤50%, DSR>0 & PBO≤0.5 over
ALL ledger rows, state-error (corruption 5/10/20%, vintage divergence,
recompute divergence) reported separately, FLAT/duty audit. PASS bars P1–P7
typed; close codes negative-first-class (`ROUTER_NO_INCREMENTAL_VALUE`,
`ROUTER_TRADE_COUNT_ONLY`, `ROUTER_STATES_THIN`, `ROUTER_TABLE_UNINFORMATIVE`,
`NOT_RUN_*`).

## 6. Trial budget freeze (DRAFT — owner amends at registration)

| Ledger class | Cap |
|---|---|
| Trial-ledger rows total (every try, incl. train-fold grid nodes, admissions, kill constants) | **220** |
| Scored test-fold arm-executions (router+baselines+robustness reruns) | **64** |
| State-engine grid nodes (TRAIN-only, preregistered 3×3×3×2) | 54 (inside the 220) |
| Sleeves in initial slate | ≤10 (SLOT_LEFT_EMPTY valid) |
| Ledger overflow at any point | STOP → owner decision (no silent budget growth) |

Observed vs published denominators tracked separately (P-9). Every scored
number enters the ledger even if publication fails. S1 SEALED throughout this
cycle; no S1 read at any stage without a future owner-typed S1 plan.

## 7. Terminal outcomes (negative outcomes are first-class, preregistered)

- Any P1–P7 failure ⇒ typed FAIL close with full artifacts; no threshold
  iteration, no floor relaxation after PnL (owner law).
- Data-gate failures (V2/V3 PIT, calendar floor) ⇒ typed NOT_RUN close —
  valid, cheap, honest.
- Reopening condition (stated once, Q-10): a router-class retry on this
  universe requires a changed mechanism axis (payer/information/risk), never
  threshold/timeframe/symbol iteration.

## 8. Governance

- Lanes per `LANE_CHARTER.md`; A1-only integration; A7/skeptic independent
  (`skeptic/A7_PREREVIEW.md` — prereview of THIS draft; the formal A7
  prelaunch audit runs post-registration, pre-GO, fresh-context).
- Structured handoffs `zcode_orch_v3_handoff@1` under `handoffs/` (17 present:
  12 census + L1 + L3 + L4 [+ L5 skeptic on dispatch]).
- No push/merge/S1/credentials/orders/purchases this session. Owner changes
  (SANDBOX dirs) preserved.

## 9. GO phrases (typed, one per gate — NOT consumable from this document)

1. Registration: `GO PORTFOLIO ROUTER 12ASSETS 100K V1 REGISTER PLAN plan/PLAN_portfolio_router_12assets_100k_v1_DRAFT.md`
2. Scored execution (only after A7 prelaunch AUTHORIZED, fresh at its gate):
   `GO PORTFOLIO ROUTER 12ASSETS 100K V1 SCORED EXECUTION`

Typed early = intent, dies unconsumed (P-8). The owner's 2026-09-28 directive
is already recorded as intent only.

## 10. Artifact pins (sha256@16, at draft time — refreshed at registration)

```
dd6424c71b193449  census/CENSUS_1200.tsv        (v2 re-score, see CENSUS_SUMMARY erratum)
f72049deb6bdaa63  census/CENSUS_SUMMARY.md      (pre-erratum digest; erratum appended after)
fe9b920916cadcd9  census/shortlist.tsv          (v2 re-score)
19dd37c2ff068623  datacost/DATA_COST_MATRIX.md
f0b156266dbd8b05  datacost/DATA_COST_MATRIX_DRAFT.md
2efa3b17f330192e  datacost/PIT_SOURCE_TABLE.md
82558b58cdad68ec  cost/COST_ACCOUNTING_SPEC.md
f15fb1f29e2949f2  router/ROUTER_POLICY_DESIGN_DRAFT.md
f9fa23ba8abeedcf  router/EVALUATION_PROTOCOL_DRAFT.md
5342423039205af2  LANE_CHARTER.md
dfca3a1db55d12ab  census/CENSUS_PROTOCOL.md
```

## 11. Open items needing owner decisions (each is one action)

1. Register this cycle (GO phrase #1) or send the draft back for revision.
2. Data unblocks (each independent, each flips FLAT columns only after gates):
   (a) one M1 FX history source decision → NZDUSD + USDCHF; (b) one metals
   history decision + IBKR probe resume → XAUUSD/XAGUSD; (c) one energy
   continuous-futures decision → BRENT/WTI/NATGAS (+weather archive for
   NATGAS); (d) IBKR Activity/Flex statement → measured FX commission/swap.
3. REGIME-GATED-COMBO-V1 a/b decision remains OPEN (separate cycle's gate —
   listed here only so the owner sees both pending items in one place; this
   program takes no position and touches nothing).

If the owner declines registration: this control dir remains as complete
pre-GO research evidence (census + matrix + designs), nothing scored, S1
untouched, budget 0/0 consumed.

## 12. A1 addendum — skeptic prereview outcome (2026-09-28, post-draft)

Independent Lane-5 prereview: **AUTHORIZED_FOR_OWNER_REVIEW** — 0 CRITICAL,
0 HIGH, 3 MEDIUM, 6 LOW, 5 INFO (`skeptic/A7_PREREVIEW.md`; counts, source
line-refs, ancestry ids, PIT locks, baseline completeness, budget sums and
artifact pins were independently re-verified clean). The three MEDIUMs and
their dispositions:

- **F-1 ALFRED contradiction (load-bearing for the registration decision):**
  the router draft names ALFRED vintages as the cheap PIT-evidence path for
  V2 (VIX) / V3 (Brent−WTI), but L1's own `PIT_SOURCE_TABLE.md` records
  ALFRED as BLOCKED_DATA_AUTHORITY on this host. Fail-closed consequence: as
  of this draft, **V2/V3 have NO evidenced unblock path**, so if the cycle
  registered today the state engine's realistic pre-PnL outcome is
  `NOT_RUN_PIT_GATE_FAILED` (engine runs on V1 only is NOT an option —
  post-hoc variable substitution is forbidden). Unblocking V2/V3 therefore
  belongs on the owner-decision list alongside the data unblocks in §11
  (one actionable option: owner names an allowed VIX/EIA vintage source or
  accepts the cycle opening with the typed NOT_RUN close as a live
  possibility).
- **F-2 donchian cross-lane adjudication:** disclosed in CENSUS_SUMMARY
  erratum; F-0 court re-adjudicates at sleeve admission (may reduce the 15
  DISTINCT_TESTABLE to 13).
- **F-3 priority-formula deviation:** fixed — `merge_census.py` v2 implements
  the frozen §5 formula literally, census re-run (no verdict/count/ordering
  change), erratum + pin refresh recorded.

None of the three blocks owner review; F-1 should be read BEFORE deciding on
registration because it prices the most likely first gate the cycle would
hit.
