# SESSION_REPORT — PORTFOLIO-ROUTER-12ASSETS-100K-V1 pre-GO session (2026-09-28)

Lead A1 session per owner directive 2026-09-28. Everything below is PRE-GO
research: **0 scored cells, 0 backtests, 0 orders, 0 shadow touches, S1
SEALED_UNTOUCHED, no registration, no git writes.** The owner's directive was
recorded as intent only — it is NOT a GO phrase (P-8).

## What was done (owner's 5 steps → status)

1. **CENSUS — DONE.** 1,200/1,200 ideas read and verdicted (12 symbols ×
   S1–S100, verified gapless). Rubric + verdict tree frozen BEFORE dispatch
   (`census/CENSUS_PROTOCOL.md`; no PnL existed or exists for any idea — all
   remain HYPOTHESIS/NOT_RUN; Top-10 lists never treated as winners).
   Results (`census/CENSUS_SUMMARY.md` + `CENSUS_1200.tsv`):
   DISTINCT_TESTABLE 15 · PIT_UNPROVEN 433 · VARIANT_OR_DUPLICATE 548 ·
   BLOCKED_DATA 121 · NOT_FALSIFIABLE 68 · BLOCKED_COST 15. 917 distinct
   mech_keys; shortlist pool 385 (deduped global exemplars).
2. **DATA_COST_MATRIX — DONE.** 12/12 symbols decided
   (`datacost/DATA_COST_MATRIX.md`): ELIGIBLE = EURUSD GBPUSD USDJPY USDCAD
   AUDUSD (5 FX pairs; USDCAD/AUDUSD at H1 ceiling); FLAT_BLOCKED_DATA =
   NZDUSD USDCHF XAGUSD BRENT WTI NATGAS; FLAT_PIT_UNPROVEN = XAUUSD. Each
   FLAT names its single owner unblock. Vehicles, PIT publication rules per
   source, and the 18-item UNMEASURED cost register are pinned in
   `datacost/PIT_SOURCE_TABLE.md` + `cost/COST_ACCOUNTING_SPEC.md`.
3. **ONE POLICY — DESIGNED (not scored).** `router/ROUTER_POLICY_DESIGN_DRAFT.md`:
   gated sleeves (≤10, FLAT default, admission = census → F-0 mechanism court
   → PIT battery → ×2.0 after-cost TRAIN bill → floors) + state engine of
   exactly 3 PIT variables (V1 EFFR Δ63bd evidenced; V2 VIX pctl; V3
   Brent−WTI spread pctl — both PIT-gated) and exactly 4 states (WAR_ENERGY >
   RISK_STRESS > TIGHTENING > EASING) + ABSTAIN⇒FLAT, weekly Friday-17:00-ET
   clock with T−1 publication lock; ON/OFF/FLAT table state×cluster; $100k
   allocation with cluster caps; typed kill-switches KS1–KS6.
4. **ROUTER VALUE CHECK — PROTOCOL FROZEN (run is post-GO).**
   `router/EVALUATION_PROTOCOL_DRAFT.md`: nested walk-forward (26w folds,
   embargo, warmup, ≥6-fold calendar floor), trial ledger counting EVERY try,
   baselines B0–B8 (FLAT/ALWAYS_ON/equal-risk/BEST_LEG-train-only/
   ABSTAIN-ONLY/RANDOM-100-seeds duty+turnover matched/CLOCK/INVERTED/LAGGED/
   ORACLE-non-governing), pre-PnL battery (state floors 10/2/26 weekly-scaled,
   representation-rho ≤0.20 vs dead ancestors, P-20 distinctness, inverted-
   router kill), robustness (×1.5/×2 costs, switching ladder, leave-one-
   asset/cluster, fold-concentration, DSR/PBO over ALL trials, state-error
   battery), typed PASS bars P1–P7 with `ROUTER_TRADE_COUNT_ONLY` as an
   explicit FAIL.
5. **PLAN + GATES — DRAFTED, STOPPED AT OWNER GATE.**
   `plan/PLAN_portfolio_router_12assets_100k_v1_DRAFT.md` (+ `OUTCOME_EXPOSURE_MAP.md`,
   `TRIAL_BUDGET_FREEZE_DRAFT.md`: ledger ≤220 rows, ≤64 scored arm-executions),
   including §2's written justification for NOT scoring 1,200 ideas.
   Independent skeptic prereview: **AUTHORIZED_FOR_OWNER_REVIEW** (0 CRITICAL/
   0 HIGH; 3 MEDIUM dispositioned in plan §12 — F-1 ALFRED contradiction is
   the one to read before registering: V2/V3 currently have NO evidenced PIT
   unblock path, so the state engine may honestly open to a typed
   `NOT_RUN_PIT_GATE_FAILED`).

## Owner deliverables checklist (from the directive)

- (a) 1,200 sorted with reasons: `census/CENSUS_1200.tsv` (per-row verdict +
  reason + ancestry + source line) — DONE.
- (b) 12 symbols ELIGIBLE or FLAT/BLOCKED with reason: `datacost/DATA_COST_MATRIX.md` — DONE.
- (c) Single codeable/replayable ON/OFF policy: `router/ROUTER_POLICY_DESIGN_DRAFT.md`
  (A1-endorsed; PIT-replayable by construction) — DONE as spec; code is post-registration.
- (d) OOS walk-forward positive/negative table vs ALWAYS_ON: **NOT_RUN by
  design** — produced only by the post-GO scored stage under the frozen protocol.
- (e) PASS/FAIL/NOT_RUN conclusion: **NOT_RUN (nothing scored; S1 untouched)**.
  Honest prior stated in plan §0: negative, given four dead router-class ancestors.

## Incidents (all disclosed; no silent repairs)

- 3 census dispatches died on model-pool rate limit (1302) → fresh re-dispatch,
  no partials consumed (P-22). BRENT part missing `s_id` column → mechanical
  merge repair. Priority formula v1 deviated from frozen rubric (skeptic F-3)
  → script v2 re-run, erratum in CENSUS_SUMMARY. One hand-typed digest typo
  (shortlist pin) caught by machine re-measure and fixed. No git operations.

## Standing at close

Tree: `main` @ `abe7f70b`, dirty = owner's SANDBOX dirs (untouched) + this
program's new control dir (uncommitted — awaiting owner review/commit
instruction). Lock FREE_PROVEN, workers 0. REGIME-GATED-COMBO-V1 still AWAITING
OWNER a/b — untouched. 16 handoff JSONs under `handoffs/` (12 census + L1 + L3 + L4 + L5),
48 files total in the control dir (measured). Next action is the owner's: see §11 of the
plan draft for the exact decision list and GO phrase #1.

## Addendum — REGISTRATION (2026-09-28T12:53:46Z)

Owner typed the registration GO verbatim at the gate. Consumed: pre-GO
evidence landed at `a51dc758` (root main); worktree + branch
`orca/portfolio-router-12assets-100k-v1-integration` bootstrapped (manifest
`a63d053d`); cycle registered via researchctl — **ACTIVE_LIGHT, 0/64, doctor
0 findings for the new row**; control-plane committed at `36638aa3`
(registry sha256 9f3af880…). Full chain: `plan/REGISTRATION_RECEIPT.md`.
Scored execution remains locked behind A7 prelaunch + owner GO #2 (two-key).
S1 sealed; no orders; lock free.
