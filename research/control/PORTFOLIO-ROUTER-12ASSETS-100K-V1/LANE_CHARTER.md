# LANE_CHARTER — PORTFOLIO-ROUTER-12ASSETS-100K-V1 (pre-GO research, 2026-09-28)

Owner directive 2026-09-28 (Lead-session prompt). Program goal: research ONE
portfolio coordination policy ("router") for exactly 12 assets (EURUSD GBPUSD
USDCAD USDJPY AUDUSD NZDUSD USDCHF XAUUSD XAGUSD BRENT WTI NATGAS) on ONE
simulated $100,000 account. **This session: research + trustworthy backtest
DESIGN only. No shadow/paper/live. No orders. No registration, no scored run —
those need a separate owner GO.**

## Measured state at charter (2026-09-28, root checkout)

- Branch `main` @ `abe7f70bf22639184541be6b3564cd0760580f45`; dirty = owner's
  untracked `research/control/SANDBOX-OVERFIT-3ASSETS/{data,out}/` (preserve,
  do not touch). Heavy lock FREE_PROVEN; no workers.
- Live cycles (registry): REGIME-GATED-COMBO-V1 ACTIVE_LIGHT (0/3, prelaunch
  REFUSED, AWAITING OWNER a/b) — DO NOT TOUCH. Other ACTIVE_LIGHT cycles
  untouched. S1 SEALED everywhere — no S1 access this program (pre-GO anyway).
- Corpus verified: 12 × 100 = 1,200 ideas, all HYPOTHESIS/NOT_RUN.
- Key dead ancestry for this program's class: JEV-REGIME-ROUTER-V2
  (`JEV_NO_INCREMENTAL_VALUE`), REGIME-STRATEGY-MAPPING-V1
  (`NO_REGIME_STRATEGY_INCREMENTAL_VALUE`), PHASE-STRATEGY-V1
  (`PHASE_STRATEGY_V1_NO_INCREMENTAL_VALUE`), REGIME-GATED-COMBO-V1 (exposed
  reading: GATED loses all baselines; pending owner). DAYTRADER-100-V1
  REJECT_ALL. RANGEFADE/RANGEEXP ancestry killed by PIT seam (ERP1-TRACKA-1).

## Lanes (only A1 integrates; lanes never touch each other's outputs)

| Lane | Scope | Agent writes (ONLY these) | Handoff JSON |
|---|---|---|---|
| L1 data/PIT+instrument | inventory repo/prospective data for 12 symbols; vehicle choice; PIT source table with available_at rules; per-symbol ELIGIBLE/FLAT rec | `datacost/DATA_COST_MATRIX_DRAFT.md`, `datacost/PIT_SOURCE_TABLE.md` | `handoffs/L1_data_pit.json` |
| L2 census ×12 | read one symbols/*.md fully; 100 TSV rows per CENSUS_PROTOCOL | `census/parts/census_<SYM>.tsv` | `handoffs/census_<SYM>.json` |
| L3 cost/accounting | cost stack per vehicle (measured vs UNMEASURED), $100k portfolio accounting (cash, FX conversion, overlap, cluster caps, margin, switching costs) | `cost/COST_ACCOUNTING_SPEC.md` | `handoffs/L3_cost_accounting.json` |
| L4 router design | state engine (≤3 PIT vars, ≤4 states, floors), ON/OFF/FLAT table, allocation, kill-switches; evaluation protocol (baselines, nested walk-forward, falsifiers, DSR/PBO) | `router/ROUTER_POLICY_DESIGN_DRAFT.md`, `router/EVALUATION_PROTOCOL_DRAFT.md` | `handoffs/L4_router_design.json` |
| L5 skeptic/A7 | independent prereview of integrated artifacts (wave 2) | `skeptic/A7_PREREVIEW.md` | `handoffs/L5_skeptic.json` |
| A1 (this session Lead) | protocols, merge/integration, final matrix/policy/plan drafts, session report | everything under `plan/`, `census/CENSUS_1200.tsv`, `census/CENSUS_SUMMARY.md`, `STATE_REMEASURE.md`, `SESSION_REPORT.md` | — |

## Laws binding every lane agent

1. Read-only outside your two/three declared output files. No git write
   operations at all (no add/commit/push). No registry/ledger/MAP/LESSONS
   writes. No heavy jobs, no backtests, no S1, no network fetches beyond
   read-only public documentation if strictly needed (record URLs).
2. Never touch: other cycles' control dirs, `.worktrees/`, SANDBOX dirs,
   `plans/`, `research/wayfinder/` (read OK).
3. All 1,200 ideas are HYPOTHESIS/NOT_RUN. Never call any "Top-10" list
   winners. No PnL claims.
4. Handoff JSON schema `zcode_orch_v3_handoff@1` at the exact path above;
   fields: schema, task_id, cycle_id ("PORTFOLIO-ROUTER-12ASSETS-100K-V1"),
   role, lane, dispatch_sha `abe7f70bf22639184541be6b3564cd0760580f45`,
   actual_start_sha (same), commit_sha "NONE_READ_ONLY_SESSION", changed_paths
   (your outputs), tests [], authority_claims [], known_limitations [],
   incidents [], tree_status "READ_ONLY_OWNER_DIRTY_PRESERVED", workers 0,
   outputs (your artifact paths). Chat prose is advisory; the artifact is
   authority.
5. Numbers you quote must come from files you actually read (cite path).
   Missing evidence = NOT_RUN/UNMEASURED, never inferred good.
