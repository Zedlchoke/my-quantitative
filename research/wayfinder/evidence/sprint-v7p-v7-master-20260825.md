# Sprint V7P → V7 Master Report — 2026-08-25

```text
V6P_VERDICT            = V6P_PASS_V6_AUTHORIZED (immutable, prior sprint)
V6_FAMILY              = REJECT_ALL (4/4 scored)
V7P_VERDICT            = 18/18 PASS (one remediation round: golden-report contract-ref sync; A7 scoped re-audit PASS)
V7_LAUNCH_AUTHORITY    = A7 prelaunch attestation PASS @6533ce0 lineage; expanded preflight 14/14 incl B1/B2 blockers resolved
V7_TERMINAL            = V7_REJECT_ALL_CANDIDATE
V8_TRANSITION          = V8_NOT_STARTED_PREP_GATES_T12_T13_T14_FAIL (10/15 true)
SCORED_BUDGET          = 8/8 used (V6:4 + V7:4) — zero spare
LOCKED_CANDIDATE       = NONE
S1_STATUS              = NOT_STARTED
LIVE_MONEY             = UNCHANGED_DISABLED
OWNED_WORKERS          = none alive at shutdown
GIT                    = clean tree; HEAD see shutdown_report.json; not pushed
```

## V7 measured results (all hashes CLEAN, repro all-match)

| Trial | Net PnL | PF | Verdict | Primary reject reason |
|---|---:|---:|---|---|
| PRICE-DIV-1D | −5,982.48 | 0.9765 | REJECTED | PF<1.10 & pnl<0 |
| PRICE-DIV-3D | −3,443.75 | 0.9835 | REJECTED | PF<1.10 & pnl<0 |
| PRICE-DIV-7D | +938.24 | 1.0049 | REJECTED | PF<1.10 (edge too weak) |
| REV-3D control | −23,415.55 | 0.8876 | CONTROL_ONLY | negative control as designed |

Concentration (positive-pnl basis): top fold ≤43.18%, top symbol ≤21.50% — concentration gates were NOT the failing surface this family; the failure is raw edge strength below the hard PF floor on every lookback.

## Decision-surface repairs proven this sprint

- Generation-aware provenance (divergence⇒v7p, carry⇒v6p, unknown⇒abort) + manifest records actual paths/hashes.
- Hardened resolved-contract generator: explicit launch SHA (placeholder/invalid commit rejected), frozen trial inventory, registry/output + execution contract, provenance_contract block inside canonical hash.
- Machine finalizer FG0–FG7 + concentration + stress manifest + statistical haircut fail-closed sentinels.
- Full-family reproduction harness (V6 4/4 then V7 4/4, 20+ fail-closed surfaces).
- Global trial ledger before/after snapshots; append-only verified after deterministic full-sort reconstruction.

## Why V8 did not start

T12 (dedicated six-alt two-year data audit), T13 (weekly-reversal engine/golden/PIT path) and T14 (its prelaunch attestation) were not completable within the window — per §17.3 a single missing gate blocks launch. Preregistration itself IS safely frozen (hashes pinned in baseline v5+) so a future sprint can execute V8 without re-spec drift.

## Next safe action

Fresh sprint: run A2 six-alt data audit → implement weekly reversal dispatcher + golden → T13/T14 → then V8 quartet under remaining budget rules. Do NOT touch S1; do not reuse this sprint's PnL for tuning.
