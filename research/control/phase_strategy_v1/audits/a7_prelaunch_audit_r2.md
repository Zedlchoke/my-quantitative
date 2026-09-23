# A7 PRELAUNCH AUDIT — ROUND 2 (DELTA) — PHASE-STRATEGY-V1

- Schema twin: `a7_prelaunch_audit_r2.json` (`psv1_a7_prelaunch_audit@1`, round 2)
- Audited head: `8865e7d33e6e6e00d9b1dae7ce8b911e740139aa` on `orca/phase-strategy-v1-integration` (registry head matches)
- R1 baseline: verdict `REMEDIATION_REQUIRED` at commit `991b4e02` (this branch, unchanged)
- Remediation commits adjudicated: `458d8aa3` (L1 lane), `0a7d9c8b`, `75765be2`, `a7d355db`, `8865e7d3`
- Method: delta-only; every r1-closing claim re-verified from bytes. The H1 rhos
  were **re-measured by the auditor** from the L1 worktree staging bytes
  (digest-verified in r1) using the adjudicated lane code extracted from git
  objects plus **auditor-owned** shadow and Pearson implementations.

## VERDICT: `AUTHORIZED_FOR_DISCOVERY_STOP`

Zero unresolved HIGH/CRITICAL. All five r1 findings CLOSED with independent
verification. Two new INFO observations, no action required.

---

## r1 findings — closed/open

| r1 item | Sev | Status | One-line evidence |
|---|---|---|---|
| A7-H1 unmeasured run_imbalance (3 BTC_H1 arms) | HIGH | **CLOSED** | Auditor re-measured from raw bytes: UPTREND +0.119477, ACC +0.005920, DOWN +0.084990 — all ≤ 0.20, matching the record to 6 decimals; estimator proven to be signal-vs-shadow information correlation (books are {0,±1} positions; rho vs returns would be 0.0122); freeze records `E3 DISCHARGED`; `self_veto` now wired to run_imbalance so a >0.20 reading would have vetoed. |
| A7-M2 missing BTC_H4 arm_config_digest | MEDIUM | **CLOSED** | Auditor recomputed `sha256(canonical JSON, sorted keys, compact)` of the frozen arm_config = `3dbbdb5f77acb8cd47634d9599d540c382d9ebe7a5efc0f17ebdade33890f21f` — exact; method cross-validated against all three L1 known-good digests (also exact); config params match the frozen proposal law (30/15/6/12/450, long, 1.0, next_open). |
| A7-M3 BTC digest re-verification unscheduled | MEDIUM | **CLOSED** | `evaluation_freeze.scored_run_ingest_verification` is now a BINDING fail-closed precondition: re-hash every BTC manifest entry (102 + 182 incl. 4h shadow) against bytes re-staged from data.binance.vision + SPY sha re-verify; ANY drift ⇒ `BLOCKED_DATA_OR_SELECTION`, zero cells scored. |
| A7-L4 missing not_scored row | LOW | **CLOSED** | BTC_H4 TRANSITION_UNKNOWN row added (GATE_STATE_NOT_TRADABLE / FLAT); 15/15 cell×phase slots enumerated. |
| A7-L5 stale manifest status | LOW | **CLOSED** | `a7d355db` sets `a7.status` SPAWNED with the r1 verdict reference. |

## New findings (r2)

- **A7-R2-I1 (INFO)** — shadow head-bar convention differs between lanes
  (L1 keeps NaN head; L2 fills first ret with 0): visible only in the 7th
  decimal of the rho; finite-grid Pearson excludes the head either way. No action.
- **A7-R2-I2 (INFO)** — run_imbalance window is per-cell clock-scaled
  (L1 24×H1 per its frozen lane convention; L2 12×H4); same construction
  family, which is what the veto governs. No action.

## Duty-by-duty verification summary

- **(a) Independent re-measurement** — adjudicated lane code extracted from
  git objects at `458d8aa3` into a scratch dir; labels rebuilt from the
  digest-verified staging parquet; candidate position books rebuilt via the
  frozen proposal signal functions; shadow and Pearson computed with
  auditor-owned code. All three recorded rhos reproduced
  (0.119477 / 0.005920 / 0.084990). Estimator verified as signal-information
  correlation, not returns (control: rho(signal, returns) = 0.0122 ≠ recorded).
- **(b) Shadow family** — `sign(ret1).rolling(24).sum()/24` matches L2's
  frozen `shadow_series` construction; window 24 documented as L1's
  convention across all its shadows.
- **(c) Freeze + veto wiring** — `8865e7d3` rewrites the three L1 ancestry
  blocks with measured values and E3 DISCHARGED; `self_veto = any(not
  distinct_within_bar)` now includes run_imbalance (a >0.20 reading would
  have vetoed); the remaining NOT_MEASURED entries (OI, DVOL, pair) keep the
  r1-judged legitimate reasons; all previously measured rhos byte-identical
  to the r1-audited census.
- **(d) M2/M3/L4/L5** — see table above; all verified by recomputation or
  direct diff inspection.
- **(e) Scope scan** — `git diff 4b7eae34..8865e7d3`: 12 files, 206+/34−,
  all inside `research/control/phase_strategy_v1/`; plan untouched; code
  changes confined to `ancestry.py` + a notes-only `run_lane.py` addition;
  no PnL path introduced, no gate weakened, no floor/cost/budget movement,
  no scope creep; new `test_ancestry.py` goldens are hand-computed and
  falsifiable; suites re-run by the auditor on the full tree extracted at
  `8865e7d3`: L1 35+3s, L2 44+1s, L3 55 — green, matching claimed counts.
- **(f) Terminal carry-overs** — r1 A7-I6..I9 remain recorded in the r1
  artifact and are carried to A7 terminal (G9), together with R2-I1/I2.

## What the owner must know before STOP-1

This verdict authorizes proceeding to the STOP-1 owner gate. It is **not**
the GO. The remaining obligations are procedural: the §16.2 plain-language
report, the verbatim phrase `GO PHASE STRATEGY V1 SCORED EXECUTION` typed by
the owner at STOP-1, the scored run under the machine-wide heavy lock with
the now-binding ingest verification as its first step, per-lane test
invocation, and the A7 terminal audit (G9) which carries I6–I9 and R2-I1/I2.

— A7, independent prelaunch auditor (round 2)
