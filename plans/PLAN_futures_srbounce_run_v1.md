# PLAN — FUTURES-SRBOUNCE-RUN-V1 (STAGE B ONLY — behavioral tables)

Status: REGISTERED (PLANNED_NOT_STARTED) · Owner authorization chain:
"OWNER DECISION — FINAL PRELAUNCH PREPARATION" (2026-10-17) →
"OWNER INSTRUCTION — CLOSE B2 DELTA AUDIT → PREPARE STAGE B ONLY"
(2026-10-18, registration authorized after B2 closure; B2 CLOSED by
verifier6, CONFIRM, zero FAIL). Evidence base: prep branch
`prep/futures-srbounce-prep-20261017` (cycle
FUTURES-SRBOUNCE-PREP-V1 control dir, SHAs pinned in
STAGE_B_EXACT_RUN_PACKET.md).

## 0. Mission

Deliver the owner's behavioral outcome tables: how price reacts when it
touches a known M15/H1/H4 support/resistance — bounce/break/deadband
probabilities, favorable/adverse excursion magnitudes and timing,
first-passage ordering — on the development window
**2010-06-06..2014-12-31 ONLY**, with baselines. THIS CYCLE IS STAGE B
ONLY. No policy walk-forward (Stage P), no ancestry rho (Stage A), no
PnL/edge claims.

## 1. Staged authority (no implicit promotion)

| Stage | Budget | Authority |
|---|---|---|
| **B — behavior tables** | **18 evaluation units** (6 behavior + 6 placebo-baseline + 6 clock-matched; ES/NQ × M15/H1/H4) | **APPROVED (owner 2026-10-18)** — this cycle runs ONLY Stage B |
| P — walk-forward SL/TP | 688 evaluation units (manifest v2 rev 2) | PREPARED, **NOT authorized to run** — requires its own owner gate |
| A — ancestry rho | TBD by separate proposal | **NOT authorized**; will never run under a signal-side/behavioral label |

No stage consumes another's budget; no implicit promotion; each future
stage requires its own owner gate and (where applicable) typed GO.

## 2. Definitions (all frozen upstream — unchanged)

Levels/engagements: census v2 law (completed-bar extremes M15/H1/H4,
fresh-first-touch, arming/merging/availability-by-completion) — NOT
confirmed swing levels. Horizons: 15/60/240 wall-clock minutes from touch
completion (t_obs). Estimands: p_ref (touch close) and p_level (level
price) reported SEPARATELY. Deadband = 0.10×S_tf (S_tf = median HIGH−LOW
range of last 20 same-TF bars). Barrier grid = ±{0.25,0.50,1.00}×S_tf.
Classes: BOUNCE/BREAK/DEADBAND + HORIZON_CENSORED +
AMBIGUOUS_PARTIAL_WINDOW. No filters/patterns/new axes (owner: locked).

## 3. Execution law

- Data: 1m front-quarter chains, exposure window sealed at 2014-12-31 for
  this cycle (Layer A only); the 2023+/S1 seal (SealedWindowRefused) and
  6A zero-read remain absolute.
- The Stage B runner STRUCTURALLY REFUSES: any bar/request outside
  2010-06-06..2014-12-31; any Stage P or ancestry-rho invocation; unknown
  configuration ids; budget expansion beyond 18 units; authorization drift.
- Tables A/B/C/D + baselines per BEHAVIOR_STUDY_SPEC.md; outputs are
  DESCRIPTIVE — never called edge; baselines (placebo levels,
  clock-matched) computed on the same population/context.
- Machine-enforced accounting: 18 units logged
  observed/published/failed/retry; nested engagement-row counts enumerated
  per unit (never "18 observations").

## 4. Budget

**18 evaluation units (APPROVED).** Any scope increase (extra baselines,
extra TFs, cross-horizon, retouch) = new owner decision. Runtime estimate:
~2M engagement-rows across 18 passes (census-v2 dev-window volumes),
well under one heavy-lock session.

## 5. Gates

G1 prelaunch audit (fresh-context verifier: B2 closure binding, scope,
budget, refusal paths, dry-run) → G2 owner typed GO phrase at THIS cycle's
gate → G3 run under heavy lock + ledger → G4 independent run audit →
tables delivered to owner. Stage P / Stage A each restart at their own
plan+gate. No GO phrase is registered now (P-8: typed only at its own
gate with the owner present).
